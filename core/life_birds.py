"""
Nascence — THE BIRDS (Living World L2, J-0511, 2026-09-03; rulings D-0128..D-0133).

The bird cast of every place as rows in the ONE life engine (core/life.py). Each row says where it can be, when in
the day and the year, how weather and light bear on it, which sound points it makes (core/soundscape._SOUNDS
keys) and at what hours, how many there are, how long it lives, what it eats, what it leaves, how it answers his
own deeds, and how it comes to be NAMED.

NAMING (D-0129), one ledger not two: a bird that already has a learnable VOICE in core/sound_knowledge.AUDITION
carries `audition=<key>` and its name is whatever that ledger says — heard-and-seen or read there, learned there.
A bird the world already names in its own lines (the blackbird, the tui, the gulls, the karoro, the tōrea, the
terns, the tauhou, the starlings, the sparrows, the swallows, the thrush, the wren, the morepork, the wood pigeon)
keeps that name (grandfathered). Everything else is HIDDEN TRUTH rendered feature-first until sighting + a book.

MIGRATION CALENDAR (D-0133, NZ): the season curves ARE the calendar — the shining cuckoo arrives in October and
is gone by March; the terns are a summer shore; kororā come ashore Sep–Feb; tauhou flock through in winter;
swallows thicken in summer; godwits pass over in September–October (D-0132: overhead only, no estuary) and again
in March going north. Arrivals and departures are logged once by life.advance and weighted by the Transport
Manager as "earlier / later / rarer than usual" freight.

Rows per place (D-0128: things are their own lists) — this module is the birds' list; the garden's insects and
the mammals will be their own. Zero LLM, fail-open. Registered by core/life._ensure_builtin.
"""
from __future__ import annotations

from core.life import row

# ── shared curves ────────────────────────────────────────────────────────────────────────────────
DIURNAL = {"dawn": 1.0, "day": 0.85, "dusk": 0.6, "night": 0.0}
CREPUSCULAR = {"dawn": 0.8, "day": 0.3, "dusk": 1.0, "night": 0.2}
NOCTURNAL = {"dawn": 0.2, "day": 0.0, "dusk": 0.5, "night": 1.0}
RESIDENT = [1.0] * 12
# Jan..Dec
SUMMER_VISITOR = [1.0, 1.0, 0.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.7, 1.0, 1.0]        # cuckoo, terns: arrive Oct, gone by Apr
WINTER_FLOCK = [0.2, 0.2, 0.4, 0.8, 1.0, 1.0, 1.0, 0.9, 0.5, 0.2, 0.2, 0.2]          # tauhou flocks
SEPT_PASSAGE = [0.0, 0.0, 0.5, 0.2, 0.0, 0.0, 0.0, 0.0, 1.0, 0.8, 0.1, 0.0]          # godwits over (Sep–Oct; a March return)
KORORA_ASHORE = [0.9, 0.7, 0.2, 0.0, 0.0, 0.0, 0.0, 0.1, 0.6, 1.0, 1.0, 1.0]         # Sep–Feb, moult ashore Feb
SMALL_BIRD_WEATHER = {"rain": 0.5, "wind": 0.35, "storm": 0.05, "frost": 0.8}         # gales ground the small ones
SEABIRD_WEATHER = {"rain": 0.8, "wind": 1.0, "storm": 0.4, "frost": 1.0}


def _passage_day(now: float, place: str = "") -> float:
    """Godwits (D-0132): skeins pass over on some September days, not every hour of the month — one seeded fact per
    day (about a third of the days), for the daylight hours of that day."""
    import random as _r, time as _t
    lt = _t.localtime(now)
    return 1.0 if _r.Random(f"godwits:{lt.tm_year}:{lt.tm_yday}").random() < 0.33 else 0.0


def _gulls_inland(now: float, place: str = "") -> float:
    """The gulls come over the garden in WIND (riding the updraft off the slope — the garden's own line); on a
    calm day they are the shore's. The shore keeps them always."""
    if place != "garden":
        return 1.0
    try:
        from core import sensorium as _s
        wind = str(_s.state.get("wind") or "")
    except Exception:
        wind = ""
    return 1.0 if wind in ("gale", "strong") else 0.5 if wind in ("fresh", "gusty") else 0.12


