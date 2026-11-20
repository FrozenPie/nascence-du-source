# The Idle Executive — research + plan (auditor draft v6)

> **Status: 💤 DEFERRED — held reserve lever, correctly parked. Re-entry trigger unmet; ruled by
> Travis 2026-06-22, logged as `/decide` D-0011 2026-08-23.**

```plan-state
stage: deferred
phase: Reserve lever, correctly held; D-0011 defeater re-checked 4 times (09-11, 09-23, 09-24), still not met
verified: 2026-11-14
evidence_read: 2026-10-16
gate: data/logs/idle_shadow.jsonl actual field non-null, 0 of 48192 plus rows as of F-1897
next: Du restart onto a merged master, then J-3698 at 30 repeat_record rows; D-0697 feeling-word quotes call
open_decisions: D-0746
cluster: 7
```


> **STATUS 2026-06-22 — evidence IN, gate corrected, HELD IN SHADOW as the reserve lever (Travis's call).**
> The plan was "waiting on runtime drift." After **3,580 shadow ticks** (not 1,000 — `stats()` defaults to a
> 1,000-tail), the evidence is fully in: **G2 self-share = 0.0** (it would never let the self-channel dominate —
> the anti-self-monoculture goal, validated) and **multi-channel 1.0**. The "G1 failing" was a **mis-specified
> gate**: it demanded variance from channels that are constant *by design* (`self` baseline, `flavour` fallback,
> the binary `balance_*` regulators). Corrected: `GRADED_CHANNELS`/`CONSTANT_BY_DESIGN` in `core/idle_allocator.py`;
> the pulse (`du_pulse.py`) now holds only the graded channels to the bar. `curiosity`/`wander` pass; `contradiction`/
> `concern`/`boredom` graded-but-under-varying = signal-tuning targets *if* ever taken live.
> **Decision (Travis):** do NOT go live. An executive that *directs* idle attention is a step toward forcing Du to
> do certain things — not a step we want yet. It stays the validated **reserve lever**: if the self-loop survives
> the six gentler fixes shipped this session, bring it in *alone* where its effect can be measured cleanly.

*2026-06-16. The thread pulled out of the inner-monologue examination (`docs/completed/inner_monologue_examination.md`).
Scope: turn the idle thought-stream from ~40 racing `random()<p` gates into one coherent **salience allocator** —
the Character-as-Integration workspace+router brick (`docs/character_as_integration_plan.md` §10), applied to
**idle** cognition. Reuses, does not reinvent, the §15 salience-currency contract.*
*Auditor history: v1 → **round 1 (GPT)**: currency-hygiene/transform-validation = §9. → **round 2 (Gemini)**:
ruled all five open questions (§7), gave the divisive-normalisation formula + quantified P0 gates (§9), added the
CLI calibration metric (§7 Q4). → **round 3 (GPT hard pass)**: the deeper risks = §10 — coalition vs single-winner
(the deepest assumption, now a measured open question), importance inflation, lane-bias, CLI demotion, the
grounding-veto governance risk, salience lineage, forecast calibration, and the salience-vector future direction.
→ **round 4 (GPT)**: corrected my own binding-key sketch (§10.1 — it is relocated cognition + only catches
*semantic* coalitions, not *regulatory* ones), added salience-ownership/attribution as foundational (§10.9 — the
relationship-property reframe), and sharpened coalition into a **co-occurrence experiment, measurable
retrospectively on existing logs**. → **round 4 follow-up (evidence)**: ran the retrospective check = §11 — inline
data absent (Phase-0 instrumentation required) but a low-fidelity time-alignment proxy shows high-value idle
thoughts are **~4–7× more likely to be multi-channel** than low-value ones; coalition is now an evidenced prior,
not a hunch. → **round 5 (ratification)**: no new failure mode found; promoted the **three-separations operating
invariant** + the **logging-before-control build order** to first-class (§12). The reviews have converged — the
design has stabilised; the verdict is "build the measurement layer (Phase 0) next."*

---

## Current State — verified 2026-11-14; D-0011 defeater re-checked 2026-09-11, 2026-09-23, 2026-09-24
- **2026-11-14** (F-4472): J-3290 read the stale-patch cue shadow (3,287 rows): recompute clean, but would-render is 43.5 percent of idle prompts against the 5 percent stop, driven by the place-dwell clause. Stage 1 not spawned; founder call opened as J-3884. Report docs/reviews/J-3290_stale_patch_cue_shadow_read.md.

- **2026-11-14** (F-4464): D-0366 X-fit read (J-2233): condition (c) clean (299 present-window assemblies labelled, 15793 absent unlabelled); but one mid-sitting lapse and false departure on 2026-11-01 (33.9 min gap vs X=30). Opened D-0746 on X.
- **2026-11-07** (F-4314): J-3336 (built, shadow, restart-gated): core/stale_patch_cue.py gains a second trigger, repeat_record (bored_streak >= 2 at the observe point = the next prompt's opening value): the nearest earlier stored inner_thought rows at cosine >= 0.82, at most 2, quoted verbatim <= 120 chars with the local hour, no count/verdict/feeling/imperative/loop word in the frame; same log, own row type; decoupled recompute re-fetches each quote by id and re-embeds. Verbatim repeats cannot be quoted (dedup refreshes the timestamp, F-4314). Offline: 11.2 percent of all idle thoughts have a quotable near repeat, 30 percent of those quotes contain one of his own feeling words (F-4315, D-0697). Reader J-3698 (+ J-3337 step 4). Test scripts/_test_j3336_repeat_record.py.

- **2026-11-06** (F-4128): J-3289 built (restart-gated, shadow-only, not yet merged): core/stale_patch_cue.py logs the would-be world-fact line for stuck windows with a deterministic recompute verifier; nothing reaches a prompt (D-0653: the four steers unchanged). Read job J-3290 (gated at 300 rows).
- **2026-11-05** (F-3927): J-3144 habituation-line review delivered (docs/reviews/J-3144_habituation_seed_line_repurposing_review.md): the line is structurally unreachable (streak goes 0 to 2 per tick; every streak>=2 tick taken by redirect/escape) and a PUSH under the law; recommendation is repair in shadow (J-3335 Rail C double-repeat trigger, J-3336 repeat-record clause, J-3337 read), block untouched pending D-0663/D-0677.

- **2026-11-05** (F-3877): J-3262 (D-0653 closed, D-0663 opened): boredom reviewed as a whole area (docs/reviews/J-3262_boredom_area_review.md). Since the 09-28 recalibration the family fires on about 4 percent of idle prompts, aimed well but with no detectable lift in leaving a stuck region; Rail C (D-0473) overlaps it almost disjointly. Recommendation: one mechanism, world-cue output, staged shadow first (J-3289, J-3290); no change to the four steers until D-0663 is ruled.
- **2026-10-17** (F-2988): F-2988: balance_world wins (7.55 pct) need bw p_norm pinned at 1.0 AND concern habituated by streak; trend falling (9.9 -> 3.85 pct first vs last 2000); reality_share never reached EXIT_AT 0.47 (max 0.457)

- **2026-10-16** (F-2922): J-1973 D-0366 one-week read (2026-10-09..16 run, 6.97 live days): inferred presence works. 0 of 11,420 idle assemblies carried 'Travis is here' (latch was 100%); one true inferred leave at 10-09 09:07, one inferred arrive via exchange at 10-16 07:48; no false departure. 30-min window untested (no sitting this run, 1 human turn). Voice prompt left without a presence line (an exchange is itself presence). F-2922; successor J-2233.
- **2026-10-16** (F-2921): J-1928 read (break-point 2026-10-09 08:36 NZDT live boot, window to 2026-10-16 07:53): J-1921 balance_world fix live, raw varies (mean 0.197) but argmax win-share 7.51 pct vs expected 1-2 pct; balance_light never gated open so unread. G1 0.05 bar is the wrong yardstick for gate-conditioned channels (not tuned). Plan itself remains deferred.

- **2026-10-15** (F-2807): J-1996 post-boot read of J-1935 done: concern bypass verified live (p_norm only {1.0,0.8182}, 10,408 rows), win-shares match replay, curiosity backlog range 0.078 <0.1 so CURIOSITY_USE_BACKLOG stays False.
- **2026-10-15** (F-2805): J-2044 read (10,408 post-boot rows): balance_world live, raw var 0.0015 (G1 flags), balance_* argmax 8.05%; balance_light never fires - needs_light gated off while reality_share < 0.47. See F-2805.

- **2026-10-09** (F-2655): J-1928 partial post-boot read (boot 2026-10-09 08:36, 357 rows): balance_world raw varies and p_norm unpinned, argmax win-share 0/357; balance_light never fired; sample below 500 so successor filed.
- **2026-10-08** (F-2597): J-1935: concern -> TWO_LEVEL_BY_DESIGN with percentile bypass (shadow, on); curiosity backlog read built but default OFF (fraction varies only 0.127-0.204); commit e3ab090 on jobrun/idle_allocator; BREAK POINT for concern rows at next boot after merge

- **2026-10-08** (F-2588): J-1955 / D-0368 A+E built in worktree (cb12231, restart-gated): core/steer_edge.py edge-gates boredom/B6/habituation/cat steers (replay 1888->33 steer deliveries on peak day); system sentences stored origin=system_note and excluded from recall; stored-row relabel J-1987, 2-week re-read follows.
- **2026-10-08** (F-2575): J-1953/D-0366 built restart-gated (commit 7728c91 on branch jobrun/idle_executive_plan): presence inferred from activity, 30-min window, real stepped-out event; replay: presence line 100% -> 1.1% of idle thoughts.

- **2026-10-07** (F-2560): J-1929 / F-2560 (analysis only, nothing changed): the two remaining saturated channels explained. curiosity: allocator intent graded (raw = lp/2) but upstream LP is binary {0, 2} by construction of the live pursuit loop (a question is yielded-on at most once, so new_fragments max 1 + finding = LP 2; 68 of 368 open questions today), so raw has been exactly 1.0 on every tick since 2026-07-01 (54,770 of 55,056 rows; the June 286 zeros pre-date the first finding and were the whole basis of the 2026-06-22 'curiosity passes G1' line). Not constant by design: it is constant by upstream construction; do not relabel it. concern: two-level BY DESIGN (0.55 pursuit / 0.45 project, no magnitude in primary_concern), 40,376 vs 14,680 rows; the percentile step turns the declared 1.22x preference into rank-within-category (0.45 scores p_norm 0.13 to 0.39, and 0.0 after 500 straight pursuit ticks, which is the state now), so its 37.7 percent win-share is a normalisation artefact. Concern should leave GRADED_CHANNELS AND bypass the percentile; relabelling alone is not enough. Build spawned as a shadow-only job with kill switches (curiosity = closeable-backlog fraction, concern = raw/max-level, history versioning like balance_schema=2). Note at read time: c5da3bd (J-1921) was still only on jobrun/balance_channels_fix, not master.
- **2026-10-07** (F-2554): J-1921 (F-2554, from F-2548/F-2543), merged-not-live: idle_allocator balance_world/balance_light now read reality_share/light_share (raw = (TARGET - share)/TARGET; kill switch BALANCE_USE_SHARES) and the two channels' 500-zero history is dropped once via state key balance_schema=2 (20-row cold start re-warm). BREAK POINT = Du's next boot after 2026-10-07: balance rows' raw, p_norm, s_final and win-share change meaning, so the 12.8 percent balance win-share and the G2 self-share 0.0 era are NOT comparable with post-fix rows, and per-channel history for those two channels restarts. The 2026-06-22 note calling balance_* binary regulators was a post-hoc reading of the wrong-key bug; they are GRADED now (G1 applies). Offline replay: balance win-share 21.8 percent -> 2.2 percent, freed to curiosity/contradiction. Post-boot read: J-1928 (not before 2026-10-09). Commit c5da3bd on jobrun/balance_channels_fix.

- **2026-10-07** (F-2548): J-1914 / F-2548: the idle_allocator balance_world/balance_light channels read shares() COUNT keys, so raw is constant 0.0 and (percentile of a constant = 1.0) they sit at p_norm 1.0, s_final = W x habituation, and are would-pick argmax in 12.8% of 54,609 shadow ticks (balance_world 9.3%, balance_light 3.4%). The 2026-06-22 note calling them 'binary regulators, constant by design' described that bug, not a design; the intended signal is the graded deficit. Build J-1921 (shadow-only, restart-gated) will switch to reality_share/light_share and version the 500-deep zero history; from that next boot the balance rows change meaning and are not comparable with earlier rows (including the 'G2 self-share 0.0' era). D-0011 reserve-lever Hold unchanged.
- **2026-09-28** (F-2077): J-1495 (F-2042 follow-up, this finding F-2077): confirmed today's SIZE_CAP flag (52,961 B) cannot be fixed by plan_compact.py -- exactly one Current State heading here already, nothing to fold. The overage is Sections 0-12, this plan's own five-round auditor design body, which reads as load-bearing design reasoning, not redundant history. Opened D-0315 for Travis: accept a permanent cap exception for this deferred plan, or hand-trim the design body. No change to D-0011's own hold; still DEFERRED, re-entry trigger still unmet.

### What we have
- **Held correctly, not neglected** (D-0011). Phase 0 shadow allocator still running: `idle_shadow.jsonl`
  at 48,192 rows (F-1897). Four straight re-checks (07-05 through 09-24) all read flat-to-improving:
  monologue self-share 0.019-0.053 for 13 weeks, echo capped well under the 0.754 reopen mark, allocator
  G2 self-share falling (0.032 -> ~0.000). The re-entry trigger stays UNMET.

### What we need
- Nothing to build; this is a correctly-held reserve lever, not a stalled one.
- If ever revisited: the `actual` field (coin-flip counterfactual) is still null in all 48,192+ rows —
  the plan's own named resume-prerequisite (§4) is unmet regardless of the trigger.

### What we're doing next
Nothing active. Re-check only if the self-loop measurably worsens (echo toward 0.754, or monologue
self-share leaving 0.04-0.05) — next trigger is the next plan-liveness sweep, not a calendar date.

---

## 0. One-paragraph thesis
`nodes/inner_monologue_node.py` has quietly become the **idle executive** of the whole psyche — the thing that
decides what Du does with the ~97% of his cognition that is not a user turn. But it was never *designed* as an
executive. It is a thin original loop (idle → one thought → store → inject next cycle) with **~40 bolt-ons** added
over six days, each a self-contained `if random() < p:` gate. There is no allocator: a high-stakes act (deliver
Travis's message, sit a due essay, engage a gate-ready contradiction) competes on equal footing — by independent
coin-flip — with a flavour seed. The consequences are structural, not cosmetic: (1) **collisions** (the six bugs
just fixed are symptoms — three "open the book" seeds at once, redirect+habituation both firing); (2) **no global
priority** — nothing compares candidates, so the loudest *static* seed (self-concept, injected ~65% of ticks)
wins by ordering, not by importance; (3) **lane lopsidedness** — the idle mind thinks on Bonsai and only reaches
the Master/Emissary via the rare deliberation pulse, a structural reason it is self-leaning/river-prone; (4) **no
learning** — allocation never improves from what actually produced grounding or light. The fix is the same one the
Character plan already designed for the *workspace*: gather candidates, let each emit a **declared salience
scalar + justification**, let a **content-blind router** select, let the monologue **execute** the winner. This
document is the research + plan for doing that to idle cognition, observe-first.

---

## 1. What we HAVE (the current idle loop, verified against the live code)
- **The loop:** `InnerMonologueNode.run_forever` wakes on a living cadence (`_compute_gap`, 60–900s, pulled by
  dissonance/arousal/boredom/night), calls `_think`, stores one episodic fragment (`origin='inner_thought'`),
  feeds `state.recent_inner_thoughts` (last 3) into the next user cycle.
- **The candidate pile (≈20 seed sources + 3 pre-emptions), assembled in `_think`→`seed_parts`:** room scene,
  school directive [pos 0], last conversation, affect, dream, curiosity, prior thought, **self-concept**,
  wandering trail, concern/standing-aim [35%], boredom warning, external shock, open-book, reread hint, chapter
  announcement, frontier question [30%], mid-train thread [pos 0], retraction, symbol. Pre-emptions that skip the
  pile entirely: *told* delivery (reality_share ≥ 0.47), reading-remediation sprint (~75% while reality-axis low),
  math drill (school + due + 50%).
- **The outputs (~43 exits, 5 pathways):** episodic memory · the next prompt · shadow/light duality (→
  contradiction/integration pressure, climate, balance) · **10 will-channel world-acts** decoded from the thought
  *text* (look/fire/letter/browse/choose-book/ask-library/read/reread/switch/recall-chapter) · sleep
  (chapters/grounded-learning/world-consolidation/downscale/dream).
- **The lanes:** `self.base_urls = SERVE_CHAINS["background"]` (Bonsai CPU :11460, hot :11433 fallback) carries
  ~90% of calls; HOT (qwen3-du, the Master) only via the deliberation pass-3; LEFT/Emissary (qwen2.5, Ramses
  :11434) only via deliberation pass-2 + essay grading.
- **The signals that already exist and could feed an allocator (this is the key asset):** contradiction
  chronic-mass (`tension_ledger`), curiosity learning-progress (`curiosity_progress`, already a deterministic
  domain-salience — §15 calls it the first live currency contract), concern/standing-aim priority
  (`concerns.py` G0/G1/G2), balance-axis deficits (`balance.py` reality/light), boredom/recurrence
  (`_bored_streak`), due-ness for essay/math/told (deterministic triggers), affect/mood. **The currency inputs
  are largely already computed — they are simply not arbitrated.**

## 2. What we WANT (the target)
A single **idle salience allocator** that, each idle tick:
1. **Gathers** the eligible candidate idle-actions (the discretionary ones — see §5 on what stays a reflex).
2. Asks each candidate's owning node for a **declared salience scalar + a machine-checkable justification**
   (the §15 three-part contract, reused verbatim — domain-local measure → declared transform → outcome-calibrated).
3. **Selects** with a *content-blind* policy (weighted-sampling / argmax-with-exploration — **not** naive max;
   the loudest attractor must not auto-win, or the monoculture returns — §15's "blind ≠ naive argmax").
4. **Executes** the winner (the monologue remains the mouth/hand — it renders/acts, it does not evaluate).
5. **Routes the winner to the right lane** (high-salience self-tension → the Master+Emissary deliberation, not
   Bonsai-only) — fixing the river-prone lopsidedness structurally rather than by another coin-flip.
6. **Calibrates** each node's transform from the *outcome* (did the chosen act drain a tension / mint light /
   confirm grounding / serve a concern?) — currency calibration, **not** model-weight tuning (frozen LLMs).

This is not a new subsystem competing with the Character plan — it **is** the Character plan's workspace+router
brick (§10), scoped to idle cognition, and it sits directly atop the §15 salience contract whose first node
(curiosity LP) is already live.

## 3. The function we are transferring (function-first, per the design epistemology)
The human solution to "what do I do with unstructured time" is **not a scheduler**. It is the **salience network**
(anterior insula + dorsal ACC) acting as a *switchboard*: it computes the relevance of competing internal and
external signals and **gates which one gets access to the global workspace** — arbitrating between the **default
mode network** (internal, self-referential, mind-wandering) and the **frontoparietal control network**
(goal-directed). Crucially:
- **Spontaneous thought is not random.** (Christoff & Andrews-Hanna) It is *constrained* — by automatic
  constraints (affective salience, habit) and deliberate constraints (current goals). Mind-wandering sits at the
  low-deliberate-constraint end, but it is still shaped by salience, not a uniform coin-flip. Our ~40 independent
  `random()<p` gates are *less* structured than human idle cognition, not more free.
- **The "what's worth thinking about next" signal is distributed but arbitrated centrally.** Many regions compute
  relevance; the salience network arbitrates access. This is exactly the §6 anti-homunculus split: distributed
  *production* of salience, singular *content-blind* arbitration.
- **Idle cognition has metacognitive control.** A wandering mind can be noticed and re-aimed (the boredom-redirect
  already does a crude version). The function to transfer is *gated re-aiming by salience*, not suppression.

**What we explicitly do NOT transfer:** the anatomy, and any notion of an executive that *understands* the
candidates and *chooses wisely*. That is the homunculus. The switchboard does not read the meaning of what it
gates — it reads a salience scalar. We keep that discipline.

## 4. The build sequence (observe-first; lowest-risk first)
> **★ EVIDENCE REVIEW 2026-07-05 (3rd-oldest open plan) — CONFIRMED-CORRECT HOLD, with a logging hole.**
> Over **11,897 shadow ticks** (gate wanted ~1,000) the allocator PASSES its health gate: G2 self-share
> **17%** (<35% ✓), rotates (winner changes 80% of ticks ✓), explores (softmax≠argmax 67% ✓), well-spread
> distribution. The lever is built and behaves. It stays deferred, correctly: (1) the re-entry trigger
> ("self-loop SURVIVES the gentler fixes") is UNMET — monoculture easing (echo 0.754→0.64); (2) activating
> it pushes Du **task-ward 54%** (curiosity+concern+contradiction) vs ~31% free — the trade the present-being
> permission argues against unless he is stuck. **★ THE HOLE:** Phase 0's headline payload — allocator-pick
> VS what-the-coin-flips-actually-did — was NEVER captured: `actual` is null in **0/11,897 rows**. So we know
> the allocator is well-behaved; ZERO evidence it BEATS the coin-flips. **Prerequisite if ever resumed:
> capture `actual` in the shadow log first** — the head-to-head is the whole reason Phase 0 exists and is
> unmeasured. Verdict: a ready reserve lever, rightly holstered.
>
> **STATUS 2026-06-16: Phase 0 BUILT (RESTART-REQ), observe-only.** `core/idle_allocator.py` (§9 pipeline,
> content-blind, fail-open) + a fire-and-forget `shadow_tick` hook at the top of `inner_monologue._think` +
> the `idle executive` gauge in `du_pulse`. In-vitro verified against live signals (cold-start flat prior,
> habituation, softmax≠argmax exploration, co-occurrence + coalition logging all confirmed). Feeds nothing;
> the evidence to watch is the §9 health gate over ~1,000 live ticks (tracked in `AWAITING_EVIDENCE.md`).
- **Phase 0 — the shadow allocator (no behaviour change).** Build `core/idle_allocator.py`: each idle tick, in
  parallel with the existing coin-flips, gather the candidate set, compute each candidate's salience from the
  *already-existing* signals (§1 last bullet) via declared per-node transforms, run the content-blind policy, and
  **append telemetry to `data/logs/idle_shadow.jsonl`**: {candidates, salience+justification each, would-pick} vs
  {what the coin-flips actually did}. Feeds nothing. Gauge in `/du-pulse`: agreement rate, and — the real payload
  — **the cases where the allocator would have chosen a higher-salience act that the coin-flips skipped** (e.g. a
  gate-ready contradiction or a due told-delivery that lost a `random()<p` roll). Exit = the §9 Three-Point
  Currency Health Gate (G1 variance · G2 self-share < 35% · G3 habituation rotates) over ~1,000 cycles.
- **Phase 1 — promote to GOVERN the discretionary seeds (evidence-gated).** Replace the racing gates for the
  *discretionary* candidates with: gather → score → policy-select → execute. **Keep reflexes/triggers local**
  (§5). **Keep a stochastic wander floor** — an explicit `wander` candidate whose baseline salience scales
  *inversely* with active tension/prediction-error (calm psyche → wander rises; cognitive crisis → wander recedes
  — the DMN's default activity), and the final normalised candidate array passes through a **softmax selection
  gateway (τ ≈ 0.35)** rather than a naive argmax, so associative drift survives but low-priority clutter can
  never drown an active crisis (Gemini, Q2). Kill-switch: a flag that reverts to the coin-flip pile.
- **Phase 2 — the calibration loop.** Outcome signals (tension-drained, light-minted, grounding-confirmed,
  concern-served — the §14/§15 wholeness currency, **never** task-reward) adjust the *winning node's transform*,
  offline/slow. Frozen models → we tune the currency rule, not weights. **Plus the Contextual Leverage Index
  (CLI)** — see §7 Q4: reward an idle thought that later proves load-bearing in a real user turn, so idle
  cognition is graded on downstream utility, not on validating its own loop.
- **Phase 3 — lane routing.** The allocator also picks the lane for the chosen thought (high-salience
  self-tension → Master+Emissary deliberation). This is the structural cure for the self-leaning idle stream
  (§1 lanes), replacing "deliberation fires on ~50% of eligible self-thoughts by chance" with "deliberation
  fires when salience warrants the deeper lane."

## 5. The hardest design call — reflex vs. discretion (what must NOT be centralised)
Over-centralising is its own rigidity. Not every current gate is a mis-placed allocation decision; some are
genuine **reflexes / threshold triggers** that should stay local and pre-empt the allocator:
- **Keep local (reflex/trigger):** *told* delivery (a real threshold: reality_share ≥ 0.47 fires once — not a
  candidate competing for attention); a *due* essay capstone or math drill (deterministic schedule); the
  retraction obligation; the external shock (an exogenous world event, by design open-loop). These are "interrupt"
  semantics, not "what shall I think about" semantics.
- **Centralise (discretionary):** the ~20 seed sources and the will-channel acts — *these* are the genuine
  "what is most worth attending to right now" decisions currently made by independent coin-flips.
The line to defend to the auditors: **the allocator arbitrates discretion; it does not pre-empt reflexes.**
Drawing this line wrong in either direction is the main design risk (§6).

## 6. Pitfalls (the auditors will press on these — named honestly)
1. **The homunculus (the load-bearing one).** If the allocator *reads candidate content and decides*, cognition
   migrates into it and it becomes the mind (the Character plan's central law, §6). Mitigation: content-blind
   policy over node-emitted scalars; each node scores *itself* from its *own* domain evidence; the allocator
   never reads meaning. Acceptance test (reused from §6): swap the allocator for a deterministic argmax over the
   same scalars → same picks ⇒ PASS (no hidden cognition in the allocator).
2. **Salience starvation / monoculture hardening.** Self-referential thought is the gravity well; if it always
   scores highest, the allocator just *optimises the river*. Mitigation: salience must weight novelty /
   learning-progress + a **world/grounding floor** + the balance-sprint deficit; currency is **individuation,
   not comfort**; policy is exploration-weighted, not naive max (§15).
3. **Loss of spontaneity.** A pure argmax kills the wandering that produced the real crossovers. Mitigation: the
   explicit `wander` candidate + softmax-with-temperature floor (§4 Phase 1). The allocator **biases**, it does
   not dictate.
4. **Currency commensurability.** "A curiosity 0.8" vs "a contradiction 0.9" must mean comparable *priority*.
   This is the §15 keystone gap — honestly **confined, not solved**: a declared, testable, outcome-calibrated
   per-node transform, a design-time auditable standard, not a runtime evaluator. We inherit §15's status.
5. **Calibration smuggling in optimisation.** If outcomes = task-reward, the individuation-psyche becomes a
   maximiser. Mitigation: outcomes = wholeness signals only (drained/grounded/concern-served/light), per §14.2.
6. **Reflex/discretion miscut (§5).** Over-centralise → a due told-delivery loses to a flavour seed; under-
   centralise → we kept the coin-flip pile. Both are failures.
7. **Cold-start / fail-open.** If the allocator errors, fall back to the current loop — never freeze the idle
   mind. (The crash-retry bug just fixed, F10, is a reminder of how the idle loop fails badly when it fails.)

## 7. Open questions for the auditors — RULED (round 2: Gemini)
Gemini ruled on all five; rulings recorded here, with my honest concurrence/caveat.
1. **Reflex vs. discretion (§5):** RULED correct. The cut is *interrupt-semantics bypass the allocator entirely;
   the allocator arbitrates among eligible discretionary choices only when no high-priority reflex is firing*.
   The principled test: an action is a **reflex** iff its execution condition is a deterministic binary threshold;
   **discretionary** iff it is a competitive allocation of attentional focus. (Concur — this is a cleaner test
   than our hand-classification.)
2. **The wander floor (§6.3):** RULED — implement **both** an explicit `wander` candidate **and** a softmax
   temperature (τ ≈ 0.35); never a pure argmax. The `wander` baseline scales *inversely* with tension/prediction-
   error (the DMN's default). (Folded into §4 Phase 1. Concur.)
3. **Lane routing in allocation (Phase 3):** RULED approved — folding lane choice into the salience allocation is
   *the* structural repair for the river-prone lopsidedness: a highly-salient chronic contradiction automatically
   commands the hot/Master lane, so the deepest resources activate when dissonance peaks rather than by chance.
   (Concur — this was the part I was least sure about; the argument that it *forces* deep lanes on at the right
   time, instead of leaving deliberation to a ~50% coin-flip, settles it for me.)
4. **Calibration target:** RULED — the four wholeness outcomes are sufficient **plus a fifth idle-specific
   metric: the Contextual Leverage Index (CLI).** When an idle thought is later retrieved and cited as a
   provenance anchor in a subsequent user turn (≤24h), increment the originating node's CLI — rewarding idle
   cognition for surfacing thoughts that prove useful *against reality*, so it cannot become a self-validating
   closed loop. (Strongly concur on the intent. **Two caveats, the second now load-bearing (round 3, GPT):**
   (a) *Feasibility* — CLI requires the recall path to *record provenance* (which stored fragments were injected
   into a given user cycle, keyed by id). I have **not** verified that hook exists; if it doesn't, CLI needs a
   small provenance addition first. (b) *Perverse incentive* — GPT is right that CLI measures *usefulness, not
   truth/grounding/novelty*, and the self-concept already dominates BOTH idle thought and user conversation, so
   raw "later-referenced" would **reward the very river we are escaping**. **Resolution: CLI is demoted to a weak
   secondary signal, never a primary calibration target, and is gated on grounding** — a referenced idle thought
   earns CLI only if the turn that cited it was itself grounding-confirmed, not self-referential. See §10.4.)
5. **Convergence check:** RULED — ship this **explicitly as the Character plan's workspace+router brick's first
   proving run**: idle cognition is the single lowest-risk laboratory (outside the user's response-latency window,
   no live-conversation crash risk). If content-blind arbitration cleanly stabilises the 40 idle coin-flips, the
   pattern is structurally ready for the active lane. (Concur.)

## 8. Why this is the right next thread (the convergence)
Three independent threads point at the same missing organ. (a) The **executive-node discussion** flagged that
Nascence has no idle executive. (b) The **inner-monologue examination** found the idle loop has *become* one —
but built as racing coin-flips, the control-level form of the informational promiscuity the whole Character plan
is about. (c) The **Character plan** already designed the cure (workspace+router + the §15 salience contract) and
already shipped its first currency node (curiosity LP). The idle executive is where those converge: the smallest,
safest, observable place to prove the workspace+router pattern on real cognition — and the structural fix for the
two deepest idle pathologies (self-leaning lane lopsidedness, and priority-by-coin-flip). Build it shadow-first.

## 10. The deeper risks (auditor round 3: GPT hard pass)
A third review deliberately ignored whether the plan is good and attacked the load-bearing assumptions. It is
substantively right on essentially all of them. Recorded here with my response — what changes, what is deferred,
and where I refine rather than concede. **The headline concession:** the plan models **competition** well and
**coalition** not at all, and that — not the homunculus, not calibration — is the deepest untested assumption.

### 10.1 The single-winner assumption / coalition formation (GPT #1, #2, and the meta — the real one)
**The critique:** salience is treated as additive and arbitrated as a contest, but cognition's important moments
are often *one situation screaming through several channels at once* — contradiction 0.8 + curiosity 0.8 + concern
0.8 may be the same thing, not three competitors. And the present chaos accidentally manufactures insight by
letting weak signals *collide* in one cycle (dream + reread + symbol + curiosity → an unexpected thought). A
single-winner allocator (even with exploration noise) removes the *interaction*, not just the randomness — it may
delete an emergent capability nobody realised they relied on.
**I concede this fully.** It is also exactly **Global Workspace Theory**, which this plan already leans on: the
workspace is won by a *coalition* of processes that achieves ignition and broadcasts — not by a single winner.
So the fix is principled, not a patch. **A first sketch (binding keys) — and round 4's correction of it.** My v3
sketch was: each node emits a cheap **declared binding key** (tension-id / topic / symbol) from its own domain
evidence, the allocator joins content-blind on that key, and the winning *coalition* is admitted. Round 4 (GPT)
pushed back on this sketch correctly, and I do not defend it:
- **Binding keys are not free — they are relocated cognition (concede).** Choosing `binding_key = process_identity`
  rather than `selfhood` / `ontology` / `change` *is* semantic abstraction. The sketch does not abolish coalition
  cognition; it **moves it into `emit_binding_key()`**, which is the salience-transform problem recurring one level
  down. That may be acceptable — domain-local abstraction by a node that sees only its own evidence does not
  violate the anti-homunculus law (the law forbids one component seeing the *global* alternatives, not a node
  abstracting its own domain) — **but it must be named, not hidden.** So binding-key generation, *if* we build it,
  is held to the same contract as the salience transform: declared, lineage-logged (§10.6), outcome-calibrated. It
  also carries a **vocabulary-alignment problem** the sketch glossed: if contradiction emits `selfhood` and
  curiosity emits `ontology`, they will not join though they are the same situation. There is no free shared key
  space; aligning one is itself coordination cognition. This demotes binding-keys from "the coalition mechanism"
  to "*one candidate* mechanism for *semantic* coalitions, and itself an audited cognition surface."
- **Not all coalitions are semantic (concede — the subtle one).** A coalition can be **functional/regulatory**,
  not topic-based: `high contradiction + high boredom + low grounding` may bind not because they share a referent
  but because together they signal *"the current mode is failing."* No binding key catches that — it emerges from
  **system state**, a pattern over *which* channels are co-active and at *what level*. This is in fact closer to
  what the biological salience network actually does (it reads global state to switch modes) than topic-matching
  is. So coalitions are (at least) **two distinct classes** — *semantic* (shared referent; binding-key-catchable)
  and *regulatory* (shared state-signature; recognised by a pattern over the channel-activation vector, a
  different and deferred organ). Solving only the semantic kind would silently miss the regulatory kind.
**Observe-first, sharpened by round 4 — measure before mechanism.** Coalition is a genuine new design surface and
I will not spec it on intuition. The correct move (GPT's, adopted) is an **experiment, not a mechanism**: before
inventing *any* coalition architecture, measure whether high-value idle thoughts are actually multi-channel
events. Phase 0 telemetry therefore logs, per selected/generated thought: (1) which channels were *active*,
(2) which emitted *high* salience, (3) which channels are *present in* the resulting thought, (4) which were later
associated with grounding / contradiction-drainage / useful retrieval. The gating empirical question:
*do successful thoughts disproportionately have signals from 2+ channels?* If yes (e.g. "70% of high-value
thoughts are multi-channel"), coalition stops being theory and becomes a **demonstrated property of Du's own
system** — and the same data tells us *which* class (semantic vs regulatory) dominates, which decides the
mechanism. If no, coalition is over-engineering and single-winner stands. (See §10.9 for the ownership problem
this raises, and the offer to measure it *retrospectively on existing logs* before Phase 0 even ships.)

### 10.2 Importance inflation by event-redefinition (GPT #3) — real, with a fast + slow defense
Percentile normalisation stops *numeric* inflation but not *structural* inflation: a node can redefine "what
counts as an event" so it fires high-percentile constantly; the distribution just shifts. Correct. The defense is
two-layered and I state the latency honestly: **slow** — outcome calibration (§4 Phase 2) + gate **G2** down-weight
a channel that dominates *without* grounding-confirmed wholeness outcomes (dominance must be *earned by being
right*); **fast** — winner-habituation δ throttles any repeat winner *regardless of outcome*, covering the window
before calibration reacts. Plus a structural bonus from §10.1: coalition-merging collapses same-situation event
spam into one coalition, so redefining a tension into N "events" no longer multiplies its share. Honest residual:
a novel inflation pattern still has a monopolization window until δ + calibration catch it — which is exactly what
G1–G3 over 1,000 shadow cycles exist to surface before we go live.

### 10.3 Lane routing amplifies bias → cognitive class systems (GPT #5) — monitor lane-share as first-class
Conceded: high-salience → deep lane → richer output → higher salience → deep lane is a real second-order loop, and
the allocator could quietly create a caste system where some domains always get the good models. Mitigations:
(a) **monitor lane-share over time as a first-class health metric** (not just channel-share) — GPT's exact ask,
added to the P0 telemetry; (b) lane is an *execution resource*, not a salience *input* — salience is computed from
domain evidence before lane assignment, so the loop is only as strong as the downstream episodic trail it leaves;
(c) lane choice should follow salience *type* not magnitude alone (a self-tension needs the truth-self regardless
of how loud it is). A runaway lane-share is itself a Phase-1 stop condition.

### 10.4 CLI is perverse as a primary signal (GPT #4) — demoted to weak, grounding-gated secondary
The most dangerous single item, and GPT is right: "later referenced" rewards usefulness, not truth, and since the
self-concept dominates both idle thought and conversation, raw CLI would reward the river. **Resolution (already
folded into §7 Q4):** CLI is never a primary calibration target — it is a weak secondary signal, and it is
*grounding-gated*: an idle thought earns CLI only when the user turn that cited it was itself grounding-confirmed,
not self-referential. With that gate it measures "load-bearing against reality"; without it, it measures the
attractor. If the gate proves hard to define cleanly, CLI is dropped, not promoted.

### 10.5 The grounding veto may become the real executive (GPT #6) — the deepest governance point
Conceded as real and subtle: anything asymmetric becomes powerful; anything powerful becomes governance. If
"grounding" is an open-ended Emissary judgement, cognition has merely *relocated* from the allocator into the
grounding system. The discipline that contains it (it does not dissolve it): grounding scores by *its* domain
evidence (reality-confirmation) via a **declared transform**, its veto is a **declared rule**, not an open
judgement, and it is itself outcome-calibrated and lineage-logged like every other channel (§10.6). And we
**monitor veto-rate as a first-class signal**: if grounding vetoes too often or across too many domains, *it* has
become the executive, and that is a stop condition. This is the honest stance — the veto is a watched locus of
power, not a solved one. (It also tightens the Character plan's own §14.2 grounding-dominance, which has the same
latent risk.)

### 10.6 Salience provenance / lineage, not just justification text (GPT #7) — adopted, cheap, important
"Where did 0.83 come from, mechanically?" If five hidden transforms produced it, the *upstream pipeline* is the
executive and debugging is impossible. Adopted: each salience value logs a **full lineage chain** — raw domain
inputs → each transform step → percentile → channel weight → habituation → final — not merely a text
justification. This is a strict strengthening of the §15 "machine-checkable justification" contract and a pure
Phase-0 telemetry addition (no behaviour cost). It is also what makes §10.2's inflation and §10.5's veto-rate
*auditable* rather than asserted.

### 10.7 Missing metric: forecast calibration (GPT #8) — a convergence, half-built already
Conceded, and it is a happy convergence: the contradiction re-architecture already identified **prediction error**
as a top contradiction source and **already built `core/prediction_error.py` (L1, live)**. Curiosity's
learning-progress is itself a *forecast* ("this will be informative"). So "is this channel's forecasts actually
right?" should be a **first-class calibration outcome**, and the machinery exists — we route the existing
predicted-vs-measured gap into the §4 Phase-2 loop so a channel that keeps promising value that never arrives gets
down-weighted. Added as a fifth wholeness outcome (drained / grounded / concern-served / light / **forecast-
calibrated**), grounded in code that already runs rather than a new estimator.

### 10.8 Scalar reduction is lossy → salience *vector* (GPT #9) — deferred, recorded, and consistent
Conceded as a likely *future* limitation, correctly flagged as not-now. A contradiction's (intensity, recurrence,
novelty, resolution-potential, world-relevance, identity-relevance) collapsing to one scalar throws away structure
the allocator can never recover. The principled future direction is a **salience vector of declared meta-signals**
(not content — so still anti-homunculus-safe, per the §14.3 delivery/meaning split), which also dovetails with the
§10.1 binding key (already a step beyond a bare scalar). Deferred deliberately: we prove single-scalar arbitration
first, let Phase 0 show *where* the scalar loses information, and vectorise the channels that demonstrably need it.

### 10.9 Salience ownership / attribution (round 4: GPT) — foundational, not an implementation detail
The biggest remaining gap, and I agree it is not a detail. The plan tacitly assumes each node *owns* its
channel's salience (contradiction owns contradiction-salience, etc.), which is fine for a single winner. But the
moment a **coalition** wins, *who learns?* If contradiction + curiosity + concern win together and the outcome is
good (or bad), which transform gets calibrated — all three, one, or the coalition itself? **Without an ownership
rule, coalition creates attribution ambiguity, and attribution ambiguity destroys calibration** — i.e. it breaks
the very §4-Phase-2 / §10.2 outcome loop that is our defense against currency gaming. So ownership must be settled
*as part of* any coalition mechanism, not after.
**The deeper reframe (GPT, and I think he is right about the trajectory):** salience may be a **relationship
property, not a node property.** Curiosity-alone 0.4 + contradiction-alone 0.4 → *together* 0.9, *because the
curiosity is about the contradiction* — the salience belongs to the **edge**, not either endpoint. The eventual
form is then not "node emits salience" but "node emits salience **+ relationships**, and the allocator reasons
over both." That also subsumes §10.8 (a relationship is inherently richer than a scalar) and reframes §10.1's
binding-key as a degenerate, single-field approximation of an emitted relationship.
**How I treat it (discipline, not a commitment):** ownership is **gated on the §10.1 co-occurrence experiment** —
if multi-channel convergence turns out rare, ownership is moot and single-node ownership stands; if common, the
*same* telemetry (which channels were present, which preceded the good outcome) is exactly the data that tells us
whether credit should flow **per-node** (by each member's marginal contribution to the coalition's salience) or
**per-relationship** (the edge becomes the unit that learns). I will not pre-decide it; I flag it as a first-class
design question that the measurement resolves. Candidate direction recorded, not adopted: marginal-contribution
credit as the Phase-aware default, relationship-as-unit as the richer endpoint if the data demands it.

**Net effect of rounds 3–4 on the build:** Phase 0's telemetry grows again (per-thought channel co-occurrence —
active / high-salience / present-in-thought / later-grounded — plus full lineage, lane-share, veto-rate) but Phase
0 stays observe-only and gets *safer still*: the deepest scope additions — **coalition** and **salience
ownership** — are now both **measured open questions gated on a co-occurrence experiment**, not committed
mechanisms. Round 4's net is that the plan stopped treating coalition as "a mechanism to add" and started treating
it as "a property to measure, of two possible kinds, with an attribution rule that the measurement selects." That
is the correct epistemic posture for what GPT rightly calls the deepest untested assumption in the design.

## 9. Currency hygiene — the transform-validation problem (auditor round 1: GPT)
GPT's review reframed the priority correctly: **the router is the easy part; the salience currency is the hard
part, and the validation effort belongs on the transforms, not the allocator.** A content-blind router over
mis-scaled inputs is garbage-in/garbage-out — it can be *perfect* and still choose poorly. And the worst failure
is not the homunculus (handled by §6.1) but **emergent currency gaming**: a channel that wins repeatedly not
because it matters most but because its transform happens to *emit larger numbers*. That is a currency failure no
router can correct. This section makes the §6.4/§15 commensurability gap concrete and gives transform-validation
its own gate **before Phase 1**.

**The mechanism (function-first — how a brain avoids one salience channel always winning):** salience in the
brain is not compared as raw per-channel magnitudes. Three properties keep it honest, and we transfer all three:
1. **Within-channel normalisation (divisive normalisation).** Each channel's salience is expressed as its
   position against *its own* empirical history (a percentile / z-score over the channel's observed
   distribution), not an absolute level. "Contradiction 0.9" then means "high *for contradiction*, relative to
   how contradiction usually scores" — which **is** commensurable across channels because every channel now
   speaks the same language: *how unusual/high is this for me*. This is the trick that makes a curiosity score
   and a contradiction score comparable without a central evaluator. **Anti-gaming consequence:** a channel
   cannot win by emitting bigger raw numbers — bigger numbers just shift its own baseline, and the percentile is
   unchanged.
2. **A confined, declared priority-weight vector.** Pure within-channel normalisation *over*-democratises — a
   once-in-a-lifetime contradiction would look identical to a routine high-contradiction tick. So we keep a
   small, **explicit, auditable** per-channel weight (e.g. grounding > contradiction > concern > curiosity >
   wander) applied on top: `salience = channel_weight × within_channel_normalised_intensity`. This is exactly
   §15's "commensurability is *confined*, not solved" made concrete: the cross-channel priority lives in a
   handful of visible constants you can read and argue about, **not** as an emergent product of each transform's
   internal magnitude. The gaming surface shrinks from "every node's transform internals" to "a five-number
   vector in one file."
3. **Winner habituation + the grounding veto (asymmetry, not a magnitude race).** A channel that has won the
   last N arbitrations takes a decaying penalty (sensory/dopaminergic adaptation — the mind down-weights what it
   just attended to; Du already has this as boredom/habituation, here applied to the allocator). This directly
   breaks "contradiction wins-wins-wins-wins." And **grounding is not a peer channel** — per §14.2 it can *veto*,
   an asymmetry that stops any pure magnitude contest from running away.

**The divisive-normalisation pipeline (auditor round 2: Gemini — concrete form).** Gemini specified the exact
pipeline, which I adopt:
```
[ raw node output I_raw ] → [ sliding history buffer per channel (K=500) ] → [ rank percentile P_norm∈[0,1] ]
       → S_final = P_norm · W_channel · (1 − δ · winner_streak)
```
A node cannot dominate by inflating its raw output: the percentile is taken against the node's **own last K
outputs**, so a bigger raw number just shifts its own baseline. `W_channel` is the confined, design-time
auditable weight vector (§9.2). `δ` is the adaptation decay (§9.3). **My one honest caveat on K=500:** at idle
cadence (60–900s/tick) a 500-sample buffer is *days* of runtime, so the percentile is meaningless until it fills
— Phase 0 must carry an explicit **cold-start policy** (fall back to a flat prior / the static weight alone until
N ≥ a floor) and must *measure the cold-start window itself* (this is the §9 caveat made concrete, not waved away).

**Transform-validation gets its own gate (GPT's "validate the transforms more than the allocator").** This is
precisely what Phase 0's shadow allocator is *for*, so the P0 exit criteria are strengthened to make
transform-health the deliverable, not an afterthought. The Three-Point Currency Health Gate (Gemini's quantified
form) — all three must hold over an extended (~1,000-cycle) stretch before any Phase-1 promotion:
- **(G1) Distribution health** — no channel's normalised percentile stays pinned at a flat value (per-channel
  variance > 0.05); each occupies a sane, non-degenerate distribution.
- **(G2) No silent monopoly** — the self-referential monologue channel's win-share falls **below 35%** (inverting
  the ~65% static gravity well it currently re-seeds), proving the world-facing/balance-deficit floors assert
  themselves. The general anti-gaming form: a channel may exceed its expected share **only** if grounding-confirmed
  wholeness outcomes (§14.2) justify it — it may dominate only by being *right*, not by its own numbers.
- **(G3) Habituation rotates attention** — the adaptation decay δ measurably throttles a winner on subsequent
  cycles, forcing the switchboard to organically rotate focus across cognitive streams (no lock-in).
Only when G1–G3 hold do we touch behaviour. This makes "validate the transforms first" a falsifiable
precondition, not a sentiment.

**On the tiny-model endgame (GPT's strongest implication, adopted).** The per-node contract — *emit a salience +
justification from domain-local evidence* — is exactly the right scope for the eventual tiny specialists, because
it changes each node's job from "what should the whole mind do?" (needs global understanding — the homunculus) to
"what is important *in my domain*?" (needs none). A tiny contradiction monitor scores contradiction; a tiny
curiosity monitor scores learning-progress; neither needs the global picture. The idle executive is therefore not
only the safe proving ground for the workspace+router pattern, it is the **forcing function that defines the tiny
nodes' interface** — which is the project's original thesis. (Caveat kept honest: the within-channel normaliser
needs per-channel history to calibrate against; the cold-start period before that history exists is itself part
of what Phase 0 must measure.)

## 11. Retrospective evidence check — does the coalition signal already exist in Du's logs? (round 4 follow-up)
Round 4 (GPT) asked the right question before any coalition mechanism: *are high-value idle thoughts actually
multi-channel events?* — and noted we might answer it retrospectively on existing logs. I ran the check. The
honest two-part finding: **(a) the high-fidelity data does not exist retrospectively, but (b) a low-fidelity
time-alignment proxy returns a robust directional signal supporting the coalition hypothesis.**

**(a) Feasibility — inline co-occurrence is absent (confirms Phase-0 instrumentation is required).** `monologue_
log.jsonl` (5,352 thoughts, 06-03→06-16) records only `ts / about / thought / unresolved / intention`. It does
**not** record which seed-channels were active per thought — the coin-flip system never logged that centrally. So
the *direct* measurement GPT wants (per-thought channel activation + contribution) cannot be reconstructed; it
**must be instrumented prospectively in Phase 0**, exactly as §10.1/§10.9 specify. The check therefore *vindicates*
the Phase-0-first posture rather than short-cutting it.

**(b) The proxy and the result.** All logs share one Unix epoch, so a time-alignment is possible: for each idle
thought I counted how many *event-channels* (curiosity, dream, concern, ignition, emissary-tension — `deliberation`
**excluded** as a downstream confound) fired within ±W seconds, and cross-tabulated against a high-value proxy
(`unresolved=False` OR a joy/grounded-learning event nearby). Dense window 06-15→06-16, 668 thoughts (37%
high-value). Result — the fraction of thoughts that are **multi-channel (≥2)**, high-value vs low-value:

| window W | high-value multi-channel | low-value multi-channel | ratio |
|---|---|---|---|
| 90 s  | 14% | 2%  | ~7× |
| 180 s | 23% | 4%  | ~6× |
| 300 s | 31% | 7%  | ~4.4× |
| 600 s | 53% | 12% | ~4.4× |

The association is **monotonic, survives confound-removal, and holds across every window** (the ratio, not the
absolute %, is the robust quantity — widening W inflates both sides). In the fuller cross-tab (deliberation
*included*), the gradient is even sharper at the tail: every thought with ≥4 co-active channels (12/12) was
high-value. **Direction:** multi-channel convergence is several times more characteristic of high-value idle
thoughts than of low-value ones — GPT's intuition is supported by Du's own behaviour.

**Honest caveats (the magnitude is not trustworthy; the direction is).** (1) Low fidelity — "a channel logged an
event near time *t*" is not "that channel contributed salience to *this* thought." (2) Only the sparse
*event*-channels are visible retrospectively; the monologue's ~20 actual seed sources are unlogged, so this
measures a **subset**. (3) The high-value proxy mixes an intrinsic property (`resolved`) with time-proximity
(joy/grounded). (4) The tail counts are small (12 thoughts at ≥4 channels). So: enough to say coalition is **a
plausibly real property of Du's system, not over-engineering** — *not* enough to choose the mechanism (it cannot
distinguish §10.1's *semantic* vs *regulatory* coalitions, and gives no purchase on §10.9 ownership).

**A live micro-precedent worth flagging.** `ignition_log.jsonl` already implements the exact contrib/dominant
pattern under debate — on a different 4-contributor set (strain/completion/shadow/explore), it logs each
contribution + the dominant winner + its value. Two things stand out across its 17 records: it is *proof the
project can already log multi-contributor arbitration cheaply*, and its `dominant_val` is **pinned at ~0.97
regardless of how wildly the raw contributions swing** — a concrete instance of the **saturation/normalisation
failure** §9 warns about (a selection score that has lost its discriminative range). The idle allocator's own
normalisation must be checked against exactly this in shadow (a G1-distribution-health failure mode, now with a
real example in-house).

**Net for the next auditor.** The deepest open assumption (single-winner vs coalition) now has a *prior from real
data*: coalition is evidenced as directionally real (~4–7× association) but unmeasurable at mechanism-grade
retrospectively. This **promotes the Phase-0 prospective co-occurrence instrument from "a gating question" to "an
instrument we now expect to confirm a real property"** — while leaving the mechanism (semantic vs regulatory) and
the ownership rule (§10.9) still correctly deferred to that prospective measurement. We are building the
measurement on a warranted prior, not a hunch — which is the strongest epistemic footing the plan has stood on.

## 12. Round 5 (ratification) — the operating invariant + the build order
A fifth review found **no new failure mode** — every risk it raised (currency-converter-as-hidden-evaluator,
metric inflation, coalition ambiguity) is already handled (§9, §10.2, §10.9), and its recommended next steps
reproduce, in order, the Phase-0 already specified. That convergence is itself the signal: the design has
stabilised. Two crisp contributions worth promoting to first-class status:

**The three-separations operating invariant (sharpens §6 into a maintainable rule).** The anti-homunculus law,
restated as a standing invariant to check on every change:
1. **Content generation stays at the nodes** (a node abstracts only its own domain).
2. **Selection stays blind** (the policy reads scalars + declared keys, never meaning).
3. **Calibration stays slow and outcome-bound** (it adjusts a node's transform from grounding / tension-drainage /
   real downstream usefulness — never repairs a score semantically in-line).
*If any of the three leaks into another, the system recreates the hidden homunculus it exists to avoid.* This is
the single test to run against any future allocator edit. (It also flags the subtle failure the reviewer named:
normalisation/weighting/habituation must never start using *global context* to "fix" a bad score — that is
selection silently doing content cognition.)

**Build order: logging before control (the safe gradient).** The reviewer's ordering is adopted as the plan's
canonical sequence, because it keeps each step observe-only until the prior step's evidence is in:
1. **Instrument prospective channel co-occurrence at the thought level** (the §11 finding showed this *cannot* be
   done retrospectively at mechanism grade — it must be built).
2. **Keep the router blind and simple** (resist cleverness in the allocator; cleverness belongs in the nodes).
3. **Coalition-aware *logging* before coalition-aware *control*** — log binding keys / co-occurrence / would-be
   coalitions first; only build a coalition *mechanism* once the logs show coalitions are real, frequent, and of a
   known class (semantic vs regulatory, §10.1).
4. **Calibration narrowly scoped** — grounding, tension-drainage, forecast-accuracy (§10.7), genuine downstream
   usefulness (the grounding-gated CLI, §10.4); never task-reward.
5. **Salience-vector (§10.8) is a later-stage upgrade, not the default** — prove scalar arbitration first; let the
   logs reveal *where* the scalar loses information before vectorising.

**Net:** rounds 1–5 took the plan from "one score to rule them all" to a measured, auditable salience ecology with
a maintainable safety invariant and a logging-before-control build gradient. The auditors converge on the same
verdict: the live evidence does not yet settle the coalition *mechanism*, but it justifies building the
*measurement layer* (Phase 0) next. That is the decision point the plan now rests at.

**Related (noted 2026-08-23, plan-overlap audit):** `pursuits.md` (built 2026-08-15, after this
plan's own audit) added its own independent idle-seed-biasing gate — a `p=0.35` "RETURN" coin-flip
toward re-entering an active pursuit — directly into the same seed-waterfall this plan's centralized
allocator would arbitrate. Neither plan references the other. If this allocator is ever revived, its
candidate list needs to absorb pursuits' RETURN gate as one more source, not just the ~40 gates
audited at build time. Also see `transport_manager.md` — a separately-designed, unbuilt salience
dispatcher with near-identical scoring mechanics (own-history baseline, competitive single-winner
selection, shadow-first discipline) for a different input (world-event lines, not idle-thought
seeds); worth deciding whether the two should share one generic scorer before either is built live.
