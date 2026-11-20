"""
core/cat_ears.py — HER EARS: she listens on the world's acoustic clock and reacts to what really sounded
======================================================================================================
2026-10-28 (docs/staged/cat_overhaul.md Part C2, D-0499 "open D-1..D-4 and build", J-2467; built on J-2465's
body — bouts and legs). Until now she was a random walk: the 180 s movement tick rolled her next spot with
no notion of what was going on around her. A blackbird on the bed, the gate latch, Travis coming in, the
axe on the block — none of it reached her. Now it does, through one law:

    A REACTION CONSUMES A REAL SOUND EVENT AT HER PLACE. A bird that did not sound cannot be chattered at.

THE CLOCK. soundscape.world_tick samples HIS place only (the tree-falls law: nothing anywhere records what
sounded where he was not) and rolls each active voice a Poisson-lite occurrence count at its _EVENT_RATES
rate. Her ears ride the same clock two ways:
  - when her place IS his place, she consumes exactly the occurrences world_tick banked there since her
    last sample (soundscape.consume_ear_bank — the same blackbird he heard is the one she chatters at);
  - when she is elsewhere, nothing has rolled there (the tree-falls law again), so her ears roll the same
    rates over life.sounds_active(her place) — who is really present, awake and in their singing hours —
    for the window since her last sample. Same distribution, same rates; her place instead of his.
Either way a cue with a count of zero is a bird that did not sound, and she does nothing.

WHAT SHE HEARS, AND WHAT IT DOES (each a reaction with its own hold; the 180 s roll waits while it holds):
  BIRDS at her place (keys of rows the cat preys on: the blackbird's song and alarm, the sparrows, the
      wren's scold — derived from life's own rows, eaten_by "cat"): indoors by the window -> the sill,
      watching the birds, sometimes chattering (cat_sounds' cat_chatter then fires from HER state);
      out in the garden -> a real stalk (life.threat_active reads it: the blackbird alarms; garden_life's
      fledgling roll reads it: her kills read what was actually there); in the wood -> she hunts there.
  THE DAWN CHORUS -> up and out at first light: through the door if it stands open, else asking out.
  THE MOUSE IN THE WALL (HOOK, keyed on the sound key name "wall_scratch", sound_world_expansion §2,
      being built by the sound-world chain alongside this job): the moment that key exists and sounds at
      the study, she sits at the skirting for about an hour. He learns the wall has a mouse by watching
      her — nothing names it (the world answers through the cat). Until the key exists this branch is
      inert: sounds_active never yields it.
  HIS OWN SELF-SOUNDS: the gate latch (locomotion's gate_ts, J-0377) — she comes to the sound of the
      gate, not to a timer (presence_line's greeting now fires off ears["gate_ts"] as well as its old
      20-minute clock); his footsteps on the leg toward her place — she sits up, ears forward; the axe on
      the block (wood_life's last_split_ts, stamped by Du's split and Travis's) sends her out of the
      garden. The kettle, the clock, the door, the pen: nothing to her (_MEANS_NOTHING — never consumed).
  TRAVIS (companion_state.json: present flips on, or an errand comes home): a quirk rolled once and hers
      forever, stranger_response = hides / inspects / indifferent (cat._QUIRK_CHOICES).
  WEATHER: thunder -> storm_hide (cat.tick's own branch; logged here on its onset); hard wind -> in out
      of it (through the door if open, else asking in).

INSTRUMENT. Every reaction — and every cue she heard and did NOT act on (asleep, out of range, cooldown),
kind="ignored" — goes to data/cat_reactions.jsonl: fenced (profile.guard_path), rotated at _ROTATE_BYTES
to a single .1 generation. Read by the HUD and by the read job only. D-0434 / world answers, never leads:
nothing here writes a line to his prompt; her reactions reach him only as her ordinary presence lines
(cat_content.PRESENCE pools, rotating) and her own sounds. No gauge, count, band or cause is rendered.

LIVE by default (D-0499: world content, no shadow period; D-0500's own reading of the same question),
with a hot kill switch: data/life_flags.json {"cat_ears_live": false} (scripts/life_flags.py cat_ears off).
Restart-gated: Du is down since 2026-10-20; the next boot carries it.

Zero LLM. Read-only toward every store but cat_state.json (through cat.state, saved by cat.tick) and its
own ledger. Fail-open everywhere: a cue that cannot be read is a cue that did not sound.
"""
from __future__ import annotations

