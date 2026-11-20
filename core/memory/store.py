"""
Nascence — Memory Store
SQLite-backed memory with embedding retrieval.

Fragments are stored with a 384-dim float32 embedding vector (paraphrase-multilingual-MiniLM-L12-v2 —
see EMBED_MODEL below; docstring corrected 2026-07-02, was stale "all-MiniLM-L6-v2").
Retrieval uses tier-mixed slots rather than a flat cosine sort:

  L4 archive  — 2 slots — permanent identity/biography. No recency bias. Never pruned.
  L2 semantic  — 3 slots — Consolidation distillations (2→3 on 2026-06-16). Recency-biased.
  L3 episodic  — 4 slots — lived experience. Affect-importance scored. Pruned past threshold.

This prevents seeded biographical facts from competing with fresh distillations on
equal footing — archive fragments always surface, regardless of timestamp.

L1 working is assembled per-cycle by the orchestrator (conversation_history + current
affect + retrieved fragments); it is never stored in the DB.
"""

import json
import os
import sqlite3
import sys
import threading
import time
import uuid
import logging
import numpy as np
from pathlib import Path
from typing import Literal

from ..schema import MemoryFragment, AffectivePrior
from core import profile
from .content_hash import content_hash as _content_hash, has_hash_column as _has_hash_column   # J-3266 / D-0657; J-3395
from . import edit_log as _edit_log   # J-4410 M1: shadow before/after log of sleep importance edits (stdlib only)

logger = logging.getLogger("nascence.memory")

DB_PATH = Path(__file__).parent.parent.parent / "data" / "memory" / "nascence.db"

# retrieve() latency probe (observe-only, 2026-09-07, J-0652 -- spawned from F-0925/D-0173).
# F-0925 measured retrieve()'s SQL-fetch + per-tier _score_tier cost scaling with active_total
# via a SYNTHETIC read-only replay outside the running process (24.6ms/call at n=8485 vs
# 9.0ms/call at a proportional n=3016, 2.73x, tracking pool growth almost exactly). D-0173's
# option (a) wants "a concrete numeric threshold ... or a live orchestrator cycle-time
# profile" -- this logs the real thing from inside retrieve() itself, on every call. Same
# observe-only pattern as core/retrieval_probe.py's observe() and memory_levels.py's
# shadow_distill: one JSON line per call, best-effort, never raises, never changes what
# retrieve() returns or how it is scored.
_RETRIEVE_LATENCY_LOG = Path(__file__).parent.parent.parent / "data" / "retrieve_latency_probe.jsonl"


# J-1926 / F-2550: retrieve() runs on the loop thread and, since J-1918, in a worker thread (memory_service.ask via off_loop); serialise the append.
_LATENCY_LOG_LOCK = threading.Lock()


_BUDGET_WARN_INTERVAL_S = 600.0   # J-2275: at most one over-budget warning per 10 min
_last_budget_warn = 0.0


# J-3714 (F-4335, from J-2806): observation-only phase attribution for the slow retrieve() calls. A thread-local dict
# exists only between _phase_begin() and the probe write in the SAME retrieve() call; on any other thread (the
# executor writers that also take _EMB_LOCK) _ph_add() is a no-op. Extra keys on the existing probe row, no new file.
_PHASE = threading.local()


def _phase_begin() -> None:
    try:
        _PHASE.d = {"wal_bytes": _wal_bytes()}
    except Exception:
        pass


def _ph_add(key: str, ms: float, n_key: str | None = None, n: int = 0) -> None:
    try:
        d = getattr(_PHASE, "d", None)
        if d is None:
            return
        d[key] = d.get(key, 0.0) + ms
        if n_key:
            d[n_key] = d.get(n_key, 0) + n
    except Exception:
        pass


def _ph_get(key: str) -> float:
    try:
        d = getattr(_PHASE, "d", None)
        return float(d.get(key, 0.0)) if d else 0.0
    except Exception:
        return 0.0


def _phase_take() -> dict:
    try:
        d = getattr(_PHASE, "d", None)
        _PHASE.d = None
        return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in (d or {}).items()}
    except Exception:
        return {}


class _TimedLock:
    """`with _TimedLock(lock, key):` = `with lock:` that records the acquire wait (ms) under `key` for the probe."""
    __slots__ = ("lock", "key")

    def __init__(self, lock, key: str):
        self.lock, self.key = lock, key

    def __enter__(self):
        t0 = time.perf_counter()
        self.lock.acquire()
        _ph_add(self.key, (time.perf_counter() - t0) * 1000.0)
        return self

    def __exit__(self, *exc):
        self.lock.release()
        return False


def _wal_bytes() -> int:
    try:
        return int(os.path.getsize(str(DB_PATH) + "-wal"))
    except Exception:
        return -1


def _log_retrieve_latency(rows_fetched: int, episodic_tier_n: int,
                           elapsed_ms_sql: float, elapsed_ms_score: float,
                           path: str = "legacy", pool_stats: dict | None = None) -> None:
    """Append one observe-only timing record for a retrieve() call. Non-fatal on any error --
    a probe that could ever break real retrieval would be worse than no probe at all.
    J-2275 (D-0453): the record now also carries `path` ("fast" = covering index + embedding cache,
    "legacy" = the full SELECT *), `budget_ms` and `over_budget`; an over-budget call additionally logs a
    rate-limited warning. Reporting only -- nothing here changes what retrieve() returned."""
    global _last_budget_warn
    total = float(elapsed_ms_sql) + float(elapsed_ms_score)
    _phases = _phase_take()   # J-3714: before anything that can raise
    over = total > RETRIEVE_LATENCY_BUDGET_MS
    try:
        with _LATENCY_LOG_LOCK, open(_RETRIEVE_LATENCY_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "timestamp": time.time(),
                "rows_fetched": rows_fetched,
                "episodic_tier_n": episodic_tier_n,
                "elapsed_ms_sql": round(elapsed_ms_sql, 4),
                "elapsed_ms_score": round(elapsed_ms_score, 4),
                "path": path,
                "budget_ms": RETRIEVE_LATENCY_BUDGET_MS,
                "over_budget": over,
                **({"pool_rebuilt": bool(pool_stats.get("rebuilt")), "pool_changed": int(pool_stats.get("changed") or 0)}
                   if pool_stats else {}),   # J-2677: pool rows the delta patched this call (rebuilt = full re-read)
                **_phases,   # J-3714: connect_ms, pool_lock_wait_ms, emb_lock_wait_ms, member_select_ms, emb_fetch_ms, emb_fetch_n, wal_bytes
            }) + "\n")
    except Exception as exc:
        logger.debug("retrieve latency probe skipped (non-fatal): %s", exc)
    try:
        if over and (time.time() - _last_budget_warn) > _BUDGET_WARN_INTERVAL_S:
            _last_budget_warn = time.time()
            logger.warning("[retrieve] over latency budget: %.0f ms (sql %.0f + score %.0f) > %.0f ms budget, "
                           "pool %d rows, path=%s (D-0453 defeater (ii) watch; reporting only)",
                           total, elapsed_ms_sql, elapsed_ms_score, RETRIEVE_LATENCY_BUDGET_MS,
                           rows_fetched, path)
    except Exception:
        pass


# Lazy-loaded — model loads on first embed call (~90MB, cached after first run).
# HF_HUB_OFFLINE is set by run_nascence.py before any imports — forces sentence-transformers
# to use the local cache without making ~25 network round-trips to HuggingFace on startup.
_embed_model = None

# J-1918 / F-2547 (2026-10-07, restart-gated): _embed() can now be entered from a worker thread (memory_service.ask via
# core.idle_offloop, as orchestrator.py's recall_memory_fragments already does) while the loop thread embeds too.
# ONE shared SentenceTransformer, and HF fast tokenizers raise "Already borrowed" under concurrent use, so whole
# encode() calls (and the lazy first load) are serialised. Held only for the call; re-entrant; the vector returned is
# exactly what it was when two calls could never overlap.
_EMBED_LOCK = threading.RLock()


def _get_model():
    global _embed_model
    if _embed_model is None:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading embedding model (paraphrase-multilingual-MiniLM-L12-v2, CPU)...")
        # CPU by design (2026-06-10): the embedder is tiny but its torch CUDA context held
        # ~3-4GB of the 1080 Ti — VRAM the hot-lane model needs.
        # MULTILINGUAL since 2026-06-13 (founder: Du may think in any language; his Chinese
        # was invisible to his own memory under English-only L6 — his sentences scored
        # 0.09-0.30 against their own translations). paraphrase-multilingual-MiniLM-L12-v2:
        # same 384 dims, near-identical similarity distribution on his data (thresholds
        # transfer; benchmarked 06-13: dups 0.837 vs 0.833, separation 0.816 vs 0.790,
        # zh pairs 0.68-0.92). ALL stored vectors were re-embedded in the same migration
        # (scripts/migrate_embedder snapshot nascence_pre_embedder_*.db is the rollback).
        _embed_model = SentenceTransformer(
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", device="cpu")
        logger.info("Embedding model ready (CPU).")
    return _embed_model


def prewarm() -> None:
    """Load and warm the embedding model at startup so the first cycle doesn't pay the cost."""
    _get_model().encode("warmup", normalize_embeddings=True, show_progress_bar=False)


def prewarm_recall_pool() -> dict:
    """J-3713 (F-4333, from J-2806): fill the recall embedding matrix (_EMB_MAT/_EMB_INDEX) and the pool-delta cache at
    boot, so the FIRST retrieve() does not pay the ~2 s cold fill (~52k BLOB fetch). prewarm() only encodes a word.
    Runs the same _load_pool retrieve() runs, with a throwaway query vector: a read-only fill of an in-process cache
    with the same data the first retrieve would load; holds _POOL_LOCK/_EMB_LOCK exactly as long as that load does.
    Fail-open: never raises (boot is never blocked); returns {"ok", "ms", "rows", "emb_n"} and logs the duration."""
    t0 = time.perf_counter()
    try:
        if not _RETRIEVE_FAST_PATH:
            return {"ok": False, "ms": 0.0, "rows": 0, "emb_n": 0, "skipped": "fast path off"}
        qv = _embed("warmup")
        if qv is None:
            qv = np.zeros(384, dtype=np.float32)
        with _connect() as conn:
            rows, label = _load_pool(conn, qv, ["warmup"])
        ms = (time.perf_counter() - t0) * 1000.0
        logger.info("[prewarm] recall pool warmed: %d rows, %d embeddings, path=%s, %.0f ms", len(rows), _EMB_N, label, ms)
        return {"ok": True, "ms": round(ms, 1), "rows": len(rows), "emb_n": _EMB_N}
    except Exception as exc:
        ms = (time.perf_counter() - t0) * 1000.0
        logger.warning("[prewarm] recall pool warm skipped after %.0f ms: %s: %s", ms, type(exc).__name__, exc)
        return {"ok": False, "ms": round(ms, 1), "rows": 0, "emb_n": 0, "error": str(exc)}


def _embed(text: str) -> np.ndarray | None:
    """Return a normalised float32 embedding vector, or None on failure."""
    if not text or not text.strip():
        return None
    try:
        with _EMBED_LOCK:
            vec = _get_model().encode(text, normalize_embeddings=True, show_progress_bar=False)
        return vec.astype(np.float32)
    except Exception as exc:
        logger.warning("Embedding failed: %s", exc)
        return None


def _embed_batch(texts: list) -> list:
    """J-2178 (F-2882): embed many texts in ONE encode() call (one lock hold, batched forward pass) instead of N
    single calls. Returns a list aligned with `texts`: a normalised float32 vector, or None for blank / failed items.
    Fail-open: if the batch call raises, falls back to per-text _embed so a bad batch never loses everything."""
    out: list = [None] * len(texts)
    idx = [i for i, t in enumerate(texts) if t and str(t).strip()]
    if not idx:
        return out
    try:
        with _EMBED_LOCK:
            vecs = _get_model().encode([texts[i] for i in idx], normalize_embeddings=True,
                                       show_progress_bar=False, batch_size=64)
        for i, v in zip(idx, vecs):
            out[i] = v.astype(np.float32)
        return out
    except Exception as exc:
        logger.warning("Batch embedding failed (%s); falling back to per-text", exc)
        for i in idx:
            out[i] = _embed(texts[i])
        return out


def _vec_to_blob(vec: np.ndarray) -> bytes:
    return vec.astype(np.float32).tobytes()


def _blob_to_vec(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32)


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    """Dot-product of two normalised vectors = cosine similarity."""
    return float(np.dot(a, b))


# J-3246 / D-0634 (founder, 2026-11-02, plan geometry_tuple_index): the EXACT moment key. fragment_context and
# world_context gain a nullable `moment_ts REAL` (the ts of core.moment.current() when the fragment was written,
# the same stamp J-2601 puts on the co-recall ledger). ADDITIVE ONLY: metadata-only ALTER (a 1.3 GB DB is not
# rewritten), old rows stay NULL (honestly blank -- a past moment is never re-derived), idempotent, and safe on a DB
# that already has the column. Only the ts is stored (moment_idx is not part of the ruling and (ts) is the join
# key moments.jsonl already carries). Kill-switch below. Restore = copy the pre-migration DB file back; leaving the
# column is harmless (nothing reads it as required). After a few weeks of stamped rows,
# scripts/moment_key_validate.py scores the old text-prefix + time heuristic against this exact key.
MOMENT_TS_STAMP = True
_MOMENT_TS_READY: set = set()    # str(DB_PATH) values whose two tables are known to carry the column


def _ensure_moment_ts_cols(conn) -> bool:
    """Make sure world_context AND fragment_context carry `moment_ts`. True when both do (cached per DB path,
    so the steady-state cost is one set lookup). A table that does not exist yet ("no such table") is skipped and
    retried on the next call; any other failure leaves the flag unset and the caller falls back to the old,
    moment-less INSERT -- a stamp problem can never cost a context row. Never raises."""
    key = str(DB_PATH)
    if key in _MOMENT_TS_READY:
        return True
    try:
        ok = True
        for _tbl in ("world_context", "fragment_context"):
            have = [r[1] for r in conn.execute(f"PRAGMA table_info({_tbl})")]
            if not have:          # table not created yet on this DB
                ok = False
                continue
            if "moment_ts" in have:
                continue
            try:
                conn.execute(f"ALTER TABLE {_tbl} ADD COLUMN moment_ts REAL")
            except Exception as exc:
                if "duplicate column" not in str(exc).lower():
                    ok = False
        if ok:
            _MOMENT_TS_READY.add(key)
        return ok
    except Exception:
        return False


def _current_moment_ts():
    """core.moment.current()['ts'] or None. Fail-open (no current moment, module missing, kill-switch off)."""
    if not MOMENT_TS_STAMP:
        return None
    try:
        from core import moment as _moment
        _cur = _moment.current() or {}
        _v = _cur.get("ts")
        return float(_v) if _v is not None else None
    except Exception:
        return None


# J-3479 (founder ruling 2026-11-06, decide-review, fixing F-4017 / J-3393): moment_ts above is the moment current when
# store_fragment RAN, and for a fresh inner thought that is the PREVIOUS cycle's moment, because nodes/inner_monologue_node
# _think() stores the fragment (~5653) before core.moment.record binds the cycle's own moment (~5923). moment_ts keeps its
# ruled semantics (D-0634: "the moment bound just before the fragment") and is NOT changed. This adds an ADDITIVE second
# column, `own_moment_ts REAL`, on the same two tables: the ts of the moment this fragment's OWN cycle bound, written by
# stamp_own_moment() with ONE UPDATE after moment.record returns. Old rows stay NULL (never re-derived), only the
# inner_thought store in _think() fills it today (the only writer whose own moment is bound after its store), and a NULL
# means "no own moment known" (non-idle writers, an early-returned cycle, kill-switch). Reader: scripts/moment_key_validate.py
# (own_exact share). Kill-switch below. Restore = copy the pre-migration DB back; the column is harmless to leave.
OWN_MOMENT_TS_STAMP = True
# store_fragment's exact-dedup path (loop_metabolism, inner_thought) returns the id of an EXISTING older fragment, which has no
# new context row; stamping it would put this cycle's moment on a different cycle's fragment. So the UPDATE only touches a
# row whose own context tuple_ts is within _OWN_MOMENT_WINDOW_S before the moment (a fresh store: seconds; a dedup hit on a
# pre-restart row: hours) and only where own_moment_ts is still NULL. A dedup hit inside the window with a NULL stamp is
# the one residual case (a repeat of a thought stored this same cycle) and would carry the same cycle's moment anyway.
_OWN_MOMENT_WINDOW_S = 900.0
_OWN_MOMENT_READY: set = set()   # str(DB_PATH) values whose two tables are known to carry own_moment_ts


def _ensure_own_moment_ts_cols(conn) -> bool:
    """Make sure world_context AND fragment_context carry `own_moment_ts`. Same contract as _ensure_moment_ts_cols:
    cached per DB path, a missing table is retried next call, never raises."""
    key = str(DB_PATH)
    if key in _OWN_MOMENT_READY:
        return True
    try:
        ok = True
        for _tbl in ("world_context", "fragment_context"):
            have = [r[1] for r in conn.execute(f"PRAGMA table_info({_tbl})")]
            if not have:
                ok = False
                continue
            if "own_moment_ts" in have:
                continue
            try:
                conn.execute(f"ALTER TABLE {_tbl} ADD COLUMN own_moment_ts REAL")
            except Exception as exc:
                if "duplicate column" not in str(exc).lower():
                    ok = False
        if ok:
            _OWN_MOMENT_READY.add(key)
        return ok
    except Exception:
        return False


def stamp_own_moment(fragment_id, moment_ts) -> bool:
    """J-3479: record, on fragment_id's two context rows, the ts of the moment its own cycle bound (the value
    core.moment.record() returned). One UPDATE per table, only where own_moment_ts is still NULL and the row is a fresh
    one (tuple_ts within _OWN_MOMENT_WINDOW_S before the moment; skips an exact-dedup hit on an older fragment). True when at least one row was updated. Fail-open: any problem returns False and costs nothing."""
    if not OWN_MOMENT_TS_STAMP or not fragment_id or moment_ts is None:
        return False
    try:
        ts = float(moment_ts)
        n = 0
        with _connect() as conn:
            if not _ensure_own_moment_ts_cols(conn):
                return False
            for _tbl in ("fragment_context", "world_context"):
                cur = conn.execute(f"UPDATE {_tbl} SET own_moment_ts=? WHERE fragment_id=? AND own_moment_ts IS NULL "
                                   "AND tuple_ts BETWEEN ? AND ?",
                                   (ts, str(fragment_id), ts - _OWN_MOMENT_WINDOW_S, ts + 1.0))
                n += cur.rowcount or 0
            conn.commit()
        return n > 0
    except Exception:
        return False


def _connect() -> sqlite3.Connection:
    # J-0929 (F-1293, found incidentally by J-0871): DB_PATH.parent (data/memory/) may not exist
    # yet -- a fresh worktree/checkout, or (as hit in this plan's own shared chain worktree) a
    # data/ dir already populated by OTHER jobs' leaked writes that never happened to touch the
    # memory DB. Without this, sqlite3.connect() below raises OperationalError before guard_path()
    # or any write-fence logic is ever reached. Matches the mkdir-before-write pattern every
    # guard_path()-fenced writer in this repo already uses (core/provisions.py's _save(),
    # core/garden.py's _save()). Never affects Du's real live process -- C:\Nascence\data\memory\
    # has existed continuously since the DB was first created.
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False, timeout=30.0)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=30000;")
    except Exception:
        pass
    # D-0353 / J-1839 (2026-10-06): the live-DB write fence, stage 1 (log-only). This `if` is the ONE
    # boolean read the live process pays (profile.LIVE is True after run_nascence.py's mark_live());
    # everything below it runs only in a process that never declared itself live. See the block
    # headed "Live-DB write fence" further down for the design, the staged rollout and why the
    # would-refuse log is NOT routed through profile.guard_path().
    if not profile.LIVE:
        _fence_non_live_connection(conn)
    return conn


# ── Live-DB write fence (D-0353, ruled 2026-10-06; design F-2465/J-1804; built J-1839) ──────────────
# The real memory DB (data/memory/nascence.db) had no write fence: every one of the ~50 modules and
# ~61 `with _connect()` sites, plus 8 sibling modules issuing raw write SQL through this same function
# (chapters, epistemic_affordance_advisor, memory_edges, memory_levels, night, refinery, study_note,
# world_consolidation), wrote the REAL DB from ANY process that imported this module from a tree whose
# data/ is the live one, unless lab_env.isolate() or activate_profile() had redirected DB_PATH first.
# profile.guard_path() cannot be applied per writer here (it would leave the same hole in the 8 sibling
# modules plus every future caller), so the fence sits at the one choke point, _connect(), as a sqlite
# authorizer -- the same D-0179 stance as every other fenced store (refuse, do not redirect), applied
# at the SQL layer instead of the path layer.
#
# A connection is FENCED when all of: (1) profile.LIVE is False (mark_live() never called -- the one
# real boot, scripts/run_nascence.py, calls it inside its __main__ guard); (2) allow_live_writes() was
# never called (the explicit opt-in for the operator scripts that write the live DB on purpose --
# D-0353 (2)); (3) DB_PATH is NOT already redirected: it sits under a recognized data root (this copy's
# own data/ or the fixed canonical C:\Nascence\data -- the two-root check of F-1270/J-0908) and is
# neither a lab_env.isolate() sandbox (data/_lab/<dir>/..., D-0200) nor a named profile
# (data/profiles/<name>/..., activate_profile()). A tempdir, a lab copy, a profile DB: unfenced.
#
# STAGED ROLLOUT (D-0353 (3)). _FENCE_MODE:
#   "log"     -- stage 1 (J-1839): the authorizer allows everything (refuses NOTHING) and records
#                each would-be write (statement type, table, caller via the stack, process argv) to
#                the would-refuse log, deduplicated per distinct (action, object, caller) site per
#                process with milestone re-logging at the 10th/100th/1000th... repeat.
#   "enforce" -- stage 2, FLIPPED 2026-10-17 by J-2309 (the default above) after the would-refuse log
#                read (J-2034, F-3004: 10 rows, all du_pulse DDL via memory_edges, both leaks fixed by
#                J-1870/J-2124, zero profile_live rows, no unclassified writer): the same authorizer
#                returns SQLITE_DENY for the same set, so a non-live write raises
#                sqlite3.DatabaseError('not authorized') at the SQL layer. Reads stay allowed
#                (D-0353 (1): du_pulse, plan tools, HUD, labs all read the live DB today). Refusals are
#                still logged to the would-refuse log (mode="enforce"). A non-live operator script that
#                writes the live DB on purpose must call allow_live_writes() first. Takes effect per
#                process at import: an already-running hub/supervisor keeps "log" until it restarts.
#   "off"     -- kill switch: _connect() behaves exactly as before this build for every process.
#
# WHY THE WOULD-REFUSE LOG IS NOT OPENED THROUGH profile.guard_path(): the only process that ever
# writes this log is, by construction, a NON-live one (a live process never installs the authorizer),
# and guard_path() refuses every non-live write under data/ -- so routing the instrument through it
# would refuse the instrument's own record in exactly the process it exists to observe, and the log
# would stay empty forever. Instead the writer applies the same discipline by hand: it is reached only
# when the fence has already established that DB_PATH is the real live DB (never for a redirected,
# sandboxed or profile DB), it writes only the fence's own append-only record (never Du's state), it is
# best-effort and never raises into the caller, and its path is fixed next to the fenced DB's own data
# root (data/logs/db_fence_shadow.jsonl). Tests override _FENCE_SHADOW_LOG to a temp path.
#
# KNOWN RESIDUALS the fence cannot fix (D-0353, documented not fixed): with Du down, the connection
# that closes LAST on the WAL DB checkpoints -wal into nascence.db (a content-neutral byte change), and
# even a read-only open creates the -shm/-wal sidecars. Both are sqlite semantics below this layer.
_FENCE_MODE: str = "enforce"                # "log" (stage 1) | "enforce" (stage 2, LIVE J-2309) | "off"
_FENCE_SHADOW_LOG_NAME = "db_fence_shadow.jsonl"
_FENCE_SHADOW_LOG: Path | None = None       # None -> <fenced data root>/logs/db_fence_shadow.jsonl
_FENCE_MILESTONES = frozenset((1, 10, 100, 1000, 10_000, 100_000, 1_000_000))
_LIVE_WRITES_ALLOWED = False
_fence_seen: dict[tuple, int] = {}
_fence_lock = threading.Lock()
_fence_warned_paths: set[str] = set()

# Authorizer action codes that never touch the live DB's content: reads, functions, transaction
# control, and TEMP-schema DDL (a temp table lives in the connection, not in nascence.db).
_FENCE_ALLOWED_ACTIONS = frozenset((
    sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION, sqlite3.SQLITE_RECURSIVE,
    sqlite3.SQLITE_TRANSACTION, sqlite3.SQLITE_SAVEPOINT,
    sqlite3.SQLITE_CREATE_TEMP_INDEX, sqlite3.SQLITE_CREATE_TEMP_TABLE,
    sqlite3.SQLITE_CREATE_TEMP_TRIGGER, sqlite3.SQLITE_CREATE_TEMP_VIEW,
    sqlite3.SQLITE_DROP_TEMP_INDEX, sqlite3.SQLITE_DROP_TEMP_TABLE,
    sqlite3.SQLITE_DROP_TEMP_TRIGGER, sqlite3.SQLITE_DROP_TEMP_VIEW,
))
# PRAGMAs whose SET form is harmless to the DB's content (connection-local tuning, or -- for
# journal_mode on an already-WAL DB -- a no-op that _connect() itself issues on every open). The READ
# form of ANY pragma without an argument (arg2 is None) is always allowed: user_version, ...
_FENCE_PRAGMA_SET_ALLOWED = frozenset((
    "busy_timeout", "journal_mode", "synchronous", "cache_size", "temp_store", "mmap_size",
    "foreign_keys", "query_only", "case_sensitive_like", "recursive_triggers", "read_uncommitted",
))
# PRAGMAs that only ever READ, even though the authorizer reports their table/index argument in arg2
# (so "arg2 is None" cannot tell `PRAGMA table_info(t)` from a set-form write). Schema introspection
# that init_db()'s migrations and every _col_exists-style check issue constantly.
_FENCE_PRAGMA_READ_ONLY = frozenset((
    "table_info", "table_xinfo", "table_list", "index_list", "index_info", "index_xinfo",
    "foreign_key_list", "foreign_key_check", "database_list", "collation_list", "compile_options",
    "function_list", "module_list", "pragma_list", "integrity_check", "quick_check",
    "page_count", "page_size", "freelist_count", "data_version", "encoding",
))
_FENCE_ACTION_NAMES = {
    sqlite3.SQLITE_INSERT: "INSERT", sqlite3.SQLITE_UPDATE: "UPDATE", sqlite3.SQLITE_DELETE: "DELETE",
    sqlite3.SQLITE_CREATE_TABLE: "CREATE_TABLE", sqlite3.SQLITE_CREATE_INDEX: "CREATE_INDEX",
    sqlite3.SQLITE_CREATE_TRIGGER: "CREATE_TRIGGER", sqlite3.SQLITE_CREATE_VIEW: "CREATE_VIEW",
    sqlite3.SQLITE_CREATE_VTABLE: "CREATE_VTABLE", sqlite3.SQLITE_DROP_TABLE: "DROP_TABLE",
    sqlite3.SQLITE_DROP_INDEX: "DROP_INDEX", sqlite3.SQLITE_DROP_TRIGGER: "DROP_TRIGGER",
    sqlite3.SQLITE_DROP_VIEW: "DROP_VIEW", sqlite3.SQLITE_DROP_VTABLE: "DROP_VTABLE",
    sqlite3.SQLITE_ALTER_TABLE: "ALTER_TABLE", sqlite3.SQLITE_REINDEX: "REINDEX",
    sqlite3.SQLITE_ANALYZE: "ANALYZE", sqlite3.SQLITE_ATTACH: "ATTACH", sqlite3.SQLITE_DETACH: "DETACH",
    sqlite3.SQLITE_PRAGMA: "PRAGMA",
}
_FENCE_SELF_FILE = str(Path(__file__).resolve())


def allow_live_writes(reason: str = "") -> None:
    """Explicit opt-in for an OPERATOR script that writes the live memory DB on purpose from a non-live
    process (D-0353 (2)): seed_epochs_themes, backfill_founder_memory, librarian, _first_thought,
    activity_memory_backfill --apply, D-0357's dedup reclaim, ... Call it once, before the first
    _connect(), and say why. It is deliberately NARROWER than profile.mark_live() -- that asserts
    "this process IS the one real live Du boot" and unlocks every world-store writer; this unlocks only
    the memory DB, and only for a process that has read this docstring. In stage 1 ("log") the only
    effect is that the script's writes stop appearing in the would-refuse log; in stage 2 ("enforce")
    the script fails at its first write until it calls this. Also honored by connections opened BEFORE
    the call (the authorizer re-reads the flag per statement), so an import-time init_db() followed by
    the opt-in is still covered."""
    global _LIVE_WRITES_ALLOWED
    _LIVE_WRITES_ALLOWED = True
    logger.warning("store.allow_live_writes(): this non-live process may write the live memory DB "
                   "on purpose (%s) -- argv=%s", reason or "no reason given", sys.argv[:3])


