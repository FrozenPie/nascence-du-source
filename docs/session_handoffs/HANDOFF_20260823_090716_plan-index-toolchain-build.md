# Session: Built the plan-index toolchain from scratch (plan-index, plan-files-audit, memory-links prototype)

## Session timing
- **Session started:** 2026-08-23 01:23:03 UTC
- **Last message before wrap:** 2026-08-23 09:07:13 UTC
- **Wrapped:** 2026-08-23 09:07:16 UTC

## Summary

Started from a founder ask ("index Nascence plans like Du's own transit map") and built three tools
from nothing over the course of the session: `/plan-index` (stage cross-check across ROADMAP/plan
docs/memory), `/plan-files-audit` (plan claims vs. real filesystem), and `/memory-links` (a
prototype typed-edge store modeled directly on `core/memory_edges.py`). Along the way, ran a
plan-index memory-fill pass (0/56 missing), a 5-cluster cross-domain overlap audit (15 findings, 9
fixed), and found + fixed 6 real bugs across the toolchain (3 in `plan_index.py`'s stage detection,
1 stale doc line, 1 in the overlap-audit parser). By the end of this session, a **second, concurrent
session** ("the other chat," confirmed via on-disk file-change notices during this session's final
turns) had picked up the same tools and substantially extended them — see Warnings below before
trusting any specific count this handoff cites as still current.

## What changed

- **Built `C:\Nascence\scripts\plan_index.py`** + **`~/.claude/skills/plan-index/`** — cross-checks
  every `docs/plans`/`docs/staged` plan's stage against ROADMAP.md, its own Status line, and its
  memory file; writes `project_nascence_plan_index.md`. Found and fixed 3 real bugs during this
  session: negation blindness (`"not built"` read as `"built"`), emoji picked by fixed list-order
  instead of leftmost text position, and an emoji-scan window wide enough to bleed into unrelated
  nearby text (tightened 400/200 chars → 80).
- **Ran a memory-fill workflow**: wrote all 49 previously-missing `project_nascence_<slug>.md`
  memory files (read from source, not fabricated), fixed 8 ROADMAP.md links (backed up first to
  `docs/ROADMAP.md.bak-2026-08-23`), resolved the T4 Watershed stage mismatch.
- **Investigated and resolved 3 more stage mismatches** (`curiosity_goals_dreams`,
  `transport_manager`, `world_census`) — all were tool bugs, not real disagreements; one also needed
  a stale `Status:` line fixed directly in `docs/archive/world_census.md`.
- **Built and ran a 5-cluster cross-domain overlap audit** —
  `docs/reviews/plan_overlap_audit_2026-08-23.md`, 15 findings (5 DUPLICATE, 2 CONFLICT, 8
  SHARED-DEPENDENCY/coordination issues). Fixed 9 of 15 this session: verified the Ramses port 11441
  conflict live (`command-r7b` really is up — corrected `hud2_visual.md` and
  `ramses_second_tier.md`), fixed stale status rows in `friction_and_self_evidence_plan.md` and
  `pulse_manager_wiring_plan.md`, flagged `euclidean_memory_plan.md`'s overdue retrial, added naming
  disambiguation to `lane2_lab.md`/`emissary_lane2_cognition.md`, added the missing
  `becoming-symbol` ontology entry to `identity_estate.md`, added uncited-dependency cross-references
  to `shore_upgrade.md`/`study_upgrade.md`/`wood_upgrade.md`/`garden_upgrade.md`/`hud2_visual.md`/
  `idle_executive_plan.md`/`self_interrogation.md`.
- **Built `C:\Nascence\scripts\plan_files_audit.py`** + **`~/.claude/skills/plan-files-audit/`** —
  extracts every file a plan claims (backtick-quoted `.py`/`.jsonl`/`.json`) and checks it against
  the real filesystem. First run found 13 MISSING code-file claims; all 13 individually verified
  this session: **3 were naming drift** (`lane2_the_witness` → real impl is `core/lane2.py`;
  `garden_upgrade`'s ledger → folded into `core/garden.py`; `thermal_causality`'s ledger → folded
  into `core/thermal.py` — all 3 corrected in their plan docs), **1 was a cross-project reference**
  (`emissary_lane2.md` citing a real file that lives in `C:\FreshStart`, not Nascence), **9 are
  genuinely unbuilt** by confirmed deliberate decision.
