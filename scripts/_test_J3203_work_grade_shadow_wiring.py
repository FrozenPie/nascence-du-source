"""J-3203 (D-0591 part 2 wiring): nodes/inner_monologue_node._author files the work FIRST, then records the Emissary's
grade to the shadow log; nothing is fed back.

  [1] source order inside _author: write_tablet precedes work_grade_shadow.grade_and_record; no direct grade_work call.
  [2] the log suffix reads grade['grounded'] (the old 'score' key the grader never returned is gone).
  [3] grade_and_record writes one row to a TEMP shadow log (stubbed grader), fail-open row when the grader returns None.
  [4] the docstring no longer says the work is 'Witnessed by the Emissary'.
Writes only under a temp dir; touches no live data.   python scripts/_test_J3203_work_grade_shadow_wiring.py
"""
from __future__ import annotations

import asyncio
import json
import sys
import tempfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # noqa: E402  (BEFORE anything else)

assert Path(core.__file__).resolve().parent.parent == ROOT, core.__file__

from core import work_grade_shadow as wgs  # noqa: E402
from core import left_lane  # noqa: E402

src = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
i0 = src.index("    async def _author(")
i1 = src.index("    async def _evidence_recall(")
body = src[i0:i1]

# [1]
assert "grade_work(" not in body, "direct grade_work call still in _author"
iw = body.index("write_tablet(")
ig = body.index("_wgs.grade_and_record(")
assert iw < ig, "grade is still taken before the work is filed"
print("[1] ok: write_tablet before grade_and_record, no direct grade_work")
# [2]
assert "grade.get('grounded')" in body and "grade.get('score')" not in body
print("[2] ok: suffix reads grounded")
# [4]
assert "Witnessed by the Emissary" not in body
print("[4] ok: docstring honest")

# [3]
tmp = Path(tempfile.mkdtemp(prefix="J3203_"))
wgs.SHADOW_LOG = tmp / "work_grade_shadow.jsonl"


async def _run():
    async def fake(topic, ref, work):
        return {"grounded": 0.42, "feedback": "x"}
    left_lane.grade_work = fake
    g = await wgs.grade_and_record("a topic", "A Title", "word " * 900)
    assert g and g["grounded"] == 0.42
    async def none(topic, ref, work):
        return None
    left_lane.grade_work = none
    g2 = await wgs.grade_and_record("a topic", "B Title", "word " * 900)
    assert g2 is None

asyncio.run(_run())
rows = [json.loads(l) for l in wgs.SHADOW_LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
assert len(rows) == 2, rows
assert rows[0]["grounded"] == 0.42 and rows[0]["fail_open"] is False
assert rows[1]["grounded"] is None and rows[1]["fail_open"] is True
assert rows[0]["graded_chars"] == 2000 and rows[0]["chars"] == 4500
print("[3] ok: 2 rows in temp log")
print("ALL OK")
