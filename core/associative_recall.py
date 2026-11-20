"""
Nascence — Associative Recall (the trail-following recall engine, 2026-06-23)
============================================================================
A rehash of memory retrieval, from flat topical top-N + rigid tiers to SPREADING ACTIVATION — recall that
follows a TRAIL. Seed from the most relevant AND IMPORTANT memories, then spread along associative trails
(embedding-neighbours, plus the explicit links where they exist), activation decaying each hop, so one memory
cues the next. Importance is in the score (what MATTERED surfaces). No rigid tiers or hard counts: a dynamic
budget up to a soft ceiling. The walled-off cold/chaptered detail (~93% of his store) is reachable BY THE
TRAIL, but only when STRONGLY cued — so the vault opens proportional to relevance, never floods.

LIVE (2026-06-23): the trail AUGMENTS the live topical retrieve in the orchestrator (additive + deduped —
the topical set is still present, so no regression); every downstream reader gets memories the context
actually cues. (Was shadow-only earlier that day; the shadow log is retained for diagnostics but the
trail now feeds his cognition — docstring corrected 2026-07-02 after the systems check caught the drift.)

M2 RELATIONAL LIVE (2026-09-27, D-0287, J-1415, docs/plans/memory_multiway_linking.md Sec 5/6):
`recall_memory_fragments()` below — the one function that feeds the augmentation above — now ALSO
layers in `recall_trail_edge_aware(mode="relational")`, kill-switched via `M2_EDGE_AWARE_RELATIONAL_LIVE`
just above that function. Shadow evidence (F-1966) found "relational" the one MODE_EDGE_WEIGHTS profile
(core/memory_edges.py) a real usage proxy clears; "task"/"reflective" are UNCHANGED — still read only by
`shadow_compare()` for logging, never consumed by a live path.
"""
from __future__ import annotations

import json
import logging
import sqlite3
import threading
import time
from pathlib import Path

import numpy as np

logger = logging.getLogger("nascence.assoc_recall")
_LOG = Path(__file__).parent.parent / "data" / "associative_recall_shadow.jsonl"

# ── Tuning (shadow — cheap to retune before it goes live) ─────────────────────────────────────────
CEILING        = 15      # soft max memories a trail may surface into one cycle (the only real limit)
N_SEEDS        = 5       # entry points: best relevance × importance × recency
N_HOPS         = 2       # how far the trail spreads from the seeds
HOP_DECAY      = 0.6     # activation multiplier per hop (the trail fades as it lengthens)
NEIGHBORS_PER  = 8       # associative neighbours examined from each activated node
MAX_PER_ORIGIN = 6       # soft diversity guard: no single kind of memory may dominate the trail (anti-echo-chamber)
ACT_THRESHOLD  = 0.13    # min activation to be recalled (active memories) — tuned to the post-decay scale
COLD_THRESHOLD = 0.22    # cold/chaptered need MORE activation — reachable only on a STRONG hop, not a weak one
# J-2098 (D-0410 B / F-1981, restart-gated): kind=self gists are committed at a FIXED importance 0.85 (memory_levels
# ._commit_gist), so importance-seeded trails over-seed from them. Damp their SEED score only (no stored row changes;
# similarity still dominates, so a genuine self-knowledge query still seeds them). 1.0 = off.
SELF_GIST_SEED_WEIGHT = 0.75
_SEED_SHARE_LOG = Path(__file__).parent.parent / "data" / "assoc_seed_share_shadow.jsonl"
_REFRESH_S     = 900     # rebuild the cached embedding matrix at most this often

_cache: dict = {"ts": 0.0, "M": None, "ids": None, "imp": None, "age": None, "walled": None, "origin": None,
                "self_gist": None}


_EMB_CACHE = Path(__file__).parent.parent / "data" / "embedding_matrix.npz"


def _load_persisted():
    """The persisted (normalised) embedding matrix + parallel ids — the index that avoids re-decoding BLOBs."""
    try:
        if _EMB_CACHE.exists():
            z = np.load(_EMB_CACHE, allow_pickle=False)
            return z["M"].astype(np.float32), [str(x) for x in z["ids"]]
    except Exception as exc:
        logger.debug("[assoc] persisted matrix load failed (will rebuild): %s", exc)
    return None, []


def _save_persisted(M, ids) -> None:
    try:
        import os
        from core import profile
        cache_path = profile.guard_path(_EMB_CACHE)   # J-2180/F-2883: fenced (D-0179) -- a non-live, non-isolate()d process is refused here, swallowed by the fail-open net
        tmp = cache_path.with_suffix(".tmp.npz")
        np.savez(tmp, M=M.astype(np.float32), ids=np.asarray(ids, dtype="U64"))
        os.replace(tmp, cache_path)
    except Exception as exc:
        logger.debug("[assoc] persist failed: %s", exc)


def _refresh(now: float) -> None:
    """Refresh the cached matrix. The EXPENSIVE part — decoding embedding BLOBs — is PERSISTED to disk and done
    only INCREMENTALLY for new fragments (an embedding never changes once written). The cheap, MUTABLE metadata
    (importance, cold/chapter, timestamp) is re-queried fresh every time, so cold/chapter changes stay current."""
    from core.memory.store import _connect, _blob_to_vec
    cached_M, cached_ids = _load_persisted()
    cached_set = set(cached_ids)
    with _connect() as conn:
        # J-3191 (D-0578): the spirit-invisible tier (temp='hidden', e.g. the 61 dict-repr understanding notes) is
        # left out of the matrix, as store.retrieve and memory_levels.deep_recall already leave it out. A hidden id
        # missing from `meta` is dropped by the `keep` filter below, so the trail, recall_block and
        # recall_memory_fragments never surface it; unmarking brings it back as a "new" id on the next refresh.
        # Only when the column exists (an old/profile DB lacks it -> the query is unchanged).
        _has_temp = any(r[1] == "temp" for r in conn.execute("PRAGMA table_info(memory_fragments)"))
        _q = ("SELECT fragment_id, importance, timestamp, cold, chapter_id, origin{k} "
              "FROM memory_fragments WHERE embedding IS NOT NULL AND origin != 'system_note' "   # J-1955: D-0368 E
              + ("AND temp != 'hidden' " if _has_temp else "") +
              "AND layer != 'dormant'")   # J-2018 (D-0400 B): cold rows ARE reachable here on a strong hop; night thoughts must not be
        try:   # J-2098: kind column may be absent on an old/profile DB -> fall back (no self-gist damping there)
            meta = {r["fragment_id"]: r for r in conn.execute(_q.format(k=", kind")).fetchall()}
        except sqlite3.OperationalError:
            meta = {r["fragment_id"]: dict(r, kind=None) for r in conn.execute(_q.format(k="")).fetchall()}   # J-2018 (D-0400 B): cold rows ARE reachable here on a strong hop; night thoughts must not be
        new_ids = [fid for fid in meta if fid not in cached_set]
        new_vecs = []
        for j in range(0, len(new_ids), 400):                       # decode ONLY new embeddings, chunked
            chunk = new_ids[j:j + 400]
            ph = ",".join("?" * len(chunk))
            for r in conn.execute(f"SELECT fragment_id, embedding FROM memory_fragments "
                                  f"WHERE fragment_id IN ({ph})", chunk).fetchall():
                v = _blob_to_vec(r["embedding"])
                if v is not None:
                    v = np.asarray(v, dtype=np.float32)
                    new_vecs.append((r["fragment_id"], v / (float(np.linalg.norm(v)) or 1.0)))
    ids = list(cached_ids) + [fid for fid, _ in new_vecs]
    parts = ([cached_M] if cached_M is not None else []) + (
        [np.vstack([v for _, v in new_vecs])] if new_vecs else [])
    if not parts:
        return
    M = parts[0] if len(parts) == 1 else np.vstack(parts)
    keep = [k for k, fid in enumerate(ids) if fid in meta]           # drop deleted fragments; align metadata
    if len(keep) != len(ids):
        ids = [ids[k] for k in keep]
        M = M[keep]
    _save_persisted(M, ids)
    _cache.update(
        ts=now, M=M, ids=ids,
        imp=np.asarray([float(meta[i]["importance"] or 0.5) for i in ids], dtype=np.float32),
        age=np.asarray([(now - float(meta[i]["timestamp"] or now)) / 86400.0 for i in ids], dtype=np.float32),
        walled=np.asarray([bool(meta[i]["cold"]) or (meta[i]["chapter_id"] is not None) for i in ids], dtype=bool),
        origin=[meta[i]["origin"] or "lived" for i in ids],
        self_gist=np.asarray([(meta[i]["origin"] == "gist" and meta[i]["kind"] == "self") for i in ids], dtype=bool))


# J-1918 / F-2547 (2026-10-07, restart-gated): memory_service.ask() (curiosity's idle recall) now runs in a worker
# thread, and orchestrator.py already calls recall_memory_fragments from one, so _matrix() can be entered from two
# threads at once. Unlocked, two overlapping refreshes would both write the ONE shared tmp name in _save_persisted
# (embedding_matrix.tmp.npz) and a reader could see _cache half applied (M from one build, imp/age/walled from
# another -> a shape mismatch or silently wrong scores). The lock covers the stale-check + refresh + snapshot; the
# snapshot (a shallow copy of the dict -- the arrays inside are replaced, never mutated, by _refresh) is what callers
# hold, so every later read of c["M"], c["imp"], ... is from ONE build. Re-entrant; single-thread results unchanged.
_MATRIX_LOCK = threading.RLock()


def _matrix() -> dict:
    with _MATRIX_LOCK:
        now = time.time()
        if _cache["M"] is None or now - _cache["ts"] > _REFRESH_S:
            try:
                _refresh(now)
            except Exception as exc:
                logger.debug("[assoc] matrix refresh failed: %s", exc)
        return dict(_cache)


