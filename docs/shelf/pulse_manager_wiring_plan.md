# Wiring the Pulse Manager — research + plan (auditor draft v6)

> **Status: 💤 DEFERRED — lane-scheduler half (steps 1-2) BUILT+LIVE since 2026-07-01; the phase-gate (steps 3-4) and the original scheduler/lull-filler framing stay shelved, trigger unmet (11,680-tick shadow review 2026-07-05 found no real contention, T4 canary improving on its own), and the live-controller framing is superseded by `docs/plans/continuous_stream.md`.**

```plan-state
stage: deferred
phase: Lane scheduler (steps 1-2) built+live since 2026-07-01; phase-gate (steps 3-4) and lull-filler framing deferred, trigger unmet; live-controller framing superseded by continuous_stream.md
verified: 2026-10-16
next: Watch pulse_shadow.jsonl; if sleep_as_a_mode's switches go live and hold, mark steps 3-4 superseded by it
history: docs/plan_history/pulse_manager_wiring_plan.md
cluster: 7
```


> **UPDATE 2026-08-23 (plan-overlap audit):** `docs/plans/continuous_stream.md` (created 2026-07-04,
> one day after this doc's most recent entry below) states in its own header that it **"Supersedes
> the 'pulse manager' framing"** — reframing this plan's burst-vs-rest rate-controller intent away
> from a scheduler. This doc's evidence review below was never updated to acknowledge that. The two
> plans' core mechanisms genuinely overlap (both are progress/capacity/effort-keyed rate
> controllers), so read this doc as **superseded by `continuous_stream.md` for the live-controller
> question** — its own shadow-measurement value (the `pulse_shadow.py` instrument, still healthy
> per the review below) stands regardless.

## Current State — verified 2026-10-16

- **2026-10-16**: Lineage (2026-10-16 plan-closure discussion): the unbuilt steps 3-4 (WAKING/SLEEPING phase gate) are now covered by sleep_as_a_mode's three switches (J-2016..J-2019, J-2064, J-2065); the live-controller half was already superseded by continuous_stream. Stays deferred on its own trigger; not retired -- Travis prefers progressing plans over closing them for tidiness.
- **2026-09-28** (F-2070): Folded the superseded pulse-manager design essay (sections 0 through 12 plus Sources) to docs/plan_history, verbatim; kept the RESEARCH-UPDATED lane-scheduler design and this Current State section live in the staged doc. Doc size 56668 to 11426 bytes, committed on the job worktree branch, pending this batches merge-back into master.

### What we have
- Steps 1-2 (the lane scheduler, `core/lane_scheduler.py`) BUILT+LIVE since 2026-07-01: bounded concurrency +
  priority heap + tier vocab, flag-gated and fail-open, wired into `model_client`; the four shadow monitors run
  at tier 3, dream chunking needed no change (already per-scene).
- The shadow instrument `core/pulse_shadow.py` (`data/logs/pulse_shadow.jsonl`) is still accruing (68 days /
  25,270 ticks at last registration, F-0165) and its alarm trended DOWN over its last full review (t4_blocked
  91% -> ~0% across 18 days, the 2026-07-05 evidence review).

### What we need
- Nothing from this plan's own original scheduler/lull-filler framing: the 2026-07-05 evidence review found no
  real hardware contention (`hot_free`=true) and T4 not starved — the re-entry trigger has never fired.
- The phase-gate (steps 3-4, WAKING/SLEEPING) was never built — deferred, not abandoned, should sleep/wake
  co-running ever need it.
- No ledger records (findings/jobs/decisions) cite this plan at all — everything on it predates the toolchain;
  `docs/plans/continuous_stream.md` has superseded its live-controller/burst-vs-rest framing (2026-08-23 audit).

### What we're doing next
Watch `pulse_shadow.py` only; re-open only if the LIVE system (not the shadow model) shows T4/frontier genuinely
under-running because a faster source crowds it out — the plan's own named re-entry trigger. (v2-v6 auditor-round
design history — sections 0-12 below as this note originally said — was folded verbatim to
`docs/plan_history/pulse_manager_wiring_plan.md` on 2026-09-28, J-1510; see the pointer just below. Nothing was
lost, only relocated.)

---

