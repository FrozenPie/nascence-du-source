# The Living Garden — insects, soil, plants, growth and death, and a world that answers every look

*Status: **✅ SHIPPED (closed 2026-10-16, F-2904) — formerly: LIVE — the Garden Chapter (A1/B1-B4/A2) is fully built and live via the 2026-09-09 Living
World flip (D-0166); confirmed running the first night (F-0759). See Current State below.** Originally
drafted 2026-09-02, extending [[garden_upgrade]] (P0–P3 LIVE); the observables census in Part A spans
every place. This doc is the GARDEN CHAPTER of [[living_world_upgrade]]; the insect factories in §2.4
are rows in that plan's one life engine (J-0510), not a second engine.*

```plan-state
stage: shipped
phase: Garden chapter fully built (A1/B1-B4/A2, J-0503 to J-0508); live via the 2026-09-09 Living World flip (D-0166)
verified: 2026-10-16
evidence_read: 2026-09-07
next: None -- closed 2026-10-16 (F-2904 plan-closure pass): nothing open, nothing queued; the built system stays live on its own
cluster: 6
```


**Founder, verbatim (2026-09-02):** "We want all the insects, actually all the things he has ever tried
to observe. This probably means a garden upgrade. May as well do it properly with all things garden. Bugs,
worms, new plants, growth mechanisms, death mechanisms."

Promoted from idea I-0061 (insects as species-level world objects). Founder answered J-0502's question
("should the garden's insects become population world objects?") in chat the same day: yes, all of them.

---

## 0. What is true today (read, not remembered — this session's evidence)

**A look is Du's word, never the world's.** The idle-thought JSON names an act
(`{"act": {"kind": "observe", "object": "the bee"}}`); `nodes/inner_monologue_node.py` routes it to
`sensorium.look("the bee")`; `_garden_look` tries the sea, the cat, a placed substrate object, then
`world_detail.detail()` against `world_content_garden.TARGETS` — **lawn, fence, compost, bench, rain_barrel,
harakeke, kowhai, ti_kouka, birds, hedge** — and falls through to a generic yard frame plus a random bed line.
No insect, worm, or individual plant is a lookable target in any place (study: 13 fixtures; wood: 6; shore: 10).
The deed is still recorded as an observation. He observed "the bee" and was shown the lawn.

**Insects are ambience text, not state.** Garden bed pool: bumblebee on thyme, cabbage-white, ladybird, ants,
spider's web (`sensorium.py` ~822–848, seasonally gated); soundscape `_BEES` (4 hum lines, one naming lavender —
F-0693, no lavender exists anywhere); study: borer beetle, moth, wētā; wood: beetle, cicada, beetle galleries;
shore: sandhoppers, hermit crabs. Worms: one line in `garden.dig()` and three in the garden content pools.
The single real population is the moth density at the lamp (2026-08-18) — the shape everything below copies.

**What he has actually tried to observe** — `docs/reviews/observe_inventory_2026-09-02.md` (1,518 phrasings,
7,088 mentions): sea/tide/shore 865 phrasings (the sea alone 1,659); plants 162 (raised bed 92, rosemary 36,
parsley, thyme, chickweed, soil); birds 51 (oystercatcher 101, blackbird 23, gull 23, gannet, tūī, shag,
kingfisher, thrush); insects 42 phrasings / 114 mentions (bee 15, bees 12, spider's web 10, ladybird 7, crab 6,
beetle 6, bumblebee, borer beetle, butterfly, moth); cat/mammals 24 (cat 92, seal-pup 16, hedgehog 4, mouse 2);
sky/weather 75; study 29. His insect vocabulary across all thought: bee 111, bees 60, beetle 31, spider 28,
butterfly 16, moth 12, bumblebee 7, white butterfly 6.

