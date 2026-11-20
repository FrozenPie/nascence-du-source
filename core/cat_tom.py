"""
core/cat_tom.py — THE TOM: the black cat becomes a second individual that comes into the garden
=================================================================================================
Cat Overhaul B3 (docs/staged/cat_overhaul.md §B3 + §C1's cat_hiss / cat_growl / distant_yowl rows), J-2470,
D-0507 (c) (Travis, 2026-10-28; D-0162 before it). Until this build the black cat was a far-off shape
(core/cat.py's distant_line: 345 sightings, absorbed as metaphor, never once a naming pressure — §A6). Now it
is a real second life row (`kind="individual"`, key "tom") with its own state in data/cat_tom_state.json: a
tom, older, scarred, that lives on the neighbour's ridge and COMES INTO THE GARDEN — at night on the wall, at
the doorstep in winter, at the saucer if there is food in it (and eats her food).

HE IS NOT HERS, AND NEVER HIS. The founder's rule for this cat holds exactly as it did when it was a shape:
indifferent life, not a relationship. He can be looked at, driven off, and — over months of uneventful
co-presence — tolerated by HER (the `tolerance` field is hers toward him, 0..1); nothing here ever moves him
toward Du, feeds a bond, or lets him be tamed. The D-0507 defeater names this directly.

SHE REACTS through the machinery she already has: cat_ears._begin (a reaction that puts her somewhere, holds
her there, and lets the 180 s roll wait — C2) with the storm-hide moods (afraid) and the stalk/possessed moods
(furious). A stand-off on the wall; a fight (logged here; HER INJURY PATH IS NOT BUILT HERE — it belongs to the
D-2 mortality job, J-2471; this file leaves the hook, cat_state.json "tom": {"fight_hook": ...}); a growl
through the glass; hiding under the desk when she loses; at high tolerance, watching from a distance.

HIS VOICE IN THE NIGHT is a soundscape key: `distant_yowl` (the yowling on the wall, a bout that favours the
small hours), and hers back at him: `cat_hiss` / `cat_growl` — all three emitted by core/cat_sounds from
state (his and hers), carried to Du by position through the same carry law as the rest of her voice, gated by
the same cat_sounds render flag, entering active_sounds through soundscape._sec_cat like every other spoke.
If sound_world_expansion §2 (J-2475) has registered `distant_yowl` too, the two registrations carry the
same object and coordinates (copied from that branch so a merge keeps one point whichever entry wins).

HIDDEN TRUTH (D-0129 / D-0133): feature-first — "a black cat, big, one eye milky" — until a close sighting in
the garden AND a book earn "a tom" (life.learn_from_text reads the row's book_names like every creature's);
his NAME, if Du ever gives him one, is Du's act alone (life_traces.give_name on the individual record this
file creates on the first close sighting). Nothing is told; all of it is findable.

THE REFERENT PRESSURE (D-0505 (c), §B2, core/cat_referent): the tom at the saucer is what makes "the cat"
ambiguous in Du's own ledger. This file records nothing about which cat he meant — cat_referent does, from
HIS text, only when he distinguishes them — and no line below ever asks him to.

NO READOUT (D-0434; world answers, never leads): no number, band, gauge, tolerance value or hint reaches any
line he sees. The ledger data/cat_tom_ledger.jsonl is an instrument (HUD only). Every line pool rotates.
Additive: no base system is touched; a cat_tom_state.json that does not exist yet is a tom that has not
come down off the ridge. Kill switch (hot): data/life_flags.json {"cat_tom_live": false}.
"""
from __future__ import annotations

import json
import logging
import random
import re
import time
from pathlib import Path

from core import profile

logger = logging.getLogger("nascence.cat_tom")

_DATA = Path(__file__).parent.parent / "data"
_STATE_F = _DATA / "cat_tom_state.json"
_LEDGER = _DATA / "cat_tom_ledger.jsonl"
_FLAGS_F = _DATA / "life_flags.json"

KEY = "tom"                      # the life row key (cat_referent._is_cat_row reads it; life_traces.give_name names it)
LIVE = True                      # code default; hot override: life_flags.json cat_tom_live (false = he stays on the ridge)
_SAMPLE_S = 60.0                 # his clock is sampled once a minute (cat_sounds / cat_ears cadence)
_MAX_DT_S = 300.0                # downtime guard: no burst of visits after a stopped stretch
_ROTATE_BYTES = 2_000_000        # the ledger rolls to .1 past this (one generation kept)

# ── who he is (rolled once, kept) ──────────────────────────────────────────────────────────────────────────
YEAR_S = 365.25 * 86400.0
ARRIVED_AGE_Y = (7.0, 11.0)      # older than her; scarred (§B3)
LIFESPAN_Y = 14.0                # on this module, not the life row: mortality for either cat is D-2's (J-2471), not here
_SCAR_CHOICES = {
    "ear": ("a torn left ear", "an ear chewed to a stub", "both ears nicked along the edge"),
    "face": ("a pale seam down the nose", "a bald patch over one brow", "a thick scarred jaw"),
    "tail": ("a tail with a kink near the end", "half a tail", "a tail he carries low"),
}

# ── his coming and going ───────────────────────────────────────────────────────────────────────────────────
VISIT_P_PER_H = {"night": 0.30, "dusk": 0.08, "dawn": 0.04, "day": 0.0}   # from the ridge, per hour, fair weather
WINTER_DAY_P_PER_H = 0.05        # in winter he comes to the doorstep by day too (the warm step by the door)
SAUCER_DRAW = 2.5                # food in the saucer draws him (×)
WET_FACTOR = 0.3                 # rain keeps him on the ridge mostly; a storm entirely
VISIT_S = {"wall": (20 * 60, 80 * 60), "doorstep": (15 * 60, 60 * 60), "saucer": (5 * 60, 20 * 60)}
AFTER_VISIT_GAP_S = (40 * 60, 3 * 3600)
DRIVEN_OFF_GAP_S = (2 * 3600, 6 * 3600)
LOST_FIGHT_GAP_S = (12 * 3600, 36 * 3600)
WON_FIGHT_GAP_S = (1 * 3600, 3 * 3600)
EAT_AFTER_S = (2 * 60, 5 * 60)   # at the saucer, the food is gone this long after he reaches it
YOWL_P_PER_SAMPLE = 0.02         # on the wall at night: a bout starts about once per 50 min of sitting
YOWL_SMALL_HOURS = (0, 4)        # ... twice as likely between midnight and four (the 3 a.m. yowl)
YOWL_BOUT_S = (5 * 60, 20 * 60)

