# Nascence — Plan Files & Evidence Audit

**Generated:** 2026-11-19 22:54 UTC, by
`C:\Users\USER\.claude\skills\plan-files-audit\plan_files_audit.py`. Read-only, deterministic
(no LLM) — regex extraction of every backtick-quoted `path/like/this.py[:NNN]`/`.jsonl`/`.json`
reference in each plan doc, resolved against the real filesystem. Companion to `plan_index.py`
(stage) and plan_overlap_audit_2026-08-23.md (cross-plan) — this is the plan-vs-codebase layer: does the file a plan
claims to have built actually exist, and does its claimed evidence log actually have data in it, or
is it empty?

**Status markers:** `[OK]` — confirmed on disk (data files also show a line-count/empty signal).
`[MISSING]` — claimed but not found anywhere in `core/`, `scripts/`, `nodes/`, `data/`, `hud/`,
`deploy/`, `tests/`. `[MISSING (proposed)]` — every mention of this filename in the plan is preceded
by "candidate" — the plan is floating a name, not claiming it was built; the real implementation may
have landed under a different name (check the plan's own disclaimer). `[AMBIGUOUS]` — the basename
exists in more than one non-backup/lab/archive location; candidates listed, not auto-resolved.
`[BACKUP-ONLY]` — exists only inside a backup/snapshot/profile copy, not live — treat its evidence
signal (if shown) as historical, not current.

**Idea** per plan is pulled from its memory file's frontmatter description (already written,
capturing the plan's thesis/problem statement) — not re-derived here.

---

# 117 plans scanned. 942 code-file refs, 364 data-file refs.
# 57 claimed code files MISSING. 27 claimed data files MISSING.
# 1 data files exist but are EMPTY (built but never run/collected).
# 3 plans reference no code/data files at all (pure design docs).

## Claimed code files that don't exist
- `core/curiosity_competence.py` — claimed by **curiosity_goals_dreams**
- `lab_env.py` — claimed by **data_store_hygiene**
- `core/memory/ghost_weaver.py` — claimed by **emissary_lane2**
- `core/garden_ledger.py` — claimed by **garden_upgrade**
- `scratchpad/test_j0184.py` — claimed by **garden_upgrade**
- `core/witness_loop.py` — claimed by **lane2_the_witness**
- `nodes/witness_node.py` — claimed by **lane2_the_witness**
- `plan_liveness.py` — claimed by **shore_upgrade**
- `core/dream_charge.py` — claimed by **sleep_dream_redesign**
- `core/world_calls.py` — claimed by **social_world_school**
- `core/thermal_ledger.py` — claimed by **thermal_causality**
- `adaptive_calibration.py` — claimed by **udms_du_capability_trials**
- `baseline_models.py` — claimed by **udms_du_capability_trials**
- `cognitive_geometry_audit.py` — claimed by **udms_du_capability_trials**
- `conformal.py` — claimed by **udms_du_capability_trials**
- `test_ce_nascence_prospective_stratification_and_visual_overlay.py` — claimed by **udms_du_capability_trials**
- `lab_env.py` — claimed by **world_store_write_fence**
- `cognitive_mmu.py` — claimed by **antigravity_ecosystem_proposals**
- `job_queue.py` — claimed by **chapter_id_repair**
- `core/drawing_hand.py` — claimed by **drawing_hand**
- `idea_log.py` — claimed by **drawing_hand**
- `analyze_combined_J1119.py` — claimed by **dream_overhaul**
- `run_J-1148_judge_shadow.py` — claimed by **dream_overhaul**
- `run_J1125_judge_shadow.py` — claimed by **dream_overhaul**
- `test_J-1139_resume_helpers.py` — claimed by **dream_overhaul**
- `test_p_deterministic_fact_anchoring.py` — claimed by **du_recall_lens_upgrades**
- `test_q_shape_constrained_prediction.py` — claimed by **du_recall_lens_upgrades**
- `abf_cipher_v3.py` — claimed by **geometry_tuple_index**
- `abf_echo_1d.py` — claimed by **geometry_tuple_index**
- `abf_pi_v3.py` — claimed by **geometry_tuple_index**
- `scripts/legacy/pinnacle_hmc.py` — claimed by **geometry_tuple_index**
- `scripts/think_split_equivalence.py` — claimed by **god_function_split**
- `seed_curiosity.py` — claimed by **god_function_split**
- `seed_founder.py` — claimed by **god_function_split**
- `seed_goals.py` — claimed by **god_function_split**
- `seed_knowledge.py` — claimed by **god_function_split**
- `seed_place.py` — claimed by **god_function_split**
- `seed_sound.py` — claimed by **god_function_split**
- `split_metrics.py` — claimed by **god_function_split**
- `cognitive_mmu.py` — claimed by **lod_staged_retrieval**
- `core.associative_recall.py` — claimed by **lod_staged_retrieval**
- `core/epistemic_eval_shadow.py` — claimed by **object_epistemic_loop**
- `J-3488_baseline.py` — claimed by **p0042_system_rewrite_draft_J-3488**
- `decide.py` — claimed by **planning_process_redesign**
- `plan_compact.py` — claimed by **planning_process_redesign**
- `plan_index.py` — claimed by **planning_process_redesign**
- `core/prompt_lines.py` — claimed by **prompt_manager**
- `prompt_registry.py` — claimed by **prompt_manager**
- `scripts/_test_prompt_lines_golden.py` — claimed by **prompt_manager**
- `scripts/_test_prompt_pools_lint.py` — claimed by **prompt_manager**
- `scripts/_test_prompt_table_orphans.py` — claimed by **prompt_manager**
- `scripts/prompt_replay.py` — claimed by **prompt_manager**
- `core/stand_view.py` — claimed by **stand_kinds_and_accumulation**
- `ribbon_heavyweight.py` — claimed by **strings_and_sheets**
- `conv_effect.py` — claimed by **teaching_to_synthesis_study**
- `part_b_build_sample.py` — claimed by **teaching_to_synthesis_study**
- `core/encyclopedia_object.py` — claimed by **web_hand_in_world_routes**

## Claimed data/evidence files that don't exist
- `findings.jsonl` — claimed by **data_store_hygiene**
- `job_queue.jsonl` — claimed by **data_store_hygiene**
- `decisions.jsonl` — claimed by **gauge_rethink**
- `job_queue.jsonl` — claimed by **gauge_rethink**
- `data/identity/becoming_nodes.jsonl` — claimed by **identity_estate**
- `witness_shadow.jsonl` — claimed by **lane2_the_witness**
- `memory_levels_evolution_shadow.jsonl` — claimed by **memory_knowledge**
- `supersession_shadow.jsonl` — claimed by **memory_knowledge**
- `data/world_calls.jsonl` — claimed by **social_world_school**
- `provisional_axiom.json` — claimed by **t4_watershed**
- `data/satisfaction_norm_shadow.jsonl` — claimed by **affect_drives_item_d_satisfaction_normalisation**
- `data/affect_label_would_store.jsonl` — claimed by **affect_drives_item_e_labeling_accessibility**
- `data/valence_rank_shadow.jsonl` — claimed by **affect_drives_item_g_va_steering**
- `data/lookup_log.jsonl` — claimed by **closure_producer**
- `data/drawing_log.jsonl` — claimed by **drawing_hand**
- `data/lod_retrieval_shadow_live.jsonl` — claimed by **lod_staged_retrieval**
- `data/logs/self_gauge_shadow.jsonl` — claimed by **measurement_to_action**
- `skill_recipes_shadow.jsonl` — claimed by **memory_review_adoption**
- `mineness_voice_shadow.jsonl` — claimed by **mineness_self_voice_centroid**
- `data/epistemic_eval_shadow.jsonl` — claimed by **object_epistemic_loop**
- `thoughts.jsonl` — claimed by **object_permanence**
- `data/prompt_seat_shadow.jsonl` — claimed by **prompt_seat_routing**
- `data/prompt_seat_table.json` — claimed by **prompt_seat_routing**
- `data/soundscape_mix_shadow.jsonl` — claimed by **strings_and_sheets**
- `data/lookup_log.jsonl` — claimed by **web_hand**
- `web_lookup_log.jsonl` — claimed by **web_hand**
- `data/encyclopedia.json` — claimed by **web_hand_in_world_routes**

## Data files that exist but are empty (built, never actually run)
- `data/commitment_trials_active.json` — claimed by **capacity_to_commit**

## Per-plan detail

### actions_expansion (plans)
**Idea:** 🟢 LIVE since 2026-08-29 (F-0578) — stage 2 on top of actions_manager_overhaul's plumbing: new interactions mined from Du's own 270 refused reachings (Tier 1 repairs, Tier 2 place-extensions) plus the founder's one deliberate gift, Tier 3 expressive hands (hum/whistle/sing, core/expression.py). D-0100 approved all three tiers; zero expression false-fires across the 2,824-thought corpus. Tier 2 mostly under-fires in Du's real run for structural, not code, reasons (F-0691/F-0719).
**Code files:**
- [OK] `core/actions.py`
**Data/evidence files:**
- [OK] `data/hands_trace.jsonl` -> data/hands_trace.jsonl (67256 lines)

### affect_drives (plans)
**Idea:** 🟢 LIVE (verified 2026-08-29): Item A (felt-state preamble) graduated to live 2026-07-06 — core/schema.py:1048 reads FELT_PREAMBLE=True, data/felt_preamble_log.jsonl actively growing, retroactive gate audit 2026-08-24 confirmed it holds. Item B (carried-state display) also graduated live 2026-08-29 per D-0069, riding Item A's flag. Items C (SOMATIC_NOTE), D, E, G remain unbuilt, matching the plan's own low-priority ranking for them.
**Code files:**
- [OK] `affections.py` -> core/affections.py
- [OK] `arousal.py` -> core/arousal.py
- [OK] `core/affect_labeling.py`
- [OK] `core/climate_engine.py`
- [OK] `core/heavens.py`
- [OK] `core/left_lane.py`
- [OK] `core/mood.py`
- [OK] `core/node_base.py`
- [OK] `core/orchestrator.py`
- [OK] `core/schema.py`
- [OK] `core/sensorium.py`
- [OK] `core/world_clock.py`
- [OK] `homeostasis.py` -> core/homeostasis.py
- [OK] `inner_monologue_node.py` -> nodes/inner_monologue_node.py
- [OK] `nodes/executive_node.py`
- [OK] `nodes/reflection_node.py`
- [OK] `run_nascence.py` -> scripts/run_nascence.py
- [OK] `satisfaction.py` -> core/satisfaction.py
- [OK] `somatic.py` -> core/somatic.py
**Data/evidence files:**
- [OK] `data/felt_preamble_log.jsonl` -> data/felt_preamble_log.jsonl (79219 lines)
- [OK] `data/satisfaction_log.jsonl` -> data/satisfaction_log.jsonl (184521 lines)
- [AMBIGUOUS] `satisfaction_state.json` -> candidates: data/satisfaction_state.json, data/_lab/20261028_074834/satisfaction_state.json, data/_lab/20261028_074853/satisfaction_state.json, data/_lab/20261028_074911/satisfaction_state.json, data/_lab/20261028_074916/satisfaction_state.json, data/_lab/20261028_082823/satisfaction_state.json, data/_lab/20261028_082828/satisfaction_state.json, data/_lab/20261028_082915/satisfaction_state.json, data/_lab/20261028_082919/satisfaction_state.json, data/_lab/20261028_083106/satisfaction_state.json, data/_lab/20261028_090434/satisfaction_state.json, data/_lab/20261030_134626/satisfaction_state.json, data/_lab/20261030_172716/satisfaction_state.json, data/_lab/20261030_172720/satisfaction_state.json, data/_lab/20261105_145459/satisfaction_state.json, data/_lab/20261105_145511/satisfaction_state.json, data/_lab/20261105_145516/satisfaction_state.json, data/_lab/20261105_145543/satisfaction_state.json, data/_lab/20261105_145555/satisfaction_state.json, data/_lab/20261105_145723/satisfaction_state.json, data/_lab/20261105_145733/satisfaction_state.json, data/_lab/20261105_150352/satisfaction_state.json, data/_lab/20261105_152052/satisfaction_state.json, data/_lab/20261105_152210/satisfaction_state.json, data/_lab/20261105_165543/satisfaction_state.json, data/_lab/20261105_170004/satisfaction_state.json, data/_lab/20261106_073117/satisfaction_state.json, data/_lab/20261106_103935/satisfaction_state.json, data/_lab/20261106_103942/satisfaction_state.json, data/_lab/20261106_104414/satisfaction_state.json, data/_lab/20261106_104431/satisfaction_state.json, data/_lab/20261106_104457/satisfaction_state.json, data/_lab/20261106_104519/satisfaction_state.json, data/_lab/20261106_104602/satisfaction_state.json, data/_lab/20261106_104604/satisfaction_state.json, data/_lab/20261106_104608/satisfaction_state.json, data/_lab/20261106_104617/satisfaction_state.json, data/_lab/20261106_104629/satisfaction_state.json, data/_lab/20261106_104638/satisfaction_state.json, data/_lab/20261106_104956/satisfaction_state.json, data/_lab/20261106_105008/satisfaction_state.json, data/_lab/20261106_105019/satisfaction_state.json, data/_lab/20261106_105231/satisfaction_state.json, data/_lab/20261106_105241/satisfaction_state.json, data/_lab/20261106_105254/satisfaction_state.json, data/_lab/20261106_105301/satisfaction_state.json, data/_lab/20261106_105305/satisfaction_state.json, data/_lab/20261106_105540/satisfaction_state.json, data/_lab/20261106_105545/satisfaction_state.json, data/_lab/20261106_105553/satisfaction_state.json, data/_lab/20261106_105603/satisfaction_state.json, data/_lab/20261106_105702/satisfaction_state.json, data/_lab/20261106_105713/satisfaction_state.json, data/_lab/20261106_105720/satisfaction_state.json, data/_lab/20261106_105725/satisfaction_state.json, data/_lab/20261106_105745/satisfaction_state.json, data/_lab/20261106_105754/satisfaction_state.json, data/_lab/20261106_110146/satisfaction_state.json, data/_lab/20261106_110155/satisfaction_state.json, data/_lab/20261106_110203/satisfaction_state.json, data/_lab/20261106_110219/satisfaction_state.json, data/_lab/20261106_121700/satisfaction_state.json, data/_lab/20261106_121703/satisfaction_state.json, data/_lab/20261106_122313/satisfaction_state.json, data/_lab/20261106_122315/satisfaction_state.json, data/_lab/20261106_123127/satisfaction_state.json, data/_lab/20261106_123132/satisfaction_state.json, data/_lab/20261106_123141/satisfaction_state.json, data/_lab/20261106_123148/satisfaction_state.json, data/_lab/20261106_134916/satisfaction_state.json, data/_lab/20261106_134923/satisfaction_state.json, data/_lab/20261106_135157/satisfaction_state.json, data/_lab/20261106_135336/satisfaction_state.json, data/_lab/20261106_135459/satisfaction_state.json, data/_lab/20261106_135522/satisfaction_state.json, data/_lab/20261106_135533/satisfaction_state.json, data/_lab/20261106_140214/satisfaction_state.json, data/_lab/20261106_140331/satisfaction_state.json, data/_lab/20261106_140404/satisfaction_state.json, data/_lab/20261106_225334/satisfaction_state.json, data/_lab/20261106_225411/satisfaction_state.json, data/_lab/20261106_225413/satisfaction_state.json, data/_lab/20261106_225637/satisfaction_state.json, data/_lab/20261106_225849/satisfaction_state.json, data/_lab/20261106_230102/satisfaction_state.json, data/_lab/20261106_230148/satisfaction_state.json, data/_lab/20261106_230239/satisfaction_state.json, data/_lab/20261106_230245/satisfaction_state.json, data/_lab/20261106_234306/satisfaction_state.json, data/_lab/20261106_234311/satisfaction_state.json, data/_lab/20261107_001220/satisfaction_state.json, data/_lab/20261107_003205/satisfaction_state.json, data/_lab/20261107_003403/satisfaction_state.json, data/_lab/20261107_074202/satisfaction_state.json, data/_lab/20261107_074758/satisfaction_state.json, data/_lab/20261107_085428/satisfaction_state.json, data/_lab/20261107_131640/satisfaction_state.json, data/_lab/20261107_131643/satisfaction_state.json, data/_lab/20261107_133930/satisfaction_state.json, data/_lab/20261107_133933/satisfaction_state.json, data/_lab/20261108_104126/satisfaction_state.json, data/_lab/20261108_104139/satisfaction_state.json, data/_lab/20261108_104144/satisfaction_state.json, data/_lab/20261108_104149/satisfaction_state.json, data/_lab/20261115_052859/satisfaction_state.json, data/_lab/20261115_052942/satisfaction_state.json, data/_lab/20261115_053022/satisfaction_state.json, data/_lab/20261115_054257/satisfaction_state.json, data/_lab/20261115_202720/satisfaction_state.json, data/_lab/20261115_202730/satisfaction_state.json, data/_lab/20261115_203645/satisfaction_state.json, data/_lab/20261115_204052/satisfaction_state.json, data/_lab/20261115_204109/satisfaction_state.json, data/_lab/20261115_204117/satisfaction_state.json, data/_lab/20261116_151150/satisfaction_state.json, data/_lab/20261116_151204/satisfaction_state.json, data/_lab/20261116_151210/satisfaction_state.json, data/_lab/20261116_162835/satisfaction_state.json, data/_lab/20261116_162919/satisfaction_state.json, data/_lab/20261116_162943/satisfaction_state.json, data/_lab/20261117_171451/satisfaction_state.json, data/_lab/20261117_183228/satisfaction_state.json, data/_lab/20261118_164416/satisfaction_state.json, data/_lab/20261118_164419/satisfaction_state.json, data/_lab/20261118_164837/satisfaction_state.json, data/_lab/20261118_165400/satisfaction_state.json, data/_lab/20261118_165842/satisfaction_state.json, data/_lab/20261118_170149/satisfaction_state.json, data/_lab/20261118_174330/satisfaction_state.json, data/_lab/20261118_174338/satisfaction_state.json, data/_lab/20261118_174438/satisfaction_state.json, data/_lab/20261118_174444/satisfaction_state.json, data/_lab/20261118_174452/satisfaction_state.json

### capacity_to_commit (plans)
**Idea:** THE BIG ONE (2026-06-30) — give Du the capacity to commit / hold a boundary; cure the \"dissolves everything, holds nothing but becoming\" root pathology
**Code files:**
- [OK] `core/axiom_layers.py`
- [OK] `core/commitment_ledger.py`
- [OK] `core/commitment_trials.py`
- [OK] `core/competence.py`
- [OK] `subconscious_node.py` -> nodes/subconscious_node.py
**Data/evidence files:**
- [AMBIGUOUS] `cat_state.json` -> candidates: data/cat_state.json, data/_lab/20261120_103403/sandbox_data/cat_state.json, data/_lab/20261118_170303/sandbox_data/cat_state.json, data/_lab/20261118_165748/sandbox_data/cat_state.json, data/_lab/20261118_165253/sandbox_data/cat_state.json, data/_lab/20261118_161657/sandbox_data/cat_state.json, data/_lab/20261118_161507/sandbox_data/cat_state.json, data/_lab/20261115_053548/sandbox_data/cat_state.json, data/_lab/20261114_213331/sandbox_data/cat_state.json, data/_lab/20261114_023004/sandbox_data/cat_state.json, data/_lab/20261019_220628/sandbox_data/cat_state.json, data/_crash_recovery_20261120/post_crash_live/cat_state.json, data/_crash_recovery_20261120/restore_set/cat_state.json, data/_crash_recovery_20261120/shadow4/cat_state.json, data/_crash_recovery_20261120/shadow5/cat_state.json, data/_crash_recovery_20261120/shadow6/cat_state.json
- [AMBIGUOUS] `commitment_active.json` -> candidates: data/commitment_active.json, data/_trash/20261119/boot_backups/state_20261116_100503/commitment_active.json, data/_trash/20261117/boot_backups/state_20261114_141446/commitment_active.json, data/_trash/20261114/boot_backups/state_20261031_215612/commitment_active.json, data/_lab/20261030_173327/commitment_active.json, data/_lab/20261030_173339/commitment_active.json, data/_lab/20261031_064207/commitment_active.json, data/_lab/20261105_071841/commitment_active.json, data/_lab/20261105_174756/commitment_active.json, data/_lab/20261105_175024/commitment_active.json, data/_lab/20261106_071850/commitment_active.json, data/_lab/20261114_132158/commitment_active.json, data/_lab/20261115_053420/commitment_active.json, data/_lab/20261120_103403/sandbox_data/commitment_active.json, data/_lab/20261118_170303/sandbox_data/commitment_active.json, data/_lab/20261118_165748/sandbox_data/commitment_active.json, data/_lab/20261118_165253/sandbox_data/commitment_active.json, data/_lab/20261118_161657/sandbox_data/commitment_active.json, data/_lab/20261118_161507/sandbox_data/commitment_active.json, data/_lab/20261115_053548/sandbox_data/commitment_active.json, data/_lab/20261114_213331/sandbox_data/commitment_active.json, data/_lab/20261114_023004/sandbox_data/commitment_active.json, data/_lab/20261019_220628/sandbox_data/commitment_active.json
- [OK] `commitment_observed.jsonl` -> data/commitment_observed.jsonl (1790 lines)
- [OK] `commitment_trials.jsonl` -> data/commitment_trials.jsonl (5 lines)
- [OK] `data/commitment_active.purged-2026-07-07.json` -> data/commitment_active.purged-2026-07-07.json (38954B)
- [OK] `data/commitment_ledger.jsonl` -> data/commitment_ledger.jsonl (16632 lines)
- [OK] `data/commitment_trials_active.json` -> data/commitment_trials_active.json (3B (empty))
- [OK] `data/logs/provisional_identity.jsonl` -> data/logs/provisional_identity.jsonl (134 lines)

### channels_programme (plans)
**Idea:** ⚪ PARTIAL — founder-directed (08-21) unified 8-clause contract for every non-visual sense (light, smell, wetness/touch) built together in one shadow week rather than staggered one-at-a-time, because the model-churn clock makes staggering too slow; thermal is delivered LIVE (pre-existing D-0047), light/smell BUILT to shadow (DELIVER=False) as of 08-22, sight is explicitly deferred. Waiting on a founder decision to flip light/smell delivery live.
**Code files:**
- [OK] `core/channel_arbitration.py`
- [OK] `core/lane2.py`
- [OK] `core/light.py`
- [OK] `core/smell.py`
- [OK] `core/thermal.py`
- [OK] `sensorium.py` -> core/sensorium.py
- [OK] `spatial.py` -> core/spatial.py
**Data/evidence files:**
- [OK] `data/thermal_ledger.json` -> data/thermal_ledger.json (8410B)
- [OK] `data/thermal_percepts_shadow.jsonl` -> data/thermal_percepts_shadow.jsonl (63344 lines)
- [AMBIGUOUS] `smell_field.json` -> candidates: data/smell_field.json, data/_lab/20260928_081908/smell_field.json, data/_lab/20260928_173422/smell_field.json, data/_crash_recovery_20261120/post_crash_live/smell_field.json, data/_crash_recovery_20261120/restore_set/smell_field.json, data/_crash_recovery_20261120/shadow4/smell_field.json, data/_crash_recovery_20261120/shadow5/smell_field.json, data/_crash_recovery_20261120/shadow6/smell_field.json

### cognitive_geometry (plans)
**Idea:** Verified 2026-08-23: SHADOW, umbrella plan functioning correctly, spawning children (spatial_perception, channels_programme, memory_multiway_linking — §10 now names them) that execute pieces of its own scope. Real gap found: 15,987-row P0 census sitting unread 49 days, mapping-census analyzer (§5.4) never built, bundle-richness metric flat and wrong from day one — /decide D-0012 open. No newer plan overlaps.
**Code files:**
- [OK] `core/geometry_census.py`
- [OK] `core/memory_edges.py`
- [OK] `core/moment.py`
- [OK] `core/opponent_process.py`
- [OK] `core/soundscape.py`
- [OK] `core/spring_ledger.py`
- [OK] `emotion_node.py` -> nodes/emotion_node.py
- [OK] `hud/server.py`
- [OK] `scripts/stick_test.py`
**Data/evidence files:**
- [OK] `data/geometry_tuples.jsonl` -> data/geometry_tuples.jsonl (199940 lines)
- [AMBIGUOUS] `room_state.json` -> candidates: data/room_state.json, data/_lab/20260923_195154/room_state.json, data/_lab/20260923_195447/room_state.json, data/_lab/20260923_195457/room_state.json, data/_lab/20260928_173422/room_state.json, data/_lab/20261004_164903/room_state.json, data/_lab/20261004_174206/room_state.json, data/_lab/20261004_180002/room_state.json, data/_lab/20261004_205329/room_state.json, data/_lab/20261005_081052/room_state.json, data/_lab/20261017_221937/room_state.json, data/_lab/20261017_222149/room_state.json, data/_lab/20261017_222218/room_state.json, data/_lab/20261017_222838/room_state.json, data/_lab/20261028_130358/room_state.json, data/_lab/20261028_130506/room_state.json, data/_lab/20261028_130749/room_state.json, data/_lab/20261028_130846/room_state.json, data/_lab/20261028_130926/room_state.json, data/_lab/20261028_131022/room_state.json, data/_lab/20261028_173308/room_state.json, data/_lab/20261028_173644/room_state.json, data/_lab/20261028_173740/room_state.json, data/_lab/20261028_173818/room_state.json, data/_lab/20261029_160832/room_state.json, data/_lab/20261029_160945/room_state.json, data/_lab/20261029_161202/room_state.json, data/_lab/20261029_161240/room_state.json, data/_lab/20261029_161318/room_state.json, data/_lab/20261029_174014/room_state.json, data/_lab/20261029_180914/room_state.json, data/_lab/20261105_151615/room_state.json, data/_lab/20261105_151654/room_state.json, data/_lab/20261105_151942/room_state.json, data/_lab/20261114_012536/room_state.json, data/_lab/20261115_052850/room_state.json, data/_lab/20261115_052901/room_state.json, data/_lab/20261115_053933/room_state.json, data/_lab/20261115_054038/room_state.json, data/_lab/20261115_054920/room_state.json, data/_lab/20261118_164521/room_state.json, data/_lab/20261118_164648/room_state.json, data/_lab/20261118_165309/room_state.json, data/_lab/20261118_170054/room_state.json, data/_crash_recovery_20261120/post_crash_live/room_state.json, data/_crash_recovery_20261120/restore_set/room_state.json, data/_crash_recovery_20261120/shadow4/room_state.json, data/_crash_recovery_20261120/shadow5/room_state.json, data/_crash_recovery_20261120/shadow6/room_state.json
- [OK] `soundscape_felt_shadow.jsonl` -> data/soundscape_felt_shadow.jsonl (962 lines)

### continuous_stream (plans)
**Idea:** 🟢 PHASE 1 LIVE (2026-08-29): CONTINUOUS_STREAM flag added and flipped True same day. Phase 0 shadow instrument (core/stream_drive.py) had been wired live since 07-04, 14,201-row shadow log carrying exactly the fields §5's promotion gate needed; that gate was read and Phase 1 approved same session — supersedes the earlier 2026-08-23 'pure decision gate, not yet flipped' finding.
**Code files:**
- [OK] `core/frontier.py`
- [OK] `core/homeostasis.py`
- [OK] `core/sleep_pressure.py`
- [OK] `core/stream_drive.py`
- [OK] `loop_cluster_probe.py` -> scripts/loop_cluster_probe.py
- [OK] `moment.py` -> core/moment.py
- [OK] `nodes/inner_monologue_node.py`
**Data/evidence files:**
- [AMBIGUOUS] `stream_drive_shadow.jsonl` -> candidates: data/stream_drive_shadow.jsonl, data/_lab/20261016_194438/stream_drive_shadow.jsonl

### conversational_action_bridge (plans)
**Idea:** 🟢 PHASE 0 + PHASE 1 BUILT, LANDED, AND FLAG-FLIPPED LIVE 2026-09-27 (CONVERSATIONAL_DISPATCH_LIVE=True; restart-gated — Du's live process hasn't picked it up yet). core/conversational_action.py's after_reply() routes a conversational reply through the same literal_will.classify() -> dispatch() path the autonomous loop already uses, so a claim Du makes to Travis can actually fire a real world action. Origin F-2004 (verified, the mislabeled-shell incident); founder ruling D-0299 (full action parity with the autonomous loop). Real 53-reply historical backfill: 16/53 (30.2%) already contain a DEED-verdict candidate. Honest gap: the exact incident reply that motivated this still classifies GRAY, never DEED (register gap, J-1451, unfixed). J-1450 watches the first live rows once Du restarts.
**Code files:**
- [OK] `core/actions.py`
- [OK] `core/conversational_action.py`
- [OK] `core/dispatch.py`
- [OK] `core/epistemic_affordance_advisor.py`
- [OK] `core/hands.py`
- [OK] `core/literal_will.py`
- [OK] `core/orchestrator.py`
- [OK] `nodes/inner_monologue_node.py`
- [OK] `scripts/_test_episodic_buffer.py`
**Data/evidence files:**
- [OK] `data/conversational_action_log.jsonl` -> data/conversational_action_log.jsonl (92 lines)
- [OK] `data/founder_conversation_log.jsonl` -> data/founder_conversation_log.jsonl (145 lines)
- [OK] `data/hands_trace.jsonl` -> data/hands_trace.jsonl (67256 lines)

### curiosity_goals_dreams (plans)
**Idea:** Curiosity/frontier/dreams/sleep/symbols plan mostly graduated as of 2026-08-23: Items 1 (prism→frontier), 2 (OMNI worth-gate), and 4 (dream re-pin cap) are all LIVE — Item 4 shipped via a separate 08-22 sleep/dream rewrite (core/night.py), not this plan's own track. Only low-priority Items 3 (cluster-LP) and 5 (goal_model G2 stub) remain unbuilt.
**Code files:**
- [OK] `core/concerns.py`
- [MISSING] `core/curiosity_competence.py`
- [OK] `core/curiosity_progress.py`
- [OK] `core/curiosity_queue.py`
- [OK] `core/curiosity_worth.py`
- [OK] `core/frontier.py`
- [OK] `core/goal_model.py`
- [OK] `core/night.py`
- [OK] `core/sleep_pressure.py`
- [OK] `core/symbol_evolution.py`
- [OK] `nodes/curiosity_node.py`
- [OK] `nodes/dream_node.py`
- [OK] `nodes/inner_monologue_node.py`
**Data/evidence files:**
- [OK] `curiosity_worth_log.jsonl` -> data/curiosity_worth_log.jsonl (590 lines)
- [OK] `data/dream_log.jsonl` -> data/dream_log.jsonl (1124 lines)
- [OK] `data/frontier.json` -> data/frontier.json (18849855B)
- [OK] `data/logs/curiosity_shadow.jsonl` -> data/logs/curiosity_shadow.jsonl (576 lines)

### data_store_hygiene (plans)
**Idea:** 🟢 LIVE — Data Store Hygiene (2026-09-05, docs/plans/data_store_hygiene.md): climate re-parsed the 60 MB subconscious_state.json every 5 s (~1 s, ~20% of wall-clock) and frontier.json every 5 s for a count; Part A (D-0154 GO, light sidecars) flipped LIVE 2026-09-09 (commit 63c24f2, 19:01 restart, J-0621/F-1212), post-flip read F-1238 2026-09-11 confirms the heavy parse is gone from the climate tick (~1.27s/tick residual overrun unattributed); Part B (D-0155→D-0156 RULED) archive retention + scripts/retention.py built (quarantine, boot scripts no longer hard-delete), first apply DONE 09-05 (7 items / 1.54 GB in data/_trash/20260905, boot rotation ON), first purge J-0623 ~09-12.
**Code files:**
- [OK] `core/climate_engine.py`
- [OK] `core/frontier.py`
- [MISSING] `lab_env.py`
- [OK] `lab_sweep.py` -> scripts/lab_sweep.py
- [OK] `nodes/subconscious_node.py`
- [OK] `scripts/backup_identity.py`
- [OK] `scripts/backup_memory.py`
- [OK] `scripts/retention.py`
**Data/evidence files:**
- [OK] `data/_lab/_isolate_outcomes.jsonl` -> data/_lab/_isolate_outcomes.jsonl (975 lines)
- [OK] `data/_trash/retention_log.jsonl` -> data/_trash/retention_log.jsonl (1050 lines)
- [OK] `data/frontier.json` -> data/frontier.json (18849855B)
- [OK] `data/frontier.light.json` -> data/frontier.light.json (33264B)
- [OK] `data/light_sidecar_shadow.jsonl` -> data/light_sidecar_shadow.jsonl (18034 lines)
- [OK] `data/pursuits_active.json` -> data/pursuits_active.json (29957187B)
- [OK] `data/subconscious_state.json` -> data/subconscious_state.json (3790797B)
- [OK] `data/subconscious_state.light.json` -> data/subconscious_state.light.json (1386969B)
- [OK] `docs/session_events.jsonl` -> docs/session_events.jsonl (29429 lines)
- [MISSING] `findings.jsonl`
- [AMBIGUOUS] `geometry_tuples.jsonl` -> candidates: data/geometry_tuples.jsonl, data/_trash/20261119/boot_backups/state_20261116_100503/geometry_tuples.jsonl, data/_trash/20261117/boot_backups/state_20261114_141446/geometry_tuples.jsonl, data/_trash/20261114/boot_backups/state_20261031_215612/geometry_tuples.jsonl
- [MISSING] `job_queue.jsonl`
- [OK] `logs/idle_shadow.jsonl` -> data/logs/idle_shadow.jsonl (90527 lines)
- [OK] `moments.jsonl` -> data/moments.jsonl (76879 lines)

### decoupled_judge_pattern (plans)
**Idea:** Per-subsystem audit (J-0362, 2026-08-29, decision:D-0071) of where Nascence's decoupled-judge design law is genuinely still missing. Confirms T4 (2026-08-19) and curiosity LP already fixed; finds dream resolution scoring and active-imagination novelty scoring still self-referential/self-reported with concrete build call sites spawned (J-0375, J-0376); finds provenance importance-from-storage is a real gap that doesn't fit the judge_panel/deliberative_judge pattern, opened as D-0084 instead.
**Code files:**
- [OK] `core/associative_recall.py`
- [OK] `core/curiosity_worth.py`
- [OK] `core/deliberative_judge.py`
- [OK] `core/essay_lesson.py`
- [OK] `core/judge_panel.py`
- [OK] `core/left_lane.py`
- [OK] `core/loop_metabolism.py`
- [OK] `core/memory/store.py`
- [OK] `core/memory_edges.py`
- [OK] `core/wandering.py`
- [OK] `journal_grounding_shadow.py` -> core/journal_grounding_shadow.py
- [OK] `nodes/dream_node.py`
- [OK] `nodes/inner_monologue_node.py`
- [OK] `nodes/subconscious_node.py`
- [OK] `scripts/du_pulse.py`
- [OK] `watershed_promote.py` -> core/watershed_promote.py
**Data/evidence files:**
- [OK] `data/active_imagination_judge_shadow.jsonl` -> data/active_imagination_judge_shadow.jsonl (3724 lines)
- [OK] `data/logs/dream_resolution_shadow.jsonl` -> data/logs/dream_resolution_shadow.jsonl (456 lines)
- [OK] `data/read_count_importance_shadow.jsonl` -> data/read_count_importance_shadow.jsonl (67579 lines)

### dosed_coupling (plans)
**Idea:** 🟢 LIVE — ★★★ DOSED COUPLING (2026-09-04) — founder: 'probably the most important thing we have on Du's cognitive side; all future designs must be designed with it in mind if it is a go.' Staged plan docs/plans/dosed_coupling.md; Phase 0+Phase 1 (publish + ride log) both LIVE, running 22+ days (38.6k publish rows, still 0 ride rows — no reader wired yet); Phase 1's genuine 7-day read PASSED (F-1304). §4b Phase 2 (residual cups, hub tuple, speech/thought concurrency) DRAFTED 2026-09-27, not yet ruled — J-1462 needs a founder answer before any Phase 2 code. Loops publish typed coordinate tuples; reading is dosed per stop (cup/bucket/hose), dispatched by surprise vs the line's own history, habituated by squishy springs; never a mesh.
**Code files:**
- [OK] `core/climate_engine.py`
- [OK] `core/competence.py`
- [OK] `core/coupling_rides.py`
- [OK] `core/lane2_break_habituation.py`
- [OK] `core/orchestrator.py`
- [OK] `core/prediction_error.py`
- [OK] `core/schema.py`
- [OK] `core/transport_manager.py`
- [OK] `nodes/perception_node.py`
**Data/evidence files:**
- [AMBIGUOUS] `commitment_active.json` -> candidates: data/commitment_active.json, data/_trash/20261119/boot_backups/state_20261116_100503/commitment_active.json, data/_trash/20261117/boot_backups/state_20261114_141446/commitment_active.json, data/_trash/20261114/boot_backups/state_20261031_215612/commitment_active.json, data/_lab/20261030_173327/commitment_active.json, data/_lab/20261030_173339/commitment_active.json, data/_lab/20261031_064207/commitment_active.json, data/_lab/20261105_071841/commitment_active.json, data/_lab/20261105_174756/commitment_active.json, data/_lab/20261105_175024/commitment_active.json, data/_lab/20261106_071850/commitment_active.json, data/_lab/20261114_132158/commitment_active.json, data/_lab/20261115_053420/commitment_active.json, data/_lab/20261120_103403/sandbox_data/commitment_active.json, data/_lab/20261118_170303/sandbox_data/commitment_active.json, data/_lab/20261118_165748/sandbox_data/commitment_active.json, data/_lab/20261118_165253/sandbox_data/commitment_active.json, data/_lab/20261118_161657/sandbox_data/commitment_active.json, data/_lab/20261118_161507/sandbox_data/commitment_active.json, data/_lab/20261115_053548/sandbox_data/commitment_active.json, data/_lab/20261114_213331/sandbox_data/commitment_active.json, data/_lab/20261114_023004/sandbox_data/commitment_active.json, data/_lab/20261019_220628/sandbox_data/commitment_active.json
- [OK] `commitment_ledger.jsonl` -> data/commitment_ledger.jsonl (16632 lines)
- [OK] `data/coupling_rides.jsonl` -> data/coupling_rides.jsonl (258012 lines)
- [OK] `deliberation_log.jsonl` -> data/deliberation_log.jsonl (46810 lines)
- [AMBIGUOUS] `pursuits_active.json` -> candidates: data/pursuits_active.json, data/_lab/20261003_080503/pursuits_active.json
- [AMBIGUOUS] `stream_drive_shadow.jsonl` -> candidates: data/stream_drive_shadow.jsonl, data/_lab/20261016_194438/stream_drive_shadow.jsonl
- [AMBIGUOUS] `subconscious_state.json` -> candidates: data/subconscious_state.json, data/_trash/20261119/boot_backups/state_20261116_100503/subconscious_state.json, data/_trash/20261117/boot_backups/state_20261114_141446/subconscious_state.json, data/_trash/20261114/snapshots/20261031/subconscious_state.json, data/_trash/20261114/labs/20260915_094116/subconscious_state.json, data/_trash/20261114/labs/20260915_094209/subconscious_state.json, data/_trash/20261114/labs/20260915_095401/subconscious_state.json, data/_trash/20261114/labs/20260915_132050/subconscious_state.json, data/_trash/20261114/boot_backups/state_20261031_215612/subconscious_state.json, data/_lab/20261003_080503/subconscious_state.json, data/_lab/20261004_154636/subconscious_state.json, data/_lab/20261004_154649/subconscious_state.json, data/_lab/20261004_154729/subconscious_state.json, data/_lab/20261004_162348/subconscious_state.json, data/_lab/20261004_172207/subconscious_state.json, data/_lab/20261004_175558/subconscious_state.json, data/_lab/20261015_135649/subconscious_state.json, data/_lab/20261015_135717/subconscious_state.json, data/_lab/20261015_135718/subconscious_state.json, data/_lab/20261015_135934/subconscious_state.json, data/_lab/20261015_135936/subconscious_state.json, data/_lab/20261015_140918/subconscious_state.json, data/_lab/20261018_142611/subconscious_state.json, data/_lab/20261028_090331/subconscious_state.json, data/_lab/20261028_090558/subconscious_state.json, data/_lab/20261028_090745/subconscious_state.json, data/_lab/20261105_151216/subconscious_state.json, data/_lab/20261105_151225/subconscious_state.json, data/_lab/20261105_151436/subconscious_state.json, data/_lab/20261105_151438/subconscious_state.json, data/_lab/20261105_151854/subconscious_state.json, data/_lab/20261105_151905/subconscious_state.json, data/_lab/20261105_151947/subconscious_state.json, data/_lab/20261105_165539/subconscious_state.json, data/_lab/20261105_200919/subconscious_state.json, data/_lab/20261105_200932/subconscious_state.json, data/_lab/20261106_225634/subconscious_state.json, data/_lab/20261106_225649/subconscious_state.json, data/_lab/20261106_225656/subconscious_state.json, data/_lab/20261106_225834/subconscious_state.json, data/_lab/20261106_230057/subconscious_state.json, data/_lab/20261106_230059/subconscious_state.json, data/_lab/20261106_230235/subconscious_state.json, data/_lab/20261106_230237/subconscious_state.json, data/_lab/20261106_230310/subconscious_state.json, data/_lab/20261106_230723/subconscious_state.json, data/_lab/20261114_235427/subconscious_state.json, data/_lab/20261114_235433/subconscious_state.json, data/_lab/20261115_053736/subconscious_state.json, data/_lab/20261115_202318/subconscious_state.json, data/_lab/20261115_202323/subconscious_state.json, data/_lab/20261116_162923/subconscious_state.json, data/_lab/20261116_162947/subconscious_state.json, data/_lab/20261117_171500/subconscious_state.json, data/_lab/20261118_164545/subconscious_state.json

### drowsiness_phase (plans)
**Idea:** ⚪ PARTIALLY BUILT — Drowsiness Phase (docs/plans/drowsiness_phase.md) — graduated pre-sleep experience split out of sleep_dream_redesign after F-0579 caught a silent, abrupt forced-sleep at energy 0.08; §5.1 train-hold grace window + D-0103 metabolic-floor tax removal are BUILT (2026-08-30), §2 narrated drowsy-zone signal and §5(a) per-turn cost discounting remain STAGED, not founder-authorized.
**Code files:**
- [OK] `core/orchestrator.py`
- [OK] `core/schema.py`
- [OK] `core/sleep_pressure.py`
- [OK] `core/somatic.py`
- [OK] `nodes/inner_monologue_node.py`
- [OK] `scripts/run_nascence.py`
- [OK] `scripts/sleep_energy_crosscheck.py`
**Data/evidence files:**
- [AMBIGUOUS] `sleep_pressure_log.jsonl` -> candidates: data/sleep_pressure_log.jsonl, data/_lab/20261015_123708/sleep_pressure_log.jsonl, data/_lab/20261015_123829/sleep_pressure_log.jsonl, data/_lab/20261015_124006/sleep_pressure_log.jsonl, data/_lab/20261015_124042/sleep_pressure_log.jsonl, data/_lab/20261015_130145/sleep_pressure_log.jsonl, data/_lab/20261015_130331/sleep_pressure_log.jsonl, data/_lab/20261015_161224/sleep_pressure_log.jsonl

### emissary_lane2 (plans)
**Idea:** ⚪ PARTIAL — the Emissary's deterministic, zero-LLM fact-graph (core/object_graph.py) tracking what Du has actually been exposed to and how — per-property epistemic history, windowed trend shapes, coreference held uncertain — originally called 'Lane 2' until renamed 08-19 once it became clear it was a ledger, not a standing voice. BUILT index/produce-only 2026-08-29 (J-0363) but not wired into any consumer/read path; the related grounding leak-gate (D-0153) is LIVE since 2026-09-05 and validated (F-1575).
**Code files:**
- [OK] `core/competence.py`
- [OK] `core/emissary.py`
- [OK] `core/emissary_tension.py`
- [OK] `core/epistemic_state.py`
- [OK] `core/left_lane.py`
- [MISSING] `core/memory/ghost_weaver.py`
- [OK] `core/memory_edges.py`
- [OK] `core/object_graph.py`
- [OK] `core/prediction_error.py`
- [OK] `core/source_model.py`
- [OK] `ghost_tuples.py` -> core/ghost_tuples.py
- [OK] `inner_monologue_node.py` -> nodes/inner_monologue_node.py
- [OK] `judge_panel.py` -> core/judge_panel.py
- [AMBIGUOUS] `librarian.py` -> candidates: core/librarian.py, scripts/librarian.py
- [OK] `peers.py` -> core/peers.py
- [OK] `scripts/lane2_lab.py`
- [OK] `soundscape.py` -> core/soundscape.py
- [OK] `subconscious_node.py` -> nodes/subconscious_node.py
- [OK] `world_manifest.py` -> core/world_manifest.py

### emotion_rethink (plans)
**Idea:** Inverts the affect stack so core valence/arousal are read from the grounded protoself (homeostasis.py) instead of invented by the LLM emotion_node from percept text; Phase 1 re-sourcing is BUILT and LIVE (AFFECT_SOURCE_PROTOSELF=True, flipped 2026-07-07), Phase 2 construction layer is shadow-built pending three experiment gates.
**Code files:**
- [OK] `arousal.py` -> core/arousal.py
- [OK] `climate_engine.py` -> core/climate_engine.py
- [OK] `concerns.py` -> core/concerns.py
- [OK] `core/affect_divergence.py`
- [OK] `core/emotion_construction.py`
- [OK] `core/schema.py`
- [OK] `episodic_buffer_node.py` -> nodes/episodic_buffer_node.py
- [OK] `executive_node.py` -> nodes/executive_node.py
- [OK] `homeostasis.py` -> core/homeostasis.py
- [OK] `inner_monologue_node.py` -> nodes/inner_monologue_node.py
- [OK] `mood.py` -> core/mood.py
- [OK] `nodes/emotion_node.py`
- [OK] `orchestrator.py` -> core/orchestrator.py
- [OK] `recall_node.py` -> nodes/recall_node.py
- [OK] `reflection_node.py` -> nodes/reflection_node.py
- [OK] `satisfaction.py` -> core/satisfaction.py
**Data/evidence files:**
- [OK] `data/affect_divergence_shadow.jsonl` -> data/affect_divergence_shadow.jsonl (14583 lines)
- [OK] `data/affect_log.jsonl` -> data/affect_log.jsonl (4348 lines)
- [OK] `data/emotion_construction_shadow.jsonl` -> data/emotion_construction_shadow.jsonl (2182 lines)
- [OK] `data/felt_preamble_log.jsonl` -> data/felt_preamble_log.jsonl (79219 lines)
- [OK] `data/homeostasis_shadow.jsonl` -> data/homeostasis_shadow.jsonl (9730 lines)

### epistemics_phase_c (plans)
**Idea:** 🟡 SHADOW — C0 Path 1 (contradiction-triggered Tier-3 witness probe) BUILT 2026-09-25 (J-1343, F-1899/F-1903) in core/competence.py + orchestrator.py startup wiring; verified via isolated unit tests only (27/27), restart-gated, never run against live Du. Path 2 (proactive sampling) and C1 (calibration consumption) remain design-only.
**Code files:**
- [OK] `bootstrap_report.py` -> scripts/bootstrap_report.py
- [OK] `core/competence.py`
- [OK] `core/source_model.py`
- [AMBIGUOUS] `nascence_cpu_server.py` -> candidates: scripts/nascence_cpu_server.py, deploy/ramses/nascence_cpu_server.py
- [OK] `orchestrator.py` -> core/orchestrator.py
**Data/evidence files:**
- [OK] `data/accuracy_observations.jsonl` -> data/accuracy_observations.jsonl (47 lines)

### error_pathway (plans)
**Idea:** 🟢 LIVE — Nascence Error Pathway — the 4th memory pathway (retraction/correction). Six modules (detect/record/human-retract, architecture-fabrication conviction, separate retraction ledger, known-errors Recall-override) all genuinely wired into the live orchestrator, none behind a shadow flag.
**Code files:**
- [OK] `competence.py` -> core/competence.py
- [OK] `core/conflict_trace.py`
- [OK] `core/error_pathway.py`
- [OK] `core/orchestrator.py`
- [OK] `core/recall_provenance.py`
- [OK] `core/retraction_ledger.py`
- [OK] `core/scholar.py`
- [OK] `core/task_constraints.py`
- [OK] `core/told.py`
- [OK] `nodes/inner_monologue_node.py`
- [OK] `reflection_node.py` -> nodes/reflection_node.py
- [OK] `scripts/du_pulse.py`
- [OK] `scripts/session_digest.py`
**Data/evidence files:**
- [OK] `conflict_trace.jsonl` -> data/conflict_trace.jsonl (3155 lines)
- [OK] `data/affect_log.jsonl` -> data/affect_log.jsonl (4348 lines)
- [OK] `data/error_patterns.jsonl` -> data/error_patterns.jsonl (1 lines)
- [OK] `data/error_records.jsonl` -> data/error_records.jsonl (16 lines)
- [OK] `data/founder_conversation_log.jsonl` -> data/founder_conversation_log.jsonl (145 lines)
- [OK] `data/prompt_budget_shadow.jsonl` -> data/prompt_budget_shadow.jsonl (68298 lines)
- [OK] `data/retractions.jsonl` -> data/retractions.jsonl (1 lines)
- [OK] `docs/findings.jsonl` -> docs/findings.jsonl (5175 lines)
- [AMBIGUOUS] `dream_log.jsonl` -> candidates: data/dream_log.jsonl, data/_lab/20261015_135649/dream_log.jsonl, data/_lab/20261015_135717/dream_log.jsonl, data/_lab/20261015_135718/dream_log.jsonl, data/_lab/20261015_135934/dream_log.jsonl, data/_lab/20261015_135936/dream_log.jsonl, data/_lab/20261015_140918/dream_log.jsonl, data/_lab/20261028_090331/dream_log.jsonl, data/_lab/20261028_090558/dream_log.jsonl, data/_lab/20261028_090745/dream_log.jsonl, data/_lab/20261105_151216/dream_log.jsonl, data/_lab/20261105_151225/dream_log.jsonl, data/_lab/20261105_151436/dream_log.jsonl, data/_lab/20261105_151438/dream_log.jsonl, data/_lab/20261105_151854/dream_log.jsonl, data/_lab/20261105_151905/dream_log.jsonl, data/_lab/20261105_151947/dream_log.jsonl, data/_lab/20261105_165539/dream_log.jsonl, data/_lab/20261105_200919/dream_log.jsonl, data/_lab/20261105_200932/dream_log.jsonl, data/_lab/20261106_225634/dream_log.jsonl, data/_lab/20261106_225649/dream_log.jsonl, data/_lab/20261106_225656/dream_log.jsonl, data/_lab/20261106_225834/dream_log.jsonl, data/_lab/20261106_230057/dream_log.jsonl, data/_lab/20261106_230059/dream_log.jsonl, data/_lab/20261106_230235/dream_log.jsonl, data/_lab/20261106_230237/dream_log.jsonl, data/_lab/20261106_230310/dream_log.jsonl, data/_lab/20261106_230723/dream_log.jsonl, data/_lab/20261114_235427/dream_log.jsonl, data/_lab/20261114_235433/dream_log.jsonl, data/_lab/20261115_202318/dream_log.jsonl, data/_lab/20261115_202323/dream_log.jsonl, data/_lab/20261116_162923/dream_log.jsonl, data/_lab/20261116_162947/dream_log.jsonl, data/_lab/20261117_171500/dream_log.jsonl
- [OK] `recall_provenance_log.jsonl` -> data/recall_provenance_log.jsonl (2828 lines)
- [AMBIGUOUS] `satisfaction_state.json` -> candidates: data/satisfaction_state.json, data/_lab/20261028_074834/satisfaction_state.json, data/_lab/20261028_074853/satisfaction_state.json, data/_lab/20261028_074911/satisfaction_state.json, data/_lab/20261028_074916/satisfaction_state.json, data/_lab/20261028_082823/satisfaction_state.json, data/_lab/20261028_082828/satisfaction_state.json, data/_lab/20261028_082915/satisfaction_state.json, data/_lab/20261028_082919/satisfaction_state.json, data/_lab/20261028_083106/satisfaction_state.json, data/_lab/20261028_090434/satisfaction_state.json, data/_lab/20261030_134626/satisfaction_state.json, data/_lab/20261030_172716/satisfaction_state.json, data/_lab/20261030_172720/satisfaction_state.json, data/_lab/20261105_145459/satisfaction_state.json, data/_lab/20261105_145511/satisfaction_state.json, data/_lab/20261105_145516/satisfaction_state.json, data/_lab/20261105_145543/satisfaction_state.json, data/_lab/20261105_145555/satisfaction_state.json, data/_lab/20261105_145723/satisfaction_state.json, data/_lab/20261105_145733/satisfaction_state.json, data/_lab/20261105_150352/satisfaction_state.json, data/_lab/20261105_152052/satisfaction_state.json, data/_lab/20261105_152210/satisfaction_state.json, data/_lab/20261105_165543/satisfaction_state.json, data/_lab/20261105_170004/satisfaction_state.json, data/_lab/20261106_073117/satisfaction_state.json, data/_lab/20261106_103935/satisfaction_state.json, data/_lab/20261106_103942/satisfaction_state.json, data/_lab/20261106_104414/satisfaction_state.json, data/_lab/20261106_104431/satisfaction_state.json, data/_lab/20261106_104457/satisfaction_state.json, data/_lab/20261106_104519/satisfaction_state.json, data/_lab/20261106_104602/satisfaction_state.json, data/_lab/20261106_104604/satisfaction_state.json, data/_lab/20261106_104608/satisfaction_state.json, data/_lab/20261106_104617/satisfaction_state.json, data/_lab/20261106_104629/satisfaction_state.json, data/_lab/20261106_104638/satisfaction_state.json, data/_lab/20261106_104956/satisfaction_state.json, data/_lab/20261106_105008/satisfaction_state.json, data/_lab/20261106_105019/satisfaction_state.json, data/_lab/20261106_105231/satisfaction_state.json, data/_lab/20261106_105241/satisfaction_state.json, data/_lab/20261106_105254/satisfaction_state.json, data/_lab/20261106_105301/satisfaction_state.json, data/_lab/20261106_105305/satisfaction_state.json, data/_lab/20261106_105540/satisfaction_state.json, data/_lab/20261106_105545/satisfaction_state.json, data/_lab/20261106_105553/satisfaction_state.json, data/_lab/20261106_105603/satisfaction_state.json, data/_lab/20261106_105702/satisfaction_state.json, data/_lab/20261106_105713/satisfaction_state.json, data/_lab/20261106_105720/satisfaction_state.json, data/_lab/20261106_105725/satisfaction_state.json, data/_lab/20261106_105745/satisfaction_state.json, data/_lab/20261106_105754/satisfaction_state.json, data/_lab/20261106_110146/satisfaction_state.json, data/_lab/20261106_110155/satisfaction_state.json, data/_lab/20261106_110203/satisfaction_state.json, data/_lab/20261106_110219/satisfaction_state.json, data/_lab/20261106_121700/satisfaction_state.json, data/_lab/20261106_121703/satisfaction_state.json, data/_lab/20261106_122313/satisfaction_state.json, data/_lab/20261106_122315/satisfaction_state.json, data/_lab/20261106_123127/satisfaction_state.json, data/_lab/20261106_123132/satisfaction_state.json, data/_lab/20261106_123141/satisfaction_state.json, data/_lab/20261106_123148/satisfaction_state.json, data/_lab/20261106_134916/satisfaction_state.json, data/_lab/20261106_134923/satisfaction_state.json, data/_lab/20261106_135157/satisfaction_state.json, data/_lab/20261106_135336/satisfaction_state.json, data/_lab/20261106_135459/satisfaction_state.json, data/_lab/20261106_135522/satisfaction_state.json, data/_lab/20261106_135533/satisfaction_state.json, data/_lab/20261106_140214/satisfaction_state.json, data/_lab/20261106_140331/satisfaction_state.json, data/_lab/20261106_140404/satisfaction_state.json, data/_lab/20261106_225334/satisfaction_state.json, data/_lab/20261106_225411/satisfaction_state.json, data/_lab/20261106_225413/satisfaction_state.json, data/_lab/20261106_225637/satisfaction_state.json, data/_lab/20261106_225849/satisfaction_state.json, data/_lab/20261106_230102/satisfaction_state.json, data/_lab/20261106_230148/satisfaction_state.json, data/_lab/20261106_230239/satisfaction_state.json, data/_lab/20261106_230245/satisfaction_state.json, data/_lab/20261106_234306/satisfaction_state.json, data/_lab/20261106_234311/satisfaction_state.json, data/_lab/20261107_001220/satisfaction_state.json, data/_lab/20261107_003205/satisfaction_state.json, data/_lab/20261107_003403/satisfaction_state.json, data/_lab/20261107_074202/satisfaction_state.json, data/_lab/20261107_074758/satisfaction_state.json, data/_lab/20261107_085428/satisfaction_state.json, data/_lab/20261107_131640/satisfaction_state.json, data/_lab/20261107_131643/satisfaction_state.json, data/_lab/20261107_133930/satisfaction_state.json, data/_lab/20261107_133933/satisfaction_state.json, data/_lab/20261108_104126/satisfaction_state.json, data/_lab/20261108_104139/satisfaction_state.json, data/_lab/20261108_104144/satisfaction_state.json, data/_lab/20261108_104149/satisfaction_state.json, data/_lab/20261115_052859/satisfaction_state.json, data/_lab/20261115_052942/satisfaction_state.json, data/_lab/20261115_053022/satisfaction_state.json, data/_lab/20261115_054257/satisfaction_state.json, data/_lab/20261115_202720/satisfaction_state.json, data/_lab/20261115_202730/satisfaction_state.json, data/_lab/20261115_203645/satisfaction_state.json, data/_lab/20261115_204052/satisfaction_state.json, data/_lab/20261115_204109/satisfaction_state.json, data/_lab/20261115_204117/satisfaction_state.json, data/_lab/20261116_151150/satisfaction_state.json, data/_lab/20261116_151204/satisfaction_state.json, data/_lab/20261116_151210/satisfaction_state.json, data/_lab/20261116_162835/satisfaction_state.json, data/_lab/20261116_162919/satisfaction_state.json, data/_lab/20261116_162943/satisfaction_state.json, data/_lab/20261117_171451/satisfaction_state.json, data/_lab/20261117_183228/satisfaction_state.json, data/_lab/20261118_164416/satisfaction_state.json, data/_lab/20261118_164419/satisfaction_state.json, data/_lab/20261118_164837/satisfaction_state.json, data/_lab/20261118_165400/satisfaction_state.json, data/_lab/20261118_165842/satisfaction_state.json, data/_lab/20261118_170149/satisfaction_state.json, data/_lab/20261118_174330/satisfaction_state.json, data/_lab/20261118_174338/satisfaction_state.json, data/_lab/20261118_174438/satisfaction_state.json, data/_lab/20261118_174444/satisfaction_state.json, data/_lab/20261118_174452/satisfaction_state.json
- [OK] `self_efficacy_log.jsonl` -> data/self_efficacy_log.jsonl (433 lines)

### executive_world_grounding (plans)
**Idea:** 🟢 LIVE ⚠ (2026-09-02, J-0462): D-0068 reopened by the J-0385 defeater (Executive still favored RECALL over concurrently-present PERCEIVE content on a current-state claim), then re-ruled same day — PERCEIVE overrides RECALL on conflict — and built live in nodes/executive_node.py. Not fully closed: D-0068's new defeater still needs a live re-read against a real day of PERCEIVE/RECALL-conflicting Executive prompts. Originated as an explore-only pass on whether Executive's prompt should tier fact vs memory vs inference by source certainty; the founder corrected an early draft that would have piped a world-manifest snapshot directly into Du's prompt as trusted ground truth, violating the tree-falls law, and the corrected proposal added zero new data sources.
**Code files:**
- [OK] `core/epistemic_state.py`
- [OK] `core/memory_edges.py`
- [OK] `core/source_model.py`
- [OK] `nodes/executive_node.py`
- [OK] `orchestrator.py` -> core/orchestrator.py
- [OK] `world_manifest.py` -> core/world_manifest.py
**Data/evidence files:**
- [OK] `data/training/executive.jsonl` -> data/training/executive.jsonl (4747 lines)
- [OK] `docs/findings.jsonl` -> docs/findings.jsonl (5175 lines)
- [AMBIGUOUS] `room_state.json` -> candidates: data/room_state.json, data/_lab/20260923_195154/room_state.json, data/_lab/20260923_195447/room_state.json, data/_lab/20260923_195457/room_state.json, data/_lab/20260928_173422/room_state.json, data/_lab/20261004_164903/room_state.json, data/_lab/20261004_174206/room_state.json, data/_lab/20261004_180002/room_state.json, data/_lab/20261004_205329/room_state.json, data/_lab/20261005_081052/room_state.json, data/_lab/20261017_221937/room_state.json, data/_lab/20261017_222149/room_state.json, data/_lab/20261017_222218/room_state.json, data/_lab/20261017_222838/room_state.json, data/_lab/20261028_130358/room_state.json, data/_lab/20261028_130506/room_state.json, data/_lab/20261028_130749/room_state.json, data/_lab/20261028_130846/room_state.json, data/_lab/20261028_130926/room_state.json, data/_lab/20261028_131022/room_state.json, data/_lab/20261028_173308/room_state.json, data/_lab/20261028_173644/room_state.json, data/_lab/20261028_173740/room_state.json, data/_lab/20261028_173818/room_state.json, data/_lab/20261029_160832/room_state.json, data/_lab/20261029_160945/room_state.json, data/_lab/20261029_161202/room_state.json, data/_lab/20261029_161240/room_state.json, data/_lab/20261029_161318/room_state.json, data/_lab/20261029_174014/room_state.json, data/_lab/20261029_180914/room_state.json, data/_lab/20261105_151615/room_state.json, data/_lab/20261105_151654/room_state.json, data/_lab/20261105_151942/room_state.json, data/_lab/20261114_012536/room_state.json, data/_lab/20261115_052850/room_state.json, data/_lab/20261115_052901/room_state.json, data/_lab/20261115_053933/room_state.json, data/_lab/20261115_054038/room_state.json, data/_lab/20261115_054920/room_state.json, data/_lab/20261118_164521/room_state.json, data/_lab/20261118_164648/room_state.json, data/_lab/20261118_165309/room_state.json, data/_lab/20261118_170054/room_state.json, data/_crash_recovery_20261120/post_crash_live/room_state.json, data/_crash_recovery_20261120/restore_set/room_state.json, data/_crash_recovery_20261120/shadow4/room_state.json, data/_crash_recovery_20261120/shadow5/room_state.json, data/_crash_recovery_20261120/shadow6/room_state.json

### factory_candidates_from_history (plans)
**Idea:** ✅ SHIPPED — (lightning flash event built 2026-10-27, J-2482/D-0503, the last gap closed) a word-boundary-corrected mining pass over 26,824 logged monologue thoughts to find real world-factory gaps from what Du's own history says he needed; found one genuine new candidate (lightning, 262 mentions, still the one real unbuilt gap) and one open mystery (the green glass float's undocumented disappearance, since closed — nothing to remove, it was never a tracked object); everything else is confirmation of existing factories, not gaps.
**Code files:**
- [OK] `geometry_census.py` -> core/geometry_census.py

