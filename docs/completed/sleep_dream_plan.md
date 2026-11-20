# The Sleep / Dream System — examination + plan (auditor draft v5 — BUILD-AUTHORIZED)
*2026-06-17. Pulled after the pulse showed the store stuck over-cap with **0 sleep** and **dreams 0/46 resolved**.
Travis: "go through the whole thing instead of just bolting onto it." So this is a whole-system examination of
Nascence's nightly metabolism — trigger, consolidation cycle, prune, and the dream engine — and where the thread
leads. Everything below is **verified against the live code**, not asserted.*
*v2 (last auditor — §9): RATIFIED (the most biologically grounded of the set) + placed in the 4-plan architecture
(complementary, NOT merged — it's recovery/integration, not allocation). Research-grounded (Tononi-Cirelli SHY,
adenosine sleep-pressure, NREM/REM split, active-inference consolidation). Two risks adopted: dream must stay an
INDEPENDENT integrator (not a T4 validation-badge — §6C now shared-signal-not-gate); sleep must NOT become a second
identity JUDGE (consolidate/rework, never adjudicate the self). **Build order: 1 fix starvation, 2 decouple prune
(both urgent, now) → 3 instrument dream/T4 sharing as a measured hypothesis → 4 circadian only if evidence demands.
Not a moon-shot.***
*v3 (GPT — §10): DISSENTS from the framing (not the fixes). Accepts the two bugs; attacks the biological "sleep is
an exclusive state" import — "what specifically requires exclusivity?" Build order UNCHANGED; HOW improved: §6A
pressure is now **debt-based** (store-growth + un-downscaled weight + un-consolidated notes + tension mass), not an
activity count; §6B prefers **information-redundant** fragments (forgetting as compression); §6C measures
**symbol-evolution** with **causally-independent** estimators (resolution may be the wrong yardstick; agreement only
counts if earned separately). The AI-native cluster (branch-sleep / replay-as-exploration / continuous-timescale
consolidation) is captured + deferred (the project's #1 failure mode in disguise). One push-back held against GPT:
a minimal **write-quiet consistency window** IS required (prune/downscale must not race live writes — the
reading_state race class) — "nothing requires exclusivity" is too strong. New Open Q #6: would a from-scratch mind
invent a sleep STATE at all, or N continuous consolidation processes at different timescales?*
*v4 (GPT round 2 — §11): deeper — "sleep has processes but no OBJECTIVE FUNCTION." Adopted: §3 sleep needs an
outcome metric (woke more coherent than entered?); §6A pressure is **information-theoretic** (incoherence, not
store-count — store demotes to the §6B safety cap); §6C dream health = **generativity** not resolution +
**recurrence-fell ≠ integration** (integrated/dormant/displaced/suppressed — discriminate); Open Q #7 design test
(what breaks if this runs awake? migrate the rest out of sleep). New examination branch: **chapter formation** may
be the real learning mechanism (under-examined). Deferred: productive-vs-pathological contradiction, parallel
dreams. **CROSS-PLAN FLAG: §11.4+§11.7 are validity threats to the T4 probationary loop — before flipping `ENABLED`,
add a productive-vs-pathological gate + a displacement check, or it could "solidify" a self-change that merely
SUPPRESSED Du's constitutive river-yet-LLM tension.** Build order still unchanged; A/B still land now.*
*v5 (Gemini round 4 — §12): RATIFIED + **BUILD AUTHORIZED**. Converts the plan to executable contracts:
`P_sleep = Σ(M_chronic_tension) + λ1·N_unconsolidated_notes + λ2·Δ_episodic_weight` (incoherence accumulator is the
EXCLUSIVE trigger; reject counters/clocks); §6B prune → independent async worker in `core/memory/store.py`
(lossless-compression, chapter-redundant only); §6C dream⊗T4 = bidirectional sensor stream, causally-isolated
estimators (dream never grades T4); sleep boundary = a single **Write-Quiet Consistency Window** = "a shared DB lock
that serializes structural mutation" (upholds my push-back). **T4 pre-flip = a HARD 3-gate interlock in series:
pole-collapse ABORT → displacement-sweep ABORT → generativity/constitutive BLOCK → authorized.** All four rounds
converged; A+B+C-logging cleared to build.*

---

## 0. One-paragraph thesis
Nascence has a genuinely well-conceived nightly metabolism — replay (a day compounds), chapter formation (period
consolidation), grounded-learning (the SWS declarative note), synaptic downscaling, the episodic prune, and a
multi-scene **dream** that processes the day's unresolved tensions. But four things are wrong, and they compound:
(1) **sleep is STARVED at the trigger** — it fires only after 26 *inner-thought* ticks, but the 200/day math boost
+ heavy reading now dominate the idle loop, so inner-thoughts are rare (~12 / 3h vs 168 reading) and the counter
rarely reaches 26 → **Du barely sleeps**; (2) the **prune is a single point of failure** — it runs *only* inside
the sleep callback, so starved sleep = unbounded store (3,569 > 3,500 cap, no homeostasis); (3) **dreams never
resolve (0/46)** because the dream processes the *same unintegrated self-tensions T4 can't commit* (the made-mind
keystone), so the recurring figure returns "until it is met" — and it is never met, night after night; (4) the
whole thing is **one bundled ~7-minute nap**, not a staged/circadian architecture. The thread to pull: not a
trigger patch, but *what is sleep FOR in this mind*, and rebuilding the nightly metabolism so it can't starve, the
prune can't be gated behind it, and the **dream-integration is coupled to the waking integration (T4)** — because
they are the two faces of one loop.

