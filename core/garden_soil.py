"""
Nascence — SOIL LIFE (Living Garden B2, J-0505, 2026-09-03): earthworms, the compost heap as a living thing, and soil
health feeding growth.

WHAT WAS TRUE: worms were one random line in garden.dig() and three content-pool lines; the compost heap was a static
item; soil was moisture + potash only. Nothing under the bed had a life.

WHAT THIS ADDS (all world-side state on the sensorium tick, nothing told — he finds it by digging, by looking at the
heap, by what grows):
  EARTHWORMS  a POPULATION row in the life engine (core/life): active at night and after rain when the soil is wet and
              mild (a `scale` read from the bed's moisture and soil temperature), dense in the compost and under the
              sacking, up on the lawn on wet mornings leaving CASTS (a trace the engine drops for the tracking hand and
              the ambient read path), turned up by dig() — the dig line is truth-gated now; a dry hard bed has none.
  SLATERS     woodlice, hidden truth, in the heap and under the sacking at night.
  SOIL HEALTH per bed slot, 0..1 (starts 0.5): fed slowly by worm activity and by spread compost; drained by cropping
              (a harvest) and by a bare wet winter (an empty slot in the cold, wet months). garden._advance_plant reads it
              into the growth gain the way it already reads potash.
  THE HEAP    warmth, worms, slaters, finished compost. Material comes in from mowing (clippings), weeding (pulled
              weeds), and the kitchen (a slow trickle); it rots down at a rate set by warmth (mass × moisture × season);
              TURNING it (a hand) doubles the rate for a week and lets the heat out; FINISHED compost accumulates and is
              spread on the bed by another hand (raises the target slot's soil health — a deed with a consequence he can
              see in the plants weeks later). The blackbird turns the heap edge for worms (row interaction).
Zero LLM; fail-open; additive; the rows are registered by core/life._ensure_builtin and advanced from life.advance.
"""
from __future__ import annotations

import logging
import random
import time

from core import profile   # J-0796: guard_path()'s NonLiveWriteError, forwarded from garden._save()/
                            # _log() -- this module's own hands call those directly and had no carve-out.
from core.life import row

logger = logging.getLogger("nascence.garden_soil")

SOIL_HEALTH_START = 0.5
WORM_GAIN_PER_DAY = 0.004            # at full worm activity
CROP_DRAIN = 0.03                    # per harvest of a slot
BARE_WINTER_DRAIN_PER_DAY = 0.004    # an empty, wet, cold slot
COMPOST_LIFT = 0.18                  # one spread on one slot
ROT_PER_DAY = 0.012                  # base rate of raw -> finished at warmth 1.0
TURN_BOOST_S = 7 * 86400.0
KITCHEN_PER_DAY = 0.004              # peelings and tea leaves
_STAGES_LIVE = ("shoot", "leaf", "established", "flowering", "seeding")


# ── state in garden's own store (additive keys) ─────────────────────────────────────────────────

def _soil(st: dict) -> dict:
    s = st.setdefault("soil", {"health": {}, "compost": {"raw": 0.35, "finished": 0.1, "warmth": 0.2, "worms": 0.3, "turned_ts": 0.0, "spread_n": 0},
                               "_last": 0.0, "casts_ts": 0.0})
    s.setdefault("health", {}); s.setdefault("compost", {}); s.setdefault("_last", 0.0); s.setdefault("casts_ts", 0.0)
    c = s["compost"]
    for k, v in (("raw", 0.35), ("finished", 0.1), ("warmth", 0.2), ("worms", 0.3), ("turned_ts", 0.0), ("spread_n", 0)):
        c.setdefault(k, v)
    return s


def soil_health(st: dict, slot) -> float:
    if slot is None:
        return SOIL_HEALTH_START
    return float(_soil(st)["health"].get(str(slot), SOIL_HEALTH_START))


