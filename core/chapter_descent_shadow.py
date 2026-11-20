"""
chapter_descent_shadow.py -- J-3319 (D-0637, plan memory_knowledge, prompt-free). Design and pre-registered read:
docs/reviews/J-3248_chaptered_memory_recall_review.md sections 5 and 6 (findings F-3907, F-3908, F-3909).

WHAT THIS IS. An OBSERVE-ONLY instrument that answers one question for the founder's D-0637 read: when a chapter
gist is already in the set Du is served on his own cue, which members of that chapter lie closest to the present
query, and would surfacing them add anything? Today the members behind a period chapter are sealed (19,052 rows,
8 of 3,224 served slots in six days, F-3908) because chapters never got the memory_levels parent/child links every
other gist has. A live "descent" (the recall-balance step also fetching the one or two nearest members) is the
recommended design; this module builds only its SHADOW. It injects NOTHING into the recall set, writes NOTHING to
memory_fragments or any store, adds NO prompt text, and does not touch _lattice_parents or deep_recall. The live
path is byte-identical: the hook in core/orchestrator.py _retrieve_memory only READS self.state.memory_fragments
(it passes a snapshot tuple) and ignores the return value.

WHAT IT LOGS. One jsonl row per (cycle, served chapter) to data/chapter_descent_shadow.jsonl (profile.guard_path,
same fence as the other shadows): ts, cycle_id, input_type, chapter_id, chapter_level, n_members, query_head (120
chars), served_ids, served_cos_median, served_lex_median, n_dropped_served, n_dropped_neardup, ms, and
  candidates              the top 3 members by cosine to the query, each {fragment_id, origin, cos, lex_overlap,
                          age_days, max_cos_to_served}; members already served, and members with cosine >= 0.85
                          to any served fragment, are dropped first
  control_chapter_member  one random ELIGIBLE member of the same chapter (not a top-3 candidate when another one
                          exists; seed = cycle_id + chapter_id, so a re-run draws the same member)
  control_unwalled        one random unwalled episodic pool row whose cosine to the query is within +/-0.05 of the
                          best candidate's (same fields; null when no candidate, or the pool view is not serving)
Content-word overlap = tokens of 4+ letters minus a stopword list, as in docs/lab/chapter_wall_descent_J-3248.py:
|tokens(row) & tokens(query)| / |tokens(query)|.

WHICH CHAPTERS. A fragment in the served set with origin == 'chapter' and relevance >= RECALL_GIST_MIN_RELEVANCE
(0.25, the same gate _deep_recall_balance uses to call a gist central). At most MAX_CHAPTERS_PER_CYCLE rows a cycle
(the same cap idea as RECALL_EXPAND_GISTS; the replay expects 0 or 1 in 91 percent of cycles).

COST. Cycles with no served chapter return before any query or embed (the common case, about 91 percent). Otherwise:
one query embedding, one indexed SELECT by chapter_id (idx_chapter; mean 222 members, max 1,845; vectors only, the
content of at most 5 rows is read afterwards), a matrix-vector product, one log line. `ms` is logged per row and a
row above SLOW_MS (50) is flagged `slow` and logged at INFO, so the founder's 50 ms budget is read from data.

READER (write-only is the #1 failure). The reader is job J-3320 (the gated read of this log against the
pre-registered measures M1..M5 of the review, gate: 40 rows in data/chapter_descent_shadow.jsonl since boot). It
reads data/chapter_descent_shadow.jsonl and joins cycle_id to the cycle's output. scripts/chapter_descent_summary.py
prints the row counts, M1 reach inputs, M2 distinctness, M5 loop-safety proxy and the latency from the log so the
read does not start from nothing.

SAFETY. CHAPTER_DESCENT_SHADOW kill switch (module constant; default True = logging on; False returns at once, nothing
is read or written); fail-open (shadow_descent never raises); restart-gated; the module is in core.profile's rebase
list so a named profile writes its own copy.
"""
from __future__ import annotations

