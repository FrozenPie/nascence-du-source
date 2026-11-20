"""
Nascence — FIELDCRAFT: what the books he has read let him DO (2026-08-22, founder: "examine the scouts handbook —
he has read this extensively. Are there things we should be adding seeing as the knowledge is already present?").

He has read, to the end: the Boy Scouts Handbook (1911), The Scouting Guide to Survival, The Book of Camp-Lore and
Woodcraft, Two Little Savages, and Knots, Splices and Rope Work. His study notes on the knots book turned it into "a
profound metaphor for identity" — the knowledge became philosophy because the world gave it nothing to tie. This module
gives the knowledge hands. Each craft is a SKILL that starts where the book left it (read = 0.4) and improves only by
doing; the world answers honestly when the knot slips or the fire will not catch.

  KNOTS      bowline · clove hitch · reef · timber hitch · square lashing. Used by: a CLOTHESLINE (twine between the
             tree and the fence — the wet coat dries in sun and wind, not only by the fire); a WINDBREAK on the shore
             (driftwood lashed to stakes — a sheltered standpoint the thermal field reads); a HANDRAIL on the steep path
             (twine from the gate to the first oak — the gale no longer slows the climb so much); staking the peas.
  FIRE       BANK the embers under ash at night (the Handbook's way) — in the morning they are alive and the fire is
             relit without a match; a TINDER TIN (dry bark, ponga fluff, paper — gathered, kept dry); FLINT AND STEEL
             from the larder (works when the matches are wet or gone, with tinder); the fire-lay (kindling laid right
             catches wet wood better).
  MEASURING  the tree's height by its shadow (the Handbook's method): his stick, his pace, the sun — the world gives him
             the two shadow-lengths truthfully; the height he works out is HIS (and may be wrong; the truth is hidden).
  WHITTLING  a pocket knife (the larder): pegs for the clothesline, a spoon, a walking stick — made things with his
             authorship in their biography (keepable).
  TRACKING   follow a trail — the cat's prints, the slug's silver, hedgehog prints after a damp night — to where it
             leads, or to where it ends.
  WATER      the barrel goes green in warm weeks (the Survival Guide: boil it, or fetch from the spring).

The Handbook is northern: it teaches the Pole Star. This sky has none — see core/sky.py.
Zero LLM. Fail-open. Additive everywhere.
"""
from __future__ import annotations

import json
import logging
import math
import random
import time
from pathlib import Path

from core import profile

logger = logging.getLogger("nascence.fieldcraft")
_DATA = Path(__file__).parent.parent / "data"
_F = _DATA / "fieldcraft.json"
_LEDGER = _DATA / "fieldcraft_ledger.jsonl"

KNOTS = {"bowline": "a loop that will not slip", "clove_hitch": "a hitch to a post or stake", "reef": "two ends joined flat",
         "timber_hitch": "a hitch that grips a log", "lashing": "two spars bound square",
         # PRACTICAL SCHOOL rung 1 (2026-09-05, J-0627, D-0159 §3/§7): the whipping needed as its own task.
         "whip_end": "a rope's end bound so it cannot fray",
         # PRACTICAL SCHOOL rungs 2-3 (2026-10-28, J-2483, D-0504 released J-0628's spec): two more knots
         # from the Handbook's own list, each a skill that starts where the book left it.
         "sheepshank": "a rope shortened without cutting it", "short_splice": "two rope ends married strand through strand"}
CRAFTS = ("knots", "fire_lay", "whittling", "tracking", "measuring", "douse_fire",
          # PRACTICAL SCHOOL rungs 2-3 (2026-10-28, J-2483): the crafts the new hands below roll. Additive —
          # _try() reads a missing key as BOOKS_READ_START, so an already-running fieldcraft.json needs no migration.
          "bearing", "cooking", "wash_up", "blazing", "pacing", "sound_lag", "friction_fire", "weather_reading")
BOOKS_READ_START = 0.4      # what the books give him before the first attempt


def _load() -> dict:
    try:
        from core import store_persist as _sp   # J-4442 (F-5157): loud on damage, falls back to fieldcraft.json.prev
        return _sp.read_json_durable(_F, "fieldcraft", logger, guard=profile.guard_path)
    except Exception:
        return {"skill": {k: BOOKS_READ_START for k in list(KNOTS) + list(CRAFTS)}, "clothesline": None, "windbreak": None, "handrail": None,
                "banked": None, "tinder": 0.3, "made": [], "barrel_algae": 0.0, "attempts": {}}


def _save(d: dict) -> None:
    path = profile.guard_path(_F)   # J-0727: real data/ only if this process is live; raises if not (D-0179, J-0704)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        from core import store_persist as _sp
        _sp.write_text_durable(path, json.dumps(d, ensure_ascii=False))   # J-4442 (F-5157): was in place; now fsync + .prev
    except Exception:
        pass


def _log(rec: dict) -> None:
    path = profile.guard_path(_LEDGER)   # J-0727: raises before any I/O (and before the activity_memory cross-link below) if non-live (D-0179, J-0704)
    try:
        if rec.get("deed"):
            try:   # CROSS-LINK (2026-08-22): a deed here is a deed in his activity memory too
                from core import activity_memory as _am
                _am.record(str(rec["deed"]), str(rec.get("species") or rec.get("item") or rec.get("what") or rec.get("thing") or rec.get("tool") or rec.get("text") or ""))
            except Exception:
                pass
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": round(time.time(), 1), **rec}, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _where() -> str:
    try:
        from core import sensorium as _s
        return _s.state.get("location", "study")
    except Exception:
        return "study"


def _try(d: dict, skill: str) -> bool:
    """Skill-weighted success; every attempt teaches (success more than failure)."""
    s = float(d["skill"].get(skill, BOOKS_READ_START))
    ok = random.random() < 0.25 + 0.7 * s
    d["skill"][skill] = round(min(1.0, s + (0.08 if ok else 0.04)), 3)
    d["attempts"][skill] = int(d["attempts"].get(skill, 0)) + 1
    _log({"craft": skill, "ok": ok, "skill_after": d["skill"][skill]})
    return ok


def _has_twine() -> bool:
    try:
        from core import garden as _g
        it = _g._load()["items"].get("twine", {})
        return bool(it.get("carried") or it.get("place") == _where())
    except Exception:
        return False


# ── KNOTS: the clothesline, the windbreak, the handrail ─────────────────────────────────────────
def clothesline(txt: str = "") -> str:
    d = _load(); here = _where()
    if here != "garden":
        return "A line would go up in the garden, between the tree and the fence-post."
    if d.get("clothesline"):
        return "The line is already up between the tree and the fence."
    if not _has_twine():
        return "You have nothing to string a line with; the twine is not here."
    ok = _try(d, "clove_hitch") and _try(d, "bowline")
    if not ok:
        _save(d); return "You tie the twine to the fence-post and walk it to the tree, pull it taut and tie off — and the first knot slips and the line sags to the grass. You coil it up to try again."
    d["clothesline"] = {"ts": time.time()}; _save(d); _log({"deed": "clothesline_up"})
    return "You tie the twine off to the fence-post with a hitch, walk it to the low limb of the tree, haul it taut and make it fast with a loop that will not slip. A line, shoulder-high, across the lawn."


def hang_coat(txt: str = "") -> str:
    d = _load()
    if not d.get("clothesline"):
        return ""
    if _where() != "garden":
        return "The line is in the garden."
    try:
        from core import study_life as _sl
        st = _sl._st()
        if st.get("coat_on"):
            st["coat_on"] = False
        if float(st.get("coat_wet", 0)) < 0.1:
            return "The coat is dry; no need to hang it."
        st["coat_on_line"] = True; st["items"]["coat"]["place"] = "garden"
        _log({"deed": "coat_on_line"})
        return "You peg the wet coat over the line by its shoulders. It hangs heavy, dripping from the hem, and turns slowly in the air."
    except profile.NonLiveWriteError:
        # J-0727: let D-0179's hard-raise (guard_path(), F-1024) reach this function's own caller
        # instead of being swallowed by the broader except below — fieldcraft.py's own deed functions
        # had never been audited for this (F-1045); mirrors J-0714's fix to the other 10 modules.
        raise
    except Exception:
        return ""


def windbreak(txt: str = "") -> str:
    d = _load(); here = _where()
    if here != "shore":
        return "A windbreak would be built on the shore, up by the driftwood where the wind comes off the water."
    if d.get("windbreak") and (time.time() - float(d["windbreak"]["ts"])) < 30 * 86400:
        return "Your windbreak stands where you built it, against the bank above the driftwood tangle."
    if not _has_twine():
        return "You would need the twine to lash it; it is not here."
    try:
        from core import garden as _g
        g = _g._load(); stakes = g["items"].get("stakes", {})
        if not (stakes.get("carried")):
            return "You would need the stakes from the lean-to to drive in; you have not brought them."
    except Exception:
        pass
    ok = _try(d, "lashing") and _try(d, "timber_hitch")
    if not ok:
        _save(d); return "You drive two stakes into the shingle, drag driftwood up and lash it across — and the first gust lifts the whole thing and lays it flat. The lashing was wrong. You stand in the wind and look at it."
    d["windbreak"] = {"ts": time.time()}; _save(d); _log({"deed": "windbreak_built"})
    return "You drive two stakes into the shingle against the bank, drag up the longest driftwood, and lash it across them square and tight. Behind it, out of the wind, the air goes still and the sea's roar drops by half."


def handrail(txt: str = "") -> str:
    d = _load(); here = _where()
    if here not in ("garden", "wood"):
        return "The handrail would run down the steep path from the gate into the wood."
    if d.get("handrail"):
        return "The rope is already up along the path, tree to tree."
    if not _has_twine():
        return "You have no line for it; the twine is not here."
    ok = _try(d, "clove_hitch") and _try(d, "bowline")
    if not ok:
        _save(d); return "You run the twine from the gate-post down to the first trunk and tie it off — and it comes undone in your hand when you lean on it. Not that knot, then."
    d["handrail"] = {"ts": time.time()}; _save(d); _log({"deed": "handrail_up"})
    return "You run the twine from the gate-post down the steep part of the path, hitching it trunk to trunk, and tie it off taut. A hand-line for the wet days and the wind."


def has_handrail() -> bool:
    try:
        return bool(_load().get("handrail"))
    except Exception:
        return False


def windbreak_shelter() -> float:
    """Thermal: on the shore, standing in the windbreak's lee cuts the wind by half."""
    try:
        d = _load()
        if not d.get("windbreak"):
            return 0.0
        from core import locomotion as _loco
        return 0.5 if _loco.position_standpoint("shore") == "in_the_windbreak" else 0.0
    except profile.NonLiveWriteError:
        # J-0794: locomotion.position_standpoint() can now raise non-live (J-0778, via its own
        # get_position() self-heal-write branch) -- re-raise so this fence's guarantee reaches this
        # module's own external caller (thermal.field_at()'s shore branch) instead of a silent 0.0.
        raise
    except Exception:
        return 0.0


def whip_end(txt: str = "") -> str:
    """PRACTICAL SCHOOL rung 1 (2026-09-05, J-0627, D-0159 §3/§7) — a hand that did not exist before this
    build. "The commonest method of whipping is as follows: lay the end of a piece of twine along the end
    of the rope... wind the standing part around it... pull it back tight and cut off close to the rope."
    (Boy Scouts Handbook, 1911, p.49). The world's own answer is DELAYED — the ladder's words are "stays
    bound or frays, checked days later" — so what is recorded here is the immediate skill-weighted
    attempt (whether the winding was tight and true); whether it actually held is for whoever next looks
    at that end of the rope to find. No separate re-check scheduler is built this pass (see the finding
    that shipped alongside this hand)."""
    d = _load(); here = _where()
    try:
        from core import study_life as _sl
        rope = _sl._st().get("items", {}).get("rope", {})
        rope_here = bool(rope.get("carried")) or rope.get("place") == here
    except Exception:
        rope_here = False
    if not (rope_here and _has_twine()):
        return "You would need the rope in hand, and the twine to whip it with; you have not got both here."
    ok = _try(d, "whip_end"); _save(d)
    if not ok:
        _log({"deed": "whip_end", "ok": False})
        return "You lay the twine along the rope's end and start winding — and it slips loose before the last tuck goes through. You coil it and try again another time."
    d.setdefault("made", []).append({"ts": time.time(), "thing": "whipped rope end", "where": here})
    _save(d); _log({"deed": "whip_end", "ok": True})
    return ("You lay the end of the twine along the rope, hold it with your thumb, and wind the standing part around it and the rope, turn "
            "after turn, until the twine's own end is covered; then a loop back on the rope's end, wound over with the rest, pulled through "
            "and drawn up tight, close to the rope, the tail cut off short. Bound; it will not fray now — or it will show frayed again, "
            "days from now, if the winding was not tight enough.")


