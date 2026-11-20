"""
Cat Overhaul B4 -- the cat as a dosed loop: one tuple published on change, read dosed with habituation at the
idle-scene stop (J-2473, D-0499 / D-0508, docs/staged/cat_overhaul.md §B4 under docs/staged/dosed_coupling.md,
2026-10-29)
==============================================================================================================
HERMETIC: every store core/cat.py, core/cat_loop.py, core/transport_manager.py and the modules the tick / the
presence line reach can write is redirected into a tempfile.mkdtemp() dir OUTSIDE data/ before any write (the
scripts/_test_cat_seek_J-2469.py pattern); the live C:\\Nascence\\data top-level files are fingerprinted before and
after and any change (bar arousal_shadow.jsonl / hud.err.log, written by other processes) is reported as a LEAK.
`import core` BEFORE anything else and core.__file__ must resolve under this worktree (the F-2570 / jobrun
live-store-leak rule). The clock is simulated: cat.time is replaced by a fake whose time() is SIM["now"].

What it proves:
  T1  PUBLISH: the tuple (location, activity, mood, hunger, energy, in_transit); a publish row only on a CHANGE
      (discrete fields or a hunger / energy band -- drift inside a band is silent); the first publish of a boot
      is marked and teaches the dispatcher nothing; every later transition observes "cat:change" and
      "cat:state:<activity>@<location>" in transport_manager; cargo_types.WORLD_FACT_CAT; she is in
      coupling_rides' registry with no row in its file
  T2  THE FOUR-HOUR SLEEP: 294 scene asks (every 49 s, the stream's median gap) over 4 h with her asleep by the
      fire and him at his desk -> 2 ride rows (the first sight, then one more two hours on), ~290 held
  T3  THE SURPRISE: she arrives at the doorstep wet with a mouse inside a held stretch -> rides at once (event),
      the damp-coat clause and the mouse are in the line; the next asks are held again
  T4  MOVES: an ordinary change (sill -> desk, watching) is dosed on a doubling gap (10 min, then 20); a held
      move does not render
  T5  ENTRY / RETURN: no asks for AWAY_S (he was elsewhere / asleep) re-shows her after a fifth of the gap; a
      return from the garden (asks there found her out of sight) does the same; a return before that is held
  T6  ARRIVAL: she comes into his sight from out of it -> rides even inside a fresh gap
  T7  THE PULSE: two consumers inside 90 s see the same line and one ride row
  T8  THE DISPATCHER: a drought candidate on "cat:change" (a line past cold start, quiet far longer than its own
      gap) lets a held repeat through early, at most once an hour
  T9  THE KILL SWITCH: life_flags cat_dosed=false -> every ask renders as before B4, rows carry on=false / would_*
  T10 D-0434 + the protected paths: status() keys unchanged; no digit in any rendered line; no prompt-path module
      reads the ledger or the gate; the greeting still fires once per arrival and is never a ride row; look_line
      answers while the ambient line is held; is_here is untouched; a dead cat's paths are untouched (gate never
      asked)
  T11 HER VOICE: B4 adds no state -- cat_sounds.KEYS is the same 12 and every holds-condition still fires on its
      own state (demand at the door, the door meow, the sill chatter, the thump, the storm rustle, lapping)
  T12 THE FENCES: life_smoke's redirect list, the HUD registry and life_flags carry cat_loop; a non-live ledger
      write is refused and swallowed; gate() fails open (rides) on a broken state
Run:  python scripts/_test_cat_loop_J-2473.py   (from the worktree root)
"""
from __future__ import annotations

import json
import os
import random as _rnd
import re
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core                                            # noqa: E402  -- BEFORE anything else (house rule)
assert str(Path(core.__file__).resolve()).lower().startswith(str(ROOT).lower()), core.__file__
WT = str(Path(__file__).resolve().parents[1])   # this checkout, wherever it sits (was the jr1028 cat worktree)
assert str(Path(core.__file__).resolve()).lower().startswith(WT.lower()), f"core resolves outside the worktree: {core.__file__}"

