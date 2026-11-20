# ITEM FACTORIES vs POPULATION FACTORIES (founder's deepening, 2026-08-16)

**Status: ⚪ PARTIAL — the GIVEN trigger is now BUILT (2026-08-29, J-0342/D-0067); the repeated-look
trigger and population presence/count state remain unbuilt.** Extends
`sound_causality.md`'s factory model (cargo → questions → answers) from sound specifically onto
ALL first-order world producers — the general shape underneath the factory census's Tier 1. See
"Current State" below — the third graduation trigger is real code now, not just a naming pass.

```plan-state
stage: partial
phase: GIVEN trigger BUILT+verified 08-29 (J-0342/D-0067); population presence/count good + repeated-look trigger still not built as code
verified: 2026-09-27
evidence_read: 2026-08-29
next: No job open against this plan; insect-population follow-through (I-0061) promoted to garden_living_upgrade instead
cluster: 6
```


**Founder, verbatim:** "We need a factory of items, let's say. Each item has a tuple. The birds
are factories as such that have specific properties. But a flock of sparrows does not need to
be individually tracked. Each factory has its own line of products."

## The two grains, and both already exist in embryo — verified against code

**ITEM-grain (one tuple per individual, its own product line over time)**: `world_substrate.py`
already IS this, exactly. Each spawned object (`driftwood_17`, `shore_kelp_f633cb`…) has its
own record — hidden Layer-1 biography, its own append-only observation stream (its "line of
products" is literally its `observations` list, growing one entry per encounter). This is the
pattern; nothing new needs inventing for items that qualify.

**POPULATION-grain (one factory per species/kind, producing RATE not individuals)**: partially
built, incompletely. `sound_knowledge.AUDITION` already carries per-species PROPERTIES —
`sight_prob`, `miss_weight`, `day_only` — exactly the "specific properties" the founder means.
Verified: `fantail_chatter → sight_prob 0.85` vs `riroriro_trill → sight_prob 0.03` — two
species, two real, different parameter sets, already a factory's worth of specificity. What's
MISSING from it: no notion of "how many" (population size), no seasonal presence curve, no
per-place affinity beyond which location-keyed unknown-line it renders. AUDITION is a
behavior-properties table wearing a population factory's clothes without its core good (a
presence/count state).

## The rule, stated plainly

- **A species/kind is a POPULATION factory** by default. A flock of sparrows is the sparrow
  factory's current output, not forty individual tuples. Its product line is a RATE (and,
  eventually, an estimate — `world_census.md`'s surviving idea) — never per-bird state.
- **An item graduates to its OWN factory (its own tuple) only when something makes it
  individually worth tracking.** Three honest graduation triggers now:
  1. **He KEEPS it.** `keepsakes.keep_act` is, quite literally, the existing individual-
     promotion event — the instant he pockets a shell, it stops being "population: shells on
     this shore" and becomes a named individual with its own place on the mantel. The mechanism
     for graduation already exists; it just hasn't been named as that.
  2. **He returns to it repeatedly.** The glass float is the case that was never formally
     promoted — 30 observations should have graduated it into a real item-tuple, and (per the
     historical scan) apparently didn't, or did and then silently lost its thread. Repeated
     engagement is the SECOND honest earned-promotion signal, symmetrical with keeping: keeping
     is an act that claims an item; returning is attention that claims it just as validly.
  3. **It is GIVEN to him.** Ruled in by D-0067 (2026-08-29), built the same day as J-0342: a
     thing handed to him — a letter's enclosure, a gift — earns the same promotion as a pocketed
     find, honestly recorded as arrived by gift rather than found-and-kept. `keepsakes.given()` /
     `keepsakes.given_act()` are the real code (parallel to `keep()`/`keep_act()`), wired into the
     same monologue latch pipeline as the KEEP trigger in `nodes/inner_monologue_node.py`. See
     "Current State" below.
  - **Fixed/unique-by-construction things are ALREADY item-grain and always were**: the gate,
    the mailbox, the hearth, the woodpile, the kettle — one of a kind, never a population, no
    graduation needed. (These are also exactly List B's "seen but silent" acts-cargo from the
    sound plan — the same objects, a different gap.)
