"""
Nascence — Dream Probe: delta-association for the CURRENT dream engine (Phase 1 instrumentation,
2026-09-17, J-1057, docs/staged/dream_overhaul.md sec 4 / sec 7 Phase 1 row).

Defines "delta-association" for the store that exists TODAY: for a pair of fragment ids (A, B), what
does the memory graph already know about the two of them TOGETHER —
  {edge_exists, edge_types, rank_of_B_in_recall_trail_edge_aware(seed=A), cosine}.
None of this is new measurement machinery: every number here already exists elsewhere in the codebase
(core/memory_edges.py's own typed-edge table; core/associative_recall.py's own edge-aware trail;
core/memory/store.py's own embedding cosine). This module only reads them, PAIRED, and logs the
pairing — read-only against memory/edges, never a write to memory, edges, tensions, frontier, or
climate. The one file it writes is its own: data/logs/dream_assoc_probe.jsonl.

Why cosine is the CONTROL, not the measure (plan sec 4): embeddings never change once written
(core/memory/store._embed runs once at store_fragment() time; associative_recall._refresh's cached
matrix re-reads the SAME stored vectors on every rebuild — nothing in this codebase ever re-embeds a
fragment in place). So cosine(A, B) computed "before" a dream and "after" it, on the SAME pair, must be
numerically identical up to float reproducibility. If a before/after read (scripts/dream_assoc_after.py)
ever shows cosine actually drifting on the same pair, that is a bug in the measurement pipeline itself
(the wrong fragment id, a stale cache, a different embedding model), not a real change in association —
this is exactly the honest "seed / generated / after cannot be separated from the logs" failure mode
the plan's own Phase 1 kill condition names.

rank_of_B_in_recall_trail_edge_aware(seed=A) is the one number that CAN legitimately move between
"before" and "after": it depends on what has surfaced, co-recalled, or been edge-linked to A in the
meantime (a waking thought, a later dream, a new memory_edges row) — never on A's or B's own embedding.
That is the real day-after question this plan asks (sec 0): did the day carry the dormant thing back
into reach? A rank that improves (drops toward 0) or a None that becomes a real rank is the honest
signal; cosine sitting still beside it is what proves the mover was recall, not the vectors.

No dormant-node selection, no seeding decision, no writeback of any kind lives here — this module is
read + log only, callable from any context (a live night, an in-vitro test, a by-hand re-probe script)
without side effects on the entity itself.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from pathlib import Path

logger = logging.getLogger("nascence.dream_probe")

_PROBE_LOG = Path(__file__).parent.parent / "data" / "logs" / "dream_assoc_probe.jsonl"

# The M2 trail mode used for the rank read (associative_recall._M2_MODES[0] — "task" is the plan's own
# default reading mode; no new tuning surface introduced here). recall_trail_edge_aware's own three
# modes differ only in how they WEIGHT edge-reached candidates against the greedy walk; "task" is the
# least relational-biased of the three, matching a probe that should not itself lean toward any one of
# the plan's later coupling questions.
_TRAIL_MODE = "task"

# J-2111 / F-2748: nodes/dream_node.py runs log_seed_pairs in a worker thread (core.idle_offloop.off_loop)
# so the ~4-7 s probe no longer holds the event loop. Kill switch: False = the old synchronous call on the loop.
DREAM_PROBE_OFFLOOP = True

# serialises appends to _PROBE_LOG between worker threads of this process (scripts/dream_assoc_after.py is a
# separate process doing small O_APPEND line writes, same as before).
_PROBE_LOG_LOCK = threading.Lock()


def _fragment_vec(fragment_id: str, conn=None):
    """The stored embedding for a fragment id as a numpy array, or None if the fragment/embedding is
    missing. Read-only; opens its own connection unless `conn` is given (caller keeps it open)."""
    if not fragment_id:
        return None
    try:
        from core.memory.store import _connect, _blob_to_vec
        own = conn is None
        if own:
            conn = _connect()
        try:
            row = conn.execute(
                "SELECT embedding FROM memory_fragments WHERE fragment_id = ?", (fragment_id,)
            ).fetchone()
        finally:
            if own:
                conn.close()
        if row is None or row["embedding"] is None:
            return None
        return _blob_to_vec(row["embedding"])
    except Exception as exc:
        logger.debug("[dream_probe] fragment_vec(%s) failed: %s", fragment_id, exc)
        return None


def _edges_between(fragment_a: str, fragment_b: str) -> dict:
    """{edge_exists, edge_types} for this fragment pair, either direction, kind='fragment' on both
    sides. Reads core/memory_edges.py's own table directly (its own `_connect()`, same convention every
    other memory_edges reader in this codebase uses) — read-only, no write."""
    try:
        from core.memory_edges import _connect as _medges_connect
        conn = _medges_connect()
        try:
            rows = conn.execute(
                "SELECT DISTINCT edge_type FROM memory_edges WHERE "
                "(src_kind='fragment' AND src_id=? AND dst_kind='fragment' AND dst_id=?) OR "
                "(src_kind='fragment' AND src_id=? AND dst_kind='fragment' AND dst_id=?)",
                (fragment_a, fragment_b, fragment_b, fragment_a),
            ).fetchall()
        finally:
            conn.close()
        types = sorted(r[0] for r in rows)
        return {"edge_exists": bool(types), "edge_types": types}
    except Exception as exc:
        logger.debug("[dream_probe] edges_between(%s, %s) failed: %s", fragment_a, fragment_b, exc)
        return {"edge_exists": False, "edge_types": []}


def _rank_in_trail(fragment_a: str, fragment_b: str) -> "int | None":
    """B's 0-based rank (strongest-first) in recall_trail_edge_aware(seed=A)'s output, or None if A has
    no stored embedding, the trail is empty, or B never surfaces in it. Reuses
    core/associative_recall.py's own cached embedding matrix and its own greedy-walk + edge-aware-hop
    functions UNMODIFIED (recall_trail, then recall_trail_edge_aware with base=that trail) — no new
    embedding call, no write, no new trail algorithm."""
    try:
        from core import associative_recall as _ar
        av = _fragment_vec(fragment_a)
        if av is None:
            return None
        base = _ar.recall_trail(av)
        if not base:
            return None
        trail = _ar.recall_trail_edge_aware(av, mode=_TRAIL_MODE, base=base)
        for rank, t in enumerate(trail):
            if t.get("fragment_id") == fragment_b:
                return rank
        return None
    except Exception as exc:
        logger.debug("[dream_probe] rank_in_trail(%s, %s) failed: %s", fragment_a, fragment_b, exc)
        return None


def probe_pair(fragment_a: str, fragment_b: str) -> dict:
    """{edge_exists, edge_types, rank_of_B_in_recall_trail_edge_aware, cosine} for one fragment pair
    (module docstring has the full reasoning for each field). Read-only against the existing
    memory/edges store. Fail-open per field — one field's failure (e.g. a missing embedding) never
    blanks the others; never raises past this function."""
    out = {"edge_exists": False, "edge_types": [], "rank_of_B_in_recall_trail_edge_aware": None,
           "cosine": None}
    try:
        out.update(_edges_between(fragment_a, fragment_b))
    except Exception as exc:
        logger.debug("[dream_probe] probe_pair edges step failed: %s", exc)
    try:
        out["rank_of_B_in_recall_trail_edge_aware"] = _rank_in_trail(fragment_a, fragment_b)
    except Exception as exc:
        logger.debug("[dream_probe] probe_pair rank step failed: %s", exc)
    try:
        from core.memory.store import _connect, _cosine
        conn = _connect()
        try:
            av = _fragment_vec(fragment_a, conn=conn)
            bv = _fragment_vec(fragment_b, conn=conn)
        finally:
            conn.close()
        if av is not None and bv is not None:
            out["cosine"] = round(_cosine(av, bv), 4)
    except Exception as exc:
        logger.debug("[dream_probe] probe_pair cosine step failed: %s", exc)
    return out


def log_seed_pairs(dream_id: str, fragment_ids: list, phase: str = "before") -> int:
    """Probe every unique unordered pair among `fragment_ids` and append one row per pair to
    data/logs/dream_assoc_probe.jsonl: {ts, dream_id, phase, fragment_a, fragment_b, edge_exists,
    edge_types, rank_of_B_in_recall_trail_edge_aware, cosine}. `phase="before"` is this module's own
    seed-time call (nodes/dream_node.py's synthesise(), at seed capture — not gated on commit=True: a
    read-only probe plus a write to its OWN log is not a memory-store write); `phase="after"` is
    scripts/dream_assoc_after.py's by-hand (or later waking-side) re-probe of the SAME pairs 24-48h on.
    Returns the number of rows written (0 if fewer than 2 distinct ids). Fail-open; never raises."""
    ids = list(dict.fromkeys(fid for fid in (fragment_ids or []) if fid))
    if len(ids) < 2:
        return 0
    n = 0
    try:
        rows = []
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                a, b = ids[i], ids[j]
                result = probe_pair(a, b)
                rows.append({"ts": round(time.time(), 1), "dream_id": dream_id, "phase": phase,
                            "fragment_a": a, "fragment_b": b, **result})
        _PROBE_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_PROBE_LOG, "a", encoding="utf-8") as f:
            for rec in rows:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n += 1
    except Exception as exc:
        logger.debug("[dream_probe] log_seed_pairs failed (non-fatal): %s", exc)
    return n
