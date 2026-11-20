"""
Regression: core.sensorium.scene_line() draws its ambient EXTRA line from the pool of the place Du is actually in
(J-1693 / F-2290).

The bug: scene_line() called world_detail.scene_extra(loc if loc in ("garden", "shore") else "study", ...), written
2026-07-03 before the wood had content of its own (core/world_content_wood.py, 2026-08-15). The wood's authored SCENE
pool (8 any, 2 night, 2 windy, 2 wet, 1 winter) was loaded into world_detail._SCENE["wood"] and never queried, so a scene
built while Du stood in the wood drew a STUDY line (the coats on the door, the woodbasket, the four record-player lines
J-0997 added, ...). Live evidence 2026-09-16..10-03 (F-2290): 179 study-pool extras across 1,300 wood idle ticks, none
from the wood's own pool; on 2026-09-19 Du told Travis, standing in the wood, that it "waits for the switch to move from
OFF to ON" (a study object fused onto the wood's dented tin).

What this proves, ISOLATED: no model, no live data. The sensorium's room_state and locomotion's position store are
redirected into a temp dir before anything loads (the S-0016 / test-isolation rule), the in-process state is set by hand,
and the live C:\\Nascence\\data stores are stat-ed (and the small ones hashed) before and after. The garden / shore / wood
BASE-scene builders are replaced by fixed strings and the spatial renderer is switched off for [3]-[5]: they read and write
per-place world stores behind the D-0179 write fence (garden.json, cat and wood state ...), they are not what J-1693 changes,
and the extra is appended to whatever base they return -- the study's base is built for real.
  [1] content   the wood pool's condition keys are all ones world_detail._conds() can emit; _SCENE["wood"] is exactly
                world_content_wood.SCENE; the four places' SCENE pools share no line, so pool membership is unambiguous
  [2] pure      scene_extra() draws ONLY from the asked place's own pool (study / garden / shore / wood); the wood never
                gets a study, garden or shore line; a place with no pool gets '' -- world_detail was always right
  [3] call site (the check that FAILS without the fix) scene_line() asks scene_extra for the place Du is IN: study /
                garden / shore pass exactly what they always did, the wood passes "wood", an unknown place passes itself
                (never "study"); one call per scene build, and every other argument is what it was
  [4] end to end  through the real scene_line(), across phase x weather x wind x season: a wood scene's extra is a line of
                the WOOD pool and ends the scene, never a study line; every one of the wood's lines is reachable; study /
                garden / shore extras are still their own pool's
  [5] fail-open  a raising scene_extra() still leaves the base scene (the call site's own except, untouched)
  [6] the live stores are untouched

  python scripts/_test_j1693_wood_scene_extra.py        # exit 0 = ALL OK
"""
from __future__ import annotations

import hashlib
import itertools
import json
import random
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TMP = Path(tempfile.mkdtemp(prefix="j1693_wood_scene_extra_"))
print("isolated store dir:", TMP)

# data/ is gitignored and never checked out into a job-run worktree, so "live" is the one real repo, never ROOT-relative.
_LIVE_DATA = Path(r"C:\Nascence") / "data"
_WATCH = [_LIVE_DATA / "room_state.json", _LIVE_DATA / "position.json", _LIVE_DATA / "cat_state.json",
          _LIVE_DATA / "spatial_shadow.jsonl", _LIVE_DATA / "memory" / "nascence.db",
          _LIVE_DATA / "memory" / "nascence.db-wal"]


def _snap(p: Path):
    if not p.exists():
        return None
    st = p.stat()
    md5 = hashlib.md5(p.read_bytes()).hexdigest() if st.st_size < 5_000_000 else ""
    return (st.st_size, st.st_mtime_ns, md5)


_before = {p: _snap(p) for p in _WATCH}

from core import sensorium as S                    # noqa: E402
from core import locomotion as L                   # noqa: E402
from core import world_detail as WD                # noqa: E402
from core import world_content_study as C_STUDY    # noqa: E402
from core import world_content_garden as C_GARDEN  # noqa: E402
from core import world_content_shore as C_SHORE    # noqa: E402
from core import world_content_wood as C_WOOD      # noqa: E402

