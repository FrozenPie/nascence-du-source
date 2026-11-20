# plan-maintain run — 2026-11-19 22:54 UTC

## 0. Lint conventions
```
{
  "no_status_line": [],
  "no_current_state_section": [
    "shore_creatures",
    "wood_creatures",
    "closure_producer",
    "common_ground",
    "follow_line_stricter_settle",
    "letters_to_travis",
    "memory_review_adoption",
    "nature_observation_outside_the_study_design_J-3483",
    "p0042_system_rewrite_draft_J-3488",
    "prompt_manager",
    "recall_confidence_graded_loss",
    "stand_kinds_and_accumulation",
    "t5_conversational_world_grading_design",
    "teaching_to_synthesis_study",
    "web_hand",
    "world_shelf_gap"
  ],
  "roadmap_orphan_links": [],
  "decisions_bad_plan_slug": [],
  "memory_underscore_names": [
    "feedback_decoupled_judge.md",
    "feedback_my_failure_modes.md",
    "project_buddha_aif_ast.md",
    "project_buddha_predictive_processing.md",
    "project_cognitive_frameworks_roadmap.md",
    "project_nascence_active_imagination.md",
    "project_nascence_affect_drives_item_d_satisfaction_normalisation.md",
    "project_nascence_attention_allocation.md",
    "project_nascence_attention_economy.md",
    "project_nascence_balance_sprint.md",
    "project_nascence_cognitive_ledger.md",
    "project_nascence_curator_lane.md",
    "project_nascence_curiosity_observatory.md",
    "project_nascence_decoupled_judge_pattern.md",
    "project_nascence_dream_c_and_library.md",
    "project_nascence_emissary_axiom.md",
    "project_nascence_epistemic_source.md",
    "project_nascence_error_pathway.md",
    "project_nascence_field_scan.md",
    "project_nascence_goals.md",
    "project_nascence_j2064_wake_on_message.md",
    "project_nascence_left_lane.md",
    "project_nascence_math_lessons.md",
    "project_nascence_memory_as_a_service.md",
    "project_nascence_memory_levels.md",
    "project_nascence_multilens_notes.md",
    "project_nascence_october_restart_batch_2026_10_28.md",
    "project_nascence_place_upgrades.md",
    "project_nascence_procedural_leak.md",
    "project_nascence_prompt_manager_p0_provenance_coverage.md",
    "project_nascence_question_cargo.md",
    "project_nascence_qwen3_swap.md",
    "project_nascence_reading_provenance.md",
    "project_nascence_reality_instruments.md",
    "project_nascence_self_efficacy_court.md",
    "project_nascence_session_handoff_20261014_232328_j2064-wake-on-message-j2065-night-mind-beside-wave3.md",
    "project_nascence_session_handoff_20261015_010059_wave3-parallel-builds-five-rulings-final.md",
    "project_nascence_session_handoff_20261114_084145_jobrun-du-up-waves-1-4-decide-review.md",
    "project_nascence_session_handoff_20261114_172437_jobrun-overnight-waves-1-4.md",
    "project_nascence_session_handoff_20261115_185735_du-unanswered-questions-web-hand.md",
    "project_nascence_session_handoff_20261117_212430_needs-input-reads-labelling-feasibility.md",
    "project_nascence_session_handoff_20261118_011416_plan-audit-jobruns-founder-questions.md",
    "project_nascence_sleep_as_a_mode.md",
    "project_nascence_symbol_evolution.md",
    "project_nascence_t2_consolidation.md",
    "project_nascence_t4_deliberation.md",
    "project_nascence_t4_redesign.md",
    "project_nascence_theme_recurrence.md",
    "project_nascence_transport_manager.md",
    "project_nascence_web_hand_in_world_routes.md",
    "project_nascence_world_loop.md",
    "project_nascence_world_shelf_gap_sources_2026-11-18.md",
    "project_social_targeting.md",
    "project_spirit_theory_of_mind.md",
    "project_x4_mod_porting.md"
  ],
  "unharvested_review_docs": [
    "File_Manifest_Groupings_J0229.md",
    "J-3140_symbolic_reading_repurposing.md",
    "J-3141_self_relate_repurposing.md",
    "J-3142_narrative_quality_coder_repurposing.md",
    "J-3144_habituation_seed_line_repurposing_review.md",
    "J-3171_reflection_unread_fields_review.md",
    "J-3210_lane2_held_hand_label.md",
    "J-3240_entity_name_and_model_knowledge_tag_review.md",
    "J-3248_chaptered_memory_recall_review.md",
    "J-3262_boredom_area_review.md",
    "J-3290_stale_patch_cue_shadow_read.md",
    "J-3309_blind_sheet.md",
    "J-3309_key_blend_replay.md",
    "J-3312_draft_keyed_second_recall_replay.md",
    "J-3313_expressed_valence_lab.md",
    "J-3316_arc_entry_trace_read.md",
    "J-3321_chapter_magnet_review.md",
    "J-3343_chapter_telling_audit.md",
    "Scripts_Orphan_Ownership_J0258.md",
    "actions_system_2026-08-22.md",
    "affect_chain_2026-11-14.md",
    "arc_entry_review_J-3215.md",
    "audit_2026-08-20.md",
    "axiom_deep_dive_2026-10-30.md",
    "backlog_triage_2026-11-16.md",
    "build_marathon_brief_2026-11-05.md",
    "butlin_long_mapping_2026-11-19.md",
    "chain_walk_findings.md",
    "consciousness_theories_vs_du_2026-10-31.md",
    "crosslink_audit_2026-08-22.md",
    "curator_repurposing_review_J-3143.md",
    "curiosity_end_to_end_J-3988_2026-11-14.md",
    "d0509_defeater_baseline_2026-10-31.md",
    "day_investigation_audit_2026-08-23.md",
    "day_timeline_2026-08-16.md",
    "day_timeline_2026-08-17.md",
    "day_timeline_2026-08-18.md",
    "day_timeline_2026-08-19.md",
    "day_timeline_2026-08-20.md",
    "day_timeline_2026-08-21.md",
    "day_timeline_2026-08-23.md",
    "dream_overhaul_founder_design_2026-09-15.md",
    "du_24h_2026-08-21.md",
    "du_actions_inventory_2026-09-27.md",
    "du_clinical_read_2026-11-16.md",
    "du_dreams_evolution_2026-08-21.md",
    "du_humanity_check_2026-11-16.md",
    "du_prompt_inventory_2026-10-31.md",
    "du_prompt_inventory_appendix_a_rejoined_2026-11-07.md",
    "du_telemetry_claims_triage_2026-08-27.md",
    "du_vs_human_2026-10-15.md",
    "factory_census.md",
    "findings_wipe_2026-10-31.md",
    "founder_needs_input_2026-11-18.md",
    "founder_triage_2026-11-02.md",
    "frontier_disciplines_2026-10-30.md",
    "frontier_semantic_merge_replay_2026-10-19.md",
    "gemini_pointers_vs_du_2026-10-18.md",
    "ghost_memory_index_chord_echo_J-3247.md",
    "goal_distributions_2026-11-14.md",
    "goal_system_research_comparison_2026-11-14.md",
    "god_function_bug_count_2026-11-20.md",
    "human_thinking_vs_du_channels_2026-10-17.md",
    "humanity_scorecard.md",
    "hygiene_dead_function_triage_2026-11-07.md",
    "identity_adapter_step0_2026-10-18.md",
    "index_coverage.md",
    "index_skills_audit_2026-08-23.md",
    "job_backlog_breakdown_2026-11-06.md",
    "jobrun_2026-10-17.md",
    "jung_naming_audit_2026-10-30.md",
    "lane2_the_witness_review_brief_2026-09.md",
    "ledger_id_citation_audit.md",
    "ledger_replay_plan_20261117.md",
    "letters_to_travis_2026-10-16.md",
    "literal_will_real_exemplar_candidates.md",
    "memory_router_keys_shadow_design_J-3163.md",
    "nascence_writeup_for_gpt_2026-11-16.md",
    "near_duplicate_text_tests_J-3308.md",
    "needs_input_reads_2026-11-18.md",
    "observables_gap_2026-09-03.md",
    "observe_inventory_2026-09-02.md",
    "outside_knowledge_review_J-3243_2026-11-05.md",
    "p0042_rewrite_candidates.md",
    "plan_files_evidence_audit.md",
    "plan_folder_checkup_2026-11-18.md",
    "plan_index_2026-08-23.md",
    "plan_liveness_audit.md",
    "plan_maintain_run.md",
    "plan_progress_audit_2026-11-18.md",
    "plan_schema_audit.md",
    "plan_shadow_read.md",
    "prompt_flow_audit.md",
    "prompt_manager_audit_round1_2026-11-14.md",
    "prompt_manager_research_2026-11-14.md",
    "ramses_stall_plan_2026-11-03.md",
    "recall_temporal_terms_2026-09-28.md",
    "recall_used_label_calibration_J-3311.md",
    "sleep_dream_2026-08-22.md",
    "soft_live_hard_shadow_pattern_2026-08-23.md",
    "ssd_usage_2026-10-18.md",
    "stands_retire_in_minutes_2026-11-18.md",
    "stash0_audit_2026-09-04.md",
    "strings_sheets_by_ear_2026-10-19.md",
    "strings_sheets_repick_candidates.md",
    "sumner_sky_tide_weather_design_J-3264.md",
    "system_overview_antigravity_review_2026-10-18.md",
    "t4_estate_node_design_J-3835.md",
    "t4_tension_lifecycle_J-3302.md",
    "t4_whole_picture_review_J-3252.md",
    "t5_conversational_compile_J-3179.md",
    "t5_procedural_skills_2026-08-22.md",
    "take_integration_baseline_J-3323.md",
    "thought_channels_plan_coverage_2026-10-17.md",
    "transport_reader_design_2026-11-18.md",
    "triple_lens_review_2026-07-02.md",
    "tuple_substrate_reply_to_gpt_2026-10-30.md",
    "udms_mcp_wishlist_2026-11-19.md",
    "vitality_scale_replay_J3967.md",
    "wave_b_merge_plan_2026-11-05.md"
  ]
}
```


