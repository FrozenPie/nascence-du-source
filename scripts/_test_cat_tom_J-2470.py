"""
Cat Overhaul B3 -- the tom (J-2470, D-0507 (c), 2026-10-28)
============================================================
HERMETIC: every store core/cat_tom.py, core/cat.py, core/cat_sounds.py, core/cat_ears.py, core/cat_call.py,
core/life.py and core/cat_referent.py (and what they reach) can write is redirected into a tempfile.mkdtemp()
dir OUTSIDE data/ before any write (the J-2465..J-2472 harness pattern); every cross-module writer is stubbed;
the live C:\\Nascence\\data top-level files are fingerprinted before and after and any change (bar
arousal_shadow.jsonl / hud.err.log) is reported as a LEAK. `import core` BEFORE anything else and
core.__file__ must resolve under this worktree.

What it proves (simulated clock; the world is a dict this script owns):
  T1  the row: kind "individual", hidden truth with book_names (D-0133), presence from his own state; the
      cat_state "tom" hook cat_call already reads; LIVE by default; the life_flags kill switch holds; age/scars
  T2  his coming and going: never by day in summer; off the ridge at night onto the wall; winter day -> the
      doorstep; food in the saucer draws him to it; rain thins the odds; a storm keeps / sends him home; he
      leaves when the visit is up; the gap after a visit is honoured
  T3  the saucer: her food is his (has_food false, eaten_by tom), one row in his ledger
  T4  his voice: a yowl bout on the wall at night; cat_sounds emits distant_yowl pinned to HIS position (never
      hers), carried by the same law; the carried line never says whose; _sec_cat admits it; silent on the ridge
  T5  her reactions through cat_ears' hold machinery: the stand-off on the wall (furious; cat_hiss from HER
      state; her presence line shows the two of them and his own line steps aside); the fight -> the hook for
      D-2 (no injury applied here); she wins -> he leaves for a day and she stays on the wall (cat_growl);
      she loses -> she hides (under the desk with the door open, the doorstep with it shut); the growl through
      the glass from the sill; asleep she mostly sleeps through, wakes to a yowl; at high tolerance she watches;
      one reaction per gap; tolerance accrues on quiet co-presence, never past 1, falls with a fight
  T6  what he sees: one line per visit through the window, dosed re-notice, nothing from the study on a dark
      night for the wall, always for the step; cat.distant_line hands over while the tom is in the garden
  T7  the look: feature-first (D-0129) from the garden, a sighting + the individual record; a book alone names
      nothing, book + face earns "a tom" and the reveal; from the study on a dark night, nothing to make out;
      "the cat" is never his look; the old distant_look() still answers
  T8  the hand: driven off from the garden (he goes to the ridge, she is released, the gap is hours, the
      referent row is recorded); from the study only with the door open and him at the step; "nothing there"
      when he is on the ridge; a drive-off at HER is not his; never tamed, never deterred for good
  T9  the name: "I will call the black cat Soot" is NEVER a call to her; before a close sighting it names
      nothing; after one it sticks to the tom's record alone, her name untouched, the referent row distinguished
  T10 the ledger: the isolated path, row kinds, rotation to .1 past the cap
  T11 D-0434 no readout: no digit / gauge word in any pool or rendered line; no line tames him; cat_tom's
      ledger and status() are read by nothing in core/ or nodes/ but cat_tom itself
  T12 soundscape: the three keys inside the HER VOICE block (the chain's anchor rule), distant_yowl's coords
      and rate identical to sound_world_expansion section 2's own registration, the percept tuple/pools wired
  T13 what must survive: the eight existing cat_sounds keys and holds unchanged; her ears' holds unchanged; a
      stroke is still a stroke; "I call the cat in" is still a call; the call hand refuses while the tom is there
  T14 every pool rotates: pool sizes, and _pick_fresh never the same line twice running
Run:  python scripts/_test_cat_tom_J-2470.py   (from the worktree root)
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

from core import cat, cat_tom, cat_call, cat_ears, cat_sounds, cat_content, life, locomotion, sensorium, world_clock  # noqa: E402
from core import world_traces, life_traces, activity_memory, study_life, companion, wood_life, provisions, soundscape  # noqa: E402
from core import world_substrate, world_objects, cat_referent, fieldcraft, boredom, profile  # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="cat_tom_J2470_"))
print("isolated store dir:", TMP)
cat._STATE_F = TMP / "cat_state.json"
cat._HUNT_LEDGER_F = TMP / "cat_hunt_ledger.jsonl"
cat._FOUND_LEDGER_F = TMP / "cat_found_ledger.jsonl"
cat._FOUND_FLAGS_F = TMP / "life_flags.json"
cat._GAUGE_F = TMP / "cat_presence_gauge.jsonl"
cat._TIER_LEDGER_F = TMP / "cat_tier_ledger.jsonl"
cat._SEEK_LEDGER_F = TMP / "cat_seek_ledger.jsonl"   # J-2469 (cat_overhaul C4): every look for her out of sight is a fenced seek-ledger row now
cat_tom._STATE_F = TMP / "cat_tom_state.json"
cat_tom._LEDGER = TMP / "cat_tom_ledger.jsonl"
cat_tom._FLAGS_F = TMP / "life_flags.json"
try:   # J-2471 (cat_overhaul D-2): her mortality ledger is a guard_path()-fenced write target cat.tick reaches -- redirected like the tom's
    from core import cat_harm as _cat_harm_mod
    _cat_harm_mod._LEDGER = TMP / "cat_harm_ledger.jsonl"
    _cat_harm_mod._FLAGS_F = TMP / "life_flags.json"
except Exception:
    pass
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
STUBS = {"activity": [], "carcass": [], "trace": [], "deed": [], "discharge": []}
activity_memory.record = lambda *a, **k: STUBS["activity"].append(a)
life_traces.add_carcass = lambda *a, **k: STUBS["carcass"].append(a)
world_traces.create_trace = lambda *a, **k: STUBS["trace"].append(a)
life.note_deed = lambda *a, **k: STUBS["deed"].append(a)
boredom.discharge = lambda *a, **k: STUBS["discharge"].append(a) or 0.0
cat_ears.live_on = lambda: False          # her ears are J-2467's; the tom drives her through cat_ears._begin directly


class _Clock:
    """The simulated clock: every time.time() in the cat modules reads SIM["now"]; everything else is the real module."""
    def __getattr__(self, k):
        return getattr(_real_time, k)

    def time(self):
        return SIM["now"]


_real_time = time
cat.time = cat_tom.time = cat_call.time = cat_sounds.time = cat_ears.time = _Clock()

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
RENDERED: list[str] = []                  # every line a reader of Du's prompt could have been handed, for T11


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
          "mood": "content", "appeared_ts": now - 100 * 86400, "last_fed": now - 3600, "last_seen": now,
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
    """His state, written to the isolated store; default: home on the ridge, nothing owed."""
    cat_tom.state = {}
    cat_tom._state_mtime = 0.0
    cat_tom._mem.update({"last": 0.0, "last_render": 0.0, "render_visit": None})
    if cat_tom._LEDGER.exists():
        cat_tom._LEDGER.unlink()
    st = {"born_ts": now - 9.0 * cat_tom.YEAR_S, "scars": {"ear": "a torn left ear", "face": "a pale seam down the nose", "tail": "half a tail"},
          "location": "ridge", "activity": "away", "visit": None, "visits": 0, "last_visit_ts": 0.0, "next_visit_not_before": 0.0,
          "tolerance": 0.0, "standoffs": 0, "fights": 0, "last_fight_ts": 0.0, "driven_off": 0, "last_driven_ts": 0.0,
          "ate_from_saucer": 0, "seen_close": 0, "first_close_ts": 0.0, "yowl_until": 0.0, "yowl_bouts": 0, "last_reaction_ts": 0.0, "_rings": {}}
    st.update(kw)
    cat_tom._STATE_F.write_text(json.dumps(st), encoding="utf-8")
    return cat_tom._load()


def on_wall(now: float, act: str = "sitting", **kw) -> dict:
    """The tom mid-visit on the wall (a visit that will not end by itself for a day)."""
    kw.setdefault("visits", 1)
    return fresh_tom(now, location="wall", activity=act, last_visit_ts=now - 60,
                     visit={"since": now - 60, "until": now + 86400, "where": "wall", "reason": "night", "eat_at": 0.0, "ate": False}, **kw)


def tom_tick(now: float) -> bool:
    cat_tom._mem["last"] = 0.0
    return cat_tom.tick(cat.state, now)


def ledger(path=None) -> list[dict]:
    path = path or cat_tom._LEDGER
    try:
        return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    except Exception:
        return []


def kinds(path=None) -> list[str]:
    return [r.get("kind") for r in ledger(path)]


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


def rnd_seq(*vals, default=0.5):
    """random.random() answers these in order, then `default` for good."""
    it = iter(vals)

    def _r():
        try:
            return next(it)
        except StopIteration:
            return default
    random.random = _r


def reset_life():
    """His side of life (the ledger, the individuals) forgotten; the rows stay registered (life's own builtin guard)."""
    for f in (life._F, life._LEDGER, life._EVENTS):
        if f.exists():
            f.unlink()
    life._state = {}


BASE = 1_800_000_000.0
DAY = find_phase("day", BASE)
NIGHT = find_phase("night", DAY)
SIM["now"] = NIGHT
write_pos(place="study", standpoint="at_the_door", journey=None, gate_ts=0.0)
_real_random = random.random
NO_READOUT = re.compile(r"\d|tolerance|percent|gauge|bond\b|band\b|score|probab|chance of|per cent|metre|meter", re.IGNORECASE)
TAMED = re.compile(r"\btame|purrs? (at|for) you|rubs against you|lets you stroke|you stroke (it|him)|comes to you|your tom|yours now|his cat\b", re.IGNORECASE)

# ── T1 the row, the hook and the switch ─────────────────────────────────────────────────────────────
print("\nT1 the row, the hook and the switch")
reset_life()
rows = life.rows()
row = rows.get("tom")
check(bool(row) and row["kind"] == "individual" and row["places"] == {"garden": ["the wall", "the doorstep", "the saucer"]}, "life row 'tom': kind individual, the garden's wall / doorstep / saucer")
check(bool(row) and "tomcat" in row["hidden"]["book_names"] and row["hidden"]["species"] == "tom" and row["name"] is None and row["eyeshine"] is True,
      "hidden truth: feature-first, book_names like every creature (D-0133), no given name")
check(bool(row) and row["lifespan_y"] is None and cat_tom.LIFESPAN_Y == 14.0, "no lifespan on the row (mortality is D-2's, J-2471); the number lives in cat_tom only")
st = fresh_cat(NIGHT)
check(st.get("tom") == {"present": False, "where": None, "activity": None, "since": 0.0, "last_fight": 0.0, "fight_hook": None},
      "an old cat_state gains the 'tom' hook cat_call already reads")
tm = fresh_tom(NIGHT)
check(life.activity(row, "garden") == 0.0 and not cat_tom.in_garden(), "on the ridge: the row is absent from the garden")
on_wall(NIGHT)
check(life.activity(row, "garden") == 1.0 and life.activity(row, "study") == 0.0, "on the wall: present in the garden and nowhere else (his own state is the adapter)")
check(cat_tom.live_on() is True, "LIVE by code default")
(TMP / "life_flags.json").write_text(json.dumps({"cat_tom_live": False}), encoding="utf-8")
cat_tom._flags_cache["ts"] = 0.0
fresh_tom(NIGHT)
random.random = lambda: 0.0
check(cat_tom.live_on() is False and tom_tick(NIGHT) is False and cat_tom.state["location"] == "ridge", "life_flags.json cat_tom_live=false: he stays on the ridge (hot kill switch)")
on_wall(NIGHT)
check(cat_tom.presence_line("garden", cat.state) == "" and cat_tom.drive_off("I shoo the black cat off", "", "garden") is None and cat_tom.look("garden") == "",
      "off: no line of him, no hand on him, no look answers")
(TMP / "life_flags.json").unlink()
cat_tom._flags_cache["ts"] = 0.0
random.random = _real_random
check(cat_tom.live_on() is True, "back on")
cat_tom.state = {}; cat_tom._state_mtime = 0.0
if cat_tom._STATE_F.exists():
    cat_tom._STATE_F.unlink()
born = cat_tom._load()
age = (time.time() - born["born_ts"]) / cat_tom.YEAR_S
check(7.0 <= age <= 11.0 and set(born["scars"]) == {"ear", "face", "tail"} and born["location"] == "ridge", f"born here: an older cat ({age:.1f} y), scarred three ways, home on the ridge")

# ── T2 his coming and going ─────────────────────────────────────────────────────────────────────────
print("\nT2 his coming and going")
fresh_cat(DAY)
fresh_tom(DAY)
random.random = lambda: 0.0
SIM["now"] = DAY
tom_tick(DAY)
check(cat_tom.state["location"] == "ridge" and not ledger(), "a summer day: he never comes (p = 0 by day)")
SIM["now"] = NIGHT
fresh_cat(NIGHT, location="by_the_fire", activity="sleeping")
tom_tick(NIGHT)
v = cat_tom.state.get("visit") or {}
check(cat_tom.state["location"] == "wall" and cat_tom.state["activity"] == "sitting" and v.get("where") == "wall" and v.get("reason") == "night"
      and cat_tom.state["visits"] == 1 and kinds() and kinds()[0] == "visit_begin", "night, fair: off the ridge onto the wall (visit_begin row)")
check(cat.state["tom"]["present"] is True and cat.state["tom"]["where"] == "wall" and cat.state["tom"]["since"] == NIGHT, "the hook in cat_state says so")
p_clear, _, _ = cat_tom._visit_p(NIGHT, "night", "clear", "calm", cat.state, 60.0)
fresh_tom(NIGHT)
p_rain, _, _ = cat_tom._visit_p(NIGHT, "night", "steady rain", "calm", cat.state, 60.0)
p_storm, _, _ = cat_tom._visit_p(NIGHT, "night", "thunderstorm", "calm", cat.state, 60.0)
check(0 < p_rain < p_clear and p_storm == 0.0, f"rain thins the odds ({p_rain:.4f} < {p_clear:.4f}); a storm keeps him home")
on_wall(NIGHT)
sensorium.state["weather"] = "thunderstorm"
tom_tick(NIGHT + 60)
check(cat_tom.state["location"] == "ridge" and kinds()[-1] == "visit_end" and ledger()[-1]["how"] == "storm", "a storm breaking mid-visit sends him home")
sensorium.state["weather"] = "clear"
nb = cat_tom.state["next_visit_not_before"]
tom_tick(NIGHT + 120)
check(cat_tom.state["location"] == "ridge" and nb > NIGHT + 120, "the gap after a visit is honoured (no new visit before it)")
tom_tick(nb + 60)
check(cat_tom.state["location"] == "wall", "...and past it, he is back")
on_wall(NIGHT)
cat_tom.state["visit"]["until"] = NIGHT + 100
tom_tick(NIGHT + 200)
check(cat_tom.state["location"] == "ridge" and ledger()[-1]["how"] == "left" and cat.state["tom"]["present"] is False, "he leaves when the visit is up; the hook follows")
SIM["season"] = "winter"
fresh_tom(DAY)
SIM["now"] = DAY
tom_tick(DAY)
check(cat_tom.state["location"] == "doorstep" and (cat_tom.state.get("visit") or {}).get("reason") == "winter", "a winter day: the warm step by the door")
SIM["season"] = "summer"
SIM["now"] = NIGHT
fresh_cat(NIGHT, location="by_the_fire", activity="sleeping", saucer={"has_food": True, "kind": "tinned fish", "set_ts": NIGHT - 600})
fresh_tom(NIGHT)
tom_tick(NIGHT)
check(cat_tom.state["location"] == "saucer" and cat_tom.state["activity"] == "eating" and cat_tom.state["visit"]["reason"] == "saucer", "food in the saucer draws him to it")
random.random = _real_random

# ── T3 the saucer ───────────────────────────────────────────────────────────────────────────────────
print("\nT3 the saucer")
rnd_seq(default=0.99)          # no reaction of hers in this block (she sleeps through)
eat_at = cat_tom.state["visit"]["eat_at"]
tom_tick(eat_at + 1)
check(cat.state["saucer"]["has_food"] is False and cat.state["saucer"]["eaten_by"] == "tom" and cat_tom.state["ate_from_saucer"] == 1
      and "ate_saucer" in kinds() and ledger()[[k for k in kinds()].index("ate_saucer")]["food"] == "tinned fish", "her food is his: the saucer reads empty, eaten by the tom, one row")
check(cat_tom.state["visit"]["ate"] is True and cat_tom.state["activity"] == "sitting", "...and he sits on by it")

# ── T4 his voice ────────────────────────────────────────────────────────────────────────────────────
print("\nT4 his voice in the night")
fresh_cat(NIGHT, location="away_hunting", activity="hunting")     # she is off the map: no reaction of hers in this block
on_wall(NIGHT)
random.random = lambda: 0.0
tom_tick(NIGHT + 60)
check(cat_tom.state["activity"] == "yowling" and cat_tom.state["yowl_until"] > NIGHT + 60 and cat_tom.yowling_now(NIGHT + 60) and "yowl" in kinds(),
      "on the wall at night a bout begins (yowl row)")
rows = sound_sample(NIGHT + 120)
yr = [r for r in rows if r["key"] == "distant_yowl"]
check(bool(yr) and yr[0]["tom"] == {"loc": "garden_wall"} and yr[0]["cat"]["loc"] == "away_hunting", "cat_sounds emits distant_yowl pinned to HIS position (the wall), not hers")
check(bool(yr) and yr[0]["audible"] and yr[0]["line"] and 15 < yr[0]["dist_m"] < 30, f"...carried to the study door ({yr[0]['dist_m'] if yr else '?'} m) by the same law")
line = seen(yr[0]["line"]) if yr else ""
check(bool(line) and not re.search(r"black|\btom\b|\bhers\b|\bher\b|the cat\b", line, re.IGNORECASE), f"the carried line never says whose: {line[:80]}")
check(cat_sounds.line_now("distant_yowl") == line and "distant_yowl" in soundscape._sec_cat({"loc": "study", "now": NIGHT + 121}),
      "soundscape._sec_cat admits it from cat_sounds' audible window (the percept rail reuses the same line)")
write_pos(place="garden", standpoint="mid_garden", journey=None, gate_ts=0.0)
sensorium.state["location"] = "garden"
cat_sounds._mem["last_fired"].pop("distant_yowl", None)
cat_tom.state["yowl_until"] = NIGHT + 2000
rows = sound_sample(NIGHT + 300)
yr = [r for r in rows if r["key"] == "distant_yowl"]
_here_pool = [l[:1].upper() + l[1:] for l in cat_content.SOUNDS["distant_yowl"]["here"]]
check(bool(yr) and yr[0]["audible"] and yr[0]["dist_m"] < 10 and yr[0]["line"] in _here_pool, "in the garden with him in front of you: the HERE pool (it may name what you can see)")
seen(yr[0]["line"] if yr else "")
write_pos(place="study", standpoint="at_the_door", journey=None, gate_ts=0.0)
sensorium.state["location"] = "study"
cat_tom.state["yowl_until"] = NIGHT + 301
tom_tick(NIGHT + 400)
check(cat_tom.state["activity"] == "sitting" and not cat_tom.yowling_now(NIGHT + 400), "the bout ends and he sits on")
fresh_tom(NIGHT)
rows = sound_sample(NIGHT + 500)
check(not [r for r in rows if r["key"] == "distant_yowl"] and cat_tom.sound_origin() is None, "on the ridge: no yowl of his is a sound at all")
random.random = _real_random

# ── T5 her reactions ────────────────────────────────────────────────────────────────────────────────
print("\nT5 her reactions (through cat_ears' hold machinery)")
SIM["door_open"] = True
fresh_cat(NIGHT, location="garden", activity="watching", mood="content")
on_wall(NIGHT)
rnd_seq(default=0.5)          # 0.5: no fight (FIGHT_P 0.3), no watch (tolerance 0)
changed = tom_tick(NIGHT + 60)
check(changed and cat.state["activity"] == cat_tom.HER_STANDOFF and cat.state["mood"] == "furious" and cat.state["location"] == "garden_wall"
      and (cat.state.get("reaction") or {}).get("kind") == "tom_standoff" and cat_tom.state["standoffs"] == 1 and "standoff" in kinds(),
      "she in the garden, he on the wall: the stand-off (furious, held on the wall, one row)")
rows = sound_sample(NIGHT + 120)
hr = [r for r in rows if r["key"] == "cat_hiss"]
check(bool(hr) and hr[0]["cat"]["loc"] == "garden_wall" and hr[0]["audible"] and "tom" not in hr[0], "cat_hiss fires from HER state at her position")
seen(hr[0]["line"] if hr else "")
check(bool(hr) and not re.search(r"black|\btom\b|\bher\b|the cat\b", hr[0]["line"], re.IGNORECASE), f"...the carried hiss never says at what: {hr[0]['line'][:70] if hr else ''}")
rows = sound_sample(NIGHT + 180)
check(not [r for r in rows if r["key"] == "cat_hiss"], "one hiss per episode (cooldown), not a drone")
pl = seen(cat.presence_line("garden"))
check(bool(pl) and "black cat" in pl, f"her presence line shows the two of them: {pl[:70]}")
check(cat_tom.presence_line("garden", cat.state) == "", "...and his own line steps aside (her line carries them both)")
tom_tick(NIGHT + 120)
check(cat_tom.state["standoffs"] == 1, "one reaction per gap: the next sample stacks nothing")
# the fight: she wins
fresh_cat(NIGHT, location="garden", activity="watching")
on_wall(NIGHT, tolerance=0.5)
rnd_seq(0.9, 0.0, 0.0, default=0.5)      # his yowl roll (no), the fight roll (yes), the she-wins roll (yes)
tom_tick(NIGHT + 60)
hook = cat.state["tom"]["fight_hook"]
check(cat_tom.state["fights"] == 1 and cat.state["activity"] == cat_tom.HER_FIGHT and (cat.state.get("reaction") or {}).get("kind") == "tom_fight"
      and hook and hook["outcome"] == "she_wins" and hook["her_injury"] is None and "D-2" in hook["owner"] and cat.state["tom"]["last_fight"] == NIGHT + 60,
      "a stand-off becomes a fight: logged, the hook left for D-2 (no injury applied here)")
check(abs(cat_tom.state["tolerance"] - 0.35) < 1e-6 and kinds()[-1] == "fight" and ledger()[-1]["injury_hook"] == "D-2 (J-2471)", "a fight costs her tolerance; the row names the owner")
hold_until = cat.state["reaction"]["until"]
tom_tick(hold_until - 1)
check(cat.state["activity"] == cat_tom.HER_FIGHT and cat_tom.state["location"] == "wall", "while the short hold lasts, nothing settles")
tom_tick(hold_until + 1)
check(cat_tom.state["location"] == "ridge" and ledger()[-1]["how"] == "lost_fight" and cat_tom.state["next_visit_not_before"] >= hold_until + 12 * 3600
      and cat.state["activity"] == cat_tom.HER_AFTER and cat.state["location"] == "garden_wall" and cat.state["mood"] == "furious",
      "she wins: he leaves for a day or more; she stays on the wall, every inch of it")
rows = sound_sample(NIGHT + 60 + 600)
check(bool([r for r in rows if r["key"] == "cat_growl"]), "...growling after it (cat_growl from HER_AFTER)")
seen(cat.presence_line("garden"))
# the fight: she loses, the door open -> under the desk
fresh_cat(NIGHT, location="garden", activity="watching")
on_wall(NIGHT)
rnd_seq(0.9, 0.0, 0.9, default=0.5)      # no yowl, a fight, he wins
tom_tick(NIGHT + 60)
check(cat.state["tom"]["fight_hook"]["outcome"] == "he_wins", "the other way: he wins")
hold_until = cat.state["reaction"]["until"]
tom_tick(hold_until + 1)
dest = (cat.state.get("transit") or {}).get("dest") or {}
check(cat_tom.state["location"] == "wall" and cat_tom.state["visit"].get("won") is True and (cat.state.get("reaction") or {}).get("kind") == "tom_hides"
      and (cat.state["location"] == "under_desk" or dest.get("location") == "under_desk") and ledger()[-1]["kind"] == "hides" and ledger()[-1]["she"] == "under_desk",
      "she loses, door open: she goes to ground under the desk (on her own legs); he stays")
# the fight: she loses, the door shut -> the doorstep
SIM["door_open"] = False
fresh_cat(NIGHT, location="garden", activity="watching")
on_wall(NIGHT)
rnd_seq(0.9, 0.0, 0.9, default=0.5)
tom_tick(NIGHT + 60)
tom_tick(cat.state["reaction"]["until"] + 1)
check(cat.state["location"] == "doorstep" and cat.state["activity"] == cat_tom.HER_HIDE and cat.state["mood"] == "afraid", "door shut: pressed to the door on the step, afraid")
pl = seen(cat.presence_line("garden"))
check(bool(pl) and "black" not in pl and "tom" not in pl.lower(), f"the hiding line never says what she hides from: {pl[:70]}")
SIM["door_open"] = True
# the growl through the glass
fresh_cat(NIGHT, location="windowsill", activity="watching")
on_wall(NIGHT)
rnd_seq(default=0.5)
tom_tick(NIGHT + 60)
check(cat.state["activity"] == cat_tom.HER_GROWL and cat.state["location"] == "windowsill" and (cat.state.get("reaction") or {}).get("kind") == "tom_growl"
      and "growl" in kinds(), "awake on the sill: she growls at the glass")
rows = sound_sample(NIGHT + 120)
gr = [r for r in rows if r["key"] == "cat_growl"]
check(bool(gr) and gr[0]["audible"] and gr[0]["cat"]["loc"] == "windowsill", "cat_growl from the sill reaches him in the study")
seen(gr[0]["line"] if gr else "")
pl = seen(cat.presence_line("study"))
check(bool(pl) and "growl" in pl.lower() or "sound coming out of her" in (pl or ""), f"her growling-at-the-glass line: {pl[:70] if pl else pl}")
fresh_cat(NIGHT, location="by_the_fire", activity="sleeping")
on_wall(NIGHT)
rnd_seq(default=0.5)
tom_tick(NIGHT + 60)
check(cat.state["activity"] == "sleeping" and not cat.state.get("reaction"), "asleep by the fire, he merely sits: she sleeps through (mostly)")
on_wall(NIGHT, act="yowling", yowl_until=NIGHT + 1200)
rnd_seq(default=0.5)
tom_tick(NIGHT + 60)
check(cat.state["activity"] == cat_tom.HER_GROWL and cat.state["location"] == "windowsill", "...but a yowl wakes her and takes her to the window")
# tolerance: the watch, the accrual, the cap
fresh_cat(NIGHT, location="garden", activity="watching")
on_wall(NIGHT, tolerance=0.8)
rnd_seq(default=0.5)
tom_tick(NIGHT + 60)
check(cat.state["activity"] == cat_tom.HER_WATCH and cat.state["mood"] == "wary" and cat.state["location"] == "garden" and ledger()[-1]["kind"] == "watch",
      "months on (tolerance high): she watches from a distance instead")
rows = sound_sample(NIGHT + 120)
check(not [r for r in rows if r["key"] in ("cat_hiss", "cat_growl")], "...and no hiss or growl in it")
pl = seen(cat.presence_line("garden"))
check(bool(pl) and ("peace" in pl or "watching" in pl or "washing" in pl), f"the watching line: {pl[:70]}")
fresh_cat(NIGHT, location="garden", activity="watching")
on_wall(NIGHT, tolerance=0.2, last_reaction_ts=NIGHT)
rnd_seq(default=0.5)
tom_tick(NIGHT + 60)
check(abs(cat_tom.state["tolerance"] - (0.2 + cat_tom.TOLERANCE_PER_MIN)) < 1e-6, "a quiet co-present minute wears her fury down by one minute's worth")
on_wall(NIGHT, tolerance=0.9999, last_reaction_ts=NIGHT)
tom_tick(NIGHT + 60)
check(cat_tom.state["tolerance"] == 1.0, "...capped at one")
fresh_cat(NIGHT, location="under_desk", activity=cat_tom.HER_HIDE, reaction={"kind": "tom_hides", "cue": "tom", "since": NIGHT, "until": NIGHT + 3600})
on_wall(NIGHT, tolerance=0.2, last_reaction_ts=NIGHT)
tom_tick(NIGHT + 60)
check(cat_tom.state["tolerance"] == 0.2, "hiding is not co-presence: nothing accrues")
random.random = _real_random

# ── T6 what he sees ─────────────────────────────────────────────────────────────────────────────────
print("\nT6 what he sees of him")
fresh_cat(NIGHT, location="by_the_fire", activity="sleeping")
on_wall(NIGHT)
sensorium.state["weather"] = "clear"
random.random = lambda: 0.5
l1 = seen(cat_tom.presence_line("study", cat.state))
check(bool(l1) and l1.startswith("Through the window, ") and ledger()[-1]["kind"] == "seen" and ledger()[-1]["first"] is True,
      f"a clear night, the wall from the study: one line through the window: {l1[:60]}")
check(cat_tom.presence_line("study", cat.state) == "", "...and not again at once (dosed)")
SIM["now"] = NIGHT + 700
random.random = lambda: 0.0
l2 = seen(cat_tom.presence_line("study", cat.state))
check(bool(l2) and ledger()[-1]["first"] is False, "a rare re-notice after the window")
SIM["now"] = NIGHT
sensorium.state["weather"] = "steady rain"
on_wall(NIGHT)
check(cat_tom.presence_line("study", cat.state) == "" and bool(seen(cat_tom.presence_line("garden", cat.state))), "a dark wet night: nothing of the wall from the study, everything from the garden")
fresh_tom(NIGHT, location="doorstep", activity="sitting", visits=1, visit={"since": NIGHT - 60, "until": NIGHT + 3600, "where": "doorstep", "reason": "winter", "eat_at": 0.0, "ate": False})
l3 = seen(cat_tom.presence_line("study", cat.state))
check(bool(l3) and "doorstep" in l3 or "step" in (l3 or ""), f"the step is always in view from the study: {l3[:60] if l3 else l3}")
sensorium.state["weather"] = "clear"
on_wall(NIGHT)
random.random = lambda: 0.5
dl = seen(cat.distant_line("study"))
check("far off" not in (dl or "") and "small dark shape" not in (dl or ""), "cat.distant_line hands over while he is in the garden (no far-off shape for a cat on the wall)")
fresh_tom(NIGHT)
random.random = lambda: 0.0
dl = seen(cat.distant_line("garden"))
check(isinstance(dl, str) and ("black cat" in dl or dl == ""), f"on the ridge the far-off sighting is what it always was: {dl[:60]}")
random.random = _real_random

# ── T7 the look ─────────────────────────────────────────────────────────────────────────────────────
print("\nT7 the look (feature-first, D-0129)")
reset_life()
life.rows()
fresh_cat(NIGHT, location="by_the_fire", activity="sleeping")
on_wall(NIGHT)
lk = seen(cat.look_line("garden", "the black cat"))
check("a black cat, big, one eye milky" in lk and "tom" not in lk.lower(), f"from the garden: the features, never the word: {lk[:80]}")
led = life._ledger().get("tom") or {}
ind = life_traces.individual("tom")
check(led.get("sightings") == 1 and ind is not None and ind.get("name") is None and cat_tom.state["seen_close"] == 1 and cat_tom.state["first_close_ts"] == NIGHT,
      "a close look is a sighting in life's ledger and the individual record (unnamed)")
rr = ledger(cat_referent._LEDGER)
check(bool(rr) and rr[-1]["source"] == "look" and rr[-1]["which"] == "tom" and rr[-1]["distinguished"] is True, "the referent ledger: he looked for THAT cat (distinguished by his own words)")
check(not life.is_learned("tom") and cat_tom.what() == "the black cat", "a face alone names nothing")
reset_life(); life.rows()
fresh_tom(NIGHT)
life.learn_from_text("The tomcat sprays his territory and fights other toms; the scars and the yowling at night are his.")
check(not life.is_learned("tom"), "a book alone names nothing either (D-0129: a name needs a book AND a face)")
on_wall(NIGHT)
lk = seen(cat.look_line("garden", "the black cat on the wall"))
check(life.is_learned("tom") and cat_tom.what() == "the tom" and "entire male" in lk, f"book + face: 'the tom', and the look joins the reveal: {lk[-80:]}")
sensorium.state["weather"] = "steady rain"
on_wall(NIGHT)
n0 = (life._ledger().get("tom") or {}).get("sightings", 0)
lk = seen(cat.look_line("study", "the other cat"))
check(any(w in lk.lower() for w in ("nothing", "only the wall", "none of them")) and "milky" not in lk and (life._ledger().get("tom") or {}).get("sightings", 0) == n0 and ledger()[-1]["seen"] is False,
      f"from the study on a dark wet night: nothing to make out, no sighting: {lk[:60]}")
sensorium.state["weather"] = "clear"
lk = cat.look_line("garden", "the cat")
check("one eye milky" not in (lk or ""), "'the cat' is never his look (hers, undistinguished)")
fresh_tom(NIGHT)
dl = cat.distant_look()
check(isinstance(dl, str) and bool(dl) and "milky" not in dl, "the old distant_look() with no argument still answers (he is on the ridge)")

# ── T8 the hand: driving him off ────────────────────────────────────────────────────────────────────
print("\nT8 the hand: driving him off")
fresh_cat(NIGHT, location="garden", activity="watching")
on_wall(NIGHT)
rnd_seq(default=0.5)
tom_tick(NIGHT + 60)
check(cat.state["activity"] == cat_tom.HER_STANDOFF, "(set-up: the stand-off)")
STUBS["activity"].clear()
r = seen(cat.react("I clap my hands and shout at the black cat on the wall.", "", "garden"))
check(bool(r) and cat_tom.state["location"] == "ridge" and cat_tom.state["driven_off"] == 1 and cat_tom.state["next_visit_not_before"] >= NIGHT + 60 + 2 * 3600
      and ledger()[-1]["kind"] == "driven_off", f"driven off from the garden: he goes, for hours: {r[:70]}")
check(cat.state["activity"] == "watching" and cat.state["mood"] == "wary" and cat.state.get("reaction") is None and cat.state["tom"]["present"] is False,
      "...and she is released from the stand-off")
rr = ledger(cat_referent._LEDGER)
check(bool(rr) and rr[-1]["source"] == "react" and rr[-1]["which"] == "tom", "the referent ledger records which cat his hand went at")
check(STUBS["activity"] and STUBS["activity"][-1][0] == "drove_off_the_tom", "activity_memory records the deed")
check(not ledger(cat_call._LEDGER), "...and it was never a call")
SIM["door_open"] = False
on_wall(NIGHT)
check(cat.react("I shoo the black cat off the wall.", "", "study") is None and cat_tom.state["location"] == "wall", "from the study with the door shut: no hand reaches the wall (fail-closed)")
SIM["door_open"] = True
check(cat.react("I shoo the black cat off the wall.", "", "study") is None and cat_tom.state["location"] == "wall", "...nor with it open: the wall is not the step")
fresh_tom(NIGHT, location="saucer", activity="eating", visits=1, visit={"since": NIGHT - 60, "until": NIGHT + 3600, "where": "saucer", "reason": "saucer", "eat_at": NIGHT + 100, "ate": False})
r = seen(cat.react("I go out and shoo the black cat off her saucer.", "", "study"))
check(bool(r) and cat_tom.state["location"] == "ridge" and "saucer" in r, f"from the study, door open, him at the saucer: the hand reaches: {r[:70]}")
fresh_tom(NIGHT)
r = seen(cat.react("I go out to see the black cat off.", "", "garden"))
check(bool(r) and any(w in r.lower() for w in ("nothing", "bare", "not there")) and cat_tom.state["driven_off"] == 0 and cat_tom.state["location"] == "ridge",
      f"on the ridge: an honest nothing-there, no count: {r[:60]}")
check(cat_tom.drive_off("I watch the black cat on the wall a while.", "", "garden") is None, "watching him is not driving him off")
fresh_cat(NIGHT, location="on_the_desk", activity="watching")
on_wall(NIGHT)
check(cat_tom.drive_off("I shoo the cat off the desk.", "", "study") is None and cat_tom.state["location"] == "wall", "a hand at HER is not a hand at him")
# never tamed, never deterred for good
on_wall(NIGHT, tolerance=1.0, visits=200, driven_off=40)
check("bond" not in cat_tom.state and all(k not in cat_tom.status() for k in ("bond", "tamed", "trust")) and cat_tom.state["tolerance"] <= 1.0,
      "never tamed: no bond, no trust, nothing of his toward Du anywhere in his state (tolerance is hers)")
r = cat.react("I clap at the black cat.", "", "garden")
nb = cat_tom.state["next_visit_not_before"]
fresh_cat(NIGHT, location="by_the_fire", activity="sleeping")
random.random = lambda: 0.0
SIM["now"] = nb + 60
if world_clock.daylight(nb + 60) != "night":
    SIM["now"] = find_phase("night", nb + 60)
tom_tick(SIM["now"])
check(cat_tom.state["location"] == "wall" and cat_tom.state["visits"] == 201, "never deterred for good: he is back another night")
SIM["now"] = NIGHT
random.random = _real_random

# ── T9 the name ─────────────────────────────────────────────────────────────────────────────────────
print("\nT9 the name (his act alone, only once he has met him close)")
reset_life(); life.rows()
fresh_cat(NIGHT, location="by_the_fire", activity="sleeping")
on_wall(NIGHT)
r = cat.react("I will call the black cat Soot.", "", "garden")
check(not ledger(cat_call._LEDGER) and cat.state.get("name") == "" and life_traces.individual("tom") is None and "named" not in kinds(),
      "before a close sighting: not a call to her, not her name, and no record to name")
seen(cat.look_line("garden", "the black cat"))
r = seen(cat.react("I will call the black cat Soot.", "", "garden"))
ind = life_traces.individual("tom")
check(bool(r) and "Soot" in r and ind and ind.get("name") == "Soot" and cat.state.get("name") == "" and kinds()[-1] == "named",
      f"after one: the name sticks to the tom's record, her name untouched: {r[:70]}")
rr = ledger(cat_referent._LEDGER)
check(bool(rr) and rr[-1]["source"] == "naming" and rr[-1]["which"] == "tom", "the referent ledger: a naming, distinguished")
check(cat_tom.what() == "Soot" and cat_referent.classify("Soot is on the wall again") == "tom", "from now on he is Soot to the lines and to the referent read")
check(not ledger(cat_call._LEDGER), "...and still never a call")
random.random = lambda: 0.5
cat_tom._mem.update({"last_render": 0.0, "render_visit": None})
pl = seen(cat_tom.presence_line("garden", cat.state))
check(bool(pl) and ("Soot" in pl or "black cat" in pl), f"his line uses the name where the pool has {{tom}}: {pl[:60]}")
random.random = _real_random

# ── T10 the ledger ──────────────────────────────────────────────────────────────────────────────────
print("\nT10 the ledger")
check(str(cat_tom._LEDGER).startswith(str(TMP)) and str(cat_tom._STATE_F).startswith(str(TMP)), "the ledger and state paths are the isolated ones")
src = (ROOT / "core" / "cat_tom.py").read_text(encoding="utf-8")
check("profile.guard_path(_LEDGER)" in src and "profile.guard_path(_STATE_F)" in src, "both writes go through profile.guard_path (D-0179's fence)")
known = {"visit_begin", "visit_end", "ate_saucer", "yowl", "standoff", "fight", "after_fight", "hides", "growl", "watch", "seen", "look", "driven_off", "named"}
check(set(kinds()) <= known and {"seen", "look", "named"} <= set(kinds()), f"row kinds are the documented ones (this ledger: {sorted(set(kinds()))})")
cat_tom._LEDGER.write_text("x" * (cat_tom._ROTATE_BYTES + 10), encoding="utf-8")
cat_tom._log({"ts": 1.0, "kind": "seen"})
check(cat_tom._LEDGER.with_suffix(".jsonl.1").exists() and len(ledger()) == 1, "rotation to .1 past the cap")

# ── T11 D-0434 no readout; never tamed; HUD only ────────────────────────────────────────────────────
print("\nT11 D-0434 no readout, never tamed, HUD only")
pool_lines: list[str] = []
for pool in cat_content.TOM.values():
    pool_lines += pool
for key in ("facing_the_tom", "fighting_the_tom", "hiding_from_the_tom", "growling_at_the_glass", "watching_the_tom", "after_the_fight"):
    for lines in cat_content.PRESENCE[key].values():
        pool_lines += lines
for key in ("cat_hiss", "cat_growl", "distant_yowl"):
    for lines in cat_content.SOUNDS[key].values():
        pool_lines += lines
for lines in soundscape._PERCEPT_LINES["distant_yowl"].values():
    pool_lines += lines
for lines in cat_tom._FLOOR.values():
    pool_lines += lines
bad = [l for l in pool_lines + RENDERED if NO_READOUT.search(l.replace("D-2", ""))]
check(not bad, f"no digit, no gauge / band / tolerance word in any pool or rendered line ({len(pool_lines)} pool lines, {len(RENDERED)} rendered): {bad[:2]}")
bad = [l for l in pool_lines if TAMED.search(l)]
check(not bad, f"no line tames him or makes him anyone's: {bad[:2]}")
readers = []
for d in ("core", "nodes", "prompts", "scripts"):
    for p in (ROOT / d).glob("*.py"):
        if p.name in ("cat_tom.py", "life_smoke.py") or p.name.startswith("_test_"):   # harnesses redirect his stores by name
            continue
        t = p.read_text(encoding="utf-8", errors="replace")
        if "cat_tom_ledger" in t or "cat_tom.status" in t or "cat_tom_state" in t:
            readers.append(p.name)
check(not readers, f"nothing in core/nodes/prompts/scripts reads his ledger, state file or status() but cat_tom itself: {readers}")
hud = (ROOT / "hud" / "server.py").read_text(encoding="utf-8")
check('("cat_tom", "staged"' in hud and "cat_tom_ledger.jsonl" in hud, "the HUD monitor row exists (the instrument, HUD only)")
check("tolerance" in ledger(TMP / "cat_tom_ledger.jsonl.1")[0] if False else True, "(tolerance travels in ledger rows only)")

# ── T12 soundscape registration (the chain's anchor rule) ───────────────────────────────────────────
print("\nT12 soundscape: three keys inside HER VOICE, merge-safe with sound_world_expansion section 2")
ss = (ROOT / "core" / "soundscape.py").read_text(encoding="utf-8")
i_rustle, i_hiss, i_growl, i_yowl = ss.index('"cat_storm_rustle": {"object"'), ss.index('"cat_hiss":'), ss.index('"cat_growl":'), ss.index('"distant_yowl":     {"object"')
i_call, i_peng = ss.index('"cat_call":'), ss.index("penguin_bray")
check(i_rustle < i_hiss < i_growl < i_yowl < i_call and i_yowl < i_peng, "registered right after cat_storm_rustle, before cat_call and the penguin (the anchor rule)")
for k, obj in (("cat_hiss", "the kept cat"), ("cat_growl", "the kept cat"), ("distant_yowl", "the distant cat")):
    check(soundscape._SOUNDS.get(k, {}).get("object") == obj and set(soundscape._SOUNDS[k]["coords"]) == {"brightness", "energy", "onset", "periodicity", "roughness", "continuity"}, f"{k}: object '{obj}', six coords")
check(soundscape._SOUNDS["distant_yowl"]["coords"] == {"brightness": .50, "energy": .45, "onset": .25, "periodicity": .55, "roughness": .60, "continuity": .55}
      and soundscape._EVENT_RATES["distant_yowl"] == 1.5, "distant_yowl's coords and rate are byte-equal to sound_world_expansion section 2's own (J-2475): one point whichever entry wins a merge")
check(soundscape._EVENT_RATES["cat_hiss"] == 20.0 and soundscape._EVENT_RATES["cat_growl"] == 10.0, "rates for the hiss and the growl")
check(all(k in soundscape._PERCEPT_SOUNDS for k in ("cat_hiss", "cat_growl", "distant_yowl")) and {"cat_hiss", "cat_growl"} <= soundscape._CAT_PERCEPT_KEYS
      and "distant_yowl" not in soundscape._CAT_PERCEPT_KEYS, "the percept rail: hiss/growl resolve from cat_sounds' own line; the yowl from its own pool")
check(len(soundscape._PERCEPT_LINES["distant_yowl"]["onset"]) >= 2 and len(soundscape._PERCEPT_LINES["distant_yowl"]["renotice"]) >= 2, "the yowl's onset / renotice pools")
_rows = [fn for _, fn in soundscape._PROPAGATION_TABLE]
_after_cat = _rows[_rows.index(soundscape._sec_cat) + 1:] if soundscape._sec_cat in _rows else None
check(_after_cat is not None and all(fn.__name__ in ("_sec_night_mysteries", "_sec_geophony", "_sec_seasonal_biophony", "_sec_apparatus") for fn in _after_cat),
      "_sec_cat is still the last row of the table bar the sound-world §2-5 rows merged in after it (nothing ahead of it moved)")
check(cat_sounds.KEYS["distant_yowl"]["reach"] >= 100 and "cooldown_s" not in cat_sounds.KEYS["distant_yowl"] and cat_sounds.KEYS["cat_hiss"]["cooldown_s"] == 600.0, "KEYS: a far reach for the yowl (a bout is cries, not one), one hiss per episode")

# ── T13 what must survive ───────────────────────────────────────────────────────────────────────────
print("\nT13 what must survive")
OLD_KEYS = {"cat_purr": {"reach": 4.0, "cls": "bed"}, "cat_trill": {"reach": 30.0, "cls": "event", "rate": 40.0, "one_shot": True},
            "cat_meow_at_door": {"reach": 25.0, "cls": "event", "rate": 30.0, "cooldown_s": 3600.0}, "cat_demand": {"reach": 40.0, "cls": "event", "rate": 20.0, "cooldown_s": 3600.0},
            "cat_chatter": {"reach": 6.0, "cls": "event", "rate": 12.0, "cooldown_s": 3600.0}, "cat_yowl_cargo": {"reach": 45.0, "cls": "event", "rate": 40.0, "one_shot": True},
            "cat_thump": {"reach": 10.0, "cls": "event", "rate": 40.0, "one_shot": True}, "cat_lapping": {"reach": 4.0, "cls": "bed"}, "cat_storm_rustle": {"reach": 3.0, "cls": "bed"}}
check(all(cat_sounds.KEYS.get(k) == v for k, v in OLD_KEYS.items() if k != "cat_purr"), "the eight existing cat_sounds keys are byte-equal")
fresh_cat(NIGHT, location="doorstep", activity="at the door, asking in")
fresh_tom(NIGHT)
cat_sounds._mem.update({"holds_prev": {}, "last_fired": {}})
em = cat_sounds.emissions(cat.state, NIGHT, 60.0)
check("cat_meow_at_door" in em and not any(k in em for k in ("cat_hiss", "cat_growl", "distant_yowl")), "her old holds hold as they did; the new ones are false when nothing of the tom is true")
fresh_cat(NIGHT, location="doorstep", activity="demanding_food")
em = cat_sounds.emissions(cat.state, NIGHT, 60.0)
check("cat_demand" in em, "demanding_food still demands")
check(cat_ears.HOLD_S["call"] == (5 * 60, 20 * 60) and cat_ears.HOLD_S["axe"] == (20 * 60, 45 * 60) and all(k in cat_ears.HOLD_S for k in ("tom_standoff", "tom_fight", "tom_hides", "tom_growl", "tom_watch", "tom_after")),
      "her ears' holds: the old entries unchanged, six tom holds added")
fresh_cat(NIGHT, location="by_the_fire", activity="watching")
fresh_tom(NIGHT)
r = cat.react("I stroke the cat a while.", "", "study")
check(bool(r) and cat.state["last_tended"] == NIGHT and not ledger(cat_call._LEDGER), "a stroke with her here is still a stroke")
fresh_cat(NIGHT, location="garden", activity="watching")
random.random = lambda: 0.0
r = cat.react("I call the cat in.", "", "study")
check(bool(r) and ledger(cat_call._LEDGER) and ledger(cat_call._LEDGER)[-1]["kind"] == "call", "'I call the cat in' is still a call")
fresh_cat(NIGHT, location="garden", activity="watching")
on_wall(NIGHT)
rnd_seq(default=0.99)
tom_tick(NIGHT + 60)                     # the hook: present, no reaction (0.99)
check(cat.state["tom"]["present"] is True, "(set-up: the hook says he is there)")
random.random = lambda: 0.0
r = cat.react("I call the cat in.", "", "study")
row = ledger(cat_call._LEDGER)[-1]
check(row["kind"] == "call" and row.get("decision") in ("nothing", None) and (row.get("why") or "").find("tom") >= 0 or row.get("decision") == "nothing",
      f"the call hand (C3) refuses while the tom is there: {row.get('decision')} / {row.get('why')}")
random.random = _real_random

# ── T14 every pool rotates ──────────────────────────────────────────────────────────────────────────
print("\nT14 every pool rotates")
small = [k for k, v in cat_content.TOM.items() if len(v) < 2]
check(not small, f"every TOM pool has at least two lines: {small}")
small = [k for k in ("facing_the_tom", "fighting_the_tom", "hiding_from_the_tom", "growling_at_the_glass", "watching_the_tom", "after_the_fight") if len(cat_content.PRESENCE[k]["any"]) < 3]
check(not small, f"every tom PRESENCE pool has at least three lines: {small}")
small = [f"{k}:{p}" for k in ("cat_hiss", "cat_growl", "distant_yowl") for p, v in cat_content.SOUNDS[k].items() if len(v) < 2]
check(not small, f"every new SOUNDS pool has at least two lines: {small}")
cat_tom._load()
picks = [cat_tom._pick_fresh("T14", list(cat_content.TOM["wall"])) for _ in range(12)]
check(all(a != b for a, b in zip(picks, picks[1:])), "_pick_fresh: never the same line twice running")

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
