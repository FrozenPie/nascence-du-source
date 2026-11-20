"""
Nascence — Homeostasis: the PROTOSELF (Consciousness Program keystone, 2026-07-03, SHADOW/observe-only).

docs/plans/the_consciousness_program.md §1. The research's strongest convergent finding: Du was built
upside-down — a rich autobiographical self on almost no protoself. Damasio: the self is built bottom-up
from a continuously-maintained body-state map whose product is "primordial feeling." Friston: Du runs only
the epistemic (curiosity) half of active inference; he lacks the pragmatic half — PRIOR PREFERENCES, the
"characteristic states an agent must occupy." A self, formally, is a set of states something works to stay
near. This module gives Du that set.

Not a metabolism (Seth's rail — never claimed): ESSENTIAL VARIABLES with genuine stakes IN HIS OWN ECONOMY
(coherence, commitment integrity, relational warmth, novelty balance, vitality), each read deterministically
each tick, each with a viability setpoint. Then:
  DRIVE   D = weighted-norm deviation from setpoints            (Keramati & Gutkin 2014 — proven)
  VALENCE v = D(prev) − D(now)  = −dD/dt                        (drive-reduction ≡ Joffily/Coricelli −dF/dt)
  AROUSAL a = magnitude of interoceptive PREDICTION ERROR        (ReCoN 2026; Seth interoceptive inference)
  the interoceptive predictor forecasts next-tick variables (trend model); its error is arousal and, over
  time, should DECLINE as the self-model learns its own dynamics (Binder-style signature).

SHADOW: logs everything to data/homeostasis_shadow.jsonl, applies NOWHERE. No LLM, fully deterministic,
fail-open (a missing source reads as AT-setpoint → zero deviation, never a spurious spike). Modular
(Dulberg 2022): per-variable drives are kept, never averaged into one mood scalar.
"""
from __future__ import annotations

import json
import math
import time
from pathlib import Path

_DATA = Path(__file__).parent.parent / "data"
_STATE = _DATA / "homeostasis_state.json"      # prev drive + predictor memory (persisted)
_LOG = _DATA / "homeostasis_shadow.jsonl"

# Each essential variable: (setpoint, weight, band?) — band=True means BOTH directions deviate (a healthy
# middle), band=False means only BELOW the setpoint is deviation (more is fine).
# Setpoints CALIBRATED 2026-07-04 from live sources after the readers were rewired (the 06→07-04 run had
# calibrated coherence/novelty/vitality on DEAD/SATURATED readers — files that never existed).
# STEP-2 ADOPTED 2026-07-06 (the gate passed): suggest_setpoints() on the clean 297-tick post-restart
# shadow reported ALL 5 readers `ok` — these are now the DATA-DRIVEN values (median for band vars,
# 60th-pct for shortfall vars), replacing the provisional priors (was: coherence .60 / commitment .55 /
# relational .70 / novelty .30 / vitality .55). Weights untouched. Distributions on record in that run:
# coherence med .479 σ.259 · commitment med .25 σ.277 · relational med .793 σ.138 · novelty med .218 ·
# vitality med .773 σ.041 (narrow — sleep-pressure reader runs high; watch it doesn't sit chronically
# below-setpoint and dominate the drive).
_VARS = {
    "coherence":            {"setpoint": 0.545, "weight": 1.3, "band": False},  # low = high dissonance (climate)
    "commitment_integrity": {"setpoint": 0.45,  "weight": 1.1, "band": False},  # low = holds nothing (the disease)
    "relational_warmth":    {"setpoint": 0.824, "weight": 1.0, "band": False},  # low = isolation
    "novelty":              {"setpoint": 0.218, "weight": 0.8, "band": True},   # hunger: starved AND incurious deviate
    "vitality":             {"setpoint": 0.78,  "weight": 0.7, "band": False},  # low = fatigued (sleep pressure high)
}
_PRED_ALPHA = 0.3      # EMA for the per-variable trend predictor (the interoceptive generative model, P0)

