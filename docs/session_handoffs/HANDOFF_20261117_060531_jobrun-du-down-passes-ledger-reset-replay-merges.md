# Du-down job-run (3 passes), decide-review, ledger reset and replay, 7 branch merges

## Session timing
- **Session started:** 2026-11-16 08:13:58 UTC
- **Last message before wrap:** 2026-11-17 06:05:31 UTC
- **Wrapped:** 2026-11-17 06:05:31 UTC

## Summary
Ran three Du-down job-run passes (about 77, 55 and 69 agents), then a decide-review that ruled all 13 open decisions. The job, decision, findings and event ledgers were silently reset to git HEAD several times mid-run and were rebuilt by replaying agent transcripts. Seven reviewed job-run branches were merged into master; Du was restarted afterward and was running normally at 19:03 NZDT.

## Decisions
All ruled by travis via decide-review on 2026-11-17: D-0777 keep re-ask weight 0; D-0778 symbol node carries newest tablet text; D-0781 (a) promote surviving questions to the goal register; D-0783 keep label view, tighten tension judge, stay shadow; D-0785 tighten rehearse/self_distance cues before wiring the gauge; D-0787 build both opener diversity (D) and phrasing pools (B); D-0795 set `_EPOCH_RETRIEVAL_FLOOR` to about 0.66; D-0796 hold Curiosity base_temperature 0.2; D-0797 (c) hold until J-2083, re-baseline together, Lane 2 stays shadow; D-0798 (c) add self-domain opposite-pole pass; D-0799 retire the swap poll and gate on a real swap; D-0800 (b) adopt Recall arm E flag-gated shadow first; D-0801 remove the BEFORE YOU APPRAISE paragraph from the Emotion prompt.
The numbers D-0797..D-0799 in the question text above are the ORIGINAL ids. After replay, agent-opened decisions from the lost window were re-issued as D-0802..D-0809, all open (see docs/reviews/ledger_replay_plan_20261117.md for the old-to-new map).

## Builds
Seven branches reviewed (workflow wf_29fad84b-291, all verdict MERGE, tests passed) and merged: J-3249, J-3724, J-3818, J-4050 (scripts and tests only), J-2829 (`nodes/consolidation_node.py`, flag `CONSOLIDATION_DROP_PERSONA_BLOCK` default False, prompt unchanged), J-3750 (`core/librarian.py` word-boundary `_cap`, ungated, 26/26 tests), J-4083 (`core/closure.py`, `core/commitment_ledger.py` deed gate, `COMMITMENT_DEED_GATE` default True, shadow arm only). Merge commits be4f48b1..694df6f8. Evidence is finding F-5028. Smoke import from a throwaway worktree of merged HEAD passed and prompt_registry check exits 0.
Commits at wrap: 1c041df0 (ledgers, plan reports, review docs) and 164f92b9 (docs/lab outputs and scripts).

## Fixes
J-3818 released chapter_id on 545 members of three present-tense chapters, applied live while Du was down (D-0721, commit 0cc6ceea). J-4099 stage badges synced, J-4100 ROADMAP link, J-3471 CLAUDE.md UDMS ranker paragraph rewritten.

## Findings
- The ledgers (job_queue, decisions, findings, session_events) were reset to HEAD at about 16:36-16:38 NZDT on 11-17 and again roughly five times until 17:16, coinciding with WinError 5 on `os.replace`. Cause not identified. [OPEN] What resets them; what would resolve it: watch the ledger row counts and file-lock holders during the next heavy multi-agent run.
- Replay result: job_queue 4178 rows (J-4178 incl. two refresh-filed jobs), decisions 809 (D-0809), findings 5028 (F-5028 is the merge finding), thoughts 144 (T-0144). Post-reset writes were remapped (F-4852.. to F-4983..F-5027, J-4099..4102 to J-4161..J-4176, D-0797..0799 to D-0804..D-0809). J-4130 is a labelled placeholder; about 80 plan_state notes and some session_events/plan_snapshot rows were not replayed.
- Hub saturation: CPU hubs :11439/:11440 and Ramses mixtral :11438 took 50-170 s per trivial call even at 4 concurrent labs, so many hub-bound labs ended partial or blocked.
- Lab results worth knowing: J-3447 same-text noise floor p90 0.264 so `_DRIFT_MOVE_MIN` 0.05 flags 91% of unchanged retellings (J-4132 to set 0.25); J-3723 yi:34b critic precision 0.53 so the critic stays shadow; J-4123 narrow misattribution check fails (precision 0.40); J-2815 the Emotion prior steers labels (51% vs 23%); J-3751 study-note facts still do not accumulate (D-0802 open).
- The merge-back failure for the branches was a stale git index (MM on CLAUDE.md, docs/ROADMAP.md, docs/staged/closure_producer.md, docs/staged/web_hand.md with a clean working tree) plus two untracked J-3249 script copies; fixed with `git add` by path and moving the copies to docs/ledger_backups_20261117/untracked_displaced/.

## Open
1. Find the cause of the ledger resets. Next: log row counts and handle holders during the next multi-agent batch; keep docs/ledger_backups_20261117/*.replayed.jsonl until then.
2. Eight open decisions D-0802..D-0809 (agent-opened during the run). Next: `/decide-review`.
3. Build jobs from today's rulings (D-0778, D-0785, D-0787, D-0795, D-0798, D-0800, D-0801, D-0799, D-0783 judge tightening, J-4132 drift 0.25). The ruling-followups agent created jobs for some; several went through the replay as open and unstarted. Next: `job_queue.py list --ready` and check each.
4. About 40 hub-bound lab jobs that ended partial or blocked (for example J-3401, J-3563, J-2673, J-3593, J-3509, J-3657, J-4034, J-3442). Next: rerun on an idle box.
5. J2828 fields test fails on plain master as well as on J-2829. Next: file a job.
6. After Du has run a while: check re-formed chapters are not present-tense or copied (J-3818, J-3249) and read the deed-gate `not_achieved` rows (J-4083; the next 10 fragments go to the founder under D-0423).
7. In progress and stuck: J-2829, J-3218, J-3748, J-4050, J-4083 may still show in_progress or open after the merges. Next: `job_queue.py list --all` and release or done each.

## Warnings
- Never run git stash, reset, checkout --, restore or clean in C:\Nascence. Do not hand-edit the ledgers.
- If a ledger row count drops below 4178 / 809 / 5028, restore from docs/ledger_backups_20261117/<name>.replayed.jsonl before doing more writes.
- Merge only after refreshing a stale index with `git add <path>`; see memory feedback_safe_commit_stale_index.

## Pointers
docs/reviews/ledger_replay_plan_20261117.md; docs/ledger_backups_20261117/; commits 1c041df0, 164f92b9; findings F-5028; workflow journals under C:\Users\USER\.claude\projects\C--Nascence\482b149b-18f5-4094-87b7-2109d8b7b9a9\subagents\workflows\.
