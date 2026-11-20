# J-3794 pre-registration: blind re-grade of Follow Line settle verdicts (F-4417)

Committed BEFORE any judge call.

## What is being tested
The logged settle verdict (yes/partly/no/unsaid) is NOT from a separate judge: it is Du's own `settled` field in his
idle-thought JSON (core/follow_line.py parse_settled; generator = the idle-thought model, command-r7b family), self-reported
on the tick a return was delivered. So this re-grade asks whether Du's self-report agrees with an outside reader.

## Sample
scripts/lab_J-3794_sample.py, seed 3794, frozen to rows with ts <= 1794650552.2. 120 rows: 30 each of yes, partly, no, unsaid
(20 after 2026-11-08 10:51 + 10 before, per stratum; 80 post total). Rows with empty q or thought excluded. Output: docs/lab/J-3794_data/sample.jsonl.

## Judge
Different family from generator: gemma4:12b via :11439 (primary) and falcon3:7b via :11440 (second). temperature 0.
Logged verdict hidden; order shuffled (sample is pre-shuffled, sid order). Prompt (fixed):
"QUESTION: ... THOUGHT: ... Does THOUGHT answer or directly engage QUESTION? Answer with one word: yes, partly, or no."
Parsed: first of yes/partly/no found in lowercase reply; else invalid (counted, not retried).

## Metrics and decision rules
- Per-stratum agreement of primary judge verdict with logged verdict (exact), with Wilson 95% intervals.
- False-yes rate = among logged yes (30), share the primary judge says no. Also report yes-or-partly strict variant (judge no) and the
  looser "judge != yes". Cross-check with falcon3; headline figure = rows where BOTH judges say no, with gemma-only as upper bound.
- Share of the 46 line closures (resolved yes with closure_how=ok) that were false: computed on ALL logged resolved yes rows with closure_how=ok
  (not only sampled) by running the primary judge on them, plus the sampled subset.
- Hand-check 20 rows blind (by me, before looking at either judge verdict): 10 logged-yes, 10 other, fixed by seed 3795.
- If headline false-yes rate >= 30%: record a finding and spawn a build job proposing a stricter settle. No code changes here.
- Honest confidence: judges are small models; the finding is at most 'inferred' unless hand-check agrees with judges.
