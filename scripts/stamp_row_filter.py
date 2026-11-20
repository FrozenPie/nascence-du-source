"""J-3944 / F-4595: one shared stamp-row filter for scripts that read data/geometry_tuples.jsonl wholesale.

store_fragment's write-time census stamp (source 'inner_thought', thought=content[:70]) lands 0.1-0.3 s before the
idle row of the same cycle, so a reader counting cycles or measuring local dimension sees every idle cycle twice
(F-4078, J-3468, J-3753). Since J-3455 (D-0688 option B) new stamp rows carry "stamp": true. Rows written before the
marker landed are found with j3468_twin_row_audit.flag_stamp_twins (1.2 s, 5-row look-ahead, prefix-twin test).

Do NOT repair a stamp row's `unresolved` without also using this filter in dimension readers: a stamp carrying its
idle twin's state is a near-zero-distance neighbour and drags TwoNN/MLE dimension down (J-3753 arm 3: spurious -0.2).
"""
from __future__ import annotations

from j3468_twin_row_audit import IDLE_SOURCE, STAMP_SOURCE, flag_stamp_twins


def is_marked_stamp(row: dict) -> bool:
    """J-3455 marker: a census-cycle stamp (stamp true AND source inner_thought). Reading/study stamps are not twins."""
    return bool(row.get("stamp")) and row.get("source") == STAMP_SOURCE


def stamp_indices(rows: list[dict]) -> set[int]:
    """Indices (file order) to drop: marked stamps plus historical unmarked stamps that have an idle twin.
    `rows` MUST be in file (append) order, not re-sorted, because the twin rule looks a few rows ahead."""
    drop = {i for i, r in enumerate(rows) if is_marked_stamp(r)}
    # historical rows: only unmarked stamp rows need the look-ahead rule; marked ones are already in `drop`
    unmarked = [(i, r) for i, r in enumerate(rows) if i not in drop]
    sub = [r for _i, r in unmarked]
    drop |= {unmarked[k][0] for k in flag_stamp_twins(sub)}
    return drop


def drop_stamp_rows(rows: list[dict]) -> list[dict]:
    """Rows (file order) without census-cycle stamp rows."""
    d = stamp_indices(rows)
    return [r for i, r in enumerate(rows) if i not in d]