def rows() -> list[dict]:
    R: list[dict] = []
    # ── GARDEN ─────────────────────────────────────────────────────────────────────────────────
    R.append(row("blackbird", name="the blackbird", aliases=("blackbird", "blackbirds"),
                 places={"garden": ["lawn_edge", "hedge", "compost", "bed"], "wood": ["undergrowth"]},
                 active_hours=DIURNAL, season_curve=RESIDENT, weather_gate={"rain": 0.9, "wind": 0.5, "storm": 0.1, "frost": 0.9},
                 sound=("blackbird_song",), alarm_sound="blackbird_alarm", alarm_on="cat", sings_at=("dawn", "dusk"),
                 count=("one", "a pair", "a pair"), lifespan_y=4, ease=0.8, nest="blackbird_nest",
                 diet=("worms", "snails", "berries", "seed"), eaten_by=("cat",), traces=("a feather", "turned leaves"),
                 responds_to_du={"feed_birds": 0.6, "dig": 0.5, "mow": 0.4},
                 hidden={"feature": {"day": "a blackbird works the lawn edge, head cocked, then stabs and comes up with something thin and fighting",
                                     "night": "nothing — the blackbird roosts deep in the hedge and does not stir"},
                         # J-1216 (D-0254/F-1706, confirmed fire): the two feature lines above are
                         # garden-worded (lawn edge, hedge) and misrender in the wood, this row's other
                         # registered place -- same J-1006 precedent as the "absent" override below, now
                         # extended to the feature lines themselves. F-1706's own drafted wording, verbatim.
                         "feature_by_place": {"wood": {"day": "a blackbird works the undergrowth, head cocked, then stabs and comes up with something thin and fighting",
                                                        "night": "nothing — the blackbird roosts deep in the undergrowth and does not stir"}},
                         # J-1006 (F-1250/J-0892 precedent): the flat "chance" line below is garden-worded
                         # (lawn edge, hedge) and would misrender in the wood, this row's other registered
                         # place -- a per-place override gives the wood its own line naming only its own
                         # registered spot (undergrowth); every other place/why key is untouched.
                         "absent": {"wood": {"chance": "No blackbird in the undergrowth just now."},
                                    "night": "The blackbird has gone to roost in the hedge; it will be the first voice at first light.",
                                    "weather": "The blackbird keeps to the hedge in this — nothing feeds on the open lawn in a gale.",
                                    "chance": "The lawn edge is empty; the blackbird is somewhere in the hedge, quiet."}},
                 note="grandfathered; follows the spade, the shears and the seed; alarms when the cat crosses (D-0133)"))
    R.append(row("song_thrush", name="the thrush", aliases=("thrush", "song thrush"),
                 places={"garden": ["lawn", "anvil_stone", "hedge"]},
                 active_hours=DIURNAL, season_curve=RESIDENT, weather_gate={"rain": 1.0, "wind": 0.5, "storm": 0.1, "frost": 0.8},
                 sound=(), sings_at=("dawn", "dusk"), count=("one", "one", "a pair"), lifespan_y=3, ease=0.6,
                 diet=("snails", "worms"), eaten_by=("cat",), traces=("broken snail shells at the anvil stone",),
                 responds_to_du={"mow": 0.5, "dig": 0.4},
                 hidden={"feature": {"day": "a speckled brown bird stands very upright on the lawn, then runs three steps and stops, listening to the ground",
                                     "night": ""},
                         "absent": {"night": "The thrush is roosting; its anvil stone by the hedge holds only broken shells.",
                                    "chance": "No thrush on the lawn now — but the anvil stone by the hedge has fresh-broken shells round it."}},
                 note="grandfathered ('thrush' in world_content_garden); the anvil stone is J-0513's trace"))
    R.append(row("tui", name="the tūī", aliases=("tui", "tūī"),
                 places={"garden": ["kowhai", "tree", "harakeke"]},
                 active_hours=DIURNAL, season_curve=[0.9, 0.7, 0.5, 0.4, 0.5, 0.6, 0.8, 1.0, 1.0, 1.0, 0.9, 1.0],
                 weather_gate={"rain": 0.7, "wind": 0.6, "storm": 0.1, "frost": 0.9},
                 sound=("tui_song",), sings_at=("dawn", "day"), count=("one", "two", "three or four"), lifespan_y=12, ease=0.7, days_about=0.8,
                 diet=("nectar", "berries", "insects"), traces=(),
                 hidden={"feature": {"day": "a heavy dark bird with a white tuft at its throat bosses the flowering branch, chasing off another between mouthfuls"},
                         "absent": {"chance": "No tūī in the tree just now; when the kōwhai or the big tree flowers they will be back.",
                                    "weather": "The tūī keep out of this wind."}},
                 note="grandfathered; peaks at kōwhai (Aug–Oct) and pōhutukawa (Dec) flowering"))
    R.append(row("bellbird", aliases=("bellbird", "korimako"), audition="bellbird_song",
                 places={"garden": ["kowhai", "tree"], "wood": ["canopy"]},
                 active_hours=DIURNAL, season_curve=[0.6, 0.5, 0.4, 0.4, 0.5, 0.6, 0.8, 1.0, 1.0, 0.9, 0.8, 0.9],
                 weather_gate=SMALL_BIRD_WEATHER, sound=("bellbird_song",), sings_at=("dawn",), count=("one", "one", "two"), lifespan_y=8, ease=0.35,
                 diet=("nectar", "insects"),
                 hidden={"species": "bellbird", "book_names": ("bellbird", "korimako", "makomako"), "book_words": ("bell", "chime", "notes", "nectar", "song", "honeyeater"),
                         "feature": {"day": "a small olive-green bird, quick and shy, works the flowers with a curved bill and is gone before you have it properly"},
                         "reveal": "— a bellbird, the korimako; the chiming you hear at first light is this bird's.",
                         "miss": "Something small and green moved in the flowers and did not wait to be looked at.",
                         "absent": {"chance": "Nothing works the flowers just now.", "weather": "Nothing small stays out in this."}},
                 note="HIDDEN TRUTH; species reveal via sight + book. Sound point registered 2026-09-03 (J-0515/F-0697): bellbird_song in soundscape._SOUNDS + sound_knowledge.AUDITION, garden/wood voice lines added to the pickers"))
    R.append(row("tauhou", name="the tauhou", aliases=("tauhou", "silvereye", "silvereyes", "waxeye", "waxeyes"),
                 places={"garden": ["hedge", "tree"]},
                 active_hours=DIURNAL, season_curve=WINTER_FLOCK, weather_gate=SMALL_BIRD_WEATHER,
                 # J-2477 (sound_world_expansion §4, D-0500): silvereye_flock is the flock's OWN voice -- soft contact cheeps
                 # from many throats as the winter flock works the hedge -- bound here so life.sounds_active decides when it
                 # can sound (present, awake, in season). The BIRD stays grandfathered by sight; the SOUND arrives unnamed
                 # through sound_knowledge.AUDITION until he looks at the hedge and sees the flock on it (easily sighted).
                 sound=("small_birds", "silvereye_flock"), count=("a few", "a flock", "a big loose flock"), lifespan_y=3, ease=0.7,
                 diet=("insects", "berries", "seed"), responds_to_du={"feed_birds": 0.7},
                 hidden={"feature": {"day": "a loose flock of small grey-green birds with white eye-rings works through the hedge end to end and leaves the way it came"},
                         "absent": {"season": "No tauhou now; the flocks come through in the cold months.", "chance": "The hedge is quiet; the flock has moved on down the fence line."}},
                 note="grandfathered ('tauhou' in world_content_garden); winter flocks; silvereye_flock sound point added 2026-10-28 (J-2477)"))
    R.append(row("riroriro", aliases=("riroriro", "grey warbler", "warbler"), audition="riroriro_trill",
                 places={"garden": ["hedge"], "wood": ["canopy"]},
                 active_hours=DIURNAL, season_curve=RESIDENT, weather_gate=SMALL_BIRD_WEATHER,
                 sound=("riroriro_trill",), sings_at=("dawn", "day"), count=("one", "one", "a pair"), lifespan_y=5, ease=0.15,
                 diet=("insects",), eaten_by=("cat",),
                 hidden={"feature": {"day": "a tiny grey bird, hardly more than a movement, high in the hedge — the long falling trill is its"},
                         "miss": "The trill comes from the hedge again; whatever makes it stays a movement, not a shape.",
                         # J-1006 (F-1250/J-0892 precedent): the flat line names the garden's own spot
                         # (hedge); the wood's own registered spot (canopy) gets a parallel line.
                         "absent": {"wood": {"chance": "The canopy is quiet just now."}, "chance": "The hedge is quiet just now."}},
                 note="named by the audition ledger; heard far more than seen (ease 0.15)"))
    R.append(row("fantail", aliases=("fantail", "piwakawaka", "pīwakawaka"), audition="fantail_chatter",
                 places={"garden": ["bed", "hedge"], "wood": ["path", "undergrowth"]},
                 active_hours=DIURNAL, season_curve=RESIDENT, weather_gate=SMALL_BIRD_WEATHER,
                 sound=("fantail_chatter",), count=("one", "one", "a pair"), lifespan_y=3, ease=0.85,
                 diet=("insects",), eaten_by=("cat",), responds_to_du={"dig": 0.6, "walk": 0.5},
                 hidden={"feature": {"day": "a small bird with its tail spread like a fan loops almost at your shoulder, snapping at the air your feet stirred"},
                         "miss": "The chatter moved again — a flicker at the edge of sight.", "absent": {"chance": "Nothing follows your feet just now."}},
                 note="named by the audition ledger; follows whatever his feet stir"))
    R.append(row("kingfisher", aliases=("kingfisher", "kotare", "kōtare"), audition="kingfisher_call",
                 places={"garden": ["fence_post", "wire"], "shore": ["cliff"]},
                 active_hours=DIURNAL, season_curve=[1.0, 1.0, 0.9, 0.8, 0.8, 0.8, 0.8, 0.9, 1.0, 1.0, 1.0, 1.0],
                 weather_gate={"rain": 0.6, "wind": 0.7, "storm": 0.1, "frost": 0.9},
                 sound=("kingfisher_call",), count=("one", "one", "a pair"), lifespan_y=6, ease=0.6, days_about={"garden": 0.5},
                 diet=("whitebait", "crabs", "lizards", "insects"), traces=("a burrow in the cliff bank",),
                 # F-1801/J-1281 (Travis-approved via /decide-review, 2026-09-23): the burrow is a
                 # real shore-only nesting site; the garden's own kingfisher spots (post, wire) are
                 # a hunting perch, not a nesting site, and this trace was firing there falsely (4
                 # real mismatched rows). Restrict to shore -- she still shows/sounds in the garden
                 # via the ordinary living-row roll, just no separate ground-trace find there.
                 traces_only_at={"a burrow in the cliff bank": ("shore",)},
                 hidden={"feature": {"day": "a stocky bird sits sentry on the post, blue-green back flaring when it turns, and drops away toward the shore"},
                         "miss": "The dry rattle came from the wire, and the wire is empty.",
                         # J-1216 (D-0254/F-1706, confirmed fire, the founder's own named example): the
                         # feature/miss lines above name the garden's own spots (post, wire) and misrender
                         # at the shore, this row's other registered place (cliff) -- same J-1006 precedent
                         # as the "absent" override below, now extended to the feature/miss lines
                         # themselves. F-1706's own drafted wording, verbatim.
                         "feature_by_place": {"shore": {"day": "a stocky bird sits sentry on the cliff edge, blue-green back flaring when it turns, and drops away toward the water"}},
                         "miss_by_place": {"shore": "The dry rattle came from the cliff, and the cliff face is empty."},
                         # J-1006 (F-1250/J-0892 precedent): the flat line names the garden's own spots
                         # (post, wire); the shore's own registered spot (cliff) gets a parallel line.
                         "absent": {"shore": {"chance": "No kingfisher on the cliff just now."}, "chance": "The post and the wire are empty."}},
                 note="named by the audition ledger"))
    R.append(row("starlings", name="the starlings", plural=True, aliases=("starling", "starlings"),
                 places={"garden": ["powerline", "lawn", "ti_kouka"]},
                 active_hours=DIURNAL, season_curve=[0.7, 0.8, 1.0, 1.0, 0.8, 0.6, 0.6, 0.8, 1.0, 0.9, 0.7, 0.7],
                 weather_gate={"rain": 0.8, "wind": 0.6, "storm": 0.1, "frost": 0.9},
                 sound=("small_birds",), count=("a few", "a dozen", "a whole line of them"), lifespan_y=4, ease=0.8, days_about=0.6,
                 diet=("grubs", "insects", "fruit"), responds_to_du={"mow": 0.5},
                 hidden={"feature": {"day": "the starlings sit spaced along the powerline, all arguing, and lift off it in one motion so the wire swings empty",
                                     "dusk": "the starlings gather on the wire in the evening, more each week"},
                         "absent": {"chance": "The wire is empty just now."}},
                 note="grandfathered; autumn evening gatherings, spring prospecting of the tī kōuka head"))
    R.append(row("house_sparrows", name="the sparrows", plural=True, aliases=("sparrow", "sparrows"),
                 places={"garden": ["doorstep", "fence", "hedge"]},
                 active_hours=DIURNAL, season_curve=RESIDENT, weather_gate=SMALL_BIRD_WEATHER,
                 sound=("small_birds",), count=("a few", "a squabble of them", "a whole flock"), lifespan_y=3, ease=0.9,
                 diet=("seed", "crumbs", "insects"), eaten_by=("cat",), responds_to_du={"feed_birds": 0.9},
                 hidden={"feature": {"day": "sparrows squabble along the fence and drop to the doorstep for anything you have let fall",
                                     "summer": "young sparrows beg along the fence, wings shivering, mouths wide"},
                         "absent": {"chance": "The doorstep is empty of sparrows for once; they are somewhere down the hedge."}},
                 note="grandfathered; the feed_birds hand's first takers"))
    R.append(row("welcome_swallows", name="the swallows", plural=True, aliases=("swallow", "swallows"),
                 places={"garden": ["lawn", "sky"], "study": ["eaves"], "shore": ["sky"]},
                 active_hours={"dawn": 0.6, "day": 1.0, "dusk": 1.0, "night": 0.0},
                 season_curve=[1.0, 1.0, 0.8, 0.5, 0.3, 0.2, 0.2, 0.3, 0.6, 0.9, 1.0, 1.0],
                 weather_gate={"rain": 0.5, "wind": 0.6, "storm": 0.05, "frost": 0.6},
                 sound=(), count=("a pair", "a few", "a dozen"), lifespan_y=4, ease=0.75,
                 diet=("flying insects",), traces=("a mud nest under the eaves",),
                 # F-1801/J-1281 (Travis-approved via /decide-review, 2026-09-23): the mud nest is
                 # study-only (the cottage's own eaves) -- garden and shore have no eaves, and this
                 # was this plan's single biggest place-mismatch (20 of 39 real mismatched rows
                 # plan-wide). Restricted to study rather than inventing a new garden/shore feature
                 # (e.g. a porch rail) that isn't established anywhere else in the world; swallows
                 # still show via their own flight sightings over the garden/shore, just leave no
                 # findable ground trace there.
                 traces_only_at={"a mud nest under the eaves": ("study",)},
                 hidden={"feature": {"day": "swallows cut low over the lawn on stiff wings, turning on nothing, taking insects out of the air",
                                     "dusk": "the swallows work the evening air over the grass in long fast curves and tight turns"},
                         # J-1006 (F-1250/J-0892 precedent): the flat "chance" line is garden-worded (the
                         # lawn); this row has TWO other registered places, each with its own override
                         # naming only its own registered spot -- study's eaves (ties to this row's own
                         # "a mud nest under the eaves" trace) and shore's sky.
                         "absent": {"study": {"chance": "No swallows at the eaves just now."},
                                    "shore": {"chance": "The sky over the shore is empty of swallows just now."},
                                    "season": "No swallows over the lawn in the cold months.", "chance": "The air over the lawn is empty of swallows just now."}},
                 note="grandfathered; summer thickening, a nest under the study eaves (J-0513)"))
    R.append(row("shining_cuckoo", aliases=("cuckoo", "shining cuckoo", "pipiwharauroa", "pīpīwharauroa"), audition="cuckoo_call",
                 places={"garden": ["kowhai", "hedge", "tree"], "wood": ["canopy"]},
                 active_hours=DIURNAL, season_curve=SUMMER_VISITOR, weather_gate=SMALL_BIRD_WEATHER,
                 sound=("cuckoo_call",), sings_at=("dawn", "day"), count=("one", "one", "two"), lifespan_y=6, ease=0.2,
                 diet=("caterpillars",), traces=(),
                 hidden={"feature": {"day": "a small bird, green above with barred white below, keeps to the leaves and will not be looked at straight — the rising whistle is its"},
                         "miss": "The whistle came again from the leaves and nothing moved that you could name.",
                         "absent": {"season": "Nothing of that voice now; it comes with the spring and leaves before the cold.", "chance": "The trees hold no such voice just now."}},
                 note="HIDDEN TRUTH; October arrival, parasitises the riroriro's nest (J-0513 interaction); named by the audition ledger"))
    R.append(row("kereru", name="the wood pigeon", aliases=("wood pigeon", "kereru", "kererū", "pigeon"), audition="kereru_wingbeats",
                 places={"garden": ["kowhai", "tree"], "wood": ["oak", "canopy"]},
                 active_hours=DIURNAL, season_curve=RESIDENT, weather_gate={"rain": 0.8, "wind": 0.6, "storm": 0.1, "frost": 0.9},
                 sound=("wood_pigeon", "kereru_wingbeats"), count=("one", "one", "a pair"), lifespan_y=15, ease=0.7, nest="kereru_nest", days_about={"garden": 0.4},
                 diet=("leaves", "berries", "kowhai buds"), traces=("a big soft feather", "droppings under the oak"),
                 hidden={"feature": {"day": "a big heavy pigeon, white breast and iridescent green-purple back, sits stock still on a branch and lets you look"},
                         # J-1030 (F-1250/J-0892/J-1006 precedent): the REVERSE direction from most of
                         # this pattern's fixes -- the flat "chance" line below is already WOOD-worded
                         # ("the canopy" is wood's own registered spot, not garden's kowhai/tree) and was
                         # rendering unchanged in the garden too. A per-place override gives the garden
                         # its own feature-first line naming its own registered kowhai; the wood's flat
                         # line (and every other line on this row) is untouched.
                         "absent": {"garden": {"chance": "No wood pigeon on its branch; the kowhai holds only small birds."},
                                    "chance": "No wood pigeon on its branch; the canopy holds only small birds."}},
                 note="grandfathered ('the wood pigeon' — soundscape); the whoosh of its wingbeats is a learnable voice"))
    R.append(row("morepork", name="the morepork", aliases=("morepork", "ruru", "owl"),
                 places={"wood": ["canopy"], "garden": ["tree"]},
                 active_hours=NOCTURNAL, season_curve=RESIDENT, weather_gate={"rain": 0.5, "wind": 0.6, "storm": 0.05, "frost": 0.9},
                 light="indifferent", eyeshine=True, sound=("morepork_call",), sings_at=("night", "dusk"),
                 count=("one", "one", "a pair"), lifespan_y=10, ease=0.25,
                 diet=("moths", "weta", "mice", "small birds"), traces=("pellets", "a feather"),
                 hidden={"feature": {"night": "a shape on a branch against the lesser dark of the sky, round-headed, that turns its face to you and does not move",
                                     "dusk": "a silent shape crosses between the trees at head height and is gone into the canopy"},
                         # J-1216 (D-0254/F-1706): the dusk line above names "the canopy" -- wood's own
                         # registered spot (world_content_wood.py carries a whole "canopy" place entry;
                         # the word never appears in world_content_garden.py) -- and misrenders in the
                         # garden, this row's other registered place ("tree", not "canopy": the exact
                         # distinction J-1030's absent-line override below already draws for this SAME
                         # row). F-1706 logged this pair borderline and drafted no replacement, flagging
                         # "Travis's own read" on whether the historical fire even was this line; read
                         # directly, data/life_events.jsonl line 2635 (ts 1789628298.3) settles it --
                         # "phase": "dusk" and "line": "a silent shape crosses between the trees at head
                         # height and is gone into the canopy" logged verbatim, so the one recorded
                         # garden sighting IS this line, confirmed rather than inferred: the
                         # phase-uncertainty D-0254 named resolves real. feature_by_place carries the
                         # (unchanged) "night" text forward too, since feature_by_place[place] replaces
                         # this row's flat feature dict wholesale for "garden" rather than merging key by
                         # key -- omitting "night" here would silently blank the night line for
                         # morepork/garden. No F-1706 draft existed for the dusk replacement itself
                         # (explicitly left to "Travis's own read", not drafted); the wording below is a
                         # fresh draft in the row's own established voice for this place (echoing "the
                         # tree" from this same row's eyeshine and absent/garden lines), not F-1706's own
                         # text -- flagged for review in J-1216's own report.
                         "feature_by_place": {"garden": {"night": "a shape on a branch against the lesser dark of the sky, round-headed, that turns its face to you and does not move",
                                                          "dusk": "a silent shape crosses the garden at head height and is gone into the tree"}},
                         "eyeshine": "two points of light low in the tree, wide apart, that do not blink — and then they are gone",
                         "miss": "The call comes again from further along; you cannot find the shape it belongs to.",
                         # J-1030 (F-1250/J-0892/J-1006 precedent): same reverse direction as kereru
                         # above -- the flat "chance" line is wood-worded ("the canopy" is wood's own
                         # spot; the garden's is "tree") and was rendering unchanged in the garden too.
                         "absent": {"garden": {"chance": "The tree is quiet; nothing shows against the sky."},
                                    "day": "Nothing in the trees by day but small birds; the night's voice is asleep somewhere in the canopy.",
                                    "weather": "Not in this wind — nothing hunts on a night like it.", "chance": "The canopy is quiet; nothing shows against the sky."}},
                 note="grandfathered; night, eye-shine in a carried light (moved here from life.py's reference rows)"))
    # ── SHORE ──────────────────────────────────────────────────────────────────────────────────
    R.append(row("oystercatcher", name="the oystercatcher", aliases=("oystercatcher", "oystercatchers", "torea", "tōrea"),
                 places={"shore": ["shingle", "tideline", "rocks"]},
                 active_hours={"dawn": 1.0, "day": 1.0, "dusk": 0.9, "night": 0.3}, season_curve=RESIDENT, weather_gate=SEABIRD_WEATHER,
                 sound=("oystercatcher_call",), count=("one", "a pair", "a pair and a third"), lifespan_y=25, ease=0.9, nest="oystercatcher_nest",
                 diet=("shellfish", "worms", "crabs"), eaten_by=("karoro",), traces=("three-toed prints on the wet sand", "opened shells"),
                 hidden={"feature": {"day": "the oystercatcher stands on the wet stones on two red legs, orange bill down, and screams at you for coming too close",
                                     "night": "a piping in the dark along the tideline and a pale shape that runs, stops, runs"},
                         "absent": {"weather": "The tideline is empty of the pair in this; they will be tucked in behind the rocks.",
                                    "chance": "The pair are not on the shingle just now — further along the tide's edge, out of sight."}},
                 note="grandfathered; the pair; the nest scrape on the shingle is shore_life's oyc_nest"))
    # J-1174 (D-0166 re-ruled 2026-09-21, F-1614): THE GULLS KEEP THE DAY. "night" was 0.2 -- just above the 0.15 PRESENT_AT floor --
    # so the row was present on most clear September nights (day_factor >= 0.75: 71% in expectation, 19 of 30 in a probe), and
    # core/soundscape.py rolls a present voice at its flat per-hour rate whatever its activity (gull_cries 40/h): the shore's night
    # carried the daytime cry (about 31% of the gull cries Du heard since the flip were night cries; the legacy `if day` rule gave
    # none). 0.1 is under the floor for EVERY weather and every day: activity = 0.1 x day_factor (< 1.25) x weather (<= 1) x
    # _gulls_inland (<= 1), so < 0.125 < 0.15 -- never present at night -- and 0.1 is the value dolphins / godwits / whitebait already
    # use for "not here by night". Dawn 0.9, day 1.0 and dusk 0.8 are unchanged (present at the shore in every weather: at the very
    # least 0.8 x 0.55 x 0.4 = 0.176). The night look is then the generic plural template, "Not by night; the gulls keep the day."
    # (_absent_line: active_hours[night] < 0.15 and no hidden.absent.night line).
    R.append(row("gulls", name="the gulls", plural=True, aliases=("gull", "gulls", "seagull", "seagulls", "red-billed gull"),
                 places={"shore": ["tideline", "rocks", "sky"], "garden": ["sky", "fence"]},
                 active_hours={"dawn": 0.9, "day": 1.0, "dusk": 0.8, "night": 0.1}, season_curve=RESIDENT, weather_gate=SEABIRD_WEATHER,
                 sound=("gull_cries",), count=("a few", "a dozen", "a working flock"), lifespan_y=10, ease=0.95, scale=_gulls_inland,
                 diet=("fish", "crabs", "anything"), traces=("prints", "a white feather", "a dropped shell"),
                 hidden={"feature": {"day": "small grey-and-white gulls with red bills and legs work the tideline, squabbling over what the tide left"},
                         # F-1250/J-0892 (2026-09-14): the flat "chance" line below is shore-worded ("the
                         # tideline") and was rendering in the garden too (08:55 09-11, garden activity 0.145
                         # correctly under the 0.15 floor -- a wording nit, not a presence error). A per-place
                         # override, tried before the flat form by _absent_line() (core/life.py), gives the
                         # garden its own feature-first line without touching the shore's; every other row's
                         # flat "absent" dict is untouched and behaves byte-identically.
                         "absent": {"garden": {"chance": "No gull over the garden just now; the sky above the fence is empty."},
                                    "chance": "The gulls are out over the water for once; the tideline is quiet."}},
                 note="grandfathered; the small red-billed gull — the big black-backed one is the karoro"))
    # J-1174 (F-1614's mechanism read again): the karoro carries the SAME voice key as the gulls (sound=("gull_cries",)) and life.sounds_active
    # adds a present row's sound keys with no phase restriction, so with the karoro's night at 0.3 (present on every September night in
    # clear weather: 0.3 x 0.55 = 0.165 >= 0.15) the gull_cries voice stayed in the night shore's active set even on the nights the gulls
    # themselves were absent (probe: 30 of 30 September nights, gulls present on 19 of them). Lowering only the gulls row would have left
    # the ruling's outcome -- a night shore with no gull_cries -- undone. The big gull keeps the day the same way, same value, same reason.
    R.append(row("karoro", name="the karoro", aliases=("karoro", "black-backed gull", "black-back", "big gull"),
                 places={"shore": ["tideline", "rocks"]},
                 active_hours={"dawn": 0.9, "day": 1.0, "dusk": 0.8, "night": 0.1}, season_curve=RESIDENT, weather_gate=SEABIRD_WEATHER,
                 sound=("gull_cries",), count=("one", "a few", "a spaced line of them"), lifespan_y=15, ease=0.95,
                 # F-1244/J-0887: "a dead gannet picked clean" removed from this row's OWN traces (2026-09-11)
                 # -- it was a second, bypassing dead-gannet source that world_traces could hold with no
                 # matching `carcasses` state row, so a look at "the dead gannet" could find nothing in life
                 # state and fall through to the LIVING gannet row (mechanism A's own bug). GANNET_STORM_P
                 # (below) is now the one source of a real gannet carcass; the karoro's picking of it is
                 # still true (carcass_look's own "picked" line names "the karoro's work, or the cat's").
                 diet=("fish", "carrion", "eggs", "chicks"), traces=("big prints",),
                 hidden={"feature": {"day": "the big black-backs stand spaced along the tide's edge, all facing the wind, and lift one at a time as you come"},
                         "absent": {"chance": "No karoro on the tideline just now."}},
                 note="grandfathered (world_content_shore); the shore's scavenger — the dead gannet is its work (J-0513)"))
    R.append(row("terns", name="the terns", plural=True, aliases=("tern", "terns", "tara", "white-fronted tern"),
                 places={"shore": ["sky", "surf", "rocks"]},
                 active_hours=DIURNAL, season_curve=SUMMER_VISITOR, weather_gate={"rain": 0.7, "wind": 0.8, "storm": 0.2, "frost": 1.0},
                 sound=(), count=("a few", "a dozen", "a working flock"), lifespan_y=10, ease=0.8,
                 diet=("small fish",),
                 hidden={"feature": {"day": "the terns hover on beating wings over the surf, fold, and drop into it white and clean"},
                         "absent": {"season": "No terns over the surf now; they are a summer shore.", "weather": "The terns have given up the hover and gone downwind."}},
                 note="grandfathered ('terns', 'tara' in world_content_shore); summer"))
    R.append(row("gannet", name="the gannets", plural=True, aliases=("gannet", "gannets", "takapu", "tākapu"),
                 places={"shore": ["sky", "offshore"]},
                 active_hours=DIURNAL, season_curve=[1.0, 1.0, 0.9, 0.7, 0.6, 0.6, 0.6, 0.7, 0.9, 1.0, 1.0, 1.0], weather_gate=SEABIRD_WEATHER,
                 sound=(), count=("one", "a few", "several, working a patch"), lifespan_y=20, ease=0.7,
                 # F-1244/J-0887 (2026-09-11): "a dead gannet on the tideline" removed from this row's OWN
                 # traces -- it was a second, bypassing dead-gannet source (a world_traces trace with no
                 # matching `carcasses` state row), so "the dead gannet" could find nothing in life state
                 # and fall through to THIS row's own visibility roll -- 89s after the engine minted that
                 # very trace (mechanism A's own bug, live 2026-09-10 06:24 and 09-11 07:34/16:56). Checked
                 # before removing: the "observed 12x" pre-engine dead gannet (docs/reviews/observe_inventory
                 # _2026-09-02.md) predates this row by a day (life_birds.py is J-0511, 09-03) and comes from
                 # core/sensorium.py's own separate ambient lines (:947 the shore-look "rare" pool, :2189
                 # the storm-wrack list) -- untouched by this removal, so nothing Du already believes in is
                 # stranded. GANNET_STORM_P (life_traces.py) is now the ONE source of a real gannet carcass.
                 diet=("fish",), traces=("a gannet feather, white and stiff",),
                 hidden={"feature": {"day": "a gannet folds and drops like a thrown knife, and the water takes it white"},
                         "absent": {"chance": "Nothing is diving offshore just now; the water is empty out to the horizon."}},
                 note="grandfathered; offshore all year; the dead one on the tideline (observed 12x) is a J-0513 carcass"))
    R.append(row("shag", aliases=("shag", "shags", "cormorant", "kawau"), audition="shag_wingbeats",
                 places={"shore": ["rocks", "water"]},
                 active_hours=DIURNAL, season_curve=RESIDENT, weather_gate=SEABIRD_WEATHER,
                 sound=("shag_wingbeats",), count=("one", "one", "two"), lifespan_y=10, ease=0.8,
                 diet=("fish",), traces=("white-streaked rock",),
                 hidden={"feature": {"day": "a black shag stands on the rock with its wings held out to dry, like something hung up"},
                         "miss": "The heavy wingbeats went by low over the water and the bird was gone round the point.",
                         "absent": {"chance": "The drying rock is empty."}},
                 note="named by the audition ledger"))
    R.append(row("reef_heron", aliases=("heron", "reef heron", "matuku"),
                 places={"shore": ["rock_pools", "tideline"]},
                 active_hours={"dawn": 1.0, "day": 0.8, "dusk": 1.0, "night": 0.3}, season_curve=RESIDENT, weather_gate={"rain": 0.9, "wind": 0.7, "storm": 0.2, "frost": 1.0},
                 sound=(), count=("one", "one", "one"), lifespan_y=15, ease=0.5, tide="low",
                 diet=("small fish", "crabs"),
                 hidden={"species": "reef heron", "book_names": ("reef heron", "heron", "matuku"), "book_words": ("wading", "stalks", "pools", "grey", "neck", "still"),
                         "feature": {"day": "a tall slate-grey bird stands motionless in the rock-pool, neck drawn in, then strikes and swallows"},
                         "reveal": "— a reef heron; it hunts the pools at low water.",
                         "miss": "Something grey and tall stood in the pools a moment ago and has folded itself into the rocks.",
                         "absent": {"chance": "The pools are empty of anything tall and grey.", "weather": "Nothing hunts the pools in this."}},
                 note="HIDDEN TRUTH; low tide"))
    R.append(row("stilt", aliases=("stilt", "stilts", "poaka"),
                 places={"shore": ["stream_mouth"]},
                 active_hours=DIURNAL, season_curve=[0.6, 0.6, 0.7, 0.8, 0.9, 1.0, 1.0, 0.9, 0.7, 0.6, 0.5, 0.5], weather_gate=SEABIRD_WEATHER,
                 sound=(), count=("one", "a pair", "a few"), lifespan_y=10, ease=0.6,
                 diet=("worms", "insects"),
                 hidden={"species": "pied stilt", "book_names": ("pied stilt", "stilt", "poaka"), "book_words": ("legs", "pink", "wading", "yapping", "black and white"),
                         "feature": {"day": "a black-and-white wader on absurdly long pink legs picks along the stream mouth and yaps at you"},
                         "reveal": "— a pied stilt.", "miss": "Whatever was yapping at the stream mouth has walked off round the bend.",
                         "absent": {"chance": "The stream mouth holds no waders just now."}},
                 note="HIDDEN TRUTH; the stream mouth only (D-0132: no estuary)"))
    R.append(row("korora", aliases=("penguin", "penguins", "korora", "kororā"), audition="penguin_bray",
                 places={"shore": ["cliff_foot", "shingle"]},
                 active_hours={"dawn": 0.3, "day": 0.0, "dusk": 1.0, "night": 1.0}, season_curve=KORORA_ASHORE,
                 weather_gate={"rain": 0.9, "wind": 0.8, "storm": 0.3, "frost": 1.0},
                 light="avoids", sound=("penguin_bray",), count=("one", "a few", "several, coming ashore"), lifespan_y=7, ease=0.5,
                 diet=("small fish",), traces=("a burrow under the cliff", "a fishy smell at the burrow mouth"),
                 hidden={"feature": {"night": "a small upright shape, blue-grey, white-fronted, hurries on short legs across the shingle toward the rocks",
                                     "dusk": "something small and upright comes out of the surf and stands, then sets off up the shingle at a waddle"},
                         "miss": "A scuffle on the stones under the cliff, no more.",
                         "absent": {"season": "Nothing comes ashore under the cliff at this time of year.", "day": "Nothing of that by day; whatever burrows under the cliff is out at sea."}},
                 note="named by the audition ledger (was life.py's external adapter); ashore at dusk Sep–Feb"))
    R.append(row("godwits", aliases=("godwit", "godwits", "kuaka"), audition="godwits_overhead",
                 places={"shore": ["sky"], "garden": ["sky"]},
                 active_hours={"dawn": 0.8, "day": 1.0, "dusk": 0.8, "night": 0.1}, season_curve=SEPT_PASSAGE,
                 weather_gate={"rain": 0.6, "wind": 0.9, "storm": 0.2, "frost": 1.0},
                 sound=("godwits_overhead",), count=("a line", "a long line", "skein after skein"), lifespan_y=20, ease=0.3, scale=_passage_day,
                 diet=(), traces=(),
                 hidden={"feature": {"day": "high up, a long wavering line of birds heading south along the coast, calling as they go — too high to be anything but a line",
                                     "dusk": "against the last light a line of birds crosses high and fast, calling, and is gone down the coast"},
                         "miss": "The calling passed over and by the time you found the sky it was empty.",
                         "absent": {"season": "Nothing passes over now; the long lines come with the spring.", "chance": "The sky is empty of any line."}},
                 note="HIDDEN TRUTH; D-0132: overhead only — September–October south, a March return; named by the audition ledger"))
    # ── WOOD ───────────────────────────────────────────────────────────────────────────────────
    R.append(row("robin", aliases=("robin", "toutouwai"), audition="robin_song",
                 places={"wood": ["path", "undergrowth"]},
                 active_hours=DIURNAL, season_curve=RESIDENT, weather_gate=SMALL_BIRD_WEATHER,
                 sound=("robin_song",), sings_at=("dawn", "day"), count=("one", "one", "a pair"), lifespan_y=6, ease=0.8,
                 diet=("insects", "worms"), responds_to_du={"walk": 0.6, "dig": 0.7},
                 hidden={"feature": {"day": "a dark, long-legged little bird drops onto the path a yard from your boots and looks at you, unbothered"},
                         "miss": "The clear little phrases came from a low perch close by, and the perch was empty when you found it.",
                         "absent": {"chance": "The path is empty; nothing comes to your feet just now."}},
                 note="named by the audition ledger; comes to turned earth and to his feet"))
    R.append(row("wren", name="the wren", aliases=("wren", "rifleman", "titipounamu"),
                 places={"wood": ["undergrowth", "trunks"]},
                 active_hours=DIURNAL, season_curve=RESIDENT, weather_gate=SMALL_BIRD_WEATHER,
                 sound=("wren_scold",), count=("one", "a pair", "a pair"), lifespan_y=3, ease=0.3,
                 diet=("insects",),
                 hidden={"feature": {"day": "a bird so small it is hardly a bird works up a trunk in jerks, scolding out of all proportion to its size"},
                         "absent": {"chance": "The trunks are quiet; the scold has stopped."}},
                 note="grandfathered ('the wren' — soundscape)"))
    return R


