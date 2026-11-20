# Strings and Sheets Phase 4: measured strings vs constructed realness envelope (J-2372, 2026-10-18)

Pre-registered sheet: `strings_sheets_phase4_metric_sheet.md` (committed before the script existed). Script: `scripts/strings_phase4_envelope_lab.py` (python -I, scratch copies of the recordings). Full data: `strings_sheets_phase4_envelope_2026-10-18.json`. Offline only; nothing was written to `data/` and nothing reaches Du.

## Headline

- **19/63 keys = 30.2% are inside their constructed string's realness envelope. The bar is 60%: NOT MET.** By the plan's own rule, this reads as "the hand-seeding was wrong", which is itself the finding.
- **Discrimination check: NON-DISCRIMINATING.** Each measured string passes a mean of 25.4% of the OTHER keys' envelopes. That is at least 0.8 x the headline (24.1%), so even the passes barely tell keys apart. Median own-envelope rank by out-of-envelope distance is 19 of 63, against about 32 by chance: a weak signal, not none.
- All keys with a recording, including the five excluded ones: 23/68 = 33.8%.
- Excluded from the primary denominator, as pre-registered. Short files (n < 3 s): cat_thump, cat_trill, gate_latch. F-3069 MISMATCH: dawn_chorus, log_on_fire. Constructed keys with no recording (D-0392 drops): cat_storm_rustle, shag_wingbeats.

## Secondary reads

- **S1, excluded keys:** `cat_thump` PASS (1 s); `cat_trill` fail (1 s); `gate_latch` PASS (2 s); `dawn_chorus` PASS (42 s); `log_on_fire` PASS (32 s). Both MISMATCH files pass their envelope. So a passing envelope does not show the recording is the right sound, which agrees with the discrimination flag.
- **S2, 150 Hz high-pass:** the kill rule held. At a 0 Hz cutoff the lab code reproduces the JSON string to a max deviation of 0.0006 (worst: ['wood_snap', 'onset']), under the 0.01 limit. With the 150 Hz high-pass: 19/63 = 30.2%, baseline 27.4%. Flips: `footsteps_floorboards` PASS->fail, `godwits_overhead` fail->PASS, `pen_scratch` fail->PASS, `saw_rasp` PASS->fail. The rumble does not drive the headline.
- **S3, energy contour** (events: loudest third is the middle one; beds: thirds within 6 dB): 33/63 agree.
- **S4, axis misses** over 189 primary measured vertices: continuity 104, roughness 90, periodicity 77, onset 68, brightness 47.
- **S5, by archetype:** bed 3/12, bed_like 3/10, call 5/20, thump 8/20, wingbeat 0/1.

## Post-hoc description (NOT pre-registered; it explains, it does not re-score)

Which way each axis misses, counted over the 189 primary measured vertices: continuity is above the envelope 92 times and below it 12 times. Periodicity is below 49 times and above 26. Roughness is below 50 times and above 40. Measured continuity has a median of 0.82, while the constructed peak continuity has a median of 0.38. Most recordings are continuous signal, because a field recording carries background between the calls. The hand-seeded strings instead describe the sound object alone as brief or intermittent. `extract()`'s continuity (frames above 0.1x a 5 s local max) counts that background as continuity. The largest single miss is therefore partly a definitional gap between the two channels, and partly a seeding error. Telling the two apart would need source separation or a per-key event gate, which this lab does not do.

## Per-key verdicts (primary, n = 63)

