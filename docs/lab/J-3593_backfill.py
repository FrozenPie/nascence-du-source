"""J-3593 lab: backfill decoupled social tracks_intent verdicts over uncovered HUMAN voice rows.
Isolated (lab_env.isolate db=empty); judge hubs overridden to LOCAL hubs (no Ramses): JUDGE_1 gemma4:12b :11439,
JUDGE_2 falcon3:7b :11440, TIEBREAK yi:34b :11442. Only the tracks_intent key is run (the only social key the voice-set
builder reads; its prompt does not use earlier turns, so this equals score_turn's tracks_intent ruling).
Output: docs/lab/J-3593_data/social_shadow_backfill.jsonl (social_cognition_shadow-shaped rows, prompt_v 5).
Resumable (skips cycle_ids already scored). Usage: python docs/lab/J-3593_backfill.py [--limit N] [--budget-s S]"""
import argparse, asyncio, json, pathlib, sys, time
ROOT = pathlib.Path("C:/Nascence")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
import core  # noqa: F401  (before lab_env)
sys.path.insert(0, "C:/Users/USER/.claude/skills/job-queue")
from lab_env import isolate
from core import social_cognition_shadow as S, judge_panel as jp
import build_voice_set as B

ap = argparse.ArgumentParser()
ap.add_argument("--limit", type=int, default=0)
ap.add_argument("--budget-s", type=float, default=0)
ap.add_argument("--list", action="store_true")
a = ap.parse_args()

OUT = ROOT / "docs/lab/J-3593_data"
OUT.mkdir(parents=True, exist_ok=True)
SHADOW = OUT / "social_shadow_backfill.jsonl"
DATA = ROOT / "data"

src = B.load_sources(DATA)
conv = {str(t.get("cycle_id")): t for t in S.load_turns(DATA / "founder_conversation_log.jsonl")}
todo = []
for r in B._rows(DATA / "training" / "voice.jsonl"):
    if r.get("input_type") != "human":
        continue
    if B.decide_row(r, src, B.ALL_SOURCES)["status"] != "uncovered":
        continue
    cid = str(r["cycle_id"])
    fin, hu = B._final(r), (r.get("raw_input") or "").strip()
    if cid in conv:      # real logged turn: judge the reply Travis actually received
        t = conv[cid]
        todo.append({"cycle_id": cid, "ts": t["ts"], "human": t.get("human") or "", "entity": t.get("entity") or "", "src": "conv_log"})
    elif fin and hu:
        todo.append({"cycle_id": cid, "ts": float(r["ts"]), "human": hu, "entity": fin, "src": "voice_row"})
seen, uniq = set(), []
for t in todo:
    if t["cycle_id"] not in seen:
        seen.add(t["cycle_id"]); uniq.append(t)
todo = uniq
print("uncovered human cycles to judge:", len(todo), "by src:", {k: sum(1 for t in todo if t["src"] == k) for k in ("conv_log", "voice_row")})
if a.list:
    sys.exit(0)

done = set()
if SHADOW.exists():
    for l in open(SHADOW, encoding="utf-8"):
        try:
            done.add(json.loads(l).get("cycle_id"))
        except Exception:
            pass
todo = [t for t in todo if t["cycle_id"] not in done]
if a.limit:
    todo = todo[:a.limit]
print("remaining this run:", len(todo))


async def main():
    jp.JUDGE_1 = "http://127.0.0.1:11439"
    jp.JUDGE_2 = "http://127.0.0.1:11440"
    jp.TIEBREAK = "http://127.0.0.1:11442"
    t0 = time.monotonic()
    n = ok = 0
    for t in todo:
        if a.budget_s and time.monotonic() - t0 > a.budget_s:
            print("budget stop"); break
        n += 1
        d = await jp.rule_detail(S._SYS["tracks_intent"], S._user("tracks_intent", t["human"], t["entity"], []),
                                 "tracks", context=f"J3593:{t['cycle_id'][:8]}", cycle_id=t["cycle_id"], node="voice")
        row = {"ts": round(time.time(), 1), "cycle_id": t["cycle_id"], "human_ts": t["ts"], "backfill": True,
               "prompt_v": S.PROMPT_V, "kind": S.classify_kind(t["human"]), "src": t["src"],
               "tracks_intent": d.get("verdict"), "how": d.get("how"), "v1": d.get("v1"), "v2": d.get("v2"),
               "err1": d.get("err1"), "err2": d.get("err2")}
        if d.get("verdict") is not None:
            ok += 1
        with open(SHADOW, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        if n % 25 == 0:
            print(f"{n}/{len(todo)} ok={ok} {time.monotonic()-t0:.0f}s", flush=True)
    print(f"done {n} ok={ok} {time.monotonic()-t0:.0f}s ({(time.monotonic()-t0)/max(n,1):.1f}s/row)")

with isolate(db="empty", also=[(jp, ["_LOG", "_INPUTS_LOG"]), (S, ["_LOG", "_STATE"])]) as lab:
    print("lab dir", lab)
    asyncio.run(main())
