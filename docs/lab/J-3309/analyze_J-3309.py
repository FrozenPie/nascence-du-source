"""J-3309 step 4: verdicts, win rates, binomial tests, blind sheet. Reads judge caches; no network."""
import json, glob, collections, math, random
D = r"C:\Nascence\docs\lab\J-3309"
Q = {q["cycle_id"]: q for q in json.load(open(D + r"\frozen_queries_J-3309.json", encoding="utf-8"))}
votes = collections.defaultdict(dict)   # (cid,arm) -> {(hub,order): arm_pref}
errs = collections.Counter()
for f in glob.glob(D + r"\judge_cache_*_J-3309.jsonl"):
    for l in open(f, encoding="utf-8"):
        r = json.loads(l)
        if r["arm_pref"] is None: errs[(r["hub"], r["err"])] += 1; continue
        votes[(r["cycle_id"], r["arm"])][(r["hub"], r["order"])] = r["arm_pref"]
def fam(v, hub):
    a, b = v.get((hub, 1)), v.get((hub, 2))
    if a is None or b is None: return None
    return "win" if a and b else ("loss" if (not a and not b) else "tie")
def panel(v):
    f1, f2 = fam(v, "j1"), fam(v, "j2")
    if f1 is None or f2 is None: return None
    if f1 == f2 and f1 != "tie": return f1
    return "tie"
def tbonly(v):
    return fam(v, "tb")
def binom_p(k, n, p=0.5):
    return sum(math.comb(n, i) for i in range(k, n + 1)) / 2 ** n if n else float("nan")
res = {}
for arm in ("N", "A05", "A025", "B"):
    for strat in ("all", "human", "internal"):
        c = collections.Counter(); fc = {"j1": collections.Counter(), "j2": collections.Counter(), "tb": collections.Counter()}
        for (cid, a), v in votes.items():
            if a != arm: continue
            if strat != "all" and Q[cid]["input_type"] != strat: continue
            p = panel(v)
            if p: c[p] += 1
            for h in ("j1", "j2", "tb"):
                f = fam(v, h)
                if f: fc[h][f] += 1
        w, l, t = c["win"], c["loss"], c["tie"]
        res[(arm, strat)] = {"win": w, "loss": l, "tie": t, "decided": w + l, "win_rate": (w / (w + l)) if w + l else None,
                             "p_one_sided": binom_p(w, w + l) if w + l else None,
                             "j1": dict(fc["j1"]), "j2": dict(fc["j2"]), "tb": dict(fc["tb"])}
for k, v in res.items():
    if v["win"] + v["loss"] + v["tie"]:
        print(k, v)
print("errors", dict(errs))
json.dump({f"{a}|{s}": v for (a, s), v in res.items()}, open(D + r"\results_J-3309.json", "w"), indent=1)
