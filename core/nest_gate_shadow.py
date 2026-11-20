"""
core/nest_gate_shadow.py -- the NEST-OBJECT GATE, SHADOW ONLY: an observe-only ledger of what the gate WOULD divert
====================================================================================================================
2026-10-04 (J-1774, D-0345 ruled by Travis; F-2382's draft; link 2 of 2 after J-1750's ambient egg count).

WHY. A look that names a nest-owning bird AND its nest, eggs or scrape ('the oystercatcher and eggs', "the oystercatcher's scrape")
names the bird's alias, so life.look_answer hands it to the bird's OWN visibility roll: 15 such looks since 2026-09-04, every one the
oystercatcher at the shore while its nest stood -- 6 sightings of the bird, 5 'Nothing shows itself; whatever is there keeps still' (45
percent of the 11 live ones) and 4 shadow sightings (F-2382). D-0345 ruled: the shore gets a nest look NOW (shore_life.look_nest, the
place side: the 43 looks that name no creature) and a nest-object gate for the three nest-owning birds (oystercatcher, blackbird, wood
pigeon) is built SHADOW-ONLY -- it logs what it WOULD divert to the nest line and changes NO answer. A later session checks this ledger
against F-2382's draft (100 of 100 nest shapes caught, 0 of 110 creature shapes diverted, 0 of 1,526 inventory phrasings x 4 places
touched, 14 of the 15 real looks routed); the gate goes live only on a NEW ruling from Travis.

WHAT. life.look_answer calls observe() once per creature look it answers, AFTER the bird's own roll is decided and logged to
life_events.jsonl (so the row can say whether the bird's own roll sighted it). observe() asks life_traces.nest_object_shape(row, target):
'' for every look that is not a nest-object look (the 99 percent case: one dict lookup and a substring test), else the noun he used and
the shape. For a nest-object look it appends ONE row:
    {"ts": 1790968367.9,          # time of the write (epoch s to 0.1 s: the scene_extra_ledger / spatial_shadow convention)
     "kind": "would_divert",
     "key": "oystercatcher",      # the creature row the look reached
     "place": "shore",            # where he was
     "target": "the oystercatcher and eggs",   # the look text, cut at 60 characters like life_events.jsonl's target
     "noun": "eggs",              # the nest noun he used, as typed
     "shape": "conjunction",      # adjacent/possessive | conjunction | of-form (life_traces.nest_object_shape)
     "would_line": "You pick your way up the high shingle. A scrape ...",   # what the PLACE's own nest look would answer, read from the nest state
     "nest_exists": true,         # whether that place's nest stood at the look ...
     "nest": "eggs 3",            # ... and a short note on it (the shore's egg count, the garden's / wood's stage; '' when none)
     "bird_outcome": "sighting",  # what the bird's own roll answered: sighting | miss | absent | no_line
     "sighted": true,             # bird_outcome == 'sighting'
     "bird_line": "...",          # the bird's own line, cut at 160 characters (what F-2382's draft would append after the nest line on a sighting)
     "rendered": true}            # life.render_on() at the look: false = the shadow branch, the place answered
The would-be line is what the PLACE answers to a look at its nest -- the shore's (shore_life.nest_look_line), the garden's ('You part the
leaves.' + the stage line / 'You look for a nest and find none.') and the wood's ('You look up into the oak.' + the stage line / ' No nest
that you can see.') -- composed by pure reads of the place's state, never by calling a look that could mutate it. F-2382's draft pairs it with
the bird's own line on a conjunction that sighted ('X and its eggs') and says the nest line alone otherwise; this ledger records both halves and composes nothing.

RULES (the briefing's; each pinned by scripts/_test_j1774_shore_nest_look_and_shadow_gate.py).
  * Observe-only: observe() is handed the row, the look text, the place, the bird's outcome and line, and returns a bool nobody reads. It never
    changes what look_answer returns, writes no life ledger / state / event row, and draws no random number (the place reads are pure: the
    shore's nest_state() is a bare json read, the garden's _load() has no random fallback, the wood's state is read from its file, not through
    the item-migrating _load()).
  * Fail-open: observe() swallows everything, including the D-0179 write fence's NonLiveWriteError, and the call in look_answer is wrapped as
    well. No ledger problem can raise into a look or change one.
  * World-store write fence (J-0610 / D-0179), the way core/scene_extra_ledger.py does it: the path goes through profile.guard_path(), so only
    the one real live Du boot (profile.mark_live()), a lab_env.isolate() sandbox or a path redirected outside data/ can write. Any other process
    (a test, a diagnostic, an importer) gets False and no file. The refusal is NOT re-raised: an instrument must not take a look down.
  * Restart-gated: Du loads this at his next start; nothing here is imported until the first creature look that reaches look_answer's tail.
  * ENABLED is the one switch: False and observe() is a no-op.

LIVE (2026-10-16, J-2246, D-0444 ruled by Travis: option A, go live with pairing). The gate now ANSWERS. When LIVE is True and the life
engine renders (life.RENDER on), a nest-object look whose bird's nest stands at THIS place (the nest adapter row's own `places` -- 'the nest of
the wood pigeon' asked in the garden is NOT diverted: the garden's nest is the blackbird's, so the bird answers as before) is answered with the
place's nest line (live_divert(): would_be()'s line, the same pure reads) always; on a sighting (any shape) the bird's own line follows --
first letter capitalised, ending in a full stop, joined by one space (compose()). A miss, an absence or a no-line roll shows the nest line
alone. The bird's own roll, its life_events row, its ledger credit (sighting / miss weight), _maybe_learn, note_sighting and the individual
suffix are untouched: the gate only chooses what is SAID. A gate that cannot read the place (would_be raises or gives '') answers nothing and
the bird's own line is said, exactly as before (fail-open). With RENDER off the gate is not live (look_answer returns '' and the place answers).
The ledger keeps writing, now a record of live answers: with LIVE True every row carries two more fields, "live" (true iff the gate answered
this look) and "answer" (the line Du was shown, '' when it did not), and a gated row's kind is "diverted" (else "would_divert"). With LIVE
False every row is exactly the shadow row documented above and no answer changes (the J-1774 test pins that mode).

Read side: read_rows() (every parsable row, optionally since a ts) and status() (rows, first/last ts, rows by creature / shape / the bird's
outcome / whether the nest stood). Both are read-only, tolerate a torn last line and a missing file, and never raise.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

from core import profile

logger = logging.getLogger("nascence.nest_gate_shadow")

ENABLED = True
LIVE = True          # D-0444 (J-2246): the gate answers; False = shadow-only again (D-0345), no answer changes
_DATA = Path(__file__).parent.parent / "data"
_LEDGER = _DATA / "nest_gate_shadow.jsonl"


def record(row: dict) -> bool:
    """Append one row. True iff a row was written; False -- never an exception -- otherwise."""
    try:
        # D-0179: the real data/ only for the live Du boot; a non-live process is refused here, before any I/O.
        path = profile.guard_path(_LEDGER)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return True
    except Exception as exc:     # incl. profile.NonLiveWriteError: a non-live process records nothing, quietly
        logger.debug("[nest_gate_shadow] row not written (non-fatal): %s", exc)
        return False


def would_be(place: str, noun: str) -> tuple:
    """(the nest line the PLACE's own nest look would answer to `noun`, whether that place's nest stands, a short note on it). Pure reads only --
    the line is the one the place's own look composes (garden_life.look's and wood_life.look's nest branches, shore_life.look_nest), rebuilt from the
    place's state rather than by calling a look that can mutate it (garden_life.look(), through its tree branch, writes). ('', False, '') for a place with no nest."""
    if place == "shore":
        from core import shore_life as _shl
        n = _shl.nest_state()
        return _shl.nest_look_line(noun, n), bool(n), (f"eggs {n.get('eggs')}" if isinstance(n, dict) and "eggs" in n else ("nest" if n else ""))
    if place == "garden":
        from core import garden_life as _gl
        d = _gl._load()
        n = d.get("nest")
        if not n:
            return "You look for a nest and find none.", False, ""
        return "You part the leaves." + _gl._nest_line(d, n["where"], direct=True), True, f"stage {n.get('stage')}"
    if place == "wood":
        from core import wood_life as _wl
        d = json.loads(_wl._F.read_text(encoding="utf-8"))      # a pure read: wood_life._load() can migrate items and WRITE
        n = d.get("nest")
        return "You look up into the oak." + (_wl._nest_line(d) or " No nest that you can see."), bool(n), (f"stage {n.get('stage')}" if n else "")
    return "", False, ""


