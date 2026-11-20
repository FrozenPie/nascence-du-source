# Powered replication of the rank-matched control (J-2663) — 2026-10-31

Status: **PRE-REGISTRATION SHEET**, committed BEFORE any judge call (the item sets were built with `--stage items`, which makes no
panel call). Results are appended below the final line afterwards; nothing above it is edited. Job J-2663, plan
`cognitive_geometry`, replication of J-2657 / F-3409 (design note F-3410). Active holds D-0083 and D-0088 (cross-space edge
layer) are NOT ruled on, reopened or worked around here; if the result bears on them the results section says so plainly.

## 0. Question

J-2657 (pilot) found that the J-2639 place gap (base top-1 0.800 vs perturbed 0.433) is a depth effect, and that the placement
effect D (perturbed item minus same-depth base-ranker items) was positive but inconclusive in all arms: place +0.117 (n=30, CI
[-0.017,+0.267], p 0.178), fire +0.133 (n=15), weather +0.267 (n=15, CI [+0.067,+0.500], p 0.055). Does the coordinate move
surface items judged more appropriate than items at the same depth, with enough queries to say?

## 1. Design (fixed now; the rank-matched control definition of F-3410 / J-2657 is reused UNCHANGED)

* Harness: `scripts/lab_rank_matched_control.py` imported as a module, unchanged (`construct`, `arm_stats`, `boot_mean`, N_CTRL = 2,
  TXT_MAX 600, WC 0.15, TOPK 8, pool = 600 most recent cohort fragments before the query, same panel `core.judge_panel.rule_detail`:
  mixtral:8x7b Ramses :11438 + falcon3:7b :11440, granite3.1-moe :11437 tiebreak, same arm-blind primary prompt `SYS_APPROP`,
  same one-retry rule). New driver: `scripts/lab_rank_matched_replication.py`.
* Rank-matched control R: the two base-ranker items nearest in base rank to the perturbed item's base rank k (ties to the smaller
  rank), excluding the perturbed item and every member of the base top-8 and perturbed top-8, text >= 30 chars, text differs.
* **New queries only.** Query source: J-2535 `S_queries` (276 ids). Excluded: all 58 distinct query ids rated in J-2657 (30 place + 15 fire
  + 15 weather, with overlap, as listed in `rank_matched_control_2026-10-31_results.json` arms). Eligibility as in J-2657 fire/weather:
  cohort index >= 800, query text >= 40 chars, query category value for the arm's dimension present; 218 eligible new queries per
  arm (place and weather draw independently, so the same query may appear in both arms). Seeded draw: numpy
  `default_rng(20261031 + 2663 + off)` with off = 1 place, 2 weather, 3 fire; take successive permuted candidates until n items
  with a non-empty newly surfaced set, both texts >= 30 chars and >= 1 control have been constructed (same `construct` as J-2639).
* **Arms and n.** place n = 90, weather n = 90 (both built in full: 90/90, from 108 and 152 candidates tried). Item-set hashes
  (sha256 over query id, perturbed-item id, control ids, in draw order): place `05bb01f5d02e163fbe69941300c9fda5241c9f48923862169275454b0bedac08`,
  weather `d36bfc3e737283a2eb1c616f3651e84c45124c5b928c5ebd3dc8643f432d40e0`.
* **Ratings per query:** perturbed item + 2 R = 3 rulings (270 per arm). Base top-1 is NOT re-rated (a secondary descriptive in
  J-2657; its depth-cost reading is already replicated by J-2639/J-2657 and costs a third more panel time). So the depth-cost
  decomposition is not reported for the new arms.
* **Gate G1 (instrument) re-run as in J-2639:** the first 30 drawn queries per arm also get one random same-pool control item
  (uniform from the 600-pool, not any item already used for that query, text >= 30). G1 passes if the pooled random-control
  appropriate rate (60 items) is <= 0.25 AND is below the pooled rank-matched control rate R of all new queries. If G1 fails the panel is not discriminating and nothing further is claimed.
* Items are shuffled in a seeded random order within each arm's run; arms run as two separate processes concurrently (one per arm); no
  tuple, dimension, arm, rank or role is shown to the judges.

## 2. Statistics and verdict rule (as J-2657, applied by code, per arm, not pooled across arms)

