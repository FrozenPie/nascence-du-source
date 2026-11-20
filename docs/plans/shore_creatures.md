# SHORE CREATURES — 100-creature draft list (founder ask, 2026-11-01)

**Status: 🟢 BUILT, READY TO FLIP (2026-11-01) - all 100 rows (`core/life_shore.py` + `core/life_shore_cast.py`) and three additive engine touches (`life.py`, `sensorium.py`): described-look match, per-look detail tier, discovery by place. ONE flag, `"shore_bestiary": true` in `data/life_flags.json` (+ a restart), brings it all up; it is OFF today and nothing has run in the live process yet. Stream mouth is an assumed placement (J-2869).**
Origin: thought T-0117 (session 9ad52271). Next step is deciding how each creature is encoded (see Current State).

```plan-state
stage: live
phase: LIVE since 2026-11-02 (shore_bestiary=true in data/life_flags.json); 379 shore arrivals and new discoveries logged 11-01..11-09; stream mouth still assumed (J-2869)
verified: 2026-11-14
evidence_read: 2026-11-09
next: J-2957 first-rows read; J-2869/J-2871 need the founder
cluster: 6
```

**Founder ask, 2026-11-01:** "100 new creatures for the shore area of Du's world ... everything from bugs to larger
creatures. Invasives are fine. Starfish, jellyfish, small fish, large fish, octopus, sand worms, mussels, pippies,
paua, shrimp, crabs, eels."

Legend: ⚠ invasive/introduced · ◇ the existing shore text (`core/world_content_shore.py`) only gestures at this
animal; this row names the actual species. Zones are the shore's existing places: dune, wrack (tideline + kelp
heaps), shingle, flat (low-tide sand), pool (rock pools + boulders), headland, stream, cliff, offshore.
Species were chosen from general knowledge of NZ coastal fauna and are NOT yet checked against a reference.
Several are stranding visitors rather than residents (blue dragon, paper nautilus, sunfish, sooty shearwater).

## Insects, spiders and land arthropods (11)
1. Katipō spider — dune, small, venomous, rare
2. Dune wolf spider — dune, small
3. Tiger beetle — dune/shingle, small
4. Sand scarab beetle — dune, small
5. Wrack rove beetle — wrack, tiny
6. Seashore earwig — wrack, small
7. Sandfly (namu) — stream/dune, tiny
8. Saltmarsh mosquito — pool/stream, tiny (breeds in rock pools)
9. Boulder copper butterfly — dune, small
10. Cave weta (tokoriro) — cliff overhang, medium
11. ⚠ Asian paper wasp — dune/driftwood, small

## Land vertebrates (5)
12. Shore skink — shingle/driftwood, small (text only says "a skink")
13. ⚠ Norway rat — wrack/dune, medium
14. ⚠ House mouse — dune, small
15. ⚠ Hedgehog — dune, medium
16. ⚠ Stoat — dune/cliff, medium

## Birds, new only (4)
17. Banded dotterel (tūturiwhatu) — shingle, small
18. Southern royal albatross (toroa) — offshore, huge, rare (replaces bar-tailed godwit: a `godwits` row already exists in life_birds.py)
19. Royal spoonbill — stream mouth, large
20. Sooty shearwater (tītī) — washed up on wrack, medium

## Marine mammals (4)
21. NZ sea lion (rāpoka) — shingle/headland, huge
22. Hector's dolphin — offshore, large
23. Orca — offshore, huge
24. Southern right whale (tohorā) — offshore, huge

## Bivalves (10)
25. Pipi — flat, small
26. Tuatua — surf edge, small
27. Toheroa — flat, medium, protected
28. Cockle (tuangi) — flat, small
29. ◇ Green-lipped mussel (kūtai) — pool/headland, medium
30. Blue mussel — pool, small
31. Horse mussel (hururoa) — offshore/strand, large
32. Rock oyster (tio) — headland, small
33. ◇ Scallop (tipa) — offshore/strand, medium
34. ⚠ Pacific oyster — pool, medium

