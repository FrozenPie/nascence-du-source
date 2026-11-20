"""
Nascence — THE WOODS BESTIARY (2026-11-02; docs/staged/wood_creatures.md, job J-3062). The wood joins the same engine as the shore:
core/life_shore.py holds the closed vocabularies, the composer, the detail model, the leak test and the place registry (PLACES); this
module is only what is the wood's own: its ZONES over data/world_geometry/wood.json (plus sidecar placements that wood.json does not
have), the words that make a look a look at a PLACE of the wood, the flag, and the rows.

Founder rulings (the shore's, restated for the wood, 2026-11-01): one life row per species; every creature has a real position in the
authored geometry; Du is never told what a thing is and the world never leads (no name, no alias, no reveal caption; a name needs a book
AND a face, D-0129).

ONE FLAG brings it all up: data/life_flags.json "wood_bestiary": true (+ a restart). It registers the rows and, unless set explicitly,
turns the described-look answers ("wood_bestiary_render") and the place-look discovery ("wood_bestiary_discover") ON with it. Explicit
false on either = shadow. OFF today; life._ensure_builtin imports this module (which only registers the place) and registers the rows
only when the flag is true.

SIDECAR PLACEMENTS (wood.json is authored truth and is NOT edited). Marked ASSUMED where the files do not say:
  stream          wood_life.py says the spring "runs into a STREAM down the gully to the shore", wood.json has only `the_spring`. ASSUMED: a
                  braid from the spring (4,14) down to (12.5,19.2), a little east of the sea_gap. Founder to confirm (J-3062 / the shore's J-2869).
  canopy          wood.json has one point (10,10,8). ASSUMED: a disc of radius 6 at heights 5-9 m.
  oak_trunk       the oak's position is authored (5,13); its trunk height is ASSUMED 0.5-5 m.
  kanuka_grove / totara_grove / tree_ferns   positions are wood_life.TREES' (authored there, not in wood.json); radii/heights ASSUMED.
Zero LLM, additive-only, no I/O.
"""
from __future__ import annotations

from core import life_shore as LS
from core.life_shore import place_row

PLACE = "wood"
FRAME = (24.0, 20.0)                        # wood.json "size" (x, y); z runs to 10

try:                                         # the groves live in wood_life.TREES, not in wood.json: read them, fall back to the known values
    from core import wood_life as _wl
    _T = {k: list(v["pos"]) for k, v in _wl.TREES.items()}
except Exception:                            # pragma: no cover
    _T = {"kanuka": [12.0, 6.0, 0.0], "totara": [16.0, 13.0, 0.0], "ponga": [3.5, 15.5, 0.0]}

ZONES = {
    "the_path": {"mode": "disc", "anchor": "the_path", "r": 3.0},
    "leaf_floor": {"mode": "disc", "anchor": "leaf_floor", "r": 5.0},
    "undergrowth": {"mode": "disc", "anchor": "undergrowth", "r": 3.0, "z": (0.0, 1.0)},
    "the_old_oak": {"mode": "disc", "anchor": "the_old_oak", "r": 2.5},
    "oak_trunk": {"mode": "disc", "anchor": "the_old_oak", "r": 0.9, "z": (0.5, 5.0), "assumed": True},
    "deadfall": {"mode": "disc", "anchor": "deadfall", "r": 2.5},
    "sea_gap": {"mode": "disc", "anchor": "sea_gap", "r": 2.5, "z": (0.5, 3.0)},
    "clearing": {"mode": "disc", "anchor": "clearing", "r": 2.5},
    "the_spring": {"mode": "disc", "anchor": "the_spring", "r": 1.2},
    "canopy": {"mode": "disc", "anchor": "canopy", "r": 6.0, "z": (5.0, 9.0), "assumed": True},
    "stream": {"mode": "segment", "a": [4.0, 14.0, 0.0], "b": [12.5, 19.2, 0.0], "jitter": 0.6, "assumed": True},
    "kanuka_grove": {"mode": "disc", "pos": _T["kanuka"], "r": 2.5, "z": (0.0, 4.0), "assumed": True},
    "totara_grove": {"mode": "disc", "pos": _T["totara"], "r": 2.5, "z": (0.0, 5.0), "assumed": True},
    "tree_ferns": {"mode": "disc", "pos": _T["ponga"], "r": 1.8, "z": (0.0, 2.0), "assumed": True},
}

