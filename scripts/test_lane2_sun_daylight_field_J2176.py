"""
Test -- Lane 2 _prediction_field_ok counts daylight as a mapped field for sun topics (J-2176, D-0433 B).
Pure function, no I/O, no live data.
Run: python scripts/test_lane2_sun_daylight_field_J2176.py   (exit 0 = all passed)
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core import lane2  # noqa: E402

assert str(Path(lane2.__file__).resolve()).startswith(str(ROOT)), lane2.__file__

ok = lane2._prediction_field_ok
FAILS = []


def check(name, got, want):
    if got != want:
        FAILS.append(name)
    print(("PASS " if got == want else "FAIL ") + name, got)


for ph in ("night", "dusk", "dawn", "day"):
    check(f"sun claim, no sun_az, daylight={ph}", ok("I see the sun at 37 degrees", {"world_fields": [], "world": {"daylight": ph}}), True)
for t in ("sunset", "sunrise", "sunlight"):
    check(f"{t} night", ok(f"the {t} will come", {"world_fields": [], "world": {"daylight": "night"}}), True)
check("sun claim, daylight missing -> still field-absent", ok("the sun is up", {"world_fields": [], "world": {}}), False)
check("sun claim, daylight blank -> still field-absent", ok("the sun is up", {"world_fields": [], "world": {"daylight": "  "}}), False)
check("sun claim, no world -> field-absent", ok("the sun is up", {"world_fields": []}), False)
check("sun_az present unchanged", ok("the sun is up", {"world_fields": ["sun_az"], "world": {}}), True)
# other topics untouched by the daylight licence
check("moon night still field-absent", ok("the moon is bright", {"world_fields": [], "world": {"daylight": "night"}}), False)
check("fire night still field-absent", ok("the fire is lit", {"world_fields": [], "world": {"daylight": "night"}}), False)
check("no topic named -> fail-open", ok("something happens", {"world_fields": [], "world": {}}), True)
# mixed: sun + moon named, daylight present -> ok (any named topic judgeable, as before)
check("sun+moon night", ok("the sun and the moon", {"world_fields": [], "world": {"daylight": "night"}}), True)

print("FAILED: %s" % FAILS if FAILS else "ALL PASSED")
sys.exit(1 if FAILS else 0)
