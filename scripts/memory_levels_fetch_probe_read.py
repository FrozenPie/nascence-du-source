"""J-1280: reusable, READ-ONLY reader for data/memory_levels_fetch_probe.jsonl (J-1156 / F-1799's observe-only probe).

WHY THIS EXISTS. F-1584 *estimated* (INFERRED, from a guessed fetch time) that core/memory_levels.py's
shadow_distill() fetch -- `ORDER BY timestamp DESC LIMIT _FETCH_LIMIT(160)`, with the frontier then jumping to the
newest CLUSTERED row -- truncates ~35-40% of runs and leaves ~half of all new eligible raw rows unexamined forever.
J-1156 added a one-line-per-run probe so that could be MEASURED; J-1280 read it (its two findings are in
docs/findings.jsonl under plan memory_levels_plan, session J-1280). This script keeps that read (and the zero-LLM
counterfactual built on it), so the next re-read -- more runs, a changed _FETCH_LIMIT or bucket cap -- is one command
instead of a throwaway script (the F-1818 lesson, same as scripts/memory_levels_cap_replay.py).

WHAT IT DOES.
  1. (always) reads the probe: integrity checks (frontier chain last_ts_before[k+1] == newest_ts[k]; fetched_rows ==
     min(pool_size, fetch_limit)); truncation (runs with pool_size > fetch_limit, Wilson 95%); rows dropped =
     sum(max(0, pool_size - fetched_rows)) and its share of the pool (bootstrap 95% over runs); the pool-size
     distribution; the share of the pool that would be dropped at other window sizes (arithmetic on the real pools);
     throughput of truncated vs non-truncated runs; the row accounting (dropped / fetched-but-unclustered /
     clustered / retired); a per-run table (gap since the previous run, first-run-after-restart from nascence.log).
  2. (--replay) re-clusters the REAL pools with the module's own _cluster() at other window sizes / bucket caps and
     prints what each would have formed. Pools are reconstructed from the DB: every level-0 row in a raw origin with
     last_ts_before < timestamp <= (the run's first shadow-log row) -- cold rows included, because most rows gisted
     since are cold NOW but were warm at fetch time. The probe's own pool_size is the check: this reconstruction
     matched it to within -1..+5 rows on all 30 runs of the first read, and replaying the LIVE window (160) reproduced the
     logged cluster COUNTS and per-kind counts on 30/30 runs and the exact source sets on 23/30 (the other 7 differ
     only by <=5 boundary rows). It is a ONE-STEP counterfactual (each run replayed from the real frontier it started
     at; later runs' frontiers are not re-simulated) and zero-LLM (clusters only: gist faithfulness/commit yield is NOT
     simulated -- project retirement yourself from the observed per-kind commit rates, and label that INFERRED).

IT NEVER WRITES, and is safe while Du is live: probe/shadow/log are opened read-only; the DB is opened with
mode=ro + PRAGMA query_only in ONE query, then closed; core/memory_levels.py is loaded by file path with importlib (the
core/ package __init__ never runs; the module's top level only defines constants/functions) and any cap override is an
in-memory attribute set on that private module object. No model call, no server contact. (Do not point it at a
different process's stores.)

USAGE (from the repo root; data dir defaults to <repo>/data, else C:\\Nascence\\data):
    python scripts/memory_levels_fetch_probe_read.py
    python scripts/memory_levels_fetch_probe_read.py --since "2026-09-25 19:21:51"
    python scripts/memory_levels_fetch_probe_read.py --replay --limits 160,320,500,720,0
    python scripts/memory_levels_fetch_probe_read.py --replay --limits 160,500 --caps semantic=5,self=8,episodic=2 --max-clusters 15
    python scripts/memory_levels_fetch_probe_read.py --replay --limits 160,500 --caps semantic=5,self=8,episodic=2 --max-clusters 15 --demote-cap 90
  --limits: fetch-window sizes to replay (0 = unbounded). --caps/--max-clusters override _KIND_BUCKET_CAP/_MAX_CLUSTERS in
  memory only (default = the module's live values). --demote-cap N adds a Monte Carlo of shadow_distill's commit gate at
  MAX_DEMOTE_PER_RUN=N over each replayed config (observed per-kind commit rates, independent draws): does the cap keep its
  headroom if throughput rises? Its baseline row reproduced the logged demoted/run (41.9 vs 41.8, p90 59 vs 59) on the first read. Choose --since as a real RESTART boundary (a "Nascence is awake"
  line), not a commit time: _FETCH_LIMIT/_KIND_BUCKET_CAP are module constants read at process start.
  _cluster()'s tie-break between equal-size topic buckets depends on PYTHONHASHSEED (F-1799); --replay re-executes
  itself with PYTHONHASHSEED=0 so a re-read is reproducible (aggregates were identical across 12 seeds in the first read).
"""
import argparse
import bisect
import collections
import datetime
import importlib.util
import json
import math
import os
import random
import sqlite3
import statistics
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")   # Windows charmap guard (this repo's own daemon lesson)
except Exception:
    pass

