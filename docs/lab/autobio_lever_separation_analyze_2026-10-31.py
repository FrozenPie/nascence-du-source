"""J-2652 aggregation: separate the lever behind F-3388's recency-attractor drop effect.
usage: python autobio_lever_separation_analyze_2026-10-31.py <J-2636_out dir (ctl, drop)> <J-2652_out dir (rnd, inner, chap, norec, rest)>
Conditions: ctl (no change) / drop (all fragments dated >10-28 removed; F-3388) / rnd (random 3283 of the full store removed,
the store-size null) / inner (post-10-28 inner_thought only) / chap (post-10-28 chapter+session_summary only) /
norec (everything kept, recency multiplier 1.0) / rest (post-10-28 everything EXCEPT inner_thought, chapter, session_summary).
All runs: --now 1793390400, seeds 0-3, n=24, identical event set (checked below)."""
import json, glob, statistics as st, sys, collections, os

D0 = sys.argv[1]; D1 = sys.argv[2]
CONDS = [("ctl", D0), ("drop", D0), ("rnd", D1), ("inner", D1), ("chap", D1), ("norec", D1), ("rest", D1)]


def load(cond, arm, d):
    ev = {}
    for f in sorted(glob.glob(f"{d}/{cond}_{arm}_s*.jsonl")):
        for l in open(f, encoding="utf-8"):
            r = json.loads(l)
            if r.get("kind") != "event":
                continue
            ev.setdefault((r["source"], r["provenance"]["locator"], r["cue"]), r)
    return ev


def err(r):
    return r["date_error_days"] if r["answered"] and r["date_error_days"] is not None else 999


def stats(rs):
    n = len(rs)
    if not n:
        return "n=0"
    errs = [r["date_error_days"] for r in rs if r["answered"] and r["date_error_days"] is not None]
    w3 = sum(1 for r in rs if err(r) <= 3)
    ex = sum(1 for r in rs if err(r) == 0)
    pr = sum(r["detail_precision"] for r in rs) / n
    return (f"n={n:2d} med_err={st.median(errs) if errs else None!s:>5} within3={w3:2d}/{n}={w3/n:4.0%} "
            f"exact={ex:2d}/{n}={ex/n:4.0%} prec={pr:.3f}")


BINS = [("<=10-16", lambda d: d <= "2026-10-16"), ("10-17..19", lambda d: "2026-10-17" <= d <= "2026-10-19"),
        (">=10-29", lambda d: d >= "2026-10-29")]
for arm in ("A", "B"):
    data = {c: load(c, arm, d) for c, d in CONDS}
    base = set(data["ctl"])
    print(f"\n######## ARM {arm}  event sets identical to ctl: " + ", ".join(f"{c}={set(v) == base}({len(v)})" for c, v in data.items()))
    for name, f in BINS:
        keys = [k for k in data["ctl"] if f(data["ctl"][k]["event_date"])]
        print(f"[{name}]")
        for c, _ in CONDS:
            ks = [k for k in keys if k in data[c]]
            line = f"   {c:6s} {stats([data[c][k] for k in ks])}"
            if c != "ctl":
                better = sum(1 for k in ks if err(data[c][k]) < err(data["ctl"][k]))
                worse = sum(1 for k in ks if err(data[c][k]) > err(data["ctl"][k]))
                line += f"  vs ctl better/worse/same {better}/{worse}/{len(ks)-better-worse}"
            print(line)
    keys = [k for k in data["ctl"] if data["ctl"][k]["event_date"] <= "2026-10-16"]
    print("[wrong top-1 pointing at a fragment dated >10-28, events <=10-16]")
    for c, _ in CONDS:
        wrong = [data[c][k] for k in keys if k in data[c] and data[c][k]["answered"] and data[c][k]["date_error_days"] not in (0, None)]
        post = [r for r in wrong if r["pred_date"] and r["pred_date"] > "2026-10-28"]
        oc = collections.Counter(r["recalled"][0]["origin"] for r in post)
        print(f"   {c:6s} wrong={len(wrong):2d}  -> >10-28: {len(post):2d}  origins {dict(oc)}")
