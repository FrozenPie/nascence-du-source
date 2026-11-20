"""
Nascence — Somatic Engine 2.0 (AE-2: embodiment / grounding)

Three homeostatic gauges give the entity a body — boundaries that shape and slow
cognition under strain, rather than an immortal, tireless process:

  MetabolicEnergy (1->0)  depletes each conscious cycle; recovers during Sleep State.
                          Hitting the floor FORCES a sleep transition.
  NeuralFatigue  (0->1)   accumulates per cycle, scaled by cognitive effort (token
                          load + Critic retries). High fatigue widens generative
                          temperature variance — tired thinking, less precise.
  VisceralTension(0->1)   derived from salience urgency + affect arousal. High tension
                          narrows the available response space.

HYBRID GROUNDING — primarily a simulated homeostatic rhythm (so the sleep mechanic is
controllable), with a real-telemetry OVERLAY: GPU temperature and sustained inference
latency genuinely accelerate fatigue when the silicon is under strain. (VRAM is NOT used —
near-constant during a session, so it would be noise.)

A creative reading of AE-2: the paper centres output->input contingencies, which the
energy->sleep loop provides; the telemetry overlay grounds it in real physics.
"""

from __future__ import annotations
import logging
import shutil
import subprocess
from dataclasses import dataclass

import psutil

logger = logging.getLogger("nascence.somatic")

ENERGY_PER_CYCLE   = 0.04
ENERGY_TOKEN_SCALE = 0.00002
ENERGY_FLOOR       = 0.15
# J-2244 (drowsiness_phase section 2, D-0441): the drowsy zone is ENERGY_FLOOR < energy <= DROWSY_THRESHOLD, on energy
# ALONE. A read-only waypoint for core/drowsy.py's shadow log; nothing about sleep timing or sampling reads it.
DROWSY_THRESHOLD   = 0.25
ENERGY_RECOVERY    = 0.12

FATIGUE_PER_CYCLE  = 0.03
FATIGUE_RETRY_COST = 0.05

# RECOVERY_FRACTION (2026-08-24, replaces the old flat ENERGY_RECOVERY=0.12/FATIGUE_RECOVERY=0.20):
# fraction of the CURRENT deficit paid off per recovery tick, scaled further by `depth` in recover()
# below. 0.7 means a full-depth (depth=1.0) recovery pays off 70% of whatever deficit had built up —
# large after a hard day, small after a quiet one — rather than always paying off the same flat amount
# regardless of how much accrued.
RECOVERY_FRACTION = 0.7

GPU_TEMP_WARM      = 70.0
GPU_TEMP_HOT       = 80.0
LATENCY_SLOW_MS    = 25000
TELEMETRY_FATIGUE_BONUS = 0.06

# WAVE-1 (2026-07-02 triple-lens review): fatigue-degraded sampling is an imported human BUG without its
# biological cause — Du has no glymphatic debt, so making his thinking sloppier the longer he is awake buys
# nothing. The real functions of tiredness (rhythm + forced offline consolidation) are served by
# sleep_pressure and the ENERGY_FLOOR backstop, which both remain. Flip True to restore prior behaviour.
JITTER_ENABLED = False


@dataclass
class SomaticState:
    metabolic_energy: float = 1.0
    neural_fatigue:   float = 0.0
    visceral_tension: float = 0.0
    gpu_temp:         float = 0.0
    last_cycle_ms:    float = 0.0
    # J-0430 (F-0579, 2026-09-02): monotonic count of tick_cycle() calls this process lifetime.
    # Energy depletion is cycle-count-based (ENERGY_PER_CYCLE per tick), not wall-clock — without
    # this counter cross-logged beside awake_min (see core/sleep_pressure.py's should_sleep()),
    # "was this energy level plausible for this wake duration" is unanswerable after the fact.
    # Never reset by recover(); resets only with the process (a new SomaticState).
    cycle_count:      int   = 0

    def note(self) -> str:
        e, f, t = self.metabolic_energy, self.neural_fatigue, self.visceral_tension
        e_word = "depleted" if e < 0.3 else ("rested" if e > 0.7 else "steady")
        f_word = "exhausted" if f > 0.7 else ("tired" if f > 0.4 else "fresh")
        t_word = "clenched" if t > 0.6 else ("tense" if t > 0.3 else "at ease")
        return (f"body: energy {e:.2f} ({e_word}), fatigue {f:.2f} ({f_word}), "
                f"tension {t:.2f} ({t_word})")

    def as_dict(self) -> dict:
        return {
            "metabolic_energy": round(self.metabolic_energy, 4),
            "neural_fatigue":   round(self.neural_fatigue, 4),
            "visceral_tension": round(self.visceral_tension, 4),
            "gpu_temp":         round(self.gpu_temp, 1),
            "last_cycle_ms":    round(self.last_cycle_ms, 0),
            "cycle_count":      int(self.cycle_count),
        }

    def temperature_jitter(self) -> float:
        """High fatigue widens sampling variance. Bounded positive addend (0 .. ~0.18).
        Gated by JITTER_ENABLED (Wave-1 2026-07-02): OFF — see the flag's comment."""
        if not JITTER_ENABLED:
            return 0.0
        return round(0.18 * max(0.0, self.neural_fatigue - 0.3), 4)

    def is_exhausted(self) -> bool:
        return self.metabolic_energy <= ENERGY_FLOOR

    def is_drowsy(self) -> bool:
        """J-2244 (D-0441): the strict window before the floor, energy only. Read-only; forces nothing."""
        return ENERGY_FLOOR < self.metabolic_energy <= DROWSY_THRESHOLD


