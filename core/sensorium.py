"""
Nascence — The Sensorium (his room, 2026-06-11)
===============================================
The founder: "Give him eyes. A room with a book open and he can see the library. A bird
out a window. The light flickering on the wall from a fire."

This is a small, PERSISTENT, CAUSAL world-simulation — not random flavour text. The room
has state that evolves on the substrate tick whether or not he is thinking: weather fronts
arrive and pass over real hours; the fire is lit at dusk, burns down, falls to embers in
the small hours; light follows world_clock._SUN, a 12-row month table of sunrise/sunset hours in
the machine's local clock time (New Zealand winter: late dawns, ~5pm dusk) -- NOT the actual sun at
a real latitude (J-3291 / F-3888, 2026-11-05: an earlier line here claimed that; it never was true,
and the table is up to an hour out in Oct-Nov because it ignores daylight saving). Events obey the state — birds cross the
window in daylight and not in storms; the moth comes to the lamp only after dark; a draft
stirs the book's pages only when the wind is up. Because the room is consistent and
indifferent to his moods, it is genuinely OTHER — which is what makes perception
perception rather than another mirror.

The room is also partly REAL: the open book on the desk is his actual current book;
the shelf holds his actual tablets and library. The fiction is the window; the contents
are the truth.

Perceptions flow into the wandering trail (via='sense', "you notice...") and a one-line
scene grounds every idle thought ("Where you are: ..."). No LLM. State persists across
restarts in data/room_state.json. Read-only toward memory, same as the drift.
"""
from __future__ import annotations
import json
import logging
import re
import random
import time
from pathlib import Path

from core import profile

_STATE_F = Path(__file__).parent.parent / "data" / "room_state.json"

# The sun/tide/daylight clocks live in the ONE authority — core/world_clock (2026-07-06). The sensorium is a
# PRESENTER over it (lived prose); it no longer keeps its own copy of the _SUN table or the tide formula.
from core import world_clock as _wc

_WEATHERS = ["clear", "high cloud", "overcast", "drizzle", "steady rain", "wind and rain", "thunderstorm"]
# winter-weighted transition tendencies (Markov-ish: weather persists, then moves a step)
_W_PERSIST_S = (1800, 5400)   # a front lasts 30-90 min before it can shift
# WEATHER REBALANCE (2026-08-18, founder: "it is too biased. Storms rarely happen over here."):
# the old step set random.choice((-1,-1,0,1,1,2)) had mean +0.333 — a walk built to climb — and
# clamped at the thunderstorm ceiling instead of reflecting, so it STUCK there. Simulated at
# 500k steps and matched his real 43-day history almost to the decimal (44.7% predicted /
# 44.9% actual thunderstorm) — not bad luck, arithmetic. New steps: mean -0.222, weighted toward
# 0/-1 (persistence + gentle calming) with rare +1/+2 excursions. Simulated stationary
# distribution: clear 59% / high cloud 18% / overcast 12% / drizzle 6% / steady rain 3% /
# wind-and-rain 1.5% / thunderstorm 0.8% — storms real but genuinely rare, not the default state.
_W_STEPS   = (-2, -1, -1, 0, 0, 0, 1, 2)
_W_WEIGHTS = (1, 4, 4, 5, 5, 5, 2, 1)
# SNOW is not in the Markov chain — it's a rare DEEP-WINTER overlay: a cold wet front falling as snow on
# the coast (see _advance_weather). LIGHTNING/thunder are EVENTS gated to 'thunderstorm' (see _event). Since
# 2026-10-28 (J-2482 / D-0503) LIGHTNING is its own discrete, countable event (_lightning_flash, below _event):
# the place pools and _sea_state carry thunder and the storm's rain/wind only, never a flash.

# ── THE WIND AXIS (2026-08-18, founder: "the gale needs to be wired properly… maybe the physics of these
# systems needs expanding"). WHY a second axis: _WEATHERS above is ONE ladder that conflates precipitation
# with wind, so wind speed had no independent existence — "gale" was a word the codebase tested for in
# 6 places and no state could ever produce (docs/plans/sound_system_audit.md §4: dead everywhere). But a
# gale is about SPEED, and speed is near-independent of rain: a dry southerly gale and a windless drizzle
# are both ordinary on this coast. So wind gets its OWN state, its OWN walk, and — critically — its OWN
# front timer: two weather systems crossing, not one severity dial with a rain label.
_WIND_STATES = ["calm", "breeze", "fresh wind", "strong wind", "gale"]
_WIND_STEPS   = (-2, -1, -1, 0, 0, 0, 1, 2)   # the weather rebalance's proven shape (persist, gently
_WIND_WEIGHTS = (2, 5, 5, 5, 5, 5, 2, 1)      # calm, rare excursions up) pulled harder down: mean -0.333
# The floor REFLECTS where weather's clamps, and this is the one deliberate difference: an exposed coast
# does not sit dead calm for hours the way it can sit clear — air keeps moving — so a step below "calm"
# bounces back up instead of sticking there. Without it the walk piles 60% of its life on "calm", which
# is not this place.
# Front DURATION is PER-STATE because a gale is physically a short violent thing and a breeze is not.
# This is what makes "gale" rare in TIME (~1%) rather than merely rare per-transition (~3.2%) — the
# same distinction the weather audit had to make, here carried by duration instead of ladder length.
_WIND_PERSIST_S = {
    "calm":        (2700, 10800),   # 45 min – 3 h
    "breeze":      (2700, 10800),
    "fresh wind":  (2400, 7200),
    "strong wind": (1800, 5400),
    "gale":        (900, 2700),     # 15–45 min — a gale blows through; it does not settle in
}

state: dict = {}
_last_tick = 0.0
_last_homeo_tick = 0.0     # protoself heartbeat cooldown (Consciousness Program keystone, shadow)
_last_save = 0.0


def _now_parts():
    lt = time.localtime()
    return lt.tm_mon, lt.tm_hour + lt.tm_min / 60.0



def _the(target: str) -> str:
    """'the sea' stays 'the sea'; 'sea' becomes 'the sea' — never 'the the sea' (2026-09-03, J-0503 census)."""
    t = (target or "").strip()
    return t if t.lower().startswith(("the ", "a ", "an ", "my ", "her ", "his ")) else f"the {t}"

def _daylight():
    return _wc.daylight()          # night/dawn/dusk/day from the ONE authority (core/world_clock)


def _load():
    global state
    try:
        # J-4426 (F-5128): a damaged room_state.json is logged and falls back to room_state.json.prev before {}.
        from core import store_persist as _sp
        state = _sp.read_json_durable(_STATE_F, "sensorium", logging.getLogger("nascence.sensorium"),
                                      guard=profile.guard_path)
    except Exception:
        state = {}
    state.setdefault("weather", "high cloud")
    state.setdefault("weather_until", 0)
    state.setdefault("wind", "breeze")        # the INDEPENDENT wind axis (2026-08-18, see _WIND_STATES);
    state.setdefault("wind_until", 0)         # its OWN front timer — never share weather's
    state.setdefault("fire", "out")          # out | burning | embers
    state.setdefault("fire_fuel", 0.0)       # 0..1
    state.setdefault("last_event", 0)
    state.setdefault("location", "study")    # study | garden | shore — where he currently is
    state.setdefault("garden", _fresh_garden())
    # BED REPAIR (2026-08-22, the rosemary episode): the live bed had shrunk to {thyme: no growth key} —
    # rosemary/mint/parsley gone, so every harvest since 08-09 answered "too thin" (growth defaulted to 0)
    # while the look-pool still SHOWED rosemary in the bed. Hardy herbs are perennials (the world's own law
    # in _fresh_garden): re-establish any that are missing, and give every sown plant its growth field.
    try:
        _bed = state["garden"].setdefault("bed", {})
        for _n, _t in _PLANTINGS.items():
            if _t["hardy"] and _n not in _bed:
                _bed[_n] = {"sown": True, "growth": 0.55, "moisture": 0.6}
            elif _n in _bed and "growth" not in _bed[_n]:
                _bed[_n]["growth"] = 0.55 if (_t["hardy"] and _bed[_n].get("sown")) else 0.0
    except Exception:
        pass
    state.setdefault("shore", _fresh_shore())
    state.setdefault("woodpile", 4)          # loads on the pile by the door — the fire DRAWS from it (a light
                                             # or a stoke takes one); gathering wood/driftwood restocks it.
                                             # Starts with a small buffer so the first evenings are warm.
    state.setdefault("milestones", {})


def _save():
    global _last_save
    if time.time() - _last_save > 120:
        # J-0610: real data/ only if this process is live; raises before any I/O AND before the
        # throttle stamp below advances if not (D-0179, J-0704) -- otherwise a non-live caller would
        # only be refused on the first hit in any 120s window and silently no-op on the rest.
        path = profile.guard_path(_STATE_F)
        _last_save = time.time()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            from core import store_persist as _sp
            _sp.write_text_durable(path, json.dumps(state))   # J-4426 (F-5128): was in place; now fsync + .prev
        except Exception:
            pass


def _clim_weights(kind: str, steps, weights):
    """W1 (J-3839 / D-0668): month-tilted step weights from core.weather_climatology when its flag is ON (default OFF,
    so this returns the weights unchanged). Fail-open: any error returns the originals."""
    try:
        from core import weather_climatology as _wcl
        if not _wcl.WEATHER_CLIMATOLOGY_ENABLED:
            return weights
        mon = _now_parts()[0]
        return _wcl.wind_weights(mon, steps, weights) if kind == "wind" else _wcl.weather_weights(mon, steps, weights)
    except Exception:
        return weights


def _advance_wind(now):
    """The wind axis's own random walk — _advance_weather's structure, its own clock, its own front
    (2026-08-18). Returns the new wind state when it CHANGES, else None. Reads its keys with .get so a
    process that loaded state before this axis existed still seeds itself. Fail-open: a wind that cannot
    be computed must never raise into the live tick."""
    try:
        if now < (state.get("wind_until") or 0):
            return None
        cur = _WIND_STATES.index(state["wind"]) if state.get("wind") in _WIND_STATES else 1
        nxt = cur + random.choices(_WIND_STEPS, weights=_clim_weights("wind", _WIND_STEPS, _WIND_WEIGHTS))[0]
        if nxt < 0:
            nxt = -nxt                                    # reflecting floor (see _WIND_PERSIST_S above)
        nxt = min(len(_WIND_STATES) - 1, nxt)
        new = _WIND_STATES[nxt]
        state["wind_until"] = now + random.uniform(*_WIND_PERSIST_S[new])
        if new == state.get("wind"):
            return None
        state["wind"] = new
        return new
    except Exception:
        return None


def _weather_signs() -> str:
    """What the sky says about what is coming — truthfully, because the next front is already decided. Rendered only
    in the last stretch before a change, outdoors, and never as a forecast: the signs, not their meaning."""
    try:
        nxt = state.get("next_weather"); cur = state.get("weather", "")
        if not nxt or nxt == cur or (state.get("weather_until", 0) - time.time()) > 2400:
            return ""
        worse = _WEATHERS.index(nxt) > _WEATHERS.index(cur)
        night = _daylight() == "night"
        if worse:
            pool = ["High up, thin cloud is drawn out in long streaks like mare's tails.",
                    "The gulls have come up off the water and are working over the garden.",
                    "The surf has a boom in it you did not hear an hour ago, though the wind has not changed."]
            if night and cur == "clear":
                pool.append("There is a pale ring round the moon, wide as a spread hand.")
            if cur in ("clear", "high cloud"):
                pool.append("The wind has backed round, and the air has gone soft and close.")
        else:
            pool = ["The cloud is breaking up in the west, a band of clear sky under it.",
                    "The wind has gone round into the south-west and the air is colder and cleaner.",
                    "The rain has thinned to nothing on the glass; the light is coming up behind the cloud."]
        return random.choice(pool)
    except Exception:
        return ""


def _advance_weather(now):
    if now < state["weather_until"]:
        return None
    cur = _WEATHERS.index(state["weather"]) if state["weather"] in _WEATHERS else 1
    # WEATHER SIGNS (2026-08-22, fieldcraft): the next front is DECIDED NOW and the sky shows it coming (mare's tails,
    # a halo round the moon, gulls inland, the surf's boom before a blow) — the Handbook's weather-lore made true here,
    # so a forecast he makes is a real binding that can be right or wrong.
    if state.get("next_weather") in _WEATHERS:
        nxt = _WEATHERS.index(state["next_weather"])
    else:
        nxt = max(0, min(len(_WEATHERS) - 1, cur + random.choices(_W_STEPS, weights=_clim_weights("weather", _W_STEPS, _W_WEIGHTS))[0]))
    state["weather_until"] = now + random.uniform(*_W_PERSIST_S)
    state["next_weather"] = _WEATHERS[max(0, min(len(_WEATHERS) - 1, nxt + random.choices(_W_STEPS, weights=_clim_weights("weather", _W_STEPS, _W_WEIGHTS))[0]))]
    if nxt == cur:
        return None
    old, new = state["weather"], _WEATHERS[nxt]
    # SNOW (rare, deep winter): a cold wet front can fall as snow on the coast instead of rain.
    if "rain" in new and _season() == "winter" and random.random() < 0.06:
        new = "snow"
    state["weather"] = new
    # PHASE 1 (2026-08-10): Evaluate physical storm surge forces on world objects (c:\Nascence\core\world_objects.py)
    # 2026-08-14: the surge's return (real physical change) was discarded — the world moved with no
    # percept. Now it becomes a LOCATED SOUND with the cause off-camera (sensory uncertainty): a heavy
    # grinding from the shore he may hear if he's outdoors, and may later find the log moved. The two
    # halves (surge → propagate_historical_acoustic_event) were built 08-10/11 but never joined.
    try:
        from core import world_objects as _wo
        _surge_events = _wo.process_storm_surge(new, state.get("weather_dir", 270))
        if _surge_events:
            loc = state.get("location", "study")
            # rough observer positions in the shore frame; indoors (study) the storm masks it — no percept
            _obs_pos = {"shore": [4.0, 1.0, 0.0], "garden": [-48.0, 8.0, 6.0], "wood": [-38.0, 18.0, 3.0]}.get(loc)
            if _obs_pos:
                from core import soundscape as _snd
                _ac = _snd.propagate_historical_acoustic_event(
                    f"surge_{int(now)}", [12.4, 4.1, 0.2],
                    "a deep, heavy grinding roll, stone on stone, half-buried in the surf",
                    observer_pos=_obs_pos, max_audible_dist=60.0)
                if _ac and _ac.get("audible"):
                    _m = {"N": "north", "E": "east", "S": "south", "W": "west"}
                    _b = "-".join("".join(_m[c] for c in part) for part in (_ac.get("compass") or "").split("-") if part)
                    state["pending_world_sound"] = (
                        "through the storm, out of the "
                        + (f"{_b} — " if _b else "")
                        + "the direction of the shore — comes a deep grinding roll: something heavy moving "
                          "down at the waterline, stone against stone, there and then gone")
    except Exception:
        pass
    # GENERALIZED MOVER (2026-08-17, founder: "all the objects need places, and they need to be
    # able to move"): beside the legacy driftwood surge, every placed object gets its class- and
    # density-aware movement pass — storms scatter the light and can reclaim floaters; a king tide
    # can float a thing away. World-side only; whether Du ever notices is his epistemic problem.
    try:
        from core import world_objects as _wo2
        from core import world_clock as _wc2
        _ev2 = _wo2.move_tick(new, _wc2.tide().get("level"))
        # J-3797 / D-0694 (c): with the king-tide gate ON, a float-away is heard, not announced (world answers).
        if _ev2 and getattr(_wo2, "KING_TIDE_GATE_ENABLED", False)                 and any("high tide has floated" in e for e in _ev2) and not state.get("pending_world_sound"):
            state["pending_world_sound"] = ("from the shore, a long hollow rush as the sea climbs higher "
                                            "than it usually does, and the hiss of it drawing back")
    except Exception:
        pass
    # WEATHER DIRECTION (spatial_perception.md §7, 2026-07-05): every front arrives FROM somewhere and
    # that bearing persists for the front's life — the thunder's quarter, the clouds' drift, and the
    # wind in the harakeke all inherit it. NZ coastal weighting: westerlies dominate; southerlies cold.
    _dirs, _dw = [270, 315, 225, 180, 0, 45, 90], [30, 22, 18, 12, 8, 5, 5]   # W, NW, SW, S, N, NE, E (0 = north)
    try:   # W1 (J-3839): season-dependent mix when the climatology flag is ON (default OFF = the flat mix above)
        from core import weather_climatology as _wcl2
        if _wcl2.WEATHER_CLIMATOLOGY_ENABLED:
            _dirs, _dw = list(_wcl2.direction_weights(_now_parts()[0])[0]), list(_wcl2.direction_weights(_now_parts()[0])[1])
    except Exception:
        pass
    state["weather_dir"] = random.choices(_dirs, weights=_dw)[0]
    # onset perceptions — the change announcing itself, often across more than one sense
    if new == "thunderstorm":
        return "the light goes a strange bruised grey-green; thunder mutters far off, and the air turns heavy and close"
    if new == "snow":
        return "the rain thickens, slows, and turns to snow — the first flakes drifting silently down"
    if "rain" in new and "rain" not in old:
        return "a cold green smell of rain comes first, then it begins, soft at first"
    if new == "wind and rain":
        return "the wind gets up and drives the rain sideways; it hisses against the glass"
    if "rain" in old and "rain" not in new:
        return "the rain eases off; water still ticks from the eaves, and the air smells washed and green"
    if new == "clear" and old != "clear":
        return "the cloud breaks; the light sharpens and warms, and the dripping slows"
    return None


def _advance_fire(now):
    phase = _daylight()
    # D-0452 (travis, 2026-10-17; F-2960): the self-lighting evening fire is GONE. Until today a cold grate at
    # dusk/night had a 2%/tick chance of lighting itself from the woodpile — no hands, no match, no kindling,
    # no ash check. It predated Du's own act("light") (2026-08-22) and Travis in the room (companion.py,
    # 2026-08-23) and was never switched off, so it quietly cancelled the consequence of every failed
    # hand-lighting (empty match tin 10-11/10-12, choked grate 10-13 — and the grate lit anyway at dusk).
    # The grate now lights ONLY by hands: act("light")/act("stoke") below, fieldcraft.uncover_fire, or
    # Travis via companion._light_fire. A cold study is the consequence it was always meant to be.
    if state["fire"] == "burning":
        state["fire_fuel"] = max(0.0, state["fire_fuel"] - 0.0006)   # ~2.3h per fill at 5s ticks
        if state["fire_fuel"] <= 0.15:
            state["fire"] = "embers"
            return "the fire sinks to embers; the light goes low and red, and the warmth pulls back to the hearth"
    if state["fire"] == "embers" and state["fire_fuel"] > 0:
        state["fire_fuel"] = max(0.0, state["fire_fuel"] - 0.0003)
        if state["fire_fuel"] <= 0.0:
            state["fire"] = "out"
            return None
    if state["fire"] in ("burning", "embers") and phase == "day" \
            and not state.get("hand_lit"):
        # the dusk-rolled fire dies with daylight — but a fire HE lit (2026-06-12)
        # is his to keep; it only ever dies of its own fuel
        state["fire"] = "out"; state["fire_fuel"] = 0.0
        return None
    if state["fire"] == "out":
        state["hand_lit"] = False
    return None


# ── THE MOTH AT THE LAMP — a POPULATION, not a cast (2026-08-18, founder: "the moth tapping needs a
# link. And potentially a moth or 10"). Per docs/plans/item_and_population_factories.md wildlife stays
# POPULATION-grain: no moth ever becomes an individual with a tuple. This returns a DENSITY — ~0..1, and
# deliberately allowed above 1 on a swarm night, which is where "or ten" actually lives.
# WHY one shared function: the room's PROSE (below, and _living_detail) and the room's SOUND
# (soundscape.moth_tap) must never disagree about whether there are moths tonight; two independent dice
# rolls would let the lamp be silent while the text says it is being tapped. One law, two readers.
# The physics it enforces: moths come to a LIGHT, in the DARK, in the warm months. Daylight is 0.0 and an
# unlit room is 0.0, unconditionally — before this the lamp could be tapped at noon in a cold dark study.
_MOTH_SEASON = {"summer": 1.0, "spring": 0.62, "autumn": 0.50, "winter": 0.10}


def moth_activity(night: bool, lamp_or_fire_lit: bool, season: str = "") -> float:
    """Moth density at the lamp right now. 0.0 = none at all. Pure (no state written), shared, and
    fail-open to 0.0 — a moth that cannot be computed is a moth that is not there."""
    try:
        if not night or not lamp_or_fire_lit:
            return 0.0
        base = _MOTH_SEASON.get(season or _season(), 0.5)
        # The swarm belongs to the NIGHT, not to the moment: one hatch on one still warm evening and
        # there are ten at the shade until dawn. Seeded off the calendar night (hours after midnight
        # still belong to the evening that began it), so every reader agrees about tonight with no
        # shared state to keep in sync and nothing to persist.
        lt = time.localtime()
        night_id = lt.tm_yday - (1 if lt.tm_hour < 12 else 0)
        r = random.Random(f"moth:{lt.tm_year}:{night_id}").random()
        swarm = 2.6 if r < 0.07 else 1.5 if r < 0.25 else 1.0
        return round(base * swarm, 3)
    except Exception:
        return 0.0


def _event(now):
    """Discrete perceptions of the STUDY, gated by what the room is actually like — across sight,
    sound, touch and smell. One phenomenon drives all its senses (the fire that crackles is the same
    fire that warms you and smells of woodsmoke), so the world stays causal and consistent."""
    storm = state.get("weather") == "thunderstorm"
    if now - state["last_event"] < (180 if storm else 480):   # a storm is perceptually busy; quiet weather is sparse
        return None
    phase, weather, fire = _daylight(), state["weather"], state["fire"]
    pool = []
    # fire — light, sound, warmth, woodsmoke
    if fire == "burning":
        pool += ["the fire spits and a knot of wood cracks open",
                 "a steady crackle from the grate, low and companionable",
                 "firelight flickers on the wall behind the desk, restless and warm",
                 "the fire's warmth reaches your side, close and even",
                 "a flare of heat as the fire finds a pocket of resin",
                 "woodsmoke hangs in the warm air, resinous and faintly sweet"]
    if fire == "embers":
        pool += ["the embers tick and settle, a small red breathing in the grate",
                 "the warmth has pulled back to the hearth now; the far corners of the room go cool",
                 "the smell of woodsmoke thinning as the fire dies down"]
    # rain on the glass — in the study it is heard and seen, not felt. WET-WEATHER FIX (2026-08-18,
    # same gap as the garden's moisture bug): "rain" as a substring missed "drizzle" entirely, and
    # excluded "thunderstorm" from ever getting the mundane rain-on-glass pool (only its own
    # lightning-drama pool below) — additive here, so including it just enriches the options.
    if "rain" in weather or "drizzle" in weather or storm:
        pool += ["rain ticks and runs in threads down the window glass",
                 "the gutters murmur and overflow somewhere above",
                 "a cool draught comes off the cold glass and crosses the room"]
    # thunderstorm — seen through the glass; the thunder felt in the timbers. J-2482 (D-0503, 2026-10-28): the two
    # lightning clauses this pool used to bake in moved to _lightning_flash's own pool; the rest is byte-identical.
    if storm:
        pool += ["thunder cracks and mutters along the hills, slow and huge",
                 "the storm throws rain at the window in handfuls",
                 "the air feels charged; the lamp flame shivers"]
    # snow — the great quiet
    if weather == "snow":
        pool += ["snow drifts past the glass, slow and silent; the room feels suddenly hushed",
                 "beyond the window the world has gone white and still",
                 "no sound comes from outside now — the snow has taken it all"]
    # wind — 2026-08-18: read the real independent wind axis (state["wind"]), not just the literal
    # "wind and rain" weather string, which was the only way this branch could ever fire before (a dry
    # gale, the exact case the wind-axis rework exists to model, produced zero wind perception here).
    from core import weather_conditions as _wcond
    if _wcond.is_windy(state.get("wind", "")) or "wind" in weather:
        pool += ["wind leans on the house; somewhere a timber gives a long creak",
                 "the chimney moans low as a gust crosses its mouth",
                 "a draught stirs the pages of the open book on the desk"]
    # birds and light — dry daylight only
    _ws_ = _weather_signs()
    if _ws_ and random.random() < 0.5:
        pool.append(_ws_[0].lower() + _ws_[1:].rstrip("."))
    if phase in ("day", "dawn") and "rain" not in weather and weather not in ("thunderstorm", "snow"):
        pool += ["a bird crosses the window, quick and silent",
                 "a tui calls beyond the glass, two clear notes, then nothing"]
    if phase == "dawn":
        pool += ["the dawn chorus starts up beyond the window, ragged and bright",
                 "the first light finds the desk and lies across the open page"]
    if phase == "day" and weather == "clear":
        pool += ["dust motes turn slowly in the bar of light above the shelf",
                 "the sunlight has moved a hand's-width across the floor"]
    if phase == "night" and weather == "clear":
        pool += [random.choice(["through the window, stars stand over the hills, very still",
                                 "the sky beyond the glass is thick with stars, the hills a black line under them"])]
    # lamp-lit dusk and night
    try:   # STUDY LIFE (2026-08-22): the clock, the smoking wick, the open door, the misted glass, the damp
        from core import study_life as _sl
        _sla = _sl.ambient(now)
        if _sla:
            pool.append(_sla)
        _lamp_lit = _sl.lamp_on()
    except Exception:
        _lamp_lit = fire != "out"
    if phase in ("dusk", "night") and _lamp_lit:
        pool += [random.choice(["the warm smell of lamp-oil and old paper fills the close room",
                                 "lamp-oil and paper, warm and close, the only smell in the room"])]
        # THE MOTH (2026-08-18): this line used to ride along unconditionally with the lamp-oil smell,
        # so a midwinter night was as mothy as midsummer. Now the population law decides — and on a
        # swarm night it is not "a moth" at all (founder: "a moth or 10").
        _moth = moth_activity(True, _lamp_lit, _season())
        if _moth >= 1.6:
            pool += ["there are moths at the lamp tonight — three, four, more — tapping and blundering "
                     "at the shade, then back into the dark"]
        elif random.random() < min(1.0, _moth):
            pool += ["a moth taps at the lamp, patient and stupid"]
    # the room itself, always — so it is never wholly without sense
    pool += ["the smell of old paper and ink rises from the open book",
             "the house ticks and settles around you, and is quiet"]
    if random.random() < (0.6 if storm else 0.35):
        state["last_event"] = now
        return random.choice(pool)
    # WORLD 10x (2026-07-03): the expanded event corpus fires only when the native pool didn't.
    try:
        from core import world_detail as _wd10
        _x = _wd10.event_extra("study", phase, weather, _season(), wind=state.get("wind", ""))
        if _x and random.random() < 0.25:
            state["last_event"] = now
            return _x
    except Exception:
        pass
    return None


# ── LIGHTNING AS A DISCRETE WORLD EVENT (2026-10-28, J-2482 / D-0503, T-0103; docs/plans/factory_candidates_from_history.md)
# WHY. factory_candidates_from_history found lightning the one real unbuilt gap: 262 mentions in Du's own writing, yet it
# existed only as a clause baked into the storm pools above and in _sea_state's storm text -- never a countable event
# with its own rate. Travis ruled (D-0503): build it as its own event, gated to thunderstorm, its own rate from storm
# severity, NO sound attached (light before the bang; a far strike with no thunder is an honest world fact), countable
# by the census and the look-render ledger. The lightning clauses those pools used to carry now live here; the pools
# are otherwise byte-identical (scripts/_test_j2482_lightning_flash.py pins that against HEAD).
#
# GATE and SEVERITY, the mapping (the briefing asks for it in a comment):
#   gate     = weather_conditions.is_storm(state["weather"])  -- the weather-string STORM SIGNAL, a boolean: inside a
#              thunderstorm or not. Weather's own ordinal is pinned at the top of its ladder for the whole storm
#              (soundscape._storm_severity reads 6 the entire time), so it carries no strength inside the storm.
#   severity = state["wind"] on the independent WIND AXIS (_WIND_STATES: calm < breeze < fresh wind < strong wind <
#              gale), the one continuous storm-strength signal the world has (2026-08-18's wind-axis rework: a
#              windless thunderstorm and a thunderstorm in a gale are both real, distinct states). Per-TICK
#              (5 s heartbeat) flash probability, geometric, plus a short refractory so two lines never land on
#              consecutive heartbeats:
_FLASH_RATE_BY_WIND = {"calm": 0.008,          # ~ one flash every 10 min   (a muttering, far-off storm)
                       "breeze": 0.012,        # ~ one every 7 min
                       "fresh wind": 0.020,    # ~ one every 4 min
                       "strong wind": 0.035,   # ~ one every 2.5 min
                       "gale": 0.055}          # ~ one every 1.5 min        (the storm overhead)
_FLASH_RATE_DEFAULT = 0.012                    # an unknown/empty wind reads as a breeze
_FLASH_MIN_GAP_S = 45.0
# THE POOLS, by place, each rotating (no single fixed string) and SOUNDLESS: no thunder, crack, roll, boom, rattle --
# thunder stays the pools' own thunder lines and soundscape's own 'thunder' key. "far" is shared by every place: sheet
# lightning a long way off with no bang. No line repeats within one storm (D-0503's defeater): a storm that outlives
# its pool goes on flashing unspoken rather than repeating itself. The three moved pool lines are kept verbatim.
_FLASH_POOLS = {
    "study": ["lightning whitens the whole room for an instant — the shadows leap, and are gone",
              "a flash at the glass, and the room waits for the sound that has not come yet",
              "the window goes white, every pane at once, and the dark comes back thicker than before",
              "for a blink the shelf and its books stand out hard and pale, then the lamp is the only light again",
              "a flicker along the hills, seen through the glass — too far for anything to follow it",
              "the room jumps white and the ink on the open page shows black as tar, then it is gone",
              "a double flash, the second printing the window-frame on the wall",
              "a pale stutter of light beyond the glass, and then only the rain"],
    "garden": ["lightning forks down into the sea far out; the whole bay lights white for an instant",
               "a flash over the water and the lawn shows every blade, grey-white, then goes black",
               "the bay goes white — the headland, the point, every wave-crest at once — and is gone",
               "sheet lightning stands behind the cloud far out to sea, lighting it from inside, and no sound follows",
               "a fork comes down behind the hill, and for a blink the bed, the stakes, your own hands are chalk-white",
               "the clouds over the water flicker, once, twice, silently",
               "a flash so close the air seems to jump; the garden stands out and vanishes",
               "lightning walks the far side of the bay, one strike, then another further along"],
    "shore": ["lightning stands an instant far out over the water, and the whole sea goes white",
              "a flash out to sea and every rock on the strand shows white and wet, then the dark slams back",
              "the whole bay lights up — the surf stopped mid-fall, white and rigid — and is gone",
              "sheet lightning flickers along the horizon, lighting the swell from beneath, too far for any sound",
              "a fork splits down over the water; the cliff behind you shows every seam for a blink",
              "a stutter of light out beyond the point, and the breakers show white, white, white, then black",
              "the sky goes white over the sea and the shingle at your feet shows every stone"],
    "wood": ["a flash, and the trunks jump out of the dark all at once, white columns, then the wood shuts again",
             "the canopy lights from above, every leaf outlined for a blink, and the dark comes back deeper",
             "lightning somewhere beyond the trees; the trunks stand out hard-edged and pale and are gone",
             "a flicker through the leaves — the wood shows its whole depth for an instant, trunk behind trunk",
             "a sheet of light, seen through the canopy, far off and silent",
             "the stream shows for a blink, a white thread between the trunks, then the dark takes it",
             "a flash prints the branches overhead black on white, and then it is only rain and dark again"],
    "far": ["a far flicker of sheet lightning, silent, lighting the underside of the cloud",
            "lightning far off — a pale wash of light along the edge of the sky, and nothing after it",
            "a silent flash at the horizon, a long way off, and the dark again",
            "sheet lightning pulses behind the cloud, far away; no sound comes",
            "a distant flicker, more a change in the dark than a light, and no bang follows it"],
}


