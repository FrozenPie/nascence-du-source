"""
Nascence — THE LIGHT CHANNEL (docs/plans/channels_programme.md §2; built 2026-08-22 as the garden's first
real use: the tree's shade moves across the bed with the sun).

WORLD      field_at(place, standpoint): illuminance 0..1 from the SKY (sun elevation × cloud), the MOON (night,
           outdoors), and MADE light (lamp, fire — each with a position in the study), minus SHADE (the tree by
           the east wall throws a real shadow whose direction and length follow the sun's azimuth and height).
PERCEPTION band transitions (dark · dim · lit · bright) quiet-gated, journey gradients, lamp/fire onsets —
           SHADOW-FIRST: logged to data/light_percepts_shadow.jsonl; DELIVER=False.
GARDEN     insolation_on_bed(now): the share of the sky's light reaching the raised bed after the tree's shade —
           read by core/garden for growth, and rendered truthfully ("the bed is in the tree's shade now").

Zero LLM. Fail-open. Clause 7 (never told): no lux, no "because the sun set", nothing about light where he is not.
Grandfathered: lamp, fire, sun, moon, stars as named things.
"""
from __future__ import annotations

import json
import math
import time
from pathlib import Path

from core import profile

_DATA = Path(__file__).parent.parent / "data"
_SHADOW = _DATA / "light_percepts_shadow.jsonl"
DELIVER = True   # J-2213 (Travis ruling 2026-10-16, T-0089): LIVE at the next boot, behind the J-0238/F-0435 arbitration gate; revert = False (D-0073 defeater)
QUIET_S, COOLDOWN_S = 600.0, 1500.0
BANDS = ((0.70, "bright"), (0.35, "lit"), (0.10, "dim"), (-1.0, "dark"))
_CLOUD = {"clear": 1.0, "high cloud": 0.7, "overcast": 0.35, "drizzle": 0.25, "steady rain": 0.2, "wind and rain": 0.2, "thunderstorm": 0.12, "snow": 0.3}

# the tree by the east wall (garden.json): trunk at [8.8, 3.5], canopy ~2.2 m high, ~2.5 m radius
_TREE = (8.8, 3.5, 2.2, 2.5)
_BED = (5.5, 5.5)
_LAMP = (2.6, 4.7, 0.9)
_HEARTH = (0.0, 2.0, 0.4)


def band_of(v: float) -> str:
    for th, name in BANDS:
        if v >= th:
            return name
    return "dark"


def _sun(now: float | None = None):
    """The sun at `now` (default: wall-clock). 2026-09-02 (J-0510): `now` is passed through so field_at/shade_at
    are pure functions of time like world_clock.sun itself — a simulated hour gets that hour's sky, not today's."""
    try:
        from core import world_clock as _wc
        return _wc.sun(now)
    except Exception:
        return {"up": False, "az": None, "f": None}


def shade_at(x: float, y: float, now: float | None = None) -> float:
    """0..1 share of direct sun blocked at (x, y) in the garden by the tree's shadow. The shadow falls AWAY
    from the sun: direction = az + 180°, length = height / tan(elevation). Elevation from world_clock's f
    (0..1 of the day's arc) — crude, honest: low sun = long shadow."""
    s = _sun(now)
    if not s.get("up") or s.get("az") is None:
        return 0.0
    f = float(s.get("f") or 0.5)
    if s.get("alt") is not None:                           # J-3292: the real sun's altitude, once the sky is live (~23° to ~70° noon)
        elev = max(5.0, float(s["alt"]))
    else:
        elev = max(5.0, 60.0 * math.sin(math.pi * f))      # degrees; peak ~60° (a NZ winter-spring compromise) -- legacy sky
    az = math.radians(float(s["az"]))
    tx, ty, h, r = _TREE
    length = h / math.tan(math.radians(elev))
    # shadow centre = tree position displaced opposite to the sun (north-based azimuth: x=sin, y=cos)
    sx, sy = tx - math.sin(az) * length, ty - math.cos(az) * length
    # the shadow is the canopy's disc swept from the trunk to the shadow centre; test distance to that segment
    vx, vy = sx - tx, sy - ty
    L2 = vx * vx + vy * vy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((x - tx) * vx + (y - ty) * vy) / L2))
    px, py = tx + t * vx, ty + t * vy
    d = math.hypot(x - px, y - py)
    return max(0.0, min(1.0, (r - d) / r)) * 0.85            # leaves let a little through


