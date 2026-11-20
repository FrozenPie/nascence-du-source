"""
Cat Overhaul C3 -- his call (J-2468, D-0499 / D-0505 (c), 2026-10-28)
======================================================================
HERMETIC: every store core/cat_call.py, core/cat.py, core/cat_sounds.py and core/cat_ears.py (and what they
reach) can write is redirected into a tempfile.mkdtemp() dir OUTSIDE data/ before any write (the J-2465 /
J-2466 / J-2467 harness pattern); every cross-module writer is stubbed; the live C:\\Nascence\\data top-level
files are fingerprinted before and after and any change (bar arousal_shadow.jsonl / hud.err.log) is reported as
a LEAK. `import core` BEFORE anything else and core.__file__ must resolve under this worktree.

What it proves (simulated clock; the world is a dict this script owns):
  T1  fields: call / name_recognition on an old state; LIVE by default; the life_flags kill switch holds
  T2  the grammar: a call verb + a cat word is a call; the morepork's call is a noun; a bare "her" only inside
      A2's anaphora window; "I will call her Ash" while unnamed is the R1 act (naming), never a call; once named,
      "I call Ash" is a call by name; "call to" is no longer a stroke (no TEND line, no last_tended stamp)
  T3  what he called: puss / the kissing noise / her name / "by name" / the default
  T4  the carry in reverse: garden from the study door with the door open reaches; shut, it does not; the wood
      is beyond "puss-puss" from anywhere; the name reaches the wood's edge physically but is "a voice she does
      not place" until learned; hard wind masks it; the row says why, the LINE never does
  T5  her hearing gate: storm none (even in the room), hunting far none, in transit yes (the leg's midpoint),
      asleep-deep a quarter, asleep a half, dozing three quarters
  T6  her decision: the tom present -> no; afraid -> nothing; handled four times this hour -> ignores; aloof ->
      a sound and no move; hungry + bonded -> comes, and fast (the first leg shortened)
  T7  the answer, sound first: answered_ts -> cat_sounds emits cat_trill from HER state, the answer pool, carried
      to him; then her legs (a real transit, dest "coming to your call"); she lands, presence_line fires the
      greeting and releases the hold; an answer in the room is his own line and never a second percept;
      silence is silence (no stamp, no legs, no explanation)
  T8  the name as a learned sound: called by name and came -> name_recognition rises; fed within the window
      after a name-call -> rises again, once per call; past the threshold the name reaches her at the wood's
      edge where puss-puss never does; nothing he reads carries any of it
  T9  the ledger: fenced path, row shape (call / fed_after_call), rotation to .1 past the cap
  T10 D-0434 no readout: no digit, no reason word in any CALL / answer / arrival line; status() keys unchanged;
      cat_call writes no prompt line; nothing in core but cat_call reads cat_call_ledger
  T11 soundscape: his call is "cat_call" (object his own voice) in _sec_cat for its window, never a percept key
  T12 cat.call() public API: what given outright; the here-gate is bypassed for a call and nothing else
  T13 what must survive: a stroke with her here is still a stroke; the naming latch still names
Run:  python scripts/_test_cat_call_J-2468.py   (from the worktree root)
"""
from __future__ import annotations
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789: no write to the tree's data/

import json
import random
import re
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core                                            # noqa: E402  -- BEFORE anything else (house rule)
WT = str(Path(__file__).resolve().parents[1])   # this checkout, wherever it sits (was the jr1028 cat worktree)
assert str(Path(core.__file__).resolve()).lower().startswith(WT.lower()), f"core resolves outside the worktree: {core.__file__}"

LIVE_DATA = Path(r"C:\Nascence\data")
_IGNORE = {"arousal_shadow.jsonl", "hud.err.log"}


def _fingerprint() -> dict:
    out = {}
    try:
        for p in LIVE_DATA.iterdir():
            if p.is_file():
                st = p.stat()
                out[p.name] = (st.st_size, st.st_mtime)
    except Exception:
        pass
    return out


FP_BEFORE = _fingerprint()

from core import cat, cat_call, cat_ears, cat_sounds, cat_content, life, locomotion, sensorium, world_clock  # noqa: E402
from core import world_traces, life_traces, activity_memory, study_life, companion, wood_life, provisions, soundscape  # noqa: E402
from core import world_substrate, world_objects, cat_referent, fieldcraft, boredom  # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="cat_call_J2468_"))
print("isolated store dir:", TMP)
cat._STATE_F = TMP / "cat_state.json"
cat._HUNT_LEDGER_F = TMP / "cat_hunt_ledger.jsonl"
cat._FOUND_LEDGER_F = TMP / "cat_found_ledger.jsonl"
cat._FOUND_FLAGS_F = TMP / "life_flags.json"
cat._GAUGE_F = TMP / "cat_presence_gauge.jsonl"
cat._TIER_LEDGER_F = TMP / "cat_tier_ledger.jsonl"
cat_sounds._LEDGER = TMP / "cat_sound_ledger.jsonl"

