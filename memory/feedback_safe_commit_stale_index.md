---
name: feedback-safe-commit-stale-index
description: After job-run's safe_commit.py commits a path (esp. --new-file), the SHARED .git/index is stale for it; a later bare `git commit` in C:\Nascence deletes/reverts that file. Run `git add <path>` first. Hit for real 2026-10-08 (F-2570, S-0278).
metadata:
  type: feedback
---

**safe_commit.py leaves the shared index stale.** It builds the commit against a private index and
only syncs the working tree. For a `--new-file` commit the path then shows as `D ` (staged deletion)
in `git status`, and the next ordinary bare `git commit` in the shared tree removes the file from
HEAD. 2026-10-08 04:05: ad72313 added `scripts/dedup_reclaim_D0357.py`, my wave-1 "ledgers and plan
notes" commit 49bcfbb deleted it (`6 files changed, 637 deletions`), restored by 0de972d.

**Why:** the private-index design (F-2055) is right for the race it closes, but the shared index is
what every later bare commit reads, and the end-of-wave ledger commit is exactly such a commit.

**How to apply:** before ANY bare `git commit` in C:\Nascence, read `git status --short` and treat
an unexpected `D ` or `M ` on a path you did not edit as a stale index, not a real change — `git add
<that path>` (never reset/checkout) so the index matches HEAD+disk, then commit. After using
safe_commit yourself, `git add <path>` immediately. Fix proposal filed as S-0278 on [[job-run]];
related: [[feedback-jobrun-parked-jobs-and-sweep-sizing]], [[feedback-my-failure-modes]].

**2026-10-17 recurrence (job-run, J-2339):** the same stale `docs/ROADMAP.md` (safe_commit `working_tree_synced=false`, index showing `M `) also blocked every `worktree_dispatch.py merge-back` in the batch with git's "local changes would be overwritten by merge". Fix that worked: write `git show HEAD:<path>` bytes straight to the file, `git add <path>`, confirm `git diff HEAD -- <path>` is empty, then merge. Check this BEFORE the Teardown phase of any job-run; a Tier 2 safe_commit on ROADMAP.md is the usual trigger.
