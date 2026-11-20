"""J-3291 (2026-11-05, D-0655, F-3887 / F-3888): the study almanac no longer lies about the tide, and the
world_clock timezone hand rule is right.

  [1] look('almanac') never says 'morning'/'afternoon' high water (the old bug said 'morning' always), prints no
      invented hour, says the tide columns cannot be read, and keeps the moon-margin and 'near enough' lines.
  [2] the answer is the same at a spring tide and a neap tide (it reads no tide state, so it cannot lie by phase).
  [3] world_clock._nz_offset_hours: the DST edges for 2026/2027 (26 Sep 14:00 UTC, 4 Apr 14:00 UTC in 2026;
      25 Sep and 3 Apr 2027) and mid-winter / mid-summer.
  [4] world_clock.tz_check() returns the documented shape and reports a forced disagreement without raising.

ISOLATED like scripts/_test_candles_name_migration.py: world stores redirected to a temp dir before any write;
activity_memory.record stubbed; the live data/ is never read or written. `import core` comes BEFORE lab-style
helpers and the module path is asserted to be inside this worktree.
    python scripts/_test_J3291_almanac_tz.py
"""
from __future__ import annotations

import datetime as _dt
import sys
import tempfile
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

TMP = Path(tempfile.mkdtemp(prefix="J3291_almanac_"))
from core import sensorium as S                          # noqa: E402
from core import study_life as SL                        # noqa: E402
from core import provisions as PV                        # noqa: E402
from core import world_clock as WC                       # noqa: E402
from scripts._test_isolation import redirect_world_stores  # noqa: E402
redirect_world_stores(TMP, locomotion=True)
if hasattr(PV, "_d"):
    PV._d = None
import core.activity_memory as AM                        # noqa: E402
AM.record = lambda *a, **k: None
import core.sky as SKY                                   # noqa: E402  -- learn() writes garden_knowledge.json (fenced): stubbed
SKY.almanac_chart = lambda: ""

S.state.clear()
S.state.update({"weather": "clear", "wind": "calm", "fire": "out", "fire_fuel": 0.0, "last_event": 0,
                "location": "study", "garden": S._fresh_garden()})
st = SL._st()
for it in st["items"].values():
    it["carried"] = False
    it["place"] = "study"

print("[1] the almanac look")
out = SL.look("the almanac")
print("    ->", out[:260])
check("answers as the almanac", out.startswith("You take the almanac off its nail"))
check("no 'morning'/'afternoon' high-water claim", "morning" not in out and "afternoon" not in out and "high water" not in out)
check("no clock hour invented", not any(ch.isdigit() for ch in out.split("Last year's")[0]))
check("says the tide columns cannot be read", "too small" in out and "too faded" in out)
check("keeps the moon margin and the 'near enough' line", "moon's phase is drawn in the margin" in out and "near enough" in out)

print("[2] the same at spring and neap")
real_tide = WC.tide
try:
    for sf in (0.0, 1.0):
        WC.tide = (lambda t=None, _sf=sf: {"level": 0.5, "rising": True, "word": "coming in", "spring_factor": _sf})
        o2 = SL.look("the almanac")
        check(f"spring_factor={sf}: tide line identical", o2.split("Last year's")[0] == out.split("Last year's")[0])
finally:
    WC.tide = real_tide

print("[3] NZ DST hand rule")
def ts(*a):
    return _dt.datetime(*a, tzinfo=_dt.timezone.utc).timestamp()
cases = [((2026, 9, 26, 13, 59), 12), ((2026, 9, 26, 14, 0), 13), ((2026, 11, 5, 0, 0), 13),
         ((2026, 4, 4, 13, 59), 13), ((2026, 4, 4, 14, 0), 12), ((2026, 7, 1, 0, 0), 12), ((2026, 1, 15, 0, 0), 13),
         ((2027, 4, 3, 13, 59), 13), ((2027, 4, 3, 14, 0), 12), ((2027, 9, 25, 13, 59), 12), ((2027, 9, 25, 14, 0), 13),
         ((2026, 12, 31, 23, 59), 13)]
for args, exp in cases:
    got = WC._nz_offset_hours(ts(*args))
    check(f"{args} -> +{exp}", got == exp, f"got {got}")

print("[4] tz_check shape and forced disagreement")
r = WC.tz_check()
check("shape", set(r) == {"agree", "os_hours", "nz_hours"}, str(r))
print("    this machine:", r)
real_lt = WC.time.localtime
class _LT:  # a localtime result 5 hours off NZ
    tm_gmtoff = 0
WC.time.localtime = lambda t=None: _LT()
try:
    r2 = WC.tz_check(ts(2026, 11, 5))
    check("UTC machine reported as disagreeing", r2["agree"] is False and r2["os_hours"] == 0.0 and r2["nz_hours"] == 13, str(r2))
finally:
    WC.time.localtime = real_lt

print("\nFAILS:", FAILS)
sys.exit(1 if FAILS else 0)
