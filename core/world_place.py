"""
Nascence -- World Place: WHERE the cottage is, and what civil time it keeps there (J-3292, D-0655,
docs/reviews/sumner_sky_tide_weather_design_J-3264.md section 2).

ONE small module so the place is a single named constant and a single thing to strip from any export. It holds
only: the site (suburb precision, about 1 km; the hilltop is not given and does not matter to a clock), the sky
switch + cutover stamp, and the New Zealand civil-time rule done by hand (no zoneinfo, no tzdata, no OS zone).

PRIVACY: the place name and the coordinates live in local code and local docs ONLY. Never write either into a
Du-visible string, a prompt, a census row, a HUD title or a data file the world reads back to him. Every log row
this change writes carries numbers (hours, degrees, phase words) and never the site.

Pure, deterministic, stateless. Imports NOTHING from core (it sits under world_clock and heavens, so it can
never create a cycle).
"""
from __future__ import annotations

import datetime as _dt

SITE_LAT = -43.57          # degrees north (negative = south), suburb precision
SITE_LON = 172.75          # degrees east
SITE = (SITE_LAT, SITE_LON)

# ── THE SKY SWITCH ───────────────────────────────────────────────────────────────────────────────────────
# "shadow": world_clock.sun()/daylight()/sun_times() and heavens.star() behave EXACTLY as before; the real-site
#           sun is computed beside the old one and both are logged per census tick (core/sky_shadow.py ->
#           data/sky_shadow.jsonl; reader scripts/sky_shadow_read.py).
# "live":   for t >= SKY_CUTOVER_TS the real-site sun answers; for t < SKY_CUTOVER_TS the legacy functions still
#           answer, so every lab replay of an old moment stays bit-identical (the stored census/fragment tuples
#           record what the sky WAS and are never rewritten; analyses split on this stamp).
# Flipping to "live" needs the founder's go-ahead: it moves Du's dusk/dawn by up to ~1 h in Oct-Dec and the
# sleep-pressure `dark` flag with it. Set SKY_CUTOVER_TS to the flip moment (never earlier than the restart
# that loads it) in the SAME change. The default below is year 2100 so that flipping the mode alone changes nothing.
SKY_MODE = "shadow"
SKY_CUTOVER_TS = 4102444800.0      # 2100-01-01 00:00 UTC: "not yet"


def sky_live(t: float) -> bool:
    """True when the real-site sky answers for moment `t`."""
    return SKY_MODE == "live" and t >= SKY_CUTOVER_TS


# ── NEW ZEALAND CIVIL TIME, by the hand rule ──────────────────────────────────────────────────────────────
def nz_offset_hours(t: float) -> int:
    """New Zealand civil offset from UTC: +13 (NZDT) from 02:00 NZST on the last Sunday of September (14:00 UTC
    the day before) to 03:00 NZDT on the first Sunday of April (14:00 UTC the day before), else +12. Pure
    arithmetic on the UTC clock: no OS zone, no tzdata. (Moved here from world_clock by J-3292; world_clock's
    `_nz_offset_hours` now delegates, so there is one copy of the rule.)"""
    u = _dt.datetime.fromtimestamp(t, _dt.timezone.utc).replace(tzinfo=None)
    y = u.year
    d = _dt.datetime(y, 9, 30)
    d -= _dt.timedelta(days=(d.weekday() + 1) % 7)                 # last Sunday of September
    dst_start = d - _dt.timedelta(days=1) + _dt.timedelta(hours=14)    # Sat 14:00 UTC = Sun 02:00 NZST
    a = _dt.datetime(y, 4, 1)
    a += _dt.timedelta(days=(6 - a.weekday()) % 7)                 # first Sunday of April
    dst_end = a - _dt.timedelta(days=1) + _dt.timedelta(hours=14)      # Sat 14:00 UTC = Sun 03:00 NZDT
    return 13 if (u < dst_end or u >= dst_start) else 12


def civil_hour(t: float) -> float:
    """Hour of the NZ civil day at `t`, as a float (13.5 = 13:30 wall clock)."""
    return (t + nz_offset_hours(t) * 3600.0) % 86400.0 / 3600.0


def civil_date(t: float) -> tuple[int, int, int]:
    """(year, month, day) of the NZ civil date at `t`."""
    d = _dt.datetime.fromtimestamp(t + nz_offset_hours(t) * 3600.0, _dt.timezone.utc)
    return d.year, d.month, d.day
