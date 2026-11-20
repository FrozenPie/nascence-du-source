# Backlog triage: the in-progress job pool, 2026-11-16

**By:** Claude (session 690f9a1f), at Travis's request after the GPT review exchange (T-0143). **Scope:** every job with status `in_progress` in `docs/job_queue.jsonl`. No Du code or data was touched. Job state was changed only through `job_queue.py done`.

## Result

| | Before | After |
|---|---|---|
| in_progress | 343 | 53 |
| done | 3,347 | 3,637 |
| open | 404 | 404 |

290 jobs were finished work that had never been marked done. Almost all date from the 11-05/06 build marathon (the prompt-registry rulings D-0530 to D-0658) and the 11-13 to 11-15 job-run waves: the work was committed from worktrees and the `done` call never reached the shared ledger.

| Bucket | Count | Action |
|---|---|---|
| 1 Done, not closed | 290 | Closed |
| 2 Waiting on a gate or date | 29 | Left as is, listed below |
| 3 Stalled or interrupted | 13 | Left as is (the tool has no way to return a job to open) |
| 4 Unclear or possibly active in another window | 11 | Left as is |

## Method

`triage.py` (session scratchpad, read-only) matched each job against: commits whose subject starts with the job id or is a job-run worktree merge naming it, dated on or after the job's start; findings citing the id; `docs/lab/` files or directories named for it; successor jobs; and its own `gate` / `not_before` fields.

Hand checks before closing anything:

- 16 random jobs from the commit bucket: 16 of 16 had a commit whose subject and files match the job title (code files under `core/`, `nodes/` or `scripts/`).
- 11 commit subjects flagged for words like "fail" or "cannot": all were descriptions of the fix, none a failed job.
- 11 jobs the script set aside as "partial commit" (subject mentioned a phase or step): in each the phase is the job's own scope and a build commit exists. Closed.
- 13 jobs with a finding but no commit of their own: 9 have a **verified** finding saying the work is already in master through another job or was superseded (J-2837, J-2843, J-2856, J-2879, J-2974, J-2990, J-3056, J-3068, J-3481). J-3571 is in force in `CLAUDE.md` (the session warm-up paragraph cites it). These 10 were closed.
- 16 jobs the script called "done by report or finding": **none closed.** Reading the findings showed partial or not-run results. They are in buckets 3 and 4 below. The script's rule was wrong for this group.

Closed set: 269 by commit, 11 phase-scoped commits, 10 superseded or in force. A build job counted as done when the build was committed; whether the build has been loaded and read live is a separate read job, not this one.

## Bucket 2: waiting on a gate or date (29)

These are mostly post-restart reads. They sit in `in_progress`, so the job-run planner cannot see them. I did not evaluate whether each evidence gate is now met.

- **Evidence-file gate since boot (17):** J-2354, J-2602, J-2603, J-2611, J-2615, J-3385, J-3432, J-3595, J-3601, J-3613, J-3649, J-3702, J-3725, J-3743, J-3746, J-3880, J-3986.
- **Live-hours gate (4):** J-2502 (168 h, cat overhaul), J-3380 (8 h), J-3600 (168 h), J-3716 (24 h).
- **Date only (8):** J-2220 (11-27), J-2644 (11-29), J-2951 (11-17), J-3558 (11-17), J-3394 (11-14, passed), J-3411 (11-16), J-3855 (11-16), J-3982 (11-16, layered goals Phase 0 gate).

Date already passed, worth checking first: J-3394, J-3411, J-3716, J-3725, J-3743, J-3746, J-3855, J-3982.

## Bucket 3: stalled or interrupted (13)

**No trace of work (5):** J-2813 (Emotion farewell replay), J-2829 (ConsolidationNode persona block), J-3471 (CLAUDE.md UDMS ranker paragraph), J-3574 (UDMS utf-8-sig), J-3736 (dead `latency_status`).

**Interrupted with a partial result on record (8):** nearly all stopped because the judge hubs were too slow or congested.

| Job | Finding | State |
|---|---|---|
| J-3447 | F-4728 | Partial noise floor, 6 of 20 gists |
| J-3711 | F-4730 | Partial, 41 of 65 chapters judged |
| J-3083 | F-4732 | Partial gist-fidelity grader result |
| J-3950 | F-4744 | Partial anchoring replay |
| J-2928 | F-4773 | Not run, lane :11441 congested; script ready |
| J-3344 | F-4786 | Not runnable at pre-registered scale on live hubs |
| J-3662 | F-4806 | Interim AUC 0.634 on 72 of 367 cycles |
| J-4035 | F-4838 | Not run, both judge hubs timed out |

