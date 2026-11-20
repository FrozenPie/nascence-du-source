# Strings and Sheets Phase 4: event-gated envelope re-run (J-2383, 2026-10-18)

Pre-registered sheet: `strings_sheets_phase4_gated_metric_sheet.md` (commit 330c0722, before the script existed;
amendment A1 commit 427641f7, before any gated verdict was computed). Script: `scripts/strings_phase4_gated_lab.py`
(python -I, scratch copies of the 68 recordings; it imports the J-2372 lab unchanged). Full data:
`strings_sheets_phase4_gated_2026-10-18.json`. Offline only; nothing written to `data/`; nothing reaches Du.
`core/audio_features.py` unchanged. D-0476 / D-0477 are not ruled here.

## Kill rule

G0 held: with no gate the lab code reproduces the features JSON string to a max deviation of 0.0006 (worst
wood_snap onset), under the 0.01 limit. The gated numbers below are read.

## Headline (X = 10 dB over each file's 10th-percentile frame energy)

- **Gated: 23/63 = 36.5%** against the ungated **19/63 = 30.2%** (J-2372). **The 60% bar is NOT MET.**
- Shuffle baseline 27.0% (ungated 25.4%). 0.8 x 36.5% = 29.2%, so the gated result is **discriminating, barely**
  (the ungated one was not). Median own-envelope rank 25.5 of 63 (ungated 19): worse, not better.
- Zero gated seconds (A1, FAIL): distant_surf_boom, morepork_call, tide_pool_trickle. One gated second (point rule):
  bed_watering, bees_in_garden. Over the 60 keys that kept at least one second: 23/60 = 38.3%.
- **Pre-registered reading: gated share < 60%, so the hand-seeded coordinates are wrong on the named axes.** The gate
  removes part of the continuity gap, but not enough to change the verdict. Re-seeding is the founder's call (D-0476).

## Flips against J-2372 (X = 10)

- **fail -> PASS (9):** bed_watering (on 1 gated second, fragile), cat_demand, godwits_overhead, gull_cries,
  moth_tap, oystercatcher_call, pen_scratch, shingle_drag, sow_dig.
- **PASS -> fail (5):** bees_in_garden (only 1 gated second), door_sound, footsteps_floorboards, small_birds,
  waves_on_shingle.
- Net +4.

## Per-axis misses, gated X = 10 (176 vertices) vs J-2372 (189 vertices)

| axis | gated total | above | below | J-2372 total | J-2372 above / below |
|---|---|---|---|---|---|
| continuity | 90 | 51 | 39 | 104 | 92 / 12 |
| roughness | 73 | 22 | 51 | 90 | 40 / 50 |
| onset | 70 | 48 | 22 | 68 | n/a |
| periodicity | 67 | 21 | 46 | 77 | 26 / 49 |
| brightness | 45 | 30 | 15 | 47 | n/a |

Median measured continuity over the gated vertices: **0.45** (ungated 0.82; constructed peak median 0.38). The gate
moves continuity onto the seeds' scale in the median, but the misses now split both ways (51 above, 39 below):
continuity is no longer one-sided background. Onset misses are mostly ABOVE: part of that is the gate's own
artefact (zeroing the background makes every gate opening a spectral-flux onset), so the onset row is the least
trustworthy one here. Over the 40 failing keys, the axes that miss at least once: continuity 30 keys, roughness 26,
onset 25, periodicity 24, brightness 17.

## Secondary reads (X = 10)

- **S5 by archetype:** bed 3/12 (median kept share 0.31), bed_like 2/10 (0.17), call 8/20 (0.36), thump 10/20 (0.38),
  wingbeat 0/1 (0.66). Calls and thumps gain (5 -> 8, 8 -> 10); beds do not, as the sheet's stated limit predicted.
- **S3 energy contour:** 25/58 keys with >= 3 gated seconds agree (ungated 33/63).
- **Excluded keys through the gate:** cat_thump fail (ungated PASS), cat_trill PASS (ungated fail), gate_latch PASS,
  dawn_chorus fail on 3 gated seconds (ungated PASS), log_on_fire PASS. One MISMATCH file now fails its envelope.
- Median kept-frame share over the 63 primary keys: 0.34.

## Sensitivity (never the headline)

