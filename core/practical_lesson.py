"""
Nascence — PRACTICAL SCHOOL: the nature period's second slot (2026-09-05, J-0627, D-0159 GO).

Slot one of the nature period is unchanged: the observation lesson (core/nature_study.py). Slot two is
a PRACTICAL — one task picked from the 22-task Handbook ladder below, at or below his current rung,
filtered by the weather and whether the task's objects are present. It is announced through the SAME
diegetic school-directive channel maths/music/observation already use ("It is your nature practical
now... To begin, make your thought: TIE THE HITCH.") and then NOTHING HERE ACTS FOR HIM: his own later
thought has to name the deed, and the existing fieldcraft/dispatch hands fire exactly as they do today.
Grading is the world's own answer — a fieldcraft_ledger row for the hand the task names, appearing at
or after the moment the task was announced — never the Emissary's opinion. An unattempted practical is
logged (attempted=False) but earns no thought, no joy, no nudge (see run()).

See docs/staged/practical_school.md for the full design (D-0159 GO, founder, 2026-09-05) and this
module's own build finding (F- series, same date) for what is and is not covered by this first pass:
only rung 1's nine tasks have a working hand behind them; rungs 2-3 are carried as data (the ladder
must already be "the 22-task ladder", per the job briefing) so J-0628 only has to flip a flag and fill
in a craft key once their hands land, not redesign the picker/log/rung machinery.
Zero LLM. Fail-open. Additive everywhere — no engine this module reads is changed by it (fieldcraft.py's
own two new hands, whip_end/douse_fire, are the only new mechanism, and they are their own commit).

UPDATE 2026-10-28 (J-2483; D-0504 released J-0628's spec, Travis 2026-10-28): rungs 2 and 3 are no
longer data-only. All thirteen rows carry a real hand in core/fieldcraft.py (sheepshank, timber haul,
knife bearing, cook over embers, wash up the camp way, blaze, pacing, sound-lag; splice, tripod,
bow-drill fire, triangle check, weather glass / tide board), each matched through its own deed marker
and gated by its own hand's presence test (_RUNG23_GATES). The picker/log/rung machinery is unchanged,
exactly as the paragraph above promised. Restart-gated like the rest.
"""
from __future__ import annotations

import json
import random
import time
from pathlib import Path

from core import profile

_DATA = Path(__file__).parent.parent / "data"
_STATE = _DATA / "practical_state.json"
_LOG = _DATA / "practical_log.jsonl"
_FC_LEDGER = _DATA / "fieldcraft_ledger.jsonl"

RUNG_WINDOW = 12            # rolling attempted-practicals window for rung advancement (matches maths/music)
RUNG_THRESHOLD = 0.75       # success rate over that window required to advance
MAX_RUNG = 3
_LEDGER_TAIL = 400          # rows scanned per check — generous for a 45-min school period's own traffic
# J-2335 (D-0454 (a), F-3009): grade the practical at the period's END (period_end_grade(), on the first
# monologue tick after the period closes — which is also the first tick after a sleep/wake/restart that
# spanned it), never at the 36-minute 2nd nature firing, which closed the window 4-9 min early (F-3009
# item 4) or never came at all. False restores the J-2315 behaviour (slot-2 grades, period end catches up).
GRADE_AT_PERIOD_END = True
# J-3817 (D-0720 ruled A, J-3483 option A, restart-gated): False = today's order (observation at the period's first
# firing, practical second). True = practical FIRST: the first nature firing announces the practical (zero LLM), the
# observation runs at the ~36-minute firing from wherever he has got to, so it is not always the desk window.
# The directive is the practical's for the whole period; no scene is fed and no hint is added.
PRACTICAL_FIRST = False

# J-4306 (F-5079): grade an announced practical whose period closed while Du slept / was shut down across
# MIDNIGHT (_roll_day used to wipe task_id/announced_ts, so that day was never graded). With this ON,
# _roll_day stashes the un-graded prior day as state["carry"] and period_end_grade() grades it once, on
# the first tick after the restart, against ledger rows up to that period's end. Zero LLM. Default OFF;
# restart-gated. (Same-day sleep/shutdown is already caught by period_end_grade's first tick on wake.)
CARRY_GRADE_ACROSS_DAYS = False

