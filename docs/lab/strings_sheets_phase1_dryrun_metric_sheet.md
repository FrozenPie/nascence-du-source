# Strings and Sheets — Phase 1 dry run: pre-registered metric sheet

Written 2026-09-28, BEFORE any per-key number in this run is computed (this project's pre-registration
law). Job J-1473. Plan: `docs/staged/strings_and_sheets.md` §3 Object A, §5 Phase 1 row, §7, §10. No live
change: sidecar file + offline test only — `core/soundscape.py`'s `_SOUNDS` is read, never edited.

## (a) What gets built

`data/sound_strings_constructed.json`: for every one of the 70 keys in `core.soundscape._SOUNDS`, three
points (onset, peak, tail) on the same six axes (`brightness, energy, onset, periodicity, roughness,
continuity` — `core.soundscape._AXES`, unchanged order), plus a one-line rationale per key drawn from
that key's own registry comment / `_PERCEPT_LINES` prose (the "render strings" the job names) and object
semantics. A new file; `core/soundscape.py` is not touched anywhere in this job.

## (b) Construction method — pinned before any point is written

**Archetype per key**, assigned by hand from the registry's own `object` field, inline comments, and
(where one exists) `_PERCEPT_LINES` prose — five archetypes:

- **BED** (13 keys — exactly `core.soundscape._BEDS`): flat body. `peak = fixed` (unchanged);
  `onset = peak` minus a small build-in (`energy -0.08, brightness -0.03, onset-axis -0.04`); `tail =
  peak` minus a smaller fade (`energy -0.06, brightness -0.02, onset-axis -0.03`). Clipped to [0,1].
- **BED-LIKE** (11 keys — registered continuity >= 0.60, but not in the curated `_BEDS` set:
  `bees_in_garden, wind_in_trees, stream_run, clock_tick, kettle_sing, dawn_chorus, tide_pool_trickle,
  footsteps_shingle, footsteps_leafmould, saw_rasp, cat_chatter`): same numeric treatment as BED — a
  sustained presence by the space's own continuity axis, even though no one added it to the hand-curated
  list.
- **CALL** (21 keys — bird/animal vocalisations and choruses with a real rise-peak-fall arc:
  `gull_cries, tui_song, blackbird_song, bellbird_song, morepork_call, cat_trill, cat_meow_at_door,
  cat_demand, cat_yowl_cargo, oystercatcher_call, cuckoo_call, godwits_overhead, blackbird_alarm,
  small_birds, wood_pigeon, wren_scold, fantail_chatter, riroriro_trill, kingfisher_call, robin_song,
  penguin_bray`): `peak = fixed`; `onset = peak` minus a build-in (`brightness -0.12, energy -0.15,
  onset-axis -0.10`, scaled by `(1 - 0.4 x continuity)`); `tail = peak` minus a fall (`brightness -0.15,
  energy -0.18, onset-axis -0.12`, same scale) — directly the plan's own §3A worked example
  ("brightness and energy high at the peak, both falling at the tail"); the scale softens the fall for
  calls whose own continuity axis already reads closer to sustained.
- **WINGBEAT** (2 keys — `shag_wingbeats, kereru_wingbeats`): an approach/recede arc. `peak = fixed`
  (the close pass); `onset` and `tail` both = `peak` minus `(brightness -0.05, energy -0.15, onset-axis
  -0.06)` (quieter, approaching/receding).
- **THUMP** (23 keys — a single sharp transient or momentary self/object act: `cat_thump, thunder,
  wood_snap, gate_latch, window_rattle, moth_tap, canopy_drip, woodpile_settle, chair_desk_scrape,
  pen_scratch, page_turn, herb_cut, sow_dig, door_sound, log_on_fire, kettle_fill, kettle_pour,
  bed_watering, wood_haul_clatter, leaf_rustle, branches_creak, footsteps_floorboards,
  footsteps_grass_soil`): `onset = peak = fixed` (the strike/impact IS the onset — no separate build for
  an instantaneous event); `tail = peak` minus a sharp decay (`brightness -0.10, energy -0.30,
  onset-axis -0.45`) — near-silence, no further discrete onsets once the hit has happened.

`13 + 11 + 21 + 2 + 23 = 70` — every key in `_SOUNDS` gets exactly one archetype, no leftovers, checked
by the script itself (refuses to run on a mismatch).

**Only the three envelope axes move** (`brightness, energy, onset` — loudness / brightness / event-
density, the axes with a real time-course within one sound). **The three timbre axes stay fixed across
onset/peak/tail** (`periodicity, roughness, continuity` — properties of the sound's *kind*, not its
instant) at every one of the three points, equal to the registered value. Stated simplification, not an
oversight: the plan's own worked example varies only brightness/energy and treats continuity as a static
descriptor ("continuity low"), never a time-varying one.

