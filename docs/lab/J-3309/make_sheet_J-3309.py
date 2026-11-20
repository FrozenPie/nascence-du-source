"""J-3309: 20-item blind X/Y/tie sheet for the founder (10 A05-vs-plain, 10 B-vs-plain, mixed human/internal, order randomised)."""
import json, random, sqlite3
D = r"C:\Nascence\docs\lab\J-3309"
Q = {q["cycle_id"]: q for q in json.load(open(D + r"\frozen_queries_J-3309.json", encoding="utf-8"))}
A = json.load(open(D + r"\arms_J-3309.json"))
cn = sqlite3.connect("file:C:/Nascence/data/memory/nascence.db?mode=ro", uri=True)
def content(fid):
    r = cn.execute("SELECT content FROM memory_fragments WHERE fragment_id=?", (fid,)).fetchone()
    t = " ".join((r[0] if r else "").split()); return t[:500] + ("..." if len(t) > 500 else "")
rng = random.Random(33093309)
items = []
for arm in ("A05", "B"):
    cand = [r for r in A if arm in r and {x["id"] for x in r[arm]} != {x["id"] for x in r["plain"]}]
    half = []
    for t in ("human", "internal"):
        pool = [r for r in cand if r["input_type"] == t]; rng.shuffle(pool); half += pool[:5]
    items += [(arm, r) for r in half]
rng.shuffle(items)
md = ["# J-3309 blind sheet: which set of memories would help more?", "",
      "For each item read the query, then pick X, Y or tie (a tie is fine). Judge: which set would help the entity more in answering or thinking about this? Reply as a list like `1 X, 2 tie, 3 Y ...`.", ""]
key = []
for n, (arm, r) in enumerate(items, 1):
    q = Q[r["cycle_id"]]
    a_ids = [x["id"] for x in r[arm]]; p_ids = [x["id"] for x in r["plain"]]
    a_only = [i for i in a_ids if i not in p_ids]; p_only = [i for i in p_ids if i not in a_ids]
    arm_is_x = rng.random() < 0.5
    X, Y = (a_only, p_only) if arm_is_x else (p_only, a_only)
    key.append({"n": n, "cycle_id": r["cycle_id"], "arm": arm, "arm_is_x": arm_is_x, "input_type": q["input_type"]})
    md += [f"## Item {n}", f"**Query:** {q['raw_input'][:500]}", f"**Summary:** {q['summary'][:300]}", "", "**Set X**"]
    md += [f"- {content(i)}" for i in X] + ["", "**Set Y**"] + [f"- {content(i)}" for i in Y] + [""]
open(r"C:\Nascence\docs\reviews\J-3309_blind_sheet.md", "w", encoding="utf-8").write("\n".join(md))
json.dump(key, open(D + r"\sheet_key_J-3309.json", "w"), indent=1)
print(len(items), "items")
