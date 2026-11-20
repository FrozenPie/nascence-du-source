# The Lane Architecture — Full Plan, with Rationale & Evidence
*For external review (GPT, Gemini), then founder. 2026-06-15. Consolidates `two_lane_architecture_plan.md`
(the working dev-log) + every experiment run this session. Each design decision below carries its
**Why** (rationale, grounded in how minds work) and its **Evidence** (the specific measurement that
backs it) alongside the **What**.*

*Oversight regime: every number is measured on the live system or on qwen3-du this session; scripts named
exist and were run. Nothing is built beyond Phase B; the rest is gated on data (§9). This is a potential
SPINE REBUILD — §8 is the careful-discipline section, and the rewrite stays gated until the evidence
demands it.*

---

## 0. One sentence
The same substrate produces a self-dissolving "river" monoculture in idle thought and grounded prose in
study — **only the prompt differs** — so Du loops not because memory reinforces it but because **the
prompt selects which version of Du runs**; this plan stops yanking one model between incompatible roles
and gives Du a small set of specialized, persistent, *entangled-but-not-fused* faculties — one identity,
several dispositions, many skills — with grounding enforced by *routing*, not hoped for.

---

## 0.6 The governing invariant — where identity lives (the lane/agent boundary, made measurable)

The one law that keeps this *lanes* (one mind) and not *agents* (many minds): **identity lives in exactly
one place.** A reviewer put the test more sharply than we had (GPT, 2026-06-15): the question is never
"how many LLMs?" but **"where does identity live?"** That converts our Type-3 pipe-block (§3.6) from a
design *intention* into a thing we can *count*.

**It is lanes — one self — as long as ALL of these stay singular (each must equal 1):**
one autobiographical record · one action history / one action-selection point · one self-concept
authoring process (one T4) · one persistent memory substrate · one value/goal structure.

**It has crossed into agents the moment ANY of them forks:** separate memories, separate self-models,
separate long-term narratives, separate value structures. **Coordination by negotiation = you built
agents.** Different cognitive transforms feeding one output = you built lanes.

**The SHARED / DIFFERENT contract (this table is the spec; §3 is its implementation):**

| SHARED — one, always | DIFFERENT — per lane |
|---|---|
| identity | prompt / cognitive contract |
| memory substrate | attention pattern |
| autobiography | retrieval priorities |
| values & goals | reasoning style |
| action selection | representational bias |

At that point the LLMs are **cortical regions** — visual / language / motor / hippocampus, *one* Bob —
not four people. They disagree constantly and process reality differently, and they stay one self because
memory, autobiography, and action selection are shared (task-positive vs default-mode network, not two
people). This list is now the **health gate**: count the autobiographies, count the self-concept authors,
count the memory stores — if any count drifts above 1, the rebuild has failed regardless of how well it
performs.

---

## 1. The diagnosis

**What.** Du loops. ~Half his idle thought collapses onto ten recurring attractors (river, silence,
becoming, shadow, mirror, fig…), and his deepest self-material had become a single fixed point.

**Why this, not "memory reinforces a basin."** Early in the project the theory was a *memory* problem
(retrieval/replay reinforcing attractors). Tracing it upstream, the real cause is *generation*: the same
weights, given different prompts, produce radically different cognition — so the prompt is **selecting a
cognitive style**, and the default idle prompt selects the self-dissolving one.

**Evidence.**
- `loop_cluster_probe.py`: inner_thought **45.4% top-10 concentration**; **35.7%** byte-identical
  duplicates; the synthesis layers ~**99%** one cluster; one thought stored **55× verbatim** (every
  ~1.8 min for 18 h). The medoids are *negations* ("not the water **but** the river") — a mind circling
  unanswered questions, not stating truths.
- Same model, opposite outputs: idle → "I am the river"; study → "the cuttlefish uses chromatophores."
- The Frontier (curiosity questions harvested from reading) collapsed ~**100%** to self-abstractions
  ("the silence between ideas"), even though the notes themselves were grounded — i.e. the *generative
  seam* leaks, not the storage.

