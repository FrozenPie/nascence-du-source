# Unified Contradiction Re-Architecture — plan (2026-06-16)

> **★ EVIDENCE REVIEW + DECOUPLED-JUDGE GATE (2026-07-05) — thesis retired, L0 red-flagged, L1 shipped.**
>
> **L0 (decomposed critic) — CONFIRMED BROKEN; DO NOT PROMOTE.** Over 214 shadow-alongside rows it rejects
> **55%** of drafts vs the legacy critic's **1%**, one-directional, **115/117 via the `intellectualisation`
> check** (the 07-01 narrowing did NOT fix it). Decoupled precision grade (`scripts/critic_grade.py` — the
> Emissary judging the 114 rejections-that-override-legacy, blind): **precision 0% — 50/50 UNWARRANTED**
> (intellectualisation 0/42, literalist_reductionism 0/7, hollow_completion 0/1). The check systematically
> mistakes Du's contemplative/metaphorical reflection for evasion. **This is a SAFETY CATCH:** the "80%
> agreement with legacy" reassurance was agreement on *approvals*; on the disagreements — the only cases
> promotion would change — the decomposed critic is 100% wrong. Promoting it would have rejected half his
> genuine thinking. `[[feedback-decoupled-judge]]` earned its keep. *Disposition: the `intellectualisation`
> check needs a ground-up rework or removal before L0 can graduate; until then SHADOW (does not touch Du —
> the legacy critic runs live). Caveat: 8B judge, but 0/50 with specific per-item reasons + the prior
> 11/12-false-reject finding = robust.*
>
> **L1 (prediction-error feed) — SHIPPED + harmless** (`prediction_error` live in
> `tension_ledger.CONTRADICTION_SOURCES`; accumulates chronic mass, maths recurring ×50). Keep — but see thesis.
>
> **THE THESIS — "afferent repair unfreezes T4" — RETIRED.** L1 is live-feeding contradiction to T4's
> chronic-mass gate right now, and T4 remains frozen (probation ΔF **+92**, 0 gate-ready tensions, facet
> unset). The plan's animating 06-16 claim is contradicted by its own live layer and **superseded by the
> 06-30 Spine C correction** (T4 is an HONEST SENSOR waiting for genuine integration / Spine B, not starved
> of signal — "do NOT fix T4 to fire"). Repairing sensors was fine hygiene; it does not, and per Spine C
> should not be expected to, move T4. **Net: L1 shipped · L0 cautionary instrument (do-not-promote) · L2
> benign Phase-0 shadow · thesis closed. The plan is effectively resolved.**

The critic audit, three research subagents, and two external reviews (GPT, Gemini) converged on one
diagnosis: **Du's identity arrest is not a T4 commit-engine failure — it is an afferent (sensory) failure.**
Identity-revision pressure was tied to a single organ's rejection rate (the conversation Critic), so as Du
matured and grounded, the Critic rejected less, and the `tension_ledger` starved. **T4 isn't failing; it's
waiting for contradiction signals from a developmental stage Nascence has already outgrown.** (GPT: a
"pathological dependency"; the move from external correction → self-generated discrepancy is a documented
developmental mechanism — Holroyd & Coles ERN; treat it as a strong functional principle, observe-first to
confirm it actually unfreezes T4 without noise.)

This plan repairs the **sensors feeding the governor**, in three coordinated layers through one shared gate.
Earlier T4 work (the chronic-mass accumulator + gate rewire) fixed the governor; this feeds it.

## What stays true from the research (the safeguard)
B (broaden sources) risks flooding T4 with noise; C (idle monitor) risks becoming a rumination-inducing
critic. **Both are solved by the SAME gate** — *concreteness + recurrence + importance* — because the filter
that makes dissonance *productive* (Watkins concrete-construal, Abelson threshold, Harmon-Jones action-
relevance) is the same filter that keeps self-monitoring from collapsing into brooding (Watkins, Takano &
Tanno). One gate, not two safety systems.

