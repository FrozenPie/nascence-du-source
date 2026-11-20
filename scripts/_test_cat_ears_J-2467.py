"""
Cat Overhaul C2 -- her ears (J-2467, D-0499, 2026-10-28)
=========================================================
HERMETIC: every store core/cat_ears.py and core/cat.py (and what their ticks reach) can write is redirected
into a tempfile.mkdtemp() dir OUTSIDE data/ before any write (the J-2465 / J-2466 harness pattern); every
cross-module writer the tick can reach is stubbed; the live C:\\Nascence\\data top-level files are
fingerprinted before and after and any change (bar arousal_shadow.jsonl / hud.err.log) is reported as a LEAK.
`import core` BEFORE anything else and core.__file__ must resolve under this worktree.

What it proves (simulated clock; the world's voices are a dict this script owns, so "what sounded" is exact):
  T1  fields and the quirk: ears / reaction on an old state; stranger_response rolled ONCE onto her existing
      quirks and kept; the other three quirks untouched; LIVE by default, the life_flags kill switch holds
  T2  the clock: heard_counts rolls only what life.sounds_active lists at HER place; a voice that rolled 0 is
      a bird that did not sound (no reaction, no row); at his place she consumes world_tick's own bank, once
  T3  birds through the glass: a shut house lets only the chorus and the alarm in; at the window / window
      open the blackbird's song puts her on the sill watching or chattering; the reaction HOLDS through the
      180 s roll; cat_sounds' cat_chatter still fires from HER state; a second sounding inside the cooldown
      is logged ignored, not re-acted
  T4  the garden: a sparrow row that sounded -> a real stalk; life.threat_active reads it (the alarm's gate)
  T5  the wood: the wren's scold -> she hunts there (bout hunt); her kills read what was actually there
      (prey_about from life's rows; nothing about = an honest miss, prey_about [] in the hunt ledger; a
      mouse present -> a mouse)
  T6  the dawn chorus: asleep indoors at dawn, door open -> up and out (a real leg); door shut -> asking out
      (cat_meow_at_door's hold); spent -> sleeps on
  T7  the mouse in the wall (HOOK keyed on "wall_scratch"): the moment it sounds at the study she sits at the
      skirting for about an hour; no skirting line says "mouse"
  T8  the gate latch: a bonded cat comes to the gate (ears.gate_ts stamped); the greeting then fires on his
      arrival inside the 20-minute clock; an old stamp (a restart) is not heard; the kettle and the door are
      never a cue; an unbonded stray only watches from the wall
  T9  the axe on the block: in the garden it sends her out; indoors it is ignored; wood_life.split and
      companion's split both carry the stamp
  T10 Travis: present flips on / an errand comes home -> hides / inspects / indifferent by the quirk; the
      first sight of the store never reacts
  T11 weather: hard wind -> in out of it (door open) / asking in (door shut); thunder -> storm_hide logged, the
      held reaction cleared
  T12 footsteps on the leg toward her place -> ears forward, no move
  T13 mid-leg: the gate re-aims her journey, never teleports her
  T14 the ledger: fenced path, every row's shape, rotation to .1 past the cap
  T15 D-0434 no readout: no digit in any new PRESENCE line; status() keys unchanged; cat_ears writes no prompt
      line; nothing in a prompt path reads cat_reactions.jsonl
Run:  python scripts/_test_cat_ears_J-2467.py   (from the worktree root)
"""
from __future__ import annotations

import json
import os
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

from core import cat, cat_ears, cat_sounds, cat_content, life, locomotion, sensorium, world_clock  # noqa: E402
from core import world_traces, life_traces, activity_memory, study_life, companion, wood_life, provisions, soundscape  # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="cat_ears_J2467_"))
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
from core import world_substrate, world_objects, cat_referent  # noqa: E402
world_substrate._SUBSTRATE_F = TMP / "world_substrate.json"
world_objects._OBJECTS_F = TMP / "world_objects.json"
cat_referent._LEDGER = TMP / "cat_referent_ledger.jsonl"
STUBS = {"activity": [], "carcass": [], "trace": [], "deed": []}
activity_memory.record = lambda *a, **k: STUBS["activity"].append(a)
life_traces.add_carcass = lambda *a, **k: STUBS["carcass"].append(a)
world_traces.create_trace = lambda *a, **k: STUBS["trace"].append(a)
life.note_deed = lambda *a, **k: STUBS["deed"].append(a)