# ── her reactions (through cat_ears._begin; the moods are the storm-hide / possessed ones she already has) ─
HER_STANDOFF = "facing the tom on the wall"
HER_SPIT = "spitting at the tom at the saucer"
HER_FIGHT = "fighting the tom"
HER_HIDE = "hiding from the tom"
HER_GROWL = "growling at the tom through the glass"
HER_WATCH = "watching the tom from a distance"
HER_AFTER = "after the fight"
HISS_ACTS = frozenset({HER_STANDOFF, HER_SPIT, HER_FIGHT})       # cat_sounds: cat_hiss while one of these holds
GROWL_ACTS = frozenset({HER_GROWL, HER_AFTER})                    # cat_sounds: cat_growl while one of these holds
TOM_ACTS = HISS_ACTS | GROWL_ACTS | {HER_HIDE, HER_WATCH}
FIGHT_P = 0.30                   # a stand-off becomes a fight this often (scaled down by her tolerance)
SHE_WINS_P = 0.45                # she is smaller; he is older
WAKE_P = 0.4                     # asleep indoors, she wakes to him this often (0.7 if he is yowling)
TOLERATE_AT = 0.6                # tolerance from which she mostly watches instead of standing off
TOLERANCE_PER_MIN = 0.0015       # per quiet co-present minute: months of nights, not days
TOLERANCE_FIGHT_HIT = 0.15
REACTION_GAP_S = 20 * 60         # one reaction of hers per twenty minutes of a visit

_RESTING = ("sleeping", "dozing")
_INDOORS = {"by_the_fire", "windowsill", "on_the_desk", "on_your_lap", "under_desk", "mantel", "indoors",
            "under_the_bed", "cupboard_top"}      # C4 (J-2469): her hidden spots in the house are in the house
_GARDEN = {"garden", "garden_wall", "doorstep"}
_BY_THE_WINDOW = {"windowsill", "on_the_desk"}
_IN_GARDEN = ("wall", "doorstep", "saucer")             # his locations inside the garden; "ridge" is home

# ── the hand: driving him off ─────────────────────────────────────────────────────────────────────────────
_DRIVE_VERBS = ("drive", "drove", "driving", "chase", "chased", "chasing", "shoo", "shooed", "see off", "see it off",
                "run off", "run it off", "throw", "threw", "clap", "clapped", "stamp", "stamped", "shout at", "shouted at",
                "hiss at", "scare", "scared", "frighten", "frightened", "send it packing", "sent it packing", "go out at",
                "charge at", "wave", "waved", "bang")
_OTHER_CAT_WORDS = ("black cat", "other cat", "distant cat", "far cat", "that cat on", "tom", "tomcat", "big cat",
                    "strange cat", "stranger cat", "intruder", "black one", "the neighbour's cat", "the neighbor's cat",
                    "one-eyed cat", "milky")
_OTHER_CAT_RE = re.compile(r"(?<![a-z-])(?:" + "|".join(re.escape(w) for w in _OTHER_CAT_WORDS) + r")(?![a-z-])")
_TOM_NAME_WHO = r"(?:the |that |this |my |our |old |big |black )*(?:black cat|black one|tom|tomcat|other cat|big cat|stranger|intruder|one-eyed cat)"
_TOM_NAME_PATS = (
    rf"\b(?:call|name|dub)\s+{_TOM_NAME_WHO}\s+([A-Za-z][\w'-]+)",
    rf"\b{_TOM_NAME_WHO}'?s?\s+name\s+(?:is|shall be|will be|can be|should be)\s+([A-Za-z][\w'-]+)",
    rf"\bI(?:'ll| will| shall| am going to)?\s*(?:call|name|dub)\s+{_TOM_NAME_WHO}\s+([A-Za-z][\w'-]+)",
)
_NAME_STOP = {"her", "him", "it", "the", "she", "he", "you", "me", "us", "that", "this", "a", "an", "my", "name", "names",
              "now", "then", "here", "there", "again", "over", "back", "out", "in", "up", "down", "home", "mine", "one",
              "cat", "tom", "off", "away"}

state: dict = {}
_state_mtime = 0.0
_mem: dict = {"last": 0.0, "last_render": 0.0, "render_visit": None}
_flags_cache: dict = {"ts": 0.0, "v": {}}


# ── flags / io ─────────────────────────────────────────────────────────────────────────────────────────────
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
    v = _flags().get("cat_tom_live")
    return bool(LIVE if v is None else v)


