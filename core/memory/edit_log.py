"""Per-edit before/after log for importance changes (J-4410, plan memory_review_adoption item M1).

WHAT. One append-only row per importance edit made by the three sleep writers that rewrite
memory_fragments.importance in place:
    replay    core/memory/store.py replay_strengthen   (x1.08, capped 0.98)
    downscale core/memory/store.py downscale_episodic  (center + (old - center) * factor)
    dream_fade core/night.py dream_fade                (halving curve past the vivid day)
Row: {ts, stage, fragment_id, old_importance, new_importance, cold_before}. The row is written BEFORE the
UPDATE runs, so a crash mid-sleep still leaves the intended edit on record. Cold flips are NOT logged here:
the memory_pool_changes trigger table already records them.

WHY. Before this, an importance value was only ever its latest number; nothing could say what a given
night did to a given fragment. This is the before/after record the memory review asked for in place of a
git-backed store (Letta-style), at a few hundred rows a night.

RULES. Shadow only: the log is never read by Du, never reaches a prompt, percept or preamble (D-0434). It
must not change behaviour: every function here swallows its own errors and returns, and the callers'
UPDATE statements are unchanged. Restart-gated (the writers are imported at boot).
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Callable, Iterable

logger = logging.getLogger(__name__)

# "shadow" = write the log (no behaviour change, nothing read back); "off" = no-op.
MEMORY_EDIT_LOG_MODE = "shadow"

_ROOT = Path(__file__).resolve().parent.parent.parent
EDIT_LOG_PATH = _ROOT / "data" / "memory_edit_log.jsonl"     # the ONE write target

# A bulk call that would log more rows than this writes one summary row instead (downscale_episodic with
# since_ts=None touches the whole episodic layer; no live caller does that, but a lab one could).
MAX_ROWS_PER_CALL = 5000


def enabled() -> bool:
    return MEMORY_EDIT_LOG_MODE == "shadow"


def _target(path: Path | None) -> Path:
    if path is not None:
        return Path(path)
    from core import profile
    return profile.guard_path(EDIT_LOG_PATH)


def log_edits(stage: str, edits: Iterable[tuple], path: Path | None = None) -> int:
    """Append one row per (fragment_id, old_importance, new_importance, cold_before). Never raises.
    Returns the number of rows written (0 when off or on any error)."""
    if not enabled():
        return 0
    try:
        ts = round(time.time(), 3)
        lines = []
        for fid, old, new, cold in edits:
            lines.append(json.dumps({
                "ts": ts, "stage": stage, "fragment_id": fid,
                "old_importance": None if old is None else round(float(old), 6),
                "new_importance": None if new is None else round(float(new), 6),
                "cold_before": None if cold is None else int(cold),
            }, ensure_ascii=False))
        if not lines:
            return 0
        if len(lines) > MAX_ROWS_PER_CALL:
            lines = [json.dumps({"ts": ts, "stage": stage, "fragment_id": None, "old_importance": None,
                                 "new_importance": None, "cold_before": None,
                                 "truncated_rows": len(lines)}, ensure_ascii=False)]
        target = _target(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "a", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        return len(lines)
    except Exception as exc:          # includes profile.NonLiveWriteError: no write, behaviour untouched
        logger.debug("[memory_edit_log] %s: log skipped (non-fatal): %s", stage, exc)
        return 0


def log_bulk_before(conn, stage: str, where: str, params: tuple, new_fn: Callable[[float], float],
                    path: Path | None = None) -> int:
    """For a set-based UPDATE ... WHERE <where>: read the rows it is about to touch on the SAME connection,
    compute each new value with `new_fn(old)` (the UPDATE's own formula) and log them. Call it immediately
    before the UPDATE. Off -> no query at all. Never raises."""
    if not enabled():
        return 0
    try:
        rows = conn.execute(f"SELECT fragment_id, importance, cold FROM memory_fragments WHERE {where}",
                            params).fetchall()
        edits = []
        for r in rows:
            old = r[1]
            new = None if old is None else new_fn(float(old))
            edits.append((r[0], old, new, r[2]))
        return log_edits(stage, edits, path=path)
    except Exception as exc:
        logger.debug("[memory_edit_log] %s: bulk read skipped (non-fatal): %s", stage, exc)
        return 0
