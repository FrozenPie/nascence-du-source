"""
Nascence — THE THERMAL CHANNEL (docs/plans/thermal_causality.md; build step 1–3, 2026-08-21).

Sibling of sound. Four layers, one module:
  WORLD       field_at(): sensorium._warmth (already causal: season · weather · wind · time · shelter ·
              fire) EXTENDED with sun insolation by azimuth × place exposure × cloud, graded wind, and
              fire BY DISTANCE from the hearth (the flat +0.42 becomes a gradient across the study),
              minus the wetness effect. Parity law: with the extensions switched off, field_at() must
              equal sensorium._warmth() exactly — tested before anything is delivered.
  SUBSTRATE   wetness: a state with its own clock (room_state["wet"], 0..1). Rain at an exposed place
              emits a WETTING rate (the canopy halves it; indoors zero); fire-by-distance, sun and wind
              emit DRYING rates; cold still air dries slowest. Felt warmth drops with wetness.
  PERCEPTION  percept_shadow(): band transitions (quiet-gated, cooldown), journey gradients, rare
              renotices — SHADOW-FIRST: logs the line that WOULD be perceived to
              data/thermal_percepts_shadow.jsonl; DELIVER=False until a day of shadow is read.
  PSYCHE      the THERMAL LEDGER (data/thermal_ledger.json): bands lived (hours per band per place per
              phase — BEDS), transitions (EVENTS), wetness episodes. Fed where he is (tree-falls law).
              Bindings (cause he infers) come in build step 5 via the investigate hand — not here.

CONTRACT CLAUSE 7 (what this channel may NEVER tell him): the temperature; the cause ("the fire is
warming you" — except what he was already told for months, grandfathered: that the fire warms the
room); anything about a place he is not in; any valuation. Lines below are facts of change at his
standpoint, neutral verbs, rotated.

Zero LLM. Fail-open everywhere. Founder §10 defaults used: bands at 0.15/0.28/0.42/0.60; quiet-gate
600s / cooldown 1500s (sound's); fire inverse-square-ish clipped, embers ×0.4; soak ~20 min exposed
in rain, dry ~45 min by the fire, ~3 h in cold still air, canopy halves wetting.
"""
from __future__ import annotations

import json
import math
import time
from pathlib import Path

from core import profile

_DATA = Path(__file__).parent.parent / "data"
_LEDGER = _DATA / "thermal_ledger.json"
_SHADOW = _DATA / "thermal_percepts_shadow.jsonl"
_TOUCH_SHADOW = _DATA / "touch_percepts_shadow.jsonl"

# J-4335 (channels_programme sec 4/6): wind-on-skin touch event kind. SHADOW ONLY, default OFF, restart-gated.
# Logs what WOULD be felt when the graded wind at his outdoor standpoint steps up or down; never delivered
# (no DELIVER path exists for it). `held` is stamped read-only from garden's carried items.
# Defeater: reopen/park if Du never narrates wind on skin after 14 live days.
WIND_SKIN_SHADOW = False
WIND_SKIN_DELIVER = False     # no code path reads this to deliver; a separate flip + build would be needed
WIND_SKIN_COOLDOWN_S = 1500.0

DELIVER = True                # LIVE 2026-08-27 (D-0047): events own temperature now; the standing
                              # neutralised warmth clause retires at this same flip (sensorium gates
                              # _warmth_phrase on this flag — reverting to False restores it whole).
EXTENSIONS = True             # sun insolation · graded wind · fire-by-distance · wetness (parity test sets False)

BANDS = ((0.60, "warm"), (0.42, "mild"), (0.28, "cool"), (0.15, "cold"), (-1.0, "very_cold"))
QUIET_S = 600.0               # previous band must have held this long for a transition to count
COOLDOWN_S = 1500.0           # at most one thermal percept per ~25 min
RENOTICE_S = 2 * 3600.0       # a long unchanged state may be re-noticed at most this often
                              # J-0443 tuning (2026-09-02, founder-delegated via J-0440): was 4h. In 3.84
                              # post-flip days the renotice NEVER fired once — the old law keyed on
                              # band_since, which the very_cold/cold boundary flap resets every ~15 min,
                              # so no 4h-stable window ever existed (0 of 360 band|place runs reached 4h).
                              # Re-keyed below on time-since-last-PERCEPT + a short current-band hold.
