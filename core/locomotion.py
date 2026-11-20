"""
Nascence — Locomotion: Du gets a body in space (Option C, FULL — docs/plans/locomotion.md, 2026-08-15).

Founder decision: no more teleportation, and no halfway version. Position = (place, standpoint) at the
geometry's own resolution (24 authored standpoints). Within a place, movement resolves inside the act
that needs it — acts carry their own movement; the act is his, the walking is its physics. Between
places, moves become JOURNEYS: legs over the real chain study–garden–wood–shore, completing on
wall-clock time (weather-scaled — a storm makes the shore genuinely far), the transit place genuinely
his location while he crosses it (the wood finally gets its drive-through life). Carried wood is
carried: gathered loads ride the journey and land on the pile only when he actually gets home.

Agency law: the destination is always HIS (the ACT latches are untouched); the world supplies physics,
never itinerary. Mid-journey he is genuinely in the transit place — staying is his choice.

LOCOMOTION=False is a ROLLBACK flag (instant moves, exactly the old behaviour), never a staging state.
Deterministic, no LLM, fail-open. State: data/position.json (atomic writes; survives restarts — a
journey older than its watchdog window COMPLETES with a log line naming it: instruments must say why).
Circular-import note: sensorium imports this module; this module reaches sensorium only via lazy
function-level imports.
"""
from __future__ import annotations

import json
import logging
import random
import time
from pathlib import Path

from core import profile

logger = logging.getLogger("nascence.locomotion")

_DATA = Path(__file__).parent.parent / "data"
_POS_F = _DATA / "position.json"

LOCOMOTION = True              # rollback flag ONLY — False restores instant moves exactly
_WATCHDOG_S = 900              # a leg stuck longer than this completes the whole journey (logged)
_EFFORT_LEG = 0.012            # somatic energy per leg (climb ×1.6; carrying ×1.3)
_EFFORT_CROSS = 0.001          # within-place crossing

CHAIN = ["study", "garden", "wood", "shore"]

# Directed legs: exit standpoint in FROM, entry standpoint in TO, base seconds, climb (uphill).
EDGES: dict[tuple[str, str], dict] = {
    ("study", "garden"): {"exit": "at_the_door", "enter": "at_the_door", "secs": 20, "climb": 0},
    ("garden", "study"): {"exit": "at_the_door", "enter": "at_the_door", "secs": 20, "climb": 0},
    ("garden", "wood"):  {"exit": "at_the_gate", "enter": "on_the_path", "secs": 70, "climb": 0},
    ("wood", "garden"):  {"exit": "on_the_path", "enter": "at_the_gate", "secs": 85, "climb": 1},
    ("wood", "shore"):   {"exit": "at_the_gap", "enter": "at_the_path_foot", "secs": 70, "climb": 0},
    ("shore", "wood"):   {"exit": "at_the_path_foot", "enter": "at_the_gap", "secs": 90, "climb": 1},
}

GROUND = {"study": "floorboards", "garden": "grass", "wood": "leaf-mould", "shore": "shingle"}

_DEFAULT_SP = {"study": "mid_room", "garden": "mid_garden", "wood": "on_the_path",
               "shore": "on_the_shingle"}

