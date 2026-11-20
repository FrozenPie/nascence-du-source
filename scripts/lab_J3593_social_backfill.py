"""J-3593 lab: backfill decoupled social verdicts (score_turn path) over UNCOVERED human voice rows, isolated.
Never writes live data/. Judge log + social log redirected into the isolate lab dir. Usage:
  python scripts/lab_J3593_social_backfill.py --n 12 [--conv-only]"""
import argparse, asyncio, json, pathlib, sys, time, shutil
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core
sys.path.insert(0, "C:/Users/USER/.claude/skills/job-queue")
from lab_env import isolate
from core import social_cognition_shadow as S, judge_panel as jp

ap = argparse.ArgumentParser()
ap.add_argument("--n", type=int, default=12)
ap.add_argument("--conv-only", action="store_true")
a = ap.parse_args()
D = ROOT / "data"
def rows(p):
    for l in open(p, encoding="utf-8", errors="replace"):
        try: yield json.loads(l)
        except Exception: pass
scored = {r.get("cycle_id") for r in rows(D/"social_cognition_shadow.jsonl") if "tracks_intent" in r}
conv = [c for c in rows(D/"founder_conversation_log.jsonl")]
convids = {str(c["cycle_id"]) for c in conv}
todo = [c for c in conv if str(c["cycle_id"]) not in scored]
if not a.conv_only:
    for r in rows(D/"training"/"voice.jsonl"):
        cid = str(r.get("cycle_id"))
        if r.get("input_type") != "human" or cid in scored or cid in convids: continue
        o = r.get("output"); fin = o.get("final") if isinstance(o, dict) else None
        if not fin or not r.get("raw_input"): continue
        todo.append({"ts": float(r["ts"]), "cycle_id": cid, "human": r["raw_input"], "entity": fin})
todo = sorted({str(t["cycle_id"]): t for t in todo}.values(), key=lambda t: t["ts"])
print("uncovered candidates:", len(todo))
step = max(1, len(todo)//a.n)
sample = todo[::step][:a.n]
# context turns (prior) come from the same temp log: include whole todo+conv so prior_turns has context
with isolate(db="empty", also=[(S, ["_LOG", "_STATE"]), (jp, ["_LOG"])]) as lab:
    tmp = pathlib.Path(lab) / "J3593_conv.jsonl"
    with open(tmp, "w", encoding="utf-8") as f:
        for t in sample: f.write(json.dumps(t, ensure_ascii=False) + "\n")
    t0 = time.time()
    r = asyncio.run(S.sweep(since_ts=0, max_items=a.n, backfill=True, conv_path=tmp))
    dt = time.time() - t0
    out = [x for x in rows(S._LOG) if "tracks_intent" in x]
    print("sweep", r, "secs", round(dt, 1), "per-turn", round(dt/max(1,len(out)), 1))
    import collections
    print("tracks_intent", collections.Counter(x["tracks_intent"] for x in out))
    dst = ROOT/"docs/lab/J-3593_data"/f"sample_n{a.n}.jsonl"
    shutil.copy(S._LOG, dst); print("lab dir", lab)