**Why `peak = fixed` for every archetype (stated before the run, not fitted after it):** a single
hand-seeded point for a nameable, describable sound most naturally encodes that sound's characteristic /
most recognisable instant — for an event (a call, a thump) that instant IS its peak; for a bed, "peak" is
degenerate (a flat body has no separate peak instant from its steady value). Consequence, stated up
front: metric (2) below (peak within 0.15 of the fixed point) is expected to read 100% at offset 0.000
for all 70 keys, by construction — a real, reportable methodological fact about what this dry run's
chosen method claims of the existing registry, not an empirical discovery, written down here before the
run so it cannot be mistaken for one afterwards. If any key's computed offset is NOT 0 it means that
key's archetype code has a bug against its own stated rule above, not a hand-seeding finding.

## (c) The realness test — what is actually reused, corrected from the job briefing

The job briefing pointed at `core/geometry_census.py` or `core/stick_test.py` for "the existing test."
Both read in full this session: neither computes anything called realness — `geometry_census.py` is the
tuple *recorder* (writes `data/geometry_tuples.jsonl`; no distance/neighbour math anywhere in it);
`stick_test.py` computes bundle-richness ("spokes"), a different metric entirely. The actual §5.3-named
realness-test *script* that exists in this repo (found by grepping "realness" repo-wide, not guessed),
`scripts/geometry_realness_test.py`, tests a different, unrelated hypothesis — the cross-space edge layer
(P1/P2, J-0416/D-0088) — against two outcome variables that only exist for cognitive events that were
actually LIVED (`restate_sim` from `data/train_state_log.jsonl`; `developed` from
`data/co_recall_ledger.jsonl`). It cannot run against hypothetical, never-fired onset/peak/tail strings;
re-running it here would not be reusing it, it would be feeding it data it was never built to join
against, and per its own results doc it already returned a clean FAIL for that (different) hypothesis.

What **is** directly reusable, unmodified, and is the actual mechanism `cognitive_geometry.md` §4's own
roster table cites for how Sound Space's interior was originally sanity-checked ("interior verified:
purr's nearest neighbour is the waves, tui's is the blackbird") is `core.soundscape.distance()` /
`.neighbours()` — the module's own Euclidean nearest-neighbour functions. This dry run reuses those
functions exactly, via a temporary, in-process, restored-after substitution of `_SOUNDS` with the
constructed peak points (never written to disk, never touching the live module state after the script
exits) — not a reimplementation of the six-axis distance formula.

**Pre-registered per-key pass rule**, calibrated against the plan's own two cited examples BEFORE this
run, using their raw registered coordinates (not this run's output): for key K's peak point, take its
rank-1 nearest neighbour among all 70 keys' peak points (`soundscape.neighbours`, k=1, on the constructed
set). **PASS iff at least 2 of the 3 *timbre* axes (periodicity, roughness, continuity) are within 0.25
of the neighbour's.** Hand-check before locking the rule: purr vs. waves_on_shingle agrees within 0.25
on periodicity (Δ0.20) and continuity (Δ0.00) but not roughness (Δ0.30) = 2/3 → PASS; tui vs.
blackbird_song agrees within 0.25 on periodicity (Δ0.05) and continuity (Δ0.05) but not roughness
(Δ0.30) = 2/3 → PASS. The rule reproduces both of the plan's own cited "real interior" examples at
exactly the passing margin (2 of 3), not padded above it. FAIL otherwise. Whether `waves_on_shingle` is
still `cat_purr`'s actual rank-1 neighbour today, now that the registry holds 70 keys instead of the
~11 it had on 2026-07-05, is exactly what this run's own output — not this calibration paragraph — will
say.

This is a **coarser, static self-consistency check**, not the full §5.3 predictive-outcome test above —
stated as such in the results doc, so an 80% pass rate here is never conflated with the harder bar
§5.3's own script already answered (a clean FAIL, unrelated hypothesis) or read as more than it is.

## (d) Pre-registered bars (the job's own two, plus one reporting requirement)

1. **>= 80% of the 70 keys PASS realness** (rule above). Outcome genuinely unknown before the run —
   this is the dry run's real empirical content.
2. **>= 70% of keys have peak-vs-fixed-point offset <= 0.15.** Expected at 100% / offset 0.000 by
   construction (see (b)) — reported as a methodological fact, not a discovery.
3. Any key failing (1) is reported individually with its actual nearest neighbour and the two timbre
   deltas that failed, per the job's own instruction that this is itself data, not a thing to smooth over.

## Pointers

Script: `scripts/sound_strings_phase1_dryrun.py` (this worktree). Sidecar:
`data/sound_strings_constructed.json`. Results: `docs/lab/strings_sheets_phase1_dryrun_2026-09-28.md` +
`.json`. Source of the construction/test spec: job J-1473 briefing, this session. Plan:
`docs/staged/strings_and_sheets.md` §3A, §5 Phase 1 row, §7, §10. Precedent style: Phase 0's own
`docs/lab/strings_sheets_ribbon_metric_sheet.md` (J-1468).
