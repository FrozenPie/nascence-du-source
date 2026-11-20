"""
coalition_mining_read.py -- J-2531 (I-0109, F-3224 direction 19, plan dosed_coupling).

Read-only. Which dosed reads (reader stop <- source line) were present together in the window before each
outcome class, and is that more often than at random live moments? Writes NOTHING under data/; prints a
report and, with --out PATH, writes the JSON result there (the caller's scratch dir). Zero LLM. Nothing here
reaches Du (D-0434) and no coalition is reinforced (a positive result opens a /decide question instead).

EVERY THRESHOLD BELOW WAS DECLARED BEFORE THE FIRST RUN (2026-10-30, J-2531) AND IS NOT TUNED TO THE RESULT.

ITEMS (the alphabet a read-set is built from), from data/coupling_rides.jsonl:
  "<stop><-<line>:ride"        a kind=ride row whose value is NON-EMPTY (a coordinate was actually delivered;
                               an empty witness cup is an attempt, not a read, and is excluded)
  "<stop><-<line>:fire"        a kind=probe row where any gate has residual_fire or spike_fire true
                               (shadow: the read WOULD have been dispatched by surprise)
  "mid-thread step<-si:would"  a kind=si_would_ride row with eligible true
  Standing (dose=standing) hub probes and non-firing probes fire on a fixed clock and carry no choice; excluded.

OUTCOME CLASSES (timestamp = when it happened):
  deed_done / deed_lapsed      data/intentions_log.jsonl event=done / event=lapsed
  craft_ok / craft_fail        data/fieldcraft_ledger.jsonl rows with ok true / ok false
  wager                        data/logs/recall_wager_shadow.jsonl, every row
  dream_met                    data/logs/dream_met_state.jsonl state=met, first per dream_id, at arc_ts
  correction                   data/provenance_log.jsonl input_type=human and contradiction_count>=1 (proxy for a
                               live social correction: epistemic_state sets contradiction=1 when delta_social>0.3)
  pursuit_advance              data/pursuits_series.jsonl rows whose cumulative advances rose vs the previous row
  (curiosity_progress has no timestamped event log -- it lives in frontier.json state; not available.)

METHOD: analysis period = [first probe row, last ride-log row] (the full alphabet exists only after probes
began). A moment t is LIVE if any coupling_rides row lies in (t-LIVE_GAP_S, t]; only live outcomes count.
Read-set(t) = items with a row in (t-WINDOW_S, t]. For every coalition C (an itemset; size>=2 is a coalition,
size 1 is reported for context) support k = #outcomes whose read-set contains C. Null: N_SHUFFLES draws of the
same number of outcome times, uniform over live 60-s buckets of the same half (uniform offset in bucket);
lift = k / mean(k_null); p = (1 + #(k_null >= k)) / (1 + N_SHUFFLES).
The period is split at its time midpoint; each half gets its own null.
PASS (a recurring coalition) iff on BOTH halves: lift >= LIFT_MIN and k >= K_MIN and p <= P_MAX.
FALSIFIED (the briefing's null) iff no size>=2 coalition passes for any outcome class.
INSUFFICIENT iff ride+probe item rows < MIN_ITEM_ROWS or distinct 60-s item buckets < MIN_ITEM_TICKS.
"""
from __future__ import annotations

import argparse
import bisect
import json
import random
import sys
from itertools import combinations
from pathlib import Path

# ---- declared before the first run (J-2531) ----
WINDOW_S = 600.0
LIVE_GAP_S = 300.0
N_SHUFFLES = 1000
LIFT_MIN = 1.5
K_MIN = 5
P_MAX = 0.05
MIN_ITEM_ROWS = 2000
MIN_ITEM_TICKS = 1000
SEED = 2531
# -----------------------------------------------


def _rows(path: Path):
    if not path.exists():
        return
    with path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                yield json.loads(line)
            except Exception:
                continue


