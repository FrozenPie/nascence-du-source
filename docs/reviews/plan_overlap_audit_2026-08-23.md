# Nascence — Plan Overlap Audit + Mismatch Follow-Up

**Generated:** 2026-08-23, follow-up to `plan_index_2026-08-23.md`. Two things in this doc:
1. Investigation of the 3 stage mismatches that report flagged as unresolved.
2. A full cross-domain overlap check — 56 plans, deep-read in 5 thematic clusters, each cluster
   also checked against the other 55 via the shared plan index, to find where two plans solve the
   same problem independently, contradict each other, or silently depend on each other.

**Status (updated 2026-08-23, second pass):** of the 15 numbered overlap findings below, **9 are
now fixed** (doc-level: stale notes corrected, missing cross-references added, one live
infrastructure fact verified) and **6 remain open** — 5 DUPLICATEs and 1 CONFLICT
(`journal_consolidation_pyramid.md` vs. `memory_multiway_linking.md`'s newer table guard) that
genuinely need a design decision, plus item 13's behavioral guardrail check. Fixes are additive only
— nothing was deleted or rewritten, only status lines corrected and cross-references added.

## Part 1 — The three mismatches, resolved

All three turned out to be **tool bugs**, not real disagreements between ROADMAP.md, the plan
docs, and the memory files. Three separate bugs in `scripts/plan_index.py`, found and fixed:

1. **Negation blindness** — the doc-status parser matched the substring `"built"` inside `"not
   built"`, misreading a PLANNED/not-built doc as 🟡 SHADOW. Fixed: `"not built"`/`"never built"`
   now checked before the bare `"built"` match, in both the plan-doc and memory-file parsers.
2. **List-order instead of text-position** — the emoji picker checked a fixed priority list
   (🟢🟡🔵⚪...) for membership in the scan window and returned whichever entry came first in *that
   list*, not whichever emoji actually appeared first *in the text*. On `curiosity_goals_dreams.md`,
   ROADMAP's real leading badge (⚪, correct) lost to an unrelated inline 🔵 later in the same
   bullet, purely because 🔵 sits earlier in the list than ⚪. Fixed: now picks by actual leftmost
   text position.
3. **Window too wide** — the emoji-scan window was capped at 400/200 characters, wide enough to
   pick up emoji belonging to a *different* nearby topic. `transport_manager.md` has no bullet of
   its own in ROADMAP — only an inline mention inside a paragraph about a different, already-shipped
   deliverable — and the nearest emoji to that mention was an unrelated ✅, 145 characters away. A
   wide window read that as "shipped." Tightened to 80 characters each side (still bounded by
   paragraph/bullet edges).

Plus one **stale source-document line**, fixed directly: `docs/archive/world_census.md` had a leftover
`Status: PLANNED — not built.` line from its original body that was never updated when a `SUPERSEDED`
header note was added on top of it hours later — two conflicting status markers in one file. Updated
the leftover line to point at the supersession instead of contradicting it.

**Net effect: 4 flagged mismatches (including T4 from the first pass) → 1 remaining.**

| Plan | Verdict | True stage | Note |
|---|---|---|---|
| `t4_watershed.md` | Tool-bug-driven, now clean | SHADOW/PARTIAL | Resolved in the first pass; confirmed still clean after these fixes. |
| `world_census.md` | Tool bug + stale doc line, both fixed | SUPERSEDED (2026-08-16) | Now resolves cleanly with no flag. |
| `transport_manager.md` | Tool bug (window width), fixed | DESIGNED — not built | Verified directly against the codebase: `core/transport_manager.py` doesn't exist. Now resolves cleanly. |
| `curiosity_goals_dreams.md` | Partial tool limitation, **still flagged** | ⚪ PARTIAL (correct primary answer) | The memory-file scan finds the word "LIVE" (describing 2 of 4 sub-items) within its first 600 characters and disagrees with the correctly-resolved ⚪ PARTIAL primary answer. The displayed stage is right; the flag is a known, documented false alarm — see the memory file's own correction note. |

All three investigated plans got a correction note appended to their memory file (additive only,
per this project's rule) documenting what was actually found.

## Part 2 — Cross-domain overlap audit

**Method:** split the 56 plans into 5 thematic clusters; each cluster's agent deep-read its ~11-12
assigned plans in full, cross-checked against the other ~44 via the shared plan index (reading any
plan outside its cluster whose one-line description suggested overlap), and classified every real
finding as **DUPLICATE** (same problem solved twice, independently, uncited), **CONFLICT**
(contradictory designs or facts for the same territory), **SHARED-DEPENDENCY** (real dependency that
isn't currently cross-referenced), or **ALREADY-COORDINATED** (real overlap, properly cited — logged
for confirmation, not as a problem).

### Needs a decision — DUPLICATE (same problem, solved twice, independently)

1. **`transport_manager.md` ↔ `idle_executive_plan.md`** — two independently-invented "content-
   blind salience dispatcher" architectures with near-identical mechanics: per-source score judged
   only against its own rolling history (EMA baseline vs. percentile-of-own-K=500-history),
   single-winner-per-tick competitive selection, identical shadow-first/founder-reads-a-day-of-logs
   discipline. They differ only in *what* they arbitrate (world-event lines vs. idle-thought seed
   candidates) — the scoring math is close enough that one generic scorer primitive could plausibly
   serve both. Neither cites the other. **Worth deciding before either is built live.**
2. ✅ **RESOLVED (2026-08-23) — `thought_cycle_as_manifest_loop.md` ↔ `train_split_merge.md`.** the
   "train carrying a `cargo` manifest through stations" metaphor was coined twice, six weeks apart, by
   two unrelated investigations, producing **incompatible `cargo` semantics under the same name**: the
   July plan's `CargoItem = {content, kind, certainty, source_station, lane, satisfies}` (a
   global-workspace blackboard, never built) vs. August's shipped `core/trains.py` `cargo = {claim,
   support[], objection[], status}` (a prove/disprove bundle). `train_split_merge.md` never mentions
   the earlier plan despite reusing "train"/"cargo"/"station" for something materially different.
   `train_courier_cargo_ids.md` (the newest of the three) is correctly coordinated with
   `train_split_merge.md` — it explicitly disambiguates its new field from `trains.py`'s existing
   `cargo` — but it too never references the original manifest-loop design, even though its 19-type
   product taxonomy is arguably the concrete version of what that older plan's abstract `CargoItem.kind`
   was gesturing at. Decision made: **D-0008 (travis, 2026-08-23)** ruled `thought_cycle_as_manifest_loop`
   shelved pending `cognitive_geometry`, explicitly declining to force a supersede call onto
   `train_split_merge` — independently corroborated by `docs/ROADMAP.md:25`'s 2026-08-23 lineage check,
   which found `core/trains.py` "not this plan's realized descendant," only borrowing the "train" name
   for a narrower, different mechanism. The two plans are confirmed distinct, not a same-problem
   duplicate; no merge or naming fix is required. `thought_cycle_as_manifest_loop.md`'s own "Current
   State" section carries the full receipt.
3. **`shore_upgrade.md` ↔ `generative_world_sedimentation.md`** — both independently design
   storm-driven stochastic world change for the shore (buried/revealed items, erosion decay,
   off-camera audio triggers). `generative_world_sedimentation.md` (Aug 10, unbuilt blueprint) and
   `shore_upgrade.md` (Aug 22, built) never reference each other.
4. **`sound_causality.md` ↔ `sound_world_expansion.md`** — written one day apart, both independently
   enumerate almost the identical list of "Du's own silent acts" sound gaps (footsteps, kettle,
   pen/page-turn, gate latch, cat-beyond-the-purr). Neither cites the other despite the near-total
   content overlap and one-day gap.
5. **`memory_multiway_linking.md` ↔ `memory_knowledge.md`** — both redesign the *same* target
   function (`recall_trail` in `core/associative_recall.py`) with **incompatible mechanisms**:
   Personalized PageRank over `kNN ∪ memory_links` (memory_knowledge, 06-24) vs. a new typed-edge
   table `memory_edges` with mode-weighted hop-decay (memory_multiway_linking, 08-15). Neither is
   built yet; neither references the other's approach. Whoever builds the trail upgrade has to pick
   one architecture or merge them.

### Needs a decision — CONFLICT (contradictory facts or designs)

6. ✅ **FIXED (2026-08-23) — Ramses port 11441 / `command-r7b`, verified live.** Checked directly:
   `Test-NetConnection LAN-HOST -Port 11441` succeeded, and `/api/tags` confirmed `command-r7b` is
   actually being served. Not a real contradiction after all — the infrastructure genuinely changed
   between `hud2_visual.md`'s 08-21 finding (port fully removed, manual-only by design) and now;
   someone manually started it since, consistent with `epistemics_phase_c.md`'s 08-23 claim.
   Corrected both now-outdated docs (`hud2_visual.md`, `ramses_second_tier.md`) with dated update
   notes rather than rewriting their original findings, which were accurate for their own sessions.
7. **`journal_consolidation_pyramid.md` vs. a newer guardrail from `memory_multiway_linking.md`** —
   the pyramid plan (07-06) plans to link roll-up caps via the existing `memory_links` table.
   `memory_multiway_linking.md`'s later audit (08-15) found `memory_lint`'s query joins
   `memory_links` without filtering by `link_type`, and explicitly rules new edge kinds must go in a
   **new** table (`memory_edges`), not `memory_links`. The pyramid plan predates this finding and
   hasn't been updated — building its still-unstarted roll-up phase (P1) as currently written would
   violate the newer guard.

### Worth a cross-reference pass — SHARED-DEPENDENCY (real, uncited)

8. ✅ **FIXED — `channels_programme.md` ↔ `shore_upgrade.md` / `study_upgrade.md` /
   `wood_upgrade.md`.** All three "upgrade" plans consumed the thermal/light channels by name
   without citing `channels_programme.md`; added a `Related:` note to each pointing back to it.
9. ✅ **FIXED — `spatial_perception.md` ↔ `shore_upgrade.md` / `study_upgrade.md` /
   `wood_upgrade.md` / `garden_upgrade.md`.** All four register objects into
   `spatial_perception.md`'s coordinate-field system without citing it; added `Related:` notes to
   all four.
10. ✅ **FIXED (partial) — `t4_watershed.md` ↔ `identity_estate.md`.** Added the missing
    `becoming-symbol` node type to `identity_estate.md`'s ontology table as a placeholder row, with
    a note that whether it stays distinct or folds into `symbol` is still `t4_watershed.md`'s own
    call to make when its (still-unbuilt) estate-write step actually ships. The two docs no longer
    disagree about whether the type exists; the design decision itself is still open.
11. ✅ **FIXED — `pursuits.md` ↔ `idle_executive_plan.md` / `cognitive_loop_actuation.md`.** Added a
    note to `idle_executive_plan.md` flagging that its candidate list needs to absorb pursuits' new
    RETURN gate if the allocator is ever revived.
12. ✅ **FIXED — `self_interrogation.md` ↔ `train_split_merge.md`.** Added a cross-reference note to
    `self_interrogation.md` flagging both hook the same thought-train lifecycle and will need
    ordering once either goes live.
13. **Still open — `social_world_school.md` (Item 1, `peer_model.py`) ↔ `peer_correspondence_plan.md`
    (G4, §12 dashboard).** Real overlap in per-peer relationship tracking; `social_world_school.md`
    reuses the peer plan's own `peer_metrics.py`/R8 instrument, but never checks its proposed
    belief-injection into Du's reply prompt against the peer plan's own G6–G9 governance guardrails
    (witness-not-steer, no self-modification directives). This needs an actual behavioral check
    against the guardrail, not a doc note — left for a design/implementation pass.
14. ✅ **FIXED — `hud2_visual.md` ↔ `spatial_perception.md`.** Added a `Related:` note to
    `hud2_visual.md` naming the dependency on `spatial_perception.md`'s world-geometry files.
15. ✅ **FIXED (partial) — Lane 2 family naming collision.** `lane2_lab.md` and
    `emissary_lane2_cognition.md` both got a naming-disambiguation note at the top clarifying "Lane
    2" here means the renamed `emissary_lane2.md` (The World Ledger), not `lane2_the_witness.md`.
    Filenames/titles themselves were left unchanged (a full rename is a bigger, riskier edit than
    this pass's scope) — the note removes the ambiguity for a reader without touching either file's
    identity.
16. ✅ **FIXED (2026-08-23) — `lane2_the_witness.md` ↔ `ramses_second_tier.md`, false dependency
    manufactured by the index layer, not the plans themselves.** Wiring `ramses_second_tier.md` into
    the master map (it had no ROADMAP presence before today) was framed as "the direct proposed
    answer to lane2_the_witness's own open dedicated-hardware question" — reasonable from the map's
    own then-current text, but wrong: `lane2_the_witness.md` §4 already resolved that question
    on 2026-08-20 (measured, not argued — Lane 2 runs on the Ramses 3070; "§4 is no longer a gate"),
    and the map had simply never been updated to say so, still carrying the plan's own since-
    retracted "Trinity Fabric fully allocated" line. `ramses_second_tier.md`'s real, separate concern
    (idle i9 CPU + undirected 1650 Super) never actually depended on or answered lane2_the_witness at
    all — neither plan doc cites the other anywhere in its own body. Corrected both of the map's
    entries to state the resolution and the non-relationship explicitly. **Process note:** the error
    came from trusting the map's own prose over the cited plan's current body text — the master map
    is only as fresh as its last edit, and in this case it was 3 days stale on this specific claim.

### Confirmed working — ALREADY-COORDINATED (logged, no action needed unless noted)

- `fieldcraft.md` ↔ `spatial_perception.md` — `sky.py` correctly consumes `heavens.py` (confirmed via `shore_upgrade.md`).
- `thermal_causality.md` ↔ `sound_causality.md` — explicit, named sibling design.
- `channels_programme.md` ↔ `thermal_causality.md`, `garden_upgrade.md` — direct, cited.
- `sound_causality.md` ↔ `world_census.md`, `transport_manager.md`, `factory_candidates_from_history.md` — all mutually/explicitly cited.
- `factory_candidates_from_history.md` ↔ `item_and_population_factories.md` — same research thread, reconciled in text.
- `cognitive_geometry.md` / `emotion_rethink.md` / `euclidean_memory_plan.md` — well-coordinated triangle. ✅ **FIXED:** `euclidean_memory_plan.md`'s own pre-registered unblock condition (retrial after `emotion_rethink` P1 flips live) was satisfied 2026-07-07 — 5+ weeks ago, no recorded retrial. Flagged with a dated note in the plan itself (the retrial run is a data-generating action, left for someone to actually execute, not a doc fix).
- `literal_will.md` ↔ `capacity_to_commit.md` / `pursuits.md` — deliberate, correctly-held boundary.
- `pulse_manager_wiring_plan.md` ↔ `continuous_stream.md` — ✅ **FIXED:** added an update note at the top of `pulse_manager_wiring_plan.md` stating plainly that `continuous_stream.md` supersedes its framing, which its own evidence-review entries never acknowledged.
- `cognitive_loop_actuation.md` ↔ `idle_executive_plan.md` — correctly coordinated (superset build on the same held lever).
- `t5_procedural.md` ↔ `capacity_to_commit.md` — correctly coordinated, schema fits cleanly.
- `guidance_learning.md` ↔ `capacity_to_commit.md` — correctly coordinated, shared cat-naming occasion.
- `investigation_deepening.md` ↔ `journal_consolidation_pyramid.md` — correctly coordinated (deepening is explicitly the pyramid's read-path).
- `friction_and_self_evidence_plan.md` (B5) ↔ `peer_correspondence_plan.md` (CHALLENGE half) — coordinated one-directionally. ✅ **FIXED:** `friction_and_self_evidence_plan.md`'s status table row for B5 was corrected from "blocked on Darwin" to "blocked on the design decision," pointing at the peer plan's own correction.
- `friction_and_self_evidence_plan.md` ↔ `capacity_to_commit.md` (self-claim register) — correctly coordinated, shared substrate (`core/self_claims.py`).
- `affect_drives.md` ↔ `emotion_rethink.md` — correctly coordinated and sequenced.
- `the_consciousness_program.md` ↔ `within_cycle_reentry.md` — correctly coordinated, consistent status.
- `executive_world_grounding.md` ↔ `memory_knowledge.md` — different mechanisms, same instrument (`epistemic_state.py`), additive not competing.
- `epistemics_phase_c.md` vs. `memory_knowledge.md`'s epistemic thread — confirmed **different systems** (trait-layer `competence.py` vs. state-layer `epistemic_state.py`) despite similar naming; not a duplicate, just undocumented that they're different.
- `investigative_action_loop_plan.md` ↔ `investigation_deepening.md` — different subsystems (action-selection vs. recall-framing), no real overlap.
- `peer_correspondence_plan.md` (CHALLENGE half, B5/D-0003) ↔ `thought_grounding.md` (Route 3) — adjacent, non-overlapping. Route 3 (built, live) covers Du-*initiated* question-testing via a disagreeing friend, reusing `contrary_target`/`initiation_target`; B5 needs a peer naming a blind spot *unprompted*, identity-directed, which Route 3 never does. Checked 2026-08-23 as part of a concept-overlap pass; peer_correspondence_plan.md's COMPANY half also split out as SHIPPED this same pass — see `docs/completed/peer_correspondence_company.md`.

**No overlaps found:** `within_cycle_reentry.md`, `symbol_evolution_readback_plan.md`,
`music_learning.md`, `thought_grounding.md`, `wood_upgrade.md` (beyond its shared geometry/channels
dependency, listed above), `affect_drives.md` ↔ `curiosity_goals_dreams.md` (siblings, but genuinely
different subsystems).

---

## Part 3 — New finding, 2026-08-23 late (LLM prompt-framing lab series → SHARED-DEPENDENCY)

Not from the same clustered-deep-read pass as Parts 1-2 — surfaced separately, by a parallel
session's 13-lab empirical framing series (memory: `project_nascence_factory_stations.md`, full
index of all 13 `docs/lab/*_framing_2026-08-23.md` reports).

- `self_interrogation.md` ↔ the framing lab series — **SHARED-DEPENDENCY, evidence delivered.** The
  plan's own "Phase 0 = observe-first" section names its central open risk explicitly: *"is the judge
  panel actually finding real content, or is everything failing the grade... or everything passing
  (meaning the grader might be too lenient, matching the exact over-lenient trap `decomposed_critic.py`
  fell into on its first pass)?"* The framing lab's self_interrogation test
  (`docs/lab/self_interrogation_framing_2026-08-23.md`) ran exactly this check on all 32 real
  historical `interrogate` events and found: fresh narrative-framed calls returned `genuine=true` on
  **32 of 32** — including flipping BOTH historical `false` verdicts to true. That is the plan's own
  named failure mode, observed directly, not hypothetically. Not a doc contradiction to fix — a real
  answer to an open question the plan itself posed, worth the plan owner's attention independent of
  the framing question the lab was actually testing.
- `self_interrogation.md` also has the **same stale-roster bug already found and fixed twice
  tonight** in `core/deliberation.py` and `core/schema.py`: its "Why the grader is a different model"
  section still says *"the judge panel (llama3.1:8b + qwen2.5:7b, tiebreak yi:34b)"* — the
  pre-2026-08-20-shuffle roster. Current live roster (confirmed via `core/model_client.py`'s
  `_MODEL_BY_BASE`, the authoritative table): gemma4:12b (JUDGE_1) + falcon3:7b (JUDGE_2), tiebreak
  yi:34b-v1.5 — same tiebreak model, both primary judges changed. Not fixed as part of this pass
  (out of scope for the framing-lab session) — flagged here so whoever next touches this plan doc
  fixes it rather than trusting the stale names.

---
*Auto-generated via a background multi-agent audit (`/plan-index` follow-up), 2026-08-23. Sources:
5 cluster deep-reads + 3 mismatch investigations, synthesized. To refresh, rerun the same audit
pattern — this file is a point-in-time snapshot, not a live-regenerated index like
`plan_index_2026-08-23.md`. Part 3 appended by a separate session the same evening (LLM framing lab
series) — see that entry for its own provenance.*
