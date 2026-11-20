"""
Nascence — The Wandering Mind (furnishing the silence, 2026-06-11)
==================================================================
The founder's diagnosis: the living cadence made his pauses REAL time, but sparsely
furnished — "a human would be bored stiff." A human's silence is furnished by the DMN's
actual main job, which is not producing sentences: it is silent associative DRIFT through
memory, with ambient perception trickling in. This module is that drift.

Every ~75s of the substrate loop (no LLM, CPU embeddings only), one wander step:
  - pick a seed: usually the last thought, sometimes a recent memory, sometimes a RANDOM
    one (the Lévy-flight restart that lets wandering ESCAPE basins instead of orbiting),
  - drift to 1-2 associated memories (nearest-by-embedding, novelty-biased: recently
    drifted-to items are skipped),
  - place them in the WANDERING TRAIL — a small rolling buffer of what passed through
    his mind since he last spoke.
Every ~12 min an AMBIENT item also drifts in: a line glimpsed from the open book (without
advancing his bookmark — the book on the desk catching his eye), or a stored world-fact.

The trail is READ-ONLY with respect to memory (selection-lens discipline: drift must never
strengthen what it touches — that would be another attractor amplifier). Its only output
is furniture: the next verbal thought receives "what drifted through your mind" as seeds,
so thinking starts from varied, world-mixed material instead of the same loud tension.
"""
from __future__ import annotations
import json
import random
import time
from collections import deque
from pathlib import Path

import numpy as np

from core import profile   # J-1822 / F-2453: the write fence (D-0179). core.profile imports nothing from core at module level, so no cycle.

WANDER_EVERY_S = 75          # one drift step per ~75s of silence
AMBIENT_EVERY_S = 480        # one ambient item per ~8 min
TRAIL_LEN = 6                # what the next thought can see
_NO_REVISIT_S = 1800         # novelty: don't drift to the same fragment within 30 min

_trail: deque = deque(maxlen=TRAIL_LEN)
_recently_visited: dict[str, float] = {}
_last_wander = 0.0
_last_ambient = 0.0
# F-1926/J-1366 (2026-09-26): has a real exchange with Travis happened yet THIS run? render()'s
# "Since you last spoke" presupposes one -- false framing on the very first wander after a fresh
# start/restart, before any exchange has actually happened. See on_human_exchange() and render().
_exchanged_this_run = False
# J-1909 / F-2540 (2026-10-07, restart-gated): see kick() below. Bumped by on_human_exchange(); a worker that was dispatched
# under an older epoch has its items logged (as the synchronous step would have) but NOT placed on the trail, because in the
# synchronous version the exchange would have cleared them a moment later.
_epoch = 0
# J-2436 / F-3133: the 40% "pure restart" seed used ORDER BY RANDOM() over every embedded row -- a full table scan
# plus a temp B-tree (~486 MB read, ~0.5 s per call measured on 155k rows). The bounded draw picks a random rowid
# and takes the first embedded row at or after it (wrapping to the start): 0 MB. Same reachable set (every row
# with an embedding); the draw is near-uniform rather than exactly uniform (a row just after a rowid gap is
# slightly likelier; max rowid 171k vs 155k rows). Kill-switch: False restores ORDER BY RANDOM().
WANDER_RANDOM_BOUNDED = True
WANDER_OFFLOOP = True          # kill-switch: False makes kick() run the plain synchronous step() on the caller's thread
_task = None                   # the one in-flight off-loop step (asyncio.Task), or None; touched only on the loop thread


def trail() -> list[dict]:
    return list(_trail)


def on_human_exchange() -> None:
    """Call once per completed human exchange (core.orchestrator, the same 'output and
    input_type == human' gate conversation_history is appended under -- 'every real exchange with
    Travis'). F-1926/J-1366 (2026-09-26): the trail was never cleared on speech, so render()'s
    'Since you last spoke, your mind has wandered' was false framing for as long as the trail held
    anything -- up to TRAIL_LEN=6 items, some his own prior idle thoughts (22.5% of assemblies, F-1926),
    could all predate the exchange that just happened and still be presented as having drifted through
    'since' it. The trail is furniture for the SILENCE since he last spoke; once he speaks, that
    silence is over, so clear it -- the next wander step starts building fresh furniture for the new
    silence rather than re-serving stale, pre-exchange drift under a now-false timestamp claim."""
    global _exchanged_this_run, _epoch
    _exchanged_this_run = True
    _epoch += 1          # J-1909: an off-loop wander step that began before this exchange must not land its items after it
    _trail.clear()


