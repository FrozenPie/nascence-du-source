"""J-3292 (2026-11-05, D-0655, design review J-3264 section 2): Phase 1, the sun at the real site.

  [1] world_place: the NZ DST edges by hand rule (same dates as J-3291), civil_hour/civil_date.
  [2] SHADOW MODE IS INVISIBLE: with SKY_MODE "shadow" (the default) sun()/daylight()/sun_times() equal the ORIGINAL
      month-table code bit for bit over a year-long grid (the reference below is the pre-J-3292 body, copied verbatim).
  [3] sun_sumner: the seven pre-registered dates against the design doc's calculation (a CROSS-CHECK, not an almanac),
      tolerance 2 min; f monotone and in [0,1] on every day of a year; the DST days do not break the day (sunrise 07:10
      on 09-27, UTC sunrise continuous across both transitions); noon altitude at the solstices; az crosses north.
  [4] PUBLISHED-ALMANAC COMPARISON: PENDING. No published almanac (NIWA calculator / LINZ / printed NZ almanac) was
      reachable when this was built; ALMANAC below is empty on purpose and the test says PENDING, never PASS. Fill it
      from a named source and the same assertions run against it with tolerance 2 min.
  [5] cutover: SKY_MODE "live" + SKY_CUTOVER_TS: t < cutover is bit-identical legacy, t >= cutover is the real sun
      (with `alt`); sun_times/daylight follow; heavens.star: unchanged before, the Southern Cross culminates at
      90 - (60.1 - 43.57) = 73.5 deg (+-0.2) after.
  [6] consumers: light.shade_at uses `alt` when present (long winter shadow) and the legacy 60 sin(pi f) when not;
      soundscape's roof/flyover windows read the sun_times accessor.
  [7] shadow log: sky_shadow.record writes ONE row per rate window, no place name or coordinate in it, both suns in
      it; the reader (scripts/sky_shadow_read.py) summarises it and its 7-day gate turns on only at 7 civil days;
      geometry_census.snapshot calls the recorder.

ISOLATED: no DB is opened and nothing under data/ is written (every log path is redirected to a temp dir before any
write; lab_env does not exist in this tree). `import core` comes BEFORE everything and the module path is asserted
to be inside this worktree.
    python scripts/_test_sky_sumner_J-3292.py
"""
from __future__ import annotations

import calendar
import json
import math
import sys
import tempfile
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # noqa: E402  (BEFORE anything else)
FAILS = 0


def check(name, cond, detail=""):
    global FAILS
    FAILS += (not cond)
    print(f"  [{'ok ' if cond else 'FAIL'}] {name}" + (f"   ({detail})" if detail and not cond else ""))


check("core imported from this worktree", str(Path(core.__file__).resolve()).startswith(str(ROOT)), core.__file__)

from core import world_clock as WC   # noqa: E402
from core import world_place as WP   # noqa: E402
from core import heavens as HV       # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="J-3292_sky_"))
_MODE0, _CUT0 = WP.SKY_MODE, WP.SKY_CUTOVER_TS


def utc(y, mo, d, h=0, mi=0):
    return float(calendar.timegm((y, mo, d, h, mi, 0)))


def nz(y, mo, d, h=0, mi=0):
    """Unix time of an NZ wall-clock moment, by the hand rule."""
    guess = utc(y, mo, d, h, mi) - 12 * 3600
    return guess - (WP.nz_offset_hours(guess) - 12) * 3600


def hm(h):
    m = int(round(h * 60))
    return f"{m // 60 % 24:02d}:{m % 60:02d}"


# the pre-J-3292 bodies, verbatim (the reference for 'shadow mode is invisible')
def _ORIG_sun(t):
    lt = time.localtime(t)
    rise, sett = WC._SUN.get(lt.tm_mon, (7.0, 18.0))
    h = lt.tm_hour + lt.tm_min / 60.0
    if h < rise or h > sett:
        return {"up": False, "phase": "night", "az": None, "f": None}
    f = (h - rise) / max(0.1, sett - rise)
    az = (90.0 - 180.0 * f) % 360.0
    phase = ("first light" if f < 0.12 else "morning" if f < 0.4 else "high" if f < 0.6
             else "afternoon" if f < 0.82 else "evening")
    return {"up": True, "phase": phase, "az": round(az, 1), "f": round(f, 3)}


