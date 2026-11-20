"""
Nascence -- J-4156 test: Recall arm E prompt flag + shadow (D-0800 b, P-0005). Hermetic: no model call, no network,
no read or write of data/ (the shadow log path is pointed at a temp dir; call_node_json is replaced by a stub).
Run from the tree under test:  python scripts/_test_J-4156_recall_arm_e.py

Asserts:
  1. modules under test are THIS tree's;
  2. flag off: Recall system prompt (normal + content_mode) and user prompt are byte-identical to the pre-change
     text (system rebuilt from the literal J-2819 builder; user prompt ends with the old closing);
  3. flag on: system prompt = arm E head + unchanged self_model line + confidence line; user prompt carries the
     arm C closing (non-content mode) and the content_mode closing is unchanged;
  4. shadow: after a successful run with the stub, exactly one row is written with the documented shape; state.recall
     keeps the LIVE result; a stub that raises still writes a row with err and never raises; flag-on disables shadow;
     in-flight cap holds; a non-live process (guard refusal) schedules nothing.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path

os.environ["NASCENCE_TRAINING_LOG"] = "0"
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # noqa: E402  -- core BEFORE anything lab-ish
assert Path(core.__file__).resolve().parent == ROOT / "core", core.__file__
from core import recall_arm_e as ae, recall_self_model as rsm, profile  # noqa: E402
from core import node_base  # noqa: E402
from core.schema import CognitiveState, MemoryFragment  # noqa: E402
import nodes.recall_node as rn  # noqa: E402
from nodes.recall_node import RecallNode  # noqa: E402

results = []


def check(name, cond, detail=""):
    results.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + (f"  [{detail}]" if detail and not cond else ""))


check("tree: recall_node", Path(rn.__file__).resolve().parent == ROOT / "nodes")
check("tree: recall_arm_e", Path(ae.__file__).resolve().parent == ROOT / "core")
check("defaults: prompt flag off", ae.RECALL_ARM_E_PROMPT is False)


def OLD_SYSTEM(line):
    return (
        "You are the memory reconstruction node of a cognitive architecture. "
        "Your job is NOT to answer the current question — Reflection does that. "
        "Your job is to reconstruct the EVOLVING ARGUMENT from retrieved memory: "
        "what positions has this entity taken, where do they contradict each other, "
        "and what does that reveal about where the entity currently is. "
        "\n\n"
        "Focus on RELATIONSHIPS between memories, not individual facts. "
        "The most valuable output is 'tensions' — specific contradictions or unresolved "
        "friction between positions already taken. "
        "This is what Reflection needs most: not a summary of what was said, "
        "but the live tensions between prior stances. "
        "\n\n"
        "Speak entirely in first person as the entity. "
        "If retrieved fragments are insufficient to reconstruct from, say so honestly "
        "and set confidence low. Do not fabricate tensions that aren't evidenced. "
        "Output ONLY a valid JSON object. No preamble. "
        "Schema: "
        "{\"reconstruction\": \"...\", \"tensions\": [\"...\"], "
        "\"self_model\": \"...\", \"confidence\": 0.0}\n"
        "reconstruction: first-person narrative of the remembered argument (50-80 words). "
        "tensions: 1-3 specific contradictions between prior positions (each under 20 words). "
        "  Empty list if no genuine tensions are evidenced. "
        + line +
        "confidence: how much genuine material was available to reconstruct from (0.0-1.0)."
    )


def mk_state(content_mode=False):
    s = CognitiveState(raw_input="what did I say about rivers?", spirit_name="Du",
                       axiom="I am Du.\nVOICE STYLE: x")
    s.cycle_id = "c-test"
    s.input_type = "internal"
    s.content_mode = content_mode
    try:
        s.memory_fragments = [MemoryFragment(fragment_id="f1", content="Q: a\nA: rivers carry\nTensions: old",
                                             layer="episodic", relevance=0.9, timestamp=1.0),
                              MemoryFragment(fragment_id="f2", content="Q: b\nA: rivers stay",
                                             layer="episodic", relevance=0.8, timestamp=2.0)]
    except Exception as exc:  # schema drift: run without fragments
        print("note: no fragments", exc)
    return s


node = RecallNode()
s_norm, s_cm = mk_state(False), mk_state(True)

# 2. flag off
ae.RECALL_ARM_E_PROMPT = False
check("off: system normal byte-identical", node.system_prompt_for(s_norm) == OLD_SYSTEM(rsm.SELF_MODEL_LINE))
exp_cm = OLD_SYSTEM(rsm.SELF_MODEL_LINE_CONTENT_MODE) if rsm.withhold_self_model(s_cm) else OLD_SYSTEM(rsm.SELF_MODEL_LINE)
check("off: system content_mode byte-identical", node.system_prompt_for(s_cm) == exp_cm)
u_off = node._build_prompt(s_norm)
check("off: user prompt ends with old closing", u_off.endswith(ae.CLOSE_A))
check("off: CLOSE_A matches recall_node literal", ae.CLOSE_A in u_off)
u_cm_off = node._build_prompt(s_cm)

# 3. flag on
ae.RECALL_ARM_E_PROMPT = True
sp_on = node.system_prompt_for(s_norm)
check("on: system starts with arm E head", sp_on.startswith(ae.SYS_E_HEAD))
check("on: system keeps self_model + confidence tail",
      sp_on == ae.SYS_E_HEAD + rsm.SELF_MODEL_LINE + ae.CONFIDENCE_LINE)
check("on: system tail equals old tail from 'self_model:'",
      sp_on[sp_on.find("self_model:"):] == OLD_SYSTEM(rsm.SELF_MODEL_LINE)[OLD_SYSTEM(rsm.SELF_MODEL_LINE).find("self_model:"):])
u_on = node._build_prompt(s_norm)
check("on: user prompt arm C closing", u_on.endswith(ae.CLOSE_C) and ae.CLOSE_A not in u_on)
check("on: user prompt otherwise identical", u_on[:-len(ae.CLOSE_C)] == u_off[:-len(ae.CLOSE_A)])
check("on: content_mode user prompt unchanged", node._build_prompt(s_cm) == u_cm_off)
check("on: content_mode system uses arm E head", node.system_prompt_for(s_cm).startswith(ae.SYS_E_HEAD))
ae.RECALL_ARM_E_PROMPT = False

# 4. shadow
tmp = Path(tempfile.mkdtemp(prefix="j4156_"))
ae._LOG = tmp / "recall_arm_e_shadow.jsonl"
_real_guard = profile.guard_path
profile.guard_path = lambda p: p   # temp path, treat as allowed
calls = []
mode = {"raise": False}


async def stub(base_urls, system, user, **kw):
    calls.append((system, user, kw))
    if system.startswith(ae.SYS_E_HEAD):
        if mode["raise"]:
            raise RuntimeError("boom")
        await asyncio.sleep(0.01)
        return {"reconstruction": "e", "tensions": [], "self_model": "", "confidence": 0.9}
    return {"reconstruction": "live", "tensions": ["A vs B"], "self_model": "", "confidence": 0.95}


node_base.call_node_json = stub
import core.model_client as mc  # noqa: E402
mc.call_node_json = stub
node._log_teacher_example = lambda *a, **k: None


async def run_once(state):
    ok = await node.run(state)
    await asyncio.sleep(0)
    pend = list(ae._INFLIGHT)
    if pend:
        await asyncio.gather(*pend, return_exceptions=True)
    return ok


def rows():
    try:
        return [json.loads(l) for l in open(ae._LOG, encoding="utf-8")]
    except FileNotFoundError:
        return []


s = mk_state(False)
ok = asyncio.run(run_once(s))
r = rows()
check("shadow: live run ok", ok)
check("shadow: state keeps live result", s.recall and s.recall.tensions == ["A vs B"] and s.recall.reconstruction == "live")
check("shadow: one row", len(r) == 1, len(r))
keys = {"ts", "cycle_id", "input_type", "content_mode", "old_tensions", "e_tensions", "old_empty", "e_empty",
        "old_confidence", "e_confidence", "e_reconstruction", "err", "sec"}
check("shadow: row shape", r and set(r[0]) == keys, r and sorted(r[0]))
check("shadow: row values", r and r[0]["old_tensions"] == ["A vs B"] and r[0]["e_empty"] is True
      and r[0]["old_empty"] is False and r[0]["err"] is None and r[0]["cycle_id"] == "c-test")
e_call = [c for c in calls if c[0].startswith(ae.SYS_E_HEAD)]
check("shadow: E call got arm C closing", e_call and e_call[0][1].endswith(ae.CLOSE_C))

mode["raise"] = True
ok2 = asyncio.run(run_once(mk_state(False)))
r = rows()
check("shadow: raising E call -> live ok, err row", ok2 and len(r) == 2 and r[1]["err"] and r[1]["e_tensions"] is None)
mode["raise"] = False

ae.RECALL_ARM_E_PROMPT = True
n0 = len(calls)
asyncio.run(run_once(mk_state(False)))
check("shadow: off when arm E is live", len(rows()) == 2 and len(calls) == n0 + 1)
ae.RECALL_ARM_E_PROMPT = False

ae._INFLIGHT.add(object())
check("shadow: in-flight cap", ae.maybe_shadow(node, mk_state(False), "x", rsm.SELF_MODEL_LINE) is False)
ae._INFLIGHT.clear()


def _refuse(p):
    raise profile.NonLiveWriteError(str(p))


profile.guard_path = _refuse
check("shadow: non-live process schedules nothing",
      ae.maybe_shadow(node, mk_state(False), "x", rsm.SELF_MODEL_LINE) is False)
check("shadow: never raises on garbage", ae.maybe_shadow(None, None, "x", "") is False)
profile.guard_path = _real_guard

st = ae.stats(ae._LOG)
check("stats: reader", st["rows"] == 2 and st["errors"] == 1 and st["e_empty_rate"] == 1.0, st)

failed = [n for n, c in results if not c]
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
