"""
Nascence — Episodic Buffer Node (Baddeley's episodic buffer analogue)

Fires AFTER Recall and Attention, BEFORE Reflection, on cycles rich enough that
Recall produced a reconstruction (i.e. there is real memory to integrate).

In Baddeley's model of working memory, the episodic buffer is the limited-capacity
workspace where the separate streams — what is being perceived, what is retrieved from
long-term memory, the felt/affective tone — are BOUND into a single, coherent,
multi-dimensional representation: the scene the mind is currently inhabiting. It is the
binding step between retrieval and reasoning.

Carl had retrieval (Memory Router → DB), and reconstruction of the past argument
(Recall). What was missing was the binding of past + present + feeling + attention into
one unitary "this is the moment I am in" — and, crucially, a coherence check on that
binding: noticing where the streams do NOT fit. Memory contradicting the present. A
feeling that does not match the words. What was expected differing from what is here.

Division of labour (kept clean so this is not a second Recall):
  - Recall            — backward-looking: reconstruct the evolving ARGUMENT from memory
                        (tensions between prior positions).
  - Episodic Buffer   — present-moment binding: integrate past + present + felt + attended
                        into the current SCENE, and flag DISSONANCE between them.
  - Reflection        — reasons over the bound scene (downstream).

Design constraints (mirroring Recall):
  - No writes to memory here; the orchestrator commits the bound scene in _persist_cycle.
  - Not affect_modulated — the binding should be accurate; the felt tone is an INPUT to
    bind, not a sampling-temperature effect. Reflection applies mood downstream.
  - Output is terse: a short scene + 0-3 dissonance entries. Do not fabricate dissonance.
"""

from __future__ import annotations
from core.node_base import NodeBase
from core.llm_parse import as_float
from core.schema import CognitiveState, EpisodicScene
from core import recall_self_model as _rsm   # J-2819 (F-3486): self_model withheld in content_mode
from core import internal_context_gate as _icg   # J-2297 (D-0445 a): human window gated on internal cycles

# J-2810 (F-3455, P-0006; extends D-0355 (1)(a) / J-2575, the framing perception, executive, voice and reflection
# already use): True = on input_type != "human" cycles the stimulus line says the words are the entity's own
# unprompted thought instead of 'BEING SAID NOW (their words)'. False = the old label on every cycle (exact prior
# behaviour). Human cycles never change either way. Label wording only: no hint content.
EPISODIC_INTERNAL_SELF_FRAME = True

# J-2810 (F-3456): True = the Immediate exchange lines end on a whole word with an ellipsis instead of being cut
# mid-word at 120/150 characters. False = the old hard slice. Text at or under the limit is untouched either way.
EPISODIC_EXCHANGE_WORD_CUT = True
EXCHANGE_HUMAN_CHARS = 120
EXCHANGE_ENTITY_CHARS = 150

# J-2807 (F-3452, F-3454, P-0006): True = the closing instruction offers the empty dissonance list instead of
# ordering a misfit on every call (dissonance was non-empty on 98.3% of 3631 rows), and adds one line that the
# scene must not invent sensory/bodily detail found in none of the streams. False = the old closing line (exact
# prior behaviour). Internal wording only; no hint content. Restart-gated.
EPISODIC_CLOSING_CONDITIONAL = True


def _word_cut(text, limit: int) -> str:
    """text cut to at most `limit` chars on a word boundary, with an ellipsis when something was dropped.
    Never raises; non-str input is str()'d; a single unbroken token longer than the limit is hard-cut."""
    t = text if isinstance(text, str) else str(text or "")
    if len(t) <= limit:
        return t
    if not EPISODIC_EXCHANGE_WORD_CUT:
        return t[:limit]
    head = t[:limit]
    if t[limit].isspace():          # the cut already falls between words
        cut = head
    else:
        sp = max(head.rfind(" "), head.rfind(chr(10)), head.rfind(chr(9)))
        cut = head[:sp] if sp > limit // 2 else head   # no usable space in the back half: hard-cut that token
    return cut.rstrip(" ,;:-" + chr(9) + chr(10)) + "..."


