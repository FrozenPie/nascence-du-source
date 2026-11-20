# Memory store migration (D-0126), continuing from the Judge1/Control Panel session

## Session timing
- **Session started:** 2026-09-02 01:50:50 UTC
- **Last message before wrap:** 2026-09-02 04:44:44 UTC
- **Wrapped:** 2026-09-02 04:44:46 UTC

## Summary

Same session as HANDOFF_20260902_041735_judge1-repoint-control-panel-bug.md (read first — Judge1/ground_thought/Control Panel work) | wrap resumed: real work continued after first wrap | founder moved to S-0025 (skill bug filed during first wrap), fixed | then D-0126 (founder ruling): migrated toolchain's real memory store from stale project dir to the dir Claude Code's built-in auto-memory reads

## Decisions

- D-0126: founder ruled "full migrate" on F-0687 (toolchain's real memory store — 255+ files, live _memory_edges.jsonl graph — lived at C--FreshStart\memory, invisible to Claude Code's built-in auto-memory, which reads C--Nascence\memory) | Executed: copied 254 non-colliding files C--FreshStart\memory→C--Nascence\memory | hand-merged 2 real collisions (MEMORY.md, this session's own handoff memory file) | repointed common.py's MEMORY_DIR to derive from ROOT (same _project_slug() helper S-0025 added) | fixed plan_index.py's own separate hardcoded copy of same constant to reference common.py's instead | C--FreshStart\memory left in place untouched, frozen backup, not deleted | verified via full /plan-maintain run against new location | Defeater: revisit if any tool found still reading old C--FreshStart\memory location directly — symptom: plan-index/memory-links/decide entry looks stale despite real update

## Fixes

- ~/.claude/skills/_plan_tools_common/common.py (S-0025): PROJECTS_DIR (used only for session-transcript timing lookups in session_timing()) was hardcoded to MEMORY_DIR.parent (stale C--FreshStart project dir) — no current session's transcript could be found | Fix: added _project_slug() helper replicating Claude Code's ':'/'\'/'.'→'-' project-folder naming convention, derived PROJECTS_DIR from ROOT via it, kept LEGACY_PROJECTS_DIR (old literal) as fallback for pre-move session ids | Verified both paths live: this session's own transcript now resolves real timestamps; a 2026-08-23 FreshStart-era session id resolves via fallback
- ~/.claude/skills/_plan_tools_common/common.py (D-0126): MEMORY_DIR (left untouched at S-0025 fix time, pending founder call) now also derives from ROOT via same helper | LEGACY_MEMORY_DIR keeps old literal | LEGACY_PROJECTS_DIR fixed to reference LEGACY_MEMORY_DIR.parent explicitly, not MEMORY_DIR.parent — that expression's meaning silently changed once MEMORY_DIR got repointed (else would have collapsed to equal new PROJECTS_DIR)
- ~/.claude/skills/plan-index/plan_index.py (D-0126): had own separate hardcoded copy of C--FreshStart\memory literal, not derived from common.py's constant, despite file already importing common.py as ct | Fix: replaced with direct reference to ct.MEMORY_DIR — duplicate literal was exactly the drift that caused original split; eliminating it (not just updating value) closes root cause, not symptom
- ~/.claude/skills/session-wrap/session_handoff.py: transcript-not-found warning message updated to name both new PROJECTS_DIR and LEGACY_PROJECTS_DIR path it now also checks

## Findings

- F-0687 [verified]: toolchain's real memory store — 255+ files, live _memory_edges.jsonl graph, actively written by every /plan-maintain run — always lived at C--FreshStart\memory, not C--Nascence\memory (what Claude Code's built-in auto-memory reads, derived from project's current cwd) | Confirmed by: file counts (255 vs ~6 pre-migration — far more) | recency (FreshStart files actively modified same-day pre-migration) | session-transcript-folder cross-check (49 old transcripts under C--FreshStart vs 11 current under C--Nascence — more under old) | Practical effect before D-0126: toolchain's explicit tools (memory-links, session-resume, decide, plan-index) unaffected — read MEMORY_DIR by absolute path; only PASSIVE auto-loaded context at fresh-session start was thin, missing whole real history

## Open

1. J-0496 (needs_input, carried over from first handoff, unchanged): should scripts/supervisor.py's watchdog also auto-heal CPU judge tier, not just rely on launch_servers.ps1 to start it once? | Next: founder ruling via /decide
2. Migration housekeeping (not filed as job, low priority): C--FreshStart\memory sits frozen/unused, still a full backup — no action needed unless disk space/clutter becomes concern | if anything later found still reading it directly, re-grep "C--FreshStart" across ~/.claude/skills/*.py (D-0126's own defeater, not a new open item)

## Warnings

- ~/.claude/skills/_plan_tools_common/common.py's MEMORY_DIR, EDGES_PATH, PROJECTS_DIR all changed value this session (D-0126/S-0025) — any note/memory/prior-session recollection citing OLD C--FreshStart\memory path as toolchain's real store location is now stale | new canonical location: C--Nascence\memory (i.e. wherever project's ROOT actually is — follows ROOT automatically if it changes again)
- Backups of both memory dirs as they stood immediately before D-0126 migration saved under this session's scratchpad (C:\Users\USER\AppData\Local\Temp\claude\C--Nascence\cf28a05a-aaeb-4471-aeda-fe2ac6d2ade0\scratchpad\memory_migration_backup\) — scratchpad is session-temporary, not a permanent backup location; copy may no longer exist if migration needs audit/revert later
- All other warnings from HANDOFF_20260902_041735_judge1-repoint-control-panel-bug.md (local CPU tier now running, left_lane.py's partial repoint scope, Control Panel [1] Full Start now fixed) still apply unchanged — this handoff covers only what happened after that one

## Pointers

- HANDOFF_20260902_041735_judge1-repoint-control-panel-bug.md — first half of this same session
- ~/.claude/skills/_plan_tools_common/common.py — MEMORY_DIR/PROJECTS_DIR and their LEGACY_ counterparts
- ~/.claude/skills/plan-index/plan_index.py — now references ct.MEMORY_DIR instead of its own copy
- C:\Users\USER\.claude\projects\C--Nascence\memory\ — new canonical memory store
- C:\Users\USER\.claude\projects\C--FreshStart\memory\ — frozen backup, not to be written to going forward
