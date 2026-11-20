# Pre-onset tangent-velocity characterisation — D-0196 / J-0838 (2026-09-11)

> **Status: LAB RESULT (read-only analysis). No wiring, no gauge, nothing Du-facing.** Produced by `scripts/pre_onset_velocity_characterisation.py`; machine-readable sweep in the `.jsonl` beside this file. Interpretation is in the sections marked *Reading* below the tables.

## Setup

- Data: `data/geometry_tuples.jsonl`, 27874 rows, 40 distinct UTC days (2026-07-04 .. 2026-09-11), sorted by `ts`. `unresolved` rows: 17210 (61.7%). Fresh onsets (first tuple of an unresolved run): 6766.
- Chronological split by day: fit = first 28 days (2026-07-04 .. 2026-08-30, 17562 rows, 4005 onsets); **held-out = last 12 days (2026-08-31 .. 2026-09-11, 10312 rows, 2761 onsets)**. Every theta/tau is chosen on the fit days only; every headline number below is held-out.
- Trigger: `score(t) > theta`. Positive: a fresh onset at any step in `(t, t+k]`, k in {1,2,3}. Theta sweep = the 0..99th, 99.5th, 99.9th percentiles of the fit-period score.
- Scores: `raw_velocity` = ||x_t − x_{t−1}|| on the raw 5-vector (tension, energy, valence, arousal, level); `fit_standardized_velocity` = same after z-scoring each dimension with fit-period mean/std (floor √0.05); `adaptive_velocity` = F-0932's rolling-window standardized step (window 2000, refit every 50, first 2000 rows unscored).
- Baselines: `random` = a trigger firing uniformly at random at the same rate as the chosen theta (expected precision = onset base rate, recall = fire rate); `always` = fire every step; `tension_tick` = `tension(t) > tau`, tau chosen on the fit days exactly as theta is.
- D-0196 defeater bar: **precision ≥ 0.5 at recall ≥ 0.3 on held-out days.**

- Step-gap note: 25% of consecutive rows are ≤0.2 s apart (bursts of tuples from one cycle), median gap 13 s, 1.41% of gaps exceed 10 min. A sensitivity row below excludes burst steps (gap < 1 s) to check the signal is not an artefact of near-duplicate rows.

## Horizon k=1: onset within the next 1 step

Positive base rate: fit 0.228, held-out 0.268 (`always` baseline: P=0.268, R=1.000, F1=0.422).

| score | theta (fit-best-F1) | fit P/R/F1 | **held-out P/R/F1** | fire rate (ho) | lift vs base | random @ same rate (P/R/F1) | held-out ROC-AUC | held-out AP | bar met (ho, any theta)? |
|---|---|---|---|---|---|---|---|---|---|
| `raw_velocity` | 0.0000 | 0.227/0.953/0.367 | **0.267/0.984/0.420** | 0.986 | 1.00x | 0.268/0.986/0.421 | 0.487 | 0.263 | no |
| `fit_standardized_velocity` | 0.0000 | 0.227/0.953/0.367 | **0.267/0.984/0.420** | 0.986 | 1.00x | 0.268/0.986/0.421 | 0.487 | 0.261 | no |
| `adaptive_velocity` | 0.0000 | 0.229/0.956/0.369 | **0.267/0.984/0.420** | 0.986 | 1.00x | 0.268/0.986/0.421 | 0.487 | 0.262 | no |
| `tension_tick` | 0.0000 | 0.230/0.973/0.372 | **0.269/0.991/0.423** | 0.987 | 1.00x | 0.268/0.987/0.421 | 0.503 | 0.267 | no |

Held-out operating points (precision at fixed recall) — the honest way to read whether ANY theta reaches the bar:

| score | P@R≥0.1 | P@R≥0.2 | P@R≥0.3 | P@R≥0.5 | P@R≥0.8 |
|---|---|---|---|---|---|
| `raw_velocity` | 0.240 | 0.250 | 0.255 | 0.262 | 0.265 |
| `fit_standardized_velocity` | 0.248 | 0.247 | 0.254 | 0.262 | 0.265 |
| `adaptive_velocity` | 0.246 | 0.249 | 0.254 | 0.260 | 0.266 |
| `tension_tick` | 0.256 | 0.257 | 0.264 | 0.271 | 0.270 |

Sensitivity — same sweep with burst steps (gap < 1 s) excluded from both fit and held-out:

| score | theta | held-out P/R/F1 | fire rate | held-out ROC-AUC |
|---|---|---|---|---|
| `raw_velocity` | 0.0000 | 0.267/0.984/0.420 | 0.986 | 0.487 |
| `fit_standardized_velocity` | 0.0000 | 0.267/0.984/0.420 | 0.986 | 0.487 |
| `adaptive_velocity` | 0.0000 | 0.267/0.984/0.420 | 0.986 | 0.487 |

(no-burst held-out base rate: 0.268)

Per-day held-out stability for `raw_velocity` at theta=0.0000:

| day | rows | onsets | P | R | fire rate |
|---|---|---|---|---|---|
| 2026-08-31 | 273 | 79 | 0.292 | 1.000 | 0.993 |
| 2026-09-01 | 152 | 25 | 0.167 | 1.000 | 0.987 |
| 2026-09-02 | 1053 | 271 | 0.257 | 0.978 | 0.978 |
| 2026-09-03 | 1092 | 302 | 0.274 | 0.977 | 0.987 |
| 2026-09-04 | 1348 | 355 | 0.265 | 0.986 | 0.979 |
| 2026-09-05 | 1260 | 347 | 0.276 | 0.986 | 0.985 |
| 2026-09-06 | 1117 | 286 | 0.251 | 0.965 | 0.984 |
| 2026-09-07 | 969 | 264 | 0.275 | 0.992 | 0.981 |
| 2026-09-08 | 718 | 190 | 0.266 | 0.995 | 0.989 |
| 2026-09-09 | 845 | 228 | 0.269 | 0.991 | 0.995 |
| 2026-09-10 | 1431 | 401 | 0.278 | 0.983 | 0.991 |
| 2026-09-11 | 53 | 13 | 0.245 | 1.000 | 1.000 |

## Horizon k=2: onset within the next 2 steps

Positive base rate: fit 0.456, held-out 0.536 (`always` baseline: P=0.536, R=1.000, F1=0.698).

| score | theta (fit-best-F1) | fit P/R/F1 | **held-out P/R/F1** | fire rate (ho) | lift vs base | random @ same rate (P/R/F1) | held-out ROC-AUC | held-out AP | bar met (ho, any theta)? |
|---|---|---|---|---|---|---|---|---|---|
| `raw_velocity` | 0.0000 | 0.455/0.954/0.616 | **0.536/0.986/0.694** | 0.986 | 1.00x | 0.536/0.986/0.694 | 0.492 | 0.531 | YES @ theta=0.0204 -> P=0.524 R=0.304 F1=0.385 fire=0.311 (tp=1681 fp=1524 fn=3841) |
| `fit_standardized_velocity` | 0.0000 | 0.455/0.954/0.616 | **0.536/0.986/0.694** | 0.986 | 1.00x | 0.536/0.986/0.694 | 0.491 | 0.528 | YES @ theta=0.0558 -> P=0.523 R=0.301 F1=0.382 fire=0.308 (tp=1662 fp=1516 fn=3860) |
| `adaptive_velocity` | 0.0000 | 0.459/0.959/0.620 | **0.536/0.986/0.694** | 0.986 | 1.00x | 0.536/0.986/0.694 | 0.493 | 0.53 | YES @ theta=0.0674 -> P=0.527 R=0.300 F1=0.382 fire=0.305 (tp=1657 fp=1486 fn=3865) |
| `tension_tick` | 0.0000 | 0.460/0.974/0.624 | **0.538/0.991/0.697** | 0.987 | 1.00x | 0.536/0.987/0.694 | 0.504 | 0.534 | YES @ theta=0.3440 -> P=0.528 R=0.302 F1=0.385 fire=0.306 (tp=1670 fp=1490 fn=3852) |

Held-out operating points (precision at fixed recall) — the honest way to read whether ANY theta reaches the bar:

| score | P@R≥0.1 | P@R≥0.2 | P@R≥0.3 | P@R≥0.5 | P@R≥0.8 |
|---|---|---|---|---|---|
| `raw_velocity` | 0.514 | 0.520 | 0.524 | 0.534 | 0.532 |
| `fit_standardized_velocity` | 0.524 | 0.517 | 0.523 | 0.530 | 0.531 |
| `adaptive_velocity` | 0.521 | 0.525 | 0.528 | 0.531 | 0.533 |
| `tension_tick` | 0.511 | 0.515 | 0.528 | 0.541 | 0.540 |

Sensitivity — same sweep with burst steps (gap < 1 s) excluded from both fit and held-out:

| score | theta | held-out P/R/F1 | fire rate | held-out ROC-AUC |
|---|---|---|---|---|
| `raw_velocity` | 0.0000 | 0.536/0.986/0.694 | 0.986 | 0.492 |
| `fit_standardized_velocity` | 0.0000 | 0.536/0.986/0.694 | 0.986 | 0.491 |
| `adaptive_velocity` | 0.0000 | 0.536/0.986/0.694 | 0.986 | 0.493 |

(no-burst held-out base rate: 0.536)

Per-day held-out stability for `raw_velocity` at theta=0.0000:

| day | rows | onsets | P | R | fire rate |
|---|---|---|---|---|---|
| 2026-08-31 | 273 | 159 | 0.583 | 0.994 | 0.993 |
| 2026-09-01 | 152 | 49 | 0.320 | 0.980 | 0.987 |
| 2026-09-02 | 1053 | 543 | 0.517 | 0.982 | 0.978 |
| 2026-09-03 | 1092 | 604 | 0.551 | 0.983 | 0.987 |
| 2026-09-04 | 1348 | 709 | 0.527 | 0.982 | 0.979 |
| 2026-09-05 | 1260 | 695 | 0.552 | 0.986 | 0.985 |
| 2026-09-06 | 1117 | 571 | 0.509 | 0.979 | 0.984 |
| 2026-09-07 | 969 | 528 | 0.547 | 0.985 | 0.981 |
| 2026-09-08 | 718 | 380 | 0.531 | 0.992 | 0.989 |
| 2026-09-09 | 845 | 456 | 0.540 | 0.996 | 0.995 |
| 2026-09-10 | 1431 | 802 | 0.560 | 0.990 | 0.991 |
| 2026-09-11 | 52 | 26 | 0.500 | 1.000 | 1.000 |

## Horizon k=3: onset within the next 3 steps

Positive base rate: fit 0.633, held-out 0.726 (`always` baseline: P=0.726, R=1.000, F1=0.841).

| score | theta (fit-best-F1) | fit P/R/F1 | **held-out P/R/F1** | fire rate (ho) | lift vs base | random @ same rate (P/R/F1) | held-out ROC-AUC | held-out AP | bar met (ho, any theta)? |
|---|---|---|---|---|---|---|---|---|---|
| `raw_velocity` | 0.0000 | 0.631/0.955/0.760 | **0.726/0.986/0.836** | 0.986 | 1.00x | 0.726/0.986/0.836 | 0.488 | 0.718 | YES @ theta=0.0204 -> P=0.715 R=0.306 F1=0.429 fire=0.311 (tp=2292 fp=913 fn=5194) |
| `fit_standardized_velocity` | 0.0000 | 0.631/0.955/0.760 | **0.726/0.986/0.836** | 0.986 | 1.00x | 0.726/0.986/0.836 | 0.486 | 0.715 | YES @ theta=0.0558 -> P=0.712 R=0.302 F1=0.424 fire=0.308 (tp=2263 fp=915 fn=5223) |
| `adaptive_velocity` | 0.0000 | 0.633/0.958/0.763 | **0.726/0.986/0.837** | 0.986 | 1.00x | 0.726/0.986/0.836 | 0.488 | 0.717 | YES @ theta=0.0674 -> P=0.718 R=0.302 F1=0.425 fire=0.305 (tp=2258 fp=885 fn=5228) |
| `tension_tick` | 0.0000 | 0.636/0.972/0.769 | **0.729/0.991/0.840** | 0.987 | 1.00x | 0.726/0.987/0.837 | 0.499 | 0.719 | YES @ theta=0.3440 -> P=0.716 R=0.302 F1=0.425 fire=0.307 (tp=2264 fp=896 fn=5222) |

Held-out operating points (precision at fixed recall) — the honest way to read whether ANY theta reaches the bar:

| score | P@R≥0.1 | P@R≥0.2 | P@R≥0.3 | P@R≥0.5 | P@R≥0.8 |
|---|---|---|---|---|---|
| `raw_velocity` | 0.709 | 0.711 | 0.713 | 0.722 | 0.723 |
| `fit_standardized_velocity` | 0.717 | 0.711 | 0.713 | 0.719 | 0.721 |
| `adaptive_velocity` | 0.709 | 0.716 | 0.718 | 0.722 | 0.722 |
| `tension_tick` | 0.685 | 0.700 | 0.716 | 0.728 | 0.730 |

Sensitivity — same sweep with burst steps (gap < 1 s) excluded from both fit and held-out:

| score | theta | held-out P/R/F1 | fire rate | held-out ROC-AUC |
|---|---|---|---|---|
| `raw_velocity` | 0.0000 | 0.726/0.986/0.836 | 0.986 | 0.488 |
| `fit_standardized_velocity` | 0.0000 | 0.726/0.986/0.836 | 0.986 | 0.486 |
| `adaptive_velocity` | 0.0000 | 0.726/0.986/0.837 | 0.986 | 0.488 |

(no-burst held-out base rate: 0.726)

Per-day held-out stability for `adaptive_velocity` at theta=0.0000:

| day | rows | onsets | P | R | fire rate |
|---|---|---|---|---|---|
| 2026-08-31 | 273 | 206 | 0.753 | 0.990 | 0.993 |
| 2026-09-01 | 152 | 69 | 0.453 | 0.986 | 0.987 |
| 2026-09-02 | 1053 | 741 | 0.707 | 0.982 | 0.978 |
| 2026-09-03 | 1092 | 807 | 0.737 | 0.985 | 0.988 |
| 2026-09-04 | 1348 | 972 | 0.721 | 0.980 | 0.980 |
| 2026-09-05 | 1260 | 927 | 0.737 | 0.986 | 0.985 |
| 2026-09-06 | 1117 | 780 | 0.697 | 0.982 | 0.984 |
| 2026-09-07 | 969 | 721 | 0.746 | 0.983 | 0.981 |
| 2026-09-08 | 718 | 522 | 0.730 | 0.992 | 0.989 |
| 2026-09-09 | 845 | 619 | 0.732 | 0.995 | 0.995 |
| 2026-09-10 | 1431 | 1085 | 0.758 | 0.991 | 0.992 |
| 2026-09-11 | 51 | 37 | 0.725 | 1.000 | 1.000 |

## Burst diagnostics — where does the theta=0 signal come from?

- Rows with exactly zero velocity: 907 (3.3% of scored rows). Of those, 0.0% are burst steps (gap < 1 s); 0.0% of burst steps have zero velocity. Burst steps are 0.0% of all steps.
- `unresolved` flips at a burst step 0 times out of 0 burst steps; fresh onsets sitting at a burst step: 0 / 6766.
- Onset-within-k rate conditioned on the row at t:

| k | after a zero-velocity row | after a nonzero-velocity row | after a nonzero-velocity NON-burst row |
|---|---|---|---|
| 1 | 0.259 | 0.242 | 0.242 |
| 2 | 0.491 | 0.485 | 0.485 |
| 3 | 0.665 | 0.667 | 0.667 |

No-burst held-out operating points (precision at fixed recall), velocity scores only:

| k | score | base rate | P@R≥0.1 | P@R≥0.3 | P@R≥0.5 | P@R≥0.8 |
|---|---|---|---|---|---|---|
| 1 | `raw_velocity` | 0.268 | 0.240 | 0.255 | 0.262 | 0.265 |
| 1 | `fit_standardized_velocity` | 0.268 | 0.248 | 0.254 | 0.262 | 0.265 |
| 1 | `adaptive_velocity` | 0.268 | 0.246 | 0.254 | 0.260 | 0.266 |
| 2 | `raw_velocity` | 0.536 | 0.514 | 0.524 | 0.534 | 0.532 |
| 2 | `fit_standardized_velocity` | 0.536 | 0.524 | 0.523 | 0.530 | 0.531 |
| 2 | `adaptive_velocity` | 0.536 | 0.521 | 0.528 | 0.531 | 0.533 |
| 3 | `raw_velocity` | 0.726 | 0.709 | 0.713 | 0.722 | 0.723 |
| 3 | `fit_standardized_velocity` | 0.726 | 0.717 | 0.713 | 0.719 | 0.721 |
| 3 | `adaptive_velocity` | 0.726 | 0.709 | 0.718 | 0.722 | 0.722 |

## Population-level check (F-0932's own statistic, held-out block only)

| score | k | mean pre-onset | mean other | Mann-Whitney p |
|---|---|---|---|---|
| `raw_velocity` | 1 | 0.0447 | 0.0446 | 0.048 |
| `raw_velocity` | 2 | 0.0443 | 0.0450 | 0.165 |
| `raw_velocity` | 3 | 0.0435 | 0.0475 | 0.0626 |
| `fit_standardized_velocity` | 1 | 0.1327 | 0.1380 | 0.0385 |
| `fit_standardized_velocity` | 2 | 0.1333 | 0.1404 | 0.12 |
| `fit_standardized_velocity` | 3 | 0.1316 | 0.1498 | 0.0302 |
| `adaptive_velocity` | 1 | 0.1472 | 0.1514 | 0.036 |
| `adaptive_velocity` | 2 | 0.1473 | 0.1537 | 0.192 |
| `adaptive_velocity` | 3 | 0.1458 | 0.1621 | 0.07 |

