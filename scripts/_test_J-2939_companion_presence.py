"""
Regression/verification for J-2939 (F-3629, P-0031): the companion presence line is location-blind and presence lives
on two clocks.

What this proves, ISOLATED (no model, no live data written: companion's _DATA/_STATE_F/_LOG_F and sensorium's/
locomotion's state files are temp paths; the live stores are stat-ed and hashed before and after):
  [1] line       presence_line(): study = 'Travis is here with you in the room.' (unchanged); garden/shore/wood never
                 say 'in the room' and each has its own outdoor wording; the garden wording is the sensorium's own;
                 an unlisted non-study place is still not 'in the room'; absent = None; an errand line is unchanged
  [2] events     the one-shot arrive / leave events are worded for the place Du is on the tick they are DELIVERED
                 (cottage door seen from outside), indoors unchanged, nothing held: the queue is empty after one read
  [3] one clock  sensorium's latch follows companion.is_present(): after a 'restart' (latch False, companion present)
                 the study scene still says he is here; at minute 15 the scene still says it (the old 600 s latch
                 had dropped it); at minute 31 the latch is lowered with NO second departure perception and the
                 companion's single 'stepped out' event is delivered once
  [4] once       the idle composition (scene_line(presence=False) + presence_line()) states his presence exactly once
                 in the study and on the shore; a default scene_line() (executive / voice / nature study) keeps its
                 clause; the monologue call site asks for presence=False
  [5] arrival    human_present() is not an 'arrival' when the companion already has him here; it is when neither does
  [6] fail-open  companion unreadable -> the legacy 600 s latch and its departure perception, 'the room' only indoors
  [7] unchanged  PRESENCE_WINDOW_S is still 30 min (D-0366)
  [8] canary     live stores untouched (size + mtime + hash)

  python scripts/_test_J-2939_companion_presence.py        # exit 0 = ALL OK
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core                                                       # noqa: E402  (core BEFORE lab_env)
assert Path(core.__file__).resolve().is_relative_to(ROOT.resolve()), f"core resolved outside this tree: {core.__file__}"
from core import companion as C                                   # noqa: E402
from core import sensorium as S                                   # noqa: E402
from core import locomotion as L                                  # noqa: E402
from core import cat as CAT                                       # noqa: E402

sys.path.append(str(Path.home() / ".claude" / "skills" / "job-queue"))
import lab_env                                                    # noqa: E402,F401
assert Path(core.__file__).resolve().is_relative_to(ROOT.resolve()), "lab_env shadowed this tree's core"

_LIVE = [Path(r"C:\Nascence") / "data" / n for n in ("companion_state.json", "companion_actions_log.jsonl",
                                                      "room_state.json", "position.json")]
_LIVE += [ROOT / "data" / n for n in ("companion_state.json", "companion_actions_log.jsonl")]


def _snap(p: Path):
    if not p.exists():
        return None
    st = p.stat()
    return (st.st_size, st.st_mtime_ns, hashlib.md5(p.read_bytes()).hexdigest() if st.st_size < 50_000_000 else "")


_before = {p: _snap(p) for p in _LIVE}
FAILS = 0


def check(name, ok, detail=""):
    global FAILS
    print(("  ok   " if ok else "  FAIL ") + name + (f"  -- {detail}" if detail and not ok else ""))
    if not ok:
        FAILS += 1


TMP = Path(tempfile.mkdtemp(prefix="x_J-2939_"))
C._DATA = TMP
C._STATE_F = TMP / "companion_state.json"
C._LOG_F = TMP / "companion_actions_log.jsonl"
S._STATE_F = TMP / "room_state.json"
L._POS_F = TMP / "position.json"
for _p in (C._STATE_F, C._LOG_F, S._STATE_F, L._POS_F):
    assert str(_p).lower().startswith(str(TMP).lower())

# collaborators of the study scene pinned (same stubs the J-3257 scene test uses)
from core import care_package as _CP         # noqa: E402
from core import night_wake as _NW           # noqa: E402
from core import world_detail as _WD         # noqa: E402
from core import study as _STUDY             # noqa: E402
from core import reading as _READING         # noqa: E402

_CP.scene_clause = lambda: ""
_NW.scene_lead = lambda: ""
L.pending_line = lambda: ""
_WD.scene_extra = lambda *a, **k: ""
_READING.current_book = lambda: Path("the_meditations.txt")
_STUDY.shelf = lambda: list(range(7))
_STUDY.misplaced_title = lambda: ""
CAT.presence_line = lambda loc: ""
CAT.distant_line = lambda loc: ""
CAT.state = {"phase": "kept", "location": "indoors", "activity": "sleeping"}
S._daylight = lambda: "evening"
S._season = lambda: "winter"
S._now_parts = lambda: (7, 20)
S._bed_summary = lambda: ""            # would write data/garden.json (non-live fence)
S._letterbox_phrase = lambda: ""


def place(loc):
    S.state.clear()
    S.state.update({"weather": "clear", "weather_until": 0, "wind": "calm", "wind_until": 0, "fire": "burning",
                    "fire_fuel": 0.5, "last_event": 0, "location": loc, "woodpile": 4, "milestones": {}})
    L._POS_F.write_text(json.dumps({"place": loc, "standpoint": "", "journey": None, "effort": 0.0,
                                    "carried_wood": 0}), encoding="utf-8")


def companion_reset(present: bool, last_ago_s: float = 5.0):
    C._pending_events.clear()
    now = time.time()
    C._state.clear()
    C._state.update({"present": present, "since_ts": (now - last_ago_s) if present else None,
                     "last_activity_ts": now - last_ago_s, "errand": None, "found_cupboard_matches": False})


def n_here(text):
    return text.count("Travis is here")


# ── [7] unchanged window ──────────────────────────────────────────────────────────────────────────────────
print("[7] unchanged")
check("PRESENCE_WINDOW_S still 30 min", C.PRESENCE_WINDOW_S == 30 * 60)

# ── [1] the line by place ─────────────────────────────────────────────────────────────────────────────────
print("[1] line")
companion_reset(True)
place("study")
check("study: unchanged wording", C.presence_line() == "Travis is here with you in the room.")
for loc in ("garden", "shore", "wood"):
    place(loc)
    companion_reset(True)
    ln = C.presence_line()
    check(f"{loc}: no 'in the room'", ln and "in the room" not in ln and "room" not in ln, ln)
    check(f"{loc}: says he is here, once", ln and n_here(ln) == 1, ln)
    check(f"{loc}: explicit location arg gives the same line", C.presence_line(loc) == ln)
check("three outdoor wordings are distinct", len({C.presence_line(l) for l in ("garden", "shore", "wood")}) == 3)
check("garden wording is the sensorium's own clause",
      (" " + C.presence_line("garden")) in (S._garden_scene_line(True) if (S.__dict__.update(_was_present=True) or True) else ""))
S._was_present = False
check("unlisted non-study place: not 'in the room'", "in the room" not in C.presence_line("cellar"))
companion_reset(False)
check("absent: None", C.presence_line("shore") is None)
companion_reset(True)
C._state["errand"] = {"kind": "x"}
_orig_out, _orig_adv = C._out_phrase, C._advance
C._out_phrase = lambda: "down on the shore for kindling"
C._advance = lambda: None
check("errand line unchanged", C.presence_line("shore") == "Travis is out — down on the shore for kindling; he'll be back.")
C._out_phrase, C._advance = _orig_out, _orig_adv

# ── [2] one-shot events by delivery place ─────────────────────────────────────────────────────────────────
print("[2] events")
place("study")
companion_reset(False, last_ago_s=99999)
C.note_activity("exchange")                       # absent -> present: emits the arrival
check("arrival queued", len(C._pending_events) == 1)
ev_out = C.consume_witnessed_event("shore")       # Du is on the shore when it is delivered
check("arrival outdoors: the cottage, not boots", ev_out and "cottage" in ev_out and "boots" not in ev_out
      and "in from outside" not in ev_out, ev_out)
check("nothing held: queue empty after one read", C.consume_witnessed_event("shore") is None and not C._pending_events)
companion_reset(False, last_ago_s=99999)
C.note_activity("exchange")
check("arrival indoors: unchanged wording", C.consume_witnessed_event("study")
      == "Travis comes back in from outside, stamping the cold off his boots.")
# departure
companion_reset(True, last_ago_s=C.PRESENCE_WINDOW_S + 60)
C._tick_presence()
check("departure queued once", len(C._pending_events) == 1 and not C._state["present"])
ev = C.consume_witnessed_event("garden")
check("departure outdoors: gone in to the cottage", ev and "gone in" in ev and "stepped out" not in ev
      and "room" not in ev, ev)
companion_reset(True, last_ago_s=C.PRESENCE_WINDOW_S + 60)
C._tick_presence()
check("departure indoors: unchanged wording", C.consume_witnessed_event("study")
      == "Travis has stepped out; the door eases shut behind him.")
# emit in the study, deliver outdoors: worded for the delivery place (not guessed at emit time)
S.state["location"] = "study"
companion_reset(False, last_ago_s=99999)
C.note_activity("exchange")
S.state["location"] = "wood"
check("emit while in the study, deliver in the wood: true in the wood", "cottage" in (C.consume_witnessed_event() or ""))
# a plain string event (errand stage / action) is untouched
C._pending_events.clear()
C._emit("He lays the fire.", "action")
check("plain event passes through unchanged", C.consume_witnessed_event("shore") == "He lays the fire.")
# toggle path
companion_reset(False, last_ago_s=99999)
r = C.set_present(True)
check("toggle on: composer narration unchanged", r["narration"] == "Travis comes in from outside, stamping the cold off his boots.")
check("toggle on: Du-side event worded outdoors", "cottage" in (C.consume_witnessed_event("shore") or ""))
rows = [json.loads(x) for x in C._LOG_F.read_text(encoding="utf-8").splitlines() if x.strip()]
check("log keeps the indoor narration and records the outdoor wording",
      any(r_.get("event") == "arrive" and r_.get("outdoor_narration") and "boots" in r_["narration"] for r_ in rows))

# ── [3] one clock ─────────────────────────────────────────────────────────────────────────────────────────
print("[3] one clock")
place("study")
companion_reset(True, last_ago_s=5)
S._was_present, S._last_human_ts = False, 0.0                 # a restart: the in-memory latch is gone
sc = S.scene_line()
check("after a restart the study scene still says he is here (companion clock)", n_here(sc) == 1, sc[-200:])
place("study")
companion_reset(True, last_ago_s=15 * 60)                     # minute 15: the old 600 s latch had dropped him here
S._was_present, S._last_human_ts = True, time.time() - 15 * 60
check("minute 15: _presence_tick says nothing and keeps the latch", S._presence_tick() is None and S._was_present)
check("minute 15: the scene still says he is here", n_here(S.scene_line()) == 1)
check("minute 15: the standing line agrees", C.presence_line() == "Travis is here with you in the room.")
place("study")
companion_reset(True, last_ago_s=31 * 60)                     # minute 31: the companion's window has lapsed
S._was_present, S._last_human_ts = True, time.time() - 31 * 60
check("minute 31: no second departure perception", S._presence_tick() is None)
check("minute 31: latch lowered, scene silent", (not S._was_present) and n_here(S.scene_line()) == 0)
check("minute 31: the companion's single departure event is delivered once",
      (C.consume_witnessed_event("study") or "").count("stepped out") == 1 and C.consume_witnessed_event("study") is None)
place("study")
companion_reset(False, last_ago_s=99999)
S._was_present, S._last_human_ts = True, time.time() - 20            # a message just arrived, reply not yet written
check("message in flight (companion not yet noted): latch holds", S._presence_tick() is None and S._was_present)

# ── [4] exactly once in the idle prompt ────────────────────────────────────────────────────────────────────
print("[4] once")
for loc in ("study", "garden", "shore", "wood"):
    place(loc)
    companion_reset(True, last_ago_s=60)
    S._was_present, S._last_human_ts = True, time.time() - 60
    idle = S.scene_line(presence=False) + "\n" + (C.presence_line() or "")
    check(f"idle composition in the {loc}: stated exactly once", n_here(idle) == 1, idle[-260:])
    if loc != "study":
        check(f"idle composition in the {loc}: never 'in the room'", "in the room" not in idle)
place("study")
S._was_present = True
companion_reset(True)
check("default scene_line() (executive / voice / nature study) keeps its clause", n_here(S.scene_line()) == 1)
check("garden fallback line: clause present by default, absent with presence=False",
      n_here(S._garden_scene_line()) == 1 and n_here(S._garden_scene_line(presence=False)) == 0)
src = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
check("monologue call site asks for scene_line(presence=False)", "_scene = scene_line(presence=False)" in src)

# ── [5] arrival ────────────────────────────────────────────────────────────────────────────────────────────
print("[5] arrival")
place("study")
companion_reset(True, last_ago_s=300)
S._was_present, S._last_human_ts = False, 0.0
check("already here per the companion (after a restart): no arrival perception", S.human_present() is None)
companion_reset(False, last_ago_s=99999)
S._was_present, S._last_human_ts = False, 0.0
check("neither has him: arrival perception", (S.human_present() or "").startswith("Travis has come to talk"))

# ── [6] fail-open ──────────────────────────────────────────────────────────────────────────────────────────
print("[6] fail-open")
_real_is_present = C.is_present


def _boom():
    raise RuntimeError("companion unreadable")


C.is_present = _boom
try:
    for loc, want_room in (("study", True), ("shore", False), ("wood", False), ("garden", False)):
        place(loc)
        S._was_present, S._last_human_ts = True, time.time() - 700
        out = S._presence_tick()
        check(f"legacy departure perception in the {loc}", bool(out) and out.startswith("Travis has gone for now."), out)
        check(f"legacy departure in the {loc}: 'room' only indoors", ("room" in out) == want_room, out)
        check(f"legacy latch lowered in the {loc}", S._was_present is False)
    place("study")
    S._was_present, S._last_human_ts = True, time.time() - 20
    check("legacy: a fresh latch holds", S._presence_tick() is None and S._was_present)
    check("legacy: scene_line does not raise", isinstance(S.scene_line(), str))
finally:
    C.is_present = _real_is_present

# ── [8] canary ─────────────────────────────────────────────────────────────────────────────────────────────
print("[8] canary")
after = {p: _snap(p) for p in _LIVE}
check("live stores untouched", after == _before, str({p.name: (b, after[p]) for p, b in _before.items() if after[p] != b}))
shutil.rmtree(TMP, ignore_errors=True)

print("\nALL OK" if FAILS == 0 else f"\n{FAILS} FAILED")
sys.exit(1 if FAILS else 0)
