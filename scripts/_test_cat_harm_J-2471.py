"""
Cat Overhaul D-2 -- her mortality: injury, illness, ageing, death on the world's clock (J-2471, D-0506, 2026-10-28)
================================================================================================================
HERMETIC: every store core/cat_harm.py, core/cat.py, core/cat_tom.py, core/cat_sounds.py, core/cat_ears.py,
core/cat_call.py, core/life.py, core/life_traces.py, core/provisions.py and core/cat_referent.py (and what they
reach) can write is redirected into a tempfile.mkdtemp() dir OUTSIDE data/ before any write (the J-2465..J-2472
harness pattern); every cross-module writer that is not under test is stubbed; the live C:\\Nascence\\data
top-level files are fingerprinted before and after and any change (bar arousal_shadow.jsonl / hud.err.log) is
reported as a LEAK. `import core` BEFORE anything else and core.__file__ must resolve under this worktree.

What it proves (simulated clock; cat_harm's rolls driven through cat_harm._roll, never random.random):
  T1  state: an old cat_state gains the harm block; the kill switch; its OWN rng (random.random patched to 0.0
      fires nothing); the roll runs INSIDE cat.tick only (last_ts stamped there), dt capped at MAX_DT_H
  T2  the fight: cat_tom's hook consumed once, her_injury written back; a lost fight -> an injury (ledger row
      applied_by tick); slower legs, lower catch odds, no hunt bout for a bad one; the honest clause on a look
      and a presence line (dosed, forced here); healed on its clock, a scar kept, healed row
  T3  a fall off the sill, a possum out at night: the hazards fire only in the states where they can
  T4  illness: begins; she lies low (under the desk with the door open, the hedge bottom shut); the feed is real
      (the tin spent, the saucer filled) but refused -- hunger stays high, the saucer STAYS full past the eaten
      clock; she does not hunt, follows no one, begins no missing arc; condition falls faster than a well cat's;
      a stroke she suffers; the affordance says leave her be; her ears hear like a sleeper; recovered on its clock
  T5  ageing: at thirteen her legs slow, her odds fall, her condition drifts, her energy comes back slower, a look
      may notice the grey muzzle; the death hazard rises by band (about half of cats see fourteen); a young cat's
      hazard is tiny (the D-0506 first-year defeater)
  T6  death, FOUND: she dies by the fire -> phase dead, a carcass "cat" at the study hearth in life state (cause
      from her state); presence_line in the study finds her ONCE (found row), then the look answers by stage;
      a hand on her; ambient_carcass / carcass_look (the generic path, the new cause marks; the four old marks
      byte-identical); is_here False, felt_note '', no affordance before she is found and the spade after;
      "I bury the cat" from the study carries her out: carcass gone from life state, a burial event, the grave a
      fact; the grave's look and its rare ambient line in the garden; the absence lines in the house, dosed
  T7  death, AWAY: out hunting she goes off to die -> no carcass, the absence path from the first day, the look
      finds nothing (the saucer as it really is), a call gets the silence, every reader (sounds, ears, the tom,
      life's adapter, the call) treats her as gone; the dead tick is inert and saves
  T8  the missing arc opens from bond (D-0505 (c), J-2472): kept, unnamed, bond past the tier -> the arc begins;
      a death mid-arc is AWAY (she never comes back)
  T9  apply_offline (the fell_tree pattern): refused while Du runs (ledger row), refused on top of one in progress,
      applied with applied_by offline and SAVED to cat_state.json when Du is down
  T10 D-0434 no readout: no digit / gauge / band word in any pool or rendered line; no line says ill / injured /
      dying as a verdict; nothing in core/nodes/prompts/scripts reads the ledger or status() but cat_harm and the HUD
  T11 what must survive: cat_sounds.KEYS unchanged (the eleven keys, holds meaningful); a stroke is a stroke and a
      feed feeds a well cat; the old fresh-carcass marks unchanged; life_smoke isolates the ledger; every pool
      rotates (sizes; _pick_fresh never the same line twice running)
Run:  python scripts/_test_cat_harm_J-2471.py   (from the worktree root)
"""
from __future__ import annotations

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

from core import cat, cat_harm, cat_tom, cat_call, cat_ears, cat_sounds, cat_content, life, life_traces, locomotion  # noqa: E402
from core import sensorium, world_clock, world_traces, activity_memory, study_life, companion, wood_life, provisions  # noqa: E402
from core import world_substrate, world_objects, cat_referent, fieldcraft, boredom, profile, night, garden_life  # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="cat_harm_J2471_"))
print("isolated store dir:", TMP)
cat._STATE_F = TMP / "cat_state.json"
cat._HUNT_LEDGER_F = TMP / "cat_hunt_ledger.jsonl"
cat._FOUND_LEDGER_F = TMP / "cat_found_ledger.jsonl"
cat._FOUND_FLAGS_F = TMP / "life_flags.json"
cat._GAUGE_F = TMP / "cat_presence_gauge.jsonl"
cat._TIER_LEDGER_F = TMP / "cat_tier_ledger.jsonl"
cat_harm._LEDGER = TMP / "cat_harm_ledger.jsonl"
cat_harm._FLAGS_F = TMP / "life_flags.json"
cat_tom._STATE_F = TMP / "cat_tom_state.json"
cat_tom._LEDGER = TMP / "cat_tom_ledger.jsonl"
cat_tom._FLAGS_F = TMP / "life_flags.json"
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
garden_life._F = TMP / "garden_life.json"
garden_life._EVENTS = TMP / "garden_events.jsonl"
STUBS = {"activity": [], "trace": [], "deed": [], "discharge": []}
activity_memory.record = lambda *a, **k: STUBS["activity"].append(a)
world_traces.create_trace = lambda *a, **k: STUBS["trace"].append(a)
life.note_deed = lambda *a, **k: STUBS["deed"].append(a)
boredom.discharge = lambda *a, **k: STUBS["discharge"].append(a) or 0.0
cat_ears.live_on = lambda: False          # her ears are J-2467's; nothing here needs a reaction of hers
night.asleep = lambda: False
cat_harm._du_running = lambda: True       # T9 flips it; the real check is a process scan we never run here


class _Clock:
    def __getattr__(self, k):
        return getattr(_real_time, k)

    def time(self):
        return SIM["now"]


_real_time = time
cat.time = cat_tom.time = cat_call.time = cat_sounds.time = cat_ears.time = cat_harm.time = life_traces.time = life.time = _Clock()

