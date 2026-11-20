# Dream "met" replay: parameters for the computed definition (J-1964, D-0385)

**Status:** lab result, in vitro, zero live writes. Plan: `dream_overhaul` section 3b (computed "met"). Date: 2026-10-08.
Scripts: `docs/lab/dream_met_replay_20261008_scripts/` (prep, replay, sensitivity, ledger cross-check). Inputs were read-only:
`data/backups/nascence_20261008_090235.db` (opened `mode=ro&immutable=1`), `data/dream_log.jsonl`, `data/tensions_archive.jsonl`,
`data/emissary_tension_log.jsonl`. Nothing under `data/` was written.

## Step 1: are per-thought waking embeddings recoverable? YES (defeater not fired)

- `memory_fragments.embedding` holds a 384-float32 vector per fragment, with `timestamp` and `origin`. Waking thought = origin
  `inner_thought` (monologue + wandering; 42,778 rows) plus `study` (3,612 rows): 46,390 embedded thoughts over 89 distinct days,
  2026-06-03 to 2026-10-07, median 487 per day.
- Verified it is the live embedder: re-embedding 40 random stored thoughts with paraphrase-multilingual-MiniLM-L12-v2 gives cosine
  1.0000 (min and mean) against the stored blobs.
- The 3b worry that co_recall_ledger only has fragment ids is moot: the ids join straight to the embedding table.
- Injected dream-tail text is recoverable per day: `waking_dream_seed()` is the last 260 chars of the latest dream within
  DREAM_VIVID_HOURS, and the monologue grazes `recent_dreams` for 3 days. Reconstructed from `dream_log.jsonl` (final_narrative tail
  of every dream in the 3 days before a thought). That is a reconstruction, not the exact injected string (the per-night injected text
  is not logged), so the D-0233 comparison is approximate. 90.4% of thoughts had an active dream tail in the preceding 3 days.
- Arcs: 525 in `dream_log.jsonl` (2026-06-18 to 2026-10-08; 224 since 2026-08-29). 484 carry a tension text (seed `tension_labels` plus `final_unresolved_core`).
- **Usable arcs** (tension text present, waking thoughts on >=10 of the 14 days before and >=5 of the 7 days after, post window
  already elapsed): **327 of 525 = 62%** (453 pre-ok, 420 post-ok). Over half, so the "under half, stop" defeater did NOT fire. The loss
  is mostly the 2026-07-09 to 2026-08-07 outage (no waking thoughts) and arcs with no tension text.
