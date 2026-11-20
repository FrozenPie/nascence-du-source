"""
Regression: the SCENE-extra RENDER LEDGER (J-1694 / F-2293).

The gap: world_detail.scene_extra() left no record of a draw, so J-1014's four record-player read-backs (F-1466, F-1624,
F-1741, F-2293) could not COUNT the exposure they were measuring -- data/spatial_shadow.jsonl cuts the scene to 220 chars
(the study's base scene alone is longer, so no study-place extra is ever visible there) and data/training/voice.jsonl is a
sample. The build: every NON-EMPTY scene_extra() draw appends one row {ts, loc, place, conds, line, pool} to
data/scene_extra_ledger.jsonl (core/scene_extra_ledger.py), observe-only and fail-open.

What this proves, ISOLATED: no model, no live data. The ledger path is redirected into a temp dir before a row is written,
the sensorium's room_state and locomotion's position store likewise (the S-0016 / test-isolation rule), and the live
C:\\Nascence\\data stores are stat-ed (the small ones hashed) before and after, the live ledger asserted still absent.
  [1] surface     the module and its path, the optional place= kwarg (default ''), SCENE_P untouched
  [2] exact       over a place x phase x weather x season x tide x wind grid, at SCENE_P 0.25 and forced 1.0: one row per
                  NON-EMPTY draw and none per empty one, each row's loc/place/conds/line/pool equals what the content
                  modules say; AND the returned line and the random.getstate() after the call are identical to the
                  pre-J-1694 function (a verbatim copy below): no draw added, none reordered, no line changed
  [3] fail-open   an unwritable path, a directory as the path, a raising record() and a non-live process on the default
                  path each leave the draw (line AND RNG state) exactly as the reference, with no exception and no file
  [4] the fence   (a simulated data/ root, never the real one) a non-live process is refused, the live boot writes, a
                  data/_lab/<stamp>/ sandbox writes, data/_lab/<file> directly stays refused -- profile.guard_path as the
                  cat-sound ledger uses it, but the refusal is swallowed, not re-raised
  [5] call site   through the real scene_line(): one row per drawn extra, loc == place == where he is, the row's line is
                  the scene's final extra; study / garden / shore / wood; an unknown place draws and records nothing;
                  a raising record() still leaves the scene carrying its extra
  [6] readers     read_rows() / status() on a hand-made file with a garbage line, a torn last line; a missing file
  [7] the live stores are untouched, and neither the live nor the worktree ledger exists

  python scripts/_test_j1694_scene_extra_ledger.py        # exit 0 = ALL OK
"""
from __future__ import annotations

import hashlib
import inspect
import itertools
import json
import random
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TMP = Path(tempfile.mkdtemp(prefix="j1694_scene_extra_ledger_"))
print("isolated store dir:", TMP)

# data/ is gitignored and never checked out into a job-run worktree, so "live" is the one real repo, never ROOT-relative.
_LIVE_DATA = Path(r"C:\Nascence") / "data"
_LIVE_LEDGER = _LIVE_DATA / "scene_extra_ledger.jsonl"
_WORKTREE_LEDGER = ROOT / "data" / "scene_extra_ledger.jsonl"
_WATCH = [_LIVE_LEDGER, _LIVE_DATA / "room_state.json", _LIVE_DATA / "position.json", _LIVE_DATA / "cat_state.json",
          _LIVE_DATA / "spatial_shadow.jsonl", _LIVE_DATA / "memory" / "nascence.db",
          _LIVE_DATA / "memory" / "nascence.db-wal"]


def _snap(p: Path):
    if not p.exists():
        return None
    st = p.stat()
    md5 = hashlib.md5(p.read_bytes()).hexdigest() if st.st_size < 5_000_000 else ""
    return (st.st_size, st.st_mtime_ns, md5)


_before = {p: _snap(p) for p in _WATCH}
_ledgers_existed = [p.exists() for p in (_LIVE_LEDGER, _WORKTREE_LEDGER)]

from core import profile as P                      # noqa: E402
from core import scene_extra_ledger as LED         # noqa: E402
from core import sensorium as S                    # noqa: E402
from core import locomotion as L                   # noqa: E402
from core import world_detail as WD                # noqa: E402
from core import spatial as SPT                    # noqa: E402
from core import world_content_study as C_STUDY    # noqa: E402
from core import world_content_garden as C_GARDEN  # noqa: E402
from core import world_content_shore as C_SHORE    # noqa: E402
from core import world_content_wood as C_WOOD      # noqa: E402

