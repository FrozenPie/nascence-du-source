# Strings and Sheets Phase 4: event-gated envelope re-run (pre-registered gate sheet, J-2383)

Written 2026-10-18 by agent J-2383, BEFORE any gated number is computed, and committed on its own before the run
script exists. Source: F-3081 (J-2372). Question: how much of the 19/63 = 30.2% envelope failure is a
**definitional gap** between the channels (field recordings carry continuous background between events, and
`extract()`'s continuity, periodicity and roughness are computed on the whole signal) and how much is **wrong
hand-seeding**. D-0476 and D-0477 are open for Travis; this job measures only and rules nothing. Offline only.
Nothing reaches Du, `data/`, or any live store. `core/audio_features.py` is read, never edited.

**What was already seen before this sheet was written.** Everything in the J-2372 results
(`strings_sheets_phase4_envelope_2026-10-18.md/.json`): the ungated headline, per-key verdicts, per-axis misses
and their direction. No gated number has been computed by anyone.

## 1. Unchanged from the J-2372 sheet

Everything in `strings_sheets_phase4_metric_sheet.md` (commit 4e99bca8) stays exactly as written, except the
per-second string's source, which section 2 below replaces:

- the constructed strings (`build_all()` at this worktree's HEAD, post J-2067) and the envelope (min..max of
  the three constructed vertices, widened by **tau = 0.25**, clipped to [0, 1]);
- the time-thirds mapping (`numpy.array_split`, energy-weighted vertices), the axis normalisation table, and
  the exclusion of energy from the envelope;
- vertex IN on **>= 4 of 5** axes, key PASS on **>= 2 of 3** vertices, the **60%** bar;
- the **same 63 primary keys** as J-2372 (short files cat_thump, cat_trill, gate_latch and MISMATCH dawn_chorus,
  log_on_fire excluded and reported separately; cat_storm_rustle and shag_wingbeats have no recording);
- the shuffle baseline (mean share of foreign envelopes passed) and its rule: baseline >= 0.8 x share means
  NON-DISCRIMINATING; the median own-envelope rank is reported.

## 2. The one change: a lab-side event gate

Per file, decoded from a scratch copy with `audio_features.decode()` and `_stft_mag()`, unchanged, no high-pass:

- **Frame energy** `e_f = sqrt(mean(mag^2))` per STFT frame, exactly as `string_hp()` in
  `scripts/strings_phase4_envelope_lab.py` computes it.
- **Reference** = the 10th percentile of `e_f` over all frames of that file. If it is <= 0 (digital silence), the
  10th percentile of the strictly positive frames is used instead.
- **Gate**: a frame is kept iff `20 * log10(e_f / ref) >= X` dB (e_f is an amplitude-like RMS, so 20 log10).
  **Primary X = 10 dB.** Sensitivity: **X = 6** and **X = 15**, reported, never the headline.
- **Recomputation.** Ungated frames are replaced by silence: their STFT magnitude rows are set to 0, so the
  sound object sits in silence, which is what a hand-seeded string describes. On that masked spectrogram,
  `audio_features`' own unchanged helpers compute per second: energy (`_per_second_mean` of `e_f`), onset
  (`_onset_env` then `_onset_density_per_second` with the features JSON's section bounds), periodicity
  (`_periodicity_per_second`) and continuity (`_continuity_per_second`).
- **Brightness and roughness** are the per-second means of the per-frame centroid and of `_roughness_per_frame`
  over the **kept frames only**, in the same 1 s frame bins as `_per_second_mean`. Reason, stated before the
  run: on a zeroed frame the centroid is 0 Hz and the spectral flatness is 1.0 (`eps / eps`), both artefacts of
  the zeroing, not properties of the sound.
- **Seconds with no kept frame** have no row. The gated string is the remaining seconds, in time order. The
  thirds are taken over those seconds.
- **Gated-short keys.** A primary key left with fewer than 3 gated seconds stays in the 63 and is tested as one
  point, the energy-weighted mean of its gated seconds (the J-2372 S1 point rule), PASS iff that point is IN.
  These keys are listed.

## 3. Kill rule (before anything gated is read)

**G0 reproduction.** The same lab code with no gate (every frame kept, `X = -inf`) must reproduce the features
JSON's `string6` within **0.01** on every normalised axis of every second of every key with a recording, as
J-2372's S2 did. Otherwise no gated number is read. A units bug found after the run is fixed and rerun, never
read off the buggy numbers (F-2017's shape).

## 4. Reported

- **Headline at X = 10**: gated PASS / 63, against the ungated 19/63; shuffle baseline and the
  non-discrimination flag; median own-rank.
- **Per-key flips** against J-2372's per-key verdicts (fail->PASS and PASS->fail, by name).
- **Per-axis miss counts with direction** (above / below the envelope) over the gated vertices, next to
  J-2372's (continuity 104: 92 above, 12 below; roughness 90; periodicity 77; onset 68; brightness 47), plus the
  median measured continuity of the gated vertices against the ungated 0.82.
- **Share by archetype** (S5) and the energy contour (S3) on the gated strings.
- **Kept-frame share** per key, and its median per archetype (the gate's own footprint).
- **X = 6 and X = 15**: share, baseline, flips against J-2372.
- The excluded keys (short and MISMATCH) through the same gate, reported separately.

## 5. Pre-registered reading

- **Gated share >= 60% AND discriminating** (baseline < 0.8 x gated share): the miss was **definitional**. The
  follow-up is a measurement definition (what the measured channel calls "the sound"), not a re-seed.
- **Gated share < 60%**: the hand-seeded coordinates are wrong on the named axes. The gated per-axis misses list
  which keys and axes would need a re-seed. That is the founder's call on D-0476, not this job's.
- **Gated share >= 60% but NON-DISCRIMINATING**: the gate widened agreement without making it specific; reported
  as such, neither reading above applies cleanly.
- A known limit, stated now: the gate is built for events. A stationary bed's frame energy sits in a narrow
  band, so a 10 dB gate can cut most of a bed and make it read intermittent. Beds' kept-frame shares and
  their S5 row are read with that in mind; the headline is not re-scored for it.

## Outputs

Script `scripts/strings_phase4_gated_lab.py` (this worktree; it imports the J-2372 lab's functions unchanged).
Results `docs/lab/strings_sheets_phase4_gated_2026-10-18.json` and `.md`. Job J-2383, source F-3081.

## Amendment A1 (2026-10-18, J-2383): keys with zero gated seconds

Written after the G0 kill rule passed (max deviation 0.0006, worst wood_snap onset) and after a crash showed the
sheet did not cover a key with **no** kept frame. Only the count of gated seconds per key was looked at; no
gated verdict, share or baseline had been computed. At X = 10 three primary keys have zero gated seconds
(distant_surf_boom, morepork_call, tide_pool_trickle): no frame is 10 dB over the file's own 10th percentile, so
the gate finds no event in them. Rule added: a key with zero gated seconds has no measured point and is a
**FAIL**; it stays in the 63; its own-rank is not defined and is left out of the median; its foreign-pass
share is 0; its envelope still counts as a foreign envelope for every other key. Also reported, never the
headline: the share over the keys that kept at least one gated second.