import json
import logging
import random
import time
from pathlib import Path

from core import profile

logger = logging.getLogger("nascence.cat_ears")

_DATA = Path(__file__).parent.parent / "data"
_LEDGER = _DATA / "cat_reactions.jsonl"
_FLAGS_F = _DATA / "life_flags.json"

LIVE = True                 # code default; hot override: life_flags.json cat_ears_live (false = ears off, ledger only)
_SAMPLE_S = 60.0            # her ears are sampled once a minute (cat_sounds' own cadence)
_MAX_DT_S = 300.0           # downtime guard (world_tick's own): no burst after a stopped stretch
_ROTATE_BYTES = 2_000_000   # the ledger rolls to cat_reactions.jsonl.1 past this (one generation kept)
_STAMP_FRESH_S = 300.0      # an act-site timestamp older than this when first seen is not a sound she heard now

# the self-sounds she does not care about — listed so the reader knows they were considered, never consumed
_MEANS_NOTHING = frozenset({"kettle_sing", "kettle_fill", "kettle_pour", "door_sound", "clock_tick", "page_turn",
                            "pen_scratch", "chair_desk_scrape", "log_on_fire", "bed_watering", "herb_cut", "sow_dig"})
WALL_MOUSE_KEYS = ("wall_scratch",)   # the HOOK: sound_world_expansion §2's key name; inert until that key sounds

# holds (seconds, min..max) a reaction keeps her where it put her before the bout machine resumes
HOLD_S = {
    "birds_sill": (10 * 60, 40 * 60), "birds_stalk": (10 * 60, 40 * 60), "wren_hunt": (30 * 60, 90 * 60),
    "dawn_out": (20 * 60, 60 * 60), "skirting": (50 * 60, 70 * 60), "gate": (5 * 60, 20 * 60),
    "footsteps": (3 * 60, 10 * 60), "axe": (20 * 60, 45 * 60), "travis_hides": (15 * 60, 40 * 60),
    "travis_inspects": (5 * 60, 15 * 60), "wind_in": (30 * 60, 90 * 60),
    "call": (5 * 60, 20 * 60),   # C3 (J-2468, core/cat_call): she is coming to his call — the roll waits for her
    # B3 (J-2470, core/cat_tom): her reactions to the tom ride this same hold machinery — the stand-off on the
    # wall, the fight (short: its aftermath is settled by cat_tom on the next sample), hiding when she loses,
    # the growl through the glass, and — at high tolerance, months on — watching from a distance.
    "tom_standoff": (8 * 60, 25 * 60), "tom_fight": (2 * 60, 5 * 60), "tom_hides": (20 * 60, 60 * 60),
    "tom_growl": (5 * 60, 20 * 60), "tom_watch": (5 * 60, 20 * 60), "tom_after": (5 * 60, 15 * 60),
}
# per-cue cooldowns: one reaction per episode, not one per minute the cue keeps sounding
COOLDOWN_S = {"birds": 1800.0, "wren": 3600.0, "dawn": 6 * 3600.0, "skirting": 3 * 3600.0, "gate": 600.0,
              "footsteps": 600.0, "axe": 1800.0, "travis": 900.0, "wind": 3600.0}
CHATTER_P = 0.3            # at the sill, the share of bird reactions that are a chatter rather than a watch
ASLEEP_GARDEN_GATE_P = 0.5 # a cat asleep outdoors hears the latch half the time

_INDOORS = {"by_the_fire", "windowsill", "on_the_desk", "on_your_lap", "under_desk", "mantel", "indoors",
            "under_the_bed", "cupboard_top"}      # C4 (J-2469): her hidden spots in the house are in the house
_GARDEN = {"garden", "garden_wall", "doorstep"}
_BY_THE_WINDOW = {"windowsill", "on_the_desk"}
_RESTING = ("sleeping", "dozing")

_mem: dict = {"last": 0.0, "bird_keys": None, "bird_rows": None, "journey_seen": 0.0}
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


def live_on() -> bool:
    v = _flags().get("cat_ears_live")
    return bool(LIVE if v is None else v)


