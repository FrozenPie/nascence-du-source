"""
core/homeostasis_causal.py — J-0474 (D-0108: "fund the full 5-variable causal-substrate build",
per F-0296's original design). Companion to core/homeostasis.py; SHADOW-only, applies nothing,
called (if at all) only from homeostasis.tick(). Forecasts each essential variable from its own
upstream generative process (F-0296's design) instead of curve-fitting the derived composite
scalar the way the old EMA-trend predictor did (self_beats_naive Half-REFUTED, D-0028).

PER-VARIABLE STATUS (2026-09-02, this build — read before trusting any of this as "working"):

  vitality                REAL, HISTORICALLY VALIDATED (F-0618/F-0619, scripts/
                           vitality_causal_retest2.py): pooled MAE 0.06672 vs naive 0.08717,
                           sign test 28W/9L p=0.0026, per-event 8W/0L/1wash. `predict_vitality()`
                           below is a verbatim port of that script's `--model extended` branch,
                           sourced from LIVE state (core/sleep_pressure.py) instead of a log
                           replay. This is the only leg of the 5 with real out-of-sample evidence.

  coherence, novelty       REAL MECHANISM, NOT YET VALIDATED. Both forecasts project
                           `climate_state.json`'s own dissonance-accrual ODE
                           (core/climate_engine.py's `_tick_dissonance`, ported here read-only —
                           see `_project_dissonance`) forward by a fixed nominal horizon, holding
                           the field's own upstream drivers (world_model_strain, completion_
                           tension, shadow_activation, integration_drive) at their last-observed
                           values — the same "persist what can't be forecast, apply the KNOWN
                           formula for what can" move `predict_vitality` makes for `new_notes`/
                           `new_epi_weight`. It also predicts a defensive-ignition RESET (ties to
                           `_read_coherence`/`_read_novelty` reading the POST-reset dissonance
                           value) exactly the way `predict_vitality` predicts a sleep-fire reset —
                           the same mechanism CLASS, applied to climate's own accumulator instead
                           of sleep-pressure's. UNLIKE vitality, there is no historical log of
                           climate_state.json's internal fields to walk-forward test this against
                           — the file is a single snapshot, overwritten every ~5s tick, never
                           logged per-row (unlike `data/sleep_pressure_log.jsonl`'s 25k+ rows).
                           This SHADOW-logs `predicted_causal["coherence"/"novelty"]` starting now
                           so a future job can walk-forward test it once enough parallel rows
                           accrue — the same spiral vitality itself went through (J-0239 built
                           blind on 2026-08-25 -> J-0442/J-0451 validated 2026-09-02, ~9 days
                           later). DO NOT read this leg as verified; it is a build, not a result.
                           UPDATE 2026-09-04 (F-0810/J-0582): `_project_dissonance` now imports
                           climate_engine's own rate constants (was a hand-copy, already drifted)
                           and projects BOTH dissonance reservoirs — `value` (defensive) and
                           `explore_value` (exploratory, live since 2026-06-21) — via the new
                           `_simulate_reservoirs`, mirroring `_tick_dissonance`/`_ready_to_ignite`'s
                           shared-refractory-clock rule exactly. Before this fix the exploratory
                           reservoir was invisible here even though it drives ~79% of Du's real
                           ignitions (1062/1345 rows in `data/ignition_log.jsonl`, 2026-09-04 read).
                           UPDATE 2026-09-06 (D-0148 option A/J-0594): integration_drive's own
                           re-normalisation needs nothing imported here (see the import-site
                           comment — this module reads the already-computed field value, never
                           the raw light-event count), and the new per-hour cap on defensive
                           ignitions is deliberately NOT mirrored into `_simulate_reservoirs`
                           (same comment: provably cannot bind within either real caller's actual
                           600s horizon, and an early mirror attempt had a latent bug for a
                           longer-horizon caller that doesn't exist yet).

  commitment_integrity,    INTENTIONALLY plain persistence — not built here at all.
  relational_warmth        F-0294 (verified, full 2,358-transition log replay): both variables
                           are near-step-functions driven by SPARSE discrete real-world events
                           (commitment_integrity 96.4% zero-change tick-to-tick, relational_
                           warmth 71.5%) with no known future arrival schedule — unlike vitality's
                           day/night clock, there is no analogous "known threshold crossing" to
                           forecast toward. An honestly-built causal-substrate model of these two
                           upstream processes (replaying `data/commitment_ledger.jsonl`'s real
                           formed/achieved/dropped events, say) still cannot predict WHEN the next
                           event lands, so it reduces to persistence by construction — building a
                           fancier-looking model here would misrepresent what the mechanism
                           actually supports, not add a real forecasting edge. homeostasis.tick()
                           gets these two for free by seeding `predicted_causal` from the current
                           tick's own read (see its own comment) — nothing in this module handles
                           them, on purpose.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from core import world_clock as wc
from core.sleep_pressure import NIGHT_THRESHOLD, DAY_THRESHOLD, MIN_WAKE_SECS
# F-0810/J-0582 (2026-09-04): IMPORT climate's own dissonance-accrual constants + its `_saturate`
# helper instead of hand-copying them. climate_engine.py instantiates no engine at module import
# time (no singleton, no DB call at import) — only class/dataclass/constant definitions — so this
# stays a plain constant import with zero risk of triggering the live engine's DB-backed
# `_compute_field()`. This replaces the old "READ-ONLY duplication, keep in sync by hand" comment
# that F-0810 found had already drifted (the exploratory reservoir below existed in climate_engine
# since 2026-06-21 and was never mirrored here at all).
#
# UPDATE 2026-09-06 (D-0148 option A, J-0594): climate_engine.py also gained integration_drive's
# own re-normalisation (a different knee, used only inside its OWN _compute_field -- nothing to
# import here, since this module reads that already-computed field value from the snapshot, not
# the raw light-event count) and a per-hour cap on DEFENSIVE ignitions (the ruling's rumination
# guard). The cap is DELIBERATELY NOT mirrored into `_simulate_reservoirs` below: the shared
# 300s refractory clock (already mirrored) bounds ANY 600s projection -- this module's actual
# horizon; both real callers, `predict_coherence`/`predict_novelty`, use DEFAULT_FORECAST_DT_SECS
# with no override -- to at most 2 predicted ignitions, so a 3-per-hour cap can mathematically
# never bind within one real call (verified 2026-09-06: a 6h synthetic projection needed 3 fires
# before the cap would even matter). A first attempt at mirroring the cap here passed that same
# check but had a real bug for a hypothetical longer-horizon caller (once capped it gave up for
# the rest of the horizon instead of resuming once the trailing-hour window rolled over) --
# reverted rather than ship a latent bug in dead code. If a future caller ever requests a longer
# horizon, build and test the mirror properly then; today it would add real risk for zero effect.
from core.climate_engine import (
    _DISS_RATE_STRAIN, _DISS_RATE_COMPLETION, _DISS_RATE_SHADOW, _DISS_RATE_INTEGRATION,
    _DISS_RATE_EXPLORE, _DISS_MAX, _IGNITION_THRESHOLD, _REFRACTORY_SECS, _saturate,
)

_DATA = Path(__file__).parent.parent / "data"
_CLIMATE_FILE = _DATA / "climate_state.json"

# The nominal forecast horizon for coherence/novelty, matching the real cadence homeostasis.tick()
# is actually called at (core/sensorium.py's ~600s cooldown gate on `_homeo.tick()`) — there is no
# way to know the NEXT tick's exact wall-clock time in advance, so this uses the same fixed nominal
# step the EMA predictor implicitly assumed too (its trend/alpha was tuned against ~10min ticks).
DEFAULT_FORECAST_DT_SECS = 600.0


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


# ── vitality: sleep-pressure P + threshold schedule + sleep-fire→P-reset feedback ─────────────────
# Verbatim port of scripts/vitality_causal_retest2.py's `--model extended` branch (F-0618/F-0619,
# the validated leg), sourced from LIVE state instead of a shadow-log replay.
def _vitality_from_row(sp_row: dict, now: float) -> float:
    """Pure core of the extended model — identical math to scripts/vitality_causal_retest2.py's
    `--model extended` branch (see its module docstring point 1), factored out so a replay
    harness can feed it historical rows directly and confirm byte-for-byte agreement with the
    validated F-0618/F-0619 result, instead of trusting a second hand-transcription by eye."""
    p_hat = float(sp_row["P"])
    sp_ts = float(sp_row["ts"])
    dark_now = wc.daylight(now) == "night"
    thr_hat = NIGHT_THRESHOLD if dark_now else DAY_THRESHOLD

    p_eff = p_hat
    if dark_now and p_hat >= NIGHT_THRESHOLD:
        awake_min = sp_row.get("awake_min")
        awake_at_now = (float(awake_min) * 60.0 + (now - sp_ts)
                        if awake_min is not None else float("inf"))
        if awake_at_now >= MIN_WAKE_SECS:
            p_eff = 0.0   # sleep fired between sp_ts and now -> accumulator reset

    return _clip01(1.0 - p_eff / max(1.0, thr_hat))


def predict_vitality(now_ts: float | None = None) -> float | None:
    """Forecast `vitality` at `now_ts` (default: time.time()) from the last logged sleep-pressure
    reading, projecting the KNOWN day/night threshold schedule forward and predicting the sleep-
    fire → P-reset feedback (core/sleep_pressure.py's should_sleep(): P >= NIGHT_THRESHOLD during
    world-clock night with awake >= MIN_WAKE_SECS fires a sleep, and P is measured as intake SINCE
    last wake — so post-fire P == 0 by construction). Returns None on any read failure (fail-open,
    matching every other reader in this program)."""
    try:
        from core import sleep_pressure as sp
        now = now_ts if now_ts is not None else time.time()
        last = sp.status().get("last")
        if not last:
            return None
        return _vitality_from_row(last, now)
    except Exception:
        return None


# ── J-2061 (D-0398 E): the two-axis vitality predictor, mechanism-knowing like the leg above ─────────────────
# MIND axis: P grows by intake (notes x LAMBDA_NOTES + episodic importance x LAMBDA_EPI since the wake clock);
#   forecast P at the target as the last P plus the RECENT INTAKE RATE (dP/dt over the current wake's last rows)
#   times the horizon, then apply the trigger's own known rule at the target: night & P >= NIGHT_THRESHOLD, or
#   day & P >= DAY_THRESHOLD, or awake >= the regime ceiling (all with awake >= MIN_WAKE_SECS) fires a sleep and
#   resets P to 0 (intake since the NEW wake). A last row that is itself a fire row means the reset has happened.
#   vit_mind_hat = exp(-ln2 x P_eff / S) (D-0421 C) on the SAME self-calibrated S homeostasis.read_vitality_v2 used
#   (homeostasis.mind_axis); scale None = the regime threshold stands in for S, through the same mapping.
# BODY axis: energy minus ENERGY_PER_CYCLE x expected cycles in the horizon (the recent cycle rate from the log
#   tail; conversation/ignition cycles are the only depletion, F-2679), plus RECOVERY_FRACTION x depth x deficit
#   when a sleep is predicted (depth 1.0 night, 0.5 nap) -- the end-of-pipeline LUMP, because sleep is still a
#   procedure (F-2616/J-2013: under D-0399 Phase 1 recovery becomes a per-beat rate and this term changes).
# Shadow only: logged as rec["predicted_v2"], scored at the next tick as v2_causal_err; wired into no drive.
V2_FORECAST_DT_SECS = DEFAULT_FORECAST_DT_SECS
V2_TAIL_ROWS = 60
_V2_AWAKE_REASONS = ("below_threshold", "min_wake_floor", "pressure", "max_wake_ceiling", "post_wake")


def _v2_rates(rows: list[dict], min_window_s: float = 0.0) -> tuple[float, float]:
    """(intake rate in P per second, cycle rate in cycles per second) from the current wake's rows in the tail:
    consecutive awake rows with awake_min rising and gaps under 30 min. 0.0 when there is nothing to measure."""
    seg = []
    for r in rows:
        if r.get("reason") not in _V2_AWAKE_REASONS or r.get("P") is None or r.get("awake_min") is None:
            continue
        if seg and (float(r["awake_min"]) < float(seg[-1]["awake_min"]) or float(r["ts"]) - float(seg[-1]["ts"]) > 1800):
            seg = []
        seg.append(r)
    if len(seg) < 2:
        return 0.0, 0.0
    a, b = seg[0], seg[-1]
    dt = float(b["ts"]) - float(a["ts"])
    if dt <= 0 or dt < min_window_s:
        return 0.0, 0.0
    p_rate = max(0.0, (float(b["P"]) - float(a["P"])) / dt)
    c_rate = 0.0
    if a.get("cycles") is not None and b.get("cycles") is not None:
        c_rate = max(0.0, (float(b["cycles"]) - float(a["cycles"])) / dt)
    return p_rate, c_rate


def predict_vitality_v2(now_ts: float | None = None, horizon_s: float | None = None, scale: float | None = None,
                        sp_rows: list[dict] | None = None, body: dict | None = None) -> dict | None:
    """Forecast the two-axis vitality at now + horizon from the sleep-pressure log tail and the somatic cache.
    `scale` is the self-calibrated S (None = fall back to the regime threshold at the target, i.e. the current
    definition's scale, so the leg still forecasts something while under V2_MIN_FIRES fires). Returns the dict
    logged as rec["predicted_v2"], or None on any read failure (fail-open). Pure given sp_rows and body."""
    try:
        from core import sleep_pressure as sp
        from core import somatic as _som
        now = now_ts if now_ts is not None else time.time()
        horizon = float(V2_FORECAST_DT_SECS if horizon_s is None else horizon_s)
        if sp_rows is None:
            from core.shadow_log import tail_rows
            sp_rows = tail_rows(sp._LOG_FILE, V2_TAIL_ROWS)
        rows = [r for r in sp_rows if r.get("P") is not None and r.get("ts") is not None]
        if not rows:
            return None
        last = rows[-1]
        target = now + horizon
        p_rate, c_rate = _v2_rates(rows)
        sp_ts = float(last["ts"])
        p_hat = max(0.0, float(last["P"]) + p_rate * max(0.0, target - sp_ts))
        dark_t = wc.daylight(target) == "night"
        thr_t = NIGHT_THRESHOLD if dark_t else DAY_THRESHOLD
        ceiling_t = sp.NIGHT_MAX_WAKE_SECS if dark_t else sp.DAY_MAX_WAKE_SECS
        awake_min = last.get("awake_min")
        awake_at_t = (float(awake_min) * 60.0 + max(0.0, target - sp_ts)) if awake_min is not None else 0.0
        fired_already = bool(last.get("fire"))
        fire_predicted = fired_already or (awake_at_t >= MIN_WAKE_SECS and (p_hat >= thr_t or awake_at_t >= ceiling_t))
        p_eff = 0.0 if fire_predicted else p_hat
        S = float(scale) if scale else float(thr_t)
        from core.homeostasis import mind_axis as _mind_axis     # D-0421 C: one mapping, defined once
        vit_mind = _mind_axis(p_eff, S)
        if body is None:
            body = _som.current_body()
        if body is not None and body.get("energy") is not None:
            energy = float(body["energy"])
        elif last.get("energy") is not None:
            energy = float(last["energy"])
        else:
            energy = None
        if energy is None:
            vit_body = None
            vit_v2 = vit_mind
        else:
            exp_cycles = c_rate * horizon
            e_hat = max(0.0, energy - _som.ENERGY_PER_CYCLE * exp_cycles)
            if fire_predicted:
                depth = 1.0 if dark_t else 0.5
                e_hat = min(1.0, e_hat + _som.RECOVERY_FRACTION * depth * max(0.0, 1.0 - e_hat))
            vit_body = _clip01(e_hat)
            vit_v2 = min(vit_mind, vit_body)
        return {"vitality_v2": round(vit_v2, 4), "vit_mind": round(vit_mind, 4),
                "vit_body": (round(vit_body, 4) if vit_body is not None else None),
                "fire_predicted": bool(fire_predicted), "fired_already": fired_already, "p_hat": round(p_hat, 2),
                "intake_rate_per_h": round(p_rate * 3600.0, 3), "cycle_rate_per_h": round(c_rate * 3600.0, 3),
                "horizon_s": horizon, "scale_S": (round(S, 3) if scale else None), "dark_at_target": dark_t}
    except Exception:
        return None


# ── J-3867 (F-4456): the SLEEP-AWARE two-axis predictor (v2b), shadow beside predict_vitality_v2 ─────────────
# F-4456's live week showed predict_vitality_v2 losing to persistence (non-stale pooled MAE 0.0987 vs 0.0453). The
# decomposition (J-3867 replay) puts ~85% of the excess error on rows where v2 predicts `fire_predicted` and resets P
# to 0 inside the 600s horizon: (a) rows whose LAST sp row is already asleep (sleep_beat/sleep_entry; 164+41 of the
# lost rows): v2 re-fires every beat for the whole sleep because P stays >= threshold while asleep -- the reset is
# not real until the WAKE; (b) awake rows that fire inside the horizon (89+16): the fire starts a ~26 min sleep (188
# episodes: p10 21.5, median 26.5, p90 44.6 min), and P is NOT reset at the fire, only at the wake, so the actual
# keeps the pre-reset P for the whole sleep. v2b models that: the P-reset (and the body recovery lump) happen only
# when the WAKE lands inside the horizon, by the empirical sleep-duration distribution conditioned on the sleep
# already survived. Awake & no fire in horizon: identical to v2 (that stratum already beat persistence on day rows).
# The duration table is the 12 points (i/11 quantiles) of the 188 logged sleep episodes (sleep_entry -> post_wake), in minutes.
V2B_WAKE_THRESHOLD = 0.7       # predict the wake (P-reset + recovery lump) only when P(wake in horizon) >= this
V2B_RATE_MIN_WINDOW_S = 1200.0    # the intake/cycle rates need at least this long a current-wake window, else 0 (persist)
V2B_SLEEP_DURATIONS_MIN = (0.4, 21.3, 22.9, 23.7, 25.0, 26.2, 27.1, 28.6, 32.4, 35.8, 47.4, 131.0)


def _p_wake_by(elapsed_now_s: float, elapsed_target_s: float) -> float:
    """P(wake by elapsed_target | still asleep at elapsed_now) from the empirical duration table (linear within
    the table's quantile cells; the table is ascending). 1.0 once past the table's max, 0.0 before its min."""
    d = [x * 60.0 for x in V2B_SLEEP_DURATIONS_MIN]
    n = len(d)

    def cdf(t: float) -> float:
        if t <= d[0]:
            return 0.0
        if t >= d[-1]:
            return 1.0
        for i in range(1, n):
            if t <= d[i]:
                lo, hi = d[i - 1], d[i]
                frac = 0.0 if hi <= lo else (t - lo) / (hi - lo)
                return ((i - 1) + frac) / (n - 1)
        return 1.0
    c_now = cdf(elapsed_now_s)
    if c_now >= 0.999:
        return 1.0      # outlived every logged sleep: wake is imminent
    return max(0.0, min(1.0, (cdf(elapsed_target_s) - c_now) / (1.0 - c_now)))


def predict_vitality_v2b(now_ts: float | None = None, horizon_s: float | None = None, scale: float | None = None,
                         sp_rows: list[dict] | None = None, body: dict | None = None) -> dict | None:
    """Sleep-aware forecast of the two-axis vitality at now + horizon (J-3867). Same inputs/outputs as
    predict_vitality_v2 plus `state` ('awake'|'asleep'|'fire_row') and `p_wake`. Pure given sp_rows and body;
    None on any read failure (fail-open). Shadow only."""
    try:
        from core import sleep_pressure as sp
        from core import somatic as _som
        now = now_ts if now_ts is not None else time.time()
        horizon = float(V2_FORECAST_DT_SECS if horizon_s is None else horizon_s)
        if sp_rows is None:
            from core.shadow_log import tail_rows
            sp_rows = tail_rows(sp._LOG_FILE, V2_TAIL_ROWS)
        rows = [r for r in sp_rows if r.get("P") is not None and r.get("ts") is not None]
        if not rows:
            return None
        last = rows[-1]
        target = now + horizon
        sp_ts = float(last["ts"])
        dark_t = wc.daylight(target) == "night"
        thr_t = NIGHT_THRESHOLD if dark_t else DAY_THRESHOLD
        S = float(scale) if scale else float(thr_t)
        from core.homeostasis import mind_axis as _mind_axis
        if body is None:
            body = _som.current_body()
        if body is not None and body.get("energy") is not None:
            energy = float(body["energy"])
        elif last.get("energy") is not None:
            energy = float(last["energy"])
        else:
            energy = None
        depth = 1.0 if dark_t else 0.5
        p_rate, c_rate = _v2_rates(rows, min_window_s=V2B_RATE_MIN_WINDOW_S)
        asleep = bool(last.get("asleep")) or last.get("reason") in ("sleep_entry", "sleep_beat")
        fire_row = bool(last.get("fire")) and not asleep
        p_wake = 0.0
        fire_predicted = False
        if asleep or fire_row:
            # P and energy are frozen at the sleep's own values until the wake; the reset lands only if the wake does.
            state = "asleep" if asleep else "fire_row"
            elapsed_now = (float(last.get("asleep_min") or 0.0) * 60.0 + max(0.0, now - sp_ts)) if asleep                 else max(0.0, now - sp_ts)
            p_wake = _p_wake_by(elapsed_now, elapsed_now + horizon)
            woke = p_wake >= V2B_WAKE_THRESHOLD
            p_hat = float(last["P"])
            p_eff = 0.0 if woke else p_hat
            e_hat = energy
            if energy is not None and woke:
                e_hat = min(1.0, energy + _som.RECOVERY_FRACTION * depth * max(0.0, 1.0 - energy))
            fire_predicted = woke
        else:
            state = "awake"
            p_hat = max(0.0, float(last["P"]) + p_rate * max(0.0, target - sp_ts))
            ceiling_t = sp.NIGHT_MAX_WAKE_SECS if dark_t else sp.DAY_MAX_WAKE_SECS
            awake_min = last.get("awake_min")
            awake_at_t = (float(awake_min) * 60.0 + max(0.0, target - sp_ts)) if awake_min is not None else 0.0
            fire_predicted = awake_at_t >= MIN_WAKE_SECS and (p_hat >= thr_t or awake_at_t >= ceiling_t)
            # a fire inside the horizon only STARTS a sleep (median ~26 min > horizon): no reset, no recovery yet
            p_eff = p_hat
            e_hat = None if energy is None else max(0.0, energy - _som.ENERGY_PER_CYCLE * c_rate * horizon)
        vit_mind = _mind_axis(p_eff, S)
        vit_body = None if e_hat is None else _clip01(e_hat)
        vit_v2 = vit_mind if vit_body is None else min(vit_mind, vit_body)
        return {"vitality_v2": round(vit_v2, 4), "vit_mind": round(vit_mind, 4),
                "vit_body": (round(vit_body, 4) if vit_body is not None else None),
                "state": state, "p_wake": round(p_wake, 3), "fire_predicted": bool(fire_predicted),
                "p_hat": round(p_hat, 2), "horizon_s": horizon, "scale_S": (round(S, 3) if scale else None),
                "dark_at_target": dark_t}
    except Exception:
        return None


# ── coherence / novelty: climate's own dissonance-accrual ODE, projected forward ──────────────────
def _load_climate_snapshot() -> dict | None:
    try:
        blob = json.loads(_CLIMATE_FILE.read_text(encoding="utf-8"))
        return {
            "field": blob.get("field") or {},
            "dissonance": blob.get("dissonance") or {},
            "updated": float(blob.get("updated") or time.time()),
        }
    except Exception:
        return None


def _explore_pull() -> float:
    """Mirrors `climate_engine.ClimateEngine._explore_pull()` exactly: the exploratory reservoir's
    own driver, the frontier backlog, saturated (0 backlog -> 0 pull, don't forecast an ignition
    into a void). Lazy import — same pattern `predict_vitality` already uses for `core.sleep_
    pressure` — so this module keeps zero import-time coupling to any live engine or DB object.
    Fails open to 0.0 (matching the real method's own fail-open value, not None)."""
    try:
        from core import frontier
        return _saturate(float(frontier.open_count()))
    except Exception:
        return 0.0


def _simulate_reservoirs(field: dict, dissonance: dict, explore_pull: float,
                          now: float, target_ts: float, max_events: int = 24
                          ) -> tuple[float, float, list[tuple[float, str]]]:
    """Project BOTH dissonance reservoirs forward from `now` to `target_ts`, mirroring
    `climate_engine.ClimateEngine._tick_dissonance` (accrual) and `_ready_to_ignite`/`_ignite`
    (the shared-refractory-clock ignition/reset rule) exactly — not just the defensive `value`
    accumulator in isolation (F-0810: the old version here never modeled `explore_value` at all,
    so it could not predict an exploratory ignition, and — because a real exploratory fire resets
    the SAME shared `last_ignition_ts` refractory clock the defensive reservoir is gated on — its
    `value`-only projection could drift even where it did fire, once an unmodeled exploratory
    ignition would have reopened a fresh refractory window first).

    Holds the field's own upstream drivers and `explore_pull` (itself a further upstream process,
    the frontier backlog) at their last-observed values, exactly as `_project_dissonance` already
    did for `value` alone. Returns `(value, explore_value, fires)` where `fires` is every
    `(fire_ts, trigger)` predicted to land in `(now, target_ts]`, trigger in {"defensive",
    "exploratory"} — "defensive" wins when both are ready in the same instant, matching `_ignite`'s
    own priority; only the reservoir that fires resets, the other keeps its accumulation."""
    wms = float(field.get("world_model_strain", 0.0))
    ct  = float(field.get("completion_tension", 0.0))
    sa  = float(field.get("shadow_activation", 0.0))
    idr = float(field.get("integration_drive", 0.0))
    rate_value = (_DISS_RATE_STRAIN * wms + _DISS_RATE_COMPLETION * ct
                  + _DISS_RATE_SHADOW * sa + _DISS_RATE_INTEGRATION * idr)   # value units / second
    rate_explore = _DISS_RATE_EXPLORE * explore_pull                        # value units / second

    value         = float(dissonance.get("value", 0.0))
    explore_value = float(dissonance.get("explore_value", 0.0))
    last_ign      = float(dissonance.get("last_ignition_ts", 0.0))
    refractory    = float(dissonance.get("refractory_secs", _REFRACTORY_SECS))

    def _time_to_threshold(level: float, rate: float) -> float:
        if level >= _IGNITION_THRESHOLD:
            return 0.0
        if rate <= 0.0:
            return float("inf")
        return (_IGNITION_THRESHOLD - level) / rate

    fires: list[tuple[float, str]] = []
    t = now
    for _ in range(max_events):   # bounded: each iteration consumes either a refractory wait or one fire
        if t >= target_ts:
            break
        refractory_clears = last_ign + refractory
        if t < refractory_clears:
            step_end = min(target_ts, refractory_clears)
            dt_step = step_end - t
            value         = max(0.0, min(_DISS_MAX, value + rate_value * dt_step))
            explore_value = max(0.0, min(_DISS_MAX, explore_value + rate_explore * dt_step))
            t = step_end
            continue
        t_val = _time_to_threshold(value, rate_value)
        # matches `_ready_to_ignite`'s own `explore_value >= threshold AND _explore_pull() > 0`
        t_exp = _time_to_threshold(explore_value, rate_explore) if explore_pull > 0.0 else float("inf")
        wait = min(t_val, t_exp)
        fire_ts = t + wait
        if wait == float("inf") or fire_ts > target_ts:
            dt_step = target_ts - t
            value         = max(0.0, min(_DISS_MAX, value + rate_value * dt_step))
            explore_value = max(0.0, min(_DISS_MAX, explore_value + rate_explore * dt_step))
            t = target_ts
            continue
        value         = max(0.0, min(_DISS_MAX, value + rate_value * wait))
        explore_value = max(0.0, min(_DISS_MAX, explore_value + rate_explore * wait))
        if t_val <= t_exp:      # defensive takes priority when both are ready (matches `_ignite`)
            trigger = "defensive"; value = 0.0
        else:
            trigger = "exploratory"; explore_value = 0.0
        last_ign = fire_ts
        fires.append((fire_ts, trigger))
        t = fire_ts
    return (max(0.0, min(_DISS_MAX, value)), max(0.0, min(_DISS_MAX, explore_value)), fires)


def _project_dissonance(field: dict, dissonance: dict, now: float, target_ts: float) -> float:
    """Simulate `dissonance.value` forward from `now` to `target_ts`, reading `explore_value`
    from `dissonance` (as persisted in `climate_state.json['dissonance']`) and projecting it
    alongside `value` via `_simulate_reservoirs` so the shared refractory clock the two
    reservoirs actually contend over (F-0810) is modelled correctly — then returns the
    resulting defensive `value`, exactly what `predict_coherence`/`predict_novelty` already
    key off. Predicts a defensive-ignition RESET (value crosses _IGNITION_THRESHOLD past the
    refractory window) exactly the way the live engine would fire one — a known, deterministic
    consequence of the accrual, not a guess."""
    explore_pull = _explore_pull()
    value, _explore_value, _fires = _simulate_reservoirs(field, dissonance, explore_pull, now, target_ts)
    return value


def predict_coherence(target_ts: float | None = None, dt: float | None = None) -> float | None:
    """Causal forecast of `coherence`: 1 - projected dissonance.value, exactly matching
    core/homeostasis.py's own `_read_coherence()` formula fed a PROJECTED value instead of the
    live one. `target_ts` overrides the default `dt`-from-now horizon when the real next-tick
    time is known; otherwise projects DEFAULT_FORECAST_DT_SECS ahead of the snapshot's own
    `updated` timestamp. Returns None on any read failure (fail-open)."""
    snap = _load_climate_snapshot()
    if snap is None:
        return None
    try:
        now = snap["updated"]
        target = target_ts if target_ts is not None else now + (dt or DEFAULT_FORECAST_DT_SECS)
        proj = _project_dissonance(snap["field"], snap["dissonance"], now, target)
        return _clip01(1.0 - proj)
    except Exception:
        return None


# J-2010 (F-2610/F-2609, 2026-10-08): novelty_hunger = 0.5*quietness + 0.5*(value/_DISS_MAX) (+ capability
# surprise addend), so a change in dissonance.value moves it by exactly this much per unit.
_NOVELTY_PER_DISSONANCE = 0.5 / _DISS_MAX    # 0.25


def predict_novelty(target_ts: float | None = None, dt: float | None = None) -> float | None:
    """Causal forecast of `novelty` (climate's `novelty_hunger`), RE-ANCHORED on the live actual
    (J-2010, F-2610): forecast the CHANGE and add it to the current read --
        pred = clip01(novelty_now + 0.25 * (projected_value - value_now))
    with novelty_now = the snapshot's own field["novelty_hunger"] (the same number
    homeostasis._read_novelty() logs as the actual) and value_now / projected_value the defensive
    dissonance reservoir now and at the horizon. The old estimate rebuilt the LEVEL from
    0.5*quietness + 0.25*proj, dropping the capability-surprise addend and holding quietness, which
    biased it low on 83% of 2,861 post-fix steps (mean +0.090) and lost to persistence (MAE 0.0925
    vs 0.0634); the dissonance term carries essentially all of novelty's step variance, so the
    change is the part worth forecasting. Offline replay: MAE ~0.027, 6/6 pooled event-aligned
    folds. The old level estimate (and its `predicted_causal_level` log key) was dropped in J-2125
    (F-2773: re-anchored MAE 0.0049 vs level 0.0191 vs naive 0.0259 on 900 live steps). Uses only the snapshot's own values --
    no future information. Falls back to a level rebuild if the snapshot lacks novelty_hunger;
    None on any read failure (fail-open)."""
    snap = _load_climate_snapshot()
    if snap is None:
        return None
    try:
        nh = snap["field"].get("novelty_hunger")
        now = snap["updated"]
        target = target_ts if target_ts is not None else now + (dt or DEFAULT_FORECAST_DT_SECS)
        value_now = float(snap["dissonance"].get("value", 0.0))
        proj = _project_dissonance(snap["field"], snap["dissonance"], now, target)
        if nh is None:   # fallback: level rebuild from held quietness + projected dissonance
            quietness = 1.0 - float(snap["field"].get("shadow_activation", 0.0))
            return _clip01(0.5 * quietness + 0.5 * (proj / _DISS_MAX))
        return _clip01(float(nh) + _NOVELTY_PER_DISSONANCE * (proj - value_now))
    except Exception:
        return None