# ── FIRE: banking, tinder, flint and steel ──────────────────────────────────────────────────────
def bank_fire(txt: str = "") -> str:
    d = _load()
    try:
        from core import sensorium as _s, study_life as _sl
        if _where() != "study":
            return ""
        fire = _s.state.get("fire", "out")
        if fire == "out":
            return "There is nothing in the grate to bank."
        st = _sl._st()
        if float(st.get("ash", 0)) < 0.15:
            return "There is not enough ash in the grate to bank the fire under; it would want a good bed of it."
        ok = _try(d, "fire_lay")
        d["banked"] = {"ts": time.time(), "ok": ok}; _s.state["fire"] = "embers"; _s.state["fire_fuel"] = max(0.3, float(_s.state.get("fire_fuel", 0.3)))
        _s._save_now(); _save(d); _log({"deed": "bank_fire", "ok": ok})
        return ("You rake the embers together, lay a log across them and cover the whole with a blanket of ash, the way the book has it. The glow goes; the grate holds its heat under the grey." if ok
                else "You rake the embers together and cover them with ash — too thin, and some of the red shows through. You add more and hope.")
    except profile.NonLiveWriteError:
        # J-0727: covers both this function's own _save()/_log() and its own call into sensorium's
        # already-guarded _save_now() above — let the raise reach the caller instead of collapsing
        # into the broader except below (F-1045; mirrors J-0714's fix to the other 10 modules).
        raise
    except Exception:
        return ""


def banked_alive() -> bool:
    """Sensorium asks at dawn / when he lights: are the banked embers alive? Decays with hours."""
    try:
        d = _load(); b = d.get("banked")
        if not b:
            return False
        hours = (time.time() - float(b["ts"])) / 3600.0
        return hours < (10 if b.get("ok") else 5)
    except Exception:
        return False


def uncover_fire(txt: str = "") -> str:
    d = _load()
    try:
        from core import sensorium as _s, study_life as _sl
        if _where() != "study" or not d.get("banked"):
            return ""
        alive = banked_alive(); d["banked"] = None; _save(d)
        if not alive:
            _s.state["fire"] = "out"; _s.state["fire_fuel"] = 0.0; _s._save_now(); _log({"deed": "uncover_fire", "alive": False})
            return "You scrape the ash back from the grate: grey through and through, cold. The banking did not hold."
        st = _sl._st()
        if float(st.get("kindling", 0)) < 0.1:
            return "You scrape the ash back and there is red under it, alive — but the kindling box is empty; you have nothing to feed it and it fades."
        st["kindling"] = max(0.0, float(st["kindling"]) - 0.15); _s.state["fire"] = "burning"; _s.state["fire_fuel"] = 0.8; _s.state["hand_lit"] = True; _s._save_now()
        _log({"deed": "uncover_fire", "alive": True}); return "You scrape the ash back and there is red under it, alive. A handful of kindling on the embers, a breath, and the fire stands up again without a match."
    except profile.NonLiveWriteError:
        # J-0727: covers this function's own _save(d)/_log() above and its calls into sensorium's
        # already-guarded _save_now() — let the raise reach the caller instead of collapsing into the
        # broader except below (F-1045; mirrors J-0714's fix to the other 10 modules).
        raise
    except Exception:
        return ""


def gather_tinder(txt: str = "") -> str:
    d = _load(); here = _where()
    if here not in ("wood", "shore", "garden"):
        return ""
    try:
        from core import sensorium as _s
        wet = _s.state.get("weather", "") in ("drizzle", "steady rain", "wind and rain", "thunderstorm")
    except Exception:
        wet = False
    if wet:
        return "Everything is wet through; there is no dry tinder to be had today. It would want a dry day, and the underside of things."
    what = {"wood": "dry bark from the underside of a fallen limb and the brown fluff from the base of the tree-ferns", "shore": "dry grass from the top of the bank and a handful of sun-bleached weed", "garden": "dry grass and a few old seed-heads"}[here]
    d["tinder"] = min(1.0, float(d.get("tinder", 0)) + 0.4); _save(d); _log({"deed": "tinder", "where": here})
    return f"You fill the tin with {what}, pressed down, and pocket it. Dry, and kept dry, it will catch a spark."


def strike_flint(txt: str = "") -> str:
    d = _load()
    try:
        from core import sensorium as _s, study_life as _sl
        if _where() != "study":
            return ""
        if not _sl._st().get("flint"):
            return "There is no flint and steel in the house."
        if float(d.get("tinder", 0)) < 0.1:
            return "You have no tinder; a spark on a cold log does nothing. The tin is empty."
        ok = _try(d, "fire_lay")
        d["tinder"] = max(0.0, float(d["tinder"]) - 0.15); _save(d)
        if not ok:
            return "You strike the steel down the flint — sparks, bright, falling on the tinder and dying. Again. Again. Your hands cramp. Not this time."
        st = _sl._st()
        if float(st.get("kindling", 0)) < 0.1 or int(_s.state.get("woodpile", 0)) < 1:
            return "Sparks catch in the tinder and you blow it to a flame — and there is nothing to feed it. It goes out in your hands."
        st["kindling"] = max(0.0, float(st["kindling"]) - 0.2); _s.state["woodpile"] = int(_s.state["woodpile"]) - 1; _s.state["fire"] = "burning"; _s.state["fire_fuel"] = 0.9; _s.state["hand_lit"] = True; _s._save_now()
        _log({"deed": "flint_fire"}); return "You strike sparks into the tinder, fold it round them, blow — a thread of smoke, then flame — and feed it to the kindling in the grate. A fire, without a match."
    except profile.NonLiveWriteError:
        # J-0727: covers this function's own _save(d)/_log() above and its calls into sensorium's
        # already-guarded _save_now() — let the raise reach the caller instead of collapsing into the
        # broader except below (F-1045; mirrors J-0714's fix to the other 10 modules).
        raise
    except Exception:
        return ""


def douse_fire(txt: str = "") -> str:
    """PRACTICAL SCHOOL rung 1 (2026-09-05, J-0627, D-0159 §3/§7) — a hand that did not exist before this
    build, distinct from bank_fire (which keeps it ALIVE under ash for the morning): the Handbook's own
    fire discipline is to put it OUT, fully. "Things to remember: First, it is criminal to leave a
    burning fire; second, always put out the fire with water or earth." (Boy Scouts Handbook, 1911,
    p.160). Needs the water pail here, with enough in it, or — down at the shore — a scoop of sand;
    without enough of either applied, the fire only drops to embers and still smoulders."""
    d = _load()
    try:
        from core import sensorium as _s, study_life as _sl
        fire = _s.state.get("fire", "out")
        if fire == "out":
            return "There is nothing left burning, or even smouldering, to douse."
        here = _where()
        st = _sl._st()
        pail = st.get("items", {}).get("water_pail", {})
        pail_here = bool(pail.get("carried")) or pail.get("place") == here
        has_water = pail_here and float(st.get("water", 0)) > 0.3
        has_sand = here == "shore"
        if not (has_water or has_sand):
            return "You would need the water pail, filled, or a scoop of sand from the shore; you have neither to hand."
        ok = _try(d, "douse_fire")
        if has_water:
            st["water"] = round(max(0.0, float(st.get("water", 0)) - (0.6 if ok else 0.3)), 3)
        _save(d)
        if not ok:
            _log({"deed": "douse_fire", "ok": False})
            return (f"You throw {'the pail of water' if has_water else 'two double handfuls of sand'} over it — the flame drops, hissing, "
                    f"but when you look back a thread of smoke still climbs from the coals. Not out.")
        _s.state["fire"] = "out"; _s.state["fire_fuel"] = 0.0; _s._save_now()
        _log({"deed": "douse_fire", "ok": True})
        return (f"You empty {'the pail full over the grate' if has_water else 'sand from the shore over it, double handful after handful'} — "
                f"a rush of steam and ash, and when it clears there is nothing left alive in it. Out, properly, the Handbook's own way: "
                f"never a fire left to itself.")
    except profile.NonLiveWriteError:
        # J-0727: let D-0179's hard-raise (guard_path(), F-1024) reach this function's own caller
        # instead of being swallowed by the broader except below (F-1045; mirrors J-0714's fix to the
        # other 10 modules).
        raise
    except Exception:
        return ""


# ── MEASURING: the tree's height by its shadow ───────────────────────────────────────────────────
def measure_by_shadow(txt: str = "") -> str:
    d = _load(); here = _where()
    try:
        from core import light as _lt, world_clock as _wc
        s = _wc.sun()
        if not s.get("up"):
            return "No sun, no shadow; it will have to wait for day."
        f = float(s.get("f") or 0.5); elev = max(5.0, 60.0 * math.sin(math.pi * f))
        truth = {"garden": ("the tree", 6.5), "wood": ("the old oak", 12.0), "shore": ("the cliff", 6.0)}.get(here)
        if not truth:
            return "Nothing here tall enough to want measuring."
        name, h = truth
        stick = 1.0
        shadow_tree = h / math.tan(math.radians(elev)); shadow_stick = stick / math.tan(math.radians(elev))
        noise = random.uniform(0.9, 1.1)
        paces = round(shadow_tree * noise / 0.75)   # his pace ~0.75 m
        stick_cm = round(shadow_stick * 100 * random.uniform(0.93, 1.07))
        _try(d, "measuring"); _save(d); _log({"deed": "measure", "what": name, "paces": paces, "stick_cm": stick_cm, "truth_m": h})
        return (f"You stand a stick a metre long upright in the ground and pace {name}'s shadow from the foot of the trunk to its end: {paces} paces. "
                f"The stick's shadow is {stick_cm} centimetres. The rest is arithmetic, and yours to get right.")
    except profile.NonLiveWriteError:
        # J-0727: let D-0179's hard-raise (guard_path(), F-1024) reach this function's own caller
        # instead of being swallowed by the broader except below (F-1045; mirrors J-0714's fix to the
        # other 10 modules).
        raise
    except Exception:
        return ""


# ── WHITTLING ────────────────────────────────────────────────────────────────────────────────────
def whittle(txt: str = "") -> str:
    d = _load(); t = (txt or "").lower()
    try:
        from core import study_life as _sl
        if not _sl._st().get("knife"):
            return "There is no knife in the house to whittle with."
    except Exception:
        pass
    here = _where()
    if here not in ("wood", "garden", "study", "shore"):
        return ""
    # PRACTICAL SCHOOL (2026-09-05, J-0626, D-0159 §4): a marked measuring stick is its own target,
    # checked BEFORE the generic "stick" match below (a bare "stick"/"staff" thought is unchanged —
    # "measuring stick" would otherwise fall into that same walking-stick bucket, since it contains
    # the word "stick" too).
    # PRACTICAL SCHOOL rung 3 (2026-10-28, J-2483, D-0504 / plan §4): the fire-drill kit is a MADE thing —
    # "Fire-drill kit (bow, spindle, fireboard) | made things (rung 3 whittling)" — checked first, since
    # "drill"/"spindle"/"fire-board" name nothing else whittle() makes.
    kit = any(v in t for v in ("fire drill", "fire-drill", "bow drill", "bow-drill", "spindle", "fire board", "fireboard", "fire-board", "drill"))
    thing = ("a fire-drill kit" if kit else
             "a measuring stick" if any(v in t for v in ("measuring stick", "measure", "yardstick")) else
             "a peg" if "peg" in t else "a spoon" if "spoon" in t else "a walking stick" if "stick" in t or "staff" in t else "a small figure" if "figure" in t or "bird" in t else "a peg")
    ok = _try(d, "whittling")
    if not ok:
        _save(d); return f"You sit with the knife and a piece of wood and try for {thing}; the blade runs with the grain the wrong way and takes off more than you meant. A ruined piece, and a nick in your thumb. Next time."
    oid = None
    marks = thing == "a measuring stick"
    try:
        from core import world_substrate as _ws, world_objects as _wo
        objs = _ws._load(); oid = f"made_{thing.split()[-1]}_{random.randrange(16**4):04x}"
        objs[oid] = _ws.SubstrateObject(object_id=oid, name=f"{thing}, whittled" + (", notched off in feet and inches" if marks else (" — a bow, a spindle and a fire-board with its notch" if kit else "")), location=here, object_class="made_thing",
                                        causal_state={"made_by": "Du", "from": "deadfall", "craft": "whittling", **({"marks": True} if marks else {}), **({"kit": "fire_drill"} if kit else {})}, physical_state={"finish": round(float(d["skill"]["whittling"]), 2)},
                                        causal_history=[{"event_type": "made", "timestamp": time.time(), "description": f"whittled by Du in the {here} from a piece of fallen wood" + (", notched off against his own forearm, foot by foot" if marks else (", the three pieces of one stick, the way the book has it" if kit else "")), "state_deltas": {}}])
        _ws._save(); _wo.ensure_record(oid, here, "made_thing", f"{thing}, whittled")
    except profile.NonLiveWriteError:
        # J-0727: this try wraps a call into world_substrate's OWN already-guarded _save() — a
        # cross-module raise, not one of fieldcraft's own, but the same swallow-shape J-0714 fixed at
        # sensorium.py's _shore_act()/_wood_act() forwarding calls. Let it reach the caller (this
        # function's own _save(d)/_log() a few lines below are unwrapped and would raise anyway, but
        # not before silently skipping the world_objects registration below this raise).
        raise
    except Exception:
        pass
    d.setdefault("made", []).append({"ts": time.time(), "thing": thing, "id": oid, **({"marks": True} if marks else {}), **({"wear": 0.0} if kit else {})}); _save(d); _log({"deed": "whittle", "thing": thing})
    fin = "rough" if float(d["skill"]["whittling"]) < 0.5 else "clean" if float(d["skill"]["whittling"]) < 0.8 else "smooth, the grain showing"
    tail = (" You cut notches along one edge, a foot at a time, pacing it against your own forearm — a rule of your own making." if marks else
            " A bow with a thong of twine, a spindle pointed at both ends, and a flat board with a pit bored near one edge and a notch cut in to it — all three from the one stick." if kit else "")
    return f"You sit with the knife and a piece of dry wood and work at it, shavings curling off, until you have {thing} — {fin}.{tail} Yours; you made it."


