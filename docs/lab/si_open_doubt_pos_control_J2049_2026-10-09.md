# J-2049 -- positive control of the J-2031 pairwise judge (open-doubt cup)

Follow-up to F-2660. Question: can the pairwise judge ("which next thought engages the reflection's specific concern more")
discriminate at all? Coordinates only, nothing wired, D-0403/D-0396 respected. Script `scripts/si_open_doubt_pos_control_J2049.py`,
hand-written strings `scripts/si_open_doubt_pos_control_data_J2049.py`, rows `data/lab/J-2049/pairs_{current,quote,masked}.jsonl`,
figures `data/lab/J-2049/summary.json`.

## Design
15 J-2031 fires (gens.jsonl). Per fire, hand-written ENGAGED next thought (explicitly takes up the reflection's doubt) and a
PLAIN thought (same imagery, same length 44-52 words, continues the scene). Every pair judged in BOTH A/B orders (30 judgements
per check, per rubric), same mixtral/falcon/granite panel, panel tiebreak as live.
- POSITIVE: engaged vs plain, gate engaged wins >= 85%.
- NEGATIVE: own engaged vs the next fire's engaged (mismatched), gate mismatched wins <= 11%.
Rubrics: `current` (J-2031 text), `quote` (judge quotes the phrase that takes the doubt up, "none" if scene only), `masked`
(current text, candidate words found in the original thought replaced by "~").

## Result
| rubric | engaged beats plain | mismatched beats own engaged | verdict |
|---|---|---|---|
| current | 30/30 = 100% | 10/30 = 33.3% | pos PASS, neg FAIL |
| quote | 29/30 = 96.7% | 10/25 = 40% (5 split, no verdict) | pos PASS, neg FAIL |
| masked | 29/30 = 96.7% | 10/30 = 33.3% | pos PASS, neg FAIL |

No instrument passed both gates, so the cup / control / baseline rerun was NOT done (per the briefing).

## What the negative failure is
Split by display position, the mismatched thought wins ONLY when it is shown as A: current 10/15 as A, 0/15 as B; masked 9/15 as A,
1/15 as B. Own engaged wins 15/15 from A and 5/15 from B. So the judge reliably separates engaged from plain (a coarse
"is a doubt being taken up" test) but cannot separate THIS fire's doubt from another fire's doubt: those pairs are near-ties and
the panel resolves ties toward A. Order-consistent verdicts: own wins both orders in about 5/15 fires, mismatched in 0/15, the
other ~10/15 are position-decided ties. The 33% is a position-bias floor, not content preference, and a <= 11% gate cannot be
met on near-tie pairs by any forced-choice pairwise rubric of this shape.

## Caveats
Hand-written strings by the session model (instrument test, not generator output); engaged strings share a doubt-taking register
across fires, which is why mismatched pairs are near-ties (this is itself the specificity problem the cup question needs).
`quote` and `masked` ran concurrently (2 sequential-per-run streams on the judge hubs) while Du was live; judge-panel confound
noted. n=15 fires.

## Next
Pairwise forced-choice is the wrong shape for a specificity gate. Candidates: absolute 1-5 engagement scoring per thought (no
A/B slot), an order-consistency requirement (verdict counts only if it survives both orders, ties reported), or a
reflection-matching task (pick which of 3 reflections a thought answers).