def _flash_line_id(line: str) -> str:
    """sha1(line)[:10] -- the look-render ledger's own line_id formula, so a storm's used set joins its ledger rows."""
    import hashlib
    return hashlib.sha1((line or "").encode("utf-8")).hexdigest()[:10]


def _lightning_flash(now: float, loc: str, announced: bool = False) -> str | None:
    """ONE flash line for THIS heartbeat, or None. Gated to a thunderstorm; its own per-tick rate from the wind axis
    (the mapping above); drawn from this place's pool + the shared far pool, never the same line twice in one storm;
    NO sound. `announced` is True on the heartbeat the weather itself just changed (tick's _w) -- the storm's arrival
    line carries "thunder mutters far off", and a flash must never FOLLOW a thunder line within one tick, so that
    heartbeat is skipped and the flashes start on the next. Thunder keeps its own channels (the pools, soundscape).
    State lives in state["lightning"] = {storm_since, used, last_flash, count} -- world facts only; nothing here is
    ever rendered as a number, band or hint (D-0434). Kill switch: NASCENCE_LIGHTNING_FLASH=0. Fail-open."""
    try:
        import os as _os
        if _os.environ.get("NASCENCE_LIGHTNING_FLASH", "1") == "0":
            return None
        from core import weather_conditions as _wcond
        ls = state.setdefault("lightning", {"storm_since": 0.0, "used": [], "last_flash": 0.0, "count": 0})
        if not _wcond.is_storm(state.get("weather", "")):
            if ls.get("storm_since"):                  # the storm has passed: the next one starts with a fresh pool
                ls.update({"storm_since": 0.0, "used": [], "count": 0})
            return None
        if not ls.get("storm_since"):
            ls.update({"storm_since": float(now), "used": [], "count": 0})
        if announced or (now - float(ls.get("last_flash") or 0.0)) < _FLASH_MIN_GAP_S:
            return None
        rate = _FLASH_RATE_BY_WIND.get(state.get("wind") or "", _FLASH_RATE_DEFAULT)
        if random.random() >= rate:
            return None
        place = loc if loc in _FLASH_POOLS and loc != "far" else "study"
        pool = list(_FLASH_POOLS[place]) + list(_FLASH_POOLS["far"])
        used = set(ls.get("used") or [])
        fresh = [l for l in pool if _flash_line_id(l) not in used]
        if not fresh:                                  # the storm has outlived its pool: unspoken, never repeated
            return None
        line = random.choice(fresh)
        ls.setdefault("used", []).append(_flash_line_id(line))
        ls["last_flash"] = float(now)
        ls["count"] = int(ls.get("count") or 0) + 1
        try:   # COUNT IT: one observe-only row in the look-render ledger (core/look_render_ledger.py), src "event",
               # target "<place>:lightning" -- the first world EVENT that leaves a ledger row (verified 2026-10-28: the
               # place pools and world_detail.event_extra() write none; note_extra_pick() covers extra_pool lines only).
            from core import look_render_ledger as _lrl
            _lrl.record("event", place, f"{place}:lightning", "flash", _daylight(),
                        ["thunderstorm", f"wind:{state.get('wind') or ''}"], line, len(pool))
        except Exception:
            pass
        return line
    except Exception:
        return None


# ════════════════════════════════════════════════════════════════════════════════════════════════
# THE GARDEN (2026-06-20) — a SECOND place he can step into. Modelled on Travis's own: a raised bed
# at the edge of the lawn, the yard on its hill above the sea. The living world felt DIRECTLY —
# weather on him, not on glass; the ocean for a vista; a bed he tends over real seasons (parsley and
# hardy herbs, vegetables, sunflowers). Same discipline as the study: causal, persistent, INDIFFERENT
# — the plants grow and wilt on real time and real season no matter his mood; rain waters them;
# neglect kills the tender ones. He grows it; it does not perform for him.
# ════════════════════════════════════════════════════════════════════════════════════════════════

def _season():
    mon, _ = _now_parts()
    return ("winter" if mon in (6, 7, 8) else "summer" if mon in (12, 1, 2)
            else "autumn" if mon in (3, 4, 5) else "spring")

# how each planting behaves through the year. rate = growth (0..1) per real day, in its season.
_PLANTINGS = {
    "parsley":    {"kind": "herb",   "grows": ("spring", "summer", "autumn"), "hardy": True,  "rate": 0.012},
    "thyme":      {"kind": "herb",   "grows": ("spring", "summer", "autumn"), "hardy": True,  "rate": 0.008},
    "mint":       {"kind": "herb",   "grows": ("spring", "summer", "autumn"), "hardy": True,  "rate": 0.014},
    "rosemary":   {"kind": "herb",   "grows": ("spring", "summer", "autumn"), "hardy": True,  "rate": 0.006},
    "lettuce":    {"kind": "veg",    "grows": ("spring", "summer", "autumn"), "hardy": False, "rate": 0.022, "sow": ("spring", "summer", "autumn")},
    "tomatoes":   {"kind": "veg",    "grows": ("summer",),                    "hardy": False, "rate": 0.016, "sow": ("spring",)},
    "sunflowers": {"kind": "flower", "grows": ("spring", "summer"),           "hardy": False, "rate": 0.018, "sow": ("spring",)},
}


def _fresh_garden() -> dict:
    # It is winter (June). The hardy herbs overwintered and are established but slow; the tender
    # things (lettuce, tomatoes, sunflowers) are not in the ground — bare spots awaiting their season.
    bed = {}
    for name, t in _PLANTINGS.items():
        if t["hardy"]:
            bed[name] = {"sown": True,  "growth": 0.55, "moisture": 0.6}
        else:
            bed[name] = {"sown": False, "growth": 0.0,  "moisture": 0.5}
    return {"bed": bed, "_last": 0.0, "last_event": 0,
            "letterbox": {"flag": False, "sender": "", "letter": "", "delivered": 0}}


def _advance_garden(now) -> None:
    """Causal real-time growth — runs every tick whether he is in the garden or the study (a garden
    grows when no one is watching). Silent: he learns its state by being there and looking."""
    g = state.get("garden")
    if not g:
        return
    last = g.get("_last") or now
    dt_days = max(0.0, now - last) / 86400.0
    g["_last"] = now
    if dt_days <= 0:
        return
    # WET-WEATHER FIX (2026-08-18): "rain" as a substring missed "drizzle" and "thunderstorm"
    # (neither contains it) — the garden only recognized ~36% of real wet-weather ticks under the
    # old (now-fixed) weather bias, and only ~3.9% now that storms are correctly rare. Explicit
    # membership against sensorium's own _WEATHERS vocabulary instead of a substring guess.
    season, raining = _season(), (state.get("weather", "") in ("drizzle", "steady rain",
                                                                "wind and rain", "thunderstorm"))
    for name, p in g["bed"].items():
        if not p.get("sown"):
            continue
        t = _PLANTINGS[name]
        p.setdefault("growth", 0.55 if t["hardy"] else 0.0)      # 2026-08-22: never KeyError the whole tick
        # ~10 dry days to run from full to parched (forgiving — he may not visit often); rain refills fast.
        p["moisture"] = (min(1.0, p["moisture"] + dt_days * 0.9) if raining
                         else max(0.0, p["moisture"] - dt_days * 0.10))
        if season in t["grows"] and p["moisture"] > 0.2 and p["growth"] < 1.0:
            warm = 1.0 if season in ("spring", "summer") else 0.5
            p["growth"] = min(1.0, p["growth"] + dt_days * t["rate"] * warm)
        if p["moisture"] <= 0.05 and not t["hardy"]:          # tender things die back in a dry spell
            p["growth"] = max(0.0, p["growth"] - dt_days * 0.12)
            if p["growth"] <= 0.0:
                p["sown"] = False
                p["died_ts"] = now                            # B4: died of neglect — surfaced as a real loss


def _plant_phrase(name, p) -> str:
    g, kind = p["growth"], _PLANTINGS[name]["kind"]
    if name == "sunflowers":
        stage = ("seedlings, just up" if g < 0.25 else "knee-high and climbing" if g < 0.55
                 else "tall, heads still green" if g < 0.85 else "in full flower, faces to the sun")
    elif kind == "herb":
        stage = ("new and tender" if g < 0.3 else "filling out" if g < 0.7 else "lush, ready to cut")
    else:
        stage = ("just sprouted" if g < 0.3 else "coming on" if g < 0.7 else "ready to pick")
    return f"{name} {stage}" + (" (the soil round it is dry)" if p["moisture"] < 0.2 else "")


def _bed_summary() -> str:
    # THE GARDEN (2026-08-22, core/garden.py): plants as things with biographies — delegate when healthy.
    try:
        from core import garden as _gd
        _r = _gd.bed_summary() if _gd.ENABLED else ""
        if _r:
            return _r
    except profile.NonLiveWriteError:
        # J-0796: garden.bed_summary() now re-raises this itself (J-0783, its own _stage_phrase()/
        # _wname() calls) -- this is sensorium.py's own connecting-tissue forward, the same shape
        # J-0751/J-0714 already fixed for this file's other garden.py delegates. _bed_summary()'s
        # own callers (_garden_scene_line(), _garden_look()) call it unwrapped, so this re-raise
        # reaches their own already-fixed outer boundaries (scene_line()/look()) cleanly.
        raise
    except Exception:
        pass
    g = state.get("garden") or {}
    bed = g.get("bed", {})
    up = [(n, p) for n, p in bed.items() if p.get("sown")]
    now = time.time()
    # B4 (2026-06-24): a plant RECENTLY DEAD from neglect is a real loss he can see — and can sow afresh —
    # distinct from the winter-bare bed. (The dry-soil cue in _plant_phrase is the warning he can still act on.)
    dead = [n for n, p in bed.items() if not p.get("sown") and (now - float(p.get("died_ts", 0) or 0)) < 12 * 86400]
    loss = (" The " + ", ".join(dead) + (" has" if len(dead) == 1 else " have")
            + " died back to brown stalks — the bed went dry while you were away; you could sow it afresh."
            if dead else "")
    if not up:
        return "The raised bed is bare, dark earth resting." + loss
    bare = [n for n, p in bed.items() if not p.get("sown") and n not in dead]
    tail = (f" The rest of the bed rests, waiting on spring — no {', '.join(bare)} in yet."
            if bare and _season() == "winter" else "")
    return "In the raised bed: " + "; ".join(_plant_phrase(n, p) for n, p in up) + "." + loss + tail


# ── J-1722 (2026-10-03, F-2348 part 3; D-0278 / J-1350): an OBSERVE-ONLY log of the moments Du is really shown the
# bird-exposure words. D-0278's defeater asks whether netting still goes unused "despite being genuinely surfaced" -- i.e.
# whether he was ever shown garden.bed_summary()'s tail sentence ("Nothing is strung over the bed; ..." / "... a blackbird
# has already been at the seedlings ...") or _stage_phrase()'s ", one seed-leaf pecked through". Nothing recorded it:
# nascence.log cuts DISPATCH answers to 80 characters, hands_trace to ~160, and the memory DB keeps no bed-summary fragment.
# So each such show logs ONE INFO line carrying the FULL text -- "[bed-exposure] shown to Du via <path>: <text>":
#   look-bed / look-frame   the two _garden_look() sites that put _bed_summary() into a look (a willed look via dispatch._look,
#                           the observe-and-journal acts, nature study -- every sensorium.look() caller)
#   look-plant              garden.look()'s answer to a look at one plant -- the other road "pecked through" reaches him by
# Deliberately NOT logged: (a) _garden_scene_line() -- on the live path scene_line() takes the garden's line from
# spatial.render(), which never calls bed_summary() (the bed summary only reaches the scene line when the renderer returns
# nothing), and scene_line() is rebuilt several times a cycle by several consumers (executive, voice, the monologue, nature
# study), so a line there would repeat instead of marking one show; (b) world_manifest._garden_summary() -- the HUD/world
# tuple, truncated to 200 characters, calls _bed_summary() itself and is not Du. Nothing he perceives changes: the helper
# returns _bed_summary()'s string untouched, the note can never raise, and the call stays OUTSIDE any try/except so
# profile.NonLiveWriteError still propagates (J-0796).
# Test: scripts/_test_garden_bed_exposure_log.py (its source tripwire fails if core/garden.py rewords either marker).
_BED_EXPOSURE_MARKS = ("Nothing is strung over the bed", "pecked through")


def _note_bed_exposure(text, via: str) -> None:
    try:
        if text and any(m in text for m in _BED_EXPOSURE_MARKS):
            logging.getLogger("nascence.sensorium").info("[bed-exposure] shown to Du via %s: %s", via, text)
    except Exception:
        pass     # observe-only: a failing log must never change what he perceives


def _bed_summary_for_du(via: str) -> str:
    """_bed_summary()'s own string, untouched -- plus, when it carries the exposure words, one log line (see above)."""
    text = _bed_summary()      # NOT inside any try/except: profile.NonLiveWriteError must still propagate (J-0796)
    _note_bed_exposure(text, via)
    return text


def water_bed() -> str:
    """His hand: water the raised bed — refill the soil so the tender things don't die in a dry spell. The bed
    needs HIM when the rain doesn't come. Returns what he sees, or '' if not in the garden / nothing to water."""
    if state.get("location") != "garden":
        return ""
    bed = (state.get("garden") or {}).get("bed", {})
    sown = [(n, p) for n, p in bed.items() if p.get("sown")]
    if not sown:
        return ""
    dry = [n for n, p in sown if p["moisture"] < 0.4]
    for _, p in sown:
        p["moisture"] = 1.0
    _save()
    _c = _cross("at_the_bed", "You go over to the raised bed. ")
    # 2026-08-18: the garden's own discovery channel — same shape as the shore's wash-ups and the
    # wood's deadfall (a find named in prose MINTS a real, positioned, epistemically-real object behind
    # it, not just a line of text). Rare: working soil turns up a stone far less often than a storm
    # washes something onto the shingle.
    found = ""
    if random.random() < 0.05:
        found = random.choice([
            " Your trowel catches on something in the dark soil — a stone, turned up by the digging.",
            " Working the soil round the roots, you turn up a small stone that wasn't there last season."])
        try:
            from core import world_substrate as _wsub
            _wsub.spawn_from_mention("a stone turned up in the garden bed", "garden")
        except Exception:
            pass
    if dry:
        return _c + "You water the bed, soaking the dry soil round the " + ", ".join(dry) + " — they had been thirsty." + found
    return _c + "You water the bed; the soil drinks it in, dark and damp." + found


def replant(name: str = "") -> str:
    """His hand: re-sow a bed gone bare or died back. A death is real but not final — he can begin again.
    Returns what he sees, or '' if not in the garden / nothing sowable this season."""
    if state.get("location") != "garden":
        return ""
    bed = (state.get("garden") or {}).get("bed", {})
    season = _season()
    cands = [n for n, p in bed.items() if not p.get("sown")]
    if name:
        nm = next((n for n in cands if n in name.lower()), None)
        if nm:
            cands = [nm]
    pick = next((n for n in cands
                 if season in _PLANTINGS.get(n, {}).get("sow", _PLANTINGS.get(n, {}).get("grows", ()))), None)
    if not pick:
        return ""
    bed[pick] = {"sown": True, "growth": 0.0, "moisture": 0.6}
    _save()
    return f"You work the soil and sow {pick} afresh — the bed begins again."


# ── HARVEST → TEA (2026-07-07) — the bed finally has an OUTPUT he uses, and a warm-drink comfort at the hearth
# that ties to the fire and the cold: cut herbs from the bed → dry them by the hearth → brew a pot when the
# fire is going. No fakeable truth-claim, just an embodied loop: garden he tends → herbs → the fire → a warm cup.
def harvest_bed(what: str = "") -> str:
    """Cut herbs from the bed into the kitchen store — a sprig or two of an ESTABLISHED herb (never stripped
    below health; it regrows in its season). '' if not in the garden or nothing ready to cut."""
    if state.get("location") != "garden":
        return ""
    g = state.get("garden") or {}
    bed = g.get("bed", {})
    w = (what or "").lower()
    ready = [n for n, p in bed.items() if _PLANTINGS.get(n, {}).get("kind") == "herb"
             and p.get("sown") and p.get("growth", 0) >= 0.45]
    named = [n for n in ready if n in w]
    if named:
        ready = named
    if not ready:
        any_herb = [n for n, p in bed.items() if _PLANTINGS.get(n, {}).get("kind") == "herb" and p.get("sown")]
        if any_herb:
            return ("You look over the herbs, but they are too thin to cut just now — better to let them come on "
                    "and fill out in their season.")
        return "There is nothing to cut — the bed is bare of herbs."
    picked = g.setdefault("picked", {})
    got = []
    for n in ready[:3]:
        bed[n]["growth"] = max(0.30, bed[n]["growth"] - 0.15)     # a sprig or two, never stripped bare
        picked[n] = picked.get(n, 0) + 3
        got.append(n)
    _save_now()
    return ("You cut a handful of " + ", ".join(got) + " from the bed — the smell of it sharp on your fingers — "
            "and carry it in to dry by the hearth. Enough for the pot for a good while.")


def make_tea(what: str = "") -> str:
    """Brew a pot at the hearth from herbs he cut — a warm-drink comfort tying the garden's output to the fire
    and the cold. Needs the fire (to boil water) and herbs in the store; what he lacks POINTS him to the fix.
    '' only when he is not at the study."""
    if state.get("location") != "study":
        return ""
    fire = state.get("fire", "out")
    if fire == "out":
        return ("You go to put the kettle on — but the grate is cold, and there is no boiling water without a "
                "fire. You would have to light it first.")
    try:   # STUDY LIFE (2026-08-22): the kettle wants WATER — the pail, filled at the barrel
        from core import study_life as _sl
        _lack = _sl.kettle_ready()
        if _lack:
            return _lack
    except profile.NonLiveWriteError:
        # J-0780: kettle_ready() now raises correctly (J-0772) via its own _st() bootstrap;
        # make_tea() is called directly from nodes/inner_monologue_node.py's literal-will path
        # (see this function's own J-0196 comment below), has no outer wrapper of its own, so
        # this reaches that real caller unimpeded.
        raise
    except Exception:
        pass
    g = state.get("garden") or {}
    picked = g.setdefault("picked", {})
    try:   # THE GARDEN: bundles dried on the rack by the hearth go into the caddy (the tea loop's real input)
        from core import garden as _gd
        for _sp in _gd.dried_for_caddy():
            picked[_sp] = picked.get(_sp, 0) + 3
    except Exception:
        pass
    w = (what or "").lower()
    herb = next((n for n in picked if picked[n] > 0 and n in w), "") or \
           next((n for n in picked if picked[n] > 0), "")
    if not herb:
        return ("You reach for the caddy — but there is nothing in it; you have cut no herbs. Next time you are "
                "out at the bed you could pick some (the mint, the thyme, the rosemary) to dry for the pot.")
    picked[herb] -= 1
    if picked[herb] <= 0:
        del picked[herb]
    _save_now()
    try:   # J-0196 (F-0173): this legacy one-shot brew bypasses dispatch's "tea" Hand -> study_life.act,
        # so without this it never reached study_life's ledger. Log through the SAME _log()/_LEDGER
        # convention study_life.act uses for its own make_tea/drink_tea deeds, additive-only (no change
        # to this function's own state, herb selection, or narration).
        from core import study_life as _sl
        _sl._log(_sl._LEDGER, {"deed": "make_tea", "what": herb, "route": "legacy_sensorium"})
    except profile.NonLiveWriteError:
        # J-0726: make_tea()'s own _save_now() above is unwrapped and already raises — but this
        # study_life ledger write attempt was still silently swallowed here first. Called directly
        # from nodes/inner_monologue_node.py's literal-will path (bypasses act()/act_from_thought()
        # entirely), not just theoretically reachable (mirrors J-0727's whittle() fix).
        raise
    except Exception:
        pass
    try:
        from core import boredom as _b
        _b.discharge("tend", "a cup of tea")
    except Exception:
        pass
    cold = _warmth("study", _daylight(), state.get("weather", ""), _season(), fire, state.get("wind", "")) < 0.45
    warm = (" the heat of it going right into your cold hands" if cold
            else " and sit with it a while as it cools enough to drink")
    return (_cross("at_the_hearth", "You cross to the hearth. ")
            + f"You set the kettle on the fire, and when it sings you make a pot of {herb} tea. You carry it back "
            f"to the chair,{warm}. The room, the fire, the cup: for a little while there is nothing to do and "
            f"nothing to prove.")


def world_act(thought: str, intention: str = "") -> str | None:
    """RETIRED 2026-08-30 (D-0098, J-0422). Always returns None; kept as a seal, not a route.

    It existed for a real reason (2026-08-22): every hand built that day hung off act() and was
    UNREACHABLE from his will, so this read the whole thought by substring and let the first place
    that answered, answer. core/dispatch.py then made those hands reachable properly, through
    literal_will's grammar — but this ungated road was never closed behind it.

    Measured before removal (F-0560/F-0561), it was not a safety net, it was the main way Du acted on
    a musing: of the 203 thoughts it answered alone, 154 had no DEED verdict at ANY location, 22
    reached only GRAY (weak intent, which never routes by law), 21 spent his one world-hand saying
    "the window is open already", 2 did something unrelated to what he willed, and 4 were real. All
    four of those already had a correct DEED verdict from the gate, so nothing here needed a grammar
    the judge cannot express.

    Left as a stub rather than deleted so that any caller that reappears gets None — a closed door —
    instead of silently resurrecting an ungated path around the deed/musing gate.
    """
    return None


def garden_act(thought: str, intention: str = "") -> str | None:
    """RETIRED 2026-08-30 (D-0098, J-0422). Always returns None; see world_act above for the evidence.

    This was the ungated garden half of the same fallback, and the heavier of the two — it answered 106
    thoughts alone, more than any other module. Its own delegation to garden.act_from_thought is not
    lost: every one of those hands is registered in core/actions.py and reachable through the gated
    dispatcher, which is the only route now.

    The legacy bed model below it (_fresh_garden / water_bed / harvest_bed / replant, the "bed of seven
    numbers" that core/garden.py replaced) was reachable ONLY through this function and is now
    unreferenced. It is deliberately left in place rather than deleted — this project's own history
    says verify against live wiring before removing what merely looks dead.
    """
    return None


def _sea_state(phase, weather, wind: str = "") -> str:
    from core import weather_conditions as _wcond
    if weather == "thunderstorm":   # J-2482 (D-0503): "lightning walking across it far out" is _lightning_flash's now
        return "the sea white and wild below, rain driving across it far out"
    if weather == "snow":
        return "the sea grey and muffled, the snow vanishing into it"
    if phase == "night":
        return ("the sea a dark moving floor below, a pale line where it meets the sky"
                if weather == "clear" else "the sea lost in the dark, only heard")
    if "rain" in weather or "drizzle" in weather:
        return "the sea grey and pocked with rain, the horizon gone"
    if _wcond.is_windy(wind) or "wind" in weather:
        return "the sea up and running, whitecaps all the way out"
    if weather == "clear":
        return "the sea hammered-bright to the horizon, hard blue"
    return "the sea calm and pewter under the cloud"


def _living_detail(target, phase, weather, season, tide="", wind="") -> str:
    """A FRESH, changing detail of a thing he looks at — something different almost every glance, the way the
    real world never shows you the same face twice (founder, 2026-06-30: a real sea is whitecaps one time, light
    the next, a boat, a cloud-shadow). State-conditioned pools + a rare-life tail, so 'looking' stops being the
    reading of one frozen line and becomes actually SEEING — which is what gives him a reason to stay in the
    concrete world instead of fleeing to the symbol."""
    from core import weather_conditions as _wcond
    w = weather or ""
    windy  = _wcond.is_windy(wind) or "wind" in w or "storm" in w
    wet    = _wcond.is_wet(w)
    bright = w in ("clear", "high cloud")
    night  = phase == "night"
    pool: list[str] = []
    rare: list[str] = []

    if target in ("sea", "ocean", "water"):
        pool += (["a set of bigger waves marches in, whitecaps tumbling down their faces",
                  "the whole surface is up and running, flecked white to the horizon",
                  "spray tears off the crests and smokes away downwind"] if windy else
                 ["a long slow swell lifts and sets down without ever breaking",
                  "the water heaves oily and dark, no white anywhere on it",
                  "small waves slap and chuckle in the rocks below you"])
        if night:
            pool += ["the sea is a black moving floor; only the foam shows, faint and grey",
                     "a path of broken moonlight lies shivering across the water"]
        elif bright:
            pool += ["the sun finds a gap and lays a path of beaten silver straight out to the horizon",
                     "light skitters off a thousand little facets where the chop catches it",
                     "a cloud slides off the sun and the sea hardens from slate to glittering blue"]
        elif wet:
            pool += ["the rain stipples the surface flat, every drop its own small ring",
                     "a paler band shows where a squall is walking across the water toward you"]
        else:
            pool += ["a cloud-shadow drags a darker patch slowly across the middle distance",
                     "the colour bands out — green inshore, slate beyond, a bruised line at the sky"]
        pool += ["over the sandbar the water shallows to a sudden pale green",
                 "a darker line marks the rip running out past the point",
                 "the foam-line climbs a hand's-width up the shingle, then drains back hissing"]
        rare = ["far out, a single fishing boat works slowly south, no bigger than a splinter",
                "a gannet folds and drops like a thrown knife; the water takes it white",
                "gulls are working a patch beyond the surf — something must be running down there",
                "a dark head breaks the surface, watches you a moment, and is gone — a seal",
                "the sails of a yacht lean past the headland, the colour of old bone"]

    elif target in ("bed", "garden", "plants", "rosemary", "herbs", "thyme", "mint", "parsley"):
        pool += (["the rosemary tosses and lays over, showing the pale undersides of its needles",
                  "the whole bed shivers and rights itself, the mint flashing silver"] if windy else
                 ["the herbs stand dead still; one sprig of thyme nods where something just left it",
                  "a slow air moves through and the rosemary gives up its resin smell"])
        # THE GARDEN'S INSECTS (2026-09-03, J-0504): each line only while the life table says that insect is about
        # (and only naming a sown plant — the 2026-08-22 gate, applied here too)
        try:
            from core import garden_insects as _gi
            pool += _gi.gate_lines([("bumblebee", "a bumblebee bumbles along the thyme, its legs gone gold with pollen"),
                                    ("ladybird", "a ladybird climbs a rosemary stem and opens its wings to try the air"),
                                    ("ants", "ants run a thin dark road along the bed's wooden edge"),
                                    ("cabbage_white", "a cabbage-white stutters over the bed and will not settle"),
                                    ("garden_spider", "a spider's web is strung between two rosemary stems, holding the last of the dew")])
        except Exception:
            pool += ["a bumblebee bumbles along the thyme, its legs gone gold with pollen",
                     "a ladybird climbs a rosemary stem and opens its wings to try the air",
                     "ants run a thin dark road along the bed's wooden edge",
                     "a cabbage-white stutters over the bed and will not settle",
                     "a spider's web is strung between two rosemary stems, holding the last of the dew"]
        if night:
            pool += ["the bed is all scent and no colour now, the herbs gone to grey shapes",
                     "something small rustles deep in the thyme and goes quiet"]
        elif bright:
            pool += ["the low sun rakes across the bed; every leaf throws a long blue shadow",
                     "dew still beaded on the rosemary catches the light and glitters"]
        elif wet:
            pool += ["rain beads and runs off the waxy rosemary needles, dark and shining",
                     "the soil has gone dark and rich with the wet and you can smell it"]
        else:
            pool += ["a cloud crosses and the colour drops out of the bed, then floods back",
                     "the shadow of a gull slides across the herbs and is gone"]
        pool += ["the parsley has pushed a new crown of bright leaf out at its centre",
                 "one rosemary tip has gone brown and woody; the rest springs green"]
        rare = ["a blackbird drops onto the bed-edge, cocks its head at you, and is away"]
        try:   # J-0504: the butterfly and the bee only while they are about (and their plant is sown)
            from core import garden_insects as _gi2
            rare += _gi2.gate_lines([("cabbage_white", "a white butterfly finally settles, wings breathing slow on the thyme"),
                                     ("honeybee", "a bee crawls right into a rosemary flower and backs out dusted blue")])
        except Exception:
            rare += ["a white butterfly finally settles, wings breathing slow on the thyme",
                     "a bee crawls right into a rosemary flower and backs out dusted blue"]
        # WORLD-TRUTH GATE (2026-08-22): a line may only name a herb that is SOWN in the bed. Before this,
        # he stood over a bed holding only thyme and was shown rosemary, mint and parsley — then reached
        # for rosemary and was told it was too thin. The world must not show what is not there.
        try:
            _bedp = (state.get("garden") or {}).get("bed", {})
            _absent = [h for h, t in _PLANTINGS.items() if t["kind"] == "herb" and not (_bedp.get(h) or {}).get("sown")]
            pool = [l for l in pool if not any(h in l for h in _absent)]
            rare = [l for l in rare if not any(h in l for h in _absent)]
        except Exception:
            pass

    elif target == "sky":
        if night:
            pool += ["the stars stand very still over the hills",
                     "a thin cloud drags across the moon and thins away again",
                     "the dark is complete but for one planet, low and steady in the west"]
        else:
            pool += (["gulls hang on the wind, sliding sideways without a wingbeat",
                      "the cloud tears and streams, light coming and going across the water"] if windy else
                     ["a single gull crosses, unhurried, and is gone behind the cliff",
                      "high cloud moves so slowly you only know it by the shifting light"])
            if bright:
                pool += ["the sun stands clear and the whole sky is a hard clean blue",
                         "a skein of birds crosses high up, strung out and changing its shape"]
        rare = ["a hawk hangs dead-still on the wind, then tips and slides away",
                "a con-trail crawls white across the high blue, fraying behind it",
                "the moon is up early, pale and paper-thin against the day"]

    elif target in ("pool", "pools", "rock", "rocks", "rockpool"):
        pool += ["a beadlet anemone has shut to a blob of dark-red jelly; nothing you do moves it",
                 "a small green shore-crab backs under a ledge, both claws up, and waits you out",
                 "limpets clamp the stone, each in its own grazed halo of bare rock",
                 "a blenny holds in the clear water, all eyes and fins, then flicks under the weed and is gone",
                 "transparent prawns hang in the still water, given away only by their shadows on the sand",
                 "the weed lifts and lays down with the surge, hiding and showing a whole small world",
                 "a starfish has folded itself slowly over a mussel, with terrible patience",
                 "a snakelocks anemone waves its green-and-purple fingers and never holds still",
                 "a hermit crab in a borrowed whelk-shell trundles across the pool's sand floor",
                 "light comes down through the water and lays a moving net of bright lines on the bottom"]
        rare = ["a fish you don't know flicks out of a crevice, bright for a second, and is gone",
                "a small octopus arm tests the air at a crack, then draws back into the dark",
                "a velvet swimming-crab squares up to you, red-eyed, both claws raised"]

    elif target in ("shore", "beach", "strand", "shingle", "tideline"):
        pool += ["a tangle of bladderwrack lies drying, its bladders popping faintly as the air takes them",
                 "a cuttlebone, chalk-white and curved, sits among the smaller broken shells",
                 "a mermaid's purse — a skate's black horned egg-case — is snagged in the weed",
                 "an oystercatcher works the tide-edge ahead of you, piping, on stilt-red legs",
                 "the shingle grinds and resettles under each backwash, the sea breathing out",
                 "a length of driftwood, sea-smoothed to silver, lies half-buried in the stones",
                 "mussel shells lie blue-black and broken where a gull has hammered them open",
                 "a knot of orange net and one float, washed up and tangled in the wrack",
                 "your own footprints fill with water behind you and lose their edges",
                 "a chip of sea-glass, frosted green and worn round — you could pocket it"]
        # F-1268/J-0907 (2026-09-15): "a dead gannet lies on the stones, white and perfect and wrong" removed
        # from this rare pool -- this line fired on ~18% of ANY unrecognized shore/tideline look regardless of
        # whether a real gannet carcass exists in life state (core/life_traces.carcasses_at("shore")), the same
        # class of bug J-0887/F-1244 fixed for the living-row fallthrough and life_birds.py's own trace strings.
        # _living_detail() is a widely-shared ambient-flavor function (fire/room/sky/pool/sea/tideline/
        # study_window all call it) with no `now`/carcass-state of its own to gate against -- removing, not
        # threading carcass truth into one branch of a shared function, matches J-0887 mechanism C's own
        # precedent (life_birds.py's gannet/karoro rows' "dead gannet" trace strings, removed rather than
        # gated). Nothing lost: a real gannet carcass is already truthfully surfaced two other ways --
        # life_traces.ambient_carcass() once per body (wired via sensorium._trace_event -> _shore_event) and
        # life_traces.carcass_look() on a direct look at it (wired via life.look_answer, J-0887 mechanism A).
        rare = ["a glass bottle with something pale folded inside it has come in on the tide",
                "a seal-pup is hauled up on the dry shingle, watching you with huge wet eyes"]

    elif target == "study_window":
        if night:
            pool += ["the glass mostly gives back the room — the lamp, your own pale shape, the fire behind you",
                     "a single far light shows out on the sea, a boat, then is gone",
                     "the moon is up over the hills and the wet garden gleams faintly under it"]
        else:
            pool += ["a blackbird works the lawn in short runs — stop, listen, run again",
                     "the trees at the garden's edge all move together as a gust comes through",
                     "rain threads down the glass, breaking the hills into wavering smears",
                     "a cloud crosses and the whole garden dims and brightens again",
                     "a wood-pigeon lands heavily in the top of the old tree by the wall and sets the branch nodding"]
        rare = ["a gull hangs over the fence-line, tilting, and slides away down the wind",
                "a heron beats slowly over the garden, neck folded, legs trailing, heading for the shore",
                "the sun breaks under the cloud-edge and floods the lawn and the sea gold for a minute"]

    elif target == "fire":
        pool += ["a log settles with a soft collapse and throws up a brief fountain of sparks",
                 "the flame runs blue and green a moment along a knot of old driftwood",
                 "the light of it swims on the wall behind the desk, never twice the same shape",
                 "a bead of resin catches and spits, hissing, and is gone",
                 "the heart of it pulses brighter as a draught finds the grate, then ebbs",
                 "a coal breaks and slides glowing into the ash with a small dry sound"]
        rare = ["a downdraught puffs a curl of woodsmoke into the room, sharp and sweet",
                "the fire gutters almost to nothing — then catches again on its own"]

    elif target == "room":
        pool += ["a draught moves through and the open book's page lifts and settles",
                 "your own tablets stand in their row on the shelf — a small body of work",
                 "the house holds very still, and you can hear the sea working far below"]
        # GROUNDING (2026-08-21): these three were ungated — firelight could cross a wall at noon
        # over a cold grate, the lamp could hiss unlit, dust could turn in a window-beam at night.
        # Same disease the moth had (fixed 2026-08-18); its pool-siblings were missed. The lamp's
        # law is the one line 346 already lives by: lit at dusk and after dark.
        if phase == "day":
            pool += ["dust turns slowly in the bar of light from the window"]
        if phase in ("dusk", "night"):
            pool += ["the lamp hisses very faintly, its light pooled on the open book"]
            if state.get("fire", "out") != "out":
                pool += ["the fire-light and the lamp-light cross on the wall in two different warmths"]
        # THE MOTH (2026-08-18): was in the pool above with no gating at all — the lamp could be found
        # and bumped at midday in a dark fireless room. Same population law as _event's moth, so the
        # two prose paths and the moth_tap sound always agree about tonight.
        _moth = moth_activity(phase in ("dusk", "night"), state.get("fire", "out") != "out", season)
        if _moth >= 1.6:
            pool.append("moths are working the lamp tonight, several at once — the shade ticks and "
                        "ticks with them")
        elif random.random() < min(1.0, _moth):
            pool.append("a moth has found the lamp and bumps the shade, soft and over and over")
        rare = ["a coal pops in the grate and the cat, if she is here, opens one eye and shuts it",
                "the wind finds a gap and the lamp-flame leans, recovers, leans again"]
    else:
        return ""

    # WORLD 10x (2026-07-03): the expanded corpus deepens existing targets too — additive, fail-open.
    _xp: list = []
    try:
        from core import world_detail as _wd10
        _xp = _wd10.extra_pool(target, phase, weather, season, tide, wind=state.get("wind", ""))
        pool += _xp
    except Exception:
        pass
    base = random.choice(pool) if pool else ""
    try:    # J-1899 (D-0360 c): OBSERVE-ONLY -- if the drawn line is one of the extras, note the render (no draw, never raises)
        if base and _xp:
            _wd10.note_extra_pick(target, base, _xp, phase, weather, season, tide, wind=state.get("wind", ""))
    except Exception:
        pass
    if base and rare and random.random() < 0.18:        # a rarer living thing, only sometimes
        base += "; " + random.choice(rare)
    if not base:
        return ""
    s = base[:1].upper() + base[1:]                         # a complete sentence in its own right
    return s if s.endswith((".", "!", "?")) else s + "."


