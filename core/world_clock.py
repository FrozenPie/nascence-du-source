"""
Nascence — World Clock: the ONE authority for the world's deterministic physics (2026-07-06).

Every clock that is a pure function of time — the tide, the sun's position, the daylight phase — lives HERE,
computed once, so the sensorium (which presents it as lived prose), spatial (which presents it as geometry),
and the census (which records it) all read the SAME rhythm and can never drift apart.

This module exists because they DID drift: the tide was computed in BOTH spatial and the sensorium, a
quarter-cycle out of phase (sin vs -cos) AND a period mismatch (12.4206 vs 12.42) — so the rendered
waterline contradicted the lived scene ~half the shore renders. Two copies of one physics always eventually
diverge; one copy cannot.

Pure, deterministic, stateless. Imports NOTHING from the higher layers (so nothing here can create a cycle);
the presenters (sensorium/spatial) and recorders (census/keepsakes/world_model) import THIS.

NOT here: WEATHER — it is stochastic/stateful (a Markov front), not a function of time, so it stays in the
sensorium. MOON/STARS remain in heavens.py for now (already single-source); they may migrate here later for
one complete authority.
"""
from __future__ import annotations

import math
import time

# ── THE TIDE — M2 lunar semi-diurnal clock ────────────────────────────────────────────────────────────
_TIDE_PERIOD_S = 12.42 * 3600.0       # M2 semi-diurnal period (hours → seconds). ONE value, forever.


# SPRING/NEAP AMPLITUDE (2026-08-18, founder: "king tides need to be there also — potentially
# linked to our moon... physics?"). Real spring tides happen at syzygy — new OR full moon, when
# sun+moon align — and neaps at the quarter moons in between. heavens.moon()'s `illum` already runs
# 0 (new) -> 1 (full) -> 0 (new) as a clean sinusoid, so it's ALREADY the syzygy signal: no separate
# solar term needed, alignment is exactly what makes illum hit its extremes. spring_factor =
# |2*illum-1| is 1.0 at illum=0 or 1 (new/full — spring) and 0.0 at illum=0.5 (quarter — neap).
# Amplitude interpolates NEAP..SPRING on that factor. Before this, amplitude was a fixed 0.5 — every
# high tide reached exactly level=1.0, so world_objects.py's "king tide" reclaim (tide_level>=0.92)
# fired on ~19% of ALL timestamps (every ordinary high tide), not a rare event. Now: neap tides peak
# at 0.90 (never crosses 0.92 — no reclaim); only a high tide near syzygy can reach 1.0. A future
# refinement (not built): perigee/equinox proximity nudges real king tides higher still — noted, not
# needed for the core fix.
_NEAP_AMP, _SPRING_AMP = 0.40, 0.50


def _spring_factor(t: float) -> float:
    """0.0 at neap (quarter moon) .. 1.0 at spring (new/full moon). Reads heavens.moon() — a light,
    one-way dependency (heavens has no tide dependency, so this cannot cycle)."""
    try:
        from core import heavens as _hv
        illum = _hv.moon(t)["illum"]
        return abs(2.0 * illum - 1.0)
    except Exception:
        return 1.0   # fail-open to the old fixed-spring amplitude, never a crash


def tide(t: float | None = None) -> dict:
    """The tide as a pure function of time: level ∈ [0,1] (0=low, 1=high), rising/falling, phase word.
    +sin phase → high at phase 0.25 (matches the lived scene). CONSISTENCY is the whole point.
    Amplitude now varies with lunar phase (spring/neap) — see _spring_factor above."""
    t = time.time() if t is None else t
    ang = 2 * math.pi * (t % _TIDE_PERIOD_S) / _TIDE_PERIOD_S
    amp = _NEAP_AMP + (_SPRING_AMP - _NEAP_AMP) * _spring_factor(t)
    level = 0.5 + amp * math.sin(ang)
    rising = math.cos(ang) > 0                            # d(sin)/dt = cos → rising while cos>0
    if level < 0.25:
        word = "out"
    elif level > 0.75:
        word = "full"
    else:
        word = "coming in" if rising else "going out"
    return {"level": round(level, 3), "rising": rising, "word": word,
            "spring_factor": round(_spring_factor(t), 3)}


