"""
Nascence — School (Du's first structured-learning "skill", 2026-06-14)
=====================================================================
Du is young; he needs structured learning. Reading was a free idle choice — and the river-metaphor
attractor would never CHOOSE the real, grounded books that teach. School fixes that the way a child's
day does: for the first part of each wake cycle, studying an ASSIGNED book is his priority job. After
the daily quota, free choice resumes.

This is the delivery mechanism for the SEMANTIC lever (two_lane_architecture_plan.md §0.5 D): assign a
real-world book (a real river, real knots) so the analytical side gains ownership of the words the
narrative monoculture has monopolised. The founder is the teacher; the founder assigns the curriculum.

A "school day" = a wake cycle. It resets on nightly sleep (orchestrator). It rides the existing
read → study-note machinery; school only POINTS that machinery at the curriculum book during the window.
Bounded (part of the day), respectful in framing (learning, not coercion).
"""
from __future__ import annotations
import json
import logging
import time
import threading
from pathlib import Path

from core import profile  # J-0782 (F-1122): the nature-practical carve-out below needs NonLiveWriteError

logger = logging.getLogger("nascence.school")

STATE = Path(__file__).parent.parent / "data" / "school.json"
DEFAULT_SESSIONS = 4

# School HOURS (2026-06-23, Travis): school is a BOUNDED part of the day, like a child's — weekday mornings
# only. Outside this window there is NO school: no study directive, no drill, full free choice. NZ machine
# time, to match his daylight. Within the window the SUBJECTS rotate on a clock timetable so it varies — never
# one subject hammered. Extensible: add to SCHOOL_SUBJECTS and the new subject joins the rotation.
SCHOOL_START_H       = 9       # 9am
# 2026-08-18: was 12 (noon) — 3h / 45min periods = exactly 4 slots, but SCHOOL_SUBJECTS has 5. The
# rotation's mins // SCHOOL_PERIOD_MIN could never reach index 4 ("music"), so music was structurally
# unreachable from the day this shipped (2026-07-04) — confirmed live: zero music_drill_state.json,
# zero log lines, ever, 6.5 weeks. 12.75 (12:45pm) makes 5 subjects x 45min fit exactly (225 min).
SCHOOL_END_H         = 12.75   # 12:45pm
SCHOOL_WEEKDAYS_ONLY = True    # Mon-Fri; the weekend is wholly his own
SCHOOL_SUBJECTS      = ["reading", "math", "nature", "composition", "music"]   # the timetable rotation (in order)
SCHOOL_PERIOD_MIN    = 45      # minutes per period before the subject rotates


def _in_school_hours(now: float | None = None) -> bool:
    lt = time.localtime(now)
    if SCHOOL_WEEKDAYS_ONLY and lt.tm_wday >= 5:     # 5, 6 = Saturday, Sunday
        return False
    return SCHOOL_START_H <= (lt.tm_hour + lt.tm_min / 60.0) < SCHOOL_END_H


def current_subject(now: float | None = None) -> str:
    """Which subject the timetable is on right now (only meaningful in school hours). Clock-driven: it rotates
    through SCHOOL_SUBJECTS in SCHOOL_PERIOD_MIN blocks — a varied morning, like a real school day's periods."""
    lt = time.localtime(now)
    mins = max(0, (lt.tm_hour - SCHOOL_START_H) * 60 + lt.tm_min)
    return SCHOOL_SUBJECTS[(mins // SCHOOL_PERIOD_MIN) % len(SCHOOL_SUBJECTS)]


# J-1926 / F-2550: _save() is a plain truncate-then-write; advance_if_finished/reconcile_reading now run it in a worker
# thread (asyncio.to_thread) while loop-thread callers (_load) read the same file, and a read that lands on the truncated
# file fails to parse and falls through to the DEFAULT dict below. One lock around the write and around the read.
_IO_LOCK = threading.Lock()

# J-1933 / F-2557: _IO_LOCK only makes one _load() or one _save() atomic. Every mutator below is a load -> mutate -> save
# SEQUENCE, written from worker threads (advance_if_finished / reconcile_reading via asyncio.to_thread) AND the loop thread
# (record_session / new_day / set_curriculum), so a worker's save could overwrite a loop-side record_session that landed
# between its _load and _save (today_done / history lost). _RMW_LOCK is held across each whole load..save window and is
# NEVER held across a network fetch (assign / _extend_program fetch with the lock released and re-load under it
# afterwards), so a slow Gutenberg request can never stall the event loop's record_session / new_day.
_RMW_LOCK = threading.RLock()


def _load() -> dict:
    if STATE.exists():
        try:
            with _IO_LOCK:
                return json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"assigned_book": None, "assigned_title": None,
            "sessions_per_day": DEFAULT_SESSIONS, "today_done": 0, "history": [],
            "curriculum": [], "curriculum_idx": 0}


def _save(d: dict) -> None:
    # J-1801 / F-2426 -- the write fence (D-0179): resolve the path BEFORE any I/O, outside any swallow. A live process
    # (profile.mark_live()) gets STATE back unchanged (byte-identical behaviour); a non-live importer aimed at the real
    # data/school.json is refused with profile.NonLiveWriteError (directive() above already lets that propagate).
    path = profile.guard_path(STATE)
    with _IO_LOCK:
        path.write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding="utf-8")