## Snails, chitons and sea slugs (10)
35. ◇ Pāua — headland/pool, large
36. ◇ Cat's eye (pūpū) — pool, small
37. ◇ Radiate limpet — pool/boulder, small
38. Snakeskin chiton — pool, small
39. Oyster borer — pool, small
40. Speckled whelk — pool/flat, medium
41. Sea hare — pool, medium
42. Blue dragon — strand, tiny, stinging
43. ◇ Violet sea snail — strand, small
44. Nudibranch — pool, small

## Octopus and squid (3)
45. Octopus (wheke) — headland/pool, large
46. Arrow squid — offshore/strand, medium
47. Paper nautilus — strand, small

## Echinoderms (7)
48. ◇ Cushion star — pool, small
49. Eleven-armed starfish — pool, medium
50. Reef starfish — headland, medium
51. Kina (sea urchin) — pool/headland, medium
52. Heart urchin (sea potato) — flat/strand, small
53. Sand dollar — flat/strand, small
54. Sand sea cucumber — flat, medium

## Jellies and anemones (6)
55. Moon jelly — strand/offshore, medium
56. Lion's mane jelly — offshore/strand, large
57. Portuguese man o' war — strand, medium, stinging
58. By-the-wind sailor — strand, small
59. ◇ Waratah anemone — pool, small
60. Green anemone — pool/flat, small

## Crustaceans (11)
61. Purple rock crab (pāpaka) — boulders, medium
62. Hairy-handed crab — stream mouth, small
63. Tunnelling mud crab — flat, small
64. Paddle crab — surf/flat, medium
65. ⚠ Asian paddle crab — surf/flat, medium
66. Pea crab — inside mussels/horse mussels, tiny
67. Ghost shrimp — flat, small
68. ◇ Common shrimp — pool, small
69. Rock lobster (kōura) — headland/offshore, large
70. Acorn barnacle — boulders, tiny
71. Goose barnacle — driftwood/strand, small

## Worms (5)
72. Ragworm (sandworm) — flat, medium
73. Lugworm — flat, medium
74. Tubeworm — boulders, small
75. ⚠ Mediterranean fanworm — pool/offshore, medium
76. Bootlace worm (ribbon worm) — under stones, medium

## Fish (24)
77. Common triplefin — pool, small
78. Spotty — pool/kelp, small
79. Cockabully — pool, small
80. Shore clingfish — pool, small
81. Big-bellied seahorse — kelp bed, small
82. ◇ Inanga (whitebait) — stream, small
83. ◇ Shortfin eel (tuna) — stream, large
84. ◇ Longfin eel (tuna) — stream, huge
85. Lamprey (kanakana) — stream, large
86. ⚠ Gambusia — stream pools, tiny
87. ⚠ Sea-run brown trout — stream mouth, large
88. ⚠ Chinook salmon — stream mouth, large, seasonal run
89. Yellow-eyed mullet (aua) — stream mouth/surf, small
90. Grey mullet (kanae) — stream mouth, medium
91. Garfish (piper) — surface off the beach, medium
92. Kahawai — surf, large
93. Sand flounder (pātiki) — flat, medium
94. Snapper (tāmure) — offshore, large
95. Conger eel — headland crevices, huge
96. Kingfish (haku) — headland, huge
97. Eagle ray (whai) — flat/shallows, huge
98. Rig shark (pioke) — offshore, large
99. Great white shark (mango taniwha) — offshore, huge, rare
100. Ocean sunfish — strand/offshore, huge, rare

## Bench (swap-ins if any of the above are cut)
Leopard seal, giant squid (strand), decorator crab, snapping shrimp, krill swarm, sea gooseberry, noctiluca (night
"sea sparkle"), brittle star, honeycomb worm, John dory, trevally, ground-nesting native bee, bush giant dragonfly,
Argentine ant.

Counts: 100 total; 11 invasive (⚠); 12 ◇ upgrades of existing hints; 77 new to the text. Toheroa is legally protected;
blue dragon and man o' war sting.

