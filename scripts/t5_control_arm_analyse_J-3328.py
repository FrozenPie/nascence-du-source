"""J-3328 analyse: reads docs/lab/J-3328_data/{pairs,calls}.jsonl, writes docs/lab/J-3328_data/analysis.json. Read-only otherwise."""
import json, random, statistics as st, sys
from pathlib import Path
from collections import defaultdict
D = Path(__file__).resolve().parent.parent / "docs/lab/J-3328_data"
P = json.load(open(D/"pairs.json", encoding="utf-8")); pairs = {p["id"]: p for p in P["real"] + P["null"]}
rows = [json.loads(l) for l in open(D/"calls.jsonl", encoding="utf-8")]
latest = {}
for r in rows: latest[(r["pair"], r["order"], r["key"])] = r
def valid(r): return r["v1"] is not None and r["v1"] == r["v2"]   # both judges agree; tiebreak/split/unavailable = no verdict
by = defaultdict(dict)
for (pid, o, k), r in latest.items(): by[(pid, k)][o] = r
def boot(xs, n=5000):
    if not xs: return None
    rng = random.Random(1); m = []
    for _ in range(n): m.append(sum(rng.choice(xs) for _ in xs) / len(xs))
    m.sort(); return [round(m[int(.025*n)], 3), round(m[int(.975*n)], 3)]
out = {"calls": len(rows), "how": defaultdict(int)}
for r in rows: out["how"][r["how"]] += 1
out["how"] = dict(out["how"])
for kind in ("real", "null"):
    for k in ("x_more_responsive", "x_less_formulaic"):
        wins = []; pairs_both = 0; pos = []; unstable = 0
        for (pid, kk), d in by.items():
            if kk != k or pairs[pid]["kind"] != kind or 0 not in d or 1 not in d: continue
            if not (valid(d[0]) and valid(d[1])): continue
            pairs_both += 1
            pref = [d[o]["v1"] == d[o]["x_is_rec"] for o in (0, 1)]  # True -> "rec"(anchor) arm preferred
            for o in (0, 1): pos.append(1 if d[o]["v1"] else 0)       # X chosen
            if pref[0] == pref[1]: wins.append(1 if pref[0] else 0)
            else: unstable += 1
        out[f"{kind}:{k}"] = {"both_orders_valid": pairs_both, "stable": len(wins), "unstable_swap": unstable,
            "pref_for_anchor": round(sum(wins)/len(wins), 3) if wins else None, "ci95": boot(wins),
            "X_chosen_rate": round(sum(pos)/len(pos), 3) if pos else None}
def dm(f):
    d = [float(p["rec"][f]) - float(p["ctl"][f]) for p in P["real"] if f in p["rec"] and f in p["ctl"]]
    return {"n": len(d), "mean_delta_rec_minus_ctl": round(st.mean(d), 4), "ci95": boot(d)} if d else None
out["secondary_real"] = {f: dm(f) for f in ("env", "len", "cos_prev20")}
out["opener_shared_real"] = sum(1 for p in P["real"] if str(p["rec"].get("opener")) == str(p["ctl"].get("opener")))
json.dump(out, open(D/"analysis.json", "w"), indent=1); print(json.dumps(out, indent=1))
