"""
Nascence — Grounded Learning (the SWS-declarative consolidation, 2026-06-16)
===========================================================================
He reads enormously but nothing metabolises the intake into understanding (the sleep CHAPTERS consolidate
the SELF-loop only; reading/study are excluded). This is the missing slow-wave declarative pass: each sleep,
the reading since the last pass is distilled into durable UNDERSTANDING notes — the gist + the connections
(the neocortical-schema analog, McClelland CLS), not a summary of passages.

REWORKED 2026-11-05 (J-3181, D-0568, folds J-3072; findings F-3779..F-3783). It used to take the newest 24 of
a median 60 new passages of ALL books mixed, cut them at 5,000 characters mid-item, and then mark everything
up to "now" as consumed, so a note could fuse two books and a long reading stretch was represented by its last
16 passages. Now: new fragments are grouped BY BOOK; one bounded sample per book (that book's new study notes
as context first, then the reading its study notes do not already cover); at most _MAX_NOTES notes per sleep;
a per-book watermark advances only to the newest fragment actually walked (fed, or skipped as already
covered), so nothing is marked consumed that the model did not see; the label is the book; items are cut at
word boundaries and the log says how many reached the model. The 'research' (dictionary look-up) origin is no
longer fed: a look-up belongs to no book, and it was the usual source of two-topic fusion.

FIREWALLED: this is WORLD knowledge (DOING), NEVER identity (BEING) — a SEPARATE track from the self/becoming
chapters (it is NOT added to chapters.CHAPTERABLE_ORIGINS). Stored origin='understanding', layer='semantic'
(distilled, not episodic — so the episodic prune cap never touches it). A book needs enough reading its study
notes do not already cover. A synthesis is a CROSSING (reading→understanding) → mints ONE light point per
sleep (feeds the balance sprint; unchanged by the rework, however many notes a sleep writes).

Frozen-model honesty: "understanding" here = a recallable, organised ARTIFACT (his own structured take), not
weight-baked knowledge — which is exactly where his knowledge lives.
"""
from __future__ import annotations
import json
import re
import time
from pathlib import Path

_STATE = Path(__file__).parent.parent / "data" / "grounded_learning_state.json"
_LOG   = Path(__file__).parent.parent / "data" / "grounded_learning_log.jsonl"
# J-3181: every attempt (stored, waiting, covered, rejected, duplicate, call failed) plus one summary row per sleep;
# read by scripts/grounded_learning_read.py, the D-0568 one-week check. _LOG keeps its old meaning: stored notes only.
_ATTEMPT_LOG = Path(__file__).parent.parent / "data" / "grounded_learning_attempts.jsonl"

_MIN_READ  = 3     # a book needs at least this many NEW reading fragments its study notes do not cover (was: 5 of anything)
_READ_MAX  = 10    # reading fragments fed per note (a bounded sample of ONE book)
_STUDY_MAX = 3     # that book's newest new study notes, fed first as context (they are notes, not material to digest)
_MAX_NOTES = 2     # notes written per sleep (D-0568 left "N" open; tunable). Reading arrives faster than this digests it: see _EXPIRE
_READ_CUT  = 300   # characters of one reading fragment, cut on a word boundary
_STUDY_CUT = 450   # characters of one study note once its '[My study note: ...]' header is stripped
_BUDGET    = 5000  # the old material[:5000]: worst case now 3*450 + 10*300 + bullets < 5,000, so no item is ever cut by it
_SCAN      = 4000  # most new reading/study rows read per sleep (oldest first)
_WAIT_MAX  = 3 * 86400    # a book with fewer than _MIN_READ uncovered fragments waits this long, then is fed anyway
_EXPIRE    = 4 * 86400    # a fragment still unfed after this long is dropped from the queue AND COUNTED (logged), never silently
_COVER_SIM = 0.85  # fallback for core.study_note._REVISE_SIM, the study-note duplicate bar


def _study_sim() -> float:
    """The study-note duplicate bar, read from core/study_note.py so there is one number (D-0568: 'use the 0.85
    bar already in study_note.py'). Lazy so this module keeps its no-import-at-load convention."""
    try:
        from core.study_note import _REVISE_SIM
        return float(_REVISE_SIM)
    except Exception:
        return _COVER_SIM


def _load_state() -> dict:
    """{'last_ts': float, 'books': {book_key: watermark}}. The old file held only last_ts and still loads."""
    try:
        d = json.loads(_STATE.read_text(encoding="utf-8"))
        return {"last_ts": float(d.get("last_ts", 0.0) or 0.0),
                "books": {str(k): float(v) for k, v in (d.get("books") or {}).items()}}
    except Exception:
        return {"last_ts": 0.0, "books": {}}


def _save_state(state: dict) -> None:
    try:
        _STATE.write_text(json.dumps({"last_ts": state["last_ts"], "books": state["books"]}), encoding="utf-8")
    except Exception:
        pass