def recall_trail(query_vec, recency: bool = True) -> list[dict]:
    """Spreading activation from the query: seed (relevance × importance × recency) → follow trails (embedding
    neighbours, decaying) → collect the most-activated, up to CEILING. Returns [{fragment_id, activation,
    origin, walled}], strongest first.

    J-2659 (F-3403, D-0528 open, restart-gated): `recency=False` sets the 7-day recency multiplier to exactly 1.0
    (and skips the seed-share shadow row, so the comparison call never double-counts that instrument). The
    default True is today's behaviour, byte-for-byte; nothing live passes False -- only memory_service's
    shadow comparison (data/ask_recency_shadow.jsonl) and opt-in callers do."""
    c = _matrix()
    M = c["M"]
    if M is None:
        return []
    qv = np.asarray(query_vec, dtype=np.float32)
    n = np.linalg.norm(qv)
    if n == 0:
        return []
    qv = qv / n
    sims = M @ qv                                              # cosine to every memory
    imp, age, walled = c["imp"], c["age"], c["walled"]
    recency_w = (1.0 + 0.2 * np.clip(1.0 - age / 7.0, 0.0, 1.0)) if recency else 1.0
    # seeds come from the ACTIVE set (not walled), scored by relevance × importance × recency
    seed_score = sims * (0.4 + 0.6 * imp) * recency_w
    seed_score = np.where(walled, -1.0, seed_score)
    sg = c.get("self_gist")
    undamped = None
    if sg is not None and SELF_GIST_SEED_WEIGHT != 1.0 and len(sg) == len(seed_score):
        undamped = [int(i) for i in np.argsort(-seed_score)[:N_SEEDS] if seed_score[i] > 0]
        seed_score = np.where(sg & (seed_score > 0), seed_score * SELF_GIST_SEED_WEIGHT, seed_score)
    seeds = [int(i) for i in np.argsort(-seed_score)[:N_SEEDS] if seed_score[i] > 0]
    if recency and sg is not None and len(sg) == len(seed_score):
        try:   # shadow counter: self-gist share of seeds (actual vs. what the undamped formula would have picked)
            from core import profile
            with open(profile.guard_path(_SEED_SHARE_LOG), "a", encoding="utf-8") as f:   # J-2180/F-2883: fenced (D-0179) -- a non-live, non-isolate()d process is refused here, swallowed by the fail-open net
                f.write(json.dumps({"ts": time.time(), "n_seeds": len(seeds),
                                    "self_seeds": int(sum(bool(sg[i]) for i in seeds)),
                                    "undamped_self_seeds": (int(sum(bool(sg[i]) for i in undamped))
                                                            if undamped is not None else None),
                                    "weight": SELF_GIST_SEED_WEIGHT}) + "\n")
        except Exception:
            pass
    activation: dict[int, float] = {i: float(seed_score[i]) for i in seeds}
    frontier = list(seeds)
    for _hop in range(N_HOPS):
        nxt: list[int] = []
        for node in frontier:
            nsims = M @ M[node]                                # this memory's associative neighbours
            for nb in np.argsort(-nsims)[1:NEIGHBORS_PER + 1]:
                nb = int(nb)
                act = activation[node] * float(nsims[nb]) * HOP_DECAY
                thr = COLD_THRESHOLD if walled[nb] else ACT_THRESHOLD
                if act >= thr and act > activation.get(nb, 0.0):
                    activation[nb] = act
                    nxt.append(nb)
        frontier = nxt
        if not frontier:
            break
    # Soft DIVERSITY guard (Jungian opposites): collect strongest-first, but cap any single origin so the
    # trail can never collapse into an echo chamber of one kind of memory (the self-loop failure mode — a
    # 'who am I' query was returning 15 subconscious-syntheses and nothing else).
    out: list[dict] = []
    per_origin: dict[str, int] = {}
    for i, a in sorted(activation.items(), key=lambda kv: -kv[1]):
        o = c["origin"][i]
        if per_origin.get(o, 0) >= MAX_PER_ORIGIN:
            continue
        per_origin[o] = per_origin.get(o, 0) + 1
        out.append({"fragment_id": c["ids"][i], "activation": round(a, 3), "origin": o,
                    "walled": bool(walled[i])})
        if len(out) >= CEILING:
            break
    return out


def recall_trail_edge_aware(query_vec, mode: str = "task", base: list[dict] | None = None) -> list[dict]:
    """SHADOW ONLY (M2, 2026-08-25, J-0263, docs/plans/memory_multiway_linking.md §5): the SAME greedy
    trail (`recall_trail`, called here unmodified — pass `base=` to reuse an already-computed one and
    skip recomputing it) PLUS typed-edge neighbours of the resulting activated set, pulled from
    `core.memory_edges.edge_aware_neighbors()` and weighted per `mode`.

    Design choice, spelled out (build notes, not silent): this adds typed-edge reach as ONE extra hop
    on TOP of the completed greedy walk, not interleaved into each of the N_HOPS embedding hops inside
    `recall_trail` itself — simpler to reason about and log, keeps `recall_trail` truly untouched (the
    job's own requirement), at the cost of not letting an edge-reached node spawn its own further
    embedding hops this cycle. The formula mirrors the greedy hop's own
    `activation[node] * sim * HOP_DECAY` shape, with the edge weight standing in for cosine similarity
    (no embedding exists between two different edge KINDS) and the trail's PEAK activation standing in
    for "the specific node that reached this candidate" (a coarse, deliberately conservative-leaning
    stand-in — exact per-edge attribution would need `edge_aware_neighbors` to track which seed each
    candidate came from, which it does not do today; fine for shadow measurement, worth revisiting if
    this graduates). Same HOP_DECAY / ACT_THRESHOLD / COLD_THRESHOLD / MAX_PER_ORIGIN / CEILING as the
    greedy walk — no new tuning surface. Called from `shadow_compare` under all three named modes
    (log-only there — see that function's own docstring). ALSO called LIVE, mode="relational" ONLY,
    from `recall_memory_fragments()` below since 2026-09-27 (D-0287, J-1415: shadow evidence, F-1966,
    found relational's edge-reached fragments the one weighting profile a real usage proxy clears — 39%
    score >=0.4 cosine against the next thought, vs task's 0.25 mean / reflective's 0.28 mean — so only
    that mode graduated; task/reflective stay shadow-only, unchanged). Kill switch for the live call:
    `M2_EDGE_AWARE_RELATIONAL_LIVE`, defined just above `recall_memory_fragments`.
    Fail-open: any error returns the unmodified base trail — the live call site below wraps this call
    in its OWN try/except too, a second, independent fail-open layer for the live path specifically."""
    b = base if base is not None else recall_trail(query_vec)
    if not b:
        return b
    try:
        from core import memory_edges as _me
    except Exception:
        return b
    c = _matrix()
    ids_index = {fid: i for i, fid in enumerate(c.get("ids") or [])}
    walled_arr = c.get("walled")
    activation = {t["fragment_id"]: t["activation"] for t in b}
    origin_of = {t["fragment_id"]: t["origin"] for t in b}
    seed_ids = list(activation.keys())
    peak = max(activation.values()) if activation else 0.0
    try:
        candidates = _me.edge_aware_neighbors(seed_ids, mode=mode, limit=NEIGHBORS_PER * max(len(seed_ids), 1))
    except Exception as exc:
        logger.debug("[assoc] edge_aware_neighbors call failed (non-fatal): %s", exc)
        candidates = []
    for cand in candidates:
        fid = cand["fragment_id"]
        act = peak * float(cand["weight"]) * HOP_DECAY
        idx = ids_index.get(fid)
        is_cold = bool(walled_arr[idx]) if (idx is not None and walled_arr is not None) else False
        thr = COLD_THRESHOLD if is_cold else ACT_THRESHOLD
        if act < thr or act <= activation.get(fid, 0.0):
            continue
        activation[fid] = act
        origin_of.setdefault(fid, c["origin"][idx] if idx is not None else "lived")
    # Re-apply the SAME diversity guard + ceiling as recall_trail's own post-processing (unchanged
    # constants; edge candidates are just another source of activation, not a different engine).
    out: list[dict] = []
    per_origin: dict[str, int] = {}
    for fid, a in sorted(activation.items(), key=lambda kv: -kv[1]):
        o = origin_of.get(fid, "lived")
        if per_origin.get(o, 0) >= MAX_PER_ORIGIN:
            continue
        per_origin[o] = per_origin.get(o, 0) + 1
        idx = ids_index.get(fid)
        out.append({"fragment_id": fid, "activation": round(a, 3), "origin": o,
                    "walled": bool(walled_arr[idx]) if (idx is not None and walled_arr is not None) else False})
        if len(out) >= CEILING:
            break
    return out


_M2_MODES = ("task", "reflective", "relational")   # docs/plans/memory_multiway_linking.md §5's trio

# PRONG 2 INSTRUMENTATION (2026-09-02, J-0446, F-0605): the kill criterion's second half
# (memory_multiway_linking.md Sec 5 — "are edge-reached memories ever *used* by the thought that
# follows") was unmeasurable: shadow_compare logs new_ids but nothing links them to what got thought
# about next. `_pending_m2_usage` hands the latest still-unconsumed shadow event's new_ids off to
# whichever thought completes next (via `note_next_thought_for_m2_usage`, below) — approximate under
# concurrency (a second shadow_compare before a thought consumes the first overwrites it, silently
# dropping that one event's usage read), same acceptance as M1's own `_last_block_ids` precedent just
# above. Module-level, not per-instance, because shadow_compare and the thought that reads it run in
# different objects (orchestrator's retrieval vs. the monologue node).
_pending_m2_usage: dict | None = None


def shadow_compare(query_text: str, current_fragment_ids: list[str]) -> None:
    """OBSERVE-ONLY: run the trail for this cycle's query and log it against what the live retrieve() returned.
    The key signals: how many memories the trail surfaces that the current system misses, and how much of the
    walled-off vault it reaches when genuinely cued. Best-effort; never raises.

    M2 (2026-08-25, J-0263): also runs `recall_trail_edge_aware()` under EACH of the plan's three named
    modes against the SAME greedy trail and logs each under `m2_edge_aware` — no LLM call, so trying
    all three is cheap. The real per-cycle cognitive mode is NOT available at the point this fires:
    this function is now called from `orchestrator._retrieve_memory` (line ~686 of the cycle), while
    `AttentionVector.cognitive_mode` is computed in a later phase (orchestrator.py:2041/2063) and reset
    each cycle — verified 2026-08-25 by reading both call sites, not assumed. Logging all three modes
    is the honest workaround: it lets the eventual founder-read find the real winner from data instead
    of this code guessing one mode now. `shadow_compare` itself was written 2026-06-23 but had ZERO
    live callers anywhere in the codebase until this job wired it in (verified via a whole-tree grep,
    2026-08-25) — the file's own header docstring implied it was still firing; it was not. See the
    orchestrator.py hook and the plan doc's Current State note for where it is wired now."""
    try:
        from core.memory.store import _embed
        qv = _embed(query_text)
        if qv is None:
            return
        trail = recall_trail(qv)
        if not trail:
            return
        cur = set(current_fragment_ids or [])
        new = [t for t in trail if t["fragment_id"] not in cur]
        walled = [t for t in trail if t["walled"]]
        greedy_ids = {t["fragment_id"] for t in trail}
        by_mode = {}
        for m in _M2_MODES:
            et = recall_trail_edge_aware(qv, mode=m, base=trail)
            eids = {t["fragment_id"] for t in et}
            enew = eids - greedy_ids
            ewnew = [t for t in et if t["fragment_id"] in enew and t["walled"]]
            by_mode[m] = {"trail_n": len(et), "new_vs_greedy": len(enew), "walled_new": len(ewnew),
                          # J-0315 (F-0400): the kill criterion's usage clause ("are edge-reached
                          # memories ever USED by the thought that follows") is unanswerable from
                          # counts alone — capped, the log stays tiny (a dozen ids costs nothing at
                          # ~40 rows/3 days).
                          "new_ids": sorted(enew)[:12]}
        rec = {
            "ts": time.time(), "query": (query_text or "")[:90],
            "trail_n": len(trail), "current_n": len(cur),
            "new_vs_current": len(new), "walled_surfaced": len(walled),
            "overlap": len(trail) - len(new),
            "top": [(t["origin"], t["activation"], "W" if t["walled"] else "") for t in trail[:6]],
            "m2_edge_aware": by_mode,
        }
        # PRONG 2 STASH (J-0446/F-0605): hand this event's per-mode new_ids off for a usage read against
        # whatever thought comes next — `note_next_thought_for_m2_usage` consumes this and appends a
        # SEPARATE `m2_usage` row (this row's own shape above is completely untouched, written exactly
        # as before). Keyed on this row's own `ts` so a future reader can join the two.
        global _pending_m2_usage
        _pending_m2_usage = {"shadow_id": rec["ts"], "modes": {m: list(by_mode[m]["new_ids"]) for m in _M2_MODES}}
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.debug("[assoc] shadow skipped: %s", exc)