def load_items(data: Path):
    items: dict[str, list[float]] = {}
    all_ts: list[float] = []
    first_probe = None
    for r in _rows(data / "coupling_rides.jsonl"):
        ts = r.get("ts")
        if not isinstance(ts, (int, float)):
            continue
        all_ts.append(float(ts))
        k = r.get("kind")
        name = None
        if k == "ride" and r.get("value"):
            name = f"{r.get('stop')}<-{r.get('line')}:ride"
        elif k == "probe":
            first_probe = ts if first_probe is None else min(first_probe, ts)
            g = r.get("gates") or {}
            if any(isinstance(v, dict) and (v.get("residual_fire") or v.get("spike_fire")) for v in g.values()):
                name = f"{r.get('stop')}<-{r.get('line')}:fire"
        elif k == "si_would_ride" and r.get("eligible"):
            name = f"{r.get('stop')}<-{r.get('line')}:would"
        if name:
            items.setdefault(name, []).append(float(ts))
    for v in items.values():
        v.sort()
    all_ts.sort()
    return items, all_ts, first_probe


def load_outcomes(data: Path) -> dict[str, list[float]]:
    out: dict[str, list[float]] = {k: [] for k in (
        "deed_done", "deed_lapsed", "craft_ok", "craft_fail", "wager", "dream_met", "correction", "pursuit_advance")}
    for r in _rows(data / "intentions_log.jsonl"):
        if r.get("event") == "done":
            out["deed_done"].append(r["ts"])
        elif r.get("event") == "lapsed":
            out["deed_lapsed"].append(r["ts"])
    for r in _rows(data / "fieldcraft_ledger.jsonl"):
        if r.get("ok") is True:
            out["craft_ok"].append(r["ts"])
        elif r.get("ok") is False:
            out["craft_fail"].append(r["ts"])
    for r in _rows(data / "logs" / "recall_wager_shadow.jsonl"):
        out["wager"].append(r["ts"])
    seen = set()
    for r in _rows(data / "logs" / "dream_met_state.jsonl"):
        if r.get("state") == "met" and r.get("dream_id") not in seen and isinstance(r.get("arc_ts"), (int, float)):
            seen.add(r.get("dream_id"))
            out["dream_met"].append(r["arc_ts"])
    for r in _rows(data / "provenance_log.jsonl"):
        if r.get("input_type") == "human" and (r.get("contradiction_count") or 0) >= 1:
            out["correction"].append(r["ts"])
    prev = None
    for r in _rows(data / "pursuits_series.jsonl"):
        a = r.get("advances")
        if isinstance(a, (int, float)):
            if prev is not None and a > prev:
                out["pursuit_advance"].append(r["ts"])
            prev = a
    return {k: sorted(float(t) for t in v if isinstance(t, (int, float))) for k, v in out.items()}


def present(ts_list: list[float], t: float, w: float) -> bool:
    i = bisect.bisect_right(ts_list, t)
    return i > 0 and ts_list[i - 1] > t - w


