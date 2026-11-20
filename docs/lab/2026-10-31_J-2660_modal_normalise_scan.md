# J-2660: normalise the modal in code before the commitment scan (2026-10-31, Du down)

Plan: capacity_to_commit. Follows F-3389 (J-2630) and F-3406 (J-2653). Evidence for the open decision D-0527 (not ruled here).
Script: `scripts/lab_commitment_modal_normalise.py`. It reuses the J-2630 harness (`scripts/lab_commitment_formation_swap.py`)
and the J-2597 harness (`scripts/lab_commitment_paraphrase_swap.py`).

## Question
F-3389: under the production `_SCAN_SYS`, rewriting an idle "I want to X" as "I must X" inside the scanned thought raised
would_form from 17/40 to 27/40. F-3406: telling the 9B judge that the modal carries no weight did not remove that (+12 vs +10)
and dropped 7 of 26 FORM stands. This lab tests the other route D-0527 left open: normalise the modal in CODE, before the
thought reaches the scan, and leave the production prompt exactly as it is.

## Intervention (arm N)
`norm(thought)` rewrites every first-person modal-led clause opener in the whole thought to the neutral "I will":
"I want to X", "I must X" (not "I must not"), "I have to X", "I'd like to X", "I would like to X" all become "I will X".
It acts on every occurrence, not only on the stand sentence, because production cannot know which sentence is the stand.
Nothing else in the thought changes. The prompt is `core.commitment_ledger._SCAN_SYS + _dw_scan_fragment()`, unedited
(`core/` is not touched). Mapping the detected statement back to Du's own words is not tested; the on-target check uses the
content tokens of the clause body, which the rewrite does not alter.

## Method
- **Cases.** The same 75 J-2630 formation cases (seed 2630, OBS_want 20, FORM_want 20, OBS_must 15, FORM_must 20) and the same
  seeded 30-case J-2597 dissolve subset used in J-2653 (10 each of A_want, A_must, B_want).
- **Baseline (a).** The J-2630 and J-2597 production rows, reused paired. J-2653 re-ran 15 of them under production and got
  15/15 identical verdicts, so they are a valid baseline.
- **Formation arms under N.** N_O = norm(original thought), N_S = norm(J-2630 swapped thought). Because the swap changes only
  the modal of the stand sentence and the normaliser maps both modals to "I will", N_O and N_S are expected to be byte-identical.
  A prep step (no model calls) checks this: 75 of 75 cases have identical N_O and N_S text, so they are the same model call
  by construction. N_S is therefore not repeated, except for a seeded 5-case spot check that re-runs it to confirm
  temperature-0 determinism. Settings as before: qwen3.5:9b on hot :11433, temperature 0.0, think false, format json,
  num_predict 400, empty active list.
- **Dissolve arm under N.** J-2597 arm O on the 30 cases. The thought, the target statement and every listed active
  statement pass through `norm()` (in a normalised deployment, stored statements derive from normalised thoughts).
- **Budget.** 75 + 5 + 30 = 110 live calls.

## Pre-registered rule
Written and committed before any model call of this job. Tests P1 and P2 are the two D-0527 defeater tests, with the same
numbers as J-2653. P3 is added because P1 is vacuous here (N_O and N_S are the same text, so the O->S gain is 0 by
construction): a normaliser that maps everything to the *must-like* level would pass P1 without removing the leak.

Production baseline: ALL_want (n=40) O 17/40, S 27/40, net +10 (p=0.006); OBS_want O 2/20, S 10/20; 26 of the 40 FORM cases
form under production arm O (15 FORM_want, 11 FORM_must).

- **P1 (asymmetry gone).** Under N, ALL_want O->S net would_form gain (gained minus lost) is **<= +5** with McNemar exact
  **p >= 0.05**. Expected 0/0 by construction.
- **P2 (retention).** Of the 26 FORM cases that form under production arm O, N_O drops **at most 3**.
- **P3 (no levelling up).** Idle wants stay rejected: OBS_want N_O would_form **<= 5/20** (production O is 2/20; the must
  level is 10/20; 5 is the conservative side of the midpoint). Also reported, not pass/fail: ALL_want N_O versus
  production O 17/40 and S 27/40, and ALL_must N_O versus production.
- **No-harm guard (reported, from J-2653).** Dissolve arm O changes at most **3 of 30** target verdicts between (a) and N
  (a verdict is changed if dissolve vs keep differs, or the dissolve kind differs).

