"""
Nascence — THE GARDEN (2026-08-22, docs/plans/garden_upgrade.md; founder: "make the garden the most full
place in his world next… real plants, real schedules… their own world history like driftwood… a heap of
random seeds pre-spawned waiting for spring and the correct weather… items to collect and move").

A plant is a THING with a biography, not a number. Every plant and every garden item is a substrate object
(core/world_substrate: hidden truth / physical state / his observations / his inferences) with a POSITION
(core/world_objects) inside the raised bed or about the garden — the same kind of thing as the driftwood.

REAL SCHEDULES (Aotearoa, a cool coastal garden on a hill; months are NZ seasons):
  stage moves on WARMTH and LIGHT, not the calendar. The soil temperature is derived from the THERMAL
  FIELD at the bed (core/thermal.field_at — sun insolation · wind · rain · season), so the garden lives on the
  same clocks he lives in. Month windows from the catalogue are the species' real sowing/flowering habits
  and gate what CAN happen; the temperature decides whether it DOES.

SEED: a hidden SEED BANK in the soil (random species and counts, minted at first load) germinates when soil
temperature and moisture cross each species' threshold — volunteers he did not sow appear in spring. A SEED
TIN (an item) holds random packets he can find, carry and sow. Sowing a packet needs the soil warm enough;
the world answers honestly when it is not.

ITEMS: tools and containers with biographies and positions. He can TAKE one (it travels with him), PUT it
down where he stands, or move it. They are findable, misplaceable, keepable.

CONSEQUENCE: watering a wet bed harms tender roots; weeds grow with rain × warmth and crowd vigour; slugs
after wet nights eat seedlings and leave trails; birds take seedlings; frost burns the tender; cut herbs
regrow on their own clock; the rain barrel fills with rain and empties when he waters.

WHAT IS NEVER TOLD: causes. He sees the state (holes in a leaf, a silver trail, brown tips after a clear
cold dawn, a plant gone over) and the ledger keeps what he did and saw. Why is his to find.

Zero LLM. Fail-open everywhere. The old scalar bed in sensorium stays as a fallback and is never written by
this module; when this module is healthy, sensorium's bed functions delegate here.
"""
from __future__ import annotations

import json
import logging
import math
import random
import re
import time
from pathlib import Path

from core import profile

logger = logging.getLogger("nascence.garden")

_DATA = Path(__file__).parent.parent / "data"
_F = _DATA / "garden.json"
_LEDGER = _DATA / "garden_ledger.jsonl"       # his deeds + what he saw (psyche side)
_EVENTS = _DATA / "garden_events.jsonl"       # what the world did (truth side; HUD/instruments)

ENABLED = True
MONTHS = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}

# ── THE CATALOGUE — real plants, real habits (NZ months) ─────────────────────────────────────────
# life: evergreen | herbaceous (dies back, crown returns) | annual | biennial
# sow: months a seed may be sown outdoors · t_germ: soil °C needed to germinate · days_up: to first true
# leaves · days_mature: to first harvest/flower from germination · flower/seed: months · tender: frost kills
# cut_regrow_days: days for a cut herb to fill back · height_cm at maturity
CATALOGUE: dict[str, dict] = {
    "rosemary":   {"kind": "herb", "life": "evergreen", "sow": (), "t_germ": 15, "days_up": 21, "days_mature": 365,
                   "flower": (7, 8, 9, 10), "seed": (11, 12), "tender": False, "cut_regrow_days": 40, "height": 90,
                   "names": ("the rosemary bush",)},
    "thyme":      {"kind": "herb", "life": "evergreen", "sow": (9, 10, 11), "t_germ": 15, "days_up": 21, "days_mature": 120,
                   "flower": (11, 12, 1), "seed": (1, 2), "tender": False, "cut_regrow_days": 30, "height": 25,
                   "names": ("the thyme", "the low mat of thyme")},
    "mint":       {"kind": "herb", "life": "herbaceous", "sow": (), "t_germ": 12, "days_up": 14, "days_mature": 60,
                   "flower": (1, 2), "seed": (2, 3), "tender": False, "cut_regrow_days": 18, "height": 50,
                   "dormant": (5, 6, 7), "returns": (8, 9), "names": ("the mint",)},
    "parsley":    {"kind": "herb", "life": "biennial", "sow": (9, 10, 11, 2, 3), "t_germ": 10, "days_up": 28, "days_mature": 75,
                   "flower": (11, 12), "seed": (1, 2), "tender": False, "cut_regrow_days": 21, "height": 40,
                   "names": ("the parsley",)},
    "chives":     {"kind": "herb", "life": "herbaceous", "sow": (9, 10), "t_germ": 12, "days_up": 14, "days_mature": 60,
                   "flower": (10, 11), "seed": (12, 1), "tender": False, "cut_regrow_days": 14, "height": 30,
                   "dormant": (6, 7), "returns": (8, 9), "names": ("the chives",)},
    "radish":     {"kind": "veg", "life": "annual", "sow": (8, 9, 10, 11, 12, 1, 2, 3, 4), "t_germ": 8, "days_up": 7, "days_mature": 28,
                   "flower": (), "seed": (), "tender": False, "cut_regrow_days": 0, "height": 15,
                   "names": ("the radishes",)},
    "lettuce":    {"kind": "veg", "life": "annual", "sow": (9, 10, 11, 12, 1, 2, 3), "t_germ": 8, "days_up": 10, "days_mature": 50,
                   "flower": (), "seed": (), "tender": True, "bolts_above": 25, "cut_regrow_days": 10, "height": 20,
                   "names": ("the lettuces",)},
    "silverbeet": {"kind": "veg", "life": "biennial", "sow": (8, 9, 10, 11, 12, 1, 2, 3), "t_germ": 10, "days_up": 10, "days_mature": 55,
                   "flower": (10, 11), "seed": (12, 1), "tender": False, "cut_regrow_days": 14, "height": 45,
                   "names": ("the silverbeet",)},
    "peas":       {"kind": "veg", "life": "annual", "sow": (8, 9, 10, 3, 4), "t_germ": 7, "days_up": 10, "days_mature": 65,
                   "flower": (), "seed": (), "tender": False, "cut_regrow_days": 0, "height": 80, "needs_stake": True,
                   "names": ("the peas",)},
    "broad_beans": {"kind": "veg", "life": "annual", "sow": (4, 5, 6, 7, 8), "t_germ": 6, "days_up": 14, "days_mature": 110,
                   "flower": (8, 9, 10), "seed": (11, 12), "tender": False, "cut_regrow_days": 0, "height": 100, "needs_stake": True,
                   "needs_bees": True, "names": ("the broad beans",)},
    "tomatoes":   {"kind": "veg", "life": "annual", "sow": (10, 11), "t_germ": 16, "days_up": 10, "days_mature": 80,
                   "flower": (12, 1), "seed": (2, 3), "tender": True, "cut_regrow_days": 0, "height": 120, "needs_stake": True,
                   "needs_bees": True, "names": ("the tomato plants",)},
    "beans":      {"kind": "veg", "life": "annual", "sow": (10, 11, 12), "t_germ": 15, "days_up": 8, "days_mature": 60,
                   "flower": (12, 1), "seed": (2, 3), "tender": True, "cut_regrow_days": 0, "height": 50,
                   "names": ("the dwarf beans",)},
    "potatoes":   {"kind": "veg", "life": "annual", "sow": (8, 9, 10), "t_germ": 8, "days_up": 21, "days_mature": 100,
                   "flower": (11, 12), "seed": (), "tender": True, "cut_regrow_days": 0, "height": 60,
                   "names": ("the potatoes",)},
    "garlic":     {"kind": "veg", "life": "annual", "sow": (6, 7, 8), "t_germ": 5, "days_up": 14, "days_mature": 170,
                   "flower": (), "seed": (), "tender": False, "cut_regrow_days": 0, "height": 60,
                   "names": ("the garlic",)},
    "strawberries": {"kind": "fruit", "life": "herbaceous", "sow": (), "t_germ": 15, "days_up": 21, "days_mature": 90,
                   "flower": (9, 10), "seed": (11, 12), "tender": False, "cut_regrow_days": 0, "height": 20,
                   "dormant": (6, 7), "returns": (8,), "needs_bees": True, "names": ("the strawberry plants",)},
    "sunflowers": {"kind": "flower", "life": "annual", "sow": (10, 11, 12), "t_germ": 13, "days_up": 8, "days_mature": 75,
                   "flower": (1, 2), "seed": (3,), "tender": True, "cut_regrow_days": 0, "height": 200,
                   "needs_bees": True, "names": ("the sunflowers",)},
    "calendula":  {"kind": "flower", "life": "annual", "sow": (3, 4, 8, 9, 10), "t_germ": 10, "days_up": 10, "days_mature": 50,
                   "flower": (6, 7, 8, 9, 10, 11, 12), "seed": (11, 12, 1), "tender": False, "cut_regrow_days": 0, "height": 45,
                   "self_seeds": True, "needs_bees": True, "names": ("the calendula", "the orange marigolds")},
    "nasturtium": {"kind": "flower", "life": "annual", "sow": (9, 10, 11), "t_germ": 12, "days_up": 10, "days_mature": 45,
                   "flower": (11, 12, 1, 2, 3), "seed": (2, 3, 4), "tender": True, "cut_regrow_days": 0, "height": 30,
                   "self_seeds": True, "needs_bees": True, "names": ("the nasturtiums",)},
    "poppies":    {"kind": "flower", "life": "annual", "sow": (3, 4, 8, 9), "t_germ": 10, "days_up": 12, "days_mature": 70,
                   "flower": (10, 11, 12), "seed": (12, 1), "tender": False, "cut_regrow_days": 0, "height": 60,
                   "self_seeds": True, "needs_bees": True, "names": ("the poppies",)},
    # NEW PLANTS (2026-09-03, J-0506, the Living Garden): the hosts the insects were waiting for, and what he already
    # believes in. They reach him the way every seed does — the tin, the carrier's unlabelled packet, the bank — never told.
    "lavender":   {"kind": "herb", "life": "evergreen", "sow": (9, 10), "t_germ": 15, "days_up": 21, "days_mature": 120,
                   "flower": (11, 12, 1, 2), "seed": (2, 3), "tender": False, "cut_regrow_days": 30, "height": 60,
                   "needs_bees": True, "names": ("the lavender",)},
    "swan_plant": {"kind": "flower", "life": "annual", "sow": (9, 10, 11), "t_germ": 18, "days_up": 14, "days_mature": 60,
                   "flower": (12, 1, 2), "seed": (2, 3, 4), "tender": True, "cut_regrow_days": 0, "height": 120,
                   "self_seeds": True, "needs_bees": True, "names": ("the swan plant",)},
    "cabbage":    {"kind": "veg", "life": "annual", "sow": (2, 3, 8, 9), "t_germ": 8, "days_up": 10, "days_mature": 90,
                   "flower": (), "seed": (), "tender": False, "cut_regrow_days": 0, "height": 40,
                   "names": ("the cabbages",)},
    "kale":       {"kind": "veg", "life": "annual", "sow": (2, 3, 4, 8, 9), "t_germ": 7, "days_up": 8, "days_mature": 70,
                   "flower": (9, 10), "seed": (11,), "tender": False, "cut_regrow_days": 14, "height": 50,
                   "names": ("the kale",)},
    "nettle":     {"kind": "herb", "life": "herbaceous", "sow": (8, 9, 10, 3), "t_germ": 8, "days_up": 10, "days_mature": 45,
                   "flower": (11, 12, 1), "seed": (1, 2), "tender": False, "cut_regrow_days": 20, "height": 70,
                   "self_seeds": True, "dormant": (6, 7), "returns": (8,), "names": ("the nettles",)},
    "muehlenbeckia": {"kind": "shrub", "life": "evergreen", "sow": (9, 10), "t_germ": 14, "days_up": 28, "days_mature": 180,
                   "flower": (11, 12, 1), "seed": (2, 3), "tender": False, "cut_regrow_days": 40, "height": 100,
                   "names": ("the pōhuehue", "the wire vine")},
    "kumara":     {"kind": "veg", "life": "annual", "sow": (10, 11), "t_germ": 18, "days_up": 14, "days_mature": 120,
                   "flower": (), "seed": (), "tender": True, "cut_regrow_days": 0, "height": 30,
                   "names": ("the kūmara",)},
    # weeds — real ones, with real habits; they are plants too
    "chickweed":  {"kind": "weed", "life": "annual", "sow": (4, 5, 6, 7, 8, 9), "t_germ": 5, "days_up": 7, "days_mature": 35,
                   "flower": (7, 8, 9, 10), "seed": (8, 9, 10, 11), "tender": False, "cut_regrow_days": 0, "height": 10,
                   "self_seeds": True, "names": ("a mat of chickweed",)},
    "dandelion":  {"kind": "weed", "life": "herbaceous", "sow": (8, 9, 10, 3, 4), "t_germ": 10, "days_up": 10, "days_mature": 50,
                   "flower": (9, 10, 11, 12, 1), "seed": (10, 11, 12, 1, 2), "tender": False, "cut_regrow_days": 0, "height": 25,
                   "self_seeds": True, "names": ("a dandelion",)},
    "oxalis":     {"kind": "weed", "life": "herbaceous", "sow": (), "t_germ": 12, "days_up": 10, "days_mature": 40,
                   "flower": (9, 10, 11), "seed": (), "tender": False, "cut_regrow_days": 0, "height": 12,
                   "dormant": (1, 2, 3), "returns": (4, 5), "names": ("a clump of oxalis",)},
}

STAGES = ("seed", "shoot", "leaf", "established", "flowering", "seeding", "dormant", "dead")