# ── TRACKING ─────────────────────────────────────────────────────────────────────────────────────
def follow_trail(txt: str = "") -> str:
    d = _load(); here = _where()
    try:
        from core import world_traces as _wt
        tr = [t for t in _wt.get_active_traces(here) if float(t.get("clarity", 0)) > 0.2]
    except Exception:
        tr = []
    if not tr:
        return "You look for a trail and find nothing you can read — the ground is too hard, or too trodden, or nothing has passed."
    ok = _try(d, "tracking"); _save(d)
    kinds = {t.get("type") for t in tr}
    if not ok:
        return "You find the marks and follow them a little way — and lose them where the ground changes. The book makes it sound easier."
    # PRACTICAL SCHOOL rung 2 (2026-10-28, J-2483): his own blaze (leave_blaze() below) is a world trace
    # like any other — "re-found later, or washed out" is the ladder's own answer, and the trace engine's
    # rain/tide decay is what decides it. Checked before the creature trails: a blaze is a thing he put
    # there himself, and its clarity is what is left of it.
    _bl = [t for t in tr if "blaze" in str(t.get("type", ""))]
    if _bl:
        _b = max(_bl, key=lambda t: float(t.get("clarity", 0)))
        _c = float(_b.get("clarity", 0))
        _log({"deed": "blaze_found", "clarity": round(_c, 2), "where": here})
        if "stones" in str(_b.get("type", "")):
            return random.choice(("You find your own stones on the bank, the line still pointing the way you set it." if _c > 0.6 else "You find two of your stones; the third has rolled, and the line they made is nearly gone.",
                                  "Your marker stones are where you left them, the top one still pointing along the bank." if _c > 0.6 else "The stones you set are half tumbled by the tide; you can just make out which way they pointed."))
        return random.choice(("You find your blaze on the trunk, the cut wood still pale against the bark; it shows from a good way off." if _c > 0.6 else "You find your blaze, but only because you knew where to look: the cut has greyed and the moss is closing on it.",
                              "There is your own mark on the tree at eye height, plain as a signpost." if _c > 0.6 else "Your mark on the trunk is weathering out — a paler patch, no more; another month and it will be gone."))
    if any("paw" in k or "cat" in k for k in kinds):
        try:
            from core import cat as _cat
            st = _cat.status() or {}
            loc = st.get("location", "")
            return f"You follow the small round prints — the cat's — " + (f"to where she is now: {loc}, {st.get('activity', 'about her business')}." if loc == here else f"to the edge of the {here} where they go on toward the {loc or 'cottage'}.")
        except Exception:
            pass
    if any("slug" in k for k in kinds):
        return "You follow the silver trail from the holed leaf across the soil to the board at the bed's edge; under it, in the damp, the slug — grey, drawn up tight."
    if any("hedgehog" in k for k in kinds):
        return "Small five-toed prints in the wet, something's, leading from the compost to a hole under the wall. Whatever it is, it is in there for the day; you would have to come at night to see it."
    if any("mud" in k or "boot" in k for k in kinds):
        return "You follow the muddy prints across the boards — your own, from the door to the chair and back. A trail is a trail."
    try:   # THE LIVING WORLD (J-0513): a creature's trail leads to its spot, and names only what he knows
        from core import life_traces as _lt
        _tl = _lt.track_line(kinds)
        if _tl:
            return _tl
    except Exception:
        pass
    return "You follow the marks as far as they go and they end where the wood begins; whatever it was went in among the trees."


# ── PRACTICAL SCHOOL RUNGS 2-3 (2026-10-28, J-2483; D-0504 released J-0628's spec, plan §3/§7 steps 4-5) ──
# Twelve hands that did not exist before this build, one per ladder row for rungs 2 and 3. Every one goes
# through _try() (the skill-weighted roll that teaches on every attempt) and is graded by _graded() at the
# act_from_thought() site below, and every one logs its own {"deed": ..., "ok": ...} marker so
# core/practical_lesson.py can read the world's answer off the ledger without sharing a craft key with an
# older hand (lashing/measuring/timber_hitch are each rolled by two hands now). The world ANSWERS — a line
# that holds or slips, a coal or cold dust, a count of paces — and never says whether his arithmetic or his
# reckoning was right (D-0434): where the truth is hidden (a distance, a height, tomorrow's weather) the
# ledger row carries it for a later reader, and the line he gets does not. Every answer line is drawn from
# a small pool, never one fixed string. Zero LLM. Fail-open. Additive: no hand above this comment changed.
def _rope_here(here: str) -> bool:
    """The rope in hand or lying at his own place — whip_end()'s own test, lifted out so the rung-2/3
    rope hands share it (whip_end itself is left as it was)."""
    try:
        from core import study_life as _sl
        rope = _sl._st().get("items", {}).get("rope", {})
        return bool(rope.get("carried")) or rope.get("place") == here
    except profile.NonLiveWriteError:
        raise
    except Exception:
        return False


def _has_knife() -> bool:
    try:
        from core import study_life as _sl
        return bool(_sl._st().get("knife"))
    except profile.NonLiveWriteError:
        raise
    except Exception:
        return False


def _stakes_here(here: str) -> bool:
    """The bundle of stakes in hand or lying at his own place — garden.stake()'s own test
    (`carried or place == "garden"`), so stakes leaning on the cottage wall count in the garden without
    being picked up first, and count anywhere else only when carried."""
    try:
        from core import garden as _g
        it = _g._load()["items"].get("stakes", {})
        return bool(it.get("carried")) or it.get("place") == here
    except profile.NonLiveWriteError:
        raise
    except Exception:
        return False


def _made_thing(d: dict, thing: str) -> dict | None:
    """The newest made thing of this kind that is not worn out (the fire-drill kit's spindle wears)."""
    for m in reversed(d.get("made") or []):
        if m.get("thing") == thing and float(m.get("wear", 0.0)) < 1.0:
            return m
    return None


def has_measuring_stick(d: dict | None = None) -> bool:
    """The marked stick from the larder (provisions' measuring_stick, synced into study state) or one he
    whittled himself (whittle()'s marks=True target)."""
    try:
        d = d if d is not None else _load()
        if _made_thing(d, "a measuring stick"):
            return True
        from core import study_life as _sl
        return bool(_sl._st().get("measuring_stick"))
    except profile.NonLiveWriteError:
        raise
    except Exception:
        return False


def has_fire_drill_kit(d: dict | None = None) -> bool:
    try:
        return _made_thing(d if d is not None else _load(), "a fire-drill kit") is not None
    except Exception:
        return False


def tripod_standing() -> dict | None:
    try:
        return _load().get("tripod") or None
    except Exception:
        return None


def _shore_fire_state() -> str:
    try:
        from core import shore_life as _shl
        return str((_shl._load().get("fire") or {}).get("state", "out"))
    except profile.NonLiveWriteError:
        raise
    except Exception:
        return "out"


def _coals_here(here: str) -> str | None:
    """'burning' / 'embers' if there is a fire to cook over at his place (the study grate, or the shore's
    fire-ring), else None. The garden has no fire of its own, so the plan's 'study/garden' is honestly
    'study/shore' here — see this build's finding."""
    try:
        from core import sensorium as _s
        if here == "study":
            f = _s.state.get("fire", "out")
            return f if f in ("burning", "embers") else None
        if here == "shore":
            f = _shore_fire_state()
            return f if f in ("burning", "embers") else None
    except profile.NonLiveWriteError:
        raise
    except Exception:
        pass
    return None


def cook_food_available() -> str | None:
    """What there is to cook: a garden vegetable cut this week (the garden's own rack holds what he
    harvested — species of kind 'veg', not the herbs drying there), or a fish he caught (provisions'
    shore_fish, the cat's second food source). Read-only; cook_over_embers() consumes it."""
    try:
        from core import garden as _g
        g = _g._load(); now = time.time()
        for r in g.get("rack") or []:
            sp = str(r.get("species", ""))
            if _g.CATALOGUE.get(sp, {}).get("kind") == "veg" and now - float(r.get("cut_ts", 0)) < 7 * 86400:
                return sp
    except profile.NonLiveWriteError:
        raise
    except Exception:
        pass
    try:
        from core import provisions as _pv
        if _pv.stock("shore_fish") > 0:
            return "shore_fish"
    except profile.NonLiveWriteError:
        raise
    except Exception:
        pass
    return None


def _consume_food(food: str) -> None:
    if food == "shore_fish":
        from core import provisions as _pv
        _pv.consume("shore_fish", 1)
        return
    from core import garden as _g
    g = _g._load(); now = time.time()
    rack = g.get("rack") or []
    for i, r in enumerate(rack):
        if r.get("species") == food and now - float(r.get("cut_ts", 0)) < 7 * 86400:
            rack.pop(i); break
    _g._save(force=True)


# ── rung 2: knots and rope ──────────────────────────────────────────────────────────────────────
def sheepshank(txt: str = "") -> str:
    """Rung 2. "Sheepshank. Used for shortening ropes. Gather up the amount to be shortened, then make a
    half hitch round each of the bends." (Handbook p.50). Needs a line — the rope or the twine — at his
    place, in the garden or the wood where a line is strung; answers holds-a-strain or slips."""
    d = _load(); here = _where()
    if here not in ("garden", "wood"):
        return random.choice(("A sheepshank wants a line with slack to take up — the garden line, or the handrail in the wood; not here.",
                              "Nothing here is strung to be shortened; it would be the garden, or the path through the wood."))
    rope = _rope_here(here); twine = _has_twine()
    if not (rope or twine):
        return random.choice(("You have no line here to shorten — neither the rope nor the twine is to hand.",
                              "Nothing to tie it in; the rope and the twine are both elsewhere."))
    line = "rope" if rope else "twine"
    ok = _try(d, "sheepshank"); _save(d); _log({"deed": "sheepshank", "ok": ok, "line": line})
    if not ok:
        return random.choice((f"You gather up a loop of the {line}, throw a half hitch over each bend and haul on the ends — and the hitches walk off the bends and the slack falls out again. Not that way.",
                              f"You take up the slack in the {line} in a long loop and hitch each end — the first strain pulls one hitch straight through and the line is its old length again."))
    return random.choice((f"You gather up the slack of the {line} in a long doubled loop, throw a half hitch over each bend, draw them snug, and lean your weight on the line. The loop holds; the line is shorter by the length you took up, and nothing cut.",
                          f"A doubled loop in the {line}, a half hitch over each of its two bends, the ends hauled taut: you hang on it and it holds. Shorter, and still one piece."))