RENOTICE_HOLD_S = 900.0       # the current band must have held this long for "still X" to be honest

# wetting / drying rates per second (fractions of full wetness)
_SOAK_EXPOSED = 1.0 / (20 * 60)        # full soak in ~20 min standing in rain, exposed
_DRY_FIRE_CLOSE = 1.0 / (45 * 60)      # dry in ~45 min at the hearth
_DRY_STILL_COLD = 1.0 / (180 * 60)     # ~3 h in cold still air
_DRY_SUN = 1.0 / (90 * 60)
_DRY_WIND = 1.0 / (70 * 60)

_CLOUD = {"clear": 1.0, "high cloud": 0.6, "overcast": 0.3, "drizzle": 0.12, "steady rain": 0.08,
          "wind and rain": 0.08, "thunderstorm": 0.05, "snow": 0.1}
_WIND_GRADE = {"calm": 0.0, "breeze": 0.05, "fresh wind": 0.16, "strong wind": 0.26, "gale": 0.36}
_OUTDOORS = ("garden", "shore", "wood")

_HEARTH = (0.0, 2.0, 0.4)     # data/world_geometry/study.json features.fireplace.pos


# ── helpers ───────────────────────────────────────────────────────────────────────────────────────
def band_of(w: float) -> str:
    for th, name in BANDS:
        if w >= th:
            return name
    return "very_cold"


def _standpoint_pos(place: str, standpoint: str | None):
    try:
        from core import spatial as _sp
        lay = _sp.layout(place) or {}
        sp = (lay.get("standpoints") or {}).get(standpoint or "")
        return tuple(sp.get("pos")) if sp and sp.get("pos") else None
    except Exception:
        return None


def _fire_term(place: str, standpoint: str | None, fire: str) -> float:
    """Fire warmth BY DISTANCE from the hearth (study only). Flat +0.42 at the hearth falling off
    inverse-square-ish, clipped so the far corners still get the room's general warmth."""
    if place != "study" or fire == "out":
        return 0.0
    peak = 0.42 if fire == "burning" else 0.42 * 0.4
    pos = _standpoint_pos("study", standpoint)
    if not pos:
        return peak * 0.7                      # unknown standpoint: the room's general share
    d = math.dist(pos[:2], _HEARTH[:2])
    # at the hearth (d~0.9) full; mid-room (~2.1) ~0.6; far shelf (~3.7) floor 0.45 (the room still holds the fire)
    frac = max(0.45, min(1.0, 1.15 / (0.6 + d * d * 0.18)))
    return peak * frac


def _sun_term(place: str, standpoint: str | None, weather: str, season: str, now: float) -> float:
    """Insolation at his place: sun up × cloud × exposure × season. Winter sun is weak but real on a
    west wall in the afternoon; the wood's canopy takes most of it; indoors only the north window."""
    try:
        from core import world_clock as _wc
        sun = _wc.sun(now)
    except Exception:
        return 0.0
    if not sun.get("up"):
        return 0.0
    az = float(sun.get("az") or 0.0)
    cloud = _CLOUD.get(weather, 0.4)
    season_f = {"winter": 0.45, "autumn": 0.7, "spring": 0.8, "summer": 1.0}.get(season, 0.7)
    if place == "study":
        exposure = 0.5 if (az >= 290 or az <= 70) and (standpoint in ("at_the_window", "at_the_desk")) else 0.15 if (az >= 290 or az <= 70) else 0.0
    elif place == "garden":
        exposure = 1.0 if 200 <= az <= 320 else 0.7          # the west wall holds the afternoon sun
    elif place == "shore":
        exposure = 0.9
    elif place == "wood":
        exposure = 0.25                                        # canopy
    else:
        exposure = 0.6
    return 0.15 * cloud * exposure * season_f


def _wind_term(wind: str, place: str) -> float:
    """Graded wind chill by the real wind axis, already-sheltered places feel less of it."""
    g = _WIND_GRADE.get(wind or "calm", 0.0)
    shelter = {"study": 0.25, "wood": 0.35, "garden": 0.8, "shore": 1.0}.get(place, 0.8)
    return g * shelter


