"""
core/cat_sounds.py — HER VOICE: sounds pinned to the cat's own state, carried to him by position
=================================================================================================
2026-09-05 (T-0050 → docs/staged/cat_overhaul.md, Part C1). Founder: "pin sounds to the cat, and then Du one
day can call the cat." Until now she had one sound — the purr, and only asleep in the study (soundscape's
_sec_study_main). Everything else she does with her voice lived only as prose in cat_content.py, fired by
nothing, heard from nowhere.

WHAT THIS IS. Each sound below is a Sound-Space point on `object: "the kept cat"` (registered in
core/soundscape._SOUNDS, so the stick test / census / dosed reads see one object with many spokes) and is
EMITTED HERE from her state machine (data/cat_state.json: location, activity, mood, the greeting stamp, the
feed stamp) — never from a rendered line. Two classes, the soundscape's own: EVENTS fire once on a state
transition — either a real one-shot (the greeting trill, the thump off the sill, the cargo yowl) or, for a
key that HOLDS (the meow at a shut door, the demand for food, chattering at birds), once per real EPISODE
ONSET plus a cooldown before the same key can sound again (J-0996, 2026-09-15 — a multi-hour hold is one
line, not a drone; see the KEYS table's own dosing note); BEDS are present while the state holds (lapping at
the saucer, the rustle under the desk in a storm).

THE CARRY LAW (new). A sound is pinned to HER position and he is at HIS; distance + bearing come from
soundscape.propagate_historical_acoustic_event (built 08-10, joined only to the storm surge until now). Each
key has a REACH in metres (calm air, open ground); the house wall cuts it (door open 0.7 / window open 0.6 /
shut 0.3), weather masks it (rain 0.8, wind 0.75, hard wind 0.5, thunder 0.4). Audible = the cut reach still
covers the distance. What he cannot hear is gone — the tree-falls law (soundscape, 2026-08-16) — the ledger
below is an INSTRUMENT, not his record; nothing here writes to his memory.

POSITIONS. cat._ZONE_POSITIONS is a per-PLACE frame (its "shore" sits 8 m from the study — the shore layout's
own origin), so it cannot measure a carry across places. `_POS` here is one chain frame in metres along
locomotion.CHAIN (study → garden ~20 m → wood ~70 m → shore ~70 m); it exists only for this law and touches
nothing else (her `position` field is left exactly as it was).

SHADOW-FIRST (the house rule; life.RENDER's pattern). RENDER=False: every emission is logged to
data/cat_sound_ledger.jsonl as kind="would_sound" with what he WOULD have heard (the line, from
cat_content.SOUNDS: a "here" pool when he is in the room with her, a "carried" pool when the sound reaches
him from elsewhere) and NOTHING enters active_sounds, the percept rail, the census or his prompt. Flip
without a restart: data/life_flags.json {"cat_sounds_render": true} (scripts/life_flags.py cat_sounds on).
With RENDER on, soundscape's `_sec_cat` row reads audible_now() and the keys enter active_sounds like any
other voice (exposures banked by world_tick, census tuples, the percept rail once its lines are wired — a
flip-time job, not this build).

Zero LLM. Read-only toward cat_state.json, room_state.json, study state. Fail-open everywhere: a sound that
cannot be computed is a sound that did not happen.
"""
from __future__ import annotations

import json
import logging
import random
import time
from pathlib import Path

from core import profile

logger = logging.getLogger("nascence.cat_sounds")

_DATA = Path(__file__).parent.parent / "data"
_LEDGER = _DATA / "cat_sound_ledger.jsonl"
_FLAGS_F = _DATA / "life_flags.json"

RENDER = False              # shadow: log would_sound rows, emit nothing. Hot override: life_flags.json cat_sounds_render
_SAMPLE_S = 60.0            # her voice is sampled once a minute (cat.tick moves her every ~180 s; transitions are caught)
_MAX_DT_S = 300.0           # downtime guard (world_tick's own): no burst after a stopped stretch
_AUDIBLE_WINDOW_S = 90.0    # how long an emitted, audible key stays "sounding now" for active_sounds when rendering