def tide_state(t: float | None = None) -> str:
    """The sensorium's coarse tide enum, from the ONE tide clock: high / low / rising / falling."""
    d = tide(t)
    if d["word"] == "full":
        return "high"
    if d["word"] == "out":
        return "low"
    return "rising" if d["rising"] else "falling"


# ── TIMEZONE CHECK (J-3291, D-0655, design review J-3264 section 2) ──────────────────────────────────────
def _nz_offset_hours(t: float) -> int:
    """New Zealand civil offset from UTC by the hand rule (+13 NZDT / +12 NZST). The rule itself now lives in
    core/world_place.py (J-3292) so the sky and this check share ONE copy; this name stays for J-3291's callers."""
    from core import world_place as _wp
    return _wp.nz_offset_hours(t)


def tz_check(t: float | None = None) -> dict:
    """Does the machine's OS timezone agree with the New Zealand hand rule right now? REPORT ONLY: nothing
    here acts or changes a clock. sun()/daylight() read time.localtime (the OS zone) while the circadian and
    study clocks read the OS clock too, so on a machine NOT in NZ the sky and Du's circadian clock would both
    be shifted together -- but away from the real Sumner. Returns {agree, os_hours, nz_hours}."""
    t = time.time() if t is None else t
    off = time.localtime(t).tm_gmtoff
    os_h = None if off is None else off / 3600.0
    nz_h = _nz_offset_hours(t)
    return {"agree": os_h == float(nz_h), "os_hours": os_h, "nz_hours": nz_h}


# ── THE SUN — position + daylight phase, from the NZ seasonal table ───────────────────────────────────
# NZ seasonal daylight (month -> sunrise_h, sunset_h). Winter-centred; close enough for a window.
_SUN = {1: (6.1, 20.6), 2: (6.7, 20.2), 3: (7.2, 19.4), 4: (7.7, 18.4), 5: (7.3, 17.3),
        6: (7.6, 17.0), 7: (7.6, 17.2), 8: (7.1, 17.8), 9: (6.3, 18.3), 10: (5.6, 18.9),
        11: (5.1, 19.6), 12: (5.9, 20.4)}


def _sun_phase(f: float) -> str:
    return ("first light" if f < 0.12 else "morning" if f < 0.4 else "high" if f < 0.6
            else "afternoon" if f < 0.82 else "evening")


def sun_legacy(t: float | None = None) -> dict:
    """The ORIGINAL sun (the month table walked in machine-local time, a straight-line azimuth): kept verbatim so
    that every moment before SKY_CUTOVER_TS, and every shadow-mode call, answers exactly as it always did."""
    lt = time.localtime(time.time() if t is None else t)
    rise, sett = _SUN.get(lt.tm_mon, (7.0, 18.0))
    h = lt.tm_hour + lt.tm_min / 60.0
    if h < rise or h > sett:
        return {"up": False, "phase": "night", "az": None, "f": None}
    f = (h - rise) / max(0.1, sett - rise)               # 0 at rise → 1 at set
    az = (90.0 - 180.0 * f) % 360.0                       # E 90 → N 0 → W 270
    return {"up": True, "phase": _sun_phase(f), "az": round(az, 1), "f": round(f, 3)}


def _daylight_word(h: float, rise: float, set_: float) -> str:
    if h < rise - 0.7 or h > set_ + 0.7:
        return "night"
    if h < rise + 0.8:
        return "dawn"
    if h > set_ - 0.8:
        return "dusk"
    return "day"


def daylight_legacy(t: float | None = None) -> str:
    """The ORIGINAL coarse day-phase (same month table as sun_legacy). See sun_legacy."""
    lt = time.localtime(time.time() if t is None else t)
    rise, set_ = _SUN.get(lt.tm_mon, (7.0, 18.0))
    h = lt.tm_hour + lt.tm_min / 60.0
    return _daylight_word(h, rise, set_)


