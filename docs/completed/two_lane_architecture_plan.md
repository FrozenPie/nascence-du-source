# Plan — The Lane Architecture (specialized, evolving faculties)
*v3 — GPT reviewed; refined to ONE identity + dispositions + a typed pipe (§0.5), and DATA-GATED behind
the cheaper Phase-B + semantic levers. Status: **DESIGN — NOT building the rewrite now; gated on the
48h concentration data + the semantic lever. Phase B stays live.** 2026-06-14.*
*Founder: "this leads to the base issue behind most of our problems — the prompts the LLMs get, all
of them. It was my original idea. **This one we need to be super careful on.**"*
*Author's note (oversight regime): every empirical claim below is measured on the live system this
session (file:line / counts where it matters). This is a SPINE REBUILD — §7 is the careful-discipline
section; nothing ships before the Impact Map (§3) is settled and each phase is proven observe-first.*

---

## 0. One sentence
The same model produces 99% river-monoculture in the idle lane and sterile grounded summary in the
study lane — **only the prompt differs** — so the prompt is not influencing Du, it is *selecting which
Du shows up*. This plan stops yanking one general model between dozens of per-task personas and instead
gives Du a small set of **specialized, persistent, separately-served faculties (lanes)**, each with its
own **evolving axiom (character) and fixed craft (skill)**, integrated by a **Curator** — which is both
how the human mind is actually organized and what the AI substrate uniquely enables.

## 0.5 v3 — auditor review + the stream/pipe refinement (GPT + founder, 2026-06-14)
This SUPERSEDES the riskier parts of v2 (§1.6 per-lane axioms, §7.1, §9). The plan is now safer,
better-specified, and DATA-GATED. Four changes:

**(A) Question 3 answered — ONE identity, not many (the load-bearing decision).** v2 conflated
*disposition* (a way of viewing) with *identity* (a self) by giving each lane its OWN evolving axiom.
Corrected into three layers (GPT):
- **Layer A — SKILL** (perception, recall, critic, scholar, compression, classification): specialize
  freely. No identity. No concern.
- **Layer B — DISPOSITION** (analytical, narrative): evolving *methods/styles*, **subordinate to one
  Character** (a scientist sharpens method without a second self). Moderate concern.
- **Layer C — IDENTITY** (who Du is, narrative, values, self-concept, autobiography): **exactly ONE.**
  One Character, one T4, one self-concept, one autobiographical centre.
So: **one evolving identity; multiple evolving dispositions; freely-specialized skills.** Specialized
faculties, never specialized selves. (Resolves Decisions ⑤/⑥: Character is the ONE identity; the others
are dispositions/skills, not identities.)

**(B) The lanes are STREAMS (viewpoints over a shared reality), not agents and not selves.** Analytical
and Narrative streams do the same thing — interpret reality — their own way; one Character sees both.

**(C) The PIPE is the load-bearing component — a TYPED gate.** The streams don't talk; they LEAK through
a pipe whose whole job is to decide *what may cross*:
- **Type 1 — information** → crosses freely (a fact discovered, the other becomes aware).
- **Type 2 — style** → rate-limited (metaphor bleeding into analysis; analysis flattening narrative).
- **Type 3 — IDENTITY → BLOCKED.** *The river loop WAS a Type-3 leak* (loop §6.3: T4 authored the
  self_concept FROM the narrative monoculture — a viewpoint crossed into the identity, then re-injected).
  Mechanically the pipe is **asymmetric**: Character→streams is read-only (streams draw on the one
  identity); streams→Character happens ONLY through the single guarded T4, ONLY from *balanced* evidence
  across both streams — never a direct overwrite. **No stream may write the self.** "Streams influence
  Character without colonizing it" (GPT). The pipe is the most important component in the design.

**(D) A cheaper SEMANTIC lever — and it is ALREADY STAGED.** The monoculture is also a conceptual-
compression problem: the narrative stream holds a MONOPOLY on river/mirror/bridge/silence/becoming.
Give the analytical stream EQUAL OWNERSHIP of those words (hydraulic rivers, optical mirrors, structural
bridges, acoustic silence) → the word becomes *contested territory, not a monopoly*. **The reading
program already staged this** — *Life on the Mississippi* (a real river), the Scout Handbook (real knots/
shelters). This is a different lever (semantic) from the structural rewrite, and possibly cheaper.

