"""Layered Goals Phase 6 (D-0768): the what-changed record. SHADOW ONLY.

When a goal he HELD ends (by any route: set down, capped, faded, resolved), a judge other than him compares the
goal's FIRST wording with where it stood at the end and records which of these happened:
    position     he now holds a stance on it that he did not hold at first
    distinction  he drew a distinction inside it that the first wording did not make
    reframing    the question being asked became a different question
    nothing      the end wording says no more than the first
This is a record of how a goal moved, never a verdict on whether he was right or whether ending it was wise, and
nothing in it reaches him or changes any state. One row per ended goal in data/logs/goal_what_changed.jsonl.

Where "the end" comes from: for a pursuit, the standing position captured at the moment the register saw it end
(goals._how_ended); for every other kind, its last stored wording (and the store's own resolution note, if any).

The model call: the register tick runs on a daemon thread, so the judging is handed to its own short-lived
thread that runs one event loop (judge_panel opens a fresh aiohttp session per call, so a private loop is fine).
Nothing waits on it. The judge is judge_panel.JUDGE_2 alone (falcon3:7b, a different family from the thinker),
asked up to three yes/no questions in a fixed order, since judge_panel._ask answers one boolean at a time.
Prompt registered as P-0130 (prompt_registry.py).
"""
from __future__ import annotations

import json
import logging
import threading
import time
from pathlib import Path

logger = logging.getLogger(__name__)

WHAT_CHANGED_SHADOW = True      # kill switch: False -> nothing is queued, nothing is asked
MAX_PER_TICK = 4                # an ended burst beyond this is logged as skipped, not judged
KINDS = ("position", "distinction", "reframing")
JUDGE_TIMEOUT_S = 120
JUDGE_NUM_PREDICT = 200
SCHEMA = 1

_ask_fn = None                  # test hook: (system, user, key) -> (verdict, why, err, elapsed_s)
_threads: set = set()

_COMMON = ("You are shown ONE thing a mind was holding (a question, a stand, a want or a line of inquiry) as it "
           "first worded it, and where it stood when the mind stopped holding it. You see nothing else. You are "
           "not asked whether the mind was right, or whether stopping was wise; only whether the later state "
           "differs from the first wording in one specific way. Do not tilt either way. ")
_TAIL = ' Answer ONLY JSON: {"%s": true or false, "why": "one sentence"}'

SYSTEMS = {
    "position": _COMMON + ("Question: at the end, does the mind state a stance, answer or conclusion about the "
                           "thing that the first wording did not contain?" + _TAIL % "position"),
    "distinction": _COMMON + ("Question: at the end, does the mind separate two things inside the topic (a "
                              "difference, a 'not X but Y') that the first wording did not separate?" + _TAIL % "distinction"),
    "reframing": _COMMON + ("Question: at the end, is the mind asking a different question from the first "
                            "wording, about a different thing or at a different level, rather than the same one?" + _TAIL % "reframing"),
}


def log_path() -> Path:
    from core import goals
    return goals._p("logs", "goal_what_changed.jsonl")


def end_record(old: dict, standing: str = "", note: str = "") -> dict:
    """What the judge needs from an ended register goal: id, kind, first wording, and the end state of the thing."""
    texts = [t.get("text") for t in (old.get("texts") or []) if isinstance(t, dict) and t.get("text")]
    first = (texts[0] if texts else old.get("text") or "").strip()
    last = (texts[-1] if texts else old.get("text") or "").strip()
    end = " ".join((standing or "").split()) or last
    return {"id": old.get("id"), "kind": old.get("kind"), "first": first[:400], "end": end[:400],
            "end_source": "standing" if standing else "last_wording", "how_ended": old.get("state"),
            "why_ended": (old.get("ended_why") or "")[:160], "note": (note or "")[:300],
            "reworded": len(texts) > 1}


def eligible(old: dict) -> bool:
    """Only a goal that was actually held is compared; a candidate that never earned recurrence has no 'where it
    stood' worth recording."""
    return any(s.get("state") in ("held", "deferred", "engaged", "rested") for s in (old.get("states") or []))


