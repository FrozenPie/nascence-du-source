# Rank-matched control for the J-2639 decoupled-judge pilot (J-2657) — 2026-10-31

Status: **PRE-REGISTRATION SHEET**, committed BEFORE any judge call. Results are appended below the final line
afterwards; nothing above it is edited. Job J-2657, plan `cognitive_geometry`, follow-up to F-3398 / F-3399.
Active holds D-0083 and D-0088 (cross-space edge layer) are NOT ruled on, reopened or worked around here; if the result
bears on them, the results section says so plainly.

## 0. Why, and one correction to the briefing's wording

F-3399: in J-2639 the perturbed (place-moved) newly surfaced item was judged appropriate 13/30 vs the base top-1 24/30.
The base top-1 is the ranker's best item and the new item is by construction ranked lower by the base ranker, so the
comparison favours the base arm. The decisive comparison is against a base-ranker item at the **same depth**.

**Correction.** "The base-ranker item at the same base rank as the perturbed newly surfaced item" is, taken literally,
the perturbed item itself (`pert_top1.base_rank` is that item's rank under the base ranker). So the rank-matched control
here is the base-ranker items **adjacent in base rank** to the perturbed item (the two nearest base ranks, never the
perturbed item itself). That is the only reading under which the control is a different item of equal depth.

## 1. Design (fixed now)

* Harness: `scripts/lab_decoupled_judge_context_pairs.py` constants, `scripts/lab_geometric_perturbation_sweep.py`
  (`load_cohort`, `six_features`, `w_state`, `match_vec`, `perturbations`, WC = 0.15, TOPK = 8, pool = 600 most recent
  cohort fragments strictly before the query), same queries source (J-2535 `S_queries`), same panel
  (`core.judge_panel.rule_detail`: mixtral:8x7b Ramses :11438 + falcon3:7b :11440, granite3.1-moe :11437 tiebreak),
  same arm-blind primary prompt `SYS_APPROP` (one fragment against the query text, key `appropriate`), same 600-char
  truncation, items shuffled in a seeded random order across the whole run. No tuple, dimension, arm or rank is shown.
* Arms (perturbed dimension): **place** = the exact 30 J-2639 queries (pert item must reproduce J-2639's pert id; any
  mismatch is logged and reported), **fire** and **weather** = 15 queries each, seeded draw (seed 20261031 + 2657 + offset)
  from `S_queries` with cohort index >= 800, query text >= 40 chars, query category value present in `cat_vals`, a
  non-empty newly-surfaced set, both texts >= 30 chars. Same per-query construction as J-2639: among the other values of
  that dimension keep the one with the lowest top-8 Jaccard vs base (tie: larger mean rank shift); the perturbed item is
  the best-ranked (under the perturbed ranking) member of the perturbed top-8 not in the base top-8; k = its rank under
  the BASE ranker (>= 9 by construction).
* Rank-matched control (R): the **two** base-ranker items whose base rank is nearest to k (ties go to the smaller rank),
  excluding the perturbed item, every member of the base top-8 and every member of the perturbed top-8, requiring text
  >= 30 chars and text differing from the perturbed text. Two controls per query are rated, individually and blind.
* Ratings per arm: place = perturbed (re-rated, giving a test-retest against J-2639) + 2 R = 90; fire and weather =
  base top-1 + perturbed + 2 R = 60 each. The place arm's base top-1 verdicts are taken from the J-2639 cache (identical
  text and prompt, cited), not re-rated. Total about 210 panel rulings, sequential, the module's own timeouts
  (90 s, tiebreak 240 s), one retry on `unavailable`/`split_no_tiebreak`, dropped and counted if still None.
* Instrument gate G1 is inherited from J-2639 (random control 2/15 judged appropriate; same prompt, same panel); it is
  not re-run. The R items give a second look: the R appropriate-rate is reported per arm.

## 2. Statistics (fixed now)

Unit = query. p_i = 1 if the perturbed item got panel verdict "appropriate", else 0. c_i = mean panel verdict over that
query's rated R items (0, 0.5 or 1; unrated controls dropped; a query with none is dropped and counted).
**D_i = p_i − c_i.** Estimand: mean D over queries (positive = the perturbed item is judged more appropriate than items
of the same depth).