# J-2473 (cat_overhaul B4): the presence line is now read DOSED at the idle-scene stop (core/cat_loop: a ride stays up
# 90 s for every consumer, the same tuple rides again only on a habituating gap). This harness samples the ORDINARY
# line's pools many times inside one real second, which is exactly what the dose folds into one room -- so the dose is
# switched off here (its own test is scripts/_test_cat_loop_J-2473.py) and its stores are redirected like the others.
from core import cat_loop as _cat_loop, transport_manager as _tm_loop, coupling_rides as _cr_loop  # noqa: E402
_cat_loop.CAT_DOSED = False
_cat_loop._LEDGER = TMP / "cat_loop_ledger.jsonl"
_cat_loop._FLAGS_F = TMP / "life_flags.json"
_tm_loop._STATE, _tm_loop._SHADOW_LOG = TMP / "transport_lines.json", TMP / "transport_shadow.jsonl"
_cr_loop._LOG = TMP / "coupling_rides.jsonl"
cat_sounds._FLAGS_F = TMP / "life_flags.json"
cat_ears._LEDGER = TMP / "cat_reactions.jsonl"
cat_ears._FLAGS_F = TMP / "life_flags.json"
from core import cat_tom  # noqa: E402  -- B3 (J-2470): cat.tick -> cat_tom.tick writes data/cat_tom_state.json + cat_tom_ledger.jsonl (fenced); redirected per life_smoke's own rule
cat_tom._STATE_F = TMP / "cat_tom_state.json"
cat_tom._LEDGER = TMP / "cat_tom_ledger.jsonl"
cat_tom._FLAGS_F = TMP / "life_flags.json"
try:   # J-2471 (cat_overhaul D-2): her mortality ledger is a guard_path()-fenced write target cat.tick reaches -- redirected like the tom's
    from core import cat_harm as _cat_harm_mod
    _cat_harm_mod._LEDGER = TMP / "cat_harm_ledger.jsonl"
    _cat_harm_mod._FLAGS_F = TMP / "life_flags.json"
except Exception:
    pass
cat_tom.live_on = lambda: False          # the tom is J-2470's; in this harness he stays on the ridge (no random visit can move her or refuse a call)
cat_call._LEDGER = TMP / "cat_call_ledger.jsonl"
cat_call._FLAGS_F = TMP / "life_flags.json"
world_traces._TRACES_F = TMP / "world_traces.json"
locomotion._POS_F = TMP / "position.json"
life._F = TMP / "life_state.json"
life._LEDGER = TMP / "life_ledger.jsonl"
life._EVENTS = TMP / "life_events.jsonl"
life._FLAGS_F = TMP / "life_flags.json"
provisions._F = TMP / "provisions.json"
provisions._LOG = TMP / "provisions_log.jsonl"
companion._STATE_F = TMP / "companion_state.json"
companion._LOG_F = TMP / "companion_actions_log.jsonl"
wood_life._F = TMP / "wood_life.json"
wood_life._EVENTS = TMP / "wood_events.jsonl"
wood_life._LEDGER = TMP / "wood_ledger.jsonl"
world_substrate._SUBSTRATE_F = TMP / "world_substrate.json"
world_objects._OBJECTS_F = TMP / "world_objects.json"
cat_referent._LEDGER = TMP / "cat_referent_ledger.jsonl"
fieldcraft._F = TMP / "fieldcraft.json"
fieldcraft._LEDGER = TMP / "fieldcraft_ledger.jsonl"
STUBS = {"activity": [], "carcass": [], "trace": [], "deed": [], "discharge": []}
activity_memory.record = lambda *a, **k: STUBS["activity"].append(a)
life_traces.add_carcass = lambda *a, **k: STUBS["carcass"].append(a)
world_traces.create_trace = lambda *a, **k: STUBS["trace"].append(a)
life.note_deed = lambda *a, **k: STUBS["deed"].append(a)
boredom.discharge = lambda *a, **k: STUBS["discharge"].append(a) or 0.0
cat_ears.live_on = lambda: False          # her ears are J-2467's; this harness drives her legs through the call only


class _Clock:
    """The simulated clock: every time.time() in the cat modules reads SIM["now"]; everything else is the real module."""
    def __getattr__(self, k):
        return getattr(_real_time, k)

    def time(self):
        return SIM["now"]


_real_time = time
cat.time = cat_call.time = cat_sounds.time = cat_ears.time = _Clock()

# the world around them: a dict we own
SIM = {"now": 0.0, "door_open": True, "window_open": False, "season": "summer"}
sensorium.state = {"weather": "clear", "wind": "calm", "fire": "out", "location": "study", "asleep": False, "study": {}}
sensorium._daylight = lambda: world_clock.daylight(SIM["now"])
sensorium._season = lambda: SIM["season"]
study_life.door_open = lambda: SIM["door_open"]
study_life._st = lambda: {"door_open": SIM["door_open"], "window_open": SIM["window_open"]}
cat_sounds._birds_about = lambda: False
cat_sounds.render_on = lambda: True       # C1 is RENDER-on live (data/life_flags.json cat_sounds_render true)

FAILS: list[str] = []
OKS = 0


def check(cond, msg):
    global OKS
    if cond:
        OKS += 1
        print("  ok  ", msg)
    else:
        FAILS.append(msg)
        print("  FAIL", msg)