def _set_health(st: dict, slot, v: float) -> None:
    _soil(st)["health"][str(slot)] = round(max(0.0, min(1.0, v)), 4)


def _worm_scale(now: float, place: str = "garden") -> float:
    """Worms come up when the soil is wet and mild; a dry hard bed or a frozen one has none at the surface."""
    try:
        from core import garden as _g
        st = _g._load()
        m = float(st.get("moisture", 0.7)); t = float(st.get("soil_temp", 10.0))
        wet = 1.0 if m > 0.65 else 0.55 if m > 0.45 else 0.12 if m > 0.3 else 0.0
        warm = 1.0 if 8.0 <= t <= 20.0 else 0.5 if 4.0 <= t <= 24.0 else 0.05
        if place == "compost":
            return max(0.4, wet * warm)
        return wet * warm
    except Exception:
        return 0.5


def _heap_scale(now: float, place: str = "garden") -> float:
    try:
        from core import garden as _g
        c = _soil(_g._load())["compost"]
        return max(0.3, 0.5 + float(c.get("worms", 0.3)))
    except Exception:
        return 0.6


def rows() -> list[dict]:
    return [
        row("earthworms", name="the worms", aliases=("worm", "worms", "earthworm", "earthworms"),
            places={"garden": ["bed", "lawn", "compost", "under_sacking"]},
            active_hours={"dawn": 0.9, "day": 0.15, "dusk": 0.7, "night": 1.0}, season_curve=[0.7, 0.7, 0.9, 1.0, 1.0, 0.8, 0.7, 0.9, 1.0, 1.0, 0.9, 0.7],
            weather_gate={"rain": 1.4, "wind": 1.0, "storm": 1.0, "frost": 0.1},
            light="avoids", count=("one or two", "a few", "the turned earth full of them"), lifespan_y=2, ease=0.5, scale=_worm_scale,
            diet=("leaf litter", "rotting things"), eaten_by=("blackbird", "thrush", "hedgehog", "kiwi"), traces=("worm casts in small coils across the low corner of the lawn",),
            responds_to_du={"dig": 0.6, "water": 0.4},
            hidden={"feature": {"night": "on the wet lawn in the dark, worms lie half out of their holes, stretched pale across the grass, and whip back in at your step",
                                "dawn": "worm casts stand in small coils across the low corner of the lawn, fresh, the soil still glistening",
                                "day": "under the lifted sacking the soil is knotted with worms, fat and red, that draw back into the dark as the light reaches them",
                                "dusk": "a worm lies stranded on the wet path, pale, and you tip it back into the dark of the bed"},
                    "miss": "The soil is wet and there are cast-coils on the lawn, but nothing lies out just now.",
                    "absent": {"weather": "The ground is frozen; nothing comes up through it.", "chance": "The soil is dry and hard; nothing comes to the surface of ground like this — they are down deep, waiting for rain."}},
            note="grandfathered ('worms' in world_content_garden); the bed's own life; casts are its trace (J-0513 traces_pass)"),
        row("slaters", aliases=("slater", "slaters", "woodlouse", "woodlice", "grey bug"),
            places={"garden": ["compost", "under_sacking", "under_the_board"]},
            active_hours={"dawn": 0.3, "day": 0.1, "dusk": 0.6, "night": 1.0}, season_curve=[1.0] * 12,
            weather_gate={"rain": 1.1, "wind": 1.0, "storm": 0.8, "frost": 0.4},
            light="avoids", count=("a few", "dozens", "the underside of the board grey with them"), lifespan_y=2, ease=0.7, scale=_heap_scale,
            diet=("rotting leaves",), eaten_by=("hedgehog", "thrush"), traces=(),
            hidden={"species": "slater", "book_names": ("slater", "woodlouse", "woodlice", "pill bug", "sow bug"), "book_words": ("rotting", "damp", "armour", "curl", "crustacean"),
                    "feature": {"night": "lifting the board, the underside is grey and moving — dozens of small armoured things, jointed like tiny grey shells, that run for the dark",
                                "day": "under the compost board the damp wood is crusted with small grey armoured things that curl into balls when you touch them"},
                    "reveal": "— slaters; woodlice, the little land-crustaceans that live on the rot.",
                    "miss": "The board's underside is damp and bare; whatever was on it has gone into the heap.",
                    "absent": {"chance": "Nothing under the board just now."}},
            note="HIDDEN TRUTH; the heap's own"),
    ]