def note_next_thought_for_m2_usage(thought_vec) -> None:
    """PRONG 2 INSTRUMENTATION (2026-09-02, J-0446, F-0605): the kill criterion's usage clause needs to know
    whether an edge-reached fragment (an M2 `new_ids` entry, logged by `shadow_compare` above) was ever
    *used* by the thought that follows it — unmeasurable before this build (F-0605: 148/148 rows read,
    zero had any usage field). The cheap, honest proxy this uses (per the job's own briefing): cosine
    between each pending fragment's ALREADY-COMPUTED embedding (read straight off the cached matrix
    `_matrix()` already builds for the trail walk — no new embedding call) and the NEXT thought's
    ALREADY-COMPUTED embedding (`vec`, passed in by the caller — no new LLM/embed call either). Records
    the real score per fragment, deliberately NOT binarized into a used/unused bit (the job's own
    instruction) — a future gate-read can pick its own threshold, or look at the distribution directly.

    Consumes (clears) `_pending_m2_usage` unconditionally on entry so one shadow event is never credited
    to two different thoughts. Writes a NEW row, tagged `kind: "m2_usage"` and correlated by `parent_ts`
    to the `m2_edge_aware` row it scores — `shadow_compare`'s own row shape is never touched, so this is
    purely additive to the log, exactly the existing convention (Lens 1's own separate-file precedent
    just below takes the same care for a different reason: avoiding a write race on `_LOG`; this reuses
    the same file because these two writers are already both appending single lines to it independently,
    same as `shadow_compare` and any other logger sharing a data/*.jsonl file elsewhere in this codebase).

    Does NOT touch the live recall path — reads only the cached embedding matrix and writes only a log
    line. Best-effort, fail-open, never raises. Call site: nodes/inner_monologue_node.py, right where the
    M1 co-recall plumbing (`_m1_recall_ids` / `log_co_recall`) already reuses this exact per-thought
    completion point — same pattern, a second shadow instrument riding the same hook."""
    global _pending_m2_usage
    pending = _pending_m2_usage
    if pending is None or thought_vec is None:
        return
    _pending_m2_usage = None   # consume now, regardless of what happens below — never double-credit
    try:
        c = _matrix()
        M = c.get("M")
        ids = c.get("ids") or []
        if M is None:
            return
        ids_index = {fid: i for i, fid in enumerate(ids)}
        tv = np.asarray(thought_vec, dtype=np.float32)
        tn = float(np.linalg.norm(tv))
        if tn == 0.0:
            return
        tv = tv / tn
        usage_by_mode: dict[str, list[dict]] = {}
        for mode, fids in (pending.get("modes") or {}).items():
            scored = []
            for fid in fids:
                idx = ids_index.get(fid)
                if idx is None:
                    continue   # fragment aged out of the cached matrix between the retrieval and now
                scored.append({"fragment_id": fid, "cos_sim": round(float(M[idx] @ tv), 4)})
            usage_by_mode[mode] = scored
        rec = {
            "ts": time.time(),
            "kind": "m2_usage",
            "parent_ts": pending.get("shadow_id"),
            "usage_by_mode": usage_by_mode,
        }
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.debug("[assoc] m2 usage capture skipped: %s", exc)


# ── Lens 1 — spectral diffusion (SHADOW ONLY, D-0070/J-0345, docs/staged/du_recall_lens_upgrades.md) ──────────
# Ported from C:\UDMS\core\math\spectral_diffusion.py's SpectralDiffusionEngine — the Lens 1 reference
# implementation whose downstream-prediction gain reproduced cleanly on independent re-run (+3.08pp vs the
# claimed +2.69pp, stable, F-0399/D-0070). Same math (K_t = exp(-t*L) via a 3rd-order Taylor/Chebyshev
# expansion of the normalized graph Laplacian), reimplemented with plain dense numpy instead of scipy.sparse
# because the graph diffused over here is a small LOCAL subgraph (seeds + their embedding neighbours, same
# breadth `recall_trail`'s own hop already explores), not UDMS's global concept co-occurrence graph — never
# the full fragment store, so no new scipy dependency and no cost blow-up on a large memory store.
# Deliberately independent of M2's own additive lens (`recall_trail_edge_aware`/`shadow_compare`, both left
# byte-for-byte untouched by this build, per J-0345's own instruction) — a SEPARATE new function/mode and a
# SEPARATE log file (`_LENS1_LOG`, not `_LOG`), so this can never race or corrupt M2's in-flight shadow trail
# (J-0280). Never called from any live recall path.
_LENS1_LOG = Path(__file__).parent.parent / "data" / "associative_recall_lens1_shadow.jsonl"

# J-2208 (F-2907, restart-gated, shadow-only): energy -> activation scale fix shared by Lens 1/2/3.
# The truncated-Taylor heat-kernel energies of non-seed nodes are tiny (~0.006-0.019) AND nearly flat (min/max
# ~0.8 on real trails: the cosine adjacency is a dense, almost complete graph), so `peak * energy * HOP_DECAY`
# landed at 0.003-0.008, 20-40x under ACT_THRESHOLD -- every lens returned the greedy trail unchanged in
# 3010/3010 shadow rows (08-29..10-16). `_local_spectral_diffuse` now rescales the non-seed energies onto the
# trail's activation axis once, so all three lenses inherit it:
#   "minmax" (default): (e - min) / (max - min) over the local subgraph's non-seed nodes -- the strongest
#            diffused candidate lands at peak*HOP_DECAY (where a perfect first greedy hop lands), the uniform
#            background floor the dense graph spreads everywhere lands at 0, so only candidates the seeds
#            actually push energy toward clear ACT_THRESHOLD. A pure divide-by-max ("max") was measured to
#            lift nearly the WHOLE local subgraph over threshold (the floor is ~80% of the max) -- kept
#            selectable for comparison only.
#   "none":  the original raw energies (the pre-J-2208 behaviour, i.e. the lenses are a no-op again).
# Lens shadow rows now carry `energy_norm` so D-0170's >=200-rows-each read counts post-fix rows only.
LENS_ENERGY_NORM = "minmax"


def _local_spectral_diffuse(local_M, seed_local_idxs: list[int], t: float, top_k: int) -> list[tuple[int, float]]:
    """Heat-kernel diffusion K_t = exp(-t*L) over a small dense local subgraph (rows of `local_M` are already
    L2-normalised, so `local_M @ local_M.T` is a cosine-similarity adjacency). Mirrors
    SpectralDiffusionEngine.diffuse()'s truncated Taylor expansion exactly: xt = x0 - t*Lx0 + (t^2/2)L^2x0 -
    (t^3/6)L^3x0, clipped non-negative. Returns (local_index, energy) pairs, strongest first, seeds excluded."""
    n = local_M.shape[0]
    if n == 0:
        return []
    adj = local_M @ local_M.T
    np.fill_diagonal(adj, 0.0)
    adj = np.clip(adj, 0.0, None)          # diffusion is undefined over anti-correlated (negative-cosine) edges
    deg = adj.sum(axis=1)
    with np.errstate(divide="ignore"):
        d_inv_sqrt = np.where(deg > 0, 1.0 / np.sqrt(deg), 0.0)
    L = np.eye(n) - (d_inv_sqrt[:, None] * adj * d_inv_sqrt[None, :])   # normalized graph Laplacian
    x0 = np.zeros(n)
    if seed_local_idxs:
        x0[seed_local_idxs] = 1.0 / len(seed_local_idxs)
    v0 = x0
    v1 = L @ v0
    v2 = L @ v1
    v3 = L @ v2
    xt = v0 - t * v1 + (t ** 2 / 2.0) * v2 - (t ** 3 / 6.0) * v3
    xt = np.maximum(xt, 0.0)
    seed_set = set(seed_local_idxs)
    order = np.argsort(-xt)
    out = [(int(i), float(xt[i])) for i in order if xt[i] > 1e-6 and int(i) not in seed_set]
    if out and LENS_ENERGY_NORM in ("max", "minmax"):     # J-2208: rescale onto the activation axis (see above)
        hi = out[0][1]
        lo = 0.0
        if LENS_ENERGY_NORM == "minmax":
            non_seed = [float(xt[i]) for i in range(n) if i not in seed_set]
            lo = min(non_seed) if non_seed else 0.0
        span = hi - lo
        if span <= 1e-12:
            return []                                     # a flat field: diffusion singles nothing out
        out = [(i, (e - lo) / span) for i, e in out if e - lo > 0.0]
    return out[:top_k]


