"""
Regression: the LOOK-TARGET RENDER LEDGER (J-1899 / D-0360 (c) option 3 "measure first"; F-2505 section 5).

The gap: world_detail.detail() (a look at a NEW target) and extra_pool() (extra lines merged into an EXISTING target's pool)
left no record of which pool line a look rendered, so F-2505 could not count how often Du looks at the diurnal garden / shore /
wood bird targets at night. The build: every rendered look appends one row {ts, src, loc, target, key, phase, conds, pool,
line_id, line} to data/look_render_ledger.jsonl (core/look_render_ledger.py), observe-only, fail-open, fenced, rotated.

What this proves, ISOLATED: no model, no live data. Every ledger path is redirected into a temp dir before a row is written,
the sensorium's room_state likewise (the S-0016 / test-isolation rule), and the live C:\\Nascence\\data stores are stat-ed
(the small ones hashed) before and after, the live ledger asserted still absent.
  [1] surface     the module, its path, the callable surface, RARE_P / SCENE_P untouched
  [2] exact       over EVERY target x phase x weather x season x tide x wind sample, with seeded draws: the line returned by
                  detail() AND random.getstate() afterwards are identical for (a) the pre-J-1899 function (a verbatim copy
                  below), (b) the new function with the ledger ON, (c) the new function with the ledger OFF (record a no-op);
                  one row per non-empty return, none per empty one; each row's shape / key / conds / pool / line_id / prefix
                  is what the content modules say (the key is the pool that actually holds the line, "rare" for the tail)
  [3] extra_pool  extra_pool() returns exactly what it returned before and writes nothing itself; note_extra_pick() writes a row
                  only when the line drawn is one of the extras; and through the REAL sensorium._living_detail(): the text and
                  the RNG state are identical with the ledger on and off, a row appears exactly when the drawn line is an extra
  [4] fail-open   an unwritable path, a directory as the path, a raising record() and a non-live process on the DEFAULT path each
                  leave the draw (line AND RNG state) exactly as the reference, with no exception and no file
  [5] the fence   (a simulated data/ root, never the real one) a non-live process is refused, the live boot writes, a
                  data/_lab/<stamp>/ sandbox writes, data/_lab/<file> stays refused; a NAMED profile (activate_profile, not
                  live) is refused as well
  [6] rotation    past ROTATE_BYTES the file is renamed over <name>.1 and a fresh file starts; read_rows() spans both; a second
                  rotation replaces the one kept generation; night_looks() counts night rows per bird target
  [7] readers     read_rows() / status() on a hand-made file with a garbage line and a torn last line; a missing file
  [8] the live stores are untouched, and neither the live nor the worktree ledger exists

  python scripts/_test_j1899_look_render_ledger.py        # exit 0 = ALL OK
"""
from __future__ import annotations

import hashlib
import inspect
import os
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

TMP = Path(tempfile.mkdtemp(prefix="j1899_look_render_ledger_"))
print("isolated store dir:", TMP)

# data/ is gitignored and never checked out into a job-run worktree, so "live" is the one real repo, never ROOT-relative.
_LIVE_DATA = Path(r"C:\Nascence") / "data"
_LIVE_LEDGER = _LIVE_DATA / "look_render_ledger.jsonl"
_WORKTREE_LEDGER = ROOT / "data" / "look_render_ledger.jsonl"
# Du is LIVE (2026-10-07) and writes room_state.json, position.json, cat_state.json, spatial_shadow.jsonl and nascence.db itself, so a
# before/after hash of those proves nothing; the proof that THIS process never wrote real data is the audit hook below. The hash watch
# keeps only the two stores nothing but this feature (and the scene ledger's own job) writes.
_WATCH = [_LIVE_LEDGER, _LIVE_LEDGER.with_name("look_render_ledger.jsonl.1")]
_REAL_ROOTS = [os.path.normcase(str(_LIVE_DATA.resolve())), os.path.normcase(str((ROOT / "data").resolve()))]
HOOK_EVENTS: list = []
_WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC


