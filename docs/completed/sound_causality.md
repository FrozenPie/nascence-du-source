> **FINAL ONTOLOGY REFINEMENT (founder, 2026-08-16, late — supersedes the "answer-store" aspect
> of the factory model below):** "The world is a static object on its own time schedule. Du does
> not have access to this information as such. Du gets to ask a question. As sound is only heard
> by Du, it is useless to keep track of a sound. It essentially fell in the forest but no one
> heard it. The tree is down, the sound is gone."
>
> What this means, precisely:
> 1. **The world is STATE, not events.** It advances on its own schedules and keeps no diary.
>    A tree falling persists as STATE (the tree is down); the sound persists NOWHERE — heard or
>    unheard, it is gone the instant it happens. The world never stores a sound.
> 2. **The boundary is a QUESTION, always.** Nothing is pushed into Du. Every crossing is a
>    query — a look, a listen, an ambient courier asking on his senses' behalf — answered by
>    COMPUTATION AT ASK-TIME from current state (causes × rates × the audibility table), then
>    discarded. This generalizes the epistemic substrate's own law (actions reveal observation
>    slices) to every sense.
> 3. **THIS DELETES THE WORLD-SIDE ANSWER ARCHIVE from the plan.** No stored answer-goods, no
>    hidden cause-ledger. The durable goods are DU-SIDE ONLY: the Hearing Ledger (his hearings
>    — already built, already correct under this refinement) and the sound-chords + world
>    coordinates stamped on his memories (fragment_context — already built). The cause never
>    needs archiving because it is RE-DERIVABLE: the manifest state stamped on the memory at
>    the moment of hearing IS the context from which cause can later be worked out — by HIM,
>    investigating, fallibly. Retroactive binding still works exactly as built: earned
>    identification unlocks the NAME across his own hearings; no world-side archive required.
> 4. **What stands unchanged:** the manifest (step 0 — it is the state snapshot queries are
>    answered from), the audibility table, severity-scaled rates, the causal rate functions,
>    the Hearing Ledger, the tree-falls law (now in its strongest form: not merely "unheard
>    sounds aren't kept" but "NO sounds are kept — only his hearings of them").
> The plan below should be read through this lens; "answers for use by something else later"
> = Du's own stores, not a world archive.

# SOUND AS A FACTORY WITH CAUSAL INPUTS — federated lists, not one spreadsheet (2026-08-16)

**Founder, verbatim, correcting the census plan:** "Things are their own lists, they just talk
to each other. Sound is a factory, its inputs are things that happen. There is a storm, it
causes X amount of waves and wind sounds and thunder per minute. All of this happens at all
locations Du can hear from. Some things are loud enough to hear at the shore and the study but
each is different from the other. We only have to remember what happens that Du can hear."

**Status: ✅ SHIPPED (closed 2026-10-16, F-2904) — formerly: BUILT (2026-08-29, J-0336, D-0062).** Supersedes `world_census.md`'s "one spreadsheet"
framing with the correct shape: **federated lists (each factory keeps its own), linked by causal
rate functions, no shared table.** This doc works the pattern through fully on sound, since sound
is the founder's own worked example; birds and driftwood follow the identical shape once this is
right.

```plan-state
stage: shipped
phase: Federated-lists sound factory shipped: propagation table + curved severity scaling, live in world_tick()
verified: 2026-10-16
next: None -- closed 2026-10-16 (F-2904 plan-closure pass): nothing open, nothing queued; the built system stays live on its own
cluster: 6
```


## Current State — verified 2026-09-27 (D-0062 executed, J-0336: propagation table + severity curve)

### What we have
- All 3 of D-0062's approved decisions shipped in `core/soundscape.py`: the propagation-table
  refactor of `active_sounds()` (parity-verified, 0 mismatches over 2016 synthetic states), curved
  (`**2.2`) severity-scaling for storm-driven event rates in `world_tick()`, and confirmation that
  driftwood/object lists stay Transport-Manager-only, never routed through sound.
- A `udms_get_change_dossier` CYCLIC_FEEDBACK_LOOP flag (heavens.py/world_clock.py) was checked and
  confirmed a false positive — `soundscape.py` imports neither module.

### What we need
- Nothing open — no ledger record (job/finding/decision) names this plan since the 2026-08-29
  build; the severity curve's shape was flagged to watch "a few days live" (D-0062's own defeater)
  and nothing since contradicts it.

