"""
Regression: a DECLINED journey redirect is a TRUE NO-OP through sensorium.move() (J-1179 / F-1653).

The bug (live since Du's 2026-09-18 23:14 restart onto J-1040's same-destination gate and J-1111's first-leg
gate): core.locomotion.begin_journey() returned None for its two DECLINE cases, exactly like "LOCOMOTION off",
and sensorium.move() reads every None as "no journey, fall back to the instant move" -- so every declined
redirect became an INSTANT TELEPORT to the requested place while d["journey"] stayed pending, and
locomotion.tick() later dragged him back along the OLD path (F-1653: 27 of 47 'DISPATCH move' narrations since
the restart were instant-move text, 0 of 597 before). J-1040's harness (13/13) and J-1111's (21/21) called
begin_journey() directly, so nothing ever exercised the fallback; both also asserted None, which is the bug.
Their assertions live on here (Part 1), updated to the three-valued contract: narration = journey started,
None = no journey (fall back), '' = redirect DECLINED (do nothing).

  Part 1  begin_journey() called directly (the ported J-1040 / J-1111 harness cases, expectation now '').
  Part 2  THROUGH sensorium.move() -- the coverage that was missing: (a) repeat move to the same destination,
          (b) first-leg cross-destination move, (c) later-leg redirect after a REAL locomotion.tick(),
          (d) LOCOMOTION=False still takes the instant path, (e) the same-cycle duplicate (route_act then
          dispatch then the legacy latch), (f) already-there / empty-path / failure paths unchanged,
          (g) the system-driven callers' shape (night.to_bed / school reel-back call move("study")).
          Every decline must: return '', leave state['location'] and the whole in-memory state unchanged,
          leave position.json (the journey) BYTE-IDENTICAL, never call _save_now(), and log exactly one
          '[locomotion] redirect declined: <dest> while journey to <dest> (same-dest|first-leg)' line.
  Part 3  isolation and module-resolution proof.

ISOLATION. locomotion._POS_F and sensorium._STATE_F are redirected into a temp dir before anything can write
(the S-0016 / test-isolation rule; same convention as scripts/_test_sensorium_move_tokens.py). The live
C:\\Nascence\\data\\position.json and room_state.json are md5-hashed before and after, AND a Python audit hook
records any attempt by THIS process to open-for-write / rename / remove anything under C:\\Nascence\\data or
<root>\\data: with Du ONLINE the live files legitimately change on their own between the two hashes, so the
hash comparison alone cannot prove a negative -- the audit hook does. MODULE RESOLUTION (F-1285): the script
puts its own repo root at the FRONT of sys.path and asserts core.locomotion / core.sensorium were loaded from
inside that root, so a run from a worktree can never silently test the shared tree's copy.

  python scripts/_test_journey_decline_through_move.py        # exit 0 = ALL OK
"""
from __future__ import annotations

import hashlib
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

TMP = Path(tempfile.mkdtemp(prefix="journey_decline_move_"))
print("isolated store dir:", TMP)
# data/ is gitignored and never checked out into a job-run worktree, so "live" is the one real repo, never ROOT-relative.
_LIVE_DATA = Path(r"C:\Nascence") / "data"
_LIVE = [_LIVE_DATA / "room_state.json", _LIVE_DATA / "position.json"]


def _md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest() if p.exists() else ""


_before = {p: _md5(p) for p in _LIVE}

# ── write audit: this process must never attempt a write under a live data dir ─────────────────────────────────
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
S._STATE_F = TMP / "room_state.json"
L._POS_F = TMP / "position.json"
assert not str(S._STATE_F).lower().startswith(str(_LIVE_DATA).lower()) and not str(L._POS_F).lower().startswith(str(_LIVE_DATA).lower())

FAILS = 0


def check(cond: bool, label: str) -> None:
    global FAILS
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS += 1


# ── module-resolution proof (F-1285) ────────────────────────────────────────────────────────────────────────────
print("\n[0] module resolution: the code under test is THIS root's, not the shared tree's")
print("    sys.path[0] =", sys.path[0])
for _m in (L, S):
    print(f"    {_m.__name__:16s} -> {_m.__file__}")
    check(Path(_m.__file__).resolve().is_relative_to(ROOT), f"{_m.__name__} was loaded from inside {ROOT}")

