"""J-3293 (2026-11-05, D-0655, design review J-3264 section 2 step 5): Phase 1b, the real moon at the real site.

  [1] SHADOW MODE IS INVISIBLE: with SKY_MODE "shadow" (the default) moon() equals the ORIGINAL body (copied verbatim
      below as the reference) over a 3-year grid; moon_legacy() equals it too.
  [2] PRE-REGISTERED, PHASES: the 25 new/full moons the US Naval Observatory publishes for 2026 (USNO Astronomical
      Applications API, aa.usno.navy.mil/api/moon/phases/year?year=2026, fetched 2026-11-05, UTC, minute resolution)
      vs the code's elongation crossings. Pass: every event within 2 h; stop if any over 6 h. (Measured: see output.)
      Cross-check, an independent algorithm: the same events from Meeus ch.49 (the design's scratch script, re-derived
      here from the principal terms) vs the code, within 2 h.
  [3] PRE-REGISTERED, MOONRISE/SET: three dates against the same USNO API (rstt/oneday, coords -43.57,172.75, upper
      limb, standard refraction): 2026-03-20, 2026-06-21, 2026-11-05. Pass: within 15 min; stop if over 6 h.
  [4] illumination vs USNO's fracillum at local noon on those dates (41% / 1% / 19%), loose tolerance.
  [5] cutover: SKY_MODE "live" + SKY_CUTOVER_TS: t < cutover is bit-identical legacy, t >= cutover is moon_true with
      `alt`; the contract keys are the legacy ones plus alt; up/rise/set/arc_f agree with each other.
  [6] consumers: world_clock._spring_factor follows the real illumination after the cutover (1 at a real new/full moon,
      ~0 at the quarters); tide() and heavens.sky() still run; the stars are untouched by this change.
  [7] cost: moon_true uncached under 2 ms mean, so moon() inside tide() is harmless.
  [8] shadow log: a row carries the "moon" key (old + real), no place name or coordinate; the reader summarises it
      and still reads a row from before J-3293 (no moon key).

ISOLATED: no DB is opened and nothing under data/ is written (every log path is redirected to a temp dir first).
`import core` comes BEFORE everything and the module path is asserted to be inside this worktree.
    python scripts/_test_moon_true_J-3293.py
"""
from __future__ import annotations

import calendar
import datetime as dt
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

from core import heavens as HV        # noqa: E402
from core import world_place as WP    # noqa: E402
from core import world_clock as WC    # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="J-3293_moon_"))
_MODE0, _CUT0 = WP.SKY_MODE, WP.SKY_CUTOVER_TS


def nz(y, mo, d, h=0, mi=0, off=None):
    base = calendar.timegm((y, mo, d, h, mi, 0))
    return base - (WP.nz_offset_hours(base - 13 * 3600) if off is None else off) * 3600.0


# ── [1] shadow mode invisible ────────────────────────────────────────────────────────────────────────────
print("[1] shadow mode is invisible")


def _orig_moon(t):
    """The pre-J-3293 heavens.moon body, verbatim."""
    age_d = ((t - HV._NEW_MOON_EPOCH) / 86400.0) % HV._SYNODIC_D
    frac = age_d / HV._SYNODIC_D
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
    try:
        from core.world_clock import sun as _sun
        s = _sun(t - frac * 86400.0)
        up, az, f = s["up"], s["az"], s["f"]
    except Exception:
        up, az, f = False, None, None
    return {"phase": word, "illum": illum, "age_d": round(age_d, 1), "up": up, "az": az, "arc_f": f}


check("default mode is shadow and the cutover is not yet", WP.SKY_MODE == "shadow" and WP.SKY_CUTOVER_TS > time.time() + 365 * 86400)
bad = 0
n = 0
t = nz(2025, 1, 1)
while t < nz(2028, 1, 1):
    n += 1
    if not (HV.moon(t) == _orig_moon(t) == HV.moon_legacy(t)):
        bad += 1
    t += 7919.0                                  # ~2.2 h, coprime-ish to the day
check("moon() == legacy == original body over 3 years (%d samples)" % n, bad == 0, "%d differ" % bad)
check("moon() with no argument still answers", set(HV.moon()) == {"phase", "illum", "age_d", "up", "az", "arc_f"})