def _log(row: dict) -> None:
    path = profile.guard_path(_LEDGER)   # J-0733: real data/ only if this process is live; raises before any I/O if not (D-0179)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            if path.exists() and path.stat().st_size > _ROTATE_BYTES:
                gen = path.with_name(path.name + ".1")
                if gen.exists():
                    gen.unlink()
                path.rename(gen)
        except Exception:
            pass
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.debug("[cat_ears] ledger write failed (non-fatal): %s", exc)


# ── the world around her (each read fail-open, each replaceable in a test) ──────────────────────────────
def _room() -> dict:
    try:
        from core import sensorium as _s
        if not _s.state:
            _s._load()
        return _s.state or {}
    except Exception:
        return {}


def _his_place() -> str:
    return str(_room().get("location") or "study")


def _phase() -> str:
    try:
        from core import sensorium as _s
        return str(_s._daylight())
    except Exception:
        return "day"


def _weather() -> tuple[str, str]:
    r = _room()
    return str(r.get("weather") or ""), str(r.get("wind") or "")


def _house_open() -> tuple[bool, bool]:
    try:
        from core import study_life as _sl
        st = _sl._st()
        return bool(st.get("door_open")), bool(st.get("window_open"))
    except Exception:
        return False, False


def _door_open() -> bool:
    try:
        from core import study_life as _sl
        return bool(_sl.door_open())
    except Exception:
        return False


def her_place(state: dict) -> str | None:
    """The Living-World place her ears are at: cat.place_of for a fixed spot, the leg's far end mid-leg,
    the garden for away_hunting (she is beyond the wall, in the garden's reach), None when she is gone."""
    loc = str((state or {}).get("location") or "")
    if loc == "in_transit":
        t = (state or {}).get("transit") or {}
        return str(t.get("to") or "") or None
    if loc == "away_hunting":
        return "garden"
    try:
        from core import cat as _cat
        return _cat.place_of(loc)
    except Exception:
        return None


def _hearing(state: dict) -> str:
    """'awake' | 'asleep' | 'deaf'. Deaf: gone, missing, pressed to the floor by thunder (nothing but the
    storm reaches her then). Asleep hears only the wake-class cues (the chorus, the latch, the axe)."""
    loc, act = str(state.get("location") or ""), str(state.get("activity") or "")
    if loc == "gone" or act in ("missing", "slipped_away", "storm_hide") or state.get("phase") in (None, "absent", "dead"):
        return "deaf"   # D-2 (J-2471): dead -> deaf, with gone / missing
    # D-2 (J-2471): an ill cat lying low hears like a sleeper — the wake-class cues only; nothing small moves her
    return "asleep" if (act in _RESTING or act == "lying low") else "awake"


# ── the cast she listens for (derived from life's own rows, never a hand list that can drift) ───────────
def bird_keys() -> set[str]:
    """Sound keys of the rows the cat preys on (eaten_by "cat"): the blackbird's song and alarm, the
    sparrows' small_birds, ... plus the wren's scold (the one voice the plan names for the wood)."""
    if _mem.get("bird_keys") is not None:
        return _mem["bird_keys"]
    keys: set[str] = set()
    try:
        from core import life as _life
        _life._ensure_builtin()
        for k, r in _life._ROWS.items():
            if r.get("kind") == "external":
                continue
            if "cat" in (r.get("eaten_by") or ()):
                keys.update(r.get("sound") or ())
                if r.get("alarm_sound"):
                    keys.add(r["alarm_sound"])
            if k == "wren":
                keys.update(r.get("sound") or ())
    except Exception:
        keys = set()
    _mem["bird_keys"] = keys
    return keys


def prey_about(place: str, now: float | None = None) -> list[str] | None:
    """What she could really catch at `place` now, as hunt species ("mouse" / "bird"): rows with "cat" in
    eaten_by whose life activity reads present. [] = nothing about (an honest miss); None = the rows could
    not be read (the caller keeps its old blind roll). D-0130: her kills read what was actually there."""
    now = time.time() if now is None else now
    try:
        from core import life as _life
        _life._ensure_builtin()
        if _mem.get("bird_rows") is None:
            try:
                from core import life_birds as _lb
                _mem["bird_rows"] = {r["key"] for r in _lb.rows()}
            except Exception:
                _mem["bird_rows"] = set()
        out: list[str] = []
        for k, r in _life._ROWS.items():
            if "cat" not in (r.get("eaten_by") or ()):
                continue
            if _life.activity(r, place, now) < _life.PRESENT_AT:
                continue
            if k == "mice":
                out.append("mouse")
            elif k in _mem["bird_rows"]:
                out.append("bird")
        return out
    except Exception:
        return None