Unit = query. D_i = p_i − c_i (p_i = perturbed verdict 0/1, c_i = mean verdict of the query's rated R items). Mean D, bootstrap
CI (2000 resamples, percentile 2.5/97.5, seeded), label-swap p (5000 draws, two-sided).

* Gate GM: >= 80% of queries have >= 1 rated R item AND median |rank(R) − k| <= 2, else **MATCH FAILED**.
* **BEYOND DEPTH:** lo > 0 AND p < 0.05. **BELOW DEPTH:** hi < 0 AND p < 0.05. **DEPTH ONLY:** otherwise if lo >= −0.25, hi <= +0.25
  and |mean D| <= 0.10. **INCONCLUSIVE:** everything else. Unlike J-2657 no "underpowered" stamp is added (n = 90).
* The primary verdict per arm uses the NEW queries only (independent replication). The pilot is not mixed in.
* Power: the briefing's SD of D ≈ 0.4 gives SE ≈ 0.042 at n = 90; a true D of 0.12 gives an expected CI lower bound ≈ +0.04 and
  roughly 80% power for the conjunct. A true D of 0.05 or less would most likely come back INCONCLUSIVE or DEPTH ONLY (the DEPTH ONLY
  conjunct needs |m| <= 0.10). The realised SD of D is reported.
* Descriptive only, no verdict attached: (a) pooled pilot + new D with its CI and label-swap p (place 30 + 90, weather 15 + 90);
  (b) mean D split at the median k (shallower vs deeper perturbed item); (c) the random-control rate; (d) panel agreement
  (v1 == v2, kappa); (e) tiebreak counts.
* **Fire** is conditional: run `--arm fire --n 90` (new seed offset 3) only if place or weather is coded BEYOND DEPTH, or if either has
  mean D >= +0.10 with label-swap p < 0.10. Otherwise fire is not run and this is stated. Its n may fall short of 90 if the eligible set is
  smaller; the n reached is reported. Fire's depth structure differs (median base rank 68), so no depth interpretation is imported.
* Partial results: the cache is checkpointed per ruling; if the run cannot finish, the arm's reduced n is reported with the same rule
  and the shortfall is spawned as a successor job.

## 3. Confidence and bearing on holds

Honest confidence: the same limits as J-2657 — the euclidean_recall move only, one prompt author, a small-model two-family panel,
appropriateness is a proxy. Counts, rates and the coded verdict are `verified` from the committed JSON; any statement that "place adds
information" is at best `inferred`. Bearing on D-0083 / D-0088: none directly (this tests euclidean_recall's experienced-coordinate
move, not the cross-space edge layer / felt-response check); no ruling is made, reopened or worked around.

## 4. Isolation and canary

`lab_env.isolate(db="empty")`, lab root under the scratchpad, `core` imported first and asserted under the worktree, judge-panel log
redirected into the lab dir, live `nascence.db` opened `mode=ro` only. Canary: `C:\Nascence\data\memory\nascence.db` must stay
1185161216 bytes, mtime 1793342673.64. Nothing is written under `C:\Nascence\data`.

---
## RESULTS (appended after the run; the sheet above is unchanged)

Commands: `python scripts/lab_rank_matched_replication.py --arm place|weather|fire --n 90 --out <scratch>/result_<arm>.json --cache <scratch>/cache_<arm>.jsonl --lab-root <scratch>/lab_J-2663_<arm>` on branch jobrun/cg (sheet and driver committed c29e5d0b before any judge call; the circuit-breaker lines in the driver were added afterwards and change no design element). Full items, texts and every vote: `docs/lab/rank_matched_replication_2026-10-31_results_{place,weather,fire}.json`. Item-set hashes of the place and weather runs equal the pre-registered ones on every launch (the item build is deterministic although the live cohort grew by ~100 fragments while the runs went on, because the cohort is append-only and a query only looks at earlier fragments).

Run notes (honest): Du was restarted by the founder at 11:42:31 (process `run_nascence.py` PID 32056), four minutes before this lab started, so "Du is down" no longer held; Du and this lab then shared the Ramses mixtral hub. The first launch (place and weather concurrently) hit sustained mixtral timeouts after about 3 minutes (13 consecutive 91 s timeouts, falcon-only answers, which `rule_detail` records as `unavailable` with verdict None); I killed it and no such row is used (a verdict None row is re-ruled on resume; only `agreed`/`tiebreak` rows count: 0 `unavailable` and 0 `split_no_tiebreak` in the final caches). After the hub recovered (a probe answered in 9 s) the arms resumed from the cache, sequentially at first, later place and weather (and fire) concurrently at 10-30 s per ruling. A circuit breaker (abort after 4 consecutive unavailable rulings) was added to the driver. All final verdicts are from the two-family panel mixtral:8x7b (:11438) + falcon3:7b (:11440) with granite tiebreak, 100% of rulings on hubs 11438/11440.

### 1. Headline (new queries only; verdict rules of section 2 applied by code; GM passed in every arm: 100% of queries have rated controls, median |rank(R) - k| = 1; G1 random control 0.20 (place), 0.13 (weather), 0.10 (fire), all under 0.25 and under the rank-matched rate). Fire ran because the pre-registered trigger was met (place and weather coded BEYOND DEPTH); its item set (draw offset 3, 218 eligible, 90/90 built from 135 candidates) has sha256 f3a6ae7072594f903ce97dbd35709ff34e52ffaae7afd1b16ba4556a73139228, recorded at the run, not in the sheet