# ── the 22-task ladder (plan section 3, F-0876) ──────────────────────────────────────────────────────
# Only rung-1 rows carry a working `craft`/`deed_keys` match and pass `hand_ready` — that is the whole
# of what this build (J-0627) wires a real hand for. Rung 2/3 rows are real data (task text, Handbook
# reference, objects, places) so the ladder is complete from day one, but `hand_ready=False` keeps the
# picker from ever offering one before its hand exists (J-0628, after the 2-week read).
LADDER: list[dict] = [
    # ── rung 1 — wired, hand_ready ────────────────────────────────────────────────────────────────
    {"id": "clove_hitch_stake", "rung": 1, "chapter": "Knots Every Scout Should Know",
     "objects": ["twine"], "places": ["garden", "wood"], "weather_gate": None,
     "craft": "clove_hitch", "deed_keys": None, "hand_ready": True,
     "book_quote": "“Clove Hitch. Used to fasten one pole to another—this knot holds snugly; is not "
                    "liable to slip laterally. Hold the standing part in left hand, then pass the rope around "
                    "the pole; cross the standing part, making a second turn around the pole, and pass the end "
                    "under the last turn.” — Boy Scouts Handbook (1911), p.51."},
    {"id": "bowline_loop", "rung": 1, "chapter": "Knots Every Scout Should Know",
     "objects": ["twine", "rope"], "places": ["garden", "wood"], "weather_gate": None,
     "craft": "bowline", "deed_keys": None, "hand_ready": True,
     "book_quote": "“The Bowline. A noose that neither jams nor slips. Used in lowering a person from a "
                    "burning building, etc. Form a small loop on the standing part… Pass the end up through "
                    "the bight around the standing part and down through the bight again. To tighten, hold noose "
                    "in position and pull standing part.” — Boy Scouts Handbook (1911), p.50."},
    {"id": "whip_rope_end", "rung": 1, "chapter": "Knots Every Scout Should Know",
     "task": "Whip the end of the rope with the twine, so it cannot fray.", "verb": "WHIP THE ROPE'S END",
     "objects": ["rope", "twine"], "places": ["study", "garden"], "weather_gate": None,
     "craft": "whip_end", "deed_keys": None, "hand_ready": True,
     # J-2335 (D-0454): the hand (fieldcraft.whip_end) needs BOTH of these at his own place at once.
     "colocate": ["rope", "twine"],
     "book_quote": "“Lay the end of a piece of twine along the end of the rope. Hold it to the rope with the "
                    "thumb of your left hand while you wind the standing part around it and the rope until the "
                    "end of the twine has been covered… The end is then pulled back tight and cut off close "
                    "to the rope.” — Boy Scouts Handbook (1911), p.49."},
    {"id": "gather_tinder", "rung": 1, "chapter": "Fire by Rubbing Sticks",
     "task": "Go out and gather dry tinder for the tin.", "verb": "GATHER TINDER",
     "objects": ["tinder_tin"], "places": ["wood", "shore", "garden"], "weather_gate": "dry",
     "craft": None, "deed_keys": {"tinder"}, "hand_ready": True,
     "book_quote": "“The true woodcrafter limits himself to the things that he can get in the woods, and in "
                    "all my recent fire-making I have contented myself with the tinder used for ages by the red "
                    "men: that is, cedar wood finely shredded between two stones.” — Boy Scouts Handbook "
                    "(1911), p.73."},
    {"id": "flint_and_steel", "rung": 1, "chapter": "How to Make Fire by Rubbing Sticks",
     "task": "Strike flint and steel to the tinder and raise a fire without a match.", "verb": "STRIKE THE FLINT",
     "objects": ["flint", "tinder_tin"], "places": ["study"], "weather_gate": None,
     "craft": "fire_lay", "deed_keys": {"flint_fire"}, "fire_lay_exclusive": True, "hand_ready": True,
     "book_quote": "“The Indians use a flint and steel, as our own fathers and mothers did one hundred years "
                    "ago, and before they had flint and steel they used rubbing-sticks.” — Boy Scouts "
                    "Handbook (1911), p.71."},
    {"id": "bank_the_fire", "rung": 1, "chapter": "Camp Fire",
     "task": "Bank the fire under a good bed of ash for the night.", "verb": "BANK THE FIRE",
     "objects": [], "places": ["study"], "weather_gate": None,
     "craft": "fire_lay", "deed_keys": {"bank_fire"}, "hand_ready": True,
     # No literal "banking embers under ash" passage was found in the shelf copy (searched: fire-safety,
     # rubbing-sticks, over-night-camp sections) — honestly not a quote; the in-universe framing
     # fieldcraft.bank_fire() itself already uses ("the way the book has it"), not dressed up as one.
     "book_quote": "Not a page-cited quote (none found on the shelf for this one) — the Handbook's own "
                    "way, as fieldcraft.py already tells it: rake the embers together, lay a log across them, "
                    "and cover the whole with a blanket of ash; in the morning the fire stands up again "
                    "without a match."},
    {"id": "read_a_trail", "rung": 1, "chapter": "Tracks, Trailing and Signaling",
     "task": "Find a trail and read it to its end.", "verb": "FOLLOW THE TRAIL",
     "objects": [], "places": ["garden", "wood", "shore"], "weather_gate": None,
     "craft": "tracking", "deed_keys": None, "hand_ready": True,
     "book_quote": "“—the tracks in the dust, mud, or snow. These are the inscriptions that every "
                    "hunter must learn to read infallibly… he must decipher and follow them swiftly, "
                    "unerringly.” — Boy Scouts Handbook (1911), p.187 (Ernest Thompson Seton)."},
    {"id": "whittle_object", "rung": 1, "chapter": "Woodcraft",
     "task": "Whittle something useful with the knife.", "verb": "WHITTLE SOMETHING",
     "objects": ["knife"], "places": ["wood", "garden", "study", "shore"], "weather_gate": None,
     "craft": "whittling", "deed_keys": None, "hand_ready": True,
     "book_quote": "“A boy of ingenuity can make a number of convenient things—a good drinking cup "
                    "from a piece of bark, a pot lifter from a green stick, a novel candlestick made by opening "
                    "the blade of a knife and jabbing it into a tree.” — Boy Scouts Handbook (1911), "
                    "p.149."},
    {"id": "douse_a_fire", "rung": 1, "chapter": "Camp Fire",
     "task": "Douse the fire fully, with the water pail or a scoop of sand.", "verb": "DOUSE THE FIRE",
     "objects": [], "places": ["study", "shore"], "weather_gate": None,
     "craft": "douse_fire", "deed_keys": None, "hand_ready": True,
     "book_quote": "“Things to remember: First, it is criminal to leave a burning fire; second, always put "
                    "out the fire with water or earth.” — Boy Scouts Handbook (1911), p.160."},
    # ── rung 2 — hands BUILT 2026-10-28 (J-2483; D-0504 released J-0628's spec, plan §3/§7 step 4) ────
    # Every row below names a real hand in core/fieldcraft.py and matches that hand's own {"deed": ...,
    # "ok": ...} ledger marker through deed_keys (never a bare craft key — lashing, measuring and
    # timber_hitch are each rolled by two hands now). "colocate" lists what the hand itself needs at his
    # own place at once (D-0454's fix, F-3009); the rest of the object presence is checked by id in
    # _gate_ok() below through _RUNG23_GATES.
    {"id": "sheepshank", "rung": 2, "chapter": "Knots Every Scout Should Know",
     "task": "Tie a sheepshank to shorten the line without cutting it.", "verb": "TIE THE SHEEPSHANK",
     "objects": ["twine", "rope"], "places": ["garden", "wood"], "weather_gate": None,
     "craft": "sheepshank", "deed_keys": {"sheepshank"}, "hand_ready": True,
     "book_quote": "“Sheepshank. Used for shortening ropes. Gather up the amount to be shortened, then "
                   "make a half hitch round each of the bends.” — Boy Scouts Handbook (1911), p.50."},
    {"id": "timber_hitch_haul", "rung": 2, "chapter": "Knots Every Scout Should Know",
     "task": "Timber-hitch a length of driftwood with the rope and haul it clear.", "verb": "HAUL THE TIMBER",
     "objects": ["rope"], "places": ["shore"], "weather_gate": None,
     "craft": "timber_hitch", "deed_keys": {"haul_timber"}, "hand_ready": True,
     "book_quote": "“Timber Hitch. Used in hauling timber. Pass the end of the rope around the log…"
                   "” — Boy Scouts Handbook (1911), p.51."},
    {"id": "knife_bearing", "rung": 2, "chapter": "How to Get Your Bearings",
     "task": "Reckon a bearing from the clouded sun with the knife blade stood on the dial.", "verb": "RECKON THE BEARING",
     "objects": ["knife"], "places": ["garden", "wood", "shore"], "weather_gate": "sun",
     "craft": "bearing", "deed_keys": {"knife_bearing"}, "hand_ready": True,
     "book_quote": "“If you cannot see the sun, get into a clear, open space, hold your knife point upright "
                   "on your watch dial, and it will cast a faint shadow, showing where the sun really is, "
                   "unless the clouds are very heavy.” — Boy Scouts Handbook (1911), p.57."},
    {"id": "cook_over_embers", "rung": 2, "chapter": "Cooking Receipts for Scouts",
     "task": "Cook something real over the embers, buried in a bed of coals.", "verb": "COOK OVER THE EMBERS",
     # plan §3 says study/garden; the garden has no fire of its own (nothing there can answer "embers"),
     # the shore has a fire-ring — so the honest places are study/shore (see this build's finding).
     "objects": [], "places": ["study", "shore"], "weather_gate": None,
     "craft": "cooking", "deed_keys": {"cook_over_embers"}, "hand_ready": True,
     "book_quote": "“Wash and dry potatoes thoroughly, bury them deep in a good bed of coals, cover them "
                   "with hot coals until well done. It will take about forty minutes for them to bake.” "
                   "— Boy Scouts Handbook (1911), Cooking Receipts for Scouts."},
    {"id": "wash_up_camp", "rung": 2, "chapter": "Dish Washing",
     "task": "Wash up the camp way: the pan scoured with water boiled in it over the fire, or with sand.", "verb": "SCOUR THE PAN",
     "objects": ["kettle"], "places": ["study", "shore"], "weather_gate": None,
     "craft": "wash_up", "deed_keys": {"wash_up_camp"}, "hand_ready": True,
     "book_quote": "“First fill the frying-pan with water, place over the fire, and let it boil. Pour out "
                   "water and you will find the pan has practically cleaned itself. Clean the griddle with "
                   "sand and water.” — Boy Scouts Handbook (1911), p.152."},
    {"id": "leave_blaze", "rung": 2, "chapter": "Indian Signs and Blazes",
     "task": "Notch a blaze, or set a line of stones, to find your own way back by.", "verb": "NOTCH A BLAZE",
     "objects": ["knife"], "places": ["wood", "shore"], "weather_gate": None,
     "craft": "blazing", "deed_keys": {"leave_blaze"}, "hand_ready": True,
     "book_quote": "The Handbook's Indian Signs and Blazes (p.209) are drawn, not written: a blaze on a "
                   "trunk and a line of stones for 'road to be followed', and 'letter hidden three paces "
                   "from here in the direction of arrow'. A mark is left where it will be seen again."},
    {"id": "pace_distance", "rung": 2, "chapter": "Measuring Distances",
     "task": "Lay a course off with the measuring stick, then pace it at your own known pace.", "verb": "PACE THE DISTANCE",
     "objects": ["measuring_stick"], "places": ["wood", "garden"], "weather_gate": None,
     "craft": "pacing", "deed_keys": {"pace_distance"}, "hand_ready": True,
     "book_quote": "“A man's thumb is an inch wide. Span of thumb and longest finger, nine inches. Brisk "
                   "walking pace is one yard for men.” — Boy Scouts Handbook (1911), p.67."},
    {"id": "sound_lag", "rung": 2, "chapter": "Measuring Distances",
     "task": "Judge a distance by the lag between seeing a thing and hearing it.", "verb": "COUNT THE LAG",
     "objects": [], "places": ["garden", "shore"], "weather_gate": None,
     "craft": "sound_lag", "deed_keys": {"sound_lag"}, "hand_ready": True,
     "book_quote": "“Count the seconds between the sight and the hearing of the sound, and multiply by "
                   "eleven hundred feet, which is the distance sound travels in a second.” — Boy Scouts "
                   "Handbook (1911), p.66."},
    # ── rung 3 — hands BUILT 2026-10-28 (J-2483, plan §7 step 5) ──────────────────────────────────────
    {"id": "splice_rope", "rung": 3, "chapter": "Knots, Splices and Rope Work",
     "task": "Splice the snapped rope with a short splice, and strain the join.", "verb": "SPLICE THE ROPE",
     "objects": ["rope", "twine"], "places": ["garden"], "weather_gate": None,
     "craft": "short_splice", "deed_keys": {"splice_rope"}, "hand_ready": True,
     "book_quote": "“Untwist the ends of the rope for a few inches and seize with twine to prevent further "
                   "unwinding… Now place the two ends of the ropes together… work open the strand, and "
                   "through this pass the strand of the other rope.” — Knots, Splices and Rope Work, "
                   "the Short Splice (Fig. 106)."},
    {"id": "build_tripod", "rung": 3, "chapter": "Camp-Lore — Lashings and Tripods",
     "task": "Square-lash three poles into a tripod that stands under a hung kettle.", "verb": "LASH THE TRIPOD",
     "objects": ["rope", "stakes"], "places": ["garden", "shore"], "weather_gate": None,
     "craft": "lashing", "deed_keys": {"tripod_up"}, "hand_ready": True,
     "book_quote": "“Fig. 319 shows the gin or tripod made by binding the three sticks together.” — The "
                   "Book of Camp-Lore and Woodcraft, Shears, Gins or Tripods."},
    {"id": "friction_fire", "rung": 3, "chapter": "How to Make Fire by Rubbing Sticks",
     "task": "Drill a coal with the bow-drill you whittled, and raise a fire from it.", "verb": "DRILL THE SPINDLE",
     "objects": ["tinder_tin"], "places": ["wood", "study"], "weather_gate": None,
     "craft": "friction_fire", "deed_keys": {"friction_fire"}, "hand_ready": True,
     "book_quote": "“Now draw the bow back and forth with steady, even strokes, its full length… in five or "
                   "six seconds it is giving off a cloud of smoke… Fan this gently with the hand; the smoke "
                   "increases, and in a few seconds you see a glowing coal in the middle of the dust.” — "
                   "Boy Scouts Handbook (1911), p.73."},
    {"id": "triangle_check", "rung": 3, "chapter": "Measuring Distances",
     "task": "Measure a height by the shadow, then check it by the rule of the triangle.", "verb": "SIGHT THE TRIANGLE",
     "objects": ["measuring_stick", "stakes"], "places": ["garden", "wood", "shore"], "weather_gate": None,
     "craft": "measuring", "deed_keys": {"triangle_check"}, "hand_ready": True,
     "book_quote": "“Set up a ten-foot pole. Then mark the spot where the exact line from the top of the "
                   "tree over the top of the pole touches the ground. Now measure the distance from that "
                   "spot to the foot of the ten-foot pole… Measure also the distance from that spot to the "
                   "base of the tree.” — Boy Scouts Handbook (1911), p.65."},
    {"id": "read_weather_glass", "rung": 3, "chapter": "Weather Signs",
     "task": "Consult the weather glass, or the tide board, and say what tomorrow will bring.", "verb": "CONSULT THE WEATHER GLASS",
     "objects": ["weather_glass", "tide_board"], "places": ["study", "shore"], "weather_gate": None,
     "craft": "weather_reading", "deed_keys": {"read_weather_glass"}, "hand_ready": True,
     "book_quote": "“The evening red, the morning gray / Sets the traveler on his way; / The evening gray, "
                   "the morning red / Brings down showers upon his head.” … “East wind brings rain. West "
                   "wind brings clear, bright, and cool weather.” — Boy Scouts Handbook (1911), pp.156-157."},
]
_BY_ID = {t["id"]: t for t in LADDER}
_WET_WEATHER = ("drizzle", "steady rain", "wind and rain", "thunderstorm")   # matches fieldcraft.gather_tinder


