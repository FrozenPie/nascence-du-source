"""
Regression: J-3484 (D-0649 follow-up, J-3355; founder ruled yes, 8 lines, 2026-11-06): a COMPOSITE condition key for SCENE / EVENTS pools,
so the two night-wrong shore low_tide lines keep their tide gate and gain the day gate.

The fault (F-3628): two shore SCENE lines sat under "low_tide" and were night-wrong ("wet flats shine from the stream mouth to the
headland; every bird on the beach is working them", 4 night renders; "fresh shell glitters along the new tideline the sea has just left", 3).
A bare "day" key (the J-3258 move) would have dropped their tide gate. The fix is core/world_detail._cond_ok: a key with '+' holds only when
EVERY part is in the conds set; a key without '+' is the old `key in conds` test exactly. The two lines are now under "day+low_tide".
(The briefing's "9 lines" was a miscount; the sources name 8, torea excluded as not night-wrong: this job moves none of the other six.)

What this proves, PURE (only core.world_detail and the world_content_* modules are imported; the J-1694 render ledger is replaced by a
capture stub before anything draws; nothing under data/ is read or written, no DB is opened, no model is called):
  [1] _cond_ok    plain keys behave exactly as `key in conds`; composite keys need every part; empty / unknown parts fail closed
  [2] content     the two lines (wording byte-identical) are under "day+low_tide" only; the shore SCENE with them put back at their old
                  low_tide slots is byte-identical to HEAD f4a4e013 (digest pinned); garden / study / wood SCENE and all four EVENTS
                  byte-identical to HEAD; no other key gained or lost a line
  [3] gates       over every phase x weather x season x tide x wind: the pool scene_extra() builds contains the two lines iff the phase is
                  dawn / day / dusk AND tide is low or rising (the real tide_leaning set); never at night, never at high / falling / no tide
  [4] pool        exactly equals the old pool minus the two lines at night-with-low-tide, and equals the old pool exactly everywhere else
  [5] defeater    no night shore SCENE pool falls below 6 lines (D-0649), min / mean old -> new printed
  [6] ledger      the J-1694 render row names the composite key in conds at day + low tide, and not at night
  [7] events      event_extra() honours a composite key too (injected EVENTS, temp-only), and plain keys unchanged

Pins are point-in-time, taken from the unmodified files at HEAD f4a4e013 on 2026-11-06.

  python scripts/_test_j3484_composite_scene_key.py        # exit 0 = ALL OK
"""
from __future__ import annotations

import hashlib
import itertools
import json
import random
import sys
import types
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

LED_ROWS: list = []


def _record(location, place, conds, line, pool):
    LED_ROWS.append({"loc": location, "place": place, "conds": sorted(conds), "line": line, "pool": int(pool)})
    return False


_led = types.ModuleType("core.scene_extra_ledger")
_led.record = _record
sys.modules["core.scene_extra_ledger"] = _led

import core                                        # noqa: E402  (core BEFORE anything lab-ish)
core.scene_extra_ledger = _led
from core import world_detail as WD                # noqa: E402
from core import world_content_study as C_STUDY    # noqa: E402
from core import world_content_garden as C_GARDEN  # noqa: E402
from core import world_content_shore as C_SHORE    # noqa: E402
from core import world_content_wood as C_WOOD      # noqa: E402

_TREE = str(ROOT).lower()
assert str(Path(core.__file__).resolve()).lower().startswith(_TREE), f"core is not from the tree under test: {core.__file__}"
for _m in (WD, C_STUDY, C_GARDEN, C_SHORE, C_WOOD):
    assert str(Path(_m.__file__).resolve()).lower().startswith(_TREE), f"{_m.__name__} is not from the tree under test"

FAILS = 0


def check(cond: bool, label: str) -> None:
    global FAILS
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS += 1


def dig(obj) -> str:
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False).encode("utf-8")).hexdigest()


KEY = "day+low_tide"
L1 = "wet flats shine from the stream mouth to the headland; every bird on the beach is working them"
L2 = "fresh shell glitters along the new tideline the sea has just left"
LINES = (L1, L2)
SLOTS = {1: L1, 3: L2}                                     # their old indices under "low_tide"

PIN_SHORE_SCENE_OLD = "48dc96baaa5581e0c0f985c9198d86ae859124f6d15925e93edc73dd96257ae4"   # HEAD f4a4e013, with the two lines under low_tide
PIN_SCENE = {"garden": "2821b9ab44b1e74b98df95c00942246f56f5a06f33af58356e3a563f93103e9e",
             "study": "182a81ddf282707dbb496ff329b74853b11a963cfc55a3bd54c8f6720e77618d",
             "wood": "528a1ff6994a9503135445800cfbd40605099465c1de20de82757c445a5ac47e"}
