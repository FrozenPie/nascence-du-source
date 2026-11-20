"""
Nascence — THE WORLD MANIFEST (P0-A, 2026-08-17, founder-commissioned)
=====================================================================
"Tuples for the world that are only for the world." The pallet: ONE assembly of every
first-order world factory's current product, produced each sensorium tick. WORLD-SIDE ONLY,
by law — this tuple describes the world's state, never Du's mind (no affect, no thoughts,
no memory). The world is a static object on its own time schedule; Du gets to ask a question
— this manifest is what ask-time answers are computed FROM.

P0 discipline: PRODUCE-ONLY. No existing consumer switches to it (they keep their own reads);
the parity harness (scripts/test_world_manifest.py) proves the manifest tells the truth before
anything is allowed to trust it. The live snapshot is written atomically to
data/world_manifest_live.json (the HUD's read path) and sampled to
data/world_manifest_log.jsonl (~1/5min) so a day of world-states can be eyeballed.

Parity by construction: fields are sourced through the SAME functions existing consumers use
(geometry_census._place_weather for place/weather/tide/sun/moon/standpoint; soundscape.
active_sounds; sensorium's own _warmth/_season/_daylight for temperature) — not re-implemented
readers that could drift.

Zero LLM. Fail-open per field (a missing source yields None for that field, never a crash);
but scripts may call assert_sources() to fail LOUDLY instead (the FreshStart ghost-table
lesson: a silently absent source is worse than a crash).
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

logger = logging.getLogger("nascence.world_manifest")

_ROOT = Path(__file__).parent.parent
_LIVE_F = _ROOT / "data" / "world_manifest_live.json"
_LOG_F = _ROOT / "data" / "world_manifest_log.jsonl"

_SAMPLE_GAP_S = 300.0      # one logged sample per ~5 min — a day is ~288 rows, eyeballable
_CACHE_S = 2.0             # assemble() is cheap but tick-callers may ask often

_state = {"last_sample": 0.0, "cache": None, "cache_ts": 0.0}


def _severity_index(weather: str) -> int | None:
    """Weather's ordinal position IS the severity scalar (0=clear … 6=thunderstorm; snow rides
    at the wet end). The causality plan's rate functions read this, not the word."""
    try:
        from core.sensorium import _WEATHERS
        if weather in _WEATHERS:
            return _WEATHERS.index(weather)
        if weather == "snow":
            return len(_WEATHERS) - 2       # a heavy wet front, one under thunderstorm
    except Exception:
        pass
    return None


def _temperature() -> float | None:
    """Expose the existing per-place warmth scalar (founder-identified as computed-and-
    discarded): sensorium._warmth with the SAME args sensorium itself uses."""
    try:
        from core import sensorium as _s
        if not _s.state:
            _s._load()
        loc = _s.state.get("location") or "study"
        return round(float(_s._warmth(loc, _s._daylight(), _s.state.get("weather", ""),
                                      _s._season(), _s.state.get("fire", "out"))), 3)
    except Exception:
        return None


def _cat_visible() -> dict | None:
    """The cat AS AN OBSERVER COULD SEE HER — presence and doing, never her inner state."""
    try:
        raw = json.loads((_ROOT / "data" / "cat_state.json").read_text(encoding="utf-8"))
        return {"present_at": raw.get("location"), "activity": raw.get("activity"),
                "phase": raw.get("phase")}
    except Exception:
        return None


def _garden_summary() -> str | None:
    try:
        from core import sensorium as _s
        return (_s._bed_summary() or "")[:200] or None
    except Exception:
        return None