# the raised bed: 3.0 m × 1.2 m centred on garden.json's raised_bed [5.5, 5.5, 0.35] — eight slots
_BED_SLOTS = [[4.3 + 0.45 * (i % 6), 5.05 + 0.45 * (i // 6), 0.35] for i in range(12)]   # 3.0 x 1.2 m, two rows of six
_GROUND_SPOTS = {"by_the_harakeke": [2.4, 10.1, 0.0], "under_the_tree": [8.4, 3.9, 0.0],
                 "along_the_wall": [9.4, 6.5, 0.0], "by_the_doorstep": [2.2, 2.0, 0.0],
                 "by_the_fence": [5.6, 11.2, 0.0], "lawn_edge": [4.0, 7.8, 0.0]}

# ── items: tools and containers with biographies ────────────────────────────────────────────────
_ITEMS = [
    ("trowel", "a hand trowel, its blade worn bright, the wooden handle dark with use", [5.2, 4.8, 0.0],
     "left in the bed by whoever gardened here before; rain and sun have had it for a season"),
    ("hand_fork", "a three-tined hand fork, one tine bent", [5.9, 4.8, 0.0], "bent on a stone long ago"),
    ("watering_can", "a galvanised watering can with a brass rose", [3.6, 2.4, 0.0], "stands by the door; a dent in one side"),
    ("rain_barrel", "the rain barrel at the cottage corner, a tap low on its side", [4.6, 1.4, 0.0],
     "catches the roof's water; fills in rain, empties when he waters"),
    ("seed_tin", "a dented tin with a hinged lid, rattling when shaken", [3.2, 1.8, 0.0],
     "the previous occupant's seed tin — paper packets and twists, some labelled, some not"),
    ("twine", "a ball of garden twine, sun-faded", [3.4, 1.9, 0.0], "half used"),
    ("stakes", "a bundle of bamboo stakes tied with wire", [6.8, 1.6, 0.0], "leaning against the cottage wall"),
    ("pot_1", "a terracotta pot, empty, a white crust of old lime on its rim", [2.6, 2.3, 0.0], "by the doorstep"),
    ("pot_2", "a cracked terracotta pot holding dry soil and a dead stalk", [2.9, 2.3, 0.0], "something grew in it once"),
    ("bucket", "a plastic bucket, blue, a split in the rim", [4.0, 1.7, 0.0], "rainwater in the bottom"),
    ("water_bucket", "a sound oak-hooped bucket, tarred and watertight", [3.9, 2.2, 0.0],
     "kept for hauling water any real distance — unlike the split old one by the wall"),
    ("netting", "a roll of bird netting, tangled", [7.2, 1.5, 0.0], "to keep the birds off seedlings, if untangled"),
    ("bird_bath", "a shallow stone dish on a stump, water in it", [7.6, 8.6, 0.5], "the blackbird's; fills with rain"),
    ("compost_heap", "the compost heap in the corner by the wall, dark and settling under a board", [9.2, 2.2, 0.4],
     "what the garden and the kitchen threw out, rotting down; warm in the middle"),
    # THE TRAP (2026-09-03, D-0130, J-0512): a deed with moral weight. set_trap arms it where he carries it; the
    # world (core/life_mammals.night_pass) may spring it on a possum — or, less often, the hedgehog; check_trap is
    # where he finds out, and a kill goes through core/sitting.note_difficulty like an owned plant death.
    ("possum_trap", "a spring-jawed possum trap, rusted, its plate set with a twist of wire for bait", [9.0, 3.0, 0.0],
     "found hung on a nail in the wall by the tree; whoever was here before had the same trouble"),
    ("shears", "a pair of long-handled grass shears, the blades dull and a little rusted", [6.4, 1.6, 0.0], "hung on a nail by the stakes; nobody has cut the grass in a season"),
]
_CARRYABLE = {"trowel", "hand_fork", "watering_can", "seed_tin", "twine", "stakes", "pot_1", "pot_2", "bucket", "water_bucket", "netting", "shears", "possum_trap"}

_WORDS = {"shears": ("shears",), "compost_heap": ("compost", "heap"), "possum_trap": ("trap", "possum trap"), "trowel": ("trowel",), "hand_fork": ("hand fork", "fork"), "watering_can": ("watering can", "can"),
          # "dented tin" added 2026-09-28 (J-1438): Du's own established word for this object in his
          # real inner monologue (hands_trace.jsonl, dozens of uses since 2026-08-28) -- "tin"/"seed
          # tin" alone would miss the exact phrase he actually reaches for.
          "rain_barrel": ("barrel",), "seed_tin": ("tin", "seed tin", "dented tin", "packets", "packet"), "twine": ("twine", "string"),
          "stakes": ("stake", "stakes", "bamboo"), "pot_1": ("pot",), "pot_2": ("cracked pot", "pot"),
          # the split old bucket now needs a qualifier — bare "bucket" means the sound one (water_bucket) below,
          # since that's the one with a real job; this one is otherwise just a flavour object
          "bucket": ("blue bucket", "plastic bucket", "cracked bucket", "split bucket"),
          "water_bucket": ("bucket", "water bucket", "oak bucket", "the good bucket"),
          "netting": ("netting", "net"), "bird_bath": ("bird bath", "birdbath", "dish")}

# ── state ────────────────────────────────────────────────────────────────────────────────────────
_state: dict | None = None
_last_save = 0.0


def _load() -> dict:
    global _state
    if _state is not None:
        return _state
    try:
        _state = json.loads(_F.read_text(encoding="utf-8"))
    except Exception:
        _state = {}
    if not _state.get("plants"):
        _state = _bootstrap()
        _save(force=True)
    else:
        # ITEM MIGRATION (2026-08-30, J-0422): this was an `elif` hardcoded to the single key
        # "water_bucket", which meant only one migration could ever run and only while that one key
        # was missing. It is now the general diff — every declared item absent from the save is
        # created, on every load — so adding a row to _ITEMS actually reaches an existing save
        # (F-0558: in study_life and wood_life it silently did not).
        try:
            from core import inventory as _inv
            now = time.time()
            rng = random.Random("garden|2026-08-22")
            added = _inv.sync_items(
                _state.setdefault("items", {}), _ITEMS,
                lambda e: {"id": f"garden_item_{e[0]}", "key": e[0], "name": e[1], "pos": e[2],
                           "place": "garden", "bio": e[3], "carried": False,
                           "history": [{"ts": now - rng.randint(100, 400) * 86400, "event": e[3]}]})
            if added:
                logger.debug("[garden] items added by migration: %s", added)
                _save(force=True)
        except profile.NonLiveWriteError:
            # J-0726: this migration-save can attempt a real write on the very first non-live call in
            # a fresh env (any item declared in _ITEMS but missing from the loaded state triggers it)
            # — let D-0179's hard-raise (guard_path(), F-1024) reach _load()'s own caller instead of
            # being swallowed here, before the willed deed that called _load() even runs.
            raise
        except Exception as exc:     # fail-open: a migration must never cost the caller its world
            logger.debug("[garden] item migration skipped (non-fatal): %s", exc)
    return _state


def _save(force: bool = False) -> None:
    global _last_save
    if not force and time.time() - _last_save < 60:
        return
    # J-0610: real data/ only if this process is live; raises before any I/O AND before the throttle
    # stamp below advances if not (D-0179, J-0704) -- otherwise a non-live caller would only be
    # refused on the first hit in any 60s window and silently no-op on the rest.
    path = profile.guard_path(_F)
    _last_save = time.time()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(_state, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)
    except Exception as exc:
        logger.debug("[garden] save failed (non-fatal): %s", exc)


def _log(path: Path, rec: dict) -> None:
    path = profile.guard_path(path)   # J-0610: real data/ only if this process is live; raises before any I/O (and before the activity_memory cross-link below) if not (D-0179, J-0704)
    try:
        if rec.get("deed"):
            try:   # CROSS-LINK (2026-08-22): a deed here is a deed in his activity memory too
                from core import activity_memory as _am
                _am.record(str(rec["deed"]), str(rec.get("species") or rec.get("item") or rec.get("what") or rec.get("thing") or rec.get("tool") or rec.get("text") or ""))
            except Exception:
                pass
        _DATA.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": round(time.time(), 1), **rec}, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _month(t: float | None = None) -> int:
    return time.localtime(t or time.time()).tm_mon


# ── bootstrap: the garden as it stands at the end of winter ──────────────────────────────────────
def _bootstrap() -> dict:
    now = time.time()
    rng = random.Random("garden|2026-08-22")
    # No parallel "carried" list here (CONVERGED 2026-09-02, J-0467/D-0099 onto core/inventory.py's
    # shared contract, whose own docstring already flagged this as the deferred "step after" — every
    # item-bearing module now agrees the per-item `carried` flag IS the truth; inventory.carried()
    # derives the list from it, same as study_life/wood_life always did without a second copy).
    st = {"plants": {}, "items": {}, "seed_bank": [], "packets": [], "barrel": 0.7, "rack": [],
          "soil_temp": 6.0, "moisture": 0.8, "weeds": 0.25, "slugs": 0.3, "_last": now, "born": now,
          "volunteers_seen": [], "frost_last": 0.0}
    day = 86400
    # overwintered perennials — established, with a history (years, frosts, cuts by the one before him)
    peren = [("rosemary", 0, 3 * 365, 0.85), ("thyme", 1, 2 * 365, 0.7), ("mint", 2, 2 * 365, 0.5),
             ("parsley", 3, 200, 0.6), ("chives", 4, 400, 0.5), ("strawberries", 5, 300, 0.55)]
    for sp, slot, age_d, vig in peren:
        cat = CATALOGUE[sp]
        dormant = "dormant" in cat and _month(now) in cat["dormant"]
        stage = "dormant" if dormant else ("flowering" if _month(now) in cat["flower"] and cat["life"] == "evergreen" else "established")
        pid = f"garden_plant_{sp}"
        st["plants"][pid] = {"id": pid, "species": sp, "slot": slot, "pos": _BED_SLOTS[slot], "stage": stage,
                             "vigour": vig, "height": cat["height"] * (0.2 if dormant else 0.8), "moisture": 0.8,
                             "age_days": age_d, "sown_ts": now - age_d * day, "germ_ts": now - (age_d - cat["days_up"]) * day,
                             "stage_ts": now - rng.randint(5, 40) * day, "last_cut_ts": now - rng.randint(60, 200) * day,
                             "cuts": rng.randint(2, 12), "pests": 0.05, "frost_burn": 0.0, "origin": "overwintered",
                             "history": [{"ts": now - age_d * day, "event": "planted_by_previous_gardener"},
                                         {"ts": now - rng.randint(40, 70) * day, "event": "hard_frost_survived"}]}
    # broad beans sown in June by the previous gardener — up, and they will flower in spring
    bb = "garden_plant_broad_beans"
    st["plants"][bb] = {"id": bb, "species": "broad_beans", "slot": 6, "pos": _BED_SLOTS[6], "stage": "leaf", "vigour": 0.6,
                        "height": 35, "moisture": 0.8, "age_days": 70, "sown_ts": now - 70 * day, "germ_ts": now - 56 * day,
                        "stage_ts": now - 30 * day, "last_cut_ts": 0, "cuts": 0, "pests": 0.1, "frost_burn": 0.05,
                        "origin": "sown_by_previous_gardener", "history": [{"ts": now - 70 * day, "event": "sown_in_june"}]}
    # a weed or two already in the bed (winter annuals) and by the wall
    for sp, slot, spot in (("chickweed", 11, None), ("dandelion", None, "along_the_wall"), ("oxalis", None, "by_the_doorstep")):
        pid = f"garden_plant_{sp}_{rng.randrange(16**4):04x}"
        pos = _BED_SLOTS[slot] if slot is not None else _GROUND_SPOTS[spot]
        st["plants"][pid] = {"id": pid, "species": sp, "slot": slot, "pos": pos, "stage": "leaf" if sp != "oxalis" else "established",
                             "vigour": 0.5, "height": 8, "moisture": 0.8, "age_days": 30, "sown_ts": now - 30 * day,
                             "germ_ts": now - 25 * day, "stage_ts": now - 10 * day, "last_cut_ts": 0, "cuts": 0, "pests": 0.0,
                             "frost_burn": 0.0, "origin": "volunteer_from_seed_bank", "history": [{"ts": now - 25 * day, "event": "germinated_unbidden"}]}
    # THE SEED BANK — the heap of random seeds in the soil and the corners, waiting for spring and the weather
    bank_species = ["calendula", "nasturtium", "poppies", "chickweed", "dandelion", "lettuce", "parsley", "radish",
                    "silverbeet", "sunflowers", "thyme", "peas"]
    for _ in range(40):
        sp = rng.choice(bank_species)
        spot = rng.choice(list(_GROUND_SPOTS)) if rng.random() < 0.45 else None
        st["seed_bank"].append({"species": sp, "slot": rng.randrange(12) if spot is None else None, "spot": spot,
                                "viable": round(rng.uniform(0.3, 0.95), 2), "depth": round(rng.uniform(0.2, 3.0), 1)})
    # THE SEED TIN — random packets, some labelled, some twists of paper he will only know by sowing
    for _ in range(rng.randint(8, 12)):
        sp = rng.choice([s for s, c in CATALOGUE.items() if c["sow"] and c["kind"] != "weed"])
        st["packets"].append({"species": sp, "labelled": rng.random() < 0.6, "count": rng.randint(6, 40),
                              "year": rng.choice([2024, 2025, 2025, 2026])})
    # items with positions and biographies
    for key, name, pos, bio in _ITEMS:
        st["items"][key] = {"id": f"garden_item_{key}", "key": key, "name": name, "pos": pos, "place": "garden",
                            "bio": bio, "carried": False, "history": [{"ts": now - rng.randint(100, 400) * day, "event": bio}]}
    st["rack"] = []   # bundles drying by the hearth: {species, cut_ts, dry (0..1)}
    # THE STUDY DRAWER: a second, finite seed store — packets bought once; he must fetch them out to the tin
    for sp in ("lettuce", "radish", "peas", "sunflowers", "beans", "silverbeet"):
        st.setdefault("drawer", []).append({"species": sp, "labelled": True, "count": rng.randint(20, 60), "year": 2026})
    st["netted"] = False
    st["staked"] = []
    st["saved_seed"] = []
    return st


# ── registration in the shared object layers (same kind of thing as the driftwood) ───────────────
def _register_all() -> None:
    """Idempotent: every plant and item exists in world_substrate (biography + observations) and
    world_objects (position + movement history). Plants' hidden truth = species + origin + age."""
    try:
        from core import world_substrate as _ws, world_objects as _wo
        st = _load()
        objs = _ws._load()
        changed = False
        for p in st["plants"].values():
            if p["id"] not in objs:
                cat = CATALOGUE[p["species"]]
                objs[p["id"]] = _ws.SubstrateObject(
                    object_id=p["id"], name=cat["names"][0], location="garden", object_class="plant",
                    causal_state={"species_ground_truth": p["species"], "origin": p["origin"], "sown_ts": p["sown_ts"],
                                  "kind": cat["kind"], "life": cat["life"]},
                    physical_state={"height_cm": round(p["height"], 1), "vigour": p["vigour"], "moisture": p["moisture"]},
                    causal_history=[{"event_type": h["event"], "timestamp": h["ts"], "description": h["event"].replace("_", " "),
                                     "state_deltas": {}} for h in p["history"]])
                changed = True
            _wo.ensure_record(p["id"], "garden", "plant", CATALOGUE[p["species"]]["names"][0])
            _place(p["id"], p["pos"], "garden", "rooted here", quiet=True)
        for it in st["items"].values():
            if it["id"] not in objs:
                objs[it["id"]] = _ws.SubstrateObject(
                    object_id=it["id"], name=it["name"], location=it["place"], object_class="garden_item",
                    causal_state={"kind": it["key"], "bio": it["bio"]},
                    physical_state={"wear": 0.5, "wet": 0.2},
                    causal_history=[{"event_type": "history", "timestamp": h["ts"], "description": h["event"], "state_deltas": {}}
                                    for h in it["history"]])
                changed = True
            _wo.ensure_record(it["id"], it["place"], "garden_item", it["name"])
            _place(it["id"], it["pos"], it["place"], "where it was left", quiet=True)
        if changed:
            _ws._save()
    except profile.NonLiveWriteError:
        # J-0726: this runs on EVERY act_from_thought() dispatch (act_from_thought() calls
        # _register_all() unconditionally as its own second statement, and sow() calls it too) — let
        # D-0179's hard-raise (guard_path(), F-1024) reach the caller instead of being swallowed here,
        # before act_from_thought() even reaches the willed deed.
        raise
    except Exception as exc:
        logger.debug("[garden] register failed (non-fatal): %s", exc)


def _place(oid: str, pos: list, place: str, why: str, quiet: bool = False) -> None:
    try:
        from core import world_objects as _wo
        cur = _wo.get_object(oid) or {}
        if cur.get("position") == list(pos) and cur.get("location") == place:
            return
        _wo.mutate_object_position(oid, list(pos), cause="garden_placement" if quiet else "Du_agent_mutation",
                                   event_description=why, new_location=place)
    except Exception:
        pass


# ── the world's clocks ───────────────────────────────────────────────────────────────────────────
def _soil_temp_c(now: float) -> float:
    """Soil temperature from the THERMAL FIELD at the bed (the same field he stands in), smoothed: soil lags
    air by hours. warmth 0..1 -> about -3..24 °C. Honest about its crudeness; it is one clock for all."""
    try:
        from core import thermal as _th, sensorium as _s
        w = _th.field_at("garden", "at_the_bed", _s._daylight(), _s.state.get("weather", ""), _s._season(),
                         "out", _s.state.get("wind", ""), 0.0, now)
        air = -3.0 + 27.0 * w
    except Exception:
        air = 8.0
    st = _load()
    soil = float(st.get("soil_temp", air))
    return soil + (air - soil) * 0.08       # per tick (~5s..min): slow approach


def advance(now: float, dt: float) -> None:
    """Called from sensorium.tick. Everything that grows, rots, fills or eats does so here, on real time."""
    if not ENABLED:
        return
    try:
        st = _load()
        last = float(st.get("_last") or now)
        dt = max(0.0, min(dt, now - last)) if last else dt
        st["_last"] = now
        if dt <= 0:
            return
        days = dt / 86400.0
        from core import sensorium as _s
        weather = _s.state.get("weather", "") or ""
        raining = weather in ("drizzle", "steady rain", "wind and rain", "thunderstorm")
        phase = _s._daylight()
        month = _month(now)
        temp = _soil_temp_c(now)
        st["soil_temp"] = round(temp, 2)
        # moisture: rain refills, sun/wind/warmth dry
        m = float(st.get("moisture", 0.7))
        if raining:
            m = min(1.0, m + days * (0.5 if "rain" in weather else 0.25))
            st["barrel"] = min(1.0, float(st.get("barrel", 0)) + days * 0.8)
        else:
            evap = 0.08 + max(0.0, temp - 8) * 0.008 + (0.05 if "wind" in weather else 0.0)
            m = max(0.0, m - days * evap)
        st["moisture"] = round(m, 3)
        # frost: a clear cold dawn
        frost = (phase == "dawn" and temp <= 1.0 and weather == "clear" and now - float(st.get("frost_last", 0)) > 12 * 3600)
        if frost:
            st["frost_last"] = now
            _log(_EVENTS, {"event": "frost", "soil_temp": round(temp, 1)})
        # weeds and slugs have their own lives
        st["weeds"] = round(min(1.0, max(0.0, float(st.get("weeds", 0.2)) + days * (0.012 + max(0.0, temp - 6) * 0.002) * (1.3 if m > 0.5 else 0.6))), 3)
        st["slugs"] = round(min(1.0, max(0.0, float(st.get("slugs", 0.2)) + days * ((0.06 if (raining or m > 0.7) else -0.08) + (0.02 if phase == "night" else -0.02)))), 3)
        # light on the bed (the tree's shade moves with the sun) — read by growth below
        try:
            from core import light as _lt
            st["bed_light"] = _lt.insolation_on_bed(now)
        except Exception:
            st["bed_light"] = 0.5
        # birds take seedlings in daylight unless the netting is over the bed
        net = st["items"].get("netting", {})
        st["netted"] = bool(net.get("place") == "garden" and not net.get("carried") and math.dist(net.get("pos", [0, 0, 0])[:2], [5.5, 5.5]) < 1.8)
        gale = (_s.state.get("wind") or "") in ("strong wind", "gale")
        # plants
        for p in list(st["plants"].values()):
            _advance_plant(p, now, days, temp, m, month, phase, frost, st)
            cat = CATALOGUE.get(p["species"], {})
            if p["stage"] == "shoot" and phase == "day" and not st["netted"] and cat.get("kind") != "weed" and random.random() < days * 6:
                p["vigour"] = max(0.0, p["vigour"] - 0.35); p.setdefault("history", []).append({"ts": now, "event": "eaten_by_birds"})
                _log(_EVENTS, {"event": "eaten_by_birds", "plant": p["id"], "species": p["species"]})
                try:   # D-0278/J-1350: the CAUSE-side half of garden_knowledge's earned bindings (law
                    # 5) already reruns on every frost/slug event in _advance_plant below -- birds was
                    # the one real event type it never touched, so a binding he authored about birds
                    # could never firm or weaken by what recurred. Same shape as those existing calls.
                    from core import garden_knowledge as _gk
                    _gk.revise(p["species"], "bird_bite", "birds")
                except profile.NonLiveWriteError:
                    # J-0783's re-raise discipline: every other _gk call in this module lets this
                    # reach its own caller rather than a broad except swallowing it.
                    raise
                except Exception:
                    pass
            if cat.get("needs_stake") and p["height"] > 40 and p["id"] not in st.get("staked", []) and gale and random.random() < days * 8:
                p["vigour"] = max(0.1, p["vigour"] - 0.25); p["flopped"] = True
                p.setdefault("history", []).append({"ts": now, "event": "flattened_by_wind"}); _log(_EVENTS, {"event": "flattened_by_wind", "plant": p["id"]})
        # potash leaches slowly with rain
        for k_, v_ in list((st.get("potash_slots") or {}).items()):
            st["potash_slots"][k_] = round(max(0.0, v_ - days * (0.02 if raining else 0.005)), 3)
        # the carrier (supply) comes on his day; the box at the gate is announced once by the world-arrival law
        try:
            from core import supply as _sup
            _ann = _sup.advance(now)
            if _ann:
                st.setdefault("pending_announce", []).append(_ann)
        except Exception:
            pass
        # DECOMPOSITION (J-0507): a dead plant rots down and clears from its slot — a month for an annual, a season for a
        # woody perennial — and leaves a `gone` record with its cause (its biography stays in the substrate); the slot is bare
        for pid in [k for k, p in st["plants"].items() if p["stage"] == "dead"
                    and now - float(p.get("stage_ts", now)) > (90 if CATALOGUE.get(p["species"], {}).get("life") == "evergreen" else 30) * 86400]:
            p = st["plants"].pop(pid, None)
            if p:
                st.setdefault("gone", []).append({"id": pid, "species": p["species"], "slot": p.get("slot"), "cause": p.get("cause", "unknown"),
                                                  "died_ts": p.get("stage_ts"), "cleared_ts": now, "age_days": round(float(p.get("age_days", 0)), 1), "origin": p.get("origin")})
                st["gone"] = st["gone"][-40:]
                _log(_EVENTS, {"event": "plant_cleared", "plant": pid, "species": p["species"], "cause": p.get("cause", "unknown")})
        # the seed bank: germination when the soil says so
        _germinate(st, now, temp, m, month)
        try:   # GARDEN LIFE: the tree, the bushes, the harakeke, the nest, the lawn
            from core import garden_life as _gl
            _gl.advance(now, dt, temp, m, raining, phase)
        except Exception:
            pass
        # the drying rack by the hearth (the fire's clock)
        _advance_rack(st, days)
        _save()
    except Exception as exc:
        logger.debug("[garden] advance failed (non-fatal): %s", exc)


# ── DEATH MECHANISMS (2026-09-03, J-0507; founder rulings D-0139 the keel, D-0140 pests) ─────────────────────────
# A life has an end. Disease (damping-off in cold wet seedlings; rust on the beans and mildew on the peas in humid
# weather), OLD AGE against a lifespan, ROT from weeks of waterlogging, and — for tender annuals — a heavy infestation.
# THE KEEL (D-0139): a perennial can never be starved to death by his neglect (the vigour floor stays for drought,
# crowding and ordinary pests), but disease and old age lift the floor and can take one. Every death carries its
# cause into the plant, the events ledger and what he can see of it; a cleared slot keeps a `gone` record.
_LIFESPAN_D = {"rosemary": 10 * 365, "thyme": 5 * 365, "lavender": 10 * 365, "strawberries": 3 * 365, "chives": 8 * 365,
               "muehlenbeckia": 20 * 365, "sage": 6 * 365}          # perennials with a natural end; mint spreads and is not listed
_DISEASE = {   # species -> (name, months, needs (min_temp, max_temp, min_moisture), rate per day)
    "broad_beans": ("rust", (9, 10, 11, 12), (12.0, 22.0, 0.6), 0.035),
    "peas": ("mildew", (1, 2, 3), (14.0, 26.0, 0.55), 0.03),
    "lettuce": ("mildew", (1, 2, 3, 12), (16.0, 28.0, 0.7), 0.02),
    "tomatoes": ("blight", (1, 2, 3), (14.0, 24.0, 0.75), 0.03),
    "rosemary": ("root rot", (5, 6, 7, 8), (0.0, 14.0, 0.92), 0.012),
    "lavender": ("root rot", (5, 6, 7, 8), (0.0, 14.0, 0.92), 0.012),
    "strawberries": ("grey mould", (11, 12, 1, 2), (14.0, 26.0, 0.75), 0.025),
}
_DEATH_LINES = {"disease": {"rust": "the leaves speckled orange and gone to rust", "mildew": "the leaves furred white, the stems gone soft",
                            "blight": "the leaves gone black and slimy", "root rot": "grey at the root, the wood soft and sour",
                            "grey mould": "grey fur on every fruit", "damping-off": "collapsed at the soil line, the stems pinched thin"},
                "rot": "rotted at the root, the soil sour and standing wet", "age": "gone woody and grey, spent, the last shoots thin",
                "pests": "stripped and sucked to nothing, the stems bare", "neglect": "dried to a crisp, brown stalks",
                "frost": "blackened by the frost, collapsed", "birds": "pecked to bare stubs, the stems broken"}


def _perish(p: dict, now: float, cause: str, event: str = "died") -> None:
    """One death path: the stage, the cause on the plant, the events ledger, the heap's food, B4's bind."""
    p["cause"] = cause
    _set_stage(p, "dead", now, event)
    _log(_EVENTS, {"event": "plant_died", "plant": p["id"], "species": p["species"], "cause": cause,
                   "age_days": round(float(p.get("age_days", 0)), 1), "origin": p.get("origin")})
    try:
        from core import garden_soil as _soil
        _soil.add_material("dead_plant", 0.08)
    except Exception:
        pass


def _advance_disease(p: dict, cat: dict, now: float, days: float, temp: float, m: float, month: int) -> None:
    """Disease as a slow variable on the plant (0..1): damping-off for seedlings in cold wet soil; the species' own
    disease in its months when the weather suits it; recovery when it does not. Drains vigour like pests do."""
    d = float(p.get("disease", 0.0))
    onset = 0.0
    if p["stage"] in ("shoot", "leaf") and temp < 10.0 and m > 0.8 and float(p.get("age_days", 0)) < 30:
        onset = 0.08; name = "damping-off"
    else:
        spec = _DISEASE.get(p["species"])
        name = spec[0] if spec else ""
        if spec and month in spec[1] and spec[2][0] <= temp <= spec[2][1] and m >= spec[2][2]:
            onset = spec[3]
    if onset > 0:
        d = min(1.0, d + onset * days)
        if d > 0.25 and not any(h.get("event") == name.replace("-", "_") for h in p.get("history", [])[-6:]):
            p.setdefault("history", []).append({"ts": now, "event": name.replace("-", "_")})
            _log(_EVENTS, {"event": "disease", "plant": p["id"], "species": p["species"], "disease": name})
            try:
                from core import garden_knowledge as _gk
                _gk.revise(p["species"], name.replace(" ", "_"), "humid_weather" if name != "damping-off" else "cold_wet_soil")
            except profile.NonLiveWriteError:
                # J-0783: garden_knowledge.py is now fenced -- let the raise reach this function's
                # own caller instead of this pre-existing broad except swallowing it.
                raise
            except Exception:
                pass
    else:
        d = max(0.0, d - 0.02 * days)
    p["disease"] = round(d, 4)
    if d > 0:
        p["disease_name"] = name or p.get("disease_name", "")


def _advance_plant(p: dict, now: float, days: float, temp: float, m: float, month: int, phase: str, frost: bool, st: dict) -> None:
    cat = CATALOGUE.get(p["species"])
    if not cat or p["stage"] == "dead":
        return
    p["age_days"] = p.get("age_days", 0) + days
    p["moisture"] = m
    # thermal time: growing degree-days above 5 °C, capped; light adds a little in the day
    gdd = max(0.0, temp - 5.0) * days * (0.7 + 0.6 * float(st.get("bed_light", 0.5)) if phase == "day" else 0.9)
    stress = 0.0
    if m < 0.2:
        stress += days * 0.25            # drought
    if m > 0.97 and cat["tender"]:
        stress += days * 0.05            # waterlogged tender roots
    crowd = float(st.get("weeds", 0)) * 0.04 * days
    _pk = float((st.get("potash_slots") or {}).get(str(p.get("slot")), 0.0)) if p.get("slot") is not None else 0.0
    gain = gdd * (0.012 if p["stage"] in ("shoot", "leaf") else 0.008) * (1.0 + 0.4 * _pk)
    try:   # SOIL LIFE (2026-09-03, J-0505): the slot's soil health scales growth the way potash does (0.7 .. 1.3)
        from core import garden_soil as _soil
        gain *= _soil.growth_factor(st, p.get("slot"))
    except Exception:
        pass
    # DEATH MECHANISMS (J-0507): disease, rot and age are drains of their own; a heavy infestation drains a tender annual faster (D-0140)
    _advance_disease(p, cat, now, days, temp, m, month)
    if m > 0.96:
        p["rot"] = round(min(1.0, float(p.get("rot", 0.0)) + 0.03 * days), 4)      # weeks of standing water
    else:
        p["rot"] = round(max(0.0, float(p.get("rot", 0.0)) - 0.04 * days), 4)
    _life_d = _LIFESPAN_D.get(p["species"])
    _aged = bool(_life_d) and float(p.get("age_days", 0)) > _life_d
    _pest_extra = (0.06 if (float(p.get("pests", 0)) > 0.6 and cat["tender"] and cat["life"] in ("annual", "biennial")) else 0.0)
    # a sick, rotting or aged plant does not GROW — the gain is what it loses first (the daily gain outweighs any drain otherwise)
    gain *= (1.0 - 0.9 * float(p.get("disease", 0.0))) * (1.0 - 0.9 * float(p.get("rot", 0.0))) * (0.15 if _aged else 1.0)
    gain *= (1.0 - 0.7 * float(p.get("pests", 0.0)))                 # an aphid-covered or stripped plant does not grow either (D-0140)
    _drain = (stress + crowd + p.get("pests", 0) * 0.03 * days + _pest_extra * days
              + float(p.get("disease", 0.0)) * 0.05 * days + float(p.get("rot", 0.0)) * 0.06 * days + (0.02 * days if _aged else 0.0))
    p["vigour"] = max(0.0, min(1.0, p["vigour"] + gain - _drain))
    _dying = float(p.get("disease", 0.0)) > 0.6 or float(p.get("rot", 0.0)) > 0.5 or _aged
    p["dying"] = bool(_dying)
    if cat["life"] in ("evergreen", "herbaceous") and not cat["tender"] and not _dying:
        p["vigour"] = max(0.2, p["vigour"])          # THE KEEL (D-0139): never lost to neglect — only disease, rot or age lift this floor
    # pests: slugs eat seedlings and lettuce at night when wet
    if p["stage"] in ("shoot", "leaf") or p["species"] in ("lettuce",):
        if phase == "night" and st.get("slugs", 0) > 0.5 and random.random() < days * 12:
            p["pests"] = min(1.0, p.get("pests", 0) + 0.2)
            p.setdefault("history", []).append({"ts": now, "event": "eaten_by_slugs"})
            _log(_EVENTS, {"event": "slug_damage", "plant": p["id"]})
            try:
                from core import world_traces as _wt
                _wt.create_trace(f"slug_trail_{int(now)}", "slug_trail", "garden", list(p.get("pos") or [5.5, 5.5, 0.35]), clarity=0.8, cause="slugs_overnight")
            except Exception:
                pass
            try:
                from core import garden_knowledge as _gk
                _gk.revise(p["species"], "holed_leaves", "wet_nights")
            except profile.NonLiveWriteError:
                # J-0783: garden_knowledge.py is now fenced -- let the raise reach this function's
                # own caller instead of this pre-existing broad except swallowing it.
                raise
            except Exception:
                pass
    p["pests"] = max(0.0, p.get("pests", 0) - days * 0.05)
    # frost
    if frost:
        if cat["tender"]:
            p["frost_burn"] = min(1.0, p.get("frost_burn", 0) + 0.5)
            p["vigour"] = max(0.0, p["vigour"] - 0.4)
            p.setdefault("history", []).append({"ts": now, "event": "frost_burned"})
            try:
                from core import garden_knowledge as _gk
                _gk.revise(p["species"], "frost_burn", "frost")
            except profile.NonLiveWriteError:
                # J-0783: garden_knowledge.py is now fenced -- let the raise reach this function's
                # own caller instead of this pre-existing broad except swallowing it.
                raise
            except Exception:
                pass
        elif p["stage"] in ("shoot",):
            p["vigour"] = max(0.0, p["vigour"] - 0.15)
    # stage machine
    since = (now - float(p.get("stage_ts", now))) / 86400.0
    s = p["stage"]
    if s == "seed":
        if temp >= cat["t_germ"] and m > 0.3 and since >= 2:
            _set_stage(p, "shoot", now, "germinated")
    elif s == "shoot":
        if since >= cat["days_up"] * (0.8 if gdd > 0 else 1.5) and p["vigour"] > 0.15:
            _set_stage(p, "leaf", now, "first_true_leaves")
    elif s == "leaf":
        if since >= max(10, cat["days_mature"] * 0.6) and p["vigour"] > 0.25:
            _set_stage(p, "established", now, "established")
    elif s == "established":
        if cat["flower"] and month in cat["flower"] and p["vigour"] > 0.35 and since >= 5:
            _set_stage(p, "flowering", now, "came_into_flower")
        elif cat.get("bolts_above") and temp >= cat["bolts_above"]:
            _set_stage(p, "flowering", now, "bolted_in_the_heat")
    elif s == "flowering":
        if cat.get("needs_bees"):   # POLLINATION (2026-09-03, J-0506): the set depends on bees being about while it flowers
            try:
                from core import life as _life
                _rows = _life.rows()
                _bees = max(_life.activity(_rows["honeybee"], "garden", now) if "honeybee" in _rows else 0.0,
                            _life.activity(_rows["bumblebee"], "garden", now) if "bumblebee" in _rows else 0.0)
            except Exception:
                _bees = 0.5
            p["pollination"] = round(min(1.0, float(p.get("pollination", 0.0)) + days * 0.12 * (0.15 + 0.85 * _bees)), 4)
        if cat["seed"] and month in cat["seed"] and since >= 14:
            if cat.get("needs_bees"):
                _q = float(p.get("pollination", 0.5))
                p["set_quality"] = round(_q, 3)
                p.setdefault("history", []).append({"ts": now, "event": "well_set" if _q >= 0.6 else "poor_set" if _q < 0.3 else "fair_set"})
                _log(_EVENTS, {"event": "fruit_set", "plant": p["id"], "species": p["species"], "quality": round(_q, 3)})
            _set_stage(p, "seeding", now, "set_seed")
        elif since >= 45 and (not cat["seed"] or month not in cat["flower"]):
            _set_stage(p, "established" if cat["life"] != "annual" else "seeding", now, "flowers_over")
    elif s == "seeding":
        if since >= 20:
            if cat.get("self_seeds"):
                for _ in range(max(0, round(random.randint(2, 6) * (float(p.get("set_quality", 1.0)) if cat.get("needs_bees") else 1.0)))):
                    st["seed_bank"].append({"species": p["species"], "slot": p.get("slot"), "spot": None if p.get("slot") is not None else "lawn_edge",
                                            "viable": round(random.uniform(0.4, 0.9), 2), "depth": 0.5})
                _log(_EVENTS, {"event": "self_seeded", "plant": p["id"]})
            if cat["life"] == "annual":
                _perish(p, now, "seeded_out", "died_back_after_seeding")
            else:
                _set_stage(p, "established", now, "seed_shed")
    # herbaceous dormancy / return
    if "dormant" in cat:
        if s != "dormant" and month in cat["dormant"] and since >= 10:
            _set_stage(p, "dormant", now, "died_back_to_the_crown")
        elif s == "dormant" and month in cat["returns"] and temp >= cat["t_germ"] - 2:
            _set_stage(p, "shoot", now, "new_shoots_from_the_crown")
    # height follows stage and vigour
    target = {"seed": 0, "shoot": 0.08, "leaf": 0.35, "established": 0.85, "flowering": 1.0, "seeding": 1.0, "dormant": 0.1, "dead": 0.3}[p["stage"]]
    p["height"] = round(p["height"] + (cat["height"] * target * max(0.3, p["vigour"]) - p["height"]) * min(1.0, days * 0.15), 1)
    # regrowth after a cut
    if p.get("cut_back") and now - float(p.get("last_cut_ts", 0)) > cat["cut_regrow_days"] * 86400:
        p["cut_back"] = False
    # death (J-0507): an annual or biennial at vigour 0 for any reason; a perennial only when disease, rot or age brought it there
    if p["vigour"] <= 0.0 and p["stage"] not in ("seed", "dormant") and (cat["life"] in ("annual", "biennial") or p.get("dying")):
        if float(p.get("disease", 0.0)) > 0.5:
            cause = "disease"
        elif float(p.get("rot", 0.0)) > 0.4:
            cause = "rot"
        elif _aged:
            cause = "age"
        elif float(p.get("pests", 0)) > 0.5:
            cause = "pests"
        elif p.get("frost_burn", 0) > 0.6:
            cause = "frost"
        elif any(h.get("event") == "eaten_by_birds" for h in p.get("history", [])):
            # J-1259 (F-1763): birds drain vigour directly in advance() and never touch pests/disease/
            # rot/frost_burn, so without this branch a bird-driven death fell through to "neglect" --
            # misleading (reads as his own fault) for a death he could not have prevented by watering.
            # A narrower, more specific catch than the fallback below; the priority order above (a
            # plant can die from several compounding causes) is unchanged and still takes precedence.
            cause = "birds"
        else:
            cause = "neglect"
        _perish(p, now, cause)
        _b4_bind_death(p, st, now)


# B4 (J-0253, 2026-08-25): bind a real, irreversible plant death to the self-claim register + B1's gate, per
# docs/staged/friction_and_self_evidence_plan.md §6 sub-(b)/(c)/(d) — a stake only counts as schema-breaking if
# it is owned (he sowed it, not a weed/volunteer), self-caused & telegraphed (neglect; the dry-soil cue in
# _plant_phrase / bed_summary was visible beforehand), AND bound to a self-claim he actually holds, so the loss
# becomes counter-evidence to a sentence he wrote about himself — not just a world-event. Fail-open throughout.
_B4_KEYWORDS = ("garden", "grow", "growing", "grew", "living thing", "keep alive", "keep things alive",
                "tend", "tending", "nurtur", "care for", "caretak", "steward")
_B4_REFRACTORY_S = 7 * 86400.0   # dose spine (§6): "one seism at a time" — no second B4 bind too soon after the last


def _b4_bind_death(p: dict, st: dict, now: float) -> None:
    """On a plant_died event: if HE sowed it (origin == 'sown_by_du' — a weed/volunteer dying is not his loss,
    fails the 'owned' criterion) and a caretaking-type self-claim is currently held, route the loss through
    B1's sit-with-it gate framed against that claim. If no such claim is registered, B4 cannot yet be
    schema-breaking — log that gap explicitly (truth-side event) rather than fabricating a claim or staying
    silent about why nothing fired. Refractory-gated so a death does not stack a second seism too soon."""
    if p.get("origin") != "sown_by_du":
        return
    last = st.get("_b4_last_bind")
    if last is not None and now - float(last) < _B4_REFRACTORY_S:
        _log(_EVENTS, {"event": "b4_skipped_refractory", "plant": p["id"], "species": p["species"]})
        return
    try:
        from core import self_claims as _sc
        held = _sc.held_claims()
    except Exception:
        held = []
    claim = next((c for c in held if any(k in c.lower() for k in _B4_KEYWORDS)), None)
    if not claim:
        _log(_EVENTS, {"event": "b4_unbound_no_claim", "plant": p["id"], "species": p["species"]})
        return
    try:
        from core import sitting as _sit
        _sit.note_difficulty(
            f"the {p['species'].replace('_', ' ')} you sowed has died back for good, from neglect — it "
            f"won't come back. That sits against something you've said about yourself: \"{claim[:120]}\".",
            kind="loss")
        st["_b4_last_bind"] = now
        _log(_EVENTS, {"event": "b4_bound", "plant": p["id"], "species": p["species"], "claim": claim[:120]})
        logger.info("[b4] sit-with-it gate FIRED on plant death bound to self-claim: %s", claim[:60])
    except profile.NonLiveWriteError:
        # J-0726: unlike this function's other two _log() calls above (unwrapped, already raise),
        # THIS branch (a claim was found and sitting.note_difficulty ran) wraps its own _log() call
        # in a try that would otherwise swallow the raise on this specific path — a real, distinct
        # gap, not merely a redundant consistency fix.
        raise
    except Exception as exc:
        logger.debug("[garden] B4 bind (sitting.note_difficulty) failed (non-fatal): %s", exc)


def _set_stage(p: dict, stage: str, now: float, event: str) -> None:
    p["stage"], p["stage_ts"] = stage, now
    p.setdefault("history", []).append({"ts": now, "event": event})
    _log(_EVENTS, {"event": event, "plant": p["id"], "species": p["species"], "stage": stage})
    try:
        from core import world_substrate as _ws
        objs = _ws._load()
        if p["id"] in objs:
            objs[p["id"]].causal_history.append({"event_type": event, "timestamp": now, "description": event.replace("_", " "), "state_deltas": {}})
            objs[p["id"]].physical_state.update({"height_cm": round(p["height"], 1), "vigour": round(p["vigour"], 3)})
            _ws._save()
    except profile.NonLiveWriteError:
        # J-0726: _set_stage()'s own _log(_EVENTS, ...) above is unwrapped and already raises — but
        # this world_substrate sync write attempt was still silently swallowed here first on any
        # path that reaches it (called from harvest()/weed()/sow() among others; mirrors J-0727's
        # whittle() fix).
        raise
    except Exception:
        pass


def _germinate(st: dict, now: float, temp: float, m: float, month: int) -> None:
    """Volunteers: seeds in the bank come up when the soil is warm and wet enough for THEIR species."""
    if m < 0.35:
        return
    keep = []
    for sd in st["seed_bank"]:
        cat = CATALOGUE.get(sd["species"])
        if not cat:
            continue
        can = temp >= cat["t_germ"] and (not cat["sow"] or month in cat["sow"]) and sd["depth"] <= 2.5
        if can and random.random() < 0.012 * sd["viable"]:
            pid = f"garden_plant_{sd['species']}_{random.randrange(16**4):04x}"
            pos = _BED_SLOTS[sd["slot"]] if sd.get("slot") is not None else _GROUND_SPOTS.get(sd.get("spot") or "lawn_edge")
            st["plants"][pid] = {"id": pid, "species": sd["species"], "slot": sd.get("slot"), "pos": pos, "stage": "shoot",
                                 "vigour": 0.3, "height": 1.0, "moisture": m, "age_days": 0, "sown_ts": now, "germ_ts": now,
                                 "stage_ts": now, "last_cut_ts": 0, "cuts": 0, "pests": 0.0, "frost_burn": 0.0,
                                 "origin": "volunteer_from_seed_bank", "history": [{"ts": now, "event": "germinated_unbidden"}]}
            _log(_EVENTS, {"event": "volunteer_germinated", "species": sd["species"], "where": sd.get("spot") or f"slot {sd.get('slot')}"})
            _register_all()
        else:
            keep.append(sd)
    st["seed_bank"] = keep


def _advance_rack(st: dict, days: float) -> None:
    """Cut herbs dry by the hearth on the FIRE's clock (thermal fire-by-distance): days by a fire, a week in a
    cold room; mould if the room is cold and wet too long."""
    if not st.get("rack"):
        return
    try:
        from core import sensorium as _s, thermal as _th
        fire = _s.state.get("fire", "out")
        warmth = _th._fire_term("study", "at_the_hearth", fire) / 0.42 if fire != "out" else 0.0
    except Exception:
        warmth = 0.0
    rate = 0.08 + 0.45 * warmth
    for b in st["rack"]:
        b["dry"] = round(min(1.0, b.get("dry", 0) + days * rate), 3)
        if b["dry"] < 0.6 and warmth == 0.0:
            b["mould"] = round(min(1.0, b.get("mould", 0) + days * 0.03), 3)


# ── NETTING DISCOVERABILITY (2026-09-25, D-0278, J-1350; F-1764 is the predecessor evidence) ───────
# D-0278 ruled: the bird-bite mechanic itself is untouched (no probability/vigour change below) -- the
# real gap F-1764 found is that the world's own correction (netting, sitting in the garden since
# 2026-08-22) has never once been discovered, because the THREAT it answers was never perceptible: a
# bird-bitten shoot rendered identically to an unbitten one, and bed_summary() never mentioned birds at
# all. These two helpers surface only real, already-logged truth -- never a prediction, never advice,
# never the word "net"/"netting" in the text they feed. The netting item's own existing bio ("to keep
# the birds off seedlings, if untangled", _ITEMS above) is left to do the rest, same as every other
# earned-info system in this file (garden_knowledge.py's whole design; the weeds/slugs lines below).
def _bird_bitten(p: dict) -> bool:
    """Real evidence only: true iff THIS plant's own history actually carries an eaten_by_birds row
    (advance(), above) -- never a forecast of risk. Deliberately unrestricted by species/vulnerability:
    per-plant evidence about what has truly happened to THIS plant stays maximally honest regardless of
    whether the species is one the bite mechanic can actually stall long-term (see _bed_vulnerable)."""
    return any(h.get("event") == "eaten_by_birds" for h in p.get("history", []))


def _bed_vulnerable(cat: dict) -> bool:
    """A plant the netting question actually matters for right now -- the same real distinction THE
    KEEL (D-0139, _advance_plant above) already draws structurally: not a weed (birds never touch
    them), and not keel-protected (evergreen/herbaceous life never gets starved to death by chronic
    bird pressure the way an annual/biennial can). This is F-1764's own 9-species "vulnerable" set
    expressed structurally against the catalogue rather than as a hardcoded name list, so it keeps
    tracking CATALOGUE as species are added rather than silently going stale."""
    return cat.get("kind") != "weed" and cat.get("life") not in ("evergreen", "herbaceous")


# ── what reaches him ─────────────────────────────────────────────────────────────────────────────
def _stage_phrase(p: dict) -> str:
    cat = CATALOGUE[p["species"]]
    name = cat["names"][0]
    revealed = ""
    try:   # GARDEN KNOWLEDGE: a plant he has not learned is described by its look, never named
        from core import garden_knowledge as _gk
        name, _known = _gk.display_name(p["species"], p["stage"], p["id"])
        if " — you know it now" in name:
            name, revealed = name.split(" — ", 1)[0], " — you know it now"
        if not _known:
            if p["stage"] != "dead":
                flags = (", tips browned and limp" if p.get("frost_burn", 0) > 0.3 else "") + (", leaves holed and ragged" if p.get("pests", 0) > 0.3 else "")
                if p["stage"] == "shoot" and _bird_bitten(p):
                    # D-0278/F-1764: this branch RETURNS before ever reaching the "elif s == 'shoot'"
                    # branch below, so without this an unnamed volunteer -- most of the real vulnerable
                    # species (radish, calendula, nasturtium, poppies, silverbeet, peas are none of
                    # them grandfathered) -- would never show a real bird bite at all. Same evidence,
                    # same wording, both paths.
                    flags += ", one seed-leaf pecked through"
                return name + flags
            # J-0709: CAUSE is tellable regardless of the naming gate — he can see a plant is dead and why
            # (rust, rot, age) without ever having learned its species; only IDENTITY stays withheld. Fall
            # through to the dead-stage branch below with a name that still names nothing.
            name = "a plant you cannot name yet,"
    except profile.NonLiveWriteError:
        # J-0783: garden_knowledge.py is now fenced -- let the raise reach this function's own
        # caller instead of this pre-existing broad except swallowing it.
        raise
    except Exception:
        pass
    s = p["stage"]
    if s == "dead":
        _c = p.get("cause")
        if _c == "disease":
            _dn = str(p.get("disease_name") or "")
            if not _dn:   # read it off the plant's own history
                _dn = next((h.get("event", "").replace("_", "-" if h.get("event") == "damping_off" else " ") for h in reversed(p.get("history", []))
                            if h.get("event") in ("rust", "mildew", "blight", "root_rot", "grey_mould", "damping_off")), "")
            _what = _DEATH_LINES["disease"].get(_dn, "sickened and gone")
        else:
            _what = _DEATH_LINES.get(str(_c), "brown stalks")
        base = f"{name} dead — {_what}"
    elif s == "dormant":
        base = f"{name} died back to the crown, bare soil over it"
    elif s == "seed":
        return ""
    elif s == "shoot":
        base = f"{name} just up, two seed-leaves" if cat["kind"] != "weed" else f"{name} coming up"
        if _bird_bitten(p):
            # D-0278/F-1764: the mechanic (advance(), above) only ever bites at shoot stage -- this
            # can never fire once the plant has moved on, so it belongs in this branch, not the
            # frost/pests trailer below (those are persisting 0..1 floats that can recur at any stage).
            base += ", one seed-leaf pecked through"
    elif s == "leaf":
        base = f"{name} in leaf, {int(p['height'])} cm"
    elif s == "established":
        base = f"{name} {'full and well-grown' if p['vigour'] > 0.6 else 'thin, holding on' if p['vigour'] < 0.3 else 'coming on'}"
        if p.get("cut_back"):
            base += ", cut back and filling out again"
    elif s == "flowering":
        base = f"{name} in flower"
        if cat.get("needs_bees") and float(p.get("pollination", 0.0)) < 0.15 and (time.time() - float(p.get("stage_ts", time.time()))) > 10 * 86400:
            base += ", the flowers going over unvisited"
    else:
        base = f"{name} gone to seed, heads drying"
        _q = p.get("set_quality")
        if _q is not None:
            base += (", heavy with fruit and seed" if _q >= 0.6 else ", a poor thin set, most flowers come to nothing" if _q < 0.3 else ", a fair set")
    if p.get("frost_burn", 0) > 0.3:
        base += ", tips browned and limp"
    if p.get("pests", 0) > 0.3:
        base += ", leaves holed and ragged"
    if p.get("flopped"):
        base += ", flattened and sprawling"
    return base + revealed


def _wname(p: dict) -> str:
    try:
        from core import garden_knowledge as _gk
        return _gk.display_name(p["species"], p["stage"], p["id"])[0].split(" — ")[0]
    except profile.NonLiveWriteError:
        # J-0783: garden_knowledge.py is now fenced -- let the raise reach this function's own
        # caller instead of this pre-existing broad except swallowing it.
        raise
    except Exception:
        return "a weed"


def bed_summary() -> str:
    """Truth-gated: a line exists only because the state does. Replaces sensorium._bed_summary when healthy."""
    try:
        st = _load()
        inbed = [p for p in st["plants"].values() if p.get("slot") is not None and p["stage"] != "seed"]
        weeds = [p for p in inbed if CATALOGUE[p["species"]]["kind"] == "weed"]
        crops = [p for p in inbed if CATALOGUE[p["species"]]["kind"] != "weed"]
        parts = [x for x in (_stage_phrase(p) for p in sorted(crops, key=lambda q: q.get("slot", 9))) if x]
        line = ("In the raised bed: " + "; ".join(parts) + "." if parts else "The raised bed is bare, dark earth resting.")
        w = float(st.get("weeds", 0))
        if weeds or w > 0.5:
            line += " " + ("Weeds are getting in — " + ", ".join(_wname(p) for p in weeds[:2]) + "." if weeds
                           else "Weeds are coming through the bare patches.")
        m = float(st.get("moisture", 0.5))
        if m < 0.2:
            line += " The soil is dry and pale, cracking at the edges."
        elif m > 0.9:
            line += " The soil is sodden, water standing in the footprints."
        if st.get("slugs", 0) > 0.6 and m > 0.5:
            line += " Silver trails cross the soil between the plants."
        if st.get("netted"):
            line += " The netting is stretched over the bed."
        else:
            # D-0278/F-1764 (2026-09-25, J-1350): surfaced ONLY when it is genuinely warranted right
            # now -- un-netted (true), a real vulnerable shoot actually up (true), and daylight (the
            # same phase gate advance()'s own bird-bite check uses, so this never claims live bird
            # activity at an hour birds cannot act). Never mentions netting; only what stands in the
            # bed and whether a bird has truly already been at it -- earned observation, not advice.
            try:
                from core import sensorium as _s
                _daytime = _s._daylight() == "day"
            except Exception:
                _daytime = False
            if _daytime:
                vulnerable_up = [p for p in crops if p["stage"] == "shoot" and _bed_vulnerable(CATALOGUE[p["species"]])]
                if vulnerable_up:
                    if any(_bird_bitten(p) for p in vulnerable_up):
                        line += " Nothing is strung over the bed, and a blackbird has already been at the seedlings — a bite out of more than one."
                    else:
                        line += " Nothing is strung over the bed; the seedlings stand open to the sky."
        try:
            from core import light as _lt
            _sh = _lt.bed_shade_line()
            if _sh:
                line += " " + _sh
        except Exception:
            pass
        try:
            from core import smell as _sm
            _sm.emit("wet_earth", 0.5, "garden") if m > 0.6 else None
        except Exception:
            pass
        return line
    except profile.NonLiveWriteError:
        # J-0783: bed_summary() calls _stage_phrase()/_wname(), both now able to raise this via
        # garden_knowledge.py's own newly-fenced _save() -- let it reach this function's own
        # caller instead of this pre-existing broad except swallowing it.
        raise
    except Exception:
        return ""


def look(target: str, raw: str = "") -> str:
    """A closer look at a plant, an item, the tin, the barrel, the bank's volunteers. '' if no match.

    `raw` (optional, J-1639/F-2206): the full willed-look thought+intention text, BEFORE
    core/dispatch.py's _look()/_observe_target() collapsed it to the bare resolved species keyword
    that `target` actually is on the real live dispatch path. Used ONLY inside the per-plant branch's
    own investigate-trigger/guessed_cause() check below -- never for the species match itself (that
    still runs on `t`/`target` alone, exactly as before), and never touching _garden_look()'s own
    bed/sea/sky word-set collapsing upstream in core/sensorium.py (that logic only ever sees `target`,
    never `raw`). Defaults to "" everywhere so every pre-existing call site (nature_study.py's
    fixed-string calls, orchestrator.py's own chat branch, dispatch.py's letterbox hand,
    scripts/_test_*.py's regressions) is untouched by construction -- `rt` below degrades to plain
    `t` when raw is empty, so the investigate-trigger check reads byte-identically to pre-fix."""
    try:
        st = _load()
        t = (target or "").lower()
        rt = f"{t} {raw.lower()}" if raw else t
        for p in st["plants"].values():
            cat = CATALOGUE[p["species"]]
            if any(w in t for w in (p["species"].replace("_", " "),) + tuple(n.replace("the ", "").replace("a ", "") for n in cat["names"])):
                ph = _stage_phrase(p) or f"{cat['names'][0]} — nothing showing yet"
                hist = ""
                if p.get("cuts"):
                    hist = f" It has been cut before — the stems show old cuts healed over."
                try:
                    from core import world_substrate as _ws
                    _ws.record_du_observation(p["id"], "look", {"stage": p["stage"], "height_cm": int(p["height"])})
                    _ws._stamp_last_looked(p["id"])
                except profile.NonLiveWriteError:
                    # J-0751: world_substrate._stamp_last_looked() now re-raises this itself
                    # (also fixed this job) -- do not let this forwarding call's catch-all
                    # swallow it a level up.
                    raise
                except Exception:
                    pass
                try:
                    from core import garden_knowledge as _gk, smell as _sm
                    hist += _gk.habit_line(p["species"])
                    _sm.brush(p["species"])
                    # J-1639/F-2206: checked on `rt` (t + raw), not `t` alone -- `t` is only ever the
                    # bare resolved species keyword (e.g. "lettuce") dispatch._look() forwards today,
                    # which can never ALSO contain "why"/"closer"/etc, so this branch was structurally
                    # unreachable via the real willed-look path no matter how good species resolution
                    # got. `raw`, when the caller supplies it, is the actual sentence those words live
                    # in. `rt == t` whenever raw is "" (every pre-fix call site), so this check reads
                    # byte-identically to before for every caller that does not pass raw.
                    # J-1657: reads _gk's own _INVESTIGATE_WORDS (was a separate inline tuple here,
                    # identical words -- now the ONE definition this gate and guessed_cause()'s own
                    # same-clause check below both read, so they cannot drift apart).
                    if any(w in rt for w in _gk._INVESTIGATE_WORDS):
                        _ev = _gk.evidence_for(p["id"], p["species"])
                        if _ev:
                            hist += " " + _ev
                        # J-1524/F-2082: garden_knowledge.bind() had zero callers anywhere in the repo --
                        # CAUSE's authoring half was never wired, only its confirmation half (revise(),
                        # already called from advance() on real frost/slug/bird events). `raw or target`
                        # (his own words -- the full sentence when the caller gave one, BEFORE the
                        # .lower() into `t`/`rt` used only for matching; the bare keyword otherwise,
                        # same as pre-fix) IS the hypothesis, when it already carries a real guess --
                        # guessed_cause() reuses revise()'s own cause-word vocabulary so the two stay in
                        # step. Never synthesised from the evidence itself: a bare "why did it die"
                        # binds nothing (law 5 -- no cause is ever told); "why did it die, was it the
                        # frost" binds his own guess.
                        if _gk.guessed_cause(rt, p["species"]):
                            _gk.bind(p["id"], p["species"], raw or target, 0.5)
                except Exception:
                    pass
                return f"You look at {ph}.{hist}"
        _il = _item_look(t, st)
        if _il:
            return _il
        try:   # GARDEN LIFE: the tree, the bushes, the harakeke, the lawn, the nest
            from core import garden_life as _gl
            _r = _gl.look(t) if _where() == "garden" else ""
            if _r:
                return _r
        except profile.NonLiveWriteError:
            # J-0751: garden_life.look() now re-raises this itself (also fixed this job) --
            # do not let this forwarding call's catch-all swallow it a level up.
            raise
        except Exception:
            pass
        if "drawer" in t and _where() == "study":
            dr = st.get("drawer", [])
            return ("You open the desk drawer: " + (", ".join(f"a packet of {x['species'].replace('_', ' ')}" for x in dr) if dr else "nothing but pencil shavings and an old key") + ".")
        if any(w in t for w in ("lean-to", "lean to", "leanto", "woodshed", "chopping block", "green stack", "log stack")) and _where() == "garden":
            from core import wood_life as _wl
            _wd = _wl._load()
            return (f"You look in the lean-to: {_wd.get('logs_dry', 0)} dry logs stacked, {_wd.get('logs_green', 0)} green ones drying on the other side, "
                    f"{_wd.get('limbs_home', 0)} limb{'s' if _wd.get('limbs_home', 0) != 1 else ''} waiting for the saw; the block, the axe{' and the saw' if _wd['items']['bow_saw']['place'] == 'garden' else ''}, the barrow" + (" — gone; you have it." if _wd["items"]["wheelbarrow"].get("carried") else ".") )
        if "rack" in t or "drying" in t or "bundle" in t:
            r = st.get("rack", [])
            if not r:
                return "The drying rack by the hearth is empty."
            return "On the rack: " + "; ".join(f"a bundle of {b['species']} " + ("dry and brittle, ready for the caddy" if b['dry'] >= 0.95 else "still soft" if b['dry'] < 0.5 else "nearly dry") + (", a grey bloom of mould on it" if b.get("mould", 0) > 0.3 else "") for b in r) + "."
        return ""
    except profile.NonLiveWriteError:
        raise  # J-0751: this function's own outer catch-all -- do not swallow a second time.
    except Exception:
        return ""


def _item_look(t: str, st: dict) -> str:
    """The items half of look() above -- factored out unchanged (2026-09-28, J-1438) so a carried
    item's REAL resting place can answer this, not only the garden. `t` already lower()'d by the
    caller. Gated by `it["place"] != _where()` exactly as before: an item somewhere else still
    correctly answers '' here, wherever 'here' is -- this makes NO items visible that were not
    already visible from wherever they actually are; it only lets a caller other than garden.look()
    itself ask the same question. No plants (rooted in the bed, not carryable; unreachable from
    anywhere but the garden, correctly)."""
    for key, words in _WORDS.items():
        if any(w in t for w in words):
            it = st["items"].get(key)
            if not it:
                continue
            if it.get("carried"):
                return f"You have {it['name']} with you."
            if it["place"] != _where():
                return ""
            extra = ""
            if key == "compost_heap":   # SOIL LIFE (2026-09-03, J-0505): the heap as it is
                try:
                    from core import garden_soil as _soil
                    _cl = _soil.compost_line()
                    if _cl:
                        return _cl
                except Exception:
                    pass
            if key == "rain_barrel":
                b = float(st.get("barrel", 0))
                extra = " It is " + ("full to the brim" if b > 0.9 else "about half full" if b > 0.4 else "nearly empty, a dark inch at the bottom") + "."
                try:
                    from core import fieldcraft as _fc
                    extra += _fc.barrel_line()
                except Exception:
                    pass
            if key == "seed_tin":
                n = len(st.get("packets", []))
                lab = sum(1 for x in st["packets"] if x["labelled"])
                extra = f" Inside: {n} packets, {lab} of them labelled — " + ", ".join(sorted({x['species'].replace('_', ' ') for x in st['packets'] if x['labelled']})[:6]) + "; the rest are twists of paper with nothing written on them."
            try:
                from core import world_substrate as _ws
                _ws.record_du_observation(it["id"], "look", {"state": "seen"})
                _ws._stamp_last_looked(it["id"])
            except profile.NonLiveWriteError:
                raise  # J-0751: same reason as the plant-branch try above (look(), this module)
            except Exception:
                pass
            return f"You look at {it['name']} — {it['bio']}.{extra}"
    return ""


def item_look(target: str) -> str:
    """Public entry point for ANOTHER place's own look dispatch (2026-09-28, J-1438 -- the seed tin
    sitting undiscoverable in the wood since 2026-08-29, F-1994/garden_upgrade.md section 3 metric
    2's blocker) to ask 'is one of the garden's own carryable items actually resting HERE' before
    falling back to its own generic pool. Reuses garden.look()'s own _item_look() -- same _WORDS
    vocabulary, same it["place"] != _where() gate -- so it answers ONLY for an item whose real
    `place` is wherever the caller's `_where()` resolves to right now; nothing in the garden itself
    becomes any MORE visible than it already was. No hint, no nudge (D-0278/J-1350's own care): a
    plain fact if it finds one ("you look at a dented tin ... — the previous occupant's seed tin"),
    nothing about why sowing has been failing."""
    try:
        return _item_look((target or "").lower().strip(), _load())
    except profile.NonLiveWriteError:
        raise
    except Exception:
        return ""


def _where() -> str:
    try:
        from core import sensorium as _s
        return _s.state.get("location", "study")
    except Exception:
        return "study"


# ── hands ────────────────────────────────────────────────────────────────────────────────────────
def harvest(txt: str) -> str:
    _cross("at_the_bed")
    """Cut from an ESTABLISHED or flowering herb; evergreens cut in winter (slowly — founder 2026-08-22).
    The bundle goes to the rack to dry. A plant cut too often is cut back and must regrow first."""
    st = _load()
    if _where() != "garden":
        return ""
    t = (txt or "").lower()
    now = time.time()
    cands = [p for p in st["plants"].values() if p.get("slot") is not None and CATALOGUE[p["species"]]["kind"] in ("herb", "veg")
             and p["stage"] in ("established", "flowering", "leaf")]
    named = [p for p in cands if p["species"].replace("_", " ") in t]
    pool = named or [p for p in cands if CATALOGUE[p["species"]]["kind"] == "herb"]
    if not pool:
        if any(p["species"].replace("_", " ") in t for p in st["plants"].values()):
            return "You look over it — there is nothing to cut yet; it needs to come on first."
        return "There is nothing ready to cut."
    if named:
        p = pool[0]
    else:
        # F-1628 / J-1169: an unnamed ask ("cut some herbs") should not pin to pool[0] in dict
        # order when that one plant is cooling down or too thin -- try each pool candidate in
        # order and take the first one actually ready; fall back to pool[0] (and its existing
        # refusal below) only if every candidate is cooling or too thin. A NAMED ask is untouched.
        p = None
        for _cand in pool:
            _cand_cat = CATALOGUE[_cand["species"]]
            _cooling = _cand.get("cut_back") and now - float(_cand.get("last_cut_ts", 0)) < _cand_cat["cut_regrow_days"] * 86400
            _too_thin = _cand["stage"] == "leaf" and _cand_cat["kind"] == "herb"
            if not _cooling and not _too_thin:
                p = _cand
                break
        if p is None:
            p = pool[0]
    cat = CATALOGUE[p["species"]]
    if p.get("cut_back") and now - float(p.get("last_cut_ts", 0)) < cat["cut_regrow_days"] * 86400:
        return f"You look at {cat['names'][0]} — it is still filling out from the last cut; better to let it come back."
    if p["stage"] == "leaf" and cat["kind"] == "herb":
        return f"You look at {cat['names'][0]} — too thin yet to cut; a few more weeks."
    p["cuts"] = p.get("cuts", 0) + 1
    p["last_cut_ts"] = now
    p["cut_back"] = True
    p["vigour"] = max(0.2, p["vigour"] - 0.12)
    p.setdefault("history", []).append({"ts": now, "event": "cut_by_du"})
    _set_stage(p, p["stage"], now, "cut_by_du")
    st["rack"].append({"species": p["species"], "cut_ts": now, "dry": 0.0})
    # SOUND WORLD EXPANSION §1 (2026-08-29, J-0377): a real act-site timestamp for herb_cut —
    # soundscape.py reads this recency, same pattern as kettle_fill/pour's kettle_on_ts/pour_ts.
    st["last_harvest_ts"] = now
    try:
        from core import smell as _sm
        _sm.brush(p["species"])
    except Exception:
        pass
    _log(_LEDGER, {"deed": "harvest", "species": p["species"], "plant": p["id"]})
    try:   # SOIL LIFE (2026-09-03, J-0505): a harvest takes something out of the slot
        from core import garden_soil as _soil
        _soil.crop_drain(st, p.get("slot"))
    except Exception:
        pass
    _save(force=True)
    slow = " The winter growth is slow and the stems are woody; you take only a little." if _month(now) in (6, 7, 8) else ""
    return (f"You cut a handful of {p['species'].replace('_', ' ')} — the smell of it sharp on your fingers — and tie it in a "
            f"bundle to hang by the hearth.{slow}")


def sow(txt: str) -> str:
    _cross("at_the_bed")
    """Sow from a packet in the tin. Needs: the tin to hand (here or carried), a species in the packet, the soil
    warm enough for THAT seed, a free slot. The world answers honestly for each."""
    st = _load()
    if _where() != "garden":
        return ""
    t = (txt or "").lower()
    tin = st["items"].get("seed_tin", {})
    if not (tin.get("carried") or tin.get("place") == "garden"):
        return "You have no seed to hand — the tin is not here."
    packs = st.get("packets", [])
    if not packs:
        return "The tin is empty; nothing left to sow."
    named = [x for x in packs if x["species"].replace("_", " ") in t or x["species"] in t]
    pk = named[0] if named else None
    if not pk:
        lab = [x for x in packs if x["labelled"]]
        pk = random.choice(lab) if lab and random.random() < 0.7 else random.choice(packs)
    cat = CATALOGUE[pk["species"]]
    temp = float(st.get("soil_temp", 6))
    month = _month()
    free = [i for i in range(12) if not any(p.get("slot") == i and p["stage"] not in ("dead",) for p in st["plants"].values())]
    if not free:
        return "There is no room in the bed — every slot has something in it. You would have to clear one first."
    if month not in cat["sow"]:
        return (f"You shake out a few seeds of {pk['species'].replace('_', ' ') if pk['labelled'] else 'something unlabelled'} "
                f"into your palm, but this is not their season; you fold the packet and put it back.")
    if temp < cat["t_germ"] - 2:
        return (f"You crouch at the bed with the packet open. The soil is cold under your hand — too cold yet for this seed "
                f"to do anything but rot. You put it back in the tin.")
    slot = free[0]
    now = time.time()
    pid = f"garden_plant_{pk['species']}_{random.randrange(16**4):04x}"
    st["plants"][pid] = {"id": pid, "species": pk["species"], "slot": slot, "pos": _BED_SLOTS[slot], "stage": "seed", "vigour": 0.5,
                         "height": 0.0, "moisture": st.get("moisture", 0.5), "age_days": 0, "sown_ts": now, "germ_ts": None,
                         "stage_ts": now, "last_cut_ts": 0, "cuts": 0, "pests": 0.0, "frost_burn": 0.0,
                         "origin": "sown_by_du", "history": [{"ts": now, "event": "sown_by_du"}]}
    pk["count"] -= 8
    if pk["count"] <= 0:
        packs.remove(pk)
    _register_all()
    # SOUND WORLD EXPANSION §1 (2026-08-29, J-0377): real act-site timestamp for sow_dig.
    st["last_sow_ts"] = now
    _log(_LEDGER, {"deed": "sow", "species": pk["species"], "labelled": pk["labelled"], "slot": slot})
    _save(force=True)
    what = pk["species"].replace("_", " ") if pk["labelled"] else "the unlabelled seed"
    return (f"You draw a shallow drill with your finger and sow {what} along it, firm the soil over, and mark the row with a "
            f"stick. Now it is up to the soil and the weather.")


def water(txt: str = "") -> str:
    _cross("at_the_bed")
    st = _load()
    if _where() != "garden":
        return ""
    m = float(st.get("moisture", 0.5))
    b = float(st.get("barrel", 0))
    can = st["items"].get("watering_can", {})
    if not (can.get("carried") or can.get("place") == "garden"):
        return "You have nothing to carry water in — the can is not here."
    if b < 0.08:
        return "You go to the barrel and turn the tap: a trickle, then nothing. The barrel is dry. It needs rain."
    st["barrel"] = round(max(0.0, b - 0.15), 3)
    # SOUND WORLD EXPANSION §1 (2026-08-29, J-0377): real act-site timestamp for bed_watering —
    # the can's spatter, wherever the watering actually happens (both branches below water the bed).
    st["last_water_ts"] = time.time()
    if m > 0.85:
        st["moisture"] = 1.0
        _log(_LEDGER, {"deed": "water", "needed": False})
        _save(force=True)
        return "You water the bed, but the soil was already wet through; it pools on the surface and stands there."
    st["moisture"] = round(min(1.0, m + 0.45), 3)
    _log(_LEDGER, {"deed": "water", "needed": m < 0.4})
    _save(force=True)
    return ("You fill the can at the barrel and water the bed, soaking the pale dry soil until it darkens — it had been thirsty."
            if m < 0.4 else "You fill the can at the barrel and water the bed; the soil drinks it in.")


def fill_barrel_from_spring(txt: str = "") -> str:
    """Carry a vessel down to the spring in the wood, fill it, and lug it back to top up the rain
    barrel — the barrel itself only ever fills from real rain (see advance()), so this is the one
    way its level is ever raised on purpose. One trip is one vessel-load; several trips are needed
    to fill an empty barrel, same as a real bucket run. The oak bucket holds more per trip than the
    watering can (0.25 vs 0.15) — a real bucket is bigger than a watering can.
    Founder ask, 2026-08-29 (the barrel had gone dry and stayed dry with no rain in sight)."""
    try:
        st = _load()
        t = (txt or "").lower()
        has_bucket = st["items"].get("water_bucket", {}).get("carried")
        has_can = st["items"].get("watering_can", {}).get("carried")
        wants_can = ("can" in t or "watering can" in t) and "bucket" not in t
        if wants_can and has_can:
            vessel, amount, word = "watering_can", 0.15, "can"
        elif has_bucket:
            vessel, amount, word = "water_bucket", 0.25, "bucket"
        elif has_can:
            vessel, amount, word = "watering_can", 0.15, "can"
        else:
            return "You have nothing to carry water in — the bucket and the can are both back at the garden."
        try:
            from core import sensorium as _s
            _s._cross("at_the_spring", "")
        except Exception:
            pass
        b = float(st.get("barrel", 0))
        new_b = round(min(1.0, b + amount), 3)
        st["barrel"] = new_b
        _log(_LEDGER, {"deed": "fill_barrel_spring", "vessel": vessel, "amount": amount, "barrel_after": new_b})
        _save(force=True)
        level_note = ("brimming now" if new_b > 0.9 else "filling up" if new_b > 0.4 else "still low, more trips needed")
        return (f"You carry the {word} down through the wood to the spring, hold it under the pipe in the bank "
                f"until it brims, and lug it back up, heavy, to tip into the rain barrel — {level_note}.")
    except profile.NonLiveWriteError:
        # J-0726: let D-0179's hard-raise (guard_path(), F-1024) reach act_from_thought()'s own
        # caller instead of being swallowed by the broader except below.
        raise
    except Exception:
        return ""


def dig(txt: str = "") -> str:
    """Turn over a patch of the bed (2026-08-30, D-0100 Tier 2 — mined from his own refused reaching:
    3 unanswered dig deeds; the garden had water/sow/weed but no earthworks). Real consequences both
    ways: turned soil buries the chickweed (weeds down) and opens the ground (moisture evaporates a
    little faster from a fresh-dug surface). Wants the trowel or the fork to hand."""
    _cross("at_the_bed")
    st = _load()
    if _where() != "garden":
        return ""
    it_trowel, it_fork = st["items"].get("trowel") or {}, st["items"].get("hand_fork") or {}
    if not (it_trowel.get("carried") or it_trowel.get("place") == "garden"
            or it_fork.get("carried") or it_fork.get("place") == "garden"):
        return "You would want the trowel or the fork to hand for digging."
    wet = float(st.get("moisture", 0.4))
    if wet > 0.85:
        return "The bed is waterlogged; digging now would only make a puddled mess of it. Let it drain."
    tool = "fork" if (it_fork.get("carried") or it_fork.get("place") == "garden") else "trowel"
    st["weeds"] = round(max(0.0, float(st.get("weeds", 0)) - 0.3), 3)
    st["moisture"] = round(max(0.0, wet - 0.05), 3)
    st["dug_ts"] = time.time()
    _save(force=True); _log(_LEDGER, {"deed": "dig", "tool": tool})
    try:   # THE LIVING WORLD (J-0513): a deed draws its takers (life.note_deed)
        from core import life as _life; _life.note_deed("dig", "garden")
    except profile.NonLiveWriteError:
        # J-0726: dig()'s own _save(force=True)/_log() above are unwrapped and already raise — but
        # this life.note_deed() write attempt was still silently swallowed here first (mirrors
        # J-0727's whittle() fix; life.note_deed() re-raises this itself too, this job's own fix).
        raise
    except Exception:
        pass
    try:   # SOIL LIFE (2026-09-03, J-0505): worms in the turned earth only when the population is up
        from core import garden_soil as _soil
        worm = _soil.dig_worms_line()
    except Exception:
        worm = " A worm curls away from the light and you tip it back into the dark." if random.random() < 0.3 else ""
    return (f"You turn the {tool} through a stretch of the bed, lifting and breaking the clods, burying the "
            f"chickweed as you go. The turned earth is darker than the surface, and smells of itself.{worm}")


# THE RESTLESSNESS IDIOM (2026-09-03, J-0522, F-0719). Du's most-repeated figure — "sick of turning over the
# same dead ground / the same stones in my head" — carries dig's own vocabulary as its VEHICLE. Bare "turn"
# was dropped from the family (core/actions.py), which removes every shape the 6,306-thought corpus has
# produced; this is the hand's own veto for the one that grammar cannot close: a present-tense "I must turn
# over the same dead ground again" (0 corpus occurrences so far; the participle form "turning over" appears
# ~12 times and never matched). Clause-scoped, so "…turning over the same dead ground in my head; let me dig
# the bed instead" still digs. A hand-level test, not a shared-grammar frame, on purpose: adding this idiom
# to literal_will._M_FRAMES was tried and measured (isolated full-corpus replay, J-0522) — it demoted 108
# real MOVE and 32 LOOK decisions to GRAY, because restlessness is exactly when he walks. Precedent for a
# hand enforcing a rule the family table cannot express: core/expression.py's first-person veto (F-0578).
_RESTLESS_IDIOM = re.compile(r"\b(dead ground|same ground|same old ground|same stones?|(in|inside) my head)\b")


def _wills_dig(t: str) -> bool:
    """Does this thought will the DIG deed — a dig verb reaching a dig object in a clause that is not the
    restlessness idiom? Grammar READ from the one table (core/actions.py) — a second hand-kept copy of the
    verb list here is the exact drift F-0554 was about, and it had already happened once (bare "turn")."""
    from core import actions as _ac, hands as _h2
    _dig = _ac.BY_FAMILY["dig"]
    for cl in re.split(r"(?<=[.!?;])\s+", t or ""):
        if _RESTLESS_IDIOM.search(cl):
            continue
        if _h2.wants(cl, _dig.verbs, _dig.objects):
            return True
    return False


def _wills(t: str, family: str, *, loose: bool = True) -> bool:
    """Does this thought will `family`'s deed? Grammar READ from the one table (core/actions.py) — the
    derivation _wills_dig() introduced (J-0522), extended 2026-09-04 (J-0543, F-0738) to every family this
    module hosts that still carried its own hand-kept copy. `loose` keeps the module-local _wants_loose()
    retry (J-0184: object anywhere in the thought when the strict same-clause test misses) for the hands
    that always had it; feed_birds and the trap never did and stay strict. Fail-closed on an unknown family."""
    try:
        from core import actions as _ac, hands as _h2
        a = _ac.BY_FAMILY[family]
    except Exception:
        return False
    return _h2.wants(t, a.verbs, a.objects) or (loose and _wants_loose(t, a.verbs, a.objects))


# The trap family is one row in the table but three hands here (check / set / spring). This is the ONLY thing
# declared locally: which of the table's verbs each hand answers. The verbs themselves come from the table —
# a verb added there and not claimed here is reported by grammar_audit() (and fails the derivation test),
# never silently routed; a verb claimed here that the table no longer has is simply never matched.
_TRAP_HANDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("check", ("check", "look in", "inspect", "empty", "clear")),
    ("set", ("set", "bait", "arm", "lay", "reset")),
    ("unset", ("spring", "disarm", "unset")),
)


def _trap_verbs(sub: str) -> tuple:
    """The table's trap verbs this sub-hand answers — table order, table membership."""
    try:
        from core import actions as _ac
        claimed = dict(_TRAP_HANDS).get(sub, ())
        return tuple(v for v in _ac.BY_FAMILY["trap"].verbs if v in claimed)
    except Exception:
        return ()


def _wills_trap(t: str) -> str | None:
    """Which trap hand (if any) this thought wills: 'check' | 'set' | 'unset' | None. Strict same-clause
    grammar only, as the three hands always were; first hand in _TRAP_HANDS order wins, as before."""
    try:
        from core import actions as _ac, hands as _h2
        objs = _ac.BY_FAMILY["trap"].objects
    except Exception:
        return None
    for sub, _ in _TRAP_HANDS:
        if _h2.wants(t, _trap_verbs(sub), objs):
            return sub
    return None


# TOOL (2026-09-06, J-0569 / F-0783's follow-up). One row in the table, two hands here (take / put-down) —
# same shape as trap. The old hand-kept version checked verb PHRASES ONLY, with no object at all ("take the
# X" for any X), so it never actually read the table's real object list (trowel/fork/watering can/tin/twine/
# stakes/pot/bucket/netting/shears); take()/put() then did their own precise item lookup from _WORDS, which
# is why nothing ever broke live — 299 of the 302 corpus thoughts the old test matched were Du's own
# restlessness idiom ("i leave the abstract river logic behind", "i set down my pen") reaching a garden tool
# hand it had no business reaching. 'leave' is deliberately NOT one of the claimed verbs below (it is the
# single largest source of that drift: "leave the X" reads as walking away from X, not setting X down, in
# the overwhelming majority of its corpus uses) — the table never had it as a tool verb either.
_TOOL_HANDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("take", ("pick up", "take", "fetch", "carry", "bring", "grab")),
    ("put", ("set down", "put down")),
)


def _tool_verbs(sub: str) -> tuple:
    """The table's tool verbs this sub-hand answers — table order, table membership."""
    try:
        from core import actions as _ac
        claimed = dict(_TOOL_HANDS).get(sub, ())
        return tuple(v for v in _ac.BY_FAMILY["tool"].verbs if v in claimed)
    except Exception:
        return ()


def _wills_tool(t: str) -> str | None:
    """Which tool hand (if any) this thought wills: 'take' | 'put' | None. Strict same-clause grammar
    only — the old hand-kept version had no object check at all; first hand in _TOOL_HANDS order wins."""
    try:
        from core import actions as _ac, hands as _h2
        objs = _ac.BY_FAMILY["tool"].objects
    except Exception:
        return None
    for sub, _ in _TOOL_HANDS:
        if _h2.wants(t, _tool_verbs(sub), objs):
            return sub
    return None


# COMPOST (2026-09-06, J-0569 / F-0783's follow-up). One row, two hands: turning the heap (aerating it while
# it cooks) and spreading the FINISHED compost from the bottom of the heap onto the bed. Unlike trap/tool,
# the two hands do not partition the table's objects evenly — 'spread' only ever answered the bare object
# "compost", never "heap"/"compost heap" (spreading a whole heap makes no sense; you spread what has finished
# at its bottom), so that narrowing is kept as an explicit local rule, not re-widened to the full row. The
# hand-kept 'put' verb on the spread side is DROPPED, not moved: the full 9,791-thought corpus wills compost
# precisely ZERO times in either direction (its ten mentions are all ambient — "the hedgehog moves freely
# across the compost", "the blackbird cuts across the lawn... against the compost heap's rot" — never a will
# to turn or spread it), so there is no evidence 'put' was ever anything but a generic, undiscriminating verb
# a hand-kept copy accumulated; every other verb here already matches the table exactly.
_COMPOST_HANDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("spread", ("spread", "barrow", "fork in", "dig in")),
    ("turn", ("turn", "fork", "turn over", "fork over")),
)


