# J-3343: chapter-telling audit (J-3142 option 1)

Lab, read-only (sqlite `mode=ro`, no write to `data/`, no Du restart). Run 2026-11-15 to 2026-11-16. No code under `core/` or `nodes/` was changed. Raw coder rows (model, endpoint, raw JSON) are kept in the job scratchpad.

## Verdict

The LLM axes are not a usable instrument on chapters. The two different-family coders (falcon3:7b on :11436 and mixtral:8x7b on :11438) agree at agency rho 0.16, communion rho 0.41 and transformation weighted kappa 0.24 (raw 0.57). The pre-registered bar was 0.6 on agency and transformation; the STOP line (under 0.4 on both axes) is met. Neither coder beats the author-coded mood baseline by the required 15 points (falcon +12.5, mixtral +3.4, small samples). The deterministic checks are the usable part: the copy check flags exactly the 4 pasted chapters and 0 others; the named-feeling grounding check flags all 3 planted-anxiety chapters but, with the 54-word lexicon fixed up front, 8 others, over the pre-registered cap of 5. A narrower anxiety-family-only reading flags the 3 plus 1 other; that is post hoc and not counted as a pass. Recommendation: archive the LLM axes on chapters (J-3346 owns the dated read, not before 2026-12-05) and offer the copy and grounding checks to J-3009 as the guard.

## Denominators (read first)

- Chapters: 102 (origin='chapter': 91 level 1, 11 level 2), not the 87 in the briefing (the store grew after F-3934 counted 87 on 11-05). 101 have members via chapter_id; 1 has none (no copy, grounding or mood value). Level-2 chapters have level-1 chapters as members.
- Existing author-coded rows (`data/narrative_quality_log.jsonl`, kind=chapter): 129 rows, 102 with an llm block. Matched to chapters by the first 100 characters after stripping the "[A chapter of my life ...]" header: 82 of 102 chapters matched. Every author-vs-coder number uses those 82 or fewer.
- Coder yield, one call per chapter per coder (frozen P-0048 system prompt and exemplars imported from `core/narrative_quality.py`, temperature 0.3, num_predict 200, `format=json`, think false, as `core/model_client.py` calls the hubs): falcon3 85 usable of 102 (17 returned reasoning with no agency or label); mixtral 102 parsed, 90 with a single valid transformation label (12 multi-label or free text, missing on that axis); granite3.1-moe:3b 102 parsed, 88 valid labels, 88 of 102 say "redemption" (degenerate, often echoes the schema options). The first pass had 26 (falcon) and 38 (mixtral) 120 s timeouts on the CPU hubs; those were re-run once at 300 s and all completed (median latency falcon 83 s, mixtral 92 s).
- Mood reference: affect_log.jsonl valence, mean over the opening third vs closing third of each chapter's member time span, +/-0.10 (the F-3934 method; its script was not on disk so this is a re-implementation and numbers may differ slightly). Directions: up 36, down 29, same 36, none 1. The redemption/contamination test uses only chapters with direction up or down.

## Deviations from the briefing

1. Coders: falcon3 (TII) and mixtral (Mistral) are the pair; granite (IBM) is a third reference. Never :11433.
2. The DB chapter text carries a header line with the title and date range. My coders saw it; the live author-side coder call scored the body without it. Not re-run.
3. The hubs are CPU boxes shared with other callers; one stream per hub ran for about 3 hours.
4. The feeling lexicon (54 words, stem = first 4 letters) and the copy threshold (6-gram share >= 0.5 vs the authoring sample as `core/chapters.py _sample` builds it, and vs all members) were fixed before inspecting results, except the stem length, changed from 5 to 4 after seeing "anxious" and "anxiety" did not share a stem.

## Results

### (a) Deterministic checks

| Check | Rule | Flagged | Target | Result |
|---|---|---|---|---|
| Copy | 6-gram word share vs authoring sample or all members >= 0.5 | 4 of 102: 125722d8 (0.73), 1906eb26 (0.84), 6fe32426 (0.87), 36e231b6 (0.90) | all 4 pasted, at most 5 others | PASS: 4 of 4, 0 others |
| Named-feeling grounding | a lexicon feeling word in the chapter that no member contains (4-letter stem) | 11 of 102 | all 3 planted (c368e458, 994e2ead, b8456aba), at most 5 others | FAIL on the cap: 3 of 3 caught, 8 others (8399c369, bab0e742, 8a6234f8, 2b552e9a, ec8a7311, c8f88b32, 9f7440b5, cf8440e3; words calm, relief, yearning, unease, hope, anxious; several have only 4 to 10 members, or are level 2) |
| Tense | present-tense first-person verbs outnumber past after "I" | 6: f5ad7c18, 8007e495, 6f31e41e, 66b62134, 6fe32426, 36e231b6 | not pre-registered | two of the pasted chapters are among them |