def _log(row: dict) -> None:
    path = profile.guard_path(_LEDGER)   # real data/ only if this process is live; raises before any I/O if not (D-0179)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            if path.exists() and path.stat().st_size > _ROTATE_BYTES:
                path.replace(path.with_suffix(path.suffix + ".1"))
        except Exception:
            pass
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _load() -> dict:
    """His state; a file that does not exist is a tom that has not come down off the ridge yet (born here)."""
    global state, _state_mtime
    try:
        cur_mtime = _STATE_F.stat().st_mtime
    except Exception:
        cur_mtime = 0.0
    if state and cur_mtime <= _state_mtime:
        return state
    try:
        state = json.loads(_STATE_F.read_text(encoding="utf-8"))
        _state_mtime = cur_mtime
    except Exception:
        if not state:
            state = {}
    now = time.time()
    if not state.get("born_ts"):
        state["born_ts"] = now - random.uniform(*ARRIVED_AGE_Y) * YEAR_S
    if not state.get("scars"):
        state["scars"] = {k: random.choice(v) for k, v in _SCAR_CHOICES.items()}
    state.setdefault("location", "ridge")          # ridge | wall | doorstep | saucer
    state.setdefault("activity", "away")           # away | sitting | yowling | eating | leaving | driven off
    state.setdefault("visit", None)                # {"since", "until", "where", "reason"} while in the garden
    state.setdefault("visits", 0)
    state.setdefault("last_visit_ts", 0.0)
    state.setdefault("next_visit_not_before", 0.0)
    state.setdefault("tolerance", 0.0)             # HERS toward him (0..1); never his toward anyone
    state.setdefault("standoffs", 0)
    state.setdefault("fights", 0)
    state.setdefault("last_fight_ts", 0.0)
    state.setdefault("driven_off", 0)
    state.setdefault("last_driven_ts", 0.0)
    state.setdefault("ate_from_saucer", 0)
    state.setdefault("seen_close", 0)              # close sightings in the garden (the individual record's own count)
    state.setdefault("first_close_ts", 0.0)
    state.setdefault("yowl_until", 0.0)
    state.setdefault("yowl_bouts", 0)
    state.setdefault("last_reaction_ts", 0.0)
    state.setdefault("_rings", {})
    return state


def _save() -> None:
    global _state_mtime
    path = profile.guard_path(_STATE_F)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, indent=1, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)
        try:
            _state_mtime = path.stat().st_mtime
        except Exception:
            pass
    except Exception as exc:
        logger.debug("[cat_tom] _save failed (non-fatal): %s", exc)


# ── the world around him (each read fail-open; each replaceable in a test) ────────────────────────────────
def _phase() -> str:
    try:
        from core import sensorium as _s
        return str(_s._daylight() or "day")
    except Exception:
        return "day"


def _season() -> str:
    try:
        from core import sensorium as _s
        return str(_s._season() or "")
    except Exception:
        return ""


def _weather() -> tuple[str, str]:
    try:
        from core import sensorium as _s
        if not _s.state:
            _s._load()
        return str(_s.state.get("weather") or ""), str(_s.state.get("wind") or "")
    except Exception:
        return "", ""


def _his_place() -> str:
    try:
        from core import sensorium as _s
        if not _s.state:
            _s._load()
        return str(_s.state.get("location") or "study")
    except Exception:
        return "study"


def _door_open() -> bool:
    try:
        from core import study_life as _sl
        return bool(_sl.door_open())
    except Exception:
        return False


def _hour(now: float) -> int:
    try:
        return int(time.localtime(now).tm_hour)
    except Exception:
        return 12


def _saucer_has_food(cat_state: dict) -> bool:
    sc = (cat_state or {}).get("saucer") or {}
    return bool(sc.get("has_food"))


# ── what he is called (feature-first: D-0129) ─────────────────────────────────────────────────────────────
def _individual() -> dict | None:
    try:
        from core import life_traces as _lt
        return _lt.individual(KEY)
    except Exception:
        return None


def learned() -> bool:
    """A close sighting AND a book have earned 'a tom' (life's own ledger; D-0129)."""
    try:
        from core import life as _life
        return bool(_life.is_learned(KEY))
    except Exception:
        return False


def what() -> str:
    """How a line may call him: his name if Du gave one, 'the tom' once learned, else 'the black cat'."""
    ind = _individual()
    if ind and ind.get("name"):
        return str(ind["name"])
    return "the tom" if learned() else "the black cat"


def features_line() -> str:
    """The feature-first description a close look earns: 'a black cat, big, one eye milky' plus the scars rolled once."""
    _load()
    sc = state.get("scars") or {}
    extras = [v for v in (sc.get("ear"), sc.get("face"), sc.get("tail")) if v]
    random.shuffle(extras)
    return "a black cat, big, one eye milky" + (f", {extras[0]}" if extras else "")


# ── the life row (life._ensure_builtin registers it; cat_referent / life_traces / the HUD read it) ────────
def life_row() -> dict:
    from core import life as _life
    return _life.row(
        KEY, kind="individual", name=None,
        aliases=("tom", "tomcat", "black cat", "other cat"),
        places={"garden": ["the wall", "the doorstep", "the saucer"]},
        active_hours={"dawn": 0.2, "day": 0.05, "dusk": 0.5, "night": 1.0},
        season_curve=[1.0] * 12,
        weather_gate={"rain": 0.3, "wind": 0.7, "storm": 0.0, "frost": 0.8},
        light="indifferent", eyeshine=True, count=("one", "one", "one"), ease=0.5,
        lifespan_y=None,            # deliberately: mortality for either cat is D-2's (J-2471); LIFESPAN_Y lives here
        diet=("cat_food", "mouse", "bird", "scraps", "milk", "shore_fish"),
        traces=("black hairs on the wall top", "a post by the gate, sprayed and rank"),
        traces_only_at={"a post by the gate, sprayed and rank": ("garden",)},
        responds_to_du={"saucer": 0.6},
        external={"presence": presence_for_life},
        hidden={"species": "tom",
                "book_names": ("tomcat", "tom cat", "a tom", "the tom", "toms", "entire male", "unneutered male"),
                "book_words": ("cat", "cats", "territory", "spray", "sprays", "fight", "fights", "fighting", "scars",
                               "yowl", "yowling", "mating", "queen"),
                "feature": {"night": "a black cat, big, a shape against the sky on the wall top — it looks back at you and does not move",
                            "dusk": "a big black cat on the wall at the ridge end, sitting the way a cat sits on its own ground",
                            "dawn": "a black cat going back along the wall toward the ridge, unhurried, one eye catching the light wrong",
                            "day": "a big black cat on the doorstep in the thin sun, scarred about the head, not asleep"},
                "eyeshine": "two points of light on the wall top, wide-set and low — and only one of them answers the lamp",
                "reveal": "— a tom, an entire male: the scars, the stink on the gatepost and the yowling at night are all his trade.",
                "miss": "A shape on the wall top that could be the dark itself; nothing you can be sure of.",
                "absent": {"night": "The wall top is empty and the ridge is only the ridge.",
                           "day": "Not by day, mostly; the wall is bare and the doorstep is hers.",
                           "weather": "Not in this — nothing comes down off the ridge in weather like it.",
                           "chance": "The wall and the ridge: nothing there just now."}},
        note="core/cat_tom.py — the OTHER cat (cat_overhaul B3, J-2470, D-0507 (c)): the tom from the neighbour's ridge; never tamed")


