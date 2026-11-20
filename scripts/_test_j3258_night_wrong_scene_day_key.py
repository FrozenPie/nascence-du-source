"""
Regression: D-0649 (J-3258, F-3628): the night-wrong ambient SCENE lines moved from the "any" key to a "day" key, wording byte-identical
(the J-1717 / J-1882 recipe; the F-2520 test shape).

The fault (F-3628, measured on data/scene_extra_ledger.jsonl since the 2026-10-29 restart): 32 of 244 night scene-extra renders were a
line about a diurnal bird or about light and shadow that cannot exist at night. Six of those lines sat under "any" in two SCENE pools and
move here; the SCENE pools have no empty-pool floor, so no new content is needed:
  garden  the kotare on the powerline, the blackbird crossing the lawn, the piwakawaka that finds you          -> garden SCENE["day"]
  shore   the gull bathing at the stream mouth, the driftwood log's shadow, the terns over the shallows        -> shore  SCENE["day"] (new key)
NOT moved, and why: the two "low_tide" lines with the same fault ("wet flats shine ...", "fresh shell glitters ...") sit under the
"low_tide" key, not "any"; a bare "day" key would drop their tide gate (they would then render at high tide), and a composite key needs
core/world_detail.py, which D-0649 leaves untouched. The torea line was measured and is NOT night-wrong (F-2505 gives the oystercatcher
night activity 0.3). This file asserts those two low_tide lines are still where they were, so the gap stays visible.

What this proves, PURE (only core.world_detail and the world_content_* modules are imported; the J-1694 render ledger is replaced by a
capture stub before anything draws; nothing under data/ is read or written, no DB is opened):
  [1] content   each moved line is exactly under SCENE["day"] and nowhere else, in order; the OLD garden / shore SCENE rebuilt by moving the
                lines back to their old "any" slots is byte-identical to HEAD's (digest pinned before the edit); study / wood SCENE and
                garden / shore EVENTS are byte-identical to HEAD; SCENE_P untouched
  [2] pools     the pool scene_extra() really builds (captured at its random.choice) across 4 phases x 7 weathers x 4 seasons x 5 tides x
                5 winds: at night it is the old pool minus exactly the moved lines, none of them present; at dawn / day / dusk it is the
                old pool exactly, as a multiset
  [3] explicit  every moved line is ABSENT from a night pool and PRESENT in the dawn, day and dusk pools (clear / calm / summer)
  [4] defeater  D-0649: no night garden or shore SCENE pool falls below 6 lines (min / mean printed, old -> new)
  [5] draws     seeded real draws: night never returns a moved line and still reaches every other line; dawn / day / dusk reach all of them
  [6] ledger    the J-1694 render row carries "day" by day and not at night for both places
  [7] left alone the two shore low_tide lines are still under "low_tide" (the documented gap), the torea line still under "any"

Pins are point-in-time, taken from the unmodified files at HEAD 48e42c6d on 2026-11-05: if one of those is later edited ON PURPOSE, re-pin it
here (sha256 of json.dumps(obj, ensure_ascii=False).encode("utf-8")).

  python scripts/_test_j3258_night_wrong_scene_day_key.py        # exit 0 = ALL OK
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

# The render ledger is observe-only; a capture stub goes in BEFORE any draw so this process cannot touch data/ at all.
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


# place -> (module, the moved lines in their new "day" order, {old "any" index: line} for the rebuild)
MOVED = {
    "garden": (C_GARDEN,
               ["the kōtare is on the powerline again, facing the grass",
                "a blackbird crosses the lawn low, from hedge to compost, without stopping",
                "a pīwakawaka finds you the moment you step off the path"],
               {1: "the kōtare is on the powerline again, facing the grass",
                3: "a blackbird crosses the lawn low, from hedge to compost, without stopping",
                7: "a pīwakawaka finds you the moment you step off the path"}),
    "shore": (C_SHORE,
              ["the stream mouth flashes where it crosses the sand; a gull is bathing in the fresh water",
               "the driftwood log throws the beach's only shadow",
               "terns hang over the shallows off the stream mouth, where the small fish are"],
              {1: "the stream mouth flashes where it crosses the sand; a gull is bathing in the fresh water",
               4: "the driftwood log throws the beach's only shadow",
               7: "terns hang over the shallows off the stream mouth, where the small fish are"}),
}
# Already day-keyed before this job (J-1882): the garden's cloud-shadow line stays first under "day".
PRE_DAY = {"garden": ["cloud shadow crosses the lawn, takes the bench, and slides over the fence and out to sea"], "shore": []}

# Pinned from the UNMODIFIED files at HEAD 48e42c6d (2026-11-05), before J-3258's edit.
PIN_OLD_SCENE = {"garden": "f8ac786125a842ffdb58596a282203576965ba736f4886cfaf4da5a061df3fcf",
                 "shore": "3bb1ac98613420f89065ba1f5b44d37d08dd32db16dc775c5a21a44124e39e78"}
PIN_UNCHANGED_SCENE = {"study": "182a81ddf282707dbb496ff329b74853b11a963cfc55a3bd54c8f6720e77618d",
                       "wood": "528a1ff6994a9503135445800cfbd40605099465c1de20de82757c445a5ac47e"}
PIN_EVENTS = {"garden": "ccebf4ce98e1a9f4e5881404df54d3020d8e73956f1c3cbd3835dbad98962492",
              "shore": "2b599d2af5aba10775786773370fcebf8e7cab9eb8b3f914fd71d31b3dad675a"}

# J-3484: the two shore low_tide lines now live under this composite key (day AND low_tide), at these old low_tide indices.
COMPOSITE_KEY = "day+low_tide"
COMPOSITE_SLOTS = {1: "wet flats shine from the stream mouth to the headland; every bird on the beach is working them",
                   3: "fresh shell glitters along the new tideline the sea has just left"}

PHASES = ("night", "dawn", "day", "dusk")                       # core/world_clock.daylight()'s four values
WEATHERS = ("clear", "high cloud", "overcast", "drizzle", "steady rain", "wind and rain", "thunderstorm")   # sensorium._WEATHERS
WINDS = ("calm", "breeze", "fresh wind", "strong wind", "gale")                                             # sensorium._WIND_STATES
SEASONS = ("summer", "autumn", "winter", "spring")
TIDES = ("", "high", "low", "rising", "falling")
FLOOR = 6                                                       # D-0649's defeater: a night garden / shore SCENE pool below 6 lines


def rebuild_old(scene: dict, place: str) -> dict:
    """The pre-J-3258 SCENE: the moved lines back at their old slots in 'any' (shore: no 'day' key at all), the rest as it is."""
    _m, lines, slots = MOVED[place]
    day = [l for l in scene.get("day", []) if l not in lines]
    any_ = list(scene.get("any", []))
    for idx, l in sorted(slots.items()):
        any_.insert(idx, l)
    old = {}
    for k, v in scene.items():
        if k == "any":
            old[k] = any_
        elif k == "day":
            if day:
                old[k] = day
        elif k == COMPOSITE_KEY:
            continue                                  # J-3484: restored into "low_tide" below
        else:
            old[k] = list(v)
    if place == "shore" and COMPOSITE_KEY in scene:   # J-3484: the two composite lines go back to their old low_tide slots
        lt = list(old.get("low_tide", []))
        for idx, l in sorted(COMPOSITE_SLOTS.items()):
            lt.insert(idx, l)
        old["low_tide"] = lt
    return old


# ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────
print("\n[1] content: the move, and nothing else")
WD._load()
for place, (mod, lines, slots) in MOVED.items():
    sc = mod.SCENE
    check(sc.get("day") == PRE_DAY[place] + lines, f'{place:6s} SCENE["day"] is exactly {len(PRE_DAY[place])} prior + {len(lines)} moved lines, wording unchanged, in order')
    occ = Counter(l for v in sc.values() for l in v)
    check(all(occ[l] == 1 for l in lines) and not any(l in v for k, v in sc.items() if k != "day" for l in lines),
          f"{place:6s} each moved line appears exactly once, under 'day' (none left under 'any' or any other key)")
    check(len(sc.get("any", [])) >= 1, f"{place:6s} 'any' is still non-empty ({len(sc.get('any', []))} lines)")
    check(dig(rebuild_old(sc, place)) == PIN_OLD_SCENE[place],
          f"{place:6s} the OLD SCENE, rebuilt by moving the lines back to their old 'any' slots, is byte-identical to HEAD (digest pinned before the edit)")
    check(dig(mod.EVENTS) == PIN_EVENTS[place], f"{place:6s} EVENTS byte-identical to HEAD ({len(mod.EVENTS)} lines)")
    check(WD._SCENE.get(place) == {k: list(v) for k, v in sc.items()}, f"world_detail._SCENE[{place!r}] is exactly the module's SCENE")
for p, m in (("study", C_STUDY), ("wood", C_WOOD)):
    check(dig(m.SCENE) == PIN_UNCHANGED_SCENE[p], f"{p:6s} SCENE pool byte-identical to HEAD ({sum(len(v) for v in m.SCENE.values())} lines)")
check(WD.SCENE_P == 0.25, "SCENE_P is still 0.25 (untouched)")
check(all("day" in WD._conds(ph, "clear", "summer", "", "calm") and "night" not in WD._conds(ph, "clear", "summer", "", "calm")
          for ph in ("dawn", "day", "dusk")) and "day" not in WD._conds("night", "clear", "summer", "", "calm")
      and "night" in WD._conds("night", "clear", "summer", "", "calm"),
      "premise: _conds() emits 'day' at dawn / day / dusk and 'night' (never 'day') at night")

# ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────
print("\n[2] exact pool: what scene_extra() really builds, over every condition combination")


class _Spy:
    """Stands in for the `random` module inside world_detail only: the SCENE_P gate always opens, choice() records its pool."""
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


STATS = {}
for place, (mod, lines, slots) in MOVED.items():
    old_scene = rebuild_old(mod.SCENE, place)
    moved = set(lines)
    n_night = n_day = bad_night = bad_day = leaked = 0
    old_sizes, new_sizes = [], []
    for ph, w, se, t, wi in itertools.product(PHASES, WEATHERS, SEASONS, TIDES, WINDS):
        conds = WD._conds(ph, w, se, t, wi)
        got = Counter(pool_of(place, ph, w, se, t, wi))
        old = Counter(l for c, ls in old_scene.items() if c in conds for l in ls)
        if ph == "night":
            n_night += 1
            leaked += sum(got[l] for l in moved) + (sum(got[l] for l in COMPOSITE_SLOTS.values()) if place == "shore" else 0)
            old_sizes.append(sum(old.values()))
            new_sizes.append(sum(got.values()))
            _gone = Counter(lines) + (Counter(COMPOSITE_SLOTS.values()) if place == "shore" else Counter())   # J-3484
            if got != old - _gone or not got:
                bad_night += 1
        else:
            n_day += 1
            if got != old:
                bad_day += 1
    STATS[place] = (min(old_sizes), sum(old_sizes) / len(old_sizes), min(new_sizes), sum(new_sizes) / len(new_sizes))
    check(leaked == 0, f"{place:6s} night: none of the {len(lines)} moved lines is in the pool scene_extra draws from, in any of {n_night} night combinations (leaked={leaked})")
    check(bad_night == 0, f"{place:6s} night: the pool is the old pool minus exactly the moved lines, never empty (bad={bad_night})")
    check(bad_day == 0, f"{place:6s} dawn / day / dusk: the pool is the old pool exactly, as a multiset, in all {n_day} combinations (bad={bad_day})")

# ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────
print("\n[3] explicit: every moved line absent from a night pool, present in dawn, day and dusk pools")
for place, (mod, lines, slots) in MOVED.items():
    night = set(pool_of(place, "night", "clear", "summer", "", "calm"))
    by_phase = {ph: set(pool_of(place, ph, "clear", "summer", "", "calm")) for ph in ("dawn", "day", "dusk")}
    for l in lines:
        check(l not in night and all(l in by_phase[ph] for ph in by_phase),
              f"{place:6s} {l[:60]!r}: absent at night, present at dawn / day / dusk")

# ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────
print(f"\n[4] defeater (D-0649): no night garden or shore SCENE pool below {FLOOR} lines")
for place, (omin, omean, nmin, nmean) in STATS.items():
    print(f"    {place:6s} night pool size, old -> new, over every night combination: min {omin:2d} -> {nmin:2d}, mean {omean:5.2f} -> {nmean:5.2f}")
    check(nmin >= FLOOR, f"{place:6s} smallest night SCENE pool is {nmin} lines (floor {FLOOR})")

# ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────
print("\n[5] real draws: the real scene_extra(), seeded, SCENE_P forced open")
_p_orig = WD.SCENE_P
WD.SCENE_P = 1.0
try:
    for place, (mod, lines, slots) in MOVED.items():
        moved = set(lines)
        all_lines = {l for v in mod.SCENE.values() for l in v}
        night_only = set(mod.SCENE.get("night", []))
        random.seed(3258)
        seen = {ph: set() for ph in PHASES}
        n_draws = bad = 0
        for ph in PHASES:
            for w, se, t, wi in itertools.product(WEATHERS, SEASONS, TIDES, WINDS):
                for _ in range(4):
                    x = WD.scene_extra(place, ph, w, se, t, wind=wi)
                    seen[ph].add(x)
                    if ph == "night":
                        n_draws += 1
                        bad += x in moved or x not in all_lines
        check(n_draws == 2800 and bad == 0, f"{place:6s} {n_draws} night draws over every weather x season x tide x wind: none is a moved line, all are {place} lines (bad={bad})")
        for ph in ("dawn", "day", "dusk"):
            check(moved <= seen[ph], f"{place:6s} {ph:5s} reaches all {len(moved)} moved lines")
        check(not (moved & seen["night"]) and (seen["night"] | seen["dawn"] | seen["day"] | seen["dusk"]) == all_lines,
              f"{place:6s} all {len(all_lines)} lines are still reachable overall (the moved ones by day, the night ones at night)")
finally:
    WD.SCENE_P = _p_orig
    WD.random = random

# ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────
print("\n[6] ledger: the observe-only render row carries the new key by day, not at night")
for place in MOVED:
    for ph, want_day in (("night", False), ("day", True)):
        LED_ROWS.clear()
        random.seed(5)
        _p = WD.SCENE_P
        WD.SCENE_P = 1.0
        try:
            x = WD.scene_extra(place, ph, "clear", "summer", "", wind="calm", place=place)
        finally:
            WD.SCENE_P = _p
        row = LED_ROWS[-1] if LED_ROWS else {}
        conds = row.get("conds", [])
        check(row.get("loc") == place and row.get("line") == x and (("day" in conds) == want_day) and (("night" in conds) == (not want_day)),
              f"{place:6s} {ph:5s} draw -> ledger conds {conds} pool {row.get('pool')} ('day' {'in' if 'day' in conds else 'not in'} conds)")

# ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────
print("\n[7] left alone: the two shore low_tide lines (documented gap) and the torea line")
LOW = list(COMPOSITE_SLOTS.values())
check(all(l in C_SHORE.SCENE[COMPOSITE_KEY] for l in LOW) and not any(l in C_SHORE.SCENE.get("day", []) or l in C_SHORE.SCENE["low_tide"] for l in LOW),
      "J-3484: the two formerly night-wrong shore low_tide lines are now under the composite 'day+low_tide' key only (tide gate AND day gate; see scripts/_test_j3484_composite_scene_key.py)")
check("tōrea work the tideline while the karoro stand higher up, spaced out, facing the sea" in C_SHORE.SCENE["any"],
      "the torea line (F-2505: night activity 0.3, not night-wrong) is still under 'any'")

print("\nFAILS =", FAILS)
print("ALL OK" if FAILS == 0 else "SOME CHECKS FAILED")
sys.exit(1 if FAILS else 0)
