"""J-3309 step 1: freeze the 100-query set BEFORE any arm is scored. Seed 3163.
50 human (distinct raw_input) + 50 internal; rows ts>=2026-08-08 from data/training/memory_router.jsonl.
Pure file read; touches no DB, no model."""
import json, random, re, datetime, hashlib
SRC = r"C:\Nascence\data\training\memory_router.jsonl"
OUT = r"C:\Nascence\docs\lab\J-3309\frozen_queries_J-3309.json"
t0 = datetime.datetime(2026, 8, 8).timestamp()
rows = [json.loads(l) for l in open(SRC, encoding="utf-8")]
rows = [r for r in rows if r["ts"] >= t0 and isinstance(r.get("output"), dict)]
def summ(up):
    m = re.search(r"\nSummary: (.*?)(?:\nKey entities:|\Z)", up, re.S)
    return m.group(1).strip() if m else ""
rng = random.Random(3163)
out = []
for typ, n in (("human", 50), ("internal", 50)):
    pool = [r for r in rows if r["input_type"] == typ and (r.get("raw_input") or "").strip()]
    if typ == "human":
        seen = {}
        for r in pool: seen.setdefault(r["raw_input"].strip(), r)   # first row per distinct raw_input
        pool = list(seen.values())
    pool.sort(key=lambda r: r["cycle_id"] + str(r["ts"]))
    pick = rng.sample(pool, n)
    for r in pick:
        o = r["output"]
        out.append({"cycle_id": r["cycle_id"], "ts": r["ts"], "input_type": typ, "raw_input": r["raw_input"],
                    "summary": summ(r["user_prompt"]), "episodic_keys": o.get("episodic_keys") or [],
                    "semantic_keys": o.get("semantic_keys") or [], "time_bias": o.get("time_bias") or "recent"})
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(out), "frozen;", sum(1 for q in out if not q["summary"]), "without summary; sha1",
      hashlib.sha1(open(OUT, "rb").read()).hexdigest()[:12])