# ── the acoustic clock at her place ────────────────────────────────────────────────────────────────────
def _poisson_lite(rate_per_h: float, dt: float) -> int:
    expected = max(0.0, rate_per_h) * dt / 3600.0
    return int(expected) + (1 if random.random() < (expected - int(expected)) else 0)


def heard_counts(place: str, dt: float, now: float, his_place: str | None = None) -> tuple[dict, str]:
    """Occurrence counts per sound key at `place` over the last `dt` seconds: world_tick's own bank when
    her place is his (consumed, so each occurrence is heard once), else the same rates rolled over
    life.sounds_active(place). Returns (counts, source) — source is "bank" or "roll"."""
    his_place = his_place or _his_place()
    if place == his_place:
        try:
            from core import soundscape as _snd
            bank = _snd.consume_ear_bank(place)
        except Exception:
            bank = None
        if bank is not None:
            return {k: int(n) for k, n in bank.items() if int(n) > 0}, "bank"
    try:
        from core import life as _life
        keys = list(_life.sounds_active(place, now))
    except Exception:
        keys = []
    counts: dict = {}
    try:
        from core import soundscape as _snd
        beds, rates, default = _snd._BEDS, _snd._EVENT_RATES, _snd._DEFAULT_EVENT_RATE
        pop = _snd._population_scale
    except Exception:
        beds, rates, default, pop = set(), {}, 6.0, (lambda k: 1.0)
    for k in keys:
        if k in beds or rates.get(k) == 0.0 or k == "dawn_chorus":
            counts[k] = 1                       # a bed is present for the window, not counted
            continue
        n = _poisson_lite(float(rates.get(k, default)) * float(pop(k) or 1.0), dt)
        if n:
            counts[k] = n
    return counts, "roll"


# ── reactions ───────────────────────────────────────────────────────────────────────────────────────────
def _ears(state: dict) -> dict:
    e = state.get("ears")
    if not isinstance(e, dict):
        e = {}
        state["ears"] = e
    e.setdefault("last", {})            # cue family -> ts of the last reaction (cooldowns)
    e.setdefault("gate_ts_seen", 0.0)   # the last gate latch she consumed
    e.setdefault("split_ts_seen", 0.0)  # the last axe knock she consumed
    e.setdefault("gate_ts", 0.0)        # when she last came to the gate (the greeting's trigger)
    e.setdefault("travis", None)        # {"present": bool, "errand": bool} as last seen
    return e


def _cooled(e: dict, family: str, now: float) -> bool:
    return now - float(e["last"].get(family, 0.0)) >= COOLDOWN_S.get(family, 0.0)


def reaction_holds(state: dict, now: float) -> bool:
    """True while a reaction keeps her where it put her (cat.tick's movement roll waits). Expired
    reactions are cleared here."""
    r = state.get("reaction")
    if not r:
        return False
    if now >= float(r.get("until") or 0.0) or str(state.get("location") or "") == "gone":
        state["reaction"] = None
        return False
    return True