def _hook(event, args):
    try:
        if event == "open":
            m, fl = args[1], args[2]
            w = (isinstance(m, str) and any(c in m for c in "wax+")) or (isinstance(fl, int) and bool(fl & _WRITE_FLAGS) and m != "r")
            path = args[0]
        elif event in ("os.rename", "os.replace"):
            w, path = True, args[1]
        elif event in ("os.remove", "os.mkdir", "os.rmdir"):
            w, path = True, args[0]
        elif event == "sqlite3.connect":
            w, path = True, args[0]
        else:
            return
        if not w or isinstance(path, int):
            return
        n = os.path.normcase(os.path.abspath(os.fsdecode(path) if isinstance(path, bytes) else os.fspath(path)))
        if any(n == r or n.startswith(r + os.sep) for r in _REAL_ROOTS):
            HOOK_EVENTS.append((event, n))
            raise PermissionError(f"J-1899 test hook: blocked real-data {event} {n}")
    except PermissionError:
        raise
    except Exception:
        return


sys.addaudithook(_hook)


def _snap(p: Path):
    if not p.exists():
        return None
    st = p.stat()
    md5 = hashlib.md5(p.read_bytes()).hexdigest() if st.st_size < 5_000_000 else ""
    return (st.st_size, st.st_mtime_ns, md5)


_before = {p: _snap(p) for p in _WATCH}
_ledgers_existed = [p.exists() for p in (_LIVE_LEDGER, _WORKTREE_LEDGER)]

import core                                          # noqa: E402  (core BEFORE anything lab-ish)
assert Path(core.__file__).resolve().parent.parent == ROOT, core.__file__
from core import profile as P                       # noqa: E402
from core import look_render_ledger as LED          # noqa: E402
from core import sensorium as S                     # noqa: E402
from core import world_detail as WD                 # noqa: E402

assert Path(WD.__file__).resolve().parent.parent == ROOT and Path(LED.__file__).resolve().parent.parent == ROOT

S._STATE_F = TMP / "room_state.json"
assert not str(S._STATE_F).lower().startswith(r"c:\nascence\data")
_DEFAULT_LEDGER = LED._LEDGER
_real_record = LED.record
LED._LEDGER = TMP / "unused_until_redirected.jsonl"          # nothing below may reach the default path by accident

FAILS = 0


def check(cond: bool, label: str) -> None:
    global FAILS
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS += 1


WD._load()


def ref_detail(location, target_text, phase, weather, season, tide="", wind=""):
    """The pre-J-1899 detail() VERBATIM (core/world_detail.py at d8a083b): the yardstick for 'nothing else changed'."""
    spec = WD._match(target_text, location)
    if not spec:
        return ""
    conds = WD._conds(phase, weather, season, tide, wind)
    if spec["rare"] and random.random() < WD.RARE_P:
        return random.choice(spec["rare"])
    pool = [l for c, lines in spec["pools"].items() if c in conds for l in lines]
    return random.choice(pool) if pool else ""


def off_record(*a, **k):
    return False


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
print("\n[1] surface")
check(_DEFAULT_LEDGER == ROOT / "data" / "look_render_ledger.jsonl", "the ledger is data/look_render_ledger.jsonl")
check(all(callable(getattr(LED, n, None)) for n in ("record", "read_rows", "status", "night_looks", "line_id")),
      "record() / read_rows() / status() / night_looks() / line_id() exist")
check(callable(getattr(WD, "note_extra_pick", None)), "world_detail.note_extra_pick() exists")
check(WD.RARE_P == 0.08 and WD.SCENE_P == 0.25, "RARE_P is still 0.08 and SCENE_P 0.25 (untouched)")
check(list(inspect.signature(WD.detail).parameters) == ["location", "target_text", "phase", "weather", "season", "tide", "wind"]
      and list(inspect.signature(WD.extra_pool).parameters) == ["target_text", "phase", "weather", "season", "tide", "wind"],
      "detail() and extra_pool() keep their exact signatures")