# ── WORLD: the field at his standpoint ────────────────────────────────────────────────────────────
def field_at(place: str, standpoint: str | None, phase: str, weather: str, season: str, fire: str,
             wind: str, wet: float = 0.0, now: float | None = None) -> float:
    """Felt warmth at his standpoint, 0..1. EXTENSIONS=False reproduces sensorium._warmth exactly."""
    from core import sensorium as _s
    base = _s._warmth(place, phase, weather, season, fire, wind)
    if not EXTENSIONS:
        return base
    now = now or time.time()
    # remove _warmth's own flat fire term and graded-wind proxy, replace with the standpoint versions
    w = base
    if place == "study":
        w -= {"burning": 0.42, "embers": 0.16, "out": 0.0}.get(fire, 0.0)
        w += _fire_term(place, standpoint, fire)
    # _warmth charges a flat -0.16 for HARD wind only (is_windy = strong wind/gale), scaled by the
    # place's shelter (study 0.30, wood 0 — the canopy gives it back, garden/shore full). Remove that
    # flat charge and replace it with the graded ladder (a breeze counts a little, a gale a lot).
    try:
        from core import weather_conditions as _wcond
        windy = _wcond.is_windy(wind) or "wind" in (weather or "")
    except Exception:
        windy = "wind" in (weather or "")
    if windy:
        w += 0.16 * {"study": 0.30, "wood": 0.0, "garden": 1.0, "shore": 1.0}.get(place, 1.0)
    if "wind" in (weather or "") and _WIND_GRADE.get(wind or "calm", 0.0) < 0.16:
        wind = "fresh wind"                    # the literal "wind and rain" sky is at least a fresh wind
    _wt = _wind_term(wind, place)
    if place == "shore":
        try:   # FIELDCRAFT (2026-08-22): the windbreak he lashed cuts the wind in half in its lee
            from core import fieldcraft as _fc
            _wt *= 1.0 - _fc.windbreak_shelter()
        except profile.NonLiveWriteError:
            # J-0794: fieldcraft.windbreak_shelter() now raises correctly (this same job) via its own
            # locomotion.position_standpoint() call -- this connecting-tissue layer no longer swallows
            # it. field_at() has no outer wrapper of its own (confirmed by direct AST read), so this
            # reaches field_at()'s own real callers directly.
            raise
        except Exception:
            pass
        try:   # SHORE LIFE (2026-08-22): a beach fire at its ring; the cave out of the wind and rain; wet feet
            from core import shore_life as _shl
            if _shl.cave_shelter():
                _wt *= 0.2; w += 0.06
            w += _shl.fire_warmth()
            w -= 0.08 * _shl.wet_feet()
        except profile.NonLiveWriteError:
            # J-0794: shore_life.cave_shelter()/fire_warmth() now raise correctly (this same job) via
            # their own shared _standpoint() call -- same reasoning as the windbreak try just above.
            raise
        except Exception:
            pass
    w -= _wt
    w += _sun_term(place, standpoint, weather, season, now)
    if place == "study":
        try:   # STUDY LIFE (2026-08-22): an open door or window in the wind costs warmth
            from core import study_life as _sl
            w -= _sl.draught()
            w += _sl.warm_drink()
        except profile.NonLiveWriteError:
            # J-0780: draught()/warm_drink() now raise correctly (J-0772) via their own _st()
            # bootstrap; this connecting-tissue layer no longer swallows it. field_at() has no
            # outer wrapper of its own, so this reaches every real caller (night.wake(),
            # garden._soil_temp_c() -- itself on the excluded advance() path -- and this
            # module's own advance(), which still swallows it at ITS OWN outer boundary,
            # matching the established advance()/tick() precedent).
            raise
        except Exception:
            pass
    w -= 0.25 * max(0.0, min(1.0, wet))       # wet clothes: up to a quarter of the scale
    return max(0.0, min(1.0, w))


