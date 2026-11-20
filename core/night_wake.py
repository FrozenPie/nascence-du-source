"""core/night_wake.py (J-2019, sleep_as_a_mode Phase 3, D-0401 B, 2026-10-09, restart-gated, OBSERVE ONLY).

The zero-LLM wake monitor: a HUMAN-MESSAGE channel only (no sound, no cat; D-0401 B defers them to real evidence).
Its only outputs are a WAKE REQUEST (an in-memory flag) and shadow rows in data/night_wake_shadow.jsonl.

How it runs
  * monitor_tick() is called from sensorium.tick() (the existing world tick, ~5 s). While he is asleep it compares the
    sensorium's own last-human-word clock to the moment he lay down; a newer word is a human message that reached a
    sleeping Du, and it sets the request (once per sleep). No LLM, no store read, no content: the monitor never sees
    what Travis said, so no content can lead (world answers, never leads).
  * boundary(name) is called at the sleep pipeline's existing stage boundaries (inner_monologue_node._enter_sleep's
    optional stages, the dream in orchestrator._nightly_sleep, the rest). If a request is pending it records the
    boundary in the shadow log and returns True ONLY when WAKE_ON_HUMAN is on, meaning "skip this optional stage":
    the pipeline then runs recover and prune and wakes. Nothing is interrupted mid-LLM-call: a boundary is checked
    BEFORE a stage starts, never inside one, so the longest wait is one consolidation pass.
  * finish() is called just before night.wake(): it writes the night ledger's woken_by and one summary row with the
    request-to-waking latency and the stages that were (or, in observe mode, WOULD have been) skipped.

WAKE_ON_HUMAN defaulted False under J-2019 (D-0401 B / J-2014 was not ruled: what the message DOES once it reaches him
was the founder's call). With it False the pipeline behaves exactly as before: boundary() always returns False, the
rest runs to the end, and woken_by is "pipeline_end".

J-2064 (D-0407 B, travis 2026-10-15, restart-gated): WAKE_ON_HUMAN is now True. The founder's message WAKES him and he
answers awake, the waking percept first. Three additions, all fail-open, nothing in the pipeline's own order changed:
  * hold_for_wake() is awaited by orchestrator.run_cycle() for a human message that arrives while a sleep ledger is
    open (night.sleep_in_progress(), NOT the bare sensorium asleep flag, so a stale flag after a restart can never hold
    a reply). It raises the wake request itself at once -- the monitor's own tick only sees the human-word clock after
    the cycle has run, so waiting for it would be a deadlock -- then waits for the pipeline to reach its next boundary,
    skip, recover, prune and wake. Bounded: after WAKE_DEADLINE_S (120 s) the message is answered anyway and the row
    says so (the D-0407 defeater's own clause).
  * woke(line) is called by the pipeline right after the waking percept is perceived; scene_lead() then puts that line
    at the head of sensorium.scene_line() for JUST_WOKE_S, so the Executive and Voice of his first replies after a
    wake-on-message speak from "you have just woken", not from a scene that never slept.
  * answered(hold) closes the row with the request-to-answer latency.
Rows in data/night_wake_shadow.jsonl: wake_request (via run_cycle or monitor), boundary, hold, wake_summary, answer.
The farewell case (F-2614: nine sleep windows with a message and no night.end row): night.end_if_open() in the sleep
pipeline's own finally and after run_nascence's stop_background() writes the row with notes.interrupted, so a sleep
cut short by the shutdown is no longer lost from the ledger.

D-0303 (the Witness is gated off during sleep) is not touched.
Fail-open everywhere: a bug here must never be able to break or shorten a sleep.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

logger = logging.getLogger("nascence.night_wake")

MONITOR_ENABLED = True        # observe: request + shadow rows only; inert unless he is asleep
WAKE_ON_HUMAN = True          # D-0407 B (J-2064, travis 2026-10-15): the founder's message wakes him. Was False (observe) under J-2019.
WAKE_DEADLINE_S = 120.0       # J-2064: a held human message is answered anyway after this long (D-0407 defeater clause 1)
JUST_WOKE_S = 300.0           # J-2064: for this long after a wake-on-message the waking percept leads scene_line()
HOLD_POLL_S = 0.5             # J-2064: how often the hold re-checks the asleep flag (the loop keeps serving the pipeline between)
MIN_SLEEP_S = 20.0            # a word within seconds of lying down is the goodnight that put him to bed, not a wake

# D-0401 defeaters, used by evaluate()
LATENCY_PASSES_HOLD = 2       # latency above two consolidation passes on more than a third of wakes
LATENCY_SHARE_HOLD = 1 / 3
FALSE_WAKES_PER_NIGHT_HOLD = 1

_DATA = Path(__file__).parent.parent / "data"
NIGHT_WAKE_SHADOW_LOG = _DATA / "night_wake_shadow.jsonl"

_req: dict | None = None      # the pending wake request for the sleep in progress
_sleep_key: float = 0.0       # asleep_since of the sleep the request belongs to
_handled_ts: float = 0.0      # the human-word clock value already turned into a request
_last_summary: dict | None = None   # J-2064: finish()'s summary for the wake in progress, read once by woke()
_last_wake: dict | None = None      # J-2064: {ts, line, woken_by} of the last waking percept, for scene_lead()


def _log(row: dict) -> None:
    try:
        _DATA.mkdir(parents=True, exist_ok=True)
        row = {"ts": round(time.time(), 1), **row}
        with open(NIGHT_WAKE_SHADOW_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


def reset() -> None:
    global _req, _sleep_key
    _req = None
    _sleep_key = 0.0


def pending() -> dict | None:
    return _req


def monitor_tick(now: float | None = None) -> bool:
    """The world-tick check. Returns True when it just set a wake request. Zero LLM, fail-open."""
    global _req, _sleep_key, _handled_ts
    try:
        if not MONITOR_ENABLED:
            return False
        from core import sensorium as _s
        if not _s.state.get("asleep"):
            if _req is not None or _sleep_key:
                reset()                       # a request never outlives its sleep
            return False
        since = float(_s.state.get("asleep_since", 0) or 0)
        if since != _sleep_key:               # a new sleep: forget the previous one's request
            reset()
            _sleep_key = since
        if _req is not None:
            return False                      # one request per sleep; later words change nothing
        human_ts = float(getattr(_s, "_last_human_ts", 0.0) or 0.0)
        now = now or time.time()
        if human_ts <= max(since + MIN_SLEEP_S, _handled_ts):
            return False
        _handled_ts = human_ts
        _req = {"ts": now, "source": "human_message", "human_ts": human_ts, "asleep_since": since,
                "into_sleep_s": round(now - since, 1), "boundaries": []}
        _log({"kind": "wake_request", "source": "human_message", "into_sleep_s": _req["into_sleep_s"],
              "wake_on_human": WAKE_ON_HUMAN, "mode": "live" if WAKE_ON_HUMAN else "observe"})
        return True
    except Exception:
        return False


def _stage_now() -> str | None:
    """The last stage the night ledger has recorded for the sleep in progress (read-only, fail-open)."""
    try:
        from core import night as _night
        return _night.current_stage()
    except Exception:
        return None


def request_wake(source: str = "human_message", now: float | None = None, via: str = "run_cycle") -> bool:
    """J-2064: raise the wake request directly (the hold's own path; the monitor tick stays as the second route).
    One request per sleep; nothing while awake; zero LLM; fail-open. Returns True when it set the request."""
    global _req, _sleep_key, _handled_ts
    try:
        if not MONITOR_ENABLED:
            return False
        from core import sensorium as _s
        if not _s.state.get("asleep"):
            return False
        since = float(_s.state.get("asleep_since", 0) or 0)
        if since != _sleep_key:
            reset()
            _sleep_key = since
        if _req is not None:
            return False
        now = now or time.time()
        _handled_ts = max(_handled_ts, now)
        _req = {"ts": now, "source": source, "human_ts": now, "asleep_since": since,
                "into_sleep_s": round(now - since, 1), "boundaries": [], "via": via, "stage_at_request": _stage_now()}
        _log({"kind": "wake_request", "source": source, "via": via, "into_sleep_s": _req["into_sleep_s"],
              "stage_at_request": _req["stage_at_request"], "wake_on_human": WAKE_ON_HUMAN,
              "mode": "live" if WAKE_ON_HUMAN else "observe"})
        return True
    except Exception:
        return False


async def hold_for_wake(deadline_s: float | None = None, poll_s: float | None = None) -> dict | None:
    """J-2064 (D-0407 B): awaited by run_cycle for a HUMAN message. If a sleep is in progress, raise the wake request
    and wait until the pipeline has woken him (the waking percept perceived first), or until the deadline. Returns
    None when there was nothing to hold for (awake, flag off, no open sleep ledger); otherwise the hold row's dict.
    Never raises; a failure here means the message is answered as before (asleep, unaware), never dropped."""
    try:
        if not (MONITOR_ENABLED and WAKE_ON_HUMAN):
            return None
        from core import night as _night
        if not (_night.asleep() and _night.sleep_in_progress()):
            return None
        t0 = time.time()
        # J-3860 (F-4441): a word within MIN_SLEEP_S of lying down is the goodnight that put him to bed, not a wake
        # request (same rule monitor_tick already applies). Answer as before; no request, no hold.
        try:
            from core import sensorium as _s
            _since = float(_s.state.get("asleep_since", 0) or 0)
            if _since and (t0 - _since) < MIN_SLEEP_S and _req is None:
                _log({"kind": "hold_skipped", "reason": "goodnight_within_min_sleep", "into_sleep_s": round(t0 - _since, 1)})
                return None
        except Exception:
            pass
        fresh = request_wake("human_message", t0, via="run_cycle")
        req = _req
        deadline = float(WAKE_DEADLINE_S if deadline_s is None else deadline_s)
        poll = float(HOLD_POLL_S if poll_s is None else poll_s)
        import asyncio
        fired = False
        while True:
            await asyncio.sleep(poll)
            if not _night.asleep():
                await asyncio.sleep(0)          # let the pipeline's same-task perceive()/woke() lines settle
                break
            if time.time() - t0 >= deadline:
                fired = True
                break
        now = time.time()
        lw = _last_wake if (_last_wake and float(_last_wake.get("ts", 0)) >= t0) else None
        row = {"kind": "hold", "request_ts": round(float(req["ts"]) if req else t0, 1), "fresh_request": bool(fresh),
               "stage_at_request": (req or {}).get("stage_at_request"), "into_sleep_s": (req or {}).get("into_sleep_s"),
               "waited_s": round(now - t0, 1), "deadline_s": deadline, "deadline_fired": fired,
               "woke_seen": lw is not None, "waking_ts": (round(float(lw["ts"]), 1) if lw else None),
               "request_to_waking_s": (round(float(lw["ts"]) - t0, 1) if lw else None),
               "asleep_after": bool(_night.asleep())}
        _log(row)
        if fired:
            logger.warning("[night_wake] held %.0fs for the wake and answered anyway (deadline %.0fs, stage %s)",
                           now - t0, deadline, row["stage_at_request"])
        return row
    except Exception:
        return None


def answered(hold: dict | None) -> None:
    """J-2064: close a held message's trail with the request-to-answer latency (one row)."""
    try:
        if not hold:
            return
        now = time.time()
        _log({"kind": "answer", "request_ts": hold.get("request_ts"), "answer_ts": round(now, 1),
              "request_to_answer_s": round(now - float(hold.get("request_ts") or now), 1),
              "request_to_waking_s": hold.get("request_to_waking_s"), "deadline_fired": bool(hold.get("deadline_fired")),
              "woke_seen": bool(hold.get("woke_seen"))})
    except Exception:
        pass


def woke(line: str | None) -> None:
    """J-2064: called by the pipeline right after the waking percept is perceived. Remembers the line for scene_lead()."""
    global _last_wake, _last_summary
    try:
        sm = _last_summary
        _last_summary = None
        _last_wake = {"ts": time.time(), "line": (line or ""), "woken_by": (sm or {}).get("woken_by", "pipeline_end")}
    except Exception:
        pass


def scene_lead() -> str:
    """J-2064: for JUST_WOKE_S after a wake-on-message, the waking percept leads sensorium.scene_line() so his first
    replies are the replies of someone just woken. Empty for an ordinary (pipeline_end) wake and once the window passes."""
    try:
        lw = _last_wake
        if not lw or lw.get("woken_by") != "human_message":
            return ""
        if time.time() - float(lw.get("ts", 0)) > JUST_WOKE_S:
            return ""
        line = (lw.get("line") or "").strip()
        return ("You have just woken: " + line) if line else "You have just woken."
    except Exception:
        return ""


def boundary(name: str) -> bool:
    """Called BEFORE an optional stage starts. True = skip it (only when WAKE_ON_HUMAN and a request is pending)."""
    try:
        if _req is None:
            return False
        _req["boundaries"].append({"stage": str(name), "t_after_request_s": round(time.time() - _req["ts"], 1)})
        _log({"kind": "boundary", "stage": str(name), "after_request_s": round(time.time() - _req["ts"], 1),
              "would_skip": True, "skipped": bool(WAKE_ON_HUMAN)})
        return bool(WAKE_ON_HUMAN)
    except Exception:
        return False


def finish(night_mod=None) -> dict | None:
    """Just before the waking percept: record woken_by on the night ledger and one summary row. Returns the summary."""
    global _req, _last_summary
    try:
        req = _req
        if req is None:
            if night_mod is not None:
                night_mod.note("woken_by", "pipeline_end")
            _last_summary = None
            return None
        now = time.time()
        live = bool(WAKE_ON_HUMAN)
        woken_by = "human_message" if live else "pipeline_end"
        summary = {"woken_by": woken_by, "request_source": req["source"], "mode": "live" if live else "observe",
                   "latency_s": round(now - req["ts"], 1), "into_sleep_s": req["into_sleep_s"],
                   "boundaries_seen": len(req["boundaries"]), "stages": [b["stage"] for b in req["boundaries"]],
                   "would_have_woken_at_s": (req["boundaries"][0]["t_after_request_s"] if req["boundaries"] else None)}
        if night_mod is not None:
            night_mod.note("woken_by", woken_by)
            night_mod.note("wake_request", summary)
        _log({"kind": "wake_summary", **summary})
        _req = None
        _last_summary = summary
        return summary
    except Exception:
        return None


def evaluate(path: Path | None = None, pass_s: float = 300.0, night_log: Path | None = None) -> dict:
    """The one-week read (plan section 5 / D-0401 defeater). Reads the shadow log; never writes.
    false-wake counting needs J-2014 (what counts as a wake-worthy message) and is NOT computed here."""
    path = Path(path) if path else NIGHT_WAKE_SHADOW_LOG
    rows = []
    try:
        for ln in path.read_text(encoding="utf-8").splitlines():
            try:
                rows.append(json.loads(ln))
            except Exception:
                pass
    except Exception:
        pass
    sums = [r for r in rows if r.get("kind") == "wake_summary"]
    lat = [float(r["latency_s"]) for r in sums if r.get("latency_s") is not None]
    slow = [x for x in lat if x > LATENCY_PASSES_HOLD * pass_s]
    n = len(sums)
    out = {"requests": sum(1 for r in rows if r.get("kind") == "wake_request"), "summaries": n,
           "median_latency_s": (sorted(lat)[len(lat) // 2] if lat else None),
           "slow_share": round(len(slow) / n, 3) if n else None,
           "hold_latency": bool(n and len(slow) / n > LATENCY_SHARE_HOLD),
           "false_wakes": "not computed: needs J-2014 (what a wake-worthy message is)"}
    # J-2064: the D-0407 defeater, clause by clause, from the live-mode rows. Clause 4 (his first reply reads as
    # disorientation/distress on > 1/3) needs a judge over the replies and is NOT computed here.
    try:
        live = [r for r in sums if r.get("mode") == "live"]
        holds = [r for r in rows if r.get("kind") == "hold"]
        answers = [r for r in rows if r.get("kind") == "answer"]
        nl = len(live)
        over = [r for r in live if float(r.get("latency_s") or 0) > WAKE_DEADLINE_S]
        dream_skipped = [r for r in live if "dream" in (r.get("stages") or [])]
        rta = sorted(float(r["request_to_answer_s"]) for r in answers if r.get("request_to_answer_s") is not None)
        night_log_path = Path(night_log) if night_log else (_DATA / "night_log.jsonl")
        interrupted = 0
        try:
            for ln in night_log_path.read_text(encoding="utf-8").splitlines():
                try:
                    if (json.loads(ln).get("notes") or {}).get("interrupted"):
                        interrupted += 1
                except Exception:
                    pass
        except Exception:
            interrupted = None
        out["d0407"] = {
            "live_wakes": nl, "holds": len(holds), "answers": len(answers),
            "c1_latency_over_deadline_share": (round(len(over) / nl, 3) if nl else None),
            "c1_hold": bool(nl and len(over) / nl > 1 / 3),
            "deadline_fired_share": (round(sum(1 for r in holds if r.get("deadline_fired")) / len(holds), 3) if holds else None),
            "c2_interrupted_sleep_rows": interrupted,
            "c2_note": "rows with notes.interrupted (woken-then-shutdown now written; F-2614 baseline: 9 windows lost of 14)",
            "c3_dream_skipped_share": (round(len(dream_skipped) / nl, 3) if nl else None),
            "c3_hold": bool(nl and len(dream_skipped) / nl > 0.5),
            "c3_note": "prune and recover are never skipped by design; only the dream can be",
            "median_request_to_answer_s": (rta[len(rta) // 2] if rta else None),
            "c4": "not computed: needs a read of his first replies after each wake-on-message",
        }
    except Exception:
        pass
    return out