check(LED.BIRD_TARGETS == ("garden:birds", "shore:birds", "wood:birds") and all(t in WD._REGISTRY for t in LED.BIRD_TARGETS),
      "the three D-0360 (c) bird targets exist in the registry under those names")

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
print("\n[2] exact: the draw is byte-identical, one row per non-empty return, rows say what the content says")
SPECS = [(k, v) for k, v in WD._REGISTRY.items()]
PHASES = ("dawn", "day", "dusk", "night")
WEATHERS = ("clear", "high cloud", "steady rain", "overcast")
SEASONS = ("summer", "winter")
TIDES = ("", "high", "low")
WINDS = ("calm", "gale")
GRID = list(itertools.product(PHASES, WEATHERS, SEASONS, TIDES, WINDS))


def alias_for(spec):
    return spec["aliases"][0]


def run_detail_grid(path: Path, reps: int):
    LED._LEDGER = path
    LED.record = _real_record
    expected, mism, calls, errors, empties = [], 0, 0, 0, 0
    t0 = time.time()
    for key, spec in SPECS:
        for gi, (ph, w, se, t, wi) in enumerate(GRID):
            for rep in range(reps):
                seed = f"{key}|{gi}|{rep}"
                random.seed(seed)
                want = ref_detail(spec["location"], alias_for(spec), ph, w, se, t, wi)
                st_ref = random.getstate()
                random.seed(seed)
                LED.record = off_record
                got_off = WD.detail(spec["location"], alias_for(spec), ph, w, se, t, wi)
                st_off = random.getstate()
                LED.record = _real_record
                random.seed(seed)
                try:
                    got = WD.detail(spec["location"], alias_for(spec), ph, w, se, t, wi)
                except Exception:
                    errors += 1
                    continue
                st_new = random.getstate()
                calls += 1
                if not (got == want == got_off and st_new == st_ref == st_off):
                    mism += 1
                if got:
                    expected.append((key, ph, sorted(WD._conds(ph, w, se, t, wi)), got))
                else:
                    empties += 1
    return {"rows": LED.read_rows(path=path), "expected": expected, "mism": mism, "calls": calls, "errors": errors,
            "empties": empties, "t0": t0, "t1": time.time()}


grid_path = TMP / "grid.jsonl"
r = run_detail_grid(grid_path, 3)
n = len(r["expected"])
check(r["errors"] == 0 and r["calls"] == len(SPECS) * len(GRID) * 3,
      f"{r['calls']} seeded draws over {len(SPECS)} targets x {len(GRID)} conditions, none raised")
check(r["mism"] == 0, f"returned line AND random.getstate() equal for the pre-J-1899 function, ledger ON and ledger OFF on every draw "
      f"(mismatches={r['mism']}): no draw added, none reordered, no line changed")
check(n > 0 and len(r["rows"]) == n, f"{len(r['rows'])} rows for {n} non-empty draws (empty draws: {r['empties']}, no row)")
got_rows = [(x["target"], x["phase"], x["conds"], None) for x in r["rows"]]
check([(a, b, c) for a, b, c, _ in r["expected"]] == [(a, b, c) for a, b, c, _ in got_rows],
      "every row's target / phase / conds equals the draw's, in draw order")
FIELDS = {"ts", "src", "loc", "target", "key", "phase", "conds", "pool", "line_id", "line"}
check(all(set(x) == FIELDS for x in r["rows"]), "every row has exactly the ten fields")
check(all(x["src"] == "detail" for x in r["rows"]), "every grid row is src 'detail'")
check(all(isinstance(x["ts"], float) and r["t0"] - 0.2 <= x["ts"] <= r["t1"] + 0.2 for x in r["rows"]), "ts is the draw time")
ok_line = ok_key = ok_loc = ok_pool = 0
for x, (key, ph, conds, line) in zip(r["rows"], r["expected"]):
    spec = WD._REGISTRY[key]
    ok_line += 1 if (x["line_id"] == LED.line_id(line) and line.startswith(x["line"]) and len(x["line"]) <= LED.LINE_PREFIX) else 0
    held = [c for c, lines in spec["pools"].items() if line in lines]
    ok_key += 1 if ((x["key"] == "rare" and line in spec["rare"] and not held) or (x["key"] in held and x["key"] in x["conds"])) else 0
    ok_loc += 1 if (x["loc"] == spec["location"] and x["target"] == key) else 0
    if x["key"] == "rare":
        ok_pool += 1 if x["pool"] == len(spec["rare"]) else 0
    else:
        ok_pool += 1 if x["pool"] == sum(len(l) for c, l in spec["pools"].items() if c in x["conds"]) else 0
