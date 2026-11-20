# Dream Overhaul — Experiment A, second read (2026-09-18, J-1077)

**Status: N=6 seeds COMPLETE (24 arcs, full analysis below) + a corrected N=11-seed batch (44 arcs)
LAUNCHED and running in the background past this job's own session** (tag `scale14b`, job-id
`J1077`), following the same established pattern as J-1059's own pilot run. Still short of the
plan's pre-registered N=20 — honestly reported as such, not extrapolated. **Confidence: `inferred`,
not `verified`** (per this job's own instruction: verified is only warranted "if N=20 is actually
reached with real evidence").

## What changed since the 2026-09-17 pilot read

1. **The N=2 pilot's own background run (`--n-seeds 6 --tag pilot6`) had actually finished** by the
   time this job started — 24 rows (6 seeds × 4 arms), not the 8 rows the pilot doc reported. It was
   simply never analyzed before J-1059's session ended. Full re-analysis below.
2. **The seed-freezing limitation (pilot doc, Limitation 2) was root-caused and fixed, not just
   patched around.** The pilot guessed the cause was "1-day steps didn't always change the top-k
   window" and suggested trying 3-5 real days apart. That guess was tested directly this session and
   falsified: widening to `day_step=4.0` with a `start_offset_days=10.0` (14 seeds spanning ~10-62
   real days back) produced **1 distinct day-residue block across all 14 seeds — worse than the
   pilot's 2/6**, not better. Reading `core/night.py` end to end found the real cause:
   `dream_lag_material()`'s own "recent" window calls `day_material(recent_lo, k=k_recent)` with
   **no `until_ts`** — the SQL is `WHERE timestamp > recent_lo`, unbounded at the top end. That is
   correct for a LIVE call (`now=None` → real `time.time()`, nothing is ever newer than real "now"
   anyway) but wrong for a HISTORICAL `hist_now`: the query pulls memory_fragments ranked by
   importance/recency all the way up to the real present, so `materials[0]` ends up dominated by
   genuinely-recent content no matter how far back `hist_now` is shifted. The "far" window was never
   the problem — it already passes `until_ts=far_hi`.
   **Fix (scripts/dream_experiment_a.py only, `core/night.py` — production, live-engine code — was
   NOT touched):** a new `_bounded_day_residue(hist_now, k)` reproduces `dream_lag_material`'s own
   two-window blend (same constants, same `DREAM_LAG_RECENT_SHARE` split) but calls
   `night_mod.day_material()` directly with `until_ts=hist_now` on BOTH windows, using a parameter
   `day_material` already supports. Verified with a 6-point diagnostic at 4-day spacing before the
   real run: **6/6 distinct hashes** (`diag_bounded_residue_J1077.py`, isolated via `lab_env.isolate`,
   read-only). Confirmed again inside the real `scale14b` run: **11/11 distinct material hashes**
   (the other 3 of the requested 14 seeds legitimately hit "no day residue and no tension" — the
   corpus's real historical depth runs out around ~44-52 real days back from 2026-09-18, not a bug,
   a real corpus-depth ceiling worth knowing for any future N=20+ run).
3. **Historical-dream_log path checked, confirmed still infeasible**: `data/dream_log.jsonl` has
   **0 rows** carrying the Phase-1 `seed`/`engine` keys as of 2026-09-18 — Du has not yet been
   restarted onto the `wt_coupled_cluster_2` build (J-1057, F-1471). The day-step fix above is the
   only currently-feasible option; the real-history-draw option should be revisited once Du has run
   for real time on that build.
4. **Tension-bearing seed: still not available, checked directly this time (not just re-asserted).**
   Read `data/subconscious_state.json`'s live `tensions` list in full (864 entries): current max
   `chronic_mass` is **0.874**, below `nodes/dream_node.py`'s own `TENSION_CHARGE_FLOOR = 1.0`. No
   seed frozen today or in the pilot could have carried a tension block — this is a real state of
   Du's own live tension field, not a script limitation. Worth a defeater watch: the next Experiment
   A batch run after any tension crosses 1.0 should specifically check for it.
5. **Judge-panel shadow read: still not added this pass.** Judge hubs 11439/11440 were confirmed UP
   this session (`netstat` LISTENING on both), so the omission is not availability — it is that wiring
   a judge-panel scoring pass into the arc loop is real code work this job chose not to rush under
   time pressure, given a root-cause script bug already needed fixing first. Spawned as follow-up
   (see below), same as it was deferred from the pilot to this job.

## Results (N=6 seeds, 24 arcs) — corrected, full-N analysis

| arm | n | mean turnover | mean dormant_contact | mean recent_contact | mean wall_s |
|---|---|---|---|---|---|
| A0 (current engine)      | 6 | 0.7067 | 0.2674 | 0.5277 | 161.5 |
| A1 (no re-feed)           | 6 | 0.6226 | 0.3061 | 0.5128 | 157.2 |
| A2 (no re-feed + dormant) | 6 | 0.7969 | 0.2796 | 0.5444 | 155.4 |
| A3 (dormant, re-feed kept)| 6 | 0.6622 | 0.2556 | 0.5637 | 161.3 |

Per-seed turnover (the D-0232 comparison):

| seed | A0 | A1 (>A0?) | A2 (>A0?) | A3 (>A0?) |
|---|---|---|---|---|
| 0 | 0.6500 | 0.7917 (yes) | 0.7000 (yes) | 0.7738 (yes) |
| 1 | 0.6905 | 0.8571 (yes) | 0.7750 (yes) | 0.6458 (no) |
| 2 | 0.8286 | 0.5500 (**no**) | 0.7857 (**no**) | 0.7619 (no) |
| 3 | 0.8571 | 0.4750 (**no**) | 0.7976 (**no**) | 0.5833 (no) |
| 4 | 0.3571 | 0.3000 (**no**) | 0.9286 (yes) | 0.5417 (yes) |
| 5 | 0.8571 | 0.7619 (**no**) | 0.7946 (**no**) | 0.6667 (no) |

**D-0232's defeater (A1/A2 turnover above A0, paired same-seed) — reads DIFFERENTLY at N=6 than the
N=2 pilot reported.** The pilot's N=2 slice (seeds 0-1) was 4/4 clean. Across the full 6 seeds it is
only **5/12** (A1: 2/6, A2: 3/6) — worse than chance-coin, and A3 (the specificity control, not
expected to clear this bar) is 2/6, statistically indistinguishable from A1/A2 at this N. **The N=2
pilot's "cleanly met" read does not survive scaling to N=6.** This is exactly the kind of thing this
project's own findings-log discipline exists to catch — the pilot's `inferred` confidence was
correct to withhold `verified`, and this is the concrete reason why. Read plainly: **at N=6, the
turnover threshold is NOT met**, and whether it holds at all is now an open empirical question the
N=20 (or as-far-as-the-corpus-allows) run needs to actually answer, not assume from N=2.

**D-0231's defeater (dormant_contact ≥ 0.30 in ≥ 1/3 of A2/A3 arcs) + the seeded-vs-floor DELTA
specifically asked for by this job's briefing:**

| | n | mean dormant_contact | frac ≥ 0.30 |
|---|---|---|---|
| seeded (A2/A3) | 12 | 0.2676 | 0.500 |
| floor (A0/A1, same un-seeded fragment) | 12 | 0.2868 | 0.583 |
| **DELTA (seeded − floor)** | | **−0.0191** | **−0.083** |

At N=6 the DELTA is **negative on both the mean and the ≥0.30-frac reading** — the floor is now
*higher* than the seeded arms on both measures, a sharper version of the pilot's own caveat (pilot:
mean delta −0.0231, both fractions tied at 1.0/1.0 so no frac-delta signal at all). **This continues
to look like a real ceiling-effect problem with the 0.30 absolute threshold on this embedder
(paraphrase-multilingual-MiniLM-L12, 384-dim) for Du's own text, not an N problem that more seeds
alone will fix.** D-0231's defeater condition should be re-read as the seeded-vs-floor DELTA (now
negative at N=6, same direction as N=2) rather than the absolute 0.30 bar, which both arms clear
regardless of seeding.