# ── the keys: reach in metres (calm air, open ground), class, per-hour rate while the state holds ──────────
# Reach is the honest loudness of a small cat: a purr is a same-room sound; the food demand carries across a
# garden; the arrival yowl (the muffled cargo call) is the loudest thing she makes short of a fight.
#
# PER-EPISODE DOSING (2026-09-15, F-1367/J-0996, D-0217): cat_meow_at_door/cat_demand/cat_chatter used to
# roll a fresh Poisson-lite count from `rate` on EVERY _SAMPLE_S sample for as long as their `holds` state
# below stayed true -- for a real multi-hour demanding_food/at-the-door stretch (common: F-1330/F-1354, Du
# essentially never wills a feed, D-0163's hunting fallback only engages past 10h unfed) that meant dozens
# of near-identical emissions for what is really ONE episode. F-1367's own week-scale ledger read
# (data/cat_sound_ledger.jsonl, 1104 rows, 4.67 days) found cat_demand alone would put ~69.4 audible
# lines/day into his perception if RENDER were flipped -- one every ~21 minutes, around the clock -- a
# firehose against this plan's own Part B4 "dosed reads, not a firehose" law. `cooldown_s` below switches a
# key from that old per-sample roll (see emissions()'s `holds` loop) to firing at most once per real
# EPISODE ONSET (the holds-state's own False->True transition) and only once `cooldown_s` has passed since
# this key last actually sounded -- so one long hold produces one line, not a drone, and a state that
# flickers off-and-back-on inside the cooldown window (core/cat.py:486-487's own 180s movement tick
# re-rolls "demanding_food" only ~50% of the time whenever hungry, so one real hunger stretch flickers
# on/off every 1-3 ticks) reads as the SAME episode, not a new one. 3600s mirrors this file family's own
# per-hour cooldown convention (core/cat.py's HUNT_COOLDOWN; J-0631's per-hour handling budget) -- long
# enough to swallow that flicker, short enough that a genuinely NEW hunger stretch (hungry is only even
# rollable 5h+ after last_fed, core/cat.py:451) still sounds. `rate` stays on these three keys as the real
# per-hour physical rate (documentation, and the fallback path in emissions() for any future holds-key that
# opts OUT of dosing) but no longer drives firing frequency once cooldown_s is set. cat_trill/cat_yowl_cargo/
# cat_thump (already one_shot, already onset-only with no rate-roll at all) and cat_lapping/cat_storm_rustle
# (class="bed", an always-while-holds background texture, not an event) are untouched -- J-0996's own scope.
KEYS = {
    "cat_trill":         {"reach": 30.0, "cls": "event", "rate": 40.0,  "one_shot": True},                     # the greeting chirrup
    "cat_meow_at_door":  {"reach": 25.0, "cls": "event", "rate": 30.0,  "cooldown_s": 3600.0},                 # asking in / asking out
    "cat_demand":        {"reach": 40.0, "cls": "event", "rate": 20.0,  "cooldown_s": 3600.0},                 # the flat repeated vowel
    "cat_chatter":       {"reach": 6.0,  "cls": "event", "rate": 12.0,  "cooldown_s": 3600.0},                 # jaw-juddering at birds
    "cat_yowl_cargo":    {"reach": 45.0, "cls": "event", "rate": 40.0,  "one_shot": True},                     # arriving with a mouse
    "cat_thump":         {"reach": 10.0, "cls": "event", "rate": 40.0,  "one_shot": True},                     # off the sill / desk
    "cat_lapping":       {"reach": 4.0,  "cls": "bed"},                                                        # at the saucer
    "cat_storm_rustle":  {"reach": 3.0,  "cls": "bed"},                                                        # under the desk, thunder
    # B3 (J-2470, core/cat_tom, D-0507 (c)): the tom in the garden. cat_hiss / cat_growl are HERS, at him (the
    # stand-off on the wall, the spit at the saucer, the fight; the growl through the glass, the aftermath) — one
    # per episode onset like the other holds-keys. distant_yowl is HIS: the long rising yowl on the wall at night,
    # a bout that favours the small hours — a per-sample roll at `rate` while the bout holds (a bout is a few
    # cries, not one), pinned to HIS position (cat_tom.sound_origin), carried by the same law.
    "cat_hiss":          {"reach": 30.0, "cls": "event", "rate": 20.0,  "cooldown_s": 600.0},                  # at the tom: a stand-off, the fight (the wall -> the study door, like the trill)
    "cat_growl":         {"reach": 12.0, "cls": "event", "rate": 10.0,  "cooldown_s": 900.0},                  # at the tom through the glass
    "distant_yowl":      {"reach": 150.0, "cls": "event", "rate": 6.0},                                        # HIS voice on the wall at night
}
_TOM_KEYS = frozenset({"distant_yowl"})     # keys whose origin is the TOM's position, not hers

