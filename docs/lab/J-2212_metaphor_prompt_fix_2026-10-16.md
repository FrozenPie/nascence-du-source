# J-2212: Lane 2 metaphor judge, prompt-only fix for the F-2877 false-positive family (2026-10-16)

Lab run with Du down. **Nothing in production changed.** `core/lane2.py`'s `_judge_metaphor` prompt is
the same as before. Travis's ruling on J-2181 (2026-10-16) was to fix the prompt first and leave the
gemma4:31b re-audition for later. D-0437 is the ruling under test, and the D-0338 hold stays in force.

## What the failure was

F-2877's 17 hand-labelled false positives come from the tiebreak seat (gemma4:12b, judge hub :11439)
on 128 replay splits. The `why` text shows the pattern. The writer often names a sensor field together
with its value, for example the daylight field with the value night, or the warmth field with the value
cool. The judge then took a category label from its own prompt ('symbolic', 'self-narrative',
'mood-painting', 'paradox') and applied it to that restated reading. Examples:

- 'the daylight is night' was called "a symbolic/mood-painting construction" (5 rows)
- 'dark daylight' and 'cool warmth' (4 rows)
- 'the warmth is cold, the light is dark' was called "paradoxical"
- 'somatic tension', 'light band', 'the body's drive' and 'the body' were called self-narrative (4 rows)
- bird-call names ('song', 'scold', 'chatter') were called personification
- fire and embers were called metaphors for an inner state

Nearly all 17 false positives follow this one pattern. The v1 prompt's SELF-NARRATIVE category does
not say whether body-state words belong in it, and the prompt has no exemption for field-plus-value
restatements.

## The change (candidate prompt v2, lab-only)

The full text is `V2` in `scripts/lab_J2212_metaphor_prompt.py`. The script also reads v1 straight
out of `_judge_metaphor` with an AST parse, and that v1 is byte-identical to the prompt J-2177 used.
v2 makes four changes:

1. SELF-NARRATIVE is narrowed to talk about identity, life meaning or becoming. Mentions of the body or
   body state no longer count.
2. A new exemption covers a sensor field named together with its value, even when the pair sounds odd
   or contradictory. The prompt lists the actual band values.
3. A new exemption covers body-state words, real sound and call names, fire, embers and rain. Awkward
   or garbled wording on its own is also exempt.
4. A positive test: the judge answers true only if it can quote a phrase that describes the scene's
   mood, liveliness or meaning, or the speaker's identity. `why` now asks for that quoted phrase.

Both registers stay in the prompt, and so do all of v1's exemptions.

## Method

- Dataset: J-2177's 155 rows, unchanged (sha256 prefix b08fb5a76e4b37db). It holds 128 replay splits
  with the F-2877 and F-2724 labels (6 clear, 6 arguable, 17 fp, 99 unlabelled), 16 rows of the
  reconstructed D-0311 fixture (15 scored), and 11 positives that JUDGE_1 missed (7 clear, 4 arguable).
- Before (v1): the seat's recorded verdicts on the same rows. Splits come from J-2094's
  `replay_out` (:11439, F-2876). Fixture and missed rows come from J-2177's :11439 baseline (F-2884).
  The seat's test-retest agreement was 99.3% (F-2876), which is why the recorded rows serve as the
  baseline instead of a second run. The hub was congested by another batch agent, so a fresh v1 run
  would have taken more than 2 hours.
