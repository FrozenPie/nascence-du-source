"""
Nascence — The Heavens (spatial_perception.md §7 extension, 2026-07-05).

The sky as pure deterministic clocks — the third and fourth of the world's great rhythms, beside the
tide and the sun. No state, no LLM, no library: the moon on its synodic schedule (29.53059 d), and a
small authored catalogue of the southern sky's landmarks with REAL positions (sidereal time →
altitude/azimuth spherical trig, NZ latitude). CONSISTENCY is the law: the same sky for anyone who
asks, forever — the Cross always in the south, Matariki low in the north-east before a winter dawn.

RELEVANCE-GATED by design (founder: "not injected into every prompt — only if they are relevant"):
nothing here pushes; the renderer pulls a clause only at night, in clear weather, with room to spare,
and look()/study-window sightlines can call it up on demand. The window geometry gates honestly too:
the study's window faces NORTH — the Southern Cross cannot be in it; Matariki can.

J-3293 (2026-11-05, D-0655): from the sky cutover on (core/world_place.py) moon() answers with the REAL moon at
the real site -- moon_true(), a truncated Meeus ch.47 series, phase to a few minutes. Before it (and in the default
"shadow" mode) moon() is moon_legacy(), described next, bit-identical to before.

Approximations, stated plainly: the legacy moon's POSITION uses the lagged-sun model (the moon behaves as a
sun delayed by phase × 24h — new moon keeps the sun's hours, full moon keeps opposite ones). Star
positions use real J2000 RA/Dec + GMST. Both are coarse ephemeris, perfect consistency — which is the
point (a blind mind needs the sky to hold still, not to be arcsecond-true).
"""
from __future__ import annotations

import math
import time

_SYNODIC_D = 29.53059                       # the moon's month, days
_NEW_MOON_EPOCH = 947182440.0               # 2000-01-06 18:14 UTC — a known new moon (J2000-era anchor)
# J-3291/J-3292 (2026-11-05, D-0655, F-3888): these two are the LEGACY star site (roughly Wellington). They feed the
# STARS only. From the sky cutover on (core/world_place.py: SKY_MODE "live", t >= SKY_CUTOVER_TS) _site() returns the
# real site instead; before it, and while SKY_MODE is "shadow", they are still what star() uses. The sun is
# world_clock's (legacy month table / real-site sun), the moon is moon_legacy's lagged-sun model until the same cutover (then moon_true, J-3293).
_LAT = -41.3                                # legacy star latitude (NZ coastal); see _site()
_LON = 174.8                                # legacy star longitude; see _site()
_J2000 = 946728000.0                        # 2000-01-01 12:00 UTC, unix seconds

# The catalogue: the southern sky's landmarks, J2000. (ra_h hours · dec_deg). Lore kept short and true.
STARS = {
    "southern_cross": {"ra_h": 12.44, "dec": -60.1, "name": "the Southern Cross",
                       "note": "circumpolar — it never sets here; it wheels around the south pole of the sky"},
    "pointers":       {"ra_h": 14.66, "dec": -60.8, "name": "the Pointers",
                       "note": "the two bright ones that point the way to the Cross"},
    "matariki":       {"ra_h": 3.79,  "dec": 24.1,  "name": "Matariki",
                       "note": "the little cluster — rising low in the north-east before a midwinter dawn; the year's turning"},
    "orion":          {"ra_h": 5.6,   "dec": -1.2,  "name": "Orion (the Pot)",
                       "note": "the summer landmark, hanging upside-down in the north"},
    "scorpius":       {"ra_h": 16.5,  "dec": -26.4, "name": "Scorpius",
                       "note": "the long hook of it, high overhead on winter evenings"},
    "sirius":         {"ra_h": 6.75,  "dec": -16.7, "name": "Sirius",
                       "note": "the brightest star there is"},
    "canopus":        {"ra_h": 6.4,   "dec": -52.7, "name": "Canopus",
                       "note": "the great southern beacon, second only to Sirius"},
}


