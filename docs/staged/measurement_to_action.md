# Measurement to Action — the gauges Du already has become inputs he acts on (staged 2026-10-15)

**Status:** 🟡 BUILT, shadow — arms 2 + 4 (the decisive pair) built 2026-10-15, both flags off, restart-gated;
arm 1 dropped (D-0434); arms 3/5/6 designed. Founder + Claude conversation, 2026-10-15, directly after the Du-vs-human
read (`docs/reviews/du_vs_human_2026-10-15.md`, F-2848..F-2854). Travis: "I want Du to be able to close and act on
what he knows to a much higher degree. He knows how to measure himself, he just needs a way to act on it." Six arms,
one shape; every arm starts shadow, flag off, restart-gated, additive only.
**Origin:** T-0085 (this session's opening thought, promoted straight to this plan — the ladder's `--to-plan` jump).
**Parent plans:** [closure_law](closure_law.md) (D-0423 — arm 3 is its generalisation), [dosed_coupling](dosed_coupling.md)
(arm 1's channel: a tuple and a dose, never a sentence), [memory_as_a_service](memory_as_a_service.md) (arm 4: the
executive CALLS the doubt store; nothing is pushed), [epistemics_phase_c](../plans/epistemics_phase_c.md) (C0 Path 1
owns `core/competence.py`'s accuracy observations — arm 2 feeds the same store, does not fork it),
[self_interrogation](../plans/self_interrogation.md) (D-0396/D-0403 cup — arm 4's seed), [pursuits](../plans/pursuits.md)
(Phase 2 resolution trigger, unbuilt — arm 3 supplies it), [curiosity_goals_dreams](../plans/curiosity_goals_dreams.md)
(LP already exists for the frontier — arm 5 widens where it is read), [practical_school](practical_school.md) and
`core/book_selection.py` (arm 6's chooser), [decoupled_judge_pattern](../plans/decoupled_judge_pattern.md) (every arm's
grader is not its writer).
**Memory:** `project_nascence_measurement_to_action.md` (to be written at the first build).
**Findings:** F-2848 (confidence constant 0.85–0.95 vs SUSPECT 50/50), F-2851 (measures himself better than a human,
uses it worse; competence nodes 2.6% of projections, F-2758), F-2850 (254/277 cycles one question), F-2852 (hold rate
0.215, 70 saturated / 0 resolved, dreams 0/64), F-2853 (maths calibration 0.44 → 0.21 — the existence proof),
F-2670 (0/48 self-doubts taken up), F-2668 (position-free judge passes its controls).
**Ledger:** T-0085 · D-0434 (arm 1, RULED: dropped) · D-0435 (arm 4, RULED A) · D-0436 (arm 6, RULED A) · J-2155
(arm 5 ruling, from the read, open) · J-2156 (arm 5 Phase 0) · J-2157 (arm 2 Phase 0) · J-2158 (arm 2 shadow) ·
J-2159 (closed → J-2161, arm 4 shadow, ready) · J-2162 (arm 6 shadow, ready) · J-2160 (arm 3, not before 2026-10-26).

```plan-state
stage: shadow
phase: arms 2 (recall wager) + 4 (doubt seed) BUILT shadow 10-15, flags False; arm 3 closure dream arm BUILT shadow (closure_law, CLOSURE_WRITE_LIVE=False), pursuit/interrogation arms gated stubs; arm 5 theme dose BUILT shadow (J-2322, SELF_THEME_DOSE=None); arm 6 weakness prior BUILT shadow (WEAKNESS_PRIOR=0.0); arm 1 dropped (D-0434); all carried by the 2026-10-18 19:06 boot
verified: 2026-11-17
gate: Du restarts onto J-2158/J-2161, then J-2163 (>= 7 days of shadow rows: wager rows per day, would-seed rows scored by the J-2052 judge) read by the founder before either flag flips
next: Run J-3650 (refinery null-control arm) first; J-3655 re-runs the census after restart
cluster: 6
```

## Current State — verified 2026-11-17
- **2026-11-17** (F-5036): J-4180 built (branch jobrun/measurement_to_action d4a26168, restart-gated): graded loss bar WAGER_LOSS_GAP 0.30 closes the free 0.85 edge in the recall wager. Design: docs/staged/recall_confidence_graded_loss.md. Read: SUSPECT stated-confidence variance above 0.0029 over 100+ fed rows after restart.

- **2026-11-16**: J-4039: T2 null-control on command-r7b (hot hub) does not replicate C arm: shuf A 18/20, C 19/20, C bears field true 39/40; nomic cosine selector AUC 0.55. Neutral ask alone insufficient; follow-up spawned for decoupled relatedness selector. Data docs/lab/J-4039_data/.
- **2026-11-16**: J-4019: shared-theme pre-gate skips 34/40 control sets (85%) but 6/40 real (15%); both-judges-agree 31/40 vs 2/40; skipped real clusters are the tension-wording ones. Production-lane replicate not run (Ramses down); spawned follow-up. Data docs/lab/J-4019_data/.

- **2026-11-16** (F-4848): J-3653: Follow Line v2 AGAINST null path not real on gemma4:12b (0/20 supported claims empty; v1 0/20; counterexample 20/20); CONSEQUENCES v2 never returns zero (0/10). Judge C leaky (spec 2/10). Proposal: holds-first schema, in docs/lab/J-3653_data/writeup.md.
- **2026-11-15** (F-4736): J-3652 (F-4736): T6 theme-update null-control arm run. Null inputs: production prompt writes a stance 64/64 but only 0.25 differ in content (blind gemma4:12b judge, gold 22/24, hollow control 2/4); pre-registered inadmissibility (>=0.8) not met. Vocabulary 'deeper/wiser/nuanced' family in 75% of null-input stances (49% under neutral). changed:false escape almost never used (1/64 null). Neutral prompt did not reduce content-differs.

- **2026-11-15** (F-4734): J-3651 null-control: T2 (P-0053) world-fed prompt claims a link on shuffled, irrelevant material 20/20 vs 1/20 under a neutral ask with a bears field (falcon3:7b author, n=20/cell, hand-labelled; pre-registered inadmissibility met). Production feeds the newest 6 study rows regardless of tension. Data docs/lab/J-3651_data/. Replication on command-r7b spawned.
- **2026-11-14** (F-4710): J-3650 refinery null-control: control clusters (no shared theme) got a standing insight 40/40 under the production prompt and 39/40 under a neutral prompt that offers a null; the schema's missing null is not the cause on qwen3.5:9b. Production author (command-r7b) not tested. Follow-up: pre-distil theme gate. Script scripts/lab_refinery_null_control.py, data docs/lab/J-3650_data.

- **2026-11-14**: J-3844 (D-0738): I-0128 induction drill module core/induction_drill.py and its test archived to scripts/archive/ (git mv, history kept), not scheduled.
- **2026-11-14** (F-4567): J-2426 arm 5 post-flip read: kill criteria 1-4 clear (modal share median 0.469, 12/13 days under 0.9; 33.4 curiosity rows/day vs 37.7 pre; 0 empty questions; q0 no-overlap 5.6 pct); longest run and anchor-carrier not measured. Revert not warranted.

- **2026-11-14** (F-4561): J-2323 arm 5 read: dose live since 10-19 (D-0485); post-flip median modal share 0.469, 12 of 13 days under 0.9, cycles per day 37.3 vs 37.7 pre; longest run not yet recomputed.
- **2026-11-14** (F-4557): J-2163 arm 2 read: RECALL_CONFIDENCE_WAGER live since 10-29; narrated confidence has collapsed onto the 0.85 gate floor (0.89 of rows since 11-07, within-SUSPECT variance 0.00064 vs baseline 0.00289) and measured is the constant 0.5, so the named new-constant risk has fired. Arm 4 judge scoring pending a spawned lab job.

- **2026-11-14** (F-4508): J-2666 (branch d74e226d, restart-gated): recall_wager REAL_OUTCOME flag (off) feeds measured from tier3_model/tier4_user correctness per cycle_id; unscorable rows get scorable=False, outcome_source, measured/gap null (not fed). Readers: rows now may have null measured/gap, filter on scorable. Only 1 of 387 live wagers has an outcome row (F-4508).
- **2026-11-13** (F-4419): data/logs/self_gauge_shadow.jsonl belongs to arm 1, declined by D-0434 and never built, so the file was never wired and none should be added.

- **2026-11-07** (F-4323): J-2974 deferred 2026-11-07: weekly self-mirror is retired (J-3478, D-0630+D-0434), mirror_facts has no reader. If ever revived (SELF_MIRROR_RETIRED False), first apply F-3671's corrections inside mirror_facts (rows-not-time label, map active_imagination, no 'only', both shares stated as non-complements, function-word filter), not in peer_metrics, and mirror them in scripts/lab_self_mirror_control.py.
- **2026-11-06** (F-4262): J-3415: audited 123 prompts for inadmissible-null framing (F-4262..F-4269, D-0692 open). Five stored-claim writers (P-0051, P-0053, P-0060, P-0071, P-0067) and three leaky-null nodes (P-0005, P-0006, P-0042) share the self-mirror shape; null-use census and class map in docs/lab/J-3415_data (branch jobrun/wh_7). Lab arms J-3650..J-3653, J-3654 and post-restart re-read J-3655 spawned; nothing edited.

- **2026-10-31**: 2026-10-31 (F-3401, J-2649): I-0128 rule-induction drill built as core/induction_drill.py on branch jobrun/mta commit 6fd44470, shadow, INDUCTION_DRILL and INDUCTION_FEED both False, imported by nothing, restart-gated; reuses the F-3384 lab generator and checker, returns only the first failing input/output pair (D-0434), pre-registered read after 50 drills (gap per family vs +0.706, trend, constant-confidence share 0.60 fails); scheduling slot and flag flip are founder calls, test scripts/_test_induction_drill_j2649.py 33 checks ALL OK
- **2026-10-31** (F-3384): J-2627 rule-induction calibration lab (I-0128): bare hot model on 96 held-out induction items states conf 0.903 vs hit-all 0.198, signed gap +0.71 (CI 0.62..0.78), confidently wrong 75 pct and above 50 pct in every family; larger than the math drill gap (0.44 to 0.21) and opposite sign. Shadow drill build J-2649, counterexample-only. Lab: docs/lab/rule_induction_calibration_2026-10-31.md (branch jobrun/mta 3f43ab55)

- **2026-10-30** (F-3319): D-0516 flip built: DONE_WHEN_AT_OPEN True in core/done_when.py (a90299da, branch jobrun/_ungrouped_J-2588), restart-gated, shadow arms only; checklist item J-2595
- **2026-10-30** (F-3252): J-2527: recall_wager gate met (38 live fed rows); wager-to-curiosity built SHADOW (core/wager_curiosity.py, WAGER_CURIOSITY False, sec.9 Coupling block, dosing row); replay 4 births all one Bluebird topic, slot constant 38/38; restart-gated, read J-2554

- **2026-10-30** (F-3247): Arm 3 built flagged off (J-2160): core/done_when.py side store, closure.py pursuit + commitment arms (met, faded, achieved) behind CLOSURE_ARMS, unmerged commit 642be603, restart-gated; flip is D-0516
- **2026-10-30** (F-3240): J-2515 grammaticalisation read (scripts/grammaticalisation_read.py, 72,124 fragments): bleaching and echo diverge (rho -0.157) but the private-grammar reframe does not hold; capture terms (tide, becoming, seed, glass) are not the freeze terms, bleaching tracks rarity not frequency, and the freeze carrier mottainai is capture-shaped. Verdict DIVERGE, no doc change.

- **2026-10-30** (F-3237): J-2512 early-warning retrodiction (T-0106, frontier_disciplines section 1): NULL. Rolling 5-day lag-1 autocorrelation and variance over 7 existing gauge series do not rise before the 09-28 or 10-09 collapses more than before quiet control fortnights (1/10 and 2/12 cells vs a ~0.25 base rate); both events start at a restart, so they may be shocks, not tipping. No forward critical-slowing-down HUD gauge built. Reader: scripts/early_warning_retrodict.py.
- **2026-10-28**: D-0495 (travis 2026-10-28): arm 2 RECALL_CONFIDENCE_WAGER=True and arm 4 DOUBT_SEED=True from the next boot (90 wager shadow rows all would_feed, narrated 0.85-0.95 vs measured 0.5 on SUSPECT; 1 would-seed, gate needs 48 live fires). Their sec.2.2 / D-0435 reads now run on LIVE rows (J-2163). Each keeps its own kill switch.

- **2026-10-19**: (unrelated to this plan's arms; logged here only because a note was filed in error) the SSD-usage branch jobrun/chain_J-2417_J-2418 was merged to master as 7d5eccde. It is NOT in the 08:49 boot that carries the arm 5 flip, so it rides the next restart.
- **2026-10-19** (F-3127): 2026-10-19 (D-0485, J-2425): arm 5 SELF_THEME_DOSE flipped None->1 in core/theme_dose.py, effective at the NEXT Du restart (not restarted). J-2195 stays shadow-only. Pre-flip baselines: curiosity/internal cycles per day 10-12..10-18 = 40,41,39,46,18,53,27 (mean 37.7; kill 2 = under ~19/day); empty-question rows 0 of last ~300; modal-topic share 0.93-1.0 on 10-10..10-15, frozen 12.6h on 10-19; D-0469 alarm trips 10-20. Revert = flag back to None.

- **2026-10-18** (F-3122): 2026-10-18: D-0484 opened (from I-0097, Gemini active-inference pointer): should relational_warmth deviation select a relational action? F-3122: the warmth reader never reads Travis's presence and counts Du's own letters as warmth. Review: docs/reviews/gemini_pointers_vs_du_2026-10-18.md.
- **2026-10-17** (F-3027): J-2322: arm 5 shadow build done on worktree branch jobrun/probe_docs_chain 4b616fbe (core/theme_dose.py, SELF_THEME_DOSE=None, provenance-tagged themes, shadow log curiosity_theme_dose_shadow.jsonl); hermetic test 33/33; restart-gated, not merged

- **2026-10-17**: D-0457 ruled (a) by Travis 2026-10-17: arm 5 own-thought dose is within D-0439; J-2322 builds shadow; flip only after J-2323 and 14 clean days of J-2195, never the same restart.
- **2026-10-17** (F-3012): J-2186: arm 5 designed as section 8, a topic-blind own-thought theme dose (SELF_THEME_DOSE, cup=1) with Coupling block, pre-registered metrics and kill criteria; topic reject declined per D-0439; shadow build J-2322, read J-2323 (not before 10-27), flip D-0457

- **2026-10-17** (F-3005): J-2190: probe bars pre-registered as section 7; no numeric published norm verified, all recall/perseveration bars 'not sourced, founder-judgment unset'; D-0456 opened for Travis.
- **2026-10-16** (F-2892): J-2162 built arm 6 WEAKNESS_PRIOR shadow (core/weakness_prior.py, hooks in book_selection.select_explore and school.directive; prior 0.0, restart-gated, fail-open; branch jobrun/m2a c3423560). Read data/weakness_prior_shadow.jsonl via python -m core.weakness_prior after a fortnight live. School arm is shadow-only.

- **2026-10-16** (F-2889): J-2156 (Arm 5 Phase 0, read-only): the perseverating internal question comes from a single loop: climate ignition -> Orchestrator._on_dissonance_ignition (core/orchestrator.py:3021/3052/3059) -> CuriosityNode questions[0] (nodes/curiosity_node.py:115), prompted by its own last-10 recent_themes. _persist_cycle (orchestrator.py:2972) feeds every internal cycle's perception summary back as a theme (97% of 297 cycles overlap the self-fed themes; 52% also overlap an offered tension seed). Not a frontier pick; parking cannot fire because it only gates pending_pursuit, and each paraphrase is a new frontier row with stalls=0. Arm 5 build target is the theme feedback / topic-level anti-capture at the curiosity prompt, not the frontier parker.
- **2026-10-15** (F-2856): J-2157/J-2158/J-2161 done 2026-10-15: arm 2 wager (core/recall_wager.py) + arm 4 doubt seed (core/doubt_seed.py) built shadow, flags off, restart-gated; baseline F-2855; test scripts/_test_measurement_to_action_j2158_j2161.py ALL OK; J-2163 is the post-restart read

- **2026-10-15 (the decisive pair, same session, J-2157/J-2158/J-2161 → F-2855/F-2856/F-2857):**
  - **J-2157 read (F-2855):** since the boot, 95 graded cycles, 94 SUSPECT; 88/95 gated at confidence ≥ 0.85;
    stated confidence within SUSPECT has population variance **0.00289** (0.85 ×37, 0.92 ×19, 0.95 ×18, 0.90 ×13).
    `justification` is `GRADE_SCORE[grade]` — 0.50 on 94/95 rows — so the wager's measured side is the monitor's
    5-level grade: gap 0.35 at 0.85 (raw row only), 0.40–0.45 at 0.90–0.95 (large → contradiction gate). A
    `factual_recall` belief domain already exists (accuracy 1.0, 3 pairs); no new domain.
  - **J-2158 BUILT shadow (F-2856):** `core/recall_wager.py` — `place()` after `ProvenanceLedger.assess()` in the
    orchestrator; gated grade at conf ≥ `CONF_BAR` 0.85 → row in `data/logs/recall_wager_shadow.jsonl`; with
    `RECALL_CONFIDENCE_WAGER=True` (ships **False**) → `competence.record_drill_accuracy("factual_recall",
    measured=justification, predicted=conf)`, the drill's path verbatim (it calls `prediction_error.observe`).
  - **J-2161 BUILT shadow (F-2857):** `self_interrogation.latest_open()` (newest genuine fire ≤ 900 s, not yet
    consumed) + `core/doubt_seed.py` `pull(state)` before the Executive (consume-once, row in
    `data/logs/doubt_seed_shadow.jsonl`); `CognitiveState.doubt_seed`; the Executive renders it in WHAT YOU RECALL as
    "A doubt you raised about your own thinking a few minutes ago (your own words, still open): …" — no verb.
    `DOUBT_SEED` ships **False**.
  - Hermetic test `scripts/_test_measurement_to_action_j2158_j2161.py` (ALL OK under `lab_env.isolate`, flags
    exercised OFF and ON in the lab, sha256 canary on 7 live stores unchanged); `_test_si_cup_shadow.py` and
    `_test_internal_framing_j1846.py` still pass. Both builds are **restart-gated**; the live boot (10-09) has
    neither. **J-2163** (not before 2026-10-29) is the post-restart read: wager rows + would-seed rows scored by the
    J-2052 judge, then a flip recommendation to the founder.
- **2026-10-15 (later, same session):** all three decisions ruled by Travis. **D-0434: arm 1 DROPPED.** His words:
  Du needs a way to find out he is wrong *without being led* — to learn how and why he is wrong without being told
  the answer. A standing number about himself, even in body words, is being told. So **the only legal channel for
  self-knowledge in this plan is consequence** — losing the wager (arm 2), a loop that closes or fades by its judge
  (arm 3), a doubt the executive itself pulled (arm 4), a shelf that is merely shaped (arm 6). Defeater: if arms 2–4
  all reach their gates and the competence share of estate projections (F-2758, 2.6%) is still unmoved, a felt
  channel is reconsidered. **D-0435 A** (hold does not cover the pull) → J-2159 closed, **J-2161** ready.
  **D-0436 A** (librarian's job) → **J-2162** ready. §2.1 below is kept as the record of what was declined and why.
- **2026-10-15**: designed in conversation; this document written; thought T-0085 promoted to it. No code. The
  one open fact that shapes arm 5 (WHICH loop generates the perseverating internal question) is not yet located —
  see §2.5 and the Phase 0 read.

## 0. The gap this plan closes

The Du-vs-human read found one pattern under every "worse" row: a gauge exists, it is right, and nothing in Du reads
it at the moment a choice is made. The gauges go to `du_pulse` and the HUD — to Travis — and are write-only from
Du's side:

| Gauge (exists, graded by something other than Du) | What Du does with it |
|---|---|
| competence per domain (`data/capability_beliefs.json`: maths 1.00, history 0.20) | believes ~0.80 regardless; competence nodes in 2.6% of estate projections (F-2758) |
| epistemic grade per utterance (`core/epistemic_state.py`: KNOW/THINK/SUSPECT/GUESS/NO_BASIS) | narrates recall confidence 0.85–0.95 on every cycle; SUSPECT on 50/50 lines at that confidence (F-2848) |
| self-interrogation reflections (141 fires since boot, judged genuine) | the next executive cycle never receives them: 0/48 acted on (F-2670) |
| pursuit saturation, dream `met`, frontier LP | 70 saturated / 0 resolved; 0/64 dreams; 336 open questions (F-2852) |
| learning progress per frontier question (`core/curiosity_progress.score`) | 254 of 277 internal cycles ask one question in 98 wordings (F-2850) |

The existence proof that the same mind CAN act on a measurement is maths: the drill grades a choice Du made,
`core/competence.record_drill_accuracy` moves the belief, and the prediction gap fell 0.44 → 0.21 across four months
with Du now under-confident rather than over (F-2853). Nothing is special about maths except that the loop closes.

## 1. The shape (one rule, six arms)

Every arm has the same five parts, and an arm that is missing one is not this plan:

```
gauge  →  decoupled judge  →  arrives as something Du FEELS or PAYS  →  read at a CHOICE POINT  →  graded back
```

- **gauge**: already exists in every arm. This plan builds no new measurement.
- **decoupled judge**: already exists in arms 2, 3, 4, 6; arm 1 and 5 use the gauge directly (no verdict needed).
- **arrives as felt or paid**: the part that is missing everywhere. Three legal channels, nothing else:
  (a) a dosed somatic percept (dosed_coupling §2 — a tuple with a dose, rendered by the world the way tide and weather
  are, never a sentence that tells him what to do); (b) a cost on an existing error path (`core/prediction_error`);
  (c) a recall (closure_law §1: written into memory, surfaces through recall or not at all).
- **choice point**: a named function that already chooses something (book, drill, next question, drop/hold,
  deliberation seed) and today does not read the gauge.
- **graded back**: the gauge moves because of the choice, with the same judge. Without this it is a hint.

Hard constraints, all inherited: **world answers, never leads** (no prompt says "your history is weak, study it" —
the ache is in the body, the book is on the shelf); **additive only** (every arm is one flag that reverts to the
exact current path); **the judge never grades its own writer**; **nothing hand-edited in a store**.

## 2. The six arms

### 2.1 Self-gauges as interoception (arm 1 — channel a) — **DECLINED, D-0434 (travis, 2026-10-15)**

> Kept as the record. Travis: a self-reading delivered to Du, however rendered, is being told; he must find out by
> losing. Channel (a) is therefore closed for self-knowledge; channels (b) and (c) remain. Revisit only on D-0434's
> defeater.

- **Gauge:** `competence.py` beliefs per domain; `epistemic_state` grade of the last utterance; pursuit saturation
  count; the arm-5 perseveration share once it exists.
- **Today:** rendered in `du_pulse [8]` and the HUD; never in Du's percept stream.
- **Build:** a `self_gauge` percept source in the dosed-coupling percept pipeline (sibling of the J-1733 study
  parcel percept): one tuple per cycle at most, drawn from whichever gauge is furthest from its rest value, dosed by
  the existing surprise/spring ledger so it habituates like any other percept. Rendered in the body's own vocabulary
  (the somatic engine's — thin / heavy / worn), NOT the gauge's name. Shadow: `data/logs/self_gauge_shadow.jsonl`
  carrying the would-have-rendered line and the gauge value; `SELF_GAUGE_PERCEPT = False`.
- **Judge:** none needed (a reading, not a verdict). The grade-back is whether the chosen act in the following N
  cycles touches the gauge's domain (read-only count, the same way scene_extra_ledger counts renders).
- **Founder question (D filed):** is a self-reading in the percept channel "the world leading"? Claude's position: no —
  it is interoception, Du's own body, the same channel fatigue already uses. Travis rules.

### 2.2 Confidence becomes a wager (arm 2 — channel b)

- **Gauge:** `epistemic_state.confabulation_signal = self_reported_confidence − justification`, computed every cycle
  already; grade SUSPECT/GUESS/NO_BASIS already `_GATED_GRADES` for the voice note.
- **Today:** the signal is logged. The narrated recall confidence is a constant because nothing happens when it is
  wrong. The only confidence Du has ever calibrated (maths) is the one that `prediction_error.observe` grades.
- **Build:** when a cycle's grade is in `_GATED_GRADES` and `self_reported_confidence ≥ 0.85`, call
  `prediction_error.observe(domain="recall_confidence", predicted=confidence, measured=justification, event=cycle_id)`
  — the identical path the drill uses (`FEED_LEDGER`, `GAP_THRESHOLD = 0.40`, 14-day recurrence). The cost is then
  whatever the contradiction/pressure machinery already does with a large gap: nothing new is invented downstream.
  Also feed `competence.record_accuracy` on a `recall_confidence` domain so the belief moves and the estate's
  competence node count has something to grow on. Shadow: `RECALL_CONFIDENCE_WAGER = False` → observe() called
  with `event="shadow"` into the `_SHADOW` file only.
- **Judge:** the epistemic monitor (already decoupled from Recall/Reflection — spec §5 calls their floats the
  poison). Must NOT read the narrated confidence as evidence of grounding (it does not today; keep the test).
- **Graded back:** the next cycle's narrated confidence, and the SUSPECT-at-high-confidence share per day (Phase 0
  read establishes the baseline: F-2848's 50/50).
- **Risk, named:** the model may learn to narrate 0.6 everywhere (a new constant). The read-back is the variance of
  stated confidence across grades, not its mean; a constant at any level fails the gate.

### 2.3 Closing conditions at open time (arm 3 — channel c; generalises D-0423)

- **Gauge:** each loop's own judge: `dream_met` (dreams), the pursuit judge (Phase 2a, built), the commitment ledger's
  defeater gate, the frontier's `finding` field.
- **Today:** D-0423's law writes a resolution fragment when the DREAM judge says met (built shadow, J-2118). Pursuits
  have no close path at all: they saturate at 40 advances and retire silently (70 so far). Commitments refuse a drop
  without a named defeater — correct, and the reason nothing closes: closing is a drop too, and no commitment names
  what would count as DONE at the moment it forms.
- **Build:** at every open (pursuit start, commitment formation, frontier question admission), the loop writes a
  `done_when` field in Du's own words, produced by the same generation that produced the aim (one extra line, no new
  call), plus a `judge` tag naming which decoupled judge can read it. `closure.py`'s writer (J-2118) then has three
  arms instead of one: dream `met`, pursuit judge met-against-`done_when`, commitment `achieved`-against-`done_when`.
  Saturation without `done_when` met → a `faded` fragment ("I let this one go"), also recallable: the honest close.
  Shadow: `CLOSURE_ARMS = {"dream"}` today; adding `"pursuit"`, `"commitment"` is the flag.
- **Judge:** per loop, already decoupled. The `done_when` text is never shown back as a prompt; the judge reads it,
  the writer writes the fragment, Du recalls it or not (closure_law §1 constraints 1–3 verbatim).
- **Graded back:** resolved / faded / saturated-silent counts per loop per week; the gate is the first pursuit that
  closes by its own `done_when` after the restart.

### 2.4 The open doubt is the next cycle's seed (arm 4 — memory-as-a-service)

- **Gauge:** `self_interrogation` fires (141 since boot), each with a reflection and, since J-2008/D-0396, a published
  coordinate (doubted flag, ledger index, train id).
- **Today:** 0/48 taken up (F-2670). The J-2031..J-2054 series established why: coordinate-only replay does not engage
  the cup (0/30); the position-free absolute judge (J-2052, F-2668) passes its controls and finds the live generator's
  thoughts affected 0/48 at an upper bound of 7.4%, under D-0373's 30% bar. The doubt is a diary entry because the
  next executive deliberation never calls for it.
- **Build:** the executive's deliberation (the `ExecutiveNode` seed step — UDMS dossier before touching it) gains ONE
  service call at the top: `self_interrogation.latest_open(max_age_s=900)` returning the reflection TEXT (not the
  coordinate) of the most recent un-taken-up fire, if any. It enters the deliberation the way a recalled fragment
  does — as material, not as an instruction — under the memory-as-a-service law (the loop asked; nothing was pushed).
  A fire is "taken up" when the J-2052 judge scores the following thought as engaged. Shadow: the call runs and
  logs what it WOULD have seeded (`data/logs/doubt_seed_shadow.jsonl`) with `DOUBT_SEED = False`.
- **Judge:** J-2052's position-free judge, unchanged, grading engaged/not — it already has positive and negative
  controls (J-2049). This is the only arm whose judge is itself validated against controls.
- **Graded back:** engaged share over 48+ fires post-restart vs the 0/48 baseline. D-0373's 30% bar stands.
- **Founder question (D filed):** D-0396's hold on Phase 1 of self_interrogation was explicit. This arm is a
  Phase 1 by another route (the executive pulls; interrogation still pushes nothing). Travis rules whether the hold
  covers it.

### 2.5 Learning progress has to be real learning progress (arm 5 — channel: the queue's own ranking)

- **Gauge:** `curiosity_progress.score = ALPHA·new_fragments + BETA·finding − GAMMA·consecutive_stalls`, with
  `PARK_STALLS` parking — already deterministic, already mechanical, already satiety-shaped.
- **Today:** that score ranks the FRONTIER queue. Yet 254/277 internal cycles since boot ask one question (F-2850),
  and the same word is the dream tension, the letters, the librarian ask and the gist topic — so the perseverating
  loop is probably NOT the frontier picker (its LP would have parked the question by day two) but some other
  generator that re-derives the question from the attractor each cycle (the inner monologue's self-question seed,
  the dream tension carry, or the gist feeding back). Which one is **not located**. Every anti-capture gauge that
  exists measures the sentence (sim 0.89 → "forcing wander") and reads healthy because the wording changes.
- **Phase 0 (a read, before any build):** locate the loop. Trace each of the 254 cycles' `internal:` line back to
  its seed source field in the log; count per source. That read IS J-2152's gauge (modal-topic share per day) plus
  a provenance column. No build until it says which loop.
- **Build (conditional on Phase 0):** the located loop reads an LP for its TOPIC (not its sentence): topic =
  the gist-level `[self/<word>]` key memory_levels already assigns; LP = the same formula on fragments-new-this-topic.
  A topic whose LP is ≤ 0 for N cycles is not banned — it costs more to re-ask (the queue's own ranking, or a
  dose on the attractor), so a second topic wins by its own score. Satiety, not a rule.
- **Judge:** none (mechanical). **Graded back:** modal-topic share per day. **Founder:** J-2155 already asks for the
  anti-relock ruling with three options; this arm is the "satiety by LP" option made concrete.
- **2026-10-17 (J-2186):** Phase 0 located the loop (F-2889). Travis ruled out a hard topic anti-relock (D-0439), so the
  build is now the topic-blind own-thought dose in section 8 (F-3012), shadow build J-2322, flip D-0457.

### 2.6 Weakness picks the study (arm 6 — channel: the chooser's own score)

- **Gauge:** `capability_beliefs.json` per domain, graded by drills (maths, music), the comprehension judge, the
  nature-study grader (observation 0.46), the history witness (0.20).
- **Today:** `book_selection.select_explore` / `pick_one` and the school timetable choose without reading the
  belief vector. Maths is drilled daily at 100% because the drill is scheduled, not because it is weak.
- **Build:** `book_selection` and the school's practical/drill picker take an optional `weakness` term: the
  lowest-belief domain among those with a graded instrument gets a bounded prior (one extra candidate slot, never
  a forced pick — Du still picks). The grade-back is the existing instrument for that domain; nothing new.
  Shadow: `WEAKNESS_PRIOR = 0.0` (no effect) with a shadow log of what the slot WOULD have been.
- **Judge:** the domain's existing grader. **Graded back:** belief movement per domain per fortnight; the gate is
  history's belief leaving 0.20 by its own witness, or the slot being measurably ignored (then the prior is wrong,
  not Du).
- **Founder question (D filed):** a weakness prior on the shelf is a nudge from the world. Claude's position: it is
  the librarian's ordinary job (books_have_a_place already lets the library hand shape what is near), not a hint.
  Travis rules.

## 3. Order and the decisive pair

If only one thing is built: **arms 2 + 4 together.** Both reuse a judge that exists and a path that exists
(`prediction_error.observe`, the J-2052 judge); neither adds a word to any prompt; together they turn the 141-fire
self-interrogation loop from a diary into a control loop. Arm 3 next (it is one flag on J-2118's writer). Arms 1 and
6 wait on their rulings; arm 5 waits on its Phase 0 read.

## 4. Decisions opened with this document (founder)

All three ruled by Travis on 2026-10-15, the day they were opened:
- **D-0434 (arm 1): dropped** — no readout; Du finds out he is wrong by consequence, never by being told.
- **D-0435 (arm 4): A** — the D-0396 hold does not cover an executive-side pull; build shadow (J-2161).
- **D-0436 (arm 6): A** — a librarian's job; one bounded slot, shadow first (J-2162).
- J-2155 (already open from the read) covers arm 5's anti-relock ruling.

## 5. Jobs filed with this document

- **J-2156** Phase 0 read, arm 5: locate the perseverating loop (provenance of the 254 `internal:` cycles since
  boot) — pairs with J-2152.
- **J-2157** Phase 0 read, arm 2: count SUSPECT/GUESS/NO_BASIS cycles at `self_reported_confidence ≥ 0.85` per day
  since boot (the baseline the wager is graded against), and the variance of stated confidence across grades.
- **J-2158** shadow build, arm 2 (`RECALL_CONFIDENCE_WAGER`), gated on J-2157.
- **J-2161** shadow build, arm 4 (`DOUBT_SEED`), ready under D-0435 A (J-2159 was its gated predecessor); UDMS
  dossier on `nodes/executive_node.py` first.
- **J-2162** shadow build, arm 6 (`WEAKNESS_PRIOR`), ready under D-0436 A.
- **J-2160** arm 3 pursuit + commitment arms on `core/closure.py`, not before 2026-10-26 (J-2118's own 10-night read
  must land first — do not extend a shadow that has not yet produced a row).

## 6. What this plan is not

- Not a new gauge, judge, or prompt. If an arm needs a sentence in a prompt to work, the arm is wrong.
- Not a fix for the confidence constant by clamping it; the wager must be lost, not the number edited.
- Not a ban on mottainai. Satiety is the mechanism; a rule would be the integration attractor wearing a hat.
- Nothing here is live until Du restarts onto it and the founder reads the first shadow rows, same as every
  2026-10 build. The restart that gates the closure law gates this too.

## 7. Pre-registered probe bars (J-2190, D-0438 follow-up, 2026-10-17)

D-0438 (a): the referent is published cognitive norms where they exist, founder judgment elsewhere. J-2190 searched
for numeric norms for the three probes (J-2151 recall, J-2152 perseveration, J-2153 social). **Result: no numeric
published norm could be verified in this session** (web search returned catalogue/secondary pages only; the one PDF
fetched was unreadable). Per the job's rule, nothing is invented: a bar is either "founder-judgment, unset" or an
explicitly labelled design/own-history anchor. These are written BEFORE the post-restart conversation set and before
any post-restart row is graded. Nothing below is a published norm unless it says "sourced".

| Probe | Metric | Bar | Status |
|---|---|---|---|
| J-2151 `scripts/autobio_recall_probe.py` | median date_error_days (events 1-30 d old) | none | **not sourced**; founder-judgment, unset |
| J-2151 | mean detail_precision | none | **not sourced**; founder-judgment, unset |
| J-2152 `core/topic_perseveration.py` | modal_share per day | `FROZEN_SHARE` 0.80 is a design threshold, not a norm | **not sourced**; founder-judgment, unset |
| J-2152 | topic switch rate (topics per day) | none | **not sourced**; founder-judgment, unset |
| J-2153 `core/social_cognition_shadow.py` | tracks_intent >= 0.90, refs_earlier >= 0.50, attrib_supported given attributes >= 0.80 | already in code as BAR, labelled "attentive adult" | **founder-judgment, not sourced** (written 10-16 before rows were judged; keep, but do not describe as a published norm) |

What was and was not verified:
- Wagenaar (1986), "My memory: a study of autobiographical memory over six years", Cognitive Psychology 18:225-252, a
  real diary study. Only a secondary summary was retrieved: who/what/where work about equally as retrieval cues, the
  date ("when") is a weak cue, salience and emotional involvement predict memorability. No date-error-in-days or
  detail-precision figure was verified. Qualitative direction only.
- Thompson, Skowronski, Larsen & Betz (1996), Autobiographical Memory: Remembering What and Remembering When
  (Erlbaum) is real and has a chapter on how retention interval affects event-date reconstruction. Chapter content
  not retrieved; no number verified. Direction only (date error is expected to grow with retention interval).
- **The J-2151 docstring caveat (c) "detail precision ~50-60% for week-old events, date error 1-3 days" is NOT SOURCED**;
  it was copied from the J-2151 briefing and never verified. Treat it as unsourced until someone reads the books.
- Klinger (1978), "Modes of normal conscious flow" (in Pope & Singer, The Stream of Consciousness) is the usual thought-
  sampling reference, but no thought-unit duration or topic-shift figure was verified, and Du's internal cycles are
  deliberate questions minutes apart, so a thought-unit norm would not transfer anyway. No published norm exists for
  "modal-topic share of a day's self-generated questions" that this session could find.

Own-history anchor for J-2152 (descriptive, NOT a norm; read from data/topic_perseveration.jsonl, days with n >= 15):
09-17..10-05 modal_share ranged 0.21..1.0 with median about 0.41 and 3-25 topics/day; from 10-10 to 10-17 it is
0.93..1.0 on 1-3 topics. Offered to the founder as the candidate "before the attractor" baseline if he wants Du
compared to himself; adopting it is his call (D-0438's fallback: founder as baseline where norms do not exist).

Next (founder): rule per probe whether to (1) set a bar from his own judgment, (2) adopt Du's 09-17..10-05 history as
the J-2152 baseline, or (3) keep these as qualitative-only until sourced norms are read from the books themselves.
A small build job corrects the J-2151 docstring caveat and the J-2152 header to say "not sourced".

## 8. Arm 5 build design: the own-thought dose (J-2186, 2026-10-17; F-3012, F-2889; flip = D-0457)

**What the loop is (F-2889, re-measured in F-3012).** An internal cycle's perception summary goes back into
`CuriosityNode._recent_themes` (`core/orchestrator.py` `_persist_cycle`, the `add_theme` call, not guarded by
input type) and the newest 10 are shown to the same LLM at the next ignition (`nodes/curiosity_node.py`
`_build_prompt`). Since the 10-09 boot the logged window held 1934 lines from Du's own internal cycles and 31 from any
other cycle (98.4% echo; 3 human cycles in eight days). **The loop does not care about the topic.** Du restarted
2026-10-16 22:36, which empties the window. The first question after it came from study material (Johnson's grammar,
"the art of using words properly"). From cycle 2 the echo relocked onto *that* topic for 33 cycles. No tension seed
carried it (0/27 anchor rows). Mottainai was still offered as a seed and did not return until cycle 35. Whatever
topic enters first, the echo holds it.

**What D-0439 allows.** Travis ruled the world-displacement channel (J-2195) and "no hard topic-level anti-relock;
leave dwell alone". So the briefing's candidate (b), a topic novelty check on `valid_qs`, is **not designed**. It is
the declined anti-relock. The replay keeps it for the record: it would have rejected 249 of 284 mottainai questions,
and only 65 of those 249 had a different question in the same output. Candidate (a) is designed below as a
**dose**, not a brake. It reads no topic, rejects no question, adds no prompt line and shows Du nothing (D-0434).
Whether a dose on the echo is inside D-0439 is Travis's reading: **D-0457**. Claude's position: a human's last
thought stays in view, and ten copies of it act like a loudspeaker, not a memory.

**Variants replayed (prompt composition only; the LLM's answer cannot be replayed; 284 mottainai q0 rows):**

| Variant | What changes | Replay |
|---|---|---|
| A0, dose 0 | own internal lines never enter the window | 149/284 (52%) left with no logged mottainai carrier; the seed channel still carries it in 135/284 |
| **A1, dose 1 (recommended)** | the window keeps every non-self line plus only the NEWEST own line | mottainai lines in the logged 6-theme window: mean 4.90 → 0.90; 280/284 rows go from ≥2 to ≤1 |
| B, topic reject | reject q0 when its topic holds ≥80% of the last 12 | declined by D-0439; recorded only |

A1 keeps dwell possible through three routes: the newest own thought, the tension seeds (themselves partly minted
from these cycles), and recall. What it removes is the amplification.

**Build (J-2322, shadow, restart-gated, additive, fail-open).** A new module `core/theme_dose.py` holds
`SELF_THEME_DOSE: int | None = None`. `None` keeps today's path byte-for-byte. A pure `window(themes, sources, dose)`
does the selection and has no topic, similarity or keyword logic. `add_theme(theme, source="")` gains an additive
provenance tag, and the orchestrator passes `state.input_type`. With the flag at `None`, `_build_prompt` renders the
live window as today and logs the would-window (dose 1). The `curiosity_log` field `recent_themes` stays the live
window, so this replay and F-2889's stay comparable.

```coupling
publishes: nothing to other loops. Each theme gains a private provenance tag {source: input_type of the producing cycle} inside CuriosityNode.
reads_at: CuriosityNode._build_prompt (stop). Line "self_theme" (own internal-cycle summaries) at a CUP dose: the newest 1. Line "other_theme" (human, recall and other cycles) at a BUCKET dose: up to 10, as today.
surprise_line: none, deliberately. The dose is fixed. A surprise- or share-gated dose would need a topic detector, which is the anti-relock D-0439 declined.
ride_log: data/logs/curiosity_theme_dose_shadow.jsonl, one row per prompt build: {ts, stop, line, dose, flag, n_live, n_self_live, n_self_would, live_window, would_window, seeds, study_subjects, curiosity_id}.
```

**Pre-registered (written before the build, read by J-2323 at ≥7 live days and ≥100 rows after the restart onto it):**
- Shadow: rows per day; mean `n_self_live` vs `n_self_would`; the share of rows where the would-window differs from
  the live one. If it differs on fewer than 20% of rows, the dose would change nothing (D-0457's defeater).
- Baselines for a flip, all from F-3012: modal-topic share per day of internal q0 is 0.93-1.0 on 10-10..10-15 (the
  J-2152 rule); the longest same-topic run after a clean window is 33; internal cycles per day are the 7 days before
  the flip.
- Success direction, not a bar (D-0438: no invented norms): the longest run and the modal share fall, while q0 still
  overlaps something in its prompt (study, seed, or the one own line). D-0439's own defeater (still above 90% after
  14 days of the world channel) stays the founder's test.

**Kill / revert after a flip (any one; flag back to `None`, nothing else to undo):**
1. Modal-topic share per day falls below the dwell floor J-2196 names. **Until J-2196 names it, the flag cannot flip.**
2. Internal cycles per day fall below half the pre-flip 7-day mean. Curiosity urgency is starved without its themes;
   F-0777 is the precedent for a silent drop in ignitions.
3. The share of rows with an empty `valid_qs` or a parse failure doubles over the pre-flip rate.
4. More than 25% of q0 share no word with any prompt input. F-2889's "neither" was 2%; above 25% the question has
   come loose from his life.
5. Any prompt text other than the window changes. Then the build is wrong, not Du.

**Sequencing.** J-2195 (world displacement) and this arm must never flip in the same restart. D-0439's 14-day
defeater is read on J-2195 alone, and two changes at once cannot be told apart. Recommended order: J-2195's 14 clean
days first, then this flip if D-0457 rules (a).

## 9. Wager loss becomes a question (arm 2 feedback; J-2527, I-0105, F-3221 item 2; SHADOW, flag off)

**Gate (met).** `RECALL_CONFIDENCE_WAGER = True` since the 2026-10-29 18:38 boot (D-0495); 38 live rows, all
`fed=True`, between 2026-10-29 18:56 (cycle 2cffc265) and 2026-10-30 12:52 (cycle 26917e74).

**What it does.** `core/wager_curiosity.py`, called from `recall_wager.place()` right after the wager row is written
(fail-open, own flag `WAGER_CURIOSITY = False`, own log `data/logs/wager_curiosity_shadow.jsonl`). A wager whose gap is
at or above 0.40 (the drill's own `GAP_THRESHOLD`) is *lost*. A lost wager that is neither corrected (the cycle's
human input carries a `competence._CORRECTION_CUES` cue) nor already retracted (`retraction_ledger.known_errors(topic)`)
becomes at most one frontier question via `frontier.note_question_ex(q, "wager", slot, about, allow_self=True)`. The
question is shaped by the missing-context type the grade already holds: no_source (where), conflicting_sources (why),
unverified (how), ungrounded_model (what), around the cycle's own input as topic. A corrected or retracted wager never
generates curiosity; the error pathway owns it (the row says route=correction or route=retraction).

**D-0434.** The question carries the topic and a slot only: never the grade, a number, the word wager, or that he was
wrong. He meets a question about something he spoke on, not a readout about himself.

**Coupling (dosed_coupling §5).**
- **Publishes:** per lost wager `{cycle_id, gap, missing_context_type, slot, topic, question_candidate, route}`; event
  cadence (one per wager row, ~1-2 per hour on the live boot).
- **Reads at:** stop `frontier_note`, line `recall_wager`, dose **cup** (one question, never a bucket).
- **Surprise line:** the wager-curiosity log's own last 24 h: a topic overlapping a recent birth (token Jaccard > 0.55,
  frontier's own dedup bar) is habituated; at most 4 births per 24 h. Curiosity and the Follow Line stay free to
  ignore the question; it fades like any frontier entry.
- **Ride log:** every route (not_failed / correction / retraction / no_topic / habituated / capped / birth) writes
  one row with `{stop, line, dose, value}`.

**Replay on the 38 live rows (J-2527, scripts/_test_wager_curiosity_j2527.py, read-only):** 17 not_failed (narrated
0.85, gap 0.35), 21 lost: 4 birth, 1 habituated, 16 capped. missing_context_type was conflicting_sources on 38 of 38
(every live SUSPECT carries contradictions), so the slot is a constant on current data. The 4 births are paraphrases of
one Bluebird question (token overlap under 0.55): topic habituation by tokens does not catch paraphrase; the cap did
the work. Both are recorded as the risks the read must watch, not tuned away here.

**Pre-registered read (before any flip; shadow rows on the next boot that carries this build):** after >= 50 shadow
rows, report route counts, births per day, distinct-topic share of births (paraphrase clusters by frontier's
semantic matcher), and the missing_context_type distribution. Kill / do not flip if: births are >= 75% one topic
cluster, or missing_context_type stays one value on >= 95% of rows (then the slot carries nothing and the question
is a template), or any question text carries a grade, number or verdict. Flip is a founder call.
