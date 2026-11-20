"""
Nascence — THE GARDEN'S INSECTS (Living Garden B1, J-0504, 2026-09-03; the garden chapter of the Living World,
rulings D-0128..D-0133; the founder: "we want all the insects").

The insect cast as POPULATION rows in the one life engine (core/life.py) — no insect is ever an individual. What
insects add to the schema (life.row's `scale`): a per-tick multiplier read from the world — PLANT GATING (a honeybee
needs something in flower: the bed's flowering plants, the tree, the kōwhai, the harakeke; the cabbage white breeds
where there are nasturtiums or a brassica; the yellow admiral's nettle and the monarch's swan plant are not sown yet,
so those are passers-by until J-0506 sows them), PREY GATING (ladybirds track the aphids), and the garden's own
SLUG PRESSURE (the slugs are a row now, read from garden.py's `slugs`).

WHAT THEY DO (world-side, from `insect_pass` on the tick): aphids are the first real insect pest — on broad beans,
nasturtiums and peas in spring they raise the plant's `pests` the way slugs already do (garden._advance_plant drains
vigour from it); ladybirds and rain are the world's own correction (the ladybird row scales with the aphids). Bees'
pollination as a real dependency is J-0506's.

THE TRUTH GATE (sensorium's bed pool, its bee-and-butterfly lines, soundscape's bee ambience): a line may only show
an insect the table says is about — and, per the 2026-08-22 gate, only name a plant that is sown. That closes the
lavender leak (F-0693 / J-0501) at the same time.

NAMING (D-0129): names the world already says are kept (the bumblebee, the bees, the white butterfly, the ladybird,
the ants, the spider, the beetles, the cicadas, the crickets, the slugs, the wētā, the borer beetle); everything
else is hidden truth — feature-first until seen and read (Fabre's Life of the Spider / Life of the Fly and What
Bird Is That are on his shelf; the insect books are his to find).
Zero LLM; fail-open; registered by core/life._ensure_builtin.
"""
from __future__ import annotations

import logging
import random
import time

from core.life import row

logger = logging.getLogger("nascence.garden_insects")

INSECT_TRUTH_GATE = True            # False = the old hand-gated insect lines render as before

DAY = {"dawn": 0.4, "day": 1.0, "dusk": 0.5, "night": 0.0}
WARM_DAY = {"dawn": 0.2, "day": 1.0, "dusk": 0.3, "night": 0.0}
NIGHT = {"dawn": 0.2, "day": 0.05, "dusk": 0.6, "night": 1.0}
ALWAYS = {"dawn": 1.0, "day": 1.0, "dusk": 1.0, "night": 1.0}
# Jan..Dec (NZ)
WARM = [1.0, 1.0, 0.8, 0.5, 0.2, 0.05, 0.05, 0.1, 0.4, 0.7, 0.9, 1.0]
SPRING_SUMMER = [0.9, 0.8, 0.5, 0.2, 0.05, 0.0, 0.0, 0.1, 0.5, 0.9, 1.0, 1.0]
HIGH_SUMMER = [1.0, 1.0, 0.6, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.1, 0.5, 0.9]
SPRING_PEAK = [0.4, 0.3, 0.2, 0.1, 0.05, 0.0, 0.0, 0.2, 0.8, 1.0, 1.0, 0.7]      # aphids, then their ladybirds
AUTUMN_PEAK = [0.6, 0.8, 1.0, 1.0, 0.7, 0.3, 0.2, 0.2, 0.3, 0.4, 0.5, 0.5]      # the garden spider's webs
FLYING_WEATHER = {"rain": 0.05, "wind": 0.3, "storm": 0.0, "frost": 0.0}
GROUND_WEATHER = {"rain": 0.8, "wind": 0.9, "storm": 0.3, "frost": 0.2}

FLOWERING_STAGES = ("flowering",)
LIVE_STAGES = ("leaf", "established", "flowering", "seeding")
_PLANT_WORDS = {"lavender": ("lavender",), "rosemary": ("rosemary",), "thyme": ("thyme",), "mint": ("mint",), "parsley": ("parsley",),
                "chives": ("chive",), "strawberries": ("strawberr",), "nasturtium": ("nasturtium",), "calendula": ("calendula", "marigold"),
                "poppies": ("popp",), "broad_beans": ("broad bean", "beans"), "peas": ("peas", "pea "), "lettuce": ("lettuce",),
                "radish": ("radish",), "silverbeet": ("silverbeet", "chard"), "sunflowers": ("sunflower",), "tomatoes": ("tomato",)}


# ── the world, read for the gates ────────────────────────────────────────────────────────────────