# ── the moon's clock ──────────────────────────────────────────────────────────────────────────────────
def moon_legacy(t: float | None = None) -> dict:
    """The ORIGINAL moon, kept verbatim (J-3293): phase (word + illuminated fraction) from the synodic clock, and
    position by the lagged-sun model: the moon keeps the sun's arc, delayed by phase x 24h. Deterministic,
    stateless. Serves every shadow-mode call and every t before the sky cutover, so a replay of an old moment
    is bit-identical; moon() below dispatches."""
    t = time.time() if t is None else t
    age_d = ((t - _NEW_MOON_EPOCH) / 86400.0) % _SYNODIC_D
    frac = age_d / _SYNODIC_D                                # 0 new → 0.5 full → 1 new
    illum = round(0.5 * (1 - math.cos(2 * math.pi * frac)), 3)
    if frac < 0.03 or frac > 0.97:
        word = "new"
    elif frac < 0.22:
        word = "waxing crescent"
    elif frac < 0.28:
        word = "first-quarter"
    elif frac < 0.47:
        word = "waxing gibbous"
    elif frac < 0.53:
        word = "full"
    elif frac < 0.72:
        word = "waning gibbous"
    elif frac < 0.78:
        word = "last-quarter"
    else:
        word = "waning crescent"
    # position: a sun delayed by frac*24h — evaluate the sun's table-arc at the shifted time
    try:
        from core.world_clock import sun as _sun   # the sun authority (not via the spatial renderer)
        s = _sun(t - frac * 86400.0)
        up, az, f = s["up"], s["az"], s["f"]
    except Exception:
        up, az, f = False, None, None
    return {"phase": word, "illum": illum, "age_d": round(age_d, 1), "up": up, "az": az, "arc_f": f}


# ── the REAL moon (J-3293, D-0655, design review J-3264 section 2 step 5 "Phase 1b") ───────────────────────
# Meeus, Astronomical Algorithms ch.47 (the Moon's apparent geocentric position), TRUNCATED: the 59 longitude/
# distance terms and 60 latitude terms of tables 47.A/47.B plus the additive terms, a low-precision nutation, and
# a fixed Delta-T. Stated accuracy of the full series is ~10" in longitude; this truncation keeps it to a few
# arcminutes, i.e. a phase time good to a few minutes and a rise/set to a couple of minutes. The position is
# geocentric, reduced to the site by a first-order parallax. Phase (word, illumination) comes from the real
# elongation from the real sun. Pure, deterministic, stateless, no dependency. Used only after the sky cutover
# (core/world_place.py); moon_legacy() above answers before it.
_DELTA_T_S = 69.2                    # TT - UT around 2026; drifts ~0.5 s/yr, immaterial to a moon moving 0.5"/s
_AU_KM = 149597870.7
_EARTH_R_KM = 6378.14