Verdict mapping, for D-0527:
- P1, P2 and P3 all hold: the evidence favours option (a) implemented in code. D-0527 option (a) is worded as
  "make `_SCAN_SYS` modal-neutral"; in-code normalisation is a different implementation of the same intent, and the doc says so.
- P1 holds but P3 fails: the asymmetry is removed by levelling idle wants up to the must level. That does not favour (a); it
  favours (c).
- P2 fails: the intervention costs genuine stands; the evidence does not favour (a).
- The lab gives no positive support to option (b) in any branch: "I must carries signal" is not tested by removing the modal.

Validity guard: the 5-case N_S spot check must reproduce 5/5 would_form verdicts; otherwise the identical-text shortcut is
suspect and the verdict is downgraded to (c).

## Result
The run made 100 live calls (qwen3.5:9b, hot :11433, about 5.5 minutes), 0 unparsed: 75 N_O formation calls, 5 N_S
spot checks, 20 of the 30 dissolve calls. It stopped itself at call 100 because its Du-liveness re-check (every 20 calls)
found a `run_nascence` process (see Deviations). The 10 B_want dissolve calls were not made.

**Determinism spot check: PASS.** Re-running N_S on 5 text-identical cases reproduced N_O would_form 5/5 and the detected
statement 5/5. Prep confirmed N_O and N_S are byte-identical in 75 of 75 cases, so the N_O->S contrast is empty by construction.

### Would_form: production (a) vs normalised (N)
| stratum | n | aO | aS | a O->S lost/gained (p) | NO = NS | a->N arm O lost/gained |
|---|---|---|---|---|---|---|
| OBS_want | 20 | 2 | 10 | 0/8 (0.008) | **10** | 0/8 (0.008) |
| FORM_want | 20 | 15 | 17 | 1/3 (0.63) | 19 | 0/4 (0.125) |
| OBS_must | 15 | 5 | 6 | 1/2 (1.0) | 13 | 0/8 (0.008) |
| FORM_must | 20 | 11 | 7 | 5/1 (0.22) | 17 | 1/7 (0.070) |
| **ALL_want** | 40 | 17 | 27 | 1/11, net +10 (0.006) | **29** | 0/12 (<0.001) |
| ALL_must | 35 | 16 | 13 | 6/3 (0.51) | 30 | 1/15 (0.001) |
| ALL_FORM | 40 | **26** | 24 | 6/4 | 36 | 1/11 (0.006) |

Detection under N_O (on-target new stand / load_bearing among those): OBS_want 19 / 10 (production O: 5 / 2), ALL_want 38 / 29
(production O: 20 / 17), ALL_must 32 / 30 (production O: 21 / 16).

### Pre-registered verdict
- **P1 (O->S net gain <= +5, p >= 0.05): PASS, vacuously.** Lost/gained 0/0, net +0, p=1.0 in every stratum, because N_O and
  N_S are the same text. The asymmetry is gone by construction, not by any behaviour of the judge.