# ── decline-line capture ─────────────────────────────────────────────────────────────────────────────────────────
_DECLINE = re.compile(r"^\[locomotion\] redirect declined: (study|garden|wood|shore) while journey to "
                      r"(study|garden|wood|shore) \((same-dest|first-leg)\)$")


class _Cap(logging.Handler):
    def __init__(self):
        super().__init__(logging.DEBUG)
        self.msgs: list[str] = []

    def emit(self, record):
        self.msgs.append(record.getMessage())


_cap = _Cap()
_lg = logging.getLogger("nascence.locomotion")
_lg.addHandler(_cap)
_lg.setLevel(logging.INFO)
_lg.propagate = False


def declines() -> list[tuple[str, str, str]]:
    """Parsed decline lines since the last clear; a decline-prefixed line that does not parse is a FAIL."""
    out = []
    for m in _cap.msgs:
        if m.startswith("[locomotion] redirect declined:"):
            g = _DECLINE.match(m)
            if not g:
                check(False, f"decline line does not match the documented format: {m!r}")
                continue
            out.append(g.groups())
    return out


_saves = {"n": 0}
_real_save_now = S._save_now


def _counting_save_now():
    _saves["n"] += 1
    return _real_save_now()


S._save_now = _counting_save_now


# ── helpers ──────────────────────────────────────────────────────────────────────────────────────────────────────
def reset(loc: str, *, confined: bool = False, locomotion: bool = True) -> None:
    """A fresh in-memory room at `loc`, no journey pending, school not confining (unless asked)."""
    S.state.clear()
    S.state.update({"weather": "clear", "wind": "breeze", "fire": "out", "fire_fuel": 0.0, "last_event": 0,
                    "location": loc, "garden": S._fresh_garden()})
    L._POS_F.write_text(json.dumps({"place": loc, "standpoint": L._DEFAULT_SP[loc], "journey": None,
                                    "effort": 0.0, "carried_wood": 0}), encoding="utf-8")
    S._STATE_F.write_text(json.dumps(S.state), encoding="utf-8")     # a saved baseline: any later _save_now() is a change of file mtime AND a counted call
    SCH.confined_to_study = (lambda: True) if confined else (lambda: False)
    L.LOCOMOTION = locomotion
    _cap.msgs.clear()
    _saves["n"] = 0


def pos() -> dict:
    return json.loads(L._POS_F.read_text(encoding="utf-8"))


def journey():
    return pos().get("journey")


def snap() -> tuple:
    """Everything a no-op must leave alone: the journey file's raw bytes, the room file's raw bytes, the whole
    in-memory state (location included) and the number of _save_now() calls so far."""
    return (L._POS_F.read_bytes(), S._STATE_F.read_bytes() if S._STATE_F.exists() else b"",
            json.dumps(S.state, sort_keys=True, default=str), _saves["n"])


def force_due() -> None:
    """Make the pending leg due NOW (the leg clock in position.json), so a REAL locomotion.tick() completes it."""
    d = pos()
    d["journey"]["leg_ends"] = time.time() - 1.0
    L._POS_F.write_text(json.dumps(d), encoding="utf-8")


def noop(label: str, out, before: tuple, want_declines: list[tuple[str, str, str]], loc: str) -> None:
    """The full 'true no-op' contract for one declined call."""
    after = snap()
    check(out == "" and out is not None, f"{label}: returns '' (not None, not narration): {out!r}")
    check(S.state.get("location") == loc, f"{label}: state['location'] still {loc!r}: {S.state.get('location')!r}")
    check(after[0] == before[0], f"{label}: position.json (the pending journey) BYTE-IDENTICAL")
    check(after[1] == before[1], f"{label}: room_state.json BYTE-IDENTICAL")
    check(after[2] == before[2], f"{label}: whole in-memory state unchanged")
    check(after[3] == before[3], f"{label}: _save_now() never called (calls {before[3]} -> {after[3]})")
    check(declines() == want_declines, f"{label}: decline log = {want_declines!r}: {declines()!r}")