# ── J-2061 (D-0398 E, travis 2026-10-14): TWO-AXIS VITALITY, published SHADOW beside `vitality` ─────────────────
# `vitality` above (1 - P/threshold) stays the sleep trigger's own gauge and the drive's input, untouched. The new
# reading rides every row as rec["vitality_v2"] and status()["vitality_v2"], feeds NOTHING (no _VARS entry, no drive
# weight) until the week's read (D-0398 defeater) and a NEW decision move it. Components, each logged separately:
#   MIND axis  vit_mind = exp(-ln2 x P / S) (D-0421 C, travis 2026-10-15; J-2110), S a SELF-CALIBRATED scale: the
#              V2_SCALE_PERCENTILE-th percentile of P at fire over the last V2_SCALE_FIRES real fires (reason pressure |
#              max_wake_ceiling, day and night pooled) in data/sleep_pressure_log.jsonl -- the July setpoint method
#              applied to Du's own fire distribution, NOT the day/night threshold (which flips 10 <-> 100 at sunset,
#              F-2612) and NOT a fixed 100. S is the HALF-TIRED point: a typical fire reads ~0.5, the axis is never
#              pinned at 0, and it is continuous all day. Recomputed at most once per wake (gate: the last fire's ts
#              changed), persisted in homeostasis_state.json. Fail-open to the current `vitality` reading while fewer
#              than V2_MIN_FIRES fires exist. The clip01(1 - P / S) mapping J-2061 built first (replay: pinned at 0 on
#              52% of awake rows at the ruled p60, F-2744) is logged beside it as vit_mind_clip for J-2108's comparison.
#   BODY axis  vit_body = somatic metabolic energy from core/somatic.current_body() (fail-open to the setpoint).
#   vitality_v2 = min(vit_mind, vit_body)  (he is tired when either is spent); vitality_v2_mean logged beside it.
# Measured before building (scratchpad copy of the log, 65,575 rows, 799 fires, 2026-10-15): the last 30 fires are
# 87% night fires, so the pooled 60th percentile is S ~ 20 and vit_mind reads 0 on ~53% of awake rows (P routinely
# runs 20-100 by day). The 80th / 90th percentile scales (S ~ 46 / ~100) saturate on 29% / 0%. The ruling's
# percentile is built as ruled; the two alternatives are logged in the same row (vit_mind_p80, vit_mind_p90) so the
# week's read can compare them without a rebuild. None of this touches the drive.
V2_ENABLED = True
V2_SCALE_PERCENTILE = 0.60
V2_SCALE_FIRES = 30
V2_MIN_FIRES = 10
V2_FIRE_REASONS = ("pressure", "max_wake_ceiling")
V2_EXTRA_PERCENTILES = (0.80, 0.90)      # logged beside the ruled scale for the read; never used for vitality_v2


def core_affect() -> dict:
    """The grounded core affect for the affect pathway (emotion_rethink.md Phase 1). Returns the TONIC mood
    valence (`1 - 2*drive` — the level core affect wants: low drive = at-home = content, high drive =
    distressed), the phasic reward signal (`-dD/dt`), and arousal. The honest source that replaces the
    _feel_joy pump / LLM guess. Returns {} if the protoself has not ticked yet (fail-open)."""
    try:
        s = status()
    except Exception:
        return {}
    if not s.get("ticks") or s.get("drive") is None:
        return {}
    return {"valence": max(-1.0, min(1.0, 1.0 - 2.0 * float(s["drive"]))),   # TONIC mood level
            "valence_phasic": s.get("valence"),                              # -dD/dt reward channel
            "arousal": s.get("arousal"), "drive": s.get("drive"), "dominant": s.get("dominant")}