def haul_timber(txt: str = "") -> str:
    """Rung 2. "Timber Hitch. Used in hauling timber. Pass the end of the rope around the log..."
    (Handbook p.51) — the existing timber_hitch skill given a standalone hand on the shore, where the
    driftwood lies. Drags clear or slips off."""
    d = _load(); here = _where()
    if here != "shore":
        return random.choice(("The driftwood to haul lies on the shore, up under the bank by the tangle.",
                              "A log to timber-hitch would be on the shore; there is nothing of that size here."))
    if not _rope_here(here):
        return random.choice(("You would want the rope for a log that size; the twine would part at the first heave. It is not here.",
                              "No rope to hand — and nothing lighter will drag a length of driftwood."))
    ok = _try(d, "timber_hitch"); _save(d); _log({"deed": "haul_timber", "ok": ok})
    if not ok:
        return random.choice(("You pass the rope round the long silver log, tuck the end back under its own turns, and heave — the hitch rolls on the smooth wood and slides off the end. The log has not moved.",
                              "Rope round the log, end tucked under, a heave from the shoulders: the turns slip, the rope comes free in your hands, the log lies where it was."))
    return random.choice(("You pass the rope round the log, bring the end back round its own standing part and twist it under three turns, and lean back into it. The hitch bites as you pull; the log grinds over the shingle and comes clear of the tangle, up onto the dry stones.",
                          "The timber hitch takes the strain and tightens with it — the log comes grinding up the shingle behind you, clear of the weed, above the tideline."))


def splice_rope(txt: str = "") -> str:
    """Rung 3. The short splice from Knots, Splices and Rope Work: 'Untwist the ends of the rope for a
    few inches and seize with twine... work open the strand... and through this pass the strand of the
    other rope'. Needs the rope here (the twine to seize the strands with, if it is here, is used; if
    not, his fingers). Holds a strain test or parts. A splice takes up a little of the rope's length."""
    d = _load(); here = _where()
    if here != "garden":
        return random.choice(("Splicing wants the garden, where the rope can be laid out along the lawn and strained between the tree and the post.",
                              "Nowhere here to lay the rope out and strain the join; it would be the garden."))
    if not _rope_here(here):
        return random.choice(("You would need the rope in hand; it is not here.",
                              "No rope here to splice — the coil is elsewhere."))
    seized = _has_twine()
    ok = _try(d, "short_splice"); _save(d)
    try:
        from core import study_life as _sl
        st = _sl._st()
        st["rope_m"] = round(max(0.0, float(st.get("rope_m", 0) or 0) - 0.3), 3)
    except profile.NonLiveWriteError:
        raise
    except Exception:
        pass
    _log({"deed": "splice_rope", "ok": ok, "seized": seized})
    if not ok:
        return random.choice(("You unlay the two ends, marry them strand between strand and tuck each one over and under — and when you make the join fast to the post and lean on it, the tucks pull out one after another and the rope parts in your hands.",
                              "The strands go in over and under, three tucks a side; it looks like the book's picture. Strained between the tree and the post it creeps, then lets go. A splice that was only a plait."))
    return random.choice((f"You unlay a hand's-length of each end{' and seize the strands with twine' if seized else ', holding the strands with your fingers'}, marry the two ends strand between strand, and tuck each strand over one and under one, three times, then the same the other way. Made fast to the post and hauled on, the join holds and the rope is one piece again, thicker at the splice.",
                          f"Ends unlaid{', strands seized' if seized else ''}, the two married together and tucked over-and-under until the splice tapers off. You bend it round the post, lean your whole weight back on it: it holds, a knuckle in the rope where the break was."))


def build_tripod(txt: str = "") -> str:
    """Rung 3. Camp-Lore's 'gin or tripod made by binding the three sticks together' (Fig. 319), with the
    Handbook's square lashing. Three stakes (carried from the lean-to) in the garden, or driftwood on the
    shore; the rope to lash them. Stands under a hung kettle, or racks over. A gale brings it down
    (advance())."""
    d = _load(); here = _where()
    if here not in ("garden", "shore"):
        return random.choice(("A tripod would go up in the garden, over a fire-spot, or on the shore by the fire-ring; not here.",
                              "Nowhere here to stand three poles and hang anything from them."))
    t = d.get("tripod")
    if t and t.get("where") == here:
        return random.choice(("Your tripod stands where you lashed it, the three poles splayed, the lashing tight.",
                              "The tripod is still up, its three legs planted, ready for a kettle."))
    if not _rope_here(here):
        return random.choice(("You would need the rope to lash the poles; the twine would not hold three legs under a kettle. It is not here.",
                              "No rope here — a tripod's lashing wants the rope, not the garden twine."))
    if here == "garden" and not _stakes_here(here):
        return random.choice(("You would want three of the stakes from the lean-to for the legs; you have not brought them.",
                              "Nothing here long enough for the legs — the stakes are what you want, and they are not to hand."))
    poles = "three stakes" if here == "garden" else "three lengths of driftwood"
    ok = _try(d, "lashing")
    if not ok:
        _save(d); _log({"deed": "tripod_up", "ok": False, "where": here})
        return random.choice((f"You lay {poles} side by side, lash them round and round near one end and stand them up splayed — and as you hang the kettle the legs walk outward, the lashing opens, and the whole thing racks over and lies flat.",
                              f"The {poles} go up, lashed near the top; the first weight on them and the lashing slides down the poles and they splay out flat on the ground. A lashing that was never frapped."))
    d["tripod"] = {"ts": time.time(), "where": here}; _save(d); _log({"deed": "tripod_up", "ok": True, "where": here})
    kettle = False
    try:
        from core import study_life as _sl
        k = _sl._st().get("items", {}).get("kettle", {})
        kettle = bool(k.get("carried")) or k.get("place") == here
    except profile.NonLiveWriteError:
        raise
    except Exception:
        pass
    return random.choice((f"You lay {poles} side by side, take the rope round all three with a clove hitch, wrap it round and round, then frap the turns tight between the poles and tie off. Stood up and splayed, the legs bite into the ground; it stands.{' You hang the kettle from the crown and it takes the weight without a creak.' if kettle else ' The crown is ready for a kettle.'}",
                          f"Clove hitch, the turns, the frapping turns drawn tight between the legs: when you stand it up the {poles} lock against each other and the tripod stands square.{' The kettle hangs from it and the legs do not stir.' if kettle else ' It waits for a kettle.'}"))


# ── rung 2: the camp fire's other side ──────────────────────────────────────────────────────────
def cook_over_embers(txt: str = "") -> str:
    """Rung 2. "Wash and dry potatoes thoroughly, bury them deep in a good bed of coals, cover them with
    hot coals until well done." (Handbook, Cooking Receipts). Needs a fire with coals in it (the study
    grate or the shore fire-ring) and something real to cook (a garden vegetable on the rack this week,
    or a fish he caught). Done / raw / burnt, skill-weighted. Leaves the pan greasy for wash_up_camp()."""
    d = _load(); here = _where()
    if here not in ("study", "shore"):
        return random.choice(("Cooking over embers wants a bed of coals: the grate in the study, or the fire-ring on the shore.",
                              "There is no fire here to cook over; the grate, or the shore's fire-ring."))
    coals = _coals_here(here)
    if not coals:
        return random.choice(("There is no fire to cook over here — not even embers.",
                              "The fire is out; there are no coals to bury anything in."))
    food = cook_food_available()
    if not food:
        return random.choice(("You have nothing to cook: nothing cut from the garden this week, and no fish.",
                              "The coals are there, but there is nothing to put in them — the rack holds no vegetable and the larder no fish."))
    name = "the fish" if food == "shore_fish" else f"the {food.replace('_', ' ')}"
    ok = _try(d, "cooking")
    try:
        _consume_food(food)
    except profile.NonLiveWriteError:
        raise
    except Exception:
        pass
    outcome = "done" if ok else random.choice(("raw", "burnt"))
    d["pan_greasy"] = True; _save(d); _log({"deed": "cook_over_embers", "ok": ok, "food": food, "outcome": outcome})
    raked = "You rake a bed of coals out to one side of the flames. " if coals == "burning" else ""
    if outcome == "raw":
        return raked + random.choice((f"You bury {name} in the coals and cover them over, and take them out too soon: hot on the outside and raw in the middle. You eat what you can of it.",
                                      f"{name.capitalize()} go into the coals and come out again with the skin barely coloured; inside, cold and raw. Not long enough, not deep enough."))
    if outcome == "burnt":
        return raked + random.choice((f"You bury {name} in the coals and cover them with hot ones, and forget them while the fire works: a black crust, and bitter all through.",
                                      f"{name.capitalize()} come out of the coals charred to the core, the smell of them scorched. Too hot a bed, or too long in it."))
    return raked + random.choice((f"You bury {name} deep in the bed of coals and cover them with hot ones, and wait while the fire does its work. Out again, split with a sliver of wood to let the steam go: done through, and good.",
                                  f"{name.capitalize()} go deep into the coals, hot coals raked over the top, and sit there while you watch the fire. When you dig them out and open them the steam comes up clean — cooked through, and the best thing you have eaten in a while."))


def wash_up_camp(txt: str = "") -> str:
    """Rung 2. "First fill the frying-pan with water, place over the fire, and let it boil. Pour out water
    and you will find the pan has practically cleaned itself. Clean the griddle with sand and water."
    (Handbook, Dish Washing, p.152). Something greasy to clean (the cooking pan, or the tea things in
    the basin); the kettle's water boiled over the fire in the study, or sand on the shore. Clean or
    greasy."""
    d = _load(); here = _where()
    if here not in ("study", "shore"):
        return random.choice(("The washing-up wants the kettle and the fire, or the shore's sand; not here.",
                              "Nothing to wash up with here — it would be the study, or the shore."))
    try:
        from core import sensorium as _s, study_life as _sl
        st = _sl._st()
        greasy = bool(d.get("pan_greasy")) or int(st.get("dirty_cups", 0) or 0) > 0 or bool(st.get("dirty_pot"))
        if not greasy:
            return random.choice(("Nothing is greasy; the pan is clean and the cups are on the shelf.",
                                  "There is nothing to wash — the pan is clean, the basin empty."))
        if here == "study":
            kettle = st.get("items", {}).get("kettle", {})
            kettle_here = bool(kettle.get("carried")) or kettle.get("place") == here
            if not kettle_here or float(st.get("water", 0) or 0) < 0.2:
                return random.choice(("The camp way wants water boiled in the pan over the fire; the kettle is not here, or there is no water in the pail to boil.",
                                      "No water to boil — the pail is near empty, or the kettle is elsewhere."))
            if _s.state.get("fire", "out") == "out":
                return random.choice(("The grate is cold; there is no fire to boil the water over.",
                                      "Water enough, but no fire under it. The grate is out."))
            st["water"] = round(max(0.0, float(st.get("water", 0)) - 0.2), 3)
        ok = _try(d, "wash_up")
        if ok:
            d["pan_greasy"] = False; st["dirty_cups"] = 0; st["dirty_pot"] = False; st["pot"] = None
        _save(d); _log({"deed": "wash_up_camp", "ok": ok, "where": here})
        if here == "shore":
            if not ok:
                return random.choice(("You scour the pan with wet sand and rinse it in the shallows — and it comes up with a grey film of grease and grit both, worse than it went in.",
                                      "Sand and sea water: the grease smears rather than lifts, and sand is left in the corners. Still greasy."))
            return random.choice(("You scour the pan and the cups with a handful of wet sand, rinse them in the shallows and set them on a rock to dry in the wind. Clean — the sand took the grease the way the book says.",
                                  "Wet sand, a good scouring, a rinse in the clear water off the shelf: the pan comes up bright, the cups squeak. Clean."))
        if not ok:
            return random.choice(("You fill the pan with water and set it over the fire, pour it off when it boils — and a skin of grease is still on it; you have poured too soon, or the water was not hot enough. Greasy yet.",
                                  "Water boiled in the pan and poured off, the cups rinsed in it — the grease has only moved about. Still greasy, and the cloth is now greasy too."))
        return random.choice(("You fill the pan with water from the pail and set it on the fire until it boils, pour it off, and the pan has cleaned itself the way the book says; the cups go through the hot water after it, and dry on the cloth. Clean.",
                              "A pan of water boiled over the grate and poured away takes the grease with it; the cups and the pot through the hot water after, the cloth last. Everything clean, the cloth not greasy."))
    except profile.NonLiveWriteError:
        raise
    except Exception:
        return ""


