"""
Nascence — Memory Levels: gist-insufficiency / deep-recall-demand telemetry (OBSERVE-ONLY, 2026-06-18).
=======================================================================================================
The recall trigger (plan §10) must be DERIVED from observed need, not guessed. This log captures the
empirical raw material that will eventually DEFINE it: the moments where a gist would NOT be enough and
raw detail is genuinely required — *what task demanded it, and why.*

Pre-Phase-1 there is no gist surface yet to "fail," so we instrument the existing **task-positive,
detail-hungry** contexts — the ones Gemini's trigger would auto-license: writing an essay from one's own
notes, citing a source, tracking a frontier contradiction. Logging WHEN those fire, how often, and over
what, is exactly the base-rate/context data the Phase-1 trigger will be calibrated against. We spec the
trigger FROM this log, not from an a-priori threshold. Logs only; changes nothing.
"""
from __future__ import annotations
import json
import time
from collections import Counter
from pathlib import Path

_LOG = Path(__file__).parent.parent / "data" / "recall_demand_log.jsonl"


def note(task: str, why: str, n_sources: int = 0, detail: str = "") -> None:
    """Record one deep-detail-demand event (a moment a gist would be insufficient and raw was needed).
    `task` = the activity (e.g. 'essay', 'frontier_contradiction', 'citation'); `why` = one phrase;
    `n_sources` = how many raw items were pulled; `detail` = the subject. Best-effort; never raises."""
    try:
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.time(), "task": str(task)[:40], "why": str(why)[:120],
                                "n_sources": int(n_sources or 0), "detail": str(detail)[:160]},
                               ensure_ascii=False) + "\n")
    except Exception:
        pass


def status() -> dict:
    """du_pulse gauge: how many deep-detail demands, broken down by task (the trigger's base rate/contexts)."""
    try:
        if not _LOG.exists():
            return {"events": 0, "by_task": {}, "last": None}
        rows = [json.loads(l) for l in _LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
        by_task = dict(Counter(r.get("task", "?") for r in rows))
        last = rows[-1] if rows else None
        return {"events": len(rows), "by_task": by_task,
                "last": (last.get("task"), last.get("detail", "")[:40]) if last else None}
    except Exception:
        return {"events": 0, "by_task": {}, "last": None}