check(ok_line == n, f"line_id is sha1(line)[:10] and 'line' is a <= {LED.LINE_PREFIX}-char prefix of it ({ok_line}/{n})")
check(ok_key == n, f"'key' is the pool that holds the line (and was emitted), or 'rare' for the tail ({ok_key}/{n})")
check(ok_loc == n, f"'loc' and 'target' are the matched registry entry's ({ok_loc}/{n})")
check(ok_pool == n, f"'pool' is the merged pool size at the draw (the rare list's size for a rare row) ({ok_pool}/{n})")
check(any(x["key"] == "rare" for x in r["rows"]) and {"any", "bright", "night"} <= {x["key"] for x in r["rows"]} | {c for x in r["rows"] for c in x["conds"]},
      f"rare rows and the any / bright / night keys all occur ({sorted({x['key'] for x in r['rows']})})")
check(not any(x["phase"] == "night" and x["key"] == "bright" for x in r["rows"]),
      "no night row is keyed 'bright' (the J-1898 gate holds under the ledger's own eyes)")
check(WD.detail("garden", "the spaceship", "day", "clear", "summer") == "" and len(LED.read_rows(path=grid_path)) == n,
      "a target that is not ours returns '' and writes no row")

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
print("\n[3] extra_pool: unchanged; the row comes from the pick, only for an extra that was DRAWN")
ep_path = TMP / "extra.jsonl"
LED._LEDGER = ep_path
n0 = len(LED.read_rows(path=ep_path))
same, total = 0, 0
for key, spec in SPECS:
    for ph, w, se, t, wi in GRID[::7]:
        total += 1
        _sp = WD._match(alias_for(spec))        # the location-less match extra_pool() itself uses (an alias may be shared)
        want = [l for c, lines in _sp["pools"].items() if c in WD._conds(ph, w, se, t, wi) for l in lines] if _sp else []
        random.seed(f"ep|{key}")
        s0 = random.getstate()
        got = WD.extra_pool(alias_for(spec), ph, w, se, t, wi)
        if got == want and random.getstate() == s0:
            same += 1
check(same == total, f"extra_pool() returns the same lines and takes no draw on {total} calls")
check(len(LED.read_rows(path=ep_path)) == n0, "extra_pool() itself writes no row (it only OFFERS lines)")
key0, spec0 = next((k, v) for k, v in SPECS if k.startswith("study:"))
ex = WD.extra_pool(alias_for(spec0), "night", "clear", "summer", "", "calm")
WD.note_extra_pick(alias_for(spec0), "some line of the sensorium's own", ex, "night", "clear", "summer", "", "calm")
check(len(LED.read_rows(path=ep_path)) == n0, "note_extra_pick() with a line that is NOT an extra writes nothing")
WD.note_extra_pick(alias_for(spec0), "", ex, "night", "clear", "summer", "", "calm")
WD.note_extra_pick(alias_for(spec0), ex[0], [], "night", "clear", "summer", "", "calm")
check(len(LED.read_rows(path=ep_path)) == n0, "an empty line or no extras writes nothing")
st_rng = random.getstate()
WD.note_extra_pick(alias_for(spec0), ex[0], ex, "night", "clear", "summer", "", "calm")
rows = LED.read_rows(path=ep_path)
check(random.getstate() == st_rng, "note_extra_pick() takes no random draw")
check(len(rows) == n0 + 1 and rows[-1]["src"] == "extra_pool" and rows[-1]["target"] == key0 and rows[-1]["phase"] == "night"
      and rows[-1]["line_id"] == LED.line_id(ex[0]) and rows[-1]["pool"] == len(ex) and rows[-1]["key"] in rows[-1]["conds"]
      and set(rows[-1]) == FIELDS, f"a drawn extra writes one 'extra_pool' row with the right target / key / pool / id ({rows[-1] if rows else None})")