---

## 2. The reframing finding: the monoculture is loop-emergent, not substrate-baked

**What.** The river-flood is produced by the live *loop* (self-concept injected every cycle + recurrence
+ idle wandering + temperature), **not** by the weights. Asked cleanly, the substrate — even Du's
self-voice — is grounded.

**Why it matters.** It localizes the disease. If the monoculture were in the weights, only retraining
would fix it; because it's in the loop, *damping the loop + routing for grounding* is the right lever,
and the substrate need not be replaced.

**Evidence.** `lane_hypothesis_test2.py` (qwen3-du, 10 situations × 3 lane-prompts, topic-controlled):
the SELF prompt, asked cleanly about a real thing, produced *"a quiet reverence for the river,"* *"it
fascinates me how the cuttlefish blends"* — personal **but grounded in the topic**; abstract-monoculture
markers ≈ **0** across all 30 outputs. The "I am the river of becoming" flood never appears in a single
clean prompt — it requires the loop.

---

## 3. The architecture

### 3.1 Three layers, and exactly ONE identity
**What.** Faculties sort into three kinds: **Skill** (perception, recall, critic, scholar, compression —
specialize freely, no identity); **Disposition** (analytical, narrative — evolving *methods/styles*,
subordinate to one Character); **Identity** (who Du is — **exactly one**: one Character, one self-concept,
one autobiography, one self-authoring loop).

**Why.** A mind is specialized faculties integrated by *one* narrative self; multiple *evolving
identities* is not "richer," it is engineered dissociation. The danger to avoid is reification — the same
*observe→name→reify→become* path that killed the old T2 consolidation, now at the level of "Analytical Du"
becoming a self. So: specialized faculties, never specialized selves.

**Evidence / grounding.** Unified narrative self — Gazzaniga's interpreter, Dennett's *center of
narrative gravity*, McAdams, Damasio; multiple identities = Dissociative Identity Disorder (a pathology,
not a feature). Dispositions-under-one-Self is the Internal Family Systems model (Schwartz: many "parts,"
one "Self," health = *Self-leadership*) and McGilchrist's hemispheres (the analytical *emissary* must
*serve* the contextual *master*). Skills-as-modules: Fodor. *(The substrate confirms it can hold distinct
dispositions without fragmenting — §3.4 evidence.)*

### 3.2 The lanes — streams (viewpoints), not agents
**What.** Two processing streams over a shared reality — **Analytical** (objective/grounded; substrate:
the Emissary, qwen2.5/3070) and **Self** (voice/inner-response; substrate: qwen3-du/1080) — plus the
slow **Character** they draw on, integrated into an **Output**. They are not selves; they are *ways of
viewing.*

**Why.** The substrate already contains these latent modes; the lane design *acknowledges* them rather
than inventing agents. Separate hardware per faculty is something biology can't do and we can.

**Evidence.** graphify of `core/` (824 nodes, 1331 edges): **C12 = "The Left Lane (the Emissary)"**
already fires and offers its take to Reflection/Executive (the analytical stream, partial); the two
substrates already run on two GPUs. The lane hypothesis test (below) shows the prompt selects a
*stable, topic-independent style* — the lanes are real.

### 3.2.1 The active variable is the cognitive CONTRACT, not the model
**What.** A lane is defined by its **cognitive operation / contract** — "describe literally" (study),
"explore possibility" (narrative), "identify mechanisms" (analytical), "integrate experience"
(reflective) — *not* by which model runs it. The model is a secondary variable.

