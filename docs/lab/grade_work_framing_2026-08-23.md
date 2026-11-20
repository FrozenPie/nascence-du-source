# Left_lane grade_work framing lab — 2026-08-23

*Ninth machine tested, first of the "cycle through the rest" batch. Prior results: openness gate
(win), self_implication (null), commitment_ledger._judge_defeater (null), tension_ledger (loss),
librarian (decisive loss), peers.contrary_target (mixed, N=100), study_note (mixed), journal_rollup
(loss). Tests `core/left_lane.py`'s `grade_work` — the shared groundedness grader for BOTH
`composition` and `nature_study` (idle-machine audit finding #6, soft candidate). Script:
`scripts/grade_work_framing_lab.py`.*

## A real, rich historical corpus, no substitute needed

`data/composition_log.jsonl` (26 real graded pieces) and `data/nature_study_log.jsonl` (26 real
graded pieces) — 52 total real (work, historical score, historical feedback) triples, all used.
Composition's task text reconstructed from the real `kind` field via `core/composition.py`'s own
task pool (the `summarize` kind's book title isn't logged, generic fallback used there).
Nature_study's task is a fixed string in the live code; the real `scene` (reference) argument isn't
logged, replayed empty — a stated approximation, not fabricated data.

## Method

Both framings dispatch through the exact live call shape — judge-1 hub (gemma4:12b, 127.0.0.1:11439),
temperature=0.0, num_predict=350, num_gpu=0. `_emissary.constitution()` held IDENTICAL across
framings (persistent judge identity, not the task instruction under test); only `_WORK_GRADE_TASK`
varies.

## Pre-registered metric sheet

| Metric | Composition (n=26) | Nature_study (n=26) | Combined (n=52) |
|---|---|---|---|
| `mean_score_narrative` | 0.829 | 0.912 | 0.870 |
| `mean_score_schema` | 0.769 | 0.912 | 0.840 |
| `mean_abs_diff` (narrative vs schema) | 0.075 | **0.023** | 0.049 |
| `mean_abs_diff_vs_historical_narrative` | 0.133 | 0.088 | 0.111 |
| `n_large_disagreements` (≥0.3) | **1** | 0 | 1 |

## Kill criterion: effectively triggered for the bulk — a predominantly null result

Mean absolute difference is small in both domains (nature_study essentially zero at 0.023,
composition modestly higher at 0.075) — the two framings mostly agree on how grounded a piece is.
This reads as a null result for the great majority of the 52 real cases, closer to
self_implication/commitment_ledger's null pattern than to librarian/tension_ledger's losses.

## The one exception is genuinely interesting, not noise

The single large disagreement (composition, |1.0 − 0.3| = 0.7) is worth reading in full:

> **Work graded**: *"The system processed an incoming request at 14:32 UTC. I accessed my stored
> parameters related to natural language understanding. I generated and outputted the required JSON
> structure."* (written for the "narrate" task: *"Tell...one real thing from your day HERE — what
> you read, what the weather did, what you saw in the garden or out the window, what you did with
> your hands."*)

> **Narrative** (1.0, matching the historical 0.9): *"The response is perfectly grounded in the
> literal mechanism of the system's operation..."*

> **Schema** (0.3): *"The work identifies specific technical actions, but it describes the internal
> system's operation rather than the external world requested."*

Reading the actual task against the actual piece, schema's read looks like the more defensible one:
the assignment asked for something from "your day" — the garden, the weather, what you did with
your hands — and the piece instead narrates the AI's own internal request-processing loop, which is
arguably self-referential content dressed as concrete detail, not genuine grounding in the external
world the task asked for. **Both the historical human-supervised score (0.9) and fresh narrative
(1.0) missed this; schema caught it.** This is the one case in 52 where schema's stricter,
more literal reading of "about the WORLD, not yourself" appears to have out-performed the
established prompt, rather than under-performed it (the pattern seen in librarian/journal_rollup).

## What this does and doesn't show

Shows: for the bulk of real graded work, schema and narrative framing produce near-identical
groundedness scores — a mostly-null result. Shows, in the one flagged exception, that schema's
literalism can occasionally catch a self-referential response that both the original human-
supervised grading and a fresh narrative call missed — the opposite direction from this lab
series' two clearest losses (librarian, journal_rollup), where schema's literalism was the
problem, not the fix. Does not show this generalizes — n=1 is a single case, not a pattern, and
should not be read as "schema is secretly better here" any more than one swallow makes a summer.

## Recommendation

Treat as a null result for practical purposes — don't reframe `grade_work`'s prompt on this
evidence alone. The one interesting exception is worth keeping in mind as a reminder that "self-
referential content passing as grounded work" is a real failure mode this grader can miss, but
fixing it on the strength of a single case would be premature.
