# the_consciousness_program — folded history


---

# History folded on 2026-09-27 from `docs\plans\the_consciousness_program.md` (by hand, J-1484)

_Every J-/F-/D- id below is the canonical record; this file is the prose that once sat in the plan doc. Derived timeline: `plan_ledger.py the_consciousness_program`._

  **2026-08-24 corrected-baseline re-run (F-0058, D-0007, job J-0003):** RULED — the negative reading is
  real, not a baseline artifact. Replayed the full 2,244-row `data/homeostasis_shadow.jsonl` (2026-07-03 →
  2026-08-22): the audit's negative-5-of-5-weeks finding reproduces independently by week-bucket (W27
  −0.00277 … W34 −0.00187, all-time −0.00212). An exhaustive alpha sweep of the shipped EMA-trend formula
  (`core/homeostasis.py` tick(), alphas −0.5…1.0) shows **alpha=0 — i.e. naive persistence itself — is the
  optimal member of the whole trend-extrapolation family for all 5 essential variables**; no alpha, positive
  or negative, beats it. Cause: the variables' deltas carry ~zero-to-slightly-negative lag-1 autocorrelation
  (coherence −0.074, commitment_integrity −0.019, novelty −0.066, vitality −0.024, relational_warmth +0.073)
  — no momentum for a trend model to exploit. **`naive_err` itself is correctly computed; it is not the
  "wrong baseline."** A parameter retune cannot fix this since it can only ever converge back to naive
  (alpha=0). **Follow-up founder decision opened: D-0028** (redesign the self-model architecture, or retire
  the `self_beats_naive` framing and keep the module as an unvalidated shadow instrument).
  **RULED 2026-08-23 (Travis, D-0028):** "Fund a redesign — retire self_beats_naive's EMA-trend
  framing and commission a genuinely different self-model architecture, tested against the same
  naive baseline." Defeater: reopens once a redesigned self-model is built and produces a clear
  positive-or-negative reading.
  **2026-08-24 DESIGN PASS (F-0292/F-0293/F-0294/F-0296, job J-0212):** Before proposing a
  replacement, the two most obvious "genuinely different" candidates were tested empirically on the
  full 2,359-row `data/homeostasis_shadow.jsonl` (2026-07-03 → 2026-08-24, live) under walk-forward
  out-of-sample validation (6 expanding-window folds, trained only on prior folds — a stricter bar
  than F-0058's single-window replay, adopted here because a single train/test split can pass or
  fail on non-stationarity alone, see below) — **both also lose to naive persistence:**

