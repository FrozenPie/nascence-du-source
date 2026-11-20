"""
Nascence — THE LIVING WORLD, L1: the life engine (2026-09-02, J-0510; founder rulings D-0128..D-0133,
docs/staged/living_world_upgrade.md §2).

ONE SCHEMA for every creature (D-0128): a species is a ROW — places and spots, an activity curve by day-phase
(active hours), a presence curve by month (season, migration, hibernation), a weather gate, how it meets LIGHT
(drawn / avoids / needs dark / indifferent, eye-shine), its SOUND points, a count band (how many — a rate, never
individuals), lifespan and stages, what it eats and what eats it, the traces it leaves, how it answers his own
deeds, its HIDDEN TRUTH (species, book names, feature-first render lines), and a visibility roll. Populations by
default; an INDIVIDUAL only by the three graduation triggers (kept / given / re-encountered at one spot) — the cat
is the precedent and stays in core/cat.py behind an adapter (kind="external").

WHO OWNS THE ROWS (D-0128): each place module registers its own rows via register(). The rows declared here are
(a) EXTERNAL adapters over state that already exists (the cat, the nests, the seal, the kororā, the glow-worms, the
lamp moth) — presence read from the owning module, behaviour untouched — and (b) three REFERENCE rows (the hedgehog,
the morepork, the long-tailed bat) that exercise night / hibernation / light / a hidden-truth name; J-0511/J-0512
move those into the place modules when the casts land.

LAWS: the world answers, never leads (a new species renders feature-first until sighting + a book earn the name —
D-0129; grandfathered names kept); state not events, no diary (sound_causality: what he did not witness did not
happen for him — the engine advances whether or not he is there, and only his own looks write his ledger);
world-truth gate (a line may only name what a row says is present, awake and visible); zero LLM; additive-only;
fail-open everywhere. SHADOW-FIRST: RENDER=False logs what a look WOULD have been answered to data/life_events.jsonl
(kind="would_answer") and returns "" so every existing look path behaves exactly as before; flip RENDER after a week
of reading the shadow.

LIGHT (D-0131): light_at(place, standpoint) = core/light.field_at (sun × cloud, moon, the lamp and fire through
the window) + CARRIED light (a lit lantern or candle in his hand — study_life's items). DARK ADAPTATION: standing
outdoors under ~0.12 with no carried light, his eyes open over ~15 minutes; a carried light resets it. Creatures
read both: a hedgehog stops at the lantern's edge (avoids), moths come to it (drawn), glow-worms need the dark and
his adapted eyes (needs_dark), a bird by day needs the light itself (indifferent).
"""
from __future__ import annotations

import json
import logging
import math
import random
import re
import time
import threading
from pathlib import Path

from core import profile

logger = logging.getLogger("nascence.life")

_DATA = Path(__file__).parent.parent / "data"
_F = _DATA / "life_state.json"          # the world's side: presence per row per place, dark adaptation
_LEDGER = _DATA / "life_ledger.jsonl"   # his side: sightings, exposure, names earned (only when RENDER)
_EVENTS = _DATA / "life_events.jsonl"   # truth side: arrivals/departures, shadow would_answer rows

ENABLED = True
RENDER = False                          # shadow-first (plan §7): flip after a week of reading life_events.jsonl
SOUND_GATING = False                    # J-0511 (D-0133): False = soundscape keeps its own creature gating and this
                                        # engine only LOGS the diff (kind="would_gate"); True = creature voices sound
                                        # only when the life table says the bird is present and awake
DEED_BOOST_S = 2 * 3600.0               # a deed (seed scattered, earth turned) draws its takers for two hours
_GATE_LOG_GAP_S = 600.0
PRESENT_AT = 0.15                       # activity at/above which a row counts as PRESENT here now
EVENT_GAP_S = 6 * 3600.0                # one arrival/departure event per row/place per six hours at most
DARK_ADAPT_S = 900.0                    # ~15 min to full dark adaptation
DARK_BELOW = 0.12                       # light_at below this counts as "dark" for adaptation
_LEARN_AT = 1.0                         # book weight needed (a name needs a book AND a face — see learn_from_text)
_SAVE_EVERY_S = 30.0

PHASES = ("dawn", "day", "dusk", "night")
OUTDOORS = ("garden", "shore", "wood")

# ── HOT FLAGS (2026-09-03): the two shadow flags can be flipped WITHOUT a restart — data/life_flags.json overrides
# the module defaults above whenever it carries the key ({"render": true, "gating": true}); read at most every 10 s.
# scripts/life_flags.py writes it. The module constants stay as the code defaults (and as what the smoke sets).
_FLAGS_F = _DATA / "life_flags.json"
_flags_cache: dict = {"ts": 0.0, "v": {}}


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
    v = _flags().get("render")
    return bool(RENDER if v is None else v)


def gating_on() -> bool:
    v = _flags().get("gating")
    return bool(SOUND_GATING if v is None else v)

# ── the schema ──────────────────────────────────────────────────────────────────────────────────

def row(key: str, **kw) -> dict:
    """A species row with every field defaulted, so a place module can declare only what matters."""
    r = {
        "key": key,
        "kind": "population",            # population | individual | external
        "name": None,                    # the grandfathered/common name if the world already says it ("the hedgehog"); else None
        "aliases": (),                   # words in HIS text that mean this row (targets of a look)
        "places": {},                    # {place: [spot, ...]} — where it can be, and the spots within
        "active_hours": {"dawn": 0.3, "day": 1.0, "dusk": 0.3, "night": 0.0},
        "season_curve": [1.0] * 12,      # Jan..Dec presence 0..1 (0 = gone / hibernating)
        "hibernates": False,             # season_curve 0 means asleep here, not away
        "weather_gate": {"rain": 0.6, "wind": 0.7, "storm": 0.1, "frost": 0.6},
        "light": "indifferent",          # drawn | avoids | needs_dark | indifferent
        "eyeshine": False,               # a carried light at night finds two points of light
        "sound": (),                     # soundscape._SOUNDS keys it makes (J-0511 moves gating onto this)
        "sound_at": {},                  # J-2475 (sound_world_expansion §2, D-0500): OPTIONAL per-place sound keys,
                                        # {place: (key, ...)} -- a voice heard at only ONE of a row's places (the
                                        # mice's wall_scratch is the study's wall, never the wood's leaf litter or the
                                        # garden's compost). Read by sounds_active / creature_sound_keys alongside
                                        # `sound`. Additive: a row that leaves it {} is byte-identical to before.
        "sound_days": 1.0,               # J-2475 (D-0500 rarity discipline, "a possum some nights, not every night"):
                                        # the share of calendar days a PRESENT row actually voices at all -- one fact
                                        # for the whole day, seeded off the calendar day exactly as _day_factor is
                                        # (hours after midnight belong to the evening that began them). Read by
                                        # sounds_active only; presence/looks/traces never consult it. 1.0 = voices
                                        # whenever present and awake, byte-identical to before this field existed.
        "count": ("one", "a few", "several"),     # low / mid / high band words
        "lifespan_y": None,
        "stages": (),                    # optional life-cycle stages (name, days) — nests, broods
        "diet": (),                      # what it eats (interaction rows, J-0513)
        "eaten_by": (),
        "traces": (),                    # what it leaves (J-0513 makes them world_traces) -- the FULL set,
                                        # unchanged in meaning: every consumer that reads this field
                                        # directly (HEADS derivation, the trace-object noun gate, ...)
                                        # keeps seeing exactly what it always has.
        "traces_only_at": {},            # F-1671/J-1189: {phrase: (place, ...)} -- an OPTIONAL per-phrase
                                        # place restriction. A phrase with NO entry here fires at every one
                                        # of the row's places, byte-identical to before this field existed.
                                        # A phrase WITH an entry only mints at the named place(s) (life_
                                        # traces.place_traces reads this at traces_pass time) -- e.g. a
                                        # nest only the eaves have, a burrow only the cliff bank has.
                                        # Additive; most rows leave it {}.
        "responds_to_du": {},            # e.g. {"saucer": +0.5, "lantern": -0.8}
        "ease": 0.6,                     # 0..1 conspicuousness: how easily seen when present, awake and lit
        "hidden": None,                  # {"species", "book_names", "book_words", "feature": {phase: line}, "reveal", "miss", "absent": {...}}
        "external": None,                # {"presence": callable(now) -> {place: activity}} for adapters
        "audition": None,                # sound_knowledge.AUDITION key: the NAME lives in that ledger (one ledger, not two)
        "sings_at": (),                  # phases its `sound` keys sound in (empty = whenever present and awake)
        "alarm_sound": None,             # a sound key it makes when `alarm_on` (another row's key) is present at the same place
        "alarm_on": None,
        "nest": None,                    # key of an external nest adapter (garden_life / wood_life / shore_life stage machines)
        "tide": None,                    # "low" | "high": present mainly at that tide state (shore rows)
        "scale": None,                   # callable(now) -> multiplier read from the world (plants in flower, prey about, slug pressure)
        "plural": False,                 # True when `name` is a plural collective ("the gannets", population-grain narration) —
                                        # so a generic fallback line picks "keep" not "keeps" (F-0759/J-0552: verb agreement)
        "note": "",
    }
    r.update(kw)
    return r


_ROWS: dict[str, dict] = {}


