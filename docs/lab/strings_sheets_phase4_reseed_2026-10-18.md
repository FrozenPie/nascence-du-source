# Strings and Sheets Phase 4: reviewed re-seed list for the named axes (J-2395, D-0476, 2026-10-18)

Ruling: **D-0476** (travis, 2026-10-18): re-seed ONLY the axes F-3090's per-key table names, for the keys that fail
the envelope test, as a reviewed list, because the change reaches `core/soundscape.py` `_SOUNDS`. This job also
folds in **J-2399** (F-3098): the D-0477 re-pick keys are now measured (J-2397), so they are on the list under the
same rule instead of being excluded. Offline only. `core/audio_features.py` is never edited. Nothing written under
`data/`.

Sections 1 to 3 (the rule and the re-run) were written and committed **before** the proposal script ran and before
`_SOUNDS` was touched. They were written after F-3081 / F-3090 / F-3098 were read, which cannot be avoided: those
tables are what D-0476 rules on.

## 1. Which keys, which axes

- **Source table.** The J-2383 gated (X = 10 dB) per-key table (`strings_sheets_phase4_gated_2026-10-18.json`,
  `per_key_x10`), which is F-3090's per-key table. A key is a candidate iff its gated verdict is **fail**.
- **Re-picked keys** (dawn_chorus, log_on_fire, morepork_call, wind_in_trees; J-2397 window WAVs): measured
  here through the J-2383 gate code unchanged (`string_gated`, X = 10) on J-2397's windows, so every key's named
  axes come from the same gated measurement. F-3098's ungated axis names for them are shown next to it.
- **Named axes.** For a candidate key, the axes that miss on at least one gated third (the union over the
  three thirds).
- **Onset exception.** F-3090 states the gated onset row is partly a gate artefact (zeroing the background makes
  each gate opening a spectral-flux onset). So onset is re-seeded only when it is named by the gated table AND it
  also misses on at least one ungated (J-2372) third. Otherwise the row is listed with `applied = false`.
- **Not re-seeded (listed).** wood_pigeon (a D-0477 key whose swap did not happen: the XC933702 licence was
  unreadable, and its current file is the one F-3069 flagged); moth_tap (constructed-only per D-0477); any
  candidate with **fewer than 3 gated seconds** (no three thirds to fit; this covers the zero-second keys of
  amendment A1 and the one-second keys). Passing keys are never re-seeded, including log_on_fire.
- energy is never re-seeded (it is not in the envelope, per the J-2372 sheet section 3).

## 2. The new seed value

The constructed string is `build_all()` (scripts/sound_strings_phase1_dryrun.py): periodicity, roughness and
continuity are held fixed across onset/peak/tail; brightness and onset move by fixed archetype offsets around
the `_SOUNDS` point (peak offset 0).

- **Timbre axes** (periodicity, roughness, continuity): new seed = mean of the three **gated** measured thirds on
  that axis.
- **brightness**: new seed s solves mean over thirds of (measured_i - offset_i(s)) = s, using the archetype offsets
  `build_string()` actually produces (clipping included; three fixed-point iterations), on the **gated** thirds.