def _last_ts() -> float:
    return _load_state()["last_ts"]


_READ_TITLE  = re.compile(r"^\[From '(.*?)'(?:, sitting \d+)?\]")
_STUDY_TITLE = re.compile(r"· on '(.*?)' · subject:")
_STUDY_HEAD  = re.compile(r"^\[My study note:.*?\bsubject:[^\]]*\]\s*")
_BAD_OPENING = re.compile(r"^\W*(?:the|this)\s+(?:text|excerpt|passages?|article)\b", re.I)


def _book_of(origin: str, content: str) -> str | None:
    """The book a reading fragment ('[From 'T'] ...') or a study note ('[My study note: 'N' · on 'T' · subject: S]')
    belongs to, or None. Study notes carry the title cut at 50 characters, reading fragments the whole title."""
    c = (content or "").lstrip()
    m = (_STUDY_TITLE.search(c[:400]) if origin == "study" else _READ_TITLE.match(c))
    return m.group(1).strip() if m and m.group(1).strip() else None


def _book_key(title: str) -> str:
    return " ".join((title or "").split()).casefold()[:50]


def _topic(material: str) -> str:
    """Most frequent book named in a block of material. Recognises the reading marker, the old 'on:' form AND the
    study-note header ('· on 'BOOK' · subject:') that it used to miss (F-3781: 29 of 505 labels fell back to
    'my recent reading'). consolidate() now labels from the group's book directly; this stays for text-only callers."""
    titles = (re.findall(r"\[From '([^']+)'", material) + re.findall(r"on:\s*([^\]\.]+)", material)
              + re.findall(r"· on '(.*?)' · subject:", material))
    titles = [t.strip() for t in titles if t.strip()]
    return max(set(titles), key=titles.count) if titles else "my recent reading"


def _smart_cut(s: str, n: int = 50) -> str:
    """Truncate to at most n chars WITHOUT cutting a word in half (F-1724/D-0256, 2026-09-23, J-1232):
    backtrack to the last space at or before the cut, so a newly-stored tag never becomes a word
    FRAGMENT that a later, untruncated occurrence of that same word would then fail to match under
    core/essay_lesson.py's own _cites_this_book word-boundary test. FORWARD-ONLY — only changes what
    gets written from here on; cannot and does not touch any already-stored fragment (permanent once
    written). Kept as a local duplicate of essay_lesson.py's identical helper rather than imported, so
    this module stays independent of essay_lesson (matches this file's existing no-cross-import
    convention). Falls back to the hard cut when there's no space to back up to."""
    s = s or ""
    if len(s) <= n:
        return s
    cut = s.rfind(" ", 0, n)
    return s[:cut] if cut > 0 else s[:n]


def _reject_reason(raw) -> str | None:
    """Why a model answer must not be stored, or None. A non-string (the model returned an object for the key and
    str() would store its repr: F-3779, 61 stored notes), too short, a dict/list-looking string, or an opening
    that is the 'The text/excerpt/passage ... discusses' summary the prompt forbids (F-3781: 43 percent of notes)."""
    if not isinstance(raw, str):
        return "not_prose"
    t = raw.strip()
    if len(t) < 60:
        return "too_short"
    if t[0] in "{[":
        return "not_prose"
    if _BAD_OPENING.match(t):
        return "summary_opening"
    return None


