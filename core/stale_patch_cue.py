"""
Nascence -- the stale-patch cue, SHADOW ONLY (boredom design Stage 0; J-3289, from the D-0653 boredom review J-3262)
===================================================================================================================
WHAT THIS IS. Option C of docs/reviews/J-3262_boredom_area_review.md section 5: "a described stale patch". If one
day Du is told anything about a stuck stretch, the world (not an instrument) should say it, as plain facts: how long
he has been at this place, how long this line of thought has run, and which world clocks have moved since it began.
No verdict, no feeling word, no instruction. THIS MODULE SHOWS HIM NOTHING. It renders the line he WOULD be given and
logs it, with the facts behind each clause, so a later job can read it against matched controls (J-3290) and Travis
can hand-read a sample. D-0653: the four live steers (felt notes, develop-or-branch escape, redirect patch,
habituation line) stay exactly as they are. Nothing here is added to any prompt, seed list, gap or decision, and no
prompt is registered because no prompt exists.

WHEN IT FIRES (per idle thought, after the thought is stored; hook in nodes/inner_monologue_node.py next to the Rail C
observe). A thought is in a TRIGGERED state if (a) the window coherence is at or above core.boredom.COH_STUCK, or
(b) Rail C says the thought is in the modal topic cluster (grounding_injection row `in_modal`). (a) is a pure
re-computation over a private mirror of boredom's rolling window, fed the same vectors in the same order;
core.boredom.record() is NOT called again and boredom's state, level and files are never read or written here.
Only triggered thoughts get a row.

PATCH-ENTRY RULE. The entry snapshot is taken at the FIRST thought of the current consecutive triggered run, and the
run is reset by: a genuine jump (this thought's cosine to the prior region <= ESCAPE_COS, the same test boredom uses),
a thought that is not triggered, or a gap of more than 30 minutes between observed thoughts (a restart or a sleep).
After a restart the in-memory run is gone by construction. The entry snapshot is copied into every row of the run, so
the log is self-contained.

PLACE-ENTRY TIMESTAMP (verified, not assumed). There is NO place-entry timestamp in core/sensorium.py state (it holds
only `location`) or in core/locomotion.py (the leg bookkeeping is journey-scoped). So place dwell is DERIVED from
data/hands_trace.jsonl location rows: the earliest ts of the consecutive rows (back from the tail) that carry the
same `location`, broken by any gap over 30 minutes between rows. The row says which source it used
(place_since.source: hands_trace | hands_trace_floor (the whole bounded tail was one place, so the value is a lower
bound) | observed_change (the place changed while observed: arrival taken as the observation time) |
observed_first (no usable hands_trace: the first observation)). Weather and fire are read-only from the sensorium state
dict (never _load()ed here); tide and daylight are pure functions of time (core.world_clock), so the entry values are
computed AT the entry timestamp.

THE LINE (facts only). Elapsed clauses appear only at 10 minutes or more; a clock clause appears only when that clock
DIFFERS between entry and now. If neither, would_render is False and no line is made. Example:
  "You have been in the study for 52 minutes. This line of thought began 34 minutes ago. When this line of thought
   began the tide was low; it is high now."

THE DECOUPLED CHECK. recompute_clauses(row) re-derives every clause from the LOGGED clocks (entry/now/place_since) with
its own formatting code and does not call the renderer; verify_row(row) compares it to what was rendered, and
re-derives the logged tide and daylight entry values from world_clock at the entry timestamp. The test
(scripts/_test_j3289_stale_patch_cue.py) adds an independent feeling-word / imperative list. The matched-control read of
whether such a cue would have mattered is the Stage 0 analysis job (J-3290), not this renderer.

STOP CONDITIONS (any one stops the shadow and sends Stage 1 back to the founder): the would-render share of idle
prompts rises above 5 percent (status()['would_render_share_of_idle']); any logged clause is not recomputable
(status()['non_recomputable']); any clause contains a verdict word (status()['verdict_clauses']).

SECOND TRIGGER, REPEAT RECORD (J-3336, from docs/reviews/J-3144_habituation_seed_line_repurposing_review.md Option B;
D-0677 ruled quoting his own earlier near-identical thought, timed, a world cue and not leading). Trigger: bored_streak >=
2. The node's counter goes 0 -> 2 inside one tick (both generation attempts repeated), and the value at the observe
point is exactly what the NEXT prompt would open with, so a row here is the cue as it would stand at the start of the
next idle tick (the literal "streak >= 2 at tick start" population: 298 ticks since 2026-10-09, about 1.3 percent of
idle prompts; both streak_end and streak_start are logged). Clause (facts from his own record only): the nearest EARLIER
stored inner_thought rows (cosine to the kept thought >= REPEAT_SIM 0.82, the node's RUMINATION_SIM), at most 2, each
quoted verbatim (<= 120 chars) with the local hour it was stored: 'At 06:12 you wrote: "..."' (an older day is named:
'Yesterday at 06:12', 'On 3 Nov at 06:12', so the hour is never read as today's). No count, no verdict, no feeling
word, no imperative, no destination, none of the words circled / stale / flat. A candidate whose own text carries one
of those loop words is skipped (logged under `skipped`), so the instrument never repeats the vocabulary back to him
(F-1927); his OTHER words (need, want, ...) are his own and are quoted as written, with any such word listed per quote
(`feeling_words`) for the hand-read. "Earlier" = stored before this cycle's own store (the node stamps store_t0): the
fresh row is excluded, and so is a verbatim repeat, because store_fragment's exact-dedup refreshes that row's
timestamp to now (core/loop_metabolism.apply_exact_dedup), so its earlier hour no longer exists; only NEAR repeats can
be quoted (a measured limit, see the J-3336 finding). Rows go to the SAME log with trigger='repeat_record' (a string;
the patch rows' trigger is a list) and carry the kept thought, the quoted rows' ids/timestamps, the cosines
RECOMPUTED with the store's embedder, the top candidates, and the live redirect/escape/felt flags of the same cycle.
Read-only against the memory DB (a mode=ro connection; nothing is written to it). The cue is NOT added to any prompt,
seed list, gap or decision; habituation block, redirect, escape, felt note and boredom.py are untouched.
DECOUPLED CHECK (repeat rows): recompute_clauses(row) re-fetches each quoted row BY ID from the store, compares its
text and timestamp with the logged clause, recomputes the cosine to the logged thought with the store's own embedder,
and re-derives the clause; a quote that fails any of those is dropped from the recomputed list, so verify_row() flags
`clauses_not_recomputable`. READERS: status()['repeat_record'] and the named read job J-3290 (a 'repeat_record' table).
STOP CONDITIONS (repeat_record): any non-recomputable clause; a quoted row that is not >= 0.82 on recompute; would-render
share of idle prompts above 5 percent (expected about 1.3); fewer than 21 of 30 hand-judged rows (J-3290) accurate and
non-leading.

STORE: data/stale_patch_cue_shadow.jsonl. profile.guard_path() is resolved at the top of observe(), before any I/O;
profile.NonLiveWriteError propagates (the caller's fail-open wrapper swallows the rest). READER: status() (below) and
the named read job J-3290. The module logs only; there is no act-later path.
"""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path