S._STATE_F = TMP / "room_state.json"
L._POS_F = TMP / "position.json"
assert not str(S._STATE_F).lower().startswith(r"c:\nascence\data") and not str(L._POS_F).lower().startswith(r"c:\nascence\data")
_DEFAULT_LEDGER = LED._LEDGER
_real_record = LED.record
LED._LEDGER = TMP / "unused_until_redirected.jsonl"          # nothing below may reach the default path by accident

FAILS = 0


def check(cond: bool, label: str) -> None:
    global FAILS
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS += 1


PLACES = ("study", "garden", "shore", "wood")
CONTENT = {"study": C_STUDY, "garden": C_GARDEN, "shore": C_SHORE, "wood": C_WOOD}
WD._load()
_PLACE_OK = "place" in inspect.signature(WD.scene_extra).parameters


def expected_row(pool_place: str, phase: str, weather: str, season: str, tide: str, wind: str):
    """(matched conds sorted, pool size, lines) the ledger must report, from the content module itself -- not from
    world_detail's loaded copy, so a loader bug cannot hide."""
    conds = WD._conds(phase, weather, season, tide, wind)
    scene = CONTENT[pool_place].SCENE
    matched = sorted(c for c, lines in scene.items() if c in conds and lines)
    lines = [l for c in matched for l in scene[c]]
    return matched, len(lines), set(lines)


def ref_scene_extra(location, phase, weather, season, tide="", wind=""):
    """The pre-J-1694 scene_extra() VERBATIM (core/world_detail.py at 2b2dc3a): the yardstick for 'nothing else changed'."""
    if random.random() > WD.SCENE_P:
        return ""
    sc = WD._SCENE.get(location) or {}
    conds = WD._conds(phase, weather, season, tide, wind)
    pool = [l for c, lines in sc.items() if c in conds for l in lines]
    return random.choice(pool) if pool else ""


def new_scene_extra(location, phase, weather, season, tide, wind):
    return (WD.scene_extra(location, phase, weather, season, tide, wind=wind, place=location) if _PLACE_OK
            else WD.scene_extra(location, phase, weather, season, tide, wind=wind))


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
print("\n[1] surface")
check(_DEFAULT_LEDGER == ROOT / "data" / "scene_extra_ledger.jsonl", "the ledger is data/scene_extra_ledger.jsonl")
check(all(callable(getattr(LED, n, None)) for n in ("record", "read_rows", "status")), "record() / read_rows() / status() exist")
check(_PLACE_OK and inspect.signature(WD.scene_extra).parameters["place"].default == "",
      "scene_extra() takes an optional place= (default ''): every existing caller is unaffected")
check(WD.SCENE_P == 0.25, "SCENE_P is still 0.25 (untouched)")

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
print("\n[2] exact: one row per NON-EMPTY draw, none per empty one; the draw itself is byte-identical to the old function")
GRID = list(itertools.product(PLACES + ("attic",), ("day", "night"), ("clear", "steady rain"), ("summer", "winter"),
                              ("", "high"), ("calm", "gale")))
_scene_p_orig = WD.SCENE_P


def run_grid(scene_p: float, tag: str):
    WD.SCENE_P = scene_p
    path = TMP / f"grid_{tag}.jsonl"
    LED._LEDGER = path
    expected, mismatches, n_calls, n_empty_pooled, n_error = [], 0, 0, 0, 0
    t0 = time.time()
    for i, (loc, ph, w, se, t, wi) in enumerate(GRID):
        for rep in range(6):
            seed = f"{tag}|{i}|{rep}"
            random.seed(seed)
            want = ref_scene_extra(loc, ph, w, se, t, wi)
            st_ref = random.getstate()
            random.seed(seed)
            try:
                got = new_scene_extra(loc, ph, w, se, t, wi)
            except Exception:
                n_error += 1
                continue
            st_new = random.getstate()
            n_calls += 1
            if got != want or st_new != st_ref:
                mismatches += 1
            if got:
                matched, size, lines = expected_row(loc, ph, w, se, t, wi)
                expected.append((loc, loc, matched, got, size))
                if got not in lines:
                    mismatches += 1
            elif loc != "attic":
                n_empty_pooled += 1
    t1 = time.time()
    rows = LED.read_rows(path=path)
    got_rows = [(r["loc"], r["place"], r["conds"], r["line"], r["pool"]) for r in rows]
    return {"rows": rows, "got_rows": got_rows, "expected": expected, "mismatches": mismatches, "calls": n_calls,
            "empty_pooled": n_empty_pooled, "errors": n_error, "t0": t0, "t1": t1}