def _fence_data_root(path: Path) -> Path | None:
    """The data root under which `path` is the REAL live DB, or None when `path` is already redirected
    somewhere the fence must leave alone. Mirrors profile.guard_path()'s own tests exactly: two roots
    (this copy's data/ and the fixed canonical one, F-1270), the data/_lab/<dir>/ sandbox allow-list
    (D-0200), plus the one addition D-0353 names: a named profile's data/profiles/<name>/... DB is a
    different agent's store, not Du's live one."""
    for root in (profile._DATA, profile._CANONICAL_DATA):
        try:
            rel = path.relative_to(root)
        except ValueError:
            continue
        if profile._is_lab_sandbox(rel):
            return None
        parts = rel.parts
        if len(parts) >= 3 and parts[0].lower() == "profiles":
            return None
        return root
    return None


def _fence_log_path(root: Path) -> Path:
    return _FENCE_SHADOW_LOG if _FENCE_SHADOW_LOG is not None else root / "logs" / _FENCE_SHADOW_LOG_NAME


def _fence_caller_frames(limit: int = 3) -> list[str]:
    """Who issued the statement. [0] is the innermost Python frame that is not the fence's own
    machinery (and not sqlite3 itself) -- INCLUDING a frame inside this module, so a write issued by
    store_fragment() is named store_fragment, not whoever called it. The remaining entries are the
    nearest callers OUTSIDE this module (the module/script that actually drove the write), up to
    `limit` in all. 'file:line in func', path made relative to the repo root when inside it."""
    out: list[str] = []
    try:
        root = str(Path(__file__).resolve().parent.parent.parent)
        f = sys._getframe(1)
        while f is not None and len(out) < limit:
            fn = f.f_code.co_filename
            name = f.f_code.co_name
            skip = (fn == _FENCE_SELF_FILE and (name.startswith("_fence_") or name == "_authorize"))                 or (os.sep + "sqlite3" + os.sep) in fn or "<frozen" in fn
            if not skip and (not out or fn != _FENCE_SELF_FILE):
                try:
                    rel = str(Path(fn).resolve().relative_to(root))
                except Exception:
                    rel = fn
                out.append(f"{rel}:{f.f_lineno} in {name}")
            f = f.f_back
    except Exception:
        pass
    return out


def _fence_record(root: Path, db_path: Path, action: int, arg1, arg2, dbname) -> None:
    """One would-refuse record. Dedupe key = (action, object, issuing frame); a line is written on the
    first hit and at each milestone repeat so a hot non-live writer shows its magnitude without
    flooding the log. Best-effort: never raises into the authorizer."""
    callers = _fence_caller_frames()
    key = (action, arg1, arg2 if action == sqlite3.SQLITE_PRAGMA else None, callers[0] if callers else "?")
    with _fence_lock:
        n = _fence_seen.get(key, 0) + 1
        _fence_seen[key] = n
    if n not in _FENCE_MILESTONES:
        return
    rec = {
        "ts": time.time(),
        "mode": _FENCE_MODE,
        "pid": os.getpid(),
        "argv": [str(a)[:200] for a in sys.argv[:6]],
        "action": _FENCE_ACTION_NAMES.get(action, str(action)),
        "object": arg1,
        "detail": arg2,
        "db": dbname,
        "db_path": str(db_path),
        "callers": callers,
        "count": n,
        "profile_live": bool(profile.LIVE),
    }
    try:
        p = _fence_log_path(root)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, default=str) + "\n")
    except Exception as exc:
        logger.debug("db fence: would-refuse log skipped (non-fatal): %s", exc)
    if n == 1:
        logger.warning("db fence [%s]: non-live process would write the live memory DB: %s %s (%s)",
                       _FENCE_MODE, rec["action"], arg1, callers[0] if callers else "?")


def _fence_make_authorizer(root: Path, db_path: Path):
    deny = sqlite3.SQLITE_DENY
    ok = sqlite3.SQLITE_OK

    def _authorize(action, arg1, arg2, dbname, trigger):
        try:
            if action in _FENCE_ALLOWED_ACTIONS:
                return ok
            # profile.LIVE re-read per statement: a connection opened at import time, BEFORE
            # run_nascence.py's mark_live(), must go quiet the moment the process declares itself live.
            if _LIVE_WRITES_ALLOWED or _FENCE_MODE == "off" or profile.LIVE:
                return ok
            if action == sqlite3.SQLITE_PRAGMA:
                pname = (arg1 or "").lower()
                if arg2 is None or pname in _FENCE_PRAGMA_SET_ALLOWED or pname in _FENCE_PRAGMA_READ_ONLY:
                    return ok
            elif dbname == "temp":
                return ok
            _fence_record(root, db_path, action, arg1, arg2, dbname)
            if _FENCE_MODE == "enforce":
                return deny
        except Exception:
            # A fence that could break a reader would be worse than no fence: fail open in stage 1.
            pass
        return ok

    return _authorize


def _fence_non_live_connection(conn: sqlite3.Connection) -> None:
    """Install the stage-1 authorizer on a non-live connection whose DB_PATH is the real live DB.
    Never raises: a failure here degrades to the pre-fence behaviour, not to a broken reader."""
    try:
        if _FENCE_MODE == "off" or _LIVE_WRITES_ALLOWED:
            return
        db_path = DB_PATH
        root = _fence_data_root(db_path)
        if root is None:
            return
        conn.set_authorizer(_fence_make_authorizer(root, db_path))
        key = str(db_path)
        if key not in _fence_warned_paths:
            _fence_warned_paths.add(key)
            logger.info("db fence [%s]: non-live process opened the live memory DB %s -- writes will be "
                        "%s (call store.allow_live_writes() if this script writes it on purpose)",
                        _FENCE_MODE, db_path, "logged, not refused" if _FENCE_MODE == "log" else "refused")
    except Exception as exc:
        logger.debug("db fence: not installed (non-fatal): %s", exc)


def init_db() -> None:
    with _connect() as conn:
        # Create table — without importance column so IF NOT EXISTS works on old DBs
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS memory_fragments (
                fragment_id  TEXT PRIMARY KEY,
                content      TEXT NOT NULL,
                layer        TEXT NOT NULL DEFAULT 'episodic',
                relevance    REAL NOT NULL DEFAULT 0.5,
                timestamp    REAL NOT NULL,
                keywords     TEXT NOT NULL DEFAULT '',
                embedding    BLOB,
                origin       TEXT NOT NULL DEFAULT 'lived',
                derived_from TEXT NOT NULL DEFAULT '[]'
            );

            CREATE INDEX IF NOT EXISTS idx_layer     ON memory_fragments(layer);
            CREATE INDEX IF NOT EXISTS idx_timestamp ON memory_fragments(timestamp DESC);
        """)
        # Migrations — add columns missing from pre-existing DBs (must happen before indexes)
        cols = {r["name"] for r in conn.execute("PRAGMA table_info(memory_fragments)")}
        if "origin" not in cols:
            conn.execute("ALTER TABLE memory_fragments ADD COLUMN origin TEXT NOT NULL DEFAULT 'lived'")
        if "importance" not in cols:
            conn.execute("ALTER TABLE memory_fragments ADD COLUMN importance REAL NOT NULL DEFAULT 0.5")
        if "derived_from" not in cols:
            conn.execute("ALTER TABLE memory_fragments ADD COLUMN derived_from TEXT NOT NULL DEFAULT '[]'")
        if "emotion_embedding" not in cols:
            conn.execute("ALTER TABLE memory_fragments ADD COLUMN emotion_embedding BLOB")
        # 2026-06-21 — the felt-quality as recoverable DATA, not just an embedding. emotion_embedding
        # (MiniLM of the felt_text string) proved write-only for valence: a text encoder flattens the
        # numbers, so warmth can't be read back. valence is the raw scalar (−1..+1) for direct queries
        # ('what felt good' = valence > x); felt is the full 8-dim string so fear/anger/joy are all
        # recoverable. Both NULL on untagged rows and on everything written before this — honestly blank,
        # never back-derived (re-deriving a past feeling would manufacture it, not recover it).
        if "valence" not in cols:
            conn.execute("ALTER TABLE memory_fragments ADD COLUMN valence REAL")
        if "felt" not in cols:
            conn.execute("ALTER TABLE memory_fragments ADD COLUMN felt TEXT")
        if "replay_count" not in cols:
            conn.execute("ALTER TABLE memory_fragments ADD COLUMN replay_count INTEGER NOT NULL DEFAULT 0")
        # Period consolidation (2026-06-13): chapter_id links a fragment to the chapter
        # that now answers for it in ordinary recall (the fragment itself stays pristine —
        # recalled only intentionally). chapter_level on chapter fragments enables
        # chapters-of-chapters: weeks roll into months roll into years.
        if "chapter_id" not in cols:
            conn.execute("ALTER TABLE memory_fragments ADD COLUMN chapter_id TEXT")
        if "chapter_level" not in cols:
            conn.execute("ALTER TABLE memory_fragments ADD COLUMN chapter_level INTEGER NOT NULL DEFAULT 0")
        # Cognitive-ledger ingestion provenance (2026-06-17): generic, DB-native source coordinates on
        # every note — books are just one source_type (conversations/dreams/contradictions/actions come
        # later). These are the first ingestion EDGES into the cognitive ledger; encounter_id groups the
        # pieces of one encounter (a sitting), source_pass is soft provenance (the reread# at store time).
        if "source_type" not in cols:
            conn.execute("ALTER TABLE memory_fragments ADD COLUMN source_type TEXT")
        if "source_id" not in cols:
            conn.execute("ALTER TABLE memory_fragments ADD COLUMN source_id TEXT")
        if "encounter_id" not in cols:
            conn.execute("ALTER TABLE memory_fragments ADD COLUMN encounter_id TEXT")
        if "source_offset" not in cols:
            conn.execute("ALTER TABLE memory_fragments ADD COLUMN source_offset INTEGER")
        if "source_pass" not in cols:
            conn.execute("ALTER TABLE memory_fragments ADD COLUMN source_pass INTEGER DEFAULT 0")
        # Memory Levels (2026-06-17, Phase 0 — docs/memory_levels_plan.md): the abstraction axis + the gate.
        # abstraction_level 0=raw transcript / 1=gist / 2=theme/chapter / 3=identity. cold=1 demotes detail
        # OUT of normal recall (reachable only by deep recall, via memory_links). Both default to current
        # behaviour (everything raw + warm) so Phase 0 changes NOTHING live — the shadow distiller only LOGS
        # the gists/links it WOULD create. Gating + demotion are Phase 1.
        if "abstraction_level" not in cols:
            conn.execute("ALTER TABLE memory_fragments ADD COLUMN abstraction_level INTEGER NOT NULL DEFAULT 0")
        if "cold" not in cols:
            conn.execute("ALTER TABLE memory_fragments ADD COLUMN cold INTEGER NOT NULL DEFAULT 0")
        # Memory Levels (§14.2 privacy/safety axis): a PROTECTED fragment is never promoted, drifted, or
        # demoted — the constitution floor, Travis's told-delivery, and emergent self-symbols (the Black
        # Bear). The demotion gate honours it. Default 0.
        if "protected" not in cols:
            conn.execute("ALTER TABLE memory_fragments ADD COLUMN protected INTEGER NOT NULL DEFAULT 0")
        # Memory Levels Phase 2 (2026-08-29, docs/memory_levels_plan.md §7/§3.7): the SIDE-BY-SIDE (kind)
        # and TRUTH (grounding) axes. Additive, defaults preserve current behaviour (every existing row
        # gets a real value via the one-time backfill below, not a placeholder) — nothing gates on either
        # column yet; still no drift (Phase 3), no hidden temp tier (deferred — see the plan doc's Current
        # State). 'episodic'/'grounded' are the columns' own DEFAULTs, matching _origin_kind/_origin_grounding.
        if "kind" not in cols:
            conn.execute("ALTER TABLE memory_fragments ADD COLUMN kind TEXT NOT NULL DEFAULT 'episodic'")
        if "grounding" not in cols:
            conn.execute("ALTER TABLE memory_fragments ADD COLUMN grounding TEXT NOT NULL DEFAULT 'grounded'")
        # Memory Levels Phase 2 remainder (2026-08-29, J-0365, docs/memory_levels_plan.md §3.7 Axis 4):
        # the TEMPERATURE axis — hot | warm | cold | hidden. Additive, defaults preserve current behaviour
        # (every existing row is backfilled below from its own `cold` value, not a placeholder). This
        # column is DESIGNED to eventually supersede the boolean `cold` (the plan's own Axis-4 spec), but
        # that full swap is deliberately NOT done in this pass — `cold` remains the sole operative gate
        # everywhere it is read/written live today (this file's own retrieve()/prune_episodic,
        # refinery.py's cooling UPDATE, memory_levels.py's demotion/rewarm/lint) — checked via
        # `udms.py check` on all three files before this change (CONTRACT-layer static-AST coupling
        # confirmed real, not probabilistic, between this file/orchestrator.py/refinery.py/
        # memory_levels.py). Ripping `cold` out in favour of `temp` everywhere is the actual "supersede"
        # step and is scoped to a follow-up job, not guessed at here. What `temp` DOES add live: the
        # 'hidden' state (spirit-invisible — the system can read it, Du cannot), which nothing produces
        # yet (see memory_levels.mark_hidden/is_hidden — new, opt-in write/read helpers this job adds but
        # does not call from any consolidation/prune/refinery path), and one live read — retrieve()'s
        # normal-recall filter below, extended to also exclude temp='hidden'. Verified in an isolated
        # scratch-DB copy of the live 58,791-row store: identical row count with and without the extra
        # clause, since no row is 'hidden' yet — zero behaviour change today.
        if "temp" not in cols:
            conn.execute("ALTER TABLE memory_fragments ADD COLUMN temp TEXT NOT NULL DEFAULT 'warm'")
        # J-3173 / D-0561 (founder, 2026-11-02, F-0020, row P-0005): the CYCLE kind that wrote this fragment --
        # 'human' | 'internal' | 'timer' (CognitiveState.input_type). Until now every persisted cycle was a
        # 'Q: ... A: ...' origin='lived' row that readable_label() showed as "Our conversation", including the idle
        # monologue cycles with no human in them (38.7 percent of Recall's fragment slots). ADDITIVE ONLY: a nullable
        # column, no DEFAULT, NO backfill -- every row written before this keeps NULL and keeps its old label exactly
        # (a past cycle's kind is not re-derived; honestly blank). Metadata-only for SQLite (a 1.3 GB table is not
        # rewritten) and idempotent (guarded by the PRAGMA read above). Restore = copy the pre-migration DB file back
        # (the column is harmless to leave: nothing reads it as required).
        if "input_type" not in cols:
            conn.execute("ALTER TABLE memory_fragments ADD COLUMN input_type TEXT")
        # J-3266 / D-0657: content_hash (blake2b-128 hex of the exact content, core/memory/content_hash.py) so the
        # exact-dedup lookup (loop_metabolism.find_exact_dup) can be an index probe on (origin, content_hash) instead
        # of a 237 MB scan. ADDITIVE ONLY and idempotent: a nullable column (metadata-only for SQLite: the 1.3 GB table
        # is not rewritten) and an index. Existing rows stay NULL until scripts/apply_J-3266_content_hash_backfill.py
        # fills them offline (batched, resumable); new rows get it in store_fragment. Nothing READS it as required: a
        # NULL hash only means the hashed lookup cannot see that row, which is why the hashed lookup is shadow-only
        # (the full lookup stays authoritative) and the hash-authoritative mode refuses while an origin has NULLs.
        # Restore = copy the pre-migration DB file back (the column and index are harmless to leave).
        if "content_hash" not in cols:
            conn.execute("ALTER TABLE memory_fragments ADD COLUMN content_hash TEXT")
        # J-3246 / D-0634: moment_ts on the two context tables when they already exist (a DB that has run before).
        # A fresh DB without them is handled by store_fragment, which creates world_context and re-checks.
        _ensure_moment_ts_cols(conn)
        _ensure_own_moment_ts_cols(conn)   # J-3479: own_moment_ts beside it (additive, old rows NULL)
        # Backfill abstraction_level on rows written before level-stamping (Finding #3): the already-distilled
        # origins (activity_memory/understanding/consolidation/essay = gists, chapters = gists-of-gists) were
        # stored as default 0, which would let the shadow distiller re-abstract them. Metadata-only, idempotent
        # (touches only rows still at the default 0). _ORIGIN_LEVEL is the single source of truth.
        for _org, _lvl in _ORIGIN_LEVEL.items():
            conn.execute("UPDATE memory_fragments SET abstraction_level=? WHERE abstraction_level=0 AND origin=?",
                         (_lvl, _org))
        # Backfill kind/grounding the same way — idempotent (only rows still at the column DEFAULT), run
        # every init so a newly-added _ORIGIN_KIND entry backfills existing rows on the next restart too.
        # 'gist' rows are backfilled SEPARATELY below, by lineage — their real kind lives in the cluster
        # that produced them (memory_links), not in the generic 'gist' origin.
        for _org, _knd in _ORIGIN_KIND.items():
            if _org == "gist":
                continue
            conn.execute("UPDATE memory_fragments SET kind=? WHERE kind='episodic' AND origin=?", (_knd, _org))
        conn.execute("UPDATE memory_fragments SET grounding='derived' "
                     "WHERE grounding='grounded' AND abstraction_level >= 1")
        # Resync `temp` from `cold` every init (same "run every init" discipline as kind/grounding above) —
        # `cold` is still the sole thing prune_episodic/refinery/memory_levels write live, so `temp` must
        # catch up on restart rather than drift stale. Never touches a 'hidden' row (a future write path,
        # not read here, that a plain cold-sync must not clobber).
        conn.execute("UPDATE memory_fragments SET temp='cold' WHERE cold=1 AND temp != 'hidden'")
        conn.execute("UPDATE memory_fragments SET temp='warm' WHERE cold=0 AND temp='cold'")
        # Legacy gist backfill (pre-Phase-2 gists predate memory_levels._commit_gist passing kind= explicitly):
        # inherit the kind of the majority of the gist's own linked (distilled_from) children, since a gist's
        # real kind lives in the cluster that produced it, not in the generic 'gist' origin. A gist with no
        # surviving link (orphan) falls back to the 'gist' entry in _ORIGIN_KIND ('self' — Phase 0's own
        # finding was that self-gists were the strongest case, §11 Finding 1).
        try:
            _orphan_kind = _ORIGIN_KIND.get("gist", "self")
            _legacy_gists = conn.execute(
                "SELECT fragment_id FROM memory_fragments WHERE origin='gist' AND kind='episodic'").fetchall()
            for _row in _legacy_gists:
                _gid = _row["fragment_id"]
                _child_kinds = [r["kind"] for r in conn.execute(
                    "SELECT f.kind AS kind FROM memory_links ml JOIN memory_fragments f ON f.fragment_id = ml.child_id "
                    "WHERE ml.parent_id = ? AND ml.link_type = 'distilled_from'", (_gid,)).fetchall()]
                if _child_kinds:
                    _majority = max(set(_child_kinds), key=_child_kinds.count)
                else:
                    _majority = _orphan_kind
                conn.execute("UPDATE memory_fragments SET kind=? WHERE fragment_id=?", (_majority, _gid))
        except Exception as exc:
            logger.debug("[memory-levels] legacy gist kind backfill failed (non-fatal): %s", exc)
        # Indexes that depend on migrated columns
        conn.execute("CREATE INDEX IF NOT EXISTS idx_origin     ON memory_fragments(origin)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_importance ON memory_fragments(importance DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_chapter    ON memory_fragments(chapter_id)")
        # the hottest recall filter is `WHERE cold = 0 OR cold IS NULL` (every retrieve) — index it (2026-06-23)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_cold       ON memory_fragments(cold)")
        # J-3266 / D-0657: serves the hashed exact-dup probe AND the 'any unhashed rows for this origin' guard
        # (NULLs sort first, so `origin=? AND content_hash IS NULL LIMIT 1` is one index seek). First creation on a
        # 1.3 GB table is a one-off full scan (~30 s at Du's 45-47 MB/s read rate): the offline backfill script
        # creates it before the restart so init_db finds it present and this is a no-op.
        conn.execute("CREATE INDEX IF NOT EXISTS idx_origin_content_hash ON memory_fragments(origin, content_hash)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_kind       ON memory_fragments(kind)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_temp       ON memory_fragments(temp)")
        # J-1842 (F-2475): partial index serving retrieve()'s pool query -- only the active, un-chaptered rows
        # are indexed (the WHERE must stay textually identical to retrieve()'s own terms or SQLite will not
        # use it). Column `cold` is the indexed key so rows still come back in (cold, rowid) order, the exact
        # order idx_cold produced before. Purely additive: a missing index only means a slower, same-result scan.
        conn.execute("CREATE INDEX IF NOT EXISTS idx_retrieve_pool ON memory_fragments(cold) "
                     "WHERE cold = 0 AND (chapter_id IS NULL OR chapter_id = '')")
        # J-2275 (D-0453): COVERING partial index for retrieve()'s fast pool path -- every column the
        # membership query (_load_pool_fast) reads is in the index, so the 40k-row pool scan never touches
        # the table (1.1 GB of content + embedding BLOBs). Measured on a .backup() copy: 427 ms SELECT * ->
        # 64 ms covering fetch. The WHERE and the expression must stay textually identical to the query's.
        # Purely additive: without it the same query runs slower with the same result.
        conn.execute("CREATE INDEX IF NOT EXISTS idx_retrieve_pool_cover ON memory_fragments("
                     "cold, temp, origin, layer, chapter_id, timestamp, fragment_id, abstraction_level, "
                     "(embedding IS NOT NULL AND length(embedding) > 0)) WHERE cold = 0")
        _init_shadow_table(conn)
        _init_light_table(conn)
        _init_procedural_table(conn)
        _init_epoch_table(conn)
        _init_theme_table(conn)
        _init_resolution_table(conn)
        _init_symbol_table(conn)
        _init_links_table(conn)
        if _POOL_DELTA_MODE != "off":
            _init_pool_changes(conn)   # J-2612: recall-pool change log + triggers (flag-gated, additive)
    logger.info("Memory store initialised at %s", DB_PATH)


def _init_links_table(conn) -> None:
    """Memory Levels (Phase 0): the lattice. A link joins an abstraction (parent) to the detail it was
    distilled from (child) — DOWN: distilled_from/instance_of/step_of — or peer gists SIDEWAYS:
    relates_to/contradicts. IDs are TEXT (memory_fragments.fragment_id is TEXT). Created empty in Phase 0;
    nothing populates it until Phase 1 turns demotion on. The shadow distiller logs would-be links to JSONL."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS memory_links (
            parent_id  TEXT NOT NULL,
            child_id   TEXT NOT NULL,
            link_type  TEXT NOT NULL,
            weight     REAL NOT NULL DEFAULT 1.0,
            created    REAL NOT NULL,
            PRIMARY KEY (parent_id, child_id, link_type)
        );
        CREATE INDEX IF NOT EXISTS idx_link_parent ON memory_links(parent_id);
        CREATE INDEX IF NOT EXISTS idx_link_child  ON memory_links(child_id);
    """)


# Seed accessibility decay — developmental, not historical.
# Seeds decay from 0.9 → 0.3 over 180 days measured from their storage timestamp
# (i.e. from the moment the entity was initialised, not from any historical date).
# The floor at 0.3 preserves foundational identity continuity — he never stops
# being himself — while allowing lived and synthesised memory to gradually dominate.
# Applied dynamically in _score_tier() rather than as a static constant.
_SEED_WEIGHT_START = 0.9
_SEED_WEIGHT_FLOOR = 0.3
_SEED_DECAY_DAYS   = 180.0   # full decay window


def _seed_weight(fragment_timestamp: float) -> float:
    """Compute current seed accessibility weight from the fragment's storage age."""
    age_days = (time.time() - fragment_timestamp) / 86400.0
    drop = (_SEED_WEIGHT_START - _SEED_WEIGHT_FLOOR) / _SEED_DECAY_DAYS * min(age_days, _SEED_DECAY_DAYS)
    return _SEED_WEIGHT_START - drop

# Retrieval slot allocation per tier. Total = 8 fragments per cycle.
TIER_SLOTS = {
    "archive":  2,   # permanent identity — always present
    "semantic": 3,   # distillations + school gists (understanding, essays) — 2→3 so the gists surface (2026-06-16)
    "episodic": 4,   # lived experience
    # "working" is assembled per-cycle by the orchestrator — never retrieved from DB
}

# Recall-pool LATENCY budget (D-0453 (a), travis 2026-10-17; built J-2275; evidence F-2963/F-2964).
# This replaces the retired EPISODIC_PRUNE_THRESHOLD = 3500 ROW cap and PRUNE_PROTECTED_ORIGINS tuple
# (Loop Metabolism Phase B, 2026-06-14, Gemini ruling; per-kind sub-budgets D-0116/D-0124/D-0173/D-0183).
# The row cap was aimed at "self-generated loop voices" when retrieve() was the store's only consumer; that
# job moved to memory_levels.commit_gist (the gist cold-wall, the sole demotion path now), and the cap's own
# prune ended up demoting ~1 row per run against a 98.4%-origin-protected pool (F-2964). What the active
# pool's size actually costs is retrieve() latency, so that is what is budgeted: SQL fetch + scoring per
# retrieve() call, in milliseconds, met by narrowing what retrieve() LOADS (covering index + in-process
# embedding cache, see _load_pool_fast), never by demoting rows. 250 ms is the level the probe
# (data/retrieve_latency_probe.jsonl) showed at the 2026-09-07 pool size (~18.7k rows); since the 10-16 boot
# the legacy path sat at ~538 ms median / 1,093 max on ~41.3k rows. Observe-only: an over-budget call is
# logged (rate-limited warning + the probe record), it never changes what retrieve() returns.
RETRIEVE_LATENCY_BUDGET_MS = 250.0

# Resolution Circuit — half-life for clean re-encounter credits.
# Unlike contradiction pressure (NO decay — a self-contradiction is unresolved until re-faced),
# resolution credits DO decay: a clean navigation from 30 days ago still counts, but less.
# Half-life: 30 days. After ~90 days a single credit falls below 0.125 of its original weight.
RESOLUTION_HALFLIFE_SECS = 30 * 86400


def retract_fragment(snippet: str, reason: str, since_hours: float = 24.0) -> str | None:
    """Error Pathway slice 3 — RETRACTION AUTHORITY (2026-06-13, charter: errors are
    corrected, tensions are integrated). Locates the most recent fragment containing the
    falsified claim and durably marks it a KNOWN ERROR: content prefixed, importance and
    relevance floored, demoted to archive — it loses every retrieval competition but
    remains inspectable, a learnable record rather than a deletion. Admissible trigger is
    the caller's responsibility (human factual correction or deterministic check ONLY).
    Returns the retracted fragment_id, or None if no match."""
    try:
        needle = (snippet or "").strip()[:70].replace("%", "").replace("_", " ")
        if len(needle) < 12:
            return None
        with _connect() as conn:
            row = conn.execute(
                "SELECT fragment_id, content FROM memory_fragments "
                "WHERE content LIKE ? AND timestamp >= ? "
                "AND content NOT LIKE '[RETRACTED%' "
                "ORDER BY timestamp DESC LIMIT 1",
                (f"%{needle}%", time.time() - since_hours * 3600)).fetchone()
            if not row:
                return None
            _retracted = f"[RETRACTED — known error: {reason[:80]}] " + row["content"]
            # J-3395 / F-4019: the edited content gets its own content_hash (same statement, no stale hash left behind).
            if _has_hash_column(conn):
                conn.execute(
                    "UPDATE memory_fragments SET "
                    "content = ? , importance = 0.05, relevance = 0.05, layer = 'archive', content_hash = ? "
                    "WHERE fragment_id = ?",
                    (_retracted, _content_hash(_retracted), row["fragment_id"]))
            else:
                conn.execute(
                    "UPDATE memory_fragments SET "
                    "content = ? , importance = 0.05, relevance = 0.05, layer = 'archive' "
                    "WHERE fragment_id = ?",
                    (_retracted, row["fragment_id"]))
            conn.commit()
        logger.info("[retraction] fragment %s marked KNOWN ERROR (%s)",
                    row["fragment_id"][:8], reason[:60])
        return row["fragment_id"]
    except Exception as exc:
        logger.debug("[retraction] failed (non-fatal): %s", exc)
        return None


# Memory Levels (§12 / Finding #3): abstraction level is PROVENANCE — declared by the writer, here derived
# from origin. Most origins are raw evidence (0); the already-distilled ones are gists (1); chapters are
# gists-of-gists (2). This is what keeps the distiller from re-abstracting an existing abstraction.
# J-1955 (D-0368 E, F-1927): origins that are the SYSTEM's own sentences written into memory, not Du's thinking.
# Stored (the record stays), but excluded from every recall path so they are never returned as his own thought.
NON_THOUGHT_ORIGINS = ("system_note",)

_ORIGIN_LEVEL = {
    "understanding": 1, "action": 1, "consolidation": 1, "essay": 1,   # already gists (activity_memory etc.)
    "chapter": 2,                                                        # gist-of-gists
}