# F-1584's own INFERRED numbers (J-0886, 48 post-merge runs, estimated fetch time), printed beside the measured ones.
F1584 = {"runs_truncated_pct": "35-40% (17-19 of 48)", "rows_dropped_pct": "48-56% of new intake",
         "fit_in_window_pct": "<= 44.1%", "clustered_pct": "24.3% (75.0/run)", "retired_pct": "14.6%",
         "pool_mean": "253-308", "pool_median": "102-148", "steady_pool_mean": "140 (n=35, 4-6 over 160)"}


def _fmt(ts: float) -> str:
    return datetime.datetime.fromtimestamp(ts).strftime("%m-%d %H:%M:%S")


def _epoch(s: str) -> float:
    return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S").timestamp()


def load_jsonl(path: Path) -> list:
    rows = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                rows.append(json.loads(ln))
            except Exception:
                continue          # a half-written trailing line while Du appends: ignore, never raise
    return rows


def wilson(k: int, n: int, z: float = 1.96):
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (c - h) / d, (c + h) / d


def restart_events(log_path: Path, lo: float, hi: float) -> list:
    """[(epoch, 'awake'|'down')] from nascence.log's own markers inside [lo-1d, hi]; best-effort, [] if unreadable."""
    ev = []
    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            for ln in f:
                if "[nascence.main] Nascence is awake" in ln:
                    k = "awake"
                elif "[nascence.main] Nascence shutting down" in ln:
                    k = "down"
                else:
                    continue
                try:
                    t = _epoch(ln[:19])
                except Exception:
                    continue
                if lo - 86400 <= t <= hi:
                    ev.append((t, k))
    except Exception:
        return []
    return ev


