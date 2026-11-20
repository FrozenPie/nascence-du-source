"""
Regression: J-1766 (D-0335) -- GRADUATION TO 'THE SAME ONE' COUNTS DISTINCT ENCOUNTERS, N = 30 MINUTES (a read-time rule; supersedes D-0247's raw counting).

THE RULING (Travis, /decide-review 2026-10-04: "Encounters, N = 30 min"). A sighting counts toward a row's graduation only if it is at least 30 minutes after the
last COUNTED sighting, computed at READ time from the stored recent_sightings list (no migration of stored counts, no rewriting of life_state.json). The flock /
swarm / plural bar (J-1174) is untouched. J-1192's replay of the real sightings (F-2304): the korora@shore graduation is delayed 23.2 h, the tui@garden 3 d 23.9 h,
the blackbird@garden is unaffected (its two close sightings are 73 minutes apart).

THE BUILD (core/life_traces.py): GRADUATE_ENCOUNTER_GAP_S (the one named N), counted_sightings(stamps) (the greedy chain from the last COUNTED look), and
note_sighting's graduation test reading len(counted_sightings(rec)) instead of len(rec). The stored list stays RAW (every rendered look, as before); its cap moved
20 -> GRADUATE_LIST_MAX because uncounted looks now stay in it. NOTHING already stored is re-judged: individual() / individual_suffix / hud_payload / naming read a
record exactly as before -- the rule is read only at the moment a graduation is DECIDED.

  [0] module resolution + isolation set-up (the code under test is THIS root's)
  [1] counted_sightings: the chain (boundary, not pairwise, order, gap 0 = raw)
  [2] note_sighting, direct: a burst is one encounter; distinct encounters graduate on the fifth exactly as before; legacy raw lists; the window; the cap; N = 0
  [3] the real look_answer: a burst of looks says nothing, the fifth ENCOUNTER carries the recognition line
  [4] the REAL stored records (data/life_state.json, a read-only copy): nothing Du already has is hidden; the rows next to graduating
  [5] the REAL sightings replayed (life_events.jsonl, frozen at 2026-10-04 07:00): raw reproduces the live graduations; N = 30 min gives the ruling's figures
  [6] isolation: audit hook (0 write attempts under any data/), live-file hashes, py_compile

ISOLATION. The temp-redirect + audit-hook design J-1166 / J-1174 / J-1698 used: every store the engine can reach is redirected into a temp dir before anything can
write, and a Python audit hook records any attempt by THIS process to open-for-write / rename / remove anything under a data/ directory. The live C:\\Nascence\\data
files are only ever READ (md5-hashed before and after). Run it from the worktree (never from the shared tree): the code under test is the root of THIS file.

  python scripts/_test_j1766_graduation_encounters.py              # exit 0 = ALL OK
"""
from __future__ import annotations

import contextlib
import copy
import datetime
import hashlib
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

TMP = Path(tempfile.mkdtemp(prefix="j1766_graduation_encounters_"))
print("isolated store dir:", TMP)
MARKER = f"j1766_marker_{os.getpid()}"
# data/ is gitignored and never checked out into a job-run worktree, so "live" is the one real repo, never ROOT-relative (read-only here).
_LIVE_DATA = Path(r"C:\Nascence") / "data"
_LIVE_FILES = [_LIVE_DATA / f for f in ("position.json", "room_state.json", "life_state.json", "life_ledger.jsonl", "life_events.jsonl", "world_traces.json",
                                        "life_flags.json", "wandering_log.jsonl", "sound_knowledge.json", "hands_trace.jsonl",
                                        "satisfaction_log.jsonl", "satisfaction_state.json")]   # the last two: F-2406 (core/satisfaction.py is unfenced)


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
                 "shutil.copyfile", "shutil.copymode", "shutil.copystat", "shutil.copytree", "shutil.move", "shutil.rmtree"}
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

# ── redirect every store the engine can reach BEFORE anything can write (the vetted list of J-1166 / J-1174 / J-1698) ──
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
life._FLAGS_F = TMP / "life_flags.json"
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


def hm(month: int, day: int, hour: int, minute: int = 0, sec: int = 0, year: int = 2026) -> float:
    return time.mktime((year, month, day, hour, minute, sec, 0, 0, -1))


def fmt(t: float) -> str:
    return datetime.datetime.fromtimestamp(t).strftime("%m-%d %H:%M:%S")


def _inside(p) -> bool:
    q = Path(str(p))
    return q == TMP or TMP in q.parents


M, H, D = 60.0, 3600.0, 86400.0