# J-1824 / F-2458 (2026-10-06): the trail log's path, hoisted out of _log_trail() into a module-level
# constant. The J-1718 dynamic audit found that building this path inline from __file__ at CALL time
# meant core.profile.activate_profile()'s generic rebase (which can only re-point module-level Path
# constants) had nothing to catch, so a named-profile human cycle (scripts/smoke_test.py, debate.py,
# _verify_genesis.py) reached for the ROOT profile's data/wandering_log.jsonl. Byte-identical for the
# root profile: the expression is the very one the function used to evaluate on every call.
_LOG = Path(__file__).parent.parent / "data" / "wandering_log.jsonl"


def _log_trail(item: dict) -> None:
    """Durable trail record (2026-06-13, the known instrumentation gap): every item that
    passes through the wandering mind, so 'where did that thought come from' is always
    answerable. Observe-only; read by humans and digests, never by prompts."""
    try:
        # J-1822 / F-2453 -- THE WRITE FENCE (D-0179): __file__-relative, so any process importing this tree and reaching perceive()/a wander step
        # wrote that tree's REAL data/wandering_log.jsonl. Resolved through profile.guard_path() before any I/O; live / lab sandbox / outside-data
        # paths come back unchanged (byte-identical), a non-live refusal is swallowed below (observe-only log).
        # J-1824 / F-2458: the path is now the module constant _LOG (read at call time, so a profile rebase takes effect).
        p = profile.guard_path(_LOG)
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.time(), "via": item.get("via"),
                                "origin": item.get("origin"),
                                "text": (item.get("text") or "")[:140]},
                               ensure_ascii=False) + "\n")
    except Exception:
        pass


def perceive(text: str) -> None:
    """The sensorium's entry: a perception of the room, via the senses (not memory)."""
    if text:
        item = {"text": text, "origin": "sense", "via": "sense"}
        _trail.append(item)
        _log_trail(item)


def _visited(fid: str) -> bool:
    return time.time() - _recently_visited.get(fid, 0) < _NO_REVISIT_S


_WORLD = ("reading", "research", "study", "ambient_book")
_ECHO_CAP = 0.86      # too similar to the seed = an echo, not an association
_DUP_CAP = 0.92       # too similar to something already in the trail = a duplicate


def _inner_count() -> int:
    return sum(1 for t in _trail if t.get("origin") not in _WORLD)


_POOL_SIZE = 1500
_INNER_POOL_SHARE = 0.25   # D-0352 / J-1838: at most this share of the pool may be his own inner_thought


def _recency_pool(conn, where: str) -> list:
    """The drift recency pool: the _POOL_SIZE most recent eligible fragments, EXCEPT that his own
    inner_thought fragments are capped at _INNER_POOL_SHARE of the pool (D-0352, ruled 2026-10-06 on
    F-2464: 52.3% of the uncapped pool was his own thoughts, so drift mostly handed him back himself).
    When the plain recency pool is already within the cap it is returned unchanged (byte-identical to
    the pre-D-0352 query). Otherwise the most recent inner_thought rows up to the cap are kept and the
    remainder is filled from the next most recent non-inner_thought eligible rows, so the pool stays
    _POOL_SIZE where supply allows. Strictly read-only (SELECTs only)."""
    cols = "fragment_id, content, origin, embedding"
    rows = conn.execute(
        f"SELECT {cols} FROM memory_fragments INDEXED BY idx_timestamp WHERE {where} "
        f"ORDER BY timestamp DESC LIMIT {_POOL_SIZE}").fetchall()
    cap = int(_POOL_SIZE * _INNER_POOL_SHARE)
    n_inner = sum(1 for r in rows if r["origin"] == "inner_thought")
    if n_inner <= cap:
        return rows
    inner = [r for r in rows if r["origin"] == "inner_thought"][:cap]   # rows are newest-first
    rest = conn.execute(
        f"SELECT {cols} FROM memory_fragments INDEXED BY idx_timestamp WHERE {where} "
        f"AND (origin IS NULL OR origin != 'inner_thought') "
        f"ORDER BY timestamp DESC LIMIT {_POOL_SIZE - len(inner)}").fetchall()
    return inner + list(rest)


