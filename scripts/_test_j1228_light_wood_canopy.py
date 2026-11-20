"""Regression for J-1228 / F-1725 (2026-09-23): core/light.py field_at()'s night-time moon term must
be dimmed by the SAME tree-canopy factor wood's own sky term already applies, not added flat.

THE BUG (found and fixed this job): field_at() dims wood's sky term by 0.3 (`v = sky * 0.3`, a real
forest canopy blocking most daylight) but the moon term added later in the same function was a flat
`v += 0.12 * heavens.moon(now)["illum"]` for ANY of ("garden", "shore", "wood") -- so at night, wood
got the SAME full moonlight as open garden/shore, physically backwards (a canopy blocks moonlight
reaching the ground too, not just sunlight). This is what caused wood's December
day(0.300) > dusk(0.026) >= night(0.042) invariant to FAIL (dusk < night). The fix: a single
`canopy = 0.3 if place == "wood" else 1.0` now scales both the sky term (unchanged value, same 0.3)
and the moon term (`v += 0.12 * moon_illum * canopy`), so they can no longer drift apart.

This checks the MECHANISM for wood, confirms shore is genuinely unaffected (no canopy there, verified
rather than assumed per this job's own briefing), and documents (without failing on) the much smaller,
separately-diagnosed garden Jul-Oct residual (a twilight-model sine/flat-constant discontinuity near
real sunset, NOT a canopy bug -- see this job's own findings-log entry for the read).

ISOLATED as scripts/life_smoke.py and scripts/_test_j1212_light_moon_now.py are: geometry_census._DATA
and sensorium's own state file are redirected into a temp dir before any read; the live data/ is never
touched (field_at() itself performs no writes either way).
    python scripts/_test_j1228_light_wood_canopy.py
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


TMP = Path(tempfile.mkdtemp(prefix="j1228_light_wood_canopy_"))
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


print("\n-- [1] wood, December: the reported case (F-1725's own repro command)")
w_day = LT.field_at("wood", None, at(12, 13))
w_dusk = LT.field_at("wood", None, at(12, 20))
w_night = LT.field_at("wood", None, at(12, 23))
print(f"     day={w_day} dusk={w_dusk} night={w_night}")
check("wood: day > dusk >= night (was FAILING before this fix: 0.3 > 0.026 >= 0.042 is False)",
      w_day > w_dusk >= w_night, f"day={w_day} dusk={w_dusk} night={w_night}")

print("\n-- [2] wood's night moon contribution is scaled by the SAME 0.3 canopy factor as its sky term")
moon_t = at(12, 23)
illum = float(HV.moon(moon_t)["illum"])
expected_wood_night = round(0.3 * illum * 0.3, 3)     # sky*canopy (~0, sun long down) + 0.12*illum*canopy
# at 23:00 in December the sun term is 0 (well past dusk window), so night == 0.12*illum*canopy exactly
expected_wood_night = round(0.12 * illum * 0.3, 3)
check("wood night value == round(0.12 * moon_illum * 0.3, 3) -- moon term IS canopy-scaled",
      w_night == expected_wood_night, f"got {w_night}, expected {expected_wood_night} (illum={illum})")

print("\n-- [3] shore, December: spot-checked fine by F-1725, verified (not assumed) still fine post-fix")
s_day = LT.field_at("shore", None, at(12, 13))
s_dusk = LT.field_at("shore", None, at(12, 20))
s_night = LT.field_at("shore", None, at(12, 23))
print(f"     day={s_day} dusk={s_dusk} night={s_night}")
check("shore: day > dusk >= night (no canopy factor exists for shore -- this must be untouched by the fix)",
      s_day > s_dusk >= s_night, f"day={s_day} dusk={s_dusk} night={s_night}")
expected_shore_night = round(0.12 * illum, 3)   # canopy=1.0 for shore -- flat moon term, unchanged behavior
check("shore night value == round(0.12 * moon_illum, 3) -- moon term NOT scaled for shore (canopy=1.0)",
      s_night == expected_shore_night, f"got {s_night}, expected {expected_shore_night}")

print("\n-- [4] garden unaffected by this fix (canopy=1.0 there too; sanity against regressing J-1212's own fix)")
g_day = LT.field_at("garden", None, at(12, 13))
g_dusk = LT.field_at("garden", None, at(12, 20))
g_night = LT.field_at("garden", None, at(12, 23))
check("garden December: day > dusk >= night (J-1212's own invariant, must still hold)",
      g_day > g_dusk >= g_night, f"day={g_day} dusk={g_dusk} night={g_night}")

print("\n-- [5] documented, NOT asserted: garden's much smaller Jul-Oct residual (twilight-model shape,")
print("        not a canopy bug -- see this job's findings-log entry for the read; reported for visibility only)")
for m in (7, 8, 9, 10):
    d = LT.field_at("garden", None, at(m, 20))
    n = LT.field_at("garden", None, at(m, 23))
    print(f"     month={m:2d} dusk={d} night={n} inverted={d < n} (magnitude {round(n - d, 3) if n > d else 0.0})")

print(f"\n{'ALL OK' if not FAILS else str(FAILS) + ' FAILED'}")
sys.exit(1 if FAILS else 0)