# ── [0] module resolution ────────────────────────────────────────────────────────────────────────────────────────
print("\n[0] module resolution: the code under test is THIS root's, not the shared tree's")
print("    sys.path[0] =", sys.path[0])
for _m in (core, profile, life, LT, WT, life_birds, life_mammals, garden_insects, garden_soil, S, L, SK, SC, WC):
    _f = getattr(_m, "__file__", None)
    check(_f is not None and Path(_f).resolve().is_relative_to(ROOT), f"{_m.__name__} was loaded from inside {ROOT}")
for _m, _a in _REDIRECTS:
    check(_inside(getattr(_m, _a)), f"{_m.__name__}.{_a} redirected into the temp dir")

ROWS = life.rows()
POP = {k: r for k, r in ROWS.items() if r.get("kind") == "population"}
ELIGIBLE = {k for k, r in POP.items() if not LT.group_grain(r)}
BARRED = set(POP) - ELIGIBLE
life.RENDER = True
check(len(POP) == 58 and len(ELIGIBLE) == 32 and len(BARRED) == 26, f"58 population rows = 32 eligible + 26 barred (group grain) -- the J-1174 partition, untouched ({len(POP)}, {len(ELIGIBLE)}, {len(BARRED)})")


def events() -> list:
    if not life._EVENTS.exists():
        return []
    return [json.loads(x) for x in life._EVENTS.read_text(encoding="utf-8").splitlines() if x.strip()]


def ledger_rows() -> list:
    if not life._LEDGER.exists():
        return []
    return [json.loads(x) for x in life._LEDGER.read_text(encoding="utf-8").splitlines() if x.strip()]


def fresh_state(seed: dict | None = None) -> None:
    """An empty world state and empty logs (never `life._state = {}` + _load(): that would re-read the temp file a graduation just saved).
    `seed` = top-level keys of life_state.json to plant (individuals, recent_sightings), deep-copied."""
    life._state = {"rows": {}, "dark": {"since": 0.0, "place": None, "adapt": 0.0}, "_last": 0.0}
    for p in (life._EVENTS, life._LEDGER, life._F):
        if p.exists():
            p.unlink()
    for k, v in (seed or {}).items():
        life._state[k] = copy.deepcopy(v)


# ── [1] counted_sightings ────────────────────────────────────────────────────────────────────────────────────────
print("\n[1] counted_sightings: the chain from the last COUNTED look")
check(hasattr(LT, "counted_sightings") and hasattr(LT, "GRADUATE_ENCOUNTER_GAP_S"), "the build is present: LT.counted_sightings and LT.GRADUATE_ENCOUNTER_GAP_S exist")
cs = getattr(LT, "counted_sightings", lambda stamps, gap_s=None: sorted(stamps or ()))      # a base-commit run shims 'raw' so every later check FAILS on behaviour, not on a crash
check(getattr(LT, "GRADUATE_ENCOUNTER_GAP_S", None) == 1800.0, "N is ONE named constant: 30 minutes = 1800 s")
if not hasattr(LT, "GRADUATE_ENCOUNTER_GAP_S"):
    LT.GRADUATE_ENCOUNTER_GAP_S = 0.0           # a base-commit run only: the old trigger is raw counting, so the shim is faithful and the later checks fail on behaviour
check(LT.GRADUATE_SIGHTINGS == 5 and LT.GRADUATE_WINDOW_S == 30 * D, "the other two graduation constants are untouched: five, thirty days")
check(cs([]) == [] and cs(None) == [], "no looks -> no counted looks (and None does not raise)")
check(cs([100.0]) == [100.0], "one look counts")
check(cs([0.0, 1800.0]) == [0.0, 1800.0], "exactly N after the last counted look counts: at least N")
check(cs([0.0, 1799.9]) == [0.0], "a hair under N does not")
check(cs([0.0, 20 * M, 40 * M]) == [0.0, 40 * M], "the chain runs from the last COUNTED look, not pairwise: looks at 0, 20 and 40 minutes count 0 and 40")
check(cs([0.0, 29 * M, 31 * M, 61 * M]) == [0.0, 31 * M, 61 * M], "0 counts; 29 does not; 31 does (31 after 0); 61 does (30 after 31)")
check(cs([40 * M, 0.0, 20 * M]) == [0.0, 40 * M], "time order, whatever order the list is stored in")
check(cs([60.0 * i for i in range(100)]) == [0.0, 1800.0, 3600.0, 5400.0], "100 looks a minute apart are four encounters")
check(cs([0.0, 5.0, 10.0], gap_s=0.0) == [0.0, 5.0, 10.0], "gap 0 counts every look: the pre-D-0335 raw counting")
_stored = [0.0, 5.0, 3000.0]
_stored_copy = list(_stored)
cs(_stored)
check(_stored == _stored_copy, "read-only: the stored list is not rewritten or reordered by counting it")

