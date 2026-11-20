"""
Nascence — Shadow Log: shared plumbing for the "soft live path + hard grader running in shadow,
decide from accrued data" pattern (docs/reviews/soft_live_hard_shadow_pattern_2026-08-23.md, J-0007).

Extracted from the ~10-line JSONL-append + status() boilerplate independently hand-written in
memory_levels.py's gist-faithfulness grading, geometry_census.py, stream_drive.py, stick_test.py, and
journal_grounding_shadow.py — every one of the five re-typed the same `_DATA.mkdir(...)` /
`open(_LOG, "a")` / `json.dumps(row) + "\n"` wrapped in a bare `try/except: pass`, plus a `status()`
that re-reads the whole file and computes a mean/fraction.

Only the LOGGING mechanics are shared here, deliberately. A generic abstraction over the JUDGE call
itself was considered and rejected (see the review doc) — each instrument's signal is genuinely
different (drive/gap physics vs cross-space tuple structure vs gist-faithfulness), so the grading logic
stays plan-specific. This module doesn't know what a "faithful" score means; it just appends rows and
computes generic per-field stats.

append(path, row)          — mkdir + open-append + json.dumps + fail-open. Never raises.
read_rows(path)            — every parsed row, oldest first. Fail-open: [] on any error, including a
                              missing file — matches the read-side of every existing status().
summarize(path, fields=)   — generic per-field stats (mean/min/max for numbers, true_frac for bools,
                              total_len/nonempty_rows for lists, n_nonnull for anything else). Fail-open:
                              {"rows": 0} on any failure, matching every existing status()'s fail-open
                              contract.

Callers keep owning their own `_LOG = Path(__file__).parent.parent / "data" / "whatever.jsonl"` — this
module doesn't own that convention, just the read/write mechanics under it. A shadow instrument with
bespoke per-row filtering (e.g. journal_grounding_shadow.status()'s "low_faithful_caps" list) still
writes its own status() on top of `read_rows()` — summarize() is for the common case, not a replacement
for plan-specific logic.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Iterator

logger = logging.getLogger("nascence.shadow_log")


def append(path: Path, row: dict) -> bool:
    """Append one JSON row to `path`, creating its parent dir if needed. Fail-open: any error is
    swallowed (logged at debug) — a shadow logger must never be able to break the live call it's
    observing. Returns True on success, False on any failure (caller usually doesn't need to check)."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return True
    except Exception as exc:
        logger.debug("[shadow_log] append to %s failed (non-fatal): %s", path, exc)
        return False


def read_rows(path: Path) -> list[dict]:
    """Every parsed JSON row in `path`, oldest first. Fail-open: returns [] if the file is missing,
    empty, or unreadable — a malformed line is skipped rather than aborting the whole read."""
    try:
        rows = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    rows.append(json.loads(line))
                except Exception:
                    continue
        return rows
    except Exception:
        return []


def reverse_lines(path: Path, chunk_size: int = 262144) -> Iterator[bytes]:
    """Yield raw lines of `path` newest-first, reading backward from EOF in chunks so a caller can
    stop early without scanning the whole file. Port of hud/server.py's _reverse_lines() (J-0224) into
    shared plumbing (J-0278 / F-0335) so no module hand-rolls another copy. Each byte is read and each
    line seen at most once — no re-scanning of already-read data. Use this generator DIRECTLY for a
    read that FILTERS while walking backward ("last N rows matching X" where X is sparse); use
    tail_rows() below for the plain "last N rows regardless of content" case (the F-0318 distinction).
    Raises on I/O error — callers wrap in try/except (tail_rows does)."""
    with open(path, "rb") as f:
        f.seek(0, os.SEEK_END)
        pos = f.tell()
        buf = b""
        while pos > 0:
            read_size = min(chunk_size, pos)
            pos -= read_size
            f.seek(pos)
            buf = f.read(read_size) + buf
            lines = buf.split(b"\n")
            for line in reversed(lines[1:]):
                yield line
            buf = lines[0]          # leftmost fragment carries no "\n" — never re-yielded, never re-read
        if buf:
            yield buf


def tail_rows(path: Path, limit: int) -> list[dict]:
    """The last `limit` parsed JSON rows of `path`, OLDEST-FIRST — a bounded drop-in for
    `read_rows(path)[-limit:]` that reads ~limit rows from EOF instead of json.loads-ing every line of
    an ever-growing log (J-0278 / F-0335: 21 _EVIDENCE_MODULES status() functions did the full scan on
    logs up to 4.4MB, polled every ~6s by the HUD). Fail-open: [] on missing/unreadable file; a
    malformed line is skipped (does not count toward `limit`), matching read_rows()'s contract."""
    try:
        if limit <= 0:
            return []
        out: list[dict] = []
        for raw in reverse_lines(path):
            line = raw.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                continue
            if len(out) >= limit:
                break
        out.reverse()
        return out
    except Exception:
        return []


def summarize(path: Path, fields: list[str] | None = None) -> dict[str, Any]:
    """Generic per-field summary of a shadow log. `fields` restricts which keys get summarized
    (default: every key on the first row). Per field, by the type of its first non-null value seen:
      - bool                          -> {"true_frac", "n"}
      - int/float (excluding bool)    -> {"mean", "min", "max", "n"}
      - list                          -> {"total_len", "nonempty_rows"}  (e.g. an 'invented' list)
      - anything else                 -> {"n_nonnull"}
    Always includes "rows": total row count. Fail-open: {"rows": 0} on any failure, missing file, or
    empty file."""
    rows = read_rows(path)
    if not rows:
        return {"rows": 0}
    try:
        keys = fields if fields else list(rows[0].keys())
        out: dict[str, Any] = {"rows": len(rows)}
        for key in keys:
            non_null = [r[key] for r in rows if r.get(key) is not None]
            if not non_null:
                out[key] = {"n_nonnull": 0}
                continue
            sample = non_null[0]
            if isinstance(sample, bool):
                out[key] = {"true_frac": round(sum(1 for v in non_null if v) / len(non_null), 3),
                            "n": len(non_null)}
            elif isinstance(sample, (int, float)):
                nums = [v for v in non_null if isinstance(v, (int, float)) and not isinstance(v, bool)]
                out[key] = ({"mean": round(sum(nums) / len(nums), 3), "min": min(nums), "max": max(nums),
                            "n": len(nums)} if nums else {"n_nonnull": len(non_null)})
            elif isinstance(sample, list):
                out[key] = {"total_len": sum(len(v) for v in non_null if isinstance(v, list)),
                            "nonempty_rows": sum(1 for v in non_null if isinstance(v, list) and v)}
            else:
                out[key] = {"n_nonnull": len(non_null)}
        return out
    except Exception:
        return {"rows": len(rows)}