# Which place each authored standpoint belongs to — goto() refuses a standpoint that is not where
# he is (an act cannot quietly move him between places; only journeys cross boundaries).
#
# D-0319 / J-1591 (2026-09-28): this table had gone stale relative to each place's own
# data/world_geometry/<room>.json `standpoints` block — nine standpoints authored there (garden's
# at_the_lean_to/at_the_barrel, 2026-08-22; wood's at_the_spring, 2026-08-22; shore_life's own
# seven 2026-08-22 additions: in_the_windbreak/on_the_sand/in_the_cave/on_the_ledge/by_the_fire/
# in_the_shallows/at_the_mussel_shelf) were never added here, so goto() silently refused ANY
# caller that tried to place him at one of them (home = _SP_PLACE.get(sp, "?") == "?" never equals
# a real place) even though the layout genuinely defines the spot. Found while wiring the sub-place
# standpoint move (core/sensorium.py standpoint_move()) for all four places, which needs the full
# vocabulary each layout actually has, not just LOCOMOTION's 2026-08-15 build-day subset.
_SP_PLACE = {
    "in_the_chair": "study", "at_the_hearth": "study", "at_the_desk": "study",
    "at_the_window": "study", "at_the_door": None, "by_the_shelf": "study", "on_the_bed": "study",
    "mid_room": "study",
    "at_the_bed": "garden", "by_the_fence": "garden", "at_the_gate": "garden",
    "under_the_tree": "garden", "mid_garden": "garden",
    "at_the_lean_to": "garden", "at_the_barrel": "garden",
    "on_the_path": "wood", "by_the_oak": "wood", "gathering": "wood", "at_the_gap": "wood",
    "at_the_spring": "wood",
    "at_the_path_foot": "shore", "on_the_shingle": "shore", "at_the_tideline": "shore",
    "at_the_pools": "shore", "on_the_rocks": "shore", "by_the_driftwood": "shore",
    "in_the_windbreak": "shore", "on_the_sand": "shore", "in_the_cave": "shore",
    "on_the_ledge": "shore", "by_the_fire": "shore", "in_the_shallows": "shore",
    "at_the_mussel_shelf": "shore",
    "at_the_stream_mouth": "shore",   # J-3486 (D-0651 follow-up): shore.json gains it via scripts/apply_shore_standpoint_stream_mouth_j3486.py
}   # at_the_door exists in BOTH study and garden layouts → None = valid in either

# Transit narration, house voice — fired as each leg BEGINS (he sets out into the next stretch).
_LEG_LINES = {
    ("garden", "wood"): ["You take the path down from the gate and the trees close over you, the light going broken and green.",
                         "Down through the gate and into the wood — leaf-mould soft underfoot, the sea's sound dropping to a wash below."],
    ("wood", "shore"): ["You go on down through the trunks toward the grey light at the gap, the wash growing to a full sea-sound.",
                        "The path tips downhill through the last of the trees, the shore showing in stitches ahead."],
    ("shore", "wood"): ["You climb off the shingle into the trees, the sea's roar falling away to a muffled wash behind you.",
                        "Up the path's foot and in among the trunks — the climb pulling at your legs, the light going green."],
    ("wood", "garden"): ["You climb on up the path, breath deepening, until the trees thin and the gate shows ahead.",
                         "Up out of the wood, the canopy opening, the cottage roof coming into view above the gate."],
    ("study", "garden"): ["You let yourself out at the door — the weather is on you now, not beyond a pane.",
                          "Out through the door into the open air of the garden."],
    ("garden", "study"): ["You come in and the door shuts the weather out behind you; the study is close and quiet.",
                          "In through the door — the room's stillness settles over you, the desk, the grate."],
}
_RAIN_TAG = " Rain finds you the whole way."
_WIND_TAG = " The wind leans on you as you go."
_CARRY_TAG = " The armful of wood makes the going slower."