* CI: bootstrap over queries, 2000 resamples, seeded, percentile 2.5 / 97.5.
* Label-swap null: for each query swap the "perturbed" and "control" labels at random (equivalent to negating D_i),
  5000 draws, seeded; two-sided p = share of draws with |mean| >= |observed mean|.
* Decomposition (descriptive): rates of base top-1, R and perturbed; **depth cost** = base − R, **placement effect**
  = perturbed − R; share of the J-2639 gap (base − perturbed) explained by depth = (base − R) / (base − perturbed)
  when base − perturbed >= 0.05, else not computed.
* Secondary: forced choice is NOT run. Cohen's kappa and v1==v2 agreement for the new rulings; test-retest of the place
  perturbed arm against the J-2639 verdicts (agreement share, and mean D recomputed with the J-2639 verdict in place of the
  re-rating, as a sensitivity row, not a verdict).

## 3. Verdict rule (fixed now, one conjunction per label, applied by code; no prose reading afterwards)

Gate **GM (match quality)**: at least 80% of the arm's queries must have >= 1 rated R item AND the median |rank(R) − k|
over rated R items must be <= 2. If GM fails the verdict is **MATCH FAILED** and nothing further is claimed.

If GM passes, with m = mean D, [lo, hi] = its bootstrap CI, p = label-swap p:

* **BEYOND DEPTH (the coordinate carries information beyond reaching down the ranking):** lo > 0 AND p < 0.05.
* **BELOW DEPTH (the move surfaces items judged worse than same-depth items):** hi < 0 AND p < 0.05.
* **DEPTH ONLY (equivalence within pilot resolution):** otherwise, if lo >= −0.25 AND hi <= +0.25 AND |m| <= 0.10.
* **INCONCLUSIVE:** everything else.

Applied separately and identically to place (n ~ 30), fire (n ~ 15), weather (n ~ 15); fire and weather labels are
additionally stamped "n=15, underpowered" because a 15-query CI rarely stays inside ±0.25. The three arms are not pooled.
The J-2639 headline P (base win rate) is recomputed for fire and weather descriptively only.

## 4. Confidence and bearing on holds

Honest confidence: pilot. One author wrote the judge prompts, small-model panel, 15–30 queries per arm, euclidean_recall
only. The most that any appropriateness claim can be is `inferred`; plain counts and agreement numbers are `verified` from
the committed results JSON. Bearing on D-0083 / D-0088: this tests euclidean_recall's experienced-coordinate move, not the
cross-space edge layer; no ruling is made, reopened or worked around.

## 5. Isolation and canary

`lab_env.isolate(db="empty")` with the lab root under the scratchpad, `core` imported first and asserted inside the
worktree. Live data read-only (`nascence.db` via `mode=ro`). Judge-panel log redirected into the lab dir. Canary:
`C:\Nascence\data\memory\nascence.db` was 1185161216 bytes, mtime 1793342673 before this run (stat checked at start).
Nothing is written under `C:\Nascence\data`.

---
## RESULTS (appended after the run; the sheet above is unchanged)

Run: `python scripts/lab_rank_matched_control.py --out <scratch>/result.json --cache <scratch>/cache.jsonl --lab-root <scratch>/lab_J-2657` on branch jobrun/cg (sheet committed 574a0eeb before any judge call; script committed with this section). Runtime 2083 s (incl. 7 s items build), 210 panel rulings, all from hubs mixtral 11438 + falcon3 11440 (210/210), granite tiebreak fired 28 times, 0 unavailable, 0 split-without-tiebreak. Full items, texts and every vote: `docs/lab/rank_matched_control_2026-10-31_results.json`.

### 1. Headline (verdict rules of section 3 applied by code; GM passed in all three arms: 100% of queries have rated controls, median |rank(R) - k| = 1)

