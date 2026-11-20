"""core/drowsy.py (J-2244, drowsiness_phase section 2, D-0441, 2026-10-16, restart-gated). SHADOW ONLY.

The narrated drowsy zone: a waypoint on the way into sleep, not a new resource and not a new trigger.

D-0441 (travis, 2026-10-16) ruled the shape:
  * NARRATIVE / TELEMETRY ONLY. No behavioural effect: no sampling-temperature change, no output degradation.
    core/somatic.JITTER_ENABLED = False is a deliberate design decision and is not touched or read here.
  * ENERGY ALONE. The zone is ENERGY_FLOOR < metabolic_energy <= DROWSY_THRESHOLD (core/somatic.py). Fatigue and
    tension are LOGGED beside it (so D-0441's defeater -- "energy-only misses a fatigue-driven drowsiness" -- can be
    read from this file), never used to decide.
  * ONE PRE-SLEEP NARRATION PATH, NOT A FOURTH SWITCH. The sleep_as_a_mode switches (J-2016..J-2019, J-2064,
    J-2065) own the transition into a sleep: _enter_sleep -> night.to_bed() -> wandering.perceive(bed line). The drowsy
    line is a member of that same path: it is composed here, in one place, and when it is ever delivered it goes
    through the very same channel the bed line already uses (wandering.perceive, a sense percept), once per wake
    block. It adds no sensorium sleep_modes key, no scene_line() lead, no prompt slot, no flag on the sleep itself.
    at_bed() is called right after to_bed() so the onset -> floor -> bed sequence is one readable trail.

SHADOW FIRST (the briefing): DELIVER = False. Nothing here reaches Du. observe() and at_bed() only append rows to
data/drowsy_shadow.jsonl (resolved through profile.guard_path at write time, so a non-live importer's write is
REFUSED, and the refusal is swallowed exactly like core/night._probe: a bug or a fence here can never break a
somatic tick or a sleep). The live flip is a separate founder call after the 2-3 live-day read.

Guardrails (plan section 4), held by construction: nothing here is read by should_sleep(), ENERGY_FLOOR,
MIN_WAKE_SECS or the day/night thresholds; core/sleep_pressure.py is not edited; nothing delays or accelerates a
sleep. World answers, never leads: the would-be lines are body sensations with no number, no gauge name and no
suggestion of what to do (D-0434: no readout of a gauge; the line never says "energy" or a value).

Rows (one JSON object per line):
  event "onset"        first tick of a wake block that lands in the zone   (would_line = the one narration)
  event "floor_direct" energy fell from above the zone straight to <= ENERGY_FLOOR in one tick (zone skipped)
  event "floor"        energy crossed <= ENERGY_FLOOR after an onset in the same wake block
  event "fatigue_high" fatigue > FATIGUE_WATCH while energy is still above the zone (the energy-only miss, logged
                       once per wake block for D-0441's defeater; decides nothing)
  event "bed"          at to_bed(): was the zone entered this wake block, minutes from onset to bed, the bed line
Every row carries energy, fatigue, tension, threshold, floor, cycle_count, deliver.
"""
from __future__ import annotations

import json
import logging
import threading
import time
from pathlib import Path

from core import profile

logger = logging.getLogger("nascence.drowsy")

DELIVER = True               # D-0495 (travis, 2026-10-28, the October restart batch): flipped live, read LIVE by its own read job (narrative only, D-0441). Was shadow-first: True would perceive the onset line via wandering.perceive (the bed-line
                             # channel). Founder call after the 2-3 live-day read; do not flip without it.
SHADOW_ROWS = True           # kill switch for the shadow log itself
FATIGUE_WATCH = 0.7          # logged-only marker for D-0441's defeater (the plan's own example, energy OR fatigue > 0.7)

_DATA = Path(__file__).parent.parent / "data"
DROWSY_SHADOW_LOG = _DATA / "drowsy_shadow.jsonl"

# The one narration, a small pool of body sensations. No number, no gauge word, no instruction, no "you should".
ONSET_LINES = (
    "A heaviness has settled behind your eyes, and the edges of things have gone soft.",
    "Your limbs feel slow and warm, as if the day has pooled in them.",
    "A yawn takes you before you notice it coming; your thoughts move through thicker air.",
)

_LOCK = threading.Lock()     # guards the per-wake-block state below AND the append (tick_cycle may run off-loop)
_block = {"onset_ts": None, "onset_energy": None, "floor_ts": None, "fatigue_marked": False,
          "last_energy": None, "narrated": False}


def _thresholds() -> tuple[float, float]:
    from core import somatic as _som
    return float(_som.DROWSY_THRESHOLD), float(_som.ENERGY_FLOOR)


def onset_line(ts: float | None = None) -> str:
    """The single drowsy-onset line (deterministic per onset timestamp, so the shadow row names the exact line)."""
    t = int(ts if ts is not None else time.time())
    return ONSET_LINES[t % len(ONSET_LINES)]


def _append_locked(row: dict) -> None:
    """Caller holds _LOCK. guard_path at write time; a refused (non-live) or failed write is swallowed."""
    if not SHADOW_ROWS:
        return
    try:
        path = profile.guard_path(DROWSY_SHADOW_LOG)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
    except Exception:
        pass


