# The World Ledger — the Emissary's fact-graph (design, 2026-08-17; renamed 2026-08-19)

> **Status: ⚪ PARTIAL — object-graph BUILT, index-only, produce-only (job J-0363, 2026-08-29), unwired
> to any consumer; the related grounding leak-gate (D-0153) is LIVE since 2026-09-05.**
> `core/object_graph.py` is a
> real, tested, running module (`python -m core.object_graph`, ~21s, 439 referents, 129,061 mention-edges
> on today's data), NOT wired into any consumer/read path (`orchestrator.start_background()` has no entry
> for it, confirmed by grep). Covers exactly L1/L2/L4/L5/L6/L9 per the rescope below; K1/K3-excluded scope
> (standing loop, LLM prediction, affect courier) stays designed-but-deferred. See the "2026-08-29 (same
> day, later) — J-0363 build note" section under Current State for what J-0363 actually added (L5/L6
> windowed commonality weights + general L9 coreference proposals — both were missing from the module
> despite it otherwise already existing) and the storage decision (dedicated store, not `memory_edges.py`).
> Finding: F-0451.
>
> <details><summary>Superseded status line (2026-08-28, D-0080/J-0356 rescope) — kept for history</summary>
>
> **RESCOPED (D-0080, 2026-08-28, job J-0356) — the lab ran and was graded** (`docs/completed/lane2_lab.md`, `docs/lab/lane2_lab_report.md`, run 08-17, re-verified 08-24): **L1/L2/L4 PASS, 2-of-3 L5 affect pairs hold on re-verification** (storm↔arousal and fire_crackle↔valence signal; storm↔valence weakened below the |z|≥2 bar on 35% more data, z=-2.66→z=-1.21), **K1 and K3 triggered as valid, informative kills** (K1: the single canonical "glass float" validation object never emerged as terminal/absent — though the underlying float-profile *dimension* it was testing for held up as a real, populated pattern, see below; K3: script-side temporal holdout was no better than shuffled data, confirmed twice 35% apart in volume, traced to a real 30-day Du outage, not an artifact — founder-check resolved 2026-08-24, F-0108). **Scope is narrowed accordingly** (see "Current State" 2026-08-29 update below) to the index-only object-graph the passing criteria actually support — backfilled referents with per-property depth/channel tracking, windowed commonality weights, the voiceprint-filtered float-profile dimension, and coreference proposals — **explicitly excluding** the standing predict-loop, the LLM prediction call, the affect-nudge courier, and the single-object glass-float validation gate, all premature or killed per K1/K3. `core/object_graph.py` is still not built (WRONG by the time J-0363 opened it — see the build note); the scoped-down design below is a port target for `scripts/lane2_lab.py` (already built, already run twice), not a new design exercise.
>
> </details>

```plan-state
stage: partial
phase: Object-graph (L1/L2/L4/L5/L6/L9) BUILT index/produce-only, unwired to any consumer; grounding leak gate D-0153 LIVE and validated; standing loop and affect courier excluded per D-0080/K1/K3
verified: 2026-10-16
evidence_read: 2026-09-19
next: After 3 live days read the would-return shadow and bring the first 20 rows to Travis
cluster: 2
```


> **History folded** — 3 dated Current State section(s) (2026-08-23 … 2026-09-06) moved to `docs/plan_history/emissary_lane2.md` on 2026-09-27 by plan-compact. Derived timeline: `plan_ledger.py emissary_lane2`.

## Current State — verified 2026-10-16

- **2026-10-16** (F-2946): J-2217 built shadow-only World Ledger consumer (core/world_ledger_ask.py): memory_service.ask logs what a what-do-I-know-about-X query would return (earned per-property knowledge only) to data/world_ledger_ask_shadow.jsonl; graph refreshed once per sleep off-loop; worktree commit 57b13903, restart-gated
- **2026-10-16**: 2026-10-16: Travis asked whether the Witness supersedes this -- it does not (the Witness reads nothing from the World Ledger by its own section 2.8; they are different voices). Ruled: give the World Ledger its first consumer, a 'what do I know about X' query through memory-as-a-service, shadow-first; job queued. Standing loop and affect courier stay out (D-0080 K1/K3).