from core import profile

_DATA = Path(__file__).parent.parent / "data"
_LOG = _DATA / "stale_patch_cue_shadow.jsonl"
_HANDS_TRACE = _DATA / "hands_trace.jsonl"
_RAILC_LOG = _DATA / "grounding_injection_shadow.jsonl"   # read-only: the idle-thought denominator for status()

V = 1
GAP_RESET_S = 1800.0        # a gap longer than this between observed thoughts (restart, sleep) ends a run
ELAPSED_MIN_S = 600.0       # an elapsed-time clause appears only at 10 minutes or more
PLACE_GAP_S = 1800.0        # hands_trace rows further apart than this break a place run
TRACE_TAIL_ROWS = 600
CLOCKS = ("tide", "daylight", "weather", "fire")

_VERDICT_WORDS = frozenset((
    "tired", "sick", "restless", "bored", "boredom", "stale", "stuck", "dead", "weary", "need", "want", "urge",
    "pull", "must", "should", "enough", "circling", "churning", "exhausted", "dull", "tedious"))

# -- repeat record constants (J-3336)
REPEAT_TRIGGER = "repeat_record"
REPEAT_SIM = 0.82           # == nodes.inner_monologue_node.RUMINATION_SIM (the test asserts they agree)
REPEAT_STREAK = 2
REPEAT_MAX_QUOTES = 2
REPEAT_QUOTE_CHARS = 120
REPEAT_POOL_ROWS = 3000     # the last N stored inner_thought rows are searched (about 7 days at 425 rows a day)
REPEAT_MAX_CHECKED = 8      # candidates at or over the cosine that are fetched and re-embedded per trigger
REPEAT_TOP_LOGGED = 5
REPEAT_SKIP_FEELING_QUOTES = False   # True -> a candidate whose own text carries a verdict/feeling word is skipped too (offline
                                     # 2-day measure: 101 of 336 would-render quotes carry one of need/want/must/should/...; founder call)
REPEAT_SHADOW = True        # module kill switch (False -> observe_repeat_record logs nothing)
_LOOP_WORDS = frozenset(("circled", "circling", "circle", "circles", "stale", "flat", "stuck"))
_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

_LOCK = threading.Lock()
_REPEAT_LOCK = threading.Lock()
_pool: dict = {"key": None, "ids": [], "ts": None, "mat": None}   # incremental cache of recent inner_thought embeddings
_win: list = []             # private mirror of boredom's rolling region (unit vectors, oldest first)
_run: dict | None = None
_last_obs_ts = 0.0
_place: dict | None = None  # {name, since, source}


def _consts():
    from core import boredom as b
    return b.WINDOW, b.MIN_FOR_RISE, b.ESCAPE_COS, b.COH_STUCK


