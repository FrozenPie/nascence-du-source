import json, sys
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8")
bat = json.load(open(r"C:\Nascence\docs\lab\J-2970_battery.json", encoding="utf-8"))
calls = [json.loads(l) for l in open(r"C:\Nascence\docs\lab\J-2970_calls.jsonl", encoding="utf-8") if l.strip()]
V = {}
errs = defaultdict(int)
for c in calls:
    if c["verdict"] is None:
        errs[(c["hub"], c["err"])] += 1
        V.setdefault((c["hub"], c["id"], c["variant"]), None)
    else:
        V[(c["hub"], c["id"], c["variant"])] = c["verdict"]
print("errors (after retry):", dict(errs))
HUB = ["mixtral", "falcon3", "granite"]


def panel(iid, var, rule):
    m, f, g = (V.get((h, iid, var)) for h in HUB)
    if m is None or f is None:
        return None
    if rule == "both":
        return m and f
    if m == f:
        return m
    return g          # tiebreak decides (None if granite missing)


def rate(items, var, who):
    n = y = 0
    for d in items:
        v = panel(d["id"], var, who) if who in ("tiebreak", "both") else V.get((who, d["id"], var))
        if v is None:
            continue
        n += 1
        y += bool(v)
    return (y, n)


def fmt(t):
    return f"{t[0]:>2}/{t[1]:<2} {100*t[0]/t[1]:4.0f}%" if t[1] else "  n/a   "


def table(name, items, classes, var="base"):
    print(f"\n=== {name} ({var}) yes-rate by class ===")
    print(f"{'class':22s} {'n':>3s} " + " ".join(f"{w:>12s}" for w in HUB + ["tiebreak", "both-agree"]))
    for cl in classes:
        its = [d for d in items if d["cls"] == cl]
        print(f"{cl:22s} {len(its):>3d} " + " ".join(f"{fmt(rate(its, var, w)):>12s}" for w in HUB + ["tiebreak", "both"]))


C, F = bat["cuts"], bat["follows"]
cc = ["boilerplate", "concession", "non_addressing", "hand_vacuous", "substantive_real", "hand_counterexample"]
fc = ["restatement", "hedge", "non_sequitur", "hand_checkable"]
table("CUTS (judge c)", C, cc)
table("FOLLOWS (judge b)", F, fc)


def disc(items, goodcls, badcls, var="base"):
    good = [d for d in items if d["cls"] in goodcls]
    bad = [d for d in items if d["cls"] in badcls]
    print(f"  good={goodcls} bad={badcls}")
    for w in HUB + ["tiebreak", "both"]:
        g = rate(good, var, w); b = rate(bad, var, w)
        if g[1] and b[1]:
            yg, yb = g[0] / g[1], b[0] / b[1]
            print(f"   {w:11s} yes|good {fmt(g)}  yes|bad {fmt(b)}  gap {100*(yg-yb):+4.0f} pts  accuracy {100*((g[0])+(b[1]-b[0]))/(g[1]+b[1]):3.0f}%")


print("\n=== DISCRIMINATION ===")
print("cuts, real good vs real bad (substantive_real vs boilerplate+concession):")
disc(C, ["substantive_real"], ["boilerplate", "concession"])
print("cuts, hand-written pairs on the same grounds:")
disc(C, ["hand_counterexample"], ["hand_vacuous"])
print("cuts, all good vs all clear-bad (excl. non_addressing):")
disc(C, ["substantive_real", "hand_counterexample"], ["boilerplate", "concession", "hand_vacuous"])
print("follows, hand_checkable vs each bad class and all:")
for b in (["restatement"], ["hedge"], ["non_sequitur"], ["restatement", "hedge", "non_sequitur"]):
    disc(F, ["hand_checkable"], b)

print("\n=== LABEL: CLAIM vs QUESTION (question-form items only) ===")
for key, items, cls in (("cuts", C, cc), ("follows", F, fc)):
    qi = [d for d in items if (("id" in d) and ("q" in [k[2] for k in V if k[1] == d["id"]]))]
    print(f"{key}: n question-form items = {len(qi)}")
    for w in HUB:
        a = b = flips = both = 0
        for d in qi:
            x, y = V.get((w, d["id"], "base")), V.get((w, d["id"], "q"))
            if x is None or y is None:
                continue
            both += 1; a += bool(x); b += bool(y); flips += (x != y)
        print(f"  {w:8s} yes CLAIM {a}/{both}  yes QUESTION {b}/{both}  flipped {flips}")
    for w in ("tiebreak", "both"):
        a = b = both = flips = 0
        for d in qi:
            x, y = panel(d["id"], "base", w), panel(d["id"], "q", w)
            if x is None or y is None:
                continue
            both += 1; a += bool(x); b += bool(y); flips += (x != y)
        print(f"  {w:8s} yes CLAIM {a}/{both}  yes QUESTION {b}/{both}  flipped {flips}")
    # discrimination under QUESTION label on the question-form items
    print(f"  discrimination gap (question-form items only) base vs q:")
    gcl = {"cuts": ["substantive_real"], "follows": ["hand_checkable"]}[key]
    for var in ("base", "q"):
        g = [d for d in qi if d["cls"] in gcl]
        bd = [d for d in qi if d["cls"] not in gcl and d["cls"] not in ("non_addressing",)]
        for w in HUB + ["tiebreak", "both"]:
            gg, bb = rate(g, var, w), rate(bd, var, w)
            if gg[1] and bb[1]:
                print(f"    {var:4s} {w:10s} good {fmt(gg)} bad {fmt(bb)}")

# spot-check list: 15 labels spread over classes (deterministic)
import random
rnd = random.Random(2970)
sc = []
for cl in ("boilerplate", "concession", "non_addressing", "substantive_real"):
    sc += rnd.sample([d for d in C if d["cls"] == cl], {"boilerplate": 3, "concession": 2, "non_addressing": 2, "substantive_real": 4}[cl])
sc += rnd.sample([d for d in F if d["cls"] == "restatement"], 2) + rnd.sample([d for d in F if d["cls"] == "non_sequitur"], 2)
json.dump([d["id"] for d in sc], open(r"C:\Nascence\docs\lab\J-2970_spotcheck_ids.json", "w"))
print("\nspot-check ids:", [d["id"] for d in sc])
