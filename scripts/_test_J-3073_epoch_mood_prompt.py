"""Hermetic test for J-3073 (P-0071, F-3778): the /quit epoch prompt no longer carries copied mood examples.

Run from the worktree root:  python scripts/_test_J-3073_epoch_mood_prompt.py
- imports core FIRST and asserts it came from this tree; temp memory DB; the model call and the
  fragment read are stubbed, no hub is contacted, no live store is touched.
Covers: (1) the system prompt sent by _form_epoch contains none of the three old example strings
and no "e.g."; (2) it still asks for a 2-4 word mood and a two-field JSON; (3) the stored epoch is
what the stub returned (the write path is unchanged); (4) too few fragments still skips the call.
"""
from __future__ import annotations
import asyncio
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  -- BEFORE lab_env
assert Path(core.__file__).resolve().is_relative_to(ROOT), f"core imported from {core.__file__}, not {ROOT}"

import core.memory.store as store  # noqa: E402
_tmp = Path(tempfile.mkdtemp(prefix="j3073_"))
store.DB_PATH = _tmp / "test.db"
store._embed = lambda text: None
store.init_db()  # J-3789: the temp DB needs its own schema, or any memory_fragments read fails in a fresh tree

import scripts.run_nascence as rn  # noqa: E402
assert Path(rn.__file__).resolve().is_relative_to(ROOT)

import core.model_client as mc  # noqa: E402

calls = []
stored = []


async def _fake_call(chain, system, user, **kw):
    calls.append({"system": system, "user": user, "kw": kw})
    return {"mood": "steady unease", "impression": "I worked through the same question again."}


mc.call_node_json = _fake_call           # _form_epoch imports it from core.model_client at call time
rn.store_epoch = lambda **kw: stored.append(kw) or "abcdef12-0000"
frags = [{"origin": "lived", "content": f"fragment {i}"} for i in range(5)]
rn.get_fragments_spread = lambda a, b, n=25: frags  # J-3789: _form_epoch reads get_fragments_spread since J-3071

state = type("S", (), {"spirit_name": "Tester"})()
asyncio.run(rn._form_epoch(state, 0.0))

assert len(calls) == 1, calls
sysmsg = calls[0]["system"]
for banned in ("anxious precision", "quiet expansion", "restless circling", "e.g."):
    assert banned not in sysmsg, f"{banned!r} still in epoch prompt"
assert "mood: 2" in sysmsg and "own words" in sysmsg
assert '{"mood": "...", "impression": "..."}' in sysmsg
assert len(stored) == 1 and stored[0]["mood"] == "steady unease"
assert stored[0]["fragment_count"] == 5

calls.clear(); stored.clear()
rn.get_fragments_spread = lambda a, b, n=25: frags[:2]  # J-3789: _form_epoch reads get_fragments_spread since J-3071
asyncio.run(rn._form_epoch(state, 0.0))
assert not calls and not stored

print("J-3073 epoch mood prompt: all checks passed")
