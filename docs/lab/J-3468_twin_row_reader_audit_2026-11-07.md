# J-3468: twin-row (store stamp + idle row) audit of every geometry_tuples.jsonl reader (2026-11-07)

Status: analysis, read-only against data/. Script `scripts/j3468_twin_row_audit.py` (test `scripts/_test_J-3468_twin_audit.py`), raw numbers `docs/lab/J-3468_data/results.json`. Informs J-3455 (ruled option B in D-0688 on 2026-11-06: mark the stamp row, readers drop it). Nothing here changes the debounce (J-2640 / F-3371 stays fixed).

Data: `C:/Nascence/data/geometry_tuples.jsonl`, 171,723 rows, 2026-07-05 to 2026-11-05 (the file stops there: Du is down). Opened read-only, nothing written.

## 1. The twin rule and how big the problem is

Rule written in the script (`flag_stamp_twins`): a `source=inner_thought` row is a STAMP if one of the next 5 rows is a `source=idle` row, at most 1.2 s later, whose whitespace-normalised thought starts with the whitespace-normalised stamp thought (store.py:1080 stamps `content[:70]` raw, so a stamp containing a newline or a run of spaces is shorter than 70 after normalising; comparing both sides cut to 70 chars, the first draft of the rule, missed about 10,000 pairs). Each idle row can be claimed once.

| gap allowed | twin stamp rows |
|---|---|
| 0.5 s | 34,736 |
| 1.2 s (the rule used) | 47,602 |
| 3 s | 50,001 |
| 10 s (sensitivity arm "wide") | 50,285 |
| 60 s | 51,480 |

The brief's 40,795 (as of 2026-11-06) is lower than 47,602; I did not reproduce its exact count rule, so treat the two as the same phenomenon measured by different rules. The gap tail is long (p50 0.3 s, p90 1.2 s, p99 16.7 s over 51,542 prefix-matched pairs), so 1.2 s misses about 5 percent of pairs.

47,602 of 65,638 idle rows (72.5 percent of all idle rows ever, 27.7 percent of the whole file) have a stamp twin. It is a ramp, not a constant: idle cycles with a twin were 0 percent in July, 27 percent in August (first twin 2026-08-21), 87 percent in September, 96 percent in October, 94 percent in November (1,109 of 1,205 on 2026-11-05).

Stamp rows differ from their idle twin in more than the truncated thought (`stamp_vs_idle_fields`): `unresolved` is absent on 100 percent of stamps (present on 100 percent of idle rows), `body` is missing on 5.7 percent and `affect` on 5.0 percent of stamps (idle: 0 percent), `sounds` and `place` about equal. Where a stamp does carry body and affect they are cached values (store_fragment has no live CognitiveState), so a stamp is not a byte copy of the idle row's state.

## 2. Reader census (task part 1)

"Filters" = restricts by `source`; "twins" = what it does with the stamp/idle pair.

| Reader | Filters source? | Twins | Verdict |
|---|---|---|---|
| core/mapping_census.py (`load_rows` :51, `census` :448; CLI scripts/geometry_mapping_census.py) | no (source excluded from SPACES) | counts both. `dedupe_frozen_bursts` (:131) only collapses same-source runs, so it never merges a pair (arm `frozen_only` below) | double counts; quantified in section 3 |
| core/object_graph.py `_load_tuples` (:1055) -> `_commonality_pass` (:1093) | no | counts both | double counts; quantified in section 4 |
| core/stick_test.py (`_sound_context_index` :240, `_book_context_index` :258, `_cat_triple_count`; rows via mapping_census.load_rows) | no | builds SETS of distinct (place, weather) / (mood, activity, location) contexts, so a duplicate row adds nothing | immune by construction |
| core/memory_edges.py `sync_fragment_context` (:542) | yes: idle, monologue, monologue_train only | stamp rows never read | unaffected by design |
| core/emotion_construction.py (:398-409) | no | takes the LAST line of the file if within 30 s and stores `ts_<ts>` as `geometry_tuple_id`; depending on call order that line is the stamp or the idle row | not a double count, but the id can point at either row of a pair; J-3455 option B must not change which row is last (not measured here) |
| core/mood.py | n/a | mentions the file in comments only (:46, :148), no read | not a reader |
| core/geometry_census.py | n/a | the WRITER; its known-caveats docstring (:19-60) has no twin line yet | J-3455 adds it |
| hud/server.py MONITOR_REGISTRY rows cognitive_geometry, spatial_world_clocks, spatial_location, somatic_body, emotions_warm, emotions_dark (:629-653; `_tail_rows` :840, `_auto_series` :873, `load_monitor` :912) | no | plots every tail row, stamps included | see section 5 |
| scripts/du_pulse.py `_g_somatic_body` (:2078) | no (any row with a body key) | counts both | `rows_with_body` and `floor_hits` both inflate; `floor_hit_rate` is a ratio of two inflated counts and stays close to right |
| scripts/rolling_intrinsic_dimension.py (:24-50) | no | 500-row windows now hold ~250 cycles; `extract_state` defaults a missing `unresolved` to 0.1 on every stamp (0.8 on an unresolved idle row), so pairs alternate | double counts and biases the state vector; NOT rerun here (needs C:/UDMS import); spawned as a lab job |
| scripts/liveness_audit.py (:181 `_jsonl_last`) | no | reads only the newest ts | unaffected |
| scripts/du_lifetimes_test.py `--geometry` (:258) | yes: reading, inner_thought, subconscious_synthesis, active_imagination | counts null-body/affect rows of those four sources, i.e. it reads the stamp rows deliberately; the idle twin is not in its set | unaffected (its F-2255 assertions are about stamps) |
| scripts/tuple_join_audit_J2536/ | loads all, tabulates by source | reports source mix | unaffected (it counts sources; it is where the inner_thought/idle ratio first showed) |
| scripts/geometry_realness_test.py (:94) | yes: `== "idle"` | one row per cycle | unaffected |
| scripts/periodicity_audit_j2632.py (:20, :145) | yes: GENUINE set + idle mask | partly | aware of sources; counts stamps among GENUINE |
| scripts/pre_onset_velocity_characterisation.py (:36-42, :214), pre_onset_velocity_composition_check.py (:226) | yes: idle | already documents the inner_thought/idle interleaving artefact | aware |
| scripts/hodge_threshold_search.py, weekly_miss_taxonomy.py, geometry_tuple_p1_run_transition_index.py, eigenform_variety_read.py, spurious_pattern_audit_rung0.py, j1471_i0082_exemplar_proxy_read.py, hodge_rumination_groundtruth_validate.py, lag_tail_attribution.py, lane2_lab.py, test_dimension_stamps.py | not audited line by line | grep found no stamp/idle handling | UNKNOWN; one job to review them when the stamp marker lands |