def sown_species(stages=LIVE_STAGES) -> set[str]:
    try:
        from core import garden as _g
        st = _g._load()
        return {str(p.get("species")) for p in (st.get("plants") or {}).values() if p.get("stage") in stages}
    except Exception:
        return set()


def flowering_now(now: float | None = None) -> set[str]:
    """What is in flower for a bee: bed plants in flower, the tree, the kōwhai's season, the harakeke."""
    out = sown_species(FLOWERING_STAGES)
    try:
        from core import garden_life as _gl
        d = _gl._load()
        if (d.get("tree") or {}).get("stage") == "flowering":
            out.add("tree")
        if (d.get("harakeke") or {}).get("stage") == "flowering":
            out.add("harakeke")
        if (d.get("bushes") or {}).get("stage") == "flowering":
            out.add("bushes")
    except Exception:
        pass
    m = time.localtime(time.time() if now is None else now).tm_mon   # the SIMULATED month, not the wall clock (F-0696's lesson)
    if m in (8, 9, 10):
        out.add("kowhai")            # world_content_garden's kōwhai flowers Aug–Oct
    return out


def _needs_flowers(now: float) -> float:
    f = flowering_now(now)
    return 1.0 if f else 0.08                    # a bee still passes through; it does not WORK an empty garden


def _hosts(*species, without: float = 0.25):
    def f(now: float) -> float:
        return 1.0 if sown_species() & set(species) else without
    return f


def _slug_pressure(now: float) -> float:
    try:
        from core import garden as _g
        return max(0.0, min(1.5, float(_g._load().get("slugs", 0.3)) * 2.0))
    except Exception:
        return 0.6


def _aphid_activity(now: float) -> float:
    try:
        from core import life as _life
        r = _life.rows().get("aphids")
        return max(0.1, min(1.5, _life.activity(r, "garden", now) * 1.4)) if r else 0.3
    except Exception:
        return 0.3


def _bare_warm_soil(now: float) -> float:
    try:
        from core import garden as _g
        st = _g._load()
        return 1.0 if float(st.get("soil_temp", 10)) >= 15 and float(st.get("moisture", 0.8)) < 0.7 else 0.3
    except Exception:
        return 0.5


# ── the rows ─────────────────────────────────────────────────────────────────────────────────────