def probe_report(rows: list, events: list, prev0=None) -> None:
    """rows: probe rows (pool_size never None -- main() drops those first), ascending ts. prev0: ts of the probe row
    just before rows[0] in the file (None if rows[0] is the file's first row)."""
    N = len(rows)
    ts = [r["ts"] for r in rows]
    pool = [r["pool_size"] for r in rows]
    fetched = [r["fetched_rows"] for r in rows]
    lim = [r["fetch_limit"] for r in rows]
    trunc = [p > l for p, l in zip(pool, lim)]
    dropped = [max(0, p - f) for p, f in zip(pool, fetched)]
    print(f"probe rows: {N}   first {_fmt(ts[0])}   last {_fmt(ts[-1])}   span {(ts[-1]-ts[0])/86400:.2f} wall days")
    chain = sum(abs(rows[i + 1]["last_ts_before"] - rows[i]["newest_ts"]) < 1e-6 for i in range(N - 1))
    print(f"integrity: frontier chain last_ts_before[k+1]==newest_ts[k] {chain}/{N-1}; fetched_rows==min(pool,limit) "
          f"{sum(f == min(p, l) for p, f, l in zip(pool, fetched, lim))}/{N}; "
          f"0-cluster runs {sum(r['clusters'] == 0 for r in rows)}; fetch_limit values {sorted(set(lim))}")
    S = sum(pool)
    Sf, Sd = sum(fetched), sum(dropped)
    Ss, Sdem, Scl = sum(r["sources_clustered"] for r in rows), sum(r["demoted"] for r in rows), sum(r["clusters"] for r in rows)
    k = sum(trunc)
    lo, hi = wilson(k, N)
    print("\n== TRUNCATION (F-1584's question, measured) ==")
    print(f"runs with pool_size > fetch_limit: {k}/{N} = {100*k/N:.1f}%  (Wilson 95% {100*lo:.1f}-{100*hi:.1f}%)   [F-1584: {F1584['runs_truncated_pct']}]")
    rng = random.Random(1280)
    shares = sorted(sum(dropped[i] for i in idx) / sum(pool[i] for i in idx)
                    for idx in ([rng.randrange(N) for _ in range(N)] for _ in range(20000)))
    print(f"sum pool {S}; fetched {Sf} ({100*Sf/S:.1f}%)  [F-1584: {F1584['fit_in_window_pct']}]; "
          f"DROPPED {Sd} = {100*Sd/S:.1f}% of the pool (bootstrap-over-runs 95% {100*shares[int(.025*len(shares))]:.1f}-{100*shares[int(.975*len(shares))]:.1f}%)  [F-1584: {F1584['rows_dropped_pct']}]")
    print(f"clustered {Ss} = {100*Ss/S:.1f}% of pool, {Ss/N:.1f}/run  [F-1584: {F1584['clustered_pct']}]; retired behind a committed gist (demoted) "
          f"{Sdem} = {100*Sdem/S:.1f}%, {Sdem/N:.1f}/run  [F-1584: {F1584['retired_pct']}]; clusters {Scl} = {Scl/N:.2f}/run")
    print(f"row accounting: pool {S} = dropped-by-window {Sd} ({100*Sd/S:.1f}%) + fetched-but-unclustered {Sf-Ss} ({100*(Sf-Ss)/S:.1f}%) "
          f"+ clustered {Ss} ({100*Ss/S:.1f}%)")
    print("  (a dropped row is older than the newest clustered row, so it is below the NEW frontier and never fetched again: "
          "the fetch WHERE is `timestamp > last_ts`)")

    print("\n== POOL DISTRIBUTION ==")
    sp = sorted(pool)
    q = lambda f: sp[min(N - 1, math.ceil(f * N) - 1)]
    print(f"sorted: {sp}")
    print(f"mean {statistics.mean(pool):.1f} [F-1584 {F1584['pool_mean']}]  median {statistics.median(pool):.1f} [{F1584['pool_median']}]  "
          f"p75 {q(.75)} p90 {q(.9)} max {max(pool)}")
    steady = [(p, l) for p, l in zip(pool, lim) if p < 500]
    if steady:
        print(f"steady-state (pool<500): n={len(steady)} mean {statistics.mean(p for p, _ in steady):.1f}, over the limit: {sum(p > l for p, l in steady)}  [F-1584: {F1584['steady_pool_mean']}]")
    ok = [p for p, t in zip(pool, trunc) if not t]
    tr = [p for p, t in zip(pool, trunc) if t]
    if ok and tr:
        print(f"non-truncated n={len(ok)} pool mean {statistics.mean(ok):.0f} (max {max(ok)}); truncated n={len(tr)} pool mean {statistics.mean(tr):.0f} (min {min(tr)}, max {max(tr)})"
              + ("  -> BIMODAL: no pool between %d and %d" % (max(ok), min(tr)) if max(ok) < min(tr) else ""))

    print("\n== COVERAGE at other window sizes (arithmetic on the real pools; NOT a re-clustering -- see --replay) ==")
    for L in (160, 200, 250, 320, 400, 500, 640, 720, 800, 1024):
        d = sum(max(0, p - L) for p in pool)
        print(f"  L={L:4d}: runs truncated {sum(p > L for p in pool):2d}/{N}, rows dropped {d:5d} ({100*d/S:4.1f}% of pool)")

    print("\n== THROUGHPUT: truncated vs not ==")
    for name, sel in (("truncated", trunc), ("not truncated", [not t for t in trunc]), ("all", [True] * N)):
        g = [r for r, s in zip(rows, sel) if s]
        if g:
            print(f"  {name:14s} n={len(g):2d} pool/run {statistics.mean(r['pool_size'] for r in g):5.0f} fetched/run {statistics.mean(r['fetched_rows'] for r in g):4.0f}  "
                  f"clusters/run {statistics.mean(r['clusters'] for r in g):.2f}  sources/run {statistics.mean(r['sources_clustered'] for r in g):5.1f}  demoted/run {statistics.mean(r['demoted'] for r in g):5.1f}")
    print("  clusters/run histogram:", dict(sorted(collections.Counter(r["clusters"] for r in rows).items())),
          " (>=10 means the self AND semantic bucket caps of 5 were both hit; max possible 12)")

    # incarnations, off time, live-time rates
    aw = sorted(t for t, kd in events if kd == "awake")
    off = 0.0
    evs = sorted(events)
    for i, (t, kd) in enumerate(evs):
        if kd == "down":
            nxt = next((t2 for t2, k2 in evs[i + 1:] if k2 == "awake"), None)
            a, b = max(t, ts[0]), min(nxt if nxt else ts[-1], ts[-1])
            if b > a:
                off += b - a
    wall_h = (ts[-1] - ts[0]) / 3600
    live_h = wall_h - off / 3600
    if N > 1 and live_h > 0:
        print(f"\nlive time between the first and last run ~{live_h:.1f} h ({live_h/24:.2f} live days; wall {wall_h:.1f} h, logged off-time {off/3600:.1f} h; a restart with no logged "
              f"shutdown line counts as 0 off-time) -> {(N-1)/(live_h/24):.2f} runs/live-day; eligible intake (sum pool of runs 2..N) "
              f"{sum(pool[1:])/(live_h/24):.0f} rows/live-day; examined (fetched) {sum(fetched[1:])/(live_h/24):.0f}; retired {sum(r['demoted'] for r in rows[1:])/(live_h/24):.0f}  "
              f"[F-1584/F-1580 window: ~2,300 intake, 7.55 runs, 339 retired per live day]")

    print("\n== PER RUN ==  # end-of-run  gap_h  pool  fetched  dropped  clusters  sources  demoted   (FIRST = first run after a restart)")
    prev = prev0
    for i, r in enumerate(rows):
        lo_t = prev if prev is not None else r["ts"] - 86400
        first = any(lo_t < t <= r["ts"] for t in aw)
        gap = (r["ts"] - prev) / 3600 if prev is not None else float("nan")
        print(f"{i+1:3d}  {_fmt(r['ts'])}  {gap:5.1f}  {r['pool_size']:5d} {r['fetched_rows']:5d} {dropped[i]:5d}   {r['clusters']:3d} {r['sources_clustered']:4d} {r['demoted']:4d}"
              f"  {'FIRST' if first else '     '}{' TRUNC' if trunc[i] else ''}")
        prev = r["ts"]