# the world around her: a dict we own
SIM = {"now": 0.0, "door_open": True, "window_open": False, "season": "summer", "voices": {}, "act": {}}
sensorium.state = {"weather": "clear", "wind": "calm", "fire": "out", "location": "study", "asleep": False, "study": {}}
sensorium._daylight = lambda: world_clock.daylight(SIM["now"])
sensorium._season = lambda: SIM["season"]
study_life.door_open = lambda: SIM["door_open"]
study_life._st = lambda: {"door_open": SIM["door_open"], "window_open": SIM["window_open"]}
life.sounds_active = lambda place, now=None: list(SIM["voices"].get(place, []))
cat_sounds._birds_about = lambda: bool(SIM["voices"].get("garden"))
life._ensure_builtin()
_real_activity = life.activity
life.activity = lambda r, place, now=None: SIM["act"].get((r["key"], place), 0.0)

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
    cat_ears._mem.update({"last": 0.0, "journey_seen": 0.0})
    cat_sounds._mem.update({"last": 0.0, "act": None, "loc": None, "greet_ts": 0.0, "audible": {}, "holds_prev": {}, "last_fired": {}})
    st = {"phase": "companion", "name": "", "bond": 0.7, "location": "by_the_fire", "activity": "watching",
          "mood": "content", "appeared_ts": now - 100 * 86400, "last_fed": now - 3600, "last_seen": now,
          "quirks": {"storm_response": "under_desk", "greeting": "chirrup", "fair_spot": "windowsill"},
          "firsts": {"first_lap": 1.0, "first_slow_blink": 1.0, "first_silent_meow": 1.0, "first_shore_follow": 1.0, "first_play": 1.0},
          "last_tended": now, "last_greeted_ts": now - 7200, "arc": {}, "saucer": {"has_food": False, "kind": "", "set_ts": 0.0},
          "_was_in": True, "fur_moisture": 0.0, "last_fur_decay_ts": now, "last_bond_decay_ts": now,
          "body": {"hunger": 0.3, "thirst": 0.2, "energy": 0.7, "warmth": 0.5, "condition": 0.7, "bout": "active",
                   "bout_until": now + 1800, "bout_since": now, "last_ts": now, "last_drank_ts": 0.0, "cold_hours": 0.0, "last_meal": ""}}
    st.update(kw)
    cat._STATE_F.write_text(json.dumps(st), encoding="utf-8")
    return cat._load()


def ears_sample(now: float) -> list[dict]:
    cat_ears._mem["last"] = 0.0
    return cat_ears.tick(cat.state, now)


def ledger() -> list[dict]:
    try:
        return [json.loads(l) for l in cat_ears._LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()]
    except Exception:
        return []


def find_phase(want: str, start: float) -> float:
    t = start
    for _ in range(48 * 6):
        if world_clock.daylight(t) == want:
            return t
        t += 600
    raise RuntimeError(want)


def write_pos(**d):
    locomotion._POS_F.write_text(json.dumps(d), encoding="utf-8")


def write_travis(present: bool, errand: bool):
    companion._STATE_F.write_text(json.dumps({"present": present, "since_ts": 1.0, "errand": ({"for": "x"} if errand else None),
                                              "last_activity_ts": 1.0}), encoding="utf-8")


BASE = 1_800_000_000.0
DAY = find_phase("day", BASE)
NIGHT = find_phase("night", BASE)
DAWN = find_phase("dawn", BASE)
SIM["now"] = DAY
write_pos(place="study", standpoint="mid_room", journey=None, gate_ts=0.0)
write_travis(False, False)
cat_ears._poisson_lite = lambda rate, dt: 1          # "sounded" by default; T2 flips it to prove the zero case

