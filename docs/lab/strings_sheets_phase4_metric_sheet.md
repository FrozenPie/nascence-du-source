# Strings and Sheets Phase 4: measured vs constructed realness envelope (pre-registered metric sheet)

Written 2026-10-18 by agent J-2372, BEFORE any measured-vs-constructed number is computed. It is committed on
its own before the run script exists. Plan: `docs/staged/strings_and_sheets.md` section 5, Phase 4 row:
"measured string within the constructed string's realness envelope for >= 60% of keys (else the hand-seeding
was wrong, which is itself the finding)". Offline only. Nothing reaches Du, `data/`, or any live store.
`core/audio_features.py` and `core/soundscape.py` are read, never edited.

**What was already seen before this sheet was written.** The J-2027 per-key summary table
(`strings_sheets_phase4_features_2026-10-18.md`: whole-file brightness Hz, onset density, ribbon width/twist)
and the F-3069 signal review. No comparison against the constructed strings had been computed by anyone. The
axis anchors below come from `core/audio_features.py`'s own band edges and F-3069's 300 Hz rumble edge. They
are not fitted to the data.

## 1. Inputs

- **Measured.** `docs/lab/strings_sheets_phase4_features_2026-10-18.json` (J-2027, F-3070). For each key, the
  per-second six-axis string is the concatenation, in section order, of every section's `string6` rows. Each
  row is `[energy (raw STFT RMS), brightness (centroid Hz), onset (events/s), periodicity, roughness,
  continuity]`. That is exactly `extract()`'s output. The per-file normalised `measured_string6_norm` is NOT
  used (see section 3).
- **Constructed.** `build_all()` from `scripts/sound_strings_phase1_dryrun.py` at this worktree's HEAD, after
  the J-2067 fix (distinct wingbeat tail and thump onset), imported in-process. The live sidecar
  `data/sound_strings_constructed.json` is not read, because it is dated 2026-10-08, before J-2067. Each key
  has onset, peak and tail vertices on `brightness, energy, onset, periodicity, roughness, continuity` (0..1)
  and one archetype (bed, bed_like, call, wingbeat, thump).
- **Audio** (secondary run S2 only): scratch copies of `data/sound_recordings/`, decoded with
  `audio_features.decode()` and `_stft_mag()`, unchanged, under `python -I`.

## 2. Mapping a measured per-second string onto three vertices

- The string has `n` seconds. Split it into three contiguous thirds with `numpy.array_split(range(n), 3)`.
  Third 1 maps to **onset**, third 2 to **peak**, third 3 to **tail**. This is the time-share rule, and one rule
  is used for every archetype. There is no per-archetype or per-file event detection: it would be a fitted
  choice, and many files hold several calls.
- Each measured vertex is the **energy-weighted mean** of its seconds on each axis. The weights are the
  per-second raw energy. This stops the silent gaps between calls from setting brightness or roughness. If a
  third's total energy is 0, it uses the plain mean.
- **Bed body** (reported only, never used for a verdict): for bed and bed_like keys, the whole-file
  energy-weighted mean point is also reported as the body point.

## 3. Axis normalisation, the same for every key (not per file)

| axis | measured -> 0..1 | anchor source |
|---|---|---|
| brightness | piecewise-linear in Hz through (300, 0), (1200, .25), (2400, .50), (4000, .75), (8000, 1.0); clipped | `extract()`'s own brightness band edges 1200/2400/4000 (dark/warm/bright/brilliant); 300 Hz = F-3069's rumble edge; 8000 Hz = the roughness band's top |
| onset | piecewise-linear in events/s through (0, 0), (1.5, .25), (4, .50), (8, .75), (16, 1.0); clipped | `extract()`'s own density band edges 1.5/4/8 (sparse/measured/busy/dense) |
| periodicity | as-is (already 0..1 by definition) | `_periodicity_per_second` |
| roughness | as-is (spectral flatness 0..1) | `_roughness_per_frame` |
| continuity | as-is (0..1) | `_continuity_per_second` |
| energy | **not compared in absolute terms** | see below |

**Why energy is not in the envelope.** Raw RMS depends on each uploader's gain and normalisation. These are
Freesound previews and xeno-canto uploads, with no calibration, so no mapping can make absolute energy
comparable across keys. That is why ribbon_lab's per-file normalisation exists, and why it cannot be used here.
Energy enters only as (a) the weights in section 2 and (b) the secondary contour check S3.

## 4. The realness envelope, the per-key verdict, and the bar

