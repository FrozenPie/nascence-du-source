"""
Nascence -- Ignition as promotion from the stream (docs/staged/ignition_pressure_and_time.md, "Option E";
J-2662, idea I-0138). SHADOW-FIRST, ADDITIVE, RESTART-GATED.

The idea (Orch-OR shaped): a deliberate cycle is PROMOTED out of the live stream when the held state
crosses a threshold -- it RESETS that state and leaves a RECORD -- instead of being scheduled by the
dissonance accumulator alone.

What ships here:
  1. observe()        SHADOW. Called once per idle thought from the monologue loop right after
                      stream_drive.observe(). Writes one row per stream thought to
                      data/ignition_promotion_shadow.jsonl with: the stream row's drive/progress/grounded,
                      both reservoir levels, ignition_level, which reservoir WOULD be reset, a THRESHOLD
                      GRID (0.6/0.7/0.8: which would fire; none is chosen live), `eligible` plus
                      `blocked_by` (not_building / ungrounded / level_below_grid / refractory /
                      hourly_cap; Rail B's grounding gate: anchor-less self-reflection may not promote),
                      and whether the commitment-ledger scan saw this thought (F-0808). Rows for every
                      stream thought let the read compute rates against all stream rows. It never calls
                      run_cycle and never resets a reservoir.
  2. maybe_promote()  LIVE PATH behind PROMOTION_LIVE (ships False, one constant). Hands the train's
                      current thought to run_cycle(..., input_type="internal"), resets ONLY the
                      reservoir that licensed it (ClimateEngine.discharge_for_promotion), logs
                      trigger="promoted" in ignition_log.jsonl, respects the single-flight _cycle_active
                      guard (it does not discharge for a cycle that would be dropped), the engine
                      refractory, and PROMOTION_MAX_PER_HOUR. Nothing calls it while the flag is False;
                      the monologue hook is the shadow observe() only. Going live is a founder call and
                      needs two wiring steps: the orchestrator calls register(self), and the monologue
                      hook awaits maybe_promote() after observe().
  3. The accumulator keeps firing exactly as before; promotion adds a second, state-licensed route.

homeostasis_causal.py: it re-implements the accumulator to FORECAST coherence/novelty over a 600 s horizon.
A promoted discharge is a discrete behavioural rule (like the D-0148 cap), not a rate constant, so it does
NOT mirror automatically. Judged SAFE TO OMIT while PROMOTION_LIVE is False (nothing is discharged). When
live it is bounded: PROMOTION_MAX_PER_HOUR plus the shared 300 s refractory allow at most 2 discharges
inside that forecast horizon, the same bound that justified omitting the cap there (see that module's
2026-09-06 note). Re-judge before a flip using the shadow log's real promoted-vs-accumulator split.

Fail-open everywhere: any error means "no row" / "no promotion", never an exception into the thought loop.
Deterministic, no LLM.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path

logger = logging.getLogger("nascence.ignition_promotion")

_DATA = Path(__file__).parent.parent / "data"
_LOG = _DATA / "ignition_promotion_shadow.jsonl"

# ONE constant gates the live path. Ships False: nothing is promoted until a founder flip.
PROMOTION_LIVE = False
# Candidate threshold grid for the SHADOW row (ignition_level in [0,1]); no value is chosen live here.
THRESHOLD_GRID = (0.6, 0.7, 0.8)
# Used ONLY when PROMOTION_LIVE is True. A placeholder to be set from the shadow read, not a ruling.
LIVE_THRESHOLD = 0.7
PROMOTION_MAX_PER_HOUR = 2          # per-hour cap on promoted cycles (rumination guard, like D-0148's)
_HOUR = 3600.0

_promoted_ts: list = []             # in-memory (a restart resets it, same bounded imprecision as _defensive_fire_ts)
_runner = None                      # the orchestrator, set by register(); live path only


def register(orchestrator) -> None:
    """The orchestrator hands itself over so maybe_promote() can reach run_cycle + _cycle_active.
    Harmless while PROMOTION_LIVE is False (nothing reads it)."""
    global _runner
    _runner = orchestrator


def _engine():
    try:
        from core import climate_engine
        return climate_engine._ACTIVE
    except Exception:
        return None


def _cap_reached(now: float) -> bool:
    global _promoted_ts
    _promoted_ts = [t for t in _promoted_ts if now - t < _HOUR]
    return len(_promoted_ts) >= PROMOTION_MAX_PER_HOUR


def evaluate(signals: dict, engine=None, now: float | None = None) -> dict | None:
    """Decision row for one stream thought. Reads (never writes) the engine and stream_drive's math.
    Returns None when there is no engine to read yet (early boot / tooling): no signal, no row."""
    eng = engine if engine is not None else _engine()
    if eng is None:
        return None
    now = time.time() if now is None else now
    from core import stream_drive
    progress, red, grounded = stream_drive._shape_signals(signals)
    comp = stream_drive.compute(progress, red, grounded)
    building = bool(signals.get("building"))
    reservoir, level = eng.licensing_reservoir()
    refractory_left = max(0.0, (eng.dissonance.last_ignition_ts + eng.dissonance.refractory_secs) - now)
    capped = _cap_reached(now)
    blocked = []
    if not building:
        blocked.append("not_building")
    if not grounded:
        blocked.append("ungrounded")
    if level < min(THRESHOLD_GRID):
        blocked.append("level_below_grid")
    if refractory_left > 0:
        blocked.append("refractory")
    if capped:
        blocked.append("hourly_cap")
    return {
        "ts": round(now, 1),
        "building": building, "grounded": grounded, "progress": progress,
        "drive": comp["drive"], "drive_raw": comp["drive_raw"], "stream_ignition": comp["ignition"],
        "ignition_level": round(level, 4),
        "reservoir_defensive": round(float(eng.dissonance.value), 4),
        "reservoir_explore": round(float(eng.dissonance.explore_value), 4),
        "would_reset": reservoir,
        "grid": {f"{t:.1f}": bool(building and grounded and level >= t) for t in THRESHOLD_GRID},
        "refractory_left_s": round(refractory_left, 1),
        "hourly_cap_reached": capped,
        "eligible": not blocked,
        "blocked_by": blocked,
        "train_kind": signals.get("train_kind"), "train_len": signals.get("train_len"),
        "about": (signals.get("about") or "")[:60], "source": signals.get("source"),
    }


def observe(signals: dict, thought: str = "", scan_saw: bool | None = None) -> None:
    """SHADOW hook. Writes one row per stream thought. Applies nothing. Fail-open."""
    try:
        row = evaluate(signals)
        if row is None:
            return
        row["ledger_scan_saw_thought"] = scan_saw
        row["live"] = bool(PROMOTION_LIVE)
        from core import shadow_log
        shadow_log.append(_LOG, row)
    except Exception as exc:
        logger.debug("[ignition_promotion] observe skipped: %s", exc)


async def maybe_promote(signals: dict, thought: str) -> bool:
    """LIVE PATH. No-op (returns False) unless PROMOTION_LIVE. Promote the train's current thought into a
    deliberate internal cycle: reset only the licensing reservoir, log trigger=promoted, run the cycle.
    Returns True only when a cycle was actually handed off."""
    if not PROMOTION_LIVE:
        return False
    try:
        orch = _runner
        eng = _engine()
        if orch is None or eng is None or not (thought or "").strip():
            return False
        if getattr(orch, "_cycle_active", False):
            return False                                    # single-flight guard: do NOT discharge for a lost cycle
        row = evaluate(signals, engine=eng)
        if row is None or not row["eligible"] or row["ignition_level"] < LIVE_THRESHOLD:
            return False
        now = time.time()
        rec = eng.discharge_for_promotion(row["would_reset"], promo={
            "drive": row["drive"], "progress": row["progress"], "grounded": row["grounded"],
            "ignition_level": row["ignition_level"], "threshold": LIVE_THRESHOLD})
        if rec is None:
            return False
        _promoted_ts.append(now)
        await orch.run_cycle(thought, input_type="internal")
        return True
    except Exception as exc:
        logger.warning("[ignition_promotion] promote failed (non-fatal): %s", exc)
        return False
