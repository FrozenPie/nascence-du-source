"""
Nascence -- the DETERMINISTIC-URGENCY SHADOW beside Salience's model urgency (J-3402, D-0682 ruling 2026-11-05).
OBSERVE-ONLY.  Changes nothing any consumer reads.

WHY (J-3164, F-4024 / F-4025 / F-4026): the Salience LLM call's urgency is near-constant, and J-3164's ablation found
the Executive's output does not depend on the `Salience:` line.  But that urgency still feeds THREE base systems --
the climate salience warp, the somatic tick (visceral tension) and the attention schema's bandwidth -- so retiring the
call needs evidence that a DETERMINISTIC urgency (internal=low, human=moderate, explicit time-pressure words or a
human correction=high, both=pressing; scripts/lab_salience_ablation_J3164.py det_urgency, pre-registered there) moves
those three outputs no further than the model's own urgency did.  D-0682 rules: retire the call, SHADOW FIRST, switch
on only after this comparison on live cycles.  D-0682's defeater: the attention-bandwidth term, somatic tension or
climate warp moving OUTSIDE the range the model produced (model range 0.0-0.4 for the bandwidth term, human mean
0.084), or a larger high-urgency sample showing the Executive changes with the urgency word.

WHAT: one row per cycle in data/training/urgency_shadow.jsonl, assembled from three hooks that sit next to the three
consumers in core/orchestrator.py:
    observe_climate(state)   just BEFORE the climate warp  -> model urgency as the node returned it, the deterministic
                                                              word/number + why, and the warp each would produce
    observe_attention(state) right after _compute_attention -> the bandwidth each urgency would give (same affect)
    observe_somatic(...)     just BEFORE somatic.tick_cycle -> the visceral-tension target each would give; FLUSHES
                                                              the row ("complete": true)
A cycle that never reaches the somatic tick (an early return) is flushed by the NEXT cycle's observe_climate as a
partial row ("complete": false), so no Salience cycle is silently lost.  The deterministic urgency NEVER replaces
anything: the consumers keep reading state.salience.urgency exactly as before.

NUMBERS: the deterministic word maps to a mid-band number for the arithmetic (low .15 / moderate .45 / high .70 /
pressing .90 -- the middles of core.mood.urgency_word's bands), the same table J-3164 used.  The bandwidth, tension and
warp formulas are COPIED from the consumers (orchestrator._compute_attention, somatic.tick_cycle, the orchestrator's
climate warp block); scripts/_test_J3402_urgency_shadow.py runs the REAL _compute_attention and tick_cycle against this
module's arithmetic so a drift in either consumer fails the test instead of silently skewing the evidence.

READER: scripts/urgency_shadow_summary.py (range comparison against the D-0682 defeater).  A named read job is
spawned with the build.  No prompt: this module makes no model call and is registered nowhere.

Fail-open throughout (the orchestrator wraps every hook in a bare try/except and this module swallows its own errors
too).  Write-fenced: profile.guard_path() resolves the log path OUTSIDE the fail-open try (D-0179 / D-0250), so a
non-live process raises NonLiveWriteError instead of touching the real store; lab_env.isolate(also=...) or a
monkeypatched `_LOG` redirects it in tests.  Kill switch: URGENCY_SHADOW_ENABLED = False (restart-gated like the
rest of the build).
"""
from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path

from core import profile

logger = logging.getLogger("nascence.urgency_shadow")

URGENCY_SHADOW_ENABLED = True    # kill switch.  Observe-only: True adds one JSONL row per cycle and nothing else.

_DATA = Path(__file__).parent.parent / "data"
_LOG = _DATA / "training" / "urgency_shadow.jsonl"

# Pre-registered in scripts/lab_salience_ablation_J3164.py (before any generation was run); copied, and the test
# asserts the two agree over a battery so the shadow cannot drift from the rule the ruling named.
_TIME_PRESSURE = re.compile(
    r"\b(urgent(?:ly)?|immediately|right now|right away|asap|at once|hurry|hurried|quickly|deadline|emergency|"
    r"time[- ]sensitive|running out of time|before it'?s too late|no time|as soon as possible)\b", re.I)
URGENCY_NUM = {"low": 0.15, "moderate": 0.45, "high": 0.7, "pressing": 0.9}

_MAX_PENDING = 8                 # cycles in flight at once is 1; the bound only protects against a leak
_PENDING: dict[str, dict] = {}


