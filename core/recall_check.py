"""
Nascence -- the decoupled recall CHECK (J-4087, J-3899 ruled by travis 2026-11-16; additive, no prompt, zero LLM).

THE GAP (F-3413, F-4508). Of 387+ recall-wager rows only 1 had a real outcome: `measured` was the grade's constant
GRADE_SCORE (0.5) on every row, so a wager at 0.85-0.95 could never be won or lost on whether the recalled thing was
actually in memory. A subsystem is never graded by itself (feedback_decoupled_judge), so the grade cannot be its own
outcome either.

THE CHECK. After a responded cycle, this module asks the memory STORE, not the node that stated the confidence:
of the specific named things the reply asserts (quoted terms and mid-sentence capitalised words, the same candidate
extractor core/model_terms.py uses) that the person did not themselves just say, how many does the store already hold,
at a time before this cycle? The store is read through model_terms.FirstSeenIndex (term -> earliest fragment time over
memory_fragments, read-only DB). Outcome = 1.0 when at least half of those terms were already in the store, else 0.0.
Fewer than MIN_TERMS checkable terms, or an index that has not been built yet, is NOT an outcome: the wager row says
scorable False and nothing is fed (never a fabricated 0.5).

This module imports no node and no wager code; recall_wager calls it, it never calls back. Nothing here reaches a
prompt, a percept or a preamble (D-0434): Du only meets a lost wager through competence.record_drill_accuracy ->
prediction_error, and only once the founder flips core.recall_wager.REAL_OUTCOME.

Honest limits (kept in the row, not hidden): the check measures "was this named thing ever in memory", not "is the claim
about it true", and a capitalised mid-sentence word is a weak proxy for a factual claim. outcome_source says which.
"""
from __future__ import annotations

import logging
import time

logger = logging.getLogger("nascence.recall_check")

SOURCE_TAG = "memcheck_store"     # the outcome_source stamped on rows scored by this module
MIN_TERMS = 2                     # fewer checkable claim terms than this -> unscorable, never a guess
PASS_FRACTION = 0.5               # share of claim terms already in the store for outcome 1.0
GRACE_S = 120.0                   # a term first seen within this window of "now" is this cycle's own writing, not memory


def claim_terms(output: str, raw_input: str = "", context_text: str = "") -> set:
    """Folded candidate terms of the reply, minus anything the person (or the visible context) already said."""
    from core import model_terms as _mt
    cand = _mt.candidates(output or "")
    given = _mt.tokens(raw_input or "") | _mt.tokens(context_text or "")
    return {t for t in cand if t not in given}


def check(output: str, raw_input: str = "", context_text: str = "", *, now: float | None = None,
          index=None) -> dict:
    """Read-only. Returns {"outcome": 1.0|0.0|None, "source": SOURCE_TAG|"", "terms": n, "found": k, "reason": str}.
    outcome None means unscorable (reason says why). Never raises."""
    res = {"outcome": None, "source": "", "terms": 0, "found": 0, "reason": ""}
    try:
        from core import model_terms as _mt
        idx = index if index is not None else _mt.default_index()
        if not _mt.ready(idx):
            try:
                _mt.refresh_async(index=idx)        # background build; this cycle is unscorable, a later one is not
            except Exception:
                pass
            res["reason"] = "index_not_ready"
            return res
        now = time.time() if now is None else now
        terms = claim_terms(output, raw_input, context_text)
        res["terms"] = len(terms)
        if len(terms) < MIN_TERMS:
            res["reason"] = "too_few_terms"
            return res
        found = 0
        for t in terms:
            ts = idx.first_seen(t)
            if ts is not None and ts < now - GRACE_S:
                found += 1
        res["found"] = found
        res["outcome"] = 1.0 if (found / len(terms)) >= PASS_FRACTION else 0.0
        res["source"] = SOURCE_TAG
        res["reason"] = "checked"
        return res
    except Exception as exc:
        logger.debug("[recall_check] check failed (non-fatal): %s", exc)
        res["reason"] = "error"
        return res