def register(rows) -> int:
    """A place module declares its rows (D-0128: things are their own lists). Idempotent by key; a
    re-registration with the same key replaces (so a module's edit reaches the live table on reload)."""
    n = 0
    for r in rows:
        if not isinstance(r, dict) or not r.get("key"):
            continue
        _ROWS[r["key"]] = r
        n += 1
    return n


def rows() -> dict[str, dict]:
    _ensure_builtin()
    return _ROWS


# ── state / logs ────────────────────────────────────────────────────────────────────────────────
_state: dict = {}
_last_save = 0.0


def _load() -> dict:
    global _state
    if _state:
        return _state
    try:
        # J-4426 (F-5128): a damaged life_state.json is logged and falls back to life_state.json.prev before {}.
        from core import store_persist as _sp
        _state = _sp.read_json_durable(_F, "life", logger, guard=profile.guard_path)
    except Exception:
        _state = {}
    _state.setdefault("rows", {})           # {key: {place: {"present": bool, "activity": f, "count": str, "since": ts, "last_event": ts}}}
    _state.setdefault("dark", {"since": 0.0, "place": None, "adapt": 0.0})
    _state.setdefault("_last", 0.0)
    return _state


def _save(force: bool = False) -> None:
    global _last_save
    now = time.time()
    if not force and now - _last_save < _SAVE_EVERY_S:
        return
    path = profile.guard_path(_F)   # J-0610: real data/ only if this process is live; raises before any I/O if not (D-0179, J-0704)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        from core import store_persist as _sp
        _sp.write_text_durable(path, json.dumps(_state, ensure_ascii=False, indent=1))   # J-4426: fsync + .prev
        _last_save = now
    except Exception as exc:
        logger.debug("[life] save failed (non-fatal): %s", exc)


# J-1926 / F-2550: life._log is reached (sound_gate) from the loop thread and from the read_next_sitting worker thread via geometry_census.snapshot; serialise the append.
_APPEND_LOCK = threading.Lock()


def _log(path: Path, rec: dict) -> None:
    path = profile.guard_path(path)   # J-0610; raises before any I/O if non-live (D-0179, J-0704)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        rec = {"ts": round(time.time(), 1), **rec}
        with _APPEND_LOCK, open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _ledger() -> dict:
    """His side, read back from the ledger each time (small)."""
    out: dict = {}
    try:
        if _LEDGER.exists():
            for line in _LEDGER.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                r = json.loads(line)
                k = r.get("key")
                if not k:
                    continue
                s = out.setdefault(k, {"sightings": 0, "exposure": 0.0, "book": 0.0, "learned": False, "last_seen": 0.0})
                if r.get("kind") == "sighting":
                    s["sightings"] += 1; s["exposure"] += float(r.get("weight", 1.0)); s["last_seen"] = max(s["last_seen"], r["ts"])
                elif r.get("kind") == "miss":
                    s["exposure"] += float(r.get("weight", 0.2))
                elif r.get("kind") == "book":
                    s["book"] += float(r.get("weight", 1.0))
                elif r.get("kind") == "learned":
                    s["learned"] = True
    except Exception:
        pass
    return out


# ── the world's clocks (pure functions of time where possible) ──────────────────────────────────

def _phase(now: float) -> str:
    try:
        from core import world_clock as _wc
        return _wc.daylight(now)
    except Exception:
        h = time.localtime(now).tm_hour
        return "night" if (h < 6 or h > 19) else "day"


def _month(now: float) -> int:
    return time.localtime(now).tm_mon


def _weather() -> tuple[str, str, bool]:
    try:
        from core import sensorium as _s
        if not _s.state:
            _s._load()
        return str(_s.state.get("weather", "")), str(_s.state.get("wind", "")), bool(_s.state.get("frost_last"))
    except Exception:
        return "", "", False


def _du_place() -> str:
    try:
        from core import sensorium as _s
        return _s.where()
    except Exception:
        return "study"


def _du_standpoint(place: str) -> str | None:
    try:
        from core import locomotion as _loco
        p = _loco.peek() or {}
        return p.get("standpoint") if p.get("place") == place else None
    except Exception:
        return None


def _weather_factor(r: dict, weather: str, wind: str, frost: bool) -> float:
    g = r.get("weather_gate") or {}
    f = 1.0
    if weather == "thunderstorm" or wind == "gale":
        f *= float(g.get("storm", 0.1))
    elif "rain" in weather or weather == "drizzle":
        f *= float(g.get("rain", 0.6))
    if wind in ("strong", "fresh", "gusty"):
        f *= float(g.get("wind", 0.7))
    if frost:
        f *= float(g.get("frost", 0.6))
    return max(0.0, min(1.0, f))


def _day_factor(key: str, place: str, now: float, days_about: float = 1.0) -> float:
    """Who is about TODAY is one fact for the whole day (the moth-swarm law: seeded off the calendar day,
    hours after midnight belong to the evening that began them) — every reader agrees, nothing persisted.
    `days_about` (a row field, per place or overall): the share of days a VISITOR is here at all — the kererū
    comes to the garden's kōwhai some days, the kingfisher sits the post some days; a resident is 1.0."""
    lt = time.localtime(now)
    day_id = lt.tm_yday - (1 if lt.tm_hour < 12 else 0)
    rng = random.Random(f"life:{key}:{place}:{lt.tm_year}:{day_id}")
    if days_about < 1.0 and rng.random() >= days_about:
        return 0.0
    return 0.55 + 0.7 * rng.random()        # 0.55 .. 1.25


def _days_about(r: dict, place: str) -> float:
    d = r.get("days_about", 1.0)
    if isinstance(d, dict):
        return float(d.get(place, 1.0))
    return float(d if d is not None else 1.0)


def _voice_day(key: str, r: dict, now: float) -> bool:
    """J-2475 (sound_world_expansion §2, D-0500): does this row VOICE today? `sound_days` (a row field, default
    1.0) is the share of calendar days a present row sounds at all -- the plan's own rarity discipline ("a possum
    some nights, not every night; the anti-wallpaper law holds"). One fact for the whole day, seeded off the
    calendar day the way _day_factor is (hours after midnight belong to the evening that began them), on its own
    seed so it never moves the presence draw. A row that leaves the field at 1.0 is byte-identical to before."""
    try:
        share = float(r.get("sound_days", 1.0) if r.get("sound_days") is not None else 1.0)
    except (TypeError, ValueError):
        share = 1.0
    if share >= 1.0:
        return True
    if share <= 0.0:
        return False
    lt = time.localtime(now)
    day_id = lt.tm_yday - (1 if lt.tm_hour < 12 else 0)
    return random.Random(f"life:voice:{key}:{lt.tm_year}:{day_id}").random() < share


def _call_scale(fn, now: float, place: str) -> float:
    try:
        return float(fn(now, place))
    except TypeError:
        return float(fn(now))


def threat_active(key: str, place: str) -> bool:
    """Is what a row fears actually THREATENING here now — the cat present AND stalking/hunting, not asleep on the
    wall. Other keys: present is enough."""
    try:
        if key == "cat":
            from core import cat as _cat
            st = _cat._load()
            loc = str(st.get("location") or "gone"); act = str(st.get("activity") or "")
            # A7.1 (2026-09-07, J-0629/F-0882): was a SECOND, different hand-rolled mapping from
            # _cat_presence's (its "study" list missed on_the_desk/on_your_lap/mantel/by_the_fire
            # entirely, so `here` fell through to the raw location string for those — a cat stalking
            # ON THE DESK could never equal "study" and so could never trip the blackbird alarm there).
            # Now reads the same cat.place_of() _cat_presence uses, so the two can no longer disagree.
            here = _cat.place_of(loc)
            return here == place and any(w in act for w in ("stalk", "hunt", "prowl", "crouch"))
        r = _ROWS.get(key)
        return bool(r) and activity(r, place) >= PRESENT_AT
    except Exception:
        return False


def activity(r: dict, place: str, now: float | None = None) -> float:
    """How active this row is at this place right now: season × active-hours × weather × today's factor."""
    now = time.time() if now is None else now
    if place not in (r.get("places") or {}):
        return 0.0
    if r.get("external"):
        try:
            return float((r["external"]["presence"](now) or {}).get(place, 0.0))
        except Exception:
            return 0.0
    s = float((r.get("season_curve") or [1.0] * 12)[_month(now) - 1])
    if s <= 0.0:
        return 0.0
    ah = float((r.get("active_hours") or {}).get(_phase(now), 0.0))
    w, wd, fr = _weather()
    a = s * ah * _weather_factor(r, w, wd, fr) * _day_factor(r["key"], place, now, _days_about(r, place))
    if r.get("tide"):                                     # shore rows that keep a tide state (the heron at low water)
        try:
            from core import sensorium as _s
            if _s._tide() != r["tide"]:
                a *= 0.3
        except Exception:
            pass
    a *= 1.0 + _deed_boost(r, place, now)                # his own deeds draw their takers (feed_birds, dig, mow)
    if r.get("scale"):                                    # J-0504: the world's own gate — flowers, hosts, prey, slug pressure
        try:
            a *= _call_scale(r["scale"], now, place)
        except Exception:
            pass
    return round(max(0.0, min(1.5, a)), 3)