# ── T1 fields + the quirk ───────────────────────────────────────────────────────────────────────────
print("\nT1 fields and the quirk")
st = fresh_cat(DAY)
check("ears" in st and st.get("reaction") is None, "an old state gains ears / reaction on load")
q = cat._quirks()
check(q.get("stranger_response") in ("hides", "inspects", "indifferent"), f"stranger_response rolled once onto her existing quirks: {q.get('stranger_response')}")
check(q["storm_response"] == "under_desk" and q["greeting"] == "chirrup" and q["fair_spot"] == "windowsill", "her existing quirks untouched")
first = q["stranger_response"]
cat.state = {}; cat._state_mtime = 0.0; cat._load()
check(cat._quirks()["stranger_response"] == first, "the roll is kept across a reload")
check(cat_ears.live_on() is True, "LIVE by code default")
(TMP / "life_flags.json").write_text(json.dumps({"cat_ears_live": False}), encoding="utf-8")
cat_ears._flags_cache["ts"] = 0.0
check(cat_ears.live_on() is False, "life_flags.json cat_ears_live=false switches her ears off (hot)")
SIM["voices"] = {"garden": ["blackbird_song"]}
cat.state["location"], cat.state["activity"] = "windowsill", "watching"
check(ears_sample(DAY) == [] and not ledger(), "off: no reaction, no row")
(TMP / "life_flags.json").unlink()
cat_ears._flags_cache["ts"] = 0.0
check(cat_ears.live_on() is True, "back on")

# ── T2 the clock ────────────────────────────────────────────────────────────────────────────────────
print("\nT2 the acoustic clock at her place")
SIM["voices"] = {"garden": ["blackbird_song", "small_birds"], "wood": ["wren_scold"], "study": []}
sensorium.state["location"] = "wood"                   # he is elsewhere: she rolls
counts, src = cat_ears.heard_counts("garden", 60.0, DAY, "wood")
check(src == "roll" and set(counts) == {"blackbird_song", "small_birds"}, f"rolls only the voices life lists at HER place: {counts}")
counts, src = cat_ears.heard_counts("study", 60.0, DAY, "wood")
check(counts == {}, "nothing voicing at the study: nothing heard")
cat_ears._poisson_lite = lambda rate, dt: 0
counts, src = cat_ears.heard_counts("garden", 60.0, DAY, "wood")
check(counts == {}, "a voice present that rolled 0 is a bird that did not sound")
st = fresh_cat(DAY, location="garden", activity="watching", bond=0.9)
rows = ears_sample(DAY)
check(st["activity"] == "watching" and not [r for r in rows if r["kind"] == "reaction"], "...and cannot be stalked at: no reaction")
cat_ears._poisson_lite = lambda rate, dt: 1
soundscape._bank_for_ears("garden", "blackbird_song", 3, DAY)
soundscape._bank_for_ears("garden", "small_birds", 2, DAY)
counts, src = cat_ears.heard_counts("garden", 60.0, DAY, "garden")
check(src == "bank" and counts == {"blackbird_song": 3, "small_birds": 2}, f"at his place she consumes world_tick's own bank: {counts}")
check(soundscape.consume_ear_bank("garden") == {}, "consumed once: the bank is empty after")
check(soundscape.consume_ear_bank("wood") is None, "a bank for another place is None (she rolls)")
check("blackbird_song" in cat_ears.bird_keys() and "small_birds" in cat_ears.bird_keys() and "wren_scold" in cat_ears.bird_keys()
      and "blackbird_alarm" in cat_ears.bird_keys() and "gull_cries" not in cat_ears.bird_keys(),
      f"the cast she listens for is derived from life's rows (eaten_by cat + the wren): {sorted(cat_ears.bird_keys())}")

# ── T3 birds through the glass ──────────────────────────────────────────────────────────────────────
print("\nT3 birds through the glass")
sensorium.state["location"] = "wood"                   # he is in the wood: her ears roll the garden for themselves
soundscape._EAR_BANK.update({"place": None, "counts": {}})
SIM["door_open"], SIM["window_open"] = False, False
SIM["voices"] = {"garden": ["blackbird_song"], "study": []}
st = fresh_cat(DAY, location="by_the_fire", activity="watching")
rows = ears_sample(DAY)
check(st["location"] == "by_the_fire" and not [r for r in rows if r["kind"] == "reaction"], "a shut house: the song does not reach the hearth")
SIM["window_open"] = True
cat_ears.CHATTER_P = 0.0
st = fresh_cat(DAY, location="by_the_fire", activity="watching")
rows = ears_sample(DAY)
check(st["location"] == "windowsill" and st["activity"] == "watching the birds" and st["reaction"]["cue"] == "blackbird_song",
      f"window open: the blackbird's song puts her on the sill watching the birds (hold {st['reaction']['until'] - DAY:.0f}s)")