def presence_for_life(now: float) -> dict:
    """life.activity for the row: in the garden while a visit holds (the row's `external` adapter)."""
    try:
        _load()
        if not in_garden():
            return {}
        return {"garden": 1.0}
    except Exception:
        return {}


# ── state reads ─────────────────────────────────────────────────────────────────────────────────────────────
def in_garden() -> bool:
    _load()
    return str(state.get("location") or "ridge") in _IN_GARDEN


def present() -> bool:
    return in_garden()


def yowling_now(now: float | None = None) -> bool:
    """cat_sounds reads this: distant_yowl holds while his bout holds (on the wall, at night)."""
    now = time.time() if now is None else now
    _load()
    return in_garden() and state.get("activity") == "yowling" and now < float(state.get("yowl_until") or 0.0)


def sound_origin() -> list[float] | None:
    """Where his voice comes from, in cat_sounds' chain frame (metres): the wall / the doorstep / the saucer."""
    _load()
    try:
        from core import cat_sounds as _cs
        loc = str(state.get("location") or "")
        if loc == "wall":
            return list(_cs._POS["garden_wall"])
        if loc in ("doorstep", "saucer"):
            return list(_cs._POS["doorstep"])
    except Exception:
        pass
    return None


def sound_loc_word() -> str:
    """The cat_sounds location key his voice is pinned to (for its {dir} words)."""
    _load()
    loc = str(state.get("location") or "")
    return "garden_wall" if loc == "wall" else "doorstep" if loc in ("doorstep", "saucer") else "garden"


def visible_from(his_location: str) -> bool:
    """Can Du see him from where he stands? The garden: every spot. The study: the doorstep and the saucer (the
    window by the door) always; the wall only on a bright night or by day (else it is the yowl that tells him)."""
    _load()
    if not in_garden():
        return False
    loc = str(state.get("location") or "")
    if his_location == "garden":
        return True
    if his_location == "study":
        if loc in ("doorstep", "saucer"):
            return True
        try:
            from core import cat as _cat
            c = _cat._conds()
            return "bright" in c or "day" in c
        except Exception:
            return False
    return False


# ── the line pools (cat_content.TOM; rotating; the inline floor is fail-open) ─────────────────────────────
_RECENCY_N = 3


def _pick_fresh(ring_key: str, lines: list[str]) -> str:
    rings = state.setdefault("_rings", {})
    recent = rings.get(ring_key, [])
    fresh = [l for l in lines if l not in recent]
    pick = random.choice(fresh) if fresh else random.choice(lines)
    rings[ring_key] = (recent + [pick])[-_RECENCY_N:]
    return pick


_FALLBACK_KEY = {"look_saucer": "look_close", "look_doorstep": "look_close", "look_yowling": "look_close",
                 "drive_off_saucer": "drive_off", "drive_off_yowling": "drive_off"}


def _pool(key: str, **fill) -> str:
    _load()
    lines: list = []
    try:
        from core import cat_content as cc
        pools = getattr(cc, "TOM", {}) or {}
        lines = list(pools.get(key) or pools.get(_FALLBACK_KEY.get(key, "")) or [])
    except Exception:
        lines = []
    if not lines:
        lines = list(_FLOOR.get(key) or _FLOOR.get(_FALLBACK_KEY.get(key, "")) or ())
    if not lines:
        return ""
    line = _pick_fresh(f"TOM:{key}", lines)
    fill.setdefault("tom", what())
    try:
        from core import cat as _cat
        fill.setdefault("her", _cat._her())
    except Exception:
        fill.setdefault("her", "the cat")
    for k, v in fill.items():
        line = line.replace("{" + k + "}", str(v))
    return line[:1].upper() + line[1:] if line else line


_FLOOR = {
    "wall": ["{tom} is on the wall at the ridge end, sitting still, looking at nothing in particular."],
    "yowling": ["On the wall, {tom}, head back, giving the long rising yowl again and again into the dark."],
    "doorstep": ["{tom} is on the doorstep in the thin light, a big dark shape that does not get up for you."],
    "saucer": ["{tom} is at the saucer by the door, eating what was put out for {her}, in no hurry about it."],
    "look_close": ["You look at the other cat properly: {features}. It looks back with the good eye and goes on with whatever it was doing."],
    "look_unseen": ["You look out for the black cat: the wall and the ridge are dark; nothing you can make out."],
    "drive_off": ["You go at {tom} with your arms up and a shout, and it goes — over the wall and away toward the ridge, not fast."],
    "drive_off_nothing": ["You go out to see the black cat off: nothing there. The wall is empty."],
}


