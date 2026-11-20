"""
Regression: the shore's ambient oystercatcher-nest line states the nest's OWN egg count (J-1750 / F-2382's side finding).

The bug (verified, F-2382): core/shore_life.py's tick draws the nest as {'ts': now, 'eggs': random.randint(2, 3)}, but
wildlife_line() -- the ambient line sensorium._shore_event() hands Du while he stands on the shore -- always said
'... a scrape among the stones with two eggs in it, blotched like the stones'. The live nest held eggs=3 (data/shore_life.json
oyc_nest, since 2026-10-01 06:01) while data/wandering_log.jsonl kept saying 'with two eggs in' (5 rows 10-01 06:21 to 06:50; 624
rows overall) and Du's own thoughts quote 'two eggs'. A number that contradicts the state it describes breaks the World-truth gate
(a line may only name what the engine says is there).

The fix (ONE pool entry, core/shore_life.py wildlife_line): the count is read from d['oyc_nest']['eggs'] and said in words ('one egg',
'two eggs', 'three eggs', 'four eggs'); a count that is missing, not an int (a bool included), or outside 1-4 says no number at all
('... with eggs in it ...') -- never a wrong one. Every other word of the sentence and every other pool line is unchanged.

  [0] module resolution + isolation set-up (the code under test is THIS root's; shore_life's state file points into a temp dir)
  [1] BASE differential: the pre-change shore_life.py (git show BASE_REV) and the new one, same state / same stubs / same RNG, over three
      seasonal scenarios that between them surface all nine distinct pool lines, for no nest, every count 1-4 and 15 bad counts:
      every non-nest line byte-identical and in the same place; the nest line equals the base line with ONLY 'two eggs' replaced by the
      count's words; and the base itself says 'two eggs' for a 3-egg nest (the defect, so a test of the new words fails on the old code)
  [2] literal pins: eggs=2 is the old sentence to the byte; 'three eggs' for 3; singular 'one egg'; every bad count names no number
  [3] the real RNG, nothing patched but the season: every nest line that comes out names the nest's count, none the wrong one
  [4] isolation: audit hook (no write attempt under any data/), live-file hashes, py_compile

ISOLATION. Nothing here writes: wildlife_line() only READS shore_life's state file, which is redirected into a temp dir (the S-0016 /
test-isolation rule); the season comes from stubbed _weather/_month, so core.sensorium is never imported. A Python audit hook records any
attempt by THIS process to open-for-write / rename / remove under C:\\Nascence\\data or <root>\\data (same convention as
scripts/_test_j1165_trace_object_look.py), and the live files are md5-hashed before and after. Run it FROM the checkout it tests (core/
satisfaction.py writes the real data/ from any process -- F-2406 -- and this script does not touch it, but the habit is the rule).

  python scripts/_test_j1750_shore_nest_ambient_egg_count.py                    # exit 0 = ALL OK
  python scripts/_test_j1750_shore_nest_ambient_egg_count.py --against REV      # the same checks against shore_life.py as of git REV
                                                                                # (e.g. BASE_REV: must FAIL there -- the test has teeth)
"""
from __future__ import annotations

import hashlib
import json
import os
import py_compile
import random
import re
import subprocess
import sys
import tempfile
import time
import types
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TMP = Path(tempfile.mkdtemp(prefix="j1750_shore_nest_ambient_egg_count_"))
print("isolated store dir:", TMP)
# The checkout this change was built on (the parent of the J-1750 commit): the "before" that [1] compares the new code against.
BASE_REV = "24d0a73a411e1c02a519ba1c7706d247affa1850"
# data/ is gitignored and never checked out into a job-run worktree, so "live" is the one real repo, never ROOT-relative.
_LIVE_DATA = Path(r"C:\Nascence") / "data"
_LIVE_FILES = [_LIVE_DATA / f for f in ("shore_life.json", "wandering_log.jsonl", "satisfaction_log.jsonl", "satisfaction_state.json")]


