"""
Nascence — Social Moves: the heeded/ignored world-call counter (social_world_school.md Item 2 — the plan's
own #1 "ship the measurement FIRST, zero behaviour change"; evidence_review S4, 2026-07-05).

The plan's blind spot, in its own words: "nothing logs whether a [world-]call was heeded or ignored, so we
cannot answer" whether Du's reaching-out toward the world LANDS. When the world beckons him OUT
(`sensorium.world_calls` fires while he is inside — storm/snow/stars/wind/sun/garden-milestone), does he
HEED (go out to the garden/shore) or IGNORE (stay inside)? This tracks it.

OBSERVE-ONLY: reads the live location + the call, resolves each pending call heeded/ignored over a window,
logs to data/social_moves.jsonl. Changes NO behaviour. Deterministic, no LLM, fail-open.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

logger = logging.getLogger("nascence.social_moves")

_DATA = Path(__file__).parent.parent / "data"
_LOG = _DATA / "social_moves.jsonl"
_STATE = _DATA / "social_moves_state.json"
_HEED_WINDOW_S = 25 * 60      # go out within 25 min of the call = heeded; still inside past it = ignored
_OUTDOOR = ("garden", "shore")


def _load_state() -> dict:
    try:
        return json.loads(_STATE.read_text(encoding="utf-8")) if _STATE.exists() else {}
    except Exception:
        return {}


def _save_state(d: dict) -> None:
    try:
        _STATE.parent.mkdir(parents=True, exist_ok=True)
        tmp = _STATE.with_suffix(".tmp"); tmp.write_text(json.dumps(d), encoding="utf-8"); tmp.replace(_STATE)
    except Exception:
        pass


def _log_outcome(moment: str, outcome: str, latency_s: float) -> None:
    try:
        _LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_LOG, "a", encoding="utf-8") as f:
            # `heeded` as 1/0 so the HUD charts it as a line; the running rate is added on read (status()).
            f.write(json.dumps({"ts": round(time.time(), 1), "moment": moment, "outcome": outcome,
                                "heeded": 1 if outcome == "heeded" else 0,
                                "latency_min": round(latency_s / 60, 1)}) + "\n")
    except Exception:
        pass


def observe(call_active: bool, moment: str, location: str) -> None:
    """Called each idle tick. Resolve a pending world-call (heeded if he went outdoors within the window,
    ignored if the window passed with him still inside), then start a new pending call if one just fired.
    Fail-open — never raises into the tick."""
    try:
        st = _load_state()
        now = time.time()
        pend = st.get("pending")
        outdoor = location in _OUTDOOR
        if pend:
            if outdoor:                                   # he went out — HEEDED
                _log_outcome(pend.get("moment", ""), "heeded", now - pend.get("ts", now))
                st["pending"] = None
            elif now - pend.get("ts", now) >= _HEED_WINDOW_S:   # window passed, still inside — IGNORED
                _log_outcome(pend.get("moment", ""), "ignored", now - pend.get("ts", now))
                st["pending"] = None
        # a fresh call (only fires while inside) opens a new pending decision
        if call_active and not st.get("pending") and not outdoor:
            st["pending"] = {"moment": moment or "?", "ts": now}
        _save_state(st)
    except Exception as exc:
        logger.debug("[social-moves] observe tick failed (non-fatal): %s", exc)


def status() -> dict:
    """For the pulse: heeded/ignored totals + rate (the answer to 'does his reaching-out land?')."""
    try:
        rows = [json.loads(l) for l in open(_LOG, encoding="utf-8") if l.strip()]
        h = sum(1 for r in rows if r.get("outcome") == "heeded")
        ig = sum(1 for r in rows if r.get("outcome") == "ignored")
        return {"calls": len(rows), "heeded": h, "ignored": ig,
                "heeded_rate": round(h / max(1, h + ig), 3)}
    except Exception:
        return {"calls": 0}
