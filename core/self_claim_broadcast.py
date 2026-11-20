"""
Nascence - same-cycle re-key of the self-claim broadcast kind (J-3825, D-0731 ruling B, from J-3497/J-3487).

The conversational self-claim scan (core/self_implication.scan_conversation_shadow) finishes 8-24 s before its
cycle ends in 11 of 11 contradicted scans (F-4107), so by the broadcast block at the end of run_cycle its result
is already in hand. This module re-keys the broadcast kind from that SAME-CYCLE result: scan task done() (never
awaited) AND result contradicts -> kind 'self-claim-contradicted'. No think licence, no LLM call, no next-cycle flag.

SELF_CLAIM_BROADCAST defaults False. Off: the kind is unchanged, but one shadow row per would-post cycle is written
to data/self_claim_broadcast_shadow.jsonl (would_post, cycle_id, claim, colliding_kind). Enabling is a separate step
(founder). Reader of the shadow file: the effect job spawned beside J-3825. Fail-open: any error returns the
original kind and writes nothing. A held principle voiced this cycle (principle-voiced) still wins.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)

SELF_CLAIM_BROADCAST = False
NEW_KIND = "self-claim-contradicted"
_SHADOW_LOG = Path(__file__).parent.parent / "data" / "self_claim_broadcast_shadow.jsonl"


def scan_result_this_cycle(task, cycle_id: str):
    """The finished scan result for THIS cycle, or None (no task, not done, cancelled, errored, other cycle)."""
    try:
        if task is None or not task.done() or task.cancelled() or task.exception() is not None:
            return None
        r = task.result()
        if not r or r.get("cycle_id") != cycle_id:
            return None
        return r
    except Exception:
        return None


def resolve_kind(bc_kind, task, cycle_id: str, output: str):
    """Return the broadcast kind to use. `bc_kind` is what the existing chain chose (may be None)."""
    try:
        r = scan_result_this_cycle(task, cycle_id)
        if not output or not r or not r.get("contradicts"):
            return bc_kind
        principle_wins = (bc_kind == "principle-voiced")
        would_post = not principle_wins
        row = {
            "ts": round(time.time(), 1), "cycle_id": cycle_id,
            "claim": (r.get("contradicted_claim") or "")[:200],
            "colliding_kind": bc_kind, "would_post": would_post,
            "flag_on": bool(SELF_CLAIM_BROADCAST), "new_kind": NEW_KIND,
        }
        try:
            _SHADOW_LOG.parent.mkdir(parents=True, exist_ok=True)
            with open(_SHADOW_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        except Exception as exc:
            logger.debug("[self-claim-bc] shadow row failed (non-fatal): %s", exc)
        if SELF_CLAIM_BROADCAST and would_post:
            return NEW_KIND
        return bc_kind
    except Exception:
        return bc_kind