def _md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest() if p.exists() else ""


_before = {p: _md5(p) for p in _LIVE_FILES}

# -- write audit: this process must never attempt a write under a live data dir ------------------------------------
_WATCH = [str(_LIVE_DATA).lower(), str(ROOT / "data").lower()]
_WRITE_EVENTS = {"os.rename", "os.remove", "os.rmdir", "os.mkdir", "os.truncate", "os.utime", "os.chmod",
                 "shutil.copyfile", "shutil.copymode", "shutil.copystat", "shutil.copytree", "shutil.move",
                 "shutil.rmtree"}
LIVE_WRITE_ATTEMPTS: list = []


def _under_watch(p) -> bool:
    try:
        if isinstance(p, int):
            return False
        s = os.path.abspath(os.fsdecode(os.fspath(p))).lower()
    except Exception:
        return False
    return any(s == r or s.startswith(r + os.sep) for r in _WATCH)


def _audit(event, args):
    try:
        if event == "open":
            path, mode, flags = args[0], args[1], args[2]
            writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
                isinstance(flags, int) and bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC)))
            if writing and _under_watch(path):
                LIVE_WRITE_ATTEMPTS.append(("open", str(path), mode))
        elif event in _WRITE_EVENTS:
            for a in args:
                if isinstance(a, (str, bytes, os.PathLike)) and _under_watch(a):
                    LIVE_WRITE_ATTEMPTS.append((event, str(a), None))
                    break
    except Exception:
        pass


sys.addaudithook(_audit)

FAILS = 0
CHECKS = 0


def check(cond: bool, label: str) -> None:
    global FAILS, CHECKS
    CHECKS += 1
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS += 1


def quiet(cond: bool, label: str, sink: list) -> None:
    """A bulk check: count it, collect only failures (the tables below run hundreds)."""
    global FAILS, CHECKS
    CHECKS += 1
    if not cond:
        FAILS += 1
        sink.append(label)


def load_rev(rev: str, name: str):
    """core/shore_life.py as it was at git `rev`, exec'd under a throwaway module name (git show: read-only). (module, '') or (None, why)."""
    try:
        src = subprocess.run(["git", "-C", str(ROOT), "show", f"{rev}:core/shore_life.py"], capture_output=True, check=True, timeout=60).stdout
        mod = types.ModuleType(name)
        mod.__file__ = str(ROOT / "core" / "shore_life.py")
        exec(compile(src.decode("utf-8"), f"core/shore_life.py@{rev[:7]}", "exec"), mod.__dict__)
        return mod, ""
    except Exception as exc:
        return None, repr(exc)[:200]


# -- the module under test -----------------------------------------------------------------------------------------
AGAINST = sys.argv[sys.argv.index("--against") + 1] if "--against" in sys.argv else ""
if AGAINST:
    SH, _why = load_rev(AGAINST, "shore_life_under_test")
    if SH is None:
        print(f"cannot load core/shore_life.py at {AGAINST}: {_why}")
        sys.exit(2)
    print(f"MODULE UNDER TEST: core/shore_life.py as of git {AGAINST[:12]} (--against), NOT the working copy")
else:
    from core import shore_life as SH                          # noqa: E402


class _Rnd:
    """Stands in for the random module inside shore_life: random() is fixed at 0.0 (every seasonal gate and the 0.5 fire gate open);
    choice(pool) records the WHOLE pool the function built and returns the oystercatcher line (else the first)."""

    def __init__(self, want_nest: bool = True):
        self.pools: list[list[str]] = []
        self.want_nest = want_nest

    def random(self) -> float:
        return 0.0

    def choice(self, pool):
        self.pools.append(list(pool))
        if self.want_nest:
            for line in pool:
                if "oystercatcher" in line:
                    return line
        return pool[0]

    def randint(self, a, b):   # _load()'s fallback state only -- the state file always exists here
        return a