def recall_trail_spectral_diffusion(query_vec, t: float = 1.0, base: list[dict] | None = None) -> list[dict]:
    """SHADOW ONLY: Lens 1 (spectral diffusion) composed on TOP of the completed greedy trail (`recall_trail`,
    called here unmodified — pass `base=` to reuse an already-computed one), same additive shape as
    `recall_trail_edge_aware` (build notes there explain the pattern this mirrors). Builds a LOCAL embedding
    subgraph from the trail's seeds plus each seed's NEIGHBORS_PER nearest neighbours, runs heat-kernel
    diffusion over it (`_local_spectral_diffuse`), and merges diffusion-reached candidates into the trail's
    activation map — same HOP_DECAY / ACT_THRESHOLD / COLD_THRESHOLD / MAX_PER_ORIGIN / CEILING as the greedy
    walk, no new tuning surface beyond `t` (the diffusion time-scale). Diffusion energy is unitless, so it is
    scaled by the trail's PEAK activation (same coarse stand-in `recall_trail_edge_aware` uses for edge
    weights) to compose on the same activation axis. Fail-open: any error returns the unmodified base trail.
    Never called from a live recall path — only from `shadow_compare_lens1`."""
    b = base if base is not None else recall_trail(query_vec)
    if not b:
        return b
    c = _matrix()
    M = c["M"]
    if M is None:
        return b
    ids = c.get("ids") or []
    walled_arr = c.get("walled")
    origin_arr = c.get("origin")
    ids_index = {fid: i for i, fid in enumerate(ids)}
    seed_global = [ids_index[t2["fragment_id"]] for t2 in b if t2["fragment_id"] in ids_index]
    if not seed_global:
        return b
    activation = {t2["fragment_id"]: t2["activation"] for t2 in b}
    origin_of = {t2["fragment_id"]: t2["origin"] for t2 in b}
    try:
        local_set = set(seed_global)
        for node in seed_global:
            nsims = M @ M[node]
            for nb in np.argsort(-nsims)[1:NEIGHBORS_PER + 1]:
                local_set.add(int(nb))
        local_idxs = sorted(local_set)
        local_pos = {g: i for i, g in enumerate(local_idxs)}
        local_M = M[local_idxs]
        seed_local = [local_pos[g] for g in seed_global]
        diffused = _local_spectral_diffuse(local_M, seed_local, t=t,
                                            top_k=NEIGHBORS_PER * max(len(seed_global), 1))
        peak = max(activation.values()) if activation else 0.0
        for local_i, energy in diffused:
            g = local_idxs[local_i]
            fid = ids[g]
            act = peak * energy * HOP_DECAY
            is_cold = bool(walled_arr[g]) if walled_arr is not None else False
            thr = COLD_THRESHOLD if is_cold else ACT_THRESHOLD
            if act < thr or act <= activation.get(fid, 0.0):
                continue
            activation[fid] = act
            origin_of.setdefault(fid, origin_arr[g] if origin_arr is not None else "lived")
    except Exception as exc:
        logger.debug("[assoc] lens1 spectral diffusion failed (non-fatal): %s", exc)
        return b
    out: list[dict] = []
    per_origin: dict[str, int] = {}
    for fid, a in sorted(activation.items(), key=lambda kv: -kv[1]):
        o = origin_of.get(fid, "lived")
        if per_origin.get(o, 0) >= MAX_PER_ORIGIN:
            continue
        per_origin[o] = per_origin.get(o, 0) + 1
        g = ids_index.get(fid)
        out.append({"fragment_id": fid, "activation": round(a, 3), "origin": o,
                    "walled": bool(walled_arr[g]) if (g is not None and walled_arr is not None) else False})
        if len(out) >= CEILING:
            break
    return out


def shadow_compare_lens1(query_text: str, current_fragment_ids: list[str]) -> None:
    """OBSERVE-ONLY: logs Lens 1 (spectral diffusion) against the greedy trail and the current live retrieve,
    to its OWN log file (`_LENS1_LOG` = data/associative_recall_lens1_shadow.jsonl) — deliberately separate
    from `shadow_compare`'s `_LOG` (data/associative_recall_shadow.jsonl, owned by M2/J-0280) so this build
    can never race, interleave with, or corrupt M2's in-flight shadow trail. Mirrors `shadow_compare`'s own
    best-effort/never-raises discipline; does not call or modify `shadow_compare` itself."""
    try:
        from core.memory.store import _embed
        qv = _embed(query_text)
        if qv is None:
            return
        trail = recall_trail(qv)
        if not trail:
            return
        spectral = recall_trail_spectral_diffusion(qv, base=trail)
        cur = set(current_fragment_ids or [])
        greedy_ids = {t["fragment_id"] for t in trail}
        spectral_ids = {t["fragment_id"] for t in spectral}
        new_vs_greedy = spectral_ids - greedy_ids
        new_vs_current = spectral_ids - cur
        walled_new = [t for t in spectral if t["fragment_id"] in new_vs_greedy and t["walled"]]
        rec = {
            "ts": time.time(), "query": (query_text or "")[:90],
            "greedy_n": len(trail), "spectral_n": len(spectral), "current_n": len(cur),
            "energy_norm": LENS_ENERGY_NORM,   # J-2208: post-fix rows are the ones D-0170 reads
            "new_vs_greedy": len(new_vs_greedy), "new_vs_current": len(new_vs_current),
            "walled_new": len(walled_new),
            "new_ids": sorted(new_vs_greedy)[:12],
        }
        from core import profile
        with open(profile.guard_path(_LENS1_LOG), "a", encoding="utf-8") as f:   # J-2208: fenced (D-0179) -- a non-live process is refused, swallowed by the fail-open net
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        _stash_lens_usage(1, rec["ts"], new_vs_greedy, greedy_ids - spectral_ids)   # J-3507
    except Exception as exc:
        logger.debug("[assoc] lens1 shadow skipped: %s", exc)


# ── Lens 2 — deterministic fact anchoring (SHADOW ONLY, D-0170, docs/staged/du_recall_lens_upgrades.md) ─────
# Ported from C:\UDMS\scripts\test_p_deterministic_fact_anchoring.py's method: seed the diffusion with a
# cheap, 100%-certain fact (there, diurnal phase as a graph node) so certainty propagates to adjacent
# candidates. Measured +4.82pp on test_p's single 70/30 split, but F-0399's independent re-run found the
# effect size UNSTABLE (+27.43pp on near-identical data) -- direction-stable, magnitude not. DO NOT CITE
# either number; this shadow build exists to accrue the real distribution (D-0170's ruling, in place of a
# separate offline rolling-window harness). Same substrate adaptation Lens 1 already made: the reference
# script diffuses over a discrete concept co-occurrence graph with an explicit "diurnal_night"/"diurnal_day"
# node; this reimplements the same idea over Lens 1's local embedding subgraph -- the fact is embedded as one
# more row and included as an extra seed, then excluded from the output by `_local_spectral_diffuse`'s own
# seed-exclusion (it is a synthetic anchor, not a real memory).
_LENS2_LOG = Path(__file__).parent.parent / "data" / "associative_recall_lens2_shadow.jsonl"
_fact_embed_cache: dict = {}   # {"day"|"night": np.ndarray} -- only two possible facts exist; embed once


def _diurnal_fact_text(now: float) -> tuple[str, str]:
    """(fact_key, fact_text) for the current moment -- same night boundary as test_p (hour < 6 or hour >= 20)."""
    hour = time.localtime(now).tm_hour
    if hour < 6 or hour >= 20:
        return "night", "It is the middle of the night, dark and quiet."
    return "day", "It is daytime, light out."


def _fact_embedding(fact_key: str, fact_text: str):
    """Cached: the fact vocabulary is fixed (day/night), so embed each value once and reuse it forever."""
    v = _fact_embed_cache.get(fact_key)
    if v is not None:
        return v
    try:
        from core.memory.store import _embed
        raw = _embed(fact_text)
        if raw is None:
            return None
        v = np.asarray(raw, dtype=np.float32)
        n = float(np.linalg.norm(v))
        if n == 0:
            return None
        v = v / n
        _fact_embed_cache[fact_key] = v
        return v
    except Exception as exc:
        logger.debug("[assoc] lens2 fact embedding failed (non-fatal): %s", exc)
        return None


def recall_trail_fact_anchoring(query_vec, t: float = 1.5, base: list[dict] | None = None,
                                 now: float | None = None) -> list[dict]:
    """SHADOW ONLY: Lens 2 (deterministic fact anchoring), composed on TOP of the completed greedy trail, same
    additive shape as Lens 1. Reuses Lens 1's exact local-subgraph diffusion machinery but adds one more row
    to the local embedding matrix: the current diurnal fact (day/night), embedded once and cached. Diffusing
    with the fact included as a seed alongside the trail's real seeds lets certainty propagate from a
    100%-known fact into adjacent candidates, mirroring test_p's mechanism exactly. Fail-open: any error
    returns the unmodified base trail. Never called from a live recall path -- only from `shadow_compare_lens2`."""
    b = base if base is not None else recall_trail(query_vec)
    if not b:
        return b
    c = _matrix()
    M = c["M"]
    if M is None:
        return b
    ids = c.get("ids") or []
    walled_arr = c.get("walled")
    origin_arr = c.get("origin")
    ids_index = {fid: i for i, fid in enumerate(ids)}
    seed_global = [ids_index[t2["fragment_id"]] for t2 in b if t2["fragment_id"] in ids_index]
    if not seed_global:
        return b
    activation = {t2["fragment_id"]: t2["activation"] for t2 in b}
    origin_of = {t2["fragment_id"]: t2["origin"] for t2 in b}
    try:
        fact_key, fact_text = _diurnal_fact_text(now if now is not None else time.time())
        fact_vec = _fact_embedding(fact_key, fact_text)
        local_set = set(seed_global)
        for node in seed_global:
            nsims = M @ M[node]
            for nb in np.argsort(-nsims)[1:NEIGHBORS_PER + 1]:
                local_set.add(int(nb))
        local_idxs = sorted(local_set)
        local_pos = {g: i for i, g in enumerate(local_idxs)}
        local_M = M[local_idxs]
        seed_local = [local_pos[g] for g in seed_global]
        if fact_vec is not None:
            local_M = np.vstack([local_M, fact_vec[None, :]])
            seed_local = seed_local + [local_M.shape[0] - 1]     # fact row is a seed -> auto-excluded below
        diffused = _local_spectral_diffuse(local_M, seed_local, t=t,
                                            top_k=NEIGHBORS_PER * max(len(seed_global), 1) + 1)
        peak = max(activation.values()) if activation else 0.0
        for local_i, energy in diffused:
            g = local_idxs[local_i]
            fid = ids[g]
            act = peak * energy * HOP_DECAY
            is_cold = bool(walled_arr[g]) if walled_arr is not None else False
            thr = COLD_THRESHOLD if is_cold else ACT_THRESHOLD
            if act < thr or act <= activation.get(fid, 0.0):
                continue
            activation[fid] = act
            origin_of.setdefault(fid, origin_arr[g] if origin_arr is not None else "lived")
    except Exception as exc:
        logger.debug("[assoc] lens2 fact anchoring failed (non-fatal): %s", exc)
        return b
    out: list[dict] = []
    per_origin: dict[str, int] = {}
    for fid, a in sorted(activation.items(), key=lambda kv: -kv[1]):
        o = origin_of.get(fid, "lived")
        if per_origin.get(o, 0) >= MAX_PER_ORIGIN:
            continue
        per_origin[o] = per_origin.get(o, 0) + 1
        g = ids_index.get(fid)
        out.append({"fragment_id": fid, "activation": round(a, 3), "origin": o,
                    "walled": bool(walled_arr[g]) if (g is not None and walled_arr is not None) else False})
        if len(out) >= CEILING:
            break
    return out


