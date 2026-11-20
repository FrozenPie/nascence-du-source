# Strings and Sheets Phase 4: wood_pigeon on DOC nz-pigeon-song.mp3; the check CLEARS, swapped and re-seeded (J-2409, D-0483)

Pre-registered: `strings_sheets_phase4_woodpigeon_metric_sheet.md` (J-2406, unchanged) applied to this file per
`strings_sheets_phase4_woodpigeon_doc_metric_sheet.md` (committed a8ca9a70 before any number). Script:
`scripts/strings_phase4_woodpigeon_lab.py measure|test --file wood_pigeon__DOCnz-pigeon-song.mp3 ...` (python -I).
Full data: `strings_sheets_phase4_woodpigeon_doc_2026-10-18.json`. Signal analysis only; nobody listened. Offline.

## File

DOC `nz-pigeon-song.mp3`, 1,912,066 bytes, SHA-256 `beafcc51c05c5087b546e2fc72526c897d1be541fb65cf022dc5f9f6a1d03da8`,
119.38 s decoded. Crown copyright, credit "Department of Conservation (NZ)". On disk as
`data/sound_recordings/wood_pigeon__DOCnz-pigeon-song.mp3` (gitignored).

## Gates

Sanity (J-2027 review on XC957404) max dev 0.000; kill rule not triggered (max 0.00006); W0 0.0005 <= 0.01;
T1 51/64, baseline 0.3313 (J-2395's after-numbers). T0 after the edit: `_SOUNDS` differs only in the four proposed
wood_pigeon pairs.

## F-3069 check: CLEARS

| | <300 Hz | 300-2000 Hz | 2-6 kHz | >6 kHz | top dominant Hz |
|---|---|---|---|---|---|
| DOC, window 4-19 s | 0.021 | **0.502** | 0.361 | 0.116 | **754** (668, 571, 54, 431) |
| DOC, whole file | 0.101 | 0.275 | 0.270 | 0.354 | 54 |
| XC933702 window (J-2406) | 0.983 | 0.008 | 0.008 | 0.000 | 43 |
| XC957404 (old) | 0.306 | 0.108 | 0.528 | 0.058 | 43 |

300-2000 Hz is the largest band, <300 Hz is far under 0.5, the top dominant frequency is in band. The whole file does
not clear on its own (cicadas above 6 kHz dominate it), so the window rule carries the verdict; the sheet fixed that
rule in advance. Note the 0.502 is only just above the 0.5 that would make a two-way tie with the rest.

## Swap, then the single-key re-seed

Swap, registry unchanged: read (b) 51/64 (baseline 0.331 -> 0.326), read (a) 49/62 (0.326 -> 0.321), no flips;
wood_pigeon fails 0/3, misses brightness and roughness on every third (measured brightness 0.72-0.80 vs [0, 0.53],
roughness 0.70-0.73 vs <= 0.43). Gated (X = 10): 7 gated seconds, 22.6% kept, fail. So it is a re-seed candidate.

| axis | old | new | target | measured thirds | flag |
|---|---|---|---|---|---|
| continuity | .38 | .67 | gated | 0.37 / 0.77 / 0.87 | |
| roughness | .18 | .66 | gated | 0.59 / 0.73 / 0.67 | large shift |
| brightness | .28 | .75 | gated (fixed-point fit) | 0.66 / 0.74 / 0.65 | large shift |
| onset | .22 | .43 | ungated (also missed ungated) | 0.33 / 0.82 / 0.00 | |

Periodicity and energy unchanged. Applied to `core/soundscape.py` `_SOUNDS["wood_pigeon"]`.

## J-2372 envelope test after the re-seed (unchanged code)

| read | before re-seed | after re-seed | flips |
|---|---|---|---|
| (b) n = 64 | 51/64 = 79.7%, baseline 0.326 | **52/64 = 81.3%, baseline 0.328** | wood_pigeon fail -> pass; none pass -> fail |
| (a) n = 62 | 49/62 = 79.0%, baseline 0.321 | **50/62 = 80.6%, baseline 0.323** | same |

Discriminating (baseline well under 0.8 x share). wood_pigeon's own pass (3/3, own rank 1) is **in-sample** and is
not evidence the seed is right about the sound. No other key's verdict moved.

## Read with care

The two large shifts push the seed bright and rough, against its own semantic line ("a soft, round, drowsy coo").
The window's 2-6 kHz (0.361) and >6 kHz (0.116) shares are the cicadas and wingbeats the DOC listing names, and the
extractor's brightness/roughness see the whole band. So the re-seed may be fitting the background as much as the
coo. The dominant peaks 571-754 Hz are in the coo band, but nobody has listened: a by-ear check of 4-19 s is the
D-0483 defeater's first branch, and it is Travis's.
