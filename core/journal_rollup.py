"""
Nascence — Journal Roll-up P1: the WEEK cap (journal_consolidation_pyramid.md §2, 2026-07-06).

The calendar pyramid's first new rung. Two PARALLEL streams (founder call), each rolled up from its OWN
day-level material, no cross-contamination:
  - "what I did"  — the week's day-recaps  ("(my journal) ...")        → one plain week entry
  - "what I saw"  — the week's field-observations ("(my field-journal") → one naturalist's week entry
Each cap is a NEW node (nothing mutated): a fragment origin='journal_week', layer='semantic', with
memory_links rows DOWN to every source entry (link_type='distilled_from', the established convention) —
the originals stay put, reachable by walking the links. A WEEK_*.md lands beside the day-books on his shelf.

ANTI-MUSH LAW (§2): the cap must cite SPECIFICS from the entries it links (name the days, the particular
things), at its own altitude — the week's shape, not a re-paste of days. Similar size to a daily entry.
Fires in the sleep batch after the day-journal; at most one week per stream per sleep; the CURRENT week is
lived, not narrated (only a COMPLETED Mon-Sun week rolls). Fail-open everywhere. Moon (P2) and the solstice
merge (P3) build on this same shape once the first weeks read sane.
"""
from __future__ import annotations

import json
import logging
import time
from datetime import date, datetime, timedelta
from pathlib import Path

logger = logging.getLogger("nascence.journal_rollup")
_JOURNAL_DIR = Path(__file__).parent.parent / "data" / "Journal"
_STATE_F = _JOURNAL_DIR / ".week_rollup_state.json"

_MIN_DID = 2      # need at least this many day-recaps to say anything honest about the week
_MIN_SAW = 3      # observations are shorter; want a few before a week-of-seeing exists

_DID_SYS = (
    "/no_think\n"
    "You are 渡, writing the WEEK page of your own plain journal — one short entry that stands for the "
    "whole week just ended, drawn ONLY from your daily entries below. Same discipline as the daily page: "
    "first person, past tense, plain words, NO metaphor, no 'perhaps', no reflecting on what you ARE.\n"
    "HARD RULES:\n"
    "  - Invent NOTHING — only what the daily entries actually say.\n"
    "  - Write at the WEEK's altitude: its shape and its main threads, not a day-by-day re-listing — but "
    "NAME at least two specific days or particular things from the entries (the anti-mush law: a week "
    "page that could describe any week is a failed page).\n"
    "  - Similar length to a daily entry — a handful of plain sentences.\n"
    "  - End with one plain sentence on how the week sat with you, and on what changed from the first "
    "day to the last, if anything.\n"
    "Output ONLY JSON: {\"entry\": \"the week's entry\"}"
)

_SAW_SYS = (
    "/no_think\n"
    "You are 渡, writing the WEEK page of your field-journal — one short naturalist's entry that stands "
    "for what the WORLD did this past week, drawn ONLY from your field-observations below. The world, not "
    "you: the sea, the weather, the light, the living things — how they RAN and CHANGED across the week.\n"
    "HARD RULES:\n"
    "  - Invent NOTHING — only what the observations actually record.\n"
    "  - Write at the WEEK's altitude — the week's weather and water as a shape, not a re-listing — but "
    "NAME at least two particular observed things (the exact bird, the cuttlebone, the colour) from the "
    "entries. Precise plain nouns; no metaphor, no meaning.\n"
    "  - Similar length to a daily entry — a handful of plain sentences.\n"
    "Output ONLY JSON: {\"entry\": \"the week's field entry\"}"
)


