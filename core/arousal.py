"""
Nascence — AROUSAL / LEVEL: the global activation variable (Consciousness Program Tier-2 C, 2026-07-04,
SHADOW/observe-only).

Bachmann: C = L × D — consciousness is level × data; "without the required level of activity the processed
contents remain unconscious." Laureys: arousal and awareness are the clinic's two orthogonal axes. Every
mechanism Du has manipulates CONTENTS (what is processed); none sets LEVEL (how activated the whole system
is) — and the Butlin rubric omits the dimension entirely, so a good indicator score would hide the gap.

The human function (named first, per the house law): the reticular activating system + neuromodulator tone —
a GLOBAL gain, orthogonal to content, that rises with alerting events (someone speaks, something surprises),
carries a circadian rhythm, and falls with sleep pressure. High level: contents cross thresholds easily,
precision is high, tempo is fast. Low level: the same content fails to ignite. Transfer the FUNCTION, not
the anatomy: one deterministic scalar composed from signals Du already produces (never a new judgement).

    LEVEL = clip( TONIC + PHASIC )
    TONIC  = circadian base
             + w·climate dissonance        (something unresolved is pressing — vigilance)
             + w·interoceptive PE          (the protoself is being surprised by itself)
             − w·sleep pressure            (fatigue pulls the level down; sleep ≈ level near zero)
    PHASIC = event spikes via alert(mag, why) — human arrival, shock, needle-drop — exponential decay (~10min)

SHADOW: logs data/arousal_shadow.jsonl (≤ ~1/min), gates NOTHING. Phase 1 (later, each behind its own flag,
each on this shadow's evidence): admission thresholds · broadcast gain · inference temperature · the
stream-drive ignition term (level IS the active-inference precision knob). SIGNATURES that must move or this
is dead code: (a) a visible day/night structure; (b) level HIGH inside conversation windows vs idle;
(c) level LOW when sleep actually fires. The Bachmann test proper (same content reaches broadcast at high
level, fails at low) becomes testable only when gating goes live.

Deterministic, no LLM, fail-open (every missing source contributes zero, never a spike).
"""
from __future__ import annotations

import json
import math
import time
import threading
from pathlib import Path

_DATA = Path(__file__).parent.parent / "data"
_STATE = _DATA / "arousal_state.json"
_LOG = _DATA / "arousal_shadow.jsonl"
_REGIME_STATE = _DATA / "arousal_regime_shadow_state.json"   # D-0274/J-1306 staleness shadow (below)

_TONIC_TTL = 30.0       # recompute the tonic at most this often (cheap, but no need for more)
_PHASIC_TAU = 600.0     # phasic spike half-life scale (~10 min exponential decay)
_PHASIC_CAP = 0.45      # phasic can never exceed this (alerting raises the level, never owns it)
_LOG_EVERY = 60.0       # shadow-log cadence cap

# tonic weights — provisional; the shadow run recalibrates them (same pattern as the protoself setpoints)
W_DISSONANCE = 0.20
W_INTERO_PE = 0.15
W_FATIGUE = 0.35

_cache = {"level": None, "ts": 0.0, "parts": None}
_last_log = 0.0