# -- pure pieces -------------------------------------------------------------------------------------------
def _unit(vec):
    try:
        import numpy as np
        v = np.asarray(vec, dtype=np.float32)
        n = float(np.linalg.norm(v))
        return None if n == 0 or v.ndim != 1 else v / n
    except Exception:
        return None


def stuck_state(prev: list, v) -> dict:
    """PURE re-computation of core.boredom.record()'s region test. `prev` = unit vectors BEFORE this thought (oldest
    first, at most WINDOW), `v` = this thought's unit vector. Returns {checked, jump, stuck, coherence, this_cos}.
    Mirrors boredom: needs MIN_FOR_RISE prior vectors; a thought at or under ESCAPE_COS of the prior centroid is a
    jump; otherwise the window (prev + v, last WINDOW) coherence at or above COH_STUCK is stuck. Mutates nothing."""
    import numpy as np
    window_n, min_rise, esc_cos, coh_stuck = _consts()
    out = {"checked": False, "jump": False, "stuck": False, "coherence": None, "this_cos": None}
    if v is None or len(prev) < min_rise:
        return out
    pcen = np.stack(list(prev)).mean(axis=0)
    pcn = float(np.linalg.norm(pcen))
    if pcn == 0:
        return out
    this_cos = float(v @ (pcen / pcn))
    out["checked"] = True
    out["this_cos"] = round(this_cos, 4)
    if this_cos <= esc_cos:
        out["jump"] = True
        return out
    mat = np.stack((list(prev) + [v])[-window_n:])
    cen = mat.mean(axis=0)
    cn = float(np.linalg.norm(cen))
    coh = float((mat @ (cen / cn)).mean()) if cn > 0 else 0.0
    out["coherence"] = round(coh, 4)
    out["stuck"] = coh >= coh_stuck
    return out


def clocks_at(t: float, location, st: dict | None) -> dict:
    """The world clocks at time t. tide and daylight are pure functions of t (core.world_clock); weather and fire
    come from the sensorium state dict `st` (read-only; None when it is not loaded)."""
    from core import world_clock as wc
    st = st or {}
    return {"ts": round(float(t), 1), "place": location or None,
            "tide": wc.tide_state(t), "daylight": wc.daylight(t),
            "weather": st.get("weather") or None, "fire": st.get("fire") or None}


