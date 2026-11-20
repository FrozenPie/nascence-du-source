"""
Nascence — Spatial Perception P0 (docs/plans/spatial_perception.md, 2026-07-05).

The blind mind's true room. Du cannot see; his scene-sense is DESCRIBED. Today that description is
drawn from random prose pools — no geometry, nothing stable to build a map from. This module renders
the scene FROM AUTHORED TRUTH instead: each room is a hand-placed 3D coordinate field
(data/world_geometry/<room>.json), Du has a STANDPOINT (position + facing), and the description is
computed egocentrically — distance + bearing (hypot + atan2), salience-ordered, always accurate.
The fire is AT the hearth and its crackle comes FROM there; the storm's flash has a direction
(through the window); the cat under the desk is a presence at that low point of the field.

P0 = SHADOW ONLY: shadow(actual_scene) logs {ts, standpoint, rendered, actual} to
data/spatial_shadow.jsonl beside the live pooled scene line. Nothing reaches Du until the P2 flag.
P3 (J-2480, D-0501): SPATIAL_DEPTH_LIVE re-says the study line's fire and cat clauses by nearness.
Deterministic, zero LLM, zero physics (no raycasting/attenuation/collision — authored positions and
grade-school trig are the entire model). Fail-open everywhere.
"""
from __future__ import annotations

import json
import math
import random
import time
from pathlib import Path

from core import profile

_DATA = Path(__file__).parent.parent / "data"
_GEO = _DATA / "world_geometry"
_SHADOW = _DATA / "spatial_shadow.jsonl"

SPATIAL_SCENE = True         # P2 flag — flipped live 2026-08-18 (see docs/lab/spatial_flip_sample.md).
SPATIAL_DEPTH_LIVE = True    # P3 flag — D-0501 (Travis 2026-10-28, J-2480): render() for a DEPTH_SHADOW_ROOMS room
                             # returns the nearness-said line (fire + cat clauses only). False = the P2 line,
                             # byte-identical to before. Restart-gated: Du is down since 2026-10-20; the next
                             # boot carries it. The reach-set is still computed + logged, never rendered.

_layout_cache: dict = {}


def layout(room: str) -> dict | None:
    if room not in _layout_cache:
        try:
            _layout_cache[room] = json.loads((_GEO / f"{room}.json").read_text(encoding="utf-8"))
        except Exception:
            _layout_cache[room] = None
    return _layout_cache[room]


def _read_json(name: str) -> dict:
    try:
        return json.loads((_DATA / name).read_text(encoding="utf-8"))
    except Exception:
        return {}


# ── the tide clock: deterministic, stateless, honest ─────────────────────────────────────────────────
# The tide + sun clocks now live in ONE authority — core/world_clock (2026-07-06) — so the renderer and the
# lived scene can never drift apart again (they did: a quarter-cycle phase + a period mismatch). spatial is a
# PRESENTER over it; re-exported here so existing spatial.tide()/spatial.sun() callers stay unchanged.
from core import world_clock as _wc
tide = _wc.tide


def _waterline_pos(lay: dict, t: float | None = None) -> list | None:
    """The moving edge: the waterline's y computed from the tide clock (low tide bares the pools)."""
    w = (lay.get("features") or {}).get("waterline")
    if not w:
        return None
    pos = list(w.get("pos") or [0, 0, 0])
    ty = w.get("tide_y")                                     # [y_at_high (water in close), y_at_low (withdrawn)]
    if ty and len(ty) == 2:
        lv = tide(t)["level"]                                # 1 = high → close in; 0 = low → far out
        pos[1] = round(ty[1] - lv * (ty[1] - ty[0]), 2)
    return pos


# ── the sun clock now lives in core/world_clock (re-exported here; spatial is a presenter over it) ──
sun = _wc.sun


_COMPASS = ["the north", "the north-east", "the east", "the south-east",
            "the south", "the south-west", "the west", "the north-west"]