## Bucket 4: unclear or possibly active (11)

- **Started today, may belong to another open window:** J-3607, J-3653, J-3793.
- **Lab data on disk, no result recorded:** J-2943, J-3325 (its data files are modified and uncommitted), J-4036 (cut off).
- **A finding exists but does not settle the job:** J-2815 (F-4661), J-3218 (F-4092: the urgency field cannot carry the function as the schema stands), J-3654, J-3833.
- **A decision, not work:** J-3748 (whether to extend the decomposed-critic shadow).

## What this shows

1. The in-progress pool was overstated by a factor of six. The real unfinished pool is 53, not 343.
2. The slow judge hubs are the single biggest cause of genuinely stalled work: 8 of 13.
3. 29 read jobs are invisible to the planner because they are parked in `in_progress`. This is the same fault found on 2026-10-03.
4. The 404 open jobs were not triaged here. 253 of them are analysis and 78 need a founder answer.

## Addendum, same day: the remaining 53 reconciled

| | After triage | After reconciliation |
|---|---|---|
| in_progress | 53 | 6 |
| open | 404 | 450 |
| done | 3,637 | 3,639 |

(Another window started J-4019 from open during this pass, which is why the columns do not sum by 53.)

**Tool fix (S-0327, applied).** `job_queue.py` now has `release` (in_progress back to open, reason stored, refuses a done job, logs `job_released`) and `done --note`. Tested on a temp copy of the store with the live file's hash unchanged. The job-run planner still does not list idle in_progress jobs; that part is not done.

**Released to open: 46.**

- **Due now, ready to read (10):** J-2502 (cat overhaul, 330 of 168 live hours), J-3380, J-3394, J-3601 (81 of 60 rows), J-3716, J-3746 (322 of 30 rows), J-3880 (21 of 10 rows), J-3982 (layered goals Phase 0 gate). J-3411 and J-3855 are due but a commit already names each; check what is left before redoing.
- **Not due, now showing as deferred (19):** J-2220 (11-27), J-2644 (11-29), J-2951 and J-3558 (11-17), J-3385 (143 of 150 rows), J-3986 (210 of 300), J-2602 (65 of 150), J-3600 (48 of 168 live hours), J-3702 (8 of 40), J-2615 (3 of 20), J-2603 (1 of 10), and eight with no evidence rows yet: J-2354, J-2611, J-3432 (gate file missing), J-3595, J-3613, J-3649, J-3725, J-3743. Gate figures are from the tool's own `gate_status` at the time of the pass, with Du down.
- **Stalled, no trace (5):** J-2813, J-2829, J-3471, J-3574, J-3736.
- **Interrupted by the judge hubs (8):** J-3447, J-3711, J-3083, J-3950, J-2928, J-3344, J-3662, J-4035. Each carries a note not to retry before **J-4095**, a new job to diagnose and restore judge hub speed. The tool has no dependency field, so a job-run wave must exclude these eight by hand until J-4095 is done.
- **Cut off (4):** J-2943, J-3325, J-4036, J-2815.

**Closed: 2.** J-3833 (the read was done, F-4566) and J-3654 (analysis recorded, F-4571, F-4572).

**Left in progress: 6.** J-3607, J-3653, J-3793 and J-4019 were started today and may belong to another open window. J-3218 is blocked by its own verified finding (F-4092: the urgency field cannot carry the function as the schema stands) and needs a design answer. J-3748 is a decision, not work.

**Operational or developmental.** Of the 10 due reads, J-3380, J-3394, J-3601, J-3716, J-3746, J-3855 and J-3880 ask whether a change runs correctly. J-2502 and J-3982 ask whether something changed in Du. J-3411 is instrument calibration. A pass on the first kind is not a result of the second kind.

## Recommended order for what remains

1. **Closure producer first read** (J-4079, at 40 verdicts), with the judge-agreement shortfall (0.737 against 0.75) addressed, not waved through.
2. **Teaching-to-synthesis Part 1** (J-4093). Read-only, no hubs needed for delivery counting.
3. **Recall wager** (J-4087 built; J-3899, J-4078 need rulings).
4. **Bucket 2 reads whose date has passed**, in one job-run wave of 10 or fewer.
5. **Judge hub speed** before any of the 8 interrupted labs is retried; retrying them on the current hubs will fail again.
6. **Frozen scorecard definitions** (`scripts/humanity_scorecard.py` v1 is the start).
7. Then a second triage pass over the 404 open jobs: many analysis jobs from October are likely superseded the same way 9 of these were.
