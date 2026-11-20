"""
key_shadow.py -- J-3310 (D-0552, plan memory_knowledge, prompt row P-0004 MemoryRouterNode).
Design: docs/reviews/memory_router_keys_shadow_design_J-3163.md sections 3.1-3.4.

WHAT THIS IS. An OBSERVE-ONLY instrument that answers one question for the founder's D-0552 read: if the memory
router's keys (episodic_keys + semantic_keys) were allowed to do work in retrieval, which memories would change?
store.retrieve() -- a PROTECTED base system, not edited by this job -- ranks the pool by cosine to the embedding of
raw_input + perception.summary and uses the keys only as a keyword fallback for rows with no embedding (0 of 45k+).
So the keys are write-only in effect (F-3495). This module re-scores the SAME cached embedding matrix, off to the
side, under four arms, and logs the id sets. It changes nothing Du reads (D-0434): the return value of
retrieve() is untouched, the log has no reader inside Du, and a failure here is swallowed.

ARMS (all use the same tier/slot cascade, recency multiplier, seed weight and climate warp as retrieve()):
  plain   a recomputation of what retrieve() ranks (the validity self-check: plain must be a subset of what live
          returned; live adds 5 recency-guarantee rows and any trail / deep-recall rows on top)
  A05     key-vector BLEND, alpha 0.5:  warp(normalise(qv + 0.5*kv))     (headline arm)
  A025    the same at alpha 0.25                                          (dose point)
  B       key SLOT RESERVATION: the 2 best key-only hits (warp(kv)) not already in the plain set, outside the
          archive tier, replace the 2 lowest-scoring non-archive plain slots; the top-1 plain hit is never replaced
  N       NEGATIVE CONTROL: arm A05 using the PREVIOUS shadow call's keys. It must lose to plain in the judged
          read; if it does not, the judge cannot see quality and the verdict is void (design section 3.1 / 4.2)
Dropped on purpose: "widen the candidate pool" -- retrieve() already scores the whole pool, so it is a no-op.

WHAT IT READS. The cached embedding matrix and pool membership through ONE additive accessor,
core.memory.store.pool_embedding_view() (no new SQL, no second matrix in RAM). When the pool-delta cache is not
serving (mode off, invalid, matrix just reset) the call logs a small `skipped` row instead of guessing.

KEYS. A junk-token filter runs before embedding (placeholder / pronoun tokens the router model emits from the
"Key entities:" line, F-3438 / F-3496; same token list as J-2836): they can never pollute the key vector, and the
count is logged (junk_keys_n). Keys are deduplicated in order. A cycle with no usable keys logs the plain recomputation
only.

SAFETY. KEY_SHADOW_ON kill switch; the log path is fenced with profile.guard_path (D-0179) and the module is in
core.profile's rebase list; fail-open (shadow_compare_keys never raises); restart-gated (Du is live, nothing runs
until the next restart). Farewell cycles (D-0442) are logged and flagged `farewell`, because retrieve() takes its
legacy path there and plain_matches_live is not expected to hold.

READER. scripts/key_shadow_summary.py prints the validity rate, overlap, origin shift and latency from the log;
the judged read itself is J-3309's offline replay (it imports compute_arms from here so the two cannot drift).
"""
from __future__ import annotations

import json
import logging
import threading
import time
from itertools import repeat
from operator import itemgetter
from typing import Any

import numpy as np

from core import profile   # the write fence (D-0179) and the data root

logger = logging.getLogger("nascence.key_shadow")

KEY_SHADOW_ON = True            # kill switch: False = the call returns at once, nothing is read or written
ALPHAS = (0.5, 0.25)            # A05 (headline) and A025 (dose point)
HEAD_ALPHA = 0.5
B_SLOTS = 2                     # arm B: slots reserved for key-only hits
MAX_KEYS_LOGGED = 12
MAX_KEY_CHARS = 80

# path anchored on profile._DATA so activate_profile() rebases it (core.memory.key_shadow is in profile's rebase
# tuple) and guard_path() refuses a non-live process
_LOG = profile._DATA / "key_shadow.jsonl"
_APPEND_LOCK = threading.Lock()

