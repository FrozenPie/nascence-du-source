import json, math, collections, sys
sys.stdout.reconfigure(encoding="utf-8")
D = "C:/Nascence/docs/lab/J-3550_data/"
G = json.load(open(D+"judged_gemma4_12b.json", encoding="utf-8")); F = json.load(open(D+"judged_falcon3_7b.json", encoding="utf-8"))
def wil(k, n, z=1.96):
    if n == 0: return (0, 0)
    p = k/n; d = 1+z*z/n; c = p+z*z/(2*n); a = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))
    return (round((c-a)/d, 2), round((c+a)/d, 2))
V = lambda t: t[0] if t else None
others = [i for i, x in enumerate(G) if x["tag"] == "other"]; fails = [i for i, x in enumerate(G) if x["tag"] != "other"]
print("== run-to-run: others (31 x3)")
rates = [sum(r["acc"] for r in G[i]["runs"]) for i in others]
print("accepts per row (of 3) histogram", dict(collections.Counter(rates)))
tot = sum(rates); print("overall accept", tot, "/", 93, wil(tot, 93))
print("rows with split verdict across 3 runs:", sum(1 for r in rates if 0 < r < 3), "of 31")
fr = [sum(r["acc"] for r in G[i]["runs"]) for i in fails]; print("fail rows accepts of 5:", fr, "overall", sum(fr), "/25", wil(sum(fr), 25))
for jn, J in (("gemma", G), ("falcon", F)):
    print("==", jn)
    ov = collections.Counter(V(J[i]["old_v"]) for i in others); print(" old verdict others", dict(ov))
    of = collections.Counter((J[i]["tag"][:12], V(J[i]["old_v"])) for i in fails); print(" old verdict fails", dict(of))
    # lost-faithful: rows judged old-faithful; per-run reject rate
    ofa = [i for i in others if V(J[i]["old_v"]) == "faithful"]
    runs = sum(len(J[i]["runs"]) for i in ofa); rej = sum(1 for i in ofa for r in J[i]["runs"] if not r["acc"])
    print(" old-faithful rows", len(ofa), "per-run reject", rej, "/", runs, wil(rej, runs), "| rows rejected in majority (>=2/3):", sum(1 for i in ofa if sum(1 for r in J[i]["runs"] if not r["acc"]) >= 2), "rows ever rejected", sum(1 for i in ofa if any(not r["acc"] for r in J[i]["runs"])))
    # accepted new faithful rate (first accept judged)
    nf = [(V(r.get("v")) ) for i in others for r in J[i]["runs"] if r.get("v")]
    print(" new accepts judged (others)", dict(collections.Counter(nf)))
    # failure-reject
    frej = sum(1 for i in fails for r in J[i]["runs"] if not r["acc"]); print(" failure-reject per run", frej, "/25", wil(frej, 25))
    for i in fails:
        print("  ", J[i]["tag"][:28], "old:", V(J[i]["old_v"]), "new accepts judged:", [V(r.get("v")) for r in J[i]["runs"] if r["acc"]])
    errs = sum(1 for x in J for y in [x["old_v"]]+[r.get("v") for r in x["runs"] if r.get("v")] if y[0] in ("error", "unparsed")); print(" judge errors/unparsed", errs)
# agreement
print("== agreement old verdict (all 36)")
pairs = [(V(G[i]["old_v"]), V(F[i]["old_v"])) for i in range(36)]
agree = sum(a == b for a, b in pairs); print(" exact", agree, "/36")
bi = [(a == "faithful", b == "faithful") for a, b in pairs]; ba = sum(a == b for a, b in bi); print(" faithful-vs-not agree", ba, "/36")
pa = ba/36; pg = sum(a for a, _ in bi)/36; pf = sum(b for _, b in bi)/36; pe = pg*pf+(1-pg)*(1-pf); print(" kappa(faithful binary)", round((pa-pe)/(1-pe), 2) if pe < 1 else None, "gemma faithful", sum(a for a, _ in bi), "falcon faithful", sum(b for _, b in bi))
na = []; 
for i in range(36):
    for k, r in enumerate(G[i]["runs"]):
        if r.get("v") and F[i]["runs"][k].get("v"): na.append((V(r["v"]) == "faithful", V(F[i]["runs"][k]["v"]) == "faithful"))
print(" new-accept judged by both:", len(na), "agree", sum(a == b for a, b in na), "gemma faithful", sum(a for a, _ in na), "falcon faithful", sum(b for _, b in na))
# lost-faithful with both-judges-agree-old-faithful
both = [i for i in others if V(G[i]["old_v"]) == "faithful" and V(F[i]["old_v"]) == "faithful"]
runs = sum(len(G[i]["runs"]) for i in both); rej = sum(1 for i in both for r in G[i]["runs"] if not r["acc"])
print("== old faithful by BOTH judges:", len(both), "per-run reject", rej, "/", runs, wil(rej, runs))
json.dump({"both": [G[i]["cycle_id"] for i in both]}, open(D+"both_faithful.json", "w"))
# disagreement rows
print("== disagreements (old):")
for i in range(36):
    if V(G[i]["old_v"]) != V(F[i]["old_v"]): print(i, G[i]["tag"][:10], G[i]["cycle_id"][:8], "gemma", V(G[i]["old_v"]), "falcon", V(F[i]["old_v"]))
