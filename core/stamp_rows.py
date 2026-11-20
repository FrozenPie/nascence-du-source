"""Reader-side drop of geometry_tuples census stamp rows (J-3752, F-4361/F-4078/J-3468, D-0688 option B).

store_fragment's write-time census stamp (source 'inner_thought', thought=content[:70]) lands 0.1-0.3 s before the
idle row of the same cycle, so a reader counting cycles sees every idle cycle twice. Since J-3455 the stamp row
carries "stamp": true. Rows written before that marker (restart-gated; ~47,602 twins to 2026-11-05) have no marker
and are found by the same rule scripts/j3468_twin_row_audit.flag_stamp_twins uses: source 'inner_thought' followed
within 1.2 s (5-row look-ahead) by an unclaimed source 'idle' row whose whitespace-normalised thought starts with
the stamp's. This is the core/ twin of scripts/stamp_row_filter.py (core must not import scripts/).

Default behaviour for old rows: unmarked inner_thought rows WITHOUT an idle twin are KEPT (a reading/study stamp is
the only row for its event). `rows` MUST be in file (append) order: the twin rule looks a few rows ahead.
Pure functions, no I/O.
"""
from __future__ import annotations

TWIN_WINDOW_S = 1.2
TWIN_LOOKAHEAD = 5
STAMP_SOURCE = "inner_thought"
IDLE_SOURCE = "idle"


def is_marked_stamp(row: dict) -> bool:
    return bool(row.get("stamp")) and row.get("source") == STAMP_SOURCE


def _is_prefix_twin(stamp_thought, idle_thought) -> bool:
    s = " ".join((stamp_thought or "").split())
    i = " ".join((idle_thought or "").split())
    return len(s) >= 5 and i[:len(s)] == s


def _flag_unmarked_twins(rows: list[dict]) -> set[int]:
    stamps: set[int] = set()
    claimed: set[int] = set()
    n = len(rows)
    for i, r in enumerate(rows):
        if r.get("source") != STAMP_SOURCE:
            continue
        ts0 = float(r.get("ts") or 0)
        for j in range(i + 1, min(n, i + 1 + TWIN_LOOKAHEAD)):
            c = rows[j]
            if c.get("source") != IDLE_SOURCE or j in claimed:
                continue
            dt = float(c.get("ts") or 0) - ts0
            if dt < -0.05 or dt > TWIN_WINDOW_S + 1e-6:
                continue
            if _is_prefix_twin(r.get("thought"), c.get("thought")):
                stamps.add(i)
                claimed.add(j)
                break
    return stamps


def stamp_indices(rows: list[dict]) -> set[int]:
    drop = {i for i, r in enumerate(rows) if is_marked_stamp(r)}
    unmarked = [(i, r) for i, r in enumerate(rows) if i not in drop]
    drop |= {unmarked[k][0] for k in _flag_unmarked_twins([r for _i, r in unmarked])}
    return drop


def drop_stamp_rows(rows: list[dict]) -> list[dict]:
    d = stamp_indices(rows)
    return [r for i, r in enumerate(rows) if i not in d] if d else rows