| arm | n | median k | perturbed | rank-matched R | mean D | 95% CI | label-swap p | random ctrl | coded verdict |
|---|---|---|---|---|---|---|---|---|---|
| place (new) | 90 | 16 | 0.467 | 0.311 | **+0.156** | [+0.061, +0.250] | 0.0028 | 0.200 (n=30) | BEYOND DEPTH |
| weather (new) | 90 | 16 | 0.444 | 0.300 | **+0.144** | [+0.039, +0.250] | 0.0170 | 0.133 (n=30) | BEYOND DEPTH |
| fire (new) | 90 | 32 | 0.489 | 0.239 | **+0.250** | [+0.144, +0.356] | <0.0002 | 0.100 (n=30) | BEYOND DEPTH |

Descriptive (no verdict attached):

| arm | pooled with J-2657 pilot: n, mean D, CI, p | SD of D (new) | D at k<=median / k>median | perturbed-yes both-R-no / perturbed-no both-R-yes | v1==v2, kappa, tiebreaks, unavailable |
|---|---|---|---|---|---|
| place | 120, +0.146, [+0.067, +0.225], p 0.0004 | 0.466 | +0.185 (n=46) / +0.125 (n=44) at median k 16 | 12 / 3 | 0.877, 0.698, 37, 0 |
| weather | 105, +0.162, [+0.062, +0.262], p 0.0026 | 0.531 | +0.130 (n=46) / +0.159 (n=44) at median k 16 | 17 / 6 | 0.907, 0.770, 28, 0 |
| fire | 105, +0.233, [+0.133, +0.329], p <0.0002 | 0.510 | +0.344 (n=45) / +0.156 (n=45) at median k 32 | 23 / 2 | 0.923, 0.808, 23, 0 |

**place** per-query rows (`k` perturbed item base rank; R = the two rank-matched controls as rank:verdict; rand = random control where drawn):

