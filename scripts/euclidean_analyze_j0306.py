"""J-0301 stratified analysis of j0301_grades.jsonl — F-0299-comparable win rates."""
import json, sys, statistics as st, datetime
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
SCRATCH = Path(r"C:\Users\USER\AppData\Local\Temp\claude\C--FreshStart\9bbae2ae-e05b-41b6-858c-ea49c801d6a9\scratchpad")
G = [json.loads(l) for l in open(SCRATCH / "j0301_grades.jsonl", encoding="utf-8")]
F0299_TS = 1787569232.1

# Reconstruct F-0299's graded-set timestamps (last 60 divergent rows at its run time)
rows = [json.loads(l) for l in open(r"C:\Nascence\data\euclidean_shadow.jsonl", encoding="utf-8")]
def div(r): return r.get("jaccard", 1.0) < 1.0 and (r.get("state_top") or []) != (r.get("base_top") or [])
pre = [r for r in rows if r["ts"] <= F0299_TS and div(r)]
s60ts = {r["ts"] for r in pre[-60:]}

def rate(gg, label):
    n = len(gg)
    s = sum(1 for g in gg if g["winner"] == "state")
    b = sum(1 for g in gg if g["winner"] == "baseline")
    t = n - s - b
    d = s + b
    pct = f"{round(100*s/d)}%" if d else "n/a"
    print(f"  {label:<48} n={n:>3}  state {s:>2} / base {b:>2} / tie {t:>2}  -> state {pct} of {d} decisive")
    return (n, s, b, t, d)

felt = [g for g in G if g["batch"] == "felt"]
nonf = [g for g in G if g["batch"] == "nonfelt"]
print("=== J-0301 re-grade (judge gemma4:12b @11439, BLIND A/B, same _grade as F-0299) ===")
rate(felt, "FELT divergent, ALL")
new = [g for g in felt if g["ts"] > F0299_TS]
old = [g for g in felt if g["ts"] in s60ts]
other = [g for g in felt if g["ts"] <= F0299_TS and g["ts"] not in s60ts]
rate(new, "FELT divergent, NEW since F-0299 run (independent)")
rate(old, "FELT divergent, F-0299 overlap re-grade (repro)")
if other: rate(other, "FELT divergent, pre-F-0299 but not in its sample")
b24 = datetime.datetime(2026, 8, 24, tzinfo=datetime.timezone.utc).timestamp()
rate([g for g in felt if g["ts"] >= b24], "FELT divergent, ts >= 2026-08-24 UTC (job's 'fresh')")
# affect_w split (F-0299 style, median over graded felt)
aws = [g["affect_w"] for g in felt if isinstance(g.get("affect_w"), (int, float))]
med = st.median(aws)
rate([g for g in felt if g["affect_w"] >= med], f"FELT, HIGH affect_w (>= med {round(med,2)})")
rate([g for g in felt if g["affect_w"] < med], f"FELT, LOW  affect_w (<  med {round(med,2)})")
# affect_match_mean split (strength of the fired signal)
ams = [g["amm"] for g in felt if isinstance(g.get("amm"), (int, float))]
medm = st.median(ams)
rate([g for g in felt if (g.get("amm") or 0) >= medm], f"FELT, HIGH affect_match_mean (>= {round(medm,3)})")
rate([g for g in felt if (g.get("amm") or 0) < medm], f"FELT, LOW  affect_match_mean (<  {round(medm,3)})")
print()
rate(nonf, "NON-FELT contrast (pre-08-20 era rows)")
nonf_old = [g for g in nonf if g["ts"] in s60ts]
if nonf_old: rate(nonf_old, "NON-FELT overlap w/ F-0299 sample (repro)")
# repro detail on the 20 overlap felt rows
print("\nF-0299 felt-overlap repro detail (their run: 7 state / 10 base / 3 tie):")
for g in sorted(old, key=lambda x: x["ts"]):
    print(f"  {g['winner']:>8}  amm={g['amm']}  affect_w={g['affect_w']}  {g['query'][:70]}")
