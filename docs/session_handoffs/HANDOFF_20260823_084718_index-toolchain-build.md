# Index toolchain built + first real use (2026-08-23 evening session)

## Summary
Started as a plan-index skill check, grew into building a full 9-skill toolchain for managing
Nascence's 56 plans from Claude Code (not part of Du — assistant tooling), then used that toolchain
for real: rescoped 5 stalled plans, ran a founder-decision questionnaire that ruled 8 of 11 open
questions, and built a job queue + this handoff system. Confirmed mid-session: at least one other
Claude Code window was concurrently active on this same project, editing ROADMAP.md, MEMORY.md, and
the overlap audit, and separately completed job J-0001 (the cognitive_geometry analyzer) — the
concurrency this handoff system and the job-queue's per-file design exist to handle isn't
hypothetical, it happened tonight.

## What changed

**9 skills built, all under `C:\Users\USER\.claude\skills\`** (moved OUT of `C:\Nascence\scripts` —
these are Claude Code assistant tools, not Du/Nascence code):
- `plan-index` — stage cross-check (ROADMAP vs plan doc vs memory), `Open ⚖` decision count column
- `plan-files-audit` — does a plan's claimed code/data actually exist (CONFIRMED/MISSING/AMBIGUOUS)
- `plan-liveness` — does evidence fire and has it been read (GATE-MET/NEVER-FIRED/STALE/+UNREAD)
- `memory-links` — typed-edge store (`_memory_edges.jsonl`) over plans/memory/files/decisions
- `decide` — ruling+defeater ledger (`docs/decisions.jsonl`), refuses a ruling with no defeater
- `decide-review` — presents open decisions as an `AskUserQuestion` batch, logs answers immediately
- `plan-snapshot` — append-only per-plan history (`docs/plan_snapshots.jsonl`) → stall/progress verdict
- `plan-maintain` — the one-call run order for all of the above, plus a lint step
- `job-queue` — urgency-weighted jobs, ready-vs-needs_input, lab-mode (Du-down-suited)
- `plan-sync` — for a DIFFERENT session to fold its own touched files into this index
- `session-wrap` / `session-resume` (this pair) — per-session timestamped handoffs

Shared module: `C:\Users\USER\.claude\skills\_plan_tools_common\common.py` (atomic edge I/O, path
normalisation) — built after a 7-agent audit found 18 real bugs across the first version of these
tools; all fixed same session (full report: `docs/reviews/index_skills_audit_2026-08-23.md`).

**Plans rescoped** (Current State section + concept-overlap check vs every newer plan): `idle_executive_plan`,
`cognitive_geometry`, `peer_correspondence_plan` (company half split to `docs/completed/peer_correspondence_company.md`),
`spatial_perception`, `investigation_deepening`. All 5 of plan-snapshot's original "stalled" bucket closed out.

**Decisions ruled tonight**: D-0001, D-0002, D-0004, D-0006, D-0007, D-0008, D-0010, D-0011, D-0012
(D-0012 completed by another window mid-session — check `decide.py show D-0012` for its actual
finding, not this note). **Still open**: D-0003 (peer challenge mechanism — Travis wants "maybe both,
a fork, tracked via indexing/tuples," not a binary pick, needs a real design pass), D-0005 (same
pattern, Improvement 2 vs memory_multiway_linking), D-0009 (investigation_deepening — explained but
not yet re-answered).

**Jobs queued** (`job-queue`, 5 seeded from tonight's rulings): J-0001 (cognitive_geometry analyzer —
DONE by another window), J-0002 (continuous_stream shadow-log read), J-0003 (consciousness_program
corrected-baseline re-run), J-0004 (journal pyramid shadow grounding-grader), J-0005 (music listening
regression trace). Check `job_queue.py list` for current status — don't trust this note.

**ROADMAP.md gained a Model Serving Inventory section** (live-verified port/model map, found a
cross-project port conflict risk on the shared 1080 Ti between this project and the separate
Sovereign Hub/FreshStart project — flagged, not resolved).

## Key findings
- The parser-bug pattern repeated 4+ times across different tools tonight: fixed-priority word/emoji
  lists beat leftmost-in-text position, generic checkmarks (✅) get misread as top-level status,
  negation ("not stalled") isn't handled, and a doc's OWN title-date can contaminate nearby status
  claims. All fixed with the same principle: leftmost-in-actual-text wins, not first-in-list.
- Travis's repeated response to binary-choice questions tonight (D-0003, D-0005) was "explore both,
  fork it, link via the indexing/tuple system with a stated reason why" — a real, recurring
  preference, not noise. Flagged as a future `/decide` enhancement (a genuine "parallel fork" decision
  type) rather than rushed into tonight's build.
- `plan-snapshot`'s ROADMAP-sourced backfill has a structural limit, not a bug: it reads ROADMAP as it
  exists TODAY, so fixing a bullet's emoji for current accuracy can erase real historical signal — no
  clean regex fix exists; documented in the SKILL.md instead of over-engineered around.

## Open threads
- D-0003, D-0005, D-0009 need Travis's continued input (see above) — good first candidates for
  `/decide-review` next time.
- The 5 queued jobs are real, unstarted (or one done — check) work, self-contained enough to run in a
  fresh window per `/job-queue`'s design.
- `docs/reviews/index_coverage.md` lists 10 unindexed source categories (9 more `docs/reviews/*.md`
  audit docs never harvested being the largest) — a real, scoped next project if someone wants it.
- This handoff/resume pair is brand new and unused until now — no track record yet on whether the
  format is actually useful in practice; revisit after a few real uses.

## Warnings
- **Confirmed concurrent sessions.** At minimum one other window is/was active on this project
  tonight, editing shared files (ROADMAP.md, MEMORY.md, plan_overlap_audit_2026-08-23.md) and
  completing queued jobs independently. Before trusting any "current state" claim in this handoff,
  cross-check against the live tools (`plan-index`, `decide list --open`, `job_queue.py list`) — see
  `/session-resume`'s own instructions.
- `docs/ROADMAP.md.bak-2026-08-23` is a stray backup in `docs/` root, not `docs/archive/` — harmless,
  but don't mistake it for a live doc if grepping broadly.

## Pointers
- Run `/plan-maintain` first in any new session touching plans — refreshes everything in one call.
- `docs/reviews/index_skills_audit_2026-08-23.md` — the full bug-audit report, useful before touching
  any of these tools' internals.
- `MEMORY.md` (Claude's memory index) has one-line pointers to every tool built tonight, each linking
  to a fuller `reference_nascence_*_tool.md` file.
