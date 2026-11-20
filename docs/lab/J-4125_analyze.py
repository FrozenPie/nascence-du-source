import json, re, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
LAB = r"C:\Nascence\data\lab\ground_contract_lab"
rows = {r["sid"]: r for r in map(json.loads, open(r"C:\Nascence\docs\lab\J-2888_data\sample.jsonl", encoding="utf-8"))}
gens = {}; grades = {}; ctl = []
for l in open(LAB + r"\J-4125_gen.jsonl", encoding="utf-8"):
    r = json.loads(l); gens[(r["sid"], r["arm"])] = r
for l in open(LAB + r"\J-4125_grades.jsonl", encoding="utf-8"):
    r = json.loads(l)
    (ctl.append(r) if r.get("control") else grades.__setitem__((r["sid"], r["arm"]), r))
SYM = re.compile(r"\b(symbol\w*|metaphor\w*|allud\w+|alluding|represent\w*|evoke[sd]?|figurative\w*)\b", re.I)
CAUSAL = re.compile(r"\b(because|caused by|due to|results? from|is produced by|is released|is created by|works by|process of|mechanism)\b", re.I)
full = sorted(s for s in {k[0] for k in gens} if all((s, a) in gens for a in "BCD"))
print("rows with all 3 arms:", len(full), "strata", dict(collections.Counter(rows[s]["stratum"] for s in full)))
print("gen calls", len(gens), "median secs", sorted(g["secs"] for g in gens.values())[len(gens)//2], "gen errors", sum(1 for g in gens.values() if g["err"]))
for arm in "BCD":
    c = collections.Counter()
    for s in full:
        g = grades.get((s, arm))
        if g is None: c["ungraded"] += 1; continue
        k = g["kind"]
        if k.startswith("break"): c["schema_break"] += 1; c[k] += 1
        if k == "null": c["null"] += 1; continue
        t = g.get("grounding") or ""
        if not t: continue
        c["nonnull"] += 1
        if SYM.search(t): c["symbol_regex"] += 1
        if CAUSAL.search(t): c["causal_regex"] += 1
        if g.get("q1") is None: c["judge_err_q1"] += 1
        else:
            c["judged_q1"] += 1; c["invented_verified"] += bool(g["q1_verified"]); c["q1_true_raw"] += bool(g["q1"])
        if g.get("q2") is None: c["judge_err_q2"] += 1
        else: c["judged_q2"] += 1; c["mechanism"] += bool(g["q2"])
    print(arm, "n", len(full), dict(c))
print("controls", len(ctl), "hits", sum(1 for r in ctl if r.get("control_hit")), "judge errs", sum(1 for r in ctl if r.get("q1") is None))
