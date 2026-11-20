"""J-3122 scoring. python scripts/lab_J3122_score.py [list|score]  -- list = marked ticks lacking a label (to hand label)."""
import json, os, sys, math, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import lab_metaphor_union as U
D = os.path.join(U.ROOT, "docs", "lab", "J-3122_data")
frame = {r["tick_ts"]: r for r in U._load_jsonl(os.path.join(D, "frame.jsonl"))}
labels = {r["tick_ts"]: r["label"] for r in U._load_jsonl(os.path.join(U.ROOT, "docs/lab/J-3205_data/prelabels_claude.jsonl"))}
nl = os.path.join(D, "labels_new.jsonl")
if os.path.exists(nl):
    for r in U._load_jsonl(nl): labels[r["tick_ts"]] = r["label"]
V = {"A": {}, "B": {}, "C": {}}
for r in U._load_jsonl(U.RUNS):
    if r["arm"] in ("v1", "v2") and r.get("how") != "unavailable": V[{"v1": "A", "v2": "B"}[r["arm"]]][r["tick_ts"]] = r["verdict"]
for r in U._load_jsonl(os.path.join(D, "runs.jsonl")):
    if r.get("how") != "unavailable": V[r["arm"]][r["tick_ts"]] = r["verdict"]
for ts, f in frame.items():
    s = f["stored"]
    if s and s["verdict"] in ("metaphor", "literal"): V["A"][ts] = (s["verdict"] == "metaphor")
mark = {a: {t for t, v in d.items() if v is True} for a, d in V.items()}
cmd = sys.argv[1] if len(sys.argv) > 1 else "score"
if cmd == "list":
    need = sorted({t for m in mark.values() for t in m if t not in labels})
    for t in need:
        print(f"--- {t} arms={[a for a in mark if t in mark[a]]} src={frame[t]['src']}\n{frame[t]['passage']}\n")
    print(len(need), "unlabelled marked"); sys.exit()
# score: common universe = ticks where all of A,B,C have a verdict (primary); also per-arm own universe
def stats(univ, tag):
    pos = {t for t in univ if labels.get(t) == "F"}; posi = {t for t in univ if labels.get(t) in ("F", "A")}
    unl = [t for t in univ if t not in labels]
    print(f"\n== {tag}: universe {len(univ)} ticks; labelled-positive strict {len(pos)} incl {len(posi)}; unlabelled non-marked ticks {len(unl)} (treated as literal)")
    for a in "ABC":
        m = mark[a] & univ; tp = len(m & pos); tpi = len(m & posi)
        print(f" {a}: marks {len(m)} | strict TP {tp} prec {U.pct(tp,len(m))} W{U.wilson(tp,len(m))} recall {U.pct(tp,len(pos))} W{U.wilson(tp,len(pos))} | incl TP {tpi} prec {U.pct(tpi,len(m))} W{U.wilson(tpi,len(m))} recall {U.pct(tpi,len(posi))} W{U.wilson(tpi,len(posi))}")
    return pos, posi
cov = set(V["A"]) & set(V["B"]) & set(V["C"])
j3205 = {t for t in cov if "j3205" in frame[t]["src"]}
stats(cov, "all frame ticks with A,B,C verdicts")
stats(j3205, "J-3205 labelled-union subset")
stats({t for t in cov if "split" in frame[t]["src"]}, "stored splits")
stats({t for t in cov if "over500" in frame[t]["src"]}, "over-500")
print("\ncoverage:", {a: len(v) for a, v in V.items()}, "frame", len(frame))
pos = {t for t in cov if labels.get(t) == "F"}
print("C marks not in A:", len(mark["C"] - mark["A"]), "| A marks removed by C:", len((mark["A"] & cov) - mark["C"]), "| C marks not in B:", len(mark["C"]-mark["B"]))
for tag, s in (("A-marks removed by C", (mark["A"] & cov) - mark["C"]), ("B-marks removed by C", (mark["B"] & cov) - mark["C"])):
    print(tag, [(t, labels.get(t)) for t in sorted(s)])
print("strict positives:", len(pos), "| recovered by C", len(pos & mark["C"]), "| A", len(pos & mark["A"]), "| B", len(pos & mark["B"]))
print("ambient 5 (L154,L066,L179,L116,L011):")
key = {k["id"]: k["tick_ts"] for k in U._load_jsonl(os.path.join(U.ROOT, "docs/lab/J-3205_data/labelling_key.jsonl"))}
for i in ("L154", "L066", "L179", "L116", "L011"):
    t = key[i]; print(" ", i, {a: V[a].get(t) for a in "ABC"})
if cmd == "score":
    print("\n== extra")
    P = lambda s: sorted(s)
    Fs = {t for t in cov if labels.get(t) == "F"}
    print("strict pos lost by C vs A:", P((Fs & mark["A"]) - mark["C"]), "| gained by C vs A:", P((Fs & mark["C"]) - mark["A"]))
    print("FP (label L) counts: A", len({t for t in mark["A"] & cov if labels.get(t) == "L"}), "B", len({t for t in mark["B"] & cov if labels.get(t) == "L"}), "C", len({t for t in mark["C"] & cov if labels.get(t) == "L"}))
    print("C-only marks (not in A):", [(t, labels.get(t), frame[t]["passage"][:110]) for t in P(mark["C"] - mark["A"])])
    print("C FP remaining:", [(t, frame[t]["passage"][:90]) for t in P({t for t in mark["C"] if labels.get(t) == "L"})])
    # A-vs-C on priority set only, all 94, A from stored/replay
    pri = set(json.load(open(os.path.join(D, "priority_ts.json")))) & set(V["C"])
    stats(pri, "priority 94 (A vs C; B partial)")
    import datetime
    for t in sorted(frame):
        d = datetime.datetime.fromtimestamp(t)
        if d.month == 10 and d.day == 29 and 22 <= d.hour <= 22 and (frame[t]["stored"] or {}).get("verdict") == "metaphor":
            print("10-29 22h stored metaphor tick", t, d, "C", V["C"].get(t), frame[t]["passage"][:200])
