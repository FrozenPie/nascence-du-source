# Job-run: Du-down wave, wave 2, and an overnight loop with Du live

## Session timing
- **Session started:** 2026-11-14 19:17:20 UTC
- **Last message before wrap:** 2026-11-15 19:52:00 UTC
- **Wrapped:** 2026-11-15 19:52:01 UTC

## Summary
The founder asked for every waiting job that needs Du down first, then everything else, avoiding Ramses while they gamed. Wave 1 ran 23 Du-down jobs and wave 2 ran 12 non-LLM jobs. After the founder restarted Du, an overnight loop ran roughly 80 more jobs until they shut Du down and told me to stop. Everything was then committed as 03940bff.

## Decisions
- No founder rulings were made this session, and no agent ruled a decision. Two items are explicitly waiting on the founder: J-2093's finding bears on D-0415's defeater clause (17 of 33 would_ride rows are on the topic sun), and J-2068 is ready for the D-0375 Phase 2 ruling.

## Builds
- J-3521: marked 3 empty-cargo closures on the live memory DB after a backup, with Du down.
- J-3822: repaired the 9 level-2 chapter period labels (script `scripts/apply_J-3822_level2_period_repair.py`, backup `data/backups/nascence_20261115_083140_pre_J-3822.db`, finding F-4742).
- J-3532: nothing to write, since the J-3482 shock-note marking was already applied (56 notes hidden).
- J-2814: internal-aware Emotion fallback line, commit 8db8f1ee, restart-gated.
- J-4026: recency shadow change in `core/memory_service.py`, commit 0944f710, restart-gated.
- J-4030: steps 1 and 2 built on branch `jobrun/J-4030` (c7e11c1e, worktree C:/wt/J-4030), not merged.
- J-4043: `scripts/liveness_audit.py` labels the retired behavioural mirror and the flag-off known_text arm.
- Replays and reads closed: J-3911, J-3312 (spawned J-4045), J-3856, J-3905 (spawned J-4046), J-3877, J-3387 (spawned J-4047), J-2252, J-3786, J-3901, J-4028, J-3687 (F-4756), J-2038 (F-4760), J-2093 (F-4757, spawned J-4048), J-2146 (F-4758, spawned J-4049), J-3591, J-2106, plus about 40 overnight jobs listed in the workflow journal.

## Findings
- J-2038: the D-0400 defeater is not met. 35.5% of 107 morning seeds scored below cosine 0.3, against an 80% threshold.
- J-2068: fired-clock disagreement is 3.77% (n=7,346), under the 20% bar, but 75% of fired rows are reading-source and no fired wingbeat rows exist (F-4759).
- J-2146: the sleep-path semantic fallback has never fired, yet 25 of 61 classify-log pairs have overlap low enough that only the fallback should surface them. [OPEN] J-4049 traces how they got through.
- Running several model-using agents against the same hot hub :11433 stalled it (J-2813, J-2815, J-3950 got no results). Keep model-using jobs to one at a time.
- The hubs (:11433, :11439, :11440, :11442) are local CPU servers, not Ramses. That was my assumption and the founder did not object.
- session-wrap's rollup came back empty, because every agent used its job id as `--session`. That is the job-run convention, so the gap is expected and not a bug.

## Open
1. J-2813, J-2815 and probably J-3950 show in_progress with no results. `job_queue` has no reopen command, so they need a manual reset. The replay scripts are built and rerunnable (`scratch/J-2815_replay.py`).
2. J-4036 was cut off when I stopped the run. Its re-judge process (`scripts/lab_rejudge_falcon3_J-4036.py`) was at 386 of 440 and was still running. Next step: when it finishes, read `docs/lab/J-4036_data/report.json`, then done or left_open. The data dir was committed partial, so re-add it afterward.
3. Left-open jobs the overnight loop started but did not finish: J-4051, J-2928, J-2943, J-3344, J-3662, J-3325. Next step: check each one's status in the queue.
4. Still-running orphan lab processes: `lab_commitment_judge_variants.py --max-hours 7` and two J-3325 `judge_run.py` runs. They load the hubs. [OPEN] Stop them, or let them finish before the next Du boot.
5. Uncommitted code edits: `core/memory_service.py`, `nodes/critic_node.py`, `scripts/liveness_audit.py` and several `scripts/_test_*.py`. The tests are probably J-4051's unfinished work. Next step: review the diffs and commit by explicit path.
6. J-3926, J-3309 and J-3956 need the judge on Ramses, so they were left open. They can run now that the founder is not gaming.
7. Jobs that need Du down and were not reached: J-3919 part 2, J-2829. Du is being shut down now, so a Du-down window is open.
8. Founder calls: D-0375 Phase 2 (J-2068), and the D-0415 defeater question (J-2093).

## Warnings
- Du was live during the overnight loop. Code changes made then (J-2814, J-4026, J-4030) are restart-gated and not live until the next boot.
- The shared index was stale at commit time (staged deletions of files that exist on disk). I re-added those paths, so nothing was lost, but check `git status` before any bare commit.
- `docs/06. Just the Way You Are.mp3` and the two `.lock` files are untracked and were deliberately left out. Two other sessions' handoff files were also left out.

## Pointers
- Commit 03940bff.
- Workflow journals: `C:\Users\USER\.claude\projects\C--Nascence\4744a0c5-d4e4-4ad8-a737-14583b66b9b4\subagents\workflows\` (`wf_360d13e4-e89` wave 1, `wf_d4a0f718-4f0` wave 2, `wf_b9c99fa0-c3b` overnight).
- `docs/lab/J-4036_data/`, `docs/lab/J-3325_data/`, `scripts/lab_commitment_judge_variants.py`.