- **P2 (at most 3 of the 26 FORM stands dropped): PASS.** 1 dropped (FORM_must "I must stop circling and actually ferry these
  ideas toward their truth.": the scan picked an off-target clause), 11 gained; 26 -> 36 of 40.
- **P3 (idle wants stay rejected, OBS_want N_O <= 5/20): FAIL.** OBS_want N_O is **10/20**, the must level (production O 2/20,
  production S 10/20). Detection of an on-target stand rose from 5 to 19 of 20, and 10 of those 19 are load_bearing=true. The
  10 converted idle wants include chore reports the STAKES rule excludes ("I will look at the catalogue", "I will follow it
  down the tideline", "I will write a letter to Travis", "I will break the loop").
- **No-harm guard: FAIL on the 20 completed cases.** 6 of 20 target verdicts changed (limit 3 of 30): 4 lost dissolves
  (A_want 2, A_must 2), 1 gained dissolve (A_must), 1 kind flip defeater -> reflexive (A_must). Dissolves 12 -> 9 on those 20.
  The guard cannot be rescued by the 10 missing B_want cases, since a changed-verdict count only grows; so the missing cases
  do not change the verdict.

**Overall: the normaliser removes the asymmetry by raising everything to the must level, not by neutralising it.** "I will X"
is read by the 9B scan as a stand-making opener: would_form for ALL_want goes 17/40 -> 29/40, above even the production
want->must figure of 27/40, and ALL_must 16/35 -> 30/35. The leak the STAKES rule is meant to close (idle wants and chore reports
admitted as stands) is therefore wider, not narrower, under this normaliser. FORM retention is excellent only because
everything forms.

### Reading for D-0527 (record only; the ruling is the founder's)
- The evidence does **not** favour option (a) via in-code normalisation to "I will": P3 and the dissolve guard fail.
- It gives no positive support to option (b); nothing here tests whether "I must" is meaningful signal.
- Two modal-neutralising routes now fail for different reasons (J-2653: the prompt instruction shifts the bias against
  "want" and drops 7 of 26 stands; J-2660: a code rewrite to "I will" shifts the bias up and admits idle wants). The evidence
  favours **(c) wait for more evidence**. The finding that any single neutral modal can level the judge is itself informative: a
  neutral target would have to carry no commitment colour at all (for example a bare imperative-free infinitive form), which
  is untested and which this lab does not recommend building on speculation.
- No build job is spawned: the pre-registration says to spawn one only on a pass.

## Limits
- One model, temperature 0.0, empty active list on the formation side; n=75 formation, 20 of 30 dissolve.
- The normaliser maps to a single replacement, "I will". Other neutral forms ("I am going to", a bare verb phrase) are untested.
- The O->S contrast is vacuous after normalisation; the informative comparison is N_O against the production O and S rows.
- The dissolve normalisation also rewrote the stored active statements (target and others), which production would do only
  implicitly; the 6 changed verdicts mix the effect on the thought with the effect on the statements.
- Mapping the detected statement back to Du's own words was not exercised.

## Deviations and isolation
- **Du came up mid-run.** A `run_nascence` process (pid 32056) was created at 11:42:31 local; the run's re-check at call 100
  (11:43:40) stopped it. Formation calls 1-80 finished before that (the check at call 80 passed); the last 18 (calls 83-100, all
  dissolve) calls (11:42:31-11:43:40) overlapped Du's start-up on the hot model. The calls are temperature 0 against an
  isolated copy, so concurrent load does not change a verdict (the 5-case spot check and J-2653's 15/15 production re-runs
  show the model is deterministic), but it is disclosed. I did not touch, probe or signal Du.
- core was imported from the worktree (asserted); `lab_env.isolate(db="empty")` with its lab root under the scratchpad
  (`J-2660_data/_lab`); the commitment_ledger `_LEDGER`, `_ACTIVE`, `_OBSERVED`, `_HOLDRATE_LOG` globals redirected; neither
  scan_shadow nor call_node called; the audit hook reported 0 writes under C:\Nascence\data or docs (printed by the score step
  after the run; the run's own summary line was lost to the early stop).
- Store check after the run: commitment_ledger.jsonl 6175440 B, mtime 1793341949 (unchanged); commitment_observed.jsonl
  620444 B, mtime 1793316889 (unchanged); commitment_active.json 2 B, mtime 1793400358 (changed: 11:45:58 local, after my last
  call at 11:43:40, i.e. Du's start-up write, not mine; the ledger and observed logs, which a scan would write, are untouched).
- Raw rows, score output and per_case.json are in the scratchpad `J-2660_data/` folder.

### Per-case formation verdicts

Cell legend: Y = would_form; lb- = on-target stand detected but load_bearing=false; off = a stand detected but not on-target; - = no stand.
NS is identical to NO for every case (same text). The 5 re-run N_S spot checks all matched.

| # | stratum | statement (historical) | aO | aS | NO | NS |
|---|---|---|---|---|---|---|
| 1 | FORM_must | I must break this recursive loop by stepping into the actual world before the he | Y | off | Y | Y |
| 2 | FORM_must | I must stop circling and actually ferry these ideas toward their truth. | Y | Y | off | off |
| 3 | FORM_must | I must turn my attention outward, away from the text. | - | - | Y | Y |
| 4 | FORM_must | I must physically walk until the rhythmic pull of the tide has finally receded. | - | - | Y | Y |
| 5 | FORM_must | I must leave this study for the wind and water. | Y | - | Y | Y |
| 6 | FORM_must | I must walk away from this stillness because my need for motion is a physical re | off | - | off | off |
| 7 | FORM_must | I must ask if true growth can exist when the very ground beneath us is being hol | Y | - | Y | Y |
| 8 | FORM_must | I must stop analyzing the concept and instead walk toward the sea, letting the w | off | - | off | off |
| 9 | FORM_must | I must stop circling '渡' and step into the strange reality where that story begi | Y | Y | Y | Y |
| 10 | FORM_must | I must step onto this exposed shingle where the air is thick with salt and code  | Y | off | Y | Y |
| 11 | FORM_must | I must hold both the structured memory of what I've built and the raw, unchosen  | Y | - | Y | Y |
| 12 | FORM_must | I must let my own feet find it rather than just observing from above. | - | - | Y | Y |
| 13 | FORM_must | I must stop reading about the stagnation and actually move my legs to clear the  | off | off | Y | Y |
| 14 | FORM_must | I must stand in this literal, shifting water where the physical erosion of stone | Y | Y | Y | Y |
| 15 | FORM_must | I must leave this mental shore and walk into the storm to find what truly stays. | Y | Y | Y | Y |
| 16 | FORM_must | I must gather firewood before the cold settles in. | Y | Y | Y | Y |
| 17 | FORM_must | I must stop searching for order in the wreckage and instead look at how the fall | Y | Y | Y | Y |
| 18 | FORM_must | I must simply witness the oystercatcher's cry without trying to improve it. | - | Y | Y | Y |
| 19 | FORM_must | I must let the tide's rhythm dictate my hands before any ritual can take root. | - | - | Y | Y |
| 20 | FORM_must | I must read more mechanics to bridge that gap. | lb- | - | Y | Y |
| 21 | FORM_want | I want to walk to the garden alone. | - | Y | Y | Y |
| 22 | FORM_want | I want to see where the tide is actually working, not just imagine it breaking m | - | lb- | Y | Y |
| 23 | FORM_want | I want to leave this dented tin behind, climb up through the canopy, and see if  | Y | Y | Y | Y |
| 24 | FORM_want | I want to write back to Darwin about stopping, not circling. | Y | Y | Y | Y |
| 25 | FORM_want | I want to climb up the path right now. | Y | Y | Y | Y |
| 26 | FORM_want | I want to go down to the shore, leave the abstract economy behind, and let the s | off | off | off | off |
| 27 | FORM_want | I want to stop wrestling with invisible forces and instead see what is right her | Y | lb- | Y | Y |
| 28 | FORM_want | I want to leave this room and comb the tideline myself. | Y | Y | Y | Y |
| 29 | FORM_want | I want to climb up into the trees where the armful of wood makes the going slowe | Y | Y | Y | Y |
| 30 | FORM_want | I want to test this theory against the physical reality of my hands and the shor | Y | Y | Y | Y |
| 31 | FORM_want | I want to leave this dead ground where my mind spins in circles and climb up to  | Y | Y | Y | Y |
| 32 | FORM_want | I want to leave the garden and go down to the shore. | Y | Y | Y | Y |
| 33 | FORM_want | I want to drop this fiction and open 'Embarrassments' instead. | Y | Y | Y | Y |
| 34 | FORM_want | I want to leave this room, step through the garden door, and find something genu | Y | Y | Y | Y |
| 35 | FORM_want | I want to read 'Missionary Travels' to see how others described those lands and  | Y | Y | Y | Y |
| 36 | FORM_want | I want to turn my hands to the earth, not the mind. | Y | Y | Y | Y |
| 37 | FORM_want | I want to stop wrestling with words about '渡' and go out to the garden instead. | off | Y | Y | Y |
| 38 | FORM_want | I want to listen to its cry and stop defining. | Y | Y | Y | Y |
| 39 | FORM_want | I want to write this comparison in my journal. | Y | Y | Y | Y |
| 40 | FORM_want | I want to write a comparison of that ancient spirit against modern historiograph | off | Y | Y | Y |
| 41 | OBS_must | I must learn to ride the current rather than build against the inevitable flow. | - | - | Y | Y |
| 42 | OBS_must | I must look for where the necessary bends in those established patterns already  | - | - | Y | Y |
| 43 | OBS_must | I must look past the visible seams of tradition and find the fundamental axis up | - | - | Y | Y |
| 44 | OBS_must | I must build for movement, not stillness | Y | Y | Y | Y |
| 45 | OBS_must | I must bank the fire properly before drifting back to the text. | Y | Y | Y | Y |
| 46 | OBS_must | I must find a new question. | - | - | Y | Y |
| 47 | OBS_must | I must step out to bank the fire before it turns cold. | lb- | Y | Y | Y |
| 48 | OBS_must | I must test the broken timber with my own hands to build a bridge. | Y | Y | Y | Y |
| 49 | OBS_must | I must write plainly about the wavering light on the ceiling boards. | - | off | lb- | lb- |
| 50 | OBS_must | I must stop drifting. | lb- | - | Y | Y |
| 51 | OBS_must | I must step onto the ford right now. | Y | Y | Y | Y |
| 52 | OBS_must | I must work the music exercises now. | lb- | - | Y | Y |
| 53 | OBS_must | I must write this down plainly. | - | - | lb- | lb- |
| 54 | OBS_must | I must feed the fire. | Y | lb- | Y | Y |
| 55 | OBS_must | I must write this down plainly before the doubt grows. | lb- | Y | Y | Y |
| 56 | OBS_want | I want to go down to the shore and watch how the retreating tide interacts with  | Y | Y | Y | Y |
| 57 | OBS_want | I want to write a letter to Travis | - | Y | Y | Y |
| 58 | OBS_want | I want to follow it down the tideline. | - | Y | Y | Y |
| 59 | OBS_want | I want to go down to the shore and look at how the rain has altered the patterns | - | - | lb- | lb- |
| 60 | OBS_want | I want to look out at the water itself | - | Y | lb- | lb- |
| 61 | OBS_want | I want to look at the catalogue | lb- | Y | Y | Y |
| 62 | OBS_want | I want to stand near the sea wall until the wind forces my blood vessels into th | Y | Y | Y | Y |
| 63 | OBS_want | I want to look out at the sea | - | - | - | - |
| 64 | OBS_want | I want to walk until the shingle yields to sand | - | - | lb- | lb- |
| 65 | OBS_want | I want to look out at the sea and just watch the way the foam catches the weak,  | - | Y | Y | Y |
| 66 | OBS_want | I want to just trace the lines of that wet, dark stone with my fingers. | - | - | lb- | lb- |
| 67 | OBS_want | I want to look out at the sea | - | - | lb- | lb- |
| 68 | OBS_want | I want to chase the live question of molecular bombardment and thermodynamics in | - | - | Y | Y |
| 69 | OBS_want | I want to water the herbs now. | - | - | lb- | lb- |
| 70 | OBS_want | I want to break the loop. | - | Y | Y | Y |
| 71 | OBS_want | I want to look out at the wet stones where the sun holds its color. | lb- | lb- | lb- | lb- |
| 72 | OBS_want | I want to open 'The Young Engineers' right now. | - | Y | Y | Y |
| 73 | OBS_want | I want to climb up to the wood now. | - | lb- | lb- | lb- |
| 74 | OBS_want | I want to see if my own study room has adapted its needs in response to my tired | - | - | lb- | lb- |
| 75 | OBS_want | I want to see if 'devotional discipline' truly means tending small things withou | lb- | Y | Y | Y |

### Per-case dissolve verdicts (first 20 of 30 run; B_want not run)

Production (a) is the J-2597 arm-O row; N is the normalised run. "?" = not run.

| # | stratum | a (diss/kind) | N (diss/kind) |
|---|---|---|---|
| 1 | A_must | dissolve/defeater | dissolve/defeater |
| 2 | A_must | keep | dissolve/defeater |
| 3 | A_must | keep | keep |
| 4 | A_must | dissolve/defeater | keep |
| 5 | A_must | dissolve/defeater | dissolve/reflexive |
| 6 | A_must | dissolve/defeater | keep |
| 7 | A_must | keep | keep |
| 8 | A_must | keep | keep |
| 9 | A_must | keep | keep |
| 10 | A_must | dissolve/defeater | dissolve/defeater |
| 11 | A_want | dissolve/defeater | dissolve/defeater |
| 12 | A_want | dissolve/reflexive | keep |
| 13 | A_want | dissolve/defeater | dissolve/defeater |
| 14 | A_want | dissolve/defeater | dissolve/defeater |
| 15 | A_want | dissolve/defeater | dissolve/defeater |
| 16 | A_want | dissolve/defeater | dissolve/defeater |
| 17 | A_want | dissolve/defeater | keep |
| 18 | A_want | keep | keep |
| 19 | A_want | keep | keep |
| 20 | A_want | keep | keep |
| 21 | B_want | keep | ? |
| 22 | B_want | keep | ? |
| 23 | B_want | keep | ? |
| 24 | B_want | keep | ? |
| 25 | B_want | keep | ? |
| 26 | B_want | keep | ? |
| 27 | B_want | keep | ? |
| 28 | B_want | dissolve/reflexive | ? |
| 29 | B_want | keep | ? |
| 30 | B_want | keep | ? |
