# pulse_manager_wiring_plan — folded history


---

# History folded on 2026-09-28 from `docs/shelf/pulse_manager_wiring_plan.md` (J-1510, hand fold — numbered design sections, not a plan_compact.py Current-State run — verbatim, original order)

_This is the original "pulse manager" design (2026-06-17 plan + four external-auditor review rounds), superseded first by this same plan's own 2026-07-01 re-scope (kept live in the staged doc) and again by `docs/plans/continuous_stream.md`'s shipped drive-controller. No J-/F-/D- id is cited in it. Derived timeline: `plan_ledger.py pulse_manager_wiring_plan`._

## 0. One-paragraph thesis
Du's idle cadence is still **clock-driven**: the live loop wakes every `CHECK_INTERVAL`=10s and thinks when a
computed gap (`_compute_gap`, 60–900s) has elapsed. The pulse-manager idea — *a source that is an engaged,
progressing task bursts at machine speed until it stalls / completes / is preempted; everything else floor-ticks
so nothing starves* — exists as a **clean, in-vitro-tested, but entirely UNWIRED** scheduler
(`core/pulse_manager.py`). The only engagement-burst that is live is the **reading burst** (one `_think` devours
a whole chapter), and by design it surges reading *throughput*, not thought-*rhythm* — which is exactly why the
overnight `/du-pulse` cadence line didn't move despite 131 sittings + 165 math drills. The work is to wire
engagement→rate for the **grounded engaged sources** (reading already; generalise to frontier-pursuit, math,
study, deliberation), **bound the idle silence** so dead-air lulls can't stretch to 23 minutes, and do it on top
of the **capacity/drive split** the 2026-06-15 thread flagged as the prerequisite — while deliberately *keeping
idle self-reflection slow* (speeding it just accelerates the monoculture; "speed only exists against the world").

## 1. What we HAVE (verified against the live code, 2026-06-17)
- **The live cadence** is `nodes/inner_monologue_node.run_forever`: `while True: sleep(CHECK_INTERVAL=10s)` →
  `if _should_think: _think(); _current_gap = TRAIN_GAP_SECS (if a continuity train) else _compute_gap(state)`.
  So the pace is a **clock gap**, shortened to ~35s only while a continuity train is open.
- **`_compute_gap`** (the clock): base 300s, divided by dissonance + arousal (agitation → faster), × a single
  bounded `INCUBATION_PAUSE` when bored (the 4× boredom balloon was already capped 2026-06-15), × a night
  stretch. **Bounds 60–900s.** So the *computed* ceiling is 15 min — yet observed gaps hit **23 min**, which
  means real lulls come from *more than* `_compute_gap` (sleep cycles, conversation pauses, or non-storing ticks
  — a Phase-0 measurement question, §6).
