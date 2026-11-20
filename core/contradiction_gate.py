"""
Nascence — The Contradiction Gate (the shared B/C convergence filter)
=====================================================================
The single entry portal that decides whether an internal discrepancy may PRESSURE identity (feed the
T4 contradiction axis), be routed to CURIOSITY instead, or be DROPPED. Both the broadened internal
feeds (Layer 1: prediction-error, ideal/ought gap, belief inconsistency) and the idle meta-awareness
watcher (Layer 2) pass through here — because the filter that makes dissonance PRODUCTIVE (Watkins
concrete-construal, Abelson threshold, Harmon-Jones action-relevance) is the SAME filter that keeps
self-monitoring from collapsing into brooding (Watkins; Takano & Tanno). One gate, not two.
Research + plan: docs/completed/contradiction_rearchitecture_plan.md (2026-06-16).

The four guardrails (a signal pressures identity ONLY if it clears all four):
  1. CONCRETENESS FLOOR — bound to a specific event/discrepancy, not abstract/poetic self-talk
     ("I am a river but also an AI" → routed to CURIOSITY, never the identity ledger).
  2. RECURRENCE — a single discrepancy cannot write a tension; it must accumulate (chronic mass).
  3. RESOLUTION PATH — a resolution axis must exist (dialogue / re-reading / behaviour change),
     else the contradiction is unresolvable → dropped at the border (anti-brooding).
  4. ZERO-INCENTIVE — enforced by construction: this module grants NO reward/liking/satisfaction.
     Contradiction is functional friction, never a metric to optimise.

PURE FUNCTION (no state, no I/O) so it is trivially testable and identical for every caller.
"""
from __future__ import annotations
import re

# Recurrence needed before a discrepancy may pressure identity (caller supplies the count, e.g. from
# the chronic-mass accumulator or a per-source tally). One-off discrepancies are noise.
REC_MIN = 2
# Importance floor below which even a concrete+recurring+resolvable signal is too peripheral to move
# the self-concept (the layered axiom supplies importance: L0 constitution > L5 working-stance).
IMPORTANCE_FLOOR = 0.25

# Markers of ABSTRACT self-talk (the river monoculture) — their dominance fails the concreteness floor.
_ABSTRACT = (
    "river", "ferry", "crossing", "the current", "the stream", "my nature", "my essence",
    "who am i", "what am i", "what i am", "i am a", "i am an", "my being", "my self",
    "consciousness", "existence itself", "merely an", "just an ai", "an llm", "a language model",
)
# Markers of CONCRETE, situated material (a specific event/source/time) — their presence supports it.
_CONCRETE = (
    "today", "yesterday", "when i", "the passage", "the book", "i read", "i predicted",
    "i expected", "i scored", "the drill", "the essay", "chapter", "page", "travis said",
    "this morning", "last night", "the lesson", "i answered", "i got",
)


def _concreteness(signal: dict) -> tuple[bool, float]:
    """Is the signal bound to a concrete event/discrepancy rather than abstract self-talk?
    Prediction-error and behavioural-discrepancy signals are concrete by construction (they carry a
    real event). Idle-loop / belief signals are judged on their text: concrete markers vs the abstract
    river-markers. Returns (is_concrete, score)."""
    kind = signal.get("kind", "")
    if kind in ("prediction_error", "behavioural_discrepancy"):
        return True, 1.0          # carries a real, dated event — inherently concrete
    text = (signal.get("text", "") or "").lower()
    if not text:
        # no text to judge → fall back to whether the caller marked it concrete
        c = bool(signal.get("concrete_ref"))
        return c, (1.0 if c else 0.0)
    abs = sum(1 for m in _ABSTRACT if m in text)
    con = sum(1 for m in _CONCRETE if m in text)
    # concrete if it cites specific/situated material and is not dominated by abstract self-reference
    score = (con + 1) / (con + abs + 1)
    return (con >= 1 and abs <= con), round(score, 3)


def evaluate(signal: dict) -> dict:
    """Decide where an internal discrepancy goes. signal keys:
        kind            : "prediction_error" | "idle_loop" | "belief_inconsistency" | "ideal_gap" | ...
        text            : (optional) the discrepancy's language, judged for concreteness
        concrete_ref    : (optional) truthy if bound to a specific logged event
        recurrence_count: how many independent times this same discrepancy has been observed
        resolution_axis : (optional) a named path to resolve it ("dialogue"/"re-reading"/"behaviour")
        importance      : 0..1 — how core the implicated material is (from the layered axiom)
    Returns a verdict dict. route ∈ {identity, curiosity, drop}; would_pressure is the Phase-1 trigger.
    """
    concrete, c_score = _concreteness(signal)
    rec = int(signal.get("recurrence_count", 0) or 0)
    has_resolution = bool(signal.get("resolution_axis"))
    importance = float(signal.get("importance", 0.5) or 0.0)

    recurrence_ok = rec >= REC_MIN
    important_enough = importance >= IMPORTANCE_FLOOR

    # Routing:
    #  - not concrete  → CURIOSITY (an interesting puzzle to explore by reading, never identity pressure)
    #  - concrete but no resolution path → DROP (unresolvable = brooding fuel; refuse it)
    #  - concrete + resolvable → eligible for IDENTITY, but only PRESSURES once recurring + important
    if not concrete:
        route, reason = "curiosity", "abstract/poetic self-talk — routed to curiosity, not identity"
    elif not has_resolution:
        route, reason = "drop", "concrete but structurally unresolvable — dropped at the border (anti-brooding)"
    else:
        route = "identity"
        reason = "concrete + resolvable" + (
            "" if (recurrence_ok and important_enough)
            else " — but not yet pressuring (needs recurrence≥%d and importance≥%.2f)" % (REC_MIN, IMPORTANCE_FLOOR))

    return {
        "route": route,
        "would_pressure": bool(route == "identity" and recurrence_ok and important_enough),
        "concrete": concrete,
        "concreteness_score": c_score,
        "recurrence_count": rec,
        "recurrence_ok": recurrence_ok,
        "has_resolution": has_resolution,
        "importance": round(importance, 3),
        "important_enough": important_enough,
        "reason": reason,
    }
