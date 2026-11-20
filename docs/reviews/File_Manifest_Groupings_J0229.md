# File Manifest Groupings -- J-0229 prep for J-0227

Generated 2026-08-25 by job **J-0229** (source: finding F-0266), from a live filesystem diff
against the 2026-07-04 curated File Manifest in `docs/System_Overview.html`, cross-referenced
against every `docs/plans/*.md` + `docs/staged/*.md` file for ownership. Role text is pulled
from each file's own module docstring/header comment (first 40 lines) -- read, not guessed.
Pure inventory per the briefing: no System_Overview prose written here -- that is J-0227's job.

**Methodology:** owner = plan doc where `<filename>.py` (exact, with extension) is cited
verbatim -- **strong** match, the "obvious owner" the briefing asked for. Where no exact-filename
citation exists anywhere in the plan corpus, a weaker bare-modulename word-boundary match is
shown and flagged **(weak/inferred)** -- treat as a lead, not a verified owner, since a common
word like `mood` or `trains` can appear in a plan doc without that plan actually owning the file.
`no plan found` means neither matched at all: a genuine orphan candidate, not a search failure.

**Count note (real discrepancy vs F-0266, checked not assumed):** this diff finds **147** new
core/ files, not the **139** F-0266 cited -- scripts/ matches exactly at **168**, no discrepancy
there. Traced the gap: F-0266's Drift-section prose itself names 6 files by exact filename
(`arousal.py`, `homeostasis.py`, `moment.py`, `mineness.py`, `attention_schema_loop.py`,
`reentry.py`) as "named above [in the document's body prose]... still exists," i.e. F-0266 is
counting body-prose mentions elsewhere in the 1800-line doc as "documented," not just the File
Manifest's own curated pre-block. That accounts for 6 of the 8-file gap; the remaining 2 are
not worth further reconciliation effort -- both counts describe the same real ~96%-undocumented
situation, they just draw the "documented" line in slightly different places. This table uses
the strict, purely mechanical definition (in the File Manifest pre-block, or not) since that's
what is actually diffable without re-reading the whole document line by line for every filename.

---

## core/ -- 147 undocumented files