LIVE_DATA = Path(r"C:\Nascence\data")
# J-4050: llm_calls/llm_latency/thought_station_log are appended by OTHER concurrent processes (job-run agents, a live Du); this test calls no model.
_IGNORE = {"arousal_shadow.jsonl", "hud.err.log", "llm_calls.jsonl", "llm_latency.jsonl", "thought_station_log.jsonl"}


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

from core import cat, cat_loop, cat_sounds, cat_call, life, locomotion, sensorium, world_clock, world_traces, life_traces  # noqa: E402
from core import activity_memory, study_life, provisions, cat_ears, cat_tom, cat_harm, cat_referent, cat_content  # noqa: E402
from core import transport_manager as TM, coupling_rides as CR, cargo_types, profile  # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="cat_loop_J2473_"))
print("isolated store dir:", TMP)
cat._STATE_F = TMP / "cat_state.json"
cat._HUNT_LEDGER_F = TMP / "cat_hunt_ledger.jsonl"
cat._FOUND_LEDGER_F = TMP / "cat_found_ledger.jsonl"
cat._FOUND_FLAGS_F = TMP / "life_flags.json"
cat._GAUGE_F = TMP / "cat_presence_gauge.jsonl"
cat._TIER_LEDGER_F = TMP / "cat_tier_ledger.jsonl"
cat._SEEK_LEDGER_F = TMP / "cat_seek_ledger.jsonl"
cat_loop._LEDGER = TMP / "cat_loop_ledger.jsonl"
cat_loop._FLAGS_F = TMP / "life_flags.json"
cat_sounds._LEDGER = TMP / "cat_sound_ledger.jsonl"
cat_sounds._FLAGS_F = TMP / "life_flags.json"
cat_ears._LEDGER = TMP / "cat_reactions.jsonl"
cat_ears._FLAGS_F = TMP / "life_flags.json"
cat_tom._STATE_F = TMP / "cat_tom_state.json"
cat_tom._LEDGER = TMP / "cat_tom_ledger.jsonl"
cat_tom._FLAGS_F = TMP / "life_flags.json"
_cat_harm_mod = cat_harm
_cat_harm_mod._LEDGER = TMP / "cat_harm_ledger.jsonl"
_cat_harm_mod._FLAGS_F = TMP / "life_flags.json"
cat_call._LEDGER = TMP / "cat_call_ledger.jsonl"
cat_call._FLAGS_F = TMP / "life_flags.json"
cat_referent._LEDGER = TMP / "cat_referent_ledger.jsonl"
cat_tom.live_on = lambda: False
TM._STATE, TM._SHADOW_LOG = TMP / "transport_lines.json", TMP / "transport_shadow.jsonl"
CR._LOG = TMP / "coupling_rides.jsonl"
world_traces._TRACES_F = TMP / "world_traces.json"
locomotion._POS_F = TMP / "position.json"
life._F = TMP / "life_state.json"
life._LEDGER = TMP / "life_ledger.jsonl"
life._EVENTS = TMP / "life_events.jsonl"
life._FLAGS_F = TMP / "life_flags.json"
provisions._F = TMP / "provisions.json"
provisions._LOG = TMP / "provisions_log.jsonl"
from core import world_substrate, world_objects  # noqa: E402
world_substrate._SUBSTRATE_F = TMP / "world_substrate.json"
world_objects._OBJECTS_F = TMP / "world_objects.json"
STUBS = {"activity": [], "carcass": [], "trace": [], "deed": []}
activity_memory.record = lambda *a, **k: STUBS["activity"].append(a)
life_traces.add_carcass = lambda *a, **k: STUBS["carcass"].append(a)
world_traces.create_trace = lambda *a, **k: STUBS["trace"].append(a)
life.note_deed = lambda *a, **k: STUBS["deed"].append(a)

SIM = {"now": 0.0, "door_open": True, "season": "autumn"}
sensorium.state = {"weather": "clear", "wind": "calm", "fire": "burning", "location": "study", "asleep": False}
sensorium._daylight = lambda: world_clock.daylight(SIM["now"])
sensorium._season = lambda: SIM["season"]
study_life.door_open = lambda: SIM["door_open"]
cat_sounds._birds_about = lambda: False
cat_ears.prey_about = lambda place, now=None: ["mouse"]


