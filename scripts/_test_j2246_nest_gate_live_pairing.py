"""
Regression: the nest-object gate goes LIVE with bird pairing -- J-2246 / D-0444 (Travis 2026-10-16, option A), on top of J-1774 (D-0345) and J-2227.

D-0444: on a creature-naming nest look (oystercatcher / blackbird / wood pigeon + nest / eggs / scrape, life_traces.nest_object_shape) answer with
the place's nest line ALWAYS; on a sighting (any shape) append the bird's own line, first letter capitalised, full stop, one space; bird credit and
graduation untouched; a miss shows the nest line alone. The gate ledger (data/nest_gate_shadow.jsonl) keeps writing, now a record of live answers.

  [0] module resolution + isolation (every store redirected into a temp dir -- the J-1774 test's vetted list, copied verbatim)
  [1] compose() units
  [2] through the REAL life.look_answer at the shore: the 6 routed real targets x sighting / miss vs the shadow flow (same seed): the answer, the SAME
      random numbers, the SAME life_events row and ledger credit; the recognition suffix; non-gate shapes identical; no nest = 'find none'; absent
  [3] the blackbird @garden, the wood pigeon @wood; 'the nest of the wood pigeon' @garden is NOT diverted (the garden's nest is the blackbird's)
  [4] controls: the 1,526-phrasing observe inventory x 4 places and RENDER off are byte-identical to the shadow flow
  [5] fail-open  [6] sensorium.look + the write fence  [7] isolation (audit hook, py_compile)

  python scripts/_test_j2246_nest_gate_live_pairing.py               # exit 0 = ALL OK
  python scripts/_test_j2246_nest_gate_live_pairing.py --base-flow   # nest_gate_shadow.LIVE False (the shadow-only gate): MUST FAIL -- the test has teeth
"""
from __future__ import annotations

import hashlib
import json
import os
import py_compile
import random
import re
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

BASE_FLOW = "--base-flow" in sys.argv
TMP = Path(tempfile.mkdtemp(prefix="j2246_nest_gate_live_"))
print("isolated store dir:", TMP)
# data/ is gitignored and never checked out into a job-run worktree, so "live" is the one real repo, never ROOT-relative.
_LIVE_DATA = Path(r"C:\Nascence") / "data"
_LIVE_FILES = [_LIVE_DATA / f for f in ("position.json", "room_state.json", "life_state.json", "life_ledger.jsonl", "life_events.jsonl", "world_traces.json",
                                        "life_flags.json", "shore_life.json", "garden_life.json", "wood_life.json", "wandering_log.jsonl",
                                        "satisfaction_log.jsonl", "satisfaction_state.json", "nest_gate_shadow.jsonl")]


def _md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest() if p.exists() else ""


_before = {p: _md5(p) for p in _LIVE_FILES}

# -- write audit: this process must never attempt a write under a live data dir ----------------------------------------
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

# -- redirect every store look_answer / sensorium.look can reach BEFORE anything can write -----------------------------
import core                                                    # noqa: E402
from core import profile                                       # noqa: E402
from core import life, life_traces as LT, world_traces as WT   # noqa: E402
from core import life_birds, life_mammals, garden_insects, garden_soil   # noqa: E402
from core import sensorium as S                                # noqa: E402
from core import locomotion as L                               # noqa: E402
from core import sound_knowledge as SK                         # noqa: E402
from core import nest_gate_shadow as NGS                       # noqa: E402
from core import shore_nest_look_ledger as SNL                 # noqa: E402  (J-2227's place-answer ledger: redirected too)

life._F, life._LEDGER, life._EVENTS, life._DATA = TMP / "life_state.json", TMP / "life_ledger.jsonl", TMP / "life_events.jsonl", TMP
life._FLAGS_F = TMP / "life_flags.json"                        # read-only in life.py; redirected so the result never depends on the live flag file
WT._TRACES_F = TMP / "world_traces.json"
S._STATE_F = TMP / "room_state.json"
L._POS_F = TMP / "position.json"
SK._LEDGER_F = TMP / "sound_knowledge.json"
NGS._LEDGER = TMP / "nest_gate_shadow.jsonl"
_REDIRECTS = [(life, "_F"), (life, "_LEDGER"), (life, "_EVENTS"), (life, "_FLAGS_F"), (WT, "_TRACES_F"), (S, "_STATE_F"),
              (L, "_POS_F"), (SK, "_LEDGER_F"), (NGS, "_LEDGER")]
