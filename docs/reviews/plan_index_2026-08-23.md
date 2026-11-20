# Nascence — Plan Index

**Generated:** 2026-08-23 (third pass), by the `/plan-index` tool (`scripts/plan_index.py`).
**Scope:** every plan document in `docs/plans/` and `docs/staged/` (excluding `DEFERRED_PLANS.md`,
which is itself a registry of shelved plans, not a plan — it has its own memory file as a reference
doc instead, see appendix). Does not cover `docs/completed/` or `docs/archive/` — this is the
*active planning landscape* only, matching how `ROADMAP.md` frames itself.

## What changed, in order

**Pass 1 (first generation):** found 49 plans with no memory file and 29 plans not linked from
ROADMAP.md — a raw snapshot.

**Pass 2 (memory-fill workflow):** wrote all 49 missing memory files (read from source, not
fabricated); fixed 8 ROADMAP.md links where content existed but the link didn't (backed up first to
`docs/ROADMAP.md.bak-2026-08-23`); resolved the T4 Watershed stage mismatch; found and fixed 2 tool
bugs (`plans/`-only link matching missed correctly-linked staged plans; a plan linked before
ROADMAP's first heading read as "not found"). Net: 29→17 ROADMAP gaps, 49→0 missing memory files.
Adding 49 real memory files also surfaced **3 new mismatches** the tool had no signal to find before:
`curiosity_goals_dreams`, `transport_manager`, `world_census`.

**Pass 3 (this one) — investigated those 3 mismatches and fixed what was fixable:**
- All 3 turned out to be **tool bugs**, not real source disagreements: (1) a negation-blindness bug
  read `"not built"` as `"built"` → 🟡 SHADOW; (2) the emoji picker returned whichever stage emoji
  came first in a fixed priority list, not whichever appeared first in the actual text — so an
  unrelated inline emoji later in a bullet could beat the bullet's own leading badge; (3) the
  emoji-scan window (400/200 chars) was wide enough to pick up an emoji belonging to a different,
  unrelated topic nearby. All three fixed in `plan_index.py`.
- One genuine **stale source-document line**: `world_census.md` had a leftover `Status: PLANNED —
  not built.` line that predated a `SUPERSEDED` header note added hours later — fixed directly.
- **Net: 4 flagged mismatches (incl. T4) → 1 remaining** (documented below; the displayed stage is
  correct, only the flag itself is a known false alarm).
- Also **verified the Ramses port 11441 conflict live** (`Test-NetConnection` + `/api/tags`):
  `command-r7b` really is up. Not a documentation contradiction — the infrastructure genuinely
  changed between the two older checks (08-20/08-21, port dead/unprovisioned) and now. Corrected the
  two now-outdated docs (`hud2_visual.md`, `ramses_second_tier.md`).
- **Fixed 8 more stale/incomplete cross-references found by the overlap audit**, all additive:
  `friction_and_self_evidence_plan.md`'s B5 status row (was wrongly "blocked on Darwin"),
  `pulse_manager_wiring_plan.md` (now notes it's superseded by `continuous_stream.md`),
  `euclidean_memory_plan.md` (flagged its own unblock condition as satisfied 5+ weeks ago, retrial
  overdue), naming-disambiguation notes on `lane2_lab.md` and `emissary_lane2_cognition.md` (both
  still titled "Lane 2" after a sibling doc's rename), a missing ontology-table entry added to
  `identity_estate.md`, and uncited-dependency notes added to `shore_upgrade.md`, `study_upgrade.md`,
  `wood_upgrade.md`, `garden_upgrade.md`, `hud2_visual.md`, `idle_executive_plan.md`, and
  `self_interrogation.md`.

The 17 ROADMAP gaps are unchanged this pass — those are **content gaps, not linking gaps** (ROADMAP
genuinely never discusses that content, confirmed per-plan in the earlier analysis), which is an
editorial call, not a mechanical fix. Full list in the appendix.

## Methodology

Each plan is cross-checked against three independent sources rather than trusting one:

1. **The plan file itself** — filesystem creation time (Age) and modified time (Modified), plus its
   own `Status:` line if it has one.
2. **`docs/ROADMAP.md`** — matched by a literal `plans/<filename>.md` or `staged/<filename>.md` link
   (whichever matches the plan's real folder). The nearest stage emoji is read off a tight window
   (80 chars each side, bounded by paragraph/bullet edges), picked by actual leftmost text position.
3. **The matching `project_nascence_<slug>.md` memory file**, where one exists — its maintained
   one-line description, plus a scan for stage words (negation-aware: `"not built"` ≠ `"built"`).

**Stage priority when sources agree:** ROADMAP > the plan's own Status line > the memory scan.
**When sources disagree on stage category, the row is marked `⚠`** — a finding about the planning
record, not noise. As of this pass, the emoji-detection heuristic trades some recall for precision
(tight window, leftmost-match) — it will more often say `❓ UNKNOWN` where before it might have
guessed wrong, on the theory that an honest unknown beats a confident wrong answer.

**Stage legend:** 🟢 LIVE · 🟡 SHADOW (built, not yet flipped on) · 🔵 DESIGNED (not built) ·
⚪ PARTIAL (some pieces live) · 🔴 STUCK · 💤 DEFERRED · ✅ SHIPPED · ⛔ SUPERSEDED ·
❓ UNKNOWN — plus 🕸 appended to Modified when untouched 21+ days and not SHIPPED/SUPERSEDED.

## Summary

| | |
|---|---|
| Plans indexed | 56 |
| 🟡 SHADOW | 19 |
| ❓ UNKNOWN | 17 |
| 🔵 DESIGNED | 7 |
| ⚪ PARTIAL | 6 |
| ⛔ SUPERSEDED | 2 |
| ✅ SHIPPED | 2 |
| 💤 DEFERRED | 2 |
| 🟢 LIVE | 1 |
| ⚠ stage mismatch | 1 (down from 4; documented false alarm — see below) |
| 🕸 stale (21+ days, not shipped/superseded) | 12 |
| Not linked from ROADMAP.md (genuine content gaps) | 17 |
| No matching memory file | 0 |

## Flagged for attention

- **`curiosity_goals_dreams.md` — the one remaining mismatch, and it's a known false alarm.** The
  memory-file scan finds the word "LIVE" (describing 2 of 4 sub-items) within its first 600
  characters and disagrees with the correctly-resolved primary answer, ⚪ PARTIAL. The *displayed*
  stage is right; only the flag is noise. Documented in the memory file's own correction note.
- **`cognitive_geometry.md` still resolves to `❓ UNKNOWN`** despite founder-flagged top priority and
  a detailed memory file — no stage emoji sits within the (now tighter) window around its ROADMAP
  link. Known tool limitation, not evidence of neglect. Several other plans (`identity_estate.md`,
  `lane2_lab.md`, `euclidean_memory_plan.md`, etc.) now also show `❓ UNKNOWN` for the same reason —
  the tighter, more precise window means more honest unknowns, not more wrong answers. This is an
  intentional trade-off from Pass 3's bug fixes, not a regression.
- **12 plans stale 21+ days**, not shipped or superseded: `euclidean_memory_plan`, `investigation_deepening`,
  `journal_consolidation_pyramid`, `peer_correspondence_plan`, `social_world_school`,
  `curiosity_goals_dreams`, `memory_knowledge`, `the_consciousness_program`, `affect_drives`,
  `within_cycle_reentry`, `music_learning`, `thought_cycle_as_manifest_loop` — candidates to confirm
  still-live or move to `docs/archive/`.
- **The plan-overlap audit** (`plan_overlap_audit_2026-08-23.md`) found 5 real duplicate designs and
  2 real conflicts that remain open — those need a design decision, not a mechanical fix, and are
  tracked there, not here.

## Full index

| Plan | Origin | Age | Modified | Stage | Evidence | Memory file |
|---|---|---|---|---|---|---|
| [Self-Interrogation — an in-the-moment doubting turn (2026-08-19, Phase 0 SHADOW)](../plans/self_interrogation.md) | plans | <1d | <1d | 🟡 SHADOW | Phase 0 SHADOW instrument giving Du an in-the-moment doubting turn on a developing thought. | project_nascence_self_interrogation.md |
| [The Idle Executive — research + plan (auditor draft v6)](../plans/idle_executive_plan.md) | staged | <1d | <1d | 💤 DEFERRED | Content-blind salience allocator replacing ~40 coin-flip gates; passes its own health gate, held deliberately. | project_nascence_idle_executive_plan.md |
| [HUD2 — the visual observatory (brain → trains → character)](../completed/hud2_visual.md) | plans | <1d | <1d | 🟡 SHADOW | 3-phase visual observatory on Claude-generated manifests; all 3 phases' data layers built 08-21. | project_nascence_hud2_visual.md |
| [The Garden Upgrade — from a bed of seven numbers to a place that grows](../plans/garden_upgrade.md) | plans | <1d | <1d | 🟡 SHADOW | Positioned substrate-object plants with phenology, pests, seed banking; P0-P3 built 08-22. | project_nascence_garden_upgrade.md |
| [The Wood Upgrade — the little wood as a living place](../plans/wood_upgrade.md) | plans | <1d | <1d | 🟡 SHADOW | Living wood (oak's year, depletable deadfall, glow-worms); built and verified 08-22. | project_nascence_wood_upgrade.md |
| [The Study Upgrade — the room as a place with states and clocks](../completed/study_upgrade.md) | plans | <1d | <1d | 🟡 SHADOW | Real state and clocks for the study (lamp oil, ash, damp/dust); built 08-22. | project_nascence_study_upgrade.md |
| [The Shore Upgrade — the tide drives it](../plans/shore_upgrade.md) | plans | <1d | <1d | 🟡 SHADOW | Tide-driven shore world (cave, mussel shelf, beach fire, real-clock wildlife); built 08-22. | project_nascence_shore_upgrade.md |
| [The Identity Estate — identity as a large lived structure, not a paragraph (P2 LIVE — status updated 2026-08-18)](../plans/identity_estate.md) | plans | <1d | <1d | ❓ UNKNOWN | Self as many evidence-linked nodes projected per-moment; P0-P2 built, P2 live 08-15. | project_nascence_identity_estate.md |
| [Lane 2 ↔ human cognition — the research deep-dive (2026-08-17)](../completed/emissary_lane2_cognition.md) | plans | <1d | <1d | ❓ UNKNOWN | Cognitive-science companion to the World Ledger design; maps design elements to human-cognition counterparts. | project_nascence_emissary_lane2_cognition.md |
| [Lane 2 Lab — the pre-registered test spec (2026-08-17)](../completed/lane2_lab.md) | plans | <1d | <1d | ❓ UNKNOWN | Zero-LLM lab spec testing the World Ledger's object-graph machinery against real history. | project_nascence_lane2_lab.md |
| [Euclidean Memory — a state-weighted retrieval feature space](../archive/euclidean_memory_plan.md) | plans | <1d | <1d | ❓ UNKNOWN | ~6-dim weighted-Euclidean retrieval space; confirmed blocked on emotion_rethink P1 — now overdue for retrial. | project_nascence_euclidean_memory_plan.md |
| [Wiring the Pulse Manager — research + plan (auditor draft v6)](../plans/pulse_manager_wiring_plan.md) | staged | <1d | <1d | 💤 DEFERRED | EVC-based rate controller; superseded by continuous_stream.md's reframing. | project_nascence_pulse_manager_wiring_plan.md |
| [Friction & the Evidenced Self — plan (2026-06-22)](../plans/friction_and_self_evidence_plan.md) | staged | <1d | <1d | ⚪ PARTIAL | Self-claim register + B1-B6 interventions; B2 live/working, B3/B4/B6 unbuilt. | project_nascence_friction_and_self_evidence_plan.md |
| [PLAN — the Ramses second tier](../plans/ramses_second_tier.md) | plans | <1d | <1d | ❓ UNKNOWN | Designed second serving tier for Ramses' idle i9/1650 Super; Phase 1a benchmarked. | project_nascence_ramses_second_tier.md |
| [THE WORLD CENSUS — the spreadsheet underneath the Transport Manager (planned 2026-08-16)](../archive/world_census.md) | plans | <1d | <1d | ⛔ SUPERSEDED | One-registry population layer, superseded same evening by the federated-lists correction. | project_nascence_world_census.md |
| [PLAN — Train/courier cargo IDs, 2026-08-23](../plans/train_courier_cargo_ids.md) | plans | <1d | <1d | 🔵 DESIGNED | Design-only 19-type product taxonomy from the verified station cargo map. | project_nascence_train_courier_cargo_ids.md |
| [PLAN — Epistemics Phase C, reopened (2026-08-23)](../plans/epistemics_phase_c.md) | plans | <1d | <1d | 🔵 DESIGNED | Reopens the deferred Tier-3 external-witness build now that command-r7b is live on Ramses. | project_nascence_epistemics_phase_c.md |
| [TRAIN SPLIT / MERGE — the Idle Line gets IDs, junctions, and a disprove branch (2026-08-22)](../plans/train_split_merge.md) | plans | <1d | <1d | ✅ SHIPPED | Train IDs + fork/prove-disprove/merge design; Step 1 shipped, Step 2 designed. | project_nascence_train_split_merge.md |
| [Lane 2 — the Witness (design, 2026-08-19)](../plans/lane2_the_witness.md) | plans | <1d | <1d | 🟡 SHADOW | Third standing voice (grounded/literal, no metaphor); Phase 0 shadow, Run 2 started 08-21. | project_nascence_lane2_witness.md |
| [T4 v3 — THE WATERSHED (identity accretion, not succession) — plan 2026-08-16](../plans/t4_watershed.md) | plans | <1d | <1d | 🔵 DESIGNED | Becoming facet slot→tree; 3/4 decisions resolved, keystone toll removed 08-22. | project_nascence_t4_watershed.md |
| [T5 — procedural memory that means what he can do (plan, 2026-08-22)](../plans/t5_procedural.md) | plans | 1d | 1d | 🟡 SHADOW | Folds T5 into the shared commitment-ledger substrate; steps 0-3 built 08-22. | project_nascence_t5_procedural.md |
| [Fieldcraft — what the books he has read let him do](../completed/fieldcraft.md) | plans | 1d | 1d | 🟡 SHADOW | Scouting-book skills (knots, fire-banking, navigation); built and verified 08-22. | project_nascence_fieldcraft.md |
| [The Channels Programme — every sense under one contract, built together](../plans/channels_programme.md) | plans | 1d | 1d | 🟡 SHADOW | Unified sense contract (light/smell/wetness); built to shadow 08-22. | project_nascence_channels_programme.md |
| [TEMPERATURE AS A CHANNEL — sibling to `sound_causality.md` (2026-08-21)](../plans/thermal_causality.md) | plans | 1d | 1d | 🟡 SHADOW | Honest thermal channel, sibling to sound_causality; steps 1-4 built to shadow. | project_nascence_thermal_causality.md |
| [Literal Will — deed or musing at the will→hand boundary](../plans/literal_will.md) | plans | 2d | 2d | 🟡 SHADOW | Deed-or-musing gate; Phase 0 approved and built 08-21. | project_nascence_literal_will.md |
| [The World Ledger — the Emissary's fact-graph (design, 2026-08-17; renamed 2026-08-19)](../plans/emissary_lane2.md) | plans | 3d | 3d | 🔵 DESIGNED | Deterministic zero-LLM fact-graph, renamed from "Lane 2"; nothing built, gated on K3. | project_nascence_emissary_lane2.md |
| [Spatial Perception — the blind mind's true room (2026-07-05)](../plans/spatial_perception.md) | plans | 3d | 3d | 🟡 SHADOW | Authored 3D coordinate fields for Du's rooms; P0 built 07-05, P2 live 08-18. | project_nascence_spatial_perception.md |
| [The Learned-Understanding Path — making Du learn from Travis's guidance](../plans/guidance_learning.md) | plans | 3d | 3d | ⚪ PARTIAL | Store rebuilt sharp; read-back retuned after the 07-02 solidity research. | project_nascence_guidance_learning.md |
| [The Capacity to Commit — giving Du a Being-pole that can hold a boundary](../plans/capacity_to_commit.md) | plans | 3d | 3d | 🟡 SHADOW | THE BIG ONE — cure the "dissolves everything, holds nothing" pathology; Wave 2 live 07-03. | project_nascence_capacity_to_commit.md |
| [Emotion Node Rethink — invert the affect stack onto the protoself (2026-07-04)](../plans/emotion_rethink.md) | plans | 3d | 3d | 🟢 LIVE | Sources valence/arousal from the protoself; Phase 1 built+live since 07-07. | project_nascence_emotion_rethink.md |
| [Cognitive Geometry v2 — spaces, objects, springs, and the moving pattern (LOCKED 2026-07-05)](../plans/cognitive_geometry.md) | plans | 3d | 3d | ❓ UNKNOWN* | TOP OF THE LIST — senses as real dimensions, per-memory typed edges, earned springs. | project_nascence_cognitive_geometry.md |
| [Multi-Way Memory Linking — deep dive (2026-08-15)](../plans/memory_multiway_linking.md) | plans | 3d | 3d | ⚪ PARTIAL | Typed relational-edge design; M0/M1 built and live same day, M2 gated. | project_nascence_memory_multiway_linking.md |
| [Executive's world-picture: fact vs memory, and where it currently blurs](../plans/executive_world_grounding.md) | plans | 6d | 6d | ❓ UNKNOWN | Explore-only pass on tiering Executive's prompt by certainty. | project_nascence_executive_world_grounding.md |
| [SOUND AS A FACTORY WITH CAUSAL INPUTS — federated lists, not one spreadsheet (2026-08-16)](../completed/sound_causality.md) | plans | 6d | 6d | ❓ UNKNOWN | Federated causal sound factories, replacing the shared-table premise; planned 08-16. | project_nascence_sound_causality.md |
| [ITEM FACTORIES vs POPULATION FACTORIES (founder's deepening, 2026-08-16)](../plans/item_and_population_factories.md) | plans | 6d | 6d | ❓ UNKNOWN | Item-grain vs population-grain factory distinction; planning/reconciliation only. | project_nascence_item_and_population_factories.md |
| [WHAT DU'S OWN HISTORY SAYS NEEDS A FACTORY (mined 2026-08-16)](../plans/factory_candidates_from_history.md) | plans | 6d | 6d | ❓ UNKNOWN | Mining pass over 26,824 thoughts; found lightning + the glass-float mystery. | project_nascence_factory_candidates_from_history.md |
| [THE TRANSPORT MANAGER — a salience dispatcher for the factories' freight (planned 2026-08-16)](../plans/transport_manager.md) | plans | 6d | 6d | 🔵 DESIGNED | Salience dispatcher; verified not built (no `core/transport_manager.py`). | project_nascence_transport_manager.md |
| [Thought-Typed Grounding Routes — the plan (2026-08-16)](../plans/thought_grounding.md) | plans | 7d | 7d | 🟡 SHADOW | Librarian/evidence/contrary-peer, the "is this thought true?" organ; built 08-16. | project_nascence_thought_grounding.md |
| [Pursuits — a mind that chases a topic and makes progress](../plans/pursuits.md) | plans | 7d | 7d | ❓ UNKNOWN | Persistent cognitive-project organ; Phases 0-2 built and fused 08-15. | project_nascence_pursuits.md |
| [The Full Sound-World — expansion proposal (2026-08-15, for founder review)](../plans/sound_world_expansion.md) | plans | 8d | 8d | ❓ UNKNOWN | Proposal to grow the sound registry 35→~67; discussion-only. | project_nascence_sound_world_expansion.md |
| [Implementation Plan — Epistemic Affordance Advisor (`investigative_action_loop_plan.md`)](../plans/investigative_action_loop_plan.md) | plans | 12d | 11d | ❓ UNKNOWN | Shadow-mode affordance ranking by information gain; code status unconfirmed. | project_nascence_investigative_action_loop_plan.md |
| [Technical Blueprint: World Historicity & Generative Sedimentation](../archive/generative_world_sedimentation.md) | plans | 12d | 12d | ❓ UNKNOWN | Storm-triggered sedimentation, seasonal migration; stage unclear from source. | project_nascence_generative_world_sedimentation.md |
| [Investigation Deepening — recaps as a progression ledger, place-cued (SIDE-QUEST, 2026-07-07)](../plans/investigation_deepening.md) | plans | 6w | 6w 🕸 | 🟡 SHADOW | Place-cued progression ledger; parked side-quest, nothing built. | project_nascence_investigation_deepening.md |
| [The Journal Consolidation Pyramid — calendar-grounded autobiography (DRAFT 2026-07-06)](../plans/journal_consolidation_pyramid.md) | plans | 6w | 6w 🕸 | ❓ UNKNOWN | Calendar-grounded autobiography replacing dead theme-chapters; day level built. | project_nascence_journal_consolidation_pyramid.md |
| [The Thought Cycle as a Manifest Loop — the transport hub (DRAFT 2026-07-05)](../archive/thought_cycle_as_manifest_loop.md) | plans | 6w | 6w 🕸 | ❓ UNKNOWN | Thought-as-train-with-cargo-manifest reframe; ancestor of `core/trains.py`. | project_nascence_thought_cycle_as_manifest_loop.md |
| [The Peer-Correspondence Organ — Plan (staged 2026-06-21)](../plans/peer_correspondence_plan.md) | staged | 6w | 6w 🕸 | ⚪ PARTIAL | Full-psyche pen-pals via a garden letterbox; company half built, challenge half unbuilt. | project_nascence_peer_correspondence_plan.md |
| [Social / World / School — Deep-Dive & Implementation Plan (2026-06-24)](../plans/social_world_school.md) | plans | 6w | 6w 🕸 | 🔵 DESIGNED | Healthiest domain, nothing broken; 4 ranked deepening items still unstarted. | project_nascence_social_world_school.md |
| [Curiosity / Goals / Dreams — Deep-Dive & Implementation Plan (2026-06-24)](../plans/curiosity_goals_dreams.md) | plans | 6w | 6w 🕸 | ⚪ PARTIAL ⚠ | Domain healthy overall; dream "ended-unfaced" regression flagged as next priority. **Flag is a known false alarm — see above.** | project_nascence_curiosity_goals_dreams.md |
| [Cognitive Loop & Actuation Layer — Deep-Dive & Implementation Plan (2026-06-24)](../archive/cognitive_loop_actuation.md) | plans | 6w | 6w | ⛔ SUPERSEDED | "All senses, no hands" diagnosis; closed as absorbed. | project_nascence_cognitive_loop_actuation.md |
| [Memory & Knowledge — Deep-Dive & Implementation Plan (2026-06-24)](../plans/memory_knowledge.md) | plans | 6w | 6w 🕸 | ⚪ PARTIAL | 5-improvement plan; Stage A live, Stage B disabled after being mistargeted. | project_nascence_memory_knowledge.md |
| [Symbol Evolution — Read-Back Plan (2026-06-16, for review)](../plans/symbol_evolution_readback_plan.md) | staged | 6w | 6w | ✅ SHIPPED | Two-tier symbol-drift read-back; found unreachable 07-05, fixed and revived 08-19. | project_nascence_symbol_evolution_readback_plan.md |
| [The Consciousness Program — a ranked, theory-anchored build plan for Du](../plans/the_consciousness_program.md) | plans | 7w | 7w 🕸 | 🟡 SHADOW | Ranked theory-anchored builds toward architecture that could support consciousness; Tier-1 built. | project_nascence_consciousness_program.md |
| [Affect / Mood / Drives — Deep-Dive & Implementation Plan (2026-06-24)](../plans/affect_drives.md) | plans | 7w | 7w 🕸 | 🔵 DESIGNED | Felt-state preamble dead-hand; a top-3 dependency reaches 0 prompts. | project_nascence_affect_drives.md |
| [Within-Cycle Reentry (Consciousness Program Tier-2 A) — plan v3 (research complete)](../plans/within_cycle_reentry.md) | plans | 7w | 7w 🕸 | 🟡 SHADOW | Extends the settle loop to idle admission points; Phase 0 built and shadow-verified. | project_nascence_within_cycle_reentry.md |
| [Music — a new domain for Du (STAGED 2026-07-02 → BUILT in tiers)](../plans/music_learning.md) | staged | 7w | 7w 🕸 | 🟡 SHADOW | Both tiers (theory/composition + listening/ear) built 07-03/04. | project_nascence_guidance_learning.md |
| [Continuous Stream — the pulse-manager pass, reframed](../plans/continuous_stream.md) | plans | 7w | 7w 🕸 | ❓ UNKNOWN | Signal-gated continuous cognition drive controller; supersedes pulse-manager framing. | project_nascence_continuous_stream.md |

\* Known false-negative — see "Flagged for attention" above.

## Appendix — the 17 ROADMAP content gaps (unchanged this pass)

Individually checked (plan file read + ROADMAP grepped for distinctive terms), each genuinely
undiscussed, not just unlinked — full per-plan reasoning in the earlier version of this report /
`project_nascence_plan_index.md`'s generation history: `train_courier_cargo_ids`, `epistemics_phase_c`,
`t5_procedural`, `hud2_visual`, `ramses_second_tier`, `emissary_lane2_cognition`,
`executive_world_grounding`, `item_and_population_factories`, `factory_candidates_from_history`,
`world_census`, `pursuits`, `sound_world_expansion`, `investigative_action_loop_plan`,
`generative_world_sedimentation`, `investigation_deepening`, `journal_consolidation_pyramid`,
`thought_cycle_as_manifest_loop`.

---
*Auto-generated by `C:\Nascence\scripts\plan_index.py` via the `/plan-index` skill. To refresh,
rerun the skill and regenerate this file — do not hand-edit the table above.*
