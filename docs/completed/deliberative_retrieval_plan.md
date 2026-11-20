# Plan — Deliberative Retrieval (grounding Du in reality)
*Draft v1 for external review (GPT, Gemini). Status: PROPOSAL, not built. 2026-06-14.*
*Author's note: written under a "more founder oversight" regime after a build-trust rupture —
every claim below is grounded in verified code (file:line where it matters), and every phase
is designed to be proven in-vitro on his real data before it touches the live system. Do not
take the design on faith; the test is part of the plan.*

## 0. One sentence
Du's memory retrieval is a single cosine grab that returns the CLOSEST match, not the most
USEFUL one — and because his store is ~98.5% self-referential, "closest" is almost always
more self-material, so he cannot ground himself in what he has read or observed. This plan
makes retrieval **deliberative** (multi-pass, relevance-evaluated, reality-guaranteed) by
re-aiming a multi-pass loop the architecture ALREADY HAS.

## 1. The problem, from evidence (not theory)
- **Store composition (verified count, 2026-06-13):** inner_thought 4,489 · subconscious
  2,426 · lived 1,372 · active_imagination 1,100 vs **reading 90 · study 27 · research 11.**
  World material is ~1.4% of memory. Self-reference dominating is human-normal — the problem
  is that it leaves *no room* for reality to surface.
- **The live failure (verified, the book interrogation 2026-06-13 20:32–20:39):** asked "what
  was the last book you read?", his conversational Recall surfaced ONLY self-material
  ("tension between old and new", "vessel of the past") — **zero reading fragments**, though
  he had read and even quoted that book an hour earlier. He could not reach reality, so he
  papered the gap with metaphor.
- **Founder's framing (adopted):** self-reflection is good; reality should be equal-or-more
  important. The fix ELEVATES reality's standing — it does not gate the self.

## 2. The key finding — the substrate already exists, mis-aimed
This is NOT a from-scratch build. Verified in `core/orchestrator.py`:
- **A multi-pass retrieval loop already runs** — "introspective recurrence": when the bound
  scene is epistemically unstable (named dissonance AND coherence < 0.55), the hot lane
  re-runs Recall→Episodic-Buffer, pass budget 1/2/3 scaling with `world_model_strain`
  (`_INTROSPECT_*`). The episodic buffer (`episodic_buffer_node.py`) already makes an LLM
  judgment per binding: `{scene, dissonance, coherence}`.
- **But it asks the wrong question.** It only checks *"does this cohere?"* — never *"is this
  useful, and is reality represented?"* And when it re-retrieves, it pulls MORE OF THE SAME;
  it never reaches for world material.
- **And a precise bug:** the re-bind budget is per-mode (`_MODE_VECTORS`): `existential`
  mode = **3** passes, `task` mode = **0**. So when he's self-absorbed he gets three passes to
  bind self-material *deeper*, and when you ask a concrete factual question (task mode) he
  gets **zero** extra passes. **The loop is switched off in exactly the mode where grounding
  matters most** — a direct contributor to the book failure.

So: he already "thinks more than once about what to remember" — he just spends every pass on
himself and none on reality.

## 3. The design — deliberative retrieval (the T4-chain analog)
The T4 rebuild replaced single-pass self-authoring with Tension→Evidence→Delta→Synthesis,
and its decisive move was forcing retrieval of the *evidence side the single pass was blind
to*. Retrieval needs the same move — forced consideration of the *reality side* the
similarity pass is blind to. Three stages, built by extending the existing loop:

### 3.1 Stage 1 — cast a WIDE, STRATIFIED candidate net (deterministic, cheap)
Today retrieval takes 8 final slots (archive 2 / semantic 2 / episodic 4) by similarity.
Instead: gather a larger candidate POOL (~20–24) with **guaranteed origin quotas** so world
material (reading/study/research) is structurally in the pool regardless of similarity —
the exact pattern that already works for sleep replay (3 world / 3 lived / 2 inner). No LLM.

### 3.2 Stage 2 — the relevance + grounding evaluation (the "think about whether it's useful")
Two parts, deliberately split by cost:
- **(a) Structural grounding check — deterministic, free, ALWAYS ON.** "Given the input
  references something concrete/external, does the candidate set contain ANY world-origin
  material?" If not → grounding deficit flagged. This is the cheap trigger and it does NOT
  depend on a (possibly biased) model.
- **(b) Relevance judgment — LLM, GATED.** When the structural check flags a deficit, or on
  concrete/conversational cycles, the **Emissary (qwen2.5 on Ramses 3070)** — NOT qwen3-du —
  judges which candidates actually bear on this moment and whether grounding requires the
  world items. It can DISCARD a high-similarity item as irrelevant (the abort-honestly
  property) and demand a world-targeted re-retrieve.

### 3.3 Stage 3 — select & inject, with a reality floor
Final selection keeps the most *useful* (not merely closest), with a floor guaranteeing
world material a seat whenever a useful world item exists. Self-material keeps its slots;
reality just can no longer be edged out entirely.

