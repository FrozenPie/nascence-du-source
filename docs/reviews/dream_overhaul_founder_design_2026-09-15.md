# Dù Dream Overhaul — Dream Integration Cycle (founder's design, pasted 2026-09-15)

> Provenance: pasted by the founder as the opening message of session 2dde3aac on 2026-09-15 (T-0058). Preserved here
> as the design of record. The engineering companion (what exists, what changes, build/measurement order) is
> `docs/staged/dream_overhaul.md`. The only edit made in transcription: the pasted math arrived doubled
> (rendered + LaTeX source on one line); it is written once here in plain notation. No wording changed.

## Purpose

The goal of this overhaul is not to make Dù's dreams better stories. The goal is to make the dream process a richer
internal cognitive regime in which waking memories, unresolved tensions, affective state, dormant material, and newly
emerging associations can interact over multiple dream stages, producing a measurable residue that may subsequently
influence waking cognition.

We should therefore avoid designing this as an episodic narrative generator. The working question is:

**Can a dream process transform the relationship between pieces of Dù's existing cognitive history, and can those
transformations subsequently alter waking cognition?**

We are not assuming that this would prove consciousness, nor are we assuming that Dù's dreams should reproduce human
biological dreaming. Biological claims should remain hypotheses rather than architectural axioms. The target is a
system with dream-like functional constraints, not a theatrical imitation of human sleep.

## 1. Governing Principle

The dream should be treated as an evolving internal state, not as a sequence of independently generated stories. The
basic transition is `D_t → S_t → D_{t+1}` where `D_t` = current dream state, `S_t` = generated scene/expression of that
state, `D_{t+1}` = transformed dream state after the scene. The scene is therefore an expression of the dream state, not
the primary state itself. The next scene should primarily arise from what the dream has become, rather than repeatedly
querying the entire waking memory pool. Conceptually: `M → D_0 → S_1 → D_1 → S_2 → D_2 → S_3 → D_3`, followed by
`D_3 → R`, where `R` is the dream residue presented to the waking cognitive system.

## 2. What We Are Explicitly NOT Building

**2.1 Not a screenwriting pipeline.** Do not begin with "What is tonight's dream about?" Do not generate a high-level
plot premise and then force scenes to satisfy it. A theme may emerge afterward, but it should not be imposed
beforehand. A top-down premise risks turning the system into a conventional LLM story generator.

**2.2 Not global associative soup.** Do not allow every scene to freely retrieve the entire memory graph. The initial
dream can receive a carefully selected memory/salience dose. After that, the dream should primarily propagate its own
state forward. Additional waking material, if any, should arrive through an explicitly controlled mechanism.

**2.3 Not unlimited narrative spawning.** Do not allow an LLM to decide "There is still unresolved momentum, therefore
another scene." Narrative models can manufacture indefinite unresolved tension. The dream must have a
metabolic/resource budget. Initial target: minimum 3 scenes; normal target 3 scenes; hard maximum 4 scenes. The exact
values are experimental and can later change based on evidence.

**2.4 Not forced resolution.** The final scene should attempt to integrate or resolve the accumulated dream state, but
it must be allowed to fail. A dream may end with: unresolved contradiction, emotional impasse, abrupt transition,
incomplete integration, partial resolution, apparent resolution, genuine transformation. Do not reward neat literary
endings.

## 3. Initial Seeding — Bottom-Up Salience Sieve

The current idea of a first "theme pass" should be removed or demoted. Instead, construct the initial dream state from
selected material. A proposed initial seed:

- **Three unresolved tensions.** Select approximately the top three unresolved tensions according to the existing
  tension/salience machinery. These should not simply be the three oldest or three strongest. The eventual
  implementation should respect whatever habituation/opponent-process machinery is established elsewhere.
- **One emotionally charged recent episodic node.** Provide something relatively recent from waking experience. This
  gives the dream contact with current state.