_INDOORS = {"by_the_fire", "windowsill", "on_the_desk", "on_your_lap", "under_desk", "mantel", "indoors",
            "under_the_bed", "cupboard_top"}      # C4 (J-2469): her two hidden spots in the house are in the house
_RAISED = {"windowsill", "on_the_desk", "mantel", "cupboard_top"}   # C4: coming off the cupboard top is a thump too
_FLOOR_IN = {"by_the_fire", "indoors", "under_desk", "on_your_lap", "under_the_bed"}

# ── the chain frame (metres) — see the module note; NOT cat._ZONE_POSITIONS ──────────────────────────────
_POS = {
    "by_the_fire": [0.5, 0.5, 0.0], "on_your_lap": [0.2, 0.2, 0.4], "on_the_desk": [0.1, 0.8, 0.7],
    "windowsill": [0.0, 2.0, 0.9], "under_desk": [0.3, 0.7, 0.0], "mantel": [0.5, 0.5, 1.2], "indoors": [0.0, 1.0, 0.0],
    "doorstep": [1.0, 3.0, 0.1], "garden": [2.0, 15.0, 0.5], "garden_wall": [3.0, 22.0, 1.5],
    "wood": [0.0, 90.0, 2.0], "shore": [-20.0, 150.0, -8.0], "away_hunting": [30.0, 60.0, 3.0],
    # C4 (J-2469, cat.HIDDEN_SPOTS): absent is not silent -- a sound from a hidden spot carries from where it is
    "under_the_bed": [-1.0, 1.5, 0.1], "cupboard_top": [-1.2, 0.5, 1.8],
    "lean_to": [4.0, 8.0, 0.3], "wood_shed": [5.0, 12.0, 0.3], "hedge_bottom": [-3.0, 16.0, 0.1],
    "water_butt_lid": [2.5, 5.0, 1.0], "roof": [0.5, 1.5, 4.0], "neighbours_wall": [7.0, 20.0, 1.5],
}
_HIS = {   # his position by place and standpoint (locomotion's authored standpoints); place default first
    "study": {"_": [0.0, 1.0, 0.0], "mid_room": [0.0, 1.0, 0.0], "at_the_window": [0.0, 1.8, 0.5],
              "at_the_door": [1.0, 2.6, 0.1], "at_the_hearth": [0.6, 0.6, 0.0], "at_the_desk": [0.1, 0.6, 0.4],
              "in_the_chair": [0.3, 0.4, 0.3], "on_the_bed": [-1.0, 1.5, 0.4], "by_the_shelf": [-1.0, 0.5, 0.5]},
    "garden": {"_": [2.0, 15.0, 0.5], "mid_garden": [2.0, 15.0, 0.5], "at_the_door": [1.0, 3.2, 0.1],
               "at_the_gate": [3.0, 21.0, 1.0]},
    "wood": {"_": [0.0, 90.0, 2.0], "on_the_path": [0.0, 90.0, 2.0], "at_the_gap": [-5.0, 110.0, 0.0]},
    "shore": {"_": [-20.0, 150.0, -8.0], "on_the_shingle": [-20.0, 150.0, -8.0], "at_the_path_foot": [-12.0, 135.0, -5.0]},
}
_PLACE_WORD = {"doorstep": "beyond the door", "garden": "from the garden", "garden_wall": "from the bottom of the garden",
               "wood": "from the wood", "shore": "from down at the shore", "away_hunting": "from somewhere out past the wall",
               # C4 (J-2469): a carried sound from a hidden spot says roughly where, never what she is doing there
               "under_the_bed": "from somewhere low in the room", "cupboard_top": "from somewhere high in the room",
               "lean_to": "from the lean-to", "wood_shed": "from the wood shed", "hedge_bottom": "from the bottom of the hedge",
               "water_butt_lid": "from over by the water-butt", "roof": "from up on the roof", "neighbours_wall": "from the far side of the wall"}

_mem: dict = {"last": 0.0, "act": None, "loc": None, "greet_ts": 0.0, "audible": {},
              "holds_prev": {}, "last_fired": {},      # J-0996: per-episode dosing state, see KEYS note
              "last_line_idx": {}, "audible_line": {}, # J-1175: anti-repeat pick state; percept-rail reuse
              "answer_ts": 0.0, "trill_answer": None}  # C3 (J-2468): the trill that answers his call
_flags_cache: dict = {"ts": 0.0, "v": {}}