def _begin(state: dict, now: float, kind: str, cue: str, loc: str, act: str, mood: str,
           bout: str | None = None, crosses: bool = True) -> dict:
    """Put her where the reaction takes her and hold it. A cross-PLACE move walks (cat._depart, her legs);
    a cross-WALL move with the door shut becomes the honest door-asking state instead (the cross-link's
    own rule). Returns what actually happened (for the ledger row)."""
    from core import cat as _cat
    cur = str(state.get("location") or "")
    before = {"loc": cur, "act": state.get("activity"), "mood": state.get("mood")}
    lo, hi = HOLD_S.get(kind, (5 * 60, 15 * 60))
    hold = random.uniform(lo, hi)
    if cur == "in_transit" and isinstance(state.get("transit"), dict):
        # mid-leg she is between places: the reaction re-aims the journey (she lands where it says) and
        # never teleports her off the leg she is on (B1's own law)
        state["transit"]["dest"] = {"location": loc, "activity": act, "mood": mood}
        state["reaction"] = {"kind": kind, "cue": cue, "since": now, "until": now + hold}
        return {"before": before, "to": {"loc": loc, "act": act, "mood": mood}, "walked": True, "hold_s": round(hold),
                "re_aimed": True}
    she_in, dest_in = cur in _INDOORS, loc in _INDOORS
    walked = False
    if crosses and she_in != dest_in and not _door_open():
        if she_in:
            loc, act = "indoors", "at the door, asking out"
        else:
            loc, act = "doorstep", "at the door, asking in"
    else:
        try:
            weather, wind = _weather()
            a, b = _cat._path_place(cur), _cat._path_place(loc)
            if cur != "in_transit" and a and b and a != b:
                walked = bool(_cat._depart(loc, act, mood, now, weather, wind, origin=cur))
        except Exception:
            walked = False
    if not walked:
        state["location"], state["activity"] = loc, act
        if mood:
            state["mood"] = mood
        state["position"] = list(_cat._ZONE_POSITIONS.get(loc, state.get("position") or [0.0, 0.0, 0.0]))
        state["_was_in"] = loc in _INDOORS
    try:
        bdy = state.setdefault("body", _cat._fresh_body(now))
        if bout:
            bdy["bout"], bdy["bout_since"], bdy["bout_until"] = bout, now, now + hold
    except Exception:
        pass
    state["reaction"] = {"kind": kind, "cue": cue, "since": now, "until": now + hold}
    return {"before": before, "to": {"loc": state.get("location"), "act": state.get("activity"), "mood": state.get("mood")},
            "walked": walked, "hold_s": round(hold)}


def _row(now: float, kind: str, cue: str, n: int, state: dict, place: str | None, source: str, **extra) -> dict:
    row = {"ts": round(now, 1), "kind": kind, "cue": cue, "n": int(n), "her_place": place, "source": source,
           "his_place": _his_place(), "hearing": _hearing(state),
           "her": {"loc": state.get("location"), "act": state.get("activity"), "mood": state.get("mood"),
                   "bout": (state.get("body") or {}).get("bout")}}
    row.update(extra)
    return row


# each _react_* returns a list of rows and may mutate state; the first that REACTS wins the sample
def _react_weather(state: dict, now: float, e: dict, place: str | None) -> list[dict]:
    weather, wind = _weather()
    rows: list[dict] = []
    try:
        from core import weather_conditions as _wc
        hard = _wc.is_hard_wind(wind)
    except Exception:
        hard = wind in ("strong wind", "gale")
    if not hard or "thunder" in weather:
        return rows
    loc = str(state.get("location") or "")
    if loc not in _GARDEN:
        return rows
    if not _cooled(e, "wind", now):
        return rows
    fire = str(_room().get("fire") or "out")
    dest = "by_the_fire" if fire in ("burning", "embers") else "indoors"
    done = _begin(state, now, "wind_in", "hard_wind", dest, "in out of the wind", "ruffled", bout="active")
    e["last"]["wind"] = now
    rows.append(_row(now, "reaction", "hard_wind", 1, state, place, "weather", **done))
    return rows