# adapters over nests that already exist as stage machines (behaviour untouched)
def nest_adapters():
    from core.life import _nest_presence

    def _oyc(now: float) -> dict:
        try:
            from core import shore_life as _shl
            return {"shore": 1.0} if _shl._load().get("oyc_nest") else {}
        except Exception:
            return {}
    # D-0345 / J-1774 (F-2382): the nest-object gate (life_traces.nest_object_shape -- SHADOW ONLY, it changes no answer) derives a nest's nouns
    # from these rows: the head of the name ('scrape', 'nest') and the tail of the key ('nest'). `nest_nouns` is the one data field for the word
    # no row name holds -- the eggs -- the way a row carries `traces`.
    _eggs = ("egg", "eggs")
    return [
        row("blackbird_nest", kind="external", name="the blackbird's nest", places={"garden": ["bushes", "harakeke"]},
            external={"presence": _nest_presence("garden_life", "garden")}, nest_nouns=_eggs, note="garden_life nest stage machine"),
        row("kereru_nest", kind="external", name="the wood pigeon's nest", places={"wood": ["oak"]},
            external={"presence": _nest_presence("wood_life", "wood")}, nest_nouns=_eggs, note="wood_life nest stage machine"),
        row("oystercatcher_nest", kind="external", name="the oystercatchers' scrape", places={"shore": ["shingle"]},
            external={"presence": _oyc}, nest_nouns=_eggs, note="shore_life oyc_nest"),
    ]
