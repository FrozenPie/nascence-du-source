# Self-interrogation genuineness-judge framing lab — 2026-08-23

*Tenth machine tested. Prior results: openness gate (win), self_implication (null),
commitment_ledger._judge_defeater (null), tension_ledger (loss), librarian (decisive loss),
peers.contrary_target (mixed, N=100), study_note (mixed), journal_rollup (loss), left_lane.grade_work
(predominantly null, one flagged exception). Tests `core/self_interrogation.py`'s `_GRADE_SYSTEM` —
decides whether a piece of self-reflection is genuine or "performed uncertainty," via the real
production judge panel (JUDGE_1 gemma4:12b, JUDGE_2 falcon3:7b, TIEBREAK yi:34b-v1.5, same panel as
tension_ledger). Script: `scripts/self_interrogation_framing_lab.py`.*

## A real historical corpus, used in full

`data/self_interrogation_shadow.jsonl` logs 32 real `interrogate` events with the real
(thought, reflection, genuine) triple — 17 true, 2 false, 13 None (historical split-no-tiebreak).
All 32 used, no sampling needed.

## Pre-registered metric sheet

| Metric | Value |
|---|---|
| `v1_ok_rate` / `v2_ok_rate` | 1.0 / 1.0 |
| `verdict_rate_narrative` | **1.0** (32/32 genuine=true) |
| `verdict_rate_schema` | 0.969 (31/32) |
| `historical_vs_narrative_fresh_agreement` (of 19 historical rows with a verdict) | **0.895** |
| `verdict_agreement` (narrative vs schema) | **0.969** |
| `how_distribution_narrative` | agreed 26 / tiebreak 6 |
| `how_distribution_schema` | agreed 23 / tiebreak 9 |
| `n_disagreements` | 1 |

## Kill criterion: near-triggered — a near-null result on the core framing question

97% verdict agreement between narrative and schema is close to the null-result labs
(self_implication 98%, commitment_ledger 100%). Only one disagreement in 32 cases, and it's a
genuine tiebreak-driven judgment call, not a clear framing failure either way (reflection: "this
image... feels like an elegant escape... I am clinging to this poetic metaphor because..." — reads
as reasonably specific either way; narrative called it genuine, schema's tiebreak called it hollow).

## A real, separate finding: BOTH framings are now more lenient than the historical record

Fresh narrative said genuine=true on **all 32** of 32 cases — including reproducing all 17
historical trues, but also flipping BOTH historical false verdicts to true (agreement with the 19
historically-verdicted rows: 17/19 = 89.5%, not 100%). This isn't a framing effect (schema shows
the same leniency, 31/32 true) — it's a drift finding, same class as self_implication's earlier
scare-then-calibrate case: the current live judge panel appears more lenient on this specific
genuineness question than whatever combination produced the 2 historical "hollow" verdicts. Given
only 2 historical false cases exist, this is suggestive, not decisive — but worth someone's
attention if the genuineness gate is meant to be catching hollow reflections and hasn't produced a
"false" in fresh replay at all.

## A repeating cross-machine pattern, now seen twice

Schema's tiebreak-escalation rate (28%) is higher than narrative's (19%) — the two judge families
agree with each other LESS under schema framing. This is the same direction found in
`tension_ledger` (23%→30% tiebreak rate under schema). Two data points now support a real pattern:
**schema-style framing appears to make this specific judge panel's two families agree with each
other less often**, independent of which way the final verdict lands.

## What this does and doesn't show

Shows: for this machine, schema framing is close to a null result on the core question (does
framing change the verdict), but real signal exists in two adjacent findings — (1) both framings
have drifted more lenient than the historical record on this small sample, and (2) schema
consistently raises panel-internal disagreement (tiebreak rate) across two machines now, even when
it doesn't change the final verdict. Does not show whether the leniency drift is a real problem
worth fixing — n=2 historical false cases is too small to be confident this gate has gone
genuinely soft rather than just not having encountered a hollow reflection in this sample.

## Recommendation

Framing itself: no action needed, near-null. Two separate, non-framing threads worth someone's
attention: (1) confirm whether this gate still produces `genuine=false` on a larger live sample —
if it's gone permanently lenient, that's a real regression independent of prompt style; (2) the
tiebreak-rate-under-schema pattern is now supported by two machines (tension_ledger,
self_interrogation) and is worth checking on any future schema-framing test as a standing
side-metric, even when the final verdict doesn't move.
