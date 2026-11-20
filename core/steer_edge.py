"""
Nascence -- edge-triggered affective steers (J-1955 / D-0368 option A, F-1927)
=============================================================================
F-1927: repeating an INFORMATIONAL line (scene, memory, book) does not leak into Du's thoughts, but repeating an
AFFECTIVE VERDICT does -- the boredom 'sick of this' sentence alone was delivered ~12,000 times, and the
frustration/circling vocabulary in his thoughts (5.6% -> 25-37%) tracked the steers' own firing share.

Rule (founder, D-0368): an affective steer fires only on a REAL CHANGE OF STATE -- the same discipline as
mood.felt_preamble's EMA gate -- never on every prompt while a state merely persists.

`fires(key, state)`:
  * `state` is a hashable label of the steer's current condition ("sick", ("lap", "high"), True ...), or a falsy
    value (None / "" / False) when the steer is not applicable right now;
  * returns True on the EDGE only: the first evaluation after the steer was inactive, or after `state` changed
    (e.g. a boredom tier rising or falling);
  * while the SAME state persists it returns False, except for one bounded REMINDER every REMIND_S seconds
    (so a state that genuinely lasts for hours is not silenced for ever -- D-0368's defeater: 'an edge-triggered
    steer silences a state Travis wanted Du to keep feeling'). REMIND_S is the single tuning knob.
Memory is in-process (a restart re-fires each live steer once, which is correct: it is news after a restart).
Every evaluation of an ACTIVE state is also appended to data/steer_edge_log.jsonl (fired true/false), so the
firing share stays measurable the way felt_preamble_log.jsonl keeps the EMA gate measurable. Never raises:
on any error it fails OPEN to the old behaviour (True).
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)

REMIND_S = 7200.0            # a persisting state may be re-stated at most once per 2 h (was: every prompt)
_LOG = Path(__file__).parent.parent / "data" / "steer_edge_log.jsonl"
LOG_ENABLED = True           # tests / replays set False so nothing is appended anywhere

_last: dict = {}             # key -> {"state": ..., "fired_ts": float}


def reset() -> None:
    _last.clear()


def fires(key: str, state, now: float | None = None, remind_s: float | None = None,
          rank: int | None = None, rearm_s: float = 0.0) -> bool:
    """True iff the steer `key` should be delivered in this prompt (see module docstring). Fail-open.

    rank:    optional ordinal of `state` (higher = stronger, e.g. boredom mild=1 < tired=2 < sick=3). With a rank the
             gate is HYSTERETIC: it fires on entry and on an ESCALATION above the highest rank already stated in
             this episode; a fall back to a lower rank (level hovering round a threshold) is not news.
    rearm_s: how long the steer must stay inactive before the episode counts as over (0 = immediately). A brief gap
             -- a prompt where a train-hold or the escape line suppressed it -- must not re-arm the gate."""
    try:
        t = time.time() if now is None else float(now)
        rem = REMIND_S if remind_s is None else float(remind_s)
        prev = _last.get(key)
        if not state:                                  # inactive: re-arm once it has stayed inactive long enough
            if prev is not None:
                if prev.get("gone_ts") is None:
                    prev["gone_ts"] = t
                if t - prev["gone_ts"] >= rearm_s:
                    _last.pop(key, None)
            return False
        if prev is not None:
            prev["gone_ts"] = None                     # it is active again: the gap (if any) was a blip
        r = rank if rank is not None else 0
        if prev is None:
            fire, why = True, "edge"
        elif rank is not None:
            fire, why = (r > prev["rank"]), "escalation"
        else:
            fire, why = (prev["state"] != state), "edge"
        if not fire and t - prev["fired_ts"] >= rem:
            fire, why = True, "reminder"
        elif not fire:
            why = "persisting"
        if fire:
            _last[key] = {"state": state, "rank": r, "fired_ts": t, "gone_ts": None}
        elif prev is not None and rank is not None:
            prev["state"] = state                      # follow the level down; the high-water rank stays
        _log(t, key, state, fire, why)
        return fire
    except Exception as exc:                           # never break a prompt build
        logger.debug("[steer_edge] failed open (non-fatal): %s", exc)
        return True


def _log(t: float, key: str, state, fired: bool, why: str) -> None:
    if not LOG_ENABLED:
        return
    try:
        _LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": round(t, 1), "key": key, "state": str(state),
                                "fired": bool(fired), "why": why}, ensure_ascii=False) + "\n")
    except Exception:
        pass