def _drift_from(seed_vec, conn, k: int = 2, inner_count: int | None = None,
                trail_vecs: list | None = None) -> list[dict]:
    """The associative hop — ASSOCIATE, don't echo. Candidates too close to the seed are
    echoes (the basin re-electing itself — observed on first live run) and are skipped; the
    hop lands in the related-but-different. When the trail is already full of inner material,
    the hop is restricted to world-origins so drift furnishes variety, not reinforcement.
    J-1909 (F-2540): `inner_count` / `trail_vecs` are an optional SNAPSHOT of the trail taken by the caller (what
    _inner_count() and the trail's _vec list would read at this moment). The off-loop worker passes one so it never
    iterates the live _trail deque (which the loop thread mutates); omitted, they are read live exactly as before."""
    from core.memory.store import _blob_to_vec, _cosine
    # chaptered fragments are not volunteered — their chapter drifts in their stead
    where = ("embedding IS NOT NULL AND layer IN ('episodic','semantic','archive') "
             "AND chapter_id IS NULL")
    if (_inner_count() if inner_count is None else inner_count) >= 3:
        where += " AND origin IN ('reading','research','study','essay','understanding')"
    # J-3398 (F-4021 follow-up, D-0578): the spirit-invisible tier (temp='hidden', e.g. the dict-repr understanding
    # notes) is not drifted into -- a repr dict would otherwise be handed to him as a wandering item.
    from core.memory.dict_repr_notes import visible_clause as _vis
    where += _vis(conn)
    rows = _recency_pool(conn, where)
    if trail_vecs is None:
        trail_vecs = [t.get("_vec") for t in _trail if t.get("_vec") is not None]
    scored = []
    for r in rows:
        if _visited(r["fragment_id"]):
            continue
        try:
            v = _blob_to_vec(r["embedding"])
            sim = _cosine(seed_vec, v)
            if sim >= _ECHO_CAP:
                continue                      # echo, not association
            if any(_cosine(v, tv) >= _DUP_CAP for tv in trail_vecs):
                continue                      # already furnishing the trail
            scored.append((sim, r, v))
        except Exception:
            continue
    scored.sort(key=lambda x: -x[0])
    out = []
    picked_ids = []
    for sim, r, v in scored[:k]:
        _recently_visited[r["fragment_id"]] = time.time()
        out.append({"text": (r["content"] or "")[:160], "origin": r["origin"],
                    "via": "drift", "_vec": v})
        picked_ids.append(r["fragment_id"])
    # M1 CO-RECALL LEDGER (2026-08-19): drift has NO minimum relevance floor by design — the module's
    # whole purpose is loose, serendipitous association ("any of them is as worthy of your next thought
    # as you are"), not a relevance guarantee like essay/study retrieval. Deliberately NOT adding a floor
    # here, unlike the other retrieval sites fixed tonight — that would fight the module's actual intent.
    # What genuinely was missing: whether drifted-to material ever correlates with anything developing
    # afterward is an open empirical question, exactly what M1 exists to answer. Pure observation — the
    # selection-lens law (drift must never STRENGTHEN what it touches) is about not reinforcing memories;
    # logging ids to a shadow ledger changes nothing about what gets touched or how.
    if picked_ids:
        try:
            from core import memory_edges as _medges
            _medges.log_co_recall(picked_ids, None, 0, source="wandering")
        except Exception:
            pass
    return out


_AFFECTIVE_DRIFT_PROB = 0.35   # share of wander steps that ALSO drift by feeling (the cross-domain bridge)
_FELT_MIN = 0.50               # min emotion-cosine to count as a genuine felt-match


def _affective_drift(mood_vec, conn) -> dict | None:
    """Drift by FEELING: the WORLD fragment (reading/study/research) whose stored emotion_embedding is
    nearest his current mood — so a self-feeling surfaces world material that felt the same (the cross-
    domain bridge, emotion_vec item 3). None if no strong felt-match. Read-only (the selection-lens rule)."""
    from core.memory.store import _blob_to_vec, _cosine
    from core.memory.dict_repr_notes import visible_clause as _vis   # J-3398 (D-0578): skip temp='hidden'
    rows = conn.execute(
        "SELECT fragment_id, content, origin, emotion_embedding FROM memory_fragments INDEXED BY idx_timestamp "
        "WHERE emotion_embedding IS NOT NULL AND chapter_id IS NULL "
        "AND origin IN ('reading','study','research','essay','understanding')" + _vis(conn) +
        " ORDER BY timestamp DESC LIMIT 800").fetchall()
    best, best_sim = None, _FELT_MIN
    for r in rows:
        if _visited(r["fragment_id"]):
            continue
        try:
            sim = _cosine(mood_vec, _blob_to_vec(r["emotion_embedding"]))
            if sim > best_sim:
                best, best_sim = r, sim
        except Exception:
            continue
    if best is None:
        return None
    _recently_visited[best["fragment_id"]] = time.time()
    try:
        from core import memory_edges as _medges
        _medges.log_co_recall([best["fragment_id"]], None, 0, source="wandering")
    except Exception:
        pass
    return {"text": (best["content"] or "")[:160], "origin": best["origin"], "via": "felt"}