r0 = [r for r in rows if r["kind"] == "reaction"][0]
check(r0["n"] >= 1 and r0["her_place"] == "study" and r0["before"]["loc"] == "by_the_fire", "the row: the count consumed, her place, where she was")
held_until = st["reaction"]["until"]
cat._last_tick = 0.0
for k in range(3):                                      # three 180 s rolls inside the shortest hold (10 min)
    cat._last_tick = 0.0
    cat.tick(DAY + 181 * (k + 1))
check(st["location"] == "windowsill" and st["activity"] == "watching the birds", "the reaction HOLDS through three 180 s rolls")
SIM["voices"] = {"garden": [], "study": []}            # the garden falls quiet
cat.tick(held_until + 400)
check(st.get("reaction") is None, "the hold expires and the bout machine resumes")
SIM["voices"] = {"garden": ["blackbird_song"], "study": []}
cat_ears.CHATTER_P = 1.0
st = fresh_cat(DAY, location="windowsill", activity="washing")
ears_sample(DAY)
check(st["activity"] == "chattering", "at the window already: a chatter")
keys = cat_sounds.emissions(st, DAY, 60.0)
check("cat_chatter" in keys, "cat_sounds' cat_chatter still fires from HER state (the voice is live)")
check(ears_sample(DAY + 120) == [], "while the reaction holds, the living voices are not sampled (no row-per-minute drone)")
st["reaction"] = None                                   # the hold over, the cooldown still running
rows = ears_sample(DAY + 181)
ign = [r for r in rows if r["kind"] == "ignored"]
check(ign and ign[0]["why"] == "cooldown" and st["activity"] == "chattering", "a second sounding inside the cooldown is logged ignored, not re-acted")
cat_ears.CHATTER_P = 0.3
SIM["window_open"] = False

# ── T4 the garden ───────────────────────────────────────────────────────────────────────────────────
print("\nT4 the garden")
SIM["voices"] = {"garden": ["small_birds"]}
st = fresh_cat(DAY, location="garden", activity="watching", _was_in=False)
rows = ears_sample(DAY)
check(st["activity"] == "stalking something" and st["location"] == "garden", "a sparrow row that sounded: a real stalk")
check(life.threat_active("cat", "garden") is True, "life.threat_active reads the stalk (the blackbird's alarm gate)")
st = fresh_cat(DAY, location="garden", activity="sleeping", _was_in=False)
rows = ears_sample(DAY)
check(st["activity"] == "sleeping" and [r for r in rows if r["kind"] == "ignored" and r["why"] == "asleep"], "asleep in the garden: ignored, logged")

# ── T5 the wood + real prey ─────────────────────────────────────────────────────────────────────────
print("\nT5 the wood: the wren, and kills that read what was there")
SIM["voices"] = {"wood": ["wren_scold"]}
st = fresh_cat(DAY, location="wood", activity="a grey shape between the trunks", _was_in=False)
rows = ears_sample(DAY)
check(st["activity"] == "hunting" and st["location"] == "wood" and st["body"]["bout"] == "hunt", "the wren's scold: she hunts there (bout hunt)")
SIM["act"] = {}
check(cat_ears.prey_about("wood", DAY) == [], "nothing present: prey_about is [] (an honest miss)")
SIM["act"] = {("mice", "wood"): 0.5, ("blackbird", "wood"): 0.3, ("wren", "wood"): 0.9}
pa = cat_ears.prey_about("wood", DAY)
check(sorted(pa) == ["bird", "mouse"], f"the mice and the blackbird are prey; the wren is not: {pa}")
cat._HUNT_LEDGER_F.unlink(missing_ok=True)
st = fresh_cat(DAY, location="wood", activity="hunting", last_fed=DAY - 12 * 3600, last_hunt_attempt_ts=0.0)
SIM["act"] = {}
_rr = random.random
random.random = lambda: 0.0
cat._maybe_self_feed(DAY)
random.random = _rr
hl = [json.loads(l) for l in cat._HUNT_LEDGER_F.read_text(encoding="utf-8").splitlines()]
check(hl and hl[-1]["caught"] is False and hl[-1]["prey_about"] == [] and hl[-1]["place"] == "wood" and st["activity"] == "hunting",
      f"a catch roll with nothing about is a miss: {hl[-1]}")