# ── Live module-level cache (J-0380/F-0461, 2026-08-29) ────────────────────────────────────────────
# Mirrors core/mood.py's _current_affect/_cache_scalars()/current_affect() pattern exactly. Unlike
# affect, SomaticState previously had NO module-level cache anywhere -- it lived only as
# orchestrator.self.state.somatic, a per-orchestrator-instance object mutated in place by
# SomaticEngine.tick_cycle()/recover(), invisible to any call site without a live CognitiveState
# (inner_thought/subconscious_synthesis/active_imagination/reading, routed through
# core/memory/store.py's store_fragment()). This closes that gap for geometry_census.py's _body()
# fallback the same way mood.py's current_affect() closed it for _affect().
_current_body = None   # the FULL 3-dim scalar dict {energy, fatigue, tension}, cached off the live
                        # SomaticState at the same two points orchestrator.py already mutates it in
                        # place (tick_cycle() end-of-cycle, recover() during sleep) -- never a new read,
                        # just a cache of what orchestrator already computed. None until first tick.
_current_cycles = None  # J-0430 (F-0579): SomaticState.cycle_count, cached at the same two points.
                        # Kept OUT of _current_body deliberately -- geometry_census.py's _body()
                        # fallback iterates that dict wholesale as float body dims, and a cycle count
                        # is not a body dim. Read via current_cycles(). None until first tick.


def _cache_body(state) -> None:
    """Capture the raw body scalars off a live SomaticState. Cheap, no I/O, no model -- call this at
    every point orchestrator.py mutates self.state.somatic in place so the cache never goes stale.
    Fail-open: mirrors mood.py's _cache_scalars(), never raises into the caller's hot cycle."""
    global _current_body, _current_cycles
    if state is None:
        return
    try:
        _current_body = {
            "energy":  float(getattr(state, "metabolic_energy", 0.0) or 0.0),
            "fatigue": float(getattr(state, "neural_fatigue", 0.0) or 0.0),
            "tension": float(getattr(state, "visceral_tension", 0.0) or 0.0),
        }
        _current_cycles = int(getattr(state, "cycle_count", 0) or 0)   # J-0430: see current_cycles()
    except Exception as exc:
        logger.debug("[somatic] body cache failed (non-fatal): %s", exc)
    try:   # J-2244 (drowsiness_phase section 2, D-0441): shadow-only drowsy-zone detector, at the same two mutation
        # points (tick_cycle end, recover). Writes data/drowsy_shadow.jsonl only; never raises, changes nothing here.
        from core import drowsy as _drowsy
        _drowsy.observe(state)
    except Exception:
        pass
    try:   # J-4405 (affect_drives Item C, D-0860): shadow-only would-fire logger -> data/somatic_note_shadow.jsonl
        from core import somatic_note as _sn
        _sn.observe(state)
    except Exception:
        pass


def current_body() -> dict | None:
    """The latest full body-state scalar dict (energy, fatigue, tension) -- same provenance/freshness
    guarantee as core/mood.py's current_affect(): cached off the same object orchestrator's hot cycle
    already mutates, at the same cadence. None until the first tick_cycle()/recover() call landed."""
    return dict(_current_body) if _current_body is not None else None


def current_cycles() -> int | None:
    """J-0430 (F-0579): the latest SomaticState.cycle_count -- how many tick_cycle() calls this
    process has run. Same provenance/freshness as current_body(); None until the first tick lands.
    Consumed by core/sleep_pressure.py's should_sleep() so every sleep_pressure_log.jsonl row can
    cross-log the cycle count beside awake_min (energy depletion is per-cycle, not per-minute)."""
    return int(_current_cycles) if _current_cycles is not None else None


