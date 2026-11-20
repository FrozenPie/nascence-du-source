---
name: feedback-decide-review-stale-framing
description: "Before putting a /decide question to Travis, scan for newer findings/jobs that cite it — a decision's text freezes when opened; D-0330 was nearly ruled on a superseded premise (fix (b) vs the chapters seed scan). Re-ask, don't log a stale pick; ambiguous free-text answers get one clarifying question"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 2315a7b3-9526-4ef6-b6e9-5b57b923a07f
  modified: 2026-10-04T02:05:28.873Z
---

When running `/decide-review`, the open decision's own `question` text is a snapshot from the moment it was opened. Follow-up reads
spawned from it (and builds merged since) can change what it is really asking.

**Why:** 2026-10-04 — I presented D-0330 (night-sleep length) from its own text, which blamed the fix (b) shadow; Travis picked "Accept". Only
afterwards did I find F-2374/F-2377 (J-1682, verified): the chapters seed scan is 55% of a night sleep and fix (b) only ~6%, and D-0336's cost line
was corrected by F-2379. Similar drift on D-0334 (the guard it asked for had already shipped), D-0335 (the F-2305 defect already fixed) and D-0338
(the lone judged break was a mislabel). I caught it before logging, told Travis plainly, and re-asked with corrected facts; he re-chose with
the true picture. His trust in recommendations is high (he took the recommended option on nearly every question), so the framing I hand him matters.

**How to apply:** before each batch, run a read-only scan of `docs/job_queue.jsonl` and `docs/findings.jsonl` for the decision ID (and for the
source finding's topic), read every hit newer than the decision, and put corrected facts in the question. Also check whether a `needs_input` job is
gated on the decision (J-1595/J-1685/J-1702/J-1748/J-1753 were): job status cannot be reset, so after the ruling close the gated job as superseded
and spawn a `ready` successor carrying its briefing with the gate lifted. If an answer was already given on a superseded premise, do not log it — say
so and re-ask. If an "Other" free-text answer is ambiguous (D-0345: "Needs a look then a log to add/check the object in a later session"), log his
words verbatim only after one short clarifying question that changes what gets built. Also: re-verify "is Du up / is the backup still there" right
before any action that depends on it (the D-0339 archive turned out to be the only copy once the original rotated away).
Related: [[feedback_decide_review_scope]], [[feedback_decide_batch_id_mixup]], [[project_nascence_20261003_sweep_outcomes]].
