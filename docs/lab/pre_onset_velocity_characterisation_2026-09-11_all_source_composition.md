# Pre-onset tangent-velocity characterisation (J-0838 / D-0196 / F-0932)

Run 2026-09-11T00:49:35+00:00 by `scripts/pre_onset_velocity_composition_check.py`. Read-only over `data/geometry_tuples.jsonl` (63426 rows, 40 UTC days, 41 gap-free segments at a 3600s break) and a schema check of `data/moments.jsonl` (28638 rows). Companion data: `pre_onset_velocity_characterisation_2026-09-11_all_source_composition.jsonl`.

## Setup
- Vector: ['tension', 'energy', 'valence', 'arousal', 'level'] (unresolved held out as the label), null body/affect filled with [0.1, 0.5, 0.5, 0.3, 0.5] exactly as `C:/UDMS/scripts/analyze_nascence_geometry_manifold.py::extract_vector` does.
- Positive at step t: a FRESH unresolved onset (`first_in_run_mask`) at any of t+1..t+k, k in 1..3, not crossing a >1h gap.
- Trigger: velocity > theta at t. Three velocity definitions (the three F-0932 methodologies): `raw` = ||x_t - x_{t-1}|| in raw units; `pca_tangent` = UDMSEngine 2-D tangent step (PCA fit on train days only, EVR [0.4217, 0.2171, 0.1987, 0.1252, 0.0373]); `adaptive` = step of the vector standardised by the previous 2000 rows (std floor sqrt(0.05)).
- Chronological split by DAY: fit theta on the first 28 days (2026-07-04 .. 2026-08-30, 29941 rows), report on the last 12 days (2026-08-31 .. 2026-09-11, 33485 rows).
- Theta chosen on train two ways: max F1, and max precision subject to recall >= 0.3 (D-0196's defeater bar is precision >= 0.5 at recall >= 0.3 on held-out days). An 'oracle' theta (best F1 on TEST) is shown only as an upper bound.
- Baselines: always-fire / random-at-matched-rate (precision = base rate), high-tension tick (tension_t > tau, tau swept the same way), and label-adjacent triggers that use only what is known at t: `not_unresolved_now`, `row_t_is_non_idle`, `idle_and_not_unresolved_now`.

## Data facts that shape the answer
- `unresolved` is True ONLY on `source=idle` rows: idle: 0.617/27874, inner_thought: 0.0/14208, reading: 0.0/11478, subconscious_synthesis: 0.0/2054, monologue: 0.0/1270, active_imagination: 0.0/1156, study: 0.0/1070, cycle: 0.0/1057 (rate per source). 10961 fresh onsets / 17210 unresolved rows.
- `moments.jsonl` keys: ['affect', 'concern', 'emb', 'key', 'level', 'protoself', 'source', 'thought', 'ts'] -- it carries NO `unresolved` (or any resolution) label, so the positive class can only be defined on geometry_tuples.jsonl; moments.jsonl contributes nothing to this question and is not used further.
- Null body/affect (filled with defaults): pre-2026-08-29 body null 0.325, affect null 0.319; post-fix body null 0.020, affect null 0.000.
- Mean `raw` velocity at a source switch vs within-source: 0.1355 vs 0.0251 (switch rows pre-fix 0.4883, post-fix 0.0317).
- Mean `pca_tangent` velocity at a source switch vs within-source: 0.5533 vs 0.0444 (switch rows pre-fix 2.1344, post-fix 0.0882).
- Mean `adaptive` velocity at a source switch vs within-source: 0.5084 vs 0.0763 (switch rows pre-fix 1.8832, post-fix 0.1096).

## F-0932's own statistic, on the held-out days (k=3, pre-onset mean vs other)
- `raw`: pre-onset 0.0270 vs other 0.0213, n_pre=14931, MWU p=0
- `pca_tangent`: pre-onset 0.0625 vs other 0.0619, n_pre=14931, MWU p=0
- `adaptive`: pre-onset 0.0915 vs other 0.0730, n_pre=14931, MWU p=0

## Config `all_rows`
### k=1  (base rate train 0.175, test 0.170)
| trigger | theta (train maxF1) | TEST at that theta | theta (train maxP, R>=0.3) | TEST at that theta | AP test | AP train | oracle-test F1 |
|---|---|---|---|---|---|---|---|
| velocity_raw | 0.0000 | P=0.245 R=0.938 F1=0.388 fire=0.652 | 0.0000 | P=0.245 R=0.938 F1=0.388 fire=0.652 | 0.272 | 0.197 | 0.400 |
| velocity_pca_tangent | 0.0000 | P=0.245 R=0.938 F1=0.388 fire=0.652 | 0.0000 | P=0.245 R=0.938 F1=0.388 fire=0.652 | 0.274 | 0.198 | 0.406 |
| velocity_adaptive | 0.0000 | P=0.245 R=0.938 F1=0.388 fire=0.652 | 0.0000 | P=0.245 R=0.938 F1=0.388 fire=0.652 | 0.278 | 0.195 | 0.410 |
| velocity_raw | not_unresolved_now | 0.0000 | P=0.298 R=0.938 F1=0.452 fire=0.646 | 0.0010 | P=0.303 R=0.914 F1=0.455 fire=0.620 | 0.296 | 0.329 | 0.455 |
| velocity_adaptive | not_unresolved_now | 0.0000 | P=0.298 R=0.938 F1=0.452 fire=0.646 | 0.0045 | P=0.303 R=0.920 F1=0.456 fire=0.623 | 0.300 | 0.318 | 0.456 |
| high_tension_tick | 0.0000 | P=0.171 R=1.000 F1=0.292 fire=0.993 | 0.0000 | P=0.171 R=1.000 F1=0.292 fire=0.993 | 0.183 | 0.165 | 0.294 |
| always_fire | - | P=0.170 R=1.000 F1=0.291 fire=1.000 | - | - | - | - | - |
| not_unresolved_now | - | P=0.205 R=1.000 F1=0.341 fire=0.829 | - | - | - | - | - |
| row_t_is_non_idle | - | P=0.245 R=0.997 F1=0.393 fire=0.692 | - | - | - | - | - |
| idle_and_not_unresolved_now | - | P=0.004 R=0.003 F1=0.003 fire=0.137 | - | - | - | - | - |
| random at velocity_raw's fire rate | - | P=0.170 R=0.652 F1=0.270 fire=0.652 | - | - | - | - | - |

### k=2  (base rate train 0.351, test 0.340)
| trigger | theta (train maxF1) | TEST at that theta | theta (train maxP, R>=0.3) | TEST at that theta | AP test | AP train | oracle-test F1 |
|---|---|---|---|---|---|---|---|
| velocity_raw | 0.0000 | P=0.438 R=0.839 F1=0.575 fire=0.652 | 0.0000 | P=0.438 R=0.839 F1=0.575 fire=0.652 | 0.417 | 0.406 | 0.575 |
| velocity_pca_tangent | 0.0000 | P=0.438 R=0.839 F1=0.575 fire=0.652 | 0.0000 | P=0.438 R=0.839 F1=0.575 fire=0.652 | 0.413 | 0.404 | 0.575 |
| velocity_adaptive | 0.0000 | P=0.438 R=0.839 F1=0.575 fire=0.652 | 0.0000 | P=0.438 R=0.839 F1=0.575 fire=0.652 | 0.418 | 0.400 | 0.575 |
| velocity_raw | not_unresolved_now | 0.0000 | P=0.450 R=0.876 F1=0.595 fire=0.646 | 0.0010 | P=0.452 R=0.844 F1=0.589 fire=0.620 | 0.422 | 0.494 | 0.595 |
| velocity_adaptive | not_unresolved_now | 0.0000 | P=0.450 R=0.876 F1=0.595 fire=0.646 | 0.0000 | P=0.450 R=0.876 F1=0.595 fire=0.646 | 0.423 | 0.478 | 0.595 |
| high_tension_tick | 0.0000 | P=0.341 R=0.997 F1=0.509 fire=0.993 | 0.1000 | P=0.345 R=0.987 F1=0.512 fire=0.972 | 0.366 | 0.366 | 0.512 |
| always_fire | - | P=0.340 R=1.000 F1=0.508 fire=1.000 | - | - | - | - | - |
| not_unresolved_now | - | P=0.332 R=0.809 F1=0.471 fire=0.829 | - | - | - | - | - |
| row_t_is_non_idle | - | P=0.315 R=0.642 F1=0.423 fire=0.692 | - | - | - | - | - |
| idle_and_not_unresolved_now | - | P=0.416 R=0.167 F1=0.238 fire=0.137 | - | - | - | - | - |
| random at velocity_raw's fire rate | - | P=0.340 R=0.652 F1=0.447 fire=0.652 | - | - | - | - | - |

### k=3  (base rate train 0.479, test 0.446)
| trigger | theta (train maxF1) | TEST at that theta | theta (train maxP, R>=0.3) | TEST at that theta | AP test | AP train | oracle-test F1 |
|---|---|---|---|---|---|---|---|
| velocity_raw | 0.0000 | P=0.569 R=0.831 F1=0.675 fire=0.652 | 0.0000 | P=0.569 R=0.831 F1=0.675 fire=0.652 | 0.544 | 0.540 | 0.675 |
| velocity_pca_tangent | 0.0000 | P=0.569 R=0.831 F1=0.675 fire=0.652 | 0.0000 | P=0.569 R=0.831 F1=0.675 fire=0.652 | 0.540 | 0.539 | 0.675 |
| velocity_adaptive | 0.0000 | P=0.569 R=0.831 F1=0.675 fire=0.652 | 0.0000 | P=0.569 R=0.831 F1=0.675 fire=0.652 | 0.545 | 0.530 | 0.675 |
| velocity_raw | not_unresolved_now | 0.0000 | P=0.589 R=0.864 F1=0.701 fire=0.646 | 0.0020 | P=0.592 R=0.790 F1=0.677 fire=0.588 | 0.551 | 0.606 | 0.701 |
| velocity_adaptive | not_unresolved_now | 0.0000 | P=0.589 R=0.864 F1=0.701 fire=0.646 | 0.0089 | P=0.592 R=0.765 F1=0.668 fire=0.570 | 0.552 | 0.588 | 0.701 |
| high_tension_tick | 0.0000 | P=0.447 R=0.996 F1=0.617 fire=0.993 | 0.1000 | P=0.452 R=0.986 F1=0.620 fire=0.972 | 0.477 | 0.501 | 0.620 |
| always_fire | - | P=0.446 R=1.000 F1=0.617 fire=1.000 | - | - | - | - | - |
| not_unresolved_now | - | P=0.441 R=0.819 F1=0.573 fire=0.829 | - | - | - | - | - |
| row_t_is_non_idle | - | P=0.422 R=0.655 F1=0.514 fire=0.692 | - | - | - | - | - |
| idle_and_not_unresolved_now | - | P=0.534 R=0.164 F1=0.251 fire=0.137 | - | - | - | - | - |
| random at velocity_raw's fire rate | - | P=0.446 R=0.652 F1=0.530 fire=0.652 | - | - | - | - | - |

## Config `post_null_fix_only (rows from 2026-08-29 on; train/test split unchanged)`
### k=1  (base rate train 0.166, test 0.170)
| trigger | theta (train maxF1) | TEST at that theta | theta (train maxP, R>=0.3) | TEST at that theta | AP test | AP train | oracle-test F1 |
|---|---|---|---|---|---|---|---|
| velocity_raw | 0.0030 | P=0.263 R=0.828 F1=0.399 fire=0.536 | 0.0158 | P=0.300 R=0.384 F1=0.337 fire=0.218 | 0.272 | 0.251 | 0.402 |
| velocity_pca_tangent | 0.0149 | P=0.300 R=0.562 F1=0.391 fire=0.319 | 0.0192 | P=0.303 R=0.477 F1=0.370 fire=0.268 | 0.274 | 0.259 | 0.404 |
| velocity_adaptive | 0.0162 | P=0.282 R=0.749 F1=0.409 fire=0.453 | 0.0452 | P=0.310 R=0.423 F1=0.358 fire=0.232 | 0.278 | 0.253 | 0.410 |
| velocity_raw | not_unresolved_now | 0.0010 | P=0.303 R=0.914 F1=0.455 fire=0.620 | 0.0062 | P=0.315 R=0.671 F1=0.429 fire=0.437 | 0.296 | 0.294 | 0.455 |
| velocity_adaptive | not_unresolved_now | 0.0091 | P=0.310 R=0.858 F1=0.455 fire=0.568 | 0.0257 | P=0.324 R=0.619 F1=0.426 fire=0.391 | 0.300 | 0.296 | 0.457 |
| high_tension_tick | 0.2100 | P=0.176 R=0.860 F1=0.292 fire=0.830 | 0.2100 | P=0.176 R=0.860 F1=0.292 fire=0.830 | 0.183 | 0.146 | 0.294 |
| always_fire | - | P=0.170 R=1.000 F1=0.291 fire=1.000 | - | - | - | - | - |
| not_unresolved_now | - | P=0.205 R=1.000 F1=0.341 fire=0.829 | - | - | - | - | - |
| row_t_is_non_idle | - | P=0.245 R=0.997 F1=0.393 fire=0.692 | - | - | - | - | - |
| idle_and_not_unresolved_now | - | P=0.004 R=0.003 F1=0.003 fire=0.137 | - | - | - | - | - |
| random at velocity_raw's fire rate | - | P=0.170 R=0.536 F1=0.258 fire=0.536 | - | - | - | - | - |

### k=2  (base rate train 0.333, test 0.340)
| trigger | theta (train maxF1) | TEST at that theta | theta (train maxP, R>=0.3) | TEST at that theta | AP test | AP train | oracle-test F1 |
|---|---|---|---|---|---|---|---|
| velocity_raw | 0.0000 | P=0.438 R=0.839 F1=0.575 fire=0.652 | 0.0052 | P=0.443 R=0.572 F1=0.500 fire=0.439 | 0.417 | 0.397 | 0.575 |
| velocity_pca_tangent | 0.0000 | P=0.438 R=0.839 F1=0.575 fire=0.652 | 0.0035 | P=0.442 R=0.729 F1=0.550 fire=0.561 | 0.413 | 0.395 | 0.575 |
| velocity_adaptive | 0.0000 | P=0.438 R=0.839 F1=0.575 fire=0.652 | 0.0162 | P=0.445 R=0.592 F1=0.508 fire=0.453 | 0.418 | 0.396 | 0.575 |
| velocity_raw | not_unresolved_now | 0.0000 | P=0.450 R=0.876 F1=0.595 fire=0.646 | 0.0030 | P=0.453 R=0.750 F1=0.565 fire=0.550 | 0.422 | 0.412 | 0.595 |
| velocity_adaptive | not_unresolved_now | 0.0000 | P=0.450 R=0.876 F1=0.595 fire=0.646 | 0.0091 | P=0.454 R=0.777 F1=0.573 fire=0.568 | 0.423 | 0.410 | 0.595 |
| high_tension_tick | 0.1000 | P=0.345 R=0.987 F1=0.512 fire=0.972 | 0.2100 | P=0.352 R=0.860 F1=0.500 fire=0.830 | 0.366 | 0.297 | 0.512 |
| always_fire | - | P=0.340 R=1.000 F1=0.508 fire=1.000 | - | - | - | - | - |
| not_unresolved_now | - | P=0.332 R=0.809 F1=0.471 fire=0.829 | - | - | - | - | - |
| row_t_is_non_idle | - | P=0.315 R=0.642 F1=0.423 fire=0.692 | - | - | - | - | - |
| idle_and_not_unresolved_now | - | P=0.416 R=0.167 F1=0.238 fire=0.137 | - | - | - | - | - |
| random at velocity_raw's fire rate | - | P=0.340 R=0.652 F1=0.447 fire=0.652 | - | - | - | - | - |

### k=3  (base rate train 0.446, test 0.446)
| trigger | theta (train maxF1) | TEST at that theta | theta (train maxP, R>=0.3) | TEST at that theta | AP test | AP train | oracle-test F1 |
|---|---|---|---|---|---|---|---|
| velocity_raw | 0.0000 | P=0.569 R=0.831 F1=0.675 fire=0.652 | 0.0052 | P=0.577 R=0.568 F1=0.573 fire=0.439 | 0.544 | 0.536 | 0.675 |
| velocity_pca_tangent | 0.0000 | P=0.569 R=0.831 F1=0.675 fire=0.652 | 0.0149 | P=0.576 R=0.412 F1=0.480 fire=0.319 | 0.540 | 0.538 | 0.675 |
| velocity_adaptive | 0.0000 | P=0.569 R=0.831 F1=0.675 fire=0.652 | 0.0162 | P=0.579 R=0.588 F1=0.584 fire=0.453 | 0.545 | 0.535 | 0.675 |
| velocity_raw | not_unresolved_now | 0.0000 | P=0.589 R=0.864 F1=0.701 fire=0.646 | 0.0017 | P=0.591 R=0.818 F1=0.686 fire=0.610 | 0.551 | 0.539 | 0.701 |
| velocity_adaptive | not_unresolved_now | 0.0000 | P=0.589 R=0.864 F1=0.701 fire=0.646 | 0.0091 | P=0.593 R=0.764 F1=0.668 fire=0.568 | 0.552 | 0.537 | 0.701 |
| high_tension_tick | 0.1000 | P=0.452 R=0.986 F1=0.620 fire=0.972 | 0.2100 | P=0.461 R=0.859 F1=0.600 fire=0.830 | 0.477 | 0.397 | 0.620 |
| always_fire | - | P=0.446 R=1.000 F1=0.617 fire=1.000 | - | - | - | - | - |
| not_unresolved_now | - | P=0.441 R=0.819 F1=0.573 fire=0.829 | - | - | - | - | - |
| row_t_is_non_idle | - | P=0.422 R=0.655 F1=0.514 fire=0.692 | - | - | - | - | - |
| idle_and_not_unresolved_now | - | P=0.534 R=0.164 F1=0.251 fire=0.137 | - | - | - | - | - |
| random at velocity_raw's fire rate | - | P=0.446 R=0.652 F1=0.530 fire=0.652 | - | - | - | - | - |

## Config `idle_only_subsequence (steps and onsets recomputed over idle rows alone)`
### k=1  (base rate train 0.227, test 0.267)
| trigger | theta (train maxF1) | TEST at that theta | theta (train maxP, R>=0.3) | TEST at that theta | AP test | AP train | oracle-test F1 |
|---|---|---|---|---|---|---|---|
| velocity_raw (idle-only subsequence) | 0.0000 | P=0.267 R=0.984 F1=0.420 fire=0.986 | 0.0000 | P=0.267 R=0.984 F1=0.420 fire=0.986 | 0.262 | 0.215 | 0.420 |
| velocity_pca (idle-only subsequence) | 0.0000 | P=0.267 R=0.984 F1=0.420 fire=0.986 | 0.0000 | P=0.267 R=0.984 F1=0.420 fire=0.986 | 0.258 | 0.218 | 0.420 |
| velocity_raw | not_unresolved (idle-only) | 0.0000 | P=0.602 R=0.984 F1=0.747 fire=0.983 | 0.0010 | P=0.602 R=0.983 F1=0.747 fire=0.983 | 0.607 | 0.640 | 0.747 |
| high_tension_tick (idle-only) | 0.0000 | P=0.268 R=0.991 F1=0.422 fire=0.987 | 0.0900 | P=0.268 R=0.991 F1=0.422 fire=0.987 | 0.267 | 0.226 | 0.422 |
| always_fire | - | P=0.267 R=1.000 F1=0.422 fire=1.000 | - | - | - | - | - |
| not_unresolved_now | - | P=0.601 R=1.000 F1=0.751 fire=0.445 | - | - | - | - | - |

### k=2  (base rate train 0.453, test 0.534)
| trigger | theta (train maxF1) | TEST at that theta | theta (train maxP, R>=0.3) | TEST at that theta | AP test | AP train | oracle-test F1 |
|---|---|---|---|---|---|---|---|
| velocity_raw (idle-only subsequence) | 0.0000 | P=0.535 R=0.986 F1=0.693 fire=0.986 | 0.0000 | P=0.535 R=0.986 F1=0.693 fire=0.986 | 0.530 | 0.430 | 0.693 |
| velocity_pca (idle-only subsequence) | 0.0000 | P=0.535 R=0.986 F1=0.693 fire=0.986 | 0.0000 | P=0.535 R=0.986 F1=0.693 fire=0.986 | 0.525 | 0.432 | 0.693 |
| velocity_raw | not_unresolved (idle-only) | 0.0000 | P=0.823 R=0.984 F1=0.896 fire=0.983 | 0.0000 | P=0.823 R=0.984 F1=0.896 fire=0.983 | 0.831 | 0.847 | 0.896 |
| high_tension_tick (idle-only) | 0.0000 | P=0.537 R=0.991 F1=0.696 fire=0.987 | 0.0900 | P=0.537 R=0.991 F1=0.696 fire=0.987 | 0.532 | 0.451 | 0.696 |
| always_fire | - | P=0.534 R=1.000 F1=0.697 fire=1.000 | - | - | - | - | - |
| not_unresolved_now | - | P=0.822 R=0.684 F1=0.746 fire=0.445 | - | - | - | - | - |

### k=3  (base rate train 0.628, test 0.724)
| trigger | theta (train maxF1) | TEST at that theta | theta (train maxP, R>=0.3) | TEST at that theta | AP test | AP train | oracle-test F1 |
|---|---|---|---|---|---|---|---|
| velocity_raw (idle-only subsequence) | 0.0000 | P=0.725 R=0.986 F1=0.836 fire=0.986 | 0.0000 | P=0.725 R=0.986 F1=0.836 fire=0.986 | 0.717 | 0.609 | 0.836 |
| velocity_pca (idle-only subsequence) | 0.0000 | P=0.725 R=0.986 F1=0.836 fire=0.986 | 0.0000 | P=0.725 R=0.986 F1=0.836 fire=0.986 | 0.715 | 0.611 | 0.836 |
| velocity_raw | not_unresolved (idle-only) | 0.0000 | P=0.912 R=0.983 F1=0.947 fire=0.983 | 0.0020 | P=0.912 R=0.902 F1=0.907 fire=0.902 | 0.911 | 0.924 | 0.947 |
| high_tension_tick (idle-only) | 0.0000 | P=0.727 R=0.991 F1=0.839 fire=0.987 | 0.0900 | P=0.727 R=0.991 F1=0.839 fire=0.987 | 0.717 | 0.624 | 0.839 |
| always_fire | - | P=0.724 R=1.000 F1=0.840 fire=1.000 | - | - | - | - | - |
| not_unresolved_now | - | P=0.911 R=0.559 F1=0.693 fire=0.445 | - | - | - | - | - |

