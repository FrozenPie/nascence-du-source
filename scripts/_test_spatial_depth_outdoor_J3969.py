"""
Regression/verification: spatial_perception P3 depth layouts for the GARDEN and SHORE (J-3969, D-0747, Travis 2026-11-14).

Built shadow-first, the way the study was (J-2215 -> J-2480): the depth/reach tuple is computed and logged for the two
outdoor rooms in their own log; what Du reads changes only behind SPATIAL_DEPTH_OUTDOOR_LIVE, which ships False.

What this proves, ISOLATED (no model, no live data written):
  [1] flags     SPATIAL_DEPTH_OUTDOOR_LIVE is True (D-0809) and SPATIAL_DEPTH_OUTDOOR_SHADOW is True as shipped
  [2] tuple     depth() works for every garden and shore standpoint: reach within REACH_M, 'nearest' feature present,
                nearest really is the minimum horizontal distance, no fire (study only); study tuples gain no new key
  [3] flag off  render() == _render_base() for garden/shore (the player-facing line is untouched), study unaffected
  [4] flag on   the overlay changes ONLY the cat clause (distance word added, outdoor wording), clause count and every
                other clause verbatim; no digit / reach / band word in the line; lap and absent-cat lines untouched
  [5] study     the study with the study flag on is unchanged by the outdoor flag either way
  [6] shadow    spatial.shadow() in lab_env.isolate(): a garden row lands in the OUTDOOR log (room, nearest, live False),
                the study log stays untouched; the P0 row's rendered == scene with the flag off
  [7] status    depth_outdoor_status() reads the rows back
  [8] canary    live stores untouched

  python scripts/_test_spatial_depth_outdoor_J3969.py        # exit 0 = ALL OK
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
from core import spatial as SPT                                   # noqa: E402
from core import locomotion as L                                  # noqa: E402

sys.path.append(str(Path.home() / ".claude" / "skills" / "job-queue"))
import lab_env                                                    # noqa: E402
assert Path(core.__file__).resolve().is_relative_to(ROOT.resolve()), "lab_env shadowed this tree's core"

_LIVE_DATA = Path(r"C:\Nascence") / "data"
_WATCH = [_LIVE_DATA / "spatial_shadow.jsonl", _LIVE_DATA / "spatial_depth_shadow.jsonl",
          _LIVE_DATA / "spatial_depth_outdoor_shadow.jsonl", _LIVE_DATA / "room_state.json",
          _LIVE_DATA / "cat_state.json", _LIVE_DATA / "position.json"]


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


TMP = Path(tempfile.mkdtemp(prefix="x_J-3969_"))
(TMP / "world_geometry").mkdir()
for room in ("study", "garden", "shore", "wood"):
    src = _LIVE_DATA / "world_geometry" / f"{room}.json"
    if src.exists():
        shutil.copy(src, TMP / "world_geometry" / f"{room}.json")
SPT._GEO = TMP / "world_geometry"
SPT._DATA = TMP
SPT._layout_cache.clear()
try:
    from core import world_substrate as _WS
    _WS.get_objects_at_location = lambda room: []
except Exception:
    pass


def world(location, cat_loc="raised_bed", fire="out", weather="clear", cat_phase="companion"):
    (TMP / "room_state.json").write_text(json.dumps({"location": location, "fire": fire, "weather": weather,
                                                     "wind": "calm"}), encoding="utf-8")
    (TMP / "cat_state.json").write_text(json.dumps({"phase": cat_phase, "location": cat_loc}), encoding="utf-8")


_CATLOC = {"garden": ("garden", "garden_wall", "doorstep"), "shore": ("shore", "driftwood_tangle", "driftwood")}

print("[1] shipped flags")
check("SPATIAL_DEPTH_OUTDOOR_LIVE is True (D-0809)", SPT.SPATIAL_DEPTH_OUTDOOR_LIVE is True)
check("SPATIAL_DEPTH_OUTDOOR_SHADOW is True", SPT.SPATIAL_DEPTH_OUTDOOR_SHADOW is True)
check("outdoor rooms are garden + shore; DEPTH_SHADOW_ROOMS still study only",
      SPT.DEPTH_OUTDOOR_ROOMS == ("garden", "shore") and SPT.DEPTH_SHADOW_ROOMS == ("study",))

print("[2] the depth/reach tuple for every outdoor standpoint")
for room in ("garden", "shore"):
    lay = SPT.layout(room)
    world(room, cat_loc=_CATLOC[room][0])
    n_cat = 0
    for sp_name, sp in lay["standpoints"].items():
        dp = SPT.depth(room, sp_name)
        ok = dp and dp["room"] == room and dp["fire"] is None and isinstance(dp.get("nearest"), dict)
        check(f"{room}/{sp_name}: tuple has no fire + a nearest feature", bool(ok), str(dp))
        if not ok:
            continue
        ds = {}
        for name, f in lay["features"].items():
            p = f.get("pos")
            if name == "waterline":
                p = SPT._waterline_pos(lay) or p
            if p:
                ds[name] = SPT._rel(sp, p)["dist"]
        mn = min(ds.values())
        check(f"{room}/{sp_name}: nearest is the true minimum distance", dp["nearest"]["dist"] == mn,
              f"{dp['nearest']} vs {mn}")
        check(f"{room}/{sp_name}: reach within REACH_M", all(x["dist"] <= SPT.REACH_M for x in dp["reach"]))
        check(f"{room}/{sp_name}: within_3m matches", dp["nearest"]["within_3m"] == sum(1 for d in ds.values() if d <= 3.0))
        if dp["cat"]:
            n_cat += 1
    check(f"{room}: the cat shows up in the tuple at some standpoints", n_cat > 0)
world("study", cat_loc="windowsill", fire="burning")
sdp = SPT.depth("study", "at_the_hearth")
check("study tuple gains no 'nearest' key", "nearest" not in sdp)

print("[3] flag off: render() is the base line for garden and shore")
SPT.SPATIAL_DEPTH_OUTDOOR_LIVE = False
bad = 0
for room in ("garden", "shore"):
    for i, sp_name in enumerate(list(SPT.layout(room)["standpoints"])):
        world(room, cat_loc=_CATLOC[room][0])
        random.seed(i)
        a = SPT.render(room, sp_name)
        random.seed(i)
        b = SPT._render_base(room, sp_name)
        bad += (a != b)
check("render() == _render_base() on every outdoor standpoint", bad == 0, str(bad))

print("[4] flag on: only the cat clause moves")
SPT.SPATIAL_DEPTH_OUTDOOR_LIVE = True
differ = 0
seen_cat = 0
bad = 0
for room in ("garden", "shore"):
    for i, sp_name in enumerate(list(SPT.layout(room)["standpoints"])):
        for catloc in _CATLOC[room][:2] + ("absent",):
            world(room, cat_loc=catloc)
            random.seed(i)
            off = SPT._render_base(room, sp_name)
            random.seed(i)
            on = SPT.render(room, sp_name)
            if not off:
                continue
            ok = on["standpoint"] == off["standpoint"] and len(on["clauses"]) == len(off["clauses"])
            for x, y in zip(off["clauses"], on["clauses"]):
                if x.startswith("the cat is "):
                    seen_cat += 1
                    place = x.split(", ")[0]
                    ok = ok and y.startswith(place + ", ")
                    ok = ok and x.split(", ", 1)[1] == y.split(", ", 2)[2]       # same sector/elev tail
                    word = y.split(", ")[1]
                    ok = ok and word in ("right beside you", "near", "a little way off", "far off")
                    differ += (x != y)
                else:
                    ok = ok and x == y
            low = " " + on["line"].lower() + " "
            ok = ok and not any(c.isdigit() for c in on["line"]) and " reach " not in low and "band" not in low
            bad += (not ok)
check("every outdoor line: count same, non-cat clauses verbatim, cat clause keeps place + sector, outdoor distance word, no digit/reach/band",
      bad == 0, str(bad))
check("some cat clauses really were re-said", seen_cat > 0 and differ > 0, f"seen {seen_cat} differ {differ}")
SPT.SPATIAL_DEPTH_OUTDOOR_LIVE = False

print("[5] study unaffected by the outdoor flag")
world("study", cat_loc="windowsill", fire="burning")
SPT.SPATIAL_DEPTH_LIVE = True
res = []
for flag in (False, True):
    SPT.SPATIAL_DEPTH_OUTDOOR_LIVE = flag
    random.seed(3)
    res.append(SPT.render("study", "at_the_hearth"))
SPT.SPATIAL_DEPTH_OUTDOOR_LIVE = False
check("study line identical with the outdoor flag off and on", res[0] == res[1])
check("_depth_is_live: study follows SPATIAL_DEPTH_LIVE, wood never",
      SPT._depth_is_live("study") is True and SPT._depth_is_live("wood") is False)

print("[6] shadow() end to end, inside lab_env.isolate()")
L.position_standpoint = lambda room=None: "at_the_bed"
with lab_env.isolate(also=[(SPT, ["_SHADOW", "_DEPTH_SHADOW", "_DEPTH_OUTDOOR_SHADOW"])], db="empty") as lab:
    check("paths redirected into the sandbox", str(SPT._DEPTH_OUTDOOR_SHADOW).startswith(str(lab)))
    world("garden", cat_loc="raised_bed")
    SPT.shadow(actual="Where you are: the garden, pool line.")
    out_p = Path(SPT._DEPTH_OUTDOOR_SHADOW)
    rows = [json.loads(x) for x in out_p.read_text(encoding="utf-8").splitlines() if x.strip()] if out_p.exists() else []
    check("one garden row in the OUTDOOR log", len(rows) == 1 and rows[0].get("room") == "garden", str(rows)[:200])
    if rows:
        r = rows[0]
        check("row: live False, nearest + reach logged, scene == depth_line (flag off), not changed",
              r["live"] is False and r["nearest"] and isinstance(r["reach"], list)
              and r["depth_line"] == r["scene"] and r["changed"] is False)
    check("study depth log untouched", not Path(SPT._DEPTH_SHADOW).exists() or Path(SPT._DEPTH_SHADOW).stat().st_size == 0)
    SPT.SPATIAL_DEPTH_OUTDOOR_SHADOW = False
    SPT.shadow(actual="x")
    rows2 = [x for x in out_p.read_text(encoding="utf-8").splitlines() if x.strip()]
    SPT.SPATIAL_DEPTH_OUTDOOR_SHADOW = True
    check("shadow flag off -> no new row", len(rows2) == 1)
    st = SPT.depth_outdoor_status()
    check("[7] depth_outdoor_status reads it back", st["rows"] == 1 and st["by_room"] == {"garden": 1}, str(st)[:200])

print("[8] live stores untouched")
for p in _WATCH:
    check(f"unchanged: {p.name}", _snap(p) == _before[p])

shutil.rmtree(TMP, ignore_errors=True)
print("\nALL OK" if not FAILS else f"\n{FAILS} FAILURE(S)")
sys.exit(1 if FAILS else 0)
