# Strings and Sheets — Phase 1 dry run results (2026-09-28)

Job J-1473. Script: `scripts/sound_strings_phase1_dryrun.py`. Metric sheet (pre-registered before any
number below was computed): `docs/lab/strings_sheets_phase1_dryrun_metric_sheet.md`. Raw output:
`docs/lab/strings_sheets_phase1_dryrun_2026-09-28.json` (all 70 keys' full detail — this doc summarises
and calls out what needs a human read; nothing is hidden, the JSON has every row). **No live change**:
`core/soundscape.py` was only imported and read; the sidecar `data/sound_strings_constructed.json` is a
new file; the realness test ran against a temporary, restored-after substitution inside this one script
process, never touching the live module.

**Methodology correction, stated plainly (see metric sheet §c for the full account):** the job briefing
pointed at `core/geometry_census.py` or `core/stick_test.py` for "the existing realness test." Both read
in full — neither contains one. The actual §5.3 realness-test script that exists,
`scripts/geometry_realness_test.py`, tests an unrelated hypothesis (the cross-space edge layer) against
outcome variables that only exist for lived cognitive events, and cannot be reused here. What this run
actually reuses is `core.soundscape.distance()`/`.neighbours()` — the same mechanism
`cognitive_geometry.md` §4's roster table cites for how Sound Space's interior was originally
sanity-checked. This is a real, load-bearing finding of this dry run, not a footnote — recorded in the
finding below.

## Verdicts

- **Bar 1 (realness) — MET.** 69/70 keys pass (98.57%), clearing the pre-registered ≥80% bar.
  `{"n_pass": 69, "n_total": 70, "pass_rate": 0.9857}`