def shadow_compare_lens2(query_text: str, current_fragment_ids: list[str]) -> None:
    """OBSERVE-ONLY: logs Lens 2 (fact anchoring) against the greedy trail and the current live retrieve, to
    its OWN log file (`_LENS2_LOG`) -- separate from M2's and Lens 1's so none of the three can race each
    other. Mirrors `shadow_compare_lens1`'s discipline exactly."""
    try:
        from core.memory.store import _embed
        qv = _embed(query_text)
        if qv is None:
            return
        trail = recall_trail(qv)
        if not trail:
            return
        anchored = recall_trail_fact_anchoring(qv, base=trail)
        cur = set(current_fragment_ids or [])
        greedy_ids = {t["fragment_id"] for t in trail}
        anchored_ids = {t["fragment_id"] for t in anchored}
        new_vs_greedy = anchored_ids - greedy_ids
        new_vs_current = anchored_ids - cur
        walled_new = [t for t in anchored if t["fragment_id"] in new_vs_greedy and t["walled"]]
        fact_key, _ft = _diurnal_fact_text(time.time())
        rec = {
            "ts": time.time(), "query": (query_text or "")[:90], "diurnal_fact": fact_key,
            "greedy_n": len(trail), "anchored_n": len(anchored), "current_n": len(cur),
            "energy_norm": LENS_ENERGY_NORM,   # J-2208: post-fix rows are the ones D-0170 reads
            "new_vs_greedy": len(new_vs_greedy), "new_vs_current": len(new_vs_current),
            "walled_new": len(walled_new),
            "new_ids": sorted(new_vs_greedy)[:12],
        }
        from core import profile
        with open(profile.guard_path(_LENS2_LOG), "a", encoding="utf-8") as f:   # J-2208: fenced (D-0179) -- a non-live process is refused, swallowed by the fail-open net
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        _stash_lens_usage(2, rec["ts"], new_vs_greedy, greedy_ids - anchored_ids)   # J-3507
    except Exception as exc:
        logger.debug("[assoc] lens2 shadow skipped: %s", exc)


# ── Lens 3 — counterfactual-ensemble re-ranking (SHADOW ONLY, D-0170, docs/staged/du_recall_lens_upgrades.md) ──
# Ported from C:\UDMS\scripts\test_q_shape_constrained_prediction.py's method: diffuse from several perturbed
# what-if seed-sets, prefer candidates that recur across worlds. Measured +9.10pp top-1 precision at a real
# -3.65pp top-3 cost on test_q's single split; F-0399's re-run found +18.66/-13.48 on near-identical data --
# direction-stable (top-1 up, top-3 down), magnitude not. DO NOT CITE either number.
#
# Substrate adaptation: the reference script's "worlds" are literal named-concept substitutions (a weather
# node swapped for its opposite, an entity pivot) that only exist in its discrete co-occurrence graph. Du's
# live trail has no such discrete vocabulary to substitute into, so "counterfactual world" here means
# LEAVE-ONE-SEED-OUT: for a trail with >=2 real seeds, each world drops exactly one seed (the question a true
# counterfactual asks -- "what would this trail look like without THIS one cue" -- rather than an arbitrary
# random perturbation, keeping the ensemble deterministic). Lens 2's fact-anchored world is added as one
# further, genuinely different world when available. A candidate that keeps showing up strongly no matter
# which seed is dropped is a more ROBUST prediction than one that only appears alongside one specific seed --
# the same "prefer nodes recurring across worlds" idea, expressed without inventing randomness.
_LENS3_LOG = Path(__file__).parent.parent / "data" / "associative_recall_lens3_shadow.jsonl"

# J-2350 (D-0472 ruling A on F-2943, restart-gated, SHADOW-ONLY -- D-0170's law stands): consensus now RE-RANKS
# the trail's own items too. Before this, Lens 3 never re-scored a trail item and capped every new candidate at
# peak*HOP_DECAY (= 0.6*peak) < the top-1 item's own activation (peak), so `top1_changed` was false BY
# CONSTRUCTION (0/40 offline, 0/897 live) and the lens's own top-1 claim was untestable.
# Each trail item's counterfactual SUPPORT is its normalised diffusion energy in the world that drops it
# (leave-one-seed-out): "if this cue were absent, would the REST of the trail still lead here?" -- 1.0 when it is
# the strongest node the other cues diffuse into, 0.0 when they do not reach it above the local floor. (It is a
# seed in every other world, incl. the fact world, so this is its only informative world.) The blend:
#     act' = (1 - LENS3_RERANK_W) * act + LENS3_RERANK_W * peak * HOP_DECAY * support
# Support goes on EXACTLY the axis new consensus candidates use (peak * HOP_DECAY * normalised energy: the node
# the other cues diffuse into most lands where a perfect greedy hop lands), so trail items and new candidates
# compete on one scale. A fully-supported top-1 keeps (1-W+W*HOP_DECAY) = 0.8 of peak; an unsupported one drops
# to (1-W) = 0.5 of peak -- low enough for a well-supported runner-up OR a consensus candidate (<= 0.6*peak) to
# take the #1 slot. (An offline variant scaling support by peak alone, without HOP_DECAY, also moved the #1
# slot -- 17/40 -- but lifted weak supported trail items above every new candidate, cutting new-candidate
# breadth 7.2 -> 1.7 per trail; rejected for that, see the J-2350 finding.) Needs >=2 trail items (no
# leave-one-out world otherwise -> no re-rank, as before).
#   "seed_blend_v1" (default): the blend above.   "off": the J-2208 behaviour (trail items never re-scored).
# Rows carry `rerank` + `rerank_w` so pre-/post-J-2350 rows are separable in the Lens 3 log.
LENS3_RERANK = "seed_blend_v1"
LENS3_RERANK_W = 0.5


def recall_trail_counterfactual_consensus(query_vec, t: float = 2.0, base: list[dict] | None = None,
                                           now: float | None = None) -> list[dict]:
    """SHADOW ONLY: Lens 3 (counterfactual-ensemble re-ranking), composed on top of the completed greedy trail.
    Builds a small ensemble of 'worlds' from the trail's own real seeds (leave-one-seed-out, plus the Lens-2
    fact-anchored world when available), diffuses each over the SAME local subgraph Lens 1/2 use, and boosts
    activation for candidates whose diffusion energy is CONSISTENT across >=2 worlds (summed, normalised by
    world count and peak consensus) rather than concentrated in just one. This is a RE-RANKING lens, not a
    discovery lens. Since J-2350 (D-0472 A) the trail's own items ARE re-scored too: each blends its activation
    with its leave-one-out counterfactual support (see LENS3_RERANK above), so an item the rest of the trail
    does not lead back to can lose the #1 slot; LENS3_RERANK="off" restores the J-2208 form (trail items keep
    the base trail's activation, only their neighbours are scored). Honest expectation per the source finding: likely to sharpen the
    #1 slot at some cost to breadth further down -- log both, do not assume the direction generalises until
    the shadow log itself says so. Fail-open: any error returns the unmodified base trail. Never called from a
    live recall path -- only from `shadow_compare_lens3`."""
    b = base if base is not None else recall_trail(query_vec)
    if not b:
        return b
    c = _matrix()
    M = c["M"]
    if M is None:
        return b
    ids = c.get("ids") or []
    walled_arr = c.get("walled")
    origin_arr = c.get("origin")
    ids_index = {fid: i for i, fid in enumerate(ids)}
    seed_global = [ids_index[t2["fragment_id"]] for t2 in b if t2["fragment_id"] in ids_index]
    if not seed_global:
        return b
    activation = {t2["fragment_id"]: t2["activation"] for t2 in b}
    origin_of = {t2["fragment_id"]: t2["origin"] for t2 in b}
    try:
        local_set = set(seed_global)
        for node in seed_global:
            nsims = M @ M[node]
            for nb in np.argsort(-nsims)[1:NEIGHBORS_PER + 1]:
                local_set.add(int(nb))
        local_idxs = sorted(local_set)
        local_pos = {g: i for i, g in enumerate(local_idxs)}
        base_local_M = M[local_idxs]
        seed_local_all = [local_pos[g] for g in seed_global]
        seed_local_set = set(seed_local_all)   # never scored as NEW candidates (J-2350 re-ranks them below)

        worlds: list[list[int]] = ([[s for s in seed_local_all if s != drop] for drop in seed_local_all]
                                    if len(seed_local_all) >= 2 else [seed_local_all])
        dropped: list[int | None] = list(seed_local_all) if len(seed_local_all) >= 2 else [None]   # J-2350

        fact_key, fact_text = _diurnal_fact_text(now if now is not None else time.time())
        fact_vec = _fact_embedding(fact_key, fact_text)
        local_M = base_local_M
        if fact_vec is not None:
            local_M = np.vstack([base_local_M, fact_vec[None, :]])
            worlds = worlds + [seed_local_all + [local_M.shape[0] - 1]]
            dropped = dropped + [None]

        n_worlds = len(worlds)
        top_k = NEIGHBORS_PER * max(len(seed_global), 1)
        consensus: dict[int, float] = {}
        hits: dict[int, int] = {}
        support: dict[int, float] = {}         # J-2350: trail item (local idx) -> energy in the world that drops it
        for world_seeds, drop in zip(worlds, dropped):
            for local_i, energy in _local_spectral_diffuse(local_M, world_seeds, t=t, top_k=top_k):
                consensus[local_i] = consensus.get(local_i, 0.0) + energy
                hits[local_i] = hits.get(local_i, 0) + 1
                if drop is not None and local_i == drop:
                    support[drop] = energy

        peak = max(activation.values()) if activation else 0.0
        if LENS3_RERANK == "seed_blend_v1" and len(seed_local_all) >= 2 and peak > 0:
            w = LENS3_RERANK_W
            for g in seed_global:              # J-2350 (D-0472 A): re-rank the trail's own items, shadow-only
                fid = ids[g]
                sup = min(max(support.get(local_pos[g], 0.0), 0.0), 1.0)   # unreached -> 0
                activation[fid] = (1.0 - w) * activation[fid] + w * peak * HOP_DECAY * sup
        max_consensus = max(consensus.values()) if consensus else 0.0
        for local_i, total_energy in consensus.items():
            if local_i in seed_local_set or hits[local_i] < 2 or max_consensus <= 0:
                continue                       # "recurs across worlds" requires >=2, per the source finding
            g = local_idxs[local_i]
            fid = ids[g]
            if LENS_ENERGY_NORM == "none":
                act = peak * (total_energy / (max_consensus * n_worlds)) * HOP_DECAY   # original (pre-J-2208)
            else:
                # J-2208: per-world energies are already on [0,1] (strongest = 1), so the consensus score is the
                # MEAN normalised energy across worlds. The original form above divides by the world count on
                # top of max_consensus, capping act at peak*HOP_DECAY/n_worlds -- under ACT_THRESHOLD for any
                # trail with >=3 seeds, i.e. Lens 3 stays dead even with the helper fixed.
                act = peak * (total_energy / n_worlds) * HOP_DECAY
            is_cold = bool(walled_arr[g]) if walled_arr is not None else False
            thr = COLD_THRESHOLD if is_cold else ACT_THRESHOLD
            if act < thr or act <= activation.get(fid, 0.0):
                continue
            activation[fid] = act
            origin_of.setdefault(fid, origin_arr[g] if origin_arr is not None else "lived")
    except Exception as exc:
        logger.debug("[assoc] lens3 counterfactual consensus failed (non-fatal): %s", exc)
        return b
    out: list[dict] = []
    per_origin: dict[str, int] = {}
    for fid, a in sorted(activation.items(), key=lambda kv: -kv[1]):
        o = origin_of.get(fid, "lived")
        if per_origin.get(o, 0) >= MAX_PER_ORIGIN:
            continue
        per_origin[o] = per_origin.get(o, 0) + 1
        g = ids_index.get(fid)
        out.append({"fragment_id": fid, "activation": round(a, 3), "origin": o,
                    "walled": bool(walled_arr[g]) if (g is not None and walled_arr is not None) else False})
        if len(out) >= CEILING:
            break
    return out