| key | archetype | verdict | vertices IN | own rank | foreign pass share | axes missed (onset / peak / tail third) | flag | <300 Hz share |
|---|---|---|---|---|---|---|---|---|
| `bed_watering` | thump | fail | 1/3 | 21 | 0.19 | roug,cont / roug,cont / roug |  | 0.194 |
| `bees_in_garden` | bed_like | PASS | 3/3 | 3 | 0.27 | peri / peri / peri |  | 0.026 |
| `bellbird_song` | call | fail | 0/3 | 30 | 0.18 | onse,cont / onse,peri,roug,cont / onse,roug |  | 0.0 |
| `blackbird_alarm` | call | fail | 1/3 | 33 | 0.23 | onse,peri / peri,roug,cont / onse |  | 0.0 |
| `blackbird_song` | call | fail | 1/3 | 9 | 0.26 | - / onse,cont / onse,cont |  | 0.008 |
| `branches_creak` | thump | fail | 1/3 | 17 | 0.21 | onse,peri,roug / onse,peri,roug / cont |  | 0.65 |
| `canopy_drip` | thump | fail | 0/3 | 31 | 0.08 | roug,cont / roug,cont / roug,cont |  | 0.048 |
| `cat_chatter` | bed_like | fail | 0/3 | 51 | 0.10 | brig,onse,peri,roug / peri,roug,cont / brig,peri,roug,cont |  | 0.069 |
| `cat_demand` | call | fail | 0/3 | 35 | 0.47 | peri,roug,cont / peri,roug,cont / peri,cont |  | 0.302 |
| `cat_lapping` | bed | fail | 0/3 | 59 | 0.21 | onse,peri,roug / onse,peri,roug,cont / onse,peri,roug,cont |  | 0.245 |
| `cat_meow_at_door` | call | fail | 1/3 | 24 | 0.18 | onse,cont / cont / onse,cont |  | 0.036 |
| `cat_purr` | bed | fail | 0/3 | 45 | 0.10 | onse,peri,cont / onse,peri / onse,peri |  | 1.0 |
| `cat_yowl_cargo` | call | fail | 0/3 | 37 | 0.27 | brig,onse,peri,cont / roug,cont / roug,cont |  | 0.007 |
| `chair_desk_scrape` | thump | fail | 0/3 | 59 | 0.18 | peri,roug,cont / peri,roug,cont / peri,roug,cont |  | 0.286 |
| `cicada_chorus` | bed | fail | 1/3 | 15 | 0.11 | peri,roug / onse,peri,roug / onse |  | 0.505 |
| `clock_tick` | bed_like | fail | 0/3 | 21 | 0.24 | onse,peri,roug / onse,peri,roug / onse,peri,roug |  | 0.753 |
| `cricket_night` | bed | fail | 0/3 | 20 | 0.23 | onse,roug,cont / peri,roug / peri,roug,cont |  | 0.353 |
| `cuckoo_call` | call | PASS | 2/3 | 7 | 0.19 | - / onse / onse,peri |  | 0.0 |
| `distant_surf_boom` | bed | fail | 0/3 | 12 | 0.34 | brig,onse,peri,cont / brig,peri,cont / brig,peri,cont |  | 0.742 |
| `door_sound` | thump | PASS | 3/3 | 15 | 0.56 | peri / - / peri |  | 0.153 |
| `embers_settle` | bed | PASS | 2/3 | 20 | 0.53 | - / - / brig,peri |  | 0.018 |
| `fantail_chatter` | call | PASS | 3/3 | 12 | 0.40 | - / - / onse |  | 0.0 |
| `fire_crackle` | bed | fail | 0/3 | 40 | 0.18 | onse,peri,cont / onse,cont / onse,cont |  | 0.034 |
| `footsteps_floorboards` | thump | PASS | 2/3 | 19 | 0.56 | peri / peri / peri,cont |  | 0.201 |
| `footsteps_grass_soil` | thump | fail | 0/3 | 31 | 0.31 | peri,roug,cont / peri,roug,cont / roug,cont |  | 0.878 |
| `footsteps_leafmould` | bed_like | fail | 0/3 | 35 | 0.27 | brig,peri,roug / brig,peri,roug / brig,peri,roug,cont |  | 0.984 |
| `footsteps_shingle` | bed_like | fail | 0/3 | 46 | 0.37 | onse,peri,roug / onse,peri,roug,cont / onse,peri,roug,cont |  | 0.851 |
| `godwits_overhead` | call | fail | 0/3 | 16 | 0.26 | roug,cont / roug,cont / roug,cont |  | 0.004 |
| `gull_cries` | call | fail | 0/3 | 61 | 0.11 | brig,peri,roug,cont / brig,peri,roug,cont / brig,peri,roug,cont |  | 0.03 |
| `herb_cut` | thump | fail | 1/3 | 34 | 0.21 | brig,roug,cont / brig,cont / cont |  | 0.001 |
| `kereru_wingbeats` | wingbeat | fail | 0/3 | 15 | 0.08 | brig,onse,cont / brig,onse,roug / brig,onse,roug |  | 0.726 |
| `kettle_fill` | thump | PASS | 3/3 | 1 | 0.29 | cont / cont / cont |  | 0.165 |
| `kettle_pour` | thump | PASS | 2/3 | 12 | 0.42 | peri,cont / cont / - |  | 0.42 |
| `kettle_sing` | bed_like | fail | 0/3 | 6 | 0.32 | brig,onse / brig,onse / brig,onse |  | 0.136 |
| `kingfisher_call` | call | fail | 0/3 | 60 | 0.05 | brig,peri,roug,cont / brig,onse,peri,roug,cont / brig,peri,roug,cont |  | 0.987 |
| `leaf_rustle` | thump | PASS | 3/3 | 4 | 0.37 | brig / brig / brig |  | 0.004 |
| `morepork_call` | call | fail | 0/3 | 60 | 0.21 | onse,roug,cont / onse,roug,cont / onse,roug,cont | F-3069 signal flag (rumble) | 0.953 |
| `moth_tap` | thump | fail | 1/3 | 24 | 0.56 | peri / peri,cont / peri,cont | F-3069 partial mismatch | 0.968 |
| `oystercatcher_call` | call | fail | 0/3 | 60 | 0.24 | brig,roug,cont / brig,roug,cont / roug,cont |  | 0.485 |
| `page_turn` | thump | PASS | 3/3 | 8 | 0.35 | - / roug / cont |  | 0.322 |
| `pen_scratch` | thump | fail | 1/3 | 12 | 0.15 | brig,cont / brig,cont / brig |  | 0.335 |
| `penguin_bray` | call | fail | 0/3 | 39 | 0.29 | onse,roug,cont / onse,roug,cont / roug,cont |  | 0.006 |
| `rain_on_roof` | bed | PASS | 3/3 | 1 | 0.44 | - / - / - |  | 0.068 |
| `riroriro_trill` | call | fail | 0/3 | 9 | 0.15 | onse,cont / onse,peri,cont / onse,cont |  | 0.001 |
| `robin_song` | call | PASS | 2/3 | 9 | 0.23 | cont / roug,cont / cont |  | 0.0 |
| `saw_rasp` | bed_like | PASS | 3/3 | 2 | 0.18 | peri / - / peri |  | 0.206 |
| `shingle_drag` | bed | fail | 1/3 | 13 | 0.16 | peri,cont / peri,cont / cont |  | 0.199 |
| `small_birds` | call | PASS | 2/3 | 4 | 0.18 | onse,cont / peri / cont |  | 0.0 |
| `sow_dig` | thump | fail | 1/3 | 16 | 0.44 | onse,cont / peri,cont / brig |  | 0.631 |
| `stream_run` | bed_like | PASS | 3/3 | 7 | 0.23 | onse / onse / onse |  | 0.129 |
| `thunder` | thump | fail | 0/3 | 62 | 0.40 | roug,cont / roug,cont / brig,peri,roug,cont |  | 0.877 |
| `tide_pool_trickle` | bed_like | fail | 0/3 | 9 | 0.10 | onse,roug / onse,roug / onse,roug |  | 0.022 |
| `tui_song` | call | PASS | 2/3 | 3 | 0.32 | - / onse / onse,cont |  | 0.0 |
| `waves_crashing` | bed | fail | 0/3 | 12 | 0.16 | brig,peri,roug / peri,roug / peri,roug |  | 0.198 |
| `waves_on_shingle` | bed | PASS | 2/3 | 2 | 0.15 | brig / brig,onse / brig |  | 0.068 |
| `wind_in_eaves` | bed | fail | 1/3 | 2 | 0.02 | onse,roug / onse,roug / - |  | 0.002 |
| `wind_in_trees` | bed_like | fail | 0/3 | 2 | 0.03 | brig,onse,roug / brig,onse,roug / brig,onse,roug | F-3069 signal flag (rumble) | 0.998 |
| `window_rattle` | thump | PASS | 3/3 | 20 | 0.53 | roug / roug / roug |  | 0.771 |
| `wood_haul_clatter` | thump | PASS | 3/3 | 21 | 0.32 | cont / cont / cont |  | 0.063 |
| `wood_pigeon` | call | fail | 0/3 | 53 | 0.29 | brig,peri,roug,cont / brig,onse,peri,roug,cont / brig,peri,roug,cont | F-3069 signal flag | 0.306 |
| `wood_snap` | thump | fail | 0/3 | 47 | 0.24 | roug,cont / brig,roug,cont / roug,cont |  | 0.962 |
| `woodpile_settle` | thump | fail | 0/3 | 50 | 0.18 | onse,peri,cont / brig,peri / brig,peri |  | 0.167 |
| `wren_scold` | call | fail | 1/3 | 9 | 0.13 | roug / roug,cont / roug,cont | F-3069 character mismatch | 0.0 |

Axis abbreviations: brig = brightness, onse = onset, peri = periodicity, roug = roughness, cont = continuity.

## Honest limits

- Signal analysis only; no one listened. The recordings are single public clips, with Freesound previews as lossy mp3, so one recording per key stands in for the key's sound.
- The thirds mapping treats every file as one onset/peak/tail arc, but many files hold several calls. It was chosen up front rather than per file, and it is one of several defensible mappings.
- Energy is uncalibrated across files, so it is not in the envelope (sheet section 3). Only its within-file contour is checked (S3).
- tau = 0.25 and the 4-of-5 and 2-of-3 rules are reused from Phase 1 and were not tuned. The discrimination flag says the envelope is loose for its pass rate. A tighter envelope would pass even fewer keys.
