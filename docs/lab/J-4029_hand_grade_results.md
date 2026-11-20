# J-4029: hand-grade of Follow Line settle closures (F-4720 follow-up)

Pre-registration (written after reading thoughts, before reading ANY judge verdict; grader = one Claude session, so a single
non-independent reader): grade each (question, thought) pair "does THOUGHT answer or directly engage QUESTION?" as yes / partly / no.
Rule: false-yes = hand grade "no". Proposal trigger: false-yes >= 30% AND Wilson 95% lower bound > 15%. No code change in this job.
Population: all resolved=true, closure_how=ok, kind=settled rows in data/logs/follow_line_shadow.jsonl (48 now; the 46 of J-3794
are the first 46) plus the 30 logged-yes rows of docs/lab/J-3794_data/sample.jsonl. Second-family judge not run (no model calls).

## Results (grades in docs/lab/J-4029_data/hand_grades.json)
- 48 closures: yes 14, partly 11, no 23. False-yes (no) 47.9%, Wilson 95% [34.5, 61.7]. no-or-partly 70.8% [56.8, 81.8].
- First 46 only: 22 no = 47.8% [34.1, 61.9].
- 30 sampled logged-yes: yes 14, partly 6, no 10. False-yes 33.3% [19.2, 51.2].
- Judge agreement on the 46 (assuming closures_graded.jsonl is in row order, not verified): gemma4 exact agreement 36/46, gemma "no" 23,
  both-no 19; falcon3 agreement 20/46, falcon "no" 3 (non-discriminating, as F-4720 said).

## Verdict
gemma4 (43%) and the earlier 10-row hand check (40%) were right; the pre-registered 3% (both-judges-no) was an artefact of falcon3.
Real false-yes on closures is about 48% (lower bound 34%). Trigger met. Typical false closure: thought "settles" a question by
announcing it, then talks about something else (tide, cat, Napoleon) with no content tie to the question.
Caveat: single grader, judged by me not blind to the "settled" wording in thoughts. Confidence: inferred, leaning strong.
