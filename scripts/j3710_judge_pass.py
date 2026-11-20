"""J-3710: post-hoc judge pass (gemma4:12b :11439) over docs/lab/J-3710_data/chapter_prompt_ab_r7b.json; writes judge fields back. Sequential, resumable."""
import asyncio, json, sys, sqlite3
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, "C:/Users/USER/.claude/skills/job-queue")
import core  # noqa
from core import chapters as ch
from core.model_client import call_node_json
from lab_env import isolate
from scripts import j3011_chapter_prompt_ab as ab
from scripts.j3710_chapter_prompt_ab_r7b import JSYS, OUT
async def main():
    d = json.loads(OUT.read_text(encoding="utf-8")); conn = sqlite3.connect("file:C:/Nascence/data/memory/nascence.db?mode=ro&immutable=1", uri=True)
    fails = 0
    for pre, v in d["clusters"].items():
        cid, cl = ab.load_cluster(conn, pre); st = ch._sample(cl)
        for arm, runs in v["arms"].items():
            for r in runs:
                if "judge" in r or "failed" in r: continue
                try:
                    j = await call_node_json(["http://127.0.0.1:11439"], JSYS, f"SAMPLE:\n{st}\n\nCHAPTER:\n{r['chapter']}", max_tokens=200, temperature=0.0, timeout=150, retries=1)
                    r["judge"] = {"unsampled_feeling": bool(j.get("unsampled_feeling")), "feelings": j.get("feelings", [])}; r.pop("judge_failed", None); fails = 0
                except Exception as e:
                    r["judge_failed"] = str(e)[:100]; fails += 1
                    if fails >= 4: OUT.write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding="utf-8"); raise SystemExit("judge hub unusable")
                print(pre, arm, r.get("judge"), flush=True)
        OUT.write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding="utf-8")
with isolate(db="empty"): asyncio.run(main())
