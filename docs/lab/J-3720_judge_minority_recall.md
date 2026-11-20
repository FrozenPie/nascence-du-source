# J-3720: per-key judge informativeness (minority-class recall)

Source: docs/lab/J-3410_data/order_replay_falcon3.jsonl and order_replay_gemma4.jsonl (read-only; no new model calls).
Labelled pairs only (ambiguous "A" metaphor rows excluded). Fixtures: J-3232 same_lesson, J-3210 held, J-3205 metaphor.
Recall is on the minority class; balanced accuracy = mean of the two class recalls (0.50 = constant answer).

| key | judge | n pos / neg | minority recall (shipped / reversed order) | balanced acc | verdict |
|---|---|---|---|---|---|
| P-0109 held | falcon3:7b | 23 / 7 | 0.00 / 0.14 (not-held) | 0.50 / 0.55 | CONSTANT (always "held") |
| P-0109 held | gemma4:12b | 22 / 5 | 0.60 / 0.67 | 0.78 / 0.79 | informative, n=5 minority is thin |
| P-0110 metaphor | falcon3:7b | 12 / 60 | 0.08 / 0.17 (figurative) | 0.54 / 0.58 | CONSTANT (always "false") |
| P-0110 metaphor | gemma4:12b | 10-11 / 59 | 1.00 / 1.00 | 0.95 / 0.94 | informative (over-calls true ~10% of literals) |
| P-0117 same_lesson | falcon3:7b | 66 / 66 | 0.97 / 0.97 (not-same) | 0.92 | informative |
| P-0117 same_lesson | gemma4:12b | 63-64 / 64 | 0.92 / 0.98 | 0.95 | informative |

Only three keys have a hand-labelled boolean fixture in docs/lab; the J-3232 judge_runs_* files are a different 3-way task (compatible_different etc.), not a panel key. Other panel keys have no fixture, so they cannot be scored.

Limits: falcon3 held minority n=7 (0/7 has 95% Wilson upper bound about 0.35); falcon3 metaphor minority n=12 (1-2/12, upper bound about 0.35-0.45); gemma4 held minority n=5. The metaphor F labels are Claude pre-labels, not human. So "at or below chance" is established for falcon3 on held and metaphor, and only suggested, not excluded-at-large, by the small n.

Founder note: where one panel member answers the same way on a key, Judge1/Judge2 agreement on that key reflects the other judge's lean, not two independent readings. On held and metaphor, falcon3 agreement with gemma4 is roughly gemma4's own base rate. Recommend reporting, next to the panel agreement statistic, each judge's minority-class recall (or balanced accuracy) per key, and treating a key as single-judge when either judge is within chance. Follow-up that needs founder/live-LLM time: a larger held/not-held and figurative fixture to tighten the bounds.