| X | pass / 63 | share | baseline | discriminating | zero-second keys | fail->PASS | PASS->fail |
|---|---|---|---|---|---|---|---|
| 6 dB | 19 | 30.2% | 28.4% | no | morepork_call | canopy_drip, godwits_overhead, gull_cries, moth_tap, shingle_drag | bees_in_garden, door_sound, footsteps_floorboards, stream_run, waves_on_shingle |
| **10 dB** | **23** | **36.5%** | **27.0%** | **yes (barely)** | 3 | 9 (above) | 5 (above) |
| 15 dB | 22 | 34.9% | 24.7% | yes | 5 | bed_watering, cat_demand, godwits_overhead, gull_cries, herb_cut, pen_scratch, sow_dig, thunder | bees_in_garden, door_sound, footsteps_floorboards, rain_on_roof, waves_on_shingle |

No gate setting comes near 60%. Four keys flip PASS -> fail at every X (bees_in_garden, door_sound,
footsteps_floorboards, waves_on_shingle), and two flip fail -> PASS at every X (godwits_overhead, gull_cries):
those six are the keys whose verdict the background robustly set. Every other flip depends on X.

## Per-key table (X = 10)

Direction codes: `cont+2` = two vertices above the envelope on continuity, `peri-1` = one below on periodicity.