# Placeholder / pronoun tokens that are never a memory key. Matched after lower-casing, stripping punctuation and
# collapsing whitespace, EXACT match only (a real key such as "the person I met" must survive). Same set as the
# J-2836 entities fix (F-3496), plus the router's own "none".
JUNK_KEYS = frozenset({
    "the_entity", "the_person", "the_world", "you", "string", "none", "mixed",
    "the entity", "the person", "the world",
    "the person the entity is speaking with", "the entity's interlocutor", "the entitys interlocutor",
    "key entities",
})

# retrieve()'s tier order and slot counts come from the store constant, so a retune of TIER_SLOTS follows here
_TIER_CODE = {"archive": 0, "semantic": 1, "episodic": 2, "working": 3}

# the previous shadow call's key vector (arm N); guarded, process-local
_PREV_LOCK = threading.Lock()
_PREV_KV: np.ndarray | None = None

# prep cache: the per-row arrays of the previous snapshot, patched incrementally by tuple identity (see _patch_prep)
_PREP_LOCK = threading.Lock()
_PREP: Any = None
_PATCH_MAX = 2000               # more new+removed rows than this since the last call -> full rebuild


# ---------------------------------------------------------------- keys
def _norm_key(k: Any) -> str:
    s = str(k or "").strip().lower()
    s = "".join(ch for ch in s if ch.isalnum() or ch in (" ", "_", "'"))
    return " ".join(s.split())


def _key_lists(keys: Any) -> tuple[list, list]:
    """Accept the router's MemoryKeys object, a dict, an (episodic, semantic) pair, or a flat list of strings."""
    if keys is None:
        return [], []
    if hasattr(keys, "episodic_keys") or hasattr(keys, "semantic_keys"):
        return list(getattr(keys, "episodic_keys", None) or []), list(getattr(keys, "semantic_keys", None) or [])
    if isinstance(keys, dict):
        return list(keys.get("episodic_keys") or []), list(keys.get("semantic_keys") or [])
    if isinstance(keys, (tuple, list)) and len(keys) == 2 and all(isinstance(x, (list, tuple)) for x in keys):
        return list(keys[0]), list(keys[1])
    if isinstance(keys, (list, tuple)):
        return list(keys), []
    return [], []


def clean_keys(episodic: list, semantic: list) -> tuple[list[str], int]:
    """(usable keys in order, deduplicated, junk-filtered; number of junk tokens dropped)."""
    out: list[str] = []
    seen: set[str] = set()
    junk = 0
    for k in list(episodic) + list(semantic):
        if not isinstance(k, str) or not k.strip():
            continue
        n = _norm_key(k)
        if not n or n in JUNK_KEYS:
            junk += 1
            continue
        if n in seen:
            continue
        seen.add(n)
        out.append(k.strip())
    return out, junk


# ---------------------------------------------------------------- vectors and scoring (pure)
def _warp(v, bias_vec, bias_weight):
    """The climate warp exactly as store.retrieve() applies it (no-op on any shape / None issue)."""
    if v is None:
        return None
    if bias_vec is not None and bias_weight and float(bias_weight) > 0.0:
        try:
            warped = v + float(bias_weight) * np.asarray(bias_vec, dtype=np.float32)
            norm = float(np.linalg.norm(warped))
            if norm > 0.0:
                return (warped / norm).astype(np.float32)
        except Exception as exc:
            logger.debug("key_shadow climate warp skipped (non-fatal): %s", exc)
    return v


def _blend(qv, kv, alpha: float):
    b = qv + float(alpha) * kv
    n = float(np.linalg.norm(b))
    return (b / n).astype(np.float32) if n > 0.0 else qv


class _Prep:
    """Per-row arrays derived from one pool snapshot (pool order). `tups` is the snapshot's own tuple list (kept
    alive so the identity array below cannot be fooled by a recycled address); fragment id / origin of a selected
    row are read from it on demand instead of being copied out for all 51k rows."""
    __slots__ = ("n", "gen", "ident", "tups", "slots", "tier", "ts", "seed", "tier_idx")

    def fid(self, i: int) -> str:
        return self.tups[i][1]

    def origin(self, i: int) -> str:
        return self.tups[i][4]