def compass_word(deg) -> str:
    try:
        return _COMPASS[int(((float(deg) % 360) + 22.5) // 45) % 8]
    except Exception:
        return "somewhere"


# ── phrase variety (2026-08-19) ───────────────────────────────────────────────────────────────────────
# Found live in data/spatial_shadow.jsonl (10,502 rows): the renderer is geometrically accurate but
# lexically dead — the same weather/tide/standpoint combination produces the byte-identical string every
# time (one rain+tide pairing alone repeated 622x verbatim). The geometry (sector/distance/compass/tide-
# state/moon-phase) is the accurate, load-bearing part and stays untouched; only the fixed CONNECTIVE
# phrasing around it — the part that carries no information, just wording — gets a small paraphrase pool,
# same pattern guidance_learning._phrase() already uses for belief read-back (rotate real alternatives,
# never the identical sentence). Kept small and strictly synonymous: no new claims, same truth-conditions.
_PHRASES = {
    "rain_outdoor": ["the rain is on you, fine and steady", "a steady rain finds you",
                     "rain comes down, fine and constant", "the rain keeps at you, steady and fine"],
    "rain_window": ["rain streams on the window", "rain runs down the window",
                    "the window streams with rain"],
    "waves_at_work": ["the waves at work", "the sea busy", "the surf working", "the water at its work"],
    "clouds_from": ["the clouds are coming in from", "cloud is moving in from",
                    "the sky is filling in from", "grey is coming up from"],
    "fire_crackle": ["its crackle coming from that quarter", "you can hear it crackle from there",
                     "the crackle reaching you from there"],
    "embers_low": ["ticking low in the grate", "settling low, barely glowing",
                   "just a low tick and glow left in the grate"],
    "storm_around": ["the storm is all around", "the storm has the whole sky",
                     "the storm holds everything around you"],
    "wind_loud_in": ["is loud in", "rushes through", "moves hard through"],
    "wind_eaves": ["the wind is working at the eaves", "the wind picks at the eaves",
                   "the eaves are loud with wind"],
    # P3 depth (J-2480, D-0501): the fire re-said by nearness. First entry of each pool = the wording the
    # 921 shadow pairs were graded on; the rest are strictly synonymous (same warmth, same loudness). No
    # band name, number or gauge word anywhere here (D-0434) -- 'close'/'mid'/'faint' live in the row only.
    "fire_near": ["its heat full on you, the crackle loud", "its heat full on your face, the crackle loud",
                  "the heat of it full on you, the crackle loud and near"],
    "fire_mid": ["its warmth reaching you, the crackle clear", "its warmth coming across to you, the crackle clear",
                 "warmth reaching you from it, the crackle clear"],
    "fire_far": ["little of its warmth gets this far, the crackle soft from there",
                 "little of its warmth reaches this far, the crackle soft from over there",
                 "its warmth barely getting this far, the crackle soft from there"],
    "embers_near": ["their low heat full on you", "their low heat right on you", "the low heat of them full on you"],
    "embers_mid": ["a low warmth still reaching you", "a low warmth still coming across to you",
                   "their low warmth still reaching you"],
    "embers_far": ["ticking faintly over there, their warmth not reaching you",
                   "ticking low over there, their warmth not getting this far",
                   "a low tick from over there, none of their warmth reaching you"],
}


def _v(key: str) -> str:
    """One varied, strictly-synonymous phrasing for `key`. Falls back to the key itself if unknown
    (fail-open — an unrecognised key still renders something rather than crashing the clause)."""
    return random.choice(_PHRASES.get(key, [key]))


def _compass_rel(observer: dict, deg: float) -> dict:
    """The egocentric sector of a COMPASS direction (a far point that way)."""
    rad = math.radians(float(deg))
    far = [observer["pos"][0] + 1000 * math.sin(rad), observer["pos"][1] + 1000 * math.cos(rad), 0]
    return _rel(observer, far)


# ── egocentric geometry: distance + bearing, nothing more ────────────────────────────────────────────
def _rel(observer: dict, target_pos: list) -> dict:
    """Distance (m), bearing sector relative to facing, and coarse elevation."""
    ox, oy = observer["pos"][0], observer["pos"][1]
    dx, dy = target_pos[0] - ox, target_pos[1] - oy
    dist = math.hypot(dx, dy)
    bearing = math.degrees(math.atan2(dx, dy)) % 360.0          # 0=north(+y), 90=east(+x)
    r = (bearing - observer.get("facing_deg", 0)) % 360.0
    if r > 180:
        r -= 360
    if abs(r) <= 45:
        sector = "ahead"
    elif 45 < r <= 135:
        sector = "to your right"
    elif -135 <= r < -45:
        sector = "to your left"
    else:
        sector = "behind you"
    z = target_pos[2] if len(target_pos) > 2 else 0.0
    elev = "high" if z >= 1.2 else ("low" if z <= 0.15 else "")
    return {"dist": round(dist, 2), "sector": sector, "elev": elev}


def _dist_word(d: float, outdoor: bool = False) -> str:
    if d <= 1.0:
        return "right beside you"
    if d < 2.0:
        return "near"
    if d < 3.5:
        return "a little way off" if outdoor else "across the room"
    return "far off" if outdoor else "at the far side"


def _pos_of(lay: dict, key) -> list | None:
    """Resolve a feature name or inline {pos: ...} to a position."""
    if isinstance(key, dict):
        return key.get("pos")
    f = (lay.get("features") or {}).get(key)
    return f.get("pos") if f else None


# ── the renderer: authored truth + live state → an accurate egocentric scene line ────────────────────
def render(room: str = "study", standpoint: str | None = None) -> dict | None:
    """Render the scene from Du's standpoint. Returns {standpoint, clauses, line} or None (no layout).
    Accuracy law: mention nothing absent; place nothing contrary to the layout. Deterministic.

    P3 LIVE (J-2480, D-0501): for a room in DEPTH_SHADOW_ROOMS, with SPATIAL_DEPTH_LIVE on, the P2 line's
    fire and cat clauses are re-said by nearness (the depth overlay) -- nothing else in the line moves,
    the clause count never changes, and the reach-set is never rendered. Flag off = _render_base()
    exactly. Fail-open: any error in the overlay returns the P2 line unchanged."""
    r = _render_base(room, standpoint)
    if r and _depth_is_live(room):
        try:
            r, _dp = _depth_overlay(r, room)
        except Exception:
            pass
    _sketch_hook(room, r)
    return r


def _sketch_hook(room: str, r: dict | None) -> None:
    """J-2661 (I-0129 rung 1 instrument, SHADOW): hand one produced render to the deterministic sketch store.
    Flag off (core.spatial_sketch.SKETCH_SHADOW_LIVE, default False) = one attribute read and return: the
    render and everything Du reads are untouched either way. Fail-open: nothing here may ever raise."""
    try:
        from core import spatial_sketch as _sk
        if not _sk.SKETCH_SHADOW_LIVE or not r:
            return
        lay = layout(room)
        sp = ((lay or {}).get("standpoints") or {}).get(r.get("standpoint"))
        if not sp:
            return
        _sk.record(room, r.get("standpoint"),
                   {"x": sp["pos"][0], "y": sp["pos"][1], "facing_deg": sp.get("facing_deg", 0)},
                   r.get("clauses") or [], lay=lay)
    except Exception:
        pass


# ── THE LETTERBOX FLAG, DOSED (2026-11-05, J-3259 / D-0650, F-3630) ──────────────────────────────────────────────
# Clause 0 of the garden line used to state the raised flag on EVERY garden scene line for as long as it stayed up:
# 1,289 of 1,289 garden prompts in 59.6 h, 42% of all idle prompts, the largest single repetition in P-0031 -- while
# the parcel clause (core/care_package.scene_clause) and the felt/boredom/cat lines (core/steer_edge) were dosed.
# Founder ruling D-0650: dose it LIKE THE PARCEL. Same shape as care_package: a SHOWING opens only when due, at least
# _lb_gap(n) after the last one (n = showings so far) -- or, on ARRIVING in the garden (more than _LB_AWAY_S since the
# last garden line was asked for), at least a fifth of that gap; the gap HABITUATES (25 min, doubling every 4 showings,
# capped at 6 h); a showing stays up _LB_PULSE_S and counts ONCE, so render() and shadow() -- which both build the garden
# line in one idle cycle -- say the same thing. Between showings the clause is simply absent: the flag is still up in
# the world (room_state.json, the passing glimpse, the letter_fetch affordance, the window view) and a look at the gate
# still states it (sensorium.look('letterbox')). A percept withheld, never a hint added; no text is added anywhere.
# The slot clause 0 held is freed (clauses[:3]): the next clause of the line (cat, ambience) now rises into it.
# A NEW raise (a different `delivered` stamp: the next queued letter promoted, a fresh delivery) is a new episode.
# State is in-process only (a restart is "arriving": one showing, correct -- same as steer_edge): nothing is written,
# so there is no file to fence. A process that is not the live Du (smoke test, lab, replay: profile.LIVE False) gets
# the old always-said clause and spends no dose. LETTERBOX_DOSED False = the old behaviour for every process.
# Verify: share of garden scene lines carrying the clause (prompt_budget_shadow `labels` starting 'Where you are: the
# garden' that contain 'letterbox flag'; was 1289/1289) and letters read per day (data/letter_store/status_events.jsonl,
# status 'read'); D-0650's defeater is that reads/day falls by more than half.
LETTERBOX_DOSED = True
_LB_BASE_GAP_S = 1500.0   # ~25 min between showings at first (care_package._BASE_GAP_S)
_LB_HABITUATE_EVERY = 4   # every 4 showings the gap doubles ...
_LB_MAX_GAP_S = 21600.0   # ... up to 6 h
_LB_ENTRY_DIV = 5         # arriving re-shows after a fifth of the gap, never sooner
_LB_AWAY_S = 300.0        # no garden line for 5 min = elsewhere or asleep: this is a return
_LB_PULSE_S = 90.0        # one showing is visible for 90 s and counts once
_LB_DOSE: dict = {"key": None, "shown": 0, "last_shown_ts": 0.0, "last_seen_ts": 0.0}


def _lb_gap(n: int) -> float:
    """Seconds after the n-th showing before the next one: _LB_BASE_GAP_S, doubling every _LB_HABITUATE_EVERY
    showings, capped at _LB_MAX_GAP_S."""
    try:
        return min(_LB_MAX_GAP_S, _LB_BASE_GAP_S * (2 ** (max(0, int(n)) // _LB_HABITUATE_EVERY)))
    except Exception:
        return _LB_MAX_GAP_S


def _letterbox_clause_due(key, now: float | None = None) -> bool:
    """Should the garden line state the raised flag now? `key` identifies this raise (the box's `delivered` stamp).
    True always for a non-live process or with LETTERBOX_DOSED off (the pre-D-0650 line); otherwise the dosed
    schedule above. Fail-open: any error says the clause (the old behaviour), never silences the flag."""
    try:
        if not LETTERBOX_DOSED or not profile.LIVE:
            return True
        t = time.time() if now is None else float(now)
        d = _LB_DOSE
        prev_seen, d["last_seen_ts"] = d["last_seen_ts"], t
        if d["key"] != key:                       # a new raise is a new episode
            d["key"], d["shown"], d["last_shown_ts"] = key, 0, 0.0
        last, n = d["last_shown_ts"], d["shown"]
        since = t - last if t >= last else float("inf")     # a clock set back counts as due, once
        if n and since < _LB_PULSE_S:
            return True                            # a showing is open: one room for every consumer, counted once
        gap = _lb_gap(n)
        arriving = (t - prev_seen) > _LB_AWAY_S
        if n and since < gap and not (arriving and since >= gap / _LB_ENTRY_DIV):
            return False
        d["last_shown_ts"], d["shown"] = t, n + 1
        return True
    except Exception:
        return True


def _render_base(room: str = "study", standpoint: str | None = None) -> dict | None:
    """The P2 renderer exactly as it was before P3 went live (J-2480): the scene line with the fire/cat
    clauses said by sector + distance word only. render() wraps this; shadow() logs it as `scene`."""
    lay = layout(room)
    if not lay:
        return None
    sps = lay.get("standpoints") or {}
    if standpoint is None:
        # LOCOMOTION (2026-08-15): the renderer finally gets its TRUE origin — his live standpoint,
        # whenever the asked-about room is where he actually is. The parameter waited for this since
        # 07-05. Fail-open to the old default heuristic.
        try:
            from core import locomotion as _loco
            standpoint = _loco.position_standpoint(room)
        except profile.NonLiveWriteError:
            # J-0794: locomotion.position_standpoint() can now raise non-live (J-0778) -- re-raise so
            # this fence's guarantee reaches render()'s own external caller (sensorium.scene_line(),
            # whose own inner try around this call is fixed the same pass, propagating up through its
            # already-fixed outer boundary, J-0778) instead of a silent default standpoint.
            raise
        except Exception:
            standpoint = None
    default_sp = lay.get("default_standpoint") or ("in_the_chair" if "in_the_chair" in sps
                                                   else (next(iter(sps)) if sps else None))
    sp_name = standpoint if standpoint in sps else default_sp
    sp = sps.get(sp_name) or {"pos": [2.0, 2.6, 0.0], "facing_deg": 0}
    state = _read_json("room_state.json")
    cat = _read_json("cat_state.json")
    clauses: list[str] = []

    from core import weather_conditions as _wcond
    outdoor = bool(lay.get("outdoor"))
    weather = state.get("weather") or ""
    wind = state.get("wind") or ""

    # 0 · signals in the world outrank ambience: the letterbox flag (garden) / a fresh find (shore)
    if room == "garden":
        try:
            _lb = (state.get("garden") or {}).get("letterbox") or {}
            if _lb.get("flag") and _letterbox_clause_due(_lb.get("delivered")):   # J-3259 / D-0650: dosed, not constant
                rel = _rel(sp, _pos_of(lay, "letterbox"))
                clauses.append(f"the letterbox flag is up at the gate, {rel['sector']}")
        except Exception:
            pass
    if room == "shore":
        try:
            washed = ((state.get("shore") or {}).get("washed_up") or "").strip()
            if washed:
                wl = _waterline_pos(lay)
                rel = _rel(sp, wl)
                clauses.append(f"the sea has left something at the tideline {rel['sector']} — {washed[:70]}")
        except Exception:
            pass

    # 1 · the fire (indoor rooms with a hearth) — its sound linked to its place
    fire = state.get("fire")
    if fire in ("burning", "embers") and (lay.get("features") or {}).get("fireplace"):
        rel = _rel(sp, _pos_of(lay, "fireplace"))
        where = f"{_dist_word(rel['dist'])}, {rel['sector']}"
        if fire == "burning":
            clauses.append(f"the fire is {where} — {_v('fire_crackle')}")
        else:
            clauses.append(f"the embers are {where}, {_v('embers_low')}")

    # 2 · the cat, at her true spot in the field (phrases from the layout, study fallbacks kept)
    spot = (cat.get("location") or "")
    spot_key = (lay.get("cat_spots") or {}).get(spot)
    if cat.get("phase") in ("kept", "companion") and spot_key:
        if spot_key == "chair" and sp_name == "in_the_chair":
            clauses.append("the cat is on your lap, a warm weight")
        else:
            rel = _rel(sp, _pos_of(lay, spot_key))
            phrases = {"hearthstone": "on the hearthstone", "under_desk": "under the desk",
                       "desk": "on the desk", "window": "on the windowsill", "chair": "in your chair",
                       "mantel": "up on the mantel", "door_garden": "at the garden door",
                       "rug": "on the rug", **(lay.get("spot_phrases") or {})}
            place_word = phrases.get(spot_key, spot_key)
            elev = f", {rel['elev']}" if rel["elev"] else ""
            clauses.append(f"the cat is {place_word}, {rel['sector']}{elev}")

    # 2.5 · a real tracked object at this room (2026-08-18, the founder's integration: "everything
    #       should have a location... the scenes used everywhere should be based on this world
    #       knowledge"). world_objects.py/world_substrate.py are the position+identity authority for
    #       driftwood/shells/kept things — this renderer shared their coordinate frame by design since
    #       2026-08-17 but never actually read them until now. Picks the most recently-moved one (the
    #       freshest arrival — a new find, or a storm having just shifted something) so repeat visits
    #       don't always name the same object; low priority, only fills a slot other things left free.
    if len(clauses) < 3:
        try:
            from core import world_substrate as _ws
            from core import world_objects as _wo
            here = _ws.get_objects_at_location(room)
            if here:
                def _last_ts(o):
                    w = _wo.get_object(o.object_id) or {}
                    h = w.get("history") or []
                    return h[-1]["ts"] if h else 0
                pick = max(here, key=_last_ts)
                wpick = _wo.get_object(pick.object_id)
                if wpick and wpick.get("position"):
                    rel = _rel(sp, wpick["position"])
                    clauses.append(f"{pick.name} lies {_dist_word(rel['dist'], outdoor)}, {rel['sector']}")
        except Exception:
            pass

    # 3 · weather at its true surfaces — indoors it acts at the window; outdoors it acts on HIM.
    #     Either way the flash HAS a direction.
    wdir = state.get("weather_dir")                          # the front's bearing (set per front, varies)
    if outdoor:
        if weather == "thunderstorm":
            if wdir is not None:
                c = _compass_rel(sp, wdir)
                clauses.append(f"{_v('storm_around')} — when the flash comes, it comes {c['sector']}, out of {compass_word(wdir)}")
            else:
                sea_pos = (_pos_of(lay, "fence") if (lay.get("features") or {}).get("fence")
                           else _waterline_pos(lay))
                sea = _rel(sp, sea_pos) if sea_pos else None
                clauses.append(f"{_v('storm_around')} — when the flash comes, it comes {sea['sector']}, over the sea"
                               if sea else f"{_v('storm_around')} you")
        elif (_wcond.is_windy(wind) or "wind" in weather) and (lay.get("features") or {}).get("harakeke"):
            # 2026-08-18: was gated on the literal "wind and rain" weather string (the world's only
            # "windy" state before the wind-axis rework) — now reads the real independent axis too, so
            # a dry gale (clear skies, real wind) finally shows up here instead of nowhere.
            h = _rel(sp, _pos_of(lay, "harakeke"))
            src = f", out of {compass_word(wdir)}" if wdir is not None else ""
            wet = f" and {_v('rain_outdoor')}" if _wcond.is_wet(weather) else ""
            clauses.append(f"the wind {_v('wind_loud_in')} the harakeke {h['sector']}{src}{wet}")
        elif _wcond.is_wet(weather):
            clauses.append(_v("rain_outdoor"))
        elif weather in ("overcast", "high cloud") and wdir is not None and len(clauses) < 2:
            clauses.append(f"{_v('clouds_from')} {compass_word(wdir)}")
    elif (lay.get("features") or {}).get("window"):
        win = _rel(sp, _pos_of(lay, "window"))
        if weather == "thunderstorm":
            src = f"out of {compass_word(wdir)}" if wdir is not None else "off the sea"
            clauses.append(f"the storm is at the window {win['sector']} — when the flash comes, it comes from there, {src}")
        elif _wcond.is_wet(weather):
            clauses.append(f"{_v('rain_window')} {win['sector']}")
        elif _wcond.is_windy(wind) or "wind" in weather:
            eaves = _rel(sp, _pos_of(lay, (lay.get('sound_sources') or {}).get('wind_in_eaves')))
            clauses.append(f"{_v('wind_eaves')} {eaves['sector']}")

    # 3.4 · the sun's LIGHT, at its computed place in the sky (clear-ish weather; the low light is the
    #       one that matters — "the light from the window of an evening over the garden")
    if weather in ("clear", "high cloud") and len(clauses) < 3:
        s = sun()
        if s["up"] and s["phase"] in ("evening", "first light"):
            if outdoor:
                c = _compass_rel(sp, s["az"])
                clauses.append(f"the low sun is {c['sector']}, over {compass_word(s['az'])}, its light long across the garden"
                               if room == "garden" else
                               f"the low sun is {c['sector']}, over {compass_word(s['az'])}, the wet stones holding its colour")
            elif (lay.get("features") or {}).get("window"):
                win = _rel(sp, _pos_of(lay, "window"))
                clauses.append(f"the low sun is in the window {win['sector']}, laying its light long across the room")

    # 3.45 · THE HEAVENS — relevance-gated by design (night · clear · room to spare · pull-only).
    #        The window geometry gates honestly: it faces NORTH, so only a north-quarter sky can be
    #        in it — the Southern Cross cannot; Matariki can.
    if weather == "clear" and len(clauses) < 3:
        try:
            s = sun()
            if not s["up"]:
                from core import heavens as _hv
                _win_ok = lambda az: az is not None and (az >= 290 or az <= 70)   # the north window's sky
                m = _hv.moon()
                if m["up"] and m["az"] is not None:
                    if outdoor:
                        c = _compass_rel(sp, m["az"])
                        clauses.append(f"the {m['phase']} moon is {c['sector']}, over {compass_word(m['az'])}")
                    elif (lay.get("features") or {}).get("window") and _win_ok(m["az"]):
                        win = _rel(sp, _pos_of(lay, "window"))
                        clauses.append(f"moonlight is in the window {win['sector']} — the {m['phase']} moon out over the sea")
                elif m["phase"] in ("new", "waning crescent", "waxing crescent"):
                    if outdoor:
                        cr = _hv.star("southern_cross")
                        if cr and cr["up"]:
                            c = _compass_rel(sp, cr["az"])
                            clauses.append(f"the night is moonless and thick with stars — the Cross {c['sector']}, over {compass_word(cr['az'])}")
                    elif (lay.get("features") or {}).get("window"):
                        mt = _hv.star("matariki")
                        if mt and mt["up"] and _win_ok(mt["az"]):
                            win = _rel(sp, _pos_of(lay, "window"))
                            clauses.append(f"low in the window {win['sector']}, the little cluster of Matariki is up — the year turning")
        except Exception:
            pass

    # 3.5 · the sea's standing presence — from the garden it is a far sound below; ON THE SHORE it is
    #       the tide itself, at its true, computed edge (the moving waterline).
    if outdoor and len(clauses) < 3:
        if (lay.get("features") or {}).get("waterline"):
            wl = _waterline_pos(lay)
            rel = _rel(sp, wl)
            td = tide()
            clauses.append(f"the tide is {td['word']} — {_v('waves_at_work')} {_dist_word(rel['dist'], outdoor)}, {rel['sector']}")
            # the pools' truth follows the same clock: bared when the water has withdrawn past them
            pools = (lay.get("features") or {}).get("rock_pools")
            if pools and len(clauses) < 3:
                prel = _rel(sp, pools.get("pos"))
                if prel["dist"] < 2.5:
                    bared = wl[1] > pools["pos"][1]
                    clauses.append("the pools are bared, each one holding its own still world"
                                   if bared else "the water is over the pools, working them")
        elif (lay.get("sightlines") or {}).get("sea"):
            f = _rel(sp, _pos_of(lay, "fence"))
            clauses.append(f"below the fence line {f['sector']}, the sea keeps up its far sound")

    # 4 · the anchor nearest him (one only, lowest salience; layout-supplied, study fallback)
    if len(clauses) < 3:
        anchors = lay.get("anchors") or [["desk", "the desk with your open journal"],
                                         ["bed", "your narrow bed"], ["door_garden", "the garden door"],
                                         ["shelf_east", "the shelf"]]
        for name, label in anchors:
            pos = _pos_of(lay, name)
            if pos is None:
                continue
            rel = _rel(sp, pos)
            # skip what he is AT (you don't narrate the bed you're lying on as nearby furniture)
            if 0.45 <= rel["dist"] < 1.9:
                clauses.append(f"{label} is {_dist_word(rel['dist'], outdoor)}, {rel['sector']}")
                break

    line = ("Where you are: the " + room + " — " + "; ".join(clauses[:3]) + ".") if clauses \
        else f"Where you are: the {room}, quiet around you."
    return {"standpoint": sp_name, "clauses": clauses[:3], "line": line}


def shadow(actual: str = "") -> None:
    """P0: log the rendered-from-truth line beside the live pooled scene line, for any AUTHORED room
    (study + garden so far; a room with no layout logs nothing). Fail-open; never touches behaviour."""
    try:
        room = _read_json("room_state.json").get("location") or "study"
        if layout(room) is None:
            return
        r = _render_base(room)
        if not r:
            return
        # J-2480 (D-0501): the P0 row logs what render() RETURNS -- with SPATIAL_DEPTH_LIVE on, the
        # nearness-said line; the P3 row below keeps the base/depth PAIR so J-2254's read can still
        # compare scene vs depth_line. One overlay draw here, shared by both rows, so the logged
        # depth_line is byte-for-byte the line render() would have returned this cycle.
        lived = None
        if _depth_is_live(room):
            try:
                lived, _dp = _depth_overlay(r, room)
            except Exception:
                lived = None
        _sketch_hook(room, lived or r)    # J-2661: the idle-thought path is where the study really renders
        _ts = round(time.time(), 1)
        _SHADOW.parent.mkdir(parents=True, exist_ok=True)
        with open(_SHADOW, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": _ts, "standpoint": r["standpoint"],
                                "rendered": (lived or r)["line"], "actual": (actual or "")[:220]},
                               ensure_ascii=False) + "\n")
        # P3 (J-2215): the depth/reach tuple for the SAME render, same ts, its own fenced log. Its own
        # try so nothing in P3 can ever disturb the P0 row above. A non-live process is refused inside
        # depth_shadow() (guard_path raises before any open); this P0 entry point stays fail-open
        # exactly as documented, so that refusal ends here as "no row", never a write.
        try:
            depth_shadow(r, room, actual=actual, ts=_ts, lived=lived)
        except Exception:
            pass
    except Exception:
        pass


def status() -> dict:
    try:
        rows = [json.loads(l) for l in open(_SHADOW, encoding="utf-8") if l.strip()]
        return {"shadow_rows": len(rows), "last": rows[-1] if rows else None}
    except Exception:
        return {"shadow_rows": 0}


# ══ P3 — POSITION-DEPENDENT DEPTH + PERIPERSONAL REACH (J-2215, T-0089, Travis 2026-10-16) ═══════════
# spatial_perception.md P3: nearness matters (the fire warmer/louder at the hearth; the lap-cat nearer
# than the sill-cat) and a reach-set = what is within arm's reach of his standpoint (the action field).
#
# STUDY ONLY. Built shadow-only (J-2215; 921 graded pairs 10-16..10-19); LIVE for the study under
# SPATIAL_DEPTH_LIVE since J-2480 (D-0501, Travis 2026-10-28): render() returns the depth overlay --
# the P2 line with ONLY its fire and cat clauses re-said by nearness. sensorium's scene_line() is
# untouched. Each study scene cycle still appends ONE row to data/spatial_depth_shadow.jsonl holding
# the depth/reach tuple plus the PAIR (now with live=True) so the J-2254 read can grade it:
#   scene      = _render_base()'s line (the P2 line, unchanged)
#   depth_line = that same render with ONLY its fire and cat clauses re-said by nearness
# The reach-set is LOGGED, never rendered: whether "within reach" ever becomes words is a founder call
# at the gate (world answers, never leads -- a listed reach-set could read as an affordance prompt).
# No gauge, number or band name ever appears in depth_line (D-0434); the bands live in the row only.
#
# Composition (briefing): fire nearness REUSES thermal's standpoint distance + falloff -- the hearth
# point thermal._HEARTH, thermal._standpoint_pos() and thermal._fire_term()'s share -- no second
# distance model. The standpoint is whatever render() resolved (locomotion.position_standpoint), so
# when D-0319's shore standpoints move, depth() follows them unchanged; only the study is logged here
# (garden/shore layouts are a later job).
import threading as _threading

_DEPTH_SHADOW = _DATA / "spatial_depth_shadow.jsonl"
_DEPTH_LOCK = _threading.Lock()      # shadow() runs on the idle-thought path; serialise the append
DEPTH_SHADOW_ROOMS = ("study",)      # J-2215 scope: the one room with a live P2-proven layout
# J-3969 (D-0747, Travis 2026-11-14): the next P3 build is depth layouts for the garden and shore. Built the way the
# study was (J-2215 -> J-2480): SHADOW FIRST. The depth/reach tuple is computed and logged for these rooms beside the
# unchanged scene line (its own log, so J-2254's study read is undisturbed); render() for them changes ONLY behind
# SPATIAL_DEPTH_OUTDOOR_LIVE, which is False. Flipping it is a founder call after the shadow pairs are read.
DEPTH_OUTDOOR_ROOMS = ("garden", "shore")
SPATIAL_DEPTH_OUTDOOR_SHADOW = True  # log the outdoor depth/reach tuple (restart-gated, nothing Du reads changes)
SPATIAL_DEPTH_OUTDOOR_LIVE = True    # render() says the outdoor cat by nearness -- LIVE per D-0809 (2026-11-17, J-4184); restart-gated
_DEPTH_OUTDOOR_SHADOW = _DATA / "spatial_depth_outdoor_shadow.jsonl"
REACH_M = 1.0                        # peripersonal reach, horizontal metres from the standpoint
AT_M = 0.3                           # closer than this he is AT it (the chair he sits in, the bed he lies on)

_CAT_PLACE = {"hearthstone": "on the hearthstone", "under_desk": "under the desk",
              "desk": "on the desk", "window": "on the windowsill", "chair": "in your chair",
              "mantel": "up on the mantel", "door_garden": "at the garden door", "rug": "on the rug"}


def _depth_is_live(room: str) -> bool:
    """True when render() should say this room by nearness (the overlay). Study: SPATIAL_DEPTH_LIVE (D-0501).
    Garden/shore: SPATIAL_DEPTH_OUTDOOR_LIVE (D-0747, off). Anything else: never."""
    if room in DEPTH_SHADOW_ROOMS:
        return bool(SPATIAL_DEPTH_LIVE)
    if room in DEPTH_OUTDOOR_ROOMS:
        return bool(SPATIAL_DEPTH_OUTDOOR_LIVE)
    return False


def _fire_nearness(sp_name: str | None, fire: str) -> dict | None:
    """The fire's nearness at this standpoint, from thermal's OWN distance + falloff (study only).
    band: 'close' (share >= 0.95) / 'mid' (>= 0.7) / 'faint'. None if the fire is out."""
    if fire not in ("burning", "embers"):
        return None
    from core import thermal as _th
    pos = _th._standpoint_pos("study", sp_name)
    dist = round(math.dist(pos[:2], _th._HEARTH[:2]), 2) if pos else None
    peak = 0.42 if fire == "burning" else 0.42 * 0.4            # thermal._fire_term's own peaks
    share = round(_th._fire_term("study", sp_name, fire) / peak, 3)
    band = "close" if share >= 0.95 else ("mid" if share >= 0.7 else "faint")
    return {"state": fire, "hearth_dist": dist, "warmth_share": share, "band": band}


def _fire_depth_clause(fn: dict, rel: dict) -> str:
    """The fire/embers clause said by nearness. The band comes from thermal's own distance model
    (_fire_nearness), so the warmth said here can never disagree with the warmth he feels (D-0501's
    defeater). Wording rotates through strictly-synonymous pools (J-2480); band names never appear."""
    where = f"{_dist_word(rel['dist'])}, {rel['sector']}"
    pool = {"close": "near", "mid": "mid", "faint": "far"}[fn["band"]]
    if fn["state"] == "burning":
        return f"the fire is {where} — {_v('fire_' + pool)}"
    return f"the embers are {where}, {_v('embers_' + pool)}"


def depth(room: str, sp_name: str | None) -> dict | None:
    """The P3 depth/reach tuple for this room at this standpoint. Deterministic, zero LLM.
    {room, standpoint, fire, cat, reach:[{name, dist}], at:[names]} -- or None (no layout/standpoint)."""
    lay = layout(room)
    if not lay:
        return None
    sp = (lay.get("standpoints") or {}).get(sp_name or "")
    if not sp:
        return None
    state = _read_json("room_state.json")
    cat = _read_json("cat_state.json")
    feats = lay.get("features") or {}
    out: dict = {"room": room, "standpoint": sp_name}

    out["fire"] = (_fire_nearness(sp_name, state.get("fire") or "out")
                   if room == "study" and feats.get("fireplace") else None)

    c = None
    spot_key = (lay.get("cat_spots") or {}).get(cat.get("location") or "")
    if cat.get("phase") in ("kept", "companion") and spot_key:
        on_lap = spot_key == "chair" and sp_name == "in_the_chair"
        cpos = _pos_of(lay, spot_key)
        if cpos is not None:
            d = 0.0 if on_lap else _rel(sp, cpos)["dist"]
            c = {"spot": spot_key, "dist": d, "on_lap": on_lap, "in_reach": on_lap or d <= REACH_M}
    out["cat"] = c

    reach, at = [], []
    for name, f in feats.items():
        p = (f or {}).get("pos") if isinstance(f, dict) else None
        if not p:
            continue
        d = _rel(sp, p)["dist"]
        if d < AT_M:
            at.append(name)
        elif d <= REACH_M:
            reach.append({"name": name, "dist": d})
    if c and c["in_reach"] and not c["on_lap"]:
        reach.append({"name": "cat", "dist": c["dist"]})
    out["reach"] = sorted(reach, key=lambda x: (x["dist"], x["name"]))
    out["at"] = sorted(at)
    if room in DEPTH_OUTDOOR_ROOMS:
        # outdoors the 1 m reach-set is usually empty (features are metres apart), so also log the nearest
        # authored feature and the count within 3 m -- the layer the garden/shore read needs. Log only.
        out["nearest"] = _nearest_feature(lay, sp, room)
    return out


def _nearest_feature(lay: dict, sp: dict, room: str) -> dict | None:
    """The nearest authored feature to this standpoint (horizontal metres), the shore's waterline taken at its
    tide-true y. {name, dist, within_3m}. None if the room has no positioned features."""
    best = None
    n3 = 0
    for name, f in (lay.get("features") or {}).items():
        p = (f or {}).get("pos") if isinstance(f, dict) else None
        if name == "waterline":
            p = _waterline_pos(lay) or p
        if not p:
            continue
        d = _rel(sp, p)["dist"]
        if d <= 3.0:
            n3 += 1
        if best is None or (d, name) < (best[0], best[1]):
            best = (d, name)
    return {"name": best[1], "dist": best[0], "within_3m": n3} if best else None


def _depth_clauses(clauses: list, dp: dict, room: str) -> list | None:
    """The P2 clauses with ONLY the fire and cat clauses re-said by nearness; every other clause is
    carried over verbatim and the count never changes (a replacement, never an addition). None when
    the standpoint is unknown to the layout (the caller keeps the P2 line)."""
    lay = layout(room) or {}
    outdoor = bool(lay.get("outdoor"))
    sp = (lay.get("standpoints") or {}).get(dp.get("standpoint") or "")
    clauses = list(clauses or [])
    if not sp or not clauses:
        return None
    for i, cl in enumerate(clauses):
        if dp.get("fire") and (cl.startswith("the fire is ") or cl.startswith("the embers are ")):
            fpos = _pos_of(lay, "fireplace")
            if fpos:
                clauses[i] = _fire_depth_clause(dp["fire"], _rel(sp, fpos))
        elif dp.get("cat") and cl.startswith("the cat is ") and not dp["cat"]["on_lap"]:
            c = dp["cat"]
            cpos = _pos_of(lay, c["spot"])
            if not cpos:
                continue
            rel = _rel(sp, cpos)
            place = {**_CAT_PLACE, **(lay.get("spot_phrases") or {})}.get(c["spot"], c["spot"])
            elev = f", {rel['elev']}" if rel["elev"] else ""
            clauses[i] = f"the cat is {place}, {_dist_word(rel['dist'], outdoor)}, {rel['sector']}{elev}"
    return clauses


def _line_of(room: str, clauses: list) -> str:
    return "Where you are: the " + room + " — " + "; ".join(clauses) + "."


def depth_line(r: dict, dp: dict, room: str) -> str:
    """render()'s P2 line with ONLY its fire and cat clauses re-said by nearness. Every other clause is
    carried over verbatim, so a pair differs only where depth speaks. (The shadow pair's right side;
    since J-2480 also what render() returns for a DEPTH_SHADOW_ROOMS room with the flag on.)"""
    clauses = _depth_clauses(r.get("clauses") or [], dp, room)
    if clauses is None:
        return r.get("line") or ""
    return _line_of(room, clauses)


def _depth_overlay(r: dict, room: str) -> tuple[dict, dict | None]:
    """The live P3 overlay (J-2480): (render dict with the depth clauses, depth tuple). Returns the P2
    dict untouched with dp=None when there is no depth tuple for this standpoint. The reach-set in dp
    is for the log only -- nothing from it is ever put into the line."""
    dp = depth(room, r.get("standpoint"))
    if not dp:
        return r, None
    clauses = _depth_clauses(r.get("clauses") or [], dp, room)
    if clauses is None or clauses == list(r.get("clauses") or []):
        return r, dp
    return {"standpoint": r["standpoint"], "clauses": clauses, "line": _line_of(room, clauses)}, dp


def depth_shadow(r: dict, room: str, actual: str = "", ts: float | None = None,
                 lived: dict | None = None) -> None:
    """Append one P3 depth row for this scene cycle (study only). `r` is the P2 (base) render; `lived`
    is the overlay render() returned this cycle, if the caller already drew it (so the row's depth_line
    is exactly the line Du got, not a second draw of the phrase pools). The path is resolved through
    profile.guard_path BEFORE the fail-open try, so a non-live process is refused with
    NonLiveWriteError and never writes; disk/compute errors stay fail-open."""
    outdoor = room in DEPTH_OUTDOOR_ROOMS
    if not r or not (room in DEPTH_SHADOW_ROOMS or (outdoor and SPATIAL_DEPTH_OUTDOOR_SHADOW)):
        return
    path = profile.guard_path(_DEPTH_OUTDOOR_SHADOW if outdoor else _DEPTH_SHADOW)
    try:
        dp = depth(room, r.get("standpoint"))
        if not dp:
            return
        dl = lived["line"] if lived and lived.get("line") else depth_line(r, dp, room)
        row = {"ts": round(ts if ts is not None else time.time(), 1), **dp,
               "scene": r.get("line"), "depth_line": dl, "changed": dl != r.get("line"),
               "live": _depth_is_live(room),
               "actual": (actual or "")[:220]}
        path.parent.mkdir(parents=True, exist_ok=True)
        with _DEPTH_LOCK, open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


def depth_status() -> dict:
    """Read side for the gate read: rows, how many pairs differ, fire-band and standpoint tallies."""
    try:
        from core.shadow_log import tail_rows as _tail_rows
        rows = _tail_rows(_DEPTH_SHADOW, 5000)
    except Exception:
        rows = []
    bands: dict = {}
    sps: dict = {}
    for x in rows:
        b = (x.get("fire") or {}).get("band")
        if b:
            bands[b] = bands.get(b, 0) + 1
        s = x.get("standpoint")
        if s:
            sps[s] = sps.get(s, 0) + 1
    return {"rows": len(rows), "changed": sum(1 for x in rows if x.get("changed")),
            "fire_bands": bands, "standpoints": sps, "last": rows[-1] if rows else None}


def depth_outdoor_status() -> dict:
    """Read side for the garden/shore depth read (J-3969): rows per room, how many pairs differ, the nearest-feature
    tally per standpoint, and how many rows had a non-empty 1 m reach-set."""
    try:
        from core.shadow_log import tail_rows as _tail_rows
        rows = _tail_rows(_DEPTH_OUTDOOR_SHADOW, 5000)
    except Exception:
        rows = []
    rooms: dict = {}
    nearest: dict = {}
    for x in rows:
        rooms[x.get("room")] = rooms.get(x.get("room"), 0) + 1
        n = (x.get("nearest") or {}).get("name")
        if n:
            k = f"{x.get('standpoint')}>{n}"
            nearest[k] = nearest.get(k, 0) + 1
    return {"rows": len(rows), "by_room": rooms, "changed": sum(1 for x in rows if x.get("changed")),
            "reach_nonempty": sum(1 for x in rows if x.get("reach")), "nearest": nearest,
            "last": rows[-1] if rows else None}