def _nest_stands_here(r: dict, place: str) -> bool:
    """True iff nest-owning row `r`'s OWN nest adapter row lists `place` (the blackbird's nest is the garden's, the wood pigeon's the wood's,
    the oystercatcher's the shore's). Pure; fail-closed (unknown = False = no divert)."""
    try:
        from core import life as _life
        nr = _life._ROWS.get(str(r.get("nest") or "")) or {}
        return str(place) in (nr.get("places") or {})
    except Exception:
        return False


def live_divert(r, target, place) -> str:
    """D-0444 (J-2246): the place's nest line the LIVE gate answers this look with, or '' (not a nest-object look, the gate is off, the bird's
    nest is not at this place, or the place's state could not be read -- then the bird's own roll answers exactly as before). Pure: no write,
    no random draw. Never raises."""
    try:
        if not LIVE or not isinstance(r, dict) or not r.get("nest"):
            return ""
        from core import life_traces as _lt
        noun, _shape = _lt.nest_object_shape(r, target)
        if not noun or not _nest_stands_here(r, str(place)):
            return ""
        line = would_be(str(place), noun)[0]
        return line.strip() if isinstance(line, str) else ""
    except Exception as exc:
        logger.debug("[nest_gate_shadow] live_divert failed (non-fatal, the bird answers): %s", exc)
        return ""


