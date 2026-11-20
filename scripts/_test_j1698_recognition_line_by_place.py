"""
Regression: J-1698 (F-2305) -- A GRADUATED INDIVIDUAL'S RECOGNITION LINE IS SAID ONLY AT THE PLACE IT GRADUATED AT.

THE DEFECT (F-2305, verified live). core/life.py look_answer appended core/life_traces.with_individual_suffix(key, line) to EVERY later
sighting of a graduated key, at any place. The blackbird graduated at the GARDEN (five garden sightings, 2026-09-25 05:49:52); its first ever
rendered sighting at the WOOD (2026-09-27 15:45:51, life_events.jsonl line 4416) was told 'It is the same one -- you are sure of it now; you
have seen it here too often for it to be any other.' -- a claim of long acquaintance at a place where Du had never seen the bird. The record's
own 'place' was stored and never read at render. 15 of the 32 rows that can still graduate are registered at more than one place.

THE FIX (render-only, restart-gated). individual_suffix(key, place=None) / with_individual_suffix(key, line, place=None): look_answer passes the
look's place and the line is said only when it equals the record's place; place omitted / empty, or a record with no stored place, is today's
behaviour (naming, give_name and the HUD have no look place). note_sighting is NOT touched: graduation (D-0335 is open), the counter and what is
written to data/life_state.json do not change -- every sighting still counts, wherever it is.

  [0] module resolution + isolation set-up (F-1285: the code under test is THIS root's, not the shared tree's)
  [1] the REAL graduated records (a read-only copy of data/life_state.json): blackbird@wood plain (the F-2305 look) and blackbird@garden suffixed;
      oystercatcher / tui / korora (single-place rows) byte-identical to the old render; honeybee / gulls still dormant; naming + HUD unchanged
  [2] every multi-place eligible row, through the real look_answer: graduate at one place (5 looks), look at its other place(s) -> the plain line
      a creature that never graduated gives; back at the first place -> the suffix; name it (Bramble) -> the named line only at the first place
  [3] the before/after differential: ALL 58 population rows, the same look sequence under the OLD render (re-injected, place ignored) and the NEW
      one: lines byte-identical everywhere except the other-place looks of a graduated multi-place row (old = plain + suffix, new = plain);
      the world state, ledger, events and the saved life_state.json bytes are identical in every case -- the change writes nothing different
  [4] the API contract of individual_suffix / with_individual_suffix (no place = today's; legacy record with no place; named; dormant; signature)
  [5] isolation: audit hook (0 write attempts under any data/), canary marker, live-file hashes, py_compile

ISOLATION. The temp-redirect + audit-hook design J-1166 / J-1174 used: every store the engine can reach is redirected into a temp dir before anything
can write, and a Python audit hook records any attempt by THIS process to open-for-write / rename / remove anything under a data/ directory. The live
C:\\Nascence\\data files are only ever READ (md5-hashed before and after; with Du ONLINE they could change on their own, so the audit hook is the proof).
lab_env.isolate is NOT used (it would copy the 670 MB DB into data/_lab).

  python scripts/_test_j1698_recognition_line_by_place.py              # exit 0 = ALL OK
"""
from __future__ import annotations

import contextlib
import copy
import hashlib
import inspect
import json
import os
import py_compile
import random
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TMP = Path(tempfile.mkdtemp(prefix="j1698_recognition_by_place_"))
print("isolated store dir:", TMP)
MARKER = f"j1698_marker_{os.getpid()}"
# data/ is gitignored and never checked out into a job-run worktree, so "live" is the one real repo, never ROOT-relative.
_LIVE_DATA = Path(r"C:\Nascence") / "data"
_LIVE_FILES = [_LIVE_DATA / f for f in ("position.json", "room_state.json", "life_state.json", "life_ledger.jsonl", "life_events.jsonl",
                                        "world_traces.json", "life_flags.json", "wandering_log.jsonl", "sound_knowledge.json", "hands_trace.jsonl")]


def _md5(p: Path) -> str:
    if not p.exists():
        return ""
    h = hashlib.md5()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


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

# ── redirect every store the engine can reach BEFORE anything can write (the vetted list of J-1166 / J-1174) ─────
import core                                                    # noqa: E402
from core import profile                                       # noqa: E402
from core import life, life_traces as LT, world_traces as WT   # noqa: E402
from core import life_birds, life_mammals, garden_insects, garden_soil   # noqa: E402
from core import sensorium as S                                # noqa: E402
from core import locomotion as L                               # noqa: E402
from core import sound_knowledge as SK                         # noqa: E402
from core import soundscape as SC                              # noqa: E402
from core import world_clock as WC                             # noqa: E402