# ── [2] phases vs USNO ───────────────────────────────────────────────────────────────────────────────────
print("[2] new/full moons 2026 vs the published USNO table")
USNO = """1 3 10:03 F|1 18 19:52 N|2 1 22:09 F|2 17 12:01 N|3 3 11:38 F|3 19 01:23 N|4 2 02:12 F|4 17 11:52 N|5 1 17:23 F
5 16 20:01 N|5 31 08:45 F|6 15 02:54 N|6 29 23:56 F|7 14 09:43 N|7 29 14:36 F|8 12 17:37 N|8 28 04:18 F|9 11 03:27 N
9 26 16:49 F|10 10 15:50 N|10 26 04:12 F|11 9 07:02 N|11 24 14:53 F|12 9 00:52 N|12 24 01:28 F""".replace("\n", "|").split("|")
events = []
for ln in USNO:
    mo, d, hm, k = ln.split()
    h, mi = hm.split(":")
    events.append((calendar.timegm((2026, int(mo), int(d), int(h), int(mi), 0)), k))
check("25 published events loaded", len(events) == 25, len(events))


def crossing(t0, tgt):
    a, b = t0 - 6 * 3600, t0 + 6 * 3600
    f = lambda x: ((HV.moon_elongation(x) - tgt + 180.0) % 360.0) - 180.0
    for _ in range(40):
        c = 0.5 * (a + b)
        if f(c) > 0:
            b = c
        else:
            a = c
    return 0.5 * (a + b)


errs = [(crossing(t0, 0.0 if k == "N" else 180.0) - t0) / 60.0 for t0, k in events]
print("     code - USNO, minutes: max abs %.1f, mean abs %.1f (USNO prints whole minutes)" % (
    max(abs(e) for e in errs), sum(abs(e) for e in errs) / len(errs)))
check("pre-registered: every one of the 25 events within 2 h", max(abs(e) for e in errs) < 120.0, max(abs(e) for e in errs))
check("stop condition not hit: none over 6 h", max(abs(e) for e in errs) < 360.0)
check("tighter than pre-registered: within 5 min", max(abs(e) for e in errs) < 5.0, max(abs(e) for e in errs))


def meeus49(k, full):
    k = k + (0.5 if full else 0.0)
    T = k / 1236.85
    jde = 2451550.09766 + 29.530588861 * k + 0.00015437 * T ** 2
    E = 1 - 0.002516 * T - 0.0000074 * T ** 2
    M = math.radians((2.5534 + 29.10535670 * k) % 360)
    Mp = math.radians((201.5643 + 385.81693528 * k) % 360)
    F = math.radians((160.7108 + 390.67050284 * k) % 360)
    if not full:
        c = (-0.40720 * math.sin(Mp) + 0.17241 * E * math.sin(M) + 0.01608 * math.sin(2 * Mp) + 0.01039 * math.sin(2 * F)
             + 0.00739 * E * math.sin(Mp - M) - 0.00514 * E * math.sin(Mp + M) + 0.00208 * E * E * math.sin(2 * M))
    else:
        c = (-0.40614 * math.sin(Mp) + 0.17302 * E * math.sin(M) + 0.01614 * math.sin(2 * Mp) + 0.01043 * math.sin(2 * F)
             + 0.00734 * E * math.sin(Mp - M) - 0.00515 * E * math.sin(Mp + M) + 0.00209 * E * E * math.sin(2 * M))
    return (jde + c - 2440587.5) * 86400.0 - 69.2          # TT -> UT


k0 = round((2026 - 2000) * 12.3685)
cross_err = []
for k in range(k0, k0 + 14):
    for full in (False, True):
        t49 = meeus49(k, full)
        if dt.datetime.fromtimestamp(t49, dt.timezone.utc).year == 2026:
            cross_err.append((crossing(t49, 180.0 if full else 0.0) - t49) / 60.0)
print("     code - Meeus ch.49 (independent series), minutes: max abs %.1f over %d events" % (max(abs(e) for e in cross_err), len(cross_err)))
check("cross-check vs Meeus ch.49: every 2026 event within 2 h", len(cross_err) >= 24 and max(abs(e) for e in cross_err) < 120.0)

# ── [3] moonrise / moonset vs USNO ───────────────────────────────────────────────────────────────────────
print("[3] moonrise/set vs the published USNO table (coords -43.57,172.75)")
RS = [((2026, 3, 20), 13, "08:33", "19:55"), ((2026, 6, 21), 12, "12:01", None), ((2026, 11, 5), 13, "03:57", "16:02")]
worst = 0.0
for ymd, off, rise_s, set_s in RS:
    y, mo, d = ymd
    mt = HV.moon_times(nz(y, mo, d, 12, 0, off=off))
    for lab, want, got in (("rise", rise_s, mt["rise"]), ("set", set_s, mt["set"])):
        if want is None:
            continue
        h, mi = map(int, want.split(":"))
        w = nz(y, mo, d, h, mi, off=off)
        e = None if got is None else (got - w) / 60.0
        print("     %s %s: USNO %s, code %s, diff %s min" % (ymd, lab, want,
              "none" if got is None else dt.datetime.fromtimestamp(got + off * 3600, dt.timezone.utc).strftime("%H:%M"),
              "n/a" if e is None else "%+.1f" % e))
        check("%s %s found" % (ymd, lab), got is not None)
        if e is not None:
            worst = max(worst, abs(e))
            check("%s moon%s within 15 min of USNO" % (ymd, lab), abs(e) < 15.0, e)
    if set_s is None:
        check("%s: USNO lists no moonset that civil day and neither does the code" % (ymd,), mt["set"] is None, mt)