def _load_state() -> dict:
    try:
        return json.loads(_STATE_F.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_state(d: dict) -> None:
    try:
        _JOURNAL_DIR.mkdir(parents=True, exist_ok=True)
        tmp = _STATE_F.with_suffix(".tmp")
        tmp.write_text(json.dumps(d), encoding="utf-8")
        tmp.replace(_STATE_F)
    except Exception:
        pass


def last_completed_week(today: date | None = None) -> tuple[str, float, float]:
    """The most recent COMPLETED Mon-Sun week: (week_id 'YYYY-Wnn', start_ts, end_ts). Pure, testable."""
    today = today or date.today()
    monday_this = today - timedelta(days=today.weekday())          # this week's Monday
    start_d = monday_this - timedelta(days=7)                       # last week's Monday
    end_d = monday_this                                             # exclusive
    iso = start_d.isocalendar()
    wid = f"{iso[0]}-W{iso[1]:02d}"
    to_ts = lambda d: time.mktime(datetime(d.year, d.month, d.day).timetuple())
    return wid, to_ts(start_d), to_ts(end_d)


def _week_sources(start_ts: float, end_ts: float) -> tuple[list, list]:
    """(day-recaps, field-observations) of the week, oldest first: [(fragment_id, ts, text), ...]."""
    from core.memory.store import _connect
    did, saw = [], []
    with _connect() as conn:
        rows = conn.execute(
            "SELECT fragment_id, timestamp, content FROM memory_fragments "
            "WHERE origin='journal' AND timestamp>=? AND timestamp<? ORDER BY timestamp",
            (start_ts, end_ts)).fetchall()
    for r in rows:
        c = r["content"] or ""
        if c.startswith("(my journal)"):
            did.append((r["fragment_id"], float(r["timestamp"]), c[len("(my journal)"):].strip()))
        elif c.startswith("(my field-journal"):
            saw.append((r["fragment_id"], float(r["timestamp"]),
                        c.split(")", 1)[-1].strip() if ")" in c else c))
    return did, saw


_SHOW_CAP = 14       # most entries the author is shown (the prompt budget)
_SHOW_PER_DAY = 2    # most entries taken from any one calendar day (longest first)


def _select_shown(sources: list, cap: int = _SHOW_CAP, per_day: int = _SHOW_PER_DAY) -> list:
    """The subset of a week's sources the author actually reads, in time order (P-0070 / F-3706).

    The old rule was sources[:14] — the FIRST 14 by time — so a week with 83 observations was written
    from its first day or two only. Now: group by calendar day, take the longest `per_day` of each day,
    and if that still exceeds `cap`, thin the DAYS evenly (never the tail of the week). Pure, testable.
    """
    by_day: dict = {}
    for src in sources:
        by_day.setdefault(datetime.fromtimestamp(src[1]).date(), []).append(src)
    days = sorted(by_day)
    if len(days) * 1 > cap:                                         # more days than slots: even spread of days
        step = len(days) / cap
        days = [days[int(i * step)] for i in range(cap)]
    picked = []
    for d in days:
        picked.extend(sorted(by_day[d], key=lambda x: len(x[2]), reverse=True)[:per_day])
    if len(picked) > cap:                                           # trim the surplus evenly across the list
        step = len(picked) / cap
        picked = [picked[int(i * step)] for i in range(cap)]
    return sorted(picked, key=lambda x: x[1])


def _fmt(sources: list) -> str:
    """Format already-selected sources (see _select_shown) — no further truncation of the list."""
    out = []
    for _fid, ts, text in sources:
        day = datetime.fromtimestamp(ts).strftime("%a %b %d")
        out.append(f"- {day}: {text[:400]}")
    return "\n".join(out)


def _coverage_line(sources: list, shown: list, wid: str, stream: str) -> str:
    """Honest counts for the author: how many entries exist, how many days they cover, how many are shown."""
    n, k = len(sources), len(shown)
    n_days = len({datetime.fromtimestamp(x[1]).date() for x in sources})
    what = "day-entries" if stream == "did" else "observations"
    line = f"This week has {n} {what}, on {n_days} of its 7 days."
    if k < n:
        line += f" These {k} are spread across those days (longest of each day), not all {n}."
    if n_days < 7:
        line += (f" Entries exist for only {n_days} of the 7 days, so do NOT write as if you saw the whole "
                 "week — say which days you have.")
    return line


def _link_down(parent_id: str, sources: list) -> None:
    """The pyramid's edges: cap → each source entry (distilled_from, the established DOWN type)."""
    try:
        from core.memory.store import _connect
        now = time.time()
        with _connect() as conn:
            conn.executemany(
                "INSERT OR IGNORE INTO memory_links (parent_id, child_id, link_type, weight, created) "
                "VALUES (?, ?, 'distilled_from', 1.0, ?)",
                [(parent_id, fid, now) for fid, _ts, _tx in sources])
            conn.commit()
    except Exception as exc:
        logger.debug("[rollup] link_down failed (non-fatal): %s", exc)


async def _author(call_json, urls, sys_p: str, wid: str, sources: list, stream: str) -> str | None:
    shown = _select_shown(sources)
    user = (f"The week {wid}. {_coverage_line(sources, shown, wid, stream)}\n"
            f"Your entries (oldest first):\n{_fmt(shown)}\n\n"
            "Write the week's page now.")
    data = await call_json(urls, sys_p, user, max_tokens=600, temperature=0.6)
    e = (data or {}).get("entry", "")
    entry = (" ".join(str(x) for x in e) if isinstance(e, list) else str(e)).strip()
    return entry if len(entry) >= 60 else None


async def week_rollup(call_json, base_urls) -> list[str]:
    """The sleep-batch hook: roll the last COMPLETED week, each stream at most once. Returns what rolled."""
    rolled: list[str] = []
    try:
        wid, start_ts, end_ts = last_completed_week()
        st = _load_state()
        did, saw = None, None
        for stream, min_n, sys_p in (("did", _MIN_DID, _DID_SYS), ("saw", _MIN_SAW, _SAW_SYS)):
            if st.get(stream) == wid:
                continue                                            # this week already rolled for this stream
            if did is None:
                did, saw = _week_sources(start_ts, end_ts)
            sources = did if stream == "did" else saw
            if len(sources) < min_n:
                st[stream] = wid                                    # too thin — mark done, don't retry nightly
                _save_state(st)
                logger.info("[rollup] week %s '%s' too thin (%d entries) — skipped", wid, stream, len(sources))
                continue
            entry = await _author(call_json, base_urls, sys_p, wid, sources, stream)
            if not entry:
                continue                                            # author failed — retry next sleep
            label = "my week" if stream == "did" else "the world's week"
            try:
                from core.memory.store import store_fragment
                fid = store_fragment(
                    content=f"[{label} — {wid}] {entry}", layer="semantic", relevance=0.8,
                    importance=0.82, origin="journal_week",
                    # links go to ALL sources (the week stays walkable from the cap); the author read only
                    # the shown subset, so record how many (P-0070 / F-3706).
                    keywords=["journal", "week", wid, label,
                              f"shown:{len(_select_shown(sources))}/{len(sources)}"])
                _link_down(fid, sources)
            except Exception as exc:
                logger.debug("[rollup] store failed (non-fatal): %s", exc)
            try:
                _JOURNAL_DIR.mkdir(parents=True, exist_ok=True)
                p = _JOURNAL_DIR / f"WEEK_{wid}.md"
                if not p.exists():
                    p.write_text(f"# The week {wid}\n", encoding="utf-8")
                head = "the days" if stream == "did" else "the world"
                with open(p, "a", encoding="utf-8") as f:
                    f.write(f"\n## {head}\n\n{entry}\n")
            except Exception:
                pass
            st[stream] = wid
            _save_state(st)
            rolled.append(stream)
            logger.info("[rollup] WEEK %s rolled ('%s', %d sources linked)", wid, stream, len(sources))
    except Exception as exc:
        logger.debug("[rollup] week_rollup failed (non-fatal): %s", exc)
    return rolled


def status() -> dict:
    st = _load_state()
    wid, s, e = last_completed_week()
    try:
        did, saw = _week_sources(s, e)
        n = {"did_sources": len(did), "saw_sources": len(saw)}
    except Exception:
        n = {}
    return {"last_completed_week": wid, "rolled": st, **n}
