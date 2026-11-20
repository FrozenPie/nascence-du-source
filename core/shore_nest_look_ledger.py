"""
core/shore_nest_look_ledger.py -- an observe-only ledger of the shore's NEST LOOK answers (one row per look_nest hit)
==================================================================================================================
2026-10-16 (J-2227, F-2917; D-0345's place look, J-1774 build).

WHY. D-0345's defeater for the shore's nest look is 'a nest line shown while no nest, or find-none while a nest stands'. F-2917 (J-1796's read)
found the place's answer is logged NOWHERE: hands_trace observe rows carry no answer, and nascence.log, llm_calls.jsonl, thought_station_log.jsonl
and scene_extra_ledger.jsonl hold neither 'in the scrape three eggs' nor 'and find none' -- so the defeater could only be RECONSTRUCTED by
replaying the targets through the real functions. This ledger makes it readable: sensorium._shore_look calls record() once, right before it
returns a non-empty shore_life.look_nest() answer, and nowhere else.

ROW.
    {"ts": 1792040548.0,                # time of the write (epoch s to 0.1 s: the scene_extra_ledger / nest_gate_shadow convention)
     "kind": "nest_look",
     "target": "the eggs",              # the look text, cut at 60 characters (life_events.jsonl's convention)
     "noun": "eggs",                    # shore_life.nest_look_noun(target): the nest noun he used, as typed
     "nest_exists": true,               # shore_life.nest_state() read at the look: whether the oystercatcher's nest stood ...
     "eggs": 3,                         # ... and its egg count as held (None when no nest or no count)
     "line": "You pick your way up ...",# the answer the place returned, exactly (cut at 240 characters)
     "consistent": true}                # line == shore_life.nest_look_line(noun, nest state as read here); false = the state moved between the look and this read
The noun and the nest state are re-read here by the same pure reads look_nest uses (nest_look_noun is a regex walk, nest_state a bare json read --
no random draw, no write); `consistent` says whether that re-read reproduces the line the place actually gave.

RULES (pinned by scripts/_test_j2227_shore_nest_look_noun_and_ledger.py).
  * Observe-only: record() returns a bool nobody reads, draws no random number, writes no state but its own row, and is called AFTER the answer
    is fixed; the look returns the same line with the ledger on, off, broken or refused.
  * Fail-open: record() swallows everything, including the D-0179 write fence's NonLiveWriteError, and the call site in sensorium is wrapped too.
  * World-store write fence (J-0610 / D-0179): the path goes through profile.guard_path() (core/nest_gate_shadow.py's convention), so only the live
    Du boot, a lab_env.isolate() sandbox or a path redirected outside data/ can write; any other process gets False and no file.
  * One writer lock: the append happens under _LOCK (a look can come from the monologue's thread and from the chat's perception branch).
  * ENABLED is the one switch: False and record() is a no-op.
  * No readout: nothing here is read by Du or reaches a prompt (D-0434). It is for the session that reads D-0345's defeater.

Read side: read_rows() and status() -- read-only, tolerate a torn last line and a missing file, never raise.
"""
from __future__ import annotations

import json
import logging
import threading
import time
from pathlib import Path

from core import profile

logger = logging.getLogger("nascence.shore_nest_look_ledger")

ENABLED = True
_DATA = Path(__file__).parent.parent / "data"
_LEDGER = _DATA / "shore_nest_looks.jsonl"
_LOCK = threading.Lock()


def build_row(target, line) -> dict:
    """The row record() would append for a look at `target` the place answered with `line`. Pure reads only; may raise (record() catches)."""
    from core import shore_life as _shl
    noun = _shl.nest_look_noun(target)
    nest = _shl.nest_state()
    eggs = nest.get("eggs") if isinstance(nest, dict) else None
    line = str(line or "")
    return {"ts": round(time.time(), 1), "kind": "nest_look", "target": str(target or "")[:60], "noun": noun,
            "nest_exists": bool(nest), "eggs": eggs if (type(eggs) is int) else None, "line": line[:240],
            "consistent": line == _shl.nest_look_line(noun, nest)}


def record(target, line) -> bool:
    """Append one row for a shore nest look that answered `line`. True iff a row was written; False -- never an exception -- otherwise."""
    try:
        if not ENABLED or not line:
            return False
        row = build_row(target, line)
        # D-0179: the real data/ only for the live Du boot; a non-live process is refused here, before any I/O.
        path = profile.guard_path(_LEDGER)
        with _LOCK:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return True
    except Exception as exc:     # incl. profile.NonLiveWriteError: a non-live process records nothing, quietly
        logger.debug("[shore_nest_look_ledger] row not written (non-fatal): %s", exc)
        return False


def read_rows(since_ts: float = 0.0, path=None) -> list:
    """Every parsable row with ts >= since_ts, oldest first. A torn or garbled line is skipped; a missing ledger is []."""
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
                try:
                    ts = float(row.get("ts") or 0.0) if isinstance(row, dict) else -1.0
                except Exception:
                    ts = 0.0
                if isinstance(row, dict) and ts >= since_ts:
                    out.append(row)
    except Exception:
        pass
    return out


def status(path=None) -> dict:
    """{path, rows, first_ts, last_ts, by_noun, nest_stood, nest_absent, nest_line_while_absent, find_none_while_stood, inconsistent} -- D-0345's
    defeater arms counted directly: a scrape-and-eggs line on a row whose nest did not stand, or a 'find none' line on a row whose nest stood."""
    p = Path(path) if path is not None else _LEDGER
    rows = read_rows(0.0, p)
    by_noun: dict = {}
    for r in rows:
        k = str(r.get("noun", ""))
        by_noun[k] = by_noun.get(k, 0) + 1
    tss = []
    for r in rows:
        try:
            tss.append(float(r.get("ts") or 0.0))
        except Exception:
            pass
    nest_line = lambda r: "in the scrape" in str(r.get("line", ""))          # noqa: E731
    find_none = lambda r: str(r.get("line", "")).endswith("and find none.")  # noqa: E731
    return {"path": str(p), "rows": len(rows), "first_ts": min(tss) if tss else None, "last_ts": max(tss) if tss else None, "by_noun": by_noun,
            "nest_stood": sum(1 for r in rows if r.get("nest_exists")), "nest_absent": sum(1 for r in rows if not r.get("nest_exists")),
            "nest_line_while_absent": sum(1 for r in rows if nest_line(r) and not r.get("nest_exists")),
            "find_none_while_stood": sum(1 for r in rows if find_none(r) and r.get("nest_exists")),
            "inconsistent": sum(1 for r in rows if r.get("consistent") is False)}