# ── [2] note_sighting, direct ────────────────────────────────────────────────────────────────────────────────────
print("\n[2] note_sighting, direct")
KEY, PLACE = "hedgehog", "garden"
LISTK = f"{KEY}@{PLACE}"
check(KEY in ELIGIBLE and PLACE in ROWS[KEY]["places"], f"{KEY}@{PLACE} is an eligible population row (the one life_smoke graduates)")


def feed(stamps, key=KEY, place=PLACE) -> list:
    return [LT.note_sighting(key, place, t) for t in stamps]


T0 = hm(10, 2, 9, 0)
fresh_state()
burst = [T0 + 60 * i for i in range(5)]
check(feed(burst) == [False] * 5 and LT.individual(KEY) is None, "[burst] five looks a minute apart are ONE encounter: no graduation (the raw rule graduated on the fifth)")
check(life._state["recent_sightings"][LISTK] == burst, "[burst] ... and the stored list is still RAW: all five looks, as written (nothing migrated, nothing dropped)")
check(not ledger_rows() and not any(e.get("kind") == "graduated" for e in events()), "[burst] no ledger row, no event")
more = [T0 + 2100, T0 + 4200, T0 + 6300, T0 + 8400]
check(feed(more) == [False, False, False, True], "[burst] then four looks 35 minutes apart: each is a new encounter; the fifth ENCOUNTER (the ninth look) graduates it")
rec = life._load()["individuals"][KEY]
check(rec == {"place": PLACE, "since": T0 + 8400, "name": None, "sightings": 9, "last_seen": T0 + 8400,
              "history": [{"ts": T0 + 8400, "event": "recognised: the same one at the garden, 5 times in a month"}]},
      "[burst] the record: the graduating look's time, sightings = the 9 raw looks (the HUD's own look counter), history names the 5 encounters")
_gl = [x for x in ledger_rows() if x.get("kind") == "graduated"]
check(len(_gl) == 1 and _gl[0].get("key") == KEY and _gl[0].get("place") == PLACE and _gl[0].get("sightings") == 9, "[burst] exactly one 'graduated' ledger row (its sightings = the raw looks, as the record's)")
check(feed([T0 + 8401, T0 + 8402]) == [False, False] and life._load()["individuals"][KEY]["sightings"] == 11 and life._load()["individuals"][KEY]["last_seen"] == T0 + 8402,
      "[after] a graduated row keeps counting EVERY look in its own counter, one second apart or not (the HUD figure is raw, as before)")

fresh_state()
days = [hm(10, 1 + i, 12) for i in range(5)]
check(feed(days) == [False, False, False, False, True], "[days] five looks on five different days graduate on exactly the fifth, as before")
check(life._load()["individuals"][KEY] == {"place": PLACE, "since": days[-1], "name": None, "sightings": 5, "last_seen": days[-1],
                                           "history": [{"ts": days[-1], "event": "recognised: the same one at the garden, 5 times in a month"}]},
      "[days] ... and the record is byte-identical to what the raw rule wrote when every look was a new encounter")

fresh_state()
check(feed([T0 + 1800 * i for i in range(5)]) == [False] * 4 + [True], "[boundary] five looks exactly N (1800 s) apart: every one counts (at least N), the fifth graduates")
fresh_state()
check(feed([T0 + 1799 * i for i in range(9)]) == [False] * 8 + [True], "[boundary] looks 1799 s apart: only every second one counts, so the NINTH look is the fifth encounter")

fresh_state({"recent_sightings": {LISTK: [T0, T0 + 300, T0 + 600, T0 + D]}})
check(feed([T0 + 2 * D]) == [False] and LT.individual(KEY) is None,
      "[legacy] a stored RAW list is judged by the same rule at read time: 4 stored looks + this one were five looks (the old rule graduated) but are 3 encounters")
check(life._state["recent_sightings"][LISTK] == [T0, T0 + 300, T0 + 600, T0 + D, T0 + 2 * D], "[legacy] ... and the legacy entries are untouched: only the new look was appended")
check(feed([T0 + 3 * D, T0 + 4 * D]) == [False, True], "[legacy] two more encounters: the fifth encounter graduates it")