_STOCK = ["study", "garden", "wood", "shore"]

# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
print("\n══ PART 1: begin_journey() directly (J-1040 / J-1111 harness cases, expectation now '') ══")
assert L.LOCOMOTION is True, "this test only means anything with LOCOMOTION=True"

print("\n[1a] same-destination retrigger mid-journey (J-1040): '' -- and the leg clock is untouched")
reset("garden")
out1 = L.begin_journey("shore")                 # garden -> shore = [wood, shore]; first leg garden->wood, 70 s base
j1 = journey()
check(bool(out1) and j1 is not None and j1.get("dest") == "shore", f"first call departs normally: {out1[:60]!r}")
d = pos(); d["journey"]["leg_ends"] = time.time() + 7.0          # 90% of the 70 s leg elapsed
L._POS_F.write_text(json.dumps(d), encoding="utf-8")
b = L._POS_F.read_bytes(); jb = journey(); _cap.msgs.clear()
out2 = L.begin_journey("shore")
check(out2 == "" and out2 is not None, f"same-dest retrigger returns '' (NOT None): {out2!r}")
check(L._POS_F.read_bytes() == b, "position.json BYTE-IDENTICAL (leg_ends / started / path all untouched)")
check(journey() == jb, "journey dict equal before/after")
check(declines() == [("shore", "shore", "same-dest")], f"one decline line (same-dest): {declines()!r}")

print("\n[1b] FIRST-LEG cross-destination redirect (D-0224/J-1111): '' -- original journey untouched")
reset("study")
out1 = L.begin_journey("shore")                 # study -> shore = [garden, wood, shore]; first leg study->garden
j1 = journey()
check(bool(out1) and j1.get("dest") == "shore" and j1.get("departure") == "study", f"departs toward shore, departure='study': {out1[:50]!r}")
d = pos(); d["journey"]["leg_ends"] = time.time() + 1.0          # nearly done with leg 1 but NOT arrived: tick() never ran
L._POS_F.write_text(json.dumps(d), encoding="utf-8")
b = L._POS_F.read_bytes(); jb = journey(); _cap.msgs.clear()
out2 = L.begin_journey("wood")
check(out2 == "" and out2 is not None, f"first-leg redirect returns '' (NOT None): {out2!r}")
check(L._POS_F.read_bytes() == b, "position.json BYTE-IDENTICAL")
check(journey() == jb and journey().get("dest") == "shore", "ORIGINAL destination 'shore' preserved, path/leg_ends/started untouched")
check(declines() == [("wood", "shore", "first-leg")], f"one decline line (first-leg): {declines()!r}")

print("\n[1c] LATER-LEG cross-destination redirect (>=1 real leg completed): unaffected, still fires from the true place")
reset("study")
L.begin_journey("shore"); force_due(); L.tick(time.time())       # a REAL tick completes leg 1: study -> garden
check(pos().get("place") == "garden" and S.state.get("location") == "garden", f"leg 1 completed, genuinely at 'garden': {S.state.get('location')!r}")
check(journey().get("departure") == "study" and journey().get("from") == "garden", "departure still 'study' (tick never touches it), 'from' advanced to 'garden'")
_cap.msgs.clear()
out2 = L.begin_journey("wood")
j2 = journey()
check(bool(out2), f"later-leg redirect still fires (narration): {out2!r}"[:100])
check(j2.get("dest") == "wood" and j2.get("from") == "garden" and j2.get("path") == ["wood"], f"fresh journey garden->wood: {j2.get('dest')!r} from {j2.get('from')!r} path {j2.get('path')!r}")
check(declines() == [], "no decline line for a redirect that fires")

print("\n[1d] ordinary non-journey case: fires normally")
reset("garden"); out = L.begin_journey("shore")
check(bool(out) and journey().get("dest") == "shore" and declines() == [], f"no prior journey: fires normally, no decline line: {out[:50]!r}")

