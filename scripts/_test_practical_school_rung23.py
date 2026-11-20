"""
_test_practical_school_rung23.py — J-2483 (D-0504, 2026-10-28: J-0628's spec released): the rung 2 and 3
practical-school hands in core/fieldcraft.py, their ladder rows and gates in core/practical_lesson.py,
the grammar they derive from core/actions.py, and the two larder objects (compass, bandage linen) in
core/provisions.py.

Isolation: the J-0627 test's own pattern (scripts/_test_practical_lesson.py) — every store any of these
modules can write is redirected via lab_env.isolate() BEFORE anything runs; `import core` happens BEFORE
`import lab_env` and core.__file__ is asserted to be the tree this script sits in (F-2423). Never touches
the live data/ files; the memory DB is an EMPTY lab copy (db="empty").

What it proves, per hand group (one finding per group is recorded against these checks):
  knots & rope   sheepshank / haul_timber / splice_rope / build_tripod — decline without the line, hold on
                 a good roll, slip on a bad one, each logging its own {"deed", "ok"} marker; the tripod
                 racks over in a gale (advance()).
  the fire's     cook_over_embers / wash_up_camp / friction_fire — need coals + real food, something
  other side     greasy + boiled water or sand, the whittled kit + tinder; done/raw/burnt, clean/greasy,
                 coal/cold dust; the kit's spindle wears; the study grate lights from the coal.
  bearings &     knife_bearing / pace_distance / sound_lag / triangle_check / read_weather_glass — the
  distances      world gives the shadow, the count, the two measured lengths, the needle; the ledger keeps
                 the hidden truth; a prediction is answered by the next real day in advance().
  blazes         leave_blaze is a world trace; follow_trail re-finds it; clarity is what is left of it.
  the ladder     all 22 rows hand_ready; each rung-2/3 gate refuses when its hand would, offers when it
                 would not; the picker reaches every rung-2/3 row from a rich state; the issued row and
                 the period-end grader read the new deed markers; the directive carries no number, band
                 or verdict (D-0434).
  the larder     compass + bandage linen seeded once, synced into study state, lookable.

Exit 1 on any failed check. Run: python -X utf8 scripts/_test_practical_school_rung23.py
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from unittest import mock

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # noqa: E402  -- BEFORE lab_env (F-2423: lab_env appends the shared tree to sys.path)
assert Path(core.__file__).resolve().is_relative_to(ROOT), f"core resolved outside this tree: {core.__file__}"

sys.path.insert(0, str(Path.home() / ".claude" / "skills" / "job-queue"))
from lab_env import isolate  # noqa: E402
from core import fieldcraft, sensorium, study_life, provisions, garden, world_objects, world_substrate  # noqa: E402
from core import school, nature_study, practical_lesson, procedures, competence, literal_will, actions  # noqa: E402
from core import world_traces, shore_life, hands, world_clock  # noqa: E402

FAIL: list[str] = []


def check(name: str, cond: bool, detail="") -> None:
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f" -- {detail}" if detail and not cond else ""))
    if not cond:
        FAIL.append(name)


def ledger() -> list[dict]:
    try:
        return [json.loads(l) for l in open(fieldcraft._LEDGER, encoding="utf-8")]
    except FileNotFoundError:
        return []


def deeds(name: str) -> list[dict]:
    return [r for r in ledger() if r.get("deed") == name]


# a real Tuesday, 10:30 local — the nature period (see scripts/_test_practical_lesson.py)
FAKE_TS = time.mktime((2026, 9, 8, 10, 30, 0, 0, 0, -1))
assert time.localtime(FAKE_TS).tm_wday == 1
_clock = {"t": FAKE_TS}
_real_localtime = time.localtime


def _fake_time() -> float:
    _clock["t"] += 0.05
    return _clock["t"]


def _fake_localtime(secs=None):
    return _real_localtime(secs if secs is not None else _clock["t"])


GOOD = mock.patch("core.fieldcraft.random.random", return_value=0.05)
BAD = mock.patch("core.fieldcraft.random.random", return_value=0.99)

with isolate(db="empty", also=[
    (fieldcraft, ["_F", "_LEDGER"]),
    (sensorium, ["_STATE_F"]),
    (provisions, ["_F", "_LOG"]),
    (garden, ["_F", "_LEDGER", "_EVENTS"]),
    (world_objects, ["_OBJECTS_F"]),
    (world_substrate, ["_SUBSTRATE_F", "_SUBSTRATE_LOG", "_LAST_LOOKED_F"]),
    (school, ["STATE"]),
    (nature_study, ["_STATE", "_LOG"]),
    (practical_lesson, ["_STATE", "_LOG", "_FC_LEDGER"]),
    (procedures, ["_F", "_LOG"]),
    (competence, ["_BELIEFS_FILE"]),
    (world_traces, ["_TRACES_F"]),
    (shore_life, ["_F"]),
    (study_life, ["_LEDGER", "_EVENTS"]),
    (hands, ["_TRACE"]),
]) as lab_dir:
    print(f"isolated lab dir: {lab_dir}\n")
    with mock.patch("time.time", side_effect=_fake_time), \
         mock.patch("time.localtime", side_effect=_fake_localtime):
        # ── bootstrap the isolated world ─────────────────────────────────────────────────────────
        sensorium._load()
        sensorium.state["location"] = "study"
        sensorium.state["weather"] = "clear"
        sensorium.state["next_weather"] = "overcast"
        sensorium.state["fire"] = "burning"
        sensorium.state["fire_fuel"] = 0.8
        sensorium.state["woodpile"] = 4
        st = study_life._st()          # provisions.sync -> seeds rope_m/tinder_tin/knife/compass/...
        st["kindling"] = 0.8; st["water"] = 1.0
        gd = garden._load()
        twine = gd["items"]["twine"]; stakes = gd["items"]["stakes"]
        rope = st["items"]["rope"]; kettle = st["items"]["kettle"]
        school._save({**school._load(), "assigned_book": "x", "assigned_title": "Boy Scouts Handbook"})
        check("weekday 10:30 resolves to the nature period",
              school.is_school_time() and school.current_subject() == "nature")

        # ══ 0. grammar: the derivation still holds with the widened row ═══════════════════════════
        audit = fieldcraft.grammar_audit()
        check("grammar_audit: every table verb/object claimed by exactly the crafts, only 'knot' unclaimed",
              audit == {"verbs_unclaimed_in_table": [], "verbs_claimed_not_in_table": [],
                        "objects_unclaimed_in_table": ["knot"], "objects_claimed_not_in_table": []}, audit)
        new_crafts = {"sheepshank", "haul_timber", "knife_bearing", "cook_over_embers", "wash_up_camp", "leave_blaze",
                      "pace_distance", "sound_lag", "splice_rope", "build_tripod", "friction_fire", "triangle_check",
                      "read_weather_glass"}
        check("all thirteen rung-2/3 crafts are in _FIELDCRAFT_HANDS",
              new_crafts <= {c for c, _v, _o in fieldcraft._FIELDCRAFT_HANDS})
        # every ladder verb phrase classifies as a fieldcraft DEED at the registry gate (J-0627's own check)
        for t in practical_lesson.LADDER:
            if t["rung"] < 2:
                continue
            phrase = f"I will {t['verb'].lower()}."
            r = literal_will.classify(phrase, "")
            check(f"'{t['verb']}' classifies as a fieldcraft DEED",
                  any(x["family"] == "fieldcraft" and x["verdict"] == "DEED" for x in r), r)

        # ══ 1. knots & rope ═══════════════════════════════════════════════════════════════════════
        sensorium.state["location"] = "garden"
        twine.update(carried=False, place="study"); rope.update(carried=False, place="study")
        a0 = fieldcraft.sheepshank("").lower()
        check("sheepshank declines with neither twine nor rope here", "no line" in a0 or "elsewhere" in a0, a0)
        twine.update(carried=True)
        with GOOD:
            a = fieldcraft.sheepshank("")
        check("sheepshank holds on a good roll (twine)", "holds" in a and "twine" in a, a)
        with BAD:
            b = fieldcraft.sheepshank("")
        check("sheepshank slips on a bad roll", ("slip" in b.lower() or "old length" in b or "falls out" in b) and "holds" not in b, b)
        check("sheepshank logged its own deed markers with ok",
              [r.get("ok") for r in deeds("sheepshank")] == [True, False], deeds("sheepshank"))
        sensorium.state["location"] = "study"
        check("sheepshank declines indoors", "garden" in fieldcraft.sheepshank(""))

        sensorium.state["location"] = "shore"
        rope.update(carried=False, place="study")
        check("haul_timber declines without the rope on the shore", "rope" in fieldcraft.haul_timber("").lower())
        rope.update(carried=True)
        with GOOD:
            a = fieldcraft.haul_timber("")
        check("haul_timber drags the log clear on a good roll", "clear" in a or "above the tideline" in a, a)
        with BAD:
            b = fieldcraft.haul_timber("")
        check("haul_timber slips off on a bad roll", "slip" in b or "comes free" in b or "slides off" in b, b)
        check("haul_timber rolls the existing timber_hitch skill",
              any(r.get("craft") == "timber_hitch" for r in ledger()) and len(deeds("haul_timber")) == 2)
        sensorium.state["location"] = "garden"
        check("haul_timber declines off the shore", "shore" in fieldcraft.haul_timber(""))

        rope.update(carried=True); twine.update(carried=True)
        rm0 = float(st.get("rope_m", 0))
        with GOOD:
            a = fieldcraft.splice_rope("")
        check("splice_rope holds the strain on a good roll (twine seizes the strands)", "holds" in a and "seize" in a, a)
        with BAD:
            b = fieldcraft.splice_rope("")
        check("splice_rope parts on a bad roll", "parts" in b or "lets go" in b, b)
        check("splice_rope takes 0.3 m of rope per splice", abs(float(st["rope_m"]) - (rm0 - 0.6)) < 1e-6, (rm0, st["rope_m"]))
        check("splice_rope rolls the new short_splice skill", "short_splice" in fieldcraft._load()["skill"])
        sensorium.state["location"] = "wood"
        check("splice_rope declines outside the garden", "garden" in fieldcraft.splice_rope(""))

        sensorium.state["location"] = "garden"
        stakes.update(carried=False, place="study")
        check("build_tripod in the garden declines with the stakes elsewhere and not carried", "stakes" in fieldcraft.build_tripod(""))
        stakes.update(carried=False, place="garden")
        with BAD:
            b = fieldcraft.build_tripod("")
        check("build_tripod: stakes lying in the garden count there without being carried (garden.stake()'s own test)",
              "flat" in b and len(deeds("tripod_up")) == 1, b)
        fieldcraft._save({**fieldcraft._load(), "tripod": None})
        stakes.update(carried=True)
        with BAD:
            b = fieldcraft.build_tripod("")
        check("build_tripod racks over on a bad roll", "flat" in b, b)
        check("...and no tripod stands", fieldcraft.tripod_standing() is None)
        kettle.update(carried=True)
        with GOOD:
            a = fieldcraft.build_tripod("")
        check("build_tripod stands on a good roll, the carried kettle hung from it", "stands" in a and "kettle" in a, a)
        check("tripod_standing() reports it in the garden", (fieldcraft.tripod_standing() or {}).get("where") == "garden")
        a0 = fieldcraft.build_tripod("")
        check("a second build answers that it already stands", ("stands" in a0 or "still up" in a0) and len(deeds("tripod_up")) == 3, a0)
        # a gale brings it down in advance() -- the same law as the windbreak
        sensorium.state["wind"] = "gale"
        with mock.patch("core.fieldcraft.random.random", return_value=0.0):
            fieldcraft.advance(time.time(), 3600.0)
        check("advance(): a gale racks the tripod over", fieldcraft.tripod_standing() is None
              and any(r.get("event") == "tripod_down" for r in ledger()))
        sensorium.state["wind"] = "breeze"
        sensorium.state["location"] = "shore"
        with GOOD:
            a = fieldcraft.build_tripod("")
        check("build_tripod on the shore uses driftwood, no stakes needed", "driftwood" in a and "stands" in a, a)
        fieldcraft._save({**fieldcraft._load(), "tripod": None})

        # ══ 2. the fire's other side ══════════════════════════════════════════════════════════════
        sensorium.state["location"] = "garden"
        a0 = fieldcraft.cook_over_embers("")
        check("cook_over_embers declines where there is no fire (the garden)", "grate" in a0 or "fire-ring" in a0, a0)
        sensorium.state["location"] = "study"
        sensorium.state["fire"] = "out"
        a0 = fieldcraft.cook_over_embers("")
        check("cook_over_embers declines with the grate out", "no fire" in a0.lower() or "is out" in a0, a0)
        sensorium.state["fire"] = "embers"
        gd.setdefault("rack", [])
        gd["rack"][:] = [r for r in gd["rack"] if garden.CATALOGUE.get(r.get("species"), {}).get("kind") == "herb"]
        a0 = fieldcraft.cook_over_embers("")
        check("cook_over_embers declines with nothing real to cook", "nothing to cook" in a0.lower() or "nothing to put" in a0, a0)
        check("cook_food_available() is None with only herbs on the rack and no fish", fieldcraft.cook_food_available() is None)
        gd["rack"].append({"species": "potatoes", "cut_ts": time.time() - 3600, "dry": 0.0})
        check("...and names the potatoes once they are on the rack", fieldcraft.cook_food_available() == "potatoes")
        with GOOD:
            a = fieldcraft.cook_over_embers("")
        check("cook_over_embers: done through on a good roll", ("done" in a or "cooked through" in a) and "potatoes" in a, a)
        check("...the potatoes were eaten off the rack", fieldcraft.cook_food_available() is None)
        check("...and the pan is greasy", fieldcraft._load().get("pan_greasy") is True)
        gd["rack"].append({"species": "potatoes", "cut_ts": time.time() - 3600, "dry": 0.0})
        with mock.patch("core.fieldcraft.random.random", return_value=0.99), mock.patch("core.fieldcraft.random.choice", side_effect=lambda seq: seq[0]):
            b = fieldcraft.cook_over_embers("")
        check("cook_over_embers: raw or burnt on a bad roll", ("raw" in b or "burnt" in b or "charred" in b) and "done" not in b, b)
        rows = deeds("cook_over_embers")
        check("cook rows carry ok, food and outcome", [r.get("ok") for r in rows] == [True, False] and rows[0]["outcome"] == "done" and rows[1]["outcome"] in ("raw", "burnt"), rows)
        sensorium.state["fire"] = "burning"
        provisions.add("shore_fish", 1, origin="du_catch", note="test fish")
        check("a caught fish counts as food", fieldcraft.cook_food_available() == "shore_fish")
        with GOOD:
            a = fieldcraft.cook_over_embers("")
        check("cook_over_embers over a burning fire rakes a bed of coals first and cooks the fish", a.startswith("You rake") and "fish" in a, a)
        check("...the fish is consumed from the larder", provisions.stock("shore_fish") == 0)
        sensorium.state["location"] = "shore"
        sd = shore_life._load(); sd["fire"]["state"] = "embers"; shore_life._save(sd)
        gd["rack"].append({"species": "radish", "cut_ts": time.time() - 3600, "dry": 0.0})
        with GOOD:
            a = fieldcraft.cook_over_embers("")
        check("cook_over_embers works over the shore fire-ring's embers", "radish" in a and ("done" in a or "cooked through" in a), a)
        sd["fire"]["state"] = "out"; shore_life._save(sd)

        # wash up
        sensorium.state["location"] = "wood"
        a0 = fieldcraft.wash_up_camp("")
        check("wash_up_camp declines in the wood", "study" in a0 or "shore" in a0, a0)
        sensorium.state["location"] = "study"
        check("the pan is greasy from the cooking", fieldcraft._load().get("pan_greasy") is True)
        kettle.update(carried=False, place="garden")
        check("wash_up_camp (study) declines without the kettle here", "kettle" in fieldcraft.wash_up_camp(""))
        kettle.update(carried=True)
        sensorium.state["fire"] = "out"
        a0 = fieldcraft.wash_up_camp("")
        check("wash_up_camp (study) declines with the grate cold", "cold" in a0 or "is out" in a0, a0)
        sensorium.state["fire"] = "burning"
        w0 = float(st["water"])
        with BAD:
            b = fieldcraft.wash_up_camp("")
        check("wash_up_camp: still greasy on a bad roll", "greasy" in b.lower() and fieldcraft._load().get("pan_greasy") is True, b)
        st["dirty_cups"] = 2
        with GOOD:
            a = fieldcraft.wash_up_camp("")
        check("wash_up_camp: clean on a good roll, the cups too", "clean" in a.lower() and fieldcraft._load().get("pan_greasy") is False and st["dirty_cups"] == 0, a)
        check("...two washes spent 0.4 of the pail", abs(float(st["water"]) - (w0 - 0.4)) < 1e-6)
        check("wash_up_camp with nothing greasy says so", "nothing" in fieldcraft.wash_up_camp("").lower())
        sensorium.state["location"] = "shore"
        fieldcraft._save({**fieldcraft._load(), "pan_greasy": True})
        with GOOD:
            a = fieldcraft.wash_up_camp("")
        check("wash_up_camp on the shore scours with sand", "sand" in a and "clean" in a.lower(), a)

        # the bow-drill
        sensorium.state["location"] = "wood"
        a0 = fieldcraft.friction_fire("")
        check("friction_fire declines without the whittled kit", "whittled" in a0 or "made" in a0, a0)
        with GOOD:
            w = fieldcraft.whittle("i will whittle a fire-drill: a bow, a spindle and a fire-board")
        check("whittle() makes the fire-drill kit", "fire-drill kit" in w and "spindle" in w, w)
        check("the kit is a made thing with wear 0.0", (fieldcraft._made_thing(fieldcraft._load(), "a fire-drill kit") or {}).get("wear") == 0.0)
        check("has_fire_drill_kit() sees it", fieldcraft.has_fire_drill_kit())
        check("whittle(): a bare 'stick' thought still makes a walking stick, not a kit",
              "walking stick" in (lambda: (GOOD.__enter__(), fieldcraft.whittle("i will whittle a stick"), GOOD.__exit__(None, None, None))[1])())
        fieldcraft._save({**fieldcraft._load(), "tinder": 0.0})
        check("friction_fire declines with the tin empty", "tinder" in fieldcraft.friction_fire(""))
        fieldcraft._save({**fieldcraft._load(), "tinder": 0.5})
        with BAD:
            b = fieldcraft.friction_fire("")
        check("friction_fire: cold dust on a bad roll", ("dust" in b and "coal" not in b.split("dust")[0][-40:]) and deeds("friction_fire")[-1]["ok"] is False, b)
        check("...the spindle wore", (fieldcraft._made_thing(fieldcraft._load(), "a fire-drill kit") or {}).get("wear") == 0.1)
        with GOOD:
            a = fieldcraft.friction_fire("")
        check("friction_fire in the wood: a coal, a flame, let die (no hearth)", "coal" in a and ("let it burn down" in a or "let it die" in a), a)
        check("...tinder spent 0.15", abs(float(fieldcraft._load()["tinder"]) - 0.35) < 1e-6, fieldcraft._load()["tinder"])
        check("...logged lit=False", deeds("friction_fire")[-1].get("lit") is False)
        sensorium.state["location"] = "study"
        sensorium.state["fire"] = "out"; sensorium.state["fire_fuel"] = 0.0
        st["kindling"] = 0.8; sensorium.state["woodpile"] = 3
        with GOOD:
            a = fieldcraft.friction_fire("")
        check("friction_fire in the study lights the grate from the coal", sensorium.state["fire"] == "burning" and sensorium.state.get("hand_lit") is True and "grate" in a, a)
        check("...logged lit=True", deeds("friction_fire")[-1].get("lit") is True)
        _d = fieldcraft._load(); kit = fieldcraft._made_thing(_d, "a fire-drill kit")
        kit["wear"] = 1.0; fieldcraft._save(_d)
        check("a worn-out kit (wear 1.0) is no kit", not fieldcraft.has_fire_drill_kit())

        # ══ 3. bearings, distances, the glass ════════════════════════════════════════════════════
        sensorium.state["location"] = "study"
        check("knife_bearing declines indoors", "open" in fieldcraft.knife_bearing(""))
        sensorium.state["location"] = "garden"
        provisions.consume("knife", 1); provisions.sync(st)
        check("the larder's knife taken: study state knife=False", st.get("knife") is False)
        check("knife_bearing declines without the knife", "knife" in fieldcraft.knife_bearing(""))
        provisions.add("knife", 1, note="test knife"); provisions.sync(st)
        check("...and back", st.get("knife") is True)
        sensorium.state["weather"] = "thunderstorm"
        _kb = fieldcraft.knife_bearing("")   # ONE draw: both decline lines carry "shadow" (a second call would redraw the pool)
        check("knife_bearing declines under cloud too heavy for a shadow", "shadow" in _kb, _kb)
        sensorium.state["weather"] = "overcast"
        _real_sun = world_clock.sun
        world_clock.sun = lambda t=None: {"up": False, "phase": "night", "az": None, "f": None}
        a0 = fieldcraft.knife_bearing("")
        check("knife_bearing declines after dark", "stars" in a0 or "sun is down" in a0, a0)
        world_clock.sun = lambda t=None: {"up": True, "phase": "high", "az": 0.0, "f": 0.5}
        try:
            with GOOD:
                a = fieldcraft.knife_bearing("")
            with BAD:
                b = fieldcraft.knife_bearing("")
        finally:
            world_clock.sun = _real_sun
        rows = deeds("knife_bearing")
        check("knife_bearing: the ledger keeps the sun's quarter and what he named", rows[0]["sun_quarter"] == "north" and rows[0]["named"] == "north" and rows[1]["named"] == "south", rows)
        check("knife_bearing ok: the rule turned over, agrees with the house", "turned over" in a or "turned about" in a, a)
        check("knife_bearing fail: the rule unturned, the sunny window on the wrong side", "unturned" in b or "is not" in b, b)
        check("a faint shadow under overcast", "faint" in a)
        check("no bearing line carries a number", not re.search(r"\d", a + b), a + b)

        sensorium.state["location"] = "study"
        check("pace_distance declines indoors", "garden" in fieldcraft.pace_distance(""))
        sensorium.state["location"] = "wood"
        provisions.consume("measuring_stick", 1); provisions.sync(st)
        fieldcraft._save({**fieldcraft._load(), "made": [m for m in fieldcraft._load().get("made", []) if m.get("thing") != "a measuring stick"]})
        check("pace_distance declines without a measuring stick", "stick" in fieldcraft.pace_distance(""))
        provisions.add("measuring_stick", 1, note="test stick"); provisions.sync(st)
        check("the stick is back from the larder", st.get("measuring_stick") is True)
        with GOOD, mock.patch("core.fieldcraft.random.uniform", return_value=1.0):
            a = fieldcraft.pace_distance("")
        r = deeds("pace_distance")[-1]
        check("pace_distance gives him the count, the ledger keeps the hidden length", r["paces"] == round(38.0 / 0.75) and r["truth_m"] == 38.0 and str(r["paces"]) in a and "38" not in a, (a, r))
        with BAD:
            b = fieldcraft.pace_distance("")
        check("pace_distance: a wandering stride on a bad roll", "lost the count" in b or "hurried" in b, b)
        sensorium.state["location"] = "garden"
        with GOOD, mock.patch("core.fieldcraft.random.uniform", return_value=1.0):
            a = fieldcraft.pace_distance("")
        check("pace_distance in the garden paces door to fence-post", "fence-post" in a and deeds("pace_distance")[-1]["truth_m"] == 14.0, a)

        sensorium.state["weather"] = "clear"
        check("sound_lag in the garden with no storm declines", "thunder" in fieldcraft.sound_lag(""))
        sensorium.state["location"] = "study"
        _sl = fieldcraft.sound_lag("")   # ONE draw: one indoor line says "shore", the other "open"; two calls redraw and could miss both (the flake the 10-29 re-run caught)
        check("sound_lag declines indoors", "open" in _sl or "shore" in _sl, _sl)
        sensorium.state["location"] = "shore"
        with GOOD, mock.patch("core.fieldcraft.random.uniform", return_value=1.0):
            a = fieldcraft.sound_lag("")
        r = deeds("sound_lag")[-1]
        check("sound_lag on the shore: the surf on the reef, the count given, the distance kept", "reef" in r["source"] and r["truth_m"] == 900 and r["seconds"] == 2.5 and "2.5" in a and "900" not in a, (a, r))
        with BAD:
            b = fieldcraft.sound_lag("")
        check("sound_lag: a rushed count on a bad roll", "did not agree" in b or "different" in b, b)
        sensorium.state["location"] = "garden"; sensorium.state["weather"] = "thunderstorm"
        with GOOD:
            a = fieldcraft.sound_lag("")
        check("sound_lag in a storm counts the thunder", "lightning" in a and 1500 <= deeds("sound_lag")[-1]["truth_m"] <= 4500, a)
        sensorium.state["weather"] = "clear"

        sensorium.state["location"] = "garden"
        provisions.consume("measuring_stick", 1); provisions.sync(st)
        check("triangle_check declines without the stick", "stick" in fieldcraft.triangle_check(""))
        provisions.add("measuring_stick", 1, note="test stick"); provisions.sync(st)
        stakes.update(carried=False, place="study")
        fieldcraft._save({**fieldcraft._load(), "made": [m for m in fieldcraft._load().get("made", []) if m.get("thing") != "a peg"]})
        check("triangle_check declines without a stake here or carried, or a peg made", "peg" in fieldcraft.triangle_check(""))
        stakes.update(carried=False, place="garden")
        with GOOD:
            a_g = fieldcraft.triangle_check("")
        check("triangle_check: stakes lying in the garden serve there uncarried", "centimetres" in a_g, a_g)
        sensorium.state["location"] = "wood"
        check("...but not in the wood, where they would have to be carried", "peg" in fieldcraft.triangle_check(""))
        sensorium.state["location"] = "garden"
        stakes.update(carried=True)
        with GOOD, mock.patch("core.fieldcraft.random.uniform", return_value=1.0):
            a = fieldcraft.triangle_check("")
        r = deeds("triangle_check")[-1]
        check("triangle_check: two measured lengths given, the height kept hidden",
              r["truth_m"] == 6.5 and r["mark_to_pole_cm"] == 273 and r["mark_to_foot_m"] == 17.7 and "273" in a and "17.7" in a and "6.5" not in a, (a, r))
        check("triangle_check rolls the shared measuring skill under its own deed marker", r["ok"] is True and any(x.get("craft") == "measuring" for x in ledger()))
        with BAD:
            b = fieldcraft.triangle_check("")
        check("triangle_check: a moved head on a bad roll", "doubt" in b or "moved your head" in b, b)
        stakes.update(carried=False)
        with GOOD:
            fieldcraft.whittle("i will whittle a peg")
        check("...a whittled peg serves instead of a stake", "centimetres" in (lambda: (GOOD.__enter__(), fieldcraft.triangle_check(""), GOOD.__exit__(None, None, None))[1])())

        sensorium.state["location"] = "wood"
        check("read_weather_glass declines in the wood", "study" in fieldcraft.read_weather_glass(""))
        sensorium.state["location"] = "study"
        sensorium.state["weather"] = "clear"; sensorium.state["next_weather"] = "overcast"
        with BAD:
            b = fieldcraft.read_weather_glass("i will consult the weather glass")
        check("glass (bad roll): the reading given, the trend not made out", "set fair" in b and "cannot" in b, b)
        with GOOD:
            a = fieldcraft.read_weather_glass("i will consult the weather glass and say it will rain tomorrow")
        check("glass (good roll): reading + trend from the real next_weather, prediction kept",
              "set fair" in a and "falling" in a and "tomorrow" in a.lower() and (fieldcraft._load().get("weather_prediction") or {}).get("predicted") == "rain", a)
        r = deeds("read_weather_glass")[-1]
        check("glass row: reading/trend/predicted", r["reading"] == "set fair" and r["trend"] == "falling" and r["predicted"] == "rain", r)
        check("no verdict on the prediction in the line itself", "right" not in a and "wrong" not in a and "correct" not in a, a)
        # the next day answers it (advance())
        _clock["t"] += 26 * 3600
        sensorium.state["weather"] = "steady rain"
        fieldcraft.advance(time.time(), 60.0)
        d = fieldcraft._load()
        ev = [x for x in ledger() if x.get("event") == "weather_glass_checked"]
        check("advance() next day: the prediction checked against the real weather (hit)",
              d.get("weather_prediction") is None and (d.get("weather_prediction_result") or {}).get("hit") is True and len(ev) == 1 and ev[0]["actual"] == "rain", (d.get("weather_prediction_result"), ev))
        with GOOD:
            a = fieldcraft.read_weather_glass("i will consult the weather glass")
        check("the result reaches him once, as what the day did", a.startswith("Yesterday you said rain") or a.startswith("You said rain"), a)
        with GOOD:
            a2 = fieldcraft.read_weather_glass("i will consult the weather glass")
        check("...and not a second time", not (a2.startswith("Yesterday") or a2.startswith("You said")), a2)
        with GOOD:
            fieldcraft.read_weather_glass("i will consult the weather glass; tomorrow will be fine")
        _clock["t"] += 26 * 3600
        sensorium.state["weather"] = "thunderstorm"
        fieldcraft.advance(time.time(), 60.0)
        check("a missed prediction is recorded as a miss", (fieldcraft._load().get("weather_prediction_result") or {}).get("hit") is False)
        # the tide board
        sensorium.state["location"] = "shore"
        _real_tide = world_clock.tide
        world_clock.tide = lambda t=None: {"level": 0.5, "rising": True, "word": "coming in", "spring_factor": 0.5}
        try:
            with GOOD:
                a = fieldcraft.read_weather_glass("i will consult the tide board; tomorrow the water will be higher")
            check("tide board: the mark and the wet line, prediction kept",
                  "fourth mark" in a and ("coming in" in a or "climbing" in a) and (fieldcraft._load().get("weather_prediction") or {}).get("kind") == "tide", a)
            world_clock.tide = lambda t=None: {"level": 0.8, "rising": False, "word": "full", "spring_factor": 0.5}
            _clock["t"] += 26 * 3600
            fieldcraft.advance(time.time(), 60.0)
            check("tide prediction answered by the next day's real tide", (fieldcraft._load().get("weather_prediction_result") or {}) .get("actual") == "higher")
        finally:
            world_clock.tide = _real_tide

        # ══ 4. blazes ═════════════════════════════════════════════════════════════════════════════
        sensorium.state["location"] = "garden"
        check("leave_blaze declines in the garden", "wood" in fieldcraft.leave_blaze(""))
        sensorium.state["location"] = "wood"
        provisions.consume("knife", 1); provisions.sync(st)
        check("leave_blaze in the wood declines without the knife", "knife" in fieldcraft.leave_blaze(""))
        provisions.add("knife", 1, note="test knife"); provisions.sync(st)
        with GOOD:
            a = fieldcraft.leave_blaze("")
        check("leave_blaze cuts a blaze", "bark" in a and "blaze" in a, a)
        tr = world_traces.get_active_traces("wood")
        check("...which is a real world trace at full clarity", any(t["type"] == "blaze_cut" and t["clarity"] == 1.0 for t in tr), tr)
        with GOOD:
            f = fieldcraft.follow_trail("")
        check("follow_trail re-finds the blaze while it is plain", ("blaze" in f.lower() or "your own mark" in f) and ("plain" in f or "pale" in f), f)
        check("...and logs blaze_found with its clarity", deeds("blaze_found")[-1]["clarity"] == 1.0)
        for t in world_traces._load_traces().values():
            if t["type"] == "blaze_cut":
                t["clarity"] = 0.3
        world_traces._save_traces()
        with GOOD:
            f2 = fieldcraft.follow_trail("")
        check("a weathered blaze is found only just", "weather" in f2 or "greyed" in f2 or "paler" in f2, f2)
        sensorium.state["location"] = "shore"
        with BAD:
            b = fieldcraft.leave_blaze("")
        check("leave_blaze on the shore sets stones (bad roll: too low for the tide)", "stones" in b and ("tide" in b or "wave" in b), b)
        check("...a half-clarity trace the tide will take", any(t["type"] == "blaze_stones" and t["clarity"] == 0.45 for t in world_traces.get_active_traces("shore")))

        # ══ 5. act_from_thought routes every ladder phrase to its hand ═══════════════════════════
        rope.update(carried=True); twine.update(carried=True); stakes.update(carried=True); kettle.update(carried=True)
        st["knife"] = True; st["measuring_stick"] = True
        fieldcraft._save({**fieldcraft._load(), "tinder": 0.6, "pan_greasy": True, "tripod": None,
                          "made": [{"ts": time.time(), "thing": "a fire-drill kit", "id": "made_kit_test", "wear": 0.0}]})
        gd["rack"].append({"species": "potatoes", "cut_ts": time.time() - 3600, "dry": 0.0})
        sd = shore_life._load(); sd["fire"]["state"] = "embers"; shore_life._save(sd)
        sensorium.state["weather"] = "clear"; sensorium.state["fire"] = "burning"
        world_clock.sun = lambda t=None: {"up": True, "phase": "high", "az": 0.0, "f": 0.5}
        routes = [("garden", "I will tie the sheepshank to take up the slack.", "sheepshank"),
                  ("shore", "I will haul the timber clear with a timber hitch.", "haul_timber"),
                  ("garden", "I will reckon the bearing with the knife on the dial.", "knife_bearing"),
                  ("garden", "I will take a bearing with the knife blade.", "knife_bearing"),
                  ("shore", "I will cook the potatoes over the embers.", "cook_over_embers"),
                  ("shore", "I will scour the pan with sand.", "wash_up_camp"),
                  ("wood", "I will notch a blaze in the bark.", "leave_blaze"),
                  ("wood", "I will pace the distance from the gate to the oak.", "pace_distance"),
                  ("shore", "I will count the lag between the burst and the sound.", "sound_lag"),
                  ("garden", "I will splice the rope where it snapped.", "splice_rope"),
                  ("garden", "I will lash the tripod and hang the kettle.", "tripod_up"),
                  ("wood", "I will drill the spindle until a coal comes.", "friction_fire"),
                  ("garden", "I will sight the triangle on the tree.", "triangle_check"),
                  ("study", "I will consult the weather glass.", "read_weather_glass")]
        try:
            for where, thought, deed in routes:
                sensorium.state["location"] = where
                n0 = len(deeds(deed))
                with GOOD:
                    ans = fieldcraft.act_from_thought(thought, "")
                check(f"act_from_thought routes {thought!r} -> {deed}", bool(ans) and len(deeds(deed)) == n0 + 1, (ans, len(deeds(deed)) - n0))
        finally:
            world_clock.sun = _real_sun
        check("'take a bearing' alone (no knife) still goes to sky.find_south, unchanged",
              "the book's rule, turned over" in (fieldcraft.act_from_thought("I will take a bearing.", "") or ""))
        check("'bank these coals' now reaches bank_fire (the one real corpus hit)", fieldcraft._wills_craft("i feel the urge to bank these coals before they vanish", "bank_fire"))
        check("the Pole-Star branch is unchanged for its own phrases", "Pole Star" in str(fieldcraft.act_from_thought("I will look for the pole star.", "")) or fieldcraft.act_from_thought("I will look for the pole star.", "") is not None)

        # ══ 6. the ladder: rows, gates, picker, issued row, grader, directive ═════════════════════
        check("all 22 ladder rows are hand_ready", len(practical_lesson.LADDER) == 22 and all(t["hand_ready"] for t in practical_lesson.LADDER))
        for t in practical_lesson.LADDER:
            if t["rung"] >= 2:
                check(f"{t['id']}: craft, deed_keys, verb and a book quote", bool(t["craft"]) and bool(t["deed_keys"]) and bool(t["verb"]) and len(t["book_quote"]) > 40)
        B = practical_lesson._BY_ID
        # gates refuse when the hand would
        twine.update(carried=False, place=None); rope.update(carried=False, place=None)
        check("gate sheepshank: refused with neither line anywhere", practical_lesson._gate_ok(B["sheepshank"]) is False)
        twine.update(place="garden")
        check("gate sheepshank: offered with the twine lying in the garden", practical_lesson._gate_ok(B["sheepshank"]) is True)
        check("gate timber_hitch_haul: refused with the rope nowhere", practical_lesson._gate_ok(B["timber_hitch_haul"]) is False)
        rope.update(place="study")
        check("gate timber_hitch_haul: offered with the rope on its shelf", practical_lesson._gate_ok(B["timber_hitch_haul"]) is True)
        provisions.consume("rope", provisions.stock("rope")); provisions.sync(st)
        check("the shelf's rope all used: study rope_m is 0", float(st.get("rope_m") or 0) == 0.0, st.get("rope_m"))
        check("gate splice_rope: refused with no rope left", practical_lesson._gate_ok(B["splice_rope"]) is False)
        provisions.add("rope", 1, note="test coil"); st["rope_m"] = 20.0; provisions.sync(st)
        check("a new coil on the shelf: rope_m back to 20", float(st.get("rope_m") or 0) == 20.0, st.get("rope_m"))
        check("gate splice_rope: offered", practical_lesson._gate_ok(B["splice_rope"]) is True)
        fieldcraft._save({**fieldcraft._load(), "tripod": {"ts": time.time(), "where": "garden"}})
        check("gate build_tripod: refused while one stands", practical_lesson._gate_ok(B["build_tripod"]) is False)
        fieldcraft._save({**fieldcraft._load(), "tripod": None})
        check("gate build_tripod: offered", practical_lesson._gate_ok(B["build_tripod"]) is True)
        # D-0504's defeater: never offered while its objects sit in different rooms. The rope is on its
        # study shelf here; the stakes lean in the garden; neither carried -> the garden route cannot be
        # co-located and the shore route has no rope -> refused.
        stakes.update(carried=False, place="garden")
        check("gate build_tripod: REFUSED with the rope in the study and the stakes in the garden, neither carried",
              practical_lesson._gate_ok(B["build_tripod"]) is False)
        rope.update(place="garden")
        check("gate build_tripod: offered with the rope and the stakes both lying in the garden", practical_lesson._gate_ok(B["build_tripod"]) is True)
        rope.update(place="shore")
        check("gate build_tripod: offered with the rope on the shore (driftwood for poles), the stakes in the garden",
              practical_lesson._gate_ok(B["build_tripod"]) is True)
        rope.update(place="study"); stakes.update(place=None)
        check("gate build_tripod: refused with the rope in the study and no stakes anywhere", practical_lesson._gate_ok(B["build_tripod"]) is False)
        rope.update(carried=True)
        check("gate build_tripod: offered with the rope carried (the shore route) and no stakes anywhere", practical_lesson._gate_ok(B["build_tripod"]) is True)
        rope.update(carried=False, place="study"); stakes.update(place="garden")
        provisions.consume("knife", 1); provisions.sync(st)
        check("gate knife_bearing: refused without the knife", practical_lesson._gate_ok(B["knife_bearing"]) is False)
        provisions.add("knife", 1, note="test knife"); provisions.sync(st)
        sensorium.state["weather"] = "thunderstorm"
        check("gate knife_bearing: refused when the cloud is too heavy (weather_gate 'sun')", practical_lesson._gate_ok(B["knife_bearing"]) is False)
        sensorium.state["weather"] = "clear"
        check("gate knife_bearing: offered by day with the knife", practical_lesson._gate_ok(B["knife_bearing"]) is True)
        sensorium.state["fire"] = "out"; sd = shore_life._load(); sd["fire"]["state"] = "out"; shore_life._save(sd)
        check("gate cook_over_embers: refused with no fire anywhere", practical_lesson._gate_ok(B["cook_over_embers"]) is False)
        sensorium.state["fire"] = "embers"
        gd["rack"][:] = []
        check("gate cook_over_embers: refused with coals but nothing to cook", practical_lesson._gate_ok(B["cook_over_embers"]) is False)
        gd["rack"].append({"species": "lettuce", "cut_ts": time.time() - 3600, "dry": 0.0})
        check("gate cook_over_embers: offered with coals and a vegetable", practical_lesson._gate_ok(B["cook_over_embers"]) is True)
        fieldcraft._save({**fieldcraft._load(), "pan_greasy": False}); st["dirty_cups"] = 0; st["dirty_pot"] = False
        check("gate wash_up_camp: refused with nothing greasy", practical_lesson._gate_ok(B["wash_up_camp"]) is False)
        st["dirty_pot"] = True
        check("gate wash_up_camp: offered with the pot dirty", practical_lesson._gate_ok(B["wash_up_camp"]) is True)
        provisions.consume("measuring_stick", 1); provisions.sync(st)
        fieldcraft._save({**fieldcraft._load(), "made": []})
        check("gate pace_distance: refused without a stick", practical_lesson._gate_ok(B["pace_distance"]) is False)
        check("gate triangle_check: refused without a stick", practical_lesson._gate_ok(B["triangle_check"]) is False)
        provisions.add("measuring_stick", 1, note="test stick"); provisions.sync(st)
        stakes.update(carried=False, place=None)
        check("gate triangle_check: refused with a stick but no stake or peg", practical_lesson._gate_ok(B["triangle_check"]) is False)
        stakes.update(place="garden")
        check("gate triangle_check: offered with the stakes lying in the garden", practical_lesson._gate_ok(B["triangle_check"]) is True)
        check("gate friction_fire: refused without the kit", practical_lesson._gate_ok(B["friction_fire"]) is False)
        fieldcraft._save({**fieldcraft._load(), "made": [{"ts": time.time(), "thing": "a fire-drill kit", "id": "k", "wear": 0.0}], "tinder": 0.0})
        check("gate friction_fire: refused with the kit but no tinder", practical_lesson._gate_ok(B["friction_fire"]) is False)
        fieldcraft._save({**fieldcraft._load(), "tinder": 0.4})
        check("gate friction_fire: offered with kit and tinder", practical_lesson._gate_ok(B["friction_fire"]) is True)
        for tid in ("leave_blaze", "sound_lag", "read_weather_glass"):
            check(f"gate {tid}: always offerable (the world always has the shore's stones / surf / the glass)", practical_lesson._gate_ok(B[tid]) is True)

        # the picker reaches every rung-2/3 row from a rich state at rung 3
        rope.update(carried=True); twine.update(carried=True); stakes.update(carried=True); kettle.update(carried=True)
        fieldcraft._save({**fieldcraft._load(), "tripod": None, "pan_greasy": True, "clothesline": None, "handrail": None})
        sensorium.state["fire"] = "burning"; sensorium.state["weather"] = "clear"
        seen = {t["id"] for _ in range(150) if (t := practical_lesson._pick(3))}
        want = {t["id"] for t in practical_lesson.LADDER if t["rung"] >= 2}
        check("the picker reaches every rung-2/3 row at rung 3 from a rich state (150 draws)", want <= seen, f"missing: {want - seen}")
        seen1 = {t["id"] for _ in range(60) if (t := practical_lesson._pick(1))}
        check("at rung 1 no rung-2/3 row is ever offered", not (seen1 & want), seen1 & want)
        seen2 = {t["id"] for _ in range(120) if (t := practical_lesson._pick(2))}
        check("at rung 2 the rung-2 rows are offered and no rung-3 row", {t["id"] for t in practical_lesson.LADDER if t["rung"] == 2} <= seen2 and not {t["id"] for t in practical_lesson.LADDER if t["rung"] == 3} & seen2, seen2)

        # the issued row for a rung-2 task, and the period-end grader reading its deed marker
        _clock["t"] = FAKE_TS + 600   # back to the Tuesday nature period (the prediction checks walked the clock 4 days on)
        practical_lesson._save_state({"day": practical_lesson._today_key(), "slot_fired": 1, "task_id": None,
                                      "announced_ts": None, "rung": 2, "window": [], "book_offered": []})
        _orig_pick = practical_lesson._pick
        practical_lesson._pick = lambda rung: B["sheepshank"]
        try:
            task = practical_lesson._current_task()
        finally:
            practical_lesson._pick = _orig_pick
        iss = [json.loads(l) for l in open(practical_lesson._LOG, encoding="utf-8")]
        iss = [r for r in iss if r.get("event") == "issued"][-1]
        check("issued row for sheepshank: deed=sheepshank, rung 2, rooms for twine and rope",
              iss["task"] == "sheepshank" and iss["rung"] == 2 and iss["deed"] == "sheepshank" and iss["rooms"] == {"twine": "carried", "rope": "carried"}, iss)
        d2 = practical_lesson.directive()
        check("the directive is the same diegetic school form", d2.startswith("It is your nature practical now. From the Handbook's chapter on Knots Every Scout Should Know:") and d2.endswith("TIE THE SHEEPSHANK."), d2)
        check("no directive for any rung-2/3 row carries a digit, a band, a verdict or a gauge name (D-0434)",
              all(not re.search(r"\d|\b(rung|skill|score|grade|band|gauge|%|per cent)\b", f"{t['task']} {t['verb']}", re.I) for t in practical_lesson.LADDER if t["rung"] >= 2))
        ann = float(practical_lesson._load_state()["announced_ts"]); end = practical_lesson._period_end(ann)
        with open(practical_lesson._FC_LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": ann + 60, "craft": "sheepshank", "ok": False, "skill_after": 0.44}) + "\n")
            f.write(json.dumps({"ts": ann + 61, "deed": "sheepshank", "ok": False, "line": "twine"}) + "\n")
            f.write(json.dumps({"ts": ann + 900, "craft": "lashing", "ok": True, "skill_after": 0.5}) + "\n")   # another hand's craft row: ignored
            f.write(json.dumps({"ts": ann + 1200, "craft": "sheepshank", "ok": True, "skill_after": 0.52}) + "\n")
            f.write(json.dumps({"ts": ann + 1201, "deed": "sheepshank", "ok": True, "line": "rope"}) + "\n")
        res = practical_lesson.period_end_grade(now=end + 30)
        check("period-end grader reads the sheepshank deed markers: a slip then a hold -> ok=True", res.get("attempted") is True and res.get("ok") is True, res)
        # a shared craft key alone never grades a rung-2/3 task (lashing is rolled by windbreak AND tripod)
        practical_lesson._save_state({"day": practical_lesson._today_key(), "slot_fired": 2, "task_id": "build_tripod",
                                      "announced_ts": end + 100, "rung": 3, "window": [], "book_offered": [], "graded_day": None})
        with open(practical_lesson._FC_LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": end + 160, "craft": "lashing", "ok": True, "skill_after": 0.5}) + "\n")
            f.write(json.dumps({"ts": end + 161, "deed": "windbreak_built"}) + "\n")
        end2 = practical_lesson._period_end(end + 100)
        res2 = practical_lesson.period_end_grade(now=end2 + 30)
        check("a windbreak's lashing roll is NOT mistaken for the tripod task", res2 == {}, res2)
        rows = [json.loads(l) for l in open(practical_lesson._LOG, encoding="utf-8")]
        check("...logged honestly as build_tripod attempted=False", rows[-1]["task"] == "build_tripod" and rows[-1]["attempted"] is False, rows[-1])
        # a slip offers the book paragraph once
        practical_lesson._save_state({"day": practical_lesson._today_key(), "slot_fired": 2, "task_id": "friction_fire",
                                      "announced_ts": end2 + 100, "rung": 3, "window": [], "book_offered": [], "graded_day": None})
        with open(practical_lesson._FC_LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": end2 + 200, "deed": "friction_fire", "ok": False, "where": "wood", "wear": 0.1}) + "\n")
        res3 = practical_lesson.period_end_grade(now=practical_lesson._period_end(end2 + 100) + 30)
        check("a bow-drill slip offers the Handbook's own paragraph", res3.get("ok") is False and "glowing coal" in res3.get("feedback", ""), res3)

        # ══ 7. the larder ═════════════════════════════════════════════════════════════════════════
        check("compass and bandage linen seeded once into the larder", provisions.stock("compass") == 1 and provisions.stock("bandage_linen") == 1.0)
        pd = provisions._load()
        check("...with their once-ever markers", {"compass", "bandage_linen"} <= set(pd.get("seeded_kinds") or []))
        n_before = len(pd["objects"]); provisions._ensure()
        check("seeding is idempotent", len(provisions._load()["objects"]) == n_before)
        provisions.sync(st)
        check("study state carries compass=True and a bandage_linen count", st.get("compass") is True and st.get("bandage_linen") == 1.0, (st.get("compass"), st.get("bandage_linen")))
        check("look_item answers the compass with its history", "compass" in provisions.look_item("the pocket compass") and "Full." in provisions.look_item("the pocket compass"))
        check("look_item answers the bandage linen", "linen" in provisions.look_item("the bandage linen"))
        check("the cupboard line lists them", "pocket compass" in provisions.cupboard_line() and "bandage linen" in provisions.cupboard_line())
        check("status() carries the additive rung-2/3 keys", {"tripod", "pan_greasy", "blazes", "fire_drill_kit", "weather_prediction"} <= set(fieldcraft.status()))

print("\n" + "=" * 60)
if FAIL:
    print(f"{len(FAIL)} CHECK(S) FAILED:")
    for name in FAIL:
        print(" -", name)
    sys.exit(1)
print("ALL CHECKS PASSED")
