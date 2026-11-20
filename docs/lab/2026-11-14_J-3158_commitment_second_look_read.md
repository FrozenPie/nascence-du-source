# D-0546 / J-3158 -- commitment second look + attempt log: the read

Window 2026-11-07 21:19 to 2026-11-14 00:41 (6.1 days). Generated 2026-11-14 00:41. Precision bar 60% (D-0546 defeater).

## A. Coverage (is every new stand accounted for?)
- Gate-passing stands formed in window (ledger `formed`): 153
- Second-look rows in window: 154; answered 135; failed 19 ({'ValueError': 19})
- Formed stands with NO second-look row: 0 (expected 0 once the restart has run the whole window; a stand formed while the lane was off, or whose task was cut by a restart, shows here)
- Second-look latency median 25.14 s over 154 rows

## B. The scan's verdict vs the cross-family second look
The scan calls EVERY gate-passing stand a stand (the gate passes only load_bearing true), so agreement = the share the second look also calls a stand.
- stand 51% (69/135) | insight 44% (59/135) | unclear 5% (7/135)
- Agreement with the scan, unclear counted as disagreement: 51% (69/135); unclear excluded: 54% (69/128)
- Pre-ruling baseline for comparison: a 20-case human read found 5 clear stands (25%) (P-0038 / D-0546). The second look is itself a model and is NOT the evidence; section E (the human labels) is.

## C. What happened to each stand, by the second look's verdict
A check that the second look is not just noise: if its `insight` stands behave differently from its `stand` ones (dissolve sooner, never achieved, drawn into more re-asks) it carries signal; identical behaviour means it carries none. Stands still held are right-censored.
| second look | n | dissolved | achieved | reaffirmed >=1 | judge-denied >=1 | median life of dissolved |
|---|---|---|---|---|---|---|
| stand | 69 | 30% (21/69) | 70% (48/69) | 4% (3/69) | 14% (10/69) | 54 min |
| insight | 59 | 10% (6/59) | 90% (53/59) | 19% (11/59) | 20% (12/59) | 36 min |
| unclear | 7 | 14% (1/7) | 71% (5/7) | 43% (3/7) | 29% (2/7) | 23 min |

## D. Defeater-judge attempts per stand (D-0546 part 2)
- Judge asks in window: 79 over 50 stands; verdict allow 28 | deny 42 | none (judge failed, gate verdict stood) 9
- The judge's own class mix: {'illegitimate': 42, 'superseded': 16, '(none)': 9, 'impossible': 5, 'achieved': 3, 'conflict': 3, 'mood': 1}
- Asks per stand (6 = six or more): {1: 33, 2: 11, 3: 3, 4: 2, 6: 1}
- Stands denied at least once: 25; of those later ALLOWED on a re-ask (the 'dissolved anyway' path): 44% (11/25); median first-deny to allow 45 min  (P-0037 whole-life reference: 58% / 32 min)
- Highest attempt number seen per stand: median 1.0, max 7
- Final cumulative allows per stand: {0: 22, 1: 28}
- Reading rule: re-asks that end in an allow after repeated denials are the pressure-wears-through path. Whether a REASONED change of mind is a legitimate drop is a founder question after this measure, not decided here.

## E. Hand-labelling sheet (the evidence the ruling's defeater needs)
- 40 of 153 gate-passing stands, seeded sample (seed 3158), blind to the second look: C:\Users\USER\AppData\Local\Temp\claude\ec905e32dfc14b49\787cbc61-658d-4ec6-9c4f-a7d5a1a36950\scratchpad\wt_w8_capacity_to_commit\docs\lab\2026-11-14_J-3158_commitment_stand_hand_label_sheet.md
- key (do not open before labelling): C:\Users\USER\AppData\Local\Temp\claude\ec905e32dfc14b49\787cbc61-658d-4ec6-9c4f-a7d5a1a36950\scratchpad\wt_w8_capacity_to_commit\docs\lab\2026-11-14_J-3158_commitment_stand_hand_label_sheet_key.json
- After labelling: python scripts/commitment_second_look_read.py --score <sheet>