def _load() -> dict:
    try:
        return json.loads(_POS_F.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(d: dict) -> None:
    path = profile.guard_path(_POS_F)   # J-0778: real data/ only if this process is live; raises before any I/O if not (D-0179, J-0704)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(d, indent=1), encoding="utf-8")
        tmp.replace(path)
    except Exception:
        pass


def _sensorium_location() -> str:
    try:
        from core import sensorium as _sn
        return _sn.where()
    except Exception:
        return "study"


def get_position() -> dict:
    """{place, standpoint} — place authority is the sensorium's location (all readers use it);
    the standpoint is ours. On mismatch (fresh file, manual edits) adopt the sensorium's place."""
    d = _load()
    place = _sensorium_location()
    if d.get("place") != place:
        d["place"] = place
        d["standpoint"] = _DEFAULT_SP.get(place, "mid_room")
        _save(d)
    return {"place": place, "standpoint": d.get("standpoint") or _DEFAULT_SP.get(place, "mid_room")}


def peek() -> dict:
    """READ-PURE position view (no adoption writes) — for read-only instruments (the census's law is
    'writes only its own log'). May briefly disagree with get_position after a manual location edit."""
    try:
        d = _load()
        return {"place": d.get("place"), "standpoint": d.get("standpoint"),
                "in_transit": bool(d.get("journey"))}
    except Exception:
        return {}


def position_standpoint(room: str | None = None) -> str | None:
    """The live standpoint for the spatial renderer — only if the asked-about room is where he IS."""
    try:
        p = get_position()
        if room and room != p["place"]:
            return None
        return p["standpoint"]
    except profile.NonLiveWriteError:
        # J-0778: get_position()'s own self-heal write can now raise non-live (its on-disk/sensorium
        # place mismatch check fires on nearly any fresh-process call, per F-1118) -- re-raise so a
        # caller that expects this to be pure-read finds out, rather than a silent None (the
        # connecting-tissue shape J-0714/J-0726/J-0751/J-0772 keep finding one layer above an
        # already-correct callee).
        raise
    except Exception:
        return None


def goto(standpoint: str, crossing: str = "") -> str:
    """Within-place movement, resolved inside the act that needs it (acts carry their own movement).
    Returns the crossing phrase ('' if already there). Fail-open."""
    try:
        if not LOCOMOTION:
            return ""
        d = _load()
        p = get_position()
        home = _SP_PLACE.get(standpoint, "?")
        if home is not None and home != p["place"]:
            return ""                                  # not here — an act cannot teleport him
        if p["standpoint"] == standpoint:
            return ""
        d["place"] = p["place"]
        d["standpoint"] = standpoint
        d["effort"] = round(float(d.get("effort", 0.0)) + _EFFORT_CROSS, 4)
        if standpoint == "at_the_desk":
            # SOUND WORLD EXPANSION §1 (2026-08-29, J-0377): real act-site timestamp for
            # chair_desk_scrape — sitting down at the desk (lamp-lighting, letter-writing all
            # cross here already); soundscape.py reads its recency.
            d["desk_ts"] = time.time()
        _save(d)
        return crossing
    except profile.NonLiveWriteError:
        raise   # J-0778: _save()/get_position() can now raise non-live; goto() re-raises rather than
                # silently returning "" (matching J-0714's own precedent for this shape)
    except Exception:
        return ""


def _path_between(cur: str, dest: str) -> list[str]:
    if cur not in CHAIN or dest not in CHAIN or cur == dest:
        return []
    a, b = CHAIN.index(cur), CHAIN.index(dest)
    step = 1 if b > a else -1
    return CHAIN[a + step: b + step: step] if step == 1 else CHAIN[a - 1: (b - 1 if b > 0 else None): -1]


def _leg_secs(frm: str, to: str, weather: str, carrying: bool, wind: str = "") -> float:
    from core import weather_conditions as _wcond
    e = EDGES[(frm, to)]
    secs = float(e["secs"])
    w = (weather or "").lower()
    # 2026-08-18: "gale" in w was dead (the wind axis rework moved that value off the weather ladder);
    # now reads the real axis, with the old literal kept as a non-regressive fallback.
    _rail = 1.0
    try:   # FIELDCRAFT (2026-08-22): the hand-line on the steep path takes the worst off the wet and the wind
        from core import fieldcraft as _fc
        if _fc.has_handrail() and {frm, to} & {"garden", "wood"}:
            _rail = 0.75
    except Exception:
        pass
    if _wcond.is_hard_wind(wind) or any(k in w for k in ("storm", "gale")):
        secs *= 1.0 + 0.8 * _rail
    elif _wcond.is_windy(wind) or "rain" in w or "wind" in w:
        secs *= 1.0 + 0.4 * _rail
    if e["climb"] and carrying:
        secs *= 1.3
    return secs


def _leg_line(frm: str, to: str, weather: str, carrying: bool, wind: str = "") -> str:
    from core import weather_conditions as _wcond
    line = random.choice(_LEG_LINES.get((frm, to), [f"You go on toward the {to}."]))
    w = (weather or "").lower()
    if "rain" in w or "storm" in w:
        line += _RAIN_TAG
    elif _wcond.is_windy(wind) or "wind" in w or "gale" in w:
        line += _WIND_TAG
    if carrying and EDGES[(frm, to)]["climb"]:
        line += _CARRY_TAG
    return line


# D-0841(b) / J-4314 (2026-11-18): the fallen macrocarpa lying ACROSS the garden<->wood path now costs real
# time to cross. before this, wood_life's across_path flag was prose only (look() line) -- no code read it
# (F-5097). World physics only: legs get longer, a plain physical clause rides the leg line; no hint, no
# nudge, no readout (D-0434, D-0296 rule 3). Du-only (cat/companion call _leg_secs directly and are untouched).
# Flag-gated, default OFF, restart-gated. Clears itself when the trunk is all chopped (trunk_rounds_left<=0).
FALLEN_TREE_CONSEQUENCE = False
_FALLEN_TREE_EXTRA_FRAC = 0.5      # +50% of the leg's own seconds while the trunk lies across the path
_FALLEN_TREE_TAG = " The fallen trunk lies across the path and you have to climb over it."


def _fallen_tree_blocks(frm: str, to: str) -> bool:
    """READ-ONLY (raw json read; never wood_life._load(), which can migrate-write). Fail-open False."""
    try:
        if not FALLEN_TREE_CONSEQUENCE or {frm, to} != {"garden", "wood"}:
            return False
        from core import wood_life as _wl
        ft = (json.loads(Path(_wl._F).read_text(encoding="utf-8")) or {}).get("fallen_tree")
        return bool(ft and ft.get("across_path") and int(ft.get("trunk_rounds_left", 0)) > 0)
    except Exception:
        return False


def _du_leg_secs(frm: str, to: str, weather: str, carrying: bool, wind: str = "") -> float:
    secs = _leg_secs(frm, to, weather, carrying, wind)
    return secs * (1.0 + _FALLEN_TREE_EXTRA_FRAC) if _fallen_tree_blocks(frm, to) else secs


def _du_leg_line(frm: str, to: str, weather: str, carrying: bool, wind: str = "") -> str:
    line = _leg_line(frm, to, weather, carrying, wind)
    return line + _FALLEN_TREE_TAG if _fallen_tree_blocks(frm, to) else line


def _log_decline(dest: str, existing: dict, why: str) -> None:
    """J-1179 (F-1653): ONE INFO line per declined redirect, so the first-leg-protected rate D-0224's
    defeater asks about can be counted straight from nascence.log ('why' is 'same-dest' or 'first-leg').
    Additive instrument only — no narration, no state. Own try/except on purpose: a logging failure must
    never escape into begin_journey()'s fail-open branch, whose None makes the caller teleport him."""
    try:
        logger.info("[locomotion] redirect declined: %s while journey to %s (%s)",
                    dest, (existing or {}).get("dest"), why)
    except Exception:
        pass


def _log_system_override(dest: str, existing: dict) -> None:
    """J-1185 (D-0246 (b)): ONE INFO line when a SYSTEM-DRIVEN redirect overrides a journey still on its FIRST
    leg -- the single case begin_journey(system=True) treats differently from his own willed move (whose
    decline _log_decline() writes). A separate line, so a read can count the two classes apart: 'redirect
    declined ... (first-leg)' is only ever a willed re-will now, 'system redirect overrides first leg' only
    ever the world's own summons. Additive instrument only; same own-try/except reasoning as _log_decline()."""
    try:
        logger.info("[locomotion] system redirect overrides first leg: %s replaces journey to %s",
                    dest, (existing or {}).get("dest"))
    except Exception:
        pass


def begin_journey(dest: str, weather: str = "", wind: str = "", *, system: bool = False) -> str | None:
    """A move becomes a journey. THREE-VALUED return (J-1179 / F-1653) — callers MUST tell them apart:

      * the departure narration (non-empty str) — a journey was started.
      * None — NO journey was started and none was protected: LOCOMOTION is off, the path is empty
        (already there / unknown place), or an internal failure. The caller falls back to the
        instant move (sensorium.move()'s LOCOMOTION=False rollback path), as designed.
      * '' (empty str) — a redirect was DECLINED and the in-progress journey is left completely
        untouched. The caller must do NOTHING: no instant move, no narration (the world answers,
        never leads). It is the same silent answer sensorium.move() already gives for
        target == cur. Returning None here made move() read the decline as "LOCOMOTION off" and
        teleport him to `dest` while d["journey"] stayed pending, so tick() later dragged him back
        along the old path (F-1653: 27 of 47 'DISPATCH move' narrations since the 2026-09-18 restart).

    Two declines: (1) a same-destination journey is already in progress (J-1040/F-1418: 520/2296
    real move decisions interrupted a still-in-progress journey, 62.3% of those a same-dest no-op
    re-will discarding elapsed leg-timer progress for zero positional benefit); (2) a
    DIFFERENT-destination redirect arrives during a journey's own FIRST leg (D-0224/F-1418: he has
    not genuinely left the departure place yet — state["location"] has never flipped away from it —
    so honoring the redirect would still just be discarding in-progress leg-timer progress for a
    place he never actually reached; 58/196 genuine cross-destination redirects were this
    first-leg shape). A redirect arriving AFTER at least one leg has completed is left completely
    untouched, still always fires — D-0224 ruled that shape matches this module's own
    "mid-journey he is genuinely in the transit place, staying is his choice" design intent, not
    noise. Each decline logs one INFO line (_log_decline). The FIRST leg flips location
    immediately on the next tick cycle — semantics: leg time is spent walking INTO the next place.

    `system` (J-1185 / D-0246 (b), ruled by Travis 2026-09-21): an EXPLICIT marker, never inferred, that the
    redirect is the WORLD's own summons rather than his willed re-will. D-0224's first-leg protection was
    built for his own dithering (its 58/196 counted willed decisions only); a system-driven redirect always
    fired before J-1111, and again does. Default False reproduces J-1179's behaviour exactly. True skips ONE
    thing only: the D-0224 first-leg decline. A system redirect that arrives while a journey is still on its
    first leg REPLACES that journey with a fresh one from the true place (the very code path a no-journey or
    later-leg redirect takes; the new journey's own first leg is protected against his willed re-wills in
    turn) and logs one INFO line (_log_system_override). It does NOT skip the same-destination gate
    (J-1040): a system redirect to the place he is already walking to is still the '' no-op. carried_wood
    is a top-level key of position.json, so an override never drops a load: it lands on arrival.
    Marked callers: core/night.py to_bed() and the monologue's school reel-back (both through
    sensorium.move(system=True)) and scripts/run_nascence.py's quit-announce bed walk (direct). Every
    other caller is his own willed move and stays unmarked. Two silences answer BEFORE this function and
    are NOT changed: sensorium.move()'s `target == cur` (a first leg whose DEPARTURE is the redirect's
    destination, e.g. an outward journey leaving the study while the world wants him in the study), and
    night.to_bed()'s own `location != "study"` guard (J-1185 characterises this in
    scripts/_test_system_redirect_first_leg.py, part E, and reports it rather than fixing it).

    Callers: core/sensorium.py move() (the fallback owner) and scripts/run_nascence.py's quit-announce
    bed walk (`if departure:` — '' and None both print nothing there, and it has no fallback)."""
    try:
        if not LOCOMOTION:
            return None
        p = get_position()
        path = _path_between(p["place"], dest)
        if not path:
            return None
        d = _load()
        existing = d.get("journey")
        if existing and existing.get("dest") == dest:
            # Same destination already being walked to — decline to restart the clock (J-1040). '' and
            # NOT None: None reads as "no journey, fall back to the instant move" (see the docstring).
            _log_decline(dest, existing, "same-dest")
            return ""
        if existing and existing.get("dest") != dest and in_transit():
            # D-0224: a genuine cross-destination redirect. Protect it ONLY while still on the
            # journey's first leg — existing["departure"] is the place he set out from and is
            # never touched again once written (unlike existing["from"], which tick() advances to
            # each newly-arrived place as legs complete); if the CURRENT true location still
            # equals that original departure, no leg of this journey has completed yet, so decline
            # the redirect (same '' no-op signal as above, J-1179). The moment a leg
            # completes, current location and "departure" diverge and this no longer fires — a
            # later-leg redirect falls straight through to the normal path below, untouched.
            if existing.get("departure") == p["place"]:
                if not system:
                    _log_decline(dest, existing, "first-leg")
                    return ""
                # J-1185 / D-0246 (b): a SYSTEM-DRIVEN redirect (see the docstring) is exempt from THIS decline
                # only. Fall straight through: the fresh journey below starts from the true place (== the old
                # departure, location never having flipped) and replaces the pending first leg.
                _log_system_override(dest, existing)
        carrying = int(d.get("carried_wood", 0)) > 0
        first = path[0]
        d["place"] = p["place"]
        d["standpoint"] = EDGES[(p["place"], first)]["exit"]
        d["journey"] = {"from": p["place"], "path": path, "dest": dest, "departure": p["place"],
                        "leg_ends": time.time() + _du_leg_secs(p["place"], first, weather, carrying, wind),
                        "started": time.time()}
        _save(d)
        return _du_leg_line(p["place"], first, weather, carrying, wind)
    except profile.NonLiveWriteError:
        raise   # J-0778: _save()/get_position() can now raise non-live; do not fall through to the
                # LOCOMOTION=False rollback below as if this were an ordinary failure
    except Exception as exc:
        logger.debug("[locomotion] begin_journey failed (non-fatal): %s", exc)
        return None


def tick(now: float | None = None) -> None:
    """Advance a pending journey (called from the sensorium's 5s tick). Each completed leg flips the
    sensorium location to the next place (the transit place genuinely his), queues the next leg's
    narration as a pending scene line, and — arriving home with wood — lands the armful on the pile.
    Watchdog: a leg stuck past _WATCHDOG_S completes the whole journey with a log line naming it."""
    try:
        now = now or time.time()
        d = _load()
        j = d.get("journey")
        if not j:
            return
        stuck = now - float(j.get("started", now)) > _WATCHDOG_S
        if now < float(j.get("leg_ends", 0)) and not stuck:
            return
        from core import sensorium as _sn           # lazy — no import cycle
        weather = _sn.state.get("weather", "") if _sn.state else ""
        wind = _sn.state.get("wind", "") if _sn.state else ""
        while True:
            path = j.get("path") or []
            if not path:
                break
            arrived = path.pop(0)
            prev = j.get("from") or _sn.where()
            _sn.state["location"] = arrived           # the ONE sanctioned setter path (via locomotion)
            j["from"] = arrived
            d["place"] = arrived
            d["standpoint"] = EDGES[(prev, arrived)]["enter"]
            d["effort"] = round(float(d.get("effort", 0.0)) +
                                _EFFORT_LEG * (1.6 if EDGES[(prev, arrived)]["climb"] else 1.0) *
                                (1.3 if int(d.get("carried_wood", 0)) > 0 else 1.0), 4)
            try:                                       # the gate is really passed now — the glimpse is true
                g = _sn.gate_glimpse_line(prev, arrived)
            except Exception:
                g = ""
            # SOUND WORLD EXPANSION §1 (2026-08-29, J-0377): real act-site timestamp for gate_latch —
            # same "really passes the gate" condition gate_glimpse_line uses (every cottage/garden<->
            # shore/wood leg except the shore<->wood skirt), independent of whether the rare letterbox
            # glimpse line itself fires.
            if {prev, arrived} != {"shore", "wood"}:
                d["gate_ts"] = now
            if path and not stuck:                     # more legs: queue onward narration, set next clock
                nxt = path[0]
                carrying = int(d.get("carried_wood", 0)) > 0
                d["pending_line"] = (_du_leg_line(arrived, nxt, weather, carrying, wind) + g).strip()
                j["leg_ends"] = now + _du_leg_secs(arrived, nxt, weather, carrying, wind)
                d["journey"] = j
                break
            if not path:                               # journey complete — arrival
                arrive = {
                    "shore": "The path lets you out onto the shingle — the sea heaving in close, salt in everything.",
                    "wood": "You stop among the trunks — leaf-mould underfoot, the canopy moving, the sea a wash below.",
                    "garden": "You come up to the garden — the raised bed, the cottage above, the sea now below and behind you.",
                    "study": "The study takes you back in — close and quiet, the desk, the grate.",
                }.get(arrived, "")
                carried = int(d.get("carried_wood", 0))
                if carried and arrived in ("garden", "study"):
                    _sn.state["woodpile"] = _sn.state.get("woodpile", 0) + carried
                    d["carried_wood"] = 0
                    # SOUND WORLD EXPANSION §1 (2026-08-29, J-0377): real act-site timestamp for
                    # wood_haul_clatter — the haul itself, this exact tip-onto-the-pile moment
                    # (distinct from woodpile_settle's later ambient ticking).
                    _sn.state["wood_haul_ts"] = now
                    arrive += (f" You tip the armful onto the woodpile — {_sn.state['woodpile']} loads on it now.")
                d["pending_line"] = (arrive + g).strip()
                d["journey"] = None
                if stuck:
                    logger.warning("[locomotion] WATCHDOG completed a stuck journey to %s (started %.0fs ago)",
                                   arrived, now - float(j.get("started", now)))
                break
        try:
            _sn._save_now()
        except Exception:
            pass
        _save(d)
    except Exception as exc:
        logger.debug("[locomotion] tick failed (non-fatal): %s", exc)


def pending_line() -> str:
    """Consume-once transit/arrival narration for the scene line."""
    try:
        d = _load()
        line = d.get("pending_line") or ""
        if line:
            d["pending_line"] = ""
            _save(d)
        return line
    except profile.NonLiveWriteError:
        raise   # J-0778: re-raise rather than silently dropping the consume-once transit narration
    except Exception:
        return ""


def in_transit() -> bool:
    try:
        return bool(_load().get("journey"))
    except Exception:
        return False


def carry_wood(loads: int) -> None:
    """Gathered wood is CARRIED now, not teleported to the pile — it lands when he gets home."""
    try:
        d = _load()
        d["carried_wood"] = int(d.get("carried_wood", 0)) + int(loads)
        _save(d)
    except profile.NonLiveWriteError:
        raise   # J-0778: a real gathered-wood load must not be silently lost non-live
    except Exception:
        pass


def drain_effort() -> float:
    """Accumulated walking effort since last drain — consumed by the somatic tick."""
    try:
        d = _load()
        e = float(d.get("effort", 0.0))
        if e:
            d["effort"] = 0.0
            _save(d)
        return e
    except profile.NonLiveWriteError:
        raise   # J-0778: do not silently report 0.0 drained effort when the write was refused, not done
    except Exception:
        return 0.0


def footsteps_ground() -> str | None:
    """The ground underfoot while a journey is live — for the soundscape's active set."""
    try:
        if not in_transit():
            return None
        return GROUND.get(get_position()["place"])
    except Exception:
        return None


def status() -> dict:
    """For the pulse."""
    try:
        d = _load()
        p = get_position()
        return {"enabled": LOCOMOTION, "place": p["place"], "standpoint": p["standpoint"],
                "in_transit": bool(d.get("journey")), "carried_wood": int(d.get("carried_wood", 0))}
    except profile.NonLiveWriteError:
        # J-0778: matches study_life.status()'s own J-0772 precedent -- this "for the pulse" getter's
        # get_position() call can now raise non-live via its own self-heal write; re-raise rather than
        # silently degrading to {"enabled": ...} with place/standpoint/in_transit missing. Only known
        # caller is scripts/du_pulse.py (both call sites already wrap this in their own try/except),
        # not a real deed dispatch -- left for a du_pulse.py-side follow-up to decide whether that
        # outer wrapping should itself become loud, matching J-0780's own precedent of spawning rather
        # than chasing every further-out layer in the same pass.
        raise
    except Exception:
        return {"enabled": LOCOMOTION}