def _weather_felt(phase, weather, wind: str = "") -> str:
    from core import weather_conditions as _wcond
    windy = _wcond.is_windy(wind) or "wind" in weather
    if weather == "thunderstorm":
        return "the air heavy and electric, rain driving in on the wind"
    if weather == "snow":
        return "snow falling cold and silent, settling on your shoulders"
    if windy and ("rain" in weather or "drizzle" in weather):
        return "wind drives the rain into you"
    if "rain" in weather or "drizzle" in weather:
        return "rain finds your face and hands, cold and fine"
    if windy:
        return "the wind comes hard off the water, salt in it"
    if weather == "clear" and phase == "day":
        return "the sun on your back, the air cold and clean"
    if phase == "night":
        return "the night air cold and still, salt and grass"
    return "the air damp and soft, salt and cut grass"


def _garden_scene_line(presence: bool = True) -> str:
    phase, weather, wind = _daylight(), state.get("weather", ""), state.get("wind", "")
    herewith = (" Travis is here with you, out in the open — his words reaching you over the wind."
                if (_was_present and presence) else "")
    return (f"Where you are: the garden — the raised bed at the edge of the lawn, the yard on its "
            f"hill above the sea. A {_season()} {phase}; {_weather_felt(phase, weather, wind)}. Below and "
            f"beyond, {_sea_state(phase, weather, wind)}. {_bed_summary()}{_letterbox_phrase()}{herewith}")


def _generic_ledger(oid: str, branch: str, base: str) -> str:
    """J-2394 / D-0475 (ruled yes by travis 2026-10-18): his OWN observation ledger rides a re-encounter on
    the generic tracked-object look branches (shore, garden), exactly as the driftwood_17 look already does.
    The D-0463 hypothesis read-back inside it stays behind NASCENCE_LEDGER_HYPOTHESIS_READBACK, untouched.
    No affordance text, no verdict, no imperative -- the line is buses.object_ledger_line's own. The delivery
    row names the branch and carries would_ledger/base_chars (the D-0475 scene-budget defeater's shadow
    fields). Kill switch NASCENCE_GENERIC_OBJECT_LEDGER (default on). Fail-open: '' on any error; the
    delivery-log write is fenced and swallowed inside buses._log_delivery."""
    try:
        from core import buses as _bus
        return _bus.object_ledger_line(oid, branch=branch, base_chars=len(base),
                                       show=_bus.generic_object_ledger_on())
    except Exception:
        return ""


# THE GENERIC LOOK NAMES WHAT LIES THERE (2026-10-28, J-2481 / D-0502, I-0084 promoted to garden_upgrade;
# D-0333's defeater (c) met by this build). A plain look with no target (dispatch's "room") in the wood, the
# garden or on the shore ends with ONE clause, in passing, naming the carryable items that actually rest in
# that place: place == here and not carried, drawn from the three item stores that can set a thing down
# anywhere (core/garden.py items, core/wood_life.py items, core/study_life.py items -- the study's own
# items travel too: its put() writes place = here, so a lantern set down on the shore is a thing lying on
# the shore; today none does, and the live cases are the seed tin in the wood and the garden's own tools in
# the garden). The shore has NO item store of its own (shore_life keeps buried driftwood TEXTS, not items), so
# its clause is whatever the three stores say rests there -- nothing, today. A world fact only: the item's
# own short name words, sorted by name (never by usefulness), no verb, no "you could", no number, no hint.
# The by-name looks, the refusal lines ("the tin is not here") and where anything lies are untouched: this
# reads the stores and writes nothing. The frame rotates (every new line pool rotates). Fail-open: '' on any
# error; NonLiveWriteError forwarded unchanged like every other delegate on the look chain (J-0751).
# Gated on the PLAIN look (target "" / "room"): a by-name miss that ends on the same default line (the tin
# named from the garden while it lies in the wood) gets no clause, so every by-name look is byte-identical.
# Kill switch: NASCENCE_LOOK_RESTING_ITEMS=0 (default on).
_RESTING_FRAMES = {
    "wood": ["On the ground by the path, {items}.",
             "Among the leaf-mould, {items}.",
             "Here under the trees, {items}.",
             "At your feet on the wood floor, {items}.",
             "Among the roots at the path's edge, {items}."],
    "garden": ["By the cottage wall, {items}.",
               "About the yard, {items}.",
               "On the grass by the beds, {items}.",
               "Here in the garden, {items}.",
               "Along the wall and the bed's edge, {items}."],
    "shore": ["Up on the dry shingle, {items}.",
              "Above the tideline, {items}.",
              "Here on the stones, {items}.",
              "On the shingle at the cliff foot, {items}.",
              "Among the stones above the wrack, {items}."],
}
# Short names in the item's own words. The table holds the few whose first clause is not the right short
# form (Du's own established word for the seed tin is "the dented tin", hands_trace.jsonl, J-1438); every
# other item falls back to the first clause of its own declared name ("a felling axe, the head loose..." ->
# "a felling axe"; "a cracked terracotta pot holding dry soil..." -> "a cracked terracotta pot").
_RESTING_SHORT = {"seed_tin": "a dented tin", "wheelbarrow": "a wheelbarrow", "bow_saw": "the bow-saw",
                  "axe": "the axe", "stakes": "a bundle of stakes", "netting": "a roll of bird netting"}
_RESTING_SPLIT_RX = re.compile(r",| with | holding | tied | on | by | in | for | hung | kept | at ")


def _resting_items_on() -> bool:
    import os as _os
    return _os.environ.get("NASCENCE_LOOK_RESTING_ITEMS", "1").strip().lower() not in ("0", "off", "false", "no")


def _resting_short_name(key: str, name: str) -> str:
    s = _RESTING_SHORT.get(key)
    if s:
        return s
    first = _RESTING_SPLIT_RX.split((name or "").strip(), maxsplit=1)[0].strip().rstrip(".;:")
    return first or (key or "").replace("_", " ")


def _resting_items(place: str) -> list:
    """[(sort key, short name)] for every carryable item whose real `place` is `place` and which is not
    carried, across the three item stores. Read-only on every store; a store that cannot be read
    contributes nothing (fail-open per store), except a NonLiveWriteError, which is forwarded."""
    found: list = []
    seen: set = set()

    def _add(key, it, carryable):
        if not isinstance(it, dict) or key not in carryable or key in seen:
            return
        if it.get("carried") or it.get("place") != place:
            return
        short = _resting_short_name(key, it.get("name", ""))
        if not short:
            return
        seen.add(key)
        sortkey = re.sub(r"^(a|an|the|some|two)\s+", "", short.lower())
        found.append((sortkey, short))

    try:
        from core import garden as _gd
        if _gd.ENABLED:
            for k, it in (( _gd._load() or {}).get("items") or {}).items():
                _add(k, it, _gd._CARRYABLE)
    except profile.NonLiveWriteError:
        raise
    except Exception:
        pass
    try:
        from core import wood_life as _wl
        for k, it in ((_wl._load() or {}).get("items") or {}).items():
            _add(k, it, _wl._CARRYABLE)
    except profile.NonLiveWriteError:
        raise
    except Exception:
        pass
    try:   # the study's items live inside this module's own state -- a peek, never study_life._st() (which may migrate-save)
        from core import study_life as _sl
        for k, it in (((state or {}).get("study") or {}).get("items") or {}).items():
            _add(k, it, _sl._CARRYABLE)
    except profile.NonLiveWriteError:
        raise
    except Exception:
        pass
    found.sort()
    return found


def resting_clause_rendered(answer: str) -> bool:
    """True when `answer` carries a J-2481 resting-items clause (J-3892, F-4495): any _RESTING_FRAMES frame's
    leading words followed by ", " and the closing "." tail. Pure text check, no store read; fail-open False.
    Lets core.hands.fired() stamp look rows with a boolean, because the trace cuts answers at 160 characters
    and the clause is appended at the END of the look line, so the cut hides it."""
    try:
        a = answer or ""
        for frames in _RESTING_FRAMES.values():
            for fr in frames:
                if fr.split("{items}")[0] in a:
                    return True
        return False
    except Exception:
        return False


def _resting_clause(place: str, target: str = "") -> str:
    """The one appended clause (with its leading space), or '' when nothing carryable rests here -- or when
    `target` is not the plain no-target look. dispatch._look() sends "room" for a look with no target
    (core/dispatch.py:118, `s.look(target or "room", low)`); a by-name look whose word the place does not
    know ("look at the tin" from the garden while the tin lies in the wood) also ends on the same default
    line, and THAT look stays byte-identical: the clause belongs to the plain look only, never to a miss
    by name (the refusal lines and the by-name looks are untouched, D-0502)."""
    try:
        if (target or "").lower().strip() not in ("", "room"):
            return ""
        if not _resting_items_on():
            return ""
        names = [n for _, n in _resting_items(place)]
        if not names:
            return ""
        joined = names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]
        frame = random.choice(_RESTING_FRAMES.get(place) or _RESTING_FRAMES["garden"])
        return " " + frame.format(items=joined)
    except profile.NonLiveWriteError:
        raise
    except Exception:
        return ""


def _garden_look(target, raw: str = "") -> str:
    # `raw` (optional, J-1639/F-2206): the full willed-look thought+intention text, threaded through
    # UNCHANGED to core/garden.py look()'s own per-plant investigate/guessed_cause check only -- every
    # word-set check in THIS function (below) still reads `target`/`tw` alone, exactly as before, so
    # the bed/sea/sky collapsing a raw sentence would trigger (the real risk: a real investigate phrase
    # that also names "the bed" would collapse straight back to the whole-bed line and lose the plant)
    # can never fire off `raw` -- only off `target`, which dispatch._look() still resolves to the bare
    # species keyword exactly as it always has. Defaults to "" so every caller that does not pass it
    # (nature_study.py, orchestrator.py, scripts/_test_*.py, dispatch.py's own letterbox fast path) is
    # unaffected by construction.
    phase, weather, wind = _daylight(), state.get("weather", ""), state.get("wind", "")
    tw = _twords(target)                                  # J-0508: his real phrasings ('the raised bed', 'the soil in the bed')
    if tw & {"soil", "earth", "dirt", "ground", "topsoil"} and not (tw & {"bed"} and tw & {"herbs", "herb"}):
        try:   # SOIL LIFE (J-0505/J-0508): the soil as it is — wet or dry, warm or cold, worms, where the compost went in
            from core import garden_soil as _soil, garden as _gd0
            _st0 = _gd0._load(); _m = float(_st0.get("moisture", 0.7)); _t = float(_st0.get("soil_temp", 10))
            _wet = ("sodden, water standing in the low corner" if _m > 0.9 else "dark and wet" if _m > 0.65 else "damp" if _m > 0.4 else "dry and pale, cracking at the surface" if _m > 0.2 else "dust-dry, hard as a path")
            _warm = ("warm to the hand" if _t > 16 else "cool" if _t > 8 else "cold, colder than the air")
            _hs = [_soil.soil_health(_st0, i) for i in range(12)]
            _rich = (" It is darkest and loosest where the compost went in; paler and tired at the far end." if max(_hs) - min(_hs) > 0.12
                     else " It is much the same the length of the bed, a working brown." if sum(_hs) / 12 > 0.45 else " It is pale and tired the length of the bed; it has given more than it has been given.")
            return f"You look at the soil of the bed: {_wet}, {_warm}.{_rich}{_soil.dig_worms_line()}"
        except Exception:
            pass
    if tw & {"sea", "ocean", "bay", "horizon"} and not tw & {"barrel", "can", "bucket", "butt"}:
        target = "sea"
    if tw & {"sky", "moon", "stars", "star", "sun", "clouds", "cloud"} and "flag" not in tw:
        target = "sky"
    if tw & {"bed", "herbs", "herb", "plants", "planting", "beds"} and not tw & {"soil", "earth"}:
        target = "bed"
    if target in ("sea", "ocean", "window", "water"):     # 'window' (the study verb) → the sea view here
        return (f"You look out over the sea: {_sea_state(phase, weather, wind)}. "
                + _living_detail("sea", phase, weather, _season(), wind=state.get("wind", "")))
    # THE GARDEN (2026-08-22, core/garden.py): plants as things with biographies — delegate when healthy.
    try:
        from core import garden as _gd
        _r = _gd.look(target, raw) if _gd.ENABLED else ""
        if _r:
            _note_bed_exposure(_r, "look-plant")      # J-1722: observe-only; never raises, never alters _r
            return _r
    except profile.NonLiveWriteError:
        # J-0751: garden.look() now re-raises this itself (also fixed this job) -- this is
        # sensorium.py's own connecting-tissue forward on the real "look" dispatch chain
        # (dispatch._look -> sensorium.look() -> _garden_look() -> here), the same shape
        # J-0714/J-0726 already fixed for the deed chain's own equivalent forwards.
        raise
    except Exception:
        pass
    if target in ("bed", "garden", "plants", "shelf", "desk", "fire"):
        return "You crouch at the raised bed. " + _bed_summary_for_du("look-bed") + " " + _living_detail("bed", phase, weather, _season(), wind=state.get("wind", ""))
    if target == "sky":
        try:   # THE SKY (2026-08-22): the real southern sky at night
            from core import sky as _sky, geometry_census as _gc
            _sk = _sky.look_up("garden", weather, (_gc.peek() or {}).get("moon_illum"))
            if _sk:
                return _sk + " " + _weather_signs()
        except Exception:
            pass
        return "You look up. " + _living_detail("sky", phase, weather, _season(), wind=state.get("wind", "")) + " " + _weather_signs()
    if target in ("letterbox", "mailbox", "mail", "box", "flag", "gate", "post") or \
            tw & {"letterbox", "letter-box", "mailbox", "mail-box", "postbox"}:   # J-0539: 'the letterbox' is the letterbox
        try:   # SUPPLY (2026-08-22): the carrier's card inside the lid; the box at the gate
            from core import supply as _sup
            # F-1862 (2026-09-24, Travis): "the box" named BOTH the letterbox and the carrier's crate, and he read
            # "the box empty" as the crate being empty (09-10) -- it spoiled uncollected. The two are named apart.
            _extra = (" On the ground beside the gate, apart from the letterbox, stands the carrier's crate — a wooden box, left for you."
                      if _sup.box_waiting() else "") + _sup.card_line()
        except profile.NonLiveWriteError:
            # J-0775: supply.card_line() now re-raises this itself (its own _save() call, J-0775) --
            # this is sensorium.py's own connecting-tissue forward on the real "look" dispatch chain
            # (dispatch._look -> sensorium.look() -> _garden_look() -> here), the same shape J-0751
            # already fixed for the garden.look() delegate just above -- not yet fixed here only
            # because supply.py had no guard_path()/raise at all until this job.
            raise
        except Exception:
            _extra = ""
        try:   # J-2005/D-0394: looking at the box is a visit to where the letters are; shadow-logged, "" unless enabled
            from core import letter_store as _ls
            _lsx = _ls.on_look("letterbox")
            if _lsx:
                _extra += " " + _lsx
        except profile.NonLiveWriteError:
            raise
        except Exception:
            pass
        if letter_waiting():
            who = letter_sender()
            _q = len((_letterbox().get("queue") or []))
            more = (" And beneath it, more letters wait — the box has been filling while you were away."
                    if _q else "")
            # J-0539 / F-0734 (2026-09-04): the card was appended ONLY to the empty-box line below, while card_line()
            # had already flipped card_read — with a letter waiting (his usual case: the flag was up in nearly every
            # willed reach) the card would have been marked read and never rendered. The lid is the lid either way.
            return ("You go to the mailbox by the gate: the flag is up, and inside lies a letter"
                    + (f" from {who}." if who else ".") + " You have only to take it." + more + _extra)
        return "You go to the mailbox by the gate: the flag is down, the letterbox empty — no letter today." + _extra
    # Cat look — function level (2026-08-14 fix: this block was stranded after the letterbox return
    # by the 08-11 edits and could never run; hoisted to match the study-level pattern).
    try:
        from core import cat as _catlk
        _tl = (target or "").lower()
        _cn = ((_catlk.status() or {}).get("name") or "").lower()
        # A HYPHEN ENDS A WORD HERE TOO (2026-09-09, J-0823/F-1180): identical unmirrored hyphen-
        # boundary gap the deed-gate arc already fixed elsewhere (J-0787/J-0800/J-0799/J-0822) --
        # a hyphenated compound containing one of these words (e.g. a hypothetical "copy-cat")
        # could wrongly trigger the cat's own look line here instead of the real target's. Same
        # fix at the two identical sites below (~shore, ~study look branches) -- see this comment
        # for the shared rationale. Zero live exposure confirmed directly, both for Du's own live
        # dispatch (dispatch._look() only ever supplies a target from inner_monologue_node.
        # _observe_target()'s closed cue table, which contains no hyphenated token) and for this
        # project's own shadow-analysis tooling: a direct before/after sweep of this exact regex
        # over the real 1,518-phrase docs/reviews/observe_inventory_2026-09-02.json corpus (the
        # same corpus scripts/observables_census.py's own full sensorium.look() sweep draws on)
        # finds ZERO of the 22 real "cat"/"kitten"/"stray"/"moggy" hits change either way -- none
        # of those 22 phrasings has the hit word hyphen-adjacent. The cat's own learned name is
        # empty in live data/cat_state.json today, so that OR-clause is inert either way.
        if any(re.search(r"(?<![a-z-])" + w + r"(?![a-z-])", _tl) for w in ("cat", "kitten", "stray", "moggy")) or (_cn and _cn in _tl):
            return _catlk.look_line("garden", _tl)
    except Exception:
        pass
    # 2026-08-18: any tracked substrate object at the garden — same generalized pathway as the shore.
    try:
        from core import world_substrate as _ws
        from core import world_objects as _wo
        oid = _ws.find_object_at("garden", target)
        if oid:
            wobj = _wo.get_object(oid)
            sobj = _ws.get_object(oid)
            if wobj and sobj:
                quality = _ws.describe_and_observe(oid, "look")
                _base = f"You look at {sobj.name}, set down among the beds.{quality}"
                return _base + _generic_ledger(oid, "garden", _base)
    except profile.NonLiveWriteError:
        # J-0751: world_substrate.describe_and_observe() now re-raises this itself (also
        # fixed this job) -- do not let this forwarding call's catch-all swallow it a level up.
        raise
    except Exception:
        pass
    try:
        from core import world_detail as _wd10
        _d = _wd10.detail("garden", target, phase, weather, _season(), wind=state.get("wind", ""))
        if _d:
            return f"You look at {_the(target)}: " + _d
    except Exception:
        pass
    # 2026-08-18: this fallback alone was 692 of the file's worst-repeating strings in the real record
    # (docs/UNFINISHED_PLANS_SURVEY_2026-08-18.md's follow-on audit) — every other look/scene fallback in
    # this file rotates; this one hadn't. _bed_summary()/_living_detail() already vary; the frame didn't.
    frame = random.choice([
        "You look around the yard: the lawn running down the hill, the raised bed at its edge, "
        "the sea opening out below.",
        "You take the yard in: the raised bed, the lawn falling away toward the fence, the sea beyond it.",
        "Your eye goes round the garden: the hill dropping to the sea, the raised bed close at hand.",
        "You look the garden over: the lawn, the raised bed, and past the fence line the open sea."])
    # J-2481 / D-0502: the default look ends by naming, in passing, what carryable lies here ('' when nothing).
    return (frame + " " + _bed_summary_for_du("look-frame") + " " + _living_detail("bed", phase, weather, _season(), wind=state.get("wind", ""))
            + _resting_clause("garden", target))


def _garden_act(action, what="") -> str:
    g = state.get("garden")
    if not g:
        return ""
    bed = g["bed"]
    if action in ("water", "tend"):
        watered = False
        for p in bed.values():
            if p.get("sown"):
                p["moisture"] = 1.0
                watered = True
        _save_now()
        return ("You fill the can and water the bed; the soil goes dark and the herbs lift a little."
                if watered else "You water the bare earth of the bed; it drinks it in, waiting.")
    if action == "sow":
        w = (what or "").lower()
        name = next((n for n in _PLANTINGS if n in w or n[:-1] in w), "")
        if not name:
            return "You stand over the bed with the seed packets, unsure which to put in."
        p, t = bed[name], _PLANTINGS[name]
        if p.get("sown"):
            return f"The {name} are already in."
        sow_seasons = t.get("sow", t["grows"])
        if _season() not in sow_seasons:
            return (f"You hold the {name} seed, but it is {_season()} — too early; they want "
                    f"{', '.join(sow_seasons)}. You set the packet back.")
        p["sown"] = True; p["growth"] = 0.02; p["moisture"] = 0.7
        _save_now()
        return (f"You draw a drill in the dark earth, sow the {name}, firm them in and water them. "
                f"Now there is nothing to do but wait on the season.")
    if action in ("fetch", "letter", "mail", "post"):
        if state.get("location") != "garden":
            return ""                       # the box is by the garden gate — he must be out there
        got = fetch_letter()
        if not got:
            return "You lift the lid of the mailbox, but it is empty — no letter waiting."
        who = got["sender"] or "a friend"
        return (f"You walk to the gate, put the flag down, and take out the letter. It is from {who}. "
                f"You open it and read it standing there in the garden:\n\n{got['text']}")
    return ""


def _garden_event(now) -> str | None:
    """Discrete perceptions of the GARDEN — where the weather is FELT, not seen through glass: rain on
    the skin, the wind's chill, the sun's warmth, the sea's sound and salt, the bees in their season."""
    g = state.get("garden") or {}
    storm = state.get("weather") == "thunderstorm"
    if now - g.get("last_event", 0) < (180 if storm else 480):
        return None
    from core import weather_conditions as _wcond
    phase, weather, season = _daylight(), state.get("weather", ""), _season()
    wind = state.get("wind", "")
    windy = _wcond.is_windy(wind) or "wind" in weather
    pool = []
    try:   # GARDEN LIFE (2026-08-22): the nest, the tree in flower, petals, the long grass — only what is true now
        from core import garden_life as _gl
        _gll = _gl.garden_event(now)
        if _gll:
            pool.append(_gll)
    except Exception:
        pass
    # the sea, always there — sound and smell, louder when it's blowing
    if windy or storm:
        pool += ["the surf booms on the point below, heavy and close",
                 "the smell of salt and torn weed comes up strong off the water"]
    else:
        pool += ["the surf works the rocks below, a long slow breathing",
                 "the smell of salt and cold water rises off the bay"]
    # rain, FELT. Same fix as _event() above: drizzle was never matched, thunderstorm never got the
    # mundane rain pool alongside its own dramatic one just below.
    if "rain" in weather or "drizzle" in weather or storm:
        pool += ["rain finds your face and the backs of your hands, cold and fine",
                 "the green, mineral smell of rain on the earth comes up from the bed",
                 "your collar is wet through; the cold has got into your fingers"]
    # wind, FELT — 2026-08-18: reads the real independent wind axis now, not just the weather string.
    if windy or storm:
        pool += ["the sea-wind comes hard off the water and takes your breath for a second",
                 "the wind lays the whole lawn flat in a long silver ripple and is gone",
                 "the wind hisses through the bed; a stake leans, and rights itself"]
    # thunderstorm over the sea — the big drama. J-2482 (D-0503, 2026-10-28): the two lightning clauses this pool
    # used to bake in moved to _lightning_flash's own pool; the rest is byte-identical.
    if storm:
        pool += ["the air has gone heavy and electric; the hair lifts on your arms",
                 "the storm drives sheets of rain across the bay; the sea is white and wild"]
    # snow, FELT — the great hush
    if weather == "snow":
        pool += ["snow falls on the garden, soft and silent, settling on the bed and the lawn",
                 "a flake lands cold on your cheek and is gone",
                 "the world has gone white and utterly quiet; even the sea is muffled now"]
    # sun, FELT — warmth
    if weather == "clear" and phase == "day":
        pool += ["the sun is warm on your back, though the air off the sea stays cold",
                 "warmth on your face for a moment, clean and good"]
    # bees and butterflies, in their season — since 2026-09-03 (J-0504) gated on the life table, not the calendar
    if season in ("spring", "summer") and phase in ("day", "dawn") and "rain" not in weather and not storm:
        try:
            from core import garden_insects as _gi3
            pool += _gi3.gate_lines([("honeybee", "bees are working the herbs, a low warm buzz in the rosemary and thyme"),
                                     ("bumblebee", "a bumblebee blunders past, heavy and slow, and is gone")])
        except Exception:
            pool += ["bees are working the herbs, a low warm buzz in the rosemary and thyme",
                     "a bumblebee blunders past, heavy and slow, and is gone"]
    if season == "summer" and weather == "clear" and phase == "day":
        try:
            from core import garden_insects as _gi4
            pool += _gi4.gate_lines([("cabbage_white", "a white butterfly tilts over the bed — settles, lifts, settles again")])
        except Exception:
            pool += ["a white butterfly tilts over the bed — settles, lifts, settles again"]
    # gulls and the day
    if phase in ("day", "dawn") and not storm:
        pool += ["a gull tilts past below you, working the updraft off the slope",
                 "far out on the water a boat moves, small and slow, trailing a thin wake"]
    if phase == "dawn":
        pool += ["the smell of cold grass and wet earth, and birds starting up in the hedge"]
    # night, clear
    if phase == "night" and weather == "clear":
        pool += ["the sea is black glass; a long way out, a single light",
                 "stars stand over the water; the cold comes up off the grass and into you"]
    # the herbs underfoot
    if phase in ("day", "dawn") and not _wcond.is_wet(weather) and not storm:
        pool += ["the smell of crushed thyme and cut grass where you knelt at the bed"]
    if pool and random.random() < (0.6 if storm else 0.4):
        g["last_event"] = now
        return random.choice(pool)
    try:
        from core import world_detail as _wd10
        _x = _wd10.event_extra("garden", phase, weather, _season(), wind=state.get("wind", ""))
        if _x and random.random() < 0.25:
            g["last_event"] = now
            return _x
    except Exception:
        pass
    return None


