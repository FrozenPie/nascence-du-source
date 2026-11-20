"""J-3309: offline structural guards (no LLM): origin mix of added vs dropped, top-1 plain hit removal, human vs internal change."""
import json, sqlite3, collections
D = r"C:\Nascence\docs\lab\J-3309"
A = json.load(open(D + r"\arms_J-3309.json")); Q = {q["cycle_id"]: q for q in json.load(open(D + r"\frozen_queries_J-3309.json", encoding="utf-8"))}
cn = sqlite3.connect("file:C:/Nascence/data/memory/nascence.db?mode=ro", uri=True)
org = {}
def o(i):
    if i not in org:
        r = cn.execute("SELECT origin FROM memory_fragments WHERE fragment_id=?", (i,)).fetchone(); org[i] = r[0] if r else "?"
    return org[i]
for arm in ("A05", "A025", "B", "N"):
    add = collections.Counter(); drop = collections.Counter(); top1 = 0; n = 0; ch = {"human": [], "internal": []}
    for r in A:
        if arm not in r: continue
        n += 1; p = [x["id"] for x in r["plain"]]; a = [x["id"] for x in r[arm]]
        for i in a:
            if i not in p: add[o(i)] += 1
        for i in p:
            if i not in a: drop[o(i)] += 1
        t1 = max(r["plain"], key=lambda x: x["score"])["id"]
        if t1 not in a: top1 += 1
        ch[r["input_type"]].append(len(set(p) - set(a)))
    sh = lambda c: {k: round(v / max(1, sum(c.values())), 2) for k, v in c.most_common(5)}
    print(arm, "n", n, "top1_removed", top1, "chg human %.2f internal %.2f" % tuple(sum(v) / len(v) for v in (ch["human"], ch["internal"])),
          "\n  added", sh(add), "inner_thought share", round(add["inner_thought"] / max(1, sum(add.values())), 2), "vs dropped", round(drop["inner_thought"] / max(1, sum(drop.values())), 2),
          "\n  lived added/dropped", add["lived"], drop["lived"], "of", sum(add.values()))