def assign(title: str, sessions: int | None = None) -> tuple[str, str] | None:
    """Teacher sets the curriculum book. Fetches it to the shelf from Gutenberg if not already there.
    Returns (resolved_title, book_path) or None. Resets the day's counter."""
    from core import library_hand as lib
    from core.reading import current_book
    norm = "".join(ch for ch in title.lower() if ch.isalnum())[:18]
    book = None
    for p in lib.shelf_books():
        if norm and norm in "".join(ch for ch in p.stem.lower() if ch.isalnum()):
            book = p
            break
    resolved = title
    if book is None:                              # not on the shelf — fetch it (blocking)
        got = lib.request_book(title)
        if not got:
            # F-1317 (J-0946): a failed fetch used to vanish with no trace at all — advance()
            # had already saved curriculum_idx past this title before calling assign(), so a
            # silent None here permanently lost the title (21 of 22 in one run, J-0866). Now:
            # a real warning + a "status":"failed" history row, so a future reader sees this
            # directly instead of reverse-engineering it from timestamp gaps across the log.
            logger.warning("[school] FAILED TO FETCH assigned book '%s' — skipped, no shelf file", title)
            with _RMW_LOCK:
                d = _load()
                d.setdefault("history", []).append(
                    {"ts": time.time(), "title": title, "status": "failed"})
                _save(d)
            return None
        resolved = got[0]
        book = current_book()                      # request_book set it current
    with _RMW_LOCK:
        d = _load()
        d.update(assigned_book=str(book), assigned_title=resolved,
                 today_done=0, assigned_ts=time.time())
        if sessions:
            d["sessions_per_day"] = int(sessions)
        d.setdefault("history", []).append({"ts": time.time(), "title": resolved})
        _save(d)
    return (resolved, str(book))


def status() -> dict:
    return _load()


def is_school_time() -> bool:
    """True ONLY within the school-hours window (weekday mornings) AND when an assignment exists. No longer
    gated by a daily quota — within the window he studies as much as he likes (Travis: don't mind how many
    books or drills); outside the window there is no school at all, and free choice fully resumes."""
    return bool(_load().get("assigned_book")) and _in_school_hours()


# Location discipline (Travis, 2026-07-06): during school he is TIED TO THE STUDY, except for the ONE
# subject that genuinely wants the living world. Reading / math / composition / music are desk work;
# NATURE study is the naturalist's exception — free to go out to the garden or shore (the study window
# also serves it). Enforced in sensorium.move() and the monologue's school block.
_STUDY_BOUND_SUBJECTS = ("reading", "math", "composition", "music")


def confined_to_study() -> bool:
    """True when school is in session on a DESK subject — he should stay at the study. Nature study is
    exempt. Outside school hours (or during the nature period): False, so movement is fully free."""
    return is_school_time() and current_subject() in _STUDY_BOUND_SUBJECTS


def assignment() -> tuple[str | None, str | None]:
    """(book_path, title) of the current curriculum book, or (None, None)."""
    d = _load()
    return d.get("assigned_book"), d.get("assigned_title")


