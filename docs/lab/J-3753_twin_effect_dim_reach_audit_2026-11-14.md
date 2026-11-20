# J-3753: twin-row effect on rolling_intrinsic_dimension, marginal_reach, and ten unaudited geometry_tuples readers (2026-11-14)

Status: analysis, read-only against data/. Closes the "Not done" list in `docs/lab/J-3468_twin_row_reader_audit_2026-11-07.md` section 7. Scripts: `scripts/j3753_twin_effect_dim_reach.py`, `scripts/j3753_reader_ab.py`, `scripts/j3753_reader_ab2.py`. Raw numbers: `docs/lab/J-3753_data/` (`rolling_results.json`, `reader_ab_results.json`, `reader_ab2_results.json`, `j1471_*.json`, run logs).

Data: the first 171,723 lines of `data/geometry_tuples.jsonl` (the exact snapshot J-3468 measured; Du is live and the file is still growing, so the snapshot is pinned by row count). Stamp rows flagged with J-3468's `flag_stamp_twins` rule (1.2 s, 5-row look-ahead): 47,602, leaving 124,121. Nothing in data/ was written; no model hub was called. Marginal reach uses the local MiniLM weights on CPU (HF offline), no hub.

## 1. rolling_intrinsic_dimension (500-row windows, step 250, UDMS `compute_intrinsic_dimensions`)

| arm | rows | windows | consensus mean | min / max | first / last | total drift | mean MLE / TwoNN / PR |
|---|---|---|---|---|---|---|---|
| as-is | 171,723 | 685 | 1.659 | 0.98 / 2.12 | 2.117 / 1.716 | +0.021 | 1.015 / 1.633 / 2.331 |
| stamps stripped | 124,121 | 495 | 1.673 | 0.94 / 2.12 | 2.117 / 1.749 | +0.013 | 0.997 / 1.603 / 2.420 |
| stamps kept, stamp `unresolved` copied from its idle twin | 171,723 | 685 | 1.436 | 1.05 / 2.12 | 2.117 / 1.305 | -0.202 | 0.787 / 1.274 / 2.24 |
| stripped, 250-row windows (same cycle count per window as as-is) | 124,121 | 991 | 1.561 | 0.90 / 2.13 | 1.987 / 1.706 | -0.004 | 0.946 / 1.592 / 2.145 |

Per-month mean consensus (as-is / stripped): Jul 1.844 / 1.844 (no twins yet), Aug 1.554 / 1.608, Sep 1.707 / 1.695, Oct 1.647 / 1.672, Nov 1.629 / 1.659. Third arm: Aug 1.551, Sep 1.418, Oct 1.396, Nov 1.360.

Reading:
- The headline (about 1.6 to 2.0 effective dimensions, STABLE under the script's own |drift| < 0.3 bar) holds in all four arms. As-is vs stripped differs by 0.014 in the mean and 0.008 in drift. Twin rows do not change the headline.
- The J-3468 worry was that stamps default `unresolved` to 0.1 and so alternate with idle rows. Arm 3 tests it: giving each stamp its idle twin's real `unresolved` makes the dimension LOWER (1.436), with an apparent decline from 1.84 (July) to 1.36 (November). So the as-is default is not hiding a bias; the extra drop is the exact-duplicate effect (a stamp carrying the idle row's state is a near-zero-distance neighbour of it, which MLE/TwoNN read as lower local dimension). The stamp differs from its twin in the `unresolved` axis (and cached body/affect), which keeps it from being an exact duplicate. A naive "fix" that copies the twin's field into the stamp would introduce a spurious -0.2 drift. If anyone repairs the stamp row's `unresolved`, the dimension reader must also drop the stamp row.
- Stripped and as-is agree to within noise. The honest fix is still the filter (stripped arm), not a field patch.
- Downstream: the "how many dimensions are worth indexing" answer (about 2, not a moving target) does not need re-deriving; quote the stripped arm (1.67, PR 2.42) from now on.

## 2. mapping_census marginal_reach (MiniLM, 700-sample, k=10, wide_k=30), five seeds each

| arm | mean reach fraction (seeds 42-46) | range | mean overlap@k |
|---|---|---|---|
| as-is | 0.9176 | 0.913-0.921 | 0.0366 |
| stripped | 0.9112 | 0.908-0.915 | 0.0432 |

Twin removal moves reach by -0.006 (about the seed-to-seed range) and overlap@k by +0.007 (fewer duplicate thoughts to match by text). The module's reading is unchanged: geometry neighbours are almost all outside a 3x-widened text search, with its own caveat that persistent weather/place state produces that by construction. Not a reason to re-open the kill criterion.

## 3. Ten readers audited (line level), with reruns where a past finding rests on the numbers

