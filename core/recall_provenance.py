"""
Nascence — Recall Provenance (the "why now" tag)

Recall already answers WHAT is being remembered and WHERE the tensions are. It does not
record WHY this memory surfaced on THIS cycle. Without that, every retrieval looks the
same from the outside, and we cannot tell a memory that was dragged up by an external
correction from one the system reached for on its own — which is precisely the
distinction that matters for the reality-thinness question: how often does anything from
OUTSIDE the narrative cause a recall, versus the system associating with its own material.

This module is pure observation. It classifies the dominant trigger for the cycle's
retrieval from signals already computed on CognitiveState, and appends one line per
recall to data/recall_provenance_log.jsonl. It feeds nothing back into behaviour — no
node reads it, no routing changes. The session digest reads the log to show the trigger
mix and whether external-sourced recalls actually yield richer reconstructions than
self-associative ones.

The trigger ladder (first match wins — strongest "why now" at the top):
  social_correction — a correction signal fired (δ_social spiked); the memory came up
                      because the OUTSIDE pushed back. The one genuinely external edge.
  autonomous        — an internal/ignition cycle: the thought (and its recall) originated
                      from the system's own climate dissonance, not from any input.
  direct_reference  — the human explicitly invoked prior conversation ("you said earlier").
                      External, but solicited memory, not contested.
  affective_prior   — charged memory leaned the cycle pre-cortically (C.2) before reasoning;
                      a felt pull, not a reasoned retrieval.
  associative       — plain semantic retrieval surfaced fragments; the default self-loop.
  none              — recall ran with no fragments to stand on.

Best-effort throughout: a classification or log failure must never perturb a cycle.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

logger = logging.getLogger("nascence.recall_provenance")

_LOG_PATH = Path(__file__).parent.parent / "data" / "recall_provenance_log.jsonl"

# δ_social at or above this is treated as a live correction spike for trigger purposes.
# Matches the spirit of the social model's override threshold without importing it.
_DELTA_SOCIAL_SPIKE = 0.30

TRIGGERS = (
    "social_correction",
    "autonomous",
    "direct_reference",
    "affective_prior",
    "associative",
    "none",
)

# Which triggers count as memory surfacing because of something OUTSIDE the system's own
# narrative loop. This is the number the reality-thinness discussion actually cares about.
EXTERNAL_TRIGGERS = frozenset({"social_correction", "direct_reference"})


def classify_retrieval_trigger(
    state,
    *,
    delta_social: float = 0.0,
    conversation_reference: bool = False,
) -> dict:
    """
    Determine the dominant reason memory surfaced this cycle. Pure — reads state, no I/O.

    Args:
      state:                  the live CognitiveState (read-only here).
      delta_social:           social prediction error this cycle (correction spike signal).
      conversation_reference: True if the raw input explicitly referenced prior dialogue
                              (the orchestrator already computes this for _should_recall).

    Returns a record dict (also the thing logged). Never raises.
    """
    try:
        frags = list(getattr(state, "memory_fragments", []) or [])
        recall = getattr(state, "recall", None)
        input_type = getattr(state, "input_type", "human")
        social_note = getattr(state, "social_note", None)
        affective_prior = getattr(state, "affective_prior", None)

        correction = bool(social_note) or (float(delta_social or 0.0) >= _DELTA_SOCIAL_SPIKE)

        if correction:
            trigger = "social_correction"
        elif input_type != "human":
            trigger = "autonomous"
        elif conversation_reference:
            trigger = "direct_reference"
        elif affective_prior is not None:
            trigger = "affective_prior"
        elif frags:
            trigger = "associative"
        else:
            trigger = "none"

        return {
            "cycle_id":       getattr(state, "cycle_id", "") or "",
            "ts":             time.time(),
            "trigger":        trigger,
            "external":       trigger in EXTERNAL_TRIGGERS,
            "input_type":     input_type,
            "delta_social":   round(float(delta_social or 0.0), 3),
            "fragment_count": len(frags),
            "recall_confidence": (
                round(float(recall.confidence), 3) if recall is not None else None
            ),
            "tension_count": (
                len(recall.tensions) if (recall is not None and recall.tensions) else 0
            ),
            "driver": (
                getattr(state.attention, "driver", None)
                if getattr(state, "attention", None) else None
            ),
        }
    except Exception as exc:  # observation must never break a cycle
        logger.debug("[recall_provenance] classify failed (non-fatal): %s", exc)
        return {"cycle_id": getattr(state, "cycle_id", "") or "", "ts": time.time(),
                "trigger": "none", "external": False}


def log_retrieval(record: dict) -> None:
    """Append one classified retrieval to the jsonl log. Best-effort — silent on failure."""
    try:
        _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.debug("[recall_provenance] log write failed (non-fatal): %s", exc)


def observe(state, *, delta_social: float = 0.0,
            conversation_reference: bool = False) -> dict:
    """Classify + log in one call. Returns the record (handy for inline logging)."""
    rec = classify_retrieval_trigger(
        state, delta_social=delta_social, conversation_reference=conversation_reference
    )
    log_retrieval(rec)
    return rec