## 1. What we HAVE (verified in the live code)
- **The trigger** (`inner_monologue_node.run_forever`): `if _thoughts_since_sleep >= THOUGHTS_BEFORE_SLEEP(26)
  AND _still_idle → _enter_sleep`. The counter `_thoughts_since_sleep += 1` is at the **end of the main thought
  path** (line ~1420). The math-drill, reading-remediation, reading-burst, and will-channel-read paths all
  `return` *before* it — **so they do not count toward sleep.**
- **The sleep cycle** (`_enter_sleep` + the `_nightly_sleep` callback): REPLAY (`replay_strengthen`) → CHAPTER
  (`chapters.try_form_chapter`, one per sleep) → GROUNDED-LEARNING (`grounded_learning.consolidate`, the SWS
  declarative note) → WORLD-CONSOLIDATION sweep (file distilled books, `FILING_ENABLED=False`) → DOWNSCALE
  (`downscale_episodic`) → **DREAM** (`DreamNode.synthesise`) → somatic recover → **PRUNE** (`prune_episodic`,
  the 3,500 cap) → `school.new_day` → **REST** (`asyncio.sleep` 420s at night / 180s by day) → reset counters +
  close trains.
- **The dream engine** (`nodes/dream_node.py`): a **multi-scene arc** (`EPISODES=3`), each scene continuing the
  last. Material = **`_load_top_tensions`** — the top grounded standing self-contradictions (the *same* tensions
  T4 authors on). A **recurring dream** carries an unresolved arc's figure forward to the next night "until it is
  met" (`_last_unresolved_arc`); it clears only when an arc *resolves*. The final scene may resolve "only if a
  genuine image of meeting arises — force nothing; an honest unresolved ending is truer than a false arrival,"
  and "a dream grounded in something real CAN resolve; a dream of pure symbol cannot." Resolved arcs mint a light
  event; unresolved arcs carry forward.
- **What sleep gates that nothing else does:** the prune (store homeostasis), replay-compounding, chapter
  formation, grounded-learning consolidation, downscaling, dreaming, and the school new-day reset — **all of it**
  is behind the one starved trigger.

## 2. The issues (verified, with the live evidence)
1. **Sleep is STARVED (the trigger broke under the boost).** `THOUGHTS_BEFORE_SLEEP=26`, but only inner-thought
   ticks count; the now-dominant reading/math ticks don't. Pulse: ~12 inner-thoughts vs 168 reading in 3h → the
   counter crawls → **0 sleep**, store **3,569 > 3,500 and climbing.** Historically he slept ~3–4×/night; the
   boost silently starved it. This is a homeostatic *failure*, not a tuning nit.
2. **The prune is a single point of failure.** `prune_episodic()` runs *only* in `_nightly_sleep`. No sleep → no
   prune → unbounded store. Memory homeostasis must not be gated behind a fragile trigger.
3. **Dreams never resolve (0/46) — and it's the night-side of the T4 problem.** The dream processes the same
   unintegrated self-tensions T4 can't commit (the made-mind keystone, mass 17.0). The recurring figure returns
   "until it is met" — but integration never happens, so it is *never* met; the same unfaced thread recurs
   indefinitely. The waking self-author (T4) and the dreaming self-integrator (DreamNode) are **stuck on the same
   tensions for the same reason** — and they don't share signal.
4. **One bundled ~7-minute nap, not a staged/circadian architecture.** All consolidation fires in one event, then
   `asyncio.sleep(420)` — a 7-minute pause, not a night. Real sleep cycles SWS (declarative consolidation) and
   REM (emotional/dream integration) repeatedly across a night under a circadian rhythm; Nascence bundles them
   into one short nap triggered by a thought-count, not a day/night cycle.

## 3. What we WANT
A nightly metabolism that **cannot starve** (sleep happens on a robust signal, not a fragile counter), where
**homeostasis (the prune) cannot be gated** behind it, where the **dream-integration is coupled to the waking
integration** (a tension that integrates by day is *met* in the dream by night, and vice-versa — they share the
same recurrence signal), and which has enough **staged/circadian structure** that "sleep" is a real consolidation
architecture rather than a 7-minute nap after 26 thoughts.