- **onset** (only when the exception above allows it): the same fit on the **ungated** J-2372 thirds.
- Clipped to [0, 1], rounded to 2 decimals (the registry's own precision). Timbre axes are fitted before
  brightness/onset, because a call's offsets scale with its continuity.
- Only the listed (key, axis) pairs change. A gate in the test script (T0) refuses to run if the edited `_SOUNDS`
  differs from the proposal anywhere else.

## 3. Gates and the re-run

- **R0a**: on J-2397's four window WAVs, the gate code with no gate reproduces J-2397's `string6` within 0.01.
- **R0b**: this pipeline reproduces J-2383's gated vertices for cat_purr, gull_cries and wren_scold within 0.002.
- **T0**: the `_SOUNDS` edit equals the proposal exactly.
- **T1**: before the re-seed, the J-2372 test reproduces J-2397's read (a) 19/62 and read (b) 20/64 with their
  baselines.
- **T2**: before the re-seed, the gated code reproduces J-2383's 23/63.
- **Headline (the D-0476 defeater's own test):** the J-2372 envelope test, **unchanged** (no gate), on the
  re-seeded strings. Denominator = read (b): the 64 keys with a recording of at least 3 seconds, the four re-picked
  keys on their new files, moth_tap out. Read (a) (dawn_chorus and log_on_fire out, n = 62) is also reported.
  Bar 60%; NON-DISCRIMINATING if shuffle baseline >= 0.8 x share.
- **Secondary:** the J-2383 gated test on the same denominators. Stated now: it is **in-sample** for the
  re-seeded axes (the new seeds were fitted to those gated thirds), so a higher gated share is expected by
  construction and is not evidence on its own. The shuffle baseline is the part of it that can still fail.
- **Defeater reading (D-0476).** It fires if the re-seeded J-2372 test still fails 60% OR is non-discriminating.
  Its second branch (D-0477 re-picks changing more than 5 primary verdicts) is read from J-2397.

## 4. The reviewed list

Produced by `python -I scripts/strings_phase4_reseed_lab.py propose` (full data:
`strings_sheets_phase4_reseed_proposal_2026-10-18.json`, which also stores the pre-re-seed constructed strings).
Committed **before** `core/soundscape.py` was edited.

**Gates.** R0a held: the window WAVs reproduce J-2397's string6 to a max deviation of 0.0005 (wind_in_trees
roughness). R0b held: J-2383's gated vertices reproduce to 0.0005.

**Count.** 40 keys fail the gated test (37 on the J-2383 table excluding the four re-picked keys, plus dawn_chorus
and wind_in_trees on their new files; morepork_call and log_on_fire PASS gated on their new files). 4 are not
re-seeded: bees_in_garden (1 gated second), distant_surf_boom and tide_pool_trickle (0 gated seconds), wood_pigeon
(re-pick not done). moth_tap is constructed-only. **36 keys, 116 (key, axis) rows, 115 applied** (dawn_chorus onset
is not applied by the onset exception). 41 rows shift a seed by 0.40 or more: those are flagged below.

**The re-picked keys, against F-3098's axis names (J-2399).** dawn_chorus: F-3098 names brightness and continuity;
the gated table adds onset, which the onset exception drops, so brightness and continuity are re-seeded, the same
two axes. wind_in_trees: F-3098 names brightness and periodicity; the gated table also names roughness and onset
(onset also misses ungated), so four axes are re-seeded. morepork_call: F-3098 names onset and roughness from the
ungated test, but on the new file it PASSES the gated test (2+ thirds in; onset is its only gated miss), so under
the rule it is **not** re-seeded and stays on the ungated failing list. log_on_fire passes both tests; its ungated
tail-third misses (onset, roughness, continuity) are reported and not re-seeded.

**What a reviewer should look at first.** The large shifts. Several contradict the key's own semantic line in
`scripts/sound_strings_phase1_dryrun.py` `_SNIPPETS`, which points at the recording rather than the seed:
`kingfisher_call` brightness 0.75 -> 0.12 and continuity 0.18 -> 0.91 (a "dry staccato kek-kek-kek" measured as a
dark continuous sound); `wood_snap` continuity 0.08 -> 0.59 and brightness 0.55 -> 0.12 ("a single crack");
`herb_cut` continuity 0.05 -> 0.69 ("a single snip"); `clock_tick` continuity 0.95 -> 0.38 and periodicity
0.98 -> 0.56 (a running clock). Under D-0476 these are applied as ruled, not filtered by judgement; each is a
candidate for a by-ear check of its file, and a wrong file there would mean the seed was right.

**Blast radius of the edit** (read from the code, not run live). `_SOUNDS` coords reach: `coords()` /
`distance()` / `neighbours()` / `distance_to_point()`; `_felt_shadow()` (observe-only affect nudge, which also
threads into `fragment_context.sound_felt_valence/arousal` because `SOUND_STRING_FIELDS = True`); the
`fragment_context.sound_onset/peak/tail` JSON written per sound fragment (new fragments carry the new point, old
ones keep the old: a mixed population); `felt_recall`'s cross-key coordinate match (off: `SOUND_COORD_MATCH =
False`); and `build_all()`. The Phase 1 shadow (`core/sound_string_shadow.py`) does **not** read `_SOUNDS`: it reads
the sidecar `data/sound_strings_constructed.json`, which only `scripts/sound_strings_phase1_dryrun.py` regenerates.
That sidecar is still dated 2026-10-08, before J-2067 (moth_tap onset vertex still equals its peak), so neither
J-2067's fix nor this re-seed reaches the shadow until it is regenerated before a boot.

| key | archetype | axis | old seed | measured thirds (onset/peak/tail) | target | envelope before | gated miss dir | proposed seed | delta | review flag |
|---|---|---|---|---|---|---|---|---|---|---|
| `bellbird_song` | call | continuity | 0.30 | 0.61 / 0.36 / 0.36 | gated | 0.05-0.55 | + | **0.45** | +0.15 |  |
| `bellbird_song` | call | periodicity | 0.55 | 0.57 / 0.24 / 0.51 | gated | 0.30-0.80 | - | **0.44** | -0.11 |  |
| `bellbird_song` | call | roughness | 0.08 | 0.24 / 0.48 / 0.34 | gated | 0.00-0.33 | ++ | **0.35** | +0.27 |  |
| `bellbird_song` | call | onset | 0.40 | 0.88 / 0.00 / 0.80 | ungated | 0.04-0.65 | +-+ | **0.62** | +0.22 |  |
| `blackbird_alarm` | call | continuity | 0.15 | 0.00 / 0.85 / 0.00 | gated | 0.00-0.40 | + | **0.28** | +0.13 |  |
| `blackbird_alarm` | call | periodicity | 0.55 | 0.86 / 0.86 / 0.58 | gated | 0.30-0.80 | ++ | **0.77** | +0.22 |  |
| `blackbird_alarm` | call | roughness | 0.70 | 0.53 / 0.25 / 0.55 | gated | 0.45-0.95 | - | **0.44** | -0.26 |  |
| `blackbird_alarm` | call | onset | 0.90 | 0.00 / 0.85 / 0.00 | ungated | 0.54-1.00 | -- | **0.35** | -0.55 | **large shift (>=0.40)** |
| `blackbird_song` | call | continuity | 0.35 | 0.63 / 0.71 / 0.72 | gated | 0.10-0.60 | +++ | **0.69** | +0.34 |  |
| `blackbird_song` | call | onset | 0.45 | 0.64 / 0.80 / 0.80 | ungated | 0.10-0.70 | +++ | **0.80** | +0.35 |  |
| `branches_creak` | thump | continuity | 0.60 | 0.71 / 0.78 / 0.27 | gated | 0.35-0.85 | - | **0.58** | -0.02 |  |
| `branches_creak` | thump | periodicity | 0.15 | 0.64 / 0.51 / 0.57 | gated | 0.00-0.40 | +++ | **0.57** | +0.42 | **large shift (>=0.40)** |
| `branches_creak` | thump | roughness | 0.62 | 0.16 / 0.18 / 0.21 | gated | 0.37-0.87 | --- | **0.18** | -0.44 | **large shift (>=0.40)** |
| `branches_creak` | thump | onset | 0.25 | 0.60 / 0.60 / 0.16 | ungated | 0.00-0.50 | +++ | **0.63** | +0.38 |  |
| `canopy_drip` | thump | continuity | 0.40 | 0.07 / 0.08 / 0.07 | gated | 0.15-0.65 | --- | **0.07** | -0.33 |  |
| `canopy_drip` | thump | roughness | 0.22 | 0.60 / 0.64 / 0.66 | gated | 0.00-0.47 | +++ | **0.63** | +0.41 | **large shift (>=0.40)** |
| `cat_chatter` | bed_like | continuity | 0.25 | 0.42 / 0.51 / 0.72 | gated | 0.00-0.50 | ++ | **0.55** | +0.30 |  |
| `cat_chatter` | bed_like | periodicity | 0.60 | 0.20 / 0.16 / 0.22 | gated | 0.35-0.85 | --- | **0.19** | -0.41 | **large shift (>=0.40)** |
| `cat_chatter` | bed_like | roughness | 0.60 | 0.00 / 0.01 / 0.00 | gated | 0.35-0.85 | --- | **0.00** | -0.60 | **large shift (>=0.40)** |
| `cat_chatter` | bed_like | brightness | 0.65 | 0.40 / 0.44 / 0.33 | gated | 0.37-0.90 | - | **0.41** | -0.24 |  |
| `cat_chatter` | bed_like | onset | 0.92 | 0.50 / 0.78 / 0.65 | ungated | 0.63-1.00 | - | **0.67** | -0.25 |  |
| `cat_lapping` | bed | continuity | 0.55 | 0.10 / 0.44 / 0.16 | gated | 0.30-0.80 | -- | **0.23** | -0.32 |  |
| `cat_lapping` | bed | periodicity | 0.80 | 0.16 / 0.27 / 0.30 | gated | 0.55-1.00 | --- | **0.24** | -0.56 | **large shift (>=0.40)** |
| `cat_lapping` | bed | roughness | 0.20 | 0.62 / 0.68 / 0.66 | gated | 0.00-0.45 | +++ | **0.65** | +0.45 | **large shift (>=0.40)** |
| `cat_lapping` | bed | onset | 0.85 | 0.22 / 0.50 / 0.55 | ungated | 0.56-1.00 | --- | **0.45** | -0.40 | **large shift (>=0.40)** |
| `cat_meow_at_door` | call | continuity | 0.18 | 0.84 / 0.64 / 0.75 | gated | 0.00-0.43 | +++ | **0.74** | +0.56 | **large shift (>=0.40)** |
| `cat_meow_at_door` | call | onset | 0.45 | 0.78 / 0.60 / 0.71 | ungated | 0.09-0.70 | +++ | **0.75** | +0.30 |  |
| `cat_purr` | bed | periodicity | 0.95 | 0.16 / 0.34 / 0.25 | gated | 0.70-1.00 | --- | **0.25** | -0.70 | **large shift (>=0.40)** |
| `cat_purr` | bed | onset | 0.05 | 0.32 / 0.51 / 0.59 | ungated | 0.00-0.30 | +++ | **0.50** | +0.45 | **large shift (>=0.40)** |
| `cat_yowl_cargo` | call | continuity | 0.35 | 0.66 / 0.69 / 0.72 | gated | 0.10-0.60 | +++ | **0.69** | +0.34 |  |
| `cat_yowl_cargo` | call | periodicity | 0.30 | 0.66 / 0.51 / 0.55 | gated | 0.05-0.55 | + | **0.57** | +0.27 |  |
| `cat_yowl_cargo` | call | roughness | 0.70 | 0.59 / 0.17 / 0.11 | gated | 0.45-0.95 | -- | **0.29** | -0.41 | **large shift (>=0.40)** |
| `cat_yowl_cargo` | call | brightness | 0.35 | 0.73 / 0.39 / 0.34 | gated | 0.00-0.60 | + | **0.55** | +0.20 |  |
| `cat_yowl_cargo` | call | onset | 0.30 | 0.60 / 0.54 / 0.54 | ungated | 0.00-0.55 | + | **0.61** | +0.31 |  |
| `chair_desk_scrape` | thump | continuity | 0.25 | 0.99 / 0.97 / 0.96 | gated | 0.00-0.50 | +++ | **0.97** | +0.72 | **large shift (>=0.40)** |
| `chair_desk_scrape` | thump | periodicity | 0.05 | 0.33 / 0.42 / 0.58 | gated | 0.00-0.30 | +++ | **0.44** | +0.39 |  |
| `chair_desk_scrape` | thump | roughness | 0.75 | 0.31 / 0.29 / 0.26 | gated | 0.50-1.00 | --- | **0.29** | -0.46 | **large shift (>=0.40)** |
| `cicada_chorus` | bed | continuity | 0.95 | 0.71 / 0.98 / 0.46 | gated | 0.70-1.00 | - | **0.72** | -0.23 |  |
| `cicada_chorus` | bed | periodicity | 0.85 | 0.22 / 0.19 / 0.26 | gated | 0.60-1.00 | --- | **0.22** | -0.63 | **large shift (>=0.40)** |
| `cicada_chorus` | bed | roughness | 0.80 | 0.49 / 0.47 / 0.56 | gated | 0.55-1.00 | -- | **0.51** | -0.29 |  |
| `cicada_chorus` | bed | onset | 0.15 | 0.06 / 0.94 / 0.43 | ungated | 0.00-0.40 | + | **0.50** | +0.35 |  |
| `clock_tick` | bed_like | continuity | 0.95 | 0.35 / 0.51 / 0.27 | gated | 0.70-1.00 | --- | **0.38** | -0.57 | **large shift (>=0.40)** |
| `clock_tick` | bed_like | periodicity | 0.98 | 0.56 / 0.55 / 0.56 | gated | 0.73-1.00 | --- | **0.56** | -0.42 | **large shift (>=0.40)** |
| `clock_tick` | bed_like | roughness | 0.15 | 0.52 / 0.49 / 0.60 | gated | 0.00-0.40 | +++ | **0.54** | +0.39 |  |
| `clock_tick` | bed_like | onset | 0.85 | 0.43 / 0.46 / 0.42 | ungated | 0.56-1.00 | --- | **0.46** | -0.39 |  |
| `cricket_night` | bed | continuity | 0.85 | 0.49 / 0.49 / 0.55 | gated | 0.60-1.00 | --- | **0.51** | -0.34 |  |
| `cricket_night` | bed | periodicity | 0.90 | 0.61 / 0.47 / 0.48 | gated | 0.65-1.00 | --- | **0.52** | -0.38 |  |
| `cricket_night` | bed | roughness | 0.30 | 0.49 / 0.57 / 0.58 | gated | 0.05-0.55 | ++ | **0.55** | +0.25 |  |
| `cricket_night` | bed | brightness | 0.60 | 0.89 / 0.80 / 0.68 | gated | 0.32-0.85 | + | **0.81** | +0.21 |  |
| `cricket_night` | bed | onset | 0.25 | 0.55 / 0.35 / 0.43 | ungated | 0.00-0.50 | +++ | **0.47** | +0.22 |  |
| `dawn_chorus` | bed_like | continuity | 0.90 | 0.37 / 0.40 / 0.44 | gated | 0.65-1.00 | --- | **0.40** | -0.50 | **large shift (>=0.40)** |
| `dawn_chorus` | bed_like | brightness | 0.85 | 0.51 / 0.48 / 0.47 | gated | 0.57-1.00 | --- | **0.51** | -0.34 |  |
| `dawn_chorus` | - | onset | 0.3 | - | - | - | - | **not applied** | - | named by the gated table only; the ungated vertices sit inside on onset (gate artefact, F-3090) |
| `door_sound` | thump | periodicity | 0.05 | 0.41 / 0.24 / 0.35 | gated | 0.00-0.30 | ++ | **0.34** | +0.29 |  |
| `door_sound` | thump | roughness | 0.35 | 0.63 / 0.62 / 0.50 | gated | 0.10-0.60 | ++ | **0.58** | +0.23 |  |
| `door_sound` | thump | brightness | 0.35 | 0.69 / 0.69 / 0.52 | gated | 0.00-0.60 | ++ | **0.68** | +0.33 |  |
| `fire_crackle` | bed | continuity | 0.60 | 0.06 / 0.08 / 0.09 | gated | 0.35-0.85 | --- | **0.07** | -0.53 | **large shift (>=0.40)** |
| `fire_crackle` | bed | periodicity | 0.10 | 0.37 / 0.04 / 0.23 | gated | 0.00-0.35 | + | **0.21** | +0.11 |  |
| `fire_crackle` | bed | onset | 0.80 | 0.23 / 0.23 / 0.19 | ungated | 0.51-1.00 | --- | **0.24** | -0.56 | **large shift (>=0.40)** |
| `footsteps_floorboards` | thump | continuity | 0.50 | 0.22 / 0.24 / 0.25 | gated | 0.25-0.75 | --- | **0.24** | -0.26 |  |
| `footsteps_floorboards` | thump | periodicity | 0.75 | 0.40 / 0.46 / 0.51 | gated | 0.50-1.00 | -- | **0.46** | -0.29 |  |
| `footsteps_grass_soil` | thump | continuity | 0.55 | 0.20 / 0.16 / 0.17 | gated | 0.30-0.80 | --- | **0.18** | -0.37 |  |
| `footsteps_grass_soil` | thump | periodicity | 0.80 | 0.53 / 0.48 / 0.65 | gated | 0.55-1.00 | -- | **0.55** | -0.25 |  |
| `footsteps_grass_soil` | thump | brightness | 0.20 | 0.48 / 0.33 / 0.32 | gated | 0.00-0.45 | + | **0.42** | +0.22 |  |
| `footsteps_leafmould` | bed_like | periodicity | 0.80 | 0.21 / 0.24 / 0.20 | gated | 0.55-1.00 | --- | **0.22** | -0.58 | **large shift (>=0.40)** |
| `footsteps_leafmould` | bed_like | roughness | 0.40 | 0.77 / 0.76 / 0.78 | gated | 0.15-0.65 | +++ | **0.77** | +0.37 |  |
| `footsteps_shingle` | bed_like | continuity | 0.70 | 0.08 / 0.02 / 0.02 | gated | 0.45-0.95 | --- | **0.04** | -0.66 | **large shift (>=0.40)** |
| `footsteps_shingle` | bed_like | periodicity | 0.80 | 0.34 / 0.25 / 0.25 | gated | 0.55-1.00 | --- | **0.28** | -0.52 | **large shift (>=0.40)** |
| `footsteps_shingle` | bed_like | roughness | 0.80 | 0.47 / 0.58 / 0.46 | gated | 0.55-1.00 | -- | **0.50** | -0.30 |  |
| `footsteps_shingle` | bed_like | onset | 0.75 | 0.42 / 0.09 / 0.00 | ungated | 0.46-1.00 | --- | **0.19** | -0.56 | **large shift (>=0.40)** |
| `herb_cut` | thump | continuity | 0.05 | 0.43 / 0.63 / 1.00 | gated | 0.00-0.30 | +++ | **0.69** | +0.64 | **large shift (>=0.40)** |
| `herb_cut` | thump | roughness | 0.40 | 0.71 / 0.61 / 0.53 | gated | 0.15-0.65 | + | **0.62** | +0.22 |  |
| `herb_cut` | thump | brightness | 0.55 | 0.86 / 0.85 / 0.70 | gated | 0.20-0.80 | ++ | **0.85** | +0.30 |  |
| `kereru_wingbeats` | wingbeat | continuity | 0.25 | 0.63 / 0.00 / 0.00 | gated | 0.00-0.50 | + | **0.21** | -0.04 |  |
| `kereru_wingbeats` | wingbeat | roughness | 0.45 | 0.67 / 0.72 / 0.59 | gated | 0.20-0.70 | + | **0.66** | +0.21 |  |
| `kereru_wingbeats` | wingbeat | brightness | 0.20 | 0.61 / 0.71 / 0.54 | gated | 0.00-0.45 | +++ | **0.68** | +0.48 | **large shift (>=0.40)** |
| `kereru_wingbeats` | wingbeat | onset | 0.65 | 0.96 / 0.00 / 0.00 | ungated | 0.28-0.90 | +-- | **0.38** | -0.27 |  |
| `kettle_sing` | bed_like | brightness | 0.80 | 0.48 / 0.48 / 0.48 | gated | 0.52-1.00 | --- | **0.50** | -0.30 |  |
| `kettle_sing` | bed_like | onset | 0.20 | 0.76 / 0.57 / 0.46 | ungated | 0.00-0.45 | ++ | **0.62** | +0.42 | **large shift (>=0.40)** |
| `kingfisher_call` | call | continuity | 0.18 | 0.92 / 0.87 / 0.94 | gated | 0.00-0.43 | +++ | **0.91** | +0.73 | **large shift (>=0.40)** |
| `kingfisher_call` | call | periodicity | 0.70 | 0.31 / 0.29 / 0.22 | gated | 0.45-0.95 | --- | **0.27** | -0.43 | **large shift (>=0.40)** |
| `kingfisher_call` | call | roughness | 0.60 | 0.17 / 0.14 / 0.14 | gated | 0.35-0.85 | --- | **0.15** | -0.45 | **large shift (>=0.40)** |
| `kingfisher_call` | call | brightness | 0.75 | 0.09 / 0.05 / 0.05 | gated | 0.36-1.00 | --- | **0.12** | -0.63 | **large shift (>=0.40)** |
| `kingfisher_call` | call | onset | 0.85 | 0.56 / 0.33 / 0.85 | ungated | 0.49-1.00 | -- | **0.63** | -0.22 |  |
| `penguin_bray` | call | continuity | 0.35 | 0.50 / 0.81 / 0.86 | gated | 0.10-0.60 | ++ | **0.72** | +0.37 |  |
| `penguin_bray` | call | roughness | 0.85 | 0.39 / 0.33 / 0.38 | gated | 0.60-1.00 | --- | **0.37** | -0.48 | **large shift (>=0.40)** |
| `penguin_bray` | call | onset | 0.60 | 0.21 / 0.91 / 0.36 | ungated | 0.25-0.85 | + | **0.55** | -0.05 |  |
| `riroriro_trill` | call | continuity | 0.45 | 0.82 / 0.80 / 0.81 | gated | 0.20-0.70 | +++ | **0.81** | +0.36 |  |
| `riroriro_trill` | call | periodicity | 0.45 | 0.22 / 0.15 / 0.26 | gated | 0.20-0.70 | - | **0.21** | -0.24 |  |
| `riroriro_trill` | call | onset | 0.40 | 0.71 / 0.80 / 0.82 | ungated | 0.05-0.65 | +++ | **0.83** | +0.43 | **large shift (>=0.40)** |
| `small_birds` | call | continuity | 0.35 | 0.75 / 0.61 / 0.77 | gated | 0.10-0.60 | +++ | **0.71** | +0.36 |  |
| `small_birds` | call | periodicity | 0.25 | 0.28 / 0.51 / 0.35 | gated | 0.00-0.50 | + | **0.38** | +0.13 |  |
| `small_birds` | call | onset | 0.68 | 0.93 / 0.69 / 0.75 | ungated | 0.33-0.93 | + | **0.84** | +0.16 |  |
| `thunder` | thump | continuity | 0.10 | 0.43 / 0.64 / 0.83 | gated | 0.00-0.35 | +++ | **0.63** | +0.53 | **large shift (>=0.40)** |
| `thunder` | thump | roughness | 0.90 | 0.42 / 0.41 / 0.55 | gated | 0.65-1.00 | --- | **0.46** | -0.44 | **large shift (>=0.40)** |
| `thunder` | thump | brightness | 0.15 | 0.28 / 0.29 / 0.45 | gated | 0.00-0.40 | + | **0.38** | +0.23 |  |
| `waves_crashing` | bed | periodicity | 0.45 | 0.71 / 0.71 / 0.70 | gated | 0.20-0.70 | +++ | **0.71** | +0.26 |  |
| `waves_crashing` | bed | roughness | 0.88 | 0.52 / 0.47 / 0.43 | gated | 0.63-1.00 | --- | **0.47** | -0.41 | **large shift (>=0.40)** |
| `waves_crashing` | bed | brightness | 0.25 | 0.52 / 0.48 / 0.45 | gated | 0.00-0.50 | + | **0.50** | +0.25 |  |
| `waves_on_shingle` | bed | brightness | 0.25 | 0.52 / 0.50 / 0.50 | gated | 0.00-0.50 | ++ | **0.52** | +0.27 |  |
| `waves_on_shingle` | bed | onset | 0.35 | 0.59 / 0.60 / 0.51 | ungated | 0.06-0.60 | +++ | **0.59** | +0.24 |  |
| `wind_in_eaves` | bed | roughness | 0.40 | 0.03 / 0.06 / 0.09 | gated | 0.15-0.65 | --- | **0.06** | -0.34 |  |
| `wind_in_eaves` | bed | onset | 0.20 | 0.64 / 0.74 / 0.24 | ungated | 0.00-0.45 | +++ | **0.56** | +0.36 |  |
| `wind_in_trees` | bed_like | periodicity | 0.22 | 0.49 / 0.50 / 0.33 | gated | 0.00-0.47 | ++ | **0.44** | +0.22 |  |
| `wind_in_trees` | bed_like | roughness | 0.48 | 0.75 / 0.74 / 0.76 | gated | 0.23-0.73 | +++ | **0.75** | +0.27 |  |
| `wind_in_trees` | bed_like | brightness | 0.35 | 0.70 / 0.68 / 0.72 | gated | 0.07-0.60 | +++ | **0.71** | +0.36 |  |
| `wind_in_trees` | bed_like | onset | 0.22 | 0.52 / 0.38 / 0.40 | ungated | 0.00-0.47 | ++ | **0.46** | +0.24 |  |
| `wood_snap` | thump | continuity | 0.08 | 0.62 / 0.55 / 0.60 | gated | 0.00-0.33 | +++ | **0.59** | +0.51 | **large shift (>=0.40)** |
| `wood_snap` | thump | roughness | 0.70 | 0.23 / 0.18 / 0.24 | gated | 0.45-0.95 | --- | **0.22** | -0.48 | **large shift (>=0.40)** |
| `wood_snap` | thump | brightness | 0.55 | 0.07 / 0.03 / 0.12 | gated | 0.20-0.80 | --- | **0.12** | -0.43 | **large shift (>=0.40)** |
| `woodpile_settle` | thump | continuity | 0.20 | 0.82 / 0.12 / 0.33 | gated | 0.00-0.45 | + | **0.43** | +0.23 |  |
| `woodpile_settle` | thump | periodicity | 0.05 | 0.64 / 0.63 / 0.41 | gated | 0.00-0.30 | +++ | **0.56** | +0.51 | **large shift (>=0.40)** |
| `woodpile_settle` | thump | brightness | 0.30 | 0.51 / 0.63 / 0.77 | gated | 0.00-0.55 | ++ | **0.68** | +0.38 |  |
| `woodpile_settle` | thump | onset | 0.40 | 0.93 / 0.00 / 0.00 | ungated | 0.00-0.65 | + | **0.49** | +0.09 |  |
| `wren_scold` | call | continuity | 0.14 | 0.31 / 0.40 / 0.44 | gated | 0.00-0.39 | ++ | **0.38** | +0.24 |  |
| `wren_scold` | call | roughness | 0.42 | 0.09 / 0.10 / 0.06 | gated | 0.17-0.67 | --- | **0.08** | -0.34 |  |

## 5. The re-run (after the `_SOUNDS` edit)

`python -I scripts/strings_phase4_reseed_lab.py test` (full data: `strings_sheets_phase4_reseed_2026-10-18.json`).

**Gates.** T0 held: the edited `_SOUNDS` differs from the pre-edit registry in exactly the 115 proposed (key, axis)
pairs. T1 held: before the re-seed the J-2372 test gives J-2397's read (b) 20/64, baseline 0.2597, and read (a)
19/62, baseline 0.2509. T2 held: before the re-seed the gated code gives J-2383's 23/63.

**Headline: the J-2372 envelope test, unchanged (no gate), read (b), n = 64.**

| | pass / n | share | shuffle baseline | 0.8 x share | discriminating | own-rank median |
|---|---|---|---|---|---|---|
| before re-seed | 20 / 64 | 31.3% | 26.0% | 25.0% | no | 17.5 |
| **after re-seed** | **51 / 64** | **79.7%** | **33.1%** | 63.8% | **yes** | **5.5** |

- Read (a), n = 62: 19/62 = 30.6% (baseline 25.1%) -> **49/62 = 79.0%** (baseline 32.6%), discriminating.
- 31 keys flip fail -> PASS; **0 flip PASS -> fail**. 35 of the 36 re-seeded keys pass; `cicada_chorus` still
  fails (onset and continuity in two thirds, periodicity in the tail).
- Still failing (13): 3 of the 4 not re-seeded (distant_surf_boom, tide_pool_trickle, wood_pigeon; bees_in_garden
  passes ungated), cicada_chorus, morepork_call (gated PASS, so not a candidate), and 8 keys that
  pass the gated test but fail ungated, all on continuity and/or roughness: bed_watering, cat_demand,
  godwits_overhead, gull_cries, oystercatcher_call, pen_scratch, shingle_drag, sow_dig. These are the keys whose
  background, not their seed, is what the ungated test reads.
- Ungated axis misses over the vertices (above / below), before -> after: continuity 88/15 -> 67/5, roughness
  40/48 -> 22/12, onset 42/25 -> 20/12, periodicity 29/46 -> 10/14, brightness 33/17 -> 17/5. Continuity above the
  envelope stays the largest miss: the definitional gap F-3081 named (field-recording background) is still there
  for the keys the gate rescued.
- By archetype (pass before -> after / n): bed 3 -> 9 / 12, bed_like 3 -> 10 / 11, call 5 -> 14 / 20, thump 9 -> 17 /
  20, wingbeat 0 -> 1 / 1.

**Secondary: the J-2383 gated test** (in-sample for the re-seeded axes, see section 3): read (b) 24/64 = 37.5%
(baseline 27.5%) -> 60/64 = 93.8% (baseline 33.3%), own-rank median 25.5 -> 1.5; read (a) 23/62 -> 58/62 = 93.5%.

**Phase 1's own realness test** (cognitive_geometry nearest-neighbour timbre test, `run_realness()` in-process, no
write): 69/70 before and 69/70 after (bar 80%), flips saw_rasp PASS -> fail and waves_crashing fail -> PASS; peak
proximity 1.0 both. But the space is reshaped: 55 of 70 keys have a different nearest neighbour, and keys whose
nearest neighbour is a spoke of the same object fall from 9 to 4. Every constructed string still has three
pairwise-distinct vertices (`scripts/_test_j2067_string_vertices.py` PASS 70).

## 6. Reading against D-0476

- **Defeater branch 1 (re-seeded test still fails 60% or stops discriminating): does NOT fire.** 79.7% >= 60%, and
  the baseline 33.1% is well under 0.8 x 79.7%.
- **Branch 2 (D-0477 re-picks change more than 5 primary verdicts): does NOT fire.** J-2397 changed one own-envelope
  verdict among the re-picked keys (dawn_chorus PASS -> fail; log_on_fire PASS -> PASS; morepork_call and
  wind_in_trees fail -> fail).
- **What this does and does not show.** The pass is **in-sample**: each re-seed was fitted to the same recording
  it is then tested against, so 35/36 re-seeded keys passing is close to guaranteed and is not evidence that the
  new seeds are right about the sound. What can still fail, and did not, is discrimination: after the re-seed a
  measured string sits in its own key's envelope far more than in other keys' (own-rank median 5.5, from 17.5).
  The seeds now describe these 64 recordings. Whether they describe the sounds is a question for a second,
  independent recording per key, or for the large-shift keys in section 4 a by-ear check of the file.
- **Restart-gated.** The edit lives on branch jobrun/strings_and_sheets. It reaches the live process only at the
  next boot after the merge. It reaches the Phase 1 shadow only if `data/sound_strings_constructed.json` is
  regenerated before that boot (it is still the 2026-10-08, pre-J-2067 sidecar).

## Revert note (J-2440, F-3141, 2026-10-19)

Travis's by-ear check (F-3141) found 10 of the 25 large-shift keys were the WRONG FILE, so their re-seed was fitted to
the wrong recording. Reverted in `core/soundscape.py` `_SOUNDS` to the exact pre-J-2395 seeds (read from
`39bd1587^`): kingfisher_call, wood_snap, herb_cut, cat_chatter, cat_lapping, cat_purr, cat_yowl_cargo,
chair_desk_scrape, woodpile_settle, cicada_chorus. All other entries (including the 15 right-file re-seeds and
wood_pigeon from J-2409) are byte-identical to before (`scripts/_test_reseed_revert_J2440.py`, digest check).
Restart-gated like the original edit. Each reverted key still needs a file re-pick under the reviewed-before-download
rule (D-0376/D-0377) and then a fresh measure; that re-measure was NOT done here (no audio fetched), so the headline
J-2372 shares quoted above (51/64, later 52/64) include those 10 keys' now-reverted seeds and are stale until re-run.
