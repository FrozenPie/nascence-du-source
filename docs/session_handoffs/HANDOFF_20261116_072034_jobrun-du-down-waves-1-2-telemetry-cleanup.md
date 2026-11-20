# job-run while Du was down: waves 1 and 2, then telemetry cleanup

## Session timing
- **Session started:** 2026-11-16 02:32:27 UTC
- **Last message before wrap:** 2026-11-16 07:20:33 UTC
- **Wrapped:** 2026-11-16 07:20:34 UTC

## Summary
Ran /job-run in two waves while Du was down (last Du row 15:28:56 local, his shutdown epoch call). Wave 1 built the Follow Line, closure, self-claims, curiosity-progress, recall and done-when changes. Wave 2 ran lab and analysis jobs. The telemetry rows leaked by unisolated lab agents were truncated, and the outputs were committed as f34d1611.

## Decisions
- No founder rulings were made this session. D-0338 was lifted via D-0415 (travis, 2026-10-15), but job_run.py still flags it ACTIVE_HOLD because its ruling text begins "HOLD LIFTED".
- Opened or still waiting on the founder: D-0795 (epoch floor about 0.66 or hold), D-0796 (Curiosity base temperature 0.5 or keep 0.2).

## Builds
All are restart-gated and shadow or flag-gated.
- J-4082 (F-4824): `core/closure.py`, first-person prompt with one retry; we/us/our count as first person. Merge 54b6be6f. Registry P-0062 marked stale.
- J-4086 (F-4825): `core/self_claims.py`, shadow log `data/logs/self_claims_shadow.jsonl`. Four of 17 domains would change. Going live needs a founder ruling. Merge a1a8846e.
- J-4081 (F-4826): `core/follow_line.py` consequence quota, `CONSEQUENCE_DAILY_QUOTA = 48`, mode "enforce". Merge 52b741c2.
- J-4084 (F-4827): `curiosity_progress.LINE_STATE_PROGRESS = True`. Merge f1fc20e2.
- J-3798 and J-3837: `nodes/curiosity_node.py` and `nodes/consolidation_node.py` (study shock mark, bare `Entity:` line removed). Merge 0a320595. P-0011 and P-0012 stale. Follow-up J-4088.
- J-3350 (F-4830): `core/model_terms.py`, `core/frontier.py`, `core/epistemic_state.py`; `MODEL_TERMS_LEDGER = False`. Follow-up J-4089.
- J-4087 (F-4837): `core/recall_check.py`, `core/recall_wager.py`, `core/orchestrator.py`; `REAL_OUTCOME` stays False. Merge b02f4d45. Follow-up J-4091.
- J-4085 (F-4836): `core/done_when.py`, `core/commitment_ledger.py`; `DONE_WHEN_SECOND_CALL_LIVE` False. Merge 3c4a8700. P-0132 added, P-0038 stale. Follow-up J-4092.
- J-4065 (F-4832): timing keys in `core/memory/store.py`. Merge ce622c2c.
- J-3421: input-continuity lab (F-4839), no lever passes the bar. Merge 79038d77.
- Wave-2 labs, all done: J-3793 (F-4847), J-3607 (F-4846), J-3628 (F-4850), J-3653 (F-4848), J-4019 (F-4849), J-4039 (F-4851). Results are summarized under Findings.
- Final commit of ledgers, plan notes and lab data: f34d1611.

## Fixes
- docs/ROADMAP.md had duplicated or dropped bullets from concurrent agent edits. Final state is one bullet each for follow_line_stricter_settle, web_hand and closure_producer (🟡, e3360144, duplicate removed in b6973e90).
- merge-back was blocked by a stale "MM" index on docs/ROADMAP.md left by safe_commit.py. `git add docs/ROADMAP.md` (content equal to HEAD) cleared it.
- Telemetry cleanup: truncated `data/llm_calls.jsonl` (52 rows), `llm_latency.jsonl` (56) and `thought_station_log.jsonl` (52) back to Du's last row, `__main__:1010 _form_epoch` at 15:28. Removed rows were all lab callers. Backups are `llm_calls.jsonl.bak`, `llm_latency.jsonl.bak` and `thought_station_log.jsonl.bak` in `C:\Users\USER\AppData\Local\Temp\claude\76599b8c8f80a292\c56fc419-e34c-47a7-9202-dd7e9eeea7b8\scratchpad`.