PIN_EVENTS = {"garden": "ccebf4ce98e1a9f4e5881404df54d3020d8e73956f1c3cbd3835dbad98962492",
              "study": "c2e9a6a5494763ee9f16f1ac93ab9e0558ac645b8011f3281a73368257f724d3",
              "wood": "50b915cd8337b48ee06925d9983ca359d6174f2c1e08a2d1515db52e2f8aa1ad",
              "shore": "2b599d2af5aba10775786773370fcebf8e7cab9eb8b3f914fd71d31b3dad675a"}

PHASES = ("night", "dawn", "day", "dusk")
WEATHERS = ("clear", "high cloud", "overcast", "drizzle", "steady rain", "wind and rain", "thunderstorm")
WINDS = ("calm", "breeze", "fresh wind", "strong wind", "gale")
SEASONS = ("summer", "autumn", "winter", "spring")
TIDES = ("", "high", "low", "rising", "falling")
LOW_LEANING = ("low", "rising")                            # core.weather_conditions.tide_leaning -> "low_tide"
FLOOR = 6

# ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────
print("\n[1] _cond_ok semantics")
ok = WD._cond_ok
check(ok("any", {"any", "day"}) and not ok("night", {"any", "day"}), "plain keys: exactly `key in conds`")
check(ok("day+low_tide", {"any", "day", "low_tide"}), "composite holds when every part is present")
check(not ok("day+low_tide", {"any", "day"}) and not ok("day+low_tide", {"any", "low_tide"}) and not ok("day+low_tide", {"any", "night", "high_tide"}),
      "composite fails when any single part is missing")
check(ok("a+b+c", {"a", "b", "c", "d"}) and not ok("a+b+c", {"a", "b"}), "three parts work the same way")
check(not ok("day+", {"day"}) and not ok("+day", {"day"}) and not ok("", set()) and not ok("night+day", {"day"}),
      "an empty part or an unknown part fails closed (a malformed key never matches by accident)")

# ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────
print("\n[2] content: the move, and nothing else")
WD._load()
SC = C_SHORE.SCENE
check(SC.get(KEY) == list(LINES), f'shore SCENE["{KEY}"] is exactly the two lines, wording byte-identical, in order')
check(not any(l in v for k, v in SC.items() if k != KEY for l in LINES) and all(Counter(l for v in SC.values() for l in v)[l] == 1 for l in LINES),
      "each line appears exactly once, under the composite key only (not left under low_tide / day / any)")
old = {}
for k, v in SC.items():
    if k == KEY:
        continue
    old[k] = list(v)
lt = list(old["low_tide"])
for idx, l in sorted(SLOTS.items()):
    lt.insert(idx, l)
old["low_tide"] = lt
check(dig(old) == PIN_SHORE_SCENE_OLD, "the shore SCENE with the two lines put back at their old low_tide slots is byte-identical to HEAD f4a4e013 (digest pinned)")
check(len(SC["low_tide"]) == 3 and len(old["low_tide"]) == 5, "shore low_tide keeps its other 3 lines")
for p, m in (("garden", C_GARDEN), ("study", C_STUDY), ("wood", C_WOOD)):
    check(dig(m.SCENE) == PIN_SCENE[p], f"{p:6s} SCENE byte-identical to HEAD")
for p, m in (("garden", C_GARDEN), ("study", C_STUDY), ("wood", C_WOOD), ("shore", C_SHORE)):
    check(dig(m.EVENTS) == PIN_EVENTS[p], f"{p:6s} EVENTS byte-identical to HEAD")
check(WD._SCENE["shore"] == {k: list(v) for k, v in SC.items()}, "world_detail._SCENE['shore'] is exactly the module's SCENE")
check(WD.SCENE_P == 0.25, "SCENE_P untouched")


# ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────
class _Spy:
    def __init__(self):
        self.pools: list = []

    def random(self):
        return 0.0

    def choice(self, seq):
        self.pools.append(list(seq))
        return seq[0]


def pool_of(place, phase, weather, season, tide, wind) -> list:
    spy = _Spy()
    WD.random = spy
    try:
        WD.scene_extra(place, phase, weather, season, tide, wind=wind)
    finally:
        WD.random = random
    return spy.pools[0] if spy.pools else []