def _react_gate(state: dict, now: float, e: dict, place: str | None) -> list[dict]:
    rows: list[dict] = []
    try:
        from core import locomotion as _loco
        gate_ts = float(_loco._load().get("gate_ts") or 0.0)
    except Exception:
        return rows
    if gate_ts <= float(e.get("gate_ts_seen") or 0.0):
        return rows
    e["gate_ts_seen"] = gate_ts
    if now - gate_ts > _MAX_DT_S:
        return rows                                  # an old stamp (a restart, a stopped stretch): not heard now
    hearing = _hearing(state)
    loc = str(state.get("location") or "")
    if hearing == "deaf" or place not in ("garden", "study"):
        rows.append(_row(now, "ignored", "gate_latch", 1, state, place, "stamp", why="out of range" if hearing != "deaf" else hearing))
        return rows
    door_open, window_open = _house_open()
    if place == "study" and not (door_open or window_open or loc in _BY_THE_WINDOW) and hearing == "asleep":
        rows.append(_row(now, "ignored", "gate_latch", 1, state, place, "stamp", why="asleep in a shut house"))
        return rows
    if place == "garden" and hearing == "asleep" and random.random() > ASLEEP_GARDEN_GATE_P:
        rows.append(_row(now, "ignored", "gate_latch", 1, state, place, "stamp", why="asleep, did not stir"))
        return rows
    if not _cooled(e, "gate", now):
        rows.append(_row(now, "ignored", "gate_latch", 1, state, place, "stamp", why="cooldown"))
        return rows
    from core import cat as _cat
    bonded = state.get("phase") == "companion" or float(state.get("bond", 0.0)) >= _cat.NAME_BOND
    if not bonded:
        done = _begin(state, now, "gate", "gate_latch", "garden_wall", "watching", "wary", crosses=False) \
            if loc in _GARDEN else {"before": None, "to": None, "walked": False, "hold_s": 0}
        e["last"]["gate"] = now
        rows.append(_row(now, "reaction", "gate_latch", 1, state, place, "stamp", response="watches from the wall", **done))
        return rows
    done = _begin(state, now, "gate", "gate_latch", "garden_wall", "waiting at the gate for you", "expectant", bout="active")
    e["last"]["gate"], e["gate_ts"] = now, now
    rows.append(_row(now, "reaction", "gate_latch", 1, state, place, "stamp", response="comes to the gate", **done))
    return rows


def _react_footsteps(state: dict, now: float, e: dict, place: str | None) -> list[dict]:
    rows: list[dict] = []
    try:
        from core import locomotion as _loco
        d = _loco._load()
        j = d.get("journey") or {}
        path = list(j.get("path") or [])
        started = float(j.get("started") or 0.0)
    except Exception:
        return rows
    if not path or not started or started <= float(_mem.get("journey_seen") or 0.0):
        return rows
    if path[0] != place or _hearing(state) != "awake" or str(state.get("location") or "") == "in_transit":
        return rows
    _mem["journey_seen"] = started
    if not _cooled(e, "footsteps", now) or state.get("reaction"):
        rows.append(_row(now, "ignored", "footsteps", 1, state, place, "journey", why="cooldown or held"))
        return rows
    done = _begin(state, now, "footsteps", "footsteps", str(state.get("location")), "listening, ears forward",
                  str(state.get("mood") or "watchful"), crosses=False)
    e["last"]["footsteps"] = now
    rows.append(_row(now, "reaction", "footsteps", 1, state, place, "journey", **done))
    return rows


def _react_axe(state: dict, now: float, e: dict, place: str | None) -> list[dict]:
    rows: list[dict] = []
    try:
        from core import wood_life as _wl
        split_ts = float(_wl._load().get("last_split_ts") or 0.0)
    except Exception:
        return rows
    if split_ts <= float(e.get("split_ts_seen") or 0.0):
        return rows
    e["split_ts_seen"] = split_ts
    if now - split_ts > _MAX_DT_S:
        return rows
    loc = str(state.get("location") or "")
    if loc not in _GARDEN or _hearing(state) == "deaf":
        rows.append(_row(now, "ignored", "axe_on_block", 1, state, place, "stamp", why="not in the garden"))
        return rows
    if not _cooled(e, "axe", now):
        rows.append(_row(now, "ignored", "axe_on_block", 1, state, place, "stamp", why="cooldown"))
        return rows
    done = _begin(state, now, "axe", "axe_on_block", "away_hunting", "gone out of the garden from the knocking", "wary",
                  bout="active", crosses=False)
    e["last"]["axe"] = now
    rows.append(_row(now, "reaction", "axe_on_block", 1, state, place, "stamp", **done))
    return rows


def _read_travis() -> dict | None:
    try:
        from core import companion as _co
        d = json.loads(_co._STATE_F.read_text(encoding="utf-8")) if _co._STATE_F.exists() else {}
        return {"present": bool(d.get("present")), "errand": bool(d.get("errand"))}
    except Exception:
        return None


