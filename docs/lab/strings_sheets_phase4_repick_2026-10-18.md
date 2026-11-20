# Strings and Sheets Phase 4: D-0477 re-picks re-measured (J-2397, 2026-10-18)

Pre-registered sheet: `strings_sheets_phase4_repick_metric_sheet.md` (committed 88bdc90c before the run). Script:
`scripts/strings_phase4_repick_lab.py` (python -I; signal-review code copied unchanged from J-2027's scratch
`analyze_J-2027.py` + `tonal_J-2027.py`; envelope test imported unchanged from `scripts/strings_phase4_envelope_lab.py`).
Full data: `strings_sheets_phase4_repick_2026-10-18.json`. Signal analysis only; nobody listened. Offline; nothing
reaches Du.

## Gates the run passed before anything was read

- **Signal-review reproduction.** On the OLD files (scratch copies `rec_J-2027/`), the script reproduces J-2027's
  stored `review_signal` exactly (max deviation 0.000 on tonal share and all four band shares) for `dawn_chorus`
  (tonal 0.005, <300 Hz 0.364), `morepork_call` (0.281, 0.953) and `wind_in_trees` (0.000, 0.998).
- **Envelope reproduction.** With the old strings and J-2372's exclusions, the imported `evaluate()` gives 19/63 =
  30.2%, baseline 0.254: J-2372's own headline.
- Extractor kill rule (ribbon_lab, 0.02): not triggered on any of the four windows (max 0.0005).

## Licences and downloads

| key | new file | licence (item page, 2026-10-18) | window used | verdict |
|---|---|---|---|---|
| `dawn_chorus` | DOC `46-tui-morning-chorus.mp3` (184 s) | Crown copyright, reuse with credit "Department of Conservation (NZ)" | 31-91 s (rule: max 1.5-9 kHz power over 60 s) | **mismatch gone** |
| `log_on_fire` | Freesound 455132 HQ preview (181.9 s) | CC0 1.0 | 22-27 s (thud at 23.59 s, +33.0 dB over the prior 1 s) | **mismatch gone** |
| `morepork_call` | DOC `morepork-song.mp3` (103 s) | Crown copyright (as above) | 12-27 s (rule: max 300-2000 Hz power over 15 s) | **rumble gone** |
| `wind_in_trees` | Freesound 523389 HQ preview (139.5 s) | CC0 1.0 | whole file | **rumble gone** |
| `wood_pigeon` | XC933702 NOT downloaded | item page returned BotStopper; licence not readable, not bypassed; XC alternate XC378290 is on the same blocked site | - | key stays on XC957404 |
| `moth_tap` | none | - | - | constructed-only (D-0477); old file 131340 leaves the measured set |

## The D-0477 defeater checks

- **dawn_chorus**: tonal share (1.5-9 kHz) **0.832** in the window (old file 0.005; bar 0.5). Whole file 0.839;
  every non-overlapping 60 s block passes too (0-60 s 0.840, 60-120 s 0.758, 120-180 s 0.620), so the window choice
  does not carry the verdict. Band shares <300 Hz 0.025, 300-2000 Hz 0.790, 2-6 kHz 0.184.
- **morepork_call**: <300 Hz share **0.006** (old 0.953), 300-2000 Hz **0.986** (largest band); dominant peaks
  754-980 Hz, i.e. in the two-note call's band; 1.13 onsets/s. Whole file: 0.009 / 0.985.
- **wind_in_trees**: <300 Hz **0.218** (old 0.998), centroid **3221 Hz** (old 172 Hz), flatness 0.688 (noise-like
  rustle), continuous (3% of frames below -20 dB).
- **log_on_fire**: per-second energy 0.215, **0.582**, 0.135, 0.135, 0.154; first third of three is the loudest
  (0.398 vs 0.135 / 0.154); strongest onset at 1.58 s into the window. Thud-then-decay shape, so it passes. Caveat: the
  load event includes a 1.5 kHz tonal clank (tonal share 0.639, likely the stove door), so "log" vs "stove door" is not
  separable by signal alone.

## Envelope test (J-2372 rule unchanged)

- **Read (a)**, J-2372's denominator (dawn_chorus, log_on_fire excluded; moth_tap now constructed-only): **19/62 =
  30.6%**, shuffle baseline 0.251, NON-DISCRIMINATING (baseline >= 0.8 x share), own-rank median 17.5.
- **Read (b)**, dawn_chorus and log_on_fire moved in (both cleared their mismatch): **20/64 = 31.3%**, baseline 0.260,
  non-discriminating, own-rank median 17.5.
- Both stay far under the 60% bar. Fixing the recordings did not move the headline.

| key | own envelope, old file | own envelope, new file | axes missed (new) | own rank (new, read b) |
|---|---|---|---|---|
| `dawn_chorus` | PASS 3/3 (wrong sound) | **fail 0/3** | brightness (0.49-0.51 vs 0.57-1.0), continuity (0.43-0.51 vs 0.65-1.0) | 52 |
| `log_on_fire` | PASS 3/3 (wrong sound) | PASS 2/3 | onset, roughness, continuity in the tail third | 14 |
| `morepork_call` | fail 0/3 | fail 0/3 | onset (0.65-0.80 vs <=0.55), roughness (0.46-0.51 vs <=0.35) | 45 |
| `wind_in_trees` | fail 0/3 | fail 0/3 | brightness (0.60-0.65 vs <=0.60), periodicity (0.55-0.57 vs <=0.47) | 7 |

**Read.** The two former mismatches passed their envelope while they were the wrong sound; with the right sound,
the dawn chorus now fails. This is the J-2372 non-discrimination flag seen key by key: the envelope does not separate
right from wrong recordings. The new misses point at seeds, not files: the dawn chorus seed wants brighter and
more continuous than a real NZ mixed-bush chorus measures; the morepork seed wants sparser onsets and purer
(less flat) tone than the DOC song measures. These are candidates for D-0476's reviewed re-seed list (J-2395), which
until now excluded these keys pending this measurement.

## Honest limits

- Freesound files are HQ preview mp3; DOC files are the published mp3s. Windows were chosen by fixed rules (sheet),
  not by ear.
- Tonal share is a 1.5-9 kHz measure; it is the right test for the chorus, not for the morepork (whose call sits
  near 800-900 Hz).
- wood_pigeon is unchanged because its licence could not be read on the item page.