def det_urgency(input_type: str, raw: str, correction: str | None) -> tuple[str, list[str]]:
    """The J-3164 rule: internal=low, human=moderate; time-pressure words OR a human correction => high; both =>
    pressing."""
    why: list[str] = [f"base:{input_type}"]
    word = "moderate" if input_type == "human" else "low"
    tp = bool(_TIME_PRESSURE.search(raw or ""))
    if tp:
        why.append("time_pressure")
    if correction:
        why.append(f"correction:{correction}")
    if tp and correction:
        word = "pressing"
    elif tp or correction:
        word = "high"
    return word, why


# ── the three consumers' arithmetic, copied (parity enforced by the test) ───────────────────────────────────
def warp_bump(shadow_activation: float, world_model_strain: float) -> float:
    """orchestrator climate warp: urgency += 0.10*shadow_activation + 0.05*world_model_strain, capped at 1.0."""
    return 0.10 * float(shadow_activation or 0.0) + 0.05 * float(world_model_strain or 0.0)


def warped(urgency: float, bump: float) -> float:
    return min(1.0, float(urgency) + bump)


def bandwidth(arousal: float, fear: float, urgency: float) -> float:
    """orchestrator._compute_attention: narrowing = 0.5*arousal + 0.3*fear + 0.4*urgency; floor .1, cap 1.0, rounded
    to 2 places exactly as AttentionSchema stores it."""
    narrowing = 0.5 * float(arousal) + 0.3 * float(fear) + 0.4 * float(urgency)
    return round(max(0.1, min(1.0, 1.0 - narrowing)), 2)


def target_tension(urgency: float, arousal: float) -> float:
    """somatic.tick_cycle: target_tension = clamp(0.6*urgency + 0.4*arousal)."""
    return max(0.0, min(1.0, 0.6 * float(urgency) + 0.4 * float(arousal)))


def tension_after(prev: float, urgency: float, arousal: float) -> float:
    """somatic.tick_cycle: visceral_tension = round(0.5*prev + 0.5*target, 4)."""
    return round(0.5 * float(prev) + 0.5 * target_tension(urgency, arousal), 4)


# ── hooks ────────────────────────────────────────────────────────────────────────────────────────────────────
def _f(x, nd: int = 4):
    try:
        return round(float(x), nd)
    except Exception:
        return None


def _det_for(state) -> tuple[str, float, list[str], str | None]:
    it = getattr(state, "input_type", "human")
    raw = getattr(state, "raw_input", "") or ""
    corr = None
    if it == "human":
        try:
            from core.error_pathway import detect_human_correction
            corr = detect_human_correction(raw)
        except Exception:
            corr = None
    word, why = det_urgency(it, raw, corr)
    return word, URGENCY_NUM[word], why, corr


def _flush(row: dict, complete: bool) -> None:
    row["complete"] = complete
    _write(row)


def observe_climate(state) -> dict | None:
    """Hook 1 -- call just BEFORE the climate warp block mutates state.salience.urgency.  Starts this cycle's row."""
    if not URGENCY_SHADOW_ENABLED:
        return None
    try:
        # A previous cycle that never reached the somatic tick is flushed now, partial, rather than lost.
        for cid in [c for c in _PENDING if c != getattr(state, "cycle_id", "")]:
            _stale = _PENDING.pop(cid)
            try:
                _flush(_stale, False)
            except Exception:
                pass
        sal = getattr(state, "salience", None)
        clim = getattr(state, "climate", None)
        sa = getattr(clim, "shadow_activation", 0.0) if clim is not None else 0.0
        ws = getattr(clim, "world_model_strain", 0.0) if clim is not None else 0.0
        bump = warp_bump(sa, ws)
        word, num, why, corr = _det_for(state)
        mu = _f(getattr(sal, "urgency", None)) if sal is not None else None
        row = {
            "ts": round(time.time(), 1),
            "cycle_id": getattr(state, "cycle_id", ""),
            "input_type": getattr(state, "input_type", ""),
            "model": {
                "urgency_raw": mu,
                "word": _model_word(mu),
                "interrupt": bool(getattr(sal, "interrupt", False)) if sal is not None else None,
                "has_salience": sal is not None,
            },
            "det": {"word": word, "urgency": num, "why": why, "correction": corr,
                    "time_pressure": "time_pressure" in why},
            "climate": {
                "applies": bool(sal is not None and clim is not None),
                "shadow_activation": _f(sa), "world_model_strain": _f(ws), "bump": _f(bump),
                "model_warped": _f(warped(mu, bump)) if mu is not None else None,
                "det_warped": _f(warped(num, bump)),
            },
            "bandwidth": None,
            "somatic": None,
        }
        # Remember the numbers the later hooks need: what the consumers will actually read (state.salience.urgency
        # AFTER the warp) is read live by those hooks; the deterministic arm needs the same bump added.
        row["_bump"] = bump
        row["_det_num"] = num
        _PENDING[row["cycle_id"]] = row
        while len(_PENDING) > _MAX_PENDING:
            _PENDING.pop(next(iter(_PENDING)), None)
        return row
    except Exception as exc:
        logger.debug("[urgency_shadow] observe_climate failed (non-fatal): %s", exc)
        return None


