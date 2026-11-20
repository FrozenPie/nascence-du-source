"""J-4127: breadth-first, checkpointed judge sweep over J-3710 chapter A/B outputs. Usage: j4127_judge_sweep.py <hub_url> <tag> <concurrency>
Reads chapter_prompt_ab_r7b.json (read-only) + live DB ro; appends one row per call to docs/lab/J-4127_judge_<tag>.jsonl; resumable."""
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
hub, tag, conc = sys.argv[1], sys.argv[2], int(sys.argv[3])
LOG = ROOT / f"docs/lab/J-4127_judge_{tag}.jsonl"
async def main():
    d = json.loads(OUT.read_text(encoding="utf-8")); conn = sqlite3.connect("file:C:/Nascence/data/memory/nascence.db?mode=ro&immutable=1", uri=True)
    done = set()
    if LOG.exists():
        for l in LOG.read_text(encoding="utf-8").splitlines():
            r = json.loads(l)
            if "judge" in r: done.add((r["pre"], r["arm"], r["i"]))
    samples = {pre: ch._sample(ab.load_cluster(conn, pre)[1]) for pre in d["clusters"]}
    jobs = []
    maxn = max(len(r) for v in d["clusters"].values() for r in v["arms"].values())
    for i in range(maxn):
        for pre, v in d["clusters"].items():
            for arm, runs in v["arms"].items():
                if i < len(runs) and (pre, arm, i) not in done: jobs.append((pre, arm, i, runs[i]["chapter"]))
    q = asyncio.Queue()
    for j in jobs: q.put_nowait(j)
    async def w():
        while not q.empty():
            pre, arm, i, chap = q.get_nowait()
            row = {"pre": pre, "arm": arm, "i": i}
            try:
                j = await call_node_json([hub], JSYS, f"SAMPLE:\n{samples[pre]}\n\nCHAPTER:\n{chap}", max_tokens=200, temperature=0.0, timeout=240, retries=0)
                row["judge"] = {"unsampled_feeling": bool(j.get("unsampled_feeling")), "feelings": j.get("feelings", [])}
            except Exception as e:
                row["failed"] = str(e)[:100]
            with LOG.open("a", encoding="utf-8") as f: f.write(json.dumps(row) + "\n")
    await asyncio.gather(*[w() for _ in range(conc)])
with isolate(db="empty"): asyncio.run(main())
