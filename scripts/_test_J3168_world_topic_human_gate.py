"""J-3168 (D-0557): Perception.subject == 'the_world' may set content_mode only on a human cycle.

  [1] internal / timer cycle with subject the_world -> _is_world_topic False
  [2] human cycle with subject the_world -> True; other subjects -> False
  [3] the other content_mode triggers (_human_requested_direct_mode, _is_correction_context) are untouched
Builds a bare Orchestrator via __new__ with a stub state; touches no live data.
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # noqa: E402  (BEFORE lab_env / anything else)

assert Path(core.__file__).resolve().parent.parent == ROOT, core.__file__

from core.orchestrator import Orchestrator  # noqa: E402

o = object.__new__(Orchestrator)


def st(input_type, subject, raw="x", hist=None):
    return SimpleNamespace(input_type=input_type, perception=SimpleNamespace(subject=subject),
                           raw_input=raw, conversation_history=hist or [])


for it in ("internal", "timer"):
    o.state = st(it, "the_world")
    assert o._is_world_topic() is False, it
print("[1] ok: non-human the_world does not trigger")

o.state = st("human", "the_world")
assert o._is_world_topic() is True
for sub in ("the_entity", "the_person", "mixed", ""):
    o.state = st("human", sub)
    assert o._is_world_topic() is False, sub
o.state = SimpleNamespace(input_type="human", perception=None, raw_input="", conversation_history=[])
assert o._is_world_topic() is False
print("[2] ok: human the_world triggers, others do not")

# other triggers do not read input_type: unchanged behaviour on an internal cycle
o.state = st("internal", "the_entity", raw="explain how a clock works")
assert o._human_requested_direct_mode() is True
o.state = st("internal", "the_entity", raw="you did not answer my question")
assert o._is_correction_context() is True
print("[3] ok: other triggers unchanged")
print("ALL OK")