def note_deed(deed: str, place: str, now: float | None = None) -> None:
    """A world hand tells the engine what he just did where (garden.feed_birds, garden.dig, garden_life.mow…):
    rows whose `responds_to_du` names the deed are drawn for DEED_BOOST_S. World-side state, never rendered."""
    try:
        now = time.time() if now is None else now
        st = _load()
        st.setdefault("deeds", {})[f"{deed}@{place}"] = now
        _save()
    except profile.NonLiveWriteError:
        # J-0726: called directly (own try/except at the call site) from garden.dig()/feed_birds()
        # and garden_life.mow() — let D-0179's hard-raise (guard_path(), F-1024) reach note_deed()'s
        # own caller instead of being swallowed here, one layer below where those callers' own
        # try/except is fixed separately.
        raise
    except Exception:
        pass


def _deed_boost(r: dict, place: str, now: float) -> float:
    resp = r.get("responds_to_du") or {}
    if not resp:
        return 0.0
    deeds = (_load().get("deeds") or {})
    boost = 0.0
    for deed, w in resp.items():
        ts = float(deeds.get(f"{deed}@{place}", 0.0) or 0.0)
        if ts and 0.0 <= now - ts <= DEED_BOOST_S:
            boost += float(w) * (1.0 - (now - ts) / DEED_BOOST_S)
    return max(-0.9, min(1.0, boost))


def _count_band(r: dict, act: float) -> str:
    bands = r.get("count") or ("one", "a few", "several")
    if act < 0.45:
        return bands[0]
    if act < 0.9 or len(bands) < 3:
        return bands[1]
    return bands[2]


# ── light (D-0131) ──────────────────────────────────────────────────────────────────────────────

def carried_light() -> tuple[float, str]:
    """A lit light in his hand: the lantern (D-0131) or a candle. (value 0..1 at arm's length, source)."""
    try:
        # PASSIVE read of the study's state (never study_life._st(): that runs the item sync and can SAVE the room
        # state — a foreign reader like du_pulse must not write Du's live store from its own stale snapshot)
        from core import sensorium as _s
        st = (_s.state or {}).get("study") or {}
        items = st.get("items") or {}
        if st.get("lantern_lit") and (items.get("lantern") or {}).get("carried"):
            return 0.45, "lantern"
        if st.get("candle_lit") and (items.get("candles") or {}).get("carried"):
            _, wind, _ = _weather()
            return (0.0, "") if wind in ("gale", "strong") else (0.18, "candle")
    except Exception:
        pass
    return 0.0, ""


def light_at(place: str | None = None, standpoint: str | None = None, now: float | None = None) -> dict:
    """The light where he stands: the field (sun/cloud/moon/lamp/fire/shade — core/light) plus what he carries.
    Returns {"value", "field", "carried", "source", "band"}. Fail-open to a lit day."""
    try:
        place = place or _du_place()
        standpoint = standpoint if standpoint is not None else _du_standpoint(place)
        from core import light as _lt
        field = float(_lt.field_at(place, standpoint, now))
        c, src = carried_light()
        v = max(0.0, min(1.0, field + c))
        return {"value": round(v, 3), "field": round(field, 3), "carried": c, "source": src, "band": _lt.band_of(v)}
    except profile.NonLiveWriteError:
        # J-0792: light.field_at() now raises correctly (J-0780); this function's own single try
        # no longer swallows it here. Real callers: _advance_dark() (inside advance(), called only
        # from sensorium.tick() -- periodic-tick-only, confirmed excluded, left untouched);
        # look_answer() (dispatch chain dispatch._look -> sensorium.look() -> here, already
        # carrying its own NonLiveWriteError carve-out since J-0751 -- this reaches it safely);
        # and status() (this same file, its own outer except fixed below).
        raise
    except Exception:
        return {"value": 0.6, "field": 0.6, "carried": 0.0, "source": "", "band": "lit"}


def dark_adaptation() -> float:
    """0..1 — how far his eyes have opened to the dark (state kept by advance())."""
    return float((_load().get("dark") or {}).get("adapt", 0.0))


def _advance_dark(now: float) -> None:
    st = _load()
    d = st["dark"]
    place = _du_place()
    lt = light_at(place, now=now)
    if place in OUTDOORS and lt["field"] < DARK_BELOW and lt["carried"] <= 0.0:
        if d.get("place") != place or not d.get("since"):
            d["since"], d["place"] = now, place
        d["adapt"] = round(min(1.0, (now - float(d["since"])) / DARK_ADAPT_S), 3)
    else:
        # a carried light, a lit room, or daylight closes the eyes again — fast
        d["since"], d["place"], d["adapt"] = 0.0, None, 0.0


SEE_BY = 0.10                           # illuminance with plenty of light to SEE by — the field's own 'dim' band starts here (a drizzly
                                        # 07:00 is 'dim', and a blackbird on the lawn is perfectly visible in it); only 'dark' ramps


def _sight(L: float, adapt: float, night: bool = False) -> float:
    """Can he see by this light? 1.0 from a dim overcast morning up; ramping down only into real dark, where his
    opened eyes give some of it back. (The 2026-09-03 replay: treating 0.15 daylight as one-fifth sight made
    694 of 698 looks a miss.) At NIGHT even a full moon is half-sight at best — a shape, not a bird."""
    base = min(1.0, L / SEE_BY)
    if night:
        base = min(0.5, base * 0.5)
    return max(base, 0.4 * adapt)


def _light_factor(r: dict, place: str, now: float) -> tuple[float, bool]:
    """How the light helps or hinders SEEING this row now. (factor 0..1+, eyeshine-possible)."""
    lt = light_at(place, now=now)
    L, carried = lt["value"], lt["carried"]
    adapt = dark_adaptation()
    mode = r.get("light", "indifferent")
    night = _phase(now) in ("night",) or lt["field"] < DARK_BELOW
    eyes = bool(r.get("eyeshine")) and night and carried > 0.0
    if mode == "needs_dark":
        return (max(0.0, 1.0 - L) * max(0.15, adapt), False)
    if mode == "avoids":
        if not night:
            return (_sight(L, adapt, night), False)
        return ((0.25 + 0.75 * adapt) * max(0.1, 1.0 - 0.8 * carried) + (0.5 if eyes else 0.0), eyes)
    if mode == "drawn":
        return ((0.3 + 0.7 * max(L, carried)) if night else _sight(L, adapt, night), False)
    # indifferent: light to see by, or opened eyes at night
    return (_sight(L, adapt, night), eyes)


def visibility(r: dict, place: str, now: float | None = None) -> float:
    now = time.time() if now is None else now
    act = activity(r, place, now)
    if act < PRESENT_AT:
        return 0.0
    lf, _ = _light_factor(r, place, now)
    return round(max(0.0, min(1.0, act * lf * float(r.get("ease", 0.6)))), 3)


# ── the tick ────────────────────────────────────────────────────────────────────────────────────

def advance(now: float | None = None, dt: float = 5.0) -> None:
    """Called from sensorium.tick. Every row's presence at every place moves on the world's clocks whether or
    not he is there (state, no diary): an arrival/departure is logged ONCE as a truth-side event, never rendered."""
    if not ENABLED:
        return
    try:
        now = time.time() if now is None else now
        _ensure_builtin()
        st = _load()
        for key, r in _ROWS.items():
            for place in (r.get("places") or {}):
                act = activity(r, place, now)
                cell = st["rows"].setdefault(key, {}).setdefault(place, {"present": False, "activity": 0.0, "count": "", "since": 0.0, "last_event": 0.0})
                was = bool(cell.get("present"))
                is_now = act >= PRESENT_AT
                cell["activity"], cell["count"] = act, _count_band(r, act) if is_now else ""
                if is_now != was:
                    if now - float(cell.get("last_event", 0.0)) >= EVENT_GAP_S or not cell.get("last_event"):
                        cell["present"], cell["since"], cell["last_event"] = is_now, now, now
                        reason = "hibernating" if (r.get("hibernates") and not is_now and float((r.get("season_curve") or [1] * 12)[_month(now) - 1]) <= 0) else _phase(now)
                        _log(_EVENTS, {"kind": "arrived" if is_now else "departed", "key": key, "place": place, "activity": act, "phase": reason})
                        if is_now:
                            try:   # Transport Manager (D-0133): an arrival is freight — earlier / later / rarer than usual
                                from core import transport_manager as _tm
                                _tm.observe(f"life:{key}:{place}", now, 1.0)
                            except Exception:
                                pass
                    else:
                        cell["present"] = is_now      # flip quietly inside the gap (a bird that comes and goes)
        _advance_dark(now)
        try:   # J-0512 (D-0130): the possum's night work and the trap, on the world's clock
            from core import life_mammals as _lm
            _lm.night_pass(now, dt)
        except Exception:
            pass
        try:   # J-0513: traces left, carcasses decaying (and the natural / storm / cat deaths), the hedgehog's slugs
            from core import life_traces as _lt
            _lt.traces_pass(now, dt)
            _lt.carcass_pass(now, dt)
            _lt.interactions_pass(now, dt)
        except Exception:
            pass
        try:   # J-0504: the aphids on the bean tips (and the ladybirds against them)
            from core import garden_insects as _gi
            _gi.insect_pass(now, dt)
        except Exception:
            pass
        try:   # J-0505: the heap rots down, the worms work the soil, the bed's health moves
            from core import garden_soil as _gs
            _gs.advance(now, dt)
        except Exception:
            pass
        st["_last"] = now
        _save()
    except Exception as exc:
        logger.debug("[life] advance failed (non-fatal): %s", exc)


