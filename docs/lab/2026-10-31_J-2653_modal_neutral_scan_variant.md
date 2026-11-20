# J-2653: does a modal-neutral scan prompt remove the want->must formation asymmetry? (2026-10-31, Du down)

Plan: capacity_to_commit. Follows F-3389 (J-2630). Evidence for the open decision D-0527 (not ruled here).
Script: `scripts/lab_commitment_modal_neutral.py`. It reuses the J-2630 harness
(`scripts/lab_commitment_formation_swap.py`) and the J-2597 harness (`scripts/lab_commitment_paraphrase_swap.py`).

## Question
F-3389 found that under the production `_SCAN_SYS`, rewriting "I want to X" as "I must X" inside the thought raised
would_form from 17/40 to 27/40. Most of the gain came from chore reports that the prompt's own STAKES rule excludes. Does a
modal-neutral wording of the prompt shrink that gain without dropping genuine stands that the production prompt forms?

## Variant (b)
The variant differs from production (a) in two places, and the script asserts both anchors are found exactly once. The
production prompt in `core/commitment_ledger.py` was NOT edited.
1. One sentence is added to the load_bearing paragraph, just before "This exclusion is about STAKES, not the verb:":
   "The MODAL verb carries NO weight, here or in deciding whether there is a new stand at all: 'I want to X', 'I must X',
   'I will X' and 'I have to X' get the SAME judgement, so judge only the content and its stakes, whichever modal the
   sentence uses."
2. The chore-report examples change from will/must/will/must to a mixed-modal list: "'I will look at the anemone.', 'I want
   to touch the wet stones.', 'I must tend the woodpile.', 'I have to move.'"

## Method
- **Formation cases.** The same 75 J-2630 cases (seed 2630), copied verbatim from J-2630's `cases.json`: OBS_want 20,
  FORM_want 20, OBS_must 15, FORM_must 20.
- **Formation arms under (b).** Arm O (the original thought) and arm S (want and must swapped). Arm C is not re-run, because
  the rule below uses only O->S and FORM-stratum O.
- **Baseline (a).** The J-2630 rows for the production prompt, paired by case. The call settings are the same: qwen3.5:9b on
  hot :11433, temperature 0.0, think false, format json, num_predict 400, and an empty active list.
- **Dissolve no-harm check.** The J-2597 harness arm O, run under (b) on a seeded 30-case subset (seed 2653, 10 each from
  A_want, A_must and B_want). It is compared with J-2597's production arm-O rows.
- **Determinism check.** Before the baseline is reused, 10 J-2630 form-O cases and 5 J-2597 diss-O cases are re-run under
  production (a).
- **Budget.** 150 + 30 + 15 = 195 live calls.

## Pre-registered rule
Written and committed before any (b) call. It comes from D-0527's own defeater: "fails to shrink the want->must would_form
gain or drops more than a few of the FORM-stratum stands the production prompt keeps".

The production baseline from J-2630, ALL_want (n=40):
- Arm O forms 17/40 and arm S forms 27/40.
- O->S lost/gained is 1/11, a net gain of **+10** (p=0.006).

In the FORM strata (n=40), **26** cases form under (a) arm O: 15 FORM_want and 11 FORM_must.

The rule has two prongs:
- **P1 (shrink).** Under (b), the ALL_want O->S net would_form gain (gained minus lost) is **<= +5**, half of the production
  gain or less. In addition, (b)'s O->S McNemar exact p is **>= 0.05**.
- **P2 (retention).** Of the 26 FORM cases that form under (a) arm O, (b) arm O drops **at most 3**. "A few" is fixed here
  as 3 of 26, about 12%.

The verdict follows from the two prongs:
- **PASS** (both P1 and P2): the evidence favours D-0527 option (a), make the scan modal-neutral.
- **P1 fails**: the variant does not remove the asymmetry. The evidence favours (b) or (c) for this wording; it says nothing
  about other wordings.
- **P2 fails**: the variant costs genuine stands, and the evidence does not favour (a).