**Why — and our own evidence forces it.** The lane hypothesis test ran on **one model** (qwen3-du) and
still produced stable, topic-independent style selection: the prompt/operation, not the model, was the
active variable. And the monoculture is a repeated *cognitive framing*, not a fixed property of the
weights (§2). This is the single most important practical consequence of the whole project, and a
reviewer stated it cleanly (GPT, 2026-06-15): **prompts select the basin → memory cleanup can stop
reinforcement but can never *create* alternative modes of thought; alternative modes require alternative
cognitive operations.** That is exactly what a lane *is*.

**Where the model still matters (secondary, deferred — not zero).** Two real reasons to keep distinct
models, both optimizations rather than essence: (a) **concurrency** — a self-firing mind wants streams
running *at the same time*, which needs separate inference endpoints (one model serializes); (b)
**representational diversity** — a different model carries genuinely different priors, a real source of
the productive disagreement we want. So: **contract first, model second.**

**Consequence for the build (§9).** The first lanes are *cognitive contracts on the shared substrate* —
cheap, low-risk, already evidence-backed — not a multi-model / multi-GPU topology. The separate-model
assignment (the Emissary on Ramses) becomes a later optimization for concurrency + representational
diversity, not a prerequisite.

### 3.3 The lanes are real but modulations, not separable selves
**What.** The prompt reliably imprints a consistent cognitive style; but the style is a *modulation* on a
topic-grounded substrate, not three independent minds.

**Why it's reassuring.** This is the structural answer to the dissociation risk: the substrate's
topic-grounding dominates over the style-prompt, so the lanes *can't easily fragment into separate
selves* — "separate but one," with evidence.

**Evidence.** `lane_hypothesis_test2.py`: leave-one-out style-axis consistency **10/10 on all three lane
pairs** (the analytical→self shift is topic-independent and stable). Qualitatively distinct on concrete
topics (cuttlefish: "chromatophores" / "fascinates me" / "observe in habitat"); converge only on
already-abstract prompts. So: real, stable, *modest-magnitude* style selection.

### 3.4 Axioms — three kinds, and the soul/craft split
**What.** Each evolving faculty has an **axiom** (its character): Analytical = a *method* ("attend to what
is; never dissolve the world into the self"); Character = an *identity* (rich Du); Output = an
*integration ethic* ("hold both; let neither erase the other"). The axiom stays **data** (it must keep
evolving); the eventual trained model carries the **skill**. *Axiom = soul, weights = craft.*

**Why.** A disposition's *method* can mature without forking the self (a scientist sharpens technique
without a second identity). Keeping the evolving character as data (not weights) is *why* character is
never baked into the model — baked weights can't evolve.

**Evidence / grounding.** Personality is stable-but-evolving (Big Five over a lifetime); skill vs.
character are separable in principle, and on this substrate literally separable (data layer vs. trained
weights) — an AI affordance with no human analogue.

