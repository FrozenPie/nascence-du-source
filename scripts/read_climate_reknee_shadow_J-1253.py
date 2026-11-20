#!/usr/bin/env python
"""READ-ONLY reader for data/climate_reknee_shadow.jsonl (D-0211's shadow-first re-knee, built by J-1226 / F-1754).

Written for J-1253 (2026-10-03) so the next read of this log reuses a tool instead of re-deriving the method.
Touches NOTHING: every file is opened "rb", nothing is written unless --json-out is given. Safe to run while Du is
live: every input is snapshotted by byte size / --until-epoch at start, so the numbers are reproducible.

What it computes (the J-1253 briefing's three questions + the gate + the downstream consequences):
  GATE     live hours on the J-1226 build, from data/nascence.log's own "Nascence is awake" / "Nascence shutting down"
           lines (a boot that logged no shutdown line ends at the last log line before the NEXT boot's first line,
           i.e. its "Memory store initialised" line) -- strict live runtime, never calendar time (F-1568's rule).
  Q1/Q3    argmax distributions (live_dominant, reknee_dominant, among-the-4-cluster-dims), dominant-value / pressure
           spread (sd, percentiles), correlations of the raw scores, per-phase and per-day.
  Q2       completion_reknee by day (median / p90 / share > 0.90) + completion_raw change points.
  CONSUMERS what promotion would do to executive_hint() (>= 0.55), surfacing_symbol() (>= 0.65) and orchestrator beta
           (0.15 + 0.30 * pressure()) -- computed from the LOGGED values and constants read from core/.
  IGNITION fires per live day / defensive share in the live window (J-0671's F-1570 method).
  REPLAY   first-order replay of the DEFENSIVE dissonance reservoir (core/climate_engine._tick_dissonance) with the live
           knee vs the re-kneed values, validated on the live variant against the OBSERVED defensive fires;
           strain / integration_drive come from the 5-minute "[climate] dominant=..." telemetry lines (the shadow log
           does not carry them). --sweep adds a (k_shadow, k_completion) trade-off table.
  TENSION MASS (--tension-mass) why completion_raw steps down: the contradiction pressure carried by each tension-demotion
           burst in data/tensions_archive.jsonl (the 2026-09-25 drain of 632 tensions carried 24.63 of the ~30.3 plateau)
           and by the tensions still active today (3.00 at the 10-03 boot = that boot's completion_raw). Opens the live DB
           mode=ro and replicates core/tension_ledger.contradiction_pressure_for; read-only.

Findings recorded from it (2026-10-03): F-2264 (gate + discriminative range + hint/symbol/beta consequences),
F-2268 (completion_tension / D-0260: the raw collapsed because J-1276's tension-demotion fix drained 632 stale
tensions at the same restart), F-2270 (defensive-reservoir replay). Reproduce those exact numbers with
--until-epoch 1790964818.7 (2026-10-03 07:13:38.7 NZDT).

Usage:  python scripts/read_climate_reknee_shadow_J-1253.py [--data-dir DIR] [--until-epoch T] [--sweep] [--json-out F]
        (default data dir: ../data next to this script, else C:\\Nascence\\data)
"""
import argparse
import bisect
import datetime as dt
import json
import math
import os
import re
import statistics as st
import sys
from collections import Counter, defaultdict
from pathlib import Path

DIMS4 = ["shadow_activation", "belonging_pressure", "autonomy_pressure", "completion_tension"]
RAW = {"shadow_activation": "shadow_raw", "belonging_pressure": "belonging_raw", "autonomy_pressure": "autonomy_raw", "completion_tension": "completion_raw"}
RK = {"shadow_activation": "shadow_reknee", "belonging_pressure": "belonging_reknee", "autonomy_pressure": "autonomy_reknee", "completion_tension": "completion_reknee"}
# argmax tie-break order = ClimateField declaration order restricted to the four dims (max(dict, key=dict.get) keeps the first)
TIE_ORDER = ["shadow_activation", "completion_tension", "autonomy_pressure", "belonging_pressure"]
HINT_T, SYMBOL_T = 0.55, 0.65                 # core/climate_engine.py _HINT_THRESHOLD / _SYMBOL_THRESHOLD
BETA_BASE, BETA_RANGE = 0.15, 0.30            # core/orchestrator.py _CLIMATE_BETA_BASE / _CLIMATE_BETA_RANGE
RATE = {"strain": 0.0010, "completion": 0.0004, "shadow": 0.0002, "integration": -0.0006}   # _DISS_RATE_*
THRESH, REFRACT, DMAX, CAP_N, CAP_WIN = 1.0, 300.0, 2.0, 3, 3600.0                          # ignition threshold, refractory, cap
SAT_K = 3.0                                   # live shared knee