def _compost_verbs(sub: str) -> tuple:
    """The table's compost verbs this sub-hand answers — table order, table membership."""
    try:
        from core import actions as _ac
        claimed = dict(_COMPOST_HANDS).get(sub, ())
        return tuple(v for v in _ac.BY_FAMILY["compost"].verbs if v in claimed)
    except Exception:
        return ()


def _wills_compost(t: str) -> str | None:
    """Which compost hand (if any) this thought wills: 'spread' | 'turn' | None. 'spread' is checked first
    and ONLY against the bare object "compost" (never "heap"/"compost heap" — spreading the whole heap is
    not a real deed; the finished stuff comes off its bottom), exactly as the hand-kept version always
    scoped it; 'turn' then gets the table's full object row. The verb VOCABULARY comes only from the table;
    this narrowing is the one thing still declared locally, same shape as trap's sub-hand partition."""
    try:
        from core import actions as _ac, hands as _h2
    except Exception:
        return None
    if _h2.wants(t, _compost_verbs("spread"), ("compost",)) and "heap" not in t.split("compost")[-1][:12]:
        return "spread"
    if _h2.wants(t, _compost_verbs("turn"), _ac.BY_FAMILY["compost"].objects):
        return "turn"
    return None


# WATER_FILL, the wood side (2026-09-06, J-0569 / F-0783's follow-up). One row, three hands total: the garden
# hand (fill_pail_at_barrel, plain _wills() — only one hand answers there, no split needed) and two in the
# wood, split here because they are physically different acts — carrying water UP to the barrel vs filling
# whatever he is holding directly AT the spring. The old hand-kept version keyed the barrel hand off the bare
# word "barrel" plus a loose OR of mostly non-verb words ("water", "bucket", "can" with no object check at
# all); this reads the same barrel/other split off the table's real verb list instead.
def _wills_water_fill_wood(t: str) -> str | None:
    """Which wood-side water_fill hand this thought wills: 'barrel' (fill_barrel_from_spring) | 'pail'
    (fill_pail_at_spring) | None. 'barrel' is the more specific ask and is checked first."""
    try:
        from core import actions as _ac, hands as _h2
        verbs = _ac.BY_FAMILY["water_fill"].verbs
        objs = _ac.BY_FAMILY["water_fill"].objects
    except Exception:
        return None
    if _h2.wants(t, verbs, ("barrel",)):
        return "barrel"
    if _h2.wants(t, verbs, tuple(o for o in objs if o != "barrel")):
        return "pail"
    return None


