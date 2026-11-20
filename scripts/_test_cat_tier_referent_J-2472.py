"""
Cat Overhaul D-1 + B2 -- the companion tier opens from bond; which cat he meant (J-2472, D-0505 (c), 2026-10-28)
================================================================================================================
HERMETIC: every store core/cat.py, core/cat_referent.py, core/geometry_census.py and core/life_traces.py can write
is redirected into a tempfile.mkdtemp() dir OUTSIDE data/ before any write (the J-2465 pattern); every cross-module
writer the exercised paths can reach (activity_memory.record, memory.store.store_fragment, commitment_trials.
register_acceptance, life_traces.add_carcass, world_traces.create_trace, life.note_deed) is stubbed; the live
C:\\Nascence\\data top-level files are fingerprinted before and after and any change (bar arousal_shadow.jsonl /
hud.err.log, written by other processes) is reported as a LEAK. `import core` BEFORE anything else and
core.__file__ must resolve under this worktree.

What it proves:
  T1  companion_tier(): kept + bond < 0.70 -> closed; kept + 0.70 -> open; named companion -> open at any bond;
      appearing / absent -> closed; `phase` never changed by the predicate
  T2  felt_note / felt_state render for a KEPT, UNNAMED cat at bond 0.80 on the rug; "" / None at 0.69; a named
      companion decayed below 0.4 still gets nothing (the floor stays); the FELT lines rotate and carry no digit;
      the tier ledger logs felt ONCE per (location, tier) with bond / phase / bar
  T3  the slow blink and the silent meow render for a kept unnamed cat at bond 0.95 (600 presence lines) and never
      at 0.69; each tier row carries bond >= its own bar
  T4  the gone_missing arc can begin for a kept unnamed cat at bond 0.90 and never at 0.69 (random forced);
      the six-hour "no sign of her" line renders at 0.80, rotates, and not at 0.69
  T5  the naming latch is untouched: "I will call her Ash" still names her, sets phase companion, registers R1
      (stubbed); the standing-occasion line still rides KEPT presence lines with the tier open, and never after the
      name; distant-cat naming still refused
  T6  cat_referent.classify: the table (grey / tom / both / undistinguished / None); a bare "Tom" or a "black sky"
      means no cat; her learned name counts; the hooks record (look target, react, her naming, the census stamp,
      life_traces.give_name on a cat individual) and the dedupe holds; summary() counts
  T7  D-0434 no readout: status() keys unchanged; no digit in any felt / six-hour line; the recorder never changes
      what look_line returns; nothing under nodes/ imports cat_referent or reads either ledger; cat_sounds holds
      still fire from the unlocked machine (demanding_food -> cat_demand)
  T8  D-0505 defeater sweep: across every tier row this run, phase kept => bond >= COMPANION_BOND
Run:  python scripts/_test_cat_tier_referent_J-2472.py   (from the worktree root)
"""
from __future__ import annotations
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789: no write to the tree's data/

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

from core import cat, cat_referent, cat_sounds, cat_content, life, locomotion, sensorium, world_clock, world_traces, life_traces  # noqa: E402
from core import activity_memory, thermal, study_life, provisions, geometry_census, commitment_trials  # noqa: E402
import core.memory.store as _mstore  # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="cat_tier_J2472_"))
print("isolated store dir:", TMP)
cat._STATE_F = TMP / "cat_state.json"
cat._HUNT_LEDGER_F = TMP / "cat_hunt_ledger.jsonl"
cat._FOUND_LEDGER_F = TMP / "cat_found_ledger.jsonl"
cat._FOUND_FLAGS_F = TMP / "life_flags.json"
cat._GAUGE_F = TMP / "cat_presence_gauge.jsonl"
cat._TIER_LEDGER_F = TMP / "cat_tier_ledger.jsonl"
cat_referent._LEDGER = TMP / "cat_referent_ledger.jsonl"
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
from core import cat_ears  # noqa: E402  -- C2 (J-2467): cat.tick -> cat_ears.tick writes data/cat_reactions.jsonl (fenced); redirected here per life_smoke's own rule
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
geometry_census._LOG = TMP / "geometry_tuples.jsonl"
geometry_census._DATA = TMP                      # its _read_json("cat_state.json") reads OUR cat state, never live
from core import world_substrate, world_objects  # noqa: E402
world_substrate._SUBSTRATE_F = TMP / "world_substrate.json"
world_objects._OBJECTS_F = TMP / "world_objects.json"
STUBS = {"activity": [], "carcass": [], "trace": [], "deed": [], "fragment": [], "r1": []}
activity_memory.record = lambda *a, **k: STUBS["activity"].append(a)
life_traces.add_carcass = lambda *a, **k: STUBS["carcass"].append(a)
world_traces.create_trace = lambda *a, **k: STUBS["trace"].append(a)
life.note_deed = lambda *a, **k: STUBS["deed"].append(a)
_mstore.store_fragment = lambda *a, **k: STUBS["fragment"].append(k)
commitment_trials.register_acceptance = lambda *a, **k: STUBS["r1"].append(a)