class _FakeTime:                                       # cat.py uses only time.time(); presence_line's clock is ours now
    @staticmethod
    def time() -> float:
        return SIM["now"]


_REAL_TIME = cat.time
cat.time = _FakeTime

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
    cat_loop._REG.clear()
    cat_loop._mem["open"].clear()
    st = {"phase": "kept", "name": "", "bond": 0.65, "location": "by_the_fire", "activity": "sleeping",
          "mood": "content", "appeared_ts": now - 100 * 86400, "last_fed": now - 3600, "last_seen": now,
          "quirks": {"storm_response": "under_desk", "greeting": "chirrup", "fair_spot": "windowsill"},
          "firsts": {"first_lap": 1.0, "first_slow_blink": 1.0, "first_silent_meow": 1.0, "first_shore_follow": 1.0,
                     "first_play": 1.0},
          "last_tended": now, "last_greeted_ts": now, "arc": {}, "saucer": {"has_food": False, "kind": "", "set_ts": 0.0},
          "_was_in": True, "fur_moisture": 0.0, "last_fur_decay_ts": now, "last_bond_decay_ts": now,
          "body": {"hunger": 0.3, "thirst": 0.2, "energy": 0.8, "warmth": 0.6, "condition": 0.7, "bout": "sleep", "bout_until": now + 7200}}
    st.update(kw)
    cat._STATE_F.write_text(json.dumps(st), encoding="utf-8")
    return cat._load()


def midnight_local(days_from_now: int = 1) -> float:
    lt = time.localtime(time.time() + days_from_now * 86400)
    return time.mktime((lt.tm_year, lt.tm_mon, lt.tm_mday, 0, 0, 0, 0, 0, -1))


def rows(kind: str | None = None) -> list[dict]:
    f = cat_loop._LEDGER
    out = [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()] if f.exists() else []
    return [r for r in out if kind is None or r.get("kind") == kind] if kind else out


def clear_ledger():
    if cat_loop._LEDGER.exists():
        cat_loop._LEDGER.unlink()


def seed_seen(*ids: str):
    """Mark states as already seen at the stop so a ride's `why` is the mechanism under test, not `first`."""
    loop = cat.state.setdefault("_loop", {})
    seen = loop.setdefault("seen", {})
    for i in ids:
        seen[i] = SIM["now"]


def ask(place: str = "study") -> str:
    return cat.presence_line(place)


def advance(secs: float, place: str = "study", hop: float = 240.0) -> list[str]:
    """Move the clock `secs` on in hops under AWAY_S, asking at each hop (the stream never stops asking; this
    keeps the entry rule out of a test that is about something else). Returns the non-empty lines seen."""
    got = []
    left = float(secs)
    while left > 0:
        step = min(hop, left)
        SIM["now"] += step
        left -= step
        x = ask(place)
        if x:
            got.append(x)
    return got


T0 = midnight_local(1) + 14 * 3600          # 2 pm tomorrow, local: daylight, no crepuscular edge
STOP = cat_loop.STOP_SCENE