def fresh_cat(now: float, **kw) -> dict:
    cat.state = {}
    cat._state_mtime = 0.0
    cat._last_tick = 0.0
    cat._prev_ref_txt = ""
    cat_call._mem.update({"last_call_ts": 0.0})
    for f in (cat_call._LEDGER, cat_sounds._LEDGER):
        if f.exists():
            f.unlink()
    cat_sounds._mem.update({"last": 0.0, "act": None, "loc": None, "greet_ts": 0.0, "audible": {}, "holds_prev": {},
                            "last_fired": {}, "audible_line": {}, "answer_ts": 0.0, "trill_answer": None})
    st = {"phase": "kept", "name": "", "bond": 0.8, "location": "by_the_fire", "activity": "watching",
          "mood": "content", "appeared_ts": now - 100 * 86400, "last_fed": now - 3600, "last_seen": now,
          "quirks": {"storm_response": "under_desk", "greeting": "chirrup", "fair_spot": "windowsill", "stranger_response": "inspects"},
          "firsts": {"first_lap": 1.0, "first_slow_blink": 1.0, "first_silent_meow": 1.0, "first_shore_follow": 1.0, "first_play": 1.0},
          "last_tended": now - 7200, "last_greeted_ts": now - 7200, "arc": {}, "saucer": {"has_food": False, "kind": "", "set_ts": 0.0},
          "_was_in": True, "fur_moisture": 0.0, "last_fur_decay_ts": now, "last_bond_decay_ts": now, "name_invited": True,
          "body": {"hunger": 0.3, "thirst": 0.2, "energy": 0.7, "warmth": 0.5, "condition": 0.7, "bout": "active",
                   "bout_until": now + 1800, "bout_since": now, "last_ts": now, "last_drank_ts": 0.0, "cold_hours": 0.0, "last_meal": ""}}
    st.update(kw)
    cat._STATE_F.write_text(json.dumps(st), encoding="utf-8")
    return cat._load()


def ledger(path=None) -> list[dict]:
    path = path or cat_call._LEDGER
    try:
        return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    except Exception:
        return []


def write_pos(**d):
    locomotion._POS_F.write_text(json.dumps(d), encoding="utf-8")


def find_phase(want: str, start: float) -> float:
    t = start
    for _ in range(48 * 6):
        if world_clock.daylight(t) == want:
            return t
        t += 600
    raise RuntimeError(want)


def sound_sample(now: float) -> list[dict]:
    cat_sounds._mem["last"] = 0.0
    return cat_sounds.tick(cat.state, now)


BASE = 1_800_000_000.0
DAY = find_phase("day", BASE)
SIM["now"] = DAY
write_pos(place="study", standpoint="at_the_door", journey=None, gate_ts=0.0)
_real_random = random.random

# ── T1 fields + the switch ──────────────────────────────────────────────────────────────────────────
print("\nT1 fields and the kill switch")
st = fresh_cat(DAY)
check(st.get("call") == {} and st.get("name_recognition") == 0.0, "an old state gains call / name_recognition on load")
check(cat_call.live_on() is True, "LIVE by code default")
(TMP / "life_flags.json").write_text(json.dumps({"cat_call_live": False}), encoding="utf-8")
cat_call._flags_cache["ts"] = 0.0
check(cat_call.live_on() is False, "life_flags.json cat_call_live=false switches the hand off (hot)")
r = cat.react("I call the cat in from the garden.", "", "study")
check(r is None and not ledger() and not cat.state.get("call"), "off: a call is no deed at all (no line, no row, no stamp)")
(TMP / "life_flags.json").unlink()
cat_call._flags_cache["ts"] = 0.0
check(cat_call.live_on() is True, "back on")

# ── T2 the grammar ──────────────────────────────────────────────────────────────────────────────────
print("\nT2 the grammar")
random.random = lambda: 0.0      # she hears, she comes
st = fresh_cat(DAY, location="garden", activity="watching")
r = cat.react("I go to the door and call the cat in.", "", "study")
check(bool(r) and ledger() and ledger()[-1]["kind"] == "call", f"a call verb + a cat word is a call: {r[:70] if r else r}")
st = fresh_cat(DAY, location="garden", activity="watching")
r = cat.react("The call of the morepork cuts the dark wood; I sit with the cat on my knee.", "", "study")
check(not ledger(), "the morepork's call is a noun, not his deed (no row)")
st = fresh_cat(DAY, location="garden", activity="watching")
r = cat.react("I call her in.", "", "study")
check(not ledger() and r is None, "a bare 'her' with no antecedent is nobody (not a call)")
st = fresh_cat(DAY, location="by_the_fire", activity="washing")
cat.react("The cat is washing by the fire, one leg up like a cello.", "", "study")   # her here: the window moves (A2's own rule)
r = cat.react("I call her over.", "", "study")
check(bool(r) and ledger() and ledger()[-1]["kind"] == "call", "a bare 'her' the thought after a cat noun is her (A2's own window)")
st = fresh_cat(DAY, location="garden", activity="watching")
r = cat.react("She has been mine for weeks now. I will call her Ash.", "", "garden")
check(cat.state.get("name") == "Ash" and cat.state.get("phase") == "companion" and not ledger(), f"'I will call her Ash' while unnamed is the R1 act, not a call: {r[:60] if r else r}")
r = cat.react("I call Ash in from the garden.", "", "study")
check(bool(r) and ledger() and ledger()[-1]["by_name"] is True and ledger()[-1]["what"] == "name", "once named, 'I call Ash' is a call BY NAME")
check("call to" not in cat._TEND_VERBS, "'call to' has left the tend verbs")
st = fresh_cat(DAY, location="by_the_fire", activity="watching")
t0 = cat.state["last_tended"]
r = cat.react("I call to the cat softly.", "", "study")
check(bool(r) and cat.state["last_tended"] == t0 and ledger()[-1]["kind"] == "call" and not any(
    s in r for s in ("engine of her", "kneads", "headbutts", "accepts the long stroke")), f"'call to' with her here is a CALL, not a stroke: {r[:70]}")