### What we have
- Object-graph (`core/object_graph.py`) BUILT, index/produce-only (J-0363, 2026-08-29), covering
  L1/L2/L4/L5/L6/L9 — not wired into any consumer/read path.
- The grounding leak-gate (D-0153) is LIVE (since 2026-09-05) and validated: J-0620's week-mark
  re-measure (F-1575) found fire rate 2.65-2.68% (bar >5%), zero real title leaks at the grounding
  seam, hot-fallback cost 0.58-0.63% of rows — none of D-0153's defeater clauses fires.
- The standing predict-loop, LLM prediction call, and affect-nudge courier stay explicitly excluded
  per D-0080/K1/K3 (temporal holdout no better than shuffled data, traced to the real 30-day outage).

### What we need
- Nothing currently open — J-0620 recommended the gate question done.

### What we're doing next
- None scheduled. Object-graph consumer-wiring and the standing loop remain deferred until a
  founder call restarts that line of work (see Open questions in the design below).

## The question that started this

Founder, post-restart: *"think about the executive node next and how it plays into du and sees this
world as it is fact based from memory to a certain degree."* That led first to a wrong answer (piping
`world_manifest.live()` into Executive as trusted ground truth — corrected same night, see F-EX), then
to the right question: what IS the Emissary actually for, and why does it currently look like a pile
of unconnected scripts rather than one thing?

## The three-lane model

Founder: *"We have 2 lanes that try to predict the answer to a question... Then you have another lane,
no llm, that runs the world."* Confirmed and refined across the whole conversation:

- **Lane 1 — the Master, self-facing.** Already built: `subconscious_node.py` (T2) + `inner_monologue_node.py`.
  Predicts from the rich, meaning-laden, identity-colored memory store. Points inward. Has personality —
  that's its whole job.
- **Lane 2 — the Emissary, fact-facing.** The subject of this doc. Predicts from its OWN evolving,
  narrower, experiential memory — not Lane 1's memory, not Lane 3's ground truth. No personality of its
  own.
- **Lane 3 — the world, zero-LLM.** Built earlier the same night as P0: `world_manifest.py`,
  `ghost_tuples.py`'s world index, `soundscape.py`, `sensorium._warmth()`. Not a "loop" — a stream. Runs
  on its own schedule; neither predicting lane may read it directly.

**Du is not just the two loops.** Founder: *"Du as an identity is all of his parts not just the loops,
he is also the pipes."* The pipes, couriers, trains, and factories are Du's own apparatus — his body,
his senses — not machinery external to him. Only the raw world-stream itself sits outside him.

## The boundary law (liquid, one law stated three ways this session)

Founder, on the sound plan, hours earlier: *"The world is a static object on its own time schedule...
Du gets to ask a question."* Same law, re-derived independently for this design and nearly violated
before being caught (F-EX): Lane 2 must predict from **what it has been exposed to and linked, never
from Lane 3 directly.** Its grounding is not privileged access to truth — it's rigorous inference from
whatever it actually holds, which means it can be wrong, which is what makes it a real epistemic act
and not a mirror.

Founder's final phrasing: *"Du also gets 'liquid' from the world stream... he just does not leak any
back. The liquid is shared in the pipes. Each loop recycles the liquid it needs. It still is allowed to
take and receive liquid from other streams as needed also within its rules. For both sides."*