print("\n[1e] already-arrived (dest == current place): still None (the fallback signal), unchanged")
reset("shore"); out = L.begin_journey("shore")
check(out is None and declines() == [], f"already at shore: begin_journey('shore') is None: {out!r}")

print("\n[1f] LOCOMOTION off: still None (the rollback signal), unchanged")
reset("garden", locomotion=False); out = L.begin_journey("shore")
check(out is None and journey() is None and declines() == [], f"LOCOMOTION=False: None, no journey: {out!r}")
L.LOCOMOTION = True

print("\n[1g] internal failure: still None (fail-open), unchanged")
reset("garden")
_real_pb = L._path_between


def _boom(*a, **k):
    raise ValueError("boom")


L._path_between = _boom
try:
    out = L.begin_journey("shore")
finally:
    L._path_between = _real_pb
check(out is None and declines() == [], f"exception path: None, no decline line: {out!r}")

# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
print("\n══ PART 2: the same cases THROUGH sensorium.move() (the coverage F-1653 found missing) ══")

print("\n[2a] repeat move to the same destination while a journey to it is in progress")
reset("garden")
out1 = S.move("shore")
check(bool(out1) and S.state.get("location") == "garden" and journey().get("dest") == "shore",
      f"first move('shore') starts the journey, location stays 'garden' until a leg completes: {out1[:50]!r}")
_cap.msgs.clear(); _saves["n"] = 0
b = snap()
out2 = S.move("shore")
noop("2a move('shore') again", out2, b, [("shore", "shore", "same-dest")], "garden")

print("\n[2b] FIRST-LEG cross-destination moves (D-0224): declined, then declined AGAIN (the F-1653 second-order effect is gone)")
reset("garden"); S.move("shore"); _cap.msgs.clear(); _saves["n"] = 0
b = snap()
noop("2b move('wood') on leg 1", S.move("wood"), b, [("wood", "shore", "first-leg")], "garden")
_cap.msgs.clear(); b = snap()
noop("2b move('study') on leg 1, right after", S.move("study"), b, [("study", "shore", "first-leg")], "garden")
_cap.msgs.clear(); b = snap()
out = S.move("garden")                            # a reversal to the DEPARTURE place: move()'s own target == cur no-op, never reaches the gate
check(out == "" and snap() == b and declines() == [],
      "2b move('garden') on leg 1 (reversal to the departure): '' by move()'s own target == cur, untouched, NO decline line (it never reaches the gate)")

print("\n[2b'] end to end: after the declines a REAL tick walks the ORIGINAL path -- no teleport, no drag-back")
reset("garden"); S.move("shore"); S.move("wood"); S.move("study")
trail = [S.state["location"]]
force_due(); L.tick(time.time()); trail.append(S.state["location"])
force_due(); L.tick(time.time()); trail.append(S.state["location"])
check(trail == ["garden", "wood", "shore"], f"location trail through two real ticks = garden -> wood -> shore (buggy code: shore/study first): {trail!r}")
check(journey() is None, "journey completed at 'shore' and cleared")

print("\n[2c] LATER-LEG redirect after a real tick: still fires, fresh journey from the TRUE place; its own first leg is protected in turn")
reset("garden"); S.move("shore"); force_due(); L.tick(time.time())
check(S.state["location"] == "wood" and journey().get("departure") == "garden", "leg 1 done: genuinely in the wood, journey still to the shore")
_cap.msgs.clear(); _saves["n"] = 0
out = S.move("garden")
j = journey()
check(bool(out) and j.get("dest") == "garden" and j.get("from") == "wood" and j.get("path") == ["garden"] and j.get("departure") == "wood",
      f"move('garden') from the wood fires: fresh journey wood->garden, departure='wood': {j.get('dest')!r} from {j.get('from')!r}")
check(S.state["location"] == "wood" and declines() == [], "still in the wood until its leg completes; no decline line")
_cap.msgs.clear(); b = snap()
noop("2c move('shore') on the FRESH journey's first leg", S.move("shore"), b, [("shore", "garden", "first-leg")], "wood")
_cap.msgs.clear(); b = snap()
noop("2c move('garden') again (same-dest of the fresh journey)", S.move("garden"), b, [("garden", "garden", "same-dest")], "wood")

