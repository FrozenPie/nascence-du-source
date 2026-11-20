"""
Nascence — Loop Metabolism, PHASE B logic (2026-06-14).
Both auditors approved Phase B (the deterministic "homeostatic lock"). This module holds the pure
logic; the LIVE call sites (store_fragment dedup, prune-on-sleep, active_imagination guard) are wired
ONLY after the in-vitro proofs pass and the founder gives the go. Nothing here changes behaviour by
being imported — it is called from nowhere live until then.

Four pieces (auditor-ruled):
  1. exact dedup → replay_count    : a verbatim repeat strengthens ONE trace, it does not mint a new
                                     row (Hebbian). Exact-hash only (semantic merge is deferred to
                                     the harvest — Q1).
  2. three-signal importance       : persistence (replay_count) is kept SEPARATE from significance
                                     (importance). Unmodified repetition (zero novelty) drives
                                     importance DOWN, so a jam prunes FIRST (the v1 curve was
                                     inverted — §0.5a). change_score (novelty) is the third signal,
                                     definitionally 0 for an exact dup; it only moves under the
                                     semantic/near-dup case, which is harvest-era work.
  3. active_imagination anti-echo  : the exact guard T2 already uses (rolling buffer, cosine-distance
                                     threshold) — ported so the live 99.9% engine stops re-encoding
                                     itself. Deterministic; reinterprets no content (Q8 = Layer-0
                                     sibling).
  4. active_imagination earned importance : drop the flat 0.8 (which made the most monocultural voice
                                     the most prune-protected); it earns importance via novelty.
"""
from __future__ import annotations

import numpy as np

# Self-voices only — world origins (reading/study/research), keyed `action`, and `lived`
# conversation are NEVER deduped (distinct passages / anchors).
SELF_ORIGINS = ("inner_thought", "subconscious_synthesis", "active_imagination")

# ---- 2. three-signal importance -------------------------------------------------------------
REPLAY_BASE    = 0.60     # importance of a thought seen once
REPLAY_FLOOR   = 0.15     # a pure jam sinks here → prunes first, never immortalised
REPLAY_PENALTY = 0.03     # importance lost per verbatim repeat (zero-novelty repetition)


def replay_importance(replay_count: int) -> float:
    """Significance of an exactly-repeated thought. Persistence (replay_count) is the OTHER, separate
    signal; here repetition without novelty (an exact dup is novelty=0) LOWERS importance so the
    pruning engine targets jams first. n=1→0.60, n=10→0.33, n=55→0.15 (floor)."""
    return max(REPLAY_FLOOR, REPLAY_BASE - REPLAY_PENALTY * max(0, replay_count - 1))


# ---- 3 & 4. active_imagination anti-echo + earned importance --------------------------------
AI_ECHO_THRESHOLD = 0.15  # cosine DISTANCE; echo if a recent contemplation is within this (cos>0.85)
AI_BUFFER_N       = 40     # rolling window — T2's GLOBAL_ECHO buffer size
AI_IMP_LO         = 0.40   # a contemplation that just cleared the echo guard
AI_IMP_HI         = 0.80   # a genuinely novel one earns up to here (no longer a flat default)


def _cos(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b))


def nearest_distance(new_vec: np.ndarray, buffer: list[np.ndarray]) -> float:
    """Smallest cosine distance from new_vec to any vector in the recent buffer (1.0 if empty)."""
    if not buffer:
        return 1.0
    return min(1.0 - _cos(new_vec, v) for v in buffer)


def is_echo(new_vec: np.ndarray, buffer: list[np.ndarray],
            threshold: float = AI_ECHO_THRESHOLD) -> bool:
    """True if this contemplation is within `threshold` cosine-distance of anything recent — i.e. it
    re-encodes a thought already held. The exact guard T2 uses ([subconscious_node 819–827])."""
    return nearest_distance(new_vec, buffer) < threshold


def ai_earned_importance(new_vec: np.ndarray, buffer: list[np.ndarray]) -> float:
    """Importance EARNED by novelty (distance to the nearest recent contemplation), replacing the
    flat 0.8. Just-cleared-the-guard → ~LO; genuinely far from anything recent → up to HI."""
    d = nearest_distance(new_vec, buffer)
    frac = min(1.0, d / 0.5)                      # 0.5 distance saturates to fully novel
    return round(AI_IMP_LO + (AI_IMP_HI - AI_IMP_LO) * frac, 3)


