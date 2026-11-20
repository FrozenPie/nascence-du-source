import json, collections
rows = [json.loads(l) for l in open(r"C:\Nascence\docs\lab\J-3950_data\results.jsonl", encoding="utf-8")]
err = [r for r in rows if "error" in r]
print("rows", len(rows), "errors", len(err))
g = collections.defaultdict(list)
for r in rows:
    if "error" in r: continue
    g[(r["site"], r["var"])].append(r)
for site in ("emissary", "narrative"):
    print("==", site)
    for v in "ABCDE":
        L = g[(site, v)]
        if not L: continue
        n = len(L)
        parsed = sum(r["parsed"] for r in L)
        kp = sum(r["key_present"] for r in L)
        vals = [r["val"] for r in L if isinstance(r["val"], float)]
        z = sum(1 for x in vals if x == 0.0); o = sum(1 for x in vals if x == 1.0)
        both0 = sum(1 for r in L if r["val"] == 0.0 and r.get("val2") == 0.0) if site == "narrative" else None
        mean = sum(vals) / len(vals) if vals else None
        print(f"{v}: n={n} parsed={parsed} key_missing={n-kp} exact0={z} ({z/max(1,len(vals)):.0%}) exact1={o} ({o/max(1,len(vals)):.0%}) mean={mean and round(mean,3)} both0={both0}")
# narrative split by passage kind
for kind in ("candidate", "head_both0"):
    for v in "ABCDE":
        L = [r for r in g[("narrative", v)] if r.get("kind") == kind]
        vals = [r["val"] for r in L if isinstance(r["val"], float)]
        if vals: print(kind, v, "n", len(vals), "exact0", sum(x == 0.0 for x in vals), "mean", round(sum(vals)/len(vals), 3))
# paired: emissary var A vs others, same input same rep
d = {(r["idx"], r["rep"], r["var"]): r["val"] for r in rows if r["site"] == "emissary" and "error" not in r}
for v in "BCDE":
    diffs = [abs(d[(i, rp, "A")] - d[(i, rp, v)]) for (i, rp, vv) in d if vv == v and (i, rp, "A") in d and isinstance(d[(i, rp, "A")], float) and isinstance(d[(i, rp, v)], float)]
    if diffs: print("emissary |A-%s| mean" % v, round(sum(diffs)/len(diffs), 3), "identical", sum(x == 0 for x in diffs), "/", len(diffs))
# copying: does output echo the prefill?
for v, pv in (("A", 0.0), ("B", 1.0), ("C", 0.5)):
    for site in ("emissary", "narrative"):
        vals = [r["val"] for r in g[(site, v)] if isinstance(r["val"], float)]
        if vals: print("echo", site, v, "share == prefill", round(sum(x == pv for x in vals)/len(vals), 3))