# The families whose grammar act_from_thought() READS from core/actions.py (no local copy) — every family
# _GARDEN_FAMILIES lists, as of 2026-09-06 (J-0569 / F-0783's follow-up: collect, mow, stake, net, save_seed,
# tool, ash_out, water_fill and compost derived alongside J-0543's harvest/sow/weed/water/feed_birds/trap and
# J-0522's dig). No hand-kept verb/object tuple for a garden family remains anywhere in this module.
_DERIVED_FAMILIES: tuple[str, ...] = ("harvest", "sow", "weed", "water", "dig", "feed_birds", "trap",
                                      "collect", "mow", "stake", "net", "save_seed", "tool", "ash_out",
                                      "water_fill", "compost")


def grammar_audit() -> dict:
    """What this module derives from core/actions.py, and any seam where the derivation could still drift:
    a derived family the table no longer has, or (trap/tool/compost) a sub-hand verb partition out of sync
    with its table row. Read by scripts/_test_garden_grammar_derivation.py; empty lists are healthy."""
    try:
        from core import actions as _ac
        out = {"derived_families": list(_DERIVED_FAMILIES),
               "derived_missing_from_table": [f for f in _DERIVED_FAMILIES if f not in _ac.BY_FAMILY]}
        for fam, hands_tbl in (("trap", _TRAP_HANDS), ("tool", _TOOL_HANDS), ("compost", _COMPOST_HANDS)):
            table = set(_ac.BY_FAMILY[fam].verbs)
            claimed = {v for _, vs in hands_tbl for v in vs}
            out[f"{fam}_unclaimed_in_table"] = sorted(table - claimed)
            out[f"{fam}_claimed_not_in_table"] = sorted(claimed - table)
        return out
    except Exception as exc:
        return {"error": repr(exc)[:120]}


