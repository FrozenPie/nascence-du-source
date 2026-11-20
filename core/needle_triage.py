"""
Nascence — Needle Triage (2026-08-18, SHADOW / observe-only).

`core/judge_panel.py`'s two-family judge is the load-bearing guard for pursuits.judge_pending and
tension_ledger._judge_resolution, but a resident 3rd (tiebreak) judge doesn't fit the CPU-tier's capacity
("3 at a time was too much" — founder, deferred in docs/staged/DEFERRED_PLANS.md #5). ~52% of panel calls
split with no tiebreak and get dropped after retries, discarding real candidate advances.

Needle 2 (Cactus Compute, 45M params, CQ2-bit, 14MB binary, ~28MB session RAM, CPU-only, no GPU/NPU slot
needed) can't replace the panel's judgment — its own benchmarks are modest (42-64% on structured tool-calling
tasks, nowhere near judge-grade). But it costs almost nothing to run alongside everything else, so it's being
tried here as an independent THIRD READING, not a verdict, logged side by side with the two real judges'
votes, so we can see over real volume whether Needle2 tends to agree with the resolved verdict when there is
one, and whether it leans usefully on splits. SHADOW ONLY — it decides nothing; the calling judge's verdict
is unchanged by this module's output.

WIRED (2026-08-19 — built 2026-08-18, smoke-tested once, then sat unconnected for a day; a codebase survey
caught it before it became genuinely abandoned): `core/pursuits.py`'s `judge_pending()` calls `read()`
alongside every `judge_panel.rule()` call it makes, the one caller whose prompt shape (PURSUIT / PRIOR
POSITION / NEW THOUGHT) actually matches this module's hardcoded prompt. `tension_ledger._judge_resolution`
and `left_lane`'s judges use different prompt shapes — not wired here; would need their own read() variant
or a generalized prompt if this proves worth extending.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

logger = logging.getLogger("nascence.needle_triage")

_DATA = Path(__file__).parent.parent / "data"
_LOG = _DATA / "needle_triage_shadow.jsonl"

NEEDLE_TRIAGE_LIVE = True   # shadow kill-switch: False = module does nothing, callers see None

_ENGINE_ERROR_LOGGED = False


def _verdict_schema():
    from pydantic import BaseModel, Field

    class Verdict(BaseModel):
        advances: bool = Field(description="Does the new thought genuinely advance the pursuit beyond its "
                                             "prior position, vs merely restate/circle it?")
        confidence: float = Field(description="0.0-1.0, how sure you are")

    return Verdict


def read(question: str, prior_standing: str, thought: str, context: str = "") -> dict | None:
    """One independent structured-extraction read on the same advance/restate question the judge panel
    rules on. Returns {"advances": bool, "confidence": float, "elapsed_ms": float} or None (engine
    unavailable / any error — fail-open, never raises, never blocks a real judge call)."""
    global _ENGINE_ERROR_LOGGED
    if not NEEDLE_TRIAGE_LIVE:
        return None
    t0 = time.time()
    try:
        import needle
        Verdict = _verdict_schema()
        prompt = (f"PURSUIT: {question[:200]}\n\n"
                  f"ITS PRIOR POSITION: {prior_standing[:280]}\n\n"
                  f"NEW THOUGHT: {thought[:450]}\n\n"
                  "Does the new thought advance the pursuit beyond its prior position, or merely restate it?")
        v = needle.extract(prompt, Verdict)
        if v is None:
            return None
        out = {"advances": bool(v.advances), "confidence": round(float(v.confidence), 3),
               "elapsed_ms": round((time.time() - t0) * 1000, 1)}
        _log({"ts": time.time(), "context": context[:80], **out})
        return out
    except Exception as exc:
        if not _ENGINE_ERROR_LOGGED:
            logger.warning("[needle_triage] engine unavailable (logged once): %s", exc)
            _ENGINE_ERROR_LOGGED = True
        return None


def _log(ev: dict) -> None:
    try:
        _DATA.mkdir(parents=True, exist_ok=True)
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    except Exception:
        pass