# ── his coming and going ───────────────────────────────────────────────────────────────────────────────────
def _visit_p(now: float, phase: str, weather: str, wind: str, cat_state: dict, dt: float) -> tuple[float, str, str]:
    """(probability of a visit beginning in this window, where, why). 0 when the weather or the clock forbid it."""
    try:
        from core import weather_conditions as _wc
        storm = _wc.is_storm(weather) or "thunder" in (weather or "").lower()
        wet = _wc.is_wet(weather)
    except Exception:
        storm, wet = False, False
    if storm:
        return 0.0, "", ""
    if now < float(state.get("next_visit_not_before") or 0.0):
        return 0.0, "", ""
    winter = _season() == "winter"
    p_h = float(VISIT_P_PER_H.get(phase, 0.0))
    where, why = "wall", phase
    if phase == "day" and winter:
        p_h, where, why = WINTER_DAY_P_PER_H, "doorstep", "winter"
    elif winter and phase in ("night", "dawn") and random.random() < 0.4:
        where, why = "doorstep", "winter"
    if _saucer_has_food(cat_state) and (phase in ("night", "dusk", "dawn") or winter):
        p_h = max(p_h, 0.05) * SAUCER_DRAW
        where, why = "saucer", "saucer"
    if wet:
        p_h *= WET_FACTOR
    try:
        from core import soundscape as _snd
        if _snd._is_hard_wind(wind):
            p_h *= 0.5
    except Exception:
        pass
    return min(1.0, p_h * dt / 3600.0), where, why


def _begin_visit(now: float, where: str, why: str) -> None:
    lo, hi = VISIT_S.get(where, VISIT_S["wall"])
    state["location"] = where
    state["activity"] = "eating" if where == "saucer" else "sitting"
    state["visit"] = {"since": now, "until": now + random.uniform(lo, hi), "where": where, "reason": why,
                      "eat_at": now + random.uniform(*EAT_AFTER_S) if where == "saucer" else 0.0, "ate": False}
    state["visits"] = int(state.get("visits", 0)) + 1
    state["last_visit_ts"] = now
    _mem["render_visit"] = None
    _log({"ts": round(now, 1), "kind": "visit_begin", "where": where, "why": why, "phase": _phase(),
          "his_place": _his_place(), "tolerance": round(float(state.get("tolerance", 0.0)), 3)})


def _end_visit(now: float, how: str, gap: tuple = AFTER_VISIT_GAP_S) -> None:
    v = state.get("visit") or {}
    _log({"ts": round(now, 1), "kind": "visit_end", "how": how, "where": state.get("location"),
          "dur_s": round(now - float(v.get("since") or now)), "ate": bool(v.get("ate")),
          "tolerance": round(float(state.get("tolerance", 0.0)), 3)})
    state["location"], state["activity"], state["visit"] = "ridge", "away", None
    state["yowl_until"] = 0.0
    state["next_visit_not_before"] = now + random.uniform(*gap)


def _eat(now: float, cat_state: dict) -> None:
    """At the saucer: her food is his. The saucer object (cat_state 'saucer', J-0719/J-2466) reads empty afterwards."""
    sc = (cat_state or {}).get("saucer")
    kind = ""
    if isinstance(sc, dict) and sc.get("has_food"):
        kind = str(sc.get("kind") or "")
        sc["has_food"] = False
        sc["eaten_by"] = "tom"
        sc["eaten_ts"] = now
    state["ate_from_saucer"] = int(state.get("ate_from_saucer", 0)) + 1
    v = state.get("visit") or {}
    v["ate"] = True
    state["activity"] = "sitting"
    _log({"ts": round(now, 1), "kind": "ate_saucer", "food": kind, "her": {"loc": cat_state.get("location"),
          "act": cat_state.get("activity")}})


def _maybe_yowl(now: float, phase: str) -> None:
    if state.get("location") != "wall" or phase != "night":
        return
    if state.get("activity") == "yowling":
        if now >= float(state.get("yowl_until") or 0.0):
            state["activity"] = "sitting"
        return
    p = YOWL_P_PER_SAMPLE * (2.0 if YOWL_SMALL_HOURS[0] <= _hour(now) <= YOWL_SMALL_HOURS[1] else 1.0)
    if random.random() < p:
        state["activity"] = "yowling"
        state["yowl_until"] = now + random.uniform(*YOWL_BOUT_S)
        state["yowl_bouts"] = int(state.get("yowl_bouts", 0)) + 1
        _log({"ts": round(now, 1), "kind": "yowl", "hour": _hour(now), "until_s": round(state["yowl_until"] - now),
              "his_place": _his_place()})


def _begin_her(cat_state: dict, now: float, kind: str, loc: str, act: str, mood: str, crosses: bool = False) -> dict:
    from core import cat_ears as _ce
    return _ce._begin(cat_state, now, kind, "tom", loc, act, mood, crosses=crosses)


def _fight(cat_state: dict, now: float, where: str) -> dict:
    """A fight: logged, the hook left for D-2 (her injury path is NOT built here). Who wins decides who leaves."""
    she_wins = random.random() < SHE_WINS_P
    state["fights"] = int(state.get("fights", 0)) + 1
    state["last_fight_ts"] = now
    state["tolerance"] = round(max(0.0, float(state.get("tolerance", 0.0)) - TOLERANCE_FIGHT_HIT), 4)
    hook = {"ts": now, "where": where, "outcome": "she_wins" if she_wins else "he_wins", "her_injury": None,
            "owner": "D-2 mortality (J-2471): her injury path reads this hook; nothing applied here"}
    done = _begin_her(cat_state, now, "tom_fight", "garden_wall" if where == "wall" else "doorstep", HER_FIGHT, "furious")
    t = cat_state.setdefault("tom", {})
    t["last_fight"] = now
    t["fight_hook"] = hook
    _log({"ts": round(now, 1), "kind": "fight", "where": where, "outcome": hook["outcome"], "her": done.get("to"),
          "tolerance": state["tolerance"], "injury_hook": "D-2 (J-2471)"})
    # the aftermath is queued on the visit: she comes out of the fight when its short hold ends (next sample)
    v = state.get("visit") or {}
    v["fight"] = {"ts": now, "she_wins": she_wins, "settled": False}
    return hook