S._STATE_F = TMP / "room_state.json"
L._POS_F = TMP / "position.json"
assert not str(S._STATE_F).lower().startswith(r"c:\nascence\data") and not str(L._POS_F).lower().startswith(r"c:\nascence\data")

FAILS = 0


def check(cond: bool, label: str) -> None:
    global FAILS
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS += 1


PLACES = ("study", "garden", "shore", "wood")
CONTENT = {"study": C_STUDY, "garden": C_GARDEN, "shore": C_SHORE, "wood": C_WOOD}
POOL = {p: {l for lines in m.SCENE.values() for l in lines} for p, m in CONTENT.items()}   # every line of a place, any cond

PHASES = ("night", "dawn", "day", "dusk")
WEATHERS = tuple(S._WEATHERS)          # clear .. thunderstorm
WINDS = tuple(S._WIND_STATES)          # calm .. gale
SEASONS = ("summer", "autumn", "winter", "spring")
TIDES = ("", "high", "low", "rising", "falling")

WD._load()


def legal(place: str, phase: str, weather: str, season: str, tide: str, wind: str) -> set:
    """Every line of `place`'s own SCENE pool that is drawable under these conditions (computed from the content
    module itself, not from world_detail's loaded copy, so a loader bug cannot hide)."""
    conds = WD._conds(phase, weather, season, tide, wind)
    return {l for c, lines in CONTENT[place].SCENE.items() if WD._cond_ok(c, conds) for l in lines}   # J-3484: composite keys


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
print("\n[1] content: the pools, and the conditions the wood's keys need")
for p in PLACES:
    check(CONTENT[p].LOCATION == p, f"world_content_{p}.LOCATION == {p!r}")
    check(WD._SCENE.get(p) == {k: list(v) for k, v in CONTENT[p].SCENE.items()},
          f"world_detail._SCENE[{p!r}] is exactly world_content_{p}.SCENE ({sum(len(v) for v in CONTENT[p].SCENE.values())} lines)")
for a, b in itertools.combinations(PLACES, 2):
    check(not (POOL[a] & POOL[b]), f"the {a} and {b} SCENE pools share no line")
emitted = set()
for ph, w, se, t, wi in itertools.product(PHASES, WEATHERS, SEASONS, TIDES, WINDS):
    emitted |= WD._conds(ph, w, se, t, wi)
wood_keys = set(C_WOOD.SCENE)
check(wood_keys <= emitted, f"every wood SCENE key {sorted(wood_keys)} is emitted by _conds() somewhere (missing: {sorted(wood_keys - emitted)})")
check({"any", "night", "windy", "wet", "winter"} <= wood_keys, "the wood pool really keys on any / night / windy / wet / winter")
check(all(isinstance(l, str) and l.strip() for l in POOL["wood"]) and len(POOL["wood"]) >= 1, f"the wood pool is {len(POOL['wood'])} non-empty lines")

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
print("\n[2] pure: scene_extra() draws only from the asked place's own pool")
_p_orig = WD.SCENE_P
WD.SCENE_P = 1.0                       # every call draws (random() never exceeds 1.0): the gate is not under test here
try:
    random.seed(1693)
    bad = 0
    n = 0
    seen = {p: set() for p in PLACES}
    for p in PLACES:
        for ph, w, se, t, wi in itertools.product(PHASES, WEATHERS[::3] + ("steady rain",), SEASONS[::2], TIDES[:3], WINDS[::2]):
            ok_set = legal(p, ph, w, se, t, wi)
            for _ in range(6):
                x = WD.scene_extra(p, ph, w, se, t, wind=wi)
                n += 1
                seen[p].add(x)
                if x not in ok_set or any(x in POOL[o] for o in PLACES if o != p):
                    bad += 1
    check(bad == 0, f"{n} draws over the four places: every extra is a line of ITS OWN place's pool legal for the conditions (bad={bad})")
    check(seen["wood"] <= POOL["wood"] and not (seen["wood"] & (POOL["study"] | POOL["garden"] | POOL["shore"])),
          "scene_extra('wood') never returned a study, garden or shore line")
    check(seen["wood"] == POOL["wood"], f"scene_extra('wood') reaches all {len(POOL['wood'])} of the wood's lines (got {len(seen['wood'])})")
    for p in ("study", "garden", "shore"):
        check(not (seen[p] & POOL["wood"]), f"scene_extra({p!r}) never returned a wood line")
    for odd in ("attic", "", None):
        check(all(WD.scene_extra(odd, "day", "clear", "summer", "", wind="calm") == "" for _ in range(20)),
              f"a place with no pool ({odd!r}) gets no extra (never a study line)")