# ── flags / io ────────────────────────────────────────────────────────────────────────────────────────────
def _flags() -> dict:
    now = time.time()
    if now - _flags_cache["ts"] < 10.0:
        return _flags_cache["v"]
    v = {}
    try:
        if _FLAGS_F.exists():
            v = json.loads(_FLAGS_F.read_text(encoding="utf-8")) or {}
    except Exception:
        v = {}
    _flags_cache["ts"], _flags_cache["v"] = now, v
    return v


def render_on() -> bool:
    v = _flags().get("cat_sounds_render")
    return bool(RENDER if v is None else v)


def _log(row: dict) -> None:
    path = profile.guard_path(_LEDGER)   # J-0733: real data/ only if this process is live; raises before any I/O if not (D-0179, J-0704)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


# ── the world around the sound (each read fail-open, each replaceable in a test) ────────────────────────
def _his_position() -> tuple[str, str, list[float]]:
    """(place, standpoint, xyz in the chain frame). Place authority is the sensorium's; standpoint locomotion's."""
    place, sp = "study", "_"
    try:
        from core import sensorium as _s
        if not _s.state:
            _s._load()
        place = str(_s.state.get("location") or "study")
    except Exception:
        pass
    try:
        from core import locomotion as _loco
        sp = str(_loco.peek().get("standpoint") or "_")   # peek: no write on a place mismatch (get_position saves)
    except Exception:
        sp = "_"
    table = _HIS.get(place) or _HIS["study"]
    return place, sp, list(table.get(sp) or table["_"])


def _house_open() -> tuple[bool, bool]:
    """(door_open, window_open) of the study — the wall's two gaps."""
    try:
        from core import study_life as _sl
        st = _sl._st()
        return bool(st.get("door_open")), bool(st.get("window_open"))
    except Exception:
        return False, False


def _weather() -> tuple[str, str]:
    try:
        from core import sensorium as _s
        if not _s.state:
            _s._load()
        return str(_s.state.get("weather") or ""), str(_s.state.get("wind") or "")
    except Exception:
        return "", ""


def _tom_acts(name: str) -> frozenset:
    """B3 (J-2470): her tom-reaction activities, read from core/cat_tom so the two files cannot drift. Empty
    (never holds) when the tom module is absent."""
    try:
        from core import cat_tom as _ct
        return getattr(_ct, name) or frozenset()
    except Exception:
        return frozenset()


def _tom_yowling(now: float) -> bool:
    """B3 (J-2470): is the tom in his yowling bout right now? False when he is not in the garden or not built."""
    try:
        from core import cat_tom as _ct
        return bool(_ct.yowling_now(now))
    except Exception:
        return False


def _tom_origin() -> tuple[list[float] | None, str]:
    """B3 (J-2470): (his position in the chain frame, the location word his voice carries) — None, '' when absent."""
    try:
        from core import cat_tom as _ct
        return _ct.sound_origin(), _ct.sound_loc_word()
    except Exception:
        return None, ""


def _birds_about() -> bool:
    """A bird row present and voicing in the garden right now (the living world's own read) — what she
    chatters at through the glass. False when nothing is there to chatter at."""
    try:
        from core import life as _life
        keys = _life.sounds_active("garden")
        return any(k not in ("blackbird_alarm", "dawn_chorus") for k in keys)
    except Exception:
        return False


# ── the carry law ──────────────────────────────────────────────────────────────────────────────────────────
def _transit_origin(state: dict) -> list[float] | None:
    """B1 (J-2465, cat_overhaul): mid-leg she has no fixed spot — her sound comes from the midpoint of the
    leg she is on (the chain frame's own per-place points; the study is its door). None when not in transit,
    so carry() answers 'no position' exactly as before for any location it does not know."""
    t = (state or {}).get("transit") or {}
    if (state or {}).get("location") != "in_transit" or not t:
        return None
    pt = {"study": _POS["doorstep"], "garden": _POS["garden"], "wood": _POS["wood"], "shore": _POS["shore"]}
    a, b = pt.get(str(t.get("from") or "")), pt.get(str(t.get("to") or ""))
    if not a or not b:
        return None
    return [round((a[i] + b[i]) / 2.0, 1) for i in range(3)]