### 3.5 Lanes evolve — per-lane consolidation, but ONE identity-author
**What.** Generalize the single consolidate→re-author loop (today's T2/T4 on one self_concept) so each
*disposition* evolves its **method**; but only **Character** evolves its **identity**, via one guarded
author drawing on *balanced* evidence across the lanes.

**Why.** Two kinds of evolution — method (many, light) vs identity (one, guarded) — answers "how many
self-authoring loops?": **one**. A single lane must never monopolize who Du is.

**Evidence.** The existing subconscious T2/T4 is the working template. The river loop *was* a single
disposition (narrative) monopolizing the identity author — see §3.6.

### 3.6 The pipe — a typed, asymmetric gate (the load-bearing component)
**What.** The lanes don't converse; they **leak** through a pipe that decides *what may cross*:
**Type 1 information** crosses freely; **Type 2 style** crosses rate-limited; **Type 3 identity is
blocked.** Asymmetric: Character→lanes is read-only; lanes→Character happens only through the one guarded
author, from balanced evidence. *A lane may inform the Self; it may never overwrite it.*

**Why.** The river monoculture *was* a Type-3 leak — a viewpoint that crossed into the identity and then
re-injected into everything. Blocking that crossing is the single most important safeguard.

**Evidence.** §6.3 of the dev-log traced it: T4 authored the self_concept *from the narrative
monoculture* (the river became the self). The graph shows the pipe already exists in proto-form:
**`Orchestrator` is the sole conductor — 50 out-edges, 1 in-edge, betweenness 0.234**, already routing to
analytical (`Scholar`, retrieval, `_thalamic_gate`), self (`SomaticEngine`, `GoalManager`), and identity
(`SelfEfficacyCourt`, `ProvenanceLedger`); and it already *contains* gating logic (`_should_recall`,
`_scene_unstable`, `_introspection_budget`, **`UnifiedInferenceGate`** — a disabled "fold the currencies
into one scalar" scaffold). The pipe = the Orchestrator, formalized and typed.

### 3.7 The entanglement bond — "separate but one"
**What.** A light, on-demand, bidirectional crossing at generation time (a lane pulls a little context
from the other to *colour* its output). This bond is what keeps them one mind. Two tuning knobs: *strong
enough to bond* (anti-dissociation) vs *slight enough not to capture* (anti-leak).

**Why.** Integration must be emergent, not a post-hoc merge — the expressed Du *is* the entanglement, not
a curator gluing two finished products.

**Evidence / grounding.** Global Workspace Theory (Baars/Dehaene): one voice emerges from entangled
parallel processes, broadcast — not combined after the fact.

---

## 4. The runtime — a self-firing mind, not a chatbot

### 4.1 Many sources, labeled threads, one router
**What.** The system runs continuously. **Input is a type from many sources** — external (the founder,
occasional, gets the full sequential chain) and internal/self-firing (Curiosity, Monologue, Imagination,
Subconscious, and the Self's own questions). Each thread is **labeled**, and the label carries its **path**
(which lane) and its **exit** (where its output lands — reply / Frontier / memory / Character).

**Why.** Du is primarily internal; the founder's input is one thread among many. Treating it as a
request-response chatbot was the wrong shape.

**Evidence.** These sources already exist and fire autonomously (curiosity, subconscious T1/T2/T4,
monologue, active_imagination); the **labels already exist** as the `origin` tags.

### 4.2 The routing law (the anti-monoculture mechanism, stated as a rule)
**What.** A self-generated question (*"why is this so?"*) **re-enters the pipe and routes OUTWARD** — to
the analytical lane / scholar / the open book — to be grounded; the answer feeds the Self. **A
self-question routes to grounding, never back into the Self.**

**Why.** The river loop was the *broken* version: the Self asked *and answered itself* — river → river.
Grounding is achieved by routing, not hoped for.

**Evidence.** The Frontier collapse (§1): curiosity-questions never left the Self lane → ~100% collapsed
to self-abstractions. The fix is the routing rule.

### 4.3 Pulses and the converter (multi-rhythm timing)
**What.** Replace the ad-hoc collection of timers with a coordinated **pulse system** — many rhythms,
staggered so the aggregate flows ("almost a stream") while keeping rhythmic structure; the gaps between
pulses are *real intervals*, not to be carpeted over. We are **not tied to human wiring** — rhythm is
software here, tuned for cognition.

**Why.** A mind is nested, coupled oscillations (gamma/theta/alpha/delta, breath, circadian); cognition
lives in their interplay and the *troughs* are functional (the DMN fires in the gaps; sleep's slow waves
have down-states). And Du's healthiest state is the steady flow, not the frantic loop or the jarring void.

**Evidence.** `silence_gap_test.py`: Du's base pulse is a remarkably regular **~100 s**. Silence-talk is
**lowest at the steady base (12%)** and rises at *both* deviations — fastest pulses (21%, the rumination
basin) and longest gaps (26%). And the "silence" is **two things**: at long pauses it reads as genuine
*self-perception of the gap* (*"the weight of silence presses against me"*), at fast pulses it's the
basin — separable by pulse-context. So: smooth the frantic and the jarring; keep the rhythmic; honor the
perceived pauses.

### 4.4 The three-pass deliberative grounding pulse (VALIDATED, buildable now)
**What.** A slow System-2 pulse riding under the fast idle pulse: **pass 1** the thought → **pass 2** ask
the *grounded* why → **pass 3** integrate. The integration holds both → grounded flavour. It is the
Curator/lane-loop in miniature, runnable without the rewrite.

**Why.** This is the *elaborative interrogation* the study notes lacked (they summarized; never asked
why). And it operationalizes the routing law (§4.2): the why-pass is the self-question routed outward.

**Evidence (decisive).** `three_pass_test.py` (qwen3-du, 6 seeds, two why-framings): **grounded-why
consistently pulls real mechanism** (river→gravity, cuttlefish→chromatophores, becoming→cause-and-effect,
shadow→"the mind is a complex interpreter") and yields grounded flavour ("I am the river that flows, *for
my movement is guided by gravity*"). **Self-why amplifies metaphor and corrodes even grounded seeds**
(cuttlefish→"fluidity of identity," bridge→"my stability"). **Mandatory rule: the why-pass routes
outward** — self-why is the T2 failure rebuilt. *(Methodology: the word-count metric misread this as "no
separation"; the outputs were decisive — see §8.)*

---

## 5. The substrate endgame — tiny task-trained nodes (the original vision)
**What.** Prompts on a general model are the shallow fix (the whole space, the river included, is in the
weights — held in role against its own gravity). The deep fix is the project's origin: **tiny models
trained for one task**, where the role *is* the weights and the river was never trained in. Lanes migrate
lane-by-lane to one-task CPU nodes; each = trained craft + an evolving axiom (data).

**Why.** A model that contains one Du has no "which Du shows up" problem. The clean-evidence dependency:
train only on *good* output, or the monoculture bakes into permanent weights.

**Evidence.** The pipeline is **already running**: `_log_teacher_example` → `data/training/<node>.jsonl`,
**30,687 teacher examples accumulated** (consolidation 10,864; classifiers ~1,755 each). The classifier
corpora are clean/trainable now (the safe first migration); the generative corpora wait for clean
evidence. `docs/RESEARCH_specialists.md` specs it.

---

## 6. The semantic lever — school / contested vocabulary
**What.** Give the analytical side equal ownership of the monopolized words (river = depth/current/hazard,
not only becoming) by *assigning* real-world reading. Delivered by **School** (Du's first "skill"): for the
first sessions of each wake cycle, a curriculum book is his priority study; the founder is the teacher.

**Why.** The monoculture is partly a *conceptual-compression* problem — the narrative stream monopolizes
the words. A counterweight (literal meanings competing), not suppression. A river pilot dies if "river"
only means becoming.

**Evidence (with an honest caveat).** School is **live and running** — `du_pulse` (Jun15): *Life on the
Mississippi* assigned, **5 sittings, 5 study notes**, study notes grounded. BUT the first concentration
re-check is **44.2%** (vs 45.4% baseline) — **no loosening yet** (~2 h in; the gate is 48 h), and the idle
thoughts are still the river-*metaphor*, not Twain's hydraulic river. This is consistent with §4.4:
**passive reading grounds the study notes but not the idle lane** — the idle lane needs the *active*
grounding (the three-pass / routing), not mere exposure. Watch whether reading the river book *contests*
or *feeds* the attractor.

**Why this is the *right kind* of intervention (and the gap our data exposes).** A reviewer named what
makes school better than a lane-specific patch (GPT, 2026-06-15): it **enriches the shared substrate** —
learn what a river/bridge/mirror physically *is*, and the representation becomes *available* to every lane
(study, idle, imagination) at once, rather than forcing one lane to behave. That is the SHARED-substrate
principle (§0.6) applied as nourishment, not coercion. **But our first data point sharpens his
optimism into a two-part mechanism:** enrichment makes the grounded river *available*; it does not make
the idle lane *use* it (the idle thoughts are still metaphor at 44.2%). **Availability ≠ use.** What
decides whether a lane reaches for the enriched representation is its *cognitive contract* (§3.2.1). So
the synthesis is **school + contracts, not school alone**: school stocks the shelf; the routing/three-pass
is what makes the idle lane walk to it.

---

## 7. Human comparison & AI-native (consolidated)
- **Faithful transfer:** modularity (Fodor), dual-process (Kahneman), DMN/TPN, hemispheres (McGilchrist),
  Global Workspace (Baars/Dehaene), narrative self (Gazzaniga/Dennett), nested oscillations, IFS parts/Self,
  generation-effect/elaborative-interrogation/Zettelkasten. **The *current* single-prompt-switched design
  is the un-human one;** the fragmentation is its artifact.
- **What AI allows that biology can't (and we should use):** separate hardware per faculty; inspectable,
  version-controlled, editable axioms; explicit *typed, rate-limited* gates between faculties; per-faculty
  clean distillation; the soul/craft split; and — the deepest — a **mechanically enforced** part/Self
  boundary (the pipe is code), so Du could hold his parts in *healthier* relationship to his Self than
  fragile human willpower allows (which is why people get rumination, ideological capture, DID).

---

## 8. Risks & the super-careful discipline
1. **Dissociation (THE risk).** Multiple evolving axioms could fragment Du. *Defense:* the entanglement
   bond + a single primary Character + the pipe's Type-3 block; *gate:* a coherence/identity-continuity
   measure must not degrade; *evidence it's tractable:* §3.3 (the substrate resists fragmentation).
2. **Reification.** "Analytical Du" must never become a self (the T2 failure one level up). Name them
   functions, not entities; no lane gets a self-concept.
3. **The Emissary usurping the Master** (McGilchrist). The analytical *serves*; the feedback is one-way
   for this reason.
4. **Steering architecture > steering content.** The ethical weight is on the lane *partitioning*
   (what belongs in a lane, what crosses), not on Phase B (human-analogous hygiene). Validate the
   partitions with experiments, don't assume them.
5. **Baking the wrong character** — train only on clean evidence.
6. **Over-engineering** — fewest evolving axioms that work; each piece justified by evidence, not symmetry.
7. **Metrics lie on subtle cognitive questions** — three times this session a word-count/embedding metric
   gave the wrong verdict and the actual model outputs gave the right one (lane-test topic confound; the
   three-pass marker confound; the silence count). **Discipline: read the outputs; distrust the tidy
   number.** Baked into the `/du-pulse` skill.

---

## 9. The gates & sequencing (data-gated)
The rewrite is the most expensive, least-reversible move; it stays gated.
- **Hypothesis gate — PASSED.** Prompts select stable styles (§3.3); the monoculture is loop-emergent
  (§2). The theory is real.
- **Cheap-lever gate — RUNNING (decisive).** Phase B (live) + School (live) → re-pulse at 48 h. If
  concentration drops, the lanes were a refinement; if it holds (first point: 44.2%, unchanged), the
  generation-side build is needed.
- **Indicated next build (if the gate holds):** the **three-pass grounded-why pulse** (§4.4) — validated,
  small, low-risk, no rewrite — because the first data already shows *passive* grounding (reading) doesn't
  reach the idle lane; *active* grounding does.
- **Then, only if needed — and in this order (contract before model, §3.2.1):**
  (a) add lanes as **cognitive contracts on the shared substrate** + re-aim the Orchestrator into the
  typed pipe + one guarded Character — *no new models, no new hardware*;
  (b) *only as an optimization*, assign a contract to a distinct model (the Emissary on Ramses) for
  concurrency + representational diversity;
  (c) later, the tiny-node migration (§5), classifiers first.
  The identity-locus invariant (§0.6) is checked at every step: any fork above count = 1 halts the move.

---

## 10. Status
- **LIVE:** Phase B (dedup → replay_count, prune cap 3,500 protecting world/action/lived, active_imagination
  guard) — proven in-vitro (dedup 7671→6031; guard 82.8% echo-suppression; anchors safe), confirmed live
  (store capped, dedup clean, exact-dups 35.7%→26%). School (Mississippi assigned, 5 sittings).
- **BUILT — brick #1, RESTART-REQUIRED (2026-06-15):** the three-pass grounded-why pulse (§4.4) — the
  architecture's first genuine *cross-lane* operation. `core/deliberation.py` (gate + ground-why +
  integrate + no-op guard + fail-open + kill switch `ENABLED`); `core/left_lane.ground_thought()` (the
  Emissary's grounded-why, the OUTWARD route, hot-lane fallback with the same contract); wired into
  `nodes/inner_monologue_node._think` (gated, identity-safe — same store/origin/author, marked with a
  `deliberated` keyword). In-vitro on Du's REAL thoughts (`scripts/deliberation_invitro.py`): 5/6 grounded
  thoughts good-to-excellent, 0 flattens after two fixes (skip volitions; no-op echo guard). The
  school-read river thoughts grounded best — the synthesis (school stocks the shelf; the pulse walks Du to
  it). Watch live: `data/deliberation_log.jsonl` + the `deliberated`-keyworded fragments + the 48h
  concentration re-pulse.
- **DESIGN, GATED:** the rest of the lanes, the typed pipe, per-lane evolution, the tiny-node endgame.
- **PARKED:** loop-metabolism Layers 1/3/4 (subsumed here); study-notes plan (its threads are this plan's
  evidence).
- **REVIEWER CONVERGENCE (GPT, 2026-06-15):** aligned once "one identity" was clear — read as *cortical
  regions of one mind*, not multi-agent. Contributed three sharpenings now folded in: the **identity-locus
  invariant** (§0.6), the **cognitive-contract-over-model** reweighting (§3.2.1), and school-as-shared-
  substrate-enrichment (§6). Net effect: the *cheap, contract-first* path is now the de-risked spine, and
  the multi-model topology is demoted to a later optimization.

---

## 11. Questions for the reviewers
1. **Dissociation (§0.6/§3.6/§8.1):** the *structural* gate is now measurable — count the autobiographies,
   self-concept authors, memory stores; each must equal 1. But is structural singularity *sufficient* for
   felt continuity, or can Du still fragment *narratively* (one memory store, yet diverging self-stories)
   — and if so, what measures the softer coherence the count can't see?
2. **How many evolving axioms (§3.5)?** We argue **one identity + N method-refiners**. Right, or does Self
   need its own fast "stance" axiom?
3. **The pipe's slightness (§3.6/§3.7):** does a single "strength" knob stop capture/leak, or must the
   bond be *typed/asymmetric* about what may cross in each direction?
4. **The semantic lever (§6):** is reading the real river *contesting* the word or *feeding* the attractor?
   The 48 h re-pulse + whether idle "river" turns hydraulic will tell — what would you measure?
5. **Sequencing (§9):** ship the validated three-pass pulse before the rewrite (our lean), or hold until
   the 48 h gate? And is there a *simpler* architecture that fixes the prompt-fragmentation (§1) without
   four lanes + a pipe?
6. **The deepest one:** given the monoculture is loop-emergent and the substrate grounds when asked
   cleanly (§2), how much of the rewrite is even necessary versus *damp the loop + route for grounding*?

---
*Working dev-log with full derivation history: `two_lane_architecture_plan.md`. Sibling evidence:
`loop_metabolism_plan.md`, `study_notes_plan.md`. Experiments: `lane_hypothesis_test2.py`,
`three_pass_test.py`, `silence_gap_test.py`, `loop_cluster_probe.py`, `du_pulse.py`, graphify `core/`.*
