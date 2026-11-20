# Lane 2 Recheck — founder-check re-run of K1/K3 (2026-08-18)

> Re-runs the two triggered kill criteria from `docs/lab/lane2_lab_report.md` (2026-08-17)
> against the CURRENT `core/object_graph.py` output (`data/lane2/graph.json`), which postdates
> the report's own fixes (voiceprint filter) and the data-gap window the original K3 fell into.
> Same pre-registered methodology, same seed (20260817). Zero LLM. Read-only. Spec:
> `docs/completed/lane2_lab.md`.

**Graph checked:** built 0.56 day(s) ago, 218 referents, day0=2026-05-30, max_day=80.

## Verdicts

| Criterion | Original (2026-08-17) | Recheck (2026-08-18) |
|---|---|---|
| K1 (glass float) | TRIGGERED (did not emerge) | RESOLVED — not triggered |
| K3 (temporal holdout) | TRIGGERED (real ≥ shuffled) | still TRIGGERED |

- **K1 (glass float absent, corrected criterion)**: not triggered
- **K3 (holdout no better than shuffled)**: TRIGGERED

## L3 detail — corrected criterion

corrected criterion: >=20 observations AND recurring (low days_silent or a 'still here' trend shape) — replaces the original terminal+world-absent test, which the lab report's own diagnosis named as the wrong premise.

- `shore_sea_glass_5e60b2`: {"kind": "item", "total_mentions": 0, "seen": 0, "kept": 0, "trend_shape": "insufficient", "days_silent": null, "last_mention_day": null, "float_like": false, "in_world_substrate": true}
- `sea_glass`: {"kind": "item_class", "total_mentions": 182, "seen": 16, "kept": 0, "trend_shape": "episodic", "days_silent": 0.02, "last_mention_day": 79, "float_like": false, "in_world_substrate": true}
- `glass`: {"kind": "item_class", "total_mentions": 1637, "seen": 58, "kept": 1, "trend_shape": "settled_companion", "days_silent": 0.02, "last_mention_day": 79, "float_like": true, "in_world_substrate": true}
- `book:Astronomy with an Opera-glass A Popular Introduction to the`: {"kind": "book", "total_mentions": 447, "seen": 3, "kept": 0, "trend_shape": "settled_companion", "days_silent": 3.02, "last_mention_day": 76, "float_like": false, "in_world_substrate": false}

## L7 detail — temporal holdout

- 117 eligible referents (>= 30 total mentions)
- split day 64 / 80 (80% train)
- median holdout gap: real=6.1176, shuffled=1.7689
- top real gaps (worst-predicted referents):
  - `study`: gap 131.471
  - `small_birds`: gap 109.765
  - `tide_pool_trickle`: gap 94.353
  - `wind_in_eaves`: gap 58.941
  - `wind_in_trees`: gap 58.941
  - `door`: gap 56.353
  - `fire`: gap 56.059
  - `glass`: gap 53.176
  - `shingle_drag`: gap 52.706
  - `wood`: gap 52.059

## Reading this result

**Mixed result** — one criterion resolved, one didn't. Read both details above before
deciding; this is not a clean go/no-go and deserves a direct founder read rather than an
automatic verdict.

*Recheck runtime: 0.2s. Raw data: `data/lab/lane2_recheck/recheck.json`.*
---

## ★ K3 RETIRED — VERDICT REVISED TO `INCONCLUSIVE` (2026-08-20, founder-approved)

K3's recorded FAIL (6.12 vs 1.77) is struck. Three defects, each independently fatal
(full derivation: docs/reviews/audit_2026-08-20.md):
1. **Empty training window.** The predictor's last-14-train-day window fell entirely inside the
   30-day outage (days 40–69, zero fragments) — it predicted 0 for everything; "6.12" was merely the
   test-period base rate. A precondition failure was reported as a substantive failure.
2. **Degenerate null.** Full-span shuffling forces train-mean ≈ test-mean, handing the null the test
   level for free on any non-stationary series — it measured sampling noise, not temporal structure.
   (Autocorrelation-preserving circular shift gave 2.47, not 1.77 — and even that null inflates
   Type-I error on trending series.)
3. **The surrogate never went through the pipeline.** The real arm was a starved model; the null arm
   was an oracle. Theiler's rule: surrogate the DATA, then run the identical code path on it.
Also a category error on the record: the "substrate genuinely thin (37 entries / 19 objects)"
diagnosis described `world_objects.json`, which K3 never touches — K3 runs on the mention-graph
(117 referents over 46k+ fragments).

An invalid test's verdict is not evidence in either direction. K3 is retired, not failed.

## ★★ K3b — FRESH REGISTRATION (pre-registered 2026-08-20, BEFORE any run)

**Question (unchanged):** does the World Ledger's mention history contain real temporal structure —
does predicting a referent's near-future mention rate from its own real history beat predicting it
from structure-destroyed history?

**Fixed in advance — no element below may change after the first real run:**
- **day0 = 2026-08-08** (post-outage; clean single-era data only). No data before day0 enters
  train, test, or surrogate.
- **Windows in OBSERVATIONS, never calendar days.** Train = the referent's first 80% of
  observations; test = the remaining 20%. (The calendar-day window is what walked into the hole.)
- **Null: stationary block bootstrap** (geometric block lengths; mean block = the lag at which the
  pooled sample ACF first crosses zero, computed on train only and REPORTED in the log line),
  **B = 999**, and — the Theiler rule — **each surrogate is refit and scored through the identical
  pipeline** as the real arm. p = (1 + #{surrogate_gap ≤ real_gap}) / (B + 1).
- **Score: MASE** (MAE / in-sample naive MAE) so level shifts cannot dominate.
- **Margin (SESOI):** PASS requires p ≤ 0.05 AND real MASE ≥ 10% better than the surrogate median.
  Direction-only wins do not pass.
- **Folds:** rolling-origin, ≥ 3 folds as data allows; the verdict is per-fold, and the criterion's
  overall PASS requires ≥ 2 folds passing with 0 folds failing preconditions silently.
- **Preconditions (checked FIRST; any failure → `INCONCLUSIVE`, never FAIL):**
  n_train ≥ 200 observations pooled · ≥ 30 test-window events pooled · per-referent minimum 12
  train observations (referents below it are excluded and COUNTED, not silently dropped) ·
  gap_fraction in the fold < 0.20.
- **Controls before the first real run (the executed-failing-run rule):**
  (a) POSITIVE: synthetic series with planted autocorrelation must PASS;
  (b) NEGATIVE: the same pipeline on white-noise series must return FAIL/INCONCLUSIVE, never PASS.
  Both control runs are checked in beside the first real result. No controls, no verdict.
- **Kill date:** if by **2026-10-01** K3b has not PASSED, the World Ledger stays produce-only
  (no LLM-prediction layer, no live consumer) and the question is closed for this design — not
  extended with "just needs more data."
- **Verdicts are three-valued** (PASS / FAIL / INCONCLUSIVE) and every evaluation logs its
  preconditions, block length, fold boundaries, and n's.

*Registered by Claude on founder instruction ("register fresh"), 2026-08-20. The harness change to
`scripts/lane2_lab.py` implements this spec verbatim; any deviation discovered between spec and
implementation invalidates the run, not the spec.*