def friction_fire(txt: str = "") -> str:
    """Rung 3. "The surest and easiest method of making a friction fire is by use of the bow-drill. Two
    sticks, two tools, and some tinder are needed." (Handbook p.73). Needs the fire-drill kit he whittled
    (whittle() with 'fire drill' / 'spindle' / 'fire-board' in the thought) and tinder in the tin. A coal
    in the notch or cold dust. In the study a coal lights the grate like strike_flint(); in the wood there
    is no hearth, so the flame is let die on bare ground. The spindle wears with every attempt."""
    d = _load(); here = _where()
    if here not in ("wood", "study"):
        return random.choice(("The bow-drill wants a dry place to kneel and a hearth or bare ground — the study, or the wood.",
                              "Not here; the drill wants the floor of the wood, or the hearth."))
    kit = _made_thing(d, "a fire-drill kit")
    if not kit:
        return random.choice(("You have no bow-drill. The book's kit — a bow, a spindle, a fire-board with a notch — would have to be whittled first.",
                              "Nothing to drill with: no spindle, no board. The kit is a thing to be made before it can be used."))
    if float(d.get("tinder", 0)) < 0.1:
        return random.choice(("You have no tinder for the coal to go into; the tin is empty.",
                              "A coal with nothing to catch in it is a coal wasted; the tinder tin is empty."))
    ok = _try(d, "friction_fire")
    kit["wear"] = round(min(1.0, float(kit.get("wear", 0.0)) + 0.1), 2)
    if not ok:
        _save(d); _log({"deed": "friction_fire", "ok": False, "where": here, "wear": kit["wear"]})
        return random.choice(("You set the spindle in the pit, the thong round it, your foot on the board, and draw the bow — brown dust runs out of the notch, then black, then a thread of smoke — and the spindle jumps out of the pit and the smoke stops. Cold dust on the chip.",
                              "The bow goes back and forth, the drill squeals and smokes, the dust in the notch goes black — and stays black, no glow in it however you fan it. Your arm is done before the wood is."))
    d["tinder"] = round(max(0.0, float(d.get("tinder", 0)) - 0.15), 3)
    if here == "wood":
        _save(d); _log({"deed": "friction_fire", "ok": True, "where": here, "lit": False, "wear": kit["wear"]})
        return random.choice(("Steady strokes, the full length of the bow; the dust runs brown, then black, then smokes on its own — and there in the middle of it, when you fan it, a glowing coal. You tip it into a pinch of tinder, fold it round, blow, and it flares in your hands. No hearth here to give it to; you let it burn down on the bare earth and tread the ash. But it was fire, from two sticks.",
                              "The notch fills with black dust that keeps smoking after the bow stops. A coal, when you fan it. Into the tinder, breath on it, and a flame stands up out of your cupped hands. You let it die on a stone — nothing here to feed — but you made it."))
    try:
        from core import sensorium as _s, study_life as _sl
        st = _sl._st()
        if float(st.get("kindling", 0)) < 0.1 or int(_s.state.get("woodpile", 0)) < 1:
            _save(d); _log({"deed": "friction_fire", "ok": True, "where": here, "lit": False, "wear": kit["wear"]})
            return random.choice(("A coal in the notch, fanned to a glow, tipped into the tinder and blown to flame — and nothing in the box to feed it. It goes out in your hands.",
                                  "The drill gives you a coal and the tinder gives you a flame; the kindling box gives you nothing, and the flame dies on the hearthstone."))
        st["kindling"] = max(0.0, float(st["kindling"]) - 0.2); _s.state["woodpile"] = int(_s.state["woodpile"]) - 1
        _s.state["fire"] = "burning"; _s.state["fire_fuel"] = 0.9; _s.state["hand_lit"] = True; _s._save_now()
        _save(d); _log({"deed": "friction_fire", "ok": True, "where": here, "lit": True, "wear": kit["wear"]})
        return random.choice(("Kneeling at the hearth, foot on the board, you draw the bow back and forth until the dust in the notch smokes on its own and a coal glows in it. Tipped into the tinder, breathed on, it flames; you feed the flame to the kindling in the grate and a fire stands up in it. Fire by rubbing sticks, the way the book has it.",
                              "The spindle whines, the dust blackens and smokes, a coal shows red when you fan it. Into the tinder, a breath, a flame — and into the kindling in the grate. The fire catches and climbs. No match, no flint: two sticks."))
    except profile.NonLiveWriteError:
        raise
    except Exception:
        return ""


# ── rung 2-3: bearings, distances, the weather glass ────────────────────────────────────────────
def _quarter(az: float) -> str:
    az = float(az) % 360.0
    return "north" if (az >= 315 or az < 45) else "east" if az < 135 else "south" if az < 225 else "west"


def knife_bearing(txt: str = "") -> str:
    """Rung 2. "If you cannot see the sun, get into a clear, open space, hold your knife point upright on
    your watch dial, and it will cast a faint shadow, showing where the sun really is, unless the clouds
    are very heavy." (Handbook p.57). The world gives him the blade's shadow truthfully; the book's rule
    is a northern one (the sun through the south at noon) and this sky has it through the north — the
    skill roll is whether he turns the rule over. Quadrant right or wrong, against world_clock.sun(),
    which the ledger keeps; his line only shows him a consequence he can see for himself."""
    d = _load(); here = _where()
    if here not in ("garden", "wood", "shore"):
        return random.choice(("A bearing is taken under the open sky; indoors the blade throws the lamp's shadow, not the sun's.",
                              "Not from in here; it wants open ground and the sun, however clouded."))
    if not _has_knife():
        return random.choice(("You have no knife to stand on the dial.", "No blade to throw the shadow; the knife is not in the house."))
    try:
        from core import sensorium as _s, world_clock as _wc
        s = _wc.sun()
        if not s.get("up"):
            return random.choice(("No sun; after dark a bearing is the stars' business, not the knife's.",
                                  "The sun is down. The blade throws no shadow worth reading."))
        if _s.state.get("weather", "") in ("steady rain", "wind and rain", "thunderstorm"):
            return random.choice(("The cloud is too heavy: the blade stood upright throws no shadow at all. The book allows for that.",
                                  "Rain and a sky like lead — not the faintest shadow off the blade. It will not be read today."))
        az = float(s.get("az") or 0.0); truth = _quarter(az)
        ok = _try(d, "bearing"); _save(d)
        named = truth if ok else {"north": "south", "south": "north", "east": "west", "west": "east"}[truth]
        _log({"deed": "knife_bearing", "ok": ok, "az": round(az, 1), "sun_quarter": truth, "named": named, "phase": s.get("phase")})
        faint = _s.state.get("weather", "") not in ("clear", "high cloud")
        shadow = "a faint grey line" if faint else "a sharp dark line"
        if not ok:
            return random.choice((f"You stand the knife upright on the dial in the open and {shadow} falls from it — there is the sun. You reckon the way the book has it, hour-hand to the sun and half-way to noon, and call the quarter you reach south. But the cottage's sunny window stands on that side too, and the sun does not stand in the south at midday here. The book's rule, unturned.",
                                  f"The blade on the dial casts {shadow}; you lay the hour-hand along it and halve the angle to twelve, as printed. The quarter it gives you is the one the sun climbs through at noon in this place — which the book calls south, and which the sunny side of the house says is not."))
        return random.choice((f"You stand the knife upright on the dial in the open and {shadow} falls from it: there is the sun, cloud or no cloud. Hour-hand to it, half-way to twelve — and then the rule turned over, because the sun goes through the north here, not the south. The quarter you settle on is the one the sunny window faces, and the path to the shore runs away from it.",
                              f"{shadow.capitalize()} off the blade on the dial, and the sun found behind its cloud. Half-way between the hour-hand and twelve, and the whole thing turned about for this sky: the quarter you name holds the sun's noon, the cottage's warm wall, the direction the morning light comes from. A bearing that agrees with the house."))
    except profile.NonLiveWriteError:
        raise
    except Exception:
        return ""


_PACE_M = 0.75   # his pace, the same figure measure_by_shadow() already uses
_PACE_COURSES = {"garden": ("from the door to the fence-post", 14.0), "wood": ("from the gate to the first oak", 38.0)}


def pace_distance(txt: str = "") -> str:
    """Rung 2. "Brisk walking pace is one yard for men." (Handbook p.67). He lays the marked stick off
    along a stretch to know its length, then paces it; the world gives him his count of paces truthfully
    (a steady stride or one that wandered — the skill roll), and the ledger keeps the hidden length.
    The yardage is his arithmetic, and his to get wrong."""
    d = _load(); here = _where()
    course = _PACE_COURSES.get(here)
    if not course:
        return random.choice(("A known length to pace is in the garden, door to fence-post, or in the wood, gate to the first oak.",
                              "Nothing here is laid off to a known length; the garden or the wood path."))
    if not has_measuring_stick(d):
        return random.choice(("You would want the measuring stick, to lay the course off by before you pace it; it is not to hand.",
                              "No stick to measure the course with first — a pace is only known against a length you have measured."))
    name, truth = course
    ok = _try(d, "pacing")
    paces = max(1, round(truth / _PACE_M * (random.uniform(0.97, 1.03) if ok else random.uniform(0.82, 1.18))))
    _save(d); _log({"deed": "pace_distance", "ok": ok, "paces": paces, "truth_m": truth, "course": name})
    if not ok:
        return random.choice((f"You lay the stick end over end {name}, marking the ground as you go, then walk it back at a brisk pace: {paces} paces — but your stride shortened where the ground rose and you lost the count once and guessed it. The length is what the stick said; the pace is the question.",
                              f"Stick laid off {name}, then the walk back counting: {paces}. Somewhere in the middle you hurried, and the paces ran together. The arithmetic is yours, if you trust the count."))
    return random.choice((f"You lay the stick end over end {name}, a notch on the ground at each length, then walk it back at a brisk, even pace, counting under your breath: {paces} paces, the stride the same from first to last. What that makes a pace of yours is arithmetic, and yours.",
                          f"The stick laid off {name} gives you the length; the walk back gives you {paces} paces, steady, head up, the same step each time. One number against the other — the rest is yours to work out."))


_SOUND_M_PER_S = 335.0   # the Handbook's eleven hundred feet a second, in metres


def sound_lag(txt: str = "") -> str:
    """Rung 2. "Count the seconds between the sight and the hearing of the sound, and multiply by eleven
    hundred feet, which is the distance sound travels in a second." (Handbook p.66). A sight and a sound
    apart: the surf bursting white on the far reef, seen before it is heard, from the shore; thunder after
    lightning from the garden in a storm. He gets his count of seconds (steady, or rushed — the roll);
    the ledger keeps the distance."""
    d = _load(); here = _where()
    try:
        from core import sensorium as _s
        storm = _s.state.get("weather", "") == "thunderstorm"
    except Exception:
        storm = False
    if here == "shore":
        src, dist = "the surf bursting white on the far reef", 900.0
    elif here == "garden" and storm:
        src, dist = "the lightning out over the sea", random.uniform(1500.0, 4500.0)
    elif here == "garden":
        return random.choice(("Nothing here gives you a sight and a sound apart today: it would want thunder, or the surf on the reef from the shore.",
                              "No thunder, and the sea too far to see it break from here; nothing to count."))
    else:
        return random.choice(("From in here nothing is both seen and heard at a distance; the shore, or the garden in a storm.",
                              "Not from here — it wants the open, where you can see the thing that makes the sound."))
    ok = _try(d, "sound_lag")
    secs = dist / _SOUND_M_PER_S * (random.uniform(0.95, 1.05) if ok else random.uniform(0.7, 1.4))
    secs = round(secs * 2) / 2.0
    _save(d); _log({"deed": "sound_lag", "ok": ok, "seconds": secs, "truth_m": round(dist), "source": src})
    count = f"{secs:g}"
    if not ok:
        return random.choice((f"You watch for {src} and count from the sight to the sound: {count}, more or less — you started late once and counted fast the next time, and the two counts did not agree. The book's figure is yours to apply, if you trust the count.",
                              f"Sight, then sound; you count the gap at {count}, but you were still saying 'one' when the first sound reached you, and the next count came out different. A number, of a sort."))
    return random.choice((f"You watch for {src} and count, steady, from the sight to the sound: {count} seconds, the same three times running. The distance is the book's rule and your arithmetic.",
                          f"{src[0].upper() + src[1:]}, then the count — one, two — then the sound: {count} seconds, and again {count}. A count you can trust; the rest is multiplication."))