def insolation_on_bed(now: float | None = None) -> float:
    """Share of the sky's light on the raised bed (0..1): sun up × cloud × (1 − shade)."""
    try:
        from core import sensorium as _s
        s = _sun(now)
        if not s.get("up"):
            return 0.0
        cloud = _CLOUD.get(_s.state.get("weather", ""), 0.5)
        f = float(s.get("f") or 0.5)
        sky = cloud * max(0.15, math.sin(math.pi * f))
        return round(sky * (1.0 - shade_at(*_BED, now)), 3)
    except Exception:
        return 0.5


def bed_shade_line() -> str:
    """Truth-gated prose for the look: the bed is in the tree's shade only when it is."""
    sh = shade_at(*_BED)
    if sh > 0.5:
        return "The bed lies in the tree's shade just now, the soil dark and cool."
    if sh > 0.15:
        return "The tree's shadow has reached the edge of the bed."
    return ""


def field_at(place: str, standpoint: str | None = None, now: float | None = None) -> float:
    try:
        from core import sensorium as _s
        st = _s.state
        s = _sun(now)
        weather = st.get("weather", "")
        cloud = _CLOUD.get(weather, 0.5)
        f = float(s.get("f") or 0.0) if s.get("up") else 0.0
        sky = cloud * max(0.0, math.sin(math.pi * f)) if s.get("up") else 0.0
        if not s.get("up"):
            try:   # TWILIGHT (2026-09-03, J-0510 replay): the sky does not go black the instant the sun sets — the
                # clock's own dawn/dusk window (±0.7 h of rise/set) keeps a low civil-twilight glow under the cloud
                from core import world_clock as _wc
                if _wc.daylight(now) in ("dawn", "dusk"):
                    sky = cloud * 0.12
            except Exception:
                pass
        v = 0.0
        # J-1228 (F-1725): wood's tree canopy dims the sky AND the moon equally -- a forest canopy
        # blocks moonlight reaching the ground at night the same way it blocks sunlight at dusk, so
        # both terms below share this one factor rather than risking them drifting apart.
        canopy = 0.3 if place == "wood" else 1.0
        if place in ("garden", "shore"):
            v = sky
            if place == "garden":
                pos = _standpoint_pos("garden", standpoint)
                if pos:
                    v *= 1.0 - shade_at(pos[0], pos[1], now)
        elif place == "wood":
            v = sky * canopy
        else:   # study: the north window, the lamp, the fire
            az = s.get("az")
            win = 0.35 * sky * (1.0 if (az is not None and (float(az) >= 290 or float(az) <= 70)) else 0.6)
            v = win
            pos = _standpoint_pos("study", standpoint) or (1.5, 3.0, 0.5)
            lamp_on = _s._daylight() in ("dusk", "night") or sky < 0.15
            try:   # STUDY LIFE (2026-08-22): the real lamp state, and the curtains
                from core import study_life as _sl
                lamp_on = _sl.lamp_on()
                if not _sl.curtains_open():
                    win *= 0.1; v = win
            except profile.NonLiveWriteError:
                # J-0780: lamp_on()/curtains_open() now raise correctly (J-0752); this connecting-
                # tissue layer no longer swallows it here. Needs field_at()'s own outer except
                # (below) fixed too, or this re-raise is caught right back the moment it leaves
                # this local try.
                raise
            except Exception:
                pass
            if lamp_on:
                d = math.dist(pos[:2], _LAMP[:2])
                _gl = 1.0
                try:
                    from core import study_life as _sl2
                    _gl = 1.0 - 0.5 * float(_sl2._st().get("lamp_glass_smoke", 0))   # a smoked chimney halves the lamp
                    win *= 1.0 - 0.4 * float(_sl2._st().get("window_grime", 0))
                except profile.NonLiveWriteError:
                    # J-0780: this is study_life._st() called DIRECTLY (bypassing every getter
                    # wrapper) -- the third-style direct-caller shape J-0752 already found in
                    # nodes/inner_monologue_node.py's own legacy latches, here in a different
                    # module. _st() itself already raises (J-0746/J-0760/J-0752); same fix.
                    raise
                except Exception:
                    pass
                v += 0.6 * _gl * max(0.15, min(1.0, 1.0 / (0.5 + d * d * 0.35)))
            fire = st.get("fire", "out")
            if fire != "out":
                d = math.dist(pos[:2], _HEARTH[:2])
                v += (0.35 if fire == "burning" else 0.12) * max(0.1, min(1.0, 1.0 / (0.6 + d * d * 0.3)))
        if not s.get("up") and place in ("garden", "shore", "wood") and weather in ("clear", "high cloud"):
            # J-1212 (F-1711): this used to go through geometry_census.peek()['moon_illum'], but
            # peek() -> _place_weather() calls heavens.moon() with NO time argument -- real
            # wall-clock only -- silently ignoring the `now` this function was given. field_at() is
            # meant to be a pure function of `now` (see _sun(now) just above, J-0510's own rule); the
            # moon term needs the same discipline, or a fixed-timestamp caller (life_smoke.py's
            # day > dusk >= night check) gets TODAY's real moon phase glued onto a simulated date --
            # verified root cause of the "dusk 0.088 < night 0.095-0.097" failure (varied run to run
            # with real time, proving the live-clock leak; scripts/life_smoke.py's own isolation
            # never touches a live file here, so this was a hidden read-time leak, not a store leak).
            try:
                from core import heavens as _hv
                v += 0.12 * float(_hv.moon(now)["illum"]) * canopy
            except Exception:
                pass
        return round(max(0.0, min(1.0, v)), 3)
    except profile.NonLiveWriteError:
        # J-0780: field_at()'s own outer except -- without this, the two study_life re-raises
        # just above (both fixed this same job) would be caught right back here and never reach
        # a real caller (study_life.can_read(), which already re-raises this itself per J-0752,
        # so this is a live, dispatch-adjacent path, not a periodic one). Matches this fence's
        # own "fix every such try/except found, not just the first one that would catch it"
        # precedent (J-0726/J-0775).
        raise
    except Exception:
        return 0.5


