---
name: feedback-archaeology-not-bug-hunting
description: "FreshStart archaeology digs investigate information about the past — don't frame findings as bugs to fix"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 6018d4ef-528c-46a3-b67e-af8d7de710a7
  modified: 2026-08-23T20:24:04.669Z
---

FreshStart's archaeology work (see [[project-freshstart-archaeology-synthesis-2026-08-24]] and
[[reference-freshstart-archaeology-index]]) is historical investigation — cataloguing what existed,
what happened, what's live/dead/superseded, tracing lineage. It is explicitly NOT bug-hunting, even
when a finding looks like something that would crash or misbehave (e.g. the ARCHIMEDES
council-trigger location-string mismatch, F-0080, or the two confirmed code bugs found in the
Encyclopedia-audit pass).

**Why:** Founder corrected this directly (2026-08-24, right after a 7-pass archaeology effort
wrapped): "there are no bugs to find in this. Only information about the past we want to
investigate. The things we find here will be investigated for future and current projects
eventually." The findings are raw material for later evaluation, not defects demanding triage —
whether something ever gets "fixed" is a separate, future decision, not an implication the
archaeology finding itself should carry.

**How to apply:** When writing up or summarizing archaeology findings (in `docs/archaeology/*.md`,
chat summaries, `PROGRESS.md` entries), describe what was found and what it means
historically/structurally — not "this is broken, here's the fix." Reserve "bug"/"fix" framing for
when the founder explicitly shifts from archaeology into implementation/triage on a specific item.
Findings still feed job-queue/idea-log as open questions worth surfacing — that's fine, surfacing is
part of preservation — just don't editorialize them as a backlog of defects.