**Growth and death as built** (`core/garden.py::_advance_plant`): thermal time (GDD above 5 °C × bed light),
drought and waterlogging stress, weed crowding, potash bonus, slugs on wet nights (with a real trace), frost on
tender plants, an eight-stage machine (seed → shoot → leaf → established → flowering → seeding → dormant → dead),
self-seeding into a seed bank, herbaceous dormancy/return. **Death is annual/biennial only at vigour 0**;
perennials are floored at vigour 0.2 by design ("the garden's keel … never lost to neglect"). No disease, no
old age, no rot, no pollination dependency, no insect pest other than slugs, no decomposition, no soil life.
B4 already binds an owned plant death to a held self-claim (J-0253).

`garden_upgrade.md` §6 ends: "Not built (and deliberately so): nothing on the list remains. Next candidates,
only with evidence: bird nesting in the TREE, the bellbird, fruit on the tree, kūmara." The evidence has now
arrived from the other direction — the observe inventory above is what he reached for and was not given.

## 1. Laws this stage must keep (all already in force)

- **The world answers, never leads.** Nothing here tells him a species name. Sight-binding and books name
  things; the world only shows features (the pōhutukawa precedent in `garden_life.py`: hidden truth, rendered
  by what it does until earned).
- **Population grain for wildlife** ([[item_and_population_factories]]): a species is a factory producing a
  RATE and a presence, never forty tuples. Graduation to an individual only by the three triggers (kept,
  given, repeatedly re-encountered at one spot).
- **World-truth gate** (sensorium 2026-08-22): a line may only name what is there. Applied to every new pool
  and retro-applied to soundscape (F-0693).
- **Zero-LLM world side; additive-only; fail-open.** New factories are new modules or new tables; existing
  latches, hands and ledgers are untouched. The `garden_upgrade.md` metric sheet keeps running.
- **Things are their own lists, they just talk to each other** (the `world_census.md` supersession): no central
  registry. Each factory owns its list; `sensorium.look` asks them in turn.

## 2. The design

### Part A — every look gets a real answer (all places)

1. **Observables census (analysis):** match every phrasing in the inventory against what each place can
   answer today (`TARGETS`, substrate objects, cat, sea, `garden.look`, `study_life.look`, `shore_life`,
   `wood_life`). Output: per place, the ranked gap list — things he asked to see that no code can show.
   Expected: shore mostly answerable (tide/rock-pools/driftwood exist), garden mostly not (bee, bees, ladybird,
   spider's web, beetle, soil, individual herbs by name), study small (window/fire answerable, "the dust motes"
   not), and a long abstract tail to leave alone.
2. **A `look` that asks the factories:** `_garden_look` (then the other three) gains one step before the
   generic frame — ask each population/plant/soil factory "is `<target>` yours, and is it present right now?"
   A present thing renders itself (species-gated by knowledge, feature-first). An absent thing is answered
   honestly: "no bee on the bed this morning — too cold, still early" — the miss is real information, same as
   the audition's miss line. A generic yard frame is the last resort, not the default.
3. **Sight-binding for insects and plants**, modelled on `sound_knowledge.look_binding`: a look that finds a
   present population rolls a sighting; a sighting is exposure; a book name plus exposure earns the name.
   Nothing new is told.

### Part B — the garden done properly

