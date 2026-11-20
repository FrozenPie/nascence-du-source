"""
Regression/verification: the deterministic spatial sketch store (J-2661, I-0129 rung 1 instrument, SHADOW ONLY).

Feeds the 12 seeded stops per place from the J-2628 renders (docs/lab/spatial_map_reconstruction_2026-10-31.json)
through core/spatial_sketch.record() into a temp-dir store and proves, hermetically (no model, no live data written):
  [1] parity     the store's aggregator reproduces the ideal decoder (scripts/spatial_map_ideal_decoder.decode, imported)
                 EXACTLY on the lab's search box: study 0.28 m, garden 0.69 m, study depth 0.21 m, shore 0.81 m, wood 0.68 m
                 (raw RMSE, pair accuracy, every per-object error identical)
  [2] bar        with the layout-only default search box and one-vote-per-unique-observation (the live path), the F-3407
                 bar still holds: raw RMSE <= ideal + 1.0 m, pair accuracy >= 0.85 in study AND garden, and the shuffled-pose
                 control is >= 2x worse
  [3] parser     core's moved clause parser labels every lab clause identically to the lab's observe(); the vocabulary
                 equals the lab VOCAB; truth_of(layout) equals the lab's saved truth
  [4] flag off   the default is OFF: record() returns None and writes nothing; a real spatial.render() with the flag off
                 writes nothing and returns the identical dict as with the flag on
  [5] hook       flag on: spatial.render() fills the store (one row per render), score rows appear only on NEW unique
                 observations, repeats add none, unlabeled clauses are logged not guessed, status() reads it back
  [6] fence      flag on with the DEFAULT (worktree data/) path: record() is refused by profile.guard_path
                 (NonLiveWriteError), the render hook swallows it, no file appears
  [7] seam       a custom extractor= callable is honoured (the optional model-extractor alternative stays flag-off)
  [8] canary     live stores and world_geometry untouched (hash + size + mtime), nothing created under the worktree data/

  python scripts/_test_spatial_sketch_J2661.py        # exit 0 = ALL OK
"""
from __future__ import annotations

import copy
import hashlib
import json
import random
import shutil
import sys
import tempfile
import types
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import core                                                       # noqa: E402  (core BEFORE anything else)
assert Path(core.__file__).resolve().is_relative_to(ROOT.resolve()), f"core resolved outside this tree: {core.__file__}"
from core import profile                                          # noqa: E402
from core import spatial as SPT                                   # noqa: E402
from core import spatial_sketch as SK                             # noqa: E402
import spatial_map_ideal_decoder as IDEAL                         # noqa: E402  (imports the lab, which imports core.spatial)
import spatial_map_reconstruction_lab as LAB                      # noqa: E402
assert Path(SPT.__file__).resolve().is_relative_to(ROOT.resolve()), SPT.__file__

LIVE = Path(r"C:\Nascence") / "data"
WATCH = ([LIVE / "spatial_shadow.jsonl", LIVE / "spatial_depth_shadow.jsonl", LIVE / "room_state.json",
          LIVE / "cat_state.json", LIVE / "position.json", LIVE / "spatial_sketch.jsonl",
          LIVE / "spatial_sketch_shadow.jsonl"] + sorted((LIVE / "world_geometry").glob("*.json")))
FIXTURE = ROOT / "docs" / "lab" / "spatial_map_reconstruction_2026-10-31.json"


def snap(p: Path):
    if not p.exists():
        return None
    st = p.stat()
    return (st.st_size, st.st_mtime_ns, hashlib.md5(p.read_bytes()).hexdigest() if st.st_size < 50_000_000 else "")


BEFORE = {p: snap(p) for p in WATCH}
WT_DATA_BEFORE = (ROOT / "data").exists()
FAILS = 0


def check(name, ok, detail=""):
    global FAILS
    print(("  ok   " if ok else "  FAIL ") + name + (f"  -- {detail}" if detail and not ok else ""))
    if not ok:
        FAILS += 1


TMP = Path(tempfile.mkdtemp(prefix="x_J-2661_"))
GEO = TMP / "world_geometry"
GEO.mkdir()
for room in ("study", "garden", "shore", "wood"):
    shutil.copy(LIVE / "world_geometry" / f"{room}.json", GEO / f"{room}.json")      # read-only source, private copy