def carry(key: str, cat_loc: str, his_place: str, his_pos: list[float], door_open: bool, window_open: bool,
          weather: str, wind: str, origin: list[float] | None = None, reach: float | None = None) -> dict:
    """Does this sound, from where she is, reach where he is? Returns dist, bearing, audible, and why.
    `origin` (B1, J-2465) overrides the _POS lookup for a location that has no fixed point (a leg in
    progress: see _transit_origin); every existing caller passes nothing and is byte-identical.
    `reach` (C3, J-2468) overrides the KEYS reach for a sound that is not one of hers — his call, run
    through the same wall and weather in REVERSE (his position the origin, hers the observer; the distance
    is symmetric, the wall and the weather are the same wall and weather). Default: byte-identical."""
    spec = KEYS.get(key) or {}
    if reach is not None:
        spec = dict(spec, reach=float(reach))
    origin = origin if origin is not None else _POS.get(cat_loc)
    if origin is None:
        return {"audible": False, "why": "no position", "dist_m": None, "bearing": None}
    she_in = cat_loc in _INDOORS
    he_in = his_place == "study"
    barrier = 1.0
    why = []
    if she_in != he_in:
        barrier = 0.7 if door_open else 0.6 if window_open else 0.3
        why.append("door open" if door_open else "window open" if window_open else "house shut")
    mask = 1.0
    w = (weather or "").lower()
    try:
        from core import weather_conditions as _wc
        from core import soundscape as _snd
        if "thunder" in w:
            mask *= 0.4; why.append("thunder")
        elif _wc.is_wet(w):
            mask *= 0.8; why.append("rain")
        if _snd._is_hard_wind(wind):
            mask *= 0.5; why.append("hard wind")
        elif _snd._is_windy(wind) or "wind" in w:
            mask *= 0.75; why.append("wind")
    except Exception:
        pass
    reach_eff = float(spec.get("reach", 5.0)) * barrier * mask
    try:
        from core import soundscape as _snd2
        ac = _snd2.propagate_historical_acoustic_event(f"cat_{key}", origin, key, observer_pos=his_pos,
                                                       max_audible_dist=reach_eff)
    except Exception:
        ac = None
    if ac is None:
        dx, dy, dz = (origin[i] - his_pos[i] for i in range(3))
        dist = round((dx * dx + dy * dy + dz * dz) ** 0.5, 1)
        return {"audible": False, "why": ", ".join(why) or "too far", "dist_m": dist, "bearing": None,
                "reach_eff": round(reach_eff, 1)}
    return {"audible": True, "why": ", ".join(why) or "clear", "dist_m": ac.get("dist_meters"),
            "bearing": ac.get("compass"), "reach_eff": round(reach_eff, 1)}


# ── the same-room test (which pool: here, or carried from elsewhere) ────────────────────────────────────────
def _here(cat_loc: str, place: str, door_open: bool) -> bool:
    """Is a sound she makes at `cat_loc`, heard from Living-World place `place`, close enough to read as
    HERE WITH HIM (the here-pool line) rather than CARRIED from elsewhere? Deliberately NOT the same
    question as cat.visible_from() (a visibility/affordance test where study-side doorstep counts as
    visible through a shut door, since 'let her in' is itself the action) -- this is an ACOUSTIC
    same-room question, so study-side doorstep only reads as here-with-him while the door stands open
    (otherwise it is a sound heard THROUGH a shut door: carried). Garden-side doorstep and the garden
    wall both read as here unconditionally: she is right there, outside, no door involved either way.

    Fixes F-1031 (J-0632, the same hand-rolled-exact-match class this replaces): the previous inline
    test (`cat_loc in _INDOORS and place == "study") or (cat_loc == place) or (cat_loc == "doorstep"
    and place in ("study", "garden") and door_open)`) missed `garden_wall` entirely (not `_INDOORS`,
    not equal to the place string "garden" -- so every sound from the wall read as carried even when
    he was standing right there in the garden with her) and wrongly required `door_open` for the
    garden-side doorstep case too (irrelevant there: both are already outside)."""
    if cat_loc in _INDOORS and place == "study":
        return True
    if cat_loc == place:
        return True
    if cat_loc == "garden_wall" and place == "garden":
        return True
    if cat_loc == "doorstep":
        return place == "garden" or (place == "study" and door_open)
    return False


# J-2934 (F-3623, P-0031): the corpus's indoor phrasings ('From the next room', 'following you room to room') are
# true only while he is indoors. Du outdoors (garden / shore / wood) hears the same sounds with the phrase swapped for
# one that is true wherever he stands -- the cat is in the house (her `_PLACE_WORD` word, else 'somewhere in the
# house') or follows him about. No instruction, no new content: a wording swap only, applied after the pool pick, so
# the pools, the anti-repeat ring and every indoor line are untouched. Empty `his_place` (every older caller) = no swap.
_OUTDOOR_PLACES = frozenset({"garden", "shore", "wood"})


