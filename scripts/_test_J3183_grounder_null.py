"""Hermetic test for J-3183 / D-0570: the thought grounder may answer {"grounding": null} and the thought then
passes through untouched. Touches nothing under data/: the model call, the leak-gate log, the null log, the
deliberation log, emissary context and the tension counter are all stubbed or pointed at a temp dir."""
import asyncio
import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import core  # noqa: E402  -- must resolve to THIS checkout, never the live tree

assert Path(core.__file__).resolve().is_relative_to(HERE), core.__file__

from core import left_lane as ll  # noqa: E402
from core import deliberation as dl  # noqa: E402

tmp = Path(tempfile.mkdtemp(prefix="j3183_"))
ll._LEAK_GATE_LOG = tmp / "ground_leak_gate.jsonl"
ll._GROUND_SKIP_LOG = tmp / "ground_skip_log.jsonl"   # J-2873: failed groundings now log a skip row
ll.GROUND_OUTCOME_LOG = tmp / "ground_outcome.jsonl"        # J-2890: the outcome row stays in the temp dir
import core.ground_grade as _gg  # noqa: E402
_gg.GROUND_GRADE_SHADOW = False                          # J-2890: no shadow grade (it would call a real hub)
dl._DATA_DIR = tmp
dl._LOG_FILE = tmp / "deliberation_log.jsonl"
dl._NULL_LOG_FILE = tmp / "deliberation_null_log.jsonl"
ll._emissary.master_context = lambda **_k: ""
import core.emissary_tension as _et  # noqa: E402
_et.note_recurrence = lambda *a, **k: None
import core.source_sight as _ss  # noqa: E402
_ss.is_self_mechanism = lambda t: False
import core.memory.store as _store  # noqa: E402
_store.store_light_event = lambda *a, **k: "stub"          # deliberate() records a light event on success

fails = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


# 1. prompt text -------------------------------------------------------------------------------------------
OLD_SHA = "88ace9ba15d809de0ea5df6027f387cda80070eeabb71a0092cd2ad48e946fea"   # pre-D-0570 _GROUND_TASK (HEAD~ of this job)
check("kill-switch text is byte-identical to the pre-D-0570 _GROUND_TASK",
      hashlib.sha256(ll._GROUND_TASK_NO_NULL.encode()).hexdigest() == OLD_SHA)
check("live text carries the null clause", '{"grounding": null}' in ll._GROUND_TASK)
check("live text = old text up to the schema line (only the schema tail changed)",
      ll._GROUND_TASK.startswith(ll._GROUND_TASK_NO_NULL[:-len(ll._GROUND_SCHEMA)]))
check("old text has no null clause", "null" not in ll._GROUND_TASK_NO_NULL)
tail = ll._GROUND_SCHEMA_NULLABLE[len(ll._GROUND_SCHEMA):]
cond = tail.split('{"grounding": null}', 1)[1]
check("null clause states only the condition (no example, quote, list or conclusion)",
      cond == " when the thought has no physical referent whose mechanism could be named."
      and '"' not in cond and "," not in cond)
ll.GROUND_ALLOW_NULL = True
check("_ground_system uses live text when flag on", ll._ground_system().endswith(ll._GROUND_TASK))
ll.GROUND_ALLOW_NULL = False
check("_ground_system uses old text when flag off", ll._ground_system().endswith(ll._GROUND_TASK_NO_NULL))
ll.GROUND_ALLOW_NULL = True

# 2. reply parsing ----------------------------------------------------------------------------------------
check("null -> None", ll._read_grounding({"grounding": None}) is None)
check("'null' string -> None", ll._read_grounding({"grounding": " Null "}) is None)
check("text -> text", ll._read_grounding({"grounding": " a real mechanism "}) == "a real mechanism")
check("missing key -> '' (unavailable, not a null answer)", ll._read_grounding({"other": 1}) == "")
check("empty string -> ''", ll._read_grounding({"grounding": ""}) == "")
check("empty reply -> ''", ll._read_grounding(None) == "" and ll._read_grounding({}) == "")
ll.GROUND_ALLOW_NULL = False
check("flag off: null -> '' (old behaviour)", ll._read_grounding({"grounding": None}) == "")
ll.GROUND_ALLOW_NULL = True