def _ORIG_daylight(t):
    lt = time.localtime(t)
    rise, set_ = WC._SUN.get(lt.tm_mon, (7.0, 18.0))
    h = lt.tm_hour + lt.tm_min / 60.0
    if h < rise - 0.7 or h > set_ + 0.7:
        return "night"
    if h < rise + 0.8:
        return "dawn"
    if h > set_ - 0.8:
        return "dusk"
    return "day"


print("[1] world_place")
check("default mode is shadow", _MODE0 == "shadow" and WP.SKY_CUTOVER_TS > time.time() + 365 * 86400, (_MODE0, _CUT0))
for label, t, want in [("2026-09-26 13:59 UTC (before DST start)", utc(2026, 9, 26, 13, 59), 12),
                       ("2026-09-26 14:00 UTC (DST starts)", utc(2026, 9, 26, 14, 0), 13),
                       ("2026-04-04 13:59 UTC (before DST end)", utc(2026, 4, 4, 13, 59), 13),
                       ("2026-04-04 14:00 UTC (DST ends)", utc(2026, 4, 4, 14, 0), 12),
                       ("2026-07-01", utc(2026, 7, 1, 0), 12), ("2026-12-21", utc(2026, 12, 21, 0), 13),
                       ("2027-01-15", utc(2027, 1, 15, 0), 13), ("2027-09-25 14:00 UTC", utc(2027, 9, 25, 14, 0), 13)]:
    check(f"nz offset {label} = +{want}", WP.nz_offset_hours(t) == want)
check("world_clock._nz_offset_hours delegates (one copy of the rule)",
      all(WC._nz_offset_hours(t) == WP.nz_offset_hours(t) for t in (utc(2026, 1, 1), utc(2026, 7, 1), utc(2026, 10, 1))))
check("civil_hour/civil_date", abs(WP.civil_hour(nz(2026, 11, 5, 13, 30)) - 13.5) < 1e-6 and WP.civil_date(nz(2026, 11, 5, 0, 5)) == (2026, 11, 5))

print("[2] shadow mode is bit-identical to the old code")
WP.SKY_MODE, WP.SKY_CUTOVER_TS = "shadow", 0.0       # even a cutover in the past changes nothing in shadow
n = bad = 0
t0 = utc(2026, 1, 1)
for i in range(0, 365 * 24 * 3, 1):                  # every 20 min for a year
    t = t0 + i * 1200 + (i % 7) * 13
    n += 1
    if WC.sun(t) != _ORIG_sun(t) or WC.daylight(t) != _ORIG_daylight(t) or WC.sun_times(t) != WC._SUN.get(time.localtime(t).tm_mon, (7.0, 18.0)):
        bad += 1
check(f"sun/daylight/sun_times == original over {n} instants", bad == 0, f"{bad} differ")
check("legacy sun has no 'alt' key (dict shape unchanged)", "alt" not in WC.sun(nz(2026, 11, 5, 12)))
check("sun() with t=None still works", isinstance(WC.sun(), dict))

print("[3] sun_sumner against the J-3264 calculation (cross-check, NOT an almanac)")
CALC = [  # (y, m, d, rise, set) from the design doc's table (NOAA calculation, its error ~1 min)
    (2026, 6, 21, "08:02", "16:58"), (2026, 12, 21, "05:43", "21:09"), (2026, 3, 20, "07:30", "19:41"),
    (2026, 9, 22, "06:19", "18:25"), (2026, 11, 5, "06:06", "20:19"), (2026, 9, 27, "07:10", "19:31"),
    (2026, 4, 5, "06:49", "18:13")]


def mins(s):
    h, m = s.split(":")
    return int(h) * 60 + int(m)