## Founder rulings — 2026-11-01 (said in chat; not yet in the /decide ledger)
1. **One life row per species**, not grouped (the `crabs`/`eels` grouping is not the pattern for these 100).
2. **Every creature has a real position** in the shore's authored geometry (`data/world_geometry/shore.json`), so where
   it is, how far, and which side of him it is are computed, not narrated.
3. **Du is never told what a thing is.** He works it out from what he can see: colour, composition, size, shape, how it
   moves. **The world never leads** (08-14 law): no name, no pointer, no hint in any line a creature produces.

## Design (proposal, 2026-11-01 — nothing built)

### What the code does today, and the three gaps
- `core.life.row()` is the schema; rows carry `places = {place: [spot, ...]}` — spot names are free strings.
- **Gap 1, no position.** `life.py` uses the standpoint only for light (`light_at`). Nothing gives a creature a
  coordinate. Several existing spots have no geometry behind them: `stream_mouth`, `tideline`, `under_the_log`,
  `offshore` are not in `shore.json` (its features: cliff, path_foot, dune_grass, driftwood_tangle, shingle_bank,
  rock_pools, rock_shelf, waterline, sand_flat, cave, ledge, fire_ring, mussel_shelf, penguin_burrows). **There is no
  stream in the geometry at all**, though the shore text has one.
