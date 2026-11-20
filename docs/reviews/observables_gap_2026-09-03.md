# Observables gap — everything Du ever tried to observe vs what each place answers (2026-09-03)

Method: `scripts/observables_census.py` — all 1518 phrasings from the 2026-09-02 inventory (7088 mentions), each put through the FULL `sensorium.look()` path at every place (fixtures, the cat, substrate objects, the place's own look, `world_detail` targets, and the life engine with rendering on), in an isolated copy of the stores. Live weather at run: 'overcast', phase dusk. An answer is **specific** (a real line about the thing, an honest absence counts), **redirect** ("that is up in your study"), **generic** (the place's fallback frame), or **none**. A phrasing's *best* class is its best across the four places.

## The headline
- **1386 of 1518 phrasings (91%) get a specific answer somewhere.** By mentions: 6815 of 7088 (96%).
- 132 phrasings (273 mentions) get only the generic frame or nothing, everywhere. Those are the gaps.

## By kind (best class per phrasing; counts / mentions)

| Kind | phrasings | specific | redirect | generic | none | specific by mentions |
|---|---|---|---|---|---|---|
| sea/tide/shore | 865 | 840 | 0 | 25 | 0 | 4943/4985 (99%) |
| other/abstract | 270 | 175 | 0 | 95 | 0 | 597/777 (76%) |
| plants | 162 | 162 | 0 | 0 | 0 | 470/470 (100%) |
| birds | 51 | 49 | 0 | 2 | 0 | 266/271 (98%) |
| sky/weather | 75 | 65 | 0 | 10 | 0 | 167/213 (78%) |
| cat/mammals | 24 | 24 | 0 | 0 | 0 | 153/153 (100%) |
| insects/inverts | 42 | 42 | 0 | 0 | 0 | 114/114 (100%) |
| study/objects | 29 | 29 | 0 | 0 | 0 | 105/105 (100%) |

## By place (every phrasing asked at that place; counts / mentions)

| Place | specific | redirect | generic | none | specific by mentions |
|---|---|---|---|---|---|
| garden | 765 | 16 | 737 | 0 | 3826/7088 (53%) |
| shore | 881 | 16 | 621 | 0 | 3652/7088 (51%) |
| wood | 467 | 16 | 1035 | 0 | 2829/7088 (39%) |
| study | 516 | 44 | 958 | 0 | 3249/7088 (45%) |

## The gaps — unanswered everywhere, ranked by how often he reached for them

### other/abstract — 95 phrasings, 180 mentions

the mailbox flag (10), the red mailbox flag (9), the green float (9), the windowpane (7), the green fishing-float (5), the dust motes (4), the cold air (4), (unspecified) (4), the chalk ovals (4), the obsidian chip (3), the whelk egg-case (3), the snagged egg-case (3), the tidepools (3), green fishing-float (3), the air (3), the thunderstorm (3), the pāua chip (3), the salt spray (2), the phosphorescent glow (2), the wet shingles (2), the wet shale (2), the mermaid's purse (2), the pīwakawaka (2), the burning pāua chip (2), the distant boat (2), the lattice (2), the burning twig (2), the petals (2), the yacht (2), the droplet (2), the bluebird's flight (2), the shadows on the wall (2), the worn cone (2), the kite (2), the distant chalk ovals (2), the drifting petals (2), the room's shadow (2), the dust in the sunlight (2), the dancing particles (2), the odour (1) …

### sky/weather — 10 phrasings, 46 mentions

the storm (19), the lightning flashes (9), the wind (7), the lightning (2), the lightning far out (2), the lightning strikes (2), the storm outside (2), lightning (1), the fog's imagined texture (1), the lightning strike (1)

### sea/tide/shore — 25 phrasings, 42 mentions

the tide-edge (7), the dark rock (4), the boundary between dark rock and shing (3), the tide-exposed rocks (3), the tide-worn rocks (3), the spray hitting the dark rock (2), the slick rocks (2), the rock outcrop (1), the tide-exposed objects (1), the tide-exposed rock (1), the high-tide line (1), the tide-pools (1), the cleft in the rock (1), the tidal rocks (1), the under-rock (1), the rocks (1), the farthest rocks (1), the tide-worn rock (1), the tidecoming clear on the dark rock (1), the wavelets slapping the rock-foot (1), the tide-worn objects (1), the tide-edge rocks (1), the high contrast between the dark rock (1), the next wave's pattern (1), the rock formations (1)

