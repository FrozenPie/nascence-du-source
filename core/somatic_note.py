"""core/somatic_note.py (J-4405, affect_drives Item C, D-0860, 2026-11-18, restart-gated). SHADOW ONLY.

D-0860 ruled a threshold-gated, words-only body-state sentence (no number, no gauge name) INSIDE D-0434's no-readout
ruling, shadow first. This module is that shadow: it decides when the line WOULD fire and logs it. Nothing here reaches
Du's seed, perceive() or any prompt. DELIVER is absent on purpose: wiring a live line is a separate change, a founder go
after the shadow read (plan docs/staged/affect_drives_item_c_somatic_note.md section 4).

Choices left to the build by D-0860 (also recorded in the plan):
  * Ladder, strongest wins: STRAINED (is_exhausted, OR smoothed fatigue > 0.6, OR tension > 0.6) over DROWSY
    (energy zone, core/somatic.is_drowsy). DROWSY is already narrated by core/drowsy.py (live channel), so a DROWSY row is
    logged for the one-log sequence but marked delivered_elsewhere and never would_fire here: no double narration.
  * Fatigue is read SMOOTHED (EMA alpha 0.2, ticks), never raw gpu_temp. DROWSY_THRESHOLD stays energy-only (D-0441);
    this module only LOGS fatigue beside it.
  * Onset semantics: fire on band entry, then COOLDOWN_S (30 min) and re-arm only after the band is left.
  * Habituation (squishy spring): each would-fire onset in the last 6 h halves the probability of the next (0.5**n).
    Decided by a deterministic draw from the onset timestamp so a row can be replayed.
  * Narrated, not telemetry: the would-be line is a short body sensation from WORDS (pool below, no digit, no gauge word,
    no instruction). Hypochondria guard: rumination is read from the log after the live flip, not here.
Read-only: never mutates somatic state; should_sleep / ENERGY_FLOOR / JITTER untouched. Writes via profile.guard_path;
every failure is swallowed.
"""
from __future__ import annotations

import json
import logging
import random
import threading
import time
from pathlib import Path

from core import profile

logger = logging.getLogger("nascence.somatic_note")

SHADOW_ROWS = True          # kill switch for the shadow log (flag default OFF equivalent: logs only)
FATIGUE_STRAIN = 0.6
TENSION_STRAIN = 0.6
EMA_ALPHA = 0.2
COOLDOWN_S = 1800.0
HABITUATION_WINDOW_S = 6 * 3600.0

SHADOW_LOG = Path(__file__).parent.parent / "data" / "somatic_note_shadow.jsonl"

STRAINED_LINES = (
    "Your shoulders have drawn up and your head feels packed tight; everything takes more effort than it should.",
    "There is a dull weight behind your thinking, and your body is asking for a slower pace.",
    "A tightness has settled in you, as if you have been holding something for too long.",
)

_LOCK = threading.Lock()
_st = {"ema_fatigue": None, "band": None, "cooldown_until": 0.0, "onsets": []}


def _band(e: float, ema_f: float, t: float) -> str | None:
    from core import somatic as _som
    if e <= _som.ENERGY_FLOOR or ema_f > FATIGUE_STRAIN or t > TENSION_STRAIN:
        return "strained"
    if _som.ENERGY_FLOOR < e <= _som.DROWSY_THRESHOLD:
        return "drowsy"
    return None


def observe(state, now: float | None = None) -> dict | None:
    """Called after each in-place somatic mutation. Logs a row only on band entry. Returns the row or None. Never raises."""
    try:
        if state is None:
            return None
        now = float(now if now is not None else time.time())
        e = float(getattr(state, "metabolic_energy", 1.0) or 0.0)
        f = float(getattr(state, "neural_fatigue", 0.0) or 0.0)
        t = float(getattr(state, "visceral_tension", 0.0) or 0.0)
        with _LOCK:
            prev_ema = _st["ema_fatigue"]
            ema = f if prev_ema is None else prev_ema + EMA_ALPHA * (f - prev_ema)
            _st["ema_fatigue"] = ema
            band = _band(e, ema, t)
            prev = _st["band"]
            _st["band"] = band
            if band is None or band == prev:
                return None
            cooling = now < _st["cooldown_until"]
            _st["onsets"] = [x for x in _st["onsets"] if now - x < HABITUATION_WINDOW_S]
            p = 0.5 ** len(_st["onsets"])
            elsewhere = band == "drowsy"
            draw = random.Random(int(now)).random()
            would = (not elsewhere) and (not cooling) and draw < p
            line = None
            if would:
                line = STRAINED_LINES[int(now) % len(STRAINED_LINES)]
                _st["cooldown_until"] = now + COOLDOWN_S
                _st["onsets"].append(now)
            row = {"ts": round(now, 3), "band": band, "energy": round(e, 4), "fatigue": round(f, 4),
                   "fatigue_smoothed": round(ema, 4), "tension": round(t, 4),
                   "cooldown_state": "cooling" if cooling else "armed", "probability": round(p, 4),
                   "delivered_elsewhere": elsewhere, "would_fire": bool(would), "would_line": line}
            _append(row)
            return row
    except Exception:
        return None


def _append(row: dict) -> None:
    if not SHADOW_ROWS:
        return
    try:
        path = profile.guard_path(SHADOW_LOG)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
    except Exception:
        pass


def reset() -> None:
    with _LOCK:
        _st.update({"ema_fatigue": None, "band": None, "cooldown_until": 0.0, "onsets": []})