| key | archetype | J-2372 | gated X=10 | vertices IN | gated s / total s | kept share | axes missed (thirds) | direction of misses |
|---|---|---|---|---|---|---|---|---|
| `bed_watering` | thump | fail | PASS **flip** | 1/1 | 1/12 | 0.014 | - | - |
| `bees_in_garden` | bed_like | PASS | fail **flip** | 0/1 | 1/54 | 0.0 | brig,peri,roug,cont | brig+1 cont-1 peri-1 roug+1 |
| `bellbird_song` | call | fail | fail | 0/3 | 14/25 | 0.217 | onse,cont / onse,peri,roug / onse,roug | cont+1 onse+2 onse-1 peri-1 roug+2 |
| `blackbird_alarm` | call | fail | fail | 1/3 | 8/9 | 0.658 | onse,peri / peri,roug,cont / onse | cont+1 onse-2 peri+2 roug-1 |
| `blackbird_song` | call | fail | fail | 0/3 | 21/44 | 0.28 | onse,cont / onse,cont / onse,cont | cont+3 onse+3 |
| `branches_creak` | thump | fail | fail | 0/3 | 14/46 | 0.162 | onse,peri,roug / onse,peri,roug / onse,peri,roug,cont | cont-1 onse+3 peri+3 roug-3 |
| `canopy_drip` | thump | fail | fail | 0/3 | 12/32 | 0.02 | roug,cont / roug,cont / roug,cont | cont-3 roug+3 |
| `cat_chatter` | bed_like | fail | fail | 0/3 | 3/3 | 0.548 | onse,peri,roug / peri,roug,cont / brig,peri,roug,cont | brig-1 cont+2 onse-1 peri-3 roug-3 |
| `cat_demand` | call | fail | PASS **flip** | 2/3 | 28/33 | 0.129 | peri,roug / peri / peri | peri-3 roug-1 |
| `cat_lapping` | bed | fail | fail | 0/3 | 61/63 | 0.19 | onse,peri,roug,cont / onse,peri,roug / onse,peri,roug,cont | cont-2 onse-3 peri-3 roug+3 |
| `cat_meow_at_door` | call | fail | fail | 0/3 | 31/37 | 0.39 | onse,cont / onse,cont / onse,cont | cont+3 onse+3 |
| `cat_purr` | bed | fail | fail | 0/3 | 16/18 | 0.737 | onse,peri / onse,peri / onse,peri | onse+3 peri-3 |
| `cat_yowl_cargo` | call | fail | fail | 0/3 | 45/46 | 0.776 | brig,onse,peri,cont / roug,cont / roug,cont | brig+1 cont+3 onse+1 peri+1 roug-2 |
| `chair_desk_scrape` | thump | fail | fail | 0/3 | 26/28 | 0.889 | peri,roug,cont / peri,roug,cont / peri,roug,cont | cont+3 peri+3 roug-3 |
| `cicada_chorus` | bed | fail | fail | 0/3 | 13/16 | 0.443 | peri,roug / peri,roug / onse,peri,cont | cont-1 onse+1 peri-3 roug-2 |
| `clock_tick` | bed_like | fail | fail | 0/3 | 61/65 | 0.215 | onse,peri,roug,cont / onse,peri,roug,cont / onse,peri,roug,cont | cont-3 onse-3 peri-3 roug+3 |
| `cricket_night` | bed | fail | fail | 0/3 | 78/91 | 0.32 | brig,onse,peri,cont / onse,peri,roug,cont / onse,peri,roug,cont | brig+1 cont-3 onse+3 peri-3 roug+2 |
| `cuckoo_call` | call | PASS | PASS | 2/3 | 27/34 | 0.628 | - / onse / onse,peri | onse+2 peri-1 |
| `distant_surf_boom` | bed | fail | fail | 0/0 | 0/63 | 0.0 | (no gated second) | - |
| `door_sound` | thump | PASS | fail **flip** | 1/3 | 9/19 | 0.09 | brig,peri,roug / brig,roug / peri | brig+2 peri+2 roug+2 |
| `embers_settle` | bed | PASS | PASS | 2/3 | 6/6 | 0.276 | brig / brig / brig,peri | brig+3 peri+1 |
| `fantail_chatter` | call | PASS | PASS | 3/3 | 11/13 | 0.724 | - / - / onse | onse-1 |
| `fire_crackle` | bed | fail | fail | 0/3 | 16/17 | 0.303 | onse,peri,cont / onse,cont / onse,cont | cont-3 onse-3 peri+1 |
| `footsteps_floorboards` | thump | PASS | fail **flip** | 1/3 | 23/34 | 0.184 | peri,cont / peri,cont / cont | cont-3 peri-2 |
| `footsteps_grass_soil` | thump | fail | fail | 1/3 | 11/12 | 0.492 | brig,peri,cont / peri,cont / cont | brig+1 cont-3 peri-2 |
| `footsteps_leafmould` | bed_like | fail | fail | 0/3 | 24/24 | 0.436 | peri,roug / peri,roug / peri,roug | peri-3 roug+3 |
| `footsteps_shingle` | bed_like | fail | fail | 0/3 | 4/14 | 0.014 | onse,peri,roug,cont / onse,peri,cont / onse,peri,roug,cont | cont-3 onse-3 peri-3 roug-2 |
| `godwits_overhead` | call | fail | PASS **flip** | 3/3 | 6/17 | 0.071 | onse / - / cont | cont-1 onse+1 |
| `gull_cries` | call | fail | PASS **flip** | 3/3 | 10/21 | 0.115 | roug / roug / roug | roug-3 |
| `herb_cut` | thump | fail | fail | 1/3 | 4/4 | 0.585 | brig,roug,cont / brig,cont / cont | brig+2 cont+3 roug+1 |
| `kereru_wingbeats` | wingbeat | fail | fail | 0/3 | 4/6 | 0.657 | brig,onse,cont / brig,onse,roug / brig,onse | brig+3 cont+1 onse+1 onse-2 roug+1 |
| `kettle_fill` | thump | PASS | PASS | 3/3 | 8/9 | 0.755 | cont / cont / cont | cont+2 cont-1 |
| `kettle_pour` | thump | PASS | PASS | 2/3 | 13/15 | 0.242 | brig / onse,cont / - | brig-1 cont+1 onse+1 |
| `kettle_sing` | bed_like | fail | fail | 1/3 | 19/25 | 0.493 | brig,onse / brig / brig,onse | brig-3 onse+2 |
| `kingfisher_call` | call | fail | fail | 0/3 | 20/24 | 0.748 | brig,onse,peri,roug,cont / brig,onse,peri,roug,cont / brig,peri,roug,cont | brig-3 cont+3 onse-2 peri-3 roug-3 |
| `leaf_rustle` | thump | PASS | PASS | 3/3 | 44/47 | 0.409 | brig / brig / brig | brig+3 |
| `morepork_call` | call | fail | fail | 0/0 | 0/17 | 0.0 | (no gated second) | - |
| `moth_tap` | thump | fail | PASS **flip** | 2/3 | 3/3 | 0.154 | peri / brig,peri / peri | brig-1 peri-3 |
| `oystercatcher_call` | call | fail | PASS **flip** | 3/3 | 24/33 | 0.139 | roug / roug / roug | roug-3 |
| `page_turn` | thump | PASS | PASS | 3/3 | 19/20 | 0.488 | - / - / cont | cont+1 |
| `pen_scratch` | thump | fail | PASS **flip** | 2/3 | 6/6 | 0.435 | brig / brig,cont / brig | brig+3 cont+1 |
| `penguin_bray` | call | fail | fail | 1/3 | 11/16 | 0.468 | roug / onse,roug,cont / roug,cont | cont+2 onse+1 roug-3 |
| `rain_on_roof` | bed | PASS | PASS | 2/3 | 11/25 | 0.024 | cont / onse,cont / cont | cont-3 onse-1 |
| `riroriro_trill` | call | fail | fail | 0/3 | 14/18 | 0.651 | onse,cont / onse,peri,cont / onse,cont | cont+3 onse+3 peri-1 |
| `robin_song` | call | PASS | PASS | 3/3 | 33/35 | 0.701 | cont / cont / cont | cont+3 |
| `saw_rasp` | bed_like | PASS | PASS | 3/3 | 12/13 | 0.83 | peri / - / peri | peri-2 |
| `shingle_drag` | bed | fail | PASS **flip** | 3/3 | 21/63 | 0.081 | onse / cont / onse | cont-1 onse+2 |
| `small_birds` | call | PASS | fail **flip** | 1/3 | 14/22 | 0.393 | onse,cont / peri,cont / cont | cont+3 onse+1 peri+1 |
| `sow_dig` | thump | fail | PASS **flip** | 3/3 | 18/19 | 0.395 | onse / peri / brig | brig+1 onse+1 peri+1 |
| `stream_run` | bed_like | PASS | PASS | 2/3 | 45/126 | 0.015 | cont / onse,cont / cont | cont-3 onse+1 |
| `thunder` | thump | fail | fail | 0/3 | 58/90 | 0.262 | roug,cont / roug,cont / brig,roug,cont | brig+1 cont+3 roug-3 |
| `tide_pool_trickle` | bed_like | fail | fail | 0/0 | 0/30 | 0.0 | (no gated second) | - |
| `tui_song` | call | PASS | PASS | 2/3 | 3/5 | 0.323 | - / onse,roug / - | onse+1 roug-1 |
| `waves_crashing` | bed | fail | fail | 0/3 | 71/85 | 0.552 | brig,peri,roug / peri,roug / peri,roug | brig+1 peri+3 roug-3 |
| `waves_on_shingle` | bed | PASS | fail **flip** | 1/3 | 75/134 | 0.445 | brig,onse / brig,onse / onse | brig+2 onse+3 |
| `wind_in_eaves` | bed | fail | fail | 0/3 | 49/59 | 0.717 | onse,roug / onse,roug / onse,roug | onse+3 roug-3 |
| `wind_in_trees` | bed_like | fail | fail | 0/3 | 52/103 | 0.128 | brig,onse,roug,cont / brig,onse,roug,cont / brig,onse,roug,cont | brig-3 cont-3 onse+3 roug-3 |
| `window_rattle` | thump | PASS | PASS | 3/3 | 33/40 | 0.363 | roug / roug / roug | roug-3 |
| `wood_haul_clatter` | thump | PASS | PASS | 3/3 | 11/11 | 0.882 | cont / cont / cont | cont+3 |
| `wood_pigeon` | call | fail | fail | 0/3 | 7/14 | 0.111 | brig,onse,peri,roug / brig,onse,peri / brig,peri,cont | brig+3 cont-1 onse+2 peri-3 roug+1 |
| `wood_snap` | thump | fail | fail | 0/3 | 7/8 | 0.338 | brig,roug,cont / brig,roug,cont / brig,roug,cont | brig-3 cont+3 roug-3 |
| `woodpile_settle` | thump | fail | fail | 0/3 | 9/9 | 0.723 | onse,peri,cont / brig,peri / brig,peri | brig+2 cont+1 onse+1 peri+3 |
| `wren_scold` | call | fail | fail | 1/3 | 8/10 | 0.326 | roug / roug,cont / roug,cont | cont+2 roug-3 |