# ── his look (the answer, or the honest miss) ───────────────────────────────────────────────────

def _match(target: str, place: str) -> dict | None:
    t = (target or "").lower()
    if not t:
        return None
    best = None
    for r in _ROWS.values():
        if r.get("external"):
            continue                      # adapters keep their own look lines (cat.py, garden_life, ...)
        if place not in (r.get("places") or {}):
            continue
        for a in r.get("aliases") or ():
            # A HYPHEN ENDS A WORD HERE TOO (2026-09-09, J-0823/F-1180): the identical unmirrored
            # hyphen-boundary gap the deed-gate arc already fixed in hands.wants()/literal_will.
            # classify()/hands._wants_split()/garden._wants_loose() (J-0787/J-0800/J-0799/J-0822) --
            # a hyphenated compound in the look target could satisfy a bare-alias match via the old
            # (?<![a-z])/(?![a-z]) boundary treating '-' as a word-end. Zero live exposure today, and
            # not merely unobserved -- checked the whole call graph: this function's only caller is
            # look_answer(), reached solely through sensorium.look()'s production entry points
            # (dispatch._look()'s willed-deed chain via inner_monologue_node._observe_target()'s
            # closed cue table; nature_study.py's literal strings; core/orchestrator.py's own
            # human-chat "active perception" branch, its own closed literal set), and every value
            # any of those can ever produce is a bare hyphen-free word ("garden"/"sea"/"pool"/
            # "shore"/"bed"/"sky"/"fire"/"cat"/"letterbox"/"room"/"window"/"desk"/"shelf") --
            # confirmed directly, not assumed. This project's OWN
            # shadow-analysis tooling (scripts/life_shadow_replay.py, scripts/observables_census.py)
            # DOES call look_answer()/sensorium.look() with rich phrases from the real docs/reviews/
            # observe_inventory_2026-09-02.json corpus (1,518 phrasings), bypassing _observe_target()
            # entirely -- a direct before/after sweep of this exact function over all 1,518 found
            # ZERO rows differ (unlike world_detail.py's own sibling fix a few files over, which DID
            # close 12 real rows on that same corpus -- see this job's (J-0823) own recorded finding
            # for the full count). Hardened anyway, for the same reason J-0799/J-0800/J-0822 hardened
            # their own zero-impact sites: convention consistency and defense against a future caller
            # that skips the normalization step.
            if re.search(r"(?<![a-z-])" + re.escape(a.lower()) + r"(?![a-z-])", t):
                if best is None or len(a) > best[0]:
                    best = (len(a), r)
    return best[1] if best else None


# THE BIRD HE HEARD (J-1357/F-1916, 2026-09-26, founder: "that's an honest world answer"): Du names birds by what they
# do -- 'the screaming bird' is his own name for the nesting oystercatcher (12 looks since 09-02) -- and _match() knows
# only aliases, so each of those looks fell through to the bare place look: no bird, while 'the oystercatcher' 109s
# earlier found it screaming at him. A look at 'the <something> bird' that names no row now goes to the bird he actually
# heard or saw here lately: a bird row at this place whose voice (sound_knowledge hearings) or sighting (his ledger) is
# within _HEARD_BIRD_S, AND whose own look text shares a stem with a word he put in front of 'bird' ('screaming' ~
# 'screams'); the most recent such bird wins. No describing word, no match, nothing heard or seen lately, or an unknown
# voice pending sight-binding here = None, and the place's look answers as before ('the birds', 'the bird on the
# branch' are unchanged). Worst-case sweep of all 2,057 phrasings he has used: only his 2 'screaming bird' looks change.
# The world answers his look at the bird that screamed; it never names one he has not met.
_HEARD_BIRD_S = 1800
_BIRD_WORDS = {"bird", "birds"}
# Words that do not tell one bird from another: articles, and the sizes every small-bird line uses ('the small birds' keeps
# its place look). A look must carry a word the row's own text shares, or it is not a description of any bird here.
_DESC_SKIP = {"the", "that", "this", "which", "with", "from", "there", "again", "bird", "birds", "some", "those", "these",
              "small", "little", "tiny", "large", "other", "another", "same"}
_DESC_STOP = {"the", "a", "an", "and", "or", "of", "that", "his", "my", "its", "with", "to", "at", "on", "in"}
_bird_keys: set | None = None


def _bird_row_keys() -> set:
    global _bird_keys
    if _bird_keys is None:
        try:
            from core import life_birds as _lb
            _bird_keys = {r["key"] for r in _lb.rows() if isinstance(r, dict) and r.get("key")}
        except Exception:
            _bird_keys = set()
    return _bird_keys


def _row_text(r: dict) -> str:
    """The row's own words -- aliases, name and every look line -- that his descriptor can meet."""
    h = r.get("hidden") or {}
    parts = [r.get("name") or "", " ".join(r.get("aliases") or ())]

    def _walk(v):
        if isinstance(v, str):
            parts.append(v)
        elif isinstance(v, dict):
            for x in v.values():
                _walk(x)
    _walk(h.get("feature") or {})
    _walk(h.get("feature_by_place") or {})
    return " ".join(parts).lower()


def _heard_bird(target: str, place: str, now: float) -> dict | None:
    words = re.findall(r"[a-zāēīōū]+", (target or "").lower())
    if not _BIRD_WORDS & set(words):
        return None
    # Only the words IN FRONT of 'bird' describe it ('the SCREAMING bird'); where it is ('the bird on the branch', 'the
    # shore and bird') is not a description, and a sweep of his 2,057 observe phrasings showed place words matching the
    # rows' own spot text -- a guess, not the bird he heard. Walk back from 'bird' to the article/conjunction.
    i = next(k for k, w in enumerate(words) if w in _BIRD_WORDS)
    desc = []
    for w in reversed(words[:i]):
        if w in _DESC_STOP:
            break
        if len(w) >= 4 and w not in _DESC_SKIP:
            desc.append(w)
    if not desc:
        return None
    birds = _bird_row_keys()
    try:
        from core import sound_knowledge as _sk
        led = _sk._load()
        # An unknown voice heard here lately owns a 'bird' look: sound_knowledge.look_binding() (after the place's look)
        # is how he earns its name by sight. Step aside so that path runs exactly as before.
        for rc in led.get("recent", []) or []:
            if (rc.get("loc") == place and now - float(rc.get("ts", 0)) <= _sk._RECENT_WINDOW_S
                    and not _sk.is_learned(rc.get("key", ""))):
                return None
        hearings = led.get("hearings", {}) or {}
    except Exception:
        hearings = {}
    seen = _ledger()
    best = None
    for r in _ROWS.values():
        if r["key"] not in birds or r.get("external") or place not in (r.get("places") or {}):
            continue
        voices = tuple(r.get("sound") or ()) + tuple(k for k in (r.get("audition"), r.get("alarm_sound")) if k)
        last = max([float((hearings.get(k) or {}).get("last_ts", 0.0)) for k in voices] +
                   [float((seen.get(r["key"]) or {}).get("last_seen", 0.0))])
        if now - last > _HEARD_BIRD_S:
            continue
        text_words = re.findall(r"[a-zāēīōū]+", _row_text(r))
        hits = sum(1 for w in desc if any(t[:5] == w[:5] for t in text_words if len(t) >= 4))
        if not hits:
            continue
        if best is None or (hits, last) > best[0]:
            best = ((hits, last), r)
    return best[1] if best else None


def is_learned(key: str) -> bool:
    r = _ROWS.get(key) or {}
    if r.get("name"):
        return True
    if r.get("audition"):                 # one ledger, not two: the voice's ledger owns the name
        try:
            from core import sound_knowledge as _sk
            return bool(_sk.is_learned(r["audition"]))
        except Exception:
            return False
    if not r.get("hidden"):
        return True
    return bool(_ledger().get(key, {}).get("learned"))


def name_for(r: dict) -> str:
    """What HE can call it: the grandfathered name, the earned name, or nothing but its look."""
    if r.get("name"):
        return r["name"]
    if r.get("audition"):
        try:
            from core import sound_knowledge as _sk
            if _sk.is_learned(r["audition"]):
                return str(_sk.AUDITION.get(r["audition"], {}).get("source") or "")
        except Exception:
            pass
        return ""
    if r.get("hidden") and is_learned(r["key"]):
        return "the " + str(r["hidden"].get("species") or r["key"])
    return ""