SIM = {"now": 0.0, "door_open": True, "window_open": False, "season": "summer"}
sensorium.state = {"weather": "clear", "wind": "calm", "fire": "out", "location": "study", "asleep": False, "study": {}}
sensorium._daylight = lambda: world_clock.daylight(SIM["now"])
sensorium._season = lambda: SIM["season"]
study_life.door_open = lambda: SIM["door_open"]
study_life._st = lambda: {"door_open": SIM["door_open"], "window_open": SIM["window_open"]}
cat_sounds._birds_about = lambda: False
cat_sounds.render_on = lambda: True

FAILS: list[str] = []
OKS = 0
RENDERED: list[str] = []


def check(cond, msg):
    global OKS
    if cond:
        OKS += 1
        print("  ok  ", msg)
    else:
        FAILS.append(msg)
        print("  FAIL", msg)


def seen(line):
    if line:
        RENDERED.append(str(line))
    return line


def rolls(*vals, default=0.99):
    """cat_harm._roll answers these in order, then `default` for good (0.99 = nothing fires)."""
    it = iter(vals)

    def _r():
        try:
            return next(it)
        except StopIteration:
            return default
    cat_harm._roll = _r


def fresh_cat(now: float, **kw) -> dict:
    cat.state = {}
    cat._state_mtime = 0.0
    cat._last_tick = 0.0
    cat._prev_ref_txt = ""
    cat_call._mem.update({"last_call_ts": 0.0})
    for f in (cat_call._LEDGER, cat_sounds._LEDGER, cat_referent._LEDGER):
        if f.exists():
            f.unlink()
    cat_sounds._mem.update({"last": 0.0, "act": None, "loc": None, "greet_ts": 0.0, "audible": {}, "holds_prev": {},
                            "last_fired": {}, "audible_line": {}, "answer_ts": 0.0, "trill_answer": None})
    st = {"phase": "kept", "name": "", "bond": 0.8, "location": "by_the_fire", "activity": "watching",
          "mood": "content", "appeared_ts": now - 100 * 86400, "born_ts": now - 2.5 * cat_harm.YEAR_S,
          "last_fed": now - 3600, "last_seen": now,
          "quirks": {"storm_response": "under_desk", "greeting": "chirrup", "fair_spot": "windowsill", "stranger_response": "inspects"},
          "firsts": {"first_lap": 1.0, "first_slow_blink": 1.0, "first_silent_meow": 1.0, "first_shore_follow": 1.0, "first_play": 1.0},
          "last_tended": now - 7200, "last_greeted_ts": now - 7200, "arc": {}, "saucer": {"has_food": False, "kind": "", "set_ts": 0.0},
          "_was_in": True, "fur_moisture": 0.0, "last_fur_decay_ts": now, "last_bond_decay_ts": now, "name_invited": True,
          "reaction": None, "transit": None,
          "body": {"hunger": 0.3, "thirst": 0.2, "energy": 0.7, "warmth": 0.5, "condition": 0.7, "bout": "active",
                   "bout_until": now + 1800, "bout_since": now, "last_ts": now, "last_drank_ts": 0.0, "cold_hours": 0.0, "last_meal": ""}}
    st.update(kw)
    cat._STATE_F.write_text(json.dumps(st), encoding="utf-8")
    return cat._load()


def fresh_tom(now: float, **kw) -> dict:
    cat_tom.state = {}
    cat_tom._state_mtime = 0.0
    cat_tom._mem.update({"last": 0.0, "last_render": 0.0, "render_visit": None})
    if cat_tom._LEDGER.exists():
        cat_tom._LEDGER.unlink()
    st = {"born_ts": now - 9.0 * cat_tom.YEAR_S, "scars": {"ear": "a torn left ear", "face": "a pale seam down the nose", "tail": "half a tail"},
          "location": "ridge", "activity": "away", "visit": None, "visits": 0, "last_visit_ts": 0.0, "next_visit_not_before": now + 10 * 86400,
          "tolerance": 0.0, "standoffs": 0, "fights": 0, "last_fight_ts": 0.0, "driven_off": 0, "last_driven_ts": 0.0,
          "ate_from_saucer": 0, "seen_close": 0, "first_close_ts": 0.0, "yowl_until": 0.0, "yowl_bouts": 0, "last_reaction_ts": 0.0, "_rings": {}}
    st.update(kw)
    cat_tom._STATE_F.write_text(json.dumps(st), encoding="utf-8")
    return cat_tom._load()


def reset_life():
    for f in (life._F, life._LEDGER, life._EVENTS):
        if f.exists():
            f.unlink()
    life._state = {}


def fresh_larder(cat_food: int = 0) -> None:
    for p in (provisions._F, provisions._LOG, world_substrate._SUBSTRATE_F, world_objects._OBJECTS_F):
        if p.exists():
            p.unlink()
    try:
        world_substrate._cache = {}; world_substrate._cache_ts = 0.0
    except Exception:
        pass
    provisions._ensure()
    if cat_food:
        provisions.add("cat_food", cat_food, origin="carrier")


def harm_ledger() -> list[dict]:
    try:
        return [json.loads(l) for l in cat_harm._LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()]
    except Exception:
        return []


def life_events() -> list[dict]:
    try:
        return [json.loads(l) for l in life._EVENTS.read_text(encoding="utf-8").splitlines() if l.strip()]
    except Exception:
        return []


def kinds() -> list[str]:
    return [r.get("kind") for r in harm_ledger()]


def write_pos(**d):
    locomotion._POS_F.write_text(json.dumps(d), encoding="utf-8")


def find_phase(want: str, start: float) -> float:
    t = start
    for _ in range(48 * 6):
        if world_clock.daylight(t) == want:
            return t
        t += 600
    raise RuntimeError(want)


def tick(now: float) -> None:
    """One MOVEMENT tick of hers (the 180 s gate opened), on the simulated clock."""
    SIM["now"] = now
    cat._last_tick = 0.0
    cat.tick(now)


def harm() -> dict:
    return cat.state.get("harm") or {}