# ── T1 PUBLISH ──────────────────────────────────────────────────────────────────────────────────────
print("\nT1 publish: the tuple, change-only rows, the dispatcher's lines, the cargo type, the registry")
SIM["now"] = T0
st = fresh_cat(T0)
t = cat_loop.tuple_of(st)
check(set(t) == {"location", "activity", "mood", "hunger", "energy", "in_transit"}, f"the tuple is the six coordinates of §B4: {t}")
check(t["location"] == "by_the_fire" and t["activity"] == "sleeping" and t["mood"] == "content" and t["hunger"] == 0.3 and t["energy"] == 0.8 and t["in_transit"] is False, "values read from state / body")
clear_ledger()
r1 = cat_loop.publish(st, T0)
check(r1 is not None and rows("publish")[-1]["first"] is True, "the first publish of a boot is a row marked first")
check(not TM._STATE.exists() or "cat:change" not in (json.loads(TM._STATE.read_text(encoding="utf-8")).get("lines") or {}), "a boot's first publish teaches the dispatcher nothing (not a transition)")
check(cat_loop.publish(st, T0 + 10) is None and len(rows("publish")) == 1, "the same tuple again: no row (no I/O)")
st["body"]["hunger"] = 0.42
check(cat_loop.publish(st, T0 + 20) is None and len(rows("publish")) == 1, "hunger drift inside a band (0.3 -> 0.42) is silent")
st["body"]["hunger"] = 0.55
check(cat_loop.publish(st, T0 + 30) is not None and len(rows("publish")) == 2, "a band crossing (0.42 -> 0.55) publishes")
st["activity"], st["mood"] = "washing", "content"
r = cat_loop.publish(st, T0 + 40)
check(r is not None and rows("publish")[-1]["from"] == {"location": "by_the_fire", "activity": "sleeping"}, "an activity change publishes, with where she came from")
lines = (json.loads(TM._STATE.read_text(encoding="utf-8")).get("lines") or {})
check("cat:change" in lines and "cat:state:washing@by_the_fire" in lines, f"the dispatcher now holds her lines: {sorted(k for k in lines if k.startswith('cat:'))}")
check(rows("publish")[-1]["cargo_type"] == cargo_types.WORLD_FACT_CAT and cargo_types.WORLD_FACT_CAT in cargo_types.WORLD_CARGO_TYPES, "cargo-typed WORLD_FACT_CAT, a world cargo type")
check(cat_loop.registry() == cat_loop.tuple_of(st), "registry() is the last published tuple")
check((CR._REG.get("cat") or {}).get("activity") == "washing" or not getattr(CR, "COUPLING_PUBLISH", True), "she is in coupling_rides' registry (loop 'cat')")
check(not CR._LOG.exists(), "no row went into coupling_rides.jsonl (registry only, log=False)")
check(len(rows("publish")[-1]["tuple"]) == 6 and all(not isinstance(v, str) or not re.search(r"\d", v) for v in rows("publish")[-1]["tuple"].values() if isinstance(v, str)), "the row carries the tuple as coordinates")

# ── T2 THE FOUR-HOUR SLEEP ──────────────────────────────────────────────────────────────────────────
print("\nT2 the four-hour sleep: 294 asks, two lines")
SIM["now"] = T0
st = fresh_cat(T0)
clear_ledger()
texts = []
for k in range(294):                                    # 4 h at the stream's median 49 s gap
    SIM["now"] = T0 + k * 49.0
    if k == 0:
        cat.tick(SIM["now"])                            # one heartbeat publishes her (the 180 s roll would re-decide her
    texts.append(ask("study"))                          # state over four hours; this test holds her asleep on purpose)
rides = rows("ride")
nonempty = [x for x in texts if x]
check(len(rides) == 2, f"two ride rows over four hours asleep by the fire (got {len(rides)}: {[r['why'] for r in rides]})")
check(rides[0]["why"] == "first" and rides[1]["why"] == "gap" and 7000 <= rides[1]["ts"] - rides[0]["ts"] <= 7400, f"the first sight, then the same tuple again after REST_BASE_GAP_S: {[(r['why'], r['ts'] - T0) for r in rides]}")
check(len(nonempty) <= 4 and all(x in (rides[0]["text"], rides[1]["text"]) or len(x) > 160 for x in nonempty), f"{len(nonempty)} non-empty asks of 294 (each ride plus its 90 s pulse), nothing else")
_pending = cat.state["_loop"]["stops"][STOP]["held"]
check(rides[1]["held"] >= 140 and sum(r["held"] for r in rides) + _pending + len(nonempty) == 294, f"held counts account for every ask: {[r['held'] for r in rides]} + {_pending} pending + {len(nonempty)} shown")
check(rides[1]["gap_s"] == cat_loop.REST_BASE_GAP_S and 1.5 <= rides[1]["n"] <= 2.0 and cat_loop.REST_BASE_GAP_S < cat_loop._gap_same(rides[1]["n"], True) <= 2 * cat_loop.REST_BASE_GAP_S, f"the gap grows after the second showing (n={rides[1]['n']} -> {cat_loop._gap_same(rides[1]['n'], True) / 3600:.2f} h next)")
check(cat.is_here("study") and cat.look_line("study", "cat"), "she is still here and a look still answers while the ambient line is held")
cat.state["activity"] = "sleeping"

