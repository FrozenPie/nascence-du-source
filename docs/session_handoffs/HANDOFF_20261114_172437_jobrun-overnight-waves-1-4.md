# Overnight job-run, waves 1-4 (2026-11-14/15), Du live throughout

## Session timing
- **Session started:** 2026-11-14 08:54:02 UTC
- **Last message before wrap:** 2026-11-14 17:24:36 UTC
- **Wrapped:** 2026-11-14 17:24:37 UTC

## Summary
Founder went to bed after Du restarted (about 21:53 NZDT) and asked for an overnight job-run until 9 am. Four Workflow waves (about 53 agents) ran roughly 22:05 to 06:00 NZDT; about 25 jobs closed, the rest were deferred, partial or blocked. Nothing new is live: all code changes are restart-gated.

## Decisions
- D-0782 opened (not ruled) by J-3996: founder go/no-go on the A-B-A model-swap test (hot lane, qwen3.5:9b / tulu3:8b / qwen3.5:9b, 7-day arms, about 23 days, needs a core/nodes code freeze). Design is docs/staged/model_swap_aba_test.md.
- No rulings made by Claude. Active holds (D-0718 curiosity, D-0338 lane2) were respected; J-3988 was a read-only write-up.

## Builds
Merged and verified by their own hermetic tests, all flag-off or shadow, restart-gated:
- J-3636 core/decomposed_critic.py logs full draft (2000 chars); follow-up J-4020 (needs 30 new rows).
- J-3341 self-relate pinned to :11441 (nodes/subconscious_node.py, hud/server.py); follow-up J-4021.
- J-4012 pursuit close judge v3, `V3_PROMPT = False` (core/pursuit_close_shadow.py); follow-up J-4023.
- J-3983 train ids on pursuits, `spawned_by` lineage in core/goals.py.
- J-4013 supervisor `top_rss` (scripts/supervisor.py, takes effect on supervisor restart).
- J-3752 core/stamp_rows.py reader-side twin-row drop (mapping_census, object_graph, du_pulse).
- J-4017 core/pipeline_stage_shadow.py plus core/orchestrator.py hook: merged by hand from branch jobrun/j4017_pre_speech_shadow (merge commit on master), worktree and branch removed.
- J-3981 docs/staged/pre_speech_pipeline_latency.md; J-3997 stage badges synced (layered_goals shadow, prompt_manager partial, maths_of_mind_atlas designed).
- Test hygiene: J-3525, J-3916, J-3505 stale pins fixed; J-3789 added scripts/_hermetic_data.py and guarded 46 data-writing tests; J-3583 guarded 12 guidance_learning tests.

## Fixes
- J-3855 scripts/backfill_founder_memory.py now matches on the first line of the Q block (F-4436 fix, commit 0b0f278e). The real write was NOT run (needs Du stopped).
- J-3547, J-3590, J-3512 were already fixed on HEAD; closed with no change. J-3590: closure_test.py still fails two "lab DB byte-identical" checks; follow-up J-4022.

## Findings
- F-4721 (J-3939): the night freezes are frontier.json load/save on the loop thread, 14 of 18 probed freezes, about 76 percent of freeze seconds. Follow-up J-4030.
- F-4725 and F-4727 (J-2952, J-2794): the granite tiebreak never beats the constant-majority baseline; on "bears" it answers True 60/63. Follow-ups J-4032, J-4033, J-4034.
- F-4729 (J-3416): the mixtral blind judge is at chance on "faithful", so J-3150's faithful verdict is untrustworthy. Follow-up J-4036.
- F-4734 (J-3651): the P-0053 T2 prompt claims a link on shuffled material 20/20 vs 1/20 neutral. J-3652: the T6 null arm did not meet the inadmissibility rule (F-4736). J-3650 (F-4710, follow-up J-4019): the Refinery null rule not met, but the author was qwen3.5:9b, not production command-r7b.
- F-4731 (J-3428): symbol window replay, 650 windows. F-4719 (J-3742): critic check 4 over-fires (10 of 11 approve-to-reject flips cite it; grader found a real violation in 1); remaining steps in J-4028. F-4706 (J-3866) librarian eval, weak; J-4018 reruns. F-4708 (J-3996) day-to-day variance numbers. F-4722 (J-2968) single-rater only, J-4031.
- [INFERRED] Judge hubs :11439/:11440 were saturated for hours during wave 3; labs there ran 19 of about 1,580 calls (J-3411) or timed out (J-2968, J-3711). Du's own traffic or a hub stall is the likely cause; not diagnosed.

## Open
1. J-3855: run `scripts/backfill_founder_memory.py --dry-run --job J-3855`, then for real with Du stopped and founder go-ahead; deferred to 2026-11-16 (placeholder).
2. D-0782: founder go/no-go on the model-swap test.
3. Deferred, data not yet accrued since the 14:15 / 21:53 boots: J-3982 and J-3986 (layered goals, need 300 rows, have about 47; real gate about 42 more live hours), J-3716 (needs 60 study notes). J-3500 (needs 168 live hours after J-2981) is unfinished.
4. Partial, left in_progress: J-3711 (85 of 128 sentences judged, 68 percent unsupported), J-3447 (6 of 20 gists, `_DRIFT_MOVE_MIN`=0.05 looks too low but sample thin), J-3411 (harness built, judges too slow), J-3742 (J-4028 has the rest). J-3501: both Follow Line tests still fail the canary while Du is live; run when Du is down.
5. Blocked: J-3208 (needs J-2951 done, and `not_before` 2026-11-17), J-2829 (needs LLM calls; run with hubs free).
6. Wave 3 chains that ran after J-3447 were truncated in my view; check `job_queue.py list` for J-3083, J-3558, J-3694, J-2951, J-3131, J-3463, J-3378 statuses before assuming anything. J-3131 is committed (cb9f5cd0, F-4733).
7. Verify after the next restart: J-3983 pursuit train ids match frontier `asked_by.train_id`; J-4017 shadow rows accrue (J-4017's follow-up reads).

## Warnings
- safe_commit.py leaves the git index stale (F-2570): after it, run `git add <path>`; this session fixed 9 MM files that way. Eight lab files left staged were committed (2f67c3e0).
- The session-event rollup is empty because every agent used its job id as `--session`; use `plan_ledger.py` or the job ids above, not the session rollup, to see what changed.
- Another session's working-tree edits (docs ledgers, plans) are uncommitted in the shared tree; this session committed only explicit paths.
- Old worktree branches jobrun/wb_* through wl_* and worktrees under C:/wt predate this session; not touched.

## Pointers
- Agent returns: C:/Users/USER/.claude/projects/C--Nascence/239b1ff8-1be8-4e4b-b6bd-f5632d31557c/subagents/workflows/ (wf_4099a469-8f8, wf_1329ab25-b88, wf_bd414bdc-0ac, wf_e804e98a-99c, each with journal.jsonl).
- docs/staged/model_swap_aba_test.md, docs/staged/pre_speech_pipeline_latency.md, docs/lab/J-3416_data, docs/lab/J-2952_data, docs/lab/J-3428_data.