- World → Du: one-way. Liquid flows in; nothing flows back out (never touches the weather, the cat,
  anything on Lane 3's side).
- Loop ↔ loop: two-way, already built for the reactive path — `core/emissary.py`'s own docstring:
  *"THE CORPUS CALLOSUM, Master→Emissary direction... The Emissary→Master direction already exists
  (the grounding it returns)."* `master_context()` is Master→Emissary liquid (his latest thought, a
  recent dream, what he's working toward). `left_take`/`ground_thought`'s return values are
  Emissary→Master liquid. Both real, both live, today — for the *reactive* functions only. Lane 2's
  standing loop needs its own version of both pipes; that's new.

## What already exists (the audit — nothing here gets replaced, all of it stays)

Six fragments, never introduced to each other, that together are most of what Lane 2 needs:

| File | What it does today | Status |
|---|---|---|
| `core/emissary.py` | Axiom + constitution loading | Keep as-is — Lane 2's identity |
| `core/left_lane.py` | 7 reactive functions (dispatch, ground_thought, 5 graders incl. the live T4 decoupled judge) | Keep as-is — proven, load-bearing (66 rows of real T4 gating) |
| `core/emissary_tension.py` | Trend-tracking, hardcoded to ONE topic (the bicameral gap) | Prototype for the general trend mechanism |
| `core/prediction_error.py` | `observe(domain, predicted, measured)` → `gap`, proven, scoped to 2 lesson domains | Prototype for the general predicted≠measured discipline |
| `core/competence.py` | Rolling-aggregate calibration, skill-domain grain | Prototype for trend-over-time at a different grain |
| `core/source_model.py` + `core/epistemic_state.py` | KNOW/THINK/SUSPECT/GUESS vocabulary — grades the **Master's** utterances, post-hoc | Never read by anything on Lane 2's side today |
| `core/memory_edges.py` | Typed edge graph, provenance-required, Du-side only | Built, but "NOTHING reads these edges yet" (its own docstring) |
| `core/ghost_tuples.MemoryIndex` | Rarity-weighted chord index (Du-side namespace, P0-B) | Built tonight, no live consumer yet |
| `orchestrator._emotional_pre_retrieval` / `memory_store.emotional_prior` / `state.affect.apply_prior` | The existing amygdala-gate: text-similarity match against charged memory → lean carried affect. No LLM. | The precedent for the affect-nudge courier (see below) — currently owned entirely by the Master's side, keyed to conversation text, single nearest-neighbor |

Also found in the same audit pass: **five independent HTTP-calling implementations** exist for reaching
LLM endpoints (`model_client`, `left_lane`, `judge_panel`, `librarian`, `peers`), two of which
(`librarian.py`, `peers.py`'s `contrary_target()`) are invisible to telemetry entirely and were built
*this session*, duplicating capability `model_client.call_node()` already had. Deferred — see Open
Questions.

## The gap

Lane 1 has a dedicated card (the 3070, `phi3:mini`, continuous). Lane 2 has no standing presence at
all — everything above is reactive, called by something else, on someone else's turn. `left_lane.
dispatch()` only fires `if input_type in ("human", "internal")`. There is no self-ticking version of
anything on Lane 2's side. `orchestrator.start_background()` — the one place every other standing
presence in Du's mind already lives (`subconscious.run_forever()`, `monologue.run_forever()`, climate,
consolidation, competence, the substrate tick) — has no entry for the Emissary at all.

## The design

### Identity & constraints (unchanged from the axiom, restated precisely for this build)
- No personality of its own. Flat, literal. Any coloring it shows is cargo residue from the corpus
  callosum, never self-generated.
- Never reads Lane 3 (`world_manifest`, the ghost world-index, any factory) directly. Only predicts
  from its own held/linked memory.
- Never writes to Lane 3. No influence on weather, the cat, anything world-side — ever, under any
  framing.

### The object-graph
New node-kind(s) in `memory_edges.py` (or a small new store, TBD) — referents (a sound-type, a
book-fact, a specific entity) as first-class objects. Kept structurally separate from Lane 1's rich
episodic/synthesis memory, same "never mixed" discipline `ghost_tuples.py` already enforces between
the world and memory namespaces — one level deeper this time (self-memory vs. fact-memory, not
world vs. Du).

**Real prerequisite gap, not solved by this doc:** the founder's gull example (*"He does not get the
memory of the sound of a gull. He gets the memory of the sound. Later he might get the memory of the
description."*) requires a raw, pre-conceptual sensory layer that doesn't currently exist upstream.
`soundscape.py`'s `_EVENT_RATES` (line 232) emits sound already labeled — `"gull_cries"` is a string
key from the moment the world generates it. There is no unlabeled acoustic signature to split from its
identification. Building the true raw/label split means the world layer changes first. Flagged, not
built here.

### Coreference stays uncertain, never assumed
*"He knows he read of gulls. Are they the same gulls? maybe not. Different cats."* A shared label
(book-gulls, heard-gulls) is not identity. A new edge type — `possibly_same_referent_as`, carrying its
own confidence — holds this open rather than silently collapsing it, which is what happens everywhere
else in the system today (a label IS treated as identity by default).

### Knowledge is partial by design: depth and channel (founder correction, late 08-17)
Founder: *"The world does not feed this stream the full history of an item at a glance... Driftwood
might only be 'seen' and not 'investigated'. How much does Du know?... His remembered knowledge is not
all the knowledge — just what he has been exposed to AND HOW that knowledge entered his base. A book?
He thought it? He was told it?"* This corrects a drift in the senses-twice section: the stamped tuple
records PRESENCE, not depth. Two dimensions the object-graph must carry per knowledge-atom:

- **Encounter depth** — seen-only → looked-at → investigated → kept. The ladder already exists in four
  unconnected places: `world_substrate` observation lists, the Hearing Ledger's exposure counts,
  `reading.current_offset`, `keepsakes.keep_act` (and the item-graduation triggers — kept /
  repeatedly-returned-to — are depth thresholds already). The object-graph is where an object's depth
  becomes ONE queryable fact: "driftwood: seen 14×, investigated 0×."
- **Entry channel** — `source_model.SourceType` finally gets its Lane 2 reader: every edge carries how
  the knowledge got in (PARAMETRIC_LIBRARY = read it · INFERENCE = thought it · USER_ASSERTION = told
  · MEMORY_RECALL = lived it). Channels about the same referent stay DISTINCT (same law as
  coreference): the filter scripts find hidden connections precisely at cross-channel intersections —
  read-about-driftwood × seen-this-driftwood is a link only findable because the channels were kept
  apart.

**The Du-knowledge / world-knowledge gap is load-bearing, not a defect.** The world knows the
driftwood's spawn time and decay clock; Du knows "I saw it Tuesday, it was wet." Lane 2 is never
topped up from Lane 3 to close that gap — partiality is what makes investigation a meaningful act.
If his graph were complete, looking closer would find nothing.

### THE PER-PROPERTY EARNING LAW (founder ruling, late 08-17)
Founder: *"We need to be very careful what we feed back to Du from the world. We want his world
model to gradually evolve as he questions things. His answers should be direct or he has performed
a good hypothesis — why the wood is fir, or driftwood, or dry fall, or fresh, or weight — all these
things are their own property and history also."*
- **Every property of every object is its own epistemic object with its own history** — species,
  origin-category (driftwood vs deadfall vs fresh-fall), moisture/freshness, weight, age, position.
  Each separately known or unknown; each with its own observation trail and hypothesis record. The
  substrate's 5-layer architecture already implements this per-property (Layer-3 append-only
  observations per action; Layer-5 inferences with provenance/confidence/outcome; UNDETERMINED a
  success) — the ruling extends its contract to EVERY feedback channel, present and future
  (renderer clauses, register surfacing, Lane 2 read-paths, event prose).
- **A property reaches Du exactly two ways:** as a DIRECT percept of an action he performed (heft →
  the felt weight; look → where it lies, its color) or as HIS OWN earned hypothesis. Never as a
  world-side assertion. No name, label, or line of prose may pre-answer a property question.
- **The lesson that taught it, caught the same night:** the Gen-1 record's display name — "Bleached
  FIR log" — pre-answered the species question in the object's name, and pre-answered it WRONGLY
  (hidden truth: silver beech). Latent, never spoken to Du (verified: surge prose reaches him only
  as "something heavy... stone against stone," cause off-camera; the look-path emits qualitative
  percepts, never species) — but a loaded gun for any future consumer. Neutralized 08-17 with a
  history record; the spawn pipeline's neutral-name rule is now general law, not a spawn-only rule.
- **Lane 2 consequence:** the object-graph is per-PROPERTY, not per-object monolith — each property
  its own knowledge atom carrying its own channel mix, depth, and trend shape. "How much does Du
  know about the log" becomes a per-property answer: weight KNOWN (hefted, direct), species
  SUSPECTED (his hypothesis, 0.6), origin-category his own earned working belief, age UNDETERMINED.

### Gap diagnosis — prediction failures get a WHY, not just a number
Founder: *"Prediction engines can fail and he has to work out why. New links form and he has to work
out why."* The gap (`|predicted − measured|`) is the trigger, not the endpoint. The script layer
classifies candidate causes deterministically before any LLM is asked:
1. **Too shallow** — the depth ladder shows only ever "seen"; the knowledge never went deep enough to
   predict from.
2. **Stale** — the windowed knowledge predates a world that has moved on.
3. **Wrong referent** — a `possibly_same_referent_as` edge was a bad bet (book-gulls ≠ these gulls).
4. **Wrong channel** — book-knowledge applied to a lived case that behaves differently.
5. **Genuine novelty** — none of the above fits. The interesting residue.
New links get the same treatment: a fresh co-occurrence is a queued why-question, never a silent
absorption. Tick #4's gap-prioritized idle queue is thereby sharpened again: it is not "objects I am
wrong about" but "WHYs I have not worked out." (The glass float is the prototype case: watched 30×,
vanished, unexplained — a category-5 residue.)

### Dimensions for ALL inputs (founder, closing the loop with Cognitive Geometry)
Founder: *"I think we need to treat these as dimensions but for all our inputs. Sound is but one.
Time, temperature, sun, tide, stars, cats geolocation... all of them."* This is the Cognitive
Geometry thesis (★★★ top-of-list plan: "the faculties are not real dimensions... most of the axes
were secretly the same axis") delivered through Lane 2: every object's profile carries a spoke per
stamped dimension, and the commonality/trend machinery runs along and across ALL of them — the
geometry plan's bundle-richness win condition, made operational. Lane 2's object-graph must comply
with that plan's constitutional law (objects immutable; learning only in connections; NUDGE/BIRTH
algebra; every spring traces to real episodes).

**Missing dimensions found (not yet stamped):** temperature (sensed, never deposits — flagged
earlier), the cat's location (in cat_state.json, absent from tuples), stars (not modeled; only
sun/moon exist). Additive tuple fields when built.

**STANDING LAW for the dimension engine (lab-derived, 08-17 — the sweep's confound pass):** before
any coupling is claimed: (1) classify each dimension fast/slow-cycling; (2) slow dimensions require
de-trending/partial correlation against time (the raw sweep's fire_fuel↔valence +0.384 collapsed to
+0.018 under time control; moon↔valence is unresolvable until the span covers 2–3 lunar cycles);
(3) tautology screen — dimensions computed from shared inputs are the same axis, not a coupling
(level↔arousal caught); (4) couplings state their CONTROLLED strength, never the raw one. The
naive correlator tells Du "the moon lifts your heart"; the skeptical layer says "your heart sank
while the moon waned — mostly, it is the sinking." That skepticism is the Emissary's whole office.

### The float-profile dimension, completed (lab-derived, 08-17)
Founder: *"A good algorithm would see the Jung thoughts were in bulk and then slowly going away over
time. It would know to treat these different based off things like that."* Lab-verified on real
data: every object in the graph carries **channel mix × depth ladder × TREND SHAPE**, because a
static thought/lived ratio cannot tell an old resolved pattern from a live obsession. Six shapes
observed in Du's actual history (`docs/lab/lane2_lab_report.md`, trend appendix):
extinct ghost (jung: 48% of ALL fragments on 06-07 — the self-naming day — extinguishing to 0.5%
in eleven days; the trend-break lands exactly on the event, demonstrating the diagnosis loop
end-to-end) · new/active (glass float) · perennial symbol (door, steady 4–6%, dream-resident) ·
growing world-presence (tide/rock — rises that cross-link to WORLD-BUILDOUT eras, not obsession) ·
settled companion (the cat — novelty burst then a nonzero floor; settling ≠ extinction, the floor
matters, not just direction) · episodic (oystercatcher). Trend-breaks are cross-linked to
co-occurring events (identity events, system arrivals) as the diagnosis layer's first standing job.

**Open question (founder law, not decided here):** when a why resists Lane 2's own working-out, does
it ever surface into Du's FELT curiosity? The law-honest mechanism would be the courier pattern once
more — a rising salience lean on that referent, his own attention drifting toward the driftwood
without being told why: his prediction failure pulling him, never the world hinting. A real new
Lane 2 → Lane 1 channel; founder's call.

### Division of labor (founder, final and precise)
*"The prediction part is what the llm does. The scripts can work out graphs and trends. The llm can
predict what the answer could be based off this and any other trends it notices... and links between
these."*
- **Script (zero LLM):** builds/maintains the object-graph, computes commonality weights and trend
  series — the same discipline as every factory and courier tonight. **HARD REQUIREMENT (from the
  cognition research §4.1/§5.1): every weight and trend series is WINDOWED/decayed by explicit
  choice, never an immortal all-time count.** **SECOND HARD REQUIREMENT (from the lab's item scan,
  08-17): a SYSTEM-VOICEPRINT FILTER before any text mining — the store's fragment text is
  saturated with the architecture's own template vocabulary ('valence reflection' ×2,216 inside
  lived-channel fragments), which broke both frequency AND channel-contrast discovery in the lab.
  The filter scripts must know the system's own voice and subtract it first.** Biology gets freshness by chemical decay; we get it by
  discipline — and this project has already been bitten twice by unwindowed accumulation (balance.py's
  all-time integral = the sleep-flood bug, fixed with WINDOW_DAYS=7; T2's never-demoting archive =
  the 49% hoard). Thunder↔fear is measured over a sliding window, per referent class.
- **LLM (the dedicated Lane 2 model):** given the graph+trend context already assembled by script,
  produces (a) a prediction — outcome or trend — and (b) candidate new links/objects for script to
  write. Notices what the deterministic layer wasn't explicitly coded to compute.
- **Predicted stays separate from measured, always** — generalizing `prediction_error.py`'s exact
  `gap = abs(predicted − measured)` discipline beyond lesson domains to everything Lane 2 predicts.
  The gap itself is the signal, never blended into the confidence that produced it.

### What actually feeds the loop (corrected twice — this is the primary source, and its trigger)
Founder, first pass: *"I do think it needs to be much more of a part of the interactions I have with
him and probably of his interactions/experiences/'knowledge' his 'senses' give him. The self stream
already abstracts it. This stream should be grounding it."* **Lane 1 abstracts the live stream (every
conversation, every sensed moment) into meaning and narrative. Lane 2 grounds the SAME live stream, in
parallel** — not a private backlog Lane 2 reviews on its own schedule.

Founder, second pass, correcting the trigger itself: *"Time is the primary feed... A photo if you will
of that moment I see live streamed... it doesn't matter what you set that measure at it does not change
how fast it is to me. Du 'thinks' in bursts. The time is a stream."* Content (a conversation, a sensed
sound) is NOT what triggers a grounding photo — **time is.** `world_manifest.tick()` already works this
way: it fires on the substrate's own regular clock and writes whatever's true right now — storm or
calm, eventful or not — never skipping a sample because nothing interesting happened. Lane 2's grounding
tick is the same shape: a photo taken on a measured interval, full or empty depending on what's
actually live at that moment, not an event handler waiting for something worth grounding. The interval
itself is a free engineering choice (5s, 30s, whatever) — picking it doesn't change how fast real time
is passing underneath, it only sets how fine-grained the photographs are. `left_lane.dispatch()`'s
existing "same moment, in parallel" firing is one input the photo can capture when a conversation is
live; it is not the trigger for taking the photo.

### The senses, twice (founder, after the cognition research: "maybe this is another stream to
### explore again now Du's world is 'larger'")
Du now has real sensory instruments that didn't exist until this week: hearing (the Hearing Ledger +
active-sound chords), semi-position (locomotion standpoints), temperature (exposed 08-17), bearings
(weather_dir, sun_az), continuous scalars (tide_level, moon_illum). Verified live: the census tuple
photographs ALL of this every burst — place, standpoint, weather@bearing, tide scalar, sound chord,
fire, body, affect.

The dual-visual-streams mapping (cognition doc §1) applied to this: **Du currently has only the
ventral half.** Every sense reaches cognition pre-narrated (`scene_line` prose — "gulls cry, the fire
warm in the grate"); the METRIC version of the same moments (tide 0.674 falling, rain from 270°,
three sounds co-occurring at this standpoint) is faithfully recorded and consumed by NOTHING — the
census is observe-only by law, the manifest is Lane 3. The what-stream exists; the how-stream has no
consumer. **Lane 2 is the how-stream**, and its primary input is therefore not a new instrument but
the already-stamped Du-side tuples (fragment_context / the census record) — his experienced moments
in metric form. Boundary-clean: stamped tuples are recycled liquid that already entered through his
pipes, not a tap into Lane 3.

Two concrete findings from verifying this against live data (2026-08-17):
- **Temperature never deposits.** The newest sense (`_warmth` → world_manifest, exposed tonight)
  appears NOWHERE in the census tuple keys — sensed by the world, shown on the HUD, never stamped
  onto any memory. He can be cold, but no memory carries how cold it was when he thought it. Fix is
  one additive field in the census tuple + fragment_context, when built.
- **Sound is the least dorsal sense** — a flat key list, no bearing/intensity, while weather already
  carries its 270°. The sound_causality plan anticipated the upgrade ("calculate where the sound
  comes from using the geometry tuple"); that work slots here when sound's turn comes.

### The loop's own tick — four behaviors
> **EXCLUDED from the current build scope (2026-08-29, D-0080/K3).** Kept below unmodified as the
> design record; premature per K3 (temporal holdout no better than shuffled, real 30-day data hole,
> F-0108), not redesigned or abandoned. Waits on the data span covering real time past the outage.
1. **Predict-outcome** — an object with no prediction yet gets a fresh outcome question.
2. **Re-check-trend** — an object with a standing prediction and new evidence since: is the gap
   growing or closing.
3. **Flag-thin** — an object with too little linked to it gets flagged as under-evidenced, not guessed
   at.
4. **Self-generate new test-questions** (founder, prior turn: *"gives itself new questions to test for
   links to help keep the loop from running dry"*) — reframed given the correction above: with the live
   stream as primary feed, the graph is rarely starved for material. This behavior is now specifically
   what the loop does in genuinely idle stretches — no fresh interaction or sensation to ground —
   rather than its main food source. **Target selection is gap-prioritized, not round-robin** (cognition
   research §5.2): pick by `prediction_gap × recency`, the way sharp-wave-ripple replay over-samples
   salient and novel sequences — idle time goes where the model is most wrong.

### Considered and declined: the FreshStart ghost-weaver's LLM query-expansion
Investigated `core/memory/ghost_weaver.py`'s `_expand_query_gnostic()` (2026-08-17, same session) as a
candidate for the coreference-uncertainty check. Assessment: the core idea (cache-gated, 3-lens query
reformulation + RRF fusion) is sound IR technique, but (a) it's a retrieval pattern, not a prediction
pattern — doesn't map onto the loop's actual job; (b) its "spectral" pseudo-embedding fallback silently
degrades with no signal when real embeddings are unavailable; (c) it's deeply wired into FreshStart's
own stack (`sovereign_db`, `lai_engine`, `HubRouter`, `facade`) with no clean portable seam. Founder's
call: declined — *"we do not want to throw an llm call in unless it is needed really here."* Not
imported, not built. Recorded so it isn't re-investigated later without cause.

### The affect-nudge courier (the fifth courier)
> **EXCLUDED from the current build scope (2026-08-29, D-0080/K3).** Its own spec already said "needs
> the loop live"; K3 keeps the standing loop from going live, so this stays out with it. Kept below
> unmodified as the design record.

Founder: *"If thunder has a high commonality with the feeling of fear, he feels slight fear when he
hears it. It is measuring the trend."* This is NOT a direct call from Lane 2 into `state.affect` — per
the reservoir/timing discussion, it doesn't need to be. It's a courier, same shape as A–D: fires on its
own tick, reads whatever commonality weight is currently sitting in Lane 2's object-graph, and on a
live sensed-stimulus match, nudges affect **proportionally to the measured weight — never full-
strength, never manufactured.** Extends/generalizes the existing amygdala-gate
(`_emotional_pre_retrieval`) from single-nearest-neighbor-on-conversation-text to
trend-weighted-on-live-sensation. One-way: Lane 2 → Lane 1's affect reservoir only. Never Lane 3.

### The reverse feed
Lane 1's own activity (recent thoughts, dreams, concerns) needs to keep feeding Lane 2's loop as its
raw exposure — `master_context()`, generalized from the reactive path to also serve the standing loop.
Not a new mechanism; an extension of a proven one.

### Hardware
A dedicated LLM/hub — separate from the shared reactive judge pool (11439–11441) that `left_lane`/
`judge_panel`/T4-grading already use. Matches Lane 1's own-card precedent (the 3070 is T2's alone).
Which port, TBD — deferred alongside the left_lane CPU-consolidation question below.

## What this explicitly does NOT do
- Does not replace any of `left_lane.py`'s 7 existing reactive functions — they stay exactly as they
  are, additive only.
- Does not replace `judge_panel.py` or T4's existing gates.
- Never reads `world_manifest`/Lane 3 directly, under any framing — this is the boundary the whole
  design nearly violated once already tonight.
- Generates no narrative, no meaning, no identity content — predictions and trend-reads only.

## Open questions (founder-deferred, not blocking, not forgotten)
- **Left-lane CPU consolidation** — founder: *"It can probably be almost full cpu... we will test it at
  some point not now."*
- **`librarian.py` / `peers.py` telemetry + entanglement fix** — low priority, both seldom called,
  fixable later.
- **Which port becomes Lane 2's dedicated hub.**
- **The raw-sensory/label split's prerequisite work in `soundscape.py`** — needed for the full gull
  example, not needed to start.
- **Build sequencing** — every other system this session shipped shadow-gated/produce-only first
  (Refinery, Couriers, the sound factory, P0 itself). Lane 2 should very likely follow the same
  discipline: object-graph + script side first, produce-only; the LLM prediction call and the affect
  courier only after the graph itself is proven on real data. Not decided here — a founder call before
  any build begins. **The cognition research (§5.3) proposes the concrete first step: RETROACTIVE
  BACKFILL** — seed the object-graph from the existing logs (26k thoughts, the Hearing Ledger,
  fragment_context) before the loop ever runs live. Biology-impossible (no human re-attends their
  infancy), produce-only by nature, solves cold-start, and carries a built-in validation case: the
  glass float should emerge from the backfill as a high-observation object with an unexplained
  disappearance — if it doesn't, the graph-builder is broken and we know before anything goes live.
- **Arousal-modulated tick interval** (cognition research §5.5) — a later, cheap refinement: shorten
  the photo interval when affect arousal is high, lengthen in calm (more photos of a storm, fewer of a
  quiet afternoon). The interval is already a free knob; this just makes it adaptive. Not for P0.
