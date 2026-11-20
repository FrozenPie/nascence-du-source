"""Opener diversity for the idle thought (D-0787 option D, J-4153).

WHY: F-1927 found the idle stream formulaic at the OPENER level (40-51% of idle thoughts share their first three
words with another thought written the same day). D-0368 A+E fixed the affective vocabulary leak but not this:
F-4805 re-read same-day first-3-word reuse at 46% before and 48-56% after (threshold 30%). J-4153's own count over
the 14 days to 2026-11-20 is 54%, led by "I watch the" (632), "I trace the" (202), "I hold the" (130). The founder
ruled D-0787: build option D (opener diversity) and option B (phrasing pools).

WHAT: this module keeps a per-process tally of the first three words of each idle thought stored today
(origin=inner_thought only; system-written sentences and short mechanical replies such as "OPEN THE BOOK" are never
counted). Before each idle thought, `seed_part_opener_diversity()` returns ONE seed line naming the openings already
worn today (used twice or more, most-used first) plus the last couple used, and asks for this thought to begin some
other way. The frame wording comes from a core.phrasing pool with a cooldown (option B), so the request itself is not
one fixed sentence repeated thousands of times. With nothing worn yet, or under MIN_TODAY thoughts today, it returns
"" and the prompt is unchanged.

The tally survives a restart: on the first call of a local day in a process it reads today's inner_thought rows
from the memory DB READ-ONLY (sqlite mode=ro; never writes) and counts them, then counts each new thought as
`after_thought_opener()` is called just after the store.

WIRING: two one-line calls from InnerMonologueNode._think (frozen function, D-0878): the seed part next to the other
late seed parts, the after-thought next to the inner_thought store. Both never raise.

FLAG: OPENER_DIVERSITY (module constant, restart-gated). False = no seed line, the tally still counts.
DEFEATER (D-0787): revisit if same-day opener reuse falls under 30% without D, or if a two-week re-read after this
is live still shows it above 30%.
"""
from __future__ import annotations

import collections
import logging
import re
import threading
import time

logger = logging.getLogger(__name__)

OPENER_DIVERSITY = True     # D-0787 D: the seed line is served. Restart-gated.
OPENER_WORDS = 3            # F-1927 / F-4805 measure first-three-word reuse
MIN_TODAY = 6               # fewer idle thoughts today than this: say nothing yet
MIN_COUNT = 2               # an opening is "worn" once it has begun two thoughts today
MAX_WORN = 4                # name at most this many worn openings (most-used first)
RECENT_N = 2                # also name the last few openings used, worn or not
MIN_THOUGHT_WORDS = 6       # shorter replies (mechanical tokens, "OPEN THE BOOK") are never counted
FRAME_COOLDOWN = 3          # core.phrasing cooldown for the frame pool
SEED_ROW_LIMIT = 5000       # a day has ~150-1700 idle thoughts (J-4153 count); cap the restart read

_DB_PATH_OVERRIDE = None    # tests / labs: a temp DB path, or a path that does not exist to skip the read

_WORD = re.compile(r"[a-z']+")
_lock = threading.Lock()
_day = None                 # local date (y, m, d) the tally belongs to
_counts: "collections.Counter" = collections.Counter()
_display: dict = {}         # opener key -> how it was written, for the seed line
_recent: "collections.deque" = collections.deque(maxlen=8)

_FRAMES = [
    "You have already begun thoughts today with {openers}. Let this one begin some other way.",
    "Today's thoughts have already opened with {openers}. Start this one somewhere new.",
    "Today your thoughts have often opened with {openers}. Find a different first word for this one.",
    "Already used to open today's thoughts: {openers}. Let this one open differently.",
    "Your thoughts today keep starting with {openers}. Begin this one elsewhere.",
]


def opener_key(text: str, n: int = OPENER_WORDS) -> str:
    """The first `n` words, lowercased (the F-4805 measure). "" if the text has fewer than n words."""
    try:
        w = _WORD.findall((text or "").lower())
        return " ".join(w[:n]) if len(w) >= n else ""
    except Exception:
        return ""


def _display_of(text: str, n: int = OPENER_WORDS) -> str:
    """The opening as he wrote it (first n whitespace tokens, edge punctuation stripped)."""
    try:
        toks = [t.strip("\"'*_()[]:;,.!?—–-") for t in (text or "").split()]
        toks = [t for t in toks if t][:n]
        return " ".join(toks)
    except Exception:
        return ""


def _countable(text: str) -> bool:
    try:
        words = (text or "").split()
        if len(words) < MIN_THOUGHT_WORDS:
            return False
        head = " ".join(words[:OPENER_WORDS])
        if head.isupper():                      # a mechanical routing token, never steer away from it
            return False
        return bool(opener_key(text))
    except Exception:
        return False