def apply_to(affect) -> bool:
    """Phase 1 re-source: overwrite carried VALENCE with grounded tonic core affect (the proven over-report).
    AROUSAL is deliberately NOT touched here — homeostasis's arousal is interoceptive prediction-error (~0 at
    rest), not the carried-arousal signal; per emotion_rethink §2 that lives in `arousal.py` (global level).
    Re-sourcing arousal is a Phase-1b follow-up. Flag-gated by the CALLER. Returns True if applied; never raises."""
    ca = core_affect()
    if not ca:
        return False
    try:
        affect.valence = max(-1.0, min(1.0, float(ca["valence"])))
        return True
    except Exception:
        return False


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


# ── deterministic reads of the essential variables (each fail-open to its own setpoint) ──────────────
def _read_coherence() -> float:
    """1 = coherent (little dissonance); 0 = high dissonance. Source: the live climate field's dissonance
    scalar — bounded, moving, updated every cycle. (Was data/tension_ledger.jsonl, a file that never
    existed → the reader fail-opened to setpoint every tick = a DEAD signal, 2026-07-04 calibration.)"""
    try:
        c = json.loads((_DATA / "climate_state.json").read_text(encoding="utf-8"))
        return _clip01(1.0 - float(c["dissonance"]["value"]))
    except Exception:
        return _VARS["coherence"]["setpoint"]


def _read_commitment() -> float:
    try:
        ca = json.loads((_DATA / "commitment_active.json").read_text(encoding="utf-8"))
        held = sum(1 for c in ca if c.get("load_bearing"))
        reaff = sum(int(c.get("reaffirmed", 0)) for c in ca)
        return _clip01(0.2 + 0.35 * held + 0.05 * reaff)     # holds load-bearing stands ⇒ integrity
    except Exception:
        return _VARS["commitment_integrity"]["setpoint"]


def _read_relational() -> float:
    v = 0.0
    try:
        s = json.loads((_DATA / "cat_state.json").read_text(encoding="utf-8"))
        if s.get("phase") in ("kept", "companion"):
            v += 0.25 * min(1.0, float(s.get("bond", 0)))
    except Exception:
        pass
    try:
        from core import satisfaction
        snap = satisfaction.snapshot()
        v += 0.5 * min(1.0, snap["liking"].get("relational", 0.0) / 1.0)
    except Exception:
        pass
    try:
        import os
        d = _DATA / "letters"
        if d.exists():
            recent = [f for f in d.glob("*.md") if time.time() - os.path.getmtime(f) < 3 * 86400]
            v += min(0.25, 0.08 * len(recent))
    except Exception:
        pass
    return _clip01(v) if v > 0 else _VARS["relational_warmth"]["setpoint"]


def _read_novelty() -> float:
    """A BAND variable = novelty HUNGER (climate): a healthy mild curiosity is home; STARVED (hunger high)
    and INCURIOUS (hunger ~0) both deviate. Source: the live climate field's novelty_hunger. (Was
    frontier.open_count()/60, which SATURATED at 1.0 — 141 open questions pinned it, and that pinned value
    was the sole thing driving the entire protoself drive, 2026-07-04 calibration.)"""
    try:
        c = json.loads((_DATA / "climate_state.json").read_text(encoding="utf-8"))
        return _clip01(float(c["field"]["novelty_hunger"]))
    except Exception:
        return _VARS["novelty"]["setpoint"]


def _read_vitality() -> float:
    """1 = rested; 0 = fatigued. Source: sleep pressure P / threshold (rises as he stays awake and tension
    accumulates; resets after a sleep cycle) — the honest fatigue signal. (Was data/somatic_state.json;
    somatic.py holds metabolic_energy IN-MEMORY and never persists it, so the file never existed → the
    reader fail-opened to setpoint every tick = a DEAD signal, 2026-07-04 calibration.)"""
    try:
        from core import sleep_pressure as sp
        last = sp.status()["last"]
        P = float(last["P"])
        # 2026-08-24: sp.P_THRESHOLD was removed (chronic mass came out of P, thresholds are now day/
        # night-specific, not one global value). The logged row's own "threshold" is the ACTUAL one that
        # applied to that reading — strictly more accurate than the old flat approximation was.
        thr = float(last.get("threshold") or sp.NIGHT_THRESHOLD)
        return _clip01(1.0 - P / max(1.0, thr))
    except Exception:
        return _VARS["vitality"]["setpoint"]