# 3. ground_thought_verdict -------------------------------------------------------------------------------
def with_replies(replies):
    it = iter(replies)

    async def fake(payload):
        r = next(it)
        if isinstance(r, Exception):
            raise r
        return r
    ll._ask_ground = fake


def run(c):
    return asyncio.run(c)


with_replies([None])
check("verdict: null -> (None, True)", run(ll.ground_thought_verdict("x " * 30)) == (None, True))
with_replies([None])
check("wrapper ground_thought: null -> None", run(ll.ground_thought("x " * 30)) is None)
with_replies([""])
check("verdict: empty -> (None, False)", run(ll.ground_thought_verdict("x " * 30)) == (None, False))
with_replies(["Wood is cellulose."])
check("verdict: text -> (text, False)", run(ll.ground_thought_verdict("x " * 30)) == ("Wood is cellulose.", False))
with_replies(["The Master holds it.", None])
check("verdict: leak then null -> (None, True)", run(ll.ground_thought_verdict("x " * 30)) == (None, True))
with_replies(["The Master holds it.", "The Master again."])
check("verdict: leak twice -> (None, False)", run(ll.ground_thought_verdict("x " * 30)) == (None, False))
with_replies([OSError("down")])
check("verdict: transport error -> (None, False)", run(ll.ground_thought_verdict("x " * 30)) == (None, False))

# 4. deliberate(): null passes through, no hot-lane retry, control arm logged -----------------------------
THOUGHT = "I notice the kettle ticking as it cools and I am still."
hot_called = []
integ_called = []


async def hot_boom(thought, hot_urls):
    hot_called.append(1)
    return "an invented grounding"


async def fake_json(urls, system, user, **k):
    integ_called.append(1)
    return {"thought": "The kettle ticks as it cools, and I stay with the sound of it going quiet."}


dl._hot_ground_why = hot_boom
dl.call_node_json = fake_json

with_replies([None])
out, prov = run(dl.deliberate(THOUGHT, "the kitchen", name="X", hot_urls=["u"]))
check("deliberate: null -> thought unchanged, provenance None", out == THOUGHT and prov is None)
check("deliberate: hot lane NOT asked after a null", not hot_called)
check("deliberate: integrate pass NOT run after a null", not integ_called)
rows = [json.loads(l) for l in dl._NULL_LOG_FILE.read_text(encoding="utf-8").splitlines()]
check("deliberate: one control-arm row, raw+about+arm", len(rows) == 1 and rows[0]["raw"] == THOUGHT
      and rows[0]["about"] == "the kitchen" and rows[0]["arm"] == "grounder_null")
check("deliberate: deliberation_log.jsonl untouched by a null", not dl._LOG_FILE.exists())

with_replies([None])
run(dl.deliberate(THOUGHT, "", name="X", hot_urls=["u"], log=False))
check("deliberate(log=False): no second null row",
      len(dl._NULL_LOG_FILE.read_text(encoding="utf-8").splitlines()) == 1)

# 5. unchanged paths --------------------------------------------------------------------------------------
with_replies(["Water cools by conduction and convection into the room air."])
out, prov = run(dl.deliberate(THOUGHT, "", name="X", hot_urls=["u"]))
check("deliberate: real grounding still integrates and logs",
      prov is not None and prov["source"] == "emissary" and out != THOUGHT and dl._LOG_FILE.exists()
      and integ_called == [1] and not hot_called)

with_replies([""])
out, prov = run(dl.deliberate(THOUGHT, "", name="X", hot_urls=["u"]))
# D-0569 / J-3182 superseded the old behaviour here: unavailable now fails open (raw thought), no hot lane.
check("deliberate: unavailable (empty) fails open, hot lane NOT asked (D-0569)", hot_called == [] and prov is None
      and out == THOUGHT)

# 6. no live data touched ---------------------------------------------------------------------------------
check("test logs live under the temp dir", all(Path(p).resolve().is_relative_to(tmp)
                                               for p in (dl._LOG_FILE, dl._NULL_LOG_FILE, ll._LEAK_GATE_LOG)))

print("FAILED: %s" % fails if fails else "ALL PASS")
sys.exit(1 if fails else 0)