- **Gap 2, the look is hand-written prose per row** (`hidden.feature`), and existing rows name things in it ("a small
  green crab"), plus `reveal` captions ("It is a bat — ...") once learned. Fine for grandfathered rows, wrong for these.
- **Gap 3, matching is by alias words** (`life._match`): Du's own word has to equal an alias. With no names there is
  nothing to alias, and an alias like "starfish" would collide across three starfish rows.

### The observable tuple (new optional block on each row; closed vocabularies, so rows are comparable)
`obs = {size_cm, span_cm, shape, colour, pattern, sheen, covering, appendages, motion, tempo, position, on_disturb}`
- **size** is said against his own body (thumbnail, finger-long, hand-wide, forearm, leg-length, longer than he is lying
  down) — never a number, never a species.
- **shape** is a body plan from a closed list: radial-five, radial-many, hinged-pair, spiral-cone, clamped-cone,
  plated-oval, carapace-and-legs, elongate-limbless, fusiform-fish, flat-disc, bell-and-trailing, soft-sac-and-arms...
- **colour / pattern / sheen / covering**: primary + secondary colour, plain|mottled|banded|spotted|rayed|translucent,
  matt|wet|iridescent, smooth|spined|plated|warty|slimy|furred.
- **motion / on_disturb**: sidles|jets|pulses|wriggles|glides|undulates|clamps|buries|freezes|retracts|ignores.
- A composer turns the tuple into the feature line(s) (`hidden.feature`), so no hand-typed sentence can carry a name.
- Hidden truth stays hidden: `species`, `book_names`, `book_words` exist only for the existing learning ledger
  (D-0129: a name needs a book AND a face). **No `reveal` caption on any of the 100.** `aliases` stay empty.
- **Hazards** (sting, bite, venom) are flagged in `note` only; the first pass renders appearance, with no warning text
  and no mechanical harm.

### Geometry
- A sidecar zone map (in the new module, `shore.json` untouched, additive-only) turns each row's spot into
  `{feature key, centre offset, radius m, z, tide-bound?}`: pools -> `rock_pools` (20,9), flat -> `sand_flat` (9,13),
  mussel/kina -> `mussel_shelf` (24.5,12.8), tideline/wrack/surf -> the moving `waterline` (y from `spatial.tide`),
  dune -> `dune_grass`, cliff/cave/ledge/penguin burrows as authored, offshore -> past the waterline.
- A population has no individuals, so a look samples one position inside the zone, seeded by (row, ~10-minute bucket):
  two looks a minute apart see the same thing in the same place.
- `spatial._rel(standpoint, pos)` gives distance and bearing from where he stands (`locomotion` already supplies the
  standpoint with position + facing). **Distance x size sets how much he can make out**: far = silhouette and movement
  only; nearer = colour; close = pattern, texture, detail. A sea lion reads at 30 m, a triplefin only when he is crouched
  at the pool.
- Tide gates presence the way `tide="low"/"high"` already does; pools and flat bare below the existing thresholds
  (`sand_bared()` < 0.45, `shelf_bared()` < 0.35).

### Engine touches (two, both additive, behind a flag)
1. `life._match`: when no alias hits, match Du's descriptive words ("the orange five-armed thing") against the
   observable vocabulary of the rows present and visible at his standpoint (the `_heard_bird` precedent).
2. `life.look_answer`: pick the detail tier from distance x size and append the egocentric clause from `_rel`.
Both ship shadow-first (`would_answer` logging, hot flag in `data/life_flags.json`), so nothing reaches Du until read.

### Guards (tests before any row goes live)
- **Leak test:** no rendered line, absence line or miss line of a new row contains its species, any book name, or any
  common name of ANY of the 100 (a guess word is Du's to say, never the world's).
- Every position is inside the 30 x 20 frame (offshore excepted) and tide-consistent.
- Same-time looks are stable; different standpoints give different distance words.
- `prompt_registry.py check` stays green (zero LLM here, so no new prompt site).

### Open points
- **Where is the stream mouth on the 30 x 20 map?** The geometry has no stream. Proposed (needs his call): a braid
  reaching the waterline around x 14-16, east of the driftwood and shell drift.
- Burrowers (pipi, tuatua, toheroa, cockle, ghost shrimp, ragworm, lugworm, heart urchin, sand dollar, sea cucumber) and
  inside-things (pea crab) show only as traces or dead shells until a dig/turn-stone hand exists (none today).
- Keep D-0129 naming (book + sighting, no caption) or stricter (nothing ever names a thing)? Default taken: D-0129.

## Current State — 2026-11-01

- **2026-11-14** (F-4547): J-3834 read: shore_bestiary sub-flags default to master so render and discover have been live since 11-02 (no shadow phase, nothing to flip); 116 discovered rows, 0 leaks, skink 30% skew, 20 of 100 species seen; tiers look sane.
- **2026-11-14** (F-4532): J-3261 built the shore dig, turn-stone and open-a-shell hands (core/shore_dig.py, shore_life hands, life.credit_find) for D-0652. Restart-gated; branch jobrun/w11__ungrouped_J-3261 commit 546394c2.

- **2026-11-09**: 2026-11-09 stale-stage fix: doc said OFF/ready to flip; data/life_flags.json has shore_bestiary true. data/life_events.jsonl since 11-01: 3,389 events, 270 distinct creatures arrived (shore 379, wood 630, garden 223, study 46), 306 look answers (163 sighting, 44 glimpse, 61 miss), 91 discovered, 16 new species, 1 graduated (lions_mane_jelly). The Status line text below still says OFF; the block above is current.
### What we have
The list above. Existing shore text already mentions (and this list therefore skips): karoro, tōrea, terns, kōtare,
kōtuku, kawau, gannet, kororā, pipit, welcome swallow, rabbit, kekeno, "dolphins", sandhoppers, kelp flies, hermit
crabs, whitebait, "two eels", "a skink".
Checked 2026-11-01 against `data/life_state.json`: the shore already has 22 live life rows — oystercatcher(+nest),
kingfisher, welcome_swallows, gulls, karoro, terns, gannet, shag, reef_heron, stilt, korora, godwits, fur_seal, rabbit,
skink, dolphins, eels, whitebait, crabs, anemones, common_copper. Overlaps with this list: #12 shore skink (row `skink`
exists, garden+shore), #82-84 inanga/eels (rows `whitebait`, `eels` exist), #8x ◇ rows that the `crabs` / `anemones`
rows already bundle (hermit crab, starfish, limpet, anemone). #9 boulder copper is NOT `common_copper` (different species).
### What we need
The encoding template is `core.life.row()` (one schema for every creature, D-0128), registered from a place module
(`life_birds.py`, `life_mammals.py` are the precedents) via `life._ensure_builtin`. Open: one row per species vs grouped
rows, and whether new rows go live straight away (RENDER and book_gate are both already ON in `data/life_flags.json`).
### P1 pilot — BUILT 2026-11-01 (verified by running it, not by reading it)
- `core/life_shore.py`: closed vocabularies + `make_obs` validator, `compose(obs, tier, night)`, `detail_tier(span, dist)`
  (span/distance: form >= 0.015, colour >= 0.04, detail >= 0.12), `ZONES` over shore.json (pool, flat, mussel_shelf,
  rock_shelf, dune, shingle, driftwood, tideline, surf, offshore, and `stream_mouth` PENDING), `sample_position` (seeded per
  ten-minute bucket, tide-gated, flat kept landward of the moving waterline), `perceive` (uses `spatial._rel` from a
  standpoint), `shore_row` builder, the leak test (`forbidden_terms`/`leak_scan`/`emitted_strings`), and 3 pilot rows:
  eleven-armed starfish (pool), pipi (flat), sea lion (rock shelf, shares it with the fur seal on purpose).