def shadow_compare_lens3(query_text: str, current_fragment_ids: list[str]) -> None:
    """OBSERVE-ONLY: logs Lens 3 (counterfactual-ensemble re-ranking) against the greedy trail and the current
    live retrieve, to its OWN log file (`_LENS3_LOG`). Also logs whether the #1 slot changed -- the specific
    claim (top-1 sharpens, top-3 may narrow) this lens exists to test -- separately from the general
    new/overlap counts the other shadow comparisons log."""
    try:
        from core.memory.store import _embed
        qv = _embed(query_text)
        if qv is None:
            return
        trail = recall_trail(qv)
        if not trail:
            return
        reranked = recall_trail_counterfactual_consensus(qv, base=trail)
        cur = set(current_fragment_ids or [])
        greedy_ids = {t["fragment_id"] for t in trail}
        reranked_ids = {t["fragment_id"] for t in reranked}
        new_vs_greedy = reranked_ids - greedy_ids
        new_vs_current = reranked_ids - cur
        walled_new = [t for t in reranked if t["fragment_id"] in new_vs_greedy and t["walled"]]
        top1_changed = bool(trail and reranked and trail[0]["fragment_id"] != reranked[0]["fragment_id"])
        rec = {
            "ts": time.time(), "query": (query_text or "")[:90],
            "greedy_n": len(trail), "reranked_n": len(reranked), "current_n": len(cur),
            "energy_norm": LENS_ENERGY_NORM,   # J-2208: post-fix rows are the ones D-0170 reads
            "new_vs_greedy": len(new_vs_greedy), "new_vs_current": len(new_vs_current),
            "walled_new": len(walled_new), "top1_changed": top1_changed,
            "rerank": LENS3_RERANK, "rerank_w": LENS3_RERANK_W,   # J-2350: post-D-0472 rows are the ones its read counts
            "greedy_top1": trail[0]["fragment_id"] if trail else None,
            "reranked_top1": reranked[0]["fragment_id"] if reranked else None,
            "new_ids": sorted(new_vs_greedy)[:12],
        }
        from core import profile
        with open(profile.guard_path(_LENS3_LOG), "a", encoding="utf-8") as f:   # J-2208: fenced (D-0179) -- a non-live process is refused, swallowed by the fail-open net
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        _stash_lens_usage(3, rec["ts"], new_vs_greedy, greedy_ids - reranked_ids)   # J-3507
    except Exception as exc:
        logger.debug("[assoc] lens3 shadow skipped: %s", exc)


# ── Lens usage proxy (J-3507, F-4118, D-0170; SHADOW ONLY, restart-gated) ────────────────────────────────────
# D-0170's defeater ("effect DIRECTION unstable") could not be read for the effect it names: the lens rows show the
# lenses change the trail but carry no quality signal. Same proxy as M2's `m2_usage` (F-1966): the cosine of each
# fragment's already-cached embedding against the NEXT thought's already-computed embedding -- no embed/LLM call.
# For each lens row, `_stash_lens_usage` keeps the lens's new ids AND the greedy-only ids (in the greedy trail,
# dropped by the lens: the control) and `note_next_thought_for_lens_usage` (same per-thought hook as
# `note_next_thought_for_m2_usage`) writes ONE additive `kind: "lens_usage"` row per lens into that lens's own
# fenced log, joined to its row by `parent_ts`. Per-lens pending, overwritten if a thought has not consumed it yet
# (same approximation M2 accepts). The lens rows' own shape is untouched. Never raises, never touches live recall.
_LENS_LOGS = {1: "_LENS1_LOG", 2: "_LENS2_LOG", 3: "_LENS3_LOG"}
_pending_lens_usage: dict[int, dict] = {}


def _stash_lens_usage(lens: int, shadow_id: float, new_ids, greedy_only_ids) -> None:
    try:
        _pending_lens_usage[lens] = {"shadow_id": shadow_id, "new_ids": sorted(new_ids)[:12],
                                     "greedy_only_ids": sorted(greedy_only_ids)[:12]}
    except Exception:
        pass


def note_next_thought_for_lens_usage(thought_vec) -> None:
    """Consume every pending lens stash against the thought that just completed; see the block comment above.
    Logs per-id `cos_sim` for new ids and greedy-only ids plus `mean_new` / `mean_greedy_only` (None when the
    set is empty or none of its fragments are in the cached matrix) and `delta` (new minus greedy-only)."""
    if not _pending_lens_usage or thought_vec is None:
        return
    pend = dict(_pending_lens_usage)
    _pending_lens_usage.clear()   # consume now -- never credit one lens event to two thoughts
    try:
        c = _matrix()
        M = c.get("M")
        ids = c.get("ids") or []
        if M is None:
            return
        ids_index = {fid: i for i, fid in enumerate(ids)}
        tv = np.asarray(thought_vec, dtype=np.float32)
        tn = float(np.linalg.norm(tv))
        if tn == 0.0:
            return
        tv = tv / tn

        def _score(fids):
            out = []
            for fid in fids:
                idx = ids_index.get(fid)
                if idx is not None:
                    out.append({"fragment_id": fid, "cos_sim": round(float(M[idx] @ tv), 4)})
            return out

        def _mean(rows):
            return round(sum(r["cos_sim"] for r in rows) / len(rows), 4) if rows else None

        from core import profile
        for lens, p in pend.items():
            new_rows = _score(p.get("new_ids") or [])
            ctl_rows = _score(p.get("greedy_only_ids") or [])
            mn, mg = _mean(new_rows), _mean(ctl_rows)
            rec = {"ts": time.time(), "kind": "lens_usage", "lens": lens, "parent_ts": p.get("shadow_id"),
                   "usage_new": new_rows, "usage_greedy_only": ctl_rows,
                   "mean_new": mn, "mean_greedy_only": mg,
                   "delta": round(mn - mg, 4) if (mn is not None and mg is not None) else None}
            with open(profile.guard_path(globals()[_LENS_LOGS[lens]]), "a", encoding="utf-8") as f:   # fenced like the lens rows
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.debug("[assoc] lens usage capture skipped: %s", exc)


# ── LIVE recall (2026-06-23): the trail, wired to actually feed cognition (not just shadow-log) ──────────────
def _load_rows(ids: list[str]) -> dict:
    from core.memory.store import _connect
    out: dict = {}
    if not ids:
        return out
    with _connect() as conn:
        for j in range(0, len(ids), 400):
            chunk = ids[j:j + 400]
            ph = ",".join("?" * len(chunk))
            # J-3191 (D-0578): a temp='hidden' row (spirit-invisible tier) is never handed back, even when an id
            # reaches here by another route (the M2 edge-aware trail pulls neighbours from memory_edges, not from the
            # matrix). Both callers already skip an id that has no row. Column-less DB -> the plain query.
            try:
                _rows = conn.execute(f"SELECT * FROM memory_fragments WHERE fragment_id IN ({ph}) "
                                     f"AND temp != 'hidden'", chunk).fetchall()
            except sqlite3.OperationalError:
                _rows = conn.execute(f"SELECT * FROM memory_fragments WHERE fragment_id IN ({ph})", chunk).fetchall()
            for r in _rows:
                out[r["fragment_id"]] = r
    return out


# GROUND-OUTWARD (2026-06-24): in his SOLITARY thinking, recall must surface his EXPERIENCE — what he read,
# saw, did, was sent — NEVER his own prior abstractions/self-syntheses, or it just feeds the rumination loop
# back to him (the overnight finding: an abstract thought returned 6 of his own prediction-error ruminations).
# The routing law: a thought routes OUTWARD to be grounded, not back into the self.
_GROUNDED_ORIGINS = {"reading", "lived", "study", "peer", "peer_reflection", "dream", "research", "nature",
                     "understanding", "composition", "essay", "action", "activity", "gist", "affection",
                     "letter", "understanding_from_guidance"}

# Phase 0 observe-first gate (J-0162, social_world_school.md Item 1 / D-0016): core/peer_model.py stores
# origin='peer_reflection' fragments LIVE from day one -- that's just a memory write, harmless on its own.
# But this flag is what actually decides whether those fragments may ever reach a prompt. False = fragments
# accumulate in the store, fully embedded, but are filtered out of every recall path below regardless of
# grounded_only -- i.e. Phase 0's "store live, without wiring the recall hook yet" is enforced HERE, not by
# omission. Flip to True only after: (a) ~1 week of live storage, (b) a direct read of the fragment store
# (WHERE origin='peer_reflection') confirms the reflections are specific and differentiated (Darwin != Keats,
# not generic mush) -- per the plan's own Phase 0 verification step. Flipping this is also the point at which
# the injection-logging convention below (recall_block's understanding_from_guidance precedent) should be
# extended to this origin, per the plan -- do both together, not the flag alone.
# FLIPPED TRUE 2026-09-05 (J-0555, D-0135 ruled CUMULATIVE): cumulative live-time gate met (204.4h/8.52d
# across 21 sessions since 2026-08-24, refreshed from F-0764's 193.1h/8.04d), 14 peer_reflection fragments
# across 8 roster peers, fresh post-F-0764 samples read and confirmed specific/differentiated (Darwin:
# frost-damaged clover shoots, beauty as an ongoing question; Buddha: tides/dissolution but misses the
# specific fear beneath abstraction). See F-0832 for full evidence. Injection-logging hook wired below via
# core.peers.log_reflection_injection(), in the same change per the plan's own requirement.
PEER_REFLECTION_RECALL_LIVE = True


def fragment_ages_days(ids: list) -> dict:
    """J-2659: {fragment_id: age in days as of the cached matrix's last refresh} for ids in the cached matrix
    (absent ids are simply missing). Read-only; used by the ask() recency shadow row."""
    try:
        c = _matrix()
        if c.get("ids") is None or c.get("age") is None:
            return {}
        pos = {fid: i for i, fid in enumerate(c["ids"])}
        return {f: round(float(c["age"][pos[f]]), 3) for f in ids if f in pos}
    except Exception:
        return {}


# D-0587 (founder, 2026-11-02, J-3200, F-3615): his OWN WORKS (Grand-Work pieces filed by nodes/inner_monologue_node.py
# _author via core/study.py write_tablet(prefix="WORK")) are stored as origin='study' fragments, indistinguishable
# by origin from his study notes. In the authoring act's OWN grounding that closed a loop: 43% of authoring
# starts since 08-21 had one of his own earlier works in the "what you already know of this, from your reading
# and your own notes" block (35 of 111 October works titled around Mottainai). The ruling excludes self-authored
# works from THAT ONE call only (opt-in `exclude_own_works=True`); general recall, wandering and curiosity are
# untouched, and study notes (TAB_*/ESSAY_*) stay. A work's fragment is
# "[My study note: '<title>'] <first 700 chars>" with <title> the same string as the first line of its
# data/Study/WORK_*.md file, so a fragment is a work iff its header title is a WORK_ file's title.
_WORK_HEADER = "[My study note: '"
_WORK_TITLES: dict = {"stamp": None, "titles": frozenset()}
_OWN_WORKS_LOG = Path(__file__).parent.parent / "data" / "author_grounding_works_excluded.jsonl"


