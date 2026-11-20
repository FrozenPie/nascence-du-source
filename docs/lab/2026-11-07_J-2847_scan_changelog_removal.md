# J-2847: can the change-log text leave the commitment scan prompt with zero change in detection? (2026-11-07, Du down)

Plan: capacity_to_commit. Follows F-0040 (P-0038 prompt text) and the pre-reset J-2653 harness. LAB ONLY: `core/commitment_ledger.py`
is not edited, and the question of a production edit stays with the founder (D-0527 ruled that the modal wording of `_SCAN_SYS` stays as is;
this job touches neither the modal verb nor any rule, only a parenthetical change-log note and the position of the done_when fragment).
Script: `scripts/lab_commitment_changelog_removal.py` (reuses the J-2597 and J-2630 harnesses). Cases: `docs/lab/J-2847_data/prep.json`.

## Question
Two edits to the scan system prompt, made together as variant (b):
1. Delete the change-log parenthetical after "its LOAD": " (W2.0, 2026-07-03; negative-example set broadened 2026-09-02 per F-0055/F-0677 -- the
   original single example didn't generalize, letting a run of short physical-task statements slip through as load-bearing)".
2. Move the done_when request (`core/done_when.py scan_fragment()`, appended after the "Output ONLY" line today) to just BEFORE the "Output ONLY" line.

## Pre-registered rule (written and committed before any variant (b) call)
Arms, all fresh in one window on the same seat (qwen3.5:9b, hot lane :11433, temperature 0.0, think false, format json, num_predict 400):
- (a) production prompt: `_SCAN_SYS + _dw_scan_fragment()` (DONE_WHEN_AT_OPEN is True in this tree).
- (b) variant as above.
- (a2) a repeat of (a) on 10 formation and 5 dissolve cases (determinism guard).

Cases: the 75 J-2630 formation cases (arm O, original thought, empty active list) and the 30 J-2597 dissolve cases (arm O; 10 each of A_want, A_must, B_want).
Total 150 + 60 + 15 = 225 calls.

- **P1 (formation).** would_form (new commitment, on-topic, and `_stand_rejection` is None) is identical between (a) and (b) on **>= 73 of 75** cases.
- **P2 (dissolve).** The pair (target dissolved yes/no, kind) is identical between (a) and (b) on **>= 28 of 30** cases.
- **Validity guard.** (a2) must reproduce (a) on at least 9/10 formation would_form and 4/5 dissolve pairs; otherwise the verdict is INCONCLUSIVE
  (the prompt is noisy at the size of the tolerance).
- PASS = P1 and P2 and the guard. FAIL = P1 or P2 misses under a valid guard.

Secondary readouts, not pass/fail: would_form counts per arm, the stratum of every flip, statement identity, load_bearing agreement when both form,
whether done_when is still produced in new_commitment, and agreement of fresh (a) with the stored J-2630/J-2597 production rows (seat drift).

Verdict only: no production edit is made or proposed here.

## Result (225 pre-registered calls plus 210 exploratory, 0 unparsed, Du down throughout, 0 writes under C:\Nascence, canary identical)

**VERDICT: FAIL.** Both prongs miss by a wide margin. Detection is NOT unchanged by the two edits.

| check | result | bar |
|---|---|---|
| P1 identical would_form, 75 formation cases | **66/75** | >= 73 |
| P2 identical (dissolved?, kind), 30 dissolve cases | **21/30** | >= 28 |
| validity: production repeat (a2) vs (a) | form 10/10, dissolve 5/5 | >= 9/10 and >= 4/5 (OK) |

The guard is OK, so this is a real wording effect and not run-to-run noise: the production prompt repeats exactly at temperature 0.0.

Formation under (a) vs (b): would_form 36 -> 31. Nine flips: seven formed under (a) and not under (b) (OBS_want 2, FORM_want 3, FORM_must 2), two the other way
(OBS_want 1, OBS_must 1). A new commitment of any kind was proposed on the same cases 65/75; load_bearing agreed 38/40 when both formed.
Dissolve: total dissolves 12 vs 12, but nine cases flip (three yes->no, three no->yes, three defeater<->reflexive kind changes), so the equal total hides churn.

### Exploratory decomposition (added after the verdict; not pre-registered, so read as direction only)
Each edit alone, same cases and seat, same comparison against fresh (a):

| arm | edit | would_form (a=36) | identical would_form | identical dissolve | new commitments proposed (a=48) |
|---|---|---|---|---|---|
| b1 | change-log text removed only | 41 | 64/75 | 22/30 | 59 |
| b2 | done_when fragment moved before "Output ONLY" only | 25 | 62/75 | 21/30 | 37 |
| b  | both | 31 | 66/75 | 21/30 | 42 |

So the two edits push in opposite directions and partly cancel in the total: deleting the change-log text makes the scan LOOSER (+5 formed, mostly on
must-voiced cases), moving the done_when request makes it STRICTER (-11 formed: 13 flips, 12 of them formed -> not formed, and 9 of those 12 in the FORM strata, which are stands that really formed and were kept).
Each alone moves about as many cases as the pair. Wording of any kind moves this scan, as F-3389, F-3406 and F-3420 already showed.

### Side findings
- done_when is not being produced in either position. Among cases where a new commitment was proposed, `done_when` was non-empty in 0/48 (production),
  1/42 (b), 0/59 (b1) and 0/37 (b2). The fragment is dead weight on this seat wherever it sits, which agrees with the earlier "1 usable row in 40 formed stands" count.
  So there is no benefit to weigh against the detection cost of moving it.
- Seat drift check: fresh production vs the stored J-2630 arm-O production rows: same would_form on 72/75 (33 formed then, 36 now). The earlier rows were
  written before this window and the harness may have run with a different done_when state (inferred, not checked), so treat reuse of old baselines with care.

### What this does and does not say
- It says: removing the change-log text and folding the done_when line is NOT a free edit on qwen3.5:9b at temperature 0.0.
- It does not say the change-log text is useful to the model (it is a note to readers, not a rule). Edit b1 shows the model reads it anyway.
- Next step if the founder still wants the change-log note out of the live string: either accept and re-baseline the detection numbers (the formation rate
  moves +5 on these 75 cases, an unknown amount live), or keep the text in a code comment above `_SCAN_SYS` and not in the string sent to the model.
  The second option changes the sent prompt in exactly the same way, so it needs the same replay and the same ruling; there is no wording-neutral way to
  take the text out of the string. The registry row P-0038 should stay as is; no production edit was made.

Data: `docs/lab/J-2847_data/` (prep.json, results.jsonl with all arms a/a2/b/b1/b2, prompt_a.txt and prompt_b.txt as sent, score files).
