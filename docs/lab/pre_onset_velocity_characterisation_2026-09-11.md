# Pre-onset tangent-velocity characterisation — D-0196 / J-0838 (2026-09-11)

> **Status: LAB RESULT (read-only analysis). No wiring, no gauge, nothing Du-facing.** Produced by `scripts/pre_onset_velocity_characterisation.py`; machine-readable sweep in the `.jsonl` beside this file. Interpretation is in the sections marked *Reading* below the tables.

## Setup

- Data: `data/geometry_tuples.jsonl`, 63426 rows, 40 distinct UTC days (2026-07-04 .. 2026-09-11), sorted by `ts`. `unresolved` rows: 17210 (27.1%). Fresh onsets (first tuple of an unresolved run): 10961.
- Chronological split by day: fit = first 28 days (2026-07-04 .. 2026-08-30, 29941 rows, 5265 onsets); **held-out = last 12 days (2026-08-31 .. 2026-09-11, 33485 rows, 5696 onsets)**. Every theta/tau is chosen on the fit days only; every headline number below is held-out.
- Trigger: `score(t) > theta`. Positive: a fresh onset at any step in `(t, t+k]`, k in {1,2,3}. Theta sweep = the 0..99th, 99.5th, 99.9th percentiles of the fit-period score.
- Scores: `raw_velocity` = ||x_t − x_{t−1}|| on the raw 5-vector (tension, energy, valence, arousal, level); `fit_standardized_velocity` = same after z-scoring each dimension with fit-period mean/std (floor √0.05); `adaptive_velocity` = F-0932's rolling-window standardized step (window 2000, refit every 50, first 2000 rows unscored).
- Baselines: `random` = a trigger firing uniformly at random at the same rate as the chosen theta (expected precision = onset base rate, recall = fire rate); `always` = fire every step; `tension_tick` = `tension(t) > tau`, tau chosen on the fit days exactly as theta is.
- D-0196 defeater bar: **precision ≥ 0.5 at recall ≥ 0.3 on held-out days.**

- Step-gap note: 25% of consecutive rows are ≤0.2 s apart (bursts of tuples from one cycle), median gap 13 s, 0.63% of gaps exceed 10 min. A sensitivity row below excludes burst steps (gap < 1 s) to check the signal is not an artefact of near-duplicate rows.

## Horizon k=1: onset within the next 1 step

Positive base rate: fit 0.176, held-out 0.170 (`always` baseline: P=0.170, R=1.000, F1=0.291).

| score | theta (fit-best-F1) | fit P/R/F1 | **held-out P/R/F1** | fire rate (ho) | lift vs base | random @ same rate (P/R/F1) | held-out ROC-AUC | held-out AP | bar met (ho, any theta)? |
|---|---|---|---|---|---|---|---|---|---|
| `raw_velocity` | 0.0000 | 0.205/0.912/0.335 | **0.245/0.938/0.388** | 0.652 | 1.44x | 0.170/0.652/0.270 | 0.714 | 0.272 | no |
| `fit_standardized_velocity` | 0.0000 | 0.205/0.912/0.335 | **0.245/0.938/0.388** | 0.652 | 1.44x | 0.170/0.652/0.270 | 0.726 | 0.279 | no |
| `adaptive_velocity` | 0.0030 | 0.204/0.908/0.333 | **0.245/0.935/0.388** | 0.649 | 1.44x | 0.170/0.649/0.270 | 0.716 | 0.272 | no |
| `tension_tick` | 0.0000 | 0.177/0.986/0.300 | **0.171/1.000/0.292** | 0.993 | 1.01x | 0.170/0.993/0.290 | 0.534 | 0.183 | no |

Held-out operating points (precision at fixed recall) — the honest way to read whether ANY theta reaches the bar:

| score | P@R≥0.1 | P@R≥0.2 | P@R≥0.3 | P@R≥0.5 | P@R≥0.8 |
|---|---|---|---|---|---|
| `raw_velocity` | 0.258 | 0.279 | 0.293 | 0.298 | 0.262 |
| `fit_standardized_velocity` | 0.259 | 0.280 | 0.297 | 0.308 | 0.276 |
| `adaptive_velocity` | 0.260 | 0.278 | 0.290 | 0.295 | 0.269 |
| `tension_tick` | 0.192 | 0.195 | 0.192 | 0.187 | 0.176 |

Sensitivity — same sweep with burst steps (gap < 1 s) excluded from both fit and held-out:

