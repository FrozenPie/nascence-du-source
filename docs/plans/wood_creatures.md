# WOOD CREATURES — 150-creature draft list (founder ask, 2026-11-01)

**Status: 🟢 ALL 150 BUILT, READY TO FLIP (2026-11-02) - the 5 pilots (`core/life_wood.py`) and the other 145 (`core/life_wood_cast.py`), on the shore's engine. ONE flag, `"wood_bestiary": true` in `data/life_flags.json` (+ a restart), brings it all up; it is OFF today and nothing has run in the live process. The stream, canopy, trunk and groves are ASSUMED placements and the island is unknown (J-3065).**
Origin: founder ask 2026-11-01, sibling of the shore list (no thought id yet). Next step is the same decision as the shore: how each creature is encoded, plus the stream question below.

```plan-state
stage: live
phase: LIVE since 2026-11-02 (wood_bestiary=true in data/life_flags.json); 630 wood arrivals logged 11-01..11-09, first discoveries (harrier, whitehead); stream/canopy/trunk/groves placements still ASSUMED
verified: 2026-11-14
evidence_read: 2026-11-09
next: J-3065: confirm assumed placements, island, turn-stone hand
cluster: 6
```

**Founder ask, 2026-11-01:** "150 new creatures for the woods area of Du's world ... everything from bugs to larger
creatures." Invasives are fine; weird is fine as long as it is real and plausible for NZ native bush, a coastal forest
margin and a small freshwater spring-and-stream. Southern-hemisphere seasons.

Legend: ⚠ invasive/introduced · ◇ an existing grouped wood row (`ground_beetle` "the beetles", `cicada`, `weta`) or the
existing wood text (`world_content_wood.py` / `wood_life.py`: "beetle-galleries", "snapped snail shells") only gestures
at this animal; this row names the actual species · † needs a stream the geometry does not have (see Open points; the
creature is parked at `the_spring` for now). Zones are the features of `data/world_geometry/wood.json`: the_path,
canopy, undergrowth, leaf_floor, the_old_oak, deadfall, sea_gap, clearing, the_spring.
Species were chosen from general knowledge of NZ bush and fauna and are NOT yet checked against a reference. Te reo names
are given only where I am fairly sure of them and are also unchecked; many creatures simply have none listed. Several
entries are regional (North Island or South Island only) and are noted; the files do not say which island the cottage is on.

## Beetles and weevils (14)
1. ◇ Huhu beetle — deadfall/the_old_oak, medium, nocturnal, comes to the lamp; its grub lives in dead wood
2. ◇ Native longhorn beetle — deadfall, small, nocturnal
3. ◇ Forest ground beetle (large, black) — leaf_floor, medium, nocturnal
4. Native stag beetle — deadfall/leaf_floor, small, rare, nocturnal
5. Click beetle — undergrowth, small
6. Pie-dish beetle — deadfall (under bark), small
7. Giraffe weevil — the_old_oak/deadfall, medium, rare, North Island
8. ⚠ Clover root weevil — clearing, tiny
9. Bracket-fungus beetle — deadfall, tiny
10. Manuka beetle — clearing/canopy, small, seasonal (summer swarms on the white-flowering trees)
11. Grass grub beetle — clearing, small, seasonal, comes to the lamp
12. Darkling beetle — leaf_floor, small
13. Native dung beetle — leaf_floor, small
14. ⚠ Black pine bark beetle — deadfall, tiny

## Moths, butterflies and caterpillars (14)
15. Red admiral (kahukura) — clearing, medium, seasonal
16. Forest ringlet — undergrowth, medium, shade-loving butterfly, summer
17. Southern blue — clearing, small
18. Convolvulus hawk moth — clearing/canopy, large, nocturnal, summer migrant
19. ⚠ Emperor gum moth — canopy, large, nocturnal, seasonal, northern North Island
20. Porina moth — clearing, medium, nocturnal, seasonal (autumn)
21. Scoparia moth — the_old_oak (moss and lichen), tiny
22. Native leafroller moth — undergrowth, small
23. ⚠ Light-brown apple moth — undergrowth, small
24. Bagworm (case moth) — undergrowth/the_old_oak, small; the silk bag hangs from twigs
25. Looper moth — canopy, small, nocturnal
26. Cutworm caterpillar — leaf_floor, small, nocturnal
27. Armyworm caterpillar — clearing, small, nocturnal, seasonal
28. Looper (stick) caterpillar — undergrowth, small, holds itself out like a twig

