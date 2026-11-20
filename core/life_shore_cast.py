"""
Nascence — THE SHORE BESTIARY: the cast (2026-11-01; docs/staged/shore_creatures.md). The 97 creatures that, with the 3 pilot rows in
core/life_shore.py, make the 100. ONE ROW PER SPECIES. Every look is composed from the observable tuple by life_shore.compose(); nothing
here is ever shown to Du except through that composer, so the names below (species, book_names, notes) are hidden truth: they feed only
the existing learning ledger (D-0129: a name needs a book AND a face) and the leak test, which fails if any of them reaches a line.

How to read a row:  R(key, species, book_names, book_words, zone, ob(...), hours, season, weather, ease, count, lifespan, ...)
  ob(size_cm, span_cm, shape, colour, colour2, pattern, sheen, covering, motion, position, on_disturb [, counts])
Burrowers (ghost shrimp, ragworm, lugworm, heart urchin, sand dollar) are written as WHAT SHOWS AT THE SURFACE (a mound with a hole, a coil
of wet sand beside a dimple, a pale test): there is no dig hand yet (J-2871), so he never sees the animal itself, only its sign -- and a
book that names the animal binds to the sign he has seen, which is the honest limit of what he can know. The pea crab lives inside other
animals and is, until an open-a-shell deed exists, almost never shown (ease 0.02).
Zero LLM, additive-only, no I/O. Registered by life_shore.rows() only when data/life_flags.json has "shore_bestiary": true.
"""
from __future__ import annotations

from core.life_shore import shore_row

# ── presets ──────────────────────────────────────────────────────────────────────────────────────────────────
HOURS = {
    "D": {"dawn": 0.6, "day": 1.0, "dusk": 0.6, "night": 0.05},      # diurnal
    "N": {"dawn": 0.3, "day": 0.05, "dusk": 0.6, "night": 1.0},      # nocturnal
    "C": {"dawn": 1.0, "day": 0.3, "dusk": 1.0, "night": 0.3},       # crepuscular
    "A": {"dawn": 0.8, "day": 0.8, "dusk": 0.8, "night": 0.8},       # round the clock
    "S": {"dawn": 0.1, "day": 1.0, "dusk": 0.3, "night": 0.0},       # needs the sun
}
SEASONS = {
    "RES": [1.0] * 12,
    "SUM": [1.0, 1.0, 0.9, 0.5, 0.2, 0.05, 0.05, 0.1, 0.4, 0.7, 0.9, 1.0],
    "WIN": [0.2, 0.1, 0.2, 0.5, 0.8, 1.0, 1.0, 1.0, 0.8, 0.5, 0.3, 0.2],
    "SPRSUM": [0.9, 0.8, 0.6, 0.3, 0.1, 0.0, 0.0, 0.1, 0.5, 0.9, 1.0, 1.0],
    "OCTMAR": [1.0, 1.0, 0.8, 0.3, 0.0, 0.0, 0.0, 0.0, 0.2, 0.6, 0.9, 1.0],
    "SEPAPR": [1.0, 1.0, 0.8, 0.4, 0.0, 0.0, 0.0, 0.0, 0.4, 0.9, 1.0, 1.0],
    "AUTWIN": [0.2, 0.2, 0.8, 1.0, 1.0, 1.0, 0.8, 0.6, 0.4, 0.2, 0.1, 0.1],
    "WINTER_VISITOR": [0.2, 0.2, 0.4, 0.8, 1.0, 1.0, 1.0, 1.0, 0.5, 0.2, 0.1, 0.1],
    "RIGHTWHALE": [0.0, 0.0, 0.0, 0.0, 0.1, 0.7, 1.0, 1.0, 0.7, 0.1, 0.0, 0.0],
    "SALMON": [0.6, 0.8, 1.0, 0.8, 0.3, 0.0, 0.0, 0.0, 0.0, 0.0, 0.1, 0.3],
    "HEDGEHOG": [1.0, 1.0, 0.9, 0.6, 0.15, 0.0, 0.0, 0.1, 0.5, 0.9, 1.0, 1.0],
    "DOLPHIN": [1.0, 1.0, 0.8, 0.5, 0.3, 0.2, 0.2, 0.3, 0.5, 0.7, 0.9, 1.0],
    "SPRING": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.3, 1.0, 1.0, 0.8, 0.2],
}
WEATHER = {
    "SEA": {"rain": 1.0, "wind": 1.0, "storm": 0.6, "frost": 1.0},        # lives in the water: weather barely moves it
    "BUG": {"rain": 0.3, "wind": 0.5, "storm": 0.0, "frost": 0.3},        # small and flying or running: grounded by weather
    "FUR": {"rain": 0.6, "wind": 0.7, "storm": 0.1, "frost": 0.7},
    "BIRD": {"rain": 0.6, "wind": 0.5, "storm": 0.1, "frost": 0.8},
    "BIG": {"rain": 0.9, "wind": 0.5, "storm": 0.1, "frost": 1.0},        # big sea animals: a rough sea sends them off
    "FLY": {"rain": 0.05, "wind": 0.15, "storm": 0.0, "frost": 0.2},      # fliers: no flight in rain or a hard wind
}
C3 = ("one", "a few", "several")


def ob(size, span, shape, colour, colour2, pattern, sheen, covering, motion, position, disturb, counts=None):
    d = dict(size_cm=size, span_cm=span, shape=shape, colour=colour, pattern=pattern, sheen=sheen, covering=covering,
             motion=motion, position=position, on_disturb=disturb)
    if colour2:
        d["colour2"] = colour2
    if counts:
        d["counts"] = counts
    return d


def R(key, species, names, words, zone, o, hours="D", season="RES", weather="SEA", ease=0.5, count=C3, life=None,
      tide=None, days=1.0, diet=(), eaten_by=(), note=""):
    return shore_row(key, species=species, book_names=tuple(names), book_words=tuple(words), zone=zone, obs=o,
                     active_hours=HOURS[hours], season_curve=SEASONS[season] if isinstance(season, str) else season,
                     weather_gate=WEATHER[weather], ease=ease, count=count, lifespan_y=life, diet=diet, eaten_by=eaten_by,
                     tide=tide, days_about=days, note=note)