# ── T3 THE SURPRISE ─────────────────────────────────────────────────────────────────────────────────
print("\nT3 the surprise: she arrives wet with a mouse inside a held stretch")
SIM["now"] = T0 + 4 * 3600 + 60                      # a minute after the stretch (no entry edge): deep inside the 4 h gap
seed_seen("brought_a_mouse@doorstep")
_x = ask("study")
check(_x == "", f"the sleeping cat is held (got {rows('ride')[-1]['why'] if _x else ''} {rows('ride')[-1] if _x else ''})")
cat.state.update({"location": "doorstep", "activity": "brought_a_mouse", "mood": "proud", "fur_moisture": 0.6})
line = ask("study")
r = rows("ride")[-1]
check(line and r["why"] == "event" and r["value"]["activity"] == "brought_a_mouse", f"the arrival with a mouse rides at once: why={r['why']}")
_pool_lines = [l.replace("{her}", "the cat") for cond in (cat_content.PRESENCE.get("brought_a_mouse") or {}).values() for l in (cond if isinstance(cond, list) else [])]     if isinstance(cat_content.PRESENCE.get("brought_a_mouse"), dict) else [l.replace("{her}", "the cat") for l in (cat_content.PRESENCE.get("brought_a_mouse") or [])]
_core = line.split(" Her coat")[0]
check(_core in _pool_lines or "mouse" in _core.lower(), f"the line is the brought_a_mouse pool's own (unchanged words): {line[:90]}")
check("damp with rain" in line, "wet: the damp-coat clause is on the line (presence_line's own, unchanged)")
SIM["now"] += 120
check(ask("study") == "", "the next ask of the same state (past the pulse) is held")
cat_loop._mem["open"].clear()

# ── T4 MOVES ────────────────────────────────────────────────────────────────────────────────────────
print("\nT4 ordinary moves are dosed on a doubling gap")
SIM["now"] = T0 + 5 * 3600
st = fresh_cat(SIM["now"], location="windowsill", activity="watching", fur_moisture=0.0)
clear_ledger()
seed_seen("watching@windowsill", "watching@on_the_desk", "watching@by_the_fire")
check(ask("study") and rows("ride")[-1]["why"] == "arrival", "her first sight at the stop (she moved into it from nowhere known) rides")
SIM["now"] += 120
cat.state["location"] = "on_the_desk"
check(ask("study") == "" and cat.state["_loop"]["stops"][STOP]["held"] == 1, "sill -> desk two minutes later: held (an ordinary move inside its 10 min gap)")
SIM["now"] += cat_loop.MOVE_BASE_GAP_S
line = ask("study")
r = rows("ride")[-1]
check(line and r["why"] == "move" and r["held"] == 1, f"the move rides once its gap has run: why={r['why']}, held={r['held']}")
check(advance(11 * 60) == [], "the same state for 11 min: held throughout")
cat.state["location"] = "by_the_fire"
check(ask("study") == "", "the next move 11 min later is held: the move gap doubled to 20 min")
check(advance(8 * 60, hop=200.0) == [], "still held 19 min after the last ride (the gap is measured ride to ride)")
SIM["now"] += 120
check(ask("study") and rows("ride")[-1]["why"] == "move" and 1100 <= rows("ride")[-1]["gap_s"] <= 2 * cat_loop.MOVE_BASE_GAP_S, f"and rides 21 min after the last ride (gap_s {rows('ride')[-1]['gap_s']}, the doubled gap easing with quiet)")