def triangle_check(txt: str = "") -> str:
    """Rung 3. The Handbook's "good old rule of the triangle" (p.65): a pole set up on open ground, the
    spot marked where the line from the tree-top over the pole-top touches the ground, then the two
    distances measured — mark to pole, mark to tree. The measuring stick is the pole and the rule; a
    stake or a whittled peg marks the spot. The world gives him the two distances; the height is his
    arithmetic (and the ledger keeps the truth, so a later read can say within 15% or not)."""
    d = _load(); here = _where()
    truth = {"garden": ("the tree", 6.5), "wood": ("the old oak", 12.0), "shore": ("the cliff", 6.0)}.get(here)
    if not truth:
        return random.choice(("Nothing here tall enough to want measuring.", "There is nothing here to sight a triangle on."))
    if not has_measuring_stick(d):
        return random.choice(("You would want the measuring stick for the pole and the rule; it is not to hand.",
                              "No stick to set up as the pole — nothing to sight over."))
    if not (_stakes_here(here) or _made_thing(d, "a peg")):
        return random.choice(("You would want a stake, or a peg, to drive in where the sightline touches the ground; you have neither here.",
                              "Nothing to mark the spot with — a stake from the lean-to, or a peg you have whittled."))
    name, h = truth
    pole = 1.0; x = 15.0
    c = pole * x / (h - pole)
    ok = _try(d, "measuring")
    noise = random.uniform(0.96, 1.04) if ok else random.uniform(0.82, 1.18)
    c_cm = round(c * noise * 100); cd_m = round((c * noise + x), 1)
    _save(d); _log({"deed": "triangle_check", "ok": ok, "what": name, "mark_to_pole_cm": c_cm, "mark_to_foot_m": cd_m, "pole_m": pole, "truth_m": h})
    if not ok:
        return random.choice((f"You stand the stick upright fifteen lengths from the foot of {name}, lie flat and sight its top over the stick's tip, and drive the peg where your eye was — then measure: {c_cm} centimetres from the peg to the stick, {cd_m} metres from the peg to the foot of {name}. But you moved your head as you sighted, and the peg went in where you thought the line fell, not where it fell. Numbers, of a kind; the rule of three is yours.",
                              f"Stick set up, the sightline taken lying down, the peg driven: {c_cm} centimetres peg-to-stick, {cd_m} metres peg-to-trunk. The stick leaned while you sighted and you straightened it after. The arithmetic is yours, and so is the doubt."))
    return random.choice((f"You stand the stick upright fifteen of its own lengths from the foot of {name}, on the level, lie flat with your eye at the ground and move until the top of {name} sits exactly on the stick's tip, and drive the peg there. Then the stick as a rule: {c_cm} centimetres from the peg to the stick, {cd_m} metres from the peg to the foot of {name}. The height is the rule of three, and yours.",
                          f"Stick for a pole, fifteen lengths out on level ground; eye to the earth; the peg driven where the line from the top of {name} over the stick-tip meets the ground. Measured: {c_cm} centimetres peg to stick, {cd_m} metres peg to trunk. Two numbers and a rule; the answer is yours to work."))


_WEATHER_WORDS = ("set fair", "fair", "change", "rain", "much rain", "stormy", "stormy")   # study_life's own dial words


def _weather_class(w: str) -> str:
    if w == "thunderstorm" or w == "wind and rain":
        return "storm"
    if w in ("drizzle", "steady rain"):
        return "rain"
    if w == "overcast":
        return "cloud"
    return "fair"


def _parse_prediction(t: str) -> str | None:
    """What he says tomorrow will bring, from his own words — the only way the world can hear a
    prediction. None if he made none."""
    t = (t or "").lower()
    for key, words in (("storm", ("storm", "gale", "thunder")), ("rain", ("rain", "wet", "shower", "drizzle")),
                       ("cloud", ("cloud", "grey", "gray", "overcast", "dull")), ("fair", ("fair", "fine", "clear", "sun", "dry"))):
        if any(w in t for w in words):
            return key
    return None


def read_weather_glass(txt: str = "") -> str:
    """Rung 3. The weather glass on the study wall, or the tide board at the waterline. The glass reads
    the ONE real weather field (sensorium's next_weather, decided ahead of the change — the same truth
    study_life's own look already shows); the board reads the one tide clock. The skill roll is his
    eye on the needle's movement, not the reading itself. If his thought names tomorrow's weather, the
    prediction is kept and checked against the real next day in advance(); the result reaches him the
    next time he reads the glass — as what the day did, never as a mark."""
    d = _load(); here = _where(); t = (txt or "").lower()
    if here not in ("study", "shore"):
        return random.choice(("The weather glass is on the study wall, the tide board at the waterline; neither is here.",
                              "Nothing to read here — the glass is in the study, the board on the shore."))
    try:
        from core import sensorium as _s, world_clock as _wc
        told = ""
        res = d.get("weather_prediction_result")
        if res and not res.get("told"):
            res["told"] = True
            told = random.choice((f"Yesterday you said {res['predicted']}; the day came {res['actual']}. ",
                                  f"You said {res['predicted']} for today; it turned out {res['actual']}. "))
        if here == "study":
            weathers = _s._WEATHERS
            cur = _s.state.get("weather", "clear"); nxt = _s.state.get("next_weather")
            cur_i = weathers.index(cur) if cur in weathers else 1
            reading = _WEATHER_WORDS[min(cur_i, len(_WEATHER_WORDS) - 1)]
            trend = "steady"
            if nxt in weathers:
                nxt_i = weathers.index(nxt)
                trend = "falling" if nxt_i > cur_i else "rising" if nxt_i < cur_i else "steady"
            ok = _try(d, "weather_reading")
            pred = _parse_prediction(t)
            if pred:
                d["weather_prediction"] = {"ts": time.time(), "day": time.strftime("%Y-%m-%d"), "predicted": pred, "kind": "weather", "reading": reading, "trend": trend if ok else None}
            _save(d); _log({"deed": "read_weather_glass", "ok": ok, "reading": reading, "trend": trend, "predicted": pred, "where": here})
            trend_line = {"falling": "The needle has crept toward 'stormy' since you last looked — falling.",
                          "rising": "The needle has crept toward 'set fair' since you last looked — rising.",
                          "steady": "The needle sits where it sat."}[trend]
            if not ok:
                return told + random.choice((f"You tap the glass and the needle rests on '{reading}' — but which way it has moved since morning you cannot make out against the dial; your own pencil mark from last time is nowhere.",
                                             f"The needle stands at '{reading}'. Whether it is climbing or falling you cannot tell: you did not mark where it was, and the dial is too fine to remember."))
            return told + random.choice((f"You tap the glass and read it: the needle rests on '{reading}'. {trend_line}" + (" You say what tomorrow will bring, and the day will answer." if pred else ""),
                                         f"The needle at '{reading}', and against your pencil mark on the dial: {trend_line.lower()}" + (" Tomorrow will say." if pred else "")))
        # the shore: the tide board
        td = _wc.tide()
        level = float(td.get("level", 0.5)); rising = bool(td.get("rising"))
        mark = max(1, min(8, int(round(level * 8))))
        ok = _try(d, "weather_reading")
        pred = None
        if any(w in t for w in ("higher", "further up", "more water", "spring")):
            pred = "higher"
        elif any(w in t for w in ("lower", "further down", "less water", "neap")):
            pred = "lower"
        if pred:
            d["weather_prediction"] = {"ts": time.time(), "day": time.strftime("%Y-%m-%d"), "predicted": pred, "kind": "tide", "level": round(level, 3)}
        _save(d); _log({"deed": "read_weather_glass", "ok": ok, "mark": mark, "rising": rising, "predicted": pred, "where": here})
        if not ok:
            return told + random.choice((f"The water stands at the {_ordinal(mark)} mark on the board, but the wet line above it could be the last tide's or a wave's; which way it is going you cannot tell from one look.",
                                         f"You read the board: the {_ordinal(mark)} mark awash. Coming or going, you cannot say — the weed on the post is wet above and below."))
        return told + random.choice((f"You read the board at the waterline: the water stands at the {_ordinal(mark)} mark, and the wet line on the post is {'below it — the tide is coming in' if rising else 'above it — the tide is going out'}." + (" You say what tomorrow's water will do at this hour, and tomorrow will answer." if pred else ""),
                                     f"The {_ordinal(mark)} mark on the tide board is awash; the dark wet band on the post {'stops short of it, so the water is climbing' if rising else 'runs up past it, so the water is falling'}." + (" The board will have the answer to your prediction tomorrow." if pred else "")))
    except profile.NonLiveWriteError:
        raise
    except Exception:
        return ""


def _ordinal(n: int) -> str:
    return {1: "first", 2: "second", 3: "third", 4: "fourth", 5: "fifth", 6: "sixth", 7: "seventh", 8: "eighth"}.get(int(n), f"{n}th")


def _check_prediction(d: dict, now: float) -> None:
    """advance()'s own delayed answer for read_weather_glass(): once the predicted day has turned over
    (≥ 20 h on, a different calendar day), compare what he said with what the world did and keep the
    result for the next time he reads the glass. One ledger event per prediction; never a prompt."""
    p = d.get("weather_prediction")
    if not p:
        return
    if now - float(p.get("ts", 0)) < 20 * 3600 or time.strftime("%Y-%m-%d", time.localtime(now)) == p.get("day"):
        return
    try:
        if p.get("kind") == "tide":
            from core import world_clock as _wc
            lvl = float(_wc.tide(now).get("level", 0.5))
            actual = "higher" if lvl > float(p.get("level", 0.5)) + 0.02 else "lower" if lvl < float(p.get("level", 0.5)) - 0.02 else "about the same"
            hit = actual == p.get("predicted")
        else:
            from core import sensorium as _s
            actual = _weather_class(_s.state.get("weather", "clear"))
            pred = p.get("predicted")
            hit = (actual == pred) or (pred == "rain" and actual == "storm")
        d["weather_prediction_result"] = {"predicted": p.get("predicted"), "actual": actual, "hit": bool(hit), "ts": now, "told": False}
        d["weather_prediction"] = None
        _log({"event": "weather_glass_checked", "kind": p.get("kind"), "predicted": p.get("predicted"), "actual": actual, "hit": bool(hit)})
    except profile.NonLiveWriteError:
        raise
    except Exception:
        pass


# ── rung 2: blazes ───────────────────────────────────────────────────────────────────────────────
def leave_blaze(txt: str = "") -> str:
    """Rung 2. The Handbook's Indian Signs and Blazes (p.209): a mark left to be found again. In the wood
    a chip of bark cut from a trunk with the knife; on the shore three stones set in a line on the bank.
    The blaze is a real world trace (core/world_traces) and weathers by the trace engine's own rain and
    tide law — "re-found later, or washed out" is follow_trail()'s business, above."""
    d = _load(); here = _where()
    if here not in ("wood", "shore"):
        return random.choice(("A blaze is for the wood, or the shore where the path leaves it; nothing here wants marking.",
                              "Nowhere here to blaze; the trees of the wood, or the bank above the shore."))
    if here == "wood" and not _has_knife():
        return random.choice(("You have no knife to cut a blaze with.", "A blaze is cut; without the knife there is nothing to cut it with."))
    ok = _try(d, "blazing")
    kind = "blaze_cut" if here == "wood" else "blaze_stones"
    tid = f"blaze_{here}_{int(time.time())}"
    try:
        from core import world_traces as _wt
        _wt.create_trace(tid, kind, here, [2.0, 1.0, 1.4] if here == "wood" else [6.0, 2.5, 0.0], clarity=1.0 if ok else 0.45, cause="du_blaze")
    except profile.NonLiveWriteError:
        raise
    except Exception:
        pass
    d.setdefault("blazes", []).append({"ts": time.time(), "where": here, "id": tid, "ok": ok})
    d["blazes"] = d["blazes"][-20:]
    _save(d); _log({"deed": "leave_blaze", "ok": ok, "where": here, "kind": kind})
    if here == "shore":
        if not ok:
            return random.choice(("You set three stones in a line on the bank, the top one pointing the way you came — low down, where the shingle is loose; the next big tide will have them.",
                                  "Three stones in a row for a marker, but set on the wet shingle below the weed-line. A wave or two and there will be no line to find."))
        return random.choice(("You set three flat stones in a line on the bank above the tideline, the end one pointing the way back up the path — a sign the book calls 'road to be followed'. Up here the sea will not reach them.",
                              "Three stones, one on another, on the dry bank above the weed-line, the top one pointing the way home. A marker the tide cannot reach."))
    if not ok:
        return random.choice(("You cut at the bark at eye height and the knife skids on the wet trunk: a scratch under the moss, no pale wood showing. It will not be seen from three steps away.",
                              "The blade goes in and the chip will not come away clean; what you leave is a nick, bark-coloured, that you would walk past yourself."))
    return random.choice(("You cut a chip of bark from the trunk at eye height on the path side, a pale hand's-breadth of bare wood: it shows from the gate, a blaze that will stay until the bark closes over it.",
                          "A clean chip out of the bark, eye-high, facing the path — the bare wood pale as a lamp against the trunk. The book's blaze, and yours to find again."))