fresh_state()
feed([hm(10, 1, 12) + i * D for i in range(4)])
check(feed([hm(10, 1, 12) + 30 * D]) == [True], "[window] a look exactly 30 days after the first still counts it (the window is unchanged): 5 encounters")
fresh_state()
feed([hm(10, 1, 12) + i * D for i in range(4)])
check(feed([hm(10, 1, 12) + 30 * D + 1]) == [False] and len(life._state["recent_sightings"][LISTK]) == 4,
      "[window] a look 30 days and a second after the first no longer counts it: 4 encounters (the 30-day window is unchanged)")

for _k, _p in (("honeybee", "garden"), ("gulls", "shore")):
    fresh_state()
    _before_state = copy.deepcopy(life._state)
    _r = feed([T0 + 6 * H * i for i in range(5)] + [T0 + D * 3], key=_k, place=_p)
    check(_r == [False] * 6 and life._state == _before_state, f"[bar] {_k}@{_p}: a flock/swarm/plural row still never graduates and nothing is written for it (the J-1174 bar, untouched)")

STARE = lambda day: [hm(10, day, 9, 0) + 10 * i for i in range(30)]       # an encounter of 30 looks, 10 s apart
fresh_state()
_stares = STARE(1) + STARE(2) + STARE(3) + STARE(4)
check(feed(_stares) == [False] * 120 and len(life._state["recent_sightings"][LISTK]) == getattr(LT, "GRADUATE_LIST_MAX", 20) == 100,
      "[cap] four encounters of 30 looks each (120 looks): no graduation, and the raw list holds the last GRADUATE_LIST_MAX = 100")
check(feed([hm(10, 5, 9, 0)]) == [True], "[cap] the fifth visit graduates it: the cap did not evict a counted encounter")
fresh_state()
_real_max = getattr(LT, "GRADUATE_LIST_MAX", 20)
LT.GRADUATE_LIST_MAX = 20                                                    # the pre-J-1766 bare 20
try:
    feed(_stares)
    _starved = feed([hm(10, 5, 9, 0)])
finally:
    LT.GRADUATE_LIST_MAX = _real_max
check(_starved == [False], "[cap] (with the old bare 20-look cap the same history starves: only the last visit's looks survive -- why the cap had to move)")

fresh_state()
_real_gap = LT.GRADUATE_ENCOUNTER_GAP_S
LT.GRADUATE_ENCOUNTER_GAP_S = 0.0
try:
    _raw = feed([T0 + i for i in range(5)])
finally:
    LT.GRADUATE_ENCOUNTER_GAP_S = _real_gap
check(_raw == [False] * 4 + [True] and LT.GRADUATE_ENCOUNTER_GAP_S == 1800.0, "[N] N = 0 is exactly the old raw counting (five looks a second apart graduate): the one constant is the whole rule")
check("counted" not in json.dumps(life._state) and "encounter" not in json.dumps(life._state), "[state] nothing about the rule is stored: no new key anywhere in life_state")

# ── [3] the real look_answer ─────────────────────────────────────────────────────────────────────────────────────
print("\n[3] the real look_answer: a burst says nothing, the fifth ENCOUNTER carries the recognition line")
_real_activity, _real_visibility, _real_random = life.activity, life.visibility, random.random


@contextlib.contextmanager
def forced(act=0.9, vis=0.9, roll=0.0):
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


def day_line(r: dict, place: str) -> str:
    h = (r.get("hidden") or {})
    by_place = (h.get("feature_by_place") or {}).get(place)
    feat = by_place if isinstance(by_place, dict) else (h.get("feature") or {})
    return feat.get("day") or feat.get("any") or ""


pick = next(((k, p) for k in ("tui", "blackbird", "kingfisher", "robin", "shag", "oystercatcher") if k in ELIGIBLE
             for p in sorted(ROWS[k]["places"]) if alias_for(ROWS[k], p) and day_line(ROWS[k], p)), None)