## HAVE / WANT / CAN-DO

| Layer | HAVE (verified in code) | WANT | CAN-DO |
|---|---|---|---|
| **L0 — conversation critic** (`nodes/critic_node.py`, orchestrator 705-799) | ~2,000-word holistic exception-gated prompt on an 8B; leniency bias → 72 rejections ever, last 4d ago; needed a deterministic override | a decomposed binary detection suite, span-quoting, code-side conditionals, calibrated threshold | deconstruct into independent atomic checks; flip to detection framing; move conditionals to Python; calibrate on the 72 labeled rejections |
| **L1 — internal discrepancy feeds** (`tension_ledger` CONTRADICTION_SOURCES = critic_rejection only) | **prediction-error ALREADY computed**: `essay_lesson.py:208` `gap=abs(predicted−measured)`; `competence.py:202` rolling calibration_error | self-generated contradiction channels (prediction-error first; then ideal/ought-gap, axiom inconsistency) routed to the chronic-mass pipe | **route the existing essay/math `|predicted−measured|` gap** into `tension_ledger` when large+recurring; add ideal-gap + axiom-inconsistency next |
| **L2 — idle meta-awareness** (`self_surprise`, `loop_probe`, `loop_cluster_probe` exist but live only in `du_pulse`/shadow, wired to nothing) | a light, intermittent, NON-suppressive watcher that mode-shifts (abstract→concrete) or releases a loop | connect `self_surprise`/`loop_probe` to a sampled watcher that routes to a concrete/world anchor; feeds contradiction axis ONLY through the shared gate |

