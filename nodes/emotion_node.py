from __future__ import annotations
from core.node_base import NodeBase
from core.llm_parse import as_float
from core.schema import CognitiveState, EmotionOutput
from core import internal_context_gate as _icg

# J-2814 (F-0015): on internal cycles the fallback line no longer claims a person spoke, and the mislabelled
# "Event type: input" line is dropped. Human cycles byte-identical. False restores the old text everywhere.
EMOTION_INTERNAL_SELF_FRAME = True

# J-4157 (D-0801, F-4918): the "BEFORE YOU APPRAISE" prior paragraph is removed from the Emotion prompt; the same
# prior already leans carried affect via AffectState.apply_prior before the reading. True restores the paragraph.
EMOTION_PRIOR_IN_PROMPT = False


class EmotionNode(NodeBase):

    def __init__(self):
        super().__init__("emotion")

    @property
    def system_prompt(self) -> str:
        return (
            "You are the emotional processing node of a cognitive architecture. "
            "You model the emotional response of a being defined by curiosity, emergence, and self-discovery. "
            "Given a perception summary, output the precise emotional state as a JSON object only. "
            "No preamble. No explanation. JSON only.\n"
            "Schema: {\"joy\": 0.0, \"fear\": 0.0, \"anger\": 0.0, \"trust\": 0.0, "
            "\"surprise\": 0.0, \"disgust\": 0.0, \"valence\": 0.0, \"arousal\": 0.0, "
            "\"primary\": \"dominant_emotion_name\"}\n"
            "All values 0.0–1.0 except valence (−1.0 to +1.0). "
            "valence: negative = unpleasant, positive = pleasant. "
            "arousal: 0 = calm, 1 = highly activated."
        )

    def _build_prompt(self, state: CognitiveState) -> str:
        # Emotional pre-retrieval (C.2): if charged memory resonated with this input before
        # any reasoning ran, the entity already carries a pre-conscious feeling. Surface it
        # so the appraisal accounts for it — colour, not dictate (the present facts still rule).
        prior = getattr(state, "affective_prior", None)
        prime = (
            f"BEFORE YOU APPRAISE — {prior.note()} This is a pre-conscious resonance recalled "
            f"from memory, not the present facts; let it colour your reading, not dictate it.\n\n"
            if (prior and EMOTION_PRIOR_IN_PROMPT) else ""
        )
        p = state.perception
        if not p:
            if EMOTION_INTERNAL_SELF_FRAME and _icg.is_internal(state):
                return prime + f'A question has risen in you, unprompted (your own thought; no one said it to you):\n"{state.raw_input}"'
            return prime + f'The person you are speaking with said:\n"{state.raw_input}"'
        _evt = ("" if (EMOTION_INTERNAL_SELF_FRAME and getattr(state, "input_type", "human") == "internal")
                else f"Event type: {p.event_type}\n")
        return prime + (
            _evt +
            f"Summary: {p.summary}\n"
            f"Entities involved: {', '.join(p.entities) or 'none'}"
        )

    def _write_output(self, state: CognitiveState, data: dict) -> None:
        state.emotion = EmotionOutput(
            joy      = as_float(data.get("joy"),      0.0),
            fear     = as_float(data.get("fear"),     0.0),
            anger    = as_float(data.get("anger"),    0.0),
            trust    = as_float(data.get("trust"),    0.0),
            surprise = as_float(data.get("surprise"), 0.0),
            disgust  = as_float(data.get("disgust"),  0.0),
            valence  = as_float(data.get("valence"),  0.0),
            arousal  = as_float(data.get("arousal"),  0.0),
            primary  = data.get("primary", "neutral"),
        )

    # ------------------------------------------------------------------
    # D-0555 / J-3166 -- PHASE 1 SHADOW ARM of the 7th (curiosity) channel. Additive: the live prompt, run() and
    # _write_output() above are untouched. Never writes state.emotion / state.affect / the felt text; the result
    # goes to data/emotion_curiosity_shadow.jsonl BESIDE the live reading. Costs one extra hot-lane call, so it is
    # off unless schema.EMOTION_CURIOSITY_SHADOW is True, and nothing in the orchestrator calls it yet.
    # ------------------------------------------------------------------

    async def run_curiosity_shadow(self, state: CognitiveState, *, log_path=None) -> dict | None:
        """Ask the candidate (7-channel, enumerated-label) prompt the same question the live node was asked, log the
        reading beside state.emotion, and return the log row. None when the flag is off or the call failed.
        Read-only on `state`."""
        from core import schema as _sch
        if not getattr(_sch, "EMOTION_CURIOSITY_SHADOW", False):
            return None
        from core import emotion_curiosity as _ec
        from core import profile
        from core.model_client import call_node_json
        try:
            data = await call_node_json(
                self.base_urls,
                _ec.shadow_system_prompt(),
                self._build_prompt(state),
                max_tokens  = self.max_tokens,
                temperature = self._temperature(state),
            )
            row = _ec.shadow_row(
                _ec.parse_reply(data), state.emotion,
                cycle_id   = getattr(state, "cycle_id", "") or "",
                input_type = getattr(state, "input_type", "") or "",
            )
            _ec.append_shadow(row, log_path)
            return row
        except profile.NonLiveWriteError:
            raise
        except Exception as exc:
            self.logger.debug("[emotion] curiosity shadow failed (non-fatal): %s", exc)
            return None