import json
import logging
import random
import re
import statistics
import threading
import time
from contextlib import closing
from typing import Any

import numpy as np

from core import profile   # the write fence (D-0179) and the data root

logger = logging.getLogger("nascence.chapter_descent_shadow")

CHAPTER_DESCENT_SHADOW = True        # kill switch: False = shadow_descent returns at once, nothing read or written
RECALL_GIST_MIN_RELEVANCE = 0.25     # mirrors core.orchestrator.RECALL_GIST_MIN_RELEVANCE (a central gist)
TOP_N = 3                            # candidates logged per chapter
NEARDUP_COS = 0.85                   # drop a member this close to any served fragment
BAND = 0.05                          # unwalled control: cosine within +/- BAND of the best candidate
MAX_CHAPTERS_PER_CYCLE = 4
SLOW_MS = 50.0                       # the founder's per-hook budget; a row above it is flagged and logged at INFO
QUERY_HEAD_CHARS = 120

# anchored on profile._DATA so activate_profile() rebases it (core.chapter_descent_shadow is in profile's rebase
# tuple) and guard_path() refuses a non-live process
_LOG = profile._DATA / "chapter_descent_shadow.jsonl"
_APPEND_LOCK = threading.Lock()

_STOP = frozenset(
    "that this with from have what your about which their there would could should these those where when while been "
    "being into than then they them also just like more some such only over very much many how why who whom whose "
    "does did done each other will can may might".split())


def _toks(s: Any) -> set:
    return {w for w in re.findall(r"[a-z]{4,}", (s or "").lower()) if w not in _STOP}


def _lex(row_toks: set, q_toks: set) -> float:
    return round(len(row_toks & q_toks) / max(1, len(q_toks)), 4)


def _median(xs: list) -> float | None:
    return round(float(statistics.median(xs)), 4) if xs else None


def _age_days(ts: Any, now: float) -> float | None:
    try:
        return round((now - float(ts)) / 86400.0, 2)
    except Exception:
        return None


def _append(row: dict) -> None:
    path = profile.guard_path(_LOG)       # fenced (D-0179): a non-live process is refused (swallowed by the caller)
    with _APPEND_LOCK, open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _served_chapters(fragments: Any) -> list:
    out = []
    for f in fragments or ():
        try:
            if getattr(f, "origin", "") == "chapter" and float(getattr(f, "relevance", 0.0) or 0.0) >= RECALL_GIST_MIN_RELEVANCE:
                out.append(f)
        except Exception:
            continue
    out.sort(key=lambda f: float(getattr(f, "relevance", 0.0) or 0.0), reverse=True)
    return out[:MAX_CHAPTERS_PER_CYCLE]


def _served_matrix(conn, served_ids: list, blob_to_vec) -> tuple[list, np.ndarray | None]:
    """(ids that have a usable vector, their matrix) for the served set, one SELECT. Fragments not in the table
    (ephemeral rows) are simply absent."""
    if not served_ids:
        return [], None
    q = ",".join("?" for _ in served_ids)
    rows = conn.execute(f"SELECT fragment_id, embedding FROM memory_fragments WHERE fragment_id IN ({q}) "
                        f"AND embedding IS NOT NULL", list(served_ids)).fetchall()
    ids, vecs = [], []
    for r in rows:
        try:
            v = blob_to_vec(r["embedding"])
            if v.shape[0] == 0:
                continue
            ids.append(r["fragment_id"])
            vecs.append(v)
        except Exception:
            continue
    if not vecs:
        return [], None
    dim = vecs[0].shape[0]
    keep = [(i, v) for i, v in zip(ids, vecs) if v.shape[0] == dim]
    return [i for i, _ in keep], np.stack([v for _, v in keep]).astype(np.float32)


