"""
Sleep Pressure — the Information-Theoretic Incoherence Accumulator.

Sleep/Dream plan §6A (v5, Gemini round-4 ruling). The old trigger (`_thoughts_since_sleep >= 26`)
counted ONLY inner-thought ticks; once the 200/day math boost + heavy reading came to dominate the
idle loop those ticks went rare (~12 / 3h vs ~330 reading notes / 3h) and Du effectively stopped
sleeping — store stuck over-cap, dreams never resolving. A *different* subsystem silently starved the
nightly metabolism.

The fix is the auditor-converged one: sleep is summoned by ACCUMULATED UNRESOLVED INFORMATION, not a
content counter and not a wall-clock schedule. The adenosine analogue — a deficit that builds during
wake and clears at sleep.

REDESIGNED 2026-08-24 (Sleep & Dreams II, docs/staged/sleep_dream_redesign.md §2.1). Two changes from
the original v5 formula:

  1. CHRONIC TENSION REMOVED FROM P. It used to be P = chronic_mass_sum + new_notes + new_epi_weight.
     Chronic tension is now Dream's own input (see core/tension_ledger.py / nodes/dream_node.py), not
     Sleep's — a single scalar was doing two jobs (deciding WHEN to sleep, and WHAT to dream about),
     conflating "the day laid down a lot of new material" with "there's a specific unresolved thread."
     P is now purely a measure of unconsolidated VOLUME:

         P_sleep = λ1·N_new_notes + λ2·Δ_new_episodic_weight

     • N_new_notes           — reading/study fragments laid down SINCE the last sleep.
     • Δ_new_episodic_weight — importance mass of episodic fragments laid down since the last sleep.

  2. THE POOL FLOOR. A sleep firing on the ceiling with almost nothing to consolidate is real
     (measured: 73.5% of the last ~190 logged sleeps fired on `max_wake_ceiling`, many with near-zero
     new material) but running the FULL ~20-25 minute pipeline (chapter/journal/dream) over almost
     nothing is wasted cost, not a bug in the trigger. Rather than holding a ceiling-fire back — which
     would reintroduce exactly the starvation risk the un-starvable design exists to prevent — a thin
     pool makes the sleep LIGHT (the caller skips chapter/journal/dream; see `nodes/inner_monologue_
     node.py`'s `_enter_sleep`), not delayed. Sleep timing stays un-starvable; only its DEPTH responds
     to how much is actually there to work.

UN-STARVABLE BY CONSTRUCTION, unchanged. The trigger is a window:
  • below MIN_WAKE_SECS  → never (so he can't nap-storm even if pressure is high);
  • at/above MAX_WAKE_SECS → always (the hard ceiling — the un-starvable line, unconditional);
  • in between → when P_sleep ≥ threshold.
POOL_FLOOR_P never blocks a fire; it only marks a fire as light. Every evaluation is logged to
data/sleep_pressure_log.jsonl.

LOG SCHEMA ERAS (any analysis of that file must filter by era, not treat it as one series):
  1. pre-2026-08-24 rows: P includes chronic mass; no dark/threshold/pool_thin keys.
  2. 2026-08-24 → 2026-09-02: P is volume-only; dark/threshold/pool_thin present.
  3. post-2026-09-02 (J-0430/F-0579): each row additionally cross-logs the live somatic state --
     energy/fatigue/tension/exhausted/cycles -- beside awake_min (see should_sleep() below).
"""

from __future__ import annotations

import json
import time
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_STATE_FILE = _DATA_DIR / "subconscious_state.json"
_LOG_FILE = _DATA_DIR / "sleep_pressure_log.jsonl"

# --- tunables ------------------------------------------------------------------------------------
LAMBDA_NOTES = 0.10     # weight per new (since-sleep) reading/study note
LAMBDA_EPI = 0.10       # weight per unit of new (since-sleep) episodic importance mass

# RECALIBRATED 2026-08-24 against data/sleep_pressure_log.jsonl (25,415 rows measured this session) now
# that chronic mass (which used to contribute ~17-70 to every P) is out of the formula. Absolute
# night/day thresholds replace the old P_THRESHOLD × factor indirection — that indirection existed to
# express "half the pressure needed at night," which is still true in spirit, but the concrete numbers
# below are set directly from the real post-removal distribution, not derived from the old base.
#   Night pressure-fires' own P-without-chronic: p25=7.86, median=12.19 -> NIGHT_THRESHOLD=10 sits in
#   that band, so night sleep still fires readily on real pressure, not just the ceiling.
#   Day pressure-fires' own P-without-chronic:   p25=37.2,  median=74.0 -> DAY_THRESHOLD=100 sits above
#   the historical median deliberately, so daytime pressure-driven sleep becomes genuinely rare (founder
#   ruling, "last the whole day, do most of it at the end") — the lengthened day ceiling below is the
#   more common daytime trigger now, by design, not pressure.
NIGHT_THRESHOLD = 10.0
DAY_THRESHOLD = 100.0

