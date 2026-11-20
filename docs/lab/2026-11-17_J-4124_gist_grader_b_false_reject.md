# J-4124 lab: false-reject rate of full gist grader (b) with support quote

Status: DONE with a partial bad-row set (8 of 9 pre-listed bad rows not all run; stopped at the ~60 min wall cap). Nothing in core/ changed.

Setup: variant (b) = J-3083 TASK_B (typed claims + support quote), num_predict 700, gemma4:12b on :11439 (CPU hub, num_gpu 0, temp 0), timeout 900 s, lab_env isolate(db="empty"), 2 concurrent workers (hub tolerated this; 290-710 s per call, no timeouts). Script: docs/lab/J-4124_data/lab_j4124_gist_grader.py, rows J-4124_res_b.jsonl. Rows from earlier passes with the identical prompt were reused (J-3083 idx 0-4, 51, 57, 60, 61). Ramses hubs :11437/:11438/:11441 did not answer (nothing listening); not needed.

## Faithful gists (13, labels_fullsource good; self 5, semantic 4, episodic 4)
faithful score: self 0.9,1.0,0.8,1.0,1.0; semantic 1.0,1.0,1.0,1.0; episodic 1.0,1.0,1.0,0.67.
- False-reject at faithful <= 0.5 (the rule that "caught" #51/#61): 0 of 13 (bar <= 1 of 10 met). Per-kind pass-rate loss: 0 pts in self, semantic, episodic (bar <= 15 pts met).
- At a stricter cut (<0.9): 2 of 13 would be rejected (#2 self 0.8, #48 episodic 0.67).

## Known bad gists run with (b)
#51 0.5, #61 0.5 (caught), #43 0.75, #41 0.86, #57 0.83, #28 1.0, #44 1.0, #60 1.0 (missed). Not run: #46,#50,#52,#53 (time cap).
- Catch at <= 0.5: 2 of 8 bad rows run (the earlier "2 of 3" was the 3 J-3083 known errors #51,#60,#61 -> still #51,#61). Of the 5 additional bad rows, none scored <= 0.5; loosening to <0.9 would catch #43,#41,#57 (+3) but cost the 2 false rejects above (2/13).
- So (b) is precise (no false reject at its working cut) but low recall on the wider bad set: the quote step catches question-premise errors but not abstract over-claims, matching the J-4038 caveat that the bad labels beyond #51/#61 are subtler.

## Verdict
(b) clears the false-reject bar and the pass-rate-loss bar, but its recall on the broader bad set is poor (2/8 at <=0.5) and each call costs 5-12 min on the CPU hub, so it is not a candidate for a per-gist production gate. Faster hub / smaller model question: latency is prompt-evaluation on a shared CPU hub; a founder question is not warranted until a recall-adequate prompt exists (a speed fix would only speed a low-recall grader). Deterministic misattribution check (J-4038) stays the cheap path for one pattern.

Isolation: lab dir only; top-level data/ file set unchanged vs the J-4038 canary (504 files, none new or removed).