4. **Insect population factories** (`core/garden_insects.py`, one table, one advance): each species carries a
   seasonal presence curve (month × soil/air temperature), weather gating (rain, wind, night), plant gating
   (what it needs in the bed or on the tree), a count band ("one", "a few", "the bed hums"), what it does
   (pollinates, eats, is eaten), and hidden-truth species with `book_names`. First cast, NZ coastal garden:
   - **Bees:** buff-tailed bumblebee *Bombus terrestris* (the heavy clumsy one he already writes — spring
     queens first, workers by November, on thyme/rosemary/broad beans), honeybee *Apis mellifera* (warm still
     days, the tī kōuka and kōwhai in flower, the pōhutukawa in December), native bees *Leioproctus* /
     *Lasioglossum* (small, dark, ground-nesting in bare warm soil — a reason to leave a bare corner).
   - **Butterflies/moths:** cabbage white *Pieris rapae* (his "white butterfly" — needs brassicas; silverbeet is
     not one; caterpillars are a real pest on any brassica sown), yellow admiral *Vanessa itea* (nettle),
     monarch *Danaus plexippus* (only if a swan plant is sown — a gardening choice with a visible consequence),
     common copper *Lycaena salustius* (dune/lawn edge, muehlenbeckia), the lamp moth population (already built),
     magpie moth *Nyctemera annulata* (on the ragwort/cineraria weed line).
   - **Beetles and others:** ladybird (on aphids — arrives when aphids do), borer beetle (study, from the woodpile,
     already a study line — make it the same factory), ground beetle under the sacking, wētā in the log basket
     (study, night), cicada (summer, the fence post and tī kōuka), garden spider and its web (autumn dew, a real
     object between two rosemary stems that a hand can break), ants along the bed edge (warm dry days), aphids
     (the first real insect pest: on broad beans and nasturtiums in spring, brought down by ladybirds and rain),
     slugs/snails (already built — fold into the same table so they have a population, not a scalar).