# month, phase, weather, wind. Between them these three surface every distinct pool line wildlife_line can build: seal, penguin, its
# prints, nest, sparkle, fog, swell (October night), dolphins (January day), a whale (June day) -- asserted in [1].
SCENARIOS = {"oct night": (10, "night", "clear", "calm"), "jan day": (1, "day", "clear", "calm"), "jun day": (6, "day", "clear", "calm")}
NOW = time.mktime((2026, 10, 15, 22, 0, 0, 0, 0, -1))


def write_state(nest) -> Path:
    st = {"cairn": 0, "sand_writing": None, "fire": {"state": "out", "fuel": 0.0, "ts": 0.0}, "cave_finds": [], "wet_feet": 0.0,
          "in_cave": False, "seal": {"ts": 1.0}, "penguins": {"burrows": 4, "seen": 0}, "oyc_nest": nest, "fog": True,
          "swell": 0.9, "sparkle": True, "whale_seen": 0, "dolphins_seen": 0, "announced": [], "skips_best": 0, "_last": 0.0,
          "latent_objects": [], "_storm_active": False}
    p = TMP / "shore_life.json"
    p.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
    return p


def season(mod, scenario: str) -> None:
    month, phase, weather, wind = SCENARIOS[scenario]
    mod._weather = lambda: (weather, wind, phase)
    mod._month = lambda t=None: month


def run(mod, scenario: str, nest):
    """(the pool the module built, the line it returned) for one state under the stubbed season and RNG."""
    mod._F = write_state(nest)
    season(mod, scenario)
    rnd = _Rnd()
    mod.random = rnd
    line = mod.wildlife_line(NOW)
    return (rnd.pools[-1] if rnd.pools else None), line


# the spec, typed in (independent of the code under test)
GOOD = {1: "one egg", 2: "two eggs", 3: "three eggs", 4: "four eggs"}
NO_NUMBER = [("eggs key missing", {"ts": 1.0}), ("eggs None", {"ts": 1.0, "eggs": None}), ("eggs 0", {"ts": 1.0, "eggs": 0}),
             ("eggs 5", {"ts": 1.0, "eggs": 5}), ("eggs 9", {"ts": 1.0, "eggs": 9}), ("eggs -2", {"ts": 1.0, "eggs": -2}),
             ("eggs 'x'", {"ts": 1.0, "eggs": "x"}), ("eggs '3' (a string)", {"ts": 1.0, "eggs": "3"}),
             ("eggs 3.0 (a float)", {"ts": 1.0, "eggs": 3.0}), ("eggs True (a bool, == 1)", {"ts": 1.0, "eggs": True}),
             ("eggs [3] (a list)", {"ts": 1.0, "eggs": [3]}), ("eggs {'n': 3} (a dict)", {"ts": 1.0, "eggs": {"n": 3}}),
             ("nest is True (not a dict)", True), ("nest is 'x' (not a dict)", "x"), ("nest is [2] (not a dict)", [2])]
OLD_LINE = ("on the high shingle an oystercatcher screams and runs at you, wings out \u2014 you are near something; "
            "a scrape among the stones with two eggs in it, blotched like the stones")
