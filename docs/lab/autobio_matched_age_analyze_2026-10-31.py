"""J-2637: matched-age boot comparison for the autobio recall probe (F-3364). Reads probe output rows
(<tag>_<arm>_s<seed>.jsonl), de-dupes on source+locator+cue, bins by age_days x phase (phase recomputed from
event_ts vs the run's boot_ts), prints per-cell n, median date error, within-3d, precision, and the share of
wrong top-1s that point at 10-29/30 (the recency attractor)."""
import json, glob, statistics as st, sys, collections
D = sys.argv[1] if len(sys.argv) > 1 else "J-2637_out"
AB = [("0-3", 0, 3), ("3-10", 3, 10), ("10-20", 10, 20), ("20-30", 20, 31)]
NEW = {"2026-10-29", "2026-10-30"}
def load(tag, arm):
    ev = {}
    for f in sorted(glob.glob(f"{D}/{tag}_{arm}_s*.jsonl")):
        for l in open(f, encoding="utf-8"):
            r = json.loads(l)
            if r.get("kind") != "event": continue
            ev.setdefault((r["source"], r["provenance"]["locator"], r["cue"]), r)
    return ev
def cell(rs):
    n = len(rs)
    if not n: return "n=0"
    errs = [r["date_error_days"] for r in rs if r["answered"] and r["date_error_days"] is not None]
    w3 = sum(1 for r in rs if r["answered"] and r["date_error_days"] is not None and r["date_error_days"] <= 3)
    wrong = [r for r in rs if r["answered"] and r["date_error_days"] not in (0, None)]
    toN = sum(1 for r in wrong if r.get("pred_date") in NEW)
    pr = sum(r["detail_precision"] for r in rs) / n
    return (f"n={n} med_err={st.median(errs) if errs else None} within3={w3}/{n}={w3/n:.0%} prec={pr:.2f} "
            f"wrong={len(wrong)} ->10-29/30={toN}")
for tag, boot in (("b1016", "2026-10-16T22:37"), ("b1009", "2026-10-09T08:36")):
    for arm in ("A", "B"):
        ev = load(tag, arm)
        if not ev: continue
        bts = next(iter(ev.values()))
        print(f"\n#### boot {boot} arm {arm}: unique events {len(ev)}")
        import statistics
        for name, lo, hi in AB:
            for ph in ("before_boot", "during_boot"):
                rs = [r for r in ev.values() if lo <= r["age_days"] < hi and r["phase"] == ph]
                print(f"  age {name:5s} {ph:12s}: {cell(rs)}")
        for ph in ("before_boot", "during_boot"):
            print(f"  ALL {ph}: {cell([r for r in ev.values() if r['phase']==ph])}")
        dates = collections.Counter((r["phase"], r["event_date"]) for r in ev.values())
        print("  event dates:", dict(sorted((f"{p[:1]}:{d}", c) for (p, d), c in dates.items())))
