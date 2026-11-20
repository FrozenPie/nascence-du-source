# J-2952: gold-label accuracy of the shared judge-panel TIEBREAK (granite3.1-moe:3b), 2026-11-15

From F-3639 / P-0096. Read-only toward Du. Script: `scripts/lab_j2952_tiebreak_gold.py`; data: `docs/lab/J-2952_data/` (cases.json, runs.jsonl).

## Method and limits (read these first)
- Cases: 111 real splits (mixtral v1 != falcon v2) from `data/judge_inputs_log.jsonl`, the only log keeping case text (judge_panel_log.jsonl keeps an 80-char context). It holds 350 splits in total, so this is not ~30 per requested key: cuts 25, advances 26, bears 25, supported 17, held 7, coherent 6, follows 5. genuine, resolves, taken_up have no usable captured splits (genuine/resolves splits are `split_no_tiebreak`, skipped by D-0530) and were not measured.
- Gold: ONE labeler (Claude), applying each key's shipped rubric to the case text, strict reading ("when uncertain, false"). Not founder-labelled. Uncertain labels are flagged in the script; the last column keeps only certain ones. coherent/follows labels are all low confidence.
- Granite was called at :11437 with the exact shipped system prompt (recovered by sha1) and the production payload (temperature 0), via direct HTTP so nothing was written to data/. Swapped = option order reversed with `reverse_option_order`.
- "mixtral alone" / "falcon alone" are the original logged votes scored against gold (the split guarantees they disagree). Third family (gemma4 :11439): 1 of 7 keys returned anything in 150 s timeouts (local CPU hub busy), so NOT measured; the run was stopped.
- Selection bias: these are splits only, the hard cases where the two judges disagree, so absolute accuracies are not the panel's overall accuracy.

## Table
| key | n | gold true | granite orig | granite swapped | granite true-rate orig/swap | mixtral alone | falcon alone | gemma4 | const-prior acc | granite orig, certain labels only |
|---|---|---|---|---|---|---|---|---|---|---|
| advances | 26 | 1 | 16/26 | 1/26 | 0.42 / 1.00 | 1/26 | 25/26 | 0/0 (26 null) | 0.96 | 15/25 |
| bears | 25 | 7 | 10/25 | 11/25 | 0.88 / 0.84 | 17/25 | 8/25 | 0/0 (25 null) | 0.72 | 8/23 |
| coherent | 6 | 1 | 4/6 | 2/6 | 0.17 / 0.83 | 1/6 | 5/6 | 0/0 (6 null) | 0.83 | 0/0 |
| cuts | 25 | 4 | 7/25 | 4/25 | 0.88 / 1.00 | 21/25 | 4/25 | 2/4 (21 null) | 0.84 | 5/23 |
| follows | 5 | 1 | 2/5 | 2/5 | 0.80 / 0.80 | 3/5 | 2/5 | 0/0 (5 null) | 0.80 | 0/0 |
| held | 7 | 7 | 0/7 | 0/7 | 0.00 / 0.00 | 0/7 | 7/7 | 0/0 (7 null) | 1.00 | 0/7 |
| supported | 17 | 2 | 3/17 | 2/17 | 0.94 / 1.00 | 8/17 | 9/17 | 0/0 (17 null) | 0.88 | 2/16 |
granite flips under swap: 24 / 111

(n = cases with a verdict; "null" = no parsable answer. const-prior acc = accuracy of always answering the gold-majority class.)

## Reading
- granite never beats the constant prior on any key it was measured on (cuts 7/25 vs 0.84; supported 3/17 vs 0.88; bears 10/25 vs 0.72; advances 16/26 vs 0.96; held 0/7). On the splits that reach it, granite is at or below chance-level class guessing.
- held: gold TRUE on all 7 (the observed percepts list the predicted sound), granite FALSE on 7/7 in both orders. Matches F-3639's 0.00 true-rate and is the clearest case of a constant answer.
- cuts / supported: granite says TRUE 88-100% regardless of order while gold is mostly FALSE (the objections and whys mostly restate or do not follow). Same per-key prior as F-3639 (0.95+ true on supported).
- advances: not a constant, but it follows option position, not the case: true-rate 0.42 in the shipped order and 1.00 when the order is reversed. 24 of 111 granite verdicts flip under the swap overall (coherent 0.17 -> 0.83 as well). Content is not driving the answer there.
- bears: about 0.85 TRUE both orders vs gold 7/25 true; accuracy 10-11/25.
- falcon alone beats mixtral alone on advances, held, coherent (falcon 25/26, 7/7, 5/6); mixtral beats falcon on cuts (21/25 vs 4/25) and bears (17 vs 8). Neither is consistently right, so which judge a split resolves toward matters per key and the tiebreak is not adding information in either direction.
- Answer to the job's question: granite answers a per-key prior (held, cuts, supported, bears) or option position (advances, coherent), not the case. Sample is small and single-labelled; treat the direction as strong and the per-key percentages as rough.