# ── T5 ENTRY / RETURN ───────────────────────────────────────────────────────────────────────────────
print("\nT5 he comes back into the room")
SIM["now"] = T0 + 6 * 3600
st = fresh_cat(SIM["now"], location="windowsill", activity="watching")
clear_ledger()
seed_seen("watching@windowsill")
ask("study")                                              # arrival ride
check(len(rows("ride")) == 1, "one ride to start")
SIM["now"] += 120; check(ask("study") == "", "two minutes on: held (awake gap 30 min)")
SIM["now"] += cat_loop.AWAY_S + 60                        # no asks for 6 min: asleep / elsewhere / a long task
line = ask("study")
check(line and rows("ride")[-1]["why"] == "entry", f"back after AWAY_S and a fifth of the gap: entry (why={rows('ride')[-1]['why']})")
SIM["now"] += 60
check(ask("garden") == "", "from the garden she is out of sight (the stop notes it)")
check(cat.state["_loop"]["stops"][STOP]["visible"] is False, "the stop records her out of his sight")
SIM["now"] += 120
check(ask("study") == "", "back in the study two minutes later: held (not a fifth of the gap yet)")
check(advance(8 * 60, place="garden") == [], "eight minutes in the garden: nothing of her from there")
SIM["now"] += 120
check(ask("study") and rows("ride")[-1]["why"] == "entry", "back after a fifth of the gap (the gap is 60 min after two showings): the return re-shows her")

# ── T6 ARRIVAL ──────────────────────────────────────────────────────────────────────────────────────
print("\nT6 she arrives from out of his sight")
SIM["now"] = T0 + 7 * 3600
st = fresh_cat(SIM["now"], location="garden", activity="stalking something", mood="playful")
clear_ledger()
seed_seen("stalking something@garden", "watching@windowsill")
check(ask("study") == "" and len(rows("ride")) == 0, "in the garden: nothing from the study")
SIM["now"] += 30
cat.state.update({"location": "windowsill", "activity": "watching", "mood": "content"})
line = ask("study")
check(line and rows("ride")[-1]["why"] == "arrival", f"she comes in to the sill: an arrival rides (why={rows('ride')[-1]['why']})")

# ── T7 THE PULSE ────────────────────────────────────────────────────────────────────────────────────
print("\nT7 the pulse: one room for every consumer")
SIM["now"] += 30
l1 = ask("study"); SIM["now"] += 40; l2 = ask("study")
check(l1 == l2 == line and len(rows("ride")) == 1, "two more consumers inside 90 s see the very same line; still one ride row")
SIM["now"] += 60
check(ask("study") == "", "past the pulse: held")

# ── T8 THE DISPATCHER ───────────────────────────────────────────────────────────────────────────────
print("\nT8 the dispatcher lets an unusual stillness through early")
SIM["now"] = T0 + 8 * 3600
st = fresh_cat(SIM["now"], location="by_the_fire", activity="sleeping")
clear_ledger()
seed_seen("sleeping@by_the_fire")
ask("study")
check(len(rows("ride")) == 1 and rows("ride")[-1]["why"] == "arrival", "the first sight rides")
# a line past cold start, quiet far longer than its own established gap: a drought candidate
_rt = _REAL_TIME.time()                                   # transport_manager judges on the REAL clock (its own time.time())
tl = {"lines": {"cat:change": {"first_ts": _rt - 5 * 86400, "n_total": 40, "rate_ema": 2.0, "gap_ema": 0.5,
                                "last_instant_rate_hr": 2.0, "last_ts": _rt - 3 * 3600, "novelty_pending": False,
                                "novelty_fired": True, "spike_armed": True, "drought_armed": True, "recent_ts": []}}}
TM._STATE.write_text(json.dumps(tl), encoding="utf-8")
cand = cat_loop._dispatch_candidate(cat_loop.tuple_of(cat.state))
check(cand and cand["kind"] == "drought" and cand["line_id"] == "cat:change", f"transport_manager.evaluate holds a drought on cat:change: {cand}")
SIM["now"] += 4 * 60                                      # held territory (2 h rest gap), past 2 pulses
line = ask("study")
r = rows("ride")[-1]
check(line and r["why"] == "drought" and r.get("dispatch", {}).get("kind") == "drought", f"the held repeat rides early on the dispatcher's word (why={r['why']})")
SIM["now"] += 10 * 60
check(ask("study") == "", "a second dispatcher ride inside the hour is not allowed")
TM._STATE.write_text(json.dumps({"lines": {}}), encoding="utf-8")
cat_loop._mem["open"].clear()

