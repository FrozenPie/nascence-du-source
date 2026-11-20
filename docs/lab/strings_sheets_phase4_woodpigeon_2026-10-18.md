# Strings and Sheets Phase 4: wood_pigeon XC933702 downloaded and measured; the swap does NOT clear (J-2406, D-0481)

Pre-registered sheet: `strings_sheets_phase4_woodpigeon_metric_sheet.md` (committed 52a989b7 before any number was
computed on the new file). Script: `scripts/strings_phase4_woodpigeon_lab.py measure` (python -I; J-2027 / J-2397
helpers pulled verbatim out of `strings_phase4_repick_lab.py`; J-2372, J-2383 and J-2395 labs imported unchanged).
Full data: `strings_sheets_phase4_woodpigeon_2026-10-18.json`. Signal analysis only; nobody listened. Offline;
nothing reaches Du.

## The download

- `https://xeno-canto.org/933702/download`, plain HTTP client: HTTP 200, `audio/mpeg`, 1,789,897 bytes. Only the item
  page is bot-blocked; the download URL is not. Licence: CC BY-NC-SA 4.0, read on the item page by Travis (D-0481).
- On disk: `data/sound_recordings/wood_pigeon__XC933702.mp3` (gitignored), SHA-256
  `e095552504f305de1b4c3a515f8d8cb17a432ed55e71ea99bea08feeff9d50b0`, 44.58 s decoded, 128 kbps 48 kHz mono.
  ID3: Ken George, Maraetotara (Bay of Plenty), 2024-09-14, "The soft rising low note WOOOP, against background of
  other common NZ bush birds".

## Gates

- J-2027 review reproduces on the OLD file (XC957404): max deviation 0.000.
- Extractor kill rule (0.02): not triggered (max 0.0002).
- W0 (no-gate `string_gated` reproduces the window's `string6`): 0.0006 <= 0.01.
- T1 (current registry, wood_pigeon on its old file): 51/64, baseline 0.3313, which is J-2395's after-numbers.

## The F-3069 check (the D-0481 defeater's signal branch): FAILS

Window by the pre-registered rule (15 s, max 300-2000 Hz power): **5-20 s**.

| | <300 Hz | 300-2000 Hz | 2-6 kHz | >6 kHz | top dominant Hz | tonal share 1.5-9 kHz |
|---|---|---|---|---|---|---|
| new, window 5-20 s | **0.983** | 0.008 | 0.008 | 0.000 | **43** | 0.676 (median peak 2519 Hz) |
| new, whole file | 0.989 | 0.005 | 0.006 | 0.000 | 43 | 0.607 |
| old XC957404 | 0.306 | 0.108 | 0.528 | 0.058 | 43 | 0.320 (median peak 3607 Hz) |

The 300-2000 Hz band is not the largest, the <300 Hz share is far over 0.5, and the top dominant frequency is 43 Hz.
**By the pre-registered rule the swap does not clear, so the D-0481 defeater fires: no re-seed was applied,
`core/soundscape.py` is unchanged, and wood_pigeon stays on XC957404 in the measured set.** It is a different
failure from F-3069's: the old file's energy sat at 2-6 kHz (bush birds); the new file is 98% low-frequency
rumble (wind or handling below 100 Hz), the same shape as `kingfisher_call` (99%) and the old `morepork_call`.

## Exploratory, NOT pre-registered (read as leads, not verdicts)

`diag_J-2406.py` (scratch, python -I), on the same files:

- Below 100 Hz holds 0.979 of the window's energy. With <100 Hz left out, the shares are 100-300 Hz 0.208,
  300-2000 Hz 0.395, 2-6 kHz 0.376, >6 kHz 0.022. Even then the 300-2000 Hz band only edges the bush birds.
- The strongest spectral peaks in 100-2000 Hz are **301, 258, 345 Hz** (then 1841, 1895, 1583 Hz). A low tonal
  line (150-700 Hz, >20 dB over its band median) shows in 18.4% of active frames, median 269 Hz; the old file
  shows 8.0%, median 226 Hz. So something low and tonal near 250-350 Hz is there, which fits the recordist's
  "soft low WOOOP". But it sits **across** the check's 300 Hz band edge, so a kereru coo may be partly outside the
  band F-3069's check names. That is a question about the check, and it was not changed after the fact.

## What the swap would do to the envelope (J-2372 test, unchanged, current registry)

| | read (b) pass / n | baseline | wood_pigeon own verdict | wood_pigeon misses (onset / peak / tail third) | own rank |
|---|---|---|---|---|---|
| old file (T1) | 51 / 64 = 79.7% | 0.331 | fail 0/3 | brightness, periodicity, roughness, continuity (+ onset at the peak) | 63 |
| new file | 51 / 64 = 79.7% | 0.330 | fail 0/3 | onset, periodicity, roughness, continuity (tail: no onset) | 59 |

Read (a), n = 62: 49/62 both ways (baseline 0.326 -> 0.325). No other key flips. On the new file the measured
**brightness is inside the seed's envelope** (0.30-0.34 vs [0, 0.53]; old file 0.62-0.70), so on the extractor's
own brightness axis the new file is the low sound the seed describes. It still misses on continuity (0.99, the
rumble bed), roughness (0.52-0.54 vs <= 0.43), periodicity (0.17-0.22 vs >= 0.33) and onset (0.76-0.77 vs <= 0.47).
Gated (X = 10): 13 gated seconds (16.7% of frames kept), fail; misses onset, periodicity, roughness (and continuity
in the tail third).

**What J-2395's rule would propose if the check had cleared** (not computed as a seed, not applied): the named
axes would be the gated misses, periodicity, roughness and continuity, plus onset (also missed ungated).

## Decision needed

Opened as a new `/decide` (see the J-2406 ledger rows): the options are to accept XC933702 despite the rumble
(the coo is plausibly at 250-350 Hz), take DOC `nz-pigeon-song.mp3`, keep XC957404, or test with a stated
high-pass, which would be an amendment to the check.