def _absent_line(r: dict, place: str, now: float) -> str:
    h = (r.get("hidden") or {})
    absent = h.get("absent") or {}
    ph = _phase(now)
    s = float((r.get("season_curve") or [1.0] * 12)[_month(now) - 1])
    if s <= 0.0:
        why = "season"
    elif float((r.get("active_hours") or {}).get(ph, 0)) < 0.15:
        why = "night" if ph == "night" else "day"
    else:
        w, wd, _ = _weather()
        why = "weather" if (wd == "gale" or "rain" in w or w == "thunderstorm") else "chance"
    # F-1250/J-0892: a row registered at more than one place (several are — grep places= with two
    # keys in life_birds.py/life_mammals.py/garden_insects.py) may carry hidden.absent[place][why] as
    # a per-place override, tried before the flat hidden.absent[why] below. Only an actual dict at
    # absent[place] is treated this way (a "place" string can never collide with a `why` key, but the
    # isinstance guard makes that doubly explicit) — a row with no such nested dict falls straight
    # through to the pre-existing flat lookup, byte-identical to before this change.
    by_place = absent.get(place)
    line = by_place.get(why) or by_place.get("any") if isinstance(by_place, dict) else None
    if not line:
        line = absent.get(why) or absent.get("any")
    if line:
        return line
    what = name_for(r) or "it"
    keeps = "keep" if r.get("plural") else "keeps"
    return {"season": f"Nothing of {what} at this time of year.",
            "night": f"Not by night; {what} {keeps} the day.",
            "day": f"Not in daylight; {what} {keeps} to the dark.",
            "weather": f"Not in this weather.",
            "chance": f"Nothing shows itself just now."}[why]


def _no_body_line(r: dict | None) -> str:
    """F-1244/J-0887 mechanism A's own honest answer to a dead-thing look with no carcass and no trace
    here — never the living row's own sighting/miss roll below. Feature-first; a species name only if
    that row is already learned or grandfathered (the naming law holds even in absence)."""
    if r and is_learned(r["key"]):
        try:
            from core import life_traces as _lt
            base = re.sub(r"^(a|an)\s+", "", _lt._species_name(r["key"]))   # "a gannet" -> "gannet"
        except Exception:
            base = name_for(r) or "it"
        return f"There is no dead {base} here — nothing of the kind you can find."
    return "There is no body here — nothing of the kind you can find."


def _no_trace_line(noun: str) -> str:
    """F-1617/J-1165: the honest answer to a look at a creature's trace OBJECT ("the gannet feather", "the kingfisher's
    burrow") when the engine has no such trace active here -- never the living row's own sighting/miss roll, which
    would answer about the CREATURE. Feature-first and species-free (the noun is Du's own word from his own target; no
    name is added, so the naming law holds even in absence), and 'no SUCH x' rather than 'no x': it denies the thing
    he asked for, not every x in the place. The world answers, never leads -- no pointer to where one might be."""
    verb = "are" if noun.endswith("s") and not noun.endswith("ss") else "is"
    return f"There {verb} no such {noun} here — nothing of the kind you can find."


def look_answer(target: str, place: str, now: float | None = None, raw: str = "") -> str:
    """The world's answer to 'look at <target>' when the target is a living thing this place can hold.
    '' = not ours, fall through to the place's own look. RENDER=False: logs the would-be answer and returns ''.
    A present row with no line to show at this hour also returns '' -- logged as outcome 'no_line', credited to nothing."""
    if not ENABLED:
        return ""
    try:
        now = time.time() if now is None else now
        _ensure_builtin()
        try:   # J-0513/F-1244 (J-0887 mechanism A): a look at a DEAD thing here answers from the carcass,
               # a trace, or an honest "no body" -- NEVER the living row below. Before this fix, '' from
               # carcass_look fell through to _match()/the living row's own visibility roll -- the actual
               # bug ("the dead gannet" answered by the living gannet's own miss/sighting roll, 89s after
               # the engine minted a trace it then denied). A plant/garden noun (mechanism B's own domain)
               # still returns '' here so the bed's own look answers it, unchanged from before.
            from core import life_traces as _lt
            if _lt.word_present(_lt._CARCASS_WORDS, (target or "").lower()):  # F-1669/J-1188: whole-word, was substring
                if _lt.is_plant_target(target):
                    return ""
                cl = _lt.carcass_look(target, place, now)
                outcome = "carcass"
                if not cl:
                    cl = _lt.dead_trace_look(target, place, now)
                    outcome = "trace"
                if not cl and _lt.is_place_object_target(target, place):
                    outcome = "place_object"   # F-1669/J-1188 mechanism D: "the dead wood"/"the deadfall" --
                                                # a real, non-carcass place object named with a carcass word;
                                                # its own content answers it (falls through), not this block
                elif not cl:
                    cl = _no_body_line(_match(target, place))
                    outcome = "no_body"
                _log(_EVENTS, {"kind": "would_answer" if not render_on() else "answer", "key": "carcass", "place": place, "target": target[:60], "outcome": outcome, "line": cl[:160]})
                return cl if render_on() else ""
        except profile.NonLiveWriteError:
            raise  # J-0751: this function's own outer try (below) needs to see this, not swallow it here
        except Exception:
            pass
        r = _match(target, place)
        heard = False
        if not r:
            r = _heard_bird(target, place, now)      # J-1357: 'the screaming bird' -> the bird that screamed
            heard = r is not None
        desc = None
        if not r:
            try:   # SHORE BESTIARY P2 (docs/staged/shore_creatures.md, J-2868): rows that carry NO name or alias are reached by what he
                   # DESCRIBES -- the words of one look clause (`raw`, the sentence the willed look hand forwards) carrying two different
                   # intrinsic attributes of something actually present and resolvable from where he stands. Nothing registered (flag
                   # "shore_bestiary" off) = no candidates = None, byte-identical to before. "shore_bestiary_render" off = SHADOW: logged
                   # as would_answer and the look falls through unchanged.
                from core import life_shore as _ls
                desc = _ls.described(target, raw, place, now)
                if desc:
                    r = desc["row"]
                    if not _ls.render_live(r.get("bestiary_place", "shore")):
                        _log(_EVENTS, {"kind": "would_answer", "key": r["key"], "place": place, "target": target[:60], "raw": (raw or "")[:100],
                                       "outcome": "described_shadow", "resolved": "described", "tier": desc["pv"]["tier"],
                                       "dist": desc["pv"].get("dist"), "attrs": desc["attrs"], "line": desc["pv"]["line"][:160]})
                        return ""
            except profile.NonLiveWriteError:
                raise
            except Exception as exc:
                logger.debug("[life] described look failed (non-fatal): %s", exc)
                desc, r = None, None
        if not r:
            return ""
        try:   # F-1617/J-1165: J-0887's routing, generalised from dead things to every TRACE. A look at what a creature
               # LEFT ("the gannet feather", "the kingfisher's burrow") names the creature's alias too, so it used to reach
               # the living row's own roll below -- and be denied ("Nothing shows itself") minutes after the engine itself
               # minted the very trace (life_events.jsonl 09-12 09:28:30 and 09-17 08:28:42, the second after J-0887 was
               # live). Now: the creature's own still-active trace answers; failing that, an honest 'no such x here' --
               # never the living row, and no ledger write (a look at a feather is not a sighting of the bird).
               # life_traces.trace_object_noun is the whole (narrow, derived) gate: '' for every plain creature look,
               # which then falls straight through to the roll below exactly as before.
            from core import life_traces as _lt2
            noun = _lt2.trace_object_noun(r, target)
            if noun:
                cl = _lt2.trace_object_look(r, noun, place, now)
                outcome = "trace_object"
                if not cl:
                    cl = _no_trace_line(noun)
                    outcome = "no_trace_object"
                _log(_EVENTS, {"kind": "would_answer" if not render_on() else "answer", "key": "trace", "creature": r["key"], "place": place,
                               "target": target[:60], "outcome": outcome, "noun": noun, "line": cl[:160]})
                return cl if render_on() else ""
        except profile.NonLiveWriteError:
            raise  # J-0751: same re-raise as the carcass block above
        except Exception:
            pass
        act = activity(r, place, now)
        vis = visibility(r, place, now)
        _, eyes = _light_factor(r, place, now)
        learned = is_learned(r["key"])
        h = r.get("hidden") or {}
        ph = _phase(now)
        rendering = render_on()
        if act < PRESENT_AT:
            kind, line = "absent", _absent_line(r, place, now)
        elif (random.Random(f"shore_discover:{int(now // 600)}:{r['key']}").random() if desc else random.random()) < vis:
            # J-3924 (F-4547): a DESCRIBED look rolled an unseeded random.random() against visibility while a discovered look of the same row
            # rolls the ten-minute-bucket-seeded draw (life_shore.discover), so the two disagreed (lions_mane_jelly vis 0.373 described twice
            # = miss twice, while discovered 10x). A described look now uses the SAME seeded draw: repeated looks in a bucket agree and a
            # row he can be shown by looking at the sea is not hidden from him when he describes it. Restart-gated; founder to rule.
            # J-1216 (D-0254/F-1706, precedent: _absent_line's own hidden.absent[place] idiom above): an
            # optional per-place override, tried before the row's own flat feature/eyeshine text.
            # feature_by_place[place] (like eyeshine_by_place[place] below) REPLACES the flat dict
            # wholesale for that place, not a key-by-key merge -- a row's own feature_by_place[place]
            # must carry every phase key it wants preserved, same "no_line" honesty path F-1623/F-1672
            # already protect. Only a row given a *_by_place entry for THIS place is affected; every
            # other row/place renders byte-identically to before.
            feat_by_place = (h.get("feature_by_place") or {}).get(place)
            feat = feat_by_place if isinstance(feat_by_place, dict) else (h.get("feature") or {})
            line = feat.get(ph) or feat.get("night" if ph in ("night", "dusk") else "day") or feat.get("any") or ""
            eyeshine_by_place = (h.get("eyeshine_by_place") or {}).get(place)
            if eyes and (eyeshine_by_place or h.get("eyeshine")):
                line = eyeshine_by_place or h["eyeshine"]
            if desc:   # P2: the look is composed for HIS standpoint and the real distance, not the row's static line
                line = desc["pv"]["line"]
            nm = name_for(r)
            # F-1623/F-1672 (J-1166): a present row with no feature line for THIS phase (51 row/phase pairs: dusk 36, night 7, dawn 6,
            # day 2; the gulls carry only a 'day' line) has nothing to show him. The look already fell through to the place's own
            # look ('' = not ours), but the sighting was still logged, credited to his ledger and counted toward graduation and
            # toward a name (a name needs a face, D-0129) -- the 4th sighting that graduated the gulls (life_events.jsonl line 2193)
            # was a face he was never shown; and once graduated, the bare recognition line was returned with nothing described.
            # `shown` is read BEFORE the reveal is appended: a reveal alone ('— a reef heron; ...') is a caption, not a face.
            # Not the nearest other-phase line instead: several carry their own hour ('in the first light', 'in full daylight',
            # "in the lantern's edge", 'basks') and would be false at another phase, and row look text is not this fix's to write.
            # So: nothing shown, nothing credited, the place's own look answers as before, the row logs honestly as 'no_line'.
            # RENDER off (the shadow branch) is untouched.
            shown = bool(line) or (bool(nm) and not h)
            if nm and h.get("reveal") and learned:
                from core import life_traces as _lt3   # F-1674/J-1190: punctuated, shared with with_individual_suffix
                line = _lt3.join_reveal(line, h["reveal"])
            elif nm and not h:
                line = line or f"There — {nm}."
            kind = "sighting"
            if rendering and not shown:
                kind, line = "no_line", ""
            elif desc and desc["pv"]["tier"] == "form":
                kind = "glimpse"   # P2: an outline and a tone is something seen, not a face: it is shown but credits exposure only
        else:
            # J-1216: same per-place override idiom as the feature/eyeshine block above.
            miss_by_place = (h.get("miss_by_place") or {}).get(place)
            kind, line = "miss", (miss_by_place or h.get("miss") or f"Nothing shows itself; whatever is there keeps still.")
        rec = {"kind": "would_answer" if not rendering else "answer", "key": r["key"], "place": place, "target": target[:60],
               "outcome": kind, "activity": act, "visibility": vis, "phase": ph, "light": light_at(place, now=now)["value"],
               "adapt": dark_adaptation(), "learned": learned, "line": line[:160]}
        if heard:
            rec["resolved"] = "heard_bird"          # J-1357: auditable -- matched by what he heard, not by a name
        if desc:
            rec["resolved"], rec["tier"], rec["dist"] = "described", desc["pv"]["tier"], desc["pv"].get("dist")   # P2: matched by what he described
        _log(_EVENTS, rec)
        _nest_gate = ""
        if rendering:
            try:   # D-0444 / J-2246: the nest-object gate is LIVE -- '' unless this is a nest-object look at the place where that bird's nest is
                from core import nest_gate_shadow as _ngs0
                _nest_gate = _ngs0.live_divert(r, target, place)
            except Exception:
                _nest_gate = ""
        if not _nest_gate:
            try:   # D-0345 / J-1774 (F-2382): the NEST-OBJECT GATE observer. A look that names a nest-owning bird AND its nest, eggs or scrape
                   # ('the oystercatcher and eggs') that the live gate did NOT answer (RENDER off, the bird's nest is at another place, or
                   # nest_gate_shadow.LIVE False) was answered by the bird's own roll above and still is; this appends what the gate WOULD
                   # have diverted to data/nest_gate_shadow.jsonl and nothing else -- it is handed copies, returns a bool nobody reads, draws no
                   # random number, writes no state, and cannot raise out of here. A gated look is logged below, with the answer (J-2246).
                from core import nest_gate_shadow as _ngs
                _ngs.observe(r, target, place, kind, line, rendering)
            except Exception:
                pass
        if not rendering:
            return ""
        _bird_line0 = line                                                   # J-2246: the bird's own line as its life_events row has it
        if kind == "sighting":
            _log(_LEDGER, {"kind": "sighting", "key": r["key"], "place": place, "weight": 1.0})
            _maybe_learn(r["key"], "sight")
            try:   # J-0513: the third graduation trigger, and the individual's recognition line
                from core import life_traces as _lt
                _lt.note_sighting(r["key"], place, now)
                line = _lt.with_individual_suffix(r["key"], line, place)      # F-1622 (J-1166): the join now punctuates; J-1698 (F-2305): said only at the place it graduated at
            except Exception:
                pass
        elif kind == "miss":
            _log(_LEDGER, {"kind": "miss", "key": r["key"], "place": place, "weight": 0.2})
        elif kind == "glimpse":
            _log(_LEDGER, {"kind": "miss", "key": r["key"], "place": place, "weight": 0.2})
        if _nest_gate:
            # D-0444 / J-2246 (option A): the place's nest line always; on a sighting the bird's own line (credit, graduation and the individual
            # suffix all as above, untouched) follows, first letter capitalised, full stop, one space. A miss / absence / no_line: the nest line alone.
            from core import nest_gate_shadow as _ngs1
            try:
                ans = _ngs1.compose(_nest_gate, line if kind == "sighting" else "")
            except Exception:
                ans = _nest_gate
            try:
                _ngs1.observe(r, target, place, kind, _bird_line0, rendering, answer=ans)
            except Exception:
                pass
            return ans
        return line
    except profile.NonLiveWriteError:
        # J-0751: real guarded writes (_log() to _EVENTS/_LEDGER, several call sites above) on
        # the "look" dispatch chain (dispatch._look -> sensorium.look() -> here) -- let
        # guard_path()'s hard raise (D-0179, F-1024) escape this function's own catch-all
        # instead of returning "" silently, matching J-0726's fix shape for the deed chain.
        raise
    except Exception as exc:
        logger.debug("[life] look_answer failed (non-fatal): %s", exc)
        return ""


