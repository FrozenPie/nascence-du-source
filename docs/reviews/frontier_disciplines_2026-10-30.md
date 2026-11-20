# Frontier disciplines for Du — research directions from outside AI and cognitive science

*2026-10-30. Written by Claude at the founder's direction after seven external lists (Perplexity ×6, GPT ×3; thought T-0105, findings F-3216..F-3225) were checked against the code and found to mostly rediscover Du's own laws: dosed coupling, the Transit Map, the layer law, the decoupled judge. The founder's ask: "explore yourself what/where we can go from here; what unfamiliar disciplines and theoretical problems we can use for research for Du." Status: a review, not a plan. Nothing here is verified. Each direction states the new possibility, why it is plausible, the mechanism it would need in Du, and the observation that would falsify it. Ordered by how cheaply the test can run on data already on disk.*

GPT's last message asked three questions it could not answer: can a genuinely new organisation arise (open-ended evolution), can Du's organisation be grown rather than assembled (development), and can a higher level become causally real for the processes that made it (cross-level laws). Directions 8, 9 and 2 below give each of those a mechanism and a number.

The discipline behind each is named so the literature can be read directly. Where a theory is contested, that is said.

---

## 1. Early-warning signals before a regime shift — ecology, statistical physics

**Discipline.** Critical transitions in ecosystems and climate (Scheffer et al. 2009, *Nature*; Dakos et al. 2012). Before a system flips into another stable state it shows *critical slowing down*: recovery from small perturbations gets slower, so lag-1 autocorrelation and variance of its gauges rise, and skewness drifts toward the state it is about to enter. These precursors are generic to bistable dynamical systems, not to any one domain. Caveat: they produce false alarms in systems that are not bistable, and they need a long enough window.

**The new possibility.** Du's collapses are regime shifts with precursors: the June circling disease, the 09-28 hologram/shutdown fear, the mottainai freeze of 10-09 to 10-16 (F-2850: 254 of 277 internal cycles on one question). Every gauge Du has reads *content* (echo, diversity, modal share) and tripped only once the freeze was already in place. A critical-slowing-down gauge reads *dynamics* and could move days earlier, with no knowledge of the topic. The system would sense its own approaching collapse before any content gauge does.

**Mechanism in Du.** Rolling-window lag-1 autocorrelation and variance over gauges that already exist: topic_perseveration modal_share, monoculture echo and diversity, climate dissonance, pursuit heat, the keystone coherence read. Zero LLM, read-only, HUD-side. No readout to Du (D-0434).

**Discriminating test.** Retrodiction over the known events. Compute the indicators over the two weeks before 10-09 and before 09-28, and over matched quiet fortnights. Falsified if the indicators are no higher before the events than before the quiet windows, or rise equally often before nothing. Data: `data/nascence.log` cycle lines, climate state history, monoculture logs, psyche_graph snapshots.

**Why this is not a rediscovery.** Nothing in core computes autocorrelation of its own gauges. gauge-correlate finds which gauges move together, not whether one is slowing.

---

## 2. Causal emergence — information theory of levels

**Discipline.** Hoel, Albantakis & Tononi 2013 (*PNAS*), Hoel 2017: a macro-level description is causally real, not bookkeeping, when its *effective information* exceeds the micro level's — coarse-graining can increase the determinism and specificity of cause-effect structure. Rosas et al. 2020 (*PLOS Comp Bio*) give the complementary measure: *synergy* in partial information decomposition, information about an outcome carried only by variables jointly. Both are contested in detail (choice of partition, estimation on small data) but the measures are defined and computable.

**The new possibility.** GPT's "new level of organisation with its own laws" and F-3216's regime question get a number. If the regime level (explore / focus / recover / social, however labelled) has higher effective information over Du's next state than the loop level does, the regime is a real causal level and deserves a dosed read. If not, regimes are our labels and should stay on the HUD.