- **Wild creatures stay population-grain by default, deliberately, matching the founder's own
  example.** A specific gull is not worth individually tracking even under the repeated-
  engagement rule — the return-to-it signal applies to PLACES and OBJECTS he can actually
  re-identify (a rock, a float, a bird species' habitual perch), not to indistinguishable
  members of a flock. This is a real, load-bearing exception, not laziness: population-grain
  IS the correct model for wildlife; item-grain is for the individually re-encounterable.

## What this changes in the existing plans (reconciling, not replacing)

- `sound_causality.md`'s "birds are population-list-fed causes" is now precisely specified:
  the population factory = AUDITION's behavior table (existing) + a presence/count good
  (missing — the actual gap to fill later).
- `factory_census.md`'s Tier 1 gains a real missing row: **Bird/wildlife populations** — no
  control, population-grain, currently only half-built (behavior parameters exist, presence
  state doesn't). "Object biographies" (item #8) is refined: it is the ITEM-grain factory
  generically, not just natural beach-finds — fixed structures belong in it conceptually even
  though nothing spawns them (they simply always existed).
- The GLASS FLOAT case reads differently now: it should have graduated (30 observations far
  exceeds any reasonable threshold) and the historical scan couldn't find where that happened.
  Whether it's a lost item-factory or was always population-grain narrative text is now a more
  precise question: **did the graduation trigger fire and get lost, or did it never fire at
  all?** Still a factual question for log archaeology, not a design one.

## Open founder decisions
1. ~~Confirm the two graduation triggers (kept / repeatedly-returned-to) as sufficient, or is
   there a third case worth naming (e.g., something GIVEN to him — a letter's enclosure)?~~
   **RULED, D-0067 (2026-08-29): yes, a third trigger — GIVEN. Built same day, J-0342.**
2. Does population-grain ever need a "notable individual" escape hatch for wildlife (a
   specific, recognizable bird — an odd marking, a repeat visitor) or is the census's own
   answer-good history (many kingfisher-answers accumulating at one place) enough to give that
   feeling without ever formally promoting the bird itself? **DECLINED, D-0067: no wildlife
   escape hatch** — matches "not everything produced needs its own tuple," keeps wildlife
   honestly population-grain, per the founder's own recommendation above.

## Current State — verified 2026-09-27

### What we have
Two of three graduation triggers are real: **keep** (`keepsakes.keep_act`, pre-existing) and **given**
(`keepsakes.given()`/`given_act()`, built + live-tested 2026-08-29, J-0342/D-0067) — both wired into
`inner_monologue_node.py`'s latch pipeline, provenance rendered honestly ("from the shore" vs "given by
X"). D-0067 also declined a wildlife notable-individual escape hatch. The rule itself (item-grain vs
population-grain, three triggers) is settled design, applied by at least one neighbor: I-0061 (garden
insect populations, 09-02) used this doc's POPULATION-grain model and was promoted to
`garden_living_upgrade.md` for the actual build.

### What we need
Two pieces flagged as missing are still missing: **trigger 2 (repeated return)** is a named rule only,
not enforced code; population factories still lack the **presence/count good** (AUDITION's per-species
behavior params exist, "how many" does not). Plan-ledger shows zero jobs or decisions against this plan
itself since 09-02 (both done that day, neither touching these two gaps).

### What we're doing next
Nothing queued here. Any insect/population-factory building happens under `garden_living_upgrade.md`
(I-0061), not this plan; the presence/count good and repeated-look enforcement have no job filed.

## Build order (when approved, not now)
GIVEN-trigger wiring is done (above). What's still open: the presence/count good for population
factories is the concrete missing piece; repeated-look promotion (trigger #2) still does not
exist as enforced code, only as a named rule.
