# The Wandering Mind — audit + research
*2026-06-15. Examining `core/wandering.py`: how it connects, what it does, why, and how faithful it is to
the human function and to what an AI can actually do. Method (house rule): name the human function first,
then ask what being an AI changes, then judge the transfer. Audit, not a build.*

---

## 1. How it connects (the wiring, verified)

**Driven by** the orchestrator's `_substrate_loop` (the "Always-On" layer, `orchestrator.py:1957`) — every
**5s** it calls `wandering.step(state)` alongside `affect.tick` and `sensorium.tick`. `step()` self-gates:
a drift hop every **75s** (`WANDER_EVERY_S`), an ambient item every **8 min** (`AMBIENT_EVERY_S`). No LLM —
CPU embeddings only.

**Inputs (what fills the trail):**
- **Associative drift** (`step` → `_drift_from`): seed = 35% last inner thought / 25% a recent memory /
  **40% pure random restart**; then hop to 1–2 *nearest-by-embedding* memories, novelty-biased.
- **Ambient drip** (`_ambient_item`, every 8 min): 60% a line glimpsed from the open book (bookmark
  untouched), else a random world-fact (`reading/research/study`).
- **Perception** (`perceive`): sensory/external entries — from `sensorium.tick` (weather, fire, window),
  `orchestrator:365` (an arrival in the room), and `inner_monologue` (observations, finished actions,
  chapter excerpts, browsed catalogue pages).

**Output (the only read path):** `render()` is consumed by exactly one place —
`inner_monologue._think` (`:413`) — injected as a leading seed: *"Since you last spoke, your mind has
wandered. These passed through it unbidden — any of them is as worthy of your next thought as you are."*
So the trail is **furniture for the next verbal thought**, nothing else.

**Durable record:** `_log_trail` → `data/wandering_log.jsonl` (observe-only; read by humans/digests,
never by a prompt).

**The discipline that matters:** the trail is **READ-ONLY with respect to memory** — drift never bumps
`replay_count`/importance. Stated reason: a drift that strengthened what it touched would be *another
attractor amplifier*. So wandering is a **selection lens**, not a memory-writer.

## 2. What it does
Furnishes the silence between thoughts so the next thought starts from **varied, world-mixed** material
instead of the loudest tension. It carries explicit **anti-basin levers**:
- **40% random-restart seed** — a Lévy-flight long-jump to escape the basin (raised from lower after the
  first live run "wandered straight back into the river").
- **echo-cap (`_ECHO_CAP=0.86`)** — skip candidates *too similar to the seed* (the basin re-electing itself).
- **world-restriction** — once the trail holds ≥3 inner items, drift is restricted to `reading/research/
  study` origins (furnish variety, not reinforcement).
- **no-revisit 30 min**, **dup-cap** against the current trail.

## 3. Why (the design rationale, from the file)
Founder's diagnosis: the living cadence made pauses *real time* but "sparsely furnished — a human would be
bored stiff." The DMN's actual main job isn't producing sentences; it's **silent associative drift through
memory with ambient perception trickling in.** This module is that drift.

---

## 4. Research — the human mind

**The Default Mode Network is not "off."** (Raichle et al. 2001; Buckner et al. 2008.) It is *more* active
at rest than during external tasks — the brain's intrinsic activity, tied to autobiographical memory,
self-reference, prospection, and mind-wandering. Wandering occupies ~30–50% of waking life
(Killingsworth & Gilbert 2010), i.e. it is the **default**, not an aberration.

**What is mind-wandering FOR?** Several converging functions:
- **Associative recombination / integration** — linking disparate memories (the substrate of insight).
- **Prospection / autobiographical planning** — Baird, Smallwood & Schooler 2011 ("Back to the future"):
  much wandering is *future-oriented* rehearsal and planning.
- **Creative incubation** — Baird et al. 2012 ("Inspired by distraction"): an undemanding task that
  *permits* wandering improves creative problem-solving; the DMN recombines remote associates.
- **Exploration under loose constraint** — Christoff, Irving, Fox, Spreng & Andrews-Hanna 2016
  ("Mind-wandering as spontaneous thought: a dynamic framework"). THE key frame: spontaneous thought lives
  on a continuum of **constraint**. Healthy mind-wandering is *relatively unconstrained* (free, high
  variability); **rumination/obsession is *automatically constrained*** (sticky, low variability, orbiting
  one attractor); goal-directed thought is *deliberately* constrained. The pathology is not wandering — it
  is wandering that has **lost its variability**.