life._F, life._LEDGER, life._EVENTS, life._DATA = TMP / "life_state.json", TMP / "life_ledger.jsonl", TMP / "life_events.jsonl", TMP
life._FLAGS_F = TMP / "life_flags.json"                        # read-only in life.py; redirected so the result never depends on the live flag file
WT._TRACES_F = TMP / "world_traces.json"
S._STATE_F = TMP / "room_state.json"
L._POS_F = TMP / "position.json"
SK._LEDGER_F = TMP / "sound_knowledge.json"
SC._DATA, SC._SND_STATE_F, SC._FELT_SHADOW_F = TMP, TMP / "soundscape_state.json", TMP / "soundscape_felt_shadow.jsonl"
_REDIRECTS = [(life, "_F"), (life, "_LEDGER"), (life, "_EVENTS"), (life, "_FLAGS_F"), (WT, "_TRACES_F"), (S, "_STATE_F"),
              (L, "_POS_F"), (SK, "_LEDGER_F"), (SC, "_DATA"), (SC, "_SND_STATE_F"), (SC, "_FELT_SHADOW_F")]
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
S.state.update({"weather": "clear", "wind": "breeze", "fire": "out", "fire_fuel": 0.0, "last_event": 0, "location": "garden",
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
    """A bulk check: count it, print only failures (the table sections run hundreds)."""
    global FAILS, CHECKS
    CHECKS += 1
    if not cond:
        FAILS += 1
        sink.append(label)


def hm(month: int, day: int, hour: int, minute: int = 0, sec: int = 0, year: int = 2026) -> float:
    return time.mktime((year, month, day, hour, minute, sec, 0, 0, -1))


def _inside(p) -> bool:
    q = Path(str(p))
    return q == TMP or TMP in q.parents


# ── [0] module resolution (F-1285) ──────────────────────────────────────────────────────────────────────────────
print("\n[0] module resolution: the code under test is THIS root's, not the shared tree's")
print("    sys.path[0] =", sys.path[0])
for _m in (core, profile, life, LT, WT, life_birds, life_mammals, garden_insects, garden_soil, S, L, SK, SC, WC):
    _f = getattr(_m, "__file__", None)
    check(_f is not None and Path(_f).resolve().is_relative_to(ROOT), f"{_m.__name__} was loaded from inside {ROOT}")
for _m, _a in _REDIRECTS:
    check(_inside(getattr(_m, _a)), f"{_m.__name__}.{_a} redirected into the temp dir")
check("place" in inspect.signature(LT.with_individual_suffix).parameters and "place" in inspect.signature(LT.individual_suffix).parameters,
      "the loaded copy carries this job's code: individual_suffix / with_individual_suffix take the look's place")

ROWS = life.rows()
POP = {k: r for k, r in ROWS.items() if r.get("kind") == "population"}
PHASES = life.PHASES
life.RENDER = True
ELIGIBLE = {k for k, r in POP.items() if not LT.group_grain(r)}
BARRED = set(POP) - ELIGIBLE
check(len(POP) == 58 and len(ELIGIBLE) == 32 and len(BARRED) == 26, f"58 population rows = 32 eligible + 26 barred (group grain) -- the J-1174 partition, untouched ({len(POP)}, {len(ELIGIBLE)}, {len(BARRED)})")
F2305_MULTI = {"bellbird", "blackbird", "common_copper", "fantail", "garden_spider", "gecko", "kereru", "kingfisher", "mice", "morepork", "possum",
               "rabbit", "riroriro", "shining_cuckoo", "weta"}
MULTI = sorted(k for k in ELIGIBLE if len(POP[k].get("places") or {}) > 1)
check(F2305_MULTI <= set(MULTI) and len(MULTI) >= 15, f"the 15 multi-place rows F-2305 lists are all eligible and multi-place (now {len(MULTI)}: {MULTI})")
SINGLE_LIVE = {"oystercatcher": "shore", "tui": "garden", "korora": "shore"}
check(all(sorted(ROWS[k]["places"]) == [p] for k, p in SINGLE_LIVE.items()), "the oystercatcher (shore), tui (garden) and korora (shore) are single-place rows")

# ── helpers ─────────────────────────────────────────────────────────────────────────────────────────────────────
SFX_UNNAMED = " It is the same one — you are sure of it now; you have seen it here too often for it to be any other."
SFX_NAMED = " It is Bramble — you would know it anywhere now."


def events() -> list:
    if not life._EVENTS.exists():
        return []
    return [json.loads(x) for x in life._EVENTS.read_text(encoding="utf-8").splitlines() if x.strip()]


def ledger_rows() -> list:
    if not life._LEDGER.exists():
        return []
    return [json.loads(x) for x in life._LEDGER.read_text(encoding="utf-8").splitlines() if x.strip()]


def strip_ts(rows: list) -> list:
    return [{k: v for k, v in e.items() if k != "ts"} for e in rows]


def fresh_state(seed: dict | None = None) -> None:
    """An empty world state and empty logs (never `life._state = {}` + _load(): that would re-read the temp file a graduation just saved).
    `seed` = top-level keys of life_state.json to plant (individuals, recent_sightings), deep-copied."""
    life._state = {"rows": {}, "dark": {"since": 0.0, "place": None, "adapt": 0.0}, "_last": 0.0}
    for p in (life._EVENTS, life._LEDGER, life._F):
        if p.exists():
            p.unlink()
    for k, v in (seed or {}).items():
        life._state[k] = copy.deepcopy(v)


_real_activity, _real_visibility, _real_random = life.activity, life.visibility, random.random


@contextlib.contextmanager
def forced(act=0.9, vis=0.9, roll=0.0):
    """Hold the world at 'present, awake, and the visibility roll comes up'."""
    life.activity = lambda r, p, n=None, _a=act: _a
    life.visibility = lambda r, p, n=None, _v=vis: _v
    random.random = lambda: roll
    try:
        yield
    finally:
        life.activity, life.visibility, random.random = _real_activity, _real_visibility, _real_random


def alias_for(r: dict, place: str):
    for a in (r.get("aliases") or ()):
        m = life._match(f"the {a}", place)
        if m is not None and m["key"] == r["key"]:
            return f"the {a}"
    return None


def feat_line(r: dict, ph: str, place: str | None = None) -> str:
    """The lookup look_answer performs, verbatim (incl. J-1216's feature_by_place override)."""
    h = (r.get("hidden") or {})
    feat_by_place = (h.get("feature_by_place") or {}).get(place) if place is not None else None
    feat = feat_by_place if isinstance(feat_by_place, dict) else (h.get("feature") or {})
    return feat.get(ph) or feat.get("night" if ph in ("night", "dusk") else "day") or feat.get("any") or ""


def ph_for(r: dict, place: str) -> str:
    """A phase at which this row has a look line at this place (a nocturnal row is looked at by night); 'day' for a row with no feature text."""
    return next((p for p in PHASES if feat_line(r, p, place)), "day")


def phase_time(ph: str, off: int) -> float:
    """An instant inside phase `ph` on 2026-09-(15+off), the middle of the phase's own run of hours (bucketed by the world clock itself)."""
    hours = [h for h in range(24) if life._phase(hm(9, 15 + off, h, 30)) == ph]
    return hm(9, 15 + off, hours[len(hours) // 2], 30) if hours else hm(9, 15 + off, 12, 30)


def end_sentence(text: str) -> str:
    return LT._end_sentence(text)


# the PRE-J-1698 render, verbatim, re-injected (the place argument the new call site passes is accepted and IGNORED): the defect is shown on the
# SAME code path the fix is proved on, the way J-1174 re-injected the old night hours
def _old_individual_suffix(key: str) -> str:
    ind = LT.individual(key)
    if not ind:
        return ""
    if ind.get("name"):
        return f" It is {ind['name']} — you would know it anywhere now."
    return " It is the same one — you are sure of it now; you have seen it here too often for it to be any other."


def _old_with_individual_suffix(key: str, line: str, place=None) -> str:
    suffix = _old_individual_suffix(key)
    if not suffix:
        return line.strip()
    return (LT._end_sentence(line) + suffix).strip()


class OldRender:
    def __enter__(self):
        self._saved = LT.with_individual_suffix
        LT.with_individual_suffix = _old_with_individual_suffix
        return self

    def __exit__(self, *exc):
        LT.with_individual_suffix = self._saved


def run_seq(steps: list, seed: dict | None = None, render: str = "new"):
    """Run `steps` from a fresh (optionally seeded) world through the REAL look_answer / give_name / naming_act / hud_payload. Steps:
    ('look', target, place, now) | ('name', key, name, now) | ('act', thought, now) | ('hud', now). Returns the per-step records and the bytes
    of the life_state.json the engine itself saves at the end."""
    fresh_state(seed)
    out = []
    with (OldRender() if render == "old" else contextlib.nullcontext()), forced():
        for s in steps:
            n_ev, n_led = len(events()), len(ledger_rows())
            if s[0] == "look":
                res = life.look_answer(s[1], s[2], s[3])
            elif s[0] == "name":
                res = LT.give_name(s[1], s[2], s[3])
            elif s[0] == "act":
                _real_time = time.time
                time.time = lambda _t=s[2]: _t           # naming_act -> give_name stamps the history with time.time(): hold it so the two arms match
                try:
                    res = LT.naming_act(s[1], "")
                finally:
                    time.time = _real_time
            else:
                res = LT.hud_payload(s[1])
            out.append({"step": s, "res": res, "state": copy.deepcopy(life._state), "events": strip_ts(events()[n_ev:]), "ledger": strip_ts(ledger_rows()[n_led:])})
    life._save(force=True)
    return out, life._F.read_bytes()


_ref_cache: dict = {}


def plain_ref(key: str, place: str, now: float | None = None) -> str | None:
    """What a creature that NEVER graduated says at this place (at `now`, default an instant of the phase its look line is written for):
    one forced look from a fresh world (one sighting cannot graduate anything). None when the row has no alias that resolves at this place."""
    r = ROWS[key]
    when = phase_time(ph_for(r, place), 0) if now is None else now
    ck = (key, place, when)
    if ck not in _ref_cache:
        tgt = alias_for(r, place)
        if tgt is None:
            _ref_cache[ck] = None
        else:
            res, _ = run_seq([("look", tgt, place, when)])
            _ref_cache[ck] = res[0]["res"]
    return _ref_cache[ck]


def seq_for(key: str, a: str, bs: list, d0: int = 0):
    """five looks at `a` (the fifth graduates an eligible row), then each other place and back to `a`, the naming, then `a` and every other place again."""
    r = ROWS[key]
    d = [d0]

    def L1(place):
        s = ("look", alias_for(r, place), place, phase_time(ph_for(r, place), d[0]))
        d[0] += 1
        return s
    steps = [L1(a) for _ in range(5)]
    for b in bs:
        steps += [L1(b), L1(a)]
    steps.append(("name", key, "Bramble", phase_time("day", d[0])))
    steps += [L1(a)] + [L1(b) for b in bs]
    return steps


# ═══ [1] THE REAL RECORDS ═══════════════════════════════════════════════════════════════════════════════════════
print("\n[1] the real graduated records (read-only copy of data/life_state.json): the F-2305 look, and the rows that must not change")
_FALLBACK = {   # the documented 2026-10-03 values (F-2304 / F-2305), used only for a record the live file cannot supply
    "oystercatcher": {"place": "shore", "since": hm(9, 11, 6, 3, 30), "name": None, "sightings": 101, "last_seen": hm(10, 1, 6, 36, 44), "history": []},
    "honeybee": {"place": "garden", "since": hm(9, 17, 14, 46, 30), "name": None, "sightings": 7, "last_seen": hm(9, 17, 17, 0, 43), "history": []},
    "gulls": {"place": "shore", "since": hm(9, 19, 9, 39, 11), "name": None, "sightings": 7, "last_seen": hm(9, 19, 11, 49, 14), "history": []},
    "tui": {"place": "garden", "since": hm(9, 23, 14, 11, 52), "name": None, "sightings": 8, "last_seen": hm(9, 28, 16, 5, 28), "history": []},
    "blackbird": {"place": "garden", "since": hm(9, 25, 5, 49, 52), "name": None, "sightings": 6, "last_seen": hm(9, 27, 15, 45, 51), "history": []},
    "korora": {"place": "shore", "since": hm(9, 27, 4, 28, 33), "name": None, "sightings": 6, "last_seen": hm(9, 28, 3, 42, 53), "history": []},
}
try:
    _live = json.loads((_LIVE_DATA / "life_state.json").read_text(encoding="utf-8"))
except Exception:
    _live = {}
_live_ind = _live.get("individuals") or {}
LIVE = {}
for _k, _fb in _FALLBACK.items():
    LIVE[_k] = copy.deepcopy(_live_ind[_k]) if isinstance(_live_ind.get(_k), dict) and _live_ind[_k].get("place") else copy.deepcopy(_fb)
    LIVE[_k]["name"] = None            # the unnamed variant (a live name would only swap which suffix is expected; the named one is [2]/[4]'s)
print("    records:", {k: ((v["place"], v["sightings"]) + (("live",) if _live_ind.get(k) else ("documented",))) for k, v in LIVE.items()})
LIVE_REC = copy.deepcopy(_live.get("recent_sightings") or {})
SEED = {"individuals": LIVE, "recent_sightings": LIVE_REC}
check(LT.group_grain(ROWS["honeybee"]) and LT.group_grain(ROWS["gulls"]) and not any(LT.group_grain(ROWS[k]) for k in ("oystercatcher", "tui", "blackbird", "korora")),
      "the six records: honeybee + gulls are group grain (dormant), oystercatcher / tui / blackbird / korora are not")

NOW_F2305 = hm(9, 27, 15, 45, 51)                              # 2026-09-27 15:45:51, the blackbird's first ever rendered wood sighting
def tgt(key, place): return alias_for(ROWS[key], place)
def at(key, place, d): return ("look", tgt(key, place), place, phase_time(ph_for(ROWS[key], place), d))

STEPS1 = [("look", tgt("blackbird", "wood"), "wood", NOW_F2305),   # 0  THE F-2305 LOOK
          at("blackbird", "garden", 13),                           # 1  the place it graduated at
          at("blackbird", "wood", 14),                             # 2  the wood again
          at("oystercatcher", "shore", 13), at("tui", "garden", 13), at("korora", "shore", 13),     # 3,4,5  single-place rows
          at("honeybee", "garden", 13), at("gulls", "shore", 13), at("gulls", "garden", 13),       # 6,7,8  dormant records
          ("hud", NOW_F2305 + 86400),                              # 9
          ("act", "I will call the blackbird Ash.", NOW_F2305 + 86400),                          # 10 naming has no place
          at("blackbird", "garden", 15), at("blackbird", "wood", 15)]                              # 11, 12
check(all(s[1] is not None for s in STEPS1 if s[0] == "look"), "every look target resolves to its row at its place")
new1, new1_bytes = run_seq(STEPS1, SEED, "new")
old1, old1_bytes = run_seq(STEPS1, SEED, "old")
res_n, res_o = [x["res"] for x in new1], [x["res"] for x in old1]
REF = {(k, p): plain_ref(k, p) for k, p in (("blackbird", "wood"), ("blackbird", "garden"), ("oystercatcher", "shore"), ("tui", "garden"),
                                            ("korora", "shore"), ("honeybee", "garden"), ("gulls", "shore"), ("gulls", "garden"))}
check(all(REF.values()), f"each of those looks has a plain reference line ({[k for k, v in REF.items() if not v]})")
bb_wood, bb_garden = REF[("blackbird", "wood")], REF[("blackbird", "garden")]
bb_wood_f2305 = plain_ref("blackbird", "wood", NOW_F2305)       # the plain line AT THE F-2305 INSTANT (a 'day' look)
print("    the F-2305 look, the blackbird at the wood, 2026-09-27 15:45:51")
print("      OLD render:", repr(res_o[0][:80] + " ... " + res_o[0][-62:]))
print("      NEW render:", repr(res_n[0]))
check(res_o[0] == end_sentence(bb_wood_f2305) + SFX_UNNAMED, "the DEFECT, on the old render and the real record: 'It is the same one -- ... you have seen it here too often' at the wood")
check(res_n[0] == bb_wood_f2305 and "same one" not in res_n[0] and "too often" not in res_n[0] and "you are sure" not in res_n[0],
      "FIXED: the blackbird at the WOOD is the plain look line -- no recognition line, no 'here too often'")
check(bb_wood_f2305.startswith("a blackbird works the undergrowth") and res_n[0].endswith("fighting"), "... and it is the very line F-2305 quoted (a blackbird works the undergrowth ... something thin and fighting)")
check(res_n[1] == end_sentence(bb_garden) + SFX_UNNAMED == res_o[1], "the blackbird at the GARDEN (where it graduated) keeps the line, byte-identical to the old render")
check(res_n[2] == bb_wood, "a second look at the wood is plain again")
for i, (k, p) in ((3, ("oystercatcher", "shore")), (4, ("tui", "garden")), (5, ("korora", "shore"))):
    check(res_n[i] == res_o[i] == end_sentence(REF[(k, p)]) + SFX_UNNAMED,
          f"{k}@{p} (single-place row): the recognition line is byte-identical to the old render: {res_n[i][-48:]!r}")
for i, (k, p) in ((6, ("honeybee", "garden")), (7, ("gulls", "shore")), (8, ("gulls", "garden"))):
    check(res_n[i] == res_o[i] == REF[(k, p)] and "same one" not in res_n[i], f"{k}@{p} (a dormant group-grain record): the plain line, no suffix, byte-identical to the old render")
def first_diff(new, old):
    """(step index, component) of the first place the two arms differ, or None."""
    for i, (n, o) in enumerate(zip(new, old)):
        for comp in ("state", "events", "ledger"):
            if n[comp] != o[comp]:
                return i, comp
    return None


_fd1 = first_diff(new1, old1)
if _fd1:
    _i, _c = _fd1
    print("    first difference: step", _i, STEPS1[_i][:3], _c)
    if _c == "state":
        for _k in sorted(set(new1[_i]["state"]) | set(old1[_i]["state"])):
            if new1[_i]["state"].get(_k) != old1[_i]["state"].get(_k):
                print("      key", _k, "new:", str(new1[_i]["state"].get(_k))[:300], "| old:", str(old1[_i]["state"].get(_k))[:300])
    else:
        print("      new:", new1[_i][_c], "| old:", old1[_i][_c])
check(_fd1 is None, "the world state, the ledger and the events are identical under the old and the new render at EVERY step -- render only")
check(new1_bytes == old1_bytes, f"the life_state.json the engine saves is byte-identical under the old and the new render ({len(new1_bytes)} bytes)")
bb0, bb1 = new1[0]["state"]["individuals"]["blackbird"], LIVE["blackbird"]
check(bb0["sightings"] == bb1["sightings"] + 1 and bb0["last_seen"] == NOW_F2305 and bb0["place"] == "garden" and new1[0]["state"]["recent_sightings"] == LIVE_REC,
      f"the wood sighting is still COUNTED exactly as before (sightings {bb1['sightings']} -> {bb0['sightings']}, last_seen = the look, place still the garden, no blackbird@wood counter): only the render changed")
check(all(x["state"]["individuals"][k] == LIVE[k] for x in new1 for k in ("honeybee", "gulls")),
      "the dormant honeybee and gulls records are untouched at every step (the J-1174 read-time guard)")
hud = res_n[9]
check(sorted(hud.get("individuals", {})) == ["blackbird", "korora", "oystercatcher", "tui"] and hud["individuals"]["blackbird"]["place"] == "garden"
      and res_n[9] == res_o[9], f"the HUD payload is unchanged: the four live individuals, the blackbird at the garden ({sorted(hud.get('individuals', {}))})")
check(isinstance(res_n[10], str) and res_n[10].startswith("Ash, then.") and "at the garden" in res_n[10] and res_n[10] == res_o[10],
      f"naming (naming_act, no place) still names the garden blackbird from anywhere: {res_n[10][:70]!r}")
check(res_n[11] == end_sentence(bb_garden) + " It is Ash — you would know it anywhere now." and res_n[12] == bb_wood,
      "named: 'It is Ash -- you would know it anywhere now.' at the garden only; the wood look stays plain")
check(res_o[12] == end_sentence(bb_wood) + " It is Ash — you would know it anywhere now.", "(the old render said it at the wood too -- the named variant of the same defect)")

# ═══ [2] EVERY MULTI-PLACE ELIGIBLE ROW ═════════════════════════════════════════════════════════════════════════
print("\n[2] every multi-place eligible row through the real look_answer: graduate at one place, look at the other(s), back, name it")
bad2: list = []
n_seq = n_cross = 0
covered_rows: set = set()
for key in MULTI:
    r = ROWS[key]
    usable = [p for p in sorted(r["places"]) if alias_for(r, p) and plain_ref(key, p)]
    if len(usable) < 2:
        print(f"    (skipped {key}: usable places {usable} -- no alias or no line at the second place)")
        continue
    for a in usable:
        bs = [p for p in usable if p != a]
        steps = seq_for(key, a, bs)
        new, nb = run_seq(steps, None, "new")
        old, ob = run_seq(steps, None, "old")
        ref = {p: plain_ref(key, p) for p in usable}
        stop_a = end_sentence(ref[a])
        tag = f"[{key}: graduated at {a}, other {bs}]"
        got = [x["res"] for x in new]
        got_o = [x["res"] for x in old]
        # steps 0-3 plain, 4 the graduating look carries the line, then for each b: b plain, a suffixed; the naming; a named, each b plain
        quiet(got[:4] == [ref[a]] * 4, f"{tag} the first four looks at {a} are plain", bad2)
        quiet(got[4] == stop_a + SFX_UNNAMED and key in new[4]["state"].get("individuals", {}) and key not in new[3]["state"].get("individuals", {}),
              f"{tag} the fifth look at {a} graduates it and carries the line", bad2)
        i = 5
        for b in bs:
            quiet(got[i] == ref[b] and "same one" not in got[i] and "too often" not in got[i], f"{tag} the look at {b} is the plain line a creature that never graduated gives: {got[i][-70:]!r}", bad2)
            quiet(got_o[i] == end_sentence(ref[b]) + SFX_UNNAMED, f"{tag} (the old render DID say it at {b}: the defect, reproduced)", bad2)
            quiet(got[i + 1] == stop_a + SFX_UNNAMED, f"{tag} back at {a}: the line", bad2)
            n_cross += 1
            i += 2
        quiet(got[i].startswith("Bramble, then.") and f"at the {a}" in got[i], f"{tag} the name is given (give_name has no place): {got[i][:60]!r}", bad2)
        i += 1
        quiet(got[i] == stop_a + SFX_NAMED, f"{tag} named, at {a}: 'It is Bramble -- you would know it anywhere now.'", bad2)
        for j, b in enumerate(bs):
            quiet(got[i + 1 + j] == ref[b], f"{tag} named, at {b}: plain, no name claimed", bad2)
            quiet(got_o[i + 1 + j] == end_sentence(ref[b]) + SFX_NAMED, f"{tag} (old render: the named line at {b} too)", bad2)
        quiet(all(n["state"] == o["state"] and n["events"] == o["events"] and n["ledger"] == o["ledger"] for n, o in zip(new, old)) and nb == ob,
              f"{tag} state / ledger / events / saved bytes identical under the old and the new render", bad2)
        ind_end = new[-1]["state"]["individuals"][key]
        quiet(ind_end["place"] == a and new[4]["state"]["individuals"][key]["sightings"] == 5 and ind_end["sightings"] == len(steps) - 1,
              f"{tag} the record keeps its graduation place and every later sighting is still counted wherever it was (render-only): {ind_end['sightings']} vs {len(steps) - 1}", bad2)
        covered_rows.add(key)
        n_seq += 1
fresh_state()
for m_ in bad2[:14]:
    print("    !!", m_)
check(not bad2 and n_seq >= 28 and covered_rows >= F2305_MULTI, f"{n_seq} (row, graduation place) sequences over {len(covered_rows)} multi-place rows, {n_cross} cross-place looks: none says it away from home ({len(bad2)} failures)")
print("    rows covered:", sorted(covered_rows))
print("    rows with no usable second place (skipped):", sorted(set(MULTI) - covered_rows))

# ═══ [3] THE BEFORE / AFTER DIFFERENTIAL OVER ALL 58 ROWS ═══════════════════════════════════════════════════════
print("\n[3] the before/after differential: all 58 population rows, the same sequence under the old and the new render")
bad3: list = []
n_rows = n_same = n_diff = n_lines = 0
for key in sorted(POP):
    r = POP[key]
    usable = [p for p in sorted(r["places"]) if alias_for(r, p) and plain_ref(key, p)]
    if not usable:
        continue
    steps = seq_for(key, usable[0], usable[1:], d0=3)
    new, nb = run_seq(steps, None, "new")
    old, ob = run_seq(steps, None, "old")
    n_rows += 1
    quiet(all(n["state"] == o["state"] and n["events"] == o["events"] and n["ledger"] == o["ledger"] for n, o in zip(new, old)) and nb == ob,
          f"[{key}] world state, ledger, events and saved life_state.json bytes identical under both renders", bad3)
    home = usable[0]
    for n, o in zip(new, old):
        place = n["step"][2] if n["step"][0] == "look" else None
        n_lines += 1
        if n["res"] == o["res"]:
            n_same += 1
            continue
        # a difference is allowed in exactly one case: an eligible multi-place row, at a place that is not the one it graduated at, where the old
        # render appended the recognition line and the new one gives the plain look
        base_n = end_sentence(n["res"]) if isinstance(n["res"], str) else None
        suffix_old = o["res"][len(base_n):] if base_n is not None and isinstance(o["res"], str) and o["res"].startswith(base_n) else None
        ok = (key in ELIGIBLE and place is not None and place != home and suffix_old is not None
              and suffix_old in (SFX_UNNAMED, SFX_NAMED) and n["res"] == plain_ref(key, place))
        quiet(ok, f"[{key}@{place}] a differing line must be 'old = plain + recognition line, new = plain' at a non-home place of an eligible row: new {n['res'][-60:]!r}", bad3)
        n_diff += 1
    if len(usable) == 1:
        quiet(all(n["res"] == o["res"] for n, o in zip(new, old)), f"[{key}] single-place row: every line byte-identical to the old render", bad3)
fresh_state()
for m_ in bad3[:14]:
    print("    !!", m_)
n_single = sum(1 for k in POP if len([p for p in POP[k]["places"] if alias_for(POP[k], p) and plain_ref(k, p)]) == 1)
check(not bad3 and n_rows >= 50, f"{n_rows} rows, {n_lines} steps: {n_same} lines byte-identical, {n_diff} differ and every one of those is an other-place recognition line removed ({n_single} single-place rows identical throughout) ({len(bad3)} failures)")
check(n_diff >= 20, f"(the differential does exercise the change: {n_diff} other-place looks lost their recognition line)")

# ═══ [4] THE API CONTRACT ═══════════════════════════════════════════════════════════════════════════════════════
print("\n[4] individual_suffix / with_individual_suffix: the contract")
_OMIT = object()


def sfx(key, place=_OMIT):
    """individual_suffix, with the place argument omitted or given; a TypeError (the pre-J-1698 signature) is a failed check, not a crash."""
    try:
        return LT.individual_suffix(key) if place is _OMIT else LT.individual_suffix(key, place)
    except TypeError as exc:
        return f"<TypeError: {exc}>"


def wsfx(key, line, place=_OMIT):
    try:
        return LT.with_individual_suffix(key, line) if place is _OMIT else LT.with_individual_suffix(key, line, place)
    except TypeError as exc:
        return f"<TypeError: {exc}>"


sig_s, sig_w = inspect.signature(LT.individual_suffix), inspect.signature(LT.with_individual_suffix)
check("place" in sig_s.parameters and sig_s.parameters["place"].default is None and list(sig_s.parameters) == ["key", "place"], "individual_suffix(key, place=None)")
check("place" in sig_w.parameters and sig_w.parameters["place"].default is None and list(sig_w.parameters) == ["key", "line", "place"], "with_individual_suffix(key, line, place=None)")
fresh_state({"individuals": {
    "kereru": {"place": "wood", "since": 1.0, "name": None, "sightings": 5, "last_seen": 1.0, "history": []},
    "bellbird": {"place": "garden", "since": 1.0, "name": "Ash", "sightings": 5, "last_seen": 1.0, "history": []},
    "weta": {"since": 1.0, "name": None, "sightings": 5, "last_seen": 1.0, "history": []},      # an old-format record that stored no place
    "gulls": {"place": "shore", "since": 1.0, "name": None, "sightings": 7, "last_seen": 1.0, "history": []},     # dormant (group grain)
}})
S1 = SFX_UNNAMED
ASH = " It is Ash — you would know it anywhere now."
check(sfx("kereru") == S1 and sfx("kereru", None) == S1 and sfx("kereru", "") == S1,
      "no place (omitted / None / empty) = today's behaviour: the line (naming, the HUD and every caller without a look place are unchanged)")
check(sfx("kereru", "wood") == S1, "at the record's place: the line")
check(sfx("kereru", "garden") == "" and sfx("kereru", "shore") == "" and sfx("kereru", "study") == "", "at any other place: ''")
check(sfx("bellbird") == ASH and sfx("bellbird", "garden") == ASH and sfx("bellbird", "wood") == "", "the NAMED line is scoped the same way")
check(all(sfx("weta", p) == S1 for p in ("study", "wood", "garden", None)), "an old record with no stored place keeps the line at any place (fail-open)")
check(all(sfx("gulls", p) == "" for p in ("shore", "garden", "wood", None, "")) and LT.individual("gulls") is None, "a dormant group-grain record: '' at every place, individual() still None")
check(sfx("rabbit", "garden") == "" and sfx("nosuchrow", "garden") == "" and sfx("cat", "study") == "", "a creature that is not an individual (a row, an unknown key, the external cat): ''")
check(wsfx("kereru", "a rustle in the canopy", "wood") == "a rustle in the canopy." + S1, "with_individual_suffix at home: the J-1166 join (a full stop, then the line)")
check(wsfx("kereru", "a rustle in the canopy.", "wood") == "a rustle in the canopy." + S1, "... and a line that already ends a sentence is not given a second stop")
check(wsfx("kereru", "  a rustle in the canopy  ", "garden") == "a rustle in the canopy", "away from home: exactly the old `line.strip()` of a creature that never graduated (no stop added)")
check(wsfx("kereru", "a rustle in the canopy") == "a rustle in the canopy." + S1, "no place: the legacy join, unchanged")
check(wsfx("rabbit", " a line ", "garden") == "a line", "not an individual: the plain strip")
named = LT.give_name("kereru", "Bramble", 2.0)
check(named.startswith("Bramble, then.") and "at the wood" in named and LT.individual("kereru")["name"] == "Bramble",
      f"give_name takes no place and still names the record: {named[:64]!r}")
check(sfx("kereru") == SFX_NAMED and sfx("kereru", "wood") == SFX_NAMED and sfx("kereru", "garden") == "",
      "... and the name Du gave is said at the record's place only")
check(sorted(LT.hud_payload(5.0)["individuals"]) == ["bellbird", "kereru", "weta"], "hud_payload takes no place and lists every live individual (the dormant gulls unlisted)")
fresh_state()

# ═══ [5] ISOLATION PROOF ════════════════════════════════════════════════════════════════════════════════════════
print("\n[5] isolation")
for _m, _a in _REDIRECTS:
    check(_inside(getattr(_m, _a)), f"{_m.__name__}.{_a} still inside the temp dir")
life.note_deed(MARKER, "garden")
life._save(force=True)
check(MARKER in (TMP / "life_state.json").read_text(encoding="utf-8"), "the marker reached the isolated store through the engine's own write path")
_watch = [_LIVE_DATA / f for f in ("life_state.json", "life_ledger.jsonl", "life_events.jsonl", "room_state.json", "world_objects.json",
                                   "world_substrate.json", "provisions.json", "sound_knowledge.json", "world_traces.json", "position.json", "soundscape_state.json")]
leaked = [p.name for p in _watch if p.exists() and MARKER.encode() in p.read_bytes()]
check(not leaked, f"the marker appears in no live store ({len(_watch)} watched){' -> ' + str(leaked) if leaked else ''}")
check(not LIVE_WRITE_ATTEMPTS, f"the audit hook saw NO write attempt under any data/ ({len(LIVE_WRITE_ATTEMPTS)} attempts){' -> ' + str(LIVE_WRITE_ATTEMPTS[:3]) if LIVE_WRITE_ATTEMPTS else ''}")
_after = {p: _md5(p) for p in _LIVE_FILES}
for p in _LIVE_FILES:
    print(f"    md5 {p.name:22s} before {_before[p][:12] or '(absent)':12s} after {_after[p][:12] or '(absent)':12s}"
          + ("" if _before[p] == _after[p] else "   <- changed by a live writer, not this process; the audit hook above is the real proof"))
for _p in (ROOT / "core" / "life.py", ROOT / "core" / "life_traces.py", Path(__file__)):
    try:
        py_compile.compile(str(_p), cfile=str(TMP / (_p.name + "c")), doraise=True)
        check(True, f"py_compile {_p.name}")
    except py_compile.PyCompileError as exc:
        check(False, f"py_compile {_p.name}: {exc}")

print(f"\n{'ALL OK' if not FAILS else f'{FAILS} FAILURE(S)'} — {CHECKS} checks — isolated stores in {TMP}")
sys.exit(1 if FAILS else 0)