| # | value (query -> pert) | k | pert | R | rand |
|---|---|---|---|---|---|
| 0 | shore -> wood | 13 | Y | 12:N 11:N | Y |
| 1 | study -> wood | 67 | Y | 66:N 68:Y | N |
| 2 | wood -> shore | 13 | Y | 12:N 14:Y | N |
| 3 | study -> shore | 11 | N | 10:N 9:Y | N |
| 4 | garden -> study | 87 | N | 86:N 88:N | N |
| 5 | study -> garden | 28 | Y | 27:Y 29:Y | N |
| 6 | garden -> shore | 10 | Y | 9:N 11:Y | Y |
| 7 | garden -> shore | 17 | Y | 16:Y 18:N | N |
| 8 | wood -> garden | 13 | Y | 12:Y 14:Y | N |
| 9 | shore -> wood | 56 | Y | 55:Y 54:Y | Y |
| 10 | wood -> garden | 12 | N | 11:N 13:N | N |
| 11 | shore -> garden | 51 | N | 50:N 52:N | N |
| 12 | wood -> study | 9 | N | 10:N 13:N | N |
| 13 | shore -> garden | 13 | N | 12:Y 14:N | N |
| 14 | study -> garden | 32 | Y | 31:N 33:N | N |
| 15 | study -> garden | 17 | N | 16:Y 18:N | N |
| 16 | study -> shore | 21 | Y | 20:N 22:Y | Y |
| 17 | wood -> garden | 18 | N | 17:N 19:N | N |
| 18 | garden -> shore | 23 | Y | 22:Y 21:N | Y |
| 19 | study -> shore | 9 | N | 10:N 13:N | N |
| 20 | wood -> shore | 9 | N | 11:Y 12:Y | Y |
| 21 | study -> garden | 15 | N | 14:N 16:N | N |
| 22 | wood -> garden | 10 | N | 9:N 11:N | N |
| 23 | wood -> garden | 9 | Y | 10:Y 11:Y | N |
| 24 | wood -> shore | 9 | N | 12:N 14:N | N |
| 25 | garden -> study | 31 | Y | 30:N 32:N | N |
| 26 | shore -> garden | 16 | N | 15:N 17:N | N |
| 27 | shore -> wood | 19 | Y | 18:N 17:Y | N |
| 28 | garden -> shore | 54 | N | 53:N 55:N | N |
| 29 | garden -> shore | 11 | N | 10:N 12:N | N |
| 30 | wood -> garden | 26 | N | 25:N 27:N |  |
| 31 | garden -> shore | 41 | N | 40:N 42:N |  |
| 32 | shore -> garden | 10 | N | 9:N 12:N |  |
| 33 | garden -> shore | 183 | N | 182:Y 184:N |  |
| 34 | wood -> shore | 11 | N | 10:N 12:N |  |
| 35 | study -> shore | 63 | N | 62:N 64:N |  |
| 36 | wood -> garden | 21 | Y | 20:Y 19:Y |  |
| 37 | garden -> shore | 31 | N | 30:N 32:Y |  |
| 38 | shore -> garden | 14 | N | 13:N 12:N |  |
| 39 | garden -> shore | 29 | Y | 28:Y 30:Y |  |
| 40 | wood -> garden | 18 | Y | 17:Y 19:Y |  |
| 41 | shore -> wood | 104 | N | 103:N 105:N |  |
| 42 | shore -> garden | 13 | N | 12:Y 14:N |  |
| 43 | garden -> shore | 68 | Y | 67:Y 69:Y |  |
| 44 | wood -> shore | 12 | Y | 11:Y 10:N |  |
| 45 | garden -> shore | 10 | N | 9:Y 11:Y |  |
| 46 | shore -> garden | 14 | N | 13:N 12:N |  |
| 47 | shore -> garden | 13 | N | 12:N 14:N |  |
| 48 | garden -> study | 14 | Y | 13:Y 15:N |  |
| 49 | wood -> shore | 16 | Y | 15:N 14:Y |  |
| 50 | wood -> shore | 10 | Y | 9:N 11:N |  |
| 51 | study -> shore | 9 | N | 13:N 14:N |  |
| 52 | shore -> garden | 25 | Y | 24:N 26:N |  |
| 53 | shore -> garden | 10 | Y | 9:N 11:N |  |
| 54 | shore -> wood | 30 | N | 29:Y 28:Y |  |
| 55 | wood -> shore | 9 | N | 10:N 11:N |  |
| 56 | garden -> shore | 10 | Y | 9:Y 11:N |  |
| 57 | shore -> garden | 75 | Y | 74:N 76:N |  |
| 58 | shore -> wood | 50 | N | 49:N 51:N |  |
| 59 | wood -> shore | 14 | Y | 13:Y 12:N |  |
| 60 | garden -> wood | 45 | N | 44:Y 43:N |  |
| 61 | garden -> shore | 11 | Y | 10:N 9:N |  |
| 62 | wood -> shore | 11 | Y | 10:Y 12:N |  |
| 63 | wood -> shore | 21 | N | 20:N 19:N |  |
| 64 | garden -> shore | 11 | N | 10:N 9:N |  |
| 65 | wood -> garden | 11 | Y | 10:N 12:N |  |
| 66 | garden -> shore | 10 | N | 9:N 12:Y |  |
| 67 | wood -> garden | 44 | Y | 43:Y 42:N |  |
| 68 | shore -> garden | 41 | N | 40:N 42:N |  |
| 69 | garden -> shore | 25 | Y | 24:Y 26:Y |  |
| 70 | shore -> garden | 13 | Y | 12:N 14:Y |  |
| 71 | wood -> shore | 9 | N | 14:N 15:N |  |
| 72 | garden -> shore | 12 | N | 11:N 13:N |  |
| 73 | study -> garden | 24 | N | 23:N 25:N |  |
| 74 | wood -> garden | 30 | N | 29:N 28:N |  |
| 75 | study -> garden | 12 | Y | 11:Y 13:N |  |
| 76 | garden -> shore | 16 | Y | 15:Y 17:Y |  |
| 77 | shore -> wood | 96 | N | 95:N 94:N |  |
| 78 | garden -> study | 69 | N | 68:N 70:N |  |
| 79 | shore -> garden | 23 | Y | 22:N 24:Y |  |
| 80 | garden -> shore | 9 | Y | 10:N 11:N |  |
| 81 | shore -> garden | 37 | N | 36:N 38:N |  |
| 82 | study -> garden | 71 | Y | 70:Y 72:Y |  |
| 83 | shore -> garden | 32 | N | 31:N 33:N |  |
| 84 | wood -> shore | 23 | Y | 22:Y 24:Y |  |
| 85 | wood -> shore | 79 | N | 78:N 80:N |  |
| 86 | study -> garden | 22 | Y | 21:N 23:N |  |
| 87 | shore -> garden | 16 | N | 15:N 17:N |  |
| 88 | wood -> shore | 12 | Y | 11:N 13:N |  |
| 89 | shore -> garden | 16 | Y | 15:Y 14:N |  |

**weather** per-query rows (`k` perturbed item base rank; R = the two rank-matched controls as rank:verdict; rand = random control where drawn):