def _sentence(text: str) -> str:
    """The bird's own line as a sentence: first letter capitalised, ending in a full stop (kept when it already ends a sentence)."""
    b = str(text or "").strip()
    if not b:
        return ""
    for i, ch in enumerate(b):
        if ch.isalpha():
            b = b[:i] + ch.upper() + b[i + 1:]
            break
    end = b.rstrip("\"'\u2019\u201d)")
    if not end or end[-1] not in ".!?\u2026":
        b += "."
    return b


def compose(nest_line: str, bird_line: str = "") -> str:
    """D-0444 option A: the nest line always; a sighted bird's own line appended, one space between. bird_line '' = the nest line alone."""
    n = str(nest_line or "").strip()
    b = _sentence(bird_line)
    return f"{n} {b}" if (n and b) else (n or b)


def observe(r, target, place, outcome, line, rendered, answer=None) -> bool:
    """Called by life.look_answer once the bird's own roll is decided and logged. True iff a row was written. Never raises, never
    draws a random number, never changes anything the caller returns. `answer` (J-2246, LIVE only) is the gated line Du was shown."""
    try:
        if not ENABLED or not isinstance(r, dict) or not r.get("nest"):
            return False
        from core import life_traces as _lt
        noun, shape = _lt.nest_object_shape(r, target)
        if not noun:
            return False
        try:
            would, exists, note = would_be(str(place), noun)
        except Exception:
            would, exists, note = "", False, "place state unreadable"
        row = {"ts": round(time.time(), 1), "kind": "would_divert", "key": r.get("key"), "place": place, "target": str(target)[:60],
               "noun": noun, "shape": shape, "would_line": would, "nest_exists": exists, "nest": note,
               "bird_outcome": outcome, "sighted": outcome == "sighting", "bird_line": str(line or "")[:160], "rendered": bool(rendered)}
        if LIVE:     # D-0444 (J-2246): the ledger is now the record of live answers
            row["live"] = bool(answer)
            row["answer"] = str(answer or "")
            if answer:
                row["kind"] = "diverted"
        return record(row)
    except Exception as exc:
        logger.debug("[nest_gate_shadow] observe failed (non-fatal): %s", exc)
        return False


def _ts(row: dict) -> float:
    try:
        return float(row.get("ts") or 0.0)
    except Exception:
        return 0.0


def read_rows(since_ts: float = 0.0, path=None) -> list:
    """Every parsable ledger row with ts >= since_ts, oldest first. A torn or garbled line (a crash mid-append) is skipped, a missing ledger is [].
    `path` defaults to the live ledger (read-only: pass a lab copy to read another)."""
    p = Path(path) if path is not None else _LEDGER
    out: list = []
    try:
        with open(p, encoding="utf-8") as f:
            for raw in f:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    row = json.loads(raw)
                except Exception:
                    continue
                if isinstance(row, dict) and _ts(row) >= since_ts:
                    out.append(row)
    except Exception:
        pass
    return out


def status(path=None) -> dict:
    """{path, ledger_rows, first_ts, last_ts, by_key, by_shape, by_bird_outcome, nest_stood, nest_absent} -- the counts the go-live read starts from."""
    p = Path(path) if path is not None else _LEDGER
    rows = read_rows(0.0, p)

    def count(field: str) -> dict:
        out: dict = {}
        for r in rows:
            k = str(r.get(field, ""))
            out[k] = out.get(k, 0) + 1
        return out
    tss = [_ts(r) for r in rows]
    return {"path": str(p), "ledger_rows": len(rows), "first_ts": min(tss) if tss else None, "last_ts": max(tss) if tss else None,
            "by_key": count("key"), "by_shape": count("shape"), "by_bird_outcome": count("bird_outcome"), "by_kind": count("kind"),
            "nest_stood": sum(1 for r in rows if r.get("nest_exists")), "nest_absent": sum(1 for r in rows if not r.get("nest_exists"))}