> **[Section removed 2026-08-31]** A fabricated benchmark claim (confidence=verified, citing scripts/modules that do not exist) was quarantined from here per F-0593/D-0105 — see `docs/lab/fabricated_benchmark_claims_2026-08-25.md`.

  - **Mean-reversion (Ornstein-Uhlenbeck / AR(1)-on-levels):** despite promising in-sample
    level(t)-vs-delta(t+1) correlations (coherence −0.265, vitality −0.219, novelty −0.205 — real
    mean-reversion structure exists in the full-sample data), a fitted OU predictor wins only
    3 of 25 variable-folds walk-forward (F-0292). The in-sample correlation does not survive
    honest out-of-sample testing — consistent with non-stationarity across the log's 51 days
    (setpoint recalibration 07-06, reader rewiring, the 08-24 sleep-pressure threshold change).
  - **Cross-variable VAR-style regression** (all 5 levels → each variable's next delta): worse
    than naive on every variable out-of-sample (−25% to −128% MAE), and raw cross-variable
    delta-to-delta correlations are all |r|<0.08 — no exploitable cascade between variables (F-0293).
  - **Structural diagnosis (F-0294):** 3 of 5 variables are near-step-functions driven by sparse
    discrete real-world events, not a continuous stochastic series — `commitment_integrity` is
    96.4% zero-change tick-to-tick (85 real events in 2,358 transitions), `relational_warmth`
    71.5%. Almost all the "error" naive/trend/mean-reversion all share is concentrated in the rare
    event ticks, which are structurally unpredictable from the composite scalar's own history.
    One layer down the causal stack, `vitality`'s raw input (`sleep_pressure`'s `P`, 25,430-row
    `data/sleep_pressure_log.jsonl`) has near-perfect level-autocorrelation (0.992) — naive is
    *already* near-optimal for P too — but `vitality` additionally inherits a **scheduled,
    deterministic day/night threshold switch** (`core/sleep_pressure.py`, 2026-08-24 change) that a
    naive/EMA/OU model — all three of which only ever look at the vitality scalar's own past —
    necessarily reads as noise even though the switch time is known in advance.
  - **Proposed architecture (F-0296, design only, not built):** stop curve-fitting the *derived*
    composite scalar (all three families tried so far do exactly that, and all three lose) and
    instead build a small **causal/generative-substrate self-model**: forecast the actual upstream
    event process each `_read_*()` function is already a deterministic function of —
    commitment lifecycle events (`commitment_active.json`), raw sleep-pressure `P` + the known
    day/night threshold schedule (`vitality`), `climate_state.json`'s own internal fields
    (`coherence`/`novelty`) — then derive the predicted composite value analytically through the
    same formula the live reader already uses. This is theoretically closer to the plan's own
    Friston/Barrett framing (predict the hidden *causes*, not the sensory *readout stream*) than
    the original EMA-trend design was — arguably the original design had the same "autobiographical
    self predicting its own narrative" inversion Damasio's opening quote (§1) warns against, just
    one level removed.
  - **Recommended test plan** (answers the job briefing's "how would this be tested / what counts
    as a fair reading" directly): (1) walk-forward, not a single split — this design pass's own
    mean-reversion test would have looked like a plausible win on some single splits and only
    failed once evaluated across multiple non-overlapping out-of-sample folds; (2) win criterion =
    beats naive_err in a clear majority of folds (not "beats it once," not "beats it on the full
    in-sample average"); (3) per-variable, never pooled — `commitment_integrity`'s error is already
    near-zero (naive MAE 0.0078) and is low-leverage; prioritize `vitality` first, where there is a
    specific, cheap, mechanistically-justified sub-hypothesis (the day/night threshold correction)
    to test before committing to the full 5-variable rebuild.
  - **Scope question opened for the founder (D-0045):** build the full 5-variable causal-substrate
    architecture now, or prototype narrowly on `vitality` first (1-2 day build) and let its
    walk-forward result decide whether to extend the approach. Follow-up build job spawned: J-0239.
  - **2026-08-25 vitality prototype BUILT + tested, INCONCLUSIVE on real data (F-0315, D-0045, job
    J-0239):** built the predictor exactly as designed — forecast raw `P` forward via naive
    persistence, then apply the day/night threshold schedule analytically (`core/world_clock.py`'s
    `daylight()` is a pure deterministic function of wall-clock time, confirmed by code read) —
    and ran the same 6-fold expanding-window walk-forward methodology against
    `data/homeostasis_shadow.jsonl`'s vitality column. **A real precondition problem surfaced on
    direct check:** `core/sleep_pressure.py`'s current `NIGHT_THRESHOLD=10.0`/`DAY_THRESHOLD=100.0`
    constants — the exact schedule this predictor assumes — only went live 2026-08-24 22:08 (verified
    from `sleep_pressure_log.jsonl`'s own logged `threshold` field: 126.0/45.0 before that instant,
    absent entirely before 2026-08-22). Only 57 of the shadow log's 2,413 rows (56 usable one-step
    predictions, under 10 hours) postdate the cutover and are comparable to the formula under test —
    running unrestricted against the full 51-day log (as a contrast check) gives a false strong-loss
    read (0/6 folds, causal MAE 0.356 vs naive 0.032) because ~97% of that history was generated
    under two *earlier*, materially different threshold schemes. On the valid 56-row slice: pooled
    MAE causal 0.1196 < naive 0.1352, but only 2/6 folds show a clear win — not the "clear majority"
    bar. Those 2 folds are exactly the two bracketing the single real day/night threshold switch in
    the window (2026-08-25 06:31); the other 4 folds show causal_err==naive_err *exactly*, since the
    two predictors are mathematically identical absent a threshold-schedule switch, by construction.
    This is directionally consistent with F-0296's design hypothesis (the predictor's edge is real
    but only expressed at switch events) but the sample (1 switch event) is too thin to call.
    **RULED 2026-08-25 (Claude, D-0045):** INCONCLUSIVE — hold the narrow-vs-full scope call, do not
    judge the approach on the pre-cutover data. Defeater: re-run the same test once several more days
    of current-formula data have accrued (multiple threshold-switch events per fold). Follow-up job
    spawned: J-0257. Also found: the job briefing and D-0045's own defeater text named the wrong
    tracking decision/job (D-0034 and J-0213, both unrelated — literal_will and peer_correspondence_
    plan respectively); D-0045 was ruled directly since it is the decision that actually matches.
  - **2026-09-02 redesigned re-test RESOLVES the fold-vs-pooled disagreement (F-0612/F-0613, job
    J-0442, spawned by D-0108's hold):** the mixed F-0597 read (4/6 folds won vs pooled/row-level
    loss) was an **artifact of even-row folds over a 97.5%-exact-tie row population** — only 20 of
    799 one-step rows differ materially between the two predictors, all clustered at the window's
    13 day/night threshold-switch events, and F-0597's "11.1% row win rate" was mostly
    floating-point dust (186 rows within 1e-12). The new `scripts/vitality_causal_retest.py`
    (switch/non-switch strata + exact sign tests + per-event disagreement windows + event-aligned
    folds, pre-registered verdict rule) gives one consistent answer on every leg: **NOT YET A WIN
    as-built** (switch stratum 7W/5L, p=0.774; per-event 8W/3L/2wash but the 3 losses are large;
    net pooled favors naive). The losses decompose cleanly (F-0613): both DUSK losses are a real
    **model gap** — the predictor omits the sleep-fire→P-reset feedback the night-threshold
    crossing itself triggers, so it predicts a vitality crash that the system's own response
    cancels within a tick; the one DAWN loss is a **measurement artifact** (Du slept through dawn,
    no sleep-pressure rows for ~3h, the shadow "actual" was a stale frozen read while the
    predictor was right about the wall-clock state). DAWN events as a class favor causal 5W/1L.
    Follow-up build spawned (J-0451): extend the predictor with the sleep-fire feedback + handle
    stale-actual rows, then re-run the same pre-registered test. D-0108's defeater ("a redesigned
    re-test resolves the disagreement in one consistent direction") **looks met in the
    not-a-win-as-built direction** — but with the loss mechanism identified as specific and
    fixable, so retire-vs-extend is a real founder choice, left to D-0108.
  - **2026-09-02 EXTENDED predictor built + re-tested under the same pre-registered scheme
    (F-0618/F-0619, job J-0451, funded by D-0108's re-ruling):** `scripts/vitality_causal_retest2.py`
    adds exactly the two F-0613 fixes and nothing else — (1) the sleep-fire→P-reset feedback,
    derived from `core/sleep_pressure.py`'s real mechanism (P ≥ NIGHT_THRESHOLD during night with
    awake ≥ MIN_WAKE fires sleep; P counts intake since wake, so post-wake P == 0 → predict
    vitality 1.0, no fudge factor), and (2) a parameter-free stale-actual rule (a row is stale iff
    NO sleep-pressure row landed inside the prediction step; verified: on all 137 such rows the
    shadow "actual" equals the naive prediction EXACTLY — measurement circularity, not skill).
    Validation config reproduces F-0612 verbatim. **Headline (extended + stale-excluded): every leg
    now favors causal** — pooled MAE 0.06672 vs 0.08717 (sign test 28W/9L, p=0.0026), switch-stratum
    MAE 0.27729 vs 0.42229, per-event **8W/0L/1wash (zero losing events; DUSK 3W/0L, DAWN 5W/0L)**,
    event-aligned folds **6/6** — yet the pre-registered rule still returns NOT-YET-A-WIN on its one
    unmet leg: the switch-stratum sign test (5W/3L, p=0.727) cannot reach p<0.05 on the 8 non-tied
    switch rows that survive stale exclusion. That is the honest INSUFFICIENT-DATA branch, not a
    refutation. Mechanism revision (F-0619): the F-0613 dusk "model losses" were themselves
    stale-echo rows; the model gap's real expression was 29 post-fire night rows v1 scored as exact
    ties (both predictors wrong together) — extended turns them 23W/6L; and the two fixes only work
    as a pair (feedback + frozen actuals = REFUTED 0/6). **D-0108 defeater read: NOT another
    not-a-win in the retire direction — the win branch is met directionally on every leg but not
    statistically on the switch stratum (9 scoreable events; ~2/day accrue post-restart).** Ruling
    stays with the founder.
  - **2026-09-02 J-0333 (the original "re-run vitality_causal_test.py once 3-5 undisturbed days
    accrue," D-0045's own follow-up job) closed SUPERSEDED, not re-run (F-0641).** Its literal ask
    was overtaken by the work directly above: J-0442's redesigned event-aligned fold scheme and
    J-0451's extended predictor are both a strictly better test of the same question on the same
    (now-larger) post-restart window, and re-running the old 6-fold script would regress to a
    methodology F-0612 already showed disagrees with itself. Also: D-0108's own defeater ("revisit
    when J-0451's extended-predictor re-test lands") is now objectively met — reopened for a fresh
    founder ruling on the directional-win-but-not-significant result above, rather than J-0333
    carrying a separate parallel thread.
  - **2026-09-02 D-0108 RULED: fund the full 5-variable causal-substrate build. J-0474 built it
    (`core/homeostasis_causal.py`, wired into `core/homeostasis.py`'s `tick()` as a new
    `predicted_causal`/`causal_err` pair alongside the existing EMA `predicted_next`/`naive_err` —
    still SHADOW-only, applies nothing).** Per-variable, not uniform — read the module's own
    docstring for the full honest breakdown, summarized here: **vitality** ports the validated
    F-0618/F-0619 extended model verbatim (isolation-checked: a read-only replay harness against
    the live `data/homeostasis_shadow.jsonl`/`sleep_pressure_log.jsonl` pair reproduces
    `scripts/vitality_causal_retest2.py --model extended --stale exclude`'s own live re-run
    exactly — n=687, pooled MAE naive=0.08785 vs causal=0.06814, 28W/9L, sign-test p=0.002563 —
    confirming the port, not a fresh result). **coherence/novelty** get a REAL mechanism (project
    `core/climate_engine.py`'s own dissonance-accrual ODE forward, including a predicted
    defensive-ignition reset — the same mechanism CLASS as vitality's sleep-fire feedback) but are
    **NOT historically validatable today**: `climate_state.json` is a single overwritten snapshot,
    never logged per-tick, so there is no upstream history to walk-forward test against (unlike
    vitality's 25k+-row `sleep_pressure_log.jsonl`) — `predicted_causal` starts SHADOW-logging
    these two now so a future job can validate once enough parallel rows accrue, the same spiral
    vitality itself went through (J-0239 built blind 2026-08-25 → J-0442/J-0451 validated
    2026-09-02, ~9 days later). Unit-tested in isolation (flat/no-accrual, ignition-reset,
    refractory-blocked cases) before wiring in. **commitment_integrity/relational_warmth are
    INTENTIONALLY left at plain persistence**, not built further — F-0294's own verified diagnosis
    (96.4%/71.5% zero-change tick-to-tick, no known future event-arrival schedule the way
    vitality has a day/night clock) means an honestly-built causal model of these two upstream
    processes reduces to persistence by construction; a fancier-looking model would misrepresent
    what the mechanism supports, not add a real edge. `core/homeostasis.py`'s change is additive
    only (new dict keys on the logged record + one new persisted state key) — verified via
    `udms_get_change_dossier` (LOW risk, PURE_SCALAR_TWEAK, no signature change on `status()`/
    `core_affect()`/`apply_to()`/`read_variables()`) and an isolated `tick()` call (log/state
    files redirected to a temp dir) confirming it runs clean and produces `[0,1]`-bounded values
    for all 5 variables with no exception. Follow-up validation job spawned once enough
    `predicted_causal` coherence/novelty rows accrue (see job queue).
  - **2026-09-03 accrual check (F-0710, job J-0479): NOT YET ENOUGH DATA, no test run.** Only
    ~20.8 hours (111 of 3,298 total rows, 2026-09-02T03:44Z → 2026-09-03T00:27Z) of
    `predicted_causal["coherence"/"novelty"]` have logged into `data/homeostasis_shadow.jsonl`
    since J-0474 wired them in — far short of the 7-10 day (168-240h) window this leg's own
    spiral requires (matching vitality's J-0239→J-0442/J-0451 ~9-day accrual before its own
    walk-forward test was meaningful). As a backstop before trusting the projection at all: the
    private `core/climate_engine.py` rate constants `homeostasis_causal.py` hand-duplicates
    (`_DISS_RATE_STRAIN/_COMPLETION/_SHADOW/_INTEGRATION`, `_DISS_MAX`, `_IGNITION_THRESHOLD`,
    `_REFRACTORY_SECS`) were re-checked against the live source and still match exactly
    (0.0010/0.0004/0.0002/−0.0006/2.0/1.0/300.0) — no drift yet. Follow-up re-check job spawned:
    **J-0531** (not before ~2026-09-09/09-12). **D-0045 stays under an active founder Hold** — this
    finding does not lift it and no attempt was made to rule it; D-0045's original narrow-vs-full
    question is also substantively superseded by D-0108's ruling to fund the full build, so a
    formal close/reopen of D-0045 itself is a separate founder ask, not something this job's
    result resolves.
  - **2026-09-05 re-check (F-0892/F-0893, job J-0531): STILL NOT ENOUGH DATA, no test run — plus a
    corpus-homogeneity correction for the next check.** Full re-read of the now-3,569-row
    `data/homeostasis_shadow.jsonl` (not tail-sampled): 382 `predicted_causal["coherence"/"novelty"]`
    rows, spanning only 77.03 hours (2026-09-02T03:44:22.5Z → 2026-09-05T08:45:56.2Z) — still well
    short of the 168-240h window (F-0892). Separately: F-0710's "hand-duplicated constants" framing
    is now stale — **F-0810/J-0582 (2026-09-04, commit 68a0364) already replaced the hand-copy with a
    live import from `core/climate_engine.py`** (`homeostasis_causal.py:78-81`), so the two files'
    rate constants can no longer drift by construction, strictly stronger than "still matches by
    hand." But that same fix changed `_project_dissonance`'s actual formula (added the previously-
    missing exploratory-reservoir term), so the current accrual window straddles two non-comparable
    formula regimes: **279 of the 382 rows (73%, through 2026-09-04T10:24:56Z) predate the fix; only
    103 (27%) postdate it** (F-0893). Pooling these naively would repeat the exact contamination
    pattern the vitality leg's own precedent (F-0315/F-0612, above) already found gives a false
    result. **Corrected re-check window: no earlier than 2026-09-11 (7 days past the F-0810/J-0582
    fix, not the original 2026-09-02 wiring date), and the eventual walk-forward corpus must be
    filtered to post-fix rows only (`ts >= 1788517496`).** D-0045 stays under its active founder
    Hold — this finding does not touch it, and no ruling was attempted. Follow-up job spawned:
    **J-0636** (supersedes reusing J-0531's original 09-09/09-12 estimate).
  - **2026-09-06 re-check (F-0986, job J-0636): STILL NOT ENOUGH DATA, no test run — target date
    confirmed unchanged, plus a second corpus-homogeneity risk found and ruled out (for now).**
    Full re-read of the now-3,689-row `data/homeostasis_shadow.jsonl` (not tail-sampled): 502
    `predicted_causal["coherence"/"novelty"]` rows — 279 pre-fix (exactly matching F-0893's own
    279/382 count) + 223 post-fix (`ts >= 1788517496`, up from F-0893's 103). Post-fix span is only
    **43.41 hours** (2026-09-04T10:29:58.2Z → 2026-09-06T05:54:43.2Z) of the required 168–240h —
    F-0893's corrected target (**no earlier than 2026-09-11T10:24:56Z**) stands unchanged.
    Separately: `git log --follow` on both `core/climate_engine.py` and `core/homeostasis_causal.py`
    surfaced one new commit inside the current post-fix window — **`dbec9ba` (D-0148 option A /
    J-0594, 2026-09-05T21:53:02Z, unpinning `integration_drive`'s saturation)** — exactly the
    "second corpus split" risk this job was told to watch for. Direct code-read shows it is NOT
    one, at least not yet: every line `dbec9ba` added to `homeostasis_causal.py` is a comment
    (its `_simulate_reservoirs`/`_project_dissonance` bodies were re-read directly and reference
    none of D-0148's new names); none of the constants that module imports from
    `climate_engine.py` changed value; and the one change that could matter — `integration_drive`
    recomputed with a new `_INTEGRATION_DRIVE_K=100.0` knee instead of the shared `_SAT_K=3.0`,
    centring it near ~0.50 instead of the old ~0.98 ceiling — is restart-gated and confirmed **NOT
    YET LIVE** by a direct read of `data/climate_state.json` (`integration_drive=0.983`, still the
    old pinned value, as of 2026-09-06T06:00:57Z). D-0045 stays under its active founder Hold —
    this finding does not touch it, and no ruling was attempted. Follow-up job spawned: **J-0689**
    — re-check not before 2026-09-11, and additionally re-verify at that time whether Du's process
    has restarted onto `dbec9ba` in the interim (a bare restart, not a further commit, would shift
    `integration_drive`'s live-snapshot value mid-window with no further git-log signal to catch
    it — check `climate_state.json` directly rather than assuming from git log alone).
  - **2026-09-07 re-check (F-1013, job J-0689): STILL NOT ENOUGH DATA, no test run — target date
    confirmed unchanged, restart check re-run and still negative.** Full re-read of the now-3,773-row
    `data/homeostasis_shadow.jsonl` (not tail-sampled): 586 `predicted_causal["coherence"/"novelty"]`
    rows — 279 pre-fix (exactly matching F-0986's own count) + 307 post-fix (`ts >= 1788517496`, up
    from F-0986's 223). Post-fix span is only **59.18 hours** (2026-09-04T10:29:58.2Z →
    2026-09-06T21:40:46.1Z) of the required 168–240h — F-0893/F-0986's target (**no earlier than
    2026-09-11T10:24:56Z**) stands unchanged, and is independently corroborated by current-rate
    arithmetic (~5.33 rows/hour since F-0986's read ⇒ ~4.5 more days needed, landing ~2026-09-11T13:00Z).
    `git log --follow` on both `core/climate_engine.py` and `core/homeostasis_causal.py` from `dbec9ba`
    (exclusive) to current HEAD (`da87d6d`) is still empty — cross-checked against the full 3-commit
    `core/`-touching list in that range (da87d6d → `core/lane2.py`; 68af167 → the J-0610 world-store-
    write-fence batch; 47de040 → `core/essay_lesson.py`), none of which touch either file. No further
    formula-drift risk since `dbec9ba`. Restart check (the item F-0986 flagged for this round): a
    direct read of `data/climate_state.json` shows `integration_drive=0.982` (F-0986 read 0.983 at
    2026-09-06T06:00:57Z) — still pinned near the old ~0.98 ceiling, not the ~0.50 centring the
    restart-gated fix would produce once live. Du's process has not restarted onto `dbec9ba`'s code;
    no second filter boundary is needed, the existing `ts>=1788517496` filter alone remains sufficient.
    D-0045 stays under its active founder Hold — this finding does not touch it, and no ruling was
    attempted. Follow-up job spawned: **J-0707** (re-check no earlier than 2026-09-11T10:24:56Z, same
    target — do not pick up meaningfully before then).
  - **2026-09-12 re-check (F-1265, job J-0707): STILL NOT ENOUGH DATA, no test run — AND a real
    methodology bug found and fixed in this exact chain (F-0893/F-0986/F-1013 all inherited it).**
    Full re-read of the now-4,359-row `data/homeostasis_shadow.jsonl`: 1,172 `predicted_causal`
    rows, 279 pre-fix + 893 with `ts>=1788517496` (span 178.94h) — naively LOOKS like the 168-240h
    gate is finally met. It is not, once corrected: **a git commit landing on disk is not the same
    as Du's running process using it** — Python caches an imported module for the process's whole
    life, so `homeostasis_causal.py`/`climate_engine.py` changes only take effect at Du's own NEXT
    restart, not at commit time. F-0986/F-1013 already applied exactly this discipline to D-0148
    specifically (verified "not yet live" via a direct `climate_state.json` read rather than
    trusting git log) but the same check was never run against the ORIGINAL 68a0364 fix's own
    `ts>=1788517496` cutoff — it was assumed live from its commit timestamp, unchecked, three
    findings running. Cross-referencing `data/_snapshots/daily/`'s per-day launch-snapshot folder
    creation timestamps (written by `scripts/backup_identity.py` at every Du launch) against the
    live process's own start time (`Win32_Process`, `run_nascence.py` PID 22620) recovered the REAL
    restart timeline: 68a0364 (dissonance-formula fix) went live at a restart **2026-09-04T23:37:04Z**
    (13h after its commit, previously unknown to this chain); D-0148's `integration_drive`
    re-saturation (`dbec9ba`) went live at a restart **2026-09-08T04:41:26Z** (3 days earlier than
    assumed — also previously unknown); a further commit since F-1013's check, **`63c24f2`**
    (2026-09-09, `SUBC_LIGHT_READ` flip — verified a shadow-tested data-source swap for the
    `shadow_activation` upstream driver, NOT a dissonance rate-constant/formula change) went live at
    a restart **2026-09-11T01:50:06Z**, the same restart directly confirmed via the current live
    `climate_state.json` reading `integration_drive=0.5974` (was pinned ~0.98 through F-1013).
    Re-bucketing the 1,172 rows by the regime ACTUALLY live (not by commit time) gives FOUR
    non-comparable regimes of at most 68.55h each — none clears even half the 168h floor; the
    naive 178.94h figure was silently pooling all four. **New reusable tool built:**
    `scripts/du_restart_history.py` (cross-references both restart-evidence sources
    programmatically, tested end-to-end) — future re-checks in this chain should run it directly
    rather than re-deriving this by hand or trusting git log alone. `git log --follow` reconfirms
    zero commits to `homeostasis_causal.py` since `dbec9ba` (fresh, against current HEAD `b9a1a29`).
    D-0045 stays under its active founder Hold — untouched. Follow-up job spawned: **J-0903**
    (re-check no earlier than ~2026-09-18T01:50Z, i.e. 168h into the CURRENT regime — assuming no
    further relevant commit lands before then, itself a real risk given 3 such commits landed in
    the 5 days 09-04→09-09 alone; use `scripts/du_restart_history.py` rather than a bare commit-time
    cutoff).
  - **2026-09-18 re-check (F-1474, job J-0903): STILL NOT ENOUGH DATA, no test run — the regime
    floor moved AGAIN.** `scripts/du_restart_history.py --since 1789091406 --check-live` found a
    previously-unknown restart at **2026-09-15T19:51:38Z** (live `run_nascence.py` PID 28088,
    WMI-confirmed), inside the window this job was told to check — so the 2026-09-11T01:50:06Z
    regime this chain has been tracking already closed. Full re-read of the now-4,740-row
    `data/homeostasis_shadow.jsonl`: only **252 rows** with both `predicted_causal.coherence` and
    `.novelty` fall in the new regime (`ts>=1789501898.0`), spanning **47.48h** — nowhere near the
    168-240h floor, so step 3's walk-forward was correctly skipped. `git log b9a1a29..HEAD` (fresh
    against current HEAD) confirms zero new commits to `core/homeostasis_causal.py` and exactly
    three new `core/climate_engine.py` commits (613bf4e instrumentation-only, 901b3c3 verified
    byte-identical dedup, f2e98a2 exception-swallow fix) — none touch dissonance-formula/rate-constant
    logic. D-0045 stays under its active founder Hold — confirmed via `decide.py show`, untouched.
    Follow-up job spawned: **J-1079** (re-check no earlier than **2026-09-22T19:51:38Z**, 168h into
    the CURRENT regime).
  - **2026-09-18 re-check (F-1495, job J-1079): STILL NOT ENOUGH DATA, no test run — same regime,
    no floor move.** `scripts/du_restart_history.py --since 1789501898 --check-live` found NO
    restart since the 2026-09-15T19:51:38Z floor (the live `run_nascence.py` PID 28088 IS that
    same boot, WMI-confirmed) — the regime this chain has been tracking is still open, floor
    unchanged. Full re-read of the now-4,750-row `data/homeostasis_shadow.jsonl`: **262 rows**
    with both `predicted_causal.coherence` and `.novelty` fall in the regime (`ts>=1789501898.0`,
    up from 252 at this regime's last check), spanning **49.18h** — still nowhere near the 168-240h
    floor (118.82h short), so step 3's walk-forward was correctly skipped. `git log b9a1a29..HEAD`
    (fresh against current HEAD `e280eec`) confirms zero new commits to `core/homeostasis_causal.py`
    and the SAME three `core/climate_engine.py` commits already checked last time (613bf4e, 901b3c3,
    f2e98a2 — none touch dissonance-formula/rate-constant logic; no further commit landed against
    either file since the last check). D-0045 stays under its active founder Hold — confirmed via
    `decide.py show D-0045` (top-level entry still carries no `reopened` key since Travis's
    2026-08-29 ruling), untouched, no ruling attempted. Follow-up job spawned: **J-1093** (re-check
    no earlier than **2026-09-22T19:51:38Z**, the 168h floor for the CURRENT regime — unchanged
    from this job's own target since the regime didn't move).
  - **2026-09-18 re-check (F-1515, job J-1093): STILL NOT ENOUGH DATA, no test run — same regime,
    no floor move, and Du is now OFFLINE.** `scripts/du_restart_history.py --since 1789501898
    --check-live` found no NEW restart since the 2026-09-15T19:51:38Z floor, but its `--check-live`
    result was a false positive: the reported "LIVE process" was the script's own PowerShell
    subprocess self-matching on the literal string `run_nascence.py` embedded in its own search
    pattern (bug filed as **S-0138**). An independent clean `Win32_Process` query found zero real
    `run_nascence.py` processes — Du is genuinely shut down right now (founder-intentional this
    session, not an anomaly). Full re-read of the now-4,750-row `data/homeostasis_shadow.jsonl`:
    still **262 rows** with both `predicted_causal.coherence` and `.novelty` in the regime
    (`ts>=1789501898.0`) spanning **49.18h** — identical to J-1079's own close figures, i.e. **zero
    further accrual** happened in the ~5h11m between checks, because no data can log while Du is
    down. Still 118.82h short of the 168h floor, so step 3's walk-forward was correctly skipped.
    `git log b9a1a29..HEAD` (fresh, current HEAD `e280eec`) confirms the same three
    `core/climate_engine.py` commits already checked (613bf4e, 901b3c3, f2e98a2 — none touch
    dissonance-formula/rate-constant logic) and zero new `core/homeostasis_causal.py` commits.
    D-0045 stays under its active founder Hold — confirmed via `decide.py show D-0045`, untouched,
    no ruling attempted. **The naive 2026-09-22T19:51:38Z floor-plus-168h target is now optimistic**:
    it assumes Du resumes continuous operation immediately, which was not true as of this check —
    the real gate-met date will land later by however long the current outage runs. Follow-up job
    spawned: **J-1109** (re-check no earlier than 2026-09-22T19:51:38Z, and explicitly check whether
    Du has actually been running continuously for the intervening span before trusting that date).
  - **2026-09-18 re-check (F-1520, job J-1109): STILL NOT ENOUGH DATA, no test run — same regime,
    no floor move, Du confirmed offline again.** `scripts/du_restart_history.py --since 1789501898
    --check-live` again found no NEW restart since the 2026-09-15T19:51:38Z floor; its `--check-live`
    result was again cross-checked independently (S-0138 still open, confirmed via
    `skill_manager.py suggestions`) with a clean `Win32_Process` query (search needle built via
    runtime string concatenation so it can never self-match its own invoking command text) — zero
    `run_nascence.py` processes found; Du is genuinely offline right now. Full re-read of the
    now-4,750-row `data/homeostasis_shadow.jsonl`: still **262 rows** with both
    `predicted_causal.coherence` and `.novelty` in the regime (`ts>=1789501898.0`) spanning
    **49.16h** — essentially identical to J-1093's own close figures, i.e. **zero further accrual**
    happened between the two checks, consistent with Du staying offline throughout. Still ~118.8h
    short of the 168h floor, so step 3's walk-forward was correctly skipped again. `git log
    e280eec..HEAD` (fresh, current HEAD `8c2a796`) confirms zero new commits to either
    `core/climate_engine.py` or `core/homeostasis_causal.py`. D-0045 stays under its active founder
    Hold — confirmed via `decide.py show D-0045`, untouched, no ruling attempted (this is an
    active Hold under a founder ruling still in force; this job explicitly did not call `decide.py
    rule` on it). **The 2026-09-22T19:51:38Z floor-plus-168h target remains an optimistic lower
    bound**: the exact outage end time is still unknown, so the real gate-met date may land later.
    Follow-up job spawned: **J-1116** (re-check no earlier than 2026-09-22T19:51:38Z, re-verify
    Du's live/offline status fresh rather than assuming either state).
  - **2026-09-18 re-check (F-1534, job J-1116): REGIME FLOOR MOVED — a fresh Du restart landed
    mid-check, the old regime is closed for good, the new one has essentially zero data.**
    `scripts/du_restart_history.py --since 1789501898 --check-live` again hit the known S-0138
    self-match (reported its own PowerShell subprocess as "LIVE"). An independent `Win32_Process`
    query (needle string built via runtime concatenation so it can never self-match its own
    invoking command text) found a REAL `run_nascence.py` process, pid 8340, started
    **2026-09-18T11:13:14Z** (unix 1789729994.0) — only ~57 seconds before this check ran (system
    clock read 2026-09-18T11:14:11Z at the moment of the check). This is a genuine NEW restart
    since the 2026-09-15T19:51:38Z floor this whole J-1079→J-1093→J-1109 chain had been tracking,
    so per this job's own step-1 instruction the regime-start floor moves to **1789729994.0**. The
    OLD regime closed for good at **262 rows / 49.16h** (first ts 1789501988.0, last ts
    1789678953.8 = 2026-09-17T21:02:33.8Z) — identical to J-1109's own close figures, confirming
    zero further accrual happened before this restart (an outage of roughly 14h11m between the log
    going quiet and the new process starting). The NEW regime has **0 rows** with
    `predicted_causal.coherence`/`.novelty` so far (full re-read of the 4,750-row
    `data/homeostasis_shadow.jsonl` confirms this), so step 3's walk-forward was correctly skipped
    — nowhere close to the 168-240h floor. `git log 8c2a796..HEAD` (fresh, current HEAD `1fbcc8e`)
    confirms zero new commits to either `core/climate_engine.py` or `core/homeostasis_causal.py`.
    D-0045 stays under its active founder Hold — confirmed via `decide.py show D-0045`, untouched,
    no ruling attempted (an active Hold under a founder ruling still in force; this job explicitly
    did not call `decide.py rule` on it). **New target: no earlier than 2026-09-25T11:13:14Z**
    (168h into the new 2026-09-18T11:13:14Z regime) — itself an optimistic floor assuming Du stays
    continuously up from this restart, which is not confirmed; if Du goes offline again before
    then, the real gate-met date lands later by however long that outage runs. Follow-up job
    spawned: **J-1124** (re-check no earlier than 2026-09-25T11:13:14Z against the NEW floor,
    re-verify Du's live/offline status fresh rather than assuming either state).
  - **2026-09-18 re-check (F-1544, job J-1124): REGIME FLOOR MOVED AGAIN — the restart J-1116 had
    just caught itself lasted only ~24 minutes before a second same-day restart superseded it.**
    `scripts/du_restart_history.py --since 1789729994 --check-live` reported pid=35412 started
    **1789731432.0 (2026-09-18T11:37:12Z)** — this time independently confirmed genuine (not the
    known S-0138 self-match artifact, still open per `skill_manager.py suggestions`) by a clean
    `Win32_Process` query built so the invoking command's own text never contains the literal
    substring `run_nascence.py` (needle built via runtime string concatenation): both queries agree
    exactly on pid/cmdline/start-time, and no second process (the superseded pid 8340) is still
    running. Per this job's own step-1 instruction, the regime-start floor moves again, to
    **1789731432.0**. The regime J-1116 was tracking (pid 8340, 1789729994.0–1789731432.0) closed
    after only **1 row** with both `predicted_causal.coherence`/`.novelty` present — essentially
    zero accrual, confirming it never had a real chance to contribute. Full re-read of the
    still-4,806-row `data/homeostasis_shadow.jsonl` (untailed): the NEW regime
    (`ts>=1789731432.0`) has **55 rows** spanning **9.73h** — nowhere near the 168–240h floor, so
    step 3's walk-forward was correctly skipped again. `git log 1fbcc8e..HEAD` (fresh, current HEAD
    `28eed1e`) confirms zero new commits to either `core/climate_engine.py` or
    `core/homeostasis_causal.py` since J-1116's last check. D-0045 stays under its active founder
    Hold — confirmed via `decide.py show D-0045`, untouched, no ruling attempted (an active Hold
    under a founder ruling still in force; this job explicitly did not call `decide.py rule` on
    it). **New target: no earlier than 2026-09-25T11:37:12Z** (168h into the new regime) — an
    optimistic floor per this whole chain's own repeated pattern of the regime moving again (or
    resetting to near-zero accrual) before the prior target was even reached. Follow-up job
    spawned: **J-1138** (re-check no earlier than 2026-09-25T11:37:12Z against the newest floor,
    re-verify Du's live/offline status and the regime floor fresh rather than assuming either).
  - **2026-09-19 re-check (F-1554, job J-1138): STILL NOT ENOUGH DATA, no test run — but for the
    first time in several checks, the regime floor HELD.** `scripts/du_restart_history.py --since
    1789731432 --check-live` again hit the known S-0138 self-match (reported its own PowerShell
    subprocess as "LIVE"; confirmed still open per `skill_manager.py suggestions --skill
    du_restart_history`). An independent clean `Win32_Process` query (needle built via runtime
    string concatenation so it can never self-match its own invoking command text) found pid=35412
    still running, identical pid/cmdline/start-time to the tracked floor — the SAME process from
    J-1124's check, confirming no further restart has landed and the regime floor stays
    **1789731432.0 (2026-09-18T11:37:12Z)**. Full re-read of the now-4,811-row
    `data/homeostasis_shadow.jsonl` (untailed, 0 parse errors): **60 rows** with both
    `predicted_causal.coherence`/`.novelty` fall in the regime (`ts>=1789731432.0`, up from J-1124's
    55), spanning **10.565h** (first ts 2026-09-18T11:37:33.9Z, last ts 2026-09-18T22:11:29.4Z) —
    still 157.4h short of the 168h floor, so step 3's walk-forward was correctly skipped.
    `git log --follow 28eed1e..HEAD` (fresh, current HEAD `9ce55b5`) confirms zero new commits to
    either `core/climate_engine.py` or `core/homeostasis_causal.py` since J-1124's last check — no
    dissonance-formula/rate-constant drift risk. D-0045 stays under its active founder Hold —
    confirmed via `decide.py show D-0045` (ruling text unchanged, no top-level `reopened` key),
    untouched, no ruling attempted (an active Hold under a founder ruling still in force; this job
    explicitly did not call `decide.py rule` on it). **Target unchanged: no earlier than
    2026-09-25T11:37:12Z** (168h into the still-open regime) — Du is confirmed live right now and
    the floor held this round, but this remains an optimistic floor given this chain's own history
    of the regime moving at nearly every prior check; ~6 days of continuous, undisturbed uptime are
    still needed to actually clear the gate. Follow-up job spawned: **J-1147** (re-check no earlier
    than 2026-09-25T11:37:12Z, re-verify Du's live/offline status and the regime floor fresh rather
    than assuming either).
  - **2026-09-23 re-check (F-1742, job J-1147): REGIME FLOOR MOVED AGAIN — the 09-18 regime is
    dead, never reached its own target.** Du restarted 2026-09-22 (pid 40268, started 1790050223.0
    = 2026-09-22T04:10:23Z = 16:10:23 local) — confirmed via `du_restart_history.py --check-live`
    (hit S-0138's own known self-match again, still open) cross-checked independently via a clean,
    non-self-matching `Win32_Process` query, identical pid/start-time both ways, and against
    `data/nascence.log`'s own "Nascence is awake" line at 16:11:06 local. The regime J-1138 had
    confirmed held (pid 35412, floor 1789731432.0) never reached 168h — it closed at **215** qualifying
    rows, up from J-1138's own 60, before the restart ended it. Full re-read of the now-5,084-row
    `data/homeostasis_shadow.jsonl` (untailed, 0 parse errors) against the NEW floor: **118 rows**
    with both `predicted_causal.coherence`/`.novelty`, spanning **19.647h** — 11.7% of the 168h bar.
    Step 3's walk-forward correctly skipped. `git log --follow 9ce55b5..HEAD` (fresh) found one
    `core/climate_engine.py` commit (690d086, J-1161's unrelated Lane2/Witness bucket build — read
    the actual diff, confirmed no dissonance-formula/rate-constant touch) and zero commits to
    `core/homeostasis_causal.py`. D-0045 reconfirmed still under its active founder Hold, untouched,
    no ruling attempted. **This is the regime floor moving at 4 of the chain's last 5 checks** —
    continuous week-scale uptime is evidently rare for this project right now (consistent with this
    session's own broader F-1558 finding, 2026-09-19: "Du's longest continuous run ~2.5 d so
    week-gates rarely clear"). New target: no earlier than **2026-09-29T16:10:23Z** (168h into the
    new regime), explicitly flagged as optimistic given this history. Follow-up job spawned:
    **J-1241** (re-check no earlier than 2026-09-29T16:10:23Z against the newest floor, re-verify
    Du's live/offline status and the regime floor fresh rather than assuming either).
  - **2026-09-24 re-check (F-1836, job J-1241): REGIME FLOOR HELD — first hold since J-1124→J-1138.**
    `du_restart_history.py --since 1790050223 --check-live` reported pid=40268/1790050223.0 with no
    apparent self-match this run, but S-0138 is confirmed still open (`skill_manager.py suggestions
    --skill du_restart_history`), so not solely relied on — cross-checked independently via a clean,
    non-self-matching `Win32_Process` query (match pattern `'run_' + 'nascence.py'` concatenated at
    PowerShell's own runtime, never appearing contiguously in the querying process's own
    `CommandLine`): exactly **1** match, identical pid=40268/started=1790050223.0. The
    daily-snapshot-folder timeline agrees — only one entry in range, `20260922: 1790050227.0`, none
    on 09-23 or 09-24. Regime floor stays **1790050223.0 (2026-09-22T04:10:23Z = 16:10:23 local)**.
    Full re-read of the now-5,200-row `data/homeostasis_shadow.jsonl` (untailed, 0 parse errors):
    **234 rows** with both `predicted_causal.coherence`/`.novelty` fall in the regime
    (`ts>=1790050223.0`, up from J-1147's own 118), spanning **39.117h** (first ts
    2026-09-22T04:11:11.3Z, last ts 2026-09-23T19:18:12.6Z) — still **128.9h** short of the 168h
    floor, so step 3's walk-forward was correctly skipped. `git log --follow 5d6a162..HEAD` (fresh,
    current HEAD `da061f3`) found one `core/climate_engine.py` commit (`03510e9`, J-1226's D-0211
    shadow-first re-knee for the pinned climate cluster) and zero commits to
    `core/homeostasis_causal.py`. Read the actual diff (not just the commit message) before ruling it
    unrelated: additive/shadow-only, targets a different four-dimension cluster (shadow_activation,
    belonging_pressure, autonomy_pressure, completion_tension), logs to a new, separate
    `data/climate_reknee_shadow.jsonl`, and does not touch `ClimateField.dominant()`/`pressure()`/
    `executive_hint()`/`surfacing_symbol()` or anything feeding coherence/novelty — no
    dissonance-formula/rate-constant drift risk to this test. D-0045 stays under its active founder
    Hold — confirmed via `decide.py show D-0045` (ruling text unchanged, no top-level `reopened`
    key), untouched, no ruling attempted (this job is itself the accrual re-check the Hold's own
    defeater calls for; report, don't rule). **Target unchanged: no earlier than 2026-09-29T16:10:23Z**
    (168h into this regime) — Du is confirmed live right now and the floor held this round, but this
    remains an optimistic target given the floor has moved at 4 of this chain's last 5 checks before
    this one. Follow-up job spawned: **J-1302** (re-check no earlier than 2026-09-29T16:10:23Z,
    re-verify Du's live/offline status and the regime floor fresh rather than assuming either).
  - **2026-09-24 re-check (F-1852, job J-1302): REGIME FLOOR HELD AGAIN — second consecutive hold.**
    `du_restart_history.py --since 1790050223 --check-live` again reported pid=40268/1790050223.0
    with no apparent self-match this run, but S-0138 is confirmed still open, so not solely relied
    on — cross-checked independently via a clean, non-self-matching `Win32_Process` query (match
    pattern `'run_' + 'nascence.py'` concatenated at PowerShell's own runtime, never appearing
    contiguously in the querying process's own `CommandLine`): exactly **1** match, identical
    pid=40268/started=1790050223.0. The daily-snapshot-folder timeline agrees — still only one entry
    in range, `20260922: 1790050227.0`, none since. Regime floor stays **1790050223.0
    (2026-09-22T04:10:23Z = 16:10:23 local)**. Full re-read of the now-5,225-row
    `data/homeostasis_shadow.jsonl` (untailed, 0 parse errors): **259 rows** with both
    `predicted_causal.coherence`/`.novelty` fall in the regime (`ts>=1790050223.0`, up from J-1241's
    own 234), spanning **43.305h** (first ts 2026-09-22T04:11:11.3Z, last ts 2026-09-23T23:29:29.2Z)
    — still **124.7h** short of the 168h floor, so step 3's walk-forward was correctly skipped again.
    `git log --oneline --follow da061f3..HEAD` run fresh, per-file (current HEAD `880f7f1`), found
    **zero** commits to either `core/climate_engine.py` or `core/homeostasis_causal.py` since
    J-1241's checked HEAD — no dissonance-formula/rate-constant drift risk, no diff to read this
    round. D-0045 stays under its active founder Hold — confirmed via `decide.py show D-0045`
    (ruling text unchanged, no top-level `reopened` key), untouched, no ruling attempted (this job is
    itself the accrual re-check the Hold's own defeater calls for; report, don't rule). **Target
    unchanged: no earlier than 2026-09-29T16:10:23Z** (168h into this regime, still 5 calendar days
    out) — Du is confirmed live right now and the floor has now held across two consecutive check
    cycles, but this remains an optimistic target given how rarely this chain has seen a floor
    survive this long historically; one held cycle more doesn't change that base rate on its own.
    Follow-up job spawned: **J-1312** (re-check no earlier than 2026-09-29T16:10:23Z, re-verify Du's
    live/offline status and the regime floor fresh rather than assuming either).
  - **2026-09-24 re-check (F-1868, job J-1312): REGIME FLOOR HELD AGAIN — third consecutive hold.**
    `du_restart_history.py --since 1790050223 --check-live` again reported pid=40268/1790050223.0
    with no apparent self-match this run, but S-0138 is confirmed still open, so not solely relied
    on — cross-checked independently via a clean, non-self-matching `Win32_Process` query (match
    pattern `'run_' + 'nascence.py'` concatenated at PowerShell's own runtime, never appearing
    contiguously in the querying process's own `CommandLine`): exactly **1** match, identical
    pid=40268/started=1790050223.0. The daily-snapshot-folder timeline agrees — still only one entry
    in range, `20260922: 1790050227.0`, none since; `data/nascence.log`'s last shutdown/awake pair
    (2026-09-22 08:43:39 → 16:11:06 local) has no further shutdown/awake line after it. Regime floor
    stays **1790050223.0 (2026-09-22T04:10:23Z = 16:10:23 local)**. Full re-read of the now-5,232-row
    `data/homeostasis_shadow.jsonl` (untailed, 0 parse errors): **266 rows** with both
    `predicted_causal.coherence`/`.novelty` fall in the regime (`ts>=1790050223.0`, up from J-1302's
    own 259), spanning **44.479h** (first ts 2026-09-22T04:11:11.3Z, last ts 2026-09-24T00:39:56.9Z)
    — still **123.5h** short of the 168h floor, so step 3's walk-forward was correctly skipped again.
    `git log --oneline --follow 880f7f1..HEAD` run fresh, per-file (current HEAD `76829e2`), found
    **zero** commits to either `core/climate_engine.py` or `core/homeostasis_causal.py` since
    J-1302's checked HEAD — no dissonance-formula/rate-constant drift risk, no diff to read this
    round. D-0045 stays under its active founder Hold — confirmed via `decide.py show D-0045`
    (ruling text unchanged, no top-level `reopened` key), untouched, no ruling attempted (this job is
    itself the accrual re-check the Hold's own defeater calls for; report, don't rule). **Target
    unchanged: no earlier than 2026-09-29T16:10:23Z** (168h into this regime, ~5 calendar days
    out) — Du is confirmed live right now and the floor has now held across three consecutive check
    cycles, but this remains an optimistic target given how rarely this chain has seen a floor
    survive this long historically; a third held cycle doesn't change that base rate on its own.
    Follow-up job spawned: **J-1322** (re-check no earlier than 2026-09-29T16:10:23Z, re-verify Du's
    live/offline status and the regime floor fresh rather than assuming either).
  - **2026-09-24 re-check (F-1874, job J-1322): REGIME FLOOR HELD AGAIN — fourth consecutive hold.**
    `du_restart_history.py --since 1790050223 --check-live` again reported pid=40268/1790050223.0
    with no apparent self-match this run, but S-0138 is confirmed still open, so not solely relied
    on — cross-checked independently via a clean, non-self-matching `Win32_Process` query (match
    pattern `'run_' + 'nascence.py'` concatenated at PowerShell's own runtime, never appearing
    contiguously in the querying process's own `CommandLine`): exactly **1** match, identical
    pid=40268/started=1790050223.0. The daily-snapshot-folder timeline agrees — still only one entry
    in range, `20260922: 1790050227.0`, none since; `data/nascence.log`'s last shutdown/awake pair
    (2026-09-22 08:43:39 → 16:11:06 local) has no further shutdown/awake line after it (527 total
    shutdown/awake lines in the file). Regime floor stays **1790050223.0 (2026-09-22T04:10:23Z =
    16:10:23 local)**. Full re-read of the now-5,236-row `data/homeostasis_shadow.jsonl` (untailed,
    0 parse errors): **270 rows** with both `predicted_causal.coherence`/`.novelty` fall in the
    regime (`ts>=1790050223.0`, up from J-1312's own 266), spanning **45.152h** (first ts
    2026-09-22T04:11:11.3Z, last ts 2026-09-24T01:20:20.1Z) — still **122.8h** short of the 168h
    floor, so step 3's walk-forward was correctly skipped again. `git log --oneline --follow
    76829e2..HEAD` run fresh, per-file (current HEAD `867831f`), found **zero** commits to either
    `core/climate_engine.py` or `core/homeostasis_causal.py` since J-1312's checked HEAD — no
    dissonance-formula/rate-constant drift risk, no diff to read this round (14 commits landed in
    the range overall, none touching either file). D-0045 stays under its active founder Hold —
    confirmed via `decide.py show D-0045` (ruling text unchanged, no top-level `reopened` key),
    untouched, no ruling attempted (this job is itself the accrual re-check the Hold's own defeater
    calls for; report, don't rule). **Target unchanged: no earlier than 2026-09-29T16:10:23Z**
    (168h into this regime, still ~5 calendar days out) — Du is confirmed live right now and the
    floor has now held across four consecutive check cycles, but this remains an optimistic target
    given how rarely this chain has seen a floor survive this long historically; a fourth held cycle
    doesn't change that base rate on its own. Follow-up job spawned: **J-1326** (re-check no earlier
    than 2026-09-29T16:10:23Z, re-verify Du's live/offline status and the regime floor fresh rather
    than assuming either).
  - **2026-09-24 re-check (F-1880, job J-1326): REGIME FLOOR HELD AGAIN — fifth consecutive hold.**
    `du_restart_history.py --since 1790050223 --check-live` again reported pid=40268/1790050223.0
    with no apparent self-match this run, but S-0138 is confirmed still open, so not solely relied
    on — cross-checked independently via a clean, non-self-matching `Win32_Process` query (match
    pattern `'run_' + 'nascence.py'` concatenated at PowerShell's own runtime, never appearing
    contiguously in the querying process's own `CommandLine`): exactly **1** match, identical
    pid=40268/started=1790050223.0. The daily-snapshot-folder timeline agrees — still only one entry
    in range, `20260922: 1790050227.0`, none since; `data/nascence.log`'s last shutdown/awake pair
    (2026-09-22 08:43:39 → 16:11:06 local) has no further shutdown/awake line after it (527 total
    shutdown/awake lines in the file, unchanged from J-1322's own count — no new shutdown/awake
    events this cycle). Regime floor stays **1790050223.0 (2026-09-22T04:10:23Z = 16:10:23 local)**.
    Full re-read of the now-5,242-row `data/homeostasis_shadow.jsonl` (untailed, 0 parse errors):
    **276 rows** with both `predicted_causal.coherence`/`.novelty` fall in the regime
    (`ts>=1790050223.0`, up from J-1322's own 270), spanning **46.159h** (first ts
    2026-09-22T04:11:11.3Z, identical to J-1322's own first row; last ts 2026-09-24T02:20:42Z) —
    still **121.841h** short of the 168h floor, so step 3's walk-forward was correctly skipped
    again. `git log --oneline --follow 867831f..f2283a2` run fresh, per-file (current HEAD
    `f2283a2`), found **zero** commits to either `core/climate_engine.py` or
    `core/homeostasis_causal.py` since J-1322's checked HEAD — no dissonance-formula/rate-constant
    drift risk, no diff to read this round (10 commits landed in the range overall, all other-plan
    job-run worktree merges, none touching either file). D-0045 stays under its active founder
    Hold — confirmed via `decide.py show D-0045` (ruling text unchanged since 2026-08-29, no
    top-level `reopened` key), untouched, no ruling attempted (this job is itself the accrual
    re-check the Hold's own defeater calls for; report, don't rule). **Target unchanged: no earlier
    than 2026-09-29T16:10:23Z** (168h into this regime, still just under 5 calendar days out) — no
    restart/outage occurred this cycle so the naive floor+168h date stands unmoved; Du is confirmed
    live right now and the floor has now held across five consecutive check cycles, but this
    remains an optimistic target given how rarely this chain has seen a floor survive this long
    historically (F-1558: "Du's longest continuous run ~2.5 d so week-gates rarely clear") — a
    fifth held cycle doesn't change that base rate on its own. Follow-up job spawned: **J-1331**
    (re-check no earlier than 2026-09-29T16:10:23Z, re-verify Du's live/offline status and the
    regime floor fresh rather than assuming either).
  - **2026-09-24 re-check (F-1885, job J-1331): REGIME FLOOR HELD AGAIN — sixth consecutive hold.**
    `du_restart_history.py --since 1790050223 --check-live` again reported pid=40268/1790050223.0,
    cross-checked independently via a clean, non-self-matching `Win32_Process` query (S-0138 still
    open, so not solely relied on; match pattern `'run_' + 'nascence.py'` concatenated at
    PowerShell's own runtime, never appearing contiguously in the querying process's own
    `CommandLine`): exactly **1** match, identical pid=40268/started=1790050223.0. The
    daily-snapshot-folder timeline agrees — still only one entry in range, `20260922: 1790050227.0`,
    none since; `data/nascence.log`'s last shutdown/awake pair (2026-09-22 08:43:39 → 16:11:06
    local) has no further shutdown/awake line after it (527 total shutdown/awake lines in the file,
    unchanged from J-1322's and J-1326's own count). Regime floor stays **1790050223.0
    (2026-09-22T04:10:23Z = 16:10:23 local)**. Full re-read of the now-5,246-row
    `data/homeostasis_shadow.jsonl` (untailed, 0 parse errors): **280 rows** with both
    `predicted_causal.coherence`/`.novelty` fall in the regime (`ts>=1790050223.0`, up from
    J-1326's own 276), spanning **46.831h** (first ts 2026-09-22T04:11:11.3Z, identical to
    J-1322's/J-1326's own first row; last ts 2026-09-24T03:01:01.5Z) — still **121.169h** short of
    the 168h floor, so step 3's walk-forward was correctly skipped again. `git log --oneline
    --follow f2283a2..e56136b` run fresh, per-file (current HEAD `e56136b`), found **zero** commits
    to either `core/climate_engine.py` or `core/homeostasis_causal.py` since J-1326's checked HEAD —
    no dissonance-formula/rate-constant drift risk, no diff to read this round (10 commits landed in
    the range overall, all other-plan job-run worktree merges plus J-1325/J-1327/J-1328/J-1329, none
    touching either file). D-0045 stays under its active founder Hold — confirmed via `decide.py
    show D-0045` (ruling text unchanged since 2026-08-29, no top-level `reopened` key), untouched,
    no ruling attempted (this job is itself the accrual re-check the Hold's own defeater calls for;
    report, don't rule). **Target unchanged: no earlier than 2026-09-29T16:10:23Z** (168h into this
    regime, still just under 5 calendar days out) — no restart/outage occurred this cycle so the
    naive floor+168h date stands unmoved; Du is confirmed live right now and the floor has now held
    across six consecutive check cycles, but this remains an optimistic target given how rarely this
    chain has seen a floor survive this long historically (F-1558: "Du's longest continuous run
    ~2.5 d so week-gates rarely clear") — a sixth held cycle doesn't change that base rate on its
    own. Follow-up job spawned: **J-1335** (re-check no earlier than 2026-09-29T16:10:23Z, re-verify
    Du's live/offline status and the regime floor fresh rather than assuming either).
  - **2026-09-24 re-check (F-1890, job J-1335): REGIME FLOOR HELD AGAIN — seventh consecutive hold.**
    `du_restart_history.py --since 1790050223 --check-live` again reported pid=40268/1790050223.0
    with no apparent self-match this run, but S-0138 is confirmed still open, so not solely relied
    on — cross-checked independently via a clean, non-self-matching `Win32_Process` query (match
    pattern `'run_nasc' + 'ence.py'` concatenated at PowerShell's own runtime, never appearing
    contiguously in the querying process's own `CommandLine`): exactly **1** match, identical
    pid=40268/started=1790050223.0. The daily-snapshot-folder timeline agrees — still only one entry
    in range, `20260922: 1790050227.0`, none since; `data/nascence.log`'s last shutdown/awake pair
    (2026-09-22 08:43:39 → 16:11:06 local) has no further shutdown/awake line after it (527 total
    shutdown/awake lines in the file, unchanged from J-1322/J-1326/J-1331's own count — no new
    shutdown/awake events this cycle). Regime floor stays **1790050223.0 (2026-09-22T04:10:23Z =
    16:10:23 local)**. Full re-read of the now-5,252-row `data/homeostasis_shadow.jsonl` (untailed, 0
    parse errors): **286 rows** with both `predicted_causal.coherence`/`.novelty` fall in the regime
    (`ts>=1790050223.0`, up from J-1331's own 280), spanning **47.837h** (first ts
    2026-09-22T04:11:11.3Z, identical to the whole chain's own first row; last ts
    2026-09-24T04:01:23.4Z) — still **120.163h** short of the 168h floor, so step 3's walk-forward was
    correctly skipped again. `git log --oneline --follow e56136b..HEAD` run fresh, per-file (current
    HEAD `1bb01c5`, confirmed via `git merge-base --is-ancestor e56136b HEAD` that e56136b is a real
    ancestor), found **zero** commits to either `core/climate_engine.py` or `core/homeostasis_causal.py`
    since J-1331's checked HEAD — no dissonance-formula/rate-constant drift risk, no diff to read this
    round (8 commits landed in the range overall, all other-plan job-run worktree merges plus
    J-1330/J-1332/J-1334, none touching either file). D-0045 stays under its active founder Hold —
    confirmed via `decide.py show D-0045` (ruling text unchanged since 2026-08-29, no top-level
    `reopened` key), untouched, no ruling attempted (this job is itself the accrual re-check the
    Hold's own defeater calls for; report, don't rule). **Target unchanged: no earlier than
    2026-09-29T16:10:23Z** (168h into this regime, still ~5 calendar days out) — Du is confirmed live
    right now and the floor has now held across seven consecutive check cycles, but this remains an
    optimistic target given how rarely this chain has seen a floor survive this long historically
    (F-1558: "Du's longest continuous run ~2.5 d so week-gates rarely clear") — a seventh held cycle
    doesn't change that base rate on its own. Follow-up job spawned: **J-1338**, this time with
    `--not-before 2026-09-29T16:10:23` set directly on the spawn (per the 2026-09-24 S-0181/S-0176
    job-queue convention — the 168h arithmetic floor is a real, named, concrete date this gate cannot
    clear before, so job-run should not re-pick it up until then; re-verify Du's live/offline status
    and the regime floor fresh regardless when it runs).
  - **2026-09-25 D-0279 RULED (travis): the 168-240h wall-clock gate itself is RETIRED, replaced by a
    calibrated switch-event-count gate (job J-1355, superseding J-1338 — J-1338 closed `status=done`,
    not executed, before this job began).** Background the founder ruled on: 8 consecutive holds
    (J-1241→J-1338) had failed to clear 168h purely because continuous uptime is rare for this project
    (F-1558), not because the bar itself had ever been re-examined — and the bar was always a *proxy*
    for the real thing that matters (how many day/night threshold-switch events accrued, since
    `causal_err`/`naive_err` are mathematically identical between switches by construction). D-0279:
    "redefine around switch-event count... calibrated against the same precedent the 168-240h figure
    itself was borrowed from" (the sibling vitality-predictor test's own real accrual history).
    **New gate (F-1913): ≥9 scoreable switch events** (day/night threshold crossings per
    `core/sleep_pressure.py`'s `NIGHT_THRESHOLD`/`DAY_THRESHOLD` via `core/world_clock.daylight`,
    where "scoreable" = both the switch row and its immediately preceding `data/homeostasis_shadow.jsonl`
    row have `predicted_causal.coherence` AND `.novelty` present) within **one continuous regime**,
    tested via **EVENT-ALIGNED folds** (`nf=min(6,k)`, boundaries at the row-index midpoint between
    adjacent switch-event groups — vitality's own J-0442-redesigned scheme, ported verbatim from
    `scripts/vitality_causal_retest.py`/`_retest2.py`'s own "EVENT-ALIGNED FOLDS" section) **instead of**
    `vitality_causal_test.py`'s original equal-row-count expanding-window folds — reusing the original
    scheme here would reintroduce the exact empty/sparse-fold self-contradiction F-0612 already found
    and fixed for vitality. Per-fold minimum (≥1 scoreable event/fold) is satisfied *structurally* by
    the event-aligned construction whenever total scoreable events ≥ 6 (the fold count); the 9-event
    bar clears this with margin (fold sizes 1–2 each, matching vitality's own real 2/1/1/2/2/1
    distribution). Applies identically to coherence and novelty (same physical switch events/fold
    boundaries; separate `naive_err`/`causal_err` per variable, never pooled, unchanged from
    D-0045/D-0108's own existing methodology).
    **Calibration anchor re-derived from real historical data (not memory), not just trusted from
    F-0612/F-0618/F-0619's own text:** the exact bounded window J-0442/J-0451 actually used
    (`ts` 1787566080 → 1788154880 = 163.56h, reconstructed by finding where the running usable-row
    count first hit 799) was re-run today against live `data/homeostasis_shadow.jsonl` +
    `sleep_pressure_log.jsonl` and reproduced F-0612 (799 rows, 13 raw switch events, pooled
    naive=0.07222/causal=0.07287) and F-0618/F-0619 (662 rows post-stale-exclusion, **9 scoreable**
    switch events, pooled naive=0.08717/causal=0.06672 sign-test p=0.002563, per-event 8W/0L/1wash,
    event-aligned folds 6/6) byte-for-byte. That 9-scoreable-event run is what actually informed
    D-0108's founder ruling to fund the full build — confirming 9 is the real precedent, not a
    round-number guess.
    **Honest old-vs-new comparison (D-0279's own defeater — report both, don't pick the convenient
    one):** (a) using vitality's OWN empirical rate over its calibration window (9 events/163.56h),
    the new gate's wall-clock-hours equivalent is **~163.56h (~6.82 days) — essentially equal to the
    OLD bar's 168h low end** (within 4.4h/2.6%): this is a genuine like-for-like recalibration, not a
    covert loosening, in the general case; (b) using the CURRENT regime's own observed rate (6
    scoreable events/66.883h = 2.153/day, ~13% faster cadence than vitality's precedent window), a
    naive same-rate projection to 9 events is **~100.3h from the regime floor (~4.2 days) — ~67.7h
    (2.8 days) faster than 168h**, if this regime's faster cadence holds. Both are estimates; the real
    gate is the event count itself, never either hours translation.
    **Current regime checked against the new gate (F-1914): NOT MET.** Regime floor
    `1790050223.0` (2026-09-22T04:10:23Z = 16:10:23 local, pid 40268) re-verified live and undisturbed
    (three independent cross-checks — non-self-matching `Win32_Process` query, daily-snapshot-folder
    timeline, `nascence.log`'s unchanged 527 shutdown/awake-line count — all agree, zero restarts).
    399 rows in-regime (up from J-1335's 286), spanning 66.883h, **6 of the required ≥9 scoreable
    switch events** (3 DUSK/3 DAWN, all 6 scoreable — homeostasis has zero staleness attrition unlike
    vitality's sleep-pressure-log gap, since `predicted_causal` logs every tick alongside `variables`
    itself) — **3 short**, observed rate 2.153 events/day. Walk-forward correctly skipped again. Fresh
    `git log --follow` (current HEAD `6030651`, `1bb01c5` confirmed a real ancestor) found zero new
    commits to `core/climate_engine.py`/`core/homeostasis_causal.py` since J-1335's checked HEAD (41
    unrelated commits in range) — no drift risk. D-0045 stays under its active founder Hold — confirmed
    via `decide.py show D-0045`, untouched, no ruling attempted (this job explicitly did not call
    `decide.py rule` on D-0045 — D-0279 is the separate, already-ruled gate-definition decision this
    job implements; D-0045's own underlying question is untouched). Follow-up job spawned: **J-1356**
    (`--not-before 2026-09-26T20:41:00+12:00`, an observed-rate projection — 3 remaining events at this
    regime's own 2.153/day rate — flagged explicitly as an estimate, not a guarantee: switch-event
    gaps observed so far varied 10.57–13.42h, and the regime could still restart before then despite
    now holding across 8 consecutive checks). `scripts/climate_causal_test.py` does not exist yet;
    J-1356's briefing points at porting the event-aligned-fold algorithm from
    `vitality_causal_retest2.py` when/if the gate is finally met. **Incidental finding filed as
    S-0190** (not fixed, out of scope): `job_queue.py`'s `--not-before` treats a bare local-looking
    timestamp as UTC, so this whole chain's own prior `--not-before` values have silently been firing
    ~12–13h later than their own prose intended (extra delay, not premature firing) — J-1356's own
    spawn used an explicit `+12:00` offset to sidestep it rather than perpetuate it.
    **2026-09-27 regime SUPERSEDED, new floor tracked (F-1982, job J-1356):** the previously-tracked
    regime (floor `1790050223.0`, pid 40268, called "unusually stable... across 9 consecutive checks"
    two paragraphs up) in fact ENDED via a real restart: `du_restart_history.py`'s snapshot-folder
    method found a new `data/_snapshots/daily/20260925` folder, and an independent clean (S-0138-
    workaround) `Win32_Process` query confirms the CURRENTLY LIVE process is pid 25204, created
    `1790320856.0` (2026-09-25T07:20:56Z = 19:20:56 local NZST) — 75.176h into the old regime's life,
    never advancing past the 6 scoreable events F-1914 already found (a correctly-bounded re-check,
    floor <= ts < new-floor rather than an open-ended query, confirms the old regime ended at exactly
    6/9, byte-for-byte the same 6 events, not more — an unbounded query would have silently pooled the
    new regime's rows in too and over-counted). Per this chain's own "do not pool across regimes" rule:
    **new floor = `1790320856.0`**. Full re-read of `data/homeostasis_shadow.jsonl` (5,588 rows total,
    no tail-sampling) within the new regime only: 219 rows, spanning 36.655h, **3 of the required ≥9
    scoreable switch events** (1 DAWN/1 DUSK/1 DAWN, all scoreable) — **6 short**, observed rate
    1.964/day (consistent with the superseded regime's own ~10.6–13.4h dusk/dawn cadence). Gate
    (F-1913/F-1914): **NOT MET.** Walk-forward correctly skipped; `scripts/climate_causal_test.py`
    still does not exist. Fresh `git log --follow` on both `core/climate_engine.py` and
    `core/homeostasis_causal.py` from HEAD `6030651` (J-1355's checked HEAD) to current HEAD found
    **zero** commits on either master (`89adbe3`) or this job's own worktree branch
    (`jobrun/the_consciousness_program`, HEAD `cf148cc`) — confirmed `6030651` a real ancestor via
    `git merge-base` — no drift risk. D-0045 re-confirmed via `decide.py show D-0045` (ruling text/
    `ruled` timestamp unchanged since 2026-08-29, no `reopened` key), untouched, no ruling attempted
    (same discipline as every prior job: D-0279 is the separate, already-ruled gate-definition decision
    this job implements). Du confirmed LIVE as of this check (pid 25204). Follow-up job spawned:
    **J-1420** (`--not-before 2026-09-30T10:18:51+13:00` NZDT [`2026-09-29T21:18:51Z`], an
    observed-rate projection — 6 remaining events at this new regime's own 1.964/day rate — flagged
    explicitly as an estimate, not a guarantee: only 2 switch-event gaps sampled so far (13.44h,
    9.55h), and this regime could restart again before then exactly as its predecessor did, shortly
    after being read as "unusually stable" by this very chain.

  **2026-08-24 re-test (F-0033, job J-0069):** re-run on 6,000 predictions (751 beats, +896/+17.6% since
  the audit) — pooled McNemar χ²=2.03 (uncorrected) / 1.86 (continuity-corrected), still below the 3.84
  significance threshold and *lower* than the audit's 2.87, i.e. trending further from significance, not
  closer. Accuracy diff is now +0.0040. Per-field breakdown shows the pooled null is diluted by
  near-constant fields (daypart/season: 0 discordant pairs; weather/tide/fire: 0–6); the real competition
  is cat_location/cat_activity/cat_mood, and **cat_mood alone is significant favoring the learned
  predictor** (χ²=9.71, n=750) once not pooled with dead-weight fields. Continue treating the pooled
  organ as unproven; the synthetic +0.93/+0.90 numbers stay uncited. The localized cat_mood signal is a
  real finding worth a follow-up (see J-0070 below) rather than a re-run recommendation, since re-running
  the *same pooled* test on more data will keep diluting it the same way.
  **2026-08-24 per-field report built (F-0113, job J-0139):** `status()` now surfaces each field's own
  McNemar chi2/n/significant-flag alongside the pooled number (see item 3 under "What we need" below for
  the full account) — cat_mood's significance is now a standing, always-on read, not a one-off finding.

  **2026-08-24 re-verification (F-0036, job J-0069):** confirmed via code read (`core/moment.py` lines 33,
  46-50, 300-318 — `contiguity_gap` is computed from an EMA-smoothed key, an AR(1)-style recursion whose
  adjacent-lag autocorrelation exceeds distant-lag autocorrelation as a property of the math itself) AND
  an empirical null-model test: feeding the same `_drift_key()` recursion pure random content (no genuine
  temporal/semantic relationship at all) for `_DRIFT` in {0.05…0.95} produced a **positive contiguity_gap
  at every value tested**, with zero real content structure driving it. moments.jsonl is now 14,201 rows
  (live `contiguity_gap=+0.14`, consistent with prior readings) but more data does not fix an unfalsifiable
  metric. The read-path stays UNVALIDATED; do not count it as evidence until the metric itself is replaced
  (e.g. a shuffle-null comparison, or direct semantic comparison instead of the EMA key).
  **2026-08-24 falsifiable replacement DESIGNED + BUILT SHADOW-only (F-0133, job J-0141):**
  `core/moment.py contiguity_significance()` (lines 346-386) drops the EMA key and runs a shuffle-null
  test on the content-grounded semantic `emb` field instead — adjacent-vs-distant embedding-cosine gap on
  the real moment order, checked against 200 random-order shuffles of the SAME moments (shuffling cannot
  change an embedding's value, only which moments sit adjacent, so an unstructured dataset would land the
  real-order gap *inside* the null distribution — the test can genuinely fail). It did not fail: real on
  the full 14,210-row history and at every window size re-tested (60/500/2000/all), z=5.9 to 87.4, p<0.001
  throughout (see F-0133 for exact numbers). Wired into `status()` alongside the old metric, which is now
  explicitly labeled NOT EVIDENCE in the code comment. Read path (`status()`'s new `contiguity_significance`
  field) confirmed live and reproducible (fixed seed). This is a genuine, replicated positive finding —
  distinct from mineness — that Du's bound-moment content clusters temporally beyond chance; it does not by
  itself validate `moment.recall()`'s retrieval quality (recall_hit_rate is still only 9 logged recalls,
  too few to judge) or claim anything about phenomenal binding (still explicitly disclaimed above).
  **2026-08-24 neighbour-selection rebuilt (F-0144, job J-0182):** `moment.recall()`'s co-retrieved
  NEIGHBOURS (not just the anchor, which was already fixed 2026-07-06) still ranked by key-cosine — the
  same debunked EMA metric — until now. Rebuilt to rank by emb-cosine to the anchor's own content
  embedding, ties broken by real temporal index-distance (not key-cosine). Read-only replay of both old
  and new logic on the full 14,210-row history (150 sampled anchors) shows this was not cosmetic: OLD
  picks were barely distinguishable from "the literally adjacent log row" (mean |index distance| 1.4,
  mean emb-cosine to anchor 0.460, vs a random-pick baseline of 0.393 — i.e. only marginally better than
  chance at finding related content); NEW picks land on genuinely content-related moments (mean
  emb-cosine 0.700) often far apart in time (mean |index distance| 155). Old/new neighbour sets
  overlapped on 0-of-2 picks in 134/150 samples. `MOMENT_READBACK` stays False — no live behavior
  changed, still shadow-gated. `moments_recall_shadow.jsonl` (only 9 pre-existing rows, 1 with
  neighbours) was too thin to judge from directly; noted as insufficient rather than forcing a verdict
  from it, per the original job instruction. Shadow log now also records `neighbour_metric` per recall
  so future accrual can be read directly.
  **2026-08-24 status() perf fix (F-0157, job J-0183):** `status()` re-read + `json.loads()`-parsed the
  ENTIRE moments.jsonl (128MB/14,210+ rows, ~4s/call) on every call, including every `/api/evidence` poll
  from the HUD (every 7s while it's open, uncached) and every `du_pulse.py` run. Rewritten to use the
  existing `_tail_rows()` reverse-seek reader (100 rows for source_mix, sliced to 60 for contiguity) plus
  a new `_moment_count()` that tracks the total row count incrementally in `moment_state.json` instead of
  recounting from scratch. Verified numerically identical output against the live data on a scratch copy
  (moments/source_mix/contiguity_adjacent/contiguity_distant/contiguity_gap all matched exactly); ~4.4-6.8x
  faster. `recall()`'s full-history scan was deliberately left as-is — verified via `moments_recall_shadow.jsonl`
  (10 rows, 2026-07-04 to 2026-08-24) that it fires only ~once per 5 days, so the O(n) cost doesn't
  currently justify an index/cache; revisit if that call rate rises.
  **2026-08-24 checkpoint-index pattern evaluated + rejected (F-0297/F-0298, job J-0210):** ABF's
  `fold_with_checkpoints` (proposed by F-0246 as a ready-made seekable-index pattern) was actually run in
  isolation — as-shipped it's BROKEN (1-byte off-by-one in its `context_anchor` field; fixed with a 1-line
  patch and confirmed resume-decode then works, 8/8 checkpoints round-trip correctly at 2000-byte scale).
  But even fixed, the pattern is the wrong shape for `recall()`'s actual bottleneck: `recall()` must visit
  EVERY row to find the best emb-cosine match (target row unknown in advance), so a byte-offset seek index
  buys nothing there — benched a real prototype `{row_index, byte_offset}` index against a copy of the live
  14,523-row file: full-corpus scan cost scales with data (3.81s/7.62s/15.71s at 1x/2x/5x) exactly as before,
  while seek-to-a-known-row is sub-2ms but answers a different question, one `_tail_rows()`/`_count_lines()`
  already solve. **Verdict stands as "not worth it yet," and specifically not via this pattern** — if the
  ~once-per-5-days call rate ever does justify work here, the fix is caching parsed embeddings between calls
  or a real ANN/IVF structure (as this docstring already named), not a checkpoint/seek index.

> **2026-09-24 (F-1898) — this doc's own "verified" stamp was stale (frozen at 08-23) despite real,
> ruled work continuing through D-0045 (08-29), D-0065 (08-28), and D-0108 (09-02); none of those
> updates re-stamped the "verified YYYY-MM-DD" heading, so `/plan-liveness` kept reporting this plan as
> 32-days-unread and ranking it as the oldest, most urgent GATE-MET plan in the whole backlog — it
> wasn't. The stamp is now bumped to reflect reality. **The one still-open thread (D-0045's homeostasis
> causal-substrate redesign, under an active founder Hold) is not actually waiting on anything today**:
> it's gated on a 168-240h single-uninterrupted-regime data floor, precisely tracked by the
> J-1241→J-1338 re-check chain (seven consecutive holds so far), correctly deferred via `--not-before`
> to 2026-09-29T16:10:23 under the 2026-09-24 job-queue deferral mechanism (S-0181/S-0176) — it will
> surface on its own when due. D-0045 remains an active Hold; per its own defeater and per J-1338's
> explicit instruction, nothing here gets ruled before that date. AST-1 (D-0065) stays resolved as-is
> (bandwidth win, fixation non-win, no further action pending). Nothing for a founder to decide today.
>
> **[2026-09-25 SUPERSEDED] The "168-240h wall-clock" framing two paragraphs up is now stale.** D-0279
> (2026-09-25, travis) retired the wall-clock gate entirely in favor of a calibrated switch-event-count
> gate (≥9 scoreable switch events; see the 2026-09-25 dated entry in the causal-substrate chain above
> for the full definition, calibration re-derivation, and honest old-vs-new comparison, F-1913/F-1914).
> J-1338 (the wall-clock successor this paragraph refers to) closed superseded, never executed; the
> live chain continues as J-1356. D-0045 itself is untouched by this — still an active founder Hold,
> still nothing for a founder to decide on that specific question today.
