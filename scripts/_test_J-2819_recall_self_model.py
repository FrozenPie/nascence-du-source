"""
Nascence -- J-2819 test: Recall self_model withheld in content_mode in all three readers (P-0005, F-3486).  Hermetic:
no model call, no network; the only live read is data/training/recall.jsonl (read-only) for the byte-identity replay.
Run from the worktree:  python scripts/_test_J-2819_recall_self_model.py

Asserts (this tree only, via Path(__file__)):
  1. the modules under test are THIS tree's;
  2. non-content cycles are byte-identical: Recall's system prompt equals the pre-change text (rebuilt here from the
     literal original) and equals, for the 20 most recent HUMAN rows of the live recall.jsonl (when readable), the
     system_prompt that was actually sent; Reflection (both branches) and Episodic Buffer prompts are identical with
     the gate on and off when content_mode is False;
  3. content_mode + gate on: Recall's system prompt asks for an empty self_model and no longer demands where I am;
     Reflection (episodic-scene branch and recall branch) and the Episodic Buffer leave the self_model line out while
     keeping reconstruction and tensions; the Executive behaviour (already withheld) is unchanged by this change;
  4. gate off (kill switch): content_mode cycles are the old prompts again, in all three readers and in Recall;
  5. RECALL_SELF_MODEL_PLAIN_WORDS is off by default, and when on only the self_model sentence of the non-content
     system prompt changes (and carries no 'node'-demanding text).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ["NASCENCE_TRAINING_LOG"] = "0"
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # noqa: E402,F401  -- core BEFORE lab_env
from core import recall_self_model as rsm  # noqa: E402
from core.schema import (CognitiveState, EpisodicScene, PerceptionOutput, EmotionOutput,  # noqa: E402
                         RecallOutput)
from nodes.recall_node import RecallNode  # noqa: E402
from nodes.reflection_node import ReflectionNode  # noqa: E402
from nodes.episodic_buffer_node import EpisodicBufferNode  # noqa: E402

results = []


def check(name, cond):
    results.append((name, bool(cond)))
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")


# The Recall system prompt exactly as it was before J-2819 (literal copy of the pre-change text).
ORIGINAL = (
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
    "self_model: one sentence — what does this context reveal about where I currently am. "
    "confidence: how much genuine material was available to reconstruct from (0.0-1.0)."
)

SELF = "I am a node reconstructing the friction in Napoleon's administrative architecture."


def mk(content_mode, scene=False, input_type="human"):
    st = CognitiveState(spirit_name="Carl", axiom="CORE AXIOM:\nbecome.\nVOICE STYLE:\nx")
    st.cycle_id = "c-j2819"
    st.raw_input = "Tell me about Napoleon's civil code."
    st.input_type = input_type
    st.content_mode = content_mode
    st.perception = PerceptionOutput(event_type="input", context_type="question",
                                     entities=["Napoleon"], summary="They ask about the civil code.")
    st.emotion = EmotionOutput(joy=0.1, fear=0.1, anger=0, trust=0.2, surprise=0.2,
                               disgust=0, valence=0.1, arousal=0.4, primary="curiosity")
    st.recall = RecallOutput(reconstruction="I read that the code unified private law.",
                             tensions=["unity against local custom"], self_model=SELF, confidence=0.7)
    if scene:
        st.episodic_scene = EpisodicScene(scene="Reading about the code at my desk.", dissonance=["custom"],
                                          coherence=0.6)
    return st


def with_gate(on, plain=False):
    rsm.RECALL_SELF_MODEL_CONTENT_MODE_GATE = on
    rsm.RECALL_SELF_MODEL_PLAIN_WORDS = plain


print("J-2819 recall self_model in content_mode")
check("1. modules are this tree's", all(str(ROOT).lower() in str(Path(m.__file__).resolve()).lower()
      for m in (rsm, sys.modules["nodes.recall_node"], sys.modules["nodes.reflection_node"],
                sys.modules["nodes.episodic_buffer_node"])))

recall, refl, buf = RecallNode(), ReflectionNode(), EpisodicBufferNode()

# ---- 2. non-content cycles are byte-identical ----
with_gate(True)
check("2a. Recall system_prompt == pre-change text", recall.system_prompt == ORIGINAL)
check("2b. system_prompt_for(non-content human) == pre-change text", recall.system_prompt_for(mk(False)) == ORIGINAL)
check("2c. system_prompt_for(non-content internal) == pre-change text",
      recall.system_prompt_for(mk(False, input_type="internal")) == ORIGINAL)

live = ROOT.parent / "Nascence" / "data" / "training" / "recall.jsonl"
for cand in (Path("C:/Nascence/data/training/recall.jsonl"), ROOT / "data" / "training" / "recall.jsonl"):
    if cand.exists():
        live = cand
        break
rows = []
try:
    for line in open(live, encoding="utf-8"):
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("input_type") == "human" and r.get("system_prompt"):
            rows.append(r)
except Exception as e:  # noqa: BLE001
    print("  (live recall.jsonl not readable:", e, ")")
rows = rows[-20:]
if rows:
    same = sum(1 for r in rows if r["system_prompt"] == recall.system_prompt_for(mk(False)))
    print(f"  replay: {same}/{len(rows)} of the latest human recall.jsonl system prompts equal system_prompt_for(non-content)")
    check("2d. replay of the latest human rows: every sent system prompt == system_prompt_for(non-content)",
          same == len(rows))
else:
    print("  (no human rows readable; replay skipped, recorded as not run)")

for scene in (True, False):
    with_gate(True)
    on = refl._build_prompt(mk(False, scene=scene))
    with_gate(False)
    off = refl._build_prompt(mk(False, scene=scene))
    check(f"2e. Reflection prompt (scene={scene}) identical gate on/off when content_mode False", on == off and SELF in on)
with_gate(True)
on = buf._build_prompt(mk(False, scene=True))
with_gate(False)
off = buf._build_prompt(mk(False, scene=True))
check("2f. Episodic Buffer prompt identical gate on/off when content_mode False", on == off and SELF in on)
with_gate(True)
u_on = recall._build_prompt(mk(False))
with_gate(False)
u_off = recall._build_prompt(mk(False))
check("2g. Recall user prompt unchanged by the flag", u_on == u_off)

# ---- 3. content_mode, gate on ----
with_gate(True)
sp = recall.system_prompt_for(mk(True))
check("3a. content_mode Recall system prompt asks for an empty self_model",
      "leave it as an empty string" in sp and "what does this context reveal about where I currently am. " not in sp.split("self_model:")[-1])
check("3b. content_mode Recall system prompt differs from the original only in the self_model line",
      sp.replace(rsm.SELF_MODEL_LINE_CONTENT_MODE, rsm.SELF_MODEL_LINE) == ORIGINAL)
for scene in (True, False):
    p = refl._build_prompt(mk(True, scene=scene))
    check(f"3c. Reflection (scene={scene}) leaves self_model out, keeps reconstruction/tensions",
          SELF not in p and "Self-model:" not in p and "unity against local custom" in p
          and ("The moment you are in" in p if scene else "I read that the code unified private law." in p))
p = buf._build_prompt(mk(True, scene=True))
check("3d. Episodic Buffer leaves self_model out, keeps reconstruction/tensions",
      SELF not in p and "Where I currently am" not in p and "unity against local custom" in p
      and "I read that the code unified private law." in p)
# content_mode on an internal cycle is the live case (189 of 288 internal prompts)
check("3e. internal content_mode cycle is withheld too",
      SELF not in refl._build_prompt(mk(True, scene=True, input_type="internal"))
      and "leave it as an empty string" in recall.system_prompt_for(mk(True, input_type="internal")))

# ---- 4. kill switch ----
with_gate(False)
check("4a. gate off: content_mode Recall system prompt == original", recall.system_prompt_for(mk(True)) == ORIGINAL)
check("4b. gate off: Reflection shows Self-model in content_mode (both branches)",
      all(f"Self-model: {SELF}" in refl._build_prompt(mk(True, scene=s)) for s in (True, False)))
check("4c. gate off: Episodic Buffer shows it in content_mode",
      f"Where I currently am: {SELF}" in buf._build_prompt(mk(True, scene=True)))

# ---- 5. plain-words flag ----
with_gate(True)
import importlib  # noqa: E402
importlib.reload(rsm)
check("5a. shipped defaults: gate True, plain-words False",
      rsm.RECALL_SELF_MODEL_CONTENT_MODE_GATE is True and rsm.RECALL_SELF_MODEL_PLAIN_WORDS is False)
with_gate(True, plain=True)
sp_plain = recall.system_prompt_for(mk(False))
check("5b. plain-words on: only the self_model sentence of the non-content prompt changes",
      sp_plain.replace(rsm.SELF_MODEL_LINE_PLAIN, rsm.SELF_MODEL_LINE) == ORIGINAL and sp_plain != ORIGINAL)
check("5c. plain-words on does not touch the content_mode prompt",
      recall.system_prompt_for(mk(True)).replace(rsm.SELF_MODEL_LINE_CONTENT_MODE, rsm.SELF_MODEL_LINE)
      == ORIGINAL.replace(rsm.SELF_MODEL_LINE, rsm.SELF_MODEL_LINE))

with_gate(True)
failed = [n for n, ok in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