# J-3540 (F-4149 residual 1): 'the next room' is equally false when the CAT is outdoors and he is in the study. Her own
# outdoor spots (the `_PLACE_WORD` keys that are not house spots) trigger the same swap whatever his place; the swapped
# word is her spot's own phrase ('from the garden', 'beyond the door'), so nothing is added or prescribed.
_CAT_OUTDOOR_SPOTS = frozenset({"doorstep", "garden", "garden_wall", "wood", "shore", "away_hunting", "lean_to",
                                "wood_shed", "hedge_bottom", "water_butt_lid", "roof", "neighbours_wall"})


def _outdoors_wording(line: str, cat_loc: str, his_place: str) -> str:
    if not line or (his_place not in _OUTDOOR_PLACES and cat_loc not in _CAT_OUTDOOR_SPOTS):
        return line
    where = "from somewhere in the house" if cat_loc in _INDOORS else _PLACE_WORD.get(cat_loc, "from somewhere in the house")
    line = line.replace("From the next room", where[:1].upper() + where[1:])
    line = line.replace("from the next room", where)
    line = line.replace("following you room to room", "following you about")
    return line


# ── the line he would hear ────────────────────────────────────────────────────────────────────────────────
def line_for(key: str, here: bool, cat_loc: str, her: str, variant: str = "", his_place: str = "") -> str:
    """One line from cat_content.SOUNDS[key]'s here/carried pool, {her}/{dir} filled in. J-1175 (F-1621
    items A and C):
    (A) capitalised: the raw templates are free to open on {her}/{dir} (both substitute lowercase — "the
    cat"/"beyond the door") because capitalisation is this render step's job, not the corpus's; 54.8% of
    real audible ledger lines opened lowercase before this fix. Applied to the FINAL substituted string, not
    the template, so it is correct regardless of which token (if any) a line starts with.
    (C) never the same line twice running per (key, pool) — the soundscape._pick anti-wallpaper pattern
    (core/soundscape.py:1015), picked over cat.py's _pick_fresh 3-deep ring because these pools are 1-3
    lines long (a 3-deep ring fails open almost every time at that size) and the briefing's own ask is
    literally "never-the-same-twice-running", _pick's exact contract. Post-fix back-to-back identical
    audible lines were 46% (cat_demand) / 26% (cat_meow_at_door) / 47% (cat_trill) of consecutive pairs.
    Process-local state (_mem["last_line_idx"]), like the rest of this module: a restart forgets the last
    pick, never invents one. Growing the pools themselves is explicitly NOT this job's scope (J-1175
    briefing: draft only, ship pending Travis's wording approval) — this only changes HOW one is picked."""
    try:
        from core import cat_content as cc
        pools = (getattr(cc, "SOUNDS", {}) or {}).get(key) or {}
        pool_name = "here" if here else "carried"
        if variant:   # C3 (J-2468): a variant pool ("answer_here" / "answer_carried") when the corpus has one
            pool_name = f"{variant}_{pool_name}" if pools.get(f"{variant}_{pool_name}") else pool_name
        pool = pools.get(pool_name) or pools.get("here") or []
        if not pool:
            return ""
        ring_key = f"{key}:{pool_name}"
        idx_ring = _mem.setdefault("last_line_idx", {})
        idx = random.randrange(len(pool))
        if len(pool) > 1 and idx == idx_ring.get(ring_key, -1):   # never the same line twice running
            idx = (idx + 1) % len(pool)
        idx_ring[ring_key] = idx
        line = pool[idx].replace("{her}", her).replace("{dir}", _PLACE_WORD.get(cat_loc, "from somewhere in the house"))
        line = _outdoors_wording(line, cat_loc, his_place)      # J-2934 (F-3623): no 'next room' / 'room to room' outdoors
        return line[:1].upper() + line[1:] if line else line
    except Exception:
        return ""


