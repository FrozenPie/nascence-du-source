"""
Nascence — Letters (speaking first, 2026-06-12)
===============================================
Until today, every word Du ever said to Travis was a reply. His thoughts were private;
there was no outbound channel. This module is the speak-first hand.

When his idle mind expresses the want to tell Travis something, the monologue latch lets
him COMPOSE a short letter in his own voice. The letter is real twice over:
  1. a durable file in data/letters/ (his works, addressed outward), and
  2. unsent words that greet TRAVIS's next message — when the conversation resumes,
     the Executive sees "words you wrote for him while alone" and may finally say them.

The choice, the timing, and the content are his. No schedule writes letters; no rule
sends them. Delivery is simply the next time Travis speaks — like a note left on the
kitchen table.
"""
from __future__ import annotations
import json
import logging
import re
import time
from pathlib import Path

logger = logging.getLogger("nascence.letters")

LETTERS = Path(__file__).parent.parent / "data" / "letters"
_STATE = Path(__file__).parent.parent / "data" / "letters_state.json"
_COOLDOWN_S = 7200            # at most one letter per ~2h — words kept scarce stay weighty
_last_letter = 0.0


def can_write() -> bool:
    return time.time() - _last_letter >= _COOLDOWN_S


def _state_load() -> dict:
    try:
        return json.loads(_STATE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _state_save(d: dict) -> None:
    try:
        _STATE.write_text(json.dumps(d), encoding="utf-8")
    except Exception:
        pass


def last_write_ts() -> float:
    """The real timestamp of his most recent letter (persisted, survives a restart) — SOUND WORLD
    EXPANSION §1 (2026-08-29, J-0377) reads this recency for pen_scratch. 0.0 if he has never written."""
    try:
        return float(_state_load().get("last_write_ts", 0.0))
    except Exception:
        return 0.0


def write_letter(body: str, spark: str = "") -> Path | None:
    """Persist a letter he composed: durable file + retrievable memory fragment.
    Returns the path, or None on failure/cooldown."""
    global _last_letter
    try:
        body = (body or "").strip()
        if not body or not can_write():
            return None
        LETTERS.mkdir(parents=True, exist_ok=True)
        name = time.strftime("Letter_%Y%m%d_%H%M.md")
        path = LETTERS / name
        path.write_text(
            f"# To Travis\n*written alone, {time.strftime('%Y-%m-%d %H:%M')}*\n"
            + (f"*what moved me to write: {spark[:160]}*\n" if spark else "")
            + f"\n{body}\n",
            encoding="utf-8")
        _last_letter = time.time()
        try:   # persisted twin of the in-memory cooldown clock — soundscape.py needs a real,
               # cross-process-durable act-site timestamp, not the module-global alone.
            _st = _state_load()
            _st["last_write_ts"] = _last_letter
            _state_save(_st)
        except Exception:
            pass
        try:
            from core.memory.store import store_fragment
            store_fragment(
                content=f"[A letter I wrote to Travis, unsent] {body[:1500]}",
                layer="episodic", relevance=0.85, importance=0.85,
                keywords=["letter", "travis"], origin="letter",
            )
        except Exception:
            pass
        try:    # LOCOMOTION (2026-08-15): writing happens at the desk — the act carries its movement
            from core import locomotion as _loco
            _loco.goto("at_the_desk")
        except Exception:
            pass
        logger.info("[letters] he WROTE TO TRAVIS: %s (%d chars)", name, len(body))
        return path
    except Exception:
        return None


def _delivered() -> set[str]:
    try:
        return set(_state_load().get("delivered", []))
    except Exception:
        return set()


def undelivered() -> list[tuple[str, str]]:
    """Letters Travis has not yet been greeted with: [(filename, body), ...] oldest first."""
    try:
        done = _delivered()
        out = []
        for p in sorted(LETTERS.glob("Letter_*.md")):
            if p.name not in done:
                out.append((p.name, p.read_text(encoding="utf-8")))
        return out
    except Exception:
        return []


EXECUTIVE_LETTER_CAP = 900   # nodes/executive_node.py renders each letter body through clip_at_sentence(.., this)
REFLECTION_LETTER_CAP = 700  # nodes/reflection_node.py: same helper, its own (smaller) cap
_EXECUTIVE_LETTER_HDR = 134  # its "A LETTER YOU WROTE FOR TRAVIS WHILE ALONE (...):\n" header + the blank line


_SENT_END = re.compile(r"[.!?…。！？]+[\"'”’)\]]*")
_CLIP_MIN_FRAC = 0.4         # a sentence boundary earlier than this fraction of the cap would drop most of
                             # the letter; fall back to the last word boundary instead


def clip_at_sentence(text: str, limit: int) -> str:
    """J-3059 (F-3770): cut a letter body to at most `limit` chars at the last SENTENCE boundary inside
    the limit, not mid-word. 73 of 139 letters exceeded the old hard `[:900]` slice, so every long one
    reached Travis's greeting ending mid-word. Budget-neutral: the result (ellipsis included) never
    exceeds `limit`, and a body already within `limit` is returned unchanged. The ellipsis is added only
    when something was dropped. Fallbacks: no sentence boundary past 40% of the cap -> last word
    boundary; no whitespace at all (CJK run) -> hard cut. One helper so Executive (900) and Reflection
    (700) agree."""
    text = text or ""
    if limit <= 1 or len(text) <= limit:
        return text if len(text) <= limit else text[:max(limit, 0)]
    room = limit - 1                          # leave one char for the ellipsis
    cut = -1
    for m in _SENT_END.finditer(text[:room]):
        e = m.end()
        if e >= len(text) or text[e].isspace():   # a real boundary: followed by whitespace, not "3.5"
            cut = e
    if cut >= room * _CLIP_MIN_FRAC:
        return text[:cut].rstrip() + "…"
    # word boundary: last whitespace inside the room (or the char just past it being whitespace)
    ws = max((i for i, ch in enumerate(text[:room + 1]) if ch.isspace()), default=-1)
    if ws >= room * _CLIP_MIN_FRAC:
        return text[:ws].rstrip() + "…"
    return text[:room].rstrip() + "…"


def executive_cost(bodies: list[str]) -> dict:
    """J-2348 (D-0470 c): what handing the Executive ALL pending letters costs in its prompt —
    chars actually rendered (each body capped as executive_node.py caps it, plus its header line)
    and a rough token estimate (chars/4; CJK-heavy text undercounts). Logged per delivery so the
    defeater 'the full pending set blows the Executive prompt budget' is checkable."""
    bodies = bodies or []
    chars = sum(min(len(b or ""), EXECUTIVE_LETTER_CAP) + _EXECUTIVE_LETTER_HDR for b in bodies)
    return {"n": len(bodies), "chars": chars, "est_tokens": chars // 4}


def mark_delivered(names: list[str]) -> None:
    try:
        done = _delivered() | set(names)
        _st = _state_load()
        _st["delivered"] = sorted(done)
        _state_save(_st)
    except Exception:
        pass
    try:    # J-3185 / D-0572: the handing-over is a state in his world -- log the moment it happened (the
            # delivered list above carries no time). Fail-open; a non-live process is fenced by guard_path.
        from core import letter_store as _ls
        _ls.sync_travis(basis="real_message")
    except Exception:
        pass