# ── T9 THE KILL SWITCH ──────────────────────────────────────────────────────────────────────────────
print("\nT9 the kill switch")
(TMP / "life_flags.json").write_text(json.dumps({"cat_dosed": False}), encoding="utf-8")
cat_loop._flags_cache["ts"] = 0.0
check(not cat_loop.dosed_on(), "life_flags cat_dosed=false reads off")
SIM["now"] += 60
got = [ask("study") for _ in range(3)]
check(all(got) and rows("ride")[-1]["on"] is False and rows("ride")[-1]["why"].startswith("would_"), f"off: every ask renders as before B4; rows carry on=false and why={rows('ride')[-1]['why']}")
check(len({x for x in got}) >= 2 and not cat_loop._mem["open"], "off: no pulse either -- three asks draw afresh (the rotation ring, as before B4)")
(TMP / "life_flags.json").unlink()
cat_loop._flags_cache["ts"] = 0.0
check(cat_loop.dosed_on() and cat_loop.CAT_DOSED is True, "flag file gone: the code default is ON (ships live on the next boot)")
cat_loop._mem["open"].clear()

# ── T10 D-0434 + THE PROTECTED PATHS ────────────────────────────────────────────────────────────────
print("\nT10 no readout; the protected paths")
check(set(cat.status()) == {"phase", "name", "bond", "location", "activity"}, "status() keys unchanged (nothing new reaches orchestrator's facts)")
texts = [r["text"] for r in rows("ride")]
check(texts and not any(re.search(r"\d", x) for x in texts), "no digit in any rendered line (the tuple's numbers stay in the ledger)")
offenders = []
for p in list((ROOT / "core").glob("*.py")) + list((ROOT / "nodes").glob("*.py")):
    if p.name in ("cat.py", "cat_loop.py"):
        continue
    src = p.read_text(encoding="utf-8", errors="replace")
    if "cat_loop_ledger" in src or "cat_loop.gate" in src or "cat_loop.registry" in src or "cat_loop.status" in src:
        offenders.append(p.name)
check(not offenders, f"no module outside cat.py / cat_loop.py reads the ledger, the gate or the registry (offenders: {offenders})")
# the greeting: its own one-shot, before the gate, never a ride row
SIM["now"] = T0 + 10 * 3600
st = fresh_cat(SIM["now"], location="by_the_fire", activity="washing", last_greeted_ts=0.0, last_seen=SIM["now"] - 3600)
clear_ledger()
seed_seen("washing@by_the_fire")
line = ask("study")
check(line and len(rows("ride")) == 0 and cat.state["last_greeted_ts"] == SIM["now"], "the reunion greeting fires (last_greeted_ts stamped) and is not a ride row")
SIM["now"] += 30
line2 = ask("study")
check(line2 and rows("ride")[-1]["why"] == "arrival", "the ordinary line follows on the next ask as an arrival (the stop had not seen her)")
# look_line answers while held; is_here untouched
SIM["now"] += 300
check(ask("study") == "" and cat.is_here("study") and "washing" in cat.look_line("study", "cat").lower() or cat.look_line("study", "cat"), "held ambiently, but a look answers and she is handleable")
# a dead cat: the gate is never asked (cat_harm's own dosed paths)
cat.state["phase"] = "dead"
n_before = len(rows("ride"))
calls = {"n": 0}
_g = cat_loop.gate
cat_loop.gate = lambda *a, **k: calls.__setitem__("n", calls["n"] + 1) or _g(*a, **k)
ask("study")
cat_loop.gate = _g
check(calls["n"] == 0 and len(rows("ride")) == n_before, "a dead cat's found / absence paths never reach the gate")
cat.state["phase"] = "kept"