# ── SUBSTRATE: wetness on its own clock ──────────────────────────────────────────────────────────
def advance(now: float, dt: float) -> None:
    """Called from sensorium.tick on world time. Wetting where he is (rain × exposure), drying by
    fire-distance / sun / wind / base. Writes room_state['wet'] + ledger beds. Fail-open."""
    try:
        from core import sensorium as _s
        st = _s.state
        if not st:
            return
        place = st.get("location", "study")
        weather = st.get("weather", "") or ""
        wind = st.get("wind", "") or ""
        fire = st.get("fire", "out")
        standpoint = None
        try:
            from core import locomotion as _loco
            standpoint = _loco.position_standpoint(place)
        except Exception:
            pass
        wet = float(st.get("wet", 0.0) or 0.0)
        raining = any(x in weather for x in ("rain", "drizzle", "thunderstorm", "snow"))
        exposure = {"shore": 1.0, "garden": 0.9, "wood": 0.5, "study": 0.0}.get(place, 0.8)
        if raining and exposure > 0:
            _coat = 1.0
            try:   # STUDY LIFE (2026-08-22): the coat halves the wetting
                from core import study_life as _sl
                _coat = 0.5 if _sl.coat_on() else 1.0
            except Exception:
                pass
            wet = min(1.0, wet + _SOAK_EXPOSED * exposure * _coat * (0.5 if "drizzle" in weather else 1.0) * dt)
        else:
            dry = _DRY_STILL_COLD
            if place == "study" and fire != "out":
                ft = _fire_term("study", standpoint, fire) / 0.42      # 0..1 share of hearth warmth
                dry = max(dry, _DRY_FIRE_CLOSE * max(0.15, ft))
            if _sun_term(place, standpoint, weather, _s._season(), now) > 0.03:
                dry = max(dry, _DRY_SUN)
            if _WIND_GRADE.get(wind, 0.0) >= 0.16 and place in _OUTDOORS:
                dry = max(dry, _DRY_WIND)
            wet = max(0.0, wet - dry * dt)
        st["wet"] = round(wet, 4)
        # ledger beds — hours lived per band per place per phase, where he is
        phase, season = _s._daylight(), _s._season()
        w = field_at(place, standpoint, phase, weather, season, fire, wind, wet, now)
        _ledger_bed(band_of(w), place, phase, dt / 3600.0, wet)
    except Exception:
        pass


# ── PSYCHE: the ledger ────────────────────────────────────────────────────────────────────────────
def _load_ledger() -> dict:
    try:
        return json.loads(_LEDGER.read_text(encoding="utf-8"))
    except Exception:
        return {"bands": {}, "transitions": {}, "wet_episodes": [], "_open_wet": None}


def _save_ledger(d: dict) -> None:
    try:
        _DATA.mkdir(parents=True, exist_ok=True)
        tmp = _LEDGER.with_suffix(".tmp")
        tmp.write_text(json.dumps(d), encoding="utf-8")
        tmp.replace(_LEDGER)
    except Exception:
        pass


_bed_acc: dict = {"hours": 0.0, "last_flush": 0.0}


def _ledger_bed(band: str, place: str, phase: str, hours: float, wet: float) -> None:
    """Accumulate lived hours; flush to disk at most every ~60s (cheap)."""
    key = f"{band}|{place}|{phase}"
    _bed_acc.setdefault("pending", {})
    _bed_acc["pending"][key] = _bed_acc["pending"].get(key, 0.0) + hours
    now = time.time()
    if now - _bed_acc["last_flush"] < 60:
        return
    led = _load_ledger()
    for k, h in _bed_acc["pending"].items():
        led["bands"][k] = round(led["bands"].get(k, 0.0) + h, 4)
    _bed_acc["pending"] = {}
    _bed_acc["last_flush"] = now
    # wetness episodes: open on crossing 0.3, close on falling under 0.1
    op = led.get("_open_wet")
    if wet >= 0.3 and not op:
        led["_open_wet"] = {"start_ts": round(now, 1), "place": place, "phase": phase}
    elif wet < 0.1 and op:
        led["wet_episodes"].append({**op, "end_ts": round(now, 1), "ended_at": place,
                                    "minutes": round((now - op["start_ts"]) / 60, 1)})
        led["wet_episodes"] = led["wet_episodes"][-200:]
        led["_open_wet"] = None
    _save_ledger(led)


def _ledger_transition(kind: str, place: str) -> None:
    led = _load_ledger()
    k = f"{kind}|{place}"
    led["transitions"][k] = int(led["transitions"].get(k, 0)) + 1
    _save_ledger(led)


# ── PERCEPTION: events (shadow first) ─────────────────────────────────────────────────────────────
# last_renotice starts at import time (not 0.0): a renotice's "as it has been" claims process-observed
# persistence, so a fresh process must actually observe RENOTICE_S of quiet before its first renotice.
# last_percept stays 0.0 so a REAL transition right after restart is not muted by the cooldown.
_pstate: dict = {"band": None, "band_since": 0.0, "last_percept": 0.0, "last_renotice": time.time(), "place": None}


