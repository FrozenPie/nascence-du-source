# UDMS→Du Capability Trials — Eight Candidates, One Verdict Each (2026-08-28)

> **Status: ✅ SHIPPED — all 8 trials verdicted, D-0059's own defeater met (founder ruling 2026-08-28:
> investigate ALL EIGHT surveyed UDMS capabilities for Du usefulness, shadow-first, with a
> pre-registered helpful/not-helpful criterion per trial). D-0143/D-0180/D-0197 await a founder
> decision pass on disposal, not more trial work. This plan is the umbrella index; candidates that belong to an
> existing plan CROSS-LINK there rather than duplicating (per D-0005 compose-don't-duplicate).
> Sibling: `du_recall_lens_upgrades.md` holds the three PARKED recall lenses (D-0057-era, J-0291) —
> they are deliberately NOT re-listed here.**

```plan-state
stage: shipped
phase: All 8 trials verdicted (D-0059's defeater met); Du-lens A/B/C trilogy done with real fixes landed; D-0143/D-0180/D-0197 still open
verified: 2026-11-07
evidence_read: 2026-09-06
next: J-3781 re-score after D-0686 warm-up produces editing-session calls
cluster: 0
```


## Why this plan exists

The 2026-08-28 UDMS reuse survey (agent-run, catalog-grounded) identified eight capabilities beyond
the parked recall lenses, each with an honest evidence status. The founder ruled (D-0059): test them
all. Ground rules inherited from the UDMS audit and F-0399:

1. **Cite computed numbers only, never script prose** — several scripts print conclusions their own
   output contradicts (`udms_lens_atlas.md` §5).
2. **No single-split effect sizes** — F-0399 proved test_p/test_q swing wildly with the evaluation
   window. Any trial reporting an effect size uses rolling windows or CIs (trial 7's harness).
3. **Shadow-first** — nothing touches Du's live loop until its trial has a recorded verdict and a
   founder decision.
4. **A "not helpful" verdict is a success of the trial**, recorded the same way as a win.

## Current State — verified 2026-11-07

- **2026-11-07** (F-4398): J-3453 (2026-11-07): pre-registered dossier follow-through scorer run; served list V0 clears the roll-null bar on pooled calls (reads z +10.6, edits +5.9, W30, own file excluded); main thread unscorable (16 reads); hub removal does not help; no ranker job. See C:/UDMS/docs/audits/dossier_followthrough_prereg_2026-11-07.md
- **2026-11-06** (F-4096): 2026-11-06 review of the UDMS update (commits 8de9d8e, 4cbfecf): 18 findings F-4028..F-4042, F-4077..F-4079 and jobs J-3404..J-3407, J-3453..J-3456 were filed under this SHIPPED plan plus I-0146..I-0149; nothing in core/udms or the MCP tools changed. Trial 4's beta_1 was an edge count (F-4028, section 9.2 of the Argon audit) and Trial 6's Koopman gain line was a scale artifact (F-4029), both consistent with their NOT HELPFUL / retired verdicts. The Du-lens work (I-0066 and the four new ideas) now outgrows this umbrella; a staged du_observability_lens plan is the candidate home.

### What we have
All eight pre-registered trials now have a verdict (D-0059's own "all eight verdicted" defeater is met):
Trial 1 NOT HELPFUL on the post-D-0057 fabric (D-0143 open: retire vs re-register with a per-model stall
definition); Trial 2 NOT HELPFUL (weekly split too volatile); Trial 3 BAR MET (its "drift" alarm resolved to
an instrumentation bug, F-0419); Trial 4 BAR MET (a real, separate, lower-priority open question); Trial 5
tooling fixed, label-validation method needs founder input (J-0330); Trial 6 NOT HELPFUL (persistence beats
every forecaster tested); Trial 7 DONE (the enabler harness; re-run pending J-0280's window); Trial 8 NOT
HELPFUL (a genuine null result). Full per-trial mechanism/evidence stays in each "## Trial N" section below;
full dated history is `plan_ledger.py udms_du_capability_trials`. A related-but-separate trilogy (idea I-0066,
the Du-lens A/B/C tests, not one of the 8 numbered trials) found real associations (Test A/B helpful / a
minority signal; Test C: journal and letters concord with world state, essays a clean null) and produced real
code fixes along the way: a journal-header mislabel (J-0695), 8 scripts' test-isolation redirect gaps
including one genuine live leak into `core/activity_memory.py` via `garden.py` (J-0743), and a T6 Step 1
retirement ruling (D-0191). Nothing from either the 8 trials or the trilogy is wired into Du's live loop —
every run was read-only against `C:\Nascence\data`; hygiene only, J-0906 (done 2026-09-13) committed the
previously-uncommitted `du_lens` tooling to UDMS's own git history.

### What we need
D-0197 (do the context/action word-association pairs replicate on full text) is still OPEN: context pairs
51.1% replicate, action pairs 39.2-45.1%, both below the plan's own >=50% bar on the full set, so the
shadow-recall-anchor / HUD-gauge / nothing choice is still the founder's. D-0143 (Trial 1 retire-or-reregister)
and D-0180 (retire the primary full-text table) are also both still open.

### What we're doing next
No trial work is queued; D-0143, D-0180 and D-0197 are what a founder decision pass would clear next. UDMS
lineage B stays parked (D-0195); `core/math` continues as this plan's own analysis library only.

---

## Trial 1 — Stall-cascade early warning on LLM telemetry

- **Mechanism:** PCA-reconstruction residual over rolling latency features from `llm_latency`
  telemetry, threshold at p95 of non-stall steps, forward-only evaluation from clean steps.
- **Evidence in:** lift 2.71× at horizon 1 (P(stall|warn) 19.92% vs 7.34%), 1.99×/1.68×/1.40× at
  h=3/5/10 — saved JSON `C:\UDMS\data\viability_validation\nascence_prospective_and_stratification_results.json`.
  Script prose is fabricated (prints 4.8× / AUROC 0.88–0.96; its own JSON says 1.68× / 0.50–0.975)
  — JSON only. Also: `yi:34b-v1.5` = 211 events, 211 stalls, mean 180.2s.
- **Du question:** can `pulse_manager`/`model_client` demote a model or defer a node BEFORE a stall
  cascade instead of reacting after? And should yi:34b be in any rotation?
- **Trial:** re-run `test_ce_nascence_prospective_stratification_and_visual_overlay.py` against
  CURRENT telemetry (post-D-0057 fabric is a different model mix — the old per-model numbers may
  not transfer). Then a two-week paper-trade: log warnings alongside real stalls, no action taken.
- **Helpful =** horizon-1 lift ≥ 2× on the new fabric's telemetry with ≥ 30 warning events.
  **Not helpful =** lift < 1.5× or warnings too rare to act on.
- **Caveat carried:** PCA+threshold are calibrated in-sample in the script; the paper-trade phase
  must calibrate on a prefix and evaluate forward only.

## Trial 2 — Prediction-miss error taxonomy

- **Mechanism:** classify each failed next-concept prediction as semantic near-miss /
  environmental shift / model blindspot, with predicted↔actual graph distance.
- **Evidence in:** 3,593 real misses → 93.2 / 2.0 / 4.9% (`test_l`'s computed counts; its printed
  "surprise" conclusion is self-falsified — atlas §5. The Du-side plan's 97.3/1.9/0.8 has no
  verified source).
- **Du question:** should `self_surprise`/`prediction_error` scale surprise by miss KIND? A 93%
  near-miss rate argues most misses deserve small surprise; the rare blindspot deserves the spike.
- **Trial:** re-run `test_l` on current data (counts only); then classify a month of misses by
  week to check the 93/2/5 split is stable over Du's life, not one window.
- **Helpful =** split stable (near-miss share 85–97% across weeks) AND blindspot misses visibly
  differ (graph distance) from near-misses — i.e. the classifier separates something real.
  **Not helpful =** split unstable across windows or the classes don't differ on any measured axis.

## Trial 3 — Intrinsic dimension of Du's state → `geometry_tuple_index`

- **Cross-link:** this trial's verdict lands in `docs/staged/geometry_tuple_index.md` (its open
  sizing question); this plan only tracks the trial.
- **Mechanism:** Levina-Bickel MLE + TwoNN + participation ratio on state vectors; rolling
  `d_eff = (Tr C)²/Tr(C²)` over 500-tuple windows for the time series.
- **Evidence in:** REAL-MATH-UNPROVEN-VALUE — atlas §2 certifies the implementation
  (`test_y_through_ad` §compute_intrinsic_dimensions; `cognitive_geometry_audit.py` Stage 1 is the
  certified-genuine rolling variant inside an otherwise self-falsifying script). The `d=2.06`
  figure floating in the Du-side plan has no verified source.
- **Trial:** run the estimators on current tuples; produce the ROLLING series (does d_eff drift
  over Du's life?). Take only the dimension estimators from those files — nothing else.
- **Helpful =** the three estimators roughly agree (within ~1 dimension) and the rolling series is
  stable enough to size the index (or shows a real drift worth knowing).
  **Not helpful =** estimators disagree wildly (says the manifold assumption itself is shaky at
  this data size — also worth knowing, verdict goes to geometry_tuple_index either way).

## Trial 4 — Longitudinal Betti numbers on the concept graph

- **Mechanism:** β₀ (components) / β₁ (independent loops) via Euler characteristic per time
  window — a computed number for "did a concept community merge/split".
- **Evidence in:** REAL-MATH-UNPROVEN-VALUE — `test_w`'s graph version is certified correct;
  atlas's own words: "never actually run longitudinally". Do NOT import the MST-based
  "persistent homology" from the observable-atlas script (mislabeled, no birth/death pairing).
- **Du question:** the monoculture is topologically a β₀/β₁ story — `monoculture.py` and
  `theme_recurrence.py` currently use heuristics. Also `memory_edges`: a component-bridging edge
  is structurally different from an intra-community one.
- **Trial:** snapshot run first (sanity), then a small new runner: slide test_w's β computation
  over monthly windows of `geometry_tuples.jsonl`; plot β₀/β₁ against known monoculture episodes.
- **Helpful =** β trajectory visibly moves at known monoculture onsets/breaks (the episodes the
  du-pulse history already flags). **Not helpful =** flat/noisy β regardless of episodes.

## Trial 5 — Turning-angle rumination metric → `cognitive_geometry`

- **Cross-link:** verdict lands in `docs/plans/cognitive_geometry.md`, which currently cites an
  UNVERIFIED "100% deterministic rumination throttling (42.3µs)" from an orphan benchmark — this
  trial replaces that claim with something real or kills it.
- **Mechanism:** net-displacement vs accumulated turning angle over sliding state windows — a
  cheap, non-LLM "is this trajectory looping" measure (`C:\UDMS\core\math\hodge_governor.py`;
  real metric, explicitly NOT true Hodge).
- **Evidence in:** one honest longitudinal finding — Du's later-life trajectories measure more
  ruminative (curl 0.477→0.577 train→test, `test_c`, 70/30 temporal split, threshold locked on
  train). BUT the threshold-search code is broken (thresholds don't affect the ratios searched) —
  the "elbow at τ=0.70" is not supportable.
- **Trial:** (a) fix the threshold search (small); (b) validate the metric against ground truth Du
  already has — `wandering_log.jsonl` + monologue episodes a human (or judge model) labels as
  ruminative vs exploratory; (c) only then ask whether a governor belongs in `wandering.py`.
- **Helpful =** metric separates labeled ruminative from exploratory windows (any honest effect
  with a CI). **Not helpful =** no separation once the threshold bug is fixed.

## Trial 6 — Koopman/DMD mood forecasting

- **Mechanism:** fit linear operator K on state snapshots, forecast by matrix powers — genuinely
  validated out-of-sample to k=50 (the one non-name-drop Koopman in the corpus, catalog §4).
- **Du question:** "where is this mood heading" k steps out — nothing in Du produces a forecast
  today (`mood.py`, `opponent_process.py`, `sleep_pressure.py` are all reactive).
- **Trial:** re-point the fitter from geometry-tuple state onto `affect_log.jsonl` (small change);
  forecast k∈{1,5,10,50}; compare against trial 7's baselines (VAR, Kalman, persistence) — a
  Koopman forecast that doesn't beat persistence is decoration, per rule 2.
- **Helpful =** beats persistence AND at least one classical baseline at k≥5 with CI.
  **Not helpful =** persistence wins (also a real result: Du's affect is then locally static and
  every forecaster is over-engineering). The "87.8% residual reduction" in the old Du-side plan is
  unverified — ignore it.

## Trial 7 — Eval harness + baseline suite (the enabler — run FIRST)

- **Mechanism:** `C:\UDMS\core\udms\eval_harness.py` (Wilson CI, McNemar, paired bootstrap,
  marginal-preserving shuffle, noise-injection control, risk-coverage sweep) +
  `baseline_models.py` (VAR, HMM, Kalman, BOCPD, PCA-residual, Koopman). Both self-tested,
  numpy-only core.
- **Why first:** it is the measurement instrument for trials 2, 5, 6 and the fix for F-0399's
  single-split instability — and it upgrades EVERY shadow log Du accrues (associative_recall,
  affect_divergence, arousal, ast_loop) from "different from live" to "beats a named baseline
  with a CI, survives a shuffle control".
- **Trial:** import + self-test (done this session — see Current State); then port a thin
  `scripts/shadow_eval.py` in Nascence wrapping harness calls over one existing shadow log
  (M2's `associative_recall_shadow.jsonl` when its week gate matures — composes with J-0280/J-0315
  rather than racing them).
- **Helpful =** self-tests pass and the first real shadow-log evaluation produces a CI-carrying
  verdict the old hand-read couldn't. **Not helpful =** hidden sklearn-style dependency weight or
  the harness's assumptions don't fit jsonl-shaped shadow data.
- **Warning carried:** port the classes, NOT `test_ap`'s data loaders or invented cost economics;
  `search_optimal_observable_subset` methodology is real but has never seen real labeled data.

## Trial 8 — Conformal / adaptive threshold calibration

- **Mechanism:** split conformal + Adaptive Conformal Inference (`conformal.py`) and a
  moving-window recalibrator (`adaptive_calibration.py`) — distribution-free false-alarm
  guarantees that survive drift. Falls back to fixed thresholds when uncalibrated.
- **Evidence in:** synthetic-only: frozen threshold under drift → 44.7% false alarms vs 5% target;
  adaptive holds 6.1%; ACI post-shift 100%→5.2%. NOTHING has seen Du data yet.
- **Du question:** every hand-tuned threshold on a drifting lifetime signal —
  `affect_divergence.py`, `arousal.py`, `boredom.py`, `sleep_pressure.py`, the shadow graders.
- **Trial:** pick ONE Du threshold with a logged history (boredom or affect_divergence), replay
  its real signal through frozen-vs-adaptive calibration OFFLINE, count false-alarm/miss rates
  against whatever ground truth that subsystem's log carries.
- **Helpful =** adaptive materially beats the frozen threshold on Du's own replayed history.
  **Not helpful =** Du's signals are stationary enough that frozen thresholds already hold their
  target rate (then this ports nowhere and the finding says why).

---

## What is deliberately OUT of scope

- The three parked recall lenses (D-0057-era; `du_recall_lens_upgrades.md`, J-0291) — separate gate.
- Everything on the survey's kill list (golden-angle mystique, test_cd's circular AUROC,
  Grassmannian drift, the fabricated agent-failure cluster, Lorentz-cone decoration, singularity
  calculus at Du's noise level) — killed by the catalogs' own data; do not re-litigate without new
  evidence.
- Any live-loop wiring. Every trial verdict that says "helpful" still needs its own founder
  decision + shadow period before touching Du.

## Pointers

- D-0059 (`decide.py show`) — the founder ruling this plan executes.
- F-0399 (single-split instability), F-0400 (M2 gate preliminary), F-0401 (stale side-plan) — the
  findings that shaped the ground rules.
- `C:\UDMS\docs\plans\udms_lens_atlas.md` — evidence atlas (§5 = cite-numbers-not-prose list).
- `docs/archive/multidimensional_dynamical_field_side_plan.md` — the STALE pre-audit index (J-0316
  reconciles it; do not cite its numbers meanwhile).
- Session scratchpad `trial_*.out` — this session's first-pass run outputs (durable numbers get
  copied into the trial sections above, not left in temp).
- I-0066, `C:\UDMS\docs\audits\du_lens_first_test_2026-09-06.md` — the 2026-09-06 Du-lens A/B/C
  trilogy (F-0980–F-0983, F-1000, F-1001; J-0684/J-0685/J-0686/J-0687/J-0695/J-0712) plus the
  2026-09-07 J-0687 document-block null addendum (F-1021; D-0180 open), the 2026-09-07 J-0712
  block-null diagnosis + per-pair comparison (F-1051, DONE, D-0180 still open — see the Current State
  update above), the 2026-09-07 J-0695 journal-header fix (F-1044, DONE, committed `4b039ca`;
  J-0725 spawned on an incidental test-isolation gap), and the 2026-09-07 J-0725 test-isolation
  redirect-gap fix (F-1063, DONE, committed `ee6823c` on worktree branch `jobrun/udms_isolation_fix`,
  not yet merged to master; wider sweep spawned as J-0743). A related application
  of this plan's discipline, not one of the eight numbered trials — see the Current State updates
  above. The 2026-09-08 J-0743 wider sweep (F-1129/F-1130, real `activity_memory` leak fixed +
  4 more scripts' redirect gaps fixed + the tension-ledger/multilevel discovery) and its own J-0788
  follow-up (F-1133, DONE — split verdict: the axiom-text confrontation channel is orphaned since the
  multilevel cutover, but the functional contradiction→self-revision channel is not; **D-0191 open**,
  founder call on restoring vs. formally retiring the text channel) are also findings under this same
  plan, not separate trials. The 2026-09-10 J-0839 read (F-1241, D-0197 reopened on the context table's
own replication share) and the 2026-09-12 J-0884 follow-up (F-1267, DONE — the full-text action
table, 39.2%/45.1% of F-0980's 51 action pairs re-pass, attached to **D-0197**, still OPEN, as
further evidence) are the same trilogy's own D-0197 thread — see the Current State updates above.