- **Bar 2 (peak proximity) — MET, as predicted by construction, not as a discovery.** 70/70 keys have
  peak == fixed point exactly (offset 0.000), clearing the pre-registered ≥70% bar at 100%. This is the
  expected, stated consequence of this run's own method (peak = fixed for every archetype — metric
  sheet §b) and is reported as a methodological fact about the chosen construction, not evidence that the
  registry's points "really are" peaks in some independent sense. `{"n_within": 70, "n_total": 70,
  "within_rate": 1.0}`

## Archetype breakdown (70 keys, no leftovers)

| Archetype | n | Rule (onset -> peak -> tail) |
|---|---:|---|
| bed | 13 | flat body; peak = fixed; small build-in / fade on energy+brightness+onset-axis only |
| bed_like | 11 | same as bed (continuity >= 0.60, not in curated `_BEDS`) |
| call | 21 | builds to peak (=fixed), falls away at tail; fall softened by the key's own continuity |
| wingbeat | 2 | approach (quieter) -> peak (=fixed, the close pass) -> recede (quieter) |
| thump | 23 | onset = peak = fixed (instantaneous strike); sharp decay to near-silence at tail |

## The one realness FAIL, reported in full per the job's own instruction

**`waves_crashing`** (object: "the sea") — nearest neighbour: `waves_on_shingle` (same object, distance
0.572). Only 1 of 3 timbre axes agree within 0.25: periodicity Δ0.30, roughness Δ0.28, continuity Δ0.10
(agrees). Reading: `waves_crashing` (a big, breaking sea — roughness 0.88, periodicity 0.45) and
`waves_on_shingle` (the calmer working of the water — roughness 0.60, periodicity 0.75) are the *same
real-world source* but different enough *acoustic* character that even their own nearest-point match
fails the coarse timbre-agreement bar — a genuinely informative fail, not a construction bug: no other
key in the 70-key space is any closer to `waves_crashing`'s peak point than its own gentler sibling is,
and that sibling still isn't texturally close enough by this rule. Per the metric sheet and the job's own
kill/no-kill instruction, this key's string stays as constructed (a real point, correctly hand-seeded from
its own description) — a realness FAIL here means "flag it," not "the string is wrong."

## Notable PASS pairings worth a human skim (full 70 rows in the JSON)

| Key | Nearest neighbour | Same object? | Timbre axes agreeing |
|---|---|---|---|
| wind_in_eaves | wind_in_trees | no (mutual nearest neighbour, distance 0.136 — the tightest pair in the whole set) | 3/3 |
| riroriro_trill | robin_song | no (mutual, distance 0.129) | 3/3 |
| footsteps_leafmould | footsteps_grass_soil | yes (mutual, both soft-ground steps) | 3/3 |
| shag_wingbeats | kereru_wingbeats | no (mutual — the two WINGBEAT-archetype keys correctly find each other) | 3/3 |
| log_on_fire | wood_snap | no (mutual, both fire-adjacent wood impacts) | 3/3 |
| door_sound | gate_latch | no (mutual, both brief mechanical catches) | 3/3 |
| blackbird_song | robin_song | no (bird-song cluster) | 3/3 |
| cat_purr | footsteps_grass_soil | no — cross-object, borderline (2/3: periodicity+roughness agree, continuity does not) | 2/3 |

**The plan's own two cited exemplars are NOT reproduced today, and that is itself worth recording:**
`cognitive_geometry.md` §4's roster table cites "purr's nearest neighbour is the waves, tui's is the
blackbird" from 2026-07-05, when the registry held roughly 11 keys. Today, with 70: `cat_purr`'s nearest
neighbour is `footsteps_grass_soil` (still a PASS, 2/3 timbre axes), and `tui_song`'s is `godwits_overhead`
(PASS, 3/3) — `blackbird_song` is now only tui's 4th-nearest. Neither original pairing failing to
reproduce is a problem with the space; it is the expected consequence of 59 more points being added to
the same geometry since that claim was written, each one a candidate to be someone's new nearest
neighbour. Recorded here so nobody reads the old roster-table line as still-current.

## Anything unexpected

1. **The realness-test location in the job briefing was wrong, and finding the actual instrument was
   real work in itself** (see the correction note at the top and metric sheet §c) — `git grep`-ing
   "realness" repo-wide rather than trusting the two named files was what surfaced
   `scripts/geometry_realness_test.py`, and reading it in full is what showed it could not be reused
   as-is (no lived-outcome data exists for hypothetical strings). The mechanism that WAS genuinely
   reusable (`soundscape.distance()`/`.neighbours()`) sits one level lower than either file the briefing
   named.
2. **Bar 2 is trivially met by this run's own design choice (peak = fixed), stated as a limitation, not
   spun as a finding.** A harder version of this same check — one that estimates the peak independently
   of the registered point (e.g., from Phase 4's future measured recordings) — would be a real test of
   whether the existing single points describe peaks or something else (an average, a "typical" moment).
   This dry run's method cannot distinguish those; Phase 4 is where that distinction becomes testable
   against real audio.
3. **One real, non-trivial fail surfaced** (`waves_crashing`) exactly where the pre-registration said one
   might: two sounds sharing a real-world source can still be acoustically far apart on this space's own
   axes. That is evidence the six-axis distance is tracking something besides "which object is this," not
   a flaw to explain away.
4. **Zero prose change, zero wiring** — confirmed by construction: this run only reads `_SOUNDS` and
   writes two new files; no call site of `active_sounds()`, `percept()`, or `fire_ambience()` was touched.
5. **The sidecar cannot travel through this batch's own git-based worktree merge, and that needed
   saying plainly rather than discovering later.** This repo's root `.gitignore` excludes the whole
   `data/` directory outright ("Live data stores — written continuously by the running Du process;
   never track."). `data/sound_strings_constructed.json` is not that kind of file (static, hand-seeded,
   deterministic), but the exclusion is deliberate project policy ("never track"), not an oversight, so
   this session did not force-add it against that stated intent. Consequence: only
   `scripts/sound_strings_phase1_dryrun.py` and the three `docs/lab/` files are committed to this
   worktree's branch; the sidecar itself exists only in this worktree's own local, gitignored `data/`
   directory and will not appear in `C:\Nascence\data\` after the batch's worktree-merge. The fix is
   cheap and stated here so it is not lost: the script is a pure, deterministic function of the current
   `core.soundscape._SOUNDS` registry (no randomness, no other input) — re-running
   `python scripts/sound_strings_phase1_dryrun.py` directly against `C:\Nascence` regenerates a
   byte-identical sidecar there. This is now the first line of the spawned live-wire job's own briefing,
   not left implicit.

## Pointers

Sidecar: `data/sound_strings_constructed.json` (70 keys, onset/peak/tail + rationale). Script:
`scripts/sound_strings_phase1_dryrun.py`. Metric sheet: `docs/lab/strings_sheets_phase1_dryrun_metric_sheet.md`.
Raw per-key JSON: `docs/lab/strings_sheets_phase1_dryrun_2026-09-28.json`. Plan:
`docs/staged/strings_and_sheets.md` §3A, §5 Phase 1 row. Job: J-1473. Next: the live wire (census reading
the string's current point instead of the fixed one) is explicitly out of scope here and gated on its own
`/decide` per the plan's §5 — see the finding/job spawned from this run.