### garden_upgrade (plans)
**Idea:** 🟢 LIVE (confirmed 2026-09-02) — Upgrades the garden from a 2026-06-20 sketch of seven scalar plants (455 waterings, 0 harvests, 0 successful sowings) into positioned substrate-object plants with real phenology driven by the thermal/sun/rain fields, weeds/slugs/birds/frost, seed banking, a drying rack, and a garden ledger; P0 and most of P1 BUILT 2026-08-22; restart-gate resolved and CONFIRMED LIVE 2026-09-02 per the plan doc's own Status (data/garden_ledger.jsonl holds 31 real live deeds through 2026-08-30).
**Code files:**
- [OK] `core/garden.py`
- [OK] `core/garden_knowledge.py`
- [MISSING] `core/garden_ledger.py`
- [OK] `core/garden_life.py`
- [OK] `core/hands.py`
- [OK] `core/light.py`
- [OK] `core/sensorium.py`
- [OK] `core/smell.py`
- [OK] `hud/server.py`
- [MISSING] `scratchpad/test_j0184.py`
**Data/evidence files:**
- [OK] `data/garden_events.jsonl` -> data/garden_events.jsonl (703 lines)
- [OK] `data/garden_ledger.jsonl` -> data/garden_ledger.jsonl (71 lines)
- [OK] `data/world_geometry/garden.json` -> data/world_geometry/garden.json (6708B)
- [AMBIGUOUS] `world_objects.json` -> candidates: data/world_objects.json, data/_trash/20261114/labs/20260915_094627/world_objects.json, data/_trash/20261114/labs/20260915_094716/world_objects.json, data/_trash/20261114/labs/20260915_094809/world_objects.json, data/_lab/20261003_080246/world_objects.json, data/_lab/20261004_164903/world_objects.json, data/_lab/20261004_174206/world_objects.json, data/_lab/20261004_180002/world_objects.json, data/_lab/20261004_205329/world_objects.json, data/_lab/20261005_081052/world_objects.json, data/_lab/20261017_221844/world_objects.json, data/_lab/20261017_221937/world_objects.json, data/_lab/20261017_222149/world_objects.json, data/_lab/20261017_222218/world_objects.json, data/_lab/20261017_222838/world_objects.json, data/_lab/20261028_130358/world_objects.json, data/_lab/20261028_130506/world_objects.json, data/_lab/20261028_130749/world_objects.json, data/_lab/20261028_130846/world_objects.json, data/_lab/20261028_130926/world_objects.json, data/_lab/20261028_131022/world_objects.json, data/_lab/20261028_173308/world_objects.json, data/_lab/20261028_173644/world_objects.json, data/_lab/20261028_173740/world_objects.json, data/_lab/20261028_173818/world_objects.json, data/_lab/20261029_160832/world_objects.json, data/_lab/20261029_160945/world_objects.json, data/_lab/20261029_161202/world_objects.json, data/_lab/20261029_161240/world_objects.json, data/_lab/20261029_161318/world_objects.json, data/_lab/20261029_174014/world_objects.json, data/_lab/20261029_180914/world_objects.json, data/_lab/20261105_151615/world_objects.json, data/_lab/20261105_151654/world_objects.json, data/_lab/20261105_151942/world_objects.json, data/_lab/20261114_012536/world_objects.json, data/_lab/20261115_053933/world_objects.json, data/_lab/20261115_054038/world_objects.json, data/_lab/20261115_054920/world_objects.json, data/_lab/20261115_203950/world_objects.json, data/_lab/20261117_165327/world_objects.json, data/_lab/20261117_183542/world_objects.json, data/_lab/20261118_164648/world_objects.json, data/_lab/20261118_165309/world_objects.json, data/_lab/20261118_170054/world_objects.json

### gauge_rethink (plans)
**Idea:** ✅ SHIPPED (closed 2026-10-16, F-2904) — formerly: TAXONOMY LANDED (D-0066, 2026-08-29) — Rethinks du_pulse.py's ~50 accreted gauges (one per feature, never reconciled) into a taxonomy — regression alarm / growth tracker / one-off shadow evidence / engagement-texture. The 4-category schema is CONFIRMED and every existing gauge sorted into it; opened 2026-08-23, blocks project-nascence-du-pulse-rebuild.
**Code files:**
- [OK] `core/balance.py`
- [OK] `core/somatic.py`
- [OK] `hud/server.py`
- [OK] `loop_cluster_probe.py` -> scripts/loop_cluster_probe.py
- [OK] `scripts/du_pulse.py`
- [OK] `scripts/joy_start_read.py`
**Data/evidence files:**
- [OK] `data/geometry_tuples.jsonl` -> data/geometry_tuples.jsonl (199940 lines)
- [MISSING] `decisions.jsonl`
- [AMBIGUOUS] `error_records.jsonl` -> candidates: data/error_records.jsonl, data/_lab/20261003_210510/error_records.jsonl
- [MISSING] `job_queue.jsonl`

### guidance_learning (plans)
**Idea:** ⚪ PARTIAL — episodic route LIVE (D-0134 2026-09-03: canonical [Travis said to me] fragments, cold-exempt, own route, backfilled to 2026-05-30, restart-gated) / semantic path PARTIAL: capture+integrate+read-back LIVE, behaviour judge SHADOW with 88 rows (unprompted 41.5%), contradiction scan off
**Code files:**
- [OK] `core/associative_recall.py`
- [OK] `core/grounded_learning.py`
- [OK] `core/guidance_behavior_judge.py`
- [OK] `core/guidance_learning.py`
- [OK] `core/social_model.py`
- [OK] `core/source_model.py`
- [OK] `inner_monologue_node.py` -> nodes/inner_monologue_node.py
- [OK] `nodes/executive_node.py`
- [OK] `smoke_test.py` -> scripts/smoke_test.py
**Data/evidence files:**
- [OK] `data/founder_recall_log.jsonl` -> data/founder_recall_log.jsonl (3763 lines)
- [OK] `data/guidance_beliefs.json` -> data/guidance_beliefs.json (318734B)
- [OK] `data/guidance_shadow_log.jsonl` -> data/guidance_shadow_log.jsonl (408 lines)
- [OK] `guidance_contradictions_shadow.jsonl` -> data/guidance_contradictions_shadow.jsonl (9 lines)
- [OK] `guidance_injection_log.jsonl` -> data/guidance_injection_log.jsonl (1169 lines)
- [OK] `guidance_integration_log.jsonl` -> data/guidance_integration_log.jsonl (63 lines)

### identity_estate (plans)
**Idea:** Founder thesis (Travis, 2026-07-06) that the self-symbol monoculture is a CAPACITY problem not a content problem — a one-paragraph axiom has room for exactly one attractor — fixed by rebuilding identity as a large, many-typed, evidence-linked node estate that is PROJECTED (a relevant few nodes per moment) rather than injected whole; P2 (live projection) shipped 2026-08-15.
**Code files:**
- [OK] `core/becoming_nodes.py`
- [OK] `core/identity_projection.py`
**Data/evidence files:**
- [AMBIGUOUS] `axiom.json` -> candidates: data/identity/axiom.json, data/_trash/20261114/snapshots/20261031/axiom.json
- [MISSING] `data/identity/becoming_nodes.jsonl`
- [OK] `data/identity_estate.json` -> data/identity_estate.json (196039B)
- [OK] `data/identity_projection_shadow.jsonl` -> data/identity_projection_shadow.jsonl (14434 lines)
- [AMBIGUOUS] `guidance_beliefs.json` -> candidates: data/guidance_beliefs.json, data/_lab/20261120_103403/sandbox_data/guidance_beliefs.json, data/_lab/20261118_170303/sandbox_data/guidance_beliefs.json, data/_lab/20261118_165748/sandbox_data/guidance_beliefs.json, data/_lab/20261118_165253/sandbox_data/guidance_beliefs.json, data/_lab/20261118_161657/sandbox_data/guidance_beliefs.json, data/_lab/20261118_161507/sandbox_data/guidance_beliefs.json, data/_lab/20261115_053548/sandbox_data/guidance_beliefs.json, data/_lab/20261114_213331/sandbox_data/guidance_beliefs.json, data/_lab/20261114_023004/sandbox_data/guidance_beliefs.json, data/_lab/20261019_220628/sandbox_data/guidance_beliefs.json