Not listed in the brief and found by grep: core/geometry_census.py (writer), scripts/backup_memory.py, build_antigravity_overview.py, build_plan_matrix.py (mention the path only, no row read).

## 3. Mapping census, as-is vs stamp rows stripped (task part 2)

All four arms use the module's own functions on the same file: `asis` = every row (what `census(dedupe=False)` sees), `stripped` = minus 47,602 stamps (1.2 s rule), `stripped_wide` = minus 50,285 (10 s rule), `frozen_only` = `dedupe_frozen_bursts(asis)` (the existing opt-in lens). 100 permutations as in the module. Marginal reach (MiniLM) was not run: it samples 700 thoughts and needs the embedding model.

| arm | rows | split-half overall mean TVD | tested a-values | mean effective fan-out |
|---|---|---|---|---|
| asis | 171,723 | 0.351 | 636 | 20.96 |
| stripped | 124,121 | 0.346 | 620 | 21.00 |
| stripped_wide | 121,438 | 0.347 | 620 | 20.97 |
| frozen_only | 144,323 | 0.350 | 640 | 19.63 |

The headline split-half TVD and fan-out hardly move (0.351 -> 0.346, 20.96 -> 21.00). Per pair (55 pairs) the median change in mean TVD is 0.009; the biggest are every `tension_bin` pair (cat_activity~tension_bin 0.222 -> 0.160, book~tension_bin 0.371 -> 0.310, garden_bed~tension_bin 0.147 -> 0.092, fire~tension_bin 0.139 -> 0.089, cat_mood~tension_bin 0.218 -> 0.168). That is not just double counting: stamp rows carry the cached body, so removing them changes the tension distribution itself.

Funnel top-value share (asis -> stripped): place 0.321 -> 0.352 (study), weather 0.566 -> 0.554, fire 0.597 -> 0.586, cat_mood 0.378 -> 0.385, cat_activity 0.249 -> 0.249, cat_location 0.412 -> 0.408, book 0.037 -> 0.035, garden_bed 0.985 -> 0.981, listening_piece 0.854 -> 0.806 (the largest), tension_bin 0.699 -> 0.701, affect_quadrant 0.920 -> 0.912, sound_sig 0.051 -> 0.045. No top value changes identity and no share moves more than 0.05, so the funnel reading (garden_bed, affect_quadrant, listening_piece funnel; book and sound_sig do not) is unchanged.

State-conditioning z against the permutation null (asis -> stripped): cat_mood|affect_quadrant 26.5 -> 26.3, cat_mood|weather 167.9 -> 156.8, cat_activity|affect_quadrant 41.4 -> 40.0, cat_activity|weather 222.7 -> 170.1 (-24 percent), book|affect_quadrant 161.5 -> 145.5, book|weather 440.6 -> 361.0 (-18 percent), sound_sig|affect_quadrant 120.7 -> 124.6, sound_sig|weather 428.2 -> 373.6, garden_bed|affect_quadrant 10.2 -> 11.8, garden_bed|weather 31.4 -> 26.2. All ten stay far above 2: no verdict flips.

