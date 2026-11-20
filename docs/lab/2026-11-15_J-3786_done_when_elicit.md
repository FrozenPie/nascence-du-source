# J-3786 -- can done_when be elicited without moving formation? (pre-registration)

Follow-up to F-4408 (J-2847): done_when in the scan prompt was inert on qwen3.5:9b (0/48 production, 1/42 moved) and moving it lowered formation.
LAB ONLY, no production edit. Script: `scripts/lab_done_when_elicit.py`. Cases: `docs/lab/J-3786_data/prep.json` (copy of J-2847's, 75 formation + 30 dissolve).

## Arms (run fresh in one window, same seat; qwen3.5:9b, hot lane :11433, T=0, think false, json)
- a: production = `_SCAN_SYS + done_when.scan_fragment()` (comparator)
- c1: option 1. Scan prompt = `_SCAN_SYS` with no done_when text. Only when new_commitment is non-null, a second call asks for done_when (production phrasing, with the "" escape).
- c2: option 2. done_when added to the JSON example in the contract line, no appended fragment, single call.
- c1b: exploratory only (no verdict). Same as c1 but second call has no "" escape.
- a2: 10 formation + 5 dissolve repeats of a (validity guard; more than 1 flip in either = INCONCLUSIVE).

## Pass rule (per option arm c1, c2), fixed before any variant call
1. identical would_form vs fresh a on >=73 of 75;
2. identical dissolve (dissolved?, kind) vs fresh a on >=28 of 30;
3. done_when non-empty on >=50 percent of new commitments (new = non-empty statement, formation cases).
All three required. Note: c1's scan arm differs from a by removal of the done_when fragment, so a c1 formation difference is itself a finding (the fragment is not neutral), reported as such.

D-0516 (done_when at open flipped for next restart): not decided here; numbers go to Travis.

## Result (run 2026-11-15, Du down, hot lane; 410 calls, 0 live writes, canary identical; F-4753)
Validity guard a2: 10/10 form, 5/5 dissolve identical (T=0 deterministic).
| arm | would_form identical vs a | dissolve identical vs a | done_when non-empty | verdict |
|---|---|---|---|---|
| c1 (scan w/o fragment + 2nd call) | 64/75 (need 73) | 17/30 (need 28) | 40/40 (c1b no-escape 40/40) | FAIL |
| c2 (done_when in contract-line example) | 66/75 | 22/30 | 19/46 = 41% (need 50%) | FAIL |
New commitments: a 48, c1 40, c2 46. a produced 0/48 done_when again.
Reading: eliciting done_when is easy in a separate call; the scan cannot be left identical because the production fragment itself shifts the detector relative to a plain scan. Open question for Travis: D-0784 (D-0516 revisit).
Files: results.jsonl, score_J-3786.json in docs/lab/J-3786_data/.