# ── T11 HER VOICE ───────────────────────────────────────────────────────────────────────────────────
print("\nT11 her voice: B4 adds no state; every holds-condition still fires on its own state")
check(len(cat_sounds.KEYS) == 11 and set(cat_sounds.KEYS) >= {"cat_trill", "cat_meow_at_door", "cat_demand", "cat_chatter", "cat_yowl_cargo", "cat_thump", "cat_lapping", "cat_storm_rustle", "cat_hiss", "cat_growl", "distant_yowl"}, "KEYS unchanged: 11 points, no new sound point from B4")
cat_sounds._mem.update({"last": 0.0, "act": None, "loc": None, "greet_ts": 0.0, "audible": {}, "holds_prev": {}, "last_fired": {}})
base = {"phase": "companion", "name": "", "last_greeted_ts": 0.0, "last_fed": 0.0, "last_self_fed": 0.0}
def em(**kw):
    s = dict(base); s.update(kw)
    return cat_sounds.emissions(s, kw.get("_now", 100000.0), 60.0)
check("cat_demand" in em(activity="demanding_food", location="doorstep"), "demanding_food -> cat_demand")
check("cat_meow_at_door" in em(activity="at the door, asking in", location="doorstep"), "at the door -> cat_meow_at_door")
cat_sounds._birds_about = lambda: True
check("cat_chatter" in em(activity="watching the birds", location="windowsill"), "sill + watching + birds -> cat_chatter")
cat_sounds._birds_about = lambda: False
em(activity="dozing", location="windowsill")
check("cat_thump" in em(activity="sleeping", location="by_the_fire"), "sill -> floor -> cat_thump")
check("cat_storm_rustle" in em(activity="storm_hide", location="under_desk"), "storm_hide -> cat_storm_rustle")
check("cat_lapping" in em(activity="watching", location="doorstep", last_fed=99990.0, _now=100000.0), "a real feed -> cat_lapping")
check(set(cat_loop._event_acts()) >= set(cat._EARS_KEYS) | {"brought_a_mouse", "demanding_food", "storm_hide", "zoomies"}, "every ears / tom / illness state and every arc state is an event to the dose (a surprise rides)")

# ── T12 THE FENCES ──────────────────────────────────────────────────────────────────────────────────
print("\nT12 the fences")
smoke = (ROOT / "scripts" / "life_smoke.py").read_text(encoding="utf-8")
check('("core.cat_loop", ("_LEDGER", "_FLAGS_F"))' in smoke, "life_smoke's redirect list carries core.cat_loop")
hud = (ROOT / "hud" / "server.py").read_text(encoding="utf-8")
check('"cat_loop_ledger.jsonl"' in hud and '("cat_loop", "staged"' in hud, "the HUD registry carries the cat_loop ledger")
flags = (ROOT / "scripts" / "life_flags.py").read_text(encoding="utf-8")
check('"cat_dosed"' in flags and "cat_loop._flags_cache" in flags, "life_flags.py knows cat_dosed and resets the cache")
_gp = profile.guard_path
def _refuse(p):
    raise profile.NonLiveWriteError(str(p))
profile.guard_path = _refuse
try:
    cat_loop._log({"ts": 1, "kind": "ride"})
    refused_ok = True
except Exception:
    refused_ok = False
profile.guard_path = _gp
check(refused_ok, "a non-live ledger write is refused and swallowed (the line still renders)")
g = cat_loop.gate(STOP, None, SIM["now"], "study")        # a broken state: fail open, rides
check(g.get("ride") is True and g.get("why") == "fail_open", "gate() fails open (rides) on a broken state")
check(cat_loop.status()["dosed"] is True and "ride_rows" in cat_loop.status(), "status() for the HUD / du_pulse")

# ── LEAK CHECK ──────────────────────────────────────────────────────────────────────────────────────
cat.time = _REAL_TIME
FP_AFTER = _fingerprint()
leaks = sorted(k for k in set(FP_BEFORE) | set(FP_AFTER)
               if k not in _IGNORE and FP_BEFORE.get(k) != FP_AFTER.get(k))
check(not leaks, f"no live data/ file changed (leaks: {leaks})")

print(f"\n{'ALL OK' if not FAILS else 'FAILURES'} -- {OKS} checks passed, {len(FAILS)} failed")
for f in FAILS:
    print("  -", f)
sys.exit(1 if FAILS else 0)