SIM["act"] = {("mice", "wood"): 0.5}
st["last_hunt_attempt_ts"] = 0.0
random.random = lambda: 0.0
cat._maybe_self_feed(DAY + 1)
random.random = _rr
hl = [json.loads(l) for l in cat._HUNT_LEDGER_F.read_text(encoding="utf-8").splitlines()]
check(hl[-1]["caught"] is True and hl[-1]["species"] == "mouse" and st["activity"] == "self_fed", f"a mouse present -> a mouse caught: {hl[-1]}")
SIM["act"] = {}

# ── T6 the dawn chorus ──────────────────────────────────────────────────────────────────────────────
print("\nT6 the dawn chorus")
SIM["now"] = DAWN
SIM["voices"] = {"garden": ["dawn_chorus", "blackbird_song"]}
SIM["door_open"] = True
st = fresh_cat(DAWN, location="by_the_fire", activity="sleeping")
rows = ears_sample(DAWN)
check(st["location"] == "in_transit" and st["transit"]["dest"]["activity"] == "up and out at first light", "door open: up and out, on her own legs")
SIM["door_open"] = False
st = fresh_cat(DAWN, location="by_the_fire", activity="sleeping")
rows = ears_sample(DAWN)
check(st["location"] == "indoors" and st["activity"] == "at the door, asking out", "door shut: asking out")
check("cat_meow_at_door" in cat_sounds.emissions(st, DAWN, 60.0), "...and cat_sounds' meow-at-the-door hold is meaningful for it")
st = fresh_cat(DAWN, location="by_the_fire", activity="sleeping", body={"hunger": 0.3, "thirst": 0.2, "energy": 0.1, "warmth": 0.5, "condition": 0.7,
                                                                    "bout": "sleep", "bout_until": DAWN + 3600, "bout_since": DAWN, "last_ts": DAWN})
rows = ears_sample(DAWN)
check(st["activity"] == "sleeping" and [r for r in rows if r["kind"] == "ignored" and "spent" in r["why"]], "spent: sleeps on, logged")
SIM["now"] = DAY
SIM["door_open"] = True

# ── T7 the mouse in the wall (hook) ─────────────────────────────────────────────────────────────────
print("\nT7 the mouse in the wall (hook keyed on wall_scratch)")
SIM["voices"] = {"study": ["wall_scratch"], "garden": []}
st = fresh_cat(DAY, location="by_the_fire", activity="washing")
rows = ears_sample(DAY)
hold = st["reaction"]["until"] - DAY if st.get("reaction") else 0
check(st["activity"] == "at the skirting, listening" and st["location"] == "indoors" and 50 * 60 <= hold <= 70 * 60,
      f"wall_scratch at the study: she sits at the skirting about an hour ({hold / 60:.0f} min)")
lines = set()
for _ in range(20):
    lines.add(cat.presence_line("study"))
check(all("mouse" not in l.lower() and "mice" not in l.lower() for l in lines) and len(lines) >= 3, f"the skirting lines rotate ({len(lines)} seen) and never say mouse")
SIM["voices"] = {"study": [], "garden": []}
check(ears_sample(DAY + 61) == [] or st["activity"] == "at the skirting, listening", "no key, no reaction (the hook is inert until the key sounds)")

# ── T8 the gate latch ───────────────────────────────────────────────────────────────────────────────
print("\nT8 the gate latch")
SIM["voices"] = {}
sensorium.state["location"] = "wood"
write_pos(place="wood", standpoint="on_the_path", journey=None, gate_ts=DAY - 5)
st = fresh_cat(DAY, location="garden", activity="washing", _was_in=False, last_seen=DAY - 60, last_greeted_ts=1.0)
rows = ears_sample(DAY)
check(st["location"] == "garden_wall" and st["activity"] == "waiting at the gate for you" and st["ears"]["gate_ts"] == DAY,
      "a bonded cat in the garden comes to the sound of the gate")