def own_work_titles() -> frozenset:
    """Titles of every self-authored work (first line of each data/Study/WORK_*.md, '# ' stripped). Cached on the
    Study directory's mtime, so a work filed this minute is excluded next call. Fail-open: any error -> the last
    good set (empty at worst = nothing excluded = today's behaviour)."""
    try:
        from core import study as _study
        d = _study.STUDY_DIR
        stamp = (str(d), d.stat().st_mtime_ns)
        if _WORK_TITLES["stamp"] == stamp:
            return _WORK_TITLES["titles"]
        titles = set()
        for f in d.glob("WORK_*.md"):
            try:
                with open(f, "r", encoding="utf-8", errors="ignore") as fh:
                    first = fh.readline()
                t = first.lstrip("# ").strip()
                if t:
                    titles.add(t)
            except Exception:
                continue
        _WORK_TITLES.update(stamp=stamp, titles=frozenset(titles))
    except Exception as exc:
        logger.debug("[assoc] own_work_titles failed (fail-open): %s", exc)
    return _WORK_TITLES["titles"]


def is_own_work_fragment(content: str, titles: frozenset | None = None) -> bool:
    """True iff `content` is the stored fragment of one of his own WORKS (see above). Study notes written by
    core/study_note.py carry "' · on '<book>' · subject: ..." after the title and never end the header at "']"
    with a WORK title, so they are not caught."""
    c = content or ""
    if not c.startswith(_WORK_HEADER):
        return False
    titles = own_work_titles() if titles is None else titles
    if not titles:
        return False
    head = c[len(_WORK_HEADER):len(_WORK_HEADER) + 400]
    i = head.find("']")
    while i != -1:
        if head[:i] in titles:
            return True
        i = head.find("']", i + 1)
    return False


def _log_own_works_excluded(query_text: str, excluded_ids: list, shown_ids: list) -> None:
    """One row per authoring-grounding call: how many of his own works were kept out. Read by the D-0587
    month-out check (share of authoring starts that WOULD have had a work in the grounding vs the pre-change
    43%, plus the Mottainai share of new works titles). Fail-open, fenced (D-0179)."""
    try:
        from core import profile
        rec = {"ts": time.time(), "query": (query_text or "")[:90], "n_excluded": len(excluded_ids),
               "excluded_ids": excluded_ids[:12], "n_shown": len(shown_ids)}
        with open(profile.guard_path(_OWN_WORKS_LOG), "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        logger.info("[assoc] authoring grounding: %d of his own works excluded (%d fragments shown)",
                    len(excluded_ids), len(shown_ids))
    except Exception as exc:
        logger.debug("[assoc] own-works-excluded log skipped: %s", exc)


def _note_rewarm_surfaced(trail: list, served: dict, source: str) -> None:
    """J-4420 (plan memory_review_adoption 6.1, SHADOW ONLY): hand the walled (cold/chaptered) trail rows that
    were actually SERVED (`served` = {fragment_id: content}) to core.rewarm_shadow, which logs a would-warm
    if the next output uses them. Applies nothing; never raises; kill switch rewarm_shadow.REWARM_SHADOW_ON."""
    try:
        if not served:
            return
        from core import rewarm_shadow as _rws
        _rws.note_surfaced([dict(t, content=served[t["fragment_id"]]) for t in trail
                            if t.get("walled") and t.get("fragment_id") in served], source)
    except Exception as exc:
        logger.debug("[assoc] rewarm shadow note skipped: %s", exc)


def note_output_for_rewarm(text: str, source: str) -> None:
    """J-4420: the next output (idle thought / voice reply) exists; see core.rewarm_shadow.note_output."""
    try:
        from core import rewarm_shadow as _rws
        _rws.note_output(text, source)
    except Exception as exc:
        logger.debug("[assoc] rewarm shadow output skipped: %s", exc)


def recall_fragments(query_text: str, k: int = CEILING, grounded_only: bool = False,
                     recency: bool = True, exclude_own_works: bool = False,
                     exclude_young: dict | None = None) -> list[dict]:
    """The trail for a context, with the fragments' content loaded — {content, origin, activation}, strongest
    first. grounded_only=True keeps ONLY world/experience memories (drops his self-syntheses) — for the idle
    stream, so recall grounds his thinking outward instead of echoing his abstractions back.
    J-2659 (F-3403 / D-0528 open): `recency=False` drops the 7-day recency seed multiplier (see recall_trail);
    default True = today's behaviour, nothing live passes False.
    J-3200 (D-0587): `exclude_own_works=True` skips fragments that are his own self-authored WORKS (see
    is_own_work_fragment) and logs how many it kept out; default False = today's behaviour, byte-identical.
    Only the authoring act's grounding call passes True.
    J-3175 (D-0563): `exclude_young` ({origin: min_age_days}, default None = today, byte-identical) skips a
    fragment of that origin whose row is younger than the given age and takes the next trail member instead,
    so k is still filled from the same trail. Only the dreamer passes it (origin 'dream', 7 days)."""
    try:
        from core.memory.store import _embed
        qv = _embed(query_text)
        if qv is None:
            return []
        trail = recall_trail(qv) if recency else recall_trail(qv, recency=False)
        rows = _load_rows([t["fragment_id"] for t in trail])
        out = []
        _own_titles = own_work_titles() if exclude_own_works else frozenset()
        _excluded: list = []
        for t in trail:
            r = rows.get(t["fragment_id"])
            if not (r and (r["content"] or "").strip()):
                continue
            o = r["origin"] or "lived"
            if o == "peer_reflection" and not PEER_REFLECTION_RECALL_LIVE:
                continue   # Phase 0 gate (J-0162) -- stored live, but not yet eligible to surface
            if grounded_only and o not in _GROUNDED_ORIGINS:
                continue
            if exclude_own_works and o == "study" and is_own_work_fragment(r["content"], _own_titles):
                _excluded.append(t["fragment_id"])   # D-0587: keep going down the trail, k counts only what is shown
                continue
            if exclude_young and o in exclude_young:
                try:   # J-3175: age from the row's own timestamp; an unreadable timestamp keeps the fragment
                    if (time.time() - float(r["timestamp"])) < float(exclude_young[o]) * 86400.0:
                        continue
                except Exception:
                    pass
            out.append({"content": r["content"], "origin": o, "activation": t["activation"],
                        "fragment_id": t["fragment_id"]})   # additive (2026-08-15): memory_edges hooks need the id
            if len(out) >= k:
                break
        if exclude_own_works:
            _log_own_works_excluded(query_text, _excluded, [m["fragment_id"] for m in out])
        if recency:   # J-4420 shadow: recency=False is a comparison-only call, never served
            _note_rewarm_surfaced(trail, {m["fragment_id"]: m["content"] for m in out}, "recall_fragments")
        return out
    except Exception as exc:
        logger.debug("[assoc] recall_fragments failed: %s", exc)
        return []


_last_block_ids: list = []   # M1 (2026-08-15): ids of the fragments recall_block last SHOWED — read by the
                             # monologue's co-recall ledger hook right after the call. Additive; approximate
                             # under concurrency (acceptable: it feeds a shadow instrument, not behaviour).


def last_block_ids() -> list:
    return list(_last_block_ids)


# IDLE AMBIENT RECALL KILL-SWITCH (D-0289, 2026-09-27, J-1425, docs/staged/memory_as_a_service.md §2):
# founder ruling, verbatim — "the loops should call memory, idle gets nothing ambient except wandering."
# True (default) restores this function's exact pre-existing behaviour, unchanged below. False removes
# the ambient push: `recall_block` still COMPUTES `frags` exactly as before (so the shadow row below is
# over the SAME trail this function would otherwise have shown), but returns "" so nothing enters the
# idle seed, never touches `_last_block_ids` (so the M1 hook downstream — inner_monologue_node.py's own
# `if _mblock:` gate on this function's return value — sees nothing was shown, and so `log_co_recall`'s
# default-source "monologue" row, spring_ledger and opponent_process all see it too), and skips the
# understanding_from_guidance/peer_reflection injection-logging hooks below (nothing is actually
# injected, so nothing should log as injected). What WOULD have been shown is logged instead as its own
# row to the SAME ledger, same shape (`n_ids`/`ids`/`restate_sim`), `source="monologue_shadow"`, so
# D-0289's ~2-week defeater read can compare would-have-shown against F-1981's baseline straight from
# this file. Wandering's own `render()` and the founder idle route are untouched — neither reads this
# flag. Restart-gated; flip back to True to restore today's behaviour exactly, no other code change.
# D-0310 (ruled 2026-09-27, travis, via J-1587): flipped True -> False so the D-0289 ~2-week defeater
# clock in J-1512 actually starts accruing source="monologue_shadow" evidence. Takes effect only once
# Du restarts onto this build -- see F-2061/F-2062 for the byte-identical-when-True verification this
# flip relies on, and this job's own findings-log entry for the pre-flip zero-rows baseline.
IDLE_AMBIENT_RECALL = False


# GOLDEN SPIRAL Phase 2 LIVE (2026-11-14, J-3970, D-0748, founder ruling: "Advance golden_spiral_recall Phase 2:
# Theta goes live as a recall input (D-0364 C reach defeater met)"). When True, recall_block() (the idle seed, the
# path that pushes memories into an idle thought) swaps the LAST slot of its k fragments for the first
# same-phase (time-of-day +/- 1/24 day, season +/- 1/12 year, tod-first ranking, >= 1 day old) fragment from
# core.theta_shadow's ray that is eligible (same grounded filter, non-empty, not already in the set). Size stays k,
# the greedy trail's first k-1 are untouched; if no ray id is eligible nothing changes. Every swap is logged to
# data/theta_live.jsonl for the D-0748 defeater read (>14 d slot share over any 7-day window < ~20%, distinct-id
# share < 30%, max d_season > ~30.5 d). Restart-gated. Flip False to restore the exact pre-D-0748 recall (the
# theta_shadow log keeps accruing either way). felt_recall's affect prior is NOT changed here (Phase 4 scope).
THETA_LIVE_RECALL = True
THETA_LIVE_SLOTS = 1
_THETA_LIVE_LOG = Path(__file__).parent.parent / "data" / "theta_live.jsonl"