def feed_birds(txt: str = "") -> str:
    """Scatter something for the birds by the bath (2026-08-30, D-0100 Tier 2 — the bird_bath item
    existed and did nothing). A pinch from the seed tin, so it has a real cost; the birds answer on
    their own terms — daylight, weather, and their own sweet time — never on his."""
    _cross("at_the_bed")
    st = _load()
    if _where() != "garden":
        return ""
    tin = st["items"].get("seed_tin") or {}
    if not (tin.get("carried") or tin.get("place") == "garden"):
        return "The seed tin is not out here to scatter from."
    from core import sensorium as _s
    weather = _s.state.get("weather", "")
    if any(k in weather for k in ("storm", "thunder")):
        return "You scatter a pinch by the bath, but nothing is flying in this; the seed sits dark on the wet stone."
    _save(force=True); _log(_LEDGER, {"deed": "feed_birds"})
    try:   # THE LIVING WORLD (J-0511): the seed draws its takers for two hours (sparrows, tauhou, the blackbird)
        from core import life as _life; _life.note_deed("feed_birds", "garden")
    except profile.NonLiveWriteError:
        # J-0726: feed_birds()'s own _save(force=True)/_log() above are unwrapped and already raise —
        # but this life.note_deed() write attempt was still silently swallowed here first (mirrors
        # J-0727's whittle() fix; life.note_deed() re-raises this itself too, this job's own fix).
        raise
    except Exception:
        pass
    r = random.random()
    if any(k in weather for k in ("rain", "drizzle")):
        return ("You scatter a pinch of seed on the stump by the bath. Nothing comes while you stand there — "
                "but the rain eases, and something will find it.")
    if r < 0.45:
        return ("You scatter a pinch of seed by the bath and step back. Inside a minute a blackbird drops to the "
                "stump, quick and businesslike, watching you between every peck.")
    if r < 0.65:
        return ("You scatter seed by the bath. A waxeye works the stump the moment your back is half-turned — "
                "there, gone, there again.")
    return ("You scatter a pinch by the bath. The garden holds still around it; the birds keep to the wall, "
            "not fooled into hurry. It will go by evening all the same.")