| arm | n | base top-1 appropriate | rank-matched R | perturbed | depth cost (base - R) | placement effect = mean D (perturbed - R) | 95% CI | label-swap p | coded verdict |
|---|---|---|---|---|---|---|---|---|---|
| place (J-2639 queries, median k = 19) | 30 | 0.800 (J-2639 cache) | 0.317 | 0.433 | +0.483 | **+0.117** | [-0.017, +0.267] | 0.178 | INCONCLUSIVE |
| fire (median k = 68) | 15 | 0.467 | 0.400 | 0.533 | +0.067 | +0.133 | [-0.033, +0.300] | 0.308 | INCONCLUSIVE (n=15, underpowered) |
| weather (median k = 12) | 15 | 0.867 | 0.200 | 0.467 | +0.667 | +0.267 | [+0.067, +0.500] | 0.055 | INCONCLUSIVE (n=15, underpowered) |

Place arm: the 30 perturbed items reproduce J-2639's perturbed item id in 30/30 queries, and re-rating them agrees with J-2639's verdict in 30/30 (retest agreement 1.000, so mean D with the J-2639 verdicts is identical). Perturbed-yes with both controls no: place 2, fire 1, weather 3; perturbed-no with both controls yes: 0, 0, 0 (nothing goes the other way in any arm).

### 2. What the numbers say