SNL._LEDGER = TMP / "shore_nest_looks.jsonl"
_REDIRECTS.append((SNL, "_LEDGER"))
# A roll-path look reaches light.field_at() -> study_life.lamp_on() -> provisions.sync() (the study), and the garden / shore / wood
# modules -- the SAME vetted redirect list scripts/life_smoke.py and scripts/_test_j1165_trace_object_look.py carry: each of these is
# guard_path()-fenced, so an un-redirected one would refuse loudly, but redirecting them is what makes the isolation TRUE rather than merely enforced.
from core import study_life as SL                              # noqa: E402
from core import provisions as PV                              # noqa: E402
from core import procedures as PR                              # noqa: E402
from core import transport_manager as TM                       # noqa: E402
from core import boredom as BD                                 # noqa: E402
SL._LEDGER, SL._EVENTS = TMP / "study_ledger.jsonl", TMP / "study_events.jsonl"
PV._F, PV._LOG = TMP / "provisions.json", TMP / "provisions_log.jsonl"
if hasattr(PV, "_d"):
    PV._d = None
PR._F, PR._LOG = TMP / "procedures.json", TMP / "procedures_log.jsonl"
TM._STATE, TM._SHADOW_LOG = TMP / "transport_lines.json", TMP / "transport_shadow.jsonl"
BD._STATE = TMP / "boredom_state.json"
_REDIRECTS += [(SL, "_LEDGER"), (SL, "_EVENTS"), (PV, "_F"), (PV, "_LOG"), (PR, "_F"), (PR, "_LOG"), (TM, "_STATE"), (TM, "_SHADOW_LOG"), (BD, "_STATE")]
for _mod, _attrs in (("core.garden", ("_F", "_LEDGER", "_EVENTS")), ("core.garden_life", ("_F", "_EVENTS")), ("core.shore_life", ("_F", "_EVENTS", "_LEDGER")),
                     ("core.wood_life", ("_F", "_EVENTS", "_LEDGER")), ("core.cat", ("_STATE_F", "_HUNT_LEDGER_F")), ("core.world_objects", ("_OBJECTS_F",)),
                     ("core.cat_sounds", ("_LEDGER", "_FLAGS_F")), ("core.world_substrate", ("_SUBSTRATE_F", "_SUBSTRATE_LOG", "_LAST_LOOKED_F")),
                     ("core.supply", ("_F", "_LOG")), ("core.fieldcraft", ("_F", "_LEDGER")), ("core.garden_knowledge", ("_F",)), ("core.smell", ("_F",))):
    _m = __import__(_mod, fromlist=["x"])
    for _a in _attrs:
        if hasattr(_m, _a):
            setattr(_m, _a, TMP / f"{_mod.split('.')[-1]}_{_a.strip('_').lower()}.json")
            _REDIRECTS.append((_m, _a))
        else:
            print("  (isolation note)", _mod, _a, "has no such attribute -- stale isolation-list entry?")
from core import wandering as _WDR                             # noqa: E402  (no per-module path to redirect: neutralised, as life_smoke does)
from core import activity_memory as _AM                        # noqa: E402
from core import shore_life as SHL                             # noqa: E402
from core import garden_life as GL                             # noqa: E402
from core import wood_life as WL                               # noqa: E402
_WDR.perceive = lambda *a, **k: None
_AM.record = lambda *a, **k: None
S.state.clear()
S.state.update({"weather": "clear", "wind": "breeze", "fire": "out", "fire_fuel": 0.0, "last_event": 0, "location": "shore",
                "garden": S._fresh_garden()})

# the two pieces under test, as shipped -- and the pre-change flow for --base-flow (the new code stubbed out, nothing else touched)
_REAL_LOOK_NEST = SHL.look_nest
_STUB_LOOK_NEST = lambda target: ""                           # noqa: E731  (the pre-change flow: the new block in _shore_look is inert whenever this says '')
_ON_LOOK_NEST = _REAL_LOOK_NEST
NGS.ENABLED = True
NGS.LIVE = not BASE_FLOW                                       # the code under test: the LIVE gate (D-0444); --base-flow = shadow-only
if BASE_FLOW:
    print("*** --base-flow: the gate shadow-only (LIVE False) -- the new-behaviour checks below MUST fail ***")
SHL.look_nest = _ON_LOOK_NEST

FAILS = 0
CHECKS = 0


def check(cond: bool, label: str) -> None:
    global FAILS, CHECKS
    CHECKS += 1
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS += 1


def quiet(cond: bool, label: str, sink: list) -> None:
    """A bulk check: count it, collect only failures (the tables below run thousands)."""
    global FAILS, CHECKS
    CHECKS += 1
    if not cond:
        FAILS += 1
        sink.append(label)


