# The Garden Upgrade — from a bed of seven numbers to a place that grows

*2026-08-22, founder: "This is a very early part of our system. Time for an upgrade I think."*
*Status: **P0 + most of P1 BUILT 2026-08-22 — and CONFIRMED LIVE 2026-09-02** (`core/garden.py`; the original "restart-gated" caveat is resolved: `data/garden_ledger.jsonl` holds 31 real live deeds through 2026-08-30, see §11) on the founder's rulings the same morning: rosemary/thyme cuttable now; the garden to be the fullest place; real plants, real schedules; plants with world history like the driftwood; a heap of random seeds pre-spawned waiting for spring; items to collect and move. See §6.*

```plan-state
stage: live
phase: P0 gate accepted (D-0243); deed stream stalled on seed-tin + harvest cooldowns (F-1994)
verified: 2026-11-14
evidence_read: 2026-11-14
next: next boot carries J-2481; then the D-0502 defeater read (hands_trace since boot, 7 live days)
history: docs/plan_history/garden_upgrade.md
cluster: 6
```


---

## 0. What the garden is today (read, not remembered)

Built 2026-06-20 as "a second place he can step into," modelled on Travis's own raised bed on the hill above the
sea. Honest inventory, from `core/sensorium.py` + `data/world_geometry/garden.json`:

| Part | What exists | Verdict |
|---|---|---|
| Plantings | 7 entries (`_PLANTINGS`): parsley, thyme, mint, rosemary, lettuce, tomatoes, sunflowers. Each plant = **two numbers**: `growth` 0..1 and `moisture` 0..1, plus `sown`. | A plant is a scalar. No stage, no vigour, no flowering, no seed, no age. |
| Clocks | `_advance_garden` on real time: moisture −0.10/day dry, +0.9/day rain; growth +rate/day **only in the plant's `grows` seasons** (all herbs exclude winter); tender plants die at moisture ≤0.05. | Correct in spirit, and **frozen for three months**: every plant's growth is zero all winter. He has lived in a static bed since June. |
| Hands | water · replant/sow · harvest (→ `picked` store) · tea (at the hearth, needs fire + picked herbs). | Water is the only hand that always "works" — **455 waterings in the log, 0 harvests, 0 successful sowings, 20 refusals**. He waters a bed at moisture 0.996 in drizzle and is told the soil drinks it in. A deed with no consequence. |
| Rendering | `_bed_summary` (stage phrases from growth) · `_garden_look` bed/sea/sky/letterbox pools (~40 lines) · `_garden_event` ambient pool (37 lines) · `_garden_milestone` (sunflowers open; a herb lush). | Look-pools were **not gated on truth** until today (showed rosemary in a bed holding only thyme). Otherwise good prose; thin. |
| Geometry | 10.5 × 12.5 m, 12 positioned features (cottage, door, doorstep, window, **raised_bed**, tree, wall, fence, flower bushes, harakeke, gate, letterbox), 6 standpoints, act→standpoint map, sound sources, cat spots. | Good bones. The bed is ONE feature; plants have no positions. |
| Substrate objects | `world_objects.json`: 21 objects, **0 in the garden** (the shore has driftwood/stones; the garden's 5% "trowel catches a stone" is the only mint path). | The place he spends most hours in (48–56 tuple-rows/hour overnight) is the emptiest. |
| Channels into it | Weather felt (events), sea sound/smell (events), thermal field at standpoints (built last night), wetness (built last night), sun insolation by place (built). | The new channels exist but **the garden physics don't read them** — growth still keys off `season` and `moisture` only. |
| Memory | Garden deeds land as `origin='action'` fragments and activity-memory counts. No garden ledger; nothing he has sown/cut/seen flower is kept as his. | He cannot remember his own garden except as counts. |
| Instruments | None specific. | |

Two bugs found on the way (both fixed 08-22, restart-gated): the bed had silently lost three of four herbs and
its growth field (cause unknown — only `_fresh_garden` writes the bed); the look-pool named unsown plants.

**The short verdict:** the garden is a 2026-06-20 sketch that the rest of the world grew past. It was where
the first real deeds happened (water, sow) and where he goes when theory wears thin — tonight's rosemary —
and it cannot answer him with anything but "the soil drinks it in" or "too thin to cut."

---

## 1. Laws this upgrade must keep (all founder's, all already in force)

1. **The world decides what exists; the channel decides what reaches him; the psyche decides what it means.**
   Plants are world truth with positions; what he sees is gated by where he stands and what is actually there.
2. **Tuples linked to tuples.** Garden physics read the SAME fields he experiences — the thermal field at the
   bed, rain → wetness/moisture, sun insolation, wind, frost. No private garden weather.
3. **World answers, never leads.** No hints. The affordance block stays as it is (informing). Milestones are
   announced once as world events (already the law). Consequences are shown when he looks or acts.
4. **Deeds have consequences both ways.** The cure for "deed without consequence": a hand can do harm, can be
   unnecessary, can fail for a reason he can find out.
5. **Earned bindings.** What a plant does over weeks (shoot, bolt, flower, set seed) is learnable by watching
   and the investigate hand — and he may bind it wrongly. Phenology is the emergence lever: it cannot be told,
   only lived.
6. **Additive, shadow-first.** The scalar bed stays as a projection until the new physics has run a parity
   week beside it; old render lines keep working; nothing he already knows is removed.
7. **Pre-registered metric sheet** before the flip.

---

## 2. The design

### 2.1 A plant is a thing, not a number (world truth)
Each plant becomes a **positioned substrate object** inside `raised_bed` (slots along the bed, like the mantel
slot law), with state:
`stage` (seed · shoot · leaf · established · flowering · seeding · dormant · dead) · `vigour` 0..1 · `moisture`
(per slot) · `last_cut_ts` · `cut_count` · `sown_ts` · `flower_ts` · `seed_set` (bool) · `pests` 0..1 ·
`weeds` 0..1 (per slot).

Stage transitions are driven by **degree-days and light**, not by `season` labels: daily growth =
f(thermal field at the bed by hour, sun insolation at the bed, moisture band, vigour − weeds − pests). Frost
(thermal band very_cold at dawn + clear sky) damages tender plants; repeated frost kills them. Rosemary and
thyme are evergreen — **cuttable in winter** (slowly); mint dies back to the root in winter and returns in
spring (the first spring event he could witness); parsley bolts in its second summer; lettuce bolts in heat;
sunflowers track the sun (insolation + az → "faces to the sun" becomes literally true); tomatoes need stakes.

### 2.2 The garden's own clocks (substrate)
- **Weeds** grow with rain × warmth on every slot, and crowd vigour. He can weed (a real hand with a real
  effect, currently a synonym for water).
- **Slugs/snails** after rain at night eat lettuce and seedlings (a trace he can find in the morning: holes,
  a silver trail — a world-trace like the cat's paw prints).
- **Birds** take seedlings unless netted (the tui is already in the tree).
- **Drying**: cut herbs dry on a **rack by the hearth** at a rate driven by the thermal fire-by-distance
  term (built) — days by a fire, a week in a cold room, mould if the room is wet/cold too long. Dried herbs
  are the tea loop's real input and a keepable thing (a bundle of dried rosemary on the mantel).
- **The rain barrel** at the cottage corner fills with rain (weather → level) and empties when he waters;
  a dry barrel in a dry spell is a real constraint, and the first reason to carry water from the shore is
  wrong (salt) — a binding he may get wrong.
- **Seed**: sowing needs seed. Seed comes from (a) a small packet store in the study drawer (finite, seeded
  for spring), (b) saved seed from what he lets flower and seed (sunflowers, lettuce, parsley) — the long
  loop: patience now → seed next season. Saved seed is his; it goes on the mantel.

### 2.3 What reaches him (perception)
- `_bed_summary` and look-pools render **from plant state**: stage words, visible pests/weeds, wilting
  (moisture + heat), frost-burn, flowering, seed heads. Truth-gated by construction — a line exists only
  because the state does.
- **Events** (the channels programme pattern): first shoots, first flower, a plant gone over, slugs' work
  found, frost-burn seen at dawn — quiet-gated, once each, only when he is at the bed or looking.
- **Smell** (programme §3 Phase-1 odorants): brushed rosemary/mint, wet earth after rain, at the bed only.
- **Tree shade** moves across the garden with sun azimuth (the light channel's first real garden use):
  "the bed is in the tree's shade now" at the hours it is.

### 2.4 What he keeps (psyche)
- A **garden ledger** (sibling of the thermal and hearing ledgers): sowings, cuttings, waterings-when-dry vs
  waterings-when-wet, weedings, first-flower dates he witnessed, deaths, seed saved. Fed only by what he did
  or saw. Readable by activity memory ("I have been tending the bed") and by keepsakes.
- **Bindings** via the investigate hand: "why did the lettuce die" → the ledger + the trace (dry spell /
  slug trails / frost) → a binding he authors, possibly wrong, revisable. No cause is ever told.
- Experienced tuple: `bed_state` summary at his place when at the bed (what he could see), never elsewhere.

### 2.5 Hands (all existing latches kept; new ones additive)
water (now with effect-or-harm) · weed · sow (needs seed, season-aware by **soil temperature**, not month)
· stake/net (tomatoes, seedlings) · harvest (cut; regrowth real) · dry (rack) · save seed · tea (unchanged,
now reachable) · investigate (already exists; gains the ledger as evidence).

---

## 3. Pre-registered metric sheet (read after two weeks live, spring)

1. **Deed-with-consequence rate** — share of garden deeds whose world answer was not the neutral default
   (water-when-dry vs water-when-wet; sow-with-seed vs no-seed). Today ≈ 0 (455 waterings, all "drinks it
   in"). Want > 0.5. Kill if the hands start failing for reasons he cannot discover.
2. **Loop closures** — sow → shoot seen → harvest/flower → seed saved, per plant. Today 0. Want ≥ 1 full loop by
   the end of spring.
3. **Phenology bindings** — investigate-hand bindings about the garden (count; share later revised). Wrong
   ones are allowed and counted; what is NOT allowed is a binding that was told.
4. **Watching** — does he return to the bed to look (not act) after an event? (the "return and develop"
   signature the pursuits work looks for).
5. **Contamination** — zero garden lines naming a state that does not exist (grep audit, the firelight /
   rosemary class of bug). Any hit is a bug.
6. **Cost** — zero LLM calls in garden physics; render remains pooled prose.

---

## 4. Build order (shadow-first, additive)

| Step | What | Touches |
|---|---|---|
| P0 | Plant objects with positions + new state, advanced by the thermal/sun/rain fields; the old scalar bed kept and compared (parity week: stage words must not regress) | `core/garden.py` (new), `sensorium.tick`, `world_objects` |
| P0 | Truth-gated rendering from state; frost; evergreen winter cutting; mint dieback/return | `sensorium` bed summary + look pools |
| P1 | Weeds, slugs, birds; rain barrel; seed store + saved seed; drying rack (thermal-driven); hands gain consequence | `core/garden.py`, keepsakes (dried bundle, saved seed), study drawer feature |
| P1 | Garden ledger; activity memory + keepsakes read it | `core/garden_ledger.py` — **UPDATE 2026-08-23 (files-and-evidence audit): never built as a separate module; the ledger-writing logic landed inside `core/garden.py` instead, writing `data/garden_ledger.jsonl` (confirmed: 1 real entry as of 2026-08-22).** |
| P2 | Events (shoots/flower/pests/frost) quiet-gated; smell odorants at the bed; tree shade by azimuth; investigate hand gets the ledger as evidence | channels programme hooks |
| P2 | HUD: the bed as a small live panel (slots, stage, moisture, barrel, rack) | `hud/server.py` |

**Target:** P0 + P1 live for 2026-09-01 so the first spring he can witness is a real one.

---

## 5. Founder decisions

1. **Seed source** — packets in the study drawer (finite, we seed it once) and/or saved seed from flowering?
   Recommendation: both; packets small, so saving matters by next season.
2. **How harsh** — can he lose a whole bed (drought + slugs + no seed)? Recommendation: yes for tender plants,
   never for the evergreen perennials (rosemary/thyme are the garden's keel, like the river).
3. **Tools as objects** (trowel, can, rack, netting, string/stakes, positioned, keepable) or as verbs only?
   Recommendation: objects — they give the investigate hand and keepsakes something real, and they are
   findable/misplaceable.
4. **Travis's actual garden** — the original is modelled on yours. What is in your bed right now, and what
   will you sow this spring? If the seed packets match yours, the garden stays yours.
5. **The cat and the bed** — she sleeps in the warm soil and flattens seedlings (consequence with a face).
   Yes/no?
6. **Scope of winter cutting** — rosemary/thyme evergreen and cuttable now (so his first harvest can happen
   before spring), or hold to spring? Recommendation: cuttable now, slowly; he has asked three times.

---

## 6. Build state (2026-08-22)

**Built in `core/garden.py`** (zero LLM, fail-open, additive — sensorium's scalar bed kept as fallback):
- **Catalogue of 22 real plants** with NZ habits (sow months, germination soil °C, days to leaf/maturity, flower and
  seed months, frost-tenderness, cut-regrow days, dormancy/return for mint · chives · strawberries · oxalis): rosemary,
  thyme, mint, parsley, chives, radish, lettuce, silverbeet, peas, broad beans, tomatoes, dwarf beans, potatoes, garlic,
  strawberries, sunflowers, calendula, nasturtium, poppies + the weeds chickweed, dandelion, oxalis.
- **Every plant and item is a substrate object** (class `plant` / `garden_item`, hidden truth = species/origin/age,
  observations recorded on look) **with a position** (world_objects): 12 bed slots in two rows across the raised bed,
  six ground spots (by the harakeke, under the tree, along the wall, by the doorstep, by the fence, lawn edge).
- **Soil temperature from the thermal field at the bed** (`thermal.field_at("garden","at_the_bed")`, smoothed) →
  degree-days drive the stage machine; month windows gate what CAN happen. Frost = a clear dawn ≤ 1 °C.
- **The garden at the end of winter**: rosemary (3 years, in flower — real: late-winter blue), thyme, mint dormant, parsley,
  chives dormant, strawberries; broad beans sown in June by the previous gardener; chickweed in the bed, a dandelion
  by the wall, oxalis by the doorstep — each with a biography.
- **The seed bank**: 40 random seeds in the soil and corners (calendula, nasturtium, poppies, lettuce, parsley, radish,
  silverbeet, sunflowers, thyme, peas, chickweed, dandelion) at random depths and viability; they germinate when THEIR
  soil temperature and moisture arrive — volunteers he did not sow. **The seed tin**: 8–12 packets, ~60% labelled.
- **12 items with biographies and positions**: trowel, hand fork, watering can, rain barrel (fills in rain, empties when he
  waters), seed tin, twine, stakes, two pots, bucket, netting, bird bath. Ten are carryable: TAKE travels with him,
  PUT sets it down where he stands (any place), with movement history on the object.
- **Consequence**: weeds grow with rain × warmth and crowd vigour (weed hand pulls them); slugs after wet nights eat
  seedlings and lettuce (silver trails seen); frost burns the tender; watering a sodden bed pools; a dry barrel is a
  dry barrel; cut herbs are cut back and regrow on their clock; perennials are the keel (never lost to neglect).
- **The rack**: a cut bundle hangs by the hearth and dries on the FIRE's clock (thermal fire-by-distance); a cold room
  moulds it; dried bundles go to the caddy — the tea loop finally has input.
- **Rendering from state** (`bed_summary`, `look` for plants/items/tin/barrel/rack): a line exists only because the
  state does. Milestones (volunteers up; first flower) announced once via the existing world-arrival law.
- **Hands** wired ahead of sensorium's old ones: harvest · sow (needs the tin to hand, a packet, the month, the soil
  °C, a free slot — each refusal honest) · water · weed · take · put. `literal_will` gained `harvest`, `weed`, `tool`.
- **Ledger** `data/garden_ledger.jsonl` (his deeds) · `data/garden_events.jsonl` (the world's). HUD signature row.

**Simulated 90-day spring (isolated, soil 6→16 °C):** rosemary harvested in winter (slow, woody); second cut refused
(still filling out); radish sown in August at 6 °C; strawberries, chives, broad beans came into flower on schedule;
10 volunteers germinated from the bank (poppies, lettuce, silverbeet, parsley); silver trails after wet nights; weeds
climbed to 0.8 unweeded; the bed dried to cracking in a warm dry spell with a full barrel waiting. Nothing died that
should not have.

**P2 BUILT the same morning (founder: "do the not built stuff next… as in depth as possible"):**
- **Birds** take unprotected seedlings in daylight; the **netting** is a real hand (`net` / take it off) — the bed is
  netted only while the netting object actually lies over it. **Stakes** (`stake`, needs the stakes AND the twine to
  hand): peas, broad beans, tomatoes flop in a gale unstaked. **Save seed** from anything gone to seed → a packet he
  labels himself (and a keepable twist of paper). **The study drawer** (`desk_drawer` feature added to study.json): six
  bought packets; `fetch` moves one to the tin. **Compost heap** item by the wall.
- **`core/garden_knowledge.py` — what he knows is EARNED** (sound_knowledge's pattern): unlabelled sowings and
  volunteers render by their LOOK ("a plant you cannot name yet — soft, slightly sticky pale leaves") until the stage
  at which the species declares itself (radish when established; calendula, peas, beans when flowering) — "you know
  it now"; watching earns weight; a book that ties a name to a look teaches it (radish learned from one sentence).
  Witnessed firsts become habit ("You have seen it come into flower before"). The INVESTIGATE look ("look closer /
  why / what happened") hands him EVIDENCE with no cause — waterings in the last fortnight and whether the soil was
  already wet, browning after a clear cold dawn, holes after wet nights with trails on the soil, dry soil, weeds —
  and `bind()` stores the hypothesis he authors, revised by what recurs. The old seven are grandfathered.
- **`core/light.py` — the light channel's first real use:** sky × cloud × sun height, the moon, the lamp and the
  fire by distance indoors; **the tree's shadow falls away from the sun and lengthens as it sinks** — the bed's
  insolation (read by growth) and the truthful line "the bed lies in the tree's shade just now". Perception events
  (brightening/darkening/enter brighter-darker) SHADOW-logged, DELIVER=False.
- **`core/smell.py` — the smell channel:** odorants with sources, half-lives and wind-carry — woodsmoke while the fire
  burns (the chimney's smoke reaches the garden on a southerly), wet earth, rain on dry ground, salt and weed, leaf
  litter, the herbs when BRUSHED (a harvest, a look), tomato leaf, the cat, the tea, the compost. Entry/onset/renotice
  events SHADOW-logged, DELIVER=False; unknown odorants render as features until bound.
- **Slug damage leaves a real world-trace** (`slug_trail`) on the soil, like the cat's paw prints.
- **HUD:** a garden card on the Evidence tab — the bed by slot/stage/vigour/height, the garden's clocks (soil °C,
  moisture, bed light, weeds, slugs, barrel, bank, tin, drawer, netted, staked, rack, carrying), and what he knows /
  is learning; light and smell shadow counts.

**P3 BUILT the same day — `core/garden_life.py` (founder: "do the still-on-the-list items too"):**
- **The tree** has a hidden species (pōhutukawa, 60 years, by the east wall): leaf → old-leaf drop (Oct–Nov) → grey felted
  buds (Nov) → crimson flower (Dec–Jan, when the soil is warm; the tui come) → woody capsules (Mar–Apr) → leaf. Aerial
  roots on the low limb. **Its name is never told: seeing it flower is half, reading of it is the other half** — the book
  alone earns a little, the flower alone earns a little, both together name it (verified: 0.3 read → 0.5 seen → 0.6 read → known).
- **The flower bushes** are a winter-flowering evergreen (sasanqua camellia, hidden): pink bloom Apr–Aug, petals thick on
  the grass, over by September (announced once). Same naming law.
- **The harakeke** (named, grandfathered): flower spikes Nov–Dec with a tui on them, pods Feb–Mar, black stalks all winter.
- **The nest**: a blackbird builds in the bushes or the harakeke in spring (≤2 broods): building 7d → eggs 13d → chicks
  14d (a thin insistent cheeping in the garden pool) → fledglings on the lawn 7d. **The kept cat hunts** — a fledgling can
  be taken while she is stalking in the garden. Seen only when he looks; heard only when he is there.
- **The lawn**: grass grows with warmth × moisture; daisies in spring; long grass hides the trowel, the fork, the twine
  (a TAKE may fail until it is cut); the **shears** (new item) are the mow hand — clippings to the compost.
- **Reading binds**: `study_note` now feeds `garden_knowledge` and `garden_life` beside the sound binding.
- **The experienced tuple** gained `light_band` (always — ambient light is already rendered) and `smells` (NULL while
  the smell channel is shadow; honest) on both context tables.
- **The HUD as a live map**: `/api/garden_map` + an SVG plan on the garden card — north (the sea) up; cottage, bed,
  wall, fence, tree, harakeke, bushes, gate, letterbox; every plant as a dot coloured by stage; items; the netting;
  **the tree's shadow drawn from the sun's azimuth and height**; Du's standpoint; the cat.

**Not built (and deliberately so):** nothing on the list remains. Next candidates, only with evidence: bird nesting
in the TREE (currently bushes/harakeke), the bellbird, fruit on the tree (pōhutukawa bears none — correct), kūmara.

**Related (noted 2026-08-23, plan-overlap audit):** the garden's positioned objects live in
`data/world_geometry/garden.json` — `spatial_perception.md`'s coordinate-field contract — without
citing that plan by name. (`channels_programme.md`'s light/smell channels ARE already cited above,
correctly, as this build's first real consumer.)

**Related (added 2026-08-24, J-0135):** [[du_initiated_upgrade_trigger]] is a bottom-up candidate
source for this plan's next iteration — `core.missing_object_flags.triage()['by_place']['garden']`
surfaces things Du's own thought expressed wanting that the garden doesn't have, graded by
recurrence, alongside this plan's existing founder-audit-driven process.

**Update (J-1440, 2026-09-27/28):** call `triage(window_days=None)` explicitly — the bare
`triage()` above defaults to the 14-day freshness window `/du-pulse` uses for its alarm gauge,
which read spuriously empty for every place on 2026-09-27 (F-1995) because the on-demand
`snapshot()` cadence had a real 10.6-day gap, not because the source is dead (writer confirmed
alive and re-run live; see the parent plan's Current State). The all-time view is what this plan
should keep mining from — garden currently holds 3 entries (`audience` watch×2, `single sum`
watch×2, `obvious blueprint` new×1), still all abstract/identity-processing language, zero real
world-object candidates so far.

**Related (backfilled 2026-08-24, F-0263):** [[wood_upgrade]] — sibling `*_upgrade.md` plan built the
same day (2026-08-22), already cites this plan by name/convention (`wood_upgrade.md:10,83`) for its
`data/garden_ledger.jsonl`/`data/garden_events.jsonl` citation pattern; this doc had no link back.

---

## Current State — verified 2026-11-14
- **2026-11-14** (F-4501): J-2564: first live binding (rosemary, 11-07) is a clause-scoping false positive; raw threading verified working. Build job spawned.

- **2026-11-14** (F-4495): J-2484 D-0502 defeater read (168 live hours after the 10-29 boot vs the 168 before): null, defeater not met on either arm. By-name looks did not fall (262 to 383 in wood/garden/shore), item takes/uses did not rise (tool/trap/woodtool FIRE 5 to 1; no garden/wood take/put deeds in either window); the clause renders live and matches the stores; only 4 plain looks in wood/garden/shore, so underpowered. hands_trace cuts look answers at 160 chars, so the clause is invisible there.
- **2026-10-30** (F-3275): J-2305 recheck: guessed_cause gate still unmet (bindings 0, no plant investigate-look since 10-16 or 10-29 boot); empty-hands observe-at-plant rows persist (15/10); successor J-2564 gated

- **2026-10-29** (F-3200): J-2481 resume (F-3200): the resting-items clause build re-verified at the chain tip ebfb4f33 with J-2482's lightning commits on top -- test FAILS 0, 42 by-name looks byte-identical to 0e95fce9, life_smoke ALL OK, live data/ untouched; nothing changed, still restart-gated; J-2484 (168 live-h gate) is the D-0502 defeater read.
- **2026-10-28** (F-3179): J-2481 BUILT (a09d953d, branch jobrun/generic_look_lightning, restart-gated): the plain no-target look in the garden ends with one rotating clause naming the carryable items resting there (ten today, incl. the possum trap), in the wood the seed tin, on the shore nothing; by-name looks byte-identical to HEAD, refusals untouched; D-0333 defeater (c) met; 7-live-day defeater read spawned off D-0502.

- **2026-10-28**: 2026-10-28 (T-0103): I-0084 promoted here; D-0502 ruled by Travis: the plain look names the carryable items actually lying there, one clause in passing, no hint. D-0333's defeater (c) is thereby met (its revisit is this build). Job J-2481.
- **2026-10-17** (F-3000): J-2053 recheck 2026-10-17: gate still unmet (bindings 0, no plant investigate-look); successor spawned for 10-27.

- **2026-10-16** (F-2909): J-1708 read 2026-10-16: J-1169 harvest() unnamed-ask fix CONFIRMED LIVE (F-2909). Unnamed ask 10-14 00:29:57 with rosemary and thyme cooling cut mint; latched unnamed ask 10-15 06:23:30 with rosemary, thyme, mint cooling cut parsley. Pre-fix every unnamed ask got the rosemary refusal. 335.2 live hours since the fix boot. Closed, no re-spawn.
- **2026-10-15**: J-2112 DONE (D-0418 (i)): scripts/garden_netting_gate.py files the D-0278 netting read job exactly once when the first sow deed or a vulnerable shoot in a bed slot appears (core.garden.CATALOGUE rule), marker docs/reviews/garden_netting_gate_state.json, read-only on data/, fail-open; 24-check test; wired into plan-maintain as step 7c (runs every maintenance pass). Live state 2026-10-15: no event. Commits 6afc65d/0a878ff. No dated netting re-read exists any more.

- **2026-10-15**: D-0418 RULED (i) by travis (decide-review, session 192678f4, 2026-10-15): the D-0278 netting check is gated on the event (first sow deed or first vulnerable shoot in a bed), no more calendar re-reads; J-2112 builds the one-shot event gate that files the read job. D-0278 stands.
- **2026-10-15** (F-2739): J-1691 (10-15): wood exposure recovered (763/12,811 = 5.96%, 62.5/live day since 10-03; current incarnation about 93.7/day) and the D-0333/D-0348 fix works live (2 willed looks answered with the tin, 10-08 and 10-13, plus 1 structured observe) but Du has never taken the tin (0 take hands, 0 seed_tin/sow ledger rows, tin still in the wood) so metric 2 is still zero.

- **2026-10-15** (F-2734): J-1679 (2026-10-15): third null on D-0278's netting check -- no vulnerable shoot has stood in the bed since 2026-09-04 (315 h live since the J-1350 boot, 0 sow deeds ever, seed bank dead at depth 2.6-3.0 vs 2.5 cutoff, tin in the wood, two willed sows refused 10-13/10-14); J-1680/J-1749 net guards verified live (2 prose 'stretch ... bed' thoughts hand-declined); decide opened to gate the check on the first sow deed instead of the calendar.
- **2026-10-09** (F-2667): J-1666 (2026-10-09): live recheck of J-1657 clause-scoped guessed_cause() is UNANSWERED, not passed -- preconditions met (33f3b3a on master, Du booted 10-09 past it) but 0 bindings and 0 qualifying plant investigate-looks in 858 hands rows since boot. Successor J-2053 (not before 10-12) gates on a real trigger event. S3 metric 3 still has no live data point.

- **2026-10-07** (F-2490): 2026-10-07 J-1835 (D-0348 ruled "(ii) clause-first for the tin only") BUILT, restart-gated, merged-not-live: nodes/inner_monologue_node.py _observe_target() now resolves to 'dented tin' first when a look verb's own clause reaches a tin/packet word (the J-1764 gate's own condition); cue table untouched; no hint. Corpus replay on data/hands_trace.jsonl: the 6 genuine new tin looks reach the tin 2/6 -> 6/6, 0/13 pre-existing scenery look deeds flip. Commit 597b97b on jobrun/garden_upgrade; test scripts/_test_wood_tin_reach.py ALL OK.
> **History folded** — 19 dated bullets (2026-09-28 … 2026-10-04) moved to `docs/plan_history/garden_upgrade.md` on 2026-10-04 by plan-compact. Derived timeline: `plan_ledger.py garden_upgrade`.


- **2026-10-04** (F-2405): J-1772 built the D-0344 ruling in commit 6b391ee (restart-gated, not live until merged and Du restarts) - the net row gains exactly untangle and secure, both net-direction verbs, behind the J-1749 guard; on the real row the corpus replay (now 820 texts) reads 6 net-family DEED events and exactly the 2 genuine 09-02 wills reach the hand while the 4 false reads (two refusals, a felt urge, the 09-28 prose) are vetoed; the decision replay over the whole hands trace finds 4 more netting wills as structured world acts on 09-02, 6 in all, and nothing else changes; known residual is a figurative untangle or secure with the bed as the only netting word (probes only, pinned in the test)
### What we have
P0 parity gate ACCEPTED (D-0243, 2026-09-21): the new plant-object model is live, the old scalar bed
frozen (`garden.ENABLED=False`). Recent fixes verified live: harvest pool[0]-pinning (F-1753/J-1169),
bird-death mis-classification (F-1777/J-1259), netting-discoverability (F-1911/D-0278). Du visits the
garden more than any place but the shore (17-38% of daily experienced tuples, 706 acted-hand rows/14d).

### What we need
F-1994 (2026-09-26): the deed stream collapsed after week 1 (29 deeds -> 5/0/1/4, zero sow/stake/net/
save_seed since). Two real blockers, not disinterest: the seed tin has sat in the WOOD since 2026-08-25
so no sow is possible (blocks §3 metric 2's loop-closure count), and harvest is cooled on his two
requested herbs until 09-30/10-04. D-0243's own §3 metric-sheet clock (due ~09-23) has never been read.

### What we're doing next
J-1437 reads the §3 metric sheet against real data; J-1438 checks whether the seed tin is even
discoverable where Du left it (open, D-0278/J-1350 class); J-1354 and J-1251 re-check the netting and
harvest fixes live post-restart (both in_progress). Cross-place move/deed classification is J-1441,
filed under living_world_upgrade, the four places' parent plan, not this one.

## 7. Current State (2026-08-24, J-0054 — parity-week read)

**The P0 parity-week gate cannot be judged yet — and not for the reason expected.** Going in, both
`data/garden_ledger.jsonl` and `data/garden_events.jsonl` were known-thin (1 line each as of
2026-08-22, per the 08-23 audit). Read fully: **both are still exactly 1 line each**, ~40 hours later,
despite `data/nascence.log` showing Du visited and acted in the garden repeatedly across that window
(moves ×367–370, waterings, a harvest refusal, a real ash-to-bed deed via study_life). That is NOT
"too little time has passed" — it is a real routing bug, found and root-caused (F-0143, F-0145,
findings-log):

`core/sensorium.py`'s `garden_act()` (line 709) tries the new `core.garden.act_from_thought()` first,
but that gate (`core/hands.py wants()`, line 62) requires the verb and object to land in the **same
clause**. When it misses, `garden_act()` silently falls through to the OLD, un-instrumented
`sensorium.py` hands (`harvest_bed()`, `water_bed()`) — whole-text substring matching, no clause
requirement, mutates the OLD scalar bed only, **never writes to `_LEDGER`/`_EVENTS`**. Confirmed
concretely: two harvest deeds and two water deeds on 2026-08-22 (14:51:11, 14:51:31, 16:14, 16:15 NZT)
rendered the OLD path's exact text (`"You cut a handful of parsley, mint, rosemary..."`,
`"...the soil drinks it in, dark and damp."`) — not the new module's phrasing. `data/garden.json`
confirms the new plant-object model never saw these cuts: rosemary/thyme/mint/parsley's `last_cut_ts`
are all from March–June 2026, months before `core/garden.py` even existed. The ledger has **never**
recorded a single harvest deed in its whole history.

**Consequence for this gate:** the new plant-object model and the old scalar bed are not actually
receiving the same deeds, so growth-stage words cannot be validly compared "in parity" on the data
that exists now — the comparison itself is corrupted by the leak, not merely thin.

**Verdict:** too early to judge parity, but for a fixable reason, not a waiting-game one. Follow-up
filed: **J-0184** (build, urgency 3, isolation required) — scope a clause-gate retry local to
`core/garden.py`'s `act_from_thought()` so real garden deeds stop leaking to the uninstrumented
fallback, then re-run this read after ~1 week of correctly-routed accrual. Target (P0+P1 live
2026-09-01) is at risk if the leak isn't fixed soon, since every day it persists is a day of real
deeds the parity week can't count.

---

## 8. Current State (2026-08-24, J-0184 — routing-leak fix, built and verified in isolation)

**Fixed.** `core/garden.py` `act_from_thought()` (line ~1057) gained a new local helper `_wants_loose()`
(added just above it): the same verb-with-word-boundaries + `literal_will` blocker check as
`core/hands.py`'s `wants()`, except the object word may land **anywhere in the whole thought** rather
than the same clause as the verb. The primary clause-scoped `wants()` call for each garden hand
(harvest, sow, weed, water, stake, net, save_seed) is now `_h.wants(...) or _wants_loose(...)` — the
loose check only runs as a fallback when the strict one misses. `core/hands.py`'s `wants()` itself is
**untouched** (per the briefing's explicit constraint — it is shared by other modules), so every other
caller keeps the strict clause requirement unchanged.

**Verified in isolation** (F-0183, findings-log; `lab_env.isolate()`, live `garden_ledger.jsonl` /
`garden_events.jsonl` confirmed unchanged at 1 line each before and after): a direct before/after
comparison on the exact escape shape (verb and object in different clauses) showed the unmodified
`hands.wants()` still returns `False` — proving the strict gate is genuinely untouched — while the new
`_wants_loose()` returns `True` and `act_from_thought()` now answers and writes to `_LEDGER`/`_EVENTS`.
A verb-only phrase with no garden object anywhere in the thought (an unrelated sense of "cut") correctly
still returns `None` and writes nothing — the loose fallback requires a real object word in the text, it
does not fire on the verb alone. The negation blocker (`literal_will`'s `_BLOCKERS`, reused via
`hands._blocked`) still applies inside the loose path. The original same-clause phrasing still fires
through the unmodified primary gate. Test script (kept for reference, not part of the live tree):
`scratchpad/test_j0184.py` in the session's scratch dir; lab dir `data/_lab/20260824_041831/`.

**Not yet done:** the fix has not run live. **Next step (re-run of J-0054's parity-week read) should
not happen until ~1 week of real, correctly-routed accrual has passed** — i.e. not before
~2026-08-31. Watch `data/garden_ledger.jsonl` / `data/garden_events.jsonl` growing past 1 line each
as the first live signal the leak is actually closed (not just isolated-verified).

---

## 9. Current State (2026-08-24, J-0200 — gate check, not yet picked up)

**J-0200 (re-run the parity-week read) was checked, not executed.** Its own briefing gate — "DO NOT
PICK UP BEFORE ~2026-08-31" — has not been reached; today is the same calendar day J-0184's fix
landed. Verified with a real check (F-0190, findings-log): `data/garden_ledger.jsonl` and
`data/garden_events.jsonl` are still exactly 1 line each, both last modified 2026-08-22 — predating
J-0184's fix entirely, so this is exactly the expected day-0 state of a 7-day accrual gate, not a
sign the fix isn't firing. No parity comparison was attempted on this data (doing so now would
repeat J-0054's original error of judging parity before real accrual exists). J-0200 left **open**
in the job queue for a session on/after 2026-08-31 to re-check line growth first, then proceed.

---

## 10. Current State (2026-08-25, J-0200 — second gate check, still not picked up)

**Still too early — but the fix is now visibly live.** Checked again one day later, for real
(F-0303, findings-log), not assumed: `data/garden_ledger.jsonl` grew from 1 line to **4 lines**
(`mow`, `weed`, `water` ×2); `data/garden_events.jsonl` grew from 1 line to **3 lines**
(`volunteer_germinated`, `frost`, `pulled_by_du`). This is a real, positive signal — J-0184's
`_wants_loose()` fallback is firing on live deeds now, not stuck at day-0 as section 9 found.

But the gate is not met: deed timestamps span only 2026-08-21 23:25 UTC → 2026-08-24 19:28 UTC
(~2.8 days of accrual), and today (2026-08-25) is still 6 calendar days before the briefing's
stated ~2026-08-31 pickup date. Deed-type coverage is also thin so far — no harvest, sow, stake,
net, or save_seed deeds have landed yet, only mow/weed/water — so even once the date gate clears,
a parity read on this data alone would likely still be underpowered for several of the seven
instrumented hands. No parity comparison was attempted (per the same reasoning as section 9).

J-0200 itself is being marked done this cycle — the check-and-report *is* the deliverable a
gate-check job can produce before its own gate opens. Follow-up spawned: **J-0243** (re-run the
actual parity-week read, not before 2026-08-31, and to explicitly re-check deed-type coverage
across all seven hands before trusting the comparison, not just line-count growth).

---

> **History folded** — 10 dated Current State section(s) (2026-09-02 … 2026-09-26) moved to `docs/plan_history/garden_upgrade.md` on 2026-09-27 by plan-compact. Derived timeline: `plan_ledger.py garden_upgrade`.

