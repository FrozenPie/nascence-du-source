"""J-3550: widen the J-3013 capture-prompt replay. Phases: capture (repeats) -> judge (2-3 families). Isolated via lab_env.
python docs/lab/J-3550_widen_replay.py capture|judge <model>"""
import asyncio, json, sys, time, random, importlib.util
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Nascence"); sys.path.insert(0, str(ROOT))
import core  # noqa
from core import guidance_learning as G
from core.model_client import call_node_json
from core.schema import SERVE_CHAINS
sys.path.insert(0, "C:/Users/USER/.claude/skills/job-queue")
from lab_env import isolate
spec = importlib.util.spec_from_file_location("rp", ROOT / "scripts/lab_J-3013_capture_replay.py")
rp = importlib.util.module_from_spec(spec); spec.loader.exec_module(rp)
OUT = ROOT / "docs/lab/J-3550_data"
url = SERVE_CHAINS["hot"]

def sample():
    shadow = rp._jl(ROOT / "data/guidance_shadow_log.jsonl")
    full = {d.get("cycle_id"): d.get("human") for d in rp._jl(ROOT / "data/founder_conversation_log.jsonl")}
    pos = [r for r in shadow if r.get("is_guidance")]
    by = {r["cycle_id"]: r for r in pos}
    fails = [by[c] for c in rp.FAILURE_CYCLES if c in by]
    rest = [r for r in pos if r["cycle_id"] not in rp.FAILURE_CYCLES]
    newest = sorted(rest, key=lambda r: r["ts"], reverse=True)[:20]
    rng = random.Random(3013)
    pool = [r for r in rest if r not in newest and 1.7e9 < r["ts"] < time.mktime((2026, 10, 1, 0, 0, 0, 0, 0, -1))]
    others = newest + rng.sample(pool, max(0, min(len(pool), 31 - len(newest))))
    rows = [(r, rp.FAILURE_CYCLES[r["cycle_id"]], 5) for r in fails] + [(r, "other", 3) for r in others[:31]]
    return rows, full

async def capture():
    rows, full = sample()
    res = []
    with isolate(db="empty", also=[(G, ["_LOG"])]) as lab:
        for r, tag, reps in rows:
            raw = full.get(r["cycle_id"]) or r.get("raw_input") or ""
            runs = []
            for k in range(reps):
                before = G._LOG.read_text(encoding="utf-8").count("\n") if G._LOG.exists() else 0
                rec = None
                for attempt in range(2):
                    try:
                        rec = await G.capture_shadow(call_node_json, url, raw, r["cycle_id"], None); break
                    except Exception as e:
                        print("err", repr(e)[:80])
                lg = [json.loads(x) for x in G._LOG.read_text(encoding="utf-8").splitlines()[before:]] if G._LOG.exists() else []
                reason = None if rec else ((lg[-1].get("reason") or "model_negative") if lg else "no_call_or_gate")
                runs.append({"acc": bool(rec), "reason": reason, "principle": (rec or {}).get("principle", ""),
                             "quote": (rec or {}).get("quote", ""), "domain": (rec or {}).get("domain")})
            print(tag[:30], r["cycle_id"][:8], "".join("A" if x["acc"] else "r" for x in runs), flush=True)
            res.append({"cycle_id": r["cycle_id"], "tag": tag, "raw": raw, "old_principle": r.get("principle", ""), "runs": runs})
            (OUT / "capture_runs.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")

async def judge(model, jurl=None):
    res = json.loads((OUT / "capture_runs.json").read_text(encoding="utf-8"))
    cache = {}
    async def j(raw, p):
        k = (raw, p)
        if k not in cache:
            cache[k] = await rp._judge(jurl or url, model, raw, p)
            if cache[k][0] in ("error", "unparsed"):
                cache[k] = await rp._judge(jurl or url, model, raw, p)
        return cache[k]
    for x in res:
        x["old_v"] = (await j(x["raw"], x["old_principle"]))
        seen = 0
        for run in x["runs"]:
            if run["acc"]:
                seen += 1
                if x["tag"] == "other" and seen > 1: continue
                run["v"] = await j(x["raw"], run["principle"])
        print(x["tag"][:20], x["cycle_id"][:8], x["old_v"][0], flush=True)
    (OUT / f"judged_{model.replace(':','_')}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")

if __name__ == "__main__":
    asyncio.run(capture() if sys.argv[1] == "capture" else judge(sys.argv[2], (sys.argv[3] if len(sys.argv) > 3 else None)))
