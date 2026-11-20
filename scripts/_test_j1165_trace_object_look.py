"""
Regression: a Living World look at a creature's TRACE OBJECT is answered by the trace, never by the living
creature's visibility roll (J-1165 / F-1617 -- the generalisation of J-0887's dead-thing routing to every trace).

The bug (live: life_events.jsonl 2026-09-12 09:28:30 and 2026-09-17 08:28:42, the second AFTER J-0887 was live):
the engine mints a trace ('a burrow in the cliff bank', 'a gannet feather, white and stiff'), Du looks at it -- "the
kingfisher's burrow", "the gannet feather" -- and because the target also carries the creature's alias, life._match()
resolved it to the LIVING row and its visibility roll answered ("The dry rattle came from the wire, and the wire is
empty." / "Nothing shows itself; whatever is there keeps still."), 82 s and 3 min 16 s after the engine placed the thing.

The fix (core/life.py look_answer + core/life_traces.py trace_object_noun / trace_object_look): a target that names
the matched row's OWN trace object -- a head noun DERIVED from that row's `traces` phrases, in the shape "the gannet
feather" / "the kingfisher's burrow" / "the feather of the gannet", and not a noun the row's own lines or the bed
already speak of -- is answered by the creature's still-active trace at the place, else by an honest 'no such x
here', never by the living row (and no ledger write: a look at a feather is not a sighting of the bird).

  [0] module resolution + isolation set-up (F-1285: the code under test is THIS root's, not the shared tree's)
  [1] the noun set is DERIVED from the rows' own traces (a synthetic row proves it; no typed-in noun list)
  [2] the gate: creature-word versus trace-phrase targets for EVERY row family that has traces, the number policy,
      and the ambiguous cases ('the gull', 'feathers', ...) with how each was decided
  [3] behaviour through look_answer: the two real incidents replayed (old = the logged wrong line, new = the trace),
      the honest fallback, another creature's trace never answers, shadow mode, fail-open, the re-raise
  [4] the controls are byte-identical: whole-corpus differential, gate ON vs gate OFF (OFF == the pre-change flow,
      because the new block is inert whenever the gate says ''): the observe-inventory phrasings, the real live
      targets, and a synthetic sweep -- outputs AND event rows differ exactly where the gate says trace object
  [5] REAL rows replayed read-only: every kind=answer/would_answer row of data/life_events.jsonl (frozen at the
      CUTOFF this test was written against) through the gate -- exactly the two wrong rows are diverted; and every
      look/observe object in data/hands_trace.jsonl (append-only, NOT frozen) -- a RULE, not a frozen list (J-1725):
      every diverted pair is a trace-object look at a creature that left that trace and is answered from that trace,
      with the two original pairs kept as a floor
  [6] isolation: audit hook (no write attempt under any data/), canary marker, live-file hashes

ISOLATION. Every store look_answer can reach is redirected into a temp dir before anything can write (the S-0016 /
test-isolation rule; same convention as scripts/life_smoke.py). The live C:\\Nascence\\data files are md5-hashed before
and after AND a Python audit hook records any attempt by THIS process to open-for-write / rename / remove anything
under C:\\Nascence\\data or <root>\\data: with Du ONLINE the live files legitimately change on their own between two
hashes, so a hash comparison alone cannot prove a negative -- the audit hook does (same as
scripts/_test_journey_decline_through_move.py). The live files are only ever READ (section [5]).

  python scripts/_test_j1165_trace_object_look.py                    # exit 0 = ALL OK
  python scripts/_test_j1165_trace_object_look.py --full-canary      # + scan every data/*.json* for the marker
"""
from __future__ import annotations

import collections
import copy
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

TMP = Path(tempfile.mkdtemp(prefix="j1165_trace_object_look_"))
print("isolated store dir:", TMP)
MARKER = f"j1165_marker_{os.getpid()}"
# data/ is gitignored and never checked out into a job-run worktree, so "live" is the one real repo, never ROOT-relative.
_LIVE_DATA = Path(r"C:\Nascence") / "data"
_LIVE_FILES = [_LIVE_DATA / f for f in ("position.json", "room_state.json", "life_state.json", "life_ledger.jsonl",
                                        "life_events.jsonl", "world_traces.json", "life_flags.json")]


def _md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest() if p.exists() else ""


_before = {p: _md5(p) for p in _LIVE_FILES}

# ── write audit: this process must never attempt a write under a live data dir ──────────────────────────────────
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

# ── redirect every store look_answer / traces_pass can reach BEFORE anything can write ───────────────────────────
import core                                                    # noqa: E402
from core import profile                                       # noqa: E402
from core import life, life_traces as LT, world_traces as WT   # noqa: E402
from core import life_birds, life_mammals, garden_insects, garden_soil   # noqa: E402
from core import sensorium as S                                # noqa: E402
from core import locomotion as L                               # noqa: E402
from core import sound_knowledge as SK                         # noqa: E402

life._F, life._LEDGER, life._EVENTS, life._DATA = TMP / "life_state.json", TMP / "life_ledger.jsonl", TMP / "life_events.jsonl", TMP
life._FLAGS_F = TMP / "life_flags.json"                        # read-only in life.py; redirected so the result never depends on the live flag file
WT._TRACES_F = TMP / "world_traces.json"
S._STATE_F = TMP / "room_state.json"
L._POS_F = TMP / "position.json"
SK._LEDGER_F = TMP / "sound_knowledge.json"
_REDIRECTS = [(life, "_F"), (life, "_LEDGER"), (life, "_EVENTS"), (life, "_FLAGS_F"), (WT, "_TRACES_F"), (S, "_STATE_F"),
              (L, "_POS_F"), (SK, "_LEDGER_F")]
# A roll-path look reaches light.field_at() -> study_life.lamp_on() -> provisions.sync() (the study), and the garden / shore / wood
# modules -- the SAME vetted redirect list scripts/life_smoke.py carries (J-0743 / J-0783 / J-0920): each of these is guard_path()-fenced,
# so an un-redirected one would refuse loudly, but redirecting them is what makes the isolation TRUE rather than merely enforced.
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
_WDR.perceive = lambda *a, **k: None
_AM.record = lambda *a, **k: None
life.note_deed(MARKER, "garden")                               # the marker, through the engine's own write path (lands in TMP)
S.state.clear()
S.state.update({"weather": "clear", "wind": "breeze", "fire": "out", "fire_fuel": 0.0, "last_event": 0, "location": "shore",
                "garden": S._fresh_garden()})

FAILS = 0
CHECKS = 0


def check(cond: bool, label: str) -> None:
    global FAILS, CHECKS
    CHECKS += 1
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS += 1