random.random = _real_random

# ── T3 what he called ───────────────────────────────────────────────────────────────────────────────
print("\nT3 what he called")
check(cat_call.what_called("i call puss-puss into the garden", "") == ("puss-puss", False), "puss-puss")
check(cat_call.what_called("i call puss, puss, puss", "Ash") == ("puss-puss", False), "puss (named cat, name not said): puss-puss")
check(cat_call.what_called("i make the kissing noise and call the cat", "") == ("the kissing noise", False), "the kissing noise")
check(cat_call.what_called("i click my tongue for the cat", "") == ("the kissing noise", False), "a click of the tongue is the kissing noise")
check(cat_call.what_called("i call ash", "Ash") == ("name", True), "her name")
check(cat_call.what_called("i call her by name", "Ash") == ("name", True), "'by name' when she has one")
check(cat_call.what_called("i call her by name", "") == ("puss-puss", False), "'by name' with no name is the ordinary call (never invents one)")
check(cat_call.what_called("i call the cat", "") == ("puss-puss", False), "unspecified: the ordinary call")

# ── T4 the carry in reverse ─────────────────────────────────────────────────────────────────────────
print("\nT4 the carry in reverse (his position the origin, hers the observer)")
random.random = lambda: 0.0


def one_call(text="I call the cat.", place="study", **kw):
    fresh_cat(DAY, **kw)
    r = cat.react(text, "", place)
    return r, ledger()[-1]


r, row = one_call(location="garden", activity="watching")
check(row["reaches"] and row["heard"] and row["dist_m"] and row["dist_m"] < 15, f"garden from the study door, door open: reaches ({row['dist_m']} m, reach {row['reach_eff']})")
SIM["door_open"] = False
r, row = one_call(location="garden", activity="watching")
check(not row["reaches"] and not row["heard"] and "house shut" in row["why"], f"house shut: the call does not get out ({row['why']})")
check(not any(w in r.lower() for w in ("shut", "door", "too far", "cannot", "hear")), f"...and the LINE says nothing of why: {r[:80]}")
SIM["door_open"] = True
r, row = one_call(location="wood", activity="hunting in the leaf-litter")
check(not row["reaches"] and row["dist_m"] > 80, f"the wood is beyond puss-puss from the study ({row['dist_m']} m)")
r, row = one_call("I call the cat.", "garden", location="wood", activity="hunting in the leaf-litter")
check(not row["reaches"], "...and from the garden too (75 m against 30)")
r, row = one_call("I call Ash.", "study", name="Ash", phase="companion", location="wood", activity="hunting in the leaf-litter")
check(row["reaches"] and not row["heard"] and row["why"] == "at range, a voice she does not place", f"the NAME reaches the wood's edge physically ({row['dist_m']} m) but is a voice she does not place yet")
check(not any(w in r.lower() for w in ("place", "know", "learn", "far", "range")), f"...and the line says nothing of it: {r[:80]}")
r, row = one_call("I call Ash.", "study", name="Ash", phase="companion", location="wood", activity="hunting in the leaf-litter", name_recognition=0.6)
check(row["reaches"] and row["heard"] and row["name_known"], "learned: the name reaches her at the wood's edge from the study door")
sensorium.state["wind"] = "gale"
r, row = one_call("I call Ash.", "study", name="Ash", phase="companion", location="wood", activity="hunting in the leaf-litter", name_recognition=0.6)
check(not row["reaches"] and "hard wind" in row["why"], f"a gale masks even the learned name at that range ({row['why']})")
sensorium.state["wind"] = "calm"
r, row = one_call("I call Ash.", "study", name="Ash", phase="companion", location="garden", activity="watching", name_recognition=0.0)
check(row["reaches"] and row["heard"], "an unlearned name within the near range is still HIM to her (she knows his voice)")
random.random = _real_random

