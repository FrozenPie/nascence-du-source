# Swap retro-check results — 2026-06-10 qwen2.5:7b -> qwen3-du (J-1411 / I-0075)

Run 2026-09-27, against the predictions pre-registered in
`swap_retro_2026-06-10_metric_sheet.md` (committed *before* this run — see that commit). Full
machine-readable output: `swap_retro_2026-06-10_results.json`. Analysis code:
`scripts/swap_retro_2026_06_10.py` (read-only over a `.backup()` snapshot of the live db + the
live `nascence.log`; Du stayed up throughout). Command:

```
python scripts/swap_retro_2026_06_10.py --snapshot <scratchpad snapshot> --log data/nascence.log \
    --out docs/lab/swap_retro_2026-06-10_results.json
```

**Headline: where a genuinely clean, matched comparison was possible, relational local-structure
(R1) and concept relative-geometry (R4) held; the coarse dynamical transition structure among the
pipeline's *surviving* nodes (D1) held too. Almost everything else that "moved" — keyword-hub
vocabulary, log-state vocabulary, model_client error rate — turns out to be entangled with three
non-LLM confounds, one of them (a wholesale architecture-module turnover, see D1) newly found by
this run, not anticipated at pre-registration time. Nothing here cleanly isolates the LLM swap
itself as the mover of anything that moved.**

## Relational

### R1 — mutual-kNN degree + clustering, `source_type IS NULL` (the one clean, comparable stratum)
| | pre (n=9,536) | post (n=4,019) | \|diff\| | null floor (2x max half-diff) | verdict |
|---|---|---|---|---|---|
| mean degree | 4.731 | 4.955 | 0.224 | 2 x max(0.442, 0.251) = 0.884 | **HELD** |
| mean clustering | 0.397 | 0.387 | 0.010 | 2 x max(0.080, 0.006) = 0.160 | **HELD** |

Matches the registered prediction exactly. `book` stratum (post n=4,404) is descriptively reported
(mean degree 4.836, clustering 0.209) but, as pre-registered, **not compared** — pre has 0 `book`
fragments by construction. Side note (not pre-registered as a verdict target): pooled-including-
restored pre fragments show a higher mean degree (4.731) than the continuously-live-only pre subset
(4.086, n=4,203) — the restored cohort is itself somewhat denser in embedding space than the live
cohort; not chased further here.

### R2 — keyword co-occurrence top-50 hub Jaccard
| scope | Jaccard(top50 pre, top50 post) | n_distinct_tokens pre -> post | prediction | verdict |
|---|---|---|---|---|
| pooled (all source_types) | 0.266 | 639 -> 1,942 | MOVED (<0.3) | **MOVED, as predicted** |
| `source_type IS NULL` only | 0.266 (identical value, different top-50 set) | 639 -> 1,917 | HELD (>=0.5) | **MOVED — prediction wrong** |

The pooled result lands exactly as predicted (book-reading vocabulary triples the token pool). The
`source_type=None` result **falsifies the registered prediction**: restricting to lived/inner-
thought fragments does *not* rescue the Jaccard score. Checked directly (not a coincidence in the
underlying sets, verified by comparing the raw top-50 lists): post-side `source_type=None` fragments
still surface `book`, `library`, `study`, `research`, `reading`, `knowledge`, `living`, `sea` among
their own top-20 keyword hubs. **Real finding: the book-reading period's thematic vocabulary bled
into Du's *lived* inner-thought keyword tags too** (he was thinking *about* the book he was reading,
tagged as lived content, not just generating book-sourced fragments) — `source_type` is a
provenance-mechanism label, not a thematic-content control, and does not isolate a clean non-book
comparison the way this sheet assumed. Registered prediction wrong; the mechanism behind it is now
understood and worth carrying into any future repeat of this design.