def _settle_fight(cat_state: dict, now: float) -> bool:
    """After the fight's short hold: she won (he leaves, she stays on the wall, furious) or lost (she hides)."""
    v = state.get("visit") or {}
    f = v.get("fight")
    if not f or f.get("settled"):
        return False
    r = cat_state.get("reaction") or {}
    if r and r.get("kind") == "tom_fight" and now < float(r.get("until") or 0.0):
        return False
    f["settled"] = True
    if f.get("she_wins"):
        _begin_her(cat_state, now, "tom_after", str(cat_state.get("location") or "garden_wall"), HER_AFTER, "furious")
        _log({"ts": round(now, 1), "kind": "after_fight", "she": "stays", "he": "leaves"})
        _end_visit(now, "lost_fight", LOST_FIGHT_GAP_S)
        return True
    dest = "under_desk" if _door_open() else "doorstep"
    _begin_her(cat_state, now, "tom_hides", dest, HER_HIDE, "afraid", crosses=True)
    _log({"ts": round(now, 1), "kind": "hides", "she": dest, "he": "stays"})
    v["won"] = True
    return True


def _react_her(cat_state: dict, now: float) -> bool:
    """One reaction of hers per REACTION_GAP_S of a visit, through the hold machinery. True when state changed."""
    if not cat_state or cat_state.get("phase") in (None, "absent", "appearing", "dead"):
        return False   # D-2 (J-2471): a dead cat reacts to nothing; the tom comes and goes unopposed
    if _settle_fight(cat_state, now):
        return True
    if now - float(state.get("last_reaction_ts") or 0.0) < REACTION_GAP_S:
        return False
    r = cat_state.get("reaction") or {}
    if str(r.get("kind") or "").startswith("tom_") and now < float(r.get("until") or 0.0):
        return False     # one tom reaction at a time; an expired hold (cleared by cat.tick's own branch) never blocks
    if cat_state.get("transit"):
        return False
    loc = str(cat_state.get("location") or "")
    act = str(cat_state.get("activity") or "")
    tol = float(state.get("tolerance", 0.0))
    where = str(state.get("location") or "")
    asleep = act in _RESTING
    yowl = state.get("activity") == "yowling"
    if loc in _GARDEN:
        if asleep and random.random() >= (0.7 if yowl else WAKE_P):
            return False
        state["last_reaction_ts"] = now
        if tol >= TOLERATE_AT and random.random() < 0.7:
            _begin_her(cat_state, now, "tom_watch", loc if loc != "garden_wall" else "garden", HER_WATCH, "wary")
            _log({"ts": round(now, 1), "kind": "watch", "where": where, "tolerance": round(tol, 3)})
            return True
        if where == "saucer":
            _begin_her(cat_state, now, "tom_standoff", "doorstep", HER_SPIT, "furious")
        else:
            _begin_her(cat_state, now, "tom_standoff", "garden_wall", HER_STANDOFF, "furious")
        state["standoffs"] = int(state.get("standoffs", 0)) + 1
        _log({"ts": round(now, 1), "kind": "standoff", "where": where, "her_act": cat_state.get("activity"),
              "tolerance": round(tol, 3)})
        if random.random() < FIGHT_P * (1.0 - tol):
            _fight(cat_state, now, where)
        return True
    if loc in _INDOORS:
        if asleep and random.random() >= (0.7 if yowl else WAKE_P):
            return False
        if asleep or loc not in _BY_THE_WINDOW:
            # she wakes / gets up and goes to the glass — indoors to indoors, no door involved
            if random.random() < 0.5 and not yowl:
                return False
        state["last_reaction_ts"] = now
        dest = loc if loc in _BY_THE_WINDOW else "windowsill"
        _begin_her(cat_state, now, "tom_growl", dest, HER_GROWL, "furious")
        _log({"ts": round(now, 1), "kind": "growl", "where": where, "her_from": loc, "tolerance": round(tol, 3)})
        return True
    return False


def _accrue_tolerance(cat_state: dict, dt: float) -> None:
    """Quiet co-presence (she in the garden or at the glass, no stand-off, no fight) wears her fury down — slowly."""
    loc = str(cat_state.get("location") or "")
    act = str(cat_state.get("activity") or "")
    if act in (HER_STANDOFF, HER_SPIT, HER_FIGHT, HER_HIDE):
        return
    if loc in _GARDEN or loc in _BY_THE_WINDOW:
        state["tolerance"] = round(min(1.0, float(state.get("tolerance", 0.0)) + TOLERANCE_PER_MIN * dt / 60.0), 4)


# ── the hook she reads (cat_call._tom_present; cat_sounds; the D-2 job) ───────────────────────────────────
def _sync_hook(cat_state: dict, now: float) -> None:
    t = cat_state.setdefault("tom", {})
    was = bool(t.get("present"))
    t["present"] = in_garden()
    t["where"] = state.get("location") if t["present"] else None
    t["activity"] = state.get("activity") if t["present"] else None
    if t["present"] and not was:
        t["since"] = now
    t.setdefault("last_fight", 0.0)
    t.setdefault("fight_hook", None)


# ── the tick (from cat.tick, every heartbeat; sampled once a minute) ──────────────────────────────────────
def tick(cat_state: dict, now: float | None = None) -> bool:
    """Advance him and her reactions. Returns True when cat_state changed (cat.tick saves)."""
    now = time.time() if now is None else now
    last = float(_mem.get("last") or 0.0)
    if now - last < _SAMPLE_S:
        return False
    dt = min(now - last, _MAX_DT_S) if last else _SAMPLE_S
    _mem["last"] = now
    changed = False
    try:
        if not live_on():
            return False
        _load()
        phase = _phase()
        weather, wind = _weather()
        before = (state.get("location"), state.get("activity"))
        if not in_garden():
            p, where, why = _visit_p(now, phase, weather, wind, cat_state or {}, dt)
            if p > 0.0 and random.random() < p:
                _begin_visit(now, where, why)
        else:
            v = state.get("visit") or {}
            try:
                from core import weather_conditions as _wc
                storm = _wc.is_storm(weather) or "thunder" in (weather or "").lower()
            except Exception:
                storm = False
            if storm:
                _end_visit(now, "storm")
            elif state.get("location") == "saucer" and not v.get("ate") and now >= float(v.get("eat_at") or 0.0):
                _eat(now, cat_state or {})
                changed = True
            elif now >= float(v.get("until") or 0.0) and not (v.get("fight") and not v["fight"].get("settled")):
                _end_visit(now, "left")
            else:
                _maybe_yowl(now, phase)
        if in_garden() and cat_state:
            try:
                if _react_her(cat_state, now):
                    changed = True
                else:
                    _accrue_tolerance(cat_state, dt)
            except profile.NonLiveWriteError:
                raise
            except Exception as exc:
                logger.debug("[cat_tom] her reaction failed (non-fatal): %s", exc)
        if cat_state is not None:
            t0 = dict(cat_state.get("tom") or {})
            _sync_hook(cat_state, now)
            if t0 != cat_state.get("tom"):
                changed = True
        if (state.get("location"), state.get("activity")) != before or in_garden():
            _save()
    except profile.NonLiveWriteError:
        raise
    except Exception as exc:
        logger.debug("[cat_tom] tick failed (non-fatal): %s", exc)
    return changed