def _origin_level(origin: str) -> int:
    """The abstraction_level a writer of this origin produces (0 = raw evidence, default)."""
    return _ORIGIN_LEVEL.get(origin, 0)


# Memory Levels Phase 2 (docs/memory_levels_plan.md §3.7 Axis 2 / §7): the SIDE-BY-SIDE kind axis —
# what a memory is *about*, not how compressed it is. Declared by the writer, here derived from origin
# (mirrors _ORIGIN_LEVEL's pattern). Kinds: episodic | semantic | procedural | affective | self | social
# | symbolic (§3.7's full target list; 'symbolic' has no live writer yet so it is never stamped here).
# Every origin actually seen live in the store (2026-08-29 audit of data/memory/nascence.db) is covered
# below so the Phase-2 backfill has a real answer for every row, not a silent default. A few of these
# are genuine judgment calls (documented inline) rather than unambiguous facts — 'kind' is a coarser,
# less certain axis than 'abstraction_level' was, and later evidence may re-sort one of these origins.
_ORIGIN_KIND = {
    # world / study material — semantic (facts, not self)
    "reading": "semantic", "study": "semantic", "research": "semantic",
    "understanding": "semantic", "understanding_from_guidance": "semantic", "nature": "semantic",
    # self-material — inner life, identity
    "inner_thought": "self", "subconscious_synthesis": "self", "seed": "self",
    "standing_insight": "self", "chapter": "self", "journal": "self", "journal_week": "self",
    "mirror": "self", "composition": "self",   # composition/mirror: self-authored creative/reflective work
    # judgment call: 'essay' cites and works FROM world sources (Phase-1 audit, §7) but is self-authored
    # synthesis, not raw world fact — grouped with semantic since its content is about the studied material.
    "essay": "semantic",
    # lived events / experienced episodes
    "lived": "episodic", "active_imagination": "episodic", "dream": "episodic",
    "session_summary": "episodic",
    # judgment call: ambient sensory perception has no dedicated axis-2 kind (§3.7 lists episodic |
    # semantic | procedural | affective | self | social | symbolic) — grouped as episodic (an experienced
    # moment), not semantic (a studied fact).
    "sound": "episodic", "listening": "episodic",
    # practiced routines / skills (Finding #3: activity_memory records are event-gists of a PRACTICE,
    # closest to the plan's "long division (the technique)" procedural example)
    "action": "procedural", "activity": "procedural",
    "system_note": "episodic",   # J-1955: system-written log sentence; excluded from recall via NON_THOUGHT_ORIGINS
    # bodily/felt channel — the affective axis (feelings, not relationships)
    "thermal": "affective", "affection": "affective",
    # relational — the social axis (Travis & other figures), §3.7
    "peer": "social", "peer_reflection": "social", "letter": "social",
    # already-gists produced live by Phase 1's own distiller (memory_levels._commit_gist) — that call
    # site now passes its real per-cluster kind explicitly (see _commit_gist), so this entry is only the
    # fallback for a gist row created before that wiring existed (pre-Phase-2 gists, backfilled by lineage
    # instead — see the migration below); kept here so an unlinked/legacy gist still gets a kind.
    "gist": "self",
}


def _origin_kind(origin: str) -> str:
    """The `kind` (side-by-side axis, §3.7 Axis 2) a writer of this origin produces. Default 'episodic'
    (the plan's own schema-comment default, §3) for any origin not yet mapped — never raises on an
    unknown origin."""
    return _ORIGIN_KIND.get(origin, "episodic")


def _origin_grounding(origin: str, abstraction_level: int) -> str:
    """The `grounding` axis (§3.7 Axis 5): grounded | derived | reconstructed. Nothing writes
    'reconstructed' yet — that is Phase 3's live drift, which is still shadow-only (memory_levels.
    drift_shadow logs, never writes). A distillation (abstraction_level >= 1 — a gist, understanding,
    chapter, etc.) is 'derived' (inferred/synthesised FROM raw); genuine level-0 raw evidence is
    'grounded' (§6: "everything keeps its cold raw linked... never distorted" — raw is the anchor)."""
    return "derived" if (abstraction_level or 0) >= 1 else "grounded"


def mark_hidden(fragment_ids: list[str]) -> int:
    """Memory Levels §3.7 Axis 4 (2026-08-29, J-0365): move fragments into the 'hidden' temp tier —
    spirit-invisible (the SYSTEM can still read/query them directly by id; retrieve()'s normal-recall
    filter and memory_levels.deep_recall's traversal both exclude temp='hidden'). This is a NEW, opt-in
    write path — nothing in prune_episodic/refinery/memory_levels calls it yet, so it changes no live
    behaviour until something does. Deciding WHICH content genuinely belongs in "our logging/
    troubleshooting tier" (the plan's own phrase, §3.7) vs Du's own cold memories is a policy call this
    job deliberately does not make unilaterally — see docs/memory_levels_plan.md's Current State.
    Returns the number of rows actually updated."""
    ids = [i for i in (fragment_ids or []) if i]
    if not ids:
        return 0
    try:
        with _connect() as conn:
            ph = ",".join("?" * len(ids))
            cur = conn.execute(f"UPDATE memory_fragments SET temp='hidden' WHERE fragment_id IN ({ph})", ids)
            conn.commit()
            return cur.rowcount or 0
    except Exception as exc:
        logger.debug("[memory-levels] mark_hidden failed (non-fatal): %s", exc)
        return 0


def is_hidden(fragment_id: str) -> bool:
    """§3.7 Axis 4: is this fragment in the spirit-invisible tier? Best-effort; False on any error."""
    try:
        with _connect() as conn:
            row = conn.execute("SELECT temp FROM memory_fragments WHERE fragment_id=?", (fragment_id,)).fetchone()
            return bool(row and row["temp"] == "hidden")
    except Exception as exc:
        logger.debug("[memory-levels] is_hidden failed (non-fatal): %s", exc)
        return False