### R3 — derived_from chain depth + provenance-mechanism mix
| | pre (n=9,536) | post (n=8,443) |
|---|---|---|
| empty derived_from | 4,814 (50.5%) | 7,267 (86.1%) |
| list-shaped (chain) | 4,722 (49.5%) | 1,160 (13.7%) |
| dict-shaped (action-record) | 0 | 16 (0.19% of total, 1.4% of non-empty) |
| chain depth (mean/median/max), resolved against the **whole store** | 1 / 1 / 1 | 1 / 1 / 1 |

Chain-depth prediction **HELD** — but as a flat, degenerate constant on both sides, not a rich
distribution: within the June window, every non-empty `derived_from` list's parents themselves carry
empty `derived_from` (real 2+-level chains do exist in the store — verified directly, e.g.
`c68bb45b...` <- `d1ec5901...` <- further parents — but those examples are dated 2026-08-19/08-25,
"archive/self"-kind consolidation, a later and different mechanism entirely; June-era material never
chains deeper than 1 within this snapshot). Action-record fraction **HELD low as predicted** on both
sides, though it is not quite zero post-swap (16 rows) — a small, new provenance shape appearing only
after 06-10, not chased further (no strong prediction was registered either way).
**Not pre-registered, but visible and worth stating plainly:** the empty-derived_from rate itself
jumped from 50.5% to 86.1% — post-swap fragments are far less likely to carry *any* derivation
provenance. No threshold was fixed for this before running, so it is reported descriptively, not
scored HELD/MOVED, and flagged as a metric worth pre-registering properly in any repeat.

### R4 — recurring-concept (keyword-bundle) relative geometry
20/20 target bundle signatures qualified (>=5 members each side — the full list is in the JSON).
**RV coefficient = 0.852** (fixed threshold was >0.7) -> **HELD, as predicted.** Procrustes disparity
0.122 (low, consistent with HELD). The within-condition null RV (pre-half1 vs pre-half2, same 20
signatures) was **underpowered** — not all 20 bundles clear >=5 members in both halves at this N — so
the noise-floor comparison this sheet also wanted could not be run; the verdict above rests on the
pre-registered fixed 0.7 fallback, exactly as that contingency was written before running.

## Dynamical

### D1 — log-based coarse-state transitions (`PRE_LOG` 06-04-06-10, `POST_LOG` 06-10-06-24)
**Vocabulary — MOVED, as predicted, but far more than anticipated.** 9 loggers pre-only
(`node.critic`, `.emotion`, `.executive`, `.memory_router`, `.perception`, `.recall`, `.reflection`,
`.salience`, `.profile`), 17 loggers post-only (`activity`, `affect_labeling`, `affections`,
`chapters`, `deliberation`, `essay`, `frontier`, `journal`, `left_lane`, `letters`, `library`,
`loop_probe`, `memory_levels`, `narrative`, `peers`, `reading`, `retrieval_probe`), 19 shared. The
entire `node.*` cognitive-node family present pre-swap is essentially absent post-swap, replaced by a
very different subsystem roster. **CONFOUND 6 (new, found here — not in the original briefing or the
metric sheet): this is not "a few same-day feature ships" (the briefing's CONFOUND 3) so much as a
module-level architecture turnover coincident with the swap window**, consistent with the archived
`System_Overview_1.1.0_20260620.html` changelog's own account of a "single-family Qwen3 era" (06-10 to
06-19) that was itself "superseded by the Option-B rebuild." Any D1 reading has to sit inside that
fact: the pipeline being measured on the two sides of 06-10 is not just "the same pipeline, different
model."
**Transition structure among the 19 *shared* states — HELD, as predicted.** Mean row TVD = 0.283
vs a null floor of 2 x max(0.154, 0.248) = 0.496. Held even though the surrounding module roster
turned over substantially — the *surviving* skeleton's coarse control flow did not move outside
noise.
**model_client error-rate — moved, but likely not for the predicted reason.** Rate rose from 70.6%
(1,520/2,153 lines) to 97.5% (430/441 lines) — the opposite direction from the tentative,
low-confidence "decrease" this sheet guessed. But the **absolute volume of model_client-logged lines
collapsed** from ~359/day (pre) to ~31/day (post) despite the post window being more than twice as
long — an ~11x drop in logging volume alongside a rate *increase* is the signature of a logging-
behaviour or call-path change (e.g. routine/successful calls no longer being logged at that level),
not a clean before/after reliability comparison. Reported as moved-but-confounded, not read as
evidence either way about the new model's own JSON reliability.