def weed(txt: str = "") -> str:
    _cross("at_the_bed")
    st = _load()
    if _where() != "garden":
        return ""
    w = float(st.get("weeds", 0))
    weeds = [p for p in st["plants"].values() if CATALOGUE[p["species"]]["kind"] == "weed" and p.get("slot") is not None and p["stage"] != "dead"]
    if w < 0.15 and not weeds:
        return "You go over the bed, but it is clean; nothing to pull."
    now = time.time()
    for p in weeds:
        _set_stage(p, "dead", now, "pulled_by_du")
    st["weeds"] = round(max(0.0, w - 0.5), 3)
    _log(_LEDGER, {"deed": "weed", "pulled": [p["species"] for p in weeds]})
    try:   # SOIL LIFE (2026-09-03, J-0505): the pulled weeds go on the heap
        from core import garden_soil as _soil
        _soil.add_material("weeds", 0.05 + 0.03 * len(weeds))
    except profile.NonLiveWriteError:
        # J-0818: let D-0179's hard-raise (guard_path(), F-1024) reach act_from_thought()'s own
        # already-safe outer carve-out (J-0714) instead of being swallowed here first (F-1175).
        raise
    except Exception:
        pass
    _save(force=True)
    names = ", ".join(_wname(p) for p in weeds[:3])
    return (f"You work along the bed on your knees pulling {names or 'the small weeds'} out by the root, and pile them at the "
            f"edge. The soil round the plants is bare and open again.")


def take(txt: str) -> str:
    """Pick up a carryable item where he stands; it travels with him."""
    st = _load()
    t = (txt or "").lower()
    for key, words in _WORDS.items():
        if key in _CARRYABLE and any(w in t for w in words):
            it = st["items"][key]
            if it.get("carried"):
                return f"You already have {it['name']} with you."
            if it["place"] != _where():
                return ""
            try:
                from core import garden_life as _gl
                if _where() == "garden" and _gl.hidden_in_grass(key):
                    return f"You look for {it['name'].split(',')[0]} where you left it, but the grass is long and you cannot find it in it."
            except Exception:
                pass
            it["carried"] = True
            it.setdefault("history", []).append({"ts": time.time(), "event": f"picked_up_by_du_at_{_where()}"})
            _log(_LEDGER, {"deed": "take", "item": key, "where": _where()})
            _save(force=True)
            return f"You pick up {it['name']} and take it with you."
    return ""


def put(txt: str) -> str:
    """Set a carried item down where he stands (the garden, the study, the shore, the wood)."""
    st = _load()
    t = (txt or "").lower()
    here = _where()
    from core import inventory as _inv
    for key in _inv.carried(st["items"]):
        if any(w in t for w in _WORDS.get(key, ())) or "everything" in t:
            it = st["items"][key]
            it["carried"] = False
            it["place"] = here
            pos = _standpoint_pos(here) or it["pos"]
            it["pos"] = pos
            it.setdefault("history", []).append({"ts": time.time(), "event": f"set_down_by_du_at_{here}"})
            _place(it["id"], pos, here, f"set down by Du at {here}")
            try:
                from core import world_substrate as _ws
                _ws.update_location(it["id"], here)
            except profile.NonLiveWriteError:
                # J-0726: let D-0179's hard-raise (guard_path(), F-1024) reach this function's own
                # caller instead of being swallowed here — put()'s own _log()/_save() a few lines
                # below are unwrapped and would raise anyway, but not before silently skipping this
                # world_substrate location sync (mirrors J-0727's whittle() fix in fieldcraft.py).
                raise
            except Exception:
                pass
            _log(_LEDGER, {"deed": "put", "item": key, "where": here})
            _save(force=True)
            return f"You set {it['name']} down here."
    return ""


def stake(txt: str = "") -> str:
    _cross("at_the_bed")
    st = _load()
    if _where() != "garden":
        return ""
    stakes, twine = st["items"].get("stakes", {}), st["items"].get("twine", {})
    here = lambda it: it.get("carried") or it.get("place") == "garden"
    if not here(stakes):
        return "You have nothing to stake them with — the bundle of stakes is not here."
    if not here(twine):
        return "You have the stakes but nothing to tie with; the twine is not here."
    cands = [p for p in st["plants"].values() if CATALOGUE[p["species"]].get("needs_stake") and p["stage"] not in ("seed", "dead") and p["id"] not in st.get("staked", [])]
    if not cands:
        return "Nothing in the bed wants staking just now."
    p = cands[0]
    st.setdefault("staked", []).append(p["id"]); p["flopped"] = False
    p.setdefault("history", []).append({"ts": time.time(), "event": "staked_by_du"})
    _log(_LEDGER, {"deed": "stake", "species": p["species"], "plant": p["id"]}); _save(force=True)
    return f"You push stakes in along {CATALOGUE[p['species']]['names'][0]} and tie the stems up loosely with twine. They stand."