def quiet(cond: bool, label: str, sink: list) -> None:
    """A bulk check: count it, print only failures (the table sections run thousands)."""
    global FAILS, CHECKS
    CHECKS += 1
    if not cond:
        FAILS += 1
        sink.append(label)


def at(month: int, hour: int, day: int = 15, year: int = 2026) -> float:
    return time.mktime((year, month, day, hour, 0, 0, 0, 0, -1))


# ── [0] module resolution (F-1285) ──────────────────────────────────────────────────────────────────────────────
print("\n[0] module resolution: the code under test is THIS root's, not the shared tree's")
print("    sys.path[0] =", sys.path[0])
for _m in (core, profile, life, LT, WT, life_birds, life_mammals, garden_insects, garden_soil, S, L, SK):
    _f = getattr(_m, "__file__", None)
    print(f"    {_m.__name__:22s} -> {_f}")
    check(_f is not None and Path(_f).resolve().is_relative_to(ROOT), f"{_m.__name__} was loaded from inside {ROOT}")
check(hasattr(LT, "trace_object_noun") and hasattr(LT, "trace_object_look") and hasattr(life, "_no_trace_line"),
      "the loaded copy carries the J-1165 code (not a stale/shared copy)")
for _m, _a in _REDIRECTS:
    check(TMP in Path(str(getattr(_m, _a))).parents, f"{_m.__name__}.{_a} redirected into the temp dir")

ROWS = life.rows()
TRACE_ROWS = {k: r for k, r in ROWS.items() if r.get("traces") and not r.get("external")}
print(f"    {len(ROWS)} rows registered, {len(TRACE_ROWS)} population rows carry `traces`")

# ── [1] the noun set is DERIVED ─────────────────────────────────────────────────────────────────────────────────
print("\n[1] the trace-noun set is derived from the rows' own `traces` phrases (no typed-in vocabulary)")
HEADS = {k: {LT.trace_head(p) for p in r["traces"]} - {""} for k, r in TRACE_ROWS.items()}
USABLE = {k: LT.trace_nouns(r) for k, r in TRACE_ROWS.items()}
for k in sorted(TRACE_ROWS):
    print(f"    {k:18s} heads {sorted(HEADS[k])!s:52s} gate-active {sorted(USABLE[k])}")
_expect_head = {"a burrow in the cliff bank": "burrow", "a gannet feather, white and stiff": "feather",
                "three-toed prints on the wet sand": "prints", "big prints": "prints", "a dropped shell": "shell",
                "broken snail shells at the anvil stone": "shells", "a wet shape's drag-mark on the shelf": "drag-mark",
                "a split brown cicada shell clinging to the fence post": "shell", "a mud nest under the eaves": "nest",
                "a web strung between two rosemary stems, holding the last of the dew": "web", "white-streaked rock": "rock",
                "a thin dark road along the bed's wooden edge": "road", "a fishy smell at the burrow mouth": "smell",
                "a scatter of feathers on the sand": "feathers", "": ""}
for ph, hd in _expect_head.items():
    check(LT.trace_head(ph) == hd, f"trace_head({ph!r}) == {hd!r}")
# every real head is a plain lowercase word, never a function word (the grammatical sets stay separate from the derived nouns)
_all_heads = set().union(*HEADS.values())
check(not (_all_heads & (LT._NP_END | LT._CLAUSE_JOIN | LT._ARTICLES)), "no derived trace noun is a function word")
check(all(re.fullmatch(r"[a-zāēīōū]+(?:-[a-zāēīōū]+)*", h) for h in _all_heads), "every derived noun is a plain word")
# the derivation follows the DATA: a synthetic row with an invented phrase yields the invented noun (nothing to type in)
_syn = life.row("zz_j1165_probe", aliases=("zzyzx",), places={"garden": ["hedge"]}, traces=("a zzyzx cairn on the ridge",))
check(LT.trace_nouns(_syn) == {"cairn"} and LT.trace_object_noun(_syn, "the zzyzx cairn") == "cairn", "an invented 'cairn' phrase yields the noun 'cairn'")
_syn2 = life.row("zz_j1165_probe", aliases=("zzyzx",), places={"garden": ["hedge"]}, traces=("a zzyzx beacon in the dune",))
check(LT.trace_nouns(_syn2) == {"beacon"} and LT.trace_object_noun(_syn2, "the zzyzx cairn") == "", "edit the phrase, the noun follows ('beacon', no longer 'cairn')")
_syn3 = life.row("zz_j1165_probe", aliases=("zzyzx",), places={"garden": ["hedge", "cairn"]}, traces=("a zzyzx cairn on the ridge",))
check(LT.trace_nouns(_syn3) == set(), "a noun the row's own place spots already name is the row's own subject -> not a trace noun")
_syn4 = life.row("zz_j1165_probe", aliases=("zzyzx",), places={"garden": ["hedge"]}, traces=("a zzyzx cairn on the ridge",),
                 hidden={"feature": {"day": "a zzyzx sits by its cairn"}})
check(LT.trace_nouns(_syn4) == set(), "a noun the row's own look lines already speak of is the row's own subject -> not a trace noun")
_consts = set()
for _fn in (LT.trace_head, LT.trace_nouns, LT._row_speaks, LT.trace_object_noun, LT.trace_object_look):
    _consts |= {c for c in _fn.__code__.co_consts if isinstance(c, str)}
_consts |= set(LT._ARTICLES) | set(LT._NP_END) | set(LT._CLAUSE_JOIN)
check(not (_consts & _all_heads), f"none of the {len(_all_heads)} derived nouns appears as a literal in the new code or its word sets")
# the concrete design decisions, asserted where a wrong call would matter
check(USABLE["gannet"] == {"feather"} and USABLE["kingfisher"] == {"burrow"}, "gannet -> feather, kingfisher -> burrow (the two live wrong answers)")
check({"prints", "feather", "shell"} <= USABLE["gulls"] and USABLE["karoro"] == {"prints"} and {"prints", "shells"} <= USABLE["oystercatcher"],
      "gulls / karoro / oystercatcher: prints, feather, shell(s)")
for _k, _h in (("shag", "rock"), ("garden_spider", "web"), ("ants", "road"), ("slugs", "trail"), ("crabs", "shell"),
               ("song_thrush", "shells"), ("korora", "burrow"), ("blackbird", "leaves"), ("aphids", "tips"), ("borer_beetle", "dust")):
    check(_h in HEADS[_k] and _h not in USABLE[_k], f"{_k}: '{_h}' is derived but left to the row (its own lines / spots / alias / the bed already speak of it)")