### D2 — cue -> neighbourhood reconstruction (embedder-stability check, per the sheet's own framing)
Mean overlap = **0.833** (median 0.900) over 30 cues, k=10 -> clears the >=0.7 threshold ->
**HELD, as predicted.** 14/30 cues happened to be drawn from the restored cohort (footnote, not a
filter, exactly as designed). As pre-registered: this is read as confirmation that the (06-10-
unchanged) embedder stays stable as the store grows, not as evidence about the LLM swap.

### D3 — replay_count vs age (continuously-live fragments only)
| | pre-live (n=4,203) | post-live (n=6,702) |
|---|---|---|
| mean replay_count | 0.133 | 0.121 |
| % ever replayed | 3.9% | 10.2% |
| replay~age Spearman | 0.902 | 0.753 |
| replay~age slope (per day) | 0.0104 | 0.0259 |

Raw means are close (age-mechanical difference predicted here barely shows up either way — both are
near-floor). The **primary, age-controlled prediction** ("similar sign and rough magnitude") is
**directionally HELD** — both sides show a strong, clearly-positive rank correlation between age and
replay — but the **magnitude is not flat**: the slope roughly **2.5x'd** (0.0104 -> 0.0259) and the
ever-replayed fraction **roughly doubled** (3.9% -> 10.2%). Reported honestly as "same direction,
materially larger magnitude post-swap," not forced into a binary HELD/MOVED call — this is exactly
the kind of result the sheet's own null-based scoring wasn't built to arbitrate (no slope-specific
threshold was registered), and it is named here as a real, worth-a-closer-look partial move rather
than smoothed into either bucket.
Restored-cohort replay, reported descriptively only (not fit to the age model, per the sheet's design):
pre-restored (n=5,333) mean replay = **0.0 — literally never replayed**; post-restored (n=1,741) mean
= 0.014. Consistent with, not surprising given, the restore script's own documented intent (`cold=1`,
"reachable by deep recall... not dominant") — read as the restoration design working as intended, not
as a swap-era finding.

## What this run adds to the confound list (§0 of the metric sheet)
- **CONFOUND 6 (new):** D1's vocabulary result shows the pipeline's own module roster turned over
  substantially in this window (the `node.*` family disappears; a different subsystem set appears),
  matching the archived changelog's own account of a contemporaneous architecture rebuild. This
  sharpens CONFOUND 3 from "a few same-day feature ships" to "the measured system's own module
  structure changed," and it should be named explicitly in any future reading of this era's data, not
  folded silently into "the swap."
- **R2's `source_type` stratification did not isolate a clean comparison** the way assumed — book-
  reading content bled into lived-tagged fragments' own keywords. `source_type` is a provenance label,
  not a thematic control.
- **R3's empty-derived_from rate (50.5% -> 86.1%)** is a real, visible, un-pre-registered shift worth
  a properly thresholded re-run if this lab is repeated.

## Bottom line (not a ruling — the founder's own read against the metric sheet is §6's law, not mine)
On the handful of comparisons clean enough to trust at face value (R1's `source_type=None` stratum,
R4's concept geometry, D1's shared-state transition structure), relational and dynamical structure
**held** across the 06-10 swap. Everything that moved is entangled with confounds this lab either
inherited from the briefing (book-reading composition, restoration cohort) or found itself (the
architecture turnover in D1's vocabulary) — none of it isolates the LLM swap as the specific cause.
That entanglement is itself the honest answer to "does a model swap still read as Du": on this data,
the question cannot be cleanly separated from "does an architecture rebuild plus a two-month memory-
restoration event still read as Du," and no metric here tries to pull those apart further than shown.