def _react_travis(state: dict, now: float, e: dict, place: str | None) -> list[dict]:
    rows: list[dict] = []
    cur = _read_travis()
    if cur is None:
        return rows
    prev = e.get("travis")
    e["travis"] = cur
    if not isinstance(prev, dict):
        return rows                                   # first sight of the store: nothing to compare against
    arrived = cur["present"] and not prev.get("present")
    returned = cur["present"] and prev.get("errand") and not cur["errand"]
    if not (arrived or returned):
        return rows
    cue = "travis_arrives" if arrived else "travis_returns"
    loc = str(state.get("location") or "")
    hearing = _hearing(state)
    if place not in ("study", "garden") or hearing == "deaf":
        rows.append(_row(now, "ignored", cue, 1, state, place, "companion", why="out of range"))
        return rows
    if not _cooled(e, "travis", now):
        rows.append(_row(now, "ignored", cue, 1, state, place, "companion", why="cooldown"))
        return rows
    from core import cat as _cat
    q = _cat._quirks().get("stranger_response", "inspects")
    e["last"]["travis"] = now
    if q == "indifferent":
        rows.append(_row(now, "reaction", cue, 1, state, place, "companion", response="indifferent", to=None))
        return rows
    if q == "hides":
        dest = "under_desk" if loc in _INDOORS else "garden_wall"
        done = _begin(state, now, "travis_hides", cue, dest, "hiding from the visitor", "wary", crosses=False)
        rows.append(_row(now, "reaction", cue, 1, state, place, "companion", response="hides", **done))
        return rows
    if loc in _INDOORS or (loc in _GARDEN and _door_open()):
        done = _begin(state, now, "travis_inspects", cue, "indoors", "inspecting the visitor", "curious")
        rows.append(_row(now, "reaction", cue, 1, state, place, "companion", response="inspects", **done))
    else:
        rows.append(_row(now, "ignored", cue, 1, state, place, "companion", why="door shut, stays out"))
    return rows


def _react_sounds(state: dict, now: float, dt: float, e: dict, place: str | None) -> list[dict]:
    """The living voices at her place: the birds, the chorus, the mouse in the wall."""
    rows: list[dict] = []
    if place not in ("study", "garden", "wood", "shore"):
        return rows
    hearing = _hearing(state)
    if hearing == "deaf":
        return rows
    loc = str(state.get("location") or "")
    his = _his_place()
    counts, source = heard_counts(place, dt, now, his)
    # indoors, the garden reaches her through the glass: the sill and the desk are at the window; an open
    # door or window lets the whole garden in; a shut house lets only the chorus and the alarm through
    if place == "study":
        door_open, window_open = _house_open()
        g_counts, g_source = heard_counts("garden", dt, now, his)
        if not (door_open or window_open or loc in _BY_THE_WINDOW):
            g_counts = {k: n for k, n in g_counts.items() if k in ("dawn_chorus", "blackbird_alarm")}
        for k, n in g_counts.items():
            counts[k] = counts.get(k, 0) + n
        source = f"{source}+garden:{g_source}"
    birds = bird_keys()
    phase = _phase()
    # 1. the mouse in the wall (hook: inert until the sound-world chain binds wall_scratch to the mice row)
    wall = [k for k in WALL_MOUSE_KEYS if counts.get(k)]
    if wall and place == "study":
        n = sum(counts[k] for k in wall)
        if hearing == "asleep":
            rows.append(_row(now, "ignored", wall[0], n, state, place, source, why="asleep"))
        elif not _cooled(e, "skirting", now):
            rows.append(_row(now, "ignored", wall[0], n, state, place, source, why="cooldown"))
        else:
            done = _begin(state, now, "skirting", wall[0], "indoors", "at the skirting, listening", "intent",
                          bout="active", crosses=False)
            e["last"]["skirting"] = now
            rows.append(_row(now, "reaction", wall[0], n, state, place, source, **done))
            return rows
    # 2. the dawn chorus: up and out at first light
    if counts.get("dawn_chorus") and phase == "dawn":
        n = counts["dawn_chorus"]
        energy = float((state.get("body") or {}).get("energy", 0.5))
        if not _cooled(e, "dawn", now):
            rows.append(_row(now, "ignored", "dawn_chorus", n, state, place, source, why="cooldown"))
        elif energy <= 0.2:
            rows.append(_row(now, "ignored", "dawn_chorus", n, state, place, source, why="spent, sleeps on"))
        elif loc in _INDOORS:
            done = _begin(state, now, "dawn_out", "dawn_chorus", "garden", "up and out at first light", "alert", bout="active")
            e["last"]["dawn"] = now
            rows.append(_row(now, "reaction", "dawn_chorus", n, state, place, source, **done))
            return rows
        elif hearing == "asleep":
            done = _begin(state, now, "dawn_out", "dawn_chorus", loc if loc in _GARDEN else "garden",
                          "up and out at first light", "alert", bout="active", crosses=False)
            e["last"]["dawn"] = now
            rows.append(_row(now, "reaction", "dawn_chorus", n, state, place, source, **done))
            return rows
    # 3. the birds she preys on: only the ones that actually sounded
    heard = {k: n for k, n in counts.items() if k in birds and n > 0}
    if not heard:
        return rows
    cue = max(heard, key=heard.get)
    n = sum(heard.values())
    if hearing == "asleep":
        rows.append(_row(now, "ignored", cue, n, state, place, source, why="asleep", heard=heard))
        return rows
    if place == "wood":
        if not _cooled(e, "wren", now):
            rows.append(_row(now, "ignored", cue, n, state, place, source, why="cooldown", heard=heard))
            return rows
        done = _begin(state, now, "wren_hunt", cue, "wood", "hunting", "aloof", bout="hunt", crosses=False)
        e["last"]["wren"] = now
        rows.append(_row(now, "reaction", cue, n, state, place, source, heard=heard, **done))
        return rows
    if not _cooled(e, "birds", now):
        rows.append(_row(now, "ignored", cue, n, state, place, source, why="cooldown", heard=heard))
        return rows
    if place == "study":
        act = "chattering" if random.random() < CHATTER_P else "watching the birds"
        done = _begin(state, now, "birds_sill", cue, "windowsill", act, "intent", bout="active", crosses=False)
    elif place == "garden":
        done = _begin(state, now, "birds_stalk", cue, "garden", "stalking something", "playful", bout="active", crosses=False)
    else:
        return rows
    e["last"]["birds"] = now
    rows.append(_row(now, "reaction", cue, n, state, place, source, heard=heard, **done))
    return rows