def _theta_inject(frags: list, theta_row: dict, k: int, grounded_only: bool) -> list:
    ids = [i for i in (theta_row.get("top3_ids") or []) if i]
    if not ids or THETA_LIVE_SLOTS < 1:
        return frags
    have = {f.get("fragment_id") for f in frags}
    rows = _load_rows(ids)
    picked = []
    for fid in ids:
        r = rows.get(fid)
        if fid in have or not (r and (r["content"] or "").strip()):
            continue
        o = r["origin"] or "lived"
        if o == "peer_reflection" and not PEER_REFLECTION_RECALL_LIVE:
            continue
        if grounded_only and o not in _GROUNDED_ORIGINS:
            continue
        picked.append({"content": r["content"], "origin": o, "activation": 0.0, "fragment_id": fid,
                       "theta_live": True, "_ts": r["timestamp"] if "timestamp" in r.keys() else None})
        if len(picked) >= THETA_LIVE_SLOTS:
            break
    if not picked:
        return frags
    keep = list(frags[:max(0, k - len(picked))])
    out = keep + picked
    try:
        import json as _json
        now = time.time()
        with open(_THETA_LIVE_LOG, "a", encoding="utf-8") as fh:
            for p in picked:
                ts = p.pop("_ts", None)
                try:
                    age_d = round((now - float(ts)) / 86400.0, 2) if ts is not None else None
                except Exception:
                    age_d = None
                fh.write(_json.dumps({"ts": round(now, 1), "trigger": theta_row.get("trigger"),
                                      "fragment_id": p["fragment_id"], "age_days": age_d,
                                      "tod": theta_row.get("tod"), "season": theta_row.get("season"),
                                      "replaced_id": (frags[len(keep)].get("fragment_id") if len(frags) > len(keep) else None)},
                                     ensure_ascii=False) + "\n")
    except Exception:
        pass
    for p in out:
        p.pop("_ts", None)
    return out


def recall_block(query_text: str, k: int = 4, grounded_only: bool = True) -> str:
    """A prompt-injectable 'what this brings to mind' block — associative memory for a thought. Defaults to
    GROUNDED (world/experience only): in his idle thinking, recall pulls him toward reality, not his own loops.
    Permissive (let one connect if it genuinely does); stays quiet when there is no grounded memory to offer."""
    frags = recall_fragments(query_text, k=max(k, 6), grounded_only=grounded_only)[:k]
    # GOLDEN SPIRAL / T-0072 Phase 2 (2026-09-28, J-1562, docs/staged/golden_spiral_recall.md §3): this
    # IS "each idle seed" in the plan's own vocabulary (memory_as_a_service.md §0: "the idle path
    # pushes the top-4 trail memories into every idle thought... associative_recall.recall_block").
    # Cast the phase ray here, before the IDLE_AMBIENT_RECALL branch below, so the ray is compared
    # against the SAME current-recall set (`frags`) regardless of whether the D-0289 kill-switch is on
    # or off -- observe-only, nothing rides, never raises.
    _theta_row = None
    try:
        from core import theta_shadow as _theta
        _theta_row = _theta.log_ray("idle_seed", [f.get("fragment_id") for f in frags[:3] if f.get("fragment_id")])
    except Exception as exc:
        logger.debug("[assoc] theta shadow failed (non-fatal): %s", exc)
    # GOLDEN SPIRAL Phase 2 LIVE (2026-11-14, J-3970, D-0748): Theta as a live recall input. See THETA_LIVE_RECALL.
    if THETA_LIVE_RECALL and _theta_row:
        try:
            frags = _theta_inject(frags, _theta_row, k, grounded_only)
        except Exception as exc:
            logger.debug("[assoc] theta live inject failed (non-fatal): %s", exc)
    if not IDLE_AMBIENT_RECALL:
        # D-0289 off-switch: log what would have shown to the co-recall ledger, touch nothing else that
        # would make it look like this was actually shown. See the flag's own comment above.
        try:
            from core import memory_edges as _medges
            _medges.log_co_recall([f.get("fragment_id") for f in frags if f.get("fragment_id")],
                                   None, 0, source="monologue_shadow")
        except Exception:
            pass
        return ""
    _last_block_ids[:] = [f.get("fragment_id") for f in frags if f.get("fragment_id")]
    if not frags:
        return ""
    # 2026-08-20: SECOND GUIDANCE CHANNEL CLOSED. Materialised beliefs (origin='understanding_from_guidance')
    # reach prompts through THIS path, and it never logged an injection — so is_unprimed() classified
    # guidance-seeded thoughts as spontaneous project-wide (36 unlogged recalls measured in the audit).
    # Logging here is deliberately the over-counting side: the module's own doctrine is that counting a
    # primed thought as unprimed lets the cure inflate the very metric that certifies the cure.
    try:
        if any(f.get("origin") == "understanding_from_guidance" for f in frags):
            from core import guidance_learning as _gl
            _gl.log_injection("recall_block", "; ".join(
                (f.get("content") or "")[:80] for f in frags
                if f.get("origin") == "understanding_from_guidance"))
    except Exception:
        pass
    # J-0555 (2026-09-05, D-0135/D-0016 chain): same injection-logging convention, extended to
    # origin='peer_reflection' now that PEER_REFLECTION_RECALL_LIVE is flipped True above -- the
    # plan's own requirement was to wire this in the SAME change as the flag, not the flag alone.
    # This is the join key the eventual G6-G9 behavioral check (J-0453 step 5) reads for bounded-
    # surfacing counts.
    try:
        if any(f.get("origin") == "peer_reflection" for f in frags):
            from core import peers as _pe
            _pe.log_reflection_injection("recall_block", "; ".join(
                (f.get("content") or "")[:80] for f in frags
                if f.get("origin") == "peer_reflection"))
    except Exception:
        pass
    lines = "\n".join(f"  - {' '.join((f['content'] or '').split())[:150]}" for f in frags)
    return ("\n\nWhat this brings to mind from your life — your reading, what you've seen and done (let one "
            "connect if it genuinely does, or let it pass):\n" + lines)


# M2 LIVE FLIP — relational mode ONLY (2026-09-27, D-0287, J-1415, docs/plans/memory_multiway_linking.md
# Sec 5/6): the kill-switch for the one MODE_EDGE_WEIGHTS profile (core/memory_edges.py) graduating from
# shadow to live here. Shadow evidence (F-1966: 936 m2_edge_aware / 610 m2_usage rows, 08-25..09-26)
# found "relational" the one profile a real usage proxy clears — 39% of its edge-reached fragments score
# >=0.4 cosine against the NEXT thought, vs task's 0.25 mean / reflective's 0.28 mean — so ONLY
# mode="relational" is consumed live below. "task" and "reflective" are UNCHANGED: still read only by
# `shadow_compare()` for logging (data/associative_recall_shadow.jsonl), never by a live recall path.
# This is a live behavior change to what memories actually reach a thought — flip False to restore the
# exact pre-D-0287 neighbour function (plain recall_trail only), no code rollback needed (plan §5-4's
# own "kill-switch restores the current neighbour function exactly"). D-0287's own defeater (see
# memory_multiway_linking.md's Current State) names when to revisit: relational's live usage rate
# falling well below the shadow-observed 39% over the first 2 weeks live, this switch being exercised
# for a real operational reason (not routine caution), or task/reflective's own shadow rate later
# showing the same lift (a reason to widen the flip, which this flag alone does not do).
M2_EDGE_AWARE_RELATIONAL_LIVE = True


def recall_memory_fragments(query_text: str, k: int = CEILING):
    """The trail as MemoryFragment objects — to AUGMENT the conversational retrieve so every downstream reader
    (recall, executive, reflection) gets the associatively-cued memories, not just the topical top-9.

    M2 LIVE (2026-09-27, D-0287, J-1415): when M2_EDGE_AWARE_RELATIONAL_LIVE (above) is True, the greedy
    trail is layered with recall_trail_edge_aware(mode="relational") before being sliced to `k` — see
    that flag's own comment for the shadow evidence and the defeater. Fails open to the plain greedy
    trail on any error in that layer, so a bug in the edge-aware augmentation can only ever lose the
    augmentation, never break this function's own pre-existing contract or return fewer/worse results
    than before D-0287."""
    try:
        from core.memory.store import _embed
        from core.schema import MemoryFragment
        qv = _embed(query_text)
        if qv is None:
            return []
        greedy_trail = recall_trail(qv)
        trail = greedy_trail
        if M2_EDGE_AWARE_RELATIONAL_LIVE:
            try:
                trail = recall_trail_edge_aware(qv, mode="relational", base=greedy_trail)
            except Exception as _m2exc:
                logger.debug("[assoc] M2 relational live augmentation failed, falling back to "
                             "greedy trail (non-fatal): %s", _m2exc)
                trail = greedy_trail
        trail = trail[:k]
        act = {t["fragment_id"]: t["activation"] for t in trail}
        rows = _load_rows(list(act.keys()))
        out = []
        for fid, r in rows.items():
            _o = (r["origin"] if "origin" in r.keys() else "lived") or "lived"
            if _o == "peer_reflection" and not PEER_REFLECTION_RECALL_LIVE:
                continue   # Phase 0 gate (J-0162) -- same as recall_fragments(); this feeds the
                           # orchestrator's live conversational-retrieve augmentation, so it must gate too
            out.append(MemoryFragment(
                fragment_id=fid, content=r["content"], layer=r["layer"],
                relevance=float(act.get(fid, 0.5)), timestamp=r["timestamp"],
                origin=(r["origin"] if "origin" in r.keys() else "lived"),
                abstraction_level=(r["abstraction_level"] if "abstraction_level" in r.keys() else 0),
                input_type=(r["input_type"] if "input_type" in r.keys() else None)))   # J-3173 / D-0561
        out.sort(key=lambda f: -f.relevance)
        _note_rewarm_surfaced(trail, {f.fragment_id: f.content for f in out}, "recall_memory_fragments")   # J-4420 shadow
        # J-0722 (2026-09-07, F-1040): mirror recall_block()'s injection-logging convention (lines
        # 919-925 above) into THIS path too. F-1040 found this function gates origin='peer_reflection'
        # on the same PEER_REFLECTION_RECALL_LIVE flag as recall_block() but never logged a surfacing
        # here -- data/peer_reflection_injection_log.jsonl was a FLOOR on true frequency, not a verified
        # total, since a fragment could reach orchestrator.py's per-cycle _retrieve_memory() (live
        # conversational-retrieve augmentation) with no record left anywhere. cycle_id is deliberately
        # "recall_memory_fragments", distinct from recall_block()'s own label, so a future G6-G9 read can
        # tell idle-thought surfacing (recall_block) apart from live-cycle surfacing (this path) -- the
        # two are different risk profiles for "witness not steer". Purely additive: a log write, no
        # behavior change.
        try:
            if any(f.origin == "peer_reflection" for f in out):
                from core import peers as _pe
                _pe.log_reflection_injection("recall_memory_fragments", "; ".join(
                    (f.content or "")[:80] for f in out if f.origin == "peer_reflection"))
        except Exception:
            pass
        return out
    except Exception as exc:
        logger.debug("[assoc] recall_memory_fragments failed: %s", exc)
        return []