SIM = {"now": 0.0, "door_open": True, "season": "summer"}
sensorium.state = {"weather": "clear", "wind": "calm", "fire": "lit", "location": "study", "asleep": False}
sensorium._daylight = lambda: world_clock.daylight(SIM["now"])
sensorium._season = lambda: SIM["season"]
study_life.door_open = lambda: SIM["door_open"]
cat_sounds._birds_about = lambda: False

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
    cat._tier_mem["felt_key"] = None
    st = {"phase": "kept", "name": "", "bond": 0.8, "location": "by_the_fire", "activity": "watching",
          "mood": "content", "appeared_ts": now - 100 * 86400, "last_fed": now - 3600, "last_seen": now,
          "name_invited": True,
          "quirks": {"storm_response": "under_desk", "greeting": "chirrup", "fair_spot": "windowsill"},
          "firsts": {"first_lap": 1.0, "first_slow_blink": 1.0, "first_silent_meow": 1.0, "first_shore_follow": 1.0,
                     "first_play": 1.0},
          "last_tended": now, "last_greeted_ts": time.time(), "arc": {}, "saucer": {"has_food": False, "kind": "", "set_ts": 0.0},
          "_was_in": True, "fur_moisture": 0.0, "last_fur_decay_ts": now, "last_bond_decay_ts": now}
    st.update(kw)
    cat._STATE_F.write_text(json.dumps(st), encoding="utf-8")
    return cat._load()


def tier_rows() -> list[dict]:
    if not cat._TIER_LEDGER_F.exists():
        return []
    return [json.loads(l) for l in cat._TIER_LEDGER_F.read_text(encoding="utf-8").splitlines() if l.strip()]


def ref_rows() -> list[dict]:
    if not cat_referent._LEDGER.exists():
        return []
    return [json.loads(l) for l in cat_referent._LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()]


def midday_local(days_from_now: int = 1) -> float:
    lt = time.localtime(time.time() + days_from_now * 86400)
    return time.mktime((lt.tm_year, lt.tm_mon, lt.tm_mday, 13, 0, 0, 0, 0, -1))


T0 = midday_local(1)
SIM["now"] = T0
assert sensorium._daylight() == "day", sensorium._daylight()

# ── T1 the predicate ─────────────────────────────────────────────────────────────────────────────────
print("\nT1 companion_tier()")
check(cat.COMPANION_BOND > cat.NAME_BOND, f"COMPANION_BOND {cat.COMPANION_BOND} sits above NAME_BOND {cat.NAME_BOND} (the occasion opens first)")
for ph, bond, name, want in (("kept", 0.69, "", False), ("kept", 0.70, "", True), ("kept", 1.0, "", True),
                             ("companion", 0.55, "Ash", True), ("companion", 0.3, "Ash", True),
                             ("appearing", 1.0, "", False), ("absent", 1.0, "", False)):
    fresh_cat(T0, phase=ph, bond=bond, name=name)
    check(cat.companion_tier() is want and cat.state["phase"] == ph, f"{ph} bond {bond} name {name!r} -> tier {want}; phase untouched")

# ── T2 felt_note / felt_state ────────────────────────────────────────────────────────────────────────
print("\nT2 felt_note and felt_state from bond")
fresh_cat(T0, bond=0.8)
fn = cat.felt_note()
check(fn.strip() != "" and cat.felt_state() == ("by_the_fire", "high"), f"kept unnamed 0.80 on the rug: felt_note renders, felt_state {cat.felt_state()}")
check(not re.search(r"\d", fn), "the felt line carries no digit")
check(cat.state["phase"] == "kept" and not cat.state.get("name"), "she is still kept and unnamed after feeling")
rows = tier_rows()
check(len(rows) == 1 and rows[0]["kind"] == "felt" and rows[0]["phase"] == "kept" and rows[0]["bond"] == 0.8
      and rows[0]["bar"] == cat.COMPANION_BOND and rows[0]["tier"] == "high" and rows[0]["named"] is False,
      f"tier ledger: one felt row with bond / phase / bar: {rows[0] if rows else None}")