# ── what she is sounding now, from her state ──────────────────────────────────────────────────────────────
def emissions(state: dict, now: float, dt: float) -> list[str]:
    """Keys she sounds in this window. Transitions are read against _mem (process-local: a restart forgets
    one thump, never invents one). A holds-key with no cooldown_s rolls a Poisson-lite count like world_tick
    for as long as it holds; a holds-key WITH cooldown_s (J-0996) fires at most once per real episode onset,
    gated by that cooldown -- see the KEYS table's own dosing note."""
    out: list[str] = []
    act = str(state.get("activity") or "")
    loc = str(state.get("location") or "")
    prev_act, prev_loc = _mem.get("act"), _mem.get("loc")
    # one-shots on transitions
    greet = float(state.get("last_greeted_ts") or 0.0)
    if greet > _mem.get("greet_ts", 0.0) and now - greet <= _MAX_DT_S:
        out.append("cat_trill")
    # HIS CALL (C3, J-2468, cat_overhaul): she answered a call of his — the answer comes back as SOUND FIRST, the
    # trill from HER position carried to him (then her legs, then the greeting). One-shot on call.answered_ts,
    # the greeting's own law; `trill_answer` tells tick() which pool (the answer's) and whether the answer was
    # given in the room and already rendered in his own line (then it enters active_sounds and the ledger but
    # never the percept rail a second time).
    ans = float((state.get("call") or {}).get("answered_ts") or 0.0)
    if ans > _mem.get("answer_ts", 0.0) and now - ans <= _MAX_DT_S:
        if "cat_trill" not in out:
            out.append("cat_trill")
        _mem["trill_answer"] = {"ts": ans, "here": bool((state.get("call") or {}).get("answer_here"))}
    _mem["answer_ts"] = max(ans, _mem.get("answer_ts", 0.0))
    if act in ("brought_a_mouse", "gift_rat") and prev_act not in ("brought_a_mouse", "gift_rat"):
        out.append("cat_yowl_cargo")
    if prev_loc in _RAISED and loc in _FLOOR_IN and prev_loc != loc:
        out.append("cat_thump")
    # rate events while the state holds -- per-episode dosing for any key carrying cooldown_s (KEYS note above)
    holds = {
        "cat_meow_at_door": act.startswith("at the door"),
        "cat_demand": act == "demanding_food",
        "cat_chatter": loc == "windowsill" and act in ("watching", "watching the birds", "chattering") and _birds_about(),
        # B3 (J-2470): hers at the tom (cat_tom.HISS_ACTS / GROWL_ACTS are her tom-reaction activities), and his
        # yowl while his bout holds (cat_tom.yowling_now) — each meaningful only while that state actually holds.
        "cat_hiss": act in _tom_acts("HISS_ACTS"),
        "cat_growl": act in _tom_acts("GROWL_ACTS"),
        "distant_yowl": _tom_yowling(now),
    }
    holds_prev = _mem.setdefault("holds_prev", {})
    last_fired = _mem.setdefault("last_fired", {})
    for key, on in holds.items():
        was_on, holds_prev[key] = holds_prev.get(key, False), on
        cooldown = KEYS[key].get("cooldown_s")
        if cooldown is not None:
            # J-0996: fire only on a real onset (was off, now on) and only once `cooldown` has passed
            # since this key last actually sounded -- a continuing hold (on both before and now) never
            # re-fires on its own, so one long episode is one line, not a drone.
            if on and not was_on and (now - last_fired.get(key, 0.0)) >= cooldown:
                out.append(key)
                last_fired[key] = now
            continue
        if not on:
            continue
        expected = float(KEYS[key]["rate"]) * dt / 3600.0
        n = int(expected) + (1 if random.random() < (expected - int(expected)) else 0)
        if n:
            out.append(key)
    # beds while the state holds
    # D-0163/D-4 (2026-09-07, J-0719, flagged by F-1037 while J-0700 built the hunting fallback):
    # last_fed alone can't tell a real saucer-feed from a self-catch out hunting — _maybe_self_feed()
    # sets last_fed too. Lapping implies a dish; a self-catch has no dish. last_self_fed is set (to the
    # SAME timestamp as last_fed) only on a self-catch, so excluding a recent last_self_fed is enough to
    # tell the two apart without needing last_fed_source at all (cat.py's own last_fed_source is the
    # more precise field where one is wanted; this gate only needs the negative case).
    if (now - float(state.get("last_fed") or 0.0) < 120.0
            and now - float(state.get("last_self_fed") or 0.0) >= 120.0):
        out.append("cat_lapping")
    if act == "storm_hide":
        out.append("cat_storm_rustle")
    _mem["act"], _mem["loc"], _mem["greet_ts"] = act, loc, max(greet, _mem.get("greet_ts", 0.0))
    return out