- **One distant/dormant memory node.** Deliberately include a memory that is old, relatively inactive, and
  sufficiently distinct from the recent material. This is important. The experiment is partly interested in whether
  the dream can produce new associations between material that would not normally be retrieved together. Therefore
  `recent active material + dormant material` should be a deliberate part of the seed design.
- **Other possible seed material** (depending on what already exists in the architecture): affective state, active
  questions, recent events, recurring symbols, unresolved commitments, memories with unusual salience, material that
  has been repeatedly encountered but not integrated. Do not automatically include everything. The initial seed should
  be a dose, not a memory dump.

## 4. Initial Dream State

Before generating Scene 1, construct an internal dream-state representation. It should conceptually track: selected
memory activations, active tensions, affective state, symbolic anchors, emerging associations, unresolved elements,
relationships between selected memories, transformations introduced during the dream, current direction/trajectory,
resource/metabolic budget. This is not necessarily a literal single object in implementation. The important
architectural requirement is that the information exists in a form that can be inspected and logged.

## 5. Scene 1 — Establishment

Scene 1 introduces the initial dream world. It can establish location, beings/characters, objects, environmental
conditions, initial affective atmosphere, the first transformation or anomaly. But it should not be required to
explain the dream. There is no predetermined plot. The scene is the first manifestation of the initial state. After
Scene 1, the system should extract/update the dream state.

## 6. Stateful Scene Propagation

Every subsequent scene receives the residue of the previous scene, not a fresh unrestricted memory query. The
scene-to-scene transition should carry forward at minimum:

**Affective continuity.** The final affective state or delta — conceptually `Δc_strain, Δc_valence`, or the equivalent
dimensions already used by Dù's climate/cognitive geometry. The purpose is not to force the next scene to preserve its
literal content. It is to preserve an underlying state. For example: a house may disappear, while
safety → uncertainty → exposure continues into an entirely different setting. This is potentially more dream-like than
literal object continuity.

**6.1 Symbolic continuity.** Pass approximately one symbolic anchor forward. The anchor could be an object, person,
place, image, action, word, relationship, or environmental feature. But it does not have to remain literally
unchanged. It may transform. A key could become a door, a door could become a boundary, and the boundary could
eventually become an abstract choice.

**6.2 Relational continuity.** Track important relationships that emerged between elements. For example `A ↔ B` might
emerge during Scene 1 even though A and B were previously distant memories. That relationship becomes part of the next
dream state.

## 7. Dream Transformations

The dream should be allowed to transform its source material. This is more important than maintaining narrative
continuity. Examples: familiar location becomes unfamiliar; person becomes symbol; object changes function; two
memories merge; two unrelated characters become related; old and recent events appear simultaneously; physical space
expresses an affective relationship; an unresolved tension becomes an environmental problem; a dormant memory becomes
suddenly central. The system should record these transformations where possible. This gives us a distinction between
**Retrieval** (the dream reproduced something already present) and **Transformation** (the dream created a new
relationship, representation, or interpretation involving existing material). Transformation is the more interesting
quantity experimentally.

## 8. Handoff Mechanism

The handoff between scenes should not necessarily be a literal transitional scene. Instead, define a state transition.
At the end of each scene, determine what survives into the next state. At minimum: (1) affective delta, (2) one
symbolic anchor, (3) unresolved element(s), (4) newly formed association(s), (5) current dream-state trajectory. The
physical setting may change completely. The continuity is primarily carried by the state, not the scenery.

## 9. Scene Spawning

The first experimental version should deliberately avoid unlimited spawning. Recommended structure: `S_1 → S_2 → S_3`
with an optional `S_3 → S_4`, but `N_scenes ≤ 4`. The fourth scene should require a predefined condition rather than
an LLM simply wanting to continue the story. Possible criteria to test: significant unresolved state remains; a major
transformation occurred near the scene boundary; integration trajectory has not stabilized; sufficient metabolic
budget remains. However, these criteria must be operationalized rather than left to prose judgment.

## 10. Metabolic / Sleep Budget