- **Built `~/.claude/skills/memory-links/`** (`build_edges.py` + `query.py`) — a prototype typed-edge
  store over Claude's own memory files/plans/reports, schema and discipline ported directly from
  `core/memory_edges.py` (every edge needs citable provenance; deterministic harvest, never
  LLM-guessed). First run: 438 edges from 4 sources (memory-file wikilinks, `originSessionId`
  frontmatter, the `project_nascence_<slug>.md` naming convention, the overlap audit's 34 findings).
  Found and fixed a real parsing bug (a blank line wasn't ending a list item, so a trailing
  unrelated paragraph got merged into the prior bullet, fabricating 7 cross-plan edges) and added
  resolved-vs-open edge distinction (`_resolved` suffix + lower weight) after noticing an already-
  fixed finding was still showing as an active conflict.
- **Memory housekeeping**: added `reference_nascence_plan_index_tool.md`,
  `reference_nascence_plan_files_audit_tool.md`, `reference_memory_links_tool.md`, and MEMORY.md
  pointers for all three tools.

## Key findings

- The most valuable pattern this session validated: **verify a plan's own claims against the real
  codebase, not just against other docs.** Every real bug and every genuine naming-drift case was
  found this way, not by reading prose more carefully.
- `lane2_the_witness.md`'s candidate filenames (`core/witness_loop.py`, `nodes/witness_node.py`)
  were never used — real implementation is `core/lane2.py`. Same drift pattern hit
  `garden_upgrade.md` and `thermal_causality.md`'s ledger modules (folded into their parent files).
  **If this pattern shows up a 4th time, it's worth generalizing plan_files_audit.py's check rather
  than fixing case-by-case.**
- `transport_manager.md` and `idle_executive_plan.md` independently invented near-identical
  salience-dispatcher architectures (own-history EMA/percentile scoring, competitive single-winner
  selection, shadow-first discipline) for different inputs — still unresolved, needs a design
  decision before either is built live.
- `thought_cycle_as_manifest_loop.md` and `train_split_merge.md` coined the same "train/cargo"
  metaphor 6 weeks apart with **incompatible field semantics** under the same vocabulary — still
  unresolved.
- `memory_multiway_linking.md` and `memory_knowledge.md` propose **incompatible mechanisms**
  (Personalized PageRank vs. a new typed-edge table) for the same target function
  (`recall_trail` in `core/associative_recall.py`) — still unresolved, and per a concurrent
  session's memory note this is now flagged as a real CONFLICT too (`journal_consolidation_pyramid.md`
  depends on a `memory_links` usage that `memory_multiway_linking.md`'s own audit later ruled
  against).

## Open threads

- **6 of the overlap audit's 15 findings are still genuinely open** and need a design decision, not
  a doc fix: the `transport_manager`/`idle_executive_plan` duplicate, the
  `thought_cycle_as_manifest_loop`/`train_split_merge` metaphor collision, `shore_upgrade`/
  `generative_world_sedimentation`, `sound_causality`/`sound_world_expansion`,
  `memory_multiway_linking`/`memory_knowledge`, and `journal_consolidation_pyramid`'s stale
  `memory_links` usage. Full detail in `docs/reviews/plan_overlap_audit_2026-08-23.md`.
- **`memory-links` was left as an explicit v1/prototype** — only 4 harvest sources wired at the time
  I stopped touching it. The user asked (this session) whether it could also match lab-test results
  to the plan they belong to, and whether it could find similar existing plans before a new lab test
  starts — I confirmed the existing tools (`plan-index` + `memory-links` + live grep) already
  support both workflows in principle, but flagged that neither is a packaged one-command lookup
  yet. **Per the concurrent session's memory notes, this has already been extended** (a
  `claims_file`/`shares_file` harvester reusing `plan_files_audit.py`, plus a full ROADMAP-wiring
  pass) — read `reference_memory_links_tool.md` fresh before assuming the v1 I built is still
  accurate.