def _user(rec: dict) -> str:
    return (f"FIRST WORDING: {rec['first']}\n\nWHERE IT STOOD AT THE END: {rec['end']}"
            + (f"\n\nHOW IT ENDED: {rec['note']}" if rec.get("note") else ""))


async def _default_ask(system: str, user: str, key: str):
    import aiohttp
    from core import judge_panel
    async with aiohttp.ClientSession() as s:
        return await judge_panel._ask(s, judge_panel.JUDGE_2, system, user, key,
                                      timeout=JUDGE_TIMEOUT_S, num_predict=JUDGE_NUM_PREDICT)


async def judge_one(rec: dict) -> dict:
    """The row for one ended goal. Never raises. 'nothing' only when all three questions were answered no."""
    row = {"ts": round(time.time(), 1), "schema": SCHEMA, "id": rec["id"], "kind": rec["kind"],
           "first": rec["first"], "end": rec["end"], "end_source": rec["end_source"],
           "how_ended": rec["how_ended"], "recorded": None, "kinds": [], "unjudged": []}
    try:
        if rec["first"] == rec["end"]:
            row.update({"recorded": "nothing", "how": "identical"})      # no model needed: same words
            return row
        fn = _ask_fn or _default_ask
        user = _user(rec)
        whys = {}
        for k in KINDS:
            try:
                v, why, err, _el = await fn(SYSTEMS[k], user, k)
            except Exception as exc:
                v, why, err = None, None, f"exception:{type(exc).__name__}"
            if v is None:
                row["unjudged"].append(k)
            elif v:
                row["kinds"].append(k)
                whys[k] = (why or "")[:200]
        row["why"] = whys
        if row["kinds"]:
            row["recorded"] = row["kinds"][0]            # the fixed order position > distinction > reframing
        elif not row["unjudged"]:
            row["recorded"] = "nothing"
        else:
            row["recorded"] = None                       # a judge was down: not 'nothing', not anything
        row["how"] = "judge2"
    except Exception as exc:
        row["how"] = f"error:{type(exc).__name__}"
    return row


def _write(rows: list[dict]) -> None:
    from core import profile
    lp = profile.guard_path(log_path())
    lp.parent.mkdir(parents=True, exist_ok=True)
    with open(lp, "a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _work(recs: list[dict]) -> None:
    import asyncio

    async def _all():
        out = []
        for rec in recs:
            out.append(await judge_one(rec))
        return out
    try:
        rows = asyncio.run(_all())
        _write(rows)
    except Exception as exc:                              # includes NonLiveWriteError: logged, never raised
        logger.warning("[goal_change] what-changed pass failed (non-fatal): %s: %s", type(exc).__name__, exc)


def record_later(recs: list[dict], wait: bool = False) -> bool:
    """Hand ended-goal records to a private thread for judging. Never raises; returns True if anything queued.
    `wait` is for tests: join the thread before returning."""
    try:
        if not (WHAT_CHANGED_SHADOW and recs):
            return False
        recs = [r for r in recs if r.get("id")]
        keep, skipped = recs[:MAX_PER_TICK], recs[MAX_PER_TICK:]
        if skipped:
            _write([{"ts": round(time.time(), 1), "schema": SCHEMA, "id": r["id"], "kind": r["kind"],
                     "recorded": None, "how": "skipped_burst"} for r in skipped])
        if not keep:
            return False
        t = threading.Thread(target=_work, args=(keep,), name="goal-what-changed", daemon=True)
        _threads.add(t)
        t.start()
        if wait:
            t.join(30)
        _threads.discard(t) if not t.is_alive() else None
        return True
    except Exception as exc:
        logger.debug("[goal_change] not queued: %r", exc)
        return False


def stats(tail_bytes: int = 2_000_000) -> dict:
    """For the hand read: how often each outcome was recorded."""
    from core import goals
    rows = goals._tail_jsonl(log_path(), tail_bytes)
    out = {"rows": len(rows)}
    for r in rows:
        k = r.get("recorded") or ("unjudged" if r.get("how") != "skipped_burst" else "skipped")
        out[k] = out.get(k, 0) + 1
    return out