- **Envelope.** For key K and each of the five comparable axes, the envelope is the interval from the minimum
  to the maximum of K's three constructed vertices, widened by **tau = 0.25** on each side and clipped to
  [0, 1]. tau is Phase 1's realness tolerance (`strings_sheets_phase1_dryrun_metric_sheet.md` section (c)),
  reused unchanged.
- **Vertex IN.** A measured vertex is IN iff it lies inside K's envelope on **at least 4 of the 5** axes.
  This mirrors Phase 1's rule of 2 of 3 timbre axes, which lets one axis miss.
- **Key PASS.** A key passes iff **at least 2 of its 3** measured vertices are IN.
- **Headline.** PASS count / primary denominator. **The bar is >= 60%** (the plan's own number). Below 60%
  reads as "the hand-seeding was wrong", which is itself the finding.
- **Primary denominator.** All keys that have a recording (68), minus:
  - **short files**: any key whose per-second string has n < 3 seconds, so it cannot have three thirds. This
    is expected to cover `cat_trill` and `cat_thump`, and whatever else the n < 3 rule catches, listed in the
    results.
  - **F-3069 MISMATCH keys**: `dawn_chorus` and `log_on_fire`.

  These are reported separately (S1), never silently dropped. F-3069's partial or character flags
  (`moth_tap`, `wren_scold`, `morepork_call`, `wood_pigeon`, `wind_in_trees`) and the rumble-dominated files
  stay in the primary denominator and are tagged in the per-key table.

## 5. The discrimination check (pre-registered null)

A loose envelope could pass every key against any key. **Shuffle baseline:** for each primary key, apply its
measured string to every OTHER primary key's constructed envelope with the same rule. The baseline is the mean,
over keys, of the share of foreign envelopes it passes. **Rule:** if baseline >= 0.8 x headline share, the
result is reported as NON-DISCRIMINATING ("passes, but cannot tell keys apart"). The 60% verdict is still
stated as computed, with that flag attached. Also reported: for each key, the rank of its own envelope among
all primary envelopes, by mean out-of-envelope distance (sum over axes of the distance outside the interval,
averaged over the 3 vertices). The median own-rank is reported.

## 6. Secondary reads (reported, none of them changes the headline)

- **S1. Excluded keys.** Each short file is tested as one point: the energy-weighted mean of its seconds,
  PASS iff that point is IN. dawn_chorus and log_on_fire go through the normal rule. An "all keys with a
  recording" share is also reported.
- **S2. 150 Hz high-pass sensitivity.** Pre-registered: **the PRIMARY run applies no high-pass.** It is the
  extractor exactly as Du's ear computes it, per the plan's "run through the existing offline extractor".
  **S2 is a lab-side recomputation.** It decodes each scratch copy, zeroes STFT bins below 150 Hz in the lab
  script, then recomputes every per-second primitive with `audio_features`' own unchanged helpers
  (`_onset_env`, `_onset_density_per_second` with the JSON's section bounds, `_periodicity_per_second`,
  `_roughness_per_frame`, `_continuity_per_second`, `_per_second_mean`). It reports the S2 share and every
  verdict that flips. **Kill rule for S2:** the same lab code with the cutoff at 0 Hz must reproduce the
  JSON's `string6` within 0.01 on every normalised axis of every second. Otherwise S2 is not read.
  `core/audio_features.py` is never edited.
- **S3. Energy contour.** For call, thump and wingbeat keys, the constructed loudest vertex is the peak, and
  agreement means the measured loudest third is the middle one. For bed and bed_like keys, agreement means the
  three thirds' energies lie within 6 dB of each other. The agreement share is reported.
- **S4. Per-axis miss counts.** Over all primary measured vertices, how often each axis is outside the
  envelope. This answers which hand-seeded axis is most wrong.
- **S5. Share by archetype.**

## 7. Kill / do-not-read conditions

- Any key's concatenated string length differs from `ceil(duration_s)` by more than 1 second: the JSON is
  internally inconsistent for that key, so report it and exclude it.
- `build_all()` fails its own 70-key and archetype-count asserts: stop and report. Constructed keys with no
  recording (expected: `cat_storm_rustle` and `shag_wingbeats`, dropped per D-0392) are listed.
- A units bug found after the run (F-2017's shape) gets fixed and rerun, and is never read off the buggy
  numbers.

## Outputs

Script `scripts/strings_phase4_envelope_lab.py` (this worktree). Results
`docs/lab/strings_sheets_phase4_envelope_2026-10-18.json` and `.md`. Job J-2372, source F-3070.