# ── T5 her hearing gate ─────────────────────────────────────────────────────────────────────────────
print("\nT5 her hearing gate")
random.random = lambda: 0.0
r, row = one_call(location="under_desk", activity="storm_hide", mood="afraid")
check(row["reaches"] and not row["heard"] and row["hearing"] == "storm", "storm: nothing reaches her, even in the room")
r, row = one_call(location="away_hunting", activity="hunting")
check(not row["heard"] and row["hearing"] == "hunting_far", "hunting far: none")
r, row = one_call(location="in_transit", activity="on her way", transit={"from": "garden", "to": "study", "path": [], "started": DAY - 10,
                  "leg_ends": DAY + 60, "dest": {"location": "indoors", "activity": "watching", "mood": "content"}, "origin": "garden"})
check(row["reaches"] and row["heard"] and row["hearing"] == "transit", f"in transit: yes, from the leg's midpoint ({row['dist_m']} m)")
for energy, label, p in ((0.3, "asleep_deep", 0.25), (0.8, "asleep", 0.5)):
    random.random = lambda p=p: p - 0.01
    r, row = one_call(location="by_the_fire", activity="sleeping", body=dict(fresh_cat(DAY)["body"], energy=energy))
    heard_under = row["heard"]
    random.random = lambda p=p: p + 0.01
    r, row2 = one_call(location="by_the_fire", activity="sleeping", body=dict(fresh_cat(DAY)["body"], energy=energy))
    check(row["hearing"] == label and heard_under and not row2["heard"], f"{label}: heard with probability {p} (just under hears, just over does not)")
random.random = lambda: 0.74
r, row = one_call(location="by_the_fire", activity="dozing")
check(row["hearing"] == "dozing" and row["heard"], "dozing: three quarters")
random.random = _real_random

# ── T6 her decision ─────────────────────────────────────────────────────────────────────────────────
print("\nT6 her decision")
random.random = lambda: 0.0
r, row = one_call(location="garden", activity="watching", tom={"present": True})
check(row["heard"] and not row["answered"] and row["why"] == "the tom is there", "the tom present (B3's hook): no")
r, row = one_call(location="garden", activity="watching", mood="afraid")
check(row["heard"] and not row["answered"] and row["why"] == "afraid", "afraid: nothing")
r, row = one_call(location="garden", activity="watching", _handled_ts=[DAY - 100, DAY - 200, DAY - 300, DAY - 400])
check(row["heard"] and not row["answered"] and "handled" in row["why"], "handled four times this hour: she ignores it")
r, row = one_call(location="garden", activity="watching", mood="aloof")
check(row["answered"] and not row["came"] and cat.state["location"] == "garden" and not cat.state.get("transit"), "aloof: a sound, and she does not move")
r, row = one_call(location="by_the_fire", activity="watching", mood="aloof")
check(row["answered"] and not row["came"] and "does not move" in r or "stays exactly" in r or "goes on with" in r, f"aloof in the room: answers from her spot: {r[-70:]}")
cat._cat_leg_secs = lambda *a, **k: 100.0
r, row = one_call(location="garden", activity="watching", body=dict(fresh_cat(DAY)["body"], hunger=0.8))
t_h = cat.state["transit"]
check(row["came"] and "hungry" in row["why"] and t_h and abs((t_h["leg_ends"] - DAY) - 70.0) < 0.01, f"hungry + bonded: comes, and fast (first leg {round(t_h['leg_ends'] - DAY)} s of 100)")
r, row = one_call(location="garden", activity="watching", body=dict(fresh_cat(DAY)["body"], hunger=0.1))
t_n = cat.state["transit"]
check(row["came"] and t_n and abs((t_n["leg_ends"] - DAY) - 100.0) < 0.01, "not hungry: comes at her ordinary pace")
random.random = lambda: 0.99
r, row = one_call(location="garden", activity="watching", bond=0.2)
check(row["heard"] and row["answered"] and not row["came"], "a thin bond, an unlucky roll: a sound, no walk (never a refusal to answer him)")
random.random = _real_random

# ── T7 the answer, sound first ──────────────────────────────────────────────────────────────────────
print("\nT7 the answer comes back as sound first, then her legs, then the greeting")
random.random = lambda: 0.0
cat._cat_leg_secs = lambda *a, **k: 100.0
r, row = one_call("I call the cat in.", "study", location="garden", activity="watching", bond=0.65)   # bonded, below the companion tier: no blink pre-empts the pool
cs = cat.state["call"]
check(cs.get("answered_ts") == DAY and cs.get("came") and not cs.get("answer_here"), "answered_ts stamped, came, not an answer-in-the-room")
check(cat.state["location"] == "in_transit" and (cat.state.get("transit") or {}).get("dest", {}).get("activity") == "coming to your call"
      and (cat.state.get("reaction") or {}).get("kind") == "call", "her legs: a real transit toward him, dest 'coming to your call', held by a call reaction")
check(not any(w in r for w in ("chirrup", "trill", "note")), f"his own line carries no answer yet (the sound comes through her voice): {r[:80]}")
rows = sound_sample(DAY + 30)
trill = [x for x in rows if x["key"] == "cat_trill"]
check(len(trill) == 1 and trill[0].get("answer") and trill[0]["audible"] and trill[0]["kind"] == "sounded", f"cat_sounds emits the answer trill from HER state, audible: {trill[0]['line'] if trill else rows}")
check(trill and any(w in trill[0]["line"] for w in ("chirrup", "trill", "rolled note")) and ("answer" in trill[0]["line"] or "reply" in trill[0]["line"] or "coming back" in trill[0]["line"]),
      "...from the ANSWER pool (carried): it is a reply, from where she is")
