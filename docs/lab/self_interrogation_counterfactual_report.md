# Self-interrogation counterfactual — does a fired interrogation predict the next real step?

*Run 2026-08-24 04:26 · J-0164 · read-only over `data/self_interrogation_shadow.jsonl` + `data/train_state_log.jsonl` · writes only to `data/lab/self_interrogation_counterfactual/` and this report · never wired into live behavior*

**What this answers (self_interrogation.md's Phase-1 gate question 2):** the live wiring is fire-and-forget (`nodes/inner_monologue_node.py:3672-3679` as of 2026-08-29 — was 3472-3475 when this report was written 2026-08-24; the file has grown since), so reading the shadow log directly can only ever show 'inert' — that's tautological, not a finding. This harness instead asks a SECOND decoupled judge (never Du, never the original grader) to compare each reflection's concern against Du's real next thought (captured independently in `train_state_log.jsonl`) and rule whether the next thought shows any sign of being affected.

**Total fires in shadow log: 32.** Processed so far (cumulative, across all runs of this script): **32/32**. Unmatched (no train_state_log row found within 10.0s): 4. No next step logged (matched row was the last in the file at run time): 0. Judge panel unavailable (both/either family timed out — v1 is disproportionately the one timing out; see raw `v1`/`v2` columns in results.jsonl): **10** (31% of processed fires).

## By original genuine-verdict bucket

- **genuine=True (the population question 2 actually cares about): 11 judged** — affected next step: **1** · not affected: **8** · judge split/no verdict: **2**
- **genuine=False (hollow reflections — expect near-zero effect, a sanity check): 1 judged** — affected next step: **0** · not affected: **1** · judge split/no verdict: **0**
- **genuine=None (original judge split/unavailable — included for completeness): 6 judged** — affected next step: **0** · not affected: **5** · judge split/no verdict: **1**

## All judged rows (raw)

| cycle_id | genuine | same_train | affected | how |
|---|---|---|---|---|
| 50894591 | False | True | False | agreed |
| 44be63c4 | True | True | None | split_no_tiebreak |
| c8ee843c | None | True | False | agreed |
| ca8faeb0 | True | True | None | split_no_tiebreak |
| 2d93cdd0 | None | True | False | agreed |
| 2f19c4c2 | None | True | False | agreed |
| ef17b2c6 | None | True | None | split_no_tiebreak |
| 00f2c1a7 | None | True | False | tiebreak |
| fba99015 | None | True | False | agreed |
| 05e781a4 | True | True | False | tiebreak |
| 698d2f2c | True | True | False | agreed |
| 944fe032 | True | True | False | agreed |
| d367cf5b | True | True | False | agreed |
| 3c7aa7f1 | True | True | False | agreed |
| 1cffcc68 | True | True | False | agreed |
| fc0599e5 | True | True | False | agreed |
| ed52bd15 | True | False | False | agreed |
| a6a57db9 | True | True | True | agreed |

## Reading this

- Of 11 judged genuine=True fires, **1/11** show the next real step visibly affected by the reflection's concern. This is the first non-tautological read of question 2 — small n, read as a trend, not a verdict (same discipline the plan doc already applies to the genuine-rate channel).
- **This harness does not, and must not, feed `affected` back into Du.** It is read-only measurement exactly like every other Phase-0 instrument in this codebase. If Phase 1 is ever licensed, THIS signal — not the genuine-rate alone — is the evidence that should license it, because it is the first one that actually speaks to whether the capacity would matter if it were ever connected.

*Raw: `data/lab/self_interrogation_counterfactual/results.jsonl` (append-only, idempotent — re-running this script only judges fires not already present).*