| score | theta | held-out P/R/F1 | fire rate | held-out ROC-AUC |
|---|---|---|---|---|
| `raw_velocity` | 0.0000 | 0.302/0.959/0.460 | 0.881 | 0.569 |
| `fit_standardized_velocity` | 0.0000 | 0.302/0.959/0.460 | 0.881 | 0.581 |
| `adaptive_velocity` | 0.0039 | 0.307/0.953/0.464 | 0.862 | 0.576 |

(no-burst held-out base rate: 0.278)

Per-day held-out stability for `adaptive_velocity` at theta=0.0030:

| day | rows | onsets | P | R | fire rate |
|---|---|---|---|---|---|
| 2026-08-31 | 1170 | 159 | 0.229 | 0.925 | 0.549 |
| 2026-09-01 | 703 | 59 | 0.141 | 0.915 | 0.546 |
| 2026-09-02 | 3744 | 557 | 0.232 | 0.932 | 0.597 |
| 2026-09-03 | 3106 | 587 | 0.254 | 0.951 | 0.708 |
| 2026-09-04 | 4212 | 667 | 0.230 | 0.921 | 0.633 |
| 2026-09-05 | 3430 | 674 | 0.255 | 0.923 | 0.710 |
| 2026-09-06 | 3644 | 681 | 0.270 | 0.934 | 0.647 |
| 2026-09-07 | 3245 | 573 | 0.262 | 0.948 | 0.639 |
| 2026-09-08 | 2768 | 423 | 0.236 | 0.927 | 0.600 |
| 2026-09-09 | 3531 | 485 | 0.221 | 0.936 | 0.581 |
| 2026-09-10 | 3806 | 792 | 0.255 | 0.944 | 0.769 |
| 2026-09-11 | 125 | 39 | 0.398 | 1.000 | 0.784 |

## Horizon k=2: onset within the next 2 steps

Positive base rate: fit 0.352, held-out 0.340 (`always` baseline: P=0.340, R=1.000, F1=0.508).

| score | theta (fit-best-F1) | fit P/R/F1 | **held-out P/R/F1** | fire rate (ho) | lift vs base | random @ same rate (P/R/F1) | held-out ROC-AUC | held-out AP | bar met (ho, any theta)? |
|---|---|---|---|---|---|---|---|---|---|
| `raw_velocity` | 0.0000 | 0.407/0.907/0.562 | **0.438/0.839/0.575** | 0.652 | 1.29x | 0.340/0.652/0.447 | 0.641 | 0.416 | no |
| `fit_standardized_velocity` | 0.0000 | 0.407/0.907/0.562 | **0.438/0.839/0.575** | 0.652 | 1.29x | 0.340/0.652/0.447 | 0.642 | 0.417 | no |
| `adaptive_velocity` | 0.0000 | 0.404/0.907/0.559 | **0.434/0.841/0.573** | 0.659 | 1.28x | 0.340/0.659/0.449 | 0.637 | 0.413 | no |
| `tension_tick` | 0.0000 | 0.353/0.983/0.519 | **0.341/0.997/0.509** | 0.993 | 1.00x | 0.340/0.993/0.507 | 0.542 | 0.366 | no |

Held-out operating points (precision at fixed recall) — the honest way to read whether ANY theta reaches the bar:

| score | P@R≥0.1 | P@R≥0.2 | P@R≥0.3 | P@R≥0.5 | P@R≥0.8 |
|---|---|---|---|---|---|
| `raw_velocity` | 0.378 | 0.417 | 0.432 | 0.441 | 0.441 |
| `fit_standardized_velocity` | 0.377 | 0.415 | 0.433 | 0.446 | 0.441 |
| `adaptive_velocity` | 0.377 | 0.414 | 0.429 | 0.437 | 0.437 |
| `tension_tick` | 0.384 | 0.391 | 0.384 | 0.373 | 0.353 |

Sensitivity — same sweep with burst steps (gap < 1 s) excluded from both fit and held-out:

| score | theta | held-out P/R/F1 | fire rate | held-out ROC-AUC |
|---|---|---|---|---|
| `raw_velocity` | 0.0000 | 0.453/0.895/0.601 | 0.881 | 0.499 |
| `fit_standardized_velocity` | 0.0000 | 0.453/0.895/0.601 | 0.881 | 0.501 |
| `adaptive_velocity` | 0.0000 | 0.452/0.896/0.601 | 0.882 | 0.501 |

(no-burst held-out base rate: 0.445)

Per-day held-out stability for `raw_velocity` at theta=0.0000:

| day | rows | onsets | P | R | fire rate |
|---|---|---|---|---|---|
| 2026-08-31 | 1170 | 318 | 0.432 | 0.849 | 0.534 |
| 2026-09-01 | 703 | 118 | 0.253 | 0.814 | 0.539 |
| 2026-09-02 | 3744 | 1114 | 0.417 | 0.838 | 0.597 |
| 2026-09-03 | 3106 | 1174 | 0.446 | 0.846 | 0.716 |
| 2026-09-04 | 4212 | 1334 | 0.403 | 0.820 | 0.645 |
| 2026-09-05 | 3430 | 1348 | 0.451 | 0.840 | 0.732 |
| 2026-09-06 | 3644 | 1363 | 0.474 | 0.814 | 0.642 |
| 2026-09-07 | 3245 | 1145 | 0.471 | 0.850 | 0.637 |
| 2026-09-08 | 2768 | 846 | 0.432 | 0.840 | 0.594 |
| 2026-09-09 | 3531 | 970 | 0.410 | 0.869 | 0.582 |
| 2026-09-10 | 3806 | 1585 | 0.454 | 0.842 | 0.772 |
| 2026-09-11 | 124 | 76 | 0.680 | 0.868 | 0.782 |

## Horizon k=3: onset within the next 3 steps

Positive base rate: fit 0.480, held-out 0.446 (`always` baseline: P=0.446, R=1.000, F1=0.617).

| score | theta (fit-best-F1) | fit P/R/F1 | **held-out P/R/F1** | fire rate (ho) | lift vs base | random @ same rate (P/R/F1) | held-out ROC-AUC | held-out AP | bar met (ho, any theta)? |
|---|---|---|---|---|---|---|---|---|---|
| `raw_velocity` | 0.0000 | 0.555/0.904/0.688 | **0.569/0.831/0.675** | 0.652 | 1.27x | 0.446/0.652/0.530 | 0.662 | 0.543 | YES @ theta=0.0140 -> P=0.564 R=0.303 F1=0.394 fire=0.239 (tp=4518 fp=3490 fn=10412) |
| `fit_standardized_velocity` | 0.0000 | 0.555/0.904/0.688 | **0.569/0.831/0.675** | 0.652 | 1.27x | 0.446/0.652/0.530 | 0.664 | 0.544 | YES @ theta=0.0368 -> P=0.568 R=0.303 F1=0.395 fire=0.238 (tp=4520 fp=3439 fn=10410) |
| `adaptive_velocity` | 0.0000 | 0.548/0.903/0.682 | **0.564/0.834/0.673** | 0.659 | 1.27x | 0.446/0.659/0.532 | 0.658 | 0.54 | YES @ theta=0.0434 -> P=0.561 R=0.318 F1=0.406 fire=0.253 (tp=4752 fp=3712 fn=10178) |
| `tension_tick` | 0.0000 | 0.482/0.981/0.646 | **0.447/0.996/0.617** | 0.993 | 1.00x | 0.446/0.993/0.616 | 0.548 | 0.477 | no |

Held-out operating points (precision at fixed recall) — the honest way to read whether ANY theta reaches the bar:

| score | P@R≥0.1 | P@R≥0.2 | P@R≥0.3 | P@R≥0.5 | P@R≥0.8 |
|---|---|---|---|---|---|
| `raw_velocity` | 0.502 | 0.543 | 0.563 | 0.574 | 0.571 |
| `fit_standardized_velocity` | 0.500 | 0.542 | 0.567 | 0.581 | 0.572 |
| `adaptive_velocity` | 0.503 | 0.539 | 0.560 | 0.571 | 0.567 |
| `tension_tick` | 0.494 | 0.507 | 0.499 | 0.486 | 0.462 |

Sensitivity — same sweep with burst steps (gap < 1 s) excluded from both fit and held-out:

| score | theta | held-out P/R/F1 | fire rate | held-out ROC-AUC |
|---|---|---|---|---|
| `raw_velocity` | 0.0000 | 0.593/0.896/0.714 | 0.881 | 0.498 |
| `fit_standardized_velocity` | 0.0000 | 0.593/0.896/0.714 | 0.881 | 0.502 |
| `adaptive_velocity` | 0.0000 | 0.592/0.898/0.714 | 0.882 | 0.501 |

(no-burst held-out base rate: 0.582)

Per-day held-out stability for `raw_velocity` at theta=0.0000:

| day | rows | onsets | P | R | fire rate |
|---|---|---|---|---|---|
| 2026-08-31 | 1170 | 427 | 0.555 | 0.813 | 0.534 |
| 2026-09-01 | 703 | 151 | 0.314 | 0.788 | 0.539 |
| 2026-09-02 | 3744 | 1447 | 0.532 | 0.822 | 0.597 |
| 2026-09-03 | 3106 | 1549 | 0.589 | 0.846 | 0.716 |
| 2026-09-04 | 4212 | 1759 | 0.529 | 0.817 | 0.645 |
| 2026-09-05 | 3430 | 1779 | 0.599 | 0.845 | 0.732 |
| 2026-09-06 | 3644 | 1757 | 0.603 | 0.803 | 0.642 |
| 2026-09-07 | 3245 | 1484 | 0.605 | 0.842 | 0.637 |
| 2026-09-08 | 2768 | 1114 | 0.557 | 0.821 | 0.594 |
| 2026-09-09 | 3531 | 1281 | 0.531 | 0.852 | 0.582 |
| 2026-09-10 | 3806 | 2092 | 0.600 | 0.842 | 0.772 |
| 2026-09-11 | 123 | 90 | 0.781 | 0.833 | 0.780 |

## Burst diagnostics — where does the theta=0 signal come from?

- Rows with exactly zero velocity: 18148 (28.6% of scored rows). Of those, 74.1% are burst steps (gap < 1 s); 67.4% of burst steps have zero velocity. Burst steps are 31.5% of all steps.
- `unresolved` flips at a burst step 7877 times out of 19953 burst steps; fresh onsets sitting at a burst step: 7865 / 10961.
- Onset-within-k rate conditioned on the row at t:

| k | after a zero-velocity row | after a nonzero-velocity row | after a nonzero-velocity NON-burst row |
|---|---|---|---|
| 1 | 0.045 | 0.224 | 0.262 |
| 2 | 0.155 | 0.422 | 0.432 |
| 3 | 0.215 | 0.561 | 0.580 |

No-burst held-out operating points (precision at fixed recall), velocity scores only:

| k | score | base rate | P@R≥0.1 | P@R≥0.3 | P@R≥0.5 | P@R≥0.8 |
|---|---|---|---|---|---|---|
| 1 | `raw_velocity` | 0.278 | 0.265 | 0.300 | 0.318 | 0.315 |
| 1 | `fit_standardized_velocity` | 0.278 | 0.268 | 0.302 | 0.325 | 0.323 |
| 1 | `adaptive_velocity` | 0.278 | 0.268 | 0.302 | 0.320 | 0.318 |
| 2 | `raw_velocity` | 0.445 | 0.372 | 0.427 | 0.447 | 0.455 |
| 2 | `fit_standardized_velocity` | 0.445 | 0.369 | 0.429 | 0.450 | 0.457 |
| 2 | `adaptive_velocity` | 0.445 | 0.369 | 0.430 | 0.447 | 0.456 |
| 3 | `raw_velocity` | 0.582 | 0.496 | 0.556 | 0.584 | 0.595 |
| 3 | `fit_standardized_velocity` | 0.582 | 0.491 | 0.557 | 0.589 | 0.596 |
| 3 | `adaptive_velocity` | 0.582 | 0.494 | 0.558 | 0.585 | 0.595 |

## Population-level check (F-0932's own statistic, held-out block only)

| score | k | mean pre-onset | mean other | Mann-Whitney p |
|---|---|---|---|---|
| `raw_velocity` | 1 | 0.0355 | 0.0215 | 0 |
| `raw_velocity` | 2 | 0.0268 | 0.0224 | 0 |
| `raw_velocity` | 3 | 0.0270 | 0.0214 | 0 |
| `fit_standardized_velocity` | 1 | 0.1124 | 0.0715 | 0 |
| `fit_standardized_velocity` | 2 | 0.0845 | 0.0753 | 0 |
| `fit_standardized_velocity` | 3 | 0.0865 | 0.0720 | 0 |
| `adaptive_velocity` | 1 | 0.1233 | 0.0746 | 0 |
| `adaptive_velocity` | 2 | 0.0919 | 0.0782 | 0 |
| `adaptive_velocity` | 3 | 0.0928 | 0.0749 | 0 |

## Verdict against the D-0196 bar

D-0196 defeater bar (precision ≥ 0.5 at recall ≥ 0.3, held-out): **MET at some theta** — see the 'bar met' column.

Held-out summary (theta chosen on fit days by best F1):