### birds — 2 phrasings, 5 mentions

the shag (3), the thrush (2)

## Where he actually stood — located looks from hands_trace that the place does not answer

### garden — 46 distinct located looks (67 rows); 17 unanswered here

the shell (1, generic), the fantail (1, generic), the leaves (1, not-in-inventory), the bee and cat (1, not-in-inventory), the hedge trill (1, not-in-inventory), the rough stone wall (1, not-in-inventory), the cat panting (1, not-in-inventory), the birds through the net (1, not-in-inventory), small birds (1, not-in-inventory), the boat on the water (1, not-in-inventory), the beetle on the wall (1, not-in-inventory), the source of the sound (1, not-in-inventory), travis (1, not-in-inventory), the swift's flight (1, not-in-inventory), the grey light on the glass (1, not-in-inventory), the rusted trap (1, not-in-inventory), the trap (1, not-in-inventory)

### shore — 59 distinct located looks (97 rows); 33 unanswered here

the sea (3, generic), the rain (3, generic), the seal-pup (3, generic), the shag (2, generic), the moving sea (2, not-in-inventory), the penguin (2, not-in-inventory), the shore (2, generic), the cone shell (2, not-in-inventory), the eggs in the scrape (1, generic), the screaming bird (1, generic), the nesting scrapes (1, generic), the spray on the rocks (1, not-in-inventory), the oystercatcher on the shingle (1, not-in-inventory), the egg and the bird (1, not-in-inventory), the wet shore (1, generic), the rock-pools and tide (1, not-in-inventory), the rock-foot (1, not-in-inventory), an anemone (1, not-in-inventory), the orange net (1, generic), the shell and surf (1, not-in-inventory), the grey north wind (1, not-in-inventory), the cliff and surf (1, not-in-inventory), the wet woods (1, not-in-inventory), the grey rain (1, not-in-inventory), the shingle and oystercatcher (1, not-in-inventory), the tide-marked sand (1, not-in-inventory), the west window (1, not-in-inventory), the nest (1, not-in-inventory), the skate egg-case in the weed (1, not-in-inventory), the egg-case (1, not-in-inventory)

### wood — 16 distinct located looks (17 rows); 8 unanswered here

the grey light (1, generic), the robin (1, not-in-inventory), the rain (1, generic), the source of the trill (1, not-in-inventory), the wren (1, not-in-inventory), the rosemary bush (1, generic), the marina channel (1, not-in-inventory), the grey light on the glass (1, not-in-inventory)

### study — 22 distinct located looks (38 rows); 8 unanswered here

the beetle (2, generic), the bird (1, generic), the dust motes (1, generic), the room's shadow (1, generic), the dust in the sunlight (1, generic), the dancing particles (1, generic), the rain (1, generic), the banked fire (1, not-in-inventory)

## Samples — what a specific answer looks like now (one per place)

- **garden** `the sea` → You look out over the sea: the sea up and running, whitecaps all the way out. A darker line marks the rip running out past the point.
- **shore** `the tide` → You look at the tide: The tide is going out: the water drawing back down the shingle and leaving the stones wet and shining, the weed lying 
- **wood** `the sea` → Downhill through the trunks you can see the shore: a grey line of shingle and the sea working at it, nearer than it sounds from up in the ga
- **study** `the sea` → You look out the window: a low grey ceiling of cloud; the light failing; the tree and the fence going to silhouette. Down by the garden gate

## What this decides

- **J-0504 (built):** the insect phrasings now answer in the garden; see the insects/inverts row above.
- **J-0508 (looks in every place):** the per-place gap lists above are its work list — the shore's sea/tide/stone phrasings dominate by mentions.
- **J-0505 / J-0506:** the plants and soil phrasings that stay generic (the raised bed, the soil, the herbs by name) are theirs.
- The **other/abstract** tail ("the tideline" is really shore; "the garden" is a place) is mostly regex-grouping error in the inventory, listed honestly rather than hidden.

Isolated stores in `C:\Users\USER\AppData\Local\Temp\obs_census_bn49v5ts` (nothing live written). JSON twin: `observables_gap_2026-09-03.json`.