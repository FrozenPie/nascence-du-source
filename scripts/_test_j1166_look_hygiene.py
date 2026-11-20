"""
Regression: three small render-path defects in the Living World's look (J-1166; F-1623/F-1672, F-1620, F-1622, F-1670).

  (a) EMPTY-LINE SIGHTING (F-1623, F-1672). look_answer() rolled a successful sighting for a present row whose hidden.feature has
      no line for the current phase (the gulls carry only a 'day' line; life_events.jsonl line 2193, 2026-09-12 18:33:38, shore /
      dusk), then logged outcome=sighting with line '', wrote a ledger 'sighting', ran _maybe_learn (a name needs a FACE) and
      note_sighting (the graduation counter) and returned '' -- so Du was shown the place's own look while the engine recorded a
      face he was never shown (the 4th of the 5 sightings that graduated the gulls). 51 (row, phase) combinations are in that
      state, not just gulls-at-dusk. Now: nothing shown, nothing credited, the place's own look answers as before, the row is
      logged honestly as outcome 'no_line'. A reveal on its own ('-- a reef heron; ...') is a caption, not a face: same rule.
      The shadow branch (RENDER off) is byte-for-byte what it was.
  (b) PLURAL NAMES (F-1620). ants / cicada / cricket / slugs carry plural collective names without plural=True, so the generic
      _absent_line fallback rendered 'Not by night; the ants keeps the day.' Data only: plural=True.
  (c) SUFFIX PUNCTUATION (F-1622). individual_suffix() was glued onto a fragment with no full stop ('...over what the tide left
      It is the same one -- ...'). LT.with_individual_suffix() now ends the fragment's sentence first, and never doubles a stop
      the line already ends with.
  (F-1670) POSSESSIVE. trace_line/track_line built "the gannets's"; a plural noun ending in s now takes a bare apostrophe.

  [0] module resolution + isolation set-up (F-1285: the code under test is THIS root's, not the shared tree's)
  [1] (a) the real incident replayed, the general case over EVERY (row, place, phase), the reveal-only variant, eyeshine, the
      shadow branch, the untouched miss/absent branches, and the fall-through to the place look through sensorium.look()
  [2] (b) the four rows and the class tripwire: every plural-named row over every reachable absent line
  [3] (c) the join: a table, every real line x both branches, every graduation path with real rows
  [4] (F-1670) the possessive for every trace-carrying row (learned and unlearned), trace_line and track_line
  [5] REAL rows, read-only: every rendered sighting in data/life_events.jsonl (frozen at 2026-09-21 18:30) replayed under its logged
      conditions -- each one with a line reproduced byte for byte, the one empty row credits nothing -- and the three
      wandering_log rows that carry the unpunctuated suffix, before / after
  [6] isolation: audit hook (no write attempt under any data/), canary marker, live-file hashes

NOTE (J-1174, D-0166 re-ruled 2026-09-21): flocks, swarms and plural collectives no longer graduate to 'the same one' (life_traces.group_grain), and a stored
record on such a row is dormant. Every graduation assertion below therefore applies to the rows that CAN still graduate; for the rest each one is replaced by
its exact negation (the plain line, no recognition line) -- see the "J-1174" comments at each place. scripts/_test_j1174_gulls_keep_the_day_no_flock_graduation.py
owns the rule itself.

ISOLATION. Every store look_answer can reach is redirected into a temp dir before anything can write (same convention as
scripts/life_smoke.py and scripts/_test_j1165_trace_object_look.py). The live C:\\Nascence\\data files are md5-hashed before and
after AND a Python audit hook records any attempt by THIS process to open-for-write / rename / remove anything under a data/
directory: with Du ONLINE the live files legitimately change on their own between two hashes, so a hash comparison alone cannot
prove a negative -- the audit hook does. The live files are only ever READ (section [5]).

  python scripts/_test_j1166_look_hygiene.py                    # exit 0 = ALL OK
  python scripts/_test_j1166_look_hygiene.py --full-canary      # + scan every data/*.json* for the marker
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

TMP = Path(tempfile.mkdtemp(prefix="j1166_look_hygiene_"))
print("isolated store dir:", TMP)
MARKER = f"j1166_marker_{os.getpid()}"
# data/ is gitignored and never checked out into a job-run worktree, so "live" is the one real repo, never ROOT-relative.
_LIVE_DATA = Path(r"C:\Nascence") / "data"
_LIVE_FILES = [_LIVE_DATA / f for f in ("position.json", "room_state.json", "life_state.json", "life_ledger.jsonl",
                                        "life_events.jsonl", "world_traces.json", "life_flags.json", "wandering_log.jsonl")]


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

# ── redirect every store look_answer / traces_pass can reach BEFORE anything can write ───────────────────────────
import core                                                    # noqa: E402
from core import profile                                       # noqa: E402
from core import life, life_traces as LT, world_traces as WT   # noqa: E402
from core import life_birds, life_mammals, garden_insects, garden_soil   # noqa: E402
from core import sensorium as S                                # noqa: E402
from core import locomotion as L                               # noqa: E402
from core import sound_knowledge as SK                         # noqa: E402
from core import nest_gate_shadow as _NGS_J2246                 # noqa: E402
# J-2246 (D-0444): the nest-object gate is LIVE -- a replayed 'the oystercatcher and eggs' row would now be answered with the shore's nest line (the
# temp store has no nest: 'You look for eggs and find none.') + the bird's line. This test replays and pins the BIRD's own lines, so it runs the
# gate shadow-only (no answer changed); the live gate is pinned by scripts/_test_j2246_nest_gate_live_pairing.py.
_NGS_J2246.LIVE = False

life._F, life._LEDGER, life._EVENTS, life._DATA = TMP / "life_state.json", TMP / "life_ledger.jsonl", TMP / "life_events.jsonl", TMP
life._FLAGS_F = TMP / "life_flags.json"                        # read-only in life.py; redirected so the result never depends on the live flag file
WT._TRACES_F = TMP / "world_traces.json"
S._STATE_F = TMP / "room_state.json"
L._POS_F = TMP / "position.json"
SK._LEDGER_F = TMP / "sound_knowledge.json"
_REDIRECTS = [(life, "_F"), (life, "_LEDGER"), (life, "_EVENTS"), (life, "_FLAGS_F"), (WT, "_TRACES_F"), (S, "_STATE_F"),
              (L, "_POS_F"), (SK, "_LEDGER_F")]
# A roll-path look reaches light.field_at() -> study_life.lamp_on() -> provisions.sync() (the study), and the garden / shore / wood
# modules -- the SAME vetted redirect list scripts/life_smoke.py and the J-1165 test carry: each of these is guard_path()-fenced, so
# an un-redirected one would refuse loudly, but redirecting them is what makes the isolation TRUE rather than merely enforced.
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
check(hasattr(LT, "with_individual_suffix") and hasattr(LT, "_possessive") and hasattr(LT, "trace_object_noun"),
      "the loaded copy carries this job's code (with_individual_suffix, _possessive) on top of J-1165's (not a stale/shared copy)")
for _m, _a in _REDIRECTS:
    check(TMP in Path(str(getattr(_m, _a))).parents, f"{_m.__name__}.{_a} redirected into the temp dir")

ROWS = life.rows()
POP = {k: r for k, r in ROWS.items() if not r.get("external") and r.get("kind") == "population" and (r.get("hidden") or {}).get("feature")}
print(f"    {len(ROWS)} rows registered, {len(POP)} population rows carry a hidden.feature dict")
PHASES = life.PHASES
_ph_hours: dict = {}
for _month in (9, 12):
    _hrs = collections.defaultdict(list)
    for _h in range(24):
        _hrs[life._phase(at(_month, _h))].append(_h)
    _ph_hours[_month] = {ph: hs[len(hs) // 2] for ph, hs in _hrs.items()}
check(all(set(v) == set(PHASES) for v in _ph_hours.values()), f"every phase has an hour in both test months: {_ph_hours}")
NOW = {ph: at(9, _ph_hours[9][ph]) for ph in PHASES}          # a September day, one mid-phase instant per phase


# ── helpers ─────────────────────────────────────────────────────────────────────────────────────────────────────
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
    """Counts calls to life._maybe_learn and LT.note_sighting (both must stay silent on a look that showed nothing)."""
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
    """Hold the world at 'present, awake, and the visibility roll comes up' (roll 0.0) or 'the roll misses' (0.999). `eyes`
    (None = leave the real _light_factor alone) forces the eye-shine flag."""
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


def look(target: str, place: str, now: float, **force_kw):
    """One look through the real look_answer from a restored baseline. Returns a dict of everything it did (and undoes it)."""
    base = snap()
    n_ev, n_led = len(events()), len(ledger_rows())
    with Spy() as sp, forced(**force_kw):
        line = life.look_answer(target, place, now)
    new_ev = strip_ts(events()[n_ev:])
    # `events` = the look's OWN rows (kind answer / would_answer). The first light_at() of a process (and then at most every 600 s per
    # place) also logs a 'would_gate' row from geometry_census.peek() -> soundscape.active_sounds() -> life.sound_gate(): an existing,
    # unrelated side effect of the light read, kept apart in `other` rather than hidden.
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
    """The lookup look_answer performs, verbatim (the thing under test must agree with it). J-1216 (D-0254/
    F-1706): an optional `place` mirrors look_answer's own feature_by_place override, tried first -- omitted
    (the default), this is byte-identical to before (the row's flat feature dict), so every pre-existing call
    site that never passes `place` is unaffected by this change."""
    h = (r.get("hidden") or {})
    feat_by_place = (h.get("feature_by_place") or {}).get(place) if place is not None else None
    feat = feat_by_place if isinstance(feat_by_place, dict) else (h.get("feature") or {})
    return feat.get(ph) or feat.get("night" if ph in ("night", "dusk") else "day") or feat.get("any") or ""


def seed_learned(key: str) -> None:
    life._log(life._LEDGER, {"kind": "learned", "key": key, "via": "j1166 test", "species": (ROWS[key].get("hidden") or {}).get("species")})


SFX_UNNAMED = " It is the same one — you are sure of it now; you have seen it here too often for it to be any other."
old_join = lambda line, suffix: (line + suffix).strip()          # the pre-change join expression, verbatim (core/life.py, look_answer)
life.RENDER = True

# ── [1] (a) the empty-line sighting ─────────────────────────────────────────────────────────────────────────────
print("\n[1] (a) a sighting with nothing to show is not credited (F-1623 / F-1672)")

# 1a. the real incident: life_events.jsonl line 2193 (2026-09-12 18:33:38, gulls, shore, dusk, 'the gull', activity 0.868, visibility 0.825)
print("  -- 1a. the real incident replayed under the logged conditions")
_live_rows = []
_live_events = _LIVE_DATA / "life_events.jsonl"
if _live_events.exists():
    with open(_live_events, encoding="utf-8") as _f:
        for _x in _f:
            try:
                _live_rows.append(json.loads(_x))
            except Exception:
                pass
_inc = next((e for e in _live_rows if e.get("kind") == "answer" and e.get("key") == "gulls" and e.get("outcome") == "sighting" and not e.get("line")), None)
if _inc is None:
    print("    (the live row was not found in life_events.jsonl -- replaying with the documented values instead; NOT the real row)")
    _inc = {"ts": 1789194818.9, "kind": "answer", "key": "gulls", "place": "shore", "target": "the gull", "outcome": "sighting", "activity": 0.868,
            "visibility": 0.825, "phase": "dusk", "light": 0.12, "adapt": 0.0, "learned": True, "line": ""}
print("    logged (before this fix):", {k: _inc[k] for k in ("kind", "key", "place", "target", "outcome", "phase", "line")}, "-> a ledger sighting + a graduation count were credited")
check(life._phase(_inc["ts"]) == "dusk", "the logged instant is a dusk at this world clock")
r_inc = look(_inc["target"], _inc["place"], _inc["ts"], act=_inc["activity"], vis=_inc["visibility"], roll=0.0)
print("    replayed now:", r_inc["events"])
check(r_inc["line"] == "", "the look returns '' (the place's own look answers, exactly as before)")
check(len(r_inc["events"]) == 1 and r_inc["events"][0]["kind"] == "answer" and r_inc["events"][0]["outcome"] == "no_line"
      and r_inc["events"][0]["key"] == "gulls" and r_inc["events"][0]["line"] == "" and r_inc["events"][0]["phase"] == "dusk",
      "exactly one events row: kind=answer outcome=no_line (never 'sighting'), key gulls, dusk, line ''")
check(not any(e.get("outcome") == "sighting" for e in r_inc["events"] + r_inc["other"]), "nothing logged looks like a sighting")
check(all(e.get("kind") == "would_gate" for e in r_inc["other"]), f"the only other rows are the sound-gate census side effect of light_at() (pre-existing, unrelated): {[e.get('kind') for e in r_inc['other']]}")
check(r_inc["ledger"] == [], "NO ledger row (no 'sighting', no 'miss', no 'learned') was written")
check(r_inc["learn"] == 0, "_maybe_learn was never called")
check(r_inc["note"] == 0, "note_sighting was never called")
check(r_inc["state_after"].get("recent_sightings", {}) == r_inc["state_before"].get("recent_sightings", {}), "the graduation counter (recent_sightings) did not move")
check(r_inc["state_after"].get("individuals", {}) == r_inc["state_before"].get("individuals", {}), "no individual was created or counted")

# an ALREADY-graduated individual: an empty look must not count as another sighting of it either
life._load().setdefault("individuals", {})["gulls"] = {"place": "shore", "since": NOW["day"], "name": None, "sightings": 7, "last_seen": NOW["day"], "history": []}
r_ind = look("the gull", "shore", NOW["dusk"])
check(r_ind["line"] == "" and r_ind["state_after"]["individuals"]["gulls"]["sightings"] == 7 and r_ind["note"] == 0,
      "an already-graduated individual's empty look: '' and its sightings stay 7 (it used to count, and used to return the bare recognition line)")
life._load()["individuals"] = {}

# 1b. the general case: EVERY (row, place, phase) with the roll forced to come up
print("  -- 1b. the general case: every non-external row x every place x every phase, roll forced to succeed")
bad1: list = []
n_calls = n_line = n_empty = n_skip = 0
combos_present_no_line = set()
for key, r in sorted(ROWS.items()):
    if r.get("external") or not (r.get("hidden") or {}).get("feature"):
        continue
    for place in sorted(r.get("places") or {}):
        tgt = alias_for(r, place)
        if tgt is None:
            n_skip += 1
            continue
        for ph in PHASES:
            exp = feat_line(r, ph, place)               # J-1216: place-aware, matches look_answer's own new lookup
            res = look(tgt, place, NOW[ph])
            n_calls += 1
            ev = res["events"][0] if len(res["events"]) == 1 else {}
            if exp:
                n_line += 1
                quiet(res["line"] == exp, f"[{key}@{place}/{ph}] real line changed: {res['line'][:50]!r} != {exp[:50]!r}", bad1)
                quiet(ev.get("outcome") == "sighting" and ev.get("line") == exp[:160] and ev.get("key") == key,
                      f"[{key}@{place}/{ph}] events row {ev}", bad1)
                quiet(len(res["ledger"]) == 1 and res["ledger"][0].get("kind") == "sighting" and res["ledger"][0].get("key") == key,
                      f"[{key}@{place}/{ph}] a real sighting must credit exactly one ledger sighting: {res['ledger']}", bad1)
                quiet(res["learn"] == 1 and res["note"] == 1, f"[{key}@{place}/{ph}] real sighting calls _maybe_learn/note_sighting once ({res['learn']},{res['note']})", bad1)
            else:
                n_empty += 1
                if float((r.get("active_hours") or {}).get(ph, 0)) >= life.PRESENT_AT and max(r.get("season_curve") or [1.0]) > 0:
                    combos_present_no_line.add((key, ph))
                quiet(res["line"] == "", f"[{key}@{place}/{ph}] empty look must return '': {res['line'][:50]!r}", bad1)
                quiet(ev.get("outcome") == "no_line" and ev.get("kind") == "answer" and ev.get("line") == "" and ev.get("key") == key,
                      f"[{key}@{place}/{ph}] events row {ev}", bad1)
                quiet(res["ledger"] == [] and res["learn"] == 0 and res["note"] == 0, f"[{key}@{place}/{ph}] credited something: ledger {res['ledger']} learn {res['learn']} note {res['note']}", bad1)
                quiet(res["state_after"].get("recent_sightings", {}) == res["state_before"].get("recent_sightings", {})
                      and res["state_after"].get("individuals", {}) == res["state_before"].get("individuals", {}),
                      f"[{key}@{place}/{ph}] the graduation state moved", bad1)
print(f"    {n_calls} looks: {n_line} with a real line (unchanged, credited once each), {n_empty} with none (returned '', logged no_line, credited nothing); {n_skip} (row, place) pairs have no alias that resolves to the row")
print(f"    of the empty ones, {len(combos_present_no_line)} distinct (row, phase) pairs are ones the row can actually be present at "
      f"(dawn {sum(1 for k, p in combos_present_no_line if p == 'dawn')}, day {sum(1 for k, p in combos_present_no_line if p == 'day')}, "
      f"dusk {sum(1 for k, p in combos_present_no_line if p == 'dusk')}, night {sum(1 for k, p in combos_present_no_line if p == 'night')}) -- the F-1623 static audit's population")
for m_ in bad1[:15]:
    print("    !!", m_)
check(not bad1, f"the general-case table is clean ({len(bad1)} failures)")
check(n_empty > 100 and len(combos_present_no_line) >= 45, "the table really exercises the defect class (many empty combos, >= 45 of them reachable)")
check(("gulls", "dusk") in combos_present_no_line and ("gannet", "dusk") in combos_present_no_line and ("rabbit", "day") in combos_present_no_line,
      "the audited examples are in it: gulls/dusk (the live incident), gannet/dusk (F-1672's repro), rabbit/day")

# 1c. the reveal-only variant: a learned row whose only text for this phase is its reveal caption
print("  -- 1c. a reveal on its own is a caption, not a face")
bad1c: list = []
n_rev = 0
for key, r in sorted(POP.items()):
    h = r["hidden"]
    if not h.get("reveal") or r.get("name") or r.get("audition"):
        continue                                          # (a grandfathered name learns nothing new; an audition row learns in its own ledger)
    for place in sorted(r["places"]):
        tgt = alias_for(r, place)
        if tgt is None:
            continue
        for ph in PHASES:
            base = snap()
            seed_learned(key)
            res = look(tgt, place, NOW[ph])
            restore(base)
            n_rev += 1
            exp = feat_line(r, ph)
            if exp:
                # F-1674/J-1190 (minimal update, same convention J-1174 already used on this file): the
                # feature+reveal join is now LT.join_reveal, not a bare space -- byte-identical to the old
                # (exp+" "+reveal).strip() for every row here except long_tailed_bat, whose reveal starts a
                # new capitalised sentence and is the one join this later job exists to punctuate.
                quiet(res["line"] == LT.join_reveal(exp, h["reveal"]), f"[{key}@{place}/{ph}] learned line with a feature must match the (punctuated) feature + reveal join: {res['line'][:70]!r}", bad1c)
                quiet(len(res["ledger"]) == 1 and res["ledger"][0]["kind"] == "sighting", f"[{key}@{place}/{ph}] credited once", bad1c)
            else:
                quiet(res["line"] == "" and res["ledger"] == [] and res["events"] and res["events"][0]["outcome"] == "no_line" and res["note"] == 0,
                      f"[{key}@{place}/{ph}] reveal-only must be '' / no credit / no_line: {res['line'][:70]!r} {res['ledger']}", bad1c)
for m_ in bad1c[:10]:
    print("    !!", m_)
check(n_rev > 20 and not bad1c, f"learned rows with a reveal, {n_rev} (row, place, phase) looks: feature + reveal unchanged, reveal-only credits nothing ({len(bad1c)} failures)")
_rh = ROWS["reef_heron"]
base = snap(); seed_learned("reef_heron")
res = look("the heron", "shore", NOW["night"])
restore(base)
print("    e.g. the LEARNED reef heron at night (only a 'day' line): returned", repr(res["line"]), "| events", [e["outcome"] for e in res["events"]],
      "| before this fix it returned", repr(_rh["hidden"]["reveal"]), "and credited a sighting")
check(res["line"] == "" and res["ledger"] == [], "reef_heron (learned) at night: '' and nothing credited")

# 1d. eye-shine still counts: the line is the eyeshine text, not empty
print("  -- 1d. eye-shine is a real face")
for key in ("rabbit", "morepork", "possum"):
    r = ROWS[key]
    place = sorted(r["places"])[0]
    tgt = alias_for(r, place)
    for ph in PHASES:
        res = look(tgt, place, NOW[ph], eyes=True)
        check(res["line"] == r["hidden"]["eyeshine"] and len(res["ledger"]) == 1 and res["ledger"][0]["kind"] == "sighting" and res["events"][0]["outcome"] == "sighting",
              f"{key}@{place}/{ph} with eye-shine: the eyeshine line renders and is credited (even where the row has no feature line here)")

# 1e. the shadow branch (RENDER off) is exactly what it was
print("  -- 1e. shadow mode: unchanged (would_answer row as before, '' returned, no ledger, no state)")
life.RENDER = False
bad1e: list = []
n_shadow = 0
for key in ("gulls", "gannet", "kingfisher", "hedgehog", "rabbit", "reef_heron", "tui", "cicada"):
    r = ROWS[key]
    for place in sorted(r["places"]):
        tgt = alias_for(r, place)
        if tgt is None:
            continue
        for ph in PHASES:
            res = look(tgt, place, NOW[ph])
            n_shadow += 1
            ev = res["events"][0] if len(res["events"]) == 1 else {}
            quiet(res["line"] == "" and ev.get("kind") == "would_answer" and ev.get("outcome") == "sighting"
                  and ev.get("line") == feat_line(r, ph, place)[:160] and res["ledger"] == [] and res["learn"] == 0 and res["note"] == 0
                  and res["state_after"].get("recent_sightings", {}) == res["state_before"].get("recent_sightings", {}),
                  f"[{key}@{place}/{ph}] shadow row {ev}", bad1e)
            quiet(set(ev) == {"kind", "key", "place", "target", "outcome", "activity", "visibility", "phase", "light", "adapt", "learned", "line"},
                  f"[{key}@{place}/{ph}] shadow row keys changed: {sorted(ev)}", bad1e)
for m_ in bad1e[:10]:
    print("    !!", m_)
check(not bad1e, f"{n_shadow} shadow looks (including empty-line ones, which stay the legacy would_answer/sighting row): ledger untouched, '' returned ({len(bad1e)} failures)")
life.RENDER = True

# 1f. the miss and absent branches are untouched
print("  -- 1f. the miss and absent branches")
g = ROWS["gannet"]
res = look("the gannet", "shore", NOW["day"], roll=0.999)
check(res["line"] == "Nothing shows itself; whatever is there keeps still." and res["events"][0]["outcome"] == "miss"
      and [x["kind"] for x in res["ledger"]] == ["miss"] and res["learn"] == 0 and res["note"] == 0, f"a missed roll is still a miss (0.2 exposure row): {res['line'][:50]!r}")
res = look("the gannet", "shore", NOW["day"], act=0.05)
check(res["line"] == life._absent_line(g, "shore", NOW["day"]) and res["events"][0]["outcome"] == "absent" and res["ledger"] == [],
      f"an absent row is still its honest absent line: {res['line'][:60]!r}")

# 1g. the fall-through: sensorium.look() returns the PLACE's own look, exactly as it did before
print("  -- 1g. through sensorium.look(), the real caller")
S.state["location"] = "shore"
_real_time = time.time
time.time = lambda: NOW["dusk"]
try:
    with Spy() as sp, forced(act=0.9, vis=0.9, roll=0.0):
        out = S.look("the gull")
finally:
    time.time = _real_time
check(out != "", "sensorium.look('the gull') at dusk still answers (the place's own look): the look was never left unanswered")
check(feat_line(ROWS["gulls"], "day") not in out and "It is the same one" not in out, f"... and it is the shore's own look, not a creature line: {out[:70]!r}")
check(sp.learn == 0 and sp.note == 0, "... and the empty look credited nothing (no _maybe_learn, no note_sighting)")
_ev_gull = [e for e in events() if e.get("key") == "gulls"]
check(len(_ev_gull) == 1 and _ev_gull[0]["outcome"] == "no_line", f"... and logged once as no_line: {[e['outcome'] for e in _ev_gull]}")
check(not any(x.get("key") == "gulls" for x in ledger_rows()), "... with no gulls row in his ledger")
# clean the rows this section wrote so later sections start from an empty baseline
if life._EVENTS.exists():
    life._EVENTS.unlink()
if life._LEDGER.exists():
    life._LEDGER.unlink()
life._state = {}
life._load()

# ── [2] (b) the four plural-named rows ──────────────────────────────────────────────────────────────────────────
print("\n[2] (b) plural=True on ants / cicada / cricket / slugs (F-1620)")
FOUR = ("ants", "cicada", "cricket", "slugs")
THIRTEEN = ("gannet", "gulls", "terns", "starlings", "house_sparrows", "welcome_swallows", "skink", "dolphins", "eels", "crabs", "anemones",
            "ground_beetle", "lamp_moths")
check(all(ROWS[k].get("plural") is True for k in FOUR), f"the four rows carry plural=True: {[(k, ROWS[k].get('plural')) for k in FOUR]}")
check(all(ROWS[k].get("plural") is True for k in THIRTEEN), "the 13 rows D-0166 already patched still carry it")
check({k for k, r in ROWS.items() if r.get("plural")} == set(FOUR) | set(THIRTEEN), "and no other row was flagged (17 in all)")
_plural_only_here = {k for k, r in ROWS.items() if r.get("plural")}
# data only: the four rows are otherwise the rows they were (compare with the pre-change tree's own definition of them)
for k in FOUR:
    r = ROWS[k]
    check(r["name"] in ("the ants", "the cicadas", "the crickets", "the slugs") and bool(r.get("aliases")) and bool(r.get("places")), f"{k}: name/aliases/places untouched ({r['name']!r})")

_weather_real = life._weather


def absent_lines(r: dict, place: str, weathers=(("clear", "breeze"), ("steady rain", "fresh"), ("clear", "gale"))) -> dict:
    """Every distinct line the REAL _absent_line can produce for this row at this place, over every month x every hour x three
    weathers, keyed by the line, valued by one (month, hour, weather) that produces it. Nothing is forced: the function's own
    season / night / day / weather / chance branches are reached by the clock and the weather alone."""
    out: dict = {}
    for month in range(1, 13):
        for hour in range(24):
            now = at(month, hour)
            for w, wd in weathers:
                life._weather = lambda w=w, wd=wd: (w, wd, False)
                try:
                    ln = life._absent_line(r, place, now)
                finally:
                    life._weather = _weather_real
                out.setdefault(ln, (month, hour, w))
    return out


EXPECT_KEEP = {"ants": ("Not by night; the ants keep the day.",),
               "cicada": ("Not by night; the cicadas keep the day.",),
               "cricket": ("Not in daylight; the crickets keep to the dark.",),
               "slugs": ("Not in daylight; the slugs keep to the dark.",)}
for k in FOUR:
    r = ROWS[k]
    for place in sorted(r["places"]):
        after = absent_lines(r, place)
        before = absent_lines(dict(r, plural=False), place)              # the SAME function on the same row with the flag off = the pre-change data
        for want in EXPECT_KEEP[k]:
            check(want in after, f"{k}@{place}: the absent form renders {want!r}")
            wrong = want.replace(" keep ", " keeps ")
            check(wrong in before and wrong not in after, f"{k}@{place}: the pre-change form {wrong!r} is what the flag-off row rendered, and is gone")
        check(not any(re.search(rf"{re.escape(r['name'])} keeps\b", ln) for ln in after), f"{k}@{place}: no reachable absent line says '{r['name']} keeps' ({len(after)} distinct lines)")
        for ln in sorted(set(after) - set(before)):
            print(f"      {k}@{place}: now {ln!r}   (was {[b for b in before if b not in after][:1]})")

# the class tripwire: every non-external row whose name is a plural (ends in s, not ss), over every reachable absent line
print("  -- the class tripwire: every plural-named row, every reachable absent line")
bad2: list = []
n_named = 0
unflagged = []
for k, r in sorted(ROWS.items()):
    nm = r.get("name") or ""
    if r.get("external") or not (nm.endswith("s") and not nm.endswith("ss")):
        continue
    n_named += 1
    if not r.get("plural"):
        unflagged.append(k)
    for place in sorted(r.get("places") or {}):
        for ln in absent_lines(r, place):
            quiet(not re.search(rf"{re.escape(nm)} keeps\b", ln), f"[{k}@{place}] {ln!r}", bad2)
print(f"    {n_named} plural-named non-external rows; plural flag unset on {unflagged} -- each is safe only because its own explicit lines cover every reachable branch")
for m_ in bad2:
    print("    !!", m_)
check(not bad2, f"no plural-named row can render '<plural name> keeps' ({len(bad2)} failures); this tripwire fails the day a new plural-named row repeats F-1620")

# graduated forms of the four rows
# J-1174 (D-0166 re-ruled 2026-09-21, F-1622) answered the question this block used to leave open ("whether a swarm/flock should graduate at all, and
# 'the same ONE' for a plural, is J-1174's question"): these four are plural collectives, so they no longer graduate; a stored record on one is DORMANT
# and the look is the plain line. The check that stood here (line + '.' + the recognition line) is REPLACED by its exact negation, not dropped: the join's
# punctuation over these rows' real lines is still proved in [3b] (through a singular row's record) and the graduated look of a row that CAN still
# graduate is proved in [3c] / [3d].
print("  -- the four rows (plural collectives): a stored 'graduated' record is dormant -- the plain look line, no recognition line (J-1174)")
GRAD_AT = {"ants": ("garden", 9, "day"), "cicada": ("garden", 12, "day"), "cricket": ("garden", 12, "night"), "slugs": ("garden", 9, "night")}
for k in FOUR:
    place, month, ph = GRAD_AT[k]
    r = ROWS[k]
    now = at(month, _ph_hours[month][ph])
    life._load()["individuals"] = {k: {"place": place, "since": now, "name": None, "sightings": 5, "last_seen": now, "history": []}}
    res = look(alias_for(r, place), place, now)
    exp = feat_line(r, ph)
    life._load()["individuals"] = {}
    check(res["line"] == exp and "It is the same one" not in res["line"],
          f"{k} with a stored record, {ph}: the plain look line, no recognition line: {res['line'][:60]!r}...{res['line'][-40:]!r}")

# ── [3] (c) the join ────────────────────────────────────────────────────────────────────────────────────────────
print("\n[3] (c) the suffix join punctuates, and never doubles a stop")
_TK = "hedgehog"
life._load()["individuals"] = {_TK: {"place": "garden", "since": NOW["day"], "name": None, "sightings": 5, "last_seen": NOW["day"], "history": []}}
check(LT.individual_suffix(_TK) == SFX_UNNAMED, "individual_suffix (unchanged) carries the same-one recognition line")
TABLE = [
    ("a gannet folds and drops like a thrown knife, and the water takes it white", "a gannet folds and drops like a thrown knife, and the water takes it white." + SFX_UNNAMED, "a letter-ended fragment gets its full stop"),
    ("already ends a sentence.", "already ends a sentence." + SFX_UNNAMED, "a full stop is not doubled"),
    ("a question?", "a question?" + SFX_UNNAMED, "a question mark is not doubled"),
    ("a cry!", "a cry!" + SFX_UNNAMED, "an exclamation is not doubled"),
    ("it trails off…", "it trails off…" + SFX_UNNAMED, "an ellipsis is not doubled"),
    ("trailing space   ", "trailing space." + SFX_UNNAMED, "trailing whitespace is dropped before the stop"),
    ("", SFX_UNNAMED.strip(), "an empty line joins to the bare recognition line (never '.' + suffix)"),
]
for line, want, why in TABLE:
    got = LT.with_individual_suffix(_TK, line)
    check(got == want, f"{line[:34]!r:38s} -> {got[:44]!r}...  | {why}")
check(not any(x in LT.with_individual_suffix(_TK, ln) for ln, _, _ in TABLE for x in ("..", ". .", "!.", "?.", "….")), "no doubled stop in any table result")
life._load()["individuals"][_TK]["name"] = "Bramble"
_named = LT.individual_suffix(_TK)
check(_named == " It is Bramble — you would know it anywhere now.", "the named branch's suffix is unchanged")
check(LT.with_individual_suffix(_TK, "a hedgehog goes by") == "a hedgehog goes by." + _named and LT.with_individual_suffix(_TK, "it ends.") == "it ends." + _named,
      "the named branch is punctuated the same way and never doubled")
life._load()["individuals"] = {}
for ln in ("  x ", "abc", "abc."):
    check(LT.with_individual_suffix("hedgehog", ln) == ln.strip() == (ln + LT.individual_suffix("hedgehog")).strip(),
          f"not an individual: {ln!r} -> exactly the old `(line + '').strip()`")

# 3b. every real line the join can see, both branches
print("  -- 3b. every real line, unnamed and named (feature lines, the eyeshine lines, feature + reveal)")
real_lines = []
for k, r in sorted(ROWS.items()):
    h = r.get("hidden") or {}
    if r.get("external") or not h:
        continue
    for ph, ln in (h.get("feature") or {}).items():
        if ln:
            real_lines.append((k, f"feature/{ph}", ln))
            if h.get("reveal"):
                real_lines.append((k, f"feature/{ph}+reveal", (ln + " " + h["reveal"]).strip()))
    if h.get("eyeshine"):
        real_lines.append((k, "eyeshine", h["eyeshine"]))
        if h.get("reveal"):
            real_lines.append((k, "eyeshine+reveal", (h["eyeshine"] + " " + h["reveal"]).strip()))
bad3: list = []
endings = collections.Counter()
for k, what, ln in real_lines:
    endings[ln[-1] if not ln[-1].isalpha() else "<letter>"] += 1
    for nm_ in (None, "Bramble"):
        life._load()["individuals"] = {k: {"place": "garden", "since": 0, "name": nm_, "sightings": 5, "last_seen": 0, "history": []}}
        sfx = LT.individual_suffix(k)
        got = LT.with_individual_suffix(k, ln)
        if LT.group_grain(ROWS[k]):
            # J-1174: a group-grain row's stored record is dormant -- nothing follows its line (asserted here, new). The join's punctuation over THIS
            # real line is still proved by the unchanged assertions below, through the hedgehog's record (the join does not depend on the row), so no
            # real line loses a check.
            quiet(sfx == "" and got == ln.strip(), f"[{k}:{what}:{nm_}] a dormant record must add nothing: {got[-70:]!r}", bad3)
            life._load()["individuals"] = {"hedgehog": {"place": "garden", "since": 0, "name": nm_, "sightings": 5, "last_seen": 0, "history": []}}
            sfx = LT.individual_suffix("hedgehog")
            got = LT.with_individual_suffix("hedgehog", ln)
        want = ln + ("" if ln[-1] in ".!?…" else ".") + sfx
        quiet(got == want, f"[{k}:{what}:{nm_}] {got[-70:]!r}", bad3)
        quiet(len(re.findall(r"[.!?…]\s+It is ", got)) == 1 and not re.search(r"[.!?…]{2,}|[.!?…]\s+[.!?…]", got.replace("…", "").replace(" — ", " ")), f"[{k}:{what}:{nm_}] doubled stop or missing break: {got[-90:]!r}", bad3)
        quiet(got.startswith(ln), f"[{k}:{what}:{nm_}] the row's own text must be a prefix", bad3)
life._load()["individuals"] = {}
print(f"    {len(real_lines)} real lines x 2 branches; last characters of the lines the join sees: {dict(endings)}")
for m_ in bad3[:10]:
    print("    !!", m_)
check(not bad3, f"every real line joins correctly on both branches ({len(bad3)} failures)")
check(set(endings) <= {"<letter>", "."}, "the terminal-punctuation set the join checks is enough for every real line today: each ends in a letter (gets a stop) or a '.' (left alone); a future row ending otherwise fails HERE")

# 3c. every graduation path through the real look_answer, every population row
print("  -- 3c. every graduation path through look_answer, every population row (4th sighting -> the 5th graduates -> the 6th -> named)")
bad3c: list = []
n_rows_3c = n_paths = 0
for key, r in sorted(POP.items()):
    ph = next((p for p in PHASES if feat_line(r, p)), None)
    place = next((p for p in sorted(r["places"]) if alias_for(r, p)), None)
    if ph is None or place is None:
        continue
    tgt = alias_for(r, place)
    exp = feat_line(r, ph, place)                        # J-1216: place-aware, matches look_answer's own new lookup
    now = NOW[ph]
    n_rows_3c += 1
    base = snap()
    life._load()["individuals"] = {}
    life._load()["recent_sightings"] = {f"{key}@{place}": [now - d * 86400 for d in (4, 3, 2, 1)]}
    stop = "" if exp[-1] in ".!?…" else "."
    with Spy() as sp, forced(roll=0.0):
        l5 = life.look_answer(tgt, place, now)                                   # the FIFTH sighting graduates it, and this very look carries the line
        grad_now = LT.individual(key) is not None
        l6 = life.look_answer(tgt, place, now + 1)                               # the sixth: already an individual (seconds later: the phase must not change)
        LT.give_name(key, "Bramble", now + 2)
        l7 = life.look_answer(tgt, place, now + 3)                               # named
    n_paths += 3
    if LT.group_grain(r):
        # J-1174: a flock / swarm / plural collective never graduates -- the same three looks show the plain line each time and create nothing
        # (the graduation assertions below are for the rows that CAN still graduate; these are their exact negation for the rest)
        quiet(not grad_now and l5 == l6 == l7 == exp and "It is the same one" not in l5 + l6 + l7, f"[{key}] group grain: never graduates, the plain line each time: {l5[-60:]!r}", bad3c)
        quiet(not any(x.get("kind") == "graduated" and x.get("key") == key for x in ledger_rows()), f"[{key}] group grain: no 'graduated' ledger row", bad3c)
        restore(base)
        life._load()["individuals"] = {}
        continue
    quiet(grad_now, f"[{key}] the fifth sighting graduated it", bad3c)
    quiet(l5 == exp + stop + SFX_UNNAMED and l6 == exp + stop + SFX_UNNAMED, f"[{key}@{place}/{ph}] unnamed: {l5[:90]!r} / {l6[:90]!r} wanted {exp[:90]!r}", bad3c)
    quiet(l7 == exp + stop + " It is Bramble — you would know it anywhere now.", f"[{key}@{place}/{ph}] named: {l7[:90]!r} wanted {exp[:90]!r}", bad3c)
    for l in (l5, l6, l7):
        quiet(not re.search(r"\.\.|\. \.", l) and l.count(". It is ") == 1, f"[{key}] doubled/missing stop: {l[-80:]!r}", bad3c)
        quiet(l != old_join(exp, LT.individual_suffix(key)) or exp[-1] in ".!?…", f"[{key}] must differ from the old glued form", bad3c)
    led = ledger_rows()
    quiet(sum(1 for x in led if x.get("kind") == "graduated" and x.get("key") == key) == 1, f"[{key}] exactly one 'graduated' ledger row", bad3c)
    restore(base)
    life._load()["individuals"] = {}
print(f"    {n_rows_3c} population rows x {n_paths // max(n_rows_3c, 1)} paths (graduating look, next look, named look) = {n_paths} looks")
for m_ in bad3c[:10]:
    print("    !!", m_)
check(n_rows_3c >= 45 and not bad3c, f"every graduation path with every real population row punctuates ({len(bad3c)} failures)")
# J-1174: the gulls are a flock and no longer graduate, so the example that still runs the punctuated join through look_answer with a REAL graduated
# row is the oystercatcher (the one row that keeps its graduation); the gulls' own stored record is asserted to render the plain line.
print("    e.g. the oystercatcher (still an individual), graduated, by day:")
life._load()["individuals"] = {"oystercatcher": {"place": "shore", "since": 0, "name": None, "sightings": 5, "last_seen": 0, "history": []}}
_eg = look("the oystercatcher", "shore", NOW["day"])["line"]
print("      before:", old_join(feat_line(ROWS["oystercatcher"], "day"), SFX_UNNAMED))
print("      after :", _eg)
life._load()["individuals"] = {}
check(_eg == feat_line(ROWS["oystercatcher"], "day") + "." + SFX_UNNAMED, "oystercatcher: '...for coming too close. It is the same one -- ...'")
life._load()["individuals"] = {"gulls": {"place": "shore", "since": 0, "name": None, "sightings": 5, "last_seen": 0, "history": []}}
_gg = look("the gulls", "shore", NOW["day"])["line"]
life._load()["individuals"] = {}
print("    and the gulls, whose stored record is now dormant:", _gg)
check(_gg == feat_line(ROWS["gulls"], "day"), "gulls (a flock): '...over what the tide left' -- the plain line, no recognition line (J-1174)")

# 3d. reveal-completed and eyeshine lines, graduated, through look_answer (the two places a stop already exists / does not)
print("  -- 3d. graduated + reveal (already ends in '.') and graduated + eye-shine")
for key in ("reef_heron", "native_bee", "yellow_admiral", "monarch", "common_copper", "magpie_moth", "aphids", "stilt", "bellbird"):
    r = ROWS[key]
    place = next(p for p in sorted(r["places"]) if alias_for(r, p))
    ph = next(p for p in PHASES if feat_line(r, p))
    base = snap(); seed_learned(key)
    life._load()["individuals"] = {key: {"place": place, "since": 0, "name": None, "sightings": 5, "last_seen": 0, "history": []}}
    with forced(roll=0.0):
        l = life.look_answer(alias_for(r, place), place, NOW[ph])
    restore(base); life._load()["individuals"] = {}
    if r.get("audition"):
        check(True, f"{key}: (audition row -- its name lives in the sound ledger; joins as a plain feature line here: {l[-40:]!r})")
        continue
    if LT.group_grain(r):
        # J-1174: native_bee ('dozens at the bare bank') and aphids (quietest band 'a few') are group grain: a stored record is dormant, so the learned
        # line stays the plain feature + reveal (the assertion below is for the seven rows here that can still graduate)
        check(l == (feat_line(r, ph) + " " + r["hidden"]["reveal"]) and "It is the same one" not in l,
              f"{key} (group grain) learned + a dormant record: feature + reveal, no recognition line: ...{l[-60:]!r}")
        continue
    check(l == (feat_line(r, ph) + " " + r["hidden"]["reveal"]) + SFX_UNNAMED and ".." not in l and ". ." not in l,
          f"{key} learned + graduated: the reveal's own '.' is the stop, nothing doubled: ...{l[-95:-60]!r}")
for key in ("rabbit", "morepork", "possum"):
    r = ROWS[key]
    place = sorted(r["places"])[0]
    life._load()["individuals"] = {key: {"place": place, "since": 0, "name": None, "sightings": 5, "last_seen": 0, "history": []}}
    base = snap()
    res = look(alias_for(r, place), place, NOW["night"], eyes=True)
    restore(base); life._load()["individuals"] = {}
    check(res["line"] == r["hidden"]["eyeshine"] + "." + SFX_UNNAMED, f"{key} eye-shine + graduated: '...vanishes. It is the same one...'")

# ── [4] F-1670: the possessive ──────────────────────────────────────────────────────────────────────────────────
print("\n[4] (F-1670) a plural name takes a bare apostrophe: trace_line and track_line")
POSS = [("the gannets", "the gannets'"), ("the gulls", "the gulls'"), ("the swallows", "the swallows'"), ("the crabs", "the crabs'"),
        ("the ants", "the ants'"), ("the cicadas", "the cicadas'"), ("the slugs", "the slugs'"), ("the worms", "the worms'"), ("the aphids", "the aphids'"),
        ("the hedgehog", "the hedgehog's"), ("the mice", "the mice's"), ("the tūī", "the tūī's"), ("the wētā", "the wētā's"), ("the karoro", "the karoro's"),
        ("the borer beetle", "the borer beetle's"), ("the moss", "the moss's")]
for nm, want in POSS:
    check(LT._possessive(nm) == want, f"_possessive({nm!r}) == {want!r}")
NAMED_S = {k: r["name"] for k, r in ROWS.items() if not r.get("external") and r.get("traces") and (r.get("name") or "").endswith("s") and not (r.get("name") or "").endswith("ss")}
print("    trace-carrying rows whose grandfathered name ends in s:", NAMED_S)
check(set(NAMED_S) == {"welcome_swallows", "gulls", "gannet", "crabs", "ants", "cicada", "slugs", "earthworms"}, "exactly the eight rows F-1670 counted")
# every name a trace line can carry that ends in s is a genuine plural (hand-checked list; a singular that merely ends in s would fail the
# second check below and force a decision) -- 'the mice' is a plural that does NOT end in s and correctly stays "the mice's"
PLURAL_NAMES = {"the gannets", "the gulls", "the swallows", "the crabs", "the ants", "the cicadas", "the slugs", "the worms", "the aphids"}
bad4: list = []
n_tl = n_named_lines = 0
for k, r in sorted(ROWS.items()):
    if r.get("external") or not r.get("traces"):
        continue
    variants = [False]
    if r.get("hidden") and not r.get("name") and not r.get("audition"):
        variants.append(True)               # the earned 'the <species>' once he has the name (an audition row's name lives in the sound ledger: not exercised)
    for learned in variants:
        base = snap()
        if learned:
            seed_learned(k)
        nm = life.name_for(r)
        if nm and nm.endswith("s") and not nm.endswith("ss"):
            quiet(nm in PLURAL_NAMES, f"[{k}] name {nm!r} ends in s but is not in the hand-checked plural list", bad4)
        whose = ("something's" if not nm else nm + "'" if nm in PLURAL_NAMES else nm + "'s")
        for phrase in r["traces"]:
            for clarity, age in ((0.8, "fresh"), (0.4, "not fresh, softening already")):
                t = {"type": f"{k}_trace", "creature": k, "detail": phrase, "clarity": clarity}
                got = LT.trace_line(t)
                n_tl += 1
                quiet(got == f"here, {phrase} — {whose}, {age}", f"[{k}/{'learned' if learned else 'unlearned'}] {got!r}", bad4)
                if nm in PLURAL_NAMES:
                    n_named_lines += 1
                    quiet(f"{nm}'s" not in got, f"[{k}] still 's after an s: {got!r}", bad4)
        if nm:
            tk = LT.track_line({f"{k}_trace"})
            quiet(f"— {whose} —" in tk and (f"{nm}'s" not in tk if nm in PLURAL_NAMES else True), f"[{k}] track_line {tk[:80]!r}", bad4)
        restore(base)
for m_ in bad4[:10]:
    print("    !!", m_)
check(not bad4 and n_tl > 60 and n_named_lines >= 9 * 2, f"trace_line over every trace phrase of every trace-carrying row, learned and not, fresh and fading ({n_tl} lines, {n_named_lines} of them on a plural name, {len(bad4)} failures)")
_ex = {"type": "gannet_trace", "creature": "gannet", "detail": ROWS["gannet"]["traces"][0], "clarity": 0.8}
print("      before:", f"here, {_ex['detail']} — the gannets's, fresh")
print("      after :", LT.trace_line(_ex))
for k in sorted(NAMED_S):
    t = {"type": f"{k}_trace", "creature": k, "detail": ROWS[k]["traces"][0], "clarity": 0.8}
    print(f"      {k:17s} {LT.trace_line(t)}")
tk = LT.track_line({"gannet_trace"})
print("      track_line(gannet):", tk[:78])
check("— the gannets' —" in tk and "gannets's" not in tk, "track_line carries the same fix (its own copy of the defect)")
check(all("s's" not in LT.trace_line({"type": f"{k}_trace", "creature": k, "detail": ROWS[k]["traces"][0], "clarity": 0.8}) for k in NAMED_S),
      "no trace line of the eight rows contains \"s's\"")
# carcass_look's possessive is built on the singular _species_name and is unchanged
life._load()["carcasses"] = []
c = LT.add_carcass("gannet", "shore", "tideline", "storm", NOW["day"])
bones = LT.carcass_look("the bones", "shore", NOW["day"] + 20 * 86400)
check("a gannet's, picked clean" in bones, f"carcass_look (singular by construction) is unchanged: ...{bones[:60]!r}")
life._load()["carcasses"] = []


# J-1165's channel: a look at the trace object repeats trace_line byte for byte, so it carries the fix too
def reset_traces() -> None:
    WT._traces_cache = {}
    WT._last_load = 0.0
    WT._TRACES_F.write_text("{}", encoding="utf-8")


def mint(key: str, place: str, detail: str, clarity: float = 0.8) -> dict:
    spots = (ROWS[key].get("places") or {}).get(place, [])
    tid = f"{key}_{place}_{int(time.time())}_j1166"
    WT.create_trace(tid, f"{key}_trace", place, LT._pos(place, spots), clarity=clarity, cause=key)
    tr = WT._load_traces()[tid]
    tr["detail"], tr["creature"] = detail, key
    WT._save_traces()
    return tr


reset_traces()
tr = mint("gannet", "shore", ROWS["gannet"]["traces"][0])
res = look("the gannet feather", "shore", NOW["day"])
check(res["line"] == LT.trace_line(tr) and res["line"].endswith("— the gannets', fresh") and res["events"][0]["outcome"] == "trace_object",
      f"J-1165's trace-object look: {res['line']!r}")
S.state["location"] = "shore"
check(S.look("the gannet feather") == LT.trace_line(tr), "... and through sensorium.look()")
reset_traces()

# ── [5] REAL rows, read-only ────────────────────────────────────────────────────────────────────────────────────
print("\n[5] real rows, read-only: data/life_events.jsonl and data/wandering_log.jsonl")
CUTOFF = time.mktime((2026, 9, 21, 18, 30, 0, 0, 0, -1))          # the files are append-only and Du is online; freeze what this test was written against
ans = [e for e in _live_rows if e.get("kind") == "answer" and e.get("outcome") == "sighting" and e.get("key") in ROWS and float(e.get("ts", 0)) <= CUTOFF]
if len(ans) < 80:
    print(f"    (only {len(ans)} rendered sighting rows readable -- data/life_events.jsonl is missing or rotated; real-row replay skipped, NOT a pass)")
else:
    _is_learned, _sk_is_learned = life.is_learned, SK.is_learned
    same = empty = skipped = fixed = 0
    pre_j0887: list = []
    bad5: list = []
    per_key = collections.Counter()
    # J-1216 (D-0254/F-1706): these two logged rows are KNOWN, INTENDED to replay differently now -- the whole
    # point of the per-place feature/miss fix is that they used to misrender. kingfisher/shore ts=1789150549.1
    # is the founder's own D-0249 example ("the post"/"the wire" -> "the cliff edge"/"the water"); morepork/
    # garden ts=1789628298.3 is D-0254's phase-uncertainty resolved real (life_events.jsonl's own "phase":
    # "dusk" and logged line confirm the fire was the borderline dusk/"canopy" line, not a guess). Carved out
    # here exactly as [1a] above carves out the gulls/dusk incident: asserted against the NEW correct line
    # (not the old logged one), not counted in `same` (which stays a true "unrelated to this fix" byte count).
    J1216_FIXED = {("kingfisher", "shore", 1789150549.1): "a stocky bird sits sentry on the cliff edge, blue-green back flaring when it turns, and drops away toward the water",
                   ("morepork", "garden", 1789628298.3): "a silent shape crosses the garden at head height and is gone into the tree"}
    for e in ans:
        key, place = e["key"], e["place"]
        r = ROWS[key]
        m = life._match(e["target"], place)
        if any(w in e["target"].lower() for w in LT._CARCASS_WORDS):
            pre_j0887.append(e)                     # answered by the LIVING row before J-0887 diverted dead-thing looks to the carcass block: not replayable through today's routing
            continue
        if m is None or m["key"] != key or life._phase(e["ts"]) != e["phase"]:
            skipped += 1
            continue
        h = r.get("hidden") or {}
        eyes = bool(h.get("eyeshine")) and e["line"] == h.get("eyeshine")
        life.is_learned = lambda k, _v=bool(e.get("learned")): _v
        SK.is_learned = lambda k, _v=bool(e.get("learned")): _v
        try:
            res = look(e["target"], place, e["ts"], act=e["activity"], vis=e["visibility"], roll=0.0, eyes=eyes)
        finally:
            life.is_learned, SK.is_learned = _is_learned, _sk_is_learned
        per_key[key] += 1
        j1216_key = (key, place, float(e["ts"]))
        if j1216_key in J1216_FIXED:
            fixed += 1
            quiet(res["line"][:160] == J1216_FIXED[j1216_key] and res["line"] != e["line"] and res["events"] and res["events"][0]["outcome"] == "sighting"
                  and len(res["ledger"]) == 1 and res["ledger"][0]["kind"] == "sighting",
                  f"[{key} {e['ts']}] J-1216: now the fixed per-place line, not the logged mis-rendered one: {res['line'][:60]!r}", bad5)
        elif e["line"]:
            same += 1
            quiet(res["line"][:160] == e["line"] and res["events"] and res["events"][0]["outcome"] == "sighting" and len(res["ledger"]) == 1
                  and res["ledger"][0]["kind"] == "sighting", f"[{key} {e['ts']}] {res['line'][:60]!r} != logged {e['line'][:60]!r}", bad5)
        else:
            empty += 1
            quiet(res["line"] == "" and res["ledger"] == [] and res["learn"] == 0 and res["note"] == 0 and res["events"][0]["outcome"] == "no_line",
                  f"[{key} {e['ts']}] the logged EMPTY sighting credited something: {res['events']} {res['ledger']}", bad5)
    print(f"    {len(ans)} rendered sighting rows in life_events.jsonl up to the freeze: {same} with a line replayed byte-identical (same line, one ledger "
          f"sighting), {fixed} intentionally changed by J-1216 (D-0254/F-1706's per-place fix, now the correct line), {empty} EMPTY replayed as no_line / "
          f"no credit, {len(pre_j0887)} answered by the living row before J-0887 routed dead-thing looks to the carcass block "
          f"{[(e['target'], e['key']) for e in pre_j0887]} (not replayable through today's routing; not touched by this change), "
          f"{skipped} skipped (target no longer resolves to the row, or the phase differs)")
    print("    by row:", dict(per_key))
    for m_ in bad5[:10]:
        print("    !!", m_)
    check(not bad5 and empty == 1 and fixed == 2 and same >= 78,
          f"real rows: every logged line reproduced except J-1216's own 2 known fixes, the one empty row credits nothing ({len(bad5)} failures, {skipped} skipped)")
    check(skipped == 0, "no logged row was skipped (every target still resolves to its row at the same phase)")

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
        check(row_["origin"] == "sense" and cut > 0, f"line {i} is a 'sense' row carrying the glued suffix: {text[:50]!r}...{text[cut - 12:cut + 24]!r}")
        prefix = text[:cut]
        r = ROWS[key]
        cand = [ln for ph, ln in (r["hidden"]["feature"]).items() if ln.startswith(prefix[:60])]
        check(len(cand) == 1, f"line {i} ({key}): the logged fragment is one of the row's own feature lines")
        feat = cand[0]
        before = old_join(feat, SFX_UNNAMED)                                # what the old code returned to Du
        check(before[:len(text)] == text, f"line {i}: the OLD join reproduces the logged text byte for byte (the log truncates at ~160 chars)")
        life._load()["individuals"] = {key: {"place": r["places"] and sorted(r["places"])[0], "since": 0, "name": None, "sightings": 7, "last_seen": 0, "history": []}}
        after = LT.with_individual_suffix(key, feat)
        life._load()["individuals"] = {}
        if LT.group_grain(r):
            # J-1174: the honeybees (a swarm) and the gulls (a flock) no longer carry the recognition line at all -- a stored record is dormant -- so these
            # two rows now read as the plain look line; the oystercatcher (line 148115) keeps its graduation and its punctuated join, asserted below
            check(after == feat and "It is the same one" not in after, f"line {i} ({key}): J-1174 -- a swarm / a flock no longer carries the recognition line: the plain look line")
        else:
            check(after == feat + "." + SFX_UNNAMED and after.startswith(prefix + ". It is the same one"), f"line {i}: the NEW join ends the fragment's sentence")
        print(f"      line {i} ({key}):")
        print(f"        before: {before}")
        print(f"        after : {after}")
else:
    print("    (data/wandering_log.jsonl missing or rotated -- the three-row replay skipped, NOT a pass)")

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
for _p in (ROOT / "core" / "life.py", ROOT / "core" / "life_traces.py", ROOT / "core" / "garden_insects.py", Path(__file__)):
    try:
        py_compile.compile(str(_p), cfile=str(TMP / (_p.name + "c")), doraise=True)
        check(True, f"py_compile {_p.name}")
    except py_compile.PyCompileError as exc:
        check(False, f"py_compile {_p.name}: {exc}")

print(f"\n{'ALL OK' if not FAILS else f'{FAILS} FAILURE(S)'} — {CHECKS} checks — isolated stores in {TMP}")
sys.exit(1 if FAILS else 0)