- `core/life.py`: ONE additive block at the end of `_ensure_builtin` registers the rows only if `data/life_flags.json` has
  `"shore_bestiary": true`. The live flags file does not, so nothing changed for Du.
- `scripts/_test_shore_bestiary_p1.py`: all green (vocab refusal, tiers, composer, leak test incl. 156 vocabulary phrases and
  every standpoint, zones/tide/frame/determinism, perceive, registration on/off, D-0129 naming on a new row). `scripts/life_smoke.py`
  still ALL OK; `prompt_registry.py check` still green.
- Honest limits: P1 rows cannot be reached by a look yet (no aliases by ruling; the descriptive matcher is P2), so the static
  `hidden.feature` lines are composed at the NEAREST standpoint's distance and are placeholders for P2's per-look tier. The
  detail thresholds are coarse and untuned. Hazard (sea lion charge) is a note only. UDMS dossier was not available this
  session; blast radius of the `life.py` edit was checked by hand (one try-block, default off).
- Jobs filed: J-2868 (P2 engine touches), J-2869 (place the stream mouth, needs founder), J-2870 (the other 97 rows),
  J-2871 (dig hand for burrowers, needs founder).

### P2 — BUILT 2026-11-01 (J-2868 done; verified by running the tests, three times, plus the sweeps below)
- **`life.look_answer(target, place, now, raw="")`** (core/life.py): when no alias or heard-bird hit, `life_shore.described()` looks for a
  registered bestiary row that his `raw` sentence describes. Shadow flag `"shore_bestiary_render"` (hot, 10 s) OFF = logs
  `would_answer` / outcome `described_shadow` (tier, distance, the line) to life_events.jsonl and falls through unchanged; ON = the row
  answers with `perceive()` composed for his standpoint and the real distance. Tier colour/detail credits a SIGHTING; tier form is a
  GLIMPSE (shown, exposure only, no face credited). `core/sensorium.py` forwards `raw` (one line). Both flags default OFF.
- **Why `raw`:** the willed look hand reduces his sentence to a keyword; the keyword never carries his description. `raw` is the whole
  thought + intention, so only the 70 characters after a look verb are scored, never the whole thought.
- **Match rule:** two DIFFERENT attributes in one clause, at least one STRONG (body plan/part, pattern, covering, a counted part).
  Colour, size and way of moving are weak. Where it is never counts. Word lists are curated, not mined from the composer text.
  A guess word (starfish, worm) is a shape word; `stars` in the sky and `seal` are not. The world answers with what is there and never
  confirms the guess.