# ---------------------------------------------------------------------------------------------------------------
# NZ local time <-> epoch (the log is NZ local: NZST +12, NZDT +13 from the last Sunday of Sept 02:00 to the first
# Sunday of April 03:00). Hand-rolled so no tzdata package is needed on Windows.
# ---------------------------------------------------------------------------------------------------------------
def _dst_bounds(year):
    d = dt.date(year, 9, 30)
    while d.weekday() != 6:
        d -= dt.timedelta(days=1)
    start_local = dt.datetime(year, 9, d.day, 2, 0, 0)        # in NZST
    e = dt.date(year, 4, 1)
    while e.weekday() != 6:
        e += dt.timedelta(days=1)
    end_local = dt.datetime(year, 4, e.day, 3, 0, 0)          # in NZDT
    return start_local, end_local


def local_to_epoch(n):
    s, e = _dst_bounds(n.year)
    off = 13 if (n >= s or n < e) else 12
    return (n - dt.timedelta(hours=off)).replace(tzinfo=dt.timezone.utc).timestamp()


def epoch_to_local(ts):
    u = dt.datetime.fromtimestamp(ts, dt.timezone.utc).replace(tzinfo=None)
    s, e = _dst_bounds(u.year)
    s_utc, e_utc = s - dt.timedelta(hours=12), e - dt.timedelta(hours=13)
    off = 13 if (u >= s_utc or u < e_utc) else 12
    return u + dt.timedelta(hours=off)


def fmt(ts):
    return epoch_to_local(ts).strftime("%m-%d %H:%M:%S")


# ---------------------------------------------------------------------------------------------------------------
def pct(v, p):
    v = sorted(v)
    if not v:
        return float("nan")
    k = (len(v) - 1) * p
    f = int(k)
    c = min(f + 1, len(v) - 1)
    return v[f] + (v[c] - v[f]) * (k - f)


def sd(v):
    return st.pstdev(v) if len(v) > 1 else float("nan")


def summ(v, name):
    return (f"{name}: n={len(v)} mean={st.mean(v):.4f} sd={sd(v):.4f} min={min(v):.4f} p5={pct(v,.05):.4f} "
            f"p50={pct(v,.5):.4f} p95={pct(v,.95):.4f} max={max(v):.4f}")


def sat(raw, k):
    r = max(0.0, raw)
    return r / (r + k)


def corr(x, y):
    mx, my = st.mean(x), st.mean(y)
    sx = math.sqrt(sum((a - mx) ** 2 for a in x))
    sy = math.sqrt(sum((b - my) ** 2 for b in y))
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy) if sx and sy else float("nan")


def read_jsonl_snapshot(path, until_epoch=None):
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        data = f.read(size)
    data = data[: data.rfind(b"\n") + 1]
    rows, bad = [], 0
    for ln in data.split(b"\n"):
        if not ln.strip():
            continue
        try:
            r = json.loads(ln)
        except Exception:
            bad += 1
            continue
        if until_epoch is not None and r.get("ts", 0) > until_epoch:
            continue
        rows.append(r)
    return rows, {"bytes": len(data), "rows": len(rows), "bad_lines": bad}


# ---------------------------------------------------------------------------------------------------------------
# nascence.log: boundaries + telemetry in ONE pass
# ---------------------------------------------------------------------------------------------------------------
TEL_RE = re.compile(r"\[climate\] dominant=(\w+)\(([\d.]+)\) dissonance=([\d.]+) strain=([\d.]+) completion=([\d.]+) integration=([\d.]+)")
REST_RE = re.compile(r"\[climate\] restored field \+ dissonance \(value=([\d.]+)\)")


def parse_ts(line):
    # "2026-09-22 16:11:06,032 ..." -> naive local datetime or None
    if len(line) < 23 or line[4] != "-" or line[7] != "-" or line[10] != " " or line[13] != ":":
        return None
    try:
        return dt.datetime(int(line[0:4]), int(line[5:7]), int(line[8:10]), int(line[11:13]), int(line[14:16]), int(line[17:19]),
                           int(line[20:23]) * 1000)
    except Exception:
        return None


