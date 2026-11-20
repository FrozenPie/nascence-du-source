"""
Regression + characterisation: SYSTEM-DRIVEN redirects are exempt from D-0224's first-leg gate (J-1185 / D-0246 (b)).

THE RULING. Travis, 2026-09-21 (D-0246, option (b)): a redirect the WORLD itself issues (night.to_bed()'s walk to bed and
the monologue's school reel-back) always fires, as it did before J-1111, while his OWN willed first-leg re-wills stay
protected by D-0224 (ruled 2026-09-18, not re-litigated). F-1657 found the gate was declining both: while an outward
journey was on its FIRST leg, to_bed()'s move('study') was declined, he was marked asleep anyway, and the outward
journey carried on through the night (about 1 sleep entry in 21 by the log model), and the school reel-back was silently
delayed a leg. Built with an EXPLICIT keyword marker, never a heuristic:
    sensorium.move(dest, *, system=False)  ->  locomotion.begin_journey(dest, weather, wind, *, system=False)
The marker skips ONE thing, the D-0224 first-leg decline (`existing["departure"] == place`). The same-destination gate
(J-1040) is kept for system callers too. One INFO line marks an override:
    [locomotion] system redirect overrides first leg: <dest> replaces journey to <existing dest>

  Part A  begin_journey() directly. A0 the marker is keyword-only. A1 a PARITY MATRIX: ten journey situations, each run
          once with system=False (the default) and once with system=True; the two runs must be IDENTICAL in every
          situation except the one D-0246 changes (first leg, cross-destination), where willed is declined ('' and a
          decline line, journey untouched) and system fires (departure narration, journey replaced, one override line).
          A2..A5 the detail of the override: it is the ordinary fresh-journey path from the true place; carried wood is
          never dropped; the fresh journey's own first leg is protected against his willed re-wills in turn.
  Part B  THROUGH sensorium.move(): the shape of both named callers (garden outward journey, move('study', system=True)),
          end to end with real ticks (no teleport, no drag to the old destination), the school-confinement shape, and the
          claim that move()'s own confinement rewrite of a WILLED move is not exempt.
  Part C  night.to_bed() END TO END (study_life.on_sleep stubbed: its stores are not isolated; everything else is real):
          a spy proves to_bed() passes exactly system=True; the `moved` text is the departure narration; he is marked
          asleep with the walk home replacing the outward journey; same-dest, later-leg, no-journey and in-the-study
          variants.
  Part D  STATIC caller inventory (AST over every .py in the tree): every production .move( / begin_journey( call site is
          classified, and system=True appears at EXACTLY the three system-driven sites (night.to_bed, the school
          reel-back, the quit-announce bed walk). This is also how the two callers that cannot be run in isolation (a 2,900
          line async method, a launcher script) are proven wired. A NEW caller fails here until it is classified.
  Part E  CHARACTERISATION, NOT A FIX (reported in J-1185): a first leg whose DEPARTURE is the study. move()'s own
          `target == cur` silence (and to_bed()'s own `location != "study"` guard) answer BEFORE the gate, so a
          system-driven move('study') does nothing, the outward journey keeps running, and he walks out of the study
          during the night. Pre-dates J-1040/J-1111 (both guards are in the pre-git baseline commit 8eef0bb). These
          checks pin today's behaviour on purpose; a future fix should flip exactly them.
  Part F  isolation and module-resolution proof.

ISOLATION. locomotion._POS_F and sensorium._STATE_F are redirected into a temp dir before anything can write (the S-0016
rule; same convention as scripts/_test_journey_decline_through_move.py, whose 91 checks stay byte-unchanged and are the
DEFAULT-behaviour regression). core.study_life.on_sleep is replaced by a recorder (its stores are not part of this
redirect). A Python audit hook records any attempt by THIS process to open-for-write / rename / remove anything under
C:\\Nascence\\data or <root>\\data; with Du ONLINE the live files change by themselves, so the hook, not the md5s, is the
proof. MODULE RESOLUTION (F-1285): the script puts its own root FIRST on sys.path and asserts core.locomotion /
core.sensorium / core.night / core.school / core.study_life were loaded from inside that root; the AST parts read the
same root's files, and the `nodes` package is proven to resolve there without importing the 2,900-line node.

  python scripts/_test_system_redirect_first_leg.py        # exit 0 = ALL OK
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import inspect
import json
import logging
import os
import re
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TMP = Path(tempfile.mkdtemp(prefix="system_redirect_first_leg_"))
print("isolated store dir:", TMP)
# data/ is gitignored and never checked out into a job-run worktree, so "live" is the one real repo, never ROOT-relative.
_LIVE_DATA = Path(r"C:\Nascence") / "data"
_LIVE = [_LIVE_DATA / "room_state.json", _LIVE_DATA / "position.json",
         _LIVE_DATA / "night_log.jsonl", _LIVE_DATA / "recent_dreams.json"]


def _md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest() if p.exists() else ""


_before = {p: _md5(p) for p in _LIVE}

# -- write audit: this process must never attempt a write under a live data dir --------------------------------------
_WATCH = [str(_LIVE_DATA).lower(), str((ROOT / "data")).lower()]
_WRITE_EVENTS = {"os.rename", "os.remove", "os.rmdir", "os.mkdir", "os.truncate", "os.utime", "os.chmod",
                 "shutil.copyfile", "shutil.copymode", "shutil.copystat", "shutil.copytree", "shutil.move",
                 "shutil.rmtree"}
LIVE_WRITE_ATTEMPTS: list = []


def _under_watch(p) -> bool:
    try:
        if isinstance(p, int):
            return False
        s = os.fsdecode(os.fspath(p))
        s = os.path.abspath(s).lower()
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

from core import sensorium as S          # noqa: E402
from core import locomotion as L         # noqa: E402
from core import school as SCH           # noqa: E402
from core import night as N              # noqa: E402
from core import study_life as SL        # noqa: E402
S._STATE_F = TMP / "room_state.json"
L._POS_F = TMP / "position.json"
assert not str(S._STATE_F).lower().startswith(str(_LIVE_DATA).lower()) and not str(L._POS_F).lower().startswith(str(_LIVE_DATA).lower())

# night.to_bed() calls study_life.on_sleep(), whose stores (sensorium.state["study"] bootstrap, provisions, inventory,
# the curriculum) are not covered by the two redirects above -> replaced by a recorder. Nothing else in to_bed() is stubbed.
_ONSLEEP = {"n": 0}


def _fake_on_sleep() -> None:
    _ONSLEEP["n"] += 1


_real_on_sleep = SL.on_sleep
SL.on_sleep = _fake_on_sleep

FAILS = 0
NCHECKS = 0


def check(cond: bool, label: str) -> None:
    global FAILS, NCHECKS
    NCHECKS += 1
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS += 1


# -- module-resolution proof (F-1285) --------------------------------------------------------------------------------
print("\n[0] module resolution: the code under test is THIS root's, not the shared tree's")
print("    sys.path[0] =", sys.path[0])
for _m in (L, S, N, SCH, SL):
    print(f"    {_m.__name__:16s} -> {_m.__file__}")
    check(Path(_m.__file__).resolve().is_relative_to(ROOT), f"{_m.__name__} was loaded from inside {ROOT}")
_nodes_spec = importlib.util.find_spec("nodes")                    # a top-level find_spec does NOT import the package
_nodes_dir = list(_nodes_spec.submodule_search_locations or [])[0] if _nodes_spec else ""
print(f"    nodes (package dir, not imported) -> {_nodes_dir}")
check(bool(_nodes_dir) and Path(_nodes_dir).resolve().is_relative_to(ROOT), "the `nodes` package resolves inside this root (Part D parses these files)")

# -- log capture (level AND message) ----------------------------------------------------------------------------------
_DECLINE = re.compile(r"^\[locomotion\] redirect declined: (study|garden|wood|shore) while journey to "
                      r"(study|garden|wood|shore) \((same-dest|first-leg)\)$")
_OVERRIDE = re.compile(r"^\[locomotion\] system redirect overrides first leg: (study|garden|wood|shore) replaces journey to "
                       r"(study|garden|wood|shore)$")


class _Cap(logging.Handler):
    def __init__(self):
        super().__init__(logging.DEBUG)
        self.recs: list[tuple[int, str]] = []

    def emit(self, record):
        self.recs.append((record.levelno, record.getMessage()))

    def clear(self):
        self.recs.clear()


_cap = _Cap()
_lg = logging.getLogger("nascence.locomotion")
_lg.addHandler(_cap)
_lg.setLevel(logging.INFO)
_lg.propagate = False


def declines() -> list[tuple[str, str, str]]:
    """Parsed decline lines since the last clear (J-1179's format, unchanged); a decline-prefixed line that does not
    parse is a FAIL."""
    out = []
    for _lvl, m in _cap.recs:
        if m.startswith("[locomotion] redirect declined:"):
            g = _DECLINE.match(m)
            if not g:
                check(False, f"decline line does not match the documented format: {m!r}")
                continue
            out.append(g.groups())
    return out


def overrides() -> list[tuple[str, str]]:
    """Parsed system-override lines since the last clear (dest, existing dest); each must be exactly INFO and match the
    documented format, else a FAIL."""
    out = []
    for lvl, m in _cap.recs:
        if m.startswith("[locomotion] system redirect"):
            g = _OVERRIDE.match(m)
            if not g:
                check(False, f"override line does not match the documented format: {m!r}")
                continue
            if lvl != logging.INFO:
                check(False, f"override line is not INFO (levelno {lvl}): {m!r}")
                continue
            out.append(g.groups())
    return out


_saves = {"n": 0}
_real_save_now = S._save_now


def _counting_save_now():
    _saves["n"] += 1
    return _real_save_now()


S._save_now = _counting_save_now


# -- helpers -----------------------------------------------------------------------------------------------------------
def reset(loc: str, *, confined: bool = False, locomotion: bool = True, carried: int = 0) -> None:
    """A fresh in-memory room at `loc`, no journey pending, school not confining (unless asked), not asleep."""
    S.state.clear()
    S.state.update({"weather": "clear", "wind": "breeze", "fire": "out", "fire_fuel": 0.0, "last_event": 0,
                    "location": loc, "garden": S._fresh_garden(), "woodpile": 4})
    L._POS_F.write_text(json.dumps({"place": loc, "standpoint": L._DEFAULT_SP[loc], "journey": None,
                                    "effort": 0.0, "carried_wood": carried}), encoding="utf-8")
    S._STATE_F.write_text(json.dumps(S.state), encoding="utf-8")     # a saved baseline: any later _save_now() is counted
    SCH.confined_to_study = (lambda: True) if confined else (lambda: False)
    L.LOCOMOTION = locomotion
    _cap.clear()
    _saves["n"] = 0
    _ONSLEEP["n"] = 0


def pos() -> dict:
    return json.loads(L._POS_F.read_text(encoding="utf-8"))


def journey():
    return pos().get("journey")


def jsum(j) -> tuple | None:
    """A journey with its clocks removed: what makes two journeys the same journey."""
    return None if not j else (j.get("dest"), tuple(j.get("path") or ()), j.get("from"), j.get("departure"))


def snap() -> tuple:
    return (L._POS_F.read_bytes(), S._STATE_F.read_bytes() if S._STATE_F.exists() else b"",
            json.dumps(S.state, sort_keys=True, default=str), _saves["n"])


def force_due() -> None:
    """Make the pending leg due NOW (the leg clock in position.json), so a REAL locomotion.tick() completes it."""
    d = pos()
    d["journey"]["leg_ends"] = time.time() - 1.0
    L._POS_F.write_text(json.dumps(d), encoding="utf-8")


def age_journey(secs_started_ago: float = 30.0, leg_left: float = 7.0) -> None:
    """Backdate the pending journey's clocks (started N s ago, the leg 90% elapsed) so a REPLACEMENT is visible in them
    even on a coarse clock."""
    d = pos()
    d["journey"]["started"] = time.time() - secs_started_ago
    d["journey"]["leg_ends"] = time.time() + leg_left
    L._POS_F.write_text(json.dumps(d), encoding="utf-8")


def is_departure(text, frm: str, to: str) -> bool:
    """True iff `text` is a journey DEPARTURE narration for that leg (one of _LEG_LINES, weather tags allowed after it)."""
    return isinstance(text, str) and any(text.startswith(c) for c in L._LEG_LINES[(frm, to)])


def noop(label: str, out, before: tuple, want_declines: list, loc: str) -> None:
    """The full 'true no-op' contract for one declined call (J-1179's), plus: no override line."""
    after = snap()
    check(out == "" and out is not None, f"{label}: returns '' (not None, not narration): {out!r}")
    check(S.state.get("location") == loc, f"{label}: state['location'] still {loc!r}: {S.state.get('location')!r}")
    check(after[0] == before[0], f"{label}: position.json (the pending journey) BYTE-IDENTICAL")
    check(after[1] == before[1], f"{label}: room_state.json BYTE-IDENTICAL")
    check(after[2] == before[2], f"{label}: whole in-memory state unchanged")
    check(after[3] == before[3], f"{label}: _save_now() never called (calls {before[3]} -> {after[3]})")
    check(declines() == want_declines, f"{label}: decline log = {want_declines!r}: {declines()!r}")
    check(overrides() == [], f"{label}: no override line: {overrides()!r}")


# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
print("\n══ PART A: begin_journey() directly ══")
assert L.LOCOMOTION is True, "this test only means anything with LOCOMOTION=True"

print("\n[A0] the marker is an EXPLICIT keyword-only parameter, default False, on both functions")
for _fn, _nm in ((L.begin_journey, "locomotion.begin_journey"), (S.move, "sensorium.move")):
    _p = inspect.signature(_fn).parameters.get("system")
    check(_p is not None and _p.kind is inspect.Parameter.KEYWORD_ONLY and _p.default is False,
          f"{_nm} has `system` keyword-only, default False: {_p}")
reset("garden")
try:
    L.begin_journey("study", "", "", True)
    _raised = False
except TypeError:
    _raised = True
check(_raised, "begin_journey('study', '', '', True): `system` cannot be passed positionally (TypeError)")
try:
    S.move("study", True)
    _raised = False
except TypeError:
    _raised = True
check(_raised, "move('study', True): `system` cannot be passed positionally (TypeError)")
check(journey() is None, "neither rejected call started a journey")

print("\n[A1] PARITY MATRIX: every situation run with system=False (default) and system=True; identical except first-leg cross-destination")
_real_pb = L._path_between


def _boom(*a, **k):
    raise ValueError("boom")


def _scn_no_journey():
    reset("garden"); return "study"


def _scn_same_dest():
    reset("garden"); L.begin_journey("shore"); age_journey(); _cap.clear(); return "shore"


def _scn_first_leg_cross():
    reset("garden"); L.begin_journey("shore"); age_journey(); _cap.clear(); return "study"


def _scn_first_leg_cross_from_study():
    reset("study"); L.begin_journey("shore"); age_journey(); _cap.clear(); return "wood"


def _scn_later_leg_cross():
    reset("garden"); L.begin_journey("shore"); force_due(); L.tick(time.time()); _cap.clear(); return "study"


def _scn_later_leg_same_dest():
    reset("garden"); L.begin_journey("shore"); force_due(); L.tick(time.time()); _cap.clear(); return "shore"


def _scn_already_there():
    reset("study"); return "study"


def _scn_loco_off():
    reset("garden", locomotion=False); return "study"


def _scn_failure():
    reset("garden"); L._path_between = _boom; return "study"


def _scn_unknown_dest():
    reset("garden"); return "nowhere"


_SCENARIOS = [
    ("no journey in progress", _scn_no_journey),
    ("same destination (J-1040)", _scn_same_dest),
    ("FIRST leg, cross-destination (D-0224)  <- the ONE cell D-0246 changes", _scn_first_leg_cross),
    ("FIRST leg out of the STUDY, cross-destination, third place", _scn_first_leg_cross_from_study),
    ("later leg, cross-destination", _scn_later_leg_cross),
    ("later leg, same destination", _scn_later_leg_same_dest),
    ("already there (empty path)", _scn_already_there),
    ("LOCOMOTION off", _scn_loco_off),
    ("internal failure inside begin_journey", _scn_failure),
    ("unknown destination (empty path)", _scn_unknown_dest),
]
_CHANGED = {_scn_first_leg_cross, _scn_first_leg_cross_from_study}


def _run(scn, system: bool):
    dest = scn()
    before = (L._POS_F.read_bytes() if L._POS_F.exists() else b"")
    try:
        out = L.begin_journey(dest, system=system)
    finally:
        L._path_between = _real_pb
        L.LOCOMOTION = True
    kind = "None" if out is None else ("''" if out == "" else "narration")
    after = (L._POS_F.read_bytes() if L._POS_F.exists() else b"")
    return {"kind": kind, "out": out, "journey": jsum(journey()), "declines": declines(), "overrides": overrides(),
            "file_changed": before != after}


for _label, _scn in _SCENARIOS:
    _w, _s = _run(_scn, False), _run(_scn, True)
    if _scn in _CHANGED:
        print(f"  ..   {_label}: willed={_w['kind']} declines={_w['declines']} | system={_s['kind']} overrides={_s['overrides']}")
        _dest = "study" if _scn is _scn_first_leg_cross else "wood"
        _old = "shore"
        check(_w["kind"] == "''" and not _w["file_changed"] and _w["journey"] is not None and _w["journey"][0] == _old
              and _w["declines"] == [(_dest, _old, "first-leg")] and _w["overrides"] == [],
              f"  willed (system=False): declined '' , journey to {_old} untouched, one first-leg decline line, no override line")
        _from = "garden" if _scn is _scn_first_leg_cross else "study"
        check(_s["kind"] == "narration" and _s["file_changed"] and _s["journey"] is not None and _s["journey"][0] == _dest
              and _s["journey"][2] == _from and _s["journey"][3] == _from
              and _s["declines"] == [] and _s["overrides"] == [(_dest, _old)],
              f"  system=True: fires (narration), journey REPLACED (dest {_dest}, from/departure {_from}), zero decline lines, one override line ({_dest} replaces {_old})")
        check(is_departure(_s["out"], _from, L._path_between(_from, _dest)[0]),
              f"  system=True narration is the {_from}->{L._path_between(_from, _dest)[0]} DEPARTURE line: {_s['out'][:60]!r}")
    else:
        same = ({k: v for k, v in _w.items() if k != "out"} == {k: v for k, v in _s.items() if k != "out"})
        both_narr = (_w["kind"] == "narration") == (_s["kind"] == "narration")
        check(same and both_narr, f"{_label}: identical with system=False and system=True ({_w['kind']}, journey {_w['journey']}, "
                                  f"declines {_w['declines']}, overrides {_w['overrides']})")
        check(_w["overrides"] == [] and _s["overrides"] == [], f"{_label}: no override line either way")

print("\n[A2] the override is the ORDINARY fresh-journey path from the true place (garden, outward first leg to shore)")
reset("garden")
L.begin_journey("shore"); age_journey()
j0 = journey(); old_started = j0["started"]
check(j0["dest"] == "shore" and j0["departure"] == "garden" and j0["path"] == ["wood", "shore"], f"outward journey in place: {jsum(j0)}")
_cap.clear()
t_before = time.time()
out = L.begin_journey("study", system=True)
j1 = journey(); p1 = pos()
check(is_departure(out, "garden", "study"), f"returns the garden->study departure narration: {out!r}")
check(jsum(j1) == ("study", ("study",), "garden", "garden"), f"journey replaced: dest study, path [study], from garden, departure garden: {jsum(j1)}")
check(j1["started"] >= t_before > old_started, "the fresh journey has a NEW start clock (the aged one is gone)")
check(15 <= j1["leg_ends"] - time.time() <= 35, f"the leg clock restarted for a 20 s garden->study leg: {j1['leg_ends'] - time.time():.1f} s left")
check(p1["place"] == "garden" and p1["standpoint"] == "at_the_door", f"standpoint set to the leg's exit (at_the_door): {p1['place']!r}/{p1['standpoint']!r}")
check(overrides() == [("study", "shore")] and declines() == [], f"exactly one override line, no decline line: {overrides()!r} / {declines()!r}")
check(len([1 for lvl, m in _cap.recs if m.startswith("[locomotion]")]) == 1, "and it is the ONLY locomotion line written by that call")

print("\n[A3] the same-destination gate (J-1040) is KEPT for system callers")
reset("garden")
L.begin_journey("study"); age_journey()
b = L._POS_F.read_bytes(); jb = journey(); _cap.clear()
out = L.begin_journey("study", system=True)
check(out == "" and out is not None, f"system redirect to the place he is ALREADY walking to: '' (not None, not narration): {out!r}")
check(L._POS_F.read_bytes() == b and journey() == jb, "position.json BYTE-IDENTICAL, journey unchanged")
check(declines() == [("study", "study", "same-dest")] and overrides() == [], f"one same-dest decline line, no override: {declines()!r} / {overrides()!r}")
reset("garden")
L.begin_journey("shore"); age_journey(); b = L._POS_F.read_bytes(); _cap.clear()
out = L.begin_journey("shore", system=True)
check(out == "" and L._POS_F.read_bytes() == b and declines() == [("shore", "shore", "same-dest")] and overrides() == [],
      "system redirect to the (non-study) destination already being walked to: still the same-dest no-op")

print("\n[A4] a system redirect on a LATER leg is not an override: it fires exactly as before, from the true place")
reset("garden")
L.begin_journey("shore"); force_due(); L.tick(time.time()); _cap.clear()
check(S.state["location"] == "wood" and journey()["departure"] == "garden", "leg 1 done: genuinely in the wood, journey still to the shore")
out = L.begin_journey("study", system=True)
check(is_departure(out, "wood", "garden") and jsum(journey()) == ("study", ("garden", "study"), "wood", "wood"),
      f"fires: fresh journey wood->garden->study, departure 'wood': {jsum(journey())}")
check(overrides() == [] and declines() == [], "no override line and no decline line (nothing was overridden)")

print("\n[A5] carried wood survives an override and lands on arrival (D-0246's defeater names 'a lost carried-wood load')")
reset("wood", carried=2)
L.begin_journey("garden"); age_journey()                                   # wood -> garden, first leg, carrying two loads
check(journey()["dest"] == "garden" and pos()["carried_wood"] == 2 and S.state["woodpile"] == 4, "carrying 2 loads on a first-leg walk home; woodpile 4")
_cap.clear()
out = L.begin_journey("study", system=True)
check(is_departure(out, "wood", "garden") and jsum(journey()) == ("study", ("garden", "study"), "wood", "wood") and overrides() == [("study", "garden")],
      f"override: fresh journey wood->garden->study: {jsum(journey())}")
check(pos()["carried_wood"] == 2, f"carried_wood untouched by the override: {pos()['carried_wood']}")
force_due(); L.tick(time.time())
check(S.state["location"] == "garden" and pos()["carried_wood"] == 2 and S.state["woodpile"] == 4, "leg 1 complete (garden): the load is still being carried, nothing landed early")
force_due(); L.tick(time.time())
check(S.state["location"] == "study" and journey() is None and pos()["carried_wood"] == 0 and S.state["woodpile"] == 6,
      f"arrived at the study: both loads landed on the pile (4 -> {S.state['woodpile']}), carried_wood 0, journey cleared")

print("\n[A6] the fresh journey's OWN first leg is protected against his willed re-wills (D-0224 intact, willed side)")
reset("garden")
L.begin_journey("shore"); age_journey()
L.begin_journey("study", system=True); age_journey()
b = L._POS_F.read_bytes(); jb = journey(); _cap.clear()
out = L.begin_journey("wood")
check(out == "" and out is not None and L._POS_F.read_bytes() == b and journey() == jb, "willed move('wood') right after the override: declined '', journey byte-identical")
check(declines() == [("wood", "study", "first-leg")] and overrides() == [], f"a first-leg decline line, no override line: {declines()!r} / {overrides()!r}")

# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
print("\n══ PART B: THROUGH sensorium.move() ══")

print("\n[B1] the shape of BOTH named callers: an outward first leg from the garden, then move('study', system=True)")
reset("garden"); S.move("shore"); _cap.clear(); _saves["n"] = 0
check(journey()["dest"] == "shore" and S.state["location"] == "garden", "outward journey garden->shore on its FIRST leg (location still the departure)")
out = S.move("study", system=True)
check(is_departure(out, "garden", "study"), f"returns the departure narration of the fresh journey: {out[:70]!r}")
check(not out.startswith("You come in from outside"), "NOT the instant-move text (no teleport: the F-1653 signature is absent)")
check(S.state["location"] == "garden" and _saves["n"] == 0, f"he has NOT been moved yet and the instant path never ran (location {S.state['location']!r}, _save_now calls {_saves['n']})")
check(jsum(journey()) == ("study", ("study",), "garden", "garden"), f"the outward journey is REPLACED by garden->study: {jsum(journey())}")
check(overrides() == [("study", "shore")] and declines() == [], f"one override line, no decline line: {overrides()!r} / {declines()!r}")

print("\n[B2] end to end with REAL ticks: he walks home, and is never dragged out along the old path")
force_due(); L.tick(time.time())
check(S.state["location"] == "study" and journey() is None, f"one tick completes the 20 s leg: at the study, journey cleared: {S.state['location']!r}")
trail = [S.state["location"]]
for _ in range(3):
    time.sleep(0.01); L.tick(time.time() + 5000)                     # even a very late tick has nothing left to walk
    trail.append(S.state["location"])
check(trail == ["study"] * 4 and journey() is None, f"later ticks never move him again (no drag-back to wood/shore): {trail}")
check("study takes you back in" in (L.pending_line() or "").lower(), "the arrival narration is the study's")

print("\n[B3] his own WILLED moves during the first leg are STILL declined exactly as before (default and explicit False)")
reset("garden"); S.move("shore"); _cap.clear(); _saves["n"] = 0
b = snap()
noop("B3 willed move('study') (default)", S.move("study"), b, [("study", "shore", "first-leg")], "garden")
_cap.clear(); b = snap()
noop("B3 willed move('study', system=False)", S.move("study", system=False), b, [("study", "shore", "first-leg")], "garden")
_cap.clear(); b = snap()
noop("B3 willed move('wood')", S.move("wood"), b, [("wood", "shore", "first-leg")], "garden")
_cap.clear(); b = snap()
noop("B3 system move('shore') to the destination already being walked to (same-dest kept)", S.move("shore", system=True), b, [("shore", "shore", "same-dest")], "garden")

print("\n[B4] the school shape: school starts while an outward first leg is running")
reset("garden"); S.move("shore")                                      # unconfined: the outward journey is legitimate
SCH.confined_to_study = lambda: True                                  # the desk period begins
_cap.clear(); b = snap()
noop("B4 confined WILLED move('wood') (move()'s own rewrite makes its target 'study'; the trigger is HIS act, so NOT exempt)",
     S.move("wood"), b, [("study", "shore", "first-leg")], "garden")
_cap.clear(); _saves["n"] = 0
out = S.move("study", system=True)                                    # the monologue's reel-back call
check(is_departure(out, "garden", "study") and jsum(journey()) == ("study", ("study",), "garden", "garden"),
      f"the reel-back (system=True) fires: fresh journey garden->study, the outward one replaced: {jsum(journey())}")
check(overrides() == [("study", "shore")] and declines() == [] and _saves["n"] == 0 and S.state["location"] == "garden",
      "one override line, no decline, no instant move")
_cap.clear(); b = snap()
noop("B4 the reel-back repeated (same-dest kept)", S.move("study", system=True), b, [("study", "study", "same-dest")], "garden")
_cap.clear(); b = snap()
noop("B4 confined WILLED move('shore') while being reeled in (rewritten to 'study': same-dest)", S.move("shore"), b, [("study", "study", "same-dest")], "garden")
SCH.confined_to_study = lambda: False

print("\n[B5] paths that never reach the gate are unchanged by the marker")
reset("garden", locomotion=False)
out = S.move("study", system=True)
check(bool(out) and out.startswith("You come in from outside") and S.state["location"] == "study" and journey() is None and _saves["n"] == 1 and declines() == [] and overrides() == [],
      f"LOCOMOTION=False + system=True: the instant path exactly as before (one _save_now): {S.state['location']!r}, saves {_saves['n']}")
reset("study")
check(S.move("study", system=True) == "" and journey() is None and _saves["n"] == 0 and declines() == [] and overrides() == [],
      "already there + system=True: '' silence, no journey, no save")
reset("garden")
check(S.move("nowhere at all", system=True) == "" and S.move("", system=True) == "" and journey() is None, "unknown / empty text + system=True: ''")

# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
print("\n══ PART C: night.to_bed() END TO END (study_life.on_sleep stubbed) ══")
_BED = "You lie down on the bed; the blanket is rough and the room ticks and settles around you."
_real_move = S.move
_move_calls: list = []


def _spy_move(*a, **k):
    _move_calls.append((a, dict(k)))
    return _real_move(*a, **k)


S.move = _spy_move
try:
    print("\n[C1] garden, outward journey on its FIRST leg (the F-1657 case): the walk home REPLACES it")
    reset("garden"); S.move("shore"); _cap.clear(); _saves["n"] = 0; _move_calls.clear(); _ONSLEEP["n"] = 0
    text = N.to_bed()
    check(_move_calls == [(("study",), {"system": True})], f"to_bed() called move exactly once, exactly as move('study', system=True): {_move_calls}")
    check(isinstance(text, str) and text.endswith(_BED) and is_departure(text, "garden", "study"),
          f"`moved` text is the garden->study DEPARTURE narration, then the bed line: {text[:60]!r} ... {text[-30:]!r}")
    check(S.state.get("asleep") is True and bool(S.state.get("asleep_since")) and _ONSLEEP["n"] == 1, "he is marked asleep (and study_life.on_sleep ran once)")
    check(jsum(journey()) == ("study", ("study",), "garden", "garden"), f"the outward journey to the shore is REPLACED by the walk home: {jsum(journey())}")
    check(overrides() == [("study", "shore")] and declines() == [], f"one override line, no decline line: {overrides()!r} / {declines()!r}")
    check(S.state["location"] == "garden" and _saves["n"] == 0, "no teleport: he is still walking (the night's stage ticks complete the leg)")
    force_due(); L.tick(time.time())                                    # what night.stage() -> sensorium.tick() does between stages
    check(S.state["location"] == "study" and journey() is None and S.state.get("asleep") is True,
          f"the night's tick lands him in the STUDY, asleep (before D-0246 he slept at the shore): {S.state['location']!r}")

    print("\n[C2] a journey ALREADY walking home: same-destination gate kept, to_bed() adds nothing")
    reset("garden"); L.begin_journey("study"); age_journey(); b = L._POS_F.read_bytes(); jb = journey(); _cap.clear(); _move_calls.clear()
    text = N.to_bed()
    check(text == _BED, f"`moved` is '' (the decline) so the text is just the bed line: {text!r}")
    check(S.state.get("asleep") is True and L._POS_F.read_bytes() == b and journey() == jb, "asleep; the homeward journey is BYTE-IDENTICAL (clock not restarted)")
    check(declines() == [("study", "study", "same-dest")] and overrides() == [], f"one same-dest decline, no override: {declines()!r} / {overrides()!r}")

    print("\n[C3] a LATER leg (in the wood): fires as before, no override line")
    reset("garden"); S.move("shore"); force_due(); L.tick(time.time()); _cap.clear(); _move_calls.clear()
    text = N.to_bed()
    check(S.state["location"] == "wood" and is_departure(text, "wood", "garden") and text.endswith(_BED), f"departure narration wood->garden then the bed line: {text[:60]!r}")
    check(jsum(journey()) == ("study", ("garden", "study"), "wood", "wood") and overrides() == [] and declines() == [], "fresh journey from the wood; nothing overridden, nothing declined")

    print("\n[C4] no journey in progress: the ordinary walk to bed")
    reset("garden"); _cap.clear(); _move_calls.clear()
    text = N.to_bed()
    check(is_departure(text, "garden", "study") and text.endswith(_BED) and S.state.get("asleep") is True, "departure narration then the bed line; asleep")
    check(_move_calls == [(("study",), {"system": True})] and overrides() == [] and declines() == [], "marker passed, but nothing to override: no line of either class")

    print("\n[C5] already in the study, no journey: to_bed() does not even call move()")
    reset("study"); _cap.clear(); _move_calls.clear()
    text = N.to_bed()
    check(text == _BED and S.state.get("asleep") is True and _move_calls == [], f"just the bed line, move() never called: {text!r} / {_move_calls}")
finally:
    S.move = _real_move

# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
print("\n══ PART D: STATIC caller inventory (every production .move( / begin_journey( site, by AST) ══")
_SKIP_DIRS = {".git", "data", "scratch", "_lab", "backups", "graphify-out", "__pycache__", "node_modules", "models", "engine",
              "public_repo", "docs_site", ".claude"}


class _Sites(ast.NodeVisitor):
    def __init__(self, rel: str):
        self.rel, self.stack, self.sites = rel, [], []

    def visit_FunctionDef(self, n):
        self.stack.append(n.name); self.generic_visit(n); self.stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Call(self, n):
        f = n.func
        recv = name = None
        if isinstance(f, ast.Attribute) and f.attr in ("move", "begin_journey"):
            recv, name = (f.value.id if isinstance(f.value, ast.Name) else ast.unparse(f.value)), f.attr
        elif isinstance(f, ast.Name) and f.id == "begin_journey":
            recv, name = "<bare>", f.id
        if name and recv != "shutil":                                   # shutil.move is a file operation
            a0 = n.args[0] if n.args else None
            dest = a0.value if isinstance(a0, ast.Constant) else ("<expr>" if a0 is not None else "<none>")
            kw = next((k for k in n.keywords if k.arg == "system"), None)
            sysv = None if kw is None else (kw.value.value if isinstance(kw.value, ast.Constant) else "<expr>")
            self.sites.append({"file": self.rel, "line": n.lineno, "func": self.stack[-1] if self.stack else "<module>",
                               "recv": recv, "name": name, "dest": dest, "system": sysv})
        self.generic_visit(n)


_sites: list[dict] = []
_skipped_tests = 0
_unparseable: list[str] = []
_CALLER_TEXT = re.compile(r"(?<!shutil)\.move\(|begin_journey\(")           # the textual fallback for a file the AST cannot read
_hidden: list[str] = []
import warnings                                                              # noqa: E402  (a scanned file's own bad escape must not be noise here)
for _dp, _dns, _fns in os.walk(ROOT):
    _dns[:] = [d for d in _dns if d not in _SKIP_DIRS]
    for _fn in _fns:
        if not _fn.endswith(".py"):
            continue
        _p = Path(_dp) / _fn
        if _fn.startswith("_test_") or _fn == "life_smoke.py":
            _skipped_tests += 1
            continue
        _rel = _p.relative_to(ROOT).as_posix()
        _src = _p.read_text(encoding="utf-8", errors="replace")
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                _tree = ast.parse(_src, filename=_rel)
        except Exception:
            _unparseable.append(_rel)
            if _CALLER_TEXT.search(_src):
                _hidden.append(_rel)
            continue
        _v = _Sites(_rel)
        _v.visit(_tree)
        _sites.extend(_v.sites)
print(f"  scanned {ROOT} ({_skipped_tests} test scripts skipped, {len(_unparseable)} unparseable {_unparseable}): {len(_sites)} production call sites")
check(not _hidden, f"no unparseable file textually contains a .move( / begin_journey( call (the AST cannot see into it): {_hidden}")

# (file, enclosing function, receiver, first-arg) -> (system value, classification + the evidence for it)
_NAV = "nodes/inner_monologue_node.py"
_EXPECT = {
    ("core/dispatch.py", "_move", "s", "<expr>"): (None, "WILLED: the move hand; dest from his own thought/intention text, gated by hands.wants() move verbs"),
    ("core/night.py", "to_bed", "_s", "study"): (True, "SYSTEM: the night's walk to bed (sleep pipeline stage 1, called from _enter_sleep; no thought of his triggers it)"),
    (_NAV, "_think", "_sens_sch", "study"): (True, "SYSTEM: the school reel-back (school.is_school_time() and confined_to_study() and where() != 'study': the world's timetable)"),
    (_NAV, "_think", "_room", "wood"): (None, "WILLED: legacy phrase-latch, hands.wants() on his own thought text"),
    (_NAV, "_think", "_room", "shore"): (None, "WILLED: legacy phrase-latch, hands.wants() on his own thought text"),
    (_NAV, "_think", "_room", "garden"): (None, "WILLED: legacy phrase-latch, hands.wants() on his own thought text"),
    (_NAV, "_think", "_room", "study"): (None, "WILLED: legacy phrase-latch ('come inside' etc.), hands.wants() on his own thought text"),
    (_NAV, "_route_act", "_room", "<expr>"): (None, "WILLED: route_act kind == 'move', his own declared ACT"),
    ("core/sensorium.py", "move", "_loco", "<expr>"): ("<expr>", "PIPE: forwards move()'s own `system` to begin_journey(); the school-confinement rewrite inside move() is a WILLED-move rewrite"),
    ("scripts/run_nascence.py", "_announce_shutdown", "_loco", "study"): (True, "SYSTEM: the deliberate-/quit bed walk (only reached from `if _graceful_quit:`, the operator's shutdown ritual)"),
}
_found = {}
for _s_ in _sites:
    _found.setdefault((_s_["file"], _s_["func"], _s_["recv"], _s_["dest"]), []).append(_s_)
for _k, _v_ in sorted(_found.items()):
    _sys = _v_[0]["system"]
    _tag = "SYSTEM" if _sys is True else ("PIPE  " if _sys == "<expr>" else "WILLED")
    print(f"  {_tag} {_v_[0]['file']}:{_v_[0]['line']:<5d} {_k[1]:<20s} {_k[2]}.{_v_[0]['name']}({_k[3]!r}) system={_sys!r}")
_unknown = sorted(set(_found) - set(_EXPECT))
_missing = sorted(set(_EXPECT) - set(_found))
check(not _unknown, "every production caller is classified below (a NEW caller must be classified here: mark system=True ONLY for the world's own summons, "
                    f"never for his willed move) -- unclassified: {_unknown}")
check(not _missing, f"every classified caller still exists at the classified place -- missing: {_missing}")
for _k in sorted(set(_EXPECT) & set(_found)):
    _want, _why = _EXPECT[_k]
    _got = {x["system"] for x in _found[_k]}
    check(_got == {_want} and len(_found[_k]) == 1, f"{_k[0]} {_k[1]} {_k[2]}.<call>({_k[3]!r}): system={_want!r} ({_why})")
_marked = sorted((x["file"], x["func"]) for x in _sites if x["system"] is True)
check(_marked == sorted([("core/night.py", "to_bed"), (_NAV, "_think"), ("scripts/run_nascence.py", "_announce_shutdown")]),
      f"system=True appears at EXACTLY the three system-driven sites: {_marked}")

# the receivers really are the modules the classification assumes (so `_sens_sch.move` IS sensorium.move, `_loco.begin_journey` IS locomotion's)
_BIND = [("core/night.py", "_s", "sensorium"), (_NAV, "_sens_sch", "sensorium"), ("scripts/run_nascence.py", "_loco", "locomotion"),
         ("core/sensorium.py", "_loco", "locomotion")]
for _file, _alias, _mod in _BIND:
    _t = ast.parse((ROOT / _file).read_text(encoding="utf-8"))
    _bound = any(isinstance(n, ast.ImportFrom) and n.module == "core" and any(a.name == _mod and a.asname == _alias for a in n.names) for n in ast.walk(_t))
    check(_bound, f"{_file}: `{_alias}` is bound by `from core import {_mod} as {_alias}`")

# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
print("\n══ PART E: CHARACTERISATION (reported, NOT fixed): a first leg whose DEPARTURE is the study ══")
print("   pre-dates J-1040/J-1111: move()'s `target == cur` and to_bed()'s `location != \"study\"` are both in the pre-git baseline commit 8eef0bb.")
S.move = _spy_move
try:
    print("\n[E1] move('study', system=True) while an outward journey is on its first leg OUT OF the study: move()'s own silence answers first")
    reset("study"); S.move("shore"); _cap.clear(); _saves["n"] = 0; _move_calls.clear()
    check(S.state["location"] == "study" and jsum(journey()) == ("shore", ("garden", "wood", "shore"), "study", "study"),
          f"outward journey study->garden->wood->shore, first leg, location still 'study': {jsum(journey())}")
    b = snap(); _move_calls.clear()
    out = S.move("study", system=True)
    check(out == "" and snap() == b and declines() == [] and overrides() == [],
          "system move('study'): '' by move()'s own `target == cur`; journey, state, saves all untouched; NO decline line and NO override line (never reaches the gate)")
    out = S.move("study")
    check(out == "" and snap() == b and declines() == [] and overrides() == [], "the WILLED move('study') answers the same way: `system` makes no difference on this path")
    check(jsum(journey()) == ("shore", ("garden", "wood", "shore"), "study", "study"), "so the OUTWARD journey is still pending")

    print("\n[E2] night.to_bed() in that state: its own `location != 'study'` guard means move() is never even called")
    _move_calls.clear(); _ONSLEEP["n"] = 0
    b = L._POS_F.read_bytes()
    text = N.to_bed()
    check(text == _BED and S.state.get("asleep") is True and _ONSLEEP["n"] == 1 and _move_calls == [],
          f"just the bed line, asleep, move() NOT called: {_move_calls}")
    check(L._POS_F.read_bytes() == b and journey()["dest"] == "shore", "and the outward journey to the shore is still running, byte-identical")

    print("\n[E3] the consequence, PINNED as today's behaviour (a future fix should flip exactly these): he walks out of the study while asleep")
    trail = [S.state["location"]]
    for _ in range(3):
        force_due(); L.tick(time.time()); trail.append(S.state["location"])
    check(trail == ["study", "garden", "wood", "shore"] and S.state.get("asleep") is True and journey() is None,
          f"KNOWN LIMITATION: location trail while asleep = {trail}: he ends the night at the SHORE (asleep flag still True)")
finally:
    S.move = _real_move
SL.on_sleep = _real_on_sleep

# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
print("\n══ PART F: isolation ══")
print("\n[F] the override line as it will read in data/nascence.log (root format '%(asctime)s [%(name)s] %(message)s'):")
_rec = logging.LogRecord("nascence.locomotion", logging.INFO, __file__, 0,
                         "[locomotion] system redirect overrides first leg: %s replaces journey to %s", ("study", "shore"), None)
print("    " + logging.Formatter("%(asctime)s [%(name)s] %(message)s").format(_rec))

check(not LIVE_WRITE_ATTEMPTS, f"write audit: this process attempted 0 writes under {_LIVE_DATA} or {ROOT / 'data'}"
      + (f" -- ATTEMPTS: {LIVE_WRITE_ATTEMPTS[:3]!r}" if LIVE_WRITE_ATTEMPTS else ""))


def _du_live() -> bool:
    try:
        return time.time() - (_LIVE_DATA / "nascence.log").stat().st_mtime < 180
    except OSError:
        return False


for p in _LIVE:
    after = _md5(p)
    if after == _before[p]:
        check(True, f"{p.name}: md5 unchanged ({after[:8] or 'absent'})")
    elif _du_live() and not LIVE_WRITE_ATTEMPTS:
        check(True, f"{p.name}: md5 {_before[p][:8]} -> {after[:8]}: changed by the LIVE Du process (nascence.log is fresh), "
                    f"not by this one (write audit: 0 attempts)")
    else:
        check(False, f"{p.name}: md5 CHANGED {_before[p][:8]} -> {after[:8]} and Du is not demonstrably live / a write was attempted")

print(f"\n{NCHECKS} checks")
print("FAILS =", FAILS)
print("ALL OK" if FAILS == 0 else f"SOME CHECKS FAILED (isolated store dir kept for inspection: {TMP})")
if FAILS == 0:
    import shutil
    shutil.rmtree(TMP, ignore_errors=True)         # only this run's own mkdtemp dir, and only when everything passed
sys.exit(1 if FAILS else 0)
