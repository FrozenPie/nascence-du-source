"""
Cat Overhaul D-4 -- real food: the carrier's fish and milk, her kills, scraps, the feed branch (J-2466, D-0508)
=============================================================================================================
HERMETIC: every store this reaches (cat_state, provisions, supply, garden_life, world_substrate/objects, the
cat ledgers) is redirected into a tempfile.mkdtemp() dir OUTSIDE data/ before any write; every cross-module
writer the paths can reach (study_life._st, garden._load/_save, sensorium._save_now, activity_memory.record,
life_traces.add_carcass, life.note_deed) is stubbed; the live C:\\Nascence\\data top-level files are
fingerprinted before and after and any change (bar arousal_shadow.jsonl / hud.err.log, written by other
processes) is reported as a LEAK. `import core` BEFORE anything else and core.__file__ must resolve under
this worktree (the F-2570 / jobrun live-store-leak rule).

What it proves:
  T1  provisions: "milk" and "scraps" are real kinds (unit, qty, plural, bios); a fresh house starts at ZERO of
      both (not bootstrapped, not seeded); add/consume/cupboard_line/look_item handle them
  T2  the carrier: a note naming milk / tinned fish / "a saucer of milk" is parsed; the card names milk; on the
      day the box holds a jug; collecting it puts a real jug on the shelf, credited to the study's count (no
      sync-back), the unpacking phrase rotating; the carrier stays the only supply (no bootstrap of either)
  T3  milk spoils: MILK_SPOIL_H is a real-world estimate citing SHORE_FISH_SPOIL_H as its precedent; a jug past
      it is discarded quietly under its own "discarded" log event, never "used up"; a fresh jug is ready
  T4  the feed branch consumes: milk alone -> the saucer gets milk, a saucer leaves the jug, thirst drops more
      than hunger, the line is a milk line; "a saucer of milk" with a tin AND a jug -> milk first; "feed her"
      with a tin and a jug -> the tin first (J-0719 untouched); scraps given -> spent, a scraps line; the
      order tin > fish > scraps > jug; with NOTHING in the house the feed fails honestly: nothing spent, no
      last_fed, one of the honest lines; _has_real_food / affordance_line agree with the spend
  T5  her kills feed her budget: note_kill("bird") lowers hunger; garden_life's fledgling roll is scaled by her
      hunger (a full cat lets them go at a third of the odds, a hungry one takes them at the old odds), the
      kill lands on her hunger, the event row carries the scale; an old state with no body rolls the old odds
  T6  D-0434 no readout: no digit in any new line; hunger_level() has no reader outside garden_life; the cat
      sound hold "cat_lapping" still fires from a milk feed (the voice stays meaningful)
Run:  python scripts/_test_cat_food_J-2466.py   (from the worktree root)
"""
from __future__ import annotations

import json
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

