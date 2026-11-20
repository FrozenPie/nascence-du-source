# Strings and Sheets Phase 4: wood_pigeon on DOC nz-pigeon-song.mp3 (pre-registered sheet, J-2409, D-0483)

Written by agent J-2409 after the download landed and BEFORE any signal, envelope or seed number was computed on
the new file. Committed on its own before the run. Offline only; nothing reaches Du.

## The ruling

D-0483 (travis, 2026-10-18): option (c), then (a). Run the SAME pre-registered check J-2406 committed
(`strings_sheets_phase4_woodpigeon_metric_sheet.md`, unchanged) on DOC `nz-pigeon-song.mp3`. If it fails, fall
back to option (a): accept XC933702 with the rumble caveat and run J-2395's single-key re-seed on it.

## The file

- `https://www.doc.govt.nz/globalassets/documents/conservation/native-animals/birds/bird-song/nz-pigeon-song.mp3`,
  plain HTTP client: HTTP 200, `audio/mpeg`, 1,912,066 bytes, last-modified 2018-05-25. Listed on
  `https://www.doc.govt.nz/nature/native-animals/birds/bird-songs-and-calls/` as "Three adults in song and in-flight
  wingbeats (cicadas in the background)", 01:58. Crown copyright, reuse with credit "Department of Conservation (NZ)".
- Saved into a new empty scratch directory as untrusted data, read only with `python -I`; copied to
  `data/sound_recordings/wood_pigeon__DOCnz-pigeon-song.mp3` (gitignored).
  SHA-256 `beafcc51c05c5087b546e2fc72526c897d1be541fb65cf022dc5f9f6a1d03da8`. MPEG layer III, 128 kbps, 44.1 kHz.

## What runs (nothing amended)

`scripts/strings_phase4_woodpigeon_lab.py measure` with `--file wood_pigeon__DOCnz-pigeon-song.mp3 --sha <above>
--tag DOCnz-pigeon-song --job J-2409 --out docs/lab/strings_sheets_phase4_woodpigeon_doc_2026-10-18.json`. The
J-2409 change to that script only makes the file, SHA, window-WAV label, job id and output path arguments; with no
arguments it is J-2406's run byte for byte in what it computes. Window rule, gates (sanity, kill rule, W0, T1),
the F-3069 check, the swap headline, the single-key re-seed rule and T0 are J-2406's sheet, unchanged.

## Branches, fixed now

- **Check clears on DOC:** swap wood_pigeon to the DOC window in the manifest, apply the re-seed rule as the
  J-2406 sheet states, edit `_SOUNDS`, run `test` (T0 + J-2372 read (b) n = 64 and read (a) n = 62).
- **Check fails on DOC:** re-run `measure` on XC933702 with `--accept-ruling D-0483` (output
  `docs/lab/strings_sheets_phase4_woodpigeon_accept_2026-10-18.json`). The flag only skips the "check did not
  clear" stop, as D-0483 (a) rules; the window, gates and re-seed rule are unchanged, and the other two skip
  conditions (passes gated, fewer than 3 gated seconds) still apply. Then edit `_SOUNDS`, run `test`, and write
  the rumble caveat into the manifest.
- Either way wood_pigeon's own post-re-seed pass is in-sample, as the J-2406 sheet states.