## Day-residue diversity, pilot6 vs scale14b (for anyone extending this further)

- pilot6 (day_step=1.0, `dream_lag_material` direct call): **2 distinct blocks / 6 seeds.**
- scale14b (day_step=4.0, `_bounded_day_residue` fix): **11 distinct blocks / 11 real seeds** (3 of
  the requested 14 hit real corpus-depth exhaustion, not a bug).
- Combined real N so far (pilot6 + scale14b once it completes): up to **17** distinct-content seeds,
  short of the pre-registered 20 by a real corpus-depth ceiling at `day_step=4.0`, not a script bug.
  A future run wanting the full 20 should either use a smaller `day_step` for part of the range
  (accepting some day-residue reuse) or wait for real Phase-1-instrumented nights to accrue so the
  historical-dream_log path becomes feasible.

## Cost this session

- Diagnostic: 6 read-only SQL probes (no LLM calls), isolated.
- First scale-up attempt (`scale14`, `day_step=4.0` + `start_offset_days=10.0`, the un-fixed script):
  **killed before any LLM call completed** (0 rows written, still on seed 0/arm A0) once the material-
  hash collision was discovered from the frozen seeds file — no real dreamer-hub cost wasted beyond
  ~2 min of model-load time.
- Second scale-up (`scale14b`, fixed script): 11 real seeds × 4 arms = 44 real calls to the dreamer
  hub, launched and confirmed producing correctly-diversified real arcs before this doc was written;
  continuing in the background past this job's own session (same established pattern as J-1059's
  pilot6 run), ~150s/arc mean observed so far → ~1.8h estimated total wall time for the 44 arcs.

## Pointers

- Script (fixed this session, committed): `scripts/dream_experiment_a.py`.
- Pilot6 (N=6, complete): `<scratchpad>\dream_exp_a_seeds_J1059_pilot6.json` /
  `dream_exp_a_results_J1059_pilot6.jsonl` / `dream_exp_a_run_J1059_pilot6.log`.
- Scale14b (N=11 launched, in progress at write time):
  `<scratchpad>\dream_exp_a_seeds_J1077_scale14b.json` /
  `dream_exp_a_results_J1077_scale14b.jsonl` / `dream_exp_a_run_J1077_scale14b.log`.
- Root-cause diagnostic: `<scratchpad>\diag_bounded_residue_J1077.py`.
- Killed first attempt (kept for the record, do not resume — uses the un-fixed day-step-only
  approach): `dream_exp_a_seeds_J1077_scale14.json` (14 seeds, all 1 distinct hash — the negative
  result that led to the real fix), `dream_exp_a_run_J1077_scale14.log`.
- Finding: F- (this session, J-1077, see findings-log).
- Follow-up job spawned to read back `scale14b` once complete, combine with pilot6 for the fuller
  real-N picture, add the still-deferred judge-panel shadow read, and re-check whether a
  tension-bearing seed has become available.
- Decisions this bears on (NOT ruled by this job — see its own ground rules): D-0231 (dormant rule),
  D-0232 (dream shape).