# ── [2] the gate: creature-word vs trace-phrase targets, every row family ───────────────────────────────────────
print("\n[2] the gate (life_traces.trace_object_noun): creature looks stay creature looks, trace objects are diverted")
fails2: list = []
n_trace = n_creature = n_left = n_number = 0
for k, r in sorted(TRACE_ROWS.items()):
    aliases = [a for a in (r.get("aliases") or ()) if a]
    for a in aliases:
        for n in sorted(USABLE[k]):
            trace_forms = [f"the {a} {n}", f"the {a}'s {n}", f"the {a}'s big {n}", f"the {n} of the {a}", f"{a} {n} on the tideline"]
            if a.endswith("s"):
                trace_forms.append(f"the {a}' {n}")
            for t in trace_forms:
                n_trace += 1
                quiet(LT.trace_object_noun(r, t) == n, f"[{k}] TRACE {t!r} -> {LT.trace_object_noun(r, t)!r}, wanted {n!r}", fails2)
            creature_forms = [f"the {a}", f"the {a} bathing", f"the {a} on the rocks", f"the {a} and the tide", f"the {a} with a {n}",
                              f"the {a} dropping a {n}", f"the {a} and its {n}", f"the {a} at the {n}", f"the {a} near the {n}",
                              f"the {a} hunting for {n}", f"the {a}, the {n}", f"the screaming {a}", f"the {a} over the water", f"the {a} in the {n}"]
            for t in creature_forms:
                n_creature += 1
                quiet(LT.trace_object_noun(r, t) == "", f"[{k}] CREATURE {t!r} -> {LT.trace_object_noun(r, t)!r}, wanted ''", fails2)
            other = n + "s" if not n.endswith("s") else n[:-1]          # the number the engine did NOT write
            if other not in USABLE[k]:
                n_number += 1
                quiet(LT.trace_object_noun(r, f"the {a}'s {other}") == "", f"[{k}] NUMBER 'the {a}'s {other}' must not be a trace look", fails2)
        for h in sorted(HEADS[k] - USABLE[k]):
            n_left += 1
            quiet(LT.trace_object_noun(r, f"the {a}'s {h}") == "", f"[{k}] LEFT-TO-ROW 'the {a}'s {h}' must stay with the row", fails2)
        quiet(LT.trace_object_noun(r, f"the {a}") == "", f"[{k}] bare creature word {a!r}", fails2)
print(f"    {n_trace} trace-object shapes diverted, {n_creature} creature shapes left alone, {n_number} number variants left alone, "
      f"{n_left} row-owned nouns left alone, across {len(TRACE_ROWS)} rows / every alias")
for m_ in fails2[:15]:
    print("    !!", m_)
check(not fails2, f"the gate table is clean ({len(fails2)} failures)")

print("    the ambiguous cases, and how each was decided:")
AMBIG = [
    # (target, place, expected noun or '', decision)
    ("the gull", "shore", "", "a creature word alone: no trace noun in the target -> creature look, the visibility roll"),
    ("the gulls", "shore", "", "same, plural alias"),
    ("the gull bathing", "shore", "", "real live target; participle, no trace noun"),
    ("the gull's feather", "shore", "feather", "a single feather in the possessive: the engine's own 'a white feather' -> trace object"),
    ("the gull feather", "shore", "feather", "attributive shape, same as the live 'the gannet feather' -> trace object"),
    ("the gull's feathers", "shore", "", "PLURAL 'feathers' is plumage (real live look: \"the shag's feathers\"); the engine writes 'feather' -> creature look"),
    ("the gull with a feather", "shore", "", "'with' ends the noun phrase: a bird carrying a feather is a creature look"),
    ("the gull dropping a shell", "shore", "", "participle 'dropping' ends the noun phrase: the bird doing something -> creature look"),
    ("the gull and a white feather", "shore", "", "a coordination names two things; the creature is one of them -> left with the roll (as today)"),
    ("the gull's prints", "shore", "prints", "the engine's own 'prints' -> trace object"),
    ("the gulls' prints", "shore", "prints", "plural possessive of the alias -> trace object"),
    ("the gull's print", "shore", "", "singular 'print' is not what the engine wrote -> unchanged (documented narrowness)"),
    ("feathers", "shore", None, "no creature alias at all: life._match() finds no row, look_answer returns '' as before (the place look answers)"),
    ("the feather", "shore", None, "same: never reaches a living row, so never this bug"),
    ("the shag's feathers", "shore", "", "REAL live look; the shag leaves no feather trace and 'feathers' is plumage -> creature look"),
    ("the shag on the rock", "shore", "", "the shag's own trace noun 'rock' is the row's designed subject AND follows 'on' -> creature look"),
    ("the shag's white-streaked rock", "shore", "", "the row's own lines/spots speak of 'rock' -> left to the row (the one residual of this class, documented)"),
    ("the kingfisher dropping", "garden", "", "REAL live look: 'dropping' is a participle of the bird, and not this row's noun"),
    ("the kingfisher's burrow", "shore", "burrow", "REAL live wrong answer (09-12 09:28:30) -> trace object"),
    ("the gannet feather", "shore", "feather", "REAL live wrong answer (09-17 08:28:42) -> trace object"),
    ("the gannet", "shore", "", "control from the briefing: creature look"),
    ("the oystercatcher and eggs", "shore", "", "control from the briefing (4+ live rows): 'eggs' is no trace noun of this row; the nest adapter is a separate question"),
    ("the oystercatcher and its nest", "shore", "", "REAL live look: 'nest' is not the oystercatcher's trace noun (a swallow's)"),
    ("the oystercatcher hunting near the scrape", "shore", "", "REAL live look: not its noun, and 'hunting'/'near' end the phrase"),
    ("the oystercatcher opening shells", "shore", "", "participle 'opening' ends the phrase: the bird at work -> creature look"),
    ("the oystercatcher's opened shells", "shore", "shells", "the engine's own 'opened shells' -> trace object"),
    ("the hermit crab's shell", "shore", "", "the crab's own lines already speak of its shell (it wears one) -> creature look"),
    ("the spider's web", "garden", "", "'web' is an ALIAS of the spider row: the row's designed subject -> unchanged"),
    ("the ants' road", "garden", "", "the ants' own feature line is the road -> unchanged"),
    ("the blackbird in the leaves", "garden", "", "'leaves' is a plant word and follows 'in' -> creature look"),
    ("the dead gannet feather", "shore", "feather", "gate alone says trace object, but look_answer's carcass block (a dead word) takes it first -- see [3]"),
    ("the kingfisher’s burrow", "shore", "burrow", "a curly apostrophe is the same possessive"),
    ("The  Gannet   FEATHER", "shore", "feather", "case and spacing do not matter"),
    ("the gannet's old, worn feather", "shore", "", "a comma ends the noun phrase (conservative: adjectives only, no list punctuation)"),
    ("the gannet's wing feather", "shore", "feather", "'wing' is an ordinary adjective, not a participle (participles are 5+ letters)"),
    ("the gannet's shining feather", "shore", "", "'shining' IS a participle: ends the phrase, left with the roll (conservative)"),
]
_g0 = ROWS["gannet"]
check(all(LT.trace_object_noun(_g0, t) == "" for t in (None, "", " ", "the", "'s", "the gannet's", "feather", "the gannet ", "the gannet.", "the gannet, feather")),
      "odd inputs (None, '', bare possessives, fragments) never raise and never divert")