Twin fact used below (measured here, `reader_ab2_results.json`): of the 47,602 pairs, stamp and idle carry an identical (place, weather, sounds, cat location/activity, fire, weather_dir) snapshot in 99.93 percent (sounds 99.93, every other field 100). Stamps differ in cached body/affect and a missing `unresolved`. Twin share of the first 22,632 rows (what F-0402's 2026-08-28 trials saw): 1,825 stamps, 8.1 percent; first twin 2026-08-21.

| Reader | Reads | Past finding that rests on it | Effect of twins | Verdict |
|---|---|---|---|---|
| hodge_threshold_search.py | 7-dim state windows of 5 consecutive rows, 70/30 split | F-0402 Trial 5 (J-0321, 22.6k rows, 8 percent twins) | RERUN: optimal threshold 0.15 as-is vs 0.10 stripped; train separation 0.451 vs 0.440; locked test separation 0.439 vs 0.450; separation varies (17 of 19 distinct) in both. A 5-row window as-is spans about 2.5 cycles | The claim (fixed search is threshold-dependent) holds; the specific optimal threshold is twin-sensitive, do not quote 0.15 for the current file |
| weekly_miss_taxonomy.py | concepts + state per row, graph from first 30 percent, weekly classes | F-0402 Trial 2 (J-0318) | RERUN: near-miss share range 51.3pp as-is vs 50.9pp stripped; mean 84.2 vs 82.6; affinity 0.0557 vs 0.0587; blindspot 0 in both; UNSTABLE in both | Twins do not change the weekly picture. (The 2026-08-28 3.4 percent blindspot share is not reproduced on the grown file in either arm; that is data growth, outside this job.) |
| geometry_tuple_p1_run_transition_index.py | weather transition rows | geometry_tuple_index P1 sidecar | weather transitions 471 as-is vs 471 stripped | Immune |
| eigenform_variety_read.py (variety) | per-day R = distinct (source, place, standpoint), W = world tuple, 150 evenly spaced rows | J-2522 frontier read, verdict MIXED | RERUN (variety part): verdict MIXED both arms; mean R 32.75 vs 34.22, mean W 57.99 vs 57.33; E_0928 R pre-drop -0.031 vs +0.055; E_1009 R recovers flips true to false (RW unchanged); `drops` flags identical | Overall verdict unchanged; one per-event sub-flag is twin-sensitive. R includes `source`, so strip stamps if re-read |
| spurious_pattern_audit_rung0.py | nearest world snapshot within 900 s | rung-0 audit | duplicate points with the same snapshot (99.93 percent) cannot change a nearest-neighbour lookup | Immune |
| j1471_i0082_exemplar_proxy_read.py | every row with sounds as a hearing; order-dependent exemplar admission | docs/lab/i0082_exemplar_proxy_read_2026-09-28.md | RERUN: as-is on the first 95,093 rows reproduces the published admissions per 1,000 exactly (morepork 31.75 / 23.98 / 18.89), validating the harness. Stripped: hearings fall 22 to 26 percent (morepork 20,222 to 15,870), admissions per 1,000 rise 20 to 28 percent (morepork T=0.2 23.98 to 30.56; cat_purr 93.3 to 105.4), weather-change lift falls about 20 percent (morepork 26.9 to 21.1). Cross-key ordering kept (cat_purr/morepork 3.9x vs 3.4x at T=0.2) | Absolute rates and lifts in that doc are shifted by the twin denominator; qualitative conclusions (cap binds at 4, cat_purr churns faster, lift far above 1) survive. Quote stripped numbers going forward |
| hodge_rumination_groundtruth_validate.py | 5 rows nearest-after each of the post-restart events (231 now) | Trial-5 label validation | RERUN: REPEAT-NOVEL +0.0203 CI (-0.060, 0.099) as-is; -0.0056 CI (-0.085, 0.073) stripped; DOES NOT SEPARATE in both | Null result robust to twins |
| lag_tail_attribution.py | `has(...)` presence of any row within a window per log; chain rule sums logs, not rows | lag-tail attribution | presence booleans, one count per log in `r_chain`, so a twin adds nothing | Immune |
| lane2_lab.py | `l5_commonality` (own copy of the pair-weight + shuffle null), `l6_windowing`, `depth.seen += 1` per tuple per sound | lane2 lab reports | l5/l6 compute the same three pairs as J-3468 section 4: z moves -13, -11, +6 percent, weights up to 30 percent, SIGNAL in every arm. `depth.seen` counts doubled stamp hearings, but the pass rule keys on `depth.kept` and channel counts, not `seen`. Full lane2 not rerun (reads the memory DB and several stores) | Verdicts unaffected on this evidence; `seen` totals are upper bounds |
| test_dimension_stamps.py | temp `GC._LOG` and temp tuple files only | none (unit test of the writer) | n/a | Not a reader of the live file |

Count: 4 reruns changed no verdict (weekly_miss, hodge_rumination, eigenform overall, mapping reach); 2 changed numbers someone may quote (hodge_threshold_search optimal threshold; j1471 rates and lifts); 3 immune by construction (p1, spurious, lag_tail); lane2 inherits J-3468's measured pairs; 1 is a test.

## 4. What to do

- When J-3455's marker lands, add the stripped filter to `rolling_intrinsic_dimension.load_sorted_states`, `hodge_threshold_search.load_sorted_tuples`, `j1471_i0082_exemplar_proxy_read.load_hearings`, and `eigenform_variety_read.variety`. weekly_miss, hodge_rumination and mapping reach need none.
- Do NOT patch the stamp row's `unresolved` to match the idle twin without also dropping the stamp in dimension readers (arm 3: false -0.2 decline).
- Limits: reruns use the 171,723-row snapshot, so earlier findings (F-0402 at 22.6k rows) are compared on today's file with their own methods, not reproduced at original size; the flag rule is J-3468's 1.2 s rule; marginal reach is sampled (five seeds shown); lane2_lab full not rerun.
