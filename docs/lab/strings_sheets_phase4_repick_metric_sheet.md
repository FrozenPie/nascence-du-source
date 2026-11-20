# Strings and Sheets Phase 4: re-pick re-measure (pre-registered sheet, J-2397, 2026-10-18)

Written by agent J-2397 after the D-0477 downloads landed and BEFORE any signal or envelope number was computed on
the new files. Committed on its own before the run. Offline only; nothing reaches Du or any live store.

## Which swaps are measured

D-0477 approved five swaps. Licences were re-checked on the item page on 2026-10-18 before download:

| key | new file | licence read from the item page | measured? |
|---|---|---|---|
| `dawn_chorus` | DOC `46-tui-morning-chorus.mp3` | DOC bird-songs page: "These bird songs are Crown Copyright. They may be reused, even commercially, as long as you credit the Department of Conservation (NZ)" | yes |
| `log_on_fire` | Freesound 455132 (HQ preview) | item page licence link `creativecommons.org/publicdomain/zero/1.0/`, `data-duration` 181.906 | yes |
| `morepork_call` | DOC `morepork-song.mp3` | DOC bird-songs page (as above), listed 01:43 | yes |
| `wind_in_trees` | Freesound 523389 (HQ preview) | item page licence link `creativecommons.org/publicdomain/zero/1.0/`, `data-duration` 139.52 | yes |
| `wood_pigeon` | XC933702 | NOT VERIFIED: `https://xeno-canto.org/933702` returns a BotStopper page (8215 bytes, no licence link); the XC alternate XC378290 is on the same site. Not bypassed. | no, key stays on XC957404 |

`moth_tap` is constructed-only (no stand-in, D-0477); its old recording leaves the measured set.

## Windows (rules fixed here, before looking at any result)

Window audio is cut from the decoded 22050 Hz mono signal (`audio_features.decode()`) and written as a 16-bit WAV in
scratch; every window starts on a whole second; the search uses 1 s steps.

- `dawn_chorus`: the 60 s window with the highest mean 1.5-9 kHz band power (where the chorus is).
- `log_on_fire`: find the frame with the largest rise of 50-500 Hz band power in dB over the median of the
  preceding 1 s (the load thud). Window = [t - 1 s, t + 4 s].
- `morepork_call`: the 15 s window with the highest mean 300-2000 Hz band power (the call's own band).
- `wind_in_trees`: the whole file (no window was named; the old pick was also measured whole).

## What is computed (all reused code, unchanged)

1. J-2027 signal review (`analyze_J-2027.py` + `tonal_J-2027.py` logic, copied unchanged into the run script):
   band shares, tonal share 1.5-9 kHz, silence and onset statistics. Sanity check: the run script must
   reproduce J-2027's stored `review_signal` for the OLD `dawn_chorus` and `morepork_call` files to within 0.002 on
   tonal share and band shares, or nothing is read.
2. `core/audio_features.py` `extract()` via `scripts/ribbon_lab.py` `process_piece()` on each new window, as J-2027.
3. J-2372 envelope test (`scripts/strings_phase4_envelope_lab.py` `evaluate()`, tau 0.25, 4-of-5, 2-of-3), with
   the new keys' strings swapped in.

## Verdicts (the D-0477 defeater, made concrete)

- **dawn_chorus mismatch gone** iff tonal share (1.5-9 kHz) of the window >= 0.5. Also reported: the whole file
  and every non-overlapping 60 s window, so the window choice can be seen not to carry the verdict.
- **morepork not rumble-dominated** iff the window's <300 Hz energy share < 0.5 (old file 0.953) AND its 300-2000
  Hz share is the largest band.
- **wind_in_trees** fixed iff <300 Hz share < 0.5 (old 0.998) and centroid > 1000 Hz (old 172 Hz).
- **log_on_fire** fixed iff the window's energy contour has its loudest of three thirds in the first or middle
  third (a thud then flare, not a flat bed) AND the strongest onset lies inside the window's first 2 s.
- **Envelope headline, two reads.** (a) J-2372's primary denominator rule unchanged (dawn_chorus, log_on_fire
  still excluded as MISMATCH, moth_tap now excluded as constructed-only): pass share vs 60%. (b) dawn_chorus and
  log_on_fire moved into the primary set if, and only if, their mismatch verdict above cleared. Neither read
  changes tau or any rule. J-2372's 30.2% and the 60% bar are the comparison; no re-tuning.