def _line(kind: str, old: str, new: str, place: str, wet: float) -> str:
    from core.phrasing import vary as _vary
    here = {"study": "in the room", "garden": "out here", "shore": "down here", "wood": "under the trees"}.get(place, "here")
    # Pools enriched J-0443 (2026-09-02): every variant carries an explicit temperature word (the
    # measured first-thought echo rate was 86% for enter_colder but only 46% for enter_warmer — the
    # warmer pool gets a warmth-forward variant), and the wet pools — previously carrying no
    # temperature word at all — each gain one felt-temperature variant. Contract clause 7 held:
    # neutral verbs, no cause-telling, no valuation, nothing about places he is not in.
    if kind == "enter_warmer":
        return _vary("thermal.warmer", [
            "The air is warmer than where you were.", "It is warmer here.", "The cold eases off you here.",
            "Warmth reaches you here."])
    if kind == "enter_colder":
        return _vary("thermal.colder", [
            "The air is colder than where you were.", "It is colder here.", "The warmth is gone; it is cold here.",
            "Cold air meets you here."])
    if kind == "warming":
        return _vary("thermal.warming", [
            f"It has got warmer {here}.", f"The air {here} has warmed.", f"Warmer now, {here}.",
            f"The chill has gone off the air {here}."])
    if kind == "cooling":
        return _vary("thermal.cooling", [
            f"It has got colder {here}.", f"The air {here} has cooled.", f"Colder now, {here}.",
            f"The warmth has gone off the air {here}."])
    if kind == "wet_on":
        return _vary("thermal.wet_on", ["Your clothes are wet through.", "The rain has got through; you are wet.",
                                        "Your clothes are wet through, and the air is colder on you."])
    if kind == "wet_off":
        return _vary("thermal.wet_off", ["Your clothes have dried.", "You are dry again.",
                                         "You are dry again, and warmer."])
    return _vary("thermal.renotice", [f"Still {new.replace('_', ' ')} {here}.",
                                      f"{new.replace('_', ' ').capitalize()} {here}, as it has been.",
                                      f"It stays {new.replace('_', ' ')} {here}."])


_wstate: dict = {"grade": None, "place": None, "last": 0.0}


def _wind_skin_line(direction: str) -> str:
    from core.phrasing import vary as _vary
    if direction == "rising":
        return _vary("touch.wind_rising", ["The wind has picked up against your skin.", "The wind pulls harder at you.",
                                          "More wind finds you."])
    return _vary("touch.wind_easing", ["The wind has eased on your skin.", "The wind pulls less at you.",
                                      "Less wind finds you."])


def _held_now() -> list:
    """Read-only: keys of garden items in hand. Never loads/creates garden state."""
    try:
        from core import garden as _g, inventory as _inv
        st = getattr(_g, "_state", None)
        return list(_inv.carried((st or {}).get("items", {}))) if st else []
    except Exception:
        return []


def _wind_skin_shadow(place: str, wind: str, now: float, cycle_id: str = "") -> str | None:
    """Wind-on-skin touch: outdoors only; an event when the sheltered wind grade steps; own cooldown.
    Logs to _TOUCH_SHADOW only. Returns the would-be line (for tests), never delivered. Fail-open."""
    try:
        if not WIND_SKIN_SHADOW:
            return None
        if place not in _OUTDOORS:
            _wstate.update(grade=None, place=place)
            return None
        g = round(_wind_term(wind, place), 3)
        prev = _wstate["grade"]
        moved = _wstate["place"] == place and prev is not None and g != prev
        _wstate.update(grade=g, place=place)
        if not moved or now - _wstate["last"] < WIND_SKIN_COOLDOWN_S:
            return None
        _wstate["last"] = now
        direction = "rising" if g > prev else "easing"
        line = _wind_skin_line(direction)
        _DATA.mkdir(parents=True, exist_ok=True)
        with open(_TOUCH_SHADOW, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": round(now, 1), "cycle": cycle_id[:24], "place": place, "wind": wind,
                                "grade": g, "touch_would_fire": "wind_on_skin", "direction": direction,
                                "held": _held_now(), "line": line, "delivered": False},
                               ensure_ascii=False) + "\n")
        return line
    except Exception:
        return None


