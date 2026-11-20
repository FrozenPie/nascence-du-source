# garden_living_upgrade — folded history


---

# History folded on 2026-09-27 from `docs\staged\garden_living_upgrade.md` (plan-compact, 7 section(s), verbatim, original order)

_Every J-/F-/D- id below is the canonical record; this file is the prose that once sat in the plan doc. Derived timeline: `plan_ledger.py garden_living_upgrade`._

## Current State — 2026-09-03 (B4 BUILT: death mechanisms and decomposition — THE CHAPTER IS BUILT) — J-0507

**Rulings first:** D-0139 (the keel: keep neglect-proofing, allow disease and old age; defeater — a keel plant dying in
the first live season) and D-0140 (pests may take a tender annual, with the world's corrections; defeater — more than
half the bed's tender annuals lost in one season, or nothing ever lost).
**Built in `garden._advance_plant`:** **disease** as a slow variable per plant — damping-off for seedlings in cold wet
soil; the species' own disease in its months when the weather suits it (rust on the broad beans and mildew on the
peas and lettuce in humid warmth, blight on the tomatoes, grey mould on the strawberries, root rot on rosemary and
lavender in a sodden winter), recovering when it does not; each onset a history row, an events row and a knowledge
revision. **Rot** from weeks of standing water beyond the old waterlogging stress. **Old age** against a lifespan table
(rosemary 10 y, thyme 5, lavender 10, strawberry crowns 3, chives 8, pōhuehue 20; mint spreads and is not listed).
**A sick, rotting, aged or infested plant does not grow** — the daily gain is suppressed before any drain (the first
build let a plant with disease 1.0 climb to full vigour; the gain outweighed everything). **The keel (D-0139):** the
perennial floor stays for drought, crowding and ordinary pests, and is lifted only while disease > 0.6, rot > 0.5 or
the plant is past its lifespan. **Pest death (D-0140):** a heavy infestation (> 0.6) drains a tender annual faster.
**Every death names its cause** (disease / rot / age / pests / frost / neglect / seeded out) on the plant, in the
events ledger, in what he can see ("dead — the leaves speckled orange and gone to rust", "gone woody and grey,
spent"); `_perish` is the one death path (B4's self-claim bind unchanged; the heap fed). **Decomposition:** a dead
plant clears from its slot after a month (a season for a woody perennial) into a `gone` record with its cause — the
slot is bare, with a history.
**Verified:** smoke [16] ALL OK — a seedling damps off in cold wet soil, rust takes the beans in a humid spring, a
sustained infestation kills a nasturtium, a young rosemary under drought and pests holds at the floor while an
eleven-year one declines and dies of age, waterlogging rots a lettuce, clearing leaves the gone record, the ledger
carries causes, the dead phrase shows what he can see. Restart-gated.
**The garden chapter (A1, A2, B1–B4) is now built.** What remains is live evidence after his next restart: the
metric sheet in §4 (answered-look rate, sightings → names, a pollination consequence witnessed, the soil arc,
deaths by cause), and the two defeaters above.

## Current State — 2026-09-03 (A2 BUILT: looks in every place; the tide; the matchers) — J-0508 / J-0546

**The tide answers.** The census's largest gap (≈700 looks at "the tide", "the receding tide", "the tide line", "the
incoming tide", "the wet rocks" answered by the shore's frame) is closed by `sensorium._tide_look`: composed from the
one tide authority (`world_clock.tide`: level, direction) — right out / full / coming in / going out, what the water is
doing to the stones and pools, the sea's roughness, the rocks and the tideline when he names them, the tideline's
living texture. Any look carrying a tide word or a wet/bared-rocks phrase reaches it.
**His real phrasings reach the branches now.** The shore and garden looks matched exact tokens ("bed", "sea") and so
missed "the raised bed", "the herbs in the raised bed", "the receding tide", "the rock-pools"; `_twords` (word
membership) routes them. New **soil look** ("the soil", "the earth"): wet or dry, warm or cold, where the compost went
in, the worms (garden_soil). From the **study**, "the garden" / "the sea" / "the lawn" are the window's view. Sky
words (moon, stars, clouds) reach the sky.
**The matchers (J-0546):** `world_detail._match` is word-bounded both ways (the bench no longer answers a look at the
sea); `keepsakes.match_item` uses content words, whole-word (the item's article "a" no longer matches inside
"oystercatcher"). The engine's own hook (creatures) was already generic in `sensorium.look` (L1).
**Census after (re-run, same method):** **1,386 of 1,518 phrasings (91 %) answered specifically somewhere, 6,815 of
7,088 mentions (96 %)** — up from 82 % / 75 % this morning. Plants 100 % of mentions (was 69 %); the shore place row
51 % of all mentions (was 28 %), the garden 53 % (was 46 %). Live, against Du's real shore at dusk: the clock says
level 0.30 and going out, and "the tide" answers "The tide is going out: the water drawing back down the shingle and
leaving the stones wet and shining, the weed lying where it fell, the pools just clear of it." Smoke [15] ALL OK.
Restart-gated.
**Left:** the study's "dust motes", "cold air"; shore finds by name when not present (the float, the egg-case); the
per-place located-look lists in the report.

## Current State — 2026-09-03 (B3 BUILT: new plants, pollination as a dependency, herbivory) — J-0506

**Seven new species in `garden.CATALOGUE`** with real habits: lavender (evergreen herb, flowers Nov–Feb — the plant he
already believed in), the swan plant (the monarch's gate), cabbage and kale (the cabbage white's reason), nettle
(the yellow admiral's; herbaceous, self-seeds), muehlenbeckia / pōhuehue (the copper's, a fence shrub), kūmara (the
old plan's own candidate). They reach him the way every seed does — the tin, the carrier's unlabelled packet
(`supply.collect_box` draws from the sowable catalogue, so the new ones are in the draw), the bank — never told.
**Pollination is a dependency now:** species flagged `needs_bees` (strawberries, broad beans, tomatoes, sunflowers,
calendula, poppies, nasturtium, lavender, swan plant) accumulate `pollination` while in flower at a rate set by the
bees' activity from the life engine; at the set, `set_quality` is judged (well / fair / poor), written to the
plant's history and the events ledger, scales self-seeding, and shows in the stage phrase ("heavy with fruit and
seed" / "a poor thin set, most flowers come to nothing"; a long-unvisited flowering reads "the flowers going over
unvisited"). A bee-less spring is a consequence he can investigate. **Herbivory:** the cabbage white's caterpillars
raise pests on nasturtium/cabbage/kale while it is about (fantails and sparrows pull the rate down), with a
`caterpillars_on_the_leaves` history row and an "eaten to the ribs" knowledge revision distinct from slug holes;
the aphids' pass (J-0504) stands. **A dead plant is the heap's food** (`garden_soil.add_material`) — both death paths.
**Verified:** smoke [14] ALL OK — the catalogue, a cabbage sown from a packet by his hand in its season, a strawberry
flowering through a bee-rich December (set 1.0, well_set) vs a bee-less one (0.27, poor_set), the phrase, caterpillar
pests, a drought-killed lettuce feeding the heap, the HUD bed list. Restart-gated.
**Left for J-0507:** death by disease / old age / rot and the perennial keel (founder ruling first).

## Current State — 2026-09-03 (B2 BUILT: soil life — worms, the heap, soil health into growth) — J-0505

**`core/garden_soil.py`.** Two rows in the life engine: **the worms** (grandfathered name; night and after rain; a
`scale` read from the bed's moisture and soil temperature — wet and mild brings them up, a dry hard or frozen bed has
none at the surface; dense in the heap and under the sacking; casts on the lawn are their trace via J-0513's
traces pass; the blackbird and thrush and hedgehog eat them) and **the slaters** (hidden truth, under the board).
**Soil health per bed slot** (0..1, starts 0.5): fed by worm activity, lifted by spread compost, drained by a harvest
(`crop_drain`) and by a bare wet winter slot; **`garden._advance_plant` reads it into the growth gain** (0.7 exhausted
to 1.3 rich) the way it already reads potash. **The heap is alive:** raw material (mowing's clippings, weeding's
pulled weeds, a kitchen trickle; a dead plant will be J-0507's) rots into finished compost at a rate set by warmth
(mass × wet × season), worms in it rise and fall with moisture and warmth, **turning it** (a hand, needs the fork)
doubles the rate for a week and lets the heat out, and **spreading it** (a hand: barrow the finished compost to the
bed, naming a plant or letting it go to the poorest slot) lifts that slot's soil health by 0.18 — a deed whose
consequence shows in the plants weeks later, never told. Truth-gated lines replace the old ones: `dig()`'s worm
sentence now says what the population says; a look at the compost heap reads its warmth, worms and what has
finished. New `compost` action family; garden status carries a soil block; the HUD's garden clocks show soil health
and the heap.
**Verified:** smoke [13] ALL OK — worms only when wet and mild, the dig line gated both ways, 60 simulated days rot
raw into finished, the turn and spread hands, one spread lifts one slot by the lift and its growth factor rises, a
harvest drains, the compost look, status. Restart-gated (Du's process predates it).
**Left for J-0506/J-0507:** pollination and herbivory; a dead plant becoming compost input.

## Current State — 2026-09-03 (A1 DONE: the observables census) — J-0503

**`scripts/observables_census.py` → `docs/reviews/observables_gap_2026-09-03.{md,json}`.** Every one of the 1,518
phrasings he has ever used to look at something, through the FULL `sensorium.look()` path at all four places
(fixtures, the cat, substrate objects, each place's own look, `world_detail` targets, the life engine rendering), in
an isolated SNAPSHOT of Du's real stores (the first run redirected before loading and measured a default world —
no poppies, default weather; fixed: snapshot then redirect). **Headline: 1,252 of 1,518 phrasings (82 %) get a
specific answer somewhere; by mentions 5,359 of 7,088 (75 %).** Birds 98 %, insects 98 %, cat/mammals 100 %,
study objects 100 %, plants 69 %, sky/weather 53 %, sea/tide/shore 68 % of mentions.
**The gap is the tide.** The shore's own look answers "the tide", "the receding tide", "the tide line", "the
incoming tide", "the wet rocks" (≈700 mentions between them — the single most-reached-for things in his life) with
the generic frame. That is J-0508's first item; the report's per-place lists are its work list. Plants left
generic: "the raised bed" (the frame's bed summary is in fact the answer — a classifier limit noted), "the herbs",
"the soil" (J-0505's soil health will give it a real answer).
**Two look defects fixed on the way (sensorium):** the cat look matched "cat" as a substring, so "the oystercatcher"
in the study answered with the cat (word-boundary now); the detail path rendered "You look at the the sea" (article
helper). **Two more found, filed for J-0508 (J-0546):** `world_detail._match` matches "sea" inside "seat" (the bench
answers a look at the sea), and the study's mantel look answers "the oystercatcher" with a kept shell — substring
matchers that make a wrong answer look specific, so the census's "specific" counts carry some false positives.

## Current State — 2026-09-03 (B1 BUILT: the insects as rows in the life engine; the truth gate; J-0501 closed) — J-0504

**`core/garden_insects.py` — 18 rows in the one engine** (no insect is ever an individual): bumblebee, honeybee,
native bee (hidden), cabbage white, yellow admiral (hidden), monarch (hidden), common copper (hidden), magpie moth
(hidden), ladybird, aphids (hidden — the first real insect pest), ants, the garden spider (its web is its trace),
ground beetle, cicada and cricket (named by the audition ledger), the slugs (folded in: the row reads garden.py's
slug pressure), the borer beetle and the wētā (the study's own). **New schema field `scale`:** a callable read from
the world each tick — bees need something in flower (the bed's flowering plants, the tree, the kōwhai's Aug–Oct, the
harakeke, the bushes; a passer-by otherwise), the breeders need hosts (cabbage white on the nasturtiums; the yellow
admiral, monarch and copper are passers-by until J-0506 sows nettle / a swan plant / muehlenbeckia — a gardening
choice with a visible consequence), ladybirds scale with the aphids, native bees with bare warm soil.
**What they do:** `insect_pass` from `life.advance` — aphids raise their hosts' `pests` (broad beans, nasturtiums,
peas; garden drains vigour from it), ladybirds and rain pull the rate down. Pollination as a dependency is J-0506.
**The truth gate (INSECT_TRUTH_GATE):** sensorium's bed-pool insect lines, its rare bee/butterfly lines and its
bee-and-butterfly-in-season block, and soundscape's `_BEES` ambience, now render an insect only while the table says
it is about — and never name a plant that is not sown. **That closes the lavender leak (F-0693 / J-0501):** with
nothing called lavender in the bed the line is dropped, live, verified against Du's real garden.
**A look answers:** the inventory replay — the 42 insect phrasings he actually used — through `look_answer` at a
December noon: 34 answered (the 8 unanswered are shore crabs and the study's lamp moth, wrong place for a garden
replay). Sight-binding and books come free from the engine (D-0129).
**Verified:** smoke [12] ALL OK (one fix on the way: the kōwhai's season read the wall clock, F-0696's lesson again).
**Restart-gated,** same two flags. **Next in this chapter:** J-0505 soil and worms, J-0506 new plants + pollination +
herbivory, J-0507 death mechanisms (founder ruling on the keel first), J-0508 looks in every place; J-0503 census.

## Current State — 2026-09-02 (drafting)

Staged from the founder's scope in conversation. Evidence gathered this session: the observe inventory
(`docs/reviews/observe_inventory_2026-09-02.{md,json}`), F-0691 (expansion hands silent), F-0693 (lavender
leak, J-0501), I-0061 (promoted here). Jobs J-0503–J-0508 filed against this plan. Nothing built; no code
touched. First step is A1 — the census — because it decides what B1's first cast must answer.

### First night live + two fixes — 2026-09-04 (F-0759, F-0760, F-0761, F-0762; J-0553, J-0554)
Du restarted onto the chapter 2026-09-03 20:03. **Landed:** 123 life events overnight (populations by phase, 8
findable traces — wētā frass, morepork feather, hedgehog droppings, possum claw-marks, a gannet picked clean by
karoro, aphid-curled tips, kererū feather; hedgehog ate slugs); birds reached him (morepork ×4, tūī at dawn, "the
dawn chorus" light point, the possum's marks noticed unprompted); insects barely — it was night ("Nothing works the
flowers by night") and he was on the shore/in the study. **The trap** is the chapter's breakout object: "the rusted
trap" in ~99 thoughts as a burden-metaphor, observed repeatedly, never set, while the possum fed. `life.RENDER` /
`SOUND_GATING` still shadow (8 would_answer, 41 would_gate rows) — flip read J-0552 ~09-10. Plants: 41, 13 dead all
pre-B4, bed sodden (0.99) — B4's rot path has its first real test coming.
**Fixed the same morning (restart-gated):** (1) possum berries only at the fruit stage and once a night — the first
night ate one flowering plant five times (F-0760 → J-0553); (2) his trap metaphors were dispatched as trap deeds and
one was answered by the WEEDING hand — dispatch now hands `family=` to `garden.act_from_thought`, which runs only
that family's hands, and the grammar learned "a verb is a verb" (determiner → noun, hyphen → compound, gated reach
stops at a comma). Decision replay vs baseline: 0 deeds gained, 424 false-fire rows lost (F-0761 → J-0554, F-0762).
Regressions: `scripts/_test_dispatch_family_scope.py`, `scripts/life_smoke.py` (+2 checks).