check("stop condition not hit: none over 6 h", worst < 360.0)

# ── [4] illumination vs USNO fracillum ───────────────────────────────────────────────────────────────────
print("[4] illumination at local noon vs USNO fracillum")
for ymd, off, want in (((2026, 6, 21), 12, 0.41), ((2026, 3, 20), 13, 0.01), ((2026, 11, 5), 13, 0.19)):
    got = HV.moon_true(nz(*ymd, 12, 0, off=off))["illum"]
    check("%s illum %.3f vs USNO %.2f (+-0.05)" % (ymd, got, want), abs(got - want) <= 0.05, got)

# ── [5] cutover ──────────────────────────────────────────────────────────────────────────────────────────
print("[5] cutover")
CUT = nz(2026, 11, 20, 0, 0)
WP.SKY_MODE, WP.SKY_CUTOVER_TS = "live", CUT
try:
    tb = [CUT - 86400.0 * k - 777.0 for k in (1, 5, 40, 400)]
    check("t < cutover: moon() is the legacy answer, bit for bit", all(HV.moon(t) == _orig_moon(t) for t in tb))
    ta = nz(2026, 11, 25, 2, 50)                     # an hour before the real full moon (14:53 UTC on 11-24 = 03:53 NZDT 11-25)
    m = HV.moon(ta)
    check("t >= cutover: moon() is moon_true (has alt)", "alt" in m and m == HV.moon_true(ta), m)
    check("contract keys = the legacy keys + alt", set(m) == {"phase", "illum", "age_d", "up", "az", "arc_f", "alt"}, set(m))
    check("a night an hour before the real full moon: illum > 0.99 and 'full'", m["illum"] > 0.99 and m["phase"] == "full", m)
    check("moon_legacy() stays callable after the cutover and has no alt", "alt" not in HV.moon_legacy(ta))
    # up / rise / set / arc_f agree
    mt = HV.moon_times(nz(2026, 11, 5, 12, 0))
    r, s_ = mt["rise"], mt["set"]
    check("just after moonrise up, just before it down", HV.moon_true(r + 120)["up"] and not HV.moon_true(r - 120)["up"])
    check("just before moonset up, just after it down", HV.moon_true(s_ - 120)["up"] and not HV.moon_true(s_ + 120)["up"])
    fs = [HV.moon_true(r + (s_ - r) * q)["arc_f"] for q in (0.1, 0.3, 0.5, 0.7, 0.9)]
    check("arc_f runs 0..1 and rises along the arc", all(f is not None for f in fs) and fs == sorted(fs) and 0.0 <= fs[0] <= fs[-1] <= 1.0
          and abs(fs[2] - 0.5) < 0.02, fs)
    dn = HV.moon_true(s_ + 1800)
    check("moon down: az and arc_f None, alt below the horizon", dn["az"] is None and dn["arc_f"] is None and dn["alt"] < 0.5, dn)
    up_ = HV.moon_true(0.5 * (r + s_))
    check("moon up: az in 0..360 and alt > 0", up_["az"] is not None and 0.0 <= up_["az"] < 360.0 and up_["alt"] > 0.0, up_)
    # the moon crosses the NORTH (southern-hemisphere site): at transit the azimuth is ~0/360
    tr = max((HV.moon_true(r + (s_ - r) * q / 100.0) for q in range(101)), key=lambda x: x["alt"])
    check("highest point of the arc is in the north (az within 25 deg of 0)", min(tr["az"], 360.0 - tr["az"]) < 25.0, tr)
    # DST days
    for ymd in ((2026, 9, 27), (2026, 4, 5), (2026, 9, 26)):
        ev = HV._moon_day_events(ymd)
        ok = all(ev[i][1] != ev[i + 1][1] for i in range(len(ev) - 1))
        check("%s (a DST edge): events alternate rise/set, %d found" % (ymd, len(ev)), ok and len(ev) <= 2, ev)
    # 25 hours / year: a rise happens on most days; count over a year
    days = [HV._moon_day_events(HV._dt_shift(2026, 1, 1, i)) for i in range(0, 365, 3)]
    check("a year of sample days: 0..2 events each, some days have a rise and some a set", all(len(e) <= 2 for e in days)
          and any(any(x[1] == "rise" for x in e) for e in days) and any(any(x[1] == "set" for x in e) for e in days))
    # ── [6] consumers
    print("[6] consumers")
    sf_new = WC._spring_factor(nz(2026, 11, 9, 18, 0))              # the real new moon was 20:02 NZDT on 11-09
    sf_q = WC._spring_factor(nz(2026, 11, 17, 12, 0))               # first quarter 11-17 11:48 UTC
    check("spring factor ~1 at the real new moon, ~0 at the real quarter", sf_new > 0.97 and sf_q < 0.08, (sf_new, sf_q))
    check("tide() runs after the cutover", set(WC.tide(ta)) >= {"level", "rising", "word", "spring_factor"})
    sk = HV.sky(ta)
    check("heavens.sky() runs after the cutover and carries the real moon", "alt" in sk["moon"] and isinstance(sk["stars_up"], dict))
    cross = HV.star("southern_cross", nz(2026, 11, 25, 21, 0))
    check("stars untouched by this change (Cross still computed)", cross is not None and cross["alt"] > 0)