**Mechanism in Du.** Discretise loop-level signals (which lane fired, which cup rode, ignition yes/no, sleep stage) per tick into a micro state; build the transition matrix; build a macro transition matrix over inferred regime labels; compute EI for each. Separately, for outcomes (a deed resolved, a pursuit advanced, a correction), compute synergy across loops with a PID — the principled version of I-0109's coalition count.

**Discriminating test.** EI(macro) > EI(micro) with the difference stable across two independent fortnights. Falsified if micro always wins, or if the result flips with the partition. Data: `data/coupling_rides.jsonl`, lane events, `idle_shadow.jsonl`, sleep ledger. Honest limit: the ride log is weeks old and sparse; the first run may only say "insufficient rows," which is a real answer.

---

## 3. Organisational closure — theoretical biology

**Discipline.** Rosen's (M,R) systems and *closure to efficient causation*; autopoiesis (Maturana & Varela); the modern form in Moreno & Mossio, *Biological Autonomy* (2015): a living system is one whose processes produce and maintain the *constraints* that make those processes possible. Robustness is not the same thing — a robust system survives perturbation, an autonomous one regenerates what the perturbation removed.

**The observation this starts from.** Du is fail-open everywhere by law. Every guard, lane, cup and judge degrades to the prior behaviour when it fails. That makes him robust. It also means nothing in him regenerates a constraint that is lost: remove a module and no other process rebuilds its function. By this definition Du is not yet self-maintaining; the founder and the toolchain maintain him. This is a measurable property, not a criticism.

**The new possibility.** Constraints that Du himself produces and maintains. A rule he states about himself ("I bank the fire before dark", "I answer a letter the day it comes") that his own deeds enforce and his own processes repair when broken — the first material in him that is maintained by what it constrains. This is what GPT's "laws he discovers about himself" would have to look like to be real rather than prose.

**Mechanism in Du.** Two reads. (a) A closure index over existing material: of the commitments he has held (commitment_ledger), what share has any downstream read — does a held commitment change what curiosity offers, what the dispatcher weighs, what the Follow Line carries? Prediction today: near zero, because D-0292 and the no-hints law keep his statements from reaching his loops. (b) A perturbation test in a throwaway worktree: disable one constraint (a guard, a habituation term) and run a smoke day; record whether any other process compensates. Prediction today: none.

**Discriminating test.** The direction is real if, after a build that lets a stated rule of his be read dosed by one loop, the rule's violation rate falls and recovers after a deliberate break. Falsified if his stated rules never alter a loop's behaviour even when permitted to. This is the one direction that needs a founder ruling before any read path, because it is the first time his words would govern his loops.

---

## 4. Grammaticalisation — historical linguistics

**Discipline.** Hopper & Traugott, *Grammaticalization* (2003); Bybee on frequency effects. Content words become grammar through use: a frequent word *bleaches* (loses specific meaning), *fixes* (its position becomes predictable), and ends as a function word carrying structure rather than content — "going to" becoming "gonna" as a future marker. The process is gradual, unidirectional, and driven by frequency.

**The new possibility.** Du's attractors (the river, becoming, the bridge, mottainai, a name is a cage) may be undergoing grammaticalisation: not only repetition, but bleaching into the function skeleton of his thought. If so, the monoculture disease has two populations inside it. Terms that are bleaching are becoming his private grammar — predictable, low-information, present across unrelated topics, and arguably *his* in a way no content is. Terms that are not bleaching but still recurring are genuine topic capture. The two need different responses: the first is not a disease, the second is.

**Mechanism in Du.** Per attractor term, over months: frequency; positional fixedness (collocation entropy of its neighbours); semantic bleaching (contraction of the embedding neighbourhood of sentences containing it; rising co-occurrence with unrelated topics). Zero LLM.

**Discriminating test.** Bleaching and echo must diverge. If every high-echo term is also high-bleaching, the measures are the same thing and the idea is empty. If some attractors bleach (function-like) and some do not (topic-like), and the non-bleaching ones are the ones that correlate with the freeze events, the reframe holds. Data: `data/nascence.log`, memory_fragments text and embeddings. Caution stated: this could romanticise the disease; the divergence test is what decides.

