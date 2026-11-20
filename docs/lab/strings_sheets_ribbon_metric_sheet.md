# Strings and Sheets — Phase 0 ribbon lab: pre-registered metric sheet

Written 2026-09-27, BEFORE any number in this run is computed (this project's pre-registration law).
Job J-1468. Plan: `docs/staged/strings_and_sheets.md` §3 Object C, §5 Phase 0 row, §10's three scoping
requirements. Reproduces and extends the scratchpad demonstration F-2017
(`ribbon_heavyweight.py`/`.json`/`.svg`) into `scripts/ribbon_lab.py`.

**Material available at the time this sheet is written:** exactly ONE real recording exists anywhere
in this repo — `data/music/Heavyweight.mp3` (duration 521.0 s, 21 cached sections). The plan's §5
Phase 0 row says "all six cached pieces"; a real check (this job's briefing) found the other five
`data/music/*.features.json` files are audio-less shells with no `sections` key and no source audio
(`core/listening.py`'s `shelf()` docstring: "their source audio is gone"). So this run is Heavyweight
only. `scripts/ribbon_lab.py` takes `--audio PATH [PATH ...]` so any future recording is processed by
the identical pipeline (computing sections on the fly via `audio_features.extract()` if no cache
exists) the instant it appears, without rewriting this sheet or the script.

## (a) Axis definitions — pinned verbatim

All six axes are computed from `core.audio_features`'s own STFT: `SR=22050, HOP=512, WIN=2048`,
`mag = af._stft_mag(y)`.

- **energy**: per frame `sqrt(mean(mag**2))` — identical to `extract()`.
- **brightness**: per frame spectral centroid `(mag*freqs).sum/mag.sum` — identical to `extract()`.
- **onset**: per second, count of frames whose onset envelope (`af._onset_env(mag)`) exceeds (the
  containing section's mean + std of that envelope), divided by the second's duration — `extract()`'s
  own section rule applied per second, so per-section means match the cache by construction.
- **periodicity** (NEW): per second, take a centered 4 s window of the onset envelope, subtract its
  mean, compute its normalised autocorrelation, and report the maximum autocorrelation at lags
  between 0.1 s and 2.0 s, clipped to 0..1. Clockwork = 1, irregular = 0.
- **roughness** (NEW): per frame spectral flatness = geometric mean / arithmetic mean of the
  magnitude spectrum over bins 100–8000 Hz (add 1e-12 inside the log), averaged per second, clipped
  0..1. Pure tone → 0, noise → 1.
- **continuity** (NEW): per second, fraction of that second's frames whose energy ≥ 0.1 × the maximum
  frame energy within a centered 5 s window. Continuous = 1, intermittent = 0.

## (b) Normalisation

- `energy` → `energy / max(section energy of the piece)` (i.e. `emax_sec` from the cache, matching
  F-2017's own `norm()`).
- `brightness_hz` → `brightness_hz / 4800.0`.
- `onset_density` → `onset_density / 8.0`.
- `periodicity`, `roughness`, `continuity` are already 0..1 by construction (no further scaling).
- All six clipped to `[0, 1]` after normalisation/construction.

## (c) Two channels

- **Summary channel** (what Du receives): the piece's per-section values, held piecewise-constant
  across every second inside that section. For Heavyweight this comes from the cache
  (`data/music/Heavyweight.features.json`'s `sections[].energy/brightness_hz/onset_density`) on the
  three cached axes; on the three new axes (periodicity, roughness, continuity) there is no cached
  value, so the summary is the **per-section mean of the measured string itself** — stated here
  explicitly: on those three axes the summary is *derived*, not independently sourced, so their
  contribution to the six-axis width is within-section variation only, never a genuine
  summary-vs-measurement disagreement.
- **Measured channel**: the per-second string computed from PER-FRAME PRIMITIVES ONLY — no
  whole-piece dependency (no SSM sections, no global tempo) enters the string itself. Sections are
  used only to (i) know the summary channel's step boundaries and (ii) provide the per-second onset
  threshold per the onset definition above; they are never used to compute the measured value.

## (d) Ribbon metrics

- **width** = Euclidean offset between the two channels per second, on the six axes:
  `width_6[t] = ||measured_6[t] - summary_6[t]||`.
- Also report the **three-axis width** restricted to energy/brightness/onset
  (`width_3[t] = ||measured_3[t] - summary_3[t]||`), directly comparable to F-2017's reported
  0.294 mean / 0.569 p90 / 62.7 °/s twist.
- **twist** = angle in degrees between consecutive seconds' offset vectors:
  `twist[t] = degrees(acos(clip(dot(off[t-1], off[t]) / (|off[t-1]|·|off[t]|), -1, 1)))`, computed
  separately for the 3-axis and 6-axis offset vectors, `twist[0]` undefined (not counted in means).

## (e) Pre-registered predictions

- **P1** (reproduction check of F-2017): Heavyweight's **three-axis** width mean lands in **0.25–0.35**
  and twist mean in **50–75 °/s**. If this does not reproduce, that is the headline of the results
  doc, not a footnote.
- **P2** (sanity check, true by construction — stated as such, not a real test): the six-axis width is
  ≥ the three-axis width for every section, since the six-axis offset vector strictly adds
  non-negative squared components.
- **P3**: the closing three sections (by section index) are wider (six-axis width mean) than the
  opening three sections — F-2017 saw this on the three-axis measure.
- **P4**: `felt()` per section under (i) (mode/key held piece-level, only `onset_density` varies) takes
  exactly ONE valence value across all sections; under (ii) (a per-section key/mode estimate via
  `af._key(af._chroma(mag[fa:fb]))` fed into `felt()`) valence varies in at least 3 sections.
- **P5**: for any additional piece supplied via `--audio`, width mean (six-axis) lands in 0.15–0.45
  and twist mean > 30 °/s. **Cannot be tested this run** — only one recording exists. The verdict for
  P5 will be reported as "untestable with one piece."

## (f) Kill rules

- If the measured per-second string's **per-section mean**, on any of the three cached axes
  (energy, brightness, onset), deviates from the cached section value by more than **0.02** (in the
  same normalised 0..1 units used for width), the pipeline's definitions were not matched to
  `extract()`'s own — this is F-2017's exact bug shape (summed magnitude instead of RMS, a global
  onset threshold instead of per-section). The script must refuse to write results in that case: fix
  the pipeline and rerun, never read past the mismatch.
- Deviation is computed and printed for all three cached axes before any other output is produced.

## Pointers

Script: `C:\Nascence\scripts\ribbon_lab.py`. Results: `docs/lab/strings_sheets_ribbon_results_2026-09-27.md`
+ `.json` + per-piece SVG. Source of the axis/prediction spec: job J-1468 briefing (this session).
Demonstration this reproduces: F-2017, scratchpad `ribbon_heavyweight.py`.