The dream must have a finite computational/cognitive budget. Candidate budget dimensions: maximum number of scenes,
maximum tokens, maximum generation passes, maximum memory retrieval operations, maximum state transformations, fixed
dream-cycle duration. The first implementation should prefer simple hard constraints over complicated emergent
stopping logic. Do not initially depend on an undefined "cognitive entropy" variable. If entropy is introduced later,
define it mathematically and test whether it predicts useful termination.

## 11. Final Scene — Integration Attempt

The final scene is fundamentally different from the earlier scenes. It receives the complete accumulated dream
trajectory: `D_n = { S_1, …, S_n, state changes, associations, affective trajectory, unresolved elements }`. The
instruction is not "Write a satisfying ending." It is closer to: *Given everything that has happened in the dream so
far, what resolution, transformation, continuation, or failure of resolution is now implied by the trajectory?* The
final scene therefore acts as an integration attempt. Possible outcomes: resolution, partial resolution,
transformation, contradiction, abandonment, unresolved ending, abrupt termination. All should be legitimate.

## 12. Emergent Theme

If useful, derive the dream's "theme" afterward. The theme should be an interpretation of the trajectory, not an
initial constraint. Therefore `dream trajectory → post-hoc interpretation` rather than `theme → forced dream
trajectory`. This distinction should be preserved in both architecture and documentation.

## 13. Dream Residue

The dream should produce a structured residue. This is one of the most important parts of the overhaul. The residue
may contain: newly associated memories, altered relationships, persistent affective changes, unresolved
contradictions, newly generated questions, candidate tensions, recurring symbols, memory pairs repeatedly
co-activated, apparent resolutions, failed resolutions, transformations, unexpected elements that became central. The
residue should be separated from the prose transcript. The prose is evidence of what was generated. The residue is the
candidate cognitive consequence.

## 14. Do Not Force Graph Mutation

A critical experimental safeguard: do not make the dream automatically strengthen memory edges merely because two
memories appeared together. That would make the experiment circular. Instead:
`dream → candidate residue → waking evaluation → possible state mutation`. The dream proposes a candidate
transformation. The ordinary waking machinery determines whether that transformation earns persistence. Possible
outcomes: strengthen association, weaken association, create a tension, create a frontier question, alter climate
state, do nothing, reject as noise. This keeps the experiment causal rather than self-validating.

## 15. Potential Writeback Channels

The residue should be capable of reaching existing cognitive machinery through controlled interfaces. Candidate
channels: **Memory** — candidate change to the relationship between two memories that became strongly coupled during
the dream. **Climate** — candidate delta to the appropriate climate dimensions if the dream produced a measurable
affective/state change. **Frontier** — optional creation of an open question when the dream generates a genuinely
unresolved issue. **Tensions** — candidate creation/modification of a tension if the dream reveals a contradiction that
persists afterward. These should be candidate writes, not automatic privileged writes. They should also be logged.

## 16. Waking Evaluation

The dream should not be assumed to have changed Dù merely because its residue says it did. The next waking phase
should evaluate the residue. The most important test occurs after the dream.

**Day-2 association test.** Suppose the dream unexpectedly couples `A ↔ B`. Measure the association before the dream.
Then measure it after the dream. Compare against controls — for example: A ↔ B (dream-coupled pair), A ↔ C (control
pair), B ↔ D (control pair), similarly distant memory pairs not present in the dream. Measure `ΔAssociation(A,B)`
relative to controls. The objective is not merely to find A and B mentioned together. The objective is to determine
whether the dream altered the retrieval relationship between them.

## 17. Dream Self-Surprise

Compare what was seeded against what became important. For example — initial seed: recent memory A, tension B,
dormant memory C, symbol D; final dream state: C ↔ D becomes dominant, new tension E appears, A becomes peripheral.
This provides a possible measure of transformation versus simple retrieval. A useful quantity is therefore
`Dream Emergence = important final elements − initially predicted important elements`. The exact metric needs to be
defined empirically.