for tgt, place, want, why in AMBIG:
    m = life._match(tgt, place)
    got = None if m is None else LT.trace_object_noun(m, tgt)
    check(got == want, f"{tgt!r:44s} @{place:6s} -> {got!r:10s} | {why}")

# ── helpers for the behavioural sections ────────────────────────────────────────────────────────────────────────
_REAL_GATE = LT.trace_object_noun


def gate_off() -> None:
    """The pre-change flow: the new block in look_answer only acts when the gate names a noun."""
    LT.trace_object_noun = lambda r, t: ""


def gate_on() -> None:
    LT.trace_object_noun = _REAL_GATE


def reset_traces() -> None:
    WT._traces_cache = {}
    WT._last_load = 0.0
    WT._TRACES_F.write_text("{}", encoding="utf-8")


_minted = [0]


def mint(key: str, place: str, detail: str, clarity: float = 0.8) -> dict:
    """A creature trace exactly as life_traces.traces_pass writes one (type '<key>_trace', detail, creature)."""
    _minted[0] += 1
    spots = (ROWS[key].get("places") or {}).get(place, [])
    tid = f"{key}_{place}_{int(time.time())}_{_minted[0]}"
    WT.create_trace(tid, f"{key}_trace", place, LT._pos(place, spots), clarity=clarity, cause=key)
    tr = WT._load_traces()[tid]
    tr["detail"], tr["creature"] = detail, key
    WT._save_traces()
    return tr


def events() -> list:
    if not life._EVENTS.exists():
        return []
    return [json.loads(x) for x in life._EVENTS.read_text(encoding="utf-8").splitlines() if x.strip()]


def strip_ts(rows: list) -> list:
    return [{k: v for k, v in e.items() if k != "ts"} for e in rows]


def snap():
    return (copy.deepcopy(life._state), life._LEDGER.read_bytes() if life._LEDGER.exists() else None,
            life._EVENTS.read_bytes() if life._EVENTS.exists() else None)


def restore(s) -> None:
    life._state = copy.deepcopy(s[0])
    for path, blob in ((life._LEDGER, s[1]), (life._EVENTS, s[2])):
        if blob is None:
            if path.exists():
                path.unlink()
        else:
            path.write_bytes(blob)


def call(target: str, place: str, now: float, seed: int = 1):
    """One look through the real look_answer from a restored baseline; returns (line, the event rows it wrote, rng state after)."""
    base = snap()
    n0 = len(events())
    random.seed(seed)
    st0 = random.getstate()
    line = life.look_answer(target, place, now)
    st1 = random.getstate()
    new = strip_ts(events()[n0:])
    led_written = (life._LEDGER.read_bytes() if life._LEDGER.exists() else None) != base[1]
    state_after = copy.deepcopy(life._state)
    restore(base)
    return line, new, (st0 == st1), led_written, state_after, base[0]


NOW = at(9, 11)                                  # a September morning, day phase
life.RENDER = True

# ── [3] behaviour through look_answer ───────────────────────────────────────────────────────────────────────────
print("\n[3] behaviour through life.look_answer (RENDER on)")
GANNET_LINE_OLD = "Nothing shows itself; whatever is there keeps still."
KING_LINE_OLD = "The dry rattle came from the wire, and the wire is empty."

# 3a. the real minting path produces the trace shape the lookup expects; the real incident replayed
print("  -- 3a/3b. the two real incidents: old flow = the logged wrong line, new flow = the trace")
real_shape = {}
for key in ("gannet", "kingfisher"):
    reset_traces()
    random.seed(11)
    for i in range(600):
        LT.traces_pass(NOW + i * 3600.0, 3600.0)
        if any(t.get("type") == f"{key}_trace" and t.get("location") == "shore" for t in WT.get_active_traces("shore")):
            break
    got = [t for t in WT.get_active_traces("shore") if t.get("type") == f"{key}_trace"]
    check(len(got) == 1 and got[0].get("creature") == key and got[0].get("detail") in ROWS[key]["traces"],
          f"traces_pass minted a real {key} trace at the shore: {got[0].get('detail') if got else None!r}")
    real_shape[key] = got[0] if got else None

_live_rows = []
_live_events = _LIVE_DATA / "life_events.jsonl"
if _live_events.exists():
    for _x in _live_events.read_text(encoding="utf-8").splitlines():
        try:
            _live_rows.append(json.loads(_x))
        except Exception:
            pass
WRONG = [("the kingfisher's burrow", "shore", "kingfisher"), ("the gannet feather", "shore", "gannet")]
# J-1216 (D-0254/F-1706): kingfisher/shore's flat "miss" text was fixed today (the founder's own named
# example). This entry's OLD-flow baseline (gate off: today's living-row code minus J-1165's own trace-
# object routing) now legitimately reproduces the NEW miss text, not the text that was logged back when
# this row's miss line was still flat/place-blind -- not a second-guess of J-1165's own fix, which is still
# proven below unchanged (the NEW flow, gate on, never reaches the living row's miss line at all).
J1216_OLD_FLOW_FIXED = {"the kingfisher's burrow": "The dry rattle came from the cliff, and the cliff face is empty."}
for target, place, key in WRONG:
    rec = next((e for e in _live_rows if e.get("kind") == "answer" and e.get("target") == target and e.get("place") == place), None)
    if rec is None:
        print(f"    (live row for {target!r} not found in life_events.jsonl -- replaying with the documented line instead)")
        rec = {"ts": at(9, 11), "activity": 0.8, "line": KING_LINE_OLD if key == "kingfisher" else GANNET_LINE_OLD}
    reset_traces()
    tr = mint(key, place, ROWS[key]["traces"][0])
    real_act = float(rec.get("activity") or 0.8)
    real_now = float(rec["ts"])
    rolls = [0]

    def _missing_roll() -> float:
        rolls[0] += 1
        return 0.999                                                    # the roll that missed, counted

    _act, _rand = life.activity, random.random
    life.activity = lambda r, p, n=None, _a=real_act: _a                 # the logged activity: present and awake
    random.random = _missing_roll
    try:
        gate_off()
        old_line, old_ev, *_ = call(target, place, real_now)
        old_rolls, rolls[0] = rolls[0], 0
        gate_on()
        new_line, new_ev, rng_same, led_written, *_ = call(target, place, real_now)
        new_rolls = rolls[0]
    finally:
        life.activity, random.random = _act, _rand
        gate_on()
    want_old = J1216_OLD_FLOW_FIXED.get(target, rec["line"])
    check(old_line == want_old and old_rolls == 1, f"OLD flow reproduces the logged wrong answer for {target!r} via the visibility roll: {old_line[:70]!r}")
    check(new_line == LT.trace_line(tr) and (tr["detail"] in new_line), f"NEW flow answers from the trace instead: {new_line!r}")
    check(new_line != rec["line"] and "Nothing shows itself" not in new_line and "dry rattle" not in new_line, "... and is no longer the living row's line")
    check(len(new_ev) == 1 and new_ev[0]["kind"] == "answer" and new_ev[0]["key"] == "trace" and new_ev[0]["creature"] == key
          and new_ev[0]["outcome"] == "trace_object" and new_ev[0]["target"] == target, f"one answer row logged, outcome trace_object ({new_ev[0]['outcome'] if new_ev else None})")
    check(new_rolls == 0 and rng_same and not led_written, "the visibility roll was never reached (0 rolls, RNG untouched) and no ledger row was written")