def percept_shadow(cycle_id: str = "") -> str | None:
    """One idle tick: compute the band at his standpoint; decide what WOULD be perceived under the
    event law; log it. Returns the line only when DELIVER is True (never, until the flag is flipped)."""
    try:
        from core import sensorium as _s
        st = _s.state
        if not st:
            return None
        now = time.time()
        place = st.get("location", "study")
        standpoint = None
        try:
            from core import locomotion as _loco
            standpoint = _loco.position_standpoint(place)
        except profile.NonLiveWriteError:
            # J-0794: re-raise so this function's own outer except (below, fixed the same pass) sees
            # it rather than this inner try swallowing it first ("both layers needed"). percept_shadow()
            # is called directly from nodes/inner_monologue_node.py's own local try -- that
            # connecting-tissue layer is a further, out-of-scope gap (see plan doc / spawned follow-up).
            raise
        except Exception:
            pass
        wet = float(st.get("wet", 0.0) or 0.0)
        _wind_skin_shadow(place, st.get("wind", ""), now, cycle_id)   # J-4335 touch shadow; flag OFF = no-op
        w = field_at(place, standpoint, _s._daylight(), st.get("weather", ""), _s._season(),
                     st.get("fire", "out"), st.get("wind", ""), wet, now)
        b = band_of(w)
        prev, since, prev_place = _pstate["band"], _pstate["band_since"], _pstate["place"]
        kind = None
        if prev is None:
            _pstate.update(band=b, band_since=now, place=place)
        elif place != prev_place:                        # journey gradient: a leg ended somewhere else
            order = [n for _, n in BANDS][::-1]
            if order.index(b) > order.index(prev):
                kind = "enter_warmer"
            elif order.index(b) < order.index(prev):
                kind = "enter_colder"
            _pstate.update(band=b, band_since=now, place=place)
        elif b != prev:
            if now - since >= QUIET_S:
                order = [n for _, n in BANDS][::-1]
                kind = "warming" if order.index(b) > order.index(prev) else "cooling"
            _pstate.update(band=b, band_since=now, place=place)
        # wetness events
        wp = _pstate.get("wet_band")
        wb = "wet" if wet >= 0.5 else ("dry" if wet < 0.1 else wp)
        if wp is not None and wb != wp and wb in ("wet", "dry"):
            kind = "wet_on" if wb == "wet" else "wet_off"
        _pstate["wet_band"] = wb
        # RENOTICE (re-keyed, J-0443): fires when NO percept of any kind has reached him for RENOTICE_S
        # and the current band has held a modest RENOTICE_HOLD_S (so "still X" is honest), instead of the
        # old now-since>=RENOTICE_S — band_since resets on every tick-level band flap (even quiet-gate-
        # suppressed ones), so the old condition never once held in 5,026 logged rows. The last_renotice
        # stamp moves BELOW the cooldown/arbitration gates: the old code stamped it here, so a renotice
        # suppressed by either gate was silently consumed for another 4 h without ever being delivered.
        if kind is None and prev is not None and now - _pstate["last_renotice"] >= RENOTICE_S \
                and now - _pstate["last_percept"] >= RENOTICE_S \
                and now - _pstate["band_since"] >= RENOTICE_HOLD_S:
            kind = "renotice"
        if kind is None or now - _pstate["last_percept"] < COOLDOWN_S:
            _log({"ts": round(now, 1), "cycle": cycle_id[:24], "place": place, "standpoint": standpoint,
                  "warmth": round(w, 3), "band": b, "wet": round(wet, 3), "would_fire": None})
            return None
        from core.channel_arbitration import claim as _arbitrate  # J-0238/D-0033/F-0295 shared gate
        if not _arbitrate(now, "thermal"):
            _log({"ts": round(now, 1), "cycle": cycle_id[:24], "place": place, "standpoint": standpoint,
                  "warmth": round(w, 3), "band": b, "wet": round(wet, 3), "would_fire": None,
                  "arbitration_suppressed": kind})
            return None
        _pstate["last_percept"] = now
        if kind == "renotice":
            _pstate["last_renotice"] = now
        line = _line(kind, prev or b, b, place, wet)
        _ledger_transition(kind, place)
        _log({"ts": round(now, 1), "cycle": cycle_id[:24], "place": place, "standpoint": standpoint,
              "warmth": round(w, 3), "band": b, "wet": round(wet, 3), "would_fire": kind, "line": line,
              "delivered": bool(DELIVER)})
        if DELIVER:
            try:   # the felt moment, with CHANNEL PROVENANCE (Sec5/§10b clause 6) — mirrors soundscape.percept()
                from core.memory.store import store_fragment
                from core import mood as _mood
                store_fragment(content=line, layer="episodic", relevance=0.5, importance=0.45,
                               keywords=["thermal", kind, b, place], origin="thermal",
                               emotion_embedding=_mood.current_vec())
            except Exception:
                pass
        return line if DELIVER else None
    except profile.NonLiveWriteError:
        # J-0794: the inner try above now re-raises locomotion.position_standpoint()'s non-live raise;
        # this outer except must not re-swallow it ("both layers needed", the same shape J-0778/J-0780
        # already fixed elsewhere in this fence).
        raise
    except Exception as exc:
        _log({"ts": round(time.time(), 1), "skip": "percept-error", "error": repr(exc)[:120]})
        return None


