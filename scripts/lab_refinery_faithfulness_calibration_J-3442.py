"""J-3442: calibrate D-0627 faithfulness judge. Read-only on a backup copy of nascence.db. Resumable."""
import sys, json, sqlite3, random, asyncio, os, shutil, tempfile, hashlib, time
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r"C:/Nascence"; sys.path.insert(0, ROOT); os.chdir(ROOT)
from core import refinery as R
OUT = ROOT + "/docs/lab/J-3442_data"; os.makedirs(OUT, exist_ok=True)
RES = OUT + "/results.jsonl"
live = ROOT + "/data/memory/nascence.db"
h0 = (os.path.getsize(live), os.path.getmtime(live))
tmp = os.path.join(tempfile.gettempdir(), "J-3442_copy.db")
src = sqlite3.connect(f"file:{live}?mode=ro", uri=True); dst = sqlite3.connect(tmp); src.backup(dst); src.close()
rows = [json.loads(l) for l in open(ROOT + "/data/refinery_shadow.jsonl", encoding="utf-8")]
acc = [r for r in rows if r.get("accepted") and r.get("member_ids")]
def members(ids):
    q = ",".join("?" * len(ids))
    got = dst.execute(f"SELECT content,timestamp FROM memory_fragments WHERE fragment_id IN ({q}) ORDER BY timestamp DESC", ids).fetchall()
    return [g[0] or "" for g in got]
R.FAITH_TIMEOUT = 240
random.seed(3442)
pool = [r for r in acc[-300:] if len(members(r["member_ids"])) >= 3]
sample = random.sample(pool, 40)
done = set()
if os.path.exists(RES):
    for l in open(RES, encoding="utf-8"): done.add((json.loads(l)["i"], json.loads(l)["arm"]))
async def one(i, arm, ins, shown, total):
    for attempt in range(1):
        r = await R._judge_faithfulness(ins, shown, None, total)
        if r.get("supported") is not None: break
    return r
async def main():
    for i, r in enumerate(sample):
        own = members(r["member_ids"])
        other = random.choice([x for x in pool if not set(x["member_ids"]) & set(r["member_ids"])])
        oth = members(other["member_ids"])
        for arm, ms in (("neg", oth), ("pos", own)):
            if (i, arm) in done: continue
            res = await one(i, arm, r["insight"], ms[:R.MAX_MEMBERS_IN_PROMPT], len(ms))
            row = {"i": i, "arm": arm, "ts": r["ts"], "lex_fid": r.get("fidelity"), "lex_fid_shown": r.get("fidelity_shown"),
                   "would_accept_shown": r.get("would_accept_shown"), "supported": res["supported"], "why": res["why"], "err": res["err"], "el": res["elapsed_s"]}
            open(RES, "a", encoding="utf-8").write(json.dumps(row, ensure_ascii=False) + "\n")
            print(i, arm, res["supported"], res["err"], flush=True)
asyncio.run(main())
h1 = (os.path.getsize(live), os.path.getmtime(live)); print("live db unchanged:", h0 == h1)
