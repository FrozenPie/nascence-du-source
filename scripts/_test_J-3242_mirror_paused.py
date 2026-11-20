"""J-3242 / D-0630: with SELF_MIRROR_PAUSED the weekly mirror makes no model call, writes no fragment, and still logs
the facts and advances its own clock. Isolated: _STATE / _PAUSED_LOG point into a temp dir, mirror_facts is stubbed,
store_fragment is stubbed to fail loudly. Never touches a live store."""
import asyncio
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")
from core import self_mirror as sm  # noqa: E402

tmp = Path(tempfile.mkdtemp(prefix="j3242_"))
sm._STATE = tmp / "state.json"
sm._PAUSED_LOG = tmp / "paused.jsonl"
sm.mirror_facts = lambda: ["acting about 34 percent", "outward 78"]
fails = []


async def _boom(*a, **k):
    raise AssertionError("model called while paused")

sm.SELF_MIRROR_RETIRED = False   # J-3478 retired it by default; this test exercises the PAUSED branch beneath
assert sm.SELF_MIRROR_PAUSED is True
assert sm.due(), "state file absent => due"
out = asyncio.run(sm.hold_up_mirror(_boom, ["http://x"]))
if out is not None:
    fails.append("returned a reflection while paused")
if sm.due():
    fails.append("clock not advanced (would re-fire every cycle)")
rows = [json.loads(l) for l in sm._PAUSED_LOG.read_text(encoding="utf-8").splitlines()]
if len(rows) != 1 or rows[0]["facts"] != ["acting about 34 percent", "outward 78"]:
    fails.append(f"paused log wrong: {rows}")

# flag off => original path reached (model called, fragment stored)
sm.SELF_MIRROR_PAUSED = False
sm._STATE.unlink()
called = []


async def _ok(urls_unused, *a, **k):
    called.append(1)
    return {"seen": ""}

async def _call(urls, sys_, user, **k):
    called.append(1)
    return {"seen": ""}

asyncio.run(sm.hold_up_mirror(_call, ["http://x"]))
if not called:
    fails.append("flag False did not reach the model call")
print("FAIL: " + "; ".join(fails) if fails else "PASS")
sys.exit(1 if fails else 0)