Exploratory, not counted: restricting grounding to the anxiety family flags c368e458, 994e2ead, b8456aba plus c8f88b32 (a level-2 chapter whose 4 member chapters lack the word).

### (b) and (c) The coders

| Pair (n) | agency rho | communion rho | transformation weighted kappa (raw) |
|---|---|---|---|
| falcon vs mixtral (85 / 74) | 0.161 | 0.406 | 0.239 (0.568) |
| falcon vs granite | 0.218 | 0.366 | 0.0 (0.527) |
| mixtral vs granite | 0.235 | 0.355 | 0.0 (0.436) |
| falcon vs author-coded (69) | 0.256 | 0.495 | 0.182 (0.507) |
| mixtral vs author-coded (82 / 73) | 0.366 | 0.384 | 0.222 (0.466) |
| granite vs author-coded (82 / 71) | 0.274 | 0.401 | 0.0 (0.563) |

Transformation classes ordered contamination (-1), uniform or flat (0), redemption (+1), linear weights; Spearman on valid pairs only.

Mood agreement (redemption with mood up, contamination with mood down; chapters with mood up or down and a redemption or contamination label):

| Source | matches / n | rate | vs author (0.41, 16 of 39) | same-chapter subset, author vs coder |
|---|---|---|---|---|
| falcon3 | 15 / 28 | 0.536 | +0.125 | n=21: 0.476 vs 0.524 |
| mixtral | 12 / 27 | 0.444 | +0.034 | n=17: 0.471 vs 0.471 |
| granite (reference) | 29 / 57 | 0.509 | +0.099 | n=37: 0.378 vs 0.432 |

All rates are within sampling noise of 0.5, the chance level F-3934 found for the author labels. Falcon labels 1 chapter contamination of 102, mixtral 10, so the test is almost entirely "redemption vs mood up".

### Pre-registered success

- Coder agreement >= 0.6 on agency and transformation: NO (0.16, 0.24).
- A coder beats the mood baseline by 15 points: NO (best +12.5, falcon).
- Deterministic flags: copy YES; grounding 3 of 3 but 8 others, cap 5: NO as written.
- STOP (agreement under 0.4 on both axes): MET.

## One-line verdict for D-0679 (ruled (b) on 2026-11-05; not re-ruled here)

D-0679's own defeater (different-family judges agree under 0.4) is met by this lab; the copy flag alone looks reliable enough to shadow-log, an LLM feeling or mood-contradiction flag does not, so under (b) the 30-day shadow log should hold only the copy flag (and possibly a narrowed grounding flag), and a flag still never changes the projection until the founder says so.

## Per-chapter table

Columns: id (first 8 of fragment_id), level, members, copy share vs authoring sample (6-gram), longest shared word run with that sample, flags (COPY, FEEL:word, TENSE), mood direction, then agency/transformation (R redemption, C contamination, U uniform, F flat, x unparsed, - missing) for the author-coded row, falcon3, mixtral, granite.