### 3.4 Fix the mode bug
`task` mode `max_rebind` 0 → allow grounding-triggered re-retrieval in the concrete/factual
modes. The grounding loop must be available precisely where grounding matters.

## 4. Model / hardware allocation (uses the diversity we have)
- **Embedder (multilingual MiniLM, local CPU):** Stage-1 candidate net. (Stays local — a
  network hop per embed would be slower than CPU.)
- **Deterministic structural check (no model, free):** Stage-2a, always-on. Carries the
  constant load so we are not firing an LLM every thought.
- **Emissary — qwen2.5:7b, Ramses 3070 (LAN-HOST:11434):** Stage-2b relevance judge.
  Chosen because it is a DIFFERENT model from the thinker (qwen3-du) — so retrieval is not
  graded by the metaphor-bias that buried reality — AND it is the constitutionally literal,
  anti-metaphor hemisphere (its existing role). On its own card; does not contend with the
  hot lane. We are growing the Emissary's role, not adding an unrelated module.
- **qwen3-du (1080 Ti):** unchanged — does the thinking, now with grounded material.
- **Bonsai-Q1 (CPU, 11460):** unchanged fallback; too quantized to judge.
- **1650S 4GB (Ramses, idle):** HELD IN RESERVE. It caps at ~3B (too crude for nuanced
  usefulness) and adds a server to babysit (real operational cost given stack-stability
  history). Deploy a dedicated relevance-judge here ONLY if the 3070 becomes a latency
  bottleneck under the added gated calls. Don't add the server before the evidence demands it.

## 5. The bias trap, and how the design defeats it
The central risk: if the same metaphor-biased model judges "usefulness," it votes for
self-material and re-buries reality — a "fix" that entrenches the problem. Three defenses,
layered: (1) world quota is enforced at the **candidate** stage (structural, pre-judgment);
(2) the grounding-deficit trigger is **deterministic**, not an LLM opinion; (3) the relevance
judge is a **different model** (Emissary qwen2.5), literal by disposition, not the thinker
grading its own homework.