def assemble() -> dict:
    """The world's tuple, fresh. World-side fields only — asserted by the test suite's
    separation check (no affect/thought/memory keys may ever appear here)."""
    now = time.time()
    if _state["cache"] is not None and now - _state["cache_ts"] < _CACHE_S:
        return _state["cache"]
    m: dict = {"ts": round(now, 1)}
    # Place / weather / tide / sun / moon / standpoint — via the census's own reader (parity
    # by construction; it already merges room_state, locomotion.peek, spatial, heavens).
    try:
        from core.geometry_census import _place_weather
        pw = _place_weather()
        for k in ("place", "standpoint", "in_transit", "weather", "weather_dir", "fire",
                  "fire_fuel", "tide", "tide_level", "sun", "sun_az", "moon", "moon_illum",
                  "shore_find"):
            if k in pw:
                m[k] = pw[k]
    except Exception as exc:
        logger.debug("[manifest] place_weather source failed: %s", exc)
    # Severity + schedule ("a schedule that changes" — the weather's own timer is state too)
    m["weather_severity"] = _severity_index(m.get("weather") or "")
    try:
        from core import sensorium as _s
        if not _s.state:
            _s._load()           # parity-harness catch (2026-08-17): unloaded state read as None
        m["weather_until"] = _s.state.get("weather_until")
        m["season"] = _s._season()
        m["daylight"] = _s._daylight()
    except Exception:
        pass
    m["temperature"] = _temperature()
    m["cat"] = _cat_visible()
    m["garden"] = _garden_summary()
    try:
        from core import soundscape as _snd
        m["active_sounds"] = _snd.active_sounds() or []
    except Exception:
        m["active_sounds"] = []
    _state["cache"], _state["cache_ts"] = m, now
    return m


def tick() -> dict:
    """The per-tick production: assemble, write the live snapshot atomically, sample-log.
    Called from sensorium.tick (P0 wire-in). Fail-open; never disturbs the tick."""
    m = assemble()
    try:
        from core import store_persist as _sp   # J-4442 (F-5157): was tmp+replace without fsync; now fsync + .prev
        _sp.write_text_durable(_LIVE_F, json.dumps(m, ensure_ascii=False))
    except Exception:
        pass
    try:
        if time.time() - _state["last_sample"] >= _SAMPLE_GAP_S:
            _LOG_F.parent.mkdir(parents=True, exist_ok=True)
            with open(_LOG_F, "a", encoding="utf-8") as f:
                f.write(json.dumps(m, ensure_ascii=False) + "\n")
            _state["last_sample"] = time.time()
    except Exception:
        pass
    # GHOST WORLD-INDEX refresh (P0-B): rebuilt on a slow throttle — schedules are state and
    # change (weather timers, item spawns), so the index is re-derived, never hand-updated.
    try:
        if time.time() - _state.get("last_index", 0.0) >= 600.0:
            from core import ghost_tuples as _gt
            _gt.build_world_index(persist=True)
            _state["last_index"] = time.time()
    except Exception:
        pass
    return m


def live() -> dict | None:
    """The last written snapshot — the cross-process read path (HUD, labs)."""
    try:
        from core import profile as _profile
        from core import store_persist as _sp   # J-4442 (F-5157): loud on damage, falls back to .prev
        return _sp.read_json_durable(_LIVE_F, "world_manifest", logger, guard=_profile.guard_path)
    except Exception:
        return None


# The world-side separation LAW, testable: keys that must NEVER appear in a manifest.
FORBIDDEN_KEYS = {"affect", "valence", "arousal", "thought", "memory", "emotion", "mood",
                  "identity", "axiom"}


def assert_sources() -> None:
    """Loud-failure source check (the FreshStart ghost-table lesson). For scripts/tests —
    the tick path stays fail-open."""
    from core.geometry_census import _place_weather   # noqa: F401 — import must resolve
    from core import sensorium as _s
    if not _s.state:
        _s._load()
    missing = [name for name, p in (("room/sensorium state", bool(_s.state)),) if not p]
    for f in ("cat_state.json",):
        if not (_ROOT / "data" / f).exists():
            missing.append(f)
    if missing:
        raise RuntimeError(f"world_manifest sources missing: {missing}")