## Verdict against the D-0196 bar

D-0196 defeater bar (precision ≥ 0.5 at recall ≥ 0.3, held-out): **MET at some theta** — see the 'bar met' column.

Held-out summary (theta chosen on fit days by best F1):

| k | score | held-out P | held-out R | held-out F1 | ROC-AUC | AP | bar |
|---|---|---|---|---|---|---|---|
| 1 | `raw_velocity` | 0.267 | 0.984 | 0.420 | 0.487 | 0.263 | no |
| 1 | `fit_standardized_velocity` | 0.267 | 0.984 | 0.420 | 0.487 | 0.261 | no |
| 1 | `adaptive_velocity` | 0.267 | 0.984 | 0.420 | 0.487 | 0.262 | no |
| 1 | `tension_tick` | 0.269 | 0.991 | 0.423 | 0.503 | 0.267 | no |
| 2 | `raw_velocity` | 0.536 | 0.986 | 0.694 | 0.492 | 0.531 | yes |
| 2 | `fit_standardized_velocity` | 0.536 | 0.986 | 0.694 | 0.491 | 0.528 | yes |
| 2 | `adaptive_velocity` | 0.536 | 0.986 | 0.694 | 0.493 | 0.530 | yes |
| 2 | `tension_tick` | 0.538 | 0.991 | 0.697 | 0.504 | 0.534 | yes |
| 3 | `raw_velocity` | 0.726 | 0.986 | 0.836 | 0.488 | 0.718 | yes |
| 3 | `fit_standardized_velocity` | 0.726 | 0.986 | 0.836 | 0.486 | 0.715 | yes |
| 3 | `adaptive_velocity` | 0.726 | 0.986 | 0.837 | 0.488 | 0.717 | yes |
| 3 | `tension_tick` | 0.729 | 0.991 | 0.840 | 0.499 | 0.719 | yes |


## Reading (written by hand after the run — J-0838, 2026-09-11)

**This is the honest characterisation.** Only idle-source rows carry a real `unresolved` label (see the
label caveat in the script docstring and the all-source file's Reading); here a "fresh onset" is Du's own
idle thought turning unresolved after being resolved, with velocity measured between consecutive idle
tuples (27,874 rows; fit 2026-07-04..08-30, held-out 2026-08-31..09-11, 2,761 held-out onsets).

1. **Velocity has no per-instance discriminative power for an upcoming onset.** Held-out ROC-AUC is
   0.486–0.493 for all three velocity definitions at k=1, 2 and 3 — chance, slightly the wrong side of
   it. Precision at every fixed recall equals the positive base rate (k=1: 0.25–0.27 vs base 0.267;
   k=2: 0.52–0.54 vs 0.536; k=3: 0.71–0.73 vs 0.726). Lift vs always-fire: 1.00x; the random-rate
   baseline has the same numbers within rounding.
2. **The population-level statistic reverses or vanishes.** On held-out days pre-onset velocity is
   slightly *lower* than elsewhere (raw k=3: 0.0435 vs 0.0475, p=0.06; standardized 0.132 vs 0.150,
   p=0.03; k=2 all p>0.1) — small, and the opposite sign to F-0932's claim. With AUC at chance this is
   not a usable signal in either direction; it confirms the elevation seen in the all-source run was the
   interleaving artefact, not Du's affective dynamics.
3. **The D-0196 bar is "met" at k=2 and k=3 purely by base rate.** Positives are 54% of held-out steps
   at k=2 and 73% at k=3, so any trigger that fires at all clears P >= 0.5 — including `tension_tick`
   (AUC 0.50). No threshold beats a trivial baseline: this is the defeater's *shelve* branch.
4. Per-day held-out rows (tables above) show no day on which any trigger separates from the base rate;
   the burst-exclusion sensitivity run is identical (no idle-only steps are bursts).

**Recommendation:** shelve the pre-onset velocity signal as a trigger/gauge candidate; retract F-0932's
lead claim. F-0932's separate contemporaneous-drop claim (velocity lower DURING unresolved runs) was not
re-tested here and is affected by the same null-coercion — it is spawned as its own re-check, not
assumed either way.