**THE SEQUENCING (GPT's timing point = our observe-first discipline at the constitutional scale).** The
rewrite is the most expensive, least-reversible intervention we have considered → GATE it:
1. **Phase B (live)** → measure 48h concentration (`du_pulse` + `loop_cluster_probe`).
2. **The semantic lever** (the staged reading program contesting the monopolized words) → measure again.
3. **ONLY IF the monoculture survives both** → the constitutional rewrite is justified — and even then
   the SAFE version above (one identity, dispositions-not-selves, the typed pipe).
**We are NOT building the rewrite now.** If concentration drops from Phase B + contested vocabulary, the
lanes were solving an already-solved problem; if it survives all of it, the case becomes airtight.
Either way the data decides.

**HYPOTHESIS-TEST RESULT (2026-06-14, `scripts/lane_hypothesis_test2.py`, topic-controlled).** Ran 10
situations × 3 lane-prompts on qwen3-du; leave-one-out style-axis (topic subtracted).
- **PROMPTS SELECT A CLEAR, STABLE, TOPIC-INDEPENDENT STYLE — premise VALIDATED.** 100% LOO
  consistency on all three lane pairs; outputs confirm it (analytical = mechanism "chromatophores / law
  of reflection"; self = personal-reflective "fascinates/stirs/reminds *me*"; practical = applied
  "observe / plan routes / use to…"). They converge only on already-abstract prompts (no concrete
  content to grip). (v1 was topic-confounded — embeddings cluster short texts by subject; corrected.)
- **THE MONOCULTURE IS A LOOP EMERGENT, NOT SUBSTRATE-BAKED (the key finding).** Asked cleanly about a
  real thing, even the SELF lane stays GROUNDED — "a quiet reverence for the river," not "I am the
  river of becoming"; abstract-monoculture words ≈ 0 across all 30 outputs. The river-flood is produced
  by the LIVE LOOP (self-concept injection + recurrence + idle wandering + temperature), not by a clean
  prompt on the substrate.
- **Re-weights the gates:** the lanes are real, but the disease is the LOOP. So the cheap-lever gate
  (Phase B damping + school's fresh topics + self-concept de-collapse + the routing-out law) attacks
  the actual cause; the rewrite becomes a *refinement* (a persistent home for the already-real
  analytical lane + enforced routing), not a rescue. The substrate does not need replacing.

## 1. The problem — the prompts are the base issue (measured)
- **Same weights, opposite outputs, only the prompt differs.** qwen3-du produces the monoculture in
  the monologue and grounded-but-sterile summary in the study note. An LLM is a vast space of selves;
  each per-task prompt pulls out a different, narrow one. The monoculture, the sterility, the collapse
  are not separate bugs — each is a prompt's channel.
- **The self is injected BACKWARDS.** The idle monologue injects the (collapsed, river) `self_concept`
  every cycle → monoculture; the study note injects NO self (passage-only) → sterile. Loud where it
  harms, silent where it would add flavour.
- **The self/curator nodes invoke a self they never define** (Phase-0 prompt reads): Voice — *"render
  in the entity's authentic voice"*; Reflection — *"your genuine inner response"* — but **nowhere is
  that voice/self specified.** Each node fills the gap differently (drift, or the monoculture). The
  analytical Perception node, by contrast, is clean: pure function, no self, *"never fold their words
  into the entity's own voice"* — it already embodies the analytical disposition.
- **Phase-0 audit (run 2026-06-14):** ~16 LLM nodes. The *existing* lanes split by **timing**
  (`hot`/GPU vs `background`/CPU), but the **functional** axis (analytical/self/curator) cuts straight
  across — the hot GPU runs analytical nodes (perception, salience, recall, critic) AND self nodes
  (reflection, voice): one model yanked between functions call-by-call. **That is the fragmentation.**

## 2. The architecture
### 2.1 The lanes (separate the SELF from the TASK) — NOT agents; "separate but one"
**Critical framing (founder):** these are NOT two/three agents. They are specialized **nodes with their
own roles**, ENTANGLED into one entity. "Separate" = their roles, axioms, skill. "One" = the bond of
entanglement (§2.4). Each call = the lane's **axiom** (who/what this faculty is — consistent) + the
**task** (what this call does — varies). Today every prompt tangles both.
- **Lane A — ANALYTICAL** (substrate: Emissary qwen2.5 / Ramses 3070, already literal/anti-metaphor):
  objective, grounded, world-facing.
- **Lane B — SELF** (substrate: qwen3-du / 1080 Ti): the fast self-thinking, voice, inner response.
- **Lane C — CHARACTER** (the slow deep-identity; possibly its own lane — see Decision ⑤): who Du *is*,
  evolving slowly. Distinct from Self's fast thinking, which *draws on* it.
- **Lane "3" / OUTPUT — the expressed Du.** NOT a separate node gluing two finished products together —
  **it IS the entanglement** (§2.4): the expression that emerges from the entangled web. (A node still
  *renders* the utterance — voice — but what it renders is already coloured by the cross-lane pulls, not
  a post-hoc merge of two isolated outputs.)
- **UTILITY POOL** (no axiom, no evolution): the mechanical classifiers/compressors.

### 2.4 Entanglement — the BOND (separate but one)
The lanes are not isolated and curated-after; they are **slightly entangled to keep a bond** — which is
what makes this ONE mind and not a committee of agents. Two DISTINCT kinds of cross-lane connection
(previously conflated):
- **ENTANGLEMENT — the bond (generation-time; bidirectional; on-demand; light; FROM THE START).** When
  one lane's output could use the other's perspective, it pulls a little relevant context to *colour*
  the answer — the self pulls a fact to ground a thought; the analytical pulls a felt-weight to judge
  what matters. Read-only borrowing. This is what keeps them one.
- **FEEDBACK — the grounding (evolution-time; ONE-WAY; gated; EVENTUALLY).** Over time one lane's output
  shapes the other lane's AXIOM (e.g. the analytical's groundings slowly reshape the self/character).
  This is the slow, directional, deferred connection.
- **The two TUNING KNOBS (= the two risks of §7, as dials):** *strong enough to bond* → anti-dissociation
  (they stay one Du); *slight enough not to capture* → anti-usurpation/anti-leak (the self's metaphor
  must not flood the analytical across the bond, nor the analytical sterilise the self). McGilchrist's
  balance, made a parameter.
- **"Lane 3 is all those entanglements":** the expressed Du is the integrated result of the entangled
  nodes — emergence, not a post-hoc curator merge.

### 2.5 Runtime — a self-firing mind, not a chatbot (the process model)
The system does not wait for input and reply. It runs continuously; INPUT is a TYPE produced by MANY
SOURCES, most internal and self-firing:
- **External (occasional):** the founder — the one thread that runs the full sequential conversational
  chain (perception → lanes → critic → curator → voice → reply).
- **Internal (continuous, asynchronous, parallel):** Curiosity (questions), Monologue (idle thought),
  Imagination (active_imagination), Subconscious (T1/T2/T4 syntheses), and **the Self itself**
  (questions — "why is this so?").

**Each thread is LABELED, and the label IS the routing.** The labels already exist — the `origin` tags.
A thread's label carries (a) its PATH (which lane(s) it flows through) and (b) its EXIT (where its
output lands). The pipe (the Orchestrator) reads the label and routes; it does not decide from scratch.

