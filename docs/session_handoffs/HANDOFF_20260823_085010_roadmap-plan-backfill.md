# Session handoff — ROADMAP plan backfill + index toolchain edges

## Summary
Started from a `memory-links` extension (add `claims_file`/`shares_file` edges derived straight from
`plan_files_audit.py`, not the hand-written overlap doc) and used it to find every Nascence plan with
zero ROADMAP.md presence. Investigated and wired all 17 in two agent-fanout batches, caught and fixed
a real stale-claim error that propagated from ROADMAP into a plan bullet this session itself wrote,
then ran the full `/plan-maintain` pipeline to leave the index/edge store consistent. Ended by handing
the top job-queue item (J-0001) to the founder to run in a separate window while this session wrapped.

## What changed
- **`docs/ROADMAP.md`** — added ROADMAP entries for all 17 previously-untracked plans:
  `emissary_lane2_cognition`, `executive_world_grounding`, `factory_candidates_from_history`,
  `hud2_visual` (own new cluster 8, "HUD / Observability"), `investigation_deepening`,
  `investigative_action_loop_plan`, `item_and_population_factories`, `journal_consolidation_pyramid`,
  `ramses_second_tier`, `t5_procedural`, `thought_cycle_as_manifest_loop`, `train_courier_cargo_ids`,
  `world_census`, `epistemics_phase_c`, `pursuits` (own new top-of-file "★★ THE PURSUITS" section,
  same tier as THE TRAINS), `sound_world_expansion`, `generative_world_sedimentation`. Verified via
  `/plan-index`: 17 untracked → 0. Also corrected a stale claim in the `lane2_the_witness.md` bullet
  and in the `ramses_second_tier.md` bullet this session itself had written (see Key findings).
- **`docs/reviews/plan_overlap_audit_2026-08-23.md`** — added item #16 (SHARED-DEPENDENCY, ✅ FIXED)
  documenting the false-dependency correction below.
- **`C:\Users\USER\.claude\skills\memory-links\build_edges.py` / `SKILL.md`** — added
  `claims_file`/`shares_file` harvesters (imports `plan_files_audit.py`, never reimplements it).
  Fixed a real bug mid-session: the first version kept only the first shared file per plan pair
  (add_edge's dedup key silently dropped the rest). **Note: a concurrent session substantially
  rewrote this script further after my changes** — moved shared logic to
  `~/.claude/skills/_plan_tools_common/common.py`, switched from append-forever to full-rebuild-
  every-run, added plan-slug validation on `documents` edges and negation-aware overlap parsing. My
  `SKILL.md` edit describing the harvesters may now undersell what the script actually does — worth
  a fresh read-and-reconcile next time either file is touched.
- **`C:\Users\USER\.claude\projects\C--FreshStart\memory\reference_memory_links_tool.md`** —
  updated twice with what was built and found (see file for full detail, kept out of this handoff to
  avoid duplication).
- Ran `python C:\Users\USER\.claude\skills\plan-maintain\plan_maintain.py` at the end: edge store
  rebuilt 1272→1279 owned edges (408 `claims_file`, 254 `shares_file`), plan_index/plan_files_audit/
  plan_liveness/plan_snapshot all ran clean. `/plan-index` now: 56 plans, 0 untracked, 0 missing
  memory files.

## Key findings
- **`pursuits.md` had been fully built, restart-approved, and LIVE for 7 weeks with zero ROADMAP
  presence** — 4,837-line shadow log, 257 births, 2,563 judge-confirmed advances, 90 real RETURN
  events. Exactly the "built then never watched" disease this project's own evidence reviews keep
  finding elsewhere, just never caught for this specific plan. Notably it does not cite or get cited
  by THE TRAINS despite attacking the same founder-diagnosed AuDHD/cold-reset symptom from a different
  angle — flagged, not resolved.
- **`hud2_visual.md` was far more built than its "untracked SHADOW" label implied** — all three data
  layers confirmed 🟢 LIVE.
- **Self-caught error, now fixed:** this session's own `ramses_second_tier.md` ROADMAP bullet
  originally claimed it was "the direct proposed answer to lane2_the_witness's own open dedicated-
  hardware question." That was wrong — `lane2_the_witness.md` §4 had already resolved that exact
  question on 2026-08-20 (Lane 2 runs on the Ramses 3070, measured not argued, "§4 is no longer a
  gate"), and ROADMAP's own pre-existing `lane2_the_witness` bullet just hadn't been updated to say
  so — it still carried the plan's own since-retracted "Trinity Fabric fully allocated" line. The
  error came from trusting ROADMAP's own prose over the cited plan's current body text, propagated by
  an investigation agent that was only pointed at the ROADMAP entry, not the plan doc's §4. Both
  ROADMAP entries and the overlap audit are now corrected — see item #16 there for the full account
  and the process note.
- **A concurrent session (not this one) independently found and documented the `music_learning.md`
  stall** (post-Heavyweight listening regression, drill stuck at level 1, ABC composition hand never
  fired) and had already updated both the plan doc and its ROADMAP bullet by the time this session
  went to fix it — nothing left to do there.
- Confirmed genuinely useful pattern: de-hubbing the `shares_file` graph (dropping edges through
  files claimed by ≥4 plans) surfaces load-bearing, specific overlaps a raw shares-file count buries.
  Worth reusing.

## Open threads
- **J-0001 (cognitive_geometry mapping-census analyzer, resolves `/decide` D-0012)** — founder is
  running this in a separate Claude Code window right now. Don't touch `cognitive_geometry.md` or
  D-0012 concurrently; check `job_queue.py list` for its status before starting anything that
  overlaps.
- **J-0005 (trace the music-listening `sections_heard=0` regression + the never-fired ABC composition
  hand, resolves D-0010)** — still open, unstarted. Directly follows from the `music_learning.md`
  stall diffed this session; the diagnosis exists, the root-cause trace doesn't yet.
- **`docs/decisions.jsonl` row D-0013 references a plan slug (`factory_stations`) that doesn't
  exist** — flagged by `plan-maintain`'s lint, not fixed (not this session's territory — belongs to
  whoever owns the `/decide` ledger).
- 41 plans still lack a `## Current State — verified` section per the lint pass — pre-existing
  backlog, not new, not touched this session.

## Warnings
- **Heavy concurrent editing on this project today.** During this session, `music_learning.md`,
  `lane2_the_witness.md`, `ramses_second_tier.md`, and `journal_consolidation_pyramid.md` were all
  edited by at least one other active window (confirmed via mtimes landing inside this session's own
  wall-clock window), plus a full rewrite of `memory-links/build_edges.py`. **Always re-read a shared
  file immediately before editing it** — an in-context copy from earlier in a long session may already
  be stale, as happened here with ROADMAP's `lane2_the_witness` bullet.
- ROADMAP's own prose is not automatically current relative to a plan doc's latest section — verify
  against the actual plan body before repeating an "open question" or "unresolved" framing from
  ROADMAP alone.

## Pointers
- `C:\Nascence\docs\ROADMAP.md` — the master index, heavily edited this session.
- `C:\Nascence\docs\reviews\plan_overlap_audit_2026-08-23.md` — cross-plan findings, item #16 is this
  session's correction.
- `C:\Users\USER\.claude\skills\memory-links\build_edges.py` — needs a SKILL.md reconciliation pass
  after the concurrent rewrite.
- `C:\Nascence\docs\job_queue.jsonl` — J-0001 (in progress elsewhere), J-0005 (open, related to this
  session's music_learning findings).
- `C:\Nascence\docs\plans\lane2_the_witness.md` §4 — the corrected hardware-resolution source of truth.