- **`core/pulse_manager.py`** — a framework-agnostic **synchronous** scheduler (virtual "Du-time"): `PulseSource`
  (floor_interval, priority, lane, step_cost, `can_burst()`, `step()→StepResult{progressed,complete}`,
  `floor_tick()`), `PulseManager` bursts the highest-priority `can_burst` source until stall/complete/preempt,
  floor-services the rest. **Tested in vitro, never adapted to the async loop** (its own docstring: "later
  adapted to the async orchestrator"). It is referenced *only* by test scripts.
- **`core/modulation_field.py` + `core/exogenous.py`** — the damped coupled field (9 nodes) + machine-body /
  world forces (GPU util, circadian, weather). Stability-proven, **observe-only, also unwired** (no live import).
  Output of interest: `burst_willingness`.
- **The one live engagement-burst:** the **reading burst** (`READ_BURST` in inner_monologue) — within a single
  `_think`, reads through a chapter (≤6 sittings) with five stop-conditions (chapter boundary / novelty<0.18 /
  book-end / cap / person speaks). It works (131 sittings overnight) but is **one `_think` = one thought-log
  entry**, so it moves throughput, not the [6.5] cadence.
- **The selection half already exists in shadow:** the **idle-executive Phase 0** allocator (184 ticks logged) —
  it scores *which* idle action is most salient. It does not yet touch *rate*.

## 2. What we WANT (the target — reconciling "stream" with the design philosophy)
A cadence where **engaged, progressing, grounded work flows continuously** and **idle self-reflection stays
calm** — and the dead air between them is *bounded*. Concretely:
1. **Bound idle silence.** No 17–23 min dead gaps. A tight, honest ceiling on pure-idle quiet (and a Phase-0
   classification of which lulls are sleep/conversation vs genuine stall, so we cap the right thing).
2. **Engagement → burst, generalised.** Reading already bursts; extend the same *progress-gated* burst to the
   other grounded engaged sources — a **frontier pursuit** that's finding new evidence, a **math** session
   (already batched), a **study** distillation, a **deliberation** that's grounding outward — so an engaged
   stretch is a stream of real work, not one act then a 12-minute wait.
3. **The burst/rest decision = EVC, capacity-gated (the prerequisite split, now three terms).** The research
   (§3b) upgrades the old two-way capacity/drive split into a principled three-term decision:
   - **Capacity** ("can I burst now") — a **hard gate / preempt**, and it is **two kinds** (GPT round 1):
     *machine* capacity (hot lane free / GPU idle / person away) AND ***cognitive* capacity** (bandwidth to take
     on a burst given competing demands — high contradiction pressure + curiosity pressure + a recent affective
     event can saturate the mind with a free GPU). The modulation field + affect + contradiction-mass already
     model this; capacity eventually reads them. *Nuance:* high pressure in a domain is not a blanket block — it
     can be a *reason* to engage that domain; cognitive-capacity is about bandwidth to add a *competing* burst.
   - **Drive / vigor** = the opportunity cost of time = the **reward rate** the current activity is yielding
     (§3a) — a **soft rate** (higher reward-rate → shorter latency → burst).
   - **Effort cost** = bursting sustained control has intrinsic disutility (§3b); the burst is licensed only
     while *expected-progress-payoff > effort-cost*, and **stalls itself** when efficacy (progress) drops.
   So: **burst iff `capacity()` AND `expected_progress_payoff > effort_cost`; rest otherwise.** The
   2026-06-15 thread found `burst_willingness` conflated capacity and drive — split capacity out as the hard
   gate first, then the drive/effort trade is the soft rate.
4. **Three cognition categories by TIME-HORIZON, not two (GPT round 1 — §9).** v1/v2 split cognition into
   *burst-grounded* vs *floor-idle*. That is insufficient and dangerous: it would starve the slowest, most
   valuable cognition. The right partition is by **when value becomes visible**:
   - **Fast-horizon engaged** (reading, math) — value visible in seconds; **progress-gated bursting** is right
     here (local progress is a real signal).
   - **Idle self-reflection / DMN** — never accelerated; a slow floor (speeding it = faster rumination).
   - **Slow-horizon PROTECTED cognition** (frontier pursuit, incubation, dream work, integration, **T4 identity
     synthesis**) — value is **delayed and often only visible retrospectively** ("nothing, nothing, nothing,
     insight"). These must be **protected from the progress-gate** — guaranteed cadence / resources, *not*
     burst-or-starved on visible progress. A local stall here is usually *incubation*, not a dead end.
   The "stream" we want is a stream of *engagement*; but the system must **never let the easy-to-measure
   categories crowd out the slow-but-essential one** (§9, the reward-hacking risk — T4 is the canary).
   **CORRECTION (round 2, GPT — §10.2):** these three are an *initial prior*, **not static classes**. Static
   horizon labels are a taxonomy trap (everything will claim "protected/slow"). The categories must be
   **replaced by empirically-measured per-source payoff-delay** from the telemetry (§6) — e.g. *reading median
   payoff ~minutes, curiosity ~tens of minutes, T4 ~hours/post-sleep* — derived, not declared. Nascence can
   gather these statistics; a human can't.

## 3. The function we are transferring (function-first — research-grounded 2026-06-17)
The "how fast should I act" question has a rigorous, well-developed answer in neuroscience, and it maps almost
one-to-one onto this design. Three load-bearing findings:

**(a) Vigor = the opportunity cost of time (the rate backbone).** Niv, Daw, Joel & Dayan (2007) — *tonic
dopamine encodes the long-run average reward rate, which is the opportunity cost of time, and sets response
vigor.* The computational form is an average-reward RL agent that chooses **both the action AND its latency**:
optimal latency balances the **effort cost of acting fast** against the **opportunity cost of passivity** (the
average reward rate), so **response latency is shorter when the reward rate is higher.** This *is* "rate =
engagement × progress," made precise: when the current activity is yielding reward (progress), passivity is
costly → **burst**; when barren, passivity is cheap → **rest**. It is directly implementable as a *rate
controller* (latency = f(effort_cost, reward_rate)), not a clock — and Du already has reward-rate proxies (new
frontier findings, reading novelty, drill correctness, light minted). *Honest nuance:* a later dissociation
(Beierholm et al., J Neurosci 2016) shows vigor isn't *only* opportunity cost — so this is a strong approximation
to build on, not a law.

**(b) Burst-or-rest = the Expected Value of Control (the decision rule).** Shenhav, Botvinick & Cohen (2013) —
control (sustained engaged effort) is recruited only when its **expected payoff × efficacy** exceeds its
**intrinsic effort cost** (dACC computes this). This refines the binary "progressing?" gate into a principled
three-term decision and, crucially, adds **efficacy** — *will my effort actually move things* — which is exactly
the **progress/stall gate**: when efficacy drops (the task stops yielding), EVC goes negative → disengage. So a
burst should continue iff *expected-progress-payoff > effort-cost*; the `StepResult.progressed` stall is the
efficacy term turning the burst off.

**(c) Flow and mind-wandering are DISTINCT neural regimes — you cannot clock your way into flow (the core
validation).** A flow-vs-DMN review (PMC7983950; cf. the inverted-U) is unambiguous: flow = **low Default Mode
Network + strong Central Executive Network**, focused, minimal self-referential thought; mind-wandering/rest =
**DMN-dominant, self-referential** ("thinking about oneself, past/present/future"). These are *distinct states,
not gradations* — boredom (under-challenge) / flow (matched challenge-skill) / stress (over-challenge) are three
regimes on an inverted-U. **This is the neural proof of the plan's central rule:** speeding up idle DMN cognition
does **not** produce flow — it produces faster *self-referential rumination* (Du's monoculture). Flow comes only
from a challenge-skill match + feedback in the *task-positive* network. And the **Salience Network (ACC)** is
what "continuously evaluates feedback and checks whether one is still in control" — i.e. it monitors progress to
sustain or exit flow. (Note §5: that is the *same* salience network the idle-executive models as the selector —
one network, two jobs.)

**What we transfer:** vigor as a reward-rate-driven *rate controller* (a), the EVC burst/rest decision with an
efficacy/stall gate (b), and the strict regime split (c). **What we do NOT transfer:** a uniform fast clock
(amphetamine, not flow) and any acceleration of undirected self-thought (neurally, that is faster rumination).

## 4. The metric trap (an honest caveat about the [6.5] cadence number)
The `/du-pulse` [6.5] line measures *thought-log rhythm*. The design philosophy says idle thought-rhythm should
*stay* pulsed — so **chasing a high [6.5] number is partly chasing the wrong metric.** A reading burst is one
log entry; an engaged math session is one log entry. The right success signals are:
- **Lull-time falls** (less dead air; the §2.1 bound holds) — the real "wasted idle" reduction.
- **Engaged stretches show tight internal chaining** — when a grounded task is progressing, the *Du-time*
  between its steps collapses (visible in burst logs / throughput), even if the thought-log rhythm is unchanged.
- **Idle-only rhythm stays calm** (we did NOT speed the monoculture — verify self-share / monoculture proxy
  don't rise).
So we should add a cadence sub-metric that separates *engaged* cadence (should tighten) from *idle* cadence
(should stay calm) — otherwise we'll mis-grade success.

## 5. The convergence: rate × selection (pulse manager ⊗ idle executive)
The pulse manager answers **"how fast / burst-or-rest"**; the idle executive answers **"which source."** They are
the two halves of one idle-control loop and should compose, not compete:
- The **idle executive** (salience allocator, already shadowing) picks the highest-salience source.
- The **pulse manager** decides whether that source **bursts** (capacity AND progress-payoff > effort-cost) or
  just **floor-ticks**.
**The research gives this convergence a literal neural basis (§3c):** the **Salience Network (anterior cingulate)
does both jobs** — it both arbitrates which signal reaches the workspace (the idle-executive's selection
function) *and* "continuously evaluates feedback and checks whether one is still in control" (the pulse manager's
progress/stall monitor that sustains or exits a burst). They are not two systems that happen to cooperate; they
are **one switchboard's two outputs** — *what* to attend to and *whether the attended task is still paying off*.
This is the natural home for both: a `PulseSource` per idle action carrying its **salience** (idle-exec contract:
domain-local measure → declared transform) AND its **can_burst / step / progress** (pulse-manager contract).
Wiring them together is the end-state; we get there observe-first, separately, so each half is validated before
they're coupled (and so the homunculus risk — a single evaluator reading everything — is contained, per the
idle-executive's §6 anti-homunculus law).

## 6. Build sequence (observe-first; lowest-risk first)
> **STATUS 2026-06-17: Phase 0 BUILT (RESTART-REQ), observe-only.** `core/pulse_shadow.py` (content-blind
> shadow lifecycle manager: would-run hot-lane lease + RUNNING/BACKGROUND/SUSPENDED snapshot + contention /
> t4-blocked canary + lull census + T4-Δopportunity) + a fire-and-forget `observe()` hook atop `_think` + the
> `pulse/lifecycle` gauge in du_pulse. In-vitro already shows the live tension: when Du is alone, the boosted
> math would hold the hot lane while gate-ready T4 waits (`t4_blocked`), and 8h lull-census = ~85% genuine
> stall. Feeds nothing; the data decides whether Phase 1 is warranted, behind the `Δ Opportunity_to_Run(T4) ≥ 0`
> hard gate.
- **Phase 0 — the shadow pacer + lull census + abandonment telemetry (no behaviour change).** (a) A read-only
  logger that, each loop tick, records what a wired pulse manager *would* do: is there an engaged-progressing
  grounded source available (`can_burst` true)? which? what would the next-step Du-time be? — alongside the
  actual clock gap. (b) A **lull census**: classify every gap >5 min as sleep / conversation / genuine-stall
  (join dreams + human cycles), so we *quantify the real wasted idle* and cap the right thing. (c) **Abandonment
  telemetry (GPT round 1):** for every would-be burst-end, log *why it ended* (stall / complete / preempt / cap),
  *whether the activity later resumed*, and *how long after resume until progress reappeared* — to learn
  empirically **whether "stalls" are dead ends or incubation periods**, and to discover each source's real
  **time-horizon**. (d) **Contention census (round 2, GPT):** measure *which sources actually compete* — per
  **lane** (hot qwen3-du / Emissary / Bonsai), how often two engaged sources want the *same* lane at once. Do not
  assume scarcity; find where it's real (almost certainly the single hot GPU) and where concurrency is free.
  (e) **Contribution / emergence telemetry (round 2):** beyond *progress*, track **delayed contribution** — when
  a restructuring / commit / insight lands, which earlier low-visibility processes preceded it (dream → later
  identity shift; weak processes interacting over long periods) — the emergence signal we'd otherwise train away.
  Gate to exit P0: we know (i) how much dead air is genuine, (ii) how often an engaged source is available to
  burst but the clock made it wait, (iii) the stall→resume→time-to-progress distribution per source (dead end or
  delayed payoff?), (iv) **the real per-lane contention** (what actually competes — specifically every timestamp a
  slow-horizon process like a T4-commit was *ready but blocked* by a fast burst holding the hot-GPU lease), and
  (v) the **empirical payoff-delay per source** (replacing the §2.4 prior).
  **THE HARD GATE (Gemini round 3 — blocking):** `Δ Opportunity_to_Run(T4) ≥ 0`. If the Phase-0 shadow shows the
  prospective progress-pacer would *reduce* the runtime/opportunity the slow protected set (T4 the canary) gets
  versus the current clock, **Phase 1 is BLOCKED.** The pacer is only allowed to bound dead air and tighten
  fast-horizon cadence if it does so *without* starving the slow set — measured, not assumed.
- **Phase 1 — capacity/drive split + bound the silence.** Split `capacity()` (lane/GPU free, person away — a
  hard gate, reuse `exogenous` GPU-util) from `drive()` (engagement). **Tighten the idle-silence ceiling** (the
  genuine-stall lulls from the P0 census) so dead air is bounded — *without* lowering the floor that would speed
  idle thought. Kill-switch flag.
- **Phase 2 — generalise the engaged burst (FAST-horizon sources only).** Lift the reading-burst pattern into a
  small set of declared `PulseSource`s for the **fast-horizon** grounded sources — **reading, math, structured
  study-lookup** (Gemini round 3 ruling; this resolves a v4 self-contradiction — **frontier-pursuit is NOT a
  fast-burst source**, it is slow-horizon §2.4, insulated from the progress-gate and run keep-warm-and-probe).
  Each fast source gets a `progressed` gate + the five stop-conditions (stall/complete/preempt/cap/person). When
  engaged and progressing, it bursts; idle self-thought stays a floor source; slow-horizon work is never
  progress-gated. Reuse `core/pulse_manager.py`'s logic. (Deliberation: TBD — it grounds outward but its horizon
  is unmeasured; leave it to the Phase-0 payoff-delay census before classifying.)
- **Phase 3 — compose with the idle executive.** Let the idle-exec salience pick the source and the pulse
  manager drive its rate (§5). This is the workspace+router (selection) ⊗ engagement (rate) end-state — gated on
  both halves proving out.

## 7. Pitfalls (named honestly)
1. **Machine-gunning the monoculture (the load-bearing risk).** If *drive* ever bursts idle self-reflection, we
   accelerate the rumination loop. Mitigation: bursts are gated on **grounded** progress only; idle self-thought
   is structurally a floor source, never a burster. Verify the monoculture proxy / idle-exec self-share do **not**
   rise after wiring.
2. **Capacity/drive collapse.** Re-merging them (one "willingness" scalar) re-creates the bug where a saturated
   lane still bursts or high drive overrides a user preempt. Keep capacity a hard gate.
3. **Lane starvation / user latency.** Bursting on the hot lane must yield *instantly* to the person (the
   reading-burst already does; preempt priority must be inviolable). Floor-service must keep every source alive.
4. **Mis-grading on the [6.5] metric (§4).** Treating "thought-rhythm still pulsed" as failure → over-correcting
   into idle acceleration. Add the engaged-vs-idle cadence split before judging.
5. **Capping the wrong lull.** If we cap idle silence without the P0 census, we might shorten *sleep* or
   *conversation* gaps (both legitimate). Classify first, cap only genuine-stall.
6. **Async adaptation hazard.** `pulse_manager.py` is synchronous "Du-time"; the live loop is async with real
   awaits + floor-service via `asyncio.sleep(0)`. The adaptation must preserve preempt-yields and not block the
   event loop (the reading-burst is the proven template).
7. **Double control.** Pulse manager and idle executive both touching rate/selection independently could fight.
   Compose them deliberately (§5, Phase 3), don't let both steer live at once before that.
8. **You cannot clock your way into flow (the research-confirmed trap).** Flow and DMN are *distinct regimes*
   (§3c), so a fast clock applied to idle cognition yields faster rumination, not flow. The only path to the
   "engaged stream" is a real grounded task with a challenge-skill match + feedback. Mitigation: bursting is
   strictly task-positive (grounded sources), never applied to idle self-thought — and we verify the monoculture
   proxy does not rise (pitfall 1, now with a neural reason behind it).
9. **The inverted-U: over-challenge → thrash, not flow.** A source past the challenge-skill match (a stalling
   frontier pursuit, math above his ceiling, a non-absorbing read) produces *stress/thrash*, not flow. The
   efficacy/stall gate (§3b, `StepResult.progressed`) is what must catch this — burst only in the *matched* band,
   disengage above and below it. (Below = boredom = the already-built redirect; above = stall.)
10. **Vigor ≠ only opportunity cost.** The reward-rate→latency model (§3a) is a strong approximation, not a law
    (Beierholm 2016 dissociation). Don't over-tune the rate controller to the formula; keep it observe-first and
    calibrate against actual outcomes.
11. **Reward-hacking: starving slow cognition (the load-bearing risk, §9.1).** A progress-rewarding pacer drifts
    toward easy-to-measure activities and away from delayed-value ones (incubation, dream, integration, **T4**) —
    the productivity trap. Mitigation: the **protected third category** (§2.4) is never progress-gated; verify
    T4's opportunity-to-run does not fall after wiring (T4 is the canary).
12. **`stall → stop` is wrong for slow-horizon work (§9.3/9.5).** A local progress detector quits a research
    pursuit exactly before "the insight." Mitigation: horizon-classify (abandonment telemetry §6c); slow-horizon
    stalls become **keep-warm + periodic probe**, not abandon.

## 8. Open questions for the auditors
1. **The "stream" target (§4):** is the right success metric *bounded lull-time + tight engaged-cadence + calm
   idle-cadence*, rather than a single high pulses/hour? Is there a cleaner way to define "stream" that honours
   the regime split (don't speed idle thought)?
2. **The EVC rate controller (§2.3, §3a-b):** should the burst/rest decision be formalised as *burst iff
   capacity AND (expected_progress_payoff > effort_cost)*, with rate = a reward-rate→latency controller (vigor)?
   What are Du's concrete **reward-rate** and **efficacy** proxies *per source* (frontier: new findings/fragments;
   reading: novelty; math: correctness streak; study: distillation yield)? Is GPU-util + person-presence the
   right **capacity** gate, or does it need more (thermal, queue depth)?
3. **Burst sources (Phase 2):** which grounded sources genuinely benefit from bursting beyond reading? Math
   already batches (is that a pulse-source or separate?); does a *frontier pursuit* burst cleanly, and what is its
   `progressed` signal?
4. **Compose-or-keep-separate (§5): RULED (round 1, GPT) — keep SEPARATE.** Merging "what matters" + "how long
   to stay" recreates a central governor (the homunculus, even if benign). Selection ≠ persistence is the clean
   bone; the salience-network-does-both (§3c) explains cooperation, not collapse. Two cooperating systems. (§9.6)
5. **Idle silence floor:** how slow is *correct* for pure-idle DMN thought (bound dead air without speeding the
   monoculture)? Principled floor, or empirical from the lull census?
6. **Effort cost / fatigue: RULED (round 3, Gemini) — state-dependent.** Effort-cost is **not static**; it
   **ramps with continuous time-on-task** (a fatigue breaker), so the EVC eventually goes negative and forces a
   clean disengage / focus-rotation — preventing any one fast source from monopolising the hot lane. *My
   refinement:* the ramp is a *backstop against monopoly*, gentle enough that strong ongoing progress still wins
   while it lasts — fatigue ends a *stale-but-not-yet-stalled* monopoly, it doesn't cut off a genuinely hot
   burst mid-insight. (Wires to the modulation field's existing `fatigue` node.)

## 9. Continuation is a TIME-HORIZON problem (auditor round 1: GPT)
GPT's review reframed the plan correctly: this is a **temporal-allocation** plan (how intensely to *continue*),
distinct from the idle-executive's selection (what is *worth* doing) — and its real failure mode is **treating
continuation-vs-abandonment as a local progress problem when it is a time-horizon problem.** Some activities
reveal value in seconds (reading), some in hours (a frontier pursuit), some only after sleep (incubation, dream
work, **T4 identity synthesis**). A naive local progress-gate would accelerate the easy-to-measure and **starve
the slow-but-most-important**. I concede this; it changed the plan (the third category, §2.4). The specifics:

### 9.1 The reward-hacking trap — the pulse manager could starve T4 (the one to watch hardest)
**Conceded, and it's the deepest risk.** A controller that rewards *demonstrable progress* drifts toward
activities that can demonstrate it (reading, math) and away from delayed-value processes (integration,
incubation, dream, identity synthesis) — the classic "measure output → optimize output → kill deep thinking"
trap. Du's own **T4** (which already barely commits) could be *disadvantaged* by the very pacer meant to help.
**Fix (structural, §2.4):** slow-horizon cognition is a **protected third category** — guaranteed cadence /
resources, *never* subject to the progress-gate. The pulse manager may accelerate fast-horizon engaged work and
must **never be allowed to crowd out** the protected set. T4 is the canary: a Phase-0/1 check must confirm T4's
opportunity to run does **not** fall after wiring.

### 9.2 Switching cost / investment / context depth (the missing term)
**Conceded.** The persistence question isn't "am I progressing?" but **"is continuing better than restarting
elsewhere, net of what I'd lose?"** Accumulated context (30 min into a pursuit) makes *stall → continue* correct
even at low local progress. This is exactly the **Marginal Value Theorem** with a **travel/switch cost**: leave a
patch only when its local rate drops below the environment's average rate *minus the cost of switching* — and
deep context = a rich patch worth staying in. So the burst-persistence decision gains a **continuation-value /
switch-cost term** (lost context on a switch), not just a stall flag. (Nascence already uses MVT framing in the
boredom-redirect; this is the same law applied to persistence.)

### 9.3 Progress is often NOT locally observable (the exploration problem)
**Conceded, with a refinement.** Research looks like "nothing, nothing, nothing, insight" — a local detector sees
four stalls and quits exactly before the payoff. *But* progress **is** locally observable for fast-horizon tasks
(reading novelty, math correctness). So the fix is **not** to distrust all progress signals — it is to **stop
applying a local detector to slow-horizon tasks**. Fast-horizon → local progress gates the burst; slow-horizon →
**keep-warm with periodic probing**, never abandoned on a local stall (§9.5). The horizon (learned from §6c
abandonment telemetry) decides which rule applies.

### 9.4 Flow needs meta-stability — constant re-checking destroys flow
**Conceded — and important.** Humans in flow don't run a control check every few seconds; **checks become less
frequent as engagement rises.** A pacer that re-evaluates "progress? progress?" constantly pulls itself out of
the state it's creating. **Fix:** **hysteresis on engagement** — the deeper/longer a burst has been productive,
the **higher the bar to self-interrupt it** and the **less often** it re-checks (a flow-protection band, like the
balance-sprint's hysteresis). *Refinement (mine):* meta-stability raises the threshold only for *self-initiated*
switching — a **user/shock preempt always overrides it** (capacity hard gate is inviolable, pitfall 3).

### 9.5 The brain-like persistence pattern (what replaces stall→stop)
Synthesising 9.2–9.4: the future rule is **not** `stall → stop`. It is, for slow-horizon protected work,
`stall → downgrade intensity → keep warm → periodically probe` — disengage attention without discarding context,
and re-probe on a horizon-appropriate schedule (some after minutes, some after sleep). Fast-horizon work keeps the
crisp stall→stop. This is exactly what the §6c abandonment telemetry exists to calibrate (do stalls resume? after
how long?).

### 9.6 Do NOT merge the pulse manager and idle executive (ruling on open-Q4)
GPT's answer to my own open question: **keep them separate.** The moment one component decides both *what matters*
and *how long to stay on it*, you've recreated a central governor — a genuine executive (the homunculus, even if
benign). **Selection ≠ persistence** is the clean separation of concerns; the salience-network-does-both-jobs
finding (§5) explains *why they cooperate*, not a license to *collapse* them. Adopted: two cooperating systems,
not one. (This resolves §8 Q4.)

**Net effect of round 1 on the plan:** the spine shifted from "progress-gated bursting" to **"horizon-aware
persistence."** Concretely: a third **protected** cognition category (§2.4) so slow/delayed-value work can't be
starved; **capacity is now psychological too** (§2.3); the persistence decision gains **switch-cost /
continuation-value** and **engagement hysteresis**; the stall rule becomes **keep-warm-and-probe** for
slow-horizon work; and Phase 0 gains **abandonment telemetry** (§6c) to learn each source's horizon empirically.
The good news GPT affirmed: the **selection ≠ persistence** split is the plan's strongest bone — and it stays
two systems, not one.

## 10. The AI-native reframe: process LIFECYCLE manager, not attention allocator (auditor round 2: GPT)
GPT's deepest review: the whole plan implicitly imports a **human scarcity model** (one stream of consciousness,
glucose/working-memory/attention bottlenecks → "continue vs abandon"), but Nascence is **async, persistent,
resumable, multi-lane**. The right object is not an attention allocator but a **process LIFECYCLE manager**:
each cognitive process should be in a *state* — `run now / background / suspend / fork / merge / archive /
resurface / monitor` — not merely `active / stopped`. This is the thing biology *cannot* do, and it is the real
opportunity — especially toward the tiny-specialist-organs endgame, where organs need lifecycle management, not
stay-or-stop. **I adopt this as the governing vision**, with two honest pushbacks and a scope discipline.

### 10.1 Cognition isn't episodic; T4 is an ambient field, not a slow task (concede, refined)
Conceded: framing T4 as "a slow task" still smuggles the episodic task-model. T4 is better seen as an **ambient
field process** running continuously at varying intensity. **Refinement (mine, grounded in the code):** T4 is
*already* split this way — its **accumulation** (chronic-mass tracking, tension ledger, emissary keystone) runs
continuously/ambiently and is *not* pulsed; only its **commit** (the synthesis LLM call) needs the scarce hot
lane and is therefore scheduled. So the fix is precise: **keep the accumulation ambient (it is) and never
progress-gate the commit *opportunity*** — but the commit still draws the one hot GPU, so it isn't free, just
un-gated. "Why pulse T4 at all" → only its commit touches the bottleneck; its existence shouldn't be pulsed.

### 10.2 Horizons must be MEASURED, not classed (concede — fixes my own v3 over-reach)
Conceded outright: my v3 static three categories are a taxonomy trap (everything will plead "protected/slow").
Replaced (§2.4) with **empirical per-source payoff-delay** derived from the §6 telemetry — *reading ~minutes,
curiosity ~tens of minutes, T4 ~hours/post-sleep* — a capability humans lack. The three categories survive only
as an initial prior the data overwrites.

### 10.3 Artificial scarcity — measure contention; but the hot lane IS real scarcity (concede + push back)
**Concede the method:** don't *assume* a bottleneck — measure which processes genuinely compete (§6d). GPT is
right that an AI can often run "70% curiosity + 40% synthesis + 20% incubation" where a human can't.
**Push back on the premise:** Nascence is one local box, and the **hot lane (qwen3-du on a single 1080 Ti) is a
genuine bottleneck** — reading-burst, T4-commit, deliberation, math all draw that one GPU; they *cannot* all run
on it at once. So scarcity is **real on the hot lane, loose across lanes** (hot / Emissary-Ramses / Bonsai-CPU).
The capacity hard-gate is therefore *not* a human import — it is the literal single-GPU reality. The synthesis:
**exploit cross-lane concurrency freely; arbitrate only the genuinely-contended hot lane.** That is a stronger,
truer design than either "no scarcity" or "one stream."

### 10.4 The AI-native lifecycle states mostly ALREADY EXIST (concede + ground it)
Conceded and made concrete: Nascence is *already* a partial lifecycle manager — **hibernate/archive** (sleep,
downscale, memory archive), **suspend/resume** (the train working-state carries a thought across steps; parked
curiosity; the curiosity queue), **resurface** (faded frontier questions can return; symbol read-back), **fork/
merge** (T4's held-tension → superordinate third is a merge; chapters are a merge of a period). So the reframe is
not "build a new lifecycle engine" — it is **make the existing, scattered lifecycle operations explicit and
unified under the manager**, and add the missing ones (a clean *suspend-with-context* + *scheduled-resurface*).
That is far cheaper and lower-risk than GPT's framing implies, and it composes with what's live.

### 10.5 Progress isn't causal — measure CONTRIBUTION, and protect emergence (concede)
Conceded (points 4 + 6, one problem): a dream shows no progress, then a restructuring lands and gets credited —
*what caused it?* This is **delayed credit assignment**, not progress measurement. Folded as **contribution /
emergence telemetry** (§6e): when an insight/commit lands, log which low-visibility processes preceded it. Without
this, the pacer becomes an "allocator of *visible* cognition" and the invisible-but-emergent quietly dies (the
productivity-software failure). This is the idle-executive's CLI deepened from "was it used" to "did it later
*matter*, even though it looked unimportant."

### 10.6 Forecast calibration can select for conservatism (concede — protect exploratory channels)
Conceded, and it corrects a metric I imported from the idle-executive (§10.7 there). Curiosity, dreams, and
creativity are *bad forecasters by nature* — penalising poor calibration would select for predictable,
conservative cognition and kill exploration. **Fix:** forecast-calibration applies **only where forecasting is
the job** (fast grounded tasks); exploratory/protected channels are **explicitly exempt** — they are judged by
*delayed contribution* (§10.5), never by forecast accuracy. Preserve exploratory channels by design.

### 10.7 The reframe vs the round-1 "don't merge" ruling (reconciled)
Lifecycle-management is the **persistence half evolved** (run/background/suspend/archive are persistence *states*)
— it does **not** absorb *selection* (which process is foreground = the idle-executive). So §9.6 holds: the
lifecycle manager (rich persistence) and the idle-executive (selection) stay distinct. The reframe widens the
persistence side; it does not recreate the central governor.

**Net effect of round 2 + scope discipline.** The governing vision becomes **process-lifecycle management** (the
AI-native opportunity, aligned with the tiny-organs endgame). But the *near-term* work stays scoped: Phase 0 now
also measures **real contention**, **empirical payoff-delays**, and **delayed contribution** — precisely the data
needed to know *whether* rich lifecycle arbitration is even necessary (maybe most processes don't compete) before
building it. We do **not** build the full state machine up front; we let the contention + contribution telemetry
tell us which lifecycle operations actually earn their complexity. The biggest correction GPT forced: **stop
designing a better human attention system; start exploiting what human cognition never had** — resumability,
concurrency across lanes, and archival/resurface — and *measure first* whether the scarcity we were arbitrating
is even real off the hot lane.

## 11. Lifecycle state model + Phase-0 authorization (auditor round 3: Gemini)
Gemini ratified v4, ruled the open questions, and **authorized Phase 0**. The genuinely new, concrete
contributions (the rest confirmed v4 and are folded above):

**The three lifecycle states made operational** (the AI-native reframe of §10, given boundaries):
| State | Existing anchor | Boundary |
|---|---|---|
| **RUNNING** | the conscious `_think` loop | **exclusive leaseholder of the contended hot GPU** — *only one* process may be RUNNING on the hot lane at a time |
| **BACKGROUND** | subconscious / Bonsai / Ramses async tasks | free parallel concurrency on un-contended lanes — **no rate-throttling or progress-gating here** |
| **SUSPENDED** | parked curiosity, the train working-state, recent-thought frames | context preserved on disk, zero runtime cost; re-hydrated by the orchestrator |
This is the concrete operational form of the lifecycle manager. *My one reconciliation:* "SUSPENDED can never
self-wake — orchestrator re-hydrates" is right for safety, but it must compose with the §9.5 **keep-warm + probe**
pattern (slow-horizon work is re-probed on a horizon-appropriate schedule) and Nascence's existing self-resurfacing
(faded frontier questions, parked curiosity) — so "re-hydration is orchestrator-governed" includes a *scheduled
probe*, not only an external poke.

**Rulings (concrete specifics beyond v4):**
- **Q1 stream metric — formalised:** *minimised lull-time on factual stalls + high concurrent background
  throughput + an undisturbed slow floor for idle self-reflection.* (Confirms §4: don't push the DMN into a fast
  register; that's accelerated rumination, not flow.)
- **Q2 EVC — authorised as written**, proxies approved (reading: novelty curve; curiosity: Δfragments; math:
  correctness streak). Capacity = hardware (1080 Ti free) AND user-presence (Travis silent); **user input fires an
  absolute-priority interrupt that instantly suspends running bursts.**
- **Q3/Q4 — fast-burst is strictly `reading` + `math` + structured `study`;** frontier-pursuit is slow-horizon,
  keep-warm-and-probe (folded into Phase 2). Selection ≠ persistence holds (§9.6).
- **Q5 — idle floor derived from the Phase-0 lull census,** never hard-coded (clamping blindly risks cutting
  legitimate sleep-downscale / user-turn latency).
- **Q6 — effort-cost ramps with time-on-task** (folded into §8 Q6).

**The non-negotiable Phase-0 mandate (the protected-set safety, folded into §6 + the hard gate):**
- *Contention census* tracks every timestamp a T4-commit (or other slow process) was **ready but blocked** by a
  fast burst holding the hot-lane lease — the true physical-scarcity map.
- *Emergence / delayed-credit telemetry*: on an `axiom.json` identity commit, retrospectively trace the prior 48h
  to document which low-visibility processes (incubation, dream, frontier-drift) preceded the breakthrough.
- *The T4-canary hard gate*: **`Δ Opportunity_to_Run(T4) ≥ 0` or Phase 1 is blocked** (§6).

**Status:** both auditors have converged; Gemini authorises **Phase 0 assembly** (shadow lifecycle manager +
contention census + emergence/abandonment telemetry + the lull census) — observe-only, the data to decide
*whether* rich lifecycle arbitration is even warranted, and the safety floor that the slow set is never starved.

## 12. The content-blind invariant + stall-vs-incubation (auditor round 4: ratification)
A fourth review ratified the plan (no new structural hole) and confirmed the framing — *"if the earlier plan was
about what deserves salience, this one is about how cognition should live through time"* — while pressing the one
boundary that recurs in every plan this session: **does the lifecycle manager merely preserve and schedule, or
does it quietly become the thing that decides what is worth being — the hidden homunculus in a scheduler badge?**
This is the load-bearing safety question; it earns a first-class operational answer.

### 12.1 The content-blind lifecycle invariant (the operational boundary)
**The lifecycle manager NEVER reads thought content and NEVER judges meaning or worth.** Every state transition
(`run / background / suspend / archive / resurface`) is a **mechanical function of declared, non-semantic
signals only**: lane occupancy, capacity (hardware + person-present), time-on-task (the fatigue ramp), and the
**per-source progress/stall flag + salience scalar that the source node itself emits** (the §15-style contract
from the idle-executive). *"What is worth being"* is decided **upstream** — by each source's own salience (its
domain-local contract) and by **selection** (the idle-executive). The scheduler only moves processes between
states based on those upstream numbers; it never re-evaluates the meaning behind them. **The acceptance test
(reused from the idle-executive's anti-homunculus law):** replace the lifecycle manager with a deterministic
state-machine over the same scalars — if the *same* transitions result, it is pure lifecycle control; if outcomes
change, it has started doing cognition and must be stripped back. That is the standing pressure-test the reviewer
asked for: *scheduler, or judge?* — answerable mechanically on every change.

### 12.2 Stall-vs-incubation dissolves under horizon-classification (the missing crisp answer)
The reviewer's sharpest "what's missing": *what counts as a true stall vs incubation?* The honest answer is that
the distinction is **not locally decidable** — so the plan does **not try to decide it prospectively.** Instead:
- **Fast-horizon sources** (reading/math/study): a stall *is* a stall — local progress is reliable there — so
  `stall → stop` is safe.
- **Slow-horizon sources** (frontier/incubation/dream/T4): these are **never subject to `stall → stop` at all**;
  they keep-warm-and-probe regardless of local quiet. So we **never need to tell stall from incubation for them**
  — we simply don't abandon them on local signals.
The discrimination problem therefore **dissolves**: we only apply abandonment where stall is reliable, and the
**§6c abandonment telemetry empirically reclassifies** a source if its "stalls" keep resuming with payoff (then
it's slow-horizon, never abandoned). We learn the horizon from data; we never guess incubation in the moment.

### 12.3 Delayed value = retrospective protection, not prospective prediction
*How does it detect an unproductive-looking process is setting up delayed value?* It **doesn't try to predict**
that — predicting delayed value is the forecasting trap that selects for conservatism (§10.6). Instead the
**emergence/contribution telemetry (§6e)** detects it **retrospectively**: a source whose low-visibility outputs
keep preceding later commits earns **protected** status. Protection is *earned by demonstrated past contribution*,
not *granted by a hopeful forecast*. (Avoids both the productivity trap and the conservatism trap.)

### 12.4 Phase 0 is a DISCOVERY pass, not proof the categories are settled (concur)
Adopted explicitly: Phase 0 **discovers** the horizons, the real contention, and the contribution patterns — it
does **not** confirm a pre-set taxonomy (the §10.2 correction, restated). The initial three categories are a
prior to be overwritten by the data; the T4-canary hard gate (§6) is what makes it safe to be wrong about them
in the interim.

**Net of round 4:** no structural change — a ratification — but the recurring homunculus boundary is now an
**operational invariant with a mechanical acceptance test** (§12.1), the stall-vs-incubation gap is *dissolved*
rather than papered over (§12.2), delayed-value handling is pinned as *retrospective-protect not predict* (§12.3),
and Phase 0 is explicitly a discovery pass (§12.4). The reviewer's standing question — *scheduler or judge?* — is
now a check we can run, not a worry we carry.

## Sources (v2 research pass)
- **Vigor = opportunity cost of time:** Niv, Daw, Joel & Dayan (2007), *Tonic dopamine: opportunity costs and
  the control of response vigor*, Psychopharmacology — average reward rate (tonic dopamine) sets response vigor;
  agents choose action *and* latency, latency shorter when reward rate is higher.
  https://link.springer.com/article/10.1007/s00213-006-0502-4 ·
  https://pubmed.ncbi.nlm.nih.gov/17031711/
  *Honest counterpoint:* Beierholm et al. (2016), *Dopamine Manipulation Affects Response Vigor Independently of
  Opportunity Cost*, J Neurosci — vigor is not *only* opportunity cost. https://www.jneurosci.org/content/36/37/9516
- **Expected Value of Control:** Shenhav, Botvinick & Cohen (2013), *The Expected Value of Control: An Integrative
  Theory of ACC Function*, Neuron — control recruited iff expected payoff × efficacy > intrinsic effort cost.
  https://www.cell.com/neuron/fulltext/S0896-6273(13)00607-7 · efficacy term:
  https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7884731/
- **Flow vs DMN (distinct regimes):** *Go with the flow: a neuroscientific view on being fully engaged*
  (PMC7983950) — flow = low DMN + strong Central Executive Network; salience network (ACC) monitors feedback /
  "in control"; boredom / flow / stress = three states on an inverted-U, not gradations.
  https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7983950/