def _describe(conn, fid: str, cos: float, qt: set, now: float, max_cos_to_served: float | None) -> dict | None:
    r = conn.execute("SELECT content, timestamp, origin FROM memory_fragments WHERE fragment_id=?", (fid,)).fetchone()
    if r is None:
        return None
    return {"fragment_id": fid, "origin": r["origin"], "cos": round(float(cos), 4),
            "lex_overlap": _lex(_toks(r["content"]), qt), "age_days": _age_days(r["timestamp"], now),
            "max_cos_to_served": None if max_cos_to_served is None else round(float(max_cos_to_served), 4)}


def _unwalled_control(conn, qv, ref_cos: float, served_set: set, served_mat, cycle_id: str, chapter_id: str,
                      qt: set, now: float) -> dict | None:
    """One random unwalled episodic pool row in the cosine band around the best candidate. Reads the cached pool
    matrix through store.pool_embedding_view() (no new SQL, no second matrix in RAM); None when it is not serving."""
    from core.memory import store as _store
    view = _store.pool_embedding_view()
    if view is None:
        return None
    mat, tups, slots = view["mat"], view["tups"], np.asarray(view["slots"], dtype=np.int64)
    n = min(len(tups), len(slots))
    if n == 0:
        return None
    ok = np.nonzero(slots[:n] >= 0)[0]
    if ok.size == 0:
        return None
    sims = np.asarray(mat @ qv, dtype=np.float32)[slots[ok]]     # matvec on the view, then gather: no 30 MB row copy
    in_band = np.nonzero(np.abs(sims - float(ref_cos)) <= BAND)[0]
    pool = [int(ok[j]) for j in in_band
            if tups[int(ok[j])][2] == "episodic" and tups[int(ok[j])][1] not in served_set]
    if not pool:
        return None
    pick = random.Random(f"{cycle_id}:{chapter_id}:unwalled").choice(pool)
    fid = tups[pick][1]
    vec = np.asarray(mat[int(slots[pick])], dtype=np.float32)
    cos = float(vec @ qv)
    mx = float(np.max(served_mat @ vec)) if served_mat is not None else None
    d = _describe(conn, fid, cos, qt, now, mx)
    if d is not None:
        d["band_ref_cos"] = round(float(ref_cos), 4)
    return d


def _one_chapter(conn, ch, served_ids: list, served_set: set, served_vec_ids: list, served_mat, qv, qt: set,
                 query_text: str, cycle_id: str, input_type: str | None, served_cos_med, served_lex_med,
                 now: float, blob_to_vec) -> dict:
    t0 = time.perf_counter()
    chapter_id = getattr(ch, "fragment_id", "")
    row = {"ts": round(now, 3), "cycle_id": cycle_id, "input_type": input_type, "chapter_id": chapter_id,
           "chapter_level": None, "n_members": 0, "query_head": (query_text or "")[:QUERY_HEAD_CHARS],
           "served_ids": list(served_ids), "served_cos_median": served_cos_med, "served_lex_median": served_lex_med,
           "chapter_relevance": round(float(getattr(ch, "relevance", 0.0) or 0.0), 4),
           "n_dropped_served": 0, "n_dropped_neardup": 0, "candidates": [],
           "control_chapter_member": None, "control_unwalled": None}
    lv = conn.execute("SELECT chapter_level FROM memory_fragments WHERE fragment_id=?", (chapter_id,)).fetchone()
    if lv is not None:
        row["chapter_level"] = lv["chapter_level"]
    # members by chapter_id (idx_chapter), the chapter row itself excluded; vectors only (content is read later
    # for the handful of rows that are logged)
    mem = conn.execute("SELECT fragment_id, embedding FROM memory_fragments WHERE chapter_id=? AND fragment_id<>?",
                       (chapter_id, chapter_id)).fetchall()
    row["n_members"] = len(mem)
    ids, vecs = [], []
    dim = int(qv.shape[0])
    for r in mem:
        if r["embedding"] is None:
            continue
        try:
            v = blob_to_vec(r["embedding"])
        except Exception:
            continue
        if v.shape[0] != dim:
            continue
        ids.append(r["fragment_id"])
        vecs.append(v)
    row["n_members_embedded"] = len(ids)
    if ids:
        E = np.stack(vecs).astype(np.float32)
        cos = E @ qv
        maxsrv = (E @ served_mat.T).max(axis=1) if served_mat is not None else np.full(len(ids), -1.0, dtype=np.float32)
        is_served = np.fromiter((i in served_set for i in ids), dtype=bool, count=len(ids))
        neardup = (maxsrv >= NEARDUP_COS) & ~is_served
        row["n_dropped_served"] = int(is_served.sum())
        row["n_dropped_neardup"] = int(neardup.sum())
        eligible = np.nonzero(~is_served & ~neardup)[0]
        order = eligible[np.argsort(-cos[eligible])]
        top = [int(i) for i in order[:TOP_N]]
        has_served = served_mat is not None

        def mk(i: int) -> dict | None:
            return _describe(conn, ids[i], float(cos[i]), qt, now, float(maxsrv[i]) if has_served else None)

        for i in top:
            d = mk(i)
            if d is not None:
                row["candidates"].append(d)
        topset = set(top)
        rest = [int(i) for i in order if int(i) not in topset]
        ctrl_pool = rest or [int(i) for i in order]
        if ctrl_pool:
            pick = random.Random(f"{cycle_id}:{chapter_id}").choice(ctrl_pool)
            d = mk(pick)
            if d is not None:
                d["also_candidate"] = pick in top
                row["control_chapter_member"] = d
        if row["candidates"]:
            row["control_unwalled"] = _unwalled_control(conn, qv, row["candidates"][0]["cos"], served_set,
                                                        served_mat, cycle_id, chapter_id, qt, now)
    row["ms"] = round((time.perf_counter() - t0) * 1000.0, 2)
    if row["ms"] > SLOW_MS:
        row["slow"] = True
        logger.info("[chapter-descent-shadow] slow hook %.1f ms (chapter %s, %d members)", row["ms"],
                    chapter_id[:8], row["n_members"])
    return row