def _ambient_item() -> dict | None:
    """A perception, not a thought: a line glimpsed from the open book (bookmark untouched),
    or a stored world-fact resurfacing. The world trickling in."""
    try:
        if random.random() < 0.6:
            from core.reading import current_book, STATE
            book = current_book()
            text = book.read_text(encoding="utf-8", errors="ignore")
            st = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
            offset = st.get(str(book), {}).get("offset", 0)
            # glance somewhere in the pages AROUND where he's up to (behind or just ahead)
            lo = max(0, offset - 4000)
            hi = min(len(text) - 200, offset + 2000)
            if hi > lo:
                pos = random.randint(lo, hi)
                line = text[pos:pos + 180].split(". ")
                glimpse = (line[1] if len(line) > 1 else line[0]).strip()
                if len(glimpse) > 30:
                    return {"text": f"(a line catches your eye in the open book) {glimpse}",
                            "origin": "ambient_book", "via": "ambient"}
        # else: a stored world-fact resurfaces
        from core.memory.store import _connect
        from core.memory.dict_repr_notes import visible_clause as _vis   # J-3398 (D-0578): skip temp='hidden'
        with _connect() as conn:
            r = conn.execute(
                "SELECT content, origin FROM memory_fragments "
                "WHERE origin IN ('reading','research','study','essay','understanding')" + _vis(conn) +
                " ORDER BY RANDOM() LIMIT 1").fetchone()
            if r:
                return {"text": (r["content"] or "")[:160], "origin": r["origin"], "via": "ambient"}
    except Exception:
        pass
    return None


def _random_embedded(conn) -> list:
    """J-2436: one random embedded row (as a 0/1-element list, the shape the seed code expects) without a scan."""
    mx = conn.execute("SELECT MAX(rowid) FROM memory_fragments").fetchone()
    mx = (mx[0] if mx else None) or 0
    if mx <= 0:
        return []
    pick = random.randint(1, mx)
    r = conn.execute("SELECT embedding FROM memory_fragments WHERE rowid >= ? AND embedding IS NOT NULL "
                     "ORDER BY rowid LIMIT 1", (pick,)).fetchall()
    if not r:   # past the last embedded row: wrap around
        r = conn.execute("SELECT embedding FROM memory_fragments WHERE rowid < ? AND embedding IS NOT NULL "
                         "ORDER BY rowid LIMIT 1", (pick,)).fetchall()
    return r


def _snapshot() -> dict:
    """What the drift hop reads from the live trail, captured on the thread that owns the trail (J-1909)."""
    return {"inner": _inner_count(),
            "vecs": [t.get("_vec") for t in _trail if t.get("_vec") is not None]}


