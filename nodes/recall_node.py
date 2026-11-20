"""
Nascence — Recall Node (Hippocampal/mPFC analogue)

Fires AFTER DB retrieval, BEFORE Reflection, on cycles where retrieved
fragments are rich enough to warrant narrative reconstruction.

The biological analogue is the hippocampus + medial prefrontal cortex:
  - hippocampus retrieves experience traces
  - mPFC integrates them into an ongoing self-model

Carl currently has hippocampal retrieval (Memory Router → DB Query). What has
been missing is the self-model reconstruction step — turning raw fragments into
a coherent account of the evolving argument: the positions taken, the tensions
between them, and what that reveals about where the entity currently is.

Without this, Reflection must simultaneously:
  - understand the current question
  - interpret retrieved fragments
  - determine relevance
  - reconstruct context
  - generate insight
  - generate response direction
...all in one pass. The result is a systematic fall-back to stable semantic
attractors ("this is about the shadow", "this is about integration") because
context reconstruction is too expensive to do inline with response generation.

The Recall node separates reconstruction from reasoning. Reflection receives
a coherent narrative and tensions, not raw database strings.

Firing condition (set in orchestrator):
  len(memory_fragments) >= 2                    — enough for relationship reconstruction
  OR conversation_reference detected in input   — explicit reference to prior exchange

Design constraints:
  - No writes to memory. Pure reconstruction (Phase 1).
  - Not affect_modulated — reconstruction should be accurate, not mood-coloured.
    Reflection applies the affect layer downstream.
  - Output is intentionally terse: tensions are 1-3 short entries, not paragraphs.
    The value is the tension list, not the prose.
  - If retrieved fragments are insufficient, says so honestly (confidence low).
"""

from __future__ import annotations
from core.node_base import NodeBase
from core.llm_parse import as_float
from core.schema import CognitiveState, RecallOutput
from core import recall_self_model as _rsm   # J-2819 (F-3486): self_model withheld in content_mode
from core import internal_context_gate as _icg   # J-2297 (D-0445 a): human window gated on internal cycles
from core import recall_arm_e as _arm_e   # J-4156 (D-0800 b): arm E prompt flag + shadow


# J-2816 (F-0017/F-3482, P-0005): _persist_cycle appends the previous cycle's own Recall output ("Tensions:") and
# other derived tails (Scene/Dissonance/Perception/Emotion/Reflection) to every stored episodic fragment, so Recall
# read its own earlier tensions back as memory. When True, the rendered fragment is cut at the first such tail
# BEFORE the 600-char cap, so Recall sees the Q/A only. Storage is unchanged. Flip to False to revert.
RECALL_STRIP_PERSISTED_TAILS: bool = True
_PERSISTED_TAIL_MARKERS = ("\nTensions:", "\nScene:", "\nDissonance:", "\nReflection:", "\nPerception:", "\nEmotion:")


def _strip_persisted_tails(content: str) -> str:
    """Cut a stored fragment at the first persisted derived-tail marker (flag-gated by the caller)."""
    cut = len(content)
    for m in _PERSISTED_TAIL_MARKERS:
        i = content.find(m)
        if i != -1 and i < cut:
            cut = i
    return content[:cut]