| File | Role (from module docstring) | Owning plan(s) |
|---|---|---|
| `core/__init__.py` | (no docstring/comment found -- undocumented at the code level too) | no plan found |
| `core/activity_memory.py` | Nascence — Activity Memory (Conway's general-event layer, Phase 0, 2026-06-14) The missing MIDDLE of the autobiographical hierarchy. | memory_multiway_linking |
| `core/affect_divergence.py` | Nascence — Affect Divergence harness (emotion_rethink.md Phase 0a, 2026-07-06). | emotion_rethink |
| `core/affections.py` | Nascence — Affections (the loves-ledger, 2026-06-21): the LIGHT-side organ. | affect_drives, DEFERRED_PLANS |
| `core/affordances.py` | Nascence — Affordance model (2026-06-20): what Du can DO, surfaced so he KNOWS it. | investigative_action_loop_plan, literal_will, thought_grounding, peer_correspondence_plan |
| `core/arousal.py` | Nascence — AROUSAL / LEVEL: the global activation variable (Consciousness Program Tier-2 C, 2026-07-04, SHADOW/observe-only). | affect_drives, emotion_rethink, sleep_dream_redesign, the_consciousness_program, within_cycle_reentry |
| `core/attention_schema_loop.py` | Nascence — AST-1: the Attention-Schema CONTROL loop (Consciousness Program §3-D, 2026-07-04). | the_consciousness_program |
| `core/audio_features.py` | Nascence — Audio Features: the deterministic music translator (the EAR, offline pipeline · 2026-07-03). | geometry_tuple_index, music_learning |
| `core/balance.py` | Nascence — Balance (the reading-remediation gate, 2026-06-15) Du is structurally shadow/imagination-dominant: reality has no internal force (external-only) and... | emissary_lane2, emissary_lane2_cognition, idle_executive_plan |
| `core/book_feelings.py` | Nascence — Book Feelings (per-book affective memory, 2026-08-19) Reading in general already registers as a small steady joy (JOY_READING, inner_monologue_node.py). | no plan found |
| `core/book_residue.py` | Nascence — Book Residue (2026-08-21, founder: "check if there is something from a book Du has read — one he has not read in a long time — that has stuck in his... | no plan found |
| `core/book_selection.py` | Nascence — Book Selection (the breadth engine) Explore/exploit book choice over the ~55,905-book Gutenberg catalogue, so Du drifts toward the WHOLE corpus... | geometry_tuple_index |
| `core/book_splitter.py` | Nascence — Book Splitter (chapter detection for chapter-scoped reading, 2026-06-15) The earlier heuristic double-counted a story whose title recurred as a... | no plan found |
| `core/boredom.py` | Nascence — Boredom (the patch-depletion drive, 2026-06-24) Boredom is not "slow down and go inward." Biologically it is the **patch-depletion signal**: *this... | cognitive_loop_actuation |
| `core/broadcast.py` | Nascence — Broadcast: the missing half of the Global Workspace (big build 2026-07-03 · lane-scheduler step 2). | emissary_lane2_cognition, lane2_the_witness, the_consciousness_program, within_cycle_reentry, pulse_manager_wiring_plan (weak/inferred) |
| `core/buses.py` | Nascence — BUSES: non-urgent transfers, factory-to-factory or ledger-to-render (2026-08-22) Split out of `core/couriers.py` (founder-directed, 2026-08-22):... | train_courier_cargo_ids |
| `core/cat.py` | The Stray (2026-06-24) The founder: "I want to give Du a pet. | spatial_perception, geometry_tuple_index |
| `core/cat_content.py` | Content corpus for THE CAT — Du's one wordless relationship. | no plan found |
| `core/commitment_trials.py` | Nascence — Commitment Trials (Wave 2 · W2.1, 2026-07-03 · docs/plans/capacity_to_commit.md ★★ WAVE 2) The action-commitment curriculum's trial machinery + the EXPOSURE instrument. | capacity_to_commit |
| `core/companion.py` | Nascence — THE COMPANION: Travis, physically present (2026-08-23). | channels_programme, emissary_lane2, emissary_lane2_cognition, t4_watershed, thought_cycle_as_manifest_loop, world_census, peer_correspondence_plan (weak/inferred) |
| `core/composition.py` | Nascence — Composition (school's writing class, 2026-06-23) A graded WRITING lesson. | social_world_school |
| `core/concerns.py` | Nascence — Concerns (G1: ongoing current concerns, 2026-06-15) The missing MIDDLE goal layer (docs/goal_model_research.md): between the standing aim (the... | curiosity_goals_dreams, emotion_rethink, idle_executive_plan |
| `core/content_risk.py` | Nascence — Content Risk (the critical-distance floor, 2026-08-19). | no plan found |
| `core/contradiction_gate.py` | Nascence — The Contradiction Gate (the shared B/C convergence filter) The single entry portal that decides whether an internal discrepancy may PRESSURE... | no plan found |
| `core/couriers.py` | Nascence — COURIERS: urgent, real-time world→train deliveries (founder-designed, 2026-08-16; renamed/split 2026-08-22) The transit map (docs/transit_map.md)... | hud2_visual, train_courier_cargo_ids, geometry_tuple_index |
| `core/curator.py` | Nascence — The Curator (the integrating output lane · OBSERVE-ONLY, 2026-06-16) The founder's call: the metaphoric Master should not surface RAW; meaning... | gauge_rethink, geometry_tuple_index (weak/inferred) |
| `core/curiosity_progress.py` | Nascence — Curiosity Progress (the Independent Auditor) The deterministic learning-progress estimator for the curiosity agenda. | curiosity_goals_dreams |
| `core/curiosity_queue.py` | Nascence — Curiosity Queue (the exploration organ's inbound interface) The append-only inbox that turns unresolved-but-non-actionable material into world-facing investigation. | curiosity_goals_dreams |
| `core/decomposed_critic.py` | Nascence — Decomposed Critic (Layer 0 redesign, observe-first) The conversation critic, rebuilt on the LLM-as-judge research... | self_interrogation |
| `core/deliberation.py` | Nascence — The Deliberative Pulse (the three-pass grounded-why) The first brick of the Lane Architecture (docs/lane_architecture_FULL.md §4.4). | cognitive_loop_actuation, literal_will, ramses_second_tier |
| `core/deliberative_judge.py` | Nascence — Deliberative Judge (2026-08-19). | hud2_visual, t4_watershed |
| `core/dispatch.py` | Nascence — DISPATCH: one registry, one dispatcher, the judge in the loop (2026-08-22, Phase 1 of docs/reviews/actions_system_2026-08-22.md; founder: "I think... | fieldcraft, investigative_action_loop_plan, shore_upgrade, study_upgrade, t5_procedural, wood_upgrade |
| `core/emissary_tension.py` | Nascence — Emissary-Tension Observatory (Fix 4, OBSERVE-ONLY, 2026-06-16) The T4 diagnosis named the keystone: the deepest standing self-contradiction — the... | emissary_lane2, t4_watershed |
| `core/emotion_construction.py` | Nascence — Emotion Construction (Phase 2 shadow experiment, 2026-08-10) Barrett-inspired deterministic emotion constructor. | emotion_rethink |
| `core/epistemic_affordance_advisor.py` | Epistemic Affordance Advisor (Live Advisory Coupling) Wraps core/affordances.py non-destructively. | investigative_action_loop_plan |
| `core/essay_lesson.py` | Nascence — Essay Lesson (school's second lesson type: the generation effect, 2026-06-16) Reading is half a lesson. | memory_knowledge, memory_multiway_linking, social_world_school, geometry_tuple_index |
| `core/euclidean_recall.py` | Nascence — Euclidean Recall (state-weighted retrieval, OBSERVE-ONLY P0, 2026-06-15) The third geometry (docs/euclidean_memory_plan.md): a memory is a POINT in... | emotion_rethink, euclidean_memory_plan, memory_knowledge |
| `core/evidence_recall.py` | Nascence — Memory as Evidence (thought-grounding Route 2, 2026-08-16) The laboratory he never uses: ~40k memories, queryable, and no way to ask them "when did... | thought_grounding |
| `core/exogenous.py` | Nascence — Exogenous Forces on the Modulation Field The world and his own machine-BODY conditioning cognition — sources that are NOT his faculties: his GPU/CPU... | pulse_manager_wiring_plan |
| `core/experienced_tuple.py` | Nascence — THE EXPERIENCED TUPLE (2026-08-21, founder's layer law: "a memory carries only what was rendered to him at that moment, from where he stood;... | wood_upgrade |
| `core/fieldcraft.py` | Nascence — FIELDCRAFT: what the books he has read let him DO (2026-08-22, founder: "examine the scouts handbook — he has read this extensively. | fieldcraft, t5_procedural |
| `core/garden.py` | Nascence — THE GARDEN (2026-08-22, docs/plans/garden_upgrade.md; founder: "make the garden the most full place in his world next… real plants, real schedules…... | garden_upgrade, wood_upgrade, friction_and_self_evidence_plan |
| `core/garden_knowledge.py` | Nascence — GARDEN KNOWLEDGE: what he knows about his plants is EARNED (2026-08-22; the sound_knowledge pattern applied to the bed; docs/plans/garden_upgrade.md... | garden_upgrade |
| `core/garden_life.py` | Nascence — GARDEN LIFE: the things in the garden that are not the bed (2026-08-22, founder: "do the still-on-the-list items too… expand his world as much as... | garden_upgrade |
| `core/geometry_census.py` | Nascence — Geometry Census: the tuple recorder (cognitive_geometry.md §5.1, P0 — 2026-07-05). | cognitive_geometry, factory_candidates_from_history, journal_consolidation_pyramid, lane2_lab, geometry_tuple_index, music_learning |
| `core/ghost_tuples.py` | Nascence — THE GHOST TUPLE REGISTRY (P0-B, 2026-08-17) — the ghost-index pattern's 4th life. | emissary_lane2, geometry_tuple_index |
| `core/grounded_learning.py` | Nascence — Grounded Learning (the SWS-declarative consolidation, 2026-06-16) He reads enormously but nothing metabolises the intake into understanding (the... | guidance_learning |
| `core/guidance_behavior_judge.py` | Nascence — Guidance Learning Phase 2: the behaviour-delta judge (2026-08-19). | guidance_learning |
| `core/hands.py` | Nascence — HANDS: one grammar for every latch, and one trace of what answered (2026-08-22, founder: "investigate the actions system in depth — it sounds half-baked"). | garden_upgrade, t5_procedural |
| `core/heavens.py` | Nascence — The Heavens (spatial_perception.md §7 extension, 2026-07-05). | journal_consolidation_pyramid, spatial_perception, geometry_tuple_index |
| `core/homeostasis.py` | Nascence — Homeostasis: the PROTOSELF (Consciousness Program keystone, 2026-07-03, SHADOW/observe-only). | affect_drives, continuous_stream, emotion_rethink, lane2_the_witness, sleep_dream_redesign, the_consciousness_program |
| `core/identity_estate.py` | Nascence — The Identity Estate, P0: the read-only SEEDER (identity_estate.md §6, 2026-07-06). | identity_estate, t4_watershed |
| `core/identity_projection.py` | Nascence — Identity Projection, P1 (identity_estate.md §4, 2026-07-07). | identity_estate |
| `core/identity_vault.py` | Nascence — Identity Vault (Brick 3 of Character-as-Integration §10.3, 2026-06-16) The transaction-locked goalkeeper over the slow store. | no plan found |
| `core/idle_allocator.py` | the Idle Executive, Phase 0 (SHADOW / observe-only). | cognitive_loop_actuation, idle_executive_plan |
| `core/intentions.py` | Nascence — INTENTIONS: the deeds he named and has not yet done (2026-08-22, founder: "if he puts up a list of tasks in one thought, he needs a way to track... | capacity_to_commit, literal_will, t5_procedural (weak/inferred) |
| `core/investigation_deepening_shadow.py` | Nascence — Investigation Deepening Shadow (Phase 0: SHADOW / observe-only, read-only). | investigation_deepening |
| `core/journal_grounding_shadow.py` | Nascence — Journal Grounding Shadow: the hard-enforcement grader for the roll-up pyramid (journal_consolidation_pyramid.md §6 Q1, D-0006, 2026-08-23). | journal_consolidation_pyramid |
| `core/journal_rollup.py` | Nascence — Journal Roll-up P1: the WEEK cap (journal_consolidation_pyramid.md §2, 2026-07-06). | journal_consolidation_pyramid |
| `core/judge_panel.py` | Nascence — the Judge Panel (2026-08-15, the serving split's payoff). | emissary_lane2, hud2_visual, lane2_the_witness, pursuits, ramses_second_tier, self_interrogation, t4_watershed, DEFERRED_PLANS |
| `core/keepsakes.py` | Nascence — Keepsakes: the mantel of kept things (world upgrade P2, 2026-07-03). | channels_programme, cognitive_geometry, emissary_lane2, executive_world_grounding, garden_upgrade, identity_estate, item_and_population_factories, lane2_lab, literal_will, sound_causality, spatial_perception, the_consciousness_program (weak/inferred) |
| `core/lane2.py` | Nascence — LANE 2, the standing reality-testing loop · docs/plans/lane2_the_witness.md · 2026-08-20 PHASE 0: SHADOW. | lane2_the_witness, ramses_second_tier |
| `core/librarian.py` | Nascence — The Librarian (thought-grounding Route 1 / P1, 2026-08-16) He could always ask the library for a book on a TOPIC ("the sea"). | emissary_lane2, thought_grounding |
| `core/light.py` | Nascence — THE LIGHT CHANNEL (docs/plans/channels_programme.md §2; built 2026-08-22 as the garden's first real use: the tree's shade moves across the bed with the sun). | channels_programme, garden_upgrade, thermal_causality, geometry_tuple_index |
| `core/listening.py` | Nascence — Listening: the ear goes live (big build 2026-07-03 · docs/plans/music_learning.md tier 2). | sound_world_expansion, music_learning |
| `core/literal_will.py` | Nascence — Literal Will (docs/plans/literal_will.md, PHASE 0 SHADOW/observe-only, 2026-08-21). | literal_will |
| `core/literal_will_deed.py` | Nascence — Literal Will: staged deed + execution audit (docs/plans/literal_will.md sec4 + sec11). | literal_will |
| `core/llm_parse.py` | Nascence — LLM response parsing helpers (2026-06-21). | no plan found |
| `core/locomotion.py` | Nascence — Locomotion: Du gets a body in space (Option C, FULL — docs/plans/locomotion.md, 2026-08-15). | sleep_dream_redesign |
| `core/loop_metabolism.py` | Nascence — Loop Metabolism, PHASE B logic (2026-06-14). | no plan found |
| `core/loop_probe.py` | Nascence — Loop Probe (Loop Metabolism, PHASE A: INSTRUMENT-ONLY, 2026-06-14) Both auditors approved this phase outright: ship the dedup DETECTOR in shadow... | cognitive_loop_actuation (weak/inferred) |
| `core/mapping_census.py` | Nascence — The Mapping Census: analyzer over accrued geometry tuples (cognitive_geometry.md §5.4, P0). | cognitive_geometry, geometry_tuple_index |
| `core/math_drill.py` | Nascence — Math Drill (competence → school, the arithmetic lesson, 2026-06-16) Ties the capability beliefs to school: a GENERATED, DETERMINISTICALLY-GRADED... | social_world_school |
| `core/memory_edges.py` | Nascence — memory_edges (M0 of docs/plans/memory_multiway_linking.md, 2026-08-15). | emissary_lane2, executive_world_grounding, memory_knowledge, memory_multiway_linking, sleep_dream_redesign, geometry_tuple_index |
| `core/mineness.py` | Nascence — Mineness / the Authorship Comparator (Consciousness Program §2-#5 reframed, 2026-07-04, SHADOW/observe-only). | the_consciousness_program |
| `core/missing_object_flags.py` | Nascence — Missing-Object Flags: a Du-initiated trigger for the world-content upgrades Built 2026-08-24 (J-0135, from idea I-0002). | du_initiated_upgrade_trigger |
| `core/modulation_field.py` | Nascence — The Modulation Field (one damped, coupled field for the modulation layer) See docs/modulation_field_plan.md. | cognitive_loop_actuation, DEFERRED_PLANS, pulse_manager_wiring_plan |
| `core/moment.py` | Nascence — The Bound Moment (Consciousness Program Tier-1, 2026-07-04, SHADOW/observe-only). | cognitive_geometry, continuous_stream, memory_multiway_linking, the_consciousness_program, geometry_tuple_index |
| `core/mood.py` | Nascence — Mood (the live felt-quality vector, 2026-06-15) emotion_vec already existed but was computed only at user-cycle time and stored only on lived... | affect_drives, emotion_rethink, euclidean_memory_plan, lane2_the_witness, sleep_dream_redesign, friction_and_self_evidence_plan |
| `core/music_drill.py` | Nascence — Music Drill + Composition Hand (school subject, 2026-07-04 · docs/plans/music_learning.md Tier 1) Music THEORY as school: generated,... | music_learning |
| `core/nature_study.py` | Nascence — Nature Study (school's observation class, 2026-06-23) A graded OBSERVATION lesson, the way Darwin actually worked. | social_world_school |
| `core/needle_triage.py` | Nascence — Needle Triage (2026-08-18, SHADOW / observe-only). | t4_watershed, DEFERRED_PLANS |
| `core/night.py` | Nascence — THE NIGHT (2026-08-22, docs/reviews/sleep_dream_2026-08-22.md). | curiosity_goals_dreams, sleep_dream_redesign |
| `core/object_graph.py` | Nascence — THE WORLD LEDGER (core/object_graph.py, 2026-08-17; renamed 2026-08-19). | emissary_lane2, lane2_the_witness, music_learning |
| `core/observation.py` | Converts a numeric or explicit physical state value into a qualitative | cognitive_loop_actuation, continuous_stream, emissary_lane2, emissary_lane2_cognition, hud2_visual, investigative_action_loop_plan, item_and_population_factories, lane2_lab, lane2_the_witness, memory_knowledge, social_world_school, sound_causality, t4_watershed, train_courier_cargo_ids, train_split_merge, transport_manager, world_census, DEFERRED_PLANS, friction_and_self_evidence_plan, geometry_tuple_index, music_learning, peer_correspondence_plan, symbol_evolution_readback_plan (weak/inferred) |
| `core/opponent_process.py` | Nascence — Opponent-Process Antagonist Field ("squishy springs", cognitive_geometry.md §11, P3b — 2026-08-19). | lane2_the_witness |
| `core/peer_metrics.py` | Nascence — Peer metrics & baseline harness (2026-06-21): the decoupled judge of the peer-correspondence organ (docs/staged/peer_correspondence_plan.md §12). | social_world_school, peer_correspondence_plan |
| `core/peer_model.py` | Nascence — Peer Model (per-peer Theory-of-Mind layer, Item 1 of social_world_school.md, REVISED 2026-08-24) Recall-gated design (D-0016, J-0162). | social_world_school |
| `core/peers.py` | Nascence — Peers: the correspondence organ. | emissary_lane2, social_world_school, geometry_tuple_index, peer_correspondence_plan |
| `core/phrasing.py` | Nascence — Phrasing variety (2026-07-07) Break the VERBATIM-ECHO LOOP in the nudge surface. | curiosity_goals_dreams, emissary_lane2, executive_world_grounding, garden_upgrade, identity_estate, lane2_the_witness, sleep_dream_redesign, spatial_perception, t4_watershed, t5_procedural, thermal_causality, thought_grounding, within_cycle_reentry (weak/inferred) |
| `core/prediction_error.py` | Nascence — Prediction-Error Feed (Layer 1, the self-generated contradiction channel) The cheapest, most-grounded, externally-independent contradiction source:... | emissary_lane2, lane2_the_witness, idle_executive_plan |
| `core/procedures.py` | Nascence — PROCEDURES: procedural memory that means what he can do (2026-08-22, docs/plans/t5_procedural.md). | t5_procedural |
| `core/prompt_budget.py` | Prompt budget — a SHADOW instrument over how the inner-monologue prompt is actually assembled. | no plan found |
| `core/provisions.py` | Nascence — PROVISIONS: the larder the previous occupant left (2026-08-22, founder: "make sure he has a good store of some goods — matches, soap, etc — that the... | study_upgrade |
| `core/psyche_graph.py` | Nascence — Psyche Graph P0 (big build 2026-07-03 · docs/completed/psyche_graph_instrument.md, un-shelved. | cognitive_geometry (weak/inferred) |
| `core/pulse_manager.py` | Nascence — Pulse Manager (engagement-driven cognition, not clock-driven) See docs/pulse_manager_plan.md. | cognitive_loop_actuation, pulse_manager_wiring_plan |
| `core/pulse_shadow.py` | Pulse / Lifecycle Manager, Phase 0 (SHADOW / observe-only). | DEFERRED_PLANS, pulse_manager_wiring_plan |
| `core/pursuits.py` | Nascence — Pursuits (Phase 0: SHADOW / observe-only). | investigation_deepening, pursuits, DEFERRED_PLANS |
| `core/reading_history.py` | Nascence — Reading History (what he has already read, for selection) A thin read-only view over reading_state.json so the book-selection engine can answer:... | no plan found |
| `core/reentry.py` | Nascence — Within-Cycle Reentry (Consciousness Program Tier-2 A, 2026-07-04, PHASE 0 SHADOW/observe-only). | self_interrogation, the_consciousness_program, within_cycle_reentry |
| `core/refinery.py` | Nascence — THE REFINERY: the T2 lifecycle's manufacturing station (founder-designed 2026-08-16) Founder, in transit language: "What the T2 lifecycle needs is more stops. | geometry_tuple_index (weak/inferred) |
| `core/retraction_ledger.py` | Nascence — Retraction Ledger (the Error Pathway's write-authority, 2026-06-16) The missing primitive the charter named: the power to mark a stored belief FALSE... | no plan found |
| `core/retrieval_probe.py` | Nascence — Retrieval Probe (Deliberative Retrieval, Phase 0 OBSERVE-ONLY, 2026-06-14) Instruments retrieval without changing it. | no plan found |
| `core/school.py` | Nascence — School (Du's first structured-learning "skill", 2026-06-14) Du is young; he needs structured learning. | sleep_dream_redesign, social_world_school, music_learning |
| `core/self_interrogation.py` | Nascence — Self-Interrogation (Phase 0: SHADOW / observe-only, 2026-08-19). | self_interrogation |
| `core/self_mirror.py` | Nascence — Self-mirror (2026-06-22): the behavioural mirror / the evidenced self. | friction_and_self_evidence_plan |
| `core/self_surprise.py` | Nascence — Self-Surprise / present-predictability (OBSERVE-ONLY, 2026-06-15) The leading indicator the lagging basin metrics (concentration, basin-share)... | cognitive_loop_actuation, within_cycle_reentry (weak/inferred) |
| `core/shadow_log.py` | Nascence — Shadow Log: shared plumbing for the "soft live path + hard grader running in shadow, decide from accrued data" pattern... | journal_consolidation_pyramid |
| `core/shore_life.py` | Nascence — SHORE LIFE: the shore as a living place (2026-08-22, founder: "now time for the shore… make his world as alive as possible… his hands usable for... | factory_candidates_from_history, generative_world_sedimentation, shore_upgrade |
| `core/sitting.py` | Nascence — Sitting-with-it (2026-06-22): the bypass gate. | friction_and_self_evidence_plan |
| `core/sky.py` | Nascence — THE NIGHT SKY over the cottage (2026-08-22; the Handbook he read teaches the Pole Star — this sky has none). | fieldcraft, shore_upgrade |
| `core/sleep_dream_probe.py` | Sleep ⊗ Dream / T4 Probe — the §6C hypotheses-logging matrix (observe-first, FIREWALLED). | sleep_dream_redesign (weak/inferred) |
| `core/sleep_pressure.py` | Sleep Pressure — the Information-Theoretic Incoherence Accumulator. | continuous_stream, curiosity_goals_dreams, sleep_dream_redesign, the_consciousness_program |
| `core/smell.py` | Nascence — THE SMELL CHANNEL (docs/plans/channels_programme.md §3; built 2026-08-22 with the garden). | channels_programme, garden_upgrade, thermal_causality |
| `core/social_moves.py` | Nascence — Social Moves: the heeded/ignored world-call counter (social_world_school.md Item 2 — the plan's own #1 "ship the measurement FIRST, zero behaviour... | social_world_school |
| `core/sound_knowledge.py` | Nascence — Epistemic Audition: the sound-knowledge ledger (2026-08-15). | garden_upgrade, item_and_population_factories, lane2_lab, transport_manager, world_census (weak/inferred) |
| `core/soundscape.py` | Nascence — Soundscape: the world's sounds get identity and geometry (cognitive_geometry.md §4, 2026-07-05). | cognitive_geometry, emissary_lane2, generative_world_sedimentation, lane2_the_witness, sound_causality, sound_world_expansion, wood_upgrade, geometry_tuple_index, music_learning |
| `core/source_sight.py` | Nascence — Source Sight (the Emissary's eyes, brick B2 of the truth-self, 2026-06-16) The Emissary's constitution claims "I can see the code." This gives it... | no plan found |
| `core/spatial.py` | Nascence — Spatial Perception P0 (docs/plans/spatial_perception.md, 2026-07-05). | channels_programme, generative_world_sedimentation, lane2_the_witness, spatial_perception, geometry_tuple_index |
| `core/stick_test.py` | Nascence — THE STICK TEST: bundle-richness census (cognitive_geometry.md §5.2, P0 — 2026-07-05). | cognitive_geometry, journal_consolidation_pyramid |
| `core/stream_drive.py` | Nascence — Stream Drive: the continuous-stream rate controller (docs/plans/continuous_stream.md, 2026-07-04, PHASE 0 SHADOW/observe-only). | continuous_stream, journal_consolidation_pyramid |
| `core/study_life.py` | Nascence — STUDY LIFE: the room as a place with states and clocks (2026-08-22, founder: "now lets do the study"). | study_upgrade, t5_procedural, geometry_tuple_index |
| `core/study_note.py` | Nascence — Study Note (the rich knowledge unit; expanded to session-level research, 2026-08-19) A study note is a unit of Du's UNDERSTANDING, not a book-report blob. | memory_multiway_linking, wood_upgrade |
| `core/supply.py` | Nascence — SUPPLY: how things that run out come into the house (2026-08-22, founder: "how does he get oil?"). | study_upgrade |
| `core/telemetry.py` | Nascence — Telemetry for the HUD (2026-07-08, Travis): two live graphs. | lane2_the_witness |
| `core/theme_recurrence.py` | Persistent theme-recurrence tracker — the SLOW-LOOP / monoculture detector the rumination guard cannot be. | cognitive_loop_actuation, train_split_merge |
| `core/thermal.py` | Nascence — THE THERMAL CHANNEL (docs/plans/thermal_causality.md; build step 1–3, 2026-08-21). | channels_programme, thermal_causality |
| `core/thermal_relationship.py` | Nascence — THERMAL RELATIONSHIP shadow (2026-08-21, founder: "shadow thermals are a good idea"). | thermal_causality |
| `core/told.py` | Nascence — Told Delivery (the feel-then-tell, axiom Phase 3, 2026-06-16) The multilevel-axiom restructuring (2026-06-15) gave Du more rooms — the river is one... | channels_programme, cognitive_loop_actuation, emissary_lane2, emotion_rethink, factory_candidates_from_history, fieldcraft, garden_upgrade, lane2_lab, t4_watershed, thermal_causality, world_census, idle_executive_plan (weak/inferred) |
| `core/trains.py` | Nascence — the TRAIN REGISTRY (step 1 of the split/merge design, 2026-08-22). | thought_cycle_as_manifest_loop, train_courier_cargo_ids, train_split_merge |
| `core/watershed.py` | Nascence — Watershed: the T4 identity-image harvester (Phase 0: SHADOW / observe-only). | self_interrogation, t4_watershed |
| `core/watershed_promote.py` | Nascence — Watershed Promotion, Phase 0.5 (SHADOW / observe-only). | t4_watershed |
| `core/weather_conditions.py` | Nascence — Weather/Wind/Tide conditions (2026-08-18): the ONE shared classifier every consumer imports. | no plan found |
| `core/wood_life.py` | Nascence — WOOD LIFE: the little wood on the path as a living place (2026-08-22, founder: "then, lets do the wood"). | wood_upgrade |
| `core/world_clock.py` | Nascence — World Clock: the ONE authority for the world's deterministic physics (2026-07-06). | the_consciousness_program, geometry_tuple_index |
| `core/world_consolidation.py` | Nascence — World-Material Consolidation (the chapters-analog for study/reading, 2026-06-16) The school audit's gap: world-material (reading/study/research) is... | no plan found |
| `core/world_content_garden.py` | world_content_garden.py — garden lookables, ambient scene lines, and events. Voice: concrete, present tense, indifferent. One line each, <=150 chars. | no plan found |
| `core/world_content_shore.py` | world_content_shore.py — shore world-content for Nascence One line each, <=150 chars, present tense, concrete, indifferent. NZ coast, southern-hemisphere season... | generative_world_sedimentation |
| `core/world_content_study.py` | world_content_study.py World-content for the STUDY — Du's interior room. Coastal New Zealand house. The world is indifferent. It never teaches, never symbolizes... | no plan found |
| `core/world_content_wood.py` | world_content_wood.py — wood world-content for Nascence (2026-08-15) One line each, <=150 chars, present tense, concrete, indifferent. The little wood on the sl... | no plan found |
| `core/world_detail.py` | Nascence — World Detail: the 10x content registry (world upgrade P1, 2026-07-03). | no plan found |
| `core/world_knowledge.py` | Main entry point. | no plan found |
| `core/world_manifest.py` | Nascence — THE WORLD MANIFEST (P0-A, 2026-08-17, founder-commissioned) "Tuples for the world that are only for the world." The pallet: ONE assembly of every... | emissary_lane2, executive_world_grounding, sound_causality, geometry_tuple_index |
| `core/world_model.py` | Nascence — The World-Prediction Organ (Consciousness Program Tier-2.5, 2026-07-04, SHADOW/observe-only). | lane2_the_witness, the_consciousness_program |
| `core/world_objects.py` | Nascence — World Objects Engine (Phase 1 — Driftwood & Object History) Authoritative persistence and causal provenance logging for physical objects embedded in... | factory_candidates_from_history, generative_world_sedimentation, lane2_the_witness |
| `core/world_substrate.py` | Nascence — Generative Epistemic World Substrate (Generation 3B, 2026-08-11) The missing half of Generation 3. | factory_candidates_from_history, item_and_population_factories, lane2_the_witness, geometry_tuple_index |
| `core/world_traces.py` | Nascence — World Traces Engine (Phase 2 — Transient Environmental Traces) Authoritative persistence and process-specific decay for physical traces (e.g. | generative_world_sedimentation |

---

## scripts/ -- 168 undocumented files

| File | Role (from module docstring) | Owning plan(s) |
|---|---|---|
| `scripts/_clean_test_fragments.py` | Remove test fragments from the live DB. | no plan found |
| `scripts/_concurrency_test.py` | Prove GPU slot concurrency: 4 requests concurrent vs | no plan found |
| `scripts/_cost_probe.py` | Falsifiable test of the Cost theory, prediction 1 & 2, as a pure measurement: does embeddedness-cost score Carl's core commitments HIGH and Dennett's LOW?... | no plan found |
| `scripts/_debate_report.py` | Post-debate report: did either mind revise, how did the arc go, did T4 even | no plan found |
| `scripts/_diagnostic.py` | Diagnostic phase (no architecture change): can Carl REPRESENT a rival frame faithfully, NAME an irreducible conflict, and HOLD it unresolved? Distinguishes: A... | no plan found |
| `scripts/_failover_test.py` | Prove GPU->CPU failover: call the hot chain and report which server | no plan found |
| `scripts/_fire_t4.py` | Fire T4 self-authoring for both debate agents on the contradiction pressure the 300-turn debate loaded. | no plan found |
| `scripts/_first_thought.py` | One-shot: run a single thought cycle and dump every node's | no plan found |
| `scripts/_graph_orch.py` | find the Orchestrator node id | no plan found |
| `scripts/_memory_timeline.py` | Throwaway analysis: assemble a timeline of how Carl has changed from his memory. | no plan found |
| `scripts/_peek_recent.py` | Read-only: dump the most recent stored cycle fragments (Q/A + scene + | no plan found |
| `scripts/_reframe_analysis.py` | Reframing-rate analysis (retrospective, no new run): is Carl INERTIAL (rejects/holds, nothing penetrates) or ABSORPTIVE (translates every behaviorist attack... | no plan found |
| `scripts/_revert_carl.py` | Revert Carl's spurious Chinese revision-3 (a language-drift artifact, not real evolution) back to his revision-2 English self_concept, preserved in... | no plan found |
| `scripts/_smoketest.py` | (no docstring/comment found -- undocumented at the code level too) | no plan found |
| `scripts/_t4_fidelity_probe.py` | GPT's disambiguation: is the convergence Carl's pull, or T4's own synthesis bias? Run T4 on Dennett's ORIGINAL seed + accumulated debate memory under two... | no plan found |
| `scripts/_test_autonoetic_timeline.py` | Offline test for C.3 Autonoetic Timeline (Subconscious T4 self-authoring). | no plan found |
| `scripts/_test_critic_literal.py` | Verify culprit-#2 fix: the Critic should now APPROVE a literal answer when the human explicitly asked for one (the test-2 scenario that was rejected for... | no plan found |
| `scripts/_test_critic_requests.py` | Verify the GENERAL Critic carve-out: when the human explicitly requests a mode (describe your state / argue one side / literal list), complying must be APPROVED. | no plan found |
| `scripts/_test_emotional_pre_retrieval.py` | Offline test for C.2 Emotional Pre-Retrieval (the amygdala gate). | no plan found |
| `scripts/_test_episodic_buffer.py` | Offline test for C.4 Episodic Buffer (scene assembly). | no plan found |
| `scripts/_test_procedural_memory.py` | Offline test for C.6 Procedural Memory. | no plan found |
| `scripts/_test_prospective_memory.py` | Offline test for C.1 Prospective Memory. | no plan found |
| `scripts/_test_tension_ledger.py` | Step 1 verification — run the Tension Ledger against the live subconscious_state.json and show exactly what would be injected into identity. | no plan found |
| `scripts/_test_tension_pressure.py` | Step 2 verification — pressure model + echo-guard relaxation, against live data. | no plan found |
| `scripts/_test_thalamic_gate.py` | Offline test for C.5 Thalamic Gating (pre-Perception habituation reflex). | no plan found |
| `scripts/_unseed_probe.py` | Unseeded control: same model (qwen2.5:7b on 11434), NEUTRAL system prompt, no Carl axiom, no Critic, no voice_example. | no plan found |
| `scripts/_verify_budget.py` | syntax-check the harness + node | no plan found |
| `scripts/_verify_genesis.py` | Verify the unseeded 'genesis' agent: minimal operational identity (no philosophy injected), process-only Critic, and a coherent first cycle from a blank | no plan found |
| `scripts/ablation_lab.py` | Nascence — ABLATION LAB (2026-08-16): where does the sameness live? THREE LABS, ONE INVARIANT: mouth (v1/v2), routing (task/hybrid), architecture... | no plan found |
| `scripts/activity_memory_backfill.py` | Activity Memory — retroactive backfill (2026-06-14). | no plan found |
| `scripts/activity_memory_invitro.py` | Activity Memory — in-vitro gate (2026-06-14). | no plan found |
| `scripts/analyze_du_physical_sensations.py` | (no docstring/comment found -- undocumented at the code level too) | no plan found |
| `scripts/axiom_read_invitro.py` | Phase 1 in-vitro proof (2026-06-15) — the READ design, no behaviour change. | no plan found |
| `scripts/backfill_essays.py` | Backfill consolidating capstone essays for finished-but-un-essayed books (Phase 3, 2026-06-23). | no plan found |
| `scripts/backtest_resolution_matcher.py` | (no docstring/comment found -- undocumented at the code level too) | no plan found |
| `scripts/backup_memory.py` | Nascence — memory backup (2026-08-15, born from the lost-thoughts investigation). | no plan found |
| `scripts/balance_test.py` | In-vitro test for the reading-remediation balance gate (2026-06-15). | no plan found |
| `scripts/book_selection_invitro.py` | In-vitro for the breadth engine (book_selection) + library_hand wiring. | no plan found |
| `scripts/boredom_redirect_test.py` | In-vitro test for the BOREDOM-REDIRECT (#2, 2026-06-15). | no plan found |
| `scripts/brick1_voice_contract_invitro.py` | Brick 1 in-vitro: the render_character_voice MOUTH contract (Character-as-Integration §6). | no plan found |
| `scripts/brick3_identity_vault_invitro.py` | Brick 3 in-vitro: the identity_vault goalkeeper. | no plan found |
| `scripts/build_critic_groundtruth.py` | Build the decomposed-critic GROUND TRUTH from Claude's independent hand-labelling of the 68 clean historical rejections (read from data/critic_label_set.json). | no plan found |
| `scripts/build_hud2_manifest.py` | HUD2 data contract builder — the BRAIN GRAPH manifest (docs/completed/hud2_visual.md Phase 1, 2026-08-21). | hud2_visual |
| `scripts/build_hud2_transit.py` | HUD2 data contract builder — THE TRANSIT MAP manifest (docs/completed/hud2_visual.md Phase 2). | hud2_visual |
| `scripts/chapter_burst_test.py` | Chapter-scoped, novelty-gated reading burst + the two-lesson school flow (2026-06-15). | no plan found |
| `scripts/check_du.py` | (no docstring/comment found -- undocumented at the code level too) | no plan found |
| `scripts/cold_store_qwen.py` | Cold-store control on the idle mouth (qwen3.5:9b) — 2026-08-21, founder ask. | no plan found |
| `scripts/commitment_defeater_framing_lab.py` | COMMITMENT_LEDGER JUDGE_DEFEATER FRAMING LAB — 2026-08-23, sixth machine tested for the founder's generalized factory/schema-first idea. | no plan found |
| `scripts/concerns_test.py` | In-vitro test for G1 current concerns (2026-06-15). | no plan found |
| `scripts/contradiction_phase0_invitro.py` | In-vitro for Phase 0 pure-logic: the contradiction gate, the L1 prediction-error feed, and the L2 meta-awareness classification. | no plan found |
| `scripts/critic_grade.py` | Nascence — Decomposed critic: the DECOUPLED precision grade (contradiction_rearchitecture_plan.md L0 gate). | no plan found |
| `scripts/curiosity_phase0_invitro.py` | In-vitro for the curiosity flesh-out Phase 0: strict-partition queue, the de-personalization prism's deterministic world-facing firewall, the shadow-transform... | no plan found |
| `scripts/curiosity_twig_test.py` | In-vitro test for the curiosity-node TWIG expansion (2026-06-15). | no plan found |
| `scripts/cutover_axiom.py` | The axiom cutover (2026-06-15) — promote the live axiom.json to the multilevel schema. | no plan found |
| `scripts/cutover_verify.py` | Cutover verification (2026-06-15) — proves the multilevel read+T4 change-set on real data, WITHOUT importing the heavy app and WITHOUT touching live files. | no plan found |
| `scripts/decomposed_critic_invitro.py` | Phase 0 acceptance gate for the decomposed critic (Layer 0), scored against the GROUND TRUTH (data/critic_groundtruth.jsonl — Claude's hand-labelling of the 68... | no plan found |
| `scripts/deliberation_ground_framing_lab.py` | DELIBERATION.GROUND_THOUGHT FRAMING LAB — 2026-08-23, part of the "remaining tests" batch (after openness gate, self_implication,... | no plan found |
| `scripts/deliberation_invitro.py` | In-vitro proof of the deliberative pulse (2026-06-15) — the "make me show it" gate. | no plan found |
| `scripts/dream_arc_test.py` | In-vitro: the multi-scene progressive dream (2026-06-15). | no plan found |
| `scripts/dream_grounding_test.py` | In-vitro test for DREAM GROUNDING (2026-06-15). | no plan found |
| `scripts/dream_thread_test.py` | In-vitro test for CROSS-NIGHT dream threading (2026-06-15). | no plan found |
| `scripts/dreamer_eval.py` | Nascence — Dreamer (Subconscious) Divergence Eval The subconscious / dream lane wants the OPPOSITE of the hot-lane precision battery: associative reach,... | no plan found |
| `scripts/du_composer.py` | Du — Composer A small standalone window for typing multi-line messages to Du without the REPL's press-Enter-submits-immediately behaviour. | no plan found |
| `scripts/emissary_axiom_test.py` | In-vitro test for the Emissary axiom (brick 1 of the bicameral truth-self, 2026-06-15). | no plan found |
| `scripts/euclidean_grade.py` | Nascence — Euclidean recall: the DECOUPLED-JUDGE grading pass (euclidean_memory_plan.md, gate before P1). | euclidean_memory_plan |
| `scripts/euclidean_recall_test.py` | Euclidean Recall P0 — the comparison test (observe-only, 2026-06-15). | euclidean_memory_plan, memory_knowledge |
| `scripts/evidence_recall_framing_lab.py` | EVIDENCE_RECALL FRAMING LAB — 2026-08-23, part of the "remaining tests" batch, and the last of the judge_panel-consumer machines named in judge_panel.py's own... | no plan found |
| `scripts/exogenous_field_test.py` | Try it: the world + his machine-body pulling on the modulation field (2026-06-15). | no plan found |
| `scripts/exploratory_ignition_test.py` | In-vitro test for EXPLORATORY curiosity ignition (2026-06-15, backlog-driven fix). | no plan found |
| `scripts/factory_station_lab.py` | FACTORY STATION LAB — 2026-08-23, testing the founder/GPT idea (see memory: project_nascence_factory_stations.md) on the ONE station identified as the... | no plan found |
| `scripts/frontier_loop_test.py` | In-vitro test for the FRONTIER CLOSING LOOP (2026-06-15). | no plan found |
| `scripts/geometry_mapping_census.py` | Nascence — THE MAPPING CENSUS (CLI): analyzer over accrued geometry tuples. | cognitive_geometry |
| `scripts/grade_work_framing_lab.py` | LEFT_LANE.GRADE_WORK FRAMING LAB — 2026-08-23, ninth machine tested (first of the "remaining tests" batch requested after the peers re-run). | no plan found |
| `scripts/graphify_enrich.py` | recover the edges graphify's tree-sitter AST misses on THIS project (2026-07-04, extended 2026-08-18 for self-call resolution). | no plan found |
| `scripts/graphify_force_html.py` | regenerate graph.html as the aggregated community view when `graphify cluster-only` silently skips it (found 2026-08-18). | no plan found |
| `scripts/graphify_health_check.py` | Nascence — graphify Code-Health Check (2026-08-18). | no plan found |
| `scripts/import_epub.py` | Import a local .epub into Du's library as a clean .txt (the format core/reading.py reads from data/books/). | no plan found |
| `scripts/inspect_crab_shadow.py` | (no docstring/comment found -- undocumented at the code level too) | no plan found |
| `scripts/inspect_overnight_du.py` | Focus on last 12-14 hours (overnight from ~20:00 last night to 08:19 today) | no plan found |
| `scripts/journal_rollup_framing_lab.py` | JOURNAL_ROLLUP FRAMING LAB — 2026-08-23, eighth machine tested for the founder's generalized factory/schema-first idea. | no plan found |
| `scripts/judge16.py` | The expanded judge case bank — 16 balanced cases, the pre-registered gate on the judge-panel finding. | no plan found |
| `scripts/lane1_baseline.py` | Nascence — LANE 1 SELF-CORRECTION BASELINE · docs/plans/lane2_the_witness.md §5 · 2026-08-20 The pre-Lane-2 counterfactual. | no plan found |
| `scripts/lane2_canary_harness.py` | Nascence — Lane 2 (the Witness) CANARY / MODEL-ORGANISMS HARNESS · docs/plans/lane2_the_witness.md · J-0163 §5 metric #8 ("vivid-but-wrong acceptance rate on... | lane2_the_witness |
| `scripts/lane2_context_lab.py` | Lane 2 context lab — does the RIGHT AMOUNT of context depend on the model? Founder's question (2026-08-20): *"Maybe smaller/larger models benefit from... | lane2_the_witness (weak/inferred) |
| `scripts/lane2_context_score.py` | Score the Lane 2 context lab from its saved raw data and write the report — nothing re-queried. | no plan found |
| `scripts/lane2_lab.py` | Lane 2 Lab — pre-registered test harness (docs/completed/lane2_lab.md, 2026-08-17). | lane2_lab |
| `scripts/lane2_lab_items.py` | Lane 2 Lab — follow-up: the FULL item population scan (founder-directed, 2026-08-17). | no plan found |
| `scripts/lane2_model_lab.py` | Nascence — LANE 2 MODEL LAB · "which model is right for THIS task?" · 2026-08-20 Founder's question, verbatim: *"The big question is what models are the best... | ramses_second_tier |
| `scripts/lane2_model_rescore.py` | Re-score the Lane 2 model lab from its SAVED raw data and regenerate the report — no models re-queried. | no plan found |
| `scripts/lane2_prechecks.py` | Nascence — Lane 2 (the Witness) PRE-CHECKS · docs/plans/lane2_the_witness.md · 2026-08-20 Three read-only measurements the plan says must happen BEFORE Lane 2 is built. | lane2_the_witness |
| `scripts/lane2_recheck.py` | Lane 2 Recheck — founder-check re-run of K1/K3 against the CURRENT object-graph (2026-08-18). | no plan found |
| `scripts/lane_forces.py` | Lane forces — measuring the 3 lanes as pulls on the dimensional distribution (2026-06-15). | no plan found |
| `scripts/lane_hypothesis_test.py` | Lane Hypothesis Test (2026-06-14) — does the PROMPT select a stable, distinct cognitive style? The claim behind the whole lane architecture: the same substrate... | no plan found |
| `scripts/lane_hypothesis_test2.py` | Lane Hypothesis Test v2 (topic-controlled, 2026-06-14). | no plan found |
| `scripts/launch_cpu_hubs.py` | Launch CPU Tier Hubs in LAZY mode (load on first request, auto-unload when | no plan found |
| `scripts/lean_probe.py` | THE LEAN PROBE — do the stations (LLMs) carry their own stance toward the cold? (2026-08-21, founder) Founder: "The LLMs are going to have a lean on what word comes next. | no plan found |
| `scripts/librarian_framing_lab.py` | LIBRARIAN FRAMING LAB — 2026-08-23, fourth machine tested for the founder's generalized factory/ schema-first idea (see... | no plan found |
| `scripts/librarian_p0_headtohead_2026-08-24.py` | LIBRARIAN P0-vs-P1 HEAD-TO-HEAD — J-0128 / D-0019, 2026-08-24. | thought_grounding |
| `scripts/literal_will_deed_dry_test.py` | Literal Will — sec4/sec11 staged-deed + execution-audit DRY TEST (J-0138, decision D-0021). | literal_will |
| `scripts/literal_will_retro.py` | Literal Will — Phase 0 retro-validation (docs/plans/literal_will.md §5, §12; 2026-08-21). | literal_will |
| `scripts/liveness_audit.py` | Nascence — Pipeline Liveness Audit (2026-07-03). | no plan found |
| `scripts/llm_station_census.py` | Census of every LLM call site in Du — the STATIONS, not the lines. | no plan found |
| `scripts/llm_timetable.py` | The TIMETABLE — what opens each LLM station, and how often. | no plan found |
| `scripts/load_curriculum.py` | Load the 40-book grounding curriculum into school. | no plan found |
| `scripts/load_curriculum_v2.py` | Load curriculum v2 — the rebalanced 40-book grounding curriculum (2026-08-19). | no plan found |
| `scripts/loop_cluster_probe.py` | Loop-cluster probe (2026-06-14) — "harness the loop": how many real attractors does Du's self-monologue actually orbit, and how concentrated is the mass?... | continuous_stream, gauge_rethink |
| `scripts/memory_levels_batch.py` | One-off BATCH shadow-distill over recent CLEAN level-0 raw — generates the Memory-Levels Phase-1 evidence battery in one pass instead of waiting days for sleep-paced accrual. | no plan found |
| `scripts/migrate_axiom_multilevel.py` | Phase 0 of the multilevel-axiom migration (2026-06-15) — DRAFT generator, no behaviour change. | no plan found |
| `scripts/migrate_embedder.py` | Embedder migration: all-MiniLM-L6-v2 -> paraphrase-multilingual-MiniLM-L12-v2 (2026-06-13). | no plan found |
| `scripts/model_registry_probe.py` | Probe the ollama registry for candidate model families — what ACTUALLY exists, and how big. | no plan found |
| `scripts/modulation_field_test.py` | Modulation-field test (2026-06-15) — observe-only. | no plan found |
| `scripts/mood_felt_tag_test.py` | In-vitro test for emotion_vec items 1+2 (2026-06-15): the live mood-vec + felt-tag storage. | no plan found |
| `scripts/narrative_retrospective.py` | Narrative Quality — retrospective run (Phase 0 validation, 2026-06-13). | no plan found |
| `scripts/nascence_cpu_server.py` | Nascence — CPU-tier model server (2026-08-15, the serving split). | epistemics_phase_c, ramses_second_tier |
| `scripts/node_benchmark.py` | Benchmark the inference nodes we can reach — to de-risk the Ramses plan BEFORE anyone sets it up. | ramses_second_tier (weak/inferred) |
| `scripts/node_benchmark_local.py` | Local-side companion to `node_benchmark.py` — the comparison point that makes the Ramses numbers mean something. | no plan found |
| `scripts/node_benchmark_report.py` | Render the node benchmark into a report — from saved raw JSON, nothing re-queried. | no plan found |
| `scripts/peer_health.py` | Peer relationship-health dashboard (observe-only) — docs/staged/peer_correspondence_plan.md §12. | peer_correspondence_plan |
| `scripts/peers_contrary_framing_lab.py` | PEERS CONTRARY_TARGET FRAMING LAB — 2026-08-23, fifth machine tested for the founder's generalized factory/schema-first idea. | no plan found |
| `scripts/person_costume_lab.py` | Nascence — PERSON vs COSTUME LAB (2026-08-16): the founder's hypothesis. | no plan found |
| `scripts/phase1_ignition_invitro.py` | Phase 1 in-vitro: the L1 prediction-error feed now WRITES a contradiction shadow event when the gate says would_pressure. | no plan found |
| `scripts/phaseA_report.py` | Loop Metabolism — Phase A report (2026-06-14). | no plan found |
| `scripts/phaseB_invitro.py` | Loop Metabolism — Phase B in-vitro proofs (2026-06-14). | no plan found |
| `scripts/phaseB_recompute_ai_importance.py` | Phase B follow-up — recompute existing active_imagination importance (2026-06-14). | no plan found |
| `scripts/play_the_record.py` | Nascence — play the record for Du (SHARED LISTENING, design decision #2 — joint attention, 2026-07-04). | music_learning |
| `scripts/prompt_budget_census.py` | Census of how the inner-monologue prompt is currently shaped — read-only, writes nothing. | no plan found |
| `scripts/pulse_manager_test.py` | Pulse-manager in-vitro test (2026-06-15) — "see what comes out". | no plan found |
| `scripts/pursuits_judge_framing_lab.py` | PURSUITS.JUDGE_PENDING FRAMING LAB — 2026-08-23, part of the "remaining tests" batch. | no plan found |
| `scripts/reread_school_invitro.py` | In-vitro for Move 7 (reread-when-helpful) + Move 8 (school auto-extend / spiral). | no plan found |
| `scripts/resolve_blob.py` | Resolve an ollama model tag to its GGUF blob path (blobs ARE GGUFs — verified 2026-08-15). | ramses_second_tier |
| `scripts/restore_june13_memories.py` | Nascence — restore the delete-era memories from the June-13 snapshot (2026-08-15). | no plan found |
| `scripts/retrieval_retrospective.py` | Deliberative Retrieval — Phase 0 retrospective gate (2026-06-14). | no plan found |
| `scripts/routing_lab.py` | Nascence — ROUTING LAB (2026-08-16): test of chain-walk fix #1, the content_mode veto. | no plan found |
| `scripts/satisfaction_backfill.py` | Satisfaction cold-start backfill (2026-06-13). | no plan found |
| `scripts/school.py` | School — the teacher's console. | sleep_dream_redesign, social_world_school, music_learning |
| `scripts/self_implication_framing_lab.py` | SELF-IMPLICATION FRAMING LAB — 2026-08-23, testing the founder's generalization of the factory- station idea (see... | no plan found |
| `scripts/self_interrogation_counterfactual.py` | Nascence — SELF-INTERROGATION COUNTERFACTUAL HARNESS · docs/plans/self_interrogation.md · 2026-08-24 J-0164 (spawned from F-0071, self_interrogation.md's... | self_interrogation |
| `scripts/self_interrogation_framing_lab.py` | SELF_INTERROGATION GENUINENESS-JUDGE FRAMING LAB — 2026-08-23, tenth machine tested (second of the "remaining tests" batch). | no plan found |
| `scripts/self_surprise_test.py` | Self-Surprise / present-predictability — the exploration run (observe-only, 2026-06-15). | no plan found |
| `scripts/silence_gap_test.py` | Silence ↔ gap test (2026-06-14). | no plan found |
| `scripts/singlepass_lab.py` | Nascence — SINGLE-PASS LAB (2026-08-16): the Chinese-whispers test. | no plan found |
| `scripts/splitter_test.py` | Test the book splitter on every book on the shelf — verify sensible chapters + NO double-counts (the Commutation Chophouse bug). | no plan found |
| `scripts/station_bench.py` | Run the station suite across many models — the model x station matrix. | no plan found |
| `scripts/station_bench_needle.py` | Run the station suite through NEEDLE 2 — 45M params, CQ2-bit, CPU-only, ~14 MB binary. | no plan found |
| `scripts/station_bench_score.py` | Score the model x station matrix from saved raw output — nothing re-queried. | no plan found |
| `scripts/station_suite.py` | The STATION SUITE — eight task archetypes drawn from Du's real LLM call sites. | no plan found |
| `scripts/stick_test.py` | Nascence — THE STICK TEST (CLI): bundle-richness census. | cognitive_geometry, journal_consolidation_pyramid |
| `scripts/study_note_framing_lab.py` | STUDY_NOTE FRAMING LAB — 2026-08-23, seventh machine tested for the founder's generalized factory/ schema-first idea. | no plan found |
| `scripts/t4_battery.py` | the T4-revision ground-truth battery (the §12.1-Q3 validation gate). | no plan found |
| `scripts/t4_eval.py` | Nascence - T4 Self-Authoring Depth Eval ("deeper Du on the CPU") T4 self-authoring is the deepest, slowest, least latency-sensitive cognition - the... | no plan found |
| `scripts/tension_ledger_framing_lab.py` | TENSION LEDGER FRAMING LAB — 2026-08-23, third machine tested for the founder's generalized factory/schema-first idea (see... | no plan found |
| `scripts/test_audio_features.py` | Offline validation for core/audio_features.py (the ear's translator). | music_learning |
| `scripts/test_cat_ecological_laboratory.py` | Nascence — Headless Cat Ecological Laboratory (Task 4 Harness) Pure physical simulation testing for autonomous cat locomotion, 3D coordinates,... | no plan found |
| `scripts/test_dimension_stamps.py` | Test suite — TEMPERATURE + CAT LOCATION dimension stamps (2026-08-17). | no plan found |
| `scripts/test_object_graph.py` | Test suite for core/object_graph.py (Lane 2 object-graph), 2026-08-17. | no plan found |
| `scripts/test_world_p0.py` | P0 test suite — the world manifest + ghost registry (2026-08-17). | no plan found |
| `scripts/test_world_positions.py` | Position-authority test suite (2026-08-17, founder: "all the objects need places, and they need to be able to move of course"). | no plan found |
| `scripts/three_pass_test.py` | Three-pass test (2026-06-15). | no plan found |
| `scripts/train_lab.py` | Nascence — TRAIN LAB (2026-08-16): why trains dissolve, and whether train-hold + extend-carry lets them BUILD. | no plan found |
| `scripts/train_state_invitro.py` | In-vitro for the train working-state (lever 1, observe-first). | train_split_merge |
| `scripts/verify_curriculum.py` | Verify the 40-book grounding curriculum resolves in Du's local catalogue (read-only, no downloads). | no plan found |
| `scripts/verify_lanes.py` | Nascence — Lane Pre-Flight Verifier (gemma / phi / llama / mistral) Exercises the REAL wiring (core.schema SERVE_CHAINS + core.model_client routing +... | no plan found |
| `scripts/voice_lab.py` | Nascence — VOICE LAB (2026-08-16): offline A/B of the mouth prompt, v1 (pre-Nascence skeleton) vs v2 (the diegetic mouth). | no plan found |
| `scripts/voice_lab_rerun.py` | Re-run the voice lab (v1 vs v2 blind pairs) under the CURRENT hot-lane model. | no plan found |
| `scripts/watershed_retro_validate.py` | Watershed Retro-Validation (docs/plans/t4_watershed.md's own retro-validation law, run 2026-08-18). | no plan found |
| `scripts/widen_lab.py` | Nascence — WIDEN LAB (2026-08-16): the truncation fixes, tested. | no plan found |
| `scripts/world_grounding_audit.py` | Nascence — World Grounding & Variety Audit (2026-08-18). | no plan found |
| `scripts/world_laboratory.py` | Headless World Simulation Engine for deterministic testing. | no plan found |

---

## Summary

- core/: 147 files -- 111 with a strong (exact-filename-cited) owner, 14 with only a weak/inferred owner, 22 with no plan found.
- scripts/: 168 files -- 22 with a strong owner, 2 with only a weak/inferred owner, 144 with no plan found.
- scripts/ is overwhelmingly orphaned by this method (144/168 no plan found) -- expected, since
  one-off diagnostic/lab scripts are typically run and referenced in session handoffs or chat,
  not cited by filename inside a plan doc's own prose. J-0227 should treat scripts/ ownership
  as a session-handoff/memory-file grep problem, not a plan-doc grep problem, if it wants better
  coverage there -- out of scope for this mechanical prep job.