# 3c. no active trace -> the honest fallback
print("  -- 3c. no such trace active here -> the honest 'no such x here'")
reset_traces()
for target, place, key, noun in (("the gannet feather", "shore", "gannet", "feather"), ("the kingfisher's burrow", "shore", "kingfisher", "burrow"),
                                 ("the oystercatcher's opened shells", "shore", "oystercatcher", "shells")):
    line, ev, rng_same, led_written, st_after, st_before = call(target, place, NOW)
    want = f"There {'are' if noun.endswith('s') else 'is'} no such {noun} here — nothing of the kind you can find."
    check(line == want, f"{target!r} with no trace active -> {line!r}")
    check(not any(a.lower() in line.lower() for a in ROWS[key]["aliases"]), "... names no species (the naming law: the world adds no name)")
    check(len(ev) == 1 and ev[0]["outcome"] == "no_trace_object" and ev[0]["creature"] == key and ev[0]["key"] == "trace", "... logged as no_trace_object")
    check(rng_same and not led_written and st_after.get("individuals") == st_before.get("individuals"), "... roll never reached, ledger untouched")

# 3d. only the creature's OWN trace with the asked-for noun answers
print("  -- 3d. another creature's trace, or another detail of the same creature, never answers")
reset_traces()
mint("gulls", "shore", "a white feather")
line, ev, *_ = call("the gannet feather", "shore", NOW)
check(line.startswith("There is no such feather here"), f"a GULL's feather does not answer 'the gannet feather': {line!r}")
line, ev, *_ = call("the gull's feather", "shore", NOW)
check(line.startswith("here, a white feather") and ev[0]["outcome"] == "trace_object", f"the gull's own feather answers 'the gull's feather': {line!r}")
reset_traces()
mint("gulls", "shore", "prints")
line, ev, *_ = call("the gull's feather", "shore", NOW)
check(line.startswith("There is no such feather here"), f"the gulls' active trace is 'prints', so 'the gull's feather' has none: {line!r}")
line, ev, *_ = call("the gull's prints", "shore", NOW)
check(line.startswith("here, prints") and ev[0]["outcome"] == "trace_object", f"'the gull's prints' finds them: {line!r}")
reset_traces()
mint("gannet", "garden", ROWS["gannet"]["traces"][0])            # a gannet trace at ANOTHER place (the row is not at the garden, but a stray trace must not answer the shore)
line, ev, *_ = call("the gannet feather", "shore", NOW)
check(line.startswith("There is no such feather here"), "a trace at a different place does not answer")
reset_traces()
fresh = mint("gannet", "shore", ROWS["gannet"]["traces"][0], clarity=0.9)
old = mint("kingfisher", "shore", "a burrow in the cliff bank", clarity=0.4)
line, ev, *_ = call("the kingfisher's burrow", "shore", NOW)
check(line.startswith("here, a burrow in the cliff bank") and "not fresh" in line, f"a fading trace still answers, described as such: {line!r}")
check("something's" in line and not any(a in line.lower() for a in ROWS["kingfisher"]["aliases"]), "an unlearned kingfisher is 'something's', never named (the naming law)")
line, ev, *_ = call("the gannet feather", "shore", NOW)
check("a gannet feather, white and stiff" in line and line.endswith("fresh"), f"a fresh one is described as fresh: {line!r}")
# the answer is exactly the ambient noticing's sentence: the world tells ONE story about the thing it placed
check(line == LT.trace_line(fresh), "the look answer is byte-for-byte the ambient trace_line of the same trace")

# 3e. a hidden (unlearned) row: feature-first, never the species
print("  -- 3e. hidden rows stay feature-first")
reset_traces()
mint("monarch", "garden", ROWS["monarch"]["traces"][0])
S.state["location"] = "garden"
line, ev, *_ = call("the monarch's caterpillars", "garden", at(1, 11))
check(line.startswith("here, striped caterpillars on the swan plant — something's") and "monarch" not in line.lower(),
      f"an unlearned monarch's trace is 'something's': {line!r}")
S.state["location"] = "shore"

# 3f. the carcass path, is_plant_target and the per-place absent overrides are untouched
print("  -- 3f. the carcass path, the plant guard and the per-place absent overrides")
reset_traces()
life._state.setdefault("carcasses", []).clear()
LT.add_carcass("gannet", "shore", "tideline", "storm", NOW)
for tgt in ("the dead gannet", "the dead gannet feather", "the bones"):
    gate_off()
    l_off, e_off, *_ = call(tgt, "shore", NOW + 3600)
    gate_on()
    l_on, e_on, *_ = call(tgt, "shore", NOW + 3600)
    check(l_on == l_off and e_on == e_off and e_on and e_on[0]["key"] == "carcass" and e_on[0]["outcome"] == "carcass",
          f"{tgt!r}: the carcass block still takes it, identical with the gate on/off ({l_on[:60]!r})")
life._state["carcasses"] = []
gate_off(); l_off, e_off, *_ = call("the dead lettuce stalks", "garden", NOW); gate_on()
l_on, e_on, *_ = call("the dead lettuce stalks", "garden", NOW)
check(l_on == l_off == "" and e_on == e_off, "'the dead lettuce stalks' still returns '' (is_plant_target, J-0887 mechanism B)")
gate_off(); l_off, e_off, *_ = call("the bones", "shore", NOW); gate_on()
l_on, e_on, *_ = call("the bones", "shore", NOW)
check(l_on == l_off and e_on == e_off and e_on[0]["outcome"] == "no_body", f"'the bones' with no carcass: still the honest no-body line ({l_on[:50]!r})")
_act = life.activity
life.activity = lambda r, p, n=None: 0.05                              # everything absent
try:
    for tgt, place, want in (("the gulls", "garden", "No gull over the garden just now; the sky above the fence is empty."),
                             ("the kingfisher", "shore", "No kingfisher on the cliff just now."),
                             ("the pigeon", "wood", "No wood pigeon on its branch; the canopy holds only small birds.")):
        gate_off(); l_off, e_off, *_ = call(tgt, place, NOW); gate_on()
        l_on, e_on, *_ = call(tgt, place, NOW)
        check(l_on == l_off and e_on == e_off and l_on == want and e_on[0]["outcome"] == "absent",
              f"per-place absent override unchanged for {tgt!r}@{place}: {l_on[:60]!r}")