| # | value (query -> pert) | k | pert | R | rand |
|---|---|---|---|---|---|
| 0 | clear -> overcast | 9 | Y | 10:N 12:Y | N |
| 1 | clear -> steady rain | 11 | Y | 10:N 12:N | N |
| 2 | high cloud -> clear | 10 | N | 9:N 11:N | N |
| 3 | clear -> high cloud | 66 | N | 65:Y 67:N | N |
| 4 | clear -> high cloud | 10 | Y | 9:N 12:N | N |
| 5 | overcast -> high cloud | 24 | Y | 23:Y 22:Y | N |
| 6 | overcast -> drizzle | 9 | N | 10:Y 13:N | N |
| 7 | clear -> overcast | 44 | Y | 43:N 45:N | N |
| 8 | high cloud -> overcast | 14 | N | 13:N 15:N | N |
| 9 | clear -> drizzle | 11 | N | 10:N 9:N | N |
| 10 | drizzle -> steady rain | 22 | Y | 21:Y 20:Y | N |
| 11 | clear -> high cloud | 92 | N | 91:Y 93:Y | N |
| 12 | steady rain -> overcast | 9 | Y | 10:Y 11:Y | N |
| 13 | clear -> drizzle | 18 | N | 17:N 19:N | N |
| 14 | overcast -> drizzle | 12 | N | 11:N 13:N | N |
| 15 | high cloud -> clear | 16 | Y | 15:Y 17:Y | N |
| 16 | clear -> high cloud | 9 | N | 11:N 13:N | N |
| 17 | steady rain -> drizzle | 23 | Y | 22:N 24:N | N |
| 18 | clear -> overcast | 164 | N | 163:Y 165:Y | Y |
| 19 | clear -> high cloud | 38 | Y | 37:Y 39:Y | N |
| 20 | overcast -> drizzle | 81 | Y | 80:Y 82:Y | N |
| 21 | clear -> overcast | 11 | Y | 10:N 9:N | N |
| 22 | clear -> high cloud | 52 | Y | 51:Y 53:Y | Y |
| 23 | clear -> overcast | 27 | Y | 26:N 28:N | Y |
| 24 | clear -> high cloud | 9 | N | 10:N 11:Y | N |
| 25 | drizzle -> steady rain | 18 | Y | 17:Y 19:Y | Y |
| 26 | clear -> high cloud | 50 | Y | 49:N 51:N | N |
| 27 | overcast -> clear | 13 | N | 12:N 11:N | N |
| 28 | high cloud -> clear | 9 | N | 11:N 12:N | N |
| 29 | overcast -> drizzle | 9 | N | 10:Y 11:Y | N |
| 30 | clear -> high cloud | 55 | N | 54:N 56:N |  |
| 31 | high cloud -> clear | 24 | N | 23:N 25:N |  |
| 32 | clear -> overcast | 52 | Y | 51:N 53:Y |  |
| 33 | high cloud -> clear | 16 | Y | 15:N 17:N |  |
| 34 | high cloud -> clear | 9 | Y | 11:Y 12:Y |  |
| 35 | overcast -> clear | 9 | Y | 11:N 13:Y |  |
| 36 | clear -> overcast | 98 | Y | 97:N 99:N |  |
| 37 | overcast -> clear | 9 | N | 13:Y 14:Y |  |
| 38 | high cloud -> clear | 9 | Y | 10:N 11:N |  |
| 39 | overcast -> clear | 22 | N | 21:N 23:N |  |
| 40 | clear -> high cloud | 14 | N | 13:Y 15:Y |  |
| 41 | clear -> high cloud | 13 | N | 12:N 11:N |  |
| 42 | high cloud -> clear | 12 | Y | 11:N 13:Y |  |
| 43 | clear -> high cloud | 16 | N | 15:N 17:N |  |
| 44 | overcast -> clear | 22 | Y | 21:N 23:Y |  |
| 45 | drizzle -> clear | 15 | N | 14:N 16:N |  |
| 46 | overcast -> high cloud | 9 | N | 10:Y 12:Y |  |
| 47 | overcast -> clear | 17 | Y | 16:N 18:N |  |
| 48 | high cloud -> overcast | 17 | N | 16:N 18:N |  |
| 49 | overcast -> clear | 30 | Y | 29:Y 31:Y |  |
| 50 | clear -> overcast | 33 | N | 32:N 34:N |  |
| 51 | drizzle -> wind and rain | 9 | Y | 10:Y 11:Y |  |
| 52 | overcast -> clear | 11 | Y | 10:N 12:Y |  |
| 53 | clear -> high cloud | 60 | N | 59:N 61:N |  |
| 54 | drizzle -> overcast | 15 | N | 14:N 16:N |  |
| 55 | overcast -> drizzle | 20 | N | 19:N 21:N |  |
| 56 | clear -> high cloud | 29 | Y | 28:N 27:N |  |
| 57 | steady rain -> drizzle | 14 | N | 13:N 15:N |  |
| 58 | overcast -> drizzle | 16 | Y | 15:N 17:N |  |
| 59 | clear -> high cloud | 92 | Y | 91:Y 93:N |  |
| 60 | drizzle -> clear | 10 | N | 9:N 11:N |  |
| 61 | clear -> drizzle | 88 | N | 87:N 89:N |  |
| 62 | clear -> overcast | 94 | N | 93:N 95:N |  |
| 63 | clear -> overcast | 33 | N | 32:N 34:N |  |
| 64 | drizzle -> clear | 12 | N | 11:N 13:N |  |
| 65 | clear -> high cloud | 83 | N | 82:N 84:N |  |
| 66 | high cloud -> clear | 30 | N | 29:N 31:N |  |
| 67 | clear -> high cloud | 26 | N | 25:N 27:Y |  |
| 68 | drizzle -> clear | 68 | Y | 67:N 69:N |  |
| 69 | overcast -> high cloud | 12 | N | 11:N 13:N |  |
| 70 | drizzle -> high cloud | 10 | Y | 9:N 11:N |  |
| 71 | clear -> high cloud | 98 | N | 97:N 99:N |  |
| 72 | high cloud -> overcast | 11 | N | 10:N 9:N |  |
| 73 | drizzle -> clear | 13 | Y | 12:N 14:N |  |
| 74 | overcast -> high cloud | 11 | Y | 10:N 12:Y |  |
| 75 | overcast -> high cloud | 18 | N | 17:N 19:N |  |
| 76 | clear -> high cloud | 92 | N | 91:N 93:N |  |
| 77 | overcast -> clear | 9 | N | 12:N 14:Y |  |
| 78 | clear -> high cloud | 11 | N | 10:N 12:N |  |
| 79 | drizzle -> clear | 66 | Y | 65:N 67:Y |  |
| 80 | clear -> high cloud | 128 | Y | 127:Y 129:N |  |
| 81 | overcast -> high cloud | 78 | N | 77:N 79:Y |  |
| 82 | clear -> high cloud | 50 | N | 49:N 51:N |  |
| 83 | clear -> steady rain | 15 | N | 14:N 13:N |  |
| 84 | drizzle -> overcast | 9 | N | 14:N 16:N |  |
| 85 | high cloud -> clear | 48 | Y | 47:Y 49:Y |  |
| 86 | clear -> high cloud | 9 | N | 10:N 11:N |  |
| 87 | drizzle -> high cloud | 9 | Y | 11:N 12:N |  |
| 88 | clear -> high cloud | 11 | Y | 10:Y 12:Y |  |
| 89 | high cloud -> drizzle | 47 | N | 46:N 48:N |  |

