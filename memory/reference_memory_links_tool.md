---
name: reference-memory-links-tool
description: "The /memory-links skill — a typed-edge store over Claude's own memory files, Nascence plans, and audit reports, modeled directly on Nascence's core/memory_edges.py. Query it for 'what connects to X' before re-grepping many files by hand."
metadata: 
  node_type: memory
  type: reference
  originSessionId: 1857a5ac-8424-4a7e-930e-5da8c19bf9b9
  modified: 2026-08-23T04:54:47.172Z
---

Built 2026-08-23 (prototype), directly requested: "let's see if we have other ways from Du to make
our interface efficient... a skill that uses Du's tuple systems to track links." Read
`core/memory_edges.py` in full before designing this — the transfer is real, not just a naming
borrow: same generic `(src_kind, src_id, dst_kind, dst_id, edge_type, weight, provenance)` schema,
same hard rule ("an edge that cannot name the recorded event that earned it is confabulated and must
not be written"), same deterministic-harvest-not-LLM-guess discipline, same "ambiguous → no edge"
bias. [[function-over-imitation]] applies here too — transferred the FUNCTION (a queryable,
provenance-carrying link graph) not surface mechanism (Du's is SQLite over his own fragment store;
this is JSONL over plain memory files, matched to this system's actual architecture).

**Invoke via the `/memory-links` skill** (`~/.claude/skills/memory-links/`). `build_edges.py`
harvests edges (wikilinks, `originSessionId` frontmatter, the `project_nascence_<slug>.md` filename
convention, and the plan-overlap-audit's 34 findings) into
`C:\Users\USER\.claude\projects\C--FreshStart\memory\_memory_edges.jsonl`. `query.py <kind>:<id>`
answers "what connects to this" in one call. First real query
(`plan:t4_watershed`) surfaced both its memory-doc link and the identity_estate overlap finding
with resolution status, in place of what would've been three separate file reads.

**A real bug already caught and is worth remembering as a caution:** the overlap-audit parser
initially let a trailing non-bulleted paragraph bleed into the prior bullet (missing blank-line
handling), fabricating 7 cross-plan edges on the first run. Caught by spot-checking an unexpected hub
(`investigative_action_loop_plan` showing up with edges to plans it has nothing to do with) before
trusting the data — the same "verify before asserting" discipline as everywhere else in this
project. Fixed, but this is regex over prose, not a structured source; a differently-formatted
future report could silently break it the same way. Spot-check new harvest sources before trusting
them.

**Explicitly a prototype/v1**, per the SKILL.md's own limitations section: no fast pre-filter index
yet (not needed at ~960 edges), and `_resolved`-suffixed edges (findings marked ✅ FIXED in their
source text) need to stay distinguished from open ones — that distinction didn't exist on the very
first run either.

**2026-08-23, same day, extended with a 3rd harvester: `claims_file` / `shares_file`.** Directly
requested backfill — "find links to plans based on the files they rely on/change." Imports
`plan_files_audit.py` (doesn't reimplement it) to resolve every plan's backtick file refs against
the real filesystem; every CONFIRMED resolution is a `claims_file` edge, and every pair of plans
resolving to the *same* file gets `shares_file`. Deliberately kept separate from `shared_dependency`
(the hand-written overlap-audit narrative) since the two carry different evidence and do disagree —
cross-checking against [[reference-nascence-plan-index-tool]]'s stage table found real signal:
**78 of 162 `shares_file` pairs involve a plan not in ROADMAP.md at all or a stage mismatch** (one
retired, one active) — e.g. `cognitive_loop_actuation` (⛔ SUPERSEDED) still shares
`nodes/inner_monologue_node.py` with 8 live/shadow plans, meaning a "dead" plan's file claims
describe a module current work still depends on. Several ROADMAP-untracked plans
(`executive_world_grounding`, `emissary_lane2_cognition`, `thought_cycle_as_manifest_loop`,
`item_and_population_factories`, `sound_causality`, `journal_consolidation_pyramid`,
`ramses_second_tier`) turned out to have real file-level ties to tracked plans — they're less
isolated than plan-index alone suggests; that's a ROADMAP linking gap, not noise.

**A second real bug caught and fixed the same day:** the first version of the harvester only kept
the *first* shared file per plan pair (add_edge's dedup key is `(src,dst,edge_type)`, so a second
`add_edge` call for an already-seen pair was silently a no-op) — found while cross-checking
`t4_watershed`↔`identity_estate`, which actually shares two files
(`data/identity/axiom.json` + `data/identity_estate.json`) but only one was surviving. Fixed by
aggregating all shared files per pair before writing a single edge with `weight` = file count.

**De-hubbing finding worth reusing:** files claimed by ≥4 plans (`nodes/inner_monologue_node.py`
alone contributes 45 of the 162 pairs) are real signal but drown out narrower, more specific
overlaps. Dropping edges through those ~15 hub files leaves 54 pairs — a much more legible
"integration point" map. Top residual-degree plans (most *specific* cross-connections, not just
popular-file coincidence): `emissary_lane2`, `idle_executive_plan`, `lane2_the_witness` (6 each),
then `memory_knowledge`, `memory_multiway_linking`, `curiosity_goals_dreams`, `hud2_visual` (5 each).
Worth running again after future harvester extensions to see if the same plans stay central.

**2026-08-23, same day, follow-through: 12 of those ROADMAP-untracked plans actually wired into
`C:\Nascence\docs\ROADMAP.md`.** Directly requested ("investigate the 11 [actually 12, recount
corrected] plans not in the roadmap... send out some agents"). Dispatched 12 parallel general-
purpose agents, one per plan — each read the full plan doc, grepped ROADMAP.md for prose-only
mentions, checked the plan_files_audit report for MISSING files, and produced a ready-to-paste
ROADMAP bullet plus a verdict on real cross-plan relationships. Real findings that changed the
outcome from a mechanical "just add a link": `hud2_visual.md` turned out to have all three data
layers 🟢 LIVE (not simply 🟡 SHADOW-untracked as plan-index's own scan suggested) and is the single
most cross-file-connected untracked plan found (11 ties) — given its own new ROADMAP cluster 8
"HUD / Observability". `thought_cycle_as_manifest_loop.md` shares "train"/"cargo" vocabulary with
the already-shipped `train_split_merge.md` but is NOT its realized descendant — the agent traced
citations and found train_split_merge actually descends from `transport_manager.md`, and never
builds thought_cycle's real load-bearing piece (the decoupled completion judge). `executive_world_
grounding.md` turned out to be a redundant same-territory rediscovery of `memory_knowledge.md`'s
already-tracked Improvement 1, not a lost cross-cutting plan, despite sharing files with 11 other
plans (mostly coincidental orchestrator.py/world_manifest.py infrastructure-adjacency, not real
design overlap). Post-wiring, `/plan-index` dropped from 17 to 5 ROADMAP-untracked plans — the
remaining 5 (`world_census`, `epistemics_phase_c`, `pursuits`, `sound_world_expansion`,
`generative_world_sedimentation`) were outside this batch's scope (not in the residual `shares_file`
graph) and are the natural next candidates if this gets repeated.

**2026-08-23, same day, second pass: the remaining 5 done the same way — `/plan-index` now reads
0 ROADMAP-untracked plans of 56 (down from 17 at the start of this whole exercise).** Biggest find
by far: `pursuits.md` (2026-07-08 founder idea — fix Du's idle thoughts chasing a topic ~3 turns
then cold-resetting, by giving him a persistent `pursuit` object idle thinking is biased to RETURN
to) has been **fully built, restart-approved, and LIVE for 7 weeks** with real accrued evidence
(`data/pursuits_shadow.jsonl`, 4,837 lines: 257 births, 2,563 judge-confirmed advances, 90 real
RETURN events, 9 saturated pursuits) — and had ZERO ROADMAP presence the whole time, not even a
prose mention. Given its own top-of-file "★★ THE PURSUITS" section, same tier as THE TRAINS, since
cluster 6 would have buried a live, working, 7-week-proven mechanism. Notably it does NOT cite or
get cited by THE TRAINS despite being the founder's *same* AuDHD/looping/cold-reset diagnosis
attacked from a different angle (cross-train persistence vs. within-train mechanics) — flagged as
a real, unresolved integration gap. Also found: `epistemics_phase_c.md`'s claimed evidence file
(27 rows in `data/accuracy_observations.jsonl`) turned out to be pre-existing Tier-1/4 traffic, not
this plan's own instrument — the DRAFT/nothing-built label was correct about code despite the real
data sitting right there (a good example of why `plan_files_audit`'s CONFIRMED-file signal must
still be read, not just counted). `sound_world_expansion.md` (a founder-review proposal, never
formally decided) turned out **partially built anyway** — 4 of ~32 proposed sound names shipped
verbatim through unrelated 08-22 upgrades, including one (`clock_tick`) that directly contradicts
the doc's own explicit "no clock" recommendation, apparently overridden without anyone updating the
doc. `world_census.md` was the one genuinely simple case — SUPERSEDED same evening it was written,
kept only as a short historical footnote next to the factory family it was replaced by.

Related: [[reference-nascence-plan-index-tool]], [[reference-nascence-plan-files-audit-tool]] (the
two other tools this one cross-references and could pull more edges from next).
