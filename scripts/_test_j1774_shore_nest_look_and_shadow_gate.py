"""
Regression: the shore's NEST LOOK (built, restart-gated) and the nest-object gate (built SHADOW-ONLY) -- J-1774 / D-0345 (F-2382's draft).

The gap (verified, F-2382): shore_life's oyc_nest was read only by the ambient wildlife_line, status() and the presence adapter -- never by a
look. All 59 of Du's looks at the eggs, the nest or the scrape (hands_trace, 2026-09-02 to 10-03; every one at the shore, every one while the nest
stood) were answered nest-blind: 43 that name no creature by the generic shore text ('You look around the shore: shingle and rock ...'), 16 that
name the oystercatcher by the bird's own visibility roll (15 in life_events.jsonl: 6 sightings, 5 'Nothing shows itself; whatever is there keeps
still', 4 shadow sightings). The garden's and the wood's place looks already answer their nests in house voice.

D-0345 (Travis, 2026-10-04: "Needs a look then a log to add/check the object in a later session", "Place look now, gate logged"):
  PART 1 (live once Du restarts): sensorium._shore_look -> shore_life.look_nest. A look that names the nest, the eggs or the scrape and names NO
         creature is answered from the nest state: the scrape-and-eggs line (the count the nest's own, in words) or 'You look for <the noun he typed>
         and find none.'. Creature looks, trace-object looks and every other look are byte-identical.
  PART 2 (SHADOW ONLY): the nest-object gate for the three nest-owning birds (oystercatcher, blackbird, wood pigeon) -- life_traces.nest_object_shape
         (the trace_object_noun alias walk plus ONE 'and', nouns derived from the nest adapter rows + their `nest_nouns` data field) -- observed by
         core/nest_gate_shadow.py from life.look_answer, which appends what the gate WOULD divert to data/nest_gate_shadow.jsonl and changes NO answer.

  [0] module resolution + isolation set-up (the code under test is THIS root's; every store redirected into a temp dir)
  [1] PART 1 units: the noun detector (the 22 real no-creature shapes, the egg-case family it must not take), the line (every count, 15 bad counts,
      no nest, the noun as typed), purity (no random draw, no write)
  [2] PART 1 through the REAL sensorium.look at the shore: the 29 real distinct looks (59 looks) x nest on / nest off x life render on / off -- the 22
      that name no creature get the nest line, the 7 that name the oystercatcher are byte-identical to the pre-change flow; controls: the observe-inventory
      (1,526 phrasings) at the shore, the garden and the wood, egg-case looks, a carried look at a tracked object -- identical outputs AND random state
  [3] PART 2 gate units: nouns derived from the rows (and following the data), F-2382's synthetic table (100 of 100 nest shapes caught, 0 of 110
      creature shapes diverted), the 15 real looks (14 routed), 0 of 1,526 inventory phrasings x 4 places touched, J-1165's trace gate untouched
  [4] PART 2 shadow through the real life.look_answer: the row (every field), all three birds at their places, what is NOT logged, the write fence,
      fail-open in every mode, the read side
  [5] "every live answer is unchanged": shadow ON vs OFF over every real look, F-2382's synthetic table and the whole inventory x 4 places x render on/off:
      the returned line, the random state, the life_events rows and the life_ledger rows are identical
  [6] isolation: audit hook (no write attempt under any data/), live-file hashes, py_compile

ISOLATION. Every store look_answer / sensorium.look can reach is redirected into a temp dir before anything can write (the S-0016 / test-isolation rule;
the same vetted redirect list as scripts/_test_j1165_trace_object_look.py and scripts/life_smoke.py). A Python audit hook records any attempt by THIS
process to open-for-write / rename / remove under C:\\Nascence\\data or <root>\\data, and the live files are md5-hashed before and after (Du may be online
and change them on his own, so the audit hook is the real proof). Run it FROM the checkout it tests (core/satisfaction.py writes the real data/ from any
process -- F-2406 -- and this script never reaches it, but the habit is the rule). The live data is never read by this script: the real looks it replays are
frozen below (read-only census of 2026-10-04: hands_trace.jsonl and life_events.jsonl are append-only and would drift under a hermetic test).

  python scripts/_test_j1774_shore_nest_look_and_shadow_gate.py               # exit 0 = ALL OK
  python scripts/_test_j1774_shore_nest_look_and_shadow_gate.py --base-flow   # the pre-change flow (nest look and shadow gate stubbed out): must FAIL -- the test has teeth
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
TMP = Path(tempfile.mkdtemp(prefix="j1774_shore_nest_look_"))
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

life._F, life._LEDGER, life._EVENTS, life._DATA = TMP / "life_state.json", TMP / "life_ledger.jsonl", TMP / "life_events.jsonl", TMP
life._FLAGS_F = TMP / "life_flags.json"                        # read-only in life.py; redirected so the result never depends on the live flag file
WT._TRACES_F = TMP / "world_traces.json"
S._STATE_F = TMP / "room_state.json"
L._POS_F = TMP / "position.json"
SK._LEDGER_F = TMP / "sound_knowledge.json"
NGS._LEDGER = TMP / "nest_gate_shadow.jsonl"
_REDIRECTS = [(life, "_F"), (life, "_LEDGER"), (life, "_EVENTS"), (life, "_FLAGS_F"), (WT, "_TRACES_F"), (S, "_STATE_F"),
              (L, "_POS_F"), (SK, "_LEDGER_F"), (NGS, "_LEDGER")]
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
_ON_LOOK_NEST = _STUB_LOOK_NEST if BASE_FLOW else _REAL_LOOK_NEST
NGS.ENABLED = not BASE_FLOW
# J-2246 (D-0444, 2026-10-16): the gate is now LIVE by default. This test pins the SHADOW-ONLY mode (nest_gate_shadow.LIVE False: every answer
# unchanged, the row exactly as J-1774 shipped it); the live gate is pinned by scripts/_test_j2246_nest_gate_live_pairing.py.
NGS.LIVE = False
if BASE_FLOW:
    print("*** --base-flow: shore_life.look_nest stubbed to '' and the shadow gate disabled -- the new-behaviour checks below MUST fail ***")
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
print("    sys.path[0] =", sys.path[0])
for _m in (core, profile, life, LT, WT, life_birds, S, SHL, GL, WL, NGS):
    _f = getattr(_m, "__file__", None)
    print(f"    {_m.__name__:24s} -> {_f}")
    check(_f is not None and Path(_f).resolve().is_relative_to(ROOT), f"{_m.__name__} was loaded from inside {ROOT}")
check(hasattr(SHL, "look_nest") and hasattr(SHL, "nest_look_line") and hasattr(LT, "nest_object_shape") and hasattr(NGS, "observe"),
      "the loaded copy carries the J-1774 code (not a stale/shared copy)")
for _m, _a in _REDIRECTS:
    check(TMP in Path(str(getattr(_m, _a))).parents, f"{_m.__name__}.{_a} redirected into the temp dir")
ROWS = life.rows()
print(f"    {len(ROWS)} rows registered")

# -- [1] PART 1 units ---------------------------------------------------------------------------------------------------
print("\n[1] PART 1 units: the noun detector, the line, purity")
noun_bad: list = []
for tgt, want in EXPECT_NOUN.items():
    quiet(SHL.nest_look_noun(tgt) == want, f"nest_look_noun({tgt!r}) == {want!r}, got {SHL.nest_look_noun(tgt)!r}", noun_bad)
for b in noun_bad[:10]:
    print("  FAIL", b)
check(not noun_bad, f"the noun detector reads the {len(EXPECT_NOUN)} real no-creature shapes as typed ({len(noun_bad)} failures)")
NOT_NEST = ["the egg case", "the egg cases", "a skate's egg case", "an egg capsule", "the egg sac", "the egg sacs", "the egg shells", "the egg shell", "the mermaid's egg purse",
            "the egg-case", "the egg_case", "the eggshell", "the eggcase", "the nesting birds", "the nestling", "the nested rocks", "the scraped rock", "the scraper",
            "the sand", "the shingle", "the tide", "the cliff", "the oystercatcher", "the gulls", "the cat", "the sea", "the rock-pools", "the driftwood", "the seal",
            "the negg", "eggy", "the scrapey", "the-nest", "the nests-of", "", " ", None, 42, [], {}]
bad = [t for t in NOT_NEST if SHL.nest_look_noun(t) != ""]
check(not bad, f"{len(NOT_NEST)} looks that are NOT nest looks (egg case / sac / capsule / shell, egg-case, egg_case, nesting, scraped, odd inputs) name no nest noun: {bad}")
check(SHL.nest_look_noun("the eggs and the egg case") == "eggs" and SHL.nest_look_noun("the egg case and the nest") == "nest",
      "an egg case next to a real nest noun does not hide it")
check(SHL.nest_look_noun("THE  EGGS") == "eggs" and SHL.nest_look_noun("The Nest") == "nest", "case and spacing do not matter; the noun comes back lower-cased")
state = random.getstate()
for tgt, _n in REAL_NO_CREATURE:
    SHL.nest_look_noun(tgt)
    SHL.nest_look_line(SHL.nest_look_noun(tgt), NEST3)
    SHL.nest_look_line(SHL.nest_look_noun(tgt), None)
check(random.getstate() == state, "noun detector and line builder draw no random number")
# the line
for n, w in WORDS.items():
    check(SHL.nest_look_line("eggs", {"ts": 1.0, "eggs": n}) == LINE_EGGS.format(w=w), f"eggs={n} -> '... and in the scrape {w}, blotched like the stones.'")
nn_bad = []
for label, nest in BAD_COUNTS:
    line = SHL.nest_look_line("eggs", nest)
    quiet(line == LINE_EGGS.format(w="eggs"), f"{label}: names no number -> {line!r}", nn_bad)
    quiet(NUMBER_WORD.search(line) is None, f"{label}: no number word before 'egg(s)'", nn_bad)
for b in nn_bad[:6]:
    print("  FAIL", b)
check(not nn_bad, f"{len(BAD_COUNTS)} bad counts (missing / None / 0 / 5 / 9 / -2 / 'x' / '3' / 3.0 / True / list / dict / non-dict nest): each says "
                  f"'... in the scrape eggs, ...', no number, no exception")
check(all(SHL.nest_look_line("scrape", nest) == LINE_EGGS.format(w="three eggs") for nest in (NEST3, dict(NEST3, ts=2.0))) and
      all(SHL.nest_look_line(n, NEST3) == LINE_EGGS.format(w="three eggs") for n in FIND_NONE),
      "with a nest the line does not depend on the noun he typed (a scrape, a nest or the eggs are the same place)")
for noun, want in FIND_NONE.items():
    check(SHL.nest_look_line(noun, None) == want and SHL.nest_look_line(noun, {}) == want, f"no nest, noun {noun!r} -> {want!r}")
check(SHL.nest_look_line("", None) == FIND_NONE["scrape"] and SHL.nest_look_line(None, None) == FIND_NONE["scrape"], "no noun at all falls back to 'a scrape'")
# the state reader: a pure read
write_shore_state(NEST3)
check(SHL.nest_state() == NEST3, "nest_state() reads oyc_nest from the state file")
state = random.getstate()
for content in (None, "", "{", "[]", '{"oyc_nest": null}', '{"oyc_nest": {}}', '{"oyc_nest": 0}', '{"cairn": 1}'):
    if content is None:
        SHL._F.unlink()
    else:
        SHL._F.write_text(content, encoding="utf-8")
    check(SHL.nest_state() is None, f"nest_state() is None for state file {content!r}")
check(random.getstate() == state, "nest_state() draws no random number (even with the state file missing or corrupt -- _load()'s fallback would)")
check(not SHL._F.exists() or SHL._F.read_text(encoding="utf-8") == '{"cairn": 1}', "nest_state() writes nothing")

# -- [2] PART 1 through the real sensorium.look ----------------------------------------------------------------------------
print("\n[2] PART 1 through the REAL sensorium.look at the shore: nest on / off x life render on / off")
OLD_LOOK_NEST = _STUB_LOOK_NEST


def ask(target: str, flow: str, seed: int, render: bool, place: str = "shore"):
    """One look through the real sensorium.look from a clean life store, seeded; flow 'new' = as shipped, 'old' = the pre-change flow."""
    reset_life()
    life.RENDER = render
    SHL.look_nest = _ON_LOOK_NEST if flow == "new" else OLD_LOOK_NEST
    S.state["location"] = place
    random.seed(seed)
    out = S.look(target)
    rng = random.getstate()
    SHL.look_nest = _ON_LOOK_NEST
    return out, rng


sc_bad: list = []
n_new_diff = n_creature_same = 0
shown_old: dict = {}
for label, nest in (("nest eggs=3", NEST3), ("nest eggs=2", {"ts": 1.0, "eggs": 2}), ("no nest", None)):
    set_places(shore=nest)
    for render in (True, False):
        for tgt, _cnt in REAL_NO_CREATURE:
            new, rng_new = ask(tgt, "new", 1774, render)
            old, rng_old = ask(tgt, "old", 1774, render)
            noun = EXPECT_NOUN[tgt]
            want = LINE_EGGS.format(w=WORDS[nest["eggs"]]) if nest else FIND_NONE[noun]
            quiet(new == want, f"[{label} render={render}] {tgt!r} -> {new[:90]!r}, wanted the nest line {want[:60]!r}", sc_bad)
            quiet(old != want, f"[{label} render={render}] the pre-change flow did NOT say the nest line for {tgt!r}", sc_bad)
            n_new_diff += new != old
            shown_old.setdefault(tgt, old)
        for tgt, _cnt in REAL_CREATURE:
            new, rng_new = ask(tgt, "new", 1774, render)
            old, rng_old = ask(tgt, "old", 1774, render)
            quiet(new == old and rng_new == rng_old, f"[{label} render={render}] the creature look {tgt!r} is byte-identical (and draws the same random numbers): {new[:60]!r} vs {old[:60]!r}", sc_bad)
            quiet(NEST_MARK not in new, f"[{label} render={render}] the creature look {tgt!r} did not get the nest line", sc_bad)
            n_creature_same += new == old
for b in sc_bad[:12]:
    print("  FAIL", b)
check(not sc_bad, f"3 nest states x 2 render modes: the 22 real no-creature looks get the nest line (and the old flow never did), the 7 real creature looks are byte-identical "
                  f"({len(sc_bad)} failures)")
print("    old answers to the no-creature looks (what Du had): " + " | ".join(f"{t!r}: {v[:44]!r}" for t, v in list(shown_old.items())[:4]) + " ...")
set_places(shore=NEST3)
print("    new, nest eggs=3, 'the eggs'    :", ask("the eggs", "new", 1774, True)[0])
set_places(shore=None)
print("    new, no nest,     'the nest'    :", ask("the nest", "new", 1774, True)[0])
print("    new, no nest,     'the egg on the shore':", ask("the egg on the shore", "new", 1774, True)[0])
print(f"    {n_new_diff} (state x render x look) answers changed; {n_creature_same} creature answers byte-identical")
# what Du had for those 43 looks (the pre-change flow): the generic shore text, or a world_detail description of a word in the target ('shingle', 'stones')
_cnt = dict(REAL_NO_CREATURE)
_gen = sum(_cnt[t] for t, v in shown_old.items() if v.startswith("You look around the shore"))
_wd = sum(_cnt[t] for t, v in shown_old.items() if v.startswith("You look at "))
print(f"    before this change, the {sum(_cnt.values())} real no-creature looks got: the generic shore text x{_gen}, a world_detail description of a word in the look ('shingle', 'stones') x{_wd}, "
      f"anything else x{sum(_cnt.values()) - _gen - _wd}; none of them said a word about the nest")
# the 59 looks, weighted
total = sum(c for _, c in REAL_NO_CREATURE) + sum(c for _, c in REAL_CREATURE)
check(total == 59 and sum(c for _, c in REAL_NO_CREATURE) == 43 and sum(c for _, c in REAL_CREATURE) == 16 and len(REAL_NO_CREATURE) == 22 and len(REAL_CREATURE) == 7,
      "the frozen census adds up: 59 looks = 43 that name no creature (22 distinct) + 16 that name the oystercatcher (7 distinct)")

# controls: every other look is byte-identical, and its random state too
print("    controls: the observe-inventory (the 1,526 phrasings Du has used) and the families the new block must not take")
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
INV_NEST = [t for t in INV if SHL.nest_look_noun(t)]
print("    inventory phrasings that name a nest noun:", INV_NEST)
CONTROLS = ["the egg case", "a skate's egg case", "the egg-case", "the egg_case", "the egg sac", "the eggshell", "the sand", "the shingle", "the tide", "the gannet feather",
            "the oystercatcher", "the oystercatcher's opened shells", "the dead gannet", "the cave", "the rock-pools", "the cairn", "the fire-ring", "the burrows",
            "the mussel shelf", "the seal", "the sea", "the sky", "the cat", "the nesting birds", "the scraped rock", "the screaming bird"]
set_places(shore=NEST3)
ctl_bad: list = []
n_ctl = 0
self_unstable: set = set()
# The one family left out: the shore's exact-match driftwood branch (target in driftwood / log / fir / wood) answers from the tracked log's own observation
# ledger, which grows with every look (so a second look is not the first: the pre-change flow differs from ITSELF) and appends to data/buses_log.jsonl
# through core/buses.py's unfenced writer -- not in the vetted redirect list, and outside this change (the new block sits below it). Reported, not hidden.
DRIFTWOOD_EXACT = ("driftwood", "log", "fir", "wood")
INV_STATEFUL = [t for t in INV if t in DRIFTWOOD_EXACT]
print("    left out of the controls (the stateful driftwood branch, see above):", INV_STATEFUL)
for render in (True, False):
    for tgt in [t for t in INV if not SHL.nest_look_noun(t) and t not in DRIFTWOOD_EXACT] + CONTROLS:
        new, rng_new = ask(tgt, "new", 5, render)
        old, rng_old = ask(tgt, "old", 5, render)
        n_ctl += 1
        if new == old and rng_new == rng_old:
            continue
        # J-3505: the exact-match exclusion above is stale. (a) the shore's generic tracked-object branch (find_object_at: any phrasing that resolves to the
        # log -- 'the driftwood', 'driftwood shadow' ...) appends a look-count tail to the answer from an observation ledger that reset_life() does not clear
        # ('You have looked at this before -- N times since yesterday ...', N +1 per look, absent on the very first look); (b) the cat look ('the black cat')
        # returns the same text but a differing random state from one identical call to the next. Verified old-vs-old (same seed, pre-change flow): both
        # differ from THEMSELVES, so this is not the nest look. Accepted only for exactly those two families, and only if the answers are equal once that
        # tail is dropped (for the cat: equal text); the random state is not compared for them.
        _norm = lambda x: re.sub(r" You have looked at this before .*$", "", x)
        if ("driftwood" in tgt or tgt == "the black cat") and _norm(new) == _norm(old):
            self_unstable.add(tgt)
            continue
        quiet(False, f"[render={render}] {tgt!r}: new {new[:50]!r} vs old {old[:50]!r}", ctl_bad)
print("    pre-change flow differs from ITSELF on (same seed; new == old modulo look-count) -- J-3505:", sorted(self_unstable))
check(all(("driftwood" in t) or t == "the black cat" for t in self_unstable), "the self-unstable looks are only the tracked-log family and the black cat")
for b in ctl_bad[:10]:
    print("  FAIL", b)
check(not ctl_bad, f"{n_ctl} other looks at the shore (every inventory phrasing that names no nest noun but the {len(INV_STATEFUL)} stateful driftwood ones, + {len(CONTROLS)} controls) "
                   f"x render on / off: byte-identical, same random state ({len(ctl_bad)} differ)")
# the inventory's own nest-noun phrasings are the no-creature looks the ruling wants answered
for tgt in INV_NEST:
    new, _r = ask(tgt, "new", 5, True)
    check(new == LINE_EGGS.format(w="three eggs"), f"the inventory phrasing {tgt!r} gets the nest line while the nest stands")
# the other places have no new block: their nest-word looks are untouched
pl_bad: list = []
for place, nest_kw in (("garden", dict(garden=GARDEN_ON)), ("wood", dict(wood=WOOD_ON)), ("garden", dict()), ("wood", dict())):
    set_places(shore=NEST3, **nest_kw)
    for tgt in ("the nest", "the eggs", "the scrape", "the blackbird's nest", "the wood pigeon and its nest"):
        new, rng_new = ask(tgt, "new", 9, True, place)
        old, rng_old = ask(tgt, "old", 9, True, place)
        quiet(new == old and rng_new == rng_old, f"[{place} {sorted(nest_kw)}] {tgt!r}", pl_bad)
check(not pl_bad, "the garden and the wood answer their nest looks exactly as before (the new block lives in the shore's look only)")
# an earlier branch keeps a target it already claimed even when the target also names a nest noun (the new block sits after every existing branch,
# the tracked-object and cat looks included; the egg-case family never reaches it: nest_look_noun names no noun for it, above)
set_places(shore=NEST3)
for tgt, marker in (("the eggs in the cave", "cave"), ("the nest on the ledge", "ledge"), ("the eggs on the sand", "sand flat"), ("the scrape by the fire-ring", "fire"),
                    ("the nest near the cairn", "cairn"), ("the eggs among the rock-pools", "rock-pool"), ("the eggs and the tide", "tide")):
    new, _r = ask(tgt, "new", 3, True)
    old, _r2 = ask(tgt, "old", 3, True)
    check(new == old, f"{tgt!r}: an existing shore branch ({marker}) still claims it first -- byte-identical to the pre-change flow")

# -- [3] PART 2 gate units --------------------------------------------------------------------------------------------------
print("\n[3] PART 2 gate units (life_traces.nest_object_shape / nest_object_noun): derived nouns, F-2382's table, the real looks, the inventory")
NEST_ROWS = {k: r for k, r in ROWS.items() if r.get("nest") and not r.get("external")}
check(sorted(NEST_ROWS) == ["blackbird", "kereru", "oystercatcher"], f"exactly three rows own a nest: {sorted(NEST_ROWS)}")
ADAPTERS = {k: ROWS[r["nest"]] for k, r in NEST_ROWS.items()}
check(all(a.get("kind") == "external" for a in ADAPTERS.values()), "each owns an EXTERNAL nest adapter row (the stage machines in garden_life / wood_life / shore_life)")
check(all(tuple(a.get("nest_nouns") or ()) == ("egg", "eggs") for a in ADAPTERS.values()), "the one data field: nest_nouns == ('egg', 'eggs') on all three adapter rows")
for k, want in (("oystercatcher", {"scrape", "nest", "egg", "eggs"}), ("blackbird", {"nest", "egg", "eggs"}), ("kereru", {"nest", "egg", "eggs"})):
    got = LT.nest_nouns(NEST_ROWS[k])
    check(got == want, f"{k}: nest nouns {sorted(got)} == {sorted(want)} (name head + key tail + the data field)")
# the derivation follows the DATA: a synthetic nest adapter and an owner of it, nothing typed in
_zz_nest = life.row("zz_den", kind="external", name="the zzyzx's holt", places={"garden": ["hedge"]}, nest_nouns=("pups", "cubs"))
_zz = life.row("zz_j1774_probe", aliases=("zzyzx",), places={"garden": ["hedge"]}, nest="zz_den")
check(LT.nest_nouns(_zz, _zz_nest) == {"holt", "den", "pups", "cubs"}, "an invented adapter yields its own nouns (name head 'holt', key tail 'den', the field's 'pups' and 'cubs')")
check(LT.nest_object_shape(_zz, "the zzyzx and its pups", _zz_nest) == ("pups", "conjunction") and LT.nest_object_shape(_zz, "the zzyzx's holt", _zz_nest) == ("holt", "adjacent/possessive"),
      "edit the data and the gate follows (an invented 'pups' / 'holt' row is caught with no word typed into the code)")
check(LT.nest_object_shape(_zz, "the zzyzx and its eggs", _zz_nest) == ("", ""), "'eggs' is not a noun of an adapter that does not carry it (nothing typed in)")
check(LT.nest_nouns(life.row("zz_none", aliases=("zzyzx",)), None) == set() and LT.nest_object_shape(life.row("zz_none", aliases=("zzyzx",)), "the zzyzx and its nest") == ("", ""),
      "a row with no nest adapter has no nest nouns and is never touched")
_consts = set()
for _fn in (LT.nest_nouns, LT.nest_object_shape, LT.nest_object_noun):
    _consts |= {c for c in _fn.__code__.co_consts if isinstance(c, str)}
check(not (_consts & {"scrape", "egg", "eggs", "scrapes"}), "none of the derived / data-field nouns ('scrape', 'egg', 'eggs') appears as a literal in the gate's code")

# F-2382's synthetic table: every alias of the three nest-owning rows x ten nest-object shapes and eleven creature shapes
EXP_YES = ["the {a} nest", "the {a}'s nest", "the {a}'s eggs", "the {a} and eggs", "the {a} and its nest", "the {a} and the eggs", "the nest of the {a}",
           "the eggs of the {a}", "the {a} and its big nest", "the {a} nest in the bushes"]
EXP_NO = ["the {a}", "the {a} hunting near the nest", "the {a} on the nest", "the {a} sitting on eggs", "the {a} with eggs", "the {a} at the nest", "the {a} and the tide",
          "the {a} and a crab", "the {a} and its feathers", "the {a} near the eggs", "the {a} guarding its nest"]
n_yes = n_no = 0
tab_bad: list = []
n_alias = 0
for k, r in NEST_ROWS.items():
    for a in r["aliases"]:
        n_alias += 1
        for f in EXP_YES:
            n_yes += 1
            quiet(LT.nest_object_noun(r, f.format(a=a)) != "", f"[{k}] MISSED nest shape {f.format(a=a)!r}", tab_bad)
        for f in EXP_NO:
            n_no += 1
            quiet(LT.nest_object_noun(r, f.format(a=a)) == "", f"[{k}] DIVERTED creature shape {f.format(a=a)!r} -> {LT.nest_object_shape(r, f.format(a=a))}", tab_bad)
for b in tab_bad[:12]:
    print("  FAIL", b)
print(f"    synthetic table over {len(NEST_ROWS)} rows / {n_alias} aliases: {n_yes} nest-object shapes, {n_no} creature shapes; wrong calls: {len(tab_bad)}")
check(n_alias == 10 and n_yes == 100 and n_no == 110, f"the table is F-2382's: 10 aliases x (10 nest + 11 creature) shapes = {n_yes} + {n_no}")
check(not tab_bad, f"F-2382's draft reproduced: {n_yes - sum('MISSED' in b for b in tab_bad)} of {n_yes} nest shapes caught, "
                   f"{sum('DIVERTED' in b for b in tab_bad)} of {n_no} creature shapes diverted")
# named shapes, with how each was decided
oy = NEST_ROWS["oystercatcher"]
AMBIG = [("the oystercatcher and eggs", ("eggs", "conjunction"), "REAL (8 live): 'and' bridges to the eggs"),
         ("the oystercatcher and its nest", ("nest", "conjunction"), "REAL (2): the determiner is skipped"),
         ("the oystercatcher and its eggs", ("eggs", "conjunction"), "REAL (1)"),
         ("the oystercatcher and the eggs", ("eggs", "conjunction"), "REAL (1)"),
         ("the oystercatcher nest", ("nest", "adjacent/possessive"), "REAL (1): the attributive shape, like 'the gannet feather'"),
         ("the oystercatcher's scrape", ("scrape", "adjacent/possessive"), "REAL (1): the possessive; 'scrape' is the adapter's name head"),
         ("the oystercatchers' scrape", ("scrape", "adjacent/possessive"), "the plural possessive of the alias"),
         ("the oystercatcher’s scrape", ("scrape", "adjacent/possessive"), "a curly apostrophe is the same possessive"),
         ("the nest of the oystercatcher", ("nest", "of-form"), "'the feather of the gannet' shape"),
         ("The  Oystercatcher   AND   Eggs", ("eggs", "conjunction"), "case and spacing do not matter"),
         ("the oystercatcher and its big speckled eggs", ("eggs", "conjunction"), "a short run of adjectives is fine"),
         ("the oystercatcher hunting near the scrape", ("", ""), "REAL (1): 'hunting' (a participle) and 'near' end the phrase -> stays a bird look"),
         ("the oystercatcher", ("", ""), "no nest noun"),
         ("the oystercatcher on the nest", ("", ""), "a preposition ends the phrase"),
         ("the oystercatcher sitting on eggs", ("", ""), "a participle ends the phrase"),
         ("the oystercatcher, eggs", ("", ""), "a comma ends the phrase"),
         ("the oystercatcher and the gull and the eggs", ("", ""), "ONE 'and' only: the second ends the phrase"),
         ("the oystercatcher and the tide", ("", ""), "'and' bridges only to a nest noun"),
         ("the oystercatcher's opened shells", ("", ""), "a trace object, not a nest object (J-1165's gate owns it)"),
         ("the nest", ("", ""), "no creature alias in the target: never reaches a nest-owning row"),
         ("eggs", ("", ""), "same"),
         (None, ("", ""), "odd input"), ("", ("", ""), "odd input"), ("the", ("", ""), "odd input"), ("'s", ("", ""), "odd input")]
for tgt, want, why in AMBIG:
    got = LT.nest_object_shape(oy, tgt)
    check(got == want, f"{str(tgt)!r:48s} -> {got!r:28s} | {why}")
bb, kr = NEST_ROWS["blackbird"], NEST_ROWS["kereru"]
for row_, tgt, want in ((bb, "the blackbird's nest", "nest"), (bb, "the blackbird and its nest in the bushes", "nest"), (bb, "the blackbird and eggs", "eggs"),
                        (bb, "the blackbirds' nest", "nest"), (bb, "the blackbird and its scrape", ""), (kr, "the wood pigeon's nest", "nest"),
                        (kr, "the wood pigeon and its nest", "nest"), (kr, "the pigeon's eggs", "eggs"), (kr, "the kererū's nest", "nest"), (kr, "the kereru and eggs", "eggs"),
                        (kr, "the wood pigeon on its nest", ""), (kr, "the wood pigeon in the oak", "")):
    check(LT.nest_object_noun(row_, tgt) == want, f"[{row_['key']}] {tgt!r} -> {want!r}")
gulls = ROWS["gulls"]
check(not gulls.get("nest") and LT.nest_object_shape(gulls, "the gull and its eggs") == ("", "") and LT.nest_object_shape(gulls, "the gulls' nest") == ("", ""),
      "a bird that owns no nest adapter (the gulls) is never touched: 'the gull and its eggs' stays a creature look")
# J-1165's gate is untouched: a nest look is still not a trace object (its test pins 'the nest adapter is a separate question')
check(LT.trace_object_noun(oy, "the oystercatcher and eggs") == "" and LT.trace_object_noun(oy, "the oystercatcher and its nest") == "" and
      LT.trace_object_noun(oy, "the oystercatcher's scrape") == "" and LT.trace_object_noun(oy, "the oystercatcher's opened shells") == "shells",
      "life_traces.trace_object_noun (J-1165) is untouched: no nest look is a trace object, the opened shells still are")
# the real looks
real_bad: list = []
routed = left = 0
for tgt, cnt in REAL_LIFE_EVENTS:
    m = life._match(tgt, "shore")
    quiet(m is not None and m["key"] == "oystercatcher", f"{tgt!r} reaches the oystercatcher row", real_bad)
    noun = LT.nest_object_noun(m, tgt) if m else ""
    if noun and not LT.trace_object_noun(m, tgt):
        routed += cnt
    else:
        left += cnt
print(f"    the 15 real creature looks: {routed} routed to the nest by the gate, {left} left as bird looks")
check(not real_bad and routed == 14 and left == 1 and sum(c for _, c in REAL_LIFE_EVENTS) == 15,
      "14 of the 15 real nest-class creature looks routed (6 of the 7 distinct targets); the one left is 'hunting near the scrape'")
check(LT.nest_object_noun(life._match("the oystercatcher hunting near the scrape", "shore"), "the oystercatcher hunting near the scrape") == "", "... and it is that one")
# the inventory x four places
inv_div = []
n_reach = 0
for t in INV:
    for place in ("garden", "shore", "wood", "study"):
        m = life._match(t, place)
        if m:
            n_reach += 1
            if m.get("nest") and not LT.trace_object_noun(m, t) and LT.nest_object_noun(m, t):
                inv_div.append((place, t, m["key"]))
print(f"    inventory: {len(INV)} phrasings x 4 places = {len(INV) * 4} pairs, {n_reach} reach a living row, {len(inv_div)} diverted by the nest gate {inv_div[:5]}")
check(not inv_div, f"0 of {len(INV)} inventory phrasings x 4 places touched by the nest gate")

# -- [4] PART 2 shadow through the real life.look_answer ------------------------------------------------------------------
print("\n[4] PART 2 shadow through the REAL life.look_answer: the row, the three birds, what is not logged, the fence, fail-open, the read side")
NOW_DAY = at(10, 12)
S.state.update({"weather": "clear", "wind": "breeze", "location": "shore"})


def run_look(target: str, place: str, render: bool, seed: int, now: float = NOW_DAY):
    reset_life()
    clear_shadow()
    life.RENDER = render
    S.state["location"] = place
    random.seed(seed)
    ans = life.look_answer(target, place, now)
    return ans, events(), shadow_rows()


def find_seed(target: str, place: str, outcome: str, render: bool = True) -> int:
    for sd in range(1, 400):
        _a, ev, _sh = run_look(target, place, render, sd)
        if ev and ev[-1].get("outcome") == outcome:
            return sd
    return -1


set_places(shore=NEST3, garden=GARDEN_ON, wood=WOOD_ON)
NEST_LINE_3 = LINE_EGGS.format(w="three eggs")
GARDEN_LINE = "You part the leaves. Deep in it, a cup of mud and grass, and in the cup 3 eggs, blue-green, speckled."
WOOD_LINE = "You look up into the oak. A wood pigeon sits tight on a thin platform of twigs high up, white breast showing through the leaves."
# the oystercatcher at the shore: a sighting and a miss
for outcome in ("sighting", "miss"):
    sd = find_seed("the oystercatcher and eggs", "shore", outcome)
    check(sd > 0, f"a seed that makes the oystercatcher's own roll a {outcome} was found ({sd})")
    ans, ev, sh = run_look("the oystercatcher and eggs", "shore", True, sd)
    check(len(ev) == 1 and ev[0]["outcome"] == outcome and ev[0]["key"] == "oystercatcher", f"the life_events row is the bird's own {outcome} (as before)")
    check(len(sh) == 1, f"one shadow row for the one nest-object look ({len(sh)})")
    if sh:
        r = sh[0]
        check(r["kind"] == "would_divert" and r["key"] == "oystercatcher" and r["place"] == "shore" and r["target"] == "the oystercatcher and eggs", f"row: kind / key / place / look text ({r['kind']}, {r['key']}, {r['place']}, {r['target']!r})")
        check(r["noun"] == "eggs" and r["shape"] == "conjunction", f"row: the noun he used and the shape ({r['noun']!r}, {r['shape']!r})")
        check(r["would_line"] == NEST_LINE_3 and r["nest_exists"] is True and r["nest"] == "eggs 3", f"row: the would-be nest line is the shore's own, read from the nest state ({r['nest']!r})")
        check(r["bird_outcome"] == outcome and r["sighted"] is (outcome == "sighting") and r["bird_line"] == ev[0]["line"] and r["rendered"] is True,
              f"row: whether the bird's own roll sighted it ({r['sighted']}), the bird's own line == the life_events row's line, rendered True")
        check(isinstance(r["ts"], float) and set(r) == {"ts", "kind", "key", "place", "target", "noun", "shape", "would_line", "nest_exists", "nest",
                                                        "bird_outcome", "sighted", "bird_line", "rendered"}, "row: exactly the documented fields")
    check(ans == ev[0]["line"], f"the answer Du got is still the bird's own roll, unchanged ({ans[:50]!r})")
    if outcome == "miss":
        check(ans == "Nothing shows itself; whatever is there keeps still.", "... the 'Nothing shows itself' miss the gate WOULD have replaced with the nest line, is what is still said")
# no nest at the shore: the honest branch
set_places(shore=None, garden=None, wood=None)
for tgt, noun in (("the oystercatcher and eggs", "eggs"), ("the oystercatcher nest", "nest"), ("the oystercatcher's scrape", "scrape")):
    _a, ev, sh = run_look(tgt, "shore", True, 11)
    check(len(sh) == 1 and sh[0]["would_line"] == FIND_NONE[noun] and sh[0]["nest_exists"] is False and sh[0]["nest"] == "", f"no nest: {tgt!r} -> would say {FIND_NONE[noun]!r}")
# every shape: which looks log a row
set_places(shore=NEST3, garden=GARDEN_ON, wood=WOOD_ON)
for tgt, cnt in REAL_LIFE_EVENTS:
    _a, ev, sh = run_look(tgt, "shore", True, 21)
    want_row = LT.nest_object_noun(life._match(tgt, "shore"), tgt) != ""
    check(len(sh) == (1 if want_row else 0) and len(ev) == 1, f"{tgt!r}: {'one shadow row' if want_row else 'no shadow row'} and the usual single life_events row")
# not logged: plain creature looks, trace objects, carcasses, rows with no nest, a look that names no creature, a place with no such bird
for tgt, place in (("the oystercatcher", "shore"), ("the oystercatcher's opened shells", "shore"), ("the dead oystercatcher", "shore"), ("the gull and its eggs", "shore"),
                   ("the gulls' nest", "shore"), ("the shag on the rock", "shore"), ("the eggs", "shore"), ("the nest", "shore"), ("the screaming bird", "shore"),
                   ("the blackbird", "garden"), ("the tui and its nest", "garden"), ("the wood pigeon on its branch", "wood")):
    _a, ev, sh = run_look(tgt, place, True, 5)
    check(not sh, f"{tgt!r} @{place}: no shadow row ({len(sh)})")
# the blackbird and the wood pigeon at their places: the place's own nest line
for tgt, place, key, noun, shape, would in (("the blackbird and its nest", "garden", "blackbird", "nest", "conjunction", GARDEN_LINE),
                                            ("the blackbird's eggs", "garden", "blackbird", "eggs", "adjacent/possessive", GARDEN_LINE),
                                            ("the wood pigeon and its nest", "wood", "kereru", "nest", "conjunction", WOOD_LINE),
                                            ("the pigeon's nest", "wood", "kereru", "nest", "adjacent/possessive", WOOD_LINE),
                                            ("the nest of the wood pigeon", "garden", "kereru", "nest", "of-form", GARDEN_LINE)):
    # each bird is present at the hour asked, or the row says absent: the gate does not depend on it
    _a, ev, sh = run_look(tgt, place, True, 7)
    ok = len(sh) == 1 and sh[0]["key"] == key and sh[0]["noun"] == noun and sh[0]["shape"] == shape and sh[0]["would_line"] == would and sh[0]["nest_exists"] is True
    check(ok, f"{tgt!r} @{place}: one row, {key}, {noun} / {shape}, would-be line {would[:48]!r}" + ("" if ok else f"  GOT {sh}"))
    check(bool(ev) and sh and sh[0]["bird_outcome"] == ev[-1]["outcome"], f"{tgt!r} @{place}: the bird's own outcome ({sh[0]['bird_outcome'] if sh else None}) is the life_events row's")
# the garden's and the wood's would-be lines ARE what their own looks say (a pin against drift), nest on and off
for label, g, w in (("nest on", GARDEN_ON, WOOD_ON), ("no nest", None, None)):
    set_places(shore=NEST3, garden=g, wood=w)
    S.state["location"] = "garden"
    real_g = GL.look("the nest")
    S.state["location"] = "wood"
    real_w = WL.look("the nest")
    S.state["location"] = "shore"
    check(NGS.would_be("garden", "nest")[0] == real_g, f"garden ({label}): the shadow's would-be line == garden_life.look('the nest'): {real_g[:60]!r}")
    check(NGS.would_be("wood", "nest")[0] == real_w, f"wood ({label}): the shadow's would-be line == wood_life.look('the nest'): {real_w[:60]!r}")
    check(NGS.would_be("shore", "nest")[0] == SHL.look_nest("the nest") or BASE_FLOW, f"shore ({label}): the shadow's would-be line == shore_life.look_nest('the nest')")
check(NGS.would_be("study", "nest") == ("", False, "") and NGS.would_be("", "nest") == ("", False, ""), "a place with no nest look has no would-be line")
# a day where the wood / garden state files are stages the places word differently
for st in ("building", "eggs", "chicks", "fledged"):
    set_places(garden={"stage": st, "stage_ts": 1.0, "where": "bushes", "eggs": 3, "lost": 1})
    S.state["location"] = "garden"
    check(NGS.would_be("garden", "eggs")[0] == "You part the leaves." + GL._nest_line(GL._load(), "bushes", direct=True) and "part the leaves" in GL.look("the eggs"),
          f"garden stage {st}: the would-be line is 'You part the leaves.' + the stage line the garden's own look composes")
S.state["location"] = "shore"
# rendered flag: the shadow branch of the life engine (RENDER off) still observes
set_places(shore=NEST3, garden=GARDEN_ON, wood=WOOD_ON)
a_off, ev_off, sh_off = run_look("the oystercatcher and eggs", "shore", False, 3)
check(a_off == "" and len(ev_off) == 1 and ev_off[0]["kind"] == "would_answer" and len(sh_off) == 1 and sh_off[0]["rendered"] is False,
      "RENDER off: look_answer returns '' (the place answers) and logs would_answer as before; the shadow row says rendered False")
# the write fence: a non-live process writes nothing, quietly
_row_oy = life._match("the oystercatcher and eggs", "shore")
NGS._LEDGER = ROOT / "data" / "nest_gate_shadow.jsonl"          # the worktree's own data/ -- a path the fence refuses for a non-live process
try:
    wrote = NGS.observe(_row_oy, "the oystercatcher and eggs", "shore", "sighting", "x", True)
    check(wrote is False and not NGS._LEDGER.exists(), "write fence: a non-live process pointed at data/ gets False and NO file (guard_path refuses, nothing raised)")
    reset_life(); life.RENDER = True; random.seed(4)
    ans_fenced = life.look_answer("the oystercatcher and eggs", "shore", NOW_DAY)
    check(isinstance(ans_fenced, str) and ans_fenced != "" and not NGS._LEDGER.exists(), "write fence: look_answer still answers while the ledger is refused, and no file appears")
finally:
    NGS._LEDGER = TMP / "nest_gate_shadow.jsonl"
try:
    profile.guard_path(Path(r"C:\Nascence") / "data" / "nest_gate_shadow.jsonl")
    check(False, "write fence: the live ledger path is refused for a non-live process")
except profile.NonLiveWriteError:
    check(True, "write fence: profile.guard_path refuses the live data/nest_gate_shadow.jsonl for a non-live process (D-0179) -- this test made no write there")
check(profile.LIVE is False, "this test never marked the process live")
_was_live = profile.LIVE
profile.LIVE = True                                              # the live Du boot: the ledger path (here redirected into the temp dir) is written
try:
    clear_shadow()
    wrote = NGS.observe(_row_oy, "the oystercatcher and eggs", "shore", "miss", "Nothing shows itself; whatever is there keeps still.", True)
finally:
    profile.LIVE = _was_live
check((wrote is True) is (not BASE_FLOW) and len(shadow_rows()) == (0 if BASE_FLOW else 1), "profile.LIVE: the same call writes its one row (only the live Du boot records)")
# fail-open in every mode: the answer never changes and nothing raises. Each mode patches ONE piece of the shadow path (never profile.guard_path itself:
# life's own writes go through it).
set_places(shore=NEST3, garden=GARDEN_ON, wood=WOOD_ON)
base_ans, base_ev, _sh = run_look("the oystercatcher and eggs", "shore", True, 4)


def _boom(msg):
    def f(*a, **k):
        raise RuntimeError(msg)
    return f


_real = {"record": NGS.record, "shape": LT.nest_object_shape, "wb": NGS.would_be, "state": SHL.nest_state}
modes = [("the ledger write raises (disk error)", lambda: setattr(NGS, "record", _boom("disk full")), False),
         ("the gate raises", lambda: setattr(LT, "nest_object_shape", _boom("boom")), False),
         ("the place state is unreadable (would_be raises)", lambda: setattr(NGS, "would_be", _boom("no state")), True),
         ("the shore's nest state read raises", lambda: setattr(SHL, "nest_state", _boom("bad json")), True)]
for label, arm, row_still_written in modes:
    try:
        arm()
        clear_shadow()
        reset_life(); life.RENDER = True; random.seed(4)
        ans = life.look_answer("the oystercatcher and eggs", "shore", NOW_DAY)
        evs, rows_ = events(), shadow_rows()
        check(ans == base_ans and stable(evs) == stable(base_ev), f"fail-open [{label}]: the answer and the life_events row are exactly the ones without any shadow gate")
        if not BASE_FLOW:
            if row_still_written:
                check(len(rows_) == 1 and rows_[0]["would_line"] == "" and rows_[0]["nest"] == "place state unreadable" and rows_[0]["nest_exists"] is False,
                      f"fail-open [{label}]: the row is still written, saying the place state was unreadable")
            else:
                check(not rows_, f"fail-open [{label}]: no row, no exception")
    finally:
        NGS.record, LT.nest_object_shape, NGS.would_be, SHL.nest_state = _real["record"], _real["shape"], _real["wb"], _real["state"]
NGS.ENABLED = False
_a, _e, sh_dis = run_look("the oystercatcher and eggs", "shore", True, 4)
NGS.ENABLED = not BASE_FLOW
check(not sh_dis, "ENABLED False: observe() is a no-op")
# the read side
clear_shadow()
life.RENDER = True
for tgt in ("the oystercatcher and eggs", "the oystercatcher nest"):
    reset_life(); random.seed(8)
    life.look_answer(tgt, "shore", NOW_DAY)
with open(NGS._LEDGER, "a", encoding="utf-8") as f:
    f.write('{"ts": 1.0, "kind": "would_div')                                  # a torn last line (a crash mid-append)
rows_ = NGS.read_rows(0.0, NGS._LEDGER)
st = NGS.status(NGS._LEDGER)
check(BASE_FLOW or (len(rows_) == 2 and st["ledger_rows"] == 2), f"read_rows / status skip a torn last line ({len(rows_)} rows)")
check(BASE_FLOW or (st["by_key"] == {"oystercatcher": 2} and st["by_shape"] == {"conjunction": 1, "adjacent/possessive": 1} and st["nest_stood"] == 2 and st["nest_absent"] == 0
                    and st["first_ts"] is not None and st["last_ts"] >= st["first_ts"]), f"status(): counts by creature / shape / whether the nest stood ({st['by_key']}, {st['by_shape']})")
check(NGS.read_rows(0.0, TMP / "nope.jsonl") == [] and NGS.status(TMP / "nope.jsonl")["ledger_rows"] == 0 and NGS.read_rows(1e18, NGS._LEDGER) == [], "a missing ledger or a future since_ts reads as []")
clear_shadow()

# -- [5] every live answer is unchanged --------------------------------------------------------------------------------------
print("\n[5] every live answer is unchanged: the shadow gate ON vs OFF -- the line, the random state, the life_events rows, the life_ledger rows")
set_places(shore=NEST3, garden=GARDEN_ON, wood=WOOD_ON)


def paired(target: str, place: str, render: bool, seed: int):
    """(answer, random state, stable events, stable ledger, shadow rows) for the shadow gate ON then OFF, from a clean store, same seed, same instant."""
    out = []
    for enabled in (True, False):
        NGS.ENABLED = enabled and not BASE_FLOW
        reset_life(); clear_shadow(); life.RENDER = render; S.state["location"] = place
        random.seed(seed)
        ans = life.look_answer(target, place, NOW_DAY)
        out.append((ans, random.getstate(), stable(events()), stable(ledger_rows()), shadow_rows()))
    NGS.ENABLED = not BASE_FLOW
    return out


# WARM-UP: the first look at a place in a fresh process lazily initialises that place's state (the study's, for one) and draws random numbers
# exactly once, with the shadow gate on or off -- found by a first run of this sweep whose single random-state "difference" was the very first study
# look. Every place is touched once, both render modes, before anything is compared.
for _place, _tgt in (("garden", "the blackbird"), ("shore", "the oystercatcher"), ("wood", "the wood pigeon"), ("study", "the spider's web")):
    for _render in (True, False):
        NGS.ENABLED = False
        reset_life(); life.RENDER = _render; S.state["location"] = _place
        life.look_answer(_tgt, _place, NOW_DAY)
NGS.ENABLED = not BASE_FLOW
diff_bad: list = []
n_pairs = n_rows_on = n_rows_off = n_expect_rows = 0
corpus = []
for tgt, _c in REAL_LIFE_EVENTS + REAL_NO_CREATURE + REAL_CREATURE:
    corpus.append((tgt, "shore"))
for k, r in NEST_ROWS.items():
    for a in r["aliases"]:
        for f in EXP_YES + EXP_NO:
            for place in sorted(r["places"]):
                corpus.append((f.format(a=a), place))
for t in INV:
    for place in ("garden", "shore", "wood", "study"):
        corpus.append((t, place))
corpus = list(dict.fromkeys(corpus))
print(f"    corpus: {len(corpus)} (look, place) pairs x render on / off x shadow on / off")
for (tgt, place) in corpus:
    for render in (True, False):
        on, off = paired(tgt, place, render, 1774)
        n_pairs += 1
        quiet(on[0] == off[0], f"answer differs [{place} render={render}] {tgt!r}: {on[0][:50]!r} vs {off[0][:50]!r}", diff_bad)
        quiet(on[1] == off[1], f"random state differs [{place} render={render}] {tgt!r}", diff_bad)
        quiet(on[2] == off[2], f"life_events rows differ [{place} render={render}] {tgt!r}", diff_bad)
        quiet(on[3] == off[3], f"life_ledger rows differ [{place} render={render}] {tgt!r}", diff_bad)
        n_rows_on += len(on[4]); n_rows_off += len(off[4])
        m = life._match(tgt, place)
        if m is not None and m.get("nest") and not LT.trace_object_noun(m, tgt) and LT.nest_object_noun(m, tgt) and not LT.word_present(LT._CARCASS_WORDS, tgt.lower()):
            n_expect_rows += 1
for b in diff_bad[:12]:
    print("  FAIL", b)
print(f"    {n_pairs} paired runs; shadow rows written: {n_rows_on} with the gate on, {n_rows_off} with it off; looks the gate says it would divert: {n_expect_rows}")
check(not diff_bad, f"{n_pairs} paired runs: the answer, the random state, the life_events rows and the life_ledger rows are identical with the shadow gate on and off ({len(diff_bad)} differences)")
check(n_rows_off == 0, "with the gate off nothing is logged")
check(BASE_FLOW or n_rows_on == n_expect_rows, f"with the gate on exactly the looks the gate says it would divert are logged ({n_rows_on} rows == {n_expect_rows} looks)")
check(BASE_FLOW or n_expect_rows > 200, f"... and that is a real population ({n_expect_rows} would-divert looks across the corpus)")
# the sensorium level too: the whole shore look is unchanged by the shadow gate
sl_bad: list = []
for tgt, _c in REAL_LIFE_EVENTS + REAL_NO_CREATURE:
    for render in (True, False):
        outs = []
        for enabled in (True, False):
            NGS.ENABLED = enabled and not BASE_FLOW
            outs.append(ask(tgt, "new", 77, render))
        NGS.ENABLED = not BASE_FLOW
        quiet(outs[0] == outs[1], f"sensorium.look differs with the shadow on/off [render={render}] {tgt!r}", sl_bad)
check(not sl_bad, f"sensorium.look at the shore: the 29 real looks x render on / off are identical (answer and random state) with the shadow gate on and off ({len(sl_bad)} differences)")

# -- [6] isolation ------------------------------------------------------------------------------------------------------------
print("\n[6] isolation")
check(not LIVE_WRITE_ATTEMPTS, f"the audit hook saw NO write attempt under any data/ ({len(LIVE_WRITE_ATTEMPTS)} attempts)"
                               f"{' -> ' + str(sorted({a[1] for a in LIVE_WRITE_ATTEMPTS})) if LIVE_WRITE_ATTEMPTS else ''}")
_after = {p: _md5(p) for p in _LIVE_FILES}
for p in _LIVE_FILES:
    print(f"    md5 {p.name:24s} before {_before[p][:12] or '(absent)':12s} after {_after[p][:12] or '(absent)':12s}"
          + ("" if _before[p] == _after[p] else "   <- changed while this ran (Du online?); the audit hook above is the real proof"))
check(not (_LIVE_DATA / "nest_gate_shadow.jsonl").exists() or _before[_LIVE_DATA / "nest_gate_shadow.jsonl"] != "", "no live data/nest_gate_shadow.jsonl was created by this run")
for _p in (ROOT / "core" / "shore_life.py", ROOT / "core" / "sensorium.py", ROOT / "core" / "life.py", ROOT / "core" / "life_traces.py", ROOT / "core" / "life_birds.py",
           ROOT / "core" / "nest_gate_shadow.py", Path(__file__)):
    try:
        py_compile.compile(str(_p), cfile=str(TMP / (_p.name + "c")), doraise=True)
        check(True, f"py_compile {_p.name}")
    except py_compile.PyCompileError as exc:
        check(False, f"py_compile {_p.name}: {exc}")

print(f"\n{'ALL OK' if not FAILS else f'{FAILS} FAILURE(S)'} \u2014 {CHECKS} checks \u2014 isolated store in {TMP}")
sys.exit(1 if FAILS else 0)