# ── state ──────────────────────────────────────────────────────────────────────────────────────────
def _load_state() -> dict:
    try:
        return json.loads(_STATE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_state(d: dict) -> None:
    try:
        _DATA.mkdir(parents=True, exist_ok=True)
        _STATE.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def _log_row(rec: dict) -> None:
    try:
        _DATA.mkdir(parents=True, exist_ok=True)
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": round(time.time(), 1), **rec}, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _today_key(now: float | None = None) -> str:
    return time.strftime("%Y-%m-%d", time.localtime(now))


def _roll_day(d: dict, today: str) -> dict:
    """Reset every day-scoped field together when the day has turned over. `rung`, `window` and
    `book_offered` are NOT day-scoped (they persist across days by design) — only which slot we are on
    today and today's announced task reset."""
    if d.get("day") != today:
        if (CARRY_GRADE_ACROSS_DAYS and d.get("task_id") in _BY_ID and d.get("announced_ts")
                and d.get("graded_day") != d.get("day") and not d.get("carry")):
            d["carry"] = {"day": d.get("day"), "task_id": d["task_id"], "announced_ts": d["announced_ts"]}
            _save_state(d | {"day": today, "slot_fired": 0, "task_id": None, "announced_ts": None})
        d["day"] = today
        d["slot_fired"] = 0
        d["task_id"] = None
        d["announced_ts"] = None
    return d


def slot_today(now: float | None = None) -> int:
    """1 while today's observation slot has not fired yet; 2 once it has (today's practical slot is
    up). Persisted (survives a restart mid-morning, unlike the monologue's own in-memory cooldown) so a
    restart never re-runs the day's observation a second time, nor loses its place. Never reports past
    2 — a stray extra same-day fire (timing jitter around a restart) stays a practical, it does not
    revert to observation."""
    d = _roll_day(_load_state(), _today_key(now))
    return 2 if int(d.get("slot_fired", 0)) >= 1 else 1


def practical_first_phase(now: float | None = None) -> str:
    """Only meaningful when PRACTICAL_FIRST. 'practical' on the period's first firing (slot_fired 0), 'observation'
    on the next one (slot_fired 1), 'practical' again for any stray extra same-day fire (never a second observation)."""
    d = _roll_day(_load_state(), _today_key(now))
    return "observation" if int(d.get("slot_fired", 0)) == 1 else "practical"


def announce(now: float | None = None) -> dict | None:
    """Announce today's practical without grading it: picks and persists the task and logs the 'issued' row
    (via _current_task). Zero LLM; grading is period_end_grade()'s."""
    return _current_task(now)


def mark_slot_fired(now: float | None = None) -> None:
    """Call exactly once per actual nature-block firing (observation OR practical) — advances today's
    counter so the NEXT firing (and every directive() call in between) sees the other slot."""
    d = _roll_day(_load_state(), _today_key(now))
    d["slot_fired"] = int(d.get("slot_fired", 0)) + 1
    _save_state(d)


# ── the picker ─────────────────────────────────────────────────────────────────────────────────────
def _fc_state() -> dict:
    from core import fieldcraft as _fc
    return _fc._load()


def _weather_wet() -> bool:
    try:
        from core import sensorium as _s
        return _s.state.get("weather", "") in _WET_WEATHER
    except Exception:
        return False


def _item_loc(key: str) -> dict:
    """{"carried": bool, "place": str|None} for a placed world object, from the store that owns it
    (garden items first — twine, stakes — then study_life items — rope, coat, ...). Unknown -> both empty."""
    from core import garden as _g, study_life as _sl
    it = (_g._load().get("items") or {}).get(key)
    if it is None:
        it = (_sl._st().get("items") or {}).get(key)
    it = it or {}
    return {"carried": bool(it.get("carried")), "place": it.get("place")}


def _colocatable(keys) -> bool:
    """The hand's own co-location test, made walk-reachable: every object is carried or lying somewhere,
    and all the NON-carried ones lie in the SAME place (carried ones travel with him to it). A carried
    item's own "place" field is stale (study_life/garden leave it unchanged on pick-up), so it is not
    compared."""
    locs = [_item_loc(k) for k in keys]
    placed = set()
    for loc in locs:
        if loc["carried"]:
            continue
        if not loc["place"]:
            return False
        placed.add(loc["place"])
    return len(placed) <= 1


def _object_rooms(keys) -> dict:
    """For the issued row: where each of the task's objects is at announcement ("carried", a place, or
    None when the object is not a placed item — knife, flint and tinder are study-state flags)."""
    out = {}
    for k in keys or ():
        try:
            loc = _item_loc(k)
            out[k] = "carried" if loc["carried"] else loc["place"]
        except profile.NonLiveWriteError:
            raise
        except Exception:
            out[k] = None
    return out


# ── PRACTICAL SCHOOL rungs 2-3 gates (2026-10-28, J-2483, D-0504) ─────────────────────────────────
# One small presence test per new ladder row, each mirroring what its own hand in core/fieldcraft.py
# tests (D-0454's rule, F-3009: a hand is offered only when the world can answer it). Walk-reachable,
# like _colocatable(): an object lying anywhere counts, since the nature period lets him go to it. None
# of these reads anything but the stores the hands themselves read; none adds a word to the directive.
def _placed_any(keys) -> bool:
    for k in keys:
        loc = _item_loc(k)
        if loc["carried"] or loc["place"]:
            return True
    return False


def _rope_available() -> bool:
    from core import study_life as _sl
    return float(_sl._st().get("rope_m", 0) or 0) > 0 and _placed_any(["rope"])


def _gate_knife() -> bool:
    from core import study_life as _sl
    return bool(_sl._st().get("knife"))


def _gate_cook() -> bool:
    from core import fieldcraft as _fc, sensorium as _s
    coals = _s.state.get("fire", "out") in ("burning", "embers") or _fc._shore_fire_state() in ("burning", "embers")
    return bool(coals) and _fc.cook_food_available() is not None


def _gate_wash() -> bool:
    from core import fieldcraft as _fc, study_life as _sl
    st = _sl._st()
    return bool(_fc._load().get("pan_greasy")) or int(st.get("dirty_cups", 0) or 0) > 0 or bool(st.get("dirty_pot"))


def _gate_stick() -> bool:
    from core import fieldcraft as _fc
    return _fc.has_measuring_stick()


def _gate_tripod() -> bool:
    """The hand's own two routes, co-located the way _colocatable() reads them (D-0504's defeater: never
    offered while its objects sit in different rooms): the garden wants the rope AND the stakes at one
    place (or carried there); the shore wants only the rope, the driftwood being the poles — so the rope
    lying on the shore, or in hand, is enough on its own."""
    from core import fieldcraft as _fc
    if not _rope_available() or _fc.tripod_standing():
        return False
    rope = _item_loc("rope")
    return _colocatable(["rope", "stakes"]) or bool(rope["carried"]) or rope["place"] == "shore"


def _gate_friction() -> bool:
    from core import fieldcraft as _fc
    d = _fc._load()
    return _fc.has_fire_drill_kit(d) and float(d.get("tinder", 0)) >= 0.1


def _gate_triangle() -> bool:
    from core import fieldcraft as _fc
    d = _fc._load()
    return _fc.has_measuring_stick(d) and (_placed_any(["stakes"]) or _fc._made_thing(d, "a peg") is not None)


_RUNG23_GATES = {
    "sheepshank": lambda: _placed_any(["twine", "rope"]),
    "timber_hitch_haul": _rope_available,
    "knife_bearing": _gate_knife,            # the sun is the weather_gate "sun" below
    "cook_over_embers": _gate_cook,
    "wash_up_camp": _gate_wash,
    "leave_blaze": lambda: True,             # the shore's stones need nothing; the wood wants the knife, and he chooses where
    "pace_distance": _gate_stick,
    "sound_lag": lambda: True,               # the surf on the reef is always there from the shore
    "splice_rope": _rope_available,
    "build_tripod": _gate_tripod,
    "friction_fire": _gate_friction,
    "triangle_check": _gate_triangle,
    "read_weather_glass": lambda: True,      # the glass is on the wall, the board at the waterline
}


def _sun_readable() -> bool:
    """weather_gate 'sun' (knife_bearing): the sun up and the cloud not so heavy the blade throws no
    shadow at all — the hand's own two refusals."""
    from core import sensorium as _s, world_clock as _wc
    return bool(_wc.sun().get("up")) and _s.state.get("weather", "") not in ("steady rain", "wind and rain", "thunderstorm")


def _gate_ok(task: dict) -> bool:
    """Objects/precondition gate, per task id — each engine's own presence check is genuinely
    different (twine vs rope vs knife vs flint+tin vs an active fire), so this is a small dispatch by
    id rather than one generic rule. NOT gated on his current standing location: the nature period is
    explicitly exempt from the study-confinement rule (core/school.py's _STUDY_BOUND_SUBJECTS), so he
    is free to walk to wherever the directive names within the period — filtering candidates by
    wherever he happens to be standing the instant the period opens (usually the study, inherited from
    the prior desk period) would strand the outdoor tasks and defeat the ladder's own breadth."""
    tid = task["id"]
    if task.get("weather_gate") == "dry" and _weather_wet():
        return False
    try:
        if task.get("weather_gate") == "sun" and not _sun_readable():
            # J-2483: knife_bearing's own sun/cloud refusals, so it is never offered on a day it cannot fire
            return False
        if tid in _RUNG23_GATES:
            # J-2483 (D-0504): rung 2-3 rows gate by their own hand's presence test (see _RUNG23_GATES);
            # a row that also declares "colocate" is checked for that first, like every other row.
            if task.get("colocate") and not _colocatable(task["colocate"]):
                return False
            return bool(_RUNG23_GATES[tid]())
        if tid in ("clove_hitch_stake", "bowline_loop"):
            from core import garden as _g
            it = _g._load().get("items", {}).get("twine", {})
            has_twine = bool(it.get("carried")) or bool(it.get("place"))
            d = _fc_state()
            return has_twine and (not d.get("clothesline") or not d.get("handrail"))
        if task.get("colocate") and not _colocatable(task["colocate"]):
            # J-2315 / J-2335 (F-3009, D-0454): a deed whose hand needs two or more objects at his own
            # place at once (fieldcraft.whip_end's rope_here + _has_twine test) is offered only when they
            # can meet in one room. No fetch wording is added anywhere — the world answers, it never leads.
            return False
        if tid == "whip_rope_end":
            from core import study_life as _sl
            return float(_sl._st().get("rope_m", 0) or 0) > 0
        if tid == "flint_and_steel":
            from core import study_life as _sl
            st = _sl._st()
            return bool(st.get("flint")) and bool(st.get("tinder_tin"))
        if tid == "bank_the_fire":
            from core import sensorium as _s
            return _s.state.get("fire", "out") != "out"
        if tid == "whittle_object":
            from core import study_life as _sl
            return bool(_sl._st().get("knife"))
        if tid == "douse_a_fire":
            from core import sensorium as _s
            return _s.state.get("fire", "out") != "out"
    except profile.NonLiveWriteError:
        # J-0768 (F-1102): garden._load()'s and study_life._st()'s own self-healing bootstrap-save
        # paths raise D-0179's hard-raise (guard_path()) on a non-live process -- let it reach this
        # function's own caller instead of being swallowed by the broader except below, matching
        # J-0714/J-0726/J-0727's identical fix shape at every other layer of this fence.
        raise
    except Exception:
        return True
    return True   # gather_tinder (weather-only, handled above) and read_a_trail have no object gate


def _eligible(rung: int) -> list[dict]:
    return [t for t in LADDER if t["rung"] <= rung and t.get("hand_ready") and _gate_ok(t)]


def _pick(rung: int) -> dict | None:
    cand = _eligible(rung)
    return random.choice(cand) if cand else None


def _render(task: dict) -> tuple[str, str]:
    """(sentence, verb_phrase) for the directive. clove_hitch_stake/bowline_loop have no standalone
    hand of their own (out of this job's scope — see the finding); both only fire through the existing
    composite structures, so both are rendered as whichever of those is still unbuilt. _gate_ok()
    already guarantees at least one is, whenever either of these two ids is offered."""
    if task["id"] in ("clove_hitch_stake", "bowline_loop"):
        try:
            d = _fc_state()
            if not d.get("clothesline"):
                return ("String the twine into a clothesline, between the tree and the fence-post, tied off "
                        "with a clove hitch and a bowline.", "STRING THE CLOTHESLINE")
            return ("Run the twine as a handrail down the steep path, tree to tree, tied off with a clove "
                    "hitch and a bowline.", "RIG THE HANDRAIL")
        except Exception:
            pass
        return ("String the twine into a clothesline, between the tree and the fence-post, tied off with a "
                "clove hitch and a bowline.", "STRING THE CLOTHESLINE")
    return (task.get("task", ""), task.get("verb", ""))


def _current_task(now: float | None = None) -> dict | None:
    """Get (or, the first time today's practical slot is up, pick and persist) today's announced task.
    Both directive() and run() call this so they always agree on what today's practical is."""
    d = _roll_day(_load_state(), _today_key(now))
    if d.get("task_id") and d["task_id"] in _BY_ID:
        return _BY_ID[d["task_id"]]
    task = _pick(int(d.get("rung", 1)))
    if not task:
        return None
    d["task_id"] = task["id"]; d["announced_ts"] = time.time()
    _save_state(d)
    # J-2315 (F-3009): D-0159 criterion 1 counts days the directive was ISSUED, so log issuance itself
    # (once per day — task_id is persisted above, so this branch is never reached again today). An
    # "event" row, like rung_advance: readers counting graded practicals must skip rows with "event".
    # J-2335 (D-0454): the issued row also carries the deed, the period it was announced in (its end, so
    # a re-read can pair it with that period's attempts and grader row) and where each object was then.
    _rec = {"event": "issued", "kind": "practical", "task": task["id"], "rung": task["rung"],
            "deed": task.get("craft") or "|".join(sorted(task.get("deed_keys") or ())),
            "objects": list(task.get("objects") or [])}
    try:
        _rec["period_end"] = round(_period_end(float(d["announced_ts"])), 1)
    except Exception:
        _rec["period_end"] = None
    _rec["rooms"] = _object_rooms(_rec["objects"])
    _log_row(_rec)
    return task


def directive() -> str:
    """The high-priority seed for the second nature slot — same fixed diegetic form the other school
    subjects use. Caller (core/school.py) only reaches this once slot_today() >= 2; called again here
    defensively so a direct call is still honest rather than silently wrong."""
    if slot_today() < 2 and not PRACTICAL_FIRST:
        try:
            from core import nature_study
            return nature_study.directive()
        except Exception:
            return ""
    task = _current_task()
    if not task:
        return ("It is your nature practical now, but nothing in the Handbook's ladder is within reach — "
                "the objects for it are not here, or the weather is against it. To begin, make your thought: "
                "GO AND OBSERVE.")
    sentence, verb = _render(task)
    return (f"It is your nature practical now. From the Handbook's chapter on {task['chapter']}: {sentence} "
            f"To begin, make your thought: {verb}.")


# ── grading: the world's own answer ───────────────────────────────────────────────────────────────
def _ledger_since(ts: float) -> list[dict]:
    try:
        from core.shadow_log import tail_rows
        return [r for r in tail_rows(_FC_LEDGER, _LEDGER_TAIL) if float(r.get("ts", 0)) >= ts]
    except Exception:
        return []


def _outcome_from_rows(task: dict, rows: list[dict]) -> tuple[bool, bool | None]:
    """(attempted, ok) — best across every matching row (he may try again in the same period, plan
    §1): True if ANY matching row succeeded, else the LAST matching row's own ok if every one failed.

    fire_lay is a genuine shared craft key in fieldcraft.py (bank_fire AND strike_flint both roll it).
    bank_the_fire always logs its own unconditional deed=='bank_fire' marker regardless of outcome
    (fieldcraft.bank_fire()'s own code), so it matches on that marker alone, never the bare craft row.
    flint_and_steel matches its own deed=='flint_fire' success marker, or — since its two failure
    branches log no deed marker at all — a bare craft=='fire_lay' row, PROVIDED that row's timestamp
    does not coincide with a deed=='bank_fire' row (i.e. it was not actually the other task's attempt).
    This is a disclosed, real limitation of reading an existing shared skill key, not a claim of
    perfect attribution — see this build's own finding."""
    tid = task["id"]
    deed_keys = set(task.get("deed_keys") or ())
    craft = task.get("craft")
    bank_ts = {round(float(r.get("ts", -1)), 1) for r in rows if r.get("deed") == "bank_fire"}
    hits = []
    for r in rows:
        d = r.get("deed")
        if deed_keys and d in deed_keys:
            hits.append(r); continue
        if tid == "flint_and_steel" and r.get("craft") == "fire_lay" and round(float(r.get("ts", -1)), 1) not in bank_ts:
            hits.append(r); continue
        if craft and not deed_keys and tid != "flint_and_steel" and r.get("craft") == craft:
            hits.append(r); continue
    if not hits:
        return False, None
    # a matched row's own "ok" if it carries one (every _try()-produced craft row, and bank_fire's own
    # unconditional deed marker, always do); missing "ok" means a deed-only marker that fieldcraft.py
    # itself only ever logs on the successful branch (gather_tinder's "tinder", strike_flint's
    # "flint_fire") — presence there already IS the world's yes, not an unknown to default False on.
    oks = [bool(h.get("ok", True)) for h in hits]
    if any(oks):
        return True, True
    return True, oks[-1]


def _book_paragraph(task: dict) -> str:
    """The Handbook's own paragraph, offered ONCE, ever, per task — the first time he slips on it
    (plan §1, "the way maths offers the method after a miss"). Returns '' every other time."""
    q = task.get("book_quote") or ""
    if not q:
        return ""
    d = _load_state()
    offered = set(d.get("book_offered") or [])
    if task["id"] in offered:
        return ""
    offered.add(task["id"]); d["book_offered"] = sorted(offered); _save_state(d)
    return q


def _advance_rung(ok: bool) -> None:
    d = _load_state()
    window = list(d.get("window") or []) + [bool(ok)]
    window = window[-RUNG_WINDOW:]
    d["window"] = window
    if len(window) >= RUNG_WINDOW and (sum(window) / len(window)) >= RUNG_THRESHOLD:
        rung = min(MAX_RUNG, int(d.get("rung", 1)) + 1)
        d["rung"] = rung; d["window"] = []
        _log_row({"event": "rung_advance", "rung": rung})
    _save_state(d)


def run(until: float | None = None, trigger: str = "slot2") -> dict:
    """Called once per practical slot (the nature block's 2nd firing that day) from the monologue's
    school block — or, J-2315, by period_end_grade() when that 2nd firing never came. Always logs a
    data/practical_log.jsonl row; returns {} unless the practical was genuinely attempted, so an
    unattempted one earns _record_lesson's thought/joy/feedback exactly never (plan §1: "without
    penalty and without a nudge"). `until` caps the graded ledger rows (the period's own end)."""
    task = _current_task()
    if not task:
        return {}
    if trigger == "slot2" and GRADE_AT_PERIOD_END:
        # J-2335 (D-0454): the 36-minute firing no longer grades — period_end_grade() does, at the end.
        return {}
    try:
        from core import sensorium as _s
        where = _s.state.get("location", "study")
    except Exception:
        where = "study"
    d = _load_state()
    announced = float(d.get("announced_ts") or time.time())
    rows = _ledger_since(announced)
    if until is not None:
        rows = [r for r in rows if float(r.get("ts", 0)) <= until]
    attempted, ok = _outcome_from_rows(task, rows)
    d["graded_day"] = _today_key(); _save_state(d)
    _log_row({"kind": "practical", "rung": task["rung"], "task": task["id"], "attempted": attempted, "ok": ok,
              "craft": task.get("craft") or "|".join(sorted(task.get("deed_keys") or ())),
              "where": where, "objects": task.get("objects") or [], "trigger": trigger})
    if not attempted:
        return {}
    try:
        from core import competence as _comp
        _comp.record_drill_accuracy("fieldcraft", 1.0 if ok else 0.0)
    except Exception:
        pass
    _advance_rung(bool(ok))
    feedback = "" if ok else _book_paragraph(task)
    return {"score": 1.0 if ok else 0.0, "feedback": feedback, "attempted": True, "ok": bool(ok),
            "task": task["id"], "rung": task["rung"]}


def _period_end(ts: float) -> float:
    """End (epoch secs) of the school period that contains `ts` — school.py's own clock arithmetic
    (SCHOOL_START_H + k*SCHOOL_PERIOD_MIN), capped at SCHOOL_END_H."""
    from core import school as _sch
    lt = time.localtime(ts)
    start = time.mktime((lt.tm_year, lt.tm_mon, lt.tm_mday, int(_sch.SCHOOL_START_H), 0, 0, 0, 0, -1))
    k = max(0, int((ts - start) // (_sch.SCHOOL_PERIOD_MIN * 60)))
    end = start + (k + 1) * _sch.SCHOOL_PERIOD_MIN * 60
    cap = start + (_sch.SCHOOL_END_H - _sch.SCHOOL_START_H) * 3600
    return min(end, cap)


def _grade_carry(now: float) -> dict:
    """J-4306: grade the prior day's stashed practical once its period has closed. Clears the carry
    either way. Rung/competence effects match run(); the row is tagged trigger='carry_over'."""
    d = _load_state()
    c = d.get("carry")
    if not c:
        return {}
    task = _BY_ID.get(c.get("task_id"))
    try:
        ann = float(c.get("announced_ts") or 0)
        end = _period_end(ann)
    except Exception:
        task = None
    if not task:
        d.pop("carry", None); _save_state(d)
        return {}
    if now < end:
        return {}
    d.pop("carry", None); _save_state(d)
    rows = [r for r in _ledger_since(ann) if float(r.get("ts", 0)) <= end]
    attempted, ok = _outcome_from_rows(task, rows)
    _log_row({"kind": "practical", "rung": task["rung"], "task": task["id"], "attempted": attempted, "ok": ok,
              "craft": task.get("craft") or "|".join(sorted(task.get("deed_keys") or ())),
              "where": "carry", "objects": task.get("objects") or [], "trigger": "carry_over",
              "day": c.get("day")})
    if not attempted:
        return {}
    try:
        from core import competence as _comp
        _comp.record_drill_accuracy("fieldcraft", 1.0 if ok else 0.0)
    except Exception:
        pass
    _advance_rung(bool(ok))
    return {"score": 1.0 if ok else 0.0, "feedback": "" if ok else _book_paragraph(task), "attempted": True,
            "ok": bool(ok), "task": task["id"], "rung": task["rung"]}


def period_end_grade(now: float | None = None) -> dict:
    """J-2315 (F-3009): the catch-up grader. When today's practical was announced (task_id persisted)
    but the nature block's 2nd firing never came (slot_fired still 1 — he slept, shut down, or the
    observation was late) and the period has now closed, grade it ONCE against ledger rows up to the
    period's end. Called on every monologue tick; a cheap no-op otherwise. Never an LLM, never a
    nudge. Limitation: a shutdown spanning midnight still loses that day (_roll_day resets it)."""
    now = time.time() if now is None else now
    if CARRY_GRADE_ACROSS_DAYS:
        d0 = _roll_day(_load_state(), _today_key(now))
        if d0.get("carry"):
            res = _grade_carry(now)
            if res:
                return res
    d = _load_state()
    today = _today_key(now)
    # J-2335: with GRADE_AT_PERIOD_END the 2nd firing (slot_fired 2) defers to here too, so any announced,
    # still-ungraded practical qualifies; graded_day is what makes this once-per-day.
    _min_fired = 1 if GRADE_AT_PERIOD_END else None
    _sf = int(d.get("slot_fired", 0))
    if d.get("day") != today or (_sf < 1 if _min_fired else _sf != 1):
        return {}
    if d.get("task_id") not in _BY_ID or not d.get("announced_ts") or d.get("graded_day") == today:
        return {}
    end = _period_end(float(d["announced_ts"]))
    if now < end:
        return {}
    res = run(until=end, trigger="period_end")
    if _sf == 1:
        mark_slot_fired(now)
    return res


def status() -> dict:
    try:
        d = _load_state()
        return {"rung": d.get("rung", 1), "slot_today": slot_today(), "task_today": d.get("task_id"),
                "window": d.get("window", []), "book_offered": len(d.get("book_offered") or [])}
    except Exception as exc:
        return {"error": repr(exc)[:80]}
