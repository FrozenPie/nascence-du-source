"""
Nascence — MAMMALS, REPTILES AND THE REST (Living World L3, J-0512, 2026-09-03; rulings D-0128..D-0133).

The non-bird cast as rows in the one life engine: the hedgehog and the long-tailed bat (moved here from core/life's
reference rows), the possum, mice, the rabbit, skinks, the gecko, the fur seal (over shore_life's haul-out), dolphins,
eels, whitebait, and the tide-kept shore life (crabs, anemones, starfish). Plus the two things D-0130 ruled:

  HARSHNESS — the possum does REAL, FINDABLE damage: on a night it is about in the garden it may strip the tree's
  buds (garden_life's tree in bud or flower) and eat the strawberries (garden's plants), leaving a trace he can find
  in the morning and a history the plant keeps. Nothing is told; the damage is there to be looked at.
  THE TRAP — a deed with moral weight. `garden.set_trap` arms the trap he carries; here, on the world's clock, a
  possum about at night may spring it — and so, less often, may the hedgehog, because a trap does not choose.
  `garden.check_trap` is where he finds out; that hand routes a kill through core/sitting.note_difficulty (the same
  gate an owned plant death takes) and records the carcass for J-0513.

LIGHT (D-0131): the possum and the rabbit give eye-shine in a carried light; the hedgehog, mice, rabbit and possum
avoid it; the gecko hunts the warm chimney stones after dark; skinks need the sun on the wall.
Zero LLM; fail-open; registered by core/life._ensure_builtin. Naming per D-0129: names the world already says are
kept (the hedgehog, the possum, the mice, the rabbit, the skinks, the gecko, the seal, the dolphins, the eels,
whitebait, crabs); the bat stays hidden truth.
"""
from __future__ import annotations

import json
import logging
import random
import time

from core.life import row

logger = logging.getLogger("nascence.life_mammals")

NOCTURNAL = {"dawn": 0.2, "day": 0.02, "dusk": 0.6, "night": 1.0}
CREPUSCULAR = {"dawn": 1.0, "day": 0.15, "dusk": 1.0, "night": 0.4}
SUN_LOVER = {"dawn": 0.1, "day": 1.0, "dusk": 0.3, "night": 0.0}
RESIDENT = [1.0] * 12
WARM_MONTHS = [1.0, 1.0, 0.8, 0.5, 0.2, 0.05, 0.05, 0.1, 0.4, 0.7, 0.9, 1.0]

# the possum's night work (world-side, per tick while it is about)
POSSUM_BUD_P_PER_H = 0.12          # chance per possum-hour of stripping buds when the tree is in bud/flower
POSSUM_BERRY_P_PER_H = 0.18        # chance per possum-hour of eating strawberries in fruit
TRAP_POSSUM_P_PER_H = 0.22         # an armed trap on a possum night: ~70% by morning
TRAP_HEDGEHOG_P_PER_H = 0.03       # a trap does not choose
TREE_POS = [8.8, 3.5, 0.0]