# ── THE SUN AT THE REAL SITE (J-3292, D-0655, design review J-3264 section 2) ─────────────────────────────
# NOAA / Meeus solar position (the NOAA general solar position calculations): declination and equation of time
# from the Julian century, hour angle from the site's longitude, altitude/azimuth from the site's latitude.
# ~1 minute on rise/set, no dependency, no table, no OS timezone. Civil time is the NZ hand rule in
# core/world_place.py. Rise/set is the official one: the Sun's centre at -0.833 degrees (refraction + disc).
_RISE_ALT = -0.833


def _solar_decl_eqt(t: float) -> tuple[float, float]:
    """(declination in radians, equation of time in minutes) at unix time t."""
    jd = t / 86400.0 + 2440587.5
    T = (jd - 2451545.0) / 36525.0
    L0 = (280.46646 + T * (36000.76983 + T * 0.0003032)) % 360.0
    M = 357.52911 + T * (35999.05029 - 0.0001537 * T)
    e = 0.016708634 - T * (0.000042037 + 0.0000001267 * T)
    Mr = math.radians(M)
    C = (math.sin(Mr) * (1.914602 - T * (0.004817 + 0.000014 * T))
         + math.sin(2 * Mr) * (0.019993 - 0.000101 * T) + math.sin(3 * Mr) * 0.000289)
    true_long = L0 + C
    omega = 125.04 - 1934.136 * T
    lam = true_long - 0.00569 - 0.00478 * math.sin(math.radians(omega))
    eps0 = 23.0 + (26.0 + (21.448 - T * (46.815 + T * (0.00059 - T * 0.001813))) / 60.0) / 60.0
    eps = math.radians(eps0 + 0.00256 * math.cos(math.radians(omega)))
    decl = math.asin(math.sin(eps) * math.sin(math.radians(lam)))
    y = math.tan(eps / 2.0) ** 2
    L0r = math.radians(L0)
    eqt = 4.0 * math.degrees(y * math.sin(2 * L0r) - 2 * e * math.sin(Mr)
                             + 4 * e * y * math.sin(Mr) * math.cos(2 * L0r)
                             - 0.5 * y * y * math.sin(4 * L0r) - 1.25 * e * e * math.sin(2 * Mr))
    return decl, eqt


def _alt_az(t: float) -> tuple[float, float]:
    """(altitude in degrees above the flat horizon, azimuth in degrees 0=N 90=E clockwise) of the Sun's centre."""
    from core import world_place as _wp
    decl, eqt = _solar_decl_eqt(t)
    lat = math.radians(_wp.SITE_LAT)
    tst = (t % 86400.0) / 60.0 + eqt + 4.0 * _wp.SITE_LON          # true solar time, minutes
    ha = math.radians(tst / 4.0 - 180.0)
    sin_alt = math.sin(lat) * math.sin(decl) + math.cos(lat) * math.cos(decl) * math.cos(ha)
    alt = math.degrees(math.asin(max(-1.0, min(1.0, sin_alt))))
    az = math.degrees(math.atan2(math.sin(ha), math.cos(ha) * math.sin(lat) - math.tan(decl) * math.cos(lat))) + 180.0
    return alt, az % 360.0


_RS_CACHE: dict = {}


def _rise_set_ts(t: float) -> tuple[float, float]:
    """(sunrise, sunset) unix times for the NZ civil DATE that contains `t`. Closed form first, then a few
    Newton steps on the true altitude; cached per date. The site is mid-southern latitude, so rise and set
    always fall inside the same civil date."""
    import calendar
    from core import world_place as _wp
    ymd = _wp.civil_date(t)
    hit = _RS_CACHE.get(ymd)
    if hit is not None:
        return hit
    y, m, d = ymd
    noon_utc = calendar.timegm((y, m, d, 12, 0, 0))
    off = _wp.nz_offset_hours(noon_utc - 12 * 3600)
    noon_local = noon_utc - off * 3600.0
    decl, eqt = _solar_decl_eqt(noon_local)
    lat = math.radians(_wp.SITE_LAT)
    cos_h0 = ((math.sin(math.radians(_RISE_ALT)) - math.sin(lat) * math.sin(decl))
              / (math.cos(lat) * math.cos(decl)))
    h0 = math.degrees(math.acos(max(-1.0, min(1.0, cos_h0))))
    sn = calendar.timegm((y, m, d, 0, 0, 0)) + (720.0 - 4.0 * _wp.SITE_LON - eqt) * 60.0   # solar noon, UTC
    sn += 86400.0 * round((noon_local - sn) / 86400.0)             # the solar noon nearest this civil date's noon
    out = []
    for guess in (sn - h0 * 240.0, sn + h0 * 240.0):
        x = guess
        for _ in range(4):
            a0 = _alt_az(x)[0] - _RISE_ALT
            a1 = _alt_az(x + 60.0)[0] - _RISE_ALT
            slope = (a1 - a0) / 60.0
            if abs(slope) < 1e-9:
                break
            x -= a0 / slope
        out.append(x)
    res = (out[0], out[1])
    if len(_RS_CACHE) > 800:
        _RS_CACHE.clear()
    _RS_CACHE[ymd] = res
    return res