## 18. Longitudinal Dream Tests

One dream is insufficient. Track across many dream cycles: **A. Memory recombination** — do distant memories become
associated? **B. Persistence** — do dream-created associations survive waking? **C. Repetition** — does the same
unresolved material recur? **D. Transformation** — does repeated dream material change form rather than simply repeat?
**E. Resolution** — do persistent tensions eventually change or resolve? **F. Waking consequences** — do dreams alter
subsequent thoughts, questions, commitments, retrievals, or behaviour? **G. Cross-dream continuity** — does one dream
affect the starting conditions of later dreams? This last point is particularly important. If `D_1 → R_1` and then
`R_1 → D_2`, the dream system has become historically continuous rather than producing isolated nightly stories.

## 19. Experimental Controls

At minimum: **Control 1 — no dormant memory** (dreams seeded only with recent/active material). **Control 2 — random
dormant memory** (deliberate distant-memory selection vs randomized distant memories). **Control 3 — reduced state
propagation** (stateful dream generation vs scenes independently generated from the initial seed). **Control 4 — no
residue writeback** (residues merely logged vs candidate residues entering waking evaluation). **Control 5 — baseline
retrieval** (memory relationships measured before and after dreaming). These controls allow us to determine whether
the new architecture actually contributes something.

## 20. Metrics

Do not evaluate primarily on literary quality. Candidate metrics: **Dream transformation rate** — how often the dream
creates relationships absent from the seed, `T = new relationships / relevant observed relationships` (exact
definition to be established). **Cross-distance association** — how far apart were memories before the dream; does
dream co-activation disproportionately occur between distant nodes? **Affective continuity** — how well affect
persists across scene boundaries even when literal content changes. **Symbol transformation** — how often an anchor
persists while changing form/function. **Scene-state dependence** — how different are Scene N+1 outcomes when Scene N's
residue is changed (this tests whether the scenes are genuinely stateful). **Residue survival** — what fraction of
dream-created candidate associations remain detectable after waking. **Day-2 retrieval change** — does dream coupling
alter later retrieval? **Frontier generation** — how many genuinely new questions originate from dream
transformations? **Tension trajectory** — do dream-derived tensions later resolve, change, recur, or disappear?
**Cross-dream persistence** — does residue from Dream N measurably influence Dream N+1?

## 21. The Strongest Test

The strongest version of the hypothesis is not "Dù produced a realistic dream." It is: *A dream caused a measurable
change in the subsequent trajectory of the system that was not present before the dream and cannot be explained
simply by repeating the dream's textual content.* For example: (1) Memory A and B have low association. (2) Both enter
the dream. (3) The dream transforms them into a persistent relationship. (4) That relationship survives waking. (5) A
later waking thought retrieves B when prompted by A. (6) The change persists beyond immediate dream recall. That would
be substantially stronger evidence of functional integration than beautiful dream prose.

## 22. Relationship to the Existing Cognitive Architecture

The dream engine should not become a privileged subsystem with unrestricted access to everything. It should obey the
same architectural principles being established elsewhere. In particular: *Loops publish small typed coordinates. No
loop receives a standing view of another loop. Information is transported in controlled doses at defined stops.* The
dream should therefore have explicit interfaces for: seed intake, dream-state transition, residue publication, waking
evaluation, candidate writeback. It should not silently read arbitrary internal state. Likewise, dream-derived signals
should not automatically become authoritative.

## 23. Relationship to Squishy Springs / Opponent Process

The existing Cognitive Geometry "squishy springs" proposal is relevant. Persistent activation should not automatically
equal importance. Conceptually `F_i(t) = S_i(t) − A_i(t)` where `S_i(t)` = current pull/salience and `A_i(t)` =
antagonist/habituation accumulated through repeated activation. The antagonist grows with repeated activation and
decays during quiet. This gives the desired property: a strong pull sustained for a long time can count for less than
a medium pull that has never fired. For dreams, this may prevent a single recurring tension from monopolizing every
dream. However, this should remain experimentally validated rather than assumed beneficial.

