"""
Regression: the shore's NEST LOOK noun reader and its answer ledger -- J-2227 / F-2917 (D-0345's place look, J-1774 build).

F-2917 (J-1796's read of the live window 2026-10-09 to 10-16) found, by replaying the window's targets through the real functions:
  (1) 'the skate egg' (2026-10-11 09:55) got noun 'egg' and the OYSTERCATCHER's nest line: _EGG_MODIFIED checked only the word AFTER 'egg'.
  (2) 'the egg-scrape' (2026-10-13 18:12) got no noun (a hyphen ends a word) and the generic shore text.
  (3) the place's nest-look answer is logged nowhere, so D-0345's defeater could only be reconstructed.
J-2227 fixes (1) with a data-derived set of other egg layers (world_substrate's egg_case kinds + the life rows' alias heads, minus the shore nest's
owner), (2) with a compound reader for egg-scrape / nest-scrape, and (3) with core/shore_nest_look_ledger.py, called once from sensorium._shore_look
right before it returns a non-empty look_nest answer.

  [0] module resolution + isolation set-up (the code under test is THIS root's; every store redirected into a temp dir)
  [1] the noun reader: the two live targets, the derivation (and that it follows the data), every J-1774 expectation unchanged, the inventory diff
  [2] through the REAL sensorium._shore_look (S.look at the shore): 'the skate egg' reaches look_nest (proved with the old reader) and now gets no nest
      line; 'the egg-scrape' gets the nest line / find-none; every other nest-class look and every inventory phrasing is byte-identical, answer and random state
  [3] the ledger: one row per look_nest hit, every field; nothing for any other look; ledger on / off / broken changes no answer or random state;
      the write fence (a non-live process pointed at data/ gets False and no file); status() counts D-0345's defeater arms
  [4] isolation: audit hook (no write attempt under any data/), live-file hashes, py_compile

  python scripts/_test_j2227_shore_nest_look_noun_and_ledger.py               # exit 0 = ALL OK
  python scripts/_test_j2227_shore_nest_look_noun_and_ledger.py --old-reader  # the pre-change reader and no ledger: must FAIL -- the test has teeth
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

OLD_READER = "--old-reader" in sys.argv
TMP = Path(tempfile.mkdtemp(prefix="j2227_shore_nest_look_"))
print("isolated store dir:", TMP)
# data/ is gitignored and never checked out into a job-run worktree, so "live" is the one real repo, never ROOT-relative.
_LIVE_DATA = Path(r"C:\Nascence") / "data"
_LIVE_FILES = [_LIVE_DATA / f for f in ("position.json", "room_state.json", "life_state.json", "life_ledger.jsonl", "life_events.jsonl", "world_traces.json",
                                        "life_flags.json", "shore_life.json", "garden_life.json", "wood_life.json", "wandering_log.jsonl",
                                        "satisfaction_log.jsonl", "satisfaction_state.json", "nest_gate_shadow.jsonl", "shore_nest_looks.jsonl")]


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

from core import shore_nest_look_ledger as SNL                 # noqa: E402
from core import world_substrate as WS                         # noqa: E402
SNL._LEDGER = TMP / "shore_nest_looks.jsonl"
_REDIRECTS.append((SNL, "_LEDGER"))
S.state["location"] = "shore"


# The reader as it stood at J-1774 (HEAD before this job), copied verbatim -- the reference for "everything else is unchanged" and for --old-reader.
_OLD_NEST_NOUN_RE = re.compile(r"(?<![a-z_-])(nests?|eggs?|scrapes?)(?![a-z_-])")
_OLD_EGG_MODIFIED = frozenset(("case", "cases", "capsule", "capsules", "sac", "sacs", "shell", "shells", "purse", "purses"))


def old_nest_look_noun(target) -> str:
    try:
        t = str(target or "").lower()
        for m in _OLD_NEST_NOUN_RE.finditer(t):
            if m.group(1).startswith("egg"):
                nxt = re.match(r"\s+([a-zāēīōū]+)", t[m.end():])
                if nxt and nxt.group(1) in _OLD_EGG_MODIFIED:
                    continue
            return m.group(1)
        return ""
    except Exception:
        return ""


NEW_NEST_LOOK_NOUN = SHL.nest_look_noun
if OLD_READER:
    print("*** --old-reader: shore_life.nest_look_noun replaced by the J-1774 reader and the ledger disabled -- the new-behaviour checks below MUST fail ***")
    SHL.nest_look_noun = old_nest_look_noun
    SNL.ENABLED = False

FAILS = 0
CHECKS = 0


def check(cond: bool, label: str) -> None:
    global FAILS, CHECKS
    CHECKS += 1
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS += 1


def quiet(cond: bool, label: str, sink: list) -> None:
    global FAILS, CHECKS
    CHECKS += 1
    if not cond:
        FAILS += 1
        sink.append(label)


NEST3 = {"ts": 1790787682.4, "eggs": 3}
LINE3 = "You pick your way up the high shingle. A scrape among the stones, and in the scrape three eggs, blotched like the stones."
NEST_MARK = "scrape among the stones, and in the scrape"
GENERIC = "You look around the shore"


def write_shore_state(nest) -> None:
    st = {"cairn": 0, "sand_writing": None, "fire": {"state": "out", "fuel": 0.0, "ts": 0.0}, "cave_finds": [], "wet_feet": 0.0, "in_cave": False,
          "seal": None, "penguins": {"burrows": 4, "seen": 0}, "oyc_nest": nest, "fog": False, "swell": 0.3, "sparkle": False, "whale_seen": 0,
          "dolphins_seen": 0, "announced": [], "skips_best": 0, "_last": 0.0, "latent_objects": [], "_storm_active": False}
    SHL._F.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")


def reset_life() -> None:
    import core.garden_knowledge as _GK
    for p in (life._F, life._LEDGER, life._EVENTS, SK._LEDGER_F, _GK._F):
        if Path(p).exists():
            Path(p).unlink()
    life._state = {}
    life._last_save = 0.0


def clear_ledger() -> None:
    if SNL._LEDGER.exists():
        SNL._LEDGER.unlink()


def ledger() -> list:
    return SNL.read_rows(0.0, SNL._LEDGER)


def ask(target: str, seed: int = 2227, render: bool = True, reader=None):
    """One look through the real sensorium.look at the shore from a clean life store, seeded. `reader` swaps shore_life.nest_look_noun for this call."""
    reset_life()
    life.RENDER = render
    S.state["location"] = "shore"
    if reader is not None:
        SHL.nest_look_noun = reader
    try:
        random.seed(seed)
        out = S.look(target)
        rng = random.getstate()
    finally:
        SHL.nest_look_noun = old_nest_look_noun if OLD_READER else NEW_NEST_LOOK_NOUN
    return out, rng


def _raise(*_a, **_k):
    raise RuntimeError("deliberately broken")


# -- [0] --------------------------------------------------------------------------------------------------------------
print("\n[0] module resolution: the code under test is THIS root's")
for _m in (core, profile, life, S, SHL, SNL, WS, NGS):
    _f = getattr(_m, "__file__", None)
    print(f"    {_m.__name__:30s} -> {_f}")
    check(_f is not None and Path(_f).resolve().is_relative_to(ROOT), f"{_m.__name__} was loaded from inside {ROOT}")
for _m, _a in _REDIRECTS:
    check(TMP in Path(str(getattr(_m, _a))).parents, f"{_m.__name__}.{_a} redirected into the temp dir")

# -- [1] the noun reader ------------------------------------------------------------------------------------------------
print("\n[1] the noun reader")
layers = SHL._other_egg_layers()
print(f"    {len(layers)} other egg layers derived from data; e.g. {sorted(layers)[:14]} ...")
kinds = [k for k, _w in WS.CLASS_PRIORS["egg_case"]["kinds"]]
check({"skate", "whelk"} <= layers, f"the egg-case kinds world_substrate mints at the shore ({kinds}) give 'skate' and 'whelk'")
own = {re.split(r"[\s-]+", a.lower())[-1] for r in life.rows().values() if r.get("nest") and "shore" in (r.get("places") or {}) for a in r.get("aliases") or ()}
check(bool(own) and not (own & layers), f"the shore nest owner's own words ({sorted(own)}) are NOT other layers")
check({"gull", "gannet", "tern", "penguin", "blackbird", "pigeon", "crab", "skink"} <= layers, "the life rows' alias heads are layers (gull, gannet, tern, penguin, blackbird, pigeon, crab, skink ...)")
GENERIC_WORDS = {"the", "bird", "stone", "stones", "shingle", "three", "two", "speckled", "small", "scattering", "nesting", "and", "its", "blotched", "an", "a"}
check(not (GENERIC_WORDS & layers), f"no article / generic word Du used before 'eggs' is a layer ({sorted(GENERIC_WORDS & layers)})")
# the two live targets
check(SHL.nest_look_noun("the skate egg") == "", "'the skate egg' (2026-10-11 09:55) names no nest noun (another thing's egg)")
check(SHL.nest_look_noun("the egg-scrape") == "scrape", "'the egg-scrape' (2026-10-13 18:12) reads as the scrape")
OTHER_EGG = ["the skate egg", "the skate eggs", "the skate's egg", "a skate’s egg", "the skates egg", "the skates' eggs", "the whelk eggs", "the whelk's eggs",
             "the gull egg", "the gulls' eggs", "the tern eggs", "the penguin's egg", "the blackbird egg", "the crab eggs", "THE SKATE EGG"]
bad = [t for t in OTHER_EGG if SHL.nest_look_noun(t) != ""]
check(not bad, f"{len(OTHER_EGG)} looks at another layer's egg(s) (plain, possessive, plural, curly apostrophe, upper case) name no nest noun: {bad}")
COMPOUND = {"the egg-scrape": "scrape", "the eggs-scrape": "scrape", "the nest-scrape": "scrape", "the egg-scrapes": "scrapes", "an egg-scrape in the shingle": "scrape",
            "The Egg-Scrape": "scrape", "the eggs in the egg-scrape": "eggs", "the egg-scrape and the eggs": "scrape"}
bad = {t: SHL.nest_look_noun(t) for t, w in COMPOUND.items() if SHL.nest_look_noun(t) != w}
check(not bad, f"{len(COMPOUND)} egg-scrape / nest-scrape compounds read as the scrape (the first nest noun in the look wins, as before): {bad}")
STILL_NOT = ["the egg-case", "the egg_case", "a skate's egg case", "the skate's egg-case", "the skate egg-case", "the egg-cases", "the nest-egg", "the egg-nest",
             "the scrape-marks", "the eggshell", "the egg sac", "the mermaid's egg purse", "the-nest", "the egg_scrape"]
bad = [t for t in STILL_NOT if SHL.nest_look_noun(t) != ""]
check(not bad, f"{len(STILL_NOT)} still not nest looks (egg-case / egg_case / skate egg-case / nest-egg / egg-nest / scrape-marks / egg_scrape ...): {bad}")
KEEP = {"the eggs": "eggs", "the oystercatcher's eggs": "eggs", "the oystercatcher eggs": "eggs", "the oystercatcher and eggs": "eggs", "the tōrea eggs": "eggs",
        "the speckled eggs": "eggs", "the three eggs": "eggs", "the bird's eggs": "eggs", "the stone eggs": "eggs", "the scattering eggs": "eggs",
        "the eggs on the shingle": "eggs", "the nest scrape": "nest", "the eggs and the egg case": "eggs", "the egg case and the nest": "nest"}
bad = {t: SHL.nest_look_noun(t) for t, w in KEEP.items() if SHL.nest_look_noun(t) != w}
check(not bad, f"{len(KEEP)} looks at the oystercatcher's own eggs (the owner named, adjectives, the bird, conjunctions) keep their noun: {bad}")
# follows the data
_saved = WS.CLASS_PRIORS["egg_case"]["kinds"]
try:
    WS.CLASS_PRIORS["egg_case"]["kinds"] = list(_saved) + [("shark_purse", 0.1)]
    check(SHL.nest_look_noun("the shark egg") == "", "the layer set follows the data: a new egg_case kind 'shark_purse' makes 'the shark egg' another thing's egg")
finally:
    WS.CLASS_PRIORS["egg_case"]["kinds"] = _saved
check(SHL.nest_look_noun("the shark egg") == "egg", "... and without it 'the shark egg' is read as before (no hand list behind the data)")
# fail-open: a source that cannot be read contributes nothing
_saved_rows = life.rows
try:
    life.rows = _raise
    check(SHL.nest_look_noun("the skate egg") == "" and SHL.nest_look_noun("the eggs") == "eggs",
          "the life rows unreadable: the substrate layers still apply, plain looks unchanged, nothing raises")
finally:
    life.rows = _saved_rows
st = random.getstate()
for t in OTHER_EGG + list(COMPOUND) + STILL_NOT + list(KEEP):
    SHL.nest_look_noun(t)
check(random.getstate() == st, "the reader draws no random number")
# every phrasing in the observe inventory: new == old except the two families this job changes
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
check(len(INV) == 1526, f"the observe inventory yields its 1,526 phrasings ({len(INV)})")
F2917_WINDOW = ["the eggs", "the nest", "the eggs and stones", "the eggs on the shingle", "the bird and its nest", "the bird and eggs", "the bird and its eggs",
                "the nest scrape", "the scattering eggs", "the scrape", "the skate egg", "the egg-scrape", "the skate's egg-case", "the skate egg-case"]
diff = {t: (old_nest_look_noun(t), SHL.nest_look_noun(t)) for t in sorted(set(INV + F2917_WINDOW)) if old_nest_look_noun(t) != SHL.nest_look_noun(t)}
print("    reader changes over the inventory + F-2917's window targets:", diff)
check(set(diff) == {"the skate egg", "the egg-scrape"},
      f"over the 1,526 inventory phrasings + F-2917's 14 window targets the reader changes EXACTLY 'the skate egg' and 'the egg-scrape' ({sorted(diff)})")

# -- [2] through the real sensorium look at the shore -----------------------------------------------------------------
print("\n[2] through the REAL sensorium._shore_look (S.look at the shore)")
write_shore_state(NEST3)
clear_ledger()
old_skate = ask("the skate egg", reader=old_nest_look_noun)[0]
print("    'the skate egg', J-1774 reader :", old_skate)
check(old_skate == LINE3, "PREMISE (F-2917): with the J-1774 reader 'the skate egg' reaches look_nest through the real _shore_look (no earlier branch claims it) and "
                          "gets the oystercatcher's nest line")
new_skate = ask("the skate egg")[0]
print("    'the skate egg', now           :", new_skate)
check(NEST_MARK not in new_skate, "'the skate egg' no longer gets the oystercatcher's nest line")
check(new_skate.startswith(GENERIC) or new_skate.startswith("You look at "), "... it falls through to the shore's own text, as any look at an unminted thing does")
old_scr = ask("the egg-scrape", reader=old_nest_look_noun)[0]
new_scr = ask("the egg-scrape")[0]
print("    'the egg-scrape', J-1774 reader:", old_scr[:90])
print("    'the egg-scrape', now          :", new_scr)
check(old_scr.startswith(GENERIC), "PREMISE (F-2917): with the J-1774 reader 'the egg-scrape' got the generic shore text")
check(new_scr == LINE3, "'the egg-scrape' now gets the nest line (nest eggs=3)")
write_shore_state(None)
check(ask("the egg-scrape")[0] == "You look for a scrape and find none.", "'the egg-scrape' with no nest: 'You look for a scrape and find none.'")
check(ask("the nest-scrape")[0] == "You look for a scrape and find none.", "'the nest-scrape' with no nest: 'You look for a scrape and find none.'")
_sk = ask("the skate egg")[0]
check(NEST_MARK not in _sk and "find none" not in _sk, "'the skate egg' with no nest: no nest line and no find-none (it is not a look at the nest)")
# byte-identity: every inventory phrasing + the window targets (but the two changed ones and the stateful driftwood branch), both nest states, render on/off
DRIFTWOOD_EXACT = ("driftwood", "log", "fir", "wood")
same_bad: list = []
n_same = 0
targets = [t for t in sorted(set(INV + F2917_WINDOW)) if t not in ("the skate egg", "the egg-scrape") and t not in DRIFTWOOD_EXACT]
for nest in (NEST3, None):
    write_shore_state(nest)
    for render in (True, False):
        for t in targets:
            a = ask(t, render=render)
            b = ask(t, render=render, reader=old_nest_look_noun)
            quiet(a == b, f"[nest={bool(nest)} render={render}] {t!r}: {a[0][:60]!r} vs {b[0][:60]!r}", same_bad)
            n_same += 1
for b in same_bad[:10]:
    print("  FAIL", b)
check(not same_bad, f"{n_same} looks ({len(targets)} targets x 2 nest states x render on/off): answer AND random state identical to the J-1774 reader ({len(same_bad)} differ)")

# -- [3] the ledger ---------------------------------------------------------------------------------------------------
print("\n[3] the ledger (core/shore_nest_look_ledger.py)")
write_shore_state(NEST3)
clear_ledger()
out = ask("the eggs on the shingle")[0]
rows = ledger()
print("    row:", rows[-1] if rows else None)
check(len(rows) == 1, f"one look at the eggs (nest eggs=3) -> one ledger row ({len(rows)})")
if rows:
    r = rows[0]
    check(set(r) == {"ts", "kind", "target", "noun", "nest_exists", "eggs", "line", "consistent"}, f"the row carries exactly ts, kind, target, noun, nest_exists, eggs, line, consistent ({sorted(r)})")
    check(r["kind"] == "nest_look" and r["target"] == "the eggs on the shingle" and r["noun"] == "eggs" and r["nest_exists"] is True and r["eggs"] == 3
          and r["line"] == out == LINE3 and r["consistent"] is True and abs(r["ts"] - time.time()) < 120,
          "fields: kind nest_look, the target, noun eggs, nest_exists true, eggs 3, line == the answer returned, consistent true, ts now")
write_shore_state(None)
clear_ledger()
out = ask("the nest")[0]
rows = ledger()
check(len(rows) == 1 and rows[0]["nest_exists"] is False and rows[0]["eggs"] is None and rows[0]["line"] == out == "You look for a nest and find none."
      and rows[0]["consistent"] is True and rows[0]["noun"] == "nest", f"no nest: 'the nest' -> one row, nest_exists false, eggs None, the find-none line ({rows})")
write_shore_state({"ts": 1.0, "eggs": "3"})
clear_ledger()
out = ask("the eggs")[0]
rows = ledger()
check(len(rows) == 1 and rows[0]["nest_exists"] is True and rows[0]["eggs"] is None and "in the scrape eggs," in out,
      "a nest with a non-int count: nest_exists true, eggs None (never a wrong number)")
write_shore_state(NEST3)
clear_ledger()
NOT_LOGGED = ["the skate egg", "the oystercatcher and eggs", "the oystercatcher's scrape", "the egg case", "the sand", "the cave", "the tide", "the shingle",
              "the screaming bird", "the oystercatcher", "the sea", "the egg-case"]
for t in NOT_LOGGED:
    ask(t)
check(ledger() == [], f"{len(NOT_LOGGED)} looks that look_nest does not answer (another egg, the bird named, egg case, other places on the shore) write no row ({len(ledger())})")
# count: every nest-class look in the inventory that look_nest answers writes exactly one row
clear_ledger()
hits = 0
for t in [t for t in INV if SHL.nest_look_noun(t)] + ["the egg-scrape"]:
    o = ask(t)[0]
    hits += (NEST_MARK in o) or o.endswith("and find none.")
check(len(ledger()) == hits and hits > 0, f"inventory nest looks answered by look_nest: {hits}; ledger rows: {len(ledger())} (one per hit)")
check(bool(ledger()) and all(r.get("consistent") is True for r in ledger()), "every row is consistent (the re-read reproduces the answer)")
# on / off / broken change nothing
onoff_bad: list = []
sample = [t for t in INV if SHL.nest_look_noun(t)] + ["the egg-scrape", "the skate egg", "the eggs", "the nest", "the sand", "the cave", "the oystercatcher and eggs"]
_real_build, _real_record = SNL.build_row, SNL.record
for nest in (NEST3, None):
    write_shore_state(nest)
    for t in sample:
        SNL.ENABLED = True
        a = ask(t)
        SNL.ENABLED = False
        b = ask(t)
        SNL.ENABLED = True
        SNL.build_row = _raise
        c = ask(t)
        SNL.build_row = _real_build
        SNL.record = _raise
        d = ask(t)
        SNL.record = _real_record
        quiet(a == b == c == d, f"[nest={bool(nest)}] {t!r}: ledger on/off/broken/raising changes the answer or random state", onoff_bad)
SNL.ENABLED = not OLD_READER
check(not onoff_bad, f"{len(sample) * 2} looks: the answer and the random state are identical with the ledger on, off, broken (build_row raises) and raising (record raises) ({onoff_bad[:3]})")
# the write fence
_red = SNL._LEDGER
_was = SNL.ENABLED
SNL.ENABLED = True
for target_path in (ROOT / "data" / "shore_nest_looks.jsonl", _LIVE_DATA / "shore_nest_looks.jsonl"):
    SNL._LEDGER = target_path
    _exists = target_path.exists()
    ok = SNL.record("the eggs", LINE3)
    check(ok is False and target_path.exists() == _exists, f"write fence: a non-live process pointed at {target_path} gets False and no file")
SNL._LEDGER = _red
SNL.ENABLED = _was
try:
    profile.guard_path(_LIVE_DATA / "shore_nest_looks.jsonl")
    check(False, "profile.guard_path refuses the live data/shore_nest_looks.jsonl for a non-live process")
except profile.NonLiveWriteError:
    check(True, "profile.guard_path refuses the live data/shore_nest_looks.jsonl for a non-live process (D-0179)")
check(SNL.record("the eggs", "") is False, "an empty answer is never logged")
# status(): D-0345's defeater arms counted directly
fake = TMP / "status_fixture.jsonl"
fake.write_text("\n".join(json.dumps(x) for x in [
    {"ts": 1.0, "noun": "eggs", "nest_exists": True, "line": LINE3, "consistent": True},
    {"ts": 2.0, "noun": "nest", "nest_exists": False, "line": "You look for a nest and find none.", "consistent": True},
    {"ts": 3.0, "noun": "eggs", "nest_exists": False, "line": LINE3, "consistent": False},
    {"ts": 4.0, "noun": "scrape", "nest_exists": True, "line": "You look for a scrape and find none.", "consistent": False}]) + "\n{torn", encoding="utf-8")
s = SNL.status(fake)
print("    status():", s)
check(s["rows"] == 4 and s["nest_stood"] == 2 and s["nest_absent"] == 2 and s["nest_line_while_absent"] == 1 and s["find_none_while_stood"] == 1 and s["inconsistent"] == 2
      and s["by_noun"] == {"eggs": 2, "nest": 1, "scrape": 1} and s["first_ts"] == 1.0 and s["last_ts"] == 4.0,
      "status() counts rows, nest stood/absent, the two defeater arms (nest line while absent, find-none while stood) and inconsistent rows; a torn line is skipped")
check(SNL.status(TMP / "missing.jsonl")["rows"] == 0, "status() of a missing ledger is 0 rows, no exception")

# -- [4] isolation ------------------------------------------------------------------------------------------------------
print("\n[4] isolation")
check(not LIVE_WRITE_ATTEMPTS, f"the audit hook saw NO write attempt under any data/ ({len(LIVE_WRITE_ATTEMPTS)} attempts)"
                               f"{' -> ' + str(sorted({a[1] for a in LIVE_WRITE_ATTEMPTS})) if LIVE_WRITE_ATTEMPTS else ''}")
_after = {p: _md5(p) for p in _LIVE_FILES}
for p in _LIVE_FILES:
    print(f"    md5 {p.name:24s} before {_before[p][:12] or '(absent)':12s} after {_after[p][:12] or '(absent)':12s}"
          + ("" if _before[p] == _after[p] else "   <- changed while this ran (another process?); the audit hook above is the real proof"))
check(_before[_LIVE_DATA / "shore_nest_looks.jsonl"] == "" and not (_LIVE_DATA / "shore_nest_looks.jsonl").exists(),
      "no live data/shore_nest_looks.jsonl exists (this run created none)")
for _p in (ROOT / "core" / "shore_life.py", ROOT / "core" / "sensorium.py", ROOT / "core" / "shore_nest_look_ledger.py", Path(__file__)):
    try:
        py_compile.compile(str(_p), cfile=str(TMP / (_p.name + "c")), doraise=True)
        check(True, f"py_compile {_p.name}")
    except py_compile.PyCompileError as exc:
        check(False, f"py_compile {_p.name}: {exc}")

print(f"\n{'ALL OK' if not FAILS else f'{FAILS} FAILURE(S)'} — {CHECKS} checks — isolated store in {TMP}")
sys.exit(1 if FAILS else 0)