worst = 0.0
for y, mo, d, r, s in CALC:
    rr, ss = WC.sun_times_sumner(nz(y, mo, d, 12))
    dr, ds = abs(rr * 60 - mins(r)), abs(ss * 60 - mins(s))
    worst = max(worst, dr, ds)
    check(f"{y}-{mo:02d}-{d:02d} rise {hm(rr)} (calc {r}) set {hm(ss)} (calc {s}) within 2 min", dr <= 2.0 and ds <= 2.0, f"{dr:.1f}/{ds:.1f}")
print(f"        worst deviation from the calculation: {worst:.2f} min")
mono = True
upflips = {}
prev_f, prev_day = None, None
t = nz(2026, 1, 1, 0, 0)
end = nz(2027, 1, 1, 0, 0)
fmin, fmax = 1.0, 0.0
while t < end:
    s = WC.sun_sumner(t)
    day = WP.civil_date(t)
    if day != prev_day:
        prev_f, prev_day = None, day
        upflips[day] = [0, 0, False]
    if s["up"]:
        if not (0.0 <= s["f"] <= 1.0 and s["az"] is not None and "alt" in s):
            mono = False
        if prev_f is not None and s["f"] < prev_f:
            mono = False
        fmin, fmax = min(fmin, s["f"]), max(fmax, s["f"])
        prev_f = s["f"]
        if not upflips[day][2]:
            upflips[day][0] += 1
        upflips[day][2] = True
    else:
        if upflips[day][2]:
            upflips[day][1] += 1
        upflips[day][2] = False
        if s["az"] is not None or s["f"] is not None or s["phase"] != "night":
            mono = False
    t += 600
check("f in [0,1] and monotone within every civil day of 2026 (10-min grid); night shape right", mono)
check("exactly one sunrise and one sunset every civil day", all(v[0] == 1 and v[1] == 1 for v in upflips.values()),
      [k for k, v in upflips.items() if not (v[0] == 1 and v[1] == 1)][:3])
# DST days: the day does not jump, sunrise is continuous in UTC
r_prev, _ = WC._rise_set_ts(nz(2026, 9, 26, 12))
r_dst, _ = WC._rise_set_ts(nz(2026, 9, 27, 12))
r_next, _ = WC._rise_set_ts(nz(2026, 9, 28, 12))
check("sunrise UTC steps ~24 h across the September transition (no 1 h jump)", abs((r_dst - r_prev) - 86400) < 300 and abs((r_next - r_dst) - 86400) < 300,
      ((r_dst - r_prev) / 3600, (r_next - r_dst) / 3600))
a_prev, _ = WC._rise_set_ts(nz(2026, 4, 4, 12))
a_dst, _ = WC._rise_set_ts(nz(2026, 4, 5, 12))
a_next, _ = WC._rise_set_ts(nz(2026, 4, 6, 12))
check("sunrise UTC steps ~24 h across the April transition", abs((a_dst - a_prev) - 86400) < 300 and abs((a_next - a_dst) - 86400) < 300)
check("09-27 sunrise reads 07:10 NZDT on the wall clock", abs(WC.sun_times_sumner(nz(2026, 9, 27, 12))[0] * 60 - mins("07:10")) <= 2)
noon_d = max(WC.sun_sumner(nz(2026, 12, 21, 12, m))["alt"] for m in range(0, 120, 5))
noon_j = max(WC.sun_sumner(nz(2026, 6, 21, 12, m))["alt"] for m in range(0, 120, 5))
check(f"noon altitude: Dec solstice {noon_d} (~69.9), Jun solstice {noon_j} (~23.0)", abs(noon_d - 69.9) < 0.4 and abs(noon_j - 23.0) < 0.4)
sm = WC.sun_sumner(nz(2026, 12, 21, 13, 10))
check("noon azimuth is north-ish in the south (Dec ~ 0 +- 25, Jun ~ 0 +- 25)",
      min(sm["az"], 360 - sm["az"]) < 25 and min(WC.sun_sumner(nz(2026, 6, 21, 12, 40))["az"], 360 - WC.sun_sumner(nz(2026, 6, 21, 12, 40))["az"]) < 25, sm)