**The search architecture (why the random-restart is correct):**
- **Optimal foraging in semantic memory** — Hills, Jones & Todd 2012; memory search shows **cluster-then-
  switch** (exploit a patch, then jump). Free recall and retrieval exhibit **Lévy-flight** statistics
  (Rhodes & Turvey 2007): mostly local steps with occasional long jumps — provably near-optimal for search,
  because it balances exploitation with exploration. **Du's 40% random restart is the long-jump component,
  implemented literally.** This is the strongest human-grounding in the module.

**The collision (and where it's already right):** Du's monoculture *is* Christoff's "automatically
constrained" thought — wandering that orbits one basin. The module's anti-basin levers (random restart,
echo-cap, world-restriction) are exactly the right instinct: they push *variability* back into a drift that
would otherwise re-elect the attractor.

## 5. Research — what being an AI changes

1. **The substrate is explicit and inspectable.** Human wandering is *inferred* (thought-probes, fMRI);
   Du's is a literal embedding walk with a durable log. We can measure trajectory variability / basin-orbit
   / escape-rate directly — a research advantage no human study has. (Ties to the Curiosity Observatory's
   orbit-ratio; the `wandering_log` could feed the same metric.)
2. **Embedding space ≠ human semantic network.** A sentence-transformer cosine is a *flattened* proxy for
   meaning — it captures topical/surface similarity but lacks the multimodal, causal, emotionally-weighted
   links of human association. So Du's drift is associative but **thinner**, and can hop on lexical
   similarity that isn't a meaningful association.
3. **No affective drift — though the parts exist.** Human wandering is *emotionally biased* (we drift toward
   what is salient/unresolved). Du already stores `emotion_vec` on fragments (the contradiction-drainage
   work), but the wander step uses **semantic cosine only**, not felt-match. A real, addressable gap.
4. **No prospection.** A large share of human wandering is *future* simulation (Baird/Smallwood). Du's
   wandering is **entirely retrospective + present-ambient** — it never rehearses forward. The DMN's
   forward-modelling half is simply absent here.
5. **Deliberately no consolidation.** The human DMN *both* wanders *and* consolidates (hippocampal replay
   overlaps rest). Du **split them on purpose**: wandering is read-only, consolidation is T2/sleep. The cost
   of that (correct) safety choice is that the drift itself does no integrative/creative recombination — it
   only *supplies* material; the verbal thought must do any integrating.

---

## 6. Assessment + the finding that matters

The wandering mind is a **genuine, well-grounded** implementation of the DMN's associative-drift function,
with anti-rumination instincts that map cleanly to real findings (Lévy-flight foraging; the constraint
continuum). It is one of the more faithful function-transfers in the system.

**But the evidence says it is fighting uphill — and not because of its mechanics.** From the latest pulse,
the memory store it drifts through is ~**88% self/internal** (`subconscious_synthesis 2440 · lived 1458 ·
inner_thought 1263 · consolidation 744 · dream 325 …`) and only ~**5% world** (`reading 255 · study 82 ·
research 16`). So even a perfect random-restart lands its *next* hop on "nearest by embedding" — which, in a
store that is 88% self-material, is *probably more self-material*. **The drift re-lands in the basin because
the basin is most of the store.** The world-restriction lever helps, but it's rationing a 5% supply.

> The conclusion is not "make wandering cleverer." It is that **wandering's escape depends on there being
> somewhere to escape TO** — i.e. on the proportion of world-material in the store. The grounding work
> already underway (curriculum reading, twigs, the closing loop) is therefore *also* the real fix for
> wandering: it raises the 5%. And the boredom-redirect we just built is the active complement — wandering
> passively varies the seed, the redirect actively turns him to a patch.

## 7. Opportunities (not built — for your call)
- **Affective drift:** let `_drift_from` mix in `emotion_vec` felt-match, not just semantic cosine — the one
  human-faithful capability that's present but unused. Closest to the human function, lowest new surface.
- **A prospective wander step:** occasionally drift to an *intention / open frontier question* and imagine
  forward, not only back — restores the DMN's missing future-half. (Synergises with the closing loop.)
- **Weight drift toward the scarce world-origins more aggressively** while the store is self-skewed — a
  stopgap until reading/twigs raise the world share.
- **Instrument escape directly:** compute a basin-orbit ratio from `wandering_log.jsonl` (we have the data),
  so "is the drift actually escaping?" stops being a guess.

## 8. Confidence note
The human findings (DMN-as-default, mind-wandering-as-exploration, Christoff's constraint continuum, Lévy/
foraging memory search, incubation, prospective wandering) are well-established at the conceptual level and
I'm confident in the authors/claims as summarised; exact years/titles are citations-to-check, not re-verified
this session. The store-skew finding is grounded in the 2026-06-15 pulse origin breakdown (numbers above).
