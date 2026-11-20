"""
Regression: the six own-wording daylight lines that sat under "any" in the look-target pools and the garden's ambient SCENE pool
live under a "day" key, so they stop rendering at night (J-1882, the mechanical part of the F-2505 / J-1732 audit; same recipe
as J-1717 / F-2362, the wood SCENE).

The fault: world_detail._conds() always emits "any" and emits "night" INSTEAD of "day" when the phase is night, so a line under
"any" can render at any hour. Six lines name the sun, a day-part, flecks / coins / a line of light or a cloud shadow in their own
wording and sat under "any":
  study  shelf_of_kept_things  "afternoon sun crosses the shelf end to end in an hour"          (any index 1)
  garden kowhai                "the kowhai stands mid-slope, ... letting light through in flecks"   (any index 0)
  shore  horizon               "a container ship crosses left to right, hull-down, taking the whole morning about it"   (any 5)
  wood   canopy                "the canopy shifts and settles above you, sifting the light into coins ..." (any 0)
  wood   deadfall              "one fallen limb is shelved with pale bracket fungus, each shelf catching its own line of light" (any 3)
  garden SCENE (ambient)       "cloud shadow crosses the lawn, takes the bench, and slides over the fence and out to sea"   (any 8)
The fix is a move, wording byte-identical, to a new "day" key at each of those six places (the key _conds() already emits for dawn,
day and dusk). No engine change. NOT moved, on purpose: the "bright" / season / windy key lines, the rare lists, the tier-B bird
lines, EVENTS (D-0360 parts b and c), and the study SCENE "sun off the sea puts a wavering light on the ceiling boards" (D-0360
part a, still OPEN when this job ran, so it stays under "any" and is pinned unchanged below).

What this proves, PURE: only core.world_detail and the four world_content_* modules are imported -- no sensorium, no model, no live
data. The render ledger (J-1694) is replaced by a capture stub before anything draws, and the live stores are stat-ed before and
after.
  [1] content    each line is exactly under "day" of its own container and nowhere else; the OLD container rebuilt by moving the line
                 back to its old "any" slot matches the digest pinned from HEAD (616a360) BEFORE the edit; every other target spec (34 of
                 39 incl. rare and aliases), every EVENTS list, SCENE_P and the other SCENE pools are byte-identical to HEAD; every
                 target still registers
  [2] exact pool the pool detail() / extra_pool() / scene_extra() really draw from, across 4 phases x 7 weathers x 4 seasons x
                 5 tides x 5 winds: at night it is the old pool minus exactly the moved line (never empty); at dawn / day / dusk it
                 is the old pool exactly, as a multiset
  [3] real draws seeded draws through the real detail() / scene_extra(): at night (4,200 per container) the moved line is never drawn
                 and the rest is still reached; at dawn, day and dusk the moved line is reachable
  [4] ledger     the J-1694 render row for the garden SCENE carries "day" by day and not at night
  [5] the live stores are untouched

Pins are point-in-time, taken from the unmodified files at HEAD 616a360 on 2026-10-07: if one of those pools is later edited ON PURPOSE,
re-pin it here (sha256 of json.dumps(obj, ensure_ascii=False).encode("utf-8")).

  python scripts/_test_j1732_target_day_key.py        # exit 0 = ALL OK
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

# data/ is gitignored and never checked out into a worktree, so "live" is the one real repo, never ROOT-relative.
_LIVE_DATA = Path(r"C:\Nascence") / "data"
_WATCH = [_LIVE_DATA / "scene_extra_ledger.jsonl", _LIVE_DATA / "room_state.json", _LIVE_DATA / "position.json",
          _LIVE_DATA / "memory" / "nascence.db", _LIVE_DATA / "memory" / "nascence.db-wal"]


def _snap(p: Path):
    if not p.exists():
        return None
    st = p.stat()
    return (st.st_size, st.st_mtime_ns)


_before = {p: _snap(p) for p in _WATCH}

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

# J-3258 (D-0649) moved three more garden SCENE lines and three shore SCENE lines from "any" to "day" on purpose, AFTER this test's
# J-1882 baseline. This file proves the J-1882 move on the J-1882 baseline, so it puts J-3258's six lines back where they were, in memory
# only and before anything reads the pools (world_detail loads lazily); scripts/_test_j3258_night_wrong_scene_day_key.py proves the new move.
def _undo_j3258(scene: dict, day_lines: list, old_any_slots: dict) -> None:
    for l in day_lines:
        scene["day"].remove(l)
    any_ = scene["any"]
    for idx, l in sorted(old_any_slots.items()):
        any_.insert(idx, l)


_undo_j3258(C_GARDEN.SCENE, ["the kōtare is on the powerline again, facing the grass",
                             "a blackbird crosses the lawn low, from hedge to compost, without stopping",
                             "a pīwakawaka finds you the moment you step off the path"],
            {1: "the kōtare is on the powerline again, facing the grass",
             3: "a blackbird crosses the lawn low, from hedge to compost, without stopping",
             7: "a pīwakawaka finds you the moment you step off the path"})
_undo_j3258(C_SHORE.SCENE, ["the stream mouth flashes where it crosses the sand; a gull is bathing in the fresh water",
                            "the driftwood log throws the beach's only shadow",
                            "terns hang over the shallows off the stream mouth, where the small fish are"],
            {1: "the stream mouth flashes where it crosses the sand; a gull is bathing in the fresh water",
             4: "the driftwood log throws the beach's only shadow",
             7: "terns hang over the shallows off the stream mouth, where the small fish are"})
C_SHORE.SCENE.pop("day", None)               # the shore had no "day" key before J-3258 (undo leaves it empty)

# J-3484 (D-0649 follow-up) gave the two shore low_tide lines that are also night-wrong the composite key "day+low_tide", AFTER this
# test's baseline. This file proves an earlier move on that baseline, so it puts the two lines back under "low_tide" at their old slots,
# in memory only and before anything reads the pools (world_detail loads lazily); scripts/_test_j3484_composite_scene_key.py proves the new key.
_J3484_SLOTS = {1: "wet flats shine from the stream mouth to the headland; every bird on the beach is working them",
                3: "fresh shell glitters along the new tideline the sea has just left"}
if "day+low_tide" in C_SHORE.SCENE:
    C_SHORE.SCENE.pop("day+low_tide")
    for _i, _l in sorted(_J3484_SLOTS.items()):
        C_SHORE.SCENE["low_tide"].insert(_i, _l)

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


MODS = {"study": C_STUDY, "garden": C_GARDEN, "shore": C_SHORE, "wood": C_WOOD}

# (place, kind, target or "", the line, its old index in the old "any" list)
MOVES = [
    ("study", "target", "shelf_of_kept_things", "afternoon sun crosses the shelf end to end in an hour", 1),
    ("garden", "target", "kowhai", "the k\u014dwhai stands mid-slope, small-leaved, letting light through in flecks", 0),
    ("shore", "target", "horizon", "a container ship crosses left to right, hull-down, taking the whole morning about it", 5),
    ("wood", "target", "canopy", "the canopy shifts and settles above you, sifting the light into coins that move on the ground", 0),
    ("wood", "target", "deadfall", "one fallen limb is shelved with pale bracket fungus, each shelf catching its own line of light", 3),
    ("garden", "scene", "", "cloud shadow crosses the lawn, takes the bench, and slides over the fence and out to sea", 8),
]
MOVED_TARGET_KEYS = {f"{p}:{t}" for p, k, t, _l, _i in MOVES if k == "target"}
MOVED_SCENE_PLACES = {p for p, k, _t, _l, _i in MOVES if k == "scene"}

# Pinned from the UNMODIFIED files at HEAD 616a360 (2026-10-07), before J-1882's edit.
PIN_TARGETS = {
    "study:record_player": "88917105f933d238e921cf761be30c5d7e518e053f6c6fa0a43af4acaee29e53",
    "study:desk": "f2a4201536bcb27b8d8d51d8c4dc8e1c1a4dd423bc0b908e14f56d3212b0d30c",
    "study:bookshelf": "ce7b14ea3e356459c6f44b47b5af223d5e06e3826502d48ab231626ead893c49",
    "study:lamp": "50b2d973ea37e4eaceb03db34d5d925bea303e36b92da7612b7116aeff3842aa",
    "study:study_window": "e15e025e1b66c699273dbb136350cbbab30467a11e53c82b21667e631600dec6",
    "study:hearth_tools": "03beb663d33eba72410d0250a0ac750ee08bb6b8ce9f8f79d5219dfea3005566",
    "study:rug": "86eb2b18ba7f9f99041214a55bf572e9ba8d825e8e1b7b1f478194e9785dfd50",
    "study:ink_and_pen": "c498ef83e11a79a1d1ebdae72901d89f4ecc415923ccdd38a2838436f11b1a29",
    "study:letter_drawer": "ab3410bb654966087e464e7e5e881d86318c92042014313a983b41e3eedc8cad",
    "study:candle": "e3f416fd5548e26042fa2735c27beaea3168f30c9321a064e274b938fe4b2659",
    "study:ceiling": "c966754e1711cf39621879854557e2a7f566aa34d3b375f3aebe86c046793071",
    "study:door_and_coats": "760e77047e1d9b51494ff51f8e8f67197edf36b037a3d5e2b16124ebc2ae791f",
    "study:shelf_of_kept_things": "911b5ec60700cc5803d2ad9eafafd2f8790fcd1b918cb1a1e6600e6be706cbd7",
    "garden:lawn": "2f92b845fbe7c5d7826e13dde98efda383f84503d7211d49bc314f93059c8e9c",
    "garden:fence": "4d1dfc5d35d76f513a256c459c25f36d89ecda2e03f620713a3fb84eda4415d5",
    "garden:compost": "688ca1ac8de015daef238d993231b762326f181003c22829017e184c05493791",
    "garden:bench": "2910a011869a18358156682c17349444d7ab0446305dfc9bdc1d55bdbcb40b1c",
    "garden:rain_barrel": "fc6c2eb531b53b903d12a34e1dd3b02c265a9db8d6ec23e87754538666280736",
    "garden:harakeke": "2aaf3ffab1de880185b061caf97d5002bd62c45961f9963d0e0120261feb4635",
    "garden:kowhai": "6643c59828601916615598dfd3157b7596ed5ef4c4ac0c6565c9e471d81d1940",
    "garden:ti_kouka": "93f18dff8a9bab5fc9401d8bc30b0010746630445c7fddd7c0a66b33ca86b153",
    "garden:birds": "a7620bf727d7ed02ef174e93f28a2708a8b72c99ae531f7b5d5fccaa6bb171be",
    "garden:hedge": "ab2f672067892de7e749026782f38083f9e78be430ec58fe5fa3123caab37c09",
    "shore:driftwood": "23ba42ce2df2c2140252f3a0e4e2db21b0363d84fe5fc0cc6451849edc9aefea",
    "shore:kelp": "0a0e7144fbe4dd17854e7d9573d55331fcf7537fcdf5ec994951ee436238d8b0",
    "shore:shells": "04d92f6c3d52cf473222e9f4c006b2a64f64378b8beff7ecb21f51c7a557a3eb",
    "shore:headland": "342020fc00a7df8ec0e011f08b7054d62575e5a7310a6c57e6269529da69c00a",
    "shore:dune_grass": "2695401116c0657ba3e9f4296aac65aefc4be30e3486d758db9b7558f46b0b83",
    "shore:birds": "c6071633fcc465b9c6525ae8075dfa662fbf018ba6bee3fe9f38ca1d0b63b7cb",
    "shore:stones": "4314046eff9b6e3842be114c3ff1760bb39a327a44ca2d84ba92d68503a73d86",
    "shore:horizon": "c9af2387f61398be5cc7f7ad585012dcc545ea8f2d32611e3e76a7762efb75e5",
    "shore:cliff": "c8e6e3878df2f0ae4be94bad3844204c83f7a8bc5df05c4425ba53c01d8237bd",
    "shore:stream_mouth": "970eefa12d88163e3769647f2aa07e42354692383e28185803631f9fefca6c64",
    "wood:path": "8b1b67ca202dd0a262a7c529e998afbeafd931eb069f3155573f14acbeb3603e",
    "wood:canopy": "c96d86a4b61a7c59bd1ce1fb131288cb4abded7dfa0572400e7f62dcf2d7fef0",
    "wood:undergrowth": "176233fe345f8f6724043199d9d26f246dfcf7a90fb58ba12f8ae4ea51fdc749",
    "wood:deadfall": "53fda28a4594ad1475858ac7b97017053fea92e636fb5c008b0aa6efa503ce76",
    "wood:moss": "eaaede8b199bc2e3e3335c648067eb9ac1ac0a2689b5708f6d5582a933aa2da2",
    "wood:birds": "77fabb8fe1c276f9a23745929bd226bbbc33e1677124c69fec4965903f15f748",
}
PIN_EVENTS = {"study": "c2e9a6a5494763ee9f16f1ac93ab9e0558ac645b8011f3281a73368257f724d3",
              "garden": "ccebf4ce98e1a9f4e5881404df54d3020d8e73956f1c3cbd3835dbad98962492",
              "shore": "2b599d2af5aba10775786773370fcebf8e7cab9eb8b3f914fd71d31b3dad675a",
              "wood": "50b915cd8337b48ee06925d9983ca359d6174f2c1e08a2d1515db52e2f8aa1ad"}
PIN_SCENE = {"study": "182a81ddf282707dbb496ff329b74853b11a963cfc55a3bd54c8f6720e77618d",   # RE-PINNED by J-1898 (D-0360 a): the study SCENE line moved from "any" to "day" on purpose (was be391888...6cc)
             "garden": "5021183bc5ac15b3dc558042978e2b39424aa0bd6929370c867be51d115cac7a",   # the OLD garden SCENE (rebuilt below)
             "shore": "3bb1ac98613420f89065ba1f5b44d37d08dd32db16dc775c5a21a44124e39e78",
             "wood": "528a1ff6994a9503135445800cfbd40605099465c1de20de82757c445a5ac47e"}      # unchanged since J-1717

PHASES = ("night", "dawn", "day", "dusk")
WEATHERS = ("clear", "high cloud", "overcast", "drizzle", "steady rain", "wind and rain", "thunderstorm")
WINDS = ("calm", "breeze", "fresh wind", "strong wind", "gale")
SEASONS = ("summer", "autumn", "winter", "spring")
TIDES = ("", "high", "low", "rising", "falling")


def rebuild_old_container(container: dict, line: str, old_idx: int) -> dict:
    """The pre-J-1882 pool dict: the moved line back at its old slot in 'any', the 'day' key gone. {} if the shape is not as
    expected (the digest check then fails loudly instead of this raising)."""
    if container.get("day") != [line]:
        return {}
    any_ = list(container.get("any", []))
    if line in any_ or old_idx > len(any_):
        return {}
    any_.insert(old_idx, line)
    old = {"any": any_}
    old.update({k: v for k, v in container.items() if k not in ("any", "day")})
    return old


def container_of(place, kind, target):
    m = MODS[place]
    return m.SCENE if kind == "scene" else m.TARGETS[target]["pools"]


def old_spec(place, target, line, idx):
    spec = dict(MODS[place].TARGETS[target])
    spec["pools"] = rebuild_old_container(spec["pools"], line, idx)
    return spec


WD._load()

# ---------------------------------------------------------------------------------------------------------------------
print("\n[1] content: the move, and nothing else")
for place, kind, target, line, idx in MOVES:
    c = container_of(place, kind, target)
    where = f"{place} {target or 'SCENE'}"
    check(c.get("day") == [line], f'{where}: ["day"] is exactly the one daylight line, wording unchanged')
    occ = Counter(l for lines in c.values() for l in lines)
    check(occ[line] == 1 and line not in c.get("any", []), f"{where}: the line appears once, under 'day', not left under 'any'")
    check(len(c.get("any", [])) >= 1, f"{where}: 'any' is still non-empty ({len(c.get('any', []))} lines)")
    if kind == "target":
        old = old_spec(place, target, line, idx)
        check(dig(old) == PIN_TARGETS[f"{place}:{target}"],
              f"{where}: the OLD spec, rebuilt by moving the line back to any[{idx}], is byte-identical to HEAD (digest pinned before the edit)")
        new_spec = MODS[place].TARGETS[target]
        check(old and dig(new_spec["rare"]) == dig(old["rare"]) and new_spec["aliases"] == old["aliases"],
              f"{where}: rare list and aliases untouched")
    else:
        old = rebuild_old_container(c, line, idx)
        check(dig(old) == PIN_SCENE[place], f"{where}: the OLD SCENE, rebuilt by moving the line back to any[{idx}], is byte-identical to HEAD")
unchanged = [k for k in PIN_TARGETS if k not in MOVED_TARGET_KEYS]
bad = [f"{p}:{t}" for p, m in MODS.items() for t, spec in m.TARGETS.items()
       if f"{p}:{t}" not in MOVED_TARGET_KEYS and dig(spec) != PIN_TARGETS.get(f"{p}:{t}")]
check(len(unchanged) == 34 and not bad, f"the other {len(unchanged)} target specs (pools, rare, aliases) are byte-identical to HEAD (bad={bad})")
check(set(PIN_TARGETS) == {f"{p}:{t}" for p, m in MODS.items() for t in m.TARGETS} and len(PIN_TARGETS) == 39,
      "the pin set covers all 39 targets, none added or removed")
for p, m in MODS.items():
    check(dig(m.EVENTS) == PIN_EVENTS[p], f"{p:6s} EVENTS byte-identical to HEAD ({len(m.EVENTS)} lines)")
    if p not in MOVED_SCENE_PLACES:
        check(dig(m.SCENE) == PIN_SCENE[p], f"{p:6s} SCENE pool byte-identical to HEAD ({sum(len(v) for v in m.SCENE.values())} lines)")
check("sun off the sea puts a wavering light on the ceiling boards" not in C_STUDY.SCENE["any"]
      and C_STUDY.SCENE.get("day") == ["sun off the sea puts a wavering light on the ceiling boards"],
      "study SCENE 'sun off the sea ...' now sits under 'day' (D-0360 part a, moved by J-1898; proven in scripts/_test_j1898_bright_gate_study_scene_day.py)")
check(WD.SCENE_P == 0.25 and WD.RARE_P == 0.08, "SCENE_P is still 0.25 and RARE_P 0.08 (untouched)")
check(all(f"{p}:{t}" in WD._REGISTRY for p, m in MODS.items() for t in m.TARGETS) and len(WD._REGISTRY) == 39,
      f"every target still registers (world_detail._load() keeps all 39; got {len(WD._REGISTRY)})")
check(WD._SCENE["garden"] == {k: list(v) for k, v in C_GARDEN.SCENE.items()}, "world_detail._SCENE['garden'] is exactly the module's SCENE")
check(all("day" in WD._conds(ph, "clear", "summer", "", "calm") and "night" not in WD._conds(ph, "clear", "summer", "", "calm")
          for ph in ("dawn", "day", "dusk")) and "day" not in WD._conds("night", "clear", "summer", "", "calm")
      and "night" in WD._conds("night", "clear", "summer", "", "calm"),
      "premise: _conds() emits 'day' at dawn / day / dusk and 'night' (never 'day') at night")

# ---------------------------------------------------------------------------------------------------------------------
print("\n[2] exact pool: what detail() / extra_pool() / scene_extra() really build, over every condition combination")


class _Spy:
    """Stands in for the `random` module inside world_detail only: neither the rare roll (< RARE_P) nor the SCENE_P gate
    (> SCENE_P, with SCENE_P forced to 1.0) fires, and choice() records the pool it was handed."""
    def __init__(self):
        self.pools: list = []

    def random(self):
        return 0.99

    def choice(self, seq):
        self.pools.append(list(seq))
        return seq[0]


def real_pool(place, kind, target, ph, w, se, t, wi) -> list:
    spy = _Spy()
    WD.random = spy
    p_orig = WD.SCENE_P
    WD.SCENE_P = 1.0
    try:
        if kind == "scene":
            WD.scene_extra(place, ph, w, se, t, wind=wi)
        else:
            WD.detail(place, MODS[place].TARGETS[target]["aliases"][0], ph, w, se, t, wind=wi)
    finally:
        WD.random = random
        WD.SCENE_P = p_orig
    return spy.pools[0] if spy.pools else []


def old_pool_counter(place, kind, target, line, idx, conds) -> Counter:
    if kind == "scene":
        old = rebuild_old_container(C_GARDEN.SCENE, line, idx)
    else:
        old = old_spec(place, target, line, idx)["pools"]
    return Counter(l for c, lines in old.items() if c in conds for l in lines)


for place, kind, target, line, idx in MOVES:     # the target must resolve to its own spec for the draw to mean what it says
    if kind == "target":
        alias = MODS[place].TARGETS[target]["aliases"][0]
        check(WD._match(alias, place) is WD._REGISTRY[f"{place}:{target}"], f"{place} {target}: alias {alias!r} resolves to its own spec at {place}")

SIZES = {}
for place, kind, target, line, idx in MOVES:
    where = f"{place} {target or 'SCENE'}"
    n_night = n_day = bad_night = bad_day = leaked = 0
    ns_new, ns_old, ds = [], [], []
    for ph, w, se, t, wi in itertools.product(PHASES, WEATHERS, SEASONS, TIDES, WINDS):
        conds = WD._conds(ph, w, se, t, wi)
        got = Counter(real_pool(place, kind, target, ph, w, se, t, wi))
        old = old_pool_counter(place, kind, target, line, idx, conds)
        if ph == "night":
            n_night += 1
            leaked += got[line]
            ns_new.append(sum(got.values()))
            ns_old.append(sum(old.values()))
            if got != old - Counter([line]) or not got:
                bad_night += 1
        else:
            n_day += 1
            ds.append(sum(got.values()))
            if got != old:
                bad_day += 1
    SIZES[where] = (min(ns_old), max(ns_old), sum(ns_old) / len(ns_old), min(ns_new), max(ns_new), sum(ns_new) / len(ns_new), min(ds), max(ds))
    check(leaked == 0, f"{where}: night pool never holds the line, in any of {n_night} night combinations (leaked={leaked})")
    check(bad_night == 0, f"{where}: night pool is the old pool minus exactly that line, never empty (bad={bad_night})")
    check(bad_day == 0, f"{where}: dawn / day / dusk pool is the old pool exactly, as a multiset, in all {n_day} combinations (bad={bad_day})")

print("\n  night pool size, old -> new, over every night combination (min / max / mean):")
for where, (omn, omx, oav, nmn, nmx, nav, dmn, dmx) in SIZES.items():
    print(f"    {where:28s} {omn:2d} / {omx:2d} / {oav:5.2f}  ->  {nmn:2d} / {nmx:2d} / {nav:5.2f}     (dawn/day/dusk pool {dmn}-{dmx}, unchanged)")

# the study target is also drawn through extra_pool() (sensorium.py:1052): the same pool, no random at all
n_bad = 0
_sline = MOVES[0][3]
for ph, w, se, t, wi in itertools.product(PHASES, WEATHERS, SEASONS, TIDES, WINDS):
    conds = WD._conds(ph, w, se, t, wi)
    got = Counter(WD.extra_pool("the shelf", ph, w, se, t, wind=wi))
    old = old_pool_counter("study", "target", "shelf_of_kept_things", _sline, 1, conds)
    want = old - Counter([_sline]) if ph == "night" else old
    if got != want:
        n_bad += 1
check(n_bad == 0, f"study shelf_of_kept_things via extra_pool(): night = old minus the line, dawn / day / dusk = old exactly (bad={n_bad})")

# ---------------------------------------------------------------------------------------------------------------------
print("\n[3] real draws: the real detail() / scene_extra(), seeded")
_p_orig = WD.SCENE_P
WD.SCENE_P = 1.0                       # random() never exceeds 1.0: the gate is not under test here
try:
    for place, kind, target, line, idx in MOVES:
        where = f"{place} {target or 'SCENE'}"
        random.seed(1732)
        seen = {ph: Counter() for ph in PHASES}
        for ph in PHASES:
            for w, se, t, wi in itertools.product(WEATHERS, SEASONS, TIDES, WINDS):
                for _ in range(6):
                    if kind == "scene":
                        x = WD.scene_extra(place, ph, w, se, t, wind=wi)
                    else:
                        x = WD.detail(place, MODS[place].TARGETS[target]["aliases"][0], ph, w, se, t, wind=wi)
                    seen[ph][x] += 1
        n = sum(seen["night"].values())
        check(n == 4200 and seen["night"][line] == 0 and seen["night"][""] == 0,
              f"{where}: {n} night draws over every weather x season x tide x wind: the line is never drawn, none empty")
        old_any = rebuild_old_container(container_of(place, kind, target), line, idx).get("any", [])
        check(all(seen["night"][l] > 0 for l in old_any if l != line),
              f"{where}: night still reaches every other old 'any' line ({len(old_any) - 1} of them), none starved")
        for ph in ("dawn", "day", "dusk"):
            check(seen[ph][line] > 0, f"{where}: at {ph:5s} the line is still drawn ({seen[ph][line]} of {sum(seen[ph].values())})")

    # -----------------------------------------------------------------------------------------------------------------
    print("\n[4] ledger: the garden SCENE render row carries the new key by day, not at night")
    for ph, has_day, has_night in (("night", False, True), ("day", True, False), ("dawn", True, False), ("dusk", True, False)):
        LED_ROWS.clear()
        random.seed(5)
        x = WD.scene_extra("garden", ph, "clear", "summer", "", wind="calm", place="garden")
        row = LED_ROWS[-1] if LED_ROWS else {}
        conds = row.get("conds", [])
        check(row.get("line") == x and ("day" in conds) == has_day and ("night" in conds) == has_night,
              f"{ph:5s} garden draw -> ledger conds {conds} pool {row.get('pool')} ('day' {'in' if has_day else 'not in'} conds)")
finally:
    WD.SCENE_P = _p_orig
    WD.random = random

# ---------------------------------------------------------------------------------------------------------------------
print("\n[5] the live stores are untouched")
for p in _WATCH:
    after = _snap(p)
    check(after == _before[p], f"{p.name}: unchanged ({'absent' if after is None else f'{after[0]} bytes'})")

print("\nFAILS =", FAILS)
print("ALL OK" if FAILS == 0 else "SOME CHECKS FAILED")
sys.exit(1 if FAILS else 0)