# What makes a look a look at a PLACE of the wood (first match wins, so the specific before the general). The wood's own scenery targets
# are world_content_wood's: path, canopy, undergrowth, deadfall, moss, birds.
TARGET_ZONES = (
    ({"spring", "pipe"}, ("the_spring",)),
    ({"stream", "gully", "brook", "creek"}, ("stream",)),
    ({"oak", "ivy"}, ("the_old_oak", "oak_trunk")),
    ({"moss"}, ("oak_trunk", "leaf_floor")),
    ({"deadfall", "dead", "fallen", "firewood", "logs", "log", "stump"}, ("deadfall",)),
    ({"canopy", "leaves", "branches", "treetops", "trees", "tree", "up"}, ("canopy", "kanuka_grove", "totara_grove")),
    ({"undergrowth", "bracken", "bramble", "fern", "ferns", "ponga"}, ("undergrowth", "tree_ferns")),
    ({"litter", "leaf-mould", "mould", "ground", "floor"}, ("leaf_floor", "the_path")),
    ({"clearing", "foxgloves"}, ("clearing",)),
    ({"gap", "sea"}, ("sea_gap",)),
    ({"path", "track"}, ("the_path", "leaf_floor")),
    ({"birds", "bird"}, ("canopy", "kanuka_grove", "undergrowth")),
)

# nouns of the wood's own SCENERY (tools, fungi, nuts): a clause naming one is a look at that thing, not at a creature
SCENERY = frozenset("acorn acorns firewood kindling tinder pail saw axe mushroom mushrooms fungi fungus foxglove foxgloves bracken bramble".split())

# common names the wood's vocabulary and lines must never contain (the pilot's; the 150-name list is parsed from
# docs/staged/wood_creatures.md by scripts/_test_wood_bestiary_p1.py, which scans every vocabulary phrase against ALL of them)
NAMES = ("huhu", "huhu beetle", "green gecko", "moko-kakariki", "moko-kākāriki", "gecko", "koura", "kōura", "freshwater crayfish", "red deer",
         "tia", "deer", "stag", "kaka", "kākā", "parrot", "parakeet", "kakariki", "kākāriki")

LS.PLACES[PLACE] = {"layout": "wood", "zones": ZONES, "targets": TARGET_ZONES, "frame": FRAME, "scenery": SCENERY, "names": NAMES}


def enabled() -> bool:
    return LS.enabled(PLACE)


def wood_row(key: str, **kw) -> dict:
    return place_row(PLACE, key, **kw)


# ── presets (the shore cast's, kept local so the wood can change its own) ─────────────────────────────────────
HOURS = {
    "D": {"dawn": 0.6, "day": 1.0, "dusk": 0.6, "night": 0.05},
    "N": {"dawn": 0.3, "day": 0.05, "dusk": 0.6, "night": 1.0},
    "C": {"dawn": 1.0, "day": 0.3, "dusk": 1.0, "night": 0.3},
    "A": {"dawn": 0.8, "day": 0.8, "dusk": 0.8, "night": 0.8},
    "S": {"dawn": 0.1, "day": 1.0, "dusk": 0.3, "night": 0.0},
}
RES = [1.0] * 12
WEATHER = {
    "BUG": {"rain": 0.3, "wind": 0.5, "storm": 0.0, "frost": 0.3},
    "FUR": {"rain": 0.6, "wind": 0.7, "storm": 0.1, "frost": 0.7},
    "BIRD": {"rain": 0.6, "wind": 0.5, "storm": 0.1, "frost": 0.8},
    "WATER": {"rain": 1.0, "wind": 1.0, "storm": 0.7, "frost": 1.0},
}


def ob(size, span, shape, colour, colour2, pattern, sheen, covering, motion, position, disturb, counts=None):
    d = dict(size_cm=size, span_cm=span, shape=shape, colour=colour, pattern=pattern, sheen=sheen, covering=covering,
             motion=motion, position=position, on_disturb=disturb)
    if colour2:
        d["colour2"] = colour2
    if counts:
        d["counts"] = counts
    return d