check(pick is not None, f"an eligible row with a 'day' look line and an alias at its place: {pick}")
if pick:
    gkey, gplace = pick
    gtgt = alias_for(ROWS[gkey], gplace)
    SFX = " It is the same one — you are sure of it now; you have seen it here too often for it to be any other."
    LOOKS = [0, 60, 120, 180, 240, 2100, 4200, 6300, 8400]            # a burst of five, then four more visits 35 minutes apart
    base = next((hm(10, 3, h0, 20) for h0 in range(5, 15) if all(life._phase(hm(10, 3, h0, 20) + o) == "day" for o in (0, LOOKS[-1] + 120))), None)
    check(base is not None, "a start time inside one 'day' phase for the whole 2 h 20 m sequence (the look line must not change phase mid-sequence)")
    fresh_state()
    with forced(roll=0.0):
        got = [life.look_answer(gtgt, gplace, base + o) for o in LOOKS]
    plain = got[0]
    check(bool(plain) and plain.strip() == day_line(ROWS[gkey], gplace).strip(), f"[{gkey}@{gplace}] the first look is the row's plain 'day' look line: {plain[:70]!r}")
    check(all(g == plain for g in got[:8]) and "same one" not in "".join(got[:8]),
          f"[{gkey}@{gplace}] the first EIGHT looks (a burst of five, then three more visits) are the plain look line: nothing is said")
    check(got[8] == LT._end_sentence(plain) + SFX, f"[{gkey}@{gplace}] the NINTH look, the fifth encounter, carries the punctuated recognition line: {got[8][-60:]!r}")
    _rec = life._load()["individuals"].get(gkey, {})
    check(_rec.get("sightings") == 9 and _rec.get("history", [{}])[0].get("event", "").endswith("5 times in a month") and _rec.get("place") == gplace,
          f"[{gkey}@{gplace}] the record: 9 raw looks, '5 times in a month', at {gplace}")
    check(sum(1 for x in ledger_rows() if x.get("kind") == "graduated" and x.get("key") == gkey) == 1
          and sum(1 for x in ledger_rows() if x.get("kind") == "sighting" and x.get("key") == gkey) == 9, f"[{gkey}] one graduated row, and every one of the nine looks still credited his ledger a sighting (a name is learned from a face)")
    fresh_state()
    with forced(roll=0.0):
        burst_only = [life.look_answer(gtgt, gplace, base + 60 * i) for i in range(5)]
    check(all(g == plain for g in burst_only) and LT.individual(gkey) is None and len(life._load()["recent_sightings"][f"{gkey}@{gplace}"]) == 5,
          f"[{gkey}@{gplace}] five looks a minute apart through the engine: all plain, not an individual, five raw looks kept")
    fresh_state()

# ── [4] the REAL stored records ──────────────────────────────────────────────────────────────────────────────────
print("\n[4] the REAL stored records (data/life_state.json, a read-only copy): nothing Du already has is hidden")
_FIXTURE_IND = {       # the six records exactly as data/life_state.json held them at its 2026-10-04 06:53:25 save (Du down since 06:56)
    'oystercatcher': {'place': 'shore', 'since': 1789063410.715861, 'name': None, 'sightings': 101, 'last_seen': 1790789804.3940473, 'history': [{'ts': 1789063410.715861, 'event': 'recognised: the same one at the shore, 5 times in a month'}]},
    'honeybee': {'place': 'garden', 'since': 1789613190.7415783, 'name': None, 'sightings': 7, 'last_seen': 1789621243.7975354, 'history': [{'ts': 1789613190.7415783, 'event': 'recognised: the same one at the garden, 5 times in a month'}]},
    'gulls': {'place': 'shore', 'since': 1789767551.9992964, 'name': None, 'sightings': 7, 'last_seen': 1789775354.766397, 'history': [{'ts': 1789767551.9992964, 'event': 'recognised: the same one at the shore, 5 times in a month'}]},
    'tui': {'place': 'garden', 'since': 1790129512.286302, 'name': None, 'sightings': 8, 'last_seen': 1790564728.747828, 'history': [{'ts': 1790129512.286302, 'event': 'recognised: the same one at the garden, 5 times in a month'}]},
    'blackbird': {'place': 'garden', 'since': 1790272192.0484016, 'name': None, 'sightings': 6, 'last_seen': 1790477151.7781215, 'history': [{'ts': 1790272192.0484016, 'event': 'recognised: the same one at the garden, 5 times in a month'}]},
    'korora': {'place': 'shore', 'since': 1790436513.5255497, 'name': None, 'sightings': 6, 'last_seen': 1790520173.5544717, 'history': [{'ts': 1790436513.5255497, 'event': 'recognised: the same one at the shore, 5 times in a month'}]},
}
_FIXTURE_REC = {
    'oystercatcher@shore': [1788981309.4449792, 1788982128.2554054, 1789010015.229655, 1789017040.6525247, 1789063410.715861],
    'honeybee@garden': [1788985795.1535926, 1789163530.4466956, 1789521383.9074042, 1789613184.257962, 1789613190.7415783],
    'gulls@shore': [1788980980.6102147, 1789003029.134549, 1789082073.5832336, 1789194818.9291916, 1789767551.9992964],
    'tui@garden': [1789170537.1791415, 1789962449.7755628, 1790014036.2195208, 1790128991.88916, 1790129512.286302],
    'blackbird@garden': [1789007988.1233404, 1789012364.8353944, 1789526721.943758, 1790195366.8687577, 1790272192.0484016],
    'korora@shore': [1789030520.3607662, 1789623438.815779, 1789623511.107338, 1790172991.4602587, 1790436513.5255497],
    'robin@wood': [1789615946.1118941, 1790012959.583392, 1790469908.0982876, 1790473238.45621],
    'shag@shore': [1789012642.935043, 1789524963.9067352, 1790130300.8830326, 1790392582.7314382],
    'kingfisher@shore': [1789150549.0328197, 1790461056.7283933, 1790563130.0651872],
    'kereru@wood': [1790444067.91089, 1790536891.997445],
}
try:
    _live = json.loads((_LIVE_DATA / "life_state.json").read_text(encoding="utf-8"))
    _src = "the live file, read just now"
