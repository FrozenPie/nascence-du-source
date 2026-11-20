# Strings and Sheets — Phase 0 ribbon lab results (2026-09-27)

Job J-1468. Script: `scripts/ribbon_lab.py`. Metric sheet (pre-registered before any number here was computed): `docs/lab/strings_sheets_ribbon_metric_sheet.md`.

**One-piece limitation, stated plainly:** exactly one real recording exists anywhere in this repo — `data/music/Heavyweight.mp3`. The other five `data/music/*.features.json` files are audio-less shells with no `sections` (core/listening.py's `shelf()` docstring). P5 and any per-piece generalisation claim are therefore reported as **untestable with one piece**, not extrapolated from n=1. This script accepts `--audio PATH [PATH ...]` and will run unchanged on more pieces the moment real recordings arrive.

## Verdicts

- **P1 — MET.** Heavyweight 3-axis width mean in 0.25-0.35 and twist mean in 50-75 deg/s (reproduction check of F-2017: 0.294 / 62.7 deg/s)
  - {'width3_mean': 0.295, 'twist3_mean': 62.4}
- **P2 — MET.** 6-axis width >= 3-axis width every second (true by construction; sanity check)
  - {'note': 'sanity check, not a real prediction'}
- **P3 — MET.** closing 3 sections wider (6-axis width) than opening 3 sections
  - {'first3_mean': 0.314, 'last3_mean': 0.588}
- **P4 — MET.** felt(i) exactly one valence value across sections; felt(ii) (per-section key estimate) varies valence in >=3 sections
  - {'felt_i_distinct_values': [0.042], 'felt_ii_distinct_values': [-0.08, -0.064, -0.052, -0.037, -0.033, -0.025, 0.037, 0.038, 0.041, 0.043, 0.044, 0.045, 0.05, 0.072, 0.08, 0.088, 0.089, 0.1]}
- **P5 — UNTESTABLE (one piece).** additional piece(s): 6-axis width mean in 0.15-0.45 and twist mean > 30 deg/s
  - {'note': 'only one real recording exists in this repo as of 2026-09-27; cannot be tested this run'}

## Kill-rule check (run before any number below was read)

Per-section MEAN of the measured per-second string vs the cached section value, on the three cached axes, tolerance 0.02 (normalised units):

| piece | energy dev | brightness dev | onset dev | kill triggered |
|---|---|---|---|---|
| Heavyweight | 0.0000 | 0.0000 | 0.0006 | no |

## Per-piece summary

| piece | sections | seconds | width3 mean | width3 p90 | width6 mean | width6 p90 | twist3 mean deg/s | twist6 mean deg/s | source |
|---|---|---|---|---|---|---|---|---|---|
| Heavyweight | 21 | 521 | 0.295 | 0.569 | 0.323 | 0.599 | 62.4 | 61.1 | cache |

### Heavyweight — per-section table

SVG: `docs\lab\strings_sheets_ribbon_Heavyweight.svg`

| section | start_s | width3 mean | width6 mean | twist6 total deg | felt(i) valence | felt(i) arousal | felt(ii) valence | felt(ii) arousal |
|---|---|---|---|---|---|---|---|---|
| 0 | 0.0 | 0.481 | 0.527 | 2002.7 | 0.042 | 0.102 | 0.08 | 0.102 |
| 1 | 40.5 | 0.197 | 0.211 | 1101.7 | 0.042 | 0.104 | 0.088 | 0.104 |
| 2 | 52.2 | 0.183 | 0.203 | 4561.8 | 0.042 | 0.099 | 0.089 | 0.099 |
| 3 | 110.2 | 0.192 | 0.218 | 4329.7 | 0.042 | 0.103 | 0.038 | 0.103 |
| 4 | 158.0 | 0.149 | 0.161 | 979.5 | 0.042 | 0.103 | 0.043 | 0.103 |
| 5 | 172.1 | 0.207 | 0.226 | 761.6 | 0.042 | 0.1 | 0.037 | 0.1 |
| 6 | 182.4 | 0.361 | 0.422 | 2408.2 | 0.042 | 0.095 | -0.025 | 0.095 |
| 7 | 244.3 | 0.339 | 0.360 | 1528.3 | 0.042 | 0.106 | 0.05 | 0.106 |
| 8 | 260.9 | 0.113 | 0.123 | 1015.3 | 0.042 | 0.108 | -0.033 | 0.108 |
| 9 | 271.1 | 0.369 | 0.383 | 350.9 | 0.042 | 0.096 | -0.064 | 0.096 |
| 10 | 278.9 | 0.438 | 0.458 | 1772.1 | 0.042 | 0.095 | 0.044 | 0.095 |
| 11 | 360.4 | 0.239 | 0.271 | 506.6 | 0.042 | 0.09 | -0.08 | 0.09 |
| 12 | 371.6 | 0.157 | 0.168 | 875.1 | 0.042 | 0.099 | 0.041 | 0.099 |
| 13 | 380.8 | 0.182 | 0.206 | 4297.0 | 0.042 | 0.101 | 0.045 | 0.101 |
| 14 | 445.7 | 0.180 | 0.207 | 819.9 | 0.042 | 0.1 | -0.037 | 0.1 |
| 15 | 456.4 | 0.163 | 0.174 | 937.3 | 0.042 | 0.1 | 0.1 | 0.1 |
| 16 | 466.7 | 0.134 | 0.140 | 1140.0 | 0.042 | 0.096 | 0.072 | 0.096 |
| 17 | 476.9 | 0.185 | 0.191 | 1081.2 | 0.042 | 0.098 | 0.1 | 0.098 |
| 18 | 490.5 | 0.513 | 0.525 | 435.4 | 0.042 | 0.103 | 0.1 | 0.103 |
| 19 | 500.8 | 0.441 | 0.486 | 414.0 | 0.042 | 0.114 | 0.1 | 0.114 |
| 20 | 510.0 | 0.661 | 0.753 | 465.5 | 0.042 | 0.111 | -0.052 | 0.111 |

## Anything unexpected

**The kill rule fired on the first run of this script, exactly as pre-registered — and it was right to.**
The first cut compared the cached section value to an *unweighted* mean of the already-1-second-quantised
measured string, grouped by which second's midpoint fell in the section. That produced a max onset
deviation of **0.54** (normalised) — the kill rule refused to write results, as designed. Two real, distinct
causes were found and fixed, in order:

1. `n_sec = int(len(energy_f) / fps)` silently floor-truncated the piece's final ~0.8 s, dropping those
   frames from every per-second string (not onset-specific — this alone cost brightness ~0.043 of its
   0.049 deviation). Fixed to `math.ceil(...)`.
2. The onset axis's per-second "density" is a frame-exceedance-count divided by a ~1 s duration — a rate,
   not a plain mean. Section 20 (a quiet fade-out with one short loud burst right at its start) has a
   burst concentrated entirely in its first 3 seconds: raw per-second values of 42, 14 and 15 events/s
   against a section-wide rate of 6.48/s. An *unweighted* mean of the per-second string, once each
   value is normalised and clipped to the ribbon's 0..1 range (`min(1, d/8)`), saturates at 1.0 for
   all three burst seconds and swamps the mean — 0.51 of the total 0.54 deviation came from this one
   section. This is a real algebraic mismatch (mean-of-ratios over unequal/short windows ≠ the section's
   own total-count/total-duration), not a reading of a genuine ribbon width — the width the ribbon
   itself reports for section 20 (0.661 three-axis) is unaffected and is treated as real.

The fix that actually closed both gaps to near-zero (final max deviation **0.0006**, energy and
brightness both under 1e-5) was to stop reconstructing the per-section check from the already-quantised
per-second string at all, and instead recompute each cached axis directly over the section's own true
frame range `[fa, fb)` — `extract()`'s exact formula (`seg.mean()` for energy/brightness,
total-exceed-count/total-duration for onset) applied to our own `energy_f` / `centroid_f` / `onset_f`
arrays. This isolates the real question the kill rule exists to ask — are the per-frame primitives and
the section-aggregation rule identical to `extract()`'s own (F-2017's original bug: summed magnitude
instead of RMS, a global instead of per-section onset threshold) — from a separate, expected artifact of
representing a continuous string at 1-second resolution across a section boundary that doesn't land on a
whole second. The **per-second string used for the ribbon itself was never changed** by this fix; only
the *validation* method was corrected. Two intermediate attempts (frame-count-weighted reconstruction of
the per-second string, and per-frame instead of per-second-bin threshold assignment) each closed part of
the gap (down to 0.034) but left short sections (8–17 s long) over tolerance — worth recording in case a
future piece's shorter sections hit the same residual.

**`felt()` per section, (ii) vs (i):** as predicted, (i) (mode/key held piece-level) gives exactly one
valence value (0.042) across all 21 sections — Heavyweight's felt affect is a flat line today, confirming
F-2017. (ii) (a per-section key/mode estimate via `af._key(af._chroma(mag[fa:fb]))`) gives valence 18
distinct values across the piece, including a mode flip to minor (negative valence, e.g. -0.08 in section
11, -0.064 in section 9) in several sections whose local chroma correlates better with a minor tonal
profile than the piece-level major key (C, key_confidence 0.03 — a very weak piece-level estimate to
begin with, so per-section disagreement is not surprising). This is the first time this piece's affect
string has shown any contour at all; it remains shadow/observational per the plan's own guard (§7,
§8 "not affect going live") — nothing here changes runtime behaviour.

**Section 0's twist total (2002.7°) and section 2's (4561.8°)** are large mainly because they are long
sections (40 and 58 seconds) accumulating many small twist increments, not because any single second's
rotation is extreme — `twist6` per-second values (see the JSON) stay in a normal range throughout; the
per-section *total* in the results table sums twist over all seconds in that section and should be read
as "section length x average local twist", not compared directly against a short section's total.