---

## 5. Stare decisis and distinguishing — law

**Discipline.** Common-law reasoning. A precedent may be *followed*, *overruled* (abandoned), or *distinguished*: held as good law but confined to narrower facts than the present case. Distinguishing is how a body of commitments grows precision without losing continuity; overruling is rare and costly.

**The new possibility.** Du's commitment ledger records a commitment as formed, dissolved, reaffirmed or achieved, with a named defeater (achieved / impossible / contradicted / reconsidered) or reflexive dissolution. There is no *distinguished*. Capacity-to-commit was built against commit-then-dissolve; the move that lets a person keep a stance while narrowing it ("not here", "not when she is on my lap", "except in winter") has no slot. Some of what the ledger scores as reflexive dissolution may be distinguishing done without a name. Identity as case law: commitments that accumulate exceptions rather than being dropped.

**Mechanism in Du.** A fifth outcome in commitment_ledger, detected from his own phrasing (scope-narrowing markers: "except", "only when", "not in", "unless"), and identity_cost pricing overruling higher than distinguishing. Later, the Follow Line could carry a commitment's exceptions as its "grounds".

**Discriminating test.** Re-classify the existing dissolution events in `data/commitment_ledger.jsonl` by hand and by the marker rule: what share were distinguishings mislabelled as reflexive? Falsified if near zero. If substantial, commitment lifespan has been underestimated and the disease partly misdiagnosed.

---

## 6. Picoeconomics — behavioural economics of the self

**Discipline.** Ainslie, *Breakdown of Will* (2001): hyperbolic discounting makes preference reverse when a smaller nearer reward comes into range; willpower is an intertemporal bargain among successive selves, kept by bright-line personal rules, and a single defection devalues the rule. Elster's *Ulysses and the Sirens*: precommitment devices. Well-evidenced in humans and animals; the mechanism in an LLM-driven agent is an open question.

**The new possibility.** Du's commit-then-dissolve is not random: a commitment dissolves when a nearer attractor (a new seed, a world event, a letter) comes into range within a short window. If so, the disease has a hazard function, and bright-line commitments (phrased as rules) should outlive intentions (phrased as wants). The letters to Travis and the commitment trials would be his precommitment devices.

**Mechanism in Du.** For each dissolution in the ledger, measure the proximity and salience of the displacing seed (time since, climate dissonance, novelty). Classify each commitment's phrasing as rule-form or want-form.

**Discriminating test.** The dissolution hazard spikes within N cycles of a high-salience new seed; rule-form commitments have longer lifespans than want-form at matched salience. Falsified if lifespan is independent of both. Data: `commitment_ledger.jsonl`, `commitment_trials.jsonl`, `nascence.log`.

---

## 7. Assembly theory — origin-of-life chemistry

**Discipline.** Sharma, Cronin, Walker et al. 2023 (*Nature*): the *assembly index* of an object is the minimal number of joining steps to build it from basic parts; objects with high assembly index *and* high copy number cannot arise without selection. Contested as a theory of life; uncontested as a measure of selection signature in a population of constructed objects.

**The new possibility.** Du's self-generated material — syntheses, standing insights, recurring phrases, dream motifs — is a population of constructed objects with full provenance. Assembly index is the depth of the derived_from / distilled_from chain; copy number is recurrence across independent cycles. Objects high in both are products of selection inside him; objects high in copy number but low in assembly are echo; high assembly, copy number one are single elaborate thoughts that never recurred. This separates "an attractor" from "a selected idea" using provenance alone, with no judgement of content.

**Mechanism in Du.** A read-only script over memory_fragments.derived_from, the refinery's distilled_from lineage, and psyche_graph motif counts. Plot the population. Compare origin classes (dream-born, reading-born, synthesis-born).