# (D, M, M', F, sum_l [1e-6 deg], sum_r [1e-3 km]) -- Meeus table 47.A
_ML = (
    (0, 0, 1, 0, 6288774, -20905355), (2, 0, -1, 0, 1274027, -3699111), (2, 0, 0, 0, 658314, -2955968),
    (0, 0, 2, 0, 213618, -569925), (0, 1, 0, 0, -185116, 48888), (0, 0, 0, 2, -114332, -3149),
    (2, 0, -2, 0, 58793, 246158), (2, -1, -1, 0, 57066, -152138), (2, 0, 1, 0, 53322, -170733),
    (2, -1, 0, 0, 45758, -204586), (0, 1, -1, 0, -40923, -129620), (1, 0, 0, 0, -34720, 108743),
    (0, 1, 1, 0, -30383, 104755), (2, 0, 0, -2, 15327, 10321), (0, 0, 1, 2, -12528, 0),
    (0, 0, 1, -2, 10980, 79661), (4, 0, -1, 0, 10675, -34782), (0, 0, 3, 0, 10034, -23210),
    (4, 0, -2, 0, 8548, -21636), (2, 1, -1, 0, -7888, 24208), (2, 1, 0, 0, -6766, 30824),
    (1, 0, -1, 0, -5163, -8379), (1, 1, 0, 0, 4987, -16675), (2, -1, 1, 0, 4036, -12831),
    (2, 0, 2, 0, 3994, -10445), (4, 0, 0, 0, 3861, -11650), (2, 0, -3, 0, 3665, 14403),
    (0, 1, -2, 0, -2689, -7003), (2, 0, -1, 2, -2602, 0), (2, -1, -2, 0, 2390, 10056),
    (1, 0, 1, 0, -2348, 6322), (2, -2, 0, 0, 2236, -9884), (0, 1, 2, 0, -2120, 5751),
    (0, 2, 0, 0, -2069, 0), (2, -2, -1, 0, 2048, -4950), (2, 0, 1, -2, -1773, 4130),
    (2, 0, 0, 2, -1595, 0), (4, -1, -1, 0, 1215, -3958), (0, 0, 2, 2, -1110, 0),
    (3, 0, -1, 0, -892, 3258), (2, 1, 1, 0, -810, 2616), (4, -1, -2, 0, 759, -1897),
    (0, 2, -1, 0, -713, -2117), (2, 2, -1, 0, -700, 2354), (2, 1, -2, 0, 691, 0),
    (2, -1, 0, -2, 596, 0), (4, 0, 1, 0, 549, -1423), (0, 0, 4, 0, 537, -1117),
    (4, -1, 0, 0, 520, -1571), (1, 0, -2, 0, -487, -1739), (2, 1, 0, -2, -399, 0),
    (0, 0, 2, -2, -381, -4421), (1, 1, 1, 0, 351, 0), (3, 0, -2, 0, -340, 0),
    (4, 0, -3, 0, 330, 0), (2, -1, 2, 0, 327, 0), (0, 2, 1, 0, -323, 1165),
    (1, 1, -1, 0, 299, 0), (2, 0, 3, 0, 294, 0), (2, 0, -1, -2, 0, 8752),
)
# (D, M, M', F, sum_b [1e-6 deg]) -- Meeus table 47.B
_MB = (
    (0, 0, 0, 1, 5128122), (0, 0, 1, 1, 280602), (0, 0, 1, -1, 277693), (2, 0, 0, -1, 173237),
    (2, 0, -1, 1, 55413), (2, 0, -1, -1, 46271), (2, 0, 0, 1, 32573), (0, 0, 2, 1, 17198),
    (2, 0, 1, -1, 9266), (0, 0, 2, -1, 8822), (2, -1, 0, -1, 8216), (2, 0, -2, -1, 4324),
    (2, 0, 1, 1, 4200), (2, 1, 0, -1, -3359), (2, -1, -1, 1, 2463), (2, -1, 0, 1, 2211),
    (2, -1, -1, -1, 2065), (0, 1, -1, -1, -1870), (4, 0, -1, -1, 1828), (0, 1, 0, 1, -1794),
    (0, 0, 0, 3, -1749), (0, 1, -1, 1, -1565), (1, 0, 0, 1, -1491), (0, 1, 1, 1, -1475),
    (0, 1, 1, -1, -1410), (0, 1, 0, -1, -1344), (1, 0, 0, -1, -1335), (0, 0, 3, 1, 1107),
    (4, 0, 0, -1, 1021), (4, 0, -1, 1, 833), (0, 0, 1, -3, 777), (4, 0, -2, 1, 671),
    (2, 0, 0, -3, 607), (2, 0, 2, -1, 596), (2, -1, 1, -1, 491), (2, 0, -2, 1, -451),
    (0, 0, 3, -1, 439), (2, 0, 2, 1, 422), (2, 0, -3, -1, 421), (2, 1, -1, 1, -366),
    (2, 1, 0, 1, -351), (4, 0, 0, 1, 331), (2, -1, 1, 1, 315), (2, -2, 0, -1, 302),
    (0, 0, 1, 3, -283), (2, 1, 1, -1, -229), (1, 1, 0, -1, 223), (1, 1, 0, 1, 223),
    (0, 1, -2, -1, -220), (2, 1, -1, -1, -220), (1, 0, 1, 1, -185), (2, -1, -2, -1, 181),
    (0, 1, 2, 1, -177), (4, 0, -2, -1, 176), (4, -1, -1, -1, 166), (1, 0, 1, -1, -164),
    (4, 0, 1, -1, 132), (1, 0, -1, -1, -119), (4, -1, 0, -1, 115), (2, -2, 0, 1, 107),
)