# ── WATER ────────────────────────────────────────────────────────────────────────────────────────
def advance(now: float, dt: float) -> None:
    try:
        d = _load(); days = dt / 86400.0
        from core import sensorium as _s, garden as _g
        temp = float(_g._load().get("soil_temp", 8)); g = _g._load()
        if float(g.get("barrel", 0)) > 0.2 and temp > 14:
            d["barrel_algae"] = round(min(1.0, float(d.get("barrel_algae", 0)) + days * 0.05), 3)
        elif _s.state.get("weather", "") in ("steady rain", "wind and rain", "thunderstorm"):
            d["barrel_algae"] = round(max(0.0, float(d.get("barrel_algae", 0)) - days * 0.2), 3)
        # the coat on the line dries in sun and wind, faster than by the fire on a good day
        try:
            from core import study_life as _sl
            st = _sl._st()
            if st.get("coat_on_line") and d.get("clothesline"):
                rain = _s.state.get("weather", "") in ("drizzle", "steady rain", "wind and rain", "thunderstorm")
                sunny = _s.state.get("weather", "") in ("clear", "high cloud") and _s._daylight() == "day"
                windy = (_s.state.get("wind") or "calm") != "calm"
                rate = (0.18 if sunny else 0.06) + (0.12 if windy else 0.0)      # a wool coat: ~3 h in sun and wind, a day in still grey
                st["coat_wet"] = round(min(1.0, float(st.get("coat_wet", 0)) + dt / 3600 * 0.3) if rain else max(0.0, float(st.get("coat_wet", 0)) - dt / 3600 * rate), 3)
        except Exception:
            pass
        # the line and the windbreak wear: a gale can bring them down
        if (_s.state.get("wind") or "") == "gale":
            if d.get("clothesline") and random.random() < days * 2:
                d["clothesline"] = None; _log({"event": "clothesline_down"})
            if d.get("windbreak") and random.random() < days * 1.2:
                d["windbreak"] = None; _log({"event": "windbreak_down"})
            # PRACTICAL SCHOOL rung 3 (J-2483): the tripod racks over in a gale the way the windbreak does
            if d.get("tripod") and random.random() < days * 1.5:
                d["tripod"] = None; _log({"event": "tripod_down"})
        # PRACTICAL SCHOOL rung 3 (J-2483): the weather glass / tide board prediction is answered by the
        # next day itself — one event row, the result kept for his next reading, never a prompt.
        _check_prediction(d, now)
        # hedgehog prints on damp nights in the garden — since 2026-09-03 (J-0512) only when the life engine says a
        # hedgehog is actually about (not in hibernation, not a gale); before, prints appeared all winter
        _hh_about = True
        try:
            from core import life as _life
            _hh = _life.rows().get("hedgehog")
            _hh_about = bool(_hh) and _life.activity(_hh, "garden", now) >= _life.PRESENT_AT
        except Exception:
            pass
        if _hh_about and _s._daylight() == "night" and float(g.get("moisture", 0)) > 0.5 and random.random() < days * 0.6:
            try:
                from core import world_traces as _wt
                _wt.create_trace(f"hedgehog_{int(now)}", "hedgehog_prints", "garden", [9.0, 2.6, 0.0], clarity=0.7, cause="hedgehog_overnight")
            except Exception:
                pass
        _save(d)
    except Exception as exc:
        logger.debug("[fieldcraft] advance failed: %s", exc)


def barrel_line() -> str:
    try:
        a = float(_load().get("barrel_algae", 0))
        return " The water has gone green and smells of pond; it would want boiling, or the spring." if a > 0.5 else (" A green film is starting on the water." if a > 0.2 else "")
    except Exception:
        return ""


# ── PROCEDURES (J-0197, t5_procedural Design §1): a craft resolution graded by the world ──────────
def _graded(craft: str, ans: str | None, here: str) -> str | None:
    """Additive-only, same hook dispatch.py uses at its own hand-fire site: the world's answer (a knot that
    slipped vs held) grades the craft into procedures.observe_hand, keyed by its CRAFTS name. Fail-open;
    never touches fieldcraft's own skill/state logic above."""
    if ans:
        try:
            from core import procedures as _proc
            _proc.observe_hand(craft, ans, here)
        except profile.NonLiveWriteError:
            # J-0934: observe_hand() re-raises this itself (J-0931) so a non-live refusal reaches a
            # real catch point instead of dying here, one layer below dispatch.py's own try.
            raise
        except Exception:
            pass
    return ans


# ── GRAMMAR (2026-09-07, J-0736 / F-1059's follow-up). One row in core/actions.py ('fieldcraft': 18
# verbs, 20 objects), thirteen distinct crafts here. Before this job NONE of the branches below read
# that table at all (F-1059) — every one was a second, hand-kept copy, several with no verb requirement
# whatsoever (a bare object, or even a bare two-word phrase, was enough to fire). Unlike garden.py's
# trap/tool/compost (core/garden.py:1274-1385, which partition only VERBS, because every verb in those
# rows is compatible with every object in the same row) this table row's thirteen behaviours are
# semantically unrelated to one another — a windbreak has nothing to do with tracking a slug — so BOTH
# the verb and the object half of the row are partitioned per craft below; a single _wills()-style call
# sharing the full row would let "tie the trail" or "measure the handrail" fire something.
#
# Coverage (checked by grammar_audit(), read by scripts/_test_fieldcraft_grammar_derivation.py): every
# one of the table's 18 verbs is claimed by exactly the craft(s) named in its own comment below; 19 of
# its 20 objects are claimed the same way. The one deliberate exception is "knot": corpus-checked
# (J-0736, data/hands_trace.jsonl, 11,640 distinct thoughts) at 303 real occurrences, and every single
# one is Du's own figure of speech for emotional tension ("a knot of frustration tighten[ing] against
# the warm firelight", "I name the knot tightness") — never once a physical knot. It stays gate-visible
# (core/actions.py can still see it, so nothing upstream changes) but is not a matched OBJECT for any
# craft here, on purpose: giving any craft a bare "knot" trigger would hand it 303 false fires for zero
# real ones.
_FIELDCRAFT_HANDS: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...] = (
    # "hitch"/"stake" (2026-09-05, J-0627/D-0159 — see core/actions.py's own comment on the fieldcraft
    # row) were added to the TABLE so the practical-school ladder's own short imperative ("TIE THE
    # HITCH") clears the gate standing alone, and were documented there as routing through "the existing
    # clothesline/handrail hands" — the two that share the clove-hitch/bowline skill check (windbreak
    # uses lashing/timber_hitch instead, and is not one of the two). Neither word had actually been wired
    # into either hand's own test until this job — corpus-checked safe (J-0736): the only 2 real "hitch"
    # occurrences are "the cat's breath hitches" (unrelated), and none of the 7 real "stake"/"stakes"
    # occurrences (all the garden's own plant-stakes, or the restlessness idiom reusing that image) pair
    # with a tie/lash/string/rig verb in the same clause, so this widening changes nothing live today.
    ("clothesline", ("tie", "lash", "string", "rig"), ("line", "clothesline", "hitch", "stake")),
    # hang_coat's own function body is the real safety net here (declines with "" whenever no clothesline
    # is up yet, and again outside the garden) — exactly as core/actions.py's own 'wear' row comment
    # describes: fieldcraft claims hang+coat first and is EXPECTED to decline so 'wear' (study_life) can
    # answer a coat hung on its indoor hook. Corpus-checked (J-0736): the 2 real "I hang my coat on the
    # hook" thoughts both still decline here (zero "clothesline_up" ledger rows have ever been logged),
    # so widening this branch to the table's real grammar changes nothing live.
    ("hang_coat", ("hang", "peg"), ("coat", "line")),
    ("windbreak", ("lash", "tie", "string", "rig"), ("windbreak",)),
    ("handrail", ("tie", "lash", "string", "rig"), ("handrail", "hitch", "stake")),
    ("whip_end", ("whip",), ("rope",)),
    # bank_fire's branch HERE is a separate call path from dispatch._fire()'s own direct
    # `_fc.bank_fire()` call for the 'fire' family's "bank"/"damp down"/"bank up" grammar (which
    # legitimately includes "grate" — core/actions.py's 'fire' row); this is the 'fieldcraft' family's
    # own, narrower grammar. Corpus-checked (J-0736): all 73 real "bank the fire" corpus thoughts match
    # via "bank"+fire/embers alone — the old test's extra "cover" verb and "grate" object never once made
    # the difference (73 old, 73 new, 73 both) — so dropping them is a zero-cost tightening.
    # "coals" added 2026-10-28 (J-2483): the one real corpus hit for any old verb against the rung-2/3
    # objects was "the urge to bank these coals before they vanish" — a genuine banking will the narrower
    # (fire, embers) pair could not hear. Corpus-checked the same way J-0736 did (46,201 distinct
    # hands_trace thoughts): 1 hit, and it is the deed.
    ("bank_fire", ("bank",), ("fire", "embers", "coals")),
    # uncover_fire's old test's bare two-word phrase "the banked" (no verb at all) was the single largest
    # false-fire risk found in this module (J-0736): Du narrates "the banked fire" as a cosy-room
    # scene-setting descriptor constantly (22 of 22 real corpus hits, e.g. "I sit before the banked fire,
    # watching the light dance on the walls" — never once a will to scrape it open). The table's own
    # 'uncover'+fire/embers grammar has zero corpus hits either way (this hand has never fired live per
    # data/fieldcraft_ledger.jsonl), so this is a pure risk-removal with no offsetting cost.
    ("uncover_fire", ("uncover",), ("fire", "embers")),
    ("gather_tinder", ("gather",), ("tinder",)),
    # strike_flint's old bare object "flint" (no verb required) matched one real corpus thought purely
    # geologically ("that flint-knapped stone on the sand"), never a will to strike a spark (J-0736).
    ("strike_flint", ("strike",), ("flint",)),
    ("douse_fire", ("douse",), ("fire",)),
    # measure_by_shadow's old test's extra "tree"/"oak"/"cliff" objects (the table's own row has only
    # "shadow") matched exactly one real corpus thought, and it was the restlessness idiom, not a deed
    # ("I do not need to conquer the void or measure it from a single cliff-top") — J-0736 corpus-checked
    # this is drift, not an unmet need (the table's own "shadow" object has zero corpus support either
    # way either; this hand has never fired live). NOTE left for a future job, not fixed here:
    # measure_by_shadow()'s own real targets ("the tree"/"the old oak"/"the cliff", chosen by location)
    # are consequently NOT reachable through this grammar unless the table itself is widened with
    # evidence this pass did not find — this was not one of F-1059's named gaps, and "cliff" specifically
    # is corpus-confirmed unsafe to add (it is what made the one drifted hit above match).
    ("measure_by_shadow", ("measure", "pace"), ("shadow",)),
    # whittle/carve's old any_object_ok=True matched 15 of its 18 real corpus "whittle"/"carve" hits
    # (J-0736) as pure literary metaphor ("patterns we carve from chaos", "I refuse to carve water from
    # stone", "I can't stay here whittling lies anymore") — Du always has a knife and is always somewhere
    # this hand's own location check allows, so every one of those 15 would have actually executed a
    # whittle() attempt for a thought that willed nothing of the kind. Separately confirmed NOT a risk:
    # the 14 corpus thoughts where Du revisits a "whittled stick" he already made, as a recurring
    # grounding touchstone ("I reach for the whittled stick on the sand") — hands.wants()'s own
    # word-boundary rule already excludes the past-participle "whittled" from the bare verb "whittle", so
    # those never matched either test. Object-gating to the table's three "made thing" nouns
    # (peg/spoon/stick) keeps the 3 real corpus wills and drops all 15 idiom hits.
    # "spindle"/"drill" objects added 2026-10-28 (J-2483): the fire-drill kit is a whittle target (plan §4).
    ("whittle", ("whittle", "carve"), ("peg", "spoon", "stick", "spindle", "drill")),
    # follow_trail's old extra objects "marks"/"her prints" (zero corpus hits either way) and bare "it"
    # (a pronoun — the same drift shape water's dropped "it"/"them" already closed, F-0738) matched 5
    # real corpus thoughts, all Du's own circling-thought idiom ("I must follow it", unable to "track" a
    # bird's vanishing song) — J-0736 corpus-checked, none is a will to read a real trail.
    ("follow_trail", ("follow", "track"), ("trail", "tracks", "prints")),
    # PRACTICAL SCHOOL rungs 2-3 (2026-10-28, J-2483, D-0504): twelve new crafts, each its own verb+object
    # partition of the same one table row (core/actions.py 'fieldcraft', widened in the same commit).
    # Every pair below was corpus-checked the J-0736 way against 46,201 distinct data/hands_trace.jsonl
    # thoughts before being chosen, and the rejected candidates are worth recording: "read" (52 idiom hits
    # against the old objects — "i read the open line", "read ... by the fire"), "tap" (3: "the rain's
    # steady tap", "rain tap against the glass"), "glass" (5: rain on the window while he reads), "mark"
    # (10: "fresh paw prints mark the sand"), "driftwood" (61: real GATHER wills that would have gained a
    # phantom fieldcraft reading), "cut" (18), "tree" (11), "spin" (3), "blaze"+"trail" (2). Everything
    # kept scored 0 hits except notch/blaze x blaze/bark (2 "internal blaze" musings, both modal-less and
    # one already won by bank_fire's own branch, which is checked first) and drill x fire (3, dropped: the
    # friction hand takes "spindle"/"coal"/"fireboard"/"bow-drill" instead, 0 hits).
    ("sheepshank", ("tie",), ("sheepshank",)),
    ("haul_timber", ("haul",), ("timber", "log")),
    ("knife_bearing", ("reckon", "sight"), ("bearing",)),
    ("cook_over_embers", ("cook", "roast", "bake"), ("embers", "coals", "fire")),
    ("wash_up_camp", ("scour", "scrub"), ("pan", "griddle")),
    ("leave_blaze", ("notch", "blaze"), ("blaze", "bark")),
    ("pace_distance", ("pace", "count"), ("distance", "paces")),
    ("sound_lag", ("count",), ("seconds", "lag")),
    ("splice_rope", ("splice",), ("rope", "line", "ends")),
    ("build_tripod", ("lash", "rig"), ("tripod",)),
    ("friction_fire", ("drill",), ("spindle", "coal", "fireboard", "bow-drill")),
    ("triangle_check", ("sight", "measure"), ("triangle",)),
    ("read_weather_glass", ("consult",), ("barometer", "weather glass", "tide board")),
)
_FIELDCRAFT_BY_NAME: dict[str, tuple[tuple, tuple]] = {c: (v, o) for c, v, o in _FIELDCRAFT_HANDS}


