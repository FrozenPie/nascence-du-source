---
name: health-check-approach
description: "The right diagnostic sequence for \"sim not producing output\" — DB queries and log tail, not file listing"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: bbc5728f-50a7-4544-87d8-9b21ad5344fc
---

When the sim looks stuck or isn't producing writings, run this sequence:

1. Read the 3 fast-start files (CLAUDE.md, activeContext.md, SESSION_HANDOFF.md)
2. Check spirit_actions status distribution: `SELECT status, COUNT(*) FROM spirit_actions GROUP BY status`
3. Check FAILED action types: a high count of FAILED with action_type='PENDING' means spirits are dying before LLM assigns an action — veto or infrastructure issue, not content issue
4. Check most recent Library files by date to find WHEN output stopped
5. Check pulse_live.log tail for the actual error/veto message
6. Check Ramses connectivity: `Test-NetConnection LAN-HOST -Port 11434`

**Why:** The Library folder contains both real spirit writings (TAB_/PROJ_/GUT_) and Gutenberg book cache files (gutenberg_*.md). The cache files update even when the sim is stuck — don't mistake cache activity for spirit output. Always check file dates on TAB_/PROJ_/GUT_ specifically.

**FAILED/PENDING ratio is the key signal:** 4,123 FAILEDs vs 2,885 COMMITTEDs (May 2026 session) indicated a systemic block, not normal noise. A healthy sim should have FAILEDs well below COMMITTEDs.