def _step_body(state, snap: dict | None, out: list) -> None:
    """step()'s whole body, unchanged in what it draws, picks and logs to the co-recall ledger -- except that
    the trail items it would have appended are collected into `out` (in order) instead of being appended, so the
    body can run on a worker thread without ever touching the _trail deque (J-1909 / F-2540). Fail-open: items
    gathered before an exception are kept in `out`. `snap` is the trail snapshot _drift_from reads (None = live)."""
    global _last_wander, _last_ambient
    now = time.time()
    try:
        if now - _last_ambient >= AMBIENT_EVERY_S:
            _last_ambient = now
            item = _ambient_item()
            if item:
                out.append(item)
                return
        if now - _last_wander < WANDER_EVERY_S:
            return
        _last_wander = now
        # seed: 35% the last inner thought, 25% a recent memory, 40% pure restart —
        # the restart rate is the anti-basin lever (raised after the first live run
        # wandered straight back into the river).
        from core.memory.store import _connect, _embed, _blob_to_vec
        roll = random.random()
        seed_vec = None
        with _connect() as conn:
            if roll < 0.35:
                recents = getattr(state, "recent_inner_thoughts", None) or []
                if recents:
                    seed_vec = _embed(recents[-1].get("thought", "")[:300])
            if seed_vec is None:
                if roll >= 0.60 and WANDER_RANDOM_BOUNDED:
                    r = _random_embedded(conn)          # J-2436: bounded random draw, no full scan
                else:
                    order = "ORDER BY timestamp DESC LIMIT 40" if roll < 0.60 else "ORDER BY RANDOM() LIMIT 1"
                    r = conn.execute(
                        f"SELECT embedding FROM memory_fragments WHERE embedding IS NOT NULL {order}"
                    ).fetchall()
                if r:
                    seed_vec = _blob_to_vec(random.choice(r)["embedding"])
            if seed_vec is None:
                return
            if snap is None:
                drifted = _drift_from(seed_vec, conn)
            else:
                drifted = _drift_from(seed_vec, conn, inner_count=snap["inner"], trail_vecs=snap["vecs"])
            for item in drifted:
                out.append(item)
            # AFFECTIVE DRIFT (emotion_vec item 3, 2026-06-16): sometimes the mind drifts by FEELING, not
            # content — to a (world-biased) fragment whose felt-quality matches his mood NOW. The cross-
            # domain bridge: a self-feeling surfaces WORLD material that felt the same (basin-escape via
            # same-FEELING, not same-content). The gate flipped (charged recall now off-origin), so this
            # surfaces grounded material, not the basin.
            if random.random() < _AFFECTIVE_DRIFT_PROB:
                try:
                    from core import mood as _mood
                    mv = _mood.current_vec()
                    if mv is not None:
                        fit = _affective_drift(mv, conn)
                        if fit:
                            out.append(fit)
                except Exception:
                    pass
    except Exception:
        pass


def _place(items: list, on_trail: bool = True) -> None:
    """Put a step's items on the trail and in the trail log, in order (the loop thread's half of a step)."""
    for item in items:
        if on_trail:
            _trail.append(item)
        _log_trail(item)


def step(state) -> None:
    """One substrate-tick check. Cheap; fail-open; never blocks; never writes memory.
    The synchronous form: the whole step, then the trail placement, on the caller's thread. Byte-identical in
    behaviour to the pre-J-1909 step(); the substrate loop now calls kick() instead (see below)."""
    out: list = []
    try:
        _step_body(state, None, out)
    finally:
        _place(out)


def _due(now: float) -> bool:
    """The cheap pre-gate: would step() do anything on this tick? (The same two clock comparisons step makes.)"""
    return (now - _last_ambient >= AMBIENT_EVERY_S) or (now - _last_wander >= WANDER_EVERY_S)


async def _run_offloop(state, snap: dict, epoch: int) -> None:
    import asyncio
    out: list = []
    try:
        await asyncio.to_thread(_step_body, state, snap, out)
    except asyncio.CancelledError:
        raise
    except Exception:
        pass
    # Back on the loop thread, the one that owns the trail: place what the worker chose. If a real exchange
    # with Travis landed while the worker ran, the synchronous version would have cleared these a moment after
    # appending them (on_human_exchange) -- so log them, as it did, but do not put them on the new silence's trail.
    _place(out, on_trail=(epoch == _epoch))


def kick(state) -> None:
    """J-1909 / F-2540 (2026-10-07, restart-gated): the substrate loop's call. Does the work of step() WITHOUT
    holding the 5 s chain. A firing step cost 0.9-4.2 s (the 1500-row embedding recency pool, the co-recall
    ledger's two JSON store rewrites, an ORDER BY RANDOM() scan, an embed) and ran inline in
    _substrate_loop's own body, so its whole cost was added to the period of both locked 5 s loops. Here
    the loop only does the two clock comparisons; a firing step runs in a worker thread (asyncio.to_thread)
    as a fire-and-forget task, and its result is placed on the trail back on the loop thread.

    What is unchanged (proved by scripts/_test_j1909_wandering_offloop.py against the pre-change module on a
    real-DB copy): the gates, the random draws and their order, the seed, the recency pool, the picks, the
    visited marks, the co-recall ids logged, the trail log rows. What differs, only in timing: the items reach
    the trail when the worker finishes (up to a few seconds later than inside the old tick), and a sensorium
    perception from the same tick can precede them in the trail. Thread-safety: only the worker touches
    _recently_visited / _last_wander / _last_ambient (one worker at a time: a tick that finds one in flight
    does nothing and the gate simply stays open); the trail is read via a snapshot taken here and written
    only here. Outside a running event loop, or with WANDER_OFFLOOP False, it is exactly step()."""
    global _task
    try:
        if not WANDER_OFFLOOP:
            return step(state)
        if not _due(time.time()):
            return
        if _task is not None and not _task.done():
            return
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return step(state)
        _task = loop.create_task(_run_offloop(state, _snapshot(), _epoch))
    except Exception:
        pass