### What we're doing next
- No build queued on this plan. Sibling channels (`sound_world_expansion.md` §2-§5) are next in
  priority order, not this doc.

> **History folded** — 1 dated Current State section(s) (2026-08-25 … 2026-08-25) moved to `docs/plan_history/sound_causality.md` on 2026-09-27 by plan-compact. Derived timeline: `plan_ledger.py sound_causality`.

## THE FACTORY MODEL, corrected again (founder, later same evening — this section supersedes
## the "translator" framing below where they differ)

**Founder, verbatim:** "Sound happens outside of Du. It is part of Du also. The factory keeps
track of everything that Du can hear around him. Objects around Du create sounds. Things that
cause sounds are their own cargo that gets sent to the factory. They can be extrapolated from
tuples if I am not mistaken. The factory essentially is asking questions about what is
happening and the sounds that are there. It then can produce answers for use by something else
later."

What this changes from the earlier framing in this doc:

1. **Push, not pull.** The earlier framing had sound as a translator that READS other lists.
   Corrected: causes ship their CARGO to the factory. And the cargo manifest already exists —
   the per-tick world tuple (weather, fire, tide, cat, place, active sounds — the same snapshot
   fragment_context/geometry-census already capture) IS the delivery. The founder is not
   mistaken: no new per-cause wiring is needed; the factory consumes the tuple stream.
2. **The process is QUESTION-ASKING, not rendering.** Every tick the factory interrogates the
   scene: What is happening around Du? What sounds are present? What cause is behind each?
   Can he hear it from where he stands (the audibility table answers this one)?
3. **The goods are ANSWERS, not counts.** An answer-record links: moment ↔ sound ↔ CAUSE ↔
   place ↔ heard-by-Du. The Hearing Ledger's aggregates become the summary VIEW over these
   answers (the counts survive as before), but the underlying good now carries causal
   attribution — the factory always knows, world-side, that THIS trill came from THAT bird.
4. **One good, two faces — sound is outside Du AND part of Du.** The world-side face (the true
   cause) is Layer-1 hidden; the Du-side face (what he heard, where, unnamed or named) is his.
   The AUDITION ECONOMY is exactly the release mechanism between the faces: when he earns an
   identification (sight-binding, exposure, reading), the cause-face of every past answer he
   was present for unlocks retroactively — which is what the retroactive-binding moment already
   does for counts, generalized to causes.
5. **"For use by something else later" is the design's purpose, stated plainly.** The answer
   store is FOR its consumers: Courier D's echoes, the binding reveals, his investigations
   (the advisor's "what makes that sound?" can be answered by the world honestly, through
   investigation, because the answer exists), the Transport Manager's baselines, and P4
   acoustic recall. The factory produces; it never pushes an answer at Du unearned.