for _ in range(5):
    cat.felt_note()
check(len(tier_rows()) == 1, "felt logs ONCE per (location, tier), not per prompt")
cat.state["location"] = "on_your_lap"
cat.felt_note()
check(len(tier_rows()) == 2 and tier_rows()[-1]["location"] == "on_your_lap", "a move to the lap is a new felt row")
seen = set()
for _ in range(40):
    cat.state["bond"] = 0.72 if _ % 2 else 0.9
    cat.state["location"] = "by_the_fire"
    seen.add(cat.felt_note().strip())
check(len(seen) >= 4 and all(not re.search(r"\d", s) for s in seen), f"FELT lines rotate across both tiers ({len(seen)} distinct), none with a digit")
fresh_cat(T0, bond=0.69)
check(cat.felt_note() == "" and cat.felt_state() is None, "kept unnamed 0.69: nothing (below the tier's own bar)")
fresh_cat(T0, phase="companion", name="Ash", bond=0.35)
check(cat.felt_note() == "" and cat.felt_state() is None, "a named companion decayed to 0.35: nothing (the 0.4 floor stays)")
fresh_cat(T0, phase="companion", name="Ash", bond=0.55)
check(cat.felt_note().strip() != "" and cat.felt_state() == ("by_the_fire", "mid"), "a named companion at 0.55 feels, mid tier (as before)")

# ── T3 the blink and the silent meow ─────────────────────────────────────────────────────────────────
print("\nT3 the slow blink and the silent meow")
blink_pool = set(l.replace("{her}", "the cat") for l in (cat_content.EVENTS.get("slow_blink") or []))
meow_pool = set(l.replace("{her}", "the cat") for l in (cat_content.EVENTS.get("silent_meow") or []))
check(len(blink_pool) >= 2 and len(meow_pool) >= 2, f"corpus pools: slow_blink {len(blink_pool)}, silent_meow {len(meow_pool)}")


def presence_sweep(n: int) -> dict:
    kinds = {"slow_blink": 0, "silent_meow": 0}
    for _ in range(n):
        cat.state["location"], cat.state["activity"] = "by_the_fire", "watching"
        cat.state["last_seen"] = time.time()
        line = cat.presence_line("study")
        if line in blink_pool:
            kinds["slow_blink"] += 1
        if line in meow_pool:
            kinds["silent_meow"] += 1
    return kinds


random.seed(2472)
fresh_cat(T0, bond=0.95)
n_before = len(tier_rows())
k = presence_sweep(600)
rows = [r for r in tier_rows()[n_before:] if r["kind"] in ("slow_blink", "silent_meow")]
check(k["slow_blink"] >= 1 and k["silent_meow"] >= 1, f"kept unnamed 0.95 over 600 lines: blink {k['slow_blink']}, silent meow {k['silent_meow']}")
check(len(rows) == k["slow_blink"] + k["silent_meow"] and all(r["phase"] == "kept" and r["bond"] == 0.95 for r in rows), "each render logged a tier row with bond / phase")
check(all((r["kind"] != "slow_blink" or r["bond"] >= 0.75) and (r["kind"] != "silent_meow" or r["bond"] >= 0.9) for r in rows), "each signal keeps its own bond bar")
fresh_cat(T0, bond=0.69)
n_before = len(tier_rows())
k = presence_sweep(600)
check(k["slow_blink"] == 0 and k["silent_meow"] == 0 and len(tier_rows()) == n_before, "kept unnamed 0.69 over 600 lines: no blink, no silent meow, no tier row")
fresh_cat(T0, bond=0.8)
k = presence_sweep(600)
check(k["slow_blink"] >= 1 and k["silent_meow"] == 0, f"kept unnamed 0.80: the blink ({k['slow_blink']}) but never the silent meow (its own 0.9 bar)")

# ── T4 the missing arc and the six-hour line ─────────────────────────────────────────────────────────
print("\nT4 the gone_missing arc and the six-hour line")
_real_random = random.random


def _forced_arc(bond: float) -> bool:
    fresh_cat(T0, bond=bond, location="garden", activity="watching")
    cat.state["body"]["hunger"] = 0.1
    cat.state["last_fed"] = T0 - 600
    random.random = lambda: 0.0
    try:
        for i in range(6):
            cat._last_tick = 0.0
            cat.tick(T0 + i * 200)
            if (cat.state.get("arc") or {}).get("kind") == "gone_missing":
                return True
    finally:
        random.random = _real_random
    return False