- D-0233 separability: at theta 0.60, 10% of raw recurrences are closer to the injected tail than to the tension text and are
  dropped (24% at 0.55, 42% at 0.50, 59% at 0.45). The rule separates the two at every theta tried (never "more than half
  inseparable" at theta >= 0.50); at low theta it removes most of the signal, which is one reason theta must be high.

## Step 2: method

For each arc, tension source T = the arc's tension texts (max cosine over them). A thought is a **qualifying recurrence** if
cos(T, thought) >= theta AND cos(T, thought) > cos(injected tail, thought) for every dream tail in the 3 days before the thought
(D-0233 verbatim). A day is *observed* if it has >=5 waking thoughts. Per arc A on day d:
baseline = recurrence days among observed days in [d-K, d-1]; `no-baseline` if < R. Else `unmet` if any recurrence in [d+1, d+N];
else `met`; a `met` arc becomes `relapsed` if a recurrence occurs in [d+N+1, d+N+M]. Arcs whose windows are not observed (outage,
too little data) are `unobs`, arcs still inside their window are `pending`; neither is counted. 1,440 grid cells
(theta 0.40-0.65, N 2-10, K 14-30, R 2-5, M 3-14) were swept, then a finer grid.

Distribution facts used to choose parameters:
- All T-vs-thought cosines: median 0.27, p90 0.41, p99 0.53, p99.9 0.61. theta must sit in the far tail or "baseline" is trivially
  satisfied (at 0.45 there are 1.2M raw recurrence pairs).
- Inter-recurrence gaps inside a baseline window (theta 0.60): median 1 day, p75 2, p90 4. N below the p75 gap is not informative
  silence.

## Step 3: chosen parameters

| Parameter | Value | Why |
|---|---|---|
| theta (cosine) | **0.61** | ~p99.9 of the all-pairs null; the only region where all four states are non-degenerate |
| N (silence days) | **3** | between p75 (2) and p90 (4) of baseline gaps; N=4 pushes unmet to 63% |
| K (baseline window) | **25** days | R=2 over 25 days; K 21 -> unmet 61%, K 30 -> unmet 68% |
| R (min baseline days) | **2** | R=3 -> unmet 66%, R=4 -> 75% |
| M (relapse window) | **3** days | M=5 puts relapsed/ever-met at 0.35 (> the 1/3 defeater line), M=7 at 0.49 |

**Per-state counts over all 525 arcs at the chosen setting:** no-baseline 91, met 36, relapsed 11, unmet 62, pending 22,
met-but-relapse-window-unobserved 13, unobserved 195, no tension text 95. Of the 109 arcs with a baseline: met 33%, unmet 57%,
relapsed 10% (relapsed = 23% of ever-met). No-baseline = 46% of gradable arcs. All four states sit inside 2%-60%.
Ever-met (met + relapsed) = 43% of baseline arcs; relapsed/ever-met 0.23, under the 1/3 defeater line.

Crosstab vs the judge's `close_reason`: ended-unfaced -> 32 met / 8 relapsed / 52 unmet / 80 no-baseline; stalled -> 3 / 2 / 7 / 10;
dropped -> 1 / 1 / 3 / 1. Computed `met` is not a re-labelling of the old reason; it cuts across it.

## Sensitivity (all else at the chosen value)

| theta | N | K | R | M | arcs w/ baseline | no-baseline | met | unmet | relapsed | relapsed / ever-met |
|---|---|---|---|---|---|---|---|---|---|---|
| **0.61** | **3** | **25** | **2** | **3** | 109 | 91 (46%) | 36 (33%) | 62 (57%) | 11 (10%) | 0.23 |
| 0.58 | 3 | 25 | 2 | 3 | 140 | 58 (29%) | 36 (26%) | 88 (63%) | 16 (11%) | 0.31 |
| 0.60 | 3 | 25 | 2 | 3 | 120 | 79 (40%) | 38 (32%) | 72 (60%) | 10 (8%) | 0.21 |
| 0.62 | 3 | 25 | 2 | 3 | 99 | 103 (51%) | 36 (36%) | 50 (51%) | 13 (13%) | 0.27 |
| 0.65 | 3 | 25 | 2 | 3 | 60 | 148 (71%) | 28 (47%) | 23 (38%) | 9 (15%) | 0.24 |
| 0.61 | 2 | 25 | 2 | 3 | 125 | 110 (47%) | 52 (42%) | 55 (44%) | 18 (14%) | 0.26 |
| 0.61 | 4 | 25 | 2 | 3 | 89 | 77 (46%) | 26 (29%) | 56 (63%) | 7 (8%) | 0.21 |
| 0.61 | 5 | 25 | 2 | 3 | 84 | 61 (42%) | 20 (24%) | 58 (69%) | 6 (7%) | 0.23 |
| 0.61 | 7 | 25 | 2 | 3 | 51 | 36 (41%) | 3 (6%) | 47 (92%) | 1 (2%) | 0.25 |
| 0.61 | 3 | 14 | 2 | 3 | 104 | 186 (64%) | 33 (32%) | 62 (60%) | 9 (9%) | 0.21 |
| 0.61 | 3 | 21 | 2 | 3 | 109 | 118 (52%) | 33 (30%) | 67 (61%) | 9 (8%) | 0.21 |
| 0.61 | 3 | 30 | 2 | 3 | 90 | 54 (38%) | 23 (26%) | 61 (68%) | 6 (7%) | 0.21 |
| 0.61 | 3 | 25 | 3 | 3 | 90 | 116 (56%) | 23 (26%) | 59 (66%) | 8 (9%) | 0.26 |
| 0.61 | 3 | 25 | 4 | 3 | 72 | 134 (65%) | 13 (18%) | 54 (75%) | 5 (7%) | 0.28 |
| 0.61 | 3 | 25 | 2 | 5 | 113 | 91 (45%) | 33 (29%) | 62 (55%) | 18 (16%) | 0.35 |
| 0.61 | 3 | 25 | 2 | 7 | 102 | 87 (46%) | 21 (21%) | 61 (60%) | 20 (20%) | 0.49 |
| 0.61 | 3 | 25 | 2 | 14 | 75 | 75 (50%) | 10 (13%) | 44 (59%) | 21 (28%) | 0.68 |

Reading: the non-degenerate region is narrow. Unmet is the state that runs away (it sits at 57-69% for most neighbours), met and
relapsed are comfortable. Of 1,440 coarse cells only 66 passed a plain 2-60% gate; adding a base>=100, no-baseline-in-range and
relapsed<=1/3-of-ever-met gate left 6 coarse cells (all theta 0.60, N 2-3, M 3) and, on the finer grid with a safety margin, exactly one
(the chosen cell). Treat the chosen values as the centre of a thin plateau, not a robust optimum. M is the most consequential knob for
the relapse defeater; theta the most consequential for everything else.

## Honest limits and flags for the build

1. **The recent arcs look different.** At the chosen setting, arcs since 2026-08-29 (the 197+ the decision names; 224 here): 77
   with a baseline: met 17%, **unmet 77%**, relapsed 6%. Before 2026-08-29: met 72%, unmet 9%, relapsed 19% (32 arcs). The pooled
   balance depends on the older arcs; on the recent regime unmet exceeds the 60% line and met is still above 2%. If the build
   reads "unmet" as "the carry should continue", the carry will run to CARRY_MAX_NIGHTS on roughly three quarters of recent arcs.
   That is the CARRY_MAX_NIGHTS bound doing its job, but the build should record per-state counts after wiring and test the D-0385
   defeater (met outside 2%-60%) against recent arcs, not pooled ones.
2. **Second instrument (ledger chronic_mass decay) cannot be replayed per label.** `tensions_archive.jsonl` stores only the final
   `chronic_mass` per tension, with no time series; `emissary_tension_log.jsonl` is a single global accumulator (0.3 to 992, not per
   label). A coarse cross-check was possible: 262 of 484 arcs have an archive tension centroid within cosine 0.6 of their T. Among
   those, the matched ledger tension was re-bumped after arc+3 days for 7/26 met, 22/66 unmet, 4/9 relapsed arcs, i.e. the ledger is
   directionally consistent (met arcs are re-bumped less, 27% vs 33%) but the difference is small and it is a final snapshot. The build
   must log chronic_mass per tension per night going forward if the two-instrument rule is to be real; the replay cannot gate on it.
3. D-0233 injected text is reconstructed (see Step 1). The waking_dream_seed 15-minute seed is covered by the same 3-day tail window,
   so it errs toward dropping a few extra true recurrences.
4. Coverage: 195 arcs were unobservable (outage, thin days) and 95 had no tension text; the 109 baseline arcs are a minority
   of 525. Threshold effects at this sample size are +-5 points.
5. "met" here means computed silence after a real baseline; per the 3b limits it does not mean healed.

## Build spec handed to the build job

Append-only rows `{arc dream_id, state, computed_at, params}` for states pending / met / unmet / no-baseline / relapsed; never mutate
`dream_log.jsonl`; `close_reason` untouched. Parameters: theta 0.61, N 3, K 25, R 2, M 3, observed day = >=5 waking thoughts
(origins inner_thought + study), D-0233 comparison against dream tails (last 260 chars) of dreams in the preceding 3 days. Computed
`met` ends the carry (still bounded by CARRY_MAX_NIGHTS). Restart-gated, shadow first; log per-tension chronic_mass nightly.