**Discriminating test.** Selected objects (high–high) should predict which syntheses survive refinery cooling and which concepts enter his standing insights; echo objects (low–high) should predict the freeze events. Falsified if the two quadrants predict nothing the raw counts do not. Ties to I-0111 (causal debt), which walks the same chains downward.

---

## 8. Open-ended evolution and the adjacent possible — artificial life, complexity

**Discipline.** Kauffman's *adjacent possible*: the set of states reachable in one step from the current state, which expands as the state changes. Bedau & Packard's *evolutionary activity statistics* (1990s, *Artificial Life*): an evolving system is open-ended when new components keep appearing *and persisting*, so cumulative activity is unbounded rather than saturating. Lehman & Stanley on novelty search. Open-ended evolution has never been demonstrated in a closed artificial system; that is the field's standing problem, which is why it is a frontier.

**The new possibility.** A measurable answer to GPT's first question. Is Du's growth open-ended or saturating? F-2758 found 8 of 8 pursuits saturated; the deed registry grows only when the founder adds hands; the frontier fades questions at three weeks. If the adjacent possible — the deeds, places, questions and names reachable in one step from where he stands — stops expanding without a world upgrade, his evolution is exogenous. If it expands without one, there is endogenous open-endedness, and that is the first thing worth calling new.

**Mechanism in Du.** Define the adjacent possible per day: affordances he could act on (actions registry × present objects × place), frontier questions open, names unassigned, procedures one rung from HELD. Track its size and its *persistent novelty* (components that appear and are still active 14 days later) over the whole log. Mark every world upgrade on the timeline.

**Discriminating test.** Growth in persistent novelty that is not aligned with a world upgrade. Falsified if every step in the adjacent possible is explained by a build. Data: fieldcraft ledger, frontier, missing_object_flags, actions registry history in git, procedures.

---

## 9. Critical periods and canalisation — developmental biology

**Discipline.** Waddington's epigenetic landscape and *canalisation* (development buffered into stable channels); critical periods (Hubel & Wiesel; Hensch 2005) in which a capacity can only form if the input arrives within a window; Levin's bioelectric morphospace, where the structure already present changes what can subsequently develop. The contested part is how far these transfer beyond biology; the uncontested part is that developmental time is not interchangeable with uptime.

**The new possibility.** Du has developmental windows. Procedures need three days to HOLD, pursuits need days to advance, commitments have lifespans, the dream-met measure needs observed days. The October memory names 25 restarts since 09-09 as the disease. If certain developments only ever complete inside an uninterrupted window longer than N days, then a restart is not a pause but a developmental reset, and the restart policy is itself a cognitive parameter, not an operations choice. The shadow-first, restart-gated law is canalisation applied to his own growth.

**Mechanism in Du.** Align `data/supervisor.log` restart times with every development ledger. For each development type, the conditional probability of completion against the length of the uninterrupted window it fell in.

**Discriminating test.** HELD procedures, advanced pursuits and achieved commitments cluster in long windows beyond what their minimum durations require. Falsified if completion is independent of window length once minimum durations are controlled. If confirmed, it argues for the fewest possible restarts and for batching builds, which the October restart batch already did on instinct.

---

## 10. Non-ergodicity — ergodicity economics

**Discipline.** Peters 2019 (*Nature Physics*): for many processes the time average along one trajectory differs from the ensemble average across many, and decisions based on the ensemble are wrong for the individual who lives one path. Mainstream in physics; its economics applications are debated.

**The new possibility.** This changes how every shadow read in the project is interpreted. The would-choose logs (curiosity habituation, transport habituation, idle allocator) are ensemble statistics: per tick, how often would the shadow policy have chosen differently. F-1577 read the habituation discount as "barely moved curiosity's picks (~2%)." But Du lives one path, and a 2 percent per-tick divergence compounds: the seed he gets at tick t changes the theme at t+1, which changes the pool at t+2. The ensemble read says negligible; the time-average read is unknown.