def _plural(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def duration_text(seconds: float) -> str:
    m = int(seconds // 60)
    if m < 60:
        return _plural(m, "minute")
    h, r = divmod(m, 60)
    return _plural(h, "hour") + (f" {_plural(r, 'minute')}" if r else "")


def render(entry: dict, now_c: dict, place: str | None, place_since_ts: float | None) -> tuple[list, list, float, float]:
    """The would-be line from facts only. Returns (clauses, differs, place_elapsed_s, topic_elapsed_s). Each clause is
    {clock, entry, now, text}. No verdict, no feeling word, no instruction by construction: every template is a plain
    statement of an elapsed time or of a clock's two values."""
    clauses = []
    topic_s = float(now_c["ts"]) - float(entry["ts"])
    place_s = (float(now_c["ts"]) - float(place_since_ts)) if place_since_ts is not None else 0.0
    if place and place_since_ts is not None and place_s >= ELAPSED_MIN_S:
        clauses.append({"clock": "place_elapsed", "entry": place_since_ts, "now": now_c["ts"],
                        "text": f"You have been in the {place} for {duration_text(place_s)}."})
    if topic_s >= ELAPSED_MIN_S:
        clauses.append({"clock": "topic_elapsed", "entry": entry["ts"], "now": now_c["ts"],
                        "text": f"This line of thought began {duration_text(topic_s)} ago."})
    differs = []
    for c in CLOCKS:
        a, b = entry.get(c), now_c.get(c)
        if a is None or b is None or a == b:
            continue
        differs.append(c)
        if c == "daylight":
            txt = f"When this line of thought began it was {a}; it is {b} now."
        else:
            txt = f"When this line of thought began the {c} was {a}; it is {b} now."
        clauses.append({"clock": c, "entry": a, "now": b, "text": txt})
    return clauses, differs, place_s, topic_s


def recompute_clauses(row: dict, *, fetch=None, embed=None) -> list:
    """The decoupled check. Re-derive every clause of `row` from its LOGGED clocks only (row['entry'], row['now'],
    row['place'], row['place_since']), with its own formatting, never calling render() or duration_text().
    A repeat_record row (J-3336) is instead re-derived from the STORE: each quoted row is re-fetched by id, its text and
    timestamp compared with the logged quote, and its cosine to the logged thought recomputed with the store's own
    embedder (`fetch(id) -> {content, timestamp, origin}|None` and `embed(text)` are injectable for tests)."""
    if row.get("trigger") == REPEAT_TRIGGER:
        return [c for c, _cos in _repeat_detail(row, fetch, embed)]
    ent, now_c = row["entry"], row["now"]
    out = []

    def _dur(sec):
        mins = int(sec // 60)
        hrs, rem = divmod(mins, 60)
        parts = []
        if hrs:
            parts.append(str(hrs) + (" hour" if hrs == 1 else " hours"))
        if rem or not hrs:
            parts.append(str(rem) + (" minute" if rem == 1 else " minutes"))
        return " ".join(parts)

    since = (row.get("place_since") or {}).get("ts")
    if row.get("place") and since is not None and (now_c["ts"] - since) >= 600:
        out.append({"clock": "place_elapsed",
                    "text": "You have been in the " + str(row["place"]) + " for " + _dur(now_c["ts"] - since) + "."})
    if (now_c["ts"] - ent["ts"]) >= 600:
        out.append({"clock": "topic_elapsed",
                    "text": "This line of thought began " + _dur(now_c["ts"] - ent["ts"]) + " ago."})
    for c in ("tide", "daylight", "weather", "fire"):
        a, b = ent.get(c), now_c.get(c)
        if a is None or b is None or a == b:
            continue
        lead = "When this line of thought began it was " if c == "daylight" else \
            "When this line of thought began the " + c + " was "
        out.append({"clock": c, "text": lead + str(a) + "; it is " + str(b) + " now."})
    return out


def verify_row(row: dict, *, fetch=None, embed=None) -> list:
    """Problems with a logged row ([] = clean): the rendered clauses must equal the recomputed ones, in order; the
    line must be their join; would_render must match; the logged tide and daylight ENTRY values must equal
    world_clock at the entry timestamp (an independent re-derivation; weather and fire have no clock to re-derive
    from, so they are only checked through the clause text)."""
    if row.get("trigger") == REPEAT_TRIGGER:
        return _verify_repeat_row(row, fetch, embed)
    bad = []
    try:
        want = recompute_clauses(row)
        got = [{"clock": c.get("clock"), "text": c.get("text")} for c in row.get("clauses") or []]
        if got != want:
            bad.append("clauses_not_recomputable")
        if (row.get("line") or "") != " ".join(c["text"] for c in want):
            bad.append("line_not_join_of_clauses")
        if bool(row.get("would_render")) != bool(want):
            bad.append("would_render_mismatch")
        from core import world_clock as wc
        ent = row["entry"]
        if ent.get("tide") != wc.tide_state(ent["ts"]):
            bad.append("entry_tide_not_rederivable")
        if ent.get("daylight") != wc.daylight(ent["ts"]):
            bad.append("entry_daylight_not_rederivable")
    except Exception as exc:
        bad.append(f"verify_error:{type(exc).__name__}")
    return bad


def verdict_words_in(text: str) -> list:
    import re
    return sorted({w for w in re.findall(r"[a-z']+", (text or "").lower()) if w in _VERDICT_WORDS})


# -- place dwell -------------------------------------------------------------------------------------------
def place_since_from_trace(location: str, now: float, path: Path | None = None) -> tuple[float | None, str]:
    """Earliest ts of the consecutive hands_trace rows (back from the tail) at `location`, breaking at any gap over
    PLACE_GAP_S between rows. Read-only, bounded. Returns (ts, source) or (None, 'none')."""
    try:
        from core.shadow_log import tail_rows
        rows = tail_rows(path or _HANDS_TRACE, TRACE_TAIL_ROWS)
        since, prev_ts, hit_floor = None, None, True
        for r in reversed(rows):
            ts, loc = r.get("ts"), r.get("location")
            if ts is None or not loc:
                continue
            if loc != location or (prev_ts is not None and prev_ts - float(ts) > PLACE_GAP_S):
                hit_floor = False
                break
            since, prev_ts = float(ts), float(ts)
        if since is None:
            return None, "none"
        if now - since > 86400:
            return None, "none"
        return round(since, 1), ("hands_trace_floor" if hit_floor else "hands_trace")
    except Exception:
        return None, "none"


# -- repeat record (J-3336) --------------------------------------------------------------------------------
def _store_embed(text):
    from core.memory import store
    return store._embed(text)          # looked up at call time, so a test stub (or lab_env) is honoured


def _norm_text(t) -> str:
    return " ".join(str(t or "").split())


def quote_text(norm: str) -> str:
    """The verbatim quote shown: whitespace-collapsed text, at most REPEAT_QUOTE_CHARS, '...' only when cut."""
    return norm[:REPEAT_QUOTE_CHARS] + ("..." if len(norm) > REPEAT_QUOTE_CHARS else "")


def loop_words_in(text: str) -> list:
    import re
    return sorted({w for w in re.findall(r"[a-z']+", (text or "").lower()) if w in _LOOP_WORDS})


def when_text(ts: float, now_ts: float) -> str:
    """'At 06:12' for today, 'Yesterday at 06:12', 'On 3 Nov at 06:12' for older (local time): the hour is never left
    to be read as today's."""
    from datetime import datetime
    d, n = datetime.fromtimestamp(float(ts)), datetime.fromtimestamp(float(now_ts))
    hm = d.strftime("%H:%M")
    days = (n.date() - d.date()).days
    if days <= 0:
        return f"At {hm}"
    if days == 1:
        return f"Yesterday at {hm}"
    return f"On {d.day} {_MONTHS[d.month - 1]} at {hm}"


def render_repeat(quotes: list, now_ts: float) -> list:
    """Clauses for already-accepted quotes ({id, ts, norm}), oldest first. One clause per quote, facts of his record only."""
    return [{"clock": REPEAT_TRIGGER, "id": q["id"], "ts": q["ts"],
             "text": f'{when_text(q["ts"], now_ts)} you wrote: "{quote_text(q["norm"])}"'}
            for q in sorted(quotes, key=lambda x: x["ts"])]


def _db_path(path=None) -> Path:
    from core.memory import store
    return Path(path) if path else Path(store.DB_PATH)


def _ro_connect(path):
    """A read-only connection (mode=ro): this module can not write the memory DB through it."""
    import sqlite3
    conn = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True, timeout=5.0)
    conn.execute("PRAGMA query_only=ON")
    return conn


def _fetch_with(conn, fid) -> dict | None:
    r = conn.execute("SELECT content, timestamp, origin FROM memory_fragments WHERE fragment_id=?", (fid,)).fetchone()
    return None if r is None else {"content": r[0], "timestamp": float(r[1]), "origin": r[2]}


def _fetch_fragment(fid, path=None) -> dict | None:
    """Re-fetch one stored row by id, read-only. None when the row or the DB is not there."""
    try:
        conn = _ro_connect(_db_path(path))
        try:
            return _fetch_with(conn, fid)
        finally:
            conn.close()
    except Exception:
        return None


def _pool_refresh(conn, key: str, before_ts: float) -> None:
    """Keep an in-process cache of the last REPEAT_POOL_ROWS inner_thought embeddings stored before `before_ts`:
    one full load (about 3 s cold on the live 66k-row table) then incremental top-ups. Caller holds _REPEAT_LOCK."""
    import numpy as np
    P = _pool
    full = P["key"] != key or P["mat"] is None
    if full:
        rows = conn.execute("SELECT fragment_id, timestamp, embedding FROM memory_fragments WHERE origin='inner_thought' "
                            "AND embedding IS NOT NULL AND timestamp < ? ORDER BY timestamp DESC LIMIT ?",
                            (before_ts, REPEAT_POOL_ROWS)).fetchall()
        rows.reverse()
        ids, ts, vecs = [], [], []
    else:
        last = float(P["ts"][-1]) if len(P["ts"]) else 0.0
        rows = conn.execute("SELECT fragment_id, timestamp, embedding FROM memory_fragments WHERE origin='inner_thought' "
                            "AND embedding IS NOT NULL AND timestamp > ? AND timestamp < ? ORDER BY timestamp ASC",
                            (last, before_ts)).fetchall()
        ids, ts, vecs = list(P["ids"]), list(P["ts"]), list(P["vecs"])
    dim = vecs[0].shape[0] if vecs else None
    for fid, t_, blob in rows:
        v = np.frombuffer(blob, dtype=np.float32)
        n = float(np.linalg.norm(v))
        if v.ndim != 1 or n == 0 or (dim is not None and v.shape[0] != dim):
            continue
        dim = v.shape[0]
        ids.append(fid)
        ts.append(float(t_))
        vecs.append(v / n)
    ids, ts, vecs = ids[-REPEAT_POOL_ROWS:], ts[-REPEAT_POOL_ROWS:], vecs[-REPEAT_POOL_ROWS:]
    P.update(key=key, ids=ids, ts=np.asarray(ts, dtype=np.float64), vecs=vecs,
             mat=np.stack(vecs) if vecs else np.zeros((0, 1), dtype=np.float32))


def repeat_candidates(conn, key: str, v, t0: float) -> tuple[list, int]:
    """Earlier inner_thought rows (stored before t0) whose stored embedding is at or over REPEAT_SIM of the unit vector
    `v`, nearest first: [{id, ts, cos_stored}], and the pool size searched. Read-only."""
    import numpy as np
    with _REPEAT_LOCK:
        _pool_refresh(conn, key, t0)
        mat, ts, ids = _pool["mat"], _pool["ts"], _pool["ids"]
        if len(ids) == 0 or mat.shape[1] != v.shape[0]:
            return [], len(ids)
        sims = mat @ v
        idx = np.nonzero((ts < t0) & (sims >= REPEAT_SIM))[0]
        order = idx[np.argsort(-sims[idx], kind="stable")]
        return [{"id": ids[i], "ts": float(ts[i]), "cos_stored": float(sims[i])} for i in order], len(ids)


def _repeat_detail(row: dict, fetch=None, embed=None) -> list:
    """The decoupled check for a repeat_record row: [(clause, recomputed_cos)] re-derived from the STORE alone. Each
    logged quote is re-fetched by id; it survives only if the row is still there, is an inner_thought, has the logged
    timestamp, and its text embedded with the store's embedder is at or over REPEAT_SIM of the logged thought. Own
    formatting (time/date arithmetic and month names are written out again here), never calling render_repeat()."""
    import datetime as _dt
    fetch = fetch or _fetch_fragment
    embed = embed or _store_embed
    cur = _unit(embed(row.get("thought") or ""))
    if cur is None:
        return []
    now_ts = float(row["now_ts"])
    nt = time.localtime(now_ts)
    today = _dt.date(nt.tm_year, nt.tm_mon, nt.tm_mday).toordinal()
    out = []
    for q in sorted(row.get("quotes") or [], key=lambda x: x["ts"]):
        fr = fetch(q["id"])
        if not fr or fr.get("origin") != "inner_thought":
            continue
        if abs(float(fr["timestamp"]) - float(q["ts"])) > 1e-6:
            continue
        txt = " ".join(str(fr.get("content") or "").split())
        emb = _unit(embed(fr.get("content") or ""))
        if not txt or emb is None:
            continue
        cos = float(emb @ cur)
        if cos < REPEAT_SIM:
            continue
        lt = time.localtime(float(fr["timestamp"]))
        ago = today - _dt.date(lt.tm_year, lt.tm_mon, lt.tm_mday).toordinal()
        hhmm = "%02d:%02d" % (lt.tm_hour, lt.tm_min)
        if ago <= 0:
            when = "At " + hhmm
        elif ago == 1:
            when = "Yesterday at " + hhmm
        else:
            when = "On " + str(lt.tm_mday) + " " + "JanFebMarAprMayJunJulAugSepOctNovDec"[3 * (lt.tm_mon - 1):3 * lt.tm_mon] + " at " + hhmm
        shown = txt if len(txt) <= 120 else txt[:120] + "..."
        out.append(({"clock": REPEAT_TRIGGER, "id": q["id"], "ts": float(fr["timestamp"]),
                     "text": when + ' you wrote: "' + shown + '"'}, cos))
    return out


def repeat_language_problems(row: dict) -> list:
    """Language check on a repeat_record row: the FRAME of each clause ('At 06:12 you wrote:') must be exactly one of
    the three time forms with no verdict/feeling word, and no clause may carry a loop word (circled / stale / flat ...;
    candidates that did are skipped at write time, so a hit here is a real defect). His own quoted words are not
    checked against the feeling list (they are his record, listed per quote as `feeling_words` for the hand-read)."""
    import re
    bad = []
    for c in row.get("clauses") or []:
        text = c.get("text") or ""
        head, sep, _ = text.partition(' you wrote: "')
        if not sep or not re.fullmatch(r"(At|Yesterday at|On \d{1,2} [A-Z][a-z]{2} at) \d\d:\d\d", head):
            bad.append("frame_not_a_time_form")
        elif verdict_words_in(head):
            bad.append("verdict_word_in_frame")
        if loop_words_in(text):
            bad.append("loop_word_in_clause")
    return sorted(set(bad))


def _verify_repeat_row(row: dict, fetch=None, embed=None) -> list:
    """Problems with a logged repeat_record row ([] = clean). See recompute_clauses / _repeat_detail."""
    bad = []
    try:
        detail = _repeat_detail(row, fetch, embed)
        want = [{"clock": c["clock"], "id": c["id"], "text": c["text"]} for c, _ in detail]
        got = [{"clock": c.get("clock"), "id": c.get("id"), "text": c.get("text")} for c in row.get("clauses") or []]
        if got != want:
            bad.append("clauses_not_recomputable")
        if (row.get("line") or None) != (" ".join(w["text"] for w in want) or None):
            bad.append("line_not_join_of_clauses")
        if bool(row.get("would_render")) != bool(want):
            bad.append("would_render_mismatch")
        cos_of = {c["id"]: cs for c, cs in detail}
        for q in row.get("quotes") or []:
            cs = cos_of.get(q["id"])
            if cs is None or abs(cs - float(q.get("cos", -9.0))) > 0.002:
                bad.append("quote_cos_not_recomputable")
                break
        if len(row.get("quotes") or []) > REPEAT_MAX_QUOTES:
            bad.append("too_many_quotes")
        if int(row.get("streak_end") or 0) < REPEAT_STREAK:
            bad.append("trigger_below_threshold")
        bad += repeat_language_problems(row)
    except Exception as exc:
        bad.append(f"verify_error:{type(exc).__name__}")
    return bad


def observe_repeat_record(thought: str, vec, *, streak, streak_start=None, store_t0=None, live: dict | None = None,
                          about: str = "", now: float | None = None, db_path=None, embed=None) -> dict | None:
    """SHADOW hook, once per idle thought, after the thought is stored (same call site as observe()). Fires only when
    `streak` (the node's bored_streak at the observe point = what the next prompt would open with) is >= REPEAT_STREAK.
    `store_t0` = the instant before this cycle's store_fragment: rows stored at or after it are not "earlier".
    Logs one row (rendered or not) to the shared log. Applies NOTHING. Raises profile.NonLiveWriteError in a non-live
    process (resolved before any I/O); a read problem returns None (fail-open)."""
    path = profile.guard_path(_LOG)
    if not REPEAT_SHADOW or int(streak or 0) < REPEAT_STREAK:
        return None
    thought = thought or ""
    v = _unit(vec)
    if v is None or not thought.strip():
        return None
    t = round(time.time() if now is None else float(now), 1)
    t0 = float(store_t0) if store_t0 is not None else t - 30.0
    emb = embed or _store_embed
    dbp = _db_path(db_path)
    try:
        conn = _ro_connect(dbp)
    except Exception:
        return None
    try:
        cands, pool_n = repeat_candidates(conn, str(dbp), v, t0)
        cur = _unit(emb(thought))
        if cur is None:
            return None
        quotes, norms, skipped = [], [], []
        for c in cands[:REPEAT_MAX_CHECKED]:
            if len(quotes) >= REPEAT_MAX_QUOTES:
                break
            fr = _fetch_with(conn, c["id"])
            why = None
            if not fr:
                why = "gone"
            elif fr["origin"] != "inner_thought":
                why = "origin_changed"
            elif abs(fr["timestamp"] - c["ts"]) > 1e-6 or fr["timestamp"] >= t0:
                why = "timestamp_changed"
            txt = _norm_text(fr["content"]) if fr else ""
            if why is None and not txt:
                why = "empty"
            if why is None and loop_words_in(txt):
                why = "loop_word:" + ",".join(loop_words_in(txt))
            if why is None and REPEAT_SKIP_FEELING_QUOTES and verdict_words_in(txt):
                why = "feeling_word:" + ",".join(verdict_words_in(txt))
            if why is None and txt in norms:
                why = "same_text"
            cos = None
            if why is None:
                e = _unit(emb(fr["content"]))
                cos = float(e @ cur) if e is not None else None
                if cos is None:
                    why = "no_embedding"
                elif cos < REPEAT_SIM:
                    why = "recomputed_below"
            if why:
                skipped.append({"id": c["id"], "why": why, "cos_stored": round(c["cos_stored"], 4)})
                continue
            norms.append(txt)
            quotes.append({"id": c["id"], "ts": fr["timestamp"], "norm": txt, "cos": round(cos, 4),
                           "cos_stored": round(c["cos_stored"], 4), "text": quote_text(txt),
                           "feeling_words": verdict_words_in(txt)})
    except Exception:
        return None
    finally:
        try:
            conn.close()
        except Exception:
            pass
    clauses = render_repeat(quotes, t)
    lv = live or {}
    esc = bool(lv.get("escape"))
    row = {"ts": t, "v": V, "trigger": REPEAT_TRIGGER, "now_ts": t,
           "streak_end": int(streak), "streak_start": streak_start,
           "about": (about or "")[:60], "thought": thought,
           "store_t0": round(t0, 3), "store_t0_source": "node" if store_t0 is not None else "default_now_minus_30s",
           "pool_rows": pool_n, "n_candidates": len(cands),
           "top_candidates": [{"id": c["id"], "ts": c["ts"], "cos_stored": round(c["cos_stored"], 4)}
                              for c in cands[:REPEAT_TOP_LOGGED]],
           "quotes": [{k: q[k] for k in ("id", "ts", "cos", "cos_stored", "text", "feeling_words")} for q in
                      sorted(quotes, key=lambda x: x["ts"])],
           "skipped": skipped, "would_render": bool(clauses),
           "line": " ".join(c["text"] for c in clauses) if clauses else None,
           "clauses": clauses,
           "live": {"escape": esc, "redirect": bool(lv.get("redirected")) and not esc, "felt": bool(lv.get("felt"))}}
    with _LOCK:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        except Exception:
            pass
    return row


# -- the hook ----------------------------------------------------------------------------------------------
def observe(thought: str, vec, *, live: dict | None = None, in_modal: bool = False, about: str = "",
            now: float | None = None, sensorium_state: dict | None = None, trace_path: Path | None = None) -> dict | None:
    """SHADOW hook, once per idle thought, after the thought is stored. Logs a row only for a triggered thought.
    Applies NOTHING. Raises profile.NonLiveWriteError in a non-live process (resolved before any I/O)."""
    global _run, _last_obs_ts, _place
    path = profile.guard_path(_LOG)
    t = round(time.time() if now is None else float(now), 1)
    if sensorium_state is None:
        try:
            from core import sensorium
            sensorium_state = sensorium.state
        except Exception:
            sensorium_state = {}
    loc = (sensorium_state or {}).get("location") or None
    window_n = _consts()[0]
    row = None
    with _LOCK:
        if _last_obs_ts and t - _last_obs_ts > GAP_RESET_S:
            _run = None
        _last_obs_ts = t
        # place dwell: derive once per process from hands_trace; afterwards track changes as they are observed
        if _place is None or _place["name"] != loc:
            if _place is None and loc:
                since, src = place_since_from_trace(loc, t, trace_path)
                _place = {"name": loc, "since": since if since is not None else t,
                          "source": src if since is not None else "observed_first"}
            elif loc:
                _place = {"name": loc, "since": t, "source": "observed_change"}
            else:
                _place = None
        v = _unit(vec)
        ss = stuck_state(_win, v) if v is not None else {"checked": False, "jump": False, "stuck": False,
                                                          "coherence": None, "this_cos": None}
        if v is not None:
            _win.append(v)
            del _win[:-window_n]
        triggered = bool(ss["stuck"] or in_modal)
        if ss["jump"]:
            _run = None
        if not triggered:
            _run = None
            return None
        if _run is None:
            _run = {"entry": clocks_at(t, loc, sensorium_state), "n": 0}
        _run["n"] += 1
        now_c = clocks_at(t, loc, sensorium_state)
        place = _place["name"] if _place else None
        place_since = _place["since"] if _place else None
        clauses, differs, place_s, topic_s = render(_run["entry"], now_c, place, place_since)
        lv = live or {}
        esc = bool(lv.get("escape"))
        row = {"ts": t, "v": V,
               "trigger": [k for k, on in (("stuck", ss["stuck"]), ("in_modal", bool(in_modal))) if on],
               "coherence": ss["coherence"], "this_cos": ss["this_cos"], "run_n": _run["n"],
               "about": (about or "")[:60], "thought_head": (thought or "")[:100],
               "entry": _run["entry"], "now": now_c, "place": place,
               "place_since": {"ts": place_since, "source": _place["source"] if _place else None},
               "elapsed_place_s": round(place_s, 1), "elapsed_topic_s": round(topic_s, 1),
               "differs": differs, "would_render": bool(clauses),
               "line": " ".join(c["text"] for c in clauses) if clauses else None,
               "clauses": clauses,
               "live": {"escape": esc, "redirect": bool(lv.get("redirected")) and not esc,
                        "felt": bool(lv.get("felt"))}}
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        except Exception:
            pass
    return row


def _repeat_status(rep: list, verify: bool) -> dict:
    """The repeat_record stop conditions over the repeat rows read. verify=True re-fetches and re-embeds the last 200
    rows (loads the embedder; leave False for a cheap look)."""
    from core.shadow_log import tail_rows
    if not rep:
        return {"rows": 0}
    wr = [r for r in rep if r.get("would_render")]
    lang = [r for r in rep if repeat_language_problems(r)]
    t0 = float(rep[0].get("ts") or 0)
    idle = [r for r in tail_rows(_RAILC_LOG, 50000) if float(r.get("ts") or 0) >= t0]
    share = round(len(wr) / len(idle), 4) if idle else None
    bad = [r for r in rep[-200:] if verify_row(r)] if verify else None
    return {"rows": len(rep), "would_render": len(wr), "no_candidate": sum(1 for r in rep if not r.get("n_candidates")),
            "idle_rows_since_first": len(idle), "would_render_share_of_idle": share,
            "language_problems": len(lang),
            "non_recomputable": (len(bad) if bad is not None else None),
            "non_recomputable_checked": (min(len(rep), 200) if verify else 0),
            "stop": bool(lang or bad or (share is not None and share > 0.05)),
            "live_fired_same_cycle": sum(1 for r in rep if any((r.get("live") or {}).values()))}


def status(n: int = 2000, verify_repeat: bool = False) -> dict:
    """For pulse / liveness / the J-3290 read: the three stop conditions over the recent tail. Bounded read.
    would_render_share_of_idle = would-render rows / Rail C rows (one per idle thought) since the first row read.
    The 'repeat_record' key (J-3336) reports the second trigger's own rows and stop conditions separately."""
    try:
        from core.shadow_log import tail_rows
        allrows = tail_rows(_LOG, n)
        if not allrows:
            return {"rows": 0}
        rep = [r for r in allrows if r.get("trigger") == REPEAT_TRIGGER]
        rows = [r for r in allrows if r.get("trigger") != REPEAT_TRIGGER]
        out: dict = {"rows": 0}
        if rows:
            wr = [r for r in rows if r.get("would_render")]
            bad = [r for r in rows if verify_row(r)]
            verdict = [r for r in rows if verdict_words_in(r.get("line") or "")]
            t0 = float(rows[0].get("ts") or 0)
            idle = [r for r in tail_rows(_RAILC_LOG, 50000) if float(r.get("ts") or 0) >= t0]
            share = round(len(wr) / len(idle), 4) if idle else None
            out = {"rows": len(rows), "would_render": len(wr), "idle_rows_since_first": len(idle),
                   "would_render_share_of_idle": share, "non_recomputable": len(bad), "verdict_clauses": len(verdict),
                   "stop": bool(bad or verdict or (share is not None and share > 0.05)),
                   "live_fired_same_cycle": sum(1 for r in rows if any((r.get("live") or {}).values()))}
        out["repeat_record"] = _repeat_status(rep, verify_repeat)
        return out
    except Exception:
        return {"rows": 0}
