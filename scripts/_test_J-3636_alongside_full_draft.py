"""J-3636: shadow_alongside logs up to 2000 chars of draft and 600 of raw (hermetic: temp log path)."""
import sys, json, asyncio, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import core
from core import decomposed_critic as dc
assert Path(dc.__file__).resolve().is_relative_to(Path(core.__file__).resolve().parent.parent)
tmp = Path(tempfile.mkdtemp()) / "alongside.jsonl"
dc._ALONGSIDE = tmp
async def fake(*a, **k):
    return {"approved": True, "violations": [], "requested_modes": [], "judge_ok": True, "error": None}
dc.evaluate = fake
asyncio.run(dc.shadow_alongside("d" * 5000, "r" * 5000, legacy_approved=True, cycle_id="t"))
rec = json.loads(tmp.read_text(encoding="utf-8").splitlines()[0])
assert len(rec["draft"]) == 2000 and len(rec["raw"]) == 600, (len(rec["draft"]), len(rec["raw"]))
print("ALL OK")
