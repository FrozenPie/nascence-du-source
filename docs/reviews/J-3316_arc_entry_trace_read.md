# J-3316: does arc_entry carry anything evidence, delta and self_concept do not (D-0672)

Read-only. Source: data/logs/t4_chain_trace.jsonl, 60 rows (all, 2026-11 run after J-3007 shipped). Method: lexical analysis (content words, stoplist), plus a small decoupled judge read (falcon3:7b on judge2 :11440, temperature 0, 23 calls, no stores written). Scratch scripts in the job scratchpad.

## Gate caveat
The gate said "60 rows with arc_entry". The file has 60 rows but only 40 carry a non-empty arc_entry: 20 empty (33 percent), 17 title-only (a "Chapter: ..." line and no body, 28 percent), 23 full arcs (553-962 chars, 38 percent). Everything content-related below is over the 23 full arcs (n is small).

## (1) Novelty
Share of the body's distinct content words absent from evidence + delta + self_concept: median 0.68, mean 0.68, max 0.84; none of 23 under 15 percent. Also absent from the raw crossings the arc could see: median 0.65, none under 15 percent. The words are largely rhetorical or abstract, but some are concrete particulars not in any of the other fields (row 3 "napoleon", row 29 "auricula", row 20 "maples", "migration"). Absence from the crossings means either genuine association or confabulation; this read cannot separate them. Verdict: the arc is NOT redundant with evidence/delta/self_concept lexically. The stop condition (novelty under 15 percent for 80 percent of rows) is not met.

## (2) Decoupled judge
falcon3:7b (different family from the qwen author), asked whether the arc claims a movement the crossings do not show: 21 of 23 supported, 2 unsupported (rows 41, 52). Caveat: this judge is plainly permissive (it accepts "shift from abstract fear to action" on nearly every row, and it accepted arcs whose vocabulary is 65 percent absent from the crossings), so it is weak evidence in either direction. Not a hand grade. Same method as D-0603 but a 7B, one pass, no kappa check.

## (3) Template
Title line: 23 of 23 full arcs, and 38 of 40 non-empty, start with "Chapter" (95 percent); "Chapter: The ..." 20 times. Body opener: most common two-word opener "the study" 3 of 23 (13 percent), trailing windows of 20 top out at 2 to 3 repeats. So the template lives in the title, not the body. Bag-of-words cosine to the previous arc: median 0.07 (0.09 on full arcs only), max 0.36; none over 0.5. The opener-share-over-50-percent stop condition is met only for the title prefix, not the body, and the novelty half of the condition fails, so the drop rule is not triggered.

## (4) Title-only
17 of 60 rows (28 percent) are title-only, 17 to 35 chars, e.g. "Chapter: The Scouring Current". With the 20 empty rows, 62 percent of runs store no body.

## Verdict on D-0672 (recommendation only; the ruling is the founder's)
Do not drop on this evidence. When a body is written (38 percent of runs) it is lexically novel against the other three fields and not echoing its predecessor. Two open problems: (a) 62 percent of runs yield nothing of value, so as a store it is mostly titles; (b) whether the novel content is grounded is unresolved, since the judge is too permissive to tell. Named reader the full arcs could serve: a reader of "what is Du's story in the last N days" (they are the only field carrying particulars absent from self_concept). Next step if the founder wants a firmer verdict: hand-grade the 23 arcs for grounding (about 30 minutes), and check why title-only/empty rates are 62 percent (possible fix is in the prompt wording "one short chapter naming this movement" per J-3215).