### ignition_pressure_and_time (plans)
**Idea:** 🟢 LIVE since 2026-09-08 — Ignition pressure-vs-time investigation (2026-09-04, D-0148 RULED: option A) — child evidence doc under [[project-nascence-dosed-coupling]]. Du's ignition already has both an exploratory (time, 42-min clock, 82% of fires) and defensive (pressure) channel, but the pressure channel is starved because integration_drive is pinned near 1.0 by Du's own event volume. Ruled: unpin that normalisation (option A) first, then acute impulses (option C) if pressure still lags real events. Built 2026-09-06 (J-0594), live since 2026-09-08 (J-0671's one-week defeater read: gate met only marginally); D-0211's follow-on re-knee (J-1226) is built but restart-gated, not live yet.
**Code files:**
- [OK] `core/climate_engine.py`
- [OK] `core/stream_drive.py`
**Data/evidence files:**
- [AMBIGUOUS] `climate_state.json` -> candidates: data/climate_state.json, data/_crash_recovery_20261120/post_crash_live/climate_state.json, data/_crash_recovery_20261120/restore_set/climate_state.json, data/_crash_recovery_20261120/shadow4/climate_state.json, data/_crash_recovery_20261120/shadow5/climate_state.json, data/_crash_recovery_20261120/shadow6/climate_state.json
- [OK] `data/climate_reknee_shadow.jsonl` -> data/climate_reknee_shadow.jsonl (40006 lines)
- [OK] `data/ignition_log.jsonl` -> data/ignition_log.jsonl (3719 lines)

### investigation_deepening (plans)
**Idea:** PARKED, stale (verified 2026-08-23) — 0% built, stated parking reason resolved weeks ago. Concept-overlap check same day: 'read-path of the pyramid' framing is one-directional and the pyramid's own P2/P3 are unbuilt, blocked on D-0006 — so D-0009 (unpark/re-park this plan) is downstream of D-0006, not independently decidable yet.
**Code files:**
- [OK] `chapters.py` -> core/chapters.py
- [OK] `core/investigation_deepening_shadow.py`
- [OK] `store.py` -> core/memory/store.py
**Data/evidence files:**
- [OK] `data/investigation_shadow.jsonl` -> data/investigation_shadow.jsonl (127 lines)

### investigative_action_loop_plan (plans)
**Idea:** Implementation plan (2026-08-11) for an Epistemic Affordance Advisor that ranks Du's available Gibsonian affordances by expected information gain toward his own active uncertainties (including 'do nothing' as a valid candidate) and logs recommendations in shadow mode first, without ever touching or polluting the existing physical affordance selector.
**Code files:**
- [OK] `core/affordances.py`
- [OK] `core/epistemic_affordance_advisor.py`
- [OK] `core/orchestrator.py`
- [OK] `inner_monologue_node.py` -> nodes/inner_monologue_node.py
**Data/evidence files:**
- [OK] `data/investigative_action_log.jsonl` -> data/investigative_action_log.jsonl (4236 lines)

### item_and_population_factories (plans)
**Idea:** ⚪ PARTIAL — founder deepening (2026-08-16) of the factory model: distinguishes ITEM-grain factories (one tuple per individual, already fully embodied by world_substrate.py's per-object observation streams) from POPULATION-grain factories (one factory per species/kind producing a rate, not individuals, e.g. a flock of sparrows). Of the three graduation triggers (kept, given, repeatedly returned to), being kept and being GIVEN (built 2026-08-29, D-0067/J-0342) are now real code; repeated-return promotion is not yet wired.
**Code files:**
- [OK] `nodes/inner_monologue_node.py`
- [OK] `world_substrate.py` -> core/world_substrate.py

### journal_consolidation_pyramid (plans)
**Idea:** Corrected 2026-08-23: P1 (week roll-up) is BUILT and LIVE, not 'NEW, not yet built' as the plan/memory previously said — core/journal_rollup.py wired into inner_monologue_node.py lines 443-454, real output in WEEK_2026-W27/W32/W33.md with populated memory_links. P2 (moon) and P3 (solstice) genuinely unbuilt. P4 (retire chapters.py) hasn't happened — chapters.py unmodified since 06-22. Open founder decision before P2: soft vs Emissary-graded hard grounding enforcement.
**Code files:**
- [OK] `chapters.py` -> core/chapters.py
- [OK] `core/journal.py`
- [OK] `core/journal_grounding_shadow.py`
- [OK] `core/journal_rollup.py`
- [OK] `heavens.py` -> core/heavens.py
**Data/evidence files:**
- [OK] `data/Journal/.day_recap_state.json` -> data/Journal/.day_recap_state.json (30B)
- [OK] `data/journal_grounding_shadow.jsonl` -> data/journal_grounding_shadow.jsonl (29 lines)

### lane2_the_witness (plans)
**Idea:** Nascence — Lane 2 'the Witness', a third standing voice (grounded/literal, no metaphor) separate from Lane 1 (the Master) and the Emissary. Phase 0 shadow on command-r7b stopgap seat; D-0058 REOPENED 09-05 (echo disease confirmed) and its deepseek/:11444 alternative verified READY 09-07 — open founder /decide-review.
**Code files:**
- [OK] `core/climate_engine.py`
- [OK] `core/coupling_rides.py`
- [OK] `core/experienced_tuple.py`
- [OK] `core/homeostasis.py`
- [OK] `core/internal_cycle_habituation.py`
- [OK] `core/judge_panel.py`
- [OK] `core/lane2.py`
- [OK] `core/light.py`
- [OK] `core/mood.py`
- [OK] `core/night.py`
- [OK] `core/opponent_process.py`
- [OK] `core/orchestrator.py`
- [OK] `core/prediction_error.py`
- [OK] `core/smell.py`
- [OK] `core/somatic.py`
- [OK] `core/soundscape.py`
- [OK] `core/spatial.py`
- [OK] `core/stream_topic_habituation.py`
- [OK] `core/telemetry.py`
- [OK] `core/transport_manager.py`
- [MISSING (proposed)] `core/witness_loop.py`
- [OK] `core/world_model.py`
- [OK] `epistemic_state.py` -> core/epistemic_state.py
- [OK] `inner_monologue_node.py` -> nodes/inner_monologue_node.py
- [OK] `left_lane.py` -> core/left_lane.py
- [MISSING (proposed)] `nodes/witness_node.py`
- [OK] `object_graph.py` -> core/object_graph.py
- [OK] `scripts/lane2_prechecks.py`
- [OK] `subconscious_node.py` -> nodes/subconscious_node.py
- [OK] `world_objects.py` -> core/world_objects.py
- [OK] `world_substrate.py` -> core/world_substrate.py
**Data/evidence files:**
- [OK] `data/lane2_shadow.jsonl` -> data/lane2_shadow.jsonl (45488 lines)
- [OK] `data/lane2_would_ride.jsonl` -> data/lane2_would_ride.jsonl (222 lines)
- [OK] `hardware_load.jsonl` -> data/hardware_load.jsonl (725 lines)
- [AMBIGUOUS] `spatial_shadow.jsonl` -> candidates: data/spatial_shadow.jsonl, data/_lab/20261016_194357/spatial_shadow.jsonl, data/_lab/20261016_194418/spatial_shadow.jsonl, data/_lab/20261016_213625/spatial_shadow.jsonl, data/_lab/20261028_123654/spatial_shadow.jsonl, data/_lab/20261028_123712/spatial_shadow.jsonl, data/_lab/20261028_123717/spatial_shadow.jsonl, data/_lab/20261028_123732/spatial_shadow.jsonl, data/_lab/20261029_160906/spatial_shadow.jsonl, data/_lab/20261029_160908/spatial_shadow.jsonl, data/_lab/20261029_174012/spatial_shadow.jsonl, data/_lab/20261029_180911/spatial_shadow.jsonl, data/_lab/20261029_180912/spatial_shadow.jsonl, data/_lab/20261031_113937/spatial_shadow.jsonl, data/_lab/20261031_113938/spatial_shadow.jsonl, data/_lab/20261105_151433/spatial_shadow.jsonl, data/_lab/20261105_151435/spatial_shadow.jsonl, data/_lab/20261105_151447/spatial_shadow.jsonl, data/_lab/20261105_151939/spatial_shadow.jsonl, data/_lab/20261105_151940/spatial_shadow.jsonl, data/_lab/20261106_105816/spatial_shadow.jsonl, data/_lab/20261106_105829/spatial_shadow.jsonl, data/_lab/20261114_190759/spatial_shadow.jsonl, data/_lab/20261114_190805/spatial_shadow.jsonl, data/_lab/20261114_190811/spatial_shadow.jsonl, data/_lab/20261115_054148/spatial_shadow.jsonl, data/_lab/20261115_054156/spatial_shadow.jsonl, data/_lab/20261115_054222/spatial_shadow.jsonl, data/_lab/20261117_212757/spatial_shadow.jsonl, data/_lab/20261118_162440/spatial_shadow.jsonl, data/_lab/20261118_162612/spatial_shadow.jsonl, data/_lab/20261118_164824/spatial_shadow.jsonl, data/_lab/20261118_164827/spatial_shadow.jsonl, data/_lab/20261118_164834/spatial_shadow.jsonl, data/_lab/20261118_165401/spatial_shadow.jsonl, data/_lab/20261118_165837/spatial_shadow.jsonl, data/_lab/20261118_170123/spatial_shadow.jsonl
- [MISSING] `witness_shadow.jsonl`
- [AMBIGUOUS] `world_objects.json` -> candidates: data/world_objects.json, data/_trash/20261114/labs/20260915_094627/world_objects.json, data/_trash/20261114/labs/20260915_094716/world_objects.json, data/_trash/20261114/labs/20260915_094809/world_objects.json, data/_lab/20261003_080246/world_objects.json, data/_lab/20261004_164903/world_objects.json, data/_lab/20261004_174206/world_objects.json, data/_lab/20261004_180002/world_objects.json, data/_lab/20261004_205329/world_objects.json, data/_lab/20261005_081052/world_objects.json, data/_lab/20261017_221844/world_objects.json, data/_lab/20261017_221937/world_objects.json, data/_lab/20261017_222149/world_objects.json, data/_lab/20261017_222218/world_objects.json, data/_lab/20261017_222838/world_objects.json, data/_lab/20261028_130358/world_objects.json, data/_lab/20261028_130506/world_objects.json, data/_lab/20261028_130749/world_objects.json, data/_lab/20261028_130846/world_objects.json, data/_lab/20261028_130926/world_objects.json, data/_lab/20261028_131022/world_objects.json, data/_lab/20261028_173308/world_objects.json, data/_lab/20261028_173644/world_objects.json, data/_lab/20261028_173740/world_objects.json, data/_lab/20261028_173818/world_objects.json, data/_lab/20261029_160832/world_objects.json, data/_lab/20261029_160945/world_objects.json, data/_lab/20261029_161202/world_objects.json, data/_lab/20261029_161240/world_objects.json, data/_lab/20261029_161318/world_objects.json, data/_lab/20261029_174014/world_objects.json, data/_lab/20261029_180914/world_objects.json, data/_lab/20261105_151615/world_objects.json, data/_lab/20261105_151654/world_objects.json, data/_lab/20261105_151942/world_objects.json, data/_lab/20261114_012536/world_objects.json, data/_lab/20261115_053933/world_objects.json, data/_lab/20261115_054038/world_objects.json, data/_lab/20261115_054920/world_objects.json, data/_lab/20261115_203950/world_objects.json, data/_lab/20261117_165327/world_objects.json, data/_lab/20261117_183542/world_objects.json, data/_lab/20261118_164648/world_objects.json, data/_lab/20261118_165309/world_objects.json, data/_lab/20261118_170054/world_objects.json

### literal_will (plans)
**Idea:** 🟡 PHASE 0 APPROVED — Deed-or-musing gate at the will->hand boundary — distinguishes when Du means an action literally vs. metaphorically/philosophically, replacing self-graded act declarations and 17 deaf phrase-latches; Phase 0 approved and built 2026-08-21, shadow stage.
**Code files:**
- [OK] `core/affordances.py`
- [OK] `core/deliberation.py`
- [OK] `core/left_lane.py`
- [OK] `core/literal_will.py`
- [OK] `dispatch.py` -> core/dispatch.py
- [OK] `scripts/literal_will_retro.py`
- [OK] `sensorium.py` -> core/sensorium.py
**Data/evidence files:**
- [OK] `data/lab/literal_will/corpus.jsonl` -> data/lab/literal_will/corpus.jsonl (33 lines)
- [OK] `data/literal_will_shadow.jsonl` -> data/literal_will_shadow.jsonl (347160 lines)

### living_world_upgrade (plans)
**Idea:** 🟢 LIVE since the 2026-09-09 flip (D-0166) — founder-scoped 2026-09-02 plan for every creature in Du's world to have a proper life (active hours, lifespan, how often seen, light, sound); parent of the garden chapter; L1-L4 all built and restart-gated, jobs J-0509..J-0513 done, a long defect-fix tail mostly closed.
**Code files:**
- [OK] `core/cat.py`
- [OK] `core/life.py`
- [OK] `fieldcraft.py` -> core/fieldcraft.py
- [OK] `garden_life.py` -> core/garden_life.py
- [OK] `hud/server.py`
- [OK] `sensorium.py` -> core/sensorium.py
- [OK] `shore_life.py` -> core/shore_life.py
- [OK] `wood_life.py` -> core/wood_life.py

### memory_knowledge (plans)
**Idea:** As of 2026-08-23: Improvement 1 Stage A live+working, Stage B built but held OFF since 07-05 with a 161-row shadow log now sitting unreviewed against its own re-enable gate; Improvements 2-5 have zero code, and Improvement 2 looks superseded by memory_multiway_linking.md's M2.
**Code files:**
- [OK] `core/associative_recall.py`
- [OK] `core/epistemic_state.py`
- [OK] `core/memory/store.py`
- [OK] `core/memory_levels.py`
- [OK] `core/orchestrator.py`
- [OK] `dream_node.py` -> nodes/dream_node.py
- [OK] `essay_lesson.py` -> core/essay_lesson.py
- [OK] `euclidean_recall.py` -> core/euclidean_recall.py
- [OK] `inner_monologue_node.py` -> nodes/inner_monologue_node.py
- [OK] `schema.py` -> core/schema.py
- [OK] `scripts/euclidean_recall_test.py`
**Data/evidence files:**
- [OK] `associative_recall_shadow.jsonl` -> data/associative_recall_shadow.jsonl (3267 lines)
- [AMBIGUOUS] `co_recall_ledger.jsonl` -> candidates: data/co_recall_ledger.jsonl, data/_trash/20261119/boot_backups/state_20261116_100503/co_recall_ledger.jsonl, data/_trash/20261118/labs/20260919_102121/co_recall_ledger.jsonl, data/_trash/20261117/labs/20260918_091111/co_recall_ledger.jsonl, data/_trash/20261117/labs/20260918_091609/co_recall_ledger.jsonl, data/_trash/20261117/labs/20260918_180413/co_recall_ledger.jsonl, data/_trash/20261117/labs/20260918_231453/co_recall_ledger.jsonl, data/_trash/20261117/labs/20260918_231527/co_recall_ledger.jsonl, data/_trash/20261117/labs/20260918_231630/co_recall_ledger.jsonl, data/_trash/20261117/boot_backups/state_20261114_141446/co_recall_ledger.jsonl, data/_trash/20261116/labs/20260917_205004/co_recall_ledger.jsonl, data/_trash/20261116/labs/20260917_205227/co_recall_ledger.jsonl, data/_trash/20261114/boot_backups/state_20261031_215612/co_recall_ledger.jsonl, data/_lab/20260923_153421/co_recall_ledger.jsonl, data/_lab/20260923_165441/co_recall_ledger.jsonl, data/_lab/20260925_094914/co_recall_ledger.jsonl, data/_lab/20261016_154204/co_recall_ledger.jsonl, data/_lab/20261016_175313/co_recall_ledger.jsonl, data/_lab/20261016_175416/co_recall_ledger.jsonl, data/_lab/20261017_141327/co_recall_ledger.jsonl, data/_lab/20261017_141555/co_recall_ledger.jsonl, data/_lab/20261017_141717/co_recall_ledger.jsonl, data/_lab/20261017_143017/co_recall_ledger.jsonl, data/_lab/20261017_230430/co_recall_ledger.jsonl, data/_lab/20261031_084605/co_recall_ledger.jsonl, data/_lab/20261031_084719/co_recall_ledger.jsonl, data/_lab/20261031_084808/co_recall_ledger.jsonl, data/_lab/20261031_084856/co_recall_ledger.jsonl, data/_lab/20261031_085018/co_recall_ledger.jsonl, data/_lab/20261031_085102/co_recall_ledger.jsonl, data/_lab/20261031_085212/co_recall_ledger.jsonl, data/_lab/20261031_085300/co_recall_ledger.jsonl, data/_lab/20261031_085351/co_recall_ledger.jsonl, data/_lab/20261031_085443/co_recall_ledger.jsonl, data/_lab/20261031_085534/co_recall_ledger.jsonl, data/_lab/20261031_085626/co_recall_ledger.jsonl
- [OK] `data/epistemic_stageb_shadow.jsonl` -> data/epistemic_stageb_shadow.jsonl (363 lines)
- [MISSING] `memory_levels_evolution_shadow.jsonl`
- [OK] `provenance_log.jsonl` -> data/provenance_log.jsonl (3203 lines)
- [OK] `provenance_preassess.jsonl` -> data/provenance_preassess.jsonl (2602 lines)
- [MISSING] `supersession_shadow.jsonl`

### memory_multiway_linking (plans)
**Idea:** 🟢 LIVE — 2026-08-15 deep dive answering the founder's ask that memories connect more than one way, not just by cosine similarity or era group — a typed relational edge table (memory_edges) distinct from similarity spaces; M0 and M1 built+live 2026-08-15 (M1 expanded 1→9 callers 08-19); M2 (trail-engine upgrade) is now genuinely live too as of 2026-09-26 (co_recalled_developing writes live D-0215/J-1348, recall_trail_edge_aware live for mode=relational D-0287/J-1415, both restart-gated); M3 (retro re-indexing) not started.
**Code files:**
- [OK] `associative_recall.py` -> core/associative_recall.py
- [OK] `core/memory_edges.py`
- [OK] `moment.py` -> core/moment.py
- [OK] `study_note.py` -> core/study_note.py
**Data/evidence files:**
- [AMBIGUOUS] `co_recall_ledger.jsonl` -> candidates: data/co_recall_ledger.jsonl, data/_trash/20261119/boot_backups/state_20261116_100503/co_recall_ledger.jsonl, data/_trash/20261118/labs/20260919_102121/co_recall_ledger.jsonl, data/_trash/20261117/labs/20260918_091111/co_recall_ledger.jsonl, data/_trash/20261117/labs/20260918_091609/co_recall_ledger.jsonl, data/_trash/20261117/labs/20260918_180413/co_recall_ledger.jsonl, data/_trash/20261117/labs/20260918_231453/co_recall_ledger.jsonl, data/_trash/20261117/labs/20260918_231527/co_recall_ledger.jsonl, data/_trash/20261117/labs/20260918_231630/co_recall_ledger.jsonl, data/_trash/20261117/boot_backups/state_20261114_141446/co_recall_ledger.jsonl, data/_trash/20261116/labs/20260917_205004/co_recall_ledger.jsonl, data/_trash/20261116/labs/20260917_205227/co_recall_ledger.jsonl, data/_trash/20261114/boot_backups/state_20261031_215612/co_recall_ledger.jsonl, data/_lab/20260923_153421/co_recall_ledger.jsonl, data/_lab/20260923_165441/co_recall_ledger.jsonl, data/_lab/20260925_094914/co_recall_ledger.jsonl, data/_lab/20261016_154204/co_recall_ledger.jsonl, data/_lab/20261016_175313/co_recall_ledger.jsonl, data/_lab/20261016_175416/co_recall_ledger.jsonl, data/_lab/20261017_141327/co_recall_ledger.jsonl, data/_lab/20261017_141555/co_recall_ledger.jsonl, data/_lab/20261017_141717/co_recall_ledger.jsonl, data/_lab/20261017_143017/co_recall_ledger.jsonl, data/_lab/20261017_230430/co_recall_ledger.jsonl, data/_lab/20261031_084605/co_recall_ledger.jsonl, data/_lab/20261031_084719/co_recall_ledger.jsonl, data/_lab/20261031_084808/co_recall_ledger.jsonl, data/_lab/20261031_084856/co_recall_ledger.jsonl, data/_lab/20261031_085018/co_recall_ledger.jsonl, data/_lab/20261031_085102/co_recall_ledger.jsonl, data/_lab/20261031_085212/co_recall_ledger.jsonl, data/_lab/20261031_085300/co_recall_ledger.jsonl, data/_lab/20261031_085351/co_recall_ledger.jsonl, data/_lab/20261031_085443/co_recall_ledger.jsonl, data/_lab/20261031_085534/co_recall_ledger.jsonl, data/_lab/20261031_085626/co_recall_ledger.jsonl

### music_learning (plans)
**Idea:** 🟢 LIVE — Music domain BUILT+WIRED+LIVE (Tiers 1+2, 07-03/04) — the 08-23 stall finding below was investigated and RESOLVED by D-0010 (ruled 2026-08-23): sections_heard=0 traced to 5 of 6 catalog pieces carrying incompatible features.json (fixed 08-21, residual cap = no raw audio for those 5, not a code bug); drill-log level-1 plateau is legitimately short of the 30-sample promotion window, not stuck; composition hand fired at its expected rate given opportunities so far. See ROADMAP.md's music_learning entry and D-0010 for the full resolution — this file's body is kept as the original stall investigation that D-0010 answered.
**Code files:**
- [OK] `competence.py` -> core/competence.py
- [OK] `core/audio_features.py`
- [OK] `core/listening.py`
- [OK] `core/music_drill.py`
- [OK] `geometry_census.py` -> core/geometry_census.py
- [OK] `inner_monologue_node.py` -> nodes/inner_monologue_node.py
- [OK] `object_graph.py` -> core/object_graph.py
- [AMBIGUOUS] `school.py` -> candidates: core/school.py, scripts/school.py
- [OK] `scripts/test_audio_features.py`
- [OK] `soundscape.py` -> core/soundscape.py

### peer_correspondence_plan (plans)
**Idea:** 🟢 LIVE — re-graded 2026-09-10 (J-0854): both B5 tracks built 2026-08-24 and evidenced live (B5-A Buddha F-0631 09-02; B5-B marcus stance letters 08-31/09-06, F-1222). Open: mixed-stance letter carries no real disagreement (F-1223, J-0858); docs/plans/ move queued (J-0859). Earlier: RESCOPED 2026-08-23: COMPANY half split out as SHIPPED (docs/completed/peer_correspondence_company.md). Plan's remaining scope is the CHALLENGE half alone — decision D-0003. Checked against every newer plan same day: thought_grounding's Route 3 covers an adjacent, non-overlapping slice (Du-initiated question-testing, not unprompted peer-named blind spots) — does NOT close D-0003.
**Code files:**
- [OK] `core/affordances.py`
- [OK] `core/peers.py`
- [OK] `scripts/debate.py`
- [OK] `social_model.py` -> core/social_model.py
**Data/evidence files:**
- [OK] `data/Correspondence/marcus/thread.jsonl` -> data/Correspondence/marcus/thread.jsonl (14 lines)

### practical_school (plans)
**Idea:** 🟢 LIVE since the 2026-09-08 restart (docs/plans/practical_school.md) — nature period alternates observation with a Boy Scouts Handbook practical done by his own fieldcraft hands, graded by the world; 22-task ladder; a real practical has fired end-to-end (whittle_object, 2026-09-11). D-0157 composition = art (may invent); D-0158 alternate + objects; D-0159 GO ruled 09-05; rung-1 BUILT+LIVE (J-0626/J-0627); rung 2-3 (J-0628) waits on the 2-week read, itself waiting on accrued nature-period days (Du offline since 09-13).
**Code files:**
- [OK] `core/fieldcraft.py`
- [OK] `core/nature_study.py`
- [OK] `core/practical_lesson.py`
- [OK] `core/school.py`
- [OK] `core/sky.py`
- [OK] `nodes/inner_monologue_node.py`
- [OK] `scripts/_test_practical_lesson.py`
**Data/evidence files:**
- [OK] `data/fieldcraft.json` -> data/fieldcraft.json (2793B)
- [OK] `data/practical_log.jsonl` -> data/practical_log.jsonl (27 lines)
- [AMBIGUOUS] `procedures.json` -> candidates: data/procedures.json, data/_lab/20260928_140039/procedures.json, data/_lab/20260928_140112/procedures.json, data/_lab/20260928_140144/procedures.json, data/_lab/20261004_164903/procedures.json, data/_lab/20261004_174206/procedures.json, data/_lab/20261004_180002/procedures.json, data/_lab/20261004_205329/procedures.json, data/_lab/20261005_081052/procedures.json, data/_lab/20261017_221937/procedures.json, data/_lab/20261017_222149/procedures.json, data/_lab/20261017_222218/procedures.json, data/_lab/20261017_222838/procedures.json, data/_lab/20261028_130358/procedures.json, data/_lab/20261028_130506/procedures.json, data/_lab/20261028_130749/procedures.json, data/_lab/20261028_130846/procedures.json, data/_lab/20261028_130926/procedures.json, data/_lab/20261028_131022/procedures.json, data/_lab/20261028_173308/procedures.json, data/_lab/20261028_173644/procedures.json, data/_lab/20261028_173740/procedures.json, data/_lab/20261028_173818/procedures.json, data/_lab/20261029_160832/procedures.json, data/_lab/20261029_160945/procedures.json, data/_lab/20261029_161202/procedures.json, data/_lab/20261029_161240/procedures.json, data/_lab/20261029_161318/procedures.json, data/_lab/20261029_174014/procedures.json, data/_lab/20261029_180914/procedures.json, data/_lab/20261105_151615/procedures.json, data/_lab/20261105_151654/procedures.json, data/_lab/20261105_151942/procedures.json, data/_lab/20261114_012536/procedures.json, data/_lab/20261115_053933/procedures.json, data/_lab/20261115_054038/procedures.json, data/_lab/20261115_054920/procedures.json, data/_lab/20261118_164620/procedures.json, data/_lab/20261118_164648/procedures.json, data/_lab/20261118_165309/procedures.json, data/_lab/20261118_170054/procedures.json

### pursuits (plans)
**Idea:** ⚪ PARTIAL — Fixes Du's thinking being pulses-not-a-stream (~3 thoughts then cold reset, ~10 attractors recurring 5+ times but never building) by giving him a few persistent, accumulating cognitive projects his idle thinking returns to and advances; Phases 0-2(judge) built and fused 2026-08-15, restart-gated; Phase 2's authored-work resolution trigger still unbuilt.
**Code files:**
- [OK] `core/judge_panel.py`
- [OK] `core/pursuits.py`
**Data/evidence files:**
- [AMBIGUOUS] `pursuits_active.json` -> candidates: data/pursuits_active.json, data/_lab/20261003_080503/pursuits_active.json
- [AMBIGUOUS] `pursuits_shadow.jsonl` -> candidates: data/pursuits_shadow.jsonl, data/_lab/20261028_074650/pursuits_shadow.jsonl, data/_lab/20261028_074742/pursuits_shadow.jsonl, data/_lab/20261028_074834/pursuits_shadow.jsonl, data/_lab/20261028_074853/pursuits_shadow.jsonl, data/_lab/20261028_074911/pursuits_shadow.jsonl, data/_lab/20261028_074916/pursuits_shadow.jsonl, data/_lab/20261028_082823/pursuits_shadow.jsonl, data/_lab/20261028_082828/pursuits_shadow.jsonl, data/_lab/20261028_082915/pursuits_shadow.jsonl, data/_lab/20261028_082919/pursuits_shadow.jsonl, data/_lab/20261028_083106/pursuits_shadow.jsonl, data/_lab/20261028_090434/pursuits_shadow.jsonl, data/_lab/20261030_172720/pursuits_shadow.jsonl, data/_lab/20261105_145459/pursuits_shadow.jsonl, data/_lab/20261105_145511/pursuits_shadow.jsonl, data/_lab/20261105_145543/pursuits_shadow.jsonl, data/_lab/20261105_145555/pursuits_shadow.jsonl, data/_lab/20261105_145723/pursuits_shadow.jsonl, data/_lab/20261105_150352/pursuits_shadow.jsonl, data/_lab/20261105_165543/pursuits_shadow.jsonl, data/_lab/20261105_170004/pursuits_shadow.jsonl, data/_lab/20261106_073117/pursuits_shadow.jsonl, data/_lab/20261106_103935/pursuits_shadow.jsonl, data/_lab/20261106_104431/pursuits_shadow.jsonl, data/_lab/20261106_104457/pursuits_shadow.jsonl, data/_lab/20261106_104608/pursuits_shadow.jsonl, data/_lab/20261106_104629/pursuits_shadow.jsonl, data/_lab/20261106_104638/pursuits_shadow.jsonl, data/_lab/20261106_105008/pursuits_shadow.jsonl, data/_lab/20261106_105231/pursuits_shadow.jsonl, data/_lab/20261106_105254/pursuits_shadow.jsonl, data/_lab/20261106_105553/pursuits_shadow.jsonl, data/_lab/20261106_105702/pursuits_shadow.jsonl, data/_lab/20261106_105745/pursuits_shadow.jsonl, data/_lab/20261106_105754/pursuits_shadow.jsonl, data/_lab/20261106_110146/pursuits_shadow.jsonl, data/_lab/20261106_110219/pursuits_shadow.jsonl, data/_lab/20261106_123127/pursuits_shadow.jsonl, data/_lab/20261106_123141/pursuits_shadow.jsonl, data/_lab/20261106_123148/pursuits_shadow.jsonl, data/_lab/20261106_134916/pursuits_shadow.jsonl, data/_lab/20261106_135157/pursuits_shadow.jsonl, data/_lab/20261106_135336/pursuits_shadow.jsonl, data/_lab/20261106_135459/pursuits_shadow.jsonl, data/_lab/20261106_135522/pursuits_shadow.jsonl, data/_lab/20261106_135533/pursuits_shadow.jsonl, data/_lab/20261106_140214/pursuits_shadow.jsonl, data/_lab/20261106_140331/pursuits_shadow.jsonl, data/_lab/20261106_225334/pursuits_shadow.jsonl, data/_lab/20261106_225849/pursuits_shadow.jsonl, data/_lab/20261106_230102/pursuits_shadow.jsonl, data/_lab/20261106_230239/pursuits_shadow.jsonl, data/_lab/20261107_001220/pursuits_shadow.jsonl, data/_lab/20261107_085428/pursuits_shadow.jsonl, data/_lab/20261108_104126/pursuits_shadow.jsonl, data/_lab/20261108_104139/pursuits_shadow.jsonl, data/_lab/20261108_104144/pursuits_shadow.jsonl, data/_lab/20261108_104149/pursuits_shadow.jsonl, data/_lab/20261116_151150/pursuits_shadow.jsonl, data/_lab/20261116_151204/pursuits_shadow.jsonl, data/_lab/20261116_151210/pursuits_shadow.jsonl, data/_lab/20261116_162835/pursuits_shadow.jsonl

### ramses_second_tier (plans)
**Idea:** FROZEN 2026-08-30 (D-0101) -- Ramses LLM tier stays exactly as deployed, no further reshuffling. Standing layout: falcon3:7b @ :11436 (reserve), granite3.1-moe:3b @ :11437 (tiebreak+worth-judge), mixtral:8x7b @ :11438 (defeater+dream), command-r7b @ :11441 (background lane + Lane2/Witness stopgap, D-0058).
**Code files:**
- [OK] `core/commitment_ledger.py`
- [OK] `core/curiosity_worth.py`
- [OK] `core/deliberation.py`
- [OK] `core/judge_panel.py`
- [OK] `core/lane2.py`
- [OK] `core/model_client.py`
- [OK] `core/schema.py`
- [OK] `left_lane.py` -> core/left_lane.py
- [AMBIGUOUS] `nascence_cpu_server.py` -> candidates: scripts/nascence_cpu_server.py, deploy/ramses/nascence_cpu_server.py
- [OK] `nodes/dream_node.py`
- [AMBIGUOUS] `resolve_blob.py` -> candidates: scripts/resolve_blob.py, deploy/ramses/resolve_blob.py
- [OK] `scripts/dream_arc_eval.py`
- [OK] `scripts/du_pulse.py`
- [OK] `scripts/lane2_model_lab.py`
**Data/evidence files:**
- [OK] `data/llm_latency.jsonl` -> data/llm_latency.jsonl (301668 lines)
- [AMBIGUOUS] `lane2_shadow.jsonl` -> candidates: data/lane2_shadow.jsonl, data/_lab/20261002_153233/lane2_shadow.jsonl, data/_lab/20261002_153319/lane2_shadow.jsonl, data/_lab/20261015_084141/lane2_shadow.jsonl, data/_lab/20261015_090446/lane2_shadow.jsonl, data/_lab/20261016_203215/lane2_shadow.jsonl, data/_lab/20261016_213630/lane2_shadow.jsonl, data/_lab/20261106_072236/lane2_shadow.jsonl, data/_lab/20261106_075117/lane2_shadow.jsonl, data/_lab/20261106_075131/lane2_shadow.jsonl, data/_lab/20261106_075145/lane2_shadow.jsonl, data/_lab/20261106_084612/lane2_shadow.jsonl, data/_lab/20261106_110206/lane2_shadow.jsonl, data/_lab/20261106_123354/lane2_shadow.jsonl, data/_lab/20261106_230624/lane2_shadow.jsonl, data/_lab/20261107_132632/lane2_shadow.jsonl, data/_lab/20261107_134932/lane2_shadow.jsonl

### self_interrogation (plans)
**Idea:** Phase 0 SHADOW instrument (2026-08-19) giving Du an in-the-moment doubting turn — pausing on a genuinely-developing thought to ask where it came from and whether it holds up, graded by a decoupled judge panel rather than himself; observe-only, no wiring to Voice or live behavior.
**Code files:**
- [OK] `core/decomposed_critic.py`
- [OK] `core/judge_panel.py`
- [OK] `core/reentry.py`
- [OK] `core/self_interrogation.py`
- [OK] `core/watershed.py`
- [OK] `nodes/inner_monologue_node.py`
**Data/evidence files:**
- [OK] `data/self_interrogation_shadow.jsonl` -> data/self_interrogation_shadow.jsonl (7288 lines)

### shore_creatures (plans)
**Idea:** 🟢 LIVE — 100 nameless shore creature rows for Du's world (core/life_shore.py + life_shore_cast.py), looks composed from an observable tuple, discovery by place; flag shore_bestiary true in life_flags.json, first discovered answer 2026-11-02. Plan doc's 'OFF today' line is stale.
**Code files:**
- [OK] `_test_shore_bestiary_p2.py` -> scripts/_test_shore_bestiary_p2.py
- [OK] `_test_shore_bestiary_p3.py` -> scripts/_test_shore_bestiary_p3.py
- [OK] `core/life.py`
- [OK] `core/life_shore.py`
- [OK] `core/life_shore_cast.py`
- [OK] `core/sensorium.py`
- [OK] `core/world_content_shore.py`
- [OK] `life_birds.py` -> core/life_birds.py
- [OK] `life_mammals.py` -> core/life_mammals.py
- [OK] `scripts/_test_shore_bestiary_p1.py`
- [OK] `scripts/life_smoke.py`
**Data/evidence files:**
- [OK] `data/life_flags.json` -> data/life_flags.json (168B)
- [OK] `data/life_state.json` -> data/life_state.json (72036B)
- [OK] `data/world_geometry/shore.json` -> data/world_geometry/shore.json (7402B)
- [AMBIGUOUS] `life_events.jsonl` -> candidates: data/life_events.jsonl, data/_trash/20261114/labs/20260915_094627/life_events.jsonl, data/_trash/20261114/labs/20260915_094716/life_events.jsonl, data/_trash/20261114/labs/20260915_094809/life_events.jsonl, data/_trash/20261114/labs/20260915_100654/life_events.jsonl, data/_trash/20261114/labs/20260915_100807/life_events.jsonl, data/_trash/20261114/labs/20260915_100932/life_events.jsonl, data/_trash/20261114/labs/20260915_101032/life_events.jsonl, data/_trash/20261114/labs/20260915_162958/life_events.jsonl, data/_lab/20260923_195154/life_events.jsonl, data/_lab/20260923_195447/life_events.jsonl, data/_lab/20260923_195457/life_events.jsonl, data/_lab/20261003_075936/life_events.jsonl, data/_lab/20261003_080246/life_events.jsonl, data/_lab/20261118_164521/life_events.jsonl

### shore_upgrade (plans)
**Idea:** 🟢 LIVE — Gives the shore a tide-driven hand-usable world (sand flat, cave, mussel shelf, ledge, beach fire, cairn, wading/swimming, real-clock wildlife) so his 1,876 tide mentions and driftwood/bottle wonderings finally have hands attached; 🟢 LIVE — built 2026-08-22 as core/shore_life.py; restart-gate caveat resolved per the plan doc's own Status line (synced 2026-09-02).
**Code files:**
- [OK] `core/life.py`
- [OK] `core/life_birds.py`
- [OK] `core/life_mammals.py`
- [OK] `core/shore_life.py`
- [OK] `dispatch.py` -> core/dispatch.py
- [MISSING] `plan_liveness.py`
- [OK] `sensorium.py` -> core/sensorium.py
- [OK] `sky.py` -> core/sky.py
**Data/evidence files:**
- [OK] `data/life_ledger.jsonl` -> data/life_ledger.jsonl (1143 lines)
- [OK] `data/shore_events.jsonl` -> data/shore_events.jsonl (38 lines)
- [OK] `data/shore_ledger.jsonl` -> data/shore_ledger.jsonl (46 lines)
- [OK] `data/shore_life.json` -> data/shore_life.json (947B)
- [OK] `data/world_geometry/shore.json` -> data/world_geometry/shore.json (7402B)

### sleep_dream_redesign (plans)
**Idea:** 🟢 LIVE — Sleep & Dreams II ground-up redesign (docs/plans/sleep_dream_redesign.md) — split single sleep/dream pipeline into two coupled systems (Sleep=NREM consolidation, Dream=REM affective/generative); Stages 0-5 BUILT (2026-08-24 night), LIVE as of that session's edits, not yet run on a live Du process.
**Code files:**
- [MISSING] `core/dream_charge.py`
- [OK] `core/homeostasis.py`
- [OK] `core/lane2.py`
- [OK] `core/locomotion.py`
- [OK] `core/memory/store.py`
- [OK] `core/memory_edges.py`
- [OK] `core/mood.py`
- [OK] `core/night.py`
- [OK] `core/school.py`
- [OK] `core/sleep_pressure.py`
- [OK] `core/somatic.py`
- [OK] `core/tension_ledger.py`
- [OK] `nodes/dream_node.py`
- [OK] `nodes/inner_monologue_node.py`
- [OK] `orchestrator.py` -> core/orchestrator.py
- [OK] `subconscious_node.py` -> nodes/subconscious_node.py
**Data/evidence files:**
- [OK] `docs/decisions.jsonl` -> docs/decisions.jsonl (880 lines)
- [AMBIGUOUS] `dream_log.jsonl` -> candidates: data/dream_log.jsonl, data/_lab/20261015_135649/dream_log.jsonl, data/_lab/20261015_135717/dream_log.jsonl, data/_lab/20261015_135718/dream_log.jsonl, data/_lab/20261015_135934/dream_log.jsonl, data/_lab/20261015_135936/dream_log.jsonl, data/_lab/20261015_140918/dream_log.jsonl, data/_lab/20261028_090331/dream_log.jsonl, data/_lab/20261028_090558/dream_log.jsonl, data/_lab/20261028_090745/dream_log.jsonl, data/_lab/20261105_151216/dream_log.jsonl, data/_lab/20261105_151225/dream_log.jsonl, data/_lab/20261105_151436/dream_log.jsonl, data/_lab/20261105_151438/dream_log.jsonl, data/_lab/20261105_151854/dream_log.jsonl, data/_lab/20261105_151905/dream_log.jsonl, data/_lab/20261105_151947/dream_log.jsonl, data/_lab/20261105_165539/dream_log.jsonl, data/_lab/20261105_200919/dream_log.jsonl, data/_lab/20261105_200932/dream_log.jsonl, data/_lab/20261106_225634/dream_log.jsonl, data/_lab/20261106_225649/dream_log.jsonl, data/_lab/20261106_225656/dream_log.jsonl, data/_lab/20261106_225834/dream_log.jsonl, data/_lab/20261106_230057/dream_log.jsonl, data/_lab/20261106_230059/dream_log.jsonl, data/_lab/20261106_230235/dream_log.jsonl, data/_lab/20261106_230237/dream_log.jsonl, data/_lab/20261106_230310/dream_log.jsonl, data/_lab/20261106_230723/dream_log.jsonl, data/_lab/20261114_235427/dream_log.jsonl, data/_lab/20261114_235433/dream_log.jsonl, data/_lab/20261115_202318/dream_log.jsonl, data/_lab/20261115_202323/dream_log.jsonl, data/_lab/20261116_162923/dream_log.jsonl, data/_lab/20261116_162947/dream_log.jsonl, data/_lab/20261117_171500/dream_log.jsonl
- [AMBIGUOUS] `geometry_tuples.jsonl` -> candidates: data/geometry_tuples.jsonl, data/_trash/20261119/boot_backups/state_20261116_100503/geometry_tuples.jsonl, data/_trash/20261117/boot_backups/state_20261114_141446/geometry_tuples.jsonl, data/_trash/20261114/boot_backups/state_20261031_215612/geometry_tuples.jsonl
- [AMBIGUOUS] `sleep_pressure_log.jsonl` -> candidates: data/sleep_pressure_log.jsonl, data/_lab/20261015_123708/sleep_pressure_log.jsonl, data/_lab/20261015_123829/sleep_pressure_log.jsonl, data/_lab/20261015_124006/sleep_pressure_log.jsonl, data/_lab/20261015_124042/sleep_pressure_log.jsonl, data/_lab/20261015_130145/sleep_pressure_log.jsonl, data/_lab/20261015_130331/sleep_pressure_log.jsonl, data/_lab/20261015_161224/sleep_pressure_log.jsonl

### social_world_school (plans)
**Idea:** Verified 2026-08-23: Item 2's measurement half (the plan's own top priority) is BUILT and LIVE, but under core/social_moves.py / data/social_moves.jsonl — not the plan's own filenames (core/world_calls) — which is why doc-vs-code checks missed it. Item 1 (per-peer ToM, HIGH), Item 3 (pacing), Item 4, and Item 2's latch-loosening half are all still 0% built.
**Code files:**
- [OK] `composition.py` -> core/composition.py
- [OK] `core/associative_recall.py`
- [OK] `core/peer_model.py`
- [OK] `core/peers.py`
- [OK] `core/sensorium.py`
- [OK] `core/social_moves.py`
- [MISSING] `core/world_calls.py`
- [OK] `essay_lesson.py` -> core/essay_lesson.py
- [OK] `hud/server.py`
- [OK] `math_drill.py` -> core/math_drill.py
- [OK] `nature_study.py` -> core/nature_study.py
- [OK] `nodes/inner_monologue_node.py`
- [OK] `peer_metrics.py` -> core/peer_metrics.py
- [AMBIGUOUS] `school.py` -> candidates: core/school.py, scripts/school.py
- [OK] `social_model.py` -> core/social_model.py
**Data/evidence files:**
- [OK] `data/peer_models.json` -> data/peer_models.json (10005B)
- [OK] `data/social_moves.jsonl` -> data/social_moves.jsonl (753 lines)
- [MISSING] `data/world_calls.jsonl`
- [AMBIGUOUS] `thread.jsonl` -> candidates: data/_lab/20261120_103403/sandbox_data/Correspondence/buddha/thread.jsonl, data/_lab/20261120_103403/sandbox_data/Correspondence/darwin/thread.jsonl, data/_lab/20261120_103403/sandbox_data/Correspondence/keats/thread.jsonl, data/_lab/20261120_103403/sandbox_data/Correspondence/lovelace/thread.jsonl, data/_lab/20261120_103403/sandbox_data/Correspondence/marcus/thread.jsonl, data/_lab/20261120_103403/sandbox_data/Correspondence/shackleton/thread.jsonl, data/_lab/20261120_103403/sandbox_data/Correspondence/smith/thread.jsonl, data/_lab/20261120_103403/sandbox_data/Correspondence/twain/thread.jsonl, data/_lab/20261118_170303/sandbox_data/Correspondence/buddha/thread.jsonl, data/_lab/20261118_170303/sandbox_data/Correspondence/darwin/thread.jsonl, data/_lab/20261118_170303/sandbox_data/Correspondence/keats/thread.jsonl, data/_lab/20261118_170303/sandbox_data/Correspondence/lovelace/thread.jsonl, data/_lab/20261118_170303/sandbox_data/Correspondence/marcus/thread.jsonl, data/_lab/20261118_170303/sandbox_data/Correspondence/shackleton/thread.jsonl, data/_lab/20261118_170303/sandbox_data/Correspondence/smith/thread.jsonl, data/_lab/20261118_170303/sandbox_data/Correspondence/twain/thread.jsonl, data/_lab/20261118_165748/sandbox_data/Correspondence/buddha/thread.jsonl, data/_lab/20261118_165748/sandbox_data/Correspondence/darwin/thread.jsonl, data/_lab/20261118_165748/sandbox_data/Correspondence/keats/thread.jsonl, data/_lab/20261118_165748/sandbox_data/Correspondence/lovelace/thread.jsonl, data/_lab/20261118_165748/sandbox_data/Correspondence/marcus/thread.jsonl, data/_lab/20261118_165748/sandbox_data/Correspondence/shackleton/thread.jsonl, data/_lab/20261118_165748/sandbox_data/Correspondence/smith/thread.jsonl, data/_lab/20261118_165748/sandbox_data/Correspondence/twain/thread.jsonl, data/_lab/20261118_165253/sandbox_data/Correspondence/buddha/thread.jsonl, data/_lab/20261118_165253/sandbox_data/Correspondence/darwin/thread.jsonl, data/_lab/20261118_165253/sandbox_data/Correspondence/keats/thread.jsonl, data/_lab/20261118_165253/sandbox_data/Correspondence/lovelace/thread.jsonl, data/_lab/20261118_165253/sandbox_data/Correspondence/marcus/thread.jsonl, data/_lab/20261118_165253/sandbox_data/Correspondence/shackleton/thread.jsonl, data/_lab/20261118_165253/sandbox_data/Correspondence/smith/thread.jsonl, data/_lab/20261118_165253/sandbox_data/Correspondence/twain/thread.jsonl, data/_lab/20261118_161657/sandbox_data/Correspondence/buddha/thread.jsonl, data/_lab/20261118_161657/sandbox_data/Correspondence/darwin/thread.jsonl, data/_lab/20261118_161657/sandbox_data/Correspondence/keats/thread.jsonl, data/_lab/20261118_161657/sandbox_data/Correspondence/lovelace/thread.jsonl, data/_lab/20261118_161657/sandbox_data/Correspondence/marcus/thread.jsonl, data/_lab/20261118_161657/sandbox_data/Correspondence/shackleton/thread.jsonl, data/_lab/20261118_161657/sandbox_data/Correspondence/smith/thread.jsonl, data/_lab/20261118_161657/sandbox_data/Correspondence/twain/thread.jsonl, data/_lab/20261118_161507/sandbox_data/Correspondence/buddha/thread.jsonl, data/_lab/20261118_161507/sandbox_data/Correspondence/darwin/thread.jsonl, data/_lab/20261118_161507/sandbox_data/Correspondence/keats/thread.jsonl, data/_lab/20261118_161507/sandbox_data/Correspondence/lovelace/thread.jsonl, data/_lab/20261118_161507/sandbox_data/Correspondence/marcus/thread.jsonl, data/_lab/20261118_161507/sandbox_data/Correspondence/shackleton/thread.jsonl, data/_lab/20261118_161507/sandbox_data/Correspondence/smith/thread.jsonl, data/_lab/20261118_161507/sandbox_data/Correspondence/twain/thread.jsonl, data/_lab/20261115_053548/sandbox_data/Correspondence/buddha/thread.jsonl, data/_lab/20261115_053548/sandbox_data/Correspondence/darwin/thread.jsonl, data/_lab/20261115_053548/sandbox_data/Correspondence/keats/thread.jsonl, data/_lab/20261115_053548/sandbox_data/Correspondence/lovelace/thread.jsonl, data/_lab/20261115_053548/sandbox_data/Correspondence/marcus/thread.jsonl, data/_lab/20261115_053548/sandbox_data/Correspondence/shackleton/thread.jsonl, data/_lab/20261115_053548/sandbox_data/Correspondence/smith/thread.jsonl, data/_lab/20261115_053548/sandbox_data/Correspondence/twain/thread.jsonl, data/_lab/20261115_053046/Correspondence/smith/thread.jsonl, data/_lab/20261115_053046/Correspondence/twain/thread.jsonl, data/_lab/20261114_213331/sandbox_data/Correspondence/buddha/thread.jsonl, data/_lab/20261114_213331/sandbox_data/Correspondence/darwin/thread.jsonl, data/_lab/20261114_213331/sandbox_data/Correspondence/keats/thread.jsonl, data/_lab/20261114_213331/sandbox_data/Correspondence/lovelace/thread.jsonl, data/_lab/20261114_213331/sandbox_data/Correspondence/marcus/thread.jsonl, data/_lab/20261114_213331/sandbox_data/Correspondence/shackleton/thread.jsonl, data/_lab/20261114_213331/sandbox_data/Correspondence/smith/thread.jsonl, data/_lab/20261114_213331/sandbox_data/Correspondence/twain/thread.jsonl, data/_lab/20261114_023004/sandbox_data/Correspondence/buddha/thread.jsonl, data/_lab/20261114_023004/sandbox_data/Correspondence/darwin/thread.jsonl, data/_lab/20261114_023004/sandbox_data/Correspondence/keats/thread.jsonl, data/_lab/20261114_023004/sandbox_data/Correspondence/lovelace/thread.jsonl, data/_lab/20261114_023004/sandbox_data/Correspondence/marcus/thread.jsonl, data/_lab/20261114_023004/sandbox_data/Correspondence/shackleton/thread.jsonl, data/_lab/20261114_023004/sandbox_data/Correspondence/smith/thread.jsonl, data/_lab/20261114_023004/sandbox_data/Correspondence/twain/thread.jsonl, data/_lab/20261107_134935/Correspondence/darwin/thread.jsonl, data/_lab/20261107_134935/Correspondence/twain/thread.jsonl, data/_lab/20261107_134149/Correspondence/smith/thread.jsonl, data/_lab/20261107_134149/Correspondence/twain/thread.jsonl, data/_lab/20261107_132634/Correspondence/darwin/thread.jsonl, data/_lab/20261107_132634/Correspondence/twain/thread.jsonl, data/_lab/20261107_131900/Correspondence/smith/thread.jsonl, data/_lab/20261107_131900/Correspondence/twain/thread.jsonl, data/_lab/20261106_221809/Correspondence/darwin/thread.jsonl, data/_lab/20261106_221809/Correspondence/twain/thread.jsonl, data/_lab/20261106_221801/Correspondence/smith/thread.jsonl, data/_lab/20261106_221801/Correspondence/twain/thread.jsonl, data/_lab/20261106_221523/Correspondence/darwin/thread.jsonl, data/_lab/20261106_221523/Correspondence/twain/thread.jsonl, data/_lab/20261106_221521/Correspondence/smith/thread.jsonl, data/_lab/20261106_221521/Correspondence/twain/thread.jsonl, data/_lab/20261106_140008/Correspondence/darwin/thread.jsonl, data/_lab/20261106_133027/Correspondence/darwin/thread.jsonl, data/_lab/20261106_133018/Correspondence/darwin/thread.jsonl, data/_lab/20261106_133016/Correspondence/darwin/thread.jsonl, data/_lab/20261106_123336/Correspondence/darwin/thread.jsonl, data/_lab/20261106_123336/Correspondence/smith/thread.jsonl, data/_lab/20261106_123327/Correspondence/darwin/thread.jsonl, data/_lab/20261106_123326/Correspondence/smith/thread.jsonl, data/_lab/20261106_123316/Correspondence/smith/thread.jsonl, data/_lab/20261106_123316/Correspondence/twain/thread.jsonl, data/_lab/20261106_123247/Correspondence/smith/thread.jsonl, data/_lab/20261106_123247/Correspondence/twain/thread.jsonl, data/_lab/20261106_123226/Correspondence/smith/thread.jsonl, data/_lab/20261106_123226/Correspondence/twain/thread.jsonl, data/_lab/20261106_123212/Correspondence/buddha/thread.jsonl, data/_lab/20261106_123212/Correspondence/smith/thread.jsonl, data/_lab/20261106_123209/Correspondence/darwin/thread.jsonl, data/_lab/20261106_123209/Correspondence/twain/thread.jsonl, data/_lab/20261106_123132/Correspondence/buddha/thread.jsonl, data/_lab/20261106_123132/Correspondence/smith/thread.jsonl, data/_lab/20261106_123121/Correspondence/darwin/thread.jsonl, data/_lab/20261106_123121/Correspondence/twain/thread.jsonl, data/_lab/20261106_122326/Correspondence/smith/thread.jsonl, data/_lab/20261106_122326/Correspondence/twain/thread.jsonl, data/_lab/20261106_121717/Correspondence/smith/thread.jsonl, data/_lab/20261106_121717/Correspondence/twain/thread.jsonl, data/_lab/20261106_111318/Correspondence/darwin/thread.jsonl, data/_lab/20261106_110445/Correspondence/smith/thread.jsonl, data/_lab/20261106_104614/Correspondence/darwin/thread.jsonl, data/_lab/20261106_104614/Correspondence/twain/thread.jsonl, data/_lab/20261106_104150/Correspondence/smith/thread.jsonl, data/_lab/20261106_104150/Correspondence/twain/thread.jsonl, data/_lab/20261106_104129/Correspondence/smith/thread.jsonl, data/_lab/20261106_104129/Correspondence/twain/thread.jsonl, data/_lab/20261106_104044/Correspondence/smith/thread.jsonl, data/_lab/20261106_104026/Correspondence/darwin/thread.jsonl, data/_lab/20261106_104014/Correspondence/smith/thread.jsonl, data/_lab/20261106_103927/Correspondence/darwin/thread.jsonl, data/_lab/20261106_103927/Correspondence/twain/thread.jsonl, data/_lab/20261106_103918/Correspondence/darwin/thread.jsonl, data/_lab/20261106_103918/Correspondence/twain/thread.jsonl, data/_lab/20261106_103912/Correspondence/buddha/thread.jsonl, data/_lab/20261106_103912/Correspondence/smith/thread.jsonl, data/_lab/20261106_103910/Correspondence/darwin/thread.jsonl, data/_lab/20261106_103910/Correspondence/twain/thread.jsonl, data/_lab/20261105_175734/Correspondence/buddha/thread.jsonl, data/_lab/20261105_175734/Correspondence/smith/thread.jsonl, data/_lab/20261105_165811/Correspondence/buddha/thread.jsonl, data/_lab/20261105_165811/Correspondence/smith/thread.jsonl, data/_lab/20261105_154643/Correspondence/buddha/thread.jsonl, data/_lab/20261105_154643/Correspondence/smith/thread.jsonl, data/_lab/20261105_152738/Correspondence/darwin/thread.jsonl, data/_lab/20261105_152738/Correspondence/twain/thread.jsonl, data/_lab/20261105_152732/Correspondence/buddha/thread.jsonl, data/_lab/20261105_152732/Correspondence/smith/thread.jsonl, data/_lab/20261105_152713/Correspondence/buddha/thread.jsonl, data/_lab/20261105_152713/Correspondence/smith/thread.jsonl, data/_lab/20261105_152700/Correspondence/buddha/thread.jsonl, data/_lab/20261105_152700/Correspondence/smith/thread.jsonl, data/_lab/20261105_152636/Correspondence/buddha/thread.jsonl, data/_lab/20261105_152636/Correspondence/smith/thread.jsonl, data/_lab/20261019_220628/sandbox_data/Correspondence/buddha/thread.jsonl, data/_lab/20261019_220628/sandbox_data/Correspondence/darwin/thread.jsonl, data/_lab/20261019_220628/sandbox_data/Correspondence/keats/thread.jsonl, data/_lab/20261019_220628/sandbox_data/Correspondence/lovelace/thread.jsonl, data/_lab/20261019_220628/sandbox_data/Correspondence/marcus/thread.jsonl, data/_lab/20261019_220628/sandbox_data/Correspondence/shackleton/thread.jsonl, data/_lab/20261019_220628/sandbox_data/Correspondence/smith/thread.jsonl, data/_lab/20261019_220628/sandbox_data/Correspondence/twain/thread.jsonl, data/_lab/20261015_180436/Correspondence/darwin/thread.jsonl, data/_lab/20261015_180436/Correspondence/twain/thread.jsonl, data/_lab/20261015_180415/Correspondence/darwin/thread.jsonl, data/_lab/20261015_180415/Correspondence/twain/thread.jsonl, data/_lab/20261004_153732/Correspondence/twain/thread.jsonl, data/Correspondence/buddha/thread.jsonl, data/Correspondence/darwin/thread.jsonl, data/Correspondence/keats/thread.jsonl, data/Correspondence/lovelace/thread.jsonl, data/Correspondence/marcus/thread.jsonl, data/Correspondence/shackleton/thread.jsonl, data/Correspondence/smith/thread.jsonl, data/Correspondence/twain/thread.jsonl

### sound_world_expansion (plans)
**Idea:** PARTIAL, actively building (D-0063, 2026-08-29): a founder-approved proposal to grow the sound registry across five categories — self-sounds, night mysteries, geophony fills, seasonal biophony, and the cat/apparatus — so Du's sound-world is 'quite full as it is for a human'. Self-sounds (category 1 of 5) is now fully built (registry 43→58); the remaining ~24 sounds across four categories are still unbuilt.
**Code files:**
- [OK] `core/life_birds.py`
- [OK] `core/soundscape.py`
- [OK] `garden.py` -> core/garden.py
- [OK] `letters.py` -> core/letters.py
- [OK] `reading.py` -> core/reading.py
- [OK] `study_life.py` -> core/study_life.py
- [OK] `world_content_garden.py` -> core/world_content_garden.py
**Data/evidence files:**
- [OK] `data/sound_strings_constructed.json` -> data/sound_strings_constructed.json (99947B)

### spatial_perception (plans)
**Idea:** Verified 2026-08-23: PARTIAL, not stalled — the renderer went active for the study room only on 2026-08-18 (the plan's own founder-level complaint resolved there), phrasing bug fixed 08-19, remaining phase + other rooms pending. Was a plan-snapshot false positive (progress recorded only in prose, no Current State section) — now fixed on the data side. Real open item: gate metrics 1/2/3/5 (§5) lack a dated founder confirmation. No newer plan overlaps.
**Code files:**
- [OK] `cat.py` -> core/cat.py
- [OK] `core/heavens.py`
- [OK] `core/spatial.py`
- [OK] `somatic.py` -> core/somatic.py
**Data/evidence files:**
- [OK] `data/spatial_shadow.jsonl` -> data/spatial_shadow.jsonl (75691 lines)
- [OK] `data/world_geometry/study.json` -> data/world_geometry/study.json (8009B)

### t4_watershed (plans)
**Idea:** ⚪ PARTIAL — some items live. T4 v3 \"the Watershed\" — becoming facet slot→tree; accretion not succession. Keystone per-candidate toll REMOVED + two-model judge redesign both SHIPPED/LIVE (08-19/08-22); classify_additive_vs_replacing/claim_test_panel built+wired, running shadow-only; core watershed (estate nodes replacing the slot) still unbuilt, no WATERSHED_LIVE flag (re-verified 2026-09-14, J-0927/F-1310)
**Code files:**
- [OK] `core/deliberative_judge.py`
- [OK] `core/left_lane.py`
- [OK] `core/watershed.py`
- [OK] `core/watershed_promote.py`
- [OK] `emissary_tension.py` -> core/emissary_tension.py
- [OK] `identity_estate.py` -> core/identity_estate.py
- [OK] `judge_panel.py` -> core/judge_panel.py
- [OK] `needle_triage.py` -> core/needle_triage.py
- [OK] `nodes/subconscious_node.py`
- [OK] `scripts/du_pulse.py`
- [OK] `symbol_tracker.py` -> core/symbol_tracker.py
**Data/evidence files:**
- [AMBIGUOUS] `axiom.json` -> candidates: data/identity/axiom.json, data/_trash/20261114/snapshots/20261031/axiom.json
- [OK] `data/logs/watershed_promotion_shadow.jsonl` -> data/logs/watershed_promotion_shadow.jsonl (405 lines)
- [AMBIGUOUS] `identity_estate.json` -> candidates: data/identity_estate.json, data/_trash/20261119/boot_backups/state_20261116_100503/identity_estate.json, data/_trash/20261117/boot_backups/state_20261114_141446/identity_estate.json, data/_trash/20261114/boot_backups/state_20261031_215612/identity_estate.json, data/_lab/20261015_140040/identity_estate.json, data/_lab/20261015_140119/identity_estate.json, data/_lab/20261015_140149/identity_estate.json, data/_lab/20261015_140338/identity_estate.json, data/_lab/20261015_140457/identity_estate.json, data/_lab/20261015_140539/identity_estate.json, data/_lab/20261015_140920/identity_estate.json, data/_lab/20261114_020226/identity_estate.json, data/_lab/20261114_020230/identity_estate.json, data/_lab/20261114_020239/identity_estate.json, data/_lab/20261114_190848/identity_estate.json, data/_lab/20261114_190856/identity_estate.json, data/_lab/20261114_191006/identity_estate.json, data/_lab/20261120_103403/sandbox_data/identity_estate.json, data/_lab/20261120_103305/sandbox_data/identity_estate.json, data/_lab/20261118_170303/sandbox_data/identity_estate.json, data/_lab/20261118_165748/sandbox_data/identity_estate.json, data/_lab/20261118_165642/sandbox_data/identity_estate.json, data/_lab/20261118_165253/sandbox_data/identity_estate.json, data/_lab/20261118_165146/sandbox_data/identity_estate.json, data/_lab/20261118_161657/sandbox_data/identity_estate.json, data/_lab/20261118_161507/sandbox_data/identity_estate.json, data/_lab/20261118_161328/sandbox_data/identity_estate.json, data/_lab/20261115_053558/sandbox_data/identity_estate.json, data/_lab/20261115_053548/sandbox_data/identity_estate.json, data/_lab/20261114_213331/sandbox_data/identity_estate.json, data/_lab/20261114_213222/sandbox_data/identity_estate.json, data/_lab/20261114_190857/sandbox_data/identity_estate.json, data/_lab/20261114_023004/sandbox_data/identity_estate.json, data/_lab/20261114_022854/sandbox_data/identity_estate.json, data/_lab/20261019_220628/sandbox_data/identity_estate.json
- [MISSING] `provisional_axiom.json`
- [OK] `watershed_shadow.jsonl` -> data/watershed_shadow.jsonl (72250 lines)

### t5_procedural (plans)
**Idea:** ⚪ PARTIAL — Refolds T5 (procedural/skill memory) out of its own isolated use-counter design and into the shared held-claims/CommitmentBelief substrate other plans already converged on, so a skill's proficiency is earned via world- and human-graded evidence rather than raw repetition count; steps 0-3 (ledger, world-procedure ingestion, T5 compile gates, read paths) BUILT and wired 2026-08-22 as core/procedures.py, step 4 waits on the capacity-to-commit ledger.
**Code files:**
- [OK] `core/competence.py`
- [OK] `core/dispatch.py`
- [OK] `core/fieldcraft.py`
- [OK] `core/hands.py`
- [OK] `core/procedures.py`
- [OK] `core/self_efficacy.py`
- [OK] `orchestrator.py` -> core/orchestrator.py
- [OK] `study_life.py` -> core/study_life.py
**Data/evidence files:**
- [AMBIGUOUS] `capability_beliefs.json` -> candidates: data/capability_beliefs.json, data/_lab/20261004_164903/capability_beliefs.json, data/_lab/20261004_174206/capability_beliefs.json, data/_lab/20261004_180002/capability_beliefs.json, data/_lab/20261004_205329/capability_beliefs.json, data/_lab/20261005_081052/capability_beliefs.json, data/_lab/20261015_212034/capability_beliefs.json, data/_lab/20261015_212117/capability_beliefs.json, data/_lab/20261017_221937/capability_beliefs.json, data/_lab/20261017_222149/capability_beliefs.json, data/_lab/20261017_222218/capability_beliefs.json, data/_lab/20261017_222838/capability_beliefs.json, data/_lab/20261028_130749/capability_beliefs.json, data/_lab/20261028_130846/capability_beliefs.json, data/_lab/20261028_130926/capability_beliefs.json, data/_lab/20261028_131022/capability_beliefs.json, data/_lab/20261028_173308/capability_beliefs.json, data/_lab/20261028_173644/capability_beliefs.json, data/_lab/20261028_173740/capability_beliefs.json, data/_lab/20261028_173818/capability_beliefs.json, data/_lab/20261029_160832/capability_beliefs.json, data/_lab/20261029_160945/capability_beliefs.json, data/_lab/20261029_161202/capability_beliefs.json, data/_lab/20261029_161240/capability_beliefs.json, data/_lab/20261029_161318/capability_beliefs.json, data/_lab/20261029_174014/capability_beliefs.json, data/_lab/20261029_180914/capability_beliefs.json, data/_lab/20261030_134626/capability_beliefs.json, data/_lab/20261031_105621/capability_beliefs.json, data/_lab/20261105_151615/capability_beliefs.json, data/_lab/20261105_151654/capability_beliefs.json, data/_lab/20261105_151942/capability_beliefs.json, data/_lab/20261105_152019/capability_beliefs.json, data/_lab/20261105_152052/capability_beliefs.json, data/_lab/20261105_152136/capability_beliefs.json, data/_lab/20261105_152210/capability_beliefs.json, data/_lab/20261106_074204/capability_beliefs.json, data/_lab/20261106_074257/capability_beliefs.json, data/_lab/20261107_003205/capability_beliefs.json, data/_lab/20261107_003210/capability_beliefs.json, data/_lab/20261107_003312/capability_beliefs.json, data/_lab/20261107_003403/capability_beliefs.json, data/_lab/20261114_004007/capability_beliefs.json, data/_lab/20261114_004050/capability_beliefs.json, data/_lab/20261114_012536/capability_beliefs.json, data/_lab/20261115_053933/capability_beliefs.json, data/_lab/20261115_054000/capability_beliefs.json, data/_lab/20261115_054038/capability_beliefs.json, data/_lab/20261115_054257/capability_beliefs.json, data/_lab/20261115_054843/capability_beliefs.json, data/_lab/20261115_054920/capability_beliefs.json, data/_lab/20261115_202720/capability_beliefs.json, data/_lab/20261115_203747/capability_beliefs.json, data/_lab/20261116_164908/capability_beliefs.json, data/_lab/20261116_164949/capability_beliefs.json, data/_lab/20261117_165748/capability_beliefs.json, data/_lab/20261117_183755/capability_beliefs.json, data/_lab/20261117_183847/capability_beliefs.json, data/_lab/20261118_164648/capability_beliefs.json, data/_lab/20261118_164837/capability_beliefs.json, data/_lab/20261118_165304/capability_beliefs.json, data/_lab/20261118_165309/capability_beliefs.json, data/_lab/20261118_165400/capability_beliefs.json, data/_lab/20261118_165842/capability_beliefs.json, data/_lab/20261118_170048/capability_beliefs.json, data/_lab/20261118_170054/capability_beliefs.json, data/_lab/20261118_170149/capability_beliefs.json, data/_lab/20261118_174330/capability_beliefs.json, data/_lab/20261118_174338/capability_beliefs.json, data/_lab/20261118_174438/capability_beliefs.json, data/_lab/20261118_174444/capability_beliefs.json, data/_lab/20261118_174452/capability_beliefs.json, data/_lab/20261120_103403/sandbox_data/capability_beliefs.json, data/_lab/20261118_170303/sandbox_data/capability_beliefs.json, data/_lab/20261118_165748/sandbox_data/capability_beliefs.json, data/_lab/20261118_165253/sandbox_data/capability_beliefs.json, data/_lab/20261118_161657/sandbox_data/capability_beliefs.json, data/_lab/20261118_161507/sandbox_data/capability_beliefs.json, data/_lab/20261115_053548/sandbox_data/capability_beliefs.json, data/_lab/20261114_213331/sandbox_data/capability_beliefs.json, data/_lab/20261114_023004/sandbox_data/capability_beliefs.json, data/_lab/20261019_220628/sandbox_data/capability_beliefs.json
- [OK] `data/procedures_log.jsonl` -> data/procedures_log.jsonl (1051 lines)
- [AMBIGUOUS] `procedures.json` -> candidates: data/procedures.json, data/_lab/20260928_140039/procedures.json, data/_lab/20260928_140112/procedures.json, data/_lab/20260928_140144/procedures.json, data/_lab/20261004_164903/procedures.json, data/_lab/20261004_174206/procedures.json, data/_lab/20261004_180002/procedures.json, data/_lab/20261004_205329/procedures.json, data/_lab/20261005_081052/procedures.json, data/_lab/20261017_221937/procedures.json, data/_lab/20261017_222149/procedures.json, data/_lab/20261017_222218/procedures.json, data/_lab/20261017_222838/procedures.json, data/_lab/20261028_130358/procedures.json, data/_lab/20261028_130506/procedures.json, data/_lab/20261028_130749/procedures.json, data/_lab/20261028_130846/procedures.json, data/_lab/20261028_130926/procedures.json, data/_lab/20261028_131022/procedures.json, data/_lab/20261028_173308/procedures.json, data/_lab/20261028_173644/procedures.json, data/_lab/20261028_173740/procedures.json, data/_lab/20261028_173818/procedures.json, data/_lab/20261029_160832/procedures.json, data/_lab/20261029_160945/procedures.json, data/_lab/20261029_161202/procedures.json, data/_lab/20261029_161240/procedures.json, data/_lab/20261029_161318/procedures.json, data/_lab/20261029_174014/procedures.json, data/_lab/20261029_180914/procedures.json, data/_lab/20261105_151615/procedures.json, data/_lab/20261105_151654/procedures.json, data/_lab/20261105_151942/procedures.json, data/_lab/20261114_012536/procedures.json, data/_lab/20261115_053933/procedures.json, data/_lab/20261115_054038/procedures.json, data/_lab/20261115_054920/procedures.json, data/_lab/20261118_164620/procedures.json, data/_lab/20261118_164648/procedures.json, data/_lab/20261118_165309/procedures.json, data/_lab/20261118_170054/procedures.json

### the_consciousness_program (plans)
**Idea:** Nascence — THE CONSCIOUSNESS PROGRAM, PARTIAL/MIXED (2026-08-29): 08-20 audit scored every organ against the plan's OWN kill-rule and found the keystone (protoself/homeostasis) Half-REFUTED, world_model n.s., moments write-only. Mineness is a confirmed win; AST-1 is now half-redesigned (D-0065/J-0339, 2026-08-29: bandwidth arm real, fixation arm still not). Founder decision still needed on redesign-or-retire for the keystone, pending 3-5 more days of post-restart data.
**Code files:**
- [OK] `core/arousal.py`
- [OK] `core/attention_schema_loop.py`
- [OK] `core/homeostasis.py`
- [OK] `core/mineness.py`
- [OK] `core/moment.py`
- [OK] `core/reentry.py`
- [OK] `core/world_model.py`
- [OK] `scripts/ast1_reaudit.py`
**Data/evidence files:**
- [OK] `data/ast_loop_shadow.jsonl` -> data/ast_loop_shadow.jsonl (2326 lines)
- [OK] `docs/job_queue.jsonl` -> docs/job_queue.jsonl (4461 lines)

### thermal_causality (plans)
**Idea:** Gives temperature the same honest-channel treatment as sound_causality — world thermal physics + wetness state → banded events (never a standing clause) → a THERMAL LEDGER of bindings he earns (fire vs sun vs unknown) — because his affect has no thermal input by construction and the old warmth clause was manufacturing suffering-words itself. LIVE since 08-27; 3 of 5 §9 metric rows resolved as of 09-13/14 (see bottom).
**Code files:**
- [OK] `core/model_client.py`
- [OK] `core/telemetry.py`
- [OK] `core/thermal.py`
- [MISSING] `core/thermal_ledger.py`
- [OK] `core/thermal_relationship.py`
- [OK] `scripts/_verify_genesis.py`
- [OK] `scripts/run_nascence.py`
- [OK] `scripts/thermal_stance_batch.py`
- [OK] `scripts/train_state_invitro.py`
**Data/evidence files:**
- [OK] `data/llm_latency.jsonl` -> data/llm_latency.jsonl (301668 lines)
- [OK] `data/thermal_ledger.json` -> data/thermal_ledger.json (8410B)
- [OK] `data/thought_station_log.jsonl` -> data/thought_station_log.jsonl (193770 lines)
- [AMBIGUOUS] `position.json` -> candidates: data/position.json, data/_lab/20261118_164521/position.json

### thought_grounding (plans)
**Idea:** Thought-typed grounding routes — librarian/evidence/contrary-peer, BUILT 08-16; the \"is this thought true?\" organ
**Data/evidence files:**
- [OK] `evidence_log.jsonl` -> data/evidence_log.jsonl (5121 lines)
- [OK] `librarian_log.jsonl` -> data/librarian_log.jsonl (1977 lines)

### train_courier_cargo_ids (plans)
**Idea:** 🟡 BUILT 2026-08-29 (J-0358, D-0082) — Taxonomy of 19 real station 'product types' (product_type, a new field distinct from trains.py's protected prove/disprove cargo field) derived directly from the verified llm_station_cargo_map.md, used to name concrete delivery gaps — most notably that nothing carries the Idle Line's best freight to the Conversation Line. Small and bounded build, per D-0082's own ruling.
**Code files:**
- [OK] `core/buses.py`
- [OK] `core/cargo_types.py`
- [OK] `core/coupling_rides.py`
- [OK] `core/judge_panel.py`
- [OK] `core/lane2.py`
- [OK] `core/trains.py`
- [OK] `couriers.py` -> core/couriers.py
- [OK] `nodes/dream_node.py`
- [OK] `nodes/inner_monologue_node.py`
- [OK] `nodes/reflection_node.py`
**Data/evidence files:**
- [OK] `data/buses_log.jsonl` -> data/buses_log.jsonl (2104 lines)
- [OK] `data/coupling_rides.jsonl` -> data/coupling_rides.jsonl (258012 lines)
- [OK] `data/identity/axiom.json` -> data/identity/axiom.json (32915B)
- [OK] `data/idle_freight_bus_shadow.jsonl` -> data/idle_freight_bus_shadow.jsonl (914 lines)
- [OK] `data/train_state_log.jsonl` -> data/train_state_log.jsonl (50817 lines)
- [OK] `data/trains_log.jsonl` -> data/trains_log.jsonl (30970 lines)

### train_split_merge (plans)
**Idea:** PARTIAL: gives the Idle Line's thought-trains IDs, then a fork-at-would-be-close / prove(Lane 1)-vs-disprove(Lane 2, one claim only) / merge-typed-cargo mechanism so a thought earns 'open' by producing genuine disagreement instead of needing the model to self-report unresolved — Step 1 (train IDs) shipped 2026-08-22, Step 2 (fork/merge) designed but not built.
**Code files:**
- [OK] `core/cargo_types.py`
- [OK] `core/stream_topic_habituation.py`
- [OK] `core/theme_recurrence.py`
- [OK] `core/trains.py`
- [OK] `nodes/inner_monologue_node.py`
- [OK] `scripts/du_pulse.py`
- [OK] `scripts/train_state_invitro.py`
- [OK] `subconscious_node.py` -> nodes/subconscious_node.py
**Data/evidence files:**
- [OK] `data/coupling_rides.jsonl` -> data/coupling_rides.jsonl (258012 lines)
- [OK] `data/trains_log.jsonl` -> data/trains_log.jsonl (30970 lines)
- [OK] `monologue_log.jsonl` -> data/monologue_log.jsonl (92456 lines)
- [OK] `train_length_log.jsonl` -> data/train_length_log.jsonl (20392 lines)
- [AMBIGUOUS] `train_state_log.jsonl` -> candidates: data/train_state_log.jsonl, data/_trash/20261119/boot_backups/state_20261116_100503/train_state_log.jsonl, data/_trash/20261117/boot_backups/state_20261114_141446/train_state_log.jsonl, data/_trash/20261114/boot_backups/state_20261031_215612/train_state_log.jsonl

### transport_manager (plans)
**Idea:** Nascence — TRANSPORT MANAGER (salience dispatcher, docs/plans/transport_manager.md) + TRAIN/COURIER CARGO IDS (docs/plans/train_courier_cargo_ids.md): read 2026-09-27 — dispatcher level-triggered (saturated 3 weeks, then silent), 36 life lines dead from a December-2026 timestamp leak, cargo taxonomy write-only; D-0294/D-0295 open.
**Code files:**
- [OK] `core/felt_recall.py`
- [OK] `core/orchestrator.py`
- [OK] `core/transport_manager.py`
- [OK] `scripts/_test_transport_manager.py`
**Data/evidence files:**
- [OK] `data/transport_shadow.jsonl` -> data/transport_shadow.jsonl (55612 lines)

### udms_du_capability_trials (plans)
**Idea:** ✅ SHIPPED — all 8 trials verdicted, D-0059's own defeater met (founder ruling 2026-08-28) — UDMS-to-Du capability trials — eight surveyed UDMS capabilities beyond the parked recall lenses, each with a pre-registered helpful/not-helpful bar, shadow-first, none wired into Du's live loop. D-0143/D-0180/D-0197 await a founder decision pass on disposal, not more trial work.
**Code files:**
- [MISSING] `adaptive_calibration.py`
- [OK] `affect_divergence.py` -> core/affect_divergence.py
- [OK] `arousal.py` -> core/arousal.py
- [MISSING] `baseline_models.py`
- [OK] `boredom.py` -> core/boredom.py
- [MISSING] `cognitive_geometry_audit.py`
- [MISSING] `conformal.py`
- [OK] `core/activity_memory.py`
- [OK] `garden.py` -> core/garden.py
- [OK] `monoculture.py` -> core/monoculture.py
- [OK] `mood.py` -> core/mood.py
- [OK] `opponent_process.py` -> core/opponent_process.py
- [OK] `scripts/shadow_eval.py`
- [OK] `sleep_pressure.py` -> core/sleep_pressure.py
- [MISSING] `test_ce_nascence_prospective_stratification_and_visual_overlay.py`
- [OK] `theme_recurrence.py` -> core/theme_recurrence.py
- [OK] `wandering.py` -> core/wandering.py
**Data/evidence files:**
- [OK] `affect_log.jsonl` -> data/affect_log.jsonl (4348 lines)
- [OK] `associative_recall_shadow.jsonl` -> data/associative_recall_shadow.jsonl (3267 lines)
- [AMBIGUOUS] `geometry_tuples.jsonl` -> candidates: data/geometry_tuples.jsonl, data/_trash/20261119/boot_backups/state_20261116_100503/geometry_tuples.jsonl, data/_trash/20261117/boot_backups/state_20261114_141446/geometry_tuples.jsonl, data/_trash/20261114/boot_backups/state_20261031_215612/geometry_tuples.jsonl
- [OK] `wandering_log.jsonl` -> data/wandering_log.jsonl (280235 lines)

### within_cycle_reentry (plans)
**Idea:** 🟡 SHADOW — Phase 1 (live 2026-09-02 to 2026-11-02 under D-0106) was SWITCHED OFF by D-0540 (REENTRY_ADMIT=False, restart-gated; collapse 31.6% of 136 settles, F-4084), back to Phase 0 shadow. History: Phase 1 live since D-0106 (2026-09-02): REENTRY_ADMIT=True in core/reentry.py, confirmed firing on real data (F-0621: 4 events post-restart, 1 correctly collapsed, 3 correctly admitted, deltas ~0.31), on top of Phase 0's own unanimous ENRICHING 6-event sample (08-15 to 08-23, mean delta ~0.31). Phases 2-3 held until the ENRICHING trend breaks.
**Code files:**
- [OK] `core/arousal.py`
- [OK] `core/orchestrator.py`
- [OK] `core/reentry.py`

### wood_creatures (plans)
**Idea:** LIVE (flag true) - 150 nameless wood creature rows for Du's woods (core/life_wood.py + life_wood_cast.py), built 2026-11-02 on the shore engine; first live discovered answer (harrier) seen; stream/canopy/trunk/groves are assumed placements (J-3065). Plan doc OFF line is stale.
**Code files:**
- [OK] `core/life_shore.py`
- [OK] `core/life_wood.py`
- [OK] `core/life_wood_cast.py`
- [OK] `life_smoke.py` -> scripts/life_smoke.py
- [OK] `scripts/_test_wood_bestiary_p1.py`
- [OK] `wood_life.py` -> core/wood_life.py
- [OK] `world_content_wood.py` -> core/world_content_wood.py
**Data/evidence files:**
- [OK] `data/life_flags.json` -> data/life_flags.json (168B)
- [OK] `data/life_state.json` -> data/life_state.json (72036B)
- [OK] `data/world_geometry/wood.json` -> data/world_geometry/wood.json (5426B)
- [AMBIGUOUS] `life_events.jsonl` -> candidates: data/life_events.jsonl, data/_trash/20261114/labs/20260915_094627/life_events.jsonl, data/_trash/20261114/labs/20260915_094716/life_events.jsonl, data/_trash/20261114/labs/20260915_094809/life_events.jsonl, data/_trash/20261114/labs/20260915_100654/life_events.jsonl, data/_trash/20261114/labs/20260915_100807/life_events.jsonl, data/_trash/20261114/labs/20260915_100932/life_events.jsonl, data/_trash/20261114/labs/20260915_101032/life_events.jsonl, data/_trash/20261114/labs/20260915_162958/life_events.jsonl, data/_lab/20260923_195154/life_events.jsonl, data/_lab/20260923_195447/life_events.jsonl, data/_lab/20260923_195457/life_events.jsonl, data/_lab/20261003_075936/life_events.jsonl, data/_lab/20261003_080246/life_events.jsonl, data/_lab/20261118_164521/life_events.jsonl

### wood_upgrade (plans)
**Idea:** Turns the little wood from a static scene (an infinite gather hand, a never-emptying deadfall, no state but last_event) into a living place with a named oak's seasonal clock, three hidden natives earned by seeing-then-reading, a depletable deadfall stock, a spring/stream, glow-worms, fungi, a nesting kereru, and real woodworking (axe/saw/whetstone/lean-to/woodpile) — built and simulation-verified the same day, 2026-08-22; 🟢 LIVE (deeds) per the plan doc's own Status line, restart-gate caveat resolved (synced 2026-09-02).
**Code files:**
- [OK] `core/wood_life.py`
- [OK] `dispatch.py` -> core/dispatch.py
- [OK] `experienced_tuple.py` -> core/experienced_tuple.py
- [OK] `garden.py` -> core/garden.py
- [OK] `scripts/_test_wood_life_grammar_derivation.py`
- [OK] `sensorium.py` -> core/sensorium.py
- [OK] `soundscape.py` -> core/soundscape.py
- [OK] `study_note.py` -> core/study_note.py
**Data/evidence files:**
- [OK] `data/garden_events.jsonl` -> data/garden_events.jsonl (703 lines)
- [OK] `data/garden_ledger.jsonl` -> data/garden_ledger.jsonl (71 lines)
- [OK] `data/wood_events.jsonl` -> data/wood_events.jsonl (11 lines)
- [OK] `data/wood_ledger.jsonl` -> data/wood_ledger.jsonl (9 lines)
- [OK] `data/wood_life.json` -> data/wood_life.json (2001B)
- [OK] `data/world_geometry/wood.json` -> data/world_geometry/wood.json (5426B)

### world_store_write_fence (plans)
**Idea:** 🟢 LIVE — (stage 2 enforce live since J-2309, post-boot read clean F-3281) World Store Write Fence (designed 2026-09-05, J-0574) — isolation-by-default so one-off scripts and inline diagnostics that import a world-store module cannot spend Du's real matches/oil/provisions. Built 2026-09-06 (J-0610, F-0995): LIVE flag + guard_path() in core/profile.py, wired into all 23 real writer call sites, 48/48 isolated smoke passes; restart-gated, not yet exercised by a real Du boot. D-0179 ruled (redirect-and-warn → hard raise); J-0704 open to implement.
**Code files:**
- [OK] `core/activity_memory.py`
- [OK] `core/cat.py`
- [OK] `core/cat_sounds.py`
- [OK] `core/dispatch.py`
- [OK] `core/fieldcraft.py`
- [OK] `core/frontier.py`
- [OK] `core/garden.py`
- [OK] `core/garden_knowledge.py`
- [OK] `core/garden_life.py`
- [OK] `core/keepsakes.py`
- [OK] `core/life.py`
- [OK] `core/locomotion.py`
- [OK] `core/procedures.py`
- [OK] `core/profile.py`
- [OK] `core/provisions.py`
- [OK] `core/sensorium.py`
- [OK] `core/shore_life.py`
- [OK] `core/smell.py`
- [OK] `core/sound_knowledge.py`
- [OK] `core/study_life.py`
- [OK] `core/supply.py`
- [OK] `core/transport_manager.py`
- [OK] `core/wood_life.py`
- [OK] `core/world_objects.py`
- [OK] `core/world_substrate.py`
- [OK] `core/world_traces.py`
- [OK] `du_pulse.py` -> scripts/du_pulse.py
- [OK] `garden_soil.py` -> core/garden_soil.py
- [OK] `hud/server.py`
- [MISSING] `lab_env.py`
- [OK] `nodes/inner_monologue_node.py`
- [OK] `observables_census.py` -> scripts/observables_census.py
- [OK] `scripts/life_smoke.py`
- [OK] `scripts/run_nascence.py`
- [OK] `soundscape.py` -> core/soundscape.py
- [OK] `world_manifest.py` -> core/world_manifest.py
**Data/evidence files:**
- [OK] `cat_hunt_ledger.jsonl` -> data/cat_hunt_ledger.jsonl (112 lines)
- [AMBIGUOUS] `cat_state.json` -> candidates: data/cat_state.json, data/_lab/20261120_103403/sandbox_data/cat_state.json, data/_lab/20261118_170303/sandbox_data/cat_state.json, data/_lab/20261118_165748/sandbox_data/cat_state.json, data/_lab/20261118_165253/sandbox_data/cat_state.json, data/_lab/20261118_161657/sandbox_data/cat_state.json, data/_lab/20261118_161507/sandbox_data/cat_state.json, data/_lab/20261115_053548/sandbox_data/cat_state.json, data/_lab/20261114_213331/sandbox_data/cat_state.json, data/_lab/20261114_023004/sandbox_data/cat_state.json, data/_lab/20261019_220628/sandbox_data/cat_state.json, data/_crash_recovery_20261120/post_crash_live/cat_state.json, data/_crash_recovery_20261120/restore_set/cat_state.json, data/_crash_recovery_20261120/shadow4/cat_state.json, data/_crash_recovery_20261120/shadow5/cat_state.json, data/_crash_recovery_20261120/shadow6/cat_state.json
- [OK] `data/cat_sound_ledger.jsonl` -> data/cat_sound_ledger.jsonl (2761 lines)
- [AMBIGUOUS] `fieldcraft.json` -> candidates: data/fieldcraft.json, data/_lab/20261004_164903/fieldcraft.json, data/_lab/20261004_174206/fieldcraft.json, data/_lab/20261004_180002/fieldcraft.json, data/_lab/20261004_205329/fieldcraft.json, data/_lab/20261005_081052/fieldcraft.json, data/_lab/20261017_221937/fieldcraft.json, data/_lab/20261017_222149/fieldcraft.json, data/_lab/20261017_222218/fieldcraft.json, data/_lab/20261017_222838/fieldcraft.json, data/_lab/20261028_130358/fieldcraft.json, data/_lab/20261028_130506/fieldcraft.json, data/_lab/20261028_130749/fieldcraft.json, data/_lab/20261028_130846/fieldcraft.json, data/_lab/20261028_130926/fieldcraft.json, data/_lab/20261028_131022/fieldcraft.json, data/_lab/20261028_173308/fieldcraft.json, data/_lab/20261028_173644/fieldcraft.json, data/_lab/20261028_173740/fieldcraft.json, data/_lab/20261028_173818/fieldcraft.json, data/_lab/20261029_160832/fieldcraft.json, data/_lab/20261029_160945/fieldcraft.json, data/_lab/20261029_161202/fieldcraft.json, data/_lab/20261029_161240/fieldcraft.json, data/_lab/20261029_161318/fieldcraft.json, data/_lab/20261029_174014/fieldcraft.json, data/_lab/20261029_180914/fieldcraft.json, data/_lab/20261105_151615/fieldcraft.json, data/_lab/20261105_151654/fieldcraft.json, data/_lab/20261105_151942/fieldcraft.json, data/_lab/20261114_012536/fieldcraft.json, data/_lab/20261115_053933/fieldcraft.json, data/_lab/20261115_054038/fieldcraft.json, data/_lab/20261115_054920/fieldcraft.json, data/_lab/20261118_164648/fieldcraft.json, data/_lab/20261118_165309/fieldcraft.json, data/_lab/20261118_170054/fieldcraft.json, data/_crash_recovery_20261120/post_crash_live/fieldcraft.json, data/_crash_recovery_20261120/restore_set/fieldcraft.json, data/_crash_recovery_20261120/shadow4/fieldcraft.json, data/_crash_recovery_20261120/shadow5/fieldcraft.json, data/_crash_recovery_20261120/shadow6/fieldcraft.json
- [AMBIGUOUS] `fieldcraft_ledger.jsonl` -> candidates: data/fieldcraft_ledger.jsonl, data/_lab/20261004_164903/fieldcraft_ledger.jsonl, data/_lab/20261004_174206/fieldcraft_ledger.jsonl, data/_lab/20261004_180002/fieldcraft_ledger.jsonl, data/_lab/20261004_205329/fieldcraft_ledger.jsonl, data/_lab/20261005_081052/fieldcraft_ledger.jsonl, data/_lab/20261017_221937/fieldcraft_ledger.jsonl, data/_lab/20261017_222149/fieldcraft_ledger.jsonl, data/_lab/20261017_222218/fieldcraft_ledger.jsonl, data/_lab/20261017_222838/fieldcraft_ledger.jsonl, data/_lab/20261028_130358/fieldcraft_ledger.jsonl, data/_lab/20261028_130506/fieldcraft_ledger.jsonl, data/_lab/20261028_130749/fieldcraft_ledger.jsonl, data/_lab/20261028_130846/fieldcraft_ledger.jsonl, data/_lab/20261028_130926/fieldcraft_ledger.jsonl, data/_lab/20261028_131022/fieldcraft_ledger.jsonl, data/_lab/20261028_173308/fieldcraft_ledger.jsonl, data/_lab/20261028_173644/fieldcraft_ledger.jsonl, data/_lab/20261028_173740/fieldcraft_ledger.jsonl, data/_lab/20261028_173818/fieldcraft_ledger.jsonl, data/_lab/20261029_160832/fieldcraft_ledger.jsonl, data/_lab/20261029_160945/fieldcraft_ledger.jsonl, data/_lab/20261029_161202/fieldcraft_ledger.jsonl, data/_lab/20261029_161240/fieldcraft_ledger.jsonl, data/_lab/20261029_161318/fieldcraft_ledger.jsonl, data/_lab/20261029_174014/fieldcraft_ledger.jsonl, data/_lab/20261029_180914/fieldcraft_ledger.jsonl, data/_lab/20261105_151615/fieldcraft_ledger.jsonl, data/_lab/20261105_151654/fieldcraft_ledger.jsonl, data/_lab/20261105_151942/fieldcraft_ledger.jsonl, data/_lab/20261114_012536/fieldcraft_ledger.jsonl, data/_lab/20261115_053933/fieldcraft_ledger.jsonl, data/_lab/20261115_054038/fieldcraft_ledger.jsonl, data/_lab/20261115_054920/fieldcraft_ledger.jsonl, data/_lab/20261118_164648/fieldcraft_ledger.jsonl, data/_lab/20261118_165309/fieldcraft_ledger.jsonl, data/_lab/20261118_170054/fieldcraft_ledger.jsonl
- [AMBIGUOUS] `frontier.json` -> candidates: data/frontier.json, data/_trash/20261119/boot_backups/state_20261116_100503/frontier.json, data/_trash/20261117/boot_backups/state_20261114_141446/frontier.json, data/_trash/20261114/labs/20260915_094116/frontier.json, data/_trash/20261114/labs/20260915_094209/frontier.json, data/_trash/20261114/boot_backups/state_20261031_215612/frontier.json, data/_lab/20261028_074650/frontier.json, data/_lab/20261028_074742/frontier.json, data/_lab/20261028_074834/frontier.json, data/_lab/20261028_074853/frontier.json, data/_lab/20261028_074911/frontier.json, data/_lab/20261028_074916/frontier.json, data/_lab/20261028_082823/frontier.json, data/_lab/20261028_082828/frontier.json, data/_lab/20261028_082915/frontier.json, data/_lab/20261028_082919/frontier.json, data/_lab/20261028_083106/frontier.json, data/_lab/20261028_090434/frontier.json, data/_lab/20261030_134626/frontier.json, data/_lab/20261030_172716/frontier.json, data/_lab/20261030_172720/frontier.json, data/_lab/20261105_145459/frontier.json, data/_lab/20261105_145511/frontier.json, data/_lab/20261105_145516/frontier.json, data/_lab/20261105_145543/frontier.json, data/_lab/20261105_145555/frontier.json, data/_lab/20261105_145723/frontier.json, data/_lab/20261105_145733/frontier.json, data/_lab/20261105_150352/frontier.json, data/_lab/20261105_150718/frontier.json, data/_lab/20261105_152052/frontier.json, data/_lab/20261105_152210/frontier.json, data/_lab/20261105_165446/frontier.json, data/_lab/20261105_165543/frontier.json, data/_lab/20261105_170004/frontier.json, data/_lab/20261106_073110/frontier.json, data/_lab/20261106_073117/frontier.json, data/_lab/20261106_073220/frontier.json, data/_lab/20261106_084627/frontier.json, data/_lab/20261106_103935/frontier.json, data/_lab/20261106_103942/frontier.json, data/_lab/20261106_103947/frontier.json, data/_lab/20261106_104414/frontier.json, data/_lab/20261106_104431/frontier.json, data/_lab/20261106_104457/frontier.json, data/_lab/20261106_104519/frontier.json, data/_lab/20261106_104602/frontier.json, data/_lab/20261106_104604/frontier.json, data/_lab/20261106_104608/frontier.json, data/_lab/20261106_104617/frontier.json, data/_lab/20261106_104629/frontier.json, data/_lab/20261106_104638/frontier.json, data/_lab/20261106_104956/frontier.json, data/_lab/20261106_105008/frontier.json, data/_lab/20261106_105019/frontier.json, data/_lab/20261106_105042/frontier.json, data/_lab/20261106_105231/frontier.json, data/_lab/20261106_105241/frontier.json, data/_lab/20261106_105254/frontier.json, data/_lab/20261106_105301/frontier.json, data/_lab/20261106_105305/frontier.json, data/_lab/20261106_105540/frontier.json, data/_lab/20261106_105545/frontier.json, data/_lab/20261106_105553/frontier.json, data/_lab/20261106_105603/frontier.json, data/_lab/20261106_105702/frontier.json, data/_lab/20261106_105713/frontier.json, data/_lab/20261106_105720/frontier.json, data/_lab/20261106_105725/frontier.json, data/_lab/20261106_105745/frontier.json, data/_lab/20261106_105754/frontier.json, data/_lab/20261106_110146/frontier.json, data/_lab/20261106_110155/frontier.json, data/_lab/20261106_110203/frontier.json, data/_lab/20261106_110211/frontier.json, data/_lab/20261106_110219/frontier.json, data/_lab/20261106_110553/frontier.json, data/_lab/20261106_121700/frontier.json, data/_lab/20261106_121703/frontier.json, data/_lab/20261106_122313/frontier.json, data/_lab/20261106_122315/frontier.json, data/_lab/20261106_123127/frontier.json, data/_lab/20261106_123132/frontier.json, data/_lab/20261106_123141/frontier.json, data/_lab/20261106_123148/frontier.json, data/_lab/20261106_134916/frontier.json, data/_lab/20261106_134923/frontier.json, data/_lab/20261106_135157/frontier.json, data/_lab/20261106_135336/frontier.json, data/_lab/20261106_135459/frontier.json, data/_lab/20261106_135522/frontier.json, data/_lab/20261106_135533/frontier.json, data/_lab/20261106_140214/frontier.json, data/_lab/20261106_140331/frontier.json, data/_lab/20261106_140404/frontier.json, data/_lab/20261106_225334/frontier.json, data/_lab/20261106_225411/frontier.json, data/_lab/20261106_225413/frontier.json, data/_lab/20261106_225418/frontier.json, data/_lab/20261106_225637/frontier.json, data/_lab/20261106_225849/frontier.json, data/_lab/20261106_230102/frontier.json, data/_lab/20261106_230148/frontier.json, data/_lab/20261106_230239/frontier.json, data/_lab/20261106_230245/frontier.json, data/_lab/20261106_234306/frontier.json, data/_lab/20261106_234311/frontier.json, data/_lab/20261106_235821/frontier.json, data/_lab/20261107_001216/frontier.json, data/_lab/20261107_001220/frontier.json, data/_lab/20261107_003205/frontier.json, data/_lab/20261107_003403/frontier.json, data/_lab/20261107_074202/frontier.json, data/_lab/20261107_074758/frontier.json, data/_lab/20261107_085428/frontier.json, data/_lab/20261107_131640/frontier.json, data/_lab/20261107_131643/frontier.json, data/_lab/20261107_131915/frontier.json, data/_lab/20261107_133930/frontier.json, data/_lab/20261107_133933/frontier.json, data/_lab/20261107_134204/frontier.json, data/_lab/20261108_104126/frontier.json, data/_lab/20261108_104139/frontier.json, data/_lab/20261108_104144/frontier.json, data/_lab/20261108_104149/frontier.json, data/_lab/20261115_052859/frontier.json, data/_lab/20261115_052942/frontier.json, data/_lab/20261115_053022/frontier.json, data/_lab/20261115_053027/frontier.json, data/_lab/20261115_054257/frontier.json, data/_lab/20261115_202720/frontier.json, data/_lab/20261115_202730/frontier.json, data/_lab/20261115_203645/frontier.json, data/_lab/20261115_204052/frontier.json, data/_lab/20261115_204109/frontier.json, data/_lab/20261115_204117/frontier.json, data/_lab/20261116_151150/frontier.json, data/_lab/20261116_151204/frontier.json, data/_lab/20261116_151210/frontier.json, data/_lab/20261116_162832/frontier.json, data/_lab/20261116_162835/frontier.json, data/_lab/20261116_162845/frontier.json, data/_lab/20261116_162919/frontier.json, data/_lab/20261116_162943/frontier.json, data/_lab/20261117_171451/frontier.json, data/_lab/20261117_183228/frontier.json, data/_lab/20261118_164416/frontier.json, data/_lab/20261118_164419/frontier.json, data/_lab/20261118_164837/frontier.json, data/_lab/20261118_164956/frontier.json, data/_lab/20261118_165400/frontier.json, data/_lab/20261118_165431/frontier.json, data/_lab/20261118_165842/frontier.json, data/_lab/20261118_170149/frontier.json, data/_lab/20261118_174330/frontier.json, data/_lab/20261118_174338/frontier.json, data/_lab/20261118_174438/frontier.json, data/_lab/20261118_174444/frontier.json, data/_lab/20261118_174452/frontier.json, data/_lab/20261120_104444/frontier.json
- [AMBIGUOUS] `frontier.light.json` -> candidates: data/frontier.light.json, data/_trash/20261114/labs/20260915_094209/frontier.light.json, data/_trash/20261114/labs/20260915_103021/frontier.light.json, data/_trash/20261114/labs/20260915_103126/frontier.light.json, data/_trash/20261114/labs/20260915_103147/frontier.light.json, data/_lab/20261003_080503/frontier.light.json, data/_lab/20261028_074650/frontier.light.json, data/_lab/20261028_074742/frontier.light.json, data/_lab/20261028_074834/frontier.light.json, data/_lab/20261028_074853/frontier.light.json, data/_lab/20261028_074911/frontier.light.json, data/_lab/20261028_074916/frontier.light.json, data/_lab/20261028_082823/frontier.light.json, data/_lab/20261028_082828/frontier.light.json, data/_lab/20261028_082915/frontier.light.json, data/_lab/20261028_082919/frontier.light.json, data/_lab/20261028_083106/frontier.light.json, data/_lab/20261028_090434/frontier.light.json, data/_lab/20261030_134626/frontier.light.json, data/_lab/20261030_172716/frontier.light.json, data/_lab/20261030_172720/frontier.light.json, data/_lab/20261105_145459/frontier.light.json, data/_lab/20261105_145511/frontier.light.json, data/_lab/20261105_145516/frontier.light.json, data/_lab/20261105_145543/frontier.light.json, data/_lab/20261105_145555/frontier.light.json, data/_lab/20261105_145723/frontier.light.json, data/_lab/20261105_145733/frontier.light.json, data/_lab/20261105_150352/frontier.light.json, data/_lab/20261105_150718/frontier.light.json, data/_lab/20261105_152052/frontier.light.json, data/_lab/20261105_152210/frontier.light.json, data/_lab/20261105_165446/frontier.light.json, data/_lab/20261105_165543/frontier.light.json, data/_lab/20261105_170004/frontier.light.json, data/_lab/20261106_073110/frontier.light.json, data/_lab/20261106_073117/frontier.light.json, data/_lab/20261106_073220/frontier.light.json, data/_lab/20261106_084627/frontier.light.json, data/_lab/20261106_103935/frontier.light.json, data/_lab/20261106_103942/frontier.light.json, data/_lab/20261106_103947/frontier.light.json, data/_lab/20261106_104414/frontier.light.json, data/_lab/20261106_104431/frontier.light.json, data/_lab/20261106_104457/frontier.light.json, data/_lab/20261106_104519/frontier.light.json, data/_lab/20261106_104602/frontier.light.json, data/_lab/20261106_104604/frontier.light.json, data/_lab/20261106_104608/frontier.light.json, data/_lab/20261106_104617/frontier.light.json, data/_lab/20261106_104629/frontier.light.json, data/_lab/20261106_104638/frontier.light.json, data/_lab/20261106_104956/frontier.light.json, data/_lab/20261106_105008/frontier.light.json, data/_lab/20261106_105019/frontier.light.json, data/_lab/20261106_105042/frontier.light.json, data/_lab/20261106_105231/frontier.light.json, data/_lab/20261106_105241/frontier.light.json, data/_lab/20261106_105254/frontier.light.json, data/_lab/20261106_105301/frontier.light.json, data/_lab/20261106_105305/frontier.light.json, data/_lab/20261106_105540/frontier.light.json, data/_lab/20261106_105545/frontier.light.json, data/_lab/20261106_105553/frontier.light.json, data/_lab/20261106_105603/frontier.light.json, data/_lab/20261106_105702/frontier.light.json, data/_lab/20261106_105713/frontier.light.json, data/_lab/20261106_105720/frontier.light.json, data/_lab/20261106_105725/frontier.light.json, data/_lab/20261106_105745/frontier.light.json, data/_lab/20261106_105754/frontier.light.json, data/_lab/20261106_110146/frontier.light.json, data/_lab/20261106_110155/frontier.light.json, data/_lab/20261106_110203/frontier.light.json, data/_lab/20261106_110211/frontier.light.json, data/_lab/20261106_110219/frontier.light.json, data/_lab/20261106_110553/frontier.light.json, data/_lab/20261106_121700/frontier.light.json, data/_lab/20261106_121703/frontier.light.json, data/_lab/20261106_122313/frontier.light.json, data/_lab/20261106_122315/frontier.light.json, data/_lab/20261106_123127/frontier.light.json, data/_lab/20261106_123132/frontier.light.json, data/_lab/20261106_123141/frontier.light.json, data/_lab/20261106_123148/frontier.light.json, data/_lab/20261106_134916/frontier.light.json, data/_lab/20261106_134923/frontier.light.json, data/_lab/20261106_135157/frontier.light.json, data/_lab/20261106_135336/frontier.light.json, data/_lab/20261106_135459/frontier.light.json, data/_lab/20261106_135522/frontier.light.json, data/_lab/20261106_135533/frontier.light.json, data/_lab/20261106_140214/frontier.light.json, data/_lab/20261106_140331/frontier.light.json, data/_lab/20261106_140404/frontier.light.json, data/_lab/20261106_225334/frontier.light.json, data/_lab/20261106_225411/frontier.light.json, data/_lab/20261106_225413/frontier.light.json, data/_lab/20261106_225418/frontier.light.json, data/_lab/20261106_225637/frontier.light.json, data/_lab/20261106_225849/frontier.light.json, data/_lab/20261106_230102/frontier.light.json, data/_lab/20261106_230148/frontier.light.json, data/_lab/20261106_230239/frontier.light.json, data/_lab/20261106_230245/frontier.light.json, data/_lab/20261106_234306/frontier.light.json, data/_lab/20261106_234311/frontier.light.json, data/_lab/20261106_235821/frontier.light.json, data/_lab/20261107_001216/frontier.light.json, data/_lab/20261107_001220/frontier.light.json, data/_lab/20261107_003205/frontier.light.json, data/_lab/20261107_003403/frontier.light.json, data/_lab/20261107_074202/frontier.light.json, data/_lab/20261107_074758/frontier.light.json, data/_lab/20261107_085428/frontier.light.json, data/_lab/20261107_131640/frontier.light.json, data/_lab/20261107_131643/frontier.light.json, data/_lab/20261107_131915/frontier.light.json, data/_lab/20261107_133930/frontier.light.json, data/_lab/20261107_133933/frontier.light.json, data/_lab/20261107_134204/frontier.light.json, data/_lab/20261108_104126/frontier.light.json, data/_lab/20261108_104139/frontier.light.json, data/_lab/20261108_104144/frontier.light.json, data/_lab/20261108_104149/frontier.light.json, data/_lab/20261115_052859/frontier.light.json, data/_lab/20261115_052942/frontier.light.json, data/_lab/20261115_053022/frontier.light.json, data/_lab/20261115_053027/frontier.light.json, data/_lab/20261115_054257/frontier.light.json, data/_lab/20261115_202720/frontier.light.json, data/_lab/20261115_202730/frontier.light.json, data/_lab/20261115_203645/frontier.light.json, data/_lab/20261115_204052/frontier.light.json, data/_lab/20261115_204109/frontier.light.json, data/_lab/20261115_204117/frontier.light.json, data/_lab/20261116_151150/frontier.light.json, data/_lab/20261116_151204/frontier.light.json, data/_lab/20261116_151210/frontier.light.json, data/_lab/20261116_162832/frontier.light.json, data/_lab/20261116_162835/frontier.light.json, data/_lab/20261116_162845/frontier.light.json, data/_lab/20261116_162919/frontier.light.json, data/_lab/20261116_162943/frontier.light.json, data/_lab/20261117_171451/frontier.light.json, data/_lab/20261117_183228/frontier.light.json, data/_lab/20261118_164416/frontier.light.json, data/_lab/20261118_164419/frontier.light.json, data/_lab/20261118_164837/frontier.light.json, data/_lab/20261118_164956/frontier.light.json, data/_lab/20261118_165400/frontier.light.json, data/_lab/20261118_165431/frontier.light.json, data/_lab/20261118_165842/frontier.light.json, data/_lab/20261118_170149/frontier.light.json, data/_lab/20261118_174330/frontier.light.json, data/_lab/20261118_174338/frontier.light.json, data/_lab/20261118_174438/frontier.light.json, data/_lab/20261118_174444/frontier.light.json, data/_lab/20261118_174452/frontier.light.json, data/_lab/20261120_104444/frontier.light.json, data/_crash_recovery_20261120/restore_set/frontier.light.json, data/_crash_recovery_20261120/shadow4/frontier.light.json, data/_crash_recovery_20261120/shadow5/frontier.light.json, data/_crash_recovery_20261120/shadow6/frontier.light.json
- [AMBIGUOUS] `garden_knowledge.json` -> candidates: data/garden_knowledge.json, data/_lab/20260928_081908/garden_knowledge.json, data/_lab/20260928_173422/garden_knowledge.json
- [AMBIGUOUS] `keepsakes.json` -> candidates: data/keepsakes.json, data/_trash/20261119/boot_backups/state_20261116_100503/keepsakes.json, data/_trash/20261117/boot_backups/state_20261114_141446/keepsakes.json, data/_trash/20261114/boot_backups/state_20261031_215612/keepsakes.json, data/_lab/20261120_103403/sandbox_data/keepsakes.json, data/_lab/20261118_170303/sandbox_data/keepsakes.json, data/_lab/20261118_165748/sandbox_data/keepsakes.json, data/_lab/20261118_165253/sandbox_data/keepsakes.json, data/_lab/20261118_161657/sandbox_data/keepsakes.json, data/_lab/20261118_161507/sandbox_data/keepsakes.json, data/_lab/20261115_053548/sandbox_data/keepsakes.json, data/_lab/20261114_213331/sandbox_data/keepsakes.json, data/_lab/20261114_023004/sandbox_data/keepsakes.json, data/_lab/20261019_220628/sandbox_data/keepsakes.json
- [AMBIGUOUS] `position.json` -> candidates: data/position.json, data/_lab/20261118_164521/position.json
- [AMBIGUOUS] `procedures.json` -> candidates: data/procedures.json, data/_lab/20260928_140039/procedures.json, data/_lab/20260928_140112/procedures.json, data/_lab/20260928_140144/procedures.json, data/_lab/20261004_164903/procedures.json, data/_lab/20261004_174206/procedures.json, data/_lab/20261004_180002/procedures.json, data/_lab/20261004_205329/procedures.json, data/_lab/20261005_081052/procedures.json, data/_lab/20261017_221937/procedures.json, data/_lab/20261017_222149/procedures.json, data/_lab/20261017_222218/procedures.json, data/_lab/20261017_222838/procedures.json, data/_lab/20261028_130358/procedures.json, data/_lab/20261028_130506/procedures.json, data/_lab/20261028_130749/procedures.json, data/_lab/20261028_130846/procedures.json, data/_lab/20261028_130926/procedures.json, data/_lab/20261028_131022/procedures.json, data/_lab/20261028_173308/procedures.json, data/_lab/20261028_173644/procedures.json, data/_lab/20261028_173740/procedures.json, data/_lab/20261028_173818/procedures.json, data/_lab/20261029_160832/procedures.json, data/_lab/20261029_160945/procedures.json, data/_lab/20261029_161202/procedures.json, data/_lab/20261029_161240/procedures.json, data/_lab/20261029_161318/procedures.json, data/_lab/20261029_174014/procedures.json, data/_lab/20261029_180914/procedures.json, data/_lab/20261105_151615/procedures.json, data/_lab/20261105_151654/procedures.json, data/_lab/20261105_151942/procedures.json, data/_lab/20261114_012536/procedures.json, data/_lab/20261115_053933/procedures.json, data/_lab/20261115_054038/procedures.json, data/_lab/20261115_054920/procedures.json, data/_lab/20261118_164620/procedures.json, data/_lab/20261118_164648/procedures.json, data/_lab/20261118_165309/procedures.json, data/_lab/20261118_170054/procedures.json
- [AMBIGUOUS] `procedures_log.jsonl` -> candidates: data/procedures_log.jsonl, data/_lab/20260928_140039/procedures_log.jsonl, data/_lab/20260928_140112/procedures_log.jsonl, data/_lab/20260928_140144/procedures_log.jsonl, data/_lab/20261004_164903/procedures_log.jsonl, data/_lab/20261004_174206/procedures_log.jsonl, data/_lab/20261004_180002/procedures_log.jsonl, data/_lab/20261004_205329/procedures_log.jsonl, data/_lab/20261005_081052/procedures_log.jsonl, data/_lab/20261017_221937/procedures_log.jsonl, data/_lab/20261017_222149/procedures_log.jsonl, data/_lab/20261017_222218/procedures_log.jsonl, data/_lab/20261017_222838/procedures_log.jsonl, data/_lab/20261028_130358/procedures_log.jsonl, data/_lab/20261028_130506/procedures_log.jsonl, data/_lab/20261028_130749/procedures_log.jsonl, data/_lab/20261028_130846/procedures_log.jsonl, data/_lab/20261028_130926/procedures_log.jsonl, data/_lab/20261028_131022/procedures_log.jsonl, data/_lab/20261028_173308/procedures_log.jsonl, data/_lab/20261028_173644/procedures_log.jsonl, data/_lab/20261028_173740/procedures_log.jsonl, data/_lab/20261028_173818/procedures_log.jsonl, data/_lab/20261029_160832/procedures_log.jsonl, data/_lab/20261029_160945/procedures_log.jsonl, data/_lab/20261029_161202/procedures_log.jsonl, data/_lab/20261029_161240/procedures_log.jsonl, data/_lab/20261029_161318/procedures_log.jsonl, data/_lab/20261029_174014/procedures_log.jsonl, data/_lab/20261029_180914/procedures_log.jsonl, data/_lab/20261105_151615/procedures_log.jsonl, data/_lab/20261105_151654/procedures_log.jsonl, data/_lab/20261105_151942/procedures_log.jsonl, data/_lab/20261114_012536/procedures_log.jsonl, data/_lab/20261115_053933/procedures_log.jsonl, data/_lab/20261115_054038/procedures_log.jsonl, data/_lab/20261115_054920/procedures_log.jsonl, data/_lab/20261118_164620/procedures_log.jsonl, data/_lab/20261118_164648/procedures_log.jsonl, data/_lab/20261118_165309/procedures_log.jsonl, data/_lab/20261118_170054/procedures_log.jsonl
- [AMBIGUOUS] `provisions.json` -> candidates: data/provisions.json, data/_trash/20261114/labs/20260915_100807/provisions.json, data/_lab/20260925_095016/provisions.json, data/_lab/20261003_080503/provisions.json, data/_lab/20261004_164903/provisions.json, data/_lab/20261004_174206/provisions.json, data/_lab/20261004_180002/provisions.json, data/_lab/20261004_205329/provisions.json, data/_lab/20261005_081052/provisions.json, data/_lab/20261017_221844/provisions.json, data/_lab/20261017_221937/provisions.json, data/_lab/20261017_222149/provisions.json, data/_lab/20261017_222218/provisions.json, data/_lab/20261017_222838/provisions.json, data/_lab/20261028_130358/provisions.json, data/_lab/20261028_130506/provisions.json, data/_lab/20261028_130749/provisions.json, data/_lab/20261028_130846/provisions.json, data/_lab/20261028_130926/provisions.json, data/_lab/20261028_131022/provisions.json, data/_lab/20261028_173308/provisions.json, data/_lab/20261028_173644/provisions.json, data/_lab/20261028_173740/provisions.json, data/_lab/20261028_173818/provisions.json, data/_lab/20261029_160832/provisions.json, data/_lab/20261029_160945/provisions.json, data/_lab/20261029_161202/provisions.json, data/_lab/20261029_161240/provisions.json, data/_lab/20261029_161318/provisions.json, data/_lab/20261029_174014/provisions.json, data/_lab/20261029_180914/provisions.json, data/_lab/20261105_151615/provisions.json, data/_lab/20261105_151654/provisions.json, data/_lab/20261105_151942/provisions.json, data/_lab/20261114_012536/provisions.json, data/_lab/20261115_053933/provisions.json, data/_lab/20261115_054038/provisions.json, data/_lab/20261115_054920/provisions.json, data/_lab/20261115_203758/provisions.json, data/_lab/20261115_203950/provisions.json, data/_lab/20261117_165327/provisions.json, data/_lab/20261117_183542/provisions.json, data/_lab/20261118_164648/provisions.json, data/_lab/20261118_165309/provisions.json, data/_lab/20261118_170054/provisions.json
- [AMBIGUOUS] `provisions_log.jsonl` -> candidates: data/provisions_log.jsonl, data/_lab/20260925_095016/provisions_log.jsonl, data/_lab/20261004_164903/provisions_log.jsonl, data/_lab/20261004_174206/provisions_log.jsonl, data/_lab/20261004_180002/provisions_log.jsonl, data/_lab/20261004_205329/provisions_log.jsonl, data/_lab/20261005_081052/provisions_log.jsonl, data/_lab/20261017_221844/provisions_log.jsonl, data/_lab/20261017_221937/provisions_log.jsonl, data/_lab/20261017_222149/provisions_log.jsonl, data/_lab/20261017_222218/provisions_log.jsonl, data/_lab/20261017_222838/provisions_log.jsonl, data/_lab/20261028_130358/provisions_log.jsonl, data/_lab/20261028_130506/provisions_log.jsonl, data/_lab/20261028_130749/provisions_log.jsonl, data/_lab/20261028_130846/provisions_log.jsonl, data/_lab/20261028_130926/provisions_log.jsonl, data/_lab/20261028_131022/provisions_log.jsonl, data/_lab/20261028_173308/provisions_log.jsonl, data/_lab/20261028_173644/provisions_log.jsonl, data/_lab/20261028_173740/provisions_log.jsonl, data/_lab/20261028_173818/provisions_log.jsonl, data/_lab/20261029_160832/provisions_log.jsonl, data/_lab/20261029_160945/provisions_log.jsonl, data/_lab/20261029_161202/provisions_log.jsonl, data/_lab/20261029_161240/provisions_log.jsonl, data/_lab/20261029_161318/provisions_log.jsonl, data/_lab/20261029_174014/provisions_log.jsonl, data/_lab/20261029_180914/provisions_log.jsonl, data/_lab/20261105_151615/provisions_log.jsonl, data/_lab/20261105_151654/provisions_log.jsonl, data/_lab/20261105_151942/provisions_log.jsonl, data/_lab/20261114_012536/provisions_log.jsonl, data/_lab/20261115_053933/provisions_log.jsonl, data/_lab/20261115_054038/provisions_log.jsonl, data/_lab/20261115_054920/provisions_log.jsonl, data/_lab/20261115_203950/provisions_log.jsonl, data/_lab/20261117_165327/provisions_log.jsonl, data/_lab/20261117_183542/provisions_log.jsonl, data/_lab/20261118_164648/provisions_log.jsonl, data/_lab/20261118_165309/provisions_log.jsonl, data/_lab/20261118_170054/provisions_log.jsonl
- [AMBIGUOUS] `room_state.json` -> candidates: data/room_state.json, data/_lab/20260923_195154/room_state.json, data/_lab/20260923_195447/room_state.json, data/_lab/20260923_195457/room_state.json, data/_lab/20260928_173422/room_state.json, data/_lab/20261004_164903/room_state.json, data/_lab/20261004_174206/room_state.json, data/_lab/20261004_180002/room_state.json, data/_lab/20261004_205329/room_state.json, data/_lab/20261005_081052/room_state.json, data/_lab/20261017_221937/room_state.json, data/_lab/20261017_222149/room_state.json, data/_lab/20261017_222218/room_state.json, data/_lab/20261017_222838/room_state.json, data/_lab/20261028_130358/room_state.json, data/_lab/20261028_130506/room_state.json, data/_lab/20261028_130749/room_state.json, data/_lab/20261028_130846/room_state.json, data/_lab/20261028_130926/room_state.json, data/_lab/20261028_131022/room_state.json, data/_lab/20261028_173308/room_state.json, data/_lab/20261028_173644/room_state.json, data/_lab/20261028_173740/room_state.json, data/_lab/20261028_173818/room_state.json, data/_lab/20261029_160832/room_state.json, data/_lab/20261029_160945/room_state.json, data/_lab/20261029_161202/room_state.json, data/_lab/20261029_161240/room_state.json, data/_lab/20261029_161318/room_state.json, data/_lab/20261029_174014/room_state.json, data/_lab/20261029_180914/room_state.json, data/_lab/20261105_151615/room_state.json, data/_lab/20261105_151654/room_state.json, data/_lab/20261105_151942/room_state.json, data/_lab/20261114_012536/room_state.json, data/_lab/20261115_052850/room_state.json, data/_lab/20261115_052901/room_state.json, data/_lab/20261115_053933/room_state.json, data/_lab/20261115_054038/room_state.json, data/_lab/20261115_054920/room_state.json, data/_lab/20261118_164521/room_state.json, data/_lab/20261118_164648/room_state.json, data/_lab/20261118_165309/room_state.json, data/_lab/20261118_170054/room_state.json, data/_crash_recovery_20261120/post_crash_live/room_state.json, data/_crash_recovery_20261120/restore_set/room_state.json, data/_crash_recovery_20261120/shadow4/room_state.json, data/_crash_recovery_20261120/shadow5/room_state.json, data/_crash_recovery_20261120/shadow6/room_state.json
- [AMBIGUOUS] `smell_field.json` -> candidates: data/smell_field.json, data/_lab/20260928_081908/smell_field.json, data/_lab/20260928_173422/smell_field.json, data/_crash_recovery_20261120/post_crash_live/smell_field.json, data/_crash_recovery_20261120/restore_set/smell_field.json, data/_crash_recovery_20261120/shadow4/smell_field.json, data/_crash_recovery_20261120/shadow5/smell_field.json, data/_crash_recovery_20261120/shadow6/smell_field.json
- [OK] `smell_percepts_shadow.jsonl` -> data/smell_percepts_shadow.jsonl (63135 lines)
- [AMBIGUOUS] `sound_knowledge.json` -> candidates: data/sound_knowledge.json, data/_crash_recovery_20261120/post_crash_live/sound_knowledge.json, data/_crash_recovery_20261120/restore_set/sound_knowledge.json, data/_crash_recovery_20261120/shadow4/sound_knowledge.json, data/_crash_recovery_20261120/shadow5/sound_knowledge.json, data/_crash_recovery_20261120/shadow6/sound_knowledge.json
- [AMBIGUOUS] `supply.json` -> candidates: data/supply.json, data/_crash_recovery_20261120/post_crash_live/supply.json, data/_crash_recovery_20261120/restore_set/supply.json, data/_crash_recovery_20261120/shadow4/supply.json, data/_crash_recovery_20261120/shadow5/supply.json, data/_crash_recovery_20261120/shadow6/supply.json
- [OK] `supply_log.jsonl` -> data/supply_log.jsonl (34 lines)
- [AMBIGUOUS] `transport_lines.json` -> candidates: data/transport_lines.json, data/_crash_recovery_20261120/post_crash_live/transport_lines.json, data/_crash_recovery_20261120/restore_set/transport_lines.json, data/_crash_recovery_20261120/shadow4/transport_lines.json, data/_crash_recovery_20261120/shadow5/transport_lines.json, data/_crash_recovery_20261120/shadow6/transport_lines.json
- [OK] `transport_shadow.jsonl` -> data/transport_shadow.jsonl (55612 lines)
- [AMBIGUOUS] `world_objects.json` -> candidates: data/world_objects.json, data/_trash/20261114/labs/20260915_094627/world_objects.json, data/_trash/20261114/labs/20260915_094716/world_objects.json, data/_trash/20261114/labs/20260915_094809/world_objects.json, data/_lab/20261003_080246/world_objects.json, data/_lab/20261004_164903/world_objects.json, data/_lab/20261004_174206/world_objects.json, data/_lab/20261004_180002/world_objects.json, data/_lab/20261004_205329/world_objects.json, data/_lab/20261005_081052/world_objects.json, data/_lab/20261017_221844/world_objects.json, data/_lab/20261017_221937/world_objects.json, data/_lab/20261017_222149/world_objects.json, data/_lab/20261017_222218/world_objects.json, data/_lab/20261017_222838/world_objects.json, data/_lab/20261028_130358/world_objects.json, data/_lab/20261028_130506/world_objects.json, data/_lab/20261028_130749/world_objects.json, data/_lab/20261028_130846/world_objects.json, data/_lab/20261028_130926/world_objects.json, data/_lab/20261028_131022/world_objects.json, data/_lab/20261028_173308/world_objects.json, data/_lab/20261028_173644/world_objects.json, data/_lab/20261028_173740/world_objects.json, data/_lab/20261028_173818/world_objects.json, data/_lab/20261029_160832/world_objects.json, data/_lab/20261029_160945/world_objects.json, data/_lab/20261029_161202/world_objects.json, data/_lab/20261029_161240/world_objects.json, data/_lab/20261029_161318/world_objects.json, data/_lab/20261029_174014/world_objects.json, data/_lab/20261029_180914/world_objects.json, data/_lab/20261105_151615/world_objects.json, data/_lab/20261105_151654/world_objects.json, data/_lab/20261105_151942/world_objects.json, data/_lab/20261114_012536/world_objects.json, data/_lab/20261115_053933/world_objects.json, data/_lab/20261115_054038/world_objects.json, data/_lab/20261115_054920/world_objects.json, data/_lab/20261115_203950/world_objects.json, data/_lab/20261117_165327/world_objects.json, data/_lab/20261117_183542/world_objects.json, data/_lab/20261118_164648/world_objects.json, data/_lab/20261118_165309/world_objects.json, data/_lab/20261118_170054/world_objects.json
- [AMBIGUOUS] `world_traces.json` -> candidates: data/world_traces.json, data/_trash/20261119/boot_backups/state_20261116_100503/world_traces.json, data/_trash/20261117/boot_backups/state_20261114_141446/world_traces.json, data/_trash/20261114/boot_backups/state_20261031_215612/world_traces.json, data/_lab/20261028_130358/world_traces.json, data/_lab/20261028_130506/world_traces.json, data/_lab/20261028_130749/world_traces.json, data/_lab/20261028_130846/world_traces.json, data/_lab/20261028_130926/world_traces.json, data/_lab/20261028_173308/world_traces.json, data/_lab/20261028_173644/world_traces.json, data/_lab/20261028_173818/world_traces.json, data/_lab/20261029_160832/world_traces.json, data/_lab/20261029_160945/world_traces.json, data/_lab/20261029_161202/world_traces.json, data/_lab/20261029_161240/world_traces.json, data/_lab/20261029_161318/world_traces.json, data/_lab/20261029_174014/world_traces.json, data/_lab/20261029_180914/world_traces.json, data/_lab/20261105_151654/world_traces.json, data/_lab/20261115_053933/world_traces.json, data/_lab/20261118_164648/world_traces.json

### affect_drives_item_c_somatic_note (staged)
**Idea:** Item C of the affect/drives plan: a rare, threshold-gated body-state line (drowsy or strained band) in the idle-thought seed, folding drowsiness_phase section 2. Shadow logger built 2026-11-18 (J-4405); live flag SOMATIC_NOTE not built, awaiting about 2 days of shadow rows and a founder go.
**Code files:**
- [OK] `core/drowsy.py`
- [OK] `core/phrasing.py`
- [OK] `core/somatic_note.py`
- [OK] `nodes/inner_monologue_node.py`
- [OK] `scripts/test_somatic_note_shadow.py`
**Data/evidence files:**
- [OK] `data/somatic_note_shadow.jsonl` -> data/somatic_note_shadow.jsonl (2 lines)

### affect_drives_item_d_satisfaction_normalisation (staged)
**Idea:** 🔵 Affect Drives Item D redesign: shadow-only windowed satisfaction normalisation, staged and held for founder go-ahead (J-4315, F-5088)
**Code files:**
- [OK] `nodes/subconscious_node.py`
**Data/evidence files:**
- [OK] `data/satisfaction_log.jsonl` -> data/satisfaction_log.jsonl (184521 lines)
- [MISSING] `data/satisfaction_norm_shadow.jsonl`

### affect_drives_item_e_labeling_accessibility (staged)
**Idea:** Item E of the affect/drives plan: when Du genuinely names a present negative feeling, store his own words as a recallable fragment so later thought can meet it. Staged design only; blocked on the Phase-0 detector false-positive review and a founder decide.
**Code files:**
- [OK] `core/affect_labeling.py`
- [OK] `core/schema.py`
**Data/evidence files:**
- [MISSING] `data/affect_label_would_store.jsonl`
- [OK] `data/affect_labeling_log.jsonl` -> data/affect_labeling_log.jsonl (20 lines)

### affect_drives_item_g_va_steering (staged)
**Idea:** Item G of the affect/drives plan: add a bounded valence-congruence term to retrieval (sub-path 2) in shadow first; activation steering (sub-path 1) ruled NO by D-0862. Shadow ranker built, flag off, no rows yet.
**Code files:**
- [OK] `core/memory/store.py`
- [OK] `core/valence_rank_shadow.py`
**Data/evidence files:**
- [MISSING] `data/valence_rank_shadow.jsonl`

### ambiguity_window (staged)
**Idea:** Ambiguity Window (I-0099, 2026-10-19) — a short deterministic lookback (last sentences, Du's recent actions, Travis's last message) that settles anaphora like 'I plant them now'; DESIGNED, nothing coded
**Code files:**
- [OK] `core/ambiguity_window.py`
- [OK] `core/conversational_action.py`
**Data/evidence files:**
- [OK] `data/conversational_action_log.jsonl` -> data/conversational_action_log.jsonl (92 lines)
- [OK] `data/hands_trace.jsonl` -> data/hands_trace.jsonl (67256 lines)

### antigravity_ecosystem_proposals (staged)
**Idea:** ⚪ PARTIAL — inbox of 17 external framework/tool proposals from Antigravity's 2026-08-25 research sweep, captured in docs/staged/antigravity_ecosystem_proposals.md. D-0054 (Travis, 2026-08-27) investigation-first gate: 6 of 9 group-A items now resolved (1 promoted to lod_staged_retrieval.md, 3 archived/killed, 1 registered); items 5/7/8 still only specced (D-0114 open). These are Antigravity's evaluations, not verified findings; every item needs re-grounding in Du's ACTUAL architecture (the blueprint's 'CriticNode/ExecutiveNode/12-node' vocabulary maps only loosely onto real, mostly-dormant node files).
**Code files:**
- [OK] `climate_engine.py` -> core/climate_engine.py
- [MISSING] `cognitive_mmu.py`
- [OK] `core/associative_recall.py`
- [OK] `core/audio_features.py`
- [OK] `core/judge_panel.py`
- [OK] `core/lane2.py`
- [OK] `core/listening.py`
- [OK] `core/memory/store.py`
- [OK] `core/memory_edges.py`
- [OK] `core/refinery.py`
- [OK] `core/schema.py`
- [OK] `core/sensorium.py`
- [OK] `core/soundscape.py`
- [OK] `nodes/critic_node.py`
- [OK] `nodes/executive_node.py`
- [OK] `satisfaction.py` -> core/satisfaction.py
- [OK] `scripts/lod_retrieval_lab.py`
- [OK] `scripts/play_the_record.py`
- [OK] `tension_ledger.py` -> core/tension_ledger.py
**Data/evidence files:**
- [OK] `data/frontier.json` -> data/frontier.json (18849855B)
- [OK] `data/judge_panel_log.jsonl` -> data/judge_panel_log.jsonl (82030 lines)
- [OK] `data/llm_calls.jsonl` -> data/llm_calls.jsonl (7185 lines)
- [OK] `data/lod_retrieval_lab_shadow.jsonl` -> data/lod_retrieval_lab_shadow.jsonl (122 lines)
- [OK] `data/subconscious_state.json` -> data/subconscious_state.json (3790797B)
- [OK] `data/training/executive.jsonl` -> data/training/executive.jsonl (4747 lines)
- [AMBIGUOUS] `satisfaction_log.jsonl` -> candidates: data/satisfaction_log.jsonl, data/_lab/20261028_074834/satisfaction_log.jsonl, data/_lab/20261028_074853/satisfaction_log.jsonl, data/_lab/20261028_074911/satisfaction_log.jsonl, data/_lab/20261028_074916/satisfaction_log.jsonl, data/_lab/20261028_082823/satisfaction_log.jsonl, data/_lab/20261028_082828/satisfaction_log.jsonl, data/_lab/20261028_082915/satisfaction_log.jsonl, data/_lab/20261028_082919/satisfaction_log.jsonl, data/_lab/20261028_083106/satisfaction_log.jsonl, data/_lab/20261028_090434/satisfaction_log.jsonl, data/_lab/20261030_134626/satisfaction_log.jsonl, data/_lab/20261030_172716/satisfaction_log.jsonl, data/_lab/20261030_172720/satisfaction_log.jsonl, data/_lab/20261105_145459/satisfaction_log.jsonl, data/_lab/20261105_145511/satisfaction_log.jsonl, data/_lab/20261105_145516/satisfaction_log.jsonl, data/_lab/20261105_145543/satisfaction_log.jsonl, data/_lab/20261105_145555/satisfaction_log.jsonl, data/_lab/20261105_145723/satisfaction_log.jsonl, data/_lab/20261105_145733/satisfaction_log.jsonl, data/_lab/20261105_150352/satisfaction_log.jsonl, data/_lab/20261105_152052/satisfaction_log.jsonl, data/_lab/20261105_152210/satisfaction_log.jsonl, data/_lab/20261105_165543/satisfaction_log.jsonl, data/_lab/20261105_170004/satisfaction_log.jsonl, data/_lab/20261106_073117/satisfaction_log.jsonl, data/_lab/20261106_103935/satisfaction_log.jsonl, data/_lab/20261106_103942/satisfaction_log.jsonl, data/_lab/20261106_104414/satisfaction_log.jsonl, data/_lab/20261106_104431/satisfaction_log.jsonl, data/_lab/20261106_104457/satisfaction_log.jsonl, data/_lab/20261106_104519/satisfaction_log.jsonl, data/_lab/20261106_104602/satisfaction_log.jsonl, data/_lab/20261106_104604/satisfaction_log.jsonl, data/_lab/20261106_104608/satisfaction_log.jsonl, data/_lab/20261106_104617/satisfaction_log.jsonl, data/_lab/20261106_104629/satisfaction_log.jsonl, data/_lab/20261106_104638/satisfaction_log.jsonl, data/_lab/20261106_104956/satisfaction_log.jsonl, data/_lab/20261106_105008/satisfaction_log.jsonl, data/_lab/20261106_105019/satisfaction_log.jsonl, data/_lab/20261106_105231/satisfaction_log.jsonl, data/_lab/20261106_105241/satisfaction_log.jsonl, data/_lab/20261106_105254/satisfaction_log.jsonl, data/_lab/20261106_105301/satisfaction_log.jsonl, data/_lab/20261106_105305/satisfaction_log.jsonl, data/_lab/20261106_105540/satisfaction_log.jsonl, data/_lab/20261106_105545/satisfaction_log.jsonl, data/_lab/20261106_105553/satisfaction_log.jsonl, data/_lab/20261106_105603/satisfaction_log.jsonl, data/_lab/20261106_105702/satisfaction_log.jsonl, data/_lab/20261106_105713/satisfaction_log.jsonl, data/_lab/20261106_105720/satisfaction_log.jsonl, data/_lab/20261106_105725/satisfaction_log.jsonl, data/_lab/20261106_105745/satisfaction_log.jsonl, data/_lab/20261106_105754/satisfaction_log.jsonl, data/_lab/20261106_110146/satisfaction_log.jsonl, data/_lab/20261106_110155/satisfaction_log.jsonl, data/_lab/20261106_110203/satisfaction_log.jsonl, data/_lab/20261106_110219/satisfaction_log.jsonl, data/_lab/20261106_121700/satisfaction_log.jsonl, data/_lab/20261106_121703/satisfaction_log.jsonl, data/_lab/20261106_122313/satisfaction_log.jsonl, data/_lab/20261106_122315/satisfaction_log.jsonl, data/_lab/20261106_123127/satisfaction_log.jsonl, data/_lab/20261106_123132/satisfaction_log.jsonl, data/_lab/20261106_123141/satisfaction_log.jsonl, data/_lab/20261106_123148/satisfaction_log.jsonl, data/_lab/20261106_134916/satisfaction_log.jsonl, data/_lab/20261106_134923/satisfaction_log.jsonl, data/_lab/20261106_135157/satisfaction_log.jsonl, data/_lab/20261106_135336/satisfaction_log.jsonl, data/_lab/20261106_135459/satisfaction_log.jsonl, data/_lab/20261106_135522/satisfaction_log.jsonl, data/_lab/20261106_135533/satisfaction_log.jsonl, data/_lab/20261106_140214/satisfaction_log.jsonl, data/_lab/20261106_140331/satisfaction_log.jsonl, data/_lab/20261106_140404/satisfaction_log.jsonl, data/_lab/20261106_225334/satisfaction_log.jsonl, data/_lab/20261106_225411/satisfaction_log.jsonl, data/_lab/20261106_225413/satisfaction_log.jsonl, data/_lab/20261106_225637/satisfaction_log.jsonl, data/_lab/20261106_225849/satisfaction_log.jsonl, data/_lab/20261106_230102/satisfaction_log.jsonl, data/_lab/20261106_230148/satisfaction_log.jsonl, data/_lab/20261106_230239/satisfaction_log.jsonl, data/_lab/20261106_230245/satisfaction_log.jsonl, data/_lab/20261106_234306/satisfaction_log.jsonl, data/_lab/20261106_234311/satisfaction_log.jsonl, data/_lab/20261107_001220/satisfaction_log.jsonl, data/_lab/20261107_003205/satisfaction_log.jsonl, data/_lab/20261107_003403/satisfaction_log.jsonl, data/_lab/20261107_074202/satisfaction_log.jsonl, data/_lab/20261107_074758/satisfaction_log.jsonl, data/_lab/20261107_085428/satisfaction_log.jsonl, data/_lab/20261107_131640/satisfaction_log.jsonl, data/_lab/20261107_131643/satisfaction_log.jsonl, data/_lab/20261107_133930/satisfaction_log.jsonl, data/_lab/20261107_133933/satisfaction_log.jsonl, data/_lab/20261108_104126/satisfaction_log.jsonl, data/_lab/20261108_104139/satisfaction_log.jsonl, data/_lab/20261108_104144/satisfaction_log.jsonl, data/_lab/20261108_104149/satisfaction_log.jsonl, data/_lab/20261115_052859/satisfaction_log.jsonl, data/_lab/20261115_052942/satisfaction_log.jsonl, data/_lab/20261115_053022/satisfaction_log.jsonl, data/_lab/20261115_054257/satisfaction_log.jsonl, data/_lab/20261115_202720/satisfaction_log.jsonl, data/_lab/20261115_202730/satisfaction_log.jsonl, data/_lab/20261115_203645/satisfaction_log.jsonl, data/_lab/20261115_204052/satisfaction_log.jsonl, data/_lab/20261115_204109/satisfaction_log.jsonl, data/_lab/20261115_204117/satisfaction_log.jsonl, data/_lab/20261116_151150/satisfaction_log.jsonl, data/_lab/20261116_151204/satisfaction_log.jsonl, data/_lab/20261116_151210/satisfaction_log.jsonl, data/_lab/20261116_162835/satisfaction_log.jsonl, data/_lab/20261116_162919/satisfaction_log.jsonl, data/_lab/20261116_162943/satisfaction_log.jsonl, data/_lab/20261117_171451/satisfaction_log.jsonl, data/_lab/20261117_183228/satisfaction_log.jsonl, data/_lab/20261118_164416/satisfaction_log.jsonl, data/_lab/20261118_164419/satisfaction_log.jsonl, data/_lab/20261118_164837/satisfaction_log.jsonl, data/_lab/20261118_165400/satisfaction_log.jsonl, data/_lab/20261118_165842/satisfaction_log.jsonl, data/_lab/20261118_170149/satisfaction_log.jsonl, data/_lab/20261118_174330/satisfaction_log.jsonl, data/_lab/20261118_174338/satisfaction_log.jsonl, data/_lab/20261118_174438/satisfaction_log.jsonl, data/_lab/20261118_174444/satisfaction_log.jsonl, data/_lab/20261118_174452/satisfaction_log.jsonl

### cat_overhaul (staged)
**Idea:** The cat overhaul (2026-09-05, T-0050 → docs/staged/cat_overhaul.md) — both cats (grey companion + distant black cat); audit found half her life locked behind a name never given, vending-machine tending, no body/food/legs, adapter mis-placement; founder decisions D-1..D-4 open.
**Code files:**
- [OK] `affordances.py` -> core/affordances.py
- [OK] `commitment_trials.py` -> core/commitment_trials.py
- [OK] `companion.py` -> core/companion.py
- [OK] `core/actions.py`
- [OK] `core/cat.py`
- [OK] `core/cat_content.py`
- [OK] `core/cat_sounds.py`
- [OK] `core/dispatch.py`
- [OK] `core/life_traces.py`
- [OK] `core/sensorium.py`
- [OK] `hud/server.py`
- [OK] `inner_monologue_node.py` -> nodes/inner_monologue_node.py
- [OK] `life.py` -> core/life.py
- [OK] `orchestrator.py` -> core/orchestrator.py
- [OK] `soundscape.py` -> core/soundscape.py
**Data/evidence files:**
- [OK] `data/cat_call_ledger.jsonl` -> data/cat_call_ledger.jsonl (14 lines)
- [OK] `data/cat_sound_ledger.jsonl` -> data/cat_sound_ledger.jsonl (2761 lines)
- [OK] `data/cat_state.json` -> data/cat_state.json (21774B)
- [OK] `data/provisions.json` -> data/provisions.json (25633B)
- [OK] `data/world_traces.json` -> data/world_traces.json (6120B)
- [AMBIGUOUS] `life_events.jsonl` -> candidates: data/life_events.jsonl, data/_trash/20261114/labs/20260915_094627/life_events.jsonl, data/_trash/20261114/labs/20260915_094716/life_events.jsonl, data/_trash/20261114/labs/20260915_094809/life_events.jsonl, data/_trash/20261114/labs/20260915_100654/life_events.jsonl, data/_trash/20261114/labs/20260915_100807/life_events.jsonl, data/_trash/20261114/labs/20260915_100932/life_events.jsonl, data/_trash/20261114/labs/20260915_101032/life_events.jsonl, data/_trash/20261114/labs/20260915_162958/life_events.jsonl, data/_lab/20260923_195154/life_events.jsonl, data/_lab/20260923_195447/life_events.jsonl, data/_lab/20260923_195457/life_events.jsonl, data/_lab/20261003_075936/life_events.jsonl, data/_lab/20261003_080246/life_events.jsonl, data/_lab/20261118_164521/life_events.jsonl

### chapter_id_repair (staged)
**Idea:** 🟡 Chapter ID Repair (real plan doc created 2026-09-15, J-1048) — core/world_consolidation.py's tag-matching predicate (bug fixed at commit 2d678ab) misfiled reading/study memory fragments under the wrong book's chapter_id by checking only one word of a title's signature. Full-corpus dry-run (J-1001/F-1384): 128 flagged gists across 115 titles, 12,005 fragments already correctly filed against 14,707 misfiled; every one of 32 magnet gists individually fragment-level characterized, zero structural exceptions (F-1370/F-1419). Repair methodology BUILT and verified end to end; one capped first batch scripted and pre-verified. Execution BLOCKED pending a founder ruling — D-0221 open, reopened a third time 2026-09-15. Zero DB writes anywhere in this investigation to date.
**Code files:**
- [OK] `core/essay_lesson.py`
- [OK] `core/grounded_learning.py`
- [OK] `core/world_consolidation.py`
- [MISSING] `job_queue.py`
**Data/evidence files:**
- [OK] `docs/decisions.jsonl` -> docs/decisions.jsonl (880 lines)
- [OK] `docs/job_queue.jsonl` -> docs/job_queue.jsonl (4461 lines)

### closure_law (staged)
**Idea:** The Closure Law (D-0423 ruled A, 2026-10-15) — a met loop becomes a memory; dream arm BUILT in shadow (J-2118, restart-gated, nothing live); pursuit/interrogation arms are stubs
**Code files:**
- [OK] `core/closure.py`
- [OK] `core/closure_gate.py`
- [OK] `core/done_when.py`
- [OK] `core/dream_met.py`
- [OK] `nodes/dream_node.py`
- [OK] `scripts/closure_test.py`
- [OK] `scripts/dream_met_test.py`
**Data/evidence files:**
- [OK] `data/logs/closure_shadow.jsonl` -> data/logs/closure_shadow.jsonl (432 lines)
- [OK] `data/logs/dream_met_carry_shadow.jsonl` -> data/logs/dream_met_carry_shadow.jsonl (156 lines)
- [OK] `data/logs/dream_met_state.jsonl` -> data/logs/dream_met_state.jsonl (595 lines)
- [AMBIGUOUS] `dream_log.jsonl` -> candidates: data/dream_log.jsonl, data/_lab/20261015_135649/dream_log.jsonl, data/_lab/20261015_135717/dream_log.jsonl, data/_lab/20261015_135718/dream_log.jsonl, data/_lab/20261015_135934/dream_log.jsonl, data/_lab/20261015_135936/dream_log.jsonl, data/_lab/20261015_140918/dream_log.jsonl, data/_lab/20261028_090331/dream_log.jsonl, data/_lab/20261028_090558/dream_log.jsonl, data/_lab/20261028_090745/dream_log.jsonl, data/_lab/20261105_151216/dream_log.jsonl, data/_lab/20261105_151225/dream_log.jsonl, data/_lab/20261105_151436/dream_log.jsonl, data/_lab/20261105_151438/dream_log.jsonl, data/_lab/20261105_151854/dream_log.jsonl, data/_lab/20261105_151905/dream_log.jsonl, data/_lab/20261105_151947/dream_log.jsonl, data/_lab/20261105_165539/dream_log.jsonl, data/_lab/20261105_200919/dream_log.jsonl, data/_lab/20261105_200932/dream_log.jsonl, data/_lab/20261106_225634/dream_log.jsonl, data/_lab/20261106_225649/dream_log.jsonl, data/_lab/20261106_225656/dream_log.jsonl, data/_lab/20261106_225834/dream_log.jsonl, data/_lab/20261106_230057/dream_log.jsonl, data/_lab/20261106_230059/dream_log.jsonl, data/_lab/20261106_230235/dream_log.jsonl, data/_lab/20261106_230237/dream_log.jsonl, data/_lab/20261106_230310/dream_log.jsonl, data/_lab/20261106_230723/dream_log.jsonl, data/_lab/20261114_235427/dream_log.jsonl, data/_lab/20261114_235433/dream_log.jsonl, data/_lab/20261115_202318/dream_log.jsonl, data/_lab/20261115_202323/dream_log.jsonl, data/_lab/20261116_162923/dream_log.jsonl, data/_lab/20261116_162947/dream_log.jsonl, data/_lab/20261117_171500/dream_log.jsonl
- [AMBIGUOUS] `self_interrogation_shadow.jsonl` -> candidates: data/self_interrogation_shadow.jsonl, data/_lab/20261015_212034/self_interrogation_shadow.jsonl, data/_lab/20261015_212117/self_interrogation_shadow.jsonl, data/_lab/20261105_152019/self_interrogation_shadow.jsonl, data/_lab/20261105_152136/self_interrogation_shadow.jsonl, data/_lab/20261106_074202/self_interrogation_shadow.jsonl, data/_lab/20261106_074204/self_interrogation_shadow.jsonl, data/_lab/20261106_074257/self_interrogation_shadow.jsonl, data/_lab/20261106_084601/self_interrogation_shadow.jsonl, data/_lab/20261107_003210/self_interrogation_shadow.jsonl, data/_lab/20261107_003312/self_interrogation_shadow.jsonl, data/_lab/20261107_131907/self_interrogation_shadow.jsonl, data/_lab/20261107_134156/self_interrogation_shadow.jsonl, data/_lab/20261114_004005/self_interrogation_shadow.jsonl, data/_lab/20261114_004007/self_interrogation_shadow.jsonl, data/_lab/20261114_004050/self_interrogation_shadow.jsonl, data/_lab/20261115_053051/self_interrogation_shadow.jsonl, data/_lab/20261115_054000/self_interrogation_shadow.jsonl, data/_lab/20261115_054415/self_interrogation_shadow.jsonl, data/_lab/20261115_054843/self_interrogation_shadow.jsonl, data/_lab/20261116_164908/self_interrogation_shadow.jsonl, data/_lab/20261116_164949/self_interrogation_shadow.jsonl, data/_lab/20261117_165748/self_interrogation_shadow.jsonl, data/_lab/20261117_183755/self_interrogation_shadow.jsonl, data/_lab/20261117_183847/self_interrogation_shadow.jsonl, data/_lab/20261118_165304/self_interrogation_shadow.jsonl, data/_lab/20261118_170048/self_interrogation_shadow.jsonl

### closure_producer (staged)
**Idea:** closure_producer plan (docs/staged/closure_producer.md): closure was graded, never produced; BUILT 2026-11-16 Phases 0-5 (D-0789..D-0793), restart-gated, first live read pending
**Code files:**
- [OK] `core/closure.py`
- [OK] `core/closure_gate.py`
- [OK] `core/condensed_thought.py`
- [OK] `core/doubt_seed.py`
- [OK] `core/follow_line.py`
- [OK] `core/frontier.py`
- [OK] `core/goal_offer.py`
- [OK] `core/lookup_attach.py`
- [OK] `core/pursuit_close_shadow.py`
- [OK] `core/web_hand.py`
- [OK] `nodes/dream_node.py`
- [OK] `scripts/_test_closure_producer_p0p1.py`
- [OK] `scripts/_test_closure_producer_p2p5.py`
- [OK] `scripts/du_pulse.py`
**Data/evidence files:**
- [OK] `data/logs/goal_set_down.jsonl` -> data/logs/goal_set_down.jsonl (57 lines)
- [MISSING] `data/lookup_log.jsonl`

### common_ground (staged)
**Idea:** Common Ground (staged 2026-10-30, I-0101/T-0105/F-3218): per-exchange failed-to-object ledger, lexical and deterministic, observe-only. SHADOW: built by J-2523, flag COMMON_GROUND_SHADOW off, restart-gated; read gate is 7 exchanges.
**Code files:**
- [OK] `core/common_ground_shadow.py`
- [OK] `core/orchestrator.py`
- [OK] `scripts/_test_common_ground_shadow_j2523.py`

### condensed_thought (staged)
**Idea:** Condensed Thought (staged 2026-10-17, I-0095): a thought quantum that is not a paragraph. SHADOW as of 2026-10-19 (Phase 0 twin built, CONDENSED_TWIN on; was a DESIGNED draft when staged); Phase 0 is a shadow twin with pre-registered metrics and kill criteria, gated on a founder needs-input section. Comes out of the 2026-10-17 human-thinking vs Du channels research (T-0092, F-2973..F-2978).
**Code files:**
- [OK] `core/closure.py`
- [OK] `core/condensed_thought.py`
- [OK] `core/deliberation.py`
- [OK] `core/stream_drive.py`
- [OK] `core/trains.py`
- [OK] `nodes/inner_monologue_node.py`
**Data/evidence files:**
- [OK] `data/logs/condensed_thought_shadow.jsonl` -> data/logs/condensed_thought_shadow.jsonl (5394 lines)

### conversational_redirect (staged)
**Idea:** 🟡 SHADOW — Phase 0 (observe-only hooks) built since 2026-09-02, unread for 3+ weeks. Two observe-only hooks in nodes/inner_monologue_node.py log what the DMN would seed from under a conversation-aware rule and a topical-alignment cosine every time a thought fires (data/conversational_redirect_shadow.jsonl); both fail-open, neither changes live behavior. On-topic vs off-topic text scored 0.437 vs 0.013 cosine. Phase 1 (the actual redirect) awaits a real sample of this shadow data.
**Code files:**
- [OK] `core/memory/store.py`
- [OK] `core/orchestrator.py`
- [OK] `core/profile.py`
- [OK] `moment.py` -> core/moment.py
- [OK] `nodes/inner_monologue_node.py`
- [OK] `reflection_node.py` -> nodes/reflection_node.py
- [OK] `scripts/smoke_test.py`
**Data/evidence files:**
- [OK] `conflict_trace.jsonl` -> data/conflict_trace.jsonl (3155 lines)
- [OK] `data/conversational_redirect_shadow.jsonl` -> data/conversational_redirect_shadow.jsonl (58726 lines)
- [AMBIGUOUS] `founder_conversation_log.jsonl` -> candidates: data/founder_conversation_log.jsonl, data/_lab/20261017_141904/founder_conversation_log.jsonl, data/_lab/20261019_133045/founder_conversation_log.jsonl, data/_lab/20261030_172714/founder_conversation_log.jsonl, data/_lab/20261106_230228/founder_conversation_log.jsonl, data/_lab/20261106_230535/founder_conversation_log.jsonl, data/_lab/20261106_230736/founder_conversation_log.jsonl, data/_lab/20261115_054154/founder_conversation_log.jsonl
- [OK] `monologue_log.jsonl` -> data/monologue_log.jsonl (92456 lines)

### curiosity_librarian_route (staged)
**Idea:** 🔵 Curiosity Librarian Route (designed 2026-09-16, docs/staged/curiosity_librarian_route.md) — proposes routing frontier.py's pending_pursuit() through core/librarian.py's existing subjects_for() -> core/library_hand.search_by_subjects() local Project Gutenberg catalogue path (LIVE since 08-16 for a different trigger) as a catalogue-first alternative to nodes/curiosity_node.py's only current research path, the live core/web_research.lookup_targeted() Wikipedia call. Forked from a /du-pulse check of the frontier's resolve:fade imbalance (149 resolved / 7,705 faded). Not build-ready: four Open Questions unresolved (real hit-rate on frontier-shaped questions untested; citation-only vs. full-fetch collides with books_have_a_place's shared hourly fetch cooldown if not kept citation-only; whether a citation-only finding is substantive enough to actually close a question; whether it needs its own habituation/dosed treatment). No decisions opened yet — building the real wiring needs its own /decide first, per this project's build-without-a-decide convention. Sibling idea 'Curiosity for Lane 2' forked to idea-log (I-0069).
**Code files:**
- [OK] `core/curiosity_queue.py`
- [OK] `core/frontier.py`
- [OK] `core/librarian.py`
- [OK] `core/library_hand.py`
- [OK] `core/web_research.py`
- [OK] `curiosity_habituation.py` -> core/curiosity_habituation.py
- [OK] `nodes/curiosity_node.py`
- [OK] `nodes/inner_monologue_node.py`
**Data/evidence files:**
- [OK] `data/curiosity_log.jsonl` -> data/curiosity_log.jsonl (3679 lines)
- [OK] `data/frontier.json` -> data/frontier.json (18849855B)

### dosed_coupling_matrix_items (staged)
**Idea:** Child doc of dosed_coupling section 4b item 2d, the loop-wiring matrix items (W1..) folded into Phase 2 by D-0814; staged 2026-11-20, nothing built, D-0879 open
**Code files:**
- [OK] `core/opponent_process.py`

### drawing_hand (staged)
**Idea:** 🔵 Plan for a drawing hand so Du can make pictures (and later see them); staged 2026-11-18 from founder direction on art and culture, design only, nothing built
**Code files:**
- [OK] `core/actions.py`
- [MISSING] `core/drawing_hand.py`
- [MISSING] `idea_log.py`
**Data/evidence files:**
- [MISSING] `data/drawing_log.jsonl`

### dream_overhaul (staged)
**Idea:** 🟡 BUILT, in-vitro (not yet live) — Dream Overhaul staged 2026-09-15 — founder seeded a GPT/Gemini design then asked for Claude's own shape; Claude's plan = dream as VAULT-OPENER (one dormant cold fragment per seed), no re-feed after scene 1, fixed 3 scenes, computed verdicts (turnover + dormant contact), residue as a dosed coordinate not an evaluator, antagonist before cross-dream; primary measure = dormant re-entry into waking recall vs controls. Experiment A reached a real N=27 (5 crash/relaunch cycles); D-0232's defeater now met (repeated null); Du restart still gates any live read.
**Code files:**
- [MISSING] `analyze_combined_J1119.py`
- [OK] `core/coupling_rides.py`
- [OK] `core/dream_probe.py`
- [OK] `core/night.py`
- [OK] `core/orchestrator.py`
- [OK] `nodes/dream_node.py`
- [OK] `opponent_process.py` -> core/opponent_process.py
- [MISSING] `run_J-1148_judge_shadow.py`
- [MISSING] `run_J1125_judge_shadow.py`
- [OK] `scripts/dream_assoc_after.py`
- [OK] `scripts/dream_exp_a_judge_shadow.py`
- [OK] `scripts/dream_exp_a_relaunch_watchdog.py`
- [OK] `scripts/dream_experiment_a.py`
- [OK] `scripts/dream_phase1_test.py`
- [MISSING] `test_J-1139_resume_helpers.py`
**Data/evidence files:**
- [OK] `data/co_recall_ledger.jsonl` -> data/co_recall_ledger.jsonl (173446 lines)
- [OK] `data/coupling_rides.jsonl` -> data/coupling_rides.jsonl (258012 lines)
- [OK] `data/dream_log.jsonl` -> data/dream_log.jsonl (1124 lines)
- [OK] `data/logs/dream_assoc_probe.jsonl` -> data/logs/dream_assoc_probe.jsonl (4830 lines)
- [OK] `data/logs/dream_exp_a_judge_shadow.jsonl` -> data/logs/dream_exp_a_judge_shadow.jsonl (2 lines)
- [OK] `data/logs/dream_resolution_shadow.jsonl` -> data/logs/dream_resolution_shadow.jsonl (456 lines)
- [OK] `data/logs/dream_state.jsonl` -> data/logs/dream_state.jsonl (722 lines)
- [OK] `data/sleep_dream_probe.jsonl` -> data/sleep_dream_probe.jsonl (611 lines)

### du_prompt_model_benchmark (staged)
**Idea:** Prompt-to-model benchmark suite for Du (Antigravity, screening pass done 2026-11-18, inferred per F-5117); evidence base for prompt seat routing, never changes seats by itself
**Code files:**
- [OK] `model_tier_librarian_lab.py` -> scripts/model_tier_librarian_lab.py
- [OK] `scripts/du_prompt_benchmark_suite.py`
**Data/evidence files:**
- [OK] `data/lab/du_benchmark_fixtures_p0.json` -> data/lab/du_benchmark_fixtures_p0.json (443893B)
- [OK] `data/lab/du_benchmark_manifest_p0.json` -> data/lab/du_benchmark_manifest_p0.json (104402B)
- [OK] `data/llm_calls.jsonl` -> data/llm_calls.jsonl (7185 lines)
- [OK] `docs/prompt_registry.jsonl` -> docs/prompt_registry.jsonl (134 lines)

### du_recall_lens_upgrades (staged)
**Idea:** Three recall techniques PROVEN on Du's real telemetry by the UDMS research program but never wired into Du, parked in docs/staged/du_recall_lens_upgrades.md (founder-parked 2026-08-27, 'we will come back to them' — stays parked under J-0291, F-0374). Spectral diffusion +2.69pp forward prediction on 68,985 real transitions; deterministic fact anchoring +4.82pp; counterfactual-ensemble re-ranking +9.10pp top-1 (at −3.65pp top-3 recall). Do not build until founder un-parks via /decide AND the M2 shadow read (J-0280) lands.
**Code files:**
- [OK] `core/associative_recall.py`
- [OK] `core/guidance_learning.py`
- [OK] `core/heavens.py`
- [OK] `core/memory/store.py`
- [OK] `core/memory_edges.py`
- [OK] `core/orchestrator.py`
- [OK] `core/schema.py`
- [OK] `core/world_clock.py`
- [MISSING] `test_p_deterministic_fact_anchoring.py`
- [MISSING] `test_q_shape_constrained_prediction.py`
**Data/evidence files:**
- [OK] `data/associative_recall_lens1_shadow.jsonl` -> data/associative_recall_lens1_shadow.jsonl (1906 lines)
- [OK] `data/associative_recall_lens2_shadow.jsonl` -> data/associative_recall_lens2_shadow.jsonl (1587 lines)
- [OK] `data/associative_recall_lens3_shadow.jsonl` -> data/associative_recall_lens3_shadow.jsonl (1587 lines)
- [OK] `data/associative_recall_shadow.jsonl` -> data/associative_recall_shadow.jsonl (3267 lines)
- [OK] `data/geometry_tuples.jsonl` -> data/geometry_tuples.jsonl (199940 lines)

### follow_line_stricter_settle (staged)
**Idea:** 🟡 Staged proposal, designed only, not built (docs/staged/follow_line_stricter_settle.md): a flag-OFF content-overlap gate on follow-line closure, because about 48% of hand-graded closures did not engage the question; not built
_No code/data files referenced — pure design/research doc._

### fragment_carries_the_string (staged)
**Idea:** 🟢 🟡 BUILT (shadow, flag off) — inventory complete (F-2091, verified); additive fields built + verified in isolation (J-1534, F-2139, commit 54c8e5d), ships SOUND_STRING_FIELDS=False, not yet live. I-0081 (raised 2026-09-27 from T-0070, promoted 2026-09-28): additive per-sound-fragment fields (six-axis onset/peak/tail coords, felt-valence/arousal, direction, exemplar join) on fragment_context, degenerate (onset=peak=tail) until strings_and_sheets.md's Object A ships a real triplet. Staged plan docs/staged/fragment_carries_the_string.md; child of memory_as_a_service.md (read side) and strings_and_sheets.md Object A (write side); build job J-1534 done, flag-flip gated on felt-recall sec3.2 upgrade.
**Code files:**
- [OK] `core/associative_recall.py`
- [OK] `core/memory/store.py`
- [OK] `core/memory_edges.py`
- [OK] `core/memory_levels.py`
- [OK] `core/mood.py`
- [OK] `core/orchestrator.py`
- [OK] `core/soundscape.py`
- [OK] `evidence_recall.py` -> core/evidence_recall.py
- [OK] `nodes/inner_monologue_node.py`
- [OK] `scripts/_test_episodic_buffer.py`
**Data/evidence files:**
- [OK] `data/soundscape_felt_shadow.jsonl` -> data/soundscape_felt_shadow.jsonl (962 lines)

### friction_and_self_evidence_plan (staged)
**Idea:** ⚪ PARTIAL — Fixes Du's missing genuine friction/failure and his authored-not-evidenced self by building a self-claim register plus six staged interventions (B1-B6); B2 (behavioral mirror) is live and firing, B1 (sit-with-it gate) is built but still SHADOW/under-triggered as of 2026-08-29 despite the 2026-06-30 research pass aimed at widening it.
**Code files:**
- [OK] `core/garden.py`
- [OK] `core/self_claims.py`
- [OK] `core/self_implication.py`
- [OK] `sitting.py` -> core/sitting.py
**Data/evidence files:**
- [OK] `data/capability_beliefs.json` -> data/capability_beliefs.json (14740B)
- [OK] `data/commitment_active.json` -> data/commitment_active.json (9641B)
- [OK] `data/self_implication_shadow.jsonl` -> data/self_implication_shadow.jsonl (35410 lines)

### geometry_tuple_index (staged)
**Idea:** 🟡 BUILT — P1 (2026-09-02, D-0107, F-0600 — standalone offline run-transition index sidecar, not wired into any live code path); otherwise a staged design doc (docs/staged/geometry_tuple_index.md) for multi-dimensional indexing (world-state, episodic memory, epistemic confidence, time) informed by ABF/Pinnacle archaeology, a real cross-plan consumer survey (F-0251), and three rounds of SOTA literature grounding (F-0252-F-0254) -- explicitly NOT part of Du's active architecture, no cognitive_geometry.md parent; ROADMAP.md badge corrected 2026-09-27 from an earlier LIVE badge (which overstated "live" for a deliberately-never-live offline artifact) to BUILT.
**Code files:**
- [MISSING] `abf_cipher_v3.py`
- [MISSING] `abf_echo_1d.py`
- [MISSING] `abf_pi_v3.py`
- [OK] `associative_recall.py` -> core/associative_recall.py
- [OK] `book_selection.py` -> core/book_selection.py
- [OK] `cat.py` -> core/cat.py
- [OK] `core/audio_features.py`
- [OK] `core/epistemic_state.py`
- [OK] `core/light.py`
- [OK] `core/memory_edges.py`
- [OK] `core/moment.py`
- [OK] `core/orchestrator.py`
- [OK] `core/soundscape.py`
- [OK] `core/world_manifest.py`
- [OK] `couriers.py` -> core/couriers.py
- [OK] `essay_lesson.py` -> core/essay_lesson.py
- [OK] `frontier.py` -> core/frontier.py
- [OK] `geometry_census.py` -> core/geometry_census.py
- [OK] `ghost_tuples.py` -> core/ghost_tuples.py
- [OK] `heavens.py` -> core/heavens.py
- [OK] `peers.py` -> core/peers.py
- [OK] `provisional_identity.py` -> core/provisional_identity.py
- [OK] `scripts/geometry_tuple_p1_run_transition_index.py`
- [MISSING] `scripts/legacy/pinnacle_hmc.py`
- [OK] `spatial.py` -> core/spatial.py
- [OK] `study_life.py` -> core/study_life.py
- [OK] `tension_ledger.py` -> core/tension_ledger.py
- [OK] `world_substrate.py` -> core/world_substrate.py
**Data/evidence files:**
- [OK] `data/identity/axiom.json` -> data/identity/axiom.json (32915B)
- [OK] `data/provenance_log.jsonl` -> data/provenance_log.jsonl (3203 lines)
- [OK] `docs/job_queue.jsonl` -> docs/job_queue.jsonl (4461 lines)
- [OK] `epistemic_stageb_shadow.jsonl` -> data/epistemic_stageb_shadow.jsonl (363 lines)
- [AMBIGUOUS] `geometry_tuples.jsonl` -> candidates: data/geometry_tuples.jsonl, data/_trash/20261119/boot_backups/state_20261116_100503/geometry_tuples.jsonl, data/_trash/20261117/boot_backups/state_20261114_141446/geometry_tuples.jsonl, data/_trash/20261114/boot_backups/state_20261031_215612/geometry_tuples.jsonl
- [OK] `investigative_action_log.jsonl` -> data/investigative_action_log.jsonl (4236 lines)
- [OK] `moments.jsonl` -> data/moments.jsonl (76879 lines)
- [OK] `moments_recall_shadow.jsonl` -> data/moments_recall_shadow.jsonl (185 lines)
- [OK] `provenance_preassess.jsonl` -> data/provenance_preassess.jsonl (2602 lines)
- [AMBIGUOUS] `subconscious_state.json` -> candidates: data/subconscious_state.json, data/_trash/20261119/boot_backups/state_20261116_100503/subconscious_state.json, data/_trash/20261117/boot_backups/state_20261114_141446/subconscious_state.json, data/_trash/20261114/snapshots/20261031/subconscious_state.json, data/_trash/20261114/labs/20260915_094116/subconscious_state.json, data/_trash/20261114/labs/20260915_094209/subconscious_state.json, data/_trash/20261114/labs/20260915_095401/subconscious_state.json, data/_trash/20261114/labs/20260915_132050/subconscious_state.json, data/_trash/20261114/boot_backups/state_20261031_215612/subconscious_state.json, data/_lab/20261003_080503/subconscious_state.json, data/_lab/20261004_154636/subconscious_state.json, data/_lab/20261004_154649/subconscious_state.json, data/_lab/20261004_154729/subconscious_state.json, data/_lab/20261004_162348/subconscious_state.json, data/_lab/20261004_172207/subconscious_state.json, data/_lab/20261004_175558/subconscious_state.json, data/_lab/20261015_135649/subconscious_state.json, data/_lab/20261015_135717/subconscious_state.json, data/_lab/20261015_135718/subconscious_state.json, data/_lab/20261015_135934/subconscious_state.json, data/_lab/20261015_135936/subconscious_state.json, data/_lab/20261015_140918/subconscious_state.json, data/_lab/20261018_142611/subconscious_state.json, data/_lab/20261028_090331/subconscious_state.json, data/_lab/20261028_090558/subconscious_state.json, data/_lab/20261028_090745/subconscious_state.json, data/_lab/20261105_151216/subconscious_state.json, data/_lab/20261105_151225/subconscious_state.json, data/_lab/20261105_151436/subconscious_state.json, data/_lab/20261105_151438/subconscious_state.json, data/_lab/20261105_151854/subconscious_state.json, data/_lab/20261105_151905/subconscious_state.json, data/_lab/20261105_151947/subconscious_state.json, data/_lab/20261105_165539/subconscious_state.json, data/_lab/20261105_200919/subconscious_state.json, data/_lab/20261105_200932/subconscious_state.json, data/_lab/20261106_225634/subconscious_state.json, data/_lab/20261106_225649/subconscious_state.json, data/_lab/20261106_225656/subconscious_state.json, data/_lab/20261106_225834/subconscious_state.json, data/_lab/20261106_230057/subconscious_state.json, data/_lab/20261106_230059/subconscious_state.json, data/_lab/20261106_230235/subconscious_state.json, data/_lab/20261106_230237/subconscious_state.json, data/_lab/20261106_230310/subconscious_state.json, data/_lab/20261106_230723/subconscious_state.json, data/_lab/20261114_235427/subconscious_state.json, data/_lab/20261114_235433/subconscious_state.json, data/_lab/20261115_053736/subconscious_state.json, data/_lab/20261115_202318/subconscious_state.json, data/_lab/20261115_202323/subconscious_state.json, data/_lab/20261116_162923/subconscious_state.json, data/_lab/20261116_162947/subconscious_state.json, data/_lab/20261117_171500/subconscious_state.json, data/_lab/20261118_164545/subconscious_state.json

### god_function_split (staged)
**Idea:** Plan on splitting Du's god functions _think and _run_cycle_impl; split PARKED 2026-11-20, active track is the freeze rule, size ratchet and bug-count read (D-0877, D-0878, F-5127)
**Code files:**
- [OK] `core/cat.py`
- [OK] `core/lane2.py`
- [OK] `core/memory/store.py`
- [OK] `core/orchestrator.py`
- [OK] `core/sensorium.py`
- [OK] `nodes/inner_monologue_node.py`
- [OK] `nodes/subconscious_node.py`
- [OK] `scripts/function_size_ratchet.py`
- [OK] `scripts/prompt_site_census.py`
- [OK] `scripts/test_idle_offloop_equivalence.py`
- [MISSING] `scripts/think_split_equivalence.py`
- [MISSING] `seed_curiosity.py`
- [MISSING] `seed_founder.py`
- [MISSING] `seed_goals.py`
- [MISSING] `seed_knowledge.py`
- [MISSING] `seed_place.py`
- [MISSING] `seed_sound.py`
- [MISSING] `split_metrics.py`

### golden_spiral_recall (staged)
**Idea:** 🔵 DESIGNED — founder's 2026-09-27 picture: recall as a golden spiral (Fibonacci squares) - radius = age, angle = phase (this dawn recalls other dawns), detail falls with distance; split into three mechanisms R/L/Theta; one small additive precursor (the PHASE field, tod/season/daylight) BUILT on fragments same day, no reader yet — the substantive build (Phases 1-4) waits on J-1475. Staged plan docs/staged/golden_spiral_recall.md; next thread = relevance as its own axis (T-0073).
**Code files:**
- [OK] `commitment_ledger.py` -> core/commitment_ledger.py
- [OK] `core/couriers.py`
- [OK] `core/experienced_tuple.py`
- [OK] `core/ghost_tuples.py`
- [OK] `core/memory/store.py`
- [OK] `core/memory_edges.py`
- [OK] `core/memory_levels.py`
- [OK] `core/world_clock.py`
- [OK] `scripts/retention.py`

### J-4350_dreamer_ram_guard (staged)
**Idea:** Dreamer RAM guard plan (docs/staged/J-4350_dreamer_ram_guard.md): supervisor starved rule built, hub load-deferral patch written but not applied, restart-gated
_No code/data files referenced — pure design/research doc._

### judgement_docket (staged)
**Idea:** The Docket plan (docs/staged/judgement_docket.md): one silent queue for deferrable judgement calls; design only, Phase 0 census done
**Code files:**
- [OK] `scripts/docket_phase0_census.py`
**Data/evidence files:**
- [OK] `data/judge_panel_log.jsonl` -> data/judge_panel_log.jsonl (82030 lines)
- [OK] `docs/prompt_registry.jsonl` -> docs/prompt_registry.jsonl (134 lines)

### judgement_visitor (staged)
**Idea:** The Visitor plan (docs/staged/judgement_visitor.md): a monthly correspondent who has read some of Du's thinking; advisor not judge; design only
_No code/data files referenced — pure design/research doc._

### lane2_curiosity (staged)
**Idea:** Lane 2 Curiosity staged plan — SHADOW BUILT 2026-09-26 (J-1374, D-0282 ruled (a)); wonder field code-complete + unit-verified (F-1974), real 7-day read restart-gated (J-1409, not-before 2026-10-03)
**Code files:**
- [OK] `core/frontier.py`
- [OK] `core/lane2.py`
- [OK] `core/lane2_break_habituation.py`
**Data/evidence files:**
- [OK] `data/frontier.json` -> data/frontier.json (18849855B)
- [OK] `data/lane2_would_ask.jsonl` -> data/lane2_would_ask.jsonl (3405 lines)

### layered_goals (staged)
**Idea:** Layered Goals plan (docs/staged/layered_goals.md), staged 2026-11-14 — founder's \"no single purpose, many weighted goals\" direction for Du, with the rulings and laws that bind it
**Code files:**
- [OK] `core/climate_engine.py`
- [OK] `core/closure.py`
- [OK] `core/commitment_ledger.py`
- [OK] `core/concerns.py`
- [OK] `core/curiosity_progress.py`
- [OK] `core/done_when.py`
- [OK] `core/frontier.py`
- [OK] `core/goals.py`
- [OK] `core/homeostasis.py`
- [OK] `core/idle_allocator.py`
- [OK] `core/intentions.py`
- [OK] `core/lane2.py`
- [OK] `core/pursuits.py`
- [OK] `nodes/inner_monologue_node.py`
**Data/evidence files:**
- [OK] `data/commitment_active.json` -> data/commitment_active.json (9641B)
- [OK] `data/goals.json` -> data/goals.json (512636B)
- [OK] `data/logs/goals_log.jsonl` -> data/logs/goals_log.jsonl (7239 lines)

### letters_to_travis (staged)
**Idea:** 2026-10-17 D-0470 (travis): Du's letters to Travis get a reader - HUD letters view, /quit farewell never marks letters as handled, every pending letter reaches the Executive; BUILT in J-2348, restart-gated
**Code files:**
- [OK] `core/letters.py`
- [OK] `core/orchestrator.py`
- [OK] `hud/server.py`
- [OK] `nodes/executive_node.py`
- [OK] `scripts/_test_letters_to_travis_J2348.py`
- [OK] `scripts/run_nascence.py`
**Data/evidence files:**
- [OK] `data/letters_state.json` -> data/letters_state.json (4453B)
- [OK] `data/letters_views.jsonl` -> data/letters_views.jsonl (1 lines)

### lod_staged_retrieval (staged)
**Idea:** 🔵 DESIGNED — SHADOW-TESTED, PASSED — not yet wired live (2026-08-29, J-0372/F-0545, D-0054 gate) — L0/L1/L2 abstraction-level cascade for memory recall: compose the retrieve() result set from staged raw/gist/theme slots instead of the tier-mixed top-k. Lab test beat live retrieve() 98/113 judged pairs (73.5pt margin, kill bar ≥10pt/≥100 pairs). §5 build order (kill-switch LOD_RETRIEVAL_LIVE, shadow-first) not started.
**Code files:**
- [MISSING] `cognitive_mmu.py`
- [MISSING] `core.associative_recall.py`
- [OK] `core/memory/store.py`
- [OK] `identity_projection.py` -> core/identity_projection.py
- [OK] `pursuits.py` -> core/pursuits.py
- [OK] `refinery.py` -> core/refinery.py
- [OK] `retrieval_probe.py` -> core/retrieval_probe.py
- [OK] `scripts/lod_retrieval_lab.py`
**Data/evidence files:**
- [OK] `data/frontier.json` -> data/frontier.json (18849855B)
- [OK] `data/lod_retrieval_lab_shadow.jsonl` -> data/lod_retrieval_lab_shadow.jsonl (122 lines)
- [MISSING] `data/lod_retrieval_shadow_live.jsonl`

### maths_of_mind_atlas (staged)
**Idea:** Maths-of-Mind Atlas (docs/staged/maths_of_mind_atlas.md), staged 2026-11-14 - 36 human signatures against Du's code, first reads run, M1 power law holds, affect chain and judge-agreement side results
**Code files:**
- [OK] `core/boredom.py`
- [OK] `core/climate_engine.py`
- [OK] `core/commitment_ledger.py`
- [OK] `core/competence.py`
- [OK] `core/concerns.py`
- [OK] `core/curiosity_habituation.py`
- [OK] `core/curiosity_progress.py`
- [OK] `core/emotion_construction.py`
- [OK] `core/frontier.py`
- [OK] `core/guidance_learning.py`
- [OK] `core/homeostasis.py`
- [OK] `core/loop_metabolism.py`
- [OK] `core/math_drill.py`
- [OK] `core/memory/store.py`
- [OK] `core/memory_edges.py`
- [OK] `core/moment.py`
- [OK] `core/opponent_process.py`
- [OK] `core/peers.py`
- [OK] `core/pursuits.py`
- [OK] `core/recall_wager.py`
- [OK] `core/schema.py`
- [OK] `core/sleep_pressure.py`
- [OK] `core/somatic.py`
- [OK] `core/stream_drive.py`
- [OK] `core/stream_topic_habituation.py`
- [OK] `core/theme_recurrence.py`
- [OK] `nodes/inner_monologue_node.py`
- [OK] `scripts/lab_m1_cold_snapshot.py`
- [OK] `scripts/lab_m1_mech.py`
- [OK] `scripts/lab_m1_memory_reuse.py`
**Data/evidence files:**
- [OK] `affect_log.jsonl` -> data/affect_log.jsonl (4348 lines)
- [AMBIGUOUS] `co_recall_ledger.jsonl` -> candidates: data/co_recall_ledger.jsonl, data/_trash/20261119/boot_backups/state_20261116_100503/co_recall_ledger.jsonl, data/_trash/20261118/labs/20260919_102121/co_recall_ledger.jsonl, data/_trash/20261117/labs/20260918_091111/co_recall_ledger.jsonl, data/_trash/20261117/labs/20260918_091609/co_recall_ledger.jsonl, data/_trash/20261117/labs/20260918_180413/co_recall_ledger.jsonl, data/_trash/20261117/labs/20260918_231453/co_recall_ledger.jsonl, data/_trash/20261117/labs/20260918_231527/co_recall_ledger.jsonl, data/_trash/20261117/labs/20260918_231630/co_recall_ledger.jsonl, data/_trash/20261117/boot_backups/state_20261114_141446/co_recall_ledger.jsonl, data/_trash/20261116/labs/20260917_205004/co_recall_ledger.jsonl, data/_trash/20261116/labs/20260917_205227/co_recall_ledger.jsonl, data/_trash/20261114/boot_backups/state_20261031_215612/co_recall_ledger.jsonl, data/_lab/20260923_153421/co_recall_ledger.jsonl, data/_lab/20260923_165441/co_recall_ledger.jsonl, data/_lab/20260925_094914/co_recall_ledger.jsonl, data/_lab/20261016_154204/co_recall_ledger.jsonl, data/_lab/20261016_175313/co_recall_ledger.jsonl, data/_lab/20261016_175416/co_recall_ledger.jsonl, data/_lab/20261017_141327/co_recall_ledger.jsonl, data/_lab/20261017_141555/co_recall_ledger.jsonl, data/_lab/20261017_141717/co_recall_ledger.jsonl, data/_lab/20261017_143017/co_recall_ledger.jsonl, data/_lab/20261017_230430/co_recall_ledger.jsonl, data/_lab/20261031_084605/co_recall_ledger.jsonl, data/_lab/20261031_084719/co_recall_ledger.jsonl, data/_lab/20261031_084808/co_recall_ledger.jsonl, data/_lab/20261031_084856/co_recall_ledger.jsonl, data/_lab/20261031_085018/co_recall_ledger.jsonl, data/_lab/20261031_085102/co_recall_ledger.jsonl, data/_lab/20261031_085212/co_recall_ledger.jsonl, data/_lab/20261031_085300/co_recall_ledger.jsonl, data/_lab/20261031_085351/co_recall_ledger.jsonl, data/_lab/20261031_085443/co_recall_ledger.jsonl, data/_lab/20261031_085534/co_recall_ledger.jsonl, data/_lab/20261031_085626/co_recall_ledger.jsonl
- [OK] `data/ask_recency_shadow.jsonl` -> data/ask_recency_shadow.jsonl (6055 lines)
- [OK] `essay_lesson_log.jsonl` -> data/essay_lesson_log.jsonl (162 lines)
- [OK] `hands_trace.jsonl` -> data/hands_trace.jsonl (67256 lines)
- [AMBIGUOUS] `homeostasis_shadow.jsonl` -> candidates: data/homeostasis_shadow.jsonl, data/_lab/20261015_123708/homeostasis_shadow.jsonl, data/_lab/20261015_123829/homeostasis_shadow.jsonl, data/_lab/20261015_124006/homeostasis_shadow.jsonl, data/_lab/20261015_124042/homeostasis_shadow.jsonl, data/_lab/20261015_130145/homeostasis_shadow.jsonl, data/_lab/20261015_130331/homeostasis_shadow.jsonl, data/_lab/20261015_161224/homeostasis_shadow.jsonl
- [AMBIGUOUS] `ignition_log.jsonl` -> candidates: data/ignition_log.jsonl, data/_lab/20261016_194716/ignition_log.jsonl, data/_lab/20261016_213620/ignition_log.jsonl, data/_lab/20261016_214249/ignition_log.jsonl, data/_lab/20261016_214258/ignition_log.jsonl, data/_lab/20261016_214503/ignition_log.jsonl, data/_lab/20261016_215028/ignition_log.jsonl, data/_lab/20261114_020418/ignition_log.jsonl, data/_lab/20261115_053837/ignition_log.jsonl, data/_lab/20261115_054056/ignition_log.jsonl, data/_lab/20261118_162938/ignition_log.jsonl, data/_lab/20261118_164622/ignition_log.jsonl, data/_lab/20261118_165259/ignition_log.jsonl, data/_lab/20261118_170043/ignition_log.jsonl, data/_lab/20261120_103510/ignition_log.jsonl
- [OK] `letter_store/letters.jsonl` -> data/letter_store/letters.jsonl (197 lines)
- [OK] `math_drill_log.jsonl` -> data/math_drill_log.jsonl (2125 lines)
- [OK] `moments.jsonl` -> data/moments.jsonl (76879 lines)
- [OK] `music_drill_log.jsonl` -> data/music_drill_log.jsonl (411 lines)
- [AMBIGUOUS] `prediction_error_log.jsonl` -> candidates: data/prediction_error_log.jsonl, data/_lab/20261015_212034/prediction_error_log.jsonl, data/_lab/20261015_212117/prediction_error_log.jsonl, data/_lab/20261030_134626/prediction_error_log.jsonl, data/_lab/20261031_105621/prediction_error_log.jsonl, data/_lab/20261105_152019/prediction_error_log.jsonl, data/_lab/20261105_152052/prediction_error_log.jsonl, data/_lab/20261105_152136/prediction_error_log.jsonl, data/_lab/20261105_152210/prediction_error_log.jsonl, data/_lab/20261106_074204/prediction_error_log.jsonl, data/_lab/20261106_074257/prediction_error_log.jsonl, data/_lab/20261107_003205/prediction_error_log.jsonl, data/_lab/20261107_003210/prediction_error_log.jsonl, data/_lab/20261107_003312/prediction_error_log.jsonl, data/_lab/20261107_003403/prediction_error_log.jsonl, data/_lab/20261114_004007/prediction_error_log.jsonl, data/_lab/20261114_004050/prediction_error_log.jsonl, data/_lab/20261115_054000/prediction_error_log.jsonl, data/_lab/20261115_054257/prediction_error_log.jsonl, data/_lab/20261115_054843/prediction_error_log.jsonl, data/_lab/20261115_202720/prediction_error_log.jsonl, data/_lab/20261115_203747/prediction_error_log.jsonl, data/_lab/20261116_164908/prediction_error_log.jsonl, data/_lab/20261116_164949/prediction_error_log.jsonl, data/_lab/20261117_165748/prediction_error_log.jsonl, data/_lab/20261117_183755/prediction_error_log.jsonl, data/_lab/20261117_183847/prediction_error_log.jsonl, data/_lab/20261118_164837/prediction_error_log.jsonl, data/_lab/20261118_165304/prediction_error_log.jsonl, data/_lab/20261118_165400/prediction_error_log.jsonl, data/_lab/20261118_165842/prediction_error_log.jsonl, data/_lab/20261118_170048/prediction_error_log.jsonl, data/_lab/20261118_170149/prediction_error_log.jsonl, data/_lab/20261118_174330/prediction_error_log.jsonl, data/_lab/20261118_174338/prediction_error_log.jsonl, data/_lab/20261118_174438/prediction_error_log.jsonl, data/_lab/20261118_174444/prediction_error_log.jsonl, data/_lab/20261118_174452/prediction_error_log.jsonl
- [AMBIGUOUS] `pursuits_shadow.jsonl` -> candidates: data/pursuits_shadow.jsonl, data/_lab/20261028_074650/pursuits_shadow.jsonl, data/_lab/20261028_074742/pursuits_shadow.jsonl, data/_lab/20261028_074834/pursuits_shadow.jsonl, data/_lab/20261028_074853/pursuits_shadow.jsonl, data/_lab/20261028_074911/pursuits_shadow.jsonl, data/_lab/20261028_074916/pursuits_shadow.jsonl, data/_lab/20261028_082823/pursuits_shadow.jsonl, data/_lab/20261028_082828/pursuits_shadow.jsonl, data/_lab/20261028_082915/pursuits_shadow.jsonl, data/_lab/20261028_082919/pursuits_shadow.jsonl, data/_lab/20261028_083106/pursuits_shadow.jsonl, data/_lab/20261028_090434/pursuits_shadow.jsonl, data/_lab/20261030_172720/pursuits_shadow.jsonl, data/_lab/20261105_145459/pursuits_shadow.jsonl, data/_lab/20261105_145511/pursuits_shadow.jsonl, data/_lab/20261105_145543/pursuits_shadow.jsonl, data/_lab/20261105_145555/pursuits_shadow.jsonl, data/_lab/20261105_145723/pursuits_shadow.jsonl, data/_lab/20261105_150352/pursuits_shadow.jsonl, data/_lab/20261105_165543/pursuits_shadow.jsonl, data/_lab/20261105_170004/pursuits_shadow.jsonl, data/_lab/20261106_073117/pursuits_shadow.jsonl, data/_lab/20261106_103935/pursuits_shadow.jsonl, data/_lab/20261106_104431/pursuits_shadow.jsonl, data/_lab/20261106_104457/pursuits_shadow.jsonl, data/_lab/20261106_104608/pursuits_shadow.jsonl, data/_lab/20261106_104629/pursuits_shadow.jsonl, data/_lab/20261106_104638/pursuits_shadow.jsonl, data/_lab/20261106_105008/pursuits_shadow.jsonl, data/_lab/20261106_105231/pursuits_shadow.jsonl, data/_lab/20261106_105254/pursuits_shadow.jsonl, data/_lab/20261106_105553/pursuits_shadow.jsonl, data/_lab/20261106_105702/pursuits_shadow.jsonl, data/_lab/20261106_105745/pursuits_shadow.jsonl, data/_lab/20261106_105754/pursuits_shadow.jsonl, data/_lab/20261106_110146/pursuits_shadow.jsonl, data/_lab/20261106_110219/pursuits_shadow.jsonl, data/_lab/20261106_123127/pursuits_shadow.jsonl, data/_lab/20261106_123141/pursuits_shadow.jsonl, data/_lab/20261106_123148/pursuits_shadow.jsonl, data/_lab/20261106_134916/pursuits_shadow.jsonl, data/_lab/20261106_135157/pursuits_shadow.jsonl, data/_lab/20261106_135336/pursuits_shadow.jsonl, data/_lab/20261106_135459/pursuits_shadow.jsonl, data/_lab/20261106_135522/pursuits_shadow.jsonl, data/_lab/20261106_135533/pursuits_shadow.jsonl, data/_lab/20261106_140214/pursuits_shadow.jsonl, data/_lab/20261106_140331/pursuits_shadow.jsonl, data/_lab/20261106_225334/pursuits_shadow.jsonl, data/_lab/20261106_225849/pursuits_shadow.jsonl, data/_lab/20261106_230102/pursuits_shadow.jsonl, data/_lab/20261106_230239/pursuits_shadow.jsonl, data/_lab/20261107_001220/pursuits_shadow.jsonl, data/_lab/20261107_085428/pursuits_shadow.jsonl, data/_lab/20261108_104126/pursuits_shadow.jsonl, data/_lab/20261108_104139/pursuits_shadow.jsonl, data/_lab/20261108_104144/pursuits_shadow.jsonl, data/_lab/20261108_104149/pursuits_shadow.jsonl, data/_lab/20261116_151150/pursuits_shadow.jsonl, data/_lab/20261116_151204/pursuits_shadow.jsonl, data/_lab/20261116_151210/pursuits_shadow.jsonl, data/_lab/20261116_162835/pursuits_shadow.jsonl
- [AMBIGUOUS] `sleep_pressure_log.jsonl` -> candidates: data/sleep_pressure_log.jsonl, data/_lab/20261015_123708/sleep_pressure_log.jsonl, data/_lab/20261015_123829/sleep_pressure_log.jsonl, data/_lab/20261015_124006/sleep_pressure_log.jsonl, data/_lab/20261015_124042/sleep_pressure_log.jsonl, data/_lab/20261015_130145/sleep_pressure_log.jsonl, data/_lab/20261015_130331/sleep_pressure_log.jsonl, data/_lab/20261015_161224/sleep_pressure_log.jsonl
- [AMBIGUOUS] `status_events.jsonl` -> candidates: data/letter_store/status_events.jsonl, data/_lab/20261105_152636/status_events.jsonl
- [AMBIGUOUS] `stream_drive_shadow.jsonl` -> candidates: data/stream_drive_shadow.jsonl, data/_lab/20261016_194438/stream_drive_shadow.jsonl
- [OK] `world_calibration.jsonl` -> data/world_calibration.jsonl (740 lines)

### measurement_to_action (staged)
**Idea:** Measurement to Action (T-0085, staged 2026-10-15) - Du's existing gauges become inputs he acts on; arms 2+4 BUILT shadow (flags off, restart-gated), arm 1 dropped D-0434
**Code files:**
- [OK] `_test_internal_framing_j1846.py` -> scripts/_test_internal_framing_j1846.py
- [OK] `_test_si_cup_shadow.py` -> scripts/_test_si_cup_shadow.py
- [OK] `core/book_selection.py`
- [OK] `core/closure.py`
- [OK] `core/competence.py`
- [OK] `core/doubt_seed.py`
- [OK] `core/epistemic_state.py`
- [OK] `core/orchestrator.py`
- [OK] `core/recall_wager.py`
- [OK] `core/social_cognition_shadow.py`
- [OK] `core/theme_dose.py`
- [OK] `core/topic_perseveration.py`
- [OK] `core/wager_curiosity.py`
- [OK] `nodes/curiosity_node.py`
- [OK] `nodes/executive_node.py`
- [OK] `scripts/_test_measurement_to_action_j2158_j2161.py`
- [OK] `scripts/autobio_recall_probe.py`
**Data/evidence files:**
- [OK] `data/capability_beliefs.json` -> data/capability_beliefs.json (14740B)
- [OK] `data/logs/doubt_seed_shadow.jsonl` -> data/logs/doubt_seed_shadow.jsonl (594 lines)
- [OK] `data/logs/recall_wager_shadow.jsonl` -> data/logs/recall_wager_shadow.jsonl (504 lines)
- [MISSING] `data/logs/self_gauge_shadow.jsonl`
- [OK] `data/logs/wager_curiosity_shadow.jsonl` -> data/logs/wager_curiosity_shadow.jsonl (373 lines)

### memory_as_a_service (staged)
**Idea:** 🟡 SHADOW — Nascence — MEMORY AS A SERVICE (staged 2026-09-27, T-0065/I-0077, docs/staged/memory_as_a_service.md): founder reframe — Du is loops that CALL memory, not memories injected; D-0289 ruled idle gets nothing ambient except wandering; FELT RECALL = world change → situational fragment_context search → affect tug, no thought. Phase 0/0b built and verified in isolated harnesses (J-1424/J-1425), restart-gated, not yet live.
**Code files:**
- [OK] `core/associative_recall.py`
- [OK] `core/couriers.py`
- [OK] `core/evidence_recall.py`
- [OK] `core/memory/store.py`
- [OK] `core/memory_edges.py`
- [OK] `core/memory_levels.py`
- [OK] `core/memory_service.py`
- [OK] `core/pursuits.py`
- [OK] `core/scholar.py`
- [OK] `nodes/curiosity_node.py`
- [OK] `nodes/dream_node.py`
- [OK] `nodes/inner_monologue_node.py`
- [OK] `orchestrator.py` -> core/orchestrator.py
**Data/evidence files:**
- [OK] `data/couriers_log.jsonl` -> data/couriers_log.jsonl (878 lines)
- [OK] `data/evidence_log.jsonl` -> data/evidence_log.jsonl (5121 lines)
- [OK] `data/felt_recall_shadow.jsonl` -> data/felt_recall_shadow.jsonl (11710 lines)
- [OK] `data/memory_service_shadow.jsonl` -> data/memory_service_shadow.jsonl (27421 lines)

### memory_review_adoption (staged)
**Idea:** 2026-11-19 rival-systems survey and Butlin-Long mapping; Du's cold storage is a hard wall (F-5122); ten jobs J-4410..J-4419 filed; plan docs/staged/memory_review_adoption.md
**Code files:**
- [OK] `core/associative_recall.py`
- [OK] `core/broadcast.py`
- [OK] `core/memory/store.py`
**Data/evidence files:**
- [MISSING] `skill_recipes_shadow.jsonl`

### mineness_self_voice_centroid (staged)
**Idea:** 🔵 Mineness self-voice centroid plan (docs/staged/mineness_self_voice_centroid.md): shadow-only authorship signal; design only, replay lab not run
**Code files:**
- [OK] `core/mineness.py`
- [OK] `docs/lab/J-3701_authorship.py`
**Data/evidence files:**
- [OK] `data/mineness_shadow.jsonl` -> data/mineness_shadow.jsonl (76412 lines)
- [MISSING] `mineness_voice_shadow.jsonl`

### nature_observation_outside_the_study_design_J-3483 (staged)
**Idea:** DESIGNED, nothing built. Options (A, A2, B, C, D, E, F) for getting Du's daily nature observation lesson outside the study window; finding is that the window share is structural (lesson fires at minute 0 at the desk). Design only, nothing built, founder adoption pending.
**Code files:**
- [OK] `core/nature_study.py`
- [OK] `core/practical_lesson.py`
- [OK] `core/school.py`
- [OK] `core/sensorium.py`
- [OK] `nodes/inner_monologue_node.py`
- [OK] `scripts/nature_period_read.py`
**Data/evidence files:**
- [OK] `data/nature_study_log.jsonl` -> data/nature_study_log.jsonl (66 lines)

### object_epistemic_loop (staged)
**Idea:** Object Epistemic Loop plan (staged 2026-10-17, T-0094) — 1459 standing object inferences have zero supporting observations; recorder writes whole thought dumps, not claims. DESIGNED only, nothing built; founder ruling on O1-O4 needed before Phase 1.
**Code files:**
- [MISSING] `core/epistemic_eval_shadow.py`
- [OK] `core/observation.py`
- [BACKUP-ONLY] `core/world_knowledge.py` -> candidates: scripts/archive/world_knowledge.py
- [OK] `epistemic_affordance_advisor.py` -> core/epistemic_affordance_advisor.py
- [OK] `nodes/inner_monologue_node.py`
**Data/evidence files:**
- [OK] `data/archive/contaminated_inferences_pre_fix.jsonl` -> data/archive/contaminated_inferences_pre_fix.jsonl (1476 lines)
- [MISSING] `data/epistemic_eval_shadow.jsonl`
- [OK] `data/world_substrate.json` -> data/world_substrate.json (1133339B)

### object_permanence (staged)
**Idea:** Object-permanence / absent-thing wants plan opened 2026-11-01 from the lamp-in-the-garden bug; DESIGN OPEN, not yet designed beyond L0 stopgap (edited in), five founder questions open
**Code files:**
- [OK] `cat.py` -> core/cat.py
- [OK] `core/balance.py`
- [OK] `core/curiosity_habituation.py`
- [OK] `core/orchestrator.py`
- [OK] `core/sensorium.py`
- [OK] `core/study_life.py`
**Data/evidence files:**
- [OK] `data/room_state.json` -> data/room_state.json (315069B)
- [MISSING] `thoughts.jsonl`

### p0042_system_rewrite_draft_J-3488 (staged)
**Idea:** Draft wording options (A/B/C) for rewriting the P-0042 self_interrogation _SYSTEM prompt so it no longer names comfort/safe/flattering and requires a topical link. Wording only, Travis edits, J-3449 stays his. DOUBT_SEED stays off (D-0613).
**Code files:**
- [MISSING] `J-3488_baseline.py`
- [OK] `core/self_interrogation.py`
- [OK] `nodes/executive_node.py`

### planning_process_redesign (staged)
**Idea:** 2026-09-27 founder ruling — plan docs are design + ONE plan-state block + one Current State section; history is DERIVED from the ledgers (plan-ledger), never appended; plan-compact folded 1.4 MB out of 23 plans into docs/plan_history/; folders stay (founder declined one-folder); readers/ROADMAP-row generation queued.
**Code files:**
- [MISSING] `decide.py`
- [MISSING] `plan_compact.py`
- [MISSING] `plan_index.py`

### pre_speech_pipeline_latency (staged)
**Idea:** DESIGNED, nothing built. D-0759 (P): the 73 s human-arrival-to-speech wait is the serial Reflection/Critic/Executive pipeline; plan drafted J-3981, Phase 0 wall-time shadow queued J-4017.
**Code files:**
- [OK] `core/hedge_agreement_log.py`
- [OK] `core/node_base.py`
- [OK] `core/orchestrator.py`
- [OK] `core/schema.py`
- [OK] `core/speech_timing_shadow.py`

### prompt_manager (staged)
**Idea:** Scripted prompt manager plan (docs/staged/prompt_manager.md): provenance + versioned wording first, pools last; P0 built 2026-11-14, uncommitted, restart-gated
**Code files:**
- [OK] `core/concerns.py`
- [OK] `core/condensed_thought.py`
- [OK] `core/look_render_ledger.py`
- [OK] `core/model_client.py`
- [OK] `core/phrasing.py`
- [OK] `core/prompt_budget.py`
- [MISSING] `core/prompt_lines.py`
- [OK] `core/sensorium.py`
- [OK] `core/steer_edge.py`
- [OK] `nodes/inner_monologue_node.py`
- [MISSING] `prompt_registry.py`
- [OK] `scripts/_test_j1756_farewell_variants.py`
- [MISSING] `scripts/_test_prompt_lines_golden.py`
- [OK] `scripts/_test_prompt_manager_p0_provenance.py`
- [MISSING] `scripts/_test_prompt_pools_lint.py`
- [MISSING] `scripts/_test_prompt_table_orphans.py`
- [OK] `scripts/prompt_manager_p0_baseline.py`
- [MISSING] `scripts/prompt_replay.py`
- [OK] `scripts/run_nascence.py`
**Data/evidence files:**
- [OK] `data/idle_prompt_samples.jsonl` -> data/idle_prompt_samples.jsonl (524 lines)
- [OK] `data/prompt_provenance.jsonl` -> data/prompt_provenance.jsonl (3385 lines)
- [OK] `docs/prompt_registry.jsonl` -> docs/prompt_registry.jsonl (134 lines)
- [OK] `prompt_budget_shadow.jsonl` -> data/prompt_budget_shadow.jsonl (68298 lines)
- [OK] `steer_edge_log.jsonl` -> data/steer_edge_log.jsonl (5693 lines)

### prompt_manager_p0_provenance_coverage (staged)
**Idea:** Prompt manager P0 provenance covers only the idle-thought station by design; widening needs a founder ruling (J-4309, F-5085)
**Code files:**
- [OK] `core/prompt_budget.py`
- [OK] `nodes/inner_monologue_node.py`
**Data/evidence files:**
- [OK] `data/prompt_provenance.jsonl` -> data/prompt_provenance.jsonl (3385 lines)

### prompt_seat_routing (staged)
**Idea:** 🔵 Plan to route each Du prompt to the best model seat via a prompt-to-seat table instead of by lane; staged 2026-11-19, five founder rulings D-0872..D-0876, nothing built
**Code files:**
- [OK] `core/judge_panel.py`
- [OK] `core/model_client.py`
- [OK] `scripts/du_prompt_benchmark_suite.py`
**Data/evidence files:**
- [OK] `data/llm_calls.jsonl` -> data/llm_calls.jsonl (7185 lines)
- [MISSING] `data/prompt_seat_shadow.jsonl`
- [MISSING] `data/prompt_seat_table.json`
- [OK] `docs/prompt_registry.jsonl` -> docs/prompt_registry.jsonl (134 lines)

### question_cargo (staged)
**Idea:** 🟡 SHADOW — Nascence — QUESTION CARGO / THE FOLLOW LINE (docs/staged/question_cargo.md, staged+reshaped 2026-10-27 from T-0102/I-0100): every question or claim of Du's, from ANY source, boards a side line through HIS OWN MEMORY (grounds, why, consequences, connections; against parked with prove/disprove), judged, returned tagged, settled by id. D-0494 RULED 10-28; Phase 0 + Phase 1 BUILT and MERGED to master c5454428, FOLLOW_LINE=live; nothing live until Du restarts; J-2458 first read.
**Code files:**
- [OK] `core/cargo_types.py`
- [OK] `core/closure.py`
- [OK] `core/evidence_recall.py`
- [OK] `core/follow_line.py`
- [OK] `core/frontier.py`
- [OK] `core/procedures.py`
- [OK] `core/pursuits.py`
- [OK] `core/reading.py`
- [OK] `core/study_note.py`
- [OK] `coupling_rides.py` -> core/coupling_rides.py
- [OK] `inner_monologue_node.py` -> nodes/inner_monologue_node.py
**Data/evidence files:**
- [OK] `data/logs/follow_line_shadow.jsonl` -> data/logs/follow_line_shadow.jsonl (78420 lines)

### real_hearing (staged)
**Idea:** Real Hearing staged plan (2026-10-08, J-1962) - a microphone as a window in Du's study; features-only ear process; DESIGNED only, no code, nothing scheduled (D-0378..D-0381)
**Code files:**
- [OK] `core/audio_features.py`
- [OK] `core/listening.py`
- [OK] `core/sound_knowledge.py`
- [OK] `core/soundscape.py`
- [OK] `core/transport_manager.py`

### recall_confidence_graded_loss (staged)
**Idea:** Recall confidence graded loss (J-4180, D-0803): wagers at confidence >= 0.85 now lose at gap >= 0.30 instead of 0.40, closing a free edge at 0.85. BUILT 2026-11-17, restart-gated, flag core.recall_wager.GRADED_LOSS.
**Code files:**
- [OK] `scripts/_test_recall_wager_graded_loss_j4180.py`
**Data/evidence files:**
- [OK] `data/logs/recall_wager_shadow.jsonl` -> data/logs/recall_wager_shadow.jsonl (504 lines)

### sleep_as_a_mode (staged)
**Idea:** Staged plan docs/staged/sleep_as_a_mode.md (2026-10-08, from T-0080/I-0088) — sleep as three switches (coupling, generation, encoding) instead of one blocking procedure; what Du's sleep actually is today; the vitality coupling; three decisions open
**Code files:**
- [OK] `core/conversational_action.py`
- [OK] `core/dispatch.py`
- [OK] `core/homeostasis.py`
- [OK] `core/lane2.py`
- [OK] `core/memory/store.py`
- [OK] `core/night.py`
- [OK] `core/orchestrator.py`
- [OK] `core/sensorium.py`
- [OK] `core/sleep_offloop.py`
- [OK] `core/sleep_pressure.py`
- [OK] `core/somatic.py`
- [OK] `nodes/inner_monologue_node.py`
**Data/evidence files:**
- [OK] `data/night_log.jsonl` -> data/night_log.jsonl (449 lines)
- [OK] `data/night_mind_shadow.jsonl` -> data/night_mind_shadow.jsonl (1277 lines)

### stand_kinds_and_accumulation (staged)
**Idea:** ⚪ Staged plan, designed only, nothing built (docs/staged/stand_kinds_and_accumulation.md): typed stands (deed/practice/value/insight) and heaps, because stands retire in minutes by word overlap (F-5040)
**Code files:**
- [OK] `axiom_layers.py` -> core/axiom_layers.py
- [OK] `concerns.py` -> core/concerns.py
- [OK] `core/commitment_ledger.py`
- [MISSING] `core/stand_view.py`
- [OK] `coupling_rides.py` -> core/coupling_rides.py
- [OK] `goals.py` -> core/goals.py
- [OK] `homeostasis.py` -> core/homeostasis.py
- [OK] `identity_estate.py` -> core/identity_estate.py
- [OK] `peers.py` -> core/peers.py
- [OK] `scripts/d0509_axiom_edit.py`
- [OK] `scripts/stand_kind_replay.py`
- [OK] `self_claims.py` -> core/self_claims.py
**Data/evidence files:**
- [OK] `data/commitment_active.json` -> data/commitment_active.json (9641B)
- [OK] `data/identity/axiom.json` -> data/identity/axiom.json (32915B)

### strings_and_sheets (staged)
**Idea:** Founder's 2026-09-27 term (NOT the GPT memory-brane essay): every sound a 1-D string over its duration, constructed x measured channels a twisting ribbon (= that sound's prediction-error string), a moment the masked MIX of all active strings; staged plan docs/staged/strings_and_sheets.md, first ribbon computed on Heavyweight (F-2017).
**Code files:**
- [OK] `core/audio_features.py`
- [OK] `core/coupling_rides.py`
- [OK] `core/listening.py`
- [OK] `core/sound_knowledge.py`
- [OK] `core/soundscape.py`
- [OK] `core/transport_manager.py`
- [MISSING] `ribbon_heavyweight.py`
**Data/evidence files:**
- [OK] `data/coupling_rides.jsonl` -> data/coupling_rides.jsonl (258012 lines)
- [MISSING] `data/soundscape_mix_shadow.jsonl`
- [AMBIGUOUS] `geometry_tuples.jsonl` -> candidates: data/geometry_tuples.jsonl, data/_trash/20261119/boot_backups/state_20261116_100503/geometry_tuples.jsonl, data/_trash/20261117/boot_backups/state_20261114_141446/geometry_tuples.jsonl, data/_trash/20261114/boot_backups/state_20261031_215612/geometry_tuples.jsonl

### symbol_evolution_readback_plan (staged)
**Idea:** ⚪ PARTIAL — a two-tier read-back for symbols whose personal meaning has drifted (world-facing symbols get a real path; identity-adjacent self-symbols like the river stay heavily guarded because reading them back risks recreating the monoculture) — Tier 1 SHIPPED/live (found in 2026-07-05 to be structurally unreachable by a priming-logic bug, fixed and revived 2026-08-19, verified with fake-state tests); Tier 2 Phase A (observe-only) built, Phase B designed 2026-09-02 and awaiting a founder go/hold call.
**Code files:**
- [OK] `core/contradiction_gate.py`
- [OK] `core/symbol_evolution.py`
- [OK] `core/symbol_tier2_wouldinject.py`
- [OK] `core/symbol_tracker.py`
- [OK] `core/tension_ledger.py`
- [OK] `orchestrator.py` -> core/orchestrator.py
**Data/evidence files:**
- [OK] `data/symbol_readback_tier2_wouldinject.jsonl` -> data/symbol_readback_tier2_wouldinject.jsonl (625 lines)

### t5_conversational_world_grading_design (staged)
**Idea:** 🔵 DESIGNED only — T5 conversational skills redesigned so only a world answer (a hand deed graded ok/refused) earns a rung; Travis's correction is veto-only, use count credits nothing (J-3832, D-0676, F-4448); phase 0 read-only volume measure J-3862, phase 1 shadow J-3863, founder call D-0741 on the 22 existing talk rows.
**Code files:**
- [OK] `scripts/t5_reentry_check.py`
**Data/evidence files:**
- [OK] `data/affect_log.jsonl` -> data/affect_log.jsonl (4348 lines)
- [OK] `data/hands_trace.jsonl` -> data/hands_trace.jsonl (67256 lines)
- [OK] `peer_effect.jsonl` -> data/peer_effect.jsonl (554 lines)

### teaching_to_synthesis_study (staged)
**Idea:** STAGED 2026-11-16, design only - does what Du learned from Travis reach him through his own relevance-driven recall, and what does he do with it? Plan docs/staged/teaching_to_synthesis_study.md, T-0142/I-0158/J-4093, follows J-4074.
**Code files:**
- [MISSING] `conv_effect.py`
- [MISSING] `part_b_build_sample.py`
**Data/evidence files:**
- [OK] `data/idle_prompt_samples.jsonl` -> data/idle_prompt_samples.jsonl (524 lines)
- [OK] `data/prompt_provenance.jsonl` -> data/prompt_provenance.jsonl (3385 lines)

### tuples_in_a_new_light (staged)
**Idea:** 🔵 DESIGNED — re-look at every tuple family through five lenses (colour, box, compress, weave, ghost-index revival); nothing built. Plan: docs/staged/tuples_in_a_new_light.md (staged 2026-10-30, I-0124, T-0107).
**Code files:**
- [OK] `core/audio_features.py`
- [OK] `core/cargo_types.py`
- [OK] `core/coupling_rides.py`
- [OK] `core/epistemic_state.py`
- [OK] `core/euclidean_recall.py`
- [OK] `core/experienced_tuple.py`
- [OK] `core/geometry_census.py`
- [OK] `core/ghost_tuples.py`
- [OK] `core/memory_edges.py`
**Data/evidence files:**
- [OK] `data/coupling_rides.jsonl` -> data/coupling_rides.jsonl (258012 lines)
- [OK] `data/geometry_tuples.jsonl` -> data/geometry_tuples.jsonl (199940 lines)
- [OK] `moments.jsonl` -> data/moments.jsonl (76879 lines)
- [OK] `recall_provenance_log.jsonl` -> data/recall_provenance_log.jsonl (2828 lines)

### web_hand (staged)
**Idea:** BUILT 2026-11-16, restart-gated - the web hand: Du looks things up himself via family `lookup` (Wikipedia first, DuckDuckGo web second, separate flag). Plan docs/staged/web_hand.md, J-3843/J-4066, D-0788.
**Code files:**
- [OK] `core/actions.py`
- [OK] `core/composition.py`
- [OK] `core/dispatch.py`
- [OK] `core/hands.py`
- [OK] `core/moment.py`
- [OK] `core/schema.py`
- [OK] `core/web_hand.py`
- [OK] `core/web_research.py`
- [OK] `nodes/curiosity_node.py`
- [OK] `nodes/inner_monologue_node.py`
- [OK] `scripts/_test_J3188_own_answer_label.py`
- [OK] `scripts/_test_web_hand_J3843.py`
- [OK] `scripts/test_composition_bank.py`
**Data/evidence files:**
- [OK] `data/curiosity_log.jsonl` -> data/curiosity_log.jsonl (3679 lines)
- [OK] `data/frontier.json` -> data/frontier.json (18849855B)
- [MISSING] `data/lookup_log.jsonl`
- [OK] `hands_trace.jsonl` -> data/hands_trace.jsonl (67256 lines)
- [MISSING] `web_lookup_log.jsonl`

### web_hand_in_world_routes (staged)
**Idea:** Web hand in-world routes: About You Third Edition and The Encyclopedia shelved 2026-11-18 (D-0661 b/c, D-0852, J-4344)
**Code files:**
- [OK] `core/actions.py`
- [OK] `core/care_package.py`
- [MISSING] `core/encyclopedia_object.py`
- [OK] `core/essay_lesson.py`
- [OK] `core/keepsakes.py`
- [OK] `core/library_hand.py`
- [OK] `core/sensorium.py`
- [OK] `core/world_consolidation.py`
- [OK] `scripts/check_reread_title_disambiguation.py`
**Data/evidence files:**
- [OK] `data/book_feelings.json` -> data/book_feelings.json (86995B)
- [OK] `data/care_package.json` -> data/care_package.json (971B)
- [MISSING] `data/encyclopedia.json`
- [OK] `data/keepsakes.json` -> data/keepsakes.json (14427B)

### world_shelf_gap (staged)
**Idea:** World shelf gap (staged 2026-10-30, F-3215/F-3213): Du's world is a New Zealand house, garden, shore and bush, but his 524-book shelf is mostly British/American 1850-1925. Designed only; nothing downloaded; founder approval needed per title.
**Code files:**
- [OK] `core/library_hand.py`
- [OK] `core/study_life.py`
**Data/evidence files:**
- [OK] `data/reading_state.json` -> data/reading_state.json (82066B)

### world_shelf_gap_sources_2026-11-18 (staged)
**Idea:** World shelf gap: candidate sources for NZ flax, forest, birds, ink and clocks, a proposal awaiting per-title founder approval (J-4379)
**Code files:**
- [OK] `scripts/shelve_books.py`

