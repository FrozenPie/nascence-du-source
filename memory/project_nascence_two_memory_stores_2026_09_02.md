---
name: project-nascence-two-memory-stores-2026-09-02
description: Claude's built-in auto-memory (C--Nascence\memory) and this toolchain's real memory store (255+ files) were two separate, disconnected directories until D-0126's full migration reunited them here.
metadata:
  type: project
  originSessionId: cf28a05a-aaeb-4471-aeda-fe2ac6d2ade0
  sessionStarted: 2026-09-02T01:50:50Z
  modified: 2026-09-02T04:38:19.185Z
---

While fixing S-0025 (session_handoff.py's transcript lookup hardcoded to the stale `C--FreshStart` project dir), found a bigger, adjacent split: this toolchain's real memory store (`~/.claude/skills/_plan_tools_common/common.py`'s `MEMORY_DIR`, and `plan_index.py`'s own copy of the same constant) had always lived at `C:\Users\USER\.claude\projects\C--FreshStart\memory\` — 255+ files, a live `_memory_edges.jsonl` graph, actively written by every `/plan-maintain` run. But Claude Code's own **built-in** auto-memory system loads from `C--Nascence\memory\` instead, since that's what it derives from this project's actual cwd (`C:\Nascence`) — so that folder held only a handful of files, and every fresh session's passive context had been blind to the full 255-file history (every `feedback_*`, `ops_*`, `project_*` entry) since this project's cwd moved from `C:\FreshStart` to `C:\Nascence`. Full finding: F-0687.

**Resolved 2026-09-02 (D-0126, founder ruling: full migrate).** All 254 non-colliding files copied from `C--FreshStart\memory` into `C--Nascence\memory` (this directory); the 2 filename collisions (`MEMORY.md`, this session's own handoff memory file) hand-merged rather than overwritten. `common.py`'s and `plan_index.py`'s `MEMORY_DIR` repointed to `C--Nascence\memory` so all future writes land here too — no more drift. `build_edges` re-run against the new location and verified. `C--FreshStart\memory` was deliberately left in place, untouched, as a frozen historical backup rather than deleted (reversibility over tidiness on a one-way data move).

See [[reference_nascence_session_handoff_tools]] and [[reference_nascence_plan_index_tool]] for the tools that depend on `MEMORY_DIR`'s new location.