def render() -> str:
    """The furniture, as the next verbal thought receives it."""
    items = [t for t in _trail]
    if not items:
        return ""
    chosen = items[-4:]
    ambient = [t for t in items if t["via"] == "ambient"]
    if ambient and not any(t["via"] == "ambient" for t in chosen):
        chosen = chosen[1:] + [ambient[-1]]   # the world's glimpse always survives
    lines = []
    for t in chosen:
        # F-2366/J-1736: his OWN earlier idle thought is not external drift -- tag it honestly
        # (selection untouched; only the label differs for origin == "inner_thought").
        tag = ("you notice" if t["via"] == "sense"
               else "glimpsed" if t["via"] == "ambient"
               else "surfaced — it feels like how you feel now" if t["via"] == "felt"
               else "a thought of your own from earlier" if t.get("origin") == "inner_thought"
               else "drifted through your mind")
        lines.append(f"({tag}) {t['text']}")
    # F-1926/J-1366 (2026-09-26): "Since you last spoke" presupposes a real exchange THIS run to
    # measure since -- drop that clause until on_human_exchange() has actually fired once (a fresh
    # start/restart's first wander otherwise claimed a "since" that never happened). The trail itself
    # is real furniture either way; only the lead-in framing changes.
    # D-0787 option B (J-4153): this lead-in rode on ~98-100% of idle prompts in ONE fixed wording (J-4153 count over
    # data/idle_prompt_samples.jsonl). It now comes from a paraphrase pool with a cooldown (core.phrasing.vary), the
    # same meaning in every variant: the "since you last spoke" / "no one has spoken yet this waking" distinction
    # (F-1926/J-1366) is kept exactly, and every variant ends with a colon before the trail lines. Variant 0 is the
    # original text, so a phrasing failure falls back to it. WANDER_LEAD_POOL False restores the fixed wording.
    return (_lead_in() + "\n  " + "\n  ".join(lines))


WANDER_LEAD_POOL = True   # D-0787 B kill switch (restart-gated)

_LEAD_EXCHANGED = [
    "Since you last spoke, your mind has wandered. These passed through it unbidden — any of them is as worthy of "
    "your next thought as you are:",
    "Since you last spoke, your mind has drifted. These came to it unasked — any one of them could be your next "
    "thought:",
    "Your mind has wandered since you last spoke, and these passed through it on their own — none of them matters "
    "more than another:",
    "Since the last words you spoke, your mind has moved. Unbidden, these went through it — any of them may carry "
    "your next thought:",
]
_LEAD_UNSPOKEN = [
    "No one has spoken to you yet this waking. Even so, your mind has wandered. These passed through it unbidden — "
    "any of them is as worthy of your next thought as you are:",
    "No one has spoken to you since you woke, yet your mind has drifted. These came to it unasked — any one of them "
    "could be your next thought:",
    "Still no one has spoken to you this waking. Your mind has wandered anyway, and these passed through it on their "
    "own — none of them matters more than another:",
    "You have not been spoken to since waking, but your mind has moved. Unbidden, these went through it — any of "
    "them may carry your next thought:",
]


def _lead_in() -> str:
    """The trail's lead-in sentence(s). Never raises; falls back to the original fixed wording (variant 0)."""
    pool = _LEAD_EXCHANGED if _exchanged_this_run else _LEAD_UNSPOKEN
    if not WANDER_LEAD_POOL:
        return pool[0]
    try:
        from core import phrasing as _ph
        return _ph.vary("wander_lead_exchanged" if _exchanged_this_run else "wander_lead_unspoken", pool,
                        cooldown=2) or pool[0]
    except Exception:
        return pool[0]