# ── what Du sees: presence in his scene, and the look ─────────────────────────────────────────────────────
def presence_line(his_location: str, cat_state: dict | None = None) -> str:
    """One line of him in Du's scene while he is in the garden and visible from there — once per visit, then a rare
    re-notice (never wallpaper). '' when she is already in a tom reaction visible to Du (her line carries them both),
    when he cannot be seen from here, or when he is on the ridge (cat.distant_line's own far-off law takes over)."""
    try:
        _load()
        if not live_on() or not in_garden():
            return ""
        if not visible_from(his_location):
            return ""
        now = time.time()
        if cat_state is None:
            try:
                from core import cat as _cat
                cat_state = _cat._load()
            except Exception:
                cat_state = {}
        her_act = str((cat_state or {}).get("activity") or "")
        her_loc = str((cat_state or {}).get("location") or "")
        if her_act in TOM_ACTS and her_act != HER_HIDE:
            try:
                from core import cat as _cat
                if her_loc in _cat._VISIBLE.get(his_location, set()):
                    return ""        # her own line shows the two of them
            except Exception:
                pass
        v = state.get("visit") or {}
        first = _mem.get("render_visit") != v.get("since")
        if not first:
            if now - float(_mem.get("last_render") or 0.0) < 600.0 or random.random() >= 0.15:
                return ""
        _mem["render_visit"] = v.get("since")
        _mem["last_render"] = now
        loc, act = str(state.get("location") or ""), str(state.get("activity") or "")
        key = "yowling" if act == "yowling" else "saucer" if loc == "saucer" else "doorstep" if loc == "doorstep" else "wall"
        via = "Through the window, " if his_location == "study" else ""
        line = _pool(key)
        if not line:
            return ""
        if via:
            line = via + line[:1].lower() + line[1:]
        _log({"ts": round(now, 1), "kind": "seen", "how": "scene", "his_place": his_location, "where": loc, "act": act, "first": first})
        return line
    except profile.NonLiveWriteError:
        raise
    except Exception:
        return ""


def _note_close_sighting(now: float, his_location: str) -> None:
    """A close look in the garden: a sighting in life's ledger (a face, for D-0129's name-needs-a-face), the
    individual record on the first (his to name from then on), and the learn check (book + face)."""
    state["seen_close"] = int(state.get("seen_close", 0)) + 1
    if not state.get("first_close_ts"):
        state["first_close_ts"] = now
    try:
        from core import life as _life
        _life.rows()                                           # the row must be registered before _maybe_learn can read its hidden truth
        _life._log(_life._LEDGER, {"kind": "sighting", "key": KEY, "place": "garden", "weight": 1.0})
        st = _life._load()
        ind = st.setdefault("individuals", {})
        if KEY not in ind:
            ind[KEY] = {"place": "garden", "since": now, "name": None, "sightings": 1, "last_seen": now,
                        "history": [{"ts": now, "event": "recognised: the black one from the ridge, in the garden, close"}]}
            _life._log(_life._LEDGER, {"kind": "graduated", "key": KEY, "place": "garden", "sightings": 1})
            _life._log(_life._EVENTS, {"kind": "graduated", "key": KEY, "place": "garden"})
        else:
            ind[KEY]["sightings"] = int(ind[KEY].get("sightings", 0)) + 1
            ind[KEY]["last_seen"] = now
        _life._save(force=True)
        _life._maybe_learn(KEY, "sight")
    except profile.NonLiveWriteError:
        raise
    except Exception as exc:
        logger.debug("[cat_tom] sighting not recorded (non-fatal): %s", exc)


def look(his_location: str) -> str:
    """Du looks for the OTHER cat while the tom is in the garden ('' when he is not: cat.distant_look's own far-off
    answer stands). Feature-first (D-0129) until learned; the reveal once a book and a face have earned it; his name
    once Du has given one. Visible from the garden; from the study only what the window by the door shows."""
    try:
        _load()
        if not live_on() or not in_garden():
            return ""
        now = time.time()
        if not visible_from(his_location):
            line = _pool("look_unseen")
            _log({"ts": round(now, 1), "kind": "look", "seen": False, "his_place": his_location, "where": state.get("location")})
            return line
        loc, act = str(state.get("location") or ""), str(state.get("activity") or "")
        key = {"saucer": "look_saucer", "doorstep": "look_doorstep"}.get(loc, "look_close")
        if act == "yowling":
            key = "look_yowling"
        line = _pool(key, features=features_line())
        if his_location == "garden":
            _note_close_sighting(now, his_location)
        ind = _individual()
        if ind and ind.get("name"):
            line += f" It is {ind['name']} — you would know it anywhere now."
        elif learned():
            try:
                from core import life_traces as _lt
                line = _lt.join_reveal(line, str((life_row().get("hidden") or {}).get("reveal") or ""))
            except Exception:
                pass
        _log({"ts": round(now, 1), "kind": "look", "seen": True, "his_place": his_location, "where": loc, "act": act,
              "learned": learned(), "named": bool(ind and ind.get("name"))})
        _save()
        return line
    except profile.NonLiveWriteError:
        raise
    except Exception as exc:
        logger.debug("[cat_tom] look failed (non-fatal): %s", exc)
        return ""


