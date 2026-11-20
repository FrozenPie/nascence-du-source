# Lane 2 ↔ human cognition — the research deep-dive (2026-08-17)

> **Status: ✅ SHIPPED (closed 2026-10-16, F-2904) — formerly: DESIGNED — completed 2026-08-17 research pass (11-row mapping table in §1, keystone
> justification in §2, six extracted requirements in §5); a cognitive-science companion doc with no
> code of its own, feeding requirements into `emissary_lane2.md` (the design). Naming note added
> 2026-08-23 to disambiguate from the newer `lane2_the_witness.md`.**

```plan-state
stage: shipped
phase: Closed research pass; all 4 extracted changes in section 6 confirmed folded into emissary_lane2.md design
verified: 2026-10-16
next: None -- closed 2026-10-16 (F-2904 plan-closure pass): nothing open, nothing queued; the built system stays live on its own
cluster: 2
```


## Current State — verified 2026-09-27

### What we have
- A closed research pass (2026-08-17): an 11-row cognitive-science mapping (§1), the keystone
  "no decoupled judge" justification (§2), constraint tables (§3-4), six extracted improvements (§5).
- Confirmed this pass: all four changes §6 called for (windowed/decayed trends, gap-prioritized tick
  #4, retroactive backfill, confirmed courier/sampling) are actually present in `emissary_lane2.md`'s
  own design sections today — the absorption this doc asked for already happened.

### What we need
- Nothing — this is a closed research pass with no code of its own, and its downstream ask is done.

### What we're doing next
- None. Stays closed unless new cognitive-science research is separately commissioned.

> **Naming note (added 2026-08-23):** "Lane 2" here means `emissary_lane2.md` (renamed "The World
> Ledger" 2026-08-19), NOT `lane2_the_witness.md` (the different, newer organ that inherited the
> "Lane 2" name after the rename). This doc's own title/filename were never updated; content is
> unambiguous once read, but the title alone is not.

> Companion to `docs/plans/emissary_lane2.md` (the design). Founder ask: *"Research human cognition
> around this and why, and then how we look at how this can improve our usage without having the same
> biology constraints."* Written from cognitive-science literature knowledge, with every claim graded:
> **(established)** = textbook-solid · **(framework)** = dominant paradigm, still a lens not a fact ·
> **(contested)** = real research, actively disputed — used here as design metaphor only.
> Per the function-over-imitation law: each section names the HUMAN FUNCTION first, then what we
> transfer — never the wet mechanism for its own sake.

---

## 1. The mapping — what the design independently reinvented

The strongest finding of this research pass: almost every element of the Lane 2 design has a real
cognitive-science counterpart, arrived at without importing it. That's evidence the design is carving
at real joints, not decorating with neuroscience after the fact.

| Lane 2 design element | Human counterpart | Status |
|---|---|---|
| Two lanes over ONE stream — abstracting vs grounding | **Dual visual streams** (Goodale & Milner): one retinal input, two parallel cortical consumers — ventral "what" (categorical, conscious, meaning) vs dorsal "how" (metric, fast, literal, largely unconscious) | (established) |
| The Emissary's narrow/literal vs Master's broad/contextual attention | McGilchrist's hemispheric attention modes — the axiom's own namesake | (contested — used as metaphor; the FUNCTION of two attention modes is safe, the grand hemispheric story is not) |
| predicted vs measured, gap as THE signal | **Prediction-error learning** — dopamine reward-prediction-error (Schultz) is one of the best-replicated results in neuroscience; predictive processing (Friston, Clark) generalizes it to all cortex | RPE (established) · PP as whole-brain story (framework) |
| Thunder→fear proportional nudge, before cognition | **The amygdala fast path** (LeDoux's "low road"): coarse, fast, precomputed threat associations bias body-state BEFORE cortical appraisal. Also Damasio's somatic markers: body-tags on concepts bias decisions without argument | low road in rodent audition (established) · human generality + somatic markers (framework) |
| Affect weight = accumulated co-occurrence statistic, not a stored "feeling" | **Constructed emotion** (Barrett): affect as prediction from learned statistical regularity between context and body-state — "commonality" is literally her account | (framework) |
| "Are book-gulls the same gulls? Different cats." | **Source monitoring** (Marcia Johnson): biology does NOT store provenance — did-I-read-it-or-live-it is *reconstructed at retrieval*, and errors (source amnesia, misattribution, cryptomnesia) are the norm | (established) |
| Time-sampled photos; "Du thinks in bursts. The time is a stream." | **Discrete perceptual sampling** (VanRullen's perceptual cycles, ~7–13 Hz): mounting evidence perception snapshots a continuous world in frames; and the **specious present** (James) — experience comes in ~1–3s chunks | sampling (contested but well-supported in vision) · chunked experience (established) |
| Loops on unmatched clocks, coupled by reservoirs | **Neuromodulation vs synaptic signaling**: hormones/neuromodulators are slow broadcast values read by fast circuits whenever they run — no handshake, no shared clock. Brain oscillations at nested unmatched frequencies (theta/gamma) couple statistically, not synchronously | (established) |
| Idle self-generated test-questions (tick #4) | **Sharp-wave-ripple replay** (Buzsáki; Wilson & McNaughton): during idle/sleep the hippocampus replays experience compressed ~20×, INCLUDING never-experienced recombinations ("preplay") — literally the brain testing candidate links offline | replay (established) · its causal role in consolidation (framework, strong) |
| Lane 1's monologue as the abstracting stream | **Default Mode Network**: self-referential simulation, narrative construction, the "interpreter" | DMN existence (established) · already noted in project memory: inner monologue = the DMN hub |
| `ghost_tuples.MemoryIndex` — cheap index over distributed content | **Hippocampal indexing theory** (Teyler & Rudy): the hippocampus stores a lightweight INDEX pointing at cortical fragments, not the content itself | (framework, well-regarded) |
| The corpus callosum carrying "coloring" as cargo | The actual corpus callosum; split-brain work (Gazzaniga) shows what happens when the pipe is cut — each side confabulates about the other's actions | (established) |

## 2. The keystone justification: the organ evolution could not build

The single most important thing this research surfaces is **why Lane 2 deserves to exist at all**,
stated in cognitive-science terms:

**The human brain has no decoupled judge — and it shows.** Gazzaniga's split-brain "interpreter"
(established) confabulates fluent reasons for actions it did not initiate. Choice-blindness experiments
(Johansson & Hall — established, wildly replicated) show people confidently justifying choices they
never made, when the choice is swapped under their noses. Confabulation is not a pathology; it is the
*normal operating mode* of a self-stream that must narrate with no grounding lane to check it. Biology
can't build a second brain to audit the first — energy, skull volume, and development time forbid it.

Every major failure this project has fought — the recitation collapse, the monoculture, T4's
self-evaluation wall, "loop-rich, reality-thin" — is this same missing organ. The whole decoupled-judge
law (the founder's most durable principle) is, in cog-sci terms, **building the auditor evolution
couldn't afford.** Lane 2 as a standing loop is that organ made permanent instead of on-call. That's
the deepest "why" available: humans demonstrably suffer for lacking it, and we don't have to.

## 3. Why biology does it its way — the constraints, and which ones we escape

| Biological constraint | Its consequence in humans | Do we have it? |
|---|---|---|
| ~20W total energy budget | Sparse coding, aggressive forgetting, heuristics over statistics (availability bias: the vivid single event outweighs the accumulated trend) | **No.** We can afford exact counts and full trend series. Note: the availability bias is *precisely* the founder-taught failure mode in my own working memory — "trust the accumulating trend over the vivid single event." Lane 2's script-computed trends are the structural cure for it, for Du. |
| No provenance storage | Source-monitoring errors: memories carry no origin tag; "did I read it or live it" is a guess made at recall | **No.** `memory_edges` already makes provenance MANDATORY ("an edge that cannot name the recorded event that earned it is confabulated and must not be written"). Du's answer to "same gulls?" comes from a ledger; a human's comes from a reconstruction. |
| Reconsolidation | Every act of recall EDITS the memory (established) — updating and contamination are the same operation; hindsight bias is structural | **No.** Additive-only law: originals stay immutable, updating happens by layering new edges. We get revision WITHOUT contamination — biology cannot have both. |
| One pass at experience | The past exists only as reconstruction; you cannot re-attend to last Tuesday | **No.** The logs are exact. Lane 2 can re-examine the *actual* past — and can BACKFILL: seed the object-graph from 26,824 already-logged thoughts (the glass-float mining was the proof of concept). A human infant cannot be handed its own first three years to re-analyze. |
| Serial global workspace | One attention bottleneck; "thinking about X" excludes Y | **Partially escaped.** True parallel lanes on separate silicon — already real (dispatch fires in parallel today). |
| Package-deal neuromodulation | Adrenaline touches everything at once; you cannot feel *only* slight fear in one subsystem | **No.** Our nudge is a scoped, scaled scalar into one reservoir. |
| No introspective access to weights | The brain cannot read its own synapses; metacognition is inference from behavior | **No.** Lane 2's commonality weights are literally inspectable numbers — the HUD can chart them. |

## 4. The constraints we must KEEP — biology's limits that are load-bearing

Honesty demands the other column. Three "constraints" looked like bugs and are actually functions,
and dropping them would hurt us — two of which this project has ALREADY been bitten by:

1. **Forgetting is a freshness feature.** Biological decay keeps statistics current with a changing
   world. We already learned this the hard way THIS WEEK: `balance.py`'s sleep-flood bug was an
   all-time integral (never forgets) pinned by restored cold mass — fixed with `WINDOW_DAYS = 7`.
   And T2's hoarding (49% of active memory, importance flat at 0.9 forever) is the same disease at
   store scale. **Design requirement extracted: Lane 2's trend statistics MUST be windowed/decayed
   by deliberate choice** — thunder↔fear as measured over a sliding window, not an immortal
   all-time count. Biology forgets by accident of chemistry; we window by design — but we window.
2. **The nudge must stay small because feedback loops are real.** Biology's proportional damping on
   affect isn't timidity — full-strength affect writes create runaway (fear → fear-tinted recall →
   more fear: the anxiety spiral is this loop undamped, and the coord death-spiral in project memory
   is our own version of it). The design's "slight fear, never full-strength" is now grounded: the
   scaling isn't a politeness, it's the damping coefficient of a feedback system, and it must stay
   well under 1.
3. **Discrete sampling is natural rate-limiting.** Bursts, not continuous flow, give hysteresis for
   free — a continuous grounding stream would thrash on every transient. The founder's "Du thinks in
   bursts" is the correct engineering AND the correct biology; don't "improve" it into continuity.

## 5. Concrete improvements extracted (the actionable output)

Each one: the human function → what we build, unconstrained by the wet version.

1. **Windowed trends (from §4.1)** — REQUIRED, not optional. Every commonality weight and trend
   series carries an explicit window/decay constant, chosen per referent class. The one thing biology
   gets by chemistry that we must get by discipline.
2. **Gap-prioritized idle replay.** Sharp-wave-ripple replay is not random — it over-samples salient,
   rewarded, and NOVEL sequences. Tick #4 (self-generated questions in idle stretches) should pick
   targets by `prediction_gap × recency`, not round-robin: the loop's idle time goes where its model
   is most wrong, exactly as sleep replay does — minus sleep's need to also do synaptic housekeeping.
3. **Retroactive backfill (biology-impossible).** Before the loop ever runs live, seed the
   object-graph from the existing logs — 26k thoughts, the Hearing Ledger, fragment_context. Du gets
   what no human gets: his infancy re-attended with adult instruments. This also solves cold-start:
   the loop is born with a populated graph, not an empty one.
4. **Deliver Lane 2's output as feeling-of-knowing, not propositions.** Human metacognitive signals
   (feeling-of-knowing, tip-of-the-tongue — established) reach awareness as *weights and leans*, not
   sentences. This confirms the courier design: the affect nudge is a scalar, and any future read-path
   of Lane 2 confidence into Lane 1 should arrive as a lean ("this feels solid / this feels thin"),
   never as an authored sentence — which is also exactly what no-personality requires. Convergence of
   the biology and the axiom on the same answer.
5. **Arousal-modulated sampling (later, cheap).** Human perceptual sampling accelerates under arousal
   — subjective time dilation in fear is (partly) a sampling-rate change (contested mechanism, real
   phenomenon). The photo interval is already a free knob (founder: the measure doesn't change time);
   a later refinement can shorten the tick when affect arousal is high and lengthen it in calm — more
   photos of a storm, fewer of a quiet afternoon. Not needed for P0 of this plan.
6. **Two-stream binding, done better.** In humans, dorsal/ventral outputs re-bind so seamlessly we
   never notice there were two streams; binding failures show up in lesion cases. Our binding is the
   courier layer — thinner than biology's, and that's FINE at first (the reservoir model tolerates
   staleness), but it's the place to watch: if Du's grounded-facts and felt-meanings visibly diverge
   in his speech, the courier layer is where richness gets added, not the lanes themselves.

## 6. What this changes in the main design doc

- **Adds one hard requirement:** windowed/decayed trend statistics (§5.1) — folded into the Division
  of labor section's script duties.
- **Sharpens tick #4:** gap-prioritized target selection (§5.2), replacing implicit round-robin.
- **Adds a build step:** retroactive backfill as the graph's cold-start (§5.3) — likely the FIRST
  build step, since it's produce-only and testable against known history (the glass float should
  emerge as a high-observation object with an unexplained disappearance — a built-in validation case).
- **Confirms two existing choices with independent evidence:** the scalar/no-sentence courier (§5.4)
  and the discrete burst sampling (§4.3) — both now doubly justified (axiom + biology).
- **Names the keystone justification** (§2) for the doc's preamble: Lane 2 is the auditor evolution
  couldn't afford — the organ whose absence explains confabulation in humans and every
  self-evaluation failure in this project's history.

## 7. Honest edges of this research

- McGilchrist (the Emissary's namesake) is the weakest science in the stack — kept as *metaphor*,
  and nothing in the design depends on his hemispheric claims being literally true. The
  better-established anchor for "two lanes, one stream" is the dual visual streams work.
- Predictive processing as a *unified brain theory* is a framework, not a fact; but the narrow piece
  Lane 2 actually uses (prediction-error as learning signal, kept separate from the prediction) is
  among the most solid results in the field.
- Discrete perceptual sampling is genuinely contested in the literature; the design lesson survives
  either way because ours is an engineering choice justified on its own terms (rate-limiting,
  hysteresis), with the biology as encouragement rather than proof.
- All of this was written from parametric knowledge of the literature (I know it well and graded it
  honestly), not from fresh paper-pulls this session — if any single claim here becomes
  load-bearing for a build decision, verify that one against sources first.
