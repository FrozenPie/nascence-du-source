---
name: deferred-reads-outlive-their-gates
description: "job-run spawns evidence reads with not_before floors guessed before a boot; after a long run nobody re-checks, so dozens sit READY unread. Check the dossier against the real boot."
metadata:
  node_type: memory
  type: feedback
  originSessionId: c0ec536c-d2e5-47d7-aa00-d9267439a61b
  modified: 2026-10-14T22:00:19.119Z
---

On 2026-10-15, six days into Du's record run (boot 10-09 08:36 NZDT), 94 of 125 date-gated
jobs had passed their not_before and were sitting in the READY pool; nothing had dispatched
them since the 10-10 job-run. Four more had 7-day floors set past the real boot. Ten of the 94
could not produce an answer (code merged after the boot, or they need a conversation Travis has
not had). Two waves of 17 Sonnet read agents each closed 34 of them in about two hours total
(F-2682; waves wf_1e77001e / wf_72595a29).

**Why:** job-run agents set `--not-before` as a calendar floor at spawn time, usually "today plus
7 days", without knowing when the next boot will happen. Once the date passes the job is
indistinguishable from any other ready job, and `job_run.py plan` does not say "this read's gate
is now met". The backlog looks like ordinary work rather than a harvest waiting to be picked.

**How to apply:** after any multi-day run, before a decide-review or when Travis asks "what's
ready", build the dossier: for every open job with a not_before, count rows since the boot in
each data file its briefing names (watch the ts key, some logs use t_req), and test each cited
commit with `git merge-base --is-ancestor <hash> <boot-commit>`. Three bins fall out: ready with
evidence, ready-dated but code not live (needs a restart), ready-dated but evidence absent
(needs a conversation or an event). Pull forward floors that assumed a later boot. Then run the
reads in plan-group chains of about 12, Sonnet, one worktree per group; reads produce no
commits, so Teardown is cleanup only. Expect each wave of 17 to open 4 to 6 new founder
decisions. See [[jobrun-parked-jobs-and-sweep-sizing]] for the wave-size rule and
[[safe-commit-stale-index]] for the commit step afterwards.