n_before = len(tier_rows())
check(_forced_arc(0.9) is True, "kept unnamed 0.90 on a fair day: the gone_missing arc can begin (random forced)")
arcs = [r for r in tier_rows()[n_before:] if r["kind"] == "missing_arc"]
check(len(arcs) == 1 and arcs[0]["phase"] == "kept" and arcs[0]["bond"] == 0.9 and arcs[0].get("dur_h"), f"missing_arc tier row: {arcs[0] if arcs else None}")
check(cat.state["location"] == "gone" and cat.state["activity"] == "missing", "she is gone / missing")
n_before = len(tier_rows())
check(_forced_arc(0.69) is False and len(tier_rows()) == n_before, "kept unnamed 0.69: the arc never begins even with random forced")
fresh_cat(T0, bond=0.8, location="wood", activity="hunting")
cat.state["last_seen"] = time.time() - 7 * 3600
six = set()
for _ in range(30):
    six.add(cat.presence_line("study"))
six.discard("")
check(len(six) >= 2 and all("morning" in s for s in six) and all(not re.search(r"\d", s) for s in six), f"the six-hour line renders for kept unnamed 0.80 and rotates ({len(six)} distinct), no digit")
check(any(r["kind"] == "six_hour" and r["bond"] == 0.8 for r in tier_rows()), "six_hour tier rows logged")
fresh_cat(T0, bond=0.69, location="wood", activity="hunting")
cat.state["last_seen"] = time.time() - 7 * 3600
check(all(cat.presence_line("study") == "" for _ in range(30)), "kept unnamed 0.69: no six-hour line")

# ── T5 the naming latch and the standing occasion are untouched ──────────────────────────────────────
print("\nT5 the name stays the R1 act; the occasion still rides kept lines")
fresh_cat(T0, bond=0.9, location="by_the_fire", activity="watching")
occ = 0
for _ in range(200):
    cat.state["location"], cat.state["activity"], cat.state["last_seen"] = "by_the_fire", "watching", time.time()
    if "name" in cat.presence_line("study"):
        occ += 1
check(occ >= 10, f"the standing occasion still rides KEPT presence lines with the tier open ({occ}/200)")
cat._prev_ref_txt = ""
r = cat.react("The black cat perches on the wall.", "", "study")
r2 = cat.react("I will call her Smoke.", "", "study")
check(not cat.state.get("name"), "a name aimed at the black cat through anaphora is still refused (F-1050 guard)")
cat._prev_ref_txt = ""
r = cat.react("I will call her Ash.", "", "study")
check(cat.state.get("name") == "Ash" and cat.state["phase"] == "companion" and "Ash" in (r or ""), f"the latch: 'I will call her Ash' names her, phase companion: {r!r}")
check(STUBS["r1"] and STUBS["r1"][-1][0] == "R1_name_the_cat" and STUBS["fragment"], "R1 registered + the deed fragment (stubbed)")
check(cat.companion_tier() is True, "a named companion is in the tier outright")
occ = 0
for _ in range(200):
    cat.state["location"], cat.state["activity"], cat.state["last_seen"] = "by_the_fire", "watching", time.time()
    if "no name" in cat.presence_line("study") or "nameless" in cat.presence_line("study"):
        occ += 1
check(occ == 0, "after the name: the occasion never again")

# ── T6 which cat he meant ────────────────────────────────────────────────────────────────────────────
print("\nT6 cat_referent: classify + the hooks")
C = lambda t, her="", tom="": cat_referent.classify(t, her_name=her, tom_name=tom)   # noqa: E731
table = (
    ("the cat is on the rug", "undistinguished"), ("The stray came to the door.", "undistinguished"),
    ("I stroke my little cat.", "grey"), ("your grey one is asleep", "grey"), ("the grey cat on my lap", "grey"),
    ("the little one with the notched ear", "grey"), ("the black cat on the wall", "tom"), ("that cat on the ridge again", "tom"),
    ("the other cat is back", "tom"), ("an old scarred tom at the saucer", "tom"), ("the tomcat yowls at three", "tom"),
    ("the grey one hisses at the black one", "both"), ("a black sky over the garden", None), ("Tom wrote to me", None),
    ("the wind in the harakeke", None), ("", None), ("copy-cat behaviour", None),
)
for t, want in table:
    got = C(t)
    check(got == want, f"classify({t!r}) -> {got!r} (want {want!r})")