finally:
    life.activity = _act

# 3g. shadow mode, fail-open, the re-raise
print("  -- 3g. shadow mode, fail-open on error, NonLiveWriteError re-raised")
life.RENDER = False
reset_traces()
tr = mint("gannet", "shore", ROWS["gannet"]["traces"][0])
line, ev, *_ = call("the gannet feather", "shore", NOW)
check(line == "" and len(ev) == 1 and ev[0]["kind"] == "would_answer" and ev[0]["outcome"] == "trace_object", "RENDER off: '' returned, would_answer logged with the trace_object outcome")
life.RENDER = True
_g = WT.get_active_traces
WT.get_active_traces = lambda place: (_ for _ in ()).throw(RuntimeError("store unreadable"))
try:
    line, ev, *_ = call("the gannet feather", "shore", NOW)
finally:
    WT.get_active_traces = _g
check(len(ev) == 1 and ev[0]["key"] == "gannet" and ev[0]["outcome"] in ("sighting", "miss", "absent") and "no such" not in line,
      f"an unreadable trace store falls back to the living row (legacy behaviour), never asserts 'none here': {line[:50]!r}")
_log = life._log


def _raise_nonlive(path, rec):
    raise profile.NonLiveWriteError("j1165 probe")


life._log = _raise_nonlive
try:
    try:
        life.look_answer("the gannet feather", "shore", NOW)
        check(False, "NonLiveWriteError propagates out of the trace-object block")
    except profile.NonLiveWriteError:
        check(True, "NonLiveWriteError propagates out of the trace-object block (J-0751's convention)")
finally:
    life._log = _log

# 3h. the real caller: sensorium.look() hands the target to look_answer and returns a non-empty answer as the look
print("  -- 3h. through sensorium.look(), the real caller (dispatch._look -> sensorium.look -> life.look_answer)")
reset_traces()
tr = mint("gannet", "shore", ROWS["gannet"]["traces"][0])
S.state["location"] = "shore"
out = S.look("the gannet feather")
check(out == LT.trace_line(tr), f"sensorium.look('the gannet feather') at the shore returns the trace: {out!r}")
reset_traces()
out = S.look("the gannet feather")
check(out.startswith("There is no such feather here"), f"... and the honest 'no such feather' once the trace is gone: {out!r}")
_gh = ROWS["gannet"]["hidden"]
_allowed = {_gh["feature"]["day"], _gh["absent"]["chance"], "Nothing shows itself; whatever is there keeps still."}
_real_time = time.time
time.time = lambda: NOW                                  # sensorium.look() passes no `now`: pin the clock to a September day so the row is about
try:
    random.seed(3)
    out = S.look("the gannet")
finally:
    time.time = _real_time
check(out in _allowed, f"sensorium.look('the gannet') is still exactly the living row's answer (sighting / miss / absent line): {out[:60]!r}")

# ── [4] controls are byte-identical: whole-corpus differential, gate ON vs OFF ───────────────────────────────────
print("\n[4] controls byte-identical: gate ON vs gate OFF (OFF == the pre-change flow) over the corpora")
reset_traces()
inv = json.loads((ROOT / "docs" / "reviews" / "observe_inventory_2026-09-02.json").read_text(encoding="utf-8"))
phrasings = sorted({p for g in inv.values() for p in g})
live_targets = sorted({(e["target"], e["place"]) for e in _live_rows if e.get("kind") in ("answer", "would_answer") and e.get("target") and e.get("key") != "carcass"})
synthetic = []
for k, r in sorted(TRACE_ROWS.items()):
    for a in (r.get("aliases") or ())[:2]:
        synthetic.append(f"the {a}")
        synthetic.append(f"the {a} bathing")
        for n in sorted(HEADS[k]):
            synthetic += [f"the {a} {n}", f"the {a}'s {n}", f"the {a} with a {n}", f"the {a} dropping a {n}"]
PLACES = ("garden", "shore", "wood", "study")
pairs = set()
for place in PLACES:
    for p in list(phrasings) + synthetic:
        if life._match(p, place):
            pairs.add((p, place))