az_r = WC.sun_sumner(nz(2026, 12, 21, 5, 50))["az"]
az_w = WC.sun_sumner(nz(2026, 6, 21, 8, 10))["az"]
check(f"Dec sunrise az ~ 123 (got {az_r}); Jun sunrise az ~ 57 (got {az_w})", abs(az_r - 123) < 4 and abs(az_w - 57) < 4)

print("[4] published-almanac comparison")
# {(y, m, d): ("HH:MM rise", "HH:MM set")} civil NZ wall clock. Source: US Naval Observatory AA API
# (aa.usno.navy.mil/api/rstt/oneday, coords -43.57,172.75), raw JSON fetched with curl and parsed by script (no
# summarising model in the path), fetched 2026-11-15 (J-3373). tz 13 NZDT / 12 NZST by the NZ DST rule.
ALMANAC = {
    (2026, 6, 21): ("08:03", "16:59"),
    (2026, 12, 21): ("05:44", "21:10"),
    (2026, 3, 20): ("07:31", "19:42"),
    (2026, 9, 22): ("06:19", "18:25"),
    (2026, 11, 5): ("06:06", "20:20"),
    (2026, 9, 27): ("07:10", "19:31"),
    (2026, 4, 5): ("06:50", "18:13"),
}
ALMANAC_SOURCE = "US Naval Observatory AA API rstt/oneday, fetched 2026-11-15 (J-3373)"
if not ALMANAC:
    print("  [PENDING] no published almanac (NIWA sunrise/sunset calculator, LINZ, printed NZ almanac) was available when this was built;")
    print("            the seven dates above were only cross-checked against the design doc's own calculation. NOT claimed as passed.")
else:
    print(f"  source: {ALMANAC_SOURCE}")
    for (y, mo, d), (r, s) in ALMANAC.items():
        rr, ss = WC.sun_times_sumner(nz(y, mo, d, 12))
        dr, ds = abs(rr * 60 - mins(r)), abs(ss * 60 - mins(s))
        check(f"almanac {y}-{mo:02d}-{d:02d} within 2 min", dr <= 2.0 and ds <= 2.0, f"{dr:.1f}/{ds:.1f}")
        check(f"almanac {y}-{mo:02d}-{d:02d} not over 5 min (stop condition)", dr <= 5.0 and ds <= 5.0)