check(C("Ash is asleep on the desk", her="ash") == "grey" and C("Smoke on the wall", tom="smoke") == "tom" and C("ash in the grate", her="") is None,
      "a learned name counts for either of them; without the name, 'ash' is the grate")
check(cat_referent.classify("I will call her Ash.") is not None, "classify with no names passed reads them (fail-open) and still sees a pronoun-only line as no cat or a cat")
ref0 = len(ref_rows())
fresh_cat(T0, bond=0.8, location="by_the_fire", activity="watching")
cat_referent._mem["last"].clear()
out1 = cat.look_line("study", "the black cat")
out2 = cat.look_line("study", "the cat")
out3 = cat.look_line("study", "my little cat")
rr = ref_rows()[ref0:]
check([r["source"] for r in rr] == ["look"] * 3 and [r["which"] for r in rr] == ["tom", None, "grey"]
      and [r["distinguished"] for r in rr] == [True, False, True] and all(r["place"] == "study" for r in rr),
      f"look targets recorded: {[(r['which'], r['distinguished']) for r in rr]}")
check(("black cat" in out1 or "no cat out there" in out1) and "black" not in out3 and "black" not in out2 and all(not re.search(r"\d", o) for o in (out1, out2, out3)),
      f"look_line's answers unchanged in kind (the distant guard still routes to distant_look; the other two are hers), no digit: {out1[:50]!r}")
ref0 = len(ref_rows())
cat._prev_ref_txt = ""
cat.react("I stroke the grey cat by the fire.", "", "study")
rr = ref_rows()[ref0:]
check(len(rr) == 1 and rr[0]["source"] == "react" and rr[0]["which"] == "grey", f"react records his hand's referent: {rr}")
ref0 = len(ref_rows())
cat.react("There is nothing here at all.", "", "study")
check(len(ref_rows()) == ref0, "a thought that means no cat records nothing")
named_rows = [r for r in ref_rows() if r["source"] == "naming"]
check(len(named_rows) == 1 and named_rows[0]["which"] == "grey" and "Ash" in named_rows[0]["text"], f"her naming (T5) recorded once, grey: {named_rows}")
# the census stamp
ref0 = len(ref_rows())
geometry_census._last_ts, geometry_census._last_thought = 0.0, ""
row = geometry_census.snapshot(source="idle", thought="The black cat is on the far wall again, watching nothing.")
check(isinstance(row, dict) and row.get("cat_ref") == "tom", f"census stamps cat_ref tom: {row.get('cat_ref') if row else row}")
geometry_census._last_ts = 0.0
row2 = geometry_census.snapshot(source="idle", thought="The rain has come in off the sea.")
check(isinstance(row2, dict) and row2.get("cat_ref") is None, "a thought with no cat: cat_ref None")
geometry_census._last_ts = 0.0
row3 = geometry_census.snapshot(source="idle", thought="The cat is asleep on the chair.")
check(isinstance(row3, dict) and row3.get("cat_ref") == "undistinguished", "a bare 'the cat': undistinguished")
rr = [r for r in ref_rows()[ref0:] if r["source"] == "census"]
check([r["which"] for r in rr] == ["tom", None] and [r["distinguished"] for r in rr] == [True, False], f"census ledger rows: {[(r['which'], r['distinguished']) for r in rr]}")
# dedupe
ref0 = len(ref_rows())
cat_referent.record("look", "the black cat", now=T0)
cat_referent.record("look", "the black cat", now=T0 + 10)
cat_referent.record("look", "the black cat", now=T0 + 200)
check(len(ref_rows()) - ref0 == 2, "the same text from the same source within 90 s is one row")
# life_traces.give_name on a cat individual (J-2470's row, any key with tom/cat in it)
life._load()
life.state = life._load()
life.state.setdefault("individuals", {})["tom"] = {"place": "garden", "since": T0 - 86400, "sightings": 12, "name": ""}
life.state["individuals"]["hedgehog"] = {"place": "garden", "since": T0 - 86400, "sightings": 3, "name": ""}
ref0 = len(ref_rows())
res_tom = life_traces.give_name("tom", "Smoke", now=T0)
res_hog = life_traces.give_name("hedgehog", "Bramble", now=T0)
rr = ref_rows()[ref0:]
check("Smoke" in res_tom and "Bramble" in res_hog, f"give_name still names both: {res_tom[:40]!r} / {res_hog[:40]!r}")
check(len(rr) == 1 and rr[0]["source"] == "naming" and rr[0]["which"] == "tom" and rr[0].get("name") == "Smoke" and rr[0].get("key") == "tom",
      f"only the CAT individual's naming is a referent row (tom): {rr}")
