# Negative-control arm for the J-2663 placement effect (permuted coordinates) -- 2026-11-16

Status: **PRE-REGISTRATION SHEET**, committed BEFORE any judge call (item sets built with `--stage items`, no panel call).
Results are appended below the final line; nothing above it is edited. Job J-2673, plan `cognitive_geometry`, follow-up to
J-2663 / F-3421 via design note F-3422. Active holds D-0083 and D-0088 (cross-space edge layer) are not ruled on, reopened or
worked around; if the result bears on them the results section says so.

## 0. Question
J-2663 found D (perturbed item minus two base-rank-neighbour controls) about +0.15 for place and weather (BEYOND DEPTH). Does that
survive an information-free coordinate? If the real coordinate carries the signal, permuting the arm dimension's codes should give
D near 0 (DEPTH ONLY / INCONCLUSIVE). If D is again about +0.15 and BEYOND DEPTH, the J-2663 effect is a selection artefact of
re-ranking (the perturbed item is the best member of a second scoring function).

## 1. Design
* Harness unchanged: `scripts/lab_rank_matched_replication.py` -> `lab_rank_matched_control.py` (construct, arm_stats, verdict rule,
  N_CTRL=2, TXT_MAX 600, WC 0.15, TOPK 8, 600-fragment pool, same `rule_detail` panel: mixtral:8x7b + falcon3:7b, granite tiebreak,
  same arm-blind `SYS_APPROP`, same one-retry rule, same G1 random control on the first 30 items). New driver
  `scripts/lab_rank_matched_negctrl_J-2673.py` adds ONE step: after `load_cohort()`, `C.code[arm]` is shuffled among the fragments with
  code >= 0 (numpy default_rng(20261031 + 2673 + 77 + off), off 1 place / 2 weather; -1 codes stay), so the match term still
  re-sorts the pool but is unrelated to the real place/weather. Query values and perturbations are read from the permuted codes.
* New query seed 20261031 + 2673. Excluded: the 58 J-2657 ids and every J-2663 place and weather item query id (201 distinct ids in total).
* **Shortfall, stated before any judge call:** only 75 eligible new queries remain per arm (276 S_queries minus 201 excluded; eligibility as J-2663).
  Both arms therefore use the same 75 queries (the pool is exhausted; arm items still differ because the permutations differ), n = 75 not 90.
  Both arms built 75/75. Item-set sha256: place `3a45f8dd099dc0d9302b56549e12dd822b6a8853c280fedcc4616e9d148af602`,
  weather `6bef766f0cc56fa33d968dcac7d849603dc05458c06fab1ee06491961ebed102`. Place and weather are not independent.
* Per query: perturbed item + 2 rank-matched controls = 3 rulings (225 per arm) plus 30 random-control rulings per arm (G1).

## 2. Statistics and verdict rule: as J-2663, applied by code, per arm
D_i = p_i - c_i; mean D, bootstrap CI (2000), label-swap p (5000). GM gate, then BEYOND DEPTH (lo > 0 and p < 0.05), BELOW DEPTH, DEPTH ONLY
(lo >= -0.25, hi <= 0.25, |m| <= 0.10), else INCONCLUSIVE. Reading pre-registered: negative control PASSES (coordinate carries signal) if
both arms are not BEYOND DEPTH and mean D is clearly below J-2663's +0.15; it FAILS (re-ranking artefact) if an arm is BEYOND DEPTH with
D about +0.15. With n = 75 (SE about 0.046) an intermediate D (+0.05 to +0.10) will be INCONCLUSIVE and is reported as such, a partial
reduction not a clean pass. Pooled-with-pilot output of the J-2663 driver is not meaningful here and is ignored. G1 as in J-2663
(random control rate <= 0.25 and below R).

## 3. Confidence and bearing on holds
euclidean_recall only, one prompt author, small-model two-family panel, appropriateness a proxy. No bearing on D-0083 / D-0088 expected
(not the cross-space edge layer nor the sec5.3 felt-response check); no ruling made. Du is down; hubs shared with other labs; one process
per arm run sequentially, circuit breaker on.

## 4. Isolation and canary
`lab_env.isolate(db="empty")`, lab root in the scratchpad, `core` imported first and asserted under the tree, live `data/memory/nascence.db`
opened `mode=ro` only. Canary recorded in the results JSON; top-level data/ file sizes/mtimes compared before and after.

---
## RESULTS (appended after the run; the sheet above is unchanged)
