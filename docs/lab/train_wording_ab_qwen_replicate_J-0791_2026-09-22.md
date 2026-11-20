# Train Lab -- Wording A/B REPLICATE + SCALE-UP on qwen3.5:9b only (2026-09-22, J-0791)

**J-0791** (spawned from F-1139/J-0777; prep F-1156), prep work for **D-0165** -- D-0165's named defeater is "Revisit once J-0791 confirms or adjusts the specific candidate ranking (A vs B vs C) at a larger sample". Script: `scripts/train_lab_wording_ab_replicate_J-0791_2026-09-08.py` (run 2026-09-22 in the Du-offline lab window); this report: `scripts/train_lab_wording_ab_replicate_J-0791_analyze.py`. Does NOT change `nodes/inner_monologue_node.py` or any live file; does NOT rule D-0165.

## What was run

- Design: 4 arms (`current` = live wording, `candidate_A/B/C` = J-0777's three rewordings, wording byte-identical) x prompts x independent draws, model `qwen3.5:9b` only (hot hub 127.0.0.1:11433), temperature 0.75, max_tokens 400 (TRAIN_MIDTRAIN_TOKENS), one request at a time, timeout 300 s, infra errors retried 3x (20/60/180 s).
- Set `orig` = the SAME 40 real (origin, last_step, ledger) triples J-0724/J-0777 used; draw 1 of `orig` is J-0777's own committed data, later draws are this run.
- Sets `fresh1..freshK` = NEW real trains (never used before), J-0724's own sampling recipe over the last 5 days of `data/monologue_log.jsonl` (>=2 real steps, evenly spaced by time, ledger = up to 3 newest `train_state_log` rows), dealt round-robin into sets of 40; one draw each per scheduled pass. These are CLOSING contexts: each prompt quotes the train's last logged step, which closed that train (the design J-0724/J-0777 used).
- Sets `mid1..midM` = OPEN contexts (an extension beyond the brief, added after the calibration check in Result 5b): the quoted step is a real interior step k of a real train, so it was open by construction as in the live node; the ledger holds up to 7 `train_state_log` entries cut to 160 chars as the live `_train_ledger` does, the model is asked for step k+1 and the REAL logged step k+1 flags are kept as a calibration reference. Prompts: `..._2026-09-22_events.json` (keys `fresh`, `mid`).
- This run's units: 878 recorded, 878 parsed OK, 0 excluded after 3 infra retries, 0 parse failures (no JSON after call_node_json's own 2 retries); 0 units needed >1 attempt; per-call latency mean 5.69 s, median 4.86 s, max 14.5 s.

## Result 1 -- every draw, call level (opened = unresolved OR intention OR '?')

| draw | source | arm | n_ok | unresolved | intention | '?' | opened (share [Wilson 95%]) | act!=none |
|---|---|---|---|---|---|---|---|---|
| orig p1 | J-0777 (F-1139) | `current` | 40 | 4 | 0 | 3 | 5/40 = 0.125 [0.05, 0.26] | 8 |
| orig p1 | J-0777 (F-1139) | `candidate_A` | 40 | 23 | 21 | 6 | 23/40 = 0.575 [0.42, 0.71] | 19 |
| orig p1 | J-0777 (F-1139) | `candidate_B` | 40 | 23 | 0 | 2 | 23/40 = 0.575 [0.42, 0.71] | 4 |
| orig p1 | J-0777 (F-1139) | `candidate_C` | 40 | 13 | 18 | 4 | 20/40 = 0.500 [0.35, 0.65] | 17 |
| orig p2 | this run | `current` | 40 | 6 | 0 | 2 | 6/40 = 0.150 [0.07, 0.29] | 11 |
| orig p2 | this run | `candidate_A` | 40 | 24 | 24 | 2 | 24/40 = 0.600 [0.45, 0.74] | 18 |
| orig p2 | this run | `candidate_B` | 40 | 26 | 0 | 4 | 26/40 = 0.650 [0.50, 0.78] | 7 |
| orig p2 | this run | `candidate_C` | 40 | 10 | 14 | 1 | 15/40 = 0.375 [0.24, 0.53] | 11 |
| orig p3 | this run | `current` | 40 | 9 | 1 | 2 | 9/40 = 0.225 [0.12, 0.38] | 8 |
| orig p3 | this run | `candidate_A` | 40 | 21 | 18 | 4 | 21/40 = 0.525 [0.37, 0.67] | 14 |
| orig p3 | this run | `candidate_B` | 40 | 23 | 0 | 2 | 23/40 = 0.575 [0.42, 0.71] | 9 |
| orig p3 | this run | `candidate_C` | 40 | 8 | 10 | 1 | 12/40 = 0.300 [0.18, 0.45] | 12 |
| fresh1 p1 | this run | `current` | 40 | 2 | 0 | 1 | 2/40 = 0.050 [0.01, 0.17] | 10 |
| fresh1 p1 | this run | `candidate_A` | 40 | 24 | 23 | 6 | 24/40 = 0.600 [0.45, 0.74] | 16 |
| fresh1 p1 | this run | `candidate_B` | 40 | 25 | 0 | 4 | 25/40 = 0.625 [0.47, 0.76] | 5 |
| fresh1 p1 | this run | `candidate_C` | 40 | 5 | 8 | 3 | 9/40 = 0.225 [0.12, 0.38] | 8 |
| fresh2 p1 | this run | `current` | 20 | 3 | 0 | 1 | 3/20 = 0.150 [0.05, 0.36] | 2 |
| fresh2 p1 | this run | `candidate_A` | 19 | 8 | 7 | 1 | 8/19 = 0.421 [0.23, 0.64] | 6 |
| fresh2 p1 | this run | `candidate_B` | 19 | 7 | 0 | 1 | 7/19 = 0.368 [0.19, 0.59] | 2 |
| fresh2 p1 | this run | `candidate_C` | 20 | 6 | 3 | 2 | 6/20 = 0.300 [0.15, 0.52] | 3 |
| mid1 p1 | this run | `current` | 40 | 12 | 0 | 2 | 12/40 = 0.300 [0.18, 0.45] | 10 |
| mid1 p1 | this run | `candidate_A` | 40 | 28 | 27 | 6 | 28/40 = 0.700 [0.55, 0.82] | 20 |
| mid1 p1 | this run | `candidate_B` | 40 | 32 | 0 | 6 | 32/40 = 0.800 [0.65, 0.90] | 6 |
| mid1 p1 | this run | `candidate_C` | 40 | 19 | 12 | 6 | 22/40 = 0.550 [0.40, 0.69] | 11 |
| mid2 p1 | this run | `current` | 40 | 14 | 1 | 8 | 17/40 = 0.425 [0.29, 0.58] | 7 |
| mid2 p1 | this run | `candidate_A` | 40 | 32 | 31 | 10 | 32/40 = 0.800 [0.65, 0.90] | 23 |
| mid2 p1 | this run | `candidate_B` | 40 | 32 | 1 | 11 | 32/40 = 0.800 [0.65, 0.90] | 4 |
| mid2 p1 | this run | `candidate_C` | 40 | 17 | 20 | 10 | 24/40 = 0.600 [0.45, 0.74] | 21 |