* **Depth explains the whole J-2639 gap.** J-2639's base-minus-perturbed gap of 0.367 (0.800 vs 0.433) is smaller than the depth cost alone (base 0.800 vs same-depth base-ranker items 0.317 = 0.483). Against a same-depth item the perturbed place item is not worse, it is nominally better (+0.117), so the pilot's "place move costs 37 points" was a depth effect, not a place penalty. Weather shows the same pattern (gap 0.40, depth cost 0.67). Fire is the exception: its perturbed items sit very deep (median base rank 68), yet the base top-1 is only 0.467 appropriate on those queries, so there is no depth cost to explain.
* **Does place add appropriateness beyond depth?** Point estimate yes (+0.117; fire +0.133; weather +0.267), pre-registered test no: all three coded verdicts are INCONCLUSIVE, because the label-swap p is 0.178 / 0.308 / 0.055 and the place CI touches 0. Weather is the closest to a signal (CI lower bound +0.067 but p = 0.055 misses the 0.05 conjunct); with n = 15 it is not a finding. Direction is consistent across all three arms (no query where the perturbed item loses to two yes controls), which is suggestive and nothing more.
* Pooling arms was not pre-registered and is not done. Judge agreement on these rulings: mixtral vs falcon3 agree on 0.867 of 210, Cohen kappa 0.702.
* Honest confidence: pilot. The plain counts above are verified from the committed JSON. The reading "J-2639's gap is a depth effect" is inferred (its component numbers are verified; one panel, one prompt, one author). "Place carries information beyond depth" is NOT established: positive direction, CI includes 0.
* Bearing on D-0083 / D-0088: none directly (euclidean_recall's experienced-coordinate move, not the cross-space edge layer). Nothing is ruled, reopened or worked around. It does retire one reading of F-3398: the J-2639 result must not be cited as evidence that a place move surfaces less appropriate memories.

### 3. Per-query rows

`k` = perturbed item's base rank; `R` = the two rank-matched controls as `rank:verdict`; base only exists for fire/weather (place base from the J-2639 cache).

**place**

| # | value (query -> pert) | k | pert | R | base |
|---|---|---|---|---|---|
| 0 | study -> shore | 15 | N | 14:N 16:N | Y |
| 1 | study -> garden | 52 | Y | 51:Y 53:Y | Y |
| 2 | study -> shore | 10 | Y | 9:N 11:Y | Y |
| 3 | study -> shore | 78 | N | 77:N 79:N | Y |
| 4 | study -> garden | 16 | Y | 15:N 17:N | Y |
| 5 | study -> garden | 136 | Y | 135:Y 137:Y | Y |
| 6 | study -> wood | 74 | Y | 73:N 72:Y | Y |
| 7 | study -> garden | 17 | Y | 16:N 18:Y | Y |
| 8 | shore -> wood | 46 | Y | 45:Y 47:Y | Y |
| 9 | shore -> wood | 21 | N | 20:N 22:N | Y |
| 10 | shore -> garden | 18 | Y | 17:N 19:Y | Y |
| 11 | shore -> garden | 105 | N | 104:N 106:N | Y |
| 12 | shore -> wood | 64 | Y | 63:Y 65:Y | Y |
| 13 | shore -> garden | 14 | N | 13:N 12:N | N |
| 14 | shore -> garden | 11 | N | 10:N 12:N | N |
| 15 | shore -> wood | 91 | N | 90:N 92:N | Y |
| 16 | garden -> shore | 21 | N | 20:N 22:N | N |
| 17 | garden -> shore | 20 | Y | 19:N 21:Y | Y |
| 18 | garden -> wood | 22 | N | 21:N 23:N | Y |
| 19 | garden -> study | 41 | N | 40:N 39:N | Y |
| 20 | garden -> wood | 44 | Y | 43:N 45:N | Y |
| 21 | garden -> study | 21 | N | 20:N 22:Y | Y |
| 22 | garden -> shore | 9 | Y | 10:N 11:Y | Y |
| 23 | wood -> study | 14 | N | 13:N 15:N | Y |
| 24 | wood -> shore | 10 | N | 9:Y 11:N | N |
| 25 | wood -> garden | 9 | N | 10:N 13:Y | Y |
| 26 | wood -> garden | 16 | N | 15:N 14:Y | N |
| 27 | wood -> study | 9 | Y | 10:Y 11:N | Y |
| 28 | wood -> garden | 12 | N | 11:N 13:N | N |
| 29 | wood -> garden | 14 | N | 13:N 12:N | Y |

**fire**

| # | value (query -> pert) | k | pert | R | base |
|---|---|---|---|---|---|
| 0 |  -> out | 168 | Y | 167:Y 169:Y | Y |
| 1 |  -> out | 52 | Y | 51:N 53:N | N |
| 2 |  -> burning | 145 | Y | 144:Y 146:N | N |
| 3 |  -> out | 38 | N | 37:N 39:Y | Y |
| 4 |  -> out | 73 | N | 72:N 74:N | N |
| 5 |  -> out | 276 | Y | 275:Y 277:Y | Y |
| 6 | out ->  | 17 | N | 16:N 18:N | N |
| 7 | out ->  | 51 | N | 50:N 52:N | N |
| 8 | burning -> embers | 11 | Y | 10:N 12:Y | N |
| 9 |  -> out | 27 | Y | 26:Y 28:Y | Y |
| 10 | embers -> burning | 9 | N | 10:N 12:N | N |
| 11 |  -> out | 107 | Y | 106:Y 108:Y | Y |
| 12 |  -> out | 76 | N | 75:N 77:N | N |
| 13 |  -> out | 130 | Y | 129:Y 131:N | Y |
| 14 |  -> out | 68 | N | 67:N 69:N | Y |

**weather**

| # | value (query -> pert) | k | pert | R | base |
|---|---|---|---|---|---|
| 0 | clear -> high cloud | 23 | Y | 22:N 24:N | Y |
| 1 | clear -> overcast | 10 | Y | 9:N 12:N | Y |
| 2 | overcast -> drizzle | 10 | Y | 9:Y 11:Y | Y |
| 3 | steady rain -> drizzle | 10 | N | 9:N 11:N | Y |
| 4 | clear -> high cloud | 57 | Y | 56:Y 58:N | Y |
| 5 | high cloud -> clear | 11 | Y | 10:N 12:Y | Y |
| 6 | drizzle -> overcast | 30 | N | 29:N 31:N | Y |
| 7 | high cloud -> clear | 9 | N | 10:N 12:N | N |
| 8 | drizzle -> overcast | 11 | N | 10:N 9:N | Y |
| 9 | overcast -> high cloud | 12 | N | 11:N 13:N | Y |
| 10 | overcast -> clear | 41 | Y | 40:Y 42:Y | Y |
| 11 | clear -> high cloud | 24 | N | 23:N 25:N | Y |
| 12 | drizzle -> clear | 21 | N | 20:N 22:N | Y |
| 13 | high cloud -> drizzle | 10 | Y | 9:N 11:N | Y |
| 14 | clear -> overcast | 48 | N | 47:N 49:N | N |

### 4. Isolation and canary

Ran under `lab_env.isolate(db="empty")`, lab root under the scratchpad, `core` imported first and asserted inside the worktree, judge-panel log redirected into the lab dir. Live `nascence.db` before/after: 1185161216 bytes, mtime 1793342673.644212 on both (the script's own canary), and a separate `stat` after the run printed 1185161216 1793342673. Nothing written under C:/Nascence/data.