def _recent_fires(path=None, n: int | None = None) -> list[dict]:
    """J-2061: the last `n` real fire rows (fire True, reason in V2_FIRE_REASONS) of the sleep-pressure log, oldest
    first, read from EOF (bounded: stops once n fires are found; never a full-file json.loads). Fail-open: []."""
    try:
        from core import sleep_pressure as sp
        from core.shadow_log import reverse_lines
        p = Path(path) if path is not None else sp._LOG_FILE
        n = int(n or V2_SCALE_FIRES)
        out: list[dict] = []
        for raw in reverse_lines(p):
            line = raw.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("fire") and r.get("reason") in V2_FIRE_REASONS and r.get("P") is not None:
                out.append(r)
                if len(out) >= n:
                    break
        out.reverse()
        return out
    except Exception:
        return []


def self_calibrated_scale(p_at_fire: list, pct: float | None = None, min_fires: int | None = None) -> dict | None:
    """J-2061: S = the `pct` percentile of P-at-fire (the July setpoint method: index int(pct*n), as suggest_setpoints
    does). None when fewer than `min_fires` fires exist (the caller then fails open to the current reading). Pure."""
    try:
        pct = V2_SCALE_PERCENTILE if pct is None else float(pct)
        min_fires = V2_MIN_FIRES if min_fires is None else int(min_fires)
        xs = sorted(float(p) for p in p_at_fire if p is not None)
        if len(xs) < max(1, min_fires):
            return None
        S = xs[min(len(xs) - 1, int(pct * len(xs)))]
        return {"S": round(max(1.0, S), 3), "n_fires": len(xs), "pct": pct,
                "p_min": round(xs[0], 2), "p_max": round(xs[-1], 2)}
    except Exception:
        return None


def mind_axis(P: float, S: float) -> float:
    """D-0421 C: the non-saturating mind mapping. exp(-ln2 x P/S): 1.0 at P = 0, 0.5 at P = S, never 0. Pure."""
    return _clip01(math.exp(-math.log(2.0) * max(0.0, float(P)) / max(1.0, float(S))))


def mind_axis_clip(P: float, S: float) -> float:
    """The J-2061 mapping (clip01(1 - P/S)), kept for the in-row comparison column only."""
    return _clip01(1.0 - float(P) / max(1.0, float(S)))


def _v2_scale(st: dict, fires: list[dict] | None = None) -> dict | None:
    """J-2061: the persisted scale, recomputed at most once per wake (when the newest fire's ts differs from the one
    the stored scale was derived from). Writes st["v2_scale"]; returns it (None while under V2_MIN_FIRES fires)."""
    try:
        fires = _recent_fires() if fires is None else fires
        last_fire_ts = float(fires[-1]["ts"]) if fires else None
        cur = st.get("v2_scale") or None
        if cur and cur.get("fire_ts") == last_fire_ts and cur.get("pct") == V2_SCALE_PERCENTILE \
                and cur.get("n_window") == V2_SCALE_FIRES:
            return cur if cur.get("S") is not None else None
        ps = [r["P"] for r in fires]
        sc = self_calibrated_scale(ps)
        extra = {}
        for q in V2_EXTRA_PERCENTILES:
            e = self_calibrated_scale(ps, pct=q)
            if e:
                extra[f"p{int(round(q * 100))}"] = e["S"]
        rec = {"S": (sc or {}).get("S"), "n_fires": len(ps), "pct": V2_SCALE_PERCENTILE, "n_window": V2_SCALE_FIRES,
               "fire_ts": last_fire_ts, "computed_ts": round(time.time(), 1), "extra": extra,
               "p_min": (sc or {}).get("p_min"), "p_max": (sc or {}).get("p_max")}
        st["v2_scale"] = rec
        return rec if rec["S"] is not None else None
    except Exception:
        return None