# ---- 1. exact dedup (live store_fragment helper — wired only on founder go) ------------------
# J-2436 / F-3140: the full-origin lookup reads ~237 MB per call (idx_origin visits every inner_thought row and
# its 1.5 KB embedding blob; a MISS, the common case, always pays the full price). A recency-windowed lookup
# through idx_timestamp reads ~12 MB on a miss and ~0 MB on a hit (measured). BUT it is not identical: a verbatim
# repeat of a thought whose last occurrence is older than the window would mint a NEW row instead of bumping the
# old one's replay_count (apply_exact_dedup refreshes timestamp on every hit, so a live jam always stays inside).
# That changes what is stored, so it waits on the founder's call (decide question opened by J-2436):
#   "off"    -- the original query only (pre-J-2436 behaviour).
#   "shadow" -- the original query stays authoritative; the windowed query also runs and both outcomes + costs
#               are logged to data/loop_dedup_window_shadow.jsonl (the evidence the ruling needs). DEFAULT.
#   "live"   -- the windowed query only.
# J-3266 / D-0657 (founder, 2026-11-02): the 7-day window is NOT made live. Instead the exact lookup gets a content
# hash + index (memory_fragments.content_hash, idx_origin_content_hash), two more modes:
#   "hash_shadow" -- the full query stays authoritative; the HASHED query also runs (index probe on
#                    (origin, content_hash), then the real content is compared, so a collision cannot make a false
#                    dup) and both outcomes + costs are logged to data/loop_dedup_hash_shadow.jsonl. DEFAULT. This
#                    replaces the windowed shadow as the thing under observation; it stays here until the hashed
#                    lookup agrees with the full one on every row for >= a week and >= 5,000 calls AND the offline
#                    backfill has finished (`unhashed` False on the rows that count).
#   "hash_live"   -- the hashed query only. NOT the default and not switched on by J-3266: that is step 4 of D-0657,
#                    with a founder note. Safety net built in: while ANY row of this origin still has a NULL
#                    content_hash (backfill unfinished, or a writer that does not stamp it) the hashed query could
#                    miss a real repeat, so it falls back to the full query for that call.
# D-0806 (founder, 2026-11-17, J-4183): step 4 of D-0657 -- the hashed lookup is now authoritative. Evidence F-4858:
# 9,062 shadow calls, 0 disagreements; backfill --verify on the live DB: 186,369 rows, 0 NULL, 0 stale. The NULL-hash
# fallback to the full query stays built in. Revisit on any hash-vs-full disagreement or NULL/stale hash.
DEDUP_WINDOW_MODE = "hash_live"
DEDUP_WINDOW_S = 7 * 86400
_DEDUP_SHADOW_LOG = None   # resolved lazily: <repo>/data/loop_dedup_window_shadow.jsonl
_DEDUP_HASH_SHADOW_LOG = None   # resolved lazily: <repo>/data/loop_dedup_hash_shadow.jsonl


def _dup_full(conn, origin: str, content: str):
    return conn.execute(
        "SELECT fragment_id, replay_count FROM memory_fragments "
        "WHERE origin=? AND content=? LIMIT 1", (origin, content)).fetchone()


def _dup_windowed(conn, origin: str, content: str, since: float):
    # unary plus: keep the planner OFF idx_origin so the timestamp range bounds the walk
    return conn.execute(
        "SELECT fragment_id, replay_count FROM memory_fragments "
        "WHERE timestamp > ? AND +origin=? AND content=? LIMIT 1", (since, origin, content)).fetchone()


def _dup_hashed(conn, origin: str, content: str):
    """J-3266 / D-0657: index probe on (origin, content_hash), then CONFIRM the real content on every candidate so a
    hash collision can never yield a false duplicate. Returns (row_or_None, n_candidates). Lowest rowid wins when
    several identical rows exist (the order the index gives), the same row the full lookup's idx_origin walk meets
    first. Raises if the column/index is missing (caller treats that as 'hashed lookup unavailable')."""
    from core.memory.content_hash import content_hash
    h = content_hash(content)
    if h is None:
        return None, 0
    rows = conn.execute(
        "SELECT fragment_id, replay_count, content FROM memory_fragments "
        "WHERE origin=? AND content_hash=?", (origin, h)).fetchall()
    for r in rows:
        if r["content"] == content:
            return r, len(rows)
    return None, len(rows)


def _has_unhashed(conn, origin: str) -> bool:
    """True if any row of this origin has no content_hash yet (NULLs sort first in idx_origin_content_hash, so this is
    one index seek). While True, a hashed MISS is not proof of 'no duplicate'."""
    return conn.execute("SELECT 1 FROM memory_fragments WHERE origin=? AND content_hash IS NULL LIMIT 1",
                        (origin,)).fetchone() is not None


