"""
Nascence — World Objects Engine (Phase 1 — Driftwood & Object History)
========================================================================
Authoritative persistence and causal provenance logging for physical objects
embedded in Du's world (data/world_objects.json).

Architectural Contract v1.4:
- Invariant 1: Explicit Causal Provenance
- Invariant 2: Conservation of History (Canonical content NEVER overrides state)
- Invariant 3: Tripartite State Independence (World State != Sensory State != Cognitive State)
"""
from __future__ import annotations
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

from core import profile

logger = logging.getLogger("nascence.world_objects")

_OBJECTS_F = Path(__file__).parent.parent / "data" / "world_objects.json"

_DEFAULT_OBJECTS = {
    "driftwood_17": {
        "object_id": "driftwood_17",
        "identity": "Bleached fir log with notched end",
        "location": "shore",
        "position": [5.0, 1.2, 0.0],  # x, y, z meters relative to shore origin
        "condition": "weathered_grey",
        "history": [
            {
                "ts": 1786286400.0,
                "cause": "initial_state",
                "event": "deposited_at_flat_bedrock",
                "from": None,
                "to": [5.0, 1.2, 0.0]
            }
        ]
    }
}

_objects_cache: Dict[str, Any] = {}
_last_load: float = 0.0


def _load_objects() -> Dict[str, Any]:
    global _objects_cache, _last_load
    if _objects_cache and (time.time() - _last_load < 5.0):
        return _objects_cache
    
    if _OBJECTS_F.exists():
        try:
            _objects_cache = json.loads(_OBJECTS_F.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.debug("[world-objects] objects load failed (non-fatal): %s", exc)
            _objects_cache = json.loads(json.dumps(_DEFAULT_OBJECTS))
    else:
        _objects_cache = json.loads(json.dumps(_DEFAULT_OBJECTS))
        _save_objects()
        
    _last_load = time.time()
    return _objects_cache


def _save_objects() -> None:
    global _objects_cache
    path = profile.guard_path(_OBJECTS_F)   # J-0610: real data/ only if this process is live
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(_objects_cache, indent=2), encoding="utf-8")
    tmp.replace(path)


def get_object(object_id: str) -> Optional[Dict[str, Any]]:
    objs = _load_objects()
    return objs.get(object_id)


def get_objects_at_location(location: str) -> List[Dict[str, Any]]:
    objs = _load_objects()
    return [obj for obj in objs.values() if obj.get("location") == location]


def mutate_object_position(
    object_id: str,
    new_position: List[float],
    cause: str,
    event_description: str,
    new_location: Optional[str] = None,
    ts: Optional[float] = None
) -> Optional[Dict[str, Any]]:
    """
    Mutates an object's physical coordinates and appends an invariant-compliant
    causal provenance record to its history log. `ts` (2026-08-18, keepsakes backfill):
    backdate this history entry instead of stamping it now — for retroactively-authored moves
    that genuinely happened in the past. Defaults to now for every other caller.

    NO-OP GUARD (2026-08-19): found live — a single real storm-scatter decision produced 177
    near-identical history entries on one object (shore_kelp_530eea) in under a second. Root
    cause: move_tick()'s RNG is seeded per (object, real-wall-clock-hour), so a restart/catch-up
    burst that replays many simulated weather transitions within one real hour makes the exact
    same movement decision — and the exact same target position — every time; this function
    logged each one unconditionally. If the position genuinely hasn't changed, there is no event
    to record — skip both the write and the history append. Every real caller (Du moving driftwood,
    keepsakes backfill, storm scatter) only means something when the position actually differs.
    """
    objs = _load_objects()
    obj = objs.get(object_id)
    if not obj:
        return None

    old_position = list(obj["position"])
    if list(new_position) == old_position and new_location in (None, obj.get("location")):
        return obj
    obj["position"] = list(new_position)
    if new_location:
        obj["location"] = new_location

    history_entry = {
        "ts": ts if ts is not None else time.time(),
        "cause": cause,
        "event": event_description,
        "from": old_position,
        "to": list(new_position)
    }
    obj.setdefault("history", []).append(history_entry)
    
    _save_objects()
    return obj


