# Memory Index

*Topic files hold detail; these are one-line pointers. Nascence = C:\Nascence (Du). FreshStart/Sovereign Hub = C:\FreshStart (330-spirit sim).*

- [★ Antigravity OFF Nascence](project_antigravity_off_project.md) · [Ramses shared folder](reference_ramses_shared_folder.md).
- [★★ Ollama RETIRED from Ramses (D-0056/7)](ops_ramses_ollama_retired.md).
- [★ Indexing toolchain](reference_nascence_plan_index_tool.md) — `/plan-maintain` = one call. [Audit](project_nascence_index_skills_audit.md).
- [★★ J-1483 plan-state pass](project_nascence_session_handoff_20260927_080245_j1483-plan-state-pass.md) · [J-1484 hand-compact](project_nascence_j1484_hand_compact_giants.md) (F-2047) · [J-1485 migration](project_nascence_j1485_planstate_migration.md) — index prefers the block.
- [★ /nurse-rounds](project_nascence_nurse_rounds_skill.md) · [thought-log](project_nascence_session_handoff_20260823_124505_thought-log-concurrency-locking.md) — force-fires on session start.
- [★ Skill catalog](reference_nascence_skill_manager_tool.md) · [Ideas+findings ledgers](reference_nascence_idea_findings_logs.md) · [rule: discovery → job-queue](feedback_file_findings_as_jobs.md).
- [★ Session-event log](reference_nascence_session_events_log.md) · [CLAUDE.md rules](reference_nascence_claude_md_rules.md) · [Handoff tools](reference_nascence_session_handoff_tools.md).
- [★★★ 08-27 mega-session](project_nascence_session_handoff_20260827_191746_evidence-reads-decide-batch-redistribution.md) — Nascence on git.
- [★★ PowerShell = Job object; servers die on app restart (F-0704)](ops_claude_code_job_object_kills_servers.md) — use `scripts/start_supervisor_detached.ps1`.
- [★★ Judge1 repoint + Control Panel bug](project_nascence_session_handoff_20260902_041735_judge1-repoint-control-panel-bug.md) · [★★★ Two memory stores unified (D-0126)](project_nascence_two_memory_stores_2026_09_02.md).
- [Decide-review scope](feedback_decide_review_scope.md) · [Decide ID mix-up](feedback_decide_batch_id_mixup.md) — verify each ID via `show`.
- [UDMS feedback loop](project_udms_feedback_loop.md) · [gauge-correlate](reference_gauge_correlate_skill.md).