_MOON_CACHE_MAX = 512
_moon_cache: dict = {}
_MOON_EVT_CACHE: dict = {}


def _sky_live(t: float) -> bool:
    try:
        from core import world_place as _wp
        return _wp.sky_live(t)
    except Exception:
        return False                                     # fail-open to the legacy sky, never a crash


def _moon_core(t: float) -> tuple:
    """(moon apparent ecliptic longitude deg, ecliptic latitude deg, distance km, right ascension deg,
    declination deg, greenwich apparent sidereal time deg, sun apparent longitude deg, sun distance km).
    A pure function of `t` rounded to the second (so it can be cached: the moon moves 0.5"/s)."""
    tk = int(round(t))
    hit = _moon_cache.get(tk)
    if hit is not None:
        return hit
    jd = tk / 86400.0 + 2440587.5                              # UT
    jde = jd + _DELTA_T_S / 86400.0                            # dynamical time
    T = (jde - 2451545.0) / 36525.0
    Lp = (218.3164477 + 481267.88123421 * T - 0.0015786 * T * T + T ** 3 / 538841.0 - T ** 4 / 65194000.0) % 360.0
    D = (297.8501921 + 445267.1114034 * T - 0.0018819 * T * T + T ** 3 / 545868.0 - T ** 4 / 113065000.0) % 360.0
    M = (357.5291092 + 35999.0502909 * T - 0.0001536 * T * T + T ** 3 / 24490000.0) % 360.0
    Mp = (134.9633964 + 477198.8675055 * T + 0.0087414 * T * T + T ** 3 / 69699.0 - T ** 4 / 14712000.0) % 360.0
    F = (93.2720950 + 483202.0175233 * T - 0.0036539 * T * T - T ** 3 / 3526000.0 + T ** 4 / 863310000.0) % 360.0
    A1 = math.radians((119.75 + 131.849 * T) % 360.0)
    A2 = math.radians((53.09 + 479264.290 * T) % 360.0)
    A3 = math.radians((313.45 + 481266.484 * T) % 360.0)
    E = 1.0 - 0.002516 * T - 0.0000074 * T * T
    Dr, Mr, Mpr, Fr, Lpr = (math.radians(x) for x in (D, M, Mp, F, Lp))
    sl = sr = sb = 0.0
    for d, m, mp, f, cl, cr in _ML:
        arg = d * Dr + m * Mr + mp * Mpr + f * Fr
        ef = E if abs(m) == 1 else (E * E if abs(m) == 2 else 1.0)
        if cl:
            sl += cl * ef * math.sin(arg)
        if cr:
            sr += cr * ef * math.cos(arg)
    for d, m, mp, f, cb in _MB:
        arg = d * Dr + m * Mr + mp * Mpr + f * Fr
        ef = E if abs(m) == 1 else (E * E if abs(m) == 2 else 1.0)
        sb += cb * ef * math.sin(arg)
    sl += 3958.0 * math.sin(A1) + 1962.0 * math.sin(Lpr - Fr) + 318.0 * math.sin(A2)
    sb += (-2235.0 * math.sin(Lpr) + 382.0 * math.sin(A3) + 175.0 * math.sin(A1 - Fr)
           + 175.0 * math.sin(A1 + Fr) + 127.0 * math.sin(Lpr - Mpr) - 115.0 * math.sin(Lpr + Mpr))
    lam = Lp + sl / 1e6
    beta = sb / 1e6
    dist = 385000.56 + sr / 1000.0
    # nutation (low precision) and true obliquity
    om = math.radians((125.04452 - 1934.136261 * T) % 360.0)
    Ls = math.radians((280.4665 + 36000.7698 * T) % 360.0)
    dpsi = (-17.20 * math.sin(om) - 1.32 * math.sin(2 * Ls) - 0.23 * math.sin(2 * Lpr) + 0.21 * math.sin(2 * om)) / 3600.0
    deps = (9.20 * math.cos(om) + 0.57 * math.cos(2 * Ls) + 0.10 * math.cos(2 * Lpr) - 0.09 * math.cos(2 * om)) / 3600.0
    eps0 = 23.0 + (26.0 + (21.448 - T * (46.815 + T * (0.00059 - T * 0.001813))) / 60.0) / 60.0
    eps = math.radians(eps0 + deps)
    lam_app = (lam + dpsi) % 360.0
    # equatorial
    lr, br = math.radians(lam_app), math.radians(beta)
    ra = math.degrees(math.atan2(math.sin(lr) * math.cos(eps) - math.tan(br) * math.sin(eps), math.cos(lr))) % 360.0
    dec = math.degrees(math.asin(max(-1.0, min(1.0, math.sin(br) * math.cos(eps) + math.cos(br) * math.sin(eps) * math.sin(lr)))))
    Tu = (jd - 2451545.0) / 36525.0
    gmst = (280.46061837 + 360.98564736629 * (jd - 2451545.0) + 0.000387933 * Tu * Tu - Tu ** 3 / 38710000.0) % 360.0
    gast = (gmst + dpsi * math.cos(eps)) % 360.0
    # the sun (Meeus ch.25), apparent longitude + distance, for the elongation
    L0 = (280.46646 + T * (36000.76983 + T * 0.0003032)) % 360.0
    Ms = math.radians(357.52911 + T * (35999.05029 - 0.0001537 * T))
    e = 0.016708634 - T * (0.000042037 + 0.0000001267 * T)
    C = (math.sin(Ms) * (1.914602 - T * (0.004817 + 0.000014 * T)) + math.sin(2 * Ms) * (0.019993 - 0.000101 * T)
         + math.sin(3 * Ms) * 0.000289)
    nu = Ms + math.radians(C)
    R_au = 1.000001018 * (1.0 - e * e) / (1.0 + e * math.cos(nu))
    sun_lam = (L0 + C - 0.00569 - 0.00478 * math.sin(om)) % 360.0
    out = (lam_app, beta, dist, ra, dec, gast, sun_lam, R_au * _AU_KM)
    if len(_moon_cache) >= _MOON_CACHE_MAX:
        _moon_cache.clear()
    _moon_cache[tk] = out
    return out