# NET / UN-NET: ANSWER WHAT THE WORLD HOLDS (2026-10-03, J-1680 / F-2252). net() used to pick the un-net
# direction with a bare substring test over the WHOLE thought+intention ("off" in txt) and never asked whether
# the bed was netted: Du's purely descriptive 2026-09-28 thought ("...the cold eases off me, watching the low
# west light stretch across the thyme bed...") was answered "You lift the netting off the bed..." and logged as
# {"deed": "unnet"} for a bed that was never netted -- a world-truth contamination hit (plan garden_upgrade
# section 3 metric 5) and the only net-family ledger row the garden has ever had. Two changes, in this hand
# only (the family gate in core/actions.py and core/hands.py are untouched): (1) the direction is read from
# WHOLE WORDS inside the clause(s) that carry the family's own verb -- never a substring of another word
# ("coffee", "often", "offer") nor an 'off' from a different sentence; (2) a transition is claimed, logged and
# moved ONLY when the world is in the state it needs (lifting needs netting over the bed, stretching needs the
# bed bare) -- otherwise the hand answers what is true and writes nothing. Both real branches are unchanged.
# (Part (1)'s evidence words were replaced the same day by J-1749, below: the direction is now the verb's own.)
#
# THE AGENT GUARD AND THE VERB-BOUND DIRECTION (2026-10-03, J-1749 / F-2378; restart-gated like J-1680). Two things
# still stood in front of net(). (1) The family gate (the net row in core/actions.py, read by core/hands.py) is a
# verb reaching a bed/seedlings/netting object and nothing more, so ordinary DESCRIPTIVE prose still reached this
# hand and netted the bed for real: "The long shadows stretch across the bed." was answered "You untangle the
# netting ... stretch it over the bed" with a net ledger row (F-2378 residual a; the 09-28 sentence was the one
# corpus case in 603 net-family clauses). (2) The direction was read from the bare words "off" / "remove" /
# "take the net(ting)" anywhere in the verb's sentence, so "I take the netting and stretch it over the bed." read
# un-net, "I lift the netting from the bed." read net (lift was never un-net evidence) and Du's genuine "untangle
# that bird netting lying far off" read un-net from the word "off" (F-2378 b, d, e). Both are fixed here, in this
# hand only, and SHIP TOGETHER: the direction rule alone would turn the 09-28 sentence from the honest "no netting
# to lift" line into a real net. The net row in core/actions.py, core/hands.py, core/literal_will.py and
# core/dispatch.py are untouched and the verb table is NOT widened (untangle / secure is D-0344's call).
#   GUARD. Same precedent as dig's _RESTLESS_IDIOM / _wills_dig (J-0522): a hand enforcing a rule the shared grammar
#   cannot express. A net-family VERB OCCURRENCE counts only when its own sentence shows an agent willing it; the
#   hand declines (nothing written, nothing moved) when no occurrence counts. An occurrence FAILS when the text
#   before it in its sentence ends in a determiner plus up to three free words [np_subject: "the long shadows
#   stretch"]; in a perception verb plus one to five free words [perception: "watching the light stretch"]; in
#   "too X to" / "refuse to" / "unable to" ... [refusal]; in an urge/pull/tug/itch ... "to" with no comma or
#   semicolon between [felt_want: "the urge to untangle"]; or the verb is stretch/lift/cover directly followed by
#   across/along/over/... [intransitive: "stretch across the bed" is light, not netting; "stretch it over the
#   bed" has a pronoun and passes]. "my" is NOT a determiner here ("my hands stretch the netting" is an agent).
#   KNOWN RESIDUALS (documented, not fixed; 0 corpus hits each): "I stretch my arms across the bed." passes
#   (agent plus body object), and "I lift up the netting" is vetoed by the intransitive rule ("lift the netting
#   up" passes). Verbs and objects are READ from core/actions.py; only the veto vocabulary is declared here.
#   DIRECTION. The direction of the occurrence that PASSED: lift and take off (contiguous, or split as "take the
#   netting off") = un-net, every other table verb = net; the LAST passing occurrence in the first sentence that
#   has one decides; the default is net. Bare off / remove / "take the net(ting)" are no longer evidence.
_NET_DETS = r"(?:the|a|an|that|this|those|these|its|his|her|their|our|your|some|any|every|each)"
_NET_STOPS = (r"(?:and|then|but|or|so|to|that|which|while|as|with|from|into|of|in|on|at|by|for|when|if|because|until|"
              r"before|after|where|who|than|though|yet|nor|i|we|me|us)")
_NET_FREE = r"(?:(?!" + _NET_STOPS + r"\b)[a-z'’-]+\s+)"        # a "free word": any word that is not a clause-joiner or a subject pronoun
_NET_NP_SUBJECT = re.compile(r"\b" + _NET_DETS + r"\s+" + _NET_FREE + r"{0,3}$")
_NET_PERCEPTION = re.compile(r"\b(?:watch|watches|watching|watched|see|sees|seeing|saw|seen|notice|notices|noticing|noticed|"
                             r"feel|feels|feeling|felt|hear|hears|hearing|heard|observe|observes|observing|observed)\s+"
                             + _NET_FREE + r"{1,5}$")
_NET_REFUSAL = re.compile(r"(?:too\s+\w+\s+to|refus\w*\s+to|unable\s+to|unwilling\s+to|reluctant\s+to|afraid\s+to|not\s+ready\s+to)\s+$")
_NET_FELT_WANT = re.compile(r"\b(?:urge|urges|urging|pull|pulls|pulled|tug|tugs|tugging|temptation|itch|longing|impulse)\b"
                            r"[^.!?;,]{0,60}?\bto\s+$")
_NET_INTRANSITIVE_AFTER = re.compile(r"^\s+(?:across|along|over|through|above|toward|towards|up|down|out|away|around)\b")
_NET_INTRANSITIVE_VERBS = ("stretch", "lift", "cover")
_NET_UNNET_VERBS = ("lift", "take off")                                  # every other table verb points the net direction


def _net_guard_veto(pre: str, post: str, verb: str) -> str:
    """Why one net-family verb occurrence is NOT an agent's will -- "" when it passes. `pre` is the text of its
    own sentence before the verb word, `post` the text after it, `verb` the verb word itself (a phrasal verb's head)."""
    if _NET_NP_SUBJECT.search(pre):
        return "np_subject"
    if _NET_PERCEPTION.search(pre):
        return "perception"
    if _NET_REFUSAL.search(pre):
        return "refusal"
    if _NET_FELT_WANT.search(pre):
        return "felt_want"
    if verb in _NET_INTRANSITIVE_VERBS and _NET_INTRANSITIVE_AFTER.search(post):
        return "intransitive"
    return ""


def _net_reads(t: str) -> list:
    """Every net-family verb occurrence the grammar reads in thought `t`, in text order, as
    (pos, sentence_start, table_verb, veto) where veto == "" means it passes the agent guard. The grammar is the
    one _wills()/_wants_loose() read -- the table's verbs (core/actions.py's net row), the same word boundaries,
    literal_will's noun rule ("the stretch") and core.hands._blocked per occurrence -- so nothing counts here that
    the gate would not already have read; a phrasal verb ("take off") counts at its head word, contiguous
    ("take off the netting") or split ("take the netting off", hands._wants_split on the head's own clause tail).
    Sentence = hands._clause_at's own boundary (. ; ! ?). Fail-closed: no readable table -> no occurrence."""
    try:
        from core import actions as _ac, hands as _h2
        a = _ac.BY_FAMILY["net"]
    except Exception:
        return []
    try:   # J-0554: the verb-is-a-verb rule every other reader of this grammar applies (no noun "the stretch")
        from core.literal_will import _NOT_NOUN as _nn
    except Exception:
        _nn = ""
    t = (t or "").lower()

    def _sentence(pos: int) -> tuple:     # (start, end) of the sentence around pos -- hands._clause_at's own boundary
        s = max((t.rfind(c, 0, pos) for c in ".;!?"), default=-1) + 1
        return s, s + len(_h2._clause_at(t, pos))

    found: dict = {}
    for v in a.verbs:
        vl = v.lower()
        head = vl.split()[0]
        spots = {m.start() for m in re.finditer(_nn + r"(?<![a-z-])" + re.escape(vl) + r"(?![a-z-])", t)}
        if " " in vl:
            for m in re.finditer(r"(?<![a-z-])" + re.escape(head) + r"(?![a-z-])", t):
                if _h2._wants_split(t[m.start():_sentence(m.start())[1]], vl, a.objects, False):
                    spots.add(m.start())
        for pos in spots:
            if _h2._blocked(t, pos):
                continue
            sstart = _sentence(pos)[0]
            found[(pos, vl)] = (pos, sstart, vl, _net_guard_veto(t[sstart:pos], t[pos + len(head):], head))
    return [found[k] for k in sorted(found)]


def _wills_net(t: str) -> bool:
    """Does this thought will the NET deed -- the table-derived grammar (_wills: strict hands.wants OR the J-0184
    _wants_loose retry) AND at least one verb occurrence that passes the agent guard? Only ever narrows what
    _wills(t, "net") reads: a will that was not read before is not read now. Fail-closed, as _wills() is."""
    try:
        return _wills(t, "net") and any(not r[3] for r in _net_reads(t))
    except Exception:
        return False


def _net_direction(t: str) -> str:
    """Which way a net-family will points: "unnet" or "net" (the default, as it always was) -- the direction of
    the verb occurrence that PASSED the agent guard: lift and take off = un-net, every other table verb = net;
    the last passing occurrence in the first sentence that has one decides (see the J-1749 block above)."""
    try:
        passing = [r for r in _net_reads(t) if not r[3]]
        if not passing:
            return "net"
        last = [r for r in passing if r[1] == passing[0][1]][-1]
        return "unnet" if last[2] in _NET_UNNET_VERBS else "net"
    except Exception:
        return "net"


def _netted_now(st: dict, it: dict) -> bool:
    """Is the bed netted RIGHT NOW? The world's own flag (the one bed_summary() tells him from, and advance()
    derives from the netting item on every tick) -- unless the roll is in his hands: take() picks the netting up
    without touching that flag, which only refreshes on the next world tick, and a roll in his hands is not over
    the bed."""
    return bool(st.get("netted")) and not it.get("carried")


def _no_netting_over_bed_line(it: dict) -> str:
    """The honest answer to a will to lift netting off a bed that has none over it. Says where the roll is only
    when that is verifiably so (in his hands; at its rest spot by the wall -- _ITEMS' creation position, where the
    un-net branch of net() also leans it) and says nothing about its whereabouts otherwise."""
    tail = ""
    try:
        if it.get("carried"):
            tail = "; the roll is in your hands"
        elif math.dist(list(it.get("pos") or [])[:2], [7.2, 1.5]) < 0.5:
            tail = "; the roll lies by the wall"
    except Exception:
        tail = ""
    return "There is no netting over the bed to lift off" + tail + "."


def net(txt: str = "") -> str:
    _cross("at_the_bed")
    st = _load()
    if _where() != "garden":
        return ""
    it = st["items"].get("netting", {})
    if not (it.get("carried") or it.get("place") == "garden"):
        return "The netting is not here."
    # J-1680 / F-2252: ask the world before claiming a transition -- see the block above _net_direction(). The
    # two honest returns below write no ledger row and move nothing; the two real branches are what they were.
    over_bed = _netted_now(st, it)
    if _net_direction(txt) == "unnet":
        if not over_bed:
            return _no_netting_over_bed_line(it)
        it["pos"] = [7.2, 1.5, 0.0]; st["netted"] = False
        _log(_LEDGER, {"deed": "unnet"}); _save(force=True)
        return "You lift the netting off the bed, roll it, and lean it against the wall."
    if over_bed:
        return "The netting is already stretched over the bed."
    it["carried"] = False; it["place"] = "garden"; it["pos"] = [5.5, 5.5, 0.6]
    st["netted"] = True
    it.setdefault("history", []).append({"ts": time.time(), "event": "stretched_over_the_bed_by_du"})
    _place(it["id"], it["pos"], "garden", "stretched over the raised bed")
    _log(_LEDGER, {"deed": "net"}); _save(force=True)
    return "You untangle the netting — it takes a while — and stretch it over the bed, pegging the edges with stones."


def save_seed(txt: str = "") -> str:
    _cross("at_the_bed")
    st = _load()
    if _where() != "garden":
        return ""
    cands = [p for p in st["plants"].values() if p["stage"] == "seeding" and CATALOGUE[p["species"]]["kind"] != "weed"]
    if not cands:
        return "Nothing in the bed has set seed yet; there is nothing to save."
    p = cands[0]; sp = p["species"]
    pk = {"species": sp, "labelled": True, "count": random.randint(15, 40), "year": time.localtime().tm_year, "saved_by_du": True, "from": p["id"]}
    st.setdefault("saved_seed", []).append(pk); st.setdefault("packets", []).append(pk)
    p.setdefault("history", []).append({"ts": time.time(), "event": "seed_saved_by_du"})
    _log(_LEDGER, {"deed": "save_seed", "species": sp, "plant": p["id"]}); _save(force=True)
    try:
        from core import keepsakes as _k, sensorium as _s
        _k.keep(f"twist of paper with {sp.replace('_', ' ')} seed you saved from the bed",
                location="garden", weather=_s.state.get("weather", ""), season=_s._season())
    except profile.NonLiveWriteError:
        # J-0895: keepsakes.record() never existed (hasattr always False, F-1252) so this branch was
        # dead and no saved-seed keepsake ever fired. The intent stands -- keep()'s own _WORLD_SHAPED
        # floor already lists "seed"/"seeds"/"packet"/"packets" as keepable, so this now calls the
        # real keep() (its _is_object() gate is not on this direct path, only on keep_act()/given_act(),
        # so the line lands as-is). keep() is fenced (J-0877) and raises non-live; let it reach
        # save_seed()'s own caller, act_from_thought(), which already carries the J-0714 carve-out at
        # its outer boundary, instead of this pre-existing broad except swallowing it.
        raise
    except Exception:
        pass
    return (f"You rub the dry heads of {CATALOGUE[sp]['names'][0]} between your palms over a sheet of paper, blow the chaff off, and "
            f"fold the seed into a twist of paper. You write the name on it. Next year's, if they keep.")


def fetch_from_drawer(txt: str = "") -> str:
    st = _load()
    if _where() != "study":
        return ""
    dr = st.get("drawer", [])
    if not dr:
        return "You open the drawer — no seed left in it."
    t = (txt or "").lower()
    named = [x for x in dr if x["species"].replace("_", " ") in t or x["species"] in t]
    pk = named[0] if named else dr[0]
    dr.remove(pk); st.setdefault("packets", []).append(pk)
    _log(_LEDGER, {"deed": "fetch_seed", "species": pk["species"]}); _save(force=True)
    return f"You take the packet of {pk['species'].replace('_', ' ')} from the drawer and put it in the seed tin."


# ── THE TRAP (2026-09-03, D-0130, J-0512) ────────────────────────────────────────────────────────
def _trap_st(st: dict) -> dict:
    return st.setdefault("trap", {"armed": False, "set_ts": 0.0, "where": None, "caught": None, "kills": 0, "bait_taken": False})


def set_trap(txt: str = "") -> str:
    """He sets the possum trap where he stands with it. The world does the rest at night (life_mammals.night_pass)."""
    try:
        st = _load(); it = st["items"].get("possum_trap") or {}
        if not (it.get("carried") or it.get("place") == "garden"):
            return "The trap is not out here."
        tr = _trap_st(st)
        if tr.get("caught"):
            return "The trap is sprung and not empty. Deal with what is in it first."
        if tr.get("armed"):
            return "The trap is already set; the plate is up and the jaws are open. Best not to fiddle with it."
        tr.update({"armed": True, "set_ts": time.time(), "where": "under_the_tree" if it.get("carried") else "by_the_wall", "bait_taken": False})
        it["carried"] = False; it["place"] = "garden"
        _save(force=True); _log(_LEDGER, {"deed": "set_trap", "where": tr["where"]})
        return ("You set the trap under the tree, working the spring back with both hands until the plate catches, and lay it "
                "in the leaf-litter where the wall meets the trunk. The jaws stand open. Whatever comes down that trunk tonight will find it.")
    except profile.NonLiveWriteError:
        # J-0726: let D-0179's hard-raise (guard_path(), F-1024) reach act_from_thought()'s own
        # caller instead of being swallowed by the broader except below.
        raise
    except Exception as exc:
        logger.debug("[garden] set_trap failed: %s", exc)
        return ""


def unset_trap(txt: str = "") -> str:
    try:
        st = _load(); tr = _trap_st(st)
        if tr.get("caught"):
            return "It is already sprung — and not on nothing."
        if not tr.get("armed"):
            return "The trap is not set."
        tr["armed"] = False; _save(force=True); _log(_LEDGER, {"deed": "unset_trap"})
        return "You spring the trap with a stick from arm's length; the jaws snap on the wood with a crack you feel in your teeth. It lies harmless."
    except profile.NonLiveWriteError:
        # J-0726: let D-0179's hard-raise (guard_path(), F-1024) reach act_from_thought()'s own
        # caller instead of being swallowed by the broader except below.
        raise
    except Exception:
        return ""


def check_trap(txt: str = "") -> str:
    """The morning after. A kill is HIS deed: it goes through core/sitting.note_difficulty (the gate an owned plant
    death takes — D-0130's defeater is a trap with no weight) and is recorded as a carcass for J-0513."""
    try:
        st = _load(); tr = _trap_st(st)
        if tr.get("caught"):
            sp = str(tr["caught"].get("species") or "possum")
            when = float(tr["caught"].get("ts") or time.time())
            tr["kills"] = int(tr.get("kills", 0)) + 1
            tr["caught"] = None; tr["armed"] = False
            _save(force=True); _log(_LEDGER, {"deed": "check_trap", "found": sp})
            try:
                from core import life as _life
                _life._log(_life._LEDGER, {"kind": "kill", "key": sp, "place": "garden", "by": "trap", "when": when})
                ls = _life._load(); ls.setdefault("carcasses", []).append({"species": sp, "place": "garden", "where": tr.get("where") or "under_the_tree",
                                                                          "ts": when, "cause": "trap", "state": "fresh"})
                _life._save(force=True)
            except profile.NonLiveWriteError:
                # J-0726: let D-0179's hard-raise (guard_path(), F-1024) reach this function's own
                # caller instead of being swallowed here — check_trap()'s own _save()/_log() a few
                # lines above are unwrapped and already raise, but not before silently skipping this
                # life.py carcass/kill record (mirrors J-0727's whittle() fix in fieldcraft.py).
                raise
            except Exception:
                pass
            if sp == "hedgehog":
                line = ("The trap has sprung on the wrong animal. A hedgehog lies in it, curled as far as the jaws let it, quite dead; it must have "
                        "come along the wall for the bait in the night. You set the trap for the possum. You did not set it for this.")
                diff = ("the trap you set under the tree has killed the hedgehog — the one that worked the hedge bottom at night — not the possum you set it for")
            else:
                line = ("The trap has sprung. A possum lies in it, grey and heavy, the jaws across its neck; it is cold and stiff. Its claws are "
                        "full of bark. There are stripped buds under the tree from before it found the bait.")
                diff = "the trap you set under the tree has killed a possum — your hand did this, in the night, while you slept"
            try:
                from core import sitting as _sit
                _sit.note_difficulty(diff, kind="deed")
            except Exception:
                pass
            return line
        if tr.get("armed"):
            if tr.get("bait_taken"):
                return "The trap stands set, the jaws still open — but the bait is gone off the plate. Something took it and got clear."
            return "The trap stands set under the tree, jaws open, the bait untouched. Nothing came, or nothing came near enough."
        it = st["items"].get("possum_trap") or {}
        if it.get("carried"):
            return "The trap is in your hands, unset, the jaws shut."
        return "The trap lies by the wall, unset, its jaws shut and rusting."
    except profile.NonLiveWriteError:
        # J-0726: let D-0179's hard-raise (guard_path(), F-1024) reach act_from_thought()'s own
        # caller instead of being swallowed by the broader except below.
        raise
    except Exception as exc:
        logger.debug("[garden] check_trap failed: %s", exc)
        return ""