SPT._GEO, SPT._DATA = GEO, TMP
SPT._layout_cache.clear()
SK._DATA = TMP
SK._STORE, SK._SHADOW = TMP / "sk_store.jsonl", TMP / "sk_shadow.jsonl"
SK._CACHE.clear()
stub = types.ModuleType("core.world_substrate")
stub.get_objects_at_location = lambda room: []
sys.modules["core.world_substrate"] = stub

D = json.loads(FIXTURE.read_text(encoding="utf-8"))
RENDERS = D["renders"]
LAYOUT = {p: json.loads((GEO / f"{p}.json").read_text(encoding="utf-8")) for p in ("study", "garden", "shore", "wood")}


def feed(R, tag, perm=None, flag=True):
    """Push one lab render's 12 stops (two moments each) through record() into a fresh private store."""
    store, shadow = TMP / f"{tag}.jsonl", TMP / f"{tag}_shadow.jsonl"
    SK.SKETCH_SHADOW_LIVE = flag
    n = 0
    for i, s in enumerate(R["steps"]):
        pose = R["steps"][perm[i]]["pose"] if perm else s["pose"]
        for ln in s["lines"]:
            row = SK.record(R["place"], f"walk_{i:02d}", pose, ln["clauses"], ts=1000.0 + n, lay=LAYOUT[R["place"]],
                            store=store, shadow=shadow, score_it=False)
            n += row is not None
    SK.SKETCH_SHADOW_LIVE = False
    return store, shadow, n


def lab_box(R):
    xs = [s["pose"]["x"] for s in R["steps"]] + [v[0] for v in R["truth"].values()]
    ys = [s["pose"]["y"] for s in R["steps"]] + [v[1] for v in R["truth"].values()]
    return min(xs) - 1, max(xs) + 1, min(ys) - 1, max(ys) + 1


print("[1] parity with the ideal decoder (lab search box, no dedup)")
RES = {}
for R in RENDERS:
    key = f"{R['place']}{'+depth' if R['depth_on'] else ''}"
    store, _sh, n = feed(R, "p_" + key.replace("+", "_"))
    rows = SK.read_rows(R["place"], store)
    pred, _c = SK.estimate(rows, R["place"], lab_box(R), dedup=False, labels=set(R["truth"]))
    sc = SK.score(pred, R["truth"])
    ref = IDEAL.decode(R)
    RES[key] = (sc, ref)
    same = (sc["raw_rmse"] == ref["raw_rmse"] and sc["pair_acc"] == ref["pair_acc"]
            and sc["per_object_err"] == ref["per_object_err"])
    print(f"      {key:13s} store raw_rmse {sc['raw_rmse']} pair {sc['pair_acc']} pairs {sc['pairs']} | ideal {ref['raw_rmse']} {ref['pair_acc']}")
    n_lines = sum(1 for st_ in R["steps"] for ln in st_["lines"] if ln["clauses"])
    check(f"{key}: store == ideal decoder exactly ({n} of {n_lines} non-empty renders recorded)", same and n == n_lines, f"{sc} vs {ref}")
    un = {c for r_ in rows for c in r_["unlabeled"]}
    check(f"{key}: unlabeled clauses in the store == the lab's unlabeled list ({len(un)})", un == {c[:200] for c in R["unlabeled_clauses"]},
          f"{sorted(un)[:3]} vs {R['unlabeled_clauses'][:3]}")
check("study 0.28 / garden 0.69 / study-depth 0.21 / shore 0.81 / wood 0.68 (F-3381)",
      [RES[k][0]["raw_rmse"] for k in ("study", "study+depth", "garden", "shore", "wood")] == [0.28, 0.21, 0.69, 0.81, 0.68])

print("[2] the F-3407 bar through the live path (layout-only box, one vote per unique observation)")
for place in ("study", "garden"):
    R = next(r for r in RENDERS if r["place"] == place and not r["depth_on"])
    store, _sh, _n = feed(R, "b_" + place)
    rows = SK.read_rows(place, store)
    live = SK.score_room(place, rows, LAYOUT[place], dedup=True)
    ideal = RES[place][1]
    perm = LAB.derangement(len(R["steps"]), D["seed"])
    sstore, _s2, _n2 = feed(R, "s_" + place, perm=perm)
    shuf = SK.score_room(place, SK.read_rows(place, sstore), LAYOUT[place], dedup=True)
    print(f"      {place}: live-path raw_rmse {live['raw_rmse']} pair {live['pair_acc']} (ideal {ideal['raw_rmse']}); shuffled {shuf['raw_rmse']}")
    check(f"{place}: raw RMSE <= ideal + 1.0 m", live["raw_rmse"] <= ideal["raw_rmse"] + 1.0)
    check(f"{place}: pair accuracy >= 0.85", live["pair_acc"] >= 0.85)
    check(f"{place}: shuffled-pose control >= 2x worse", shuf["raw_rmse"] >= 2 * live["raw_rmse"])
    check(f"{place}: every named object placed", live["n_objects"] == len(R["truth"]))