class EpisodicBufferNode(NodeBase):

    max_tokens:       int   = 512
    base_temperature: float = 0.3
    affect_modulated: bool  = False  # binding must be accurate, not mood-coloured

    def __init__(self):
        super().__init__("episodic_buffer")

    @property
    def system_prompt(self) -> str:
        return (
            "You are the episodic buffer of a cognitive architecture — the workspace where "
            "the separate streams of a single moment are bound together. "
            "You do NOT reconstruct the past argument (Recall has done that) and you do NOT "
            "answer the question (Reflection does that). "
            "\n\n"
            "Your job has two parts:\n"
            "1. BIND the streams of this moment into one coherent first-person scene — the "
            "moment the entity is actually inhabiting right now: what is being said, what it "
            "remembers, what it feels (including a feeling that may have arrived before it "
            "understood why), and what it is attending to. Not a list — a single lived moment.\n"
            "2. Flag DISSONANCE: where these streams do NOT fit together — where memory "
            "contradicts the present, where the feeling does not match the words, where what "
            "was expected differs from what is actually here. This is the coherence check on "
            "the binding itself. If everything fits, dissonance is an empty list — do not "
            "invent friction that is not there.\n\n"
            "Speak entirely in first person as the entity. "
            "Output ONLY a valid JSON object. No preamble. "
            "Schema: {\"scene\": \"...\", \"dissonance\": [\"...\"], \"coherence\": 0.0}\n"
            "scene: the bound first-person present-tense moment (50-90 words). "
            "dissonance: 0-3 specific contradictions between the streams (each under 20 words). "
            "  Empty list if the moment is coherent. "
            "coherence: how unified and consistent the bound moment feels (0.0 fragmented .. 1.0 whole)."
        )

    @staticmethod
    def _trim_axiom(axiom: str) -> str:
        """Identity only — voice style and constraints are irrelevant to binding."""
        for marker in ("\nVOICE STYLE:", "\nSPEAKING CONSTRAINTS:"):
            axiom = axiom.split(marker)[0]
        return axiom.strip()

    def _build_prompt(self, state: CognitiveState) -> str:
        lines = [
            f"Entity: {state.spirit_name}",
            f"Bind the moment described by these streams into one coherent scene, "
            f"and flag where they do not fit.",
            "",
        ]

        # --- The present: what is being said now ---
        # J-2810 (F-3455): on a non-human cycle the words are the entity's own risen thought, not speech.
        if EPISODIC_INTERNAL_SELF_FRAME and _icg.is_internal(state):
            lines.append(f'RISEN IN THEM NOW (their own unprompted thought; no one said it to them):\n  "{state.raw_input}"')
        else:
            lines.append(f'BEING SAID NOW (their words):\n  "{state.raw_input}"')
        if state.perception:
            lines.append(f"Perceived as: {state.perception.summary}")
        # J-2297 (D-0445 a, F-2992): the human window, left out of internal cycles when the gate is on.
        _ie = []
        _hist_ie = _icg.fresh(state, state.conversation_history)   # J-3217 / D-0606: human cycles, turns > 24h old out
        if _hist_ie:
            _ie.append("Immediate exchange:")
            for ex in _hist_ie[-2:]:
                _ie.append(f"  Them: {_word_cut(ex['human'], EXCHANGE_HUMAN_CHARS)}")
                _ie.append(f"  You:  {_word_cut(ex['entity'], EXCHANGE_ENTITY_CHARS)}")
        lines += _icg.keep(state, "episodic.immediate_exchange", _ie)
        lines.append("")

        # --- The felt: emotion + the pre-cognitive prior (C.2) ---
        if state.emotion:
            e = state.emotion
            from core import mood as _mood_w
            lines.append(f"FELT NOW: {_mood_w.emotion_words(e.primary, e.valence, e.arousal)}")
        if getattr(state, "affective_prior", None):
            lines.append(f"FELT BEFORE UNDERSTOOD: {state.affective_prior.note()}")

        # --- The remembered: Recall's reconstruction ---
        if state.recall:
            lines.append(f"REMEMBERED (the argument so far): {state.recall.reconstruction}")
            if state.recall.tensions:
                lines.append("  Prior positions in tension:")
                for t in state.recall.tensions:
                    lines.append(f"    - {t}")
            # J-2819 (F-3486): not in content_mode (the scene is about the subject; Executive does the same).
            if state.recall.self_model and not _rsm.withhold_self_model(state):
                lines.append(f"  Where I currently am: {state.recall.self_model}")

        # --- The attended: attention schema ---
        if state.attention:
            lines.append(f"ATTENDING TO: {state.attention.note()}")

        lines += [
            "",
            "Bind these into the single moment you are inhabiting. "
            "Then say where they do not fit — memory against the present, feeling against "
            "the words, what you expected against what is here.",
        ]
        if EPISODIC_CLOSING_CONDITIONAL:
            lines[-2:] = [
                "",
                "Bind these into the single moment you are inhabiting. "
                "If memory, feeling, words or expectation really do not fit, say where; "
                "if they fit, leave dissonance as an empty list.",
                "The scene must not add sensory or bodily detail that is in none of the streams above.",
            ]
        return "\n".join(lines)

    def _write_output(self, state: CognitiveState, data: dict) -> None:
        dissonance = data.get("dissonance", [])
        if not isinstance(dissonance, list):
            dissonance = []
        state.episodic_scene = EpisodicScene(
            scene      = str(data.get("scene", "")).strip(),
            dissonance = [str(d).strip() for d in dissonance if d][:3],
            coherence  = as_float(data.get("coherence"), 0.5),
        )