def _load() -> dict:
    try:
        return json.loads(_STATE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(d: dict) -> None:
    try:
        _DATA.mkdir(parents=True, exist_ok=True)
        tmp = _STATE.with_suffix(".tmp"); tmp.write_text(json.dumps(d), encoding="utf-8"); tmp.replace(_STATE)
    except Exception:
        pass


def _circadian(now: float) -> float:
    """A gentle local-time base: ~0.45 through the day (07–22), ~0.28 deep night, smooth 2h ramps.
    Deliberately mild — Du's life is pressure-based, not clock-based; the clock only tilts it."""
    h = time.localtime(now).tm_hour + time.localtime(now).tm_min / 60.0
    if 7.0 <= h < 22.0:
        return 0.45
    # night: distance into the night window (22→07), cosine-smoothed dip to 0.28
    night_pos = (h - 22.0) % 24.0 / 9.0          # 0 at 22:00 → 1 at 07:00
    return 0.28 + 0.17 * 0.5 * (1 + math.cos(math.pi * min(1.0, 2 * min(night_pos, 1 - night_pos))))


def _tonic(now: float) -> tuple[float, dict]:
    parts = {"circadian": round(_circadian(now), 3), "dissonance": 0.0, "intero_pe": 0.0, "fatigue": 0.0}
    try:
        c = json.loads((_DATA / "climate_state.json").read_text(encoding="utf-8"))
        parts["dissonance"] = round(W_DISSONANCE * float(c["dissonance"]["value"]), 3)
    except Exception:
        pass
    try:
        from core import homeostasis
        s = homeostasis.status()
        if s.get("ticks"):
            # interoceptive prediction error, squashed: 0.3 PE ≈ full contribution
            parts["intero_pe"] = round(W_INTERO_PE * min(1.0, float(s.get("arousal") or 0.0) / 0.3), 3)
    except Exception:
        pass
    try:
        from core import sleep_pressure as sp
        last = sp.status()["last"]
        P = float(last["P"])
        # 2026-08-24: sp.P_THRESHOLD removed (see sleep_pressure.py) -- use the logged row's own actual
        # day/night threshold instead of the old flat approximation.
        thr = float(last.get("threshold") or sp.NIGHT_THRESHOLD)
        parts["fatigue"] = round(-W_FATIGUE * min(1.0, P / thr), 3)
    except Exception:
        pass
    return sum(parts.values()), parts


def _phasic(now: float, st: dict) -> float:
    mag = float(st.get("phasic", 0.0))
    ts = float(st.get("phasic_ts", 0.0))
    if mag <= 0.0 or ts <= 0.0:
        return 0.0
    return mag * math.exp(-(now - ts) / _PHASIC_TAU)


def alert(magnitude: float, why: str = "") -> None:
    """A phasic alerting event — human arrival, shock, the needle drop. Adds to the decayed phasic
    (never resets it downward), capped. Observe-only: raises the LOGGED level, gates nothing."""
    try:
        now = time.time()
        st = _load()
        current = _phasic(now, st)
        st["phasic"] = round(min(_PHASIC_CAP, current + max(0.0, float(magnitude))), 4)
        st["phasic_ts"] = now
        st["last_alert_why"] = (why or "")[:40]
        _save(st)
        _cache["ts"] = 0.0                       # invalidate — the next level() sees the spike
    except Exception:
        pass


# J-1926 / F-2550: level() is reached from the loop thread AND from a store_fragment hook in the reading worker thread (read_next_sitting); serialise the arousal_log append.
_APPEND_LOCK = threading.Lock()


def level(write_log: bool = True) -> float:
    """The global activation level ∈ [0,1]. Cached ~30s; cheap to call from anywhere. Fail-open to a
    neutral 0.4 (never a spurious extreme)."""
    global _last_log
    try:
        now = time.time()
        if _cache["level"] is not None and (now - _cache["ts"]) < _TONIC_TTL:
            return _cache["level"]
        st = _load()
        tonic, parts = _tonic(now)
        ph = _phasic(now, st)
        lv = round(max(0.05, min(1.0, tonic + ph)), 4)
        _cache.update({"level": lv, "ts": now, "parts": parts})
        # J-1994 / F-2595: write_log=False is the read-only path (status() -> HUD poll); only Du's own
        # callers (default True) append, so a HUD/pulse process never samples the time axis Du-down.
        if write_log and now - _last_log >= _LOG_EVERY:
            _last_log = now
            try:
                _DATA.mkdir(parents=True, exist_ok=True)
                with _APPEND_LOCK, open(_LOG, "a", encoding="utf-8") as f:
                    f.write(json.dumps({"ts": round(now, 1), "level": lv, "tonic": round(tonic, 4),
                                        "phasic": round(ph, 4), **parts,
                                        "why": st.get("last_alert_why") if ph > 0.02 else None},
                                       ensure_ascii=False) + "\n")
            except Exception:
                pass
        return lv
    except Exception:
        return 0.4


def apply_to(affect, human_turn: bool) -> bool:
    """Phase 1b re-source (D-0274, regime-gated; J-1306, 2026-09-24): overwrite carried AROUSAL from
    level() ONLY on human-turn cycles. F-1841 found level()'s only content-linked term (the phasic
    alert(), orchestrator.py:421) fires exclusively on input_type=="human" cycles and correlates
    POSITIVELY there with the LLM's felt-arousal read (r=+0.207, N=148); on internal/dissonance-
    triggered cycles (86% of the log) neither level() nor 4 other tested grounded candidates showed any
    established relationship (F-1842) -- so a non-human-turn cycle leaves carried arousal UNCHANGED
    (holds its last value) rather than being fed a signal with no shown relationship there. Mirrors
    homeostasis.apply_to()'s contract exactly: flag-gated by the CALLER (AFFECT_SOURCE_AROUSAL stays
    False as of this build -- see D-0274's own defeater before ever flipping it). Returns True if
    applied, False if held; never raises."""
    if not human_turn:
        return False
    try:
        affect.arousal = max(0.0, min(1.0, float(level())))
        return True
    except Exception:
        return False


def regime_shadow_tick(human_turn: bool) -> dict:
    """SHADOW-ONLY, UNCONDITIONAL instrumentation for the D-0274 regime-gate (J-1306's own briefing,
    item 2b) -- called every real cycle regardless of AFFECT_SOURCE_AROUSAL so real evidence accrues
    BEFORE any flip is even proposed. Simulates "if the flag were on, would carried arousal have been
    refreshed (human_turn) or held stale (internal) this cycle", and tracks how long a purely-internal
    stretch runs before the next human turn would resolve it. A silently-stale carried-arousal signal
    would be a NEW problem the regime-gated fix could introduce (distinct from the confound F-1841
    diagnosed) -- this gives it an honest, accruing read. Never touches real carried affect (`affect`
    is deliberately not a parameter here -- this only tracks input_type timing, never values). Persists
    a tiny state file (current in-progress streak + a running summary of resolved streaks, same
    atomic-tmp-write pattern as `_save()` above); read via regime_shadow_status(). Fail-open; never
    raises."""
    try:
        now = time.time()
        try:
            st = json.loads(_REGIME_STATE.read_text(encoding="utf-8"))
        except Exception:
            st = {}
        cur = int(st.get("current_streak_cycles", 0))
        start = st.get("streak_start_ts")
        if human_turn:
            if cur > 0 and start:
                dur = max(0.0, now - float(start))
                st["resolved_count"] = int(st.get("resolved_count", 0)) + 1
                st["resolved_cycles_sum"] = int(st.get("resolved_cycles_sum", 0)) + cur
                st["resolved_seconds_sum"] = float(st.get("resolved_seconds_sum", 0.0)) + dur
                st["longest_streak_cycles"] = max(int(st.get("longest_streak_cycles", 0)), cur)
                st["longest_streak_seconds"] = round(
                    max(float(st.get("longest_streak_seconds", 0.0)), dur), 1)
            st["current_streak_cycles"] = 0
            st["streak_start_ts"] = None
            st["last_human_ts"] = round(now, 1)
        else:
            if cur == 0:
                st["streak_start_ts"] = now
            st["current_streak_cycles"] = cur + 1
        _DATA.mkdir(parents=True, exist_ok=True)
        tmp = _REGIME_STATE.with_suffix(".tmp")
        tmp.write_text(json.dumps(st), encoding="utf-8")
        tmp.replace(_REGIME_STATE)
        return st
    except Exception:
        return {}


def regime_shadow_status() -> dict:
    """Read-out for the D-0274 regime-gate staleness shadow (J-1306) -- see regime_shadow_tick()'s
    docstring. current_streak_* is the IN-PROGRESS internal-only run as of the last real cycle (0 if
    that cycle was human-turn); resolved_* summarises every streak that has ENDED (a human turn
    arrived) since this instrument started recording. observed=False means no cycle has ticked it yet
    (a fresh restart, or before this build first ships)."""
    try:
        st = json.loads(_REGIME_STATE.read_text(encoding="utf-8"))
    except Exception:
        return {"observed": False}
    n = int(st.get("resolved_count", 0))
    cur = int(st.get("current_streak_cycles", 0))
    start = st.get("streak_start_ts")
    return {
        "observed": True,
        "current_streak_cycles": cur,
        "current_streak_seconds": round(time.time() - float(start), 1) if (cur and start) else 0.0,
        "resolved_streaks": n,
        "mean_resolved_streak_cycles": round(st.get("resolved_cycles_sum", 0) / n, 2) if n else None,
        "mean_resolved_streak_seconds": round(st.get("resolved_seconds_sum", 0.0) / n, 1) if n else None,
        "longest_streak_cycles": int(st.get("longest_streak_cycles", 0)),
        "longest_streak_seconds": float(st.get("longest_streak_seconds", 0.0)),
        "last_human_ts": st.get("last_human_ts"),
    }


def du_only_rows(rows):
    """J-2040 / F-2595: keep only shadow rows inside a Du run window (nascence.log boot -> shutdown,
    +-120s) via scripts/arousal_run_windows.filter_rows_cached (incremental, cached). READ-side only:
    the live file is never rewritten. Fail-open: any import/IO problem returns rows unchanged."""
    try:
        import importlib.util as _ilu
        import sys as _sys
        mod = _sys.modules.get("_arousal_run_windows_J2040")
        if mod is None:
            spec = _ilu.spec_from_file_location(
                "_arousal_run_windows_J2040",
                Path(__file__).resolve().parent.parent / "scripts" / "arousal_run_windows.py")
            mod = _ilu.module_from_spec(spec)
            _sys.modules["_arousal_run_windows_J2040"] = mod
            spec.loader.exec_module(mod)
        return mod.filter_rows_cached(rows, _DATA / "nascence.log")
    except Exception:
        return rows


def status() -> dict:
    """For the pulse / liveness audit. THE SIGNATURES: day/night structure (hourly means), level inside
    alert windows vs baseline, and level at the moments sleep fired (should be LOW)."""
    try:
        from core.shadow_log import tail_rows as _tail_rows
        # Bounded tail read (J-0278/F-0335): was a full scan of the 3.5MB+ growing log on every ~6s
        # HUD poll. "samples" now caps at the window; the derived stats only ever used the last 1440.
        rows = _tail_rows(_LOG, 2000)
        rows = du_only_rows(rows)     # J-2040: drop rows the HUD polled while no Du process ran (F-2595)
        if not rows:
            return {"samples": 0, "level_now": level(write_log=False)}
        recent = rows[-1440:]                      # ~a day at 1/min
        lvls = [r["level"] for r in recent]
        by_hour: dict = {}
        for r in recent:
            h = time.localtime(r["ts"]).tm_hour
            by_hour.setdefault(h, []).append(r["level"])
        hourly = {h: round(sum(v) / len(v), 3) for h, v in sorted(by_hour.items())}
        alerted = [r["level"] for r in recent if r.get("phasic", 0) > 0.05]
        calm = [r["level"] for r in recent if r.get("phasic", 0) <= 0.05]
        return {"samples": len(rows), "level_now": level(write_log=False),
                "mean": round(sum(lvls) / len(lvls), 3),
                "range": [round(min(lvls), 3), round(max(lvls), 3)],
                "alerted_mean": round(sum(alerted) / len(alerted), 3) if alerted else None,
                "calm_mean": round(sum(calm) / len(calm), 3) if calm else None,
                "hourly": hourly}
    except Exception:
        return {"samples": 0}