check(cat_sounds.line_now("cat_trill") == trill[0]["line"] and "cat_trill" in cat_sounds.audible_now("study", DAY + 30), "...and the percept rail can carry it to him (line_now)")
check(not [x for x in sound_sample(DAY + 90) if x["key"] == "cat_trill"], "one-shot: the same answer never sounds twice")
cat._advance_transit(DAY + 200)
check(cat.state["location"] == "indoors" and cat.state["activity"] == "coming to your call", "she lands where he is, coming to his call")
SIM["now"] = DAY + 200
line = cat.presence_line("study")
# the greeting_chirrup pool (cat_content, base 08-27) holds one line without the word "chirrup" (the nose-to-
# knuckle greeting); the greeting is any line of that pool, one-shot, stamped on last_greeted_ts
check(any(w in line for w in ("chirrup", "offered knuckle")) and cat.state["last_greeted_ts"] == DAY + 200, f"...and arrives with the greeting: {line[:80]}")
check(cat.state.get("reaction") is None, "the call's hold on her is released on the greeting")
line2 = cat.presence_line("study")
check(line2 and "the second she sees you" not in line2 and "saves for you" not in line2 and cat.state["last_greeted_ts"] == DAY + 200 and any(
    w in line2 for w in ("trot", "unhurried", "flag", "feet", "sent for", "looked at", "question")), f"after the greeting, her arrival pool renders (coming_to_call): {line2[:80]}")
SIM["now"] = DAY
# an answer in the room
r, row = one_call("I call the cat.", "study", location="by_the_fire", activity="watching")
check(row["here"] and row["answered"] and cat.state["call"].get("answer_here") and ("chirrup" in r or "small thing" in r), f"in the room: the answer is his own line: {r[-80:]}")
rows = sound_sample(DAY + 30)
trill = [x for x in rows if x["key"] == "cat_trill"]
check(len(trill) == 1 and trill[0].get("answer") and trill[0]["audible"] and cat_sounds.line_now("cat_trill") == "" and "cat_trill" in cat_sounds.audible_now("study", DAY + 30),
      "...the trill still sounds for the census / active_sounds but is never a SECOND percept (line_now empty)")
line = cat.presence_line("study")
check("chirrup" not in line or "answer" in line, f"...and he is not greeted twice for an answer given in the room: {line[:70]}")
# silence
random.random = lambda: 0.99
r, row = one_call("I call the cat.", "study", location="away_hunting", activity="hunting")
check(not row["heard"] and not cat.state["call"].get("answered_ts") and cat.state["location"] == "away_hunting" and not cat.state.get("transit"),
      "silence: no stamp, no legs, she is where she was")
check(not [x for x in sound_sample(DAY + 30) if x["key"] == "cat_trill"], "...and no trill")
check(r and not any(w in r.lower() for w in ("hunt", "far", "hear", "asleep", "wind", "why")), f"...and the line is only what he did and heard: {r[:90]}")
random.random = _real_random

# ── T8 the name as a learned sound ──────────────────────────────────────────────────────────────────
print("\nT8 the name is a learned sound with range")
random.random = lambda: 0.0
fresh_cat(DAY, name="Ash", phase="companion", location="garden", activity="watching")
cat.react("I call Ash in.", "", "study")
check(cat.state["name_recognition"] == 0.15 and ledger()[-1]["by_name"] and ledger()[-1]["came"], "called by name and came: name_recognition rises (0.15)")
fresh_cat(DAY, name="Ash", phase="companion", location="garden", activity="watching")
cat.react("I call puss-puss.", "", "study")
check(cat.state["name_recognition"] == 0.0, "called puss-puss and came: the NAME learns nothing")
fresh_cat(DAY, name="Ash", phase="companion", location="garden", activity="watching", mood="aloof")
cat.react("I call Ash.", "", "study")
check(cat.state["name_recognition"] == 0.0 and cat.state["call"].get("by_name_ts") == DAY, "called by name, answered but stayed: nothing learned yet; the fed-after window is open")
cat._feed_source = lambda prefer_milk=False: "cat_food"
cat.state["location"], cat.state["activity"], cat.state["mood"] = "indoors", "watching", "content"
SIM["now"] = DAY + 300
r = cat.react("I feed Ash from the tin.", "", "study")
check(abs(cat.state["name_recognition"] - 0.10) < 1e-9 and ledger()[-1]["kind"] == "fed_after_call" and "feed" in r.lower() or "saucer" in r.lower(),
      f"fed inside the window after a name-call: rises (0.10) and a fed_after_call row: {r[:60]}")