try:
    for scene_p, tag in ((0.25, "p025"), (1.0, "p100")):
        r = run_grid(scene_p, tag)
        n = len(r["expected"])
        check(r["errors"] == 0 and r["calls"] == len(GRID) * 6, f"SCENE_P={scene_p}: {r['calls']} draws, none raised")
        check(r["mismatches"] == 0, f"SCENE_P={scene_p}: the returned line AND random.getstate() equal the pre-J-1694 function's on every draw "
              f"(mismatches={r['mismatches']}): no draw added, none reordered, no line changed")
        check(n > 0 and len(r["rows"]) == n, f"SCENE_P={scene_p}: {len(r['rows'])} rows for {n} non-empty draws")
        check(r["got_rows"] == r["expected"], f"SCENE_P={scene_p}: every row's loc/place/conds/line/pool equals the content modules', in draw order")
        if scene_p < 1.0:
            check(r["empty_pooled"] > 0, f"SCENE_P={scene_p}: {r['empty_pooled']} empty draws at pooled places wrote no row (rows == non-empty draws)")
        check(not any(x["loc"] == "attic" for x in r["rows"]), f"SCENE_P={scene_p}: a place with no pool ('attic') draws nothing and records nothing")
        check(all(set(x) == {"ts", "loc", "place", "conds", "line", "pool"} for x in r["rows"]), f"SCENE_P={scene_p}: every row has exactly the six fields")
        check(all(isinstance(x["ts"], float) and r["t0"] - 0.2 <= x["ts"] <= r["t1"] + 0.2 for x in r["rows"]), f"SCENE_P={scene_p}: ts is the draw time")
        check(all(x["conds"] == sorted(x["conds"]) and "any" in x["conds"] and x["pool"] >= 1 for x in r["rows"]),
              f"SCENE_P={scene_p}: conds are sorted and include 'any'; pool >= 1")
        if scene_p == 1.0:
            seen = {p: {x["line"] for x in r["rows"] if x["loc"] == p} for p in PLACES}
            check(all(seen[p] for p in PLACES), f"SCENE_P=1.0: all four places recorded rows ({ {p: len(v) for p, v in seen.items()} } distinct lines)")
            conds_seen = {c for x in r["rows"] for c in x["conds"]}
            check({"any", "night", "wet", "windy", "winter"} <= conds_seen, f"SCENE_P=1.0: the night / wet / windy / winter keys were all recorded ({sorted(conds_seen)})")
finally:
    WD.SCENE_P = _scene_p_orig

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
print("\n[3] fail-open: nothing about the ledger can change a draw or raise")


def fail_open_case(label: str, expect_false: bool):
    WD.SCENE_P = 1.0
    bad, raised, wrote = 0, 0, 0
    for k in range(60):
        seed = f"fo|{label}|{k}"
        random.seed(seed)
        want = ref_scene_extra("study", "day", "clear", "summer", "", "calm")
        st_ref = random.getstate()
        random.seed(seed)
        try:
            got = new_scene_extra("study", "day", "clear", "summer", "", "calm")
        except Exception:
            raised += 1
            continue
        if got != want or random.getstate() != st_ref or not got:
            bad += 1
    if expect_false:
        wrote = int(LED.record("study", "study", ["any"], "x", 1) is True)
    WD.SCENE_P = _scene_p_orig
    check(raised == 0 and bad == 0 and wrote == 0, f"{label}: 60 draws, line and RNG state identical to the reference, none raised, record() False (raised={raised}, bad={bad}, wrote={wrote})")


try:
    blocker = TMP / "blocker"
    blocker.write_text("a file where the ledger's directory should be", encoding="utf-8")
    LED._LEDGER = blocker / "ledger.jsonl"
    fail_open_case("unwritable path (parent is a file)", True)

    adir = TMP / "adir"
    adir.mkdir()
    LED._LEDGER = adir
    fail_open_case("a directory where the ledger file should be", True)

    def _boom(*a, **k):
        raise RuntimeError("record exploded")
    LED._LEDGER = TMP / "boom.jsonl"
    LED.record = _boom
    fail_open_case("record() raising", False)
    LED.record = _real_record
    check(not (TMP / "boom.jsonl").exists(), "record() raising wrote nothing")

    LED._LEDGER = _DEFAULT_LEDGER
    check(P.LIVE is False, "this process is NOT live (profile.LIVE is False), as every test and diagnostic is")
    fail_open_case("non-live process on the DEFAULT data/ path (the D-0179 fence refuses)", True)
    check(_LIVE_LEDGER.exists() == _ledgers_existed[0] and _WORKTREE_LEDGER.exists() == _ledgers_existed[1],
          "the default-path attempts created no file, in the worktree or in the live data/")