def rows() -> list[dict]:
    X: list[dict] = []
    a = X.append

    # ── insects, spiders and other land arthropods ───────────────────────────────────────────────────────────
    a(R("katipo", "katipō", ("katipo", "katipō", "latrodectus"), ("web", "venom", "bite", "red stripe", "dune"), "dune",
        ob(1.0, 3, "eight_legged", "black", "red", "streaked", "glossy", "smooth", "run_stop", "in_grass", "freezes", counts={"legs": 8}),
        "N", "SUM", "BUG", ease=0.25, count=("one", "one", "a few"), life=2, days=0.4, note="venomous; rare; shy"))
    a(R("dune_wolf_spider", "dune wolf spider", ("wolf spider", "dune wolf spider"), ("burrow", "hunts", "eyes", "sand", "silk"), "dune",
        ob(1.2, 4, "eight_legged", "brown", "tan", "mottled", "matt", "hairy", "run_stop", "on_bare_sand", "flees"),
        "N", "SUM", "BUG", ease=0.3, count=C3, life=1))
    a(R("tiger_beetle", "tiger beetle", ("tiger beetle",), ("sand", "fast", "jaws", "predator", "dune"), "dune",
        ob(1.4, 2, "six_legged", "green", "cream", "spotted", "iridescent", "smooth", "run_stop", "on_bare_sand", "flees"),
        "S", "SUM", "BUG", ease=0.4, count=C3, life=1))
    a(R("sand_scarab", "sand scarab beetle", ("sand scarab", "scarab beetle"), ("dune", "burrow", "night", "larvae", "sand"), "dune",
        ob(2.0, 2.5, "six_legged", "brown", None, "plain", "matt", "rough", "run_stop", "half_buried", "buries"),
        "N", "SUM", "BUG", ease=0.3, count=C3, life=2))
    a(R("wrack_rove_beetle", "wrack rove beetle", ("rove beetle",), ("seaweed", "wrack", "tideline", "rotting", "flies"), "tideline",
        ob(0.6, 0.8, "six_legged", "black", None, "plain", "glossy", "smooth", "run_stop", "tideline_litter", "flees"),
        "A", "SUM", "BUG", ease=0.2, count=("a few", "several", "a swarm of them"), life=1))
    a(R("seashore_earwig", "seashore earwig", ("earwig", "seashore earwig"), ("pincers", "tideline", "crevice", "scavenges"), "tideline",
        ob(1.5, 1.5, "six_legged_pincers", "dark_brown", "tan", "banded", "glossy", "smooth", "run_stop", "tideline_litter", "flees"),
        "N", "SUM", "BUG", ease=0.25, count=C3, life=1))
    a(R("sandfly", "sandfly", ("sandfly", "sandflies", "namu"), ("bite", "blood", "stream", "swarm", "itch"), "dune",
        ob(0.3, 0.5, "winged_small", "dark_grey", None, "plain", "matt", "hairy", "hover_dart", "in_air", "flees"),
        "D", "SUM", "FLY", ease=0.3, count=("a few", "a cloud of them", "a thick cloud of them"), life=1, note="bites"))
    a(R("saltmarsh_mosquito", "saltmarsh mosquito", ("mosquito", "saltmarsh mosquito"), ("bite", "pool", "larvae", "dusk", "whine"), "pool",
        ob(0.5, 1.2, "winged_slender", "grey", "cream", "banded", "matt", "hairy", "hover_dart", "in_air", "flees"),
        "C", "SUM", "FLY", ease=0.25, count=("a few", "several", "a whining cloud"), life=1, note="breeds in rock pools; bites"))
    a(R("boulder_copper", "boulder copper butterfly", ("copper butterfly", "boulder copper"), ("butterfly", "wings", "muehlenbeckia", "dune", "copper"), "dune",
        ob(1.5, 3.0, "winged_broad", "orange", "brown", "spotted", "matt", "scaled", "flutter", "in_grass", "flees"),
        "D", "OCTMAR", "FLY", ease=0.45, count=("one", "a pair", "several"), life=1))
    a(R("cave_weta", "cave weta", ("cave weta", "tokoriro"), ("weta", "cave", "antennae", "legs", "night"), "cave",
        ob(4.0, 12.0, "jumper_long_legs", "tan", "brown", "mottled", "matt", "spined", "spring", "under_stone", "freezes"),
        "N", "RES", "BUG", ease=0.35, count=C3, life=2))
    a(R("paper_wasp", "Asian paper wasp", ("paper wasp", "asian paper wasp"), ("nest", "sting", "paper", "colony", "summer"), "driftwood",
        ob(1.5, 2.5, "waisted_winged", "yellow", "black", "banded", "glossy", "smooth", "hover_dart", "on_wood", "stings"),
        "S", "SUM", "FLY", ease=0.4, count=C3, life=1, note="invasive; stings"))

    # ── land vertebrates ─────────────────────────────────────────────────────────────────────────────────────
    a(R("shore_skink", "shore skink", ("shore skink",), ("lizard", "boulder", "shingle", "sun", "scales"), "shingle",
        ob(11, 12, "lizard_form", "tan", "dark_brown", "streaked", "glossy", "scaled", "run_stop", "on_rock_flat", "flees"),
        "S", "SUM", "BUG", ease=0.4, count=("one", "two or three", "several"), life=8, note="native; near-threatened"))
    a(R("norway_rat", "Norway rat", ("norway rat", "rat", "rats"), ("rodent", "burrow", "gnaw", "eggs", "nests"), "tideline",
        ob(24, 45, "small_furred", "brown", "grey", "two_tone", "matt", "furred", "run_stop", "tideline_litter", "flees"),
        "N", "RES", "FUR", ease=0.3, count=("one", "a few", "several"), life=2, note="invasive; takes eggs and chicks"))
    a(R("house_mouse", "house mouse", ("house mouse", "mouse", "mice"), ("rodent", "gnaw", "droppings", "nests"), "dune",
        ob(8, 15, "small_furred", "grey", "cream", "two_tone", "matt", "furred", "run_stop", "in_grass", "flees"),
        "N", "RES", "FUR", ease=0.25, count=C3, life=1, note="invasive"))
    a(R("shore_hedgehog", "hedgehog", ("hedgehog", "hedgehogs"), ("spines", "curl", "hibernate", "slugs", "snuffle"), "dune",
        ob(22, 22, "spined_four_legged", "brown", "cream", "banded", "matt", "spined", "shuffle", "in_grass", "curls"),
        "N", "HEDGEHOG", "FUR", ease=0.4, count=("one", "one", "two"), life=4, note="invasive; hibernates"))
    a(R("stoat", "stoat", ("stoat", "stoats", "mustelid"), ("predator", "chicks", "eggs", "hunts", "tail"), "dune",
        ob(30, 45, "long_low_furred", "tan", "cream", "two_tone", "matt", "furred", "bound", "in_grass", "flees"),
        "C", "RES", "FUR", ease=0.3, count=("one", "one", "two"), life=3, days=0.4, note="invasive; a killer of nesting birds"))

    # ── birds (new only) ─────────────────────────────────────────────────────────────────────────────────────
    a(R("banded_dotterel", "banded dotterel", ("dotterel", "banded dotterel", "tuturiwhatu", "tūturiwhatu"), ("plover", "breast band", "shingle", "nest", "wader"), "shingle",
        ob(20, 30, "wader_small", "grey", "dark_brown", "banded", "matt", "feathered", "run_stop", "among_stones", "flees"),
        "D", "WINTER_VISITOR", "BIRD", ease=0.45, count=("one", "a pair", "a small flock"), life=8, days=0.5))
    a(R("royal_spoonbill", "royal spoonbill", ("spoonbill", "royal spoonbill", "kotuku ngutupapa", "kōtuku ngutupapa"), ("bill", "wader", "estuary", "white", "sweeps"), "stream_mouth",
        ob(75, 120, "wader_tall", "white", "black", "accented", "matt", "feathered", "wade_sweep", "in_water", "flees"),
        "D", "SUM", "BIRD", ease=0.7, count=("one", "one", "two"), life=20, days=0.15, note="native; rare"))
    a(R("southern_royal_albatross", "southern royal albatross", ("albatross", "royal albatross", "toroa"), ("wingspan", "soar", "ocean", "glide", "seabird"), "offshore",
        ob(110, 300, "wings_vast", "white", "black", "edged", "matt", "feathered", "soar", "in_air", "ignores"),
        "D", "RES", "BIRD", ease=0.8, count=("one", "one", "two"), life=50, days=0.05, note="native; rare; a vagrant here"))
    a(R("sooty_shearwater", "sooty shearwater", ("shearwater", "sooty shearwater", "titi", "tītī", "muttonbird"), ("seabird", "petrel", "burrow", "migrates", "flocks"), "offshore",
        ob(40, 95, "wings_narrow", "dark_brown", None, "plain", "matt", "feathered", "skim", "in_air", "ignores"),
        "D", "SEPAPR", "BIRD", ease=0.55, count=("a few", "a long string of them", "a great raft of them"), life=30, days=0.5,
        note="alive, offshore; wrecks of dead ones belong to the carcass system"))

    # ── marine mammals ───────────────────────────────────────────────────────────────────────────────────────
    a(R("hectors_dolphin", "Hector's dolphin", ("hector's dolphin", "hectors dolphin", "tutumairekurai", "māui dolphin", "maui dolphin"), ("dolphin", "pod", "rounded fin", "endangered", "coastal"), "offshore",
        ob(140, 140, "rolling_fin", "grey", "white", "two_tone", "wet_gloss", "smooth", "roll", "in_water", "ignores"),
        "D", "DOLPHIN", "BIG", ease=0.5, count=("a pair", "a small pod", "a pod"), life=20, days=0.15, note="native; endangered"))
    a(R("orca", "orca", ("orca", "killer whale", "kakahi", "kākahi"), ("pod", "dorsal fin", "predator", "black and white", "hunt"), "offshore",
        ob(650, 700, "tall_fin", "black", "white", "two_tone", "wet_gloss", "smooth", "roll", "in_water", "ignores"),
        "D", "RES", "BIG", ease=0.9, count=("one", "a pair", "a pod"), life=60, days=0.03, note="native; rare; hunts rays and seals"))
    a(R("southern_right_whale", "southern right whale", ("right whale", "southern right whale", "tohorā", "tohora"), ("whale", "blow", "calf", "baleen", "winter"), "offshore",
        ob(1400, 1500, "back_vast", "dark_grey", None, "plain", "wet_gloss", "rough", "roll", "in_water", "ignores"),
        "D", "RIGHTWHALE", "BIG", ease=0.9, count=("one", "a pair", "a mother and calf"), life=70, days=0.15, note="native; recovering; winter"))

    # ── bivalves ─────────────────────────────────────────────────────────────────────────────────────────────
    a(R("tuatua", "tuatua", ("tuatua", "paphies subtriangulata"), ("surf", "beach", "shellfish", "sand", "kaimoana"), "tideline",
        ob(8, 8, "hinged_pair", "cream", "tan", "banded", "wet_gloss", "smooth", "clamped", "half_buried", "buries"),
        "A", "RES", "SEA", ease=0.3, count=("a few", "a scatter", "a bed of them"), life=10, tide="low"))
    a(R("toheroa", "toheroa", ("toheroa",), ("protected", "sand", "beach", "shellfish", "rare"), "flat",
        ob(12, 12, "hinged_pair", "tan", "olive_brown", "banded", "matt", "ridged", "clamped", "half_buried", "buries"),
        "A", "RES", "SEA", ease=0.25, count=("a few", "a few", "several"), life=20, days=0.3, tide="low", note="protected"))
    a(R("cockle", "cockle", ("cockle", "tuangi", "austrovenus"), ("harbour", "flats", "ribs", "shellfish", "kaimoana"), "flat",
        ob(4.5, 4.5, "hinged_ribbed", "cream", "grey", "banded", "matt", "ridged", "clamped", "half_buried", "buries"),
        "A", "RES", "SEA", ease=0.35, count=("a few", "a scatter", "a bed of them"), life=6, tide="low"))
    a(R("green_lipped_mussel", "green-lipped mussel", ("green-lipped mussel", "greenlip mussel", "kutai", "kūtai", "kuku"), ("mussel", "beard", "byssus", "shellfish", "kaimoana"), "mussel_shelf",
        ob(12, 12, "hinged_elongate", "olive_brown", "green", "edged", "wet_gloss", "smooth", "clamped", "clustered", "clamps_tight"),
        "A", "RES", "SEA", ease=0.55, count=("a few", "a cluster", "a whole bed of them"), life=10, tide="low"))
    a(R("blue_mussel", "blue mussel", ("blue mussel", "kuku"), ("mussel", "rocks", "byssus", "shellfish"), "pool",
        ob(6, 6, "hinged_elongate", "black", "blue", "streaked", "wet_gloss", "smooth", "clamped", "clustered", "clamps_tight"),
        "A", "RES", "SEA", ease=0.5, count=("a few", "a cluster", "a crust of them"), life=4, tide="low"))
    a(R("horse_mussel", "horse mussel", ("horse mussel", "hururoa", "atrina"), ("mussel", "sand", "pearl", "shellfish", "byssus"), "flat",
        ob(25, 25, "hinged_wedge", "dark_brown", None, "plain", "matt", "rough", "clamped", "half_buried", "clamps_tight"),
        "A", "RES", "SEA", ease=0.35, count=("one", "a few", "several"), life=15, days=0.3, tide="low"))
    a(R("rock_oyster", "rock oyster", ("rock oyster", "oyster", "tio"), ("oyster", "rock", "shellfish", "tide", "cemented"), "mussel_shelf",
        ob(8, 8, "hinged_rough", "grey", "cream", "mottled", "matt", "rough", "clamped", "on_rock_flat", "clamps_tight"),
        "A", "RES", "SEA", ease=0.5, count=("a few", "a cluster", "a crust of them"), life=8, tide="low"))
    a(R("scallop", "scallop", ("scallop", "tipa"), ("scallop", "fan", "swims", "shellfish", "ribs"), "surf",
        ob(9, 9, "fan_pair", "tan", "pink", "rayed", "matt", "ridged", "clamped", "half_buried", "jets_away"),
        "A", "RES", "SEA", ease=0.25, count=("one", "a few", "a bed of them"), life=8, days=0.4))
    a(R("pacific_oyster", "Pacific oyster", ("pacific oyster", "oyster"), ("oyster", "introduced", "farmed", "shellfish", "rock"), "pool",
        ob(12, 12, "hinged_rough", "grey", "cream", "mottled", "chalky", "rough", "clamped", "on_rock_flat", "clamps_tight"),
        "A", "RES", "SEA", ease=0.45, count=("a few", "a cluster", "a crust of them"), life=10, tide="low", note="invasive"))

    # ── snails, chitons, sea slugs ───────────────────────────────────────────────────────────────────────────
    a(R("paua", "pāua", ("paua", "pāua", "abalone", "haliotis"), ("shell", "mother-of-pearl", "holes", "rock", "kaimoana"), "mussel_shelf",
        ob(12, 12, "ear_shell", "dark_grey", "olive_green", "mottled", "matt", "rough", "clamped", "crevice", "clamps_tight"),
        "N", "RES", "SEA", ease=0.35, count=("one", "a few", "several"), life=30, days=0.6, tide="low"))
    a(R("cats_eye", "cat's eye", ("cat's eye", "cats eye", "pupu", "pūpū", "turban shell"), ("shell", "operculum", "door", "rock pool", "snail"), "pool",
        ob(2.5, 2.5, "spiral_cone", "dark_brown", "cream", "spotted", "matt", "smooth", "glide_slow", "on_rock_flat", "retracts"),
        "A", "RES", "SEA", ease=0.5, count=("a few", "several", "dozens of them"), life=5, tide="low"))
    a(R("radiate_limpet", "radiate limpet", ("radiate limpet", "limpet", "ngaiore", "ngāiore"), ("limpet", "cone", "rock", "grazes", "clamped"), "pool",
        ob(3, 3, "clamped_cone", "grey", "brown", "rayed", "matt", "ridged", "clamped", "on_rock_flat", "clamps_tight"),
        "A", "RES", "SEA", ease=0.55, count=("a few", "several", "dozens of them"), life=4, tide="low"))
    a(R("snakeskin_chiton", "snakeskin chiton", ("chiton", "snakeskin chiton"), ("plates", "eight", "girdle", "rock", "grazes"), "pool",
        ob(5, 5, "plated_oval", "olive_brown", "grey", "marbled", "matt", "plated", "clamped", "on_rock_flat", "clamps_tight", counts={"plates": 8}),
        "N", "RES", "SEA", ease=0.35, count=("one", "a few", "several"), life=5, tide="low"))
    a(R("oyster_borer", "oyster borer", ("oyster borer", "borer", "haustrum"), ("whelk", "drills", "predator", "shell", "rock"), "pool",
        ob(3, 3, "spiral_cone", "grey", "brown", "banded", "matt", "ridged", "glide_slow", "on_rock_flat", "retracts"),
        "A", "RES", "SEA", ease=0.45, count=("a few", "several", "dozens of them"), life=6, tide="low"))
    a(R("speckled_whelk", "speckled whelk", ("whelk", "speckled whelk"), ("whelk", "shell", "carrion", "spiral", "scavenger"), "pool",
        ob(4, 4, "spiral_cone", "tan", "brown", "spotted", "matt", "smooth", "glide_slow", "pool_floor", "retracts"),
        "N", "RES", "SEA", ease=0.4, count=("one", "a few", "several"), life=6, tide="low"))
    a(R("sea_hare", "sea hare", ("sea hare",), ("slug", "ink", "seaweed", "grazes", "soft"), "pool",
        ob(12, 15, "slug_soft", "olive_green", "brown", "mottled", "wet_gloss", "soft", "glide_slow", "pool_floor", "retracts"),
        "A", "SUM", "SEA", ease=0.45, count=("one", "one", "two"), life=1, days=0.5, tide="low"))
    a(R("blue_dragon", "blue dragon", ("blue dragon", "glaucus"), ("sting", "floats", "man o' war", "stranded", "sea slug"), "tideline",
        ob(3, 4, "slug_winged", "silver", "blue", "two_tone", "glassy", "soft", "drift", "tideline_litter", "stings"),
        "A", "SUM", "SEA", ease=0.35, count=("one", "a few", "a stranding of them"), life=1, days=0.05, note="stings; stranded by onshore winds"))
    a(R("violet_sea_snail", "violet sea snail", ("violet sea snail", "janthina"), ("raft", "bubbles", "violet", "floats", "stranded"), "tideline",
        ob(3, 3, "spiral_cone", "violet", None, "plain", "pearly", "smooth", "still", "tideline_litter", "ignores"),
        "A", "SUM", "SEA", ease=0.35, count=("one", "a few", "a stranding of them"), life=1, days=0.08))
    a(R("nudibranch", "nudibranch", ("nudibranch", "sea slug"), ("slug", "gills", "colour", "soft", "rock pool"), "pool",
        ob(4, 4, "slug_soft", "orange", "white", "spotted", "wet_gloss", "soft", "glide_slow", "pool_floor", "retracts"),
        "A", "RES", "SEA", ease=0.35, count=("one", "one", "two"), life=1, days=0.5, tide="low"))

    # ── octopus and squid ────────────────────────────────────────────────────────────────────────────────────
    a(R("octopus", "octopus", ("octopus", "wheke"), ("tentacles", "suckers", "ink", "camouflage", "intelligent"), "pool",
        ob(25, 80, "soft_sac_arms", "tan", "brown", "mottled", "wet_gloss", "warty", "pour", "crevice", "jets_away", counts={"arms": 8}),
        "N", "RES", "SEA", ease=0.2, count=("one", "one", "one"), life=2, days=0.35, tide="low"))
    a(R("arrow_squid", "arrow squid", ("arrow squid", "squid", "kaiwhaiwhai"), ("squid", "jet", "arms", "ink", "schools"), "surf",
        ob(30, 40, "squid_body", "pink", "purple", "spotted", "pearly", "smooth", "jet", "in_water", "jets_away", counts={"arms": 10}),
        "N", "AUTWIN", "SEA", ease=0.3, count=("one", "a few", "a school of them"), life=1, days=0.4))
    a(R("paper_nautilus", "paper nautilus", ("paper nautilus", "argonaut"), ("shell", "paper", "octopus", "delicate", "stranded"), "tideline",
        ob(12, 12, "coil_thin", "white", None, "plain", "chalky", "ridged", "still", "tideline_litter", "ignores"),
        "A", "RES", "SEA", ease=0.3, count=("one", "one", "one"), life=1, days=0.03, note="rare find; an empty shell"))

    # ── echinoderms ──────────────────────────────────────────────────────────────────────────────────────────
    a(R("cushion_star", "cushion star", ("cushion star", "cushion starfish", "patiriella"), ("starfish", "arms", "pool", "tube feet", "five"), "pool",
        ob(5, 5, "radial_short", "orange", "tan", "mottled", "matt", "rough", "glide_slow", "pool_floor", "ignores", counts={"corners": 5}),
        "A", "RES", "SEA", ease=0.6, count=("one", "a few", "several"), life=5, tide="low"))
    a(R("reef_starfish", "reef starfish", ("reef starfish", "orange starfish", "stichaster"), ("starfish", "mussels", "predator", "arms", "rock"), "mussel_shelf",
        ob(12, 20, "radial_five", "orange", None, "plain", "matt", "spined", "glide_slow", "on_rock_flat", "ignores", counts={"arms": 5}),
        "A", "RES", "SEA", ease=0.55, count=("one", "a few", "several"), life=10, tide="low"))
    a(R("kina", "kina", ("kina", "sea urchin", "sea egg", "evechinus"), ("urchin", "spines", "roe", "kelp", "grazes"), "mussel_shelf",
        ob(9, 12, "sphere_spines", "olive_green", None, "plain", "matt", "spined", "glide_slow", "crevice", "ignores"),
        "N", "RES", "SEA", ease=0.5, count=("one", "a few", "dozens of them"), life=20, tide="low"))
    a(R("heart_urchin", "heart urchin", ("heart urchin", "sea potato"), ("urchin", "test", "sand", "burrows", "petals"), "flat",
        ob(5, 6, "egg_fragile", "white", None, "plain", "chalky", "ridged", "still", "on_bare_sand", "ignores"),
        "A", "RES", "SEA", ease=0.35, count=("one", "a few", "a scatter"), life=4, tide="low", note="a dead test; the living animal is buried"))
    a(R("sand_dollar", "sand dollar", ("sand dollar",), ("urchin", "disc", "sand", "test", "buried"), "flat",
        ob(7, 7, "disc_flat", "olive_brown", None, "plain", "matt", "spined", "still", "half_buried", "buries"),
        "A", "RES", "SEA", ease=0.35, count=("one", "a few", "a scatter"), life=6, tide="low"))
    a(R("sand_sea_cucumber", "sand sea cucumber", ("sea cucumber", "rori"), ("sea cucumber", "tentacles", "sand", "sausage", "feeds"), "flat",
        ob(12, 18, "sausage_soft", "tan", "brown", "mottled", "matt", "leathery", "glide_slow", "half_buried", "retracts"),
        "A", "RES", "SEA", ease=0.35, count=("one", "a few", "several"), life=6, tide="low"))

    # ── jellies and anemones ─────────────────────────────────────────────────────────────────────────────────
    a(R("moon_jelly", "moon jelly", ("moon jelly", "aurelia"), ("jellyfish", "bell", "drifts", "harmless", "rings"), "surf",
        ob(15, 15, "bell_trailing", "clear", "violet", "spotted", "glassy", "soft", "pulse", "afloat", "ignores"),
        "A", "SUM", "SEA", ease=0.5, count=("one", "a few", "a bloom of them"), life=1, days=0.4))
    a(R("lions_mane_jelly", "lion's mane jellyfish", ("lion's mane", "lions mane", "cyanea"), ("jellyfish", "sting", "tentacles", "bell", "summer"), "surf",
        ob(30, 60, "bell_trailing", "orange", "red", "streaked", "wet_gloss", "soft", "pulse", "afloat", "stings"),
        "A", "SUM", "SEA", ease=0.55, count=("one", "a few", "several"), life=1, days=0.3, note="stings"))
    a(R("man_o_war", "Portuguese man o' war", ("man o' war", "man of war", "portuguese man o' war", "bluebottle"), ("sting", "float", "tentacles", "wind", "siphonophore"), "surf",
        ob(10, 60, "float_trailing", "blue", "violet", "two_tone", "glassy", "soft", "drift", "afloat", "stings"),
        "A", "SUM", "SEA", ease=0.5, count=("one", "a few", "a fleet of them"), life=1, days=0.08, note="stings badly; blown ashore"))
    a(R("by_the_wind_sailor", "by-the-wind sailor", ("by-the-wind sailor", "velella", "sailor"), ("sail", "float", "blue", "wind", "stranded"), "tideline",
        ob(5, 5, "disc_sail", "blue", None, "plain", "glassy", "soft", "drift", "tideline_litter", "ignores"),
        "A", "SUM", "SEA", ease=0.45, count=("a few", "a scatter", "a blue drift of them"), life=1, days=0.1))
    a(R("waratah_anemone", "waratah anemone", ("waratah anemone", "red anemone", "anemone", "actinia"), ("anemone", "tentacles", "rock pool", "stings", "red"), "pool",
        ob(5, 6, "column_fingers", "dark_red", None, "plain", "wet_gloss", "soft", "sway", "on_rock_flat", "retracts"),
        "A", "RES", "SEA", ease=0.7, count=("one", "a few", "dozens of them"), life=30, tide="low"))
    a(R("green_anemone", "green anemone", ("green anemone", "anthopleura"), ("anemone", "tentacles", "flats", "green", "algae"), "flat",
        ob(4, 6, "column_fingers", "green", "olive_green", "mottled", "wet_gloss", "soft", "sway", "half_buried", "retracts"),
        "A", "RES", "SEA", ease=0.45, count=("one", "a few", "dozens of them"), life=20, tide="low"))

    # ── crustaceans ──────────────────────────────────────────────────────────────────────────────────────────
    a(R("purple_rock_crab", "purple rock crab", ("purple rock crab", "rock crab", "papaka", "pāpaka"), ("crab", "claws", "rock", "scuttles", "shore"), "rock_shelf",
        ob(6, 9, "carapace_legs", "purple", "olive_green", "mottled", "matt", "rough", "sidle", "crevice", "flees"),
        "N", "RES", "SEA", ease=0.5, count=("one", "a few", "several"), life=6, tide="low"))
    a(R("hairy_handed_crab", "hairy-handed crab", ("hairy-handed crab", "half crab", "hemigrapsus"), ("crab", "claws", "stream", "estuary", "brackish"), "stream_mouth",
        ob(3, 4, "carapace_legs", "olive_brown", "tan", "mottled", "matt", "hairy", "sidle", "under_stone", "flees"),
        "N", "RES", "SEA", ease=0.35, count=C3, life=3))
    a(R("tunnelling_mud_crab", "tunnelling mud crab", ("mud crab", "tunnelling mud crab", "austrohelice"), ("crab", "burrow", "mud", "flats", "tunnel"), "flat",
        ob(2.5, 3.5, "carapace_legs", "olive_brown", None, "plain", "matt", "smooth", "sidle", "burrow_mouth", "buries"),
        "A", "RES", "SEA", ease=0.45, count=("a few", "several", "dozens of them"), life=3, tide="low"))
    a(R("paddle_crab", "paddle crab", ("paddle crab", "swimming crab", "ovalipes"), ("crab", "swims", "claws", "sand", "paddles"), "surf",
        ob(8, 12, "carapace_paddles", "tan", "purple", "spotted", "matt", "spined", "sidle", "half_buried", "flees"),
        "N", "RES", "SEA", ease=0.35, count=("one", "a few", "several"), life=4))
    a(R("asian_paddle_crab", "Asian paddle crab", ("asian paddle crab", "charybdis"), ("crab", "invasive", "claws", "swims", "harbour"), "surf",
        ob(8, 12, "carapace_paddles", "olive_brown", "cream", "banded", "matt", "spined", "sidle", "half_buried", "flees"),
        "N", "RES", "SEA", ease=0.35, count=("one", "a few", "several"), life=3, days=0.5, note="invasive"))
    a(R("pea_crab", "pea crab", ("pea crab", "pinnotheres"), ("crab", "mussel", "inside", "tiny", "parasite"), "mussel_shelf",
        ob(1.0, 1.2, "carapace_legs", "cream", None, "plain", "wet_gloss", "soft", "still", "inside_shell", "freezes"),
        "A", "RES", "SEA", ease=0.02, count=("one", "one", "two"), life=2, days=0.2, tide="low",
        note="lives inside mussels; effectively undiscoverable until an open-a-shell deed exists"))
    a(R("ghost_shrimp", "ghost shrimp", ("ghost shrimp", "callianassa"), ("burrow", "sand", "mound", "flats", "bait"), "flat",
        ob(3, 5, "mound_hole", "tan", None, "plain", "matt", "grainy", "still", "on_bare_sand", "ignores"),
        "A", "RES", "SEA", ease=0.4, count=("one", "a few", "a field of them"), life=4, tide="low", note="shows only its mound; the animal is below"))
    a(R("common_shrimp", "common shrimp", ("shrimp", "common shrimp", "palaemon"), ("shrimp", "transparent", "pool", "feelers", "prawn"), "pool",
        ob(3, 4, "jointed_curve", "clear", "brown", "spotted", "glassy", "smooth", "jet", "in_water", "jets_away"),
        "A", "RES", "SEA", ease=0.4, count=("a few", "several", "dozens of them"), life=2, tide="low"))
    a(R("rock_lobster", "rock lobster", ("rock lobster", "crayfish", "koura", "kōura", "spiny lobster"), ("crayfish", "feelers", "spiny", "crevice", "kaimoana"), "mussel_shelf",
        ob(30, 60, "spiny_armoured", "dark_red", None, "plain", "matt", "spined", "walk_slow", "crevice", "flees"),
        "N", "RES", "SEA", ease=0.3, count=("one", "one", "two"), life=40, days=0.2, tide="low"))
    a(R("acorn_barnacle", "acorn barnacle", ("barnacle", "acorn barnacle", "chamaesipho"), ("barnacle", "plates", "rock", "tide", "cement"), "rock_shelf",
        ob(1.2, 1.5, "cone_plates", "white", "grey", "mottled", "chalky", "plated", "clamped", "clustered", "clamps_tight"),
        "A", "RES", "SEA", ease=0.7, count=("a few", "a crust of them", "a rock white with them"), life=5, tide="low"))
    a(R("goose_barnacle", "goose barnacle", ("goose barnacle", "lepas"), ("barnacle", "stalk", "driftwood", "floats", "ocean"), "driftwood",
        ob(4, 10, "stalked_plates", "white", "dark_grey", "two_tone", "chalky", "leathery", "sway", "on_wood", "retracts"),
        "A", "RES", "SEA", ease=0.45, count=("a few", "a cluster", "a crust of them"), life=2, days=0.4))

    # ── worms ────────────────────────────────────────────────────────────────────────────────────────────────
    a(R("ragworm", "ragworm", ("ragworm", "sandworm", "nereid", "nicon"), ("worm", "bristles", "burrow", "bait", "segments"), "flat",
        ob(15, 20, "soft_worm", "red", "green", "banded", "wet_gloss", "soft", "wriggle", "burrow_mouth", "retracts"),
        "N", "RES", "SEA", ease=0.3, count=("one", "a few", "several"), life=3, tide="low"))
    a(R("lugworm", "lugworm", ("lugworm", "abarenicola"), ("worm", "cast", "burrow", "sand", "bait"), "flat",
        ob(2, 12, "sand_coil", "tan", "brown", "streaked", "matt", "grainy", "still", "on_bare_sand", "ignores"),
        "A", "RES", "SEA", ease=0.45, count=("a few", "several", "a field of them"), life=5, tide="low", note="shows only its cast; the animal is below"))
    a(R("tubeworm", "tubeworm", ("tubeworm", "tube worm", "spirobranchus"), ("worm", "tubes", "reef", "calcareous", "rock"), "rock_shelf",
        ob(1.0, 6, "tube_cluster", "white", None, "plain", "chalky", "rough", "still", "clustered", "retracts"),
        "A", "RES", "SEA", ease=0.5, count=("a few", "a mass", "a reef of them"), life=5, tide="low"))
    a(R("fanworm", "Mediterranean fanworm", ("fanworm", "fan worm", "sabella"), ("worm", "fan", "filaments", "invasive", "harbour"), "pool",
        ob(25, 25, "fan_crown", "brown", "cream", "banded", "wet_gloss", "leathery", "sway", "standing_upright", "retracts"),
        "A", "RES", "SEA", ease=0.5, count=("one", "a few", "a thicket of them"), life=3, tide="low", note="invasive"))
    a(R("bootlace_worm", "bootlace worm", ("bootlace worm", "ribbon worm", "nemertean"), ("worm", "long", "thread", "stones", "predator"), "rock_shelf",
        ob(150, 150, "soft_worm", "dark_brown", None, "plain", "wet_gloss", "slimy", "undulate", "under_stone", "retracts"),
        "N", "RES", "SEA", ease=0.2, count=("one", "one", "two"), life=5, days=0.4, tide="low"))

    # ── fish ─────────────────────────────────────────────────────────────────────────────────────────────────
    a(R("triplefin", "common triplefin", ("triplefin", "common triplefin", "blenny"), ("fin", "pool", "rocky", "small", "dorsal"), "pool",
        ob(8, 8, "fusiform", "olive_brown", "cream", "banded", "wet_gloss", "scaled", "swim_dart", "in_water", "jets_away"),
        "D", "RES", "SEA", ease=0.5, count=("one", "a few", "several"), life=3, tide="low"))
    a(R("spotty", "spotty", ("spotty", "paketi", "wrasse"), ("wrasse", "reef", "fish", "spots", "kelp"), "pool",
        ob(18, 18, "fusiform", "olive_brown", "blue", "mottled", "wet_gloss", "scaled", "swim_dart", "in_water", "jets_away"),
        "D", "RES", "SEA", ease=0.45, count=("one", "a few", "several"), life=10, tide="low"))
    a(R("cockabully", "cockabully", ("cockabully", "kokopara"), ("fish", "pool", "rocky", "small", "territorial"), "pool",
        ob(7, 7, "fusiform", "olive_brown", "black", "mottled", "wet_gloss", "scaled", "swim_dart", "pool_floor", "jets_away"),
        "D", "RES", "SEA", ease=0.45, count=("one", "a few", "several"), life=3, tide="low"))
    a(R("shore_clingfish", "shore clingfish", ("clingfish", "shore clingfish"), ("fish", "sucker", "clings", "rock", "pool"), "pool",
        ob(6, 6, "fusiform", "orange_brown", "cream", "mottled", "wet_gloss", "slimy", "clamped", "on_rock_flat", "clamps_tight"),
        "N", "RES", "SEA", ease=0.3, count=("one", "a few", "several"), life=3, tide="low"))
    a(R("big_bellied_seahorse", "big-bellied seahorse", ("seahorse", "big-bellied seahorse", "hippocampus"), ("seahorse", "pouch", "tail", "kelp", "male"), "pool",
        ob(18, 18, "stiff_upright", "tan", "brown", "spotted", "matt", "plated", "sway", "standing_upright", "freezes"),
        "A", "RES", "SEA", ease=0.15, count=("one", "one", "two"), life=4, days=0.1, tide="low"))
    a(R("inanga", "inanga", ("inanga", "īnanga", "whitebait", "galaxias maculatus"), ("whitebait", "stream", "spawn", "galaxiid", "estuary"), "stream_mouth",
        ob(10, 10, "fusiform", "olive_green", "silver", "two_tone", "wet_gloss", "soft", "swim_dart", "in_water", "jets_away"),
        "D", "RES", "SEA", ease=0.45, count=("a few", "a shoal", "the water alive with them"), life=1))
    a(R("shortfin_eel", "shortfin eel", ("shortfin eel", "short-finned eel", "tuna", "anguilla australis"), ("eel", "stream", "migrates", "dusk", "elver"), "stream_mouth",
        ob(70, 80, "serpent_long", "olive_brown", "cream", "two_tone", "wet_gloss", "slimy", "undulate", "under_stone", "retracts"),
        "N", "RES", "SEA", ease=0.25, count=("one", "one", "two"), life=30, days=0.6))
    a(R("longfin_eel", "longfin eel", ("longfin eel", "long-finned eel", "tuna", "anguilla dieffenbachii"), ("eel", "stream", "ancient", "migrates", "endangered"), "stream_mouth",
        ob(120, 130, "serpent_long", "dark_brown", "pale_grey", "marbled", "wet_gloss", "slimy", "undulate", "crevice", "retracts"),
        "N", "RES", "SEA", ease=0.15, count=("one", "one", "one"), life=80, days=0.3, note="native; declining; very old"))
    a(R("lamprey", "lamprey", ("lamprey", "kanakana", "piharau"), ("lamprey", "sucker", "teeth", "migrates", "river"), "stream_mouth",
        ob(45, 45, "round_mouth_long", "dark_grey", "pale_grey", "two_tone", "wet_gloss", "slimy", "undulate", "under_stone", "clamps_tight"),
        "N", "WIN", "SEA", ease=0.15, count=("one", "one", "two"), life=7, days=0.05, note="native; rare"))
    a(R("gambusia", "gambusia", ("gambusia", "mosquitofish"), ("fish", "mosquito", "introduced", "pond", "live-bearing"), "stream_mouth",
        ob(4, 4, "fusiform", "grey", "olive_brown", "mottled", "glassy", "scaled", "swim_dart", "in_water", "jets_away"),
        "D", "SUM", "SEA", ease=0.35, count=("a few", "a shoal", "a swarm of them"), life=2, note="invasive"))
    a(R("sea_run_brown_trout", "sea-run brown trout", ("brown trout", "sea-run trout", "trout"), ("trout", "spots", "river", "angler", "migrates"), "stream_mouth",
        ob(45, 45, "fusiform", "silver", "black", "spotted", "wet_gloss", "scaled", "swim_dart", "in_water", "jets_away"),
        "C", "AUTWIN", "SEA", ease=0.35, count=("one", "one", "two"), life=6, days=0.3, note="invasive"))
    a(R("chinook_salmon", "Chinook salmon", ("chinook", "quinnat", "chinook salmon", "king salmon", "salmon"), ("salmon", "spawn", "run", "river", "introduced"), "stream_mouth",
        ob(70, 70, "fusiform", "silver", "dark_grey", "spotted", "wet_gloss", "scaled", "swim_dart", "in_water", "jets_away"),
        "C", "SALMON", "SEA", ease=0.45, count=("one", "a few", "a run of them"), life=5, days=0.2, note="invasive; seasonal run"))
    a(R("yellow_eyed_mullet", "yellow-eyed mullet", ("yellow-eyed mullet", "aua", "mullet"), ("mullet", "schools", "estuary", "silver", "eye"), "stream_mouth",
        ob(15, 15, "fusiform", "silver", "olive_brown", "two_tone", "wet_gloss", "scaled", "swim_dart", "in_water", "jets_away"),
        "D", "RES", "SEA", ease=0.45, count=("a few", "a school", "a great school"), life=8))
    a(R("grey_mullet", "grey mullet", ("grey mullet", "kanae", "mullet"), ("mullet", "schools", "estuary", "jumps", "grey"), "stream_mouth",
        ob(35, 35, "fusiform", "silver", "dark_grey", "two_tone", "wet_gloss", "scaled", "swim_dart", "in_water", "jets_away"),
        "D", "SUM", "SEA", ease=0.45, count=("a few", "a school", "a great school"), life=12))
    a(R("garfish", "garfish", ("garfish", "piper", "ihe"), ("needle", "beak", "surface", "silver", "jaw"), "surf",
        ob(30, 30, "fusiform_beaked", "silver", "green", "two_tone", "wet_gloss", "scaled", "skitter", "afloat", "jets_away"),
        "D", "SUM", "SEA", ease=0.4, count=("a few", "a school", "a great school"), life=5))
    a(R("kahawai", "kahawai", ("kahawai", "arripis"), ("fish", "schools", "hunts", "silver", "spots"), "surf",
        ob(50, 50, "fusiform", "blue_green", "black", "spotted", "wet_gloss", "scaled", "swim_dart", "in_water", "jets_away"),
        "D", "SUM", "SEA", ease=0.5, count=("a few", "a school", "a boiling school"), life=25))
    a(R("sand_flounder", "sand flounder", ("flounder", "sand flounder", "patiki", "pātiki"), ("flatfish", "sand", "eyes", "camouflage", "flat"), "surf",
        ob(25, 25, "flat_oval", "tan", "brown", "mottled", "matt", "rough", "glide_slow", "half_buried", "buries"),
        "N", "RES", "SEA", ease=0.2, count=("one", "one", "two"), life=8))
    a(R("snapper", "snapper", ("snapper", "tamure", "tāmure", "pagrus"), ("snapper", "fishing", "reef", "pink", "bream"), "offshore",
        ob(45, 45, "fusiform", "pink", "blue", "spotted", "wet_gloss", "scaled", "swim_dart", "in_water", "jets_away"),
        "D", "SUM", "SEA", ease=0.35, count=("one", "a few", "a school"), life=40, days=0.6))
    a(R("conger_eel", "conger eel", ("conger eel", "conger", "ngoiro"), ("eel", "crevice", "predator", "reef", "night"), "mussel_shelf",
        ob(150, 160, "serpent_long", "dark_grey", "pale_grey", "two_tone", "wet_gloss", "smooth", "undulate", "crevice", "bites"),
        "N", "RES", "SEA", ease=0.1, count=("one", "one", "one"), life=30, days=0.1, tide="low", note="bites"))
    a(R("kingfish", "kingfish", ("kingfish", "haku", "yellowtail"), ("kingfish", "jack", "fast", "predator", "yellow stripe"), "offshore",
        ob(90, 90, "fusiform", "blue_green", "yellow", "streaked", "wet_gloss", "scaled", "swim_dart", "in_water", "jets_away"),
        "D", "SUM", "BIG", ease=0.4, count=("one", "a few", "a school"), life=25, days=0.3))
    a(R("eagle_ray", "eagle ray", ("eagle ray", "stingray", "whai", "short-tailed stingray", "stingray"), ("ray", "wings", "barb", "sting", "sand"), "surf",
        ob(100, 150, "flat_wing", "dark_grey", "white", "two_tone", "wet_gloss", "smooth", "undulate", "in_water", "stings"),
        "D", "SUM", "BIG", ease=0.55, count=("one", "one", "two"), life=20, days=0.15, note="barbed tail"))
    a(R("rig_shark", "rig shark", ("rig", "rig shark", "pioke", "school shark", "shark"), ("shark", "fin", "predator", "teeth", "gummy"), "offshore",
        ob(110, 110, "tapered_big", "grey", "white", "two_tone", "wet_gloss", "smooth", "undulate", "in_water", "bites"),
        "N", "RES", "BIG", ease=0.4, count=("one", "one", "two"), life=25, days=0.1))
    a(R("great_white_shark", "great white shark", ("great white", "great white shark", "white pointer", "mango taniwha"), ("shark", "fin", "predator", "teeth", "apex"), "offshore",
        ob(400, 450, "tapered_big", "grey", "white", "two_tone", "wet_gloss", "smooth", "undulate", "in_water", "bites"),
        "D", "SUM", "BIG", ease=0.7, count=("one", "one", "one"), life=60, days=0.01, note="rare; dangerous"))
    a(R("ocean_sunfish", "ocean sunfish", ("sunfish", "ocean sunfish", "mola"), ("sunfish", "drifts", "jellyfish", "huge", "surface"), "offshore",
        ob(150, 180, "disc_tall", "grey", None, "plain", "matt", "leathery", "lie_flat", "afloat", "ignores"),
        "D", "SUM", "BIG", ease=0.6, count=("one", "one", "one"), life=20, days=0.02, note="rare"))
    return X