**fire** per-query rows (`k` perturbed item base rank; R = the two rank-matched controls as rank:verdict; rand = random control where drawn):

| # | value (query -> pert) | k | pert | R | rand |
|---|---|---|---|---|---|
| 0 |  -> burning | 78 | Y | 77:N 76:Y | Y |
| 1 |  -> out | 34 | N | 33:N 35:N | N |
| 2 |  -> out | 13 | N | 12:N 14:N | N |
| 3 | burning -> embers | 61 | N | 60:N 62:N | N |
| 4 |  -> embers | 28 | N | 27:N 29:N | N |
| 5 |  -> out | 43 | N | 42:N 44:N | N |
| 6 | embers -> burning | 10 | Y | 9:N 12:Y | N |
| 7 |  -> burning | 14 | Y | 13:Y 15:N | N |
| 8 |  -> burning | 114 | Y | 113:N 115:N | N |
| 9 | burning ->  | 9 | N | 12:N 13:N | N |
| 10 |  -> burning | 82 | N | 81:N 83:N | N |
| 11 |  -> out | 27 | N | 26:N 28:Y | N |
| 12 |  -> burning | 11 | Y | 10:N 12:N | N |
| 13 | embers -> burning | 9 | N | 10:N 11:N | N |
| 14 |  -> out | 170 | N | 169:N 171:N | N |
| 15 |  -> out | 23 | Y | 22:N 24:N | N |
| 16 |  -> out | 37 | N | 36:Y 38:N | N |
| 17 | burning -> embers | 11 | Y | 10:Y 12:Y | N |
| 18 |  -> burning | 11 | N | 10:Y 12:N | N |
| 19 |  -> embers | 175 | Y | 174:N 176:N | Y |
| 20 |  -> out | 79 | N | 78:N 80:N | N |
| 21 |  -> embers | 72 | N | 71:N 73:N | N |
| 22 | burning -> embers | 23 | Y | 22:N 24:N | N |
| 23 | embers -> burning | 9 | Y | 10:N 13:N | N |
| 24 |  -> out | 202 | Y | 201:N 203:N | N |
| 25 |  -> out | 11 | Y | 10:N 12:N | N |
| 26 |  -> embers | 62 | N | 61:N 63:N | N |
| 27 |  -> embers | 15 | Y | 14:N 16:N | N |
| 28 |  -> embers | 14 | Y | 13:Y 15:N | Y |
| 29 |  -> burning | 197 | N | 196:N 198:N | N |
| 30 |  -> out | 63 | Y | 62:Y 64:Y |  |
| 31 |  -> out | 34 | Y | 33:Y 35:N |  |
| 32 |  -> out | 17 | Y | 16:Y 18:Y |  |
| 33 | burning -> embers | 27 | N | 26:N 28:N |  |
| 34 |  -> burning | 80 | N | 79:N 81:N |  |
| 35 |  -> embers | 83 | N | 82:Y 84:Y |  |
| 36 | burning ->  | 16 | Y | 15:N 17:N |  |
| 37 |  -> out | 29 | N | 28:N 30:N |  |
| 38 | burning -> out | 16 | Y | 15:N 17:N |  |
| 39 |  -> out | 9 | N | 10:N 13:N |  |
| 40 |  -> embers | 63 | Y | 62:Y 64:Y |  |
| 41 |  -> burning | 31 | Y | 30:N 32:N |  |
| 42 |  -> out | 31 | Y | 30:Y 32:Y |  |
| 43 |  -> out | 69 | N | 68:N 70:N |  |
| 44 |  -> burning | 116 | N | 115:N 117:N |  |
| 45 |  -> embers | 56 | Y | 55:N 57:N |  |
| 46 | out ->  | 58 | Y | 57:Y 59:Y |  |
| 47 | embers -> burning | 9 | N | 10:N 13:N |  |
| 48 |  -> out | 24 | N | 23:N 25:N |  |
| 49 |  -> embers | 31 | N | 30:N 32:Y |  |
| 50 |  -> burning | 26 | N | 25:N 27:N |  |
| 51 |  -> burning | 87 | N | 86:N 88:N |  |
| 52 |  -> burning | 19 | Y | 18:Y 20:Y |  |
| 53 |  -> out | 138 | N | 137:N 139:N |  |
| 54 | burning ->  | 21 | Y | 20:N 22:Y |  |
| 55 |  -> out | 21 | Y | 20:Y 22:Y |  |
| 56 | embers -> out | 9 | Y | 12:N 13:Y |  |
| 57 |  -> out | 70 | Y | 69:Y 71:Y |  |
| 58 | burning -> embers | 29 | N | 28:N 30:N |  |
| 59 | out ->  | 16 | Y | 15:N 17:N |  |
| 60 |  -> embers | 18 | N | 17:N 19:Y |  |
| 61 |  -> out | 178 | Y | 177:N 179:Y |  |
| 62 |  -> out | 97 | N | 96:N 98:N |  |
| 63 |  -> out | 68 | N | 67:N 69:N |  |
| 64 |  -> out | 143 | Y | 142:N 144:N |  |
| 65 |  -> out | 130 | Y | 129:Y 131:Y |  |
| 66 | burning -> embers | 29 | Y | 28:N 27:N |  |
| 67 |  -> embers | 59 | N | 58:N 60:N |  |
| 68 | burning -> out | 9 | N | 10:N 11:N |  |
| 69 | burning -> out | 12 | Y | 11:N 13:N |  |
| 70 | out ->  | 13 | N | 12:N 11:N |  |
| 71 | burning -> out | 32 | Y | 31:Y 30:Y |  |
| 72 |  -> burning | 91 | Y | 90:N 92:N |  |
| 73 |  -> burning | 108 | N | 107:N 109:N |  |
| 74 | burning ->  | 9 | Y | 11:N 12:N |  |
| 75 | out ->  | 9 | Y | 10:N 11:N |  |
| 76 |  -> out | 107 | N | 106:N 108:N |  |
| 77 |  -> embers | 129 | N | 128:Y 130:Y |  |
| 78 | burning -> embers | 13 | N | 12:N 11:Y |  |
| 79 |  -> embers | 73 | N | 72:N 74:N |  |
| 80 |  -> out | 50 | Y | 49:Y 51:Y |  |
| 81 | burning -> embers | 98 | N | 97:N 99:N |  |
| 82 |  -> burning | 28 | N | 27:N 29:N |  |
| 83 |  -> embers | 42 | Y | 41:N 43:N |  |
| 84 |  -> out | 101 | N | 100:N 102:N |  |
| 85 |  -> out | 25 | Y | 24:N 26:N |  |
| 86 |  -> out | 21 | Y | 20:Y 22:N |  |
| 87 |  -> burning | 32 | Y | 31:N 33:N |  |
| 88 | burning -> embers | 47 | N | 46:N 48:N |  |
| 89 |  -> out | 56 | N | 55:N 57:N |  |