def load_ml(repo: Path):
    spec = importlib.util.spec_from_file_location("_ml_fetch_probe_read", repo / "core" / "memory_levels.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def read_window_rows(db_path: Path, origins, lo_ts: float, hi_ts: float) -> list:
    conn = sqlite3.connect("file:" + db_path.resolve().as_posix() + "?mode=ro", uri=True, timeout=10)
    try:
        conn.execute("PRAGMA query_only=ON")
        conn.row_factory = sqlite3.Row
        ph = ",".join("?" * len(origins))
        cur = conn.execute(
            f"SELECT fragment_id, content, origin, keywords, timestamp, cold FROM memory_fragments "
            f"WHERE abstraction_level = 0 AND origin IN ({ph}) AND timestamp > ? AND timestamp <= ? ORDER BY timestamp ASC",
            (*origins, lo_ts, hi_ts))
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def commit_gate_sim(cluster_sizes: list, yields: dict, cap: int, draws: int = 2000, seed: int = 1280):
    """Monte Carlo of shadow_distill's live commit gate over replayed clusters. cluster_sizes: per run, [(kind, n_sources)]
    in _cluster()'s own order (largest first). Each cluster is eligible with its kind's OBSERVED commit rate (independent
    draws -- an assumption: real eligibility is correlated within a night); commit iff eligible and running_demoted < cap
    (checked BEFORE adding n_sources, exactly as shadow_distill does). Returns (mean demoted/run, p90, share of draws whose
    UNCAPPED eligible total >= cap, discarded raw per run)."""
    rng = random.Random(seed)
    got, hit, disc_raw, n = [], 0, 0, 0
    for run in cluster_sizes:
        for _ in range(draws):
            running = unc = 0
            for kind, size in run:
                if rng.random() < yields.get(kind, 0.0):
                    unc += size
                    if running < cap:
                        running += size
                    else:
                        disc_raw += size
            got.append(running)
            hit += unc >= cap
            n += 1
    got.sort()
    return statistics.mean(got), got[int(0.9 * n)], 100 * hit / n, disc_raw / n


def replay_report(probe_all: list, rows: list, shadow: list, repo: Path, db_path: Path, limits: list, caps, max_clusters,
                  demote_cap: int = 0):
    ml = load_ml(repo)
    live_caps, live_max = dict(ml._KIND_BUCKET_CAP), ml._MAX_CLUSTERS
    # align shadow rows to runs by time window (a run's rows lie in (previous probe ts, this probe ts]); a cluster whose
    # distil call returned < 40 chars is formed but never logged, so a count mismatch is reported, not hidden
    idx_all = {id(r): i for i, r in enumerate(probe_all)}
    runs = []
    for r in rows:
        i = idx_all[id(r)]
        if i > 0:
            lo_t = probe_all[i - 1]["ts"]
            runs.append([s for s in shadow if lo_t < s["ts"] <= r["ts"] + 0.01])
        else:   # the file's very first probe row has no earlier probe row to bound it: take the last `clusters` shadow rows before it
            runs.append([s for s in shadow if s["ts"] <= r["ts"] + 0.01][-r["clusters"]:] if r["clusters"] else [])
    aligned = [len(ch) == r["clusters"] for ch, r in zip(runs, rows)]
    print(f"\n== REPLAY (zero-LLM, one-step; module caps live: {live_caps} max {live_max}) ==")
    print(f"shadow rows aligned to runs by time: {sum(aligned)}/{len(rows)} runs have shadow-row count == probe clusters")
    lo_ts = min(r["last_ts_before"] for r in rows) - 1.0
    hi_ts = max(r["ts"] for r in rows) + 5.0
    allrows = read_window_rows(db_path, ml._RAW_ORIGINS, lo_ts, hi_ts)
    tss = [x["timestamp"] for x in allrows]
    print(f"DB window rows (level-0, raw origins, cold included): {len(allrows)}; probe sum pool_size {sum(r['pool_size'] for r in rows)}")

    def pool_of(k):
        r, ch = rows[k], runs[k]
        first_ts = min(s["ts"] for s in ch) if ch else r["ts"]
        return allrows[bisect.bisect_right(tss, r["last_ts_before"]):bisect.bisect_right(tss, first_ts)]

    resid = [len(pool_of(k)) - rows[k]["pool_size"] for k in range(len(rows))]
    print(f"reconstructed pool minus probe pool_size per run: min {min(resid)} median {statistics.median(resid)} max {max(resid)}  (-1..+5 on the first read)")

    def run_cfg(L):
        out = []
        for k in range(len(rows)):
            pool = pool_of(k)
            window = sorted(pool, key=lambda x: -x["timestamp"])[:(L if L else len(pool))]
            out.append(ml._cluster(window))
        return out

    # validation at each row's OWN live limit (usually the same for every row)
    ml._KIND_BUCKET_CAP, ml._MAX_CLUSTERS = dict(live_caps), live_max
    ok_n = ok_kind = ok_set = n_val = 0
    for k, r in enumerate(rows):
        if not aligned[k]:
            continue
        pool = pool_of(k)
        cl = ml._cluster(sorted(pool, key=lambda x: -x["timestamp"])[:r["fetch_limit"]])
        act = runs[k]
        n_val += 1
        ok_n += len(cl) == len(act)
        ok_kind += collections.Counter(c[0] for c in cl) == collections.Counter(s["kind"] for s in act)
        ok_set += sorted(sorted(x["fragment_id"] for x in c[2]) for c in cl) == sorted(sorted(s["source_ids"]) for s in act)
    print(f"VALIDATION replaying each run at its own live fetch_limit vs the logged clusters ({n_val} aligned runs): "
          f"cluster count {ok_n}/{n_val}, per-kind counts {ok_kind}/{n_val}, exact source sets {ok_set}/{n_val}")
    trunc = [r["pool_size"] > r["fetch_limit"] for r in rows]
    yields = {}
    if demote_cap:
        for kd in ("self", "semantic", "episodic"):
            kr = [s for ch in runs for s in ch if s.get("kind") == kd]
            ok = [s for s in kr if isinstance(s.get("faithful"), (int, float)) and s["faithful"] >= ml.FAITHFUL_FLOOR
                  and not any((c[1] if isinstance(c, (list, tuple)) and len(c) > 1 else "") == "GENUINE" for c in (s.get("invented_claims") or []))]
            yields[kd] = len(ok) / len(kr) if kr else 0.0
        act = sorted(r["demoted"] for r in rows)
        print(f"commit-gate sim at cap {demote_cap}: observed per-kind commit rates {({k: round(v, 3) for k, v in yields.items()})}; "
              f"ACTUAL demoted/run mean {statistics.mean(act):.1f} p90 {act[min(len(act) - 1, int(0.9 * len(act)))]} max {act[-1]}")
    if caps:
        ml._KIND_BUCKET_CAP = {**live_caps, **caps}
    if max_clusters:
        ml._MAX_CLUSTERS = max_clusters
    print(f"replayed config: caps {ml._KIND_BUCKET_CAP}, max clusters {ml._MAX_CLUSTERS}")
    print("   L      clusters/run  sources/run | TRUNCATED runs (n=%d): clusters  sources  | NON-truncated (n=%d): clusters  sources | runs with >=10 clusters | self/sem/epi clusters per run | self/sem sources per run"
          % (sum(trunc), len(trunc) - sum(trunc)))
    base = None
    for L in limits:
        res = run_cfg(L)
        cl = [len(x) for x in res]
        src = [sum(len(c[2]) for c in x) for x in res]
        kc = collections.Counter(); ks = collections.Counter()
        for x in res:
            for c in x:
                kc[c[0]] += 1; ks[c[0]] += len(c[2])
        mean = lambda v, sel: statistics.mean(a for a, s in zip(v, sel) if s) if any(sel) else float("nan")
        t_sel, n_sel = trunc, [not t for t in trunc]
        n = len(rows)
        line = (f"  {('inf' if not L else str(L)):>4s}   {statistics.mean(cl):7.2f}       {statistics.mean(src):6.1f}     |      {mean(cl, t_sel):6.2f}  {mean(src, t_sel):7.1f}    |      {mean(cl, n_sel):6.2f}  {mean(src, n_sel):7.1f}   |   {sum(c >= 10 for c in cl):3d}   |  {kc['self']/n:.2f}/{kc['semantic']/n:.2f}/{kc['episodic']/n:.2f}  |  {ks['self']/n:5.1f}/{ks['semantic']/n:5.1f}")
        if base is None:
            base = (statistics.mean(cl), statistics.mean(src))
            print(line + "   (baseline)")
        else:
            print(line + f"   d_clusters {100*(statistics.mean(cl)/base[0]-1):+.1f}%  d_sources {100*(statistics.mean(src)/base[1]-1):+.1f}%")
        if demote_cap:
            m, p90, hitpct, disc = commit_gate_sim([[(c[0], len(c[2])) for c in x] for x in res], yields, demote_cap)
            print(f"        commit-gate sim @cap {demote_cap}: mean demoted/run {m:.1f}, p90 {p90}, runs whose uncapped eligible total >= cap {hitpct:.2f}%, "
                  f"eligible raw discarded by the cap {disc:.2f}/run")
    ml._KIND_BUCKET_CAP, ml._MAX_CLUSTERS = dict(live_caps), live_max


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--since", default=None, help='local time of the first run to include, "YYYY-MM-DD HH:MM:SS" (default: whole file)')
    ap.add_argument("--replay", action="store_true", help="also run the zero-LLM re-clustering counterfactual (reads the DB read-only)")
    ap.add_argument("--limits", default="160,320,500,720,0", help="fetch-window sizes to replay, comma list; 0 = unbounded; the first is the baseline")
    ap.add_argument("--caps", default="", help="in-memory override of _KIND_BUCKET_CAP, e.g. semantic=5,self=8,episodic=2")
    ap.add_argument("--max-clusters", type=int, default=0, help="in-memory override of _MAX_CLUSTERS for the replay")
    ap.add_argument("--demote-cap", type=int, default=0, help="also Monte-Carlo shadow_distill's commit gate at this MAX_DEMOTE_PER_RUN over each replayed config "
                    "(observed per-kind commit rates, independent draws); the baseline row should reproduce the logged demoted/run")
    ap.add_argument("--data-dir", default=None)
    ap.add_argument("--no-log", action="store_true", help="skip scanning data/nascence.log for restart markers")
    args = ap.parse_args()

    if args.replay and os.environ.get("PYTHONHASHSEED") != "0":
        env = dict(os.environ, PYTHONHASHSEED="0")
        return subprocess.call([sys.executable, os.path.abspath(sys.argv[0])] + sys.argv[1:], env=env)

    root = Path(__file__).resolve().parent.parent
    data = Path(args.data_dir) if args.data_dir else (root / "data" if (root / "data").exists() else Path(r"C:\Nascence\data"))
    repo = root if (root / "core" / "memory_levels.py").exists() else Path(r"C:\Nascence")
    probe_p, shadow_p = data / "memory_levels_fetch_probe.jsonl", data / "memory_levels_shadow.jsonl"
    probe_all = sorted(load_jsonl(probe_p), key=lambda r: r["ts"])
    since = _epoch(args.since) if args.since else 0.0
    rows = [r for r in probe_all if r["ts"] >= since]
    n_none = sum(r.get("pool_size") is None for r in rows)
    if n_none:
        print(f"WARNING: {n_none} row(s) have pool_size None (the probe's own COUNT failed) and are excluded below")
        rows = [r for r in rows if r.get("pool_size") is not None]
    if not rows:
        print(f"no usable probe rows at/after {args.since or 'the start'} in {probe_p} ({len(probe_all)} rows total)")
        return 1
    first_i = probe_all.index(rows[0])
    prev0 = probe_all[first_i - 1]["ts"] if first_i > 0 else None
    events = [] if args.no_log else restart_events(data / "nascence.log", rows[0]["ts"], rows[-1]["ts"])
    probe_report(rows, events, prev0)
    if args.replay:
        shadow = sorted(load_jsonl(shadow_p), key=lambda r: r["ts"])
        caps = {}
        for kv in filter(None, (x.strip() for x in args.caps.split(","))):
            kk, vv = kv.split("=")
            caps[kk.strip()] = int(vv)
        limits = [int(x) for x in args.limits.split(",") if x.strip() != ""]
        replay_report(probe_all, rows, shadow, repo, data / "memory" / "nascence.db", limits, caps, args.max_clusters, args.demote_cap)
    return 0


if __name__ == "__main__":
    sys.exit(main())