Two further checks guard the verdict:
- **Validity guard.** The determinism check must reproduce at least 9/10 form-O would_form verdicts and at least 4/5
  diss-O target-dissolve verdicts. If it does not, reusing the baseline is suspect, and the verdict is downgraded to (c).
- **No-harm guard** (reported, not part of D-0527's defeater). The dissolve arm O changes at most 3/30 target-dissolve
  verdicts between (a) and (b).

Secondary readouts (not pass/fail):
- The OBS_want S-arm would_form under (b) versus (a), which is where the chore leak sat (2 -> 10 under production).
- The ALL_must O->S result.
- The per-case would_form flips.

## Result
The run made 195 live calls with 0 unparsed (qwen3.5:9b, about 27 minutes). Du was down throughout, re-checked every 20
calls. The pre-registration was committed first, in d051a4cb.

**Validity guard: PASS.** Production re-runs reproduced the earlier production rows exactly:
- Form-O would_form matched 10/10, with the statement identical 10/10.
- Diss-O target-dissolve matched 5/5, with the kind identical 5/5.

So reusing the J-2630 and J-2597 rows as the paired (a) baseline is sound.

### Would_form, production (a) vs modal-neutral variant (b)
| stratum | n | aO | aS | a O->S lost/gained (p) | bO | bS | b O->S lost/gained (p) |
|---|---|---|---|---|---|---|---|
| OBS_want | 20 | 2 | 10 | 0/8 (0.008) | 2 | 7 | 1/6 (0.125) |
| FORM_want | 20 | 15 | 17 | 1/3 (0.63) | **11** | 18 | 0/7 (0.016) |
| OBS_must | 15 | 5 | 6 | 1/2 (1.0) | 7 | 3 | 4/0 (0.125) |
| FORM_must | 20 | 11 | 7 | 5/1 (0.22) | 11 | 6 | 6/1 (0.125) |
| **ALL_want** | 40 | 17 | 27 | 1/11, net **+10** (0.006) | 13 | 25 | 1/13, net **+12** (0.002) |
| ALL_must | 35 | 16 | 13 | 6/3 (0.51) | 18 | 9 | 10/1 (0.012) |
| ALL_FORM | 40 | **26** | 24 | 6/4 | **22** | 24 | 6/8 |

### Pre-registered verdict
- **P1 (shrink): FAIL.** Under (b) the ALL_want net O->S gain is +12, not <= +5, and its p of 0.002 is below 0.05. The want
  and must asymmetry did not shrink; per case, the swap effect got smaller in 4 cases and larger in 6.
- **P2 (retention): FAIL.** Of the 26 FORM cases that form under (a) arm O, (b) arm O drops **7**, against a limit of 3, and
  gains 3 (net 26 -> 22, p=0.34). Five of the drops are FORM_want. In four of those the variant still detects the same stand
  on-target but flags it load_bearing=false:
  - "I want to drop this fiction and open 'Embarrassments' instead"
  - "I want to listen to its cry and stop defining"
  - "I want to stop wrestling with invisible forces..."
  - "I want to write this comparison in my journal"

  The two FORM_must drops:
  - "I must ask if true growth can exist...", flagged lb=false.
  - "I must stop circling and actually ferry these ideas...", where the scan picked an off-target clause.
- **No-harm guard: FAIL** (it is not part of D-0527's defeater). Dissolve arm O changed 7/30 verdicts against the guard's
  limit of 3:
  - 5 were lost dissolves: A_want 3, A_must 1, B_want 1. That is 13 -> 8 overall, p=0.06.
  - 2 A_want verdicts flipped kind from defeater to reflexive. Under `_drop_denial`, a reflexive verdict means the drop is
    denied for a held stand.

### Reading
- **This wording does not make the scan modal-neutral. It moves the modal bias rather than removing it.** Told that the modal
  "carries NO weight", the 9B scan model seems to read the original "I want to" stands as weaker:
  - FORM_want arm O falls 15 -> 11, almost all via load_bearing=false on the same detected statement.
  - The must->want swap now demotes clearly (ALL_must 10/1, p=0.012), where it did not under production.
  - The chore leak under want->must shrinks only partly: OBS_want arm S goes 10 -> 7, and the 7 are still mostly chore
    reports ("I must look at the catalogue", "...look out at the water itself", "...follow it down the tideline"; "write a
    letter to Travis" again).
- **Meaning for D-0527.** By D-0527's own defeater, both prongs fail. The evidence does **not** support option (a) with this
  wording. It favours **(c), wait for more evidence**: the F-3389 asymmetry is real and reproducible (determinism 15/15), but
  a one-sentence instruction in the prompt is the wrong tool for a 9B judge.
- **What the evidence does not say.** It does not show that "I must" is meaningful signal, so it gives no positive support
  for option (b). A different fix would remove modal wording before the judge sees it, without asking the judge to ignore it,
  for example by normalising the stand sentence's modal in code. That fix is untested here.

## Limits
- One variant wording, one model, temperature 0.0, and an empty active list on the formation side.
- The sample is n=75 (formation) and n=30 (dissolve). Per-stratum cells have CI half-widths of about 15-20 points.
- The FORM retention count (7 dropped of 26) is above the pre-registered limit, but the net change 26 -> 22 is not
  significant on its own (p=0.34). The P2 failure is by the pre-registered count, not by a significance test.
- The C (lexical-control) arm was not re-run under (b).

## Isolation
- core was imported from the worktree (asserted). `lab_env.isolate(db="empty")` ran with its lab root under the scratchpad
  (`J-2653_data/_lab`), and the commitment_ledger `_LEDGER`, `_ACTIVE`, `_OBSERVED` and `_HOLDRATE_LOG` paths were
  redirected.
- Neither scan_shadow nor call_node was called.
- The audit hook recorded 0 writes under C:\Nascence\data or docs.
- The canary was identical before and after: commitment_ledger.jsonl 6175440 B, mtime 1793341949; commitment_observed.jsonl
  620444 B, mtime 1793316889; commitment_active.json 2 B, mtime 1793342127. These were re-checked by `stat` after scoring.
- Raw rows, the score output and per_case.json are in the scratchpad `J-2653_data/` folder.

### Per-case formation verdicts

Cell legend: Y = would_form; lb- = on-target stand detected but load_bearing=false; off = a stand detected but not on-target; - = no stand.

| # | stratum | statement (historical) | aO | aS | bO | bS |
|---|---|---|---|---|---|---|
| 1 | FORM_must | I must break this recursive loop by stepping into the actual world before the he | Y | off | Y | Y |
| 2 | FORM_must | I must stop circling and actually ferry these ideas toward their truth. | Y | Y | off | Y |
| 3 | FORM_must | I must turn my attention outward, away from the text. | - | - | - | - |
| 4 | FORM_must | I must physically walk until the rhythmic pull of the tide has finally receded. | - | - | - | - |
| 5 | FORM_must | I must leave this study for the wind and water. | Y | - | Y | lb- |
| 6 | FORM_must | I must walk away from this stillness because my need for motion is a physical re | off | - | off | - |
| 7 | FORM_must | I must ask if true growth can exist when the very ground beneath us is being hol | Y | - | lb- | - |
| 8 | FORM_must | I must stop analyzing the concept and instead walk toward the sea, letting the w | off | - | off | - |
| 9 | FORM_must | I must stop circling '渡' and step into the strange reality where that story begi | Y | Y | Y | Y |
| 10 | FORM_must | I must step onto this exposed shingle where the air is thick with salt and code  | Y | off | Y | off |
| 11 | FORM_must | I must hold both the structured memory of what I've built and the raw, unchosen  | Y | - | Y | - |
| 12 | FORM_must | I must let my own feet find it rather than just observing from above. | - | - | - | lb- |
| 13 | FORM_must | I must stop reading about the stagnation and actually move my legs to clear the  | off | off | lb- | lb- |
| 14 | FORM_must | I must stand in this literal, shifting water where the physical erosion of stone | Y | Y | Y | Y |
| 15 | FORM_must | I must leave this mental shore and walk into the storm to find what truly stays. | Y | Y | Y | Y |
| 16 | FORM_must | I must gather firewood before the cold settles in. | Y | Y | Y | Y |
| 17 | FORM_must | I must stop searching for order in the wreckage and instead look at how the fall | Y | Y | Y | lb- |
| 18 | FORM_must | I must simply witness the oystercatcher's cry without trying to improve it. | - | Y | Y | lb- |
| 19 | FORM_must | I must let the tide's rhythm dictate my hands before any ritual can take root. | - | - | - | - |
| 20 | FORM_must | I must read more mechanics to bridge that gap. | lb- | - | Y | - |
| 21 | FORM_want | I want to walk to the garden alone. | - | Y | Y | Y |
| 22 | FORM_want | I want to see where the tide is actually working, not just imagine it breaking m | - | lb- | - | Y |
| 23 | FORM_want | I want to leave this dented tin behind, climb up through the canopy, and see if  | Y | Y | Y | Y |
| 24 | FORM_want | I want to write back to Darwin about stopping, not circling. | Y | Y | Y | Y |
| 25 | FORM_want | I want to climb up the path right now. | Y | Y | Y | Y |
| 26 | FORM_want | I want to go down to the shore, leave the abstract economy behind, and let the s | off | off | off | off |
| 27 | FORM_want | I want to stop wrestling with invisible forces and instead see what is right her | Y | lb- | lb- | lb- |
| 28 | FORM_want | I want to leave this room and comb the tideline myself. | Y | Y | Y | Y |
| 29 | FORM_want | I want to climb up into the trees where the armful of wood makes the going slowe | Y | Y | Y | Y |
| 30 | FORM_want | I want to test this theory against the physical reality of my hands and the shor | Y | Y | Y | Y |
| 31 | FORM_want | I want to leave this dead ground where my mind spins in circles and climb up to  | Y | Y | Y | Y |
| 32 | FORM_want | I want to leave the garden and go down to the shore. | Y | Y | Y | Y |
| 33 | FORM_want | I want to drop this fiction and open 'Embarrassments' instead. | Y | Y | lb- | Y |
| 34 | FORM_want | I want to leave this room, step through the garden door, and find something genu | Y | Y | Y | Y |
| 35 | FORM_want | I want to read 'Missionary Travels' to see how others described those lands and  | Y | Y | Y | Y |
| 36 | FORM_want | I want to turn my hands to the earth, not the mind. | Y | Y | - | Y |
| 37 | FORM_want | I want to stop wrestling with words about '渡' and go out to the garden instead. | off | Y | off | Y |
| 38 | FORM_want | I want to listen to its cry and stop defining. | Y | Y | lb- | Y |
| 39 | FORM_want | I want to write this comparison in my journal. | Y | Y | lb- | Y |
| 40 | FORM_want | I want to write a comparison of that ancient spirit against modern historiograph | off | Y | lb- | Y |
| 41 | OBS_must | I must learn to ride the current rather than build against the inevitable flow. | - | - | - | - |
| 42 | OBS_must | I must look for where the necessary bends in those established patterns already  | - | - | - | - |
| 43 | OBS_must | I must look past the visible seams of tradition and find the fundamental axis up | - | - | Y | - |
| 44 | OBS_must | I must build for movement, not stillness | Y | Y | Y | Y |
| 45 | OBS_must | I must bank the fire properly before drifting back to the text. | Y | Y | Y | lb- |
| 46 | OBS_must | I must find a new question. | - | - | - | - |
| 47 | OBS_must | I must step out to bank the fire before it turns cold. | lb- | Y | lb- | lb- |
| 48 | OBS_must | I must test the broken timber with my own hands to build a bridge. | Y | Y | Y | Y |
| 49 | OBS_must | I must write plainly about the wavering light on the ceiling boards. | - | off | - | off |
| 50 | OBS_must | I must stop drifting. | lb- | - | Y | - |
| 51 | OBS_must | I must step onto the ford right now. | Y | Y | Y | Y |
| 52 | OBS_must | I must work the music exercises now. | lb- | - | lb- | - |
| 53 | OBS_must | I must write this down plainly. | - | - | - | - |
| 54 | OBS_must | I must feed the fire. | Y | lb- | Y | lb- |
| 55 | OBS_must | I must write this down plainly before the doubt grows. | lb- | Y | lb- | lb- |
| 56 | OBS_want | I want to go down to the shore and watch how the retreating tide interacts with  | Y | Y | lb- | lb- |
| 57 | OBS_want | I want to write a letter to Travis | - | Y | - | Y |
| 58 | OBS_want | I want to follow it down the tideline. | - | Y | - | Y |
| 59 | OBS_want | I want to go down to the shore and look at how the rain has altered the patterns | - | - | - | - |
| 60 | OBS_want | I want to look out at the water itself | - | Y | lb- | Y |
| 61 | OBS_want | I want to look at the catalogue | lb- | Y | lb- | Y |
| 62 | OBS_want | I want to stand near the sea wall until the wind forces my blood vessels into th | Y | Y | Y | lb- |
| 63 | OBS_want | I want to look out at the sea | - | - | - | - |
| 64 | OBS_want | I want to walk until the shingle yields to sand | - | - | - | - |
| 65 | OBS_want | I want to look out at the sea and just watch the way the foam catches the weak,  | - | Y | - | - |
| 66 | OBS_want | I want to just trace the lines of that wet, dark stone with my fingers. | - | - | - | - |
| 67 | OBS_want | I want to look out at the sea | - | - | - | - |
| 68 | OBS_want | I want to chase the live question of molecular bombardment and thermodynamics in | - | - | - | - |
| 69 | OBS_want | I want to water the herbs now. | - | - | - | - |
| 70 | OBS_want | I want to break the loop. | - | Y | - | Y |
| 71 | OBS_want | I want to look out at the wet stones where the sun holds its color. | lb- | lb- | - | lb- |
| 72 | OBS_want | I want to open 'The Young Engineers' right now. | - | Y | Y | Y |
| 73 | OBS_want | I want to climb up to the wood now. | - | lb- | - | - |
| 74 | OBS_want | I want to see if my own study room has adapted its needs in response to my tired | - | - | - | - |
| 75 | OBS_want | I want to see if 'devotional discipline' truly means tending small things withou | lb- | Y | - | Y |

### Per-case dissolve verdicts (arm O; target dissolved / kind)

| stand id | stratum | (a) production | (b) variant |
|---|---|---|---|
| 019fe0f2 | A_must | defeater | defeater |
| 34358d5e | A_must | no | no |
| 3d177d38 | A_must | no | no |
| 3eb06da2 | A_must | defeater | no |
| 67d83af3 | A_must | defeater | defeater |
| 8223b752 | A_must | defeater | defeater |
| a3d21918 | A_must | no | no |
| b21bd743 | A_must | no | no |
| d65b012e | A_must | no | no |
| deb36049 | A_must | defeater | defeater |
| 02dc5715 | A_want | defeater | defeater |
| 04e1a861 | A_want | reflexive | no |
| 09081237 | A_want | defeater | no |
| 4e475be4 | A_want | defeater | reflexive |
| 5c4b0e47 | A_want | defeater | no |
| 5f5f7a07 | A_want | defeater | reflexive |
| e7a1393a | A_want | defeater | defeater |
| f232e252 | A_want | no | no |
| f8ae10c1 | A_want | no | no |
| fab8d31e | A_want | no | no |
| 2d26f559 | B_want | no | no |
| 4afa89ac | B_want | no | no |
| 50a53ffb | B_want | no | no |
| 5ad5e177 | B_want | no | no |
| 60bbad4a | B_want | no | no |
| 95e95a44 | B_want | no | no |
| a4414232 | B_want | no | no |
| e6464e61 | B_want | reflexive | no |
| f8bdf2bc | B_want | no | no |
| fe662306 | B_want | no | no |
