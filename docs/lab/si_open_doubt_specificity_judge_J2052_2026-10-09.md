# J-2052 - position-free specificity judge for the SI open-doubt cup (2026-10-09)

Follow-up to F-2664 (J-2049): the pairwise A/B judge passed the positive control but failed the mismatched control as a position-bias floor. Script: `scripts/si_open_doubt_specificity_judge_J2052.py`. Raw rows: `data/lab/J-2052/{abs,match}.jsonl`, figures `summary.json`. Controls: J-2049 hand-written engaged/plain strings (15 J-2031 fires). Nothing wired; coordinates only; D-0403/D-0396 hold unchanged. The cup arms were NOT rerun in this job.

Pre-registered gates (in the script header, before any data): engaged >= 85 percent AND mismatched/own-confusion <= 11 percent.

## Candidate 1 - absolute 1-5 score (no A/B slot)
One thought + the reflection, score 1-5. Judges mixtral (:11438) and falcon (:11440), queried one at a time. Panel "engaged" = both judges >= 4.

| thought | engaged (both >= 4) | mean mixtral / falcon |
|---|---|---|
| own engaged | 15/15 (100%, Wilson 79.6-100) | 4.47 / 4.93 |
| plain | 0/15 (0%, upper 20.4) | 1.93 / 2.40 |
| mismatched (next fire's engaged) | 0/15 (0%, upper 20.4) | 2.60 / 2.53 |

Paired: own > plain 15/15; mismatched >= own 0/15. Gate: PASS both on point estimates. n=15 means the CI cannot formally exclude 11-20 percent for the mismatched arm.

## Candidate 3 - reflection matching (thought + 3 reflections, own placed at each position)
Panel pick = both judges agree. 15 fires x 3 own positions x {engaged, plain} = 90 items.

| thought | picks own | picks a wrong reflection | no panel verdict |
|---|---|---|---|
| engaged | 44/45 (97.8%, Wilson 88.4-99.6) | 0/45 (upper CI ~7.9) | 1 |
| plain | 25/45 (55.6%) | 5/45 | 15 |

Position balance (engaged, own at position 1/2/3): 15/15, 15/15, 14/15; judge pick distributions flat (mixtral 16/15/14, falcon 15/15/15). No position floor. Gate: PASS both, and the CI lower bound clears 85 percent.

Caveat: plain thoughts (same scene vocabulary, no doubt taken up) still land on the own reflection 55.6 percent of the time (chance 33 percent), so matching partly rides shared vocabulary; the absolute score separates plain cleanly (0/15) and is the stricter specificity check.

## Candidate 2 - order-consistency
Not run: it is a patch on the pairwise judge, whose failure was positional; candidates 1 and 3 remove the slot outright.

## Verdict
Two position-free instruments pass the positive and mismatched gates on the hand-written controls. The absolute score is the cleaner discriminator; matching is the better-powered on the mismatched arm. Recommended cup-replay instrument: absolute score (engaged = both judges >= 4) with the matching task as a cross-check.

## Confounds
Strings written by the session model (the control is a hand-written ceiling, not a generated-thought test); n=15 fires; Du live and sharing judge hubs (calls sequential, 2 s pause); the mismatched thought is a different fire's engaged text, which tests specificity to the reflection but shares the style; judge thresholds (>= 4, both judges) were fixed before data but the rubric text was not tuned afterwards. lab_env.isolate redirected the DB to a lab dir under data/_lab/.