sensorium.state["location"] = "garden"
line = cat.presence_line("garden")   # presence_line reads the real clock: prev_seen is 60 s before DAY, far inside the 20-minute gap
check("chirrup" in line.lower() and st.get("reaction") is None and abs(st["last_greeted_ts"] - time.time()) < 5,
      f"the greeting fires on his arrival inside the 20-minute clock (she heard the gate): {line[:70]}...")
check(ears_sample(DAY + 61) == [], "the same stamp is never consumed twice")
write_pos(place="wood", standpoint="on_the_path", journey=None, gate_ts=DAY - 3600)
st = fresh_cat(DAY, location="garden", activity="washing", _was_in=False)
rows = ears_sample(DAY)
check(st["activity"] == "washing" and not rows, "an old stamp (a restart, a stopped stretch) is not heard now")
check({"kettle_sing", "kettle_fill", "kettle_pour", "door_sound"} <= cat_ears._MEANS_NOTHING, "the kettle and the door mean nothing to her (listed, never consumed)")
src = (ROOT / "core" / "cat_ears.py").read_text(encoding="utf-8")
check("door_ts" not in src and "kettle" not in src.replace("kettle_sing", "").replace("kettle_fill", "").replace("kettle_pour", "").replace("The kettle", "").replace("the kettle", ""),
      "no code path reads the kettle's or the door's stamps")
write_pos(place="wood", standpoint="on_the_path", journey=None, gate_ts=DAY - 5)
st = fresh_cat(DAY, phase="kept", bond=0.2, location="garden", activity="washing", _was_in=False)
rows = ears_sample(DAY)
check(st["location"] == "garden_wall" and st["activity"] == "watching" and st["mood"] == "wary", "an unbonded stray watches from the wall instead")
SIM["door_open"] = True
write_pos(place="wood", standpoint="on_the_path", journey=None, gate_ts=DAY - 5)
st = fresh_cat(DAY, location="by_the_fire", activity="washing")
rows = ears_sample(DAY)
check(st["location"] == "in_transit" and st["transit"]["dest"]["location"] == "garden_wall", "from the study she walks to the gate (a real leg)")
SIM["door_open"] = False
write_pos(place="wood", standpoint="on_the_path", journey=None, gate_ts=DAY - 5)
st = fresh_cat(DAY, location="by_the_fire", activity="sleeping")
rows = ears_sample(DAY)
check(st["activity"] == "sleeping" and [r for r in rows if r["kind"] == "ignored"], "asleep in a shut house: did not hear it")
SIM["door_open"] = True

# ── T9 the axe ──────────────────────────────────────────────────────────────────────────────────────
print("\nT9 the axe on the block")
d = wood_life._load(); d["last_split_ts"] = DAY - 3; wood_life._save(d)
write_pos(place="study", standpoint="mid_room", journey=None, gate_ts=0.0)
st = fresh_cat(DAY, location="garden", activity="washing", _was_in=False)
rows = ears_sample(DAY)
check(st["location"] == "away_hunting" and st["activity"].startswith("gone out of the garden"), "in the garden: the knocking sends her out")
check(cat.presence_line("garden") == "" and cat.presence_line("study") == "", "...and she is nowhere he can see")
d = wood_life._load(); d["last_split_ts"] = DAY + 50; wood_life._save(d)
st = fresh_cat(DAY + 60, location="by_the_fire", activity="washing")
rows = ears_sample(DAY + 60)
check(st["location"] == "by_the_fire" and [r for r in rows if r["kind"] == "ignored" and r["cue"] == "axe_on_block"], "indoors: ignored, logged")
wl_src = (ROOT / "core" / "wood_life.py").read_text(encoding="utf-8")
co_src = (ROOT / "core" / "companion.py").read_text(encoding="utf-8")
check('d["last_split_ts"] = time.time()' in wl_src and 'd["last_split_ts"] = time.time()' in co_src, "wood_life.split and companion's split both stamp last_split_ts")
d = wood_life._load(); d["last_split_ts"] = 0.0; wood_life._save(d)   # the block falls silent for the sections below

