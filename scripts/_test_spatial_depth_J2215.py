"""
Regression/verification: spatial_perception P3 -- position-dependent depth + peripersonal reach, shadow-only,
study only (J-2215, T-0089, Travis 2026-10-16).

What this proves, ISOLATED (no model, no live data written):
  [1] reuse     the fire's nearness comes from thermal's OWN hearth point / standpoint distance / falloff:
                thermal._HEARTH == study.json fireplace, hearth_dist == math.dist(thermal standpoint, hearth),
                warmth_share == thermal._fire_term / peak
  [2] nearness  the fire band grades by standpoint (hearth/chair close, mid_room mid, desk/window/shelf faint),
                and the lap-cat is nearer (0.0, in reach) than the sill-cat (>1 m, out of reach)
  [3] reach     the reach-set is what lies within REACH_M of the standpoint (at the hearth: fireplace, hearthstone,
                mantel, kettle; never the desk); what he is AT (< AT_M) is listed separately, not as reach
  [4] the pair  depth_line differs from render()'s line ONLY in the fire/cat clauses; it carries no digit, no
                band name, no gauge word (D-0434), and no reach clause (world answers, never leads)
  [5] what Du reads is unchanged: render() returns the identical dict with the P3 block present (same seed)
  [6] end to end  spatial.shadow() writes its P0 row AND one P3 row with the same ts into the lab sandbox; a
                garden scene writes no P3 row (study-only scope)
  [7] fence     a non-live process is REFUSED (NonLiveWriteError, nothing written) for both the worktree-relative
                default path and the literal live C:\\Nascence\\data path; shadow() itself stays fail-open
  [8] live stores untouched (hash canary)

  python scripts/_test_spatial_depth_J2215.py        # exit 0 = ALL OK
"""
from __future__ import annotations

import hashlib
import json
import math
import random
import shutil
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
          _LIVE_DATA / "thermal_percepts_shadow.jsonl"]


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


# ── a private world: the authored study layout (read-only copy) + hand-set room/cat state ────────────────
TMP = Path(tempfile.mkdtemp(prefix="x_J-2215_"))
(TMP / "world_geometry").mkdir()
shutil.copy(_LIVE_DATA / "world_geometry" / "study.json", TMP / "world_geometry" / "study.json")
shutil.copy(_LIVE_DATA / "world_geometry" / "garden.json", TMP / "world_geometry" / "garden.json")
SPT._GEO = TMP / "world_geometry"
SPT._DATA = TMP                         # _read_json(room_state/cat_state) reads here; _DEPTH_SHADOW/_SHADOW are
SPT._layout_cache.clear()               # module constants, redirected by lab_env.isolate() below
LAY = SPT.layout("study")
assert LAY, "study layout not loaded"
SPT.SPATIAL_DEPTH_LIVE = False   # J-2480 (D-0501): this script pins the SHADOW pair contract as built by J-2215 (scene =
                                 # the P2 line, the P0 row's rendered == scene); the live overlay behind the flag has
                                 # its own script, scripts/_test_spatial_depth_live_J2480.py


def world(fire="burning", cat_loc="windowsill", weather="steady rain", location="study"):
    (TMP / "room_state.json").write_text(json.dumps({"location": location, "fire": fire, "weather": weather,
                                                     "wind": "calm"}), encoding="utf-8")
    (TMP / "cat_state.json").write_text(json.dumps({"phase": "companion", "location": cat_loc}), encoding="utf-8")


# no tracked world objects in the private world (render's clause 2.5 reads the object stores)
try:
    from core import world_substrate as _WS
    _WS.get_objects_at_location = lambda room: []
except Exception:
    pass

print("[1] reuse of thermal's distance model")
check("thermal._HEARTH is the authored fireplace", list(TH._HEARTH) == LAY["features"]["fireplace"]["pos"])
world()
for sp in LAY["standpoints"]:
    fn = SPT._fire_nearness(sp, "burning")
    pos = LAY["standpoints"][sp]["pos"]
    check(f"hearth_dist({sp}) == thermal's own distance", fn["hearth_dist"] == round(math.dist(pos[:2], TH._HEARTH[:2]), 2))
    check(f"warmth_share({sp}) == thermal._fire_term/peak", fn["warmth_share"] == round(TH._fire_term("study", sp, "burning") / 0.42, 3))
check("fire out -> no nearness", SPT._fire_nearness("in_the_chair", "out") is None)