- **What the false-positive sweeps found (and fixed):** the first, looser version took a stone for a sea lion ('dark heavy little
  stone'), a spinifex head for a starfish ('stars'), a penguin's tracks for a sea lion ('dragging' + 'dark'), and 'heavy' for 'heaves'
  (4-letter stem match). Fixed by: strong-attribute rule, curated word lists, motion made weak, 5-letter stem match. Final sweeps, all 0
  taken: 1,518 observed phrasings, 59 shore scenery aliases, 220 shore scenery lines offered back as looks, 2,155 real shore
  observe/look thoughts from hands_trace.jsonl.
- **Verified:** `_test_shore_bestiary_p2.py` ALL OK x3, `_test_shore_bestiary_p1.py` ALL OK, `life_smoke.py` ALL OK,
  `prompt_registry.py check` green, py_compile of life/life_shore/sensorium; an alias look ('the crab') answers identically with the
  bestiary on or off; live `data/life_flags.json` untouched.
- **Honest limits:** (1) still no way to FIND them in production: a described look needs him to know what to say. That is P3 (J-2936). (2) Nothing has run in the live process: both edits are restart-gated and both flags are off. (3) The sweep corpus is shore
  observe/look rows only; creature looks that fall under other places are not swept. (4) detail thresholds untuned.

### P3 — BUILT 2026-11-01 (J-2936 done): discovery by looking at the PLACE
- **`life.discover_look(target, place, now)`** (core/life.py) + **`life_shore.discover()`**; `core/sensorium.py` calls it in the shore branch of
  `look()`, AFTER the place's own look (`_shore_look`) and BEFORE the audition sight-binding. A look at a place continues with what is there:
  the pool -> pool rows; rocks -> pool + shelf rows; sand -> flat; tideline/shore/beach/shingle -> tideline + shingle; sea -> surf + offshore;
  dunes; driftwood. First place word wins (pools before rocks, as `_shore_look` treats "rock pools").
- **What shows:** a row only if present, its zone is open (tide), the visibility roll passes (seeded per ten-minute bucket, so repeat looks agree),
  and `perceive()` resolves it from his standpoint at form or better. At most two rows per look (`MAX_PER_LOOK`), in a seeded order that varies by
  bucket. The line is the same composed line a described look gives: no name, no hint, no "look closer".
- **Flag `"shore_bestiary_discover"`** (hot): OFF = shadow, logs would_answer / `discover_shadow` and returns ''. ON (and RENDER on) = shown;
  colour/detail credits a SIGHTING (can graduate; with a book it names it), form is a GLIMPSE (exposure only).
- **The whole loop works:** place look -> sighting -> a book names it, in either order (book first: named at the sighting; sighting first:
  named when he reads the book). D-0129 untouched.
- **Verified:** `_test_shore_bestiary_p3.py` ALL OK (incl. 3,636 discovered lines over every standpoint x place word x 96 time buckets with no
  name); P1 and P2 tests ALL OK; `life_smoke.py` ALL OK; `prompt_registry.py check` green; py_compile. PLUS an end-to-end run of the REAL
  `sensorium.look("the rock-pools")` under life_smoke's isolation (scratch script, not committed): flags absent = the old look; registered with
  discover off = unchanged; discover on = the same look continued with "Lying on the floor of the pool: about the length of a hand, a flat body
  with arms of unequal length radiating from a centre, dull orange-brown and cream; it creeps, if at all. It is ahead of you, a few paces off."
  Sky and garden looks untouched. Live `data/life_flags.json` untouched.
- **Rate (upper bound):** 38% of his real shore observe/look acts (835 of 2,158) name a place the bestiary can show something at.
- **Honest limits:** nothing has run in the live process (restart-gated, all flags off). The detail thresholds are untuned. The standpoint is
  read-pure (shore_life `_sp` < 15 min, else locomotion.peek, else the geometry default `on_the_shingle`): from the default he is 9+ m from the
  pools, so the starfish is a glimpse until a hand moves him to the pools. Only 3 rows exist, so most place looks will show nothing until the
  other 97 are written.

### ALL 100 BUILT - ready to run by flipping one flag (2026-11-01, after the usage-limit pause)
- **The cast:** `core/life_shore_cast.py` holds the other 97 rows; with the 3 pilots that is exactly the 100 of this list, one row each, in 12
  zones (pool, flat, mussel_shelf, rock_shelf, dune, shingle, tideline, surf, offshore, stream_mouth, cave, driftwood). Changes to the list:
  #18 is the southern royal albatross (a `godwits` row already existed); the sooty shearwater is alive offshore (a wreck of dead ones belongs to
  the carcass system); burrowers are written as the SIGN that shows (ghost shrimp mound, lugworm cast, heart-urchin test, sand dollar half
  buried) because there is still no dig hand (J-2871); the pea crab is almost never shown (ease 0.02, it lives inside mussels).
