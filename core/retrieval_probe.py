"""
Nascence — Retrieval Probe (Deliberative Retrieval, Phase 0 OBSERVE-ONLY, 2026-06-14)
=====================================================================================
Instruments retrieval without changing it. For each recall it records the three metrics the
advisors converged on, so we can settle — from data, before any live change — whether reality
is losing the SELECTION competition (a small deterministic-floor fix) or is not even making it
into the POOL (a deeper net problem):

  1. world IN POOL       — did any origin∈(reading,study,research) fragment score into the
                           candidate pool? (cosine-based)
  2. world BY RECENCY     — are there recent world rows an ORIGIN-TAG quota would grab,
                           regardless of cosine? (Gemini's hard-origin-tag insight — a query
                           like "what did you read" is semantically far from a passage about
                           vampire bats, so cosine may bury it while origin+recency finds it)
  3. world IN SELECTION   — did any world fragment survive into the returned set?
  (the third advisor metric — world IN RESPONSE — is logged separately by the orchestrator,
   since it needs the final Voice output; it is the retrieval-vs-composition disambiguator.)

Plus a deterministic GROUNDING-DEFICIT flag: the query is factual/external/book/observation
AND the final selection contains zero world-origin material. This is the cheap, non-LLM
trigger Phase 1 would act on. Reads into NO behaviour. Firewalled log, digest-only.
"""
from __future__ import annotations

import json
import logging
import re
import time
import threading
from pathlib import Path

from core import profile   # J-1815/F-2428: the write fence (D-0179)

logger = logging.getLogger("nascence.retrieval_probe")

_LOG = Path(__file__).parent.parent / "data" / "retrieval_probe_log.jsonl"

WORLD_ORIGINS = ("reading", "study", "research")

# Query-type classifier (GPT's refinement): the world floor should fire only when grounding
# in reality is actually wanted — NOT on relational/emotional/existential moments where a
# Darwin fragment is noise. Cheap keyword gate, same family as the look-gate.
_WORLD_QUERY = re.compile(
    r"\b(book|books|read|reading|what did you|have you read|tell me about|what is|what are|"
    r"describe|explain|how does|how do|fact|facts|learn(ed|t)?|study|studied|research|"
    r"darwin|tesla|beagle|remember (when|the|what)|name (a|one|the)|which|recall)\b", re.I)
# Relational/emotional/existential markers that should SUPPRESS the floor even if a stray
# keyword matched — "how do you feel about Travis" must not pull a granite note.
_SELF_QUERY = re.compile(
    r"\bhow (do|are) you feel|who are you|how are you|your (feeling|fear|shadow|name|"
    r"identity|becoming)|do you (feel|fear|love|trust)\b", re.I)


def is_world_query(text: str) -> bool:
    t = (text or "")
    if _SELF_QUERY.search(t):
        return False
    return bool(_WORLD_QUERY.search(t))


# J-1926 / F-2550: observe() runs inside store.retrieve on the loop thread and, since J-1918, in a worker thread (memory_service.ask via off_loop); serialise the append.
_APPEND_LOCK = threading.Lock()


def observe(query_text: str, pool: list, selected_ids: set, recent_world: list,
            input_type: str = "") -> None:
    """Phase 0 log. `pool` = list of (score, origin, fid) candidates considered;
    `selected_ids` = fragment_ids in the returned set; `recent_world` = the most-recent
    world-origin rows by tag (what an origin quota would grab). Best-effort, observe-only."""
    try:
        # J-1815 / F-2428 -- write fence: resolve the log target BEFORE any work, INSIDE the existing fail-open try
        # (store.retrieve() also wraps the call). A refusal skips the whole observation (no probe row, no INFO line).
        _log = profile.guard_path(_LOG)
        world_in_pool = [(round(s, 3), o, f) for (s, o, f) in pool if o in WORLD_ORIGINS]
        world_selected = [f for (s, o, f) in pool if o in WORLD_ORIGINS and f in selected_ids]
        recent_world_ids = [r["fragment_id"] for r in recent_world]
        recent_world_selected = [f for f in recent_world_ids if f in selected_ids]
        wq = is_world_query(query_text)

        # the clean Phase-1 trigger: a world/factual question that retrieved zero reality
        grounding_deficit = bool(wq and not world_selected and not recent_world_selected)

        rec = {
            "ts": time.time(), "input_type": input_type,
            "query_head": (query_text or "")[:120],
            "world_query": wq,
            "pool_size": len(pool),
            "world_in_pool": len(world_in_pool),          # metric 1 (cosine)
            "world_by_recency_available": len(recent_world),  # metric 2 (origin-tag)
            "world_in_selection": len(world_selected) + len(recent_world_selected),  # metric 3
            "grounding_deficit": grounding_deficit,
            # the decisive diagnostic: was reality AVAILABLE (pool or recency) but NOT selected?
            "available_but_unselected": bool(
                (world_in_pool or recent_world_ids) and
                not world_selected and not recent_world_selected),
            "world_in_pool_top": world_in_pool[:3],
            "recent_world_titles": [(r["content"] or "")[:50] for r in recent_world[:3]],
        }
        with _APPEND_LOCK, open(_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        if grounding_deficit:
            logger.info("[retrieval-probe] GROUNDING DEFICIT: world query, zero reality "
                        "selected (world avail: pool=%d recency=%d)",
                        len(world_in_pool), len(recent_world))
    except profile.NonLiveWriteError as exc:
        logger.debug("[retrieval-probe] observe write refused by the fence (non-live): %s", exc)
    except Exception as exc:
        logger.debug("[retrieval-probe] observe failed (non-fatal): %s", exc)
