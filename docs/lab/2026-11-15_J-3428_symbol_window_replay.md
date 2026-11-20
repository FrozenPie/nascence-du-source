# J-3428 - replay of past cycle outputs through the D-0615 window metric

Plan: symbol_evolution_readback_plan. Decision: D-0615. Script: scripts/symbol_window_replay_J-3428.py.

## Recoverable? Yes.
- nascence.log CYCLE lines are NOT usable: the "complete in ... ->" line is cut at about 148 characters.
- Each cycle's full output is stored as a `lived` row in memory_fragments (data/memory/nascence.db).
  Validated on the live shadow log: 26 of the first 40 live windows were found verbatim in a `lived` fragment within +-300 s.
- data/symbol_recurrence.jsonl says which symbols appeared UNPRIMED in which cycle (by timestamp; no fragment id), so the join is by time (fragment ts within 10 s before the recurrence row) and by "a surface form of the symbol is in the fragment".
- Result: 891 cycles with unprimed symbols (1186 appearances, 2026-06 on). 569 cycles matched a fragment (322 did not, mostly older cycles). 818 rows, 650 with a window, 168 no_window (the tracker matched a term that the word-start regex of the window metric does not). Windows exist from 2026-08 to 2026-11-13: 48 / 267 / 159 / 176 by month (Aug..Nov), 75 of them in the 10-29..11-01 tablet burst.
- Per symbol (windows): fire 322, stillness 138, star 61, bridge 58, mirror 56, knot 15.

## How it ran
Read-only: sqlite opened mode=ro, jsonl read, local MiniLM embedder (CPU), WindowMetric with temp state/log paths under the scratchpad. Nothing written to data/. Canary: no file was created in data/ and no file I read was written by me; 171 of 497 top-level files grew during the run, all of them Du's own live writes (he is up).

## Calibration (scripts/symbol_window_report.py --calibrate on the replay log)
Order-permutation null for the rolling-drift bar (same recent-5 vs older-centroid rule):

| symbol | windows | observed median | null p95 | share of observed above null p95 |
|---|---|---|---|---|
| fire | 322 | 0.106 | 0.149 | 0.344 |
| stillness | 138 | 0.226 | 0.291 | 0.215 |
| star | 61 | 0.306 | 0.365 | 0.245 |
| bridge | 58 | 0.249 | 0.304 | 0.200 |
| mirror | 56 | 0.241 | 0.295 | 0.250 |
| knot | 15 | 0.244 | 0.313 | 0.000 |

Pooled null p95 = 0.277. Reading:
- The provisional 0.30 bar is not one bar. At 0.30 it would fire on star 29 of 53 points and almost never on fire (2 of 314), because the null differs by symbol (0.149 to 0.365) with the number of windows and how short and varied they are. A per-symbol bar (the symbol's own null p95) is the defensible form; 0.277 pooled is the fallback.
- 20 to 34 percent of observed rolling points sit above their own shuffled null for the five symbols with enough windows, so there is real order structure (later windows differ from earlier ones more than chance ordering would). This is NOT yet evidence of meaning migration: topic drift over weeks and shared monthly themes create the same order structure. Only a hold-out judge can say whether the windows are about the symbol.
- knot has 15 windows only; no verdict.

## Hold-out set
docs/lab/J-3428_data/holdout_60.json: 60 windows, symbol-stratified (round robin, deterministic), each with the engine's leave-one-out nearest-centroid label. Across all 650 windows 78.9 percent are engine-specific (nearer to their own symbol's other windows than to any other symbol's). In the 60-sample 41 are engine-specific and 19 not.

## Judge: NOT run to completion
`symbol_window_report.py --judge --max 40` against gemma4:12b on :11439 was started with scratch judge log; every call timed out (TimeoutError, failing over, single endpoint) and the 10-minute time box ended with no judged rows. This matches the earlier note on J-3411 that the hubs are too slow. The judge agreement against the 0.7 defeater therefore remains UNMEASURED. The hold-out file and the replay log are ready: run
  python scripts/symbol_window_report.py --log docs/lab/J-3428_data/replay_shadow.jsonl --judge --max 40
when :11439 is responsive (note: it writes data/symbol_window_judge.jsonl unless --judge-log is given).