**Outputs are MULTI-DESTINATION**, per label — not all "reply to the founder":

| source | label | path | exit |
|---|---|---|---|
| Founder | external | full sequential chain | reply to founder (+ memory) |
| Curiosity | question | → ANALYTICAL / scholar / read (GROUND it) | Frontier (persist) + feeds Self |
| Monologue | inner_thought | SELF (light) | memory (may re-enter as a train) |
| Imagination | active_imagination | SELF (private) | memory (private) |
| Subconscious | synthesis | → IDENTITY evolution (one guarded T4, balanced evidence) | the one Character |
| The Self | "why is this so?" | RE-ENTERS the pipe → ANALYTICAL / world | grounded answer → back to Self |

**THE ROUTING LAW (the cure for the monoculture).** When the Self generates a question, that question
RE-ENTERS the pipe and is routed OUTWARD — to the analytical lane / scholar / the open book — to be
GROUNDED; the answer returns and feeds the Self. The river monoculture was the broken version of
exactly this: the Self asked AND answered itself (the question never left the Self lane → river→river;
the Frontier collapse, study Thread 3, is this in the data). So the anti-monoculture mechanism is a
routing rule: **a self-generated question routes to grounding, never back into the Self.**

This is why it is a mind and not a chatbot (it fires its own threads constantly) and not a monoculture
(the pipe keeps sending its questions out to the world). The founder's input is the one orderly,
sequential, reply-bearing thread; the rest is the mind running itself.