def mask_at(t, names, items):
    m = 0
    for b, n in enumerate(names):
        if present(items[n], t, WINDOW_S):
            m |= 1 << b
    return m


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(Path(__file__).resolve().parent.parent / "data"))
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    data = Path(a.data)
    items, all_ts, first_probe = load_items(data)
    n_item_rows = sum(len(v) for v in items.values())
    n_ticks = len({int(t // 60) for v in items.values() for t in v})
    res = {"declared": dict(WINDOW_S=WINDOW_S, LIVE_GAP_S=LIVE_GAP_S, N_SHUFFLES=N_SHUFFLES, LIFT_MIN=LIFT_MIN,
                            K_MIN=K_MIN, P_MAX=P_MAX, MIN_ITEM_ROWS=MIN_ITEM_ROWS, MIN_ITEM_TICKS=MIN_ITEM_TICKS,
                            SEED=SEED),
           "items": {k: len(v) for k, v in items.items()}, "item_rows": n_item_rows, "item_ticks_60s": n_ticks}
    if n_item_rows < MIN_ITEM_ROWS or n_ticks < MIN_ITEM_TICKS or first_probe is None:
        res["verdict"] = "INSUFFICIENT"
        print(json.dumps(res, indent=1))
        return 0
    start, end = float(first_probe), all_ts[-1]
    mid = (start + end) / 2
    res["period"] = [start, mid, end]
    names = sorted(items)
    live_buckets = sorted({int(t // 60) for t in all_ts if start <= t <= end})

    def is_live(t):
        return present(all_ts, t, LIVE_GAP_S)

    outcomes = load_outcomes(data)
    rng = random.Random(SEED)
    halves = [(start, mid), (mid, end)]
    half_buckets = [[b for b in live_buckets if lo <= b * 60 < hi] for lo, hi in halves]
    # null masks: per half, a pool of live random moments, reused across classes (same seed, declared)
    pool = []
    for hb in half_buckets:
        ms = []
        while len(ms) < 20000:
            t = (rng.choice(hb) * 60) + rng.random() * 60
            if is_live(t):
                ms.append(mask_at(t, names, items))
        pool.append(ms)
    res["classes"] = {}
    passing = []
    for cls, tss in outcomes.items():
        info = {"n_raw": len(tss)}
        per_half = []
        for h, (lo, hi) in enumerate(halves):
            obs = [(t, mask_at(t, names, items)) for t in tss if lo <= t < hi and is_live(t)]
            per_half.append(obs)
        info["n_live_by_half"] = [len(o) for o in per_half]
        # candidate coalitions: every itemset seen in any observed read-set
        cands = set()
        for o in per_half:
            for _, m in o:
                bits = [b for b in range(len(names)) if m >> b & 1]
                for r in range(1, len(bits) + 1):
                    for c in combinations(bits, r):
                        cands.add(sum(1 << b for b in c))
        exact = {}
        for o in per_half:
            for _, m in o:
                key = "+".join(names[b] for b in range(len(names)) if m >> b & 1) or "(none)"
                exact[key] = exact.get(key, 0) + 1
        info["exact_readsets"] = dict(sorted(exact.items(), key=lambda x: -x[1]))
        # one set of shuffle draws per half for this class (same draws scored for every coalition)
        draws = []
        for h, o in enumerate(per_half):
            n = len(o)
            dh = []
            for _ in range(N_SHUFFLES if n else 0):
                cnt: dict[int, int] = {}
                for m in rng.sample(pool[h], n):
                    cnt[m] = cnt.get(m, 0) + 1
                dh.append(cnt)
            draws.append(dh)
        rows = []
        for c in sorted(cands):
            entry = {"coalition": [names[b] for b in range(len(names)) if c >> b & 1], "halves": []}
            ok_all = True
            for h, o in enumerate(per_half):
                n = len(o)
                k = sum(1 for _, m in o if m & c == c)
                if n == 0:
                    entry["halves"].append({"n": 0, "k": 0, "lift": None, "p": None})
                    ok_all = False
                    continue
                ks = [sum(v for m, v in cnt.items() if m & c == c) for cnt in draws[h]]
                mean = sum(ks) / len(ks)
                lift = (k / mean) if mean > 0 else (float("inf") if k > 0 else None)
                p = (1 + sum(1 for x in ks if x >= k)) / (1 + N_SHUFFLES)
                ex = [round(t, 1) for t, m in o if m & c == c][:3]
                entry["halves"].append({"n": n, "k": k, "null_mean": round(mean, 2),
                                        "lift": None if lift is None else round(lift, 3), "p": round(p, 4),
                                        "examples_ts": ex})
                if not (lift is not None and lift >= LIFT_MIN and k >= K_MIN and p <= P_MAX):
                    ok_all = False
            entry["pass"] = ok_all
            rows.append(entry)
            if ok_all and len(entry["coalition"]) >= 2:
                passing.append((cls, entry))
        info["coalitions"] = rows
        res["classes"][cls] = info
    res["passing_coalitions"] = [{"class": c, **e} for c, e in passing]
    res["passing_singletons"] = [{"class": cls, "item": r["coalition"][0], "halves": r["halves"]}
                                 for cls, i in res["classes"].items() for r in i["coalitions"]
                                 if r["pass"] and len(r["coalition"]) == 1]
    res["verdict"] = "COALITIONS_FOUND" if passing else "FALSIFIED_NO_COALITION"
    txt = json.dumps(res, indent=1)
    if a.out:
        Path(a.out).write_text(txt, encoding="utf-8")
    # compact print
    print("verdict", res["verdict"], "| item rows", n_item_rows, "| 60s ticks", n_ticks, "| items", res["items"])
    for cls, i in res["classes"].items():
        print(f"\n[{cls}] raw={i['n_raw']} live_by_half={i['n_live_by_half']} exact={dict(list(i['exact_readsets'].items())[:4])}")
        for r in i["coalitions"]:
            hs = " | ".join(f"k={h['k']}/{h['n']} lift={h['lift']} p={h['p']}" for h in r["halves"])
            print(f"  {'PASS' if r['pass'] else '    '} {'+'.join(r['coalition'])}: {hs}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