finally:
    WP.SKY_MODE, WP.SKY_CUTOVER_TS = _MODE0, _CUT0
check("mode restored to shadow", WP.SKY_MODE == "shadow")

# ── [7] cost ─────────────────────────────────────────────────────────────────────────────────────────────
print("[7] cost")
t0 = time.perf_counter()
for i in range(300):
    HV._moon_cache.clear()
    HV.moon_true(1.79e9 + i * 1013.0)
per = (time.perf_counter() - t0) / 300 * 1000.0
print("     moon_true uncached: %.3f ms/call (day-event caches warm for ~1 day per sample)" % per)
check("moon_true uncached under 2 ms mean", per < 2.0, per)
HV._MOON_EVT_CACHE.clear()
t0 = time.perf_counter()
HV._moon_day_events((2026, 11, 5))
cold = (time.perf_counter() - t0) * 1000.0
check("a cold moon day-scan under 50 ms (once per civil date)", cold < 50.0, cold)

# ── [8] shadow log ───────────────────────────────────────────────────────────────────────────────────────
print("[8] shadow log + reader")
from core import sky_shadow as SK    # noqa: E402
SK._LOG = TMP / "sky_shadow.jsonl"
SK._last_ts = 0.0
row = SK.record(source="test", now=nz(2026, 11, 6, 21, 0))
check("record() wrote a row with the moon key (old + real)", row is not None and isinstance(row.get("moon"), dict)
      and "alt" in row["moon"]["new"] and "alt" not in row["moon"]["old"] and "rise_h" in row["moon"]["new"], row)
low = SK._LOG.read_text(encoding="utf-8").lower()
check("no place name and no coordinate in the log", "sumner" not in low and "christchurch" not in low and "43.57" not in low and "172.75" not in low)
check("the sun half of the row is unchanged", {"old", "new", "ts", "mode", "live", "tz_agree"} <= set(row))
for i in range(8):
    for k in range(0, 24 * 6):
        SK._last_ts = 0.0
        SK.record(source="test", now=nz(2026, 11, 6 + i, 0, 0) + k * 600)
legacy_row = json.loads(json.dumps(row))
legacy_row.pop("moon")
with open(SK._LOG, "a", encoding="utf-8") as f:
    f.write(json.dumps(legacy_row) + "\n")
import scripts.sky_shadow_read as RD   # noqa: E402
s = RD.summarize(RD.load(SK._LOG), 7)
check("reader: moon rows counted (the pre-J-3293 row is skipped, not fatal)", s["moon_rows"] >= 8 * 24 * 6 and s["moon_rows"] < s["n_rows"], (s["moon_rows"], s["n_rows"]))
check("reader: the old moon clock disagrees with the real one somewhere (phase word or up/down)", s["moon_word_disagree"] + s["moon_up_disagree"] > 0, s)
check("reader: illumination difference reported", s["moon_illum_diff_max"] is not None and s["moon_illum_diff_max"] >= 0.0)
import contextlib, io   # noqa: E402
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    rc = RD.main([str(SK._LOG)])
check("reader main() prints a moon line", rc == 0 and "moon (old synodic/lagged-sun vs real)" in buf.getvalue(), buf.getvalue()[-400:])
check("nothing written under the worktree data/ by this test", not (ROOT / "data" / "sky_shadow.jsonl").exists())

print("\nFAILS:", FAILS)
sys.exit(1 if FAILS else 0)