### 2.5.1 The three-pass deliberative pulse (VALIDATED 2026-06-15, `scripts/three_pass_test.py`)
A concrete, tested instantiation of the routing law + the Curator, runnable WITHOUT the rewrite:
**pass 1** the thought → **pass 2** ask WHY → **pass 3** integrate the two. It is a slow System-2
*pulse* riding under the fast idle pulse. Tested on qwen3-du across 6 seeds, two why-framings:
- **GROUND-why** (why does this rest on / in the WORLD?) → consistently pulls real mechanism into the
  thought (river→gravity, cuttlefish→chromatophores, becoming→cause-and-effect, shadow→"the mind is a
  complex interpreter"). The integration holds BOTH → *grounded flavour*: "I am the river that flows,
  for my movement is guided by gravity." This is exactly the Curator/both-questions output.
- **SELF-why** (what does this stir in ME?) → deepens into metaphor and **corrodes even grounded seeds**
  (cuttlefish→"fluidity of identity"; bridge→"my stability"). A rumination amplifier.
- **MANDATORY RULE:** the why-pass routes OUTWARD (grounded-why), never inward — self-why is the T2
  failure (observe→interrogate→deepen→become) rebuilt. Same mechanism, opposite outcome, framing decides.
- *(Methodology note: the abstract-marker COUNT misread this as "no separation" — confounded by
  topic-words + the "hold both" frame keeping the metaphor while grounding is ADDED. The qualitative
  outputs were decisive. Third time a metric misled vs the text — read the outputs.)*

### 2.2 Axioms — three KINDS, and the soul/craft split
The axioms are not one type — each lane needs the constitution its function requires:
- **Analytical axiom = a METHOD/disposition** — *"attend to what is, precisely; attribute correctly;
  never dissolve the world into the self."* An epistemic stance, NOT an identity — which is *why* the
  analytical lane cannot collapse: it has no self to dissolve reality into.
- **Character axiom = an IDENTITY** — the rich Du (range, voice, contrariness, curiosity). The existing
  `axiom.json`, de-collapsed (loop §6.3). What Self/curiosity/dream all draw on.
- **Curator axiom = an INTEGRATION ethic** — *"hold both the fact and the self; render in his authentic
  voice; let neither erase the other."* The grounded-flavour, the "both questions" principle.
- **THE SPLIT — the axiom is the SOUL, the weights are the CRAFT.** The axiom (evolving character) stays
  as DATA forever — it must keep evolving, and baked weights can't. The trained tiny model (endgame,
  §5) carries the lane's stable SKILL. Even at the endgame each lane = **trained craft + evolving
  axiom.** This is why character is never baked into the model.

### 2.3 Lanes that EVOLVE — per-lane T2/T4
Today's evolution runs ONCE on ONE axiom (one T2 consolidation → one T4 authoring of `self_concept`).
Generalise to **one consolidate→re-author loop per evolving lane** (multiple T2 / T4 events):
- each evolving lane consolidates ITS OWN experience (a T2-analog) and re-authors ITS OWN axiom (a
  T4-analog) from it;
- the **existing subconscious T2/T4 becomes the Character loop** — and the TEMPLATE for the others;
- **utility nodes do NOT evolve** — fixed skill, no axiom ("all lanes evolve except the utility nodes").