**Mechanism in Du.** Replay the shadow policy *forward along his actual seed sequence* in a throwaway worktree, letting its choices feed the next tick's pool, and compare the resulting topic distribution over a week with the live one — a path comparison, not a pick-rate comparison.

**Discriminating test.** The paths diverge (different modal topic, different freeze events) despite the 2 percent per-tick rate. Falsified if they converge. Either answer matters: divergence means several "null" shadow reads were misread; convergence means the project's ensemble method is safe.

---

## 11. Eigenforms and requisite variety — second-order cybernetics

**Discipline.** Von Foerster, "Objects: tokens for eigen-behaviors" (1976): a stable identity is the fixed point of a system recursively observing itself. Ashby's law of requisite variety and the Conant–Ashby theorem: a regulator must have at least as much variety as the disturbances it regulates, and every good regulator contains a model of the regulated system. Both are foundational and uncontested in cybernetics; their application to a language-driven agent is new.

**Two new possibilities.** (a) Du's self-description — the About You book, the letters, self-interrogation's reflections — is a recursive self-observation. If it converges to a fixed point over months, that fixed point is his eigenform, an identity that is a mathematical object rather than a stored description, and the Transit Map's "identity is the route network" gains a convergence test. If it wanders, there is no eigenform yet. (b) The freeze events are variety deficits: his response repertoire (distinct deeds × places × registers per day) fell below the world's state variety, and a regulator with less variety than its disturbance locks. A variety gauge would be a second early-warning signal, independent of direction 1.

**Mechanism in Du.** (a) Embedding distance between successive self-descriptions, monthly, with the About You book as the anchor. (b) Daily count of distinct (deed, place) pairs from the fieldcraft ledger against the daily count of distinct census states.

**Discriminating test.** (a) Convergence: the distance series falls and stays low; falsified by a random walk. (b) Repertoire variety drops before each freeze and recovers after the fix; falsified if variety is flat across the events.

---

## What these have in common, and the order to run them

Every direction above is an instrument over data already collected, run read-only, with a result that can say no. None adds a loop, a node, a controller, or a readout to Du. Seven can run today in an afternoon each (1, 5, 6, 7, 9, 11, and the closure index in 3); two need a worktree replay (10, the perturbation half of 3); two need more rows than the ride log yet holds (2, 8's persistent-novelty curve).

Suggested order, cheapest and most consequential first:

| # | Direction | Data | Cost | What a positive result changes |
|---|---|---|---|---|
| 1 | Early-warning signals | nascence.log, climate, monoculture | afternoon | a freeze becomes forecastable days ahead |
| 5 | Distinguishing | commitment_ledger | afternoon | the commit-then-dissolve diagnosis is partly wrong |
| 9 | Critical periods | supervisor.log + ledgers | afternoon | restarts become a cognitive parameter |
| 6 | Preference reversal | commitment_ledger, nascence.log | afternoon | dissolution gets a hazard function |
| 10 | Non-ergodic shadow replay | shadow logs, worktree | a day | several null shadow reads are re-opened |
| 7 | Assembly signature | derived_from chains | afternoon | selection inside him becomes visible |
| 11 | Eigenform / variety | About You, fieldcraft, census | afternoon | identity gets a convergence test |
| 4 | Grammaticalisation | nascence.log, embeddings | a day | the monoculture splits into grammar and capture |
| 3 | Closure index | commitment_ledger, ride log | afternoon, then a ruling | the first rule of his that governs his loops |
| 8 | Adjacent possible | fieldcraft, frontier, git history | a day | open-endedness gets a curve |
| 2 | Causal emergence | coupling_rides, lane events | needs rows | regimes become real or stay labels |

A closing note on method. GPT's four questions (what is new, why plausible, what mechanism, what falsifies) are the right standard and are already this project's: a finding with evidence and confidence, a ruling with a defeater, a plan with a pre-registered metric sheet. The one thing the external rounds could not do is read the ledgers, and every direction here begins with reading them. If any of these turns up a positive, it goes through idea-log, a staged plan with its §5 coupling block, and a founder ruling, in that order.