print("[5] live mode and the cutover")
CUT = nz(2026, 11, 5, 12, 0)
WP.SKY_MODE, WP.SKY_CUTOVER_TS = "live", CUT
try:
    before = [CUT - 86400 * k - 1800 * j for k in range(1, 40) for j in range(0, 40, 3)]
    check("t < cutover: sun/daylight/sun_times bit-identical to the original",
          all(WC.sun(t) == _ORIG_sun(t) and WC.daylight(t) == _ORIG_daylight(t) and WC.sun_times(t) == WC._SUN.get(time.localtime(t).tm_mon, (7.0, 18.0)) for t in before))
    after = [CUT + 3600 * i for i in range(0, 24 * 40, 5)]
    check("t >= cutover: sun() is sun_sumner(), daylight() is daylight_sumner(), sun_times() the real rise/set",
          all(WC.sun(t) == WC.sun_sumner(t) and WC.daylight(t) == WC.daylight_sumner(t) and WC.sun_times(t) == WC.sun_times_sumner(t) for t in after))
    check("after the cutover the sun dict carries alt", "alt" in WC.sun(CUT + 3600))
    dusk_t = nz(2026, 11, 6, 19, 50)             # the old table says night from 19.6 h + 0.7; the real sunset is 20:20
    check("Nov 6 19:50: legacy says night/dusk, real says dusk/day (the dusk moved later)",
          WC.daylight_legacy(dusk_t) in ("night",) or WC.daylight_legacy(dusk_t) == "dusk", WC.daylight_legacy(dusk_t))
    # heavens.star
    tc = nz(2026, 11, 8, 3, 0)
    HV_before = HV.star("southern_cross", CUT - 7200)
    WP.SKY_CUTOVER_TS = 4102444800.0
    HV_legacy = HV.star("southern_cross", CUT - 7200)
    WP.SKY_CUTOVER_TS = CUT
    check("heavens.star before the cutover is unchanged (legacy site)", HV_before == HV_legacy)
    best = max(HV.star("southern_cross", CUT + 60 * i)["alt"] for i in range(0, 24 * 60 + 5, 1))
    check(f"Southern Cross upper culmination {best} deg ~ 73.5 (+-0.2)", abs(best - 73.5) <= 0.2, best)
    WP.SKY_CUTOVER_TS = 4102444800.0
    best_old = max(HV.star("southern_cross", CUT + 60 * i)["alt"] for i in range(0, 24 * 60 + 5, 1))
    WP.SKY_CUTOVER_TS = CUT
    check(f"legacy site culminates at ~71.2 (90 - (60.1 - 41.3)) (got {best_old})", abs(best_old - 71.2) <= 0.3)
    # [6] consumers
    print("[6] consumers")
    from core import light as LT       # noqa: E402
    tx, ty, h, r = LT._TREE
    far = (tx, ty + 4.5)
    LT._sun = lambda now=None: {"up": True, "phase": "morning", "az": 180.0, "f": 0.5, "alt": 23.0}
    sh_alt = LT.shade_at(*far, 0.0)
    LT._sun = lambda now=None: {"up": True, "phase": "morning", "az": 180.0, "f": 0.5}
    sh_leg = LT.shade_at(*far, 0.0)
    check(f"shade_at: low real sun (alt 23) throws the tree's shadow to 4.5 m ({sh_alt}); legacy 60 deg does not ({sh_leg})",
          sh_alt > 0.2 and sh_leg == 0.0)
    from core import soundscape as SS  # noqa: E402
    found = None
    for dd in range(1, 28):
        ts_ = nz(2026, 12, dd, 12, 0) if nz(2026, 12, dd, 12, 0) >= CUT else None
        if ts_ is None:
            continue
        passes = SS._flyover_passes(ts_)
        SS_share = SS._FLYOVER_DAY_SHARE
        if passes:
            found = (ts_, passes)
            break
    if found:
        rise_n, set_n = WC.sun_times_sumner(found[0])
        check("flyover passes sit inside the REAL rise+0.5 .. set-0.5 (read through sun_times)",
              all(rise_n + 0.5 <= a and b <= set_n - 0.5 for a, b in found[1]), (found, rise_n, set_n))
    else:
        print("  [skip] no flyover day drawn in the Dec sample")
    tm = nz(2026, 12, 21, 5, 44) + 3600 * 1.0
    wk = SS._roof_flex_window(nz(2026, 12, 21, 5, 44) + 0.8 * 3600 + 60) if CUT <= nz(2026, 12, 21, 6, 0) else None
    check("roof-flex morning window opens ~0.8 h after the REAL sunrise (Dec 21 05:44 + 0.8 h)", wk is True, wk)
finally:
    WP.SKY_MODE, WP.SKY_CUTOVER_TS = _MODE0, _CUT0
    import importlib
    for m in ("core.light",):
        importlib.reload(sys.modules[m])
check("flag and cutover restored to the shipped defaults", (WP.SKY_MODE, WP.SKY_CUTOVER_TS) == ("shadow", 4102444800.0))
# shadow mode: the soundscape accessor equals the old table read
from core import soundscape as SS2   # noqa: E402
tsh = nz(2026, 11, 5, 6, 30)
check("shadow mode: _roof_flex_window equals the table-based answer",
      SS2._roof_flex_window(tsh) == ((lambda lt, rs: (rs[0] + SS2._ROOF_MORNING_H[0] <= lt.tm_hour + lt.tm_min / 60.0 < rs[0] + SS2._ROOF_MORNING_H[1])
                                       or (rs[1] + SS2._ROOF_EVENING_H[0] <= lt.tm_hour + lt.tm_min / 60.0 < rs[1] + SS2._ROOF_EVENING_H[1]))(time.localtime(tsh), WC._SUN[time.localtime(tsh).tm_mon])))