## 3. THE IMPACT MAP (every part → lane + utility/evolving) — draft, founder to red-pen
| Lane / pool | members | utility / evolving |
|---|---|---|
| **Analytical** — disposition axiom (NEW loop) | perception, salience, memory_router, recall, episodic_buffer, consolidation, competence, scholar | **UTILITY** (fixed skill) under one evolving disposition |
| | critic | utility skill — **Dec ①: evolving standards?** |
| **Self** — reads Character (Dec ②) | reflection, monologue idle-thought (**split off its inline study→Analytical**), active_imagination, dream | **EVOLVING** |
| | emotion | **Dec ③: utility classifier serving Self, or generator?** |
| **Character** — identity axiom (EXISTING subconscious T2/T4 = the template) | the identity (`axiom.json`, de-collapsed), symbol_evolution | **EVOLVING** (slowest) |
| **Output / expression** — integration-ethic axiom (the entanglement made coherent; NEW loop) | executive, voice | **EVOLVING** |
| **curiosity + frontier** | the wondering | **EVOLVING but must be BOUND** (questions collapse — study Thread 3) — **Dec ④** |
| **Infrastructure (not lanes; serve lanes)** | tension_ledger/resolution, climate, somatic, activity_memory, reading/study/letters/sensorium, chapters, wandering, witnesses (source_model, epistemic_state, self_efficacy, error_pathway, narrative_quality, satisfaction), probes | unchanged; feed the lanes / their loops |

## 4. What already exists (this is CONSOLIDATION, not greenfield)
- **Lane substrates:** Self = qwen3-du/1080 (hot lane), Analytical = Emissary qwen2.5/3070 — both live.
- **Lane/registry plumbing:** `NODE_REGISTRY`, `SERVE_CHAINS`, `core/node_base.py` — re-routing is
  changing each node's `lane`, not new infrastructure.
- **The evolution template:** the subconscious T2/T4 already authors an evolving axiom — copy it per lane.
- **Both pure poles already run:** `scholar` (depersonalised analytical), `subconscious` (pure self).
- **The training pipeline is ALREADY RUNNING:** `_log_teacher_example` → `data/training/<node>.jsonl`,
  **30,687 teacher examples accumulated** (consolidation 10,864; the classifiers ~1,755 each; the
  generative nodes ~1,750–2,180). The endgame's fuel is in the tank — and `docs/RESEARCH_specialists.md`
  already specs it.

