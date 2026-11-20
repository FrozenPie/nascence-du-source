"""
Nascence — Weather/Wind/Tide conditions (2026-08-18): the ONE shared classifier every consumer imports.

Tonight's variety+grounding audit (docs/UNFINISHED_PLANS_SURVEY_2026-08-18.md's follow-on) found FIVE
independent files had each rolled their own "is it wet" / "is it windy" substring check, and they'd
drifted: sensorium.py's moisture check and soundscape.py's ambience were fixed correctly on 2026-08-18,
but soundscape.py's bird-gating, world_detail.py's shared _conds() (serving study/garden/shore/wood),
cat.py's own _conds(), and world_traces.py's decay rate all still used incomplete or ordering-broken
checks. Root cause: no single source of truth, so each new file re-derives "wet"/"windy" from the raw
weather string and gets it slightly wrong. This module is that source of truth — everyone imports it.
"""
from __future__ import annotations

# Mirrors core/sensorium.py's _WEATHERS ladder exactly — any state with real precipitation, INCLUDING
# thunderstorm (the substring-miss bug: `"rain" in weather` silently drops "thunderstorm", which contains
# no "rain" substring at all).
_WET_WEATHERS = frozenset({"drizzle", "steady rain", "wind and rain", "thunderstorm"})

# Mirrors core/sensorium.py's _WIND_STATES ladder. Read from the REAL independent wind axis
# (state["wind"]), never inferred from the weather string — a dry gale and a windless thunderstorm are
# both real, distinct states since 2026-08-18's wind-axis rework.
_WINDY_STATES = frozenset({"fresh wind", "strong wind", "gale"})
_HARD_WIND_STATES = frozenset({"strong wind", "gale"})

_TIDE_STATES = ("high", "low", "rising", "falling")


def is_wet(weather: str) -> bool:
    """Any precipitation state, including thunderstorm."""
    return (weather or "") in _WET_WEATHERS


def is_windy(wind: str) -> bool:
    """Enough air to work the trees/house: 'fresh wind' and up, from the real wind axis."""
    return (wind or "") in _WINDY_STATES


def is_hard_wind(wind: str) -> bool:
    """Severe wind only: 'strong wind'/'gale' — what rattles a loose window and stands the sea up."""
    return (wind or "") in _HARD_WIND_STATES


def is_storm(weather: str) -> bool:
    """Weather-string storm signal (thunder/lightning) — independent of the wind axis."""
    return weather == "thunderstorm"


def tide_leaning(tide_state: str) -> str:
    """Which of the two tide-extreme pools (low_tide / high_tide) a moment leans toward, covering ALL
    four of tide_state()'s real values (high/low/rising/falling) — not just the two extremes. 'rising'
    is still closer to 'low' (it started there and is heading up, most content at this end reads as
    approach-to-full); 'falling' closer to 'high' by the same logic. Falls back to '' for anything else
    (e.g. tide not supplied)."""
    t = (tide_state or "").lower()
    if t in ("low", "rising"):
        return "low_tide"
    if t in ("high", "falling"):
        return "high_tide"
    return ""