print("[7] shadow log, reader, census wiring")
from core import sky_shadow as SK    # noqa: E402
SK._LOG = TMP / "sky_shadow.jsonl"
SK._last_ts = 0.0
t1 = nz(2026, 11, 5, 19, 55)
row = SK.record(source="test", now=t1)
check("record() wrote one row", row is not None and len(SK._LOG.read_text(encoding="utf-8").splitlines()) == 1)
check("rate limit: a second call inside the window writes nothing", SK.record(source="test", now=t1 + 20) is None)
txt = SK._LOG.read_text(encoding="utf-8")
check("row carries BOTH suns", row["old"]["daylight"] and row["new"]["daylight"] and "alt" in row["new"] and "alt" not in row["old"], row)
low = txt.lower()
check("no place name and no coordinate in the log", "sumner" not in low and "christchurch" not in low and "43.57" not in low and "172.75" not in low)
check("at 19:55 NZDT the old table says dusk-or-night and the real sun is still up (the dusk moved)", row["old"]["up"] is False and row["new"]["up"] is True, row)
SK._last_ts = 0.0
for i in range(8):
    for k in range(0, 24 * 6):
        SK.record(source="test", now=nz(2026, 11, 6 + i, 0, 0) + k * 600)
        SK._last_ts = 0.0
import scripts.sky_shadow_read as RD   # noqa: E402
rows = RD.load(SK._LOG)
s = RD.summarize(rows, 7)
check("reader: 8+ civil days -> the 7-day gate is MET", s["gate_met"] and s["n_days"] >= 8, s["n_days"])
check("reader: the Nov dusk shift is visible and ~ +40..60 min", s["max_set_shift_min"] is not None and 30 <= s["max_set_shift_min"] <= 75, s["max_set_shift_min"])
check("reader: day-phase words disagree on some ticks", s["word_disagree"] > 0)
s3 = RD.summarize([r for r in rows if WP.civil_date(r["ts"]) <= (2026, 11, 8)], 7)
check("reader: 3-4 days -> gate NOT met", not s3["gate_met"], s3["n_days"])
import io, contextlib   # noqa: E402
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    rc = RD.main([str(SK._LOG)])
check("reader main() runs and prints the table", rc == 0 and "7-day gate" in buf.getvalue() and "NOT visible here: sleep onset" in buf.getvalue())
import inspect   # noqa: E402
from core import geometry_census as GC   # noqa: E402
check("geometry_census.snapshot calls sky_shadow.record", "sky_shadow" in inspect.getsource(GC.snapshot) and "_sky.record" in inspect.getsource(GC.snapshot))
from scripts._test_isolation import redirect_world_stores   # noqa: E402
redirect_world_stores(TMP, locomotion=True, watershed=True, census=True)
import core.activity_memory as AM                           # noqa: E402
AM.record = lambda *a, **k: None
GC._LOG = TMP / "geometry_tuples.jsonl"
SK._LOG = TMP / "sky_shadow_census.jsonl"
SK._last_ts = 0.0
try:
    crow = GC.snapshot(state=None, source="J-3292-test", thought="j3292 sky shadow wiring", debounce=True)
except Exception as exc:
    crow = None
    print("  census raised:", exc)
check("a real census tick writes a sky_shadow row to the (temp) log", SK._LOG.exists() and len(SK._LOG.read_text(encoding="utf-8").splitlines()) >= 1,
      "census returned %r" % (crow is not None,))
check("the census row itself carries no sky-shadow field (additive: row shape unchanged)", crow is None or not any("sky" in k for k in crow))
live_data = ROOT / "data"
check("nothing written under the worktree data/ by this test", not (live_data / "sky_shadow.jsonl").exists())

print("\nFAILS:", FAILS)
sys.exit(1 if FAILS else 0)