# ── T10 Travis ──────────────────────────────────────────────────────────────────────────────────────
print("\nT10 Travis")
sensorium.state["location"] = "study"
for quirk, want_loc, want_act in (("hides", "under_desk", "hiding from the visitor"), ("inspects", "indoors", "inspecting the visitor"),
                                  ("indifferent", "by_the_fire", "washing")):
    write_travis(False, False)
    st = fresh_cat(DAY, location="by_the_fire", activity="washing",
                   quirks={"storm_response": "under_desk", "greeting": "chirrup", "fair_spot": "windowsill", "stranger_response": quirk})
    rows = ears_sample(DAY)
    check(not rows, f"[{quirk}] first sight of the companion store: nothing to compare, no reaction")
    write_travis(True, False)
    rows = ears_sample(DAY + 61)
    rr = [r for r in rows if r["kind"] == "reaction"]
    check(st["location"] == want_loc and st["activity"] == want_act and rr and rr[0]["cue"] == "travis_arrives" and rr[0]["response"] == quirk,
          f"[{quirk}] Travis comes in -> {want_act}")
    write_travis(True, True)
    ears_sample(DAY + 122)
    write_travis(True, False)
    st["reaction"] = None; st["ears"]["last"]["travis"] = 0.0
    if quirk != "indifferent":
        st["location"], st["activity"] = "by_the_fire", "washing"
    rows = ears_sample(DAY + 183)
    rr = [r for r in rows if r["kind"] == "reaction"]
    check(rr and rr[0]["cue"] == "travis_returns" and st["activity"] == want_act, f"[{quirk}] an errand comes home -> the same answer")
write_travis(False, False)

# ── T11 weather ─────────────────────────────────────────────────────────────────────────────────────
print("\nT11 weather")
sensorium.state.update({"wind": "gale", "fire": "burning"})
SIM["door_open"] = True
st = fresh_cat(DAY, location="garden", activity="washing", _was_in=False)
rows = ears_sample(DAY)
check(st["location"] == "in_transit" and st["transit"]["dest"] == {"location": "by_the_fire", "activity": "in out of the wind", "mood": "ruffled"},
      "a gale, door open: in to the fire -- on her own legs (garden -> study is a leg under B1)")
SIM["door_open"] = False
st = fresh_cat(DAY, location="garden", activity="washing", _was_in=False)
rows = ears_sample(DAY)
check(st["location"] == "doorstep" and st["activity"] == "at the door, asking in", "a gale, door shut: asking in")
sensorium.state.update({"wind": "calm"})
sensorium.state["weather"] = "thunderstorm"
st = fresh_cat(DAY, location="windowsill", activity="chattering", reaction={"kind": "birds_sill", "cue": "blackbird_song", "since": DAY, "until": DAY + 1800})
cat._last_tick = 0.0
cat.tick(DAY + 1)
check(st["activity"] == "storm_hide" and st.get("reaction") is None, "thunder: storm_hide (the base branch), the held reaction cleared")
check([r for r in ledger() if r["cue"] == "thunder" and r["response"] == "under_desk"], "...and logged with the rest of her ears")
sensorium.state["weather"] = "clear"
SIM["door_open"] = True

# ── T12 footsteps ───────────────────────────────────────────────────────────────────────────────────
print("\nT12 footsteps on the leg toward her")
write_pos(place="study", standpoint="mid_room", gate_ts=0.0,
          journey={"from": "study", "path": ["garden"], "dest": "garden", "started": DAY - 10, "leg_ends": DAY + 200})
st = fresh_cat(DAY, location="garden", activity="washing", _was_in=False)
rows = ears_sample(DAY)
check(st["location"] == "garden" and st["activity"] == "listening, ears forward", "his steps on the path to the garden: ears forward, no move")
check(ears_sample(DAY + 61) == [], "one journey, one listen")
write_pos(place="study", standpoint="mid_room", journey=None, gate_ts=0.0)