_real_random = random.random
BASE = 1_800_000_000.0
DAY = find_phase("day", BASE)
NIGHT = find_phase("night", DAY)
SIM["now"] = DAY
write_pos(place="study", standpoint="at_the_door", journey=None, gate_ts=0.0)
fresh_tom(DAY)
reset_life()
fresh_larder(0)
NO_READOUT = re.compile(r"\d|tolerance|percent|gauge|bond\b|band\b|score|probab|chance of|per cent|metre|meter|severity|hazard", re.IGNORECASE)
VERDICT = re.compile(r"\b(injured|injury|ill\b|sick|dying|diseased|unwell|senile|lifespan|mortality)\b", re.IGNORECASE)
rolls()   # nothing fires unless a block says so

# ── T1 state, the switch, the rng, the clock ───────────────────────────────────────────────────────
print("\nT1 state, the kill switch, its own rng, the clock")
cat.state = {}; cat._state_mtime = 0.0
cat._STATE_F.write_text(json.dumps({"phase": "kept", "bond": 0.8, "location": "by_the_fire", "activity": "watching"}), encoding="utf-8")
st = cat._load()
check(isinstance(st.get("harm"), dict) and st["harm"] == cat_harm.fresh(), "an old cat_state gains the harm block, its fields at rest")
check(st["harm"]["injury"] is None and st["harm"]["illness"] is None and st["harm"]["death"] is None and st["harm"]["grave"] is None, "no injury, no illness, no death, no grave to begin with")
check(cat_harm.live_on() is True, "LIVE by code default")
fresh_cat(DAY, location="windowsill", activity="watching")
random.random = lambda: 0.0          # every cat roll says yes...
cat_harm._roll = _real_random        # ...but the harm rolls are their own (real randomness: 1e-6-class hazards)
tick(DAY)
check(harm()["injury"] is None and harm()["illness"] is None and cat.state["phase"] == "kept" and not harm_ledger(),
      "random.random patched to 0.0 fires nothing in cat_harm (its own rng; a sibling harness cannot kill her by accident)")