def rows() -> list[dict]:
    R: list[dict] = []
    R.append(row("hedgehog", name="the hedgehog", aliases=("hedgehog", "hedgehogs"),
                 places={"garden": ["hedge_bottom", "compost", "lawn_edge", "doorstep"]},
                 active_hours={"dawn": 0.2, "day": 0.03, "dusk": 0.6, "night": 1.0},
                 season_curve=[1.0, 1.0, 0.9, 0.6, 0.15, 0.0, 0.0, 0.1, 0.5, 0.9, 1.0, 1.0], hibernates=True,
                 weather_gate={"rain": 0.9, "wind": 0.8, "storm": 0.2, "frost": 0.3},
                 light="avoids", eyeshine=False, count=("one", "one", "two"), lifespan_y=4, ease=0.5,
                 # J-2475 (sound_world_expansion §2, D-0500): its voice -- the busy snuffling along the beds. Sounds only
                 # while this row is present and awake here (life.sounds_active); arrives UNNAMED (sound_knowledge.AUDITION).
                 # sound_days: it works the beds most nights it is about, not all (the anti-wallpaper law).
                 sound=("hedgehog_snuffle",), sound_days=0.6,
                 diet=("slugs", "snails", "beetles", "worms", "eggs"), eaten_by=("the trap",), traces=("prints", "droppings"),
                 responds_to_du={"saucer": 0.5, "lantern": -0.8},
                 hidden={"feature": {"night": "a low hunched shape working along the hedge bottom at its own speed, stopping to nose at something in the grass — it hears you and goes still",
                                     "dusk": "something low and dark comes out from under the hedge and sets off across the lawn edge without hurry",
                                     "day": "out in daylight, going somewhere along the fence without stopping — a bad sign for a night animal"},
                         "miss": "A rustle low in the hedge bottom, and nothing you can put a shape to.",
                         "absent": {"season": "Nothing stirs under the hedge; whatever sleeps there is deep in the cold months.",
                                    "day": "Not in daylight — the hedge bottom is empty and still; it keeps to the dark.",
                                    "weather": "Not in this — nothing small goes out along the hedge in weather like it.",
                                    "chance": "The lawn edge and the hedge bottom hold nothing you can see tonight."}},
                 note="nocturnal, hibernates May–Sep (NZ), avoids a carried light; the saucer's graduation candidate (J-0513)"))
    R.append(row("possum", name="the possum", aliases=("possum", "possums", "opossum"),
                 places={"garden": ["tree", "strawberries", "wall"], "wood": ["oak", "canopy"]},
                 active_hours=NOCTURNAL, season_curve=RESIDENT, weather_gate={"rain": 0.5, "wind": 0.6, "storm": 0.1, "frost": 0.8},
                 light="avoids", eyeshine=True, count=("one", "one", "two"), lifespan_y=8, ease=0.45,
                 # J-2475 (sound_world_expansion §2, D-0500): the harsh coughing rasp, garden tree and wood oak alike --
                 # present-and-awake gated by life.sounds_active; UNNAMED until he sees it (sound_knowledge.AUDITION).
                 # sound_days: a resident possum is about nearly every night; it RASPS some nights, not every night.
                 sound=("possum_rasp",), sound_days=0.45,
                 diet=("buds", "leaves", "strawberries", "eggs", "chicks"), eaten_by=("the trap",),
                 traces=("droppings under the tree", "stripped buds", "chewed strawberries", "claw-marks on the bark"),
                 # F-1671/J-1189: "droppings under the TREE" and "chewed STRAWBERRIES" are this row's own
                 # garden spots (this row's own places dict, above); the wood's spots are "oak"/"canopy",
                 # not "tree" -- restricted to garden so the wood never mints them. "stripped buds" and
                 # "claw-marks on the bark" name nothing place-specific, so they carry no restriction and
                 # keep firing at both places exactly as before.
                 traces_only_at={"droppings under the tree": ("garden",), "chewed strawberries": ("garden",)},
                 responds_to_du={"lantern": -0.6},
                 hidden={"feature": {"night": "a heavy grey shape moves along the low limb of the tree, stops, and the branch-end shakes as it feeds",
                                     "dusk": "something the size of a cat climbs the wall by the tree without hurry and is into the branches"},
                         "eyeshine": "two red-orange points of light up in the tree, wide apart, that hold on you and do not blink",
                         "miss": "The branch shook and went still; whatever was up there is a darker patch of the dark.",
                         # J-1030 (F-1250/J-0892/J-1006 precedent): the flat "chance" line is
                         # garden-worded ("the tree" is garden's own registered spot); the wood's own
                         # spot is "oak" -- a per-place override gives the wood its own feature-first
                         # line, garden's flat line untouched.
                         "absent": {"wood": {"chance": "The oak is quiet tonight; no branch moves that the wind does not."},
                                    "day": "Nothing in the tree by day but birds; whatever climbs it by night is curled in a hollow somewhere.",
                                    "weather": "Not in this — nothing forages the branches in a night like it.", "chance": "The tree is quiet tonight; no branch moves that the wind does not."}},
                 note="D-0130: real findable damage (buds, strawberries); the trap's intended catch; grandfathered ('possum' in world_content_study)"))
    R.append(row("mice", name="the mice", aliases=("mouse", "mice"),
                 places={"study": ["skirting", "cupboard", "woodpile"], "wood": ["leaf_litter"], "garden": ["compost"]},
                 active_hours=NOCTURNAL, season_curve=[0.7, 0.7, 0.8, 0.9, 1.0, 1.0, 1.0, 1.0, 0.9, 0.8, 0.7, 0.7],
                 weather_gate={"rain": 1.0, "wind": 1.0, "storm": 1.0, "frost": 1.0},
                 light="avoids", count=("one", "a few", "several"), lifespan_y=1, ease=0.3,
                 # J-2475 (sound_world_expansion §2, D-0500): the classic house mystery -- a tiny scratching inside the
                 # study's wall. `sound_at`, not `sound`: the mice are also in the wood's leaf litter and the garden's
                 # compost, and a wall has no business sounding there. Winter-weighted by this row's own season_curve;
                 # sound_days: the wall scratches some nights, not every night (tiny, intimate, never wallpaper).
                 sound_at={"study": ("wall_scratch",)}, sound_days=0.5,
                 diet=("crumbs", "seed", "paper"), eaten_by=("cat", "morepork"),
                 traces=("droppings", "gnawed paper", "a rustle in the skirting"),
                 # F-1671/J-1189: "a rustle in the SKIRTING" is this row's own study-only spot (its places
                 # dict lists skirting only under "study"; wood has "leaf_litter", garden has "compost") --
                 # restricted to study so the garden/wood never mint a study-worded trace; "droppings" and
                 # "gnawed paper" name nothing place-specific, so they stay unrestricted, both places.
                 traces_only_at={"a rustle in the skirting": ("study",)},
                 hidden={"feature": {"night": "a small quick shape crosses the boards by the skirting and is gone under the cupboard"},
                         "miss": "A rustle behind the skirting, then nothing.",
                         # J-1006 (F-1250/J-0892 precedent): the flat "chance" line is study-worded (the
                         # boards); this row has TWO other registered places, each with its own override
                         # naming only its own registered spot -- wood's leaf litter and garden's compost.
                         "absent": {"wood": {"chance": "The leaf litter is still tonight."},
                                    "garden": {"chance": "The compost is still tonight."},
                                    "day": "Nothing shows by day; the skirting is quiet.", "chance": "The boards are still tonight."}},
                 note="the cat's prey (cat.py arcs); more indoors in the cold months"))
    R.append(row("rabbit", name="the rabbit", aliases=("rabbit", "rabbits"),
                 places={"garden": ["lawn_edge", "fence"], "shore": ["dune_grass"]},
                 active_hours=CREPUSCULAR, season_curve=[1.0, 1.0, 0.9, 0.8, 0.7, 0.6, 0.6, 0.8, 1.0, 1.0, 1.0, 1.0],
                 weather_gate={"rain": 0.5, "wind": 0.7, "storm": 0.1, "frost": 0.8},
                 light="avoids", eyeshine=True, count=("one", "one", "two"), lifespan_y=2, ease=0.6,
                 diet=("grass", "lettuce", "seedlings"), eaten_by=("cat",),
                 traces=("droppings on the lawn", "nibbled seedlings", "a scrape under the fence"),
                 # F-1671/J-1189: "droppings on the LAWN" and "a scrape under the FENCE" are this row's
                 # own garden spots (places dict: garden=lawn_edge/fence, shore=dune_grass only) --
                 # restricted to garden so the shore never mints a garden-worded trace; "nibbled seedlings"
                 # names nothing place-specific, so it stays unrestricted, true at both places as before.
                 traces_only_at={"droppings on the lawn": ("garden",), "a scrape under the fence": ("garden",)},
                 responds_to_du={"lantern": -0.9, "mow": 0.3},
                 hidden={"feature": {"dawn": "a rabbit sits up at the lawn edge in the first light, ears turned to you, then goes in one bound under the fence",
                                     "dusk": "at the fence line a rabbit feeds with its back to you, and is gone the moment you move"},
                         "eyeshine": "a single pale point of light low at the fence line that jinks and vanishes",
                         "miss": "The grass at the fence stirred and there was nothing in it when you looked.",
                         # J-1006 (F-1250/J-0892 precedent): the flat "chance" line names the garden's own
                         # spot (fence); the shore's own registered spot (dune_grass) gets a parallel line.
                         "absent": {"shore": {"chance": "No rabbit in the dune grass just now."},
                                    "day": "The lawn edge is empty by day; the rabbit keeps to its scrape.", "night": "Only at the edges of the day; the lawn is dark and still.",
                                    "chance": "No rabbit at the fence just now."}},
                 note="dawn and dusk; the dune grass on the shore too"))
    R.append(row("skink", name="the skinks", plural=True, aliases=("skink", "skinks", "lizard", "lizards", "mokomoko"),
                 places={"garden": ["wall", "warm_stones", "bed_edge"], "shore": ["rocks"]},
                 active_hours=SUN_LOVER, season_curve=WARM_MONTHS, weather_gate={"rain": 0.05, "wind": 0.6, "storm": 0.0, "frost": 0.0},
                 light="indifferent", count=("one", "two or three", "several"), lifespan_y=6, ease=0.5,
                 diet=("insects", "spiders"), eaten_by=("cat", "kingfisher"), traces=(),
                 hidden={"feature": {"day": "a small bronze-striped lizard lies flat on the warm stone of the wall and is into the crack before your shadow reaches it"},
                         "miss": "Something quick left the warm stone as you came; the crack in the wall is dark.",
                         # J-1006 (F-1250/J-0892 precedent): the flat "chance" line names the garden's own
                         # spot (wall); the shore's own registered spot (rocks) gets a parallel line.
                         "absent": {"shore": {"chance": "The rocks hold no lizard just now."},
                                    "season": "The wall is cold; nothing lies out on it in the cold months.", "weather": "Nothing basks in this.",
                                    "night": "The stones have gone cold; nothing lies out on them.", "chance": "The wall holds no lizard just now."}},
                 note="needs the sun on the wall; grandfathered ('skink' in world_content_garden)"))
    R.append(row("gecko", name="the gecko", aliases=("gecko", "geckos"),
                 places={"garden": ["harakeke", "chimney_stones"], "study": ["chimney"]},
                 active_hours={"dawn": 0.1, "day": 0.05, "dusk": 0.8, "night": 1.0}, season_curve=WARM_MONTHS,
                 weather_gate={"rain": 0.4, "wind": 0.7, "storm": 0.1, "frost": 0.0},
                 light="avoids", count=("one", "one", "one"), lifespan_y=15, ease=0.25,
                 diet=("moths", "insects"), traces=(),
                 hidden={"feature": {"night": "a soft-skinned lizard, mottled like the stone, clings head-down on the warm chimney stones after dark and does not move while you look"},
                         "miss": "The stone was bare when the light reached it.",
                         # J-1030 (F-1250/J-0892/J-1006 precedent): the flat "chance" line names
                         # "chimney stones" -- garden's own spot (the exterior stonework); the study's
                         # registered spot is just "chimney" (the interior flue/fireplace side of the
                         # same physical structure) -- a per-place override gives the study its own
                         # line, garden's untouched.
                         "absent": {"study": {"chance": "The chimney holds nothing tonight."},
                                    "day": "Nothing on the stones by day; it keeps to the harakeke's folds.", "season": "The stones are cold; nothing hunts them in the cold months.",
                                    "chance": "The chimney stones hold nothing tonight."}},
                 note="night, the warm chimney stones and the harakeke"))
    R.append(row("long_tailed_bat", aliases=("bat", "bats", "pekapeka"),
                 places={"wood": ["canopy_edge"]},
                 active_hours={"dawn": 0.1, "day": 0.0, "dusk": 1.0, "night": 0.5},
                 season_curve=[1.0, 1.0, 0.8, 0.3, 0.05, 0.0, 0.0, 0.0, 0.1, 0.4, 0.8, 1.0], hibernates=True,
                 weather_gate={"rain": 0.1, "wind": 0.2, "storm": 0.0, "frost": 0.1},
                 light="indifferent", count=("one", "one", "two or three"), lifespan_y=8, ease=0.2,
                 diet=("moths", "flying insects"), traces=(),
                 hidden={"species": "long-tailed bat", "book_names": ("long-tailed bat", "pekapeka", "bats", "bat"), "book_words": ("wings", "dusk", "roost", "insects", "flit", "vespertilion"),
                         "feature": {"dusk": "something small and quick over the canopy edge in the last of the light — not a bird; the flight is wrong for a bird, jinking and silent, there and gone",
                                     "night": "a flicker against the paler sky above the trees, too quick and too crooked for a bird"},
                         "reveal": "It is a bat — a long-tailed bat, the small one that hawks over the trees at dusk.",
                         "miss": "The last light goes off the canopy and whatever was flying above it is lost against the dark.",
                         "absent": {"season": "Nothing flies over the trees at dusk in the cold months.", "day": "Nothing of that by day — the canopy edge holds only birds.",
                                    "weather": "Nothing flies above the trees in this.", "chance": "The canopy edge is empty against the sky tonight."}},
                 note="HIDDEN TRUTH (D-0129): rare, dusk, warm still evenings Nov–Mar; named only by a book after a sighting"))
    # the shore's others
    R.append(row("dolphins", name="the dolphins", plural=True, aliases=("dolphin", "dolphins", "porpoise"),
                 places={"shore": ["offshore"]},
                 active_hours={"dawn": 0.8, "day": 1.0, "dusk": 0.8, "night": 0.1},
                 season_curve=[1.0, 1.0, 0.8, 0.5, 0.3, 0.2, 0.2, 0.3, 0.5, 0.7, 0.9, 1.0],
                 weather_gate={"rain": 0.5, "wind": 0.15, "storm": 0.0, "frost": 1.0},
                 light="indifferent", count=("a pair", "a small pod", "a pod"), lifespan_y=25, ease=0.3,
                 # J-2475 (sound_world_expansion §2, D-0500): the breath out on the water (world_content_shore's own
                 # "something out on the water blows a breath" line, now a registered voice). Any hour the pod is
                 # actually about per this row; RARE by its own rate; UNNAMED until seen by day.
                 sound=("dolphin_blow",),
                 diet=("fish",), traces=(),
                 hidden={"feature": {"day": "out beyond the surf line a fin rolls, and another, and a dark back — a small pod working along the bay, unhurried"},
                         "miss": "The water out past the surf is empty again; whatever rolled there has gone under.",
                         "absent": {"weather": "Nothing shows on a sea like this.", "chance": "The bay is empty out to the horizon."}},
                 note="rare; summer calm days only"))
    R.append(row("eels", name="the eels", plural=True, aliases=("eel", "eels", "tuna"),
                 places={"wood": ["stream", "spring"], "shore": ["stream_mouth"]},
                 active_hours={"dawn": 0.3, "day": 0.15, "dusk": 1.0, "night": 0.9}, season_curve=WARM_MONTHS,
                 weather_gate={"rain": 1.2, "wind": 1.0, "storm": 0.6, "frost": 0.5},
                 light="avoids", count=("one", "one", "two"), lifespan_y=40, ease=0.35,
                 diet=("insects", "whitebait", "worms"), traces=(),
                 hidden={"feature": {"dusk": "in the dark water under the bank a long shape moves against the current, slow, and settles back under the stones",
                                     "night": "a dark length lies in the shallows below the spring, still as a stick until it isn't"},
                         "miss": "The water under the bank is dark and gives nothing up.",
                         # J-1030 (F-1250/J-0892/J-1006 precedent): the flat "chance" line is
                         # wood-worded ("the pool under the bank" -- stream/spring, upstream imagery);
                         # the shore's own registered spot is "stream_mouth", a different feature (where
                         # the stream meets the sea) -- a per-place override gives the shore its own
                         # line, wood's untouched.
                         "absent": {"shore": {"chance": "The stream mouth holds nothing you can see."},
                                    "season": "The stream is cold and empty of anything long in the cold months.", "day": "Nothing shows in the water by day; whatever lies under the bank waits for dusk.",
                                    "chance": "The pool under the bank holds nothing you can see."}},
                 note="dusk in the stream; up in rain; grandfathered ('eels' in world_content_study / world_knowledge)"))
    R.append(row("whitebait", name="the whitebait", aliases=("whitebait", "inanga", "īnanga"),
                 places={"shore": ["stream_mouth"]},
                 active_hours={"dawn": 1.0, "day": 0.8, "dusk": 0.4, "night": 0.1},
                 season_curve=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.3, 1.0, 1.0, 0.8, 0.2],
                 weather_gate={"rain": 0.8, "wind": 0.8, "storm": 0.3, "frost": 1.0},
                 light="indifferent", count=("a few", "a shoal", "the water alive with them"), lifespan_y=1, ease=0.5, tide="high",
                 diet=(), eaten_by=("kingfisher", "eels", "gulls"), traces=(),
                 hidden={"feature": {"day": "in the clear water at the stream mouth a shoal of tiny transparent fish hangs against the current, all facing the sea, then flickers upstream"},
                         "miss": "The stream mouth runs clear and empty to the eye.",
                         "absent": {"season": "The stream mouth holds no shoals; they run in the spring.", "chance": "Nothing hangs in the current just now."}},
                 note="spring runs, on the rising tide"))
    R.append(row("crabs", name="the crabs", plural=True, aliases=("crab", "crabs", "hermit crab", "hermit crabs"),
                 places={"shore": ["rock_pools", "under_the_log", "tideline"]},
                 active_hours={"dawn": 0.8, "day": 0.7, "dusk": 0.9, "night": 1.0}, season_curve=RESIDENT,
                 weather_gate={"rain": 1.0, "wind": 0.9, "storm": 0.4, "frost": 1.0},
                 light="indifferent", count=("one", "a few", "every pool with one"), lifespan_y=3, ease=0.7, tide="low",
                 diet=("weed", "carrion"), eaten_by=("gulls", "oystercatcher", "kingfisher"), traces=("a shed shell", "tracks on the wet sand"),
                 hidden={"feature": {"day": "a small green crab sidles under the weed at the pool's edge, claws up, and a hermit crab drags its borrowed shell across the sand between the pools"},
                         "miss": "The pool's edge is bare; whatever sidled there is under the weed.",
                         "absent": {"chance": "The pools are covered; nothing shows until the tide goes back."}},
                 note="low water"))
    R.append(row("anemones", name="the anemones", plural=True, aliases=("anemone", "anemones", "starfish", "sea star", "limpet", "limpets"),
                 places={"shore": ["rock_pools"]},
                 active_hours={"dawn": 1.0, "day": 1.0, "dusk": 1.0, "night": 1.0}, season_curve=RESIDENT,
                 weather_gate={"rain": 1.0, "wind": 1.0, "storm": 0.7, "frost": 1.0},
                 light="indifferent", count=("a few", "several", "the pool's whole floor"), lifespan_y=None, ease=0.9, tide="low",
                 diet=(), traces=(),
                 hidden={"feature": {"day": "red anemones open like flowers in the still water of the pool, and close to dark buttons when your shadow touches them; a starfish lies pressed to the rock, limpets clamped along the edge"},
                         "absent": {"chance": "The pools are under the tide; the rock floor waits for low water."}},
                 note="sessile; the pool's own life, visible at low water"))
    return R