def discover_look(target: str, place: str, now: float | None = None) -> str:
    """SHORE BESTIARY P3 (docs/staged/shore_creatures.md, J-2936): what a look at a PLACE of the shore (the pool, the sand, the rocks,
    the tideline, the sea, the dunes, the driftwood) shows of the nameless life actually there, from where he stands. The place's own
    look is answered first by sensorium; this returns the text to continue it with ('' = nothing to add). Nothing registered, a target
    that is no place of the shore's life, or nothing visible = '' (byte-identical to before). SHADOW unless data/life_flags.json has
    "shore_bestiary_discover" (and RENDER is on): then each row it WOULD have shown is logged as would_answer / 'discover_shadow'
    and '' is returned. Live: a colour/detail tier credits a SIGHTING (and can graduate, and with a book can name); a form tier is a
    GLIMPSE (exposure only). Never a name, never a pointer."""
    if not ENABLED or place not in ("shore", "wood"):
        return ""
    try:
        now = time.time() if now is None else now
        _ensure_builtin()
        from core import life_shore as _ls
        found = _ls.discover(target, place, now)
        if not found:
            return ""
        live = _ls.discover_live(place) and render_on()
        parts: list[str] = []
        for f in found:
            r, pv = f["row"], f["pv"]
            tier = pv["tier"]
            outcome = "discover_shadow" if not live else ("glimpse" if tier == "form" else "sighting")
            _log(_EVENTS, {"kind": "answer" if live else "would_answer", "key": r["key"], "place": place, "target": target[:60], "outcome": outcome,
                           "resolved": "discovered", "tier": tier, "dist": pv.get("dist"), "line": pv["line"][:160]})
            if not live:
                continue
            line = pv["line"]
            if tier == "form":
                _log(_LEDGER, {"kind": "miss", "key": r["key"], "place": place, "weight": 0.2})
            else:
                _log(_LEDGER, {"kind": "sighting", "key": r["key"], "place": place, "weight": 1.0})
                _maybe_learn(r["key"], "sight")
                try:   # the same graduation + recognition bookkeeping a creature look gets (J-0513)
                    from core import life_traces as _lt
                    _lt.note_sighting(r["key"], place, now)
                    line = _lt.with_individual_suffix(r["key"], line, place)
                except Exception:
                    pass
            parts.append(line)
        return " ".join(parts)
    except profile.NonLiveWriteError:
        raise
    except Exception as exc:
        logger.debug("[life] discover_look failed (non-fatal): %s", exc)
        return ""


def credit_find(key: str, place: str, now: float | None = None, line: str = "") -> bool:
    """A DEED put a creature in his hand (core/shore_dig.py, D-0652): log it as an answer and credit a SIGHTING exactly as a place look
    at colour/detail tier does (the ledger row, _maybe_learn, life_traces.note_sighting). Only when the engine and RENDER are on and the
    row is registered; returns whether it credited. Never a name."""
    if not ENABLED or not render_on():
        return False
    try:
        now = time.time() if now is None else now
        _ensure_builtin()
        r = _ROWS.get(key)
        if not r:
            return False
        _log(_EVENTS, {"kind": "answer", "key": key, "place": place, "target": "dig", "outcome": "sighting", "resolved": "dug",
                       "tier": "detail", "line": (line or "")[:160]})
        _log(_LEDGER, {"kind": "sighting", "key": key, "place": place, "weight": 1.0})
        _maybe_learn(key, "sight")
        try:
            from core import life_traces as _lt
            _lt.note_sighting(key, place, now)
        except profile.NonLiveWriteError:
            raise
        except Exception:
            pass
        return True
    except profile.NonLiveWriteError:
        raise
    except Exception as exc:
        logger.debug("[life] credit_find failed (non-fatal): %s", exc)
        return False