Opened-share matrix (rows = draws, columns = arms; n per cell in brackets):

| draw | `current` | `candidate_A` | `candidate_B` | `candidate_C` |
|---|---|---|---|---|
| orig p1 | 0.125 [40] | 0.575 [40] | 0.575 [40] | 0.500 [40] |
| orig p2 | 0.150 [40] | 0.600 [40] | 0.650 [40] | 0.375 [40] |
| orig p3 | 0.225 [40] | 0.525 [40] | 0.575 [40] | 0.300 [40] |
| fresh1 p1 | 0.050 [40] | 0.600 [40] | 0.625 [40] | 0.225 [40] |
| fresh2 p1 | 0.150 [20] | 0.421 [19] | 0.368 [19] | 0.300 [20] |
| mid1 p1 | 0.300 [40] | 0.700 [40] | 0.800 [40] | 0.550 [40] |
| mid2 p1 | 0.425 [40] | 0.800 [40] | 0.800 [40] | 0.600 [40] |

## Result 2 -- pooled rates and the candidate ranking (paired, prompt-cluster bootstrap)

Only complete quartets (all 4 arms parsed) enter this section. Prompts, not calls, are the resampled unit: 40 `orig` prompts (each with every draw incl. J-0777's) and the fresh prompts; this counts prompt-to-prompt variation, which repeated draws on the same prompt cannot remove.

**CLOSING contexts -- ORIG: the 40 J-0724/J-0777 prompts (all draws incl. J-0777's pass 1)** (prompt-equal-weighted, 40 prompts, cluster-bootstrap B=20000)

| arm | opened-share | 95% CI (prompts resampled) |
|---|---|---|
| `current` | 0.167 | [0.083, 0.258] |
| `candidate_A` | 0.567 | [0.458, 0.675] |
| `candidate_B` | 0.600 | [0.508, 0.692] |
| `candidate_C` | 0.392 | [0.283, 0.508] |

| contrast | point | 95% CI (paired, prompts resampled) | P(first > second) | CI vs 0 |
|---|---|---|---|---|
| A - B | -0.033 | [-0.142, +0.067] | 0.263 | INCLUDES 0 |
| A - C | +0.175 | [+0.058, +0.283] | 0.999 | excludes 0 |
| B - C | +0.208 | [+0.075, +0.342] | 0.999 | excludes 0 |
| A - current | +0.400 | [+0.308, +0.492] | 1.000 | excludes 0 |
| B - current | +0.433 | [+0.333, +0.525] | 1.000 | excludes 0 |
| C - current | +0.225 | [+0.108, +0.342] | 1.000 | excludes 0 |

Candidate ordering frequency across bootstrap resamples (best-to-worst; ties broken by label): BAC: 0.73, ABC: 0.27, ACB: 0.00, BCA: 0.00, CBA: 0.00, CAB: 0.00
Precision: SE(A - B) = 0.054, SE(A - C) = 0.058. A 95% half-width of +-0.05 on one of these gaps needs about N x (SE/0.025)^2 = 185 (A-B) / 212 (A-C) prompts (at the draws per prompt used here; this pool has 40); minimal detectable gap at 80% power ~ 2.8 x SE = 0.151 (A-B), 0.161 (A-C).

**CLOSING contexts -- FRESH: never-used real trains, same recipe, one draw each** (prompt-equal-weighted, 59 prompts, cluster-bootstrap B=20000)

| arm | opened-share | 95% CI (prompts resampled) |
|---|---|---|
| `current` | 0.085 | [0.017, 0.153] |
| `candidate_A` | 0.542 | [0.424, 0.661] |
| `candidate_B` | 0.542 | [0.407, 0.678] |
| `candidate_C` | 0.237 | [0.136, 0.356] |

| contrast | point | 95% CI (paired, prompts resampled) | P(first > second) | CI vs 0 |
|---|---|---|---|---|
| A - B | +0.000 | [-0.153, +0.153] | 0.499 | INCLUDES 0 |
| A - C | +0.305 | [+0.136, +0.458] | 1.000 | excludes 0 |
| B - C | +0.305 | [+0.136, +0.475] | 1.000 | excludes 0 |
| A - current | +0.458 | [+0.322, +0.593] | 1.000 | excludes 0 |
| B - current | +0.458 | [+0.305, +0.593] | 1.000 | excludes 0 |
| C - current | +0.153 | [+0.017, +0.288] | 0.990 | excludes 0 |

Candidate ordering frequency across bootstrap resamples (best-to-worst; ties broken by label): ABC: 0.55, BAC: 0.45, ACB: 0.00, BCA: 0.00
Precision: SE(A - B) = 0.075, SE(A - C) = 0.084. A 95% half-width of +-0.05 on one of these gaps needs about N x (SE/0.025)^2 = 535 (A-B) / 663 (A-C) prompts (at the draws per prompt used here; this pool has 59); minimal detectable gap at 80% power ~ 2.8 x SE = 0.211 (A-B), 0.235 (A-C).

**CLOSING contexts pooled (ORIG + FRESH, prompt-equal-weighted): the design J-0777 used, at a larger sample** (prompt-equal-weighted, 99 prompts, cluster-bootstrap B=20000)

| arm | opened-share | 95% CI (prompts resampled) |
|---|---|---|
| `current` | 0.118 | [0.067, 0.175] |
| `candidate_A` | 0.552 | [0.465, 0.640] |
| `candidate_B` | 0.566 | [0.481, 0.650] |
| `candidate_C` | 0.300 | [0.222, 0.380] |

| contrast | point | 95% CI (paired, prompts resampled) | P(first > second) | CI vs 0 |
|---|---|---|---|---|
| A - B | -0.013 | [-0.111, +0.084] | 0.394 | INCLUDES 0 |
| A - C | +0.253 | [+0.145, +0.360] | 1.000 | excludes 0 |
| B - C | +0.266 | [+0.155, +0.377] | 1.000 | excludes 0 |
| A - current | +0.434 | [+0.340, +0.529] | 1.000 | excludes 0 |
| B - current | +0.448 | [+0.354, +0.539] | 1.000 | excludes 0 |
| C - current | +0.182 | [+0.091, +0.273] | 1.000 | excludes 0 |

Candidate ordering frequency across bootstrap resamples (best-to-worst; ties broken by label): BAC: 0.60, ABC: 0.40
Precision: SE(A - B) = 0.050, SE(A - C) = 0.055. A 95% half-width of +-0.05 on one of these gaps needs about N x (SE/0.025)^2 = 396 (A-B) / 477 (A-C) prompts (at the draws per prompt used here; this pool has 99); minimal detectable gap at 80% power ~ 2.8 x SE = 0.140 (A-B), 0.154 (A-C).

**OPEN contexts -- MID: the quoted step is a real interior (open) step, as in the live node** (prompt-equal-weighted, 80 prompts, cluster-bootstrap B=20000)

| arm | opened-share | 95% CI (prompts resampled) |
|---|---|---|
| `current` | 0.362 | [0.263, 0.475] |
| `candidate_A` | 0.750 | [0.650, 0.838] |
| `candidate_B` | 0.800 | [0.713, 0.887] |
| `candidate_C` | 0.575 | [0.463, 0.688] |

| contrast | point | 95% CI (paired, prompts resampled) | P(first > second) | CI vs 0 |
|---|---|---|---|---|
| A - B | -0.050 | [-0.162, +0.062] | 0.191 | INCLUDES 0 |
| A - C | +0.175 | [+0.050, +0.300] | 0.996 | excludes 0 |
| B - C | +0.225 | [+0.087, +0.363] | 0.999 | excludes 0 |
| A - current | +0.388 | [+0.263, +0.512] | 1.000 | excludes 0 |
| B - current | +0.438 | [+0.312, +0.562] | 1.000 | excludes 0 |
| C - current | +0.212 | [+0.075, +0.338] | 0.999 | excludes 0 |

Candidate ordering frequency across bootstrap resamples (best-to-worst; ties broken by label): BAC: 0.78, ABC: 0.22, BCA: 0.00, ACB: 0.00, CAB: 0.00
Precision: SE(A - B) = 0.058, SE(A - C) = 0.065. A 95% half-width of +-0.05 on one of these gaps needs about N x (SE/0.025)^2 = 427 (A-B) / 542 (A-C) prompts (at the draws per prompt used here; this pool has 80); minimal detectable gap at 80% power ~ 2.8 x SE = 0.162 (A-B), 0.182 (A-C).

**ALL contexts (closing + open), prompt-equal-weighted -- mixes two designs, read the contrasts only** (prompt-equal-weighted, 179 prompts, cluster-bootstrap B=20000)

| arm | opened-share | 95% CI (prompts resampled) |
|---|---|---|
| `current` | 0.227 | [0.173, 0.285] |
| `candidate_A` | 0.641 | [0.575, 0.704] |
| `candidate_B` | 0.670 | [0.609, 0.730] |
| `candidate_C` | 0.423 | [0.358, 0.490] |

| contrast | point | 95% CI (paired, prompts resampled) | P(first > second) | CI vs 0 |
|---|---|---|---|---|
| A - B | -0.030 | [-0.106, +0.045] | 0.217 | INCLUDES 0 |
| A - C | +0.218 | [+0.134, +0.300] | 1.000 | excludes 0 |
| B - C | +0.248 | [+0.158, +0.335] | 1.000 | excludes 0 |
| A - current | +0.413 | [+0.339, +0.488] | 1.000 | excludes 0 |
| B - current | +0.443 | [+0.367, +0.518] | 1.000 | excludes 0 |
| C - current | +0.196 | [+0.117, +0.274] | 1.000 | excludes 0 |

Candidate ordering frequency across bootstrap resamples (best-to-worst; ties broken by label): BAC: 0.78, ABC: 0.22
Precision: SE(A - B) = 0.038, SE(A - C) = 0.043. A 95% half-width of +-0.05 on one of these gaps needs about N x (SE/0.025)^2 = 420 (A-B) / 519 (A-C) prompts (at the draws per prompt used here; this pool has 179); minimal detectable gap at 80% power ~ 2.8 x SE = 0.107 (A-B), 0.119 (A-C).

**CLOSING contexts pooled, THIS RUN ONLY (J-0777's draw EXCLUDED): does the result replicate on data collected after it?** (prompt-equal-weighted, 99 prompts, cluster-bootstrap B=20000)

| arm | opened-share | 95% CI (prompts resampled) |
|---|---|---|
| `current` | 0.126 | [0.071, 0.187] |
| `candidate_A` | 0.551 | [0.460, 0.641] |
| `candidate_B` | 0.571 | [0.485, 0.657] |
| `candidate_C` | 0.278 | [0.197, 0.359] |

| contrast | point | 95% CI (paired, prompts resampled) | P(first > second) | CI vs 0 |
|---|---|---|---|---|
| A - B | -0.020 | [-0.121, +0.081] | 0.349 | INCLUDES 0 |
| A - C | +0.273 | [+0.162, +0.384] | 1.000 | excludes 0 |
| B - C | +0.293 | [+0.182, +0.404] | 1.000 | excludes 0 |
| A - current | +0.424 | [+0.328, +0.520] | 1.000 | excludes 0 |
| B - current | +0.444 | [+0.348, +0.540] | 1.000 | excludes 0 |
| C - current | +0.152 | [+0.061, +0.247] | 0.999 | excludes 0 |

Candidate ordering frequency across bootstrap resamples (best-to-worst; ties broken by label): BAC: 0.63, ABC: 0.37
Precision: SE(A - B) = 0.052, SE(A - C) = 0.057. A 95% half-width of +-0.05 on one of these gaps needs about N x (SE/0.025)^2 = 436 (A-B) / 515 (A-C) prompts (at the draws per prompt used here; this pool has 99); minimal detectable gap at 80% power ~ 2.8 x SE = 0.147 (A-B), 0.160 (A-C).

### Replicate-only: this run's draws on the 40 `orig` prompts, WITHOUT J-0777's draw

| arm | n_ok | opened | unresolved | intention |
|---|---|---|---|---|
| `current` | 80 | 15/80 = 0.188 [0.12, 0.29] | 15/80 = 0.188 [0.12, 0.29] | 1/80 = 0.013 [0.00, 0.07] |
| `candidate_A` | 80 | 45/80 = 0.562 [0.45, 0.67] | 45/80 = 0.562 [0.45, 0.67] | 42/80 = 0.525 [0.42, 0.63] |
| `candidate_B` | 80 | 49/80 = 0.613 [0.50, 0.71] | 49/80 = 0.613 [0.50, 0.71] | 0/80 = 0.000 [-0.00, 0.05] |
| `candidate_C` | 80 | 27/80 = 0.338 [0.24, 0.45] | 18/80 = 0.225 [0.15, 0.33] | 24/80 = 0.300 [0.21, 0.41] |

## Result 3 -- the `current`-arm swing (0.125 in J-0777 vs 0.25 in J-0724): sampling variance or not?

| reading of the IDENTICAL wording + model + 40 prompts | opened |
|---|---|
| J-0724 (09-08 earlier run) | 10/40 = 0.250 [0.14, 0.40] |
| J-0777 (F-1139) | 5/40 = 0.125 [0.05, 0.26] |
| this run orig p2 | 6/40 = 0.150 [0.07, 0.29] |
| this run orig p3 | 9/40 = 0.225 [0.12, 0.38] |

- Homogeneity of the 4 readings: chi2=2.79, dof=3, p=0.425 (small p = the readings differ more than binomial noise allows).
- Observed SD of the readings = 0.060 vs the SD a pure-binomial n=40 draw at the pooled rate 0.188 would show = 0.062.
- J-0724 (10/40) vs J-0777 (5/40) alone: Fisher exact p=0.252 -- the 0.25-vs-0.125 gap that motivated this job.

## Result 4 -- how much of the outcome is the prompt and how much is the draw (orig set)

| arm | prompts | draws/prompt | mean opened | share of prompts with the same outcome in EVERY draw | agreement draw1 vs draw2 | Cohen kappa (draw1,draw2) | ICC(1) |
|---|---|---|---|---|---|---|---|
| `current` | 40 | 3 | 0.167 | 0.72 | 0.82 | 0.26 | 0.35 |
| `candidate_A` | 40 | 3 | 0.567 | 0.42 | 0.57 | 0.12 | 0.23 |
| `candidate_B` | 40 | 3 | 0.600 | 0.30 | 0.47 | -0.10 | 0.04 |
| `candidate_C` | 40 | 3 | 0.392 | 0.55 | 0.72 | 0.45 | 0.38 |

ICC near 1 = the prompt decides the outcome (extra draws on the same prompts add little); near 0 = the draw decides (extra draws are as good as new prompts).

- Draw independence check: identical `thought` text between J-0777's draw and this run's first orig draw for the same (arm, prompt): 0/160 (must be ~0 -- no seed is passed, so each call is a fresh draw).

## Result 5 -- by prompt set (does the 40-prompt `orig` sample look typical? do open contexts differ?)

| set (this run's draws pooled) | `current` | `candidate_A` | `candidate_B` | `candidate_C` |
|---|---|---|---|---|
| orig (J-0777 draw only) | 0.125 [40] | 0.575 [40] | 0.575 [40] | 0.500 [40] |
| orig | 0.188 [80] | 0.562 [80] | 0.613 [80] | 0.338 [80] |
| fresh1 | 0.050 [40] | 0.600 [40] | 0.625 [40] | 0.225 [40] |
| fresh2 | 0.150 [20] | 0.421 [19] | 0.368 [19] | 0.300 [20] |
| mid1 | 0.300 [40] | 0.700 [40] | 0.800 [40] | 0.550 [40] |
| mid2 | 0.425 [40] | 0.800 [40] | 0.800 [40] | 0.600 [40] |

## Result 5b -- calibration: does the lab's `current` arm look like the live node?

Real logged mid-train steps (`data/monologue_log.jsonl`, rows with a train_id, step position >= 2 = the steps the mid-train prompt generates; the wording has been the CURRENT block throughout): 08-21..09-04: opened 0.536 (unresolved 0.528, intention 0.022, '?' 0.016, n=4077); 09-05..09-08: opened 0.533 (unresolved 0.526, intention 0.022, '?' 0.013, n=2540); 09-09..09-16: opened 0.529 (unresolved 0.521, intention 0.021, '?' 0.014, n=3144); 09-17..09-22: opened 0.562 (unresolved 0.554, intention 0.020, '?' 0.017, n=1539).

Real train lengths by era (`data/train_length_log.jsonl`, one row per closed train): 08-03..08-16 (gemma, before TRAIN_HOLD): n=1404, mean length 3.78 (implied per-step continuation 0.736), thread-end = 0.922 of closes; 08-17..08-20 (gemma, TRAIN_HOLD): n=498, mean length 2.61 (implied per-step continuation 0.616), thread-end = 0.956 of closes; 08-21..09-04 (qwen): n=2242, mean length 2.06 (implied per-step continuation 0.515), thread-end = 0.960 of closes; 09-05..09-22 (qwen): n=3324, mean length 2.16 (implied per-step continuation 0.538), thread-end = 0.956 of closes. The replay lab's `fork-rate-if-ungated` (docs/lab/train_split_merge_step2_replay_2026-09-06.md, kill criterion #1) is exactly this thread-end share of closes: it has been 0.92-0.96 in every era, i.e. it does not track the per-step opened rate (0.735 -> 0.52 implied) that the wording controls.

On the 80 OPEN-context prompts with all four arms parsed, against the REAL next step that the live node logged from the same context:

| source | opened-share | lab minus real [95% CI, prompts resampled] | per-prompt corr. with real next |
|---|---|---|---|
| real logged next step (live node, full seed marketplace) | 0.550 | - | - |
| lab `current` (reduced prompt: mid-thread block only) | 0.362 | -0.188 [-0.338, -0.037] | 0.00 |
| lab `candidate_A` (reduced prompt: mid-thread block only) | 0.750 | +0.200 [+0.062, +0.337] | 0.12 |
| lab `candidate_B` (reduced prompt: mid-thread block only) | 0.800 | +0.250 [+0.100, +0.388] | -0.08 |
| lab `candidate_C` (reduced prompt: mid-thread block only) | 0.575 | +0.025 [-0.138, +0.188] | -0.12 |

Illustration (INFERRED, not measured; see the assumption in the script): map each arm onto the live node by the constant log-odds shift that takes the lab `current` arm to the real logged next-step rate, then read the implied live continuation probability p and the geometric mean train length 1/(1-p). For scale, the live mean train length (`data/train_length_log.jsonl`) was 3.78 before TRAIN_HOLD (p = 0.735), 2.61 for TRAIN_HOLD on gemma (0.617) and 2.06-2.28 on qwen (0.515-0.561).

| arm | lab opened (open contexts) | implied live p | 95% CI | implied mean train length | 95% CI |
|---|---|---|---|---|---|
| `current` | 0.362 | 0.550 | [0.438, 0.662] | 2.22 | [1.78, 2.96] |
| `candidate_A` | 0.750 | 0.866 | [0.755, 0.937] | 7.45 | [4.09, 15.78] |
| `candidate_B` | 0.800 | 0.896 | [0.808, 0.951] | 9.60 | [5.21, 20.54] |
| `candidate_C` | 0.575 | 0.744 | [0.600, 0.855] | 3.91 | [2.50, 6.90] |

- CLOSING-context prompts quote each train's LAST logged step: for the 40 `orig` prompts that step was itself open by the live gate in 0/40 cases (J-0724's own jsonl); for the 59 `fresh` prompts in this run: 0/59 (a train can also end by repetition / ceiling / stall, so a last step can still be open).

Reading guide: a live mid-train prompt quotes a step that was open by construction (a train continues only if the previous step was open, nodes/inner_monologue_node.py:4484), so OPEN contexts are the live-like ones; CLOSING contexts ask a different question (would the model re-open after a calm closer?). The live prompt also carries seed parts the lab omits (frontier questions, retraction ledger, symbol read-back, a recall snippet), so a remaining gap to the real next step is expected.

## Result 6 -- how each arm opens, the intention FORMAT, and side effects (every valid call, all draws pooled)

| arm | n | unresolved | intention set | opened via: unresolved-only / intention-only / both / '?'-only | act != none | mean words | thought lacks terminal punctuation (possible truncation) |
|---|---|---|---|---|---|---|---|
| `current` | 260 | 50/260 = 0.192 [0.15, 0.24] | 2/260 = 0.008 [0.00, 0.03] | 49 / 1 / 1 / 3 | 56/260 = 0.215 [0.17, 0.27] | 45.7 | 1/260 |
| `candidate_A` | 259 | 160/259 = 0.618 [0.56, 0.67] | 151/259 = 0.583 [0.52, 0.64] | 9 / 0 / 151 / 0 | 116/259 = 0.448 [0.39, 0.51] | 47.5 | 0/259 |
| `candidate_B` | 259 | 168/259 = 0.649 [0.59, 0.70] | 1/259 = 0.004 [0.00, 0.02] | 167 / 0 / 1 / 0 | 37/259 = 0.143 [0.11, 0.19] | 45.9 | 3/259 |
| `candidate_C` | 260 | 78/260 = 0.300 [0.25, 0.36] | 85/260 = 0.327 [0.27, 0.39] | 22 / 29 / 56 / 1 | 83/260 = 0.319 [0.27, 0.38] | 46.1 | 0/260 |

Intention FORMAT (non-empty `intention` strings; first_person = starts with I / I'd / Let me / My / We, fragment = bare infinitive or bare imperative such as 'to reach the study' / 'sit by the fire for a moment'):

| arm | n intentions | first-person share [Wilson 95%] | to-infinitive fragments | bare-imperative fragments |
|---|---|---|---|---|
| `current` | 2 | 2/2 = 1.000 [0.34, 1.00] | 0 | 0 |
| `candidate_A` | 151 | 151/151 = 1.000 [0.98, 1.00] | 0 | 0 |
| `candidate_B` | 1 | 1/1 = 1.000 [0.21, 1.00] | 0 | 0 |
| `candidate_C` | 85 | 48/85 = 0.565 [0.46, 0.67] | 7 | 30 |

- fragment examples, `candidate_C`: 'tend the fire'; 'to name what I truly want before acting'; 'walk onto the sand'; 'test the leverage point'; 'to let the boat carry me to the sea'

Act-kind shares (the schema's `act.kind`, every valid call; `none` = no deed set -- a side effect of the wording, not what the gate measures):

| arm | n | none | observe | move | read | write | search | recall | letter | world | other |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `current` | 260 | 0.785 | 0.065 | 0.108 | 0.027 | 0.004 | 0.004 | 0.000 | 0.000 | 0.008 | 0.000 |
| `candidate_A` | 259 | 0.552 | 0.212 | 0.178 | 0.027 | 0.008 | 0.008 | 0.000 | 0.000 | 0.015 | 0.000 |
| `candidate_B` | 259 | 0.857 | 0.031 | 0.085 | 0.004 | 0.012 | 0.000 | 0.000 | 0.000 | 0.012 | 0.000 |
| `candidate_C` | 260 | 0.681 | 0.108 | 0.146 | 0.042 | 0.008 | 0.000 | 0.004 | 0.000 | 0.012 | 0.000 |

## Isolation and gate record

- run summary (`J-0791_run_summary.json`, written by the batch process at exit): stop_reason = 'deadline 10:50 reached'; units done 878/1760; wall 4402.1 s; counters {'attempts': 773, 'infra_attempts_failed': 0, 'units_run': 773, 'units_excluded': 0, 'units_content_fail': 0}
- write attempts under live data (audit hook, C:\Nascence\data or \docs): **0**; elsewhere under C:\Nascence: 0; worktree data\ writes: 0; sqlite connects: 0; core.*/nodes.* modules outside the worktree: 0
- live-file fingerprint (md5 of position/room_state/life_state, size+mtime of judge_panel_log / llm_latency / llm_calls / thought_station_log / nascence.log / nascence.db, 5 canary row counts) identical before/after: **True**
- hub: {'digest': '6488c96fa5faab64', 'modified_at': '2026-06-10T11:48:35.9666496+12:00', 'resident': [['qwen3.5:9b', 8192]]}; arm system-prompt sha256[:12]: {'current': 'b3e0ed7aa723', 'candidate_A': '273e90665ea8', 'candidate_B': 'd770433a7575', 'candidate_C': 'b0a7c445f64f'}

## Gate, isolation and run notes added by hand (the script prints the rest above)

- Du-down gate (`lab_du_down_check.py`, exit 0 = DOWN; last lifecycle line in nascence.log = "Nascence shutting down" 2026-09-22 08:43:39, no run_nascence.py / core\main.py process): DOWN at 09:09 (start), 09:24, 10:05, 10:30, 10:37 and 10:50 (end); the batch process itself re-ran the gate (that script AND the WMI process count) before starting and every 20 calls -- it never fired. Du was never started, the supervisor/hubs/HUD were never touched, no life flag was flipped.
- The batch ran as two processes on the same resumable results file: the first (09:25-09:36, 105 units) was stopped by the operator so the open-context sets could be added; its own end-of-run audit line was therefore never printed. Its isolation is covered by (a) the dry-run and probe audit lines (0 attempts), (b) the hook self-test (`J-0791_hook_selftest.py`: PASS, it detects write-opens, rename/replace, mkdir, remove, copyfile, rmtree and os.open(O_CREAT) under a watched path and ignores reads), and (c) the live-file fingerprint taken at 09:36, 10:30 and 10:50 by a separate script, identical to the fingerprint the first process printed at its start (09:25). The second process (09:36-10:50, 773 units) printed `write attempts under live data: 0 (elsewhere under C:\Nascence: 0; under worktree data\: 0; sqlite3.connect calls: 0)` and an identical before/after fingerprint.
- Infrastructure errors: 0 failed attempts in 878 attempts (0 timeouts, 0 HTTP errors; hub :11433 only, latency mean 5.7 s, median 4.9 s, max 14.5 s; no unit needed a retry), 0 excluded units, 0 parse failures. No other hub was used.
- Module resolution (F-1285): every batch process printed 21 `core.*` / `nodes.*` modules loaded, 21 inside the worktree, 0 outside; `core.model_client`, `core.telemetry`, `core.sitting`, `core.emissary_tension`, `core.social_moves`, `core.memory_edges`, `core.opponent_process`, `core.intentions`, `core.training_log` and `nodes.inner_monologue_node` were each printed with their `__file__` (all under the worktree). Base system prompt 3238 chars, `CURRENT_BLOCK` found exactly once, `dwell_steer()` and `keystone_steer()` both "" -- identical to J-0777's 3238 and to the 3238/3115/3284/3181 char arms F-1156 reported.
- The schedule `orig:2,fresh1:1,mid1:1,mid2:1,orig:3,fresh2:1,...` was an upper bound (1760 units); the run stopped at its own `--deadline 10:50` with 878 units done: orig passes 2 and 3, fresh1, mid1 and mid2 complete, fresh2 20 of 40 prompts. Incomplete quartets are excluded from every paired number and counted in the call-level tables.

## Reading (Claude, 2026-09-22; interpretation is INFERRED from the tables above unless a line says measured)

**1. The candidate ranking.**
- All three rewordings lift opened-share far above the live wording in every design (closing contexts, 99 prompts: A +0.43, B +0.45, C +0.18 over `current` 0.12; open contexts, 80 prompts: +0.39 / +0.44 / +0.21 over 0.36). This part of F-1139 replicates cleanly.
- **A vs B is a statistical tie and stays one**: A - B = -0.013 [-0.111, +0.084] (closing, 99 prompts), -0.020 [-0.121, +0.081] on this run's data alone (J-0777's draw excluded), -0.050 [-0.162, +0.062] (open, 80 prompts). B's point estimate is ahead in every pool, by 0.01-0.05, and never distinguishable from 0. J-0777's exact 0.575/0.575 tie was the luck of one draw, but the tie itself survives: these data give no A-vs-B ranking on opened-share. Resolving a +-0.05 gap would take about 400 prompts per arm (SE(A - B) = 0.050 at 99 prompts; roughly 4x the closing sample here, about 2.5 hours of hub time) -- not a good use of a Du-offline window; A and B should be told apart on the other properties in section 4, not on this number.
- **C is lower, by more than J-0777's single draw suggested**: A - C = +0.253 [+0.145, +0.360] and B - C = +0.266 [+0.155, +0.377] (closing pooled); +0.175 [+0.050, +0.300] and +0.225 [+0.087, +0.363] (open). J-0777's C reading (0.50) was the top of C's range on those prompts (0.500, 0.375, 0.300 over three draws of the same 40; 0.225 on the fresh1 prompts). C keeps the strict "unresolved" paragraph, so it opens mostly through `intention` (unresolved 0.30, intention 0.33 versus A 0.62 / 0.58 and B 0.65 / 0.00).
- **C's intention text stays format-inconsistent (replicated)**: 48/85 = 56.5% first-person, 37/85 bare infinitives/imperatives ("tend the fire", "to reach the study"); A's 151/151 are first-person. The cost is not measured here: stored intentions are kept verbatim (nodes/inner_monologue_node.py:5390-5400) and shown as bullets (nodes/reflection_node.py:126-128), so a fragment reads oddly against the schema's own "write it in the first person" instruction but is not a parse failure.

**2. The sampling variance the brief asked about (measured).** The `current` arm on the 40 orig prompts now has four readings of the identical wording, model and prompts: 0.25 (J-0724), 0.125 (J-0777), 0.15 and 0.225 (this run). Homogeneity chi2 p = 0.43; the observed SD of the readings (0.060) matches the 0.062 a pure-binomial n=40 draw at the pooled 0.19 would show; the original 0.25-vs-0.125 pair alone is Fisher p = 0.25. The swing was ordinary n=40 sampling noise (one 40-call arm carries a 95% half-width of about +-0.15), not a wording or isolation difference. Draws are independent (0 of 160 identical thoughts between J-0777's draw and this run's first orig draw). On the orig prompts ICC(1) is 0.35 (`current`), 0.23 (A), 0.04 (B), 0.38 (C): A's and especially B's outcomes are mostly draw noise, so extra draws on the same prompts are worth about as much as new prompts for them; `current` and C are more prompt-driven.

**3. What the lab's contexts can and cannot say (new, beyond the brief; the facts are measured, the mechanism is inferred).**
- Every `orig` and `fresh` prompt quotes a train's LAST logged step, which closed that train (0/40 and 0/59 open by the live gate). A live mid-train prompt quotes a step that was open by construction (a train continues only if the previous step was open, nodes/inner_monologue_node.py:4484).
- The live node's per-step opened share on real mid-train steps is 0.53-0.56 (n = 11,300, 08-21..09-22, every period alike) and its mean train length fell 3.78 (08-03..08-16, gemma) -> 2.61 (08-17..08-20, TRAIN_HOLD on gemma) -> 2.06-2.16 (qwen), i.e. an implied per-step continuation of 0.736 -> 0.616 -> 0.515-0.538. The lab's `current` arm reads 0.05-0.23 per draw on closing contexts (0.12 pooled): about 4.7x below the live node's 0.55. On 80 OPEN-context replays `current` reads 0.36 against 0.55 for the real next step logged from the same contexts (lab minus real -0.19 [-0.34, -0.04], per-prompt correlation 0.00): open contexts recover about 56% of the gap; the rest is what the reduced prompt leaves out (frontier questions, retraction ledger, symbol read-back, a recall snippet) and/or noise. So the lab's absolute levels are not live levels and its per-context outcomes do not track the live node's.
- The candidate ordering is the same in open contexts (B 0.80 >= A 0.75 > C 0.575 > `current` 0.36), so the ranking result is robust to the design; the size of the effects is what does not transfer one-to-one.
- INFERRED illustration (assumes the lab-to-live distortion is one constant log-odds shift for every wording, which nothing here tests, and ignores the node's own train caps): implied live per-step continuation A 0.87 (mean train about 7.5), B 0.90 (about 9.6), C 0.74 (about 3.9), against 0.55 (about 2.2) now and 0.735 (3.78) before TRAIN_HOLD. On that assumption A and B would overshoot the pre-TRAIN_HOLD length and C would land near it -- D-0165's second defeater condition ("over-correcting the fork rate in the other direction") in numbers. It is an argument for a live-like trial before choosing, not a recommendation.
- Two more context facts for the founder's read (measured): TRAIN_HOLD's own step (3.78 -> 2.61 while gemma still served the hot lane) is about 70% of the whole fall to ~2.1, the qwen swap the rest; and the replay lab's `fork-rate-if-ungated` (the thread-end share of closes: 0.922, 0.956, 0.960, 0.956 across those four eras) barely moved, so it is not evidence about the per-step wording in either direction.

**4. Other things the candidates change (measured).**
- Deeds: `act` != none is 0.215 for `current`, 0.448 for A (observe 0.21, move 0.18), 0.143 for B, 0.319 for C -- A doubles the deed rate, B lowers it.
- Channel: A opens through intention AND unresolved together (151 of 160 unresolved calls also carry an intention); B is unresolved only and leaves intention at 0.004; C splits the two.
- Mean thought length is 46-47 words in every arm; 0-3 of ~260 calls per arm end without terminal punctuation (possible truncation), B the most (3).
- What a flip looks like (fresh1 prompt t_cba1be, raw): `current` -> "...This is not drowning; it is floating in a current too large for arithmetic to contain." (closed); B -> "...The arithmetic waits; the ocean does not care for equations, and neither should I right now." (unresolved=true, the wording's "naming what you haven't yet done" clause); A -> "...This isn't drowning; it's swimming against a different tide." (unresolved=true).

**5. What this does and does not settle for D-0165.** D-0165's named defeater ("Revisit once J-0791 confirms or adjusts the specific candidate ranking (A vs B vs C) at a larger sample") is met: the ranking is confirmed for "all three >> current" and "C below A and B", adjusted for "A = B" (a tie, not a ranking). Which wording to apply, and whether any of these three lands the live continuation where the founder wants it, is not answerable from this lab: the effect sizes do not transfer, and no candidate has been run on the live node's full prompt. Not done here: the gemma-vs-qwen model swing re-run on open contexts (it needs the hot hub's resident model swapped, so it cannot share the hub with other labs; a follow-up job was spawned), and any replay that includes the omitted seed parts.