print("[2] nearness grades by standpoint")
bands = {sp: SPT._fire_nearness(sp, "burning")["band"] for sp in LAY["standpoints"]}
print("     bands:", bands)
check("hearth close", bands["at_the_hearth"] == "close")
check("chair close", bands["in_the_chair"] == "close")
check("mid_room mid", bands["mid_room"] == "mid")
for far in ("at_the_desk", "at_the_window", "by_the_shelf", "on_the_bed"):
    check(f"{far} faint", bands[far] == "faint")
world(cat_loc="on_your_lap")
lap = SPT.depth("study", "in_the_chair")["cat"]
world(cat_loc="windowsill")
sill = SPT.depth("study", "in_the_chair")["cat"]
check("lap-cat on lap, dist 0, in reach", lap["on_lap"] and lap["dist"] == 0.0 and lap["in_reach"], str(lap))
check("sill-cat farther and out of reach", sill["dist"] > 1.0 and not sill["in_reach"], str(sill))
check("lap-cat nearer than sill-cat", lap["dist"] < sill["dist"])

print("[3] reach-set")
world(cat_loc="by_the_fire")
dh = SPT.depth("study", "at_the_hearth")
rn = [x["name"] for x in dh["reach"]]
print("     at_the_hearth reach:", rn, "at:", dh["at"])
for nm in ("fireplace", "mantel", "kettle"):
    check(f"hearth reach has {nm}", nm in rn)
check("hearthstone is AT (under him), not reach", "hearthstone" in dh["at"] and "hearthstone" not in rn)
check("hearth-cat in reach", "cat" in rn)
check("desk not in hearth reach", "desk" not in rn)
check("all reach within REACH_M", all(x["dist"] <= SPT.REACH_M for x in dh["reach"]))
dd = SPT.depth("study", "at_the_desk")
print("     at_the_desk reach:", [x["name"] for x in dd["reach"]], "at:", dd["at"])
check("desk reach has the desk", "desk" in [x["name"] for x in dd["reach"]])
check("fireplace not in desk reach", "fireplace" not in [x["name"] for x in dd["reach"]])
check("unknown standpoint -> None", SPT.depth("study", "nowhere") is None)

print("[4] the pair")
_BANNED = ("close", "mid", "faint", "band", "share", "gauge", "within reach", "reach")
_bad_pairs = 0
for fire in ("burning", "embers"):
    for cat_loc in ("windowsill", "on_your_lap", "under_desk", "by_the_fire"):
        world(fire=fire, cat_loc=cat_loc)
        for sp in LAY["standpoints"]:
            random.seed(7)
            r = SPT.render("study", sp)
            dp = SPT.depth("study", r["standpoint"])
            dl = SPT.depth_line(r, dp, "study")
            rc = r["clauses"]
            dc = dl[len("Where you are: the study — "):-1].split("; ")
            same_n = len(dc) == len(rc)
            others_same = same_n and all(a == b for a, b in zip(rc, dc)
                                         if not (a.startswith("the fire is ") or a.startswith("the embers are ")
                                                 or a.startswith("the cat is ")))
            if not (same_n and others_same):
                _bad_pairs += 1
                check(f"pair {fire}/{cat_loc}/{sp}: only fire/cat clauses differ", False, f"{rc} || {dc}")
            words = " " + dl.lower().replace(",", " ").replace(".", " ").replace(";", " ") + " "
            leaked = [w for w in _BANNED if (" " + w + " ") in words]
            if any(ch.isdigit() for ch in dl) or leaked:
                _bad_pairs += 1
                check(f"pair {fire}/{cat_loc}/{sp}: no number/band/reach words", False, f"{leaked} {dl}")
check("all 64 pairs: only fire/cat clauses differ, no digits/gauge words", _bad_pairs == 0, str(_bad_pairs))
world(fire="burning", cat_loc="windowsill")
random.seed(3)
r = SPT.render("study", "at_the_desk")
dl = SPT.depth_line(r, SPT.depth("study", "at_the_desk"), "study")
print("     scene     :", r["line"])
print("     depth_line:", dl)
check("desk pair actually differs (fire faint, cat distance said)", dl != r["line"])
random.seed(3)
r2 = SPT.render("study", "at_the_hearth")
dl2 = SPT.depth_line(r2, SPT.depth("study", "at_the_hearth"), "study")
print("     scene     :", r2["line"])
print("     depth_line:", dl2)
check("hearth line says heat full on you (any entry of the rotating fire_near pool, J-2480)",
      any(c.endswith(ph) for c in dl2[len("Where you are: the study — "):-1].split("; ") for ph in SPT._PHRASES["fire_near"]))