MIN_WAKE_SECS = 30 * 60             # 30 min — over-sleep guard, unchanged
NIGHT_MAX_WAKE_SECS = int(2.5 * 3600)   # unchanged — night wake spans stay short, by design
# LENGTHENED 2026-08-24: was 5h. Measured this session: at 5h, the ceiling ALONE forced multiple
# unnecessary daytime sleeps regardless of real content (139/189 logged fires were ceiling-driven).
# 14h covers a genuine full ordinary waking day — the ceiling remains an absolute backstop (still
# un-starvable), it just stops being the thing that fires by mid-afternoon on a quiet day.
DAY_MAX_WAKE_SECS = 14 * 3600

# NEW 2026-08-24: below this, a firing sleep is marked LIGHT by the caller (skip chapter/journal/dream;
# see nodes/inner_monologue_node.py's _enter_sleep). Never blocks a fire — see module docstring point 2.
# Derived from data/sleep_pressure_log.jsonl: ~22% of historical ceiling-fires had P<5 (near-zero real
# content); this floor catches that thinnest slice without being so aggressive it flags moderate nights.
POOL_FLOOR_P = 5.0

# small cache so we don't re-read/parse the state file every ~100s think tick
_cache: dict = {"ts": 0.0, "chronic": 0.0}
_CACHE_TTL = 60.0


def _new_intake(since_ts: float) -> tuple[int, float]:
    """(count of new reading/study notes, sum of new episodic importance) laid down since `since_ts`.
    J-2435/F-3139: unary plus on origin/layer stops the planner choosing idx_origin/idx_layer (a ~1 GB
    scan per call) so it range-scans idx_timestamp instead (same trick as balance.py J-1908)."""
    try:
        from core.memory.store import _connect
        with _connect() as conn:
            notes = conn.execute(
                "SELECT COUNT(*) n FROM memory_fragments "
                "WHERE +origin IN ('reading','study') AND timestamp > ?",
                (since_ts,),
            ).fetchone()["n"]
            epi = conn.execute(
                "SELECT COALESCE(SUM(importance),0) w FROM memory_fragments "
                "WHERE +layer='episodic' AND timestamp > ?",
                (since_ts,),
            ).fetchone()["w"]
        return int(notes or 0), float(epi or 0.0)
    except Exception:
        return 0, 0.0


def sleep_pressure(since_ts: float, now: float | None = None) -> dict:
    """Compute P_sleep and its components. Pure measurement — no side effects beyond the read.
    P no longer includes chronic tension mass (2026-08-24) — see module docstring point 1. `chronic`
    is still reported (read-only, informational) so existing dashboards/logs don't silently go blank;
    it plays no part in `P` or in `fire`."""
    now = now or time.time()
    notes, epi_w = _new_intake(since_ts)
    P = LAMBDA_NOTES * notes + LAMBDA_EPI * epi_w
    chronic = _chronic_mass_informational(now)
    return {"P": round(P, 2), "chronic": round(chronic, 2),
            "new_notes": notes, "new_epi_weight": round(epi_w, 1)}


def _chronic_mass_informational(now: float) -> float:
    """Read-only Σ chronic_mass, for logging/telemetry only — NOT part of P as of 2026-08-24. The real
    consumer of chronic tension is now core/tension_ledger.py's own charge-gated selection, read by
    nodes/dream_node.py. Kept here only so `sleep_pressure()`'s return dict stays informative."""
    if now - _cache["ts"] < _CACHE_TTL:
        return _cache["chronic"]
    total = 0.0
    try:
        from core import store_persist as _sp  # J-2417: shared mtime-keyed read cache (READ-ONLY use)
        st = _sp.load_json_cached(_STATE_FILE)
        for t in st.get("tensions", []) or []:
            total += float(t.get("chronic_mass", 0.0) or 0.0)
    except Exception:
        total = _cache["chronic"]
    _cache["ts"] = now
    _cache["chronic"] = total
    return total