print("[3] parser / vocabulary / truth parity")
check("VOCAB identical to the lab's", SK.VOCAB == LAB.VOCAB)
bad = tot = 0
for R in RENDERS:
    for s_ in R["steps"]:
        for ln in s_["lines"]:
            for c in ln["clauses"]:
                tot += 1
                a, b = SK.observe(R["place"], c), IDEAL.observe(R["place"], c)
                if (a is None) != (b is None):
                    bad += 1
                elif a is not None and ((a[0], a[1]) != (b[0], b[1]) or SK.band_of(a[2]) != b[2]):
                    bad += 1
check(f"observe() agrees with the lab's on all {tot} lab clauses", bad == 0 and tot > 200, f"{bad} mismatches")
for R in RENDERS:
    if R["depth_on"]:
        continue
    t = SK.truth_of(R["place"], LAYOUT[R["place"]], include_moving=True)
    check(f"{R['place']}: truth_of(layout) == lab truth (<=0.011 m)",
          all(abs(t[k][0] - v[0]) < 0.011 and abs(t[k][1] - v[1]) < 0.011 for k, v in R["truth"].items()
              if k != "the tideline"))   # the tideline moves with the clock: truth at another moment, never scored live
check("the tideline is excluded from default scoring (it moves)", "the tideline" not in SK.truth_of("shore", LAYOUT["shore"]))

print("[4] flag off")
check("default flag is False", SK.SKETCH_SHADOW_LIVE is False)
before_files = set(p.name for p in TMP.iterdir())
check("record() flag-off returns None", SK.record("study", "at_desk", {"x": 1, "y": 1, "facing_deg": 0},
                                                  ["the fire is near, ahead"], store=TMP / "off.jsonl", shadow=TMP / "off_sh.jsonl") is None)
check("record() flag-off creates no file", not (TMP / "off.jsonl").exists() and not (TMP / "off_sh.jsonl").exists()
      and set(p.name for p in TMP.iterdir()) == before_files)


def world(fire="burning", cat_loc="under_desk"):
    (TMP / "room_state.json").write_text(json.dumps({"location": "study", "fire": fire, "weather": "steady rain", "wind": "calm"}), encoding="utf-8")
    (TMP / "cat_state.json").write_text(json.dumps({"phase": "kept", "location": cat_loc}), encoding="utf-8")


world()
SPS = list(LAYOUT["study"]["standpoints"])


def draw(flag):
    SK.SKETCH_SHADOW_LIVE = flag
    random.seed(11)
    out = [SPT.render("study", sp) for sp in SPS]
    SK.SKETCH_SHADOW_LIVE = False
    return out


SK._STORE, SK._SHADOW = TMP / "hook_store.jsonl", TMP / "hook_shadow.jsonl"
SK._CACHE.clear()
off = draw(False)
check("flag-off render() writes no sketch file", not SK._STORE.exists() and not SK._SHADOW.exists())