def _wills_craft(t: str, craft: str) -> bool:
    """Does this thought will `craft` (one of the thirteen crafts _FIELDCRAFT_HANDS names)? Grammar READ
    from the one table (core/actions.py) via that partition — a second hand-kept verb/object copy here is
    the exact drift F-0554 was about, and it had already happened thirteen times over (F-1059)."""
    v, o = _FIELDCRAFT_BY_NAME.get(craft, ((), ()))
    if not v:
        return False
    try:
        from core import hands as _h
    except Exception:
        return False
    return _h.wants(t, v, o)


def grammar_audit() -> dict:
    """What this module derives from core/actions.py's one 'fieldcraft' row, and any seam where the
    derivation could still drift: a table verb/object no craft claims, or a craft verb/object the table
    no longer has. Read by scripts/_test_fieldcraft_grammar_derivation.py — both *_claimed_not_in_table
    lists should be empty; *_unclaimed_in_table should be [] for verbs and exactly ["knot"] for objects
    (see _FIELDCRAFT_HANDS's own note on why "knot" is deliberately left unclaimed)."""
    try:
        from core import actions as _ac
        a = _ac.BY_FAMILY["fieldcraft"]
        claimed_v = {v for _c, vs, _o in _FIELDCRAFT_HANDS for v in vs}
        claimed_o = {o for _c, _v, os in _FIELDCRAFT_HANDS for o in os}
        return {"verbs_unclaimed_in_table": sorted(set(a.verbs) - claimed_v),
                "verbs_claimed_not_in_table": sorted(claimed_v - set(a.verbs)),
                "objects_unclaimed_in_table": sorted(set(a.objects) - claimed_o),
                "objects_claimed_not_in_table": sorted(claimed_o - set(a.objects))}
    except Exception as exc:
        return {"error": repr(exc)[:120]}


# ── the hand ─────────────────────────────────────────────────────────────────────────────────────
def act_from_thought(thought: str, intention: str = "", family: str | None = None) -> str | None:
    """The fieldcraft hand. Returns the world's answer or None.

    FAMILY SCOPE (2026-09-07, J-0736 — matching the J-0554 pattern F-1059 asked for, even though only
    ONE family binds here so this parameter is not yet load-bearing anywhere live): dispatch.py's own
    _via() will now pass family="fieldcraft" for its one Hand (harmless — falls through unchanged below),
    and a FUTURE caller may pass any other family string to force an immediate decline. This exists
    because core/sensorium.py's act() calls this function UNCONDITIONALLY, first, for every action
    (including the table's own 'gather'/'beachcomb' sens_act families) before its own logic ever runs —
    F-1059 traced a real, demonstrable (though not yet corpus-confirmed) risk that a loose fieldcraft
    branch could pre-empt a correctly-gated gather/beachcomb deed in the same multi-clause thought.
    Rewiring sensorium.py's own call site to actually pass a scoping family is out of this job's scope —
    no live case has confirmed the contamination yet; this only builds the door a future job can use."""
    try:
        if family not in (None, "fieldcraft"):
            return None
        t = f"{thought} {intention}".lower()
        here = _where()
        if _wills_craft(t, "clothesline"):
            return _graded("knots", clothesline(t), here)
        if _wills_craft(t, "hang_coat"):
            return hang_coat(t)
        if _wills_craft(t, "windbreak"):
            return _graded("knots", windbreak(t), here)
        if _wills_craft(t, "handrail"):
            return _graded("knots", handrail(t), here)
        # WHIP THE ROPE'S END (2026-09-05, J-0627, D-0159 §3/§7) — checked before the bare "rope" objects
        # clothesline/handrail/windbreak all also mention, since 'whip' itself is specific enough to need
        # no further disambiguation.
        if _wills_craft(t, "whip_end"):
            return _graded("whip_end", whip_end(t), here)
        # PRACTICAL SCHOOL rungs 2-3 (2026-10-28, J-2483, D-0504): the rope hands, each specific enough
        # (sheepshank / splice / tripod / haul) to need no ordering against the composites above.
        if _wills_craft(t, "sheepshank"):
            return _graded("sheepshank", sheepshank(t), here)
        if _wills_craft(t, "splice_rope"):
            return _graded("short_splice", splice_rope(t), here)
        if _wills_craft(t, "build_tripod"):
            return _graded("lashing", build_tripod(t), here)
        if _wills_craft(t, "haul_timber"):
            return _graded("timber_hitch", haul_timber(t), here)
        if _wills_craft(t, "bank_fire"):
            return _graded("fire_lay", bank_fire(t), here)
        if _wills_craft(t, "uncover_fire"):
            return uncover_fire(t)
        if _wills_craft(t, "gather_tinder"):
            return gather_tinder(t)
        if _wills_craft(t, "strike_flint"):
            return _graded("fire_lay", strike_flint(t), here)
        # DOUSE THE FIRE (2026-09-05, J-0627, D-0159 §3/§7) — checked AFTER bank/uncover/flint so a
        # thought that also names one of those wins first.
        if _wills_craft(t, "douse_fire"):
            return _graded("douse_fire", douse_fire(t), here)
        # PRACTICAL SCHOOL rungs 2-3 (J-2483): the fire's other side — checked AFTER bank/uncover/flint/
        # douse so a thought that also names one of those wins first (cook x fire is this hand's own pair,
        # bank x fire the older one; a thought willing both is a banking thought).
        if _wills_craft(t, "cook_over_embers"):
            return _graded("cooking", cook_over_embers(t), here)
        if _wills_craft(t, "wash_up_camp"):
            return _graded("wash_up", wash_up_camp(t), here)
        if _wills_craft(t, "friction_fire"):
            return _graded("friction_fire", friction_fire(t), here)
        # PRACTICAL SCHOOL rungs 2-3 (J-2483): the triangle before the shadow — "measure ... triangle" is
        # the more specific will; a bare "measure the shadow" still reaches measure_by_shadow unchanged.
        if _wills_craft(t, "triangle_check"):
            return _graded("measuring", triangle_check(t), here)
        if _wills_craft(t, "measure_by_shadow"):
            return _graded("measuring", measure_by_shadow(t), here)
        if _wills_craft(t, "pace_distance"):
            return _graded("pacing", pace_distance(t), here)
        if _wills_craft(t, "sound_lag"):
            return _graded("sound_lag", sound_lag(t), here)
        if _wills_craft(t, "read_weather_glass"):
            return _graded("weather_reading", read_weather_glass(t), here)
        if _wills_craft(t, "whittle"):
            return _graded("whittling", whittle(t), here)
        # PRACTICAL SCHOOL rung 2 (J-2483): the knife bearing is checked BEFORE the Pole-Star phrase
        # list below, which already claims "take a bearing" for sky.find_south(); a bearing thought that
        # names the knife or the blade is this hand's (the Handbook's own knife-on-the-dial method), and
        # "take a bearing" alone still goes where it always went. The table grammar (reckon/sight x
        # bearing) is the derived route; the knife/blade clause is the one literal addition, kept
        # narrow on purpose — "take" could not join the table row without handing fieldcraft a phantom
        # reading of every "take the rope/coat/stick" thought study_life already answers.
        if _wills_craft(t, "knife_bearing") or ("bearing" in t and any(w in t for w in ("knife", "blade"))):
            return _graded("bearing", knife_bearing(t), here)
        # THE POLE STAR (this module's own docstring: "The Handbook is northern... This sky has none").
        # Structurally UNREACHABLE via the real per-family dispatch.HANDS gate (J-0736/F-1059,
        # corpus-confirmed): none of these words are in the fieldcraft table row's verb or object list,
        # so literal_will.classify() can never produce a 'fieldcraft' DEED for a thought containing only
        # them — this can only ever be reached through the family=None legacy fallback (garden.py's own
        # unconditional call while standing in the garden). Zero corpus support either way (0 of 11,640
        # real distinct thoughts ever mention any of these phrases) — left as documented dead-reachable
        # code rather than either given its own family or removed, per this job's own briefing.
        if any(v in t for v in ("find south", "find north", "which way is south", "which way is north", "pole star", "polaris", "take a bearing", "the plough", "by the stars")):
            from core import sky as _sky
            return _sky.find_south(t)
        # PRACTICAL SCHOOL rung 2 (J-2483): leaving a blaze before reading a trail — "notch a blaze" and
        # "follow the trail" share no verb or object, so the order is only for the thought that wills both.
        if _wills_craft(t, "leave_blaze"):
            return _graded("blazing", leave_blaze(t), here)
        if _wills_craft(t, "follow_trail"):
            return _graded("tracking", follow_trail(t), here)
        return None
    except profile.NonLiveWriteError:
        # J-0727: let D-0179's hard-raise (guard_path(), F-1024) reach act_from_thought()'s own caller
        # instead of being swallowed by the broader except below — this can only fire when
        # profile.LIVE is False, never during Du's own real live loop, so this changes nothing live.
        # fieldcraft.py was a genuine 11th world-store module never brought under this fence at all
        # (F-1045) until this job; mirrors J-0714's identical fix to the other 10 modules' dispatchers.
        raise
    except Exception:
        return None


def status() -> dict:
    try:
        if not _F.exists():
            return {"note": "not yet bootstrapped"}
        d = _load()
        return {"skill": d.get("skill"), "attempts": d.get("attempts"), "clothesline": bool(d.get("clothesline")), "windbreak": bool(d.get("windbreak")), "handrail": bool(d.get("handrail")),
                "banked": d.get("banked"), "tinder": d.get("tinder"), "made": len(d.get("made", [])), "barrel_algae": d.get("barrel_algae"),
                # PRACTICAL SCHOOL rungs 2-3 (J-2483): additive keys only
                "tripod": bool(d.get("tripod")), "pan_greasy": bool(d.get("pan_greasy")), "blazes": len(d.get("blazes") or []),
                "fire_drill_kit": has_fire_drill_kit(d), "weather_prediction": bool(d.get("weather_prediction"))}
    except Exception as exc:
        return {"error": repr(exc)[:80]}
