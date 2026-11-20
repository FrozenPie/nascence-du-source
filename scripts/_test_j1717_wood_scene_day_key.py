"""
Regression: the wood's four daylight-bound SCENE lines live under a "day" key, so they stop rendering at night
(J-1717 / F-2340).

The fault (J-1693 read the wood pool before it first rendered): core/world_content_wood.py SCENE keyed its ambient lines on
any / night / windy / wet / winter and had NO "day" key. world_detail._conds() always emits "any" and emits "night" INSTEAD of
"day" when the phase is night, so four lines that are daylight-bound by their own wording -- the wood pigeon crossing between
canopies, the fantail's loose company, the shaft of light on the bracket fungus, the wren's scold -- sat under "any" and could
render at night: a night draw's pool was 8 any + 2 night = 10 lines, four of them daylight-bound. The module's own EVENTS already
key the fantail and the bracket-fungus shaft on "day", and core/life_birds.py gives the fantail, the kereru (wood pigeon) and the
wren active_hours=DIURNAL, so the "any" placement was an authoring looseness, not a ruling.

The fix is a move: those four lines, wording unchanged, now sit under SCENE["day"] (_conds() emits "day" for dawn, day and dusk).
Nothing else changes: SCENE_P, every other wood pool, and the study / garden / shore content are byte-identical. The one honest
difference besides the night pool is ORDER: at dawn / day / dusk the flattened pool is the same lines (same multiset, same size,
same 1-in-N odds) but the four now follow the other "any" lines instead of sitting interleaved, so a seeded replay of a wood draw
can land on a different line than before. Nothing in the repo pins a seed to a wood line.

What this proves, PURE: only core.world_detail and the four world_content_* modules are imported -- no sensorium, no locomotion,
no model, no live data. The render ledger (J-1694) is replaced by a capture stub before anything draws, so nothing can be
written, and the live stores are stat-ed before and after.
  [1] content    the four lines are exactly SCENE["day"] and nowhere else; the old dict, rebuilt from the new one by moving the four
                 lines back to their old slots, matches a digest pinned from HEAD (da1241c) BEFORE the edit; wood TARGETS / EVENTS and
                 the study / garden / shore SCENE match their pinned digests; _conds() emits "day" at dawn / day / dusk, never at night
  [2] exact pool the pool scene_extra() really builds (captured at its random.choice) across 4 phases x 7 weathers x 4 seasons x
                 5 tides x 5 winds: at night it is the old pool minus the four (never empty); at dawn / day / dusk it is the old
                 pool exactly, as a multiset (daytime pool composition by condition is unchanged)
  [3] real draws seeded draws through the real scene_extra() with the SCENE_P gate forced open: night never returns one of the
                 four and still reaches the other 11 wood lines; dawn, day and dusk each reach the 13 lines that are not night-only (the
                 four included), and all 15 stay reachable overall
  [4] ledger     the observe-only render row (J-1694) sees the new key: a night wood draw is conds [any, night] over 6 lines, a day
                 wood draw is conds [any, day] over 8, so the J-1695 read-back counts post-J-1717 rows correctly
  [5] the live stores are untouched

Pins (the digests below) are point-in-time, taken from the unmodified files at da1241c on 2026-10-03: if one of those pools is later
edited ON PURPOSE, re-pin it here (sha256 of json.dumps(obj, ensure_ascii=False).encode("utf-8")).

  python scripts/_test_j1717_wood_scene_day_key.py        # exit 0 = ALL OK
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

# data/ is gitignored and never checked out into a job-run worktree, so "live" is the one real repo, never ROOT-relative.
_LIVE_DATA = Path(r"C:\Nascence") / "data"
_WATCH = [_LIVE_DATA / "scene_extra_ledger.jsonl", _LIVE_DATA / "room_state.json", _LIVE_DATA / "position.json",
          _LIVE_DATA / "memory" / "nascence.db", _LIVE_DATA / "memory" / "nascence.db-wal"]


def _snap(p: Path):
    if not p.exists():
        return None
    st = p.stat()
    return (st.st_size, st.st_mtime_ns)


_before = {p: _snap(p) for p in _WATCH}

# The render ledger is observe-only and would be refused by the D-0179 write fence in a non-live process anyway; a capture stub
# goes in BEFORE any draw so this process cannot touch data/ at all (and so the ledger's own rows can be inspected in [4]).
LED_ROWS: list = []


def _record(location, place, conds, line, pool):
    LED_ROWS.append({"loc": location, "place": place, "conds": sorted(conds), "line": line, "pool": int(pool)})
    return False


_led = types.ModuleType("core.scene_extra_ledger")
_led.record = _record
sys.modules["core.scene_extra_ledger"] = _led

import core                                        # noqa: E402
core.scene_extra_ledger = _led
from core import world_detail as WD                # noqa: E402
from core import world_content_study as C_STUDY    # noqa: E402
from core import world_content_garden as C_GARDEN  # noqa: E402
from core import world_content_shore as C_SHORE    # noqa: E402

# J-3484 (D-0649 follow-up) gave the two shore low_tide lines that are also night-wrong the composite key "day+low_tide", AFTER this
# test's baseline. This file proves an earlier move on that baseline, so it puts the two lines back under "low_tide" at their old slots,
# in memory only and before anything reads the pools (world_detail loads lazily); scripts/_test_j3484_composite_scene_key.py proves the new key.
_J3484_SLOTS = {1: "wet flats shine from the stream mouth to the headland; every bird on the beach is working them",
                3: "fresh shell glitters along the new tideline the sea has just left"}
if "day+low_tide" in C_SHORE.SCENE:
    C_SHORE.SCENE.pop("day+low_tide")
    for _i, _l in sorted(_J3484_SLOTS.items()):
        C_SHORE.SCENE["low_tide"].insert(_i, _l)
from core import world_content_wood as C_WOOD      # noqa: E402

FAILS = 0


def check(cond: bool, label: str) -> None:
    global FAILS
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS += 1


def dig(obj) -> str:
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False).encode("utf-8")).hexdigest()


FOUR = [
    "a wood pigeon crosses between canopies, heavy and straight as a thrown thing",
    "a fantail keeps you loose company, never still for a full second",
    "one shaft of light has found a bracket fungus and lit it like a small lamp",
    "the wren's scold moves through the undergrowth ahead of you, always a little out of sight",
]
FOUR_SET = set(FOUR)
OLD_DAY_SLOTS = (1, 3, 5, 6)         # the slots those four held in the old 8-line "any" list

# Pinned from the UNMODIFIED files at HEAD da1241c (2026-10-03), before J-1717's edit.
PIN_OLD_WOOD_SCENE = "8b65865dd887a4001cb55dcfed112a8639b7c5ddbe1c5f2e1e624952b19fc500"   # the old dict incl. key + line order
# RE-PINNED by J-1882 (F-2505): two wood look-target lines (canopy, deadfall) moved from "any" to "day" ON PURPOSE, so the TARGETS digest changed;
# the HEAD da1241c digest was b38a4c45...9768. See scripts/_test_j1732_target_day_key.py for the per-target proof.
PIN_WOOD_TARGETS = "842d0d8f64b33834a4ad689e53b87d238b0c4bfb1e2480e62d40434e18dc5e04"
PIN_WOOD_EVENTS = "50b915cd8337b48ee06925d9983ca359d6174f2c1e08a2d1515db52e2f8aa1ad"
PIN_OTHER_SCENE = {"study": "182a81ddf282707dbb496ff329b74853b11a963cfc55a3bd54c8f6720e77618d",
                   # RE-PINNED by J-1898 (D-0360 a): the study SCENE "sun off the sea puts a wavering light on the ceiling boards" line moved from "any" to
                   # a new "day" key on purpose (was be391888...6cc); scripts/_test_j1898_bright_gate_study_scene_day.py proves the move
                   # RE-PINNED by J-1882: the garden SCENE "cloud shadow crosses the lawn" line moved from "any" to a new "day" key on purpose (was 5021183b...c7a)
                   # RE-PINNED by J-3258 (D-0649): 3 garden and 3 shore SCENE lines moved from "any" to "day" on purpose (were f8ac7861...f3fcf / 3bb1ac98...e78)
                   "garden": "2821b9ab44b1e74b98df95c00942246f56f5a06f33af58356e3a563f93103e9e",
                   "shore": "48dc96baaa5581e0c0f985c9198d86ae859124f6d15925e93edc73dd96257ae4"}
OTHER = {"study": C_STUDY, "garden": C_GARDEN, "shore": C_SHORE}

PHASES = ("night", "dawn", "day", "dusk")                       # core/world_clock.daylight()'s four values
WEATHERS = ("clear", "high cloud", "overcast", "drizzle", "steady rain", "wind and rain", "thunderstorm")   # sensorium._WEATHERS
WINDS = ("calm", "breeze", "fresh wind", "strong wind", "gale")                                             # sensorium._WIND_STATES
SEASONS = ("summer", "autumn", "winter", "spring")
TIDES = ("", "high", "low", "rising", "falling")
W = C_WOOD.SCENE
ALL15 = {l for lines in W.values() for l in lines}


def rebuild_old(new: dict) -> dict:
    """The pre-J-1717 wood SCENE: the four day lines back at their old slots in 'any', the 'day' key gone, the rest as it is.
    {} if the new dict does not have the expected shape (the digest check then fails loudly instead of this raising)."""
    a, d = iter(new.get("any", [])), iter(new.get("day", []))
    old_any = []
    try:
        for i in range(8):
            old_any.append(next(d) if i in OLD_DAY_SLOTS else next(a))
    except StopIteration:
        return {}
    old = {"any": old_any}
    old.update({k: v for k, v in new.items() if k not in ("any", "day")})
    return old


def folded(new: dict) -> dict:
    """The old pool by key, order-free: every 'day' line folded back under 'any'."""
    old = {k: list(v) for k, v in new.items() if k != "day"}
    old["any"] = list(new.get("any", [])) + list(new.get("day", []))
    return old


# ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────
print("\n[1] content: the move, and nothing else")
check(W.get("day") == FOUR, f'SCENE["day"] is exactly the four daylight-bound lines, wording unchanged ({len(W.get("day", []))} lines)')
occ = Counter(l for lines in W.values() for l in lines)
check(all(occ[l] == 1 for l in FOUR) and not any(l in lines for k, lines in W.items() if k != "day" for l in FOUR),
      "each of the four appears exactly once in the pool, under 'day' (none left under 'any' or any other key)")
check(set(W) == {"any", "day", "night", "windy", "wet", "winter"}, f"the wood SCENE keys are any / day / night / windy / wet / winter (got {sorted(W)})")
check(sum(len(v) for v in W.values()) == 15 and len(occ) == 15 and max(occ.values()) == 1,
      f"still 15 lines, no duplicates ({ {k: len(v) for k, v in W.items()} })")
check(dig(rebuild_old(W)) == PIN_OLD_WOOD_SCENE,
      "the OLD wood SCENE, rebuilt from the new one by moving the four lines back, is byte-identical to HEAD's (digest pinned before the edit)")
check(dig(C_WOOD.TARGETS) == PIN_WOOD_TARGETS, "wood TARGETS (every look-target pool) byte-identical to HEAD")
check(dig(C_WOOD.EVENTS) == PIN_WOOD_EVENTS, "wood EVENTS byte-identical to HEAD")
for p, m in OTHER.items():
    check(dig(m.SCENE) == PIN_OTHER_SCENE[p], f"{p:6s} SCENE pool byte-identical to HEAD ({sum(len(v) for v in m.SCENE.values())} lines)")
WD._load()
check(WD._SCENE.get("wood") == {k: list(v) for k, v in W.items()}, "world_detail._SCENE['wood'] is exactly the module's SCENE")
check(WD.SCENE_P == 0.25, "SCENE_P is still 0.25 (untouched)")
check(all("day" in WD._conds(ph, "clear", "summer", "", "calm") and "night" not in WD._conds(ph, "clear", "summer", "", "calm")
          for ph in ("dawn", "day", "dusk")) and "day" not in WD._conds("night", "clear", "summer", "", "calm")
      and "night" in WD._conds("night", "clear", "summer", "", "calm"),
      "premise: _conds() emits 'day' at dawn / day / dusk and 'night' (never 'day') at night")

# ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────
print("\n[2] exact pool: what scene_extra('wood') really builds, over every condition combination")


class _Spy:
    """Stands in for the `random` module inside world_detail only: the SCENE_P gate always opens, choice() records its pool."""
    def __init__(self):
        self.pools: list = []

    def random(self):
        return 0.0

    def choice(self, seq):
        self.pools.append(list(seq))
        return seq[0]


def wood_pool(phase, weather, season, tide, wind) -> list:
    spy = _Spy()
    WD.random = spy
    try:
        WD.scene_extra("wood", phase, weather, season, tide, wind=wind)
    finally:
        WD.random = random
    return spy.pools[0] if spy.pools else []


OLD = folded(W)
n_night = n_day = bad_night = bad_day = leaked = 0
night_sizes, day_sizes = set(), set()
for ph, w, se, t, wi in itertools.product(PHASES, WEATHERS, SEASONS, TIDES, WINDS):
    conds = WD._conds(ph, w, se, t, wi)
    got = Counter(wood_pool(ph, w, se, t, wi))
    old = Counter(l for c, lines in OLD.items() if c in conds for l in lines)
    if ph == "night":
        n_night += 1
        night_sizes.add(sum(got.values()))
        leaked += sum(1 for l in FOUR if got[l])
        if got != old - Counter(FOUR) or not got:
            bad_night += 1
    else:
        n_day += 1
        day_sizes.add(sum(got.values()))
        if got != old:
            bad_day += 1
check(leaked == 0, f"night: none of the four daylight-bound lines is in the pool scene_extra draws from, in any of {n_night} night combinations (leaked={leaked})")
check(bad_night == 0, f"night: the pool is the old pool minus exactly those four, never empty (bad={bad_night}; sizes {sorted(night_sizes)})")
check(bad_day == 0, f"dawn / day / dusk: the pool is the old pool exactly, as a multiset, in all {n_day} combinations (bad={bad_day}; sizes {sorted(day_sizes)})")
base_night = wood_pool("night", "clear", "summer", "", "calm")
base_day = wood_pool("day", "clear", "summer", "", "calm")
check(len(base_night) == 6 and not (set(base_night) & FOUR_SET), f"clear / calm summer night: {len(base_night)} lines (was 10), none daylight-bound")
check(len(base_day) == 8 and FOUR_SET <= set(base_day), f"clear / calm summer day: {len(base_day)} lines (as before), all four daylight lines in it")

# ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────
print("\n[3] real draws: the real scene_extra(), seeded, SCENE_P forced open")
_p_orig = WD.SCENE_P
WD.SCENE_P = 1.0                       # random() never exceeds 1.0: the gate is not under test here
try:
    random.seed(1717)
    seen = {ph: set() for ph in PHASES}
    n_draws = bad = 0
    for ph in PHASES:
        for w, se, t, wi in itertools.product(WEATHERS, SEASONS, TIDES, WINDS):
            for _ in range(6):
                x = WD.scene_extra("wood", ph, w, se, t, wind=wi)
                seen[ph].add(x)
                if ph == "night":
                    n_draws += 1
                    bad += x in FOUR_SET or x not in ALL15
    check(n_draws == 4200 and bad == 0, f"{n_draws} night draws over every weather x season x tide x wind: none is one of the four, all are wood lines (bad={bad})")
    check(seen["night"] == ALL15 - FOUR_SET, f"night still reaches the other {len(ALL15 - FOUR_SET)} wood lines (reached {len(seen['night'])})")
    NIGHT_ONLY = set(W.get("night", []))              # the two night-key lines: by construction not drawable at dawn / day / dusk (before or after)
    for ph in ("dawn", "day", "dusk"):
        check(seen[ph] == ALL15 - NIGHT_ONLY,
              f"{ph:5s} reaches every wood line except the {len(NIGHT_ONLY)} night-only ones, the four daylight-bound included (reached {len(seen[ph])} of {len(ALL15)})")
    check(FOUR_SET <= seen["dawn"] & seen["day"] & seen["dusk"], "each of the four is drawable at dawn, at day and at dusk")
    check(seen["night"] | seen["dawn"] | seen["day"] | seen["dusk"] == ALL15, f"all {len(ALL15)} wood lines are still reachable overall (night-only ones at night, the daylight four by day)")

    # ─────────────────────────────────────────────────────────────────────────────────────────────────────────────
    print("\n[4] ledger: the observe-only render row sees the new key")
    for ph, want_conds, want_pool in (("night", ["any", "night"], 6), ("day", ["any", "day"], 8)):
        LED_ROWS.clear()
        random.seed(5)
        x = WD.scene_extra("wood", ph, "clear", "summer", "", wind="calm", place="wood")
        row = LED_ROWS[-1] if LED_ROWS else {}
        check(row.get("loc") == "wood" and row.get("place") == "wood" and row.get("line") == x and row.get("conds") == want_conds
              and row.get("pool") == want_pool,
              f"{ph:5s} wood draw -> ledger row conds {row.get('conds')} pool {row.get('pool')} (want {want_conds}, {want_pool})")
finally:
    WD.SCENE_P = _p_orig
    WD.random = random

# ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────
print("\n[5] the live stores are untouched")
for p in _WATCH:
    after = _snap(p)
    check(after == _before[p], f"{p.name}: unchanged ({'absent' if after is None else f'{after[0]} bytes'})")

print("\nFAILS =", FAILS)
print("ALL OK" if FAILS == 0 else "SOME CHECKS FAILED")
sys.exit(1 if FAILS else 0)
