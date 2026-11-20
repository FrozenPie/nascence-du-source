"""
Regression/verification: spatial_perception P3 LIVE for the study -- render() takes the nearness-said fire and
cat clauses behind one flag (J-2480, D-0501, Travis 2026-10-28).

What this proves, ISOLATED (no model, no live data written):
  [1] flag off   render() is BYTE-IDENTICAL to the pre-J-2480 renderer (commit 0e95fce9's core/spatial.py, loaded
                 side by side) on 200 seeded renders across every study standpoint x fire x cat x weather
  [2] flag on    the same 200 seeded renders differ ONLY in the fire/embers and cat clauses: same standpoint, same
                 clause count, every other clause verbatim; the fire clause keeps its sector + distance word, the cat
                 clause keeps her place + sector; some pairs really do differ (fire and cat both)
  [3] no readout no digit, band name, gauge word or reach word in any live line (D-0434); the reach-set is computed
                 and logged but no reach feature is ever newly named in the line (world answers, never leads)
  [4] thermal    the warmth said agrees with core/thermal's OWN felt heat at the same standpoint: the clause tier is
                 monotone in thermal._fire_term (D-0501's defeater), 'heat full on you' only where thermal's share
                 >= 0.95, hearth distance == thermal's own distance, and thermal.field_at is warmer where the line
                 says warmer
  [5] rotation   every new pool rotates (no single fixed string) -- near/mid/far fire and embers pools each produce
                 >= 2 distinct clauses over 60 renders, and the D-0501-graded wording is in every pool
  [6] no growth  the clause count never changes (a replacement, never an addition): D-0501's third defeater
  [7] not here   fire out -> no fire clause; no cat -> no cat clause; lap-cat in the chair -> the lap clause untouched
  [8] scope      garden/shore/wood renders are byte-identical with the flag on (DEPTH_SHADOW_ROOMS = study only)
  [9] shadow     spatial.shadow() in the lab sandbox: the P0 row's `rendered` is the LIVE line, the P3 row keeps the
                 pair (scene = P2 line, depth_line = the very line render() returned, live=True); flag off -> live=False
                 and rendered == scene
  [10] fail-open an overlay that raises leaves render() returning the P2 line unchanged
  [11] canary    live stores untouched (size + mtime + hash)

  python scripts/_test_spatial_depth_live_J2480.py        # exit 0 = ALL OK
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import random
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core                                                       # noqa: E402  (core BEFORE lab_env)
assert Path(core.__file__).resolve().is_relative_to(ROOT.resolve()), f"core resolved outside this tree: {core.__file__}"
from core import profile                                          # noqa: E402
from core import spatial as SPT                                   # noqa: E402
from core import thermal as TH                                    # noqa: E402
from core import locomotion as L                                  # noqa: E402

sys.path.append(str(Path.home() / ".claude" / "skills" / "job-queue"))
import lab_env                                                    # noqa: E402
assert Path(core.__file__).resolve().is_relative_to(ROOT.resolve()), "lab_env shadowed this tree's core"

_LIVE_DATA = Path(r"C:\Nascence") / "data"
_WATCH = [_LIVE_DATA / "spatial_shadow.jsonl", _LIVE_DATA / "spatial_depth_shadow.jsonl",
          _LIVE_DATA / "room_state.json", _LIVE_DATA / "cat_state.json", _LIVE_DATA / "position.json",
          _LIVE_DATA / "thermal_percepts_shadow.jsonl", _LIVE_DATA / "thermal_ledger.json"]
_BEFORE_COMMIT = "0e95fce9"          # master tip before J-2480: the renderer "as it was"


def _snap(p: Path):
    if not p.exists():
        return None
    st = p.stat()
    return (st.st_size, st.st_mtime_ns, hashlib.md5(p.read_bytes()).hexdigest() if st.st_size < 50_000_000 else "")


_before = {p: _snap(p) for p in _WATCH}
FAILS = 0


def check(name, ok, detail=""):
    global FAILS
    print(("  ok   " if ok else "  FAIL ") + name + (f"  -- {detail}" if detail and not ok else ""))
    if not ok:
        FAILS += 1


# ── a private world: the authored layouts (read-only copies) + hand-set room/cat state ────────────────────
TMP = Path(tempfile.mkdtemp(prefix="x_J-2480_"))
(TMP / "world_geometry").mkdir()
for room in ("study", "garden", "shore", "wood"):
    src = _LIVE_DATA / "world_geometry" / f"{room}.json"
    if src.exists():
        shutil.copy(src, TMP / "world_geometry" / f"{room}.json")
SPT._GEO = TMP / "world_geometry"
SPT._DATA = TMP
SPT._layout_cache.clear()
LAY = SPT.layout("study")
assert LAY, "study layout not loaded"
SPS = list(LAY["standpoints"])

# the renderer BEFORE this job, loaded side by side from git history (same core.profile / world_clock)
_old_src = subprocess.run(["git", "show", f"{_BEFORE_COMMIT}:core/spatial.py"], cwd=str(ROOT),
                          capture_output=True, text=True, encoding="utf-8", check=True).stdout
_old_path = TMP / "spatial_before_J2480.py"
_old_path.write_text(_old_src, encoding="utf-8")
_spec = importlib.util.spec_from_file_location("spatial_before_J2480", _old_path)
OLD = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(OLD)
OLD._GEO = TMP / "world_geometry"
OLD._DATA = TMP
OLD._layout_cache.clear()
assert not hasattr(OLD, "SPATIAL_DEPTH_LIVE"), "the 'before' module already carries the flag -- wrong commit"


def world(fire="burning", cat_loc="windowsill", weather="steady rain", location="study", cat_phase="companion",
          wind="calm", wdir=None):
    st = {"location": location, "fire": fire, "weather": weather, "wind": wind}
    if wdir is not None:
        st["weather_dir"] = wdir
    (TMP / "room_state.json").write_text(json.dumps(st), encoding="utf-8")
    (TMP / "cat_state.json").write_text(json.dumps({"phase": cat_phase, "location": cat_loc}), encoding="utf-8")


# no tracked world objects in the private world (render's clause 2.5 reads the object stores)
try:
    from core import world_substrate as _WS
    _WS.get_objects_at_location = lambda room: []
except Exception:
    pass

_FIRE = ("burning", "embers", "out")
_CATS = ("windowsill", "on_your_lap", "under_desk", "by_the_fire", "on_the_desk", "mantel", "doorstep", "indoors")
_WX = ("steady rain", "clear", "thunderstorm", "overcast", "high cloud", "wind and rain")


def _world_for(seed: int):
    rng = random.Random(seed)
    sp = SPS[seed % len(SPS)]
    world(fire=rng.choice(_FIRE), cat_loc=rng.choice(_CATS), weather=rng.choice(_WX),
          cat_phase=rng.choice(("companion", "kept", "wild")), wind=rng.choice(("calm", "gale")),
          wdir=rng.choice((None, 0, 135, 300)))
    return sp


def _is_fire(cl):
    return cl.startswith("the fire is ") or cl.startswith("the embers are ")


def _is_cat(cl):
    return cl.startswith("the cat is ")


_BANNED = ("close", "mid", "faint", "band", "share", "gauge", "within reach", "reach", "warmth_share", "hearth_dist")


def _words(line):
    return " " + line.lower().replace(",", " ").replace(".", " ").replace(";", " ").replace("—", " ") + " "


N = 200
print("[1] flag off: byte-identical to the renderer before J-2480 (commit %s) on %d seeded renders" % (_BEFORE_COMMIT, N))
SPT.SPATIAL_DEPTH_LIVE = False
_mism = 0
for seed in range(N):
    sp = _world_for(seed)
    random.seed(seed)
    a = OLD.render("study", sp)
    random.seed(seed)
    b = SPT.render("study", sp)
    random.seed(seed)
    c = SPT._render_base("study", sp)
    if not (a == b == c):
        _mism += 1
        if _mism <= 3:
            print("     mismatch seed", seed, "\n      old:", a, "\n      new:", b)
check(f"{N}/{N} renders identical (render() and _render_base() vs before)", _mism == 0, str(_mism))
check("flag off: no new random draw is taken (next draw equal)",
      (random.seed(5), OLD.render("study", "at_the_hearth"), random.random())[2] ==
      (random.seed(5), SPT.render("study", "at_the_hearth"), random.random())[2])

print("[2] flag on: the same %d renders differ only in the fire/cat clauses" % N)
SPT.SPATIAL_DEPTH_LIVE = True
_bad = 0
_fire_diff = _cat_diff = _differ = 0
_fire_seen = _cat_seen = 0
for seed in range(N):
    sp = _world_for(seed)
    random.seed(seed)
    off = OLD.render("study", sp)
    random.seed(seed)
    on = SPT.render("study", sp)
    dp = SPT.depth("study", on["standpoint"])
    ok = (on["standpoint"] == off["standpoint"] and len(on["clauses"]) == len(off["clauses"])
          and set(on) == {"standpoint", "clauses", "line"}
          and (on["line"] == SPT._line_of("study", on["clauses"]) if on["clauses"] else on["line"] == off["line"]))
    for x, y in zip(off["clauses"], on["clauses"]):
        if _is_fire(x):
            _fire_seen += 1
            # "the fire is {dist}, {sector} — {crackle}" / "the embers are {dist}, {sector}, {low}, {glow}": the
            # head (distance word + sector) is kept verbatim; only the tail after it is re-said by nearness
            head_x = x.split(" — ")[0] if x.startswith("the fire is ") else ", ".join(x.split(", ")[:2])
            ok = ok and _is_fire(y) and y.startswith(head_x)
            if x != y:
                _fire_diff += 1
        elif _is_cat(x):
            _cat_seen += 1
            if x == "the cat is on your lap, a warm weight":
                ok = ok and y == x
            else:
                # "the cat is {place}, {sector}{elev}" -> "the cat is {place}, {dist}, {sector}{elev}"
                place = x.split(", ")[0]
                ok = ok and y.startswith(place + ", ") and x.split(", ", 1)[1] == y.split(", ", 2)[2]
            if x != y:
                _cat_diff += 1
        else:
            ok = ok and x == y
    if on["line"] != off["line"]:
        _differ += 1
    if not ok:
        _bad += 1
        if _bad <= 3:
            print("     bad seed", seed, "\n      off:", off, "\n      on :", on)
check(f"{N}/{N} pairs: only fire/cat clauses differ, same count, same standpoint, P2 keys only", _bad == 0, str(_bad))
print(f"     fire clauses seen {_fire_seen}, re-said {_fire_diff}; cat clauses seen {_cat_seen}, re-said {_cat_diff}; lines differing {_differ}")
check("some fire clauses are really re-said", _fire_diff > 0)
check("some cat clauses are really re-said", _cat_diff > 0)
check("every burning/embers fire clause is re-said (the crackle phrasing never survives)",
      _fire_diff == _fire_seen, f"{_fire_diff} of {_fire_seen}")

print("[3] no readout: digits, band names, gauge/reach words, reach feature names never reach the line")
_leaks = 0
for seed in range(N):
    sp = _world_for(seed)
    random.seed(seed)
    off = OLD.render("study", sp)
    random.seed(seed)
    on = SPT.render("study", sp)
    dp = SPT.depth("study", sp) or {}
    w = _words(on["line"])
    leaked = [b for b in _BANNED if (" " + b + " ") in w]
    if any(ch.isdigit() for ch in on["line"]) or leaked:
        _leaks += 1
        print("     leak seed", seed, leaked, on["line"])
    # the reach-set: a feature name that is NOT in the P2 line must not be in the live line either
    for item in dp.get("reach") or []:
        nm = item["name"].replace("_", " ")
        if nm in on["line"].lower() and nm not in off["line"].lower():
            _leaks += 1
            print("     reach leak seed", seed, nm, on["line"])
check("no digit / band / gauge / reach word; no reach feature newly named", _leaks == 0, str(_leaks))

print("[4] thermal agreement: the warmth said == the warmth he feels at that standpoint")
world(fire="burning", cat_loc="windowsill")
_tier_of = {"near": 3, "mid": 2, "far": 1}


def _tier(clause):
    for k, pool in (("near", SPT._PHRASES["fire_near"]), ("mid", SPT._PHRASES["fire_mid"]), ("far", SPT._PHRASES["fire_far"])):
        if any(clause.endswith(p) for p in pool):
            return k
    for k, pool in (("near", SPT._PHRASES["embers_near"]), ("mid", SPT._PHRASES["embers_mid"]), ("far", SPT._PHRASES["embers_far"])):
        if any(clause.endswith(p) for p in pool):
            return k
    return None


from core import study_life as _SL                                # noqa: E402
_SL.draught = lambda: 0.0        # study_life's own state bootstrap writes provisions.json (fenced, non-live here);
_SL.warm_drink = lambda: 0.0     # the draught/drink terms are not the fire's distance model, which is what [4] asserts
tiers, terms, felt = {}, {}, {}
for sp in SPS:
    random.seed(1)
    on = SPT.render("study", sp)
    fc = [c for c in on["clauses"] if _is_fire(c)]
    check(f"{sp}: the live line carries a fire clause", bool(fc))
    if not fc:
        continue
    tiers[sp] = _tier(fc[0])
    terms[sp] = TH._fire_term("study", sp, "burning")
    felt[sp] = TH.field_at("study", sp, "night", "clear", "winter", "burning", "calm", now=1.0e9)
    fn = SPT._fire_nearness(sp, "burning")
    pos = LAY["standpoints"][sp]["pos"]
    check(f"{sp}: tier recognised from a pool", tiers[sp] in _tier_of, str(fc))
    check(f"{sp}: hearth distance == thermal's own distance",
          fn["hearth_dist"] == round(math.dist(pos[:2], TH._HEARTH[:2]), 2))
    check(f"{sp}: 'heat full on you' iff thermal share >= 0.95",
          ("heat" in fc[0] and "full on you" in fc[0]) == (terms[sp] / 0.42 >= 0.95), f"{fc[0]} share={terms[sp]/0.42:.3f}")
print("     tiers:", tiers)
print("     thermal fire term:", {k: round(v, 3) for k, v in terms.items()})
print("     thermal field_at :", {k: round(v, 3) for k, v in felt.items()})
_mono = all((terms[a] >= terms[b]) <= (_tier_of[tiers[a]] >= _tier_of[tiers[b]]) for a in tiers for b in tiers)
check("tier is monotone in thermal._fire_term across all standpoint pairs", _mono)
_mono_felt = all((felt[a] > felt[b] + 1e-9) <= (_tier_of[tiers[a]] >= _tier_of[tiers[b]]) for a in tiers for b in tiers)
check("tier never contradicts thermal.field_at (warmer felt -> never a cooler clause)", _mono_felt)
check("thermal says the hearth is warmer than the desk, and the line agrees",
      felt["at_the_hearth"] > felt["at_the_desk"] and _tier_of[tiers["at_the_hearth"]] > _tier_of[tiers["at_the_desk"]])
world(fire="embers", cat_loc="windowsill")
random.seed(1)
eh = [c for c in SPT.render("study", "at_the_hearth")["clauses"] if _is_fire(c)]
random.seed(1)
ed = [c for c in SPT.render("study", "at_the_desk")["clauses"] if _is_fire(c)]
check("embers: hearth near, desk far", eh and ed and _tier(eh[0]) == "near" and _tier(ed[0]) == "far", f"{eh} {ed}")

print("[5] every new pool rotates (no single fixed string)")
for fire, sp, pool in (("burning", "at_the_hearth", "fire_near"), ("burning", "mid_room", "fire_mid"),
                       ("burning", "at_the_desk", "fire_far"), ("embers", "at_the_hearth", "embers_near"),
                       ("embers", "mid_room", "embers_mid"), ("embers", "at_the_desk", "embers_far")):
    world(fire=fire, cat_loc="windowsill")
    seen = set()
    for i in range(60):
        random.seed(1000 + i)
        seen.update(c for c in SPT.render("study", sp)["clauses"] if _is_fire(c))
    check(f"{pool}: >= 2 distinct clauses over 60 renders ({len(seen)})", len(seen) >= 2)
    check(f"{pool}: every clause ends with a pool entry", all(any(c.endswith(p) for p in SPT._PHRASES[pool]) for c in seen))
    check(f"{pool}: pool has >= 3 entries", len(SPT._PHRASES[pool]) >= 3)
check("the D-0501-graded wording leads each pool",
      SPT._PHRASES["fire_near"][0] == "its heat full on you, the crackle loud"
      and SPT._PHRASES["fire_far"][0] == "little of its warmth gets this far, the crackle soft from there")

print("[6] the clause count never changes (no growth; D-0501 defeater iii)")
_grow = 0
for seed in range(N):
    sp = _world_for(seed)
    random.seed(seed)
    off = OLD.render("study", sp)
    random.seed(seed)
    on = SPT.render("study", sp)
    if len(on["clauses"]) != len(off["clauses"]) or on["line"].count(";") != off["line"].count(";"):
        _grow += 1
check(f"{N}/{N}: same clause count, same separator count", _grow == 0, str(_grow))

print("[7] nothing not in the room gets a nearness word")
world(fire="out", cat_loc="windowsill")
random.seed(2)
on = SPT.render("study", "at_the_hearth")
check("fire out: no fire/embers clause", not any(_is_fire(c) for c in on["clauses"]), on["line"])
world(fire="burning", cat_loc="windowsill", cat_phase="wild")
random.seed(2)
on = SPT.render("study", "at_the_desk")
check("no cat: no cat clause", not any(_is_cat(c) for c in on["clauses"]), on["line"])
world(fire="burning", cat_loc="on_your_lap")
random.seed(2)
on = SPT.render("study", "in_the_chair")
check("lap-cat in the chair: the lap clause is untouched", "the cat is on your lap, a warm weight" in on["clauses"], on["line"])
world(fire="burning", cat_loc="windowsill")
random.seed(2)
on = SPT.render("study", "in_the_chair")
cc = [c for c in on["clauses"] if _is_cat(c)]
check("sill-cat from the chair: 'across the room' said", cc and "across the room" in cc[0], str(cc))
world(fire="burning", cat_loc="by_the_fire")
random.seed(2)
on = SPT.render("study", "at_the_hearth")
cc = [c for c in on["clauses"] if _is_cat(c)]
check("hearth-cat from the hearth: 'right beside you' said", cc and "right beside you" in cc[0], str(cc))

print("[8] scope: rooms outside DEPTH_SHADOW_ROOMS are byte-identical with the flag on")
check("DEPTH_SHADOW_ROOMS is the study only", tuple(SPT.DEPTH_SHADOW_ROOMS) == ("study",))
L.position_standpoint = lambda room=None: None   # standpoint=None path: locomotion's live position store is fenced here
for room in ("garden", "shore", "wood"):
    if SPT.layout(room) is None:
        print("     (no layout for", room, "-- skipped)")
        continue
    _m = 0
    for seed in range(40):
        rng = random.Random(seed)
        world(fire="burning", cat_loc="doorstep", weather=rng.choice(_WX), location=room, wind=rng.choice(("calm", "gale")), wdir=rng.choice((None, 90)))
        random.seed(seed)
        a = OLD.render(room, None if seed % 2 else next(iter(SPT.layout(room).get("standpoints") or {}), None))
        random.seed(seed)
        b = SPT.render(room, None if seed % 2 else next(iter(SPT.layout(room).get("standpoints") or {}), None))
        if a != b:
            _m += 1
    check(f"{room}: 40/40 identical", _m == 0, str(_m))

print("[9] shadow() end to end, inside lab_env.isolate()")
L.position_standpoint = lambda room=None: "at_the_desk"
with lab_env.isolate(also=[(SPT, ["_SHADOW", "_DEPTH_SHADOW"])], db="empty") as lab:
    check("shadow paths redirected into the lab sandbox",
          str(SPT._DEPTH_SHADOW).startswith(str(lab)) and str(SPT._SHADOW).startswith(str(lab)))
    world(fire="burning", cat_loc="windowsill")
    SPT.SPATIAL_DEPTH_LIVE = True
    SPT.shadow(actual="Where you are: your study, the pool line.")
    SPT.SPATIAL_DEPTH_LIVE = False
    SPT.shadow(actual="Where you are: your study, the pool line.")
    SPT.SPATIAL_DEPTH_LIVE = True
    p0 = [json.loads(x) for x in Path(SPT._SHADOW).read_text(encoding="utf-8").splitlines() if x.strip()]
    p3 = [json.loads(x) for x in Path(SPT._DEPTH_SHADOW).read_text(encoding="utf-8").splitlines() if x.strip()]
    check("two P0 rows + two P3 rows", len(p0) == 2 and len(p3) == 2, f"{len(p0)} {len(p3)}")
    if len(p0) == 2 and len(p3) == 2:
        live, off = p3[0], p3[1]
        check("live row: live=True", live.get("live") is True, str(live.get("live")))
        check("live row: scene is the P2 line (crackle phrasing), depth_line differs",
              live["scene"] != live["depth_line"] and live["changed"] is True and "crackle" in live["scene"])
        check("live row: P0 rendered == the very depth_line Du got (one draw, shared)", p0[0]["rendered"] == live["depth_line"])
        check("live row: same ts as its P0 row", p0[0]["ts"] == live["ts"])
        check("live row: reach-set logged, not rendered (no reach name newly in the line vs the P2 scene)",
              isinstance(live.get("reach"), list) and len(live["reach"]) > 0
              and not any(x["name"].replace("_", " ") in live["depth_line"].lower()
                          and x["name"].replace("_", " ") not in live["scene"].lower() for x in live["reach"]))
        check("live row: band in the row only, not in the line",
              live["fire"]["band"] == "faint" and " faint " not in _words(live["depth_line"]))
        check("flag-off row: live=False, P0 rendered == scene", off.get("live") is False and p0[1]["rendered"] == off["scene"])
        print("     scene     :", live["scene"])
        print("     depth_line:", live["depth_line"])
    st = SPT.depth_status()
    check("depth_status reads both rows", st["rows"] == 2 and st["fire_bands"].get("faint") == 2, str(st))

print("[10] fail-open: an overlay that raises leaves the P2 line untouched")
world(fire="burning", cat_loc="windowsill")
_orig_depth = SPT.depth
SPT.depth = lambda room, sp: (_ for _ in ()).throw(RuntimeError("boom"))
random.seed(9)
on = SPT.render("study", "at_the_hearth")
SPT.depth = _orig_depth
random.seed(9)
base = SPT._render_base("study", "at_the_hearth")
check("render() == _render_base() when the overlay raises", on == base)
SPT._layout_cache["nowhere"] = None
check("no layout -> None, flag on", SPT.render("nowhere") is None)

print("[11] live stores untouched")
for p in _WATCH:
    check(f"unchanged: {p.name}", _snap(p) == _before[p])

shutil.rmtree(TMP, ignore_errors=True)
print("\nALL OK" if not FAILS else f"\n{FAILS} FAILURE(S)")
sys.exit(1 if FAILS else 0)