def observe_attention(state) -> None:
    """Hook 2 -- call right AFTER orchestrator._compute_attention().  Same affect for both arms; only urgency differs.
    The model arm reads the urgency _compute_attention itself read (state.salience.urgency, post-warp, 0.0 if no
    salience); the deterministic arm is the deterministic number plus the same climate bump."""
    if not URGENCY_SHADOW_ENABLED:
        return
    try:
        row = _PENDING.get(getattr(state, "cycle_id", ""))
        if row is None:
            return
        aff = state.affect
        sal = getattr(state, "salience", None)
        u_model = float(sal.urgency) if sal is not None else 0.0
        u_det = warped(row["_det_num"], row["_bump"])
        att = getattr(state, "attention", None)
        row["bandwidth"] = {
            "arousal": _f(aff.arousal), "fear": _f(aff.fear),
            "model_urgency_consumed": _f(u_model), "det_urgency_consumed": _f(u_det),
            "model": bandwidth(aff.arousal, aff.fear, u_model),
            "det": bandwidth(aff.arousal, aff.fear, u_det),
            "live_attention_bandwidth": _f(getattr(att, "bandwidth", None), 2) if att is not None else None,
            "model_urgency_term": _f(0.4 * u_model), "det_urgency_term": _f(0.4 * u_det),
        }
        row["bandwidth"]["delta"] = _f(row["bandwidth"]["det"] - row["bandwidth"]["model"], 2)
    except Exception as exc:
        logger.debug("[urgency_shadow] observe_attention failed (non-fatal): %s", exc)


def observe_somatic(state, *, urgency: float, arousal: float, prev_tension: float) -> None:
    """Hook 3 -- call just BEFORE somatic.tick_cycle(), with the SAME urgency/arousal the tick is about to receive and
    the visceral tension as it stands before the tick.  Flushes the row (complete)."""
    if not URGENCY_SHADOW_ENABLED:
        return
    cid = getattr(state, "cycle_id", "")
    row = _PENDING.pop(cid, None)
    if row is None:
        return
    try:
        u_det = warped(row["_det_num"], row["_bump"])
        row["somatic"] = {
            "arousal": _f(arousal), "prev_tension": _f(prev_tension),
            "model_urgency_consumed": _f(urgency), "det_urgency_consumed": _f(u_det),
            "model_term": _f(0.6 * float(urgency)), "det_term": _f(0.6 * u_det),
            "model_target": _f(target_tension(urgency, arousal)), "det_target": _f(target_tension(u_det, arousal)),
            "model_tension_after": tension_after(prev_tension, urgency, arousal),
            "det_tension_after": tension_after(prev_tension, u_det, arousal),
        }
        row["somatic"]["delta_target"] = _f(row["somatic"]["det_target"] - row["somatic"]["model_target"])
    except Exception as exc:
        logger.debug("[urgency_shadow] observe_somatic failed (non-fatal): %s", exc)
    try:
        _flush(row, True)
    except Exception as exc:       # NonLiveWriteError from the fence reaches here only when the caller is non-live
        logger.debug("[urgency_shadow] flush failed (non-fatal): %s", exc)


def _model_word(u) -> str | None:
    if u is None:
        return None
    try:
        from core.mood import urgency_word
        return urgency_word(u)
    except Exception:
        return None


def _write(row: dict) -> None:
    out = {k: v for k, v in row.items() if not k.startswith("_")}
    path = profile.guard_path(_LOG)   # fence resolved OUTSIDE the fail-open try (D-0179 / D-0250 convention)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(out, ensure_ascii=False) + "\n")
    except Exception:
        pass


def status() -> dict:
    try:
        rows = [json.loads(l) for l in open(_LOG, encoding="utf-8") if l.strip()]
        return {"rows": len(rows), "complete": sum(1 for r in rows if r.get("complete")),
                "enabled": URGENCY_SHADOW_ENABLED}
    except Exception:
        return {"rows": 0, "complete": 0, "enabled": URGENCY_SHADOW_ENABLED}