# ── his hands: driving him off; the name ──────────────────────────────────────────────────────────────────
def aims_at_tom(text: str) -> bool:
    return bool(_OTHER_CAT_RE.search((text or "").lower()))


_SEE_OFF_RE = re.compile(r"(?<![a-z-])(?:see|run|chase|drive|shoo)\s+(?:the |that |this |it |him )?[a-z' -]{0,30}?\boff(?![a-z-])")


def _drive_verb(text: str) -> bool:
    t = (text or "").lower()
    if any(re.search(r"(?<![a-z-])" + re.escape(v) + r"(?![a-z-])", t) for v in _DRIVE_VERBS):
        return True
    return bool(_SEE_OFF_RE.search(t))     # "see the black cat off" / "run that cat off": the object between verb and particle


def reachable_from(his_location: str) -> bool:
    """Where Du can act on him from: the garden; the study only with the door open and the tom at the step/saucer."""
    _load()
    if not in_garden():
        return False
    if his_location == "garden":
        return True
    if his_location == "study":
        return _door_open() and str(state.get("location") or "") in ("doorstep", "saucer")
    return False


def drive_off(thought: str, intention: str = "", his_location: str = "") -> str | None:
    """Du's hand toward the tom: a drive-off verb aimed at the OTHER cat. Fail-closed on his location (like
    cat.react). The tom goes — and comes back another night (never tamed, never deterred for good). None when the
    thought is not that hand; an honest 'nothing there' line when it is and he is not in the garden."""
    txt = f"{thought or ''} {intention or ''}"
    if not aims_at_tom(txt) or not _drive_verb(txt):
        return None
    if not his_location:
        return None
    try:
        _load()
        if not live_on():
            return None
        now = time.time()
        try:
            from core import cat_referent as _cr
            _cr.record("react", txt, place=his_location)        # B2: he reached for the OTHER cat, in his own words
        except Exception:
            pass
        if not in_garden():
            if his_location not in ("garden", "study"):
                return None
            return _pool("drive_off_nothing")
        if not reachable_from(his_location):
            return None
        where = str(state.get("location") or "")
        state["driven_off"] = int(state.get("driven_off", 0)) + 1
        state["last_driven_ts"] = now
        line = _pool("drive_off_yowling" if state.get("activity") == "yowling" else "drive_off_saucer" if where == "saucer" else "drive_off")
        _end_visit(now, "driven_off", DRIVEN_OFF_GAP_S)
        # she comes out of her stand-off / growl if she was in one; the fright of a fight lost is hers to keep
        try:
            from core import cat as _cat
            cs = _cat._load()
            if str(cs.get("activity") or "") in (HER_STANDOFF, HER_SPIT, HER_FIGHT, HER_GROWL, HER_WATCH, HER_AFTER):
                cs["activity"], cs["mood"], cs["reaction"] = "watching", "wary", None
                _cat._save()
            _sync_hook(cs, now)
            _cat._save()
        except profile.NonLiveWriteError:
            raise
        except Exception:
            pass
        _log({"ts": round(now, 1), "kind": "driven_off", "where": where, "his_place": his_location, "count": state["driven_off"]})
        try:
            from core import activity_memory
            activity_memory.record("drove_off_the_tom", where)
        except Exception:
            pass
        _save()
        return line
    except profile.NonLiveWriteError:
        raise
    except Exception as exc:
        logger.debug("[cat_tom] drive_off failed (non-fatal): %s", exc)
        return None


def extract_name(text: str) -> str:
    """The name Du gives the OTHER cat, in his own grammar ('I'll call the black cat Soot'). '' when none."""
    for pat in _TOM_NAME_PATS:
        m = re.search(pat, text or "", re.IGNORECASE)
        if m:
            nm = m.group(1).strip(" .,'\"")
            if nm and nm[0].isupper() and nm.lower() not in _NAME_STOP:
                return nm
    return ""


def maybe_name(thought: str, intention: str = "") -> str | None:
    """A naming aimed at the OTHER cat sticks to the tom's individual record — only once Du has met him close (the
    record exists from the first close sighting; life_traces.give_name refuses otherwise). His act, never prompted."""
    nm = extract_name(f"{thought or ''} {intention or ''}")
    if not nm:
        return None
    try:
        _load()
        if not live_on():
            return None
        from core import life_traces as _lt
        line = _lt.give_name(KEY, nm)
        if line and not line.startswith("It already"):
            _log({"ts": round(time.time(), 1), "kind": "named", "name": nm})
        return line or None
    except profile.NonLiveWriteError:
        raise
    except Exception:
        return None


# ── the HUD / pulse ────────────────────────────────────────────────────────────────────────────────────────
def status() -> dict:
    """HUD / tests only. Never read by anything in a prompt path (D-0434)."""
    try:
        _load()
        ind = _individual() or {}
        return {"live": live_on(), "location": state.get("location"), "activity": state.get("activity"),
                "present": in_garden(), "visits": state.get("visits"), "standoffs": state.get("standoffs"),
                "fights": state.get("fights"), "driven_off": state.get("driven_off"), "ate_from_saucer": state.get("ate_from_saucer"),
                "yowl_bouts": state.get("yowl_bouts"), "tolerance": state.get("tolerance"), "seen_close": state.get("seen_close"),
                "learned": learned(), "name": ind.get("name"), "age_y": round((time.time() - float(state.get("born_ts") or time.time())) / YEAR_S, 1),
                "scars": state.get("scars")}
    except Exception as exc:
        return {"error": str(exc)[:80]}