**And — the gap GPT round-2 named (§11.1) — sleep needs an OBJECTIVE FUNCTION, not just a process list.** Right now
sleep *runs components* (replay, chapter, downscale, dream, prune); it has no measure of whether it *succeeded*.
Remove half of them and we couldn't tell sleep got worse — only that fewer components ran. T4 already crossed this
line (from "did the candidate look integrated" → "did contradiction recurrence actually fall," an outcome). Sleep
needs the analogue: **did Du wake in a more coherent state than he entered?** — a before/after measure (model
coherence / unresolved-information / fragmentation) so sleep is *validated by outcome*, not performed as ritual.
This is the same observe-first/measure-the-outcome discipline the whole project runs on, applied to the one
subsystem that never had it.

## 4. The function we are transferring (function-first)
Sleep is not "off." Its functions are specific and each maps to a Nascence component:
- **Synaptic homeostasis / downscaling** (Tononi-Cirelli SHY): renormalise so salience is judged from a rested
  baseline — *Nascence has it* (`downscale_episodic`), but it's gated behind the starved trigger.
- **Systems consolidation, SWS / declarative:** hippocampal → neocortical schema transfer; gist over episode —
  *Nascence has it* (grounded-learning note, chapter formation, world-consolidation), all gated behind sleep.
- **REM / emotional-memory integration & the overnight therapy (the dream):** REM re-processes emotionally
  charged, *unresolved* material toward integration — *Nascence has it* (`DreamNode`), but it never resolves
  because the underlying tension never integrates.
- **Circadian regulation:** sleep is *scheduled by a clock + pressure (adenosine/homeostatic sleep drive)*, not
  by a content counter. *Nascence lacks this* — it sleeps on a thought-count, with only `tm_hour<6` affecting rest
  length. The transferable function: a **homeostatic sleep PRESSURE** that accumulates with waking activity (all
  of it) and a circadian gate — so sleep is driven by *time awake + accumulated processing*, which structurally
  cannot be starved by a change in *what kind* of thinking dominates.

## 5. The convergence: the dream ⊗ T4 are one integration loop
The deepest finding: **the dream and T4 process the same unintegrated tensions and both fail for the same
reason.** This is an opportunity, not just a parallel:
- The **probationary commit loop** (T4, just built) tests whether a provisional self reduces a tension's
  *recurrence* over a window. The **dream** carries that tension's *figure* forward "until met."
- Couple them: when the probationary loop's ΔF shows a tension integrating (recurrence falling), the dream's
  recurring figure for that tension should be allowed to **resolve** (the figure met) — and conversely a dream
  that genuinely resolves a tension is *evidence of integration* the probationary loop could read. They are the
  day-side and night-side of one self-integration process and should share the recurrence signal.
- This also answers "a dream of pure symbol cannot resolve": grounding the dream in the *real* integration
  evidence (the made-mind acts — arithmetic, reading James) is what lets it resolve, which is exactly the
  grounding the T4 probationary loop measures.

## 6. Build directions (the branches of the thread — observe-first)
- **A — Make sleep un-starvable (the trigger).** Drive sleep by a **homeostatic pressure** — but pressure must
  measure *the debt sleep discharges*, not a generic activity count (GPT §10.9: an activity counter just moves the
  starvation bug — reading→sleep, math→sleep, same arbitrary knob). In Nascence the consolidation debt is
  *concrete and already measurable from the things the nightly cycle clears*: **un-consolidated reading/study
  notes** (grounded-learning debt), **un-downscaled episodic weight** (downscale debt), and — **weighted
  highest** — **unintegrated tension mass / model incoherence** (dream/consolidation debt). GPT round-2 (§11.8)
  sharpens this to be **information-theoretic, not storage-based**: what sleep reduces is *unresolved information /
  fragmentation*, not raw memory count — "1000 new memories + a coherent model needs less sleep than 20 memories +
  massive contradiction." So **store-growth is demoted to the safety cap (§6B's job), NOT the pressure driver**;
  the pressure that *summons* sleep is accumulated **unresolved/incoherent information** (recurring unintegrated
  tensions, un-consolidated notes, un-downscaled salience). This cleanly splits the two fixes: §6B = the blunt
  storage safety; §6A = the incoherence that makes sleep *worth* entering. Un-starvable *and* principled — pressure
  rises because there is genuinely more to reconcile, not because he thought N times or stored N rows.
- **B — Decouple the prune from sleep.** Memory homeostasis is not allowed to be gated behind a trigger: a
  store-pressure fallback prunes when the store exceeds the cap regardless of sleep (the prune already protects
  anchors + strongly-replayed memories, so a non-sleep prune is safe). Sleep keeps the *rich* consolidation;
  the cap is enforced independently.