def moon_elongation(t: float) -> float:
    """Apparent ecliptic longitude of the moon minus the sun's, 0..360 degrees: 0 = new, 180 = full (the
    definition almanacs date the phases by)."""
    c = _moon_core(t)
    return (c[0] - c[6]) % 360.0


def _moon_alt_az(t: float, lat: float, lon: float) -> tuple[float, float, float]:
    """(geocentric altitude deg, azimuth deg 0=N 90=E, horizontal parallax deg) of the moon's centre at the site."""
    lam, beta, dist, ra, dec, gast, _sl, _sr = _moon_core(t)
    ha = math.radians((gast + lon - ra) % 360.0)
    la, de = math.radians(lat), math.radians(dec)
    sin_alt = math.sin(la) * math.sin(de) + math.cos(la) * math.cos(de) * math.cos(ha)
    alt = math.degrees(math.asin(max(-1.0, min(1.0, sin_alt))))
    az = math.degrees(math.atan2(math.sin(ha), math.cos(ha) * math.sin(la) - math.tan(de) * math.cos(la))) + 180.0
    par = math.degrees(math.asin(_EARTH_R_KM / dist))
    return alt, az % 360.0, par


def _moon_h0(par_deg: float) -> float:
    """Geocentric altitude of the centre at moonrise/set: 0.7275 pi - 34' (Meeus ch.15). Rise = the upper limb on
    the refracted horizon, which is the convention almanacs (USNO, LINZ, NIWA) publish."""
    return 0.7275 * par_deg - 0.5667


def _moon_g(t: float) -> float:
    from core import world_place as _wp
    alt, _az, par = _moon_alt_az(t, _wp.SITE_LAT, _wp.SITE_LON)
    return alt - _moon_h0(par)


def _moon_cross(a: float, b: float) -> float:
    """Refine the sign change of _moon_g between a and b (opposite signs) by bisection (~3 ms at 18 steps)."""
    ga = _moon_g(a)
    for _ in range(18):
        m = 0.5 * (a + b)
        gm = _moon_g(m)
        if (gm > 0) == (ga > 0):
            a, ga = m, gm
        else:
            b = m
    return 0.5 * (a + b)