print("[5] hook: render() fills the store when the flag is on")
on = draw(True)
check("render() output identical with the flag on and off", on == off)
rows = SK.read_rows("study")
check("one store row per render", len(rows) == len(SPS), f"{len(rows)} vs {len(SPS)}")
check("rows carry pose, obs and unlabeled", all("pose" in r and "obs" in r and "unlabeled" in r for r in rows))
sh = SK.shadow_log.read_rows(SK._SHADOW)
check("score rows written, only on new unique observations", 0 < len(sh) <= len(SPS) and all(r["new_unique"] > 0 for r in sh), f"{len(sh)}")
n_sh = len(sh)
random.seed(11)
SK.SKETCH_SHADOW_LIVE = True
[SPT.render("study", sp) for sp in SPS]
SK.SKETCH_SHADOW_LIVE = False
check("repeat renders add store rows but NO score row", len(SK.read_rows("study")) == 2 * len(SPS) and len(SK.shadow_log.read_rows(SK._SHADOW)) == n_sh)
SK._CACHE.clear()      # a fresh process: the working set reloads from disk, repeats still add no score row
SK.SKETCH_SHADOW_LIVE = True
random.seed(11)
[SPT.render("study", sp) for sp in SPS]
SK.SKETCH_SHADOW_LIVE = False
check("after a cache reload (restart) repeats still add no score row", len(SK.shadow_log.read_rows(SK._SHADOW)) == n_sh)
st = SK.status()
print("      status:", json.dumps({k: v for k, v in st.items() if k != "rooms"}), {k: (v["renders"], v["unique_obs"], v["unlabeled_distinct"]) for k, v in st["rooms"].items()})
check("status() reads fill and last score back", st["rooms"]["study"]["renders"] == 3 * len(SPS) and "study" in st["last_score"])
last = sh[-1]
print(f"      last live score row: raw_rmse {last['raw_rmse']} pair {last['pair_acc']} objects {last['n_objects']}/{last['of']} score_ms {last['score_ms']}")
check("score cost is small enough for the render path (< 3 s)", max(r["score_ms"] for r in sh) < 3000, f"{max(r['score_ms'] for r in sh)} ms")
SK.SKETCH_SHADOW_LIVE = True
r_un = SK.record("study", "at_desk", {"x": 1.0, "y": 1.0, "facing_deg": 0}, ["a distant bell tolls", "the fire is near, ahead"], lay=LAYOUT["study"])
SK.SKETCH_SHADOW_LIVE = False
check("an unlabeled clause is logged, not guessed (and the labeled one still lands)",
      r_un["unlabeled"] == ["a distant bell tolls"] and r_un["obs"] == [["the fire", "ahead", "near"]])

print("[6] write fence: default (worktree data/) path is refused")
SK._STORE, SK._SHADOW = ROOT / "data" / "spatial_sketch.jsonl", ROOT / "data" / "spatial_sketch_shadow.jsonl"
SK._CACHE.clear()
SK.SKETCH_SHADOW_LIVE = True
try:
    SK.record("study", "at_desk", {"x": 1, "y": 1, "facing_deg": 0}, ["the fire is near, ahead"])
    refused = False
except profile.NonLiveWriteError:
    refused = True
check("record() on the default path raises NonLiveWriteError in a non-live process", refused)
try:
    SPT.render("study", SPS[0])
    swallowed = True
except Exception as e:                                           # noqa: BLE001
    swallowed = False
SK.SKETCH_SHADOW_LIVE = False
check("the render hook swallows the refusal (render never breaks)", swallowed)
check("no file created at the default path", not SK._STORE.exists() and not SK._SHADOW.exists())

print("[7] extractor seam")
SK._STORE, SK._SHADOW = TMP / "seam.jsonl", TMP / "seam_sh.jsonl"
SK._CACHE.clear()
SK.SKETCH_SHADOW_LIVE = True


def fake_model(place, clauses):
    return {"obs": [["the fire", "ahead", "near"]], "no_geom": [], "unlabeled": []}


row = SK.record("study", "at_desk", {"x": 1.0, "y": 1.0, "facing_deg": 0}, ["anything"], extractor=fake_model, lay=LAYOUT["study"])
SK.SKETCH_SHADOW_LIVE = False
check("custom extractor= honoured and tagged in the row", row and row["obs"] == [["the fire", "ahead", "near"]] and row["extractor"] == "fake_model")

print("[8] canary")
after = {p: snap(p) for p in WATCH}
changed = {str(p): (BEFORE[p], after[p]) for p in WATCH if BEFORE[p] != after[p]}
check(f"live stores + world_geometry untouched ({len(WATCH)} files hashed)", not changed, str(changed))
check("no data/ directory created in the worktree", (ROOT / "data").exists() == WT_DATA_BEFORE)
check("no sketch files in live data", not (LIVE / "spatial_sketch.jsonl").exists() or BEFORE[LIVE / "spatial_sketch.jsonl"] is not None)

shutil.rmtree(TMP, ignore_errors=True)
print("ALL OK" if FAILS == 0 else f"{FAILS} FAILED")
sys.exit(1 if FAILS else 0)
