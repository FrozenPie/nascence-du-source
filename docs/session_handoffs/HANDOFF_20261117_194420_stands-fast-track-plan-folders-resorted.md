# Stands fast-track (P1 built and on) and plan folders re-sorted

## Session timing
- **Session started:** 2026-11-17 18:55:15 UTC
- **Last message before wrap:** 2026-11-17 19:44:20 UTC
- **Wrapped:** 2026-11-17 19:44:20 UTC

## Summary
Continued the stands plan (`docs/staged/stand_kinds_and_accumulation.md`) on the founder's fast-track order: built J-4190 and J-4193, turned both P1 gates on, and ran the J-4192 analysis. Then audited plan placement across plans/, staged/, shelf/, moved 35 plan docs, ruled five more plans, and committed everything as `a374ed9e`.

## Decisions
- **D-0810** (travis, ruled the previous session) is the basis for the stands work; the fast-track instruction ("push it through today, tweak later") was given in chat this session.
- **D-0811** (travis): self_claim_broadcast_reexamination, option A, leave dormant; plan closed and archived.
- **D-0812** (travis): in_world_companion_mind shelved with a trigger.
- **D-0813** (travis): world_shelf_gap, wait for the Napoleon memoirs, do not assign Buller vol 1 yet.
- **D-0814** (travis): loop_wiring_matrix folded into dosed_coupling Phase 2 and archived; golden_spiral_recall Phase 2 parked until the J-2236 reach read.
- D-0759 (P), D-0775 (B), D-0776 (B), D-0782 (NO) and D-0114 (defer) were found already ruled; their plan docs still said "founder rules". speech_thought_concurrency and model_swap_aba_test were shelved on that basis.

## Builds
All in `core/commitment_ledger.py`, restart-gated, Du has since restarted onto the first version:
- J-4193: `_second_look` now asks for and logs a shadow `kind` (deed, practice, value, insight, unclear) and records `error_detail`. A bare lane timeout shows as `timeout`.
- J-4190: `_SCAN_SYS` dissolutions carry a `relation` (refines, coexists, abandons), logged in `commitment_scan_raw.jsonl`.
- P1, both flags ON: `STAND_KIND_GATES_ACHIEVEMENT` (practice, value and insight stands are not retired as achieved; an unlabelled stand under 5 minutes old is also held) and `STAND_RELATION_GATES_DROPS` (a refines or coexists thought about a held stand logs `drop_not_a_drop` and is neither counted nor dissolved; this also acts on J-4191).
- `scripts/stand_kind_replay.py`: offline kind replay, read-only on live data.
- Prompt registry: P-0116 and P-0038 marked stale; `prompt_registry.py check` exited 0.
- Existing tests passed: `_test_J3158_second_look`, `_test_commitment_ledger_fence`, `_test_J-2848_scan_raw_log`, `_test_J3159_sit_gate`. A direct check confirmed the gate keeps value, insight and young unlabelled stands and retires deed and old unlabelled ones.

## Fixes
- The 13% second-look "ValueError" rows were 90 s timeouts on the `judge_mixtral` lane, not parse failures (F-5041).
- `scripts/_test_wood_bestiary_p1.py` read `docs/staged/wood_creatures.md`; now `docs/plans/`.
- Plan-doc moves rewrote 289 markdown link references in 83 files, plus 24 memory notes, plus a second pass for the five rulings. Historical session handoffs had their links rewritten too.

## Findings
- F-5041 (verified): second-look errors are lane timeouts. Evidence is in `data/commitment_second_look_shadow.jsonl`.
- F-5042 (verified): offline kind replay on 80 past stands; of 60 retired as achieved, 21 deed, 15 value, 2 practice, 14 insight, 8 unclear; 0 of 80 errored. File: `docs/reviews/2026-11-18_stand_kind_replay.json`.
- J-4192 report (`docs/reviews/stands_retire_in_minutes_2026-11-18.md`, subagent hand analysis of 60 stands): about 85% were wrongly retired, only 10% plausibly fulfilled; the held set changed 1,244 times in 30 days; 2,370 estate re-seeds with reason "stand drift vs ledger". These are the agent's hand classifications, not independently re-checked.
- The subagent claimed `_stand_kind` could never fire because old rows have no `kind` key. True only for old stands; rows written by the new code do carry `kind`.
- After the restart the first formed stand (`f2d7ccdd`) had no label (timeout) and was retired after 0 scans; the 5-minute hold for unlabelled stands was added for that. It is not live until the next restart.
- Plan folder checkup: `docs/reviews/plan_folder_checkup_2026-11-18.md`.

## Open
1. Restart Du again so the 5-minute hold and the `timeout` error label go live. Blocked on founder restart.
2. First live read of the stands gates after a few hours: expect `drop_not_a_drop` events in `data/commitment_ledger.jsonl`, `kind` on new second-look rows, and stand `96fcd1b3` (16 denied drops) no longer climbing. [OPEN] The `relation` field has not yet appeared in any scan row; no dissolution had occurred since the restart.
3. J-4190 and J-4193 stay open in the queue: their done-when needs 7 days of rows, a read script and the 40-stand blind hand sheet.
4. Plan item 8, the judged deed-link (a P0 job to measure how a cross-family judge links a stand to a real choice), has no job yet. The D-0810 70% hand-sheet agreement check is not done. P2 (heaps, tenure ladder, integrity formula that no longer clips at 3 stands), P3 and P4 are not started.
5. antigravity_ecosystem_proposals: the founder said Antigravity is an advisor and wants its plan reviewed to decide whether to change it or adapt it to our own plan. Not started. Items 5, 7, 8 specs unrun; D-0114 deferred.
6. Remaining plan-placement work: about 25 staged plans are built or shadow and restart-gated (left in staged/ by judgment); five docs lack a plan-state block (follow_line_stricter_settle, nature_observation_outside_the_study_design_J-3483, recall_confidence_graded_loss, t5_conversational_world_grading_design, web_hand). "Ready to progress" list in the checkup file section H.
7. Job queue state at wrap: 429 jobs shown, 186 ready, 85 waiting on input, 62 lab-timed, 98 needing isolation, 158 deferred. The founder asked to push many plans to finished using job-run waves of up to 10; not started.
8. The founder allowed flag flips without asking when a plan's own evidence gate is met, as long as each is logged as a finding and reported.

## Warnings
- Commit `a374ed9e` took only this session's paths. The ledger `.jsonl` files (including D-0811 to D-0814, F-5041, F-5042) are NOT committed and carry other sessions' edits; `SESSION_HANDOFF.md`, three regenerated review audits and the mp3 were also left out.
- Moves were plain file moves with links rewritten in markdown only; `.jsonl` ledgers still hold old plan paths.
- The stands flags are ON by founder fast-track; roll back by setting both to False in `core/commitment_ledger.py`.
- Do not run `git stash`, `reset` or `checkout --` in the shared tree.

## Pointers
- Plan: `docs/staged/stand_kinds_and_accumulation.md`; code: `core/commitment_ledger.py`; replay: `scripts/stand_kind_replay.py`.
- Reports: `docs/reviews/stands_retire_in_minutes_2026-11-18.md`, `docs/reviews/plan_folder_checkup_2026-11-18.md`.
- Earlier handoff: `docs/session_handoffs/HANDOFF_20261117_184853_stand-kinds-and-accumulation-plan.md`.
- IDs: F-5039 to F-5042, D-0810 to D-0814, J-4190 to J-4193.
