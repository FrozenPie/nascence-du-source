import json, math, collections, os
def wil(k, n, z=1.96):
    if n == 0: return (0, 0)
    p = k / n; d = 1 + z*z/n; c = p + z*z/(2*n); a = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))
    return round((c-a)/d, 3), round((c+a)/d, 3)
D = "docs/lab/J-3794_data/"
g = [json.loads(l) for l in open(D+"graded.jsonl")]
print("n", len(g), "invalid", collections.Counter((r["gemma"] == "invalid", r["falcon"] == "invalid") for r in g))
for who in ("gemma", "falcon"):
    print(who, "dist", dict(collections.Counter(r[who] for r in g)))
    for v in ("yes", "partly", "no", "unsaid"):
        s = [r for r in g if r["logged"] == v]
        ag = sum(1 for r in s if r[who] == v)
        # unsaid has no judge analogue: report the judge distribution
        print(" ", v, len(s), "judge dist", dict(collections.Counter(r[who] for r in s)), "exact agree", ag, wil(ag, len(s)))
ys = [r for r in g if r["logged"] == "yes"]
for name, f in (("gemma no", lambda r: r["gemma"] == "no"), ("falcon no", lambda r: r["falcon"] == "no"),
                ("BOTH no", lambda r: r["gemma"] == "no" and r["falcon"] == "no"),
                ("gemma != yes", lambda r: r["gemma"] != "yes"), ("BOTH != yes", lambda r: r["gemma"] != "yes" and r["falcon"] != "yes")):
    k = sum(f(r) for r in ys); print("false-yes", name, k, len(ys), round(k/len(ys), 3), wil(k, len(ys)))
for name, f in (("gemma", lambda r: r["gemma"] == "yes"), ("falcon", lambda r: r["falcon"] == "yes")):
    s = [r for r in g if r["logged"] in ("no", "unsaid")]; k = sum(f(r) for r in s); print("missed-yes (logged no/unsaid, judge yes)", name, k, len(s))
gg = [r for r in g if "invalid" not in (r["gemma"], r["falcon"])]
print("judge-judge exact agree", sum(r["gemma"] == r["falcon"] for r in gg), len(gg))
hand = json.load(open(D+"hand_grades.json")); lg = {str(r["sid"]): r for r in g}
for who in ("gemma", "falcon"):
    ex = sum(hand[k] == lg[k][who] for k in hand); print("hand vs", who, "exact", ex, "/20")
print("hand vs logged exact", sum(hand[k] == lg[k]["logged"] for k in hand if lg[k]["logged"] != "unsaid"), "of", sum(lg[k]["logged"] != "unsaid" for k in hand))
hy = [k for k in hand if lg[k]["logged"] == "yes"]
print("hand on logged-yes:", collections.Counter(hand[k] for k in hy))
if os.path.exists(D+"closures_graded.jsonl"):
    c = [json.loads(l) for l in open(D+"closures_graded.jsonl")]
    print("closures", len(c))
    for name, f in (("gemma no", lambda r: r["gemma"] == "no"), ("falcon no", lambda r: r["falcon"] == "no"), ("BOTH no", lambda r: r["gemma"] == "no" and r["falcon"] == "no"), ("BOTH != yes", lambda r: r["gemma"] != "yes" and r["falcon"] != "yes")):
        k = sum(f(r) for r in c); print(" closure false", name, k, len(c), round(k/len(c), 3), wil(k, len(c)))
