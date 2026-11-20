"""
Nascence -- SPEECH vs THOUGHT call-level timing shadow (J-1971, F-2573, D-0372).
docs/staged/speech_thought_concurrency.md section 3-4.

QUESTION: how often does a human cycle arrive while a hot-lane monologue LLM call is in flight, and
how long does speech wait because of it?  trains_log.jsonl rows are thought-THREAD spans (minutes),
not single calls, so only a call-level log can answer (F-2573).

WHAT THIS DOES (observe-only, nothing rides, fail-open, never raises into a caller):
  * log_call(...)  -- one row per hot-lane (:11433) LLM call, from core/model_client.call_node:
        {ev:"call", by, t_req, t_start, t_end, ok}   (wall-clock epoch seconds)
        t_req   = call entered call_node (before waiting for the lane slot)
        t_start = lane slot acquired (the model is actually ours)
        t_end   = response parsed / call failed
  * log_human(cycle_id) -- one row per human-cycle arrival, from core/orchestrator:
        {ev:"human", t, cycle}
Both append to its OWN new store data/speech_timing_shadow.jsonl (never an existing live log).

RESTART-GATED: Python imports are fixed at process start, so this takes effect only on Du's next
boot. Kill switch: ENABLED = False. LAB MODE (core.telemetry._LAB_MODE) writes nothing.

WRITE FENCE (J-2241, F-2933): _append() resolves its path through core.profile.guard_path() (D-0179),
so only the one real live Du boot (profile.mark_live(), scripts/run_nascence.py) or a path redirected
into a lab_env.isolate() sandbox / outside data/ can write. Before this, the ONLY lab guard was
telemetry._LAB_MODE, which lab_env.isolate() does not set and which caller-side telemetry no-op lists
(the F-1683 pattern: they name log_llm_call/log_thought_station/log_llm_latency, not this later 4th
writer) never reach -- 2026-10-16, after Du stopped, two lab scripts (si_open_doubt_cup_replay_v2:175
x120 under isolate(), j0791:640 x1) appended 121 ev=call rows to the live store. A refused write is
swallowed by log_call/log_human's own fail-open net: nothing ever raises into model_client/orchestrator.

READ: python -m core.speech_timing_shadow   (reader below, pure, writes nothing). Evaluate only after
7+ days of uptime against the plan's pre-registered 5 percent kill criterion; this module approves
no option in the plan's section 2.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

ENABLED = True
_ROOT = Path(__file__).parent.parent
_LOG = _ROOT / "data" / "speech_timing_shadow.jsonl"
HOT_PORT = ":11433"
KILL_CRITERION = 0.05          # plan section 4: park if collision rate < 5 percent


def _lab() -> bool:
    try:
        from core import telemetry as _t
        return bool(getattr(_t, "_LAB_MODE", False))
    except Exception:
        return False


def _append(row: dict, path: Path | None = None) -> None:
    p = path or _LOG
    # J-2241 / F-2933: non-live process -> NonLiveWriteError (caught fail-open by the callers below).
    from core import profile as _profile
    p = _profile.guard_path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, separators=(",", ":")) + "\n")


def log_call(base_url: str, caller: str, t_req: float, t_start: float | None,
             t_end: float, ok: bool) -> None:
    """One row per hot-lane call. Non-hot lanes are ignored. Fail-open."""
    if not ENABLED or HOT_PORT not in (base_url or "") or _lab():
        return
    try:
        _append({"ev": "call", "by": (caller or "")[:70], "t_req": round(t_req, 3),
                 "t_start": round(t_start if t_start is not None else t_end, 3),
                 "t_end": round(t_end, 3), "ok": 1 if ok else 0})
    except Exception:
        pass


def log_human(cycle_id: str = "") -> None:
    """One row per human-cycle arrival. Fail-open."""
    if not ENABLED or _lab():
        return
    try:
        _append({"ev": "human", "t": round(time.time(), 3), "cycle": str(cycle_id)[:8]})
    except Exception:
        pass


# ---------------------------------------------------------------- reader (pure, no writes)
def _kind(by: str) -> str:
    if "inner_monologue_node" in by:
        return "monologue"
    if "VoiceNode" in by or "voice_node" in by:
        return "speech"
    return "other"


def _pct(xs: list, q: float):
    if not xs:
        return None
    s = sorted(xs)
    return s[min(len(s) - 1, int(round(q * (len(s) - 1))))]


def load(path: Path | None = None) -> list:
    rows = []
    p = path or _LOG
    if not p.exists():
        return rows
    with open(p, encoding="utf-8") as f:
        for line in f:
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


def analyze(rows: list, speech_window_s: float = 600.0) -> dict:
    """Plan section 3 measures, per human cycle.

    collided (headline) = human arrival t falls inside a monologue call while it HOLDS the lane
                          slot [t_start, t_end]; P_collision_incl_queued also counts the time it
                          waited for the slot [t_req, t_end] (upper bound).
    wait = first speech call's t_start minus human t, for the first speech call whose t_req is in
           [t - 1s, t + speech_window_s]. Split collided vs clear; (median, p90, n).
    """
    humans = sorted(r["t"] for r in rows if r.get("ev") == "human")
    calls = [r for r in rows if r.get("ev") == "call"]
    mono = [(c["t_req"], c["t_start"], c["t_end"]) for c in calls if _kind(c["by"]) == "monologue"]
    speech = sorted((c["t_req"], c["t_start"]) for c in calls if _kind(c["by"]) == "speech")
    n = len(humans)
    coll_any = coll_hold = 0
    wc: list = []
    wn: list = []
    for t in humans:
        in_any = any(a <= t <= e for a, _s, e in mono)
        in_hold = any(s <= t <= e for _a, s, e in mono)
        coll_any += in_any
        coll_hold += in_hold
        w = next((st - t for rq, st in speech if t - 1.0 <= rq <= t + speech_window_s), None)
        if w is not None:
            (wc if in_hold else wn).append(max(0.0, w))
    p = (coll_hold / n) if n else None
    span_days = ((max(humans) - min(humans)) / 86400.0) if len(humans) > 1 else 0.0
    if n == 0 or span_days < 7:
        verdict = "insufficient data (<7 days or no human cycles)"
    else:
        verdict = "PARK (below 5 percent)" if p < KILL_CRITERION else "KEEP OPEN (>=5 percent)"
    return {
        "human_cycles": n, "monologue_calls": len(mono), "speech_calls": len(speech),
        "span_days": round(span_days, 2),
        "P_collision_holding_slot": p,
        "P_collision_incl_queued": (coll_any / n) if n else None,
        "wait_collided_median_p90_n": (_pct(wc, .5), _pct(wc, .9), len(wc)),
        "wait_clear_median_p90_n": (_pct(wn, .5), _pct(wn, .9), len(wn)),
        "kill_criterion": KILL_CRITERION, "verdict": verdict,
    }


if __name__ == "__main__":
    import pprint
    pprint.pprint(analyze(load()))
