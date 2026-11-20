"""J-3191 / D-0578 (founder, 2026-11-02; plan memory_knowledge; finding F-3779, row P-0066):
mark the stored understanding notes whose body is a raw Python dict/list repr, so Recall skips them.

WHY. core/grounded_learning.py stored `str(data.get("understanding"))`; when the model returned an object for that key
the repr was stored: "[Understanding - from 'The Prince'] {'grasp_of_content': ...". 61 such notes (2026-06-23 to
2026-08-23) are 45 percent of the understanding items the recall node saw. The ruling: MARK, never delete -- the rows
stay in the store, the marking is reversible, and the mark is what Recall reads.

THE MARK IS THE EXISTING `memory_fragments.temp = 'hidden'` TIER (Memory Levels Axis 4, J-0365) -- no new column, no
new write path in the hot loop. It is already honoured by: store.retrieve (both the pooled/delta fast path through
_POOL_SQL_WHERE and the legacy SQL), memory_levels.deep_recall, and -- added by this job -- the associative-recall
matrix (core/associative_recall.py `_matrix`, which feeds the trail / recall_memory_fragments / recall_block) and
core/evidence_recall.py. The pool-change triggers (trg_pool_chg_upd fires on UPDATE OF temp) keep the cached pool
exact, and init_db's temp resync never touches a 'hidden' row. Hidden rows keep their content, embedding, origin and
every other column byte for byte.

SELECTION (the briefing's rule, exactly): origin='understanding' AND the text after the first '] ' (the
"[Understanding - from ...]" prefix) starts with '{' or '['. `is_dict_repr_body` is the Python twin of the SQL
predicate; scripts/_test_J-3191_dict_repr_marking.py asserts the two agree.

REVERSIBLE: `unmark` puts temp back to what init_db's own resync would have set ('cold' when cold=1, else 'warm') for
exactly the rows that match the same selection and are currently 'hidden'. All 61 were temp='warm', cold=0 in the
pre-wave-C backup, so unmark restores them exactly. Both operations are idempotent. Neither deletes or rewrites content.

Operates on a connection the CALLER opens; this module never opens Du's live DB by itself. The sanctioned runners are
scripts/apply_J-3191_mark_dict_repr_notes.py (mark) and scripts/unmark_dict_repr_notes.py (reverse).
"""
from __future__ import annotations

import hashlib

ORIGIN = "understanding"
HIDDEN = "hidden"

# SQL predicate over memory_fragments (no table alias). instr() is 1-based and 0 when absent, so a prefix-less row is
# tested from its 2nd character, which is what the briefing's `substr(content, instr(content,'] ')+2)` does.
SELECT_PREDICATE = ("origin = 'understanding' "
                    "AND substr(substr(content, instr(content, '] ') + 2), 1, 1) IN ('{', '[')")


def visible_clause(conn, prefix: str = "") -> str:
    """J-3398 (F-4021 follow-up): ` AND <prefix>temp != 'hidden'` when memory_fragments has a `temp` column on `conn`,
    else ''. The one additive guard the remaining direct readers of origin='understanding' (wandering, essay_lesson,
    world_consolidation, memory_edges) append to their SELECTs so the spirit-invisible tier stays invisible to them
    too. Read-only (a PRAGMA); never raises (any failure -> '' = the query is unchanged, the pre-J-3398 behaviour).
    `prefix` is a table alias with its dot, e.g. 'f.'."""
    try:
        if any(r[1] == "temp" for r in conn.execute("PRAGMA table_info(memory_fragments)")):
            return f" AND {prefix}temp != '{HIDDEN}'"
    except Exception:
        pass
    return ""


def is_dict_repr_body(content) -> bool:
    """Python twin of SELECT_PREDICATE's body test (origin is checked by the caller)."""
    s = str(content or "")
    i = s.find("] ")
    start = i + 2 if i >= 0 else 1          # SQL: instr()=i+1 (or 0) -> 1-based start i+3 (or 2) -> 0-based i+2 (or 1)
    return s[start:start + 1] in ("{", "[")


def select_ids(conn) -> list:
    """fragment_ids of every dict-repr understanding note, regardless of current temp, in rowid order."""
    return [r[0] for r in conn.execute(
        f"SELECT fragment_id FROM memory_fragments WHERE {SELECT_PREDICATE} ORDER BY rowid")]


def temp_histogram(conn) -> dict:
    """{(temp, cold): count} over the selection -- recorded before/after by the scripts."""
    return {f"{t}/cold={c}": n for t, c, n in conn.execute(
        f"SELECT temp, cold, COUNT(*) FROM memory_fragments WHERE {SELECT_PREDICATE} GROUP BY temp, cold ORDER BY 1, 2")}


def rows_sha256(conn) -> str:
    """sha256 over (fragment_id, content) of the selected rows in rowid order. Mark/unmark must leave it unchanged."""
    h = hashlib.sha256()
    rows = conn.execute(f"SELECT fragment_id, content FROM memory_fragments WHERE {SELECT_PREDICATE} ORDER BY rowid")
    for fid, content in rows:
        h.update(str(fid).encode("utf-8", "surrogatepass"))
        h.update(b"\x00")
        h.update(str(content).encode("utf-8", "surrogatepass"))
        h.update(b"\x01")
    return h.hexdigest()


def mark(conn) -> int:
    """Set temp='hidden' on every selected row not already hidden. Returns rows changed (0 on a re-run). The caller
    owns the transaction (commit/rollback)."""
    cur = conn.execute(f"UPDATE memory_fragments SET temp = '{HIDDEN}' WHERE {SELECT_PREDICATE} AND temp != '{HIDDEN}'")
    return cur.rowcount or 0


def unmark(conn) -> int:
    """Reverse `mark`: selected rows that are 'hidden' go back to 'cold' (cold=1) or 'warm' (cold=0), the values
    init_db's temp<-cold resync assigns. Returns rows changed. The caller owns the transaction."""
    n = 0
    n += (conn.execute(f"UPDATE memory_fragments SET temp = 'cold' WHERE {SELECT_PREDICATE} "
                       f"AND temp = '{HIDDEN}' AND cold = 1").rowcount or 0)
    n += (conn.execute(f"UPDATE memory_fragments SET temp = 'warm' WHERE {SELECT_PREDICATE} "
                       f"AND temp = '{HIDDEN}' AND cold = 0").rowcount or 0)
    return n