- The `curiosity_goals_dreams.md` mismatch flag is a known, documented false alarm (memory-scan
  keyword collision) — the displayed stage (⚪ PARTIAL) is correct; don't spend time re-investigating
  it.

## Warnings

- **A second session was concurrently active on this same project for at least part of this
  session's run**, confirmed by on-disk file-change notices arriving in my final turns for:
  `MEMORY.md` (reorganized/condensed), `reference_memory_links_tool.md` (extended with new
  harvesters and two more found-and-fixed bugs), `reference_nascence_plan_files_audit_tool.md`
  (extended with the cross-project-reference finding), `plan_overlap_audit_2026-08-23.md`,
  `idle_executive_plan.md`, `project_nascence_curiosity_goals_dreams.md`, the `plan-index` and
  `memory-links` skill files themselves. That session also appears to have built at least 8 new
  skills (`decide`, `decide-review`, `job-queue`, `plan-liveness`, `plan-maintain`, `plan-snapshot`,
  `plan-sync`, `session-resume`, plus this `session-wrap` skill I'm using right now) and run a
  large-scale ROADMAP-wiring pass. **I have not read or verified any of that session's work directly
  — everything above about it is inferred from file-change notices and memory-file diffs shown to
  me, not independently confirmed.** Before citing any specific number from this handoff (e.g. "17
  ROADMAP-untracked plans," "438 edges") as current truth, rerun the relevant tool — the other
  session's own notes suggest most of these have already moved.
- Given `plan-maintain` now apparently exists as a single refresh-everything command, **use that
  instead of re-running `plan_index.py`/`plan_files_audit.py`/`build_edges.py` individually** next
  session, unless debugging one specific tool.

## Post-wrap maintenance pass

Ran `/plan-maintain` (built by the concurrent session, not by me) as this skill's step 4 requires
before closing out. Clean run, no errors, across all 7 stages (lint → plan_index → plan_files_audit
→ build_edges rebuild → decision-edge resync → plan_liveness → plan_snapshot). Current numbers, as
of this pass — supersede anything cited above in "What changed":
- **0 plans missing a ROADMAP link, 0 missing a memory file** (of 56) — the earlier "17
  ROADMAP-untracked" from this session's own work is fully closed now, confirming the concurrent
  session's wiring pass completed.
- **1300 owned edges** in `_memory_edges.jsonl` (up from this session's 438) — confirms the
  concurrent session's `claims_file`/`shares_file` harvester and re-run overlap-audit parse landed.
- **3 plans awaiting an open decision**, **13 decisions total** in `docs/decisions.jsonl` — a
  `/decide`-tracked ledger I did not build and haven't reviewed; check it before assuming this
  session's "6 open overlap findings" is the full picture of what needs a founder call.
- Lint flagged (not fixed, this pass doesn't auto-fix): 2 ROADMAP links to nonexistent plan slugs
  (`contradiction_rearchitecture_plan`, `evidence_review_dashboard`), 1 decision row with an
  unresolvable plan slug (`D-0013` → `factory_stations`), and 16 `docs/reviews/*.md` reports not yet
  harvested into `memory-links` (only the overlap audit is). None of these are this session's to fix
  blind — flagging for whoever picks this up next.

## Pointers

- `C:\Nascence\scripts\plan_index.py`, `C:\Nascence\scripts\plan_files_audit.py`,
  `C:\Users\USER\.claude\skills\memory-links\build_edges.py` — the three tools built this session.
- `C:\Nascence\docs\reviews\plan_overlap_audit_2026-08-23.md` — the 6 still-open findings needing a
  design decision.
- `C:\Users\USER\.claude\projects\C--FreshStart\memory\reference_memory_links_tool.md` — has the
  concurrent session's own account of what it added on top of this session's v1; read it before
  touching `memory-links` again.
- `docs/ROADMAP.md.bak-2026-08-23` — pre-edit backup, in case any of this session's or the
  concurrent session's ROADMAP.md edits need reverting.