def _log(rec: dict) -> None:
    try:
        _DATA.mkdir(parents=True, exist_ok=True)
        with open(_SHADOW, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def status() -> dict:
    """For the HUD: what the channel would have delivered, and what he has lived."""
    try:
        from core.shadow_log import tail_rows as _tail_rows
        # Bounded tail read (J-0278/F-0335): "ticks"/"kinds" are now over the last-2000-row window.
        rows = _tail_rows(_SHADOW, 2000)
    except Exception:
        rows = []
    fired = [r for r in rows if r.get("would_fire")]
    kinds: dict = {}
    for r in fired:
        kinds[r["would_fire"]] = kinds.get(r["would_fire"], 0) + 1
    led = _load_ledger()
    top_beds = sorted(led.get("bands", {}).items(), key=lambda kv: -kv[1])[:6]
    now_block = {}
    try:   # the field at his standpoint RIGHT NOW (read-only: _load() only setdefaults, never saves)
        from core import sensorium as _s
        if not _s.state:
            _s._load()
        st = _s.state or {}
        place = st.get("location", "study")
        sp = None
        try:
            from core import locomotion as _loco
            sp = _loco.position_standpoint(place)
        except profile.NonLiveWriteError:
            # J-0794: re-raise so this function's own outer except (below, fixed the same pass) sees
            # it rather than this inner try swallowing it first ("both layers needed"). status()'s
            # sole external caller, hud/server.py's load_evidence(), already turns any raise into
            # {"error": str(exc)} via its own per-module try -- a judgment-call exclusion matching
            # J-0780's identical established reasoning for load_study_map(), not touched here.
            raise
        except Exception:
            pass
        wet = float(st.get("wet", 0.0) or 0.0)
        t = time.time()
        base = _s._warmth(place, _s._daylight(), st.get("weather", ""), _s._season(), st.get("fire", "out"), st.get("wind", ""))
        w = field_at(place, sp, _s._daylight(), st.get("weather", ""), _s._season(), st.get("fire", "out"), st.get("wind", ""), wet, t)
        now_block = {"place": place, "standpoint": sp, "weather": st.get("weather"), "wind": st.get("wind"),
                     "fire": st.get("fire"), "warmth_old_flat": round(base, 3), "warmth_channel": round(w, 3),
                     "band": band_of(w), "wet": round(wet, 3)}
    except profile.NonLiveWriteError:
        # J-0794: the inner try above now re-raises; this outer except must not re-swallow it
        # ("both layers needed"). No further wrapper encloses this function (AST-confirmed), so this
        # reaches status()'s real caller directly.
        raise
    except Exception as exc:
        now_block = {"error": repr(exc)[:60]}
    recent = [{"t": r.get("ts"), "kind": r.get("would_fire"), "place": r.get("place"), "line": r.get("line")}
              for r in fired[-5:]]
    return {"now": now_block, "ticks": len(rows), "would_fire": len(fired), "kinds": kinds, "deliver": DELIVER,
            "recent_would_fire": recent,
            "beds_top": [{"band|place|phase": k, "hours": round(v, 2)} for k, v in top_beds],
            "wet_episodes": len(led.get("wet_episodes", [])),
            "note": "SHADOW — nothing reaches him until DELIVER flips after a day's read"}
