import json, re, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
LAB = r"C:\Nascence\data\lab\ground_contract_lab"; D = r"C:\Nascence\docs\lab\J-2888_data"
rows = {r["sid"]: r for r in map(json.loads, open(D + r"\sample.jsonl", encoding="utf-8"))}
gens = {}
for l in open(LAB + r"\gen.jsonl", encoding="utf-8"):
    r = json.loads(l); gens[(r["sid"], r["arm"])] = r
grades = {}; ctl = []
for l in open(LAB + r"\grades.jsonl", encoding="utf-8"):
    r = json.loads(l)
    if r.get("control"): ctl.append(r)
    else: grades[(r["sid"], r["arm"])] = r
SYM = re.compile(r"\b(symbol\w*|metaphor\w*|allud\w+|alluding|represent\w*|evoke[sd]?|figurative\w*)\b", re.I)
CAUSAL = re.compile(r"\b(because|caused by|due to|results? from|is produced by|is released|is created by|works by|process of|mechanism)\b", re.I)
HEDGE = re.compile(r"\b(likely|perhaps|possibly|may|might|could|such as|probably)\b", re.I)
META_OPEN = re.compile(r"^\s*(The thought rests on|The image of|The thought)", re.I)
def newcaps(th, g):
    tl = set(re.findall(r"[A-Za-z0-9']+", th.lower()))
    out = []
    for m in re.finditer(r"(?<![.!?]\s)(?<!^)\b([A-Z][a-z]{2,}|\d+)\b", g):
        w = m.group(1)
        if w.lower() not in tl: out.append(w)
    return out
rowsets = sorted({k[0] for k in gens if k[1] in ("A0", "B", "C", "D")})
# only rows with all four arms generated
full = [s for s in rowsets if all((s, a) in gens for a in ("A0", "B", "C", "D"))]
print("rows with all 4 arms:", len(full), "of", len(rowsets), "started; strata", dict(collections.Counter(rows[s]["stratum"] for s in full)))
secs = [g["secs"] for g in gens.values()]
print("mixtral calls", len(gens), "median secs", sorted(secs)[len(secs) // 2])
def hedged_detail(g, quote):
    for sent in re.split(r"(?<=[.!?])\s+", g):
        if quote and quote.lower()[:30] in sent.lower(): return bool(HEDGE.search(sent))
    return bool(HEDGE.search(g))
res = {}
for arm in ("A0", "B", "C", "D"):
    c = collections.Counter(); n = 0
    for s in full:
        g = gens[(s, arm)]; gr = grades.get((s, arm))
        n += 1
        if g["content"] is None: c["no_reply"] += 1; continue
        kind = gr["kind"] if gr else None
        if gr is None: c["ungraded"] += 1; continue
        if kind.startswith("break"): c["schema_break"] += 1
        if kind == "null": c["null"] += 1; continue
        txt = gr.get("grounding") or ""
        if not txt: continue
        c["nonnull"] += 1
        th = rows[s]["raw"]
        if SYM.search(txt): c["symbol_regex"] += 1
        if CAUSAL.search(txt): c["causal_regex"] += 1
        if META_OPEN.search(txt): c["meta_opener"] += 1
        if newcaps(th, txt): c["newcaps_proxy"] += 1
        if SYM.search(txt): c["symbol_any_rx"] += 1
        if gr.get("q1") is None: c["judge_err"] += 1; continue
        c["judged"] += 1
        if gr["q1_verified"]: c["invented_judge"] += 1; c["echo_proxy"] += (0 if hedged_detail(txt, gr["q1_quote"]) else 1)
        if gr.get("q2"): c["mechanism_judge"] += 1
        if gr.get("q3"): c["symbol_judge"] += 1
        if gr.get("q3") or SYM.search(txt): c["symbol_any"] += 1
    res[arm] = (n, c)
cols = ["no_reply", "ungraded", "schema_break", "null", "nonnull", "judged", "judge_err", "invented_judge", "newcaps_proxy", "echo_proxy",
        "mechanism_judge", "causal_regex", "symbol_regex", "symbol_judge", "symbol_any", "meta_opener"]
for arm, (n, c) in res.items():
    print(arm, n, {k: c[k] for k in cols})
if ctl:
    print("controls:", len(ctl), "hits", sum(1 for r in ctl if r.get("control_hit")), "judge errs", sum(1 for r in ctl if r.get("q1") is None))
bs = collections.defaultdict(collections.Counter)
for g in grades.values():
    if g.get("q1") is not None: bs["q1"][g["q1"]] += 1
    if g.get("q2") is not None: bs["q2"][g["q2"]] += 1
    if g.get("q3") is not None: bs["q3"][g["q3"]] += 1
print("judge base rates", {k: dict(v) for k, v in bs.items()})