def _maybe_learn(key: str, via: str) -> bool:
    """A name needs a book AND a face (D-0129): book weight >= 1.0 and at least one sighting."""
    r = _ROWS.get(key) or {}
    if not r.get("hidden") or r.get("name"):
        return False
    s = _ledger().get(key) or {}
    if s.get("learned"):
        return False
    if float(s.get("book", 0.0)) >= _LEARN_AT and int(s.get("sightings", 0)) >= 1:
        _log(_LEDGER, {"kind": "learned", "key": key, "via": via, "species": r["hidden"].get("species")})
        logger.info("[life] LEARNED %s -> %s (via %s)", key, r["hidden"].get("species"), via)
        return True
    return False


def learn_from_text(text: str) -> list[str]:
    """His reading can name a creature (the diegetic channel, as sound_knowledge.learn_from_text): a text that
    carries one of the row's book names beside its book words is a BOOK event; the name lands only once he has
    also seen the thing (a name without a face is a word, not knowledge). Returns newly learned keys."""
    out: list[str] = []
    try:
        if not ENABLED or not text:
            return out
        _ensure_builtin()
        low = text.lower()
        led = _ledger()
        for key, r in _ROWS.items():
            h = r.get("hidden")
            if not h or r.get("name") or (led.get(key) or {}).get("learned"):
                continue
            if any(n in low for n in (h.get("book_names") or ())) and any(w in low for w in (h.get("book_words") or ())):
                if float((led.get(key) or {}).get("book", 0.0)) < _LEARN_AT:
                    _log(_LEDGER, {"kind": "book", "key": key, "weight": 1.0, "note": low[:80]})
                if _maybe_learn(key, "read"):
                    out.append(key)
    except profile.NonLiveWriteError:
        # J-0770: let D-0179's hard-raise (guard_path(), F-1024) reach this function's own
        # caller (core/study_note.py's book-naming-a-creature channel) instead of this
        # pre-existing broad except swallowing it.
        raise
    except Exception:
        pass
    return out


# ── for the soundscape (J-0511 moves the gating here) and the pulse/HUD ─────────────────────────

def sounds_active(place: str, now: float | None = None) -> list[str]:
    """Sound-point keys of rows present and awake at this place now, in their singing hours; an ALARM sound when
    the row it fears (the cat) is present here too; DAWN CHORUS when three or more singers are here at dawn."""
    now = time.time() if now is None else now
    _ensure_builtin()
    ph = _phase(now)
    present = {k: r for k, r in _ROWS.items() if activity(r, place, now) >= PRESENT_AT}
    out: list[str] = []
    singers = 0
    for k, r in present.items():
        # the ALARM is not a song: it sounds while the bird is here and what it fears is here AND threatening
        # (the cat stalking, not asleep on the wall — the replay had it alarming 98 hours a week)
        if r.get("alarm_sound") and r.get("alarm_on") in present and threat_active(r["alarm_on"], place) and r["alarm_sound"] not in out:
            out.append(r["alarm_sound"])
        sings = r.get("sings_at") or ()
        if sings and ph not in sings:
            continue
        if not _voice_day(k, r, now):          # J-2475: a row that voices only some days is silent today (presence untouched)
            continue
        # J-2475: `sound` keys sound at every place the row is present; `sound_at[place]` keys only at THAT place.
        voiced = tuple(r.get("sound") or ()) + tuple((r.get("sound_at") or {}).get(place) or ())
        keys = [s for s in voiced if s not in out]
        out += keys
        if keys and sings and "dawn" in sings and r.get("kind") != "external":
            singers += 1
    if ph == "dawn" and singers >= 3 and "dawn_chorus" not in out:
        out.append("dawn_chorus")
    return out


def creature_sound_keys(place: str | None = None) -> set[str]:
    """The sound keys the gate is allowed to govern — for a PLACE, only the keys of rows that can BE there. A
    row's places are where it is, not where it is heard: the morepork is heard from the study but lives in the
    wood, so the study's legacy propagation keeps its say (the replay had the gate silencing it there)."""
    _ensure_builtin()
    keys = {"dawn_chorus"} if place is None else set()
    for r in _ROWS.values():
        if place is not None and place not in (r.get("places") or {}):
            continue
        keys.update(r.get("sound") or ())
        sound_at = r.get("sound_at") or {}        # J-2475: per-place voices are governed only at their own place
        if place is None:
            for ks in sound_at.values():
                keys.update(ks or ())
        else:
            keys.update(sound_at.get(place) or ())
        if r.get("alarm_sound"):
            keys.add(r["alarm_sound"])
        if place is not None and (r.get("sings_at") or ()) and "dawn" in r["sings_at"]:
            keys.add("dawn_chorus")
    return keys


_gate_last: dict = {}


def sound_gate(place: str, legacy: list[str], now: float | None = None) -> list[str]:
    """Called by soundscape.active_sounds. SOUND_GATING=False: return `legacy` unchanged and LOG what the engine
    would have changed (would_gate: added / dropped) at most every _GATE_LOG_GAP_S per place — the shadow to read
    before flipping. True: creature keys come from the life table; every non-creature key stays as it was, and the
    same diff is now logged live too (kind=gate, F-1243/J-0888) under the same per-place throttle, so the gate is
    readable from data exactly the way the shadow was — D-0166's gull_cries defeater needs this, not a guess."""
    try:
        now = time.time() if now is None else now
        governed = creature_sound_keys(place)
        mine = sounds_active(place, now)
        kept = [k for k in legacy if k not in governed]
        gated = kept + [k for k in mine if k not in kept]
        if gating_on():
            # F-1243: this branch used to return silently -- the 515 pre-flip would_gate shadow rows
            # had nothing live to replace them. Additive only; the shadow branch below is untouched.
            added = sorted(set(mine) - set(legacy))
            dropped = sorted(k for k in legacy if k in governed and k not in mine)
            if (added or dropped) and now - float(_gate_last.get(place, 0.0)) >= _GATE_LOG_GAP_S:
                _gate_last[place] = now
                _log(_EVENTS, {"kind": "gate", "place": place, "phase": _phase(now), "added": added, "dropped": dropped, "active": sorted(gated)[:12]})
            return gated
        added = sorted(set(mine) - set(legacy))
        dropped = sorted(k for k in legacy if k in governed and k not in mine)
        if (added or dropped) and now - float(_gate_last.get(place, 0.0)) >= _GATE_LOG_GAP_S:
            _gate_last[place] = now
            _log(_EVENTS, {"kind": "would_gate", "place": place, "phase": _phase(now), "added": added, "dropped": dropped})
        return legacy
    except Exception:
        return legacy


def calendar(now: float | None = None) -> list[dict]:
    """THE MIGRATION CALENDAR (D-0133): for every row that is ever absent, the months it arrives and leaves, and
    whether it is here now — read from the season curves, so the calendar can never disagree with the world."""
    now = time.time() if now is None else now
    _ensure_builtin()
    out = []
    m_now = _month(now)
    names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    for k, r in _ROWS.items():
        sc = r.get("season_curve") or [1.0] * 12
        if r.get("external") or min(sc) > 0.0:
            continue
        here = [i for i in range(12) if sc[i] > 0.0]
        arrivals = [names[i] for i in range(12) if sc[i] > 0.0 and sc[i - 1] <= 0.0]
        departures = [names[i] for i in range(12) if sc[i] <= 0.0 and sc[i - 1] > 0.0]
        out.append({"key": k, "kind": "hibernator" if r.get("hibernates") else "migrant", "arrives": arrivals, "leaves": departures,
                    "here_now": sc[m_now - 1] > 0.0, "months_here": len(here), "places": list((r.get("places") or {}).keys())})
    out.sort(key=lambda x: (not x["here_now"], x["key"]))
    return out


def who_about(place: str | None = None, now: float | None = None) -> list[dict]:
    """Present-and-awake rows at a place (all places if None) — for the pulse and the who's-about panel."""
    now = time.time() if now is None else now
    _ensure_builtin()
    led = _ledger()
    out = []
    for r in _ROWS.values():
        for p in (r.get("places") or {}):
            if place and p != place:
                continue
            act = activity(r, p, now)
            if act >= PRESENT_AT:
                out.append({"key": r["key"], "place": p, "activity": act, "count": _count_band(r, act),
                            "visibility": visibility(r, p, now), "kind": r.get("kind"),
                            "known": bool(r.get("name")) or is_learned(r["key"]),
                            "last_seen": (led.get(r["key"]) or {}).get("last_seen", 0.0)})
    out.sort(key=lambda x: -x["activity"])
    return out


