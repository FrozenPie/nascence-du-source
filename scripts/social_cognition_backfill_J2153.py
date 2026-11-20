"""J-2153: backfill core/social_cognition_shadow over every human cycle since 2026-09-28 against the REAL decoupled
judge panel. SHADOW ONLY. Reads C:/Nascence/data/founder_conversation_log.jsonl (read-only), writes rows to
C:/Nascence/data/social_cognition_shadow.jsonl, redirects the judge panel's own log away from the live one, and caps
hub asks (judge_panel._ask is counted). Idempotent on cycle_id. Du must be down; this starts no server.
Usage: python scripts/social_cognition_backfill_J2153.py [--max-asks 350] [--max-items 30] [--dry]"""
import argparse, asyncio, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core
from core import social_cognition_shadow as S, judge_panel as jp

LIVE = pathlib.Path(r"C:/Nascence/data")
ap = argparse.ArgumentParser()
ap.add_argument("--max-asks", type=int, default=350)
ap.add_argument("--max-items", type=int, default=30)
ap.add_argument("--dry", action="store_true")
a = ap.parse_args()

S._CONV_LOG = LIVE / "founder_conversation_log.jsonl"
S._LOG = LIVE / "social_cognition_shadow.jsonl"
S._STATE = LIVE / "social_cognition_shadow_state.json"
lab = LIVE / "lab" / "J-2153"
lab.mkdir(parents=True, exist_ok=True)
jp._LOG = lab / "judge_panel_log_social.jsonl"

n = {"asks": 0}
_orig = jp._ask
async def counted(*args, **kw):
    if n["asks"] >= a.max_asks:
        return (None, None, "exception", 0.0)
    n["asks"] += 1
    return await _orig(*args, **kw)
jp._ask = counted

turns = S.load_turns()
todo = [t for t in turns if t["ts"] >= S.BACKFILL_SINCE_TS]
print("human turns since 09-28:", len(todo), "already scored:", len(S._scored_ids()))
if a.dry:
    sys.exit(0)
r = asyncio.run(S.sweep(max_items=a.max_items, backfill=True))
print("sweep:", r, "hub asks:", n["asks"])
import json
print(json.dumps(S.status(), ensure_ascii=False, indent=1))
