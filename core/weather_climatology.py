"""W1 month-weighted climatology for the SIMULATED weather (J-3839, D-0668; design: docs/reviews/
sumner_sky_tide_weather_design_J-3264.md section 4).

Pure, local, no network, no file reads, no state. It only answers "given the month, what are the transition
weights / front-direction mix / mean temperature": sensorium._advance_weather and _advance_wind consult it when
WEATHER_CLIMATOLOGY_ENABLED is true. Flag ships OFF (restart-gated founder flip), so importing this changes nothing.

SHAPE, NOT LEVEL. The 08-18 rebalance ("storms rarely happen") fixed the ANNUAL level of every state. W1 must not
move that level, so each month's table is a RATIO to the annual mean (mean ratio = 1.0 by construction), applied as
a tilt on the existing step weights. Annual storm share therefore stays at the 08-18 level (checked by
simulate_year / the test script); only its month-to-month shape changes.

SOURCE / CONFIDENCE. The monthly figures below are typed from recollection of the NIWA 1991-2020 climate normals for
Christchurch (Gardens / Airport, wet days >= 1 mm, mean temperature, windiest-month ordering). They are
APPROXIMATE and UNVERIFIED against the published tables: the founder (or a session with the NIWA table open) must
re-type them from the source before the flag is flipped. The tilt only uses their RATIOS, so a few percent of error
changes the shape by a few percent, not the level.
"""
from __future__ import annotations

WEATHER_CLIMATOLOGY_ENABLED = False   # flip only with founder go-ahead; see module docstring

# month 1..12. wet days (>= 1 mm) per month, approximate Christchurch normals.
_WET_DAYS = (6.5, 5.5, 6.5, 7.0, 8.0, 8.0, 8.5, 7.5, 6.5, 7.5, 7.0, 7.5)
# mean daily temperature, deg C, approximate normals.
# VERIFIED 2026-11-18 (J-4378): NIWA 1991-2020 mean monthly air temperature, Christchurch, as republished by Figure.NZ
# table "Weather and climate - Mean monthly values by station 1991-2020" (figure.nz/table/lzIenwXd73K2Ikh2).
# _WET_DAYS and _WIND_RATIO_RAW remain UNVERIFIED recollection (no trustworthy published monthly table found).
_MEAN_TEMP_C = (17.1, 16.9, 14.9, 11.9, 9.3, 6.4, 6.0, 7.3, 9.3, 11.3, 13.2, 15.7)
# relative windiness (mean 1.0): spring nor'westers and summer sea-breeze afternoons high, deep winter lower.
_WIND_RATIO_RAW = (1.05, 0.95, 0.90, 0.85, 0.80, 0.80, 0.90, 1.00, 1.15, 1.25, 1.20, 1.15)
# front direction mix per season, same order as _DIRS (W, NW, SW, S, N, NE, E); the existing flat mix is the annual
# average. Summer: NE sea breeze and N more common; winter: SW/S cold fronts and W.
_DIRS = (270, 315, 225, 180, 0, 45, 90)
_DIR_BASE = (30, 22, 18, 12, 8, 5, 5)
_DIR_BY_SEASON = {
    "summer": (24, 20, 14, 10, 10, 14, 8),
    "autumn": (30, 20, 18, 12, 8, 7, 5),
    "winter": (32, 20, 22, 16, 5, 2, 3),
    "spring": (30, 26, 16, 10, 8, 5, 5),
}
_STEPS_UP = (1, 2)

_TILT_EXP = 0.25  # fit by exact stationary distribution (scripts/_test_weather_climatology_J-3839.py): k = ratio**0.25 reproduces the monthly wet-share ratios and holds annual storm share


def _mean(xs):
    return sum(xs) / len(xs)


_WET_RATIO = tuple(x / _mean(_WET_DAYS) for x in _WET_DAYS)
_WIND_RATIO = tuple(x / _mean(_WIND_RATIO_RAW) for x in _WIND_RATIO_RAW)


def _season_of(month: int) -> str:
    return ("winter" if month in (6, 7, 8) else "summer" if month in (12, 1, 2)
            else "autumn" if month in (3, 4, 5) else "spring")


def _tilt(steps, weights, ratio: float, exp: float):
    """Scale the weights of upward steps by ratio**exp and downward steps by ratio**-exp; zero steps unchanged."""
    k = ratio ** exp
    return tuple(w * k if s > 0 else w / k if s < 0 else w for s, w in zip(steps, weights))


def weather_weights(month: int, steps, weights):
    """Month-tilted weights for the precipitation ladder walk (same steps)."""
    return _tilt(steps, weights, _WET_RATIO[(month - 1) % 12], _TILT_EXP)


def wind_weights(month: int, steps, weights):
    """Month-tilted weights for the wind walk."""
    return _tilt(steps, weights, _WIND_RATIO[(month - 1) % 12], _TILT_EXP)


def direction_weights(month: int):
    """(dirs, weights) for the front's arrival bearing in this month."""
    return _DIRS, _DIR_BY_SEASON[_season_of((month - 1) % 12 + 1)]


def mean_temperature_c(month: int, hour: float = 12.0) -> float:
    """Monthly mean temperature plus a diurnal swing (peak ~15:00, amplitude 3.5 C, half in deep winter nights)."""
    import math
    m = (month - 1) % 12
    # smooth between month midpoints to avoid a step on the 1st
    return _MEAN_TEMP_C[m] + 3.5 * math.cos(2 * math.pi * ((hour - 15.0) / 24.0))