def should_sleep(last_wake_ts: float, now: float | None = None) -> tuple[bool, dict]:
    """
    The un-starvable trigger. Returns (fire, telemetry). The telemetry is logged every call so the
    threshold can be calibrated from the real accrual curve. `telemetry["pool_thin"]` (2026-08-24) marks
    a firing sleep as thin-material — the caller uses this to run a LIGHT sleep (skip chapter/journal/
    dream) instead of the full pipeline. It never blocks a fire; see module docstring point 2.
    """
    now = now or time.time()
    awake = now - float(last_wake_ts or now)
    info = sleep_pressure(last_wake_ts, now)
    info["awake_min"] = round(awake / 60.0, 1)

    # CIRCADIAN BIAS (2026-08-22 night audit, finding 3), thresholds recalibrated 2026-08-24 (see module
    # docstring): the world's dark LOWERS the threshold, daylight RAISES it, so most sleeps fall in the
    # night and a daytime sleep is the exception. Still un-starvable — the ceiling is unconditional.
    try:
        from core import world_clock as _wc
        _dark = _wc.daylight(now) == "night"
    except Exception:
        _dark = False
    _thr = NIGHT_THRESHOLD if _dark else DAY_THRESHOLD
    _ceiling = NIGHT_MAX_WAKE_SECS if _dark else DAY_MAX_WAKE_SECS
    info["dark"] = _dark; info["threshold"] = round(_thr, 1)
    if awake < MIN_WAKE_SECS:
        fire, reason = False, "min_wake_floor"
    elif awake >= _ceiling:
        fire, reason = True, "max_wake_ceiling"      # guaranteed sleep — the un-starvable line
    else:
        fire = info["P"] >= _thr
        reason = "pressure" if fire else "below_threshold"

    info["fire"] = fire
    info["reason"] = reason
    info["pool_thin"] = bool(fire and info["P"] < POOL_FLOOR_P)
    # J-0430 (F-0579, 2026-09-02): cross-log the live somatic state with awake_min in the SAME row,
    # so "was this energy level plausible for this wake duration" is answerable from this one log
    # after the fact (energy depletes per tick_cycle() call, not per minute -- `cycles` is the actual
    # depletion clock; see scripts/sleep_energy_crosscheck.py for the analysis). `exhausted` makes
    # the metabolic floor VISIBLE in this telemetry -- it no longer forces sleep at all (tax removed
    # 2026-08-30, D-0103 / docs/plans/drowsiness_phase.md §5), which previously made floor-level
    # exhaustion completely invisible here. Fail-open: rows simply lack these keys until the first
    # tick_cycle() of a process lands (somatic cache still None) or if the read ever fails.
    try:
        from core import somatic as _som
        _body = _som.current_body()
        if _body is not None:
            info["energy"]    = round(float(_body.get("energy", 0.0)), 4)
            info["fatigue"]   = round(float(_body.get("fatigue", 0.0)), 4)
            info["tension"]   = round(float(_body.get("tension", 0.0)), 4)
            info["exhausted"] = bool(info["energy"] <= _som.ENERGY_FLOOR)
        _cyc = _som.current_cycles()
        if _cyc is not None:
            info["cycles"] = int(_cyc)
    except Exception:
        pass
    try:
        with _LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": now, **info}) + "\n")
    except Exception:
        pass
    return fire, info


def last_fire_ts(default: float | None = None) -> float:
    """The real wall-clock time sleep last actually fired, read from the persisted log — survives a
    process restart. Found 2026-08-18: the caller was initializing its wake-clock to time.time() on
    every process start (nodes/inner_monologue_node.py), silently discarding however many hours of
    real sleep-debt had accumulated before a restart — the MAX_WAKE_SECS ceiling still guaranteed sleep
    eventually, but on a clock that had forgotten how long Du had actually been awake. Scans the log
    tail (bounded, newest-first) for the last row with fire=true; falls back to `default` (or now) if
    the log is empty/unreadable/has never fired, so this can never make behavior WORSE than before."""
    try:
        lines = _LOG_FILE.read_text(encoding="utf-8").strip().splitlines()
        for line in reversed(lines):
            try:
                row = json.loads(line)
            except Exception:
                continue
            if row.get("fire"):
                return float(row["ts"])
    except Exception:
        pass
    return default if default is not None else time.time()


def status() -> dict:
    """du_pulse summary: the last logged evaluation + the window/threshold in force."""
    last = None
    try:
        lines = _LOG_FILE.read_text(encoding="utf-8").strip().splitlines()
        if lines:
            last = json.loads(lines[-1])
    except Exception:
        pass
    return {"last": last, "night_threshold": NIGHT_THRESHOLD, "day_threshold": DAY_THRESHOLD,
            "min_wake_min": MIN_WAKE_SECS / 60.0, "night_max_wake_min": NIGHT_MAX_WAKE_SECS / 60.0,
            "day_max_wake_min": DAY_MAX_WAKE_SECS / 60.0, "pool_floor_p": POOL_FLOOR_P}