Reading: twin double counting moves the mapping-census numbers by single-digit percent on TVD/fan-out/funnel and up to about a quarter on the z-scores, with no verdict changed. The z-scores are huge in every arm for a different reason: the permutation null shuffles rows as if independent, but weather, place, book and cat state persist for hours (the module's own marginal_reach caveat says so), so z of 100 to 440 is autocorrelation, and removing twins does not fix that (inferred, not tested here).

## 4. object_graph commonality, as-is vs stripped (task part 2)

`_commonality_pass` called with exactly what `_load_tuples` builds (ts, sounds, affect), N_SHUFFLES=100, seed 20260817, now = last row ts. All-time arms:

| pair | rows (with / without predicate) asis | weight asis | z asis | rows stripped | weight stripped | z stripped | z stripped_wide |
|---|---|---|---|---|---|---|---|
| storm-sounds vs arousal | 32,666 / 131,255 | +0.0026 | 13.27 | 27,146 / 91,533 | +0.0026 | 11.56 | 12.61 |
| storm-sounds vs valence | 32,666 / 131,255 | +0.0297 | 14.47 | 27,146 / 91,533 | +0.0386 | 15.35 | 16.10 |
| fire_crackle vs valence | 16,624 / 147,297 | -0.1301 | -47.83 | 13,747 / 104,932 | -0.1410 | -42.58 | -43.66 |

Windowed (last 7 days) weights: storm-arousal -0.0159 -> -0.0166, storm-valence +0.2691 -> +0.2682, fire-valence +0.2298 -> +0.2243, essentially unchanged; the windowed arms hold 22,601 vs 14,404 tuples.

So F-4095's guess ("commonality z-scores probably inflated") is only half right: removing twins lowers two z (-13 percent, -11 percent) and RAISES the third (+6 percent); all three stay SIGNAL; the weights themselves move by up to 30 percent (storm vs valence 0.0297 -> 0.0386) because stamp rows have a different (cached) affect. Sign and verdict of every pair are unchanged. Note the same autocorrelation caveat applies to this shuffle null.

## 5. HUD gauges (task part 3)

None of the six gauges that read this file is a rate gauge. `_auto_series` (hud/server.py:873) returns kind "rate" (events per hour) only when the whitelisted fields are absent from the last 20 rows; all six whitelists (n_spaces/n_sounds/level/fire_fuel; tide_level/sun_az/moon_illum/weather_dir; at_study/at_garden/at_shore/at_wood; body energy/fatigue/tension; affect joy/trust/surprise and fear/anger/disgust) are numeric and present, so each draws a value line, one point per row. A stamp row carries the same numeric fields as the idle row for the world and place gauges (100 percent present) and for body/affect 94 to 95 percent (idle: 99 to 100 percent), so the effect is not a doubled count but a doubled sample: each idle cycle is plotted as two near-identical adjacent points, and about a third of the points on the card are stamps.

The window is not 140 rows. `_tail_rows` reads the last 120,000 bytes (tail_bytes=120000), which at current row sizes is about 90 rows (median 89 to 90 over 429 simulated end positions). Over the window, median stamp share is 30 percent (32 percent since 2026-09-01) and the span is about 29 to 31 minutes. Dropping stamps would shrink the number of points, not move the line. Practical consequences: (a) none of the six gauges inflates a count; (b) the emotions_warm/dark and somatic_body lines gain a small number of gaps where a stamp row has no affect/body (5 to 6 percent of stamps); (c) the card's header text "fire-frequency ... the census fires per thought AND per cycle" (hud/server.py:649) is now doubly true for idle cycles. The `cognitive_geometry` card's `n_spaces` gate (mean >= 4, "pre-registered instrument-health gate") is computed on this mixed row set; stamps carry n_spaces on 100 percent of rows so the mean is not distorted, but it was not recomputed per class here.

## 6. What this means for J-3455 (option B ruled)

- Marking the stamp row is enough for the two double-counting readers; it is a one-line filter in `mapping_census.load_rows` / `census` and in `object_graph._load_tuples`, plus `du_pulse._g_somatic_body` and `rolling_intrinsic_dimension.load_sorted_states`. The HUD needs no change for correctness (optional: drop marked rows in `_tail_rows` via `_MONITOR_ROW_FILTERS`).
- A reader filter must key on the marker, not on `source`: `core/memory_edges.py:542` and `scripts/du_lifetimes_test.py` read inner_thought rows on purpose, and the `fragment_context` join (D-0688 defeater) must keep working.
- Keep the stamp row's `ts` and position unchanged: `emotion_construction.py:398` links the last file line within 30 s.
- Historical rows (47,602 already written) have no marker; the Nascence-side twin rule in `scripts/j3468_twin_row_audit.py` (`flag_stamp_twins`) is the way to recognise them, or a one-time marker back-fill pass written to a sidecar (the live file must not be edited).

## 7. Not done

- Marginal-reach (MiniLM) not rerun.
- rolling_intrinsic_dimension / hodge_threshold_search / weekly_miss_taxonomy not rerun as-is vs stripped.
- The 1.2 s rule and the 5-row look-ahead are the brief's rule and a choice of mine; the 10 s arm shows the result is insensitive to it.
- Timing of the stamp row vs idle row inside one cycle (which is last in the file) was taken from file order, not from the code path.