check(cat.state["call"].get("by_name_ts") == 0.0, "...the window is consumed (one rise per call)")
cat.react("I feed Ash again.", "", "study")
check(abs(cat.state["name_recognition"] - 0.10) < 1e-9, "a second feed on the same call learns nothing more")
SIM["now"] = DAY
fresh_cat(DAY, name="Ash", phase="companion", location="garden", activity="watching", call={"by_name_ts": DAY - cat_call.NAME_FED_WINDOW_S - 1, "what": "name"})
cat.state["location"] = "indoors"
cat.react("I feed Ash.", "", "study")
check(cat.state["name_recognition"] == 0.0, "fed outside the window: nothing")
fresh_cat(DAY, name="Ash", phase="companion", location="wood", activity="hunting in the leaf-litter", name_recognition=0.45)
cat.react("I call Ash.", "", "study")
check(not ledger()[-1]["heard"] and cat.state["name_recognition"] == 0.45, "below the threshold the name does not reach the wood (nothing learned from a call she did not hear)")
fresh_cat(DAY, name="Ash", phase="companion", location="wood", activity="hunting in the leaf-litter", name_recognition=0.6)
r = cat.react("I call Ash.", "", "study")
check(ledger()[-1]["heard"] and ledger()[-1]["came"] and cat.state["location"] == "in_transit" and cat.state["name_recognition"] == 0.75,
      "at the threshold the name reaches the wood's edge, she comes, and it rises again")
fresh_cat(DAY, name="Ash", phase="companion", location="wood", activity="hunting in the leaf-litter", name_recognition=0.9)
r = cat.react("I call puss-puss.", "", "study")
check(not ledger()[-1]["reaches"], "...where puss-puss never does, however well she knows her name")
random.random = _real_random

# ── T9 the ledger ───────────────────────────────────────────────────────────────────────────────────
print("\nT9 the ledger")
check(str(cat_call._LEDGER).startswith(str(TMP)), "the ledger path is the isolated one (fenced through guard_path)")
rows = ledger()
need = {"ts", "kind", "what", "by_name", "name_known", "recognition", "reaches", "heard", "answered", "came", "here", "decision", "why",
        "hearing", "his", "her", "dist_m", "reach_eff", "bearing", "door_open", "weather", "wind"}
calls = [x for x in rows if x["kind"] == "call"]
check(calls and all(need <= set(x) for x in calls), f"every call row carries the briefing's fields (call, what, heard, answered, came, by_name) + the carry ({len(calls)} rows)")
fresh_cat(DAY, name="Ash", phase="companion", call={"by_name_ts": DAY - 60, "what": "name"})
check(cat_call.note_fed(cat.state, DAY) and ledger()[-1]["kind"] == "fed_after_call" and {"recognition", "name_known", "by_name"} <= set(ledger()[-1]), "the fed_after_call row")
cat_call._ROTATE_BYTES = 10
cat_call._log({"ts": 1, "kind": "x"})
check((TMP / "cat_call_ledger.jsonl.1").exists() and cat_call._LEDGER.read_text(encoding="utf-8").count("\n") == 1, "past the cap the ledger rolls to .1 (one generation kept)")
cat_call._ROTATE_BYTES = 2_000_000

# ── T10 no readout ──────────────────────────────────────────────────────────────────────────────────
print("\nT10 no readout (D-0434)")
bad = []
reason_words = ("recogni", "learn", "threshold", "range", "metre", "too far", "did not hear", "cannot hear", "asleep", "hunting")
for key, pool in cat_content.CALL.items():
    for tpl in pool:
        s = tpl.replace("{her}", "the cat").replace("{name}", "Ash")
        if re.search(r"\d", s) or "{" in s or len(s) > 170 or any(w in s.lower() for w in reason_words):
            bad.append((key, s))
for key in ("answer_here", "answer_carried"):
    for tpl in cat_content.SOUNDS["cat_trill"][key]:
        s = tpl.replace("{her}", "the cat").replace("{dir}", "from the garden")
        if re.search(r"\d", s) or "{" in s or any(w in s.lower() for w in reason_words):
            bad.append((key, s))
for cond, pool in cat_content.PRESENCE["coming_to_call"].items():
    for tpl in pool:
        s = tpl.replace("{her}", "the cat")
        if re.search(r"\d", s) or "{" in s or any(w in s.lower() for w in reason_words):
            bad.append(("coming_to_call", s))
check(not bad, f"no digit, no unfilled token, no reason word in any CALL / answer / arrival line {bad[:2]}")
check(set(cat.status()) == {"phase", "name", "bond", "location", "activity"}, "cat.status() -- the one cat read in his prompt path -- keys unchanged")
src = (ROOT / "core" / "cat_call.py").read_text(encoding="utf-8")
check(all(w not in src for w in ("scene_line", "percept(", "pending_line", "_emit(", "presence_line(", "note_exposures")),
      "cat_call writes no prompt line (no scene/percept/pending/emit/presence writer is called)")
readers = []
for p in sorted((ROOT / "core").glob("*.py")) + sorted((ROOT / "nodes").glob("*.py")):
    txt = p.read_text(encoding="utf-8", errors="replace")
    if p.name not in ("cat_call.py",) and "cat_call_ledger" in txt:
        readers.append(p.name)
