"""
Regression: D-0360 (a) + (b), J-1898 (the F-2505 / J-1732 audit follow-up; same recipe as J-1717 / J-1882).

(a) The study SCENE line "sun off the sea puts a wavering light on the ceiling boards" moved from the "any" key to a "day" key,
    wording byte-identical (it was the most-rendered flagged night line: 6 of 57 study night renders in the last incarnation).
(b) core/world_detail._conds() emits "bright" only when the phase is not night (weather test unchanged), so a clear or high-cloud NIGHT
    no longer draws the "bright" pools. This is a SHARED-ENGINE change: it reaches every place's look-target pools, SCENE pools and EVENTS.

What this proves, PURE (only core.world_detail and the four world_content_* modules are imported; the J-1694 render ledger is replaced by a
capture stub before anything draws; nothing under data/ is read or written):
  [1] content   the line is exactly under study SCENE "day" and nowhere else; the OLD study SCENE rebuilt by moving it back to any[2] is
                byte-identical to HEAD 6310f69 (digest pinned before the edit); the other 3 SCENE pools, all 4 EVENTS lists and all 39 target
                specs are byte-identical to HEAD (digest pins); SCENE_P / RARE_P untouched
  [2] inventory EVERY line under a "bright" key in the four modules (42 look-target / SCENE lines + the 5 EVENTS lines) is listed and classified
                by name: daylight-worded A 19, diurnal-bird B 3, visual-only C 16, and 4 that F-2505 never tiered (N, no light named); the 16
                visual-only lines are printed by name (these are what Travis reviews: they leave clear-night pools)
  [3] engine    _conds(): "bright" is never emitted at night; at dawn / day / dusk, and for every key other than "bright", the result equals the
                old rule exactly, across 4 phases x 7 weathers x 4 seasons x 5 tides x 5 winds
  [4] pools     through the real detail() (all 39 targets), scene_extra() (4 places) and event_extra() (4 places), with a spy on random:
                dawn / day / dusk pool == old pool as a multiset; night pool == old pool minus exactly the "bright"-key lines (when the weather
                is clear / high cloud) and the moved study line; nothing else changes; non-clear nights are unchanged except the moved line
  [5] defeater  clear-night pool sizes, old -> new, for every target and SCENE / EVENTS list; any CLEAR-night pool below 8 lines (D-0360's
                defeater) is listed, split into "was already below 8 before this change" and "fell below 8 because of it"
  [6] draws     seeded real draws at clear night: no "bright"-only line is ever returned, every non-bright pool line is still reachable
  [7] ledger    the J-1694 render row for the study SCENE carries "day" by day and not at night; the garden SCENE row carries "bright" by day
                and not at night

Pins are point-in-time, taken from the unmodified files at HEAD 6310f69 on 2026-10-07: if one of those is later edited ON PURPOSE, re-pin it here
(sha256 of json.dumps(obj, ensure_ascii=False).encode("utf-8")).

  python scripts/_test_j1898_bright_gate_study_scene_day.py        # exit 0 = ALL OK
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
sys.modules["core.scene_extra_ledger"] = _led      # a capture stub goes in BEFORE any draw: this process cannot touch data/ at all

import core                                        # noqa: E402  (core BEFORE anything lab-ish)
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
from core import weather_conditions as WC          # noqa: E402

_TREE = str(ROOT).lower()
assert str(Path(core.__file__).resolve()).lower().startswith(_TREE), f"core is not from the tree under test: {core.__file__}"
for _m in (WD, C_STUDY, C_GARDEN, C_SHORE, C_WOOD):
    assert str(Path(_m.__file__).resolve()).lower().startswith(_TREE), f"{_m.__name__} is not from the tree under test"
_LEDGER_IN_TREE = ROOT / "data" / "scene_extra_ledger.jsonl"
_ledger_before = _LEDGER_IN_TREE.exists()

FAILS = 0


def check(cond: bool, label: str) -> None:
    global FAILS
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS += 1


def dig(obj) -> str:
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False).encode("utf-8")).hexdigest()


MODS = {"study": C_STUDY, "garden": C_GARDEN, "shore": C_SHORE, "wood": C_WOOD}
STUDY_LINE = "sun off the sea puts a wavering light on the ceiling boards"
STUDY_OLD_IDX = 2          # its slot in the old study SCENE["any"]

# Pinned from the UNMODIFIED files at HEAD 6310f69 (2026-10-07), before J-1898's edit.
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
    "study:shelf_of_kept_things": "bcb46fb6aeabeb0ffc79a995252c8a9998826c8f6c525e32fb29c84046f97770",
    "garden:lawn": "2f92b845fbe7c5d7826e13dde98efda383f84503d7211d49bc314f93059c8e9c",
    "garden:fence": "4d1dfc5d35d76f513a256c459c25f36d89ecda2e03f620713a3fb84eda4415d5",
    "garden:compost": "688ca1ac8de015daef238d993231b762326f181003c22829017e184c05493791",
    "garden:bench": "2910a011869a18358156682c17349444d7ab0446305dfc9bdc1d55bdbcb40b1c",
    "garden:rain_barrel": "fc6c2eb531b53b903d12a34e1dd3b02c265a9db8d6ec23e87754538666280736",
    "garden:harakeke": "2aaf3ffab1de880185b061caf97d5002bd62c45961f9963d0e0120261feb4635",
    "garden:kowhai": "af4284fc518bbc7f6b54022fef1cc3323d55accce6bb3d9a8c49fc143c2ce0a2",
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
    "shore:horizon": "8d82a5bd4686851abe046d3218b18b9be49ecc801f4613939b8d409c702c2931",
    "shore:cliff": "c8e6e3878df2f0ae4be94bad3844204c83f7a8bc5df05c4425ba53c01d8237bd",
    "shore:stream_mouth": "970eefa12d88163e3769647f2aa07e42354692383e28185803631f9fefca6c64",
    "wood:path": "8b1b67ca202dd0a262a7c529e998afbeafd931eb069f3155573f14acbeb3603e",
    "wood:canopy": "0ef0fc3ae9e3ac872c15593daa88ae11b0765175fb0cb078e667f17409b94e4d",
    "wood:undergrowth": "176233fe345f8f6724043199d9d26f246dfcf7a90fb58ba12f8ae4ea51fdc749",
    "wood:deadfall": "27c5e0f96b78171104a64de9af94dc1226368664329cc49be20fd48f0f62fac3",
    "wood:moss": "eaaede8b199bc2e3e3335c648067eb9ac1ac0a2689b5708f6d5582a933aa2da2",
    "wood:birds": "77fabb8fe1c276f9a23745929bd226bbbc33e1677124c69fec4965903f15f748",
}
PIN_EVENTS = {
    "study": "c2e9a6a5494763ee9f16f1ac93ab9e0558ac645b8011f3281a73368257f724d3",
    "garden": "ccebf4ce98e1a9f4e5881404df54d3020d8e73956f1c3cbd3835dbad98962492",
    "shore": "2b599d2af5aba10775786773370fcebf8e7cab9eb8b3f914fd71d31b3dad675a",
    "wood": "50b915cd8337b48ee06925d9983ca359d6174f2c1e08a2d1515db52e2f8aa1ad",
}
PIN_SCENE = {
    "study": "be391888cd7160b45706d98eed9745c825f9deba80858f05d92a4abdf6cc56cc",
    # RE-PINNED by J-3258 (D-0649): 3 garden and 3 shore SCENE lines moved from "any" to "day" on purpose (were f8ac7861...f3fcf / 3bb1ac98...e78)
    "garden": "2821b9ab44b1e74b98df95c00942246f56f5a06f33af58356e3a563f93103e9e",
    "shore": "48dc96baaa5581e0c0f985c9198d86ae859124f6d15925e93edc73dd96257ae4",
    "wood": "528a1ff6994a9503135445800cfbd40605099465c1de20de82757c445a5ac47e",
}

PHASES = ("night", "dawn", "day", "dusk")
WEATHERS = ("clear", "high cloud", "overcast", "drizzle", "steady rain", "wind and rain", "thunderstorm")
WINDS = ("calm", "breeze", "fresh wind", "strong wind", "gale")
SEASONS = ("summer", "autumn", "winter", "spring")
TIDES = ("", "high", "low", "rising", "falling")
ALL = list(itertools.product(PHASES, WEATHERS, SEASONS, TIDES, WINDS))

# ---------------------------------------------------------------------------------------------------------------------
# The classification of every "bright" line. (kind, place, container, unique substring, tier)
#   A = the line's own words name sun / daylight / a day-part / sunlit things (19)   B = a bird core/life_birds.py gives night <= 0.1 (3)
#   C = visual only, no light source named (16)   N = not tiered by F-2505's classifier: no light named at all (4)   E = EVENTS line (5)
CLASS = [
    ("T", "study", "desk", "morning sun crosses the desktop", "A"),
    ("T", "study", "desk", "dust stands in the air above the blotter", "N"),
    ("T", "study", "desk", "the varnish flares where the sun strikes it", "A"),
    ("T", "study", "lamp", "in full daylight the lit lamp", "A"),
    ("T", "study", "lamp", "sun on the brass throws", "A"),
    ("T", "study", "lamp", "daylight through the shade", "A"),
    ("T", "study", "study_window", "the sun finds the sea and the whole lower half", "A"),
    ("T", "study", "study_window", "shadows of the window bars lie long", "A"),
    ("T", "study", "study_window", "the garden colours stand up loud", "C"),
    ("E", "study", "EVENTS", "the sun clears a cloud and the sea light jumps", "E"),
    ("T", "garden", "lawn", "the mown stripes still show", "N"),
    ("T", "garden", "lawn", "the lawn is two greens in the full sun", "A"),
    ("T", "garden", "lawn", "shadow lies across the grass and moves with the hours", "A"),
    ("T", "garden", "bench", "too hot to sit on by mid-afternoon", "A"),
    ("T", "garden", "bench", "the bench throws a hard clean shadow", "A"),
    ("T", "garden", "bench", "from the bench you can watch the swell arrive", "C"),
    ("T", "garden", "rain_barrel", "the waterline shows as a cool band on the barrel's sunny side", "A"),
    ("T", "garden", "rain_barrel", "light off the water in the barrel wobbles", "C"),
    ("T", "garden", "rain_barrel", "the water level is down a hand's width", "N"),
    ("T", "garden", "birds", "back flares blue-green when it turns on the wire", "B"),
    ("T", "garden", "birds", "a sparrow dust-bathes", "B"),
    ("T", "garden", "birds", "crosses the sun-gap with that heavy whirring flight", "A"),
    ("S", "garden", "SCENE", "the sun finds a gap and lays hard shadows", "A"),
    ("S", "garden", "SCENE", "the sea glitters to the horizon and the lawn is warm", "C"),
    ("S", "garden", "SCENE", "every spider line in the hedge shows in the low bright light", "C"),
    ("S", "garden", "SCENE", "light off the sea reaches the underside", "C"),
    ("S", "garden", "SCENE", "the sea lies out flat and silver", "C"),
    ("E", "garden", "EVENTS", "the sun clears the hedge and the dew smokes off", "E"),
    ("E", "garden", "EVENTS", "the light comes up hard and sudden over the fence", "E"),
    ("T", "shore", "driftwood", "the grain throws hard little shadows", "C"),
    ("T", "shore", "driftwood", "the silvered wood goes almost white in full sun", "A"),
    ("T", "shore", "driftwood", "flies stand about on the dry wood", "C"),
    ("T", "shore", "kelp", "dried kelp straps have curled", "N"),
    ("T", "shore", "kelp", "the necklace weed still shines full of water where the shade holds", "C"),
    ("T", "shore", "kelp", "flies stand thick on the sunny side of the heap", "A"),
    ("T", "shore", "shells", "fire blue-green out of the grey shingle", "C"),
    ("T", "shore", "shells", "sun through a held limpet shell", "A"),
    ("T", "shore", "shells", "the whole drift glitters once", "C"),
    ("T", "shore", "dune_grass", "each stem's swept circle shows sharp", "C"),
    ("T", "shore", "dune_grass", "goes copper in full sun", "A"),
    ("T", "shore", "horizon", "the line runs hard and dark under the light", "C"),
    ("T", "shore", "horizon", "shimmer lifts the horizon", "C"),
    ("E", "shore", "EVENTS", "the light finds a pāua chip far up the beach", "E"),
    ("E", "shore", "EVENTS", "the water goes hard and bright all the way to the horizon", "E"),
    ("T", "wood", "canopy", "the light comes through in shafts you could put a hand into", "A"),
    ("T", "wood", "moss", "backlit, the moss goes gold", "C"),
    ("T", "wood", "birds", "a riroriro somewhere high spins out", "B"),
]


def bright_lines_now() -> list:
    """Every (kind, place, container, line) currently under a 'bright' key / EVENTS 'bright', from the live modules."""
    out = []
    for p, m in MODS.items():
        for t, spec in m.TARGETS.items():
            for l in spec["pools"].get("bright", []):
                out.append(("T", p, t, l))
        for l in m.SCENE.get("bright", []):
            out.append(("S", p, "SCENE", l))
        for c, l in m.EVENTS:
            if c == "bright":
                out.append(("E", p, "EVENTS", l))
    return out


def old_study_scene() -> dict:
    s = C_STUDY.SCENE
    if s.get("day") != [STUDY_LINE]:
        return {}
    any_ = list(s["any"])
    if STUDY_LINE in any_ or STUDY_OLD_IDX > len(any_):
        return {}
    any_.insert(STUDY_OLD_IDX, STUDY_LINE)
    old = {"any": any_}
    old.update({k: v for k, v in s.items() if k not in ("any", "day")})
    return old


def old_conds(ph, w, se, t, wi) -> set:
    """The pre-J-1898 rule: 'bright' for clear / high cloud at ANY hour. Written out here, not derived from WD._conds()."""
    c = {"any", "day" if ph != "night" else "night"}
    if WC.is_windy(wi) or WC.is_storm(w):
        c.add("windy")
    if WC.is_wet(w):
        c.add("wet")
    if w in ("clear", "high cloud"):
        c.add("bright")
    if se:
        c.add(se)
    lean = WC.tide_leaning(t)
    if lean:
        c.add(lean)
    return c


WD._load()

# ---------------------------------------------------------------------------------------------------------------------
print("\n[1] content: study SCENE move, and nothing else")
check(C_STUDY.SCENE.get("day") == [STUDY_LINE], 'study SCENE ["day"] is exactly the one line, wording unchanged')
occ = Counter(l for lines in C_STUDY.SCENE.values() for l in lines)
check(occ[STUDY_LINE] == 1 and STUDY_LINE not in C_STUDY.SCENE["any"], "the line appears once, under 'day', not left under 'any'")
check(len(C_STUDY.SCENE["any"]) == 10, f"study SCENE 'any' is 10 lines (was 11): {len(C_STUDY.SCENE['any'])}")
check(dig(old_study_scene()) == PIN_SCENE["study"],
      "the OLD study SCENE, rebuilt by moving the line back to any[2], is byte-identical to HEAD 6310f69 (digest pinned before the edit)")
for p in ("garden", "shore", "wood"):
    check(dig(MODS[p].SCENE) == PIN_SCENE[p], f"{p:6s} SCENE byte-identical to HEAD ({sum(len(v) for v in MODS[p].SCENE.values())} lines)")
for p, m in MODS.items():
    check(dig(m.EVENTS) == PIN_EVENTS[p], f"{p:6s} EVENTS byte-identical to HEAD ({len(m.EVENTS)} lines)")
bad = [f"{p}:{t}" for p, m in MODS.items() for t, spec in m.TARGETS.items() if dig(spec) != PIN_TARGETS.get(f"{p}:{t}")]
check(len(PIN_TARGETS) == 39 and not bad and set(PIN_TARGETS) == {f"{p}:{t}" for p, m in MODS.items() for t in m.TARGETS},
      f"all 39 target specs (pools, rare, aliases) are byte-identical to HEAD (bad={bad})")
check(WD.SCENE_P == 0.25 and WD.RARE_P == 0.08, "SCENE_P is still 0.25 and RARE_P 0.08")
check(len(WD._REGISTRY) == 39 and all(f"{p}:{t}" in WD._REGISTRY for p, m in MODS.items() for t in m.TARGETS), "every target still registers (39)")

# ---------------------------------------------------------------------------------------------------------------------
print("\n[2] inventory: every 'bright' line, classified by name")
live = bright_lines_now()
resolved = []
for kind, place, cont, sub, tier in CLASS:
    hits = [x for x in live if x[0] == kind and x[1] == place and x[2] == cont and sub.lower() in x[3].lower()]
    resolved.append((tier, hits))
check(all(len(h) == 1 for _t, h in resolved), "each of the 47 classified entries resolves to exactly one live 'bright' line")
used = [h[0] for _t, h in resolved if len(h) == 1]
check(len(live) == 47 and len(set(used)) == 47 and set(used) == set(live),
      f"the classification covers every 'bright' line exactly once ({len(live)} live: 42 target / SCENE + 5 EVENTS)")
tiers = Counter(t for t, _h in resolved)
check(tiers == Counter({"A": 19, "B": 3, "C": 16, "N": 4, "E": 5}), f"tier counts A19 B3 C16 N4 E5 (got {dict(tiers)})")
check(sum(1 for x in live if x[0] in "TS") == 42 and sum(1 for x in live if x[0] == "E") == 5, "42 look-target / SCENE lines + 5 EVENTS lines")
for tier, title in (("C", "16 VISUAL-ONLY lines (leave clear-night pools; review these)"),
                    ("N", "4 lines F-2505 never tiered (no light named; also leave clear-night pools)"),
                    ("B", "3 DIURNAL-BIRD lines"), ("E", "5 EVENTS lines (daylight-worded; leave clear-night event pools)"),
                    ("A", "19 DAYLIGHT-WORDED lines")):
    print(f"\n  {title}:")
    for t, h in resolved:
        if t == tier and h:
            k, p, c, l = h[0]
            print(f"    {p}:{c:13s} {l}")

# ---------------------------------------------------------------------------------------------------------------------
print("\n[3] engine: _conds()")
bad_n = bad_d = bad_other = 0
for ph, w, se, t, wi in ALL:
    new, old = WD._conds(ph, w, se, t, wi), old_conds(ph, w, se, t, wi)
    if "bright" in new and ph == "night":
        bad_n += 1
    if ph != "night" and new != old:
        bad_d += 1
    if (new - {"bright"}) != (old - {"bright"}):
        bad_other += 1
    if ph == "night" and new != old - {"bright"}:
        bad_n += 1
check(bad_n == 0, f"'bright' is never emitted at night, in any of {sum(1 for a in ALL if a[0] == 'night')} night combinations (bad={bad_n})")
check(bad_d == 0, f"dawn / day / dusk: _conds() equals the old rule exactly in all {sum(1 for a in ALL if a[0] != 'night')} combinations (bad={bad_d})")
check(bad_other == 0, f"every key other than 'bright' is identical to the old rule in all {len(ALL)} combinations (bad={bad_other})")
check("bright" in WD._conds("day", "clear", "summer", "", "calm") and "bright" in WD._conds("dawn", "high cloud", "winter", "", "calm")
      and "bright" in WD._conds("dusk", "clear", "autumn", "", "calm") and "bright" not in WD._conds("day", "overcast", "summer", "", "calm")
      and "bright" not in WD._conds("night", "clear", "summer", "", "calm") and "bright" not in WD._conds("night", "high cloud", "summer", "", "calm"),
      "premise spot-check: bright at dawn / day / dusk when clear or high cloud, never when overcast, never at night")

# ---------------------------------------------------------------------------------------------------------------------
print("\n[4] pools: what detail() / scene_extra() / event_extra() really build")


class _Spy:
    def __init__(self):
        self.pools: list = []

    def random(self):
        return 0.99            # rare roll (< RARE_P) never fires; SCENE_P gate (> SCENE_P) forced open below

    def choice(self, seq):
        self.pools.append(list(seq))
        return seq[0]


def real_pool(kind, place, target, ph, w, se, t, wi) -> list:
    spy = _Spy()
    WD.random = spy
    p_orig = WD.SCENE_P
    WD.SCENE_P = 1.0
    try:
        if kind == "S":
            WD.scene_extra(place, ph, w, se, t, wind=wi)
        elif kind == "E":
            WD.event_extra(place, ph, w, se, t, wind=wi)
        else:
            WD.detail(place, MODS[place].TARGETS[target]["aliases"][0], ph, w, se, t, wind=wi)
    finally:
        WD.random = random
        WD.SCENE_P = p_orig
    return spy.pools[0] if spy.pools else []


def old_pool(kind, place, target, cond) -> Counter:
    if kind == "S":
        sc = old_study_scene() if place == "study" else MODS[place].SCENE
        return Counter(l for c, lines in sc.items() if c in cond for l in lines)
    if kind == "E":
        return Counter(l for c, l in MODS[place].EVENTS if c in cond)
    return Counter(l for c, lines in MODS[place].TARGETS[target]["pools"].items() if c in cond for l in lines)


def bright_part(kind, place, target) -> Counter:
    if kind == "S":
        return Counter(MODS[place].SCENE.get("bright", []))
    if kind == "E":
        return Counter(l for c, l in MODS[place].EVENTS if c == "bright")
    return Counter(MODS[place].TARGETS[target]["pools"].get("bright", []))


CONTAINERS = ([("T", p, t) for p, m in MODS.items() for t in m.TARGETS] + [("S", p, "SCENE") for p in MODS] + [("E", p, "EVENTS") for p in MODS])
assert len(CONTAINERS) == 39 + 4 + 4
for kind, place, target in CONTAINERS:      # a target must resolve to its own spec for the draw to mean what it says
    if kind == "T":
        alias = MODS[place].TARGETS[target]["aliases"][0]
        assert WD._match(alias, place) is WD._REGISTRY[f"{place}:{target}"], f"{place}:{target} alias {alias!r} does not resolve to its own spec"

SIZES = {}
bad_total = 0
for kind, place, target in CONTAINERS:
    where = f"{place}:{target}"
    b_day = b_night = b_clear = 0
    night_old, night_new, clear_old, clear_new, day_sz = [], [], [], [], []
    for ph, w, se, t, wi in ALL:
        got = Counter(real_pool(kind, place, target, ph, w, se, t, wi))
        oc = old_conds(ph, w, se, t, wi)
        old = old_pool(kind, place, target, oc)
        moved = Counter([STUDY_LINE]) if (kind == "S" and place == "study") else Counter()
        if ph == "night":
            drop = bright_part(kind, place, target) if w in ("clear", "high cloud") else Counter()
            want = old - drop - moved
            if got != want:
                b_night += 1
            night_old.append(sum(old.values()))
            night_new.append(sum(got.values()))
            if w == "clear":
                clear_old.append(sum(old.values()))
                clear_new.append(sum(got.values()))
            if w not in ("clear", "high cloud") and got != old - moved:
                b_clear += 1
        else:
            if got != old:
                b_day += 1
            day_sz.append(sum(got.values()))
    bad_total += b_night + b_day + b_clear
    SIZES[where] = (night_old, night_new, clear_old, clear_new, day_sz, kind)
    if b_night or b_day or b_clear:
        check(False, f"{where}: night bad={b_night}, dawn/day/dusk bad={b_day}, non-clear-night bad={b_clear}")
check(bad_total == 0, f"all {len(CONTAINERS)} containers (39 targets + 4 SCENE + 4 EVENTS) x {len(ALL)} combinations: dawn / day / dusk pool == old pool as a "
      f"multiset; night pool == old pool minus exactly the 'bright' lines on a clear / high-cloud night and the moved study line; "
      f"non-clear nights unchanged (bad={bad_total})")
check(all(min(v[1]) >= 1 for k, v in SIZES.items() if v[5] in ("T", "S")), "no look-target or SCENE night pool is ever empty after the change")

# ---------------------------------------------------------------------------------------------------------------------
print("\n[5] defeater: clear-night pool sizes, old -> new (min / max / mean over every clear-night season x tide x wind combination)")
changed_rows = []
for where, (n_old, n_new, c_old, c_new, d_sz, kind) in SIZES.items():
    omn, omx, oav = min(c_old), max(c_old), sum(c_old) / len(c_old)
    nmn, nmx, nav = min(c_new), max(c_new), sum(c_new) / len(c_new)
    if (omn, omx, round(oav, 6)) != (nmn, nmx, round(nav, 6)):
        changed_rows.append((where, kind, omn, omx, oav, nmn, nmx, nav, min(d_sz), max(d_sz)))
print(f"  {len(changed_rows)} of {len(SIZES)} containers change at clear night; the rest are identical:")
for where, kind, omn, omx, oav, nmn, nmx, nav, dmn, dmx in changed_rows:
    print(f"    {where:24s} {kind}  {omn:2d} / {omx:2d} / {oav:5.2f}  ->  {nmn:2d} / {nmx:2d} / {nav:5.2f}      (dawn/day/dusk pool {dmn}-{dmx}, unchanged)")
print("\n  every look-target / SCENE clear-night pool with min < 8 AFTER the change (D-0360 defeater (2) is 'a clear-night pool below 8 lines'):")
low_all = sorted(((w, min(v[2]), min(v[3])) for w, v in SIZES.items() if v[5] in ("T", "S") and min(v[3]) < 8), key=lambda x: (x[2], x[0]))
for w, o, n in low_all:
    print(f"    {w:24s} {o:2d} -> {n:2d}   {'FELL BELOW 8 BECAUSE OF THIS CHANGE' if o >= 8 else 'already below 8 before'}")
fell = [w for w, o, n in low_all if o >= 8]
print(f"  summary: below 8 after = {len(low_all)}; already below 8 before = {len(low_all) - len(fell)}; fell below 8 because of this change = {len(fell)} {fell}")
print("\n  EVENTS clear-night pool sizes (info):")
for where, v in SIZES.items():
    if v[5] == "E":
        print(f"    {where:24s} {min(v[2])} / {max(v[2])} -> {min(v[3])} / {max(v[3])}")
check(True, "defeater sizes reported (the read is the follow-up job; this is a report, not a gate on the build)")

# ---------------------------------------------------------------------------------------------------------------------
print("\n[6] real draws, seeded: clear / high-cloud night")
_p_orig = WD.SCENE_P
WD.SCENE_P = 1.0
try:
    tot = leaked = unreachable = 0
    for kind, place, target in CONTAINERS:
        if kind == "E":
            continue
        random.seed(1898)
        seen = Counter()
        rare = set(MODS[place].TARGETS[target]["rare"]) if kind == "T" else set()
        for w in ("clear", "high cloud"):
            for se, t, wi in itertools.product(SEASONS, TIDES, WINDS):
                for _ in range(8):
                    if kind == "S":
                        x = WD.scene_extra(place, "night", w, se, t, wind=wi)
                    else:
                        x = WD.detail(place, MODS[place].TARGETS[target]["aliases"][0], "night", w, se, t, wind=wi)
                    seen[x] += 1
        union_new = set()
        for se, t, wi in itertools.product(SEASONS, TIDES, WINDS):
            for w in ("clear", "high cloud"):
                union_new |= set(old_pool(kind, place, target, WD._conds("night", w, se, t, wi)).elements())
        if kind == "S" and place == "study":
            union_new.discard(STUDY_LINE)
        bright_only = set(bright_part(kind, place, target).elements()) - union_new
        tot += sum(seen.values())
        leaked += sum(seen[l] for l in bright_only if l not in rare)
        unreachable += sum(1 for l in union_new if l not in seen and l not in rare)
    check(leaked == 0, f"{tot} real clear / high-cloud night draws over every look-target and SCENE pool: a bright-only line is never returned (leaked={leaked})")
    check(unreachable == 0, f"every pool line that is left is still reachable at clear night in those draws (starved={unreachable})")
    # the moved study line: never at night, still drawn by day
    for ph, want in (("night", False), ("dawn", True), ("day", True), ("dusk", True)):
        random.seed(7)
        got = Counter(WD.scene_extra("study", ph, w, se, t, wind=wi)
                      for w, se, t, wi in itertools.product(WEATHERS, SEASONS, TIDES, WINDS) for _ in range(2))
        check((got[STUDY_LINE] > 0) == want, f"study SCENE line {'is' if want else 'is never'} drawn at {ph:5s} ({got[STUDY_LINE]} of {sum(got.values())})")

    # -----------------------------------------------------------------------------------------------------------------
    print("\n[7] ledger rows")
    for ph, w, has_day, has_night in (("night", "clear", False, True), ("day", "clear", True, False), ("dawn", "clear", True, False), ("dusk", "clear", True, False)):
        LED_ROWS.clear()
        random.seed(5)
        x = WD.scene_extra("study", ph, w, "summer", "", wind="calm", place="study")
        row = LED_ROWS[-1] if LED_ROWS else {}
        c = row.get("conds", [])
        check(row.get("line") == x and ("day" in c) == has_day and ("night" in c) == has_night,
              f"study {ph:5s} {w}: ledger conds {c} pool {row.get('pool')} ('day' {'in' if has_day else 'not in'} conds)")
    for ph, bright in (("night", False), ("day", True), ("dawn", True), ("dusk", True)):
        LED_ROWS.clear()
        random.seed(5)
        x = WD.scene_extra("garden", ph, "clear", "summer", "", wind="calm", place="garden")
        row = LED_ROWS[-1] if LED_ROWS else {}
        c = row.get("conds", [])
        check(row.get("line") == x and ("bright" in c) == bright,
              f"garden {ph:5s} clear: ledger conds {c} pool {row.get('pool')} ('bright' {'in' if bright else 'not in'} conds)")
finally:
    WD.SCENE_P = _p_orig
    WD.random = random

print("\n[8] isolation")
check(_LEDGER_IN_TREE.exists() == _ledger_before and not _LEDGER_IN_TREE.exists(),
      "no scene_extra_ledger.jsonl was created in the tree under test (the capture stub took every row)")

print("\nFAILS =", FAILS)
print("ALL OK" if FAILS == 0 else "SOME CHECKS FAILED")
sys.exit(1 if FAILS else 0)