def _log_dedup_hash_shadow(origin: str, full, hashed, n_cand: int, t_full: float, t_hash: float,
                           unhashed, err, now: float) -> None:
    """Observe-only. Never raises, never affects the write path. One row per find_exact_dup call.
    `agree`      : same outcome AND (if both hit) the same fragment_id  -- the strict gate.
    `hit_agree`  : same hit/miss outcome only (two identical rows may legitimately differ in which one is met first).
    `unhashed`   : this origin still had NULL-hash rows when the call ran; a disagreement with unhashed=True is the
                   unfinished backfill, not a lookup defect. `error` set => the hashed lookup raised (e.g. column absent)."""
    global _DEDUP_HASH_SHADOW_LOG
    try:
        import json, threading
        from pathlib import Path
        from core import profile   # the write fence (D-0179); imports nothing from core at module level
        if _DEDUP_HASH_SHADOW_LOG is None:
            _DEDUP_HASH_SHADOW_LOG = Path(__file__).parent.parent / "data" / "loop_dedup_hash_shadow.jsonl"
        log = profile.guard_path(_DEDUP_HASH_SHADOW_LOG)
        hit_agree = (full is None) == (hashed is None) and err is None
        rec = {"ts": now, "origin": origin, "algo": "blake2b-128",
               "full_hit": full is not None, "hash_hit": hashed is not None,
               "hit_agree": hit_agree,
               "agree": hit_agree and (full is None or full[0] == hashed[0]),
               "candidates": n_cand, "unhashed": unhashed,
               "full_ms": round(t_full * 1000, 2), "hash_ms": round(t_hash * 1000, 2)}
        if err is not None:
            rec["error"] = err
        lock = globals().setdefault("_DEDUP_SHADOW_LOCK", threading.Lock())
        with lock, open(log, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
    except Exception:
        pass


def _log_dedup_shadow(conn, origin: str, full, win, t_full: float, t_win: float, now: float) -> None:
    """Observe-only. Never raises, never affects the write path."""
    global _DEDUP_SHADOW_LOG
    try:
        import json, threading
        from pathlib import Path
        from core import profile   # the write fence (D-0179); imports nothing from core at module level
        if _DEDUP_SHADOW_LOG is None:
            _DEDUP_SHADOW_LOG = Path(__file__).parent.parent / "data" / "loop_dedup_window_shadow.jsonl"
        log = profile.guard_path(_DEDUP_SHADOW_LOG)
        rec = {"ts": now, "origin": origin, "window_s": DEDUP_WINDOW_S,
               "full_hit": full is not None, "window_hit": win is not None,
               "agree": (full is None) == (win is None) and (full is None or full[0] == win[0]),
               "full_ms": round(t_full * 1000, 2), "window_ms": round(t_win * 1000, 2)}
        if full is not None and win is None:   # the case the window would change: how old was the match?
            try:
                ts_row = conn.execute("SELECT timestamp FROM memory_fragments WHERE fragment_id=?",
                                      (full[0],)).fetchone()
                if ts_row is not None and ts_row[0] is not None:
                    rec["missed_age_s"] = round(now - float(ts_row[0]), 1)
                rec["missed_replay_count"] = full[1] or 0
            except Exception:
                pass
        lock = globals().setdefault("_DEDUP_SHADOW_LOCK", threading.Lock())
        with lock, open(log, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
    except Exception:
        pass


def _hash_live_blocked(conn, origin: str) -> bool:
    """hash_live safety net: True (=> use the full lookup this call) while the hashed lookup cannot be trusted --
    the column/index is absent, or this origin still has NULL-hash rows. Fail-closed on any error."""
    try:
        return _has_unhashed(conn, origin)
    except Exception:
        return True


def find_exact_dup(conn, origin: str, content: str, now: float | None = None):
    """Return (fragment_id, current_replay_count) of an existing exact-content row for this
    self-origin, or None. Caller (store_fragment) increments + recomputes importance instead of
    inserting. Exact-hash equality only — semantic merge is the harvest's job.
    J-2436: DEDUP_WINDOW_MODE selects the lookup (see above); the default "shadow" returns exactly what
    the original query returns."""
    import time as _t
    mode = DEDUP_WINDOW_MODE
    now = _t.time() if now is None else now
    if mode == "live":
        row = _dup_windowed(conn, origin, content, now - DEDUP_WINDOW_S)
    elif mode == "hash_live" and not _hash_live_blocked(conn, origin):
        try:
            row, _n = _dup_hashed(conn, origin, content)
        except Exception:
            row = _dup_full(conn, origin, content)   # fail closed to the authoritative lookup
    else:
        t0 = _t.perf_counter()
        row = _dup_full(conn, origin, content)
        if mode == "hash_shadow":
            t1 = _t.perf_counter()
            hrow, n_cand, err = None, 0, None
            try:
                hrow, n_cand = _dup_hashed(conn, origin, content)
            except Exception as exc:
                err = f"{type(exc).__name__}: {exc}"[:200]
            t2 = _t.perf_counter()
            try:
                unhashed = _has_unhashed(conn, origin)
            except Exception:
                unhashed = None
            _log_dedup_hash_shadow(origin, row, hrow, n_cand, t1 - t0, t2 - t1, unhashed, err, now)
        elif mode == "shadow":
            t1 = _t.perf_counter()
            try:
                win = _dup_windowed(conn, origin, content, now - DEDUP_WINDOW_S)
            except Exception:
                win = None
            t2 = _t.perf_counter()
            _log_dedup_shadow(conn, origin, row, win, t1 - t0, t2 - t1, now)
    if not row:
        return None
    rc = row["replay_count"] if "replay_count" in row.keys() else 0
    return (row["fragment_id"], rc or 0)


def apply_exact_dedup(conn, fragment_id: str, new_replay_count: int, ts: float) -> None:
    """A verbatim repeat: bump replay_count + timestamp (it is active now), and recompute importance
    via the declining curve so the jam prunes first. Does NOT insert a new row."""
    conn.execute(
        "UPDATE memory_fragments SET replay_count=?, importance=?, timestamp=? WHERE fragment_id=?",
        (new_replay_count, replay_importance(new_replay_count), ts, fragment_id))
