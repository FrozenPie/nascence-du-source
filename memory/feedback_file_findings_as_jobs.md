---
name: feedback-file-findings-as-jobs
description: "Actionable items surfaced during a working session (triage synthesis, ad-hoc discoveries, \"do this before X\") must be filed into job-queue, not just stated in chat."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 5008482f-de41-4dd5-9bed-63c52124f514
  modified: 2026-08-23T12:53:29.389Z
---

When a session surfaces actionable work — a triage priority list, an ad-hoc discovery mid-task, a
"this needs doing before restart" observation — it must be filed as a real job-queue entry
(`job_queue.py add`/`spawn`), not just reported as chat prose. Founder correction, 2026-08-24, given
directly after a pre-restart triage session where urgent/nice-to-have/low-priority findings were
synthesized in chat.

**Why:** This mirrors the whole Nascence indexing toolchain's own founding principle — thought-log,
idea-log, findings-log, and gauge-check all exist specifically because things "being talked about"
evaporate once a conversation window closes, while a job-queue/decide/log entry persists and is
cross-referenced. A triage synthesis that only lives in chat text is exactly the kind of finding this
toolchain was built to stop losing. See [[reference-nascence-plan-index-tool]] and
[[reference-nascence-idea-findings-logs]] for the sibling pattern this generalizes.

**How to apply:** Any time I produce a prioritized list of things to do (urgent/soon/later, or
"before you restart X do Y") — even if some items already have job-queue ids — the synthesis and any
newly-surfaced item without an id should get filed via `job_queue.py add` or `spawn` (with the right
`source`/`plan`/`category`/`autonomy` fields for cross-referencing) before or alongside reporting it
in chat, not instead of. This also applies inside dispatched background agents doing real
plan-domain work (see [[project-nascence-nurse-rounds-skill]]'s Tier 3 runbook, which already
requires "don't leave a finding as prose, spawn it") — the same discipline, just now explicit for the
orchestrating session's own synthesis too, not only sub-agent findings.