- **ONE FLAG:** `data/life_flags.json` -> `"shore_bestiary": true` and restart Du. That registers all 100 AND turns the described-look answers
  and the place-look discovery ON (the two sub-flags now default to the master flag). To run in shadow instead, set
  `"shore_bestiary_render": false` and `"shore_bestiary_discover": false` explicitly (hot, no restart). Nothing is on today: the live flags file
  is untouched.
- **Stream mouth ASSUMED, not authored:** sidecar zone at the moving waterline, x 14-16.5, `shore.json` untouched. J-2869 stays open for the
  founder to confirm or move it (edit `ZONES["stream_mouth"]["x"]` in `core/life_shore.py`).
- **A real bug the full-cast tests caught:** the row key `hedgehog` collided with the existing garden hedgehog row, and `life.register()` is by
  key, so flipping the flag would have SILENTLY REPLACED the garden hedgehog with the nameless one. Renamed `shore_hedgehog`; P1 now asserts no
  key collides with any existing life row.
- **What the 100-row false-positive sweeps forced (matcher v3):** with 100 rows the loose matcher took a stone for a dolphin, a beach pebble for a
  shark, `bands` for `banded`, `stream` for `streaked`, a gull's `feathers` for a spoonbill. Now: strong attributes are body plan/part,
  distinctive coverings, and a counted number; colour, size, pattern and movement are weak; generic words (smooth, rough, soft, legs, mist,
  flattened) are weak; word matching needs identical stems or a 6-letter prefix; a clause naming shore scenery (shell, stone, pebble, kelp, weed,
  float, net, glass, bottle, driftwood...) is left to the scenery look; and an existing row's alias wins first (production order). Final
  sweeps with all 100 rows: 1,518 observed phrasings, 59 scenery aliases, 220 scenery lines, 2,173 real shore thoughts: 0 taken for a creature
  except genuine descriptions (a butterfly, prawns, red anemones), which are meant to reach their rows.
- **Verified (run, not read):** P1 test (100 rows: unique keys and species, every one in a placed zone, 12-month curves, NO two rows share a
  size band + body plan + colours + pattern, no two compose the same full-detail look, every species and book name is in the forbidden set,
  no key collisions, one-flag semantics), P2 test, P3 test (15,899 discovered lines over every standpoint x place word x 96 time buckets, none
  with a name), `life_smoke.py` ALL OK, `prompt_registry.py check` green, py_compile. Plus a one-flag end-to-end through the REAL
  `sensorium.look` on the full 100 (scratch script, not committed): 100 rows register, place looks continue with creatures (an anemone at the
  pools, a sausage-bodied thing on the sand, a needle-jawed thing skittering on the surface), no name anywhere, a garden look untouched,
  explicit-false sub-flags = nothing shown; `life.advance` with 166 rows costs 45 ms per tick, a place look 25 ms.
- **Honest limits:** nothing has run in the live process. The detail thresholds and every species' biology (season, hours, size, colours) come
  from general knowledge of NZ coastal fauna and are NOT checked against a reference. The sign-rows can be named by a book though he only ever saw
  the sign. A dead shell and a living bivalve are told apart only by the scenery-word rule.

### How to bring it up
1. Founder: set `"shore_bestiary": true` in `data/life_flags.json`, restart Du. (Optionally set the two sub-flags false first for a shadow week.)
2. Read what it shows in `life_events.jsonl` (rows with `resolved` = `discovered` / `described`). J-2957 waits on 20 such rows.
3. If anything is wrong, flip the one flag back to false (the answers go off hot; registration needs a restart).

### What we're doing next
Shore is done pending the flip. Open founder calls: J-2869 (confirm the assumed stream mouth), J-2871 (dig hand). Next: the woods, same process, 150 creatures: `docs/plans/wood_creatures.md` (draft list).