# the REAL call site: sensorium._living_detail merges extra_pool() into its own pool, draws, and notes the pick
LED.record = _real_record
EXTRA_TARGETS = []
for tgt in ("fire", "room", "study_window", "window", "desk", "lamp", "bed", "sea", "tideline", "sky", "pool", "shelf", "bookshelf"):
    if WD.extra_pool(tgt, "night", "clear", "summer", "", "calm") or WD.extra_pool(tgt, "day", "clear", "summer", "", "calm"):
        EXTRA_TARGETS.append(tgt)
check(len(EXTRA_TARGETS) >= 1, f"_living_detail targets that have extras to merge: {EXTRA_TARGETS}")
cs_path = TMP / "callsite.jsonl"
mism = total = rows_drawn = 0
for tgt in EXTRA_TARGETS:
    for gi, (ph, w, se, t, wi) in enumerate(GRID[::5]):
        for rep in range(4):
            seed = f"cs|{tgt}|{gi}|{rep}"
            LED._LEDGER = TMP / "cs_off.jsonl"
            LED.record = off_record
            random.seed(seed)
            off = S._living_detail(tgt, ph, w, se, t, wi)
            st_off = random.getstate()
            LED.record = _real_record
            LED._LEDGER = cs_path
            before = len(LED.read_rows(path=cs_path))
            random.seed(seed)
            on = S._living_detail(tgt, ph, w, se, t, wi)
            st_on = random.getstate()
            new = LED.read_rows(path=cs_path)[before:]
            total += 1
            if on != off or st_on != st_off:
                mism += 1
            extras = WD.extra_pool(tgt, ph, w, se, t, wi)
            drawn_extra = [l for l in extras if on.startswith(l[:1].upper() + l[1:].rstrip(".")[:30]) or l in on or l[:1].upper() + l[1:] in on]
            if new:
                rows_drawn += len(new)
                if not (len(new) == 1 and new[0]["src"] == "extra_pool" and new[0]["phase"] == ph and new[0]["line"][:20].lower() in on.lower()):
                    mism += 1
            elif drawn_extra and any(l[:1].upper() + l[1:] in on for l in extras):
                mism += 1          # an extra visibly rendered but no row
check(total > 0 and mism == 0, f"{total} real _living_detail() calls: text AND RNG state identical with the ledger on and off, a row exactly "
      f"when a drawn line is an extra (mismatches={mism}, rows={rows_drawn})")
check(rows_drawn > 0, f"...and the call site wrote {rows_drawn} rows in all, so the check is not vacuous")

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
print("\n[4] fail-open: nothing about the ledger can change a draw or raise")
KEY_B, SPEC_B = next((k, v) for k, v in SPECS if k == "garden:birds")


def fail_open_case(label: str, expect_false: bool):
    bad, raised, wrote = 0, 0, 0
    for k in range(80):
        seed = f"fo|{label}|{k}"
        random.seed(seed)
        want = ref_detail("garden", "birds", "night", "clear", "summer", "", "calm")
        st_ref = random.getstate()
        random.seed(seed)
        try:
            got = WD.detail("garden", "birds", "night", "clear", "summer", "", "calm")
        except Exception:
            raised += 1
            continue
        if got != want or random.getstate() != st_ref or not got:
            bad += 1
    if expect_false:
        wrote = int(LED.record("detail", "garden", "garden:birds", "any", "night", ["any"], "x", 1) is True)
    check(raised == 0 and bad == 0 and wrote == 0,
          f"{label}: 80 draws, line and RNG state identical to the reference, none raised, record() False (raised={raised}, bad={bad}, wrote={wrote})")


def _boom(*a, **k):
    raise RuntimeError("record exploded")


