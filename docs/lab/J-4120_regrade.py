"""J-4120: regrade the ungraded (grader None) arm-rows of J-2875 results. Output J-4120_regrade.jsonl (resumable)."""
import sys, json, os, asyncio, time
sys.path.insert(0, "C:/Nascence"); sys.path.insert(0, "C:/Users/USER/.claude/skills/job-queue")
sys.stdout.reconfigure(encoding="utf-8")
from core import memory_levels as ml
from core import left_lane as LL
from lab_env import isolate
D = "C:/Nascence/docs/lab/J-2875_data/"; OUT = "C:/Nascence/docs/lab/J-4120_regrade.jsonl"
async def one(it, row, arm, sem):
    async with sem:
        full = [" ".join((c or "").split()) for c in it["contents"]]
        t = time.time()
        g = await LL.grade_gist_faithfulness(row["gist"], [s[:800] for s in full])
        inv = (g or {}).get("invented", []) if isinstance(g, dict) else []
        claims = ml.verify_invention_claims(inv, full) if inv else []
        gen = sum(1 for c in claims if c[1] == "GENUINE")
        f = g.get("faithful") if isinstance(g, dict) else None
        r = dict(idx=it["idx"], arm=arm, grade=g, genuine=gen, secs=round(time.time()-t,1),
                 commit=bool(isinstance(f,(int,float)) and f >= ml.FAITHFUL_FLOOR and gen == 0))
        open(OUT, "a", encoding="utf-8").write(json.dumps(r, ensure_ascii=False) + "\n")
        print(it["idx"], arm, f, flush=True)
async def main():
    items = {i["idx"]: i for i in json.load(open(D+"J-2875_items.json", encoding="utf-8"))}
    done = set()
    if os.path.exists(OUT):
        for l in open(OUT, encoding="utf-8"):
            j = json.loads(l)
            if isinstance(j.get("grade"), dict): done.add((j["idx"], j["arm"]))
    rows = [json.loads(l) for l in open(D+"J-2875_results.jsonl", encoding="utf-8")]
    sem = asyncio.Semaphore(int(os.environ.get("WORKERS", "3")))
    tasks = []
    for r in rows:
        for arm in "AB":
            a = r[arm]
            if a.get("gist") and not isinstance(a.get("grade"), dict) and (r["idx"], arm) not in done:
                tasks.append(one(items[r["idx"]], a, arm, sem))
    print("todo", len(tasks), flush=True)
    await asyncio.gather(*tasks)
with isolate(db="empty") as lab:
    asyncio.run(main())