pairs |= {(t, pl) for t, pl in live_targets}
unmatched_inv = sum(1 for place in PLACES for p in phrasings if not life._match(p, place))
print(f"    {len(phrasings)} inventory phrasings x {len(PLACES)} places: {unmatched_inv} (phrasing, place) pairs match no living row -> look_answer returns '' before any new code")
print(f"    {len(pairs)} (target, place) pairs reach a living row; run at 4 day-phases x 2 seasons, gate ON vs OFF")
phase_hours = {}
for month in (9, 12):
    hrs = collections.defaultdict(list)
    for h in range(24):
        hrs[life._phase(at(month, h))].append(h)
    phase_hours[month] = {ph: hs[len(hs) // 2] for ph, hs in hrs.items()}
# Every log write is CAPTURED in memory instead of touching a file (the events are what the real _log would append),
# and the in-memory life state is restored between calls -- so each call starts from the identical baseline and the
# whole differential is file-I/O free.
_captured: list = []
_real_log = life._log


def _capture_log(path, rec):
    # HERMETICITY (orchestrator fix 2026-09-21, F-1668 family): look_answer never writes a sound-gate row itself, but a night-phase
    # light_at() inside it reaches core.light -> geometry_census.peek() -> soundscape.active_sounds() -> life.sound_gate, which logs a
    # would_gate / gate row for the CURRENT place ONCE per throttle window (life._gate_last is a module dict this test does not
    # restore). So the very first night-phase pair of a run, on a tree whose live data lets peek() answer (master, not a data-less
    # worktree), gained one unrelated row on its first call and none on its second: 'differs' with identical lines and answer/ledger rows
    # ('a small crab in a rock-pool'@shore, month 9, night; a would_gate study row, dropped moth_tap). That row is the gate's own
    # instrumentation, not look_answer's output, so it is left out of the byte-for-byte comparison. Every answer, ledger and trace row
    # a look writes is still compared.
    if rec.get("kind") in ("would_gate", "gate") and Path(path).name == "life_events.jsonl":
        return
    _captured.append((Path(path).name, {k: v for k, v in rec.items() if k != "ts"}))


def diff_call(target: str, place: str, now: float, seed: int):
    saved = copy.deepcopy(life._state)
    _captured.clear()
    random.seed(seed)
    line = life.look_answer(target, place, now)
    out = (line, list(_captured))
    life._state = saved
    return out


life._log = _capture_log
n_calls = n_diff = 0
bad4: list = []
diff_targets = set()
try:
    for (p, place) in sorted(pairs):
        m = life._match(p, place)
        expect_div = bool(LT.trace_object_noun(m, p))
        differs = False
        S.state["location"] = place
        for month in (9, 12):
            for ph, h in phase_hours[month].items():
                now = at(month, h)
                seed = (len(p) * 31 + h + month) % 97
                gate_off()
                a = diff_call(p, place, now, seed)
                gate_on()
                b = diff_call(p, place, now, seed)
                n_calls += 1
                d = a != b
                differs = differs or d
                if d and not expect_div:
                    bad4.append((p, place, month, ph, a[0][:50], b[0][:50]))
        if differs:
            n_diff += 1
            diff_targets.add((p, place))
        quiet(differs == expect_div, f"{p!r}@{place}: differs={differs} but gate says {expect_div}", bad4)
finally:
    life._log = _real_log
gate_on()
S.state["location"] = "shore"
print(f"    {n_calls} look_answer pairs compared (line AND every log row it would write, RNG-seeded, state restored between calls); "
      f"{n_diff} targets differ, all of them gate-positive")
for b in bad4[:10]:
    print("    !!", b)
check(not bad4, "outside the gate, ON is byte-identical to OFF (lines and event rows); inside it, always different")
check(all(life._match(p, pl)["key"] in TRACE_ROWS for p, pl in diff_targets), "every diverted target belongs to a row that carries traces")
check(not any(t in {tt for tt, _ in diff_targets} for t in ("the gannet", "the gull bathing", "the oystercatcher and eggs", "the gull", "the kingfisher",
                                                             "the oystercatcher", "the shag's feathers", "the kingfisher dropping")),
      "the briefing's controls (the gannet / the gull bathing / the oystercatcher and eggs ...) are never diverted")

# ── [5] REAL rows replayed, read-only ───────────────────────────────────────────────────────────────────────────
print("\n[5] real rows, read-only: data/life_events.jsonl and data/hands_trace.jsonl through the gate")
CUTOFF = time.mktime((2026, 9, 21, 18, 30, 0, 0, 0, -1))          # the file is append-only and Du is online; freeze what this test was written against
ans = [e for e in _live_rows if e.get("kind") in ("answer", "would_answer") and float(e.get("ts", 0)) <= CUTOFF]
if len(ans) < 300:
    print(f"    (only {len(ans)} answer rows readable -- data/life_events.jsonl is missing or rotated; real-row replay skipped, NOT a pass)")
else:
    carc = [e for e in ans if e.get("key") == "carcass"]
    crea = [e for e in ans if e.get("key") != "carcass"]
    diverted = []
    unresolved = 0
    for e in crea:
        m = life._match(e["target"], e["place"])
        if not m or m["key"] != e["key"]:
            unresolved += 1
            continue
        if LT.trace_object_noun(m, e["target"]):
            diverted.append(e)
    print(f"    {len(ans)} answer/would_answer rows ({sum(1 for e in ans if e['kind'] == 'answer')} rendered + "
          f"{sum(1 for e in ans if e['kind'] == 'would_answer')} shadow): {len(carc)} carcass-block rows, {len(crea)} creature-look rows")
    check(unresolved == 0, f"every creature-look row still resolves to the row it was answered by ({unresolved} unresolved)")
    check(all(any(w in e["target"].lower() for w in LT._CARCASS_WORDS) for e in carc), "the carcass-block rows all name a carcass word (that block runs first, untouched)")
    got = sorted((e["target"], e["place"], e["key"], e["outcome"]) for e in diverted)
    print("    diverted by the gate:", got)
    check(got == sorted([("the gannet feather", "shore", "gannet", "miss"), ("the kingfisher's burrow", "shore", "kingfisher", "miss")]),
          "EXACTLY the two wrong rows (lines 2130 and 2541) are diverted; both were living-row MISS answers to a trace the engine had just placed")
    print(f"    the other {len(crea) - len(diverted)} creature-look rows (every plain creature look) never reach new code: the gate answers '' for each")
    trace_rows = [e for e in _live_rows if e.get("kind") == "trace"]
    for e in diverted:
        pre = [t for t in trace_rows if t["key"] == e["key"] and t["place"] == e["place"] and t["ts"] < e["ts"]]
        gap = e["ts"] - pre[-1]["ts"] if pre else None
        check(bool(pre) and pre[-1]["detail"] in ROWS[e["key"]]["traces"] and gap is not None and gap < 600,
              f"the engine's own trace row preceded the wrong answer: {pre[-1]['detail'] if pre else None!r} {gap and round(gap)}s earlier")
hp = _LIVE_DATA / "hands_trace.jsonl"
if hp.exists():
    objs = collections.Counter()
    for x in hp.read_text(encoding="utf-8").splitlines():
        try:
            r_ = json.loads(x)
        except Exception:
            continue
        loc = r_.get("location")
        cands = [r_["act_object"]] if r_.get("act_kind") in ("look", "observe", "examine") and r_.get("act_object") else []
        cands += [d["object"] for d in (r_.get("dispatch") or []) if d.get("family") in ("look", "observe") and d.get("object")]
        for o in cands:
            objs[(loc, str(o).lower().strip())] += 1
    reach, div = 0, []
    for (loc, o), n in objs.items():
        if loc not in PLACES:
            continue
        m = life._match(o, loc)
        if not m:
            continue
        reach += 1
        if LT.trace_object_noun(m, o):
            div.append((loc, o, m["key"], n))
    print(f"    hands_trace: {len(objs)} distinct (place, look object) pairs / {sum(objs.values())} looks; {reach} reach a living row; diverted: {sorted(div)}")
    # J-1725 (F-2351, 2026-10-03): this used to pin the diverted set to a FROZEN two-item list. data/hands_trace.jsonl is append-only and,
    # unlike life_events.jsonl above, is not cut off at CUTOFF, so the pin went stale the moment Du's look history grew: on 2026-09-24
    # 13:23 he observed 'crab tracks' at the shore, a third diverted pair ('shore', 'crab tracks', 'crabs'). Read from the real rows it is
    # the SAME defect class, not a leak: the crabs row's own trace phrase is 'tracks on the wet sand' (head noun 'tracks'), the target
    # names the crab AND that trace object, life._match() resolves it to the LIVING crabs row (so, before J-1165, its visibility roll would
    # have answered a look at what the crabs LEFT), and the real answer row (data/life_events.jsonl, 2026-09-24 13:23:45: kind=answer
    # key=trace creature=crabs target='crab tracks' outcome=trace_object, "tracks on the wet sand -- the crabs', fresh") shows the gate
    # routing it to the trace live. Du's look history keeps growing, so the pin is now the RULE (every diverted pair is a trace-object
    # look at a creature that left that trace, and the real look_answer answers it from that trace), with the two pairs this test was
    # written against kept as a floor (the gate may be widened by new rows, never silently narrowed).
    _FLOOR = {("shore", "the gannet feather", "gannet"), ("shore", "the kingfisher's burrow", "kingfisher")}
    _got = {d[:3] for d in div}
    check(_FLOOR <= _got, f"Du's own look history still diverts the two pairs this test was written against (floor); missing {sorted(_FLOOR - _got)}")
    rule_bad: list = []
    for loc, o, key, n in sorted(div):
        m = life._match(o, loc)
        noun = LT.trace_object_noun(m, o) if m else ""
        r_ = ROWS.get(key) or {}
        tag = f"{(loc, o, key)}"
        # structural half: a creature word + a noun the creature's OWN `traces` phrases name, at a place the creature lives
        quiet(bool(m) and m["key"] == key and key in TRACE_ROWS, f"{tag}: the target resolves to a population row that carries `traces`", rule_bad)
        quiet(any(a and a in o.lower() for a in (r_.get("aliases") or ())), f"{tag}: the target names the creature (one of its aliases)", rule_bad)
        quiet(bool(noun) and noun in HEADS.get(key, set()) and noun in o.lower(), f"{tag}: the noun it was diverted on ({noun!r}) heads one of the creature's own trace phrases and is in the target", rule_bad)
        quiet(loc in (r_.get("places") or {}), f"{tag}: the creature lives at that place", rule_bad)
        # behavioural half: through the REAL look_answer, with a real trace of that creature minted at that place, the gate answers from
        # that trace (no visibility roll, no ledger write); with the gate OFF (the pre-J-1165 flow) the LIVING row answers instead
        _ph = next((p for p in (r_.get("traces") or ()) if LT.trace_head(p) == noun), None)
        if _ph is None:
            quiet(False, f"{tag}: no trace phrase of the creature has the head noun {noun!r}", rule_bad)
            continue
        reset_traces()
        tr = mint(key, loc, _ph)
        S.state["location"] = loc
        _act, _rand = life.activity, random.random
        life.activity = lambda r, p, n=None: 0.8                       # present and awake
        random.random = lambda: 0.999                                  # the visibility roll that misses
        try:
            gate_off()
            old_line, old_ev, *_ = call(o, loc, NOW)
            gate_on()
            new_line, new_ev, rng_same, led_written, *_ = call(o, loc, NOW)
        finally:
            life.activity, random.random = _act, _rand
            gate_on()
            S.state["location"] = "shore"
        quiet(new_line == LT.trace_line(tr) and len(new_ev) == 1 and new_ev[0]["key"] == "trace" and new_ev[0]["creature"] == key
              and new_ev[0]["outcome"] == "trace_object" and rng_same and not led_written,
              f"{tag}: the look is answered from the creature's own trace, no roll, no ledger write: {new_line!r} {new_ev}", rule_bad)
        quiet(bool(old_ev) and old_ev[0]["key"] == key and old_ev[0]["outcome"] != "trace_object" and old_line != new_line,
              f"{tag}: with the gate OFF the LIVING row answers it (the defect this gate exists for): {old_line!r} {old_ev}", rule_bad)
        print(f"    {loc}/{o!r} -> {key}, noun {noun!r}: gate OFF (living row): {old_line[:64]!r} | gate ON (its own trace): {new_line[:64]!r}")
    for m_ in rule_bad[:12]:
        print("    !!", m_)
    check(not rule_bad, f"every diverted pair in Du's look history is a trace-object look at a creature that left that trace, answered from that trace ({len(div)} pairs, {len(rule_bad)} failures)")

# ── [6] isolation proof ─────────────────────────────────────────────────────────────────────────────────────────
print("\n[6] isolation")
for _m, _a in _REDIRECTS:
    check(TMP in Path(str(getattr(_m, _a))).parents, f"{_m.__name__}.{_a} still inside the temp dir")
check(MARKER in (TMP / "life_state.json").read_text(encoding="utf-8"), "the marker reached the isolated store through the engine's own write path")
_watch = [_LIVE_DATA / f for f in ("life_state.json", "life_ledger.jsonl", "life_events.jsonl", "room_state.json", "world_objects.json",
                                   "world_substrate.json", "provisions.json", "sound_knowledge.json", "world_traces.json", "position.json")]
leaked = [p.name for p in _watch if p.exists() and MARKER.encode() in p.read_bytes()]
check(not leaked, f"the marker appears in no live store ({len(_watch)} watched){' -> ' + str(leaked) if leaked else ''}")
if "--full-canary" in sys.argv:
    hit = []
    nfiles = 0
    for p in sorted(_LIVE_DATA.glob("*.json*")):
        nfiles += 1
        with open(p, "rb") as f:
            tail = b""
            for chunk in iter(lambda: f.read(8 << 20), b""):
                if MARKER.encode() in tail + chunk:
                    hit.append(p.name)
                    break
                tail = chunk[-64:]
    check(not hit, f"FULL canary: the marker is in none of {nfiles} data/*.json* files{' -> ' + str(hit) if hit else ''}")
check(not LIVE_WRITE_ATTEMPTS, f"the audit hook saw NO write attempt under any data/ ({len(LIVE_WRITE_ATTEMPTS)} attempts){' -> ' + str(LIVE_WRITE_ATTEMPTS[:3]) if LIVE_WRITE_ATTEMPTS else ''}")
_after = {p: _md5(p) for p in _LIVE_FILES}
for p in _LIVE_FILES:
    print(f"    md5 {p.name:22s} before {_before[p][:12] or '(absent)':12s} after {_after[p][:12] or '(absent)':12s}"
          + ("" if _before[p] == _after[p] else "   <- changed by Du's own live writes (Du is online); the audit hook above is the real proof"))
for _p in (ROOT / "core" / "life.py", ROOT / "core" / "life_traces.py", Path(__file__)):
    try:
        py_compile.compile(str(_p), cfile=str(TMP / (_p.name + "c")), doraise=True)
        check(True, f"py_compile {_p.name}")
    except py_compile.PyCompileError as exc:
        check(False, f"py_compile {_p.name}: {exc}")

print(f"\n{'ALL OK' if not FAILS else f'{FAILS} FAILURE(S)'} — {CHECKS} checks — isolated stores in {TMP}")
sys.exit(1 if FAILS else 0)