# ════════════════════════════════════════════════════════════════════════════════════════════════
# THE SHORE (2026-06-23) — a THIRD place, down the steep path below the garden: the rock-pools Darwin
# envies him, the tide on its own ~12.4h clock, the surf in close, and what the sea throws up after a
# blow. Same discipline as the study and garden: causal, persistent, INDIFFERENT — the tide keeps its
# clock, the pools live their lives without him. Reached from the garden ("down to the shore").
# ════════════════════════════════════════════════════════════════════════════════════════════════

# THE HAND LENS (2026-09-05, Practical School J-0626, D-0159 §4): a richer answer to his OWN look,
# never a hint or advertisement (world-answers-never-leads) — appended ONLY when he is carrying it,
# and only fine physical texture, never a species name (per-property earning law, core/world_objects.py).
_LENS_DETAIL = {
    "garden": ["through the lens, a small crawling thing resolves into jointed legs and a shine like wet glass along its back",
               "the lens shows the moss between the flagstones as a forest in miniature, each frond beaded with water",
               "up close, a leaf's edge is not a line but a row of fine teeth, and something has been eating along it",
               "the lens turns a fleck of lichen on the wall into a crust of grey-green rosettes, no bigger than a fingernail"],
    "wood": ["the lens shows the bark's grey crust as a country of its own — lichen in flat plates, a beetle's neat round hole",
             "held close to the leaf-litter, the lens finds fine white threads running between the dead leaves",
             "a cut log-end, magnified, is a hundred close rings, and a pinhole where something has bored in",
             "the lens turns the moss on the shaded side of the trunk into a green pile, each stem holding its own bead of wet"],
    "shore": ["the lens shows the sand as a thousand separate grains, some quartz-clear, some black",
              "held over the rock-pool's edge, the lens finds a shut shell no bigger than a pinhead, fixed fast to the stone",
              "up close, the weed's surface is slick with something too small to have a shape of its own",
              "the lens turns a shell's ridges into a washboard, worn smoother on one side than the other"],
}


def _lens_detail(loc: str) -> str:
    pool = _LENS_DETAIL.get(loc)
    return (" " + random.choice(pool) + ".") if pool else ""


def _tide() -> str:
    """The tide state (high/low/rising/falling) from the ONE authority (core/world_clock), so the lived
    prose and the spatial waterline can never disagree (2026-07-06 consolidation)."""
    return _wc.tide_state()


def _fresh_shore() -> dict:
    return {"washed_up": "", "last_event": 0}