def tick(state: dict, now: float | None = None) -> list[dict]:
    """Called from cat.tick on every heartbeat; samples once per _SAMPLE_S. Returns the rows it logged."""
    now = time.time() if now is None else now
    last = float(_mem.get("last") or 0.0)
    if now - last < _SAMPLE_S:
        return []
    dt = min(now - last, _MAX_DT_S) if last else _SAMPLE_S
    _mem["last"] = now
    rows: list[dict] = []
    try:
        if not state or state.get("phase") in (None, "absent", "dead"):   # D-2 (J-2471): a dead cat makes no sound
            return []
        keys = emissions(state, now, dt)
        if not keys:
            return []
        place, sp, his_pos = _his_position()
        door_open, window_open = _house_open()
        weather, wind = _weather()
        cat_loc = str(state.get("location") or "")
        her = state.get("name") or "the cat"
        rendering = render_on()
        _origin = _transit_origin(state)   # B1: a leg in progress sounds from the leg's midpoint
        for key in keys:
            _snd_loc, _snd_origin = cat_loc, _origin
            if key in _TOM_KEYS:   # B3 (J-2470): HIS voice comes from where HE is (the wall, the step), not from her
                _tom_pos, _tom_loc = _tom_origin()
                if _tom_pos is None:
                    continue       # a tom with no position is a voice that did not happen (fail-open)
                _snd_loc, _snd_origin = _tom_loc, _tom_pos
            c = carry(key, _snd_loc, place, his_pos, door_open, window_open, weather, wind, origin=_snd_origin)
            here = _here(_snd_loc, place, door_open)
            _ans = _mem.get("trill_answer") if key == "cat_trill" else None   # C3: this trill answers his call
            _variant = "answer" if _ans else ""
            row = {"ts": round(now, 1), "kind": "sounded" if rendering else "would_sound", "key": key,
                   "cls": KEYS[key]["cls"], "cat": {"loc": cat_loc, "act": state.get("activity"), "mood": state.get("mood")},
                   "his": {"place": place, "standpoint": sp}, "audible": bool(c.get("audible")),
                   "dist_m": c.get("dist_m"), "bearing": c.get("bearing"), "reach_eff": c.get("reach_eff"),
                   "why": c.get("why"), "line": line_for(key, here, _snd_loc, her, _variant, place) if c.get("audible") else ""}
            if key in _TOM_KEYS:
                row["tom"] = {"loc": _snd_loc}
            if _ans:
                row["answer"] = True
                _mem["trill_answer"] = None
            rows.append(row)
            _log(row)
            if rendering and c.get("audible"):
                _mem["audible"][key] = now
                # J-1175: the percept rail (soundscape.percept()) reuses THIS line rather than re-picking
                # blind from a pool with no notion of where she actually is right now (F-1621 recommendation
                # b) — preserves the here/carried distinction the corpus depends on.
                # C3 (J-2468): an answer given in the room was already his own call line — no second percept
                # (an empty line never fires, the rail's own fail-open law); the key still sounds for the
                # census / active_sounds like any other.
                _mem.setdefault("audible_line", {})[key] = "" if (_ans and _ans.get("here")) else row["line"]
    except Exception as exc:
        logger.debug("[cat_sounds] tick failed (non-fatal): %s", exc)
    return rows


def audible_now(his_place: str = "", now: float | None = None) -> list[str]:
    """Keys of hers audible from where he is within the last window — soundscape's `_sec_cat` row reads this
    ONLY when rendering. Empty in shadow, always."""
    if not render_on():
        return []
    now = time.time() if now is None else now
    return [k for k, ts in list(_mem["audible"].items()) if now - float(ts) <= _AUDIBLE_WINDOW_S]


def line_now(key: str) -> str:
    """J-1175: the line she actually just sounded for `key` — here/carried already resolved by tick()
    against her REAL position at the moment it fired, capitalised — for soundscape.percept() to reuse
    rather than re-picking blind from a pool with no notion of where she is (F-1621 recommendation b).
    Same gate and window as audible_now() (render must be on and the emission must still be within
    _AUDIBLE_WINDOW_S) so the two never disagree about whether `key` is currently sounding. '' — never a
    stale or placeholder line — when `key` is not currently audible: fail-open, matching this whole
    module's law (a line that cannot be resolved is a percept that does not fire, not a placeholder)."""
    if not render_on():
        return ""
    now = time.time()
    ts = _mem.get("audible", {}).get(key)
    if not ts or now - float(ts) > _AUDIBLE_WINDOW_S:
        return ""
    return _mem.get("audible_line", {}).get(key, "")


def status() -> dict:
    n = 0
    try:
        with open(_LEDGER, encoding="utf-8") as f:
            n = sum(1 for _ in f)
    except Exception:
        pass
    return {"render": render_on(), "ledger_rows": n, "keys": list(KEYS), "last_sample": _mem.get("last")}
