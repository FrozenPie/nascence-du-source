# Strings and Sheets Phase 4 - offline features for the 68 recordings (J-2027, 2026-10-18)

Extractor: `core/audio_features.py` `extract()` (the J-1474 six-axis string fold-in), run through `scripts/ribbon_lab.py` `process_piece()` for the normalised measured string and the ribbon against each file's own per-section summary. Inputs were scratch copies of `data/sound_recordings/` (gitignored); nothing was written to `data/` or any Du store, and nothing reaches Du. Freesound files are HQ preview mp3 (lossy). Full data: `strings_sheets_phase4_features_2026-10-18.json` (per key: whole-file fields, sections with `string6`, the normalised measured string, ribbon width/twist, kill-rule deviation, and the J-2027 signal-review metrics).

## Honest limits

- The ribbon here is measured string vs that file's OWN per-section summary (the Phase 0 definition), not measured vs the hand-seeded constructed string. Phase 4's real metric (measured within the constructed string's realness envelope for >=60% of keys) is not computed here; it is a follow-up.
- Normalisation is per file (energy / the file's max section energy), so the energy axis is not comparable across keys in absolute terms.
- Files of about 1 s (`cat_trill`, `cat_thump`) give a one-second string, so width is ~0 and twist is undefined.
- 17 of 68 files hold >70% of their energy below 300 Hz; on the rumble-dominated ones the energy axis tracks rumble (see the manifest's review section).
- Kill rule (ribbon_lab, tolerance 0.02 on the three cached axes): triggered on 0 of 68 files.

## Per-key summary

| key | dur s | sections | brightness Hz | onset density /s | tempo bpm | mode | width6 mean | width6 p90 | twist6 deg/s | kill max dev |
|---|---|---|---|---|---|---|---|---|---|---|
| `bed_watering` | 11.8 | 1 | 3098.6 | 2.91 | 161.5 | minor | 0.5987 | 1.1535 | 67.64 | 0.0000 |
| `bees_in_garden` | 54.0 | 5 | 3033.5 | 2.06 | 107.7 | major | 0.4258 | 0.7262 | 54.6 | 0.0005 |
| `bellbird_song` | 24.9 | 3 | 3175.8 | 0.89 | 136.0 | major | 0.7421 | 1.0171 | 37.68 | 0.0006 |
| `blackbird_alarm` | 9.0 | 1 | 3077.8 | 2.02 | 136.0 | minor | 1.0483 | 1.1859 | 43.67 | 0.0002 |
| `blackbird_song` | 44.1 | 3 | 1865.6 | 1.66 | 161.5 | minor | 0.7766 | 1.1164 | 62.69 | 0.0005 |
| `branches_creak` | 45.8 | 4 | 1676.0 | 2.01 | 184.6 | minor | 0.4773 | 0.9038 | 66.81 | 0.0004 |
| `canopy_drip` | 31.4 | 3 | 4272.4 | 3.45 | 99.4 | minor | 0.2237 | 0.3759 | 95.19 | 0.0005 |
| `cat_chatter` | 3.0 | 1 | 1638.5 | 3.08 | 107.7 | minor | 0.2761 | 0.3628 | 119.3 | 0.0005 |
| `cat_demand` | 33.0 | 4 | 1346.9 | 1.0 | 117.5 | major | 0.4464 | 0.6558 | 73.72 | 0.0006 |
| `cat_lapping` | 62.4 | 4 | 3707.7 | 0.24 | 198.8 | minor | 0.3398 | 0.5552 | 72.35 | 0.0005 |
| `cat_meow_at_door` | 36.8 | 4 | 2637.0 | 1.96 | 198.8 | minor | 0.7564 | 1.0024 | 94.98 | 0.0004 |
| `cat_purr` | 17.5 | 2 | 426.4 | 2.24 | 92.3 | major | 0.5149 | 0.8483 | 74.38 | 0.0005 |
| `cat_thump` | 1.0 | 1 | 442.3 | 3.31 | 95.7 | major | 0.0002 | 0.0002 | - | 0.0002 |
| `cat_trill` | 0.9 | 1 | 708.2 | 2.53 | 107.7 | minor | 0.0004 | 0.0004 | - | 0.0004 |
| `cat_yowl_cargo` | 45.5 | 3 | 2726.2 | 1.54 | 184.6 | major | 0.7132 | 1.0099 | 71.83 | 0.0006 |
| `chair_desk_scrape` | 27.2 | 3 | 1736.0 | 2.84 | 136.0 | minor | 0.6514 | 1.1406 | 56.71 | 0.0005 |
| `cicada_chorus` | 16.0 | 1 | 3128.0 | 3.83 | 123.0 | major | 0.7331 | 0.9972 | 35.57 | 0.0003 |
| `clock_tick` | 64.3 | 4 | 1704.0 | 1.45 | 60.1 | major | 0.2786 | 0.5587 | 60.9 | 0.0006 |
| `cricket_night` | 90.6 | 4 | 4148.4 | 1.18 | 215.3 | minor | 0.6005 | 0.7995 | 79.84 | 0.0006 |
| `cuckoo_call` | 33.9 | 3 | 3632.7 | 1.86 | 99.4 | minor | 0.5917 | 1.1743 | 52.1 | 0.0004 |
| `dawn_chorus` | 41.9 | 4 | 3308.3 | 1.15 | 198.8 | minor | 0.3507 | 0.6906 | 77.74 | 0.0005 |
| `distant_surf_boom` | 62.4 | 5 | 1538.9 | 4.14 | 107.7 | minor | 0.4544 | 0.7963 | 39.81 | 0.0006 |
| `door_sound` | 18.6 | 2 | 2336.8 | 1.19 | 92.3 | minor | 0.548 | 0.7676 | 85.66 | 0.0006 |
| `embers_settle` | 5.9 | 1 | 3337.6 | 2.07 | 66.3 | major | 0.3926 | 0.6591 | 70.88 | 0.0000 |
| `fantail_chatter` | 12.6 | 1 | 3924.8 | 0.8 | 73.8 | minor | 0.4825 | 0.938 | 63.08 | 0.0002 |
| `fire_crackle` | 16.7 | 2 | 3778.7 | 0.48 | 161.5 | minor | 0.3563 | 0.6321 | 90.6 | 0.0006 |
| `footsteps_floorboards` | 33.4 | 4 | 2315.7 | 1.5 | 161.5 | minor | 0.3774 | 0.6736 | 75.6 | 0.0006 |
| `footsteps_grass_soil` | 11.4 | 1 | 1005.1 | 1.06 | 129.2 | minor | 0.5755 | 0.8968 | 36.75 | 0.0002 |
| `footsteps_leafmould` | 23.8 | 3 | 2768.0 | 3.12 | 89.1 | minor | 0.4175 | 0.6974 | 61.2 | 0.0006 |
| `footsteps_shingle` | 13.2 | 1 | 1616.9 | 0.84 | 136.0 | minor | 0.3818 | 0.5128 | 56.48 | 0.0002 |
| `gate_latch` | 1.8 | 1 | 3766.2 | 1.16 | 215.3 | minor | 0.6323 | 0.9536 | 107.38 | 0.0003 |
| `godwits_overhead` | 16.5 | 3 | 3317.1 | 1.53 | 95.7 | minor | 0.5092 | 0.755 | 86.21 | 0.0002 |
| `gull_cries` | 21.0 | 2 | 1192.6 | 1.63 | 78.3 | minor | 0.5553 | 0.7219 | 97.48 | 0.0003 |
| `herb_cut` | 3.8 | 1 | 4974.6 | 1.35 | 69.8 | major | 0.3671 | 0.4628 | 69.48 | 0.0005 |
| `kereru_wingbeats` | 5.6 | 1 | 2811.0 | 1.8 | 172.3 | minor | 0.9869 | 1.2508 | 45.7 | 0.0006 |
| `kettle_fill` | 8.5 | 1 | 3013.8 | 0.59 | 172.3 | minor | 0.6436 | 1.0812 | 53.55 | 0.0001 |
| `kettle_pour` | 14.6 | 1 | 1959.3 | 2.42 | 107.7 | minor | 0.6005 | 0.8059 | 43.17 | 0.0006 |
| `kettle_sing` | 25.1 | 3 | 2060.6 | 4.33 | 107.7 | major | 0.3809 | 0.8424 | 76.93 | 0.0004 |
| `kingfisher_call` | 23.5 | 2 | 909.2 | 2.35 | 123.0 | major | 0.7374 | 1.1835 | 38.14 | 0.0006 |
| `leaf_rustle` | 46.1 | 4 | 4666.8 | 0.91 | 51.7 | minor | 0.4718 | 0.7972 | 84.46 | 0.0006 |
| `log_on_fire` | 31.2 | 3 | 2170.3 | 0.77 | 63.0 | minor | 0.3572 | 0.547 | 75.39 | 0.0006 |
| `morepork_call` | 16.8 | 2 | 1731.0 | 2.39 | 58.7 | minor | 0.3267 | 0.9779 | 82.59 | 0.0001 |
| `moth_tap` | 2.8 | 1 | 2188.7 | 2.94 | 107.7 | minor | 0.4187 | 0.5122 | 119.15 | 0.0006 |
| `oystercatcher_call` | 32.2 | 4 | 1615.2 | 3.05 | 53.8 | major | 0.3996 | 0.7907 | 83.87 | 0.0005 |
| `page_turn` | 19.3 | 2 | 3123.5 | 0.78 | 172.3 | major | 0.5996 | 0.9138 | 80.08 | 0.0003 |
| `pen_scratch` | 6.0 | 1 | 4522.4 | 2.87 | 92.3 | minor | 0.3267 | 0.4868 | 66.86 | 0.0001 |
| `penguin_bray` | 15.5 | 1 | 2202.0 | 2.72 | 161.5 | minor | 0.8395 | 1.3153 | 53.18 | 0.0001 |
| `rain_on_roof` | 24.8 | 3 | 2359.0 | 3.48 | 123.0 | minor | 0.2357 | 0.4126 | 94.4 | 0.0004 |
| `riroriro_trill` | 17.2 | 3 | 2746.7 | 4.92 | 117.5 | minor | 0.5619 | 1.0979 | 83.51 | 0.0004 |
| `robin_song` | 34.6 | 4 | 4916.0 | 3.1 | 215.3 | minor | 0.4869 | 0.7146 | 88.2 | 0.0005 |
| `saw_rasp` | 12.2 | 1 | 3670.6 | 2.14 | 89.1 | major | 0.4556 | 1.1665 | 69.91 | 0.0005 |
| `shingle_drag` | 62.3 | 5 | 2999.2 | 3.01 | 143.6 | minor | 0.5493 | 0.979 | 52.86 | 0.0006 |
| `small_birds` | 21.3 | 3 | 3907.0 | 2.78 | 143.6 | minor | 0.7852 | 1.1205 | 51.84 | 0.0005 |
| `sow_dig` | 18.5 | 3 | 2372.0 | 2.28 | 215.3 | minor | 0.4025 | 0.6839 | 83.67 | 0.0003 |
| `stream_run` | 125.9 | 10 | 3064.0 | 4.16 | 198.8 | minor | 0.2103 | 0.3605 | 88.45 | 0.0006 |
| `thunder` | 89.7 | 6 | 2110.9 | 2.58 | 129.2 | major | 0.4884 | 0.7775 | 43.4 | 0.0004 |
| `tide_pool_trickle` | 29.9 | 3 | 3905.4 | 4.63 | 117.5 | minor | 0.3456 | 0.6911 | 75.64 | 0.0005 |
| `tui_song` | 4.6 | 1 | 2782.8 | 1.55 | 215.3 | minor | 0.6659 | 1.0362 | 47.55 | 0.0005 |
| `waves_crashing` | 84.8 | 4 | 2255.9 | 2.53 | 161.5 | minor | 0.6758 | 0.9881 | 67.04 | 0.0003 |
| `waves_on_shingle` | 134.0 | 9 | 2552.3 | 2.92 | 123.0 | minor | 0.7409 | 1.073 | 34.01 | 0.0003 |
| `wind_in_eaves` | 58.2 | 4 | 1075.2 | 2.25 | 136.0 | minor | 0.5504 | 0.8463 | 50.19 | 0.0002 |
| `wind_in_trees` | 102.9 | 8 | 194.2 | 2.16 | 123.0 | major | 0.4045 | 0.6583 | 56.38 | 0.0006 |
| `window_rattle` | 39.4 | 4 | 1564.0 | 0.66 | 103.4 | minor | 0.5633 | 0.8744 | 90.65 | 0.0006 |
| `wood_haul_clatter` | 10.5 | 1 | 2419.8 | 4.99 | 172.3 | minor | 0.4314 | 1.3162 | 65.59 | 0.0005 |
| `wood_pigeon` | 13.7 | 1 | 3345.7 | 2.43 | 89.1 | minor | 0.532 | 0.7069 | 44.33 | 0.0002 |
| `wood_snap` | 7.9 | 1 | 1135.4 | 1.28 | 99.4 | major | 0.3882 | 0.6561 | 88.31 | 0.0004 |
| `woodpile_settle` | 8.8 | 1 | 3167.5 | 2.53 | 143.6 | major | 1.074 | 1.4049 | 29.19 | 0.0000 |
| `wren_scold` | 9.1 | 1 | 9816.9 | 2.21 | 161.5 | minor | 0.5861 | 0.9906 | 63.42 | 0.0005 |

Across the 66 files longer than 1.5 s: width6 mean median 0.499 (range 0.210-1.074); twist6 mean median 68.6 deg/s (range 29.2-119.3).