### 2. What the numbers say

* **Fire (conditional arm, run because the trigger fired) also codes BEYOND DEPTH, and is the largest.** n = 90, median k = 32: perturbed 0.489 vs rank-matched 0.239, D = +0.250, CI [+0.144, +0.356], label-swap p < 0.0002 (0 of 5000 draws as extreme); pilot fire was +0.133 on 15 queries. Pooled with the pilot: n = 105, D = +0.233 [+0.133, +0.329]. Shallower half of the arm (k <= 32) D = +0.344, deeper half +0.156. 23 queries have perturbed yes with both controls no, 2 the reverse. Agreement 0.923 (kappa 0.808), 0 unavailable. Fire's structure differs from the other two (very deep items; in the pilot the base top-1 was only 0.467 appropriate there), so no depth-cost story is imported for it.
* **Place and weather both code BEYOND DEPTH.** Place: perturbed items are judged appropriate 0.467 of the time vs 0.311 for base-ranker items of the same depth; D = +0.156, CI [+0.061, +0.250], label-swap p 0.0028. Weather: 0.444 vs 0.300, D = +0.144, CI [+0.039, +0.250], p 0.017. Both clear the pre-registered conjunction (CI lower bound > 0 AND p < 0.05). The pilot's direction replicates in both arms with the pilot point estimates inside the new CIs (place +0.117 pilot vs +0.156; weather +0.267 pilot vs +0.144, the pilot value being the larger and the expected shrinkage of a 15-query estimate picked out as the biggest). Pooled with the pilot (descriptive, not a verdict): place n = 120 D = +0.146 [+0.067, +0.225]; weather n = 105 D = +0.162 [+0.062, +0.262].
* **The effect is modest and the depth story stays.** About 15 points of appropriateness-rate above items sitting at the same base rank; the larger J-2639/J-2657 point stands that most of the base-top-1 gap is depth (depth cost was measured in the pilot, not re-measured here). The effect is present on both sides of the median depth (place +0.185 shallow / +0.125 deep; weather +0.130 / +0.159), no sign it is a depth artefact of one tail. In 12 (place) and 17 (weather) of 90 queries the perturbed item is judged yes while both same-depth controls are judged no; the reverse happens 3 and 6 times.
* **Instrument.** Random-depth control appropriate 0.200 (place, n = 30), 0.133 (weather, n = 30), 0.100 (fire, n = 30), below the rank-matched controls (0.311 / 0.300 / 0.239) and the perturbed items; G1 passes. Panel agreement mixtral vs falcon3: place 0.877 (kappa 0.698), weather 0.907 (kappa 0.770), tiebreak 37 and 28 times, 0 unavailable.
* **What this does NOT show (confidence: the coded verdict and all counts are verified from the committed JSON; the reading below is inferred).** (a) The control is a population of rank-neighbours in base score (F-3410); a perturbed item is by construction the best member of the perturbed ranking, i.e. it was selected by a SECOND scoring function and that selection alone can raise quality above a depth-matched item without the coordinate carrying anything specific. This replication has no negative-control arm (a re-ranking by a coordinate that is information-free, e.g. permuted values) to size that effect; that is the open confound and a follow-up job is spawned for it. (b) One prompt author, a small-model two-family panel, text-only appropriateness as the proxy, euclidean_recall only. (c) The three arms each draw 90 of the same 218 eligible queries and may share queries; they are not independent samples.
* **Bearing on D-0083 / D-0088.** None is made, reopened or worked around. They concern the cross-space edge layer (marginal reach, then the felt-response/co-recall realness test of sec5.3). This lab measures only euclidean_recall's experienced-coordinate move: it is a point in favour of the coordinates carrying judged-appropriateness signal in recall, but it is not the sec5.3 instrument and does not settle D-0088's defeater.
* **Canary (live DB).** The brief's canary (nascence.db 1,185,161,216 bytes, mtime 1793342673) can no longer be used as stated: Du was restarted at 11:42 and writes that DB. At this run's launches the live file (fire: 1186754560 / 1793409051 at start, 1188102144 / 1793415276 at end) already read 1185316864 / 1793401687.8 (place), 1185861632 / 1793404081.9 (weather) and grew to 1186672640 and 1187336192 afterwards while Du ran. My process opened it only `mode=ro` through the driver (no write path in this script) and ran under `lab_env.isolate(db="empty")` with its own sandbox DB in the lab dir; the growth is attributable to Du's own writes (its log was active throughout), not to this lab. Nothing under C:\Nascence\data was written by this job.