def scan_log(path, since_local, until_epoch=None):
    size = os.path.getsize(path)
    until_local = epoch_to_local(until_epoch) if until_epoch else None
    events, tel, restored = [], [], []
    mem_init = None
    prev_t = None
    n_lines = 0
    read = 0
    with open(path, "rb") as f:
        for raw in f:
            read += len(raw)
            if read > size:
                break
            n_lines += 1
            line = raw.decode("utf-8", errors="replace")
            t = parse_ts(line)
            if t is None:
                continue
            if until_local is not None and t > until_local:
                break
            if t >= since_local:
                if "Memory store initialised at" in line and "nascence.db" in line:
                    mem_init = (n_lines, t, prev_t)
                elif "Nascence is awake" in line:
                    first = mem_init if (mem_init and n_lines - mem_init[0] < 400) else None
                    events.append({"kind": "awake", "t": t, "prev_before_boot": first[2] if first else prev_t})
                elif "Nascence shutting down" in line:
                    events.append({"kind": "shutdown", "t": t})
                elif "[climate]" in line:
                    m = TEL_RE.search(line)
                    if m:
                        tel.append({"ts": local_to_epoch(t) + t.microsecond / 1e6, "dominant": m.group(1), "dom_val": float(m.group(2)),
                                    "dissonance": float(m.group(3)), "strain": float(m.group(4)), "completion": float(m.group(5)),
                                    "integration": float(m.group(6))})
                    else:
                        m = REST_RE.search(line)
                        if m:
                            restored.append({"ts": local_to_epoch(t) + t.microsecond / 1e6, "value": float(m.group(1))})
            prev_t = t
    return events, tel, restored, prev_t, {"bytes": size, "lines": n_lines}


def build_windows(events, last_line_t):
    wins, cur = [], None
    for e in events:
        if e["kind"] == "awake":
            if cur is not None and e["prev_before_boot"] is not None:
                wins.append((cur["t"], e["prev_before_boot"], "ended without a shutdown line (last log line before the next boot's first line)"))
            cur = e
        elif cur is not None:
            wins.append((cur["t"], e["t"], "clean shutdown line"))
            cur = None
    if cur is not None:
        wins.append((cur["t"], last_line_t, "STILL RUNNING at snapshot (to the last log line)"))
    out = []
    for s, e, why in wins:
        se, ee = local_to_epoch(s), local_to_epoch(e)
        out.append({"start": s.isoformat(), "end": e.isoformat(), "start_epoch": se, "end_epoch": ee, "hours": (ee - se) / 3600.0, "why": why})
    return out


# ---------------------------------------------------------------------------------------------------------------
def four_way(r, which):
    if which == "live":
        vals = {d: sat(r[RAW[d]], SAT_K) for d in DIMS4}
    else:
        vals = {d: r[RK[d]] for d in DIMS4}
    best = None
    for d in TIE_ORDER:
        if best is None or vals[d] > vals[best]:
            best = d
    return best


def share(c, n):
    return {k: f"{v} ({100.0 * v / n:.1f}%)" for k, v in c.most_common()}


def interp_factory(tel):
    ts = [x["ts"] for x in tel]

    def f(key, t):
        if not tel:
            return 0.0
        i = bisect.bisect_left(ts, t)
        if i <= 0:
            return tel[0][key]
        if i >= len(tel):
            return tel[-1][key]
        a, b = tel[i - 1], tel[i]
        if b["ts"] - a["ts"] > 1800:          # Du was off between the samples: hold the nearer one
            return a[key] if t - a["ts"] < b["ts"] - t else b[key]
        w = (t - a["ts"]) / (b["ts"] - a["ts"])
        return a[key] + w * (b[key] - a[key])
    return f


def replay(rows, wins, ign, tel, restored, ks=None, kc=None, reknee=False):
    """Defensive-reservoir free run per boot. ks/kc override the knees (live k=3); reknee=True uses the logged re-kneed values."""
    interp = interp_factory(tel)
    nd = 0
    per_boot = []
    for w in wins:
        rs = [r for r in rows if w["start_epoch"] - 5 <= r["ts"] <= w["end_epoch"] + 5]
        ex = sorted(r["ts"] for r in ign if r["trigger"] == "exploratory" and w["start_epoch"] <= r["ts"] <= w["end_epoch"])
        ex_i, n_boot = 0, 0
        value = 0.0
        for x in restored:
            if abs(x["ts"] - w["start_epoch"]) < 120:
                value = x["value"]
        last_ign, dft = -1e9, []
        prev = w["start_epoch"] + 5
        for r in rs:
            t = r["ts"]
            dtt = max(0.0, t - prev)
            prev = t
            while ex_i < len(ex) and ex[ex_i] <= t:
                last_ign = max(last_ign, ex[ex_i])
                ex_i += 1
            if reknee:
                sv, cv = r["shadow_reknee"], r["completion_reknee"]
            else:
                sv = sat(r["shadow_raw"], ks if ks else SAT_K)
                cv = sat(r["completion_raw"], kc if kc else SAT_K)
            delta = (RATE["strain"] * interp("strain", t) + RATE["completion"] * cv + RATE["shadow"] * sv
                     + RATE["integration"] * interp("integration", t)) * dtt
            value = max(0.0, min(DMAX, value + delta))
            if value >= THRESH and t - last_ign >= REFRACT:
                dft = [x for x in dft if x >= t - CAP_WIN]
                if len(dft) < CAP_N:
                    n_boot += 1
                    dft.append(t)
                    value = 0.0
                    last_ign = t
        per_boot.append(n_boot)
        nd += n_boot
    return nd, per_boot