print("\n[2d] LOCOMOTION=False still takes the instant path (the rollback flag's meaning is unchanged)")
reset("garden", locomotion=False)
out = S.move("shore")
check(bool(out) and S.state.get("location") == "shore", f"instant move: location -> 'shore': {S.state.get('location')!r} | {out[:50]!r}")
check(journey() is None and declines() == [] and _saves["n"] == 1, f"no journey, no decline line, exactly one _save_now(): saves={_saves['n']}")
L.LOCOMOTION = True

print("\n[2e] the same-cycle duplicate (route_act, then dispatch, then the legacy latch): exactly ONE journey, no location change")
reset("garden")
o1, o2, o3 = S.move("shore"), S.move("shore"), S.move("shore")
j = journey()
check(bool(o1) and o2 == "" and o3 == "", f"first call narrates the departure, the duplicates answer '': {o1[:40]!r} / {o2!r} / {o3!r}")
check(S.state["location"] == "garden" and j.get("dest") == "shore" and j.get("path") == ["wood", "shore"], "location unchanged, one journey garden->shore")
check(declines() == [("shore", "shore", "same-dest")] * 2, f"two decline lines (one per duplicate call): {declines()!r}")
started = j["started"]; leg_ends = j["leg_ends"]
S.move("shore")
check(journey()["started"] == started and journey()["leg_ends"] == leg_ends, "the leg clock was never restarted by the duplicates")

print("\n[2f] already there / unknown / empty path / failure: unchanged")
reset("shore")
check(S.move("shore") == "" and journey() is None and declines() == [] and _saves["n"] == 0, "already there: '' silence, no journey, no save, no decline line")
reset("garden")
check(S.move("nowhere at all") == "" and S.move("") == "" and journey() is None, "unknown / empty text: ''")
reset("garden"); S.state["location"] = "nowhere"                      # a corrupted location: begin_journey's empty-path None
out = S.move("shore")
check(bool(out) and S.state["location"] == "shore" and declines() == [],
      f"empty path (place not on the chain): still falls back to the instant move, repairing the location: {S.state['location']!r}")
reset("garden")
L._path_between = _boom
try:
    out = S.move("shore")
finally:
    L._path_between = _real_pb
check(bool(out) and S.state["location"] == "shore" and declines() == [],
      f"internal failure inside begin_journey: still falls back to the instant move (fail-open, as designed): {S.state['location']!r}")

print("\n[2g] the system-driven callers' shape: night.to_bed() and the school reel-back both call move('study')")
reset("garden"); S.move("shore"); _cap.msgs.clear(); _saves["n"] = 0
b = snap()
# NOTE (F-1653 follow-up): these callers pass through the SAME first-leg gate as his own willed moves; while
# an outward journey is on its FIRST leg a move('study') is declined. That is pinned here as CURRENT behaviour
# (D-0224 protects the first leg; whether system-driven redirects should be exempt is a separate question).
noop("2g move('study') on an outward first leg", S.move("study"), b, [("study", "shore", "first-leg")], "garden")
reset("garden", confined=True); S.move("shore")                          # school-confined: move('shore') is reeled back to the study
check(journey() is not None and journey().get("dest") == "study", "school confinement resolves an outward move to a journey to the study")
_cap.msgs.clear(); b = snap()
noop("2g confined: move('shore') again (target reeled to 'study'; same-dest)", S.move("shore"), b, [("study", "study", "same-dest")], "garden")
SCH.confined_to_study = lambda: False

# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
print("\n══ PART 3: isolation ══")
print("\n[3] the decline line as it will read in data/nascence.log (root format '%(asctime)s [%(name)s] %(message)s'):")
_rec = logging.LogRecord("nascence.locomotion", logging.INFO, __file__, 0,
                         "[locomotion] redirect declined: %s while journey to %s (%s)", ("wood", "shore", "first-leg"), None)
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

print("\nFAILS =", FAILS)
print("ALL OK" if FAILS == 0 else "SOME CHECKS FAILED")
sys.exit(1 if FAILS else 0)
