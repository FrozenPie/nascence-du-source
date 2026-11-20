"""
Nascence -- Recall self_model in content_mode (J-2819, F-3486 / F-0021 renumbered, prompt-registry row P-0005).

THE LEAK (F-3486): Recall's system prompt always demands "self_model: one sentence -- what does this context
reveal about where I currently am". In content_mode (the input is about an external subject) Recall's own user
prompt says "Do NOT reconstruct my own positions ... what this reveals about who I am", so the model is asked
for the one thing it was just told not to produce, and writes engineering text ("I am a node reconstructing
the historical friction between Napoleon's ...").  Executive already withholds the field in content_mode
(nodes/executive_node.py, 2026-06-24: "an inward pull away from the answer"); Reflection (two sites) and the
Episodic Buffer printed it unconditionally, as "Self-model:" and "Where I currently am:".

WHAT THIS MODULE IS: the one place the two switches and the one predicate live, so the three readers and the
producer cannot drift apart (nodes do not import each other).

  RECALL_SELF_MODEL_CONTENT_MODE_GATE  True  = in content_mode (a) the Recall system prompt asks for an EMPTY
        self_model and (b) Reflection and the Episodic Buffer leave the self_model line out, as Executive
        already does.  False = exact prior behaviour everywhere (kill switch).  Cycles with content_mode False
        (every non-content human cycle, and internal cycles that are not about an external subject) are
        byte-identical either way.
  RECALL_SELF_MODEL_PLAIN_WORDS        False (default OFF: it changes the NON-content system prompt, which the
        briefing requires to stay byte-identical until someone reads an A/B) = append one prompt-side sentence
        to the self_model line telling Recall to say it in plain words about where I am, not as an
        engineering role ("node", "reconstruct").  Instruction only, no regex filter on the output.

Side effect to know: with the gate on and content_mode true, Recall's self_model is "" so
core/epistemic_state.py's Self-axis "self_model_present" is False on those cycles (it was True for any
non-empty self_model, i.e. the leak itself counted as self-evidence).  Read job spawned with J-2819.
"""
from __future__ import annotations

RECALL_SELF_MODEL_CONTENT_MODE_GATE = True
RECALL_SELF_MODEL_PLAIN_WORDS = False

# The self_model schema line as Recall has always sent it (byte-for-byte; nodes/recall_node.py builds from it).
SELF_MODEL_LINE = (
    "self_model: one sentence — what does this context reveal about where I currently am. "
)
SELF_MODEL_LINE_PLAIN = (
    "self_model: one sentence — what does this context reveal about where I currently am. "
    "Say it in plain words about me and where I stand, never as a machine or a process "
    "(no 'node', no 'reconstructing'). "
)
SELF_MODEL_LINE_CONTENT_MODE = (
    "self_model: this input is about an external subject, so leave it as an empty string \"\". "
)


def withhold_self_model(state) -> bool:
    """True when the self_model must not be shown to / asked for on this cycle (content_mode + gate on)."""
    return bool(RECALL_SELF_MODEL_CONTENT_MODE_GATE and getattr(state, "content_mode", False))