# ── the tick ────────────────────────────────────────────────────────────────────────────────────

def advance(now: float, dt: float) -> None:
    """From life.advance: the heap rots down (faster warm and wet, twice as fast for a week after a turn), worms work
    the bed's soil health up, bare wet winter slots drain, the kitchen adds a trickle. Logged to garden_events once a
    day. Nothing rendered."""
    try:
        from core import garden as _g, life as _life
        st = _g._load()
        s = _soil(st)
        days = max(0.0, min(dt, 3600.0)) / 86400.0
        if days <= 0:
            return
        c = s["compost"]
        m = float(st.get("moisture", 0.7)); t = float(st.get("soil_temp", 10.0))
        # the heap: warmth from mass × wet × season; a turn lets it breathe (faster) for a week
        turned = now - float(c.get("turned_ts", 0.0)) < TURN_BOOST_S
        warmth = min(1.0, float(c["raw"]) * (0.5 + 0.5 * min(1.0, m / 0.7)) * (0.6 + 0.4 * max(0.0, min(1.0, (t - 5.0) / 15.0))) * (1.6 if turned else 1.0))
        c["warmth"] = round(warmth, 3)
        rot = min(float(c["raw"]), ROT_PER_DAY * (0.3 + warmth) * days * (2.0 if turned else 1.0))
        c["raw"] = round(float(c["raw"]) - rot + KITCHEN_PER_DAY * days, 4)
        c["finished"] = round(min(1.5, float(c["finished"]) + rot * 0.6), 4)
        c["worms"] = round(max(0.05, min(1.0, float(c["worms"]) + days * (0.05 if (m > 0.5 and 6.0 < t < 22.0) else -0.03))), 3)
        # the bed's soil health: worms feed it, cropping and bare wet winters drain it
        worms = _life.rows().get("earthworms")
        w_act = _life.activity(worms, "garden", now) if worms else 0.0
        month = time.localtime(now).tm_mon
        occupied = {str(p.get("slot")) for p in (st.get("plants") or {}).values() if p.get("slot") is not None and p.get("stage") in _STAGES_LIVE}
        for slot in range(12):
            key = str(slot)
            h = soil_health(st, slot)
            h += WORM_GAIN_PER_DAY * w_act * days
            if key not in occupied and month in (5, 6, 7, 8) and m > 0.7:
                h -= BARE_WINTER_DRAIN_PER_DAY * days
            _set_health(st, slot, h)
        if now - float(s.get("_last", 0.0)) > 86400:
            s["_last"] = now
            _g._log(_g._EVENTS, {"event": "soil_day", "compost": {k: c[k] for k in ("raw", "finished", "warmth", "worms")},
                                 "health_mean": round(sum(soil_health(st, i) for i in range(12)) / 12.0, 3), "worm_activity": round(w_act, 3)})
        _g._save()
    except Exception as exc:
        logger.debug("[garden_soil] advance failed (non-fatal): %s", exc)


# ── what feeds the heap, what drains the bed ────────────────────────────────────────────────────