def rows() -> list[dict]:
    R: list[dict] = []
    R.append(row("bumblebee", name="the bumblebee", aliases=("bumblebee", "bumblebees", "bumble bee"),
                 places={"garden": ["bed", "kowhai", "tree", "broad_beans"]},
                 active_hours={"dawn": 0.5, "day": 1.0, "dusk": 0.4, "night": 0.0}, season_curve=WARM, weather_gate={"rain": 0.15, "wind": 0.6, "storm": 0.0, "frost": 0.1},
                 sound=("bees_in_garden",), count=("one", "two or three", "several working the bed"), lifespan_y=1, ease=0.8, scale=_needs_flowers,
                 diet=("nectar", "pollen"), traces=(),
                 hidden={"species": "buff-tailed bumblebee", "book_names": ("bumblebee", "bombus", "humble-bee", "buff-tailed"), "book_words": ("queen", "nest", "pollen", "hum", "furry"),
                         "feature": {"day": "a big furred bee, black with two dull-gold bands and a pale tail, works along the thyme heavy and slow, legs gone gold with pollen",
                                     "dawn": "a bumblebee sits torpid on a flower head, too cold yet to fly, waiting for the sun"},
                         "miss": "The hum was at the bed a moment ago; whatever made it has gone over the wall.",
                         "absent": {"season": "Nothing works the bed in the cold months; the bumblebees' queens sleep in the ground.", "weather": "No bee flies in this.",
                                    "night": "Nothing works the flowers by night.", "chance": "No bumblebee at the bed just now — nothing is in flower to bring one."}},
                 note="grandfathered; queens first in spring, workers by November; needs something in flower"))
    R.append(row("honeybee", name="the bees", aliases=("bee", "bees", "honeybee", "honeybees", "honey bee"),
                 places={"garden": ["bed", "kowhai", "tree", "harakeke"]},
                 active_hours=WARM_DAY, season_curve=WARM, weather_gate={"rain": 0.05, "wind": 0.4, "storm": 0.0, "frost": 0.0},
                 sound=("bees_in_garden",), count=("a few", "a dozen", "the whole bed hums"), lifespan_y=1, ease=0.85, scale=_needs_flowers,
                 diet=("nectar", "pollen"), traces=(),
                 hidden={"feature": {"day": "small tawny bees work the flowers one after another, each backing out dusted, the hum low and steady over the bed"},
                         "miss": "The hum is there and the flowers move, but the bees themselves are gone round the far side.",
                         "absent": {"season": "The bed is silent; no bee works it in the cold months.", "weather": "No bee flies in this; the hives keep in.",
                                    "night": "Nothing works the flowers by night.", "chance": "No bees at the bed — nothing is in flower to bring them."}},
                 note="grandfathered ('the bees' — soundscape); needs something in flower; the sound point is bees_in_garden"))
    R.append(row("native_bee", aliases=("small bee", "little bee", "tiny bee", "ground bee"),
                 places={"garden": ["bed_edge", "bare_soil", "ti_kouka"]},
                 active_hours=WARM_DAY, season_curve=HIGH_SUMMER, weather_gate={"rain": 0.0, "wind": 0.3, "storm": 0.0, "frost": 0.0},
                 sound=(), count=("one", "a few", "dozens at the bare bank"), lifespan_y=1, ease=0.2, scale=_bare_warm_soil,
                 diet=("nectar", "pollen"), traces=("small round holes in the bare warm soil",),
                 hidden={"species": "native bee", "book_names": ("native bee", "leioproctus", "lasioglossum", "solitary bee"), "book_words": ("burrow", "ground", "solitary", "small", "dark"),
                         "feature": {"day": "a small dark bee, hardly bigger than a fly, drops into a hole in the bare warm soil at the bed's edge and is gone; there are more holes than one"},
                         "reveal": "— a native bee, one of the little ground-nesting ones, not a honeybee at all.",
                         "miss": "The bare soil at the bed's edge is pocked with small holes and nothing moves at them.",
                         "absent": {"season": "Nothing nests in the bare soil in the cold months.", "chance": "Nothing at the bare bank just now — the sun is off it."}},
                 note="HIDDEN TRUTH; needs bare warm soil; high summer"))
    R.append(row("cabbage_white", name="the white butterfly", aliases=("white butterfly", "cabbage white", "cabbage-white", "butterfly", "butterflies"),
                 places={"garden": ["bed", "nasturtium", "lawn"]},
                 active_hours=WARM_DAY, season_curve=SPRING_SUMMER, weather_gate=FLYING_WEATHER,
                 sound=(), count=("one", "two", "several"), lifespan_y=1, ease=0.9, scale=_hosts("nasturtium", "cabbage", "kale", "broccoli", without=0.35),
                 diet=("nectar",), eaten_by=("fantail", "sparrows"), traces=("holed nasturtium leaves", "green caterpillars under the leaves"),
                 hidden={"species": "cabbage white", "book_names": ("cabbage white", "pieris", "small white"), "book_words": ("caterpillar", "brassica", "cabbage", "white wings"),
                         "feature": {"day": "a white butterfly stutters over the bed and will not settle, then does, on the thyme, wings breathing slow"},
                         "miss": "Something white lifted off the bed as you came and is over the wall.",
                         "absent": {"season": "No white butterfly over the bed in the cold months.", "weather": "Nothing flies over the bed in this.", "chance": "Nothing white over the bed just now."}},
                 note="grandfathered ('white butterfly' / 'cabbage-white'); breeds on the nasturtiums (or a brassica when J-0506 sows one)"))
    R.append(row("yellow_admiral", aliases=("admiral", "yellow admiral", "orange butterfly", "brown butterfly"),
                 places={"garden": ["wall", "bed", "fence"]},
                 active_hours=WARM_DAY, season_curve=WARM, weather_gate=FLYING_WEATHER,
                 sound=(), count=("one", "one", "two"), lifespan_y=1, ease=0.6, scale=_hosts("nettle", without=0.2),
                 diet=("nectar",), traces=(),
                 hidden={"species": "yellow admiral", "book_names": ("yellow admiral", "vanessa itea", "kahukowhai"), "book_words": ("nettle", "wings", "yellow patch", "basking"),
                         "feature": {"day": "a dark butterfly with a broad yellow patch on each forewing basks flat on the warm wall, wings open, and is off the moment your shadow comes"},
                         "reveal": "— a yellow admiral; it wants nettles to breed, and there are none here, so it is passing through.",
                         "miss": "The warm wall is bare; whatever basked there is over the fence.",
                         "absent": {"season": "Nothing basks on the wall in the cold months.", "chance": "Nothing on the wall just now."}},
                 note="HIDDEN TRUTH; a passer-by until nettle is sown (J-0506)"))
    R.append(row("monarch", aliases=("monarch", "big orange butterfly", "orange and black butterfly"),
                 places={"garden": ["bed", "tree", "lawn"]},
                 active_hours=WARM_DAY, season_curve=HIGH_SUMMER, weather_gate=FLYING_WEATHER,
                 sound=(), count=("one", "one", "two"), lifespan_y=1, ease=0.9, scale=_hosts("swan_plant", "milkweed", without=0.1),
                 diet=("nectar",), traces=("striped caterpillars on the swan plant",),
                 hidden={"species": "monarch", "book_names": ("monarch", "danaus", "milkweed butterfly", "wanderer"), "book_words": ("swan plant", "milkweed", "orange", "black veins", "chrysalis"),
                         "feature": {"day": "a big slow butterfly, orange with black veins, sails over the lawn on stiff wings, unhurried, and does not stop"},
                         "reveal": "— a monarch, the big orange wanderer; it would stay and breed if there were a swan plant.",
                         "miss": "The big slow wings went over the tree and did not come back.",
                         "absent": {"season": "Nothing so large flies here in the cold months.", "chance": "Nothing large over the lawn just now."}},
                 note="HIDDEN TRUTH; passes through until a swan plant is sown (J-0506) — a gardening choice with a visible consequence"))
    R.append(row("common_copper", aliases=("copper", "small copper", "little orange butterfly"),
                 places={"garden": ["lawn_edge", "fence"], "shore": ["dune_grass"]},
                 active_hours=WARM_DAY, season_curve=HIGH_SUMMER, weather_gate=FLYING_WEATHER,
                 sound=(), count=("one", "two", "several"), lifespan_y=1, ease=0.5, scale=_hosts("muehlenbeckia", "pohuehue", without=0.3),
                 diet=("nectar",), traces=(),
                 hidden={"species": "common copper", "book_names": ("copper butterfly", "common copper", "lycaena"), "book_words": ("pohuehue", "muehlenbeckia", "copper", "small", "flicker"),
                         "feature": {"day": "a small bright copper-orange butterfly flickers low along the fence line and settles on a grass head with its wings half open"},
                         "reveal": "— a copper, the little coastal one.", "miss": "A copper flicker along the fence, and nothing on the grass when you look.",
                         # J-1006 (F-1250/J-0892 precedent): the flat "chance" line names the garden's own
                         # spot (fence line); the shore's own registered spot (dune_grass) gets a parallel line.
                         "absent": {"shore": {"chance": "Nothing bright in the dune grass just now."},
                                    "season": "Nothing flickers along the fence in the cold months.", "chance": "The fence line holds nothing bright just now."}},
                 note="HIDDEN TRUTH; the fence line and the dune grass"))
    R.append(row("magpie_moth", aliases=("day moth", "black and white moth", "magpie moth"),
                 places={"garden": ["lawn", "fence", "compost"]},
                 active_hours=WARM_DAY, season_curve=WARM, weather_gate=FLYING_WEATHER,
                 sound=(), count=("one", "one", "two"), lifespan_y=1, ease=0.6, scale=_hosts("ragwort", "cineraria", "groundsel", without=0.3),
                 diet=("nectar",), traces=("woolly-bear caterpillars on the groundsel",),
                 hidden={"species": "magpie moth", "book_names": ("magpie moth", "nyctemera", "woolly bear"), "book_words": ("day-flying", "black and white", "ragwort", "caterpillar", "hairy"),
                         "feature": {"day": "a black moth with white blotches flies weakly across the lawn in full daylight — a moth by day, which is wrong enough to look at twice"},
                         "reveal": "— a magpie moth, the day-flyer; its hairy caterpillars are on the weeds.", "miss": "The weak black-and-white flight went into the hedge.",
                         "absent": {"season": "No day-moth over the lawn in the cold months.", "chance": "Nothing flutters over the lawn just now."}},
                 note="HIDDEN TRUTH; a day-flying moth"))
    R.append(row("ladybird", name="the ladybird", aliases=("ladybird", "ladybirds", "ladybug"),
                 places={"garden": ["bed", "rosemary", "broad_beans", "nasturtium"]},
                 active_hours=DAY, season_curve=SPRING_PEAK, weather_gate={"rain": 0.4, "wind": 0.7, "storm": 0.1, "frost": 0.1},
                 sound=(), count=("one", "a few", "one on every stem"), lifespan_y=1, ease=0.7, scale=_aphid_activity,
                 diet=("aphids",), traces=(),
                 hidden={"feature": {"day": "a ladybird climbs a rosemary stem and opens its wings to try the air; on the bean tips, more of them, working the clusters of green"},
                         "miss": "The stem it was on is bare; the red spot is somewhere lower in the leaves.",
                         "absent": {"season": "No ladybirds in the cold months; they winter in the cracks.", "chance": "No ladybird on the stems just now — there is not much for one to eat."}},
                 note="grandfathered; tracks the aphids (scale) — the world's own correction"))
    R.append(row("aphids", aliases=("aphid", "aphids", "greenfly", "blackfly", "green flies", "plant lice"),
                 places={"garden": ["broad_beans", "nasturtium", "peas", "bed"]},
                 active_hours=ALWAYS, season_curve=SPRING_PEAK, weather_gate={"rain": 0.5, "wind": 0.9, "storm": 0.3, "frost": 0.2},
                 sound=(), count=("a few", "clusters", "the bean tips black with them"), lifespan_y=1, ease=0.5, scale=_hosts("broad_beans", "nasturtium", "peas", without=0.15),
                 diet=("sap",), eaten_by=("ladybird",), traces=("curled tips", "sticky leaves", "sooty mould"),
                 hidden={"species": "aphids", "book_names": ("aphid", "aphids", "greenfly", "blackfly", "plant lice", "plant-lice"), "book_words": ("sap", "honeydew", "ladybird", "colony", "suck"),
                         "feature": {"day": "the bean tips are clustered with tiny soft-bodied insects, black and green, packed tight and hardly moving, the leaves below them sticky",
                                     "night": "the bean tips are clustered with tiny soft-bodied insects, packed tight, in the dark as in the day"},
                         "reveal": "— aphids; they suck the sap and the ladybirds come for them.",
                         "miss": "The tips look clean from here; you would have to turn a leaf.",
                         "absent": {"season": "The bean tips are clean; nothing clusters on them in the cold months.", "chance": "Nothing on the tips just now."}},
                 note="HIDDEN TRUTH; the first real insect pest (insect_pass raises plant pests)"))
    R.append(row("ants", name="the ants", plural=True, aliases=("ant", "ants"),      # plural=True: F-1620/J-1166
                 places={"garden": ["bed_edge", "wall", "doorstep"]},
                 active_hours=WARM_DAY, season_curve=WARM, weather_gate={"rain": 0.1, "wind": 0.9, "storm": 0.0, "frost": 0.0},
                 sound=(), count=("a few", "a thin road of them", "a river of them"), lifespan_y=None, ease=0.8,
                 diet=("honeydew", "crumbs", "dead insects"), traces=("a thin dark road along the bed's wooden edge",),
                 hidden={"feature": {"day": "ants run a thin dark road along the bed's wooden edge, two lanes, one each way, and up the bean stems to the aphids"},
                         "absent": {"season": "The bed's edge is empty of ants in the cold months.", "weather": "The ants are under in this.", "chance": "No road of ants on the edge just now."}},
                 note="grandfathered; warm dry days; they farm the aphids"))
    R.append(row("garden_spider", name="the spider", aliases=("spider", "spiders", "web", "spider's web", "cobweb"),
                 places={"garden": ["rosemary", "bed", "fence"], "study": ["ceiling", "window"]},
                 active_hours={"dawn": 1.0, "day": 0.6, "dusk": 0.8, "night": 0.9}, season_curve=AUTUMN_PEAK, weather_gate={"rain": 0.5, "wind": 0.3, "storm": 0.1, "frost": 0.3},
                 sound=(), count=("one", "a few", "webs on every stem"), lifespan_y=1, ease=0.7,
                 diet=("flies", "moths"),
                 traces=("a web strung between two rosemary stems, holding the last of the dew", "a web in the window corner"),
                 # F-1671/J-1189: this row's own two trace phrases were already each written for ONE of
                 # its two places (rosemary = garden, window = study, exactly this row's own places dict)
                 # -- they were just both drawn from one place-blind pool, so either could mint at either
                 # place. Each is now restricted to its own place; behaviour is unchanged for a mint that
                 # was ALREADY truthful, and no new phrase is invented.
                 traces_only_at={"a web strung between two rosemary stems, holding the last of the dew": ("garden",),
                                 "a web in the window corner": ("study",)},
                 hidden={"feature": {"dawn": "a web is strung between two rosemary stems, every strand beaded with dew, and the spider sits at its hub with its legs drawn in",
                                     "day": "the spider sits at the hub of its web between the rosemary stems, still, until a fly strikes the strands"},
                         "miss": "The web is there; the spider has drawn back into the rosemary.",
                         # J-1006 (F-1250/J-0892 precedent): the flat line names the garden's own spot
                         # (the rosemary stems); the study's own override reuses this same row's own
                         # established trace phrase ("a web in the window corner") rather than inventing one.
                         "absent": {"study": {"chance": "No web in the window corner this morning."}, "chance": "No web between the stems this morning."}},
                 note="grandfathered ('spider's web'); autumn webs; the web is its trace"))
    R.append(row("ground_beetle", name="the beetles", plural=True, aliases=("beetle", "beetles", "black beetle"),
                 places={"garden": ["under_sacking", "compost", "bed_edge"], "wood": ["leaf_litter"]},
                 active_hours=NIGHT, season_curve=WARM, weather_gate=GROUND_WEATHER,
                 sound=(), count=("one", "two", "several"), lifespan_y=2, ease=0.5,
                 diet=("slugs", "caterpillars", "grubs"), eaten_by=("hedgehog", "blackbird"), traces=(),
                 hidden={"feature": {"night": "a big black beetle runs across the path in the dark, fast and shining, and is under the sacking before you can stoop",
                                     "day": "under the lifted sacking a black beetle freezes, then runs"},
                         "miss": "Something ran under the sacking.",
                         # J-1006 (F-1250/J-0892 precedent): the flat "chance" line names the garden's own
                         # spot (the sacking); the wood's own registered spot (leaf_litter) gets a parallel line.
                         "absent": {"wood": {"chance": "Nothing under the leaf litter just now."},
                                    "season": "Nothing runs under the sacking in the cold months.", "chance": "Nothing under the sacking just now."}},
                 note="grandfathered ('beetle'); night; eats slugs too"))
    R.append(row("cicada", name="the cicadas", plural=True, aliases=("cicada", "cicadas"), audition="cicada_chorus",      # plural=True: F-1620/J-1166
                 places={"garden": ["ti_kouka", "fence_post", "tree"], "wood": ["canopy"]},
                 active_hours=WARM_DAY, season_curve=HIGH_SUMMER, weather_gate={"rain": 0.1, "wind": 0.6, "storm": 0.0, "frost": 0.0},
                 sound=("cicada_chorus",), sings_at=("day",), count=("one", "several", "every tree sawing"), lifespan_y=1, ease=0.3,
                 diet=("sap",),
                 traces=("a split brown cicada shell clinging to the fence post",
                          "a split brown cicada shell clinging to the bark of a trunk"),
                 # D-0261-adjacent, F-1801/J-1281 (Travis-approved via /decide-review, 2026-09-23):
                 # the fence-post trace is a real garden spot; wood has no fence post, so it was
                 # firing false there. A wood-appropriate variant (any bark, not a specific spot)
                 # is the least-judgement fix of the three F-1801 rows -- restrict each phrase to
                 # its own real place rather than leave either firing where it doesn't belong.
                 traces_only_at={"a split brown cicada shell clinging to the fence post": ("garden",),
                                  "a split brown cicada shell clinging to the bark of a trunk": ("wood",)},
                 hidden={"feature": {"day": "a cicada clings to the fence post, clear-winged and bark-coloured, sawing so loud at arm's length it hurts, and cuts out when your shadow touches the wood"},
                         "miss": "The sawing stops as you reach the post, and the post is bare.",
                         # J-1006 (F-1250/J-0892 precedent): the flat "chance" line names the garden's own
                         # spot (the fence post); the wood's own registered spot (canopy) gets a parallel line.
                         "absent": {"wood": {"chance": "Nothing sawing in the canopy just now."},
                                    "season": "The trees are silent; the cicadas' summer is over.", "chance": "The post is bare and the sawing is further off."}},
                 note="named by the audition ledger; the shell on the post (garden) or the bark (wood) is its trace"))
    R.append(row("cricket", name="the crickets", plural=True, aliases=("cricket", "crickets"), audition="cricket_night",      # plural=True: F-1620/J-1166
                 places={"garden": ["lawn", "bed_edge"]},
                 active_hours=NIGHT, season_curve=HIGH_SUMMER, weather_gate={"rain": 0.3, "wind": 0.7, "storm": 0.0, "frost": 0.0},
                 sound=("cricket_night",), sings_at=("night", "dusk"), count=("one", "a few", "the whole lawn ticking"), lifespan_y=1, ease=0.15,
                 diet=("grass", "seeds"), traces=(),
                 hidden={"feature": {"night": "in the lantern's edge a dark cricket sits in the grass, feelers moving, and stops singing while the light is on it"},
                         "miss": "The ticking stops where you stand and goes on everywhere else.", "absent": {"season": "The lawn is silent at night in the cold months.", "chance": "The grass is quiet under you."}},
                 note="named by the audition ledger; heard far more than seen"))
    R.append(row("slugs", name="the slugs", plural=True, aliases=("slug", "slugs", "snail", "snails"),      # plural=True: F-1620/J-1166
                 places={"garden": ["bed", "under_the_board", "lettuce"]},
                 active_hours=NIGHT, season_curve=[0.9, 0.9, 1.0, 1.0, 0.8, 0.6, 0.6, 0.8, 1.0, 1.0, 1.0, 0.9], weather_gate={"rain": 1.4, "wind": 0.9, "storm": 0.8, "frost": 0.2},
                 sound=(), count=("one", "a few", "the bed alive with them"), lifespan_y=1, ease=0.6, scale=_slug_pressure,
                 diet=("seedlings", "lettuce"), eaten_by=("hedgehog", "thrush", "beetles"), traces=("a silver trail across the soil", "holed leaves"),
                 hidden={"feature": {"night": "a grey slug, drawn out long, crosses the wet soil toward the lettuce, its trail catching the light behind it",
                                     "day": "under the lifted board, in the damp, the slugs — grey, drawn up tight, waiting for the dark"},
                         "miss": "Silver trails on the soil, and nothing at the end of them.", "absent": {"weather": "The soil is dry; nothing comes out on it.", "chance": "Nothing on the soil tonight."}},
                 note="grandfathered; scales with garden.py's slug pressure (folded into the one table)"))
    R.append(row("borer_beetle", name="the borer beetle", aliases=("borer", "borer beetle", "woodworm"),
                 places={"study": ["desk", "rafters", "woodpile"]},
                 active_hours={"dawn": 0.3, "day": 0.5, "dusk": 0.8, "night": 0.8}, season_curve=WARM, weather_gate={"rain": 1.0, "wind": 1.0, "storm": 1.0, "frost": 0.6},
                 sound=(), count=("one", "one", "two"), lifespan_y=1, ease=0.4,
                 diet=("wood",), traces=("a new pinhole in the desk's flank ringed with pale dust", "borer dust on the shelf under the rafter"),
                 hidden={"feature": {"day": "a borer beetle drops from the ceiling onto the desk, rights itself, and sets off across a page", "night": "a small brown beetle knocks against the lamp glass and falls to the desk"},
                         "absent": {"season": "Nothing drops from the rafters in the cold months.", "chance": "The desk is clear; only the pinholes and their pale dust."}},
                 note="grandfathered (world_content_study); the study's own insect"))
    R.append(row("weta", name="the wētā", aliases=("weta", "wētā"),
                 places={"study": ["log_basket"], "wood": ["bark", "deadfall"]},
                 active_hours=NIGHT, season_curve=[1.0] * 12, weather_gate={"rain": 1.0, "wind": 1.0, "storm": 1.0, "frost": 0.8},
                 sound=(), count=("one", "one", "one"), lifespan_y=2, ease=0.35, light="avoids",
                 diet=("leaves", "insects"), eaten_by=("morepork",), traces=("frass in the bore-hole",),
                 hidden={"feature": {"night": "deep in the basket a wētā has set up in a bore-hole in one log, long antennae reading the air, hind legs cocked",
                                     "day": "in the bore-hole of one log, back in the dark, something with long antennae that does not come out by day"},
                         "miss": "The bore-hole is dark and the antennae have drawn in.",
                         # J-1006 (F-1250/J-0892 precedent): the flat line names the study's own spot (the
                         # log basket); the wood's own registered spots (bark, deadfall) get a parallel line.
                         "absent": {"wood": {"chance": "The deadfall is quiet; whatever lives there is deep in it."},
                                    "chance": "The basket is quiet; whatever lives in the log is deep in it."}},
                 note="grandfathered (world_content_study / wood); night; the log basket"))
    return R


