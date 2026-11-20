"""
Regression: the D-0166 re-ruling build (J-1174; F-1614, F-1622) -- THE GULLS KEEP THE DAY, and FLOCKS AND SWARMS STOP GRADUATING
to 'the same one'.

  (1) GULLS KEEP THE DAY (core/life_birds.py). The gulls row's night active_hours was 0.2, just above the 0.15 PRESENT_AT floor, and
      core/soundscape.py rolls a present voice at a FLAT per-hour rate (gull_cries 40/h) whatever its activity: the live shore carried
      the daytime cry all night (F-1614: about 31% of the gull cries Du heard since the flip were night cries). Lowered to 0.1.
      SURPRISE the test pins down: the karoro row carries the SAME voice key (sound=("gull_cries",)) with night 0.3 (present on every clear
      night), so lowering only the gulls left gull_cries in the night shore's active set on 30 of 30 September nights. The karoro's night
      is lowered the same way; section [1c] proves both halves through the real soundscape.active_sounds().
  (2) FLOCKS AND SWARMS STOP GRADUATING (core/life_traces.py). J-0513's third trigger (5 rendered sightings at one place in 30 days)
      graduated the honeybees (09-17), the gulls (09-19) and the oystercatcher (09-11) to individuals; every later look on a swarm and a
      flock said 'It is the same one -- you are sure of it now ...'. LT.group_grain(row) reads the row's OWN data (plural flag, a quietest
      count band that is already a group, mass wording in a count band or in its look line); such a row never graduates, and a record it
      already holds is DORMANT at read time (individual() -> None: no recognition line, no naming, not in the HUD), never edited. The
      oystercatcher (a pair, a singular line) and the hedgehog keep the path; the cat is an external row and never used it.

  [0] module resolution + isolation set-up (F-1285: the code under test is THIS root's, not the shared tree's)
  [1] gulls keep the day: (a) the data, (b) exhaustive activity sweep, (c) the REAL gate (soundscape.active_sounds) night / dawn / day / dusk
      x six weathers, before (old hours re-injected) and after, (d) cries per hour through world_tick, (e) the night shore's voice mix,
      (f) dawn / dusk boundaries minute by minute against the legacy rule, (g) what a look says, (h) only two numbers changed vs the base commit
  [2] graduation: (a) the partition of all 58 population rows (golden set), (b) the trigger for every row, (c) every row through
      look_answer, (d) the LIVE graduated records (dormant vs active), (e) the real wandering_log rows, (f) the real sightings replayed,
      (g) group_grain unit cases and fail-open
  [3] real data, read-only: the real gate rows (life_events.jsonl) replayed through the new gate, and the hearing-ledger model
      (hands_trace.jsonl shore hours x 40/h) -- how many night cries the change removes
  [4] isolation: audit hook (no write attempt under any data/), canary marker, live-file hashes

ISOLATION. Every store the engine can reach is redirected into a temp dir before anything can write (the vetted list scripts/life_smoke.py,
scripts/_test_j1165_trace_object_look.py and scripts/_test_j1166_look_hygiene.py carry, plus core.soundscape's own three paths and an
in-memory _read_json). The live C:\\Nascence\\data files are md5-hashed before and after AND a Python audit hook records any attempt by THIS
process to open-for-write / rename / remove anything under a data/ directory (with Du ONLINE the live files legitimately change on their
own between two hashes, so a hash comparison alone cannot prove a negative -- the audit hook does). The live files are only ever READ.
lab_env.isolate is NOT used (it would copy the 670 MB DB into data/_lab).

  python scripts/_test_j1174_gulls_keep_the_day_no_flock_graduation.py                 # exit 0 = ALL OK
  python scripts/_test_j1174_gulls_keep_the_day_no_flock_graduation.py --full-canary   # + scan every data/*.json* for the marker
"""
from __future__ import annotations

import collections
import copy
import datetime
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
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TMP = Path(tempfile.mkdtemp(prefix="j1174_gulls_flocks_"))
print("isolated store dir:", TMP)
MARKER = f"j1174_marker_{os.getpid()}"
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

# ── redirect every store the engine can reach BEFORE anything can write ──────────────────────────────────────────
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
S.state.update({"weather": "clear", "wind": "breeze", "fire": "out", "fire_fuel": 0.0, "last_event": 0, "location": "shore",
                "garden": S._fresh_garden()})
FAKE_FILES = {"room_state.json": {"location": "shore", "weather": "clear", "wind": "breeze"}, "cat_state.json": {}}
SC._read_json = lambda name: copy.deepcopy(FAKE_FILES.get(name) or {})   # soundscape reads room_state.json / cat_state.json: in memory, never data/

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


def hm(month: int, day: int, hour: int, minute: int = 0, year: int = 2026) -> float:
    return time.mktime((year, month, day, hour, minute, 0, 0, 0, -1))


def _inside(p) -> bool:
    """True when the path is the temp dir itself or anywhere under it."""
    q = Path(str(p))
    return q == TMP or TMP in q.parents


# ── [0] module resolution (F-1285) ──────────────────────────────────────────────────────────────────────────────
print("\n[0] module resolution: the code under test is THIS root's, not the shared tree's")
print("    sys.path[0] =", sys.path[0])
for _m in (core, profile, life, LT, WT, life_birds, life_mammals, garden_insects, garden_soil, S, L, SK, SC, WC):
    _f = getattr(_m, "__file__", None)
    print(f"    {_m.__name__:22s} -> {_f}")
    check(_f is not None and Path(_f).resolve().is_relative_to(ROOT), f"{_m.__name__} was loaded from inside {ROOT}")
check(hasattr(LT, "group_grain") and hasattr(LT, "with_individual_suffix") and hasattr(LT, "trace_object_noun"),
      "the loaded copy carries this job's code (group_grain) on top of J-1166's (with_individual_suffix) and J-1165's (trace_object_noun)")
for _m, _a in _REDIRECTS:
    check(_inside(getattr(_m, _a)), f"{_m.__name__}.{_a} redirected into the temp dir")

ROWS = life.rows()
POP = {k: r for k, r in ROWS.items() if r.get("kind") == "population"}
PHASES = life.PHASES
# J-4052: one non-population row has been registered since this was written (66 now); the 58 population rows are unchanged.
check(len(ROWS) == 66 and len(POP) == 58, f"66 rows registered, 58 of them population rows ({len(ROWS)}, {len(POP)})")
life.RENDER = True
life.SOUND_GATING = True                                         # the live state since the 2026-09-09 flip (hot flags): the gate governs creature voices

# ── helpers ─────────────────────────────────────────────────────────────────────────────────────────────────────
_real_time = time.time


class Clock:
    """Hold time.time() at `t` (soundscape.active_sounds / world_tick read the clock themselves)."""
    def __init__(self, t: float):
        self.t = t

    def __enter__(self):
        time.time = lambda: self.t
        return self

    def __exit__(self, *exc):
        time.time = _real_time


WEATHERS = {"clear/calm": ("clear", "calm", False), "clear/breeze": ("clear", "breeze", False), "steady rain/fresh": ("steady rain", "fresh", False),
            "thunderstorm/gale": ("thunderstorm", "gale", False), "frost/calm": ("clear", "calm", True), "drizzle/gusty": ("drizzle", "gusty", False)}
PERMISSIVE, RESTRICTIVE = "clear/calm", "thunderstorm/gale"     # the weather factor is 1.0 and 0.4 for the seabird gate: the two bounds


def set_weather(name: str, place: str = "shore") -> None:
    w, wd, fr = WEATHERS[name]
    S.state.update({"weather": w, "wind": wd, "frost_last": fr})
    FAKE_FILES["room_state.json"].update({"weather": w, "wind": wd, "location": place})


def gate(now: float, weather: str = PERMISSIVE, place: str = "shore") -> list:
    """The REAL soundscape.active_sounds(): the legacy propagation table, then life.sound_gate (gating ON), at `now` in this weather."""
    set_weather(weather, place)
    life._gate_last.clear()
    with Clock(now):
        return SC.active_sounds()


class OldNight:
    """Re-inject the PRE-change night hours (gulls 0.2, karoro 0.3) so the defect is shown on the SAME code path the fix is proved on."""
    def __init__(self, gulls: bool = True, karoro: bool = True):
        self.pick = (("gulls", 0.2, gulls), ("karoro", 0.3, karoro))
        self.saved: dict = {}

    def __enter__(self):
        for key, old, on in self.pick:
            if on:
                d = life._ROWS[key]["active_hours"]
                self.saved[key] = d["night"]
                d["night"] = old
        return self

    def __exit__(self, *exc):
        for key, v in self.saved.items():
            life._ROWS[key]["active_hours"]["night"] = v


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