def _standpoint_pos(place: str, standpoint: str | None):
    try:
        from core import spatial as _sp
        lay = _sp.layout(place) or {}
        sp = (lay.get("standpoints") or {}).get(standpoint or "")
        return tuple(sp.get("pos")) if sp and sp.get("pos") else None
    except Exception:
        return None


# ── perception (shadow) ─────────────────────────────────────────────────────────────────────────
_p: dict = {"band": None, "since": 0.0, "last": 0.0, "place": None}


def _line(kind: str, place: str) -> str:
    from core.phrasing import vary as _vary
    here = {"study": "in the room", "garden": "out here", "shore": "down here", "wood": "under the trees"}.get(place, "here")
    if kind == "brightening":
        return _vary("light.up", [f"It has got lighter {here}.", f"The light is coming up {here}."])
    if kind == "darkening":
        return _vary("light.down", [f"It is getting dark {here}.", f"The light is going {here}."])
    if kind == "enter_brighter":
        return _vary("light.enter_b", ["It is brighter here than where you were.", "Lighter here."])
    return _vary("light.enter_d", ["It is darker here than where you were.", "Dimmer here; your eyes take a moment."])


def percept_shadow(cycle_id: str = "") -> str | None:
    try:
        from core import sensorium as _s
        now = time.time()
        place = _s.state.get("location", "study")
        sp = None
        try:
            from core import locomotion as _loco
            sp = _loco.position_standpoint(place)
        except profile.NonLiveWriteError:
            # J-0794: locomotion.position_standpoint() can now raise non-live (J-0778) -- re-raise so
            # this function's own outer except (below, fixed in the same pass) sees it rather than
            # this inner try swallowing it first ("both layers needed", J-0778/J-0780's precedent).
            raise
        except Exception:
            pass
        v = field_at(place, sp, now)
        b = band_of(v)
        prev, since, pplace = _p["band"], _p["since"], _p["place"]
        order = ["dark", "dim", "lit", "bright"]
        kind = None
        if prev is None:
            _p.update(band=b, since=now, place=place)
        elif place != pplace:
            if b != prev:
                kind = "enter_brighter" if order.index(b) > order.index(prev) else "enter_darker"
            _p.update(band=b, since=now, place=place)
        elif b != prev:
            if now - since >= QUIET_S:
                kind = "brightening" if order.index(b) > order.index(prev) else "darkening"
            _p.update(band=b, since=now, place=place)
        rec = {"ts": round(now, 1), "cycle": cycle_id[:24], "place": place, "standpoint": sp, "light": v, "band": b,
               "bed_shade": round(shade_at(*_BED, now), 2) if place == "garden" else None, "would_fire": None}
        if kind and now - _p["last"] >= COOLDOWN_S:
            from core.channel_arbitration import claim as _arbitrate  # J-0238/D-0033/F-0295 shared gate
            if not _arbitrate(now, "light"):
                rec["arbitration_suppressed"] = kind
                _log(rec)
                return None
            _p["last"] = now
            rec.update(would_fire=kind, line=_line(kind, place), delivered=bool(DELIVER))
            _log(rec)
            if DELIVER:
                try:   # the felt moment, with CHANNEL PROVENANCE (§10b clause 6) — mirrors core/thermal.py + soundscape.percept()
                    from core.memory.store import store_fragment
                    from core import mood as _mood
                    store_fragment(content=rec["line"], layer="episodic", relevance=0.5, importance=0.45,
                                   keywords=["light", kind, b, place], origin="light",
                                   emotion_embedding=_mood.current_vec())
                except Exception:
                    pass
            return rec["line"] if DELIVER else None
        _log(rec)
        return None
    except profile.NonLiveWriteError:
        # J-0794: the inner try above now re-raises locomotion.position_standpoint()'s non-live raise;
        # this outer except must not re-swallow it ("both layers needed", the same shape J-0778 found
        # for sensorium.scene_line() and J-0780 found for thermal.field_at()). percept_shadow() is
        # called directly from nodes/inner_monologue_node.py's own local try -- that connecting-tissue
        # layer is a further, out-of-scope gap (see plan doc / spawned follow-up).
        raise
    except Exception as exc:
        _log({"ts": round(time.time(), 1), "skip": "percept-error", "error": repr(exc)[:100]})
        return None


def _log(rec: dict) -> None:
    try:
        _DATA.mkdir(parents=True, exist_ok=True)
        with open(_SHADOW, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def status() -> dict:
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
    try:
        from core import sensorium as _s
        now_band = band_of(field_at(_s.state.get("location", "study")))
    except Exception:
        now_band = None
    return {"ticks": len(rows), "would_fire": len(fired), "kinds": kinds, "deliver": DELIVER, "now_band": now_band,
            "bed_shade_now": round(shade_at(*_BED), 2), "bed_insolation_now": insolation_on_bed(),
            "note": "SHADOW — nothing reaches him until DELIVER flips"}