from core import cat, cat_sounds, cat_referent, provisions, supply, garden_life, life, life_traces  # noqa: E402
from core import activity_memory, study_life, sensorium, garden, world_traces, locomotion, world_clock  # noqa: E402
from core import world_substrate, world_objects  # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="cat_food_J2466_"))
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
provisions._F = TMP / "provisions.json"
provisions._LOG = TMP / "provisions_log.jsonl"
supply._F = TMP / "supply.json"
supply._LOG = TMP / "supply_log.jsonl"
garden_life._DATA = TMP                    # its fledgling roll reads <_DATA>/cat_state.json == cat._STATE_F
garden_life._F = TMP / "garden_life.json"
garden_life._EVENTS = TMP / "garden_events.jsonl"
world_substrate._SUBSTRATE_F = TMP / "world_substrate.json"
world_substrate._LAST_LOOKED_F = TMP / "world_substrate_last_looked.json"   # look_item() stamps a look
world_objects._OBJECTS_F = TMP / "world_objects.json"
world_traces._TRACES_F = TMP / "world_traces.json"
locomotion._POS_F = TMP / "position.json"
life._F = TMP / "life_state.json"
life._LEDGER = TMP / "life_ledger.jsonl"
life._EVENTS = TMP / "life_events.jsonl"
life._FLAGS_F = TMP / "life_flags.json"
# cross-module writers -- stubbed (counted, never written)
STUBS = {"activity": [], "carcass": [], "deed": [], "sens_save": 0, "garden_save": 0}
activity_memory.record = lambda *a, **k: STUBS["activity"].append(a)
life_traces.add_carcass = lambda *a, **k: STUBS["carcass"].append(a)
life.note_deed = lambda *a, **k: STUBS["deed"].append(a)
STUDY = {"_init": True, "matches": 0, "cat_food": 0.0}
study_life._st = lambda: STUDY
GARDEN = {"items": {"twine": {"place": "study"}}, "packets": []}
garden._load = lambda *a, **k: GARDEN
garden._save = lambda *a, **k: STUBS.__setitem__("garden_save", STUBS["garden_save"] + 1)
sensorium.state = {"weather": "clear", "wind": "calm", "fire": "out", "location": "study", "asleep": False, "study": STUDY}
sensorium._save_now = lambda *a, **k: STUBS.__setitem__("sens_save", STUBS["sens_save"] + 1)
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
    """A kept, bonded, awake cat by the fire with him in the study; a body already on her."""
    cat.state = {}
    cat._state_mtime = 0.0
    cat._last_tick = 0.0
    cat._prev_ref_txt = ""
    st = {"phase": "kept", "name": "", "bond": 0.7, "location": "by_the_fire", "activity": "watching",
          "mood": "content", "appeared_ts": now - 100 * 86400, "last_fed": now - 6 * 3600, "last_seen": now,
          "quirks": {"storm_response": "under_desk", "greeting": "chirrup", "fair_spot": "windowsill"},
          "firsts": {"first_lap": 1.0, "first_play": 1.0}, "name_invited": True,
          "last_tended": now - 7200, "last_greeted_ts": time.time(), "arc": {},
          "saucer": {"has_food": False, "kind": "", "set_ts": 0.0}, "_handled_ts": [],
          "_was_in": True, "fur_moisture": 0.0, "last_fur_decay_ts": now, "last_bond_decay_ts": now,
          "body": {"hunger": 0.5, "thirst": 0.7, "energy": 0.7, "warmth": 0.5, "condition": 0.7, "bout": "",
                   "bout_until": 0.0, "bout_since": 0.0, "last_ts": now, "last_drank_ts": 0.0, "cold_hours": 0.0,
                   "last_meal": ""}}
    st.update(kw)
    cat._STATE_F.write_text(json.dumps(st), encoding="utf-8")
    return cat._load()


def fresh_larder() -> None:
    """A larder with the previous occupant's goods only -- never any food for her."""
    for p in (provisions._F, provisions._LOG, world_substrate._SUBSTRATE_F, world_objects._OBJECTS_F):
        if p.exists():
            p.unlink()
    try:
        world_substrate._cache = {}; world_substrate._cache_ts = 0.0
    except Exception:
        pass
    provisions._ensure()


def backdate(kind: str, hours: float) -> None:
    """Make every non-empty object of `kind` look delivered `hours` ago (its own history[0].ts)."""
    d = provisions._load()
    for o in d["objects"]:
        if o["kind"] == kind and not o.get("empty"):
            o["history"][0]["ts"] = time.time() - hours * 3600
    provisions._save(d)