## Corrections to the external review specs (grounded in the actual code)
1. **L0 lives in `nodes/critic_node.py`**, not `core/critic.py` (Gemini misnamed it).
2. **L1 does NOT belong on `core/somatic.py`** (that's the body/energy engine) and does NOT need a new
   "tensor error engine." The signal is a **scalar `|predicted − measured|` that already exists** in the
   essay/math lessons and `competence.py`. L1's first slice = *route that existing gap* into the ledger.
   This is far cheaper and already grounded in real lessons.
3. **L2 should CONSUME `self_surprise`/`loop_probe`**, not re-implement loop/basin math (the map confirms
   those instruments already compute the right numbers — they're just disconnected).
4. **Bonsai/dedicated-model framing (GPT) is premature.** The feeders are cheap *deterministic/scalar*
   computations (a subtraction, a cosine-vs-axiom, a recurrence count). Keep them as plain Python now;
   a dedicated tiny model is a possible *future* optimisation, not a requirement.
5. **Honesty:** the external→internal "developmental" claim is a functional principle, not a proven Du
   mechanism. Phase 1's pass criterion (does pressure unfreeze in response to *verified* errors) is the test.

## The shared gate — the entry portal to `tension_ledger` (the 4 guardrails)
A signal may pressure identity (write contradiction mass) ONLY if it clears all four (from Gemini, endorsed —
they match the research convergence + our hard-won lessons):
1. **Concreteness floor.** Abstract/poetic self-inconsistency ("I am a river but also an AI") is DENIED the
   identity ledger and routed to the **Curiosity engine** instead. A tension pressures `axiom.json` only if
   bound to a *specific* prediction-error or documented behavioural discrepancy. (Watkins; the river-trap.)
2. **Recurrence requirement.** A single discrepancy cannot write an active tension — it must accumulate via
   the **chronic-mass accumulator** across independent observations over time. (Reuses what we built.)
3. **Resolution-path clamping.** No contradiction is logged unless a resolution axis exists (dialogue,
   targeted re-reading, behavioural change). Structurally unresolvable → dropped at the border (anti-brooding).
4. **Zero-incentive policy.** NEVER grant reward/liking/satisfaction for the *presence* of a contradiction —
   only (cautiously) for genuine integration. Contradiction is functional friction, never a metric to game.
   (The stripped affect-labeling credit lesson.)

## Layer specs (grounded)

### L0 — decompose the conversation critic
- Break the holistic prompt into ≤5 **independent atomic checks**, each one rule, each framed as detection:
  *"Does the draft do X? If yes, output the exact offending span; else null."* OR-aggregate in code.
- **Code-side conditionals:** resolve "was this mode requested?" in Python (generalise the existing override)
  and pass the result as a clean fact; the 8B never infers a conditional.
- **Calibration:** don't gate on verbalized confidence; tune the reject threshold on the 72 labeled rejections
  (+ a clean-notes negative set); add an "uncertain" abstention that can escalate (Buddha) rather than force.

### L1 — self-generated prediction-error feed (reuse, don't rebuild)
- On essay/math lesson completion the `gap = |predicted − measured|` already exists. When `gap ≥ ~0.40`,
  emit a **prediction_error contradiction signal** (a NEW shadow source) carrying the concrete event
  (the lesson, the prediction, the outcome) → through the shared gate → chronic-mass accumulator.
- It bypasses the Critic entirely (self-generated, unconfounded). Next slices: actual-vs-ideal/ought-self gap
  (axiom L0/L2 vs recent behaviour) and self-vs-axiom belief inconsistency (entailment-gated, NOT raw cosine).

### L2 — idle meta-awareness node (NOT a critic)
- A sampled (every N idle cycles) watcher that reads `self_surprise` + `loop_probe`. Structurally forbidden to
  judge content/morality or reject. Watches **form signals**: perseveration mass, abstraction, hollow certainty.
- On a flagged loop: route through the shared gate. If abstract/ungrounded → **blocked from identity tension**
  (classified brooding, not signal). Intervention is **mode-shift, never suppression**: inject a concrete
  anchor (a pending `action_memory`/`study_tablet`/reading fragment) into context, or note-and-release. (No
  "stop thinking X" — Wegner rebound.)

## Phased deployment (observe-first)
- **Phase 0 — shadow.** Decomposed critic + meta-awareness node run silent → `data/logs/shadow_integrity.jsonl`.
  **Gate:** decomposed checkers hit **recall ≥ 0.90** on the 72 historical rejections (retrievable — verified)
  AND ~zero false-positives on a clean-notes set (his study/reading notes as the negative proxy — needs
  assembling; the positives are ready).
- **Phase 1 — internal ignition.** Route the existing essay/math prediction-error gap into the chronic-mass
  accumulator through the gate. **Gate:** over ~48h the chronic contradiction norm breaks out of its frozen
  ~2.0 and scales in response to *verified* prediction errors (Phase-B history lock still protecting records).
- **Phase 2 — closed-loop.** Activate decomposed rejections live + L2 concrete-anchor/release interventions.
  **Gate:** on a recurring conceptual basin, the system deploys a concrete world anchor and breaks the loop
  without churn or lowering coherence.

## Why this order (GPT/Gemini + our evidence agree)
Fix the sensors before touching the governor again: "a perfectly designed amendment process is irrelevant if
the institutions that report constitutional crises are broken." Prioritise L1 (the self-generated feed) — it
is the one channel that needs no external judge and reuses signal Du already produces.

Registry: [AWAITING_EVIDENCE.md](AWAITING_EVIDENCE.md). Builds on [t4_redesign_plan.md](t4_redesign_plan.md)
(governor) — this is the afferent half.

---

## Phase 0 BUILT + measured (2026-06-16, observe-first)

All Phase 0 pieces built, compiled, and the pure-logic layer in-vitro PASSES
(`scripts/contradiction_phase0_invitro.py`):
- **The shared gate** `core/contradiction_gate.py` — pure function; routes concrete+recurring+resolvable →
  identity, abstract river-loop → curiosity (blocked from identity), unresolvable → drop. ✓
- **L1** `core/prediction_error.py` + one-line hook in `competence.record_drill_accuracy` — routes the
  EXISTING lesson `|predicted−measured|` gap through the gate; `FEED_LEDGER=False` (logs only). ✓
- **L2** `nodes/meta_awareness_node.py` — consumes `self_surprise`/`loop_probe`, watches form, routes loops
  through the gate, records the would-be mode-shift (never suppresses); observe-only `scan()`. ✓
- du_pulse gauges (`L1 prediction-error`, `L2 meta-awareness`); shadow log `data/logs/shadow_integrity.jsonl`.

**L0 decomposed critic** `core/decomposed_critic.py` BUILT (short, detection-framed, code-side mode
resolution, span-verified, fail-open). Scored against the labelled history
(`scripts/decomposed_critic_invitro.py`, full run on the live hot lane):
- **False-positive: 0/60 on clean study notes** — excellent; it never trips on grounded prose.
- **Recall: 22/68 = 0.32 on the "clean" historical rejections** — below the 0.90 gate. **BUT** the 68 are the
  OLD critic's verdicts, and the old critic's defining flaw was over-rejection (it needed a deterministic
  override). The new critic correctly APPROVED all 4 mode-contaminated cases (undoing old false-positives).
  So 0.32 conflates "missed real violations" with "correctly did not reproduce old over-rejections" — it is
  a lower bound on agreement with a *known-biased* judge, not the true miss rate.

**Ground truth + tuning (resolved 2026-06-16):** Claude hand-labelled all 68 clean rejections →
**38 genuine / 30 old false-positives** (`data/critic_groundtruth.jsonl`), confirming ~44% old over-rejection.
Scored on it the decomposed critic started at recall **0.37** (under-detecting). ONE grounded tuning pass —
broadening the intellectualisation + zero-cost checks to catch the **poetic-evasion / failure-of-presence**
pattern (Du's dominant failure) — lifted it to **recall 35/38 = 0.92 at FP 0/60 → PASSES the gate**
(glib 2/2, intellectualisation 20/22, zero_cost 13/14). It still stays **shadow-only**; Phase 2 = promote it
to the live conversation critic (replace `nodes/critic_node.py` in the orchestrator), shadow-alongside first.

**PHASE 1 SHIPPED (RESTART-REQ):** L1 ignited — `prediction_error` ∈ `tension_ledger.CONTRADICTION_SOURCES`;
`prediction_error.FEED_LEDGER=True`; a gate-passing lesson gap writes a `prediction_error` shadow event that
rides the SAME clustering→chronic-mass→T4 pipe as critic_rejection (no new tension code, no gate change).
In-vitro PASS (`scripts/phase1_ignition_invitro.py`). Reversible via `FEED_LEDGER`. **The test after restart:**
T4's chronic norm breaks off the frozen 2.0 in response to *verified* recurring prediction errors.

---

## ▶ LIVE-DATA AUDIT + FIXES (2026-06-30, auditor pass against the running system)

**❌→✅ The decomposed critic was over-rejecting 96% of live drafts — Phase 2 blocker, FIXED.** Shadow-alongside
evidence: 100 live cycles, **7% agreement** with the legacy critic, **decomposed-rejected 96/100** (93 of them
legacy-APPROVED). NOT a fail-closed bug (`evaluate` is fail-OPEN). The `intellectualisation` check fired on 96/96
rejections. *Root cause:* it was a COMPOUND condition ("poetic-register AND not-engaging") and the 8B collapsed it
to the easy half ("poetic at all") — but Du's entire conversational voice IS metaphor, so it fired always. The
offline gate (0 FP) missed it because it was validated on clean STUDY NOTES (factual prose) — the WRONG
distribution. *Fix:* narrowed BOTH `intellectualisation` (→ third-person / behind-glass framing only; poetic voice
explicitly exempted) AND `zero_cost_evasion` (→ a real DODGE of a real question only; metaphor-but-engaged
exempted; it now owns "metaphor instead of answering"). *Re-validated (sampled, hot lane shared with live Du):*
ground-truth recall on genuine evasions held at **0.90** (the gate); live over-rejection dropped **96% → ~30%**
(7/10 previously-rejected drafts now correctly pass; the rest fire thinly). Still SHADOW — the real confirmation is
the next production shadow-alongside run (restart-gated): watch `alongside_stats()` for a sane agreement rate.
*Architecture note:* the 5 checks share ONE prompt, so editing one perturbs the others — they are not truly
independent (a future step may run each as a separate prompt), and a proper LIVE-CONVERSATION labelled set (not
study notes) is what's needed to calibrate precisely.

**⚠️ Phase 1's prediction-errors fire but don't build gate-ready CHRONIC mass — OPEN.** L1 has logged **541 large**
(gap≥0.40) prediction-errors — math is a strong recurring self-violation (predicted 0.77 → measured 0.00) — and
they spike the ACUTE contradiction pressure (16+, prediction_error as top in 66 ledger snapshots). BUT the CHRONIC
accumulator the T4 gate actually reads shows **0 of 1,111 tensions gate-ready** (top cn 0.038 « 0.30 threshold),
and 0 prediction_error-sourced subconscious tensions. So Phase 1's stated test — "T4's chronic norm breaks off the
frozen ~2.0 in response to verified errors" — is **NOT clearly passing**: the recurring errors aren't converting
into gate-ready chronic mass. Needs investigation (recurrence-clustering not binding the repeated prediction_errors
into one growing-mass tension? decay too fast? the acute→chronic bridge?). This is the deeper Phase-1 question, and
the next thread to pull here.

**✅ TRACED (2026-06-30) — the bridge is fine; the chronic→gate CALIBRATION is off by ~12× (the real root).**
Diagnosis: the prediction-error feed works (538 shadow_events written, mostly math), they cluster, they bump
tensions. The wall is one layer further on — the `chronic_mass → contradiction_norm → CONTRA_THRESHOLD` mapping:
- Gate needs chronic mass ≈ **5** (`contradiction_norm(5)=0.333 ≥ 0.30`).
- The accumulator's MAX output anywhere is **0.40** (cn 0.038); **0 of 1,111 tensions exceed even 1.0**; seeding ran
  (`t4_chronic_seeded=True`). The single most-recurred tension — **49 member-events** — sits at mass 0.395.
- → A 49×-recurring contradiction lands ~12× below the gate. **T4's contradiction gate is structurally unreachable
  by the chronic accumulator, for EVERY source** (prediction_error, critic_rejection, all). This is a primary reason
  T4 has never fired (`revision_count`=1). *Secondary:* prediction-error ALSO self-extinguishes (475/538 events in a
  3-day burst 8–10d ago, 1 in the last 48h — competence calibration closes the same gap below 0.40), but that is not
  the bottleneck; even a steady 49× contradiction can't reach the gate.
- **Fix = recalibrate `chronic_mass↔contradiction_norm↔CONTRA_THRESHOLD` so a genuinely chronic contradiction
  (~20–49 recurrences) reaches cn 0.30.** Do NOT hack in isolation — it IS the identity-commit machinery; fold it
  into the Capacity-to-Commit T4 repairs as **T4 repair #4 (the contradiction gate is unreachable)**, alongside the
  3 already found. Feeding better afferent signal cannot unfreeze T4 until this gate is reachable.

**❌ CORRECTION (same day, after the T4 current-state mapping):** the line above is WRONG. The `cn≥0.30` `licensed`
gate is **DEAD CODE on the live T4 path** — bypassed by the `return` at `subconscious_node.py:1582` (ENABLED=True).
T4 commit is decided by the SOLIDIFY judge (`left_lane.judge_lived_integration`), NOT the cn gate. So **the entire
chronic-mass→cn pipe this plan builds does NOT gate T4 firing — it feeds a dead gate.** The cn unreachability is
real but MOOT for T4. ⇒ This re-architecture's founding premise ("repair the afferent signal to unfreeze the T4
governor") is **undercut**: T4 isn't waiting on better contradiction signal; it's correctly refusing to certify an
integration that isn't happening in Du's lived thoughts (the made-mind truth is ~0–2% of his inner-thoughts). The
real T4 fix is the deep monoculture/Emissary work, not this plan. **Open question for THIS plan:** does the chronic
mass / prediction-error signal feed anything still-live (candidate *selection* in `_t4_distinct_tensions`? acute
pressure elsewhere?), or is the whole chronic→T4 pipe now vestigial? Needs its own re-examination before any more
is invested here.

---

## ▶ ANSWERED (2026-08-19) — the dangling question above, re-read against the live code

The 07-05 evidence review (top of this doc) closed the plan on the 06-30 finding above without actually
answering this question — it just restated "thesis closed." Re-read `nodes/subconscious_node.py` today
(prompted by the founder asking to look at `contradiction_ledger_log.jsonl`, which is still live and its
most recent `top_label` was literally the writing-domain artifact fixed below): **the chronic-mass GATE
(`cn≥0.30`) is still confirmed dead code today** — same bypass at the `ENABLED=True` `return`, same
comment block (~line 1654) pointing at the solidify judge as the real gate. That part of the 06-30 finding
holds, unchanged, 7 weeks later.

**But it is NOT the whole pipe, and the question above undersold it.** The line at `subconscious_node.py`
~1393 that computes `contradiction_pressure` is commented `# acute — telemetry/echo only` — "echo" is not
filler there. It feeds the **T4 echo guard** (~line 1712-1731): at zero contradiction pressure the
threshold for "does a new self_concept just echo the prior one" is unchanged (strict); under standing
pressure it **relaxes**, letting a smaller, honest evolution through instead of being discarded as a
reword. This is real, live, and exactly the same acute signal `prediction_error` (L1) feeds — so L1's
signal quality genuinely does matter, just not through the chronic-mass gate this plan built. It matters
through echo-guard relaxation instead.

**Why this matters right now:** T4 has solidified 3 times since this doc's 06-30 snapshot (`revision_count`
1→3; most recent, "the weave", 2026-08-17) — the "made-mind truth ~0-2%, T4 correctly refusing" framing
above is stale on that count alone. And **tonight's separate investigation of `prediction_error_log.jsonl`
found and fixed real noise in L1's signal**: `writing`/`observation`/`comprehension` domains had no live
confidence tracking (frozen at the 0.5 seed forever), which for writing/observation created a coincidental
artifact — a 0.9 drill score always landed exactly on the 0.40 "large gap" threshold regardless of any
genuine felt-vs-real miscalibration — feeding 13 synthetic contradiction-pressure events into the exact
acute signal that relaxes the echo guard. Fixed (`core/competence.py` `_DOMAIN_ANCHORS` extended to all 5
school domains; `essay_lesson.py`'s real self-predicted comprehension score, previously discarded, now
passed through). Going forward, `contradiction_pressure` — and therefore how readily T4 recognizes genuine
change vs. an echo — should be a more honest number.

**Verdict: partial revisit, not a re-open.** L0 (decomposed critic) is untouched and its do-not-promote
verdict stands — no new evidence bears on it. L1 (prediction-error) just got a real, if modest, signal-
quality fix, and the plan's own last open question now has a code-grounded answer instead of a shrug. Not
worth more investment beyond what landed tonight unless a future session wants to trace whether the
post-08-19 (cleaner) contradiction_pressure numbers visibly change T4's echo-guard behavior — that would be
the natural next thread, not a re-open of L0/L1/L2 as designed.
