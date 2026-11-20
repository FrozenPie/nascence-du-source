"""
Nascence -- Recall served log (J-2576, F-3306, plan error_pathway). OBSERVE-ONLY.

WHY. scripts/source_monitoring_audit.py asks whether the origin Du CLAIMS in prose ("I remember",
"I dreamed", "you said") matches the stored origin of the fragments actually served to that prose.
For voice cycles the served set was logged nowhere except founder_recall_log.jsonl (Travis-word ids
only), so the audit could score 102/3662 voice cycles and had to fall back to a TIME join. This
module writes the served set itself, keyed by cycle_id, so the audit can join by id.

WHAT. log_voice_cycle(state) -> ONE row per cycle that reaches voice, appended to
data/recall_served_log.jsonl, written from core/orchestrator.py immediately before the Voice node
runs (so state.memory_fragments is the final set Recall/Reflection/Executive/Voice saw this cycle,
including introspective re-bind, library and epistemic-search additions). Row:
  {ts, cycle_id, input_type, path: "voice", recall_ran, recall_confidence, introspective_passes,
   content_mode, n, fragments: [{fragment_id, origin, layer, abstraction_level, relevance}],
   founder_recall_ids}

CONTRACT. Feeds nothing Du experiences (D-0434): no node reads this file or this module. Never
raises, never blocks the cycle (fail-open, debug log only). Fenced with profile.guard_path (D-0179):
a non-live process is refused before any I/O; core.profile rebases _LOG for a named-profile boot.
Restart-gated: nothing is written until the live process is restarted onto this code.

KILL SWITCH: RECALL_SERVED_LOG_ON = False stops the writer; nothing else changes.
READER: scripts/source_monitoring_audit.py (prefers this log over the time join for voice units).
"""
from __future__ import annotations

import logging
import time
from pathlib import Path

logger = logging.getLogger("nascence.recall_served_log")

# The writer itself. On by default: observe-only, read by the source-monitoring audit only.
RECALL_SERVED_LOG_ON = True

_LOG = Path(__file__).parent.parent / "data" / "recall_served_log.jsonl"

# Hard cap on fragments listed per row (the live set is normally well under this).
_MAX_FRAGMENTS = 40


def _frag_row(f) -> dict | None:
    fid = getattr(f, "fragment_id", None)
    if not fid:
        return None
    rel = getattr(f, "relevance", None)
    try:
        rel = round(float(rel), 3) if rel is not None else None
    except Exception:
        rel = None
    return {
        "fragment_id":       str(fid),
        "origin":            getattr(f, "origin", None),
        "layer":             getattr(f, "layer", None),
        "abstraction_level": getattr(f, "abstraction_level", None),
        "relevance":         rel,
    }


def build_row(state) -> dict:
    frags = []
    for f in list(getattr(state, "memory_fragments", None) or [])[:_MAX_FRAGMENTS]:
        r = _frag_row(f)
        if r:
            frags.append(r)
    rec = getattr(state, "recall", None)
    conf = getattr(rec, "confidence", None) if rec is not None else None
    fr_ids = []
    for h in (getattr(state, "founder_recall", None) or []):
        if isinstance(h, dict) and h.get("fragment_id"):
            fr_ids.append(str(h["fragment_id"]))
    return {
        "ts":                   round(time.time(), 3),
        "cycle_id":             getattr(state, "cycle_id", None),
        "input_type":           getattr(state, "input_type", None),
        "path":                 "voice",
        "recall_ran":           rec is not None,
        "recall_confidence":    round(float(conf), 3) if isinstance(conf, (int, float)) else None,
        "introspective_passes": getattr(state, "introspective_passes", None),
        "content_mode":         bool(getattr(state, "content_mode", False)),
        "n":                    len(frags),
        "fragments":            frags,
        "founder_recall_ids":   fr_ids,
    }


def log_voice_cycle(state) -> None:
    """Append one row for a cycle about to voice. Never raises."""
    try:
        if not RECALL_SERVED_LOG_ON:
            return
        row = build_row(state)
        from core import profile, shadow_log
        shadow_log.append(profile.guard_path(_LOG), row)
    except Exception as exc:
        logger.debug("[recall-served] row skipped (non-fatal): %s", exc)
