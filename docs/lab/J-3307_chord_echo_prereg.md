# J-3307 pre-registration: chord_echo replay, U1 stage 1

Written 2026-11-16 BEFORE any replay was run. Source design: docs/reviews/ghost_memory_index_chord_echo_J-3247.md section 4 (U1).
Read-only: `data/memory/nascence.db` opened `mode=ro`; scoring code is a copy of `core/ghost_tuples._tuple_tags` + `MemoryIndex.query` weights
(w = 1/ln(2+df), score = sum w(common) / (sqrt(|entry tags|)+0.001)). Script: `scripts/lab_chord_echo_J3307.py`. Outputs: docs/lab/J-3307_*.

## Data
Table `fragment_context` (carries source, valence, arousal, tuple_ts; the memory_fragments table has no source column).
Moments: `source LIKE 'experienced:%'` and valence not null. Time = `tuple_ts`.
Sample: 3,000 queries, seed 20261116. Arousal pass: the same sample restricted to rows with arousal not null; candidate pool also arousal-not-null.
Candidates for a query: every other moment (same outcome non-null) with |tuple_ts gap| >= 7 days. Post hoc variant (labelled so): gap >= 1 day.

## Arms (each predicts the query's OWN stored outcome; outcome never used in matching)
- a1 single-key weather (courier A): mean outcome of 24 random candidates sharing the query's weather (the expectation of the courier's random pick, variance reduced).
- a2 single-key sound (courier D): same with one randomly chosen sound key of the query (queries with no sound fall back to global mean).
- b  chord top-24, rarity-weighted, tags as `_tuple_tags` (place, weather, standpoint, tide band, warmth band, cat, sounds); candidates with the highest score; mean outcome. No tags or no pool: global mean.
- c  24 nearest in time among eligible candidates (mean outcome).
- null  the tag sets permuted across all rows (20 replicates), then arm b; null stat = mean MAE per replicate.
- e  global mean of eligible candidates.
Metric: absolute error |prediction - own outcome|, mean over queries (MAE).

## Pass bar (fixed now), required for BOTH valence and arousal at the 7-day gap
1. MAE(a1) - MAE(b) >= 0.02 and MAE(a2) - MAE(b) >= 0.02, each with paired bootstrap (2,000 resamples) 95% CI excluding 0 (stricter than the J-3247 text, which said "single-key"; the two courier keys are both tested).
2. MAE(b) < MAE(c).
3. z = (mean null-replicate MAE - MAE(b)) / sd(null-replicate MAEs) >= 3.
Any miss: chord_echo retired as a build (memory namespace per D-0669 / founder decision). Pass: do NOT build; write stage-2 judge-panel design (100 blind pairs, other model family) and file needs_input.
Also reported (no bearing on pass): MAE by place and weather class, coverage (share of sampled moments with at least one tag, and with a weather), MAE(e), correlation with truth, and the 1-day post hoc variant.
Expected from F-3898 (exploratory, 1-day gap): chord 0.325 vs single-key 0.289, global 0.288, so a fail.