def _row_arrays(rows: list) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(tier code, timestamp, is_seed) for a list of pool tuples."""
    m = len(rows)
    ts = np.fromiter(map(itemgetter(3), rows), dtype=np.float64, count=m)
    tier = np.fromiter(map(_TIER_CODE.get, map(itemgetter(2), rows), repeat(2)), dtype=np.int8, count=m)  # unknown layer -> episodic, as retrieve() does
    seed = np.fromiter(map("seed".__eq__, map(itemgetter(4), rows)), dtype=bool, count=m)
    return tier, ts, seed


def _finish(p: _Prep, tups: list, ident: np.ndarray, slots: np.ndarray, gen) -> _Prep:
    p.n = len(tups)
    p.gen = gen
    p.ident = ident
    p.tups = tups
    p.slots = slots
    p.tier_idx = [np.nonzero(p.tier == c)[0] for c in (0, 1, 2)]
    return p


def _build_prep(view: dict) -> _Prep:
    """Full build from a snapshot. O(pool) in Python (about 100 ms on a 51k pool on a loaded box); the incremental
    path in _prep_for avoids it when the pool changed by a few rows since the previous call."""
    tups = view["tups"]
    p = _Prep()
    p.tier, p.ts, p.seed = _row_arrays(tups)
    ident = np.fromiter(map(id, tups), dtype=np.int64, count=len(tups))
    return _finish(p, tups, ident, np.asarray(view["slots"], dtype=np.int64), view.get("gen"))


def _patch_prep(c: _Prep, view: dict) -> _Prep | None:
    """Incremental prep. store's pool-delta cache replaces a tuple object whenever its row changes and keeps the
    others, so tuple IDENTITY says which rows are new; only those are read. Returns None (caller does a full build)
    when it cannot prove an exact patch: another generation, too many changes, or kept rows out of order."""
    tups = view["tups"]
    n = len(tups)
    ident = np.fromiter(map(id, tups), dtype=np.int64, count=n)
    slots = np.asarray(view["slots"], dtype=np.int64)
    p = _Prep()
    if n == c.n and np.array_equal(ident, c.ident):
        p.tier, p.ts, p.seed = c.tier, c.ts, c.seed
        return _finish(p, tups, ident, slots, view.get("gen"))
    common, io, inw = np.intersect1d(c.ident, ident, assume_unique=True, return_indices=True)
    if (n - len(common)) + (c.n - len(common)) > _PATCH_MAX:
        return None
    keep_old = np.zeros(c.n, dtype=bool)
    keep_old[io] = True
    is_new = np.ones(n, dtype=bool)
    is_new[inw] = False
    if not np.array_equal(c.ident[keep_old], ident[~is_new]):
        return None                                       # kept rows did not keep their relative order
    new_idx = np.nonzero(is_new)[0]
    t_n, ts_n, sd_n = _row_arrays([tups[i] for i in new_idx])
    p.tier = np.empty(n, dtype=np.int8)
    p.ts = np.empty(n, dtype=np.float64)
    p.seed = np.empty(n, dtype=bool)
    for dst, old, new in ((p.tier, c.tier, t_n), (p.ts, c.ts, ts_n), (p.seed, c.seed, sd_n)):
        dst[~is_new] = old[keep_old]
        dst[new_idx] = new
    return _finish(p, tups, ident, slots, view.get("gen"))


def _prep_for(view: dict) -> _Prep:
    global _PREP
    with _PREP_LOCK:
        c = _PREP
    p = None
    if c is not None and c.gen == view.get("gen"):
        try:
            p = _patch_prep(c, view)
        except Exception as exc:
            logger.debug("key_shadow prep patch failed (%s); full build", exc)
    if p is None:
        p = _build_prep(view)
    with _PREP_LOCK:
        _PREP = p
    return p


def _weights(p: _Prep, time_bias: str, now: float) -> tuple[np.ndarray, np.ndarray]:
    """(recency multiplier, seed weight) per pool row, the _score_tier_vec formulas. The archive tier is scored
    with time_bias "all" and without the seed weight, as retrieve() does."""
    age_days = (now - p.ts) / 86400.0
    if time_bias == "recent":
        rec = 1.0 + 0.2 * np.maximum(0.0, 1.0 - age_days / 7.0)
    elif time_bias == "distant":
        rec = 1.0 + 0.1 * np.minimum(age_days / 7.0, 1.0)
    else:
        rec = np.ones(p.n, dtype=np.float64)
    rec = np.where(p.tier == 0, 1.0, rec)
    sw = np.ones(p.n, dtype=np.float64)
    from core.memory.store import _seed_weight
    for i in np.nonzero(p.seed & (p.tier != 0))[0]:
        sw[i] = _seed_weight(float(p.ts[i]))
    return rec, sw


def _scores(mat: np.ndarray, p: _Prep, vec: np.ndarray, rec: np.ndarray, sw: np.ndarray) -> np.ndarray:
    """Final per-row ranking score under `vec`. Rows with no usable embedding score 0 here (retrieve() uses a
    keyword fallback for them; they number 0 of 45k+ and are counted in the log as no_emb_n). The never-retrieved
    'working' tier is masked to -inf."""
    sims_all = mat @ np.asarray(vec, dtype=np.float32)
    sims = np.where(p.slots >= 0, sims_all[np.maximum(p.slots, 0)], 0.0).astype(np.float64)
    score = sims * rec
    score = score * sw
    score[p.tier == 3] = -np.inf
    return score


def _top_stable(vals: np.ndarray, k: int) -> np.ndarray:
    """Positions of the k largest `vals`, ties broken by position -- identical to a stable argsort of -vals, but
    O(n) (np.partition) instead of a full sort. All ties at the boundary are kept before the stable cut."""
    m = vals.shape[0]
    if m == 0 or k <= 0:
        return np.zeros(0, dtype=np.int64)
    neg = -vals
    if k >= m:
        return np.argsort(neg, kind="stable")
    thr = np.partition(neg, k - 1)[k - 1]
    cand = np.nonzero(neg <= thr)[0]
    return cand[np.argsort(neg[cand], kind="stable")][:k]


def _slot_plan() -> list[tuple[int, int]]:
    from core.memory.store import TIER_SLOTS
    return [(_TIER_CODE.get(name, 2), int(n)) for name, n in TIER_SLOTS.items()]


def _select(score: np.ndarray, p: _Prep) -> list[int]:
    """retrieve()'s tier loop: archive, semantic, episodic in TIER_SLOTS order; a short tier's unused slots cascade
    to the next, the last (episodic) takes the overflow. Returns pool indices in result order."""
    out: list[int] = []
    spare = 0
    last_code = _slot_plan()[-1][0]
    for code, n_slots in _slot_plan():
        n = n_slots + spare
        spare = 0
        idx = p.tier_idx[code] if code < 3 else np.zeros(0, dtype=np.int64)
        top = _top_stable(score[idx], n)
        taken = idx[top]
        out.extend(int(i) for i in taken)
        if code != last_code:
            spare = n - len(taken)
    return out


def _arm_b(plain: list[int], plain_score: np.ndarray, key_score: np.ndarray, p: _Prep) -> tuple[list[int], list[int]]:
    """Arm B: the B_SLOTS best key-only hits (outside the archive tier, not already in the plain set) replace the
    lowest-scoring non-archive plain slots; the top-1 plain hit is never replaced. Returns (B ids, added)."""
    free = np.ones(p.n, dtype=bool)
    free[plain] = False
    elig = np.nonzero(((p.tier == 1) | (p.tier == 2)) & free)[0]
    add_pos = _top_stable(key_score[elig], B_SLOTS) if len(elig) else np.zeros(0, dtype=np.int64)
    added = [int(elig[j]) for j in add_pos if np.isfinite(key_score[elig[j]])]
    cand_out = [i for k, i in enumerate(plain) if k > 0 and int(p.tier[i]) != 0]
    cand_out.sort(key=lambda i: plain_score[i])           # lowest plain score first
    drop = cand_out[:len(added)]
    added = added[:len(drop)]
    b = list(plain)
    for d, a in zip(drop, added):
        b[b.index(d)] = a
    return b, added


def compute_arms(view: dict, qv: np.ndarray, kv: np.ndarray | None, prev_kv: np.ndarray | None,
                 time_bias: str, bias_vec=None, bias_weight: float = 0.0, now: float | None = None) -> dict:
    """Pure function of a pool view and vectors (no I/O, no locks beyond the prep cache): the id sets for plain,
    A05, A025, B, N. `qv` is the UNWARPED normalised query vector (as store._embed returns it); `kv` the normalised
    key vector or None (no usable keys). J-3309's offline replay imports this so live and replay cannot drift.
    Returns {"pool": _Prep, "idx": {arm: [pool indices]}, "scores": {arm: score vector}, "added_b": [...],
    "plain_score": vector, "no_emb_n": int, "ms": {...}}."""
    now = time.time() if now is None else now
    t0 = time.perf_counter()
    p = _prep_for(view)
    t1 = time.perf_counter()
    mat = view["mat"]
    rec, sw = _weights(p, time_bias, now)
    vecs: dict[str, np.ndarray] = {"plain": _warp(qv, bias_vec, bias_weight)}
    if kv is not None:
        for a in ALPHAS:
            vecs[f"A{int(round(a * 100)):02d}"] = _warp(_blend(qv, kv, a), bias_vec, bias_weight)
        vecs["Bkey"] = _warp(kv, bias_vec, bias_weight)
    if prev_kv is not None and kv is not None:
        vecs["N"] = _warp(_blend(qv, prev_kv, HEAD_ALPHA), bias_vec, bias_weight)
    scores = {name: _scores(mat, p, v, rec, sw) for name, v in vecs.items()}
    t2 = time.perf_counter()
    idx = {name: _select(sc, p) for name, sc in scores.items() if name != "Bkey"}
    added_b: list[int] = []
    if "Bkey" in scores:
        idx["B"], added_b = _arm_b(idx["plain"], scores["plain"], scores["Bkey"], p)
    t3 = time.perf_counter()
    return {"pool": p, "idx": idx, "scores": scores, "added_b": added_b, "plain_score": scores["plain"],
            "no_emb_n": int(np.count_nonzero(p.slots < 0)),
            "ms": {"prep": (t1 - t0) * 1000.0, "matvec": (t2 - t1) * 1000.0, "select": (t3 - t2) * 1000.0}}


# ---------------------------------------------------------------- the logged call
def _entries(res: dict, name: str, score_name: str | None = None, key_added: list[int] | None = None) -> list:
    p: _Prep = res["pool"]
    sc = res["scores"][score_name or name]
    ps = res["plain_score"]
    rows = []
    for i in res["idx"][name]:
        s = float(sc[i] if not (key_added and i in key_added) else res["scores"]["Bkey"][i])
        if not np.isfinite(s):
            s = 0.0
        rows.append([p.fid(i), round(s, 4), int(np.count_nonzero(ps > ps[i])) + 1, p.origin(i)])
    return rows


def _prev_kv_get():
    with _PREV_LOCK:
        return _PREV_KV


def _prev_kv_set(v) -> None:
    global _PREV_KV
    with _PREV_LOCK:
        _PREV_KV = v


def _clip(lst: list) -> list:
    return [str(k)[:MAX_KEY_CHARS] for k in lst[:MAX_KEYS_LOGGED]]


def build_row(query_text: str, keys: Any, time_bias: str, bias_vec, bias_weight: float, live_ids: list,
              cycle_id: str, input_type: str | None) -> dict | None:
    """Compute one log row (design section 3.3). Returns None when the shadow is off. Does not write."""
    if not KEY_SHADOW_ON:
        return None
    from core.memory import store
    t_start = time.perf_counter()
    ep, sem = _key_lists(keys)
    used, junk_n = clean_keys(ep, sem)
    row: dict = {"ts": round(time.time(), 3), "cycle_id": cycle_id, "input_type": input_type, "time_bias": time_bias,
                 "episodic_keys": _clip(ep), "semantic_keys": _clip(sem), "keys_used_n": len(used),
                 "junk_keys_n": junk_n}
    try:
        from core import farewell_echo as _fe
        row["farewell"] = bool(_fe.is_farewell(query_text))
    except Exception:
        row["farewell"] = None
    view = store.pool_embedding_view()
    if view is None:
        row["skipped"] = "pool_unavailable"
        return row
    t_e0 = time.perf_counter()
    q_str = query_text if (query_text or "").strip() else " ".join(used)
    qv = store._embed(q_str)               # a single embed, as retrieve() does, so the plain arm reproduces it exactly
    key_str = ", ".join(used)
    kv = store._embed(key_str) if used else None
    row["embed_ms"] = round((time.perf_counter() - t_e0) * 1000.0, 2)
    if qv is None:
        row["skipped"] = "no_query_vector"
        return row
    prev_kv = _prev_kv_get()
    res = compute_arms(view, qv, kv, prev_kv, time_bias, bias_vec, bias_weight)
    _prev_kv_set(kv)                       # arm N uses THIS call's keys next time
    p: _Prep = res["pool"]
    plain = res["idx"]["plain"]
    plain_ids = [p.fid(i) for i in plain]
    live = list(live_ids or [])
    live_set = set(live)
    row["cos_query_keys"] = round(float(np.dot(qv, kv)), 4) if kv is not None else None
    row["live_ids"] = live
    row["pool_n"] = p.n
    row["no_emb_n"] = res["no_emb_n"]
    row["plain9"] = _entries(res, "plain")
    row["plain_matches_live"] = (set(plain_ids) <= live_set) if live else None
    row["plain_missing_from_live"] = len([i for i in plain_ids if i not in live_set]) if live else None
    row["live_extra_n"] = len(live_set - set(plain_ids)) if live else None
    if kv is None:
        row["no_usable_keys"] = True
    else:
        plain_top = plain_ids[0] if plain_ids else None
        for name, label in (("A50", "A05_9"), ("A25", "A025_9")):
            if name in res["idx"]:
                ent = _entries(res, name)
                row[label] = ent
                row[label[:-2] + "_overlap"] = len({e[0] for e in ent} & set(plain_ids))
                row[label[:-2] + "_top1_kept"] = bool(plain_top in {e[0] for e in ent})
        if "B" in res["idx"]:
            row["B_9"] = _entries(res, "B", score_name="plain", key_added=res["added_b"])
            row["B_added"] = [p.fid(i) for i in res["added_b"]]
        if "N" in res["idx"]:
            row["N_9"] = _entries(res, "N")
            row["N_same_keys"] = bool(prev_kv is not None and np.allclose(prev_kv, kv, atol=1e-6))
    row["prep_ms"] = round(res["ms"]["prep"], 2)
    row["matvec_ms"] = round(res["ms"]["matvec"], 2)
    row["select_ms"] = round(res["ms"]["select"], 2)
    row["total_ms"] = round((time.perf_counter() - t_start) * 1000.0, 2)
    return row


def _append(row: dict) -> None:
    path = profile.guard_path(_LOG)       # fenced (D-0179): a non-live process is refused (swallowed by the caller)
    with _APPEND_LOCK, open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def shadow_compare_keys(query_text: str, keys: Any, time_bias: str, bias_vec, bias_weight: float, live_ids: list,
                        cycle_id: str, input_type: str | None) -> None:
    """OBSERVE-ONLY (design section 3.2). Called from Orchestrator._retrieve_memory beside shadow_compare_lens1..3,
    in asyncio.to_thread. Logs one row to data/key_shadow.jsonl; returns nothing; never raises."""
    try:
        if not KEY_SHADOW_ON:
            return
        row = build_row(query_text, keys, time_bias, bias_vec, bias_weight, live_ids, cycle_id, input_type)
        if row is not None:
            _append(row)
    except Exception as exc:
        logger.debug("[key_shadow] skipped (non-fatal): %s", exc)