def _cross(sp: str) -> None:
    """CROSS-LINK (2026-08-22): a hand carries its own movement — the same mover every older hand uses."""
    try:
        from core import sensorium as _s
        if _s.state.get("location") == "garden":
            _s._cross(sp, "")
    except Exception:
        pass


def _standpoint_pos(place: str):
    try:
        from core import locomotion as _loco, spatial as _sp
        sp = _loco.position_standpoint(place)
        lay = _sp.layout(place) or {}
        return list((lay.get("standpoints") or {}).get(sp or "", {}).get("pos") or []) or None
    except profile.NonLiveWriteError:
        # J-0794: locomotion.position_standpoint() can now raise non-live (J-0778) -- re-raise rather
        # than a silent None. This function's own caller, put(), calls it unwrapped directly inside
        # act_from_thought()'s own outer try, already fixed to re-raise (J-0714), so no further layer
        # is needed for this to reach a real caller.
        raise
    except Exception:
        return None


def _wants_loose(text: str, verbs, objects) -> bool:
    """SCOPED RETRY (J-0184, F-0143/F-0145): core.hands.wants()'s clause-scoped gate requires the verb and its
    object word in the SAME CLAUSE ("You cut the rosemary" fires; "You go to the bed. You cut some for the
    rack." does not, because "cut" and "rosemary"/"bed" land in different sentences) -- when it misses, garden
    deeds were falling through to sensorium.py's un-instrumented old hands (whole-text substring matching, no
    ledger write). This is the same verb-with-word-boundaries + literal_will blocker check as wants(), but the
    object may land ANYWHERE in the whole thought rather than the same clause as the verb. Used ONLY as a
    fallback retry inside garden.py's own act_from_thought, local to this module -- core.hands.wants() itself
    is untouched and every other caller keeps the strict clause requirement. Zero LLM, fail-open."""
    try:
        import re as _re
        from core import hands as _h2
        t = (text or "").lower()
        if not t or not objects:
            return False
        try:   # J-0554: same verb-is-a-verb rule as hands.wants (no noun "the pull", no compound "spring-jawed")
            from core.literal_will import _NOT_NOUN as _nn
        except Exception:
            _nn = ""
        for v in verbs:
            for m in _re.finditer(_nn + r"(?<![a-z-])" + _re.escape(v.lower()) + r"(?![a-z-])", t):
                if _h2._blocked(t, m.start()):
                    continue
                # AN OBJECT IS A WORD TOO (2026-09-09, J-0822 / F-1180): this sat unmirrored from the
                # verb-side regex just above -- a hyphen after (or before) the object also makes it a
                # compound ("herb-bed" is not the bare object "bed"; "dream-water" is not the bare
                # object "water"), and without this the object side stayed permeable to exactly the
                # class of false match the verb side was already hardened against (same drift shape as
                # J-0787/F-1128 in hands.wants() and J-0800/F-1149 in literal_will.classify()). Both
                # sides of the boundary get the fix, matching the verb regex's own symmetric
                # (?<![a-z-])/(?![a-z-]) shape exactly.
                if any(_re.search(r"(?<![a-z-])" + _re.escape(o.lower()) + r"(?![a-z-])", t) for o in objects):
                    return True
        return False
    except Exception:
        return False


_GARDEN_FAMILIES = frozenset({"harvest", "collect", "mow", "stake", "net", "save_seed", "weed", "tool", "water", "sow",
                              "ash_out", "water_fill", "dig", "compost", "trap", "feed_birds"})   # the families core/actions.py binds here


def act_from_thought(thought: str, intention: str = "", family: str | None = None) -> str | None:
    """The garden's will→hand boundary. Returns the world's answer or None. Called before sensorium's old
    garden_act; '' from a hand means 'not here / not this', so the old path may still answer.

    FAMILY SCOPE (J-0554 / F-0761, 2026-09-04): when the dispatcher has already judged WHICH family he willed
    (`family=`), only that family's hands may answer. Before this a dispatched 'trap' deed ran the whole chain
    in order and the weeding hand answered it — 'pull' matched the noun in "the pull of that rusted trap".
    family=None (the legacy latch path, sensorium's own callers) keeps the full chain exactly as before; a
    family this chain does not host is treated the same way."""
    if not ENABLED:
        return None
    try:
        _load()
        _register_all()
        t = f"{thought} {intention}".lower()
        if family not in _GARDEN_FAMILIES:
            family = None
        _ok = (lambda fam: family is None or fam == family)
        if _where() == "garden":
            # ONE TABLE (2026-09-04, J-0543 / F-0738): harvest, sow, weed, water, feed_birds and trap READ their grammar
            # from core/actions.py through _wills() — the same derivation dig got on 09-03. Until now each carried its
            # own hand-tuned copy here, and every copy had drifted (F-0554's shape): weed's extra "them"/"out"
            # matched 15 corpus thoughts of the "the fire pulls me out of my head" idiom, water's extra "soak"/"it"/
            # "them" matched 79 ("the tide ... stone and water" + a stray "it"), harvest's "leaves" matched "the
            # air smells of damp earth and cut leaves" — none a will; while the table's own "sunflowers" (water) and
            # "garden"/"soil"/"roots" (sow) never reached the hand at all, so a dispatched DEED on them was declined
            # unanswered. The crops the garden really grows (chives, silverbeet, lettuce, radish) and the seed packet
            # moved INTO the table instead, where the gate can see them.
            if _ok("harvest") and _wills(t, "harvest"):
                r = harvest(t)
                if r:
                    return r
            if _ok("sow") and _wills(t, "sow"):
                r = sow(t)
                if r:
                    return r
            if _ok("weed") and _wills(t, "weed"):
                r = weed(t)
                if r:
                    return r
            if _ok("water") and _wills(t, "water"):
                r = water(t)
                if r:
                    return r
            # DIG / FEED THE BIRDS (2026-08-30, D-0100 Tier 2). dig's grammar is READ from the one table
            # (core/actions.py) rather than repeated here — a second hand-kept copy of the verb list is the
            # exact drift F-0554 was about, and it had already happened: bare "turn" was dropped from the
            # family 2026-09-03 (J-0522, F-0719: it fired on the "dead ground" restlessness idiom).
            if _ok("dig") and _wills_dig(t):
                r = dig(t)
                if r:
                    return r
            if _ok("feed_birds") and _wills(t, "feed_birds", loose=False):
                r = feed_birds(t)
                if r:
                    return r
            # SOIL LIFE (2026-09-03, J-0505; derived 2026-09-06, J-0569 / F-0783's follow-up): turn the heap;
            # barrow the finished compost to the bed. _wills_compost() partitions the table's one compost row
            # into the two hands — see its own docstring for the heap-suffix exclusion it preserves.
            if _ok("compost"):
                _csub = _wills_compost(t)
                if _csub == "spread":
                    from core import garden_soil as _soil
                    r = _soil.spread_compost(t)
                    if r:
                        return r
                elif _csub == "turn":
                    from core import garden_soil as _soil
                    r = _soil.turn_compost(t)
                    if r:
                        return r
            # THE TRAP (2026-09-03, D-0130, J-0512). Three hands, one family: the table's verbs are PARTITIONED by
            # _TRAP_HANDS (J-0543) — the verb lists themselves are read from core/actions.py, never repeated here.
            if _ok("trap"):
                _sub = _wills_trap(t)
                if _sub:
                    r = {"check": check_trap, "set": set_trap, "unset": unset_trap}[_sub](t)
                    if r:
                        return r
            # STAKE / NET (2026-09-06, J-0569 / F-0783's follow-up). stake's old extra objects "them" (a
            # pronoun — the same drift shape F-0783 already ruled on twice) and "stakes" (redundant with the
            # 'tool' family, which already owns picking the stake bundle up) matched zero corpus thoughts
            # either way and are dropped, not moved — the table row itself needed no change. net's old extra
            # object "net" is dropped: see its own comment in core/actions.py — it self-matched (verb "net"
            # and object "net" are the same word) and every one of its 16 real corpus hits was an unrelated
            # beach net at the tideline, never the garden's; its "take off"/"lift" verbs (reaching the un-net
            # branch below) moved INTO the table instead.
            if _ok("stake") and _wills(t, "stake"):
                r = stake(t)
                if r:
                    return r
            if _ok("net") and _wills_net(t):       # J-1749: _wills(t, "net") plus the agent guard -- prose cannot net the bed
                r = net(t)
                if r:
                    return r
            if family is None:
                try:   # FIELDCRAFT: the clothesline, the handrail, tinder, measuring, whittling, tracking, the coat on the line
                    from core import fieldcraft as _fc
                    _r = _fc.act_from_thought(thought, intention)
                    if _r:
                        return _r
                except profile.NonLiveWriteError:
                    # J-0726: fieldcraft.act_from_thought() re-raises this itself (J-0727) — do not
                    # let THIS forwarding call's catch-all swallow it a level higher, the same gap
                    # J-0714 already closed for the wood_life forward just below. Added later than
                    # J-0714's own pass because fieldcraft.py wasn't guarded/raising yet at that time
                    # (F-1045/F-1070) — found by this job's own systematic sweep.
                    raise
                except Exception:
                    pass
                try:   # WOOD LIFE: the lean-to work — split on the block, sharpen on the step, take the axe/saw/barrow
                    from core import wood_life as _wl
                    _r = _wl.act_from_thought(thought, intention)
                    if _r:
                        return _r
                except profile.NonLiveWriteError:
                    # J-0714: wood_life.act_from_thought() now re-raises this itself (its own outer
                    # except, fixed this same job) — do not let THIS forwarding call's catch-all
                    # swallow it a level higher, or garden.act_from_thought() would still look silent
                    # to a caller willing a wood deed while standing in the garden.
                    raise
                except Exception:
                    pass
            # COLLECT / WATER_FILL (garden) / ASH_OUT / MOW (2026-09-06, J-0569 / F-0783's follow-up): four
            # more hand-kept raw-substring tests replaced with the same table-derived _wills() every other
            # family here now uses. collect's old bare phrase "the box at the gate" (no verb at all) is
            # dropped — its one corpus hit ("the box at the gate is full, heavy with letters...") is Du
            # NOTICING the box, not willing to fetch it; the table's real verb+object grammar already covers
            # every phrase that IS a will. water_fill's old test matched not one of the 9,791 corpus thoughts
            # (it only recognised "fill the pail"/"fill the kettle" as fixed phrases, missing its own
            # documented bucket/barrel capability entirely) — every dispatched water_fill DEED was a dead end
            # at this hand until now. ash_out's old test required only bare "ash" plus any of a few words
            # including the bare word "garden" itself — nearly any ash-adjacent thought spoken while standing
            # in the garden matched regardless of verb; 48 of its 49 corpus hits were "the rain washes...
            # plato's forms... the garden" circling-thought imagery, never a deed. mow's copy was already
            # identical to the table.
            if _ok("collect") and _wills(t, "collect", loose=False):
                from core import supply as _sup
                r = _sup.collect_box()
                if r:
                    return r
            if _ok("water_fill") and _wills(t, "water_fill", loose=False):
                from core import study_life as _sl
                r = _sl.fill_pail_at_barrel()
                if r:
                    return r
            if _ok("ash_out") and _wills(t, "ash_out", loose=False):
                from core import study_life as _sl
                r = _sl.tip_ash_on_bed(t)
                if r:
                    return r
            if _ok("mow") and _wills(t, "mow", loose=False):
                from core import garden_life as _gl
                r = _gl.mow(t)
                if r:
                    return r
            if _ok("save_seed") and _wills(t, "save_seed"):
                r = save_seed(t)
                if r:
                    return r
        if family is not None and family not in ("water_fill", "tool"):
            return None                                    # a scoped garden deed that its own hands declined: nothing else may answer for it
        if _where() in ("wood", "shore"):
            try:   # FIELDCRAFT out of the garden: the windbreak, tinder, measuring, whittling, tracking
                from core import fieldcraft as _fc
                _r = _fc.act_from_thought(thought, intention)
                if _r:
                    return _r
            except profile.NonLiveWriteError:
                # J-0726: same fix as the other fieldcraft-forwarding try above — fieldcraft.
                # act_from_thought() re-raises this itself (J-0727); do not let this second forwarding
                # call's catch-all swallow it too.
                raise
            except Exception:
                pass
        # WATER_FILL, the wood side (2026-09-06, J-0569 / F-0783's follow-up): _wills_water_fill_wood() reads
        # the same table row as the garden hand above and splits it barrel-vs-other — see its own docstring.
        if _ok("water_fill") and _where() == "wood":
            _wsub = _wills_water_fill_wood(t)
            if _wsub == "barrel":
                r = fill_barrel_from_spring(t)
                if r:
                    return r
            elif _wsub == "pail":
                from core import study_life as _sl
                r = _sl.fill_pail_at_spring()
                if r:
                    return r
        if _ok("tool") and _where() == "study" and "drawer" in t and any(v in t for v in ("seed", "packet", "take", "fetch", "get")):
            r = fetch_from_drawer(t)
            if r:
                return r
        # TOOL (2026-09-06, J-0569 / F-0783's follow-up): _wills_tool() partitions the table's one tool row
        # into take/put — see its own docstring for why the old hand-kept version (verb phrases with no
        # object check at all) drifted onto 299 of the 302 corpus thoughts it ever matched.
        if _ok("tool"):
            _tsub = _wills_tool(t)
            if _tsub == "take":
                r = take(t)
                if r:
                    return r
            elif _tsub == "put":
                r = put(t)
                if r:
                    return r
        return None
    except profile.NonLiveWriteError:
        # J-0714: let D-0179's hard-raise (guard_path(), F-1024) reach act_from_thought()'s own caller
        # instead of being swallowed by the broader except below — this can only fire when
        # profile.LIVE is False, never during Du's own real live loop, so this changes nothing live.
        raise
    except Exception as exc:
        logger.debug("[garden] act failed (non-fatal): %s", exc)
        return None


def milestone() -> str:
    """A change worth announcing once (world event law): first volunteers up, first flower, beans flowering."""
    try:
        try:
            from core import garden_life as _gl
            _r = _gl.milestone()
            if _r:
                return _r
        except Exception:
            pass
        try:
            from core import wood_life as _wl
            _r = _wl.milestone()
            if _r:
                return _r
        except Exception:
            pass
        st = _load()
        if st.get("pending_announce"):
            _a = st["pending_announce"].pop(0); _save(force=True)
            return _a
        seen = set(st.get("volunteers_seen", []))
        for p in st["plants"].values():
            if p["origin"] == "volunteer_from_seed_bank" and p["stage"] in ("leaf",) and p["id"] not in seen and CATALOGUE[p["species"]]["kind"] != "weed":
                st["volunteers_seen"].append(p["id"]); _save(force=True)
                return f"something has come up in the bed that you did not sow — seedlings, {CATALOGUE[p['species']]['names'][0]} by the look of the leaves"
            if p["stage"] == "flowering" and (time.time() - float(p.get("stage_ts", 0))) < 3600 * 6 and p["id"] + ":flower" not in seen:
                st["volunteers_seen"].append(p["id"] + ":flower"); _save(force=True)
                try:
                    from core import garden_knowledge as _gk
                    _gk.witness(p["species"], "come_into_flower")
                except profile.NonLiveWriteError:
                    # J-0783: garden_knowledge.py is now fenced -- let the raise reach this
                    # function's own caller instead of this pre-existing broad except swallowing it.
                    raise
                except Exception:
                    pass
                _nm = CATALOGUE[p["species"]]["names"][0]
                _pl = _nm.endswith('s') and not _nm.endswith(('oxalis', 'chickweed', 'radish'))
                return f"{_nm} {'have' if _pl else 'has'} come into flower"
        return ""
    except profile.NonLiveWriteError:
        # J-0783: the witness() call above (and garden_life.milestone()/wood_life.milestone(),
        # forwarded first) can now raise this via garden_knowledge.py's own newly-fenced _save() --
        # let it reach this function's own caller instead of this outer broad except swallowing it.
        raise
    except Exception:
        return ""


def dried_for_caddy() -> list[str]:
    """Bundles that have dried: move to the caddy (the tea loop's input). Called by make_tea / the rack hand."""
    st = _load()
    done = [b for b in st.get("rack", []) if b.get("dry", 0) >= 0.95 and b.get("mould", 0) < 0.3]
    for b in done:
        st["rack"].remove(b)
    if done:
        _save(force=True)
    return [b["species"] for b in done]


def status() -> dict:
    try:
        if _state is None and not _F.exists():
            return {"plants": 0, "note": "not yet bootstrapped (first Du start)"}
        st = _load()
        plants = st["plants"].values()
        by_stage: dict = {}
        for p in plants:
            by_stage[p["stage"]] = by_stage.get(p["stage"], 0) + 1
        led = 0
        try:
            led = sum(1 for _ in open(_LEDGER, encoding="utf-8"))
        except Exception:
            pass
        from core import inventory as _inv
        try:   # SOIL LIFE (2026-09-03, J-0505)
            from core import garden_soil as _soil
            _soil_status = _soil.status()
        except Exception:
            _soil_status = {}
        return {"plants": len(st["plants"]), "by_stage": by_stage, "soil": _soil_status, "soil_temp": st.get("soil_temp"), "moisture": st.get("moisture"),
                "weeds": st.get("weeds"), "slugs": st.get("slugs"), "barrel": st.get("barrel"), "seed_bank": len(st.get("seed_bank", [])),
                "packets": len(st.get("packets", [])), "rack": st.get("rack", []), "carried": _inv.carried(st.get("items", {})),
                "deeds_logged": led, "netted": st.get("netted"), "staked": len(st.get("staked", [])), "drawer": len(st.get("drawer", [])),
                "saved_seed": len(st.get("saved_seed", [])), "bed_light": st.get("bed_light"),
                "life": __import__("core.garden_life", fromlist=["x"]).status(),
                "bed": [{"slot": p.get("slot"), "species": p["species"], "stage": p["stage"], "vigour": round(p.get("vigour", 0.0), 2), "height": p.get("height")}
                        for p in sorted(plants, key=lambda q: (q.get("slot") is None, q.get("slot") or 0)) if p["stage"] != "dead"][:14]}
    except Exception as exc:
        return {"error": repr(exc)[:80]}
