"""J-2852 / F-3510 / D-0531: the System-2 think license no longer turns an empty reply into a failed node.

Offline, model calls STUBBED (core.model_client.call_node), no live data (telemetry path points at a temp dir,
training log off). Covers:
  1. call_node_json, think=True, lane returns '' for think=True and valid JSON for think=False: returns the dict
     after exactly TWO calls (think True then False), at the caller's normal max_tokens on the second -- not 3
     certain failures. Also with retries=0 (the downgrade earns one attempt of its own).
  2. think=True and the lane answers properly: ONE call, think stays True (the license still works when it works).
  3. think=False and the lane returns '': behaviour unchanged (retries+1 calls, then ValueError).
  4. think=True and the lane returns '' for BOTH: bounded -- one think call plus the normal retries, ValueError.
  5. NodeBase.run on the real ExecutiveNode with think_license set: the stub's empty think reply is downgraded and
     the node SUCCEEDS (state.executive written) -- the human-turn Executive no longer fails into silence.
  6. telemetry.log_llm_latency: `t`=1 only on a think call.
  7. source: orchestrator names a FAILED Executive / Critic separately from the chosen silence, and re-runs the
     Executive once, only for input_type == "human"; the chosen-silence log line is still there.
Run from the worktree:  python scripts/_test_J-2852_think_downgrade.py
"""
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789: no write to the tree's data/
import asyncio
import json
import os
import re
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ["NASCENCE_TRAINING_LOG"] = "0"
TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TREE))
import core                                             # noqa: E402  (core BEFORE lab_env)
assert TREE in Path(core.__file__).resolve().parents, core.__file__
from core import model_client as mc                     # noqa: E402
from core import telemetry                              # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="J-2852_"))
telemetry._DATA = TMP
telemetry._LAT = TMP / "llm_latency.jsonl"

GOOD = json.dumps({"synthesis": "I think the lamp is mine.", "should_respond": True,
                   "response_type": "answer", "reasoning": "", "epistemic_query": None})
URL = "http://127.0.0.1:11433"
calls = []


def stub(think_reply, plain_reply):
    async def fake(base_url, system, user, *, max_tokens=512, temperature=0.2, timeout=120, json_mode=True,
                   think=False, model_override=None, num_gpu=None, tier=None, grammar=None):
        calls.append({"think": think, "max_tokens": max_tokens})
        return think_reply if think else plain_reply
    mc.call_node = fake


def run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


# 1. downgrade after one empty think reply
stub("", GOOD)
calls.clear()
out = run(mc.call_node_json([URL], "s", "u", max_tokens=1536, think=True))
assert out["synthesis"].startswith("I think"), out
assert [c["think"] for c in calls] == [True, False], calls
assert calls[1]["max_tokens"] == 1536, calls            # the normal budget, not the raised one
calls.clear()
out = run(mc.call_node_json([URL], "s", "u", max_tokens=512, think=True, retries=0))
assert out["should_respond"] is True and [c["think"] for c in calls] == [True, False], calls
print("1 ok: empty think reply -> think=False retry, 2 calls (also with retries=0)")

# 2. a think reply that works keeps think on
stub(GOOD, "")
calls.clear()
run(mc.call_node_json([URL], "s", "u", think=True))
assert [c["think"] for c in calls] == [True], calls
print("2 ok: working think reply -> 1 call, think stays True")

# 3. think off + empty: unchanged
stub("", "")
calls.clear()
try:
    run(mc.call_node_json([URL], "s", "u", think=False, retries=2))
    raise SystemExit("expected ValueError")
except ValueError:
    pass
assert [c["think"] for c in calls] == [False, False, False], calls
print("3 ok: think=False empty -> 3 plain calls then ValueError (unchanged)")

# 4. both empty with think on: bounded
calls.clear()
try:
    run(mc.call_node_json([URL], "s", "u", think=True, retries=2))
    raise SystemExit("expected ValueError")
except ValueError:
    pass
assert [c["think"] for c in calls] == [True, False, False], calls
print("4 ok: both empty -> 1 think call then plain retries, bounded:", [c["think"] for c in calls])

# 5. real ExecutiveNode through NodeBase.run with the license on
from core.schema import CognitiveState                  # noqa: E402
from nodes.executive_node import ExecutiveNode          # noqa: E402
stub("", GOOD)
calls.clear()
st = CognitiveState("Du", "I am Du.")
st.new_cycle("Everybody judges everybody all the time!", "human", "")
st.think_license = True
node = ExecutiveNode()
ok = run(node.run(st))
assert ok is True and st.executive is not None and st.executive.should_respond, (ok, st.executive)
assert [c["think"] for c in calls] == [True, False], calls
print("5 ok: licensed Executive with an empty think reply now SUCCEEDS (reply path intact)")

# 6. telemetry think flag
telemetry.log_llm_latency("m", URL, "x:1", 1.0, True, grammar=1, think=True)
telemetry.log_llm_latency("m", URL, "x:2", 1.0, True, grammar=1)
rows = [json.loads(l) for l in telemetry._LAT.read_text(encoding="utf-8").splitlines()]
assert rows[0].get("t") == 1 and "t" not in rows[1], rows
print("6 ok: llm_latency row carries t=1 only on a think call")

# 7. orchestrator source
src = (TREE / "core" / "orchestrator.py").read_text(encoding="utf-8")
assert "_exec_ok = await self.nodes[\"executive\"].run(self.state)" in src
assert "executive FAILED (node error, not a chosen silence)" in src
m = re.search(r"if input_type == \"human\":\s+logger\.warning\(\"\[CYCLE %s\] executive re-run once", src)
assert m, "re-run must sit under the human-turn guard"
assert src.count("executive re-run once") == 1
assert "executive FAILED -> no reply" in src and "executive → silence" in src
assert "critic FAILED -- no verdict" in src
print("7 ok: orchestrator separates FAILED from chosen silence; one human-turn re-run")
print("ALL OK")