NUM_EGG = re.compile(r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+eggs?\b")


def expected(nest) -> str:
    n = nest.get("eggs") if isinstance(nest, dict) else None
    return GOOD[n] if type(n) is int and n in GOOD else "eggs"


STATES = [("no nest", None)] + [(f"eggs {n}", {"ts": 1.0, "eggs": n}) for n in GOOD] + NO_NUMBER

# -- [0] --------------------------------------------------------------------------------------------------------------
print("\n[0] module resolution")
if not AGAINST:
    print("    shore_life ->", SH.__file__)
    check(Path(SH.__file__).resolve().is_relative_to(ROOT), f"core.shore_life was loaded from inside {ROOT}")
BASE, _why = load_rev(BASE_REV, "shore_life_base_j1750")
if BASE is None:
    print(f"    SKIP  base revision {BASE_REV[:12]} is not readable here ({_why}); [1] is skipped, [2] and [3] still pin the behaviour")
else:
    check(True, f"base shore_life.py read from git {BASE_REV[:12]}")

# -- [1] --------------------------------------------------------------------------------------------------------------
print("\n[1] BASE differential: same state, same stubs, same RNG -- only the egg phrase may differ")
if BASE is not None:
    bad: list[str] = []
    union: set[str] = set()
    combos = 0
    for scen in SCENARIOS:
        for label, nest in STATES:
            bp, bl = run(BASE, scen, nest)
            np_, nl = run(SH, scen, nest)
            tag = f"[{scen} / {label}]"
            quiet(bp is not None and np_ is not None, f"{tag} both modules built a pool (an exception inside wildlife_line is swallowed to None)", bad)
            if bp is None or np_ is None:
                continue
            combos += 1
            union.update(bp)
            quiet(len(np_) == len(bp), f"{tag} pool length {len(np_)} vs base {len(bp)}", bad)
            nest_idx = [i for i, b in enumerate(bp) if "oystercatcher" in b]
            quiet(nest_idx == [i for i, n in enumerate(np_) if "oystercatcher" in n], f"{tag} the nest line sits in the same place", bad)
            for i, b in enumerate(bp):
                if i not in nest_idx:
                    quiet(i < len(np_) and np_[i] == b, f"{tag} pool[{i}] byte-identical to base ({b[:44]!r})", bad)
            if nest:
                quiet(len(nest_idx) == 1, f"{tag} exactly one nest line when a nest exists", bad)
                if len(nest_idx) == 1 and len(np_) == len(bp):
                    i = nest_idx[0]
                    quiet(bp[i].count("two eggs") == 1, f"{tag} the base nest line carries one 'two eggs'", bad)
                    quiet(np_[i] == bp[i].replace("two eggs", expected(nest)), f"{tag} nest line == base with ONLY 'two eggs' -> {expected(nest)!r}", bad)
                    quiet(nl == np_[i] and bl == bp[i], f"{tag} the returned line is the nest line in both", bad)
            else:
                quiet(not nest_idx, f"{tag} no nest -> no nest line", bad)
                quiet(nl == np_[0] and bl == bp[0], f"{tag} no nest -> the same first line returned", bad)
    for b in bad[:12]:
        print("  FAIL", b)
    check(not bad, f"{combos} scenario x state combinations ({len(STATES)} states x {len(SCENARIOS)} seasons): {len(bad)} deviations from base")
    check(len(union) == 9 and sum("oystercatcher" in u for u in union) == 1,
          f"the three seasons surface all {len(union)} distinct pool lines (8 non-nest + the nest line), so 'every other line identical' covers them all")
    _bp, _bl = run(BASE, "oct night", {"ts": 1.0, "eggs": 3})
    check("two eggs" in _bl and "three eggs" not in _bl, "the BASE says 'two eggs' for a nest holding 3 -- the defect (a test of the new words fails on the old code)")

# -- [2] --------------------------------------------------------------------------------------------------------------
print("\n[2] literal pins (through the real wildlife_line, nest line picked)")
LINES: dict[str, str | None] = {}
for label, nest in STATES[1:]:
    _p, LINES[label] = run(SH, "oct night", nest)
check(LINES["eggs 2"] == OLD_LINE, "eggs=2 is the OLD sentence, to the byte (what Du has been given 624+ times is unchanged when the nest holds two)")
check(LINES["eggs 3"] == OLD_LINE.replace("two eggs", "three eggs"), "eggs=3 -> '...a scrape among the stones with three eggs in it, blotched like the stones'")
check(LINES["eggs 1"] == OLD_LINE.replace("two eggs", "one egg"), "eggs=1 -> singular: 'with one egg in it' (never 'one eggs')")
check(LINES["eggs 4"] == OLD_LINE.replace("two eggs", "four eggs"), "eggs=4 -> 'with four eggs in it'")
print("    eggs 3  :", LINES["eggs 3"])
print("    no count:", LINES["eggs key missing"])
no_number_bad = []
for label, nest in NO_NUMBER:
    line = LINES[label]
    quiet(line == OLD_LINE.replace("two eggs", "eggs"), f"{label}: names no number -> {line!r}", no_number_bad)
    quiet(line is not None and NUM_EGG.search(line) is None, f"{label}: no number word before 'egg(s)'", no_number_bad)
for b in no_number_bad[:8]:
    print("  FAIL", b)
check(not no_number_bad, f"{len(NO_NUMBER)} bad counts (missing / None / 0 / 5 / 9 / -2 / 'x' / '3' / 3.0 / True / list / dict / non-dict nest): "
                         f"each says '...with eggs in it...', no number, no exception")
good_bad = []
for n, words in GOOD.items():
    found = NUM_EGG.findall(LINES[f"eggs {n}"] or "")
    quiet(found == [words.split()[0]], f"eggs {n}: exactly one count named, {words!r} (found {found})", good_bad)
check(not good_bad, "every count 1-4 is named exactly once, in words, and is the nest's own")

# -- [3] --------------------------------------------------------------------------------------------------------------
print("\n[3] the real RNG: nothing patched but the season")
SH.random = random
random.seed(1750)
for label, nest, want, never in (("eggs 3", {"ts": 1.0, "eggs": 3}, "with three eggs in it", "two eggs"),
                                 ("eggs 2", {"ts": 1.0, "eggs": 2}, "with two eggs in it", "three eggs"),
                                 ("no count", {"ts": 1.0}, "with eggs in it", "two eggs")):
    SH._F = write_state(nest)
    season(SH, "oct night")
    out = [SH.wildlife_line(NOW) for _ in range(3000)]
    nest_lines = [x for x in out if x and "scrape among the stones" in x]
    check(len(nest_lines) > 100 and any(x is None for x in out), f"{label}: {len(nest_lines)} nest lines in 3000 real draws ({sum(x is None for x in out)} quiet ones)")
    check(all(want in x for x in nest_lines) and not any(never in x for x in nest_lines), f"{label}: every nest line says {want!r}, none says {never!r}")

# -- [4] --------------------------------------------------------------------------------------------------------------
print("\n[4] isolation")
check(TMP in Path(str(SH._F)).parents and (BASE is None or TMP in Path(str(BASE._F)).parents), "shore_life's state file stayed inside the temp dir")
check(not LIVE_WRITE_ATTEMPTS, f"the audit hook saw NO write attempt under any data/ ({len(LIVE_WRITE_ATTEMPTS)} attempts)"
                               f"{' -> ' + str(LIVE_WRITE_ATTEMPTS[:3]) if LIVE_WRITE_ATTEMPTS else ''}")
_after = {p: _md5(p) for p in _LIVE_FILES}
for p in _LIVE_FILES:
    print(f"    md5 {p.name:24s} before {_before[p][:12] or '(absent)':12s} after {_after[p][:12] or '(absent)':12s}"
          + ("" if _before[p] == _after[p] else "   <- changed while this ran (Du online?); the audit hook above is the real proof"))
for _p in (ROOT / "core" / "shore_life.py", Path(__file__)):
    try:
        py_compile.compile(str(_p), cfile=str(TMP / (_p.name + "c")), doraise=True)
        check(True, f"py_compile {_p.name}")
    except py_compile.PyCompileError as exc:
        check(False, f"py_compile {_p.name}: {exc}")

print(f"\n{'ALL OK' if not FAILS else f'{FAILS} FAILURE(S)'} \u2014 {CHECKS} checks \u2014 isolated store in {TMP}")
sys.exit(1 if FAILS else 0)