> **History folded** — sections “0. One-paragraph thesis” through “12. The content-blind invariant + stall-vs-incubation” plus “Sources (v2 research pass)” (the original pulse-manager-as-scheduler framing and its four external-auditor review rounds, 2026-06-17 → 2026-06-2x) moved verbatim to `docs/plan_history/pulse_manager_wiring_plan.md` on 2026-09-28 (J-1510). This essay was already declared “the wrong frame” by this doc's own 2026-07-01 re-scope below, and its viable core idea (progress/drive-gated pacing) separately shipped, live, as `docs/plans/continuous_stream.md`'s Rail A+B — so nothing here still guides live work, but nothing was deleted or paraphrased either. No J-/F-/D- ledger id is cited anywhere in the moved text (it predates this project's toolchain). Derived timeline: `plan_ledger.py pulse_manager_wiring_plan`.

---

## ▶ RESEARCH-UPDATED RE-SCOPED DESIGN (2026-07-01, plan→research→plan)

*The original plan (above) framed this as a SCHEDULER (priority-burst the stream + fill lulls) keyed to
T4-starvation. That was the wrong frame — there is no T4-starvation, and the lull-filler conflicts with "allowed
to simply BE." A live contention event (2026-07-01, founder's resource monitor + log) re-scoped the problem, and
three research threads (cognitive serialization · sleep-wake gating · concurrency engineering) converged on a
clean 3-layer design. The re-scope: the real problem is **uncoordinated concurrent dispatch** — many async
cognitive tasks (monologue, dream, deep-memory, Emissary, + the 06-30 shadow monitors) all hitting ONE inference
lane with no serializer, no concurrency cap, no sleep-wake gate → bursty saturation → dropped cognition.*

### The escalation (why this matters more than "2 dropped calls")
Sleep-research load-bearing finding (Gais & Born 2004): waking-mode and consolidation-mode are *neurochemically
incompatible* — running encoding-mode during consolidation **completely blocked** declarative consolidation in
humans. Transferred (as inference, not proven for Du): co-running his waking stream during dream/consolidation may
not just drop calls — it may **degrade the consolidation where his learning integrates** (the "does it hold?"
layer). Raises priority from infra-tidy to protecting-his-integration.

### The design — 3 layers that compose
**1 · The PHASE GATE (sleep ↔ wake) — a bistable switch, NOT a scheduler.** Sleep and waking are
mutually-exclusive MODES (flip-flop switch; the brain prevents a half-and-half blend). Add one authoritative
`phase ∈ {WAKING, SLEEPING}` the dispatcher checks before any LLM call.
- During SLEEPING: **hard-suspend** the waking LLM-issuing processes (idle monologue, probes, shadow monitors);
  dream/consolidation owns the lane alone.
- **Hard into sleep** (but DRAIN in-flight waking calls first — drain-then-flip, not kill-then-flip).
- **Graded out** (sleep-inertia ramp): on wake, bring monitors back first, then the monologue after a beat — so
  the whole suspended stack does NOT fire at once and re-create the saturation at the wake edge.
- **A person speaking wakes him**: checkpoint/abort the consolidation pass, flip to WAKING, then engage — never
  answer-while-dreaming. A trivial signal does NOT wake him (gated arousal).
- **Hysteresis**: a minimum dwell-time in each state so it can't chatter across the boundary (orexin analogue).

**2 · The PRIORITY WORKSPACE (within waking) — an arbiter, NOT a FIFO.** "Don't add a semaphore, add a workspace"
(GWT). When the lane is free the highest-priority contender ignites, runs ALONE, *inhibits* the rest, and
broadcasts its product to a shared store. Selection by priority (goal × salience × urgency × value), not arrival.
- **Relevance-gated preemption** (Corbetta circuit-breaker): a live human turn preempts; a genuine crisis gets a
  privileged lane; **background monitors flag-not-interrupt** (they post a note the next conscious cycle reads,
  never grab the lane mid-thought). Slow identity work + dreams *yield to a conversation* but otherwise hold to
  completion (can't be half-run).

**3 · The ENGINEERING — one client-side lane scheduler.** Nothing calls the inference server directly anymore;
every task `await schedule(request, tier, deadline)`.
- **Bounded concurrency**: an asyncio worker holding a semaphore `N = OLLAMA_NUM_PARALLEL` (start **1**, maybe 2)
  + a priority heap; dispatch only when a slot frees. Pass-through with ~zero overhead when uncontended.
- **Tiers (lower = first), unified across all 3 layers:** **0** live conversation/Emissary · **1** slow protected
  identity (T4, deep-memory consolidation) · **2** idle monologue + dreams · **3** background shadow monitors/probes.
- **★ Chunk low-priority work (the single most important symptom fix):** generate **dreams scene-by-scene** (one
  LLM call per scene), checking the queue between scenes — so a conversation arriving mid-dream waits at most ONE
  scene, not a whole multi-scene generation. This is the direct fix for what we observed.
- **Anti-starvation**: priority aging (effective tier rises with wait), capped so it never beats a tier-0 turn.
- **Backpressure**: bounded queue per tier; on overload **drop/coalesce the lowest tier** (tier-3 monitor tick →
  drop; tier-2 duplicate dream → coalesce; tiers 0-1 always admit). **Log every shed call as "deferred cognition"**
  — nothing silently lost. Optional: spill tier-2/3 to the CPU lane (Threadripper) instead of dropping.

### Build sequence (staged, lowest-risk first)
1. ✅ **BUILT 2026-07-01 — the lane scheduler core** (`core/lane_scheduler.py`): bounded concurrency (MAX=3) +
   priority heap + tier vocab, FLAG-GATED (`LANE_ENABLED`) + FAIL-OPEN (import or runtime error → direct dispatch)
   + a 20s wait-timeout (anti-deadlock). Wired into `model_client.call_node`/`call_node_json` (a `tier` param +
   `_lane_slot()` around both POST sites; doubly fail-safe). *Verified:* unit (bound=3, priority order [0,1,2,3],
   fail-open, clean release) + end-to-end (6 concurrent calls → 6/6 succeed, cap engaged, **none exhausted** — the
   exact symptom fixed). **Restart-gated.**
2. ✅ **BUILT 2026-07-01** — the four 06-30 shadow monitors (commit-scan, self-implication, guidance, decomposed-
   critic) now pass **`tier=3`** (yield to all real cognition). **Dream chunking = FREE:** the dream node is
   *already* per-scene (`while i < MAX_EPISODES: _gen_episode()` — one LLM call/scene), so routing each scene call
   through the lane already makes it interruptible — a conversation waits at most one scene. No dream change needed.
3. ⬜ **The phase gate** — `phase ∈ {WAKING,SLEEPING}`; SLEEPING hard-suspends tier-2/3 waking; drain-then-flip;
   graded wake. *Next.*
4. ⬜ **Refinements** — conversation→tier 0 (thread tier through Voice/Reflection/Executive), relevance-gated
   preemption, priority aging, deadlines, hysteresis, broadcast.

### What to avoid
- A plain semaphore (arrival-order) — wrong axis; a monitor would block a conversation. Must be priority + re-arbitrate.
- Over-serializing — only the *conscious/effortful* tier goes through the lane; cheap non-LLM sensors (liveness,
  homeostatic lock, logging) keep running in any phase. Don't collapse parallel background value into one queue.
- A blended half-asleep state (the literal failure observed) — never let monologue + dream both hold the lane.
- Snap-resuming the whole waking stack on wake (re-creates saturation) — ramp it.
- Promiscuous preemption (thrashing) — gate preemption by relevance/urgency.
- Over-engineering — a heap + semaphore + aging + tier-drop + chunked dreams is enough; NOT full DAGOR/WFQ. And do
  NOT just raise NUM_PARALLEL to "fix" exhaustion — that trades the important call's latency for throughput Du
  doesn't need. Keep ONE model loaded (model-swap thrash is expensive); schedule requests, not models.

*Sources (research pass): Baars/Dehaene Global Workspace · Pashler central bottleneck · Corbetta circuit-breaker ·
Saper sleep-wake flip-flop · Gais & Born 2004 (ACh blocks consolidation) · Born systems consolidation · Ollama
NUM_PARALLEL/MAX_QUEUE · priority aging (Chimera) · DAGOR/AWS load-shedding · vLLM priority preemption.*