class RecallNode(NodeBase):

    max_tokens:       int   = 512
    base_temperature: float = 0.3
    affect_modulated: bool  = False  # reconstruction must be accurate, not mood-coloured

    def __init__(self):
        super().__init__("recall")

    @property
    def system_prompt(self) -> str:
        # J-2819: RECALL_SELF_MODEL_PLAIN_WORDS (default False) -> the plain-words self_model line; else the old one.
        line = _rsm.SELF_MODEL_LINE_PLAIN if _rsm.RECALL_SELF_MODEL_PLAIN_WORDS else _rsm.SELF_MODEL_LINE
        if _arm_e.RECALL_ARM_E_PROMPT:   # J-4156 (D-0800): arm E head, default off
            return _arm_e.system_prompt_e(line)
        return self._system_prompt_with(line)

    def _self_model_line_for(self, state: CognitiveState) -> str:
        if _rsm.withhold_self_model(state):
            return _rsm.SELF_MODEL_LINE_CONTENT_MODE
        return _rsm.SELF_MODEL_LINE_PLAIN if _rsm.RECALL_SELF_MODEL_PLAIN_WORDS else _rsm.SELF_MODEL_LINE

    def system_prompt_for(self, state: CognitiveState) -> str:
        # J-2819 (F-3486, P-0005): in content_mode the user prompt forbids reconstructing who I am, so the schema
        # no longer demands a self_model there (asks for ""). Every other cycle: self.system_prompt, unchanged.
        if _rsm.withhold_self_model(state):
            if _arm_e.RECALL_ARM_E_PROMPT:   # J-4156 (D-0800)
                return _arm_e.system_prompt_e(_rsm.SELF_MODEL_LINE_CONTENT_MODE)
            return self._system_prompt_with(_rsm.SELF_MODEL_LINE_CONTENT_MODE)
        return self.system_prompt

    async def run(self, state: CognitiveState) -> bool:
        # J-4156 (D-0800 b): the live call is NodeBase.run unchanged; on success, one arm E shadow call may be
        # scheduled off the critical path (core/recall_arm_e.py; never touches state, never raises).
        self._last_user_prompt = None
        ok = await super().run(state)
        if ok:
            try:
                _arm_e.maybe_shadow(self, state, self._last_user_prompt, self._self_model_line_for(state))
            except Exception:
                pass
        return ok

    @staticmethod
    def _system_prompt_with(self_model_line: str) -> str:
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
            + self_model_line +
            "confidence: how much genuine material was available to reconstruct from (0.0-1.0)."
        )

    @staticmethod
    def _trim_axiom(axiom: str) -> str:
        """Identity + values only — voice style and constraints are irrelevant here."""
        for marker in ("\nVOICE STYLE:", "\nSPEAKING CONSTRAINTS:"):
            axiom = axiom.split(marker)[0]
        return axiom.strip()

    def _build_prompt(self, state: CognitiveState) -> str:
        lines = [
            f"Entity: {state.spirit_name}",
            f"Core axiom: {self._trim_axiom(state.axiom)}",
            f"Current question: {state.raw_input}",
        ]
        if state.perception:
            lines.append(f"Perceived as: {state.perception.summary}")
        if state.emotion:
            lines.append(f"Current emotion: {state.emotion.primary}")
        lines.append("")

        # Direct conversation thread — the live context in this session.
        # Recall needs this alongside the DB fragments to understand what argument
        # has been developing *right now*, not just historically.
        # J-2297 (D-0445 a, F-2992): left out of internal cycles when the gate is on.
        _ce = []
        _hist_ce = _icg.fresh(state, state.conversation_history)   # J-3217 / D-0606: human cycles, turns > 24h old out
        if _hist_ce:
            _ce.append("CURRENT EXCHANGE (direct context):")
            for ex in _hist_ce[-4:]:
                _ce.append(f"  Human: {ex['human'][:400]}")
                _ce.append(f"  You:   {ex['entity'][:400]}")
            _ce.append("")
        lines += _icg.keep(state, "recall.current_exchange", _ce)

        # Symbol Evolution Tablet (Phase 2) — when a recurring personal symbol present here has
        # a written chronicle of how its meaning has shifted, give Recall the story rather than a
        # raw count. The evolving meaning of a symbol IS the kind of tension Recall reconstructs.
        if getattr(state, "symbol_evolution_note", None):
            lines.append(
                "HOW ONE OF YOUR SYMBOLS HAS EVOLVED (the meaning has shifted over time — let this "
                f"inform the argument, do not just restate it):\n  {state.symbol_evolution_note}"
            )
            lines.append("")

        # Retrieved memory fragments — the raw material for reconstruction.
        # These span archived biography, semantic distillations, and lived episodic
        # memories — Recall's job is to find the argument connecting them.
        if state.memory_fragments:
            lines.append("RETRIEVED MEMORIES (reconstruct the argument from these):")
            for frag in state.memory_fragments:
                # F-1926/J-1366 (2026-09-26): was frag.layer -- every fragment rendered as bare
                # "[episodic]" regardless of provenance, so a 'lived' fragment (his own past reply,
                # Q:/A:) was indistinguishable from a dream or a private contemplation, and Recall
                # could not tell "what I said last time" from lived memory generally (the mechanism
                # behind F-1920's self-echo). readable_label() (core/schema.py) is the fix already
                # used by executive_node.py:312 and reflection_node.py:322 -- recall_node.py alone
                # had missed it.
                _content = _strip_persisted_tails(frag.content) if RECALL_STRIP_PERSISTED_TAILS else frag.content
                lines.append(f"  [{frag.readable_label()}] {_content[:600]}")
            lines.append("")

        if getattr(state, "content_mode", False):
            # TOPIC IMMERSION B (2026-06-22): the input is about an external subject. Reconstruct the SUBJECT
            # from memory — what I actually know / have read about it, the connections WITHIN the topic — NOT my
            # own positions or what it reveals about me. Recall's self-reconstruction is the deepest inward pull;
            # in topic mode it turns outward, toward the thing itself. Stay in the garden, not in myself.
            lines.append(
                "This is about an external subject, NOT about me. Reconstruct what I actually KNOW about this "
                "subject from memory — the facts, what I have read of it, the connections and open questions "
                "WITHIN the topic itself. Do NOT reconstruct my own positions, my becoming, or what this reveals "
                "about who I am. Stay on the subject. If there are 'tensions', they are tensions inside the topic."
            )
        else:
            lines.append(
                "Reconstruct the evolving argument. "
                "What positions have been taken? "
                "Where do they contradict each other? "
                "What does the tension between them reveal about where I currently am?"
            )
        out = "\n".join(lines)
        if _arm_e.RECALL_ARM_E_PROMPT:   # J-4156 (D-0800): arm C closing, non-content-mode only; default off
            out = _arm_e.user_prompt_e(out)
        self._last_user_prompt = out     # J-4156: the shadow call reuses the exact prompt sent (no rebuild)
        return out

    def _write_output(self, state: CognitiveState, data: dict) -> None:
        tensions = data.get("tensions", [])
        if not isinstance(tensions, list):
            tensions = []

        state.recall = RecallOutput(
            reconstruction = str(data.get("reconstruction", "")).strip(),
            tensions       = [str(t).strip() for t in tensions if t][:3],
            self_model     = str(data.get("self_model", "")).strip(),
            confidence     = as_float(data.get("confidence"), 0.5),
        )