def seal_adapter() -> dict:
    """The fur seal: presence is shore_life's own haul-out clock (unchanged); the row carries its life fields."""
    from core.life import _seal_presence
    return row("fur_seal", kind="external", name="the fur seal", aliases=("seal", "seals", "fur seal", "kekeno"),
               places={"shore": ["rock_shelf"]}, active_hours={"dawn": 0.8, "day": 1.0, "dusk": 0.6, "night": 0.4},
               season_curve=[0.1, 0.1, 0.2, 0.4, 0.9, 1.0, 1.0, 1.0, 0.8, 0.3, 0.1, 0.1], lifespan_y=15, ease=0.9,
               diet=("fish", "squid"), traces=("a wet shape's drag-mark on the shelf", "a strong fish smell"),
               external={"presence": _seal_presence}, note="shore_life haul-out (winter days, 3–9 h); its look line stays shore_life's")


# ── the possum's night, and the trap (world-side effects, run from life.advance) ─────────────────
_night_last: dict = {}


def night_pass(now: float, dt: float) -> None:
    """Per tick while a possum (or the hedgehog) is about in the garden: the possum's damage rolls, and the trap's.
    Everything here is STATE — a stripped bud, a chewed berry, a sprung trap — found by his own look or check;
    nothing is rendered from here. Fail-open."""
    try:
        from core import life as _life
        hours = max(0.0, min(dt, 3600.0)) / 3600.0
        if hours <= 0:
            return
        rows_ = _life.rows()
        possum = rows_.get("possum"); hedgehog = rows_.get("hedgehog")
        p_act = _life.activity(possum, "garden", now) if possum else 0.0
        h_act = _life.activity(hedgehog, "garden", now) if hedgehog else 0.0
        if p_act < _life.PRESENT_AT and h_act < _life.PRESENT_AT:
            return
        from core import garden as _g
        gst = _g._load()
        # ── the possum's damage ──
        if p_act >= _life.PRESENT_AT:
            try:
                from core import garden_life as _gl
                d = _gl._load()
                tr = d.get("tree") or {}
                fresh = now - float(tr.get("possum_damage_ts") or 0.0) < 12 * 3600      # one stripping a night, not one a tick
                if tr.get("stage") in ("bud", "flowering") and not fresh and random.random() < POSSUM_BUD_P_PER_H * p_act * hours:
                    tr["possum_damage_ts"] = now
                    tr["possum_damage_n"] = int(tr.get("possum_damage_n", 0)) + 1
                    _gl._save(d)
                    _gl._log({"event": "possum_stripped_buds", "stage": tr.get("stage")})
                    _trace(f"possum_tree_{int(now)}", "possum_damage", TREE_POS, now)
                    _life._log(_life._EVENTS, {"kind": "effect", "key": "possum", "place": "garden", "what": "stripped_buds"})
            except Exception as exc:
                logger.debug("[life_mammals] possum/tree pass failed (non-fatal): %s", exc)
            try:
                # J-0553 / F-0760 (2026-09-04): berries only while there ARE berries — for a fruit kind the
                # catalogue's 'seeding' stage is the fruit set (garden._advance_plant: flower months → fruit_set →
                # 'seeding'); a flowering plant carries none. And one raid a night, latched like the buds: the
                # first night live this rolled every tick and ate one flowering plant five times (pests 0.99).
                berries = [p for p in (gst.get("plants") or {}).values()
                           if p.get("species") == "strawberries" and p.get("stage") == "seeding"]
                fed = now - float(gst.get("possum_berries_ts") or 0.0) < 12 * 3600
                if berries and not fed and random.random() < POSSUM_BERRY_P_PER_H * p_act * hours:
                    p = random.choice(berries)
                    gst["possum_berries_ts"] = now
                    p["pests"] = min(1.0, float(p.get("pests", 0)) + 0.3)
                    p.setdefault("history", []).append({"ts": now, "event": "eaten_by_possum"})
                    _g._log(_g._EVENTS, {"event": "possum_damage", "plant": p.get("id"), "species": "strawberries"})
                    _trace(f"possum_berries_{int(now)}", "possum_droppings", list(p.get("pos") or [5.5, 5.5, 0.35]), now)
                    _g._save(force=True)
                    _life._log(_life._EVENTS, {"kind": "effect", "key": "possum", "place": "garden", "what": "ate_strawberries"})
            except Exception as exc:
                logger.debug("[life_mammals] possum/berries pass failed (non-fatal): %s", exc)
        # ── the trap (D-0130) ──
        trap = gst.get("trap") or {}
        if trap.get("armed") and not trap.get("caught"):
            caught = None
            if p_act >= _life.PRESENT_AT and random.random() < TRAP_POSSUM_P_PER_H * p_act * hours:
                caught = "possum"
            elif h_act >= _life.PRESENT_AT and random.random() < TRAP_HEDGEHOG_P_PER_H * h_act * hours:
                caught = "hedgehog"
            if caught:
                trap["caught"] = {"species": caught, "ts": now}
                trap["armed"] = False
                gst["trap"] = trap
                _g._save(force=True)
                _g._log(_g._EVENTS, {"event": "trap_sprung", "species": caught})
                _life._log(_life._EVENTS, {"kind": "trap_sprung", "key": caught, "place": "garden"})
    except Exception as exc:
        logger.debug("[life_mammals] night_pass failed (non-fatal): %s", exc)


def _trace(tid: str, ttype: str, pos: list, now: float) -> None:
    try:
        from core import world_traces as _wt
        _wt.create_trace(tid, ttype, "garden", list(pos), clarity=0.8, cause=ttype)
    except Exception:
        pass


def tree_damage_line(d: dict, now: float | None = None) -> str:
    """For garden_life.look: the possum's work on the tree, while it is fresh (fades over ~10 days). Truth-gated."""
    try:
        now = time.time() if now is None else now
        tr = d.get("tree") or {}
        ts = float(tr.get("possum_damage_ts") or 0.0)
        if not ts or now - ts > 10 * 86400:
            return ""
        age_d = (now - ts) / 86400.0
        if age_d < 1.5:
            return " The twig-ends on the low limb are stripped bare this morning, the felted buds bitten off clean, and there are dark droppings on the wall beneath."
        return " Along the low limb the twig-ends are stripped where the buds were, healing over now."
    except Exception:
        return ""