def _log_attempt(row: dict) -> None:
    try:
        with open(_ATTEMPT_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _group_new(rows, state: dict, now: float) -> tuple[dict, int, int]:
    """Group new rows by book, dropping what a book's watermark already covers and what has waited past _EXPIRE.
    Returns ({key: {'book', 'items'}} with items oldest-first, n_unlabelled, n_expired). A row that names no book
    cannot be grouped; it is counted, not fed."""
    groups: dict = {}
    n_unlabelled = n_expired = 0
    cutoff = now - _EXPIRE
    for r in rows:
        title = _book_of(r["origin"], r["content"])
        if not title:
            n_unlabelled += 1
            continue
        key = _book_key(title)
        ts = float(r["timestamp"])
        if ts <= state["books"].get(key, state["last_ts"]):
            continue
        if ts < cutoff:
            n_expired += 1
            continue
        g = groups.setdefault(key, {"book": title, "items": []})
        g["items"].append(r)
    return groups, n_unlabelled, n_expired


def _study_vectors(conn, book: str):
    """[(vector, encounter_id)] of every stored study note on this book (new or old), newest first."""
    from core.memory.store import _blob_to_vec
    out = []
    needle = f"· on '{book[:50]}' ·"
    for r in conn.execute("SELECT embedding, encounter_id FROM memory_fragments WHERE origin='study' "
                          "AND embedding IS NOT NULL AND instr(content, ?) > 0 "
                          "ORDER BY timestamp DESC LIMIT 200", (needle,)).fetchall():
        v = _blob_to_vec(r["embedding"])
        if v is not None:
            out.append((v, r["encounter_id"]))
    return out


def _item_text(r) -> str:
    text = " ".join((r["content"] or "").split())
    if r["origin"] == "study":
        return _smart_cut(_STUDY_HEAD.sub("", text), _STUDY_CUT)
    return _smart_cut(_READ_TITLE.sub("", text).strip(), _READ_CUT)


def _walk(items, study_vecs, sim: float) -> dict:
    """Walk one book's new fragments oldest-first and decide what is fed. Reading a study note already covers is
    skipped (consumed, not fed): same encounter, or cosine to a stored study note of the book >= sim. Study notes
    are context: the newest _STUDY_MAX are fed, older ones are passed over (they are notes already). The walk stops
    once _READ_MAX reading fragments are taken, so `walked_to` is a contiguous prefix and nothing older than it is
    left unfed. Returns the study/reading rows fed, counts, and the timestamp consumed up to (None if none walked)."""
    from core.memory.store import _blob_to_vec, _cosine
    enc_ids = {e for _, e in study_vecs if e}
    study_all, read_fed, covered = [], [], 0
    walked_to = None
    for r in items:
        if r["origin"] == "study":
            study_all.append(r)
            walked_to = float(r["timestamp"])
            continue
        v = _blob_to_vec(r["embedding"]) if r["embedding"] is not None else None
        is_cov = bool(r["encounter_id"]) and r["encounter_id"] in enc_ids
        if not is_cov and v is not None:
            is_cov = any(_cosine(v, sv) >= sim for sv, _ in study_vecs)
        if is_cov:
            covered += 1
            walked_to = float(r["timestamp"])
            continue
        if len(read_fed) >= _READ_MAX:
            break
        read_fed.append(r)
        walked_to = float(r["timestamp"])
    study_fed = study_all[-_STUDY_MAX:]
    return {"study": study_fed, "reading": read_fed, "covered": covered, "walked_to": walked_to,
            "study_passed": len(study_all) - len(study_fed), "full": len(read_fed) >= _READ_MAX}


def _build_material(study, reading) -> tuple[str, int]:
    """'- item' lines, study notes first. Whole items only: if the budget would be exceeded the trailing items are
    dropped, never cut mid-word. Returns (material, number of items that reached the model)."""
    lines, used = [], 0
    for r in list(study) + list(reading):
        line = "- " + _item_text(r)
        if used + len(line) + 1 > _BUDGET:
            break
        lines.append(line)
        used += len(line) + 1
    return "\n".join(lines), len(lines)


_SYS = ("/no_think\nYou have read a great deal. Consolidate it into UNDERSTANDING — NOT a summary of "
        "passages, but what you now GRASP: the gist, the key facts, and how they connect. Say only what the "
        "passages state; do not join unrelated passages. Organised understanding of the WORLD (the things "
        "themselves, never about yourself). 4-8 sentences, plain and clear. "
        "Output ONLY a JSON object: {\"understanding\": \"...\"}")


async def consolidate(call_json, base_urls) -> str | None:
    """The slow-wave declarative pass — called once per sleep, beside chapter formation. Gathers the NEW reading
    since the last pass, groups it by book, and for up to _MAX_NOTES books distils one organised UNDERSTANDING note
    each (origin='understanding', semantic); mints one light point per sleep. Returns the first note's text, or
    None if nothing was written. Best-effort."""
    from core.memory.store import _connect, _embed, _cosine, store_fragment, store_light_event
    now = time.time()
    state = _load_state()
    if state["last_ts"] <= 0:
        state["last_ts"] = now - 86400    # no state yet: start from the last day, never replay the whole shelf
    try:
        with _connect() as conn:
            rows = conn.execute(
                "SELECT fragment_id, content, origin, timestamp, embedding, encounter_id FROM memory_fragments "
                "WHERE origin IN ('reading','study') AND timestamp > ? ORDER BY timestamp ASC LIMIT ?",
                (state["last_ts"], _SCAN)).fetchall()
    except Exception:
        return None
    if not rows:
        return None
    groups, n_unlabelled, n_expired = _group_new(rows, state, now)
    order = sorted(groups, key=lambda k: float(groups[k]["items"][0]["timestamp"]))
    sim = _study_sim()
    first_text, notes, attempted, light_done, hub_down = None, 0, 0, False, False
    for key in order:
        if attempted >= _MAX_NOTES or hub_down:
            break
        g = groups[key]
        book = g["book"]
        try:
            with _connect() as conn:
                svecs = _study_vectors(conn, book)
        except Exception:
            continue
        w = _walk(g["items"], svecs, sim)
        if w["walked_to"] is None:
            continue
        row = {"ts": time.time(), "book": book[:80], "n_study_fed": len(w["study"]), "n_read_fed": len(w["reading"]),
               "n_covered": w["covered"], "n_study_passed": w["study_passed"]}
        if not w["reading"]:
            # Nothing uncovered to digest: what was new was reading his study notes already cover, and/or study notes
            # (context, not material). Consumed; no model call. (Never leave them pending: they would hold the floor.)
            state["books"][key] = w["walked_to"]
            _save_state(state)
            _log_attempt({**row, "outcome": "covered", "consumed_to": w["walked_to"]})
            continue
        oldest = float(g["items"][0]["timestamp"])
        if len(w["reading"]) < _MIN_READ and not w["full"] and now - oldest < _WAIT_MAX:
            _log_attempt({**row, "outcome": "waiting"})      # too little uncovered reading yet: stays pending, not consumed
            continue
        material, n_fed = _build_material(w["study"], w["reading"])
        attempted += 1
        row["n_sources"] = n_fed                             # items that REACHED the model (was the SELECT size)
        text, reason = None, None
        for attempt in (0, 1):                               # one immediate retry on a refused answer, never a later one
            try:
                data = await call_json(base_urls, _SYS,
                                       f"From your recent reading of '{_smart_cut(book)}' and your notes on it:\n{material}",
                                       max_tokens=800, temperature=0.4 if attempt == 0 else 0.6)
            except Exception:
                reason, hub_down = "call_failed", True
                break
            raw = data.get("understanding") if isinstance(data, dict) else None
            reason = _reject_reason(raw)
            if reason is None:
                text = raw.strip()
                break
        if reason in ("call_failed", "too_short"):
            # The hub gave nothing usable. Not a verdict on the passages: nothing consumed, same offer next sleep.
            _log_attempt({**row, "outcome": "call_failed" if reason == "call_failed" else "no_answer"})
            continue
        row["consumed_to"] = w["walked_to"]
        if text is None:
            # Fed twice, refused twice (not prose / 'The text ...' opening): they were seen, so they are consumed.
            state["books"][key] = w["walked_to"]
            _save_state(state)
            _log_attempt({**row, "outcome": "rejected:" + str(reason)})
            continue
        try:
            tv = _embed(text)
            dup = bool(tv is not None and any(_cosine(tv, sv) >= sim for sv, _ in svecs))
        except Exception:
            dup = False
        if dup:
            # A restatement of his own study note adds nothing (F-3782: 2 of 18 notes were above the duplicate bar).
            state["books"][key] = w["walked_to"]
            _save_state(state)
            _log_attempt({**row, "outcome": "dup_study"})
            continue
        try:
            from core import mood as _mood
            store_fragment(content=f"[Understanding — from '{_smart_cut(book)}'] {text}",
                           layer="semantic", relevance=0.9, importance=0.9,
                           keywords=["understanding", "knowledge", book.lower()[:40]],
                           origin="understanding", emotion_embedding=_mood.current_vec(),
                           valence=_mood.current_valence(), felt=_mood.current_felt())
            if not light_done:
                store_light_event(cycle_id="sleep", raw_input=f"(consolidated understanding: {book[:50]})",
                                  integrated_content=text[:400], source="understanding")
                light_done = True
        except Exception:
            _log_attempt({**row, "outcome": "store_failed"})   # not consumed: offered again next sleep
            continue
        state["books"][key] = w["walked_to"]
        _save_state(state)
        try:
            with open(_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps({"ts": time.time(), "topic": book[:80], "n_sources": n_fed,
                                    "n_study": len(w["study"]), "n_read": len(w["reading"]),
                                    "n_covered": w["covered"], "understanding": text[:300]}, ensure_ascii=False) + "\n")
        except Exception:
            pass
        _log_attempt({**row, "outcome": "stored"})
        notes += 1
        first_text = first_text or text
    # The global floor: everything at or below it is consumed. It stops short of the oldest still-pending fragment
    # (a book waiting for more reading, a book past this sleep's note budget), so none of those is ever skipped.
    scanned_max = float(rows[-1]["timestamp"])
    pend = [float(it["timestamp"]) for k, g in groups.items() for it in g["items"]
            if float(it["timestamp"]) > state["books"].get(k, state["last_ts"])]
    new_last = min(scanned_max, min(pend) - 1e-6) if pend else scanned_max
    state["last_ts"] = max(state["last_ts"], new_last)
    state["books"] = {k: v for k, v in state["books"].items() if v > state["last_ts"]}
    _save_state(state)
    _log_attempt({"ts": time.time(), "sleep": True, "new_rows": len(rows), "books": len(groups),
                  "unlabelled": n_unlabelled, "expired": n_expired, "attempted": attempted, "notes": notes,
                  "pending_frags": len(pend), "last_ts": state["last_ts"]})
    return first_text