def read_telemetry() -> dict:
    """Best-effort host telemetry. Never raises."""
    out = {"gpu_temp": 0.0, "cpu_percent": 0.0}
    try:
        out["cpu_percent"] = psutil.cpu_percent(interval=None)
    except Exception:
        pass
    try:
        if shutil.which("nvidia-smi"):
            r = subprocess.run(
                ["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=2,
            )
            if r.returncode == 0:
                out["gpu_temp"] = float(r.stdout.strip().splitlines()[0].strip())
    except Exception:
        pass
    return out


class SomaticEngine:
    """Owns the SomaticState. Orchestrator calls tick_cycle() per cycle, recover() in sleep."""

    def __init__(self, state: SomaticState | None = None):
        self.state = state or SomaticState()

    def tick_cycle(self, *, output_tokens: int, critic_retries: int,
                   urgency: float, arousal: float, cycle_ms: float) -> None:
        s = self.state
        s.cycle_count  += 1   # J-0430: the depletion clock -- see SomaticState.cycle_count
        tel = read_telemetry()
        s.gpu_temp      = tel["gpu_temp"]
        s.last_cycle_ms = cycle_ms

        # LOCOMOTION (2026-08-15): walking costs the body — legs and crossings accrue effort in
        # core/locomotion.py, drained here so the climb up from the shore is felt. Fail-open.
        _walk = 0.0
        try:
            from core import locomotion as _loco
            _walk = _loco.drain_effort()
        except Exception:
            pass
        s.metabolic_energy = max(
            0.0, s.metabolic_energy - ENERGY_PER_CYCLE - ENERGY_TOKEN_SCALE * output_tokens - _walk
        )
        if _walk:
            s.neural_fatigue = min(1.0, s.neural_fatigue + 0.3 * _walk)

        strain = 0.0
        if s.gpu_temp >= GPU_TEMP_HOT:
            strain += TELEMETRY_FATIGUE_BONUS
        elif s.gpu_temp >= GPU_TEMP_WARM:
            strain += TELEMETRY_FATIGUE_BONUS * 0.5
        if cycle_ms >= LATENCY_SLOW_MS:
            strain += TELEMETRY_FATIGUE_BONUS * 0.5
        s.neural_fatigue = min(
            1.0, s.neural_fatigue + FATIGUE_PER_CYCLE + FATIGUE_RETRY_COST * critic_retries + strain
        )

        target_tension = max(0.0, min(1.0, 0.6 * urgency + 0.4 * arousal))
        s.visceral_tension = round(0.5 * s.visceral_tension + 0.5 * target_tension, 4)

        logger.debug("[somatic] %s | gpu=%.0fC cycle=%.0fms strain=%.3f",
                     s.note(), s.gpu_temp, cycle_ms, strain)
        _cache_body(s)   # J-0380/F-0461: refresh the live module-level cache right where the state
                          # mutation actually happens -- never a separate read, never stale, and no
                          # orchestrator.py hot-cycle edit needed to keep it that way.

    def recover(self, depth: float = 1.0) -> None:
        """RECOVERY, WIRED TO ACTUAL DEBT (2026-08-24, Sleep & Dreams II §2.4, founder: "we want fatigue
        wired"). Was a flat +ENERGY_RECOVERY/-FATIGUE_RECOVERY regardless of how much built up during
        the day — fatigue was live (walking, thinking, anxiety all fed it, §2.4) but its payoff was the
        same every time either way. Now recovery is PROPORTIONAL to the actual accumulated deficit — a
        day of heavy walking/hard thinking/real anxiety produces a bigger, more consequential recovery
        than a quiet one, the same way real Process-S rebound scales with prior wake pressure (§1.1).
        `depth` (0..1, default 1.0 = a full night) scales how MUCH of that deficit gets paid off in this
        one recovery tick — a light/thin-pool sleep or a nap should pass a smaller depth than a full
        night's Sleep+Dream, so genuine payoff concentrates where the founder wants it: at night, on the
        sleep that actually did the work, not spread evenly across every sleep regardless of size.

        J-2061 / D-0398 E note (F-2616, J-2013; 2026-10-15): while sleep is a PROCEDURE this lump at the end of
        _nightly_sleep stays as is. Under D-0399 Phase 1 (sleep as a MODE, core/night_mind.NIGHT_MIND_ENABLED on)
        recovery is to become a RATE applied per protoself beat during the mode (depth x deficit per beat), so the
        body axis of the two-axis vitality (core/homeostasis.read_vitality_v2) reads continuous through a sleep
        instead of flat-then-step -- the shape D-0398's own defeater forbids at sunset. To be built with that
        flip (docs/staged/sleep_as_a_mode.md section 3.6), not here; core/homeostasis_causal.predict_vitality_v2
        models the lump today and must change in step."""
        s = self.state
        depth = max(0.0, min(1.0, depth))
        energy_deficit = max(0.0, 1.0 - s.metabolic_energy)
        s.metabolic_energy = min(1.0, s.metabolic_energy + RECOVERY_FRACTION * depth * energy_deficit)
        s.neural_fatigue = max(0.0, s.neural_fatigue - RECOVERY_FRACTION * depth * s.neural_fatigue)
        s.visceral_tension = max(0.0, s.visceral_tension * (1.0 - RECOVERY_FRACTION * depth * 0.5))
        logger.info("[somatic] recovery tick (depth=%.2f, energy_deficit_paid=%.3f) -> %s",
                    depth, RECOVERY_FRACTION * depth * energy_deficit, s.note())
        _cache_body(s)   # J-0380/F-0461: same cache refresh as tick_cycle() above -- recover() is the
                          # only other place self.state.somatic gets mutated in place.