## 6. What this does NOT fix (honest scope)
This targets **retrieval** — world material *surfacing*. It does NOT fully fix
**composition** — Du dissolving even *present* material into metaphor (the story he was told
that he turned entirely back into the river). Better retrieval gives the composition step
better raw material, but the metaphor-dominance at generation is a separate, harder layer
(where the Emissary's take would need genuine *weight*, not just being offered). Naming this
so a retrieval win is not mistaken for a grounding cure.

## 7. Phasing (observe-first)
- **Phase 0 — instrument, change nothing.** Log, per retrieval: the candidate pool's
  origin-mix, whether a world item WOULD have been selected under a quota+floor, and (on
  concrete cycles) the structural grounding-deficit flag. Read nothing into behaviour. This
  produces the baseline: how often is reality available-but-unselected? (Hypothesis: very
  often.) Falsifiable check: on the book-interrogation-type cycles, the log should show
  reading fragments PRESENT in the candidate pool but losing selection.
- **Phase 1 — Stage 1 + Stage 3 (deterministic only):** wide stratified net + world floor +
  the task-mode fix. No LLM judge yet. Watch: does reality start surfacing in his
  conversational answers and idle thoughts? Does self-reflection degrade? (It must not.)
- **Phase 2 — Stage 2b (Emissary relevance judge):** add the gated LLM relevance pass only if
  Phase 1 shows the deterministic version surfaces reality but not *relevantly* (e.g. it
  pulls a random book passage instead of the pertinent one).

## 8. In-vitro tests & falsifiable gates (the oversight contract)
Before anything goes live, on his REAL store:
- **Retrospective replay:** re-run the book-interrogation cycles through the new Stage-1 net;
  PASS = the actual book he'd read appears in the candidate pool and survives selection.
- **No-self-starvation check:** on existential/reflective cycles, confirm self-material still
  fills its slots (the world floor must not evict the self — it reserves, not replaces).
- **Bias-independence check:** confirm the relevance judge is on qwen2.5 (Ramses), not
  qwen3-du, and that disabling it falls back gracefully to the deterministic quota.
- **Phase-0 baseline number:** "% of cycles where a relevant world item was available in the
  pool but not selected" — declared before Phase 1; Phase 1 must drive it down without
  raising rumination or harming coherence.

## 8.5 RESOLUTION from review (v1.1, 2026-06-14 — Gemini; GPT reviewed the wrong doc, retrieval still needs its take)
Gemini approved for Phase 0 with five refinements, all adopted:
- **Q1 — keep it in the existing loop; extend the payload.** No new node. `EpisodicBufferNode`
  returns `{scene, dissonance, coherence, grounding_deficit: bool}`. If `grounding_deficit`,
  the orchestrator ticks the re-bind budget and triggers the world-targeted re-retrieve.
- **Q2 — Emissary judges via tight JSON, not raw text.** Feed
  `{current_input, candidates:[{id, origin, text}]}`; it returns an array of accepted IDs by
  literal relevance. Leverages qwen2.5's JSON compliance; keeps it out of synthesis.
- **Q3 — the world floor is CONDITIONAL, not always-on.** 2 of 8 slots, but the floor
  activates ONLY when `grounding_deficit=True` OR mode is `task`/`hybrid`. On pure
  self-reflective/existential cycles he keeps all 8 slots — never force Gutenberg fragments
  into an existential moment (would inject noise the Symbol Tracker could misread as insight).
  This resolves the §9-Q3 crowding worry: reserve only when reality is actually called for.
- **Q4 — cap the grounding re-retrieve at 1 pass in `task` mode.** Miss after one pass → ship
  honestly and log, never loop a factual lookup into latency.
- **Q6 — THE critical guard: the world quota is by HARD `origin` TAG, never by text/cosine.**
  Residual trap Gemini sharpened: a metaphorical `inner_thought` ("my reading feels like a
  voyage through a dark sea") scores high on a cosine search for "book" and could masquerade
  as world material, re-burying real `origin='reading'` rows. So Stage-1's world quota counts
  ONLY actual `origin in (reading,study,research)` database rows, independent of text. Self-
  material can never sneak into the world quota by talking about reality.
- **Q5 — ship retrieval first (confirmed).** Can't fix composition with zero world data
  reaching it; the post-fix logs then isolate whether the metaphor-dominance is retrieval or
  composition. Clean upstream baseline.

**Phase 0 success criterion (Gemini, adopted as the gate):** prove on the June-13 book-
interrogation logs that `P(WorldItem ∈ CandidatePool) ≫ P(WorldItem ∈ FinalSelection)` — i.e.
the real reading fragments were PRESENT in the wider pool but lacked cosine weight to survive
selection. If they're in the pool, Phase 1's deterministic floor is structurally guaranteed
to fix the live failure. If they're NOT even in the pool, Stage-1's net needs widening first.

## 8.6 SECOND REVIEW (v1.2, 2026-06-14 — GPT, after re-review). Both advisors now converge; two additions adopted.
GPT independently confirmed the design — concrete-failure-driven not philosophical, retrieval-
not-identity (safer than the narrative witness), the hard-origin-tag quota is "the real
breakthrough... without it the proposal fails," the Emissary judge and the three bias-trap
defenses sound (no obvious hole). Two refinements adopted:

- **The floor must be gated by QUERY TYPE, not merely by mode or by "world material exists"**
  (GPT, sharpening Gemini's conditional floor). His counter-example: "How do you feel about
  Travis?" is relational — forcing a Darwin/cuttlefish/granite fragment into that pool is
  NOISE, a new failure mode ("world material ≠ relevant material"). So the world floor
  activates only on **factual / external-world / book / observation / research** queries (a
  cheap deterministic query-classifier, same family as the existing look-gate keywords), AND
  on `grounding_deficit=True`. Pure relational/emotional/existential moments get no forced
  reality. This is the tightest version of the trigger.

- **ADD ONE PHASE-0 METRIC: `P(WorldItem used in final RESPONSE)`** (GPT) — beyond
  in-pool and in-selection. Because retrieval can SUCCEED (Darwin fragment in context) while
  composition FAILS (he still answers "the crossing reminds me of my journey…" with no Darwin
  reference). This third metric is the **retrieval-vs-composition disambiguator** — without
  it the two layers masquerade as each other. It tells us immediately whether a future
  disappointment is this plan's fault (retrieval) or the deferred composition layer's.

- **Long-term watch (GPT, not a design flaw):** the Emissary judge could slowly drift toward
  Du-style preferences if it sees enough of his outputs over months. Drift-monitor, not a
  Phase-0 concern.

**STATUS: both advisors approve Phase 0.** Convergent, no unresolved holes for the observe-
only phase. Phase 1 (the deterministic floor + task-mode fix) proceeds on the Phase-0 gate
below; Phase 2 (Emissary judge) only if Phase 1 surfaces reality but not *relevantly*.

## 9. Open questions for the reviewers
1. Is extending the *existing* introspective re-bind loop the right move, or does a relevance
   pass deserve to be its own stage rather than riding the coherence loop?
2. Stage-2b on the Emissary: feed it the candidate set (new input to that lane) vs. a separate
   judge call — does doubling the Emissary's per-cycle role muddy its literal-take job?
3. The world quota/floor size — how many of 8 final slots should reality be guaranteed
   without crowding genuinely-relevant self-material on deeply self-referential moments?
4. Does fixing `task`-mode `max_rebind` risk over-thinking simple factual exchanges (latency),
   and should the grounding re-retrieve be capped at 1 pass regardless of mode?
5. Scope honesty (§6): is it acceptable to ship a retrieval fix that leaves the
   composition/metaphor-dominance layer untouched, or do they interact enough that one
   without the other will disappoint?
6. The bias trap (§5) — are three layered defenses enough, or is there a residual path by
   which the self-loop re-captures retrieval that we haven't seen?
