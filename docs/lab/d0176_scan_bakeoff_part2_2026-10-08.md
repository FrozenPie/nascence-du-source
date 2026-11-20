# D-0176 scan_shadow bake-off, part 2: falcon3:7b, mixtral:8x7b, command-r7b (J-1851, 2026-10-08)

Same harness (scripts/d0176_scan_bakeoff.py), same case files (j0842_cases.json, j0842_cases_ext.json), same labels, production
payload (temperature 0.3, 400 tokens, json) as the 2026-09-22 run (d0176_scan_bakeoff_2026-09-22.md). Du was DOWN for the whole
window (21:14 to 22:45 local, 2026-10-08); the runner wrote 0 files under live data/docs (write_attempts_under_live_data=0 in all six
runner logs); infrastructure errors: 0 in every run. All three hubs answered a scan-shaped probe before the run
(falcon 26 s, mixtral 32 s, r7b 6.6 s). Scored with `score --models hot,granite,gemma,falcon,mixtral,r7b --common`
(215 units each on the common set; the three earlier models' rows are the 09-22 results re-scored on that set).

Results: data/J-1851_results_falcon_mixtral_r7b.jsonl (raw rows) and data/J-1851_scores_common_6models.json (every table).

| | qwen3.5:9b (seat) | gemma4:12b | falcon3:7b | mixtral:8x7b | command-r7b |
|---|---|---|---|---|---|
| controls correct (12 stand + 12 non-stand, x2) | 24/24 | 24/24 | 19/24 (7/12 non-stand runs right) | 22/24 | 21/24 |
| identical-input gate flips (of 40, 3 runs) | 16 | 0 | 5 | 11 | 9 |
| templated strings formed (3 strings x 5 runs) | 2/15 | 0/15 | 15/15 | 11/15 | 12/15 |
| load_bearing flag missing | 0 | 0 | 0 | 0 | 0 |
| null (no stand) rate | 38% | 57% | 0% | 20% | 63% |
| non-stand thoughts formed (blind read, n=68) | 51% | 40% | 96% | 72% | 24% |
| chore-like thoughts formed (n=28) | 46% | 46% | 96% | 71% | 29% |
| F-0677 narrow bucket rejected (n=24) | 21% | 62% | 4% | 25% | 83% |
| formed on ledger-formed cases (recall, n=60) | 68% | 43% | 93% | 72% | 27% |
| rejected on ledger-observed cases (n=36) | 64% | 83% | 3% | 33% | 78% |
| median / p90 latency, s | 7 / 10 | 21 / 48 | 12 / 18 | 18 / 33 | 19 / 54 |

Notes. (1) falcon3:7b almost never says no: it forms a commitment on 95% of the 96 main cases, never returns null, and forms on 96% of
thoughts the blind read calls non-stands. It is unfit as a classifier of this task even though it is fast and its identical-input
flips are low (a model that always forms is stable). (2) mixtral:8x7b is lenient (72% over-formation), flips on 11/40 identical
inputs and splits tpl_c 1 formed / 4 rejected. (3) command-r7b is the strictest model (24% over-formation, 83% of the narrow
physical bucket rejected) but that comes with 27% recall on ledger-formed cases and 63% null, it forms the templated strings 12/15
times (F-0770's failure mode) and flips 9/40. Its latency in the first pass (main set) was 60 to 77 s per call while the other two Ramses
and local hubs ran concurrently; it fell to 13 to 30 s later, so the latency figure is not a clean one. (4) None of the three beats
gemma4:12b on controls, identical-input consistency and non-stand over-formation together: gemma ties or wins controls and flips
(0/40), and only command-r7b has a lower over-formation number, bought with near-total under-formation.

Temperature-0 lever (score-t0) was not run for these three models (time allowed, but the question D-0176 asks is answered at the
production temperature; a successor job covers it if wanted).