## 7b. plan_state.py lint --all
123 plans linted · 30 with problems · 0 regrowing · 14 over the 40,000-byte cap · 8 without a state block


## 7c. garden netting event gate
[garden-netting-gate] no event: {"ts": 1795129306.9, "event": null, "fired_before": false, "filed": null, "dry_run": false}


## 7d. prompt registry check
```
prompt-registry check: 141 prompt sites in code · 132 live registry rows (4 fragment rows) · idle seed parts 46 · code root C:\Nascence (via cwd)
  CALLERS P-0040 is SHADOW but none of its keys has a resolved caller (Stability loop: re-ask a knowledge question K times). Read the code (callback table / getattr / instance method are invisible); then prompt_registry.py set P-0040 --status DEAD|DORMANT --note "..."   [warning only]
  CALLERS P-0067 is LIVE but none of its keys has a resolved caller (Symbol evolution: chronicle how a symbol's meaning drifted). Read the code (callback table / getattr / instance method are invisible); then prompt_registry.py set P-0067 --status DEAD|DORMANT --note "..."   [warning only]
  CALLERS P-0119 is SHADOW but none of its keys has a resolved caller (Symbol window metric: cross-family judge of whether a logged symbol sentence is specific to its symbol (offline, scripts/symbol_window_report.py --judge)). Read the code (callback table / getattr / instance method are invisible); then prompt_registry.py set P-0119 --status DEAD|DORMANT --note "..."   [warning only]
  CALLERS P-0021 is DEAD but has a caller: core/curator.py:118 (shadow_voice, same-module). Re-check the status.   [warning only]
  CALLERS P-0097 is DEAD but has a caller: core/deliberative_judge.py:127 (literalize, same-module). Re-check the status.   [warning only]
  OK: every prompt site in the code is registered, and every registered key still exists.
```


## 7e. function size ratchet
```
ok       core/orchestrator.py::Orchestrator._run_cycle_impl: 1525 lines.
ok       nodes/inner_monologue_node.py::InnerMonologueNode._think: 3601 lines.
ratchet: green.
```


## Summary
- Decisions resynced: 880
- Open decisions: 2
- Plans missing a Status line: 0
- Plans missing a Current State section: 16
- Unharvested docs/reviews/*.md: 120 (see docs/reviews/index_coverage.md)
- Open jobs: 417 (388 ready, 29 needs-input, 70 lab, 0 backfill)