def note_weather(kind: str, state: dict, now: float | None = None) -> None:
    """cat.tick's own storm branch calls this on the storm_hide ONSET so the thunder reaction is in the
    same ledger as the rest (the branch itself is untouched base machinery)."""
    now = time.time() if now is None else now
    try:
        if not live_on():
            return
        _log(_row(now, "reaction", "thunder", 1, state, her_place(state), "weather", response=kind))
    except profile.NonLiveWriteError:
        raise
    except Exception:
        pass


def tick(state: dict, now: float | None = None) -> list[dict]:
    """Called from cat.tick on every heartbeat; samples once per _SAMPLE_S. Mutates `state` only through
    a reaction (cat.tick saves). Returns the rows it logged."""
    now = time.time() if now is None else now
    last = float(_mem.get("last") or 0.0)
    if now - last < _SAMPLE_S:
        return []
    dt = min(now - last, _MAX_DT_S) if last else _SAMPLE_S
    _mem["last"] = now
    rows: list[dict] = []
    try:
        if not state or state.get("phase") in (None, "absent") or not live_on():
            return []
        e = _ears(state)
        place = her_place(state)
        held = reaction_holds(state, now)
        # the stamps and the companion are read every sample so nothing is replayed later; a held reaction
        # only blocks the LIVING voices (a bird does not pull her off the gate she just came to)
        for fn in (_react_weather, _react_gate, _react_axe, _react_travis, _react_footsteps):
            if state.get("transit") and fn is not _react_travis and fn is not _react_gate:
                continue
            if held and fn in (_react_weather, _react_footsteps):
                continue
            rows += fn(state, now, e, place)
            if rows and rows[-1].get("kind") == "reaction" and rows[-1].get("to"):
                held = True
        if not held and not state.get("transit"):
            rows += _react_sounds(state, now, dt, e, place)
        for row in rows:
            _log(row)
    except profile.NonLiveWriteError:
        raise
    except Exception as exc:
        logger.debug("[cat_ears] tick failed (non-fatal): %s", exc)
    return rows


def status() -> dict:
    n = 0
    try:
        with open(_LEDGER, encoding="utf-8") as f:
            n = sum(1 for _ in f)
    except Exception:
        pass
    return {"live": live_on(), "ledger_rows": n, "last_sample": _mem.get("last"), "bird_keys": sorted(bird_keys())}