print("[5] render() unchanged")
random.seed(11)
a = SPT.render("study", "in_the_chair")
random.seed(11)
b = SPT.render("study", "in_the_chair")
check("render deterministic under seed and returns the P2 keys only", a == b and set(a) == {"standpoint", "clauses", "line"})

print("[6] end to end through shadow(), inside lab_env.isolate()")
L.position_standpoint = lambda room=None: "at_the_hearth"
with lab_env.isolate(also=[(SPT, ["_SHADOW", "_DEPTH_SHADOW"])], db="empty") as lab:
    check("shadow paths redirected into the lab sandbox",
          str(SPT._DEPTH_SHADOW).startswith(str(lab)) and str(SPT._SHADOW).startswith(str(lab)))
    world(fire="burning", cat_loc="windowsill")
    SPT.shadow(actual="Where you are: your study, the pool line.")
    p0 = [json.loads(x) for x in Path(SPT._SHADOW).read_text(encoding="utf-8").splitlines() if x.strip()]
    p3 = [json.loads(x) for x in Path(SPT._DEPTH_SHADOW).read_text(encoding="utf-8").splitlines() if x.strip()]
    check("one P0 row + one P3 row", len(p0) == 1 and len(p3) == 1, f"{len(p0)} {len(p3)}")
    if p0 and p3:
        row = p3[0]
        check("same ts as the P0 row", row["ts"] == p0[0]["ts"])
        check("P3 scene == P0 rendered (the pair's left side is today's line)", row["scene"] == p0[0]["rendered"])
        check("row carries standpoint/fire/cat/reach/at/depth_line/changed/actual",
              all(k in row for k in ("standpoint", "fire", "cat", "reach", "at", "depth_line", "changed", "actual")))
        check("row standpoint is the live one", row["standpoint"] == "at_the_hearth")
        print("     row:", json.dumps({k: row[k] for k in ("standpoint", "fire", "cat", "at")}, ensure_ascii=False))
    st = SPT.depth_status()
    check("depth_status reads the row", st["rows"] == 1 and st["fire_bands"].get("close") == 1, str(st))
    world(fire="burning", cat_loc="windowsill", location="garden")
    L.position_standpoint = lambda room=None: None
    SPT.shadow(actual="garden")
    p3b = [x for x in Path(SPT._DEPTH_SHADOW).read_text(encoding="utf-8").splitlines() if x.strip()]
    check("garden scene adds no P3 row (study-only)", len(p3b) == 1, str(len(p3b)))

print("[7] the non-live fence")
check("this process is not live", not profile.LIVE)
world(fire="burning", cat_loc="windowsill")
L.position_standpoint = lambda room=None: "in_the_chair"
random.seed(1)
r = SPT.render("study")
for target in (SPT._DEPTH_SHADOW, _LIVE_DATA / "spatial_depth_shadow.jsonl"):
    SPT._DEPTH_SHADOW = target
    existed = target.exists()
    try:
        SPT.depth_shadow(r, "study", actual="x")
        check(f"depth_shadow refused at {target}", False, "no exception")
    except profile.NonLiveWriteError:
        check(f"depth_shadow refused at {target}", True)
    check(f"nothing written at {target}", target.exists() == existed)
SPT._DEPTH_SHADOW = _LIVE_DATA / "spatial_depth_shadow.jsonl"     # the worst case: the literal live path
SPT._SHADOW = TMP / "p0_after_isolate_J-2215.jsonl"                # the PRE-EXISTING P0 append is unfenced; keep it in TMP
try:
    SPT.shadow(actual="x")      # P0 entry point stays fail-open (its own pre-existing contract)
    check("shadow() itself stays fail-open for a non-live caller", True)
except Exception as exc:
    check("shadow() itself stays fail-open for a non-live caller", False, repr(exc))

print("[8] live stores untouched")
for p in _WATCH:
    check(f"unchanged: {p.name}", _snap(p) == _before[p])

shutil.rmtree(TMP, ignore_errors=True)
print("\nALL OK" if not FAILS else f"\n{FAILS} FAILURE(S)")
sys.exit(1 if FAILS else 0)