def at(month: int, hour: int, day: int = 15, year: int = 2026) -> float:
    return time.mktime((year, month, day, hour, 0, 0, 0, 0, -1))


# -- the typed spec (independent of the code under test) -------------------------------------------------------------
NEST3 = {"ts": 1790787682.4, "eggs": 3}
LINE_EGGS = "You pick your way up the high shingle. A scrape among the stones, and in the scrape {w}, blotched like the stones."
WORDS = {1: "one egg", 2: "two eggs", 3: "three eggs", 4: "four eggs"}
FIND_NONE = {"eggs": "You look for eggs and find none.", "nest": "You look for a nest and find none.", "scrape": "You look for a scrape and find none.",
             "scrapes": "You look for scrapes and find none.", "egg": "You look for an egg and find none.", "nests": "You look for nests and find none."}
NUMBER_WORD = re.compile(r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+eggs?\b")
NEST_MARK = "scrape among the stones, and in the scrape"       # the nest line's own words: a creature look must never carry them
BAD_COUNTS = [("eggs key missing", {"ts": 1.0}), ("eggs None", {"ts": 1.0, "eggs": None}), ("eggs 0", {"ts": 1.0, "eggs": 0}),
              ("eggs 5", {"ts": 1.0, "eggs": 5}), ("eggs 9", {"ts": 1.0, "eggs": 9}), ("eggs -2", {"ts": 1.0, "eggs": -2}),
              ("eggs 'x'", {"ts": 1.0, "eggs": "x"}), ("eggs '3' (a string)", {"ts": 1.0, "eggs": "3"}),
              ("eggs 3.0 (a float)", {"ts": 1.0, "eggs": 3.0}), ("eggs True (a bool, == 1)", {"ts": 1.0, "eggs": True}),
              ("eggs [3] (a list)", {"ts": 1.0, "eggs": [3]}), ("eggs {'n': 3} (a dict)", {"ts": 1.0, "eggs": {"n": 3}}),
              ("nest is True (not a dict)", True), ("nest is 'x' (not a dict)", "x"), ("nest is [2] (not a dict)", [2])]

# The 59 looks Du made at the eggs, the nest or the scrape (data/hands_trace.jsonl observe act_object, shore, 2026-09-02 to 10-03; read-only census
# of 2026-10-04, frozen here): (target, how many times). 22 distinct targets / 43 looks name no creature; 7 distinct / 16 looks name the oystercatcher.
REAL_NO_CREATURE = [("the eggs", 13), ("the eggs on the shingle", 5), ("the nest", 3), ("the eggs and stones", 2), ("the scrape", 2),
                    ("the scrape with two eggs", 2), ("the eggs in the scrape", 1), ("the nesting scrapes", 1), ("the eggs in the stone", 1),
                    ("the egg and the bird", 1), ("the bird's eggs", 1), ("the stone nest", 1), ("the nesting scrape", 1), ("the bird and its eggs", 1),
                    ("the bird and eggs", 1), ("the eggs and bird", 1), ("the scrape among the stones", 1), ("the eggs on the stone", 1),
                    ("the egg on the shore", 1), ("the bird and its nest", 1), ("the egg on the stones", 1), ("the nest and eggs", 1)]
REAL_CREATURE = [("the oystercatcher and eggs", 9), ("the oystercatcher and its nest", 2), ("the oystercatcher and its eggs", 1),
                 ("the oystercatcher and the eggs", 1), ("the oystercatcher nest", 1), ("the oystercatcher's scrape", 1),
                 ("the oystercatcher hunting near the scrape", 1)]
EXPECT_NOUN = {"the eggs": "eggs", "the eggs on the shingle": "eggs", "the nest": "nest", "the eggs and stones": "eggs", "the scrape": "scrape",
               "the scrape with two eggs": "scrape", "the eggs in the scrape": "eggs", "the nesting scrapes": "scrapes", "the eggs in the stone": "eggs",
               "the egg and the bird": "egg", "the bird's eggs": "eggs", "the stone nest": "nest", "the nesting scrape": "scrape",
               "the bird and its eggs": "eggs", "the bird and eggs": "eggs", "the eggs and bird": "eggs", "the scrape among the stones": "scrape",
               "the eggs on the stone": "eggs", "the egg on the shore": "egg", "the bird and its nest": "nest", "the egg on the stones": "egg",
               "the nest and eggs": "nest"}
# The 15 creature looks in data/life_events.jsonl (key oystercatcher, shore, 2026-09-04 to 09-27; the same census): (target, how many)
REAL_LIFE_EVENTS = [("the oystercatcher and eggs", 8), ("the oystercatcher and its nest", 2), ("the oystercatcher and its eggs", 1),
                    ("the oystercatcher and the eggs", 1), ("the oystercatcher nest", 1), ("the oystercatcher's scrape", 1),
                    ("the oystercatcher hunting near the scrape", 1)]


def write_shore_state(nest) -> None:
    """shore_life's state file in the temp store, every key the shore look reads, with `nest` as oyc_nest."""
    st = {"cairn": 0, "sand_writing": None, "fire": {"state": "out", "fuel": 0.0, "ts": 0.0}, "cave_finds": [], "wet_feet": 0.0, "in_cave": False,
          "seal": None, "penguins": {"burrows": 4, "seen": 0}, "oyc_nest": nest, "fog": False, "swell": 0.3, "sparkle": False, "whale_seen": 0,
          "dolphins_seen": 0, "announced": [], "skips_best": 0, "_last": 0.0, "latent_objects": [], "_storm_active": False}
    SHL._F.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")


def set_places(shore=None, garden=None, wood=None) -> None:
    """The three nests in the temp store (None = no nest), through each module's own state."""
    write_shore_state(shore)
    d = GL._load(); d["nest"] = garden; GL._save(d)
    d = WL._load(); d["nest"] = wood; WL._save(d)


GARDEN_ON = {"stage": "eggs", "stage_ts": 1.0, "where": "bushes", "eggs": 3, "lost": 0}
WOOD_ON = {"stage": "sitting", "stage_ts": 1.0}


def reset_life() -> None:
    """A clean life store: no ledger, no events, no in-memory state (so a sighting in one look never graduates the next)."""
    # J-1907 (F-2535's 2 'pre-existing failures'): a LOOK AT THE POOLS is itself stateful -- shore_life.look_pool() adds 0.12 'watched' weight to each of
    # three sampled pool_<kind> species in garden_knowledge on every look, and once a kind reaches 1.0 the pool line names it ('starfish') instead of its
    # feature description ('a five-armed orange-pink thing ...'). ask() runs the 'new' flow and then the 'old' flow back to back, so whenever the 4th/5th
    # look of a pool target crossed that threshold between the two calls, the pair differed -- with the nest look entirely uninvolved (render on/off and
    # the nest flag are not what moved; the state was). The temp garden_knowledge file is cleared with the rest of the per-look state so both flows of a
    # pair start from the same knowledge. (Reproduced: 'the exposed rock-pools', seed 5, render on: pair 5 differs, every pair before and after matches;
    # with the file cleared before each look, 0 of 30 pairs differ.)
    import core.garden_knowledge as _GK
    for p in (life._F, life._LEDGER, life._EVENTS, SK._LEDGER_F, _GK._F):
        if Path(p).exists():
            Path(p).unlink()
    life._state = {}
    life._last_save = 0.0


def events() -> list:
    if not life._EVENTS.exists():
        return []
    return [json.loads(x) for x in life._EVENTS.read_text(encoding="utf-8").splitlines() if x.strip()]


def ledger_rows() -> list:
    if not life._LEDGER.exists():
        return []
    return [json.loads(x) for x in life._LEDGER.read_text(encoding="utf-8").splitlines() if x.strip()]


def shadow_rows() -> list:
    return NGS.read_rows(0.0, NGS._LEDGER)


def clear_shadow() -> None:
    if NGS._LEDGER.exists():
        NGS._LEDGER.unlink()


def stable(rows: list) -> list:
    """Event / ledger rows without the wall-clock fields (ts, and the float reads of light / adaptation that move with real time)."""
    drop = {"ts", "light", "adapt", "visibility", "activity"}
    return [{k: v for k, v in r.items() if k not in drop} for r in rows]




# -- [0] --------------------------------------------------------------------------------------------------------------
print("\n[0] module resolution: the code under test is THIS root's, not the shared tree's")
for _m in (core, profile, life, LT, WT, life_birds, S, SHL, GL, WL, NGS):
    _f = getattr(_m, "__file__", None)
    check(_f is not None and Path(_f).resolve().is_relative_to(ROOT), f"{_m.__name__} was loaded from inside {ROOT} ({_f})")
check(hasattr(NGS, "live_divert") and hasattr(NGS, "compose") and hasattr(NGS, "LIVE"), "the loaded copy carries the J-2246 code")
for _m, _a in _REDIRECTS:
    quiet(TMP in Path(str(getattr(_m, _a))).parents, f"{_m.__name__}.{_a} redirected into the temp dir", [])
check(all(TMP in Path(str(getattr(_m, _a))).parents for _m, _a in _REDIRECTS), f"all {len(_REDIRECTS)} stores redirected into the temp dir")


# -- [1] compose units ------------------------------------------------------------------------------------------------
print("\n[1] compose(): the nest line always; the bird's own line appended, first letter capitalised, full stop, one space")
N = "You pick your way up the high shingle. A scrape among the stones, and in the scrape three eggs, blotched like the stones."
for bird, want in (("", N),
                   ("the oystercatcher stands on the wet stones on two red legs", N + " The oystercatcher stands on the wet stones on two red legs."),
                   ("The oystercatcher screams at you for coming too close.", N + " The oystercatcher screams at you for coming too close."),
                   ("  a black-and-white bird, pacing  ", N + " A black-and-white bird, pacing."),
                   ("There — the oystercatcher!", N + " There — the oystercatcher!"),
                   ("'Kleep,' it says.'", N + " 'Kleep,' it says.'"),
                   ("— a reef heron; it is the same one", N + " — A reef heron; it is the same one.")):
    got = NGS.compose(N, bird) if not BASE_FLOW else ""
    check(got == want, f"compose(nest, {bird[:40]!r}) -> ...{got[len(N):][:60]!r}")
check((NGS.compose(N, "x") if not BASE_FLOW else "").count("  ") == 0, "exactly one space joins them")


# -- [2] the live gate through the REAL life.look_answer, at the shore -------------------------------------------------
print("\n[2] the LIVE gate through the real life.look_answer at the shore: same roll, same credit, the place's nest line said")
NOW_DAY = at(10, 12)
S.state.update({"weather": "clear", "wind": "breeze", "location": "shore"})


def run_look(target: str, place: str, render: bool, seed: int, live: bool, now: float = NOW_DAY):
    """One look from a clean life store: (answer, random state after, life_events rows, life_ledger rows, gate ledger rows)."""
    reset_life()
    clear_shadow()
    life.RENDER = render
    NGS.LIVE = live and not BASE_FLOW
    S.state["location"] = place
    random.seed(seed)
    try:
        ans = life.look_answer(target, place, now)
    finally:
        NGS.LIVE = not BASE_FLOW
    return ans, random.getstate(), events(), ledger_rows(), shadow_rows()


def find_seed(target: str, place: str, outcome: str, now: float = NOW_DAY) -> int:
    for sd in range(1, 400):
        _a, _r, ev, _l, _s = run_look(target, place, True, sd, False, now)
        if ev and ev[-1].get("outcome") == outcome:
            return sd
    return -1


set_places(shore=NEST3, garden=GARDEN_ON, wood=WOOD_ON)
NEST_LINE_3 = LINE_EGGS.format(w="three eggs")
GARDEN_LINE = "You part the leaves. Deep in it, a cup of mud and grass, and in the cup 3 eggs, blue-green, speckled."
WOOD_LINE = "You look up into the oak. A wood pigeon sits tight on a thin platform of twigs high up, white breast showing through the leaves."
ROUTED = [t for t, _c in REAL_LIFE_EVENTS if t != "the oystercatcher hunting near the scrape"]
check(len(ROUTED) == 6, f"the 6 distinct routed real targets (14 of the 15 real looks): {ROUTED}")
n_pairs = 0
for tgt in ROUTED:
    for outcome in ("sighting", "miss"):
        sd = find_seed(tgt, "shore", outcome)
        check(sd > 0, f"{tgt!r}: a seed that makes the bird's own roll a {outcome} ({sd})")
        old = run_look(tgt, "shore", True, sd, False)
        new = run_look(tgt, "shore", True, sd, True)
        n_pairs += 1
        want = NGS.compose(NEST_LINE_3, old[0]) if outcome == "sighting" else NEST_LINE_3
        check(new[0] == want, f"{tgt!r} / {outcome}: Du is shown {new[0][:70]!r}...{new[0][-50:]!r}")
        check(new[0].startswith(NEST_LINE_3), f"{tgt!r} / {outcome}: the answer starts with the place's nest line")
        if outcome == "miss":
            check("Nothing shows itself" not in new[0], f"{tgt!r} / miss: no 'Nothing shows itself' while the eggs stand")
        check(new[1] == old[1], f"{tgt!r} / {outcome}: the same random numbers drawn as the shadow flow")
        check(stable(new[2]) == stable(old[2]) and stable(new[3]) == stable(old[3]),
              f"{tgt!r} / {outcome}: the bird's life_events row and its ledger credit ({[r.get('kind') for r in new[3]]}) are exactly the shadow flow's")
        sh = new[4]
        ok = (len(sh) == 1 and sh[0]["kind"] == "diverted" and sh[0]["live"] is True and sh[0]["answer"] == new[0] and sh[0]["would_line"] == NEST_LINE_3
              and sh[0]["bird_outcome"] == outcome and sh[0]["bird_line"] == new[2][0]["line"] and sh[0]["nest_exists"] is True) if not BASE_FLOW else False
        check(ok, f"{tgt!r} / {outcome}: one gate ledger row, kind 'diverted', live true, answer == what Du was shown, bird_line == the life_events line")
print(f"    {n_pairs} paired looks (6 targets x sighting / miss)")
# a graduated bird: the individual suffix stays with the bird's line, after the nest line
sd = find_seed("the oystercatcher and eggs", "shore", "sighting")
_real_suffix = LT.with_individual_suffix
LT.with_individual_suffix = lambda key, line, place: line + "; it is the same one, the one that minds this shingle"
try:
    old = run_look("the oystercatcher and eggs", "shore", True, sd, False)
    new = run_look("the oystercatcher and eggs", "shore", True, sd, True)
finally:
    LT.with_individual_suffix = _real_suffix
check(new[0] == NGS.compose(NEST_LINE_3, old[0]) and "the one that minds this shingle" in new[0],
      "a recognised individual: the bird's line WITH its recognition suffix follows the nest line (graduation path untouched)")
# the shape the gate never takes, and plain creature looks: byte-identical to the shadow flow
for tgt in ("the oystercatcher hunting near the scrape", "the oystercatcher", "the oystercatcher on the shingle", "the oystercatcher's opened shells",
            "the gull and its eggs", "the eggs"):
    for sd in (3, 5, 9):
        old = run_look(tgt, "shore", True, sd, False)
        new = run_look(tgt, "shore", True, sd, True)
        check(new[:4] == old[:4] or (new[0] == old[0] and new[1] == old[1] and stable(new[2]) == stable(old[2]) and stable(new[3]) == stable(old[3])),
              f"{tgt!r} seed {sd}: not a nest-object look -> identical answer / random state / rows ({new[0][:50]!r})")
        check(not any(r.get("kind") == "diverted" for r in new[4]), f"{tgt!r} seed {sd}: no 'diverted' row")
# no nest at the shore: 'find none' (the noun as typed), plus the bird's line on a sighting
set_places(shore=None, garden=GARDEN_ON, wood=WOOD_ON)
for tgt, noun in (("the oystercatcher and eggs", "eggs"), ("the oystercatcher nest", "nest"), ("the oystercatcher's scrape", "scrape")):
    for outcome in ("sighting", "miss"):
        sd = find_seed(tgt, "shore", outcome)
        old = run_look(tgt, "shore", True, sd, False)
        new = run_look(tgt, "shore", True, sd, True)
        want = NGS.compose(FIND_NONE[noun], old[0]) if outcome == "sighting" else FIND_NONE[noun]
        check(new[0] == want and NEST_MARK not in new[0], f"no nest, {tgt!r} / {outcome}: {new[0][:90]!r}")
        check(bool(new[4]) and new[4][0].get("nest_exists") is False and new[4][0].get("answer") == new[0], "... the row says the nest did not stand, and what was said")
set_places(shore={"ts": 1.0, "eggs": 2}, garden=GARDEN_ON, wood=WOOD_ON)
sd = find_seed("the oystercatcher and its nest", "shore", "miss")
check(run_look("the oystercatcher and its nest", "shore", True, sd, True)[0] == LINE_EGGS.format(w="two eggs"), "the count comes from the nest state (2 eggs -> 'two eggs')")
set_places(shore=NEST3, garden=GARDEN_ON, wood=WOOD_ON)
# absent (the bird's activity below presence -- forced, since the oystercatcher is present at every probed hour): the nest line alone
_real_act = life.activity
life.activity = lambda r, place, now: 0.0
try:
    old = run_look("the oystercatcher and eggs", "shore", True, 5, False)
    new = run_look("the oystercatcher and eggs", "shore", True, 5, True)
finally:
    life.activity = _real_act
check(bool(old[2]) and old[2][0]["outcome"] == "absent" and new[0] == NEST_LINE_3 and stable(new[2]) == stable(old[2]),
      f"absent: the bird's own row says absent ({old[0][:50]!r}); Du is shown the nest line alone")


# -- [3] the blackbird and the wood pigeon ----------------------------------------------------------------------------
print("\n[3] the blackbird at the garden, the wood pigeon at the wood; a bird's nest asked at ANOTHER place is not diverted")
for tgt, place, line in (("the blackbird and its nest", "garden", GARDEN_LINE), ("the blackbird's eggs", "garden", GARDEN_LINE),
                         ("the wood pigeon and its nest", "wood", WOOD_LINE), ("the pigeon's nest", "wood", WOOD_LINE)):
    for sd in (7, 13, 21):
        old = run_look(tgt, place, True, sd, False)
        new = run_look(tgt, place, True, sd, True)
        bird_out = old[2][-1]["outcome"] if old[2] else None
        want = NGS.compose(line, old[0]) if bird_out == "sighting" else line
        check(new[0] == want, f"{tgt!r} @{place} seed {sd} ({bird_out}): {new[0][:60]!r}...")
        check(new[1] == old[1] and stable(new[3]) == stable(old[3]), f"{tgt!r} @{place} seed {sd}: same random state, same ledger credit")
for tgt, place in (("the nest of the wood pigeon", "garden"),):
    for sd in (7, 13):
        old = run_look(tgt, place, True, sd, False)
        new = run_look(tgt, place, True, sd, True)
        check(new[0] == old[0] and GARDEN_LINE not in new[0], f"{tgt!r} @{place}: the garden's nest is the blackbird's -- the pigeon's own roll answers, unchanged ({new[0][:50]!r})")
        check(len(new[4]) == 1 and new[4][0]["kind"] == "would_divert" and new[4][0].get("live") is False and new[4][0].get("answer") == "",
              f"{tgt!r} @{place}: still logged, as not gated (live false)")


# -- [4] controls: the inventory, RENDER off ----------------------------------------------------------------------------
print("\n[4] controls: the 1,526 observe-inventory phrasings x 4 places (render on) and the real looks with RENDER off are byte-identical to the shadow flow")
INV_PATH = ROOT / "docs" / "reviews" / "observe_inventory_2026-09-02.json"
inv: list = []


def _walk(x) -> None:
    if isinstance(x, str):
        inv.append(x)
    elif isinstance(x, dict):
        for k, v in x.items():
            if isinstance(k, str) and len(k) < 80 and not isinstance(v, str):
                inv.append(k)
            _walk(v)
    elif isinstance(x, list):
        for v in x:
            _walk(v)


_walk(json.loads(INV_PATH.read_text(encoding="utf-8")))
INV = sorted({s.lower().strip() for s in inv if 2 < len(s) < 80})
check(len(INV) == 1526, f"the observe inventory yields the 1,526 phrasings F-2382 swept ({len(INV)})")
inv_bad: list = []
n_reach = 0
for t in INV:
    for place in ("garden", "shore", "wood", "study"):
        if not life._match(t, place):
            continue
        n_reach += 1
        old = run_look(t, place, True, 2246, False)
        new = run_look(t, place, True, 2246, True)
        if new[1] != old[1]:      # a few looks (the study spider) are stateful across a clean life store: compare with a repeat of the shadow flow
            old = run_look(t, place, True, 2246, False)
        quiet(new[0] == old[0] and new[1] == old[1] and stable(new[2]) == stable(old[2]) and stable(new[3]) == stable(old[3]),
              f"{place}: {t!r}: {old[0][:40]!r} -> {new[0][:40]!r}", inv_bad)
for b in inv_bad[:8]:
    print("  FAIL", b)
check(not inv_bad, f"{n_reach} inventory looks that reach a living row: 0 changed by the live gate ({len(inv_bad)} changed)")
off_bad: list = []
for tgt, _c in REAL_LIFE_EVENTS:
    for sd in (1, 2, 3):
        old = run_look(tgt, "shore", False, sd, False)
        new = run_look(tgt, "shore", False, sd, True)
        quiet(new[0] == old[0] == "" and new[1] == old[1] and stable(new[2]) == stable(old[2]), f"RENDER off {tgt!r} {sd}", off_bad)
        quiet(all(r.get("live") is False for r in new[4]), f"RENDER off {tgt!r} {sd}: a row claims live", off_bad)
check(not off_bad, f"RENDER off: the gate is not live -- '' returned, same rows, rows say live false ({len(off_bad)} problems)")


# -- [5] fail-open ------------------------------------------------------------------------------------------------------
print("\n[5] fail-open: a gate that cannot read the place lets the bird answer exactly as before; a ledger failure never changes the answer")
sd = find_seed("the oystercatcher and eggs", "shore", "miss")
base_old = run_look("the oystercatcher and eggs", "shore", True, sd, False)
base_new = run_look("the oystercatcher and eggs", "shore", True, sd, True)


def _boom(msg):
    def f(*a, **k):
        raise RuntimeError(msg)
    return f


_real = {"wb": NGS.would_be, "state": SHL.nest_state, "record": NGS.record, "shape": LT.nest_object_shape, "compose": NGS.compose}
for label, arm, want in (("would_be raises", lambda: setattr(NGS, "would_be", _boom("x")), base_old[0]),
                         ("the shore's nest state read raises", lambda: setattr(SHL, "nest_state", _boom("bad json")), base_old[0]),
                         ("the gate shape raises", lambda: setattr(LT, "nest_object_shape", _boom("boom")), base_old[0]),
                         ("the ledger write raises", lambda: setattr(NGS, "record", _boom("disk full")), base_new[0]),
                         ("compose raises", lambda: setattr(NGS, "compose", _boom("c")), NEST_LINE_3)):
    try:
        arm()
        got = run_look("the oystercatcher and eggs", "shore", True, sd, True)
        check(got[0] == want and stable(got[2]) == stable(base_old[2]) and stable(got[3]) == stable(base_old[3]),
              f"fail-open [{label}]: answer {got[0][:50]!r}, the bird's rows unchanged")
    finally:
        NGS.would_be, SHL.nest_state, NGS.record, LT.nest_object_shape, NGS.compose = _real["wb"], _real["state"], _real["record"], _real["shape"], _real["compose"]
check(base_old[0] == "Nothing shows itself; whatever is there keeps still.", "(the baseline miss is the denial D-0444 fixes)")


# -- [6] the sensorium level --------------------------------------------------------------------------------------------
print("\n[6] the whole look through the real sensorium.look at the shore")
set_places(shore=NEST3, garden=GARDEN_ON, wood=WOOD_ON)
for tgt in ROUTED:
    reset_life(); clear_shadow(); life.RENDER = True; S.state["location"] = "shore"
    random.seed(sd)
    out = S.look(tgt)
    check(out.startswith(NEST_LINE_3), f"sensorium.look({tgt!r}) -> {out[:70]!r}")
reset_life(); clear_shadow(); random.seed(1)
out = S.look("the eggs")
check(out.startswith(NEST_LINE_3) and not any(r.get("kind") == "diverted" for r in shadow_rows()), "'the eggs' (no creature) is still the place's own nest look (J-1774), not the gate")
# the live-ledger fence: a non-live process pointed at data/ writes nothing and the answer stands
NGS._LEDGER = ROOT / "data" / "nest_gate_shadow.jsonl"
try:
    reset_life(); life.RENDER = True; NGS.LIVE = not BASE_FLOW; random.seed(sd)
    a = life.look_answer("the oystercatcher and eggs", "shore", NOW_DAY)
    check(a == NEST_LINE_3 and not NGS._LEDGER.exists(), "write fence: a non-live process gets the gated answer and NO ledger file (guard_path refuses quietly)")
finally:
    NGS._LEDGER = TMP / "nest_gate_shadow.jsonl"
st = NGS.status(TMP / "nope.jsonl")
check("by_kind" in st, "status() counts rows by kind (diverted / would_divert)")


# -- [7] isolation ------------------------------------------------------------------------------------------------------
print("\n[7] isolation")
check(not LIVE_WRITE_ATTEMPTS, f"the audit hook saw NO write attempt under any data/ ({len(LIVE_WRITE_ATTEMPTS)} attempts)"
                               f"{' -> ' + str(sorted({a[1] for a in LIVE_WRITE_ATTEMPTS})) if LIVE_WRITE_ATTEMPTS else ''}")
check(profile.LIVE is False, "this test never marked the process live")
_after = {p: _md5(p) for p in _LIVE_FILES}
for p in _LIVE_FILES:
    if _before[p] != _after[p]:
        print(f"    md5 {p.name} changed while this ran (Du online?); the audit hook above is the real proof")
for _p in (ROOT / "core" / "life.py", ROOT / "core" / "life_traces.py", ROOT / "core" / "nest_gate_shadow.py", Path(__file__)):
    try:
        py_compile.compile(str(_p), cfile=str(TMP / (_p.name + "c")), doraise=True)
        check(True, f"py_compile {_p.name}")
    except py_compile.PyCompileError as exc:
        check(False, f"py_compile {_p.name}: {exc}")

print(f"\n{'ALL OK' if not FAILS else f'{FAILS} FAILURE(S)'} — {CHECKS} checks — isolated store in {TMP}")
sys.exit(1 if FAILS else 0)