finally:
    LED.record = _real_record
    LED._LEDGER = TMP / "unused_until_redirected.jsonl"
    WD.SCENE_P = _scene_p_orig

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
print("\n[4] the write fence, on a SIMULATED data/ root (the real one is never written)")
fake = TMP / "fake_root" / "data"
fake.mkdir(parents=True)
_saved = (P._DATA, P._CANONICAL_DATA, P.LIVE, LED._LEDGER)
try:
    P._DATA = P._CANONICAL_DATA = fake
    led = fake / "scene_extra_ledger.jsonl"
    LED._LEDGER = led
    P.LIVE = False
    check(LED.record("study", "study", ["any"], "x", 3) is False and not led.exists(),
          "a non-live process aimed at data/ is refused: no row, no file, no exception (a non-live profile never writes the live ledger)")
    P.LIVE = True
    check(LED.record("study", "study", ["any", "night"], "x", 3) is True and len(LED.read_rows(path=led)) == 1,
          "the live boot (profile.mark_live) writes its row")
    P.LIVE = False
    lab = fake / "_lab" / "20261003_000000" / "scene_extra_ledger.jsonl"
    LED._LEDGER = lab
    check(LED.record("study", "study", ["any"], "x", 3) is True and lab.exists(),
          "a lab_env.isolate() sandbox, data/_lab/<stamp>/, may write")
    LED._LEDGER = fake / "_lab" / "scene_extra_ledger.jsonl"
    check(LED.record("study", "study", ["any"], "x", 3) is False and not LED._LEDGER.exists(),
          "data/_lab/<file> with no sandbox directory stays refused")
finally:
    P._DATA, P._CANONICAL_DATA, P.LIVE, LED._LEDGER = _saved

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
print("\n[5] the call site: scene_line() -> scene_extra() -> one ledger row per drawn extra")
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
    reset(loc, weather, wind)
    CALLS.clear()
    RET.clear()
    S._daylight, S._season = (lambda: phase), (lambda: season)
    return S.scene_line(), (CALLS[-1] if CALLS else None), (RET[-1] if RET else None)


_orig_daylight, _orig_season = S._daylight, S._season
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
    WD.SCENE_P = 1.0
    cs_path = TMP / "callsite_p100.jsonl"
    LED._LEDGER = cs_path
    for loc in PLACES:
        n_builds = bad = no_place = 0
        for i, (ph, se, w, wi) in enumerate(itertools.product(("day", "night"), ("summer", "winter"), ("clear", "steady rain"), ("calm", "gale"))):
            for rep in range(2):
                random.seed(f"cs|{loc}|{i}|{rep}")
                before = len(LED.read_rows(path=cs_path))
                scene, call, ret = build(loc, ph, se, w, wi)
                new = LED.read_rows(path=cs_path)[before:]
                args, kw = call
                n_builds += 1
                if kw.get("place") != loc:
                    no_place += 1
                matched, size, lines = expected_row(loc, args[1], args[2], args[3], args[4], kw["wind"])
                ok = (len(new) == 1 and ret in lines and scene.endswith(ret) and new[0]["loc"] == loc and new[0]["place"] == loc
                      and new[0]["line"] == ret and new[0]["conds"] == matched and new[0]["pool"] == size)
                bad += 0 if ok else 1
        check(no_place == 0, f"{loc:6s} scene_line() passes place={loc!r} to scene_extra on all {n_builds} builds")
        check(bad == 0, f"{loc:6s} {n_builds} scene builds: exactly one row each, loc == place == {loc!r}, its line is the scene's final extra, "
              f"conds and pool as the content says (bad={bad})")
    scene, call, ret = build("attic")
    check(ret == "" and call[1].get("place") == "attic" and all(x["loc"] != "attic" for x in LED.read_rows(path=cs_path)),
          "attic  an unknown place: place='attic' is passed, no pool, no extra, no row")

    WD.SCENE_P = _scene_p_orig
    ds_path = TMP / "callsite_p025.jsonl"
    LED._LEDGER = ds_path
    n_nonempty = n_empty = 0
    for k in range(300):
        random.seed(f"cs025|{k}")
        scene, call, ret = build("study", "day", "summer", "clear", "calm")
        n_nonempty += 1 if ret else 0
        n_empty += 0 if ret else 1
    rows025 = LED.read_rows(path=ds_path)
    check(n_nonempty > 0 and n_empty > 0 and len(rows025) == n_nonempty,
          f"study  SCENE_P=0.25, 300 real scene builds: {n_nonempty} drew an extra, {n_empty} did not, ledger rows = {len(rows025)} (== the draws that returned a line)")
    check(all(x["loc"] == x["place"] == "study" for x in rows025), "study  every default-rate row says loc == place == 'study'")

    print("  -- fail-open at the call site: a raising record() leaves the scene carrying its extra")
    WD.SCENE_P = 1.0
    LED._LEDGER = TMP / "callsite_boom.jsonl"
    random.seed("cs-ok")
    scene_ok, _, ret_ok = build("wood", "day", "summer", "clear", "calm")
    LED.record = _boom
    random.seed("cs-ok")
    scene_boom, _, ret_boom = build("wood", "day", "summer", "clear", "calm")
    LED.record = _real_record
    check(ret_ok and scene_boom == scene_ok and ret_boom == ret_ok and scene_boom.endswith(ret_boom),
          "wood   the same seed builds the SAME scene whether record() works or raises (scene identical, extra present)")
    random.seed("cs-ok2")
    LED.record = _boom
    scene_s2, _, ret_s2 = build("study", "night", "winter", "steady rain", "gale")
    LED.record = _real_record
    check(ret_s2 and scene_s2.endswith(ret_s2), "study  a raising record() still leaves the study scene carrying its extra")
    check(not (TMP / "callsite_boom.jsonl").exists() or len(LED.read_rows(path=TMP / "callsite_boom.jsonl")) == 1,
          "...and only the one working build wrote a row")