def process_storm_surge(weather: str, weather_dir: int = 270) -> List[str]:
    """
    Evaluates physical storm surge impact on shore objects.
    Returns a list of descriptions of physical state changes caused by the storm.
    """
    if weather not in ("wind and rain", "thunderstorm"):
        return []

    objs = _load_objects()
    mutated_events = []
    now = time.time()

    driftwood = objs.get("driftwood_17")
    if driftwood:
        pos = driftwood.get("position", [5.0, 1.2, 0.0])
        # If driftwood is down on the flat bedrock ([5.0, 1.2, 0.0]), storm surge pushes it up to high shingle ([12.4, 4.1, 0.2])
        if pos[1] < 3.0:
            new_pos = [12.4, 4.1, 0.2]
            import uuid
            cause_id = f"STORM_SURGE_{int(now)}_{uuid.uuid4().hex[:6]}"
            mutate_object_position(
                "driftwood_17",
                new_pos,
                cause=cause_id,
                event_description="shifted_by_storm_surge_to_high_shingle"
            )
            # PER-PROPERTY EARNING LAW (2026-08-17, founder): world-side prose must never pre-answer
            # a property question (species/origin/age are HIS to hypothesize) — "the heavy log", never
            # "the fir log" (which was also WRONG: hidden truth is silver beech — the leak that taught
            # the law).
            mutated_events.append("The storm surge washes high up the shore, lifting the heavy bleached log and wedging it high on the shingle strand.")

    return mutated_events


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# THE POSITION AUTHORITY FOR ALL OBJECTS (2026-08-17, founder: "all the objects need places, and
# they need to be able to move of course"). This module's written contract was always
# "authoritative persistence for physical objects" — world_substrate's docstring even says it
# extends this layer — but the extension never happened: only driftwood_17 ever got a record.
# These additive functions honor the contract: every substrate object gets a position record here
# (epistemic layers stay in world_substrate; POSITION and its causal history live here — one
# authority, joined by object_id, no duplication). Frames match data/world_geometry/<room>.json:
# origin SW corner, +x east, +y north, metres — the same compass in all four rooms, so the spatial
# renderer can consume these directly. Deterministic (seeded per object), zero LLM, fail-open.
# ═══════════════════════════════════════════════════════════════════════════════════════════════

import random as _random

# Placement bands per room, in the shared frame. Shore: +y is out to sea; the waterline swings
# y 8.5 (high) ↔ 14.5 (low) (shore.json tide_y), so wash-ups land in the tideline band and the
# dry scatter sits below it. Wood: the floor box. Others: a margin inside the room's size.
_PLACEMENT = {
    "shore": {"marine_band": (9.0, 14.0), "dry_band": (2.0, 8.0), "x": (2.0, 28.0)},
    "wood":  {"floor": ((2.0, 22.0), (2.0, 18.0))},
    "garden": {"floor": ((1.0, 9.5), (1.0, 11.5))},
    "study": {"floor": ((0.4, 3.8), (0.4, 4.8))},
}
_MARINE_CLASSES = {"stone", "shell", "bone", "egg_case", "sea_glass", "kelp", "feather", "driftwood"}


def _spawn_position(object_id: str, location: str, object_class: str) -> List[float]:
    """Deterministic class+room-aware placement in the shared frame. Same id → same spot."""
    rng = _random.Random(f"pos|{object_id}")
    p = _PLACEMENT.get(location) or _PLACEMENT["shore"]
    if location == "shore":
        band = p["marine_band"] if object_class in _MARINE_CLASSES else p["dry_band"]
        return [round(rng.uniform(*p["x"]), 2), round(rng.uniform(*band), 2), 0.0]
    box = p.get("floor") or ((1.0, 5.0), (1.0, 5.0))
    return [round(rng.uniform(*box[0]), 2), round(rng.uniform(*box[1]), 2), 0.0]


def ensure_record(object_id: str, location: str, object_class: str = "unknown",
                  name: str = "") -> Optional[Dict[str, Any]]:
    """Create the position record for an object if absent (idempotent). The birth of a place."""
    try:
        objs = _load_objects()
        if object_id in objs:
            return objs[object_id]
        pos = _spawn_position(object_id, location, object_class)
        objs[object_id] = {
            "object_id": object_id,
            "identity": name or object_id,
            "location": location,
            "object_class": object_class,
            "position": pos,
            "history": [{"ts": time.time(), "cause": "initial_placement",
                         "event": f"came_to_rest_at_{location}", "from": None, "to": list(pos)}],
        }
        _save_objects()
        return objs[object_id]
    except profile.NonLiveWriteError:
        # J-0726: ensure_record() is a shared position-registration helper called from _register_all()/
        # _register() across most of the other 10 modules (study_life, garden, provisions), plus
        # world_substrate.spawn_object() — let D-0179's hard-raise (guard_path(), F-1024) reach the
        # caller instead of being swallowed here.
        raise
    except Exception as exc:
        logger.debug("[world-objects] ensure_record failed (non-fatal): %s", exc)
        return None


def pos_of(object_id: str) -> Optional[List[float]]:
    """The one read API for an object's position. None if unplaced or gone."""
    obj = _load_objects().get(object_id)
    if not obj or obj.get("location") == "gone":
        return None
    return list(obj.get("position") or []) or None


def reclaim(object_id: str, cause: str = "reclaimed_by_sea") -> bool:
    """The sea (or the world) takes a thing back: location → 'gone', position history preserved.
    The glass-float lesson made mechanical: objects CAN leave, with a recorded cause — the record
    of the leaving is world-side truth; whether Du ever notices is his own epistemic problem."""
    try:
        objs = _load_objects()
        obj = objs.get(object_id)
        if not obj or obj.get("location") == "gone":
            return False
        obj.setdefault("history", []).append({
            "ts": time.time(), "cause": cause, "event": "taken_from_the_world",
            "from": list(obj.get("position") or []), "to": None})
        obj["location"] = "gone"
        _save_objects()
        # 2026-08-18: keepsakes.keep() already does this sync (world_substrate.update_location) —
        # reclaim() didn't, so 3 sea-taken objects were found live still reading "shore" in
        # world_substrate.json while world_objects.json correctly said "gone". Same fix, same reason:
        # without it the two registries disagree about whether a reclaimed object is still there.
        try:
            from core import world_substrate as _ws
            _ws.update_location(object_id, "gone")
        except Exception as exc:
            logger.debug("[world-objects] reclaim substrate sync failed (non-fatal): %s", exc)
        return True
    except Exception as exc:
        logger.debug("[world-objects] reclaim failed (non-fatal): %s", exc)
        return False


