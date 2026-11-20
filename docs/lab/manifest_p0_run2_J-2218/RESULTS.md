# J-2218 manifest-loop P0 Run 2 -- results (run 2026-10-18, Du down since 08:37:20)

Pre-registration: PREREGISTRATION.md (written 2026-10-16, before any model call). Harness:
scripts/manifest_p0_run2_lab.py (restored from unreachable commit 8f01e1ef; `--seat hot|dreamer` added 2026-10-18).
Fuel: the 43 `[CYCLE n] human:` turns dated <= 2026-07-03 (re-counted on a full copy of data/nascence.log, 710,013
lines: 51 human turns in total, 43 in range). Fidelity: 26 recovered from memory_fragments (read-only), 9 complete in
the log, 8 still truncated. Live DB sha256 5ff998c9... identical before and after the main run, and again afterwards.

## Seat 1 (main): MichelRosselli/bonsai-27b Q1_0 on the hot Ollama :11433 -- the plan's own Bonsai-Q1 seat

At ~10:33 the resident qwen3.5:9b expired and the "maximum pending requests exceeded" wedge (F-3060) was gone. Cold
load took 127 s (default 262k ctx = 23.7 GB, 8.9 GB VRAM); with the harness's num_ctx 4096 it sits at 4.43 GB, all
on the GPU, and takes about 8 s per decompose. JSON-schema grammar, temperature 0.2, repeat 1.18, presence 0.6,
frequency 0.3. Files: run2_bonsai27b.jsonl (129 rows), run2_bonsai27b.summary.json.

| metric | A1 full, seed 11 | A2 full, seed 23 | B truncated, seed 11 |
|---|---|---|---|
| valid JSON / schema ok | 43 / 43 | 43 / 43 | 43 / 43 |
| decomposed (>=2 items) | 41 | 43 | 43 |
| both lanes | 28 | 27 | 32 |
| degenerate (pre-registered metric) | 0 | 0 | 0 |
| ingredient count 1 / 2 / 3 | 2 / 40 / 1 | 0 / 41 / 2 | 0 / 41 / 2 |
| identity items deferred | 26 / 26 | 27 / 27 | 28 / 28 |
| rule violations (fact/epistemic deferred) | 17 | 22 | 13 |
| inline ingredients | 16 of 85 | -- | -- |
| regime closed / identity / open / relational | 0 / 1 / 20 / 22 | 0 / 2 / 16 / 25 | 1 / 1 / 23 / 18 |

A1 vs A2 lane-set agreement: 26/43 (24/43 for count plus lane set).

Pre-registered bars: P1 valid >= 42 PASS (43). P2 degeneration <= 3 PASS (0). P3 decomposition >= 30 PASS (41),
both lanes >= 15 PASS (28). P4 A1/A2 agreement >= 30 FAIL (26). P5 B degenerates at least as often as A1: passes
only trivially (0 = 0). On every other axis B did as well as or better than A1, so fix 1 (full text) shows no
measurable benefit. Kill reading not triggered (valid 43 >= 39, degeneration 0 <= 8).

Outside the pre-registration (seen on reading the rows): the decode fix took away Run 1's duplicate collapse, but
the output fell into a new template. It gives 2 ingredients on 40 of 43 turns and marks most of them "deferred"
(69 of 85 in A1, including 12 fact items). So "identity always deferred" holds only because almost everything is
deferred: the vehicle tag does not discriminate. The regime classifier never says closed on full text. #33, the
"pure math" circle-into-eight turn, is tagged open, and its fact item is deferred. Run 1's #1 mis-attribution is
still there: "Jung, do you believe you are conscious?" becomes "Clarify Jung's stance on consciousness".

## Seat 2 (secondary, partial): yi:34b-v1.5 on the dreamer CPU hub :11442

Started first, while :11433 was still wedged. This hub takes format "json" only (no schema grammar) and honours
only temperature, top_p and num_predict, so the penalties and the seed were not applied. About 176 s per call.
A1 is complete (43). B was stopped at 10 of 43 once the Bonsai seat had served all three arms. File:
run2_dreamer.jsonl (53 rows).

A1: valid 43/43, schema ok 43, decomposed 42, both lanes 34, degenerate 1, mean 3.56 ingredients (4 on 29/43),
20 rows padded with two or more same-type/same-lane items (#33 has three fact items that restate one need),
identity deferred only 2 of 28, rule violations 27. This seat over-decomposes and ignores the defer rule.