## Flies and midges (9)
29. Bluebottle (blowfly) — deadfall, small
30. Crane fly — leaf_floor, small
31. Bush mosquito (waeroa) — undergrowth, tiny, dusk
32. ⚠ Striped mosquito — the_old_oak (water in a tree hole), tiny, dusk
33. Hoverfly — clearing, small
34. Fungus gnat — leaf_floor, tiny
35. Non-biting midge swarm — clearing/the_spring, tiny, seasonal
36. Robber fly — clearing, medium
37. Long-legged fly (metallic green) — the_spring†, tiny (wet moss and stones)

## Bees, wasps and ants (8)
38. ⚠ German wasp — leaf_floor/deadfall (ground nests), small, stinging, seasonal (late summer to autumn)
39. ⚠ Common wasp — canopy/leaf_floor, small, stinging, seasonal
40. ⚠ Australian paper wasp — undergrowth, small, stinging
41. ⚠ Potter wasp — the_old_oak (mud pots on bark), small
42. Giant ichneumon wasp — the_old_oak/deadfall, medium, harmless (long egg-laying tail)
43. Spider-hunting wasp — leaf_floor, small
44. Small black native ant — leaf_floor, tiny
45. Hunter ant (ponerine) — deadfall (under logs), small, slow, stings

## Cicadas, wētā, stick insects and other insects (16)
46. ◇ Chorus cicada (kihikihi) — canopy, small, summer, loud
47. ◇ Clapping cicada — the_old_oak/canopy, small, summer, claps its wings
48. ◇ Tree wētā (wētā-punga) — the_old_oak (bore-holes), medium, nocturnal
49. ◇ Ground wētā — leaf_floor, medium, nocturnal
50. ◇ Forest cave wētā (tokoriro) — deadfall, medium, nocturnal; a different species from the shore's cave wētā
51. Smooth stick insect — undergrowth, medium, nocturnal
52. Prickly stick insect — undergrowth, medium, nocturnal
53. Praying mantis — clearing, medium
54. Native cockroach — leaf_floor, small, nocturnal
55. ⚠ European earwig — deadfall, small, nocturnal
56. ⚠ Common katydid — undergrowth, medium, nocturnal, northern North Island
57. Native green shield bug — undergrowth, small; smells when handled
58. ⚠ Passionvine hopper — clearing/undergrowth, small, summer swarms
59. Brown lacewing — undergrowth, small, nocturnal
60. Springtail — leaf_floor, tiny, springs when disturbed
61. Dampwood termite — deadfall (inside rotting wood), tiny

## Dragonflies and damselflies (4)
62. Bush giant dragonfly — clearing/the_spring†, large, summer
63. Yellow-spotted dragonfly — clearing, medium, summer
64. Red damselfly — the_spring†, small, summer
65. Blue damselfly — the_spring†, small, summer

## Spiders and harvestmen (10)
66. Nursery web spider — the_spring†, medium
67. Sheet-web spider — undergrowth, medium
68. Tunnelweb spider — leaf_floor (silk tunnel under logs and bank), medium, venomous (mild), North Island
69. Trapdoor spider — leaf_floor (bank above the spring), medium, rare
70. Jumping spider — the_old_oak (bark), small
71. Crab spider — clearing (foxglove flowers), small
72. ⚠ White-tailed spider — leaf_floor/deadfall, small, wandering, nocturnal
73. ⚠ Daddy-long-legs spider — deadfall/the_old_oak (under bark), small
74. Long-legged harvestman — leaf_floor/undergrowth, small
75. Mite harvestman — leaf_floor, tiny

## Millipedes and centipedes (4)
76. Native millipede — leaf_floor, small
77. Flat-backed millipede — deadfall, small
78. Giant centipede — deadfall, medium, nocturnal, venomous bite
79. Stone centipede — leaf_floor, small, nocturnal

