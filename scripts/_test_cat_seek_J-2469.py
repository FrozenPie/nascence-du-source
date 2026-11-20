"""
Cat Overhaul C4 -- less of her: hidden spots, crepuscular bouts, seeking as look / listen / go
(J-2469, D-0499 / D-0508, 2026-10-29)
==============================================================================================
HERMETIC: every store core/cat.py (and the modules its tick / look reach) can write is redirected into a
tempfile.mkdtemp() dir OUTSIDE data/ before any write (the scripts/_test_cat_body_J-2465.py pattern); every
cross-module writer the tick can reach is stubbed; the live C:\\Nascence\\data top-level files are
fingerprinted before and after and any change (bar arousal_shadow.jsonl / hud.err.log, written by other
processes) is reported as a LEAK. `import core` BEFORE anything else and core.__file__ must resolve under
this worktree (the F-2570 / jobrun live-store-leak rule).

What it proves (simulated clock inside the machine; the look's own clock is time.time(), so T5-T7 set their
seek stamps relative to it):
  T1  the spots: every hidden spot has a place, a position (cat + cat_sounds frames), a thermal standpoint,
      a phrase, a found pool when reachable; none is in any _VISIBLE set; the house's hidden spots are
      indoors to every sibling module; an old state gains `seek` on load; the step constants
  T2  the chooser: step 0 never hides her; step 1 hides HIDDEN_REST_P[1] of rests; cold / wet -> under
      cover (indoors only when she can get in); hot -> the shade; sun -> the water-butt lid; night -> the
      sheds and the wall; the unreachable share; never the roof in the rain
  T3  a hidden rest HOLDS across ticks; nothing renders her there (presence '', HUD invisible, not
      handleable); the door cross-link does not churn her
  T4  THE GAUGE over simulated days at steps 0 / 1 / 2 (her ears and her harm rolls stubbed: availability
      alone): step 0 reproduces the B1 baseline (~0.71, the live shadow ledger's own 0.68-0.71); step 1
      lands about half (~0.54); step 2 about a third (~0.39) -- the calibration evidence for HIDDEN_REST_P.
      With her ears live (the scratch sim of J-2469's own finding) every step reads ~0.15 lower, which is
      exactly what the seven-live-day read before the step-two flip is for
  T5  LOOK: a cat at a reachable hidden spot in his place is found by chance (FIND_P unknown), then by
      habit (known); the first find is a first; found -> handleable for FOUND_WINDOW_S (is_here,
      affordance), never rendered ambiently; a miss names only where HE looked, never her spot; a named
      spot is looked in first; pools rotate; from another place she is simply not there
  T6  the unreachable: the roof is a glimpse at most (never handleable); the far side of the wall gives
      the wall and nothing
  T7  LISTEN / GO: a carried sound of hers that actually reaches him (RENDER on) is where his ear last had
      her; a miss carries the ear's clause; arriving at that place is a `go` row; a look there carries the
      bonus; shadow rows never set it; the tom's voice never sets it; a stale sound is forgotten
  T8  cat_sounds KEYS holds stay meaningful at the hidden spots (door / demand / thump off the cupboard /
      rustle); every hidden spot carries (has a position); cat_call hears her under the bed
  T9  fur: the exposed hidden spots get wet in the rain; the lean-to does not
  T10 D-0434 no readout: status() keys unchanged; no digit in any SEEK line; no module outside cat.py /
      hud/server.py reads the seek ledger, the step or the chooser
  T11 the fences: life_smoke's redirect list and the HUD registry carry the seek ledger
Run:  python scripts/_test_cat_seek_J-2469.py   (from the worktree root)
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

# J-2506: pin the wall clock to a fixed daytime hour (13:00 local today; PIN_HOUR overrides) so a run at dusk or
# night is the same run. Elapsed real time still advances it. Patches time.time / localtime / strftime defaults.
import os, time as _pin_time
_PIN_REAL = _pin_time.time, _pin_time.localtime, _pin_time.strftime
_pin_lt = _PIN_REAL[1]()
_PIN_BASE = _pin_time.mktime((_pin_lt.tm_year, _pin_lt.tm_mon, _pin_lt.tm_mday, int(os.environ.get("PIN_HOUR", "13")), 0, 0, 0, 0, -1))
_PIN_T0 = _PIN_REAL[0]()
def _pin_now(): return _PIN_BASE + (_PIN_REAL[0]() - _PIN_T0)
_pin_time.time = _pin_now
_pin_time.localtime = lambda s=None: _PIN_REAL[1](_pin_now() if s is None else s)
_pin_time.strftime = lambda f, t=None: _PIN_REAL[2](f, _PIN_REAL[1](_pin_now()) if t is None else t)

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

from core import cat, cat_sounds, cat_call, life, locomotion, sensorium, world_clock, world_traces, life_traces  # noqa: E402
from core import activity_memory, study_life, provisions, cat_ears, cat_tom, cat_harm, cat_referent, cat_content  # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="cat_seek_J2469_"))
print("isolated store dir:", TMP)
cat._STATE_F = TMP / "cat_state.json"
cat._HUNT_LEDGER_F = TMP / "cat_hunt_ledger.jsonl"
cat._FOUND_LEDGER_F = TMP / "cat_found_ledger.jsonl"
cat._FOUND_FLAGS_F = TMP / "life_flags.json"
cat._GAUGE_F = TMP / "cat_presence_gauge.jsonl"
cat._TIER_LEDGER_F = TMP / "cat_tier_ledger.jsonl"
cat._SEEK_LEDGER_F = TMP / "cat_seek_ledger.jsonl"
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
cat_tom._STATE_F = TMP / "cat_tom_state.json"
cat_tom._LEDGER = TMP / "cat_tom_ledger.jsonl"
cat_tom._FLAGS_F = TMP / "life_flags.json"
_cat_harm_mod = cat_harm                 # J-2471's own sibling-harness guard looks for this exact redirect
_cat_harm_mod._LEDGER = TMP / "cat_harm_ledger.jsonl"
_cat_harm_mod._FLAGS_F = TMP / "life_flags.json"
cat_call._LEDGER = TMP / "cat_call_ledger.jsonl"
cat_call._FLAGS_F = TMP / "life_flags.json"
cat_referent._LEDGER = TMP / "cat_referent_ledger.jsonl"
cat_tom.live_on = lambda: False          # the tom stays on the ridge (no random visit can move her)
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
sensorium.state = {"weather": "clear", "wind": "calm", "fire": "out", "location": "study", "asleep": False}
sensorium._daylight = lambda: world_clock.daylight(SIM["now"])
sensorium._season = lambda: SIM["season"]
study_life.door_open = lambda: SIM["door_open"]
cat_sounds._birds_about = lambda: False
cat_ears.prey_about = lambda place, now=None: ["mouse"]
_EARS_TICK = cat_ears.tick

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
    st = {"phase": "kept", "name": "", "bond": 0.65, "location": "by_the_fire", "activity": "sleeping",
          "mood": "content", "appeared_ts": now - 100 * 86400, "last_fed": now - 3600, "last_seen": now,
          "quirks": {"storm_response": "under_desk", "greeting": "chirrup", "fair_spot": "windowsill"},
          "firsts": {"first_lap": 1.0, "first_slow_blink": 1.0, "first_silent_meow": 1.0, "first_shore_follow": 1.0,
                     "first_play": 1.0},
          "last_tended": now, "last_greeted_ts": 0.0, "arc": {}, "saucer": {"has_food": False, "kind": "", "set_ts": 0.0},
          "_was_in": True, "fur_moisture": 0.0, "last_fur_decay_ts": now, "last_bond_decay_ts": now}
    st.update(kw)
    cat._STATE_F.write_text(json.dumps(st), encoding="utf-8")
    return cat._load()


def midnight_local(days_from_now: int = 1) -> float:
    lt = time.localtime(time.time() + days_from_now * 86400)
    return time.mktime((lt.tm_year, lt.tm_mon, lt.tm_mday, 0, 0, 0, 0, 0, -1))


def seek_rows() -> list[dict]:
    f = cat._SEEK_LEDGER_F
    return [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines()] if f.exists() else []


_r0, _c0 = _rnd.random, _rnd.choice
T0 = midnight_local(1)
HS = cat.HIDDEN_SPOTS
REACHABLE = [k for k, v in HS.items() if v["reach"]]
UNREACH = [k for k, v in HS.items() if not v["reach"]]

# ── T1 the spots and the schema ────────────────────────────────────────────────────────────────────
print("\nT1 the hidden spots, their places, positions, the step constants")
check(set(HS) == {"under_the_bed", "cupboard_top", "lean_to", "wood_shed", "hedge_bottom", "water_butt_lid", "roof", "neighbours_wall"},
      "the eight spots of §C4 + D-0508 (six reachable, the roof and the neighbour's side of the wall not)")
check(set(UNREACH) == {"roof", "neighbours_wall"} and HS["roof"]["glimpse"] and not HS["neighbours_wall"]["glimpse"], "the roof is a glimpse; the far side of the wall is not even that")
check(all(k in cat._ZONE_POSITIONS for k in HS), "every hidden spot has a position in cat's frame")
check(all(k in cat_sounds._POS for k in HS), "every hidden spot has a position in cat_sounds' chain frame (her sounds carry from it)")
check(all(k in cat._THERMAL_SPOT and cat._THERMAL_SPOT[k][0] == HS[k]["place"] for k in HS), "every hidden spot has a thermal standpoint in its own place")
check(all(cat.place_of(k) == HS[k]["place"] for k in HS), "place_of() reads one truth for a hidden spot (life's adapter, the legs)")
check(all(k not in locs for k in HS for locs in cat._VISIBLE.values()), "no hidden spot is in any _VISIBLE set")
check(all(not cat.visible_from(p, k) for k in HS for p in ("study", "garden", "wood", "shore")), "visible_from() is False for every hidden spot from every place (the HUD maps draw nothing)")
check(all(k in cat._SPOT_PHRASE for k in HS) and all(f"found_{k}" in cat_content.SEEK for k in REACHABLE), "every spot has a phrase; every reachable spot a found pool")
check(all(len(cat_content.SEEK[k]) >= 3 for k in cat_content.SEEK) and len(cat_content.SEEK["look_spots"]) >= 5, "every SEEK pool holds 3+ lines (rotation is possible)")
for mod in (cat_sounds, cat_ears, cat_tom, cat_harm):
    check({"under_the_bed", "cupboard_top"} <= set(mod._INDOORS), f"{mod.__name__}._INDOORS knows the house's hidden spots")
check(all(k in cat_harm._DIES_WHERE for k in REACHABLE) and not any(k in cat_harm._DIES_WHERE for k in UNREACH), "cat_harm: a death at a reachable spot is findable; on the roof / beyond the wall it is a death away")
check(set(cat._HIDDEN_INDOORS) == {"under_the_bed", "cupboard_top"} and set(cat._HIDDEN_EXPOSED) == {"hedge_bottom", "water_butt_lid", "roof", "neighbours_wall"}, "indoors / exposed partitions")
st = fresh_cat(T0)
check(isinstance(st.get("seek"), dict) and set(st["seek"]) >= {"spots", "last_heard", "found", "his_place"}, "an old state gains the seek block on load")
check(cat.AVAILABILITY_STEP == 2 and cat.HIDDEN_REST_P[2] == 0.60 and set(cat.HIDDEN_REST_P) == {0, 1, 2} and cat.HIDDEN_REST_P[0] == 0.0 < cat.HIDDEN_REST_P[1] < cat.HIDDEN_REST_P[2],
      f"step two ships (AVAILABILITY_STEP 2, D-0805); the table:: {cat.HIDDEN_REST_P}")
ss = cat.seek_status()
check(set(ss) == {"step", "spots", "last_heard", "found", "hidden_now"} and ss["step"] == 2 and ss["hidden_now"] is False, "seek_status() (HUD / tests only)")

# ── T2 the chooser ─────────────────────────────────────────────────────────────────────────────────
print("\nT2 the hidden-rest chooser")
N = 2000
def rolls(step, phase, warmth, weather="clear", location="by_the_fire", door=True, n=N):
    cat.AVAILABILITY_STEP = step
    sensorium.state["weather"] = weather
    SIM["door_open"] = door
    cat.state["location"] = location
    out = []
    for _ in range(n):
        out.append(cat._hidden_rest(phase, {"warmth": warmth}))
    cat.AVAILABILITY_STEP = 2
    sensorium.state["weather"] = "clear"
    SIM["door_open"] = True
    return out
r = rolls(0, "day", 0.5)
check(all(x is None for x in r), "step 0: never a hidden rest (B1 exactly)")
r = rolls(1, "day", 0.5)
share = sum(1 for x in r if x) / N
check(abs(share - cat.HIDDEN_REST_P[1]) < 0.04, f"step 1: hidden share of rests {share:.3f} ~ HIDDEN_REST_P[1] {cat.HIDDEN_REST_P[1]}")
r = rolls(2, "day", 0.5)
share2 = sum(1 for x in r if x) / N
check(abs(share2 - cat.HIDDEN_REST_P[2]) < 0.04, f"step 2: hidden share {share2:.3f} ~ HIDDEN_REST_P[2] {cat.HIDDEN_REST_P[2]}")
picked = [x for x in rolls(1, "day", 0.1) if x]
check(picked and set(picked) <= {"under_the_bed", "cupboard_top", "lean_to", "wood_shed"}, f"cold, in the house: under cover only {sorted(set(picked))}")
check(sum(1 for x in picked if x in ("under_the_bed", "cupboard_top")) > len(picked) * 0.5, "cold, in the house: mostly the house's own covers")
picked = [x for x in rolls(1, "day", 0.1, location="garden", door=False) if x]
check(picked and set(picked) <= {"lean_to", "wood_shed"}, f"cold, out with the door shut: the lean-to or the wood shed, never indoors {sorted(set(picked))}")
picked = [x for x in rolls(1, "day", 0.5, weather="steady rain", location="garden", door=True) if x]
check(picked and set(picked) <= {"under_the_bed", "cupboard_top", "lean_to", "wood_shed"}, f"rain: under cover, never the roof or the exposed spots {sorted(set(picked))}")
picked = [x for x in rolls(1, "day", 0.9) if x]
check(picked and "hedge_bottom" in picked and "water_butt_lid" not in picked and sum(1 for x in picked if x == "hedge_bottom") > len(picked) * 0.4, f"hot: the shade (the hedge bottom first), never the sun on the lid {sorted(set(picked))}")
picked = [x for x in rolls(1, "day", 0.6) if x]
unreach = sum(1 for x in picked if x in UNREACH) / len(picked)
check("water_butt_lid" in picked and sum(1 for x in picked if x == "water_butt_lid") > len(picked) * 0.3, f"a sunny day: the water-butt lid is the favourite {sorted(set(picked))}")
check(abs(unreach - cat.HIDDEN_UNREACHABLE_SHARE) < 0.05, f"the unreachable share {unreach:.3f} ~ HIDDEN_UNREACHABLE_SHARE {cat.HIDDEN_UNREACHABLE_SHARE}")
picked = [x for x in rolls(1, "night", 0.5) if x]
check(picked and "water_butt_lid" not in picked and {"lean_to", "wood_shed"} & set(picked) and "neighbours_wall" in picked, f"night: the sheds, the bed, the wall {sorted(set(picked))}")
picked = [x for x in rolls(1, "night", 0.5, weather="steady rain") if x]
check(picked and not (set(picked) & set(UNREACH)), "a wet night: never the roof or the wall")
# _rest_spot: the hook returns the hidden pick and otherwise the old choice, untouched
_rnd.random = lambda: 0.0
try:
    sp = cat._rest_spot("day", "out", True, {"warmth": 0.5}, "study")
finally:
    _rnd.random = _r0
check(sp in HS, f"_rest_spot takes the hidden pick when the roll says so ({sp})")
_rnd.random = lambda: 0.99
try:
    sp = cat._rest_spot("day", "out", True, {"warmth": 0.5}, "study")
finally:
    _rnd.random = _r0
check(sp not in HS and sp in ("windowsill", "on_the_desk", "under_desk"), f"otherwise the old visible choice stands ({sp})")

# ── T3 a hidden rest holds; nothing renders her ─────────────────────────────────────────────────────
print("\nT3 a hidden rest holds across ticks; she is not rendered, not handleable, not churned by the door")
st = fresh_cat(T0)
cat_ears.tick = lambda state, now: False
try:
    cat.state.update({"location": "under_the_bed", "activity": "sleeping", "mood": "content", "_was_in": True})
    cat.state["body"].update({"energy": 0.5, "hunger": 0.0, "thirst": 0.0, "bout": "sleep", "bout_until": T0 + 20 * 3600, "bout_phase": "day", "last_ts": T0 + 12 * 3600, "warmth": 0.5})
    sensorium.state.update({"location": "study", "asleep": False, "fire": "out", "weather": "clear"})
    locs = set()
    for k in range(0, 12):
        now = T0 + 12 * 3600 + k * 180.0
        SIM["now"] = now
        SIM["door_open"] = (k % 2 == 0)       # the door opens and shuts: she is inside either way
        cat.state["last_fed"] = now
        cat._last_tick = 0.0
        cat.tick(now)
        locs.add(cat.state["location"])
    check(locs == {"under_the_bed"} and cat.state["activity"] == "sleeping", f"asleep under the bed she stays under the bed ({locs})")
    check(cat.presence_line("study") == "", "presence_line renders nothing for a hidden cat in his own room")
    check(not cat.is_here("study") and cat.affordance_line("study") == "", "not handleable, no affordance, until he finds her")
    check(cat.presence_fraction(now=now) == 0.0, "the gauge counts a hidden cat as NOT co-located")
    check(cat.state["_was_in"] is True, "the door cross-link knows under the bed is inside (no asking-out churn)")
    cat.state.update({"location": "lean_to", "activity": "sleeping", "_was_in": False})
    SIM["door_open"] = False
    for k in range(12, 16):
        now = T0 + 12 * 3600 + k * 180.0
        SIM["now"] = now
        cat.state["last_fed"] = now
        cat._last_tick = 0.0
        cat.tick(now)
    check(cat.state["location"] == "lean_to", "asleep in the lean-to with the door shut: she stays in the lean-to (outside to outside)")
    SIM["door_open"] = True
finally:
    cat_ears.tick = _EARS_TICK

# ── T4 the gauge over simulated days: the calibration evidence ──────────────────────────────────────
print("\nT4 cat_presence_fraction over simulated days at steps 0 / 1 / 2 (him in the study 14 of 16 waking hours)")
_HARM_TICK = cat_harm.tick
def simulate(step: int, days: int, seed: int) -> dict:
    """Her availability alone: her ears (C2) and her harm rolls (D-2) are stubbed for the read so an injury or a
    bird reaction does not add its own noise to a 6-day sample (both have their own harnesses)."""
    _rnd.seed(seed)
    cat.AVAILABILITY_STEP = step
    cat_ears.tick = lambda state, now: False
    cat_harm.tick = lambda state, now, phase, door_open: None
    fresh_cat(T0)
    cat.state["body"].update({"energy": 0.7, "hunger": 0.2, "last_ts": T0})
    cat.state["_presence_gauge_ts"] = 0.0
    SIM["season"] = "autumn"
    hidden = waking = 0
    now = T0
    for k in range(0, days * 24 * 20):
        now = T0 + k * 180.0
        SIM["now"] = now
        lt = time.localtime(now)
        h = lt.tm_hour + lt.tm_min / 60.0
        asleep = h < 7.0 or h >= 23.0
        garden = (9.0 <= h < 10.0) or (16.0 <= h < 17.0)
        sensorium.state.update({"asleep": asleep, "location": "garden" if garden else "study",
                                "fire": "burning" if (h >= 18.0 or h < 7.0) else "out", "weather": "clear", "wind": "calm"})
        SIM["door_open"] = 7.0 <= h < 21.0
        if lt.tm_min < 3 and lt.tm_hour in (8, 18):
            cat.state["last_fed"] = now
            cat.eat("cat_food", now)
        cat.tick(now)
        if not asleep:
            waking += 1
            hidden += 1 if cat.state["location"] in HS else 0
    frac = cat.presence_fraction(window_s=days * 86400.0 + 3600.0, now=now)
    cat.AVAILABILITY_STEP = 2
    cat_ears.tick = _EARS_TICK
    cat_harm.tick = _HARM_TICK
    return {"fraction": frac, "hidden_share": round(hidden / max(1, waking), 3)}
RES = {}
for step in (0, 1, 2):
    runs = [simulate(step, 6, seed) for seed in (1, 2, 3)]
    RES[step] = {"fraction": round(sum(r["fraction"] for r in runs) / len(runs), 3),
                 "hidden_share": round(sum(r["hidden_share"] for r in runs) / len(runs), 3), "runs": runs}
    print(f"      step {step}: presence_fraction {RES[step]['fraction']} (runs {[r['fraction'] for r in runs]}), hidden share of waking {RES[step]['hidden_share']}")
check(RES[0]["hidden_share"] == 0.0 and 0.60 <= RES[0]["fraction"] <= 0.80, f"step 0 reproduces the B1 baseline (~0.71 in this harness; the live shadow ledger's own estimate 0.68-0.71): {RES[0]['fraction']}")
check(RES[1]["fraction"] < RES[0]["fraction"] - 0.08 and 0.44 <= RES[1]["fraction"] <= 0.64, f"step 1 steps her down to about half his waking hours: {RES[1]['fraction']}")
check(RES[2]["fraction"] < RES[1]["fraction"] - 0.08 and 0.28 <= RES[2]["fraction"] <= 0.46, f"step 2 (the constant's next row) lands about a third: {RES[2]['fraction']}")
check(0 < RES[1]["hidden_share"] < RES[2]["hidden_share"], f"hidden share of his waking ticks grows with the step: {RES[1]['hidden_share']} -> {RES[2]['hidden_share']}")
gf = cat._GAUGE_F
rows_g = [json.loads(l) for l in gf.read_text(encoding="utf-8").splitlines()] if gf.exists() else []
check(rows_g and all("fraction_24h" in r for r in rows_g), f"the hourly gauge rows landed in the temp file ({len(rows_g)} rows)")
_rnd.seed()

# ── T5 LOOK: found by chance, then by habit ─────────────────────────────────────────────────────────
print("\nT5 the look as a search: found by chance, then by habit; present is not a button")
st = fresh_cat(T0)
cat_ears.tick = lambda state, now: False
NOW = time.time()
try:
    if cat._SEEK_LEDGER_F.exists():
        cat._SEEK_LEDGER_F.unlink()
    cat.state.update({"location": "under_the_bed", "activity": "sleeping", "mood": "content"})
    sensorium.state.update({"location": "study", "asleep": False})
    STUBS["activity"].clear()
    _rnd.random = lambda: 0.0
    try:
        line = cat.look_line("study", "the cat")
    finally:
        _rnd.random = _r0
    rows = seek_rows()
    check("under the bed" in line.lower() and "You look" not in line.split(".")[0][:3] or "under the bed" in line.lower(), f"found under the bed: {line[:90]}...")
    check(rows and rows[-1]["kind"] == "look" and rows[-1]["found"] and rows[-1]["how"] == "found" and rows[-1]["known"] == 0 and rows[-1]["p"] == cat.FIND_P["unknown"],
          f"ledger: a look, found, unknown spot at p {cat.FIND_P['unknown']}: {rows[-1] if rows else None}")
    check(cat.state["seek"]["spots"].get("under_the_bed") == 1 and cat.state["seek"]["found"]["loc"] == "under_the_bed", "he now knows the spot (spots count 1); found set")
    check(any(a[0] == "cat_first" for a in STUBS["activity"]) and any(l in line for l in cat_content.EVENTS["first_found_hidden"]), "the first find is a FIRST: autobiography + the EVENTS line")
    check(cat.is_here("study") and cat.affordance_line("study") != "", "found -> handleable: is_here True, an affordance")
    check(cat.presence_line("study") == "", "still not rendered ambiently (he looks, or nothing)")
    _rnd.random = lambda: 0.5          # < FIND_P known 0.85, > unknown 0.35
    try:
        line2 = cat.look_line("study", "the cat")
    finally:
        _rnd.random = _r0
    rows = seek_rows()
    check(rows[-1]["found"] and rows[-1]["known"] == 1 and rows[-1]["p"] == cat.FIND_P["known"] and cat.state["seek"]["spots"]["under_the_bed"] == 2,
          "second look: found by habit (p known), spots count 2")
    check(not any(l in line2 for l in cat_content.EVENTS["first_found_hidden"]), "no first-line the second time")
    cat.state["seek"]["found"]["ts"] = NOW - cat.FOUND_WINDOW_S - 1
    check(not cat.is_here("study"), "the found window closes: hidden again, not handleable")
    _rnd.random = lambda: 0.9          # > known: a miss even at a known spot
    try:
        miss = cat.look_line("study", "the cat")
    finally:
        _rnd.random = _r0
    rows = seek_rows()
    check(rows[-1]["how"] == "missed_here" and not rows[-1]["found"] and "under the bed" not in miss.lower() and ("sill" in miss or "chair" in miss or "desk" in miss or "hearth" in miss),
          f"a miss names where HE looked (never her spot): {miss[:100]}")
    check("under_the_bed" not in rows[-1]["looked_in"] and all(cat.HIDDEN_SPOTS.get(l, {"place": "study"})["place"] == "study" for l in rows[-1]["looked_in"]), f"looked_in is his order at his place, her spot excluded: {rows[-1]['looked_in']}")
    check(rows[-1]["looked_in"][0] == "windowsill", "her fair_spot comes first in his order")
    # a named spot
    _rnd.random = lambda: 0.9
    try:
        cat.look_line("study", "look for the cat under the bed")
    finally:
        _rnd.random = _r0
    rows = seek_rows()
    check(rows[-1]["named"] == "under_the_bed" and rows[-1]["p"] == cat.FIND_P["named"] and rows[-1]["found"], f"a spot his own words name is looked in first (p named {cat.FIND_P['named']})")
    # an unknown spot missed at 0.5
    cat.state["seek"]["spots"] = {}
    cat.state["seek"]["found"] = None
    cat.state.update({"location": "cupboard_top"})
    _rnd.random = lambda: 0.5
    try:
        cat.look_line("study", "the cat")
    finally:
        _rnd.random = _r0
    rows = seek_rows()
    check(not rows[-1]["found"] and rows[-1]["p"] == cat.FIND_P["unknown"], "an unknown spot: the roll misses at 0.5 (chance first)")
    # pools rotate
    _rnd.random = lambda: 0.0
    try:
        lines = [cat.look_line("study", "the cat") for _ in range(6)]
    finally:
        _rnd.random = _r0
    check(all(lines[i] != lines[i + 1] for i in range(5)) and len(set(lines)) >= 3, "the found pool rotates (no line twice running)")
    misses = []
    _rnd.random = lambda: 0.99
    try:
        for _ in range(6):
            misses.append(cat.look_line("study", "the cat"))
    finally:
        _rnd.random = _r0
    check(all(misses[i] != misses[i + 1] for i in range(5)) and len(set(misses)) >= 3, "the miss pool rotates")
    # from another place she is simply not there
    cat.state["seek"]["found"] = None
    sensorium.state["location"] = "garden"
    _rnd.random = lambda: 0.0
    try:
        far = cat.look_line("garden", "the cat")
    finally:
        _rnd.random = _r0
    rows = seek_rows()
    check(not rows[-1]["found"] and rows[-1]["in_his_place"] is False and "cupboard" not in far.lower() and not cat.is_here("garden"), f"from the garden a cat on the cupboard top is not there: {far[:80]}")
    check(all(cat.HIDDEN_SPOTS.get(l, {"place": "garden"})["place"] == "garden" or cat.place_of(l) == "garden" for l in rows[-1]["looked_in"]), f"looked_in from the garden names garden spots only: {rows[-1]['looked_in']}")
    # the appearing stray and the missing arc keep their own lines
    cat.state["phase"] = "appearing"
    check("The wall top is empty" in cat.look_line("study", "the cat"), "the appearing stray's look is untouched")
    cat.state["phase"] = "kept"
    cat.state["arc"] = {"kind": "gone_missing", "since": NOW, "dur": 3600}
    cat.state["location"] = "gone"
    gm = cat.look_line("study", "the cat")
    check(gm and not seek_rows()[-1]["her_loc"] == "gone", "the missing arc's look is untouched (no seek row)")
    cat.state["arc"] = {}
finally:
    cat_ears.tick = _EARS_TICK

# ── T6 the unreachable ──────────────────────────────────────────────────────────────────────────────
print("\nT6 the roof (a glimpse at most) and the far side of the wall (the wall, and nothing)")
st = fresh_cat(T0)
cat.state.update({"location": "roof", "activity": "sleeping"})
sensorium.state["location"] = "garden"
_rnd.random = lambda: 0.0
try:
    gl = cat.look_line("garden", "the cat")
finally:
    _rnd.random = _r0
rows = seek_rows()
check(("roof" in gl.lower() or "ridge" in gl.lower()) and rows[-1]["how"] == "glimpsed" and rows[-1]["reachable"] is False, f"the roof: a glimpse ({gl[:70]})")
check(not cat.is_here("garden") and cat.affordance_line("garden") == "" and cat.state["seek"]["found"] is None, "glimpsed is not found: never handleable, no affordance")
_rnd.random = lambda: 0.9
try:
    gm = cat.look_line("garden", "the cat")
finally:
    _rnd.random = _r0
check(seek_rows()[-1]["how"] == "missed_here" and "roof" not in gm.lower(), "or missed: the miss never names the roof she is on")
cat.state.update({"location": "neighbours_wall"})
_rnd.random = lambda: 0.0
try:
    wl = [cat.look_line("garden", "the cat") for _ in range(4)]
finally:
    _rnd.random = _r0
rows = seek_rows()
check(all("wall" in l.lower() for l in wl) and all(r["how"] == "beyond_reach" and not r["found"] for r in rows[-4:]), "the far side of the wall: the wall and nothing, every time")
check(not cat.is_here("garden") and all(wl[i] != wl[i + 1] for i in range(3)), "never handleable; the wall pool rotates")

# ── T7 LISTEN / GO ──────────────────────────────────────────────────────────────────────────────────
print("\nT7 listen (a carried sound of hers, RENDER on) and go (he arrives where he heard her)")
st = fresh_cat(T0)
cat_ears.tick = lambda state, now: False
try:
    (TMP / "life_flags.json").write_text(json.dumps({"cat_sounds_render": True}), encoding="utf-8")
    cat_sounds._flags_cache = {"ts": 0.0, "v": {}}
    check(cat_sounds.render_on(), "RENDER on through the (temp) life_flags.json")
    now = time.time()
    SIM["now"], SIM["door_open"] = now, True   # the look's clock is real time; the sim above left SIM on its last night
    cat_sounds._mem.update({"last": now - 120.0, "act": "sleeping", "loc": "lean_to", "holds_prev": {}, "last_fired": {}, "audible": {}})
    cat.state.update({"location": "lean_to", "activity": "demanding_food", "mood": "insistent", "_was_in": False, "last_fed": now - 3600})
    sensorium.state.update({"location": "garden", "asleep": False, "weather": "clear", "wind": "calm"})
    cat._last_tick = now                   # the heartbeat only: no movement tick re-rolls her
    cat.tick(now)
    lh = cat.state["seek"]["last_heard"]
    check(isinstance(lh, dict) and lh["place"] == "garden" and lh["loc"] == "lean_to" and lh["key"] == "cat_demand", f"a sounded, audible row sets last_heard: {lh}")
    srows = [json.loads(l) for l in cat_sounds._LEDGER.read_text(encoding="utf-8").splitlines() if '"cat_demand"' in l]
    srow = srows[-1] if srows else {}
    check(srow.get("kind") == "sounded" and srow.get("audible") and "lean-to" in srow.get("line", "").lower(), f"the carried line says roughly where ({srow.get('line', '')[:70]})")
    # the ear's clause on a miss from the house
    sensorium.state["location"] = "study"
    _rnd.random = lambda: 0.99
    try:
        miss = cat.look_line("study", "the cat")
    finally:
        _rnd.random = _r0
    check("from the garden" in miss and seek_rows()[-1]["last_heard"]["place"] == "garden", f"a miss from the house carries the ear's clause: ...{miss[-80:]}")
    # go: he arrives in the garden
    cat.state["seek"]["his_place"] = "study"
    cat.state["activity"] = "sleeping"
    cat.state["body"].update({"bout": "sleep", "bout_until": now + 20 * 3600, "bout_phase": "day", "last_ts": now, "energy": 0.5, "hunger": 0.0, "thirst": 0.0})
    cat.state["last_fed"] = now
    sensorium.state["location"] = "garden"
    cat._last_tick = 0.0
    cat.tick(now + 60)
    rows = seek_rows()
    gos = [r for r in rows if r["kind"] == "go"]
    check(gos and gos[-1]["his_place"] == "garden" and gos[-1]["from"] == "study" and gos[-1]["she_is_there"] and gos[-1]["hidden"] and gos[-1]["heard_key"] == "cat_demand",
          f"arriving where he heard her is a GO row: {gos[-1] if gos else None}")
    check(cat.state["location"] == "lean_to", "she is still in the lean-to (the go changes nothing about her)")
    _rnd.random = lambda: 0.4             # > unknown 0.35, < 0.35 + bonus 0.10
    try:
        gl = cat.look_line("garden", "the cat")
    finally:
        _rnd.random = _r0
    r = seek_rows()[-1]
    check(r["found"] and abs(r["p"] - (cat.FIND_P["unknown"] + cat.FIND_HEARD_BONUS)) < 0.001 and "lean-to" in gl.lower(), f"a look where he heard her carries the bonus: p {r['p']}")
    # a second arrival without a fresh sound is not a go
    n_go = len(gos)
    cat.state["seek"]["last_heard"]["ts"] = now - cat.LAST_HEARD_FRESH_S - 10
    cat.state["seek"]["his_place"] = "study"
    cat._last_tick = 0.0
    cat.tick(now + 240)
    check(len([r for r in seek_rows() if r["kind"] == "go"]) == n_go, "a stale sound: arriving is not a go")
    _rnd.random = lambda: 0.99
    try:
        sensorium.state["location"] = "study"
        miss2 = cat.look_line("study", "the cat")
    finally:
        _rnd.random = _r0
    check("from the garden" not in miss2 and seek_rows()[-1]["last_heard"] is None, "a stale sound is forgotten: no clause")
    # shadow: a would_sound row never sets it
    cat.state["seek"]["last_heard"] = None
    (TMP / "life_flags.json").write_text(json.dumps({"cat_sounds_render": False}), encoding="utf-8")
    cat_sounds._flags_cache = {"ts": 0.0, "v": {}}
    cat_sounds._mem.update({"last": now + 300 - 120.0, "act": "sleeping", "loc": "lean_to", "holds_prev": {}, "last_fired": {}})
    cat.state.update({"location": "lean_to", "activity": "demanding_food"})
    sensorium.state["location"] = "garden"
    cat._last_tick = now + 300
    cat.tick(now + 300)
    srow = [json.loads(l) for l in cat_sounds._LEDGER.read_text(encoding="utf-8").splitlines()][-1]
    check(srow["kind"] == "would_sound" and cat.state["seek"]["last_heard"] is None, "shadow (RENDER off): a would_sound row never sets last_heard")
    # the tom's voice is not hers; a leg has no place
    cat._note_heard([{"kind": "sounded", "audible": True, "key": "distant_yowl", "cat": {"loc": "lean_to"}, "his": {"place": "garden"}}], now)
    check(cat.state["seek"]["last_heard"] is None, "the tom's yowl never sets last_heard")
    cat._note_heard([{"kind": "sounded", "audible": True, "key": "cat_trill", "cat": {"loc": "in_transit"}, "his": {"place": "garden"}}], now)
    check(cat.state["seek"]["last_heard"] is None, "a sound from a leg (no place) is not a place to go to")
    cat._note_heard([{"kind": "sounded", "audible": True, "key": "cat_trill", "cat": {"loc": "away_hunting"}, "his": {"place": "study"}, "bearing": "N"}], now)
    check((cat.state["seek"]["last_heard"] or {}).get("place") == "garden", "a sound from out past the wall is 'the garden' (reached through it)")
    # cat_call: she hears under the bed
    cat.state.update({"location": "under_the_bed", "activity": "sleeping"})
    cat.state["body"]["energy"] = 0.9
    check(cat_call.hearing(cat.state) == "asleep" and cat_call._her_origin(cat.state) is not None, "cat_call: a call reaches a cat asleep under the bed (her gate, her position)")
finally:
    cat_ears.tick = _EARS_TICK
    (TMP / "life_flags.json").write_text(json.dumps({}), encoding="utf-8")
    cat_sounds._flags_cache = {"ts": 0.0, "v": {}}

# ── T8 cat_sounds holds at the hidden spots ─────────────────────────────────────────────────────────
print("\nT8 cat_sounds KEYS holds stay meaningful at the hidden spots; every spot carries")
now = time.time()
def emis(loc, act, prev_loc=None, prev_act=None):
    cat_sounds._mem.update({"act": prev_act or act, "loc": prev_loc or loc, "holds_prev": {}, "last_fired": {}, "greet_ts": 0.0, "answer_ts": 0.0})
    return cat_sounds.emissions({"location": loc, "activity": act, "last_fed": 0.0, "last_greeted_ts": 0.0, "call": {}}, now, 60.0)
check("cat_meow_at_door" in emis("under_the_bed", "at the door, asking out"), "asking out from the house's hidden spot still meows")
check("cat_demand" in emis("lean_to", "demanding_food"), "demanding food from the lean-to still cries")
check("cat_thump" in emis("by_the_fire", "watching", prev_loc="cupboard_top", prev_act="sleeping"), "coming off the cupboard top is a thump")
check("cat_storm_rustle" in emis("under_the_bed", "storm_hide"), "the storm rustle holds under the bed")
for k in HS:
    c = cat_sounds.carry("cat_demand", k, "garden", cat_sounds._HIS["garden"]["_"], True, False, "clear", "calm")
    check(c.get("dist_m") is not None and c.get("why") != "no position", f"{k}: a sound carries from it (dist {c.get('dist_m')} m, {c.get('why')})")
check(cat_sounds._here("under_the_bed", "study", False) and not cat_sounds._here("lean_to", "study", True), "the acoustic same-room test: under the bed is here; the lean-to is carried")
ln = cat_sounds.line_for("cat_demand", False, "lean_to", "the cat")
check("from the lean-to" in ln.lower(), f"the carried line's {{dir}} for the lean-to: {ln[:80]}")

# ── T9 fur at the exposed spots ─────────────────────────────────────────────────────────────────────
print("\nT9 rain reaches the exposed hidden spots, not the lean-to")
st = fresh_cat(T0)
cat_ears.tick = lambda state, now: False
try:
    sensorium.state.update({"location": "study", "weather": "steady rain", "asleep": False})
    for loc, wet_expected in (("hedge_bottom", True), ("lean_to", False)):
        cat.state.update({"location": loc, "activity": "sleeping", "fur_moisture": 0.0})
        cat.state["body"].update({"bout": "sleep", "bout_until": T0 + 20 * 3600, "bout_phase": "day", "last_ts": T0 + 12 * 3600, "energy": 0.5, "hunger": 0.0, "thirst": 0.0, "warmth": 0.5})
        for k in range(0, 6):
            now = T0 + 12 * 3600 + k * 180.0
            SIM["now"] = now
            cat.state["last_fed"] = now
            cat._last_tick = 0.0
            cat.tick(now)
        check((cat.state["fur_moisture"] > 0.0) is wet_expected and cat.state["location"] == loc, f"{loc}: fur_moisture {cat.state['fur_moisture']} in steady rain (wet expected {wet_expected})")
    sensorium.state["weather"] = "clear"
finally:
    cat_ears.tick = _EARS_TICK

# ── T10 D-0434 no readout ───────────────────────────────────────────────────────────────────────────
print("\nT10 no readout (D-0434)")
check(set(cat.status()) == {"phase", "name", "bond", "location", "activity"}, "status() -- the one cat read in his prompt path -- keys unchanged")
bad = []
for key, pool in cat_content.SEEK.items():
    for tpl in pool:
        s = tpl.replace("{her}", "the cat").replace("{spots}", "the sill, the chair").replace("{dir}", "from the garden")
        if re.search(r"\d", s) or "{" in s or re.search(r"\b(hidden|chance|per cent|percent|probab)", s, re.I):
            bad.append((key, s))
for tpl in cat_content.EVENTS["first_found_hidden"]:
    if re.search(r"\d", tpl):
        bad.append(("first_found_hidden", tpl))
check(not bad, f"no digit, no unfilled token, no odds-word in any SEEK line ({sum(len(p) for p in cat_content.SEEK.values())} lines)")
readers = []
for p in sorted((ROOT / "core").glob("*.py")) + sorted((ROOT / "nodes").glob("*.py")):
    txt = p.read_text(encoding="utf-8", errors="replace")
    if p.name != "cat.py" and any(w in txt for w in ("cat_seek_ledger", "AVAILABILITY_STEP", "HIDDEN_REST_P", "seek_status", "_hidden_rest", "last_heard")):
        readers.append(p.name)
check(not readers, f"no module outside cat.py reads the seek ledger, the step, the chooser or last_heard {readers}")

# ── T11 the fences ──────────────────────────────────────────────────────────────────────────────────
print("\nT11 the fences: life_smoke's redirect list and the HUD registry")
smoke = (ROOT / "scripts" / "life_smoke.py").read_text(encoding="utf-8")
check('"_SEEK_LEDGER_F"' in smoke, "scripts/life_smoke.py redirects core.cat._SEEK_LEDGER_F")
hud_src = (ROOT / "hud" / "server.py").read_text(encoding="utf-8")
check('("cat_seek", "staged"' in hud_src and '"cat_seek_ledger.jsonl"' in hud_src, "hud/server.py MONITOR_REGISTRY carries the seek ledger")
check(cat._SEEK_LEDGER_F == TMP / "cat_seek_ledger.jsonl" and cat._SEEK_LEDGER_F.exists(), "every seek row of this run landed in the temp dir")

# ── canary ──────────────────────────────────────────────────────────────────────────────────────────
FP_AFTER = _fingerprint()
leaks = sorted(n for n in set(FP_BEFORE) | set(FP_AFTER) if n not in _IGNORE and FP_BEFORE.get(n) != FP_AFTER.get(n))
check(not leaks, f"live C:\\Nascence\\data untouched (LEAKS: {leaks})")

print(f"\n{OKS} ok, {len(FAILS)} FAIL")
for f in FAILS:
    print("   FAIL:", f)
sys.exit(1 if FAILS else 0)