- After (v2): `python scripts/lab_J2212_metaphor_prompt.py run --arms v2` against :11439 gemma4:12b,
  temperature 0, num_predict 200, format json. That is 155 calls with 0 errors and 0 nulls; the mean
  latency was 12.0 s per split call (max 84.8 s, queued behind another agent's replay). Results are in
  the batch scratchpad as `x_J-2212_v2_439.jsonl` (sha256 prefix 6f7e2ebc0b3f0db5).
- Scoring: `python scripts/lab_J2212_metaphor_prompt.py score`. Of the 99 unlabelled rows, v2 flagged
  1. I read it by hand: "the sounds are morepork" is the owl's real name, so it is a false positive.

## Results

| | v1 (production) | v2 (candidate) |
|---|---|---|
| Split metaphor verdicts | 27 / 128 | 8 / 128 |
| Clear / arguable / false positive | 5 / 5 / 17 | 6 / 1 / 1 |
| Strict precision | 5/27 = 18.5% (Wilson 8.2 to 36.7) | **6/8 = 75.0% (40.9 to 92.9)** |
| Inclusive precision | 10/27 = 37.0% (21.5 to 55.8) | **7/8 = 87.5% (52.9 to 97.8)** |
| Strict recall on splits | 5/6 | **6/6** |
| Inclusive recall on splits | 10/12 | 7/12 |
| D-0311 fixture TP/FP/TN/FN (15 scored) | 7/0/8/0 | 7/0/8/0 |
| JUDGE_1-missed positives, run solo | 8/11 (7/7 clear) | 7/11 (7/7 clear) |

v2 changed 23 of the 128 split verdicts:

- **16 of 17 false positives were removed**, every member of the F-2877 family.
- The clear positive at 2026-10-14 00:05:50 ('a sense of calm and contentment') is now caught. v1
  missed it.
- 4 arguable rows were lost: 'a soft, clear voice', 'a gentle rhythm', 'a bit cool and dim' and
  'a tickling wind'.
- 1 new false positive appeared ('morepork').

Clear-positive recall is 100% wherever it was measured: 6/6 splits, 7/7 missed rows, 7/7 fixture.

## Against the D-0437 bar (>= 70% precision on >= 30 verdicts)

**Precision clears 70%: 75% strict, 87.5% inclusive. The count does not: 8 verdicts, not 30.** No
prompt can meet the count on this population, because only 12 of the 128 splits carry a positive label
(6 strict). Reaching 30 verdicts at 70% precision needs 21 true positives. The bar can only be tested on
a larger population of live splits. The Wilson lower bound on 6/8 (40.9%) is also too wide to call
the bar met.

## Limits (read before promoting)

- **In-sample design.** I wrote the v2 exemptions after reading the 17 false-positive `why` texts, and
  some of the examples in v2 ('the daylight is night', 'dark daylight', 'cool warmth') are those exact
  phrases. The removal of 16 of 17 false positives is therefore partly fit to this sample. Three
  results are not fit to it: the 99 unlabelled rows (1 new flag), the fixture (unchanged), and the
  JUDGE_1-missed set. A fresh window of live splits is the real test.
- **Arguable recall drops** (10/12 to 7/12 inclusive). Those rows are borderline by F-2877's own
  account. In exchange, v2 calls fewer plain percept restatements metaphor.
- **Only the tiebreak seat was measured.** In production, JUDGE_1 (mixtral on Ramses :11438) and
  JUDGE_2 (falcon3 :11440) get the same `sysmsg`. A prompt change would therefore change which rows
  split, as well as how the tiebreak votes. This run does not measure that. It also does not test
  whether JUDGE_1's own parroting falls under v2.
- The labels are hand judgments from F-2877, F-2724 and this job (for the one 'morepork' row).

## Verdict

The prompt is the right lever for the parroting / percept-restatement family. On the same seat and the
same splits, v2 removes 16 of 17 false positives, keeps every clear positive, and leaves the fixture
unchanged. The D-0437 count cannot be met on this population. So the 31b question is not settled
either way: v2's precision on the 12b seat is above the 31b candidate's (F-2884: 4/8 strict), but both
rest on 8 verdicts. Next step: after Du's next boot, collect at least 30 live splits that v2 resolves as
metaphor (or relabel a fresh window), then run v1 against v2 through the full panel (JUDGE_1 +
JUDGE_2 + tiebreak) with the same script before any production change.