except Exception:
    _live, _src = {}, "the embedded copy (the live file was not readable)"
LIVE_IND = copy.deepcopy(_live.get("individuals")) if all(k in (_live.get("individuals") or {}) for k in _FIXTURE_IND) else copy.deepcopy(_FIXTURE_IND)
LIVE_REC = copy.deepcopy(_live.get("recent_sightings")) if _live.get("recent_sightings") and LIVE_IND is not None and all(k in (_live.get("recent_sightings") or {}) for k in _FIXTURE_REC) else copy.deepcopy(_FIXTURE_REC)
print(f"    source: {_src}; {len(LIVE_IND)} stored individuals {sorted(LIVE_IND)}; {len(LIVE_REC)} recent_sightings lists")
check(all(LIVE_IND[k]["place"] == _FIXTURE_IND[k]["place"] for k in _FIXTURE_IND), "the six stored records are the ones F-2304 read (same places)")


def stored_checks(ind: dict, rec: dict, label: str) -> None:
    fresh_state({"individuals": ind, "recent_sightings": rec})
    live_keys = {k for k in ind if not LT.group_grain(ROWS.get(k))}
    dormant = set(ind) - live_keys
    check(all(LT.individual(k) == ind[k] for k in live_keys), f"[{label}] individual() returns every stored graduation exactly as stored: {sorted(live_keys)} -- NONE hidden")
    check(all(LT.individual(k) is None for k in dormant), f"[{label}] ... and the dormant group-grain records stay dormant exactly as J-1174 left them: {sorted(dormant)}")
    check(all(LT.individual_suffix(k, ind[k]["place"]).startswith(" It is the same one") for k in live_keys),
          f"[{label}] the recognition line is still said, at home, for every live individual (nothing has been un-graduated)")
    check(set(LT.hud_payload(hm(10, 4, 7))["individuals"]) == live_keys, f"[{label}] the HUD still lists the same individuals: {sorted(LT.hud_payload(hm(10, 4, 7))['individuals'])}")
    snap = copy.deepcopy(life._state["individuals"])
    for k in sorted(live_keys):
        LT.note_sighting(k, ind[k]["place"], hm(10, 4, 7) + 1)
    bumped = all(life._state["individuals"][k]["sightings"] == snap[k]["sightings"] + 1 and life._state["individuals"][k]["place"] == snap[k]["place"]
                 and life._state["individuals"][k]["since"] == snap[k]["since"] for k in live_keys)
    check(bumped and life._state["recent_sightings"] == rec, f"[{label}] a look at a stored individual only bumps its own counter: not re-judged, not un-graduated, the stored lists untouched")
    fresh_state()


stored_checks(LIVE_IND, LIVE_REC, "stored state")
if _src.startswith("the live") and (LIVE_IND != _FIXTURE_IND or LIVE_REC != _FIXTURE_REC):
    stored_checks(_FIXTURE_IND, _FIXTURE_REC, "2026-10-04 06:53 snapshot")
print("    raw looks vs counted encounters (N = 30 min) in each stored graduation's own list -- what a rule that RE-JUDGED stored records would do:")
_WOULD_HIDE = []
for k in ("oystercatcher", "tui", "blackbird", "korora", "honeybee", "gulls"):
    lst = _FIXTURE_REC[f"{k}@{_FIXTURE_IND[k]['place']}"]
    n = len(cs(lst))
    print(f"      {k:14s} raw {len(lst)}  counted {n}  {'<- would LOSE its graduation if stored records were re-judged' if n < 5 else ''}")
    if n < 5 and not LT.group_grain(ROWS[k]):
        _WOULD_HIDE.append(k)
check(sorted(_WOULD_HIDE) == ["korora", "oystercatcher", "tui"],
      "a rule that re-judged STORED records would hide 3 of the 4 live individuals (the oystercatcher, the tui and the korora) -- which is why the rule is read ONLY when a graduation is decided")
