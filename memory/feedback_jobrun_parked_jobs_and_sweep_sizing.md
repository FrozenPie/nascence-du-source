---
name: feedback-jobrun-parked-jobs-and-sweep-sizing
description: job-run only sees status=open — ~54 parked in_progress jobs hid the real backlog; a 45-job sweep burned the 5h usage window (22 agents failed incl. Teardown); run waves of <=~10 and recover by hand
metadata:
  node_type: memory
  type: feedback
  originSessionId: 2315a7b3-9526-4ef6-b6e9-5b57b923a07f
  modified: 2026-10-03T01:41:24.795Z
---

**Rule 1 — the planner is blind to `in_progress`.** `job_run.py plan` tiers only `status=open`. On 2026-10-03 it showed
"2 ready" while 58 jobs sat `in_progress` (54 with no recorded activity for 3+ days, 23 for 7+). Most were restart-gated
reads whose gate had long cleared (Du restarted 09-25/09-28/09-29/09-30/10-03) — nobody ran them because nothing surfaces
them. Check idle-ness from `docs/session_events.jsonl` (last event whose ref/session/detail names the job), not from
`started`. `job_queue.py start` on an already-in_progress job is harmless (re-stamps `started`, logs an event), so takeover is safe.
**Closing policy that works:** if the read can't be completed yet, record the finding, spawn ONE successor with a real
`--not-before`, then `done` the parked job (checkpoint + dated successor) — never leave it `in_progress`.

**Rule 2 — size sweeps to the usage window, not the agent cap.** Full-depth Tier-3 agents (read-in-full convention)
cost ~440k subagent tokens each in the sweep (11.85M for 25 finished jobs, ~58 min wall clock). A single 45-job dispatch
hit the account's 5-hour session limit mid-run: 20 job agents failed ("You've hit your session limit") plus the
Teardown and Report agents, so no worktree merge-back ran. I had quoted "~25-30 agents" and the filter actually
selected 40+5 — state the REAL count and token estimate before launching, and dispatch in waves of <=~10 jobs with an
"economy" paragraph in every prompt (≈30 tool calls, reuse existing reader scripts/findings, no new tooling, <250-word
summary). Skip lab_experiment jobs while Du is live (they load the model servers).

**Measured outcome (2026-10-03):** the same kind of job with an ECONOMY paragraph in the prompt cost ~255k tokens/job
(two 9-job waves = 2.3M each, ~45-50 min wall clock each, 0 failures) vs ~440k/job unconstrained. After the limit hit,
the 20 failed jobs were finished as two waves of 9; the parked in_progress pool went 58 -> 16 and spawned ~39 dated
successor jobs. Also: a dispatch premise ("Du is live") can go stale mid-run (Du shut down 08:15 after a 06:54 boot) —
re-verify with a process check before baking liveness into prompts, and tell agents to verify rather than trust it.

**Rule 3 — recovering a workflow whose Teardown died.** (1) `git worktree list` + `git rev-list --count master..jobrun/<key>`
and `git -C <wt> status --porcelain` to see which branches have commits / uncommitted partial work; (2) make the
consolidation commit of the shared tree's ledger + plan-doc output FIRST (explicit path list from `git diff --name-only`)
so merge-back isn't refused for "local changes would be overwritten"; (3) `worktree_dispatch.py merge-back` each branch with
commits, in order; (4) `cleanup --force` the zero-commit worktrees so the next dispatch's Setup starts fresh; (5) re-dispatch
only the failed jobs.

**Why:** Travis re-runs `/job-run` repeatedly across a day (often with context like "Du is down"/"He is back up") and expects a
clean report each time; the first Du-live sweep both surfaced real findings (D-0330..D-0335, esp. D-0334: conversational
dispatch precision) and cost a usage-limit hit. **How to apply:** before any /job-run with a big in_progress pool, count,
estimate tokens (~250-450k per deep job), propose waves; always check the workflow's `failures` block and run the Teardown by hand if it failed.
Related: [[reference_nascence_plan_index_tool]], [[ops_claude_code_job_object_kills_servers]].