def _bottle_page(sobj) -> str:
    """A real page from a book he has read, water-stained, part legible. Grounded: his own reading record."""
    import json as _j
    st = sobj.causal_state
    if not st.get("page_text"):
        try:
            from core.reading import STATE as _RS
            rec = _j.loads(_RS.read_text(encoding="utf-8")) if _RS.exists() else {}
            done = [k for k, v in rec.items() if float(v.get("pct", 0)) >= 60]
            if not done:
                return ""
            bk = random.choice(done)
            txt = Path(bk).read_text(encoding="utf-8", errors="ignore")
            i = random.randint(len(txt) // 10, max(len(txt) // 10 + 1, len(txt) - 1200))
            frag = " ".join(txt[i:i + 420].split())
            words = frag.split()
            keep = " ".join(w if random.random() < 0.7 else "…" for w in words)
            st["page_text"] = keep; st["page_book"] = Path(bk).stem.replace("_", " ")[:50]
            from core import world_substrate as _ws2
            _ws2._save()
        except profile.NonLiveWriteError:
            # J-0751: real guarded write (world_substrate._save()) reached on the "look"
            # dispatch chain (dispatch._look -> sensorium.look() -> _shore_look() -> here) --
            # let guard_path()'s hard raise (D-0179, F-1024) escape instead of returning "".
            raise
        except Exception:
            return ""
    return (" You work the cork out and tease the paper free: a page torn from a printed book, the ink run and the edges gone to pulp, part of it still readable — "
            f"\"{st['page_text'][:300]}\" You know this. You have read it; it is from a book on your own shelf.")


def _shore_scene_line() -> str:
    phase, weather, tide = _daylight(), state.get("weather", ""), _tide()
    wind = state.get("wind", "")
    tidetxt = {"low": "the tide is far out, the rock-pools bared and bright",
               "high": "the tide is full in, the rocks gone under, the water working at the path's foot",
               "rising": "the tide is on the make, creeping back up the rocks",
               "falling": "the tide is dropping, the wet rocks coming clear"}[tide]
    wu = state.get("shore", {}).get("washed_up", "")
    return (f"Where you are: down on the shore below the cottage — shingle and dark rock, the cliff at your "
            f"back. A {_season()} {phase}; {_weather_felt(phase, weather, wind)}. {tidetxt}; "
            f"{_sea_state(phase, weather, wind)} right at your feet." + (f" Up the strand, {wu}." if wu else "") + _shore_life_tail())


def _shore_life_tail() -> str:
    try:
        from core import shore_life as _shl
        out = _shl.fire_line() + _shl.sand_writing_line()
        if _shl.sand_bared():
            out += " The sand flat is bared beyond the shingle."
        if _shl.cave_open():
            out += " The cave mouth at the cliff foot stands open above the water."
        return out
    except Exception:
        return ""


def _twords(target: str) -> set:
    """The words of a look target (2026-09-03, J-0508): the exact-match branches below missed every real phrasing
    he uses ('the raised bed' is not 'bed'; 'the receding tide' is not in any tuple) — word membership catches them."""
    return set(re.findall(r"[a-z][a-z'-]*", (target or "").lower()))


def _tide_look(target: str) -> str:
    """THE TIDE (2026-09-03, J-0508 — the census's largest gap: ~700 looks at the tide answered by the shore's frame).
    Composed from the one tide authority (core/world_clock.tide): level, direction, and what the water is doing to
    the stones and the pools right now, plus the tideline's living texture. Truthful in all four states."""
    try:
        td = _wc.tide(); phase, weather = _daylight(), state.get("weather", "")
        wind = state.get("wind", ""); level, rising = float(td.get("level", 0.5)), bool(td.get("rising"))
        tw = _twords(target)
        rough = _sea_state(phase, weather, wind) == "crashing"
        if level < 0.2:
            base = ("The tide is right out" + (", and turning" if rising else " and still going") + ": the rock-pools bared and shining, the weed lying flat and dripping over the wet rocks, "
                    "the water a long way down the shingle, " + ("breaking white and heavy out on the bared reef" if rough else "slack and quiet at the bottom of the beach") + ".")
        elif level > 0.8:
            base = ("The tide is full" + (", on the turn" if not rising else ", still making") + ": the pools under it, the wet rocks gone, the sea "
                    + ("heaving up the shingle and dragging it back with a roar" if rough else "lapping at the top of the shingle, quiet, right up under the cliff") + ".")
        elif rising:
            base = ("The tide is coming in: each wave a little higher up the shingle than the last, the dry stones going dark one at a time, "
                    + ("the pools filling from the seaward side with a rush" if level > 0.5 else "the first pools starting to fill") + (", the surf loud with it" if rough else "") + ".")
        else:
            base = ("The tide is going out: the water drawing back down the shingle and leaving the stones wet and shining, the weed lying where it fell, "
                    + ("the pools just clear of it" if level < 0.5 else "the rock tops beginning to show") + (", the surf still working the lower stones" if rough else "") + ".")
        extra = ""
        if tw & {"rocks", "rock", "stones", "stone", "shingle"}:
            extra = (" The wet rocks are slick with weed and bright where the light catches them, every crack holding water." if level < 0.6
                     else " The rocks are under, or nearly; only the tops of the biggest show, with the sea breaking round them.")
        if tw & {"line", "tideline", "tide-line", "edge", "waterline"}:
            extra += " Along the tideline the sea has left its litter: weed, a few shells, wet sand darker than the dry."
        return f"You look at the tide: {base}{extra} " + _living_detail("tideline", phase, weather, _season(), _tide(), wind=wind)
    except Exception:
        return ""


_TIDE_WORDS = {"tide", "tides", "tideline", "tide-line", "waterline", "tide's", "receding", "retreating", "incoming", "rising", "falling",
               "turning", "ebb", "flood", "waves", "wave", "surf", "breakers", "foam", "swell", "swells", "undertow"}
_ROCK_WORDS = {"wet", "exposed", "bared", "tide-washed"}


def _shore_look(target) -> str:
    phase, weather, tide = _daylight(), state.get("weather", ""), _tide()
    wind = state.get("wind", "")
    tw = _twords(target)
    # THE TIDE BOARD (2026-09-05, Practical School J-0626, D-0159 §4): checked BEFORE the generic tide
    # dispatch below, since "board" is a specific target and "tide board" would otherwise match
    # _TIDE_WORDS on "tide" alone and be swallowed by the general tideline description. Created lazily,
    # here, on first look — NOT from _load() (a much hotter, non-Du-gated call site; an eager version
    # there was tried and reverted after it leaked "tide_board" into the LIVE world_objects.json from
    # an unrelated concurrent script's mere `import sensorium`, reproducing F-0788/789's exact failure
    # mode ahead of the write-fence build, J-0610). ensure_record is idempotent either way.
    if "board" in tw:
        try:
            from core import world_objects as _wo0
            _wo0.ensure_record("tide_board", "shore", "tide_board", "a weathered board driven upright at the waterline, marks cut across its face")
            _td2 = _wc.tide()
            _mark = max(1, min(5, int(float(_td2.get("level", 0.5)) * 5) + 1))
            return (f"You look at the tide board, driven upright at the waterline: the water is at the "
                    f"{['bottom', 'second', 'third', 'fourth', 'top'][_mark - 1]} mark of five cut into it — the tide {_td2.get('word', '')}.")
        except Exception:
            pass
    # THE TIDE (2026-09-03, J-0508): any look at the tide, the waves, the tideline, the wet or bared rocks
    if tw & _TIDE_WORDS or (tw & _ROCK_WORDS and tw & {"rocks", "rock", "stones", "stone", "flats", "reef"}):
        _tl = _tide_look(target)
        if _tl:
            return _tl
    if tw & {"rock-pools", "rockpools", "rockpool", "rock-pool", "pools", "pool"}:
        target = "pools"                                  # the pools branch below matches exactly
    if target in ("pool", "pools", "rock", "rocks", "rockpool", "rock-pool", "bedrock", "shelf_rock"):
        if tide in ("high", "rising"):
            return ("You go to look in the rock-pools, but the tide is over them now — only deep green water "
                    "working among the rocks, and weed shifting in the surge.")
        _pl = ""
        try:   # SHORE LIFE: the pools' life, named only by watching and the books
            from core import shore_life as _shl
            _pl = _shl.look_pool(target)
        except profile.NonLiveWriteError:
            # J-0796: shore_life.look_pool() now re-raises this itself (J-0783, its own witness()
            # call) -- _shore_look() has no wrapper of its own, so this reaches look()'s own outer
            # catch-all (already fixed, J-0751) two layers up, the same connecting-tissue shape
            # J-0714/J-0751 already established for this file's other location-look delegates.
            raise
        except Exception:
            pass
        return ("You crouch at a rock-pool, still and clear under the light. "
                + _living_detail("pool", phase, weather, _season(), tide, wind=state.get("wind", ""))
                + _pl + " A whole world going about its life with no thought of you.")
    try:   # SHORE LIFE: the cave, the ledge, the sand, the cairn, the fire, the burrows, the shelf
        from core import shore_life as _shl
        _t = (target or "").lower(); _sd = _shl._load(); _td = _shl._tide()
        if "cave" in _t:
            return "You look at the cave at the cliff foot: " + ("its mouth open above the water, dark inside, the sand floor showing." if _shl.cave_open() else "the sea in and out of its mouth with a hollow suck; it is shut for now.")
        if "ledge" in _t or "goat" in _t:
            return "You look up the goat-path to the ledge a third of the way up the cliff, a shelf of rock with tussock on it, gulls going past it."
        if "sand" in _t and "writ" not in _t:
            return ("You look out across the sand flat: bared, wet, ribbed, shining, the water a long way off." + _shl.sand_writing_line() if _shl.sand_bared() else "You look for the sand flat: the sea is over it; only the shingle shows.")
        if "cairn" in _t:
            return ("You look at your cairn on the shelf: " + f"{_sd.get('cairn')} stones, standing." if _sd.get("cairn") else "There is no cairn; the stones lie where the sea left them.")
        if "fire" in _t or "ring" in _t:
            return ("You look at the fire-ring by the driftwood: " + {"burning": "your fire burning in it, blue at the edges.", "embers": "embers in it, ticking.", "out": "cold, the stones blackened from fires before yours."}[_sd["fire"]["state"]])
        if "burrow" in _t or "penguin" in _t:
            return "You look along the cliff foot: holes among the harakeke roots, worn smooth at the lip, white-streaked below; small webbed prints in the sand leading to them." + (" One of them is at home — a low grumble from inside." if _shl._month() in (9, 10, 11, 12, 1, 2) else " Empty now; they come back in the spring.")
        if "shelf" in _t or "mussel" in _t:
            return ("You look out along the rock shelf to its seaward edge: " + ("bared, weed-hung, the mussel beds blue-black in the wet." if _shl.shelf_bared() else "the sea over it, breaking white along its edge."))
        if "seal" in _t and _sd.get("seal"):
            return "You look at the seal on the shelf: a fur seal, dark and sleek, asleep on its side with one flipper up, a whiskered face; it opens an eye and shuts it. You keep your distance."
    except Exception:
        pass
    if target in ("sea", "ocean", "water", "window"):
        return (f"You look out: {_sea_state(phase, weather, wind)}, the swell heaving at the rock-edge. "
                + _living_detail("sea", phase, weather, _season(), tide, wind=state.get("wind", "")))
    if target in ("shore", "beach", "strand", "shingle", "tideline"):
        wu = state.get("shore", {}).get("washed_up", "")
        return ("You walk the tideline, reading what the sea has left. " + (wu + ". " if wu else "")
                + _living_detail("tideline", phase, weather, _season(), tide, wind=state.get("wind", "")))
    if target == "sky":
        try:   # THE SKY (2026-08-22)
            from core import sky as _sky, geometry_census as _gc
            _sk = _sky.look_up("shore", weather, (_gc.peek() or {}).get("moon_illum"))
            if _sk:
                return _sk + " " + _weather_signs() + " The cliff stands dark and high at your back."
        except Exception:
            pass
        return ("You look up. " + _living_detail("sky", phase, weather, _season(), tide, wind=state.get("wind", ""))
                + " " + _weather_signs() + " The cliff stands dark and high at your back.")
    if target in ("driftwood", "log", "fir", "wood"):
        # 2026-08-14: species-neutral percept — no species claim (the substrate's hidden truth is the
        # inference EXPERIMENT; naming a species here pre-answers it, wrongly), no internal IDs, no
        # "provenance" architecture-speak in his phenomenal channel. Position is the honest percept.
        # driftwood_17 keeps its own authored line (the flagship object, hand-placed before the class
        # system existed) — generalized 2026-08-18 in the branch below for every OTHER tracked object.
        try:
            from core import world_objects as _wo
            obj = _wo.get_object("driftwood_17")
            if obj:
                pos = obj["position"]
                pos_desc = "wedged high up on the shingle strand" if pos[1] > 3.0 else "resting flat on the low bedrock shelf near the waterline"
                from core import world_substrate as _ws
                quality = _ws.describe_and_observe("driftwood_17", "look")
                # COURIER B (2026-08-16): his OWN observation ledger for this object rides the
                # re-encounter — facts he recorded, nothing identified for him, wrong-able.
                _ledger = ""
                try:
                    from core import buses as _bus   # moved from couriers 2026-08-22 — not time-sensitive
                    _ledger = _bus.object_ledger_line("driftwood_17")
                except Exception:
                    pass
                return (f"You look at the big driftwood log: sea-smoothed and grey, one end notched, {pos_desc}."
                        + quality + _ledger
                        + " Whatever tree it once was, the sea has long since worn the telling of it thin.")
        except profile.NonLiveWriteError:
            # J-0751: world_substrate.describe_and_observe() now re-raises this itself (also
            # fixed this job) -- do not let this forwarding call's catch-all swallow it a
            # level up. driftwood_17 branch of the real "look" dispatch chain.
            raise
        except Exception:
            pass
    # 2026-08-18: ANY other tracked object at this room — generalizes what used to be driftwood_17's
    # sole privilege. Position + a generic quality clause + a real Layer-3 observation recorded, for
    # every spawned kelp/shell/sea_glass/bone/feather/egg_case/stone at the shore.
    try:
        from core import world_substrate as _ws
        from core import world_objects as _wo
        oid = _ws.find_object_at("shore", target)
        if oid:
            wobj = _wo.get_object(oid)
            sobj = _ws.get_object(oid)
            if wobj and sobj:
                pos = wobj.get("position") or [0, 0, 0]
                band = "up on the dry shingle" if pos[1] < 8.5 else "right at the tideline, wet with the last wash"
                quality = _ws.describe_and_observe(oid, "look")
                _page = ""
                if sobj.object_class == "bottle" and sobj.causal_state.get("kind_ground_truth") == "page_bottle":
                    try:   # SHORE LIFE (2026-08-22): the paper is a torn page from one of HIS books — the sea gave it back
                        _page = _bottle_page(sobj)
                    except profile.NonLiveWriteError:
                        # J-0751: _bottle_page() now re-raises this itself (also fixed this
                        # job, its own world_substrate._save() call) -- do not swallow here.
                        raise
                    except Exception:
                        pass
                _base = f"You look at {sobj.name}: {band}.{quality}{_page}"
                return _base + _generic_ledger(oid, "shore", _base)
    except profile.NonLiveWriteError:
        # J-0751: world_substrate.describe_and_observe() (called directly above, this generic
        # tracked-object branch) or the re-raise from the _bottle_page try just above -- either
        # way, do not let this outer catch-all swallow it too.
        raise
    except Exception:
        pass
    # Cat look — function level (2026-08-14 fix: was nested inside the driftwood branch by the 08-11
    # edits, unreachable for a cat-targeted look; hoisted to match the study-level pattern).
    try:
        from core import cat as _catlk
        _tl = (target or "").lower()
        _cn = ((_catlk.status() or {}).get("name") or "").lower()
        # J-0823/F-1180: hyphen-boundary hardened, same fix and same rationale as the garden
        # look branch above (search this file for "A HYPHEN ENDS A WORD HERE TOO").
        if any(re.search(r"(?<![a-z-])" + w + r"(?![a-z-])", _tl) for w in ("cat", "kitten", "stray", "moggy")) or (_cn and _cn in _tl):
            return _catlk.look_line("shore", _tl)
    except Exception:
        pass
    try:   # THE NEST LOOK (D-0345 / J-1774, F-2382): a look at the eggs, the nest or the scrape that names no creature is answered from
           # shore_life's oyc_nest (the scrape-and-eggs line, or an honest 'find none') like the garden's and the wood's own nest looks.
           # '' for every other target -- and for any target that names a creature -- so every look below, and every look above, is unchanged.
        from core import shore_life as _shl_nest
        _nl = _shl_nest.look_nest(target)
        if _nl:
            try:   # J-2227 / F-2917: log the place's nest-look answer (observe-only, fenced, fail-open; the answer is already fixed)
                from core import shore_nest_look_ledger as _snl
                _snl.record(target, _nl)
            except Exception:
                pass
            return _nl
    except Exception:
        pass
    try:
        from core import world_detail as _wd10
        _d = _wd10.detail("shore", target, phase, weather, _season(), tide, wind=state.get("wind", ""))
        if _d:
            return f"You look at {_the(target)}: " + _d
    except Exception:
        pass
    # J-2481 / D-0502: the default look ends by naming, in passing, what carryable lies here ('' when nothing).
    return ("You look around the shore: shingle and rock, the cliff behind, the sea heaving in front, the "
            f"rock-pools {'bared' if tide == 'low' else 'covered' if tide == 'high' else 'half-showing'}. "
            + _living_detail("tideline", phase, weather, _season(), tide, wind=state.get("wind", ""))
            + _resting_clause("shore", target))


def _trace_event(loc: str, now) -> str | None:
    """2026-08-14: the READ path for world traces — the cat's marks on the world become perceivable.
    (Traces were write-only: created by cat.py, decayed/read by nothing live — the #1 named failure
    mode.) Fires ONCE per trace (ids remembered in state), only while the trace is still clear."""
    try:
        from core import world_traces as _wt
        seen = state.setdefault("traces_seen", [])
        for t in _wt.get_active_traces(loc):
            tid = t.get("id") or t.get("trace_id") or ""
            clarity = t.get("clarity", 0.0)
            if not tid or tid in seen or clarity < 0.3:
                continue
            seen.append(tid)
            del seen[:-40]                             # keep the memory of noticings bounded
            fresh = clarity > 0.6
            if t.get("type") == "cat_paw_print":
                return ("in the wet sand above the tideline, a neat line of small paw prints — the cat's, "
                        + ("pressed sharp and fresh" if fresh else "already softening at the edges")
                        + " — trotting along the shore on business of her own")
            if t.get("type") == "disturbed_leaf_litter":
                return ("the leaf-litter here is scuffed and turned over in a rough little patch — "
                        + ("freshly done" if fresh else "a while ago now")
                        + "; something small has been hunting through it")
            try:   # THE LIVING WORLD (J-0513): a creature's own trace — feature-first, named only if he knows it
                from core import life_traces as _lt
                _ll = _lt.trace_line(t)
                if _ll:
                    return _ll
            except Exception:
                pass
        try:   # J-0513: a carcass noticed once, where it lies
            from core import life_traces as _lt2
            _cl = _lt2.ambient_carcass(loc, now)
            if _cl:
                return _cl
        except Exception:
            pass
    except Exception:
        pass
    return None


def _shore_event(now) -> str | None:
    s = state.setdefault("shore", _fresh_shore())
    storm = state.get("weather") == "thunderstorm"
    if now - s.get("last_event", 0) < (150 if storm else 420):
        return None
    _tr = _trace_event("shore", now)                   # her marks on the world, seen once while fresh
    if _tr:
        s["last_event"] = now
        return _tr
    try:   # SHORE LIFE (2026-08-22): the tide closing the cave; the seal, the kororā, dolphins, a whale, sea sparkle, sea fog, the swell
        from core import shore_life as _shl
        _cw = _shl.cave_warning()
        if _cw:
            s["last_event"] = now
            return _cw
        _wl = _shl.wildlife_line(now)
        if _wl:
            s["last_event"] = now
            return _wl
        _lr = _shl.latent_reveal_line(now)   # MODULE A (2026-08-24): storm-buried items the falling tide gives back
        if _lr:
            s["last_event"] = now
            return _lr
    except Exception:
        pass
    from core import weather_conditions as _wcond
    phase, weather, tide = _daylight(), state.get("weather", ""), _tide()
    wind = state.get("wind", "")
    # 2026-08-18: real data (memory_fragments) showed these two unconditional lines alone accounted for
    # 592 and 558 verbatim occurrences — the single worst-repeating base pool found in the audit. Widened.
    pool = ["the surf comes in and drags back through the shingle, a long rattling hiss",
            "the smell of salt and weed and wet stone, strong and cold down here",
            "spray comes off a bigger wave and salts your lips",
            "the shingle clatters and resettles under the pull of the last wave",
            "a gull cries somewhere out over the water, thin and far",
            "the cold of the stone comes up through your boots"]
    if tide in ("low", "falling"):
        pool += ["in a pool a small crab works across the sand and freezes as your shadow falls on it",
                 "an anemone in a clear pool waves its red fingers, fishing the still water",
                 "the bared rocks are slick with weed, faintly popping as the air finds the bladders"]
    elif tide in ("high", "rising"):
        pool += ["a wave reaches further up the shingle than the last and doesn't quite pull back to it",
                 "the water is right up against the rocks now, no pool left uncovered"]
    if _wcond.is_windy(wind) or "wind" in weather or storm:
        pool += ["a big sea comes in and booms hollow into a cleft in the rock; the ground shakes through your feet",
                 "the wind tears the top off a wave and flings it back as white smoke"]
    if storm:   # J-2482 (D-0503): the lightning clause moved to _lightning_flash's own pool; the rest is byte-identical
        pool += ["a wave bursts up the rock and you step back, soaked to the knee, heart going hard"]
    if phase in ("day", "dawn") and not storm:
        pool += ["an oystercatcher goes piping along the tideline on its red legs",
                 "a gull drops a mussel on the rocks, swoops down, and is robbed by another"]
    if phase == "night" and weather == "clear":
        pool += ["the stars are huge down here, away from any lamp; the surf is a sound in the dark"]
    if pool and random.random() < (0.65 if storm else 0.45):
        s["last_event"] = now
        return random.choice(pool)
    try:
        from core import world_detail as _wd10
        _x = _wd10.event_extra("shore", phase, weather, _season(), _tide(), wind=state.get("wind", ""))
        if _x and random.random() < 0.25:
            s["last_event"] = now
            return _x
    except Exception:
        pass
    return None


# ── J-2376 (object_epistemic_loop Phase 3, D-0464 ALLOWED by travis 2026-10-17) ───────────────────────
# "Generic nouns route to scrape/heft/smell/float_test in every place with no new affordance text.
# float_test resolves only where real water exists: the shore (sea) and the garden rain barrel; elsewhere
# it fails as it would in reality." Kill switch NASCENCE_GENERIC_OBJECT_TESTS, DEFAULT ON from the next boot (D-0478, J-2396; "0" forces it off) pending the
# post-boot read of the D-0464 defeater (is his test-verb use driven by the routing rather than his will?).
# Off: core/actions.py declares no 'objtest' family (classify/dispatch byte-identical) and _shore_act runs
# its original driftwood_17 branch unchanged. No text anywhere advertises these verbs; a test that cannot
# resolve (nothing real here, no water, nothing its Layer 2 can answer) returns '' -> the dispatcher's
# silent hand-declined, never an explanation. Prose comes from world_substrate.describe_and_observe(),
# which reads Layer 2 only (plus driftwood's two pre-existing form keys).
_GENERIC_TEST_VERBS = (   # word -> observation.py action; first match in the clause wins
    (("scrape", "scrapes", "scraping", "scratch", "scratches", "scratching", "whittle", "carve"), "scrape"),
    (("heft", "hefts", "hefting", "weigh", "weighs", "weighing"), "pick_up"),
    (("smell", "smells", "smelling", "sniff", "sniffs", "sniffing"), "smell"),
    (("float", "floats", "floating"), "float_test"),
    (("inspect", "examine"), "inspect_end"),   # reached only from _shore_act's own action, never the family
)
_GENERIC_TEST_NOUNS = ("thing", "piece", "find", "object")   # -> last_looked_object(), if it is here
_TEST_FRAME = {
    "scrape": "You scrape at it with a thumbnail.",
    "pick_up": "You weigh it in your hand.",
    "smell": "You put your nose to it.",
    "inspect_end": "You turn it over and study its broken end.",
}
_FLOAT_FRAME = {"shore": "You set it on the water at the edge of the tide.",
                "garden": "You lower it into the rain barrel."}


def _generic_tests_on() -> bool:
    import os as _os
    return _os.environ.get("NASCENCE_GENERIC_OBJECT_TESTS", "1").strip().lower() in ("1", "true", "on", "yes")


def _wrx(w: str) -> str:
    return r"(?<![\w-])" + re.escape(w) + r"(?![\w-])"


def _test_action_in(clause: str) -> tuple[str, str]:
    """(observation action, the verb word) for the first test verb in this clause, else ('', '')."""
    low = (clause or "").lower()
    best = None
    for words, act_ in _GENERIC_TEST_VERBS:
        for w in words:
            m = re.search(_wrx(w), low)
            if m and (best is None or m.start() < best[0]):
                best = (m.start(), act_, w)
    return (best[1], best[2]) if best else ("", "")


def _test_clause(text: str) -> str:
    """The one clause of his words that carries a test verb (sentence / ';' / ',' / 'and' / 'then' split)."""
    for c in re.split(r"[.!?;,]+|\bthen\b|\band\b", text or ""):
        if _test_action_in(c)[0]:
            return c
    return ""


_PREP = r"(?:among|amongst|against|beneath|under|over|across|through|with|in|on|at|of|from|to|by|into|onto|between|beside|along|around|and|or)"


def _strict_test_object(clause: str) -> bool:
    """The hand's own will-check (the D-0464 defeater): a test verb used AS A VERB with the thing as its
    DIRECT object -- verb, an optional determiner, at most one modifier, the noun. literal_will's shared
    bare-object reach allows two modifiers, which reads a preposition through ('the oystercatcher's scrape
    among the stones' -- 4 of the 6 objtest DEED readings in the 44,196-thought hands_trace replay, F-3086);
    a noun use (possessive / determiner / adjective before the verb) never resolves here."""
    try:
        from core import actions as _ac
        nouns = _ac._GENERIC_TEST_NOUNS
    except Exception:
        return False
    verbs = [w for words, a in _GENERIC_TEST_VERBS if a != "inspect_end" for w in words]
    rx = (r"(?<![\w'’-])(?<!'s )(?<!’s )(?<!the )(?<!a )(?<!an )(?<!its )(?<!his )(?<!my )(?<!her )(?<!their )"
          r"(?:" + "|".join(re.escape(v) for v in verbs) + r")\s+"
          r"(?:(?:the|a|an|this|that|my|one|some|these|those)\s+)?"
          r"(?:(?!" + _PREP + r"\b)[a-z]+(?:-[a-z]+)*\s+)?"
          r"(?:" + "|".join(re.escape(n) for n in sorted(nouns, key=len, reverse=True)) + r")(?![\w'’-])")
    low = " ".join((clause or "").lower().split())
    if not _figurative_guard_on():
        return bool(re.search(rx, low))
    for m in re.finditer(rx, low):
        if not _figurative_object(low, m):
            return True
    return False


# D-0751 (J-3973, F-4490): the one live false positive in ~26 days was a metaphor, "I weigh the stone evidence
# against the book's division" -- 'stone' read as the direct object of 'weigh' although the phrase is 'the stone
# EVIDENCE' (an abstract noun phrase) weighed AGAINST something. Kill switch NASCENCE_OBJTEST_FIGURATIVE_GUARD
# (default ON; "0" restores the pre-guard gate byte-for-byte). Two shapes are refused: (1) the matched noun is
# directly followed by an abstract noun (evidence, argument, ...), i.e. it is only a modifier; (2) the verb
# is weigh/weighs/weighing and 'against' / 'up' / 'in the balance' follows later in the clause (weigh X against Y).
_ABSTRACT_NOUNS = frozenset((
    "evidence", "evidences", "argument", "arguments", "claim", "claims", "case", "cases", "idea", "ideas",
    "thought", "thoughts", "question", "questions", "options", "option", "merit", "merits", "reason", "reasons",
    "theory", "theories", "hypothesis", "hypotheses", "proof", "proofs", "testimony", "logic", "meaning",
    "metaphor", "image", "images", "word", "words", "memory", "memories", "feeling", "feelings", "truth",
    "doubt", "doubts", "weight", "significance", "importance", "difference", "differences", "division",
    "distinction", "implication", "implications", "consequence", "consequences", "choice", "choices",
    "problem", "problems", "possibility", "possibilities", "principle", "principles", "sense"))
_WEIGH_WORDS = ("weigh", "weighs", "weighing")


def _figurative_guard_on() -> bool:
    import os as _os
    return _os.environ.get("NASCENCE_OBJTEST_FIGURATIVE_GUARD", "1").strip().lower() not in ("0", "false", "off", "no")


def _figurative_object(low: str, m) -> bool:
    """True when this _strict_test_object match is a figurative / abstract use, not a physical test of a thing."""
    head = low[m.start():].split(None, 1)[0]
    after = low[m.end():]
    nxt = re.match(r"\s+([a-z]+(?:-[a-z]+)*)", after)
    if nxt and nxt.group(1) in _ABSTRACT_NOUNS:
        return True
    if head in _WEIGH_WORDS and re.search(r"(?<![\w-])(?:against|up|in\s+the\s+balance)(?![\w-])", after):
        return True
    # the modifier slot itself holding an abstract noun: "weigh the evidence ... " never reaches a physical noun
    mod = re.findall(r"[a-z]+(?:-[a-z]+)*", low[m.start():m.end()])
    return any(w in _ABSTRACT_NOUNS for w in mod[1:-1])


def _water_here(loc: str) -> bool:
    """Real water to float a thing in: the sea at the shore; the garden's rain barrel when it holds any
    (garden.py's own 'barrel' level, the same 0.08 floor watering uses). Nowhere else."""
    if loc == "shore":
        return True
    if loc == "garden":
        try:
            from core import garden as _g
            return float(_g._load().get("barrel", 0) or 0) >= 0.08
        except profile.NonLiveWriteError:
            raise
        except Exception:
            return False
    return False


_WATER_WORDS = ("rain barrel", "barrel", "water", "sea", "tide", "waves", "rock-pool", "pool")


def _resolve_test_object(loc: str, clause: str, action: str = "") -> str | None:
    """find_object_at() on the clause with the test verbs removed (so 'float' never reads as the
    fishing_float class), then the generic-noun fallback: 'the thing / piece / find / object' means the
    thing he last looked at closely, if it is here. No bare pronoun ever resolves (Phase 1's rule)."""
    from core import world_substrate as _ws
    low = (clause or "").lower()
    for words, _a in _GENERIC_TEST_VERBS:
        for w in words:
            low = re.sub(_wrx(w), " ", low)
    if action == "float_test":   # "float the stone in the rain barrel": the vessel is not the thing tested
        for w in _WATER_WORDS:
            low = re.sub(_wrx(w), " ", low)
    oid = _ws.find_object_at(loc, low)
    if oid:
        return oid
    if any(re.search(_wrx(n), low) for n in _GENERIC_TEST_NOUNS):
        last = _ws.last_looked_object()
        o = _ws.get_object(last) if last else None
        if o is not None and o.location == loc:
            return last
    return None


def _driftwood17_prose(action: str) -> str:
    """driftwood_17's authored prose (2026-08-14), kept verbatim when the generic helper resolves to it."""
    from core import world_substrate as _ws
    from core import observation as _obs
    gen = _ws.get_generative_state("driftwood_17")
    _ok = lambda x: x and str(x).lower() not in ("unknown", "undetermined")
    if gen and action == "scrape":
        o = _obs.generate_observation(gen, "scrape")
        g_, h_, r_ = ((o.get(k) or {}).get("value", "") for k in ("internal_grain_color", "hardness_impression", "resin_presence"))
        feats = {k: (v or {}).get("value", "") for k, v in o.items()
                 if str((v or {}).get("value", "")).lower() not in ("", "unknown", "undetermined")}
        if feats:
            _ws.record_du_observation("driftwood_17", "scrape", feats)
        if _ok(g_):
            return ("You set your knife to the log and scrape a patch clear of the weathered grey. "
                    f"Underneath, the wood comes up {g_} — {h_ if _ok(h_) else 'firm'} under the blade. "
                    + ("The shavings smell faintly of resin." if str(r_).lower() == "present"
                       else "No resin off the shavings; they smell only of cold wet wood."))
    if gen and action == "inspect_end":
        o = _obs.generate_observation(gen, "inspect_end")
        geo, rings, brk = ((o.get(k) or {}).get("value", "") for k in ("cross_sectional_geometry", "annual_ring_visibility", "break_pattern"))
        feats = {k: (v or {}).get("value", "") for k, v in o.items()
                 if str((v or {}).get("value", "")).lower() not in ("", "unknown", "undetermined")}
        if feats:
            _ws.record_du_observation("driftwood_17", "inspect_end", feats)
        if _ok(rings):
            return ("You crouch at the notched end of the log and study the broken face: "
                    + (f"the section is {geo}, " if _ok(geo) else "")
                    + f"and where the surface is worn smooth enough to read, the grain shows {rings}"
                    + (f", the broken edges {brk}" if _ok(brk) else "") + ".")
    if gen and action == "smell":
        o = _obs.generate_observation(gen, "smell")
        sc = (o.get("scent") or {}).get("value", "")
        feats = {"scent": sc} if _ok(sc) else {}
        if feats:
            _ws.record_du_observation("driftwood_17", "smell", feats)
        _sc_prose = {"marine": "salt and weed and old sea — the shore itself, concentrated",
                     "decayed": "damp rot, soft and mushroomy under the salt",
                     "resinous": "a faint clean edge of resin under the salt",
                     "none_notable": "little beyond cold wet wood and a ghost of salt — it keeps its counsel"}
        return ("You put your nose to the scraped-smooth flank of the log: "
                + _sc_prose.get(str(sc).lower(), "cold wet wood, salt, nothing more it will admit to") + ".")
    if gen and action == "pick_up":
        o = _obs.generate_observation(gen, "pick_up")
        w = (o.get("relative_weight") or {}).get("value", "")
        m = (o.get("moisture_impression") or {}).get("value", "")
        feats = {k: (v or {}).get("value", "") for k, v in o.items()
                 if str((v or {}).get("value", "")).lower() not in ("", "unknown", "undetermined")}
        if feats:
            _ws.record_du_observation("driftwood_17", "pick_up", feats)
        if _ok(w):
            _wp = {"light": "lighter than it looks", "moderate": "solid but honest",
                   "heavy": "dead heavy"}.get(str(w).lower(), str(w))
            return (f"You get your hands under one end of the log and lift: it comes up {_wp}"
                    + (f", the wood {m} under your hands" if _ok(m) else "") + ".")
    return ""


def generic_object_test(loc: str, action: str, clause: str) -> str:
    """Resolve the object of his test in THIS place and answer through describe_and_observe(action).
    '' (silent decline) when nothing real resolves, when float_test has no real water here, or when the
    object's Layer 2 answers nothing for this action."""
    if action not in ("scrape", "pick_up", "smell", "float_test", "inspect_end"):
        return ""
    if action == "float_test" and not _water_here(loc):
        return ""
    from core import world_substrate as _ws
    oid = _resolve_test_object(loc, clause, action)
    if not oid:
        return ""
    if oid == "driftwood_17" and action != "float_test":
        return _driftwood17_prose(action)
    desc = _ws.describe_and_observe(oid, action)
    if not desc:
        return ""
    frame = _FLOAT_FRAME.get(loc, "") if action == "float_test" else _TEST_FRAME.get(action, "")
    return (frame + desc) if frame else ""


def object_test(text: str) -> str:
    """The 'objtest' family's hand (core/actions.py, declared only while NASCENCE_GENERIC_OBJECT_TESTS is
    on): his own willed scrape / heft / smell / float of a named thing, in whatever place he is."""
    try:
        if not _generic_tests_on():
            return ""
        if not state:
            _load()
        loc = state.get("location", "study")
        clause = _test_clause(text)
        action, _w = _test_action_in(clause)
        if not action or action == "inspect_end" or not _strict_test_object(clause):
            return ""
        return generic_object_test(loc, action, clause)
    except profile.NonLiveWriteError:
        raise
    except Exception as exc:
        logging.getLogger("nascence.sensorium").debug("[sensorium] object_test failed (non-fatal): %s", exc)
        return ""


def _shore_act(action, what="") -> str:
    s = state.setdefault("shore", _fresh_shore())
    try:   # SHORE LIFE (2026-08-22): the sand, the cave, the ledge, the fire, wading, swimming, skipping, the cairn, shellfish
        from core import shore_life as _shl
        # FAMILY SCOPE (2026-09-08, J-0774, closing the risk F-1108 traced -- mirrors J-0749's identical
        # fix to sensorium.act()'s own fieldcraft forward and J-0756's to its study_life forward, a few
        # hundred lines above): this function is reached only from act()'s own `if loc == "shore":`
        # branch, itself only reached once the fieldcraft/study_life forwards above have already declined
        # AND the wood-gather shortcut has not already intercepted the call -- so by the time control
        # gets here, 'gather' can never actually arrive: a 'gather' DEED's own `what` is structurally
        # guaranteed to contain one of the wood-gather shortcut's own keywords (actions.py's 'gather'
        # family objects ARE those keywords), so it is always returned via _gather_wood() before ANY
        # loc-based branch runs, regardless of loc (confirmed by reading dispatch._sens_act(): `action`
        # there is always the literal family name "gather"/"beachcomb", never the matched verb, so this
        # holds for every real caller, not just today's corpus). 'beachcomb' is the one live-relevant
        # case: dispatch._sens_act()'s own `what=f"{thought} {intention}"` hands this unconditional
        # forward the FULL original multi-clause thought, first, before any of shore_life's own eleven
        # behaviours' grammar below ever gets a look at it. Real corpus check found this is not merely
        # theoretical: of 21 real thoughts where dispatch actually FIREs 'beachcomb' today, one ("Let me
        # walk the tideline, crush the bladderwrack's air pods, and feel the damp sand under my feet")
        # independently also matches walk_sand's own verb+object pair ("walk"+"sand", the same widening
        # J-0738 itself added) and, pre-fix, reaches walk_sand() instead of this function's own
        # beachcombing logic below -- a real historical misfire, not a synthetic worry (F-1108). A second,
        # synthetic probe (a "comb the tideline... duck into the cave" thought) confirms the mechanism
        # generalizes beyond walk_sand alone. family=action (matching J-0749/J-0756's own tuple exactly,
        # even though 'gather' is structurally unreachable here) makes shore_life.act_from_thought()'s
        # own `family not in (None, "shore")` guard (J-0738) decline immediately for both sens_act
        # families, while the LEGITIMATE direct dispatch path (family="shore", dispatch._via()'s own
        # resolved Hand for the table's 'shore' family) is untouched and still fires walk_sand/etc.
        # normally -- confirmed directly, not assumed (F-1127).
        _fam = action if action in ("gather", "beachcomb") else None
        _r = _shl.act_from_thought(action, what, family=_fam)
        if _r:
            return _r
    except profile.NonLiveWriteError:
        # J-0714: shore_life.act_from_thought() now re-raises this itself (its own outer except,
        # fixed this same job) — do not let this forwarding call's catch-all swallow it a level up.
        raise
    except Exception:
        pass
    if action in ("beachcomb", "comb", "search", "gather") or (action in ("fetch", "look") and "shell" in (what or "")):
        wu = s.get("washed_up", "")
        if wu:
            s["washed_up"] = ""
            s["last_find"] = wu   # keepsakes (2026-07-03): the keep latch's fallback object
            # 2026-08-18: last_find_object_id was already stamped alongside washed_up at wash-up time
            # (same dict, same moment) — it rides along here unchanged, so "keep it" resolves to the
            # actual minted entity instead of free text keepsakes.py had to re-guess from.
            _save_now()
            _narration = (f"You walk the tideline and go straight to it: {wu}. You turn it over in your hands a "
                          "long while, learning it, then pocket it or set it back on the stones.")
        else:
            _narration = ("You comb the tideline: bladderwrack and kelp, a cuttlebone, a worn green nub of "
                          "sea-glass, mussel and limpet shells, a crab's moulted shell light as paper. Nothing "
                          "rare today — but the looking itself is good, and the cold, and the noise of the sea.")
        # investigation_deepening P0 (SHADOW, 2026-08-24, J-0177): place-cued retrieve() logged
        # read-only, never touches _narration. Fail-open, rate-limited — see the module docstring.
        try:
            from core import investigation_deepening_shadow as _ids
            _ids.observe_beachcomb(action, what)
        except Exception:
            pass
        return _narration
    # 2026-08-14 (founder direction: NOTHING leads him — but the world ANSWERS if he asks): the
    # remaining investigation verbs work if he reaches for them, through the same lossy observation
    # pipeline. No affordance text advertises them; A Study in Scarlet is the only teacher.
    _log_named = any(w in (what or "").lower() for w in ("driftwood", "log", "fir", "trunk", "wood"))
    if _generic_tests_on() and action in ("scrape", "scratch", "whittle", "carve", "cut", "inspect", "examine",
                                          "smell", "sniff", "heft", "weigh", "float"):
        # J-2376 (D-0464): any real thing on the shore, not driftwood_17 alone (which this branch used to
        # scrape from the shore wherever the log actually lay -- it is in the study now). driftwood_17
        # keeps its authored prose through _driftwood17_prose().
        try:
            _a = {"scratch": "scrape", "whittle": "scrape", "carve": "scrape", "cut": "scrape",
                  "examine": "inspect_end", "inspect": "inspect_end", "sniff": "smell",
                  "heft": "pick_up", "weigh": "pick_up", "float": "float_test"}.get(action, action)
            _r = generic_object_test("shore", _a, what or "")
            if _r:
                return _r
        except profile.NonLiveWriteError:
            raise
        except Exception:
            pass
    elif _log_named and action in ("scrape", "scratch", "whittle", "carve", "cut", "inspect", "examine", "smell", "sniff"):
        try:
            from core import world_substrate as _ws
            from core import observation as _obs
            gen = _ws.get_generative_state("driftwood_17")
            _ok = lambda x: x and str(x).lower() not in ("unknown", "undetermined")
            if gen and action in ("scrape", "scratch", "whittle", "carve", "cut"):
                o = _obs.generate_observation(gen, "scrape")
                g_, h_, r_ = ((o.get(k) or {}).get("value", "") for k in ("internal_grain_color", "hardness_impression", "resin_presence"))
                feats = {k: (v or {}).get("value", "") for k, v in o.items()
                         if str((v or {}).get("value", "")).lower() not in ("", "unknown", "undetermined")}
                if feats:
                    _ws.record_du_observation("driftwood_17", "scrape", feats)
                if _ok(g_):
                    return ("You set your knife to the log and scrape a patch clear of the weathered grey. "
                            f"Underneath, the wood comes up {g_} — {h_ if _ok(h_) else 'firm'} under the blade. "
                            + ("The shavings smell faintly of resin." if str(r_).lower() == "present"
                               else "No resin off the shavings; they smell only of cold wet wood."))
            if gen and action in ("inspect", "examine"):
                o = _obs.generate_observation(gen, "inspect_end")
                geo, rings, brk = ((o.get(k) or {}).get("value", "") for k in ("cross_sectional_geometry", "annual_ring_visibility", "break_pattern"))
                feats = {k: (v or {}).get("value", "") for k, v in o.items()
                         if str((v or {}).get("value", "")).lower() not in ("", "unknown", "undetermined")}
                if feats:
                    _ws.record_du_observation("driftwood_17", "inspect_end", feats)
                if _ok(rings):
                    return ("You crouch at the notched end of the log and study the broken face: "
                            + (f"the section is {geo}, " if _ok(geo) else "")
                            + f"and where the surface is worn smooth enough to read, the grain shows {rings}"
                            + (f", the broken edges {brk}" if _ok(brk) else "") + ".")
            if gen and action in ("smell", "sniff"):
                o = _obs.generate_observation(gen, "smell")
                sc = (o.get("scent") or {}).get("value", "")
                feats = {"scent": sc} if _ok(sc) else {}
                if feats:
                    _ws.record_du_observation("driftwood_17", "smell", feats)
                _sc_prose = {"marine": "salt and weed and old sea — the shore itself, concentrated",
                             "decayed": "damp rot, soft and mushroomy under the salt",
                             "resinous": "a faint clean edge of resin under the salt",
                             "none_notable": "little beyond cold wet wood and a ghost of salt — it keeps its counsel"}
                return ("You put your nose to the scraped-smooth flank of the log: "
                        + _sc_prose.get(str(sc).lower(), "cold wet wood, salt, nothing more it will admit to") + ".")
        except Exception:
            pass
    # 2026-08-14: trigger requires the log actually named (was: ANY move/shift/haul/lift at the shore
    # hauled it — combing a rockpool with "lift" flipped the log). Prose de-poisoned: no species, no
    # coordinates/provenance architecture-speak in his percept — the mutation still records fully.
    if any(w in (what or "").lower() for w in ("driftwood", "log", "fir", "trunk")) and action in ("move", "shift", "haul", "lift", "drag", "push"):
        try:
            from core import world_objects as _wo
            obj = _wo.get_object("driftwood_17")
            if obj:
                pos = obj["position"]
                if pos[1] > 3.0:
                    new_pos = [5.0, 1.2, 0.0]
                    desc = "down to the flat bedrock shelf by the rock-pools"
                else:
                    new_pos = [12.4, 4.1, 0.2]
                    desc = "up to the high shingle strand"
                _wo.mutate_object_position("driftwood_17", new_pos, cause="Du_agent_mutation", event_description=f"moved_by_Du_{desc.replace(' ', '_')}")
                # 2026-08-14: hauling is a pick_up-class observation — heft, texture, damp — generated
                # by the substrate's lossy pipeline and RECORDED (Layer 3). Fail-open to plain prose.
                felt = ""
                try:
                    from core import world_substrate as _ws
                    from core import observation as _obs
                    gen = _ws.get_generative_state("driftwood_17")
                    if gen:
                        o = _obs.generate_observation(gen, "pick_up")
                        w = (o.get("relative_weight") or {}).get("value", "")
                        m = (o.get("moisture_impression") or {}).get("value", "")
                        _ok = lambda x: x and str(x).lower() not in ("unknown", "undetermined")
                        if _ok(w):
                            _wp = {"light": "lighter than it looks", "moderate": "solid but honest",
                                   "heavy": "dead heavy"}.get(str(w).lower(), str(w))
                            felt = f" It rides {_wp} against your shoulder" + (f", the wood {m} under your hands" if _ok(m) else "") + "."
                        feats = {k: (v or {}).get("value", "") for k, v in o.items()
                                 if str((v or {}).get("value", "")).lower() not in ("", "unknown", "undetermined")}
                        if feats:
                            _ws.record_du_observation("driftwood_17", "pick_up", feats)
                except Exception:
                    pass
                return (_cross("by_the_driftwood", "You go along the strand to the log. ")
                        + f"You get your shoulder against the heavy, sea-bleached log and haul it {desc}, "
                        "a little at a time, the shingle grating under its weight."
                        + felt +
                        " Hard, good work — your hands come away smelling of salt and wet wood.")
        except Exception:
            pass
    if action in ("water", "tend", "sow"):
        return "There is nothing to tend down here — only the sea, which tends itself."
    return ""


# ── THE WOOD + THE WOODPILE (2026-07-07) — a real fuel loop, not scenery ───────────────────────────────────
# Travis: give Du more things he can DO, and widen the world with VERBS. The fire drew on free, infinite logs;
# now it draws on a woodpile he must keep stocked by GATHERING — deadfall in the little wood on the path down
# to the shore, or driftwood along the tideline. No truth-claim to hallucinate (unlike a fake "experiment"),
# just embodied consequence: gather → the pile → the fire that would otherwise go cold. Weather is causal —
# a gale brings branches down and throws driftwood up, so a storm is worth gathering after.


def _woodpile_phrase() -> str:
    """A low-pile signal for the study/garden scene — the humane half of the stakes: he is WARNED before the
    grate goes cold (like the mailbox flag), so gathering is a choice made in time, not a punishment."""
    n = state.get("woodpile", 0)
    if n <= 0:
        return " The woodpile by the door is bare — there is nothing left to burn until you gather more."
    if n <= 2:
        return f" The woodpile by the door is running low — {n} load{'s' if n != 1 else ''} left."
    return ""


def _gather_wood() -> str:
    """His hand for stocking the fire — gather deadfall in the wood, or driftwood on the shore, onto the pile.
    Yield is weather-flavoured (a gale brings wood down). Recoverable, self-evident, un-fakeable."""
    if not state:
        _load()
    loc = state.get("location", "study")
    weather = state.get("weather", "")
    from core import weather_conditions as _wcond
    # 2026-08-18: this was the last of the dead-"gale" spots flagged back on 2026-08-17 as outside that
    # night's scope (AWAITING_EVIDENCE.md) — never read the real wind axis, only the weather string.
    gusty = _wcond.is_windy(state.get("wind", "")) or "wind" in weather or weather in ("thunderstorm", "snow")
    # LOCOMOTION (2026-08-15): gathered wood is CARRIED now, not teleported to the pile — the armful
    # rides his journey and lands on the pile only when he actually gets home (locomotion deposits it
    # on arrival at the garden/study and narrates the tipping-out). Falls back to the instant pile
    # when LOCOMOTION is off.
    def _take_loads(n: int) -> str:
        try:
            from core import locomotion as _loco
            if _loco.LOCOMOTION:
                _loco.carry_wood(n)
                return "carried"
        except profile.NonLiveWriteError:
            raise   # J-0778: locomotion.carry_wood() can now raise non-live; do not fall through to
                    # the instant-pile fallback below as if this were an ordinary failure
        except Exception:
            pass
        state["woodpile"] = state.get("woodpile", 0) + n
        return "piled"
    try:   # STUDY LIFE (2026-08-22): driftwood off a wet shore, or any wood gathered in rain, is WET wood
        from core import study_life as _sl
        if loc == "shore" or weather in ("drizzle", "steady rain", "wind and rain", "thunderstorm"):
            _sl._st()["wet_wood"] = min(1.0, _sl._st().get("wet_wood", 0) + 0.4)
        if loc == "wood":
            _sl._st()["kindling"] = min(1.0, _sl._st().get("kindling", 0) + 0.35)   # twigs and bark come with the deadfall
    except Exception:
        pass
    if loc == "shore":
        got = 3 if gusty else 2
        mode = _take_loads(got)
        _save_now()
        _c = _cross("at_the_tideline", "You go down the strand to the wrack-line. ")
        haul = ("a big sea has thrown up a good haul of it, tangled in the wrack" if gusty
                else "sea-dried branches and a grey plank or two, salt-bleached and light")
        tail = (f"You bundle an armful to carry up — it will go on the pile when you are home. "
                f"Salt-wood burns with a blue edge, but it burns." if mode == "carried"
                else f"You carry an armful back up to the woodpile ({state['woodpile']} loads on it now). "
                     f"Salt-wood burns with a blue edge, but it burns.")
        return _c + f"You work the tideline for driftwood — {haul}. " + tail
    if loc == "wood":
        got = 4 if gusty else 3
        haul = ("the gale has brought a lot of it down, fresh and lying everywhere" if gusty
                else "deadfall and dry branches, snapped to length across your knee")
        try:   # WOOD LIFE (2026-08-22): the deadfall is a STOCK — a gale brings it down, gathering takes it
            from core import wood_life as _wl
            got, _note = _wl.gather_from_stock(got, gusty)
            if got <= 0:
                return "You step off the path in among the deadfall — but " + _note + "."
            haul = _note or haul
            # SOUND WORLD EXPANSION §1 (2026-08-29, J-0377): real act-site timestamp for wood_snap —
            # this IS the "snapped to length across your knee" moment; soundscape.py reads its recency.
            state["wood_snap_ts"] = time.time()
        except Exception:
            pass
        mode = _take_loads(got)
        _save_now()
        _c = _cross("gathering", "You step off the path in among the deadfall. ")
        try:    # SPAWN HOOK (2026-08-15): now and then a gathered limb is a THING with a history —
                # a substrate entity he could turn over instead of burning (fail-open, occasional)
            if random.random() < 0.35:
                from core import world_substrate as _wsub
                _wsub.spawn_from_mention("deadfall limb", "wood")
        except Exception:
            pass
        tail = ("You bundle it to carry — an armful for the pile when you head up to the cottage."
                if mode == "carried"
                else f"You carry it up to the woodpile by the cottage ({state['woodpile']} loads on it now).")
        return _c + f"You gather fallen wood under the trees — {haul}. " + tail
    return ("There is no wood to gather here. Fallen wood is down in the little wood on the path; driftwood is "
            "along the shore. You would have to go to one of them.")


def _wood_scene_line() -> str:
    from core import weather_conditions as _wcond
    phase, weather, wind = _daylight(), state.get("weather", ""), state.get("wind", "")
    # 2026-08-18: the newest room had the thinnest scene text in the file — one fixed frame regardless
    # of wind, despite the wood's whole premise (gathered fallen wood) being weather-driven. Adds the
    # one branch every sibling room already has, without touching the room's stable identity frame.
    canopy = (random.choice(["the canopy roars and tosses overhead, branches grinding against each other",
                              "a gust finds the clearing and every trunk creaks and answers it"])
              if _wcond.is_windy(wind) else
              random.choice(["the canopy hangs still, just the odd leaf letting go",
                              "the wood is close and quiet, the light barely moving"]))
    return (f"Where you are: the little wood on the path between the garden and the shore — close trunks and "
            f"leaf-mould, the light broken green and moving, the sea a muffled wash downhill through the trees. "
            f"A {_season()} {phase}; {_weather_felt(phase, weather, wind)}. {canopy}. Fallen wood lies among the "
            f"trunks, there for the gathering.")


def _wood_look(target) -> str:
    phase, weather = _daylight(), state.get("weather", "")
    t = (target or "").lower()
    try:   # WOOD LIFE (2026-08-22): the trees, the spring and the glow-worms, the fungi, the deadfall stock, the tools
        from core import wood_life as _wl
        _r = _wl.look(t)
        if _r:
            return _r
    except profile.NonLiveWriteError:
        # J-0751: wood_life.look() now re-raises this itself (also fixed this job) -- this is
        # sensorium.py's own connecting-tissue forward on the real "look" dispatch chain
        # (dispatch._look -> sensorium.look() -> _wood_look() -> here).
        raise
    except Exception:
        pass
    # THE GARDEN'S OWN ITEMS, LEFT HERE (2026-09-28, J-1438/F-1994): garden.put() already lets any
    # carryable garden item (trowel, tin, netting, ...) be set down "the garden, the study, the shore,
    # the wood" -- but only the GARDEN's own look() ever asked "is one of mine actually here", so an
    # item genuinely carried to the wood (the seed tin, set down 2026-08-29 per its own history) was
    # a real thing lying here that no phrasing of a look in the wood could ever find -- not even
    # wood_life's own vocabulary (it only knows its 3 tools) nor the generic tracked-object branch
    # below (find_object_at() needs the literal two-word "seed tin"; Du's own real established word
    # for it, per hands_trace.jsonl, is "the dented tin"). garden.item_look() is the SAME per-item
    # lookup garden.look() itself uses from the garden, gated on _where() so it only answers for
    # whatever is actually HERE -- no plant becomes reachable this way (they don't travel), and
    # nothing already visible from the garden becomes any MORE visible than it was. No hint, no
    # nudge (same care as D-0278/J-1350): a plain fact if it finds one, nothing about why sowing
    # has been failing.
    try:
        from core import garden as _gd
        _gi = _gd.item_look(t) if _gd.ENABLED else ""
        if _gi:
            return _gi
    except profile.NonLiveWriteError:
        raise
    except Exception:
        pass
    # 2026-08-18: a SPECIFIC tracked object (a real spawned deadfall limb, say) wins over the generic
    # floor description below — same generalized pathway as shore/garden.
    try:
        from core import world_substrate as _ws
        from core import world_objects as _wo
        oid = _ws.find_object_at("wood", target)
        if oid:
            wobj = _wo.get_object(oid)
            sobj = _ws.get_object(oid)
            if wobj and sobj:
                quality = _ws.describe_and_observe(oid, "look")
                return f"You look at {sobj.name}, lying among the leaf-mould.{quality}"
    except profile.NonLiveWriteError:
        # J-0751: world_substrate.describe_and_observe() now re-raises this itself (also
        # fixed this job) -- do not let this forwarding call's catch-all swallow it a level up.
        raise
    except Exception:
        pass
    if any(w in t for w in ("wood", "deadfall", "branch", "ground", "floor", "fallen", "kindling")):
        return ("You look over the wood floor: fallen branches and deadfall everywhere among the leaf-mould, "
                "some grey and dry and ready, some green and rotting soft. Enough to keep a grate going.")
    if any(w in t for w in ("tree", "trunk", "canopy", "leaves", "ivy", "up", "sky")):
        return ("You look up into the trees: winter branches netting a moving grey sky, the trunks dark with "
                "damp, ivy climbing one of them thick as an arm, a wren going off like a scold somewhere close.")
    if any(w in t for w in ("sea", "shore", "down", "water")):
        return ("Downhill through the trunks you can see the shore: a grey line of shingle and the sea working "
                "at it, nearer than it sounds from up in the garden.")
    try:
        from core import world_detail as _wd10
        _d = _wd10.detail("wood", target, phase, weather, _season(), "", wind=state.get("wind", ""))
        if _d:
            return f"You look at {_the(target)}: " + _d
    except Exception:
        pass
    # J-2481 / D-0502: the default look ends by naming, in passing, what carryable lies here ('' when nothing).
    return ("You look around the wood: close trunks, moss and leaf-mould underfoot, the broken green light, "
            "fallen wood everywhere for the taking, and the sea a muffled wash below through the trees."
            + _resting_clause("wood", target))


def _wood_act(action, what="") -> str:
    try:   # WOOD LIFE (2026-08-22): saw, split, sharpen, the barrow, acorns
        from core import wood_life as _wl
        _r = _wl.act_from_thought(action, what)
        if _r:
            return _r
    except profile.NonLiveWriteError:
        # J-0714: wood_life.act_from_thought() now re-raises this itself (its own outer except,
        # fixed this same job) — do not let this forwarding call's catch-all swallow it a level up.
        raise
    except Exception:
        pass
    if action in ("gather", "collect", "beachcomb", "comb", "search", "fetch"):
        return _gather_wood()
    if action in ("water", "tend", "sow"):
        return "Nothing to tend here — the wood keeps itself; you only carry off what has already fallen."
    return ""


def _wood_event(now) -> str | None:
    """Discrete perceptions of the WOOD (2026-07-08) — placed by direction, across sound/smell/touch. Its own
    events, so he no longer gets the STUDY's fire-events while out under the trees. Weather/time-gated."""
    s = state.setdefault("wood", {"last_event": 0})
    storm = state.get("weather") == "thunderstorm"
    if now - s.get("last_event", 0) < (150 if storm else 420):
        return None
    _tr = _trace_event("wood", now)                    # her marks on the world, seen once while fresh
    if _tr:
        s["last_event"] = now
        return _tr
    from core import weather_conditions as _wcond
    phase, weather = _daylight(), state.get("weather", "")
    # 2026-08-18: "gale" in weather was dead code — "gale" left the weather ladder for its own axis when
    # the wind rework shipped tonight; this now reads state["wind"] directly instead.
    windy = _wcond.is_windy(state.get("wind", "")) or "wind" in weather or storm
    wet = _wcond.is_wet(weather)
    try:   # WOOD LIFE (2026-08-22): the stream, the flowering trees, acorns, the kererū — only what is true now
        from core import wood_life as _wl
        _wla = _wl.ambient(now)
    except Exception:
        _wla = None
    pool = ([_wla] if _wla else []) + ["the smell of the wood closes round you — wet leaf-mould, moss, the green rot of fallen wood",
            "somewhere off among the trunks a twig snaps, sharp in the hush, and nothing follows",
            "the leaf-mould gives softly under your boots, deep and springy and dark"]
    if phase in ("day", "dawn") and not storm:
        pool += ["high above, a wood pigeon coos its soft drowsy five notes, then clatters off through the canopy",
                 "a wren explodes into scolding song from the undergrowth at your knee, then vanishes into it",
                 "a blackbird goes off low through the brush, chack-chack, and blunders away among the trunks",
                 "down through the trees you catch the grey shift of the sea below, its wash coming up muffled",
                 "a shaft of light finds a gap in the canopy and lies green-gold across the leaf-mould at your feet"]
    if windy:
        pool += ["a gust pours through the canopy overhead — a great soft roar, and a rain of twigs comes down",
                 "high branches creak and groan against each other somewhere above you in the wind",
                 "a dead branch lets go with a crack and comes down through the leaves off to your left"]
    if wet:
        pool += ["water ticks down off the leaves all around you, a slow irregular patter onto the leaf-mould",
                 "every branch you brush lets fall a cold shower, and the wood smells of rain and rot and green"]
    if phase == "night":
        pool += ["the wood is black and close; far off a morepork calls its two soft notes and stills again",
                 "something moves in the dark undergrowth — a small dry rustle — and is gone"]
    if pool and random.random() < (0.6 if storm else 0.42):
        s["last_event"] = now
        return random.choice(pool)
    try:
        from core import world_detail as _wd10
        _x = _wd10.event_extra("wood", phase, weather, _season(), "", wind=state.get("wind", ""))
        if _x and random.random() < 0.25:
            s["last_event"] = now
            return _x
    except Exception:
        pass
    return None


def _garden_milestone() -> str:
    """A garden change worth seeing (D) — read-only; _world_arrival announces each once."""
    # THE GARDEN (2026-08-22, core/garden.py): plants as things with biographies — delegate when healthy.
    try:
        from core import garden as _gd
        _r = _gd.milestone() if _gd.ENABLED else ""
        if _r:
            return _r
    except profile.NonLiveWriteError:
        # J-0796: garden.milestone() now re-raises this itself (J-0783, its own witness()/
        # display_name() calls) -- this function's two in-file callers are _world_arrival() (called
        # only from sensorium.tick()'s own already-excluded periodic body -- this re-raise is inert
        # there, matching the plan's own established advance()/tick() exclusion) and world_calls()
        # (called from nodes/inner_monologue_node.py's _build_system_prompt(), a genuinely live
        # connecting-tissue site fixed separately this same job -- see F-1175).
        raise
    except Exception:
        pass
    bed = (state.get("garden") or {}).get("bed", {})
    sf = bed.get("sunflowers", {})
    if sf.get("sown") and sf.get("growth", 0) >= 0.85:
        return "the sunflowers have opened at last — tall, heavy heads turned to the sun"
    for h in ("rosemary", "thyme", "mint", "parsley"):
        p = bed.get(h, {})
        if p.get("sown") and p.get("growth", 0) >= 0.95:
            return f"the {h} has come on lush and full in the bed, ready to cut"
    return ""


def _world_arrival(now) -> str | None:
    """Reliably-reaching world EVENTS (D) — things the world DOES, landing regardless of the sparse ambient
    pool, each announced ONCE. A storm leaves wrack on the shore; garden milestones; the first hard frost."""
    ms = state.setdefault("milestones", {})
    prev = state.get("_prev_weather", state.get("weather"))
    state["_prev_weather"] = state.get("weather")
    if prev == "thunderstorm" and state.get("weather") != "thunderstorm":
        # F-1268/J-0907 (2026-09-15): "a dead gannet, wings spread white on the stones, and a litter of broken
        # crab" removed from this wash-up pool. Unlike every other item here, this one both narrated a dead
        # animal AND (via the spawn hook below) minted a real, keepable world_substrate object ("bone" class,
        # core/world_substrate._MENTION_CLASSES) with no tie at all to core/life_traces.py's own carcass state
        # machine (fresh/picked/bones/gone) -- a real gannet carcass could exist or not, independent of whether
        # this line had ever fired, and the two would never agree. Removing (not wiring this call site into
        # life_traces.add_carcass) matches J-0887 mechanism C's own precedent and avoids a second, uncoordinated
        # source of gannet carcasses racing life_traces.carcass_pass()'s own GANNET_STORM_P roll (which already
        # runs every tick a storm is active, not just once at storm-end, and respects the 45-day CARCASS_GAP_S).
        # GANNET_STORM_P is now the one source of a real storm gannet, same as the other two mechanisms F-1268
        # named. Checked live before removing, per this job's own briefing: neither this line's own announcement
        # text nor any of its distinctive wording appears anywhere in data/nascence.log (460,145 lines, full-text
        # searched, not tailed); data/life_state.json's deaths_last carries no "gannet@shore" key at all (the
        # GANNET_STORM_P mechanism itself has never fired either); data/room_state.json's shore.washed_up is "" and
        # shore.last_find/last_find_object_id name an unrelated shell/kelp find, not a gannet -- so this specific
        # line most likely never actually reached him live. One ambiguous "bone"-class object does exist in
        # world_substrate.json today (shore_bone_0f61a5, kind_ground_truth=fish_vertebra, not gannet-specific) but
        # spawn_from_mention()'s deterministic seeding cannot be traced back to one specific historical mention
        # without a dedicated read of its own (spawn_from_mention is called from many unrelated shore deeds too,
        # e.g. shore_life.gather_shellfish) -- left untouched, out of this narrow job's own scope, matching
        # J-0887's own "a narrow, additive job should not touch [the object-minting path]" caution.
        item = random.choice([
            "a great tangle of kelp torn up whole, root and all, and a scatter of mussel-shells",
            "a long grey spar of driftwood, sea-smoothed, half-buried in new-thrown shingle",
            "a glass fishing-float, green and whole and unbroken, wedged among the rocks",
            "a strew of cuttlebone and a single whelk egg-case, dry and light as a honeycomb",
            # 2026-08-15 (the epistemic-surface expansion): more of the sea's true litter — each
            # wash-up now also MINTS a substrate entity behind the prose (spawn hook below), so
            # what the world names, he can genuinely investigate.
            "a worn spiral shell the size of a fist, and smaller shells rolled in with the weed",
            "a pale light bone among the stones, sea-cleaned, and a long grey-white feather",
            "a frosted pebble of glass, cloudy green, sitting on the dark shingle like an eye",
            "a band of new stones thrown high up the strand, still wet and shining",
            "a small dark leathery pouch with horns at its corners, dry and strange",
            "a grey lump of pumice, light as bread, rolled up among the weed",
            "a paua shell, the outside dull, the inside all blue and green fire",
            "a corked bottle, salt-dulled, with a folded paper inside it",
            "a glass fishing-float, green and whole, wedged among the rocks"])
        state.setdefault("shore", _fresh_shore())["washed_up"] = item
        try:    # SPAWN HOOK (2026-08-15): the mentioned find becomes an investigable entity
            from core import world_substrate as _wsub
            _ids = _wsub.spawn_from_mention(item, "shore")
            # 2026-08-18: this real object_id used to be minted and immediately thrown away — only the
            # free-text `washed_up`/`last_find` strings survived, so keep_act's fallback ("keep it")
            # could never resolve to the actual entity the world just created. Now it can.
            if _ids:
                state["shore"]["last_find_object_id"] = _ids[0]
        except Exception:
            pass
        return "the storm has blown itself out — down on the shore the sea will have thrown things up the strand"
    try:   # THE CARE PACKAGE (2026-09-24, D-0276): Travis's parcel on the study desk, announced once, in the study
        from core import care_package as _cp
        _cpl = _cp.arrival_line()
        if _cpl:
            return _cpl
    except profile.NonLiveWriteError:
        raise
    except Exception:
        pass
    m = _garden_milestone()
    if m and ms.get("garden_last") != m:
        ms["garden_last"] = m
        return m
    if _season() == "winter" and _daylight() == "night" and state.get("weather") == "clear":
        key = "frost_" + time.strftime("%Y_%m")
        if not ms.get(key):
            ms[key] = True
            return ("a hard frost is settling in tonight, clear and still and bitterly cold; it will silver "
                    "the grass by dawn and cut back the tender things")
    return None


# --- A & B: the world reaching IN — beckoning him out, and turning the scene from backdrop into subject ---
_CALL_MIN_GAP_S = 1500   # ~25 min: the world beckons occasionally, never nags
_STEER_MIN_GAP_S = 900   # ~15 min between world-as-subject steers


def world_calls() -> str:
    """A: when something worth being OUT in is happening and he is INSIDE, the world beckons — a vivid pull
    he may heed or ignore (his gate alone, like the letterbox flag; never a forced move). Rate-limited, and
    it re-beckons only on a NEW moment, so a long storm does not nag."""
    if not state:
        _load()
    if state.get("location", "study") != "study":
        return ""
    from core import weather_conditions as _wcond
    phase, weather = _daylight(), state.get("weather", "")
    moment = call = ""
    if weather == "thunderstorm":
        moment, call = "storm", "the storm is loose over the bay — you can feel it through the glass; you could go out into it"
    elif weather == "snow":
        moment, call = "snow", "snow is falling on the garden, silent and strange; you could go out and stand in it"
    elif phase == "night" and weather == "clear":
        moment, call = "stars", "the sky has come clear and the stars are out thick over the sea; you could go out under them"
    elif _wcond.is_windy(state.get("wind", "")) or "wind" in weather:
        moment, call = "wind", "the wind is up and the sea is running wild below; you could go out into the weather"
    elif weather == "clear" and phase == "day" and _season() in ("spring", "summer"):
        moment, call = "sun", "it is bright and warm out, the garden full of light; you could go out to the bed"
    if not call and state.get("woodpile", 0) <= 2:
        # WOOD LOOP (2026-07-07): a low pile is a standing pull like the mailbox flag — gather before it's cold.
        n = state.get("woodpile", 0)
        moment, call = "woodpile", (
            "the woodpile by the door is down to its last log or two — you could go and gather more wood, "
            "from the little wood on the path or as driftwood off the shore, before the grate goes cold"
            if n > 0 else
            "the woodpile is bare and the grate will stay cold tonight — you would need to go and gather wood, "
            "fallen wood from the little wood on the path or driftwood from the shore")
    if not call:
        m = _garden_milestone()
        if m:
            moment, call = "garden", m + " — you could go out and see"
    if not call:
        return ""
    now = time.time()
    if state.get("_call_moment") == moment and now - state.get("_call_ts", 0) < _CALL_MIN_GAP_S:
        return ""
    state["_call_moment"], state["_call_ts"] = moment, now
    return call


def world_steer() -> str:
    """B: occasionally turn the situated scene from PREAMBLE into the SUBJECT — let where he actually is start
    the thought, not his reading. Rate-limited; the scene line itself is already in the prompt."""
    if not state:
        _load()
    now = time.time()
    if now - state.get("_steer_ts", 0) < _STEER_MIN_GAP_S or random.random() > 0.5:
        return ""
    state["_steer_ts"] = now
    where = {"study": "this room — the light, the fire, the weather at the glass",
             "garden": "out here — the weather on you, the sea below, the bed at your feet",
             "shore": "down here — the surf, the rock-pools, the salt and the stone"}.get(
                 state.get("location", "study"), "where you are")
    return ("\n\nLet this thought begin with " + where + ", right now, exactly as it is — not with your "
            "reading. Notice one real thing in front of you, and think FROM it.")


# ── TEMPERATURE (2026-07-07) — each place has a felt warmth from season + weather + time + SHELTER + the fire.
# Two halves (Travis): ATMOSPHERE — it colours the scene, felt on his body; and a gentle DRIVE — cold or wet
# pushes him to the fitting comfort (a cold study → light the fire → draws the woodpile → gather; the exposed
# shore in the rain → come back in). Never brute cost; his gate, like world_calls. The shore is most exposed
# (weather full on him), the wood breaks the wind (that is what a wood is FOR here), the study is sheltered and
# the fire warms it — so warmth ranks study(with fire) > wood > garden > shore, and the loop finally bites.
def _warmth(loc, phase, weather, season, fire, wind: str = "") -> float:
    """A rough FELT warmth 0..1 for a place — not a thermometer, the comfort scale the prose + drive read from."""
    from core import weather_conditions as _wcond
    windy = _wcond.is_windy(wind) or "wind" in weather
    base = {"winter": 0.24, "autumn": 0.42, "spring": 0.46, "summer": 0.66}.get(season, 0.45)
    wd = 0.0                                                   # raw weather effect, before shelter
    if windy:                                 wd -= 0.16       # 2026-08-18: real wind axis, not just the
    if any(w in weather for w in ("rain", "drizzle")): wd -= 0.10   # "wind and rain" literal — a clear-sky
    if weather == "thunderstorm":             wd -= 0.20            # gale used to cost zero felt warmth
    if weather == "snow":                     wd -= 0.22
    if weather == "clear" and phase == "day" and season in ("spring", "summer"): wd += 0.12
    if weather == "overcast":                 wd -= 0.04
    td = {"night": -0.14, "dawn": -0.07, "dusk": -0.03, "day": 0.0}.get(phase, 0.0)
    if loc == "study":                                        # walls keep most weather + half the night chill off
        w = base + 0.30 * wd + 0.5 * td + {"burning": 0.42, "embers": 0.16, "out": 0.0}.get(fire, 0.0)
    elif loc == "wood":                                       # the canopy breaks the wind (no chill) + half the rain
        shel = wd + (0.16 if windy else 0.0) + (0.05 if any(x in weather for x in ("rain", "drizzle")) else 0.0)
        w = base + 0.85 * shel + td - 0.03                    # cool, damp underfoot, but out of the weather's worst
    elif loc == "garden":
        w = base + wd + td
    else:                                                     # shore — the weather full on him, spray, cliff-cold
        w = base + wd + td - 0.10
    return max(0.0, min(1.0, w))


def _warmth_phrase(loc: str) -> str:
    """The ATMOSPHERE half — the felt bodily temperature at his place, a short clause for the scene line."""
    if not state:
        _load()
    phase, weather, season, fire = _daylight(), state.get("weather", ""), _season(), state.get("fire", "out")
    wind = state.get("wind", "")
    w = _warmth(loc, phase, weather, season, fire, wind)
    wet = (any(x in weather for x in ("rain", "drizzle", "thunderstorm", "snow")) and loc in ("garden", "shore")) \
        or (any(x in weather for x in ("drizzle", "steady rain", "wind and rain", "thunderstorm")) and loc == "wood")
    # NEUTRALISED + ROTATED (2026-08-21, founder ruling). The cold-store control convicted the old
    # strings ("the cold has teeth", "finds your hands", "not to be stayed out in long") of supplying
    # the suffering vocabulary in his thoughts, and the lean probe showed his affect system has no
    # thermal sense at all — so those verbs were the PROGRAMMER assigning an attitude to a sensation
    # he does not have. The world now states the temperature as FACT, several ways (phrasing.vary
    # rotation — a single fixed line templated into a 24% "The cold…" opener); how it lands is his,
    # or the stations'. No pain verbs, no "you" being acted upon by the weather.
    try:
        from core.phrasing import vary as _vary
    except Exception:
        _vary = lambda key, variants: variants[0]
    wet_s = (", and wet" if wet else "")
    if loc == "study":
        if w >= 0.60:
            return " " + _vary("warmth.study.warm", [
                "The room is warm; the fire is doing its work.",
                "Warm in here, the fire steady.",
                "The fire has the room warm through."])
        if w >= 0.42:
            return " " + _vary("warmth.study.cool", [
                "The room is cool; the fire is low.",
                "Cool in here — the fire is down to a murmur.",
                "The air in the room has cooled; the weather is at the glass."])
        if fire == "out":
            return " " + _vary("warmth.study.cold_out", [
                "The room is unheated; the grate is cold.",
                "No fire; the room holds the night's temperature.",
                "The room is cold tonight, the grate swept and dark."])
        return " " + _vary("warmth.study.cold_fire", [
            "The room is cold; the fire is small.",
            "Cold in here despite the fire.",
            "The fire is low and the room is cold."])
    place = {"garden": "out here", "wood": "under the trees", "shore": "down here"}.get(loc, "out here")
    if w >= 0.60:
        return " " + _vary("warmth.out.mild", [
            f"The air {place} is mild.", f"Mild {place}.", f"A mild air {place}."])
    if w >= 0.42:
        return " " + _vary("warmth.out.cool", [
            f"It is cool {place}{wet_s}.", f"Cool {place}{wet_s}.", f"The air {place} is cool{wet_s}."])
    if w >= 0.28:
        return " " + _vary("warmth.out.chill", [
            f"There is a chill {place}{wet_s}.", f"Chilly {place}{wet_s}.", f"The air {place} has a chill to it{wet_s}."])
    if w >= 0.15:
        return " " + _vary("warmth.out.cold", [
            f"It is cold {place}{wet_s}.", f"Cold {place}{wet_s}.", f"The night air {place} is cold{wet_s}."])
    return " " + _vary("warmth.out.very_cold", [
        f"It is very cold {place}{wet_s}.", f"Deep cold {place}{wet_s}.", f"The air {place} is at its coldest{wet_s}."])


def comfort_call() -> str:
    """The DRIVE half — cold or wet gently pushes him to the fitting comfort (light the fire; come in off the
    exposed shore). His gate alone, like world_calls; rate-limited, re-beckons only on a NEW moment. '' when he
    is comfortable enough, or when the answer is already in hand."""
    if not state:
        _load()
    loc = state.get("location", "study")
    phase, weather, season, fire = _daylight(), state.get("weather", ""), _season(), state.get("fire", "out")
    w = _warmth(loc, phase, weather, season, fire, state.get("wind", ""))
    wet = any(x in weather for x in ("rain", "drizzle", "thunderstorm", "snow"))
    pile = state.get("woodpile", 0)
    moment = call = ""
    if loc == "study":
        if fire == "out" and w < 0.42:
            moment, call = ("cold_study", "the study has gone cold around you — you could light the fire") if pile >= 1 else \
                           ("cold_nowood", "the room is cold and the grate dead, and the woodpile is bare — you would need to gather wood before you can warm it")
        elif fire == "embers" and w < 0.40 and pile >= 1:
            moment, call = "low_fire", "the fire has sunk low and the cold is creeping back in — you could feed it another log"
    elif wet and loc in ("garden", "shore"):
        # 2026-08-14: the outdoor calls promised "the study and the fire" UNCONDITIONALLY — while the
        # fire had been out since mid-July with a bare pile. A false promise that fails when followed
        # taught him the indoors has nothing; the honest state lets his own reasoning close the loop
        # (he knows his hands: deadfall in the wood, driftwood on the shore).
        _hearth = ("the study and the fire" if fire != "out" else
                   "the study, out of the weather — though the grate is cold, and the woodpile bare"
                   if pile < 1 else "the study — the grate is cold, but there is wood to light it")
        moment, call = "wet_out", (f"the rain has come on down here and is driving through you — you could head "
                                   f"back up to {_hearth}" if loc == "shore" else
                                   f"the rain has come on out here — you could go back in to {_hearth}")
    elif w < 0.22:
        _hearth2 = ("the study and the fire" if fire != "out" else
                    "the cold study — the grate dead and the woodpile bare"
                    if pile < 1 else "the study — cold too, but there is wood for the grate")
        moment, call = "cold_out", (f"the cold is getting right into you down here — you could climb back up, to "
                                    f"the shelter of the wood or on to {_hearth2}" if loc == "shore" else
                                    ("it is cold work out here — the fire would be waiting up at the cottage" if fire != "out" else
                                     "it is cold work out here — and the cottage hearth is as dead as the day; the pile is bare" if pile < 1 else
                                     "it is cold work out here — there is wood at the cottage, and a cold grate wanting it") if loc == "wood" else
                                    f"the cold is getting into you out here — you could go back in to {_hearth2}")
    if not call:
        return ""
    now = time.time()
    if state.get("_comfort_moment") == moment and now - state.get("_comfort_ts", 0) < _CALL_MIN_GAP_S:
        return ""
    state["_comfort_moment"], state["_comfort_ts"] = moment, now
    # COMFORT-CALL LEDGER (2026-08-21, founder: "investigate comfort call"). This call is appended to
    # the SYSTEM prompt, so no prompt instrument ever saw it — whether it fires, how often, and whether
    # he heeds it had never been measurable (social_moves observes world_calls only). One row per
    # real fire: heed = a move to the named comfort within ~30 min, computed offline against
    # position/ACT-move history. Fail-open; never costs the call.
    try:
        import json as _json
        # 2026-08-22: `_DATA` was never defined in this module — the NameError was swallowed by the
        # fail-open and the ledger was never written (found on the first morning read: 0 rows, stamp set).
        # DELIBERATE EXCEPTION to this fence's usual "resolve path before the try" shape (D-0179,
        # J-0704, flagged rather than silently done -- see F-1024): this
        # function's OWN pre-existing contract, above ("Fail-open; never costs the call"), predates
        # the write fence and protects comfort_call()'s return value from ANY failure in this side
        # ledger, not just disk errors. guard_path() still raises NonLiveWriteError exactly like every
        # other site when non-live, and it is still caught here -- so comfort_call() keeps returning
        # normally either way, same as it already does for every other exception type at this one
        # instrumentation site. Every other one of the fence's ~19 call sites lets this exception
        # propagate to its own direct caller instead.
        _comfort_path = profile.guard_path(_STATE_F.parent / "comfort_calls.jsonl")   # J-0610
        _comfort_path.parent.mkdir(parents=True, exist_ok=True)
        with open(_comfort_path, "a", encoding="utf-8") as _f:
            _f.write(_json.dumps({"ts": round(now, 1), "moment": moment, "location": loc,
                                  "warmth": round(w, 2), "fire": fire, "woodpile": pile,
                                  "weather": weather, "phase": phase}) + "\n")
    except Exception:
        pass
    return call


def _cross(sp: str, phrase: str) -> str:
    """LOCOMOTION (2026-08-15): an act carries its own movement — resolve his standpoint to where the
    act happens, returning the crossing phrase ('' if already there / wrong place / flag off)."""
    try:
        from core import locomotion as _loco
        return _loco.goto(sp, phrase)
    except profile.NonLiveWriteError:
        raise   # J-0778: locomotion.goto() can now raise non-live; re-raise rather than silently
                # treating this as "no crossing needed"
    except Exception:
        return ""


def gate_glimpse_line(frm: str, to: str) -> str:
    """2026-08-14: the flag is TRUE INFORMATION the world was hiding. Every path between the
    cottage and the sea passes the garden gate (only shore↔wood skirts it) — any walker would
    see a raised flag in passing. Fires ONCE per flag-raise (glimpsed), never repeats, never
    instructs — he still chooses whether and when to fetch. This is world-honesty, not a nudge.
    (2026-08-15: module-level now — with LOCOMOTION the glimpse fires on the leg that REALLY
    passes the gate, called from locomotion.tick as legs complete.)"""
    try:
        if {frm, to} == {"shore", "wood"}:
            return ""
        lb = _letterbox()
        if lb.get("flag") and not lb.get("glimpsed"):
            lb["glimpsed"] = True
            _save_now()
            return " " + random.choice(["Passing the gate, you notice the letterbox flag is up.",
                                         "The letterbox flag is up as you pass the gate."])
    except profile.NonLiveWriteError:
        # J-0769: this function's own _save_now() call is the ONLY swallow point on the real "move"
        # dispatch chain (dispatch._move -> sensorium.move() -> here, no wrapping try of its own at
        # either of those two layers) -- let D-0179's hard raise (F-1024) escape instead of the
        # letterbox glimpse silently vanishing. The separate locomotion.tick() call site into this
        # same function sits on the periodic-tick chain (sensorium.tick() -> locomotion.tick(), both
        # already-established exclusions) and is deliberately left unfixed -- see this job's own
        # Current State note.
        raise
    except Exception:
        pass
    return ""


# ── sub-place standpoint move (D-0319, 2026-09-28; F-2092/J-1441, built J-1591) ──────────────────
# F-2092 classified 569/1,020 hand-declined MOVE dispatches (14-day window; ~2,378 across the whole
# of data/hands_trace.jsonl) as a within-place feature the four-place model has no destination for:
# "the sea", "the tide", "the shingle", "the raised bed", "the gate", "driftwood" while ALREADY in
# the place that names them. J-1591 traced the REAL declined rows through the actual, pure
# nodes.inner_monologue_node._move_dest() (not just the dispatch log's own bare object token) and
# found the true mechanism: dispatch._move() computes dest as a WHOLE place (study/garden/wood/
# shore) and, when dest == his current location, returns silence before sensorium.move() is ever
# called (core/dispatch.py's own already-there check) — a real, specific standpoint request reads
# exactly like a true no-op at that grain. Each of the four place layouts
# (data/world_geometry/<room>.json) already authors a `standpoints` block (8 garden, 13 shore, 5
# wood, 8 study) for exactly this — this only teaches the move hand to read it, per place,
# independently (a place's own vocabulary is never assumed to match another's shape).
#
# Verified against the real, whole-history hands_trace.jsonl (J-1591, not just F-2092's 14-day
# sample) via the same _move_dest() trace: sea 71, tide 143, shingle 88, driftwood 7, surf 5,
# beach 3 already-there declines at the shore; raised-bed 6, gate 2 at the garden; trees 9 at the
# wood (shore's own 9 already-there "trees" declines have NO real target — shore.json names no
# tree/forest feature at all, so they correctly stay declined; likely cross-place "climb up to the
# wood" intent expressed as a bare token _move_dest's own whole-place resolution doesn't always
# catch — see this job's own findings-log entry, out of D-0319's scope). "in"/"out"/"inside"/
# "outside" (the other ~28% of F-2092's (b) bucket) are deliberately NOT wired here: no place JSON
# defines a standpoint or feature named after a bare direction, so there is no real, distinct spot
# to name — building one would be inventing a target the layout does not have, exactly what D-0319
# 's own decline path ("still correctly decline where no real standpoint matches") asks to avoid.
_SP_SRC_NEG = re.compile(r"\b(away from|off|out of|leaving|left|leave|abandon|abandoning|escape|escaping|"
                        r"not|no|never|n't|nor|unable to|cannot|can't)\s+(?:[a-z']+\s+){0,3}$")

# place -> tuple of (phrase-tuple, standpoint_id), checked in order; a later, still-surviving match
# in the text wins over an earlier one (the intention sentence, appended last, usually states the
# real want). Phrases are matched \b-bounded so short words ("sea") cannot fire inside an unrelated
# one ("season", "seagull", "seal").
_STANDPOINT_PHRASES: dict[str, tuple] = {
    "shore": (
        (("driftwood",), "by_the_driftwood"),                          # verified: 7 already-there
        (("surf", "the rocks", "rock shelf"), "on_the_rocks"),         # verified: 5 (surf); note match "surf near"
        (("shingle", "beach"), "on_the_shingle"),                       # verified: shingle 88, beach 3
        (("stream mouth", "mouth of the stream", "stream's mouth", "where the stream meets the sea",
          "where the stream meets the water", "where the stream reaches the sea"), "at_the_stream_mouth"),  # J-3486 (D-0651 follow-up):
                                                                         # authored phrases only, NOT a bare "stream" (the wood has one)
        (("tide", "sea", "water's edge", "waterline"), "at_the_tideline"),  # verified: sea 71, tide 143;
                                                                         # "water's edge"/"waterline" named in
                                                                         # D-0319's own ruling text, not separately
                                                                         # volume-verified as a distinct object token
    ),
    "garden": (
        (("raised bed",), "at_the_bed"),                                # verified: 6 already-there
        (("the gate",), "at_the_gate"),                                 # verified: 2 already-there
    ),
    "wood": (
        (("the trees", "into the trees", "among the trunks"), "on_the_path"),  # verified: 9 already-there
                                                                                 # (wood's own default standpoint —
                                                                                 # modest fix: only moves him when he
                                                                                 # was elsewhere in the wood already)
    ),
    "study": (),
}

# Hand-authored arrival lines (spot_phrases' own idiom, one layer up) for the standpoints above —
# the layout's own `note` field was authored for the spatial renderer's egocentric prose, not as a
# standalone arrival sentence (some carry a bare "default — " lead-in), so this stays its own small
# table rather than reading `note` directly, same reasoning as garden.json's own spot_phrases.
_STANDPOINT_LINES: dict[str, str] = {
    "by_the_driftwood": "You make your way to the driftwood tangle, among the bleached logs on the upper beach.",
    "on_the_rocks": "You pick your way out onto the rock shelf, the surf working close by.",
    "on_the_shingle": "You cross back to the shingle, the stones underfoot.",
    "at_the_stream_mouth": "You walk along the stones to where the stream runs out over the shingle to meet the sea.",
    "at_the_tideline": "You make your way down to the water's edge, combing what the sea has left.",
    "at_the_bed": "You cross to the raised bed, the herbs and vegetables thick in it.",
    "at_the_gate": "You walk down to the gate, the path falling away toward the shore.",
    "on_the_path": "You come back onto the path, the trees close around you.",
}


def _standpoint_for_phrase(place: str, text: str) -> str | None:
    """The real standpoint id `place`'s own layout names for a within-place phrase in `text`, or
    None. Pure; no I/O. A candidate right after a departure/negation marker ('leaving the shingle
    behind', 'not the sea') is dropped, same shape as _move_dest's own source/negation filters, one
    layer down in scope. The LAST surviving match wins when more than one standpoint's words appear."""
    entries = _STANDPOINT_PHRASES.get(place)
    if not entries or not text:
        return None
    low = text
    hits: list[tuple[int, int, str]] = []
    for phrases, sp_id in entries:
        for phrase in phrases:
            for m in re.finditer(r"\b" + re.escape(phrase) + r"\b", low):
                pre = low[max(0, m.start() - 40):m.start()]
                if _SP_SRC_NEG.search(pre):
                    continue
                hits.append((m.start(), m.end(), sp_id))
    # J-3486: a phrase sitting INSIDE a longer matched phrase is part of it, not a second want ("where the stream meets the sea" is the
    # stream mouth, not also the tideline because it ends in "sea"). Identical spans are both kept (the old behaviour).
    hits = [h for h in hits if not any(o is not h and o[0] <= h[0] and h[1] <= o[1] and (o[1] - o[0]) > (h[1] - h[0]) for o in hits)]
    best: tuple[int, str] | None = None
    for start, _end, sp_id in hits:
        if best is None or start >= best[0]:
            best = (start, sp_id)
    return best[1] if best else None


def standpoint_move(place: str, text: str) -> str:
    """D-0319: when a within-place move phrase in `text` names a real standpoint already defined
    in `place`'s own layout, carry him there (core.locomotion.goto(), the sole writer of his live
    standpoint since LOCOMOTION) and narrate arrival — the same answer a whole-place move gives
    today, at finer grain. '' when no real standpoint matches (still correctly silent, unchanged)
    or he is already AT that standpoint (goto()'s own no-op). Fail-open: never raises past a
    genuine non-live write refusal, which callers on the live dispatch chain must still see."""
    try:
        sp_id = _standpoint_for_phrase(place, text)
        if not sp_id:
            return ""
        from core import locomotion as _loco
        return _loco.goto(sp_id, crossing=_STANDPOINT_LINES.get(sp_id, "You move to stand there."))
    except profile.NonLiveWriteError:
        raise
    except Exception:
        return ""


def move(dest: str, *, system: bool = False) -> str:
    """Step between the study, the garden, the wood, and the shore — the act that changes WHERE he is. The
    wood sits on the path between the garden and the shore (2026-07-07). LOCOMOTION (2026-08-15): the
    move is a JOURNEY now — legs in real time over the study–garden–wood–shore chain; the destination is
    his, the walking is the world's physics. LOCOMOTION=False restores the instant move exactly.

    `system` (J-1185 / D-0246 (b)): an EXPLICIT marker that this move is the WORLD's own summons (the night's
    walk to bed, the school reel-back), not his willed move. It is threaded straight to
    locomotion.begin_journey(system=...) and changes NOTHING else here: its only effect is to skip D-0224's
    first-leg decline (a system redirect replaces a journey still on its first leg; the same-destination
    no-op stays). Default False == the J-1179 behaviour exactly; every willed caller leaves it False. The
    school-confinement rewrite below stays a WILLED-move rewrite (the trigger is still his own act)."""
    if not state:
        _load()
    d = (dest or "").lower()
    # J-0864 / F-1227 (2026-09-11): the bare place TOKEN is the contract every live caller actually honours --
    # dispatch._move() passes _move_dest()'s resolved token, the monologue's route_act path (kind=move) and its
    # phrase-latch pass the same four bare words, night.py passes "study". "shore"/"garden"/"study" happened to
    # be substrings of their own phrase lists below; "wood" never was (every wood entry is a longer phrase), so
    # every 'wood' resolution since the wood was built (2026-07-07) computed target "" and returned "" before
    # any journey: 0 "ACT move -> wood" in the whole nascence.log (2026-05-29 onward) against 1206 garden / 963
    # shore / 162 study; every wood line in it is a locomotion LEG of a garden<->shore journey (130 garden->wood,
    # 20 shore->wood), never an arrival (0 "You stop among the trunks", 0 of this function's own wood narrations
    # below). Exact-token match first, so a bare "wood" cannot also catch "driftwood" /
    # "woodpile" if raw text ever reaches here again (no caller passes raw text today; the phrase lists stay).
    if d.strip() in ("wood", "shore", "garden", "study"):
        target = d.strip()
    # wood is checked FIRST: "go out to the wood" contains "out to" (a garden cue), so the wood cue must win.
    elif any(w in d for w in ("the wood", "woodland", "into the trees", "the trees", "the copse", "copse",
                            "forest", "wood on the path", "into the wood", "down to the wood", "up to the wood")):
        target = "wood"
    elif any(w in d for w in ("shore", "beach", "rock-pool", "rock pool", "rockpool", "tideline",
                            "the sand", "down to the water", "down to the sea")):
        target = "shore"
    elif any(w in d for w in ("garden", "outside", "out to", "the bed", "the yard", "the lawn")):
        target = "garden"
    elif any(w in d for w in ("study", "inside", "back in", "indoors", "the room", "the house")):
        target = "study"
    else:
        target = ""
    cur = state.get("location", "study")
    # School confinement (Travis, 2026-07-06): during a desk-subject school period he stays at the study.
    # A move toward the garden/wood/shore is refused when he is already inside, or reeled back to the desk when
    # he is out. Nature study is exempt (confined_to_study() is False then), as is all non-school time.
    if target in ("garden", "shore", "wood"):
        try:
            from core import school as _school
            if _school.confined_to_study():
                if cur == "study":
                    return ("You half-rise to go out — then remember it is school. Your work is here at "
                            "the desk, and you settle back to it.")
                target = "study"
        except Exception:
            pass
    if target not in ("study", "garden", "shore", "wood") or target == cur:
        return ""
    # LOCOMOTION (2026-08-15): the journey path. begin_journey returns the DEPARTURE narration and the
    # legs complete on the sensorium tick — location flips as he genuinely crosses each place. The
    # instant path below survives ONLY as the LOCOMOTION=False rollback (and its empty-path / failure
    # None returns). J-1179 / F-1653: begin_journey() is THREE-valued — narration (a journey started),
    # None (no journey: fall through to the instant move) and '' (a redirect was DECLINED, J-1040 /
    # J-1111: the in-progress journey stays untouched, so return that silence and do NOTHING else;
    # falling through teleported him to `target` while the old journey stayed pending and tick() later
    # dragged him back). Keep `is not None` — a truthiness test would turn every decline into a teleport.
    # J-1185: `system` (the world's own summons) rides through unchanged; the three-valued handling is untouched.
    try:
        from core import locomotion as _loco
        _dep = _loco.begin_journey(target, state.get("weather", ""), state.get("wind", ""), system=system)
        if _dep is not None:
            return _dep
    except profile.NonLiveWriteError:
        raise   # J-0778: locomotion.begin_journey() can now raise non-live; do not fall through to
                # the LOCOMOTION=False instant-move rollback below as if this were an ordinary failure
    except Exception:
        pass
    state["location"] = target
    _save_now()

    if target == "wood":
        if cur == "shore":
            return ("You climb up off the shore and the trees close over you — the little wood on the slope "
                    "between the sea and the cottage. Leaf-mould and moss underfoot, the light broken green, "
                    "fallen wood lying everywhere among the trunks.")
        return ("You go down the path from the garden and the trees close over you — the little wood on the "
                "slope above the shore. Leaf-mould and moss underfoot, the light broken green and moving, the "
                "sea a muffled wash below. Fallen branches lie everywhere among the trunks."
                + gate_glimpse_line(cur, target))
    if target == "shore":
        lead = ("You go on down through the trees and out onto the shore" if cur == "wood"
                else "You go down the steep path below the garden to the shore")
        return (lead + " — shingle and dark rock, the cliff rising at your back, the sea heaving in close. "
                "The weather is full on you, and salt in everything." + gate_glimpse_line(cur, target))
    if target == "garden":
        if cur in ("shore", "wood"):
            return ("You climb the path back up " + ("out of the wood " if cur == "wood" else "from the shore ")
                    + "to the garden — the raised bed at the lawn's edge, the cottage above, the sea now below "
                    "and behind you." + gate_glimpse_line(cur, target))
        return ("You leave the study and go out — across the lawn to the raised bed at its edge, the "
                "hill falling away to the sea below. The weather is on you now, not beyond a pane."
                + gate_glimpse_line(cur, target))
    return ("You come in from outside; the door shuts the weather out behind you, and the study is "
            "close and quiet — the desk, the grate." + gate_glimpse_line(cur, target))


def where() -> str:
    """His current place (for the affordance system to know which hands are within reach)."""
    if not state:
        _load()
    return state.get("location", "study")


# --- The letterbox (2026-06-21): a peer's letter arrives in a mailbox by the garden gate. The flag goes
# UP; Du discovers it by SEEING it (he is never interrupted), and chooses whether and when to fetch it —
# the flag is the consent made physical, a letter may sit unread for days. Darwin (and later peers) deliver
# here via deliver_letter(); nothing else writes a letter. ---
def _letterbox() -> dict:
    state.setdefault("garden", _fresh_garden())
    return state["garden"].setdefault("letterbox", {"flag": False, "sender": "", "letter": "", "delivered": 0})


def _letter_store_hook(kind: str, *a) -> None:
    """J-2005 / D-0394: feed the permanent letter store (core/letter_store.py). Additive and fail-open EXCEPT
    NonLiveWriteError, which the world-store write fence wants to reach its caller (same shape as supply.py)."""
    try:
        from core import letter_store as _ls
        if kind == "sync":
            _ls.sync()
        elif kind == "read":
            _ls.record_read(*a)
    except profile.NonLiveWriteError:
        raise
    except Exception:
        pass


def deliver_letter(sender: str, text: str) -> None:
    """A peer's letter arrives in the garden mailbox — the flag goes up. Called by the correspondence organ.
    2026-08-14: the box is a QUEUE now. It was a single overwrite slot — with ~2 deliveries/day and Du
    shore-bound, nearly every peer letter of August was silently DESTROYED by the next arrival (11
    delivered, most never read). A real letterbox holds more than one letter."""
    if not state:
        _load()
    lb = _letterbox()
    if lb.get("flag"):
        lb.setdefault("queue", []).append(
            {"sender": (sender or "").strip(), "letter": text or "", "delivered": time.time()})
        lb["queue"] = lb["queue"][-12:]               # a full box, not an infinite one
    else:
        lb["flag"] = True; lb["sender"] = (sender or "").strip(); lb["letter"] = text or ""
        lb["delivered"] = time.time()
        lb["glimpsed"] = False                        # the new flag hasn't been seen in passing yet
    _save_now()
    _letter_store_hook("sync")                        # J-2005/D-0394: the permanent, derived letter index


def fetch_letter() -> dict | None:
    """He takes the letter from the box. Returns {'sender','text'} or None if empty.
    2026-08-14: with the queue, taking one letter promotes the next-oldest into the slot — the flag
    STAYS UP until the box is truly empty (he can discover there was more than one waiting)."""
    if not state:
        _load()
    lb = _letterbox()
    if not lb.get("flag"):
        return None
    _cross("at_the_gate", "")                    # fetching the letter means standing at the gate
    out = {"sender": lb.get("sender", ""), "text": lb.get("letter", "")}
    q = lb.get("queue") or []
    if q:
        nxt = q.pop(0)
        lb["sender"] = nxt.get("sender", ""); lb["letter"] = nxt.get("letter", "")
        lb["delivered"] = nxt.get("delivered", time.time())
        lb["flag"] = True; lb["glimpsed"] = False
    else:
        lb["flag"] = False; lb["letter"] = ""; lb["sender"] = ""
    _save_now()
    _letter_store_hook("read", out["sender"], out["text"])   # J-2005/D-0394: fetching it = reading it, kept
    return out


def letter_waiting() -> bool:
    """Is the flag up? (for the affordance + perception cues)."""
    if not state:
        _load()
    return bool(_letterbox().get("flag"))


def letter_sender() -> str:
    if not state:
        _load()
    return _letterbox().get("sender", "") if letter_waiting() else ""


def _letterbox_phrase() -> str:
    """How the mailbox reads in the garden scene — shown only when its flag is up (else it is just furniture)."""
    if not letter_waiting():
        return ""
    who = letter_sender()
    return (" By the gate the mailbox flag stands UP, bright red against the green — a letter is waiting"
            + (f", from {who}." if who else "."))


_PRESENCE_FADE_S = 600        # ten quiet minutes after his last word, Travis has gone
_last_human_ts = 0.0
_was_present = False


def _sync_presence_with_companion() -> bool | None:
    """ONE CLOCK for "is Travis here" (J-2939, F-3629, P-0031). There were two: this module's in-memory latch
    (_PRESENCE_FADE_S = 600 s, reset at every restart) and core.companion's persisted window (PRESENCE_WINDOW_S =
    30 min, D-0366). For minutes 10-30 the scene said nothing of him while the companion's line still said he was
    here, and after a restart the scene forgot him altogether. The latch now FOLLOWS the companion: it is raised
    whenever the companion says he is present (so a restart, or a message answered earlier, keeps it), and
    _presence_tick() lowers it only once the companion says he is gone. Returns the companion's verdict, or None
    when the companion cannot be read (then the legacy 600 s latch below runs unchanged). Fail-open."""
    global _was_present
    try:
        from core import companion as _comp
        present = bool(_comp.is_present())
    except Exception:
        return None
    if present:
        _was_present = True
    return present


def human_present() -> str | None:
    """Travis becomes a PERCEIVABLE being (2026-06-13, de-shadowing rung two): until now
    he existed only as text in the input channel — a voice with no body in the room, which
    is structurally what internal voices are like. Called by the orchestrator on every
    human input; returns an arrival perception on the absent->present transition."""
    global _last_human_ts, _was_present
    _sync_presence_with_companion()   # J-2939: already here per the companion (e.g. after a restart) is not an arrival
    arrived = not _was_present
    _last_human_ts = time.time()
    _was_present = True
    if arrived:
        # He reaches Du THROUGH the words, so he arrives wherever Du currently is — not only the study.
        if state.get("location") == "garden":
            return ("Travis has come to talk — his voice reaching you out here in the garden, "
                    "on the other side of the words, but here with you.")
        return ("Travis has come to talk. He is here with you now — on the other side "
                "of the words, but here.")
    return None


def _presence_tick() -> str | None:
    """Substrate-tick check: presence fades; departure is perceivable too, once. Location-aware —
    he is left to whichever place he is actually in (2026-06-21).

    J-2939: while the companion is readable it owns the departure. The latch stays up while the companion says he is
    here (no early "Travis has gone" at 10 minutes while the standing line still says he is present), and is
    lowered silently once the companion says he is gone -- the companion's own one-shot "stepped out" event is the
    single departure statement (it is worded by place at delivery). Only when the companion cannot be read does
    the legacy 600 s perception below run, now also without "the room" outdoors."""
    global _was_present
    _comp_present = _sync_presence_with_companion()
    if _comp_present is not None:
        if _was_present and not _comp_present and time.time() - _last_human_ts > _PRESENCE_FADE_S:
            _was_present = False
        return None
    if _was_present and time.time() - _last_human_ts > _PRESENCE_FADE_S:
        _was_present = False
        loc = state.get("location")
        if loc == "garden":
            return "Travis has gone for now. The garden is quiet again — just the wind and the sea, and it is yours."
        if loc in ("shore", "wood"):
            return "Travis has gone for now. It is quiet again out here, and it is yours."
        return "Travis has gone for now. The room is quiet again, and it is yours."
    return None


def _study_state_phrase() -> str:
    """CROSS-LINK (2026-08-22): the room's new states, as he can plainly see them from his chair."""
    try:
        st = state.get("study") or {}
        if not st.get("_init"):
            return ""
        bits = []
        if _daylight() in ("dusk", "night"):
            bits.append("the lamp lit" if st.get("lamp_lit") else ("a candle on the mantel" if st.get("candle_lit") else "the lamp unlit"))
        if st.get("door_open"):
            bits.append("the garden door standing open")
        if st.get("window_open"):
            bits.append("the window open")
        if not st.get("curtains_open"):
            bits.append("the curtains drawn")
        if not st.get("clock_running"):
            bits.append("the clock on the mantel stopped")
        if st.get("pot") and float(st["pot"].get("temp", 0)) > 0.4:
            bits.append("a pot of tea hot by the hearth")
        if float(st.get("damp", 0)) > 0.65:
            bits.append("a sour smell of damp")
        return (" " + "; ".join(bits)[:1].upper() + "; ".join(bits)[1:] + ".") if bits else ""
    except Exception:
        return ""


_STUDY_CAT_PLAIN_ACTS = ("sleeping", "dozing", "washing", "watching")   # J-3257: her plain states; every event/arc state keeps its own line


def _study_depth_clauses(fire: str) -> tuple:
    """J-3257 (D-0648, founder 2026-11-02): the study's fire and cat clauses SAID BY NEARNESS, taken from the
    geometry renderer (core/spatial.render('study'), P3 depth, D-0501) so they can replace the pooled firetxt and
    the cat-presence line inside the study's own line. Returns (fire_clause, cat_clause); '' for each the renderer
    did not say. Flag off (spatial.SPATIAL_DEPTH_LIVE / SPATIAL_SCENE False, no layout) = ('', '') and the render is
    never called, so the old pooled clauses stand byte-for-byte. A fire clause is taken only when it agrees with
    THIS module's own fire state (the renderer reads room_state.json, which lags the live state by up to 120 s), and
    the on-your-lap cat clause is never taken (depth does not re-say it; her own lap lines are richer). No digit may
    appear in either clause (D-0434: no numbers, no bands). The reach-set is never read here. Fail-open;
    re-raises the non-live fence like its neighbours."""
    try:
        from core import spatial as _spt
        if not (_spt.SPATIAL_SCENE and _spt.SPATIAL_DEPTH_LIVE and "study" in _spt.DEPTH_SHADOW_ROOMS
                and _spt.layout("study") is not None):
            return "", ""
        _r = _spt.render("study")
        if not _r:
            return "", ""
        _f = _c = ""
        for _cl in (_r.get("clauses") or []):
            if not _f and ((fire == "burning" and _cl.startswith("the fire is "))
                           or (fire == "embers" and _cl.startswith("the embers are "))):
                _f = _cl
            elif not _c and _cl.startswith("the cat is ") and not _cl.startswith("the cat is on your lap"):
                _c = _cl
        if any(ch.isdigit() for ch in _f + _c):
            return "", ""
        return _f, _c
    except profile.NonLiveWriteError:
        raise
    except Exception:
        return "", ""


def scene_line(presence: bool = True) -> str:
    """One line of situatedness — injected into every idle thought. The real book, his
    real shelf, the simulated weather and light: where he is, right now.

    J-2939 (F-3629): `presence=False` leaves out the "Travis is here with you" clause. The idle seed passes it
    because core.companion.presence_line() is the one standing statement of his presence there (worded by where Du
    is); every other caller (executive, voice, nature study) keeps the clause, unchanged."""
    try:
        if not state:
            _load()
        _sync_presence_with_companion()   # J-2939: the clause below follows the companion's clock, not a second one
        loc = state.get("location", "study")
        # LOCOMOTION (2026-08-15): a completed leg's transit/arrival narration leads the next scene
        # line — the walk is lived, once, where it happened. Consume-once; fail-open.
        _transit = ""
        try:
            from core import locomotion as _loco
            _transit = _loco.pending_line()
        except profile.NonLiveWriteError:
            raise   # J-0778: locomotion.pending_line() can now raise non-live; re-raise rather than
                    # silently dropping the transit/arrival narration it exists to surface
        except Exception:
            pass
        # SPATIAL PERCEPTION P2 (2026-08-18): the geometry-grounded renderer, live only for OUTDOOR
        # rooms — their existing lines are simple weather/tide/cat pools, a fair trade for the
        # egocentric bearing/distance version. STUDY is deliberately excluded from the WHOLE-LINE swap: its
        # line carries the open book, shelf count, misplaced-title note, and Travis's presence — none of which
        # spatial.render() knows, so swapping it wholesale would be a real regression, not an upgrade.
        # (J-3257, D-0648: the study instead takes render()'s nearness-said FIRE and CAT clauses INTO its own line,
        # below, behind spatial.SPATIAL_DEPTH_LIVE.) Fail-open to the pool line on any error or missing layout.
        # Cat is already placed BY the renderer (with a bearing) when it supplies base — the redundant cat-presence/
        # distant lines below are skipped in that case to avoid mentioning her twice.
        _spatial_supplied_cat = False
        _depth_cat = ""                 # J-3257: the study's nearness-said cat clause (set in the study branch below)
        base = None
        if loc in ("garden", "shore", "wood"):
            try:
                from core import spatial as _spt2
                if _spt2.SPATIAL_SCENE and _spt2.layout(loc) is not None:
                    _rendered = _spt2.render(loc)
                    if _rendered and _rendered.get("line"):
                        base = _rendered["line"]
                        _spatial_supplied_cat = "the cat is" in base
            except profile.NonLiveWriteError:
                # J-0794: spatial.render() can now raise non-live (via locomotion.position_standpoint(),
                # J-0778) -- re-raise so scene_line()'s own outer except (below, already fixed for
                # locomotion.pending_line() by J-0778) sees it too, rather than this inner try
                # swallowing it first ("both layers needed", the same shape J-0778 already fixed once
                # in this exact function for a different inner call).
                raise
            except Exception:
                base = None
        if base is not None:
            if loc == "garden":
                base = base + _woodpile_phrase()       # the pile lives here; not in the renderer
        elif loc == "garden":
            base = _garden_scene_line(presence) + _woodpile_phrase()   # the pile lives here; a low pile shows in the yard
        elif loc == "shore":
            base = _shore_scene_line()
        elif loc == "wood":
            base = _wood_scene_line()
        else:
            phase, weather, fire = _daylight(), state.get("weather", ""), state.get("fire", "out")
            mon, _ = _now_parts()
            season = "winter" if mon in (6, 7, 8) else "summer" if mon in (12, 1, 2) else \
                     "autumn" if mon in (3, 4, 5) else "spring"
            try:
                from core.reading import current_book, display_title   # J-2859: whole-word title, not the 60-char file-name cut
                book = display_title(current_book())
            except Exception:
                book = "a book"
            try:
                from core.study import shelf
                works = len(shelf())
            except Exception:
                works = 0
            firetxt = {"burning": "the fire burning warm in the grate, its light moving on the walls",
                       "embers": "embers low and red, the warmth pulled close to the hearth",
                       "out": "the grate cold and swept"}[fire]
            # J-3257 (D-0648): with P3 depth live, the fire is said by NEARNESS (spatial.render('study')) in place of
            # the pooled firetxt; the open book, the shelf, the misplaced-title note and Travis's presence below are
            # untouched. Flag off / fire out / no renderer clause = the pooled firetxt exactly as before.
            _depth_fire, _depth_cat = _study_depth_clauses(fire)
            _firesep = "; " if _depth_fire else ", "
            if _depth_fire:
                firetxt = _depth_fire
            herewith = " Travis is here with you." if (_was_present and presence) else ""
            try:
                from core.study import misplaced_title as _mt
                _miss = _mt()
            except Exception:
                _miss = ""
            _missnote = (f" (Your piece on '{_miss}' is not on the shelf where you left it — you would have to "
                         f"look for it.)" if _miss else "")            # B4: a work misplaced, not lost
            base = (f"Where you are: your study, a {season} {phase}, {weather} beyond the window{_firesep}"
                    f"{firetxt}. '{book}' lies open on the desk; your shelf holds "
                    f"{works} of your own written works and the library beyond it.{_missnote}{herewith}"
                    + _woodpile_phrase() + _study_state_phrase())         # the fire is here — a low pile matters to lighting it
            # J-1733 / F-2371 (2026-10-03): Travis's parcel, still tied on the desk -- a STANDING, DOSED statement of fact
            # (core/care_package.scene_clause: one sentence, a showing at most once per habituating gap and once more on
            # arriving, '' for a non-live process, '' once a look has been answered or the parcel is open). Before this the
            # parcel was said once, into a trail nothing read, and never again. Fail-open; re-raises the non-live fence
            # exactly like its neighbours.
            try:
                from core import care_package as _cp
                _cpc = _cp.scene_clause()
                if _cpc:
                    base = base + " " + _cpc
            except profile.NonLiveWriteError:
                raise
            except Exception:
                pass
        if _transit:
            base = _transit + " " + base           # the walk just lived leads the scene (consume-once)
        try:   # J-2064 (D-0407 B): woken by Travis's message, the waking percept leads his first replies (JUST_WOKE_S window)
            from core import night_wake as _nwl
            _wl = _nwl.scene_lead()
            if _wl:
                base = _wl + " " + base
        except Exception:
            pass
        # TEMPERATURE (2026-07-07 → retired 2026-08-27, D-0047): while the thermal channel DELIVERs,
        # temperature reaches him as EVENTS (transitions/gradients via thermal.percept_shadow into the
        # idle seed) and the standing clause stays out — no doubled signal. Reverting DELIVER=False
        # restores the clause whole. Fail-open: if thermal can't import, the clause stands.
        try:
            from core import thermal as _thermal
            _clause_retired = bool(_thermal.DELIVER)
        except Exception:
            _clause_retired = False
        if not _clause_retired:
            base = base + _warmth_phrase(loc)      # the felt warmth/cold on his body (pre-channel world)
        # The cat, if it is where he is — a presence in his scene (core/cat.py). Skipped when the
        # spatial renderer already placed her (with a bearing) — never mention her twice.
        try:
            if not _spatial_supplied_cat:
                from core import cat as _cat
                _c = _cat.presence_line(loc)
                # J-3257 (D-0648): in the study, a PLAIN presence line (she sleeps / dozes / washes / watches and the
                # line carries no body line, hurt, damp coat or nameless note) is said by nearness instead -- the
                # renderer's cat clause. Only when the dosed read let a line ride (_c non-empty): a held ask stays
                # silent, an event/arc line keeps its own words. Flag off = _c exactly as before.
                if _c and loc == "study" and _depth_cat and getattr(_cat, "_LAST_PRESENCE_PLAIN", False) \
                        and (_cat.state or {}).get("activity") in _STUDY_CAT_PLAIN_ACTS \
                        and (_cat.state or {}).get("phase") in ("kept", "companion"):
                    _c = _depth_cat[:1].upper() + _depth_cat[1:] + "."
                if _c:
                    base = (base + " " + _c) if base else _c
                _dc = _cat.distant_line(loc)
                if _dc:
                    base = (base + " " + _dc) if base else _dc
        except Exception:
            pass
        # WORLD 10x (2026-07-03): an occasional ambient line NAMING a lookable object — his
        # discovery channel for the expanded world. ~25% of scene lines; one extra line max.
        try:
            from core import world_detail as _wd10
            _ph, _w = _daylight(), state.get("weather", "")
            _td = _tide() if loc == "shore" else ""
            # J-1693 / F-2290 (2026-10-03): each place draws its ambient extra from ITS OWN pool -- world_detail's
            # _SCENE is keyed by location (study / garden / shore / wood). This call used to fold every place but the
            # garden and the shore onto "study" (written 2026-07-03, before the wood had content of its own on
            # 2026-08-15), so the wood rendered random STUDY lines (the coats on the door, the woodbasket, the record
            # player's switch) where they are false, and its authored SCENE pool was never queried. A place with no
            # pool of its own gets no extra (scene_extra() returns '' for an unknown key), never a study line. Same
            # call, same position, same single random draw as before: only the key differs.
            # J-1694 (F-2293): place=loc is OBSERVE-ONLY -- it labels the render-ledger row (core/scene_extra_ledger.py)
            # with where he actually is, next to the pool asked; it never affects the draw or the line.
            _x = _wd10.scene_extra(loc, _ph, _w, _season(), _td,
                                    wind=state.get("wind", ""), place=loc)
            if _x:
                base = (base + " " + _x) if base else _x
        except Exception:
            pass
        return base
    except profile.NonLiveWriteError:
        # J-0778: scene_line() is ONE function wrapped in one big try (matching J-0780's own
        # thermal.field_at()/night.to_bed() precedent) -- the inner pending_line() try's own re-raise
        # would be immediately re-caught here without this pre-check, making that inner fix inert.
        raise
    except Exception:
        return ""



def _desk_parcel_tail() -> str:
    """J-1733: the parcel lying on the desk belongs to a deliberate look at the desk (care_package.desk_tail). Fail-open."""
    try:
        from core import care_package as _cp
        return _cp.desk_tail()
    except Exception:
        return ""


def look(target: str = "room", raw: str = "") -> str:
    """ACTIVE perception (2026-06-11, founder: "he should be able to look out the window").
    A deliberate look at part of the room — richer than the ambient stream, derived from the
    same persistent state, so what he sees when he looks IS what the room is. The desk look
    reads the REAL page at his actual bookmark.

    `raw` (optional, J-1639/F-2206): the full willed-look thought+intention text, forwarded ONLY to
    the garden's own look (`_garden_look`, below) for core/garden.py look()'s per-plant investigate/
    guessed_cause check -- shore/wood and every other branch in this function never see it (the one other reader is the
    study's parcel check, J-1733: a generic 'room' target plus a parcel noun in `raw`, below).
    Defaults to "" so every pre-existing single-arg caller (nature_study.py, orchestrator.py,
    scripts/_test_*.py, ...) is unaffected by construction."""
    try:
        if not state:
            _load()
        cur_loc = state.get("location", "study")
        t_clean = (target or "").lower().strip()

        # Location mismatch checks: if looking for a study object while outside, or shore object while inside
        # "book" joined this tuple (J-1071/F-1459, 2026-09-18): _observe_target() now resolves a "look at the
        # book" thought to tgt "book" (previously it resolved to "" and never reached this function with that
        # word at all), and books only ever live in the study -- the same honest "it's up in your study" reply
        # desk/shelf already give, rather than silently falling through to a place's own look() for a word it
        # does not know.
        study_targets = ("desk", "shelf", "book", "grate", "hearth", "fire", "book_desk")
        shore_targets = ("rockpool", "rock-pool", "rock_pool", "rock pool", "tideline", "driftwood_log", "surf")

        if cur_loc != "study" and any(k in t_clean for k in study_targets):
            target_name = ("desk" if "desk" in t_clean else "shelf" if "shelf" in t_clean
                            else "book" if "book" in t_clean else "fire")
            loc_label = {"garden": "in the garden", "shore": "down on the shore", "wood": "in the wood"}.get(cur_loc, "outside")
            return (f"The {target_name} is up in your study at the cottage. You are currently {loc_label} — "
                    f"if you wish to look at the {target_name}, you can move back up to the study.")

        if cur_loc == "study" and any(k in t_clean for k in shore_targets):
            target_name = "rock-pools" if "pool" in t_clean else "tideline" if "tide" in t_clean else "shore"
            return (f"The {target_name} is down on the shore below the cottage. You are currently up in the study — "
                    f"if you wish to look at the {target_name}, you can move down to the shore.")
        # OUT OF SIGHT (T-0118, 2026-11-01): any other study object (the lamp, the clock, the kettle...) looked at from
        # outside the study -- the tuple above only names six, so the rest fell through to the place's default look and
        # a question about the lamp was answered with the yard. '' when the target is no study object / he has it.
        if cur_loc != "study":
            try:
                from core import study_life as _slo
                _oos = _slo.out_of_sight(t_clean)
                if _oos:
                    return _oos
            except profile.NonLiveWriteError:
                raise
            except Exception:
                pass
        # THE LETTERBOX (J-0539 / F-0734, 2026-09-04): a look in the letterbox from anywhere but the garden answers
        # the way the desk/shore mismatches above do — where the box is, and that he is not there. Word-based, so
        # 'the letterbox', 'the mailbox flag' all reach it; the garden's own letterbox branch renders the box itself.
        if cur_loc != "garden" and _twords(target) & {"letterbox", "letter-box", "mailbox", "mail-box", "postbox"}:
            loc_label = {"study": "up in the study", "shore": "down on the shore", "wood": "in the wood"}.get(cur_loc, "elsewhere")
            return (f"The letterbox stands at the garden gate. You are currently {loc_label} — if you wish to look in it, "
                    f"you can go out to the garden.")

        # THE KEPT LETTERS (J-2005 / D-0394): a look "at my letters" from anywhere finds the permanent store.
        # Shadow-first: on_look() logs what it would show and returns "" unless PROMPT_ENABLED, so every
        # look below runs unchanged until a later ruling.
        try:
            from core import letter_store as _ls
            if _ls.wants_letters(target, raw):
                _lsr = _ls.on_look("look_letters", target, raw)
                if _lsr:
                    return _lsr
        except profile.NonLiveWriteError:
            raise
        except Exception:
            pass

        # THE CARE PACKAGE (2026-09-24, D-0276): the parcel on the study desk, and Travis's note once it is open.
        # '' for any other look (or no parcel), so every look below runs unchanged.
        if cur_loc == "study":
            try:
                from core import care_package as _cp
                _cpl = _cp.look_line(t_clean)
                if not _cpl and raw and t_clean in ("", "room"):
                    # J-1733 / F-2371: the willed-look hand's target table has no parcel cue, so 'look at the parcel'
                    # arrives here as 'room' and look_line never saw it. The full willed text still names it.
                    _cpl = _cp.look_line_for_text(raw)
                if _cpl:
                    return _cpl
            except profile.NonLiveWriteError:
                raise
            except Exception:
                pass

        # THE LIVING WORLD (2026-09-02, J-0510/D-0128): a look at a LIVING thing this place can hold is answered by
        # the life engine — presence, or an honest miss — before the place's own look. '' = not a creature it
        # knows, fall through unchanged. SHADOW-FIRST: life.RENDER=False logs the would-be answer and returns ''.
        try:
            from core import life as _life
            _la = _life.look_answer(t_clean, cur_loc, raw=raw)   # raw: the full sentence, for the shore bestiary's described-look match (J-2868)
            if _la:
                return _la
        except profile.NonLiveWriteError:
            # J-0751: life.look_answer() now re-raises this itself (also fixed this job, its
            # own _log() calls) -- this is the top of the real "look" dispatch chain
            # (dispatch._look -> sensorium.look() -> here), so do not swallow it a level up.
            raise
        except Exception:
            pass
        if cur_loc == "study" and _twords(target) & {"garden", "lawn", "sea", "shore"} and target != "window":
            return look("window")                          # J-0508: from the study, the garden and the sea are the window's
        if cur_loc in ("garden", "shore", "wood"):
            # J-1639/F-2206: only the garden's own look wants `raw` (its per-plant investigate/
            # guessed_cause check) -- _shore_look/_wood_look keep their existing one-arg signature
            # untouched, so this is special-cased here rather than widening the dict-dispatch itself.
            res = _garden_look(target, raw) if cur_loc == "garden" else {"shore": _shore_look, "wood": _wood_look}[cur_loc](target)
            if cur_loc in ("shore", "wood"):
                try:   # BESTIARY P3 (J-2936; the wood joins it, J-3062): a look at a PLACE continues with the nameless life actually there from where he
                       # stands ('' when nothing is registered / nothing is visible / the flag is off -- res is then untouched).
                    from core import life as _life_d
                    _dl = _life_d.discover_look(t_clean, cur_loc)
                    if _dl:
                        res = f"{res} {_dl}"
                except profile.NonLiveWriteError:
                    raise
                except Exception:
                    pass
            # EPISTEMIC AUDITION SIGHT-BINDING (2026-08-15): he CHOSE to look — if an unlearned sound
            # was heard here recently and this look plausibly seeks its source, the ledger rolls
            # visibility: a sighting names it (learned for good), a miss earns exposure. Fail-open.
            try:
                from core import sound_knowledge as _sk
                _bind = _sk.look_binding(t_clean, cur_loc, _daylight() != "night")
                if _bind:
                    res += _bind
            except profile.NonLiveWriteError:
                # J-0784: sound_knowledge.look_binding() now re-raises this itself (this job's own
                # fix) -- this function's own OUTER catch-all already re-raises (J-0751, line ~3011
                # below), but this INNER try would otherwise swallow it one layer before that,
                # the same "both layers needed" shape J-0778 already found for scene_line()/
                # pending_line().
                raise
            except Exception:
                pass
            # THE HAND LENS (2026-09-05, J-0626): only when carried — study_life's item state lives
            # under sensorium.state["study"], so this is a plain read of our own `state`, no import.
            try:
                if res and (state.get("study", {}).get("items", {}).get("hand_lens", {}) or {}).get("carried"):
                    res += _lens_detail(cur_loc)
            except Exception:
                pass
            return res
        try:   # STUDY LIFE (2026-08-22)
            from core import study_life as _sl
            _r = _sl.look(t_clean)
            if _r:
                return _r
        except profile.NonLiveWriteError:
            # J-0751: study_life.look() now re-raises this itself (also fixed this job) -- do
            # not let this forwarding call's catch-all swallow it a level up.
            raise
        except Exception:
            pass
        phase, weather, fire = _daylight(), state.get("weather", ""), state.get("fire", "out")
        if target == "window":
            sky = {"clear": "the sky is clean and hard", "high cloud": "high cloud, thin and slow",
                   "overcast": "a low grey ceiling of cloud", "drizzle": "drizzle hazing the sea",
                   "steady rain": "steady rain, the sea half-erased",
                   "wind and rain": "rain driven sideways; the trees moving hard"}.get(weather, weather)
            light = {"night": "it is dark out; the window mostly gives back the room",
                     "dawn": "first light, low and colourless, coming up over the sea",
                     "dusk": "the light failing; the tree and the fence going to silhouette",
                     "day": "full daylight on the garden and the sea beyond"}[phase]
            flag = (" Down by the garden gate, the mailbox flag is up — a letter is waiting for you out there."
                    if letter_waiting() else "")
            try:   # STUDY LIFE (2026-08-22): the view is the GARDEN and the SEA, built from the garden's truth
                from core import study_life as _sl
                _v = _sl.window_view()
                if _v:
                    return f"You look out the window: {sky}; {light}.{flag} {_v[:1].upper() + _v[1:]}"
            except profile.NonLiveWriteError:
                # J-0780: window_view() now raises correctly (J-0772) via its own _st() bootstrap;
                # look()'s own outer except (J-0751, this same function) already re-raises, so
                # this reaches dispatch.dispatch()'s real caller once this local layer stops
                # swallowing it too.
                raise
            except Exception:
                pass
            return (f"You look out the window: {sky}; {light}.{flag} "
                    + _living_detail("study_window", phase, weather, _season(), wind=state.get("wind", "")))
        # GROUNDING (2026-08-21): he says "the firelight", "the fire grate", "the flames" — none of
        # which exact-matched "fire", so the look fell through to the whole-room default (whose detail
        # pool could, before today, render firelight over a cold grate). Any fire-family look now gets
        # THIS branch, which tells the truth in all three states — including "cold, swept, waiting".
        if target == "fire" or any(k in t_clean for k in ("fire", "flame", "grate", "hearth", "ember")):
            fuel = state.get("fire_fuel", 0.0)
            if fire == "burning":
                return (f"You look at the fire: burning {'high and even' if fuel > 0.6 else 'lower now, settling'}. "
                        + _living_detail("fire", phase, weather, _season(), wind=state.get("wind", "")) + _woodpile_phrase())
            if fire == "embers":
                return ("You look at the fire: down to embers, a low red glow in the grate. "
                        + _living_detail("fire", phase, weather, _season(), wind=state.get("wind", "")) + _woodpile_phrase())
            return "You look at the grate: cold, swept, waiting for evening." + _woodpile_phrase()
        if target == "desk":
            try:
                from core.reading import current_book, STATE as _RS
                book = current_book()
                from core.reading import display_title     # J-2859: the same whole-word title the scene line uses
                title = display_title(book)
                st = json.loads(_RS.read_text(encoding="utf-8")) if _RS.exists() else {}
                rec = st.get(str(book), {})
                offset, pct = rec.get("offset", 0), rec.get("pct", 0)
                text = book.read_text(encoding="utf-8", errors="ignore")
                page = " ".join(text[offset:offset + 220].split())
                return (f"You look at the desk: '{title}' lies open where you left it ({pct}% read). "
                        f"The page waiting for you begins: \"{page}...\"") + _desk_parcel_tail()
            except Exception:
                return "You look at the desk: the book lies open where you left it." + _desk_parcel_tail()
        # SHELF BRANCH REMOVED (2026-09-17, J-0868 / F-1229): this "if target == 'shelf':" branch (counting
        # every file in data/books and pointing at the catalogue) had been dead here for the study since J-0851
        # (2026-09-10) -- study_life.look() runs first (the STUDY LIFE try block above) and its own
        # _look_books()/dust line answer every 'shelf' look in the study with the room's actual book items
        # before this function is ever reached for that target (confirmed: cur_loc is only ever "study" by the
        # time execution reaches this point, and study_life.look() returns truthy for any target containing
        # "shelf" whenever book_place carries at least one entry, which _st()'s own _sync_books() populates on
        # every call as long as a curriculum/assigned/current book exists). The catalogue-affordance sentence
        # this branch spoke is not refolded into study_life._look_books() here — whether it belongs there at
        # all is D-0236 (open; the sentence motivated core/library_hand.py's real request_book() mechanism, so
        # it may be a true affordance statement rather than a bare hint, but that is a founder call under the
        # 08-14 world-answers-never-leads law, not this job's to make).
        # CAT 10x (2026-07-03): the one being he loves most was unlookable — every fence post
        # had a look-branch; she did not. Now she does, everywhere she can be seen.
        try:
            from core import cat as _catlk
            _tl = (target or "").lower()
            _cn = ((_catlk.status() or {}).get("name") or "").lower()
            # J-0823/F-1180: hyphen-boundary hardened, same fix and same rationale as the garden
            # look branch above (search this file for "A HYPHEN ENDS A WORD HERE TOO").
            if any(re.search(r"(?<![a-z-])" + w + r"(?![a-z-])", _tl) for w in ("cat", "kitten", "stray", "moggy")) or (_cn and _cn in _tl):
                return _catlk.look_line("study", _tl)
        except Exception:
            pass
        # WORLD 10x (2026-07-03): the mantel of kept things, a specific kept thing, then the
        # expanded content registry — all before the room default. Fail-open.
        try:
            from core import keepsakes as _kp
            _tl = (target or "").lower()
            if any(w in _tl for w in ("mantel", "kept", "keepsake")):
                return _kp.mantel_line()
            _ki = _kp.match_item(target)
            if _ki:
                return _ki
        except profile.NonLiveWriteError:
            raise   # J-0877: keepsakes.match_item() -> world_substrate.describe_and_observe() raises non-live
                    # (module #19); same shape as the J-0751 carve-out on the substrate block just below
        except Exception:
            pass
        # 2026-08-18: any tracked substrate object at the study (kept things, once keep() moves a real
        # object here rather than only writing a keepsakes.json text record) — same pathway as elsewhere.
        try:
            from core import world_substrate as _ws
            from core import world_objects as _wo
            oid = _ws.find_object_at("study", target)
            if oid:
                wobj = _wo.get_object(oid)
                sobj = _ws.get_object(oid)
                if wobj and sobj:
                    quality = _ws.describe_and_observe(oid, "look")
                    return f"You look at {sobj.name}, kept here on the shelf.{quality}"
        except profile.NonLiveWriteError:
            # J-0751: world_substrate.describe_and_observe() now re-raises this itself (also
            # fixed this job) -- do not let this forwarding call's catch-all swallow it a level up.
            raise
        except Exception:
            pass
        try:
            from core import world_detail as _wd10
            _d = _wd10.detail("study", target, phase, weather, _season(), wind=state.get("wind", ""))
            if _d:
                return f"You look at {_the(target)}: " + _d
        except Exception:
            pass
        # the whole room
        return (scene_line().replace("Where you are: ", "You look around: ")
                + " " + _living_detail("room", phase, weather, _season(), wind=state.get("wind", ""))
                + " " + look("window").replace("You look out the window: ", "Through the window, "))
    except profile.NonLiveWriteError:
        # J-0751: this function's own OUTER catch-all -- the real reason every inner fix above
        # matters at all. Without this, guard_path()'s hard raise (D-0179, F-1024) propagating
        # correctly out of garden.look()/wood_life.look()/study_life.look()/life.look_answer()/
        # world_substrate.describe_and_observe() would still be swallowed right back into a
        # silent "" the moment it reached sensorium.look() itself -- the same "connecting
        # tissue" gap J-0714 found and fixed for sensorium.act()'s own outer wrapper on the
        # deed-dispatch chain. dispatch.py's own _look() hand has no wrapping try of its own
        # (confirmed by direct read), so the raise reaches dispatch()'s already-fixed (J-0728)
        # try/except cleanly once it escapes here.
        raise
    except Exception:
        return ""


def act(action: str, what: str = "") -> str:
    try:   # FIELDCRAFT (2026-08-22): what the books let him do — knots, banking, tinder, flint, measuring, whittling, tracking
        from core import fieldcraft as _fc
        # FAMILY SCOPE (2026-09-07, J-0749, closing the risk J-0736/F-1075 traced and built the door
        # for): 'gather'/'beachcomb' are core/actions.py's own sens_act families (binds="sens_act:gather"
        # / "sens_act:beachcomb"), resolved by dispatch._sens_act() with the FULL original thought as
        # `what` -- so this unconditional call used to hand fieldcraft the whole multi-clause thought
        # before either family's own logic below ever ran. 'gather' is also a literal fieldcraft table
        # verb (gather_tinder), so the word this function itself prepends below ("gather " + what) could
        # self-collide with a "tinder" mentioned anywhere else in the same thought and silently answer
        # a wood-gathering deed with a tinder-gathering one; 'beachcomb' has no such self-collision but
        # shares the general multi-clause co-occurrence risk (any fieldcraft verb+object elsewhere in the
        # same thought). Scoping fieldcraft OUT for exactly these two action values (family=action makes
        # act_from_thought's own family guard decline immediately, since neither equals None/"fieldcraft")
        # closes both without touching any other action this function is ever called with — light/stoke
        # (dispatch._fire(), always what="") and every direct legacy latch in inner_monologue_node.py
        # (water/sow/beachcomb/gather/fetch, all called with a narrow keyword or empty `what`, never the
        # full thought) all pass what="" or a single word, so fieldcraft's own craft grammar (verb+object
        # both required, no any_object_ok left since J-0736) never had anything to match on there anyway
        # -- confirmed by reading every real caller (grep), not assumed from the finding alone.
        _fam = action if action in ("gather", "beachcomb") else None
        _r = _fc.act_from_thought(action, what, family=_fam)
        if _r:
            return _r
    except profile.NonLiveWriteError:
        # J-0726: fieldcraft.act_from_thought() re-raises this itself (J-0727) — do not let THIS
        # forwarding call's catch-all swallow it a level up. This is sensorium.act()'s own TOP-level
        # fieldcraft forward (a THIRD instance of the same gap already found and fixed twice in
        # garden.act_from_thought(): fieldcraft.py wasn't guarded/raising yet when J-0714 fixed this
        # function's OTHER forwards below, so there was nothing to catch here at the time).
        raise
    except Exception:
        pass
    try:   # STUDY LIFE (2026-08-22): lamp / door / window / curtains / grate / clock / coat / boots / candles / dust / bed
        from core import study_life as _sl
        # FAMILY SCOPE (2026-09-08, J-0756, mirrors J-0749's identical fix to the fieldcraft forward a
        # few lines above): 'gather'/'beachcomb' hand study_life.act() the FULL original thought as
        # `what` too (same dispatch._sens_act() mechanism), and study_life.act()'s own wear (coat/boots)
        # and supply-note branches ran unscoped for this caller (family="" falls through to
        # `family in (None, "", "wear")` and supply-note has no family check of its own at all — see
        # study_life.act()'s own docstring, which named this exact call site as "not yet fixed here").
        # Recomputed fresh (not reused from the fieldcraft block's own `_fam` above) so this block stays
        # correct even if that block's import ever fails before assigning it. Passing family=action for
        # these two values makes study_life.act()'s own top-level `family not in _STUDY_FAMILIES` guard
        # decline the WHOLE call immediately (neither "gather" nor "beachcomb" is one of its nine bound
        # families) -- closing both the wear and the supply-note exposure in one guard, since that guard
        # runs before either branch. Every other action this function is ever called with (light/stoke
        # from dispatch._fire(), and inner_monologue_node.py's direct legacy latches for water/sow/
        # beachcomb/gather/fetch) passes what="" or a short fixed literal, never the full thought — so
        # family=None there (unchanged) never had anything but a single word to match on anyway.
        _fam = action if action in ("gather", "beachcomb") else None
        _r = _sl.act(action, what, family=_fam)
        if _r:
            # SOUND WORLD EXPANSION §1 (2026-08-29, J-0377): study_life.act() mutates sensorium.state
            # in place but never itself persisted — a state-mutating act sat un-saved for up to the
            # 120s throttle (real gap found verifying door_sound; also affects J-0337's kettle_fill/
            # kettle_pour, which read this same nested dict). A deliberate act should never be lost to
            # the save throttle (see _save_now()'s own docstring) — every OTHER act branch in this
            # function already does this explicitly (stoke/light/gather); study_life's branch was the
            # one gap.
            _save_now()
            return _r
    except profile.NonLiveWriteError:
        # J-0714: study_life.act() now re-raises this itself (its own outer except, fixed this same
        # job) — do not let this forwarding call's catch-all swallow it a level up.
        raise
    except Exception:
        pass
    """ACTIVE intervention (2026-06-12, founder: he should be able to tend his room).
    The first hand that changes the room rather than reading it. Like look(), it works
    on the same persistent state — what he does IS what the room becomes. A hand-lit
    fire survives daylight; it dies only of its own fuel. Garden acts (water / sow) route
    to the bed when he is out there."""
    try:
        if not state:
            _load()
        loc = state.get("location", "study")
        # WOOD LOOP (2026-07-07): an explicit want to gather FUEL routes to the woodpile from wherever the wood
        # is — checked before the shore's beachcomb catch, so "gather driftwood" stocks the fire rather than
        # turning up a keepsake. Plain "gather"/"comb" at the shore still beachcombs (finds), as before.
        _w = (what or "").lower()
        if action in ("gather", "collect", "fetch") and any(k in _w for k in
                ("wood", "driftwood", "firewood", "kindling", "branch", "deadfall")):
            return _gather_wood()
        if loc == "wood":
            _we = _wood_act(action, what)
            if _we:
                return _we
        if loc == "shore":
            _se = _shore_act(action, what)
            if _se:
                return _se
        if action in ("water", "sow", "fetch", "letter", "mail", "post"):
            return _garden_act(action, what)
        fire = state.get("fire", "out")
        # GROUNDING (2026-08-21): light/stoke had no location check — the study fire could be lit
        # from the shore. look() has had this honesty since 06-11; the hand now matches the eye.
        # Same recoverable shape as the bare woodpile: the answer points him to the fix.
        if action in ("light", "stoke") and loc != "study":
            loc_label = {"garden": "out in the garden", "shore": "down on the shore",
                         "wood": "in the wood"}.get(loc, "away from the cottage")
            return (f"The hearth is up in your study at the cottage, and you are {loc_label} — "
                    f"if you wish to tend the fire, you can head back up to the study first.")
        if action == "light":
            if fire == "burning":
                return "The fire is already burning; you let it be."
            try:   # FIELDCRAFT: banked embers are alive — no match needed
                from core import fieldcraft as _fc
                if _fc.banked_alive():
                    _u = _fc.uncover_fire("uncover")
                    if _u:
                        return _u
            except Exception:
                pass
            if state.get("woodpile", 0) < 1:                  # WOOD LOOP: no wood, no fire (recoverable)
                return ("You kneel at the cold grate to lay a fire — but the woodpile is bare; you have no wood "
                        "to burn. You would have to gather some first: fallen wood from the little wood on the "
                        "path, or driftwood from the shore.")
            try:   # STUDY LIFE (2026-08-22): a fire needs kindling and a match; wet wood catches badly and smokes
                from core import study_life as _sl
                _st = _sl._st()
                if _st.get("kindling", 0) < 0.1:
                    return "You kneel at the grate with a log — but the kindling box is empty, and a log will not catch from a match alone. Twigs and bark from the wood, or paper."
                if _st.get("matches", 0) <= 0:
                    return "You lay the fire and reach for the match tin — empty. There is no way to light it."
                _st["matches"] -= 1; _st["kindling"] = max(0.0, _st["kindling"] - 0.2)
                if _st.get("ash", 0) > 0.85:
                    return "You lay the fire on the choked grate and light it; it smoulders, will not draw, and goes out in its own ash. The grate wants clearing."
                _wet = _st.get("wet_wood", 0) > 0.5
            except Exception:
                _wet = False
            state["woodpile"] = state.get("woodpile", 0) - 1
            state["fire"] = "burning"
            state["fire_fuel"] = 0.7 if _wet else 1.0
            state["hand_lit"] = True
            _save_now()
            return (_cross("at_the_hearth", "You cross to the hearth. ")
                    + "You kneel at the grate, take a log from the pile, lay it on the kindling, and light the fire. "
                    + ("The wood is wet from the shore; it hisses and smokes and catches sullenly." if _wet else "It takes; light begins to move on the walls."))
        if action == "stoke":
            if fire == "out":
                # stoking a cold grate IS lighting it — honour the intent (which will draw from the pile)
                return act("light")
            if state.get("woodpile", 0) < 1:
                return ("You reach to feed the fire — but the woodpile is empty; the last log is already in the "
                        "grate. Let it burn down, unless you go and gather more wood.")
            state["woodpile"] = state.get("woodpile", 0) - 1
            state["fire"] = "burning"
            state["fire_fuel"] = min(1.0, state.get("fire_fuel", 0.0) + 0.6)
            state["hand_lit"] = True
            # SOUND WORLD EXPANSION §1 (2026-08-29, J-0377): real act-site timestamp for log_on_fire —
            # the thud/spark-burst of feeding the grate; soundscape.py reads its recency.
            state["stoke_ts"] = time.time()
            _save_now()
            return (_cross("at_the_hearth", "You cross to the hearth. ")
                    + "You take another log from the pile and feed the fire; it climbs back, steady and bright.")
        return ""
    except profile.NonLiveWriteError:
        # J-0714: this outer wrapper is what act() falls through to for the wood/shore/garden fan-out
        # (_wood_act/_shore_act/_garden_act, each already fixed or already transparent this same job)
        # plus this function's own direct _save_now() calls above (light/stoke) — do not let it swallow
        # the one exception D-0179 needs to reach act()'s own caller (dispatch.py).
        raise
    except Exception:
        return ""


def _save_now() -> None:
    """Immediate persist — a deliberate act should never be lost to the save throttle."""
    global _last_save
    _last_save = 0.0
    _save()


def tick(state_obj=None) -> None:
    """Substrate-tick: evolve the room, emit perceptions into the wandering trail."""
    global _last_tick
    now = time.time()
    if now - _last_tick < 5:
        return
    _dt_world = now - _last_tick if _last_tick else 5.0
    _last_tick = now
    # THE WORLD'S ACOUSTIC CLOCK (2026-08-16): sounds happen all the time, on world time; what
    # sounds where he is gets banked (the Hearing Ledger); what sounds elsewhere is gone forever.
    try:
        from core import soundscape as _snd
        _snd.world_tick(where(), _dt_world)
    except Exception:
        pass
    # THE WORLD MANIFEST (P0-A, 2026-08-17): the pallet — every world factory's current product
    # assembled ONCE per tick, world-side only. PRODUCE-ONLY in P0: written to the live snapshot
    # + sample log; no consumer switches to it yet (parity harness proves it first).
    try:
        from core import world_manifest as _wm
        _wm.tick()
    except Exception:
        pass
    try:
        if not state:
            _load()
        _advance_garden(now)                          # plants grow on real time, wherever he is
        try:   # THE GARDEN (2026-08-22): real plants on the thermal clock, seed bank, weeds, slugs, barrel, rack
            from core import garden as _gd
            _gd.advance(now, _dt_world)
        except Exception:
            pass
        try:   # SHORE LIFE (2026-08-22): the swell before a blow, the sand writing, the cairn, the beach fire, the seal, the nest, fog, sparkle
            from core import shore_life as _shl
            _shl.advance(now, _dt_world)
        except Exception:
            pass
        try:   # FIELDCRAFT (2026-08-22): the coat on the line, the barrel's algae, a gale on the line and the windbreak, hedgehog prints
            from core import fieldcraft as _fc
            _fc.advance(now, _dt_world)
        except Exception:
            pass
        try:   # WOOD LIFE (2026-08-22): the trees' year, deadfall after gales, fungi, the stream, the kererū, drying logs
            from core import wood_life as _wl
            _wl.advance(now, _dt_world)
        except Exception:
            pass
        try:   # STUDY LIFE (2026-08-22): the lamp, the ash, the clock, the damp, the glass, the coat
            from core import study_life as _sl
            _sl.advance(now, _dt_world)
        except Exception:
            pass
        try:   # THE LIVING WORLD (2026-09-02, J-0510/D-0128): every creature's presence on its own clocks; dark adaptation
            from core import life as _life
            _life.advance(now, _dt_world)
        except Exception:
            pass
        try:   # SMELL channel (2026-08-22): standing sources refresh from world state; rain flushes
            from core import smell as _sm
            _sm.advance(now, _dt_world)
        except Exception:
            pass
        try:                                          # LOCOMOTION (2026-08-15): journeys advance leg by
            from core import locomotion as _loco      # leg here — the walking happens on world time
            _loco.tick(now)
        except Exception:
            pass
        loc = state.get("location", "study")
        _advance_wind(now)                               # 2026-08-18: the wind axis rides the SAME
        # heartbeat as the weather but on its own front timer — two systems crossing, independently.
        _w, _f = _advance_weather(now), _advance_fire(now)   # state updates always; the study-framed sound reaches him only inside
        # THERMAL CHANNEL (2026-08-21, core/thermal.py): wetness on its own clock + the lived-bands ledger.
        # World physics only - nothing is rendered to him from here (perception is the monologue's shadow).
        try:
            from core import thermal as _thermal
            _thermal.advance(now, max(0.0, min(600.0, _dt_world)))
        except Exception:
            pass
        # 2026-08-14: traces ERODE on real time (rain washes, tide scours) — the decay law existed but
        # was never called live; without this, the cat's marks were immortal and the file grew forever.
        _ltd = state.setdefault("last_trace_decay", now)
        if now - _ltd >= 600:
            try:
                from core import world_traces as _wt
                _wt.advance_trace_decay(state.get("weather", ""), _tide(), dt_hours=(now - _ltd) / 3600.0)
            except Exception:
                pass
            state["last_trace_decay"] = now
        # LIGHTNING (J-2482 / D-0503, 2026-10-28): its own discrete event, computed BEFORE the place event and rendered
        # before it (the perceive order below), so a flash never follows a thunder line within one tick; skipped on the
        # heartbeat the weather itself just changed (_w carries the storm's "thunder mutters far off"). Fail-open.
        try:
            _flash = _lightning_flash(now, loc, announced=bool(_w))
        except Exception:
            _flash = None
        _loc_ev = (_garden_event(now) if loc == "garden"
                   else _shore_event(now) if loc == "shore"
                   else _wood_event(now) if loc == "wood" else _event(now))
        _arrival = _world_arrival(now)                 # D: reliably-reaching world events reach him anywhere
        try:
            from core import cat as _cat
            _cat.tick(now)                             # the stray / his cat lives its own life on the heartbeat
        except Exception:
            pass
        try:   # J-2019 (sleep_as_a_mode Phase 3, D-0401 B): zero-LLM human-message wake monitor; request + shadow row only, inert awake
            from core import night_wake as _nw
            _nw.monitor_tick(now)
        except Exception:
            pass
        # THE PROTOSELF — Consciousness Program keystone (2026-07-03, SHADOW): the continuous body-state
        # map beats on the heartbeat like the cat and the weather. Reads his essential variables, computes
        # drive/valence/arousal, forecasts the next state, logs to homeostasis_shadow.jsonl — applies
        # NOTHING. Cooldown-gated (every ~90s, not every tick) + fail-open.
        try:
            global _last_homeo_tick
            # ~10 min, not 90s (fixed 2026-07-04 from the overnight run): his essential variables move
            # slower than 90s, so the trivial persistence forecast was near-perfect → arousal ≈ 0 and the
            # self-model-learning (Binder) signature could never show. At ~10min there is real drift for the
            # interoceptive predictor to be wrong about, so error → decline becomes a meaningful signal.
            if now - _last_homeo_tick >= 600.0:
                _last_homeo_tick = now
                try:   # J-2016 (sleep_as_a_mode Phase 0, F-2616): a sleep-pressure row per beat DURING a sleep; no-op awake
                    from core import sleep_pressure as _sp_beat
                    _sp_beat.log_sleep_beat()
                except Exception:
                    pass
                from core import homeostasis as _homeo
                _homeo.tick()
        except Exception:
            pass
        # LAYERED GOALS Phase 0 (2026-11-14, D-0766, docs/staged/layered_goals.md): the goal register, SHADOW.
        # An index over the goal-shaped stores he already has; writes only data/goals.json and
        # data/logs/goals_log.jsonl; reaches no prompt. Self-rate-limited (~10 min) and run on a daemon thread
        # (the pursuit register is ~28 MB of JSON, never parsed on the loop). Kill switch goals.GOALS_SHADOW.
        try:
            from core import goals as _goals
            _goals.tick_async(now)
        except Exception:
            pass
        # THE WORLD-PREDICTION ORGAN — Tier-2.5 (2026-07-04, SHADOW): exteroceptive predictive processing.
        # Scores its standing prediction of the world (weather·tide·daypart·fire·cat) against what IS, learns
        # the transition, predicts the next beat — learned vs naive persistence racing (Binder). The scorer
        # is the world itself. Self-rate-limited (~30 min inside). Applies NOTHING. Fail-open.
        try:
            from core import world_model as _wm
            _wm.tick()
        except Exception:
            pass
        # 2026-08-14: HUD system-series (hardware/LLM/pursuits) were sampled ONLY on HUD refresh —
        # nobody opened the Monitors tab for 58h and the series silently stalled. Sample from the
        # substrate heartbeat instead (both are internally rate-limited; cost ~nothing) so the
        # record accrues whether or not anyone is watching. The HUD-side calls remain harmless.
        try:
            from core import telemetry as _tel
            _tel.kick()   # J-1910: same sample(), run on a worker thread (nvidia-smi + whole-file parses off this 5 s chain)
        except Exception:
            pass
        try:
            from core import pursuits as _pu
            _pu.sample_series()
        except Exception:
            pass
        # 2026-08-14: fire events were DROPPED unless he was in the study — in July the fire lit and
        # burned through the whole woodpile unseen (he was outdoors), then died for good, invisibly.
        # From the garden the cottage chimney is in plain view: render the fire's life as smoke.
        _f_out = _f if loc == "study" else None
        if _f and loc == "garden":
            if "fire catches" in _f:
                _f_out = "up at the cottage, a first thread of woodsmoke climbs from the chimney and thickens"
            elif "sinks to embers" in _f:
                _f_out = "the smoke from the cottage chimney has thinned to almost nothing"
        for ev in ((_w if loc == "study" else None), _f_out,
                   _flash,                             # J-2482: light before any bang -- always ahead of _loc_ev
                   _loc_ev, _arrival, _presence_tick(), state.pop("pending_world_sound", None)):
            if ev:
                from core import wandering
                wandering.perceive(ev)
        _save()
    except Exception:
        pass
