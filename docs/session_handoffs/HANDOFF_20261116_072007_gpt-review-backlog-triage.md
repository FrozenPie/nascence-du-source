# GPT review exchange, then the in-progress backlog cut from 343 to 6

## Session timing
- **Session started:** 2026-11-16 04:57:30 UTC
- **Last message before wrap:** 2026-11-16 07:20:06 UTC
- **Wrapped:** 2026-11-16 07:20:07 UTC

(The started value is what the tool printed. The session was compacted once, and the first thought, T-0143, was logged before 04:57 UTC, so the real start is earlier. [INFERRED])

## Summary
Travis pasted GPT's overall analysis of Nascence; I checked its claims against the repo and wrote a full account for GPT (`docs/reviews/nascence_writeup_for_gpt_2026-11-16.md`). After GPT's reply Travis ruled that pending work comes before new work, so I triaged every `in_progress` job: 343 became 53 (290 were finished and never marked done), then 53 became 6 after adding a `release` command to the job-queue tool. Nothing is committed.

## Decisions
- No `/decide` ruling was made this session.
- Founder priority, stated by Travis in chat on 2026-11-16: "we have too much work still pending, we need to get as much done as we can before we can really trust where we are up to with all our ideas." Saved as memory `feedback_close_pending_before_new_work.md`. Reading it as a standing ordering preference is my interpretation, not his words.

## Builds
- `C:\Users\USER\.claude\skills\job-queue\job_queue.py`: new `release <id> --why "..."` (in_progress back to open, stores `release_why`, `released_at`, `released_from_started`, refuses a job that is not in_progress, logs `job_released`) and `done --note "..."`. Tested on a temp copy of the store with the live file's hash unchanged. `SKILL.md` in the same folder documents both. S-0327 resolved as applied.
- `docs/reviews/nascence_writeup_for_gpt_2026-11-16.md`: the checked account sent to GPT (corrections to its claims, current scale, design laws, UDMS real state, the three loops against the evidence, six questions).
- `docs/reviews/backlog_triage_2026-11-16.md`: the triage report plus the same-day addendum. Evidence: F-4844 (triage) and F-4845 (reconciliation), both verified.

## Findings
- F-4842, F-4843 (verified): checks of GPT's claims. Several of its figures (684 modules / 3,125 edges, rank 169, entropy 4.23 to 2.81, and others) exist only in UDMS commercial white papers or were not found at all; the UDMS cognitive-dynamics maths was parked by D-0195 on 2026-09-09; the AUROC 0.9549 label leaks its own latency feature. GPT also misread the topic anti-relock result: modal share fell from 97% to about 50% (F-4567), not to 0.5%.
- F-4844 (verified): of 343 in_progress jobs, 290 were finished work never marked done, mostly from the 11-05/06 build marathon and the 11-13 to 11-15 job-run waves, where work was committed from worktrees and the `done` call never reached the shared ledger. The triage script's "done by report or finding" rule was wrong for all 16 jobs it picked; none of those were closed.
- F-4845 (verified): the remaining 53. 46 released to open with a reason, 2 closed (J-3833 on F-4566; J-3654 on F-4571 and F-4572), 6 left in progress. Final counts at the time: done 3,639, open 450, in_progress 6.
- The slow judge hubs caused 8 of the 13 stalled jobs. J-4095 (urgency 4) was added to diagnose and restore judge hub speed.
- Ideas logged from GPT's replies: I-0159 (acceptance tests for the three loops), I-0160 (per-category outcome-conditioned confidence), I-0161 (bare-model house-style baseline), I-0162 (scaffolded versus self-directed availability).

## Open
1. **Ten reads are due now and were not run:** J-2502 (cat overhaul), J-3380, J-3394, J-3601, J-3716, J-3746, J-3880, J-3982 (layered goals Phase 0 gate), plus J-3411 and J-3855, where a commit already names each job. Next action: in a fresh window, one job-run wave of 10 or fewer; for J-3411 and J-3855 check what is left before redoing. Only J-2502 and J-3982 ask whether something changed in Du; the rest check that a change runs correctly.
2. **Eight labs interrupted by the judge hubs** (J-3447, J-3711, J-3083, J-3950, J-2928, J-3344, J-3662, J-4035) must not be retried before J-4095 is done. The job-queue tool has no dependency field, so a job-run wave has to exclude them by hand.
3. **Six jobs still in_progress.** J-3607, J-3653, J-3793 and J-4019 were started on 11-16 and may belong to another window [OPEN: check with `job_queue.py show` and the other windows before touching]. J-3218 is blocked by F-4092 and needs a design answer from Travis. J-3748 is a decision (whether to extend the decomposed-critic shadow), not work.
4. **The job-run planner still does not list idle in_progress jobs**, so the pool can refill after the next wave unless sessions call `release`. Not built, no job filed for it beyond the S-0327 note.
5. **The 450 open jobs are untriaged.** Many October analysis jobs are likely superseded [INFERRED from 9 of the in_progress set being superseded].
6. **Recommended order for what remains** is at the end of `docs/reviews/backlog_triage_2026-11-16.md`: closure producer first read (J-4079), teaching-to-synthesis Part 1 (J-4093), recall wager (J-4087; J-3899 and J-4078 need rulings), then the due reads.
7. **Nothing from this session is committed.** Untracked: both review docs and `docs/staged/teaching_to_synthesis_study.md` (not mine). The ledgers (`job_queue.jsonl`, `findings.jsonl`, `ideas.jsonl`, `thoughts.jsonl`, `session_events.jsonl`, `skill_suggestions.jsonl`) carry this session's rows uncommitted.

## Warnings
- Du's log ended with "Nascence shutting down" at 15:28 local on 11-16; Du may be down [OPEN: check the log line before any live read]. Gate figures in the addendum were taken with Du down.
- Model lanes in the GPT writeup were quoted from config, not checked as running.
- `findings_log.py record` hit a `PermissionError` on `os.replace` once (another process held `findings.jsonl`); the ledger was intact and a retry worked. Other windows are writing the same ledgers.
- A bulk loop over an id file fails silently on CRLF line endings ("No job J-xxxx"); strip `\r` first.

## Pointers
- `docs/reviews/backlog_triage_2026-11-16.md` — per-job detail and recommended order.
- `docs/reviews/nascence_writeup_for_gpt_2026-11-16.md` — the account given to GPT.
- `C:\Users\USER\.claude\skills\job-queue\job_queue.py` and `SKILL.md` — `release`, `done --note`.
- F-4842 to F-4845, T-0143, I-0159 to I-0162, S-0327, J-4095.
- Memory: `feedback_close_pending_before_new_work.md`.