# ── T13 mid-leg ─────────────────────────────────────────────────────────────────────────────────────
print("\nT13 mid-leg: a cue re-aims the journey, never teleports")
write_pos(place="wood", standpoint="on_the_path", journey=None, gate_ts=DAY - 5)
st = fresh_cat(DAY, location="in_transit", activity="on her way",
               transit={"from": "study", "to": "garden", "path": [], "started": DAY - 30, "leg_ends": DAY + 100,
                        "dest": {"location": "garden", "activity": "watching", "mood": ""}, "following": False, "balked": False, "origin": "by_the_fire"})
rows = ears_sample(DAY)
check(st["location"] == "in_transit" and st["transit"]["dest"]["location"] == "garden_wall" and st["transit"]["dest"]["activity"] == "waiting at the gate for you",
      "the latch mid-leg re-aims her leg at the gate; location stays in_transit")
write_pos(place="study", standpoint="mid_room", journey=None, gate_ts=0.0)

# ── T14 the ledger ──────────────────────────────────────────────────────────────────────────────────
print("\nT14 the ledger")
rows = ledger()
need = {"ts", "kind", "cue", "n", "her_place", "source", "his_place", "hearing", "her"}
check(rows and all(need <= set(r) for r in rows), f"{len(rows)} rows, every one carries {sorted(need)}")
check({r["kind"] for r in rows} == {"reaction", "ignored"}, f"kinds: {sorted({r['kind'] for r in rows})}")
check(all(r["n"] >= 1 for r in rows), "every row consumed at least one real occurrence (n >= 1)")
check(str(cat_ears._LEDGER).startswith(str(TMP)), "the ledger path is the isolated one (fenced through guard_path)")
cat_ears._ROTATE_BYTES = 10
cat_ears._log({"ts": 1, "kind": "x"})
check((TMP / "cat_reactions.jsonl.1").exists() and cat_ears._LEDGER.read_text(encoding="utf-8").count("\n") == 1, "past the cap the ledger rolls to .1 (one generation kept)")
cat_ears._ROTATE_BYTES = 2_000_000

# ── T15 D-0434 no readout ───────────────────────────────────────────────────────────────────────────
print("\nT15 no readout (D-0434)")
bad = []
for key in cat._EARS_KEYS.values():
    for cond, pool in cat_content.PRESENCE[key].items():
        for tpl in pool:
            s = tpl.replace("{her}", "the cat")
            if re.search(r"\d", s) or "{" in s or len(s) > 160:
                bad.append((key, s))
check(not bad, f"no digit, no unfilled token, <=160 chars in any new PRESENCE line ({sum(len(p) for k in cat._EARS_KEYS.values() for p in cat_content.PRESENCE[k].values())} lines)")
check(set(cat.status()) == {"phase", "name", "bond", "location", "activity"}, "cat.status() -- the one cat read in his prompt path -- keys unchanged")
check(all(w not in src for w in ("scene_line", "percept(", "pending_line", "_emit(", "presence_line(", "note_exposures")),
      "cat_ears writes no prompt line (no scene/percept/pending/emit/presence writer is called)")
readers = []
for p in sorted((ROOT / "core").glob("*.py")):
    txt = p.read_text(encoding="utf-8", errors="replace")
    if p.name not in ("cat_ears.py",) and "cat_reactions" in txt:
        readers.append(p.name)
check(not readers, f"no core module but cat_ears reads cat_reactions.jsonl {readers}")

# ── the live-store canary ────────────────────────────────────────────────────────────────────────────
print("\nlive-store canary")
FP_AFTER = _fingerprint()
leaks = sorted(n for n in set(FP_BEFORE) | set(FP_AFTER)
               if n not in _IGNORE and FP_BEFORE.get(n) != FP_AFTER.get(n))
check(not leaks, f"no live C:\\Nascence\\data top-level file changed during this run {leaks}")
for attr, mod, name in (("_STATE_F", cat, "cat_state"), ("_LEDGER", cat_ears, "reactions ledger"), ("_LEDGER", cat_sounds, "sound ledger"),
                        ("_POS_F", locomotion, "position"), ("_STATE_F", companion, "companion"), ("_F", wood_life, "wood_life")):
    check(str(getattr(mod, attr)).startswith(str(TMP)), f"{name} path still inside the temp dir")

print(f"\n{OKS} ok, {len(FAILS)} failed")
for f in FAILS:
    print("  FAILED:", f)
sys.exit(1 if FAILS else 0)