# ---------------------------------------------------------------------------------------------------------------
def tension_mass(data_dir, now):
    """F-2268's mechanism check. completion_raw = core/tension_ledger.contradiction_pressure_for(active tensions) = sum over the
    active tensions of max(0, #member events with source critic_rejection (unresolved) / prediction_error - 30-day-half-life
    resolution drain). Tensions leave that list when nodes/subconscious_node.py demotes them to data/tensions_archive.jsonl
    (idle > 30 days, or resolved > 3 days; capped at 25 per scan since J-1276). So the contradiction pressure carried by each
    demotion BURST, and by the tensions still active today, explains the completion_raw steps. Read-only: archive and light
    sidecar opened 'rb', sqlite opened mode=ro."""
    import sqlite3
    arch = Path(data_dir) / "tensions_archive.jsonl"
    side = Path(data_dir) / "subconscious_state.light.json"
    dbp = Path(data_dir) / "memory" / "nascence.db"
    if not (arch.exists() and side.exists() and dbp.exists()):
        print("  (tension-mass: archive / light sidecar / db not all present, skipped)")
        return
    data = arch.read_bytes()
    rows = [json.loads(x) for x in data[: data.rfind(b"\n") + 1].split(b"\n") if x.strip()]
    rows = [r for r in rows if isinstance(r.get("_demoted_ts"), (int, float))]
    rows.sort(key=lambda r: r["_demoted_ts"])
    src = (Path(data_dir).parent / "core" / "memory" / "store.py")
    half = 30 * 86400
    if src.exists():
        m = re.search(r"^RESOLUTION_HALFLIFE_SECS\s*=\s*([\d\s\*]+)", src.read_text(encoding="utf-8"), re.M)
        if m:
            half = eval(m.group(1).strip(), {"__builtins__": {}})
    con = sqlite3.connect("file:" + str(dbp).replace("\\", "/") + "?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    contra = ("critic_rejection", "prediction_error")

    def pressure(tensions):
        ids = list(dict.fromkeys(e for t in tensions for e in (t.get("member_event_ids") or [])))
        srcmap, drain = {}, {}
        for i in range(0, len(ids), 500):
            chunk = ids[i:i + 500]
            ph = ",".join("?" * len(chunk))
            for r in con.execute(f"SELECT event_id, source, resolved FROM shadow_events WHERE event_id IN ({ph})", tuple(chunk)):
                s = r["source"]
                srcmap[r["event_id"]] = "critic_rejection_resolved" if (r["resolved"] and s == "critic_rejection") else s
            for r in con.execute(f"SELECT shadow_event_id, encounter_similarity, timestamp FROM resolution_events WHERE shadow_event_id IN ({ph})", tuple(chunk)):
                drain[r["shadow_event_id"]] = drain.get(r["shadow_event_id"], 0.0) + float(r["encounter_similarity"]) * 0.5 ** (max(0.0, now - float(r["timestamp"])) / half)
        tot, nev = 0.0, 0
        for t in tensions:
            ce = [e for e in (t.get("member_event_ids") or []) if srcmap.get(e) in contra]
            tot += max(0.0, len(ce) - sum(drain.get(e, 0.0) for e in ce))
            nev += len(ce)
        return tot, nev

    print("  demotion BURSTS in data/tensions_archive.jsonl (gap > 2 h starts a new burst) and the contradiction pressure each carried:")
    bursts, cur = [], [rows[0]] if rows else []
    for a, b in zip(rows, rows[1:]):
        if b["_demoted_ts"] - a["_demoted_ts"] > 7200:
            bursts.append(cur)
            cur = []
        cur.append(b)
    if cur:
        bursts.append(cur)
    for b in bursts:
        if len(b) < 5 and len(bursts) > 6:
            continue
        tot, nev = pressure(b)
        why = Counter(r.get("_demoted_why") for r in b)
        print(f"    {fmt(b[0]['_demoted_ts'])} .. {fmt(b[-1]['_demoted_ts'])}: tensions={len(b)} pressure sum={tot:.2f} (events={nev}) reasons={dict(why)}")
    small = [r for b in bursts if len(b) < 5 for r in b]
    if small and len(bursts) > 6:
        tot, nev = pressure(small)
        print(f"    (all bursts of < 5 tensions together: tensions={len(small)} pressure sum={tot:.2f} events={nev})")
    sc = json.loads(side.read_bytes().decode("utf-8", errors="replace"))
    tens = sc.get("tensions", [])
    tot, nev = pressure(tens)
    print(f"  ACTIVE tensions in subconscious_state.light.json: n={len(tens)} contradiction pressure sum={tot:.2f} (events={nev})  <- should equal the newest completion_raw")
    con.close()


# ---------------------------------------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    here = Path(__file__).resolve().parent.parent / "data"
    ap.add_argument("--data-dir", default=str(here if (here / "nascence.log").exists() else Path(r"C:\Nascence\data")))
    ap.add_argument("--until-epoch", type=float, default=None, help="ignore everything after this epoch (reproduce a cited snapshot)")
    ap.add_argument("--sweep", action="store_true", help="add the (k_shadow, k_completion) reservoir trade-off table")
    ap.add_argument("--no-replay", action="store_true")
    ap.add_argument("--v2", action="store_true", help="J-2137: label-view section for schema v=2 rows (real per-row k, lv_dominant, ge firing grid, switch rates)")
    ap.add_argument("--tension-mass", action="store_true", help="F-2268 check: contradiction pressure carried by each tension-demotion burst and by the active pool (opens the live DB mode=ro)")
    ap.add_argument("--json-out", default=None)
    a = ap.parse_args()
    D = Path(a.data_dir)
    sys.stdout.reconfigure(encoding="utf-8")

    rows, rmeta = read_jsonl_snapshot(D / "climate_reknee_shadow.jsonl", a.until_epoch)
    if not rows:
        print("no rows in climate_reknee_shadow.jsonl (Du has not run on the J-1226 build yet) -> gate NOT met, 0 live hours")
        return 0
    first_ts, last_ts = rows[0]["ts"], rows[-1]["ts"]
    print(f"SHADOW LOG snapshot: {rmeta} first={fmt(first_ts)} last={fmt(last_ts)} (NZ local)")
    keys = {tuple(sorted(r.keys())) for r in rows}
    print(f"distinct key-sets: {len(keys)}; non-monotonic ts: {sum(1 for x, y in zip(rows, rows[1:]) if y['ts'] < x['ts'])}")

    # ---- GATE -------------------------------------------------------------------------------------------------
    since_local = epoch_to_local(first_ts - 36 * 3600)
    events, tel, restored, last_line_t, lmeta = scan_log(D / "nascence.log", since_local, a.until_epoch)
    wins_all = build_windows(events, last_line_t)
    build_wins = [w for w in wins_all if w["end_epoch"] >= first_ts - 5 and w["start_epoch"] >= first_ts - 600]
    live_h = sum(w["hours"] for w in build_wins)
    print(f"\nGATE (nascence.log {lmeta}, last line {last_line_t}):")
    for w in build_wins:
        print(f"  {w['start']} -> {w['end']}  {w['hours']:8.3f} h  {w['why']}")
    print(f"  LIVE HOURS on the build: {live_h:.2f} h = {live_h/24:.3f} live days (shadow-row count x ~63 s = {len(rows)*63/3600:.1f} h)")

    # ---- phases ----------------------------------------------------------------------------------------------
    cur_boot_ts = build_wins[-1]["start_epoch"] - 5 if (build_wins and build_wins[-1]["why"].startswith("STILL")) else float("inf")
    settle_ts = next((r["ts"] for r in rows if r["completion_raw"] <= 6.0), None)
    phases = {
        "ALL rows": rows,
        "excl. a still-running cold-start boot": [r for r in rows if r["ts"] < cur_boot_ts],
        "steady state (completion_raw first <= 6.0 onward, excl. cold-start boot)": [r for r in rows if (settle_ts or 0) <= r["ts"] < cur_boot_ts],
        "before completion settled": [r for r in rows if settle_ts and r["ts"] < settle_ts],
        "still-running cold-start boot only": [r for r in rows if r["ts"] >= cur_boot_ts],
    }
    summary = {"gate": {"live_hours": live_h, "live_days": live_h / 24, "rows": len(rows)}}
    for name, rs in phases.items():
        if not rs:
            continue
        n = len(rs)
        print("\n" + "=" * 110)
        print(f"PHASE: {name}  n={n}  {fmt(rs[0]['ts'])} .. {fmt(rs[-1]['ts'])}")
        print("  live_dominant (9-dim, logged):          ", share(Counter(r["live_dominant"] for r in rs), n))
        print("  reknee_dominant (hybrid 9-dim, logged): ", share(Counter(r["reknee_dominant"] for r in rs), n))
        print("  argmax of the 4 cluster dims, LIVE knee k=3 (raw/(raw+3)):", share(Counter(four_way(r, "live") for r in rs), n))
        print("  argmax of the 4 cluster dims, RE-KNEED (logged):          ", share(Counter(four_way(r, "reknee") for r in rs), n))
        c3 = Counter()
        for r in rs:
            c3[max(("shadow_activation", "autonomy_pressure", "belonging_pressure"), key=lambda d: (r[RK[d]], -("shadow_activation", "autonomy_pressure", "belonging_pressure").index(d)))] += 1
        print("  argmax of shadow/belonging/autonomy only, RE-KNEED:       ", share(c3, n))
        for key in ("live_dominant_val", "reknee_dominant_val", "live_pressure", "reknee_pressure"):
            print("  " + summ([r[key] for r in rs], f"{key:20s}"))
        for d in DIMS4:
            print("  " + summ([r[RK[d]] for r in rs], f"{RK[d]:20s}"))
        g95 = sum(1 for r in rs if r["live_dominant_val"] >= 0.95)
        g90 = sum(1 for r in rs if r["live_dominant_val"] >= 0.90)
        rg90 = sum(1 for r in rs if r["reknee_dominant_val"] >= 0.90)
        print(f"  live_dominant_val >=0.95: {g95} ({100*g95/n:.1f}%) >=0.90: {g90} ({100*g90/n:.1f}%) | reknee_dominant_val >=0.90: {rg90} ({100*rg90/n:.1f}%)")
        sw = sum(1 for x, y in zip(rs, rs[1:]) if y["ts"] - x["ts"] <= 300 and x["reknee_dominant"] != y["reknee_dominant"])
        tot = sum(1 for x, y in zip(rs, rs[1:]) if y["ts"] - x["ts"] <= 300)
        print(f"  reknee_dominant switches between consecutive rows: {sw}/{tot} ({100*sw/max(tot,1):.1f}%)")
        if name.startswith("excl."):
            summary["phase_excl_cold_start"] = {
                "n": n, "live_dominant": dict(Counter(r["live_dominant"] for r in rs)),
                "reknee_dominant": dict(Counter(r["reknee_dominant"] for r in rs)),
                "argmax4_live": dict(Counter(four_way(r, "live") for r in rs)), "argmax4_reknee": dict(Counter(four_way(r, "reknee") for r in rs)),
                "live_dominant_val_mean_sd": [st.mean(r["live_dominant_val"] for r in rs), sd([r["live_dominant_val"] for r in rs])],
                "reknee_dominant_val_mean_sd": [st.mean(r["reknee_dominant_val"] for r in rs), sd([r["reknee_dominant_val"] for r in rs])],
                "live_pressure_mean_sd": [st.mean(r["live_pressure"] for r in rs), sd([r["live_pressure"] for r in rs])],
                "reknee_pressure_mean_sd": [st.mean(r["reknee_pressure"] for r in rs), sd([r["reknee_pressure"] for r in rs])]}

    rs = phases["excl. a still-running cold-start boot"]
    print("\nCORRELATIONS of the raw scores (rows excl. cold-start boot) -- three views of ONE 200-event window:")
    for x, y in (("shadow_raw", "belonging_raw"), ("shadow_raw", "autonomy_raw"), ("belonging_raw", "autonomy_raw"), ("shadow_raw", "completion_raw")):
        print(f"  corr({x}, {y}) = {corr([r[x] for r in rs], [r[y] for r in rs]):.4f}")
    ok = [r for r in rs if r["shadow_raw"] > 1]
    print("  belonging/shadow raw ratio: median %.3f p5 %.3f p95 %.3f (k ratio 85/119 = 0.714)" % (
        st.median(r["belonging_raw"] / r["shadow_raw"] for r in ok), pct([r["belonging_raw"] / r["shadow_raw"] for r in ok], .05), pct([r["belonging_raw"] / r["shadow_raw"] for r in ok], .95)))
    print("  autonomy/shadow raw ratio:  median %.3f p5 %.3f p95 %.3f (k ratio 33/119 = 0.277)" % (
        st.median(r["autonomy_raw"] / r["shadow_raw"] for r in ok), pct([r["autonomy_raw"] / r["shadow_raw"] for r in ok], .05), pct([r["autonomy_raw"] / r["shadow_raw"] for r in ok], .95)))
    print("  raw medians: shadow %.2f belonging %.2f autonomy %.2f completion %.2f   (built-in k: 119 / 85 / 33 / 30)" % tuple(
        st.median(r[k] for r in rs) for k in ("shadow_raw", "belonging_raw", "autonomy_raw", "completion_raw")))

    # ---- Q2 per day --------------------------------------------------------------------------------------------
    print("\n" + "=" * 110)
    print("Q2 / PER DAY (NZ local): completion_reknee median / p90 / share>0.90 | completion_raw median | live completion (k=3) median")
    byday = defaultdict(list)
    for r in rows:
        byday[epoch_to_local(r["ts"]).strftime("%Y-%m-%d")].append(r)
    for day in sorted(byday):
        x = byday[day]
        cr = [r["completion_reknee"] for r in x]
        craw = [r["completion_raw"] for r in x]
        c4 = Counter(four_way(r, "reknee").split("_")[0] for r in x)
        crk = Counter(r["reknee_dominant"] for r in x)
        lv = [r["live_dominant_val"] for r in x]
        rv = [r["reknee_dominant_val"] for r in x]
        print(f"  {day} n={len(x):4d} | compl_reknee med={st.median(cr):.3f} p90={pct(cr,.9):.3f} >0.90:{sum(1 for v in cr if v>0.9)} | compl_raw med={st.median(craw):.1f} live_med={st.median([sat(v,SAT_K) for v in craw]):.3f}"
              f" | dom_val live {st.mean(lv):.4f}+-{sd(lv):.4f} reknee {st.mean(rv):.4f}+-{sd(rv):.4f} | 4way={dict(c4)} | reknee_dom={dict(crk)}")
    print("\ncompletion_raw change points (first 25):")
    prev, k = None, 0
    for r in rows:
        if prev is None or r["completion_raw"] != prev:
            k += 1
            if k <= 25:
                print("   ", fmt(r["ts"]), prev, "->", r["completion_raw"])
            prev = r["completion_raw"]

    # ---- v=2 label view (J-2137, opt-in: legacy output above/below is untouched) -------------------------------
    if a.v2:
        v2rows = [r for r in rows if r.get("v") == 2 and r["ts"] < cur_boot_ts]
        print("\n" + "=" * 110)
        print(f"LABEL VIEW (schema v=2, excl. still-running cold-start boot): n={len(v2rows)} of {len(rows)} rows")
        if v2rows:
            ks = Counter(json.dumps(r.get("k"), sort_keys=True) for r in v2rows)
            print("  per-row k (REAL knees logged, replaces the stale built-in k=3 line above):", dict(ks))
            print("  lv_dominant:", share(Counter(r["lv_dominant"] for r in v2rows), len(v2rows)))
            lv = [r["lv_dominant_val"] for r in v2rows]
            print(f"  lv_dominant_val: mean {st.mean(lv):.4f} p05 {pct(lv,.05):.4f} p50 {pct(lv,.5):.4f} p95 {pct(lv,.95):.4f} max {max(lv):.4f}")
            grid = sorted({t for r in v2rows for t in r.get("ge", {})}, key=float)
            print("  ge would-fire share per threshold (grid as logged; coarser rows lack the finer keys, n shown):")
            for t in grid:
                have = [r for r in v2rows if t in r.get("ge", {})]
                f = sum(r["ge"][t] for r in have)
                print(f"    >= {t}: {f}/{len(have)} ({100*f/max(len(have),1):.1f}%)")
            hrs = max((v2rows[-1]["ts"] - v2rows[0]["ts"]) / 3600, 1e-9)
            sw = sum(1 for x, y in zip(v2rows, v2rows[1:]) if y["ts"] - x["ts"] <= 300 and x["lv_dominant"] != y["lv_dominant"])
            sw_nc = sum(1 for x, y in zip(v2rows, v2rows[1:]) if y["ts"] - x["ts"] <= 300
                        and (x["lv_dominant"] != y["lv_dominant"]) and "completion_tension" not in (x["lv_dominant"], y["lv_dominant"]))
            print(f"  lv_dominant switches: {sw} total ({sw/hrs:.2f}/h wall span), {sw_nc} not involving completion_tension ({sw_nc/hrs:.2f}/h)")

    # ---- consumers ----------------------------------------------------------------------------------------------
    print("\n" + "=" * 110)
    print("CONSUMERS (rows excl. cold-start boot): what promotion as built would do to hint / symbol / beta")
    n = len(rs)
    for lab, key in (("LIVE", "live_dominant_val"), ("RE-KNEE", "reknee_dominant_val")):
        h = sum(1 for r in rs if r[key] >= HINT_T)
        s = sum(1 for r in rs if r[key] >= SYMBOL_T)
        print(f"  {lab:8s} executive_hint (>= {HINT_T}): {h} ({100*h/n:.1f}%)   surfacing_symbol (>= {SYMBOL_T}): {s} ({100*s/n:.1f}%)   max {max(r[key] for r in rs):.4f}")
    print("  re-knee hint would come from:", dict(Counter(r["reknee_dominant"] for r in rs if r["reknee_dominant_val"] >= HINT_T)))
    for lab, key in (("LIVE", "live_pressure"), ("RE-KNEE", "reknee_pressure")):
        b = [BETA_BASE + BETA_RANGE * r[key] for r in rs]
        print(f"  beta {lab:8s}: mean {st.mean(b):.3f} sd {sd(b):.3f} min {min(b):.3f} max {max(b):.3f}")

    # ---- ignition rate -----------------------------------------------------------------------------------------
    ign = []
    ipath = D / "ignition_log.jsonl"
    if ipath.exists():
        ign, imeta = read_jsonl_snapshot(ipath, a.until_epoch)
        ign = [r for r in ign if r.get("trigger") != "deferred"]   # J-2667
        sel = [r for r in ign if any(w["start_epoch"] <= r["ts"] <= w["end_epoch"] for w in build_wins)]
        c = Counter(r["trigger"] for r in sel)
        fires = c.get("defensive", 0) + c.get("exploratory", 0)
        days = live_h / 24
        print("\n" + "=" * 110)
        print(f"IGNITION in the live window ({imeta}): {dict(c)} -> {fires/days:.2f} fires per live day "
              f"(defensive {c.get('defensive',0)/days:.2f}, exploratory {c.get('exploratory',0)/days:.2f}); defensive share {100*c.get('defensive',0)/max(fires,1):.1f}%"
              f"   [J-0671 reference on the pre-demotion-fix code: 62.65 per live day, 48.2% defensive]")
        summary["ignition"] = {"fires_per_live_day": fires / days, "defensive_per_live_day": c.get("defensive", 0) / days, "defensive_share": c.get("defensive", 0) / max(fires, 1)}

    # ---- replay ------------------------------------------------------------------------------------------------
    if not a.no_replay and ign and tel:
        print("\n" + "=" * 110)
        print("REPLAY of the DEFENSIVE reservoir (first-order; strain/integration from [climate] telemetry; observed exploratory fires as refractory events)")
        days = live_h / 24
        n_exp = sum(1 for r in ign if r["trigger"] == "exploratory" and any(w["start_epoch"] <= r["ts"] <= w["end_epoch"] for w in build_wins))
        obs_def = sum(1 for r in ign if r["trigger"] == "defensive" and any(w["start_epoch"] <= r["ts"] <= w["end_epoch"] for w in build_wins))
        nd_l, pb_l = replay(rows, build_wins, ign, tel, restored)
        nd_r, pb_r = replay(rows, build_wins, ign, tel, restored, reknee=True)
        print(f"  OBSERVED defensive fires: {obs_def} ({obs_def/days:.1f}/live day)   exploratory (observed, unaffected by the re-knee): {n_exp} ({n_exp/days:.1f}/live day)")
        print(f"  SIM LIVE   : defensive {nd_l} ({nd_l/days:.1f}/day) per-boot {pb_l} | total {(nd_l+n_exp)/days:.1f}/day | defensive share {100*nd_l/(nd_l+n_exp):.1f}%   <- validation: should be close to OBSERVED")
        print(f"  SIM REKNEE : defensive {nd_r} ({nd_r/days:.1f}/day) per-boot {pb_r} | total {(nd_r+n_exp)/days:.1f}/day | defensive share {100*nd_r/(nd_r+n_exp):.1f}%")
        interp = interp_factory(tel)
        for lab, rv in (("live", False), ("reknee", True)):
            terms = []
            for r in rs:
                sv = r["shadow_reknee"] if rv else sat(r["shadow_raw"], SAT_K)
                cv = r["completion_reknee"] if rv else sat(r["completion_raw"], SAT_K)
                terms.append((RATE["strain"] * interp("strain", r["ts"]), RATE["completion"] * cv, RATE["shadow"] * sv, RATE["integration"] * interp("integration", r["ts"])))
            m = [st.mean(t[i] for t in terms) for i in range(4)]
            print(f"  mean inflow/s [{lab:6s}]: strain {m[0]:.6f} completion {m[1]:.6f} shadow {m[2]:.6f} bleed {m[3]:.6f} NET {sum(m):+.6f}")
        summary["replay"] = {"observed_defensive": obs_def, "sim_live_defensive": nd_l, "sim_reknee_defensive": nd_r, "exploratory": n_exp, "live_days": days}
        if a.sweep:
            print("\n  SWEEP  k_shadow k_completion | defensive/day  total/day  defensive share   (k=3,3 is the live knee)")
            for ks in (3, 10, 20, 30, 50, 80, 119):
                for kc in (3, 10, 30):
                    nd, _ = replay(rows, build_wins, ign, tel, restored, ks=float(ks), kc=float(kc))
                    print(f"         {ks:6d} {kc:6d}        |  {nd/days:6.1f}      {(nd+n_exp)/days:6.1f}      {100*nd/(nd+n_exp):5.1f}%")
    if a.tension_mass:
        print("\n" + "=" * 110)
        print("TENSION MASS (why completion_raw steps down: demotion bursts drain stale tensions out of the active list)")
        tension_mass(D, a.until_epoch or __import__("time").time())
    if a.json_out:
        with open(a.json_out, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=1, default=str)
    return 0


if __name__ == "__main__":
    sys.exit(main())