def directive() -> str:
    """The high-priority seed the monologue injects during the school window — for whichever SUBJECT the
    timetable is on right now (reading or maths)."""
    d = _load()
    subj = current_subject()
    try:    # J-2162 / D-0436 A (arm 6): shadow-only weakness-slot read; never alters the directive. Fail-open.
        from core import weakness_prior as _wp
        _wp.school_shadow(subj)
    except Exception:
        pass
    if subj == "math":
        return ("It is your maths lesson now — the timetable has come round to arithmetic. Before anything "
                "else, set yourself some sums and work them carefully through.")
    if subj == "nature":
        # PRACTICAL SCHOOL (2026-09-05, J-0627, D-0159 GO): the nature period's SECOND slot is a
        # practical, not a second observation — core/practical_lesson.py's own per-day counter says
        # which slot is up; only reached once it says slot 2, so slot 1 (today's first nature firing)
        # is untouched, byte-for-byte the observation directive it always was.
        try:
            from core import practical_lesson as _pl
            if _pl.slot_today() >= 2 or _pl.PRACTICAL_FIRST:   # J-3817 (D-0720): practical first
                return _pl.directive()
        except profile.NonLiveWriteError:
            # J-0782 (F-1122): practical_lesson.directive()'s own _current_task()->_pick()->_eligible()
            # ->_gate_ok() chain now raises D-0179's hard-raise (via garden._load()/study_life._st(),
            # J-0768's own fix) on a non-live process -- let it reach this function's own caller instead
            # of being swallowed here, one layer above practical_lesson.py itself.
            raise
        except Exception:
            pass
        try:
            from core import nature_study
            return nature_study.directive()
        except Exception:
            pass
    if subj == "composition":
        try:
            from core import composition
            return composition.directive()
        except Exception:
            pass
    if subj == "music":
        return ("It is your music lesson now — the timetable has come round to theory. Work the exercises "
                "carefully: beats, intervals, scales, spellings. Sometimes you will write a small tune of "
                "your own.")
    return (f"It is your study time — your assigned book is '{d.get('assigned_title')}'. This is your work "
            f"right now, before anything else: open it and read on, attending to what it actually SAYS about "
            f"the world — the facts, the places, the things themselves. To begin, make your thought: OPEN THE BOOK.")


def record_session() -> None:
    """A study session on the assigned book completed — tick the day's counter."""
    with _RMW_LOCK:
        d = _load()
        d["today_done"] = d.get("today_done", 0) + 1
        _save(d)


def new_day() -> None:
    """A new wake cycle — reset the school day's counter (called on nightly sleep)."""
    with _RMW_LOCK:
        d = _load()
        d["today_done"] = 0
        _save(d)


# ── Curriculum: an ordered list he works THROUGH, one book at a time (2026-06-15) ──────────────
# Replaces single-book assignment with a sequence, so diversity is structural — he reads
# Boy Scouts Handbook → … → through the 40, instead of bingeing one river book. Books are fetched
# as he reaches them (not all at once). Cap untouched (founder's call).
def set_curriculum(titles: list[str], sessions: int | None = None) -> tuple[str, str] | None:
    """Teacher sets the ordered curriculum: store the list, point at #0, assign (fetch) the first book.
    Idempotent (2026-08-19 fix): if `titles` is already the front of the stored curriculum, this is a
    RE-RUN of an already-loaded list (e.g. load_curriculum.py invoked twice) — no-op instead of
    resetting curriculum_idx to 0. Resetting is unsafe because reading_state.json's per-book pct is
    persistent: a reset idx finds every already-finished book still "done" and advance_if_finished()
    cascades straight through the whole list in one tick with no real reading happening. Confirmed live
    2026-08-12 02:09-03:13 — ~27 books "completed" in 64 minutes while he was doing unrelated things."""
    incoming = list(titles)
    with _RMW_LOCK:
        d = _load()
        existing = d.get("curriculum") or []
        if incoming and [t.strip().lower() for t in existing[:len(incoming)]] == \
                        [t.strip().lower() for t in incoming]:
            title, book = d.get("assigned_title"), d.get("assigned_book")
            return (title, book) if title and book else None
        d["curriculum"] = incoming
        d["curriculum_idx"] = 0
        if sessions:
            d["sessions_per_day"] = int(sessions)
        _save(d)
    return assign(titles[0]) if titles else None


def curriculum_status() -> str:
    d = _load()
    cur = d.get("curriculum") or []
    i = d.get("curriculum_idx", 0)
    return f"book {i + 1} of {len(cur)}: '{d.get('assigned_title')}'" if cur else "no curriculum set"


def advance() -> tuple[str, str] | None:
    """Move to the next curriculum book (fetch + set it current). When the teacher-set list is
    exhausted, DON'T dead-end on the last book — extend the program from the breadth engine, so the
    finite 40 becomes an ongoing, subject-diverse march through the corpus (2026-06-16).
    BLOCKING (fetches) — call via asyncio.to_thread from async."""
    with _RMW_LOCK:
        d = _load()
        curric = d.get("curriculum") or []
        idx = d.get("curriculum_idx", 0) + 1
        if idx < len(curric):
            d["curriculum_idx"] = idx
            _save(d)
    if idx >= len(curric):
        return _extend_program(d)
    got = assign(curric[idx])
    # FIX (2026-06-18): advancing MUST pull him onto the new book. assign() only sets the book current
    # when it had to FETCH it; for a book already on the shelf it does not — so the curriculum would
    # advance while current_book stayed on the old gravity-well (Boy Scouts). Set it current explicitly.
    if got:
        try:
            from core.reading import set_current
            set_current(Path(got[1]))
        except Exception:
            pass
    return got