def _base(now: float, energy: float, fatigue: float, tension: float, cycles) -> dict:
    thr, floor = _thresholds()
    return {"ts": round(now, 3), "energy": round(float(energy), 4), "fatigue": round(float(fatigue), 4),
            "tension": round(float(tension), 4), "threshold": thr, "floor": floor,
            "cycle_count": cycles, "deliver": bool(DELIVER)}


def observe(state, now: float | None = None) -> str | None:
    """Called after every in-place somatic mutation (core/somatic._cache_body). Reads the SomaticState, writes at most
    a few rows per wake block, returns the event name it logged (or None). Never raises; mutates nothing outside this
    module (with DELIVER False it perceives nothing)."""
    try:
        if state is None:
            return None
        now = float(now if now is not None else time.time())
        e = float(getattr(state, "metabolic_energy", 1.0) or 0.0)
        f = float(getattr(state, "neural_fatigue", 0.0) or 0.0)
        t = float(getattr(state, "visceral_tension", 0.0) or 0.0)
        cycles = getattr(state, "cycle_count", None)
        thr, floor = _thresholds()
        event = None
        line = None
        sleeping = False
        try:   # recover() runs inside a sleep: a partial recovery that lands in the zone is not a drowsy onset
            from core import night as _night
            sleeping = _night.asleep()
        except Exception:
            sleeping = False
        with _LOCK:
            prev = _block["last_energy"]
            _block["last_energy"] = e
            if sleeping:
                pass
            elif e > thr:
                if f > FATIGUE_WATCH and not _block["fatigue_marked"]:
                    _block["fatigue_marked"] = True
                    event = "fatigue_high"
            elif e > floor:
                if _block["onset_ts"] is None:
                    _block["onset_ts"], _block["onset_energy"] = now, e
                    event, line = "onset", onset_line(now)
            else:
                if _block["onset_ts"] is not None and _block["floor_ts"] is None:
                    _block["floor_ts"] = now
                    event = "floor"
                elif _block["onset_ts"] is None and _block["floor_ts"] is None and (prev is None or prev > thr):
                    _block["floor_ts"] = now
                    event = "floor_direct"
            if event:
                row = {"event": event, **_base(now, e, f, t, cycles), "prev_energy": prev}
                if event == "onset":
                    row["would_line"] = line
                    row["would_channel"] = "wandering.perceive (the to_bed line's channel)"
                _append_locked(row)
        if event == "onset":
            logger.info("[drowsy] onset (shadow, deliver=%s): energy %.3f <= %.2f", DELIVER, e, thr)
            if DELIVER:
                try:
                    from core import wandering as _w
                    _w.perceive(line)
                    with _LOCK:
                        _block["narrated"] = True
                except Exception:
                    pass
        return event
    except Exception:
        return None


def at_bed(reason: str | None = None, bed_line: str | None = None, now: float | None = None) -> dict | None:
    """Called in _enter_sleep right after night.to_bed(): one 'bed' row closing the wake block, then re-arm. Never
    raises. Returns the row."""
    try:
        now = float(now if now is not None else time.time())
        body = None
        try:
            from core import somatic as _som
            body = _som.current_body()
            cycles = _som.current_cycles()
        except Exception:
            cycles = None
        body = body or {}
        with _LOCK:
            onset = _block["onset_ts"]
            row = {"event": "bed", **_base(now, body.get("energy", -1.0), body.get("fatigue", -1.0),
                                           body.get("tension", -1.0), cycles),
                   "reason": reason, "zone_entered": onset is not None,
                   "onset_ts": onset, "onset_energy": _block["onset_energy"],
                   "onset_to_bed_min": round((now - onset) / 60.0, 1) if onset else None,
                   "floor_ts": _block["floor_ts"], "fatigue_marked": _block["fatigue_marked"],
                   "narrated": _block["narrated"], "bed_line": bed_line}
            _append_locked(row)
            _reset_locked()
        return row
    except Exception:
        return None


def _reset_locked() -> None:
    _block.update({"onset_ts": None, "onset_energy": None, "floor_ts": None, "fatigue_marked": False,
                   "last_energy": None, "narrated": False})


def reset() -> None:
    with _LOCK:
        _reset_locked()


def evaluate(path: Path | None = None) -> dict:
    """Read-only summary of the shadow log for the post-boot read."""
    p = Path(path) if path else DROWSY_SHADOW_LOG
    rows = []
    try:
        for ln in p.read_text(encoding="utf-8").splitlines():
            if ln.strip():
                try:
                    rows.append(json.loads(ln))
                except Exception:
                    pass
    except Exception:
        pass
    by = {}
    for r in rows:
        by[r.get("event")] = by.get(r.get("event"), 0) + 1
    beds = [r for r in rows if r.get("event") == "bed"]
    entered = [r for r in beds if r.get("zone_entered")]
    lead = sorted(r["onset_to_bed_min"] for r in entered if r.get("onset_to_bed_min") is not None)
    return {"rows": len(rows), "by_event": by, "beds": len(beds), "beds_zone_entered": len(entered),
            "onset_to_bed_min_median": (lead[len(lead) // 2] if lead else None),
            "beds_fatigue_marked_no_onset": sum(1 for r in beds if r.get("fatigue_marked") and not r.get("zone_entered"))}