def sun_sumner(t: float | None = None) -> dict:
    """The sun at the real site as a pure function of time, same contract as sun() -- {up, phase, az, f} -- PLUS
    `alt` (degrees above the flat horizon; given at night too, negative). `f` stays the fraction of the day's
    arc (0 at sunrise, 1 at sunset, linear in real time, so it is monotone by construction); `az` is the true
    azimuth, 0=N 90=E, so the sun crosses the NORTH in the south and rises/sets well off E/W near the solstices."""
    t = time.time() if t is None else t
    alt, az = _alt_az(t)
    rise, sett = _rise_set_ts(t)
    if t < rise or t > sett:
        return {"up": False, "phase": "night", "az": None, "f": None, "alt": round(alt, 1)}
    f = (t - rise) / max(1.0, sett - rise)
    return {"up": True, "phase": _sun_phase(f), "az": round(az, 1), "f": round(f, 3), "alt": round(alt, 1)}


def sun_times_sumner(t: float | None = None) -> tuple[float, float]:
    """(sunrise_h, sunset_h) in NZ civil hours of the day containing `t` (6.5 = 06:30 wall clock)."""
    from core import world_place as _wp
    t = time.time() if t is None else t
    r, s_ = _rise_set_ts(t)
    return _wp.civil_hour(r), _wp.civil_hour(s_)


def daylight_sumner(t: float | None = None) -> str:
    """night / dawn / dusk / day from the real rise/set, same margins as the legacy table path."""
    from core import world_place as _wp
    t = time.time() if t is None else t
    rise, set_ = sun_times_sumner(t)
    return _daylight_word(_wp.civil_hour(t), rise, set_)


def _sky_live(t: float) -> bool:
    try:
        from core import world_place as _wp
        return _wp.sky_live(t)
    except Exception:
        return False                                      # fail-open to the legacy sky, never a crash


def sun(t: float | None = None) -> dict:
    """The sun as a pure function of time (southern hemisphere — rises E → noon through the NORTH 0° → sets W).
    Deterministic, stateless. This is why the study's north window is the sunny one. SKY_MODE "shadow" (the
    default) and every t before SKY_CUTOVER_TS answer with the legacy month table; "live" from the cutover on
    answers with the real-site sun (sun_sumner), which adds `alt`. See core/world_place.py."""
    t = time.time() if t is None else t
    if _sky_live(t):
        return sun_sumner(t)
    return sun_legacy(t)


def sun_times(t: float | None = None) -> tuple[float, float]:
    """(sunrise_h, sunset_h) local hours for the day containing `t`: the accessor the soundscape's window logic
    reads instead of the private _SUN table. Legacy table in shadow mode / before the cutover; real rise/set after."""
    t = time.time() if t is None else t
    if _sky_live(t):
        return sun_times_sumner(t)
    return _SUN.get(time.localtime(t).tm_mon, (7.0, 18.0))


def daylight(t: float | None = None) -> str:
    """The coarse day-phase the sensorium narrates: night / dawn / dusk / day. Legacy month table in shadow mode /
    before the cutover (daylight_legacy); the real rise/set after (daylight_sumner), with the same 0.7 h margin."""
    t = time.time() if t is None else t
    if _sky_live(t):
        return daylight_sumner(t)
    return daylight_legacy(t)