print("\n[3] gates + [4] exact pool: every phase x weather x season x tide x wind")
n = bad_gate = bad_pool = 0
old_night, new_night = [], []
for ph, w, se, t, wi in itertools.product(PHASES, WEATHERS, SEASONS, TIDES, WINDS):
    n += 1
    conds = WD._conds(ph, w, se, t, wi)
    got = Counter(pool_of("shore", ph, w, se, t, wi))
    want_in = ph != "night" and t in LOW_LEANING
    present = all(got[l] == 1 for l in LINES)
    absent = all(got[l] == 0 for l in LINES)
    if (want_in and not present) or (not want_in and not absent):
        bad_gate += 1
    oldpool = Counter(l for c, ls in old.items() if c in conds for l in ls)
    expect = oldpool if (ph != "night" or t not in LOW_LEANING) else oldpool - Counter(LINES)
    if got != expect or not got:
        bad_pool += 1
    if ph == "night":
        old_night.append(sum(oldpool.values()))
        new_night.append(sum(got.values()))
check(bad_gate == 0, f"the two lines are in the pool iff dawn/day/dusk AND tide in {LOW_LEANING}; absent at night and at high / falling / no tide ({n} combinations, bad={bad_gate})")
check(bad_pool == 0, f"the pool is the old pool exactly, except at night with a low-leaning tide where it is the old pool minus the two lines (bad={bad_pool})")
print(f"[5] defeater (D-0649): night shore pool size old -> new: min {min(old_night)} -> {min(new_night)}, mean {sum(old_night)/len(old_night):.2f} -> {sum(new_night)/len(new_night):.2f}")
check(min(new_night) >= FLOOR, f"smallest night shore SCENE pool is {min(new_night)} lines (floor {FLOOR})")

# explicit named cases, the reading a person would do
for ph, t, want in (("night", "low", False), ("night", "rising", False), ("day", "low", True), ("dawn", "rising", True), ("dusk", "low", True),
                    ("day", "high", False), ("day", "falling", False), ("day", "", False), ("night", "high", False)):
    pool = pool_of("shore", ph, "clear", "summer", t, "calm")
    check(all((l in pool) == want for l in LINES), f"{ph:5s} tide={t or '(none)':8s} -> lines {'present' if want else 'absent'}")

# ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────
print("\n[5b] real draws (seeded, SCENE_P forced open): night + low tide never returns either line; day + low tide reaches both")
_p = WD.SCENE_P
WD.SCENE_P = 1.0
try:
    random.seed(3484)
    seen_night = set()
    seen_day = set()
    for w, se, wi in itertools.product(WEATHERS, SEASONS, WINDS):
        for t in LOW_LEANING:
            for _ in range(6):
                seen_night.add(WD.scene_extra("shore", "night", w, se, t, wind=wi))
                seen_day.add(WD.scene_extra("shore", "day", w, se, t, wind=wi))
    check(not (seen_night & set(LINES)), "night + low tide: neither line over 1,680 seeded draws")
    check(set(LINES) <= seen_day, "day + low tide: both lines reached")
finally:
    WD.SCENE_P = _p
    WD.random = random

# ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────
print("\n[6] ledger: the observe-only render row names the composite key")
for ph, t, want in (("day", "low", True), ("night", "low", False), ("day", "high", False)):
    LED_ROWS.clear()
    _p = WD.SCENE_P
    WD.SCENE_P = 1.0
    try:
        random.seed(11)
        WD.scene_extra("shore", ph, "clear", "summer", t, wind="calm", place="shore")
    finally:
        WD.SCENE_P = _p
    conds = LED_ROWS[-1]["conds"] if LED_ROWS else []
    check((KEY in conds) == want, f"{ph:5s} tide={t:5s} draw -> ledger conds {conds}")

# ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────
print("\n[7] events: event_extra honours a composite key (injected, in-memory only)")
_saved = WD._EVENTS.get("shore")
WD._EVENTS["shore"] = [("any", "E_ANY"), ("day+low_tide", "E_DAYLOW"), ("low_tide", "E_LOW")]
try:
    random.seed(3484)
    got = {}
    for ph, t in (("day", "low"), ("night", "low"), ("day", "high")):
        seen = set()
        for _ in range(60):
            seen.add(WD.event_extra("shore", ph, "clear", "summer", t, wind="calm"))
        got[(ph, t)] = seen
    check(got[("day", "low")] == {"E_ANY", "E_DAYLOW", "E_LOW"}, "day + low: all three events reachable")
    check(got[("night", "low")] == {"E_ANY", "E_LOW"}, "night + low: the composite event is not")
    check(got[("day", "high")] == {"E_ANY"}, "day + high: only the plain 'any' event")
finally:
    WD._EVENTS["shore"] = _saved

print("\nFAILS =", FAILS)
print("ALL OK" if FAILS == 0 else "SOME CHECKS FAILED")
sys.exit(1 if FAILS else 0)