fresh_state({"individuals": _FIXTURE_IND, "recent_sightings": _FIXTURE_REC})
_robin_last = _FIXTURE_REC["robin@wood"][-1]
check("robin" in ELIGIBLE and "shag" in ELIGIBLE and len(_FIXTURE_REC["robin@wood"]) == 4 and len(cs(_FIXTURE_REC["robin@wood"])) == 4 and len(cs(_FIXTURE_REC["shag@shore"])) == 4,
      "the robin@wood and the shag@shore lists are 4 counted encounters each (the robin's last two looks are 55 minutes apart: both count): one encounter from graduating")
check(LT.note_sighting("robin", "wood", _robin_last + 10 * M) is False and LT.individual("robin") is None,
      "robin: a look 10 minutes after its last is the SAME encounter -- not graduated")
check(LT.note_sighting("robin", "wood", _robin_last + 31 * M) is True and LT.individual("robin")["since"] == _robin_last + 31 * M and LT.individual("robin")["sightings"] == 6,
      "robin: the next look 31 minutes after its last counted one is the fifth encounter -- graduated (the first natural test once live)")
check(LT.note_sighting("shag", "shore", _FIXTURE_REC["shag@shore"][-1] + 2 * D) is True and LT.individual("shag") is not None,
      "shag: its next sighting graduates it (its four stored looks are days apart)")
check(LT.note_sighting("kingfisher", "shore", _FIXTURE_REC["kingfisher@shore"][-1] + 2 * D) is False and LT.individual("kingfisher") is None,
      "kingfisher (3 encounters stored): a fourth does not graduate it")
fresh_state()

# ── [5] the REAL sightings replayed ──────────────────────────────────────────────────────────────────────────────
print("\n[5] the REAL sightings (life_events.jsonl, frozen at 2026-10-04 07:00) replayed through note_sighting in timestamp order")
CUTOFF = hm(10, 4, 7, 0)
live_rows: list = []
_le = _LIVE_DATA / "life_events.jsonl"
if _le.exists():
    with open(_le, encoding="utf-8") as f:
        for x in f:
            try:
                live_rows.append(json.loads(x))
            except Exception:
                pass
sightings = sorted((float(e["ts"]), e["key"], e["place"]) for e in live_rows if e.get("kind") == "answer" and e.get("outcome") == "sighting"
                   and e.get("key") in ROWS and float(e["ts"]) <= CUTOFF)
grad_live = {e["key"]: float(e["ts"]) for e in live_rows if e.get("kind") == "graduated" and float(e["ts"]) <= CUTOFF}
if len(sightings) < 100:
    print(f"    (only {len(sightings)} rendered sightings readable -- life_events.jsonl missing or rotated; replay skipped, NOT a pass)")
