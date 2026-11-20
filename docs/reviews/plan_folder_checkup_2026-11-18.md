# Plan folder checkup, 2026-11-18 (placement only, not content)

Counts: plans/ 61 files, staged/ 65, shelf/ 3. Stage read from each doc's `plan-state` block. Folder convention from
ROADMAP.md line 5: shipped -> `completed/`, shelved with a trigger -> `staged/DEFERRED_PLANS.md` + `shelf/`,
superseded/retired -> `archive/`; CLAUDE.md rule 3: drafting -> `staged/`, live -> `plans/`.
**Nothing has been moved.** Moving breaks ROADMAP links, so a move needs the link rewrite done with it.

## A. plans/ -> completed/ (stage shipped, next = "None, closed")
du_initiated_upgrade_trigger, du_pulse_rebuild, emissary_lane2_cognition, fieldcraft, hud2_visual, sound_causality,
study_upgrade, lane2_lab (8). Keep in plans/ for now: gauge_rethink (D-0102 re-rule pending), decoupled_judge_pattern
(replays pending), factory_candidates_from_history (live on next restart).

## B. plans/ -> archive/ (superseded or retired)
cognitive_loop_actuation, euclidean_memory_plan, generative_world_sedimentation,
multidimensional_dynamical_field_side_plan, thought_cycle_as_manifest_loop, world_census (6).
Also shelf/ -> archive/: active_imagination_plan (retired), attention_economy_plan (superseded).
staged/ -> archive/: multidimensional_dynamical_field_plan (superseded).

## C. plans/ -> staged/ (not live: designed or idea)
lod_staged_retrieval (designed, 51 d idle), object_permanence (idea).

## D. staged/ -> plans/ (stage live, in production)
actions_expansion, conversational_action_bridge, data_store_hygiene, dosed_coupling, ignition_pressure_and_time,
living_world_upgrade, music_learning, practical_school, shore_creatures, wood_creatures, world_store_write_fence (11).
staged/ -> completed/: actions_manager_overhaul, garden_living_upgrade (both closed). udms_du_capability_trials is
`shipped` but has J-3781 pending: plans/.
Judgment call: ~25 more staged plans are `built` or `shadow`, restart-gated, awaiting evidence. ROADMAP treats staged/
as the home for shadow builds (AWAITING_EVIDENCE.md), so I left them. If "live = plans/" is the rule, they stay put
until the flag flips.

## E. staged/ -> shelf/ (stage deferred)
idle_executive_plan, pulse_manager_wiring_plan (DEFERRED_PLANS.md already lists shelved entries).

## F. Docs with no `plan-state` block (plan-state init needed)
follow_line_stricter_settle, nature_observation_outside_the_study_design_J-3483,
recall_confidence_graded_loss, t5_conversational_world_grading_design, web_hand (built, no next line),
p0042_system_rewrite_draft_J-3488 (a draft, not a plan).

## G. Stale and idle (50+ days unchanged)
antigravity_ecosystem_proposals (partial 51 d; project memory says Antigravity is off Nascence, so retire or
re-scope), fragment_carries_the_string (built 50 d, waits on restart), planning_process_redesign (built 50 d),
lod_staged_retrieval, lane2_lab, train_courier_cargo_ids (46 d, D-0320 founder call).

## H. Ready to progress now (no blocker except a build or a read)
- pre_speech_pipeline_latency: build the Phase 0 shadow.
- curiosity_librarian_route: run the read-only dry-run.
- ambiguity_window: J-2451 held-out replay.
- tuples_in_a_new_light: J-2536 join audit first.
- stand_kinds_and_accumulation: P1 built; P2 (heaps) is next.
- web_hand, closure_producer, closure_law, cat_overhaul: restart passed or about to, so first reads are due.

## I. Waiting only on a founder ruling
maths_of_mind_atlas (D-0775/6), model_swap_aba_test (J-3996), speech_thought_concurrency (D-0759),
loop_wiring_matrix, golden_spiral_recall (Phase 2 past shadow), self_claim_broadcast_reexamination_J-3487,
in_world_companion_mind, world_shelf_gap, du_recall_lens_upgrades (HOLD, D-0684).