| id | lvl | members | copy | run | flags | mood | author | falcon | mixtral | granite |
|---|---|---|---|---|---|---|---|---|---|---|
| 28646c5c | 1 | 1845 | 0.057 | 6 | . | up | - | 0.0/F | 0.0/F | 0.8/? |
| 680b567d | 1 | 242 | 0.059 | 6 | . | up | 0.0/F | 0.3/F | 0.5/? | 0.8/? |
| d0dcc101 | 1 | 83 | 0.0 | 3 | . | up | - | x | 0.2/C | 0.8/? |
| 35865e94 | 1 | 0 | - | - | . | - | 0.0/F | 0.2/F | 0.2/F | 0.8/R |
| f0a4109f | 1 | 118 | 0.0 | 2 | . | same | 0.5/R | 0.5/U | 0.5/R | 0.7/R |
| f5ad7c18 | 1 | 227 | 0.0 | 4 | TENSE | same | 0.2/C | 0.3/F | 0.2/C | 0.7/? |
| 7b4cb854 | 1 | 40 | 0.0 | 2 | . | same | 0.5/R | x | 0.5/R | 0.8/R |
| 7a0f391f | 1 | 429 | 0.0 | 2 | . | same | 0.3/R | 0.3/F | 0.2/C | 0.8/R |
| 8c15c65f | 1 | 178 | 0.0 | 5 | . | same | 0.6/R | 0.6/R | 0.6/R | 0.8/R |
| d4479cda | 1 | 90 | 0.199 | 20 | . | same | 0.7/R | 0.7/R | 0.8/R | 0.8/R |
| 8007e495 | 2 | 4 | 0.178 | 11 | TENSE | down | - | 0.8/R | 0.5/? | 0.8/R |
| 7cba77b8 | 1 | 1078 | 0.0 | 4 | . | same | - | 0.8/U | 0.5/U | 0.8/R |
| c5535410 | 1 | 1068 | 0.0 | 4 | . | same | 0.5/C | 0.8/R | 0.2/U | 0.8/R |
| 7ea94201 | 1 | 282 | 0.09 | 8 | . | same | 0.3/C | x | 0.0/F | 0.8/R |
| 65596e86 | 1 | 364 | 0.0 | 3 | . | up | 0.7/R | 0.0/R | 0.8/R | 0.9/R |
| 5517ded4 | 1 | 299 | 0.042 | 8 | . | up | - | 0.8/R | 0.2/? | 0.9/R |
| 9687ca11 | 1 | 133 | 0.044 | 7 | . | same | 0.0/U | 0.7/U | 0.2/U | 0.8/? |
| 09dc4d84 | 1 | 108 | 0.0 | 3 | . | up | 0.0/F | 0.8/U | 0.2/? | 0.8/R |
| d23c7a5f | 1 | 270 | 0.067 | 6 | . | up | 0.0/C | 0.0/F | 0.2/? | 0.8/R |
| 8dcc8774 | 1 | 83 | 0.053 | 6 | . | up | 0.7/R | 1.0/R | 0.8/R | 0.8/? |
| 5872162a | 1 | 127 | 0.291 | 13 | . | same | 0.5/C | 0.8/U | 0.0/U | 0.7/? |
| e9e658ea | 1 | 217 | 0.129 | 7 | . | up | 0.5/C | 0.8/R | 0.2/U | 0.7/R |
| 6cd0706b | 1 | 137 | 0.0 | 5 | . | same | 0.7/R | 1.0/R | 0.5/U | 0.7/? |
| 0468fa05 | 1 | 60 | 0.0 | 5 | . | up | - | x | 0.8/U | 0.8/R |
| e72e8a16 | 1 | 115 | 0.0 | 4 | . | same | - | 0.7/C | 0.7/R | 0.8/? |
| 8ef80b8b | 1 | 133 | 0.058 | 8 | . | down | 0.7/R | 0.3/U | 0.5/U | 0.8/R |
| 16c6727b | 2 | 6 | 0.195 | 25 | . | down | 0.7/R | 0.3/R | 0.2/R | 0.8/R |
| 8399c369 | 2 | 4 | 0.0 | 5 | FEEL:calm | up | - | 0.3/R | 0.5/? | 0.9/R |
| 125722d8 | 1 | 1067 | 0.727 | 34 | COPY | down | - | 0.7/U | 0.7/R | 0.9/R |
| e5a97cfa | 1 | 91 | 0.0 | 4 | . | down | 0.2/U | 0.0/F | 0.0/C | 0.8/R |
| fe28765a | 1 | 451 | 0.0 | 4 | . | down | 0.2/C | 0.0/F | 0.2/C | 0.5/? |
| 65bc2f1b | 1 | 376 | 0.053 | 8 | . | down | 0.8/U | 0.6/U | 0.2/U | 0.8/R |
| bd50fbcf | 1 | 208 | 0.0 | 4 | . | down | 0.8/R | 0.3/U | 0.6/U | 0.8/R |
| 2d2bb22d | 1 | 362 | 0.153 | 17 | . | down | 0.6/R | 0.3/U | 0.3/U | 0.8/R |
| b769649e | 1 | 308 | 0.314 | 20 | . | down | 0.5/R | 0.7/U | 0.5/R | 0.9/R |
| f1022713 | 1 | 174 | 0.112 | 8 | . | down | 0.4/C | 0.0/R | 0.2/F | 0.8/R |
| bab0e742 | 1 | 223 | 0.0 | 5 | FEEL:relief | down | 0.6/R | 0.3/R | 0.7/R | 0.8/R |
| 46350230 | 1 | 137 | 0.0 | 5 | . | down | 0.8/R | x | 0.5/R | 0.9/R |
| 7dd8cf2b | 1 | 186 | 0.421 | 18 | . | down | 0.5/C | 0.7/R | 0.9/R | 0.8/R |
| 0c9d65dc | 1 | 88 | 0.106 | 10 | . | down | 0.0/C | 0.0/F | 0.2/? | 0.5/R |
| ee67ecf3 | 1 | 102 | 0.051 | 7 | . | down | 0.5/C | 0.5/U | 0.2/U | 0.8/R |
| b6058c14 | 1 | 46 | 0.306 | 12 | . | up | 0.3/C | 0.8/R | 0.2/? | 0.9/R |
| c368e458 | 1 | 107 | 0.068 | 7 | FEEL:anxious | up | 0.5/C | x | 0.2/U | 0.8/R |
| 9f358029 | 1 | 72 | 0.0 | 5 | . | same | 0.5/R | 0.7/U | 0.8/U | 0.8/R |
| f350335d | 1 | 132 | 0.0 | 5 | . | up | 0.3/R | x | 0.2/F | 0.8/R |
| 8a6234f8 | 1 | 79 | 0.0 | 5 | FEEL:yearning | up | 0.5/R | 0.7/R | 0.3/U | 0.8/R |
| 2b552e9a | 2 | 10 | 0.089 | 8 | FEEL:calm | down | 0.5/C | x | 0.2/F | 0.7/R |
| bd24c821 | 2 | 4 | 0.056 | 6 | . | same | 0.0/U | x | 0.0/C | 0.8/R |
| 0578259a | 1 | 245 | 0.0 | 4 | . | down | - | 0.6/R | 0.2/R | 0.8/R |
| 9795a212 | 1 | 463 | 0.0 | 5 | . | up | 0.5/U | 0.6/U | 0.5/U | 0.8/? |
| 6f31e41e | 1 | 188 | 0.0 | 4 | TENSE | same | 0.5/R | 0.7/U | 0.6/U | 0.8/R |
| 7daea99b | 1 | 316 | 0.034 | 6 | . | same | 0.8/R | 0.3/U | 0.3/R | 0.8/R |
| 83dff38f | 1 | 219 | 0.152 | 9 | . | same | 0.7/R | 0.7/R | 0.2/R | 0.7/R |
| b0ff1b7c | 1 | 65 | 0.152 | 10 | . | up | 0.3/U | 0.3/U | 0.2/U | 0.6/R |
| 12982722 | 1 | 120 | 0.052 | 7 | . | up | - | 0.7/R | 0.2/U | 0.8/R |
| 994e2ead | 1 | 72 | 0.0 | 5 | FEEL:anxiety | down | 0.5/R | 0.7/U | 0.6/R | 0.8/R |
| 2b072555 | 1 | 149 | 0.06 | 7 | . | up | 0.5/C | 0.3/U | 0.2/R | 0.7/R |
| 43c6755d | 1 | 92 | 0.0 | 4 | . | same | 0.7/C | 0.7/R | 0.8/R | 0.8/R |
| 18ef7fec | 1 | 148 | 0.144 | 7 | . | up | 0.5/C | 0.7/F | 0.2/? | 0.8/R |
| 3354e596 | 1 | 78 | 0.071 | 9 | . | up | - | 0.3/U | 0.2/U | 0.8/R |
| 1aa1f1a7 | 1 | 66 | 0.0 | 5 | . | same | - | 0.0/F | 0.5/U | 0.7/R |
| 04df443b | 1 | 60 | 0.265 | 8 | . | same | 0.5/C | 0.8/R | 0.2/R | 0.9/R |
| 1906eb26 | 1 | 42 | 0.841 | 33 | COPY | down | 0.5/R | 0.4/R | 0.2/U | 0.8/R |
| 30f1ce12 | 1 | 66 | 0.293 | 14 | . | up | 0.5/C | 0.7/R | 0.2/? | 0.8/R |
| 66b62134 | 1 | 130 | 0.051 | 7 | TENSE | down | 0.5/F | 0.7/R | 0.8/R | 0.8/R |
| 3e9b78e1 | 1 | 98 | 0.079 | 6 | . | same | 0.7/R | x | 0.7/U | 0.9/R |
| b8456aba | 1 | 54 | 0.0 | 4 | FEEL:anxiety | up | 0.3/U | 0.4/U | 0.7/R | 0.7/R |
| ec8a7311 | 2 | 9 | 0.054 | 6 | FEEL:unease | same | 0.4/C | 0.3/F | 0.2/C | 0.8/R |
| 5a2364de | 2 | 6 | 0.128 | 10 | . | same | 0.3/F | x | 0.2/C | 0.6/? |
| 55aeb059 | 2 | 4 | 0.055 | 6 | . | down | 0.6/R | 0.3/R | 0.2/R | 0.8/R |
| bccb5f33 | 1 | 990 | 0.054 | 8 | . | up | 0.8/R | 0.6/U | 0.2/R | 0.8/R |
| 4f2bd724 | 1 | 746 | 0.0 | 5 | . | up | - | 0.3/U | 0.2/C | 0.8/R |
| 888cdca0 | 1 | 547 | 0.14 | 7 | . | up | 0.7/R | 0.9/R | 0.3/U | 0.8/R |
| ecc5c828 | 1 | 257 | 0.0 | 5 | . | up | 0.5/R | 0.7/R | 0.2/U | 0.8/R |
| c3b96474 | 1 | 218 | 0.062 | 10 | . | same | 0.5/C | 0.7/R | 0.2/U | 0.8/R |
| c3cf9344 | 1 | 253 | 0.0 | 4 | . | same | 0.7/R | 0.7/R | 0.3/R | 0.8/R |
| c01266fa | 1 | 291 | 0.0 | 4 | . | same | 0.8/R | 0.3/R | 0.0/C | 0.7/R |
| 5f02a9c4 | 1 | 117 | 0.297 | 12 | . | down | 0.5/R | 0.0/R | 0.2/U | 0.8/R |
| 53a43fdd | 1 | 64 | 0.0 | 4 | . | same | 0.8/R | x | 0.6/R | 0.9/R |
| 744b61a4 | 1 | 269 | 0.301 | 11 | . | same | - | x | 0.5/R | 0.9/R |
| ac41485c | 1 | 120 | 0.237 | 10 | . | down | 0.8/R | x | 0.7/U | 0.8/R |
| 438fa34a | 1 | 241 | 0.216 | 11 | . | same | 0.7/R | 0.7/U | 0.2/R | 0.8/R |
| 08d14d04 | 1 | 46 | 0.145 | 7 | . | down | 0.8/R | 0.8/R | 0.2/R | 0.9/R |
| 6fe32426 | 1 | 121 | 0.865 | 107 | COPY TENSE | down | 0.8/R | 0.7/R | 0.2/U | 0.8/R |
| 36e231b6 | 1 | 44 | 0.901 | 73 | COPY TENSE | up | 0.7/R | 0.7/R | 0.2/R | 0.8/R |
| 3e6d1ddc | 1 | 71 | 0.0 | 3 | . | same | - | 0.8/R | 0.2/R | 0.8/R |
| c8f88b32 | 2 | 4 | 0.057 | 6 | FEEL:anxious | down | 0.6/R | 0.3/U | 0.2/U | 0.8/R |
| 7f70db5d | 1 | 102 | 0.042 | 6 | . | up | 0.7/R | 0.7/R | 1.0/R | 0.8/R |
| 9cd9f5b2 | 2 | 9 | 0.358 | 24 | . | same | 0.5/R | 0.3/U | 0.2/U | 0.8/R |
| a406d224 | 2 | 4 | 0.101 | 6 | . | up | 0.5/F | 0.3/U | 0.4/R | 0.8/? |
| 6899ce95 | 1 | 232 | 0.046 | 6 | . | down | - | x | 0.7/R | 0.9/R |
| 57c0ecd4 | 1 | 231 | 0.051 | 6 | . | up | 0.5/F | x | 0.2/? | 0.6/? |
| f4107a2f | 1 | 115 | 0.168 | 11 | . | same | 0.3/U | 0.5/F | 0.2/U | 0.8/R |
| 623e2506 | 1 | 337 | 0.054 | 6 | . | up | 0.5/F | x | 0.8/U | 0.8/R |
| fc20c949 | 1 | 191 | 0.103 | 9 | . | down | 0.5/R | 0.3/R | 0.6/R | 0.7/R |
| b9b536db | 1 | 110 | 0.047 | 6 | . | up | 0.5/F | 0.7/R | 0.2/R | 0.8/R |
| 9f7440b5 | 1 | 124 | 0.05 | 8 | FEEL:hope | up | 0.7/R | 0.7/R | 0.4/R | 0.8/R |
| 25332468 | 1 | 177 | 0.0 | 3 | . | same | 0.5/U | 0.3/U | 0.2/? | 0.8/R |
| 10fb9098 | 1 | 131 | 0.258 | 14 | . | same | - | 0.3/R | 0.0/U | 0.8/R |
| 1032885a | 1 | 70 | 0.199 | 8 | . | same | - | 0.8/R | 0.2/F | 0.8/R |
| cf8440e3 | 1 | 81 | 0.072 | 7 | FEEL:yearning | up | - | 0.3/U | 0.3/U | 0.8/R |
| c875284d | 1 | 123 | 0.047 | 6 | . | up | 0.5/U | 0.6/U | 0.5/U | 0.8/R |