## Snails, slugs and worms (8)
80. ◇ Native carnivorous snail — leaf_floor, medium, nocturnal (the empty shells are what the text shows)
81. ◇ Small native land snail — leaf_floor, tiny
82. ⚠ ◇ Garden snail — the_path/undergrowth, small, nocturnal
83. Leaf-veined slug — undergrowth, small, nocturnal
84. ⚠ Keeled slug — leaf_floor, small, nocturnal
85. ⚠ Leopard slug — deadfall, medium, nocturnal
86. Native earthworm (noke) — leaf_floor, medium, surfaces after rain
87. Land flatworm — leaf_floor (under logs), small, nocturnal

## Odd and wonderful (5)
88. Peripatus (ngaokeoke) — deadfall (under rotting logs), small, rare, nocturnal
89. Pseudoscorpion — leaf_floor, tiny
90. Horsehair worm — the_spring†, small, rare
91. Barklouse — the_old_oak (bark), tiny
92. Vegetable caterpillar (āwheto) — leaf_floor, small, rare, seasonal (a caterpillar with a fungus stalk out of its head)

## Freshwater: the spring and its stream (17)
93. Freshwater crayfish (kōura) — the_spring†, medium, nocturnal
94. Banded kōkopu — the_spring†, medium, dusk
95. Koaro — the_spring†, small, climbs wet rock
96. Common bully (toitoi) — the_spring†, small
97. Redfin bully — the_spring†, small
98. Freshwater mussel (kākahi) — the_spring†, medium, half-buried in silt
99. Freshwater limpet — the_spring†, tiny, rare, North Island, glows when disturbed at night
100. Mud snail — the_spring†, tiny
101. ⚠ Bladder snail — the_spring†, tiny
102. Mayfly nymph — the_spring†, tiny
103. Stonefly nymph — the_spring†, small
104. Cased caddisfly larva — the_spring†, tiny
105. Backswimmer — the_spring†, small
106. Pond skater — the_spring†, small
107. Diving beetle — the_spring†, small
108. Freshwater amphipod — the_spring†, tiny
109. Freshwater shrimp — the_spring†, small

## Lizards and frogs (9)
110. Green gecko (moko-kākāriki) — undergrowth, small, rare, protected, diurnal
111. Forest gecko — the_old_oak (bark), small, nocturnal
112. Copper skink — leaf_floor, small
113. Ornate skink — deadfall, small, rare
114. Brown skink (moko-pāpā) — leaf_floor, small
115. ⚠ Rainbow skink — the_path, small
116. Hochstetter's frog (pepeketua) — the_spring†, small, rare, protected, nocturnal, North Island
117. ⚠ Southern bell frog — the_spring†, small, nocturnal
118. ⚠ Brown tree frog — undergrowth (near the spring), small, nocturnal, calls after rain

## Birds, new only (22)
119. Kākā — canopy, large, rare
120. Red-crowned parakeet (kākāriki) — canopy, small, rare
121. Brown kiwi — leaf_floor/undergrowth, large, rare, protected, nocturnal
122. Tomtit (miromiro) — the_path/undergrowth, small
123. Whitehead (pōpokatea) — canopy, small, North Island, flocks
124. Long-tailed cuckoo (koekoeā) — canopy, medium, rare, summer visitor
125. ⚠ Chaffinch (pahirini) — the_path, small
126. ⚠ Dunnock — undergrowth, small
127. ⚠ Goldfinch — clearing, small
128. ⚠ Greenfinch — clearing/canopy, small
129. ⚠ Common redpoll — clearing, small
130. ⚠ Yellowhammer — clearing, small
131. ⚠ Australian magpie (makipai) — clearing, medium, swoops at nest time (spring)
132. ⚠ Indian myna — the_path/clearing, medium, northern North Island
133. ⚠ California quail — undergrowth, small
134. Pūkeko — clearing, large, edge visitor
135. Harrier (kāhu) — sea_gap/clearing (overhead), large
136. NZ falcon (kārearea) — canopy, medium, rare, protected
137. ⚠ Eastern rosella — canopy, medium, northern North Island
138. ⚠ Spotted dove — the_path, medium, northern North Island
139. ⚠ Ring-necked pheasant — clearing/undergrowth, large
140. ⚠ Barn owl — canopy, medium, nocturnal, northern North Island