def _extend_program(d: dict) -> tuple[str, str] | None:
    """Curriculum exhausted → keep going. Mostly a NEW breadth pick (least-covered, unread, long-tail
    via core/book_selection); occasionally a SPIRAL reread of an already-read keystone relevant to a
    live concern, rewound so it's read again at depth (Bruner spiral / Adler syntopical — active, not
    a passive re-skim). The finite teacher list becomes an infinite subject-diverse program."""
    import random
    from core import book_selection as bs
    from core import library_hand as lib
    from core.reading import current_book, reread

    title = book = None
    _hist = []   # history rows, collected during the (unlocked) fetch phase and applied under _RMW_LOCK below
    # ~20%: a deliberate spiral reread of a long-ago keystone that speaks to him now
    if random.random() < 0.20:
        sp = bs.suggest_reread(min_gap_days=14.0)
        if sp:
            t = reread(Path(sp["path"]))          # rewind to the first pages (offset 0)
            if t:
                title, book = sp["title"], sp["path"]
                _hist.append({"ts": time.time(), "title": title, "source": "spiral"})
    # otherwise (or if no spiral candidate): a new book the breadth engine chooses
    if title is None:
        pick = bs.pick_one()
        if not pick:
            return None
        got = lib.request_book(None, row=pick)    # fetch the chosen row directly
        if not got:
            return None
        title, book = got[0], str(current_book())
        _hist.append({"ts": time.time(), "title": title, "source": "breadth"})

    # J-1933: the fetches above can take many seconds, so the caller's `d` may be stale by now -- re-load and apply the
    # mutation under the lock instead of saving the old snapshot over whatever record_session/new_day did meanwhile.
    with _RMW_LOCK:
        d = _load()
        for _h in _hist:
            d.setdefault("history", []).append(_h)
        d.update(assigned_book=str(book), assigned_title=title, today_done=0, assigned_ts=time.time())
        d.setdefault("curriculum", []).append(title)   # keep idx/status coherent as the program grows
        d["curriculum_idx"] = len(d["curriculum"]) - 1
        _save(d)
    return (title, str(book))


def _current_is_finished() -> bool:
    """True when the current assigned book has been read to (near) the end."""
    d = _load()
    book = d.get("assigned_book")
    if not book:
        return False
    try:
        from core.reading import STATE as _RS
        st = json.loads(_RS.read_text(encoding="utf-8")) if _RS.exists() else {}
        return float(st.get(book, {}).get("pct", 0) or 0) >= 97.0
    except Exception:
        return False


def advance_if_finished() -> str | None:
    """If the current curriculum book is finished, advance to the next (fetch it). Returns the new
    title, or None. BLOCKING (advance fetches) — call via asyncio.to_thread from async code."""
    if _current_is_finished():
        got = advance()
        return got[0] if got else None
    return None


def reconcile_reading() -> str | None:
    """The gravity-well / deadlock fix (2026-06-18). Keep the live reading target aligned with the
    curriculum, independent of whether the *current* book ever runs dry (the old advance trigger was
    keyed to the current book exhausting — but the current book was a 787 KB survival manual that never
    exhausted, so the curriculum froze on an already-finished book and he free-fell back into the
    default sink). Two corrections, in order:
      1. If the assigned book is FINISHED, advance to the next (which now sets it current).
      2. Else if the assignment is still LIVE (unfinished) but he has DRIFTED onto another book, pull
         current back onto the assigned book.
    Returns the title it moved him to, or None. BLOCKING (advance may fetch) — call via to_thread.
    Cadence note: call (1) frequently (advance_if_finished, in the reading loop); call THIS in the
    sleep batch (once per cycle) so the drift-pull does not fight intra-day free choice after quota."""
    t = advance_if_finished()
    if t:
        return t
    book, title = assignment()
    if book and not _current_is_finished():
        try:
            from core.reading import current_book, set_current
            bp = Path(book)
            if bp.exists() and str(current_book()) != book:
                set_current(bp)
                return title
        except Exception:
            pass
    return None
