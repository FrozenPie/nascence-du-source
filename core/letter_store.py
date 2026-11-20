"""core/letter_store.py -- the letters as a permanent place-and-state in Du's world (J-2005, D-0394).

WHAT THIS IS. Du's correspondence lives in core/peers.py threads (data/Correspondence/<peer>/thread.jsonl),
which are NOT anywhere he can look; the garden mailbox holds only the CURRENT letter and a fetched letter
leaves it. Travis (D-0394, 2026-10-08, verbatim ask + addendum): letters should have "a permanent world
state. A history. He should be able to see them if he looks at/for them", with a status (unread / read /
replied ...), and NO "write back" instruction or steer line -- the unanswered ones are simply visible.

DESIGN (additive, derived, append-only):
  * peers.py threads stay the source of truth and are NEVER rewritten here. This module keeps a derived
    index: data/letter_store/letters.jsonl (one permanent object per letter, from every peer AND from Du,
    backfilled from the existing threads so the history exists from day one) and
    data/letter_store/status_events.jsonl (every status change, appended, never overwritten -- the history
    of a letter's state, not just its current state).
  * Status is derived, never invented:
        unread   -- a peer letter nobody has fetched/looked at and Du has not answered
        read     -- he fetched it from the mailbox (explicit read event), OR he answered it (a reply
                    implies he read it -- same rule peers.remember_inbound already uses)
        replied  -- a Du letter exists in the same thread AFTER it
        sent     -- Du's own letters
    'rejected' / 'declined' DOES NOT EXIST in the data today (no decline path in peers.py or the hands),
    so it is deliberately left out; whether it should exist is a founder question (see the job notes).
  * SHADOW-FIRST (J-2005) -> RENDERING ON (J-2249 / D-0449, 2026-10-16): PROMPT_ENABLED now defaults True, so
    a look at the kept letters returns the tray text. With it off (NASCENCE_LETTER_STORE_PROMPT=0), a look that WOULD have found the tray still logs what it would have shown and that he
    looked (data/letter_store_shadow.jsonl) and returns "" so the existing look paths run unchanged.
  * Gauges as words (D-0367): the rendered text never shows a number; counts and ages are words.
  * Every writer resolves its path through profile.guard_path (D-0179): a non-live process raises
    NonLiveWriteError before any I/O. Callers on the live path let it propagate (like supply.py); the
    public hook functions below fail open on every OTHER error.

The pre-registered read (7 live days after the restart that enables this): did he visit the store, and did
visits precede a reply -- scripts/letter_store_read.py computes both from the shadow log + the threads.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from pathlib import Path

from core import profile

_DATA = Path(__file__).parent.parent / "data"
_DIR = _DATA / "letter_store"
_LETTERS = _DIR / "letters.jsonl"
_EVENTS = _DIR / "status_events.jsonl"
_SHADOW = _DATA / "letter_store_shadow.jsonl"

# RENDERING ON (J-2249 / D-0449, travis 2026-10-16, option (a)): a look that reaches the kept letters -- the
# letterbox at the garden gate, or "my letters" / "the letters from X" from anywhere -- now SHOWS the tray (or one
# correspondent's thread) with each letter's status, in words. This is the D-0394 design itself switched on; the
# rendered text carries no write-back / reply / steer line (the unanswered ones are simply visible). Every visit is
# still logged to the shadow log (prompt_enabled now True) for the 2-3 live-day read D-0449 asks for.
# Kill switch: NASCENCE_LETTER_STORE_PROMPT=0 restores the J-2005 shadow behaviour (log only, return "").
# Was: os.environ.get("NASCENCE_LETTER_STORE_PROMPT", "0") == "1"  (shadow-first default, J-2005).
PROMPT_ENABLED = os.environ.get("NASCENCE_LETTER_STORE_PROMPT", "1") != "0"
# The persisted index + shadow log are additive world-state and default ON (restart-gated by being new code).
STORE_ENABLED = os.environ.get("NASCENCE_LETTER_STORE", "1") != "0"

# J-3185 / D-0572 (travis 2026-11-02, plan letters_to_travis): HIS OWN letters to Travis get a state in his world, the
# same kept -> handed over -> read ladder the peer letters have. "kept" = written, not yet carried into a conversation;
# "handed over" = carried into the conversation on Travis's next REAL message (core/letters.py's delivered list; a
# farewell never marks it, J-2348); "read" = Travis opened the HUD letters card after the letter was written
# (data/letters_views.jsonl, read-only here). Shown in words in the tray a letterbox look returns, with NO steer
# line, no instruction to write or to stop. Additive: derived over data/letters + letters_state.json + the views log;
# the only new store is the append-only travis_letter_events.jsonl (the history of each letter's state).
# Kill switch: NASCENCE_LETTER_TRAVIS_STATE=0 restores the tray and the look hook byte-for-byte as they were.
TRAVIS_STATE_ENABLED = os.environ.get("NASCENCE_LETTER_TRAVIS_STATE", "1") != "0"
_TRAVIS_EVENTS = _DIR / "travis_letter_events.jsonl"
_TRAVIS_VIEWS = _DATA / "letters_views.jsonl"          # the HUD's own view log; READ-ONLY here

_SEEN_NOTE = {"unread": "not yet opened", "read": "read, not answered", "replied": "answered", "sent": "sent by you"}

_NUM = ["no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "a dozen"]


# ---- small helpers -------------------------------------------------------------------------------------

def _words_count(n: int) -> str:
    if n <= 12:
        return _NUM[n]
    return "a dozen and more" if n < 24 else "a great many"


def _age_words(ts: float, now: float | None = None) -> str:
    d = max(0.0, (now or time.time()) - ts)
    if d < 3600 * 6:
        return "a little while ago"
    if d < 86400 * 1.5:
        return "yesterday" if d >= 86400 * 0.75 else "earlier today"
    days = d / 86400
    if days < 6:
        return f"{_NUM[min(12, int(round(days)))]} days ago"
    if days < 11:
        return "about a week ago"
    if days < 25:
        return "a couple of weeks ago"
    if days < 60:
        return "a month or so ago"
    return "a long while ago"


def _read_jsonl(path: Path) -> list[dict]:
    try:
        return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    except Exception:
        return []


def _append(path: Path, rec: dict) -> None:
    p = profile.guard_path(path)      # raises NonLiveWriteError before any I/O if non-live (D-0179)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _lid(persona: str, row: dict) -> str:
    h = hashlib.sha1(((row.get("text") or "")[:200]).encode("utf-8", "ignore")).hexdigest()[:6]
    return f"{persona}-{int(float(row.get('ts', 0)) * 1000)}-{h}"


def _threads() -> dict[str, list[dict]]:
    from core import peers
    return {k: peers._read_thread(k) for k in peers.PERSONAS}


def _name(persona: str) -> str:
    try:
        from core import peers
        return peers.PERSONAS[persona]["name"]
    except Exception:
        return persona.title()


# ---- derivation (pure over threads + events) -------------------------------------------------------------

def derive(threads: dict[str, list[dict]], read_ids: set[str]) -> list[dict]:
    """Every letter in every thread as an object with its derived CURRENT status. Pure."""
    out: list[dict] = []
    for persona, rows in threads.items():
        for i, r in enumerate(rows):
            lid = _lid(persona, r)
            ts = float(r.get("ts", 0))
            if r.get("from") == "du":
                out.append({"id": lid, "peer": persona, "from": "du", "ts": ts, "text": r.get("text", ""),
                            "status": "sent", "status_ts": ts, "basis": "own_letter"})
                continue
            reply = next((x for x in rows[i + 1:] if x.get("from") == "du"), None)
            if reply is not None:
                st, sts, basis = "replied", float(reply.get("ts", ts)), "du_letter_after"
            elif lid in read_ids:
                st, sts, basis = "read", ts, "fetched"
            else:
                st, sts, basis = "unread", ts, "arrival"
            o = {"id": lid, "peer": persona, "from": persona, "ts": ts, "text": r.get("text", ""),
                 "status": st, "status_ts": sts, "basis": basis}
            if r.get("stance"):
                o["stance"] = r["stance"]
            out.append(o)
    return out


def _read_ids() -> set[str]:
    return {e["letter_id"] for e in _read_jsonl(_EVENTS) if e.get("status") == "read" and e.get("basis") == "fetched"}


def engagement_ts(persona: str) -> float:
    """When Du last ENGAGED with `persona`'s letters without writing back: the latest of (a) a fetch of one of that
    persona's letters out of the mailbox (status_events basis 'fetched') and (b) a look that named that persona
    (letter_store_shadow kind 'visit' with peer == persona). 0.0 if none. A general look at the whole tray (peer
    None) is deliberately NOT counted -- it lists every correspondent every time. Read-only; the reader is
    peers._unanswered_count (J-3189, D-0576: a persona's gap resets when Du answers OR visits the box)."""
    best = 0.0
    prefix = f"{persona}-"
    for e in _read_jsonl(_EVENTS):
        if e.get("status") == "read" and e.get("basis") == "fetched" and str(e.get("letter_id", "")).startswith(prefix):
            best = max(best, float(e.get("ts", 0) or 0))
    for e in _read_jsonl(_SHADOW):
        if e.get("kind") == "visit" and e.get("peer") == persona:
            best = max(best, float(e.get("ts", 0) or 0))
    return best


def _last_status() -> dict[str, str]:
    last: dict[str, str] = {}
    for e in _read_jsonl(_EVENTS):
        last[e["letter_id"]] = e["status"]
    return last


def sync(now: float | None = None) -> dict:
    """Append letter objects for threads rows not yet indexed, and a status event for every letter whose
    derived status differs from its last logged one. Idempotent; never rewrites anything. Returns counts."""
    if not STORE_ENABLED:
        return {"enabled": False}
    now = now or time.time()
    have = {l["id"] for l in _read_jsonl(_LETTERS)}
    last = _last_status()
    objs = derive(_threads(), _read_ids())
    new_letters = new_events = 0
    for o in objs:
        if o["id"] not in have:
            _append(_LETTERS, {"id": o["id"], "peer": o["peer"], "from": o["from"], "ts": o["ts"],
                               "text": o["text"], "stance": o.get("stance"), "indexed": now})
            new_letters += 1
        if last.get(o["id"]) != o["status"]:
            if o["status"] == "replied" and last.get(o["id"]) in (None, "unread"):
                # a reply implies he read it -- recorded as its own step so the history shows the passage
                if last.get(o["id"]) is None and o["from"] != "du":
                    _append(_EVENTS, {"letter_id": o["id"], "status": "unread", "ts": o["ts"], "basis": "arrival"})
                _append(_EVENTS, {"letter_id": o["id"], "status": "read", "ts": o["status_ts"],
                                  "basis": "implied_by_reply"})
            _append(_EVENTS, {"letter_id": o["id"], "status": o["status"], "ts": o["status_ts"],
                              "basis": o["basis"], "logged": now})
            new_events += 1
    return {"enabled": True, "new_letters": new_letters, "new_events": new_events, "letters": len(objs)}


def record_read(sender: str, text: str) -> None:
    """He fetched this letter out of the mailbox. Marks the matching thread letter READ (once)."""
    if not STORE_ENABLED:
        return
    try:
        key = " ".join((text or "").split())[:120]
        persona = next((k for k in _threads() if _name(k) == sender or k == (sender or "").lower()), None)
        if not persona:
            return
        from core import peers
        for r in reversed(peers._read_thread(persona)):
            if r.get("from") != "du" and " ".join((r.get("text") or "").split())[:120] == key:
                lid = _lid(persona, r)
                if lid not in _read_ids():
                    sync()
                    _append(_EVENTS, {"letter_id": lid, "status": "read", "ts": time.time(), "basis": "fetched"})
                    _shadow({"kind": "read", "peer": persona, "letter_id": lid})
                return
    except profile.NonLiveWriteError:
        raise
    except Exception:
        pass


# ---- Du's letters to Travis: kept -> handed over -> read (J-3185 / D-0572) ---------------------------------

_TRAVIS_STEPS = ("kept", "handed_over", "read")
_TRAVIS_NOTE = {"kept": "kept, waiting for the next time Travis speaks",
                "handed_over": "handed over when Travis next spoke",
                "read": "read by Travis"}


def _travis_letter_ts(name: str) -> float:
    """Letter_YYYYMMDD_HHMM.md -> the write time (core/letters.py names the file with time.strftime, local time)."""
    try:
        return time.mktime(time.strptime(name[len("Letter_"):-len(".md")], "%Y%m%d_%H%M"))
    except Exception:
        return 0.0


def _travis_view_ts() -> list[float]:
    """When Travis opened the HUD letters card (hud/server.py appends one row per opening). Read-only."""
    out = []
    for r in _read_jsonl(_TRAVIS_VIEWS):
        try:
            out.append(float(r.get("ts", 0) or 0))
        except Exception:
            pass
    return sorted(out)


def derive_travis(now: float | None = None) -> list[dict]:
    """Every letter he wrote to Travis (data/letters/Letter_*.md), oldest first, with the steps it has REACHED
    and its current (highest) status. Pure over the letters dir, letters_state.json and the HUD view log."""
    from core import letters as _letters
    try:
        names = sorted(p.name for p in _letters.LETTERS.glob("Letter_*.md"))
    except Exception:
        names = []
    done = _letters._delivered()
    views = _travis_view_ts()
    out = []
    for n in names:
        ts = _travis_letter_ts(n)
        first_view = next((v for v in views if v >= ts), None)
        steps = {"kept": ts}
        if n in done:
            steps["handed_over"] = None            # the delivered list carries no time; the events log does
        if first_view is not None:
            steps["read"] = first_view
        status = [s for s in _TRAVIS_STEPS if s in steps][-1]
        out.append({"id": f"travis-{n}", "name": n, "ts": ts, "steps": steps, "status": status})
    return out


def _travis_logged() -> dict[str, set[str]]:
    seen: dict[str, set[str]] = {}
    for e in _read_jsonl(_TRAVIS_EVENTS):
        seen.setdefault(e.get("letter_id", ""), set()).add(e.get("status", ""))
    return seen


def sync_travis(now: float | None = None, basis: str = "delivered_state") -> dict:
    """Append one event per (letter, step) not yet logged: kept at the write time, handed_over now (the first
    time the delivered list is seen to hold it -- core/letters.mark_delivered calls this at the moment of
    delivery with basis 'real_message'), read at the first HUD-card opening after the write. Idempotent; never
    rewrites anything. Raises NonLiveWriteError from a non-live process (D-0179) like every writer here."""
    if not (STORE_ENABLED and TRAVIS_STATE_ENABLED):
        return {"enabled": False}
    now = now or time.time()
    logged = _travis_logged()
    n = 0
    for o in derive_travis(now):
        have = logged.get(o["id"], set())
        for step in _TRAVIS_STEPS:
            if step not in o["steps"] or step in have:
                continue
            t = o["steps"][step]
            rec = {"letter_id": o["id"], "status": step, "ts": t if t is not None else now}
            rec["basis"] = {"kept": "written", "handed_over": basis, "read": "hud_card_opened"}[step]
            if t is None:
                rec["logged"] = now
            _append(_TRAVIS_EVENTS, rec)
            n += 1
    return {"enabled": True, "new_events": n}


def render_travis_summary(now: float | None = None) -> str:
    """One sentence-group, in words and never a number, on his own letters to Travis and where each stands."""
    if not TRAVIS_STATE_ENABLED:
        return ""
    objs = derive_travis(now)
    if not objs:
        return ""
    n_k = sum(1 for o in objs if o["status"] == "kept")
    n_h = sum(1 for o in objs if o["status"] == "handed_over")
    n_r = sum(1 for o in objs if o["status"] == "read")
    bits = [f"{_words_count(len(objs))} letters kept"]
    if n_k:
        bits.append(f"{_words_count(n_k)} waiting for the next time Travis speaks")
    if n_h:
        bits.append(f"{_words_count(n_h)} handed over when he spoke and not yet read")
    if n_r:
        bits.append(f"{_words_count(n_r)} read by him")
    last = objs[-1]
    bits.append(f"the newest was written {_age_words(last['ts'], now)} and is {_TRAVIS_NOTE[last['status']]}")
    return "Your own letters to Travis are kept here as well: " + "; ".join(bits) + "."


def render_travis_thread(now: float | None = None, keep: int = 6) -> str:
    """Your letters to Travis, oldest to newest (the latest few), each with its state in words."""
    objs = derive_travis(now)
    if not objs:
        return ""
    shown = objs[-keep:]
    out = ["Your letters to Travis, oldest to newest:"]
    if len(objs) > len(shown):
        out.append(f"- {_words_count(len(objs) - len(shown))} earlier ones, kept.")
    for o in shown:
        out.append(f"- {_age_words(o['ts'], now)}: {_TRAVIS_NOTE[o['status']]}.")
    return " ".join(out)


# ---- the tray, in words ---------------------------------------------------------------------------------

def _current(now: float | None = None) -> list[dict]:
    return derive(_threads(), _read_ids())


def render_tray(now: float | None = None) -> str:
    """What he sees when he looks at the kept letters: one line per correspondent, in words. Never a number."""
    objs = _current(now)
    _tv = render_travis_summary(now) if TRAVIS_STATE_ENABLED else ""     # J-3185 / D-0572: his letters to Travis
    if not objs and not _tv:
        return ""
    by: dict[str, list[dict]] = {}
    for o in objs:
        by.setdefault(o["peer"], []).append(o)
    lines = []
    for persona, ls in sorted(by.items(), key=lambda kv: -max(x["ts"] for x in kv[1])):
        ls.sort(key=lambda x: x["ts"])
        theirs = [x for x in ls if x["from"] != "du"]
        if not theirs:
            continue
        n_un = sum(1 for x in theirs if x["status"] == "unread")
        n_rd = sum(1 for x in theirs if x["status"] == "read")
        last = theirs[-1]
        bits = [f"{_words_count(len(ls))} letters kept"]
        if n_un:
            bits.append(f"{_words_count(n_un)} not yet opened")
        if n_rd:
            bits.append(f"{_words_count(n_rd)} read and not answered")
        bits.append(f"the newest came {_age_words(last['ts'], now)} and is {_SEEN_NOTE[last['status']]}")
        lines.append(f"{_name(persona)}: " + "; ".join(bits) + ".")
    if not lines and not _tv:
        return ""
    if _tv:
        if not lines:
            return ("The letters are all here, kept in the order they came, none ever thrown out -- theirs and yours. "
                    + _tv)
        return ("The letters are all here, kept in the order they came, none ever thrown out -- theirs and yours. "
                + " ".join(lines) + " " + _tv
                + " You have only to look at any one correspondent's letters to see them through.")
    return ("The letters are all here, kept in the order they came, none ever thrown out -- theirs and yours. "
            + " ".join(lines) + " You have only to look at any one correspondent's letters to see them through.")


def render_peer(persona: str, now: float | None = None) -> str:
    """One correspondent's whole thread, oldest to newest, each letter with its state in words."""
    ls = sorted([o for o in _current(now) if o["peer"] == persona], key=lambda x: x["ts"])
    if not ls:
        return ""
    out = [f"Your letters with {_name(persona)}, oldest to newest:"]
    for o in ls:
        who = "yours" if o["from"] == "du" else "theirs"
        out.append(f"- {_age_words(o['ts'], now)}, {who}: {_SEEN_NOTE[o['status']]}.")
    return " ".join(out)


# ---- shadow log + the look hook ---------------------------------------------------------------------------

def _shadow(rec: dict) -> None:
    _append(_SHADOW, {"ts": round(time.time(), 1), **rec})


_TO_TRAVIS = re.compile(r"\bletters?\s+(?:to|for)\s+travis\b")


def _unanswered_peers() -> list[str]:
    return sorted({o["peer"] for o in _current() if o["from"] != "du" and o["status"] in ("unread", "read")})


def on_look(via: str, target: str = "", raw: str = "") -> str:
    """A look that reached the kept letters. Shadow: log what the tray WOULD show and that he looked, return
    "" (no prompt text). Only when PROMPT_ENABLED does it return the tray text. Fails open (never raises
    except NonLiveWriteError, which the world-store fence wants to reach its caller)."""
    if not STORE_ENABLED:
        return ""
    try:
        sync()
        if TRAVIS_STATE_ENABLED:
            sync_travis()                 # J-3185 / D-0572: the history of each letter-to-Travis state, appended
        low = f"{target} {raw}".lower()
        peer = next((k for k in _threads() if k in low or _name(k).lower().split()[-1] in low), "")
        if not peer and TRAVIS_STATE_ENABLED and _TO_TRAVIS.search(low):
            text = render_travis_thread()
        else:
            text = render_peer(peer) if peer else render_tray()
        _shadow({"kind": "visit", "via": via, "peer": peer or None, "would_show_chars": len(text),
                 "would_show": text[:600], "unanswered_peers": _unanswered_peers(),
                 "prompt_enabled": PROMPT_ENABLED})
        return text if PROMPT_ENABLED else ""
    except profile.NonLiveWriteError:
        raise
    except Exception:
        return ""


_PHRASES = ("my letters", "the letters", "old letters", "past letters", "kept letters", "letters i", "letters from",
            "letters kept", "letter tray", "letter drawer", "letters tray", "letters drawer", "correspondence",
            "letters i have", "letters i've", "letters in the", "back through my letters", "letter from")


def wants_letters(target: str, raw: str = "") -> bool:
    """Does this look name the kept letters (not the mailbox, which has its own branch)? Phrase-based, so a
    stray 'letters' in a sentence about a book does not count."""
    import re
    t = re.sub(r"[^a-z' ]+", " ", f"{target} {raw}".lower())
    t = " " + " ".join(t.split()) + " "
    if any(m in t for m in (" letterbox ", " mailbox ", " postbox ", " letter box ", " mail box ")):
        return False
    return any(f" {p} " in t or t.startswith(f" {p}") for p in _PHRASES)