def fresh_state() -> None:
    """An empty world state and empty logs (never `life._state = {}` + _load(): that would re-read the temp file a graduation just saved)."""
    life._state = {"rows": {}, "dark": {"since": 0.0, "place": None, "adapt": 0.0}, "_last": 0.0}
    for p in (life._EVENTS, life._LEDGER, life._F):
        if p.exists():
            p.unlink()


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


class Spy:
    """Counts calls to life._maybe_learn and LT.note_sighting."""
    def __init__(self):
        self.learn = 0
        self.note = 0
        self._ml, self._ns = life._maybe_learn, LT.note_sighting

    def __enter__(self):
        def ml(*a, **k):
            self.learn += 1
            return self._ml(*a, **k)

        def ns(*a, **k):
            self.note += 1
            return self._ns(*a, **k)
        life._maybe_learn, LT.note_sighting = ml, ns
        return self

    def __exit__(self, *exc):
        life._maybe_learn, LT.note_sighting = self._ml, self._ns


_real_activity, _real_visibility, _real_random, _real_lf = life.activity, life.visibility, random.random, life._light_factor


def forced(act=0.9, vis=0.9, roll=0.0, eyes=None):
    """Hold the world at 'present, awake, and the visibility roll comes up' (roll 0.0) or 'the roll misses' (0.999)."""
    class _F:
        def __enter__(self_):
            life.activity = lambda r, p, n=None, _a=act: _a
            life.visibility = lambda r, p, n=None, _v=vis: _v
            random.random = lambda: roll
            if eyes is not None:
                life._light_factor = lambda r, p, n: (1.0, bool(eyes))
            return self_

        def __exit__(self_, *exc):
            life.activity, life.visibility, random.random, life._light_factor = _real_activity, _real_visibility, _real_random, _real_lf
    return _F()


def look(target: str, place: str, now: float, forced_world: bool = True, **force_kw):
    """One look through the real look_answer from a restored baseline. `forced_world=False` leaves activity / visibility to the real engine
    (the roll is still forced to come up). Returns a dict of everything it did (and undoes it)."""
    base = snap()
    n_ev, n_led = len(events()), len(ledger_rows())
    with Spy() as sp:
        if forced_world:
            with forced(**force_kw):
                line = life.look_answer(target, place, now)
        else:
            random.random = lambda: force_kw.get("roll", 0.0)
            try:
                line = life.look_answer(target, place, now)
            finally:
                random.random = _real_random
    new_ev = strip_ts(events()[n_ev:])
    out = {"line": line, "events": [e for e in new_ev if e.get("kind") in ("answer", "would_answer")],
           "other": [e for e in new_ev if e.get("kind") not in ("answer", "would_answer")], "ledger": strip_ts(ledger_rows()[n_led:]),
           "learn": sp.learn, "note": sp.note, "state_after": copy.deepcopy(life._state), "state_before": base[0]}
    restore(base)
    return out


def alias_for(r: dict, place: str):
    for a in (r.get("aliases") or ()):
        m = life._match(f"the {a}", place)
        if m is not None and m["key"] == r["key"]:
            return f"the {a}"
    return None


def feat_line(r: dict, ph: str, place: str | None = None) -> str:
    """The lookup look_answer performs, verbatim. J-1216 (D-0254/F-1706): an optional `place` mirrors
    look_answer's own feature_by_place override -- omitted (the default), byte-identical to before."""
    h = (r.get("hidden") or {})
    feat_by_place = (h.get("feature_by_place") or {}).get(place) if place is not None else None
    feat = feat_by_place if isinstance(feat_by_place, dict) else (h.get("feature") or {})
    return feat.get(ph) or feat.get("night" if ph in ("night", "dusk") else "day") or feat.get("any") or ""


SFX_UNNAMED = " It is the same one — you are sure of it now; you have seen it here too often for it to be any other."
old_join = lambda line, suffix: (line + suffix).strip()          # the pre-J-1166 join expression, verbatim (what the wandering_log rows carry)