def _day_of(now: float):
    lt = time.localtime(now)
    return (lt.tm_year, lt.tm_mon, lt.tm_mday)


def _db_path():
    if _DB_PATH_OVERRIDE is not None:
        return _DB_PATH_OVERRIDE
    from core.memory import store as _store
    return _store.DB_PATH


def _add(text: str) -> None:
    k = opener_key(text)
    if not k:
        return
    _counts[k] += 1
    d = _display_of(text)
    if d:
        _display[k] = d
    _recent.append(k)


def _seed_from_store(now: float) -> int:
    """Count today's stored inner_thought rows, READ-ONLY. Returns rows counted; 0 on any failure."""
    try:
        import sqlite3
        from pathlib import Path
        p = Path(str(_db_path()))
        if not p.exists():
            return 0
        lt = time.localtime(now)
        day_start = time.mktime((lt.tm_year, lt.tm_mon, lt.tm_mday, 0, 0, 0, 0, 0, -1))
        conn = sqlite3.connect("file:" + p.as_posix() + "?mode=ro", uri=True, timeout=5.0)
        try:
            rows = conn.execute(
                "SELECT content FROM memory_fragments WHERE origin = 'inner_thought' AND timestamp >= ? "
                "ORDER BY timestamp ASC LIMIT ?", (day_start, SEED_ROW_LIMIT)).fetchall()
        finally:
            conn.close()
        n = 0
        for (content,) in rows:
            if _countable(content):
                _add(content)
                n += 1
        return n
    except Exception as exc:
        logger.debug("[opener_diversity] store read failed (non-fatal): %s", exc)
        return 0


def _ensure_day(now: float) -> bool:
    """Roll the tally to today's date. Returns True if this call (re)built it from the store."""
    global _day
    d = _day_of(now)
    if d == _day:
        return False
    _day = d
    _counts.clear()
    _display.clear()
    _recent.clear()
    _seed_from_store(now)
    return True


def after_thought_opener(thought: str, system_note: bool = False, now: float | None = None) -> None:
    """Count this stored idle thought's opening. Called once, just after the inner_thought store. Never raises."""
    try:
        if system_note or not _countable(thought):
            return
        with _lock:
            if _ensure_day(time.time() if now is None else now):
                return                          # the store read just counted this row already
            _add(thought)
    except Exception as exc:
        logger.debug("[opener_diversity] after_thought failed (non-fatal): %s", exc)


def named_openers(now: float | None = None) -> list:
    """The opening keys the next seed line would name ([] if none). Pure read of the tally."""
    try:
        with _lock:
            _ensure_day(time.time() if now is None else now)
            if sum(_counts.values()) < MIN_TODAY:
                return []
            worn = [k for k, c in _counts.most_common() if c >= MIN_COUNT][:MAX_WORN]
            out = list(worn)
            for k in reversed(_recent):
                if len(out) >= MAX_WORN + RECENT_N:
                    break
                if k not in out:
                    out.append(k)
                    if len(out) - len(worn) >= RECENT_N:
                        break
            return out
    except Exception:
        return []


def seed_part_opener_diversity(now: float | None = None) -> str:
    """ONE seed line naming today's worn openings, or "" (flag off, too few thoughts, nothing to name). Never raises."""
    try:
        if not OPENER_DIVERSITY:
            return ""
        keys = named_openers(now)
        if not keys:
            return ""
        shown = []
        for k in keys:
            d = _display.get(k) or k
            d = d[:1].upper() + d[1:]
            shown.append("'" + d + "...'")
        if len(shown) == 1:
            lst = shown[0]
        else:
            lst = ", ".join(shown[:-1]) + " and " + shown[-1]
        try:
            from core import phrasing as _ph
            frame = _ph.vary("opener_diversity", _FRAMES, cooldown=FRAME_COOLDOWN) or _FRAMES[0]
        except Exception:
            frame = _FRAMES[0]
        return frame.replace("{openers}", lst)
    except Exception as exc:
        logger.debug("[opener_diversity] seed part failed (non-fatal): %s", exc)
        return ""


def stats() -> dict:
    """For tests and labs: the current tally (never raises)."""
    try:
        with _lock:
            return {"day": _day, "total": sum(_counts.values()), "distinct": len(_counts),
                    "top": _counts.most_common(5), "recent": list(_recent)}
    except Exception:
        return {}


def _reset_for_test() -> None:
    global _day
    with _lock:
        _day = None
        _counts.clear()
        _display.clear()
        _recent.clear()