finally:
    LED.record = _real_record
    WD.scene_extra = _real_scene_extra
    WD.SCENE_P = _scene_p_orig
    S._daylight, S._season = _orig_daylight, _orig_season
    for _k, _v in _orig_stubbed.items():
        setattr(S, _k, _v)
    SPT.SPATIAL_SCENE = _orig_spatial
    LED._LEDGER = TMP / "unused_until_redirected.jsonl"

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
print("\n[6] readers: read_rows() / status() on a hand-made file")
good = [{"ts": 100.0, "loc": "study", "place": "study", "conds": ["any"], "line": "a", "pool": 2},
        {"ts": 200.0, "loc": "wood", "place": "wood", "conds": ["any", "night"], "line": "b", "pool": 4},
        {"ts": 300.0, "loc": "study", "place": "study", "conds": ["any"], "line": "c", "pool": 2}]
hand = TMP / "handmade.jsonl"
hand.write_text(json.dumps(good[0]) + "\nnot json at all\n" + json.dumps(good[1]) + "\n\n" + json.dumps(good[2]) + "\n"
                + '{"ts": 400.0, "loc": "stu', encoding="utf-8")          # a garbage line, a blank line, a torn last line
check(LED.read_rows(path=hand) == good, "read_rows() returns the three good rows in order, skipping garbage, blank and torn lines")
check(LED.read_rows(200.0, path=hand) == good[1:], "read_rows(since_ts=200) returns the rows with ts >= 200")
st = LED.status(path=hand)
check(st["ledger_rows"] == 3 and st["first_ts"] == 100.0 and st["last_ts"] == 300.0 and st["by_loc"] == {"study": 2, "wood": 1},
      f"status() counts them: {st['ledger_rows']} rows, {st['first_ts']}..{st['last_ts']}, by_loc {st['by_loc']}")
none = TMP / "does_not_exist.jsonl"
stn = LED.status(path=none)
check(LED.read_rows(path=none) == [] and stn["ledger_rows"] == 0 and stn["first_ts"] is None and stn["last_ts"] is None and stn["by_loc"] == {},
      "a missing ledger reads as [] / zero rows, never an exception")
LED._LEDGER = hand
check(LED.status()["ledger_rows"] == 3 and LED.status()["path"] == str(hand), "status() with no argument reads the module's own _LEDGER")
LED._LEDGER = TMP / "unused_until_redirected.jsonl"

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
print("\n[7] the live stores are untouched, and no real ledger was created")
for p in _WATCH:
    after = _snap(p)
    check(after == _before[p], f"{p.name}: unchanged ({'absent' if after is None else f'{after[0]} bytes'})")
check(_ledgers_existed == [_LIVE_LEDGER.exists(), _WORKTREE_LEDGER.exists()],
      f"neither the live ledger nor the worktree ledger was created or removed (existed before: {_ledgers_existed})")

print("\nFAILS =", FAILS)
print("ALL OK" if FAILS == 0 else "SOME CHECKS FAILED")
sys.exit(1 if FAILS else 0)