check(not readers, f"no core/nodes module but cat_call reads cat_call_ledger.jsonl {readers}")
nr = []
for p in sorted((ROOT / "core").glob("*.py")) + sorted((ROOT / "nodes").glob("*.py")):
    txt = p.read_text(encoding="utf-8", errors="replace")
    if p.name not in ("cat_call.py", "cat.py") and "name_recognition" in txt:
        nr.append(p.name)
check(not nr, f"name_recognition is read by cat_call (and set up by cat) only {nr}")

# ── T11 soundscape ──────────────────────────────────────────────────────────────────────────────────
print("\nT11 his call in the soundscape")
check(soundscape._SOUNDS["cat_call"]["object"] == "his own voice" and "cat_call" in soundscape._EVENT_RATES, "cat_call registered on 'his own voice', rated")
check("cat_call" not in soundscape._PERCEPT_SOUNDS and "cat_call" not in soundscape._CAT_PERCEPT_KEYS, "never a percept key (a self-sound, known instantly)")
cat_call._mem["last_call_ts"] = DAY
ctx = {"loc": "study", "now": DAY + 5, "room": {}, "day": True, "wet": False}
check("cat_call" in soundscape._sec_cat(ctx), "in _sec_cat for its window")
ctx["now"] = DAY + 60
check("cat_call" not in soundscape._sec_cat(ctx), "...and gone after it")
keys = list(soundscape._SOUNDS)
# The chain's anchor rule tells EVERY later cat job to insert its new points right after cat_storm_rustle too
# (J-2470's cat_hiss / cat_growl / distant_yowl land between it and cat_call), so the invariant is "inside
# HER VOICE, after cat_storm_rustle, with nothing but cat points between" -- not one fixed offset.
_between = keys[keys.index("cat_storm_rustle") + 1: keys.index("cat_call")]
check(keys.index("cat_call") > keys.index("cat_storm_rustle")
      and all(k.startswith("cat_") or k == "distant_yowl" for k in _between),
      f"ANCHOR rule: the point sits inside HER VOICE after cat_storm_rustle (between: {_between})")

# ── T12 the public API and the here-gate ────────────────────────────────────────────────────────────
print("\nT12 cat.call() and the here-gate")
random.random = lambda: 0.0
fresh_cat(DAY, location="garden", activity="watching")
r = cat.call("study", what="puss-puss")
check(bool(r) and ledger()[-1]["what"] == "puss-puss" and ledger()[-1]["heard"], f"cat.call(his_position, what): {r[:60]}")
fresh_cat(DAY, name="Ash", phase="companion", location="garden", activity="watching")
r = cat.call("study", what="Ash")
check(bool(r) and ledger()[-1]["by_name"], "...with her name: a call by name")
fresh_cat(DAY, location="garden", activity="watching")
r = cat.call("", what="puss-puss")
check(r is None and not ledger(), "an empty his_position is refused (fail-closed, like react)")
fresh_cat(DAY, location="garden", activity="watching")
r = cat.react("I stroke the cat.", "", "study")
check(r is None and not ledger(), "a tend thought while she is elsewhere is still nothing (the here-gate holds for every other hand)")
fresh_cat(DAY, location="garden", activity="watching")
r = cat.react("I call the cat.", "", "")
check(r is None and not ledger(), "a call with no location is refused")
random.random = _real_random

# ── T13 what must survive ───────────────────────────────────────────────────────────────────────────
print("\nT13 the hands that were already right")
fresh_cat(DAY, location="by_the_fire", activity="watching")
r = cat.react("I stroke the cat a while.", "", "study")
check(bool(r) and cat.state["last_tended"] == DAY and not ledger(), f"a stroke with her here is still a stroke: {r[:60]}")
fresh_cat(DAY, location="by_the_fire", activity="watching")
r = cat.react("Her name is Mist.", "", "study")
check(cat.state.get("name") == "Mist" and cat.state["phase"] == "companion" and not ledger(), "the naming latch still names (and is never a call)")
check(len(STUBS["discharge"]) > 0 and all(a[0] == "expression" for a in STUBS["discharge"]), "the call discharges as EXPRESSION (a voice costs the world nothing)")

# ── the live-store canary ────────────────────────────────────────────────────────────────────────────
print("\nlive-store canary")
FP_AFTER = _fingerprint()
leaks = sorted(n for n in set(FP_BEFORE) | set(FP_AFTER)
               if n not in _IGNORE and FP_BEFORE.get(n) != FP_AFTER.get(n))
check(not leaks, f"no live C:\\Nascence\\data top-level file changed during this run {leaks}")
for attr, mod, name in (("_STATE_F", cat, "cat_state"), ("_LEDGER", cat_call, "call ledger"), ("_LEDGER", cat_sounds, "sound ledger"),
                        ("_LEDGER", cat_ears, "reactions ledger"), ("_POS_F", locomotion, "position"), ("_LEDGER", cat_referent, "referent ledger")):
    check(str(getattr(mod, attr)).startswith(str(TMP)), f"{name} path still inside the temp dir")

print(f"\n{OKS} ok, {len(FAILS)} failed")
for f in FAILS:
    print("  FAILED:", f)
sys.exit(1 if FAILS else 0)