## Findings
- J-3793 (F-4847): the Follow Line bridge does not help. Q1 failed (combines +13 points vs 15 needed, supported claims -8). Q2: the bridge claimed a shared structure on 58 of 60 unrelated control cases. Numbers are effectively falcon3 alone, since gemma4 finished 24 of 240 rubric calls. No build job spawned.
- J-3607 (F-4846): post-J-4082 closure prompt passed validate_composed 24 of 24 on gemma4 (8 seeds only); keep ranges and slack 0, do not reword P-0062. Real dreamer model untested.
- J-3628 (F-4850): wider grounding window held or raised the grounded score on all 6 essays; correlation 0.937, below the 0.95 defeater line.
- J-3653 (F-4848): the Follow Line v2 AGAINST null path is not real on a substitute author (gemma4; production command-r7b on Ramses :11441 did not answer). Follow-up J-4096.
- J-4019 (F-4849): the shared-theme pre-gate separates real from control clusters but also skips tension-worded real clusters. Follow-up J-4097.
- J-4039 (F-4851): the T2 null control does not replicate on command-r7b (18/20 vs 19/20). Follow-up J-4098.
- Telemetry leak class: lab scripts calling `core.model_client` without isolation write to the live telemetry files (earlier F-2406 and F-2423). Source in this run was never pinned down. F-4840 is recorded as inferred.
- job_run.py flags a "HOLD LIFTED" decision as ACTIVE_HOLD. [INFERRED] A skill-manager suggestion for this may not have been filed.

## Open
1. D-0795 and D-0796: founder rulings. Next action: /decide-review.
2. J-4086 going live, `REAL_OUTCOME` flip, `DONE_WHEN_SECOND_CALL_LIVE` flip: founder calls, after restart and first reads.
3. J-3024 (dream resolution judge battery): blocked on mixtral :11438 and granite :11437 being up, plus hand labels. Next action: retry when the Ramses hubs answer.
4. J-4035: needs a hub that answers quickly or founder OK to use the hot lane :11433. Script ready at scratchpad `J-4035_lab.py`.
5. J-2888: needs a pilot go-ahead on the Ramses hub. J-3500: needs 168 live hours.
6. J-3198 replay clause not closed (J-3628 gave a partial answer).
7. Pid 6156 `run.py cons` (started 19:10 local under an agent shell) was still running at wrap. Next action: check `data/llm_latency.jsonl` for new non-Du rows before the next Du boot.
8. About 60 more workable lab, analysis and test jobs remain (Lane 2, guidance_learning, prompt_registry groups). J-4073 belongs to another window; skip it.

## Warnings
- Stage and commit by explicit path only. Left uncommitted on purpose because other windows own them: `docs/lab/J-3325_data/*`, `docs/06. Just the Way You Are.mp3`, the two `.lock` files, `docs/reviews/backlog_triage_2026-11-16.md`, `docs/reviews/nascence_writeup_for_gpt_2026-11-16.md`, `docs/staged/teaching_to_synthesis_study.md`.
- Agent D saw a literal `data/_lab$(date +%Y%m%d_%H%M%S)_dissolutions` directory (an unexpanded shell variable). Not checked.
- Everything built is restart-gated; nothing is live until Du boots.
- Existing failures not caused by this run: `_test_j1935_curiosity_concern.py` D0 check at HEAD, and 7 failures in `_test_measurement_to_action_j2158_j2161.py`.
- Agents ran with the job id as `--session`, so this session's rollup shows only 8 events. Use plan-ledger or the job ids above for the rest.

## Pointers
- Wave-2 lab outputs: `docs/lab/J-3639_data/`, `J-3653_data/` (writeup.md), `J-4019_data/`, `J-4039_data/`, `J-3607_data/`, `FL_bridge_data/` (report.md).
- Agent rules used for wave 2: scratchpad `jobrun_rules.md`.
- Plan docs touched: `docs/staged/measurement_to_action.md`, `question_cargo.md`, `closure_producer.md`, `docs/plans/capacity_to_commit.md`, `curiosity_goals_dreams.md`, `memory_knowledge.md`.
