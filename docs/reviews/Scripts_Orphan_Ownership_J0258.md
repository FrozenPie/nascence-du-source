# J-0258 -- scripts/ orphan ownership via session-handoff/memory grep

Generated 2026-08-25 by job **J-0258** (source: finding:F-0266, spawned from J-0229's
prep table). J-0229's plan-doc grep found strong owners for only 22/168 `scripts/` files;
the 144 flagged `no plan found` were re-searched here against `docs/session_handoffs/*.md`,
`docs/session_*_summary.md`, ALL memory files under the Claude project memory directory
for this project (not just the `project_nascence_*.md` topic files -- the general founding
file `project_nascence.md` turned out to hold real hits for the earliest 2026-05-29/30
Build-0.2-era harness scripts, and it lives under the C--FreshStart project memory dir, NOT
C--Nascence as this job's own briefing assumed -- worth a correction note), and root-level
`docs/*.md` plus `docs/{reviews,reports,lab,completed,archive,node_audit,cross_model,
du_self_knowledge,chronicles}/*.md`. Matched on exact basename word-boundary, filename
with or without `.py`.

**Result: 99/144 (69%) got a real session/investigation owner** -- up from 0/144 under the
plan-doc method. 45 remain with no hit in any of these sources (see bottom section) --
genuine unowned-by-any-searched-source candidates, not proof they were never used (raw
chat transcripts were out of scope for this job).

---

| File | Role (from module docstring) | Owning session/investigation |
|---|---|---|
| `scripts/_clean_test_fragments.py` | Remove test fragments from the live DB. | founding memory project_nascence.md (pre-Nascence-name Build 0.2 era, 2026-05-29/30) |
| `scripts/_concurrency_test.py` | Prove GPU slot concurrency: 4 requests concurrent vs | founding memory project_nascence.md (pre-Nascence-name Build 0.2 era, 2026-05-29/30) |
| `scripts/_cost_probe.py` | Falsifiable test of the Cost theory, prediction 1 & 2, as a pure measurement: does embeddedness-cost score Carl's core commitments HIGH and Dennett's LOW?... | no context found |
| `scripts/_debate_report.py` | Post-debate report: did either mind revise, how did the arc go, did T4 even | no context found |
| `scripts/_diagnostic.py` | Diagnostic phase (no architecture change): can Carl REPRESENT a rival frame faithfully, NAME an irreducible conflict, and HOLD it unresolved? Distinguishes: A... | no context found |
| `scripts/_failover_test.py` | Prove GPU->CPU failover: call the hot chain and report which server | founding memory project_nascence.md (pre-Nascence-name Build 0.2 era, 2026-05-29/30) |
| `scripts/_fire_t4.py` | Fire T4 self-authoring for both debate agents on the contradiction pressure the 300-turn debate loaded. | no context found |
| `scripts/_first_thought.py` | One-shot: run a single thought cycle and dump every node's | docs/reviews: day_investigation_audit_2026-08-23.md; docs/reviews: day_timeline_2026-08-23.md; founding memory project_nascence.md (pre-Nascence-name Build 0.2 era, 2026-05-29/30) |
| `scripts/_graph_orch.py` | find the Orchestrator node id | no context found |
| `scripts/_memory_timeline.py` | Throwaway analysis: assemble a timeline of how Carl has changed from his memory. | no context found |
| `scripts/_peek_recent.py` | Read-only: dump the most recent stored cycle fragments (Q/A + scene + | no context found |
| `scripts/_reframe_analysis.py` | Reframing-rate analysis (retrospective, no new run): is Carl INERTIAL (rejects/holds, nothing penetrates) or ABSORPTIVE (translates every behaviorist attack... | no context found |
| `scripts/_revert_carl.py` | Revert Carl's spurious Chinese revision-3 (a language-drift artifact, not real evolution) back to his revision-2 English self_concept, preserved in... | no context found |
| `scripts/_smoketest.py` | (no docstring/comment found -- undocumented at the code level too) | founding memory project_nascence.md (pre-Nascence-name Build 0.2 era, 2026-05-29/30) |
| `scripts/_t4_fidelity_probe.py` | GPT's disambiguation: is the convergence Carl's pull, or T4's own synthesis bias? Run T4 on Dennett's ORIGINAL seed + accumulated debate memory under two... | no context found |
| `scripts/_test_autonoetic_timeline.py` | Offline test for C.3 Autonoetic Timeline (Subconscious T4 self-authoring). | memory: project_memory_systems_roadmap.md |
| `scripts/_test_critic_literal.py` | Verify culprit-#2 fix: the Critic should now APPROVE a literal answer when the human explicitly asked for one (the test-2 scenario that was rejected for... | no context found |
| `scripts/_test_critic_requests.py` | Verify the GENERAL Critic carve-out: when the human explicitly requests a mode (describe your state / argue one side / literal list), complying must be APPROVED. | no context found |
| `scripts/_test_emotional_pre_retrieval.py` | Offline test for C.2 Emotional Pre-Retrieval (the amygdala gate). | memory: project_memory_systems_roadmap.md |
| `scripts/_test_episodic_buffer.py` | Offline test for C.4 Episodic Buffer (scene assembly). | memory: project_memory_systems_roadmap.md |
| `scripts/_test_procedural_memory.py` | Offline test for C.6 Procedural Memory. | memory: project_memory_systems_roadmap.md |
| `scripts/_test_prospective_memory.py` | Offline test for C.1 Prospective Memory. | memory: project_memory_systems_roadmap.md |
| `scripts/_test_tension_ledger.py` | Step 1 verification — run the Tension Ledger against the live subconscious_state.json and show exactly what would be injected into identity. | no context found |
| `scripts/_test_tension_pressure.py` | Step 2 verification — pressure model + echo-guard relaxation, against live data. | no context found |
| `scripts/_test_thalamic_gate.py` | Offline test for C.5 Thalamic Gating (pre-Perception habituation reflex). | memory: project_memory_systems_roadmap.md |
| `scripts/_unseed_probe.py` | Unseeded control: same model (qwen2.5:7b on 11434), NEUTRAL system prompt, no Carl axiom, no Critic, no voice_example. | no context found |
| `scripts/_verify_budget.py` | syntax-check the harness + node | no context found |
| `scripts/_verify_genesis.py` | Verify the unseeded 'genesis' agent: minimal operational identity (no philosophy injected), process-only Critic, and a coherent first cycle from a blank | no context found |
| `scripts/ablation_lab.py` | Nascence — ABLATION LAB (2026-08-16): where does the sameness live? THREE LABS, ONE INVARIANT: mouth (v1/v2), routing (task/hybrid), architecture... | docs/lab: ablation_lab_2026-08-16.md |
| `scripts/activity_memory_backfill.py` | Activity Memory — retroactive backfill (2026-06-14). | no context found |
| `scripts/activity_memory_invitro.py` | Activity Memory — in-vitro gate (2026-06-14). | docs/completed: action_memory_plan.md; memory: project_nascence_activity_memory.md |
| `scripts/analyze_du_physical_sensations.py` | (no docstring/comment found -- undocumented at the code level too) | no context found |
| `scripts/axiom_read_invitro.py` | Phase 1 in-vitro proof (2026-06-15) — the READ design, no behaviour change. | docs/archive: systems_check_2026-06-22.md; memory: project_nascence_multilevel_axiom.md |
| `scripts/backfill_essays.py` | Backfill consolidating capstone essays for finished-but-un-essayed books (Phase 3, 2026-06-23). | no context found |
| `scripts/backtest_resolution_matcher.py` | (no docstring/comment found -- undocumented at the code level too) | docs/reports: claude_fresh_eyes_audit_aug14.md |
| `scripts/backup_memory.py` | Nascence — memory backup (2026-08-15, born from the lost-thoughts investigation). | docs/archive: awaiting_evidence_2026-08-15.md |
| `scripts/balance_test.py` | In-vitro test for the reading-remediation balance gate (2026-06-15). | session summary 2026-08-16; memory: project_nascence_balance_sprint.md |
| `scripts/book_selection_invitro.py` | In-vitro for the breadth engine (book_selection) + library_hand wiring. | memory: project_nascence_book_selection.md |
| `scripts/boredom_redirect_test.py` | In-vitro test for the BOREDOM-REDIRECT (#2, 2026-06-15). | memory: project_nascence_modulation_field.md |
| `scripts/brick1_voice_contract_invitro.py` | Brick 1 in-vitro: the render_character_voice MOUTH contract (Character-as-Integration §6). | memory: project_nascence_character_integration.md |
| `scripts/brick3_identity_vault_invitro.py` | Brick 3 in-vitro: the identity_vault goalkeeper. | memory: project_nascence_character_integration.md |
| `scripts/build_critic_groundtruth.py` | Build the decomposed-critic GROUND TRUTH from Claude's independent hand-labelling of the 68 clean historical rejections (read from data/critic_label_set.json). | memory: project_nascence_critic_contradiction.md |
| `scripts/chapter_burst_test.py` | Chapter-scoped, novelty-gated reading burst + the two-lesson school flow (2026-06-15). | memory: project_nascence_modulation_field.md |
| `scripts/check_du.py` | (no docstring/comment found -- undocumented at the code level too) | no context found |
| `scripts/cold_store_qwen.py` | Cold-store control on the idle mouth (qwen3.5:9b) — 2026-08-21, founder ask. | docs/lab: cold_store_qwen_2026-08-21.md |
| `scripts/commitment_defeater_framing_lab.py` | COMMITMENT_LEDGER JUDGE_DEFEATER FRAMING LAB — 2026-08-23, sixth machine tested for the founder's generalized factory/schema-first idea. | docs/reviews: day_timeline_2026-08-23.md; docs/lab: commitment_defeater_framing_2026-08-23.md; memory: project_nascence_factory_stations.md |
| `scripts/concerns_test.py` | In-vitro test for G1 current concerns (2026-06-15). | memory: project_nascence_goals.md |
| `scripts/contradiction_phase0_invitro.py` | In-vitro for Phase 0 pure-logic: the contradiction gate, the L1 prediction-error feed, and the L2 meta-awareness classification. | docs/completed: contradiction_rearchitecture_plan.md |
| `scripts/critic_grade.py` | Nascence — Decomposed critic: the DECOUPLED precision grade (contradiction_rearchitecture_plan.md L0 gate). | docs/root: ROADMAP.md; docs/completed: contradiction_rearchitecture_plan.md; docs/completed: evidence_review_dashboard.md |
| `scripts/curiosity_phase0_invitro.py` | In-vitro for the curiosity flesh-out Phase 0: strict-partition queue, the de-personalization prism's deterministic world-facing firewall, the shadow-transform... | docs/archive: curiosity_flesh_out_plan.md; memory: project_nascence_curiosity_organ.md |
| `scripts/curiosity_twig_test.py` | In-vitro test for the curiosity-node TWIG expansion (2026-06-15). | memory: project_nascence_curiosity_observatory.md |
| `scripts/cutover_axiom.py` | The axiom cutover (2026-06-15) — promote the live axiom.json to the multilevel schema. | memory: project_nascence_multilevel_axiom.md |
| `scripts/cutover_verify.py` | Cutover verification (2026-06-15) — proves the multilevel read+T4 change-set on real data, WITHOUT importing the heavy app and WITHOUT touching live files. | memory: project_nascence_multilevel_axiom.md |
| `scripts/decomposed_critic_invitro.py` | Phase 0 acceptance gate for the decomposed critic (Layer 0), scored against the GROUND TRUTH (data/critic_groundtruth.jsonl — Claude's hand-labelling of the 68... | docs/completed: contradiction_rearchitecture_plan.md; docs/node_audit: critic_node.md; memory: project_nascence_critic_contradiction.md |
| `scripts/deliberation_ground_framing_lab.py` | DELIBERATION.GROUND_THOUGHT FRAMING LAB — 2026-08-23, part of the "remaining tests" batch (after openness gate, self_implication,... | docs/reviews: day_timeline_2026-08-23.md; docs/lab: deliberation_ground_framing_2026-08-23.md; memory: project_nascence_factory_stations.md |
| `scripts/deliberation_invitro.py` | In-vitro proof of the deliberative pulse (2026-06-15) — the "make me show it" gate. | docs/completed: lane_architecture_FULL.md; memory: project_nascence_lane_architecture.md |
| `scripts/dream_arc_test.py` | In-vitro: the multi-scene progressive dream (2026-06-15). | memory: project_nascence_dreams.md |
| `scripts/dream_grounding_test.py` | In-vitro test for DREAM GROUNDING (2026-06-15). | memory: project_nascence_dreams.md |
| `scripts/dream_thread_test.py` | In-vitro test for CROSS-NIGHT dream threading (2026-06-15). | memory: project_nascence_dreams.md |
| `scripts/dreamer_eval.py` | Nascence — Dreamer (Subconscious) Divergence Eval The subconscious / dream lane wants the OPPOSITE of the hot-lane precision battery: associative reach,... | no context found |
| `scripts/du_composer.py` | Du — Composer A small standalone window for typing multi-line messages to Du without the REPL's press-Enter-submits-immediately behaviour. | docs/root: AWAITING_EVIDENCE.md; docs/reviews: day_investigation_audit_2026-08-23.md; docs/reviews: day_timeline_2026-08-23.md |
| `scripts/emissary_axiom_test.py` | In-vitro test for the Emissary axiom (brick 1 of the bicameral truth-self, 2026-06-15). | memory: project_nascence_emissary_axiom.md |
| `scripts/evidence_recall_framing_lab.py` | EVIDENCE_RECALL FRAMING LAB — 2026-08-23, part of the "remaining tests" batch, and the last of the judge_panel-consumer machines named in judge_panel.py's own... | docs/reviews: day_timeline_2026-08-23.md; docs/lab: evidence_recall_framing_2026-08-23.md; memory: project_nascence_factory_stations.md |
| `scripts/exogenous_field_test.py` | Try it: the world + his machine-body pulling on the modulation field (2026-06-15). | memory: project_nascence_modulation_field.md |
| `scripts/exploratory_ignition_test.py` | In-vitro test for EXPLORATORY curiosity ignition (2026-06-15, backlog-driven fix). | memory: project_nascence_curiosity_observatory.md |
| `scripts/factory_station_lab.py` | FACTORY STATION LAB — 2026-08-23, testing the founder/GPT idea (see memory: project_nascence_factory_stations.md) on the ONE station identified as the... | docs/reviews: day_timeline_2026-08-23.md; docs/lab: factory_station_2026-08-23.md; memory: project_nascence_factory_stations.md |
| `scripts/frontier_loop_test.py` | In-vitro test for the FRONTIER CLOSING LOOP (2026-06-15). | memory: project_nascence_curiosity_observatory.md |
| `scripts/grade_work_framing_lab.py` | LEFT_LANE.GRADE_WORK FRAMING LAB — 2026-08-23, ninth machine tested (first of the "remaining tests" batch requested after the peers re-run). | docs/reviews: day_timeline_2026-08-23.md; docs/lab: grade_work_framing_2026-08-23.md; memory: project_nascence_factory_stations.md |
| `scripts/graphify_enrich.py` | recover the edges graphify's tree-sitter AST misses on THIS project (2026-07-04, extended 2026-08-18 for self-call resolution). | docs/root: ROADMAP.md; docs/root: graphify_notes.md |
| `scripts/graphify_force_html.py` | regenerate graph.html as the aggregated community view when `graphify cluster-only` silently skips it (found 2026-08-18). | docs/root: graphify_notes.md |
| `scripts/graphify_health_check.py` | Nascence — graphify Code-Health Check (2026-08-18). | docs/root: graphify_notes.md |
| `scripts/import_epub.py` | Import a local .epub into Du's library as a clean .txt (the format core/reading.py reads from data/books/). | docs/completed: study_notes_plan.md |
| `scripts/inspect_crab_shadow.py` | (no docstring/comment found -- undocumented at the code level too) | no context found |
| `scripts/inspect_overnight_du.py` | Focus on last 12-14 hours (overnight from ~20:00 last night to 08:19 today) | no context found |
| `scripts/journal_rollup_framing_lab.py` | JOURNAL_ROLLUP FRAMING LAB — 2026-08-23, eighth machine tested for the founder's generalized factory/schema-first idea. | docs/reviews: day_timeline_2026-08-23.md; docs/lab: journal_rollup_framing_2026-08-23.md; memory: project_nascence_factory_stations.md |
| `scripts/judge16.py` | The expanded judge case bank — 16 balanced cases, the pre-registered gate on the judge-panel finding. | session summary 2026-08-20; docs/root: AWAITING_EVIDENCE.md; docs/reviews: day_investigation_audit_2026-08-23.md |
| `scripts/lane1_baseline.py` | Nascence — LANE 1 SELF-CORRECTION BASELINE · docs/plans/lane2_the_witness.md §5 · 2026-08-20 The pre-Lane-2 counterfactual. | docs/root: AWAITING_EVIDENCE.md; docs/lab: lane1_baseline_report.md |
| `scripts/lane2_context_score.py` | Score the Lane 2 context lab from its saved raw data and write the report — nothing re-queried. | no context found |
| `scripts/lane2_lab_items.py` | Lane 2 Lab — follow-up: the FULL item population scan (founder-directed, 2026-08-17). | docs/lab: lane2_lab_report.md |
| `scripts/lane2_model_rescore.py` | Re-score the Lane 2 model lab from its SAVED raw data and regenerate the report — no models re-queried. | no context found |
| `scripts/lane2_recheck.py` | Lane 2 Recheck — founder-check re-run of K1/K3 against the CURRENT object-graph (2026-08-18). | docs/root: UNFINISHED_PLANS_SURVEY_2026-08-18.md; docs/lab: lane2_recheck_report.md |
| `scripts/lane_forces.py` | Lane forces — measuring the 3 lanes as pulls on the dimensional distribution (2026-06-15). | memory: project_nascence_balance_sprint.md; memory: project_nascence_emissary_axiom.md |
| `scripts/lane_hypothesis_test.py` | Lane Hypothesis Test (2026-06-14) — does the PROMPT select a stable, distinct cognitive style? The claim behind the whole lane architecture: the same substrate... | no context found |
| `scripts/lane_hypothesis_test2.py` | Lane Hypothesis Test v2 (topic-controlled, 2026-06-14). | docs/completed: lane_architecture_FULL.md; docs/completed: two_lane_architecture_plan.md |
| `scripts/launch_cpu_hubs.py` | Launch CPU Tier Hubs in LAZY mode (load on first request, auto-unload when | session summary 2026-08-24 |
| `scripts/lean_probe.py` | THE LEAN PROBE — do the stations (LLMs) carry their own stance toward the cold? (2026-08-21, founder) Founder: "The LLMs are going to have a lean on what word comes next. | docs/lab: lean_probe_2026-08-21.md |
| `scripts/librarian_framing_lab.py` | LIBRARIAN FRAMING LAB — 2026-08-23, fourth machine tested for the founder's generalized factory/ schema-first idea (see... | docs/reviews: day_timeline_2026-08-23.md; docs/lab: librarian_framing_2026-08-23.md; docs/lab: librarian_p0_headtohead_2026-08-24.md |
| `scripts/liveness_audit.py` | Nascence — Pipeline Liveness Audit (2026-07-03). | session handoff 2026-08-24: system-overview-indexing; session handoff 2026-08-24: geometry-tuple-index-multidim; docs/root: System_Overview.md |
| `scripts/llm_station_census.py` | Census of every LLM call site in Du — the STATIONS, not the lines. | docs/root: transit_timetable.md; docs/lab: llm_station_map.md |
| `scripts/llm_timetable.py` | The TIMETABLE — what opens each LLM station, and how often. | docs/root: transit_timetable.md; docs/lab: llm_timetable.md |
| `scripts/load_curriculum.py` | Load the 40-book grounding curriculum into school. | memory: project_nascence_modulation_field.md |
| `scripts/load_curriculum_v2.py` | Load curriculum v2 — the rebalanced 40-book grounding curriculum (2026-08-19). | session summary 2026-08-19 |
| `scripts/memory_levels_batch.py` | One-off BATCH shadow-distill over recent CLEAN level-0 raw — generates the Memory-Levels Phase-1 evidence battery in one pass instead of waiting days for sleep-paced accrual. | memory: project_nascence_memory_levels.md |
| `scripts/migrate_axiom_multilevel.py` | Phase 0 of the multilevel-axiom migration (2026-06-15) — DRAFT generator, no behaviour change. | memory: project_nascence_multilevel_axiom.md |
| `scripts/migrate_embedder.py` | Embedder migration: all-MiniLM-L6-v2 -> paraphrase-multilingual-MiniLM-L12-v2 (2026-06-13). | memory: project_nascence_first_crossover.md |
| `scripts/model_registry_probe.py` | Probe the ollama registry for candidate model families — what ACTUALLY exists, and how big. | no context found |
| `scripts/modulation_field_test.py` | Modulation-field test (2026-06-15) — observe-only. | docs/completed: modulation_field_plan.md; memory: project_nascence_modulation_field.md |
| `scripts/mood_felt_tag_test.py` | In-vitro test for emotion_vec items 1+2 (2026-06-15): the live mood-vec + felt-tag storage. | memory: project_nascence_contradiction_drainage.md |
| `scripts/narrative_retrospective.py` | Narrative Quality — retrospective run (Phase 0 validation, 2026-06-13). | docs/completed: narrative_quality_plan.md; memory: project_nascence_narrative_witness.md |
| `scripts/node_benchmark_local.py` | Local-side companion to `node_benchmark.py` — the comparison point that makes the Ramses numbers mean something. | docs/lab: node_benchmark.md |
| `scripts/node_benchmark_report.py` | Render the node benchmark into a report — from saved raw JSON, nothing re-queried. | docs/lab: node_benchmark.md |
| `scripts/peers_contrary_framing_lab.py` | PEERS CONTRARY_TARGET FRAMING LAB — 2026-08-23, fifth machine tested for the founder's generalized factory/schema-first idea. | docs/reviews: day_timeline_2026-08-23.md; docs/lab: peers_contrary_framing_2026-08-23.md; memory: project_nascence_factory_stations.md |
| `scripts/person_costume_lab.py` | Nascence — PERSON vs COSTUME LAB (2026-08-16): the founder's hypothesis. | docs/root: chain_walk_findings.md |
| `scripts/phase1_ignition_invitro.py` | Phase 1 in-vitro: the L1 prediction-error feed now WRITES a contradiction shadow event when the gate says would_pressure. | docs/completed: contradiction_rearchitecture_plan.md; memory: project_nascence_critic_contradiction.md |
| `scripts/phaseA_report.py` | Loop Metabolism — Phase A report (2026-06-14). | memory: project_nascence_loop_monoculture.md |
| `scripts/phaseB_invitro.py` | Loop Metabolism — Phase B in-vitro proofs (2026-06-14). | docs/completed: loop_metabolism_plan.md; memory: project_nascence_loop_monoculture.md |
| `scripts/phaseB_recompute_ai_importance.py` | Phase B follow-up — recompute existing active_imagination importance (2026-06-14). | memory: project_nascence_loop_monoculture.md |
| `scripts/prompt_budget_census.py` | Census of how the inner-monologue prompt is currently shaped — read-only, writes nothing. | no context found |
| `scripts/pulse_manager_test.py` | Pulse-manager in-vitro test (2026-06-15) — "see what comes out". | memory: project_nascence_modulation_field.md |
| `scripts/pursuits_judge_framing_lab.py` | PURSUITS.JUDGE_PENDING FRAMING LAB — 2026-08-23, part of the "remaining tests" batch. | docs/reviews: day_timeline_2026-08-23.md; docs/lab: pursuits_judge_framing_2026-08-23.md; memory: project_nascence_factory_stations.md |
| `scripts/reread_school_invitro.py` | In-vitro for Move 7 (reread-when-helpful) + Move 8 (school auto-extend / spiral). | memory: project_nascence_book_selection.md |
| `scripts/restore_june13_memories.py` | Nascence — restore the delete-era memories from the June-13 snapshot (2026-08-15). | docs/root: REORGANIZATION_2026-08-18.md; docs/archive: awaiting_evidence_2026-08-15.md |
| `scripts/retrieval_retrospective.py` | Deliberative Retrieval — Phase 0 retrospective gate (2026-06-14). | docs/completed: action_memory_plan.md |
| `scripts/routing_lab.py` | Nascence — ROUTING LAB (2026-08-16): test of chain-walk fix #1, the content_mode veto. | docs/lab: routing_lab_2026-08-16.md; docs/lab: routing_lab_v2_2026-08-16.md |
| `scripts/satisfaction_backfill.py` | Satisfaction cold-start backfill (2026-06-13). | docs/completed: affiliation_system_plan.md; memory: project_nascence_satisfaction.md |
| `scripts/self_implication_framing_lab.py` | SELF-IMPLICATION FRAMING LAB — 2026-08-23, testing the founder's generalization of the factory- station idea (see... | docs/reviews: day_timeline_2026-08-23.md; docs/lab: self_implication_framing_2026-08-23.md; memory: project_nascence_factory_stations.md |
| `scripts/self_interrogation_framing_lab.py` | SELF_INTERROGATION GENUINENESS-JUDGE FRAMING LAB — 2026-08-23, tenth machine tested (second of the "remaining tests" batch). | docs/reviews: day_timeline_2026-08-23.md; docs/lab: self_interrogation_framing_2026-08-23.md; memory: project_nascence_factory_stations.md |
| `scripts/self_surprise_test.py` | Self-Surprise / present-predictability — the exploration run (observe-only, 2026-06-15). | memory: project_nascence_modulation_field.md |
| `scripts/silence_gap_test.py` | Silence ↔ gap test (2026-06-14). | docs/completed: lane_architecture_FULL.md |
| `scripts/singlepass_lab.py` | Nascence — SINGLE-PASS LAB (2026-08-16): the Chinese-whispers test. | docs/lab: singlepass_lab_2026-08-16.md |
| `scripts/splitter_test.py` | Test the book splitter on every book on the shelf — verify sensible chapters + NO double-counts (the Commutation Chophouse bug). | memory: project_nascence_modulation_field.md |
| `scripts/station_bench.py` | Run the station suite across many models — the model x station matrix. | docs/root: AWAITING_EVIDENCE.md; docs/reviews: day_investigation_audit_2026-08-23.md; docs/reviews: day_timeline_2026-08-23.md |
| `scripts/station_bench_needle.py` | Run the station suite through NEEDLE 2 — 45M params, CQ2-bit, CPU-only, ~14 MB binary. | no context found |
| `scripts/station_bench_score.py` | Score the model x station matrix from saved raw output — nothing re-queried. | docs/lab: station_matrix.md |
| `scripts/station_suite.py` | The STATION SUITE — eight task archetypes drawn from Du's real LLM call sites. | docs/lab: station_matrix.md |
| `scripts/study_note_framing_lab.py` | STUDY_NOTE FRAMING LAB — 2026-08-23, seventh machine tested for the founder's generalized factory/ schema-first idea. | docs/reviews: day_timeline_2026-08-23.md; docs/lab: study_note_framing_2026-08-23.md; memory: project_nascence_factory_stations.md |
| `scripts/t4_battery.py` | the T4-revision ground-truth battery (the §12.1-Q3 validation gate). | memory: project_nascence_t4_redesign.md |
| `scripts/t4_eval.py` | Nascence - T4 Self-Authoring Depth Eval ("deeper Du on the CPU") T4 self-authoring is the deepest, slowest, least latency-sensitive cognition - the... | no context found |
| `scripts/tension_ledger_framing_lab.py` | TENSION LEDGER FRAMING LAB — 2026-08-23, third machine tested for the founder's generalized factory/schema-first idea (see... | docs/reviews: day_timeline_2026-08-23.md; docs/lab: tension_ledger_framing_2026-08-23.md; memory: project_nascence_factory_stations.md |
| `scripts/test_cat_ecological_laboratory.py` | Nascence — Headless Cat Ecological Laboratory (Task 4 Harness) Pure physical simulation testing for autonomous cat locomotion, 3D coordinates,... | session summary 2026-08-19; docs/reviews: audit_2026-08-20.md; docs/reports: claude_fresh_eyes_audit_aug14.md |
| `scripts/test_dimension_stamps.py` | Test suite — TEMPERATURE + CAT LOCATION dimension stamps (2026-08-17). | no context found |
| `scripts/test_object_graph.py` | Test suite for core/object_graph.py (Lane 2 object-graph), 2026-08-17. | no context found |
| `scripts/test_world_p0.py` | P0 test suite — the world manifest + ghost registry (2026-08-17). | docs/completed: world_factories_P0.md |
| `scripts/test_world_positions.py` | Position-authority test suite (2026-08-17, founder: "all the objects need places, and they need to be able to move of course"). | no context found |
| `scripts/three_pass_test.py` | Three-pass test (2026-06-15). | docs/completed: lane_architecture_FULL.md; docs/completed: two_lane_architecture_plan.md |
| `scripts/train_lab.py` | Nascence — TRAIN LAB (2026-08-16): why trains dissolve, and whether train-hold + extend-carry lets them BUILD. | docs/lab: train_lab_2026-08-16.md |
| `scripts/verify_curriculum.py` | Verify the 40-book grounding curriculum resolves in Du's local catalogue (read-only, no downloads). | no context found |
| `scripts/verify_lanes.py` | Nascence — Lane Pre-Flight Verifier (gemma / phi / llama / mistral) Exercises the REAL wiring (core.schema SERVE_CHAINS + core.model_client routing +... | memory: nascence_du_hardware.md |
| `scripts/voice_lab.py` | Nascence — VOICE LAB (2026-08-16): offline A/B of the mouth prompt, v1 (pre-Nascence skeleton) vs v2 (the diegetic mouth). | docs/root: AWAITING_EVIDENCE.md |
| `scripts/voice_lab_rerun.py` | Re-run the voice lab (v1 vs v2 blind pairs) under the CURRENT hot-lane model. | docs/lab: voice_lab_2026-08-21_qwen.md |
| `scripts/watershed_retro_validate.py` | Watershed Retro-Validation (docs/plans/t4_watershed.md's own retro-validation law, run 2026-08-18). | docs/lab: watershed_retro_validation_report.md |
| `scripts/widen_lab.py` | Nascence — WIDEN LAB (2026-08-16): the truncation fixes, tested. | session summary 2026-08-16 |
| `scripts/world_grounding_audit.py` | Nascence — World Grounding & Variety Audit (2026-08-18). | docs/root: graphify_notes.md |
| `scripts/world_laboratory.py` | Headless World Simulation Engine for deterministic testing. | docs/root: UNFINISHED_PLANS_SURVEY_2026-08-18.md; docs/reports: claude_fresh_eyes_audit_aug14.md; docs/completed: INDEX.md |

---

## Still no context found (35/144)

Not matched in any session-handoff, memory file, or the broadened docs/ sweep above.
Real orphan candidates for J-0227's prose, or need a source outside what this job searched.

- `scripts/_cost_probe.py`
- `scripts/_debate_report.py`
- `scripts/_diagnostic.py`
- `scripts/_fire_t4.py`
- `scripts/_graph_orch.py`
- `scripts/_memory_timeline.py`
- `scripts/_peek_recent.py`
- `scripts/_reframe_analysis.py`
- `scripts/_revert_carl.py`
- `scripts/_t4_fidelity_probe.py`
- `scripts/_test_critic_literal.py`
- `scripts/_test_critic_requests.py`
- `scripts/_test_tension_ledger.py`
- `scripts/_test_tension_pressure.py`
- `scripts/_unseed_probe.py`
- `scripts/_verify_budget.py`
- `scripts/_verify_genesis.py`
- `scripts/activity_memory_backfill.py`
- `scripts/analyze_du_physical_sensations.py`
- `scripts/backfill_essays.py`
- `scripts/check_du.py`
- `scripts/dreamer_eval.py`
- `scripts/inspect_crab_shadow.py`
- `scripts/inspect_overnight_du.py`
- `scripts/lane2_context_score.py`
- `scripts/lane2_model_rescore.py`
- `scripts/lane_hypothesis_test.py`
- `scripts/model_registry_probe.py`
- `scripts/prompt_budget_census.py`
- `scripts/station_bench_needle.py`
- `scripts/t4_eval.py`
- `scripts/test_dimension_stamps.py`
- `scripts/test_object_graph.py`
- `scripts/test_world_positions.py`
- `scripts/verify_curriculum.py`