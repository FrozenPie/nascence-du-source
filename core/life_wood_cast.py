"""
Nascence — THE WOODS BESTIARY: the cast (2026-11-02; docs/staged/wood_creatures.md, job J-3064). The 145 creatures that, with the 5 pilot rows in
core/life_wood.py, make the 150. ONE ROW PER SPECIES; every look is composed from the observable tuple by life_shore.compose(); the names below
(species, book_names, notes) are hidden truth that feeds only the learning ledger (D-0129: a name needs a book AND a face) and the leak test.

How to read a row:  R(key, species, book_names, book_words, zone, ob(size_cm, span_cm, shape, colour, colour2, pattern, sheen, covering, motion,
position, on_disturb[, counts]), hours, season, weather, ease=, count=, life=, days=, note=)

Entries that cannot be seen without a turn-stone / peel-bark / lens hand are written as WHAT SHOWS (under a log, under loose bark, in the silt) with a low
ease, so they appear rarely and only to someone looking at that place; the dead-wood termite and the vegetable caterpillar are the extreme cases.
Regional entries (North Island only) are written, flagged in `note`, and left for the founder to drop once he says which island the cottage is on (J-3065).
Biology (season, hours, size, colours) is general knowledge of NZ bush and is NOT checked against a reference.
Zero LLM, additive-only, no I/O. Registered by life_wood.rows() only when data/life_flags.json has "wood_bestiary": true.
"""
from __future__ import annotations

from core import life_wood as LW
from core.life_shore_cast import SEASONS as _S
from core.life_wood import R, ob

LW.WEATHER.update({
    "FLY": {"rain": 0.05, "wind": 0.15, "storm": 0.0, "frost": 0.2},
    "WET": {"rain": 1.6, "wind": 0.8, "storm": 0.3, "frost": 0.4},
})
SEAS = dict(_S)
SEAS.update({
    "RES": [1.0] * 12,
    "WASP": [0.6, 0.8, 1.0, 1.0, 0.6, 0.1, 0.0, 0.0, 0.0, 0.1, 0.2, 0.4],
    "NOVFEB": [1.0, 0.6, 0.2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.3, 0.9, 1.0],
    "SPRING": [0.2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.1, 0.6, 1.0, 1.0, 0.6],
})
SWARM = ("a few", "a cloud of them", "a thick cloud of them")
C3 = ("one", "a few", "several")
PAIR = ("one", "a pair", "several")


def rows() -> list[dict]:
    X: list[dict] = []
    a = X.append

    # ── beetles and weevils ──────────────────────────────────────────────────────────────────────────────────
    a(R("longhorn_beetle", "native longhorn beetle", ("longhorn beetle", "native longhorn beetle", "longhorn"), ("feelers", "bore", "wood", "larvae", "native"), "deadfall",
        ob(2.0, 4.0, "beetle_longfeelers", "brown", "tan", "banded", "matt", "hairy", "crawl", "on_bark", "freezes"), "N", SEAS["OCTMAR"], "BUG", ease=0.3, count=C3, life=2))
    a(R("forest_ground_beetle", "forest ground beetle", ("ground beetle", "forest ground beetle", "carabid"), ("predator", "leaf litter", "night", "fast", "black"), "leaf_floor",
        ob(3.0, 3.5, "beetle_round", "black", None, "plain", "glossy", "smooth", "run_stop", "in_litter", "flees"), "N", SEAS["RES"], "BUG", ease=0.35, count=C3, life=2, note="a named species of the grouped ground_beetle row"))
    a(R("stag_beetle", "native stag beetle", ("stag beetle", "native stag beetle", "lissotes"), ("jaws", "mandibles", "rotting wood", "rare", "native"), "deadfall",
        ob(2.5, 3.5, "beetle_jaws", "dark_brown", None, "plain", "glossy", "smooth", "crawl", "under_bark", "freezes"), "N", SEAS["RES"], "BUG", ease=0.12, count=("one", "one", "two"), life=3, days=0.3, note="native; rare"))
    a(R("click_beetle", "click beetle", ("click beetle", "elaterid"), ("click", "flips", "spring", "larvae", "wireworm"), "undergrowth",
        ob(1.2, 1.4, "beetle_round", "brown", "cream", "mottled", "matt", "scaled", "run_stop", "on_leaf", "freezes"), "D", SEAS["SPRSUM"], "BUG", ease=0.3, count=C3, life=1))
    a(R("pie_dish_beetle", "pie-dish beetle", ("pie-dish beetle", "pie dish beetle", "platisus"), ("flat", "bark", "fungus", "rotting", "native"), "deadfall",
        ob(1.5, 1.5, "beetle_flat", "dark_brown", "orange_brown", "edged", "matt", "plated", "crawl", "under_bark", "freezes"), "N", SEAS["RES"], "BUG", ease=0.12, count=C3, life=2))
    a(R("giraffe_weevil", "giraffe weevil", ("giraffe weevil", "lasiorhynchus"), ("neck", "snout", "male", "rare", "bark"), "oak_trunk",
        ob(6.0, 9.0, "beetle_snout", "black", "red", "banded", "glossy", "smooth", "crawl", "on_bark", "freezes"), "N", SEAS["RES"], "BUG", ease=0.2, count=("one", "one", "two"), life=2, days=0.1, note="native; rare; North Island only"))
    a(R("clover_root_weevil", "clover root weevil", ("clover root weevil", "sitona"), ("clover", "pasture", "introduced", "pest", "roots"), "clearing",
        ob(0.5, 0.6, "beetle_snout", "grey", "tan", "mottled", "matt", "scaled", "run_stop", "on_leaf", "freezes"), "A", SEAS["SPRSUM"], "BUG", ease=0.2, count=SWARM, life=1, note="invasive"))
    a(R("bracket_fungus_beetle", "bracket-fungus beetle", ("bracket-fungus beetle", "fungus beetle", "ciidae"), ("fungus", "bracket", "spores", "tiny", "rotting"), "deadfall",
        ob(0.4, 0.4, "beetle_round", "red", "black", "spotted", "glossy", "smooth", "crawl", "on_wood", "freezes"), "A", SEAS["RES"], "BUG", ease=0.2, count=C3, life=1))
    a(R("manuka_beetle", "manuka beetle", ("manuka beetle", "mānuka beetle", "pyronota"), ("flowers", "swarm", "summer", "tea tree", "kanuka"), "kanuka_grove",
        ob(1.2, 1.4, "beetle_round", "olive_green", None, "plain", "iridescent", "smooth", "fly_straight", "on_flower", "flees"), "D", SEAS["SUM"], "FLY", ease=0.4, count=SWARM, life=1, note="seasonal swarms on the white-flowering trees"))
    a(R("grass_grub_beetle", "grass grub beetle", ("grass grub", "grass grub beetle", "costelytra"), ("pasture", "larvae", "lamp", "spring", "roots"), "clearing",
        ob(1.3, 1.5, "beetle_round", "tan", None, "plain", "matt", "hairy", "fly_straight", "on_ground", "buries"), "N", SEAS["SPRSUM"], "FLY", ease=0.3, count=SWARM, life=1, light="drawn", note="comes to the lamp"))
    a(R("darkling_beetle", "darkling beetle", ("darkling beetle", "tenebrionid", "mimopeus"), ("night", "litter", "dark", "scavenger", "beetle"), "leaf_floor",
        ob(1.0, 1.2, "beetle_flat", "black", None, "plain", "matt", "ridged", "crawl", "in_litter", "freezes"), "N", SEAS["RES"], "BUG", ease=0.25, count=C3, life=2))
    a(R("dung_beetle", "native dung beetle", ("dung beetle", "native dung beetle", "saprosites"), ("dung", "litter", "decaying", "tiny", "native"), "leaf_floor",
        ob(0.8, 0.9, "beetle_round", "dark_brown", "orange_brown", "edged", "glossy", "smooth", "run_stop", "in_litter", "flees"), "A", SEAS["RES"], "BUG", ease=0.2, count=C3, life=1))
    a(R("pine_bark_beetle", "black pine bark beetle", ("bark beetle", "black pine bark beetle", "hylastes"), ("pine", "bark", "introduced", "tunnels", "tiny"), "deadfall",
        ob(0.4, 0.4, "beetle_round", "dark_brown", None, "plain", "matt", "hairy", "crawl", "under_bark", "freezes"), "A", SEAS["SPRSUM"], "BUG", ease=0.12, count=C3, life=1, note="invasive"))

    # ── moths, butterflies and caterpillars ──────────────────────────────────────────────────────────────────
    a(R("red_admiral", "red admiral", ("red admiral", "kahukura", "bassaris gonerilla"), ("butterfly", "nettle", "wings", "migrates", "red band"), "clearing",
        ob(2.5, 6.0, "winged_broad", "black", "red", "banded", "matt", "scaled", "flutter", "on_flower", "flees"), "D", SEAS["SUM"], "FLY", ease=0.5, count=PAIR, life=1, days=0.5, note="native"))
    a(R("forest_ringlet", "forest ringlet", ("forest ringlet", "dodonidia helmsii"), ("butterfly", "shade", "eyespots", "forest", "summer"), "tree_ferns",
        ob(2.0, 4.5, "winged_broad", "brown", "orange", "spotted", "matt", "scaled", "flutter", "in_foliage", "flees"), "D", SEAS["SUM"], "FLY", ease=0.3, count=("one", "one", "two"), life=1, days=0.3))
    a(R("southern_blue", "southern blue", ("southern blue", "zizina otis"), ("butterfly", "clover", "small", "blue", "wings"), "clearing",
        ob(1.0, 2.5, "winged_broad", "blue", "brown", "edged", "matt", "scaled", "flutter", "on_flower", "flees"), "D", SEAS["SUM"], "FLY", ease=0.3, count=C3, life=1))
    a(R("convolvulus_hawk_moth", "convolvulus hawk moth", ("hawk moth", "convolvulus hawk moth", "herse convolvuli"), ("hover", "proboscis", "dusk", "migrant", "flowers"), "clearing",
        ob(5.0, 10.0, "moth_form", "grey", "pink", "banded", "matt", "hairy", "hover_dart", "in_air", "flees"), "N", SEAS["NOVFEB"], "FLY", ease=0.35, count=("one", "one", "two"), life=1, days=0.15, note="summer migrant"))
    a(R("emperor_gum_moth", "emperor gum moth", ("emperor gum moth", "opodiphthera eucalypti"), ("eyespots", "gum", "large", "night", "introduced"), "canopy",
        ob(7.0, 12.0, "moth_form", "tan", "brown", "spotted", "matt", "hairy", "flutter", "in_foliage", "freezes"), "N", SEAS["NOVFEB"], "FLY", ease=0.3, count=("one", "one", "two"), life=1, days=0.1, note="invasive; northern North Island only"))
    a(R("porina_moth", "porina moth", ("porina", "porina moth", "wiseana"), ("pasture", "autumn", "larvae", "night", "swarm"), "clearing",
        ob(3.0, 6.0, "moth_form", "brown", "tan", "streaked", "matt", "hairy", "flutter", "in_air", "flees"), "N", SEAS["AUTWIN"], "FLY", ease=0.3, count=C3, life=1))
    a(R("scoparia_moth", "scoparia moth", ("scoparia", "scoparia moth"), ("lichen", "moss", "bark", "small", "grey"), "oak_trunk",
        ob(0.8, 1.8, "moth_form", "pale_grey", "dark_grey", "marbled", "matt", "scaled", "still", "on_bark", "flees"), "N", SEAS["RES"], "FLY", ease=0.15, count=C3, life=1))
    a(R("leafroller_moth", "native leafroller moth", ("leafroller", "leafroller moth", "tortricid"), ("leaf", "rolled", "silk", "larva", "small"), "undergrowth",
        ob(1.0, 2.0, "moth_form", "tan", "brown", "banded", "matt", "scaled", "flutter", "on_leaf", "freezes"), "N", SEAS["SPRSUM"], "FLY", ease=0.2, count=C3, life=1))
    a(R("light_brown_apple_moth", "light-brown apple moth", ("light-brown apple moth", "apple moth", "epiphyas postvittana"), ("apple", "leafroller", "pest", "introduced", "orchard"), "undergrowth",
        ob(1.0, 2.2, "moth_form", "tan", "olive_brown", "mottled", "matt", "scaled", "flutter", "on_leaf", "freezes"), "N", SEAS["SPRSUM"], "FLY", ease=0.2, count=C3, life=1, note="invasive"))
    a(R("bagworm", "bagworm", ("bagworm", "case moth", "bag moth", "oiketicus"), ("bag", "silk", "twigs", "larva", "hangs"), "undergrowth",
        ob(2.0, 2.0, "bag_hanging", "tan", None, "plain", "matt", "rough", "still", "hanging", "retracts"), "A", SEAS["RES"], "BUG", ease=0.35, count=C3, life=1))
    a(R("looper_moth", "looper moth", ("looper moth", "geometrid", "geometer"), ("looper", "night", "canopy", "wings", "twig"), "canopy",
        ob(1.2, 3.0, "moth_form", "pale_grey", "dark_grey", "streaked", "matt", "scaled", "flutter", "in_foliage", "flees"), "N", SEAS["SPRSUM"], "FLY", ease=0.2, count=C3, life=1))
    a(R("cutworm", "cutworm caterpillar", ("cutworm", "cutworm caterpillar", "agrotis"), ("caterpillar", "seedlings", "night", "soil", "pest"), "leaf_floor",
        ob(4.0, 4.0, "tube_segmented", "brown", None, "plain", "matt", "smooth", "crawl", "in_litter", "curls"), "N", SEAS["SPRSUM"], "BUG", ease=0.25, count=C3, life=1))
    a(R("armyworm", "armyworm caterpillar", ("armyworm", "armyworm caterpillar", "persectania"), ("caterpillar", "grass", "marching", "night", "pest"), "clearing",
        ob(3.5, 3.5, "tube_segmented", "green", "dark_brown", "streaked", "matt", "smooth", "crawl", "on_ground", "curls"), "N", SEAS["SPRSUM"], "BUG", ease=0.25, count=C3, life=1))
    a(R("looper_caterpillar", "looper caterpillar", ("looper caterpillar", "looper", "inchworm", "geometrid larva"), ("twig", "caterpillar", "loops", "mimic", "inch"), "undergrowth",
        ob(3.0, 3.0, "twig_held_out", "olive_brown", None, "plain", "matt", "smooth", "sway_twig", "hanging", "freezes"), "A", SEAS["SPRSUM"], "BUG", ease=0.15, count=C3, life=1, note="holds itself out like a twig"))

    # ── flies and midges ─────────────────────────────────────────────────────────────────────────────────────
    a(R("bluebottle", "bluebottle", ("bluebottle", "blowfly", "calliphora"), ("carrion", "maggots", "blue", "buzz", "eggs"), "deadfall",
        ob(1.1, 2.0, "fly_stout", "blue", None, "plain", "glossy", "bristled", "fly_straight", "on_wood", "flees"), "D", SEAS["SUM"], "FLY", ease=0.4, count=C3, life=1))
    a(R("crane_fly", "crane fly", ("crane fly", "daddy longlegs fly", "tipulid"), ("long legs", "clumsy", "wings", "harmless", "damp"), "leaf_floor",
        ob(1.8, 4.0, "winged_slender", "tan", None, "plain", "matt", "smooth", "flutter", "in_litter", "flees"), "C", SEAS["SPRSUM"], "FLY", ease=0.3, count=C3, life=1))
    a(R("bush_mosquito", "bush mosquito", ("bush mosquito", "waeroa", "culex"), ("bite", "dusk", "whine", "blood", "native"), "undergrowth",
        ob(0.5, 1.0, "winged_slender", "dark_brown", "white", "banded", "matt", "hairy", "hover_dart", "in_air", "flees"), "C", SEAS["SUM"], "FLY", ease=0.2, count=SWARM, life=1, note="bites"))
    a(R("striped_mosquito", "striped mosquito", ("striped mosquito", "aedes notoscriptus"), ("bite", "stripes", "tree hole", "container", "introduced"), "oak_trunk",
        ob(0.5, 1.0, "winged_slender", "black", "white", "streaked", "matt", "hairy", "hover_dart", "in_air", "flees"), "C", SEAS["SUM"], "FLY", ease=0.2, count=SWARM, life=1, note="invasive; bites"))
    a(R("hoverfly", "hoverfly", ("hoverfly", "syrphid", "flower fly"), ("hover", "flowers", "stripes", "mimic", "pollen"), "clearing",
        ob(1.2, 2.0, "fly_stout", "yellow", "black", "banded", "glossy", "smooth", "hover_dart", "on_flower", "flees"), "D", SEAS["SUM"], "FLY", ease=0.4, count=C3, life=1))
    a(R("fungus_gnat", "fungus gnat", ("fungus gnat", "mycetophilid"), ("fungus", "damp", "tiny", "litter", "larvae"), "leaf_floor",
        ob(0.3, 0.5, "winged_small", "dark_grey", None, "plain", "matt", "hairy", "hover_dart", "in_air", "flees"), "C", SEAS["RES"], "FLY", ease=0.12, count=SWARM, life=1))
    a(R("midge_swarm", "non-biting midge", ("midge", "non-biting midge", "chironomid"), ("swarm", "dance", "harmless", "water", "larvae"), "clearing",
        ob(0.3, 0.4, "winged_small", "pale_grey", None, "plain", "matt", "smooth", "hover_dart", "in_air", "flees"), "C", SEAS["SUM"], "FLY", ease=0.3, count=SWARM, life=1, note="a dancing swarm"))
    a(R("robber_fly", "robber fly", ("robber fly", "asilid", "neoitamus"), ("predator", "ambush", "beak", "prey", "bristles"), "clearing",
        ob(2.5, 3.5, "fly_long", "grey", "black", "streaked", "matt", "bristled", "swoop", "on_ground", "flees"), "D", SEAS["SUM"], "FLY", ease=0.3, count=("one", "one", "two"), life=1))
    a(R("long_legged_fly", "long-legged fly", ("long-legged fly", "dolichopodid"), ("metallic", "wet", "moss", "green", "stones"), "the_spring",
        ob(0.5, 0.7, "fly_stout", "green", None, "plain", "iridescent", "bristled", "run_stop", "on_wet_stone", "flees"), "D", SEAS["SUM"], "FLY", ease=0.2, count=C3, life=1))

    # ── bees, wasps and ants ─────────────────────────────────────────────────────────────────────────────────
    a(R("german_wasp", "German wasp", ("german wasp", "vespula germanica"), ("sting", "nest", "ground", "colony", "autumn"), "leaf_floor",
        ob(1.3, 2.2, "waisted_winged", "yellow", "black", "banded", "glossy", "smooth", "hover_dart", "on_ground", "stings"), "S", SEAS["WASP"], "FLY", ease=0.45, count=C3, life=1, note="invasive; stings"))
    a(R("common_wasp", "common wasp", ("common wasp", "vespula vulgaris"), ("sting", "nest", "honeydew", "colony", "aggressive"), "canopy",
        ob(1.4, 2.3, "waisted_winged", "yellow", "black", "streaked", "glossy", "smooth", "hover_dart", "in_foliage", "stings"), "S", SEAS["WASP"], "FLY", ease=0.35, count=C3, life=1, note="invasive; stings"))
    a(R("australian_paper_wasp", "Australian paper wasp", ("australian paper wasp", "polistes humilis"), ("sting", "paper nest", "umbrella", "colony", "introduced"), "undergrowth",
        ob(1.6, 2.8, "waisted_winged", "orange_brown", "yellow", "banded", "glossy", "smooth", "hover_dart", "on_leaf", "stings"), "S", SEAS["SUM"], "FLY", ease=0.4, count=C3, life=1, note="invasive; stings"))
    a(R("potter_wasp", "potter wasp", ("potter wasp", "delta wasp", "delta"), ("mud", "pot", "nest", "caterpillars", "slender"), "oak_trunk",
        ob(1.5, 2.5, "waisted_winged", "black", "yellow", "banded", "glossy", "smooth", "hover_dart", "on_bark", "flees"), "S", SEAS["SUM"], "FLY", ease=0.3, count=("one", "one", "two"), life=1, note="invasive; builds mud pots on bark"))
    a(R("giant_ichneumon", "giant ichneumon wasp", ("giant ichneumon", "ichneumon wasp", "megarhyssa"), ("ovipositor", "tail", "harmless", "huhu", "parasite"), "oak_trunk",
        ob(4.0, 9.0, "ichneumon_form", "orange_brown", "black", "banded", "glossy", "smooth", "flutter", "on_bark", "flees"), "D", SEAS["SUM"], "FLY", ease=0.3, count=("one", "one", "two"), life=1, days=0.3, note="harmless; long egg-laying tail"))
    a(R("spider_hunting_wasp", "spider-hunting wasp", ("spider-hunting wasp", "spider wasp", "pompilid"), ("spiders", "paralyse", "burrow", "hunt", "wasp"), "leaf_floor",
        ob(1.5, 2.5, "waisted_winged", "black", "orange", "accented", "glossy", "smooth", "run_stop", "on_ground", "flees"), "D", SEAS["SUM"], "FLY", ease=0.3, count=("one", "one", "two"), life=1))
    a(R("black_native_ant", "small black native ant", ("native ant", "small black ant", "monomorium"), ("colony", "trail", "workers", "nest", "tiny"), "leaf_floor",
        ob(0.3, 0.4, "ant_form", "black", None, "plain", "glossy", "smooth", "run_stop", "in_litter", "flees"), "D", SEAS["SUM"], "BUG", ease=0.3, count=("a few", "a long line of them", "a stream of them"), life=1))
    a(R("hunter_ant", "hunter ant", ("hunter ant", "ponerine ant", "amblyopone"), ("sting", "predator", "slow", "centipede", "nest"), "deadfall",
        ob(1.0, 1.2, "ant_form", "orange_brown", None, "plain", "matt", "smooth", "crawl", "under_bark", "stings"), "N", SEAS["RES"], "BUG", ease=0.12, count=C3, life=2, note="stings"))

    # ── cicadas, wetas, stick insects and other insects ──────────────────────────────────────────────────────
    a(R("chorus_cicada", "chorus cicada", ("chorus cicada", "kihikihi", "amphipsalta zelandica"), ("cicada", "loud", "summer", "chorus", "wings"), "kanuka_grove",
        ob(2.5, 4.5, "cicada_form", "green", "black", "mottled", "matt", "smooth", "still", "on_branch", "flees"), "S", SEAS["SUM"], "FLY", ease=0.4, count=C3, life=3, note="a named species of the grouped cicada row"))
    a(R("clapping_cicada", "clapping cicada", ("clapping cicada", "amphipsalta cingulata"), ("cicada", "claps", "wings", "summer", "bark"), "oak_trunk",
        ob(3.0, 5.5, "cicada_form", "brown", "tan", "mottled", "matt", "smooth", "still", "on_trunk", "flees"), "S", SEAS["SUM"], "FLY", ease=0.4, count=C3, life=3))
    a(R("tree_weta", "tree wētā", ("tree weta", "tree wētā", "weta-punga", "wētā-punga", "hemideina"), ("weta", "bore hole", "tree", "night", "antennae"), "oak_trunk",
        ob(5.0, 12.0, "jumper_long_legs", "brown", "tan", "banded", "matt", "spined", "spring", "in_tree_hole", "freezes"), "N", SEAS["RES"], "BUG", ease=0.25, count=("one", "one", "two"), life=2, note="a named species of the grouped weta row"))
    a(R("ground_weta", "ground wētā", ("ground weta", "ground wētā", "hemiandrus"), ("weta", "burrow", "night", "ground", "spines"), "leaf_floor",
        ob(4.5, 10.0, "jumper_long_legs", "dark_brown", None, "plain", "matt", "spined", "spring", "in_litter", "freezes"), "N", SEAS["RES"], "BUG", ease=0.2, count=C3, life=2))
    a(R("forest_cave_weta", "forest cave wētā", ("cave weta", "forest cave weta", "tokoriro", "rhaphidophoridae"), ("weta", "cave", "dark", "antennae", "damp"), "deadfall",
        ob(4.2, 12.0, "jumper_long_legs", "dark_brown", "tan", "banded", "matt", "spined", "spring", "under_log", "freezes"), "N", SEAS["RES"], "BUG", ease=0.2, count=C3, life=2, note="a different species from the shore's cave weta"))
    a(R("smooth_stick_insect", "smooth stick insect", ("stick insect", "smooth stick insect", "clitarchus"), ("twig", "camouflage", "night", "leaves", "female"), "undergrowth",
        ob(8.0, 8.0, "twig_body", "green", None, "plain", "matt", "smooth", "sway_twig", "in_foliage", "freezes"), "N", SEAS["SUM"], "BUG", ease=0.12, count=("one", "one", "two"), life=2))
    a(R("prickly_stick_insect", "prickly stick insect", ("prickly stick insect", "acanthoxyla"), ("twig", "spines", "camouflage", "female", "parthenogenesis"), "tree_ferns",
        ob(8.0, 8.5, "twig_body", "olive_brown", None, "plain", "matt", "spined", "sway_twig", "hanging", "freezes"), "N", SEAS["SUM"], "BUG", ease=0.12, count=("one", "one", "two"), life=2))
    a(R("praying_mantis", "praying mantis", ("praying mantis", "mantis", "orthodera"), ("mantis", "ambush", "forelegs", "prey", "green"), "clearing",
        ob(6.0, 7.0, "mantis_form", "green", "tan", "streaked", "matt", "smooth", "still", "on_leaf", "freezes"), "D", SEAS["SUM"], "BUG", ease=0.2, count=("one", "one", "two"), life=1))
    a(R("native_cockroach", "native cockroach", ("native cockroach", "cockroach", "celatoblatta"), ("night", "litter", "scavenger", "flat", "native"), "the_old_oak",
        ob(2.0, 2.5, "roach_form", "dark_brown", "tan", "edged", "glossy", "smooth", "run_stop", "in_litter", "flees"), "N", SEAS["RES"], "BUG", ease=0.2, count=C3, life=2))
    a(R("european_earwig", "European earwig", ("european earwig", "earwig", "forficula auricularia"), ("pincers", "night", "garden", "introduced", "forceps"), "deadfall",
        ob(1.3, 1.5, "six_legged_pincers", "dark_brown", None, "plain", "glossy", "smooth", "run_stop", "under_log", "flees"), "N", SEAS["RES"], "BUG", ease=0.2, count=C3, life=1, note="invasive"))
    a(R("common_katydid", "common katydid", ("katydid", "common katydid", "caedicia simplex"), ("green", "song", "leaf", "night", "introduced"), "undergrowth",
        ob(3.0, 4.5, "katydid_form", "green", None, "plain", "matt", "smooth", "still", "in_foliage", "freezes"), "N", SEAS["SUM"], "BUG", ease=0.12, count=("one", "one", "two"), life=1, note="invasive; northern North Island only"))
    a(R("green_shield_bug", "native green shield bug", ("shield bug", "green shield bug", "glaucias amyoti"), ("stink", "smell", "green", "leaf", "native"), "undergrowth",
        ob(1.2, 1.3, "shield_form", "olive_green", None, "plain", "glossy", "smooth", "crawl", "on_leaf", "freezes"), "D", SEAS["SUM"], "BUG", ease=0.25, count=C3, life=1, note="smells when handled"))
    a(R("passionvine_hopper", "passionvine hopper", ("passionvine hopper", "scolypopa australis"), ("hopper", "honeydew", "swarm", "summer", "introduced"), "clearing",
        ob(0.6, 1.0, "hopper_form", "pale_grey", "brown", "spotted", "matt", "smooth", "spring", "on_leaf", "flees"), "D", SEAS["SUM"], "FLY", ease=0.3, count=SWARM, life=1, note="invasive; summer swarms"))
    a(R("brown_lacewing", "brown lacewing", ("brown lacewing", "lacewing", "micromus"), ("lace", "wings", "aphids", "night", "delicate"), "undergrowth",
        ob(1.0, 2.0, "lacewing_form", "brown", None, "plain", "matt", "smooth", "flutter", "on_leaf", "flees"), "N", SEAS["SPRSUM"], "FLY", ease=0.2, count=C3, life=1))
    a(R("springtail", "springtail", ("springtail", "collembola"), ("tiny", "springs", "litter", "damp", "moss"), "leaf_floor",
        ob(0.2, 0.2, "springtail_form", "grey", None, "plain", "matt", "smooth", "spring", "in_litter", "flees"), "A", SEAS["RES"], "BUG", ease=0.1, count=("a few", "a scatter", "a grey dust of them"), life=1))
    a(R("dampwood_termite", "dampwood termite", ("dampwood termite", "termite", "kalotermes"), ("termite", "rotting wood", "galleries", "colony", "pale"), "deadfall",
        ob(0.6, 0.6, "termite_form", "cream", None, "plain", "matt", "soft", "crawl", "under_bark", "retracts"), "A", SEAS["RES"], "BUG", ease=0.05, count=("a few", "a crowd", "a seething crowd"), life=1, note="lives inside rotting wood; almost never seen"))

    # ── dragonflies and damselflies ──────────────────────────────────────────────────────────────────────────
    a(R("bush_giant_dragonfly", "bush giant dragonfly", ("bush giant dragonfly", "kapokapowai", "uropetala carovei"), ("dragonfly", "giant", "wingspan", "bog", "summer"), "clearing",
        ob(8.0, 12.0, "dragonfly_form", "black", "yellow", "banded", "glossy", "smooth", "fly_straight", "in_air", "flees"), "D", SEAS["SUM"], "FLY", ease=0.5, count=("one", "one", "two"), life=3, days=0.3))
    a(R("yellow_spotted_dragonfly", "yellow-spotted dragonfly", ("yellow-spotted dragonfly", "procordulia grayi"), ("dragonfly", "spots", "summer", "pond", "hawker"), "clearing",
        ob(5.0, 8.0, "dragonfly_form", "dark_brown", "yellow", "spotted", "glossy", "smooth", "fly_straight", "in_air", "flees"), "D", SEAS["SUM"], "FLY", ease=0.4, count=("one", "one", "two"), life=2))
    a(R("red_damselfly", "red damselfly", ("red damselfly", "xanthocnemis zealandica", "damselfly"), ("damselfly", "red", "pond", "slender", "summer"), "stream",
        ob(3.0, 4.0, "damselfly_form", "red", None, "plain", "glossy", "smooth", "flutter", "on_leaf", "flees"), "D", SEAS["SUM"], "FLY", ease=0.3, count=C3, life=1))
    a(R("blue_damselfly", "blue damselfly", ("blue damselfly", "austrolestes colensonis"), ("damselfly", "blue", "pond", "slender", "summer"), "stream",
        ob(3.0, 4.0, "damselfly_form", "blue", "black", "banded", "glossy", "smooth", "flutter", "on_leaf", "flees"), "D", SEAS["SUM"], "FLY", ease=0.3, count=C3, life=1))

    # ── spiders and harvestmen ───────────────────────────────────────────────────────────────────────────────
    a(R("nursery_web_spider", "nursery web spider", ("nursery web spider", "dolomedes minor"), ("fishing", "water", "egg sac", "nursery", "large"), "stream",
        ob(1.8, 6.0, "eight_legged", "brown", "tan", "streaked", "matt", "hairy", "run_stop", "on_wet_stone", "flees", counts={"legs": 8}), "D", SEAS["SUM"], "BUG", ease=0.3, count=("one", "one", "two"), life=2))
    a(R("sheet_web_spider", "sheet-web spider", ("sheet-web spider", "sheet web spider", "cambridgea", "linyphiid"), ("web", "sheet", "hammock", "silk", "dew"), "undergrowth",
        ob(0.8, 2.5, "eight_legged", "dark_grey", "cream", "marbled", "matt", "smooth", "still", "in_web", "freezes"), "A", SEAS["RES"], "BUG", ease=0.3, count=C3, life=2))
    a(R("tunnelweb_spider", "tunnelweb spider", ("tunnelweb spider", "tunnel web spider", "porrhothele antipodiana"), ("tunnel", "silk", "venom", "bite", "nest"), "leaf_floor",
        ob(2.5, 6.0, "spider_heavy", "black", None, "plain", "glossy", "smooth", "run_stop", "under_log", "bites"), "N", SEAS["RES"], "BUG", ease=0.15, count=("one", "one", "two"), life=8, days=0.4, note="mild venom; North Island only"))
    a(R("trapdoor_spider", "trapdoor spider", ("trapdoor spider", "migas", "cyclosa"), ("trapdoor", "burrow", "lid", "silk", "ambush"), "leaf_floor",
        ob(2.5, 6.0, "spider_heavy", "brown", None, "plain", "matt", "hairy", "still", "in_litter", "retracts"), "N", SEAS["RES"], "BUG", ease=0.06, count=("one", "one", "one"), life=10, days=0.2, note="rare; lives in a hidden burrow"))
    a(R("jumping_spider", "jumping spider", ("jumping spider", "salticid", "trite"), ("jumps", "eyes", "stalks", "bark", "hunter"), "oak_trunk",
        ob(0.6, 1.2, "spider_stocky", "black", "white", "banded", "matt", "furred", "run_stop", "on_bark", "flees"), "D", SEAS["SUM"], "BUG", ease=0.3, count=C3, life=1))
    a(R("crab_spider", "crab spider", ("crab spider", "diaea", "thomisid"), ("flower", "ambush", "camouflage", "sidestep", "white"), "clearing",
        ob(0.7, 1.8, "eight_legged", "white", "yellow", "mottled", "matt", "smooth", "still", "on_flower", "freezes"), "D", SEAS["SUM"], "BUG", ease=0.12, count=C3, life=1))
    a(R("white_tailed_spider", "white-tailed spider", ("white-tailed spider", "white tailed spider", "lampona cylindrata"), ("wandering", "night", "white tip", "hunter", "introduced"), "leaf_floor",
        ob(1.5, 4.5, "eight_legged", "dark_grey", "white", "accented", "glossy", "smooth", "run_stop", "on_ground", "flees"), "N", SEAS["RES"], "BUG", ease=0.2, count=C3, life=2, note="invasive; the bite is more reputation than harm"))
    a(R("daddy_long_legs_spider", "daddy-long-legs spider", ("daddy-long-legs spider", "daddy long legs spider", "pholcus phalangioides"), ("cobweb", "long legs", "shaking", "introduced", "corners"), "deadfall",
        ob(0.8, 6.0, "spider_longlegs", "pale_grey", None, "plain", "matt", "smooth", "still", "under_bark", "freezes"), "N", SEAS["RES"], "BUG", ease=0.15, count=C3, life=2, note="invasive"))
    a(R("long_legged_harvestman", "long-legged harvestman", ("harvestman", "long-legged harvestman", "opiliones", "daddy long legs"), ("harvestman", "long legs", "no silk", "litter", "scavenger"), "undergrowth",
        ob(0.6, 7.0, "spider_longlegs", "brown", None, "plain", "matt", "smooth", "crawl", "in_foliage", "freezes"), "N", SEAS["RES"], "BUG", ease=0.2, count=C3, life=1))
    a(R("mite_harvestman", "mite harvestman", ("mite harvestman", "cyphophthalmi", "rakaia"), ("mite", "tiny", "damp", "litter", "ancient"), "leaf_floor",
        ob(0.3, 0.3, "harvest_round", "orange_brown", None, "plain", "matt", "rough", "crawl", "in_litter", "freezes"), "A", SEAS["RES"], "BUG", ease=0.05, count=C3, life=3, days=0.5))

    # ── millipedes and centipedes ────────────────────────────────────────────────────────────────────────────
    a(R("native_millipede", "native millipede", ("millipede", "native millipede", "diplopoda"), ("rings", "curls", "leaf litter", "decay", "legs"), "leaf_floor",
        ob(4.0, 4.0, "many_cylinder", "dark_brown", "orange", "banded", "glossy", "smooth", "crawl", "in_litter", "curls"), "N", SEAS["RES"], "BUG", ease=0.3, count=C3, life=3))
    a(R("flat_backed_millipede", "flat-backed millipede", ("flat-backed millipede", "polydesmid"), ("flat", "plates", "ridged", "decay", "legs"), "deadfall",
        ob(2.5, 2.5, "many_flat", "tan", "brown", "streaked", "matt", "plated", "crawl", "under_log", "curls"), "N", SEAS["RES"], "BUG", ease=0.2, count=C3, life=2))
    a(R("giant_centipede", "giant centipede", ("giant centipede", "cormocephalus", "centipede"), ("fangs", "venom", "bite", "night", "predator"), "deadfall",
        ob(12.0, 12.0, "many_fangs", "red", "dark_brown", "edged", "glossy", "smooth", "crawl", "under_log", "bites"), "N", SEAS["RES"], "BUG", ease=0.15, count=("one", "one", "two"), life=5, note="venomous bite"))
    a(R("stone_centipede", "stone centipede", ("stone centipede", "lithobiid", "centipede"), ("fast", "stones", "night", "predator", "legs"), "leaf_floor",
        ob(2.5, 2.5, "many_fangs", "brown", None, "plain", "matt", "smooth", "run_stop", "in_litter", "flees"), "N", SEAS["RES"], "BUG", ease=0.2, count=C3, life=3))

    # ── snails, slugs and worms ──────────────────────────────────────────────────────────────────────────────
    a(R("carnivorous_snail", "native carnivorous snail", ("carnivorous snail", "powelliphanta", "land snail", "pupurangi"), ("snail", "shell", "earthworms", "carnivorous", "rare"), "leaf_floor",
        ob(6.0, 6.0, "coil_flat", "olive_brown", "tan", "banded", "glossy", "smooth", "glide_slow", "in_litter", "retracts"), "N", SEAS["RES"], "WET", ease=0.1, count=("one", "one", "two"), life=20, days=0.3, note="native; the empty shells are what the older text shows"))
    a(R("small_land_snail", "small native land snail", ("land snail", "small native land snail", "charopid"), ("snail", "tiny", "shell", "litter", "native"), "leaf_floor",
        ob(0.4, 0.4, "spiral_cone", "tan", None, "plain", "glossy", "smooth", "glide_slow", "in_litter", "retracts"), "N", SEAS["RES"], "WET", ease=0.05, count=C3, life=3))
    a(R("garden_snail", "garden snail", ("garden snail", "cornu aspersum", "helix aspersa"), ("snail", "shell", "slime", "garden", "introduced"), "the_path",
        ob(3.0, 3.0, "spiral_cone", "brown", "tan", "banded", "glossy", "smooth", "glide_slow", "on_track", "retracts"), "N", SEAS["RES"], "WET", ease=0.4, count=C3, life=3, note="invasive"))
    a(R("leaf_veined_slug", "leaf-veined slug", ("leaf-veined slug", "athoracophorus"), ("slug", "veined", "back", "native", "damp"), "undergrowth",
        ob(4.0, 4.0, "slug_soft", "grey", "brown", "marbled", "wet_gloss", "slimy", "glide_slow", "on_leaf", "retracts"), "N", SEAS["RES"], "WET", ease=0.2, count=C3, life=2))
    a(R("keeled_slug", "keeled slug", ("keeled slug", "milax", "tandonia"), ("slug", "keel", "garden", "pest", "introduced"), "leaf_floor",
        ob(4.0, 4.0, "slug_soft", "olive_brown", None, "plain", "wet_gloss", "slimy", "glide_slow", "in_litter", "retracts"), "N", SEAS["RES"], "WET", ease=0.3, count=C3, life=1, note="invasive"))
    a(R("leopard_slug", "leopard slug", ("leopard slug", "limax maximus"), ("slug", "spots", "large", "mating", "introduced"), "deadfall",
        ob(12.0, 12.0, "slug_soft", "pale_grey", "black", "spotted", "wet_gloss", "slimy", "glide_slow", "on_wood", "retracts"), "N", SEAS["RES"], "WET", ease=0.4, count=("one", "one", "two"), life=2, note="invasive"))
    a(R("native_earthworm", "native earthworm", ("earthworm", "native earthworm", "noke", "megascolecid"), ("earthworm", "soil", "rain", "castings", "burrow"), "leaf_floor",
        ob(15.0, 15.0, "soft_worm", "pink", None, "plain", "wet_gloss", "slimy", "wriggle", "in_litter", "retracts"), "N", SEAS["RES"], "WET", ease=0.35, count=C3, life=4, note="comes to the surface after rain"))
    a(R("land_flatworm", "land flatworm", ("land flatworm", "flatworm", "geoplanid"), ("flatworm", "slime", "predator", "worms", "damp"), "deadfall",
        ob(6.0, 6.0, "ribbon_flat", "black", "orange", "streaked", "wet_gloss", "slimy", "glide_slow", "under_log", "retracts"), "N", SEAS["RES"], "WET", ease=0.08, count=("one", "one", "two"), life=2, days=0.4))

    # ── odd and wonderful ────────────────────────────────────────────────────────────────────────────────────
    a(R("peripatus", "peripatus", ("peripatus", "ngaokeoke", "velvet worm", "onychophoran"), ("velvet", "slime", "ancient", "legs", "rotting log"), "deadfall",
        ob(4.0, 4.0, "velvet_tube", "dark_grey", None, "plain", "matt", "soft", "crawl", "under_log", "retracts"), "N", SEAS["RES"], "WET", ease=0.05, count=("one", "one", "two"), life=6, days=0.15, note="native; protected; rare"))
    a(R("pseudoscorpion", "pseudoscorpion", ("pseudoscorpion", "false scorpion"), ("pincers", "tiny", "no sting", "litter", "predator"), "the_old_oak",
        ob(0.3, 0.4, "claws_tiny", "tan", None, "plain", "matt", "smooth", "run_stop", "in_litter", "retracts"), "A", SEAS["RES"], "BUG", ease=0.04, count=C3, life=3))
    a(R("horsehair_worm", "horsehair worm", ("horsehair worm", "gordian worm", "nematomorph"), ("hair", "parasite", "water", "cricket", "coil"), "the_spring",
        ob(25.0, 25.0, "soft_worm", "dark_brown", None, "plain", "wet_gloss", "slimy", "wriggle", "on_wet_stone", "retracts"), "A", SEAS["SUM"], "WATER", ease=0.1, count=("one", "one", "two"), life=1, days=0.1, note="rare; a parasite of insects"))
    a(R("barklouse", "barklouse", ("barklouse", "bark louse", "psocid"), ("bark", "lichen", "tiny", "mould", "harmless"), "oak_trunk",
        ob(0.2, 0.3, "six_legged", "clear", None, "plain", "glassy", "smooth", "run_stop", "on_bark", "flees"), "A", SEAS["RES"], "BUG", ease=0.05, count=("a few", "a scatter", "a swarm of them"), life=1))
    a(R("vegetable_caterpillar", "vegetable caterpillar", ("vegetable caterpillar", "awheto", "āwheto", "cordyceps"), ("fungus", "stalk", "caterpillar", "ghost moth", "dead"), "leaf_floor",
        ob(8.0, 15.0, "dead_stalked", "brown", None, "plain", "matt", "soft", "still", "in_litter", "ignores"), "A", SEAS["AUTWIN"], "BUG", ease=0.04, count=("one", "one", "one"), life=1, days=0.08, note="a dead caterpillar with a fungus stalk out of its head"))

    # ── freshwater: the spring and its stream ────────────────────────────────────────────────────────────────
    a(R("banded_kokopu", "banded kōkopu", ("banded kokopu", "banded kōkopu", "galaxias fasciatus"), ("galaxiid", "stream", "bands", "native", "dusk"), "stream",
        ob(20.0, 20.0, "fusiform", "dark_brown", "cream", "banded", "wet_gloss", "slimy", "swim_dart", "in_stream", "jets_away"), "C", SEAS["RES"], "WATER", ease=0.25, count=("one", "one", "two"), life=10, days=0.5, note="native"))
    a(R("koaro", "kōaro", ("koaro", "kōaro", "galaxias brevipinnis"), ("galaxiid", "climbs", "waterfall", "native", "rock"), "the_spring",
        ob(10.0, 10.0, "fusiform", "olive_brown", "cream", "mottled", "wet_gloss", "slimy", "climb_wet", "on_wet_stone", "jets_away"), "N", SEAS["RES"], "WATER", ease=0.15, count=C3, life=8, days=0.3, note="native; climbs wet rock"))
    a(R("common_bully", "common bully", ("common bully", "toitoi", "gobiomorphus cotidianus"), ("bully", "stream", "fins", "native", "stones"), "stream",
        ob(7.0, 7.0, "bully_form", "olive_brown", "black", "mottled", "wet_gloss", "scaled", "swim_dart", "in_stream", "jets_away"), "D", SEAS["RES"], "WATER", ease=0.3, count=C3, life=4, note="native"))
    a(R("redfin_bully", "redfin bully", ("redfin bully", "gobiomorphus huttoni"), ("bully", "red fin", "stream", "riffle", "native"), "stream",
        ob(7.0, 7.0, "bully_form", "dark_grey", "red", "edged", "wet_gloss", "scaled", "swim_dart", "in_stream", "jets_away"), "D", SEAS["RES"], "WATER", ease=0.25, count=C3, life=4, note="native"))
    a(R("freshwater_mussel", "freshwater mussel", ("freshwater mussel", "kakahi", "kākahi", "echyridella"), ("mussel", "silt", "filter", "native", "burrow"), "stream",
        ob(9.0, 9.0, "hinged_elongate", "dark_brown", None, "plain", "matt", "smooth", "clamped", "in_silt", "buries"), "A", SEAS["RES"], "WATER", ease=0.2, count=("one", "a few", "a bed of them"), life=30, note="native; half buried in silt"))
    a(R("freshwater_limpet", "freshwater limpet", ("freshwater limpet", "latia neritoides", "glowing limpet"), ("limpet", "glow", "stream", "rock", "native"), "the_spring",
        ob(0.5, 0.5, "clamped_cone", "grey", None, "plain", "matt", "smooth", "clamped", "on_wet_stone", "clamps_tight"), "N", SEAS["RES"], "WATER", ease=0.04, count=C3, life=1, days=0.1, note="native; North Island only; glows when disturbed at night"))
    a(R("mud_snail", "mud snail", ("mud snail", "potamopyrgus"), ("snail", "silt", "stream", "tiny", "native"), "stream",
        ob(1.0, 1.0, "spiral_cone", "dark_brown", None, "plain", "matt", "smooth", "glide_slow", "in_silt", "retracts"), "A", SEAS["RES"], "WATER", ease=0.2, count=("a few", "dozens of them", "a dark scatter of them"), life=2))
    a(R("bladder_snail", "bladder snail", ("bladder snail", "physa acuta"), ("snail", "pond", "introduced", "pest", "bubble"), "stream",
        ob(1.0, 1.0, "spiral_cone", "tan", None, "plain", "glossy", "smooth", "glide_slow", "on_wet_stone", "retracts"), "A", SEAS["SUM"], "WATER", ease=0.2, count=C3, life=1, note="invasive"))
    a(R("mayfly_nymph", "mayfly nymph", ("mayfly nymph", "mayfly", "deleatidium"), ("nymph", "stream", "gills", "stones", "tails"), "stream",
        ob(1.0, 1.8, "nymph_three", "olive_brown", None, "plain", "matt", "smooth", "crawl", "on_wet_stone", "flees"), "A", SEAS["RES"], "WATER", ease=0.1, count=("a few", "several", "dozens of them"), life=1))
    a(R("stonefly_nymph", "stonefly nymph", ("stonefly nymph", "stonefly", "zelandoperla"), ("nymph", "stream", "cold", "stones", "tails"), "stream",
        ob(1.8, 2.5, "nymph_two", "brown", "tan", "banded", "matt", "smooth", "crawl", "on_wet_stone", "flees"), "N", SEAS["RES"], "WATER", ease=0.1, count=C3, life=1))
    a(R("caddisfly_larva", "cased caddisfly larva", ("caddisfly larva", "cased caddisfly", "caddis", "olinga"), ("case", "sand grains", "larva", "stream", "builds"), "stream",
        ob(1.5, 1.5, "case_tube", "tan", None, "plain", "matt", "rough", "crawl", "in_stream", "retracts"), "A", SEAS["RES"], "WATER", ease=0.15, count=("a few", "several", "dozens of them"), life=1))
    a(R("backswimmer", "backswimmer", ("backswimmer", "notonectid", "anisops"), ("swims upside down", "pond", "bite", "oars", "predator"), "stream",
        ob(1.2, 1.4, "boatman_form", "cream", "brown", "two_tone", "wet_gloss", "smooth", "row_swim", "in_water", "jets_away"), "A", SEAS["SUM"], "WATER", ease=0.2, count=C3, life=1, note="can bite"))
    a(R("pond_skater", "pond skater", ("pond skater", "water strider", "microvelia"), ("surface", "water", "skates", "pond", "legs"), "stream",
        ob(1.2, 2.5, "skater_form", "dark_brown", None, "plain", "matt", "smooth", "skate_surface", "on_water", "flees"), "D", SEAS["SUM"], "WATER", ease=0.3, count=C3, life=1))
    a(R("diving_beetle", "diving beetle", ("diving beetle", "water beetle", "rhantus"), ("predator", "pond", "diving", "oars", "air bubble"), "stream",
        ob(1.4, 1.6, "beetle_oval_swim", "black", "yellow", "edged", "glossy", "smooth", "swim_dart", "in_water", "jets_away"), "A", SEAS["RES"], "WATER", ease=0.15, count=C3, life=2))
    a(R("freshwater_amphipod", "freshwater amphipod", ("amphipod", "freshwater amphipod", "paracalliope"), ("sideways", "scud", "stream", "tiny", "leaf litter"), "stream",
        ob(0.8, 0.9, "jointed_curve", "olive_brown", None, "plain", "matt", "smooth", "swim_dart", "in_stream", "jets_away"), "A", SEAS["RES"], "WATER", ease=0.1, count=("a few", "dozens of them", "a seething mass of them"), life=1))
    a(R("freshwater_shrimp", "freshwater shrimp", ("freshwater shrimp", "paratya curvirostris", "river shrimp"), ("shrimp", "transparent", "stream", "native", "feelers"), "stream",
        ob(2.5, 3.5, "jointed_curve", "clear", "brown", "spotted", "glassy", "smooth", "jet", "in_stream", "jets_away"), "N", SEAS["RES"], "WATER", ease=0.2, count=("a few", "several", "dozens of them"), life=2, note="native"))

    # ── lizards and frogs ────────────────────────────────────────────────────────────────────────────────────
    a(R("forest_gecko", "forest gecko", ("forest gecko", "mokopirirakau granulatus", "tuhua"), ("gecko", "night", "bark", "native", "granulated"), "oak_trunk",
        ob(7.0, 16.0, "lizard_form", "brown", "tan", "mottled", "matt", "scaled", "still", "on_trunk", "freezes"), "N", SEAS["RES"], "BUG", ease=0.1, count=("one", "one", "two"), life=20, days=0.2, note="native; protected"))
    a(R("copper_skink", "copper skink", ("copper skink", "oligosoma aeneum"), ("skink", "copper", "lizard", "litter", "native"), "leaf_floor",
        ob(5.0, 12.0, "lizard_form", "orange_brown", "dark_brown", "streaked", "glossy", "scaled", "run_stop", "in_litter", "flees"), "S", SEAS["SUM"], "BUG", ease=0.25, count=("one", "one", "two"), life=8, note="native"))
    a(R("ornate_skink", "ornate skink", ("ornate skink", "oligosoma ornatum"), ("skink", "ornate", "stripes", "lizard", "native"), "deadfall",
        ob(6.0, 15.0, "lizard_form", "dark_brown", "cream", "streaked", "glossy", "scaled", "run_stop", "on_wood", "flees"), "S", SEAS["SUM"], "BUG", ease=0.15, count=("one", "one", "two"), life=10, days=0.15, note="native; rare"))
    a(R("brown_skink", "brown skink", ("brown skink", "moko-papa", "moko-pāpā", "oligosoma zelandicum"), ("skink", "brown", "lizard", "litter", "native"), "leaf_floor",
        ob(5.0, 12.0, "lizard_form", "brown", None, "plain", "glossy", "scaled", "run_stop", "in_litter", "flees"), "S", SEAS["SUM"], "BUG", ease=0.25, count=("one", "one", "two"), life=8, note="native"))
    a(R("rainbow_skink", "rainbow skink", ("rainbow skink", "plague skink", "lampropholis delicata"), ("skink", "introduced", "australian", "lizard", "iridescent"), "the_path",
        ob(4.5, 10.0, "lizard_form", "tan", "dark_brown", "streaked", "iridescent", "scaled", "run_stop", "on_track", "flees"), "S", SEAS["SUM"], "BUG", ease=0.35, count=C3, life=4, note="invasive"))
    a(R("hochstetters_frog", "Hochstetter's frog", ("hochstetter's frog", "hochstetters frog", "pepeketua", "leiopelma hochstetteri"), ("frog", "native", "stream", "protected", "ancient"), "the_spring",
        ob(4.5, 4.5, "frog_form", "olive_brown", "dark_brown", "marbled", "wet_gloss", "warty", "hop", "on_wet_stone", "freezes"), "N", SEAS["RES"], "WET", ease=0.05, count=("one", "one", "two"), life=20, days=0.05, note="native; protected; rare; North Island only"))
    a(R("southern_bell_frog", "southern bell frog", ("southern bell frog", "bell frog", "litoria raniformis"), ("frog", "call", "pond", "introduced", "australian"), "stream",
        ob(6.0, 6.0, "frog_form", "green", "olive_brown", "mottled", "wet_gloss", "smooth", "hop", "on_wet_stone", "jets_away"), "N", SEAS["SUM"], "WET", ease=0.25, count=C3, life=5, note="invasive"))
    a(R("brown_tree_frog", "brown tree frog", ("brown tree frog", "whistling frog", "litoria ewingii"), ("frog", "whistle", "rain", "introduced", "tree"), "undergrowth",
        ob(4.0, 4.0, "frog_form", "brown", None, "plain", "wet_gloss", "smooth", "hop", "in_foliage", "freezes"), "N", SEAS["SPRSUM"], "WET", ease=0.2, count=C3, life=4, note="invasive; calls after rain"))

    # ── birds (new only) ─────────────────────────────────────────────────────────────────────────────────────
    a(R("red_crowned_parakeet", "red-crowned parakeet", ("red-crowned parakeet", "parakeet", "kakariki", "kākāriki", "cyanoramphus"), ("parrot", "green", "red crown", "native", "rare"), "totara_grove",
        ob(27.0, 45.0, "parrot_form", "green", "red", "accented", "matt", "feathered", "clamber", "high_in_the_canopy", "flees"), "D", SEAS["RES"], "BIRD", ease=0.4, count=("one", "a pair", "a small flock"), life=15, days=0.2, note="native; rare"))
    a(R("brown_kiwi", "brown kiwi", ("brown kiwi", "kiwi", "apteryx mantelli"), ("kiwi", "flightless", "night", "probe", "protected"), "leaf_floor",
        ob(40.0, 45.0, "kiwi_form", "brown", None, "plain", "matt", "hairy", "peck_walk", "in_litter", "flees"), "N", SEAS["RES"], "BIRD", ease=0.08, count=("one", "one", "a pair"), life=40, days=0.05, note="native; protected; rare; heard rather than seen"))
    a(R("tomtit", "tomtit", ("tomtit", "miromiro", "petroica macrocephala"), ("robin", "white breast", "native", "forest", "insects"), "undergrowth",
        ob(13.0, 20.0, "songbird_small", "black", "white", "two_tone", "matt", "feathered", "flit", "on_branch", "flees"), "D", SEAS["RES"], "BIRD", ease=0.4, count=("one", "a pair", "several"), life=5, note="native"))
    a(R("whitehead", "whitehead", ("whitehead", "popokatea", "pōpokatea", "mohoua albicilla"), ("flocks", "white head", "native", "canopy", "insects"), "totara_grove",
        ob(12.0, 18.0, "songbird_small", "brown", "white", "two_tone", "matt", "feathered", "flit", "in_foliage", "flees"), "D", SEAS["RES"], "BIRD", ease=0.4, count=("a few", "a busy flock", "a chattering flock"), life=5, note="native; North Island only; flocks"))
    a(R("long_tailed_cuckoo", "long-tailed cuckoo", ("long-tailed cuckoo", "koekoea", "koekoeā", "urodynamis taitensis"), ("cuckoo", "migrant", "long tail", "native", "brood parasite"), "canopy",
        ob(40.0, 55.0, "cuckoo_form", "brown", "cream", "banded", "matt", "feathered", "swoop", "high_in_the_canopy", "flees"), "D", SEAS["SPRSUM"], "BIRD", ease=0.3, count=("one", "one", "two"), life=8, days=0.1, note="native; rare summer visitor"))
    a(R("chaffinch", "chaffinch", ("chaffinch", "pahirini", "fringilla coelebs"), ("finch", "introduced", "pink breast", "song", "wing bars"), "the_path",
        ob(15.0, 25.0, "songbird_small", "pink", "grey", "two_tone", "matt", "feathered", "peck_walk", "on_track", "flees"), "D", SEAS["RES"], "BIRD", ease=0.5, count=("one", "a pair", "several"), life=4, note="invasive"))
    a(R("dunnock", "dunnock", ("dunnock", "hedge sparrow", "prunella modularis"), ("introduced", "hedge", "shy", "streaked", "thin bill"), "undergrowth",
        ob(14.0, 20.0, "songbird_small", "grey", "brown", "streaked", "matt", "feathered", "peck_walk", "in_foliage", "flees"), "D", SEAS["RES"], "BIRD", ease=0.3, count=("one", "a pair", "several"), life=3, note="invasive"))
    a(R("goldfinch", "goldfinch", ("goldfinch", "carduelis carduelis"), ("finch", "introduced", "red face", "thistle", "gold"), "clearing",
        ob(12.0, 20.0, "songbird_small", "yellow", "red", "accented", "matt", "feathered", "flit", "on_flower", "flees"), "D", SEAS["RES"], "BIRD", ease=0.5, count=("a pair", "a small flock", "a flock"), life=4, note="invasive"))
    a(R("greenfinch", "greenfinch", ("greenfinch", "chloris chloris"), ("finch", "introduced", "green", "seeds", "heavy bill"), "clearing",
        ob(15.0, 25.0, "songbird_small", "olive_green", "yellow", "edged", "matt", "feathered", "flit", "in_foliage", "flees"), "D", SEAS["RES"], "BIRD", ease=0.4, count=("one", "a pair", "a small flock"), life=4, note="invasive"))
    a(R("redpoll", "common redpoll", ("redpoll", "common redpoll", "acanthis flammea"), ("finch", "introduced", "red cap", "streaked", "small"), "clearing",
        ob(12.0, 20.0, "songbird_small", "brown", "red", "streaked", "matt", "feathered", "flit", "on_ground", "flees"), "D", SEAS["RES"], "BIRD", ease=0.4, count=("a few", "a small flock", "a flock"), life=3, note="invasive"))
    a(R("yellowhammer", "yellowhammer", ("yellowhammer", "emberiza citrinella"), ("bunting", "introduced", "yellow head", "hedges", "song"), "clearing",
        ob(16.0, 25.0, "songbird_small", "yellow", "brown", "streaked", "matt", "feathered", "flit", "on_branch", "flees"), "D", SEAS["RES"], "BIRD", ease=0.45, count=("one", "a pair", "several"), life=4, note="invasive"))
    a(R("australian_magpie", "Australian magpie", ("australian magpie", "magpie", "makipai", "gymnorhina tibicen"), ("magpie", "swoops", "nest", "introduced", "black and white"), "clearing",
        ob(40.0, 55.0, "crow_form", "black", "white", "mottled", "glossy", "feathered", "peck_walk", "in_the_open", "flees"), "D", SEAS["RES"], "BIRD", ease=0.7, count=("one", "a pair", "a family"), life=20, days=0.3, note="invasive; swoops at nest time (spring)"))
    a(R("indian_myna", "Indian myna", ("indian myna", "myna", "mynah", "acridotheres tristis"), ("myna", "introduced", "noisy", "yellow bill", "aggressive"), "the_path",
        ob(24.0, 40.0, "crow_form", "dark_brown", "yellow", "accented", "matt", "feathered", "peck_walk", "on_track", "flees"), "D", SEAS["RES"], "BIRD", ease=0.6, count=("one", "a pair", "several"), life=8, days=0.2, note="invasive; northern North Island only"))
    a(R("california_quail", "California quail", ("california quail", "quail", "callipepla californica"), ("quail", "plume", "covey", "introduced", "game"), "undergrowth",
        ob(24.0, 30.0, "game_plump", "grey", "tan", "marbled", "matt", "feathered", "peck_walk", "on_ground", "flees"), "D", SEAS["RES"], "BIRD", ease=0.4, count=("a pair", "a covey", "a large covey"), life=4, note="invasive"))
    a(R("pukeko", "pūkeko", ("pukeko", "pūkeko", "porphyrio melanotus", "swamphen"), ("swamp", "red shield", "native", "grass", "flicks tail"), "clearing",
        ob(50.0, 60.0, "swamp_heavy", "blue", "black", "two_tone", "glossy", "feathered", "peck_walk", "in_the_open", "flees"), "D", SEAS["RES"], "BIRD", ease=0.7, count=("one", "a pair", "a small group"), life=15, days=0.2, note="native; an edge visitor"))
    a(R("harrier", "harrier", ("harrier", "kahu", "kāhu", "swamp harrier", "circus approximans"), ("hawk", "soars", "carrion", "native", "raptor"), "sea_gap",
        ob(55.0, 130.0, "raptor_wide", "brown", "cream", "two_tone", "matt", "feathered", "soar", "in_air", "ignores"), "D", SEAS["RES"], "BIRD", ease=0.7, count=("one", "one", "a pair"), life=15, days=0.3, note="native; overhead"))
    a(R("nz_falcon", "New Zealand falcon", ("new zealand falcon", "nz falcon", "karearea", "kārearea", "falco novaeseelandiae"), ("falcon", "fast", "raptor", "protected", "dive"), "canopy",
        ob(40.0, 80.0, "raptor_pointed", "brown", "cream", "streaked", "matt", "feathered", "swoop", "high_in_the_canopy", "flees"), "D", SEAS["RES"], "BIRD", ease=0.4, count=("one", "one", "a pair"), life=12, days=0.05, note="native; protected; rare"))
    a(R("eastern_rosella", "eastern rosella", ("eastern rosella", "rosella", "platycercus eximius"), ("parrot", "introduced", "red head", "colourful", "australian"), "canopy",
        ob(30.0, 45.0, "parrot_form", "red", "yellow", "mottled", "glossy", "feathered", "clamber", "high_in_the_canopy", "flees"), "D", SEAS["RES"], "BIRD", ease=0.5, count=("one", "a pair", "a small flock"), life=10, days=0.2, note="invasive; northern North Island only"))
    a(R("spotted_dove", "spotted dove", ("spotted dove", "spilopelia chinensis", "dove"), ("dove", "introduced", "collar", "coo", "pigeon"), "the_path",
        ob(30.0, 45.0, "pigeon_small", "tan", "black", "spotted", "matt", "feathered", "peck_walk", "on_track", "flees"), "D", SEAS["RES"], "BIRD", ease=0.55, count=("one", "a pair", "several"), life=8, days=0.2, note="invasive; northern North Island only"))
    a(R("ring_necked_pheasant", "ring-necked pheasant", ("ring-necked pheasant", "pheasant", "phasianus colchicus"), ("pheasant", "game", "long tail", "introduced", "crow"), "clearing",
        ob(60.0, 85.0, "ground_longtail", "orange_brown", "green", "marbled", "glossy", "feathered", "peck_walk", "in_the_open", "flees"), "D", SEAS["RES"], "BIRD", ease=0.55, count=("one", "a pair", "a hen and her brood"), life=5, days=0.15, note="invasive"))
    a(R("barn_owl", "barn owl", ("barn owl", "tyto alba"), ("owl", "night", "heart-shaped face", "silent", "introduced"), "canopy",
        ob(36.0, 90.0, "owl_form", "cream", "buff", "mottled", "matt", "feathered", "swoop", "high_in_the_canopy", "flees"), "N", SEAS["RES"], "BIRD", ease=0.2, count=("one", "one", "a pair"), life=8, days=0.1, note="invasive; northern North Island only"))

    # ── mammals (new only) ───────────────────────────────────────────────────────────────────────────────────
    a(R("bush_stoat", "stoat", ("stoat", "hakuturi", "hākuturi", "mustela erminea"), ("stoat", "predator", "birds", "mustelid", "trap"), "undergrowth",
        ob(30.0, 45.0, "long_low_furred", "tan", "cream", "two_tone", "matt", "furred", "bound", "on_ground", "flees"), "C", SEAS["RES"], "FUR", ease=0.3, count=("one", "one", "two"), life=3, days=0.3, note="invasive; a killer of nesting birds"))
    a(R("ferret", "ferret", ("ferret", "mustela furo"), ("ferret", "predator", "mask", "mustelid", "feral"), "undergrowth",
        ob(45.0, 60.0, "long_low_furred", "cream", "dark_brown", "accented", "matt", "furred", "bound", "on_ground", "flees"), "C", SEAS["RES"], "FUR", ease=0.3, count=("one", "one", "two"), life=5, days=0.2, note="invasive"))
    a(R("weasel", "weasel", ("weasel", "mustela nivalis"), ("weasel", "small", "predator", "mustelid", "mice"), "leaf_floor",
        ob(22.0, 30.0, "long_low_furred", "brown", "cream", "two_tone", "matt", "furred", "bound", "on_ground", "flees"), "C", SEAS["RES"], "FUR", ease=0.25, count=("one", "one", "two"), life=2, days=0.3, note="invasive"))
    a(R("ship_rat", "ship rat", ("ship rat", "black rat", "rattus rattus", "rat"), ("rat", "climbs", "nests", "eggs", "canopy"), "oak_trunk",
        ob(20.0, 40.0, "small_furred", "dark_grey", "cream", "two_tone", "matt", "furred", "run_stop", "on_trunk", "flees"), "N", SEAS["RES"], "FUR", ease=0.25, count=C3, life=2, note="invasive; climbs; takes eggs and chicks"))
    a(R("feral_cat", "feral cat", ("feral cat", "wild cat", "felis catus"), ("cat", "predator", "feral", "hunts", "night"), "undergrowth",
        ob(45.0, 80.0, "cat_form", "grey", "black", "streaked", "matt", "furred", "bound", "on_ground", "flees"), "N", SEAS["RES"], "FUR", ease=0.25, count=("one", "one", "two"), life=6, days=0.2, note="invasive; NOT Du's household cat (a different animal)"))
    a(R("feral_pig", "feral pig", ("feral pig", "pig", "poaka", "sus scrofa"), ("pig", "tusks", "digs", "feral", "boar"), "leaf_floor",
        ob(120.0, 150.0, "pig_form", "dark_grey", "brown", "mottled", "matt", "bristled", "root", "on_ground", "flees"), "C", SEAS["RES"], "FUR", ease=0.6, count=("one", "a sow and piglets", "a sounder"), life=10, days=0.12, note="invasive; digs up the leaf-mould"))
    a(R("feral_goat", "feral goat", ("feral goat", "goat", "capra hircus"), ("goat", "browse", "horns", "feral", "cliffs"), "clearing",
        ob(90.0, 110.0, "goat_form", "tan", "dark_brown", "two_tone", "matt", "furred", "browse", "in_the_open", "flees"), "D", SEAS["RES"], "FUR", ease=0.6, count=("one", "a nanny and kid", "a small herd"), life=10, days=0.12, note="invasive"))
    a(R("brown_hare", "brown hare", ("brown hare", "hare", "lepus europaeus"), ("hare", "long ears", "fast", "form", "introduced"), "clearing",
        ob(55.0, 65.0, "hare_form", "tawny", "cream", "two_tone", "matt", "furred", "hop", "in_the_open", "flees"), "C", SEAS["RES"], "FUR", ease=0.5, count=("one", "one", "two"), life=5, days=0.25, note="invasive"))
    a(R("short_tailed_bat", "short-tailed bat", ("short-tailed bat", "pekapeka-tou-poto", "pekapeka", "mystacina tuberculata"), ("bat", "wings", "roost", "protected", "native"), "canopy",
        ob(7.0, 25.0, "bat_form", "dark_brown", None, "plain", "matt", "furred", "flit", "in_air", "flees"), "N", SEAS["NOVFEB"], "FUR", ease=0.12, count=("one", "one", "a few"), life=10, days=0.1, note="native; protected; rare; flies and crawls on the ground"))
    return X
