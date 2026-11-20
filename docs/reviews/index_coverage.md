# What the planning-index toolchain actually indexes — and what it doesn't yet

Not auto-generated (unlike the per-run reports) — a reference doc, hand-maintained, checked by
`/plan-maintain`'s lint step (the "unharvested review docs" line) so drift here gets caught instead
of silently accumulating the way plan-doc drift used to. Update this file when a tool's coverage
changes, not just when someone happens to notice a gap.

## Indexed today

| Source | Tool(s) | What it captures |
|---|---|---|
| `docs/plans/*.md`, `docs/staged/*.md` | plan_index, plan_files_audit, plan_liveness, decide, memory-links, plan_snapshot | The core plan corpus — stage, file resolution, evidence firing, decisions, edges, history |
| `docs/ROADMAP.md` | plan_index (stage cross-check), plan_snapshot (backfill source) | The human-maintained "current picture," plus dated stage claims scattered through its prose |
| `docs/decisions.jsonl` | decide, plan_index (`Open ⚖` column), memory-links (`awaits_decision`/`decided_by`/`ruled_in` edges) | Founder rulings with named defeaters |
| `docs/plan_snapshots.jsonl` | plan_snapshot | Its own append-only history store |
| `C:\Users\...\memory\project_nascence_*.md` | plan_index (evidence/stage), plan_files_audit (Idea column), memory-links (`documents`/`references`/`originated_in` edges) | Claude's own memory files about each plan |
| `docs/reviews/plan_overlap_audit_*.md` (glob, multi-file safe) | memory-links (`duplicates`/`conflicts_with`/`shared_dependency`/`coordinates_with` edges) | Hand/agent-written cross-plan overlap findings |
| Nascence codebase (`core/`, `scripts/`, `nodes/`, `data/`, `hud/`, `deploy/`, `tests/`) | plan_files_audit (resolution), plan_liveness (evidence firing) | Whatever a plan doc actually cites in backticks — not a full-repo scan |

## NOT indexed — the watch-list

Ranked by how much signal is sitting there unused, not by ease of fixing.

1. **`docs/reviews/*.md` beyond the overlap audit — the single biggest opportunity.** 9 more dated
   point-in-time audits sit in the same directory (`audit_2026-08-20.md`, `sleep_dream_2026-08-22.md`,
   `crosslink_audit_2026-08-22.md`, `actions_system_2026-08-22.md`, `du_24h_2026-08-21.md`,
   `du_dreams_evolution_2026-08-21.md`, `t5_procedural_skills_2026-08-22.md`,
   `triple_lens_review_2026-07-02.md`, `dedup_2026-08-20_manifest.json`) — each one is exactly the
   shape `build_edges.py` already knows how to harvest from the overlap audit, just never
   generalised. Real historical dated claims sitting unused. `plan_maintain`'s lint step now flags
   new ones by name (see below) so this list doesn't grow invisibly, but nothing parses them yet.
2. **`docs/UNFINISHED_PLANS_SURVEY_2026-08-18.md`** — a full historical per-plan cross-check, dated,
   116 lines. A rich `plan_snapshot backfill` source (one more real historical data point per plan)
   that nothing currently mines.
3. **`docs/completed/` (59 files) and `docs/archive/` (28 files)** — `plan_index.collect_plans()`
   only scans `docs/plans/` + `docs/staged/`. A plan moved to either directory becomes invisible to
   the ENTIRE toolchain overnight — no stage row, no liveness check, no snapshot history continuation.
   `docs/completed/` has its own hand-maintained `INDEX.md` (a fourth registry, alongside ROADMAP,
   AWAITING_EVIDENCE, DEFERRED_PLANS) that nothing cross-checks against the other three. Worth a
   dedicated, lighter-weight pass (completed plans shouldn't get `🕸 stale` flags, but SHOULD stay
   queryable via memory-links since active plans still reference their files).
4. **`docs/AWAITING_EVIDENCE.md`** — the project's own "current dashboard," explicitly meant to be
   read alongside ROADMAP.md and `docs/staged/DEFERRED_PLANS.md` per its own header. Not indexed at
   all; a genuine registry sitting outside the toolchain's view.
5. **`docs/staged/DEFERRED_PLANS.md`** — consciously-shelved plans with named re-entry triggers,
   i.e. hand-written proto-`/decide` entries that predate `/decide`. Worth eventually migrating into
   the real ledger (each trigger becomes a decision with a defeater) rather than living as prose two
   registries away from the tool built to hold exactly this.
6. **`session_2026-08-*_summary.md` (4 files, project root)** — hand-written, dated. Another
   `plan_snapshot backfill` candidate; also a natural `memory-links` session-node source beyond the
   `originSessionId` frontmatter link it already has.
7. **`docs/lab/` (43 files)** — test fixtures/experiments. `plan_files_audit` already excludes it
   from ambiguity resolution (`NOISY_DIR_MARKERS`); its own content has never been surveyed for
   whether anything in it is actually load-bearing evidence mislabeled as a fixture.
8. **`docs/cross_model/`, `docs/du_self_knowledge/`, `docs/exports/`, `docs/node_audit/`,
   `docs/reports/`, `docs/chronicles/`** — unsurveyed. Not flagged as a problem, just genuinely
   unknown — nobody has looked at what's in them relative to this toolchain's scope.
9. **System-level liveness vs. plan-level liveness** — `plan_liveness.py` only sees what a plan doc
   explicitly cites in backticks. Du's own `scripts/liveness_audit.py` (the tool this one was ported
   from) watches ~20 hardcoded evidence streams by name, independent of any plan — a structural gap
   between "is this plan's own evidence firing" and "is the whole system's evidence firing," with no
   single tool answering both.
10. **`ROADMAP.md.bak-2026-08-23`** — a backup file sitting in `docs/` root, not `docs/archive/`.
    Not a coverage gap, just a housekeeping note: a future prose-scan could mistake it for a live doc.

## How this stays current

`plan_maintain.py`'s lint step (added 2026-08-23, same pass as this doc) globs `docs/reviews/*.md`
and reports any file that isn't `plan_overlap_audit_*.md` as an "unharvested review doc" — so the
count in item 1 above is a live number on every run, not a one-time snapshot. Nothing else on this
list has an automated check yet; that's the honest state, not an oversight to paper over.