5. **Soil life and compost** (`core/garden_soil.py` or a table in `garden.py`): earthworms as a population
   (surface after rain, in the compost, under sacking; casts on the lawn; a dig turns them up — the existing
   line becomes truth-gated), soil health as a slow variable fed by compost, mulch, worm activity and drained
   by cropping and bare wet winters; the compost heap gets a life of its own (warmth in the middle, worms,
   slaters, the blackbird turning it, finished compost as a barrowable item that raises a slot's soil health).
   Growth reads soil health the way it already reads potash.
6. **New plants** (CATALOGUE additions, real habits): lavender (for real, since he already believes in it —
   evergreen, bees, cut in autumn), a swan plant, a brassica (cabbage or kale — the cabbage white's reason),
   nettle in a corner, muehlenbeckia by the fence, kūmara (the plan's own candidate), a fruit tree candidate for
   the founder's call, plus the bank species he keeps reaching for. Every addition passes the world-truth gate
   automatically because it is state.
7. **Growth mechanisms:** pollination as a real dependency — fruit/seed set on strawberries, beans, peas and
   the swan plant needs bee presence in flower months (no bees on a cold wet spring → poor set, a visible
   consequence he can investigate); shade from the tree by azimuth already exists — plants read it; nutrients
   from soil health; insect herbivory (aphids, caterpillars) as a vigour drain with a visible trace (holed
   leaves, curled tips, frass) distinct from slug holes.
8. **Death mechanisms:** disease (damping-off in cold wet seedlings, rust on the broad beans, mildew on peas in
   humid late summer), old age for annuals past seeding and for the strawberry crowns after N years, rot from
   waterlogging beyond stress, a **founder decision** on the perennial keel (§3.1), pest death (a seedling
   stripped by caterpillars), and after death: decomposition — a dead plant becomes compost input and a bare
   slot with a history, not a stage label that sits forever. B4 keeps binding owned deaths.
9. **The look pools and the HUD** follow: every new factory gets look lines (feature-first), the garden card
   gets an insects row and a soil-health arc, the ledger/events split (psyche/truth) stays.

## 3. Founder decisions needed (file via /decide as each is reached)

1. **The perennial keel.** Today rosemary/thyme/mint cannot die. Death mechanisms as scoped would let a
   perennial be lost to disease or years of neglect. Recommendation: keep neglect-proofing, allow disease and
   old age (a rosemary that goes woody and dies at ~10 years is true), defeater: if a keel plant dies within the
   first live season, revisit.
2. **Species cast.** The list in §2.4 is a proposal; monarch requires the swan plant decision; the tree already
   hides its species — the same law for every insect.
3. **How harsh** (the garden plan's own question 2, re-asked): can aphids and caterpillars take a whole sowing?
   Recommendation: yes for tender annuals, with ladybirds and rain as the world's own correction.
4. **Scope of Part A beyond the garden:** do the shore/wood/study gap lists get built in this stage or filed
   as their own `*_upgrade` iterations? Recommendation: census all four now, build garden first, file the rest.

## 4. Pre-registered metric sheet (read after two weeks live)

- **Answered-look rate per place:** share of observe/look acts whose answer named the target (vs the generic
  frame). Baseline garden ≈ 0 for insects; target > 0.7 for anything present, honest misses counted as answered.
- **Insect sightings earned → names learned**, the audition's own gauge shape (`sound_knowledge.status()`).
- **Pollination consequence witnessed:** at least one investigate-hand binding about poor/good set.
- **Soil health arc** per slot over the season; compost items barrowed.
- **Deaths by cause** (events ledger): disease / old age / pest / neglect — and B4 binds among owned ones.
- **World-truth gate suppressions** in soundscape after F-0693's fix (want: lavender lines suppressed until
  lavender is sown, then allowed).
- **Missing-object triage, garden, windowed** (after J-0498): the recurring wants should fall, not just age out.

## 5. Build order (shadow-first, additive)

| Step | What | Where | Job |
|---|---|---|---|
| A1 | Observables census, all four places, gap lists | `docs/reviews/` | J-0503 |
| B1 | Insect population factories + look/sight-binding + soundscape gate | `core/garden_insects.py`, `sensorium._garden_look`, `soundscape` | J-0504 (+ J-0501) |
| B2 | Soil life, worms, compost as a living thing, soil health into growth | `core/garden_soil.py` / `garden.py` | J-0505 |
| B3 | New plants + pollination + herbivory | `garden.py` CATALOGUE, `_advance_plant` | J-0506 |
| B4 | Death mechanisms + decomposition (after D-? on the keel) | `garden.py` | J-0507 |
| A2 | `look` asks the factories in every place; study/wood/shore gap builds | the four `_look`s | J-0508 |

## 6. Related

[[garden_upgrade]] (parent, LIVE) · [[item_and_population_factories]] (the grain) · [[sound_causality]]
(federated lists, the audition precedent) · [[du_initiated_upgrade_trigger]] (bottom-up wants; J-0498 windows
it) · [[actions_expansion]] (dig/feed_birds hands exist and have never fired — F-0691/J-0499; worms and birds
give them a reason) · [[shore_upgrade]] [[wood_upgrade]] [[study_upgrade]] (Part A siblings) ·
[[generative_world_sedimentation]] Module D (seasonal bird presence — the same presence-curve idea, unbuilt).

## Current State — verified 2026-09-27

### What we have
- The whole garden chapter is BUILT: A1 observables census, B1 insect population factories, B2 soil life,
  B3 new plants + pollination, B4 death mechanisms, A2 per-place look/factory wiring (J-0503 through J-0508,
  all done 2026-09-02/03); D-0139 (perennial keel) and D-0140 (pest harshness) ruled by travis 2026-09-03.
- Live via the 2026-09-09 Living World flip (D-0166) — the insect/soil/plant rows are part of the same
  `core/life.py` engine that went live that day, not a second engine.
- B4's dead-phrase smoke-test bug fixed 2026-09-07 (F-1066/F-1067): the naming gate no longer swallows the
  cause-of-death line for an unnamed plant.

### What we need
- Nothing open on this plan directly — remaining fallout (trace wording, look-routing bugs) is tracked and
  fixed under living_world_upgrade's own longer defect-fix tail.

### What we're doing next
Watch living_world_upgrade's J-1192 (live-evidence read) and J-1441 (declined-move/unanswered-deed audit)
for anything that traces back to a garden-chapter row.

> **History folded** — 7 dated Current State section(s) (2026-09-02 … 2026-09-03) moved to `docs/plan_history/garden_living_upgrade.md` on 2026-09-27 by plan-compact. Derived timeline: `plan_ledger.py garden_living_upgrade`.