def shadow_descent(fragments: Any, query_text: str, cycle_id: str, input_type: str | None = None) -> int:
    """OBSERVE-ONLY. Called from Orchestrator._retrieve_memory beside the other recall shadows, in
    asyncio.to_thread, with a snapshot of the served set. Appends one row per served chapter gist to
    data/chapter_descent_shadow.jsonl and returns the number of rows written. Never raises; changes nothing."""
    try:
        if not CHAPTER_DESCENT_SHADOW:
            return 0
        frags = list(fragments or ())
        chapters = _served_chapters(frags)
        if not chapters or not (query_text or "").strip():
            return 0
        from core.memory import store as _store
        qv = _store._embed(query_text)
        if qv is None:
            return 0
        qv = np.asarray(qv, dtype=np.float32)
        qt = _toks(query_text)
        now = time.time()
        served_ids = [getattr(f, "fragment_id", "") for f in frags]
        served_set = set(served_ids)
        served_lex_med = _median([_lex(_toks(getattr(f, "content", "")), qt) for f in frags])
        written = 0
        with closing(_store._connect()) as conn:
            vec_ids, served_mat = _served_matrix(conn, [i for i in served_ids if i], _store._blob_to_vec)
            if served_mat is not None and served_mat.shape[1] != qv.shape[0]:
                vec_ids, served_mat = [], None
            served_cos_med = _median([float(x) for x in (served_mat @ qv)]) if served_mat is not None else None
            for ch in chapters:
                try:
                    row = _one_chapter(conn, ch, served_ids, served_set, vec_ids, served_mat, qv, qt, query_text,
                                       cycle_id, input_type, served_cos_med, served_lex_med, now,
                                       _store._blob_to_vec)
                    _append(row)
                    written += 1
                except Exception as exc:
                    logger.debug("chapter_descent_shadow: chapter %s skipped (non-fatal): %s",
                                 getattr(ch, "fragment_id", "?"), exc)
        return written
    except Exception as exc:
        logger.debug("chapter_descent_shadow skipped (non-fatal): %s", exc)
        return 0