check(cat_referent._name_of_tom() == "smoke", "the tom's learned name is read back from life state")
check(cat_referent.classify("Smoke is on the wall") == "tom", "...and counts as distinguishing him")
s = cat_referent.summary(window_s=10 * 86400, now=time.time())
check(s["rows"] >= 8 and s["grey"] >= 3 and s["tom"] >= 3 and s["undistinguished"] >= 2 and 0 < s["share_distinguished"] < 1 and s["by_source"].get("look", 0) >= 3,
      f"summary counts: {s}")

# ── T7 no readout ────────────────────────────────────────────────────────────────────────────────────
print("\nT7 D-0434 no readout + the holds")
check(set(cat.status().keys()) == {"phase", "name", "bond", "location", "activity"}, "status() keys unchanged")
bad = []
for d in ("nodes", "core"):
    for p in (ROOT / d).rglob("*.py"):
        src = p.read_text(encoding="utf-8", errors="replace")
        if p.name in ("cat_referent.py",):
            continue
        # write-side recorders only: cat.py, the census, give_name, and the tom (J-2470: his hand reaching
        # for the OTHER cat is a referent too). The read-side guards below stay strict for every file.
        if "cat_referent" in src and p.name not in ("cat.py", "geometry_census.py", "life_traces.py", "cat_tom.py"):
            bad.append(f"{p}: imports cat_referent")
        if ("cat_tier_ledger" in src or "_TIER_LEDGER_F" in src) and p.name != "cat.py":
            bad.append(f"{p}: reads the tier ledger")
        if "cat_referent_ledger" in src and p.name != "cat_referent.py":
            bad.append(f"{p}: reads the referent ledger")
        if ".summary(" in src and "cat_referent" in src and p.name != "cat_referent.py":
            bad.append(f"{p}: reads the referent summary")
check(not bad, f"only cat.py / geometry_census.py / life_traces.py touch the recorder; nothing reads either ledger or summary(): {bad}")
hud_src = (ROOT / "hud" / "server.py").read_text(encoding="utf-8", errors="replace")
check('("cat_tier", "staged"' in hud_src and '("cat_referent", "staged"' in hud_src, "the HUD registry carries both staged cards")
# cat_sounds holds still fire from the unlocked machine
fresh_cat(T0, bond=0.8, location="doorstep", activity="demanding_food")
cat_sounds._mem.clear()
cat_sounds._mem.update({"holds_prev": {}, "last_fired": {}})
em = cat_sounds.emissions(cat.state, T0, 60.0)
check("cat_demand" in em, f"demanding_food -> cat_demand still fires on the unlocked state: {em}")
cat.state["location"], cat.state["activity"] = "doorstep", "at the door, wanting in"
em = cat_sounds.emissions(cat.state, T0 + 60, 60.0)
check("cat_meow_at_door" in em, f"at the door -> cat_meow_at_door still fires: {em}")

# ── T8 the defeater sweep ────────────────────────────────────────────────────────────────────────────
print("\nT8 D-0505 defeater sweep over every tier row this run")
rows = tier_rows()
viol = [r for r in rows if r["phase"] == "kept" and r["bond"] < cat.COMPANION_BOND]
check(rows and not viol, f"{len(rows)} tier rows; none rendered for a kept cat below {cat.COMPANION_BOND}: {viol[:3]}")
check(all(r["phase"] in ("kept", "companion") for r in rows), "every tier row is a kept or companion cat")

# ── canary ───────────────────────────────────────────────────────────────────────────────────────────
FP_AFTER = _fingerprint()
leaks = sorted(k for k in set(FP_BEFORE) | set(FP_AFTER) if k not in _IGNORE and FP_BEFORE.get(k) != FP_AFTER.get(k))
print("\nlive-store canary:", "CLEAN" if not leaks else f"LEAK {leaks}")
if leaks:
    FAILS.append(f"live-store leak: {leaks}")
print(f"\n{'ALL OK' if not FAILS else 'FAILURES'}: {OKS} checks passed, {len(FAILS)} failed")
for f in FAILS:
    print("  -", f)
sys.exit(1 if FAILS else 0)