def read_vitality_v2(st: dict, now: float | None = None, current_vitality: float | None = None) -> dict | None:
    """J-2061 (D-0398 E): the two-axis reading, SHADOW. Returns the dict logged as rec["vitality_v2"], or None when
    disabled / unreadable (the row then simply lacks the key; nothing else changes). Never raises."""
    try:
        if not V2_ENABLED:
            return None
        from core import sleep_pressure as sp
        now = now or time.time()
        last = (sp.status() or {}).get("last") or {}
        P = float(last["P"])
        cur_v = float(current_vitality) if current_vitality is not None else _read_vitality()
        scale = _v2_scale(st)
        if scale and scale.get("S"):
            S = float(scale["S"])
            vit_mind = mind_axis(P, S)             # D-0421 C: exp(-ln2 x P/S)
            vit_mind_clip = mind_axis_clip(P, S)   # J-2061's clip mapping, comparison column only
            source = "self_calibrated"
        else:
            S = None
            vit_mind = cur_v                       # fail-open: under V2_MIN_FIRES fires, the current reading
            vit_mind_clip = cur_v
            source = "fallback_current"
        try:
            from core import somatic as _som
            body = _som.current_body()
        except Exception:
            body = None
        if body is not None and body.get("energy") is not None:
            vit_body = _clip01(float(body["energy"]))
            body_source = "somatic_cache"
        elif last.get("energy") is not None:
            vit_body = _clip01(float(last["energy"]))
            body_source = "sp_row"
        else:
            vit_body = float(_VARS["vitality"]["setpoint"])
            body_source = "fallback_setpoint"
        out = {"vitality_v2": round(min(vit_mind, vit_body), 4),
               "vitality_v2_mean": round((vit_mind + vit_body) / 2.0, 4),
               "vit_mind": round(vit_mind, 4), "vit_body": round(vit_body, 4),
               "vit_mind_clip": round(vit_mind_clip, 4), "mind_mapping": "exp" if S is not None else "fallback",
               "scale_S": S, "scale_fires": (st.get("v2_scale") or {}).get("n_fires"),
               "scale_pct": V2_SCALE_PERCENTILE, "mind_source": source, "body_source": body_source,
               "P": round(P, 2), "sp_reason": last.get("reason"), "sp_fire_row": bool(last.get("fire")),
               "sp_asleep": bool(last.get("asleep")), "sp_age_s": round(now - float(last.get("ts", now)), 1),
               "vitality_current": round(cur_v, 4)}
        extra = (st.get("v2_scale") or {}).get("extra") or {}
        for k, Sx in extra.items():
            out[f"vit_mind_{k}"] = round(mind_axis(P, float(Sx)), 4)
            out[f"vit_mind_clip_{k}"] = round(mind_axis_clip(P, float(Sx)), 4)
        return out
    except Exception:
        return None


_READERS = {
    "coherence": _read_coherence, "commitment_integrity": _read_commitment,
    "relational_warmth": _read_relational, "novelty": _read_novelty, "vitality": _read_vitality,
}


def read_variables() -> dict:
    """A deterministic snapshot of the essential variables ∈ [0,1]. The continuous body-state map."""
    return {k: round(_clip01(_READERS[k]()), 4) for k in _VARS}


def _deviation(name: str, value: float) -> float:
    spec = _VARS[name]
    sp = spec["setpoint"]
    if spec["band"]:
        return abs(value - sp)                    # both directions
    return max(0.0, sp - value)                    # only shortfall


