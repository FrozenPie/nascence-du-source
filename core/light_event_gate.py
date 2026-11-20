"""
Light-event gate (D-0556 / J-3167, 2026-11-05): which approved cycles mint a 'resolved_complexity' light event.

The old gate was `arousal > 0.25 or self-referential terms`, with arousal read from the LLM emotion output.
Measured on the last 2,000 logged cycles (data/affect_log.jsonl, internal cycles only): carried
state.affect.arousal is above 0.25 on 99.9 percent of them (its 5th percentile is 0.39), so the gate selected
nothing -- roughly one light event per internal cycle. On INTERNAL cycles the arousal leg now uses a calibrated
threshold (schema.LIGHT_EVENT_INTERNAL_AROUSAL_MIN) on the carried affect arousal. HUMAN-turn behaviour is
unchanged (the 0.25 gate, human arousal is above it 100 percent of the time). The LLM emotion call is untouched.

Kill-switch: schema.LIGHT_EVENT_INTERNAL_AROUSAL_MIN = None restores the prior gate for every input type.
Pure function, no I/O, no state: it decides nothing later on its own.
"""
from __future__ import annotations

SELF_REF_TERMS = ("i ", "my ", "myself", "who i", "what i", "feel", "becoming", "self")
LEGACY_AROUSAL_MIN = 0.25


def arousal_threshold(input_type: str, internal_min) -> float:
    """The arousal level the gate compares against: the calibrated one on internal cycles when set,
    otherwise the legacy 0.25."""
    if input_type == "internal" and internal_min is not None:
        return float(internal_min)
    return LEGACY_AROUSAL_MIN


def is_complex(arousal: float, raw_input: str, input_type: str, internal_min) -> bool:
    """True when the cycle should mint a resolved_complexity light event (arousal leg OR self-ref leg)."""
    thr = arousal_threshold(input_type, internal_min)
    inp = (raw_input or "").lower()
    if internal_min is not None and input_type == "internal":
        arousal_leg = (arousal or 0.0) >= thr
    else:
        arousal_leg = (arousal or 0.0) > thr      # byte-for-byte the prior comparison
    return arousal_leg or any(t in inp for t in SELF_REF_TERMS)