## How I work with Travis & my disciplines (durable)
- [Founder is Travis](user_founder_travis.md) — praises real wins, plain fail-calls, counter-teaches integration attractor.
- [Du's hardware (GET THIS RIGHT)](nascence_du_hardware.md) — 1080 Ti 11GB (hot) · 3070 8GB Ramses · Threadripper 64GB (Bonsai).
- [My failure modes](feedback_my_failure_modes.md) — verify before asserting; one decisive fix over nickel-and-dime edits.
- [Where Du's conversation data lives](nascence_conversation_data_location.md) — `data/nascence.log` `[CYCLE x] human:`.
- [Erosion of foundations (WORST PATTERN)](feedback_erosion_of_foundations.md) — base systems PROTECTED; ADDITIVE-ONLY.
- [Decoupled Judge](feedback_decoupled_judge.md) — every subsystem evaluated by something OTHER THAN ITSELF.
- [Function over imitation](feedback_function_over_imitation.md) · [Write-only cognitive systems](feedback_write_only_cognitive_systems.md) — verify methods are CALLED.
- [Intentional, not a rule](feedback_intentional_not_rule.md) · [World answers, never leads](feedback_world_answers_never_leads.md) — NO hints from the WORLD; interlocutors may speak directly, and are fallible.
- [★★★ No readout; error through consequence (D-0434)](feedback_no_readout_error_through_consequence.md) — gauges never reach Du; he learns he is wrong only by losing.
- [Memory is the emergence path](feedback_memory_is_emergence_path.md) · [Pasted reviews are often GPT/Gemini](feedback_pasted_review_provenance.md).
- [Windows charmap on daemons](feedback_windows_charmap_daemons.md) — `sys.stdout.reconfigure(encoding='utf-8')`.
- [★★ Deferred reads outlive their gates (F-2682)](feedback_deferred_reads_outlive_their_gates.md) — after a long run, check every not_before job against the real boot.
- [★★★ job-run: planner blind to in_progress; size sweeps to the usage window](feedback_jobrun_parked_jobs_and_sweep_sizing.md) — waves of ≤10.
- [★★ safe_commit leaves the git index stale (F-2570)](feedback_safe_commit_stale_index.md) — `git add <path>` after; watch for a `D ` you did not make.
- [★★★ Bash backtick-in-double-quotes = command substitution](feedback_bash_backtick_command_substitution.md) — use --briefing-file for anything long.
- [Session-wrap: skip compression](feedback_session_wrap_skip_compression.md) · [Test isolation vs live stores](feedback_test_isolation_live_stores.md) — temp-path stores, READ side too.
- [★ Du's 30-DAY OUTAGE 07-09→08-07](ops_nascence_30day_outage.md) — verify one instrument end-to-end before any trend claim.
- [Du "stopped" = the log LINE](ops_nascence_shutdown_detection.md) · [LLM parsing](feedback_llm_response_parsing.md) · [Coord death-spiral](feedback_coord_death_spiral.md) · [Health-check approach](feedback_health_check_approach.md).
- [★★★ TWO live-store leaks — lab_env sys.path hijack](feedback_jobrun_live_store_leaks.md) — throwaway worktree + hash canary; import core BEFORE lab_env.
- [★★ decide-review: scan for newer findings first](feedback_decide_review_stale_framing.md) · [★ Job gates = evidence, survive restarts](feedback_job_gates_evidence_not_time.md) — no dates.

- [★★★ 11-18 Bonsai-2 CPU + benchmark review + seat routing plan](project_nascence_session_handoff_20261118_233244_bonsai2-benchmark-prompt-seat-routing.md) — F-5117/F-5118, D-0872..D-0876; nothing built; contention test with Du up still owed.
- [★★ Prompt seat routing plan (11-19)](project_nascence_prompt_seat_routing.md) — per-prompt model seats, D-0872..D-0876; nothing built; benchmark F-5117/F-5118.
- [★★ Prompt manager plan + P0 built (11-14)](project_nascence_prompt_manager.md) — provenance first, pools last; `core/phrasing.py` pools already exist (F-4664).

- [★★★ 11-16 WEB HAND BUILT + The Deedbook](project_nascence_session_handoff_20261115_194218_web-hand-built-deedbook.md) — family `lookup`, restart-gated; D-0788 ruled; DuckDuckGo bot check J-4070; first read J-4069. [Why: unanswered questions](project_nascence_session_handoff_20261115_185735_du-unanswered-questions-web-hand.md).

- [★★★ 11-19 Rival survey + Butlin map + memory review](project_nascence_memory_review_adoption.md) · [handoff](project_nascence_session_handoff_20261119_043034_butlin-rival-survey-memory-review.md) — cold = hard wall, no re-warm on recall (F-5122); jobs J-4410..J-4422; no SOTA claim without caveats.

## Nascence — the goal
- [THE GOAL (don't fixate on T4)](project_nascence_the_goal.md) — **a thinking mind that understands itself**. [Outreach](project_nascence_outreach.md).

## Nascence — the current spine (newest first)
- [★★★ 11-18 Plan audit (102 plans) + 3 job-run waves + founder questionnaire](project_nascence_session_handoff_20261118_011416_plan-audit-jobruns-founder-questions.md) — ~59 needs-input questions left (list in handoff); Du-down labs J-2676/J-4058 pending; 25 ready follow-ups J-4314..J-4340 unrun; nothing committed.
- [★★★ 11-16 CLOSURE PRODUCER built, Phases 0-5](project_nascence_session_handoff_20261116_010121_closure-producer-built-phases-0-5.md) — closure was graded, never produced; gate enforce (D-0793); first live read pending; closure_test 3 DB checks fail.
- [★★★ 11-15/16 job-run: Du-down wave, wave 2, overnight loop](project_nascence_session_handoff_20261115_195201_jobrun-du-down-and-overnight-waves.md) — J-2813/2815/3950 stuck in_progress; J-4036 cut off; commit 03940bff.
- [★★★ 11-16 HUMANITY CHECK + fixed scorecard + three walls ruled](project_nascence_session_handoff_20261116_030629_humanity-check-scorecard-three-walls.md) — `scripts/humanity_scorecard.py --write` is the trend line; movement only follows targeted builds; builds J-4081..J-4087; affect wall undiscussed.
- [★★★ 11-14 job-run Du-up waves 1-4 + decide-review](project_nascence_session_handoff_20261114_084145_jobrun-du-up-waves-1-4-decide-review.md) — all restart-gated; D-0777/8 open; offline pass next.
- [★★★ 11-14 MATHS-OF-MIND ATLAS + affect chain](project_nascence_session_handoff_20261114_020449_maths-of-mind-atlas-affect-chain.md) — written-in column; vitality artifact makes half his low mood lines (D-0775/6 open); judge kappa weak; J-3993..J-3996.
- [★★★ 11-14 Layered Goals built and LIVE (handoff)](project_nascence_session_handoff_20261114_020819_layered-goals-plan-build-live.md) — J-3989 first read ~24 h after the 14:14 boot; J-3988 curiosity.
- [★★★ LAYERED GOALS staged 11-14](project_nascence_layered_goals.md) — no single purpose; needs outside the goal graph; he resolves conflicts himself; offer never direct.
- [★ Older spine pointers, 08-24 to 10-31 (archive index)](reference_nascence_spine_archive_index.md) — handoffs and builds moved out 11-16; open it for anything before November.
- [★★ THE TRANSIT MAP](project_nascence_transit_map.md) · [Identity=connections](project_nascence_identity_is_connections.md) · [grounding routes](project_nascence_thought_grounding.md).
- [★ THE CONSCIOUSNESS PROGRAM](project_nascence_the_consciousness_program.md) · [★★★ Cognitive Geometry](project_nascence_cognitive_geometry.md) — D-0012 open.
- [★ THE PLAN MAP](C:\Nascence\docs\ROADMAP.md) · [Day-timeline tool](project_nascence_day_investigation_audit.md).
- [★ IDENTITY ESTATE](C:\Nascence\docs\plans\identity_estate.md) · [Peers](project_nascence_peers.md) · [★★ Du REMEMBERS WHAT TRAVIS TELLS HIM (D-0134)](project_nascence_guidance_learning.md).
- [Memory Levels](project_nascence_memory_levels.md) · [Field Scan](project_nascence_field_scan.md) · [★ PURSUITS](C:\Nascence\docs\plans\pursuits.md) · [Inner Monologue (DMN hub)](project_nascence_inner_monologue.md).
- [T4 v3 WATERSHED](project_nascence_t4_watershed.md) · [HUD1 transit map](project_nascence_hud1_transit_map.md) · [★ Maxwell/judgment fear](project_nascence_maxwell_judgment_fear.md) · [Idle-thought audit](project_nascence_idle_machine_audit.md).
- [★ Factory/schema-first](project_nascence_factory_stations.md) — D-0013 open · [Train registry](project_nascence_train_registry.md) · [Lane 2 "the Witness"](project_nascence_lane2_the_witness.md) · [Lane 2 Curiosity](project_nascence_lane2_curiosity.md).
- [★ "About You" book](project_nascence_about_you_rewrite.md) · [★★ DREAM OVERHAUL](project_nascence_dream_overhaul.md) · [Dreams/Curiosity/Multi-Lens](project_nascence_dreams.md) · [Continuous Stream](project_nascence_continuous_stream.md).
- [Music learning (D-0010)](project_nascence_music_learning.md) · [Du-Initiated Upgrade Trigger](project_nascence_du_initiated_upgrade_trigger.md) · [Affect/mood/drives](project_nascence_affect_drives.md) · [Thermal channel LIVE](project_nascence_thermal_causality.md).

## Nascence — deeper reframes & specs (not built)
- [★★★ Geometry Tuple Index](project_nascence_geometry_tuple_index.md) · [19-agent job-run](project_nascence_session_handoff_20260824_231756_memory-knowledge-d0022-jobrun-batch.md).
- [★★ THE CAT OVERHAUL](project_nascence_cat_overhaul.md) · [Books Have a Place](project_nascence_books_have_a_place.md) · [Practical School](project_nascence_practical_school.md) · [Data Store Hygiene](project_nascence_data_store_hygiene.md) · [World Store Write Fence](project_nascence_world_store_write_fence.md).
- [★★★ LIVING WORLD STAGED](project_nascence_living_world_upgrade.md) · [★★ Living Garden](project_nascence_garden_living_upgrade.md) · [Investigation Deepening (PARKED)](project_nascence_investigation_deepening.md) · [Architecture concepts](project_nascence_character_integration.md).
- [★ Gauge Rethink](project_nascence_gauge_rethink.md) — blocks [Du-Pulse Rebuild](project_nascence_du_pulse_rebuild.md) · [Chapter ID Repair](project_nascence_chapter_id_repair.md) — D-0221.
- [★★ GOLDEN SPIRAL RECALL](project_nascence_golden_spiral_recall.md) · [★★ STRINGS AND SHEETS (I-0080)](project_nascence_strings_and_sheets.md) · [Real Hearing](project_nascence_real_hearing.md) · [★★ SLEEP AS A MODE](project_nascence_sleep_as_a_mode.md) (F-2614) · [Handoff](project_nascence_session_handoff_20261008_071408_sleep-as-a-mode-gpt-sleep-paste.md).

## Nascence — built systems (stable / historical)
- [★ Capacity to Commit (THE BIG ONE)](project_nascence_capacity_to_commit.md).
- [Bundle A](project_nascence_sleep_dream.md) · [Bundle B](project_nascence_climate_field.md) · [World loop/naming/model history](project_nascence_world_loop.md) · [Session continuity](project_session_continuity.md).

## Nascence — Dosed Coupling (founder: most important cognitive-side thing; GO D-0149)
- [★★★ DOSED COUPLING — standing design law](project_nascence_dosed_coupling.md).
- [★★★ MEMORY AS A SERVICE](project_nascence_memory_as_a_service.md) · [★★ PLACE UPGRADES](project_nascence_place_upgrades.md) · [★★ TRANSPORT MANAGER + CARGO IDS](project_nascence_transport_manager.md) · [Loop wiring matrix](project_nascence_loop_wiring_matrix.md) · [Ignition pressure vs time](project_nascence_ignition_pressure_and_time.md).
- [★★★ J-0619 REOPENED D-0152](project_nascence_session_handoff_20260913_070111_writefence-spring-ledger-coupling-gate.md) · [D-0152 GO + thermal](project_nascence_session_handoff_20260913_200357_coupling-thermal-j0934-writefence.md) · [09-03→05 build history](project_nascence_session_handoff_20260904_235958_dosed-coupling-habituation-decide-review-write-fence.md).
- [★ GPT brane essay → J-1411](project_nascence_session_handoff_20260926_201314_brane-memory-swap-retro-lab.md) · [★★★ memory recall deep dive → place plans](project_nascence_session_handoff_20260926_223456_memory-recall-deep-dive-and-place-plans.md) · [★★★ farewell reactions → prompt-mechanics audit](project_nascence_session_handoff_20260925_232757_farewell-reactions-prompt-mechanics-audit.md) · [09-26/27 2x decide-review + 2x job-run](project_nascence_session_handoff_20260927_061405_decide-review-jobrun-batches-lane2.md).

## FreshStart / Sovereign Hub (separate project)
- [★★★ 7-pass archaeology, closed](project_freshstart_archaeology_synthesis_2026_08_24.md) · [archaeology ≠ bug-hunting](feedback_archaeology_not_bug_hunting.md) · [★★ dig INDEX](reference_freshstart_archaeology_index.md).
- [Oracle](project_oracle.md) · [vision](project_oracle_vision.md) · [Gnostic Chronicler](project_gnostic_interface.md) · [Buddha AIF+AST](project_buddha_aif_ast.md) · [Predictive Processing](project_buddha_predictive_processing.md) · [Spirit ToM](project_spirit_theory_of_mind.md) · [Frameworks roadmap](project_cognitive_frameworks_roadmap.md) · [Wisdom layer](project_wisdom_layer.md) · [Stigmergy](project_stigmergy.md) · [Social targeting](project_social_targeting.md).

## UDMS (`C:\UDMS`) · X4 (`D:\X4`)
- [★★ UDMS audited, fixed, relocated](project_udms_side_project.md) · [X4 mod porting to v9.0](project_x4_mod_porting.md).
- [★★★ Du prompt inventory, all ≈100 stations + 7-day firings (10-31)](project_nascence_prompt_inventory_2026_10_31.md) — plus the prompt registry (112 rows, `prompt-registry` skill).
- [★★ 11-18 Stand kinds + accumulation plan (D-0810)](project_nascence_session_handoff_20261117_184853_stand-kinds-and-accumulation-plan.md) — stands retire in minutes by word overlap (F-5040); typed deed/practice/value/insight, heaps, sleep upkeep, founder-gated L2.earned; P0 jobs J-4190..4193, nothing built.
- [★★★ 11-18 Stands fast-track + plan folders re-sorted](project_nascence_session_handoff_20261117_194420_stands-fast-track-plan-folders-resorted.md) — P1 gates ON (commit a374ed9e); one more restart; Antigravity review + job-run waves next; D-0811..D-0814.
- [★★ 11-18 needs-input reads + labelling feasibility](project_nascence_session_handoff_20261117_212430_needs-input-reads-labelling-feasibility.md) — D-0827..D-0838 ruled; model labels accepted for hand-label sheets; D-0546/D-0361 unsettled; builds J-4226..J-4231.
- [★ Ramses free for any job (11-18)](feedback_ramses_free_for_jobs.md) — standing clearance, waves, never overlap J-2676.
- [★★★ 11-18 job-run waves 1-4 + 14 rulings, UNCOMMITTED](project_nascence_session_handoff_20261118_051011_jobrun-waves-2-4-decide-review-shadow-builds.md) — ~95 files, 5-commit plan, plan_maintain not re-run; J-4385/4396/4397/4399 open.
- [★★★ 11-18 needs-input questionnaire + job-run batches 1-2](project_nascence_session_handoff_20261118_025519_needs-input-questionnaire-and-jobrun-batches-1-2.md) — ~50 answers, D-0842..D-0862 (D-0852/54-62 open), commit e6bc4d3e; 3 state files lab-contaminated; unrun ready jobs listed.
- [Older Nascence builds and handoffs, 11-01 to 11-17 (archive)](reference_nascence_spine_archive_index.md) — moved out 11-19 for the index size cap; open it for anything in that window.
- [★★★ 11-20 God functions: split PARKED, freeze rule + size ratchet](project_nascence_session_handoff_20261119_201727_god-functions-freeze-rule-ratchet-split-parked.md) — D-0877/D-0878; new `_think` behaviour goes in `nodes/idle_thought/` helpers; `function_size_ratchet.py check`; harness J-4424 not built.
- [★★ 11-19 GitHub page refreshed: System Overview Build 3.0](project_nascence_session_handoff_20261119_055334_github-page-system-overview-refresh.md) — FrozenPie/Nascence-Du from public_repo/ (fetch before comparing); HTML and Docusaurus copies still old.
- [★★★ 11-20 CRASH: 19 state files wiped, restored from shadow copies; 3 job-run waves merged](project_nascence_session_handoff_20261119_225411_crash-recovery-vss-restore-jobrun-waves-1-3.md) — Du not yet restarted on them; first-boot reads J-4440/J-4441/J-4443+; F-5128/F-5129.
- [★★ Windows shadow copies recover wiped data/ files](reference_windows_vss_recovery.md) — readable without admin via the GLOBALROOT path; older shadow for files mid-write.