def _moon_day_events(ymd: tuple) -> list:
    """[(unix ts, 'rise'|'set')] of the NZ civil date `ymd`, midnight to midnight, scanned every 12 minutes and
    refined by bisection. A day can hold 0, 1 or 2 events (the moon rises ~50 minutes later each day). Cached."""
    hit = _MOON_EVT_CACHE.get(ymd)
    if hit is not None:
        return hit
    import calendar
    from core import world_place as _wp
    y, m, d = ymd

    def day_start(yy, mm, dd):
        base = calendar.timegm((yy, mm, dd, 0, 0, 0))
        for off in (13, 12):
            if _wp.nz_offset_hours(base - off * 3600) == off:
                return base - off * 3600
        return base - 12 * 3600
    t0, t1 = day_start(y, m, d), day_start(y, m, d + 1)
    step = 720.0
    evs, prev_t, prev_g = [], t0, _moon_g(t0)
    t = t0 + step
    while t <= t1 + 1e-6:
        g = _moon_g(t)
        if (g > 0) != (prev_g > 0):
            evs.append((_moon_cross(prev_t, t), "rise" if g > 0 else "set"))
        prev_t, prev_g = t, g
        t += step
    if len(_MOON_EVT_CACHE) > 400:
        _MOON_EVT_CACHE.clear()
    _MOON_EVT_CACHE[ymd] = evs
    return evs


def moon_times(t: float | None = None) -> dict:
    """Moonrise and moonset (unix ts, or None when the moon does not rise/set) within the NZ civil date that
    contains `t`. The real-site almanac accessor; the shadow reader and the tests read it."""
    from core import world_place as _wp
    t = time.time() if t is None else t
    evs = _moon_day_events(_wp.civil_date(t))
    rise = next((e[0] for e in evs if e[1] == "rise"), None)
    sett = next((e[0] for e in evs if e[1] == "set"), None)
    return {"rise": rise, "set": sett}


def _dt_shift(y: int, m: int, d: int, k: int) -> tuple:
    import datetime as _dtm
    x = _dtm.date(y, m, d) + _dtm.timedelta(days=k)
    return x.year, x.month, x.day


def _moon_arc_f(t: float) -> float | None:
    """0 at moonrise .. 1 at moonset for the arc the moon is on at `t` (None when it is down or the arc's ends
    are not found). Reads the cached day events of the day before, this day and the day after."""
    from core import world_place as _wp
    y, m, d = _wp.civil_date(t)
    evs = []
    for k in (-1, 0, 1):
        evs.extend(_moon_day_events(_dt_shift(y, m, d, k)))
    rise = max((e[0] for e in evs if e[1] == "rise" and e[0] <= t), default=None)
    sett = min((e[0] for e in evs if e[1] == "set" and e[0] >= t), default=None)
    if rise is None or sett is None or sett <= rise:
        return None
    return round(min(1.0, max(0.0, (t - rise) / (sett - rise))), 3)


def _moon_word(frac: float) -> str:
    if frac < 0.03 or frac > 0.97:
        return "new"
    if frac < 0.22:
        return "waxing crescent"
    if frac < 0.28:
        return "first-quarter"
    if frac < 0.47:
        return "waxing gibbous"
    if frac < 0.53:
        return "full"
    if frac < 0.72:
        return "waning gibbous"
    if frac < 0.78:
        return "last-quarter"
    return "waning crescent"