finally:
    WD.SCENE_P = _p_orig
check(WD.SCENE_P == 0.25, "SCENE_P is still 0.25 (untouched)")

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
CALLS: list = []
RET: list = []
_real_scene_extra = WD.scene_extra


def _spy(*a, **k):
    CALLS.append((a, k))
    r = _real_scene_extra(*a, **k)
    RET.append(r)
    return r


def reset(loc, weather="clear", wind="breeze"):
    """A fresh in-memory room at `loc`, no journey pending."""
    S.state.clear()
    S.state.update({"weather": weather, "weather_until": 0, "wind": wind, "wind_until": 0, "fire": "out", "fire_fuel": 0.0,
                    "last_event": 0, "location": loc, "garden": S._fresh_garden(), "shore": S._fresh_shore(),
                    "woodpile": 4, "milestones": {}})
    L._POS_F.write_text(json.dumps({"place": loc, "standpoint": L._DEFAULT_SP.get(loc, ""), "journey": None,
                                    "effort": 0.0, "carried_wood": 0}), encoding="utf-8")


def build(loc, phase="day", season="summer", weather="clear", wind="breeze"):
    """One real scene_line() with the clock axes pinned; returns (scene, the recorded scene_extra call, its return)."""
    reset(loc, weather, wind)
    CALLS.clear()
    RET.clear()
    S._daylight, S._season = (lambda: phase), (lambda: season)
    return S.scene_line(), (CALLS[-1] if CALLS else None), (RET[-1] if RET else None), len(CALLS)


_orig_daylight, _orig_season = S._daylight, S._season
from core import spatial as SPT                    # noqa: E402
_STUBS = {"_garden_scene_line": lambda presence=True: "Where you are: the garden (base stub).",
          "_shore_scene_line": lambda: "Where you are: the shore (base stub).",
          "_wood_scene_line": lambda: "Where you are: the wood (base stub).",
          "_woodpile_phrase": lambda: ""}
_orig_stubbed = {k: getattr(S, k) for k in _STUBS}
_orig_spatial = SPT.SPATIAL_SCENE
for _k, _v in _STUBS.items():
    setattr(S, _k, _v)