try:
    blocker = TMP / "blocker"
    blocker.write_text("a file where the ledger's directory should be", encoding="utf-8")
    LED._LEDGER = blocker / "ledger.jsonl"
    fail_open_case("unwritable path (parent is a file)", True)
    adir = TMP / "adir"
    adir.mkdir()
    LED._LEDGER = adir
    fail_open_case("a directory where the ledger file should be", True)
    LED._LEDGER = TMP / "boom.jsonl"
    LED.record = _boom
    fail_open_case("record() raising", False)
    check(not (TMP / "boom.jsonl").exists(), "record() raising wrote nothing")
    LED.record = _real_record
    LED._LEDGER = _DEFAULT_LEDGER
    check(P.LIVE is False, "this process is NOT live (profile.LIVE is False), as every test and diagnostic is")
    fail_open_case("non-live process on the DEFAULT data/ path (the D-0179 fence refuses)", True)
    check(_LIVE_LEDGER.exists() == _ledgers_existed[0] and _WORKTREE_LEDGER.exists() == _ledgers_existed[1],
          "the default-path attempts created no file, in the worktree or in the live data/")
    # note_extra_pick and _record_look fail-open too
    LED.record = _boom
    WD.note_extra_pick(alias_for(spec0), ex[0], ex, "night", "clear", "summer", "", "calm")
    check(True, "note_extra_pick() with a raising record() returned without raising")
finally:
    LED.record = _real_record
    LED._LEDGER = TMP / "unused_until_redirected.jsonl"

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
print("\n[5] the write fence, on a SIMULATED data/ root (the real one is never written)")
fake = TMP / "fake_root" / "data"
fake.mkdir(parents=True)
_saved = (P._DATA, P._CANONICAL_DATA, P.LIVE, P.ACTIVE_BASE, LED._LEDGER)
try:
    P._DATA = P._CANONICAL_DATA = fake
    P.ACTIVE_BASE = fake
    led = fake / "look_render_ledger.jsonl"
    LED._LEDGER = led
    P.LIVE = False
    args = ("detail", "garden", "garden:birds", "any", "night", ["any", "night"], "x", 3)
    check(LED.record(*args) is False and not led.exists(),
          "a non-live process aimed at data/ is refused: no row, no file, no exception")
    P.LIVE = True
    check(LED.record(*args) is True and len(LED.read_rows(path=led)) == 1, "the live boot (profile.mark_live) writes its row")
    P.LIVE = False
    lab = fake / "_lab" / "20261007_000000" / "look_render_ledger.jsonl"
    LED._LEDGER = lab
    check(LED.record(*args) is True and lab.exists(), "a lab_env.isolate() sandbox, data/_lab/<stamp>/, may write")
    LED._LEDGER = fake / "_lab" / "look_render_ledger.jsonl"
    check(LED.record(*args) is False and not LED._LEDGER.exists(), "data/_lab/<file> with no sandbox directory stays refused")
    P.ACTIVE_BASE = fake / "profiles" / "named"
    LED._LEDGER = led
    (fake / "look_render_ledger.jsonl").unlink()
    check(LED.record(*args) is False and not led.exists(),
          "a NAMED profile (non-live, ACTIVE_BASE under data/profiles/<name>) cannot write the world ledger")
    P.LIVE = False