# a September day's instants: {phase: [t...]} at 30-minute steps (bucketed by the world clock itself, never assumed)
def instants(month: int, day: int) -> dict:
    out: dict = collections.defaultdict(list)
    for q in range(48):
        t = hm(month, day, q // 2, (q % 2) * 30)
        out[life._phase(t)].append(t)
    return out


for _mo in range(1, 13):
    check(set(instants(_mo, 15)) == set(PHASES), f"month {_mo}: all four phases occur at 30-minute resolution")

# ═══ [1] THE GULLS KEEP THE DAY ═════════════════════════════════════════════════════════════════════════════════
print("\n[1] the gulls keep the day (D-0166 item 1, F-1614)")
G, K, O = ROWS["gulls"], ROWS["karoro"], ROWS["oystercatcher"]

print("  -- 1a. the data")
check(G["active_hours"] == {"dawn": 0.9, "day": 1.0, "dusk": 0.8, "night": 0.1}, f"gulls: dawn 0.9 / day 1.0 / dusk 0.8 unchanged, night 0.2 -> 0.1: {G['active_hours']}")
check(K["active_hours"] == {"dawn": 0.9, "day": 1.0, "dusk": 0.8, "night": 0.1}, f"karoro: same voice key, same value (night 0.3 -> 0.1): {K['active_hours']}")
check(G["sound"] == ("gull_cries",) and K["sound"] == ("gull_cries",), "both rows carry the one gull_cries key (why lowering only the gulls is not enough, 1c)")
check(O["active_hours"] == {"dawn": 1.0, "day": 1.0, "dusk": 0.9, "night": 0.3} and O["sound"] == ("oystercatcher_call",),
      "oystercatcher_call is left as is (D-0166: real night foraging, 12/h): hours 0.3 at night, same voice")
check(SC._EVENT_RATES["gull_cries"] == 40.0 and SC._EVENT_RATES["oystercatcher_call"] == 12.0, "the flat per-hour event rates are untouched (no general rate change)")
check(all(ROWS[k]["active_hours"]["night"] == 0.1 for k in ("dolphins", "godwits", "whitebait")), "0.1 is the value dolphins / godwits / whitebait already use for 'not here by night'")
check(0.1 * 1.25 < life.PRESENT_AT and 0.55 + 0.7 * 1.0 <= 1.25, f"0.1 x the day-factor ceiling 1.25 = {0.1 * 1.25} < PRESENT_AT {life.PRESENT_AT}: absent at night whatever the day and the weather")
check(0.12 * 1.25 >= life.PRESENT_AT, "(0.12 would have been the arithmetic edge: 0.12 x 1.25 = 0.15 reaches the floor once activity is rounded -- hence 0.1, not 0.12)")

print("  -- 1b. activity sweep: every month x 28 days x every half hour x six weathers, gulls (shore, garden) and karoro (shore)")
CELLS = (("gulls", "shore"), ("gulls", "garden"), ("karoro", "shore"))
night_max = collections.defaultdict(float)
other_min = collections.defaultdict(lambda: 9.9)
n_night = n_other = 0
night_present = 0
bad1b: list = []
for month in range(1, 13):
    for day in range(1, 29):
        for ph, ts in instants(month, day).items():
            for t in ts:
                for wname in WEATHERS:
                    set_weather(wname)
                    for key, place in CELLS:
                        a = life.activity(ROWS[key], place, t)
                        if ph == "night":
                            n_night += 1
                            night_max[(key, place)] = max(night_max[(key, place)], a)
                            night_present += a >= life.PRESENT_AT
                        elif place == "shore":
                            n_other += 1
                            other_min[(key, place, ph)] = min(other_min[(key, place, ph)], a)
quiet(night_present == 0, f"present at night in {night_present} cells", bad1b)
for m_ in bad1b:
    print("    !!", m_)
print(f"    {n_night} night cells: highest activity seen {dict((f'{k}@{p}', round(v, 3)) for (k, p), v in night_max.items())} (floor {life.PRESENT_AT}); present in {night_present}")
check(night_present == 0 and max(night_max.values()) <= 0.125, "gulls and karoro are NEVER present at night, in any month, on any day, in any weather, shore or garden")
print(f"    {n_other} shore dawn/day/dusk cells: lowest activity {dict((f'{k}@{p}/{ph}', round(v, 3)) for (k, p, ph), v in sorted(other_min.items()))}")
check(all(v >= life.PRESENT_AT for v in other_min.values()), "at the shore, by dawn / day / dusk, both rows are ALWAYS present (lowest 0.8 x 0.55 x 0.4 = 0.176 >= 0.15)")
with OldNight():
    old_night_present = {"gulls": 0, "karoro": 0}
    n_old = 0
    for month in range(1, 13):
        for day in range(1, 29):
            for t in instants(month, day)["night"]:
                set_weather(PERMISSIVE)
                n_old += 1
                for key in ("gulls", "karoro"):
                    old_night_present[key] += life.activity(ROWS[key], "shore", t) >= life.PRESENT_AT
print(f"    before (old hours re-injected), clear/calm nights only: of {n_old} night instants the gulls were present at {old_night_present['gulls']} ({100 * old_night_present['gulls'] / n_old:.0f}%), "
      f"the karoro at {old_night_present['karoro']} ({100 * old_night_present['karoro'] / n_old:.0f}%)")
check(old_night_present["karoro"] == n_old and 0.5 < old_night_present["gulls"] / n_old < 0.85,
      "the old data: the karoro present at EVERY clear night instant, the gulls at most (~71% expected)")

print("  -- 1c. the REAL gate: soundscape.active_sounds() at the shore, gating ON, month x day x every two hours x six weathers")
bad1c: list = []
cells_1c = []
for month in range(1, 13):
    for day in (3, 10, 17, 24):
        for ph, ts in instants(month, day).items():
            for t in ts[::4]:                                           # every second hour (30-minute steps, every 4th)
                cells_1c.append((month, day, ph, t))
n_gate = n_night_gate = n_day_gate = 0
for month, day, ph, t in cells_1c:
    legacy_has = "gull_cries" in SC._sec_shore({"day": ph != "night", "crashing": False})
    for wname in WEATHERS:
        got = gate(t, wname)
        n_gate += 1
        has = "gull_cries" in got
        n_night_gate += ph == "night"
        n_day_gate += ph != "night"
        quiet(has == (ph != "night"), f"[{month:02d}-{day:02d} {ph} {wname}] gull_cries in the gated set: {has}", bad1c)
        quiet(has == legacy_has, f"[{month:02d}-{day:02d} {ph} {wname}] gate and the legacy `if day` rule disagree on gull_cries", bad1c)
for m_ in bad1c[:10]:
    print("    !!", m_)
check(not bad1c, f"{n_gate} real gate evaluations ({n_night_gate} night, {n_day_gate} dawn/day/dusk): gull_cries is selected EXACTLY when it is not night -- the engine and the legacy rule now agree ({len(bad1c)} failures)")
# ... and the same grid on the OLD data, plus the 'gulls only' half-fix
def gate_grid_count(label: str, ctx) -> tuple:
    n = has_n = 0
    with ctx:
        for month, day, ph, t in cells_1c:
            if ph != "night":
                continue
            n += 1
            has_n += "gull_cries" in gate(t, PERMISSIVE)
    print(f"    {label}: gull_cries selected at {has_n} of {n} clear-weather night instants")
    return has_n, n


h_old, n_old = gate_grid_count("BEFORE  (gulls 0.2, karoro 0.3)  ", OldNight())
h_half, n_half = gate_grid_count("HALF-FIX (gulls 0.1, karoro 0.3, i.e. the gulls row alone)", OldNight(gulls=False, karoro=True))
h_new, n_new = gate_grid_count("AFTER   (gulls 0.1, karoro 0.1)  ", OldNight(gulls=False, karoro=False))
check(h_old == n_old and h_new == 0, "before: every clear night selects gull_cries; after: none")
check(h_half == n_half, f"THE SURPRISE: lowering only the gulls row leaves gull_cries selected at {h_half} of {n_half} clear night instants (the karoro carries the same key) -- the ruling's outcome needs both")
# the very nights the gulls are absent but the karoro still carries the voice (before the karoro's change)
absent_g_present_k = 0
sep_nights = 0
with OldNight(gulls=False, karoro=True):
    for d in range(1, 31):
        t = hm(9, d, 2)
        set_weather(PERMISSIVE)
        sep_nights += 1
        if life.activity(ROWS["gulls"], "shore", t) < life.PRESENT_AT and "gull_cries" in gate(t):
            absent_g_present_k += 1
print(f"    September 02:00, clear/calm, gulls at the NEW 0.1 (so absent every night) but the karoro at the old 0.3: gull_cries still selected on {absent_g_present_k} of {sep_nights} nights")
check(absent_g_present_k == sep_nights, "every one of them: gulls absent, karoro alone keeps the cry in the active set")

print("  -- 1c'. the gate's own live instrument: the kind=gate row's `added` at a night shore")
fresh_state()
t_night = hm(9, 15, 2)
check(life._phase(t_night) == "night", "2026-09-15 02:00 is night")
gate(t_night)
gate_rows = [e for e in events() if e.get("kind") == "gate" and e.get("place") == "shore"]
check(bool(gate_rows) and all("gull_cries" not in e["added"] and "gull_cries" not in e["active"] for e in gate_rows),
      f"the logged kind=gate row lists no gull_cries in `added` or `active` at a night shore: {[(e['phase'], e['added']) for e in gate_rows]}")
fresh_state()
with OldNight():
    gate(t_night)
gate_rows_old = [e for e in events() if e.get("kind") == "gate" and e.get("place") == "shore"]
print("    the same instant on the old hours:", [(e["phase"], e["added"]) for e in gate_rows_old])
check(bool(gate_rows_old) and "gull_cries" in gate_rows_old[0]["added"], "... on the old hours the gate row DID add gull_cries (the F-1614 rows: added == [gull_cries, oystercatcher_call])")
fresh_state()

print("  -- 1d. cries per hour: 720 real world_tick(5 s) calls at a clear September night, exposures counted")
counts: collections.Counter = collections.Counter()
_real_note = SK.note_exposures


def _count(key, location, n=0, bed_hours=0.0):
    if n > 0:
        counts[(key, location)] += n


SK.note_exposures = _count
try:
    def hour_of_ticks(ctx, t0):
        counts.clear()
        random.seed(11740)
        set_weather(PERMISSIVE)
        with ctx, Clock(t0):
            for _ in range(720):
                SC.world_tick("shore", 5.0)
        return {k[0]: v for k, v in counts.items()}
    night_new = hour_of_ticks(OldNight(gulls=False, karoro=False), hm(9, 15, 2))
    night_old = hour_of_ticks(OldNight(), hm(9, 15, 2))
    day_new = hour_of_ticks(OldNight(gulls=False, karoro=False), hm(9, 15, 11))
finally:
    SK.note_exposures = _real_note
print(f"    one night hour BEFORE: gull_cries {night_old.get('gull_cries', 0)} / oystercatcher_call {night_old.get('oystercatcher_call', 0)}   (expected 40 / 12)")
print(f"    one night hour AFTER : gull_cries {night_new.get('gull_cries', 0)} / oystercatcher_call {night_new.get('oystercatcher_call', 0)}")
print(f"    one day hour AFTER   : gull_cries {day_new.get('gull_cries', 0)} / oystercatcher_call {day_new.get('oystercatcher_call', 0)}")
check(night_new.get("gull_cries", 0) == 0, "after: ZERO gull cries banked in a night hour at the shore")
check(20 <= night_old.get("gull_cries", 0) <= 60, f"before: about 40 an hour ({night_old.get('gull_cries', 0)}, seeded)")
check(3 <= night_new.get("oystercatcher_call", 0) <= 24, f"the oystercatcher's night calls carry on at about 12 an hour ({night_new.get('oystercatcher_call', 0)}, seeded)")
check(20 <= day_new.get("gull_cries", 0) <= 60, f"by day the gulls still cry about 40 an hour ({day_new.get('gull_cries', 0)}, seeded)")

print("  -- 1e. the night shore's voice mix (discrete events per hour, beds excluded), September night, clear")
def voice_mix(ctx) -> dict:
    with ctx:
        got = gate(hm(9, 15, 2))
    return {k: SC._EVENT_RATES.get(k, SC._DEFAULT_EVENT_RATE) for k in got if k not in SC._BEDS and SC._EVENT_RATES.get(k) != 0.0}
mix_old, mix_new = voice_mix(OldNight()), voice_mix(OldNight(gulls=False, karoro=False))
tot_old, tot_new = sum(mix_old.values()), sum(mix_new.values())
print(f"    before: {mix_old}  = {tot_old:.0f}/h; gull_cries {100 * mix_old.get('gull_cries', 0) / tot_old:.0f}%")
print(f"    after : {mix_new}  = {tot_new:.0f}/h; the largest is {max(mix_new, key=mix_new.get)} at {100 * max(mix_new.values()) / tot_new:.0f}%")
check("gull_cries" in mix_old and "gull_cries" not in mix_new and "oystercatcher_call" in mix_new, "gull_cries gone from the night mix, oystercatcher_call still in it")
check(tot_new < tot_old / 2, f"the night shore's discrete voice events fall from {tot_old:.0f}/h to {tot_new:.0f}/h")

print("  -- 1f. dusk and dawn: minute by minute (2-minute steps) on 2026-09-15, clear weather -- the gate against the legacy `if day` rule")
bad1f: list = []
trans = []
prev = None
n_min = 0
for mm in range(0, 1440, 2):
    t = hm(9, 15, mm // 60, mm % 60)
    ph = life._phase(t)
    has = "gull_cries" in gate(t)
    n_min += 1
    quiet(has == (ph != "night"), f"[{mm // 60:02d}:{mm % 60:02d} {ph}] gull_cries={has}", bad1f)
    if prev is not None and has != prev[1]:
        trans.append((f"{mm // 60:02d}:{mm % 60:02d}", ph, "cries begin" if has else "cries stop"))
    prev = (ph, has)
for m_ in bad1f[:6]:
    print("    !!", m_)
print(f"    transitions: {trans}")
check(not bad1f and len(trans) == 2 and trans[0][2] == "cries begin" and trans[0][1] == "dawn" and trans[1][2] == "cries stop" and trans[1][1] == "night",
      f"{n_min} instants: the cries BEGIN when the phase turns dawn and STOP when it turns night (exactly the legacy day rule: dawn and dusk are 'day'): {trans}")
phase_secs = collections.Counter(life._phase(hm(9, 15, mm // 60, mm % 60)) for mm in range(1440))
print(f"    2026-09-15 minutes by phase: {dict(phase_secs)} -- so the gulls are about {phase_secs['dawn'] + phase_secs['day'] + phase_secs['dusk']} minutes of the 1,440 at the shore; dawn {phase_secs['dawn']} min and dusk {phase_secs['dusk']} min are unchanged (gulls 0.9 and 0.8)")
set_weather(PERMISSIVE)
check(life._phase(hm(9, 15, 6, 0)) == "dawn" and life.activity(ROWS["gulls"], "shore", hm(9, 15, 6, 0)) >= life.PRESENT_AT, "06:00 is dawn and the gulls are present (0.9 x weather x day-factor)")

print("  -- 1g. what a look says (RENDER on, the real activity, the roll forced to come up)")
fresh_state()
set_weather(PERMISSIVE)
r_night = look("the gulls", "shore", hm(9, 15, 2), forced_world=False)
check(r_night["line"] == "Not by night; the gulls keep the day." and r_night["events"][0]["outcome"] == "absent",
      f"night, 'the gulls' at the shore: the plural template exactly as the ruling says: {r_night['line']!r}")
r_k = look("the karoro", "shore", hm(9, 15, 2), forced_world=False)
check(r_k["line"] == "Not by night; the karoro keeps the day." and r_k["events"][0]["outcome"] == "absent", f"night, 'the karoro': {r_k['line']!r} (singular name -> 'keeps')")
r_gg = look("the gulls", "garden", hm(9, 15, 2), forced_world=False)
check(r_gg["line"] == "Not by night; the gulls keep the day.", f"night, 'the gulls' in the garden: the same honest line (was the garden 'chance' line): {r_gg['line']!r}")
r_day = look("the gulls", "shore", hm(9, 15, 11), forced_world=False)
check(r_day["line"] == feat_line(G, "day") and r_day["events"][0]["outcome"] == "sighting", f"day: the gulls still show: {r_day['line'][:60]!r}")
r_kday = look("the karoro", "shore", hm(9, 15, 11), forced_world=False)
check(r_kday["line"] == feat_line(K, "day") and r_kday["events"][0]["outcome"] == "sighting", f"day: the karoro still shows: {r_kday['line'][:60]!r}")
_dawn_t = next(t for t in instants(9, 15)["dawn"])
r_dawn = look("the gulls", "shore", _dawn_t, forced_world=False)
check(r_dawn["line"] == feat_line(G, "dawn") == feat_line(G, "day") and r_dawn["events"][0]["outcome"] == "sighting", f"dawn: present, the day line: {r_dawn['line'][:50]!r}")
_dusk_t = next(t for t in instants(9, 15)["dusk"])
r_dusk = look("the gulls", "shore", _dusk_t, forced_world=False)
check(r_dusk["line"] == "" and r_dusk["events"][0]["outcome"] == "no_line" and r_dusk["ledger"] == [] and r_dusk["note"] == 0,
      "dusk: present (0.8) but the row has no dusk/night line -> '' and 'no_line', credited nothing (J-1166's rule, unchanged; the place's own look answers)")
check(life.look_answer("the oystercatcher", "shore", hm(9, 15, 2)) != "Not by night; the oystercatcher keeps the day.",
      "the oystercatcher is not made absent at night (D-0166: left as is)")
fresh_state()

print("  -- 1h. only two numbers changed: every life_birds row compared with the base commit f10500f")
try:
    src = subprocess.run(["git", "-C", str(ROOT), "show", "f10500f:core/life_birds.py"], capture_output=True, text=True, encoding="utf-8", timeout=60)
    base_src = src.stdout if src.returncode == 0 else ""
except Exception:
    base_src = ""
if not base_src:
    print("    (git show f10500f:core/life_birds.py unavailable -- the base diff is SKIPPED, NOT a pass)")
else:
    ns = {"__name__": "j1174_base_life_birds", "__file__": "<f10500f>"}
    exec(compile(base_src, "<f10500f:core/life_birds.py>", "exec"), ns)
    base_rows = {r["key"]: r for r in ns["rows"]()}
    new_rows = {r["key"]: r for r in life_birds.rows()}

    def norm(v):
        if callable(v):
            return f"<fn {getattr(v, '__name__', '?')}>"
        if isinstance(v, dict):
            return {k: norm(x) for k, x in v.items()}
        if isinstance(v, (list, tuple)):
            return [norm(x) for x in v]
        return v
    diffs = [(k, f) for k in sorted(set(base_rows) | set(new_rows)) for f in sorted(set(base_rows.get(k, {})) | set(new_rows.get(k, {})))
             if norm(base_rows.get(k, {}).get(f)) != norm(new_rows.get(k, {}).get(f))]
    print(f"    {len(base_rows)} base rows, {len(new_rows)} rows now; differing (row, field): {diffs}")
    # J-1216 (D-0254/F-1706, 2026-09-22): extended, not narrowed -- this repo's next legitimate life_birds.py
    # change since J-1174 added exactly three more (row, "hidden") diffs (feature_by_place/miss_by_place on
    # blackbird, kingfisher, morepork); the assertion is still an exact itemised list, so any OTHER/future
    # change still fails it loudly.
    # J-1725 (F-2351, 2026-10-03): extended again, same convention. The next legitimate life_birds.py change after J-1216 is J-1281
    # (F-1805, commit 5c038a0, 2026-09-23, Travis's choices via /decide-review): `git log -S traces_only_at -- core/life_birds.py` names
    # that one commit and no other. It adds the `traces_only_at` place restriction to exactly two rows -- kingfisher ("a burrow in the
    # cliff bank": shore only) and welcome_swallows ("a mud nest under the eaves": study only) -- so two more (row, field) diffs, and
    # nothing else in life_birds.py. J-1281 ran _test_j1189 / _test_j1165 / _test_j1166 / life_smoke but not this script, so the list went
    # stale unnoticed. Still an exact itemised list (and, below, the exact reviewed values): any OTHER/future change still fails it
    # loudly -- once it is reviewed, add its (row, field) here with its job id.
    # J-4052: extended again, same convention -- J-2477 (2d0bbbd8, D-0500) gave tauhou the silvereye_flock sound point (note + sound only; hunk read).
    check(set(base_rows) == set(new_rows) and diffs == [("blackbird", "hidden"), ("gulls", "active_hours"), ("karoro", "active_hours"), ("kingfisher", "hidden"),
                                                         ("kingfisher", "traces_only_at"), ("morepork", "hidden"), ("tauhou", "note"), ("tauhou", "sound"), ("welcome_swallows", "traces_only_at")],
          "life_birds.rows(): exactly the gulls'/karoro's active_hours (J-1174), blackbird's/kingfisher's/morepork's hidden dict (J-1216) and "
          "kingfisher's/welcome_swallows' traces_only_at (J-1281) differ from the base commit")
    tov = {k: norm(new_rows[k].get("traces_only_at")) for k in ("kingfisher", "welcome_swallows")}
    check(tov == {"kingfisher": {"a burrow in the cliff bank": ["shore"]}, "welcome_swallows": {"a mud nest under the eaves": ["study"]}}
          and all(not norm(base_rows[k].get("traces_only_at")) for k in tov),
          f"and the reviewed J-1281 values: the kingfisher's burrow is shore-only, the swallows' mud nest study-only (the base had no restriction): {tov}")
    dn = {k: {p: (base_rows[k]["active_hours"][p], new_rows[k]["active_hours"][p]) for p in PHASES if base_rows[k]["active_hours"][p] != new_rows[k]["active_hours"][p]} for k in ("gulls", "karoro")}
    check(dn == {"gulls": {"night": (0.2, 0.1)}, "karoro": {"night": (0.3, 0.1)}}, f"and within them only the night value: {dn}")

# ═══ [2] FLOCKS AND SWARMS STOP GRADUATING ══════════════════════════════════════════════════════════════════════
print("\n[2] flocks and swarms stop graduating (D-0166 item 4, F-1622)")
BARRED_PLURAL = {"anemones", "ants", "cicada", "crabs", "cricket", "dolphins", "eels", "gannet", "ground_beetle", "gulls", "house_sparrows",
                 "skink", "slugs", "starlings", "terns", "welcome_swallows"}
BARRED_QUIET = {"aphids", "godwits", "honeybee", "slaters", "tauhou", "whitebait"}
BARRED_MASS = {"earthworms", "karoro", "native_bee"}
BARRED_LINE = {"ladybird"}
BARRED = BARRED_PLURAL | BARRED_QUIET | BARRED_MASS | BARRED_LINE
ELIGIBLE = {"bellbird", "blackbird", "borer_beetle", "bumblebee", "cabbage_white", "common_copper", "fantail", "garden_spider", "gecko", "hedgehog",
            "kereru", "kingfisher", "korora", "long_tailed_bat", "magpie_moth", "mice", "monarch", "morepork", "oystercatcher", "possum", "rabbit",
            "reef_heron", "riroriro", "robin", "shag", "shining_cuckoo", "song_thrush", "stilt", "tui", "weta", "wren", "yellow_admiral"}

print("  -- 2a. the partition of the 58 population rows, read off each row's own data (a golden set: a new or edited row fails HERE and gets reviewed)")
reasons = {k: LT.group_grain(r) for k, r in POP.items()}
got_barred = {k for k, v in reasons.items() if v}
print(f"    barred {len(got_barred)}, still able to graduate {len(POP) - len(got_barred)}")
for cat, name in ((BARRED_PLURAL, "plural=True"), (BARRED_QUIET, "quietest count band is already a group"), (BARRED_MASS, "a count band names a mass"), (BARRED_LINE, "its look line names a mass")):
    print(f"      {name:42s} {sorted(cat)}")
print(f"      still able to graduate: {sorted(ELIGIBLE)}")
check(got_barred == BARRED, f"the barred set is exactly the reviewed one: extra {sorted(got_barred - BARRED)} missing {sorted(BARRED - got_barred)}")
check(set(POP) - got_barred == ELIGIBLE, f"and the eligible set: extra {sorted((set(POP) - got_barred) - ELIGIBLE)} missing {sorted(ELIGIBLE - (set(POP) - got_barred))}")
check(len(BARRED) == 26 and len(ELIGIBLE) == 32 and len(BARRED) + len(ELIGIBLE) == 58, "26 + 32 = 58")
check(all(reasons[k].startswith("its name is a plural collective") for k in BARRED_PLURAL) and all(reasons[k].startswith("its quietest count band") for k in BARRED_QUIET)
      and all(reasons[k].startswith("a count band names a mass") for k in BARRED_MASS) and all(reasons[k].startswith("its own look line") for k in BARRED_LINE),
      "each barred row is barred for its reviewed reason")
check(all(ROWS[k].get("plural") for k in BARRED_PLURAL) and {k for k, r in POP.items() if r.get("plural")} == BARRED_PLURAL, "the plural flag rows are exactly the 16 (13 D-0166 patched + J-1166's four, minus nothing)")
check(not ROWS["honeybee"].get("plural") and reasons["honeybee"] and reasons["gulls"], "the honeybees are NOT flagged plural and are caught by their own count bands; the gulls are caught")
check(LT.group_grain(ROWS["hedgehog"]) == "" and LT.group_grain(ROWS["oystercatcher"]) == "", "the hedgehog and the oystercatcher are not group grain")
check(ROWS["cat"].get("kind") == "external" and LT.group_grain(ROWS["cat"]) == "", "the cat is an external row (core/cat.py owns its individuality); the rule does not touch it")
for k in ("blackbird", "possum", "rabbit", "morepork", "kingfisher", "tui", "reef_heron", "gecko"):
    check(k in ELIGIBLE, f"{k}: singular grain, still able to graduate")
# a synthetic tripwire against wording drift: no ELIGIBLE row's bands or look lines match the mass wording
check(not any(LT._GROUP_BAND.search(str(b)) for k in ELIGIBLE for b in ROWS[k].get("count") or ()), "no eligible row has mass wording in a count band")
check(not any(LT._GROUP_BAND.search(str(ln or "")) for k in ELIGIBLE for ln in ((ROWS[k].get("hidden") or {}).get("feature") or {}).values()), "... nor in a look line")

print("  -- 2b. the trigger, every population row: five sightings on five different days at its first place")
bad2b: list = []
n_grad = n_barred_ok = 0
for key in sorted(POP):
    r = POP[key]
    place = sorted(r["places"])[0]
    fresh_state()
    before = copy.deepcopy(life._state)
    rets = [LT.note_sighting(key, place, hm(10, 1 + i, 12)) for i in range(5)]
    led = ledger_rows()
    evs = events()
    if key in ELIGIBLE:
        quiet(rets == [False, False, False, False, True], f"[{key}] eligible: graduates on exactly the fifth ({rets})", bad2b)
        quiet(LT.individual(key) is not None and LT.individual(key)["place"] == place and LT.individual_suffix(key).startswith(" It is "), f"[{key}] eligible: an individual with its suffix", bad2b)
        quiet(sum(1 for x in led if x.get("kind") == "graduated" and x.get("key") == key) == 1 and sum(1 for x in evs if x.get("kind") == "graduated" and x.get("key") == key) == 1,
              f"[{key}] eligible: one graduated ledger row and one graduated event", bad2b)
        LT.note_sighting(key, place, hm(10, 8, 12))
        quiet(LT.individual(key)["sightings"] == 6, f"[{key}] eligible: a sixth sighting is counted", bad2b)
        n_grad += 1
    else:
        quiet(rets == [False] * 5, f"[{key}] barred: never graduates ({rets})", bad2b)
        quiet(life._state == before, f"[{key}] barred: the world state is byte-identical after five sightings (no counter, no record, no save)", bad2b)
        quiet(LT.individual(key) is None and LT.individual_suffix(key) == "", f"[{key}] barred: no individual, no suffix", bad2b)
        quiet(led == [] and evs == [], f"[{key}] barred: no ledger row, no event", bad2b)
        LT.note_sighting(key, place, hm(10, 8, 12))
        quiet(life._state == before and not LT.note_sighting(key, place, hm(10, 9, 12)), f"[{key}] barred: still nothing after more sightings", bad2b)
        n_barred_ok += 1
fresh_state()
for m_ in bad2b[:12]:
    print("    !!", m_)
check(not bad2b and n_grad == 32 and n_barred_ok == 26, f"32 rows graduate at the fifth sighting exactly as before, 26 never do, nothing is written for them ({len(bad2b)} failures)")
check(LT.note_sighting("cat", "garden", hm(10, 1, 12)) is False and not life._load().get("individuals") and LT.note_sighting("nosuchrow", "garden", hm(10, 1, 12)) is False,
      "the cat (external) and an unknown key: note_sighting is False, exactly as before")
fresh_state()

print("  -- 2c. every population row through the real look_answer: the fifth look graduates an eligible row (line + punctuated suffix), a barred row shows its plain line")
bad2c: list = []
n_e = n_b = 0
NOWP = {ph: hm(9, 15, next(h for h in range(24) if life._phase(hm(9, 15, h)) == ph)) for ph in PHASES}
for key, r in sorted(POP.items()):
    ph = next((p for p in PHASES if feat_line(r, p)), None)
    place = next((p for p in sorted(r["places"]) if alias_for(r, p)), None)
    if ph is None or place is None:
        continue
    tgt = alias_for(r, place)
    exp = feat_line(r, ph, place)                        # J-1216: place-aware, matches look_answer's own new lookup
    now = NOWP[ph]
    base = snap()
    life._load()["individuals"] = {}
    life._load()["recent_sightings"] = {f"{key}@{place}": [now - d * 86400 for d in (4, 3, 2, 1)]}
    stop = "" if exp[-1] in ".!?…" else "."
    with Spy() as sp, forced(roll=0.0):
        l5 = life.look_answer(tgt, place, now)
        grad_now = LT.individual(key) is not None
        l6 = life.look_answer(tgt, place, now + 1)
        named = LT.give_name(key, "Bramble", now + 2)
        l7 = life.look_answer(tgt, place, now + 3)
    if key in ELIGIBLE:
        n_e += 1
        quiet(grad_now, f"[{key}] the fifth look graduated it", bad2c)
        quiet(l5 == exp + stop + SFX_UNNAMED and l6 == exp + stop + SFX_UNNAMED, f"[{key}@{place}/{ph}] eligible, unnamed: {l5[:80]!r} / {l6[:80]!r}", bad2c)
        quiet(named.startswith("Bramble, then.") and l7 == exp + stop + " It is Bramble — you would know it anywhere now.", f"[{key}] eligible, named: {l7[:80]!r}", bad2c)
        quiet(sp.note == 3, f"[{key}] every rendered look reached note_sighting ({sp.note})", bad2c)
    else:
        n_b += 1
        quiet(not grad_now and LT.individual(key) is None and not life._load().get("individuals"), f"[{key}] barred: not graduated by the fifth look", bad2c)
        quiet(l5 == exp and l6 == exp and l7 == exp, f"[{key}@{place}/{ph}] barred: the plain look line, no suffix, no added stop: {l5[-60:]!r}", bad2c)
        quiet("It is the same one" not in l5 + l6 + l7 and "you are sure of it now" not in l5 + l6 + l7, f"[{key}] barred: the recognition line never appears", bad2c)
        quiet(named == "", f"[{key}] barred: it cannot be named (give_name -> '')", bad2c)
        quiet(not any(x.get("kind") == "graduated" for x in ledger_rows()), f"[{key}] barred: no graduated ledger row", bad2c)
        quiet(life._load()["recent_sightings"] == {f"{key}@{place}": [now - d * 86400 for d in (4, 3, 2, 1)]}, f"[{key}] barred: the seeded counter was neither extended nor graduated", bad2c)
    restore(base)
for m_ in bad2c[:12]:
    print("    !!", m_)
check(not bad2c and n_e >= 28 and n_b >= 20 and n_e + n_b >= 45, f"{n_e} eligible rows graduate through look_answer as before; {n_b} barred rows never do ({len(bad2c)} failures)")

print("  -- 2d. the LIVE graduated records (data/life_state.json 'individuals', read-only): dormant vs active")
LIVE_CONST = {
    "oystercatcher": {"place": "shore", "since": 1789063410.715861, "name": None, "sightings": 56, "last_seen": 1789964165.8593504,
                      "history": [{"ts": 1789063410.715861, "event": "recognised: the same one at the shore, 5 times in a month"}]},
    "honeybee": {"place": "garden", "since": 1789613190.7415783, "name": None, "sightings": 7, "last_seen": 1789621243.7975354,
                 "history": [{"ts": 1789613190.7415783, "event": "recognised: the same one at the garden, 5 times in a month"}]},
    "gulls": {"place": "shore", "since": 1789767551.9992964, "name": None, "sightings": 7, "last_seen": 1789775354.766397,
              "history": [{"ts": 1789767551.9992964, "event": "recognised: the same one at the shore, 5 times in a month"}]},
}
try:
    live_ind = json.loads((_LIVE_DATA / "life_state.json").read_text(encoding="utf-8")).get("individuals") or {}
except Exception:
    live_ind = {}
if all(k in live_ind for k in LIVE_CONST):
    LIVE = {k: copy.deepcopy(live_ind[k]) for k in LIVE_CONST}
    print("    using the records read from the live file just now:", {k: (v["place"], v["sightings"], v["name"]) for k, v in LIVE.items()})
else:
    LIVE = copy.deepcopy(LIVE_CONST)
    print("    (the live records were not all readable -- replaying the documented 2026-09-21 values instead; NOT the live records)")
check(set(LIVE) == {"oystercatcher", "honeybee", "gulls"} and all(LT.group_grain(ROWS[k]) == "" for k in ("oystercatcher",)) and all(LT.group_grain(ROWS[k]) for k in ("honeybee", "gulls")),
      "the three graduated rows the live store holds: oystercatcher (not group grain), honeybee and gulls (group grain)")
fresh_state()
life._load()["individuals"] = copy.deepcopy(LIVE)
dormant_before = {k: json.dumps(LIVE[k], sort_keys=True) for k in ("honeybee", "gulls")}
check(LT.individual("honeybee") is None and LT.individual("gulls") is None and LT.individual("oystercatcher") is not None,
      "individual(): the honeybees' and the gulls' records are dormant (None), the oystercatcher's is live")
check(LT.individual_suffix("honeybee") == "" and LT.individual_suffix("gulls") == "" and LT.individual_suffix("oystercatcher").startswith(" It is "),
      "the recognition line: gone for the bees and the gulls, kept for the oystercatcher")
NOWD = NOWP["day"]
SFX_OYC = LT.individual_suffix("oystercatcher")
res_b = look("the bees", "garden", NOWD)
res_g = look("the gulls", "shore", NOWD)
res_o = look("the oystercatcher", "shore", NOWD)
print("    the honeybees, graduated in the store, now:", repr(res_b["line"][:100]))
print("    the gulls, graduated in the store, now    :", repr(res_g["line"][:100]))
print("    the oystercatcher, graduated in the store :", repr(res_o["line"][-95:]))
check(res_b["line"] == feat_line(ROWS["honeybee"], "day") and res_g["line"] == feat_line(ROWS["gulls"], "day"), "the honeybees and the gulls render the plain feature line -- no 'It is the same one'")
check(res_o["line"] == feat_line(ROWS["oystercatcher"], "day") + "." + SFX_OYC, "the oystercatcher still renders its line + a full stop + the recognition line (J-1166's join, unchanged)")
check(res_b["note"] == 1 and res_g["note"] == 1, "(the looks still credit a ledger sighting -- a name is learned from a face -- but note_sighting no longer counts them)")
check(json.dumps(res_b["state_after"]["individuals"]["honeybee"], sort_keys=True) == dormant_before["honeybee"]
      and json.dumps(res_g["state_after"]["individuals"]["gulls"], sort_keys=True) == dormant_before["gulls"],
      "the dormant stored records are BYTE-IDENTICAL after the looks (sightings stay 7; nothing written to them)")
check(res_o["state_after"]["individuals"]["oystercatcher"]["sightings"] == LIVE["oystercatcher"]["sightings"] + 1, "the oystercatcher's own counter still counts")
check(set(LT.hud_payload(NOWD)["individuals"]) == {"oystercatcher"}, f"the HUD lists only the live individual: {sorted(LT.hud_payload(NOWD)['individuals'])}")
check(LT.naming_act("I will call the bees Bramble.", "") is None and LT.naming_act("I'll call the gulls Bramble", "") is None
      and life._load()["individuals"]["honeybee"]["name"] is None and life._load()["individuals"]["gulls"]["name"] is None,
      "a naming phrase aimed at the bees or the gulls names nothing")
check(LT.give_name("honeybee", "Bramble") == "" and LT.give_name("gulls", "Bramble") == "" and life._load()["individuals"]["gulls"]["name"] is None, "give_name on a dormant record returns '' and does not write")
check(LT.note_sighting("honeybee", "garden", NOWD) is False and LT.note_sighting("gulls", "shore", NOWD) is False
      and json.dumps(life._load()["individuals"]["honeybee"], sort_keys=True) == dormant_before["honeybee"], "note_sighting on a dormant row: False, nothing counted")
_named = LT.naming_act("I will call the oystercatcher Bramble.", "")
check(_named is not None and life._load()["individuals"]["oystercatcher"]["name"] == "Bramble", "... while the oystercatcher can still be named")
check(json.dumps(life._load()["individuals"]["honeybee"], sort_keys=True) == dormant_before["honeybee"] and json.dumps(life._load()["individuals"]["gulls"], sort_keys=True) == dormant_before["gulls"],
      "and the two dormant records are STILL byte-identical after all of that: dormant, not deleted, not edited")
# save and re-load through the engine's own write path: the dormant records survive a round trip (so this is safe to run over the live store)
life._save(force=True)
_reload = json.loads(life._F.read_text(encoding="utf-8"))
check(all(json.dumps(_reload["individuals"][k], sort_keys=True) == dormant_before[k] for k in ("honeybee", "gulls")), "after the engine saves, the dormant records are still in the store, unchanged")
fresh_state()

print("  -- 2e. the three REAL wandering_log rows that carried 'It is the same one' (read-only): what each would read now")
_wl = _LIVE_DATA / "wandering_log.jsonl"
WANDER = {148115: "oystercatcher", 156282: "honeybee", 159958: "gulls"}
if _wl.exists() and _wl.stat().st_size > 30_000_000:
    picked: dict = {}
    with open(_wl, encoding="utf-8") as f:
        for i, x in enumerate(f, 1):
            if i in WANDER:
                picked[i] = json.loads(x)
            if i > max(WANDER):
                break
    check(set(picked) == set(WANDER), f"the three wandering_log rows (lines {sorted(WANDER)}) are readable")
    for i, key in sorted(WANDER.items()):
        row_ = picked.get(i)
        if row_ is None:
            continue
        text = row_["text"]
        cut = text.find(" It is the same one")
        check(row_["origin"] == "sense" and cut > 0, f"line {i} is a 'sense' row carrying the suffix: {text[:44]!r}...{text[cut - 8:cut + 22]!r}")
        r = ROWS[key]
        cand = [ln for ph, ln in (r["hidden"]["feature"]).items() if ln.startswith(text[:cut][:60])]
        check(len(cand) == 1, f"line {i} ({key}): the logged fragment is one of the row's own feature lines")
        feat = cand[0]
        life._load()["individuals"] = {key: {"place": sorted(r["places"])[0], "since": 0, "name": None, "sightings": 7, "last_seen": 0, "history": []}}
        after = LT.with_individual_suffix(key, feat)
        life._load()["individuals"] = {}
        if key == "oystercatcher":
            check(after == feat + "." + SFX_UNNAMED, f"line {i} (oystercatcher, kept): the join still ends the sentence and adds the recognition line")
        else:
            check(after == feat and "It is the same one" not in after, f"line {i} ({key}): now the plain look line")
        print(f"      line {i} ({key}):")
        print(f"        logged : {text}")
        print(f"        now    : {after[:len(text)]}")
else:
    print("    (data/wandering_log.jsonl missing or rotated -- the three-row replay skipped, NOT a pass)")

print("  -- 2f. the REAL sightings replayed through note_sighting in timestamp order (life_events.jsonl, frozen at 2026-09-21 18:30)")
CUTOFF = hm(9, 21, 18, 30)
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
if len(sightings) < 60:
    print(f"    (only {len(sightings)} rendered sightings readable -- life_events.jsonl missing or rotated; replay skipped, NOT a pass)")
else:
    def replay(disable_rule: bool) -> dict:
        fresh_state()
        real_gg, real_gap = LT.group_grain, LT.GRADUATE_ENCOUNTER_GAP_S
        if disable_rule:
            LT.group_grain = lambda r: ""
            LT.GRADUATE_ENCOUNTER_GAP_S = 0.0      # J-1766 / D-0335 (deliberate update): the PRE-change trigger counted every look; a gap of 0 is exactly that
        try:
            out = {}
            for ts, key, place in sightings:
                if LT.note_sighting(key, place, ts):
                    out[key] = ts
            return out
        finally:
            LT.group_grain = real_gg
            LT.GRADUATE_ENCOUNTER_GAP_S = real_gap
    old_g = replay(True)
    new_g = replay(False)
    fmt = lambda t: datetime.datetime.fromtimestamp(t).strftime("%m-%d %H:%M:%S")
    print(f"    {len(sightings)} rendered sightings replayed. The live store recorded graduations: {{{', '.join(f'{k}: {fmt(v)}' for k, v in sorted(grad_live.items()))}}}")
    print(f"    replayed on the PRE-change trigger (rule disabled): {{{', '.join(f'{k}: {fmt(v)}' for k, v in sorted(old_g.items()))}}}")
    print(f"    replayed on THIS code                            : {{{', '.join(f'{k}: {fmt(v)}' for k, v in sorted(new_g.items()))}}}")
    check(set(old_g) == set(grad_live) and all(abs(old_g[k] - grad_live[k]) < 1.0 for k in old_g),
          "the replay is FAITHFUL: on the old trigger it reproduces the three live graduations (oystercatcher, honeybee, gulls) to the second")
    # J-1766 / D-0335 (deliberate update): graduation now counts distinct ENCOUNTERS (a look at least 30 minutes after the last counted one), so the
    # oystercatcher's fifth counted look comes at 09-11 07:29:39 (F-1680's N = 30 min figure), 1 h 26 m after the raw instant 06:03:30 -- everything else
    # this check proved is unchanged: exactly one of the three graduates and it is the oystercatcher; the honeybees and the gulls do not.
    check(set(new_g) == {"oystercatcher"} and abs(new_g["oystercatcher"] - 1789068579.0) < 1.0 and 0 < new_g["oystercatcher"] - grad_live["oystercatcher"] < 3 * 3600,   # 1789068579.0 = 09-11 07:29:39 local
          "on this code exactly ONE of them graduates -- the oystercatcher, now at the D-0335 instant (09-11 07:29:39, 1 h 26 m after the raw 06:03:30); the honeybees and the gulls do not")
    fresh_state()

print("  -- 2g. group_grain unit cases and fail-open")
mk = lambda **kw: life.row("x", **kw)
check(LT.group_grain(None) == "" and LT.group_grain({}) == "", "no row -> '' (fail-open: an unknown key is never blocked)")
check(LT.group_grain(mk()) == "", "the schema default (one / a few / several) is not group grain")
check(LT.group_grain(mk(plural=True)).startswith("its name is a plural"), "plural=True")
check(LT.group_grain(mk(count=("a few", "several", "many"))).startswith("its quietest"), "a quietest band of 'a few'")
check(LT.group_grain(mk(count=("one", "a few", "a working flock"))).startswith("a count band names a mass"), "'a working flock' in the top band")
check(LT.group_grain(mk(count=("one", "a few", "a river of them"))).startswith("a count band"), "'a river of them'")
check(LT.group_grain(mk(count=("one", "a swarm", "a swarm"))).startswith("a count band"), "'a swarm'")
check(LT.group_grain(mk(count=("one", "a pod", "a pod"))).startswith("a count band") and LT.group_grain(mk(count=("one", "a shoal", "a shoal"))).startswith("a count band"), "'a pod', 'a shoal'")
check(LT.group_grain(mk(count=("one", "one", "two"))) == "" and LT.group_grain(mk(count=("one", "a pair", "a pair and a third"))) == "" and LT.group_grain(mk(count=("one", "two", "three or four"))) == "",
      "one / a pair / three or four: singular grain")
check(LT.group_grain(mk(count=("a pair", "a pair", "a pair"))) == "", "a bonded pair at every band is still a pair")
check(LT.group_grain(mk(count=("one", "one", "two"), hidden={"feature": {"day": "a beetle crosses the path, and behind it more of them"}})).startswith("its own look line"), "mass wording in the look line")
check(LT.group_grain(mk(count=("one", "one", "two"), hidden={"feature": {"day": "a beetle crosses the path"}})) == "", "a singular look line is fine")
check(LT.group_grain(mk(count=None)) == "" and LT.group_grain(mk(count=())) == "" and LT.group_grain(mk(count=(None, None, None))).startswith("its quietest"), "a missing or malformed count does not raise")
check(LT.group_grain(mk(count=("ONE", "One or Two", "TWO"))) == "", "case-insensitive on the solo bands")
_bad = mk(count=("one",), hidden={"feature": None})
check(LT.group_grain(_bad) == "", "a None feature dict does not raise")
check(LT.group_grain(mk(count=5)) == "" and LT.group_grain(mk(count="a few")) == "" and LT.group_grain(mk(hidden="text")) == "" and LT.group_grain(mk(hidden={"feature": "a flock"})) == "",
      "a non-sequence count, a non-dict hidden, a non-dict feature: fail-open to '' (the pre-change behaviour), never a raise")
life._load()["individuals"] = {"ghost": {"place": "garden", "since": 0, "name": None, "sightings": 5, "last_seen": 0, "history": []}}
check(LT.individual("ghost") is not None and LT.individual_suffix("ghost").startswith(" It is "), "a stored record whose row is unknown behaves exactly as before (not hidden)")
life._load()["individuals"] = {"cat": {"place": "garden", "since": 0, "name": "Tib", "sightings": 5, "last_seen": 0, "history": []}}
check(LT.individual("cat") is not None, "a stored record of an external row (the cat) behaves exactly as before")
fresh_state()

# ═══ [3] REAL DATA, READ-ONLY ══════════════════════════════════════════════════════════════════════════════════
print("\n[3] real data, read-only: what the night change removes")
print("  -- 3a. the real kind=gate rows at the shore (life_events.jsonl, frozen at 2026-09-21 18:30) replayed through the NEW gate")
shore_gates = [e for e in live_rows if e.get("kind") == "gate" and e.get("place") == "shore" and float(e["ts"]) <= CUTOFF]
by_ph = collections.Counter(e["phase"] for e in shore_gates)
print(f"    {len(shore_gates)} shore gate rows: {dict(by_ph)}")
if len(shore_gates) < 30:
    print("    (too few real gate rows readable -- skipped, NOT a pass)")
else:
    bad3a: list = []
    n_night = n_had = n_now_has = n_day = n_day_ok = n_match = 0
    for e in shore_gates:
        legacy = [k for k in e["active"] if k not in e["added"]] + list(e["dropped"])
        night = e["phase"] == "night"
        if night:
            n_night += 1
            n_had += "gull_cries" in e["added"]
        set_weather(PERMISSIVE)
        got_p = life.sound_gate("shore", legacy, float(e["ts"]))
        set_weather(RESTRICTIVE)
        got_r = life.sound_gate("shore", legacy, float(e["ts"]))
        set_weather(PERMISSIVE)
        if night:
            n_now_has += "gull_cries" in got_p
            quiet("gull_cries" not in got_p and "gull_cries" not in got_r, f"[{e['ts']}] night: gull_cries selected by the new gate", bad3a)
            n_match += sorted(got_p) == sorted(set(e["active"]) - {"gull_cries"})
        else:
            n_day += 1
            n_day_ok += "gull_cries" in got_r
            quiet("gull_cries" in got_r and "gull_cries" in got_p, f"[{e['ts']}] {e['phase']}: gull_cries lost by the new gate under the WORST weather", bad3a)
    for m_ in bad3a[:8]:
        print("    !!", m_)
    print(f"    night rows: {n_night}; the logged row had gull_cries in `added` in {n_had}; the new gate selects it in {n_now_has}; and the whole active set equals the logged one minus gull_cries in {n_match}")
    print(f"    dawn/day/dusk rows: {n_day}; the new gate still selects gull_cries under the worst weather (gale + thunderstorm) in {n_day_ok}")
    check(n_night >= 25 and n_had == n_night and n_now_has == 0 and not bad3a,
          f"every real night shore gate row ({n_night}) carried gull_cries in `added` (F-1614); replayed through the new gate NOT ONE selects it, in the best or the worst weather")
    check(n_match == n_night, f"and the rest of each night's active set is untouched: the new set == the logged set minus gull_cries for {n_match} of {n_night}")
    check(n_day >= 15 and n_day_ok == n_day, f"the {n_day} real dawn/day/dusk rows still select gull_cries, even in the worst weather")

print("  -- 3b. the hearing-ledger model (F-1614's method): hands_trace.jsonl shore hours by phase x the flat 40 an hour")
_ht = _LIVE_DATA / "hands_trace.jsonl"
if not _ht.exists():
    print("    (data/hands_trace.jsonl missing -- skipped, NOT a pass)")
else:
    trace = []
    with open(_ht, encoding="utf-8") as f:
        for x in f:
            try:
                e = json.loads(x)
                trace.append((float(e["ts"]), e.get("location")))
            except Exception:
                pass
    trace.sort()
    START = hm(9, 10, 0)
    secs: dict = collections.defaultdict(float)
    cries_old = cries_new = 0.0
    n_int = n_int_night = 0
    with OldNight():
        old_has = {}
        for i, (ts, loc) in enumerate(trace):
            if loc != "shore" or ts < START or ts > CUTOFF:
                continue
            if WC.daylight(ts) == "night":
                set_weather(PERMISSIVE)
                old_has[ts] = "gull_cries" in life.sounds_active("shore", ts)
    for i, (ts, loc) in enumerate(trace):
        if loc != "shore" or ts < START or ts > CUTOFF:
            continue
        nxt = trace[i + 1][0] if i + 1 < len(trace) else ts + 300.0
        dt = min(300.0, max(0.0, nxt - ts))
        ph = WC.daylight(ts)
        secs[ph] += dt
        set_weather(PERMISSIVE)
        has_new = "gull_cries" in life.sounds_active("shore", ts)
        n_int += 1
        if ph == "night":
            n_int_night += 1
            cries_new += dt / 3600.0 * 40.0 * has_new
            cries_old += dt / 3600.0 * 40.0 * old_has[ts]
        else:
            cries_new += dt / 3600.0 * 40.0 * has_new
            cries_old += dt / 3600.0 * 40.0 * has_new
    tot_h = sum(secs.values()) / 3600.0
    night_h = secs["night"] / 3600.0
    print(f"    shore hours 09-10 .. 09-21 18:30: {tot_h:.2f} h ({', '.join(f'{k} {v / 3600:.2f}' for k, v in sorted(secs.items()))}); night {night_h:.2f} h = {100 * night_h / tot_h:.1f}%")
    print(f"    modelled gull cries at 40/h: before {cries_old:.0f} (of which night {night_h * 40:.0f}), after {cries_new:.0f}")
    print(f"    => the change removes {cries_old - cries_new:.0f} cries ({100 * (cries_old - cries_new) / cries_old:.0f}% of the modelled total) that Du heard on the shore at night since the flip;"
          f" the ledger's own total 09-10..09-21 is {sum(v for k, v in (json.loads((_LIVE_DATA / 'sound_knowledge.json').read_text(encoding='utf-8')).get('hearings', {}).get('gull_cries', {}).get('days', {})).items() if k >= '2026-09-10')}")
    check(555 <= night_h * 40 <= 572, f"the night shore hours reproduce F-1614's ~563 night cries ({night_h * 40:.0f})")
    check(abs((cries_old - cries_new) - night_h * 40) < 1.0 and cries_new < cries_old, "with the old hours every one of those night intervals had gull_cries in the active set (fair-weather bound); with the new hours none does: ALL the night cries go, none of the dawn/day/dusk ones")
    check(n_int_night >= 100, f"({n_int_night} night intervals evaluated through the real sounds_active)")

# ═══ [4] ISOLATION PROOF ════════════════════════════════════════════════════════════════════════════════════════
print("\n[4] isolation")
for _m, _a in _REDIRECTS:
    check(_inside(getattr(_m, _a)), f"{_m.__name__}.{_a} still inside the temp dir")
life.note_deed(MARKER, "garden")
life._save(force=True)
check(MARKER in (TMP / "life_state.json").read_text(encoding="utf-8"), "the marker reached the isolated store through the engine's own write path")
_watch = [_LIVE_DATA / f for f in ("life_state.json", "life_ledger.jsonl", "life_events.jsonl", "room_state.json", "world_objects.json",
                                   "world_substrate.json", "provisions.json", "sound_knowledge.json", "world_traces.json", "position.json", "soundscape_state.json")]
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
for _p in (ROOT / "core" / "life.py", ROOT / "core" / "life_traces.py", ROOT / "core" / "life_birds.py", Path(__file__)):
    try:
        py_compile.compile(str(_p), cfile=str(TMP / (_p.name + "c")), doraise=True)
        check(True, f"py_compile {_p.name}")
    except py_compile.PyCompileError as exc:
        check(False, f"py_compile {_p.name}: {exc}")

print(f"\n{'ALL OK' if not FAILS else f'{FAILS} FAILURE(S)'} — {CHECKS} checks — isolated stores in {TMP}")
sys.exit(1 if FAILS else 0)
