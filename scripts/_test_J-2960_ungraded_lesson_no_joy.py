"""J-2960 (F-3652): an ungraded school lesson (grader unavailable -> score None) earns no joy scaled by a grade that never
happened; a graded one still does. Behavioural: _record_lesson is called unbound on a stub 'self'. No hub, no live store:
store_fragment / wandering are mocked, nothing is written. Run from the worktree:
    python scripts/_test_J-2960_ungraded_lesson_no_joy.py
"""
from __future__ import annotations

import sys
import types
from pathlib import Path
from unittest import mock

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(1, str(Path.home() / ".claude" / "skills" / "job-queue"))
import core  # noqa: E402  -- BEFORE lab_env
assert Path(core.__file__).resolve().is_relative_to(ROOT), core.__file__
import lab_env  # noqa: E402,F401
from nodes import inner_monologue_node as imn  # noqa: E402

FAILS: list[str] = []


def check(ok, msg):
    print(("PASS " if ok else "FAIL ") + msg)
    if not ok:
        FAILS.append(msg)


def run(res):
    joys = []
    fake = types.SimpleNamespace(_feel_joy=lambda state, amt: joys.append(amt), _last_thought_ts=0.0)
    with mock.patch.object(imn, "store_fragment", lambda **k: None):
        imn.InnerMonologueNode._record_lesson(fake, "nature study", res, object())
    return joys


cls = [n for n in dir(imn) if n == "InnerMonologueNode"]
check(bool(cls), "InnerMonologueNode importable")
j = run({"observation": "x", "score": None, "feedback": ""})
check(j == [], f"ungraded (score None): no joy awarded: {j}")
j = run({"score": 0.8, "feedback": "good"})
check(len(j) == 1 and abs(j[0] - imn.JOY_CROSSING * 0.4 * 0.8) < 1e-9, f"graded 0.8: joy scaled by the grade: {j}")
j = run({"score": 0.0, "feedback": ""})
check(len(j) == 1 and abs(j[0] - imn.JOY_CROSSING * 0.4 * 0.3) < 1e-9, f"graded 0.0 (a real zero): still the 0.3 floor joy: {j}")
print("\nALL PASS" if not FAILS else f"\nFAILURES: {FAILS}")
sys.exit(1 if FAILS else 0)