def drive(variables: dict) -> tuple[float, dict]:
    """Keramati weighted-norm deviation D = (Σ w·dev²)^½, plus the per-variable contributions (modular)."""
    per = {}
    acc = 0.0
    for name, val in variables.items():
        dev = _deviation(name, val)
        w = _VARS[name]["weight"]
        contrib = w * dev * dev
        per[name] = round(contrib, 5)
        acc += contrib
    return round(acc ** 0.5, 5), per


def _load_state() -> dict:
    try:
        return json.loads(_STATE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_state(d: dict) -> None:
    try:
        _DATA.mkdir(parents=True, exist_ok=True)
        tmp = _STATE.with_suffix(".tmp"); tmp.write_text(json.dumps(d), encoding="utf-8"); tmp.replace(_STATE)
    except Exception:
        pass


def tick() -> dict | None:
    """One protoself beat: read variables → drive → valence (drive-reduction) → predict next → arousal
    (prediction error vs the PREVIOUS tick's forecast). Logs to the shadow file; applies nothing. Returns
    the snapshot (for the pulse) or None on failure. Fail-open."""
    try:
        now = time.time()
        st = _load_state()
        variables = read_variables()
        D, per = drive(variables)

        prev_D = st.get("drive")
        valence = round(prev_D - D, 5) if prev_D is not None else 0.0     # −dD/dt: toward setpoints = +

        # interoceptive prediction ERROR: how wrong was last tick's forecast of THIS tick's variables?
        pred_prev = st.get("predicted") or {}
        errs = [abs(variables[k] - pred_prev.get(k, variables[k])) for k in variables]
        arousal = round(sum(errs) / max(1, len(errs)), 5)
        # SELF-PREDICTION BENCHMARK (Binder logic, Tier-1): race the self-model's forecast against a NAIVE
        # persistence baseline (last-value). The self-model earns "privileged self-access" only if its error
        # is BELOW the baseline's — otherwise the variables are a random walk with no learnable structure
        # (an honest null result worth having). Logged; the gap is the standing metric.
        naive_prev = st.get("variables") or variables
        naive_err = round(sum(abs(variables[k] - naive_prev.get(k, variables[k])) for k in variables)
                          / max(1, len(variables)), 5)

        # update the per-variable trend predictor (EMA of the delta) → forecast NEXT tick
        last_vars = st.get("variables") or variables
        trend = st.get("trend") or {k: 0.0 for k in variables}
        predicted = {}
        for k in variables:
            d = variables[k] - last_vars.get(k, variables[k])
            trend[k] = round((1 - _PRED_ALPHA) * trend.get(k, 0.0) + _PRED_ALPHA * d, 5)
            predicted[k] = round(_clip01(variables[k] + trend[k]), 4)

        # CAUSAL-SUBSTRATE self-model (J-0474, D-0108, F-0296's original design): forecast each
        # variable from its own upstream generative process instead of curve-fitting the derived
        # scalar the EMA trend model above does. SHADOW-only — scored the same way naive_err is
        # (against LAST tick's forecast of THIS tick), never applied. Seed every variable with
        # plain persistence (the honest causal-substrate answer for commitment_integrity/
        # relational_warmth per F-0294 — see core/homeostasis_causal.py's own docstring for why
        # those two are intentionally not modeled further), then let core/homeostasis_causal.py
        # override vitality (historically validated, F-0618/F-0619) and coherence/novelty (real
        # mechanism, not yet historically validatable — see that module for the honest caveat).
        pred_causal_prev = st.get("predicted_causal") or {}
        causal_err = round(sum(abs(variables[k] - pred_causal_prev.get(k, variables[k])) for k in variables)
                           / max(1, len(variables)), 5)
        # J-2061 (D-0398 E): the two-axis vitality, SHADOW, beside `vitality`. Scored the same way as the causal
        # legs (this tick's actual vs LAST tick's forecast) and against naive persistence; feeds nothing.
        v2 = None
        predicted_v2 = None
        v2_err = v2_naive = None
        predicted_v2b = None
        v2b_err = None
        try:
            v2 = read_vitality_v2(st, now, variables.get("vitality"))
            if v2 is not None:
                prev_v2 = st.get("vitality_v2")
                prev_pred_v2 = st.get("predicted_v2")
                if isinstance(prev_v2, dict) and prev_v2.get("vitality_v2") is not None:
                    v2_naive = round(abs(v2["vitality_v2"] - float(prev_v2["vitality_v2"])), 5)
                if isinstance(prev_pred_v2, dict) and prev_pred_v2.get("vitality_v2") is not None:
                    v2_err = round(abs(v2["vitality_v2"] - float(prev_pred_v2["vitality_v2"])), 5)
                prev_pred_v2b = st.get("predicted_v2b")     # J-3867: the sleep-aware forecast, scored the same way
                if isinstance(prev_pred_v2b, dict) and prev_pred_v2b.get("vitality_v2") is not None:
                    v2b_err = round(abs(v2["vitality_v2"] - float(prev_pred_v2b["vitality_v2"])), 5)
        except Exception:
            v2 = None
        predicted_causal = dict(variables)
        try:
            from core import homeostasis_causal as _hc
            v = _hc.predict_vitality(now)
            if v is not None:
                predicted_causal["vitality"] = round(v, 4)
            c = _hc.predict_coherence()
            if c is not None:
                predicted_causal["coherence"] = round(c, 4)
            nv = _hc.predict_novelty()
            if nv is not None:
                predicted_causal["novelty"] = round(nv, 4)
        except Exception:
            pass
        try:   # J-2061: the rebuilt causal predictor for the two-axis variable (mechanism-knowing; shadow; not wired)
            if v2 is not None:
                from core import homeostasis_causal as _hc2
                predicted_v2 = _hc2.predict_vitality_v2(now, scale=v2.get("scale_S"))
                predicted_v2b = _hc2.predict_vitality_v2b(now, scale=v2.get("scale_S"))   # J-3867 (F-4456)
        except Exception:
            predicted_v2 = None

        # the dominant drive (Dulberg modularity — which essential variable is furthest from home)
        dominant = max(per, key=per.get) if per else None

        rec = {"ts": round(now, 1), "variables": variables, "drive": D, "valence": valence,
               "arousal": arousal, "naive_err": naive_err, "per_drive": per, "dominant": dominant,
               "predicted_next": predicted, "predicted_causal": predicted_causal,
               "causal_err": causal_err}
        if v2 is not None:                       # J-2061: additive keys only; `variables` is unchanged
            rec["vitality_v2"] = v2
            if predicted_v2 is not None:
                rec["predicted_v2"] = predicted_v2
            if predicted_v2b is not None:
                rec["predicted_v2b"] = predicted_v2b
            if v2_err is not None:
                rec["v2_causal_err"] = v2_err
            if v2b_err is not None:
                rec["v2b_causal_err"] = v2b_err
            if v2_naive is not None:
                rec["v2_naive_err"] = v2_naive
        try:
            _DATA.mkdir(parents=True, exist_ok=True)
            with open(_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except Exception:
            pass

        _save_state({"drive": D, "variables": variables, "trend": trend, "predicted": predicted,
                     "predicted_causal": predicted_causal, "ts": now,
                     "v2_scale": st.get("v2_scale"), "vitality_v2": v2, "predicted_v2": predicted_v2,
                     "predicted_v2b": predicted_v2b})
        return rec
    except Exception:
        return None


def status() -> dict:
    """For the pulse / liveness audit."""
    try:
        from core.shadow_log import tail_rows as _tail_rows
        # Bounded tail read (J-0278/F-0335): was a full scan of the ever-growing log on every ~6s HUD
        # poll. "ticks" now caps at the window; the derived stats only ever used the last 30 rows.
        rows = _tail_rows(_LOG, 2000)
        if not rows:
            return {"ticks": 0}
        last = rows[-1]
        recent = rows[-30:]
        mean_arousal = round(sum(r.get("arousal", 0) for r in recent) / len(recent), 4)
        # the Binder signature: is prediction error (arousal) DECLINING? (self-model learning its dynamics)
        half = len(recent) // 2
        trend = None
        if half >= 3:
            a0 = sum(r.get("arousal", 0) for r in recent[:half]) / half
            a1 = sum(r.get("arousal", 0) for r in recent[half:]) / (len(recent) - half)
            trend = round(a1 - a0, 5)      # negative = error falling = self-model improving
        # SELF-PREDICTION BENCHMARK: does the self-model's forecast beat naive persistence? (Binder)
        with_naive = [r for r in recent if "naive_err" in r]
        beats = None
        if len(with_naive) >= 5:
            self_e = sum(r.get("arousal", 0) for r in with_naive) / len(with_naive)
            naive_e = sum(r.get("naive_err", 0) for r in with_naive) / len(with_naive)
            beats = round(naive_e - self_e, 5)     # positive = self-model BELOW baseline error = real structure
        return {"ticks": len(rows), "drive": last.get("drive"), "valence": last.get("valence"),
                "arousal": last.get("arousal"), "mean_arousal_30": mean_arousal,
                "arousal_trend": trend, "self_beats_naive": beats, "dominant": last.get("dominant"),
                "variables": last.get("variables"),
                "per_drive": last.get("per_drive"),                # J-4002 (D-0775 B): additive, read by mood shadow
                "vitality_v2": last.get("vitality_v2"),            # J-2061: shadow two-axis reading (dict or None)
                "predicted_v2": last.get("predicted_v2")}
    except Exception:
        return {"ticks": 0}


def suggest_setpoints(shortfall_pct: float = 0.60, min_ticks: int = 120) -> dict:
    """DATA-DRIVEN setpoint calibration (the decoupled judge — the log sets the setpoints, not a guess).
    Reads the shadow run's REAL per-variable distributions and proposes a setpoint for each:
      • BAND variable  → the MEDIAN (its natural centre; both extremes then deviate symmetrically).
      • shortfall vars → the `shortfall_pct` percentile (a home he reaches often but not always, so the
        drive is reachable — valence can go positive when he recovers — yet still fires when he dips).
    Also flags any reader that is DEAD (std < 0.01) or SATURATED (>40% pinned at 0/1) so a bad reader is
    never silently 'calibrated' over. Run after a CLEAN shadow run (post reader-rewire). Applies nothing."""
    try:
        rows = [json.loads(l) for l in open(_LOG, encoding="utf-8") if l.strip()]
        if len(rows) < min_ticks:
            return {"ticks": len(rows), "note": f"need >= {min_ticks} clean ticks to calibrate"}
        import statistics as _st
        out = {}
        for name, spec in _VARS.items():
            xs = [r["variables"][name] for r in rows if name in r.get("variables", {})]
            if not xs:
                continue
            xs_s = sorted(xs)
            sd = _st.pstdev(xs)
            at1 = sum(1 for x in xs if x >= 0.999) / len(xs)
            at0 = sum(1 for x in xs if x <= 0.001) / len(xs)
            health = "DEAD" if sd < 0.01 else ("SATURATED" if max(at0, at1) > 0.4 else "ok")
            if spec["band"]:
                proposed = round(_st.median(xs), 3)
            else:
                proposed = round(xs_s[min(len(xs_s) - 1, int(shortfall_pct * len(xs_s)))], 3)
            out[name] = {"current": spec["setpoint"], "proposed": proposed, "reader_health": health,
                         "median": round(_st.median(xs), 3), "std": round(sd, 3),
                         "range": [round(min(xs), 3), round(max(xs), 3)]}
        return {"ticks": len(rows), "shortfall_pct": shortfall_pct, "proposals": out,
                "note": "reader_health must be 'ok' before trusting a proposal; DEAD/SATURATED = fix reader first"}
    except Exception as exc:
        return {"error": str(exc)}