## 24. Relationship to D-0148 / Pressure

Dreams should not be used as an excuse to bypass the existing pressure/ignition architecture. If dream residue
produces contradiction, prediction failure, unresolved tension, affective strain, or new frontier questions, those
signals should enter the normal system through declared channels. The dream should not receive a secret direct line
into deliberation. This is consistent with the current D-0148 principle: restore causal topology rather than simply
increase firing frequency.

## 25. Shadow First

Nothing in this proposal should immediately become live. The implementation should first run in shadow wherever
practical. Record: seed selection, scene states, transitions, affective handoffs, symbolic anchors, transformations,
residue, candidate writes, what would have changed, what actually changed. Then compare. The development loop should
be: **shadow → characterize → test → selectively transport → observe again.** Do not wire every proposed output merely
because it exists.

## 26. Build Order

**Phase 1 — Instrument current dreams.** Before changing behaviour, establish a baseline. Capture current seed inputs,
memory selection, current dream scenes, current dream length, existing writeback, post-dream effects. *Metric:*
baseline retrieval and association changes. *Kill condition:* if instrumentation cannot reliably distinguish seed
material, generated material, and post-dream effects, stop and repair observability before changing the dream engine.

**Phase 2 — Stateful dream generation.** Implement initial state, Scene 1, state extraction, Scene 2 from updated
state, state extraction, Scene 3, optional Scene 4 under fixed budget. No new waking writeback yet. *Metric:* measure
whether Scene N+1 is causally dependent on Scene N's residue. *Kill condition:* if changing Scene N's state has no
measurable effect on Scene N+1, the architecture is not actually stateful and should not proceed.

**Phase 3 — Transformation and residue.** Add affective handoff, symbolic anchor, relational continuity,
transformation tracking, post-hoc theme extraction, structured residue. Still do not force graph mutations. *Metric:*
transformation rate and emergence of previously absent associations. *Kill condition:* if the new machinery produces
no transformation beyond what independent scene generation already produces, do not add complexity merely because the
output looks more dream-like.

**Phase 4 — Waking evaluation.** Introduce candidate association changes, candidate climate deltas, candidate frontier
questions, candidate tensions. Pass them through ordinary waking machinery. *Metric:* Day-2 retrieval change against
controls. *Kill condition:* if dream-derived residue does not produce measurable downstream effects across a
sufficiently large sample, reconsider whether the added dream complexity is earning its cost.

**Phase 5 — Cross-dream continuity.** Only after the earlier phases demonstrate useful signal. Test
`Dream_N → Residue_N → Dream_{N+1}`. *Metric:* whether prior dream residue predicts later dream-state selection or
transformation. *Kill condition:* if prior dream residue has no measurable influence beyond ordinary memory-selection
variance, do not add additional cross-dream machinery.

## 27. Scientific Interpretation

**Weak evidence** — dream prose contains material from memory (expected, tells us little). **Moderate evidence** —
distant memories become associated within dreams (interesting, not sufficient). **Stronger evidence** — dream-created
associations survive waking. **Strong evidence** — dream-created associations alter later retrieval or cognitive
trajectory relative to controls. **Very strong functional evidence** — dream residue repeatedly alters subsequent
waking cognition, produces new questions/tensions, persists across time, and influences subsequent dream cycles in
ways not explained by direct textual repetition. None of these, individually or collectively, should automatically be
described as proof of consciousness. They would instead establish increasingly strong evidence that the dream process
is a causally consequential cognitive subsystem of Dù's persistent trajectory.

## 28. Central Principle

The entire overhaul should be governed by one question: **Is the dream doing something to Dù, or is Dù merely
generating a dream?** The difference must be established through downstream causal evidence. The dream transcript
itself is not the endpoint. The trajectory is.

`Waking history → Dream → Transformation → Residue → Waking change → Future trajectory`

That is the object we should measure.