# ── what they do: the aphids' herbivory (world-side, from life.advance) ─────────────────────────
_APHID_HOSTS = ("broad_beans", "nasturtium", "peas")
_CATERPILLAR_HOSTS = ("nasturtium", "cabbage", "kale")      # J-0506: the cabbage white's caterpillars


def insect_pass(now: float, dt: float) -> None:
    """Aphids raise their host plants' `pests` while they are about (garden._advance_plant drains vigour from it and
    decays it 0.05/day); ladybirds — which scale with the aphids — pull the rate down. Logged once a day."""
    try:
        from core import life as _life, garden as _g
        days = max(0.0, min(dt, 3600.0)) / 86400.0
        if days <= 0:
            return
        rows_ = _life.rows()
        ap = rows_.get("aphids"); lb = rows_.get("ladybird")
        if not ap:
            return
        a = _life.activity(ap, "garden", now)
        if a < _life.PRESENT_AT:
            return
        l = _life.activity(lb, "garden", now) if lb else 0.0
        rate = 0.06 * a * max(0.2, 1.0 - 0.7 * l)             # per day, per host plant
        st = _g._load(); hit = 0
        for p in (st.get("plants") or {}).values():
            if p.get("species") in _APHID_HOSTS and p.get("stage") in LIVE_STAGES:
                p["pests"] = min(1.0, float(p.get("pests", 0)) + rate * days); hit += 1
                if random.random() < days * 0.3:
                    p.setdefault("history", []).append({"ts": now, "event": "aphids_on_the_tips"})
        # J-0506: the cabbage white's caterpillars — leaves eaten to the ribs, green droppings beneath (not slug holes);
        # fantails and sparrows are the world's correction
        cw = rows_.get("cabbage_white")
        cwa = _life.activity(cw, "garden", now) if cw else 0.0
        if cwa >= _life.PRESENT_AT:
            birds = max(_life.activity(rows_["fantail"], "garden", now) if "fantail" in rows_ else 0.0,
                        _life.activity(rows_["house_sparrows"], "garden", now) if "house_sparrows" in rows_ else 0.0)
            crate = 0.08 * cwa * max(0.3, 1.0 - 0.5 * birds)
            for p in (st.get("plants") or {}).values():
                if p.get("species") in _CATERPILLAR_HOSTS and p.get("stage") in LIVE_STAGES:
                    p["pests"] = min(1.0, float(p.get("pests", 0)) + crate * days); hit += 1
                    if random.random() < days * 0.3:
                        p.setdefault("history", []).append({"ts": now, "event": "caterpillars_on_the_leaves"})
                        try:
                            # J-0783: garden_knowledge.py is now fenced, so _gk.revise() below can
                            # raise profile.NonLiveWriteError -- deliberately NOT given its own
                            # carve-out here (unlike every other call site into garden_knowledge this
                            # job fixed). insect_pass(now, dt) is a per-subsystem periodic tick
                            # invoked once per world heartbeat from core/life.py's own subsystem list
                            # (itself a fail-open try one layer further out), not reachable via any
                            # act_from_thought()-style interactive dispatch a non-live diagnostic
                            # would actually exercise -- matches this fence's own established
                            # advance()/tick() exemption (cat_sounds.tick(), sensorium.tick(),
                            # J-0771's ambient-tick finding). Data-safety is unconditional regardless:
                            # guard_path() raises BEFORE any file I/O, so this swallow costs only
                            # diagnostic visibility on a path nothing exercises directly. See J-0783's
                            # own finding in docs/staged/world_store_write_fence.md.
                            from core import garden_knowledge as _gk
                            _gk.revise(p["species"], "eaten_to_the_ribs", "caterpillars")
                        except Exception:
                            pass
        if hit:
            _g._save()
            ls = _life._load()
            if now - float(ls.get("aphids_logged", 0.0)) > 86400:
                ls["aphids_logged"] = now; _life._save()
                _life._log(_life._EVENTS, {"kind": "effect", "key": "aphids", "place": "garden", "what": "on_the_tips", "hosts": hit, "ladybirds": round(l, 2)})
    except Exception as exc:
        logger.debug("[garden_insects] insect_pass failed (non-fatal): %s", exc)


# ── the truth gate for the old insect prose ─────────────────────────────────────────────────────

def present(key: str, place: str = "garden", now: float | None = None) -> bool:
    if not INSECT_TRUTH_GATE:
        return True
    try:
        from core import life as _life
        r = _life.rows().get(key)
        return bool(r) and _life.activity(r, place, now) >= _life.PRESENT_AT
    except Exception:
        return True


def gate_lines(pairs, place: str = "garden") -> list[str]:
    """[(row key or None, line)] → the lines whose creature is about (None = ungated). Also drops any line naming a
    plant that is not sown (the 2026-08-22 bed gate, applied to insect lines — closes the lavender leak, J-0501)."""
    try:
        sown = sown_species()
        out = []
        for key, line in pairs:
            if key and not present(key, place):
                continue
            low = line.lower()
            named = [sp for sp, words in _PLANT_WORDS.items() if any(w in low for w in words)]
            if any(sp not in sown for sp in named):
                continue
            out.append(line)
        return out
    except Exception:
        return [line for _, line in pairs]


def bees_about(now: float | None = None) -> bool:
    return present("honeybee", "garden", now) or present("bumblebee", "garden", now)