def R(key, species, names, words, zone, o, hours="D", season=RES, weather="BUG", ease=0.5, count=("one", "a few", "several"),
      life=None, days=1.0, light="indifferent", eyeshine=False, diet=(), eaten_by=(), note=""):
    return wood_row(key, species=species, book_names=tuple(names), book_words=tuple(words), zone=zone, obs=o,
                    active_hours=HOURS[hours], season_curve=season, weather_gate=WEATHER[weather], ease=ease, count=count,
                    lifespan_y=life, diet=diet, eaten_by=eaten_by, days_about=days, light=light, eyeshine=eyeshine, note=note)


def rows() -> list[dict]:
    X: list[dict] = []
    a = X.append
    # PILOT: five at the extremes of zone and size: dead wood by night, a gecko in the undergrowth, the ASSUMED stream, a huge far
    # animal in the clearing, a big bird in the canopy (the 3D case: eight metres up).
    a(R("huhu_beetle", "huhu beetle", ("huhu", "huhu beetle", "prionoplus"), ("grub", "dead wood", "lamp", "beetle", "rotting", "native"), "deadfall",
        ob(5.0, 7.0, "beetle_long", "dark_brown", None, "plain", "glossy", "smooth", "walk_slow", "on_wood", "freezes"),
        "N", [1.0, 1.0, 0.6, 0.1, 0.0, 0.0, 0.0, 0.0, 0.2, 0.7, 1.0, 1.0], "BUG", ease=0.4, count=("one", "a few", "several"), life=1,
        light="drawn", note="PILOT. native; comes to the lamp; the grub lives in rotting wood for years"))
    a(R("green_gecko", "green gecko", ("green gecko", "moko-kakariki", "moko-kākāriki", "naultinus"), ("lizard", "gecko", "tree", "protected", "sun"), "undergrowth",
        ob(8.0, 18.0, "lizard_form", "green", "white", "streaked", "matt", "scaled", "still", "on_branch", "freezes"),
        "S", RES, "BUG", ease=0.12, count=("one", "one", "two"), life=20, days=0.1, note="PILOT. native; protected; rare; diurnal"))
    a(R("freshwater_crayfish", "freshwater crayfish", ("freshwater crayfish", "koura", "kōura", "paranephrops"), ("crayfish", "stream", "claws", "night", "native"), "stream",
        ob(8.0, 15.0, "crayfish_pincers", "olive_brown", "orange", "mottled", "matt", "plated", "walk_slow", "in_stream", "jets_away"),
        "N", RES, "WATER", ease=0.2, count=("one", "a few", "several"), life=15, note="PILOT. native; declining; ASSUMED stream"))
    a(R("red_deer", "red deer", ("red deer", "deer", "tia"), ("antlers", "stag", "hind", "browse", "introduced"), "clearing",
        ob(190.0, 230.0, "deer_form", "brown", "cream", "two_tone", "matt", "furred", "browse", "in_the_open", "flees"),
        "C", RES, "FUR", ease=0.9, count=("one", "one", "a small herd"), life=15, days=0.12, note="PILOT. invasive; shy; crepuscular"))
    a(R("kaka", "kākā", ("kaka", "kākā", "nestor meridionalis"), ("parrot", "beak", "forest", "canopy", "nectar", "native"), "canopy",
        ob(45.0, 80.0, "parrot_form", "olive_brown", "red", "accented", "matt", "feathered", "clamber", "high_in_the_canopy", "flees"),
        "D", RES, "BIRD", ease=0.5, count=("one", "a pair", "a small flock"), life=25, days=0.2, note="PILOT. native; rare visitor; the 3D case"))
    try:   # the other 145 (core/life_wood_cast.py); a cast that fails to build must not take the pilot rows down with it
        from core import life_wood_cast as _cast
        X += _cast.rows()
    except Exception as exc:   # pragma: no cover - surfaced loudly by scripts/_test_wood_bestiary_p1.py (it counts 150 rows)
        import logging
        logging.getLogger("nascence.life_wood").warning("[life_wood] cast not built: %s", exc)
    return X