def add_material(kind: str, amount: float = 0.1) -> None:
    """Clippings from mowing, pulled weeds, a dead plant (J-0507), kitchen scraps: raw mass onto the heap."""
    try:
        from core import garden as _g
        st = _g._load(); c = _soil(st)["compost"]
        c["raw"] = round(min(2.0, float(c["raw"]) + amount), 4)
        _g._log(_g._EVENTS, {"event": "compost_material", "kind": kind, "amount": amount})
        _g._save()
    except profile.NonLiveWriteError:
        # J-0796: garden._log()/_save() have always resolved guard_path() themselves (J-0610) -- this
        # module never carved out its own forwarding calls to them until this job. add_material()'s
        # own external callers (garden.py's weed()/_perish(), garden_life.py's mow()) have their own
        # separate un-carved-out local wraps one layer further out -- _perish()'s is provably inert
        # (periodic, garden.advance()'s own excluded chain); weed()'s and mow()'s are genuinely live
        # and spawned rather than fixed here (out of this job's own three-file scope), see F-1175.
        raise
    except Exception:
        pass


def crop_drain(st: dict, slot) -> None:
    """A harvest takes something out of the slot's soil."""
    try:
        if slot is not None:
            _set_health(st, slot, soil_health(st, slot) - CROP_DRAIN)
    except Exception:
        pass


def growth_factor(st: dict, slot) -> float:
    """For garden._advance_plant: 0.7 (exhausted) .. 1.3 (rich), the way potash already scales the gain."""
    return 0.7 + 0.6 * soil_health(st, slot)


# ── the hands ───────────────────────────────────────────────────────────────────────────────────

def turn_compost(txt: str = "") -> str:
    try:
        from core import garden as _g, life as _life
        st = _g._load(); c = _soil(st)["compost"]
        if _g._where() != "garden":
            return ""
        fork = st["items"].get("hand_fork") or {}
        if not (fork.get("carried") or fork.get("place") == "garden"):
            return "You have nothing to turn it with; the hand fork is not out here."
        c["turned_ts"] = time.time()
        _g._save(force=True); _g._log(_g._LEDGER, {"deed": "turn_compost", "raw": c["raw"], "warmth": c["warmth"]})
        try:
            _life.note_deed("dig", "garden")           # a turned heap draws the blackbird like turned earth
        except Exception:
            pass
        heat = ("steam lifts off the middle of it into the cold air" if c["warmth"] > 0.5 else "the middle is warm to the hand" if c["warmth"] > 0.25 else "it is cold right through; not much is happening in it")
        worms = (" The fork comes up knotted with worms, fat and red." if c["worms"] > 0.5 else " A few worms in it, thin." if c["worms"] > 0.2 else " No worms to speak of; it is too dry, or too raw.")
        fin = (" Underneath, at the bottom, it has gone dark and crumbly and smells of nothing but earth — finished." if c["finished"] > 0.3 else "")
        return f"You lift the board and fork the heap over, outside to the middle: {heat}.{worms}{fin}"
    except profile.NonLiveWriteError:
        # J-0796: this function's own _g._save()/_g._log() calls above resolve guard_path() directly
        # (garden.py, J-0610) -- turn_compost() is a real hand, dispatched from garden.act_from_thought()
        # (already safe, J-0714) with no local wrap of its own at that call site, so this re-raise
        # reaches it cleanly.
        raise
    except Exception as exc:
        logger.debug("[garden_soil] turn_compost failed: %s", exc)
        return ""