def _density_of(object_id: str) -> float:
    """Specific gravity from the substrate's Layer 2 (fail-open to 'sinks')."""
    try:
        from core import world_substrate as _ws
        d = (_ws.get_object(object_id) or None)
        if d is not None:
            return float(d.physical_state.get("density", 1.5))
    except Exception as exc:
        logger.debug("[world-objects] density lookup failed (non-fatal): %s", exc)
    return 1.5


# ── KING-TIDE GATE (J-3797, D-0694 ruled (c)) ───────────────────────────────────────────────────────────
# Flag default OFF: king_tide_now() is then exactly the old bare `level >= 0.92`, byte for byte.
# ON: level >= KING_TIDE_THRESHOLD AND the calendar day is one of ~KING_TIDE_DAYS_PER_YEAR drawn
# deterministically (random.Random(f"king|{date}")). Travis gave no number; 8/yr is the one-constant start.
KING_TIDE_GATE_ENABLED = False
KING_TIDE_THRESHOLD = 0.99
KING_TIDE_LEGACY_THRESHOLD = 0.92
KING_TIDE_DAYS_PER_YEAR = 8


def _king_day(t: float) -> bool:
    import datetime as _dt
    date = _dt.date.fromtimestamp(t)
    # Per-day probability chosen so ~DAYS_PER_YEAR days qualify; the draw is a pure function of the date.
    return _random.Random(f"king|{date.isoformat()}").random() < (KING_TIDE_DAYS_PER_YEAR / 365.0)


def king_tide_now(t: float | None, level: float | None) -> bool:
    """Is this a king tide? Flag off: the legacy bare threshold. Flag on: the ruled rare event."""
    if level is None:
        return False
    if not KING_TIDE_GATE_ENABLED:
        return level >= KING_TIDE_LEGACY_THRESHOLD
    if level < KING_TIDE_THRESHOLD:
        return False
    return _king_day(time.time() if t is None else t)


def move_tick(weather: str, tide_level: float | None = None) -> List[str]:
    """The generalized mover (called beside process_storm_surge at the weather-change site).
    Class- and density-aware, deterministic per (object, hour): storms scatter the light and can
    reclaim floaters; a king tide can carry a floater off the tideline band. driftwood_17 keeps
    its bespoke legacy handling above — skipped here. Returns event prose for the world's log."""
    events: List[str] = []
    try:
        stormy = weather in ("wind and rain", "thunderstorm")
        king = king_tide_now(None, tide_level)
        if not (stormy or king):
            return events
        objs = _load_objects()
        hour = int(time.time() // 3600)
        for oid, obj in list(objs.items()):
            if oid == "driftwood_17" or obj.get("location") != "shore":
                continue
            pos = obj.get("position")
            if not pos:
                continue
            rng = _random.Random(f"move|{oid}|{hour}")
            dens = _density_of(oid)
            floats = dens < 1.0
            in_tideline = pos[1] >= 8.5
            if stormy:
                if floats and rng.random() < 0.15:
                    if reclaim(oid, cause=f"storm_reclaim_{hour}"):
                        events.append(f"the storm sea has taken {obj.get('identity', oid)} back")
                    continue
                p_move = 0.6 if floats else (0.25 if dens < 2.0 else 0.10)
                if rng.random() < p_move:
                    new_pos = _spawn_position(f"{oid}|{hour}", "shore", obj.get("object_class", "unknown"))
                    mutate_object_position(oid, new_pos, cause=f"storm_scatter_{hour}",
                                           event_description="thrown_along_the_shore_by_the_storm")
                    events.append(f"the storm has shifted {obj.get('identity', oid)} along the shore")
            elif king and floats and in_tideline and rng.random() < 0.08:
                if reclaim(oid, cause=f"king_tide_reclaim_{hour}"):
                    events.append(f"the high tide has floated {obj.get('identity', oid)} away")
    except Exception as exc:
        logger.debug("[world-objects] move_tick failed (non-fatal): %s", exc)
    return events


def backfill_positions() -> int:
    """One-time (idempotent) pass: every substrate object without a position record gets one."""
    n = 0
    try:
        from core import world_substrate as _ws
        for oid, obj in _ws._load().items():
            if oid not in _load_objects():
                if ensure_record(oid, obj.location, obj.object_class, obj.name):
                    n += 1
    except Exception as exc:
        logger.debug("[world-objects] backfill_positions failed (non-fatal): %s", exc)
    return n

