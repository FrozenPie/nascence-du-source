"""Regression for J-1212 / F-1711 (2026-09-22): core/light.py field_at()'s night-time moon term must
be a pure function of the `now` it is given, like the sun term just above it (J-0510's own rule) --
not of real wall-clock time.

THE BUG (found and fixed this job): field_at() got moon_illum via
`geometry_census.peek().get("moon_illum")`. peek() -> _place_weather() calls `heavens.moon()` with
NO time argument, so it always reads the REAL current moon phase, no matter what simulated `now`
field_at() was passed. scripts/life_smoke.py's own deterministic check (fixed December timestamps,
"day > dusk >= night") failed because the December-evening "dusk" glow (a real, low, correctly
`now`-scoped value) was being compared against a "night" value containing TODAY's real moon
illumination glued onto a December date -- on 2026-09-22 that real moon happened to be bright enough
(illum ~0.8) to push night (0.12*0.8=~0.10) above dusk (0.088). The fix: field_at() now calls
`heavens.moon(now)["illum"]` directly, the same `now`-threading `_sun(now)` already used.

This checks the MECHANISM, not just the one symptom date (a fixed-illum assertion tied to today's
real moon would itself rot the day real time moved on):
  [1] life_smoke.py's own December check (day(13:00) > dusk(20:00) >= night(23:00), garden, clear)
      now holds -- the reported failure, reproduced then fixed.
  [2] field_at()'s night-time moon contribution for a *simulated* `now` exactly matches
      heavens.moon(now)["illum"] (the value FOR THAT SIMULATED DATE), for two dates ~half a synodic
      month apart (different phases) -- proving the term is a function of `now`, not of when this
      test happens to run. If field_at() ever again routes this through a real-wall-clock-only
      helper, these two simulated dates will almost always both mismatch (the two live-clock reads
      would be identical to each other, since real time barely moves between the two field_at()
      calls, while the two SIMULATED dates deliberately are not).
  [3] "up" (daylight) hours never add a moon term regardless of weather (the existing `not s.get("up")`
      guard is unchanged by this fix).

ISOLATED as scripts/life_smoke.py is: geometry_census._DATA and sensorium's own state file are
redirected into a temp dir before any read; the live data/ is never touched (field_at() itself
performs no writes either way).
    python scripts/_test_j1212_light_moon_now.py
"""
from __future__ import annotations

import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

FAILS = 0


def check(name, cond, detail=""):
    global FAILS
    FAILS += (not cond)
    print(f"  [{'ok ' if cond else 'FAIL'}] {name}" + (f"   ({detail})" if detail and not cond else ""))


TMP = Path(tempfile.mkdtemp(prefix="j1212_light_moon_now_"))
print("isolated store dir:", TMP)

from core import geometry_census as GC                   # noqa: E402
GC._DATA = TMP                                            # never read live room_state.json etc.
from core import light as LT                              # noqa: E402
from core import sensorium as S                           # noqa: E402
from core import heavens as HV                             # noqa: E402
S._STATE_F = TMP / "room_state.json"

S.state.update({"weather": "clear", "wind": "breeze", "fire": "out", "location": "garden"})


def at(month: int, hour: int, day: int = 15, year: int = 2026) -> float:
    return time.mktime((year, month, day, hour, 0, 0, 0, 0, -1))


print("\n-- [1] the reported case: life_smoke.py's own December day/dusk/night check (garden, clear)")
day = LT.field_at("garden", None, at(12, 13))
dusk = LT.field_at("garden", None, at(12, 20))
night = LT.field_at("garden", None, at(12, 23))
print(f"     day={day} dusk={dusk} night={night}")
check("day > dusk >= night (the exact life_smoke.py [3] invariant)", day > dusk >= night, f"day={day} dusk={dusk} night={night}")
check("dusk matches the reported/confirmed pre-existing value (0.088, unaffected by this fix)", dusk == 0.088, dusk)

print("\n-- [2] the moon term is a pure function of `now`, not of real wall-clock time")
# two December nights, ~15 days apart -> roughly opposite points in the 29.53 d synodic cycle, so
# their moon illum is very unlikely to coincidentally match each other OR today's real illum.
t_a = at(12, 23, day=1)
t_b = at(12, 23, day=16)
illum_a, illum_b = HV.moon(t_a)["illum"], HV.moon(t_b)["illum"]
val_a, val_b = LT.field_at("garden", None, t_a), LT.field_at("garden", None, t_b)
print(f"     t_a (Dec 1, 23:00): heavens.moon(t_a).illum={illum_a}  field_at={val_a}")
print(f"     t_b (Dec 16,23:00): heavens.moon(t_b).illum={illum_b}  field_at={val_b}")
check("the two dates land on genuinely different lunar phases (fixture sanity)", abs(illum_a - illum_b) > 0.08, f"{illum_a} vs {illum_b}")
check("field_at(t_a) exactly equals round(0.12 * heavens.moon(t_a).illum, 3) -- scoped to t_a, not real time",
      val_a == round(0.12 * illum_a, 3), f"got {val_a}, expected {round(0.12 * illum_a, 3)}")
check("field_at(t_b) exactly equals round(0.12 * heavens.moon(t_b).illum, 3) -- scoped to t_b, not real time",
      val_b == round(0.12 * illum_b, 3), f"got {val_b}, expected {round(0.12 * illum_b, 3)}")
check("field_at(t_a) != field_at(t_b) -- the term actually tracks the simulated date (this is what the old "
      "geometry_census.peek()-based code could never do: both calls happen at the same real moment, so a "
      "real-wall-clock-only read would give the SAME value for both)",
      val_a != val_b, f"{val_a} == {val_b}")

print("\n-- [3] no moon term while the sun is up, regardless of weather (existing guard, unchanged)")
noon = LT.field_at("garden", None, at(12, 13))
check("full daylight is unaffected (sanity: this fix only touches the not-up branch)", noon == 1.0, noon)

print(f"\n{'ALL OK' if not FAILS else str(FAILS) + ' FAILED'}")
sys.exit(1 if FAILS else 0)