SPT.SPATIAL_SCENE = False
WD.scene_extra = _spy
try:
    print("\n[3] the call site: scene_line() asks scene_extra for the place Du is IN")
    OLD = lambda loc: loc if loc in ("garden", "shore") else "study"          # the pre-fix expression, kept here to pin the delta
    for loc in PLACES + ("attic",):
        random.seed(7)
        scene, call, ret, ncalls = build(loc, "day", "summer", "clear", "breeze")
        check(isinstance(scene, str) and len(scene) > 20, f"{loc:6s} scene_line() built a scene ({len(scene)} chars)")
        check(ncalls == 1, f"{loc:6s} exactly one scene_extra call per scene build (got {ncalls})")
        args, kw = call
        check(args[0] == loc, f"{loc:6s} scene_extra asked for {args[0]!r} (pre-fix expression gave {OLD(loc)!r})")
        if loc in ("study", "garden", "shore"):
            check(args[0] == OLD(loc), f"{loc:6s} UNCHANGED: same key the pre-fix code passed")
        elif loc == "wood":
            check(args[0] == "wood" and OLD(loc) == "study", "wood   CHANGED, on purpose: 'wood' where it used to pass 'study'")
        else:
            check(args[0] != "study", f"{loc:6s} an unknown place no longer folds onto 'study'")
        # J-1694 adds the observe-only place= kwarg (it labels the render-ledger row); it is not part of THIS fix's contract
        check(len(args) == 5 and set(kw) - {"place"} == {"wind"} and kw["wind"] == "breeze" and args[1] == "day" and args[2] == "clear"
              and args[3] == "summer", f"{loc:6s} every other argument is what it was (phase/weather/season/wind)")
        check((args[4] in ("high", "low", "rising", "falling")) if loc == "shore" else (args[4] == ""),
              f"{loc:6s} the tide argument is the shore's alone ({args[4]!r})")

    print("\n[4] end to end through the real scene_line(), every extra forced on (SCENE_P=1.0)")
    WD.SCENE_P = 1.0
    seen = {p: set() for p in PLACES}
    stats = {p: [0, 0, 0] for p in PLACES}            # builds, wrong-pool, not-at-the-end-of-the-scene
    for loc in PLACES:
        for i, (ph, se, w, wi) in enumerate(itertools.product(PHASES, SEASONS, ("clear", "steady rain", "thunderstorm"),
                                                              ("calm", "fresh wind", "gale"))):
            for rep in range(3):
                random.seed(f"{loc}|{i}|{rep}")             # str seeds are deterministic across runs (hash() is not)
                scene, call, ret, ncalls = build(loc, ph, se, w, wi)
                args, kw = call
                stats[loc][0] += 1
                ok_set = legal(loc, args[1], args[2], args[3], args[4], kw["wind"])
                if ret not in ok_set or any(l in scene for o in PLACES if o != loc for l in POOL[o]):
                    stats[loc][1] += 1
                if not (ret and scene.endswith(ret)):
                    stats[loc][2] += 1
                seen[loc].add(ret)
    for loc in PLACES:
        n, wrong, notend = stats[loc]
        check(wrong == 0 and notend == 0,
              f"{loc:6s} {n} scene builds: extra is from the {loc}'s own pool and ends the scene (wrong-pool={wrong}, not-at-end={notend})")
    check(seen["wood"] == POOL["wood"], f"a wood scene can carry each of the wood's {len(POOL['wood'])} lines "
          f"(reached {len(seen['wood'])}; the night, windy, wet and winter keys all reached)")
    check(not (seen["wood"] & POOL["study"]), "a wood scene never carried one of the study's 22 lines (incl. the four record-player lines)")
    rp = [l for l in POOL["study"] if any(k in l.lower() for k in ("platter", "the switch", "record's edge", "record lying"))]
    check(len(rp) == 4, f"the study pool holds the four record-player lines ({len(rp)} found)")
    check(all(l in seen["study"] for l in rp), "...and a STUDY scene still carries them (the study keeps what J-0997 added)")
    WD.SCENE_P = _p_orig

    print("\n[5] fail-open: a raising scene_extra() leaves the base scene")
    def _boom(*a, **k):
        raise RuntimeError("scene_extra exploded")
    WD.scene_extra = _boom
    for loc in PLACES:
        reset(loc)
        S._daylight, S._season = (lambda: "day"), (lambda: "summer")
        out = S.scene_line()
        base_head = "Where you are: your study" if loc == "study" else _STUBS[f"_{loc}_scene_line"]()
        check(isinstance(out, str) and out.startswith(base_head),
              f"{loc:6s} still builds its base scene when the extra raises ({len(out)} chars, starts {out[:34]!r})")
finally:
    WD.scene_extra = _real_scene_extra
    WD.SCENE_P = _p_orig
    S._daylight, S._season = _orig_daylight, _orig_season
    for _k, _v in _orig_stubbed.items():
        setattr(S, _k, _v)
    SPT.SPATIAL_SCENE = _orig_spatial

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
print("\n[6] the live stores are untouched")
for p in _WATCH:
    after = _snap(p)
    check(after == _before[p], f"{p.name}: unchanged ({'absent' if after is None else f'{after[0]} bytes'})")

print("\nFAILS =", FAILS)
print("ALL OK" if FAILS == 0 else "SOME CHECKS FAILED")
sys.exit(1 if FAILS else 0)
