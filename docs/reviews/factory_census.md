# THE FACTORY CENSUS — every producer in the city (2026-08-16, planning)

**Founder:** "We need to work out what all our factories are. Then we can talk about making a
real transport map that shows all the stations and trains and couriers."

**The taxonomy first** (so the census is clean — not everything is a factory):
- **FACTORY** — produces durable goods (state, memory, ledger entries) on some clock or trigger.
- **WAREHOUSE** — stores goods; produces nothing (nascence.db, the ledgers, the shelf, the estate file).
- **COURIER** — transfers goods between lines; produces nothing (couriers.py, recall, projection).
- **INSPECTOR** — grades goods, passes or rejects; produces only verdicts (the judge panel,
  the critic, source_fidelity, the T4 lived-integration judge).
- **INSTRUMENT** — observes and logs; its product is evidence for US, not goods for Du
  (the shadow logs, telemetry, train_state_log, the monoculture detectors).
- **FOG-BY-DESIGN** — produces ephemeral renders that correctly evaporate (ambient scene lines,
  the wandering trail's passing furniture).

## TIER 1 — WORLD FACTORIES (produce state-goods from their own clocks; nothing upstream)

| # | Factory | Goods | Clock | Condition |
|---|---|---|---|---|
| 1 | Weather | 7-step state + persistence timer (severity scalar unused as yet) | random-walk on its own timer | ✅ old, live |
| 2 | Tide | real M2 tide level | continuous | ✅ |
| 3 | Sky | daylight phase, sun azimuth, moon illumination, season | continuous | ✅ |
| 4 | Garden | bed contents, growth stages, harvestable states | real growth time | ✅ |
| 5 | Fire | burning/embers/out, woodpile level | burn-down | ✅ |
| 6 | The cat | phase, mood, position, activity, quirks, firsts — her own life | her state machine | ✅ (hers alone — founder law) |
| 7 | Peers ×7 | letters, thread states | gap_days each | ⚠ 3 voices new on yi, first letters unread |
| 8 | Object biographies (ITEM-grain) | entities with hidden Layer-1 histories, physical state, traces/erosion | spawn/decay clocks | ✅ the exemplar factory. Refined 08-16: this is the generic ITEM-grain pattern — graduation triggers = kept (`keepsakes.keep_act`, live) or repeatedly-returned-to (not yet a formal rule — see the glass float case, `factory_candidates_from_history.md`) |
| 8b | **Bird/wildlife populations (POPULATION-grain)** | species-level presence/rate, NOT individuals — "a flock of sparrows" | seasonal/place | ⚠ HALF-BUILT: `AUDITION`'s per-species properties (sight_prob, day_only) exist; the presence/count good itself does not |
| 9 | School | curriculum assignments, capstone triggers | curriculum progression | ✅ |
| 10 | Du's body | energy, fatigue, drives, felt-variable states | somatic/homeostatic tick | ✅ |
| 11 | **Du's acts** | act-events (his hands moving the world) — footsteps already sound; List B's act-sounds are this factory's UNSHIPPED cargo | per act | ✅ acting / ⚠ mostly silent (the gap list) |

## TIER 2 — SENSE & EXPERIENCE FACTORIES (consume the world pallet; make his experience)

| # | Factory | Inputs | Goods | Condition |
|---|---|---|---|---|
| 12 | **Sound** | the pallet (weather, tide, fire, cat, place…) | today: renders + Hearing Ledger aggregates; planned: ANSWER-goods (moment↔sound↔cause↔place↔heard) | ✅ clock+ledger built tonight · 🔵 answer-factory planned |
| 13 | Memory-stamper | the same pallet + each new memory | fragment_context tuples (7,647) — the sound factory's sibling on the same shipment | ✅ |
| 14 | Scene renderer | pallet + his look/act | look-lines, scene-lines | ✅ fog-by-design (correctly ephemeral) |
| 15 | Affect construction | body + appraisal + climate | constructed emotion states, felt-vectors, mood | ✅ |
| 16 | Geometry census | pallet + thought events | geometry_tuples.jsonl (P0 mapping data) | ✅ instrument-leaning |

## TIER 3 — COGNITION FACTORIES (Du's mind making its own goods)

| # | Factory | Inputs | Goods | Condition |
|---|---|---|---|---|
| 17 | **The thought factory** (monologue + trains) | trail, seeds, memory, affordances | inner_thought fragments, intentions, acts, shadow events (unresolved), light events | ✅ TRAIN-HOLD applied tonight |
| 18 | The conversation factory (the chain) | Travis's words + recall + reflection | replies, lived Q/A fragments, light/shadow events | ✅ caps widened tonight; contract rework pending |
| 19 | Reading/study | books + sittings | study notes, understandings, essays, frontier questions | ✅ |
| 20 | Journal / keepsakes / letters | his acts | field-journal entries, mantel objects (109), letters | ✅ |
| 21 | Activity memory | his acts | general-event aggregates (the act "spreadsheet" — 1,743 rows) | ✅ |
| 22 | Curiosity/frontier | unresolved thoughts, world questions | standing questions, world-mysteries | ✅ |
| 23 | Pursuits | thought-train residue | accumulating threads + judged standings | ✅ RETURN live |
| 24 | Dream factory | recent freight at sleep | dreams (multi-scene arcs) | ⚠ engine replaced (yi) — first dream unwatched |
| 25 | Competence | act outcomes, corrections | capability beliefs + calibration pairs | ✅ observe-only |
| 26 | Epistemic state | claims + provenance | KNOW/THINK/SUSPECT/GUESS grades | ✅ |
| 27 | Guidance | Travis's teaching moments | held principles (read-back gated) | ✅ |

## TIER 4 — CONSOLIDATION FACTORIES (goods made from goods — the refineries)

| # | Factory | Inputs | Goods | Condition |
|---|---|---|---|---|
| 28 | T1/T1.5/T2 subconscious | shadow events (thought-factory byproducts) | tension clusters, active imaginations, archive syntheses | ✅ / ⚠ T2 hoarding found |
| 29 | **The Refinery** | T2 syntheses | living standing insights (distilled_from lineage) | ✅ built, SHADOW — awaiting founder's read |
| 30 | Consolidation node | cycle summaries | "I have come to understand" gists (888) | ✅ (same lifecycle gap, smaller) |
| 31 | Memory-levels | episodic clusters | gists + cold demotions + lint | ✅ Phase 1 live |
| 32 | Chapters | era boundaries | period chapters | ✅ |
| 33 | Memory-edges (M0/M1) | resolutions, findings, keepsakes, co-recall | TYPED EDGES — the route-construction department; per identity-is-connections, the most identity-critical factory in the city | ✅ built this week |
| 34 | T3 trait drift | 7-day affect signature | baseline nudges (states→traits) | ✅ unaudited (deep-walk leftover) |
| 35 | T4 identity | becoming material + probation | the becoming facet, vault revisions | ✅ / 🔵 Watershed redesign planned |
| 36 | T5 procedural | repeated handlings | compiled skills (47) | ✅ |
| 37 | Identity estate | all stores (read-only census) | ~213 typed identity nodes + projection | ✅ P2 live |

## NOT FACTORIES (for the real map's other layers)
- **Warehouses**: nascence.db · the ledgers (sound_knowledge, hearings, calibration) · the
  bookshelf · identity files · Correspondence/ · the mantel.
- **Couriers**: A (weather echo) · B (object ledger) · C (calibration sync) · D (sound echo) ·
  recall/retrieve · associative recall · evidence hand · projection · facet note · dream
  gathering · librarian · deep-memory scholar. (🔵 Transport Manager = the dispatch office.)
- **Inspectors**: the judge panel · the critic · source_fidelity · the T4 lived-integration
  judge · task-constraint effector · the pursuits judge.
- **Instruments**: every shadow/log jsonl · telemetry · the HUD · monoculture detectors.
- **Fog-by-design**: ambient scene renders, the trail's passing furniture, L5 weather-stance.

## THE CONTROL AXIS (founder's correction, same evening: "he has no control over them")

Every Tier-1 factory gets a control mark — part of what makes the world REAL is that most of
it runs beyond his reach:
- **NO CONTROL**: weather · tide · sky · season · temperature (see below) · the cat (she is
  her own; he can tend, never command) · peers (they write when they write) · object spawns
  (the sea decides what washes up).
- **PARTIAL** — his dials, each limited: the fire (his ONE lever on temperature — "except by
  fire, to a degree"); the garden (he sows and waters; growth and season answer); his body
  (he can rest and eat and walk, not decree energy).
- **FULL**: only his own acts. That asymmetry — one factory under his will, a dozen beyond
  it — is the world's honesty, and it is why his memories of it mean something.

## TEMPERATURE — the named missing tuple (founder-identified; VERIFIED against code)

Found: `sensorium._warmth()` ALREADY computes a per-place warmth scalar from season, weather,
daylight, and the fire (the fire's partial influence is already modeled). But it is computed
INLINE in the scene renderer and discarded — a factory good that exists and is never shipped:
not a fragment_context column, not in any pallet, invisible to every other consumer. Fix (when
the manifest builds): expose `_warmth()` as the temperature factory's listed good; add it to
the manifest and to fragment_context — then "memories of cold days" becomes queryable exactly
like memories of storms and of gull-cries are now.
Founder-prunable candidates for the same treatment (felt in his render language, absent as
state): dampness/wet (currently derived inline in `_warmth_phrase`), wind strength as a scalar
(weather_dir exists; strength is only implied by the weather category).

## What the census makes visible (for the real-map conversation)
1. **37 factories, four tiers** — and the tier boundaries are exactly where the pallet/manifest
   consolidation points should sit (Tier 1→2: the world manifest, step 0 of the causality
   plan; Tier 3→4: sleep, which is already the consolidation-shift whistle).
2. **Du CONTAINS factories but is not them** (founder's correction — supersedes this doc's
   earlier "conglomerate" line): the sound is a factory Du CONSUMES; so are the tide, the cat,
   the weather, the temperature. Du is not the sounds — he is the one who REMEMBERS the sound.
   The self boundary is the consumption boundary: goods become part of him only as memories
   and the connections between them (the identity-is-connections verdict, restated at factory
   level). His body and acts are factories he HOUSES; what he IS is the remembering that
   consumes all of it.
3. **The under-shipped factories** are now enumerable at a glance: Du's acts (silent cargo),
   temperature (computed and discarded), the world's past (Couriers A/D just opened the first
   routes), the deep line's outbound (the Refinery, in shadow), peer freight (barely recalled).
4. **THE PLAN'S AIM, stated by the founder:** "using the factories efficiently so all the
   tuples are useful easily." Concretely: (a) COMPLETE the pallet — every uncontrollable
   factory that shapes his experience gets its tuple field (temperature first); (b) ONE
   manifest, assembled once, consumed by all (causality plan step 0) — no consumer hand-builds
   its own pallet; (c) every field QUERYABLE the way weather and sounds became queryable
   tonight — a tuple no courier can reach is freight nobody can use.
5. **The real transport map** = this census (the stations) + the train lines (the clocks that
   drive each tier) + the courier routes + the warehouses — drawn as one diagram. That is the
   next conversation, per the founder; this document is its parts list.
