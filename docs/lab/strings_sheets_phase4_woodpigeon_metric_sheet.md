# Strings and Sheets Phase 4: wood_pigeon swap XC957404 -> XC933702 (pre-registered sheet, J-2406, 2026-10-18)

Written by agent J-2406 after the download landed and BEFORE any signal, envelope or seed number was computed on
the new file (only its ID3 text was read). Committed on its own before the run. Offline only; nothing reaches Du.

## The file

- **Ruling.** D-0481 (travis, 2026-10-18): Travis read `https://xeno-canto.org/933702` himself; the licence is
  CC BY-NC-SA 4.0 (local derivative features allowed, not NC-ND). That satisfies D-0477's licence re-check.
- **Download.** `https://xeno-canto.org/933702/download` with a plain HTTP client: HTTP 200, `audio/mpeg`,
  1,789,897 bytes, `Content-Disposition: XC933702 - New Zealand Pigeon - Hemiphaga novaeseelandiae.mp3`. Not
  bot-blocked (only the item page is). Saved into a new empty scratch directory as untrusted data, read only
  with `python -I`, then copied to `data/sound_recordings/wood_pigeon__XC933702.mp3` (gitignored).
  SHA-256 `e095552504f305de1b4c3a515f8d8cb17a432ed55e71ea99bea08feeff9d50b0`.
- **ID3 text** (the file's own tags): Ken George, Maraetotara, Whakatane District, Bay of Plenty, 2024-09-14 08:00,
  "call", "The soft rising low note WOOOP, against background of other common NZ bush birds"; also Common
  Blackbird, NZ Bellbird, Tui, House Sparrow. 128 kbps, 48 kHz mono mp3.

## Window (rule fixed here, before looking at any result)

Same mechanics as J-2397 (`strings_phase4_repick_metric_sheet.md`): decoded 22050 Hz mono, whole-second starts,
1 s steps, written as a 16-bit WAV in scratch. **The 15 s window with the highest mean 300-2000 Hz band power**
(the coo's own band; the recordings list asks for 10-20 s). This is J-2397's morepork rule, unchanged.

## What is computed (all reused code, unchanged)

1. J-2027 signal review: `review()` from `scripts/strings_phase4_repick_lab.py` (J-2027's code), on the window
   and on the whole file. Sanity gate: it reproduces J-2027's stored `review_signal` for the OLD wood_pigeon file
   (`wood_pigeon__XC957404.wav`) within 0.002 on tonal share and all four band shares, or nothing is read.
2. Features: `core/audio_features.py` `extract()` via `scripts/ribbon_lab.py` `process_piece()` on the window
   (as J-2397's `features()`). Extractor kill rule 0.02.
3. Gate W0: the J-2383 gate code with no gate (`string_gated`, x = -inf) on the window reproduces the window's
   `string6` within 0.01 (J-2395's R0a, for this one key).
4. J-2372 envelope test (`evaluate()`, unchanged) and J-2383 gated test (`evaluate_gated()`, X = 10, unchanged).

## Verdicts

- **F-3069 check (the D-0481 defeater's signal branch).** The swap clears iff, in the window, the 300-2000 Hz
  energy share is the largest of the four bands AND the <300 Hz share < 0.5 AND the top dominant frequency lies
  in 300-2000 Hz. Old file for comparison: 300-2000 Hz 0.108, 2-6 kHz 0.528, top tonal peaks 2.5-4 kHz.
  Whole-file values are also reported so the window choice can be seen not to carry the verdict.
  If it does NOT clear, the D-0481 defeater fires: no re-seed, a new `/decide` for Travis, key stays on its file.
- **Gate T1 (reproduction before anything changes).** With the current registry (post J-2395, wood_pigeon seed
  untouched by it) and wood_pigeon on its OLD file, the J-2372 test on read (b) gives J-2395's after-numbers:
  51/64, baseline 0.331 (rounded). Otherwise nothing is read.
- **Swap headline.** Read (b) (n = 64) with wood_pigeon on the new window, registry unchanged: pass share,
  baseline, discriminating flag, wood_pigeon's own verdict, misses and own rank. Read (a) (n = 62) too.

## The single-key re-seed (J-2395's rule, `strings_sheets_phase4_reseed_2026-10-18.md` sections 1-2, unchanged)

Applied to wood_pigeon only, only if the F-3069 check clears (J-2395 excluded the key solely because the swap had
not happened):

- Candidate iff its **gated** (X = 10) verdict on the new window is **fail**; not re-seeded if it passes gated or
  has fewer than 3 gated seconds.
- Named axes = union over the three gated thirds of the gated misses. Onset only if also missed on at least one
  ungated third (the onset exception). Energy never.
- Timbre axes (periodicity, roughness, continuity) = mean of the three gated thirds, fitted first; brightness =
  the fixed-point offset fit on the gated thirds; onset = the same fit on the ungated thirds. Clipped to [0, 1],
  2 decimals. Fitting code is J-2395's `fit_axis()`, imported unchanged.
- **Gate T0:** the edited `_SOUNDS` differs from the pre-edit registry in exactly the proposed wood_pigeon
  (key, axis) pairs and nowhere else.
- **Re-run:** J-2372 test, unchanged, read (b) n = 64 and read (a) n = 62, wood_pigeon on the new window, after the
  edit. Bar 60%; NON-DISCRIMINATING if shuffle baseline >= 0.8 x share. Stated now: wood_pigeon's own pass after
  re-seed is **in-sample** (fitted to this recording) and is not evidence the seed is right about the sound; what
  can still fail is the other 63 keys' verdicts (a moved seed changes the shuffle baseline and every other key's
  foreign-pass count) and discrimination.
- Large shift flag: any axis moved by 0.40 or more, as J-2395.