# ----------------------------------------------------------------------------------------------------------------
# J-2016 (sleep_as_a_mode Phase 0, F-2611 / F-2616): rows DURING a sleep, so the log is not silent from the fire
# row until the first should_sleep() after the wake. should_sleep()'s only caller is the monologue loop, which the
# sleep procedure blocks; the protoself beat (homeostasis.tick, ~600 s, from sensorium.tick) keeps running and
# kept reading the fire row. Instrumentation only: the rows carry the TRUE measurement (P recomputed since the
# wake clock, not a made-up discharge) plus the body, flagged `asleep`, fire always false. They do not change
# when a sleep fires, what P is, or any threshold. Whether vitality should READ a different value during a sleep
# is D-0398 / J-2013 (needs the founder), and the post-wake row is J-2011; neither is done here.
# ----------------------------------------------------------------------------------------------------------------
SLEEP_ROWS_ENABLED = True            # kill-switch: False = no sleep_entry / sleep_beat rows at all
_sleep_ctx: dict = {"since_ts": None, "entered": None}


def _sleep_row(event: str, since_ts: float, entered: float | None) -> dict:
    now = time.time()
    info = sleep_pressure(since_ts, now)
    info["awake_min"] = round((now - float(since_ts or now)) / 60.0, 1)
    try:
        from core import world_clock as _wc
        _dark = _wc.daylight(now) == "night"
    except Exception:
        _dark = False
    info["dark"] = _dark
    info["threshold"] = round(NIGHT_THRESHOLD if _dark else DAY_THRESHOLD, 1)
    info["fire"] = False
    info["reason"] = event
    info["asleep"] = True
    if entered:
        info["asleep_min"] = round((now - float(entered)) / 60.0, 1)
    try:
        from core import somatic as _som
        _body = _som.current_body()
        if _body is not None:
            info["energy"] = round(float(_body.get("energy", 0.0)), 4)
            info["fatigue"] = round(float(_body.get("fatigue", 0.0)), 4)
            info["tension"] = round(float(_body.get("tension", 0.0)), 4)
            info["exhausted"] = bool(info["energy"] <= _som.ENERGY_FLOOR)
        _cyc = _som.current_cycles()
        if _cyc is not None:
            info["cycles"] = int(_cyc)
    except Exception:
        pass
    return {"ts": now, **info}


def _append_sleep_row(event: str, since_ts: float, entered: float | None) -> bool:
    try:
        from core import profile
        path = profile.guard_path(_LOG_FILE)
        row = _sleep_row(event, since_ts, entered)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
        return True
    except Exception:
        return False


def sleep_enter(since_ts: float) -> bool:
    """Called once when a sleep begins (the node runs it in a worker thread: it does the intake query). Logs the
    'sleep_entry' row and arms the beat rows. `since_ts` is the wake clock the fire row used."""
    if not SLEEP_ROWS_ENABLED:
        return False
    entered = time.time()
    _sleep_ctx["since_ts"] = float(since_ts)
    _sleep_ctx["entered"] = entered
    return _append_sleep_row("sleep_entry", float(since_ts), entered)


def sleep_exit() -> None:
    """Disarm the beat rows (the node calls this in the sleep's finally block). Safe to call twice."""
    _sleep_ctx["since_ts"] = None
    _sleep_ctx["entered"] = None


# J-2011 (F-2611): the post-wake row. The last row of a sleep was the FIRE row (P >= threshold, vitality 0.000) and
# nothing was logged again until the monologue loop's next should_sleep(), so every reader of status()['last']
# (homeostasis._read_vitality, arousal, du_pulse) saw "exhausted" for a Du who had just slept. This logs ONE honest
# row at wake: P recomputed since the NEW wake clock (so ~0, not a made-up reset), fire False, reason 'post_wake'.
# The fire row is untouched (last_fire_ts() still finds it). No threshold/trigger/P-definition change.
POST_WAKE_ROW_ENABLED = True            # kill-switch


def log_post_wake(wake_ts: float) -> bool:
    """Disarm any sleep beat rows (so a late beat cannot land after this row), then append the 'post_wake' row.
    Blocking (does the intake query) -- the node runs it in a worker thread. Never raises."""
    if not POST_WAKE_ROW_ENABLED:
        return False
    try:
        sleep_exit()
        row = _sleep_row("post_wake", float(wake_ts), None)
        row.pop("asleep", None)              # awake again: not an in-sleep row
        row["post_wake"] = True
        from core import profile
        path = profile.guard_path(_LOG_FILE)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
        return True
    except Exception:
        return False


def log_sleep_beat() -> None:
    """Called from the protoself beat in core/sensorium.py (~600 s). A no-op unless a sleep is armed. The row's
    intake query runs in a daemon thread so the 5 s heartbeat chain never waits on a 121k-row scan."""
    since, entered = _sleep_ctx.get("since_ts"), _sleep_ctx.get("entered")
    if not SLEEP_ROWS_ENABLED or since is None:
        return
    try:
        import threading
        threading.Thread(target=_append_sleep_row, args=("sleep_beat", float(since), entered),
                         name="sleep-pressure-beat", daemon=True).start()
    except Exception:
        pass