## Mammals, new only (10)
141. ⚠ Stoat (hākuturi) — undergrowth/deadfall, medium
142. ⚠ Ferret — undergrowth, medium, crepuscular
143. ⚠ Weasel — leaf_floor, small
144. ⚠ Ship rat — canopy/the_old_oak, medium, nocturnal
145. ⚠ Feral cat — undergrowth, medium, nocturnal (not Du's household cat)
146. ⚠ Red deer (tia) — clearing, huge, crepuscular
147. ⚠ Feral pig (poaka) — leaf_floor, large, digs up the mould
148. ⚠ Feral goat — clearing/deadfall, large
149. ⚠ Brown hare — clearing, medium
150. Short-tailed bat (pekapeka-tou-poto) — canopy/leaf_floor, small, rare, protected, nocturnal

## Already registered (skipped)
Rows with a `"wood"` place today (all live in `data/life_state.json`): blackbird, bellbird (alias korimako), riroriro,
fantail (alias pīwakawaka), shining_cuckoo, kereru, morepork (alias ruru), robin (toutouwai), wren (aliases rifleman,
titipounamu), possum, mice, long_tailed_bat, eels, ground_beetle ("the beetles"), cicada ("the cicadas"), weta ("the
wētā"), glowworms, kereru_nest. Their spot names are free strings (leaf_litter, bark, deadfall, canopy, canopy_edge, oak,
path, trunks, undergrowth, stream, spring), not wood.json feature keys.
◇ rows above are species of the three grouped rows (`ground_beetle`, `cicada`, `weta`) or of what the wood text only
gestures at (beetle-galleries, snapped snail shells). The `eels` row is not upgraded here (shortfin and longfin are
already #83 and #84 of the shore list; one row per species, so the wood would only gain a place on those rows).
Skipped, not counted: rows that exist but with no wood place — tūī, tauhou (silvereye), song_thrush, starlings,
house_sparrows, hedgehog, rabbit, skink, gecko, bumblebee, honeybee, native_bee, cabbage_white, yellow_admiral, monarch,
common_copper, magpie_moth, ladybird, aphids, ants, garden_spider, cricket, slugs, earthworms, slaters. Giving any of
them a wood place is a separate, small change to an existing row, not a new row.
Also skipped as shore duplicates (the wood has no species of its own): sandfly (namu), Norway rat, house mouse, katipō.

## Bench (swap-ins if any of the above are cut)
Giant wētā (island or translocated populations only), tusked wētā, brown creeper (pīpipi, South Island), pūriri moth
(needs a pūriri tree), kauri snail (Northland only), Pacific rat (kiore), dama wallaby, fallow deer, tardigrade (needs a
lens), land ribbon worm, wild turkey, paradise shelduck (pūtangitangi), giant kōkopu, torrentfish, oak gall wasp.

Counts: 150 total; 43 invasive (⚠); 11 ◇ upgrades of existing hints (#82 is also ⚠); 97 plain new species. Groups: beetles and weevils 14,
moths/butterflies/caterpillars 14, flies 9, bees/wasps/ants 8, cicadas/wētā/other insects 16, dragonflies 4, spiders
10, myriapods 4, snails/slugs/worms 8, odd 5, freshwater 17, lizards/frogs 9, birds 22, mammals 10. The wasps (#38-41),
hunter ant (#45), giant centipede (#78) and tunnelweb spider (#68) are the ones with a sting or bite worth a note
(white-tailed spider #72 has the reputation only); kiwi, kārearea, green gecko, Hochstetter's frog, short-tailed bat and peripatus are
protected.

## Founder rulings — 2026-11-01 (the shore rulings, restated for the wood; said in chat; not yet in the /decide ledger)
1. **One life row per species**, not grouped (the `weta`/`ground_beetle`/`cicada`/`eels` grouping is not the pattern for these 150).
2. **Every creature has a real position** in the wood's authored geometry (`data/world_geometry/wood.json`), so where it
   is, how far, and which side of him it is are computed, not narrated.
3. **Du is never told what a thing is.** He works it out from what he can see: colour, composition, size, shape, how it
   moves. **The world never leads** (08-14 law): no name, no pointer, no hint in any line a creature produces.

## Open points
- **Where is the stream?** `wood_life.py` says the spring "runs into a STREAM down the gully to the shore", the eels row
  has a `stream` spot, and the wood text mentions the gully, but `wood.json` has only `the_spring` (a pipe in the bank at
  4, 14). Entries marked † (#37, 62, 64, 65, 66, 90, 93-109, 116, 117) are parked at `the_spring` and are PENDING a
  stream feature. I have not invented coordinates. Proposed (needs his call): a braid running from the spring down the
  gully toward the sea_gap. Same question as the shore's J-2869.
- **No canopy layers or trunk zone.** `canopy` is one point (10, 10, 8). There is no understorey, no epiphyte or
  tree-fern-crown zone, no "on the trunk" zone, and no wet seep or rock face. Bark, trunk and moss creatures are all
  parked at `the_old_oak` or `deadfall`. PENDING.
- **The groves are not zones.** The kānuka grove (12, 6), tōtara (16, 13), tree-ferns (3.5, 15.5) and the fallen
  macrocarpa (1.5, 17.5) have positions in `wood_life.py` `TREES` but are not features in `wood.json`; the manuka beetle,
  green gecko, kākā, parakeet and others would sit better there. PENDING; used `clearing`/`canopy`/`undergrowth` instead.
- **No pool or open water** other than the spring pipe, so the dragonflies, damselflies, backswimmer, pond skater and
  amphibians depend on the same stream question.
- **Cannot be seen without a hand** (a dig, turn-stone or peel-bark act, or a lens; none exists today): #49, 54, 60,
  61, 68, 69, 75, 76, 79, 84, 86, 87, 88, 89, 92, 98, 100, 102-104, 108, 109 (turned stone or lifted bark, or in the
  silt), #21, 91 (a lens), #1, 2, 6, 9, 14 (traces and galleries until bark is peeled), #121 (heard or tracked, rarely
  seen), #31, 144, 145 (night only).
- **Island.** The files do not say which island the cottage is on. North-Island-only entries: #7, 19 (northern), 56, 68,
  99, 116, 123, 132, 137, 138, 140. The bench has the South Island ones (brown creeper). Founder to say, or the regional
  ones are dropped.
- **I was not sure of** (included, but check before building): land flatworm #87; horsehair worm #90; trapdoor spider
  #69; native stag beetle #4; pie-dish beetle #6; mite harvestman #75; dampwood termite #61; ornate skink #113 on a
  coastal margin; forest ringlet #16; hunter ant #45; giraffe weevil #7 outside Northland; freshwater limpet #99; every
  te reo name. Left out because I was not sure: leeches (no bush species that bites people that I am confident of),
  mainland giant and tusked wētā, tuatara (mainland-extinct, per the brief), kea.
- **Du's own cat** is the `cat` row (garden/study); #145 is a different, wild animal, and the row names must not collide.
- **Pūkeko, kāhu, kārearea** (#134-136) are visitors to the edge, not residents of a small wood; kept on the founder's
  list but worth a presence-gate when rows are written.

## Pilot BUILT - 2026-11-02 (J-3062 steps 1-2 and a 5-row slice of step 3; verified by running it)
- **The shore engine takes a place now.** `core/life_shore.py` has a `PLACES` registry; `sample_position`, `perceive`, `discover`, `described`,
  `current_standpoint`, the flags and the scenery words are all per place, and the shore registers itself as one place. The shore's behaviour is unchanged:
  its P1, P2 and P3 tests (100 rows) all still pass. `place_row(place, ...)` is the generic row builder (`shore_row` is a wrapper).
- **3D.** A creature eight metres up a tree is not as near as its ground distance says: `perceive` now uses `dist3` for the detail tier and the pace word,
  says "and up above" when the creature is 3 m or more above his eyes, and says its tone against "the leaves" or "the sky" or "the water" instead of always
  "the ground". `dist` stays spatial's own 2D figure.
- **`core/life_wood.py`** (new): 14 zones over `wood.json` features (the_path, leaf_floor, undergrowth, the_old_oak, deadfall, sea_gap, clearing, the_spring,
  canopy) plus sidecar zones, ALL marked ASSUMED where wood.json is silent (and `wood.json` is untouched): **stream** (a segment from the spring (4,14) to
  (12.5,19.2)), **canopy** (disc radius 6 at 5-9 m), **oak_trunk** (0.5-5 m), **kanuka_grove / totara_grove / tree_ferns** (positions from `wood_life.TREES`;
  radii and heights assumed). `TARGET_ZONES` map the words of a place look (canopy, leaves, up, stream, spring, oak, moss, deadfall, undergrowth, litter,
  clearing, gap, path, birds) to zones, first match wins.
- **Flags:** `"wood_bestiary": true` registers the wood's rows and turns its described-look answers and place-look discovery on with it (one flag);
  `"wood_bestiary_render": false` / `"wood_bestiary_discover": false` = shadow. The shore flag and the wood flag are independent (tested both ways).
  `life._ensure_builtin` imports `core.life_wood` (which only registers the place) and registers its rows only when the flag is true.
- **The 5 pilots (extremes of zone and size):** huhu beetle (deadfall, night), green gecko (undergrowth, rare), freshwater crayfish (the ASSUMED stream), red
  deer (clearing, huge, shy), kākā (canopy: the 3D case). Biology is from general knowledge and NOT checked against a reference.
- **Verified (run, not read):** `scripts/_test_wood_bestiary_p1.py` ALL OK: every sample of all 14 zones inside 24 x 20 x 10; canopy creatures 5-9 m up; the
  stream between the spring and the sea gap; groves where `wood_life.TREES` says; 3D distance; the leak scan of all 293 vocabulary phrases and every string
  the rows emit against 350 forbidden names (the 181 parsed from this very list + the shore's + categories); no key collides with any life row or any shore
  bestiary row; one-flag semantics both ways and independence of the shore; the described look and the place looks through the REAL `life.look_answer` /
  `life.discover_look` live and shadow; 1,398 place-look lines over every standpoint x place word x time bucket with no name; false-positive sweeps (34 wood
  scenery aliases, 53 scenery lines, 361 real wood observe/look thoughts): 0 taken for a creature. Plus an end-to-end run of the REAL `sensorium.look` in the
  wood under life_smoke's isolation (scratch script): the canopy look continues with the kākā "to your left and up above", the clearing with the deer, the deadfall
  with the beetle (from the gathering place), the stream with the crayfish; the old looks are unchanged with no flag; a shore look and a garden look are
  untouched with only the wood flag on; 9 ms per look. The shore tests, `life_smoke.py` and `prompt_registry.py check` still pass.
- **A vocabulary conflict the cross-place leak test caught:** the red deer's female is a "hind" - and the shore already says "the hind legs flattened into
  paddles". "hind" is therefore NOT a forbidden name (a body part wins); noted so it is not re-added.
- **Honest limits:** nothing has run in the live process; 145 of 150 are not written; the wood still has no turn-stone / peel-bark / lens hand (about 30
  entries need one, see Open points); the ASSUMED placements are mine; the island question is open.

## ALL 150 BUILT - 2026-11-02 (J-3064 done; verified by running it)
- **The cast:** `core/life_wood_cast.py` holds the other 145 rows; with the 5 pilots in `core/life_wood.py` that is the 150 of this list, one row each, in
  all 14 wood zones (leaf_floor 27, clearing 25, undergrowth 22, stream 19, deadfall 18, oak_trunk 11, canopy 9, the_spring 5, the_path 5, and the groves,
  oak and sea gap). Every one of the 150 list entries has a row (the test parses this list and checks).
- **ONE FLAG:** `data/life_flags.json` -> `"wood_bestiary": true` and restart Du. It registers all 150 AND turns the wood's described-look answers and place-look
  discovery ON. Shadow: set `"wood_bestiary_render": false` / `"wood_bestiary_discover": false` explicitly. Independent of the shore's flag (tested both ways).
- **What I decided where the list left it open (all easy to change in the cast file):**
  - the island question is unanswered, so the 11 North-Island-only entries ARE written and flagged `North Island` in their notes (giraffe weevil, emperor gum
    moth, common katydid, tunnelweb spider, freshwater limpet, Hochstetter's frog, whitehead, Indian myna, eastern rosella, spotted dove, barn owl): drop them
    once he says the cottage is on the South Island;
  - the entries that need a turn-stone / peel-bark / lens hand are written as what SHOWS (under a log, under loose bark, in the silt) with a very low ease, so
    they appear rarely: 12 rows have ease <= 0.08 (dampwood termite, trapdoor spider, mite harvestman, small land snail, land flatworm, peripatus, pseudoscorpion,
    barklouse, vegetable caterpillar, freshwater limpet, Hochstetter's frog, brown kiwi); the termite and the vegetable caterpillar are almost never shown;
  - 43 are marked invasive in their notes; the female deer is not called a hind anywhere (that word is a body part on the shore);
  - six rows were moved into the oak, totara and tree-fern zones so every zone has creatures.
- **Verified (run, not read):** `scripts/_test_wood_bestiary_p1.py` ALL OK on the full 150: unique keys and species; no key collides with any life row or any shore
  bestiary row; no two rows share size band + body plan + both colours + pattern, and none composes the same full-detail look; every zone used; every vocabulary
  phrase (293 + the new bush vocabulary: 61 shapes, 13 motions, 16 positions) and every string the 150 rows emit scanned against the 150 parsed list names +
  the shore's 100 + category words: no name; 2,533 place-look lines over every standpoint x place word x 24 time buckets, none with a name, reaching 101 of the
  150 creatures (the tiny ones show only to someone close); false-positive sweeps against the wood's scenery and the 361 real wood thoughts in hands_trace.jsonl: 0
  taken for a creature. The shore tests (P1, P2, P3), `life_smoke.py` and `prompt_registry.py check` still pass. Plus an end-to-end run through the REAL
  `sensorium.look` in the wood (scratch script): the canopy look continues with a moth "mid-toned against the leaves ... to your right and up above", the
  clearing with the deer, the deadfall with a wētā-like long-legged thing, the stream with a tapered finned thing, the path with a shaggy long-billed one, the oak
  with a wētā in the tree hollow; a shore look and a garden look untouched; 8 ms per look.
- **A performance bug the bigger cast exposed (fixed):** `leak_scan` compiled one regex per forbidden term and Python's regex cache holds ~500, so with the shore's 100
  and the wood's 150 names (~1,200 terms) every call recompiled and a 150-row scan took minutes. It now compiles ONE alternation per term set and falls back to the
  exact per-term check only when something matches (0.4 s for the whole 150-row scan).
- **Cost:** `life.advance` with BOTH bestiaries on (316 rows) takes ~137 ms per tick (45 ms with the shore's 166); a tick is every 5 s.
- **Honest limits:** nothing has run in the live process; the biology of all 145 (seasons, hours, sizes, colours) is from my general knowledge of NZ bush and is NOT
  checked against a reference, and the te reo names are unchecked; the ASSUMED placements (stream, canopy, oak trunk, groves) are mine; hidden-sign rows can be named by
  a book though he only ever saw the sign; the old text still calls some of these things by name (the grouped `ground_beetle`, `cicada`, `weta` rows keep their
  names), so a pair of rows can describe the same kind of animal two ways; the shore and wood bestiaries together are 250 new creatures on a world that had ~66 rows.

## Current State — 2026-11-02
- **2026-11-14** (F-4556): J-3812 (D-0714): placements confirmed as assumed (South Island, Sumner); turn-stone / peel-bark / stream-stone hand built as core/wood_dig.py behind wood_bestiary (commit f46851ad on branch jobrun/w14_wood_creatures, restart-gated, not run live). Restart/flip is the founder's.

- **2026-11-09**: 2026-11-09 stale-stage fix: doc said OFF/ready to flip; data/life_flags.json has wood_bestiary true (set 11-02). Wood arrivals 630 since 11-01; discoveries include harrier and whitehead. The Status line text below still says OFF; the block above is current.
### What we have
All 150 rows, the generalised engine, 14 wood zones, tests (`scripts/_test_wood_bestiary_p1.py` plus the shore's three, all green), an end-to-end check through the real
`sensorium.look`. OFF today.
### What we need
(1) The founder to flip `wood_bestiary` (and `shore_bestiary`) when ready, and read what it shows in `life_events.jsonl` (`resolved` = `discovered` / `described`).
(2) J-3065: confirm or move the ASSUMED stream / canopy / oak trunk / groves, say which island (drops or keeps the 11 North-Island entries), rule on the turn-stone / peel-bark hand.
### What we're doing next
Nothing queued but those. The shadow read of the shore (J-2957) is the model: set the two sub-flags false first if he wants a week of logs before anything shows.