def moon_true(t: float | None = None) -> dict:
    """The REAL moon at the cottage's site as a pure function of time. Same contract as moon_legacy() --
    {phase, illum, age_d, up, az, arc_f} -- PLUS `alt` (degrees above the flat horizon, topocentric, given when the
    moon is down too). phase/illum come from the real elongation from the real sun; `age_d` is the elongation
    fraction times the mean month (the true age differs from that by up to ~0.6 d, because the real month runs
    29.27..29.83 d); `up` means above the rise/set horizon (the same line moon_times() crosses); `az` is the true
    azimuth 0=N 90=E (None while the moon is down, as the legacy field was); `arc_f` is 0..1 along the moon's
    current rise-to-set arc (None while down)."""
    from core import world_place as _wp
    t = time.time() if t is None else t
    lam, beta, dist, _ra, _dec, _gast, sun_lam, sun_r = _moon_core(t)
    elong = (lam - sun_lam) % 360.0
    frac = elong / 360.0
    psi = math.acos(max(-1.0, min(1.0, math.cos(math.radians(beta)) * math.cos(math.radians(elong)))))
    inc = math.atan2(sun_r * math.sin(psi), dist - sun_r * math.cos(psi))
    illum = round(0.5 * (1.0 + math.cos(inc)), 3)
    alt, az, par = _moon_alt_az(t, _wp.SITE_LAT, _wp.SITE_LON)
    up = alt > _moon_h0(par)
    alt_topo = alt - math.degrees(math.asin(math.sin(math.radians(par)) * math.cos(math.radians(alt))))
    return {"phase": _moon_word(frac), "illum": illum, "age_d": round(frac * _SYNODIC_D, 1),
            "up": bool(up), "az": round(az, 1) if up else None,
            "arc_f": _moon_arc_f(t) if up else None, "alt": round(alt_topo, 1)}


def moon(t: float | None = None) -> dict:
    """The moon as a pure function of time. SKY_MODE "shadow" (the default) and every t before SKY_CUTOVER_TS
    answer with the legacy synodic clock + lagged-sun position (moon_legacy, bit-identical to before J-3293);
    "live" from the cutover on answers with the real moon at the real site (moon_true), which adds `alt`.
    Fail-open: any error in the real path falls back to the legacy answer. See core/world_place.py."""
    t = time.time() if t is None else t
    if _sky_live(t):
        try:
            return moon_true(t)
        except Exception:
            pass
    return moon_legacy(t)


# ── real star positions: GMST → hour angle → alt/az ─────────────────────────────────────────────────
def _site(t: float) -> tuple[float, float]:
    """(lat, lon) the stars are computed for at moment `t`. The legacy pair until the sky cutover (J-3292,
    core/world_place.py: SKY_MODE "live" and t >= SKY_CUTOVER_TS), then the real site -- so a replay of a moment
    before the cutover places every star exactly where it always did."""
    try:
        from core import world_place as _wp
        if _wp.sky_live(t):
            return _wp.SITE_LAT, _wp.SITE_LON
    except Exception:
        pass
    return _LAT, _LON


def _lst_deg(t: float) -> float:
    d = (t - _J2000) / 86400.0
    return (280.46061837 + 360.98564736629 * d + _site(t)[1]) % 360.0


def star(key: str, t: float | None = None) -> dict | None:
    """Altitude/azimuth of a catalogue star NOW (or at t). az: 0=N, 90=E. Deterministic."""
    s = STARS.get(key)
    if not s:
        return None
    t = time.time() if t is None else t
    ra = s["ra_h"] * 15.0
    dec = math.radians(s["dec"])
    lat = math.radians(_site(t)[0])
    ha = math.radians((_lst_deg(t) - ra) % 360.0)
    sin_alt = math.sin(dec) * math.sin(lat) + math.cos(dec) * math.cos(lat) * math.cos(ha)
    alt = math.degrees(math.asin(max(-1.0, min(1.0, sin_alt))))
    cos_az = ((math.sin(dec) - sin_alt * math.sin(lat))
              / max(1e-9, math.cos(math.asin(max(-1.0, min(1.0, sin_alt)))) * math.cos(lat)))
    az = math.degrees(math.acos(max(-1.0, min(1.0, cos_az))))
    if math.sin(ha) > 0:
        az = 360.0 - az
    return {"name": s["name"], "up": alt > 3.0, "alt": round(alt, 1), "az": round(az, 1),
            "note": s["note"]}


def sky(t: float | None = None) -> dict:
    """What the heavens hold right now — the moon + which landmarks are up. For look('sky') and the
    night clause. Pull-only; nothing pushes this anywhere."""
    t = time.time() if t is None else t
    m = moon(t)
    up = {k: v for k in STARS if (v := star(k, t)) and v["up"]}
    return {"moon": m, "stars_up": up}