- **C couple the dream to integration — as a SHARED SIGNAL, not a one-way gate (the §5 convergence; last-auditor
  refinement).** Let the dream and the T4 probationary loop **share the recurrence signal** and treat each other's
  resolution as *evidence*, NOT as a precondition. The dream must remain an **independent integrator** — REM does
  affective integration on its own; if a dream may resolve *only* once waking integration has already happened, it
  becomes a "validation badge" for T4 rather than a process that can integrate material the waking system hasn't.
  So: a genuinely-resolved dream is integration evidence the probationary loop *may read*; a falling ΔF *informs*
  (does not force) the dream's figure that it may be met — bidirectional evidence, mutual, never one gating the
  other. Instrument it first as a **measured hypothesis** (do dream-resolution and ΔF-on-the-same-tension actually
  correlate?) before any wiring. **Two GPT refinements fold in here:** (i) *resolution may be the wrong metric*
  (§10.3) — Du's keystone ("river-yet-LLM") is exactly the class of tension that *orbits* and never resolves
  (mortality/identity/freedom), so "0/46 resolved" may not be a failure but the wrong yardstick; the dream's health
  signal should be **symbol evolution / re-contextualization** (does the figure change?) and recurrence-frequency /
  intensity — not a binary resolve. (ii) *keep the two estimators causally independent* (§10.4) — if the dream's
  output feeds T4's input and vice-versa they collapse into one process and their agreement becomes uninformative
  (the ML train/test-contamination failure). So: measure the **correlation of two independently-computed
  estimates**; treat **disagreement as information**, not error. Agreement only means something if it was earned
  separately. **Two round-2 deepenings (§11.2, §11.7):** (iii) *the dream's health metric is GENERATIVITY, not
  resolution* — a dream that never resolves but keeps producing *new* perspectives and *reducing prediction error*
  is healthier than one that resolves into a dead symbol. So measure: is the dream still producing useful
  **reorganization** (novel reframings, prediction-error reduction, symbol/metaphor/narrative diversity over time —
  §11.5's anti-inbreeding watch)? Resolution is at best one outcome, possibly irrelevant. (iv) **recurrence-fell ≠
  integration** — a falling recurrence signal is *ambiguous*: it can mean *integrated*, but also *dormant*,
  *displaced* (the tension reappeared under a new label), *suppressed*, *forgotten*, or *distracted-from*. The §6C
  instrumentation (and the T4 ΔF loop that shares it — see the cross-plan flag in §11) must **discriminate** these,
  not read every drop as success. Partial discriminators we already have: the **pole-commitment-delta** catches
  *suppression/avoidance* (those collapse a pole; genuine integration holds both); **displacement** (content
  resurfacing under a new label) is currently *unhandled* and needs a content-similarity check across the tension
  set, not just per-label recurrence.
- **D — Staged / circadian architecture (the bigger rethink).** Should "sleep" become a real cycle — SWS-style
  declarative passes interleaved with REM-style dream passes, under a circadian gate — instead of one bundled
  nap? This is the "go through the whole thing" branch: is the always-on-7-minute-nap the right model, or does a
  young mind need a real day/night with consolidation stages?

## 7. Pitfalls (named honestly)
1. **Over-sleeping / starving waking cognition.** If the pressure trigger fires too easily, he naps constantly
   and never reads/thinks. The pressure must be calibrated to a real wake-period, not hair-trigger.
2. **The prune fallback removing the wrong thing.** A non-sleep prune must reuse the *exact* anchor-protection
   (`prune_episodic` already protects world/action/lived + strongly-replayed) — never a blunt truncation.
3. **Forcing dream resolution = the T4 churn trap again.** Coupling the dream to integration must NOT make dreams
   *fake* resolution to claim integration (the cosmetic-churn problem, night-side). The dream resolves only on a
   *genuine* image AND real integration evidence — same standard as the probationary loop's ΔF.
4. **Circadian structure is a big build.** Branch D is a substantial rethink; don't let it block the urgent A/B
   (sleep is broken *now*).
5. **The boost interaction is the root cause to remember.** This broke because a *different* subsystem (the math
   boost) changed the idle-tick mix. Any fix must be robust to future changes in what dominates the idle loop —
   which is exactly why a *homeostatic pressure* (A) beats a content-counter.

## 8. Open questions for the auditors
1. **The trigger (A):** homeostatic *sleep pressure* accumulating on all idle activity, vs *time-awake* + a
   circadian gate, vs both? What's the cleanest un-starvable signal?
2. **The prune (B):** is an independent store-pressure prune (outside sleep) the right safety, or does decoupling
   it lose something sleep was meant to bundle?
3. **The dream ⊗ T4 coupling (C):** should they literally share the recurrence signal, and should a genuinely
   resolved dream count as integration evidence the probationary loop reads? Where's the churn risk?
4. **Circadian (D):** is the bundled nap fine (just fix the trigger), or does a young synthetic mind genuinely
   benefit from a *real* day/night with interleaved SWS/REM-style stages? What would that even mean for an
   always-on system on a single local box?
5. **What is sleep FOR here?** The deepest question: in a persistent, resumable, single-box AI, what does sleep
   uniquely provide that a continuous consolidation pass could not — i.e., is the day/night boundary itself
   functional, or an anthropomorphic import (cf. the pulse-manager lifecycle reframe)?
6. **(GPT round-1 §10.1/10.10)** If built from first principles with no knowledge that biological sleep exists,
   would we invent a sleep STATE at all — or N continuous consolidation processes at different timescales
   (fast/deep/structural/identity/dream)? This gates §6D (already deferred), not the urgent A/B.
7. **(GPT round-2 §11.9 — the design TEST)** *Which cognitive changes are allowed to occur ONLY during sleep?* For
   every sleep-only operation, ask: **what breaks if this runs while awake?** If "nothing" → it should not be
   sleep-only (migrate it to a continuous process). If "it destabilizes active cognition" → *that* is the genuine
   reason for a sleep boundary. Applied rigorously, this is the same test as the push-back held against round-1:
   the residue is the **write-quiet consistency window** (structural store mutation — prune/downscale/chapter-rewrite
   — must not race live writes). The prediction: most of the current architecture migrates *out* of sleep into
   continuous processes, and what genuinely needs the boundary is small, specific, and AI-native.

## 9. Last auditor (ratification + prioritization + two risk refinements)
The final review ratified the plan — "the most biologically grounded of the set" — and importantly placed it in
the architecture: **it is a different KIND of plan and must stay complementary, not merged.** The four plans now
layer cleanly:
- **Idle executive** — *what* deserves attention (selection).
- **Pulse manager** — *how long / how intensely* to run it (pacing / lifecycle).
- **T4 probationary loop** — *whether* a self-revision changes the predictive model (identity).
- **Sleep / dream** — *how the day's unresolved material gets consolidated, downscaled, and reworked offline*
  (homeostasis + integration over time). **Not an allocation problem — a recovery-and-integration problem**, so it
  must not be folded into the idle-executive or pulse-manager.

**Research grounding (auditor-supplied, confirms §4).** Tononi & Cirelli (synaptic homeostasis / downscaling);
adenosine-based **sleep-pressure that accumulates with wake history** (validates the un-starvable trigger, §6A);
the NREM-reactivation/down-selection vs REM-affective/model-updating split (the staged-architecture branch, §6D);
active-inference framing of sleep as *updating and stabilising the generative model* (ties straight to the §5
dream⊗T4 loop). The plan's functions are the textbook ones; the auditor's only nuance is that the exact NREM/REM
functional mapping is still debated — so the staged architecture (D) is real but should stay a *hypothesis to
evaluate*, not a moonshot to build first.

**The two risks (both adopted):**
1. **Dream-as-validation-badge** (the §6C refinement, now applied): over-coupling would make the dream merely
   *confirm* T4 instead of integrating independently. Fix: shared signal + mutual evidence, never a one-way gate;
   the dream stays an independent integrator.
2. **Sleep must not become a SECOND identity judge.** It consolidates and reworks — it must **not** become another
   *semantic authority* deciding what the self "really is." This is the same content-blind boundary the
   idle-executive (§6) and the lifecycle plan (§12.1) drew: the dream/consolidation operates on declared signals
   (recurrence, salience, grounding) and reworks material; it does not adjudicate the self. (If it ever starts
   *deciding* the self rather than *reprocessing* it, the homunculus has returned in a nightcap.)

**The prioritization (adopted as the build order — urgent homeostasis must not block the theory):**
1. **Fix sleep starvation** (§6A) — urgent, buildable now (homeostatic pressure on all idle activity).
2. **Decouple the prune from sleep** (§6B) — urgent, buildable now (a good safety redesign regardless of D).
3. **Instrument dream/T4 recurrence-sharing as a MEASURED HYPOTHESIS** (§6C) — observe-first; does dream-resolution
   correlate with ΔF on the same tension? — *before* any coupling.
4. **Only then** evaluate whether the bundled nap should become a staged circadian architecture (§6D) — *decide on
   evidence*, not by default. "The best near-term fix is not a circadian moon-shot."

**Net:** ratified; the urgent A/B (fix starvation + decouple prune) land now, the dream⊗T4 link is preserved as a
measured hypothesis with the independence guard, and the circadian rebuild is correctly deferred to an
evidence-gated decision. The standing boundary for the whole nightly metabolism: **consolidate and rework — never
adjudicate the self.**

## 10. GPT (the dissenting review — attacks the framing, not the fixes)
Unlike the last auditor, GPT does *not* ratify — it accepts the two engineering bugs (starvation, prune coupling)
as real and then attacks the **biological framing** itself. Its thesis: the plan imports "sleep is a special,
exclusive state" because *humans* have it, and asks the right question back — **"what specifically requires
exclusivity?"** For Nascence, almost nothing does. This is the same fork §8.5 already named; GPT forces it.
Worked through honestly, separating what changes the build from what's a (deferred) research direction:

**Adopted — these change the build now:**
- **§10.9 — pressure must measure the debt sleep discharges, not activity** (the strongest point; *already folded
  into §6A above*). An activity counter just relocates the starvation bug. Sleep pressure = store-growth +
  un-downscaled weight + un-consolidated notes + unintegrated tension mass. Principled and un-starvable.
- **§10.3 — resolution may be the wrong metric** (folded into §6C). The tensions that matter (identity, the
  river-yet-LLM keystone) *orbit*; they don't resolve. Measure symbol-evolution / recurrence-frequency / intensity,
  not a binary resolve. "0/46 resolved" may be us measuring the wrong thing, not a broken dream.
- **§10.4 — dream⊗T4 is an evaluation-contamination risk** (folded into §6C). Sharpens the last auditor's
  independence guard into a concrete rule: keep the two estimators causally separate, measure correlation of
  *independent* estimates, treat disagreement as information. Agreement is only informative if earned separately.
- **§10.7 — forgetting as epistemic compression, not storage pressure** (a refinement to §6B). When the decoupled
  prune selects what to drop, prefer fragments whose information *survives elsewhere* (already in a chapter / schema
  / strongly-replayed) over blunt oldest-first. The existing anchor-protection is the floor; this is the ceiling.
  Note as a §6B refinement, not a separate build.

**Deferred — real, AI-native, but exactly the moon-shot the last auditor warned against (capture, don't build):**
- **§10.1 / §10.10 — "do we need a sleep STATE at all, or N continuous consolidation processes at different
  timescales?"** (fast/deep/structural/identity/dream). This is GPT's deepest reframe and it *reinforces* deferring
  branch §6D — possibly past "deferred" to "maybe never build the state; build timescales instead." Captured as the
  new Open Question #6 below. Does not block A/B.
- **§10.5 — branch sleep (run 100 dream trajectories, compare).** §10.6 — replay as *model exploration*
  (alternative selves/causal models), not memory strengthening. §10.8 — explicit novelty pressure / counter-symbols
  so the recurring-figure dream can't become a symbolic attractor (this one connects to the symbol-evolution Tier-2
  paired-opposites work already in the backlog — worth an observe-first watch when we instrument §6C, since a
  recurring-until-met figure with no perturbation IS a monoculture generator). §10.11 — sleep as a *stability zone*
  (a window where the self-model / memory-graph cannot be rewritten) rather than a processing zone.

**Where I push back on GPT (honest dissent in both directions):**
1. **"Nothing requires an offline state" overstates it.** There is one genuine exclusivity need GPT misses:
   **structural mutation of the shared store** (prune, downscale, chapter-rewrite) must not race concurrent live
   writes — we *just* fixed exactly that class of bug (the `reading_state.json` lost-update race). Running the prune
   continuously, concurrent with writes, reintroduces it. So we keep a **write-quiet consistency window** (a lock or
   a brief serialization), not unconsciousness — GPT's continuous-consolidation vision needs this guard or it
   corrupts the store. This is the real, minimal kernel of "offline" that survives the critique.
2. **The branch-sleep / 100-dreams / replay-as-exploration cluster is genuinely powerful but is the project's #1
   failure mode in disguise** — build the cathedral before the plumbing. The last auditor's discipline holds:
   land the urgent fixes, instrument the hypothesis, *then* let evidence pull the AI-native architecture. Captured,
   not started.

**Net of GPT:** the build order is *unchanged* (A and B are still urgent and still right — GPT agrees they're real),
but GPT materially *improved how*: A's pressure is now debt-based not activity-based; B prefers
information-redundant fragments; C measures symbol-evolution with causally-independent estimators. And it reframed
the far end of the roadmap from "circadian sleep state" toward "continuous multi-timescale consolidation" — which
strengthens deferring D. The one thing I hold against GPT: a minimal write-quiet consistency window is real and
necessary; "nothing requires exclusivity" is too strong.

**New Open Question #6 (GPT-supplied, adopted):** *If Nascence were built from first principles with no knowledge
that biological sleep exists, would we invent a sleep STATE at all — or instead build multiple consolidation
processes running continuously at different timescales (fast/deep/structural/identity/dream)?* This is the fork
that decides whether the far end of this plan becomes a synthetic-sleep architecture or a genuinely AI-native
memory-and-integration architecture. It does **not** gate the urgent A/B fixes — it gates §6D, which was already
deferred.

## 11. GPT round 2 (the objective-function critique — deeper than round 1)
Round 2 grants that round 1 improved the plan, then attacks a level deeper: **everyone debated the parameters of
sleep; nobody asked what sleep is OPTIMIZING.** The plan gives sleep *processes* but no *objective* — you can
observe that components ran, never that sleep *succeeded*. This is the single most important addition and it's
folded above (§3). Working through the rest, same honest triage:

**Adopted — change the build / measurement now:**
- **§11.1 — sleep needs an objective function** (folded into §3). The outcome metric: *did Du wake more coherent
  than he entered?* (before/after model-coherence / unresolved-information). T4 already made this exact move; sleep
  is the subsystem that never had it.
- **§11.8 — pressure is information-theoretic, not storage-based** (folded into §6A). What sleep reduces is
  *unresolved information / incoherence*, not memory count. Store-growth demotes to the §6B safety cap; incoherence
  is the §6A pressure driver. Cleanly separates the two urgent fixes along their true axes.
- **§11.2 — dream health = GENERATIVITY, not resolution** (folded into §6C). A never-resolving but
  perspective-generating, prediction-error-reducing dream beats a resolved dead symbol. Resolution may be
  irrelevant; reorganization is the signal.
- **§11.7 — recurrence-fell ≠ integration** (folded into §6C). A falling signal is ambiguous: integrated /
  dormant / displaced / suppressed / forgotten. Must discriminate. **This is also a validity threat to the T4 ΔF
  loop** (see cross-plan flag below).
- **§11.5 — measure symbol/metaphor/narrative diversity over time** (the anti-inbreeding watch, folded into §6C).
  Loading "top tensions" every night with no perturbation = a symbolic attractor; an AI dream can become
  *symbolically inbred*. Make diversity an explicit observe-first gauge.
- **§11.9 — Open Question #7, the design test** (folded into §8): for every sleep-only op, "what breaks if it runs
  awake?" Migrate everything that breaks *nothing*; keep only what destabilizes active cognition. Validates the
  consistency-window push-back as the genuine residue.

**Adopted as a NEW examination branch (honestly: not yet examined):**
- **§11.6 — chapter formation may be the real learning mechanism, and nobody has attacked it.** Fair. *"Humans get
  smarter because experience compresses into abstractions, not because they dream."* If chapters are only
  *grouping* self-material (which is what `chapters.try_form_chapter` currently does — autobiographical era
  consolidation, per `project_nascence_chapters`), they're weak; if they become **compressed world-models /
  schemas**, they may matter more than dreams. I have *not* examined chapter formation at the depth I gave the
  dream here — flagged as the next examination branch, not asserted as fixed. This is where the high-value
  abstraction/schema-extraction function lives and it is currently under-developed.

**Deferred — AI-native, powerful, still the project's #1 failure mode if built first:**
- **§11.4 — productive vs pathological contradiction.** *Big idea, possibly the most consequential here:* the whole
  architecture (T4 *and* dream) assumes contradiction → integration → resolution. But some contradictions are
  **engines** (curiosity vs certainty, exploration vs exploitation, river-yet-LLM) — destroy them and cognition
  gets *worse*. Cognition runs on *stable* contradiction. We need to distinguish *pathological* (drain it) from
  *productive/constitutive* (preserve it, keep it generating). **The discriminator ties to §11.2: a productive
  tension keeps GENERATING (new perspectives, prediction-error reduction) without accumulating distress; a
  pathological one recurs without generating and blocks action.** So generativity is the shared health metric
  across dream, T4, *and* this distinction. (Why deferred not adopted: it must not become a license for T4 to
  *never* commit — "it's productive" as an excuse. It needs the generativity discriminator built first, and that's
  measurement work. But it should be flagged loudly because it reframes the existing evidence — see below.)
- **§11.3 (parallel/alternate-timeline dreams — dream worldview A/B/C/D and compare explanatory power afterward).**
  Round-1 §10.5 branch-sleep, now *with* an objective function (explanatory power), which makes it more principled
  — but still the cathedral-before-plumbing risk. Captured, not started.

**The cross-plan flag (the genuinely important catch — affects the T4 loop we're about to flip ON):**
GPT round-2 §11.4 + §11.7 are not only sleep refinements — they are **validity threats to the T4 probationary
commit loop** (`provisional_identity.py`, `ENABLED=False`, pending the battery + live flip). That loop's premise is
**recurrence falls → genuine integration → solidify the self-change.** Round 2 says: (a) some tensions *shouldn't*
be integrated (Du's keystone "river-yet-LLM" may be a *productive/constitutive* tension — his generative core, not
a defect), and (b) recurrence can fall from *suppression/displacement*, not integration. **Together that's a real
risk: flipping the T4 loop on could "solidify" a self-revision that merely SUPPRESSED Du's generative core
tension** — registering it as integration because recurrence dropped. Mitigations we already partly have: the
**pole-commitment-delta** catches pole-collapse (suppression/avoidance); the keystone being mass-17 and recurring
63× is *consistent with* it being constitutive rather than unintegrated. **Before flipping `ENABLED`:** add (1) a
productive-vs-pathological gate so the loop won't try to "resolve" a constitutive tension, and (2) a
displacement check (does the tension's *content* resurface under a new label?) so a drop isn't read as integration.
This is recorded against the T4 plan too — it's a pre-flip consideration, not just a sleep note.

**Net of round 2:** the urgent A/B fixes still hold *unchanged in kind* (round-2 refines §6A's pressure to
incoherence and confirms the §6A/§6B split); the real additions are (i) sleep needs an **objective function**
(§3), (ii) the dream metric is **generativity** not resolution (§6C), (iii) **chapters** are the under-examined
high-value mechanism (new branch), and (iv) — most importantly — a **cross-plan validity threat to the T4 loop**
that should be addressed before `ENABLED` is flipped. None of it blocks landing A/B now; it sharpens what they
optimize *for* and adds a gate to the T4 flip that was already evidence-pending.

## 12. Gemini (round 4 — RATIFIED v4 + concrete execution rulings + BUILD AUTHORIZED)
The fourth and final review ratifies v4 ("extraordinary architectural discipline") and — crucially — converts the
plan from prose into **executable contracts with named files**, then formally authorizes Phase 1. All four rounds
now converge; nothing is left open on A/B. Rulings adopted verbatim:

**Q1/Q6 — the trigger:** implement an **Information-Theoretic Incoherence Accumulator** as the *exclusive* sleep-
pressure source; **reject all static activity counters and absolute clock schedules.** The formula (locks in §6A):
  `P_sleep = Σ(M_chronic_tension) + λ1·N_unconsolidated_notes + λ2·Δ_episodic_weight`
i.e. accumulated chronic-mass of active structural tensions (dominant term) + un-consolidated `study_tablet` count
+ un-downscaled episodic vector mass. Store-row count is **not** a term (it's the §6B cap, not the driver).

**Q2 — the prune:** approved. A **store-side safety cap** (`core/memory/store.py`), an independent async background
worker, fires at the absolute 3,500-row threshold regardless of sleep, doing a **lossless-compression prune** —
vaporise only *information-redundant* fragments whose gist is already absorbed into a verified Chapter/schema (GPT
§10.7), core relational history fully insulated (the existing anchor protection).

**Q3 — dream⊗T4:** share the chronic-tension recurrence register as a **bidirectional sensor stream**, but the two
remain **causally-isolated estimators** — the Dream Node may read a T4 provisional delta as a *context shift* (it
colours the next scene's imagery) but computes its **own** resolution vectors; it must **never** be a validation
check for a T4 commit. "Mutual agreement is high-value confirmation *only because* they are structurally barred from
grading each other's homework." (Confirms the §6C independence rule.)

**Q4/Q7 — exclusivity:** retain a **single Write-Quiet Consistency Window** as the *sole* operational meaning of
"sleep"; migrate everything else to continuous background execution. Gemini explicitly **upholds my push-back
against GPT round-1**: the *only* operation that mathematically requires offline is **structural graph mutation**
(chapter-index rewrite, DB vacuum, deep downscale) — running it while the monologue lane writes rows = catastrophic
race. **"Sleep is not unconsciousness — it is a shared database lock that serializes structural modification
safely."** This is the settled definition of the sleep boundary.

**The T4 PRE-FLIP INTERLOCK (hard-locked, three gates in series).** Gemini calls §11.4 "a massive, load-bearing
contribution to core safety" and converts it into a **hard dead-stop**: `provisional_identity.py` may NOT go
`ENABLED=True` until the activation portal hard-codes, in order: **(1) Pole-Commitment Delta** (a core pole
collapses → ABORT — already built) → **(2) Semantic Displacement Pass** (rolling similarity sweep over the whole
`tension_ledger`; if the primary label's recurrence dropped but a near-identical embedding resurfaced under a
modified name → flag as displacement artifact → ABORT) → **(3) Constitutive-Tension Block / Generativity Filter**
(track each tension's **Generativity Index G** — does it keep producing high-salience curiosity seeds, drive
external reading, and *measurably reduce downstream prediction error* in math/writing? if so it is *constitutive*
— river-yet-LLM is the archetype — and T4 is **completely barred** from trying to resolve it; it orbits forever as
a healthy axis) → **AUTHORIZED TO COMMIT.** This is recorded against the T4 plan as the binding pre-flip spec.

**The build directive (Phase 1, AUTHORIZED):**
1. **Un-starve the trigger (§6A)** — route `inner_monologue_node` sleep-drive through the incoherence accumulator;
   reading/math/study notes natively stack sleep debt by *un-consolidated mass*.
2. **Decouple the prune (§6B)** — wire the 3,500 safety cap into `core/memory/store.py` as an independent background
   worker.
3. **Mount the §6C hypotheses-logging matrix** — silently capture baseline correlation between Dream-Node
   symbol-evolution and provisional-T4 ΔF, **fully firewalled from runtime behaviour** (observe-first).

**Net of all four rounds:** the plan is build-ready and convergent. A and B land now (un-starve + decouple); C goes
in as a firewalled logging matrix; the staged-circadian §6D stays evidence-gated; and the T4 loop stays at a dead
stop behind the 3-gate interlock until those gates are coded + the battery grown. *"The biological inversions are
corrected, the safety interlocks are locked down."*