def spread_compost(txt: str = "") -> str:
    """Barrow the finished compost to the bed: one spread lifts one slot's soil health (the plant there grows better
    for weeks — a consequence he can see, never told)."""
    try:
        from core import garden as _g
        st = _g._load(); c = _soil(st)["compost"]
        if _g._where() != "garden":
            return ""
        if float(c["finished"]) < 0.25:
            return "You dig into the bottom of the heap for the finished stuff and find only a few handfuls, dark and good, not enough to spread. It wants longer."
        t = (txt or "").lower()
        plants = [p for p in (st.get("plants") or {}).values() if p.get("slot") is not None and p.get("stage") in _STAGES_LIVE]
        target = None
        for p in plants:
            sp = p["species"].replace("_", " ")
            if sp in t or sp.rstrip("s") in t:
                target = p; break
        if target is None and plants:
            target = min(plants, key=lambda p: soil_health(st, p.get("slot")))     # the poorest slot, if he did not name one
        slot = target.get("slot") if target else 0
        before = soil_health(st, slot)
        _set_health(st, slot, before + COMPOST_LIFT)
        c["finished"] = round(float(c["finished"]) - 0.25, 4); c["spread_n"] = int(c.get("spread_n", 0)) + 1
        _g._save(force=True); _g._log(_g._LEDGER, {"deed": "spread_compost", "slot": slot, "before": round(before, 3), "after": soil_health(st, slot)})
        what = _g._wname(target) if target else "the bare slot at the bed's end"
        return (f"You barrow the finished compost from the bottom of the heap to the bed and fork it in round {what} — dark, crumbly, "
                f"smelling of earth and nothing else. The soil there goes darker and looser under it. You will know in a few weeks whether it mattered.")
    except profile.NonLiveWriteError:
        # J-0796: two independent raise points in this try -- this function's own _g._save()/_g._log()
        # calls above (garden.py, J-0610) AND _g._wname() (garden.py, fixed J-0783) -- either way,
        # spread_compost() is a real hand dispatched from garden.act_from_thought() (already safe,
        # J-0714) with no local wrap of its own at that call site, so this re-raise reaches it cleanly.
        raise
    except Exception as exc:
        logger.debug("[garden_soil] spread_compost failed: %s", exc)
        return ""


# ── truth-gated lines for the old hands and looks ───────────────────────────────────────────────

def dig_worms_line(now: float | None = None) -> str:
    """For garden.dig(): worms in the turned earth only when the population is up; a dry bed has none."""
    try:
        from core import life as _life
        r = _life.rows().get("earthworms")
        act = _life.activity(r, "garden", now) if r else 0.0
        if act >= 0.6:
            return " The turned earth is full of worms, fat and red, curling away from the light; you tip the spadeful back and they go down into the dark."
        if act >= _life.PRESENT_AT:
            return " A worm curls away from the light and you tip it back into the dark."
        return " Nothing moves in the turned earth; it is too dry for worms to be near the top — they are down deep."
    except Exception:
        return ""


def compost_line() -> str:
    """For garden.look('compost'): the heap as it is — warmth, worms, what has finished."""
    try:
        from core import garden as _g
        st = _g._load(); c = _soil(st)["compost"]
        raw, fin, warm, worms = float(c["raw"]), float(c["finished"]), float(c["warmth"]), float(c["worms"])
        size = ("heaped high under the board" if raw > 1.0 else "a fair heap" if raw > 0.4 else "sunk low, the board nearly on the ground")
        heat = ("steam lifting off the middle" if warm > 0.5 else "warm in the middle to a pushed-in hand" if warm > 0.25 else "cold through")
        life_ = (" Worms show at every lifted edge, and slaters run for the dark." if worms > 0.5 else " A worm or two at the edge." if worms > 0.2 else " Nothing much lives in it yet.")
        fin_l = (f" At the bottom the finished stuff has built up, dark and crumbly, {'plenty to barrow' if fin > 0.5 else 'a barrow-load or so' if fin > 0.25 else 'a few handfuls'}." if fin > 0.1 else "")
        turned = " It was turned lately; the outside is on the inside." if time.time() - float(c.get("turned_ts", 0)) < TURN_BOOST_S else ""
        return f"You look at the compost heap in the corner by the wall: {size}, {heat}.{life_}{fin_l}{turned}"
    except Exception:
        return ""


def status() -> dict:
    try:
        from core import garden as _g
        st = _g._load(); s = _soil(st); c = s["compost"]
        return {"health_mean": round(sum(soil_health(st, i) for i in range(12)) / 12.0, 3),
                "health": {k: v for k, v in s["health"].items()},
                "compost": {k: c[k] for k in ("raw", "finished", "warmth", "worms", "spread_n")}}
    except Exception as exc:
        return {"error": str(exc)[:80]}