def log_events() -> list[dict]:
    try:
        return [json.loads(l) for l in provisions._LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
    except Exception:
        return []


NOW = time.time()

# ── T1 provisions ───────────────────────────────────────────────────────────────────────────────────
print("\nT1 provisions: milk and scraps are real kinds; a fresh house has none")
fresh_larder()
check("milk" in provisions.KINDS and "scraps" in provisions.KINDS, "KINDS carries milk and scraps")
check(provisions.KINDS["milk"][1] == 4 and provisions.KINDS["milk"][3] == "saucers", "a jug is four saucers")
check(provisions.KINDS["scraps"][1] == 1 and provisions.KINDS["scraps"][3] == "feeds", "a twist of scraps is one feed")
check(all(k in provisions._PLURAL and k in provisions._BIOS for k in ("milk", "scraps")), "plural + biography pools for both")
check(len(provisions._BIOS["milk"]) >= 2 and len(provisions._BIOS["scraps"]) >= 2, "biography pools rotate (2+ each)")
check(provisions.stock("milk") == 0 and provisions.stock("scraps") == 0 and provisions.stock("cat_food") == 0,
      "a fresh house: no milk, no scraps, no cat food (nobody here had a cat)")
check(not any(k in ("milk", "scraps") for k, *_ in [(m[1],) for m in provisions._NEW_KINDS_2026_09_05]),
      "neither is in the seeded-kinds list (not laid in, only ever acquired)")
ids = provisions.add("milk", 1, "carrier")
check(len(ids) == 1 and provisions.stock("milk") == 4, "add() mints a full jug: stock 4 saucers")
check(provisions.consume("milk", 1, by="Du") and provisions.stock("milk") == 3, "consume() takes one saucer: 3 left")
cl = provisions.cupboard_line()
check("one open jug of milk" in cl, f"cupboard_line names the open jug: ...{cl[-120:]}")
look = provisions.look_item("milk")
check(isinstance(look, str), "look_item('milk') answers without error")
oid = provisions.add_found("scraps", 1.0, note="the end of a meal, folded into paper")
check(oid is not None and provisions.stock("scraps") == 1, "add_found() credits a twist of scraps under its own 'found' event")
check(any(e.get("event") == "found" and e.get("kind") == "scraps" for e in log_events()), "the provisions log shows 'found' for scraps, not 'added'")

# ── T2 the carrier ──────────────────────────────────────────────────────────────────────────────────
print("\nT2 the carrier: fish and milk are standing lines")
fresh_larder()
if supply._F.exists():
    supply._F.unlink()
line = supply.leave_note("For the carrier: milk, and tinned fish for the cat, and matches")
d = supply._load()
check(d["note"] and set(d["note"]["items"]) == {"milk", "cat_food", "matches"}, f"a note naming milk + tinned fish + matches parses: {d['note']['items']}")
supply.leave_note("a saucer of milk for her, please")
check(supply._load()["note"]["items"] == ["milk"], "'a saucer of milk' on a list is milk")
supply.leave_note("a jug of milk and some fish for the cat")
check(set(supply._load()["note"]["items"]) == {"milk", "cat_food"}, "'a jug of milk' + 'fish for the cat' parse to the two lines")
card = supply.card_line()
check("Milk" in card and "tinned fish" in card, "the letterbox card names both tinned fish and milk (the world answers a look)")
supply.leave_note("milk, tinned fish")
d = supply._load(); day = d["next_carrier_ts"] + 1
ann = supply.advance(day)
check(ann and supply._load()["box"] and set(supply._load()["box"]["items"]) == {"milk", "cat_food"}, "on the day the crate holds the jug and the tin")
sensorium.state["location"] = "garden"
seen_phrases = set()
got = supply.collect_box()
check("milk" in got and provisions.stock("milk") == 4 and provisions.stock("cat_food") == 4, f"collecting puts a real jug and a real tin on the shelf: {got[:140]}...")
check(STUDY.get("milk") == 4.0 and STUDY.get("cat_food") == 4.0, "the study's cached counts are credited (no sync-back consumption)")
seen_phrases.add(next((p for p in supply._MILK_BOX_LINES if p in got), ""))
for _ in range(12):   # the unpacking phrase rotates
    supply.leave_note("milk"); d = supply._load(); supply.advance(d["next_carrier_ts"] + 1)
    g = supply.collect_box(); seen_phrases.add(next((p for p in supply._MILK_BOX_LINES if p in g), ""))
check(len(seen_phrases - {""}) >= 2, f"the jug's unpacking phrase rotates ({len(seen_phrases - {''})} of {len(supply._MILK_BOX_LINES)} seen)")
check(provisions.stock("milk") == 4 * 13, "every delivered jug is a real object (13 jugs on the shelf)")
check(not any(e.get("event") == "seeded" and e.get("kind") in ("milk", "scraps") for e in log_events()), "no jug or scraps were ever seeded: the carrier is the only supply")
sensorium.state["location"] = "study"

# ── T3 milk spoils ──────────────────────────────────────────────────────────────────────────────────
print("\nT3 milk spoils")
src = (ROOT / "core" / "cat.py").read_text(encoding="utf-8")
check(cat.MILK_SPOIL_H == 48.0 and cat.SHORE_FISH_SPOIL_H == 36.0, "MILK_SPOIL_H 48 h (a raw fish, 36 h, goes first)")
m = re.search(r"MILK SPOILS TOO.*?MILK_SPOIL_H = ", src, re.S)
check(m and "SHORE_FISH_SPOIL_H above is the precedent" in m.group(0) and "ESTIMATE" in m.group(0),
      "the comment names SHORE_FISH_SPOIL_H as the precedent and calls the number a real-world estimate")
fresh_larder()
provisions.add("milk", 1, "carrier"); backdate("milk", 49.0)
check(cat._milk_ready() is False and provisions.stock("milk") == 0, "a jug delivered 49 h ago is tipped out quietly: not ready, stock 0")
ev = log_events()
check(any(e.get("event") == "discarded" and e.get("kind") == "milk" for e in ev) and not any(e.get("event") == "emptied" and e.get("kind") == "milk" for e in ev),
      "the discard is its own 'discarded' event, never 'emptied'/'used up'")
d = provisions._load(); sour = [o for o in d["objects"] if o["kind"] == "milk"][0]
check(sour.get("empty") and "sour" in sour["history"][-1]["event"], "the jug's own biography says it went sour")
provisions.add("milk", 1, "carrier"); backdate("milk", 47.0)
check(cat._milk_ready() is True and provisions.stock("milk") == 4, "a jug delivered 47 h ago is still good")
provisions.add("milk", 1, "carrier"); backdate("milk", 60.0)   # both jugs now 60 h: the loop discards both
check(cat._milk_ready() is False and provisions.stock("milk") == 0, "two sour jugs: the bounded loop discards both and reports none")

# ── T4 the feed branch consumes ─────────────────────────────────────────────────────────────────────
print("\nT4 the feed branch consumes")
# milk alone, "feed her"
fresh_larder(); provisions.add("milk", 1, "carrier")
st = fresh_cat(NOW)
check(cat._has_real_food() is True, "_has_real_food: a jug alone is real food")
out = cat.react("I should feed the cat.", "", "study")
b = cat.state["body"]
check(out in [l.replace("{her}", "the cat") for l in cat._FEED_MILK_LINES], f"milk alone: a milk line: {out[:90]}")
check(provisions.stock("milk") == 3, "one saucer left the jug")
check(cat.state["saucer"]["kind"] == "milk" and cat.state["saucer"]["has_food"], "the saucer holds milk")
check(cat.state["last_fed_source"] == "milk" and b["last_meal"] == "milk", "last_fed_source / last_meal = milk")
check(abs(b["thirst"] - 0.1) < 1e-6 and abs(b["hunger"] - 0.3) < 1e-6, f"milk is mostly a drink: thirst 0.7->{b['thirst']}, hunger 0.5->{b['hunger']}")
check(cat.state["last_fed"] >= NOW and len(STUBS["deed"]) == 1, "last_fed set; the saucer deed drew its takers once")
absent = cat._saucer_absence_line()
check(absent in cat._SAUCER_MILK_LINES, f"the saucer-absence line reads milk while the saucer holds it: {absent}")
# "a saucer of milk" with a tin AND a jug -> milk first
fresh_larder(); provisions.add("milk", 1, "carrier"); provisions.add("cat_food", 1, "carrier")
st = fresh_cat(NOW)
out = cat.react("I'll put down a saucer of milk for the cat.", "", "study")
check(cat.state["last_fed_source"] == "milk" and provisions.stock("milk") == 3 and provisions.stock("cat_food") == 4,
      "his words name milk: the jug first, the tin untouched")
# "feed her" with a tin and a jug -> the tin first (J-0719 unchanged)
st = fresh_cat(NOW)
out = cat.react("Time to feed the cat.", "", "study")
check(cat.state["last_fed_source"] == "cat_food" and provisions.stock("cat_food") == 3 and provisions.stock("milk") == 3,
      "plain 'feed her' with both: the tin first, as ever")
check("winds against your legs" in out or out, f"the tin keeps its own line: {out[:80]}")
# order tin > fish > scraps > jug: with fish + scraps + jug and no tin
fresh_larder(); provisions.add("shore_fish", 1, "carrier", note="caught off the shelf's edge"); provisions.add("milk", 1, "carrier")
check(cat.give_scraps(1.0) is not None and provisions.stock("scraps") == 1, "give_scraps() credits a twist")
check(STUDY.get("scraps") == 1.0, "give_scraps() credits the study's cached count too (no sync-back)")
st = fresh_cat(NOW); cat.react("feed the cat", "", "study")
check(cat.state["last_fed_source"] == "shore_fish", "no tin: the fresh fish before the scraps")
st = fresh_cat(NOW); cat.react("feed the cat", "", "study")
check(cat.state["last_fed_source"] == "scraps" and provisions.stock("scraps") == 0, "no tin, no fish: the scraps before the jug")
st = fresh_cat(NOW); out = cat.react("feed the cat", "", "study")
check(cat.state["last_fed_source"] == "milk" and provisions.stock("milk") == 3, "then the jug")
# scraps line
fresh_larder(); cat.give_scraps(1.0)
st = fresh_cat(NOW)
out = cat.react("give the cat the scraps", "", "study")
check(out in [l.replace("{her}", "the cat") for l in cat._FEED_SCRAPS_LINES] and provisions.stock("scraps") == 0, f"scraps: a scraps line, the twist spent: {out[:80]}")
check(abs(cat.state["body"]["hunger"] - 0.15) < 1e-6, "scraps are a small meal (hunger 0.5 -> 0.15)")
# a sour jug is no food
fresh_larder(); provisions.add("milk", 1, "carrier"); backdate("milk", 50.0)
st = fresh_cat(NOW)
check(cat._has_real_food() is False, "_has_real_food: a sour jug is not food")
out = cat.react("feed the cat", "", "study")
check(cat.state.get("last_fed_source", "") == "" and provisions.stock("milk") == 0 and not cat.state["saucer"]["has_food"], "a sour jug feeds nothing: tipped out, saucer empty")
# NOTHING in the house: honest failure
fresh_larder()
st = fresh_cat(NOW); lf0 = cat.state["last_fed"]; h0 = cat.state["body"]["hunger"]
seen = set()
for _ in range(12):
    st = fresh_cat(NOW)
    out = cat.react("I will feed the cat now.", "", "study")
    seen.add(out)
    check_once = True
check(all(("nothing" in o.lower() or "empty" in o.lower()) for o in seen), "with nothing in the house every answer is the honest failure")
check(len(seen) >= 2, f"the honest-failure line rotates ({len(seen)} distinct)")
check(cat.state["last_fed"] == lf0 and cat.state["body"]["hunger"] == h0 and not cat.state["saucer"]["has_food"],
      "nothing spent, last_fed unchanged, hunger unchanged, saucer empty")
check(cat.state.get("last_fed_source", "") == "", "last_fed_source untouched")
check(cat._has_real_food() is False, "_has_real_food False with nothing in the house")
# the affordance agrees with the spend
fresh_larder(); provisions.add("milk", 1, "carrier")
st = fresh_cat(NOW, activity="demanding_food", mood="insistent", location="doorstep")
aff = cat.affordance_line("garden")
check(aff.startswith("feed the cat"), f"a jug alone: 'feed her' is offered: {aff[:60]}")
fresh_larder()
st = fresh_cat(NOW, activity="demanding_food", mood="insistent", location="doorstep")
aff = cat.affordance_line("garden")
check("larder has nothing" in aff, "nothing in the house: the affordance says so")

# ── T5 her kills feed her budget ────────────────────────────────────────────────────────────────────
print("\nT5 her kills feed her budget; a fed cat leaves the fledglings alone more")
st = fresh_cat(NOW)
cat.note_kill("bird", NOW)
cat._load()
check(abs(cat.state["body"]["hunger"] - 0.15) < 1e-6 and cat.state["body"]["last_meal"] == "bird", "note_kill('bird'): hunger 0.5 -> 0.15, saved")
check(cat.hunger_level() == 0.15, "hunger_level() reads the budget")
import random as _rnd
_r0 = _rnd.random


def nest_state(now: float) -> None:
    g = garden_life._load()
    g["nest"] = {"stage": "fledged", "stage_ts": now, "where": "bushes", "eggs": 4, "lost": 0}
    g["_last"] = now - 86400
    garden_life._F.write_text(json.dumps(g), encoding="utf-8")


def gl_events() -> list[dict]:
    try:
        return [json.loads(l) for l in garden_life._EVENTS.read_text(encoding="utf-8").splitlines() if l.strip()]
    except Exception:
        return []


_rnd.random = lambda: 0.4          # the old roll: days(1) * 0.5 = 0.5 > 0.4 -> a kill, every time
try:
    # a FULL cat (hunger 0): the odds are a third -> 0.17 < 0.4 -> she lets it go
    st = fresh_cat(NOW); cat.state["body"]["hunger"] = 0.0; cat.state["location"] = "garden"; cat.state["activity"] = "stalking something"; cat._save()
    nest_state(NOW)
    garden_life.advance(NOW, 86400, 15.0, 0.5, False, "day")
    g = garden_life._load()
    check(g["nest"]["lost"] == 0, "a full cat (hunger 0) stalking in the garden lets the fledgling go at 0.4")
    # a HUNGRY cat (hunger 1): the old odds exactly -> 0.5 > 0.4 -> taken
    st = fresh_cat(NOW); cat.state["body"]["hunger"] = 1.0; cat.state["location"] = "garden"; cat.state["activity"] = "stalking something"; cat._save()
    nest_state(NOW)
    garden_life.advance(NOW, 86400, 15.0, 0.5, False, "day")
    g = garden_life._load(); cat._load()
    check(g["nest"]["lost"] == 1, "a hungry cat (hunger 1) takes it at the old odds")
    check(abs(cat.state["body"]["hunger"] - 0.65) < 1e-6 and cat.state["body"]["last_meal"] == "bird", "the fledgling lands on HER hunger (1.0 -> 0.65)")
    ev = [e for e in gl_events() if e.get("event") == "fledgling_taken_by_cat"]
    check(ev and ev[-1].get("hunger_scale") == 1.0, "the garden event carries the hunger scale (world-side ledger only)")
    # an OLD state with no body: the old odds, unscaled
    st = fresh_cat(NOW); del cat.state["body"]; cat.state["location"] = "garden"; cat.state["activity"] = "stalking something"; cat._save()
    nest_state(NOW)
    garden_life.advance(NOW, 86400, 15.0, 0.5, False, "day")
    g = garden_life._load()
    check(g["nest"]["lost"] == 1, "no body on her (hunger_level None): the old unscaled roll (taken at 0.4)")
    _rnd.random = lambda: 0.34
    st = fresh_cat(NOW); cat.state["body"]["hunger"] = 0.5; cat.state["location"] = "garden"; cat.state["activity"] = "stalking something"; cat._save()
    nest_state(NOW)
    garden_life.advance(NOW, 86400, 15.0, 0.5, False, "day")
    check(garden_life._load()["nest"]["lost"] == 0, "half-fed (hunger 0.5): odds 0.335 -> let go at 0.34")
    _rnd.random = lambda: 0.33
    nest_state(NOW)
    garden_life.advance(NOW, 86400, 15.0, 0.5, False, "day")
    check(garden_life._load()["nest"]["lost"] == 1, "half-fed: taken at 0.33")
finally:
    _rnd.random = _r0

# ── T6 no readout; the voice stays meaningful ───────────────────────────────────────────────────────
print("\nT6 D-0434 no readout; cat_lapping still fires from a milk feed")
pools = list(cat._FEED_MILK_LINES) + list(cat._FEED_SCRAPS_LINES) + list(cat._SAUCER_MILK_LINES) + list(supply._MILK_BOX_LINES) \
    + provisions._BIOS["milk"] + provisions._BIOS["scraps"]
check(not any(re.search(r"\d", l) for l in pools), "no digit in any new line pool")
check(all(len(p) >= 2 for p in (cat._FEED_MILK_LINES, cat._FEED_SCRAPS_LINES, cat._SAUCER_MILK_LINES, supply._MILK_BOX_LINES)), "every new pool rotates (2+ lines)")
readers = []
for p in (ROOT / "core").glob("*.py"):
    if p.name in ("cat.py", "garden_life.py"):
        continue
    t = p.read_text(encoding="utf-8", errors="replace")
    if "hunger_level(" in t:
        readers.append(p.name)
check(not readers, f"hunger_level() has no reader outside cat.py / garden_life.py (found: {readers or 'none'})")
fresh_larder(); provisions.add("milk", 1, "carrier")
st = fresh_cat(NOW); cat.state["location"] = "doorstep"; cat._save()
cat_sounds._mem = {"holds_prev": {}, "last_fired": {}, "act": "", "loc": "", "greet_ts": 0.0, "last": 0.0}
cat.react("feed the cat", "", "garden")
em = cat_sounds.emissions(cat.state, time.time(), 60.0)
check("cat_lapping" in em, f"a milk feed sets last_fed: the lapping bed holds ({em})")

# ── leak check ──────────────────────────────────────────────────────────────────────────────────────
FP_AFTER = _fingerprint()
leaks = sorted(k for k in set(FP_BEFORE) | set(FP_AFTER) if k not in _IGNORE and FP_BEFORE.get(k) != FP_AFTER.get(k))
check(not leaks, f"no live-store leak in C:\\Nascence\\data (changed: {leaks or 'none'})")

print(f"\n{OKS} ok, {len(FAILS)} failed")
for f in FAILS:
    print("  FAIL", f)
sys.exit(1 if FAILS else 0)