| k | score | held-out P | held-out R | held-out F1 | ROC-AUC | AP | bar |
|---|---|---|---|---|---|---|---|
| 1 | `raw_velocity` | 0.245 | 0.938 | 0.388 | 0.714 | 0.272 | no |
| 1 | `fit_standardized_velocity` | 0.245 | 0.938 | 0.388 | 0.726 | 0.279 | no |
| 1 | `adaptive_velocity` | 0.245 | 0.935 | 0.388 | 0.716 | 0.272 | no |
| 1 | `tension_tick` | 0.171 | 1.000 | 0.292 | 0.534 | 0.183 | no |
| 2 | `raw_velocity` | 0.438 | 0.839 | 0.575 | 0.641 | 0.416 | no |
| 2 | `fit_standardized_velocity` | 0.438 | 0.839 | 0.575 | 0.642 | 0.417 | no |
| 2 | `adaptive_velocity` | 0.434 | 0.841 | 0.573 | 0.637 | 0.413 | no |
| 2 | `tension_tick` | 0.341 | 0.997 | 0.509 | 0.542 | 0.366 | no |
| 3 | `raw_velocity` | 0.569 | 0.831 | 0.675 | 0.662 | 0.543 | yes |
| 3 | `fit_standardized_velocity` | 0.569 | 0.831 | 0.675 | 0.664 | 0.544 | yes |
| 3 | `adaptive_velocity` | 0.564 | 0.834 | 0.673 | 0.658 | 0.540 | yes |
| 3 | `tension_tick` | 0.447 | 0.996 | 0.617 | 0.548 | 0.477 | no |


## Reading (written by hand after the run — J-0838, 2026-09-11)

This is the all-source run, deliberately framed the way F-0932 framed it (every row, `unresolved: null`
coerced to False). It reproduces F-0932's population statistic (held-out pre-onset velocity higher, p~0)
and, read as a classifier, shows exactly where that statistic comes from.

1. **Every velocity's best theta is 0.0 — the trigger is "the vector changed at all", not a rate.**
   28.6% of rows have velocity exactly zero; the onset-within-1 rate after a zero-velocity row is 0.045
   vs 0.224 after any nonzero step. Raising theta above zero only *lowers* precision (companion
   `_all_source_composition` file: among non-idle rows at k=1, P=0.362 at velocity>0, 0.312 at the 75th
   percentile, 0.276 at the 90th).
2. **The zero/nonzero cut is source composition, not state dynamics.** `unresolved` is only ever set on
   `source=idle` rows (null on every other source — see the script docstring); 99.7% of all-source
   "onsets" have a non-idle row at t-1 (72% `inner_thought`), so an onset at t+1 is only possible when
   row t is non-idle. Zero-velocity rows are overwhelmingly `reading` rows: 92% of reading rows carry a
   vector identical to the previous row (99.1% of reading->reading steps, and still 92% after the
   2026-08-29 null-fill fix), because the mood/somatic caches do not move between reading snapshots.
   "velocity > 0" therefore means "not inside a reading stretch", which is why the all-source held-out
   ROC-AUC (0.64–0.73) looks like a signal. Restricted to the only rows where a lead could act — a
   non-idle row whose NEXT row is idle — P(onset) is 0.556 and ranking by velocity gives AP 0.569:
   no lift (companion file, "non-idle rows whose NEXT row is idle").
3. **The D-0196 bar (P >= 0.5 at R >= 0.3, held-out) is numerically touched only at k=3**, where the
   positive base rate is 0.446 and always-fire already gives P=0.446: velocity>0 gives P=0.569 /
   R=0.831 (lift 1.28x, all of it the zero/nonzero cut above). At k=1 — the actual "pre-onset warning"
   claim — no theta on any velocity exceeds P=0.31 (base 0.17), and `tension_tick` is at chance
   (AUC 0.53). A post-2026-08-29-only run (companion file) gives the same picture (k=1 best held-out
   P 0.30–0.31 at R 0.4–0.6).
4. **The honest characterisation is the idle-only run** (`_idle_only` file): on the only rows that carry
   a real label, every velocity definition is at chance (held-out AUC 0.486–0.493), precision at any
   fixed recall equals the base rate, and F-0932's population difference reverses sign or vanishes.

**Verdict: no velocity threshold beats a trivial baseline as a per-instance trigger. F-0932's
"elevated before a fresh onset" lead claim is retracted as a source-interleaving artefact (null-label
non-idle rows + frozen-vector reading stretches). D-0196's defeater lands on its shelve branch; nothing
here justifies a gauge, a shadow gauge, or a trigger.** Finding recorded in the findings ledger under
J-0838; see `docs/staged/geometry_tuple_index.md` Current State for the dated note.