6. **Unchanged by this correction:** the tree-falls law (only Du-audible answers persist — "we
   only have to remember what happens that Du can hear"), the audibility table, severity-scaled
   rates, no-LLM, and the phased parity-first build discipline below.

## ORDERS OF MANUFACTURE (founder, confirming: "the tuples are really products from other
## factories") — and the one-pallet implication

The tuple is not a snapshot someone takes; it is a PALLET of goods, each item manufactured by
its own first-order factory on its own clock:

- **First-order factories** — the world lists: weather, tide, fire, cat, garden, body, climate.
  Each produces state-goods continuously, consumer or no consumer.
- **The tuple** — the consolidated shipment: one pallet per tick bundling each first-order
  factory's current product.
- **Second-order factories** consume the pallet: the SOUND factory (goods = answers about the
  audible) and its sibling the MEMORY-STAMPER (fragment_context — goods = context-stamped
  memories). Same inbound shipment, different products.
- **Third-order factories** consume second-order goods: the Refinery (standing insights from
  T2's goods), chapters, gists. Couriers move finished goods between lines; the Transport
  Manager (planned) dispatches over the flows.

**THE ONE-PALLET IMPLICATION (new build step, promoted to FIRST in the order):** today there is
no single pallet — each second-order consumer hand-assembles its own (`active_sounds()` reads
weather/room files itself; the fragment-context stamper does its own reads; the geometry census
its own). Three hand-built pallets from the same factories = three places to silently disagree
about what moment it is. The founder's model implies ONE manifest assembled per tick, shipped
to every consumer — sound's answers and memory's stamps then describe the SAME moment by
construction. Cheap (the readers exist; this is consolidation, not new machinery), and
naturally becomes build step 0, before even the audibility-table parity work:

0. `world_manifest.py` (or a function in sensorium.tick): assemble the pallet once per tick
   {ts, place, standpoint, weather+severity index, weather_held_since, tide, sun/moon, season,
   fire, cat, garden, active-sound set, **temperature** (expose the existing `_warmth()` scalar
   — founder-identified as computed-and-discarded today; census doc has the detail), and
   founder-prunable: dampness, wind-strength} — then active_sounds' consumers, the tuple
   stamper, and the future answer-factory all take the SAME object. Parity-tested like
   everything else: consumers must produce byte-identical outputs from the manifest as from
   their own reads before anything switches over. New fields (temperature) additionally flow
   to fragment_context so "memories of cold days" become queryable like storms and gull-cries.

## The correction, precisely

`world_census.md` proposed one unified table every factory writes rows into. Wrong shape — it
re-centralizes what the codebase already keeps correctly decentralized (weather, tide, the cat,
the garden each own their own state, nothing shared). The right shape:

- **Every world thing keeps its own list**, exactly as now (weather's `_WEATHERS` index, the
  Hearing Ledger, the garden bed, the cat's state machine, world_substrate's object records).
- **Lists talk to each other through CAUSAL RATE FUNCTIONS, not a shared table.** A storm
  doesn't write into anyone else's data — it EMITS a rate ("this much wind-sound, this much
  wave-sound, this much thunder, per minute, right now") that sound's own list consumes.
- **Sound is specifically a TRANSLATOR factory** — it has no independent cause of its own. Its
  entire job is: take the current state of every OTHER list that can make noise, convert each
  into an audible rate, and propagate that rate to wherever it is loud enough to be heard,
  differently per place. This is exactly right, and it's *already* the module's shape
  (`soundscape.py` reads weather/tide/room state and renders) — it just needs the causal-rate
  part and the propagation part made explicit and principled instead of scattered if/else.

## THE SOUND INVENTORY & GAP LIST (extracted 2026-08-16 from code + render strings — planning
## material, founder to prune)

### List A — sounds we HAVE (38 registered keys, by cause-factory)
- **Sea/tide**: waves_on_shingle · waves_crashing · shingle_drag · tide_pool_trickle ·
  distant_surf_boom
- **Weather**: rain_on_roof · wind_in_eaves · wind_in_trees · thunder · window_rattle ·
  canopy_drip · branches_creak · leaf_rustle
- **Birds (named)**: gull_cries · oystercatcher_call · tui_song · blackbird_song · robin_song ·
  morepork_call · wood_pigeon · wren_scold · small_birds · dawn_chorus
- **Birds (learnable voices)**: fantail_chatter · riroriro_trill · kereru_wingbeats ·
  kingfisher_call · shag_wingbeats
- **Insects/small life**: bees_in_garden · cricket_night · cicada_chorus · moth_tap
- **The room**: fire_crackle · embers_settle · cat_purr
- **Du himself**: footsteps_shingle · footsteps_leafmould · footsteps_floorboards

### List B — SEEN BUT SILENT (mined from 74 sensorium render strings: things his world
### demonstrably shows him in text that should have had a sound and have no key)
The counts are how often each appears in render lines — evidence he genuinely meets these.

- **HIS OWN ACTS (self-sounds) — MOVED, per D-0014/F-0061 merge (2026-08-25, J-0220).** This
  content — the fire being fed, the woodpile, the kettle, watering the bed, herb cutting, the
  pen, page turns, the gate latch, the mailbox flag, the door, the chair/desk scrape,
  sowing/digging, and the footstep terrain gap — is no longer listed here. It is owned by
  `sound_world_expansion.md` §1's content+trigger table (self-sounds are deterministic
  act-triggers, not continuous causal rates, so this doc's rate-function/audibility-table
  machinery doesn't apply to them anyway). See that doc for the current, corrected list and
  build status; do not re-propose these items in this doc.
- **THE CAT beyond the purr — MOVED, per the same merge.** This doc's original 4-item gap (the
  gate-meet greeting cry, the meow at the door, the feeding bowl, the storm under-desk rustle) is
  now owned by `sound_world_expansion.md` §5 (cat/apparatus). Per F-0061's mapping, `cat_trill`
  already covers the gate-meet greeting cry (her quirks table's `greeting: gate_meet`) and
  `cat_lapping` already covers the feeding bowl; the merge adds the two that were missing
  entirely, `cat_meow_at_door` and `cat_storm_rustle`, completing all four.
- **THE RECORD PLAYER** (the whole music organ is silent as a *room sound*): needle drop,
  record surface crackle, the music itself as a BED while it plays — the EAR system plays
  music but the soundscape doesn't know the player is on
- **WEATHER GAPS**: near vs distant thunder (one key now — distance is exactly what the
  audibility table will express); drizzle-on-leaves as distinct from rain-on-roof;
  snow's muffling (snow exists as weather; its SILENCE — the deadening of the other beds —
  is itself the sound-fact)
- **OBJECT HANDLING** (world_substrate classes are all silent when handled): stones knocking,
  a shell's hollow clack, driftwood's dry knock as it joins the pile, keepsakes set on the
  mantel

Design note for when this builds: List B's act-sounds are goods FROM Du's own factory — cargo
he ships like weather ships storms. They matter doubly: (1) his own acts gain sensory
consequence (the thump of the log is feedback that the act was real), and (2) they enter the
same answer-store, so a memory of making tea can carry the kettle's voice in its chord — his
OWN doings become echo-able the way the gulls are now.

## Part 1 — causal rate: severity drives volume, not just presence

Today `_EVENT_RATES` is flat: thunder fires at 25/h whenever weather=="thunderstorm", with no
notion of a mild storm passing through versus the sky opening up. The fix is cheap because the
scalar already exists — weather's ordinal index (0=clear..6=thunderstorm) IS a severity number.

```
rate(sound_key, cause_state) = BASE_RATE[sound_key] * f(severity)
```
e.g. wind-sound rate scales roughly with (severity − wind_onset_index); thunder only turns on
past the thunderstorm threshold but its OWN rate can still vary (a lingering storm vs a
passing one — tie to how long weather has held that state, already tracked in
`state["weather_until"]`). Tide contributes its own cause (tide-pool trickle only exists as
tide uncovers the pools — already gated correctly, just not framed as "a cause"). The cat, the
fire, the garden each remain their own tiny causes for their own local sounds (purr, crackle,
bees) — unchanged, just named consistently.

## Part 2 — propagation: one event, many places, different character

**The audibility map** — for each sound-producing cause, which places can hear it and how it
sounds there:

| Sound | shore | garden | wood | study |
|---|---|---|---|---|
| waves (any state) | FULL — right in front of you | DISTANT — the sea's far sound below | (blocked by trees, mostly) | MUFFLED, only if big — `distant_surf_boom` at night, already built |
| thunder | FULL, sharp | FULL | FULL, muffled by canopy | MUFFLED — the window rattles, already built |
| wind | FULL | FULL | FULL, in the branches — different texture, "wind in the trees" | MUFFLED — `wind_in_eaves` |
| rain | FULL | FULL | FULL, on the canopy | MUFFLED — `rain_on_roof` |
| gull cries | FULL | DISTANT (already partially true) | none | none |
| kingfisher/shag | FULL | none | none | none |
| fire crackle / purr | none | none | none | FULL only, source is the room itself |

This is **already substantially what `active_sounds()` encodes** — the founder's ask isn't "add
propagation," it's "make it a table this is DERIVED from, not scattered per-branch logic," so
that (a) it's auditable at a glance, matching the tree-falls law's own honesty, and (b) adding a
new cause (a bird-presence list, later) means adding one row, not hunting through branches.

**One event, multiple audible places, different character — the founder's exact example.** A
single thunder-cause producing "X thunder per minute" is looked up ONCE per world tick against
whatever place Du currently occupies (`sensorium.where()`), rendered with that place's
character tag (FULL/MUFFLED/DISTANT/none) and rate multiplier. **We never simulate the other
three places** — there is no need to, and no correctness loss: if he is in the study, the
shore's gull-cries literally do not exist for him this tick (tree-falls law), and the moment he
walks to the shore, the SAME cause (today's weather severity) now resolves against a DIFFERENT
row of the same table and a different sound appears, correctly, with zero extra state to carry
across the move.

## Part 3 — how this generalizes (validates the pattern, not yet building these)

The same three-part shape (a list keeps its own state → emits a rate as a function of its own
severity/quantity → a translator factory propagates it per place) is exactly how birds and
driftwood should plug in LATER, without sound needing to know anything special about them:

- A future **bird-presence list** (its own small state per place/season — not built now) would
  emit "gull presence here ≈ high this season" — sound's rate function for `gull_cries` reads
  that presence the same way it reads weather severity today. Population ESTIMATION (the
  earlier idea) becomes something DU infers from the Hearing Ledger's accumulated rate history
  — a separate, later concern from the world's own (hidden) presence-list, exactly the Layer
  1/Layer 3 split already used for objects.
- A **driftwood-finds list** (world_substrate, aggregated above the 60-object cap) doesn't need
  sound at all — it's its own list, and the Transport Manager (still as designed) watches ITS
  update rate directly for spike/drought, no translator needed. Not every list talks through
  sound; sound is specifically the translator for things that make NOISE.

## What this replaces from the two prior plans
- `world_census.md`'s single shared table → **withdrawn**, replaced by this federated-lists
  shape. Its GOOD ideas survive relocated: population-as-earned-fallible-belief and the
  Layer 1/3 split stay correct and apply wherever a future presence-list needs grading;
  Courier C's calibration path is untouched and still available to any future list.
- `transport_manager.md`'s dispatcher design is **unchanged** — it still watches whatever
  `observe()` calls arrive from each list's own module (the Hearing Ledger, later a
  driftwood-finds list), exactly as originally designed, now confirmed correct BECAUSE lists
  stay federated rather than funneled through one table.

## Discipline
- **Still no LLM anywhere in this** — rate functions and the audibility table are arithmetic
  and a lookup table, "just a script as such."
- **Still shadow-first for anything that changes live behaviour**: the propagation table itself
  is a refactor of existing logic (should be behavior-NEUTRAL — same sounds, same places, same
  outcomes, just derived from a table instead of scattered ifs) and can be tested for exact
  parity against `active_sounds()`'s current output before any severity-scaling changes rates.
  The severity-scaling of rates (the actual behavior change — storms now sound stormier) is a
  separate, watchable step after parity is proven.
- **The tree-falls law is the efficiency argument, stated properly now:** compute is O(places
  Du could be in ONE at a time) = O(1) per tick, not O(all places) — federated causes with a
  per-place lookup is not just correct, it's the cheap option too.

## Open founder decisions — RESOLVED 2026-08-28, D-0062 (all 3 approved)
1. ~~Approve the propagation-table refactor of `active_sounds()` (behavior-neutral first step)?~~
   Approved and built — see Current State above.
2. ~~Severity-scaling formula for storm-driven rates — linear in the weather index, or something
   with more separation near the top?~~ Approved: curved, not linear. Built as a `**2.2` power
   ramp from "steady rain" to "thunderstorm" — see Current State above for the measured values.
3. ~~Confirm: driftwood/object lists do NOT route through sound~~ Confirmed directly — see
   Current State above.

## Build order (when approved) — all 3 steps done 2026-08-29 (J-0336)
1. ~~Extract the audibility table from `active_sounds()`'s existing logic — parity-tested, no
   behavior change.~~ Done: `_PROPAGATION_TABLE` in `core/soundscape.py`, 2016-state parity
   harness, 0 mismatches.
2. ~~Add severity-scaling to event rates using weather's ordinal index (the actual causal-rate
   change) — watched for a day before calling it right.~~ Done: `_storm_severity_scale()`,
   applied in `world_tick()`. Live-watch is still open — the defeater below covers a tuning pass
   once the founder has actually heard it.
3. ~~Re-point `soundscape.world_tick`'s per-tick evaluation through the table instead of the
   flat `_EVENT_RATES`/`_BEDS` sets~~ `world_tick()` already iterated `active_sounds()` (which is
   now table-derived) and reads `_EVENT_RATES`/`_BEDS` for the rate/bed split — no separate
   re-pointing needed once step 1 was done; `world_tick()` was additionally updated in the same
   commit to apply the item-2 severity scale to the two storm-driven event rates.