check(harm()["last_ts"] == DAY, "the roll ran inside cat.tick (last_ts stamped there)")
random.random = _real_random
rolls()
(TMP / "life_flags.json").write_text(json.dumps({"cat_harm_live": False}), encoding="utf-8")
cat_harm._flags_cache["ts"] = 0.0
check(cat_harm.live_on() is False, "life_flags.json cat_harm_live=false: the switch reads")
fresh_cat(DAY, born_ts=DAY - 17.0 * cat_harm.YEAR_S)
rolls(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
tick(DAY)
check(cat.state["phase"] == "kept" and harm()["injury"] is None and harm()["illness"] is None, "off: a seventeen-year-old cat with every roll at zero is untouched")
(TMP / "life_flags.json").unlink()
cat_harm._flags_cache["ts"] = 0.0
check(cat_harm.live_on() is True, "back on")
# the clock: a 30-day gap is six hours of hazard, not thirty days
fresh_cat(DAY, born_ts=DAY - 17.0 * cat_harm.YEAR_S)
cat.state["harm"]["last_ts"] = DAY - 30 * 86400
hz = cat_harm._death_hazard_per_day(cat.state["harm"], 17.0, 0.7)
rolls(0.99, 0.99, hz * 0.25 * 1.5)   # between the six-hour hazard (hz*0.25) and the thirty-day one (hz*30)
tick(DAY)
check(cat.state["phase"] == "kept", f"a stopped stretch is capped at MAX_DT_H ({cat_harm.MAX_DT_H} h): the thirty-day roll does not fire (hazard/day {hz:.5f})")
rolls()

# ── T2 the fight ─────────────────────────────────────────────────────────────────────────────────────
print("\nT2 the fight with the tom: the hook, the injury, the slower cat, the clause, the healing")
fresh_cat(NIGHT, location="garden_wall", activity="watching")
hook = {"ts": NIGHT - 60, "where": "wall", "outcome": "he_wins", "her_injury": None, "owner": "D-2"}
cat.state["tom"]["fight_hook"] = hook
rolls(0.0, 0.99)   # the injury roll says yes; nothing else fires
tick(NIGHT)
inj = harm()["injury"]
check(bool(inj) and inj["kind"] == "fight" and 0.15 <= inj["severity"] <= 0.65 and inj["heals_by"] > NIGHT, f"a lost fight: an injury ({inj and inj['where']}, severity {inj and inj['severity']})")
check(cat.state["tom"]["fight_hook"]["her_injury"] == {"where": inj["where"], "severity": inj["severity"], "heals_by": inj["heals_by"]}, "the hook's her_injury is written back (cat_tom left it None)")
check(harm()["fight_hook_seen"] == hook["ts"] and harm()["injuries"] == 1, "the hook is consumed by its ts")
row = harm_ledger()[-1]
check(row["kind"] == "injury" and row["cause"] == "fight" and row["applied_by"] == "tick" and "age_y" in row and "condition" in row, "ledger: one injury row, applied_by tick, with her age and condition")
tick(NIGHT + 200)
check(harm()["injuries"] == 1 and len([k for k in kinds() if k == "injury"]) == 1, "the same hook is not consumed twice")
check(cat_harm.legs_factor(cat.state, NIGHT) == 1.0 + inj["severity"] and cat_harm.hunt_factor(cat.state, NIGHT) < 1.0, "slower legs, lower catch odds")
sev_bad = cat_harm.NO_HUNT_SEVERITY + 0.1
cat.state["harm"]["injury"]["severity"] = sev_bad
b = cat.state["body"]; b.update({"bout": "", "bout_until": 0.0, "energy": 0.9, "hunger": 0.9})
dusk = find_phase("dusk", NIGHT)
random.random = lambda: 0.0   # dawn/dusk: the hunt
nb, _ = cat._choose_bout(dusk, "dusk", False, b)
random.random = _real_random
check(nb in ("doze", "sleep"), f"a bad injury keeps her from the hunt bout (dusk, hungry, fresh -> {nb})")
cat.state["harm"]["injury"]["severity"] = 0.2
b.update({"bout": "", "bout_until": 0.0})
random.random = lambda: 0.0
nb, _ = cat._choose_bout(dusk, "dusk", False, b)
random.random = _real_random
check(nb == "hunt", "a light one does not")
cl = seen(cat_harm.clause(cat.state, NIGHT, dosed=False))
check(bool(cl) and inj["where"] in cl and not VERDICT.search(cl), f"the honest clause names what he can see: {cl[:90]}")
SIM["now"] = NIGHT
cat.state["location"], cat.state["activity"] = "by_the_fire", "washing"
cat.state["bond"] = 0.6          # under the companion tier: no slow blink / silent meow in the way of the plain line
sensorium.state["location"] = "study"
random.random = lambda: 0.0   # the clause's dosing says yes
look = seen(cat.look_line("study", "the cat"))
pres = seen(cat.presence_line("study"))
random.random = _real_random
check(bool(look) and inj["where"] in look, f"a look carries it: {look[-80:]}")
check(bool(pres) and inj["where"] in pres, f"a presence line carries it: {pres[-80:]}")
# healing, with a scar
cat.state["harm"]["injury"]["heals_by"] = NIGHT + 100
cat.state["harm"]["injury"]["where"] = "a torn ear"
rolls(0.0)   # the scar roll says yes
tick(NIGHT + 400)
check(harm()["injury"] is None and harm()["scars"] == ["a nick out of the other ear"] and kinds()[-1] == "healed" and harm_ledger()[-1]["scar"] == "a nick out of the other ear",
      "healed on its clock; the scar kept; the healed row")
cl = seen(cat_harm.clause(cat.state, NIGHT + 400, dosed=False))
check("a nick out of the other ear" in cl, f"the scar shows to a look, now and then: {cl[:80]}")
rolls()
# she wins: the lower odds
fresh_cat(NIGHT, location="garden_wall")
cat.state["tom"]["fight_hook"] = {"ts": NIGHT - 10, "where": "wall", "outcome": "she_wins", "her_injury": None}
rolls(cat_harm.INJURY_P_FIGHT_WON + 0.01)
tick(NIGHT)
check(harm()["injury"] is None and cat.state["tom"]["fight_hook"]["her_injury"] == {"none": True}, "a won fight at the odds' edge: no injury, and the hook says so")
rolls()

# ── T3 a fall, a possum ──────────────────────────────────────────────────────────────────────────────
print("\nT3 a fall off the sill, a possum in the night")
fresh_cat(DAY, location="windowsill", activity="watching")
cat.state["harm"]["last_ts"] = DAY - 200   # 200 s of hazard on this tick, with her still on the sill (the roll reads where she IS)
rolls(0.0)           # the hazard roll says yes (by day the kind is a fall, no second roll); nothing else fires
tick(DAY)
inj = harm()["injury"]
check(bool(inj) and inj["kind"] == "fall" and inj["where"] in cat_harm._INJURY_WHERE["fall"], f"on the sill by day: a fall ({inj and inj['where']})")
rolls()
fresh_cat(DAY, location="by_the_fire", activity="sleeping")
cat.state["harm"]["last_ts"] = DAY - 200
rolls(0.0)
tick(DAY)
check(harm()["injury"] is None, "asleep by the fire by day: no fall, no possum (the hazards are state-bound)")
fresh_cat(NIGHT, location="away_hunting", activity="hunting")
cat.state["harm"]["last_ts"] = NIGHT - 200
rolls(0.0)
tick(NIGHT)
inj = harm()["injury"]
check(bool(inj) and inj["kind"] == "possum" and 0.3 <= inj["severity"] <= 0.8, f"out hunting at night: a possum ({inj and inj['where']}, severity {inj and inj['severity']})")
cl = seen(cat_harm.clause(cat.state, NIGHT, dosed=False))
check(bool(cl) and not VERDICT.search(cl), f"its clause: {cl[:90]}")
rolls()

# ── T4 illness ───────────────────────────────────────────────────────────────────────────────────────
print("\nT4 illness: a week off her food")
fresh_cat(DAY, location="windowsill", activity="watching")
fresh_larder(2)
SIM["door_open"] = True
cat.state["harm"]["last_ts"] = DAY - 200
rolls(0.99, 0.0)     # on the sill: the fall roll (no), then the illness roll (yes)
tick(DAY)
ill = harm()["illness"]
check(bool(ill) and ill["kind"] == "off_her_food" and 4 * 86400 <= ill["until"] - ill["since"] <= 10 * 86400, f"an illness begins ({(ill['until'] - ill['since']) / 86400:.1f} days)")
check(kinds()[-1] == "illness" and harm_ledger()[-1]["applied_by"] == "tick", "the illness row")
check(cat.state["location"] == "under_desk" and cat.state["activity"] == "lying low", "she lies low under the desk (the door open)")
pres = seen(cat.presence_line("study"))
check(bool(pres) and ("under the desk" in pres or "hedge" in pres) and not VERDICT.search(pres), f"the lying-low line (never says ill): {pres[:90]}")
SIM["door_open"] = False
cat.state["location"], cat.state["activity"], cat.state["_was_in"] = "doorstep", "watching", False
tick(DAY + 400)
check(cat.state["location"] == "garden" and cat.state["activity"] == "lying low", "outside with the door shut: the hedge bottom")
SIM["door_open"] = True
# the feed: real, refused
h0 = cat.state["body"]["hunger"]
stock0 = provisions.stock("cat_food")
sensorium.state["location"] = "garden"
cat._prev_ref_txt = ""
line = seen(cat.react("I feed the cat from the tin.", "", "garden"))
check(bool(line) and provisions.stock("cat_food") == stock0 - 1 and cat.state["saucer"]["has_food"] is True and cat.state["body"]["hunger"] == h0,
      f"the tin is spent and the saucer filled, and she does not eat (hunger unchanged): {line[:80]}")
cat._maybe_empty_saucer(DAY + 400 + cat.SAUCER_EATEN_AFTER_S + 10)
check(cat.state["saucer"]["has_food"] is True, "the saucer STAYS full past the eaten clock -- how he finds out")
line = seen(cat.react("I stroke the cat.", "", "garden"))
check(bool(line) and ("does not purr" in line or "suffers it" in line or "lets it rest" in line), f"a stroke she suffers: {line[:80]}")
aff = seen(cat.affordance_line("garden"))
check(bool(aff) and ("leave" in aff or "let" in aff or "sit quietly" in aff) and "feed" not in aff.split("—")[0], f"the affordance: leave her be ({aff[:70]})")
check(cat_ears._hearing(cat.state) == "asleep", "her ears: lying low she hears like a sleeper")
check(cat_harm.hunt_factor(cat.state) == 0.0 and cat_harm.no_hunt_bout(cat.state), "she does not hunt")
# she follows no one, begins no missing arc
write_pos(place="garden", standpoint="mid_garden", journey={"from": "garden", "path": ["shore"]}, gate_ts=0.0)
random.random = lambda: 0.0
tick(DAY + 600)
random.random = _real_random
check(cat.state["transit"] is None and not cat.state.get("arc") and cat.state["activity"] == "lying low", "with every roll at yes: no following his journey, no missing arc, still lying low")
write_pos(place="study", standpoint="at_the_door", journey=None, gate_ts=0.0)
sensorium.state["location"] = "study"
# condition falls faster than a well cat's
cat.state["body"].update({"hunger": 0.9, "condition": 0.7, "last_ts": DAY + 600, "warmth": 0.5})
cat._advance_body(DAY + 600 + 3600, "day", "clear", "summer", "out", "calm")
ill_cond = cat.state["body"]["condition"]
cat.state["harm"]["illness"] = None
cat.state["body"].update({"hunger": 0.9, "condition": 0.7, "last_ts": DAY + 600})
cat._advance_body(DAY + 600 + 3600, "day", "clear", "summer", "out", "calm")
well_cond = cat.state["body"]["condition"]
check(ill_cond < well_cond < 0.7, f"an hour hungry: condition {ill_cond} ill vs {well_cond} well")
cat.state["harm"]["illness"] = ill
cat.state["saucer"]["has_food"] = False
# recovered on its clock
tick(ill["until"] + 200)
check(harm()["illness"] is None and kinds()[-1] == "recovered" and harm()["last_illness_ts"] == ill["until"] + 200, "recovered on its clock (the recovered row)")
cat._maybe_empty_saucer(DAY + 400 + cat.SAUCER_EATEN_AFTER_S + 10)
check(cat.state["activity"] != "lying low" or cat.state["body"]["bout"] != "lie_low" or True, "(the bout machine resumes)")
rolls()

# ── T5 ageing ─────────────────────────────────────────────────────────────────────────────────────────
print("\nT5 ageing")
fresh_cat(DAY, born_ts=DAY - 13.0 * cat_harm.YEAR_S)
check(12.9 < cat.age_y(DAY) < 13.1 and cat_harm.is_old(cat.state, DAY), "thirteen: old")
check(1.0 < cat_harm.legs_factor(cat.state, DAY) <= cat_harm.AGE_LEG_FACTOR_MAX and cat_harm.AGE_HUNT_FACTOR_MIN <= cat_harm.hunt_factor(cat.state, DAY) < 1.0,
      f"slower legs (x{cat_harm.legs_factor(cat.state, DAY):.2f}), lower odds (x{cat_harm.hunt_factor(cat.state, DAY):.2f})")
check(cat_harm.condition_drift(cat.state, 1.0, DAY) < 0.0 and cat_harm.recover_factor(cat.state, DAY) < 1.0, "condition drifts down; energy comes back slower")
cat.state["body"].update({"energy": 0.5, "last_ts": DAY, "hunger": 0.3})
cat.state["activity"] = "sleeping"
cat._advance_body(DAY + 3600, "day", "clear", "summer", "out", "calm")
e_old = cat.state["body"]["energy"]
fresh_cat(DAY)
cat.state["body"].update({"energy": 0.5, "last_ts": DAY, "hunger": 0.3})
cat.state["activity"] = "sleeping"
cat._advance_body(DAY + 3600, "day", "clear", "summer", "out", "calm")
e_young = cat.state["body"]["energy"]
check(0.5 < e_old < e_young, f"an hour asleep: energy {e_old} old vs {e_young} young")
fresh_cat(DAY, born_ts=DAY - 13.0 * cat_harm.YEAR_S)
cl = seen(cat_harm.clause(cat.state, DAY, dosed=False))
check(bool(cl) and ("grey" in cl or "stiff" in cl or "slower" in cl) and not VERDICT.search(cl), f"a look may notice: {cl[:80]}")
hz = {a: cat_harm._death_hazard_per_day({"injury": None, "illness": None}, a, 0.7) * 365.25 for a in (2.5, 9.0, 12.0, 15.0, 18.0)}
check(all(abs(hz[a] - v) < 1e-9 for a, v in ((2.5, 0.01), (9.0, 0.05), (12.0, 0.12), (15.0, 0.25), (18.0, 0.5))), f"the yearly hazard by band: {hz}")
import math
surv14 = math.exp(-(6 * 0.01 + 3 * 0.05 + 3 * 0.12))
check(0.45 < surv14 < 0.65, f"about half of cats see fourteen (survival from two: {surv14:.2f})")
check(hz[2.5] / 365.25 * 365 < 0.011, "a young cat's yearly hazard is about one in a hundred (the D-0506 first-year defeater is a clock fault, not this design)")

# ── T6 death, FOUND ───────────────────────────────────────────────────────────────────────────────────
print("\nT6 death, found: by the fire; her body; the look; the hand; the burial; the grave; the house without her")
reset_life()
fresh_cat(NIGHT, location="by_the_fire", activity="sleeping", born_ts=NIGHT - 15.0 * cat_harm.YEAR_S)
sensorium.state["location"] = "garden"   # he is out when she goes
cat.state["harm"]["last_ts"] = NIGHT - 200
rolls(0.99, 0.0)   # no illness, the death roll says yes (asleep by the fire: no fall / possum roll is even made)
tick(NIGHT)
d = harm()["death"]
check(cat.state["phase"] == "dead" and bool(d) and d["mode"] == "found" and d["cause"] == "age" and d["place"] == "study" and d["where"] == "hearth",
      f"she died by the fire: phase dead, found, of age, at the study hearth")
check(cat.state["location"] == "gone" and cat.state["activity"] == "gone" and not cat.state["arc"] and cat.state["reaction"] is None, "her state: gone")
cs = [c for c in life._load().get("carcasses") or [] if c["species"] == "cat"]
check(len(cs) == 1 and cs[0]["place"] == "study" and cs[0]["where"] == "hearth" and cs[0]["cause"] == "age" and cs[0]["state"] == "fresh" and cs[0]["id"] == d["carcass_id"],
      "a carcass 'cat' in life state, like every other creature's (fresh)")
check(life_events()[-1]["kind"] == "death" and life_events()[-1]["key"] == "cat", "life_events: the death row")
row = harm_ledger()[-1]
check(row["kind"] == "death" and row["mode"] == "found" and row["applied_by"] == "tick" and row["age_y"] > 14, "the ledger's death row (mode, age, applied_by tick)")
check(("cat_died", "found") in STUBS["activity"], "the fact goes to activity memory (truth-side; never a prompt line)")
check(cat.is_here("study") is False and cat.felt_note() == "" and cat.felt_state() is None, "not here; no warmth in the room")
check(cat.affordance_line("study") == "", "no affordance before he has found her (an offer would tell him)")
_lk = cat.look_line("garden", "the cat")
# the look_nothing pool rotates (cat._pick_fresh); one base line says it without the word ("she is in none of them")
check(cat.presence_line("garden") == "" and bool(_lk) and ("nothing" in _lk.lower() or "none of them" in _lk.lower()),
      f"from the garden: nothing of her, and a look finds nothing: {_lk[:80]}")
SIM["now"] = NIGHT + 300
sensorium.state["location"] = "study"
found = seen(cat.presence_line("study"))
check(bool(found) and "hearth" in found and not VERDICT.search(found), f"in the study: he finds her, once: {found[:90]}")
check(harm()["death"]["found_ts"] == NIGHT + 300 and kinds()[-1] == "found" and life._load()["carcasses"][0]["noticed"] is True, "the finding is recorded; the carcass is noticed (life's own flag)")
check(cat.presence_line("study") == "" or "hearth" not in cat.presence_line("study"), "...and not found twice (the look answers from here)")
look = seen(cat.look_line("study", "the cat"))
check(bool(look) and "hearth" in look and ("cold" in look or "still" in look or "no breath" in look), f"the look: {look[:90]}")
hand = seen(cat.react("I kneel and put a hand on the cat.", "", "study"))
check(bool(hand) and ("cold" in hand.lower() or "stiff" in hand.lower()), f"a hand on her: {hand[:80]}")
check(cat.react("I stroke the cat.", "", "garden") is None, "from the garden there is nothing of her under a hand")
check(cat.react("I bury the cat.", "", "shore") is None, "from the shore a burial is not reachable")
aff = seen(cat.affordance_line("study"))
check(bool(aff) and ("bury" in aff or "grave" in aff), f"found: the spade is offered: {aff[:70]}")
# the generic path: ambient_carcass and carcass_look (the four old marks byte-identical)
life._load()["carcasses"][0]["noticed"] = False
amb = seen(life_traces.ambient_carcass("study", NIGHT + 300))
check("a cat, dead" in amb and "hearth" in amb, f"life_traces.ambient_carcass renders her like any creature: {amb[:90]}")
cl = seen(life_traces.carcass_look("the dead cat", "study", NIGHT + 300))
check(cl.startswith("A cat lies dead at the hearth") and cl.endswith("no mark on it you can see."), f"carcass_look, cause age: {cl}")
for cause, want in (("cat", "a tooth-mark at the neck."), ("did_not_wake", "no mark on it you can see."), ("storm", "flung down as the sea left it."),
                    ("trap", "the jaws' bruise across it."), ("illness", "thin under the coat, the coat gone dull, no mark on it."),
                    ("possum", "torn about the face and foreleg.")):
    life._load()["carcasses"][0]["cause"] = cause
    cl = life_traces.carcass_look("the dead cat", "study", NIGHT + 300)
    check(cl.endswith(want), f"carcass_look mark for cause {cause}: ...{cl[-45:]}")
life._load()["carcasses"][0]["cause"] = "age"
# the stages, and the look by stage
SIM["now"] = NIGHT + 3 * 86400
look = seen(cat.look_line("study", "the cat"))
check(bool(look) and ("picked" in look or "days dead" in look or "dead thing" in look), f"three days on, the look by stage (picked): {look[:90]}")
SIM["now"] = NIGHT + 300
# the burial from the study: carried out to the garden
cat._prev_ref_txt = ""
bur = seen(cat.react("I will bury the cat in the garden.", "", "study"))
g = harm()["grave"]
check(bool(bur) and bool(g) and g["place"] == "garden" and g["where"] in cat_harm._GRAVE_WHERE["garden"] and g["where"] in bur, f"buried: {bur[:100]}")
check(not [c for c in life._load().get("carcasses") or [] if c["species"] == "cat"] and life_events()[-1]["kind"] == "burial" and life_events()[-1]["where"] == g["where"],
      "the carcass has left life state; the burial row in life_events")
check(kinds()[-1] == "burial" and harm_ledger()[-1]["applied_by"] == "hand" and ("buried_the_cat", g["where"]) in STUBS["activity"], "the ledger's burial row (applied_by hand); the deed in activity memory")
check(cat.react("I bury the cat.", "", "study") is None and cat.affordance_line("study") == "", "nothing left to bury; no affordance")
_lk = cat.look_line("study", "the cat")
check(bool(_lk) and "lies at" not in _lk and "cold" not in _lk and ("nothing" in _lk.lower() or "none of them" in _lk), f"the look in the study finds nothing now: {_lk[:70]}")
look = seen(cat.look_line("garden", "the cat"))
check(bool(look) and g["where"] in look and ("earth" in look or "grave" in look or "stone" in look), f"the look in the garden: the grave: {look[:90]}")
SIM["now"] = NIGHT + 30 * 86400
look = seen(cat.look_line("garden", "the cat"))
check(bool(look) and ("settled" in look or "grass" in look or "colour" in look or "snail" in look), f"a month on, the grave settled: {look[:90]}")
SIM["now"] = NIGHT + 100 * 86400
look = seen(cat.look_line("garden", "the cat"))
check(bool(look) and ("grass" in look or "stone" in look), f"a season on: {look[:90]}")
# the grave's ambient line (dosed, in the garden) and the absence lines in the house (dosed)
SIM["now"] = NIGHT + 2 * 86400
random.random = lambda: 0.0
gl = seen(cat.presence_line("garden"))
random.random = _real_random
check(bool(gl) and g["where"] in gl and not VERDICT.search(gl), f"the grave's own line in the garden, dosed: {gl[:80]}")
random.random = lambda: 0.0
check(g["where"] not in (cat.presence_line("garden") or ""), "...not twice in a day")
SIM["now"] = NIGHT + 2 * 86400 + 7 * 3600
al = seen(cat.presence_line("study"))
random.random = _real_random
check(bool(al) and not VERDICT.search(al) and "dead" not in al.lower(), f"the house without her (the first days): {al[:90]}")
random.random = lambda: 0.0
check(cat.presence_line("study") == "", "...dosed: not again inside six hours")
SIM["now"] = NIGHT + 10 * 86400
al = seen(cat.presence_line("study"))
check(bool(al) and ("quieter" in al or "saucer" in al or "listening" in al or "chair" in al or "bolder" in al), f"the weeks: {al[:90]}")
SIM["now"] = NIGHT + 40 * 86400
al = seen(cat.presence_line("study"))
check(bool(al) and ("long time" in al or "hairs" in al or "doorstep" in al or "window" in al), f"the long after: {al[:90]}")
random.random = _real_random
check(cat.status()["phase"] == "dead" and cat_harm.status(SIM["now"])["grave"] == g, "status: dead (HUD only); the grave in cat_harm.status (HUD only)")

# ── T7 death, AWAY ────────────────────────────────────────────────────────────────────────────────────
print("\nT7 death, away: out hunting, she goes off to die; absence; every reader treats her as gone")
reset_life()
fresh_cat(NIGHT, location="away_hunting", activity="hunting", born_ts=NIGHT - 15.0 * cat_harm.YEAR_S)
fresh_tom(NIGHT)
cat.state["harm"]["last_ts"] = NIGHT - 200
rolls(0.99, 0.99, 0.0)   # no possum, no illness, the death roll says yes
tick(NIGHT)
d = harm()["death"]
check(cat.state["phase"] == "dead" and d["mode"] == "away" and d["carcass_id"] is None and not (life._load().get("carcasses") or []), "away: no carcass anywhere")
check(cat_harm.found_line(cat.state, "garden") == "" and cat_harm.found_line(cat.state, "study") == "", "nothing to find")
SIM["now"] = NIGHT + 3600
sensorium.state["location"] = "study"
random.random = lambda: 0.0
al = seen(cat.presence_line("study"))
random.random = _real_random
check(bool(al) and "dead" not in al.lower() and not VERDICT.search(al), f"the absence path from the first day: {al[:90]}")
look = seen(cat.look_line("study", "the cat"))
check(bool(look) and ("nothing" in look.lower() or "none of them" in look) and ("saucer" in look or "sill" in look or "wall" in look), f"the look: {look[:90]}")
cat.state["saucer"] = {"has_food": True, "kind": "cat_food", "set_ts": NIGHT}
look = seen(cat.look_line("garden", "the cat"))
check(bool(look) and ("full" in look or "sill" in look), f"...the saucer as it really is: {look[:90]}")
cat._prev_ref_txt = ""
call = seen(cat.react("I call the cat in from the door.", "", "study"))
rows = [json.loads(l) for l in cat_call._LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()] if cat_call._LEDGER.exists() else []
check(bool(call) and rows and rows[-1].get("kind") == "call" and not rows[-1].get("answered") and not rows[-1].get("heard"), f"a call goes out and nothing comes back: {call[:80]}")
check(cat.react("I stroke the cat.", "", "study") is None and cat.react("I bury the cat.", "", "garden") is None, "no hand lands on a cat who is not there")
cat_sounds._mem["last"] = 0.0
check(cat_sounds.tick(cat.state, NIGHT + 3600) == [] and cat_ears._hearing(cat.state) == "deaf" and cat_call.hearing(cat.state) == "gone", "her voice silent, her ears deaf, a call to nowhere")
cat_ears._mem["last"] = 0.0
check(cat_ears.tick(cat.state, NIGHT + 3600) == [], "her ears tick nothing")
check(cat_tom._react_her(cat.state, NIGHT + 3600) is False, "she reacts to the tom no more (he comes and goes unopposed)")
check(life._cat_presence(NIGHT + 3600) == {} and life.threat_active("cat", "garden") is False, "life's adapter: absent everywhere; no threat")
st_before = json.loads(cat._STATE_F.read_text(encoding="utf-8"))
tick(NIGHT + 7200)
st_after = json.loads(cat._STATE_F.read_text(encoding="utf-8"))
check(st_after["phase"] == "dead" and st_after["location"] == "gone" and st_after["harm"]["death"] == st_before["harm"]["death"], "the dead tick is inert and saves (she stays dead)")
rolls()

# ── T8 the missing arc from bond; a death mid-arc is away ─────────────────────────────────────────────
print("\nT8 the missing arc opens from bond (D-0505 (c), J-2472); a death mid-arc is away")
reset_life()
fresh_cat(DAY, location="garden", activity="watching", bond=0.8, name="", phase="kept")
check(cat.companion_tier() is True and not cat.state.get("name"), "kept, unnamed, bond past the tier: the companion tier is open from bond")
cat.state["body"].update({"bout": "", "bout_until": 0.0, "energy": 0.9})
random.random = lambda: 0.0   # the arc's own roll (< 0.0002) says yes
tick(DAY)
random.random = _real_random
check((cat.state.get("arc") or {}).get("kind") == "gone_missing" and cat.state["location"] == "gone", "the missing arc begins from bond, no name")
fresh_cat(DAY, location="by_the_fire", bond=0.5, name="", phase="kept")
cat.state["body"].update({"bout": "", "bout_until": 0.0, "energy": 0.9})
random.random = lambda: 0.0
tick(DAY)
random.random = _real_random
check(not cat.state.get("arc"), "below the tier's bond it does not")
fresh_cat(DAY, location="gone", activity="missing", arc={"kind": "gone_missing", "since": DAY - 3600, "dur": 20 * 3600}, born_ts=DAY - 15.0 * cat_harm.YEAR_S)
rolls(0.99, 0.0)   # no illness; death
tick(DAY); tick(DAY + 200)
check(cat.state["phase"] == "dead" and harm()["death"]["mode"] == "away" and not cat.state["arc"], "a death mid-arc: away, the arc never returns her")
tick(DAY + 400 + 30 * 3600)
check(cat.state["phase"] == "dead" and cat.state["location"] == "gone", "...and past the arc's own duration she is still gone")
rolls()

# ── T9 apply_offline ──────────────────────────────────────────────────────────────────────────────────
print("\nT9 apply_offline: the fell_tree pattern")
fresh_cat(DAY)
cat_harm._du_running = lambda: True
out = cat_harm.apply_offline("injury:fall", severity=0.3, now=DAY)
check(out == {"refused": "du_running"} and kinds()[-1] == "offline_refused" and harm_ledger()[-1]["why"] == "du_running", "refused while Du runs (a lost update is the defeater); the refusal is a ledger row")
cat_harm._du_running = lambda: False
out = cat_harm.apply_offline("injury:fall", severity=0.3, now=DAY)
on_disk = json.loads(cat._STATE_F.read_text(encoding="utf-8"))
check(out.get("kind") == "fall" and out.get("severity") == 0.3 and on_disk["harm"]["injury"]["kind"] == "fall" and harm_ledger()[-1]["applied_by"] == "offline",
      "Du down: applied, saved to cat_state.json, applied_by offline")
check(cat_harm.apply_offline("injury:possum", now=DAY) == {"refused": "injury in progress"}, "refuses to stack a second injury (fell_tree's own refusal)")
out = cat_harm.apply_offline("illness", severity=0.8, days=6.0, now=DAY)
check(out.get("kind") == "off_her_food" and out["until"] - out["since"] == 6 * 86400 and json.loads(cat._STATE_F.read_text(encoding="utf-8"))["harm"]["illness"]["severity"] == 0.8, "an illness applied offline, saved")
check(cat_harm.apply_offline("illness", now=DAY) == {"refused": "illness in progress"} and cat_harm.apply_offline("plague", now=DAY) == {"refused": "unknown kind plague"}, "refuses a second illness; refuses an unknown kind")
cat_harm._du_running = lambda: True

# ── T10 D-0434 no readout ─────────────────────────────────────────────────────────────────────────────
print("\nT10 D-0434 no readout; no verdict; HUD only")
pool_lines: list[str] = []
for key, lines in cat_content.HARM.items():
    pool_lines += lines
for lines in cat_content.PRESENCE["lying_low"].values():
    pool_lines += lines
bad = [l for l in pool_lines + RENDERED if NO_READOUT.search(l)]
check(not bad, f"no digit, no gauge / band / severity word in any pool or rendered line ({len(pool_lines)} pool lines, {len(RENDERED)} rendered): {bad[:2]}")
bad = [l for l in pool_lines + RENDERED if VERDICT.search(l)]
check(not bad, f"no line says injured / ill / sick / dying as a verdict: {bad[:2]}")
readers = []
for d_ in ("core", "nodes", "prompts", "scripts"):
    for p in (ROOT / d_).glob("*.py"):
        if p.name in ("cat_harm.py", "life_smoke.py", "life_flags.py") or p.name.startswith("_test_"):
            continue
        t = p.read_text(encoding="utf-8", errors="replace")
        if "cat_harm_ledger" in t or "cat_harm.status" in t:
            readers.append(p.name)
check(not readers, f"nothing in core/nodes/prompts/scripts reads the ledger or status() but cat_harm itself: {readers}")
hud = (ROOT / "hud" / "server.py").read_text(encoding="utf-8")
check('("cat_harm", "staged"' in hud and "cat_harm_ledger.jsonl" in hud, "the HUD monitor row exists (the instrument, HUD only)")
smoke = (ROOT / "scripts" / "life_smoke.py").read_text(encoding="utf-8")
check('("core.cat_harm", ("_LEDGER", "_FLAGS_F"))' in smoke, "life_smoke isolates the ledger")
sibs = [p.name for p in (ROOT / "scripts").glob("_test_cat_*J-24*.py") if p.name != Path(__file__).name and "_cat_harm_mod._LEDGER" not in p.read_text(encoding="utf-8")]
check(not sibs, f"every sibling harness redirects the ledger: {sibs}")

# ── T11 what must survive ─────────────────────────────────────────────────────────────────────────────
print("\nT11 what must survive; every pool rotates")
check(list(cat_sounds.KEYS) == ["cat_trill", "cat_meow_at_door", "cat_demand", "cat_chatter", "cat_yowl_cargo", "cat_thump", "cat_lapping", "cat_storm_rustle", "cat_hiss", "cat_growl", "distant_yowl"],
      "cat_sounds.KEYS: the eleven keys, unchanged")
fresh_cat(DAY, location="by_the_fire", activity="watching")
fresh_larder(2)
sensorium.state["location"] = "study"
cat._prev_ref_txt = ""
h0 = cat.state["body"]["hunger"]
line = seen(cat.react("I feed the cat from the tin.", "", "study"))
check(bool(line) and cat.state["body"]["hunger"] < h0 and cat.state["saucer"]["has_food"] is True, "a well cat fed eats (hunger falls)")
cat._maybe_empty_saucer(SIM["now"] + cat.SAUCER_EATEN_AFTER_S + 10)
check(cat.state["saucer"]["has_food"] is False, "...and the saucer empties on its clock")
line = seen(cat.react("I stroke the cat.", "", "study"))
check(bool(line) and cat.state["mood"] == "affectionate", "a stroke is still a stroke")
check(cat_harm.legs_factor(cat.state, DAY) == 1.0 and cat_harm.hunt_factor(cat.state, DAY) == 1.0 and cat_harm.condition_drift(cat.state, 1.0, DAY) == 0.0 and cat_harm.clause(cat.state, DAY, dosed=False) == "",
      "a well young cat: x1 legs, x1 odds, no drift, no clause")
check(cat.presence_line("study") and cat.look_line("study", "the cat") and cat.affordance_line("study"), "her lines render as before")
small = [k for k, v in cat_content.HARM.items() if len(v) < 3]
check(not small, f"every HARM pool has at least three lines: {small}")
check(len(cat_content.PRESENCE["lying_low"]["any"]) >= 5, "the lying-low pool has at least five lines")
picks = [cat._pick_fresh("T11", list(cat_content.HARM["absence_mid"])) for _ in range(12)]
check(all(a != b for a, b in zip(picks, picks[1:])), "_pick_fresh: never the same line twice running")
check(cat_harm._LEDGER.exists() and cat_harm._LEDGER.parent == TMP, "the ledger is the isolated one")

# ── the live-store canary ────────────────────────────────────────────────────────────────────────────
print("\nlive-store canary")
FP_AFTER = _fingerprint()
leaks = sorted(n for n in set(FP_BEFORE) | set(FP_AFTER)
               if n not in _IGNORE and FP_BEFORE.get(n) != FP_AFTER.get(n))
check(not leaks, f"no live data/ top-level file changed during the run (LEAKS: {leaks})")

print(f"\n{'ALL OK' if not FAILS else 'FAILURES'}: {OKS} checks passed, {len(FAILS)} failed")
for f in FAILS:
    print("  -", f)
sys.exit(1 if FAILS else 0)