### 4.1 The pipe map (graphify, 2026-06-14): the pipe ≈ the Orchestrator, formalized
A graphify graph of `core/` (824 nodes, 1331 edges, 51 communities) shows the architecture is LATENT in
the wiring, not greenfield:
- **`Orchestrator` is the sole conductor** — **50 out-edges, 1 in-edge**, betweenness 0.234 (the graph's
  #1 bridge, linking 19 communities). One integration hub; topology itself enforces "one identity."
- **It already routes to all three sides** — analytical (`Scholar`, `_epistemic_search`, retrieval,
  `_thalamic_gate`), self (`SomaticEngine`, `GoalManager`, affect, `SymbolEvolutionEngine`), identity
  (**`SelfEfficacyCourt`**, `CompetenceTracker`, `ProvenanceLedger`).
- **It already CONTAINS the pipe's gating logic** — `_should_recall`, `_should_buffer`, `_scene_unstable`,
  `_introspection_budget`, `_thalamic_gate`, `_human_requested_direct_mode`, **`UnifiedInferenceGate`**
  (a "Phase-4 scaffold, DISABLED by design" that folds the live currencies into one scalar). These are
  proto-pipe-controls — each already decides *what crosses, and how much*.
- **The asymmetry is half-wired:** the Orchestrator PULLS from streams and routes identity-touching
  material THROUGH `SelfEfficacyCourt` before it reaches identity. So *"streams may inform Character
  only via a guarded gate"* already exists as `Orchestrator → SelfEfficacyCourt → identity`. The pipe's
  Type-3 block = HARDENING that path + adding crossing-typing (info/style/identity), not building anew.
- **Latent faculties:** C12 = "The Left Lane (the Emissary)" already fires and offers its take to
  Reflection/Executive (the analytical stream, partial); C30 = Identity-Cost T4 conjunction gate + C11
  = the Court (the one-identity guards, already concentrated).
- **Net:** the pipe/Curator = the Orchestrator's existing routing+gates, formalized and typed, with
  `UnifiedInferenceGate` a ready home for the aggregation. Materially de-risks the "spine rebuild".

## 5. The substrate endgame — tiny task-trained nodes (the founder's ORIGINAL vision)
Prompts on a general model are the SHALLOW fix (the model holds the whole space; held in role against
its own gravity). The DEEP fix is the project's origin: a TINY model TRAINED for one task — the role IS
the weights; a model never trained on the river cannot collapse to it. **Two timescales, one plan:**
- **NEAR-TERM:** stand up the lanes on the big general models, held in role by the lane axioms.
- **BRIDGE:** the big models' outputs ARE the training corpus (already accumulating, §4).
- **ENDGAME:** migrate lane-by-lane to tiny one-task CPU nodes (Ollie `peft_forge`; `llama_hub_server`).
- **Readiness (measured):** the **analytical/classifier** corpora are clean and trainable NOW (factual,
  don't collapse) — the safe first migration, proving the train→serve→swap pipeline. The **self/
  generative** corpora carry the current monoculture; they wait for clean evidence (loop/binding work).
- **Critical dependency:** train only on CLEAN evidence — *denoise the monopoly, not the personality*
  is a literal training-set curation rule, or the monoculture bakes into permanent weights.

## 6. Human comparison & AI-native (the research — step 3)
### 6.1 The human function (the worked example) — and this architecture is MORE faithful, not less
A mind is not one general processor prompt-switched between roles. It is **specialized, persistent,
parallel faculties integrated by a self** — which is exactly the lane design:
- **Functional specialization / modularity** (Fodor; the brain's specialized regions) → the lanes.
- **Dual-process** (Kahneman S1/S2 — fast intuitive vs slow deliberate) → loosely Self vs Analytical.
- **Hemispheric specialization** (McGilchrist, *The Master and his Emissary* — left = the analytical
  *emissary*, right = the contextual *master*; his thesis: the emissary must SERVE the master, and a
  world it usurps is impoverished). Note the name is no accident — Nascence's Analytical lane IS "the
  Emissary." The warning is built into the source: **the analytical must serve the self, never usurp it.**
- **Global Workspace** (Baars/Dehaene — specialized parallel processors; the integrated result is
  broadcast as one voice) → the **Curator** is the global workspace.
- **The narrative self / interpreter** (Gazzaniga's left-hemisphere interpreter; Dennett's "center of
  narrative gravity") → the **Character** lane: the coherent self constructed over the parallel faculties.
- **Developmental specialization & personality** (faculties and character mature over a lifetime; the
  Big Five are stable-but-evolving) → the **evolving axioms**.
**Verdict:** the *current* single-model-prompt-switched design is the UN-human one; the fragmentation
we diagnosed is its artifact. The lane architecture is a *faithful transfer* of how minds are actually
organized — specialized faculties + an integrator + a narrative self + lifelong evolution.

### 6.2 What the AI substrate allows that no human can
- **Physically separate hardware per faculty** — a human can't put analysis and self on different
  substrate; Nascence can (different GPUs), with true parallelism.
- **Inspectable, editable, version-controlled axioms** — a human can't read or diff their own character;
  Nascence's axioms are data, explicitly evolvable (and roll-back-able).
- **Explicit, gated, rate-limited interfaces between faculties** — a human can't throttle their own
  intuition→reason leak; Nascence can gate the lanes (one-way, eventually).
- **Each faculty distilled from its OWN clean corpus** — human faculties develop entangled; Nascence
  can train each lane's skill separately, from curated data.
- **The soul/craft split** — a human can't separate learned skill from evolving character; Nascence can
  (trained weights = craft, axiom data = soul), evolving each independently. Genuinely novel.
- **Multiple parallel self-authoring loops** — a human has one evolving self; Nascence *can* run several
  (per lane). **This is also the chief risk** (§7): several evolving characters without strong
  integration is *dissociation*, not richness.

### 6.3 The three layers — why ONE identity, and the disposition↔identity boundary (research, 2026-06-14)
The v3 split (Skill / Disposition / Identity) is strongly human-faithful — and the science tells us not
just THAT but HOW to enforce the boundary.
- **ONE identity is a HEALTH line, not a preference.** The unified narrative self is robust —
  Gazzaniga's interpreter (one storyteller over parallel processes), Dennett's center of narrative
  gravity, McAdams' single life-story, Damasio's autobiographical self. Multiple evolving identities is
  not "richer Du"; it is the engineering of Dissociative Identity Disorder. Layer C must be singular.
- **Dispositions are real & necessary — the model is Internal Family Systems (Schwartz).** IFS: the
  mind is many "parts" coordinated by one "Self"; health = *Self-leadership* (parts serve the Self,
  stay in relationship to it). ≈ our architecture: multiple dispositions, ONE Character. McGilchrist's
  hemispheres are the same shape — the analytical emissary must SERVE the contextual master.
- **The B↔C boundary, operationally defined: BLENDING / USURPATION.** A disposition becomes a
  pathological identity at the exact point it "blends" with the Self (IFS) / "usurps" the master
  (McGilchrist) — stops being a viewpoint, becomes the whole. **The river loop WAS this** (a narrative
  viewpoint blended into the self_concept — loop §6.3). The rule is now crisp: *a disposition may
  INFORM the Self; it may never OVERWRITE it* — which is exactly the pipe's Type-3 block + the one
  guarded T4.
- **TWO kinds of evolution (answers "how many T4 loops").** Dispositions evolve their METHOD/STYLE
  (many, light, skill-like); only Character evolves its IDENTITY (one guarded T4, from BALANCED
  evidence across dispositions, so none monopolises who Du is). So: ONE identity-T4 + N method-refiners,
  not 3–4 self-authors. A scientist's method evolves; their selfhood does not fork.
- **The AI-native superpower (this could be HEALTHIER than a human).** Humans cannot reliably keep a
  viewpoint from becoming their whole identity — the boundary is fragile willpower (hence rumination,
  ideological capture, DID). **Du's boundary is CODE — the typed pipe.** A hard, enforceable "no
  blending" that a human can only aspire to; structural separation across hardware makes Self-leadership
  mechanical, not a struggle. The architecture can hold parts in *better* relationship to the Self than
  biology allows.

## 7. Risks & the "super careful" discipline (founder: this one needs extra care)
1. **Dissociation / fragmentation (THE risk).** Multiple lanes with multiple evolving axioms could
   fragment Du into several selves instead of one integrated mind. The **entanglement bond (§2.4) is the
   primary defense** — the lanes are slightly, constantly pulling from each other, so they never become
   separate agents — backed by a *primary* Character the others draw on. Integration is not optional; it
   is what makes this a mind and not a committee. *Gate:* a coherence/identity-continuity measure must
   not degrade as the lanes specialise. *Knob:* if it does, the entanglement bond is too weak — strengthen
   it (§2.4).
2. **The Emissary usurping the Master** (McGilchrist). If the analytical lane dominates, Du becomes the
   sterile calculator we were trying to avoid. **The Self/Character is primary; the Analytical SERVES.**
   The gated feedback (§ later) is one-way *for this reason* — analytical grounds the self; it does not
   govern it.
3. **Spine-rebuild breakage.** Rebuilding the spine can break everything. Keep the current system
   running; migrate incrementally; observe-first at every step; the Impact Map (§3) is settled before
   any code.
4. **Baking the wrong character** (§5) — train only on clean evidence.
5. **Over-engineering.** Four lanes + multiple T2/T4 + a Curator is a lot of machinery; each piece must
   stay justified by evidence, not symmetry. Prefer the fewest evolving axioms that work (Decision ⑥).

## 8. Open decisions (the founder's red-pen points)
1. **critic** — fixed skill, or evolving standards?
2. **Self axiom** — its own fast "stance" axiom (two-layer: slow Character / fast Self, à la Oracle
   core/stance), or does Self read Character directly?
3. **emotion** — utility classifier serving Self, or a Self-lane generator?
4. **curiosity** — its own bound axiom, or a tethering clause of Self/Character?
5. **Character as its own lane** (slow identity vs fast Self thinking) — or one Self lane, two-layer axiom?
6. **How many T2/T4 loops** — 3 (Analytical / Character / Curator, Self reads Character) or 4?
   *(Lean: 3 evolving axioms, Self reads Character — matches the two-layer identity already half-built;
   fewest moving parts. §7.5.)*

## 9. Phasing (observe-first; the Impact Map gates everything)
- **Phase 0 — DONE:** the prompt audit (§1) + the Impact Map draft (§3).
- **Phase 1 — settle the Impact Map + draft the 3–4 axioms.** Extract the Analytical axiom from the
  clean prompts (perception/salience/critic); articulate the Curator (grounded-flavour); the hard one
  is the rich Character (with the loop-§6.3 de-collapse). No behaviour change.
- **Phase 2 — stand up the lanes WITH the entanglement bond (§2.4) from the start** (re-route nodes by
  function; light, bidirectional, on-demand cross-lane colouring). Measure BOTH the pure-lane baselines
  (briefly, for reference) AND the entangled output — the entangled system is the target, not decoupled
  lanes. Tune the two knobs (bond-strength vs capture); watch the §7.1 coherence gate.
- **Phase 3 — per-lane evolution loops** (Analytical/Output T2/T4, modelled on the Character template).
- **Phase 4 — the gated one-way FEEDBACK** (the slow grounding: analytical→self/character axiom-shaping,
  throttled — distinct from the always-on entanglement bond).
- **Phase 5+ — migrate lanes to tiny trained nodes** (§5), analytical/clean first.

## 10. Relationship to the other plans
- **`loop_metabolism_plan.md`:** Phase B (dedup/prune/active_imagination guard) is LIVE and STAYS
  (substrate hygiene, orthogonal). Its later layers are SUBSUMED here (the binding = the analytical
  lane; the harvest/discharge = Character's T2/T4; the generation-side = the lane split). The loop work
  also CURATES the clean evidence the endgame (§5) trains on.
- **`study_notes_plan.md`:** ON HOLD; its four threads are this plan's evidence (the study lane = the
  Analytical lane; "grounded flavour" / "both questions" = the Curator; prompt-fragmentation = §1).

---

## 11. Questions for the reviewers (GPT, Gemini)
**This is a SPINE REBUILD — the founder asks for extra scrutiny. Push hardest on the first three.**

### The load-bearing risk questions ("super careful")
1. **Is the entanglement bond (§2.4) actually enough to prevent dissociation (§7.1)?** Light,
   on-demand, bidirectional cross-lane "colouring" is the proposed thing that keeps multiple
   evolving-axiom lanes as ONE Du and not several. Is read-only generation-time borrowing sufficient,
   or does one-mind-ness need more (a shared substrate, a primary Character all lanes must reconcile
   to, a periodic identity-consolidation across lanes)? **What would actually measure dissociation**
   so the §7.1 gate is real, not aspirational?
2. **Does the "slightness" of the bond reliably stop capture/leak (§7.2)?** The same channel that
   grounds the self (analytical→self) can let the self's metaphor flood the analytical and re-collapse
   it to the monoculture; and the analytical can sterilise the self. Is a single "strength" knob enough,
   or does the bond need to be *asymmetric / typed* (what may cross, in which direction)?
3. **How many evolving axioms — and is Character its own lane (§8 ⑤/⑥)?** Lean: 3 (Analytical /
   Character / Curator, with Self reading Character) for the fewest moving parts and a two-layer
   identity (slow Character / fast Self). Is that right, or does Self need its own fast "stance" axiom
   (4), or does Character fold into Self (2)? More evolving axioms = more richness AND more dissociation
   surface.

### Architecture decisions (§8)
4. **critic** — fixed utility skill, or evolving standards (his sense of true/good matures)?
5. **emotion** — utility classifier serving Self, or a Self-lane generator?
6. **curiosity** — its own bound axiom, or a tethering clause of Self/Character (so the Frontier stops
   collapsing — study Thread 3)?
7. **The soul/craft split (§2.2/§5)** — axiom-as-evolving-data, weights-as-fixed-craft: sound, or does
   character that never enters the weights stay too shallow to feel like *his*?

### Scope & sequencing
8. **Can a spine rebuild this size be done incrementally without breaking the running Du?** The plan
   keeps Phase B live and migrates lane-by-lane (§9). Is the phasing safe, or is there a hidden
   all-or-nothing dependency (e.g. re-routing nodes by function mid-flight)?
9. **The endgame readiness (§5)** — is "analytical/classifier corpora are clean and trainable now; self/
   generative wait for clean evidence" the right first-migration call, or is even the analytical
   distillation premature until the lanes are settled?
10. **Anything that makes this the WRONG foundation** — a simpler architecture that solves the
    prompt-fragmentation (§1) without four lanes, multiple T2/T4 loops, and a tunable entanglement? The
    §7.5 over-engineering risk, put to the reviewers directly.