finally:
    P._DATA, P._CANONICAL_DATA, P.LIVE, P.ACTIVE_BASE, LED._LEDGER = _saved

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
print("\n[6] rotation (the cap) and the night-look count")
_rb = LED.ROTATE_BYTES
rot = TMP / "rot" / "look_render_ledger.jsonl"
try:
    LED.ROTATE_BYTES = 1500
    LED._LEDGER = rot
    written = 0
    for i in range(40):
        written += 1 if LED.record("detail", "garden", "garden:birds", "any", "night" if i % 2 else "day", ["any"], f"line number {i}", 9) else 0
    gen1 = rot.with_name(rot.name + ".1")
    check(written == 40, "40 rows written across rotations, none refused")
    check(gen1.exists() and rot.exists(), "past ROTATE_BYTES the file was renamed over <name>.1 and a fresh file started")
    check(rot.stat().st_size < 1500 + 400 and gen1.stat().st_size >= 1500 - 400, f"live file {rot.stat().st_size} B, rotated {gen1.stat().st_size} B: the disk footprint is bounded")
    allr = LED.read_rows(path=rot)
    ids = [x["line_id"] for x in allr]
    check(len(set(ids)) == len(ids) and ids == sorted(ids, key=lambda i_: [LED.line_id(f'line number {n_}') for n_ in range(40)].index(i_)),
          f"read_rows() spans both generations in order, no duplicates ({len(allr)} of 40 rows retained; the oldest generation is dropped, by design)")
    check(len(allr) < 40, "older rows past the one kept generation are gone (the cap works)")
    nl = LED.night_looks(path=rot)
    check(nl["total"] == nl["garden:birds"] == sum(1 for x in allr if x["phase"] == "night") and nl["shore:birds"] == nl["wood:birds"] == 0 and nl["nights"] >= 1,
          f"night_looks() counts night rows per bird target ({nl})")
finally:
    LED.ROTATE_BYTES = _rb
    LED._LEDGER = TMP / "unused_until_redirected.jsonl"

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
print("\n[7] readers: read_rows() / status() on a hand-made file")
mk = lambda ts, tg, ph: {"ts": ts, "src": "detail", "loc": tg.split(":")[0], "target": tg, "key": "any", "phase": ph, "conds": ["any"],
                         "pool": 4, "line_id": "x", "line": "y"}
good = [mk(100.0, "garden:birds", "night"), mk(200.0, "shore:birds", "day"), mk(300.0, "garden:birds", "night")]
hand = TMP / "handmade.jsonl"
hand.write_text(json.dumps(good[0]) + "\nnot json at all\n" + json.dumps(good[1]) + "\n\n" + json.dumps(good[2]) + "\n"
                + '{"ts": 400.0, "src": "det', encoding="utf-8")
check(LED.read_rows(path=hand) == good, "read_rows() returns the three good rows in order, skipping garbage, blank and torn lines")
check(LED.read_rows(200.0, path=hand) == good[1:], "read_rows(since_ts=200) returns the rows with ts >= 200")
st = LED.status(path=hand)
check(st["ledger_rows"] == 3 and st["first_ts"] == 100.0 and st["last_ts"] == 300.0 and st["by_src"] == {"detail": 3}
      and st["by_target"] == {"garden:birds": 2, "shore:birds": 1}, f"status() counts them ({st['ledger_rows']} rows, by_target {st['by_target']})")
check(LED.night_looks(path=hand)["total"] == 2, "night_looks() on the hand-made file: 2 night bird looks")
none = TMP / "does_not_exist.jsonl"
stn = LED.status(path=none)
check(LED.read_rows(path=none) == [] and stn["ledger_rows"] == 0 and stn["first_ts"] is None and stn["by_target"] == {}
      and LED.night_looks(path=none)["total"] == 0, "a missing ledger reads as [] / zero rows, never an exception")

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
print("\n[8] the live stores are untouched, and no real ledger was created")
for p in _WATCH:
    check(_snap(p) == _before[p], f"{p.name}: unchanged ({'absent' if _before[p] is None else 'size/mtime/hash same'})")
check(not HOOK_EVENTS, f"audit hook: zero write / rename / connect events under the real data/ roots during the whole run ({HOOK_EVENTS[:3]})")
# J-4050: the live ledger legitimately exists once Du has run with it ON (the unchanged-snapshot check above is the real proof
# the live file was not touched); the worktree ledger must still never be created by this run.
check(_snap(_LIVE_LEDGER) == _before[_LIVE_LEDGER] and not _WORKTREE_LEDGER.exists(), "the live ledger is unchanged and no worktree data/look_render_ledger.jsonl was created")

print(f"\n{'ALL OK' if FAILS == 0 else str(FAILS) + ' FAILED'}")
sys.exit(0 if FAILS == 0 else 1)