def status() -> dict:
    """For du_pulse / the HUD: rows, who is about, what he has come to know, the shadow's own counts."""
    try:
        _ensure_builtin()
        now = time.time()
        led = _ledger()
        about = who_about(None, now)
        shadow = {"would_answer": 0, "sighting": 0, "miss": 0, "absent": 0, "arrived": 0, "departed": 0, "would_gate": 0}
        try:
            if _EVENTS.exists():
                for line in _EVENTS.read_text(encoding="utf-8").splitlines()[-4000:]:
                    if not line.strip():
                        continue
                    e = json.loads(line)
                    k = e.get("kind")
                    if k in ("would_answer", "answer"):
                        shadow["would_answer"] += 1
                        shadow[e.get("outcome", "miss")] = shadow.get(e.get("outcome", "miss"), 0) + 1
                    elif k in ("would_gate", "gate"):
                        # F-1243/J-0888: a live kind=gate row counts beside a shadow would_gate row, the
                        # same "answer folds into would_answer" idiom just above -- so this counter keeps
                        # moving once GATING flips on and the shadow branch stops logging would_gate rows,
                        # and the HUD's own "N would-gate" line (hud/static/app.js: d.shadow.would_gate)
                        # does not read 0 forever.
                        shadow["would_gate"] += 1
                    elif k in shadow:
                        shadow[k] += 1
        except Exception:
            pass
        return {"enabled": ENABLED, "render": render_on(), "rows": len(_ROWS),
                "external": sum(1 for r in _ROWS.values() if r.get("external")),
                "about": [{"key": a["key"], "place": a["place"], "count": a["count"], "vis": a["visibility"]} for a in about[:12]],
                "learned": [k for k in _ROWS if _ROWS[k].get("hidden") and not _ROWS[k].get("name") and (led.get(k) or {}).get("learned")],
                "learning": {k: {"book": v.get("book", 0), "sightings": v.get("sightings", 0)} for k, v in led.items() if not v.get("learned")},
                "light": light_at(), "dark_adapt": dark_adaptation(), "shadow": shadow,
                "sound_gating": gating_on(), "calendar": calendar(now),
                "traces_deaths": (__import__("core.life_traces", fromlist=["x"]).hud_payload(now))}
    except profile.NonLiveWriteError:
        # J-0792: reached via who_about()->visibility()->_light_factor()->light_at() (line ~875)
        # or the bare light_at() call just above (line ~904), both bare (no wrapper of their own)
        # -- this function's own outer except is the real catch point, matching J-0778's identical
        # locomotion.status() precedent (fixed directly, not excluded like hud/server.py's own
        # read-only route wrapping). Both known external callers already handle this gracefully on
        # their own: hud/server.py's /api/life route already wraps _life.status() in its own
        # try/except, turning this into a proper {"error": ...} JSON response; scripts/du_pulse.py
        # already wraps its own "living world" section in a bare try/except: pass. Re-raising here
        # is real propagation, not a new crash risk for either.
        raise
    except Exception as exc:
        return {"enabled": ENABLED, "error": str(exc)[:80]}


# ── the built-in rows: adapters over existing state + three reference rows ──────────────────────
_builtin_done = False


def _cat_presence(now: float) -> dict:
    try:
        from core import cat as _cat
        st = _cat._load()
        loc = str(st.get("location") or "gone")
        if loc == "gone" or st.get("phase") == "absent":
            return {}
        # A7.1 (2026-09-07, J-0629/F-0882): was its own hand-rolled, incomplete study/else-garden split
        # (on_the_desk/on_your_lap/mantel/indoors all fell through to "garden"; shore/wood/away_hunting
        # did too) — now reads cat.place_of(), the single mapping derived from cat._VISIBLE. A place of
        # None (shore/wood/away_hunting — not registered as a place this row tracks) means genuinely not
        # present here, not a false "garden".
        place = _cat.place_of(loc)
        return {place: 1.0} if place else {}
    except Exception:
        return {}


def _nest_presence(mod: str, place: str):
    def f(now: float) -> dict:
        try:
            import importlib
            m = importlib.import_module(f"core.{mod}")
            d = m._load()
            n = d.get("nest")
            return {place: 1.0} if n else {}
        except Exception:
            return {}
    return f


def _seal_presence(now: float) -> dict:
    try:
        from core import shore_life as _shl
        return {"shore": 1.0} if _shl._load().get("seal") else {}
    except Exception:
        return {}


def _glowworm_presence(now: float) -> dict:
    w, wind, _ = _weather()
    dark = _phase(now) == "night"
    still = wind in ("", "calm", "breeze", "light")
    damp = w in ("drizzle", "overcast", "steady rain", "high cloud") or True
    return {"wood": 0.9} if (dark and still and damp) else {}


def _moth_presence(now: float) -> dict:
    try:
        from core import sensorium as _s
        st = (_s.state or {}).get("study") or {}          # passive read (see carried_light)
        lit = bool(st.get("lamp_lit") or st.get("candle_lit") or _s.state.get("fire", "out") != "out")
        a = _s.moth_activity(_phase(now) == "night", lit)
        return {"study": min(1.5, float(a))} if a > 0 else {}
    except Exception:
        return {}


def _ensure_builtin() -> None:
    global _builtin_done
    if _builtin_done:
        return
    _builtin_done = True
    # adapters — presence read from the owning module; behaviour and look lines stay theirs
    # B1 (2026-10-28, J-2465, cat_overhaul): her life-schema fields (active_hours, season_curve,
    # weather_gate, light/eyeshine, diet, traces, lifespan_y, hidden) are declared in core/cat.py's
    # LIFE_ROW and merged onto her row here — the body stays hers, the schema reads like every other
    # creature's. Fail-open: a cat module without LIFE_ROW registers the row exactly as before.
    try:
        from core import cat as _catmod
        _cat_fields = {k: v for k, v in (getattr(_catmod, "LIFE_ROW", {}) or {}).items()
                       if k not in ("key", "kind", "name", "aliases", "places", "external", "note")}
    except Exception:
        _cat_fields = {}
    register([
        row("cat", kind="external", name="the cat", aliases=(), places={"garden": [], "study": []},
            external={"presence": _cat_presence}, note="core/cat.py — the individual precedent", **_cat_fields),
        row("glowworms", kind="external", name="the glow-worms", places={"wood": ["spring"]}, light="needs_dark",
            external={"presence": _glowworm_presence}, note="wood_life — only when he stands at the spring and looks"),
        row("lamp_moths", kind="external", name="the moths", plural=True, places={"study": ["lamp"]}, light="drawn", sound=("moth_tap",),
            external={"presence": _moth_presence}, note="sensorium.moth_activity — the population precedent"),
    ])
    # THE TOM (2026-10-28, cat_overhaul B3, J-2470, D-0507 (c)): the OTHER cat as a real second life row —
    # kind "individual", presence from core/cat_tom's own state machine (an external adapter like hers), hidden
    # truth (feature-first, book_names) like every creature's. Fail-open: no tom module, no row, nothing else moves.
    try:
        from core import cat_tom as _ct
        register([_ct.life_row()])
    except Exception as exc:
        logger.debug("[life] cat_tom not registered (non-fatal): %s", exc)
    # THE BIRDS (J-0511): the whole cast, plus the nest adapters (the kororā is a real row there now)
    try:
        from core import life_birds as _lb
        register(_lb.nest_adapters())
        register(_lb.rows())
    except Exception as exc:
        logger.debug("[life] life_birds not registered (non-fatal): %s", exc)
    # THE MAMMALS, REPTILES AND THE REST (J-0512): the cast, the fur seal over shore_life's haul-out
    try:
        from core import life_mammals as _lm
        register([_lm.seal_adapter()])
        register(_lm.rows())
    except Exception as exc:
        logger.debug("[life] life_mammals not registered (non-fatal): %s", exc)
    # THE GARDEN'S INSECTS (J-0504, the garden chapter): populations gated on flowers, hosts, prey, slug pressure
    try:
        from core import garden_insects as _gi
        register(_gi.rows())
    except Exception as exc:
        logger.debug("[life] garden_insects not registered (non-fatal): %s", exc)
    # SOIL LIFE (J-0505): the worms and the slaters
    try:
        from core import garden_soil as _gs
        register(_gs.rows())
    except Exception as exc:
        logger.debug("[life] garden_soil not registered (non-fatal): %s", exc)
    # THE SHORE BESTIARY (docs/staged/shore_creatures.md, P1 pilot, 2026-11-01): rows whose look is composed from an observable
    # tuple (nothing names them). Registered ONLY when data/life_flags.json has "shore_bestiary": true -- default OFF, so with the
    # flag absent this block does nothing and every other row behaves exactly as before. Read once, here: a restart picks it up.
    try:
        from core import life_shore as _ls
        if _ls.enabled():
            register(_ls.rows())
    except Exception as exc:
        logger.debug("[life] life_shore not registered (non-fatal): %s", exc)
    # THE WOODS BESTIARY (docs/staged/wood_creatures.md, J-3062): same engine, the wood's own zones and flag. Importing core.life_wood
    # registers the wood as a place; its rows register only when data/life_flags.json has "wood_bestiary": true (default OFF).
    try:
        from core import life_wood as _lw
        if _lw.enabled():
            register(_lw.rows())
    except Exception as exc:
        logger.debug("[life] life_wood not registered (non-fatal): %s", exc)
    return

# (L1's two reference rows — the hedgehog and the long-tailed bat — moved to core/life_mammals.py on 2026-09-03, J-0512.)