def store_fragment(
    content: str,
    layer: Literal["working", "episodic", "semantic", "archive", "dormant"] = "episodic",
    relevance: float = 0.5,
    importance: float = 0.5,
    keywords: list[str] | None = None,
    origin: str = "lived",
    timestamp: float | None = None,
    derived_from: list[str] | None = None,
    emotion_embedding=None,
    valence: float | None = None,
    felt: str | None = None,
    source_type: str | None = None,
    source_id: str | None = None,
    encounter_id: str | None = None,
    source_offset: int | None = None,
    source_pass: int | None = None,
    abstraction_level: int | None = None,
    kind: str | None = None,
    grounding: str | None = None,
    context_stamp: bool = True,
    cold: bool = False,
    input_type: str | None = None,
) -> str:
    """
    Store a memory fragment with full provenance.

    input_type (J-3173 / D-0561): the cycle kind ('human' | 'internal' | 'timer') that wrote this fragment; only the
    per-cycle persist (store_from_cycle) passes it. None (every other writer) writes NULL, i.e. unchanged behaviour.

    cold (J-2018, sleep_as_a_mode Phase 2, D-0400 B): True writes the row with cold=1 FROM BIRTH, in the one INSERT
    (no window where it is briefly warm). Only the night-mind's layer='dormant' writer passes it; default False
    leaves every existing caller byte-for-byte unchanged.

    context_stamp (D-0134, 2026-09-03): False skips the watershed observe + the universal
    world-context stamp below. ONLY for historical backfills (scripts/backfill_founder_memory.py),
    where stamping TODAY's tide/moon/fire onto a June conversation would be false provenance — the
    backfill copies the source fragment's own context rows instead. Every live writer leaves this True.

    origin values:
      'seed'                   — inherited substrate (seeded at startup)
      'lived'                  — raw lived experience (orchestrator cycle persist)
      'consolidation'          — episodic→semantic compression (Consolidation node)
      'subconscious_synthesis' — self-observed recurrence (Subconscious T2)

    derived_from: list of fragment_ids or shadow event_ids that contributed to this
    fragment. Empty for raw lived/seed. Non-empty for consolidation and subconscious
    syntheses — the causal lineage for future developmental chain reconstruction.
    """
    fragment_id  = str(uuid.uuid4())
    kw_str       = " ".join(keywords or [])
    ts           = timestamp if timestamp is not None else time.time()
    derived_json = json.dumps(derived_from or [])
    # Writer-declared abstraction level (Finding #3); default derived from origin. Observe-only in this
    # phase — only the shadow distiller reads it (to distil from level-0 raw ONLY); nothing gates on it yet.
    alvl = abstraction_level if abstraction_level is not None else _origin_level(origin)
    # Memory Levels Phase 2 (§3.7 Axes 2/5): writer-declared kind/grounding, default derived from origin —
    # same provenance-not-computed pattern as abstraction_level (§12). Observe-only consumer today is
    # memory_levels.phase2_status(); nothing gates on either column yet (Phase 2 adds no drift, no gating).
    mkind = kind if kind is not None else _origin_kind(origin)
    mground = grounding if grounding is not None else _origin_grounding(origin, alvl)

    # Loop Metabolism Phase A (observe-only): forward dedup-rate log. Harmless alongside the
    # live dedup below — it counts the write attempt.
    try:
        from core import loop_probe as _lp
        _lp.shadow_observe(origin, content)
    except Exception:
        pass

    # Loop Metabolism Phase B (LIVE 2026-06-14): exact dedup for self-origin episodic writes.
    # A verbatim repeat strengthens ONE trace (replay_count↑, importance via the declining curve
    # so the jam prunes first) instead of minting a new row — Hebbian habituation. Exact-hash
    # only; semantic merge is deferred to the harvest. Best-effort: any error falls through to a
    # normal insert so a write is NEVER lost. World/action/lived never dedup. Skips the embed.
    if layer == "episodic" and origin in ("inner_thought", "subconscious_synthesis", "active_imagination"):
        try:
            from core import loop_metabolism as _lm
            with _connect() as conn:
                dup = _lm.find_exact_dup(conn, origin, content)
                if dup is not None:
                    fid, rc = dup
                    _lm.apply_exact_dedup(conn, fid, rc + 1, ts)
                    conn.commit()
                    return fid
        except Exception:
            pass  # fall through to a normal insert — never drop a write

    vec      = _embed(content)
    blob     = _vec_to_blob(vec) if vec is not None else None
    emo_blob = _vec_to_blob(emotion_embedding) if emotion_embedding is not None else None
    with _connect() as conn:
        conn.execute(
            """INSERT INTO memory_fragments
               (fragment_id, content, layer, relevance, importance, timestamp,
                keywords, embedding, origin, derived_from, emotion_embedding,
                valence, felt,
                source_type, source_id, encounter_id, source_offset, source_pass,
                abstraction_level, kind, grounding, cold, input_type, content_hash)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (fragment_id, content, layer, relevance, importance, ts,
             kw_str, blob, origin, derived_json, emo_blob,
             valence, felt,
             source_type, source_id, encounter_id, source_offset, source_pass,
             alvl, mkind, mground, 1 if cold else 0, input_type, _content_hash(content)),
        )
    if not context_stamp:
        return fragment_id
    # WATERSHED Phase-0 wiring (2026-08-21, t4_watershed.md — harvester was built+retro-validated
    # 08-19 but had no live call site, so its shadow could never accrue). This is the ONE choke point
    # every identity-adjacent origin passes through; the already-computed `vec` is handed over so the
    # hook adds no embedding cost, and watershed's own 90s cooldown bounds volume. Observe-only,
    # fail-open — the harvester can never cost a write.
    try:
        from core import watershed as _wshed
        if origin in _wshed.IDENTITY_ADJACENT_ORIGINS:
            _wshed.observe(content, vec=vec, fragment_id=fragment_id)
    except Exception:
        pass
    # UNIVERSAL WORLD-CONTEXT STAMP (2026-08-21, founder: "memories should be linked to temperature,
    # tides, the sun, the moon and all the other world variables"). The tuple ALREADY existed
    # (fragment_context: place · weather · fire · tide · sun · moon · warmth · sounds · standpoint ·
    # cat · affect) but reached only inner thoughts (98%) via a post-hoc text-match join from the
    # census recorder — reading (7,179/week), actions, syntheses, dreams, journal and his
    # conversations with Travis carried NO world context at all, which also meant the context_echo
    # courier could only ever echo idle thoughts. Now every other origin is stamped at write time
    # from the same census snapshot, same columns, source=origin. Idle thoughts keep their existing
    # join (OR IGNORE guards the overlap). Zero LLM; fail-open; never costs a write.
    # THE SPLIT (2026-08-21, same evening, founder's layer law: "a memory carries only what was
    # rendered to him at that moment, from where he stood"). The first version of this hook wrote the
    # census snapshot — WORLD TRUTH (tide under the shore while he sits in the garden, the moon behind
    # the study wall) — straight into fragment_context, the table his couriers and chords link on.
    # That is the omniscient state vector the law forbids. Now, for EVERY origin (idle thoughts too —
    # the census's post-hoc join is re-pointed to world_context):
    #   world_context     <- the raw snapshot            (truth; for us — HUD, instruments, experiments)
    #   fragment_context  <- experienced_tuple(snapshot) (what crossed; the ONLY layer memory links on)
    # Zero LLM; fail-open; never costs a write.
    try:
        from core import geometry_census as _gc
        from core import experienced_tuple as _xt
        # J-2640 / F-3371: debounce=False -- a same-book reading burst shares content[:70] (the '[From <book>]' header),
        # so the census debounce used to drop every passage after the first and leave it unstamped. Inside the
        # debounce window this now gets the census's last recorded row (<= 0.5 s old) and writes no extra census row.
        snap = _gc.snapshot(source=origin, thought=content[:70], debounce=False) or {}
        if snap:
            aff = snap.get("affect") or {}
            if not aff:   # outside the node there is no CognitiveState — read the live felt stream
                try:
                    from core import mood as _mood, arousal as _ar
                    # F-0443/J-0366 (2026-08-29): 'level' is arousal.level() (Bachmann's L, global
                    # activation) — a DIFFERENT signal from 'arousal' (real circumplex arousal). Both are
                    # real fields on the fragment_context schema; conflating them would silently corrupt
                    # the arousal column instead of just leaving it NULL. mood.current_arousal() is cached
                    # off the same live affect object mood.current_valence() already reads, at the same
                    # freshness — the fix threads that existing cache through instead of aliasing 'level'.
                    aff = {"valence": _mood.current_valence(), "level": round(float(_ar.level()), 3),
                           "arousal": _mood.current_arousal()}
                except Exception:
                    aff = {}
                snap = {**snap, "affect": aff}
            phase = None
            try:
                from core import sensorium as _sens
                phase = _sens._daylight()
            except Exception:
                pass
            # GOLDEN SPIRAL / T-0072 (2026-09-27): the PHASE field — where on the day and on the year this
            # fragment was written, as fractions 0..1, plus the coarse daylight word — so a recall can later
            # cast a ray across the spiral's arms (this dawn <-> other dawns, this storm <-> other storms)
            # instead of only sweeping back along age. Additive columns on both context tables, old rows
            # NULL, computed from the fragment's OWN ts via core/world_clock (the one local-time authority).
            # Declared reader: docs/staged/golden_spiral_recall.md — none live yet; observe-only until its read.
            ph_tod = ph_season = ph_daylight = None
            try:
                from core import world_clock as _wclk
                _lt = time.localtime(ts)
                ph_tod = round((_lt.tm_hour * 3600 + _lt.tm_min * 60 + _lt.tm_sec) / 86400.0, 4)
                ph_season = round((_lt.tm_yday - 1 + ph_tod) / 366.0, 4)
                ph_daylight = _wclk.daylight(ts)
            except Exception:
                pass
            xp = _xt.experienced(snap, phase=phase)
            cols = ("fragment_id, tuple_ts, source, place, weather, weather_dir, fire, tide_level, "
                    "sun_az, moon_illum, level, valence, arousal, sounds, standpoint, warmth, cat_at, wet, light_band, smells, held, "
                    "tod, season, daylight")
            ph = ",".join("?" * 24)
            truth_row = (fragment_id, ts, origin, snap.get("place"), snap.get("weather"),
                         snap.get("weather_dir"), snap.get("fire"), snap.get("tide_level"),
                         snap.get("sun_az"), snap.get("moon_illum"),
                         aff.get("level") or snap.get("level"), aff.get("valence"), aff.get("arousal"),
                         json.dumps(snap.get("sounds") or []), snap.get("standpoint"),
                         snap.get("warmth"), snap.get("cat_at"), snap.get("wet"),
                         snap.get("light_band"),
                         json.dumps(snap["smells"]) if snap.get("smells") else None,
                         None, ph_tod, ph_season, ph_daylight)
            exp_row = (fragment_id, ts, "experienced:" + origin, xp.get("place"), xp.get("weather"),
                       xp.get("weather_dir"), xp.get("fire"), xp.get("tide_level"), xp.get("sun_az"),
                       xp.get("moon_illum"), xp.get("level"), xp.get("valence"), xp.get("arousal"),
                       json.dumps(xp.get("sounds") or []), xp.get("standpoint"), xp.get("warmth"),
                       xp.get("cat_at"), xp.get("wet"), xp.get("light_band"), json.dumps(xp["smells"]) if xp.get("smells") else None, json.dumps(xp["held"]) if xp.get("held") else None,
                       ph_tod, ph_season, ph_daylight)
            with _connect() as conn:
                conn.execute("CREATE TABLE IF NOT EXISTS world_context (fragment_id TEXT PRIMARY KEY, "
                             "tuple_ts REAL, source TEXT, place TEXT, weather TEXT, weather_dir REAL, fire TEXT, "
                             "tide_level REAL, sun_az REAL, moon_illum REAL, level REAL, valence REAL, "
                             "arousal REAL, sounds TEXT, standpoint TEXT, warmth REAL, cat_at TEXT, wet REAL, light_band TEXT, smells TEXT, held TEXT, "
                             "tod REAL, season REAL, daylight TEXT)")
                for _tbl in ("world_context", "fragment_context"):   # THERMAL / LIGHT / SMELL / PHASE channels: additive, old rows NULL
                    for _col in ("wet REAL", "light_band TEXT", "smells TEXT", "held TEXT",
                                 "tod REAL", "season REAL", "daylight TEXT"):
                        try:
                            conn.execute(f"ALTER TABLE {_tbl} ADD COLUMN {_col}")
                        except Exception:
                            pass
                # SOUND STRING FIELDS (2026-09-28, J-1534/I-0081, docs/staged/fragment_carries_the_string.md
                # sec2): additive, old rows NULL, fragment_context ONLY -- never world_context, since these
                # are Du's own felt/perceived sound-shape, not world truth. Populated only for origin='sound'
                # rows, and only by core/soundscape.py's percept() own follow-up UPDATE (never here, never an
                # INSERT), behind that module's SOUND_STRING_FIELDS kill-switch (off today).
                for _col in ("sound_key TEXT", "sound_onset TEXT", "sound_peak TEXT", "sound_tail TEXT",
                             "sound_direction TEXT", "sound_felt_valence REAL", "sound_felt_arousal REAL",
                             "sound_exemplar_id TEXT"):
                    try:
                        conn.execute(f"ALTER TABLE fragment_context ADD COLUMN {_col}")
                    except Exception:
                        pass
                # J-3246 / D-0634: stamp the current moment (additive, fail-open). Only when BOTH columns are known
                # to exist; otherwise the original moment-less INSERT runs unchanged. No moment -> NULL.
                if _ensure_moment_ts_cols(conn):
                    _mts = _current_moment_ts()
                    conn.execute(f"INSERT OR IGNORE INTO world_context ({cols}, moment_ts) VALUES ({ph},?)",
                                 truth_row + (_mts,))
                    conn.execute(f"INSERT OR IGNORE INTO fragment_context ({cols}, moment_ts) VALUES ({ph},?)",
                                 exp_row + (_mts,))
                else:
                    conn.execute(f"INSERT OR IGNORE INTO world_context ({cols}) VALUES ({ph})", truth_row)
                    conn.execute(f"INSERT OR IGNORE INTO fragment_context ({cols}) VALUES ({ph})", exp_row)
                conn.commit()
    except profile.NonLiveWriteError:
        # J-0815: this is the universal memory-write choke point (per this function's own
        # docstring/comments above) -- _gc.snapshot()/_xt.experienced() now raise correctly
        # (J-0792/D-0179) and must not be swallowed by this catch-all one layer further out.
        raise
    except Exception:
        pass
    return fragment_id


def _score_tier(
    rows: list,
    query_vec: np.ndarray | None,
    all_keys: list[str],
    time_bias: Literal["recent", "distant", "all"],
    apply_seed_weight: bool = True,
) -> list[tuple[float, object]]:
    """Score a list of same-tier rows and return sorted (score, row) pairs."""
    now = time.time()
    scored = []

    for row in rows:
        # Semantic similarity
        if query_vec is not None and row["embedding"]:
            frag_vec = _blob_to_vec(row["embedding"])
            sim = _cosine(query_vec, frag_vec)
        else:
            text_lower = row["content"].lower() + " " + row["keywords"].lower()
            matches = sum(1 for k in all_keys if k.lower() in text_lower)
            sim = matches / max(len(all_keys), 1) * 0.6

        # Time bias multiplier
        age_days = (now - row["timestamp"]) / 86400
        if time_bias == "recent":
            recency = 1.0 + 0.2 * max(0.0, 1.0 - age_days / 7.0)
        elif time_bias == "distant":
            recency = 1.0 + 0.1 * min(age_days / 7.0, 1.0)
        else:
            recency = 1.0

        origin = row["origin"] if "origin" in row.keys() else "lived"
        if apply_seed_weight and origin == "seed":
            origin_weight = _seed_weight(row["timestamp"])
        else:
            origin_weight = 1.0

        scored.append((sim * recency * origin_weight, row))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored


# ── Recall-pool fast path (D-0453 (a), J-2275, 2026-10-17) ──────────────────────────────────────────────
# retrieve() used to `SELECT *` every eligible row (41k rows, ~64 MB of embedding BLOBs + ~22 MB of content)
# on every call and score them one Python loop at a time: 393 ms SQL + 142 ms scoring median since the
# 10-16 boot, growing ~2k rows/day. The budget (RETRIEVE_LATENCY_BUDGET_MS) is met by loading LESS, with
# the returned set identical to the legacy path (verified old-vs-new on a .backup() copy, see
# scripts/_test_retrieve_fast_pool.py):
#   1. MEMBERSHIP comes from the covering partial index idx_retrieve_pool_cover: the same WHERE as before,
#      only the small columns (no BLOBs, no content), ordered by rowid in Python so ties sort exactly as
#      the legacy (cold, rowid) index order did.
#   2. EMBEDDINGS live in an in-process float32 matrix keyed by fragment_id and validated by the row's
#      `timestamp`: every live writer that rewrites an embedding in place (activity_memory, refinery,
#      scripts/activity_memory_backfill) also rewrites timestamp, so a changed timestamp = re-fetch. Rows
#      that leave the pool (cold, chaptered, hidden) simply stop being selected; new rows are fetched by id.
#      Cosine is one matrix-vector product instead of 41k np.dot calls.
#   3. CONTENT is fetched by id only for the ~13 rows actually returned (plus the probe's 5 recent world
#      rows), after selection.
# The legacy full-SELECT path is kept verbatim and is used when the embedder is down (query_vec None --
# every row then needs its content for the keyword fallback), for a farewell query (D-0442 needs every
# row's content), or if the fast path raises. Kill switch: _RETRIEVE_FAST_PATH = False.
_RETRIEVE_FAST_PATH = True
_POOL_SQL_WHERE = ("FROM memory_fragments WHERE cold = 0 AND temp != 'hidden' "
                   "AND origin != 'system_note' "   # J-1955 (D-0368 E): system sentences are never recalled as his thought
                   "AND layer != 'dormant' "         # J-2018 (D-0400 B): night thoughts are walled by LAYER too, not only cold=1
                   "AND (chapter_id IS NULL OR chapter_id = '')")
_EMB_LOCK = threading.Lock()
_EMB_INDEX: dict[str, int] = {}          # fragment_id -> row in _EMB_MAT
_EMB_TS: np.ndarray | None = None        # timestamp the cached vector was read at, per row
_EMB_MAT: np.ndarray | None = None       # float32 (capacity, dim); rows [0:_EMB_N) used
_EMB_N = 0
_EMB_DIM = 0
_EMB_FETCH_CHUNK = 900


class _PoolRow:
    """sqlite3.Row-shaped view (row["col"], row.keys()) over a cached pool entry, so the rest of retrieve()
    and its observe-only side channels read it exactly as they read a real Row. Backed by the membership
    tuple (rowid, fragment_id, layer, timestamp, origin, has_emb) plus the cosine; the columns a returned
    row needs (content, keywords, abstraction_level, ...) arrive later via _hydrate_rows into `_x`.
    `cold` is 0 and `chapter_id` None by construction of the pool WHERE."""
    __slots__ = ("_t", "_sim", "_x")
    _COLS = {"fragment_id": 1, "layer": 2, "timestamp": 3, "origin": 4}
    _FIXED = ("fragment_id", "layer", "timestamp", "origin", "cold", "chapter_id", "_sim")

    def __init__(self, t: tuple, sim: float):
        self._t = t
        self._sim = sim
        self._x = None

    def __getitem__(self, k):
        i = self._COLS.get(k)
        if i is not None:
            return self._t[i]
        if k == "_sim":
            return self._sim
        if k == "cold":
            return 0
        if k == "chapter_id":
            return None
        if self._x is not None and k in self._x:
            return self._x[k]
        raise IndexError(f"No item with that key: {k}")

    def keys(self):
        return list(self._FIXED) + (list(self._x) if self._x else [])

    def __contains__(self, k):
        return k in self._COLS or k in ("_sim", "cold", "chapter_id") or (self._x is not None and k in self._x)


_EMB_GEN = 0                             # J-2612: bumped by every _emb_reset(); the pool-delta cache holds slots into _EMB_MAT


def _emb_reset() -> None:
    global _EMB_INDEX, _EMB_TS, _EMB_MAT, _EMB_N, _EMB_DIM, _EMB_GEN
    _EMB_INDEX, _EMB_TS, _EMB_MAT, _EMB_N, _EMB_DIM = {}, None, None, 0, 0
    _EMB_GEN += 1


def _emb_fetch(conn, need: list[tuple[str, float]]) -> None:
    """Fetch the embedding BLOBs for (fragment_id, timestamp) pairs and store them in the matrix (append, or
    overwrite the row's old slot). Caller holds _EMB_LOCK."""
    global _EMB_TS, _EMB_MAT, _EMB_N, _EMB_DIM
    if not need:
        return
    _t_ef = time.perf_counter()   # J-3714
    try:
        _emb_fetch_body(conn, need)
    finally:
        _ph_add("emb_fetch_ms", (time.perf_counter() - _t_ef) * 1000.0, "emb_fetch_n", len(need))


def _emb_fetch_body(conn, need: list[tuple[str, float]]) -> None:
    global _EMB_TS, _EMB_MAT, _EMB_N, _EMB_DIM
    ts_of = dict(need)
    ids = list(ts_of)
    for i in range(0, len(ids), _EMB_FETCH_CHUNK):
        chunk = ids[i:i + _EMB_FETCH_CHUNK]
        ph = ",".join("?" * len(chunk))
        for fid, blob in conn.execute(
                f"SELECT fragment_id, embedding FROM memory_fragments WHERE fragment_id IN ({ph})", chunk):
            if not blob:
                continue
            vec = _blob_to_vec(blob)
            if _EMB_DIM == 0:
                _EMB_DIM = int(vec.shape[0])
            if vec.shape[0] != _EMB_DIM:
                continue   # malformed blob: left out of the matrix, scored by the keyword fallback below
            slot = _EMB_INDEX.get(fid)
            if slot is None:
                if _EMB_MAT is None or _EMB_N >= _EMB_MAT.shape[0]:
                    cap = max(4096, int((_EMB_N + 1) * 1.5))
                    new_mat = np.zeros((cap, _EMB_DIM), dtype=np.float32)
                    new_ts = np.zeros(cap, dtype=np.float64)
                    if _EMB_MAT is not None and _EMB_N:
                        new_mat[:_EMB_N] = _EMB_MAT[:_EMB_N]
                        new_ts[:_EMB_N] = _EMB_TS[:_EMB_N]
                    _EMB_MAT, _EMB_TS = new_mat, new_ts
                slot = _EMB_N
                _EMB_INDEX[fid] = slot
                _EMB_N += 1
            _EMB_MAT[slot] = vec
            _EMB_TS[slot] = ts_of[fid]


def _load_pool_fast(conn, query_vec, all_keys: list[str]) -> list:
    """The retrieve-eligible pool as _PoolRow objects in legacy (rowid) order, each carrying its cosine to
    query_vec under "_sim" (keyword-fallback formula for rows without a usable embedding, exactly as
    _score_tier computes it). Only small columns cross the SQL boundary; see the block comment above."""
    global _EMB_N
    cur = conn.cursor()
    cur.row_factory = None   # plain tuples: ~40k rows, sqlite3.Row construction is measurable here
    _t_ms = time.perf_counter()   # J-3714
    rows = cur.execute(
        "SELECT rowid, fragment_id, layer, timestamp, origin, "
        "(embedding IS NOT NULL AND length(embedding) > 0) AS has_emb " + _POOL_SQL_WHERE).fetchall()
    _ph_add("member_select_ms", (time.perf_counter() - _t_ms) * 1000.0)
    if not rows:
        return []
    n = len(rows)
    rid = np.fromiter((r[0] for r in rows), dtype=np.int64, count=n)
    order = np.argsort(rid, kind="stable")
    rows = [rows[i] for i in order]
    with _TimedLock(_EMB_LOCK, "emb_lock_wait_ms"):
        # compact when the matrix carries far more rows than the pool (rows that went cold/chaptered)
        if _EMB_N > n * 1.5 + 2000:
            _emb_reset()
        idx_get = _EMB_INDEX.get
        ts_arr = _EMB_TS
        need = []
        slots = [-1] * n
        for i, r in enumerate(rows):
            if not r[5]:
                continue
            slot = idx_get(r[1])
            if slot is None or ts_arr[slot] != r[3]:
                need.append((r[1], r[3]))
            else:
                slots[i] = slot
        if need:
            _emb_fetch(conn, need)
            idx_get = _EMB_INDEX.get
            for i, r in enumerate(rows):
                if r[5] and slots[i] < 0:
                    slots[i] = idx_get(r[1], -1)
        q = np.asarray(query_vec, dtype=np.float32)
        sims_all = (_EMB_MAT[:_EMB_N] @ q) if _EMB_N else np.zeros(1, dtype=np.float32)
    slots_a = np.asarray(slots, dtype=np.int64)
    sims = np.where(slots_a >= 0, sims_all[np.maximum(slots_a, 0)], np.nan).astype(np.float64).tolist()
    out = [_PoolRow(r, sim) for r, sim in zip(rows, sims)]
    missing = [pr for pr in out if pr._sim != pr._sim]   # NaN: no usable embedding -> keyword fallback
    if missing:
        _hydrate_rows(conn, missing)
        for pr in missing:
            text_lower = (pr["content"] or "").lower() + " " + (pr["keywords"] or "").lower()
            matches = sum(1 for k in all_keys if k.lower() in text_lower)
            pr._sim = matches / max(len(all_keys), 1) * 0.6
    return out


# ── Recall-pool DELTA cache (J-2612, F-3340; plan memory_levels_plan; D-0453 (a) follow-up) ───────────────
# F-3340 (J-2308): the fast path's median is 214.8 ms against the 250 ms budget (27 percent of calls over, p90 449).
# J-2612 profiled _load_pool_fast on a .backup() copy of the live DB (45k-row pool, uncontended, warm):
#   membership fetchall 62 ms + rowid argsort 8 + per-row cache-slot loop 22 + cosine matmul 1.4 + _PoolRow build 13
#   = ~116 ms, i.e. ~92 ms of it is O(pool) Python/SQL work whose only job is to re-derive a membership list that
#   changed by a handful of rows since the previous call (live Du's GIL/page-cache contention is what stretches 116
#   to the observed 171 ms). The pool does NOT grow fast (rows_fetched flat), so this is a constant to remove, not a
#   slope to chase.
# This block keeps the membership list (rowid-ordered tuples + each row's embedding-matrix slot) between calls and
# patches it from an EXACT change log instead of re-reading the pool:
#   * table memory_pool_changes(seq AUTOINCREMENT, fragment_id) + three triggers on memory_fragments (AFTER INSERT,
#     AFTER UPDATE OF the columns that decide pool membership / the cached vector, AFTER DELETE). Every writer, in any
#     process, is covered because the triggers live in the DB file, not in a Python call site.
#   * a call reads `seq > last_seq`, re-reads ONLY those fragment_ids through the same _POOL_SQL_WHERE, and
#     remove/insert-bisects them into the sorted list. Exact (not a superset): same rows, same legacy rowid order.
#   * anything it cannot prove falls back to a FULL rebuild (same query as _load_pool_fast): a gap in the change
#     log (pruned, or a second consumer), more than _POOL_DELTA_MAX_CHANGES entries, _emb_reset() (slots moved),
#     a rowid collision, a missing table. Any exception falls back to _load_pool_fast for that call.
# Known out-of-contract case: a VACUUM that renumbers rowids fires no trigger; call _pool_invalidate() from any
# VACUUM site (none exists in the repo today, grep 2026-10-31). A shadow-mode mismatch would catch it too.
# MODE (module constant, restart-gated like _RETRIEVE_FAST_PATH): "off" = nothing happens, no table, no triggers,
# retrieve() byte-identical to before; "shadow" = triggers + table installed by init_db, retrieve() still SERVES
# _load_pool_fast, and every _POOL_SHADOW_EVERY-th call (after the latency probe bracket, so the probe stays honest)
# runs fast-load and delta-load in ONE read snapshot and logs whether they are identical (data/pool_delta_shadow.jsonl);
# "on" = delta serves, _load_pool_fast is the fallback. Flipping off -> shadow -> on is a founder call (decide.py).
_POOL_DELTA_MODE = "on"           # D-0526 (travis 2026-11-01): straight to "on", shadow step skipped; restart-gated. Kill switch: "off".
_POOL_DELTA_MAX_CHANGES = 3000
_POOL_SHADOW_EVERY = 5
_POOL_CHANGES_KEEP = 10000        # init_db prunes the change log down to the newest N entries at boot
_POOL_DELTA_SHADOW_LOG = Path(__file__).parent.parent.parent / "data" / "pool_delta_shadow.jsonl"
# J-2677 (F-3425): the TIDY half of "cheap approximate update + periodic TIDY". The delta above is EXACT for every write
# that fires a trigger, so inside that contract a row that left the pool (cold=1, hidden, dormant, chaptered, deleted)
# is dropped on the very next call (bound: 0 calls). The TIDY covers what the triggers cannot see (a VACUUM that
# renumbers rowids, a DB file swapped under the process, a trigger dropped by hand): every _POOL_TIDY_EVERY_S seconds the
# next delta call also runs the full membership SELECT in the same snapshot, compares it with the patched cache, and on
# ANY difference logs it and rebuilds. Out-of-contract bound on a stale/demoted row staying recallable = _POOL_TIDY_EVERY_S
# (30 min). This is also the only LIVE delta-vs-full identity log (D-0526 skipped shadow): every TIDY appends one row to
# data/pool_delta_tidy.jsonl {identical, n_cache, n_full, only_in_cache, only_in_full, changed_rows, ms}; its reader is the
# follow-up read job spawned by J-2677. The retrieve latency probe rows now also carry pool_rebuilt / pool_changed (how
# many pool rows the delta patched that call), which is the per-call "rows that changed" measurement.
# Kill switch: _POOL_TIDY_EVERY_S = 0 (no TIDY; J-2612 behaviour exactly). Restart-gated like _POOL_DELTA_MODE.
_POOL_TIDY_EVERY_S = 1800.0
_POOL_TIDY_LOG = Path(__file__).parent.parent.parent / "data" / "pool_delta_tidy.jsonl"
_pool_tidy_log_lock = threading.Lock()
_POOL_LOCK = threading.Lock()     # taken BEFORE _EMB_LOCK, never the other way round
_pool_shadow_calls = 0
_pool_delta_warned = 0.0
_pool_shadow_log_lock = threading.Lock()


class _PoolState:
    """The cached pool: rids/tups/slots are parallel lists sorted by rowid (the legacy (cold, rowid) order);
    by_fid maps fragment_id -> rowid; seq is the last change-log entry applied; gen is the _EMB_GEN the slots
    were taken at; stats describe the last call (what the shadow log reports)."""
    __slots__ = ("rids", "tups", "slots", "by_fid", "seq", "gen", "valid", "stats", "tidy_t")

    def __init__(self):
        self.clear()

    def clear(self):
        self.rids, self.tups, self.slots, self.by_fid = [], [], [], {}
        self.seq, self.gen, self.valid = -1, -1, False
        self.stats = {"rebuilt": False, "changed": 0}
        self.tidy_t = 0.0                  # J-2677: monotonic time of the last full membership check (rebuild or TIDY)


_POOL = _PoolState()


def _pool_invalidate() -> None:
    """Drop the cached pool (next delta call does a full rebuild). Call after anything that renumbers rowids."""
    with _POOL_LOCK:
        _POOL.clear()


def _init_pool_changes(conn) -> None:
    """Create the change log + its triggers (only when _POOL_DELTA_MODE != "off"). Additive: a trigger only
    appends a (seq, fragment_id) row; with the table unread it costs one tiny insert per membership-relevant write.
    Also trims the log to the newest _POOL_CHANGES_KEEP entries -- at boot no consumer is mid-read in this
    process, and a stale consumer elsewhere sees the gap and rebuilds."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS memory_pool_changes (
            seq         INTEGER PRIMARY KEY AUTOINCREMENT,
            fragment_id TEXT NOT NULL
        );
        CREATE TRIGGER IF NOT EXISTS trg_pool_chg_ins AFTER INSERT ON memory_fragments
        BEGIN
            INSERT INTO memory_pool_changes(fragment_id) VALUES (NEW.fragment_id);
        END;
        CREATE TRIGGER IF NOT EXISTS trg_pool_chg_upd
        AFTER UPDATE OF fragment_id, layer, timestamp, origin, cold, temp, chapter_id, embedding ON memory_fragments
        BEGIN
            INSERT INTO memory_pool_changes(fragment_id) VALUES (NEW.fragment_id);
            INSERT INTO memory_pool_changes(fragment_id) SELECT OLD.fragment_id WHERE OLD.fragment_id IS NOT NEW.fragment_id;
        END;
        CREATE TRIGGER IF NOT EXISTS trg_pool_chg_del AFTER DELETE ON memory_fragments
        BEGIN
            INSERT INTO memory_pool_changes(fragment_id) VALUES (OLD.fragment_id);
        END;
    """)
    conn.execute("DELETE FROM memory_pool_changes WHERE seq <= "
                 "(SELECT COALESCE(MAX(seq), 0) FROM memory_pool_changes) - ?", (_POOL_CHANGES_KEEP,))


def _pool_select_sql(extra: str = "", by_key: bool = False) -> str:
    """The membership query. by_key=True is for `AND fragment_id IN (...)` re-reads: the unary plus on `cold` keeps
    the planner off the covering partial index (which it prefers, and which would scan all 45k rows = 25 ms to
    return 5) and on the fragment_id primary-key index (0.2 ms). Same rows either way -- the unary plus is a no-op
    to the value."""
    where = _POOL_SQL_WHERE.replace("cold = 0", "+cold = 0", 1) if by_key else _POOL_SQL_WHERE
    if by_key:
        # J-3712 (F-4334): with >= 9 changed ids the planner abandons the PK index for a MULTI-INDEX OR over
        # idx_chapter and scans (live median 429 ms vs 20 ms). Unary plus on chapter_id keeps it on the PK.
        where = where.replace("(chapter_id IS NULL OR chapter_id = '')",
                              "(+chapter_id IS NULL OR +chapter_id = '')", 1)
    return ("SELECT rowid, fragment_id, layer, timestamp, origin, "
            "(embedding IS NOT NULL AND length(embedding) > 0) AS has_emb " + where + extra)


def _pool_assign_slots(conn, tups: list) -> tuple[list[int], int]:
    """Embedding-matrix slot per pool tuple (-1 = no usable vector), fetching vectors whose cached timestamp is
    missing/stale -- the exact rule _load_pool_fast applies. Returns (slots, the _EMB_GEN they are valid for)."""
    with _TimedLock(_EMB_LOCK, "emb_lock_wait_ms"):
        idx_get = _EMB_INDEX.get
        ts_arr = _EMB_TS
        slots = [-1] * len(tups)
        need = []
        for i, r in enumerate(tups):
            if not r[5]:
                continue
            slot = idx_get(r[1])
            if slot is None or ts_arr[slot] != r[3]:
                need.append((r[1], r[3]))
            else:
                slots[i] = slot
        if need:
            _emb_fetch(conn, need)
            idx_get = _EMB_INDEX.get
            for i, r in enumerate(tups):
                if r[5] and slots[i] < 0:
                    slots[i] = idx_get(r[1], -1)
        return slots, _EMB_GEN


def _pool_rebuild(cur, conn, st: _PoolState) -> None:
    st.clear()
    seq = cur.execute("SELECT COALESCE((SELECT seq FROM sqlite_sequence WHERE name = 'memory_pool_changes'), 0)"
                      ).fetchone()[0]
    _t_ms = time.perf_counter()   # J-3714
    rows = cur.execute(_pool_select_sql()).fetchall()
    _ph_add("member_select_ms", (time.perf_counter() - _t_ms) * 1000.0)
    rows.sort(key=lambda r: r[0])
    with _TimedLock(_EMB_LOCK, "emb_lock_wait_ms"):
        if _EMB_N > len(rows) * 1.5 + 2000:
            _emb_reset()          # same compaction rule as _load_pool_fast
    slots, gen = _pool_assign_slots(conn, rows)
    st.rids = [r[0] for r in rows]
    st.tups = rows
    st.slots = slots
    st.by_fid = {r[1]: r[0] for r in rows}
    st.seq, st.gen, st.valid = seq, gen, True
    st.stats = {"rebuilt": True, "changed": len(rows)}
    st.tidy_t = time.monotonic()


def _pool_apply_delta(cur, conn, st: _PoolState) -> bool:
    """Patch the cached pool from the change log. False = could not prove an exact patch (caller rebuilds); the
    state may then be half-patched, which is fine because a rebuild starts with st.clear()."""
    import bisect
    changes = cur.execute("SELECT seq, fragment_id FROM memory_pool_changes WHERE seq > ? ORDER BY seq",
                          (st.seq,)).fetchall()
    st.stats = {"rebuilt": False, "changed": 0}
    if not changes:
        return True
    if changes[0][0] != st.seq + 1 or changes[-1][0] - st.seq != len(changes):
        return False                                   # gap: pruned, or another consumer's gap
    fids = list({c[1] for c in changes})
    if len(fids) > _POOL_DELTA_MAX_CHANGES:
        return False
    current: dict[str, tuple] = {}
    for i in range(0, len(fids), _EMB_FETCH_CHUNK):
        chunk = fids[i:i + _EMB_FETCH_CHUNK]
        ph = ",".join("?" * len(chunk))
        for r in cur.execute(_pool_select_sql(f" AND fragment_id IN ({ph})", by_key=True), chunk):
            current[r[1]] = r
    for fid in fids:                                   # removals first (a freed rowid may be reused by another fid)
        old = st.by_fid.pop(fid, None)
        if old is not None:
            i = bisect.bisect_left(st.rids, old)
            if i >= len(st.rids) or st.rids[i] != old or st.tups[i][1] != fid:
                return False
            del st.rids[i], st.tups[i], st.slots[i]
    new_rows = sorted(current.values(), key=lambda r: r[0])
    if new_rows:
        slots, gen = _pool_assign_slots(conn, new_rows)
        if gen != st.gen:
            return False                               # the matrix was compacted under us: slots moved
        for r, sl in zip(new_rows, slots):
            i = bisect.bisect_left(st.rids, r[0])
            if i < len(st.rids) and st.rids[i] == r[0]:
                return False                           # rowid collision with a different fragment: do not guess
            st.rids.insert(i, r[0])
            st.tups.insert(i, r)
            st.slots.insert(i, sl)
            st.by_fid[r[1]] = r[0]
    if _EMB_N > len(st.rids) * 1.5 + 2000:
        return False                                   # matrix mostly dead rows: rebuild compacts it
    st.seq = changes[-1][0]
    st.stats = {"rebuilt": False, "changed": len(fids)}
    return True


def _pool_tidy(cur, conn, st: _PoolState) -> None:
    """J-2677: compare the delta-patched cache with a fresh full membership SELECT (same snapshot as the delta read).
    Identical -> restart the TIDY timer. Different -> log what differed and rebuild from scratch. Always logs one row
    (best-effort). Raises only what _pool_rebuild raises; the caller's except clears the cache and falls back."""
    t0 = time.perf_counter()
    fresh = cur.execute(_pool_select_sql()).fetchall()
    fresh.sort(key=lambda r: r[0])
    identical = fresh == st.tups
    rec = {"timestamp": time.time(), "identical": identical, "n_cache": len(st.tups), "n_full": len(fresh)}
    if not identical:
        a = {r[1]: r for r in st.tups}
        b = {r[1]: r for r in fresh}
        rec["only_in_cache"] = len(a.keys() - b.keys())
        rec["only_in_full"] = len(b.keys() - a.keys())
        rec["changed_rows"] = sum(1 for k in a.keys() & b.keys() if a[k] != b[k])
        rec["order_only"] = bool(rec["only_in_cache"] == 0 and rec["only_in_full"] == 0 and rec["changed_rows"] == 0)
        _pool_rebuild(cur, conn, st)
    else:
        st.tidy_t = time.monotonic()
    rec["ms"] = round((time.perf_counter() - t0) * 1000.0, 3)
    try:
        with _pool_tidy_log_lock, open(_POOL_TIDY_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
    except Exception as exc:
        logger.debug("pool delta tidy log skipped (non-fatal): %s", exc)
    if not identical:
        logger.warning("[retrieve] pool delta TIDY found the cache out of step with the DB (%s); rebuilt", rec)


def _pool_keyword_fallback(conn, out: list, all_keys: list[str]) -> None:
    """Rows with no usable embedding (NaN cosine) score by keyword overlap -- identical to _load_pool_fast."""
    missing = [pr for pr in out if pr._sim != pr._sim]
    if missing:
        _hydrate_rows(conn, missing)
        for pr in missing:
            text_lower = (pr["content"] or "").lower() + " " + (pr["keywords"] or "").lower()
            matches = sum(1 for k in all_keys if k.lower() in text_lower)
            pr._sim = matches / max(len(all_keys), 1) * 0.6


def _load_pool_delta(conn, query_vec, all_keys: list[str]) -> list:
    """Same contract and same result as _load_pool_fast (rowid-ordered _PoolRow list with cosines), but the
    membership list is patched from the change log instead of re-read. Raises on anything unexpected; the caller
    falls back to _load_pool_fast."""
    with _TimedLock(_POOL_LOCK, "pool_lock_wait_ms"):
        st = _POOL
        cur = conn.cursor()
        cur.row_factory = None
        began = not conn.in_transaction
        if began:
            cur.execute("BEGIN")                       # ONE snapshot for the change log and the re-read rows
        try:
            try:
                _t_md = time.perf_counter()   # J-3714: delta membership phase = change-log read + patch, minus any BLOB fill inside
                _ef0 = _ph_get("emb_fetch_ms")
                ok = st.valid and st.gen == _EMB_GEN and _pool_apply_delta(cur, conn, st)
                if ok:
                    _ph_add("member_select_ms", (time.perf_counter() - _t_md) * 1000.0 - (_ph_get("emb_fetch_ms") - _ef0))
                if not ok:
                    _pool_rebuild(cur, conn, st)
                elif _POOL_TIDY_EVERY_S > 0 and time.monotonic() - st.tidy_t >= _POOL_TIDY_EVERY_S:
                    _pool_tidy(cur, conn, st)             # J-2677
            except Exception:
                st.clear()
                raise
            q = np.asarray(query_vec, dtype=np.float32)
            with _TimedLock(_EMB_LOCK, "emb_lock_wait_ms"):
                if st.gen != _EMB_GEN:
                    st.clear()
                    raise RuntimeError("embedding matrix reset during delta load")
                _tm = time.perf_counter()
                sims_all = (_EMB_MAT[:_EMB_N] @ q) if _EMB_N else np.zeros(1, dtype=np.float32)
                _ph_add("delta_matmul_ms", (time.perf_counter() - _tm) * 1000.0)
            # J-4065 (F-4807): observation-only timers for the formerly untimed residual, extra keys on the probe row.
            _t1 = time.perf_counter()
            slots_a = np.asarray(st.slots, dtype=np.int64)
            sims = np.where(slots_a >= 0, sims_all[np.maximum(slots_a, 0)], np.nan).astype(np.float64).tolist()
            _t2 = time.perf_counter()
            out = [_PoolRow(t, sim) for t, sim in zip(st.tups, sims)]
            _t3 = time.perf_counter()
            _pool_keyword_fallback(conn, out, all_keys)
            _t4 = time.perf_counter()
            _ph_add("delta_slots_ms", (_t2 - _t1) * 1000.0)       # asarray + gather + tolist
            _ph_add("delta_rows_ms", (_t3 - _t2) * 1000.0, "delta_rows_n", len(out))   # _PoolRow list build
            _ph_add("delta_kwfb_ms", (_t4 - _t3) * 1000.0)        # keyword fallback (incl. any hydrate)
            return out
        finally:
            if began:
                conn.rollback()


def _load_pool(conn, query_vec, all_keys: list[str]) -> tuple[list, str]:
    """retrieve()'s pool loader: (rows, path label). "off"/"shadow" serve _load_pool_fast exactly as before."""
    if _POOL_DELTA_MODE == "on":
        try:
            return _load_pool_delta(conn, query_vec, all_keys), "fast+delta"
        except Exception as exc:
            global _pool_delta_warned
            if time.time() - _pool_delta_warned > _BUDGET_WARN_INTERVAL_S:   # rate-limited like the budget warning
                _pool_delta_warned = time.time()
                logger.warning("[retrieve] pool delta path failed (%s: %s); using _load_pool_fast this call",
                               type(exc).__name__, exc)
    return _load_pool_fast(conn, query_vec, all_keys), "fast"


def pool_embedding_view() -> dict | None:
    """J-3310 (D-0552, docs/reviews/memory_router_keys_shadow_design_J-3163.md section 3.2): a READ-ONLY view of the
    cached recall pool for the key-shadow instrument (core/memory/key_shadow.py). ADDITIVE: retrieve() does not call
    it and no SQL runs here. Returns None unless the pool-delta cache is serving ("on" mode, valid, slots taken at the
    current matrix generation); otherwise a dict:
      mat    float32 (n_used, dim) VIEW of the embedding matrix (not copied; rows may be rewritten in place by a
             concurrent _emb_fetch, which at worst skews one row's score in a shadow log)
      tups   shallow copy of the pool membership tuples (rowid, fragment_id, layer, timestamp, origin, has_emb),
             rowid-ordered, the same order retrieve() scores in
      slots  shallow copy of the parallel matrix-slot list (-1 = no usable vector)
      gen, seq   the matrix generation and change-log position the snapshot was taken at
    Lock order is the documented one (_POOL_LOCK, then _EMB_LOCK). The caller must treat everything as read-only."""
    if _POOL_DELTA_MODE != "on":
        return None
    with _POOL_LOCK:
        st = _POOL
        if not st.valid or not st.rids:
            return None
        with _EMB_LOCK:
            if st.gen != _EMB_GEN or _EMB_MAT is None or not _EMB_N:
                return None
            return {"mat": _EMB_MAT[:_EMB_N], "tups": list(st.tups), "slots": list(st.slots),
                    "gen": _EMB_GEN, "seq": st.seq}


def _pool_shadow_check(query_vec, all_keys: list[str]) -> None:
    """Shadow mode: every _POOL_SHADOW_EVERY-th call, load the pool BOTH ways inside one read snapshot and log
    whether they are identical (membership tuples, order, cosines). Never raises, never changes a retrieve()."""
    global _pool_shadow_calls
    if _POOL_DELTA_MODE != "shadow":
        return
    _pool_shadow_calls += 1
    if _pool_shadow_calls > 3 and _pool_shadow_calls % max(1, _POOL_SHADOW_EVERY):
        return
    rec = {"timestamp": time.time(), "call": _pool_shadow_calls}
    try:
        with _connect() as conn:
            conn.execute("BEGIN")
            try:
                t0 = time.perf_counter()
                a = _load_pool_fast(conn, query_vec, all_keys)
                t1 = time.perf_counter()
                b = _load_pool_delta(conn, query_vec, all_keys)
                t2 = time.perf_counter()
            finally:
                conn.rollback()
        same_t = [r._t for r in a] == [r._t for r in b]
        sa = np.fromiter((r._sim for r in a), dtype=np.float64, count=len(a))
        sb = np.fromiter((r._sim for r in b), dtype=np.float64, count=len(b))
        same_s = len(a) == len(b) and bool(np.all(np.abs(sa - sb) <= 1e-6))
        rec.update({"n_fast": len(a), "n_delta": len(b), "same_membership_and_order": same_t, "same_sims": same_s,
                    "ms_fast": round((t1 - t0) * 1000.0, 3), "ms_delta": round((t2 - t1) * 1000.0, 3),
                    "delta_rebuilt": _POOL.stats.get("rebuilt"), "delta_changed": _POOL.stats.get("changed"),
                    "identical": bool(same_t and same_s)})
        if not rec["identical"]:
            _pool_invalidate()                        # next delta call rebuilds from scratch
    except Exception as exc:
        rec.update({"error": f"{type(exc).__name__}: {exc}", "identical": None})
    try:
        with _pool_shadow_log_lock, open(_POOL_DELTA_SHADOW_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
    except Exception as exc:
        logger.debug("pool delta shadow log skipped (non-fatal): %s", exc)


def _hydrate_rows(conn, rows: list) -> None:
    """Fill content / keywords / the remaining returned columns for a handful of _PoolRow objects by id.
    A row deleted between the two queries (never, by policy) gets empty strings rather than an error."""
    todo = [r for r in rows if isinstance(r, _PoolRow) and r._x is None]
    if not todo:
        return
    by_id = {r["fragment_id"]: r for r in todo}
    ids = list(by_id)
    for i in range(0, len(ids), _EMB_FETCH_CHUNK):
        chunk = ids[i:i + _EMB_FETCH_CHUNK]
        ph = ",".join("?" * len(chunk))
        try:
            _recs = conn.execute(
                "SELECT fragment_id, content, keywords, abstraction_level, relevance, importance, replay_count, "
                f"derived_from, input_type FROM memory_fragments WHERE fragment_id IN ({ph})", chunk).fetchall()
        except sqlite3.OperationalError:   # J-3173: a DB not yet migrated has no input_type -- the old columns still serve
            _recs = [tuple(x) + (None,) for x in conn.execute(
                "SELECT fragment_id, content, keywords, abstraction_level, relevance, importance, replay_count, "
                f"derived_from FROM memory_fragments WHERE fragment_id IN ({ph})", chunk)]
        for rec in _recs:
            by_id[rec[0]]._x = {"content": rec[1], "keywords": rec[2], "abstraction_level": rec[3],
                                "relevance": rec[4], "importance": rec[5], "replay_count": rec[6],
                                "derived_from": rec[7], "input_type": rec[8]}
    for r in todo:
        if r._x is None:
            r._x = {"content": "", "keywords": "", "abstraction_level": 0}


def _score_tier_vec(rows: list, time_bias: Literal["recent", "distant", "all"],
                    apply_seed_weight: bool = True, top: int = 16) -> list[tuple[float, object]]:
    """Vectorised twin of _score_tier for _PoolRow rows (cosine already under "_sim"): the same recency
    and seed-weight formulas, the same stable descending sort (ties keep pool order), returning only the
    top `top` pairs -- the callers read at most scored[:8] and scored[:n_slots]."""
    n = len(rows)
    if n == 0:
        return []
    now = time.time()
    sims = np.fromiter((r._sim for r in rows), dtype=np.float64, count=n)
    ts = np.fromiter((r._t[3] for r in rows), dtype=np.float64, count=n)
    age_days = (now - ts) / 86400.0
    if time_bias == "recent":
        recency = 1.0 + 0.2 * np.maximum(0.0, 1.0 - age_days / 7.0)
    elif time_bias == "distant":
        recency = 1.0 + 0.1 * np.minimum(age_days / 7.0, 1.0)
    else:
        recency = np.ones(n, dtype=np.float64)
    score = sims * recency
    if apply_seed_weight:
        for i, r in enumerate(rows):
            if r["origin"] == "seed":
                score[i] *= _seed_weight(r["timestamp"])
    order = np.argsort(-score, kind="stable")[:top]
    return [(float(score[i]), rows[i]) for i in order]


# ---------------------------------------------------------------------------------------------------
# J-4277 / docs/staged/lod_staged_retrieval.md Steps 1+2 (2026-11-18): LOD staged retrieval, SHADOW ONLY.
# Ports the cascade from scripts/lod_retrieval_lab.py (_build_pools/_score/_lod_staged). Nothing below
# changes what retrieve() returns: LOD_RETRIEVAL_LIVE is declared but never read by retrieve() (Step 3
# would wire it), and the shadow hook is gated by LOD_RETRIEVAL_SHADOW, default OFF.
LOD_RETRIEVAL_LIVE = False
LOD_RETRIEVAL_SHADOW = False
# J-4403 / D-0862(1): valence-term rank SHADOW (observe-only, never alters retrieve() output); default OFF, restart-gated.
VALENCE_RANK_SHADOW = False
_LOD_SHADOW_LOG = Path(__file__).parent.parent.parent / "data" / "lod_retrieval_shadow_live.jsonl"
_LOD_SHADOW_LOCK = threading.Lock()


def _lod_pools() -> tuple[list, list, list]:
    """Pure/unwired: (l0, l1, l2) row lists of retrieve-eligible embedded fragments, split by abstraction_level."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT fragment_id, content, embedding, abstraction_level "
            "FROM memory_fragments WHERE (cold = 0 OR cold IS NULL) "
            "AND (chapter_id IS NULL OR chapter_id = '') AND embedding IS NOT NULL"
        ).fetchall()
    l0, l1, l2 = [], [], []
    for r in rows:
        lvl = r["abstraction_level"] or 0
        (l0 if lvl == 0 else l1 if lvl == 1 else l2).append(r)
    return l0, l1, l2


def _lod_staged_candidates(query_vec, n: int) -> list[tuple[float, object]]:
    """Pure/unwired: ~20% L2 / ~30% L1 / rest L0 slots, filled coarsest-first; a coarse pool's unfilled
    slots cascade to the next finer one (same idiom as retrieve()'s spare_slots). Returns [(cosine, row)]."""
    if query_vec is None or n <= 0:
        return []
    l0, l1, l2 = _lod_pools()
    scored_pools = []
    for pool in (l2, l1, l0):
        sc = [(_cosine(query_vec, _blob_to_vec(r["embedding"])), r) for r in pool]
        sc.sort(key=lambda x: x[0], reverse=True)
        scored_pools.append(sc)
    l2_n = max(1, round(0.2 * n))
    l1_n = max(1, round(0.3 * n))
    l0_n = max(0, n - l2_n - l1_n)
    picked: list = []
    spare = 0
    for base_n, sc in zip((l2_n, l1_n, l0_n), scored_pools):
        take = base_n + spare
        chunk = sc[:take]
        picked.extend(chunk)
        spare = take - len(chunk)
    return picked[:n]


def _lod_shadow_observe(query_text: str, query_vec, baseline_ids: list, n: int) -> None:
    """Observe-only: append {query, baseline ids, lod ids} to data/lod_retrieval_shadow_live.jsonl. Fail-open."""
    try:
        _log = profile.guard_path(_LOD_SHADOW_LOG)
        lod_ids = [r["fragment_id"] for _, r in _lod_staged_candidates(query_vec, n)]
        row = {"ts": time.time(), "query": (query_text or "")[:300], "n": n,
               "baseline_ids": list(baseline_ids), "lod_ids": lod_ids,
               "overlap": len(set(baseline_ids) & set(lod_ids))}
        _log.parent.mkdir(parents=True, exist_ok=True)
        with _LOD_SHADOW_LOCK:
            with open(_log, "a", encoding="utf-8") as f:
                f.write(json.dumps(row) + "\n")
    except Exception as exc:
        logger.debug("lod shadow skipped (non-fatal): %s", exc)


def retrieve(
    episodic_keys: list[str],
    semantic_keys: list[str],
    time_bias: Literal["recent", "distant", "all"] = "recent",
    limit: int = 8,
    query_text: str = "",
    bias_vec=None,
    bias_weight: float = 0.0,
) -> list[MemoryFragment]:
    """
    Return up to `limit` fragments using tier-mixed slot allocation.

    Tier allocation (from TIER_SLOTS — the authoritative constant; this list corrected 2026-07-02):
      archive  — 2 slots, no recency bias (permanent identity, always present)
      semantic — 3 slots, caller's time_bias (Consolidation distillations; 2→3 on 2026-06-16)
      episodic — 4 slots, caller's time_bias (lived experience)

    Within each tier, fragments are ranked by cosine similarity to query_text.
    If a tier has fewer fragments than its slot count, the remainder goes to the
    next lower tier (episodic is the overflow).

    The query embedding is built from query_text (raw_input + perception.summary).
    Falls back to keyword overlap for fragments without an embedding.

    CLIMATE WARP (bias_vec / bias_weight): the orchestrator may pass a normalised climate
    bias vector and a weight in [0,1]. The query embedding is then tilted toward the standing
    psychological weather — query_vec = normalise(query_vec + bias_weight * bias_vec) — so the
    same words retrieve different memories depending on Carl's current climate. A coordinate
    transform of the search space, not a re-ranking hack. bias_weight=0 (default) is a no-op.
    """
    all_keys = list(set(episodic_keys + semantic_keys))
    if not all_keys and not query_text:
        return []

    query_str = query_text if query_text.strip() else " ".join(all_keys)
    query_vec = _embed(query_str)

    # Climate warp — tilt the query toward the active weather, then renormalise so cosine
    # comparisons downstream stay well-formed. Best-effort: any shape/None issue is a no-op.
    if query_vec is not None and bias_vec is not None and bias_weight > 0.0:
        try:
            warped = query_vec + float(bias_weight) * np.asarray(bias_vec, dtype=np.float32)
            norm = float(np.linalg.norm(warped))
            if norm > 0.0:
                query_vec = (warped / norm).astype(np.float32)
        except Exception as exc:
            logger.debug("climate warp skipped (non-fatal): %s", exc)

    # D-0442 (travis, 2026-10-16; J-2245, option A): when THIS query is a /quit farewell, his own prior answers to
    # a farewell (the "Q: <farewell>\nA: ..." cycle fragments _persist_cycle writes) step aside -- F-2360/F-2914's
    # verbatim self-echo recalled his last farewell answer back into the next one. Detector + kill switch:
    # core/farewell_echo.py (same whitespace-normalised read of the human turn as J-1756's rotation). Applied at
    # partition time below, so the recency guarantee cannot re-insert them either. A non-farewell query is untouched.
    # (J-2275: computed here, before the fetch, because a farewell query needs every row's content and so takes
    # the legacy full-SELECT path.)
    _fw_skip_on = False
    _fw_skipped: list = []
    try:
        from core import farewell_echo as _fe
        _fw_skip_on = bool(_fe.RETRIEVE_SKIP_FAREWELL) and _fe.is_farewell(query_text)
    except Exception:
        _fw_skip_on = False

    _phase_begin()   # J-3714: phase attribution starts with the same bracket as the probe
    _t_sql0 = time.perf_counter()  # latency probe (J-0652) -- brackets connect()+execute()+fetchall(), the real per-call SQL cost
    _path = "fast" if (_RETRIEVE_FAST_PATH and query_vec is not None and not _fw_skip_on) else "legacy"
    _path_label = _path   # J-2612: the probe's path column; "fast+delta" when the pool-delta cache served the pool
    all_rows = []
    _pool_stats = None
    if _path == "fast":
        # J-2275 (D-0453): covering-index membership + cached embedding matrix; identical pool, identical
        # WHERE (_POOL_SQL_WHERE), content fetched by id for the returned rows only. See the block above.
        try:
            _t_cn = time.perf_counter()
            _cn = _connect()
            _ph_add("connect_ms", (time.perf_counter() - _t_cn) * 1000.0)   # J-3714
            with _cn as conn:
                all_rows, _path_label = _load_pool(conn, query_vec, all_keys)
                _pool_stats = dict(_POOL.stats) if _path_label == "fast+delta" else None   # J-2677: for the probe row
        except Exception as exc:
            logger.warning("[retrieve] fast pool path failed (%s: %s); using the legacy full SELECT this call",
                           type(exc).__name__, exc)
            _path = "legacy"
            _path_label = "legacy"
            all_rows = []
    if _path == "legacy":
        with _connect() as conn:
            # COLD fragments (demoted by the cap-prune or the memory-levels lattice) are excluded HERE at the
            # SQL level so the growing cold set never bloats normal recall — they stay reachable via deep_recall
            # and intentional direct queries. (Matches the per-row cold-skip below; this just avoids fetching them.)
            # 2026-08-29 (J-0365, §3.7 Axis 4): also excludes temp='hidden' — the spirit-invisible tier (system
            # can read it, Du cannot). Verified in an isolated scratch-DB copy this is a no-op today: identical
            # row count with/without the extra clause, since no live writer sets temp='hidden' yet.
            # SIMPLIFIED 2026-09-23 (J-1282, D-0187, F-1072/F-1094/F-1778): dropped the two OR-IS-NULL branches
            # -- both `cold` and `temp` are schema-level NOT NULL DEFAULT columns (see init_db() above) and a
            # fresh scratch-copy check this same job ran against the CURRENT live DB found 0 actual NULL rows
            # of 104,620, so the branches were dead weight, not a live behavior guard. Dropping them lets the
            # planner use the existing idx_cold index via a targeted SEARCH instead of a full table SCAN
            # (verified fresh, same job: `SCAN memory_fragments` -> `SEARCH memory_fragments USING INDEX
            # idx_cold (cold=?)`), with a byte-identical 37,814-row result set both before and after. J-0747's
            # CONTRACT-coupled-caller due-diligence (orchestrator.py, memory_levels.py, commitment_ledger.py,
            # memory_edges.py, geometry_census.py, inner_monologue_node.py, profile.py, schema.py, refinery.py,
            # scripts/_test_episodic_buffer.py) found no caller depends on either column ever being NULL.
            # Restart-gated: Du is live and was not restarted; this takes effect at his next restart.
            # PUSHED DOWN 2026-10-07 (J-1842, F-2475): the chapter skip below used to run in Python AFTER fetching
            # every chaptered row's full embedding BLOBs (22,466 of 51,549 rows, 44%, fetched then thrown away --
            # data/retrieve_latency_probe.jsonl's sql phase grew 460 -> 714 ms, linear in the active pool). The same
            # test now lives in the WHERE clause: `chapter_id IS NULL OR chapter_id = ''` is exactly the complement
            # of the Python loop's truthiness test (`if row["chapter_id"]: continue`) for a TEXT column. Result set
            # and order are identical (verified old-vs-new over a DB copy, scripts/_test_retrieve_chapter_pushdown.py);
            # idx_retrieve_pool (partial, see init_db) serves it. NOTE for log readers: `all_rows` is now the
            # retrieve-ELIGIBLE pool, so probe `rows_fetched`, r_shadow `pool_n_by_band` and retrieval_probe's
            # `recent_world` stop counting chaptered rows from the first boot after this lands (they never could
            # have been returned). The Python chapter check below is kept as a belt-and-braces no-op.
            all_rows = conn.execute(
                "SELECT * FROM memory_fragments WHERE cold = 0 AND temp != 'hidden' "
                "AND origin != 'system_note' "   # J-1955 (D-0368 E): system sentences are never recalled as his thought
                "AND layer != 'dormant' "         # J-2018 (D-0400 B): night thoughts are walled by LAYER too, not only cold=1
                "AND (chapter_id IS NULL OR chapter_id = '')").fetchall()
    _elapsed_ms_sql = (time.perf_counter() - _t_sql0) * 1000.0
    if _path == "fast" and _POOL_DELTA_MODE == "shadow":
        _pool_shadow_check(query_vec, all_keys)   # J-2612: after the probe bracket, so the latency record stays honest

    if not all_rows:
        _log_retrieve_latency(0, 0, _elapsed_ms_sql, 0.0, path=_path_label, pool_stats=_pool_stats)
        return []

    # Partition rows by tier. Chaptered fragments step aside — their chapter answers
    # for them in ordinary recall; the originals are pristine and reachable only by
    # intentional recollection (2026-06-13, founder: "recalled intentionally").
    by_tier: dict[str, list] = {"archive": [], "semantic": [], "episodic": [], "working": []}
    for row in all_rows:
        try:
            if _fw_skip_on and _fe.fragment_answers_farewell(row["content"]):
                _fw_skipped.append(row["fragment_id"])
                continue
        except Exception:
            pass
        try:
            if "chapter_id" in row.keys() and row["chapter_id"]:
                continue
            # MEMORY LEVELS Phase 1 (2026-06-18): COLD (demoted) raw steps aside from NORMAL recall — its
            # gist now answers for it; the raw is reachable by deep_recall (link traversal) and by intentional
            # direct queries (essay-gather etc.), never lost. Mirrors the chapter-skip above. This is the
            # loop-break: the verbatim river stops surfacing here once it has a faithful gist.
            if "cold" in row.keys() and row["cold"]:
                continue
        except Exception:
            pass
        tier = row["layer"] if row["layer"] in by_tier else "episodic"
        by_tier[tier].append(row)

    if _fw_skipped:
        logger.info("[farewell-echo] retrieve skipped %d prior farewell answer(s) (D-0442 A)", len(_fw_skipped))
        try:
            _fe.log_retrieve_skip(query_text, _fw_skipped)
        except Exception:
            pass

    result_rows: list[tuple[float, object]] = []
    spare_slots = 0  # unfilled slots cascade down to episodic
    _probe_pool: list = []  # (Phase 0 observe-only) scored candidates considered, for the probe
    _episodic_tier_n = len(by_tier.get("episodic", []))  # latency probe (J-0652): the pool F-0925/D-0173 are about
    _elapsed_ms_score = 0.0

    for tier, n_slots in TIER_SLOTS.items():
        n_slots += spare_slots
        spare_slots = 0

        tier_time_bias = "all" if tier == "archive" else time_bias
        _t_score0 = time.perf_counter()  # latency probe (J-0652)
        if _path == "fast":
            scored = _score_tier_vec(by_tier[tier], time_bias=tier_time_bias,
                                     apply_seed_weight=(tier != "archive"), top=max(16, n_slots))
        else:
            scored = _score_tier(
                by_tier[tier], query_vec, all_keys,
                time_bias=tier_time_bias,
                apply_seed_weight=(tier != "archive"),  # archive slots are always included; SEED_WEIGHT applies within-tier only when lived archive frags exist
            )
        _elapsed_ms_score += (time.perf_counter() - _t_score0) * 1000.0
        # capture the top of each tier's scored candidates as the "pool" the probe sees
        for s, r in scored[:8]:
            _probe_pool.append((s, r["origin"] if "origin" in r.keys() else "lived",
                                r["fragment_id"]))
        taken = scored[:n_slots]
        result_rows.extend(taken)

        # Unused slots from this tier overflow to episodic (cascades to last tier)
        if tier != "episodic":
            spare_slots = n_slots - len(taken)

    _log_retrieve_latency(len(all_rows), _episodic_tier_n, _elapsed_ms_sql, _elapsed_ms_score, path=_path_label, pool_stats=_pool_stats)

    # De-duplicate (shouldn't happen, but guard against it)
    seen: set[str] = set()
    unique: list[tuple[float, object]] = []
    for score, row in result_rows:
        fid = row["fragment_id"]
        if fid not in seen:
            seen.add(fid)
            unique.append((score, row))

    # Recency guarantee — ensure the 5 most-recent episodic fragments always appear
    # in the result set. Without this, seed/semantic fragments that are broadly similar
    # to the query crowd out recent exchanges. Guaranteed items are inserted at position 2
    # (after the top-1 similarity hit) so they survive the [:4] display cap in Executive.
    # 5 fragments gives ~5 recent Q→A pairs as "sticky" working context — exactly the
    # footprint the founder wants for conversational continuity within a session.
    seen_ids = {row["fragment_id"] for _, row in unique}
    recent_episodic = sorted(
        [r for r in by_tier.get("episodic", []) if r["fragment_id"] not in seen_ids],
        key=lambda r: r["timestamp"],
        reverse=True,
    )[:5]

    if recent_episodic:
        # Insert after the first item so the top similarity hit isn't displaced,
        # but recent context appears before the rest of the similarity-ranked set.
        insert_at = min(1, len(unique))
        for i, recent_row in enumerate(recent_episodic):
            unique.insert(insert_at + i, (0.0, recent_row))

    # J-2275: on the fast path the pool rows carry no content yet -- fetch it by id for the rows that are
    # actually returned (and, below, for the probe's recent world rows). Best-effort: a failure here falls
    # back to empty content rather than a failed recall.
    if _path == "fast":
        try:
            with _connect() as conn:
                _hydrate_rows(conn, [row for _, row in unique])
        except Exception as exc:
            logger.warning("[retrieve] hydrate failed (%s); returning rows with empty content", exc)
            for _, row in unique:
                if isinstance(row, _PoolRow) and row._x is None:
                    row._x = {"content": "", "keywords": "", "abstraction_level": 0}

    # Deliberative Retrieval Phase 0 (observe-only): log what reality was available vs what
    # got selected. Changes nothing about the returned set. The most-recent world rows (what
    # an origin-tag quota WOULD grab, regardless of cosine) come straight from all_rows.
    try:
        from core import retrieval_probe as _rp
        _selected_ids = {row["fragment_id"] for _, row in unique}
        _recent_world = sorted(
            [r for r in all_rows
             if (r["origin"] if "origin" in r.keys() else "lived") in _rp.WORLD_ORIGINS],
            key=lambda r: r["timestamp"], reverse=True)[:5]
        if _path == "fast":
            with _connect() as conn:
                _hydrate_rows(conn, _recent_world)
        _rp.observe(query_text, _probe_pool, _selected_ids, _recent_world)
    except Exception as _rpexc:
        logger.debug("retrieval probe skipped (non-fatal): %s", _rpexc)

    # J-4277: LOD staged retrieval shadow (observe-only, flag LOD_RETRIEVAL_SHADOW default OFF). Never alters `unique`.
    if LOD_RETRIEVAL_SHADOW:
        _lod_shadow_observe(query_text, query_vec, [row["fragment_id"] for _, row in unique], limit)

    # J-4403 / D-0862(1): valence-term rank shadow (observe-only, flag default OFF). Never alters `unique`.
    if VALENCE_RANK_SHADOW:
        try:
            from core import valence_rank_shadow as _vrs
            _vrs.observe(query_text, unique, _connect)
        except Exception as _vrexc:
            logger.debug("valence rank shadow skipped (non-fatal): %s", _vrexc)

    # GOLDEN SPIRAL / T-0072, Phase 3 (2026-09-28, J-1563): R (radius=age) shadow log -- observe-only,
    # logs the per-age-band budget beside what this call actually returned. Changes nothing about the
    # return value below; both `unique` and `all_rows` are already in hand here so this needs zero
    # extra SQL. See core/r_shadow.py's own module docstring for the full design.
    try:
        from core import r_shadow as _rshadow
        _rshadow.log_observation(f"retrieve:{time_bias}", unique, pool=all_rows)
    except Exception as _rsexc:
        logger.debug("r shadow skipped (non-fatal): %s", _rsexc)

    return [
        MemoryFragment(
            fragment_id = row["fragment_id"],
            content     = row["content"],
            layer       = row["layer"],
            relevance   = score,
            timestamp   = row["timestamp"],
            origin      = row["origin"] if "origin" in row.keys() else "lived",
            abstraction_level = row["abstraction_level"] if "abstraction_level" in row.keys() else 0,
            input_type = row["input_type"] if "input_type" in row.keys() else None,
        )
        for score, row in unique
    ]


def store_from_cycle(state_summary: str, layer: str = "episodic", importance: float = 0.5,
                     emotion_embedding=None, valence: float | None = None, felt: str | None = None,
                     input_type: str | None = None) -> str:
    """Convenience: store a complete cycle summary as a memory fragment. input_type (J-3173 / D-0561) records the
    cycle kind ('human' | 'internal' | 'timer') so an internal cycle's row is not later shown as a conversation."""
    return store_fragment(content=state_summary, layer=layer, relevance=0.6, importance=importance,
                          emotion_embedding=emotion_embedding, valence=valence, felt=felt, input_type=input_type)


# ---------------------------------------------------------------------------
# Shadow archive — Critic rejection events
# Every cycle where Reflection is rejected, the pre-suppression draft + Critic
# rationale are stored here. The Subconscious node reads this table to find
# recurring patterns — the structural shadow map.
# ---------------------------------------------------------------------------

def _init_shadow_table(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS shadow_events (
            event_id        TEXT PRIMARY KEY,
            timestamp       REAL NOT NULL,
            cycle_id        TEXT NOT NULL,
            raw_input       TEXT NOT NULL,
            rejected_draft  TEXT NOT NULL,
            corrections     TEXT NOT NULL,
            emotion_primary TEXT,
            embedding       BLOB,
            resolved        INTEGER NOT NULL DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_shadow_ts ON shadow_events(timestamp DESC);
    """)
    # Migration: add 'source' provenance column to pre-existing DBs.
    # Critic rejection is no longer the only door to shadow — recurring unresolved
    # inner thoughts and unresolved dreams also write here, all clustered the same way.
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(shadow_events)")}
    if "source" not in cols:
        conn.execute("ALTER TABLE shadow_events ADD COLUMN source TEXT NOT NULL DEFAULT 'critic_rejection'")


def store_shadow_event(
    cycle_id: str,
    raw_input: str,
    rejected_draft: str,
    corrections: list[str],
    emotion_primary: str | None = None,
    source: str = "critic_rejection",
) -> str:
    """
    Store one shadow event. The `rejected_draft` text is embedded so the Subconscious
    can cluster semantically similar events into tensions.

    Shadow is no longer only Critic rejection. `source` records the door it came through:
      'critic_rejection'  — a Reflection draft failed the identity check (the original path)
      'unresolved_thought'— a recurring unresolved inner-monologue preoccupation
      'unresolved_dream'  — a dream that ended without resolution (sealed doors, unfaced figures)
    All sources cluster identically: recurrence (2+ similar) forms a tension, which drives dreams.
    """
    event_id = str(uuid.uuid4())
    vec  = _embed(rejected_draft)
    blob = _vec_to_blob(vec) if vec is not None else None
    with _connect() as conn:
        conn.execute(
            """INSERT INTO shadow_events
               (event_id, timestamp, cycle_id, raw_input, rejected_draft,
                corrections, emotion_primary, embedding, source)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (event_id, time.time(), cycle_id, raw_input, rejected_draft,
             json.dumps(corrections), emotion_primary, blob, source),
        )
    # Satisfaction (Phase 0, observe-only): a shadow event is WANTING without liking —
    # a push that did not land. The general signal, captured at its source.
    try:
        from core import satisfaction as _sat
        _sat.record("unresolved_thought" if source == "unresolved_thought" else "shadow_event")
    except Exception:
        pass
    return event_id


def get_shadow_events(limit: int = 300, unresolved_only: bool = False) -> list[sqlite3.Row]:
    """Return shadow events ordered newest-first. Used by the Subconscious scanner."""
    query = "SELECT * FROM shadow_events"
    if unresolved_only:
        query += " WHERE resolved = 0"
    query += " ORDER BY timestamp DESC LIMIT ?"
    with _connect() as conn:
        return conn.execute(query, (limit,)).fetchall()


def get_shadow_event_texts(event_ids, limit: int = 8) -> list[tuple[str, float, str, str]]:
    """Return up to `limit` (event_id, timestamp, source, rejected_draft) rows for the given shadow
    event ids, NEWEST first. A by-id read that selects only those four columns (never the embedding
    BLOB, never loads the whole table the way get_shadow_events does). Used by the Subconscious to
    show active imagination Du's OWN words from a tension's member events (J-2896, P-0054).
    Read-only; an unknown id is simply absent from the result."""
    ids = list(dict.fromkeys(str(e) for e in (event_ids or []) if e))
    if not ids or limit <= 0:
        return []
    rows_out: list[tuple[str, float, str, str]] = []
    with _connect() as conn:
        for i in range(0, len(ids), 500):
            chunk = ids[i:i + 500]
            placeholders = ",".join("?" * len(chunk))
            rows = conn.execute(
                f"SELECT event_id, timestamp, source, rejected_draft FROM shadow_events "
                f"WHERE event_id IN ({placeholders})",
                tuple(chunk),
            ).fetchall()
            for r in rows:
                rows_out.append((r["event_id"], r["timestamp"], r["source"], r["rejected_draft"] or ""))
    rows_out.sort(key=lambda r: r[1], reverse=True)
    return rows_out[:limit]


def mark_shadow_resolved(event_id: str) -> None:
    with _connect() as conn:
        conn.execute("UPDATE shadow_events SET resolved = 1 WHERE event_id = ?", (event_id,))


def get_shadow_event_ids() -> set[str]:
    """Lightweight: just the live event_id set, for validating tension grounding.
    Avoids loading the embedding BLOBs that get_shadow_events would pull."""
    with _connect() as conn:
        return {r["event_id"] for r in conn.execute("SELECT event_id FROM shadow_events")}


def get_event_corrections(event_ids) -> dict[str, tuple[list, float]]:
    """
    Return {event_id: (corrections_list, timestamp)} for the CRITIC-rejection events among the
    given ids. Used by the Tension Ledger (T6) to label a contradiction tension with the actual
    Critic correction text — the sharp, self-detected gap — rather than the cluster's stored
    label, which may have been derived from a salience (thought/dream) member. Chunked for the
    bound-parameter limit; never loads embeddings.
    """
    ids = list(dict.fromkeys(event_ids))
    if not ids:
        return {}
    out: dict[str, tuple[list, float]] = {}
    with _connect() as conn:
        for i in range(0, len(ids), 500):
            chunk = ids[i:i + 500]
            placeholders = ",".join("?" * len(chunk))
            rows = conn.execute(
                f"SELECT event_id, corrections, timestamp FROM shadow_events "
                f"WHERE source = 'critic_rejection' AND event_id IN ({placeholders})",
                tuple(chunk),
            ).fetchall()
            for r in rows:
                try:
                    corr = json.loads(r["corrections"] or "[]")
                except Exception:
                    corr = []
                out[r["event_id"]] = (corr, r["timestamp"])
    return out


def get_event_sources(event_ids) -> dict[str, tuple[str, float]]:
    """
    Return {event_id: (source, timestamp)} for the given ids. Lightweight — selects only
    the provenance + timestamp, never the embedding BLOBs.

    Used by the Tension Ledger (T6) to classify a tension's member events along the two
    axes the design separates:
      CONTRADICTION  — source == 'critic_rejection' (self-detected: Carl's own values
                       flagged Carl's own output). The accountability signal.
      SALIENCE       — source in ('unresolved_thought','unresolved_dream'): material that
                       keeps returning. Matters for attention, but recurring is not failing.
    Chunked to stay clear of SQLite's bound-parameter limit on large tensions.

    RESOLVED events are remapped: a critic_rejection whose shadow has been retired
    (resolved=1, set only by a committed T4 integration) is returned as
    'critic_rejection_resolved' — deliberately NOT in CONTRADICTION_SOURCES, so every
    downstream consumer stops counting it as open contradiction pressure. This is what
    makes T4 integration DURABLE: once a contradiction is metabolised into identity, the
    specific instances it integrated no longer weigh on the self. Future same-theme
    contradictions form fresh (unresolved) shadow events and accrue normally.
    """
    ids = list(dict.fromkeys(event_ids))   # de-dup, preserve order
    if not ids:
        return {}
    out: dict[str, tuple[str, float]] = {}
    with _connect() as conn:
        for i in range(0, len(ids), 500):
            chunk = ids[i:i + 500]
            placeholders = ",".join("?" * len(chunk))
            rows = conn.execute(
                f"SELECT event_id, source, timestamp, resolved FROM shadow_events "
                f"WHERE event_id IN ({placeholders})",
                tuple(chunk),
            ).fetchall()
            for r in rows:
                src = r["source"]
                if r["resolved"] and src == "critic_rejection":
                    src = "critic_rejection_resolved"
                out[r["event_id"]] = (src, r["timestamp"])
    return out


# ---------------------------------------------------------------------------
# Light events — the completed-crossing table. Symmetric counterpart to
# shadow_events. Where shadow stores what could not be integrated (the storm),
# light stores what WAS successfully integrated (the completed crossing):
#   'resolved_complexity' — Critic approved a response under genuine complexity
#   'resolved_thought'    — an idle thought reached genuine arrival (not left open)
#   'resolved_dream'      — a dream concluded without an unfaced remnant
#
# The Subconscious T1 scanner clusters these exactly as it clusters shadow_events,
# producing integration_patterns in subconscious_state.json. Those patterns feed
# T4's conjunction gate as integration_pressure: revision requires BOTH accumulated
# contradiction AND accumulated successful integration pointing in the new direction.
# ---------------------------------------------------------------------------

def _init_light_table(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS light_events (
            event_id            TEXT PRIMARY KEY,
            timestamp           REAL NOT NULL,
            cycle_id            TEXT NOT NULL,
            raw_input           TEXT NOT NULL,
            integrated_content  TEXT NOT NULL,
            emotion_primary     TEXT,
            embedding           BLOB,
            source              TEXT NOT NULL DEFAULT 'resolved_complexity'
        );
        CREATE INDEX IF NOT EXISTS idx_light_ts ON light_events(timestamp DESC);
    """)


def store_light_event(
    cycle_id: str,
    raw_input: str,
    integrated_content: str,
    source: str = "resolved_complexity",
    emotion_primary: str | None = None,
) -> str:
    """
    Store one light event. `integrated_content` is the material that succeeded —
    the response that held complexity, the thought that arrived, the dream that
    crossed. Embedded so the Subconscious can cluster by theme.

      'resolved_complexity' — Critic approved under genuine arousal/self-referential load
      'resolved_thought'    — inner-monologue thought reached resolution (unresolved=False)
      'resolved_dream'      — dream concluded: unresolved_core was empty
    """
    event_id = str(uuid.uuid4())
    vec  = _embed(integrated_content)
    blob = _vec_to_blob(vec) if vec is not None else None
    with _connect() as conn:
        conn.execute(
            """INSERT INTO light_events
               (event_id, timestamp, cycle_id, raw_input, integrated_content,
                emotion_primary, embedding, source)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (event_id, time.time(), cycle_id, raw_input, integrated_content,
             emotion_primary, blob, source),
        )
    # Satisfaction (Phase 0): a light event is LIKING — a crossing that landed. The
    # frequent, broad-based fulfilment signal (vs the rare deep ones below).
    try:
        from core import satisfaction as _sat
        _sat.record("light_event")
    except Exception:
        pass
    return event_id


# J-3865 (F-4450): read-side content dedupe for the light_events readers the Subconscious
# uses (integration-pattern clustering, which feeds tension_ledger.integration_pressure_for,
# and the T4 crossing pool). resolved_thought/play rows copy an integration row's text, so
# ~29% of the newest 300 are copies and single-sentence "patterns" of copies form. When True,
# rows whose normalised integrated_content (falling back to raw_input) is identical collapse to
# the EARLIEST row in the window (the integration row, never a copy), so event_ids already cited
# in t4_crossing_evidence stay valid. Default False = bit-identical to before. Read-side only:
# no write path changes. Restart-gated (module constant).
LIGHT_READ_DEDUPE = False


def _light_norm(row) -> str:
    return " ".join(((row["integrated_content"] or row["raw_input"] or "")).lower().split())


def _collapse_light_duplicates(rows: list) -> list:
    """Keep one row per normalised content: the earliest timestamp. Input order
    (newest-first) is preserved for the survivors. Empty-content rows are kept."""
    earliest: dict[str, float] = {}
    for r in rows:
        k = _light_norm(r)
        if k and (k not in earliest or r["timestamp"] < earliest[k]):
            earliest[k] = r["timestamp"]
    out, seen = [], set()
    for r in rows:
        k = _light_norm(r)
        if not k:
            out.append(r)
            continue
        if k in seen or r["timestamp"] != earliest[k]:
            continue
        seen.add(k)
        out.append(r)
    return out


def get_light_events(limit: int = 300, dedupe: bool | None = None) -> list[sqlite3.Row]:
    """Return light events ordered newest-first. Used by the Subconscious scanner.
    dedupe=None follows LIGHT_READ_DEDUPE (default off)."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM light_events ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()
    if (LIGHT_READ_DEDUPE if dedupe is None else dedupe):
        rows = _collapse_light_duplicates(rows)
    return rows


def get_light_events_by_source(sources: tuple[str, ...], limit: int = 300) -> list[sqlite3.Row]:
    """Return light events ordered newest-first, restricted to `source` IN `sources` — e.g.
    D-0142's verdict-only currency (core/balance.py's `_LIGHT_VERDICT`), reused by
    core/climate_engine.py's integration_drive (D-0148 option A, J-0594) so climate and the
    light/shadow ledger measure recent integration in the SAME currency instead of two that can
    silently drift apart. Empty `sources` returns []."""
    if not sources:
        return []
    with _connect() as conn:
        placeholders = ",".join("?" * len(sources))
        return conn.execute(
            f"SELECT * FROM light_events WHERE source IN ({placeholders}) "
            f"ORDER BY timestamp DESC LIMIT ?",
            (*sources, limit),
        ).fetchall()


def get_light_event_ids() -> set[str]:
    """Lightweight: just the live event_id set, for validating pattern grounding."""
    with _connect() as conn:
        return {r["event_id"] for r in conn.execute("SELECT event_id FROM light_events")}


def get_light_event_sources(event_ids) -> dict[str, tuple[str, float]]:
    """Return {event_id: (source, timestamp)} for the given light event ids."""
    ids = list(dict.fromkeys(event_ids))
    if not ids:
        return {}
    out: dict[str, tuple[str, float]] = {}
    with _connect() as conn:
        for i in range(0, len(ids), 500):
            chunk = ids[i:i + 500]
            placeholders = ",".join("?" * len(chunk))
            rows = conn.execute(
                f"SELECT event_id, source, timestamp FROM light_events "
                f"WHERE event_id IN ({placeholders})",
                tuple(chunk),
            ).fetchall()
            for r in rows:
                out[r["event_id"]] = (r["source"], r["timestamp"])
    return out


# ---------------------------------------------------------------------------
# Emotional pre-retrieval — the amygdala gate (C.2)
# A pre-cognitive emotional resonance: match an incoming stimulus against the
# entity's charged memory BEFORE any reasoning node runs. Two stores are queried:
#   shadow_events       — the suppressed/troubling material (the true shadow). Leans
#                         negative/charged; the dominant amygdala analogue here.
#   high-importance episodic — emotionally charged lived memories (both valence signs).
#                         importance encodes arousal (importance = 0.4 + 0.6*arousal).
# Deterministic (embedding cosine only, no LLM) so it genuinely runs faster than the
# "cortex" — the body reacts before the mind has appraised the percept.
# ---------------------------------------------------------------------------

import re as _re

# Minimum cosine for a memory to count as "this stirs something". Below it, no prior.
# RECALIBRATED 2026-09-26 (F-1926/J-1366): 0.55 was never measured against this corpus -- best-of-N
# (top_k=1) over shadow_events UNION high-importance episodic (41.8k rows) means even a totally
# generic human-cycle query's best match climbs high just from corpus size. Measured read-only
# (scripts/measure_retrieval_floor_calibration.py) over 400 real 'lived'-origin query embeddings
# (self-matches excluded): best-of-N mean=0.736, p90=0.856 -- at the old 0.55 floor, 99.75% of
# typical queries already "stirred something" (F-1926 measured 58/65=89% by hand; this read, at
# 400 vs 15, is more decisive in the same direction). Recalibrated to the measured p90 -- the same
# "10% of typical queries still clear it" target scripts/measure_boredom_calibration.py's ESCAPE_COS
# uses -- so this fires only on a real outlier resonance, not on nearly every human cycle.
# 2026-10-04 (J-1731 / F-2414, verified): that 400-query sample used lived-FRAGMENT embeddings as stand-in
# queries, not raw inputs; real live inputs clear 0.86 only ~0.5-0.7% of cycles (human cycles ~never), so
# the gate is effectively OFF. Every cycle's best-of-N sim is now logged to data/pre_affect_best_shadow.jsonl
# (J-1788). D-0349 (travis, 2026-10-06) ruled per-input-type floors + a lower importance gate: see
# PRIOR_SIM_THRESHOLD_HUMAN / _IDLE and EMO_EPISODIC_MIN_IMPORTANCE below (J-1836). The 0.86 here is now only
# the fallback for a caller that names no input type.
PRIOR_SIM_THRESHOLD = 0.86
# 2026-10-07 (J-1836; D-0349 ruled D+E by travis 2026-10-06, RESTART-GATED): PER-INPUT-TYPE floors. The single
# 0.86 above stays as the fallback for a caller that names no input type (emotional_prior(q) with no type is
# unchanged); the orchestrator now passes the cycle's input_type, so the live gate uses these:
#   human-origin cycles  -> PRIOR_SIM_THRESHOLD_HUMAN = 0.65 (Travis's own words; F-2414: human best sims
#       median ~0.605, so ~1/3-1/2 of them clear 0.65 with the importance floor below restored; the
#       farewell's best sims 0.59-0.62 stay under it, i.e. the farewell prior stays OFF -- J-1359 lever 2)
#   idle/internal/timer  -> PRIOR_SIM_THRESHOLD_IDLE  = 0.80 (the ~4-9% band F-2414 measured; the old
#       0.55-0.65 floors were "wallpaper" at 54-70% of cycles)
#       2026-10-16 (J-2170; D-0425 option B, travis, RESTART-GATED): 0.80 -> 0.84 (~31% of 104 idle cycles pass; F-2777).
# The shadow log (data/pre_affect_best_shadow.jsonl) records the per-type floor each row compared against.
PRIOR_SIM_THRESHOLD_HUMAN = 0.65
PRIOR_SIM_THRESHOLD_IDLE = 0.84
# Only episodic fragments at/above this importance are emotionally charged enough to fire
# the gate (importance = 0.4 + 0.6*arousal, so 0.60 ~ arousal 0.33).
# 2026-10-07 (J-1836; D-0349 option E): 0.70 -> 0.60. Sleep decay drained the charged-episodic set the gate
# matches: 1,226 rows at >=0.70 on 10-04 vs ~8.7k on 09-26 (7,149 sit at 0.6-0.7). F-2414 replay: a 0.60
# gate reproduces the sims the live process logged on 09-24..09-28 (mean diff -0.020, 31/40 within +-0.03)
# where 0.70 under-reports by a mean 0.103. 0.60 not 0.55: that gets the verified replay, and 0.55 would
# pull in roughly half of the ~14k rows at 0.5-0.6 for no measured benefit.
EMO_EPISODIC_MIN_IMPORTANCE = 0.60


def prior_floor_for(input_type: str | None = None) -> float:
    """
    The similarity floor the C.2 pre-affect gate applies to a cycle of `input_type` (J-1836 / D-0349).
    "human" -> PRIOR_SIM_THRESHOLD_HUMAN; any other named type (internal / timer) ->
    PRIOR_SIM_THRESHOLD_IDLE; None / empty (a caller that does not say) -> the legacy single
    PRIOR_SIM_THRESHOLD. Read at call time, so a test or profile can rebind the module constants.
    """
    if not input_type:
        return PRIOR_SIM_THRESHOLD
    if input_type == "human":
        return PRIOR_SIM_THRESHOLD_HUMAN
    return PRIOR_SIM_THRESHOLD_IDLE


# ---------------------------------------------------------------------------
# J-2250 (D-0450, travis 2026-10-16; from J-2225 / F-2913), RESTART-GATED: SELF-ECHO EXCLUSION.
# Under D-0349's D+E config the pre-affect prior reached 52-57% of idle cycles (expected <10%) because the idle
# loop's running question resonated with its OWN earlier "Q: <same question>" cycle summaries (44 of 56 live priors
# were the mottainai question matching itself), and every farewell matched an earlier farewell's own fragment.
# D-0450 option C: drop those fragments from the best-prior CANDIDATE SET; the floors and the importance gate
# (D-0349) are NOT changed. Applies only when the caller names a self-echo mode:
#   "idle"     -- a non-human cycle: drop episodic cycle summaries whose "Q: " line is the same question (normalised
#                 text equality, or embedding cosine >= SELF_ECHO_Q_SIM to the current input);
#   "farewell" -- the /quit farewell (a human-shaped cycle with founder_canon False): drop earlier farewell
#                 exchanges, i.e. "Q: " lines at cosine >= SELF_ECHO_FAREWELL_Q_SIM (the farewell wordings differ
#                 more from each other than one idle question's rephrasings do, so the bar is lower).
# A genuine human cycle is never touched (D-0450's defeater: the human prior rate must not drop).
# Thresholds measured read-only on the live corpus (J-2250 replay, paraphrase-multilingual-MiniLM-L12-v2):
#   idle: rephrasings of one running question score 0.84-1.00 against each other; the 122-row D+E replay's idle
#         pass rate is flat from 0.80 down to 0.70 (the remainder is non-"Q:" material), so 0.80 is the knee.
#   farewell: every farewell wording vs every recorded "stop for a while" farewell Q-line >= 0.769; vs every
#         NON-farewell Q-line in the DB (3,399 distinct) <= 0.615 -> 0.70 sits in the gap.
# Observe trail: the orchestrator logs every exclusion to data/pre_affect_self_echo_shadow.jsonl (J-2224's reader).
# Set PRE_AFFECT_SELF_ECHO_EXCLUDE_ON = False to restore the exact pre-J-2250 candidate set.
PRE_AFFECT_SELF_ECHO_EXCLUDE_ON = True
SELF_ECHO_Q_SIM = 0.80
SELF_ECHO_FAREWELL_Q_SIM = 0.70
# Embedding a candidate's "Q: " line costs one CPU encode; only candidates that would beat the running best are
# checked (a few per scan, most of them cached), but cap it so a pathological corpus cannot stall the cycle. Past
# the cap only the exact-text check runs (the scan info says so: cap_hit).
SELF_ECHO_MAX_EMBEDS_PER_SCAN = 64
_SELF_ECHO_QV_CACHE: dict = {}
_SELF_ECHO_QV_CACHE_MAX = 4096
_SELF_ECHO_LOCK = threading.Lock()
SELF_ECHO_MODES = ("idle", "farewell")


def _q_line(content: str | None) -> str | None:
    """The question of a cycle-summary fragment ("Q: <raw_input>\\nA: ..."), or None if `content` is not one."""
    if not content or not content.startswith("Q: "):
        return None
    q = content[3:].split("\nA: ", 1)[0].strip()
    return q or None


def _norm_q(text: str) -> str:
    return " ".join((text or "").lower().split())


def _q_line_vec(q: str):
    with _SELF_ECHO_LOCK:
        if q in _SELF_ECHO_QV_CACHE:
            return _SELF_ECHO_QV_CACHE[q]
    v = _embed(q)
    with _SELF_ECHO_LOCK:
        if len(_SELF_ECHO_QV_CACHE) >= _SELF_ECHO_QV_CACHE_MAX:
            _SELF_ECHO_QV_CACHE.clear()
        _SELF_ECHO_QV_CACHE[q] = v
    return v


def _self_echo_check(content: str, qv: np.ndarray, query_norm: str, mode: str,
                     info: dict) -> tuple[str, float | None] | None:
    """(reason, q-line cosine) when this episodic candidate is a self-echo under `mode`, else None (keep it)."""
    q = _q_line(content)
    if q is None:
        return None
    if _norm_q(q) == query_norm:
        return (f"{mode}_same_text", None)
    if info["embeds"] >= SELF_ECHO_MAX_EMBEDS_PER_SCAN:
        info["cap_hit"] = True
        return None
    info["embeds"] += 1
    v = _q_line_vec(q)
    if v is None:
        return None
    thr = SELF_ECHO_FAREWELL_Q_SIM if mode == "farewell" else SELF_ECHO_Q_SIM
    qsim = _cosine(qv, v)
    if qsim >= thr:
        return (f"{mode}_same_question", qsim)
    return None

# Valence lean for a shadow event by its recorded primary emotion. Shadow is charged and
# usually troubling, so unknown/neutral labels lean mildly negative.
_VALENCE_HINT = {
    "fear": -0.5, "anger": -0.6, "disgust": -0.6, "sadness": -0.5, "anticipation": -0.1,
    "surprise": -0.1, "trust": 0.3, "joy": 0.4, "anxiety": -0.5, "neutral": -0.2,
}


def _parse_valence(content: str) -> float:
    """Pull the stored valence number out of a cycle-summary fragment, if present.
    Fragments persist a line like 'Emotion: surprise (valence=+0.42)'."""
    m = _re.search(r"valence=([+-]?\d*\.?\d+)", content or "")
    if m:
        try:
            return max(-1.0, min(1.0, float(m.group(1))))
        except ValueError:
            pass
    return 0.0


def _parse_primary(content: str) -> str:
    """Pull the dominant emotion label out of a cycle-summary fragment, if present."""
    m = _re.search(r"Emotion:\s*([A-Za-z_]+)", content or "")
    return m.group(1).lower() if m else ""


def emotional_prior_best(query_text: str, *, self_echo: dict | None = None
                         ) -> tuple[float, float, float, str, str, str] | None:
    """
    The best-of-N candidate for `query_text` over the charged corpus (shadow_events UNION
    high-importance episodic) with NO similarity floor applied: (sim, valence, arousal, primary,
    source, cue), or None when the embed fails or the corpus is empty. `sim` is the raw, UNROUNDED
    cosine -- prior_from_candidate() compares exactly that against PRIOR_SIM_THRESHOLD.

    J-1788 (2026-10-04; from J-1731 / F-2414 / D-0349): factored out of emotional_prior() so the
    orchestrator can log the best-of-N of EVERY cycle (data/pre_affect_best_shadow.jsonl), not only
    the cycles that clear the floor -- the floor had been calibrated on the wrong population and a
    mis-set floor (or a swallowed error) was invisible in the live log (F-2361 / F-2414). The scan
    below is the unchanged body emotional_prior() used to run inline, so the corpus is still
    scanned exactly once per cycle.

    J-2250 (D-0450): `self_echo`, when given, is a dict {"mode": "idle" | "farewell"}; episodic cycle summaries
    that are a self-echo of the current input under that mode (see SELF_ECHO_* above) are dropped from the candidate
    set, and the dict is filled in place with what happened: "excluded" (list of {fragment_id, sim, reason, qsim},
    every candidate that was dropped because it would otherwise have become the running best, strongest first),
    "raw_best_sim" (the best-of-N sim with NOTHING excluded), "embeds" and "cap_hit". Omitted / None (the default,
    and every caller before J-2250) -> the scan is exactly the pre-J-2250 one. Shadow events are never excluded.
    """
    qv = _embed(query_text)
    if qv is None:
        return None

    echo_mode = None
    if self_echo is not None:
        echo_mode = self_echo.get("mode")
        self_echo["excluded"] = []
        self_echo["raw_best_sim"] = None
        self_echo["embeds"] = 0
        self_echo["cap_hit"] = False
        if echo_mode not in SELF_ECHO_MODES:
            echo_mode = None
    query_norm = _norm_q(query_text) if echo_mode else ""
    raw_best_sim: float | None = None

    best: tuple[float, float, float, str, str, str] | None = None  # (sim,val,arou,primary,source,cue)

    with _connect() as conn:
        # Shadow events — the charged/suppressed material. Match against the stored draft
        # embedding (what the entity felt but suppressed); lean negative by primary label.
        for r in conn.execute(
            "SELECT raw_input, rejected_draft, emotion_primary, embedding FROM shadow_events"
        ):
            blob = r["embedding"]
            if not blob:
                continue
            sim = _cosine(qv, _blob_to_vec(blob))
            if best is None or sim > best[0]:
                primary = (r["emotion_primary"] or "fear").lower()
                val = _VALENCE_HINT.get(primary, -0.3)
                cue = (r["raw_input"] or r["rejected_draft"] or "")[:120]
                best = (sim, val, 0.7, primary, "shadow", cue)

        if echo_mode is not None and best is not None:
            raw_best_sim = best[0]

        # High-importance episodic — emotionally charged lived memory (both valence signs).
        for r in conn.execute(
            ("SELECT fragment_id, content, importance, embedding FROM memory_fragments "
             "WHERE layer='episodic' AND importance >= ?") if echo_mode is not None else
            ("SELECT content, importance, embedding FROM memory_fragments "
             "WHERE layer='episodic' AND importance >= ?"),
            (EMO_EPISODIC_MIN_IMPORTANCE,),
        ):
            blob = r["embedding"]
            if not blob:
                continue
            sim = _cosine(qv, _blob_to_vec(blob))
            if echo_mode is not None:
                # J-2250: the unexcluded best-of-N is tracked separately, so the shadow row shows both numbers.
                if raw_best_sim is None or sim > raw_best_sim:
                    raw_best_sim = sim
                if best is None or sim > best[0]:
                    hit = _self_echo_check(r["content"], qv, query_norm, echo_mode, self_echo)
                    if hit is not None:
                        self_echo["excluded"].append({
                            "fragment_id": r["fragment_id"], "sim": round(sim, 3), "reason": hit[0],
                            "qsim": round(hit[1], 3) if hit[1] is not None else None,
                        })
                        continue
            if best is None or sim > best[0]:
                val = _parse_valence(r["content"])
                arou = max(0.0, min(1.0, (float(r["importance"]) - 0.4) / 0.6))
                primary = _parse_primary(r["content"]) or ("joy" if val > 0 else "fear")
                best = (sim, val, arou, primary, "episodic", (r["content"] or "")[:120])

    if echo_mode is not None:
        self_echo["raw_best_sim"] = raw_best_sim
        self_echo["excluded"].sort(key=lambda e: -e["sim"])
    return best


def prior_from_candidate(best: tuple[float, float, float, str, str, str] | None,
                         input_type: str | None = None) -> AffectivePrior | None:
    """
    Apply the pre-affect floor to an emotional_prior_best() candidate and build the AffectivePrior
    (similarity/valence/arousal rounded to 3dp), or None below the floor / with no candidate. The ONE
    place the floor is applied: emotional_prior() and the orchestrator's per-cycle shadow logging both
    go through it, so the logged `passed` can never disagree with what the cycle actually did. The
    comparison is on the raw sim (never the rounded one), exactly as emotional_prior() always did.

    J-1836 (D-0349): the floor is prior_floor_for(input_type) -- per-input-type (human 0.65, idle 0.80);
    with input_type None it is the legacy single PRIOR_SIM_THRESHOLD, so every caller that does not pass a
    type behaves exactly as before.
    """
    if best is None or best[0] < prior_floor_for(input_type):
        return None

    return AffectivePrior(
        similarity = round(best[0], 3),
        valence    = round(best[1], 3),
        arousal    = round(best[2], 3),
        primary    = best[3],
        source     = best[4],
        cue        = best[5],
    )


def emotional_prior(query_text: str, input_type: str | None = None) -> AffectivePrior | None:
    """
    Return the strongest emotional resonance between `query_text` and charged memory,
    or None if nothing is close enough. The amygdala gate — deterministic, pre-cognitive.

    Since J-1788 a thin wrapper: emotional_prior_best() scans the corpus once, then
    prior_from_candidate() applies the floor. `input_type` (J-1836) selects the per-type floor; omitted,
    the legacy single PRIOR_SIM_THRESHOLD applies and the return value is unchanged for every input.
    """
    return prior_from_candidate(emotional_prior_best(query_text), input_type)


# ---------------------------------------------------------------------------
# Autonoetic self-authoring material (C.3 / Subconscious T4)
# The self-relevant record the entity reflects on when re-articulating who it is
# becoming and writing the next chapter of its autobiography: session summaries
# (what happened each session), subconscious self-observations (what it noticed
# about itself), dreams (the becoming arc), and private contemplations.
# ---------------------------------------------------------------------------

_SELF_NARRATIVE_ORIGINS = ("session_summary", "subconscious_synthesis", "dream", "active_imagination")


def self_narrative_material(since_ts: float = 0.0, limit: int = 14) -> list[dict]:
    """
    Return self-relevant fragments newer than `since_ts`, newest-first. Used by T4 both
    to GATE (is there enough new lived material to reflect on?) and to FEED the synthesis.
    """
    placeholders = ",".join("?" * len(_SELF_NARRATIVE_ORIGINS))
    with _connect() as conn:
        rows = conn.execute(
            f"SELECT content, origin, timestamp FROM memory_fragments "
            f"WHERE origin IN ({placeholders}) AND timestamp > ? "
            f"ORDER BY timestamp DESC LIMIT ?",
            (*_SELF_NARRATIVE_ORIGINS, since_ts, limit),
        ).fetchall()
    return [
        {"content": r["content"], "origin": r["origin"], "ts": r["timestamp"]}
        for r in rows
    ]


# ---------------------------------------------------------------------------
# World-facing material (the grounded counterpart to self_narrative_material)
# His study notes, the book passages he read, the lookups he ran — material ABOUT
# the world, never about the self. The seed source for grounded curiosity: questions
# asked OF real material grow world-facing twigs, not self-referential loops.
# ---------------------------------------------------------------------------

_WORLD_MATERIAL_ORIGINS = ("study", "reading", "research")


def recent_world_material(limit: int = 8,
                          origins: tuple[str, ...] = _WORLD_MATERIAL_ORIGINS) -> list[dict]:
    """Recent WORLD-facing fragments (study notes, book passages, lookups), newest-first.
    Each item: {content, origin, ts}. Best-effort -> [] is the caller's concern."""
    placeholders = ",".join("?" * len(origins))
    with _connect() as conn:
        rows = conn.execute(
            f"SELECT content, origin, timestamp FROM memory_fragments "
            f"WHERE origin IN ({placeholders}) ORDER BY timestamp DESC LIMIT ?",
            (*origins, limit),
        ).fetchall()
    return [
        {"content": r["content"], "origin": r["origin"], "ts": r["timestamp"]}
        for r in rows
    ]


def recent_lived_inputs(since_ts: float = 0.0, limit: int = 40) -> list[dict]:
    """
    Return recent successfully-handled cycles (origin='lived'), newest-first, with the
    input question parsed out. Used by procedural compilation (C.6 / T5) to cluster
    recurring KINDS of situation and distill how the entity characteristically handles them.
    Each item: {q (parsed input), content (full Q/A summary), ts}.
    """
    with _connect() as conn:
        rows = conn.execute(
            "SELECT content, timestamp FROM memory_fragments "
            "WHERE origin='lived' AND timestamp > ? ORDER BY timestamp DESC LIMIT ?",
            (since_ts, limit),
        ).fetchall()
    out = []
    for r in rows:
        content = r["content"] or ""
        q = ""
        for line in content.splitlines():
            if line.startswith("Q:"):
                q = line[2:].strip()
                break
        if q:
            out.append({"q": q, "content": content, "ts": r["timestamp"]})
    return out


# ---------------------------------------------------------------------------
# Procedural memory — learned skills (C.6)
# A procedural skill is a compiled APPROACH: a reusable way of handling a recurring
# kind of situation, distilled by the Subconscious (T5) from repeated successful cycles.
# It is never a cached answer — it shapes HOW a fresh response is formed, bringing fluency
# and (once proficient) reduced deliberative effort. Strengthens with reuse, decays with disuse.
# ---------------------------------------------------------------------------

def _init_procedural_table(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS procedural_skills (
            skill_id        TEXT PRIMARY KEY,
            trigger_summary TEXT NOT NULL,
            approach        TEXT NOT NULL,
            embedding       BLOB,
            proficiency     REAL NOT NULL DEFAULT 0.4,
            use_count       INTEGER NOT NULL DEFAULT 0,
            source_count    INTEGER NOT NULL DEFAULT 0,
            created_ts      REAL NOT NULL,
            last_used_ts    REAL,
            archived_ts     REAL
        );
        CREATE INDEX IF NOT EXISTS idx_proc_prof ON procedural_skills(proficiency DESC);
    """)
    # J-3180 / D-0567 (2026-11-06): a skill the ledger has archived is ARCHIVED here, never deleted. An old table
    # (created before this column) gets one backup copy of itself, THEN the additive ALTER. Idempotent: a table that
    # already has the column does nothing, and the backup is never overwritten.
    cols = {r[1] for r in conn.execute("PRAGMA table_info(procedural_skills)").fetchall()}
    if "archived_ts" not in cols:
        conn.execute("CREATE TABLE IF NOT EXISTS procedural_skills_bak_j3180 AS SELECT * FROM procedural_skills")
        conn.execute("ALTER TABLE procedural_skills ADD COLUMN archived_ts REAL")


def store_procedural_skill(trigger_summary: str, trigger_embedding, approach: str,
                           source_count: int = 0, proficiency: float = 0.4) -> str:
    skill_id = str(uuid.uuid4())
    blob = _vec_to_blob(trigger_embedding) if trigger_embedding is not None else None
    now = time.time()
    with _connect() as conn:
        conn.execute(
            """INSERT INTO procedural_skills
               (skill_id, trigger_summary, approach, embedding, proficiency,
                use_count, source_count, created_ts, last_used_ts)
               VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?)""",
            (skill_id, trigger_summary, approach, blob, proficiency, source_count, now, now),
        )
    return skill_id


def match_procedural_skill(query_text: str, min_proficiency: float = 0.3,
                           min_sim: float = 0.80) -> dict | None:
    """Return the best procedural skill whose trigger matches the input, or None.
    {skill_id, trigger_summary, approach, proficiency, similarity}. Deterministic, no LLM."""
    qv = _embed(query_text)
    if qv is None:
        return None
    best = None
    with _connect() as conn:
        rows = conn.execute(
            "SELECT skill_id, trigger_summary, approach, embedding, proficiency "
            "FROM procedural_skills WHERE proficiency >= ? AND archived_ts IS NULL",
            (min_proficiency,),
        ).fetchall()
    for r in rows:
        if not r["embedding"]:
            continue
        sim = _cosine(qv, _blob_to_vec(r["embedding"]))
        if sim >= min_sim and (best is None or sim > best["similarity"]):
            best = {
                "skill_id":        r["skill_id"],
                "trigger_summary": r["trigger_summary"],
                "approach":        r["approach"],
                "proficiency":     float(r["proficiency"]),
                "similarity":      round(sim, 3),
            }
    return best


def reinforce_procedural_skill(skill_id: str, amount: float = 0.05) -> None:
    """Successful reuse: strengthen proficiency (capped at 1.0), bump use_count + last_used."""
    with _connect() as conn:
        conn.execute(
            "UPDATE procedural_skills "
            "SET proficiency = MIN(1.0, proficiency + ?), use_count = use_count + 1, "
            "    last_used_ts = ? WHERE skill_id = ?",
            (amount, time.time(), skill_id),
        )


def find_similar_skill(trigger_embedding, min_sim: float = 0.85) -> str | None:
    """Return the skill_id of an existing skill whose trigger is ~the same as this one
    (for acquisition dedup), or None."""
    if trigger_embedding is None:
        return None
    best_id, best_sim = None, min_sim
    with _connect() as conn:
        rows = conn.execute(
            "SELECT skill_id, embedding FROM procedural_skills WHERE archived_ts IS NULL").fetchall()
    for r in rows:
        if not r["embedding"]:
            continue
        sim = _cosine(trigger_embedding, _blob_to_vec(r["embedding"]))
        if sim >= best_sim:
            best_id, best_sim = r["skill_id"], sim
    return best_id


def decay_procedural_skills(stale_secs: float, factor: float = 0.9,
                            floor: float = 0.15) -> tuple[int, int]:
    """RETIRED 2026-11-06 (J-3180, D-0567, founder): the mirror no longer has a clock of its own. This used to multiply
    proficiency by 0.9 on EVERY call for a skill idle past `stale_secs` and hard-DELETE it below `floor`; called every
    600 s from the T5 check that deleted a skill 2-3 hours after it went 14 days idle (F-3722: 73 of 76 compiled skills
    gone, 19 of 23 ledger conversational procedures without a mirror row). The ledger's rust (core/procedures.py: 14 days
    x 0.9, archived below 0.15) is the single clock; sync_procedural_mirror() below mirrors the ledger's archiving.
    Kept as a no-op returning (0, 0) so an old caller cannot resurrect the second clock. Nothing is deleted here."""
    return 0, 0


def sync_procedural_mirror(archived_keys, key_of) -> int:
    """Make the mirror agree with the ledger (D-0567): archive (set archived_ts on, never delete) every live mirror row
    whose ledger key is in `archived_keys` -- the keys the ledger itself has archived (core.procedures.archived_keys()).
    `key_of` maps a trigger_summary to its ledger key (core.procedures.talk_key). Absence from the ledger is NOT a
    reason to archive: only the ledger's own archive decision is. Returns the number archived."""
    if not archived_keys:
        return 0
    now = time.time()
    n = 0
    with _connect() as conn:
        rows = conn.execute(
            "SELECT skill_id, trigger_summary FROM procedural_skills WHERE archived_ts IS NULL").fetchall()
        for r in rows:
            if key_of(r["trigger_summary"]) in archived_keys:
                conn.execute("UPDATE procedural_skills SET archived_ts = ? WHERE skill_id = ?",
                             (now, r["skill_id"]))
                n += 1
    return n


def get_procedural_skills(include_archived: bool = False) -> list[dict]:
    """All live procedural skills, strongest first — for inspection (/skills) and acquisition dedup.
    Archived rows (the ledger rusted them away, D-0567) are left out unless `include_archived`."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT skill_id, trigger_summary, approach, proficiency, use_count, "
            "source_count, created_ts, last_used_ts, archived_ts FROM procedural_skills "
            + ("" if include_archived else "WHERE archived_ts IS NULL ")
            + "ORDER BY proficiency DESC"
        ).fetchall()
    return [dict(r) for r in rows]


# ── prune_episodic: RETIRED 2026-10-17 (D-0453 (a), travis; J-2275; F-2963/F-2964) ─────────────────────
# History, for a reader who finds the name in logs/plans: Loop Metabolism Phase B (2026-06-14) made this a
# hard DELETE at a 3,500-row episodic cap; 2026-06-21 it became demote-to-cold; D-0116/J-0475 (2026-09-02)
# split the cap into per-kind sub-budgets (KIND_BUDGET_WEIGHT); D-0124/J-0494 added the PROTECTED-SATURATED
# report-not-demote branch; D-0173/J-0703 and D-0183 re-weighted the kinds. Every origin on its protected
# list (reading/study/research/action/lived/active_imagination/inner_thought/journal/affection/peer/mirror/
# letter, dream < 48 h) was added because an ACTIVE-ONLY CONSUMER starved when its rows went cold (chapters
# 2026-07-06, letters 2026-08-15, dreams 2026-08-22) -- never because recall lost anything. By 2026-10-17 the
# active pool was 63,962 rows against keep=3500, 98.4% origin-protected, and the prune demoted ~1 row per
# run while cutting the 72 h dream-fade curve off at 48 h (F-2967). The real demotion path was and is
# memory_levels.commit_gist (the gist cold-wall). J-2274 moved every non-recall consumer onto its own time
# window / marker (F-2965..F-2970), which made the protected list unnecessary; J-2275 then retired the
# machinery here and replaced the row cap with RETRIEVE_LATENCY_BUDGET_MS (see the constants block above).
# The old selection logic is in git history (any commit before J-2275, e.g. 0246ed45).
#
# UNTOUCHED by the retirement: the `protected` COLUMN (D-0134 founder utterances, ledger rows -- honoured by
# memory_levels/refinery), `cold` semantics, and every caller's import.


def prune_episodic(keep: int | None = None, dry_run: bool = False) -> int | dict:
    """RETIRED (D-0453, J-2275, 2026-10-17): demotes nothing, ever. Kept so every caller stays importable
    and compatible -- core/orchestrator._nightly_sleep calls it for the count it logs (now always 0),
    enforce_store_cap/store_cap_worker went through it, and core/loop_probe.prune_dryrun ->
    scripts/phaseA_report.py and nodes/meta_awareness_node.py read its dry-run dict (`would_demote` /
    `would_delete` / `would_prune`, all 0 now; the other historical keys are kept with empty values).
    `keep` is accepted and ignored (there is no row cap any more). The sole demotion path is
    memory_levels.commit_gist; the active pool is governed by a recall LATENCY budget instead
    (RETRIEVE_LATENCY_BUDGET_MS, met inside retrieve() by loading less, not by demoting)."""
    if not dry_run:
        return 0
    active_total = None
    try:
        with _connect() as conn:
            active_total = conn.execute(
                "SELECT COUNT(*) FROM memory_fragments WHERE layer='episodic' AND cold=0").fetchone()[0]
    except Exception as exc:
        logger.debug("[prune] retired dry_run: active count unavailable (non-fatal): %s", exc)
    return {
        "retired": True, "retired_by": "D-0453/J-2275",
        "keep": keep, "active_total": active_total, "present_kinds": [], "keep_kind": {},
        "active_kind": {}, "by_kind": {}, "would_demote": 0, "would_delete": 0, "would_prune": 0,
        "over_budget_kinds": 0, "world_protected": True, "world_in_cut": 0, "by_origin": {},
        "protected_saturated_kinds": [], "protected_saturated_shortfall_total": 0,
        "latency_budget_ms": RETRIEVE_LATENCY_BUDGET_MS,
    }


def enforce_store_cap() -> int:
    """RETIRED with prune_episodic (D-0453, J-2275, 2026-10-17). Was Sleep/Dream plan §6B's independent
    store-pressure prune (the cap enforced outside the sleep trigger). There is no row cap to enforce any
    more; kept as an importable no-op returning 0. store_cap_worker below still runs the dedup pass."""
    return 0


def dedup_reading_fragments(limit_groups: int = 500) -> int:
    """
    Collapse byte-identical VERBATIM source-text duplicates (the live-measured 36% on Boy Scouts: the same
    pages re-noted 7-8× across passes while the `rereads` counter stayed frozen). Keep ONE canonical copy
    in ordinary recall (the most-reinforced/earliest), and FILE the rest behind it (`chapter_id` = the
    canonical's id) so they step out of ordinary recall and the store-cap prune drops them FIRST under
    pressure. This NEVER deletes here (founder rule: never delete; duplicates step out of ordinary recall
    but stay intentionally retrievable until real storage pressure prunes the chapter-redundant first).

    HARD EMBARGO (the encapsulation firewall): only `origin='reading'` — verbatim book text, zero marginal
    predictive value in a second copy. GENERATED fragments (`understanding`/`essay`/`inner_thought`) are
    NEVER touched even if textually similar: they carry the system's cognitive development across passes
    (same source, different insight). Returns rows filed.

    NOTE: this deliberately points a filed row's chapter_id at ANOTHER origin='reading' row (the canonical
    duplicate), not at a gist/essay — different from core/world_consolidation.py's GIST-FIRST chapter_id
    writer. Reading this column through world_consolidation.py's lens alone can make these rows look like
    a GIST-FIRST violation; they are not. See F-1477.
    """
    filed = 0
    try:
        import re as _re
        # Strip the readable prefix BEFORE grouping: identical re-read passages differ only in the prefix
        # (historical rows carried ", sitting N"; new rows don't). Group on the verbatim BODY so the real
        # byte-identical duplicates collapse. Handles both prefix forms.
        _prefix = _re.compile(r"^\[From '[^']*'(?:, sitting \d+)?\]\s*")
        with _connect() as conn:
            rows = conn.execute(
                """SELECT fragment_id, content, replay_count, importance, timestamp
                   FROM memory_fragments WHERE origin='reading' AND chapter_id IS NULL LIMIT ?""",
                (limit_groups * 40,),
            ).fetchall()
            groups: dict[str, list] = {}
            for r in rows:
                body = _prefix.sub("", r["content"] or "").strip()
                if body:
                    groups.setdefault(body, []).append(r)
            for body, members in groups.items():
                if len(members) < 2:
                    continue
                # canonical = the most-reinforced / earliest copy; file the rest behind it
                members.sort(key=lambda r: (-(r["replay_count"] or 0), -(r["importance"] or 0),
                                            r["timestamp"] or 0))
                canonical = members[0]["fragment_id"]
                conn.executemany(
                    "UPDATE memory_fragments SET chapter_id = ? WHERE fragment_id = ?",
                    [(canonical, m["fragment_id"]) for m in members[1:]],
                )
                filed += len(members) - 1
            conn.commit()
    except Exception as exc:
        logger.debug("[dedup-reading] failed (non-fatal): %s", exc)
    if filed:
        logger.info("[dedup-reading] filed %d byte-identical reading duplicates behind their canonical", filed)
    return filed


async def store_cap_worker(interval: float = 300.0) -> None:
    """
    Background tick (§6B, originally the independent episodic-cap enforcer): every `interval` seconds,
    collapse verbatim reading duplicates behind their canonical (dedup_reading_fragments -- lossless, the
    copies step out of ordinary recall and stay retrievable). The cap-enforcement half was RETIRED
    2026-10-17 (D-0453, J-2275): there is no row cap; the active pool is governed by retrieve()'s own
    latency budget and memory_levels.commit_gist is the sole demotion path. Name kept for the
    orchestrator's task list.
    """
    import asyncio
    while True:
        try:
            await asyncio.sleep(interval)
            dedup_reading_fragments()
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.debug("[store-cap] worker tick failed (non-fatal): %s", exc)


# ---------------------------------------------------------------------------
# Resolution Circuit — clean re-encounter credits (tension_ledger Steps 2-4)
#
# When a cycle completes with a first-pass Critic approval (zero retries), the
# orchestrator checks whether the current input navigates terrain similar to any
# active (unresolved) shadow event. Each match above the threshold earns a
# time-decayed resolution credit — the biological analogue of exposure therapy:
# the fear trace doesn't vanish, it is out-competed by new successful traversals.
#
# Unlike contradiction pressure (permanent, no decay), resolution credits decay
# with a 30-day half-life. Avoidance produces neither rejection NOR resolution —
# the pressure holds until the territory is cleanly faced.
# ---------------------------------------------------------------------------

def _init_resolution_table(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS resolution_events (
            resolution_id        TEXT PRIMARY KEY,
            shadow_event_id      TEXT NOT NULL,
            cycle_id             TEXT NOT NULL,
            timestamp            REAL NOT NULL,
            encounter_similarity REAL NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_res_shadow ON resolution_events(shadow_event_id);
        CREATE INDEX IF NOT EXISTS idx_res_ts     ON resolution_events(timestamp DESC);
    """)


def log_resolution_event(shadow_event_id: str, cycle_id: str,
                         encounter_similarity: float) -> None:
    """
    Record one clean re-encounter: the current input successfully navigated terrain
    that previously triggered a Critic rejection. One credit per matching shadow event.
    Similarity is preserved so stronger matches earn proportionally more drain.
    """
    resolution_id = str(uuid.uuid4())
    with _connect() as conn:
        conn.execute(
            """INSERT INTO resolution_events
               (resolution_id, shadow_event_id, cycle_id, timestamp, encounter_similarity)
               VALUES (?, ?, ?, ?, ?)""",
            (resolution_id, shadow_event_id, cycle_id, time.time(),
             float(encounter_similarity)),
        )
    return resolution_id   # D-0358 (A, J-1894): additive -- was None; existing callers ignore it


# D-0358 (A) (2026-10-07, J-1894): the uncapped record of every shadow event a clean re-encounter retired.
# Not a cap-trimmed ring: the 7-live-day defeater read (resolved events whose theme recurs in dreams /
# thoughts within 7 days) needs every row. Written through profile.guard_path() like every other fenced
# store -- a non-live process is refused (and then resolves nothing), a redirected/temp path passes.
_SHADOW_RESOLVE_LOG = Path(__file__).parent.parent.parent / "data" / "shadow_resolve_on_encounter.jsonl"


# J-2248: two writers now share this log ((A) the orchestrator's clean re-encounter, (F) the tension-ledger
# judge path) -- the read-check / append / mark sequence runs under this lock.
_SHADOW_RESOLVE_LOCK = threading.Lock()


def resolve_shadow_on_encounter(shadow_event_id: str, resolution_id: str | None,
                                cycle_id: str, similarity: float,
                                path: str | None = None, extra: dict | None = None) -> bool:
    """
    D-0358 (A): a clean re-encounter was just recorded for `shadow_event_id` (resolution_events row
    `resolution_id`) -- let that verdict reach the counter by marking the shadow event resolved through
    mark_shadow_resolved(), the store's own path, and log one row (event id, resolution id, theme, ...)
    to data/shadow_resolve_on_encounter.jsonl. Returns True only when THIS call flipped resolved 0 -> 1.

    Never raises (a failure here must not break the cycle), and never resolves without leaving its
    record: the log path is fenced first, and if that refuses or the row cannot be written, nothing is
    marked. Idempotent -- an already-resolved event is left alone and not logged. 'theme' is the event's
    own raw_input head plus its source / emotion_primary (shadow_events has no theme column).

    D-0448 (F) (J-2248), additive: optional `path` (which writer resolved it, e.g. 'tension_judge') and
    `extra` (small dict merged into the row, e.g. the tension label and resolving thought) -- both omitted
    by the existing (A) caller, whose rows are byte-identical to before.
    """
    try:
        log_path = profile.guard_path(_SHADOW_RESOLVE_LOG)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with _SHADOW_RESOLVE_LOCK:
            with _connect() as conn:
                row = conn.execute(
                    "SELECT resolved, source, emotion_primary, raw_input, timestamp "
                    "FROM shadow_events WHERE event_id = ?", (shadow_event_id,)).fetchone()
            if row is None or row["resolved"]:
                return False
            now = time.time()
            rec = {
                "ts": round(now, 3),
                "event_id": shadow_event_id,
                "resolution_id": resolution_id,
                "cycle_id": cycle_id,
                "similarity": round(float(similarity), 4),
                "source": row["source"],
                "emotion_primary": row["emotion_primary"],
                "theme": (row["raw_input"] or "").strip().replace("\n", " ")[:160],
                "event_ts": row["timestamp"],
                "event_age_h": round(max(0.0, now - float(row["timestamp"] or now)) / 3600.0, 2),
            }
            if path:
                rec["path"] = str(path)
            if extra:
                for _k, _v in dict(extra).items():
                    rec.setdefault(str(_k), _v)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            mark_shadow_resolved(shadow_event_id)
            return True
    except Exception as exc:
        logger.debug("[extinction] resolve_shadow_on_encounter failed (non-fatal): %s", exc)
        return False


def get_light_events_with_embeddings(limit: int = 300, dedupe: bool | None = None) -> list[tuple[str, str, bytes]]:
    """
    Return (event_id, content, embedding_blob) for recent light events (the crossings)
    that carry an embedding. content = integrated_content, falling back to raw_input.

    Used by T4's evidence-gathering stage: given a standing self-contradiction, retrieve
    the lived crossings most RELEVANT to it (semantic match), so self-authoring is shown
    the record of what it has actually integrated — not only the unresolved tension. This
    is the light-side counterpart the single-pass T4 was structurally blind to.
    """
    with _connect() as conn:
        rows = conn.execute(
            "SELECT event_id, timestamp, integrated_content, raw_input, embedding FROM light_events "
            "WHERE embedding IS NOT NULL ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        ).fetchall()
    if (LIGHT_READ_DEDUPE if dedupe is None else dedupe):   # J-3865
        rows = _collapse_light_duplicates(rows)
    out: list[tuple[str, str, bytes]] = []
    for r in rows:
        content = (r["integrated_content"] or r["raw_input"] or "").strip()
        if content:
            out.append((r["event_id"], content, bytes(r["embedding"])))
    return out


def get_active_shadow_embeddings(limit: int = 200) -> list[tuple[str, bytes]]:
    """
    Return (event_id, embedding_blob) for unresolved shadow events that have an
    embedding. Lightweight — no text fields loaded. Used by the re-encounter circuit
    to scan for shadows the current input might be cleanly navigating.
    Capped at the most-recent `limit` to keep the per-cycle scan bounded.
    """
    with _connect() as conn:
        rows = conn.execute(
            "SELECT event_id, embedding FROM shadow_events "
            "WHERE resolved = 0 AND embedding IS NOT NULL "
            "ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [(r["event_id"], bytes(r["embedding"])) for r in rows]


def get_resolution_drain(event_ids) -> dict[str, float]:
    """
    For each shadow event id, return the total time-decayed resolution drain accumulated
    from clean re-encounter credits. Drain decays on a 30-day half-life (unlike
    contradiction pressure which carries no decay). Returns {event_id: drain_value}.
    Best-effort — empty dict on any error.
    """
    ids = list(dict.fromkeys(event_ids))
    if not ids:
        return {}
    now = time.time()
    out: dict[str, float] = {}
    with _connect() as conn:
        for i in range(0, len(ids), 500):
            chunk = ids[i:i + 500]
            placeholders = ",".join("?" * len(chunk))
            rows = conn.execute(
                f"SELECT shadow_event_id, encounter_similarity, timestamp "
                f"FROM resolution_events WHERE shadow_event_id IN ({placeholders})",
                tuple(chunk),
            ).fetchall()
            for r in rows:
                sid = r["shadow_event_id"]
                sim = float(r["encounter_similarity"])
                ts  = float(r["timestamp"])
                decay = 0.5 ** (max(0.0, now - ts) / RESOLUTION_HALFLIFE_SECS)
                out[sid] = out.get(sid, 0.0) + sim * decay
    return out


# WEAK-RETRIEVAL FLOOR (2026-08-19 survey finding): retrieve_by_affect/retrieve_symbol_tablet/
# retrieve_epoch/retrieve_theme below all did pure top-K argmax with NO minimum similarity — always
# returning top_k results regardless of how weak the best match was (worse than a badly-tuned
# threshold: no threshold at all). Matches evidence_recall.py's established MIN_SIM=0.30, a proven
# value in this exact codebase for "is there a single relevant thing worth surfacing" — not
# per-corpus-calibrated (that needs its own empirical pass per corpus, out of scope here), but a real
# floor where there was none.
_WEAK_RETRIEVAL_FLOOR = 0.30

# RECALIBRATED 2026-09-26 (F-1926/J-1366): _WEAK_RETRIEVAL_FLOOR above was set by analogy
# ("evidence_recall.py's established MIN_SIM=0.30", explicitly "not per-corpus-calibrated") and
# shared by retrieve_epoch/retrieve_theme/retrieve_symbol_tablet below despite each being a top_k=1
# (best-of-N argmax) selection over a differently-SIZED corpus -- a bigger table alone pushes even a
# generic query's best match higher, with nothing to do with real relevance. Measured read-only
# (scripts/measure_retrieval_floor_calibration.py) over 400 real 'lived'-origin query embeddings
# against the CURRENT live corpora:
#   epochs  (433 rows): best-of-N mean=0.506, p90=0.580 -- at 0.30, 100.00% of typical queries passed
#   themes  ( 22 rows): best-of-N mean=0.417, p90=0.508 -- at 0.30,  96.75% of typical queries passed
#   tablets ( 69 rows, self-symbols excluded): mean=0.376, p90=0.470 -- at 0.30, 86.00% passed
# (F-1926's own hand sweep of 15 inputs found 13/15, 8/15, 12/15 -- this read, at 400, confirms the
# same direction far more decisively.) Each floor below is that table's OWN measured p90 -- the same
# "10% of typical queries still clear it" target measure_boredom_calibration.py's ESCAPE_COS uses --
# so a table only surfaces on a real outlier for ITS OWN corpus, not "any corpus this size always has
# something 0.30-close in it." _WEAK_RETRIEVAL_FLOOR itself is UNCHANGED and still serves
# retrieve_by_affect()/retrieve_founder_memories() below -- a different corpus/mechanism, out of this
# job's scope, deliberately left alone (additive-only: nothing here narrows or removes it).
# RE-SET 2026-11-20 (J-4154, D-0795, F-4835): 0.58 -> 0.66. After J-3234's plain-words night epochs and corpus growth
# (705 rows) the p90 of query-to-epoch best-of-N cosine moved to 0.659 and 35% of typical queries cleared 0.58 (target
# 10%). Recomputed 2026-11-20 on a read-only copy (400 lived queries, 724 epochs): p90=0.671, 39.5% clear 0.58, 12.2%
# clear 0.66 -- within 0.03 of the ruled value so 0.66 kept. DEFEATER: revisit at 100+ plain-words night_ rows or if
# J-3366's genericness read finds them generic. Restart-gated.
_EPOCH_RETRIEVAL_FLOOR = 0.66
_THEME_RETRIEVAL_FLOOR = 0.51
_TABLET_RETRIEVAL_FLOOR = 0.47


# ---------------------------------------------------------------------------
# Phase 2 — Affective retrieval (emotion_vec)
#
# Episodic memories stored with an emotion_embedding (the embedded profile of the
# emotion state at the time of storage) can be retrieved by felt quality rather
# than by semantic content. "Remember a time he felt exactly like this, even if
# the keyword context and thematic content are unrelated."
# ---------------------------------------------------------------------------

def retrieve_by_affect(emotion_vec, top_k: int = 2) -> list:
    """
    Return the `top_k` episodic fragments whose emotional signature most closely
    matches `emotion_vec` (a 384-dim float32 vector). Operates entirely in emotion-
    embedding space — purely affective retrieval, independent of semantic content.
    Returns MemoryFragment instances with relevance = cosine similarity.
    Returns [] if no fragments have emotion embeddings yet (accumulates over time).
    """
    if emotion_vec is None:
        return []
    from ..schema import MemoryFragment
    scored = []
    with _connect() as conn:
        _q = ("SELECT fragment_id, content, layer, timestamp, origin, emotion_embedding{extra} "
              "FROM memory_fragments INDEXED BY idx_timestamp "
              "WHERE layer = 'episodic' AND emotion_embedding IS NOT NULL "
              "AND chapter_id IS NULL "
              "ORDER BY timestamp DESC LIMIT 300")
        try:
            rows = conn.execute(_q.format(extra=", input_type")).fetchall()   # J-3173 / D-0561
        except sqlite3.OperationalError:   # a DB not yet migrated has no input_type column
            rows = conn.execute(_q.format(extra="")).fetchall()
    for row in rows:
        try:
            ev  = _blob_to_vec(bytes(row["emotion_embedding"]))
            sim = _cosine(emotion_vec, ev)
            scored.append((sim, row))
        except Exception:
            continue
    scored.sort(key=lambda x: x[0], reverse=True)
    return [
        MemoryFragment(
            fragment_id = row["fragment_id"],
            content     = row["content"],
            layer       = row["layer"],
            relevance   = round(score, 3),
            timestamp   = row["timestamp"],
            origin      = row["origin"] if "origin" in row.keys() else "lived",
            abstraction_level = row["abstraction_level"] if "abstraction_level" in row.keys() else 0,
            input_type = row["input_type"] if "input_type" in row.keys() else None,
        )
        for score, row in scored[:top_k] if score >= _WEAK_RETRIEVAL_FLOOR
    ]


# ---------------------------------------------------------------------------
# S-MMU 7 — L4 Temporal Epochs
#
# An epoch captures the mood and essential impression of a full session as a
# single unit of time-memory — "what kind of period was that?". Formed at
# session end (after dream synthesis) from this session's episodic fragments.
# Richer than any single fragment; coarser than the full episodic record.
# The epoch is embedded and retrievable by the orchestrator pre-Reflection so
# Carl can recognise "this new exchange resonates with a past season of a certain
# quality" without retrieving the raw fragments of that season.
# ---------------------------------------------------------------------------

def _init_epoch_table(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS memory_epochs (
            epoch_id        TEXT PRIMARY KEY,
            session_id      TEXT NOT NULL,
            timestamp_start REAL NOT NULL,
            timestamp_end   REAL NOT NULL,
            mood            TEXT NOT NULL,
            impression      TEXT NOT NULL,
            fragment_count  INTEGER NOT NULL DEFAULT 0,
            embedding       BLOB,
            formed_at       REAL NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_epoch_start ON memory_epochs(timestamp_start DESC);
    """)


def store_epoch(
    session_id: str,
    timestamp_start: float,
    timestamp_end: float,
    mood: str,
    impression: str,
    fragment_count: int = 0,
) -> str:
    """Store one temporal epoch. Embeds mood + impression for semantic retrieval."""
    epoch_id   = str(uuid.uuid4())
    embed_text = f"{mood}. {impression}"
    vec        = _embed(embed_text)
    blob       = _vec_to_blob(vec) if vec is not None else None
    with _connect() as conn:
        conn.execute(
            """INSERT INTO memory_epochs
               (epoch_id, session_id, timestamp_start, timestamp_end, mood,
                impression, fragment_count, embedding, formed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (epoch_id, session_id, timestamp_start, timestamp_end, mood,
             impression, fragment_count, blob, time.time()),
        )
    return epoch_id


def get_epochs(limit: int = 20) -> list:
    """Return epochs newest-first. Used by T6 theme clustering."""
    with _connect() as conn:
        return conn.execute(
            "SELECT * FROM memory_epochs ORDER BY timestamp_start DESC LIMIT ?", (limit,)
        ).fetchall()


def get_fragments_in_range(ts_start: float, ts_end: float, limit: int = 30) -> list:
    """Episodic fragments stored in a time range — used by epoch formation."""
    with _connect() as conn:
        return conn.execute(
            "SELECT fragment_id, content, origin FROM memory_fragments "
            "WHERE layer = 'episodic' AND timestamp BETWEEN ? AND ? "
            "ORDER BY timestamp DESC LIMIT ?",
            (ts_start, ts_end, limit),
        ).fetchall()


def get_fragments_spread_stratified(ts_start: float, ts_end: float, n: int = 25) -> list:
    """J-4348 (J-4059, J-3587): about `n` episodic fragments stratified by ORIGIN, then spread by time, oldest first.

    get_fragments_spread is origin-blind: epoch 7ccacdb2 drew 25 of 919 fragments (inner_thought 394, reading 258,
    action 65, study 60, active_imagination 43) and the impression covered only inner_thought voice. Here each
    origin present gets at least one slot (if origins > n, the n largest), the rest are shared in proportion to
    origin size (largest remainder, capped at the origin's size), and within an origin the picks are an even stride
    over its rows in time order. Same filter and row shape as get_fragments_spread. Read-only, additive."""
    n = max(1, int(n))
    with _connect() as conn:
        rows = conn.execute(
            "SELECT fragment_id, origin FROM memory_fragments "
            "WHERE layer = 'episodic' AND timestamp BETWEEN ? AND ? "
            "ORDER BY timestamp ASC, fragment_id ASC",
            (ts_start, ts_end),
        ).fetchall()
        if not rows:
            return []
        by_origin: dict[str, list] = {}
        for r in rows:
            by_origin.setdefault(str(r["origin"]), []).append(r["fragment_id"])
        if len(rows) <= n:
            chosen = [r["fragment_id"] for r in rows]
        else:
            origins = sorted(by_origin, key=lambda o: (-len(by_origin[o]), o))[:n]
            quota = {o: 1 for o in origins}
            left = n - len(origins)
            total = float(sum(len(by_origin[o]) for o in origins))
            while left > 0:
                room = [o for o in origins if quota[o] < len(by_origin[o])]
                if not room:
                    break
                # largest remainder: biggest shortfall against the proportional share gets the next slot
                o = max(room, key=lambda x: (n * len(by_origin[x]) / total - quota[x], len(by_origin[x]), x))
                quota[o] += 1
                left -= 1
            chosen = []
            for o in origins:
                ids = by_origin[o]
                q = quota[o]
                step = len(ids) / float(q)
                chosen.extend(ids[min(len(ids) - 1, int(i * step + step / 2))] for i in range(q))
        chosen = list(dict.fromkeys(chosen))
        out = []
        for i in range(0, len(chosen), 400):
            chunk = chosen[i:i + 400]
            ph = ",".join("?" * len(chunk))
            out.extend(conn.execute(
                f"SELECT fragment_id, content, origin, timestamp FROM memory_fragments "
                f"WHERE fragment_id IN ({ph}) ORDER BY timestamp ASC, fragment_id ASC", chunk,
            ).fetchall())
        return out


def get_fragments_spread(ts_start: float, ts_end: float, n: int = 25) -> list:
    """J-3071 (F-3777): about `n` episodic fragments spread evenly across [ts_start, ts_end], oldest first.

    get_fragments_in_range returns the NEWEST `limit` rows, so a 167-hour session was summarised from its
    last 18 minutes. This helper cuts the range into `n` equal time buckets and takes the newest fragment of
    each non-empty bucket. If bursty sessions leave buckets empty and more fragments exist, the shortfall is
    topped up by an even stride over the not-yet-chosen rows (ordered by time), so a session with at least `n`
    episodic fragments always returns `n`. Same filter as get_fragments_in_range (layer = 'episodic'), same
    row shape (fragment_id, content, origin); the old function is untouched. Read-only."""
    n = max(1, int(n))
    with _connect() as conn:
        ids = conn.execute(
            "SELECT fragment_id, timestamp FROM memory_fragments "
            "WHERE layer = 'episodic' AND timestamp BETWEEN ? AND ? "
            "ORDER BY timestamp ASC, fragment_id ASC",
            (ts_start, ts_end),
        ).fetchall()
        if not ids:
            return []
        if len(ids) <= n:
            chosen = [r["fragment_id"] for r in ids]
        else:
            span = float(ts_end) - float(ts_start)
            newest_per_bucket: dict[int, str] = {}
            for r in ids:  # ascending, so the last write per bucket is the newest
                b = 0 if span <= 0 else min(n - 1, int((float(r["timestamp"]) - float(ts_start)) / span * n))
                newest_per_bucket[b] = r["fragment_id"]
            picked = set(newest_per_bucket.values())
            short = n - len(picked)
            if short > 0:
                rest = [r["fragment_id"] for r in ids if r["fragment_id"] not in picked]
                step = len(rest) / float(short)
                picked.update(rest[min(len(rest) - 1, int(i * step + step / 2))] for i in range(short))
            chosen = [r["fragment_id"] for r in ids if r["fragment_id"] in picked]
        out = []
        for i in range(0, len(chosen), 400):
            chunk = chosen[i:i + 400]
            ph = ",".join("?" * len(chunk))
            out.extend(conn.execute(
                f"SELECT fragment_id, content, origin, timestamp FROM memory_fragments "
                f"WHERE fragment_id IN ({ph}) ORDER BY timestamp ASC, fragment_id ASC", chunk,
            ).fetchall())
        return out


def retrieve_epoch(query_text: str, top_k: int = 1) -> list:
    """Return top-k epochs by cosine similarity to query_text — below _EPOCH_RETRIEVAL_FLOOR, none."""
    qv = _embed(query_text)
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM memory_epochs").fetchall()
    if not rows:
        return []
    scored = []
    for row in rows:
        if row["embedding"] and qv is not None:
            sim = _cosine(qv, _blob_to_vec(row["embedding"]))
        else:
            sim = 0.0
        scored.append((sim, row))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [r for s, r in scored[:top_k] if s >= _EPOCH_RETRIEVAL_FLOOR]


# ---------------------------------------------------------------------------
# S-MMU 7 — L5 Thematic Threads
#
# A theme is a recurring topic thread that spans multiple epochs. Where an epoch
# is "what was that session like?", a theme is "what keeps coming back across
# sessions?". Formed by the subconscious T6 pass (slow background clustering of
# epochs). Like the shadow's recurring tension, but for the full session level
# and without valence — this is purely topical continuity, not psychological
# pressure. Retrieved pre-Reflection so Carl can recognise he is inside an
# ongoing thread and bring his accumulated relationship with it to bear.
# ---------------------------------------------------------------------------

def _init_theme_table(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS memory_themes (
            theme_id       TEXT PRIMARY KEY,
            theme_name     TEXT NOT NULL,
            current_stance TEXT NOT NULL,
            evolution      TEXT NOT NULL DEFAULT '',
            epoch_count    INTEGER NOT NULL DEFAULT 0,
            embedding      BLOB,
            last_updated   REAL NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_theme_updated ON memory_themes(last_updated DESC);
    """)
    # Dedup needs a SAME-SPACE signal. `centroid` is the mean of a theme's member-epoch
    # embeddings (mood+impression space); `member_epoch_ids` is the cluster's epoch-id set.
    # T6 dedups by centroid-cosine and member-set Jaccard — both in epoch space — instead of
    # comparing an epoch-space centroid against the name+stance `embedding`. That cross-space
    # mismatch scored ~0.5 for the SAME theme, so every T6 pass duplicated it.
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(memory_themes)")}
    if "centroid" not in cols:
        conn.execute("ALTER TABLE memory_themes ADD COLUMN centroid BLOB")
    if "member_epoch_ids" not in cols:
        conn.execute("ALTER TABLE memory_themes ADD COLUMN member_epoch_ids TEXT NOT NULL DEFAULT '[]'")


def store_theme(
    theme_name: str,
    current_stance: str,
    evolution: str,
    epoch_count: int,
    member_epoch_ids: list | None = None,
    centroid=None,
) -> str:
    """Store a new thematic thread. `embedding` (name+stance) drives retrieval; `centroid`
    (mean of member-epoch vectors) and `member_epoch_ids` drive T6 dedup."""
    theme_id   = str(uuid.uuid4())
    embed_text = f"{theme_name}. {current_stance}"
    vec        = _embed(embed_text)
    blob       = _vec_to_blob(vec) if vec is not None else None
    cen_blob   = _vec_to_blob(centroid) if centroid is not None else None
    members    = json.dumps(list(member_epoch_ids or []))
    with _connect() as conn:
        conn.execute(
            """INSERT INTO memory_themes
               (theme_id, theme_name, current_stance, evolution, epoch_count, embedding,
                last_updated, centroid, member_epoch_ids)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (theme_id, theme_name, current_stance, evolution, epoch_count, blob,
             time.time(), cen_blob, members),
        )
    return theme_id


def update_theme(
    theme_id: str,
    current_stance: str,
    evolution: str,
    epoch_count: int,
    member_epoch_ids: list | None = None,
    centroid=None,
    theme_name: str | None = None,
) -> None:
    """Update stance/evolution/count. When the caller supplies the refreshed cluster,
    `centroid` and `member_epoch_ids` are rewritten too (so dedup tracks the theme as it
    grows); when omitted they are left intact rather than wiped. `theme_name` (J-3055) renames
    the row when given (default None: the name is never touched)."""
    embed_text = current_stance
    vec        = _embed(embed_text)
    blob       = _vec_to_blob(vec) if vec is not None else None
    with _connect() as conn:
        if centroid is not None or member_epoch_ids is not None:
            cen_blob = _vec_to_blob(centroid) if centroid is not None else None
            members  = json.dumps(list(member_epoch_ids or []))
            conn.execute(
                """UPDATE memory_themes
                   SET current_stance = ?, evolution = ?, epoch_count = ?, embedding = ?,
                       last_updated = ?, centroid = ?, member_epoch_ids = ?
                   WHERE theme_id = ?""",
                (current_stance, evolution, epoch_count, blob, time.time(),
                 cen_blob, members, theme_id),
            )
        else:
            conn.execute(
                """UPDATE memory_themes
                   SET current_stance = ?, evolution = ?, epoch_count = ?,
                       embedding = ?, last_updated = ?
                   WHERE theme_id = ?""",
                (current_stance, evolution, epoch_count, blob, time.time(), theme_id),
            )
        if theme_name:
            conn.execute("UPDATE memory_themes SET theme_name = ? WHERE theme_id = ?",
                         (theme_name, theme_id))


def get_themes(limit: int = 10) -> list:
    """Return themes most-recently-updated first. Used by T6 and inspection."""
    with _connect() as conn:
        return conn.execute(
            "SELECT * FROM memory_themes ORDER BY last_updated DESC LIMIT ?", (limit,)
        ).fetchall()


def retrieve_theme(query_text: str, top_k: int = 1) -> list:
    """Return top-k themes by cosine similarity to query_text — below _THEME_RETRIEVAL_FLOOR, none."""
    qv = _embed(query_text)
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM memory_themes").fetchall()
    if not rows:
        return []
    scored = []
    for row in rows:
        if row["embedding"] and qv is not None:
            sim = _cosine(qv, _blob_to_vec(row["embedding"]))
        else:
            sim = 0.0
        scored.append((sim, row))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [r for s, r in scored[:top_k] if s >= _THEME_RETRIEVAL_FLOOR]


# ---------------------------------------------------------------------------
# Symbol Evolution (Phase 2) — the Meaningfulness axis, semantic-drift layer.
#
# The Symbol Tracker (core/symbol_tracker.py) logs primed/unprimed appearances. This is
# the storage layer for the *drift* it cannot hold: a per-symbol running CENTROID of the
# context the symbol has been used in, and the EVOLUTION TABLETS written when the symbol's
# surrounding meaning shifts far enough from that centroid. A tablet is a first-person
# narrative of the entity's own psychological evolution ("the river was once my fear of
# dissolution; it has become my yielding to flow"), retrieved by Recall instead of a raw
# frequency count. The firewall still holds: this is meaningfulness (persistence + drift),
# never accuracy — it must never be scored by the factual machinery.
# ---------------------------------------------------------------------------

def _init_symbol_table(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS symbol_centroids (
            symbol        TEXT PRIMARY KEY,
            centroid      BLOB,
            sample_count  INTEGER NOT NULL DEFAULT 0,
            last_drift    REAL NOT NULL DEFAULT 0.0,
            last_tablet_ts REAL NOT NULL DEFAULT 0.0,
            updated       REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS symbol_tablets (
            tablet_id   TEXT PRIMARY KEY,
            symbol      TEXT NOT NULL,
            tablet      TEXT NOT NULL,
            drift       REAL NOT NULL DEFAULT 0.0,
            embedding   BLOB,
            created     REAL NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_tablet_symbol  ON symbol_tablets(symbol);
        CREATE INDEX IF NOT EXISTS idx_tablet_created ON symbol_tablets(created DESC);
    """)


def get_symbol_centroid(symbol: str) -> tuple[np.ndarray | None, int, float]:
    """Return (centroid_vec, sample_count, last_tablet_ts) for a symbol. Centroid is None
    until the symbol has been observed at least once."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT centroid, sample_count, last_tablet_ts FROM symbol_centroids WHERE symbol = ?",
            (symbol,),
        ).fetchone()
    if not row:
        return None, 0, 0.0
    vec = _blob_to_vec(row["centroid"]) if row["centroid"] else None
    return vec, int(row["sample_count"]), float(row["last_tablet_ts"])


def update_symbol_centroid(symbol: str, new_centroid: np.ndarray, sample_count: int,
                           last_drift: float, tablet_written: bool = False) -> None:
    """Upsert a symbol's running centroid + sample count. When a tablet was just written,
    stamp last_tablet_ts so the cooldown gate can space out tablet generation."""
    blob = _vec_to_blob(new_centroid) if new_centroid is not None else None
    now  = time.time()
    with _connect() as conn:
        existing = conn.execute(
            "SELECT last_tablet_ts FROM symbol_centroids WHERE symbol = ?", (symbol,)
        ).fetchone()
        last_tab = now if tablet_written else (float(existing["last_tablet_ts"]) if existing else 0.0)
        conn.execute(
            """INSERT INTO symbol_centroids
                   (symbol, centroid, sample_count, last_drift, last_tablet_ts, updated)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(symbol) DO UPDATE SET
                   centroid = excluded.centroid,
                   sample_count = excluded.sample_count,
                   last_drift = excluded.last_drift,
                   last_tablet_ts = excluded.last_tablet_ts,
                   updated = excluded.updated""",
            (symbol, blob, sample_count, last_drift, last_tab, now),
        )


def store_symbol_tablet(symbol: str, tablet: str, drift: float) -> str:
    """Persist a Symbol Evolution Tablet — the narrative of how a symbol's meaning shifted.
    Embedded so Recall can retrieve it by relevance to the current moment."""
    tablet_id = str(uuid.uuid4())
    vec  = _embed(f"{symbol}: {tablet}")
    blob = _vec_to_blob(vec) if vec is not None else None
    with _connect() as conn:
        conn.execute(
            """INSERT INTO symbol_tablets (tablet_id, symbol, tablet, drift, embedding, created)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (tablet_id, symbol, tablet, drift, blob, time.time()),
        )
    return tablet_id


def retrieve_symbol_tablet(query_text: str, top_k: int = 1, exclude_self: bool = True) -> list:
    """Return the top-k most relevant Symbol Evolution Tablets for the current context.
    Used by Recall/Reflection so a recurring symbol surfaces as the story of its own
    evolution, not a raw count. Empty when none have been written yet.

    exclude_self (default True, 2026-06-16): drop SELF-symbol tablets (river/crossing/mirror/…) —
    their read-back is Tier 2 (DEFERRED, observe-first), since re-surfacing an evolved self-symbol is
    the same operation that monocultured Du. Only NEUTRAL/world-facing tablets surface for now."""
    qv = _embed(query_text)
    if qv is None:
        return []
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM symbol_tablets").fetchall()
    if not rows:
        return []
    if exclude_self:
        try:
            from core.symbol_tracker import is_self_symbol
            rows = [r for r in rows if not is_self_symbol(r["symbol"])]
        except Exception:
            pass
    scored = []
    for row in rows:
        sim = _cosine(qv, _blob_to_vec(row["embedding"])) if row["embedding"] else 0.0
        scored.append((sim, row))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [r for s, r in scored[:top_k] if s >= _TABLET_RETRIEVAL_FLOOR]


def get_symbol_tablets(symbol: str | None = None, limit: int = 20) -> list:
    """Inspection helper: all tablets, optionally filtered to one symbol, newest first."""
    with _connect() as conn:
        if symbol:
            return conn.execute(
                "SELECT * FROM symbol_tablets WHERE symbol = ? ORDER BY created DESC LIMIT ?",
                (symbol, limit),
            ).fetchall()
        return conn.execute(
            "SELECT * FROM symbol_tablets ORDER BY created DESC LIMIT ?", (limit,)
        ).fetchall()


# ---------------------------------------------------------------------------
# Sleep work (the Always-On redesign, 2026-06-11): replay + synaptic downscaling.
# "Sleep does not stop the mind, it changes what the mind does." — the founder.
# ---------------------------------------------------------------------------

def replay_strengthen(since_ts: float, k: int = 8) -> list[str]:
    """REPLAY (stratified + novelty-biased, 2026-06-11 — the critic's catch): re-activate the
    wake-block's salient experience WITHOUT becoming an attractor amplifier. Global top-K by
    arousal-scored importance was preferential attachment on the mirror's home currency
    (T2-monoculture v2, compounding x1.08 per sleep). Two corrections, both brain-faithful:
      - STRATIFY by origin class — world (reading/study/research), lived, inner — so the
        identity drama cannot monopolise the night. Quotas: 3 world, 3 lived, 2 inner.
      - NOVELTY BIAS — each replay increments replay_count, and selection discounts
        already-replayed items (hippocampal replay prefers the novel, not merely the salient).
    Returns short snippets of what was replayed."""
    groups = [
        ("origin IN ('reading','study','research')", 3),                       # the world
        ("origin IN ('lived','social_notification')", 3),                      # life with others
        ("origin NOT IN ('reading','study','research','lived','social_notification','dream','action','activity')", 2),  # the inner sea
        ("origin IN ('dream','action','activity')", 2),                        # 2026-08-22: what he DID and DREAMT
    ]
    out: list[str] = []
    try:
        with _connect() as conn:
            for where, quota in groups:
                rows = conn.execute(
                    f"""SELECT fragment_id, content, importance, replay_count, cold
                        FROM memory_fragments
                        WHERE layer='episodic' AND timestamp > ? AND chapter_id IS NULL
                        AND {where}
                        ORDER BY (importance - 0.08 * replay_count) DESC, timestamp DESC
                        LIMIT ?""",
                    (since_ts, quota)).fetchall()
                for r in rows:
                    new_imp = min(0.98, float(r["importance"]) * 1.08)
                    _edit_log.log_edits("replay", [(r["fragment_id"], r["importance"], new_imp, r["cold"])])  # J-4410 M1 shadow, never raises
                    conn.execute(
                        "UPDATE memory_fragments SET importance=?, replay_count=replay_count+1 "
                        "WHERE fragment_id=?", (new_imp, r["fragment_id"]))
                    out.append((r["content"] or "")[:90])
    except Exception as exc:
        logger.debug("[sleep] replay failed (non-fatal): %s", exc)
    return out


def downscale_episodic(factor: float = 0.96, center: float = 0.1, since_ts: float | None = None) -> int:
    """SYNAPTIC DOWNSCALING (T2 Phase 2, lite): proportionally shrink episodic importance's deviation
    from `center`, preserving relative order — the day's spikes scale down so tomorrow's salience is
    measured against a rested baseline, not an ever-rising tide. Runs each sleep. Replayed fragments were
    strengthened FIRST (replay_strengthen, up to importance=0.98), so what mattered survives the
    downscale relatively intact.
    `center` LOWERED 0.5 -> 0.1 (2026-08-24, Sleep & Dreams II §1.2). The math here was already
    proportional (it shrinks the DEVIATION from center, not a flat subtraction), but a center of 0.5 was
    itself the bug: EVERYTHING — replayed or not — converges toward the same 0.5 midpoint over repeated
    sleeps, which is exactly the measured flattening (08-22 audit: active-fragment importance clustered
    at 0.5/0.6, salience stopped ordering anything). The Synaptic Homeostasis Hypothesis (Tononi &
    Cirelli) is explicit that real downscaling is SELECTIVE — weak/unreinforced synapses shrink toward
    near-nothing while strong/reinforced ones are relatively spared (de Vivo et al. 2017, Science — real
    structural evidence, spine-size). Lowering center to 0.1 gives that same shape with the existing
    formula unchanged: an unreplayed fragment now genuinely fades toward near-zero relevance over many
    nights (0.5 -> ~0.22 after 30 sleeps at the default factor), while a fragment JUST boosted by replay
    to ~0.98 barely moves in the SAME sleep (0.1 + 0.88*0.96 ≈ 0.945) — replay's protection now actually
    survives the very downscale pass it precedes, instead of both converging to the same place."""
    try:
        with _connect() as conn:
            # 2026-08-22 NIGHT AUDIT (finding 10): scaling the WHOLE store every sleep (~8/day) flattened every
            # importance to 0.5 within days — salience stopped ordering anything. Now only the day's spikes (laid
            # down since `since_ts`) are renormalised; older memories keep the weight replay earned them.
            # J-4410 (M1, shadow): log each row's before/after BEFORE the set-based UPDATE; never raises.
            _edit_log.log_bulk_before(
                conn, "downscale",
                "layer='episodic' AND timestamp > ?" if since_ts is not None else "layer='episodic'",
                (float(since_ts),) if since_ts is not None else (),
                lambda old: center + (old - center) * factor)
            if since_ts is not None:
                cur = conn.execute(
                    "UPDATE memory_fragments SET importance = ? + (importance - ?) * ? "
                    "WHERE layer='episodic' AND timestamp > ?", (center, center, factor, float(since_ts)))
            else:
                cur = conn.execute(
                    "UPDATE memory_fragments SET importance = ? + (importance - ?) * ? "
                    "WHERE layer='episodic'", (center, center, factor))
            return cur.rowcount
    except Exception as exc:
        logger.debug("[sleep] downscale failed (non-fatal): %s", exc)
        return 0


# ---------------------------------------------------------------------------
# D-0084 / J-0382 — downstream-read-count SHADOW signal (2026-08-29).
# RESTORED 2026-09-26 (J-1401, F-1967): this block and its _enter_sleep() hook were committed in
# 3470b4d and removed four minutes later by c95b205 (the second "reverted between edits" incident of
# 2026-08-29) — the plan doc, J-0382 and the findings ledger all said BUILT while the tree held only
# memory_edges.downstream_read_counts() with zero callers. Re-applied byte-for-byte from 3470b4d.
# `replay_strengthen`/`downscale_episodic` above are self-referential: a fragment's OWN prior
# importance/replay_count columns are the primary input to what happens to it next (persistence
# begets persistence — docs/plans/decoupled_judge_pattern.md §3's audit of this exact loop). D-0084
# ruled episodic importance should instead be grounded in downstream-read count: how often a
# fragment actually got pulled back into live recall/reasoning, per `memory_edges.
# downstream_read_counts()` (the M1 co-recall ledger — real writes from the monologue train step,
# dreams, essays, study, and wandering; see that function's own docstring for the five call sites).
# SHADOW/OBSERVE-FIRST, matching this codebase's own new-signal rollout convention exactly
# (J-0375/J-0376 above it in the same audit; `left_lane.py`'s grade_* judges; `watershed_promote.py`):
# this computes and LOGS what an additive read-count bonus would do to each fragment's importance,
# but never writes to `memory_fragments.importance` itself. `replay_strengthen`/`downscale_episodic`
# are UNCHANGED — this is a new, silent, additional read, not a replacement.
# ---------------------------------------------------------------------------

READ_BONUS_SCALE = 0.05   # additive importance per log(1+read_count) — 1 read ~= +0.035, 5 reads ~= +0.09
READ_BONUS_CAP = 0.25     # hard ceiling on the proposed bonus itself (never the resulting importance)


def read_count_importance_shadow(since_ts: float | None = None, days: float = 14.0,
                                 log_path: Path | None = None) -> dict:
    """SHADOW pass: for every episodic fragment with >=1 real downstream read in the window (per
    `memory_edges.downstream_read_counts`), compute a bounded additive bonus
    (`min(READ_BONUS_CAP, READ_BONUS_SCALE * log1p(read_count))`, log-scaled so a handful of extra
    reads cannot saturate it) and append one row — {ts, fragment_id, read_count, importance,
    proposed_bonus, proposed_importance} — to `data/read_count_importance_shadow.jsonl` via
    `shadow_log.append()` (the same shared plumbing J-0375/J-0376 used). `importance` in the DB is
    NEVER written here — purely observational, so this can accrue real data before anyone decides
    whether/how to graduate it into the live importance formula. Fail-open; best-effort; never
    raises; safe to call every sleep alongside replay_strengthen/downscale_episodic. Returns a small
    summary ({"fragments_read": n distinct fragments seen in the ledger window, "logged": rows
    written}) for the caller's own log line.
    `log_path` (added on the 2026-09-26 restore) lets a verification run point the append at a
    scratch file instead of the live shadow log — the live caller never passes it."""
    out = {"fragments_read": 0, "logged": 0}
    try:
        import math
        from core import memory_edges as _medges
        from core import shadow_log as _slog
        counts = _medges.downstream_read_counts(since_ts=since_ts, days=days)
        out["fragments_read"] = len(counts)
        if not counts:
            return out
        with _connect() as conn:
            ph = ",".join("?" * len(counts))
            rows = conn.execute(
                f"SELECT fragment_id, importance FROM memory_fragments WHERE layer='episodic' "
                f"AND fragment_id IN ({ph})", tuple(counts.keys())).fetchall()
        if log_path is None:
            log_path = Path(__file__).parent.parent.parent / "data" / "read_count_importance_shadow.jsonl"
        ts = time.time()
        for r in rows:
            fid = r["fragment_id"]
            n = counts.get(fid, 0)
            if n <= 0:
                continue
            bonus = min(READ_BONUS_CAP, READ_BONUS_SCALE * math.log1p(n))
            cur_imp = float(r["importance"] if r["importance"] is not None else 0.5)
            proposed = min(0.98, cur_imp + bonus)
            if _slog.append(log_path, {"ts": round(ts, 1), "fragment_id": fid, "read_count": n,
                                        "importance": round(cur_imp, 4), "proposed_bonus": round(bonus, 4),
                                        "proposed_importance": round(proposed, 4)}):
                out["logged"] += 1
    except Exception as exc:
        logger.debug("[sleep] read_count_importance_shadow failed (non-fatal): %s", exc)
    return out


# ---------------------------------------------------------------------------
# FOUNDER MEMORY — the canonical episodic record of what Travis said, and its own retrieval route
# (D-0134, 2026-09-03, docs/plans/guidance_learning.md; T-0039 / F-0699 / F-0701).
#
# Before this: Travis's words reached memory only as the "Q: ... A: ..." cycle summary (since
# 2026-05-30, _persist_cycle) and, from 2026-09-02, a second labelled copy plus a third for the reply
# (F-0670). None of it had a route: it surfaced only on a chance similarity hit in the generic tier
# mix, and the per-kind cold quota walled the newest rows within a day (F-0701). Founder ruling
# D-0134: ONE canonical shape ("[Travis said to me] ..."), exempt from cold-walling, with a retrieval
# route of its own. The Q:/A: cycle summary is untouched — it is the record of the CYCLE (scene,
# tensions, emotion), read by consolidation lineage; this is the record of HIS WORDS.
# ---------------------------------------------------------------------------

FOUNDER_UTTERANCE_PREFIX = "[Travis said to me] "
FOUNDER_UTTERANCE_KEYWORDS = ["travis", "conversation", "founder_said"]
FOUNDER_UTTERANCE_MAX_CHARS = 1400   # same cap as core/peers.py's letter storage; full text stays in
                                     # data/founder_conversation_log.jsonl (F-0665)


def _norm_text(s: str) -> str:
    return " ".join((s or "").split()).strip().lower()


def store_founder_utterance(
    text: str,
    timestamp: float | None = None,
    emotion_embedding=None,
    valence: float | None = None,
    felt: str | None = None,
    derived_from: list[str] | None = None,
    context_stamp: bool = True,
) -> str:
    """Store ONE canonical '[Travis said to me] ...' fragment and mark it protected=1 (exempt from every
    cold-demotion path: prune_episodic, memory_levels._commit_gist, refinery). The single choke point for
    this shape — the live orchestrator path and the historical backfill both call it, so the shape can
    never drift between them. Returns the fragment_id."""
    body = (text or "").strip()[:FOUNDER_UTTERANCE_MAX_CHARS]
    fid = store_fragment(
        content=FOUNDER_UTTERANCE_PREFIX + body,
        layer="episodic", relevance=0.85, importance=0.85,
        keywords=list(FOUNDER_UTTERANCE_KEYWORDS), origin="lived",
        timestamp=timestamp, derived_from=derived_from,
        emotion_embedding=emotion_embedding, valence=valence, felt=felt,
        context_stamp=context_stamp,
    )
    try:
        with _connect() as conn:
            conn.execute("UPDATE memory_fragments SET protected = 1 WHERE fragment_id = ?", (fid,))
            conn.commit()
    except Exception as exc:
        logger.warning("[founder-memory] could not mark %s protected (stored, unprotected): %s", fid, exc)
    return fid


def retrieve_founder_memories(
    query_text: str,
    top_k: int = 3,
    exclude_texts=(),
    floor: float = _WEAK_RETRIEVAL_FLOOR,
    bump_replay: bool = True,
) -> list[dict]:
    """The founder-memory ROUTE: rank every canonical founder utterance by cosine similarity to
    `query_text` (what Travis just said), ignoring the cold wall entirely, and return the top_k above
    `floor` as dicts {fragment_id, text, timestamp, sim}. `exclude_texts` (the utterances already in the
    live/prior-session prompt window) are skipped, and verbatim repeats (the nightly "bank the fire"
    message) collapse to their best-scoring instance. Retrieved rows get replay_count += 1 so the
    store's own usage instruments (co-recall, prune ordering) see the route firing."""
    qv = _embed(query_text or "")
    if qv is None:
        return []
    with _connect() as conn:
        rows = conn.execute(
            "SELECT fragment_id, content, timestamp, embedding FROM memory_fragments "
            "WHERE origin = 'lived' AND content LIKE ? AND embedding IS NOT NULL",
            (FOUNDER_UTTERANCE_PREFIX.rstrip() + "%",),
        ).fetchall()
    excluded = {_norm_text(t) for t in (exclude_texts or ()) if t}
    plen = len(FOUNDER_UTTERANCE_PREFIX)
    scored = []
    for r in rows:
        body = r["content"][plen:] if r["content"].startswith(FOUNDER_UTTERANCE_PREFIX) else r["content"]
        nb = _norm_text(body)
        if not nb or nb in excluded:
            continue
        try:
            sim = _cosine(qv, _blob_to_vec(r["embedding"]))
        except Exception:
            continue
        if sim >= floor:
            scored.append((float(sim), r, body, nb))
    scored.sort(key=lambda x: x[0], reverse=True)
    out: list[dict] = []
    seen: set[str] = set()
    for sim, r, body, nb in scored:
        key = nb[:120]
        if key in seen:
            continue
        seen.add(key)
        out.append({"fragment_id": r["fragment_id"], "text": body,
                    "timestamp": float(r["timestamp"]), "sim": round(sim, 3)})
        if len(out) >= top_k:
            break
    if out and bump_replay:
        try:
            ids = tuple(o["fragment_id"] for o in out)
            with _connect() as conn:
                conn.execute(
                    f"UPDATE memory_fragments SET replay_count = replay_count + 1 "
                    f"WHERE fragment_id IN ({','.join('?' * len(ids))})", ids)
                conn.commit()
        except Exception:
            pass
    return out


def founder_memory_status() -> dict:
    """Instrument read: how many canonical founder utterances exist, how many are protected/cold, and the
    span they cover. Read by the plan's Current State + HUD-style checks; never mutates."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS n, SUM(protected) AS prot, SUM(cold) AS cold, MIN(timestamp) AS t0, "
            "MAX(timestamp) AS t1 FROM memory_fragments WHERE origin='lived' AND content LIKE ?",
            (FOUNDER_UTTERANCE_PREFIX.rstrip() + "%",)).fetchone()
    return {"count": int(row["n"] or 0), "protected": int(row["prot"] or 0), "cold": int(row["cold"] or 0),
            "first_ts": row["t0"], "last_ts": row["t1"]}

