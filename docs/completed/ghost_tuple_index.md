# THE GHOST TUPLE INDEX — adapting FreshStart's ghost indexing to our tuples (assessed 2026-08-16)

**Founder:** FreshStart is dead and old — "much older than you think" — look at its ghost
indexing and judge whether it adapts to our tuples. **Status: PLANNING; verdict below.**

## The lineage (why this pattern deserves the look)

`ghost_index.py`'s own header: *"Ported from X4-AI village_root/.library/ghost_index/"* — and
per the founder (2026-08-16), the pattern is older still: it predates X4, from work where
**there was no LLM call at all** — a pure-deterministic retrieval core from before LLMs entered
the founder's systems. This would be its third-or-more port (pre-X4 → X4 → FreshStart →
Nascence). Each generation kept the same core — **cheap entity fingerprints + set-intersection
scoring as a pre-filter before expensive search** — and shed the era's wrappings (X4's village
library, FreshStart's LLM-flavoured Weaver accretions). The design signal in that history:
**the no-LLM core is not an implementation choice, it is the pattern's identity** — it survives
every substrate change precisely because it depends on none of them. The Nascence port keeps
that property as law (which it conveniently already matches: the courier "just a script"
doctrine and this pattern's oldest form are the same idea, arrived at twice, years apart).

## What FreshStart's version actually is (verified against code, not docs)

Two systems wearing one name:
1. **`GhostIndex`** (250 lines, no deps): entities → {SHA-256 exact-match hash, 2-gram "shadow
   signature" for fuzzy text, tag-set} → query scores = 0.5·shadow-overlap + 0.3·tag-intersect
   + 0.5·exact-name bonus. In FreshStart: DEAD (zero live callers, cache never created).
2. **`GhostWeaver.query_ghost`** (live in their dispatcher): the heavyweight — LLM "gnostic"
   query expansion, parallel lens search, dual-pass Reciprocal Rank Fusion, graph-neighbor
   expansion. Genuinely good engineering — AND carrying a silent fatal bug: its FTS5 leg
   queries a `ghosts` table that exists in NO database file; that leg has returned nothing,
   silently, forever. The cautionary tale travels with the pattern.

## VERDICT: YES — adapt the CONCEPT (GhostIndex's), not the code, and not the Weaver

### The fit, benchmarked on our real tuples (2026-08-16)
7,647 fragment_context rows: index build **45ms once**; a FULL-CHORD query (place + weather +
tide-band + several sounds + standpoint, scored together) over every tuple: **5.6ms**. The win
is not raw speed — a single-key LIKE is already 3.9ms — it is **capability**: today Courier A
matches ONE note (weather) and Courier D ONE note (a sound key). The ghost-style query matches
the **whole chord at once**. That is context-dependent recall done properly — "moments LIKE
this one" across every world coordinate simultaneously — with zero LLM and zero embeddings.
It is also a direct, cheap step toward the Cognitive Geometry chords vision (#1 on the
roadmap) by purely deterministic means.

### What to port
1. **Tuple fingerprints**: each fragment_context row (and each future answer-good) registers a
   tag-set — `place:shore · wx:thunderstorm · tide:low · snd:gull_cries · sp:at_the_path_foot ·
   band(sun/moon/season)…`. Categorical coordinates ARE tags; no text-processing needed.
2. **Intersection scoring with rarity weighting** (our v2 improvement over the original's
   plain sqrt normalization): rare tags count more — a thunderstorm tag should outweigh a
   place:study tag that half the store carries. IDF-style, still pure arithmetic.
3. **The exact ghost-hash for ITEM-grain entities**: the item factory's registry lookup
   (driftwood_17, the gate, the kettle) — O(1), trivial, and exactly what item-graduation needs.
4. **2-gram shadow signatures ONLY for free-text item names/summaries** (an item's seed text) —
   not for tuples, whose fields are already categorical.
5. **Incremental registration as a courier-class script**: new tuples register at mint time
   (the memory-stamper calls one function); rebuild-from-DB as the recovery path. JSON cache
   like the original.

### What to leave behind, and why
- **GhostWeaver's LLM gnostic expansion** — violates the courier no-LLM law for ambient paths.
  (Its RRF *fusion pattern* is worth remembering separately for the multi-bus recall future —
  fusing evidence-hand + associative + context-echo candidate lists — but that is a later,
  different adoption.)
- **Persona/YAML loading, the MCP wrapper** — FreshStart-shaped, no Nascence analogue.
- **The FTS5 leg** — and its lesson comes along as LAW: the index asserts its schema/sources
  at startup and FAILS LOUDLY if a registered field vanishes (this is also seam #4 from the
  sound-system examination, now with a proven horror story attached).

### Who consumes it (the warehouse catalog, in transit-map terms)
The couriers find freight without opening every crate:
- **Couriers A+D upgrade**: from single-key rules to whole-chord resonance — "a moment like
  THIS one" (storm + shore + gulls + low tide together). Also collapses their two hardcoded
  trigger lists toward one mechanism, easing the Transport Manager's later absorption of both.
- **The item factory**: hash-lookup registry; graduation checks ("have I seen this named thing
  before?") become O(1).
- **The Transport Manager**: cheap candidate sets per line without scanning stores.
- **The evidence hand / associative recall**: optional PRE-FILTER before embedding scans (the
  original's stated purpose — eliminate 80% before the expensive pass). At today's 20k
  fragments the matrix scan is affordable; this matters as the store grows, not urgently.
- **P4 acoustic recall**: sound-chord tags are first-class index citizens from day one.

### Costs, honestly
Build 45ms / rebuild trivial; RAM footprint tiny (tag-sets for ~10-20k rows); the scoring is
crude by design (that is what makes it fast and inspectable) — it PRE-FILTERS and RANKS, it
does not understand. Anything needing meaning still goes to embeddings or the panel afterward.

## Build shape (when approved — NOT now; planning continues)
`core/ghost_tuples.py` (~150 lines, adapted not copied): register/rebuild/query + rarity
weights + the startup source-assertion. First consumer: upgrade `couriers.context_echo` +
`sound_echo` to one `chord_echo` scored against the live manifest. Isolated tests: known-chord
retrieval, rarity weighting sanity, loud failure on schema drift. Lab-testable entirely
offline against the real fragment_context (read-only), same as tonight's benchmarks.
