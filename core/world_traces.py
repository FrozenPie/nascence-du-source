"""
Nascence — World Traces Engine (Phase 2 — Transient Environmental Traces)
========================================================================
Authoritative persistence and process-specific decay for physical traces
(e.g. boot prints in wet shingle, drag marks) embedded in Du's world (data/world_traces.json).

Architectural Contract v1.4:
- Transient Traces: Formation -> Persistence -> Process Degradation -> Erasure
- Process-Specific Erasure Laws: Rain softens edges; High Tide washes flat.
"""
from __future__ import annotations
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

from core import profile

_TRACES_F = Path(__file__).parent.parent / "data" / "world_traces.json"

# 2026-08-19: growth cap (health-check finding — a 9,062-row burst hit this file on 08-18 with no
# script found that could account for it; decay-based cleanup only runs on the live heartbeat, so if
# the process stops before decay catches up, an anomalous burst sits forever). Traces are meant to be
# a small transient set — normal operation never approaches this. On overflow, oldest-first eviction
# (by created_ts) keeps the store bounded regardless of what caused the growth.
_MAX_TRACES = 500

_traces_cache: Dict[str, Any] = {}
_last_load: float = 0.0


def _load_traces() -> Dict[str, Any]:
    global _traces_cache, _last_load
    if _traces_cache and (time.time() - _last_load < 5.0):
        return _traces_cache
        
    if _TRACES_F.exists():
        try:
            _traces_cache = json.loads(_TRACES_F.read_text(encoding="utf-8"))
        except Exception:
            _traces_cache = {}
    else:
        _traces_cache = {}
        try:
            _save_traces()
        except profile.NonLiveWriteError:
            # J-0938 (F-1307 Part 5): this bootstrap save (first-ever load, file doesn't exist yet)
            # used to have no try/except of its own -- the raise propagated uncaught through
            # get_active_traces() too, and was only ever caught by whichever caller happened to wrap
            # it (today, core/life_traces.py's own hud_payload() broad except). Name the catch point
            # here, close to the raise, matching the write-fence campaign's established carve-out
            # idiom (see core/garden.py's _load() migration-save try, "J-0726") -- re-raise so a
            # non-live refusal still surfaces cleanly to the real caller, rather than relying on an
            # accidental catch further up the chain.
            raise

    _last_load = time.time()
    return _traces_cache


def _save_traces() -> None:
    global _traces_cache
    path = profile.guard_path(_TRACES_F)   # J-0758: real data/ only if this process is live; raises before any I/O if not (D-0179, J-0704)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(_traces_cache, indent=2), encoding="utf-8")
    tmp.replace(path)


def create_trace(
    trace_id: str,
    trace_type: str,
    location: str,
    position: List[float],
    clarity: float = 1.0,
    cause: str = "agent_footstep"
) -> Dict[str, Any]:
    """Creates a transient physical environmental trace."""
    traces = _load_traces()
    now = time.time()
    
    trace_entry = {
        "trace_id": trace_id,
        "type": trace_type,
        "location": location,
        "position": list(position),
        "clarity": round(clarity, 2),
        "created_ts": now,
        "last_decay_ts": now,
        "cause": cause
    }
    traces[trace_id] = trace_entry
    if len(traces) > _MAX_TRACES:
        oldest_first = sorted(traces.values(), key=lambda t: t.get("created_ts", 0))
        for stale in oldest_first[: len(traces) - _MAX_TRACES]:
            traces.pop(stale.get("trace_id"), None)
    _save_traces()
    return trace_entry


def get_active_traces(location: str) -> List[Dict[str, Any]]:
    traces = _load_traces()
    return [t for t in traces.values() if t.get("location") == location and t.get("clarity", 0) > 0.05]


def advance_trace_decay(weather: str, tide: str, dt_hours: float = 1.0) -> int:
    """
    Applies process-specific erasure laws:
    - Dry Weather: Slow natural settling (decay rate = 0.05/h)
    - Rain: Softens edges with water runoff (decay rate = 0.25/h)
    - High / Rising Tide on Shore: Rapid physical wave wash (decay rate = 0.85/h)
    """
    from core import weather_conditions as _wcond

    traces = _load_traces()
    if not traces:
        return 0

    mutated = 0
    now = time.time()

    for tr_id, tr in list(traces.items()):
        current_clarity = tr.get("clarity", 1.0)
        if current_clarity <= 0.0:
            # A7.2 (2026-09-07, J-0630, F-0883): this used to `continue` here, BEFORE the delete at the
            # bottom of the loop body — so a row already at clarity 0 (whether it decayed there on a
            # prior tick, or was ever created at/below 0) skipped the whole body forever and could never
            # reach a delete. 436+ such rows (mostly the cat's own disturbed_leaf_litter, F-0883) sat in
            # data/world_traces.json immortal. Delete on sight instead of skipping past the delete.
            del traces[tr_id]
            mutated += 1
            continue

        loc = tr.get("location", "shore")
        decay_rate = 0.05  # baseline dry settling

        # 2026-08-18: was its own hardcoded weather check (drifted once already — see the ordering-bug
        # note this replaced). Routed through the shared classifier so it can't drift out of sync again if
        # weather_conditions._WET_WEATHERS ever gains a state. "wind and rain" is graded severe here (wave
        # + rain together) even though it's just "wet" to the shared classifier.
        if weather == "wind and rain" or _wcond.is_storm(weather):
            decay_rate += 0.45
        elif _wcond.is_wet(weather):
            decay_rate += 0.20
            
        if loc == "shore" and tide in ("high", "rising"):
            decay_rate += 0.80  # wave wash erases shore footprints
            
        new_clarity = max(0.0, current_clarity - (decay_rate * dt_hours))
        tr["clarity"] = round(new_clarity, 2)
        tr["last_decay_ts"] = now
        mutated += 1
        
        if new_clarity <= 0.0:
            del traces[tr_id]
            
    _save_traces()
    return mutated