else:
    def replay(gap_s: float | None = None) -> dict:
        """gap_s None = the module's own default N, unpatched."""
        fresh_state()
        real = LT.GRADUATE_ENCOUNTER_GAP_S
        if gap_s is not None:
            LT.GRADUATE_ENCOUNTER_GAP_S = gap_s
        try:
            out = {}
            for ts, key, place in sightings:
                if LT.note_sighting(key, place, ts):
                    out[key] = ts
            return out
        finally:
            LT.GRADUATE_ENCOUNTER_GAP_S = real

    raw_g = replay(0.0)
    new_g = replay()                                    # the module's own default N, unpatched
    cur_g = replay(1800.0)
    print(f"    {len(sightings)} rendered sightings replayed; the live store recorded graduations: {{{', '.join(f'{k}: {fmt(v)}' for k, v in sorted(grad_live.items()))}}}")
    print(f"    raw counting (N = 0), group bar on : {{{', '.join(f'{k}: {fmt(v)}' for k, v in sorted(raw_g.items()))}}}")
    print(f"    N = 30 min (this code)             : {{{', '.join(f'{k}: {fmt(v)}' for k, v in sorted(new_g.items()))}}}")
    FOUR = {"oystercatcher", "tui", "blackbird", "korora"}
    check(set(raw_g) == FOUR and all(abs(raw_g[k] - grad_live[k]) < 1.0 for k in FOUR),
          "the replay is FAITHFUL: raw counting (the pre-D-0335 trigger, group bar on) reproduces the four live non-group graduations to the second (honeybee and gulls graduated before the bar)")
    check(new_g == cur_g, "the module's own default N (unpatched) gives the same replay as an explicit N = 1800 s")
    check(set(new_g) == FOUR, f"N = 30 min: the same four rows graduate and no other row does: {sorted(new_g)}")
    check(not (set(new_g) & BARRED), "no flock, swarm or plural row graduates (the bar that held: honeybee and gulls stay dormant)")
    d_tui, d_kor, d_bb, d_oyc = (new_g[k] - raw_g[k] for k in ("tui", "korora", "blackbird", "oystercatcher"))
    _wall = datetime.datetime.fromtimestamp(new_g["tui"]) - datetime.datetime.fromtimestamp(raw_g["tui"])
    print(f"    delays vs raw (elapsed): tui +{d_tui / H:.2f} h (wall-clock {_wall}), korora +{d_kor / H:.2f} h, blackbird +{d_bb:.0f} s, oystercatcher +{d_oyc / H:.2f} h")
    # absolute epoch instants (timezone-independent). The ruling's '3 d 23.9 h' for the tui is a WALL-CLOCK difference (3 d 23:52:11); New Zealand daylight saving began
    # 2026-09-27 02:00, between the two instants, so the ELAPSED delay is one hour less: 341,531 s = 94.87 h = 3 d 22.9 h. The korora and the oystercatcher are unaffected.
    check(abs(new_g["tui"] - 1790471043.0) < 1.0 and abs(d_tui - 341531.0) < 1.0,
          "tui@garden graduates at 09-27 14:04:03 (3 d 23:52:11 of wall-clock later than it did: the ruling's 3 d 23.9 h; 94.87 h elapsed, NZ daylight saving began in between)")
    check(abs(new_g["korora"] - 1790520173.0) < 1.0 and abs(d_kor - 83660.0) < 1.0, "korora@shore graduates at 09-28 03:42:53, 23.2 h (83,660 s) later than it did -- the ruling's figure")
    check(abs(d_bb) < 1.0 and abs(new_g["blackbird"] - grad_live["blackbird"]) < 1.0, "blackbird@garden is UNAFFECTED (its two close sightings are 73 minutes apart): graduates at the same instant, 09-25 05:49:52")
    check(abs(new_g["oystercatcher"] - 1789068579.0) < 1.0 and abs(d_oyc - 5169.0) < 1.0,
          "oystercatcher@shore graduates at 09-11 07:29:39 (F-1680's N = 30 min figure), 1 h 26 m later than it did")
    fresh_state()

# ── [6] isolation proof ──────────────────────────────────────────────────────────────────────────────────────────
print("\n[6] isolation")
for _m, _a in _REDIRECTS:
    check(_inside(getattr(_m, _a)), f"{_m.__name__}.{_a} still inside the temp dir")
life.note_deed(MARKER, "garden")
life._save(force=True)
check(MARKER in (TMP / "life_state.json").read_text(encoding="utf-8"), "the marker reached the isolated store through the engine's own write path")
_watch = [_LIVE_DATA / f for f in ("life_state.json", "life_ledger.jsonl", "life_events.jsonl", "room_state.json", "world_objects.json", "world_substrate.json",
                                   "provisions.json", "sound_knowledge.json", "world_traces.json", "position.json", "soundscape_state.json",
                                   "satisfaction_log.jsonl", "satisfaction_state.json")]
leaked = [p.name for p in _watch if p.exists() and MARKER.encode() in p.read_bytes()]
check(not leaked, f"the marker appears in no live store ({len(_watch)} watched){' -> ' + str(leaked) if leaked else ''}")
check(not LIVE_WRITE_ATTEMPTS, f"the audit hook saw NO write attempt under any data/ ({len(LIVE_WRITE_ATTEMPTS)} attempts){' -> ' + str(LIVE_WRITE_ATTEMPTS[:3]) if LIVE_WRITE_ATTEMPTS else ''}")
_after = {p: _md5(p) for p in _LIVE_FILES}
for p in _LIVE_FILES:
    print(f"    md5 {p.name:24s} before {_before[p][:12] or '(absent)':12s} after {_after[p][:12] or '(absent)':12s}"
          + ("" if _before[p] == _after[p] else "   <- changed by a live writer, not this process; the audit hook above is the real proof"))
for _p in (ROOT / "core" / "life_traces.py", ROOT / "core" / "life.py", Path(__file__)):
    try:
        py_compile.compile(str(_p), cfile=str(TMP / (_p.name + "c")), doraise=True)
        check(True, f"py_compile {_p.name}")
    except py_compile.PyCompileError as exc:
        check(False, f"py_compile {_p.name}: {exc}")

print(f"\n{'ALL OK' if not FAILS else f'{FAILS} FAILURE(S)'} — {CHECKS} checks — isolated stores in {TMP}")
sys.exit(1 if FAILS else 0)
