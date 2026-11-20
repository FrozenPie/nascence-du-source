# udms_hygiene dead-function triage (J-3469, UDMS roadmap item 8) - 2026-11-07

**Status:** analysis only, nothing deleted, nothing wired. Spawned follow-up jobs are listed in section 6.
**Origin:** F-4098 (30 of 63 core/+nodes/ hygiene leads had zero text references on 2026-11-06). **Tool built:**
`scripts/hygiene_ref_scan_J3469.py` (token-stream scan), data in `docs/lab/J-3469_data/` (`leads.json`,
`scan_results_2026-11-07.json`), test `scripts/_test_J3469_hygiene_scan.py`.

## 1. Answer in four lines

1. **All 30 confirmed dead, by a stricter test than F-4098's.** The token scan (comments and docstring bodies are not
   code) finds no NAME token and no string literal for any of the 30 anywhere in the tree (`.claude` worktrees excluded).
2. **J-0383's verdict was never given.** It started 2026-08-29 00:51:03 UTC and was marked done 00:54:12 (3 min 9 s);
   no finding mentions `get_available_affordance_objects`, `familiarity` or `audit_against_world_truth`, it spawned no job,
   and all three are still unreferenced. It was neither "keep, intentionally unwired" nor acted on: it was closed
   without an answer (verified from `docs/findings.jsonl` and `docs/job_queue.jsonl`, `spawned_jobs` empty).
3. **The 30 split 6 (a) / 5 (b) / 19 (c).** Six are unread instruments (three of them over logs that hold 500-2900 rows
   of real shadow data with no reader), five are planned features that never fired, nineteen are dead scaffolding.
4. **Of the other 33 leads, 6 are real calls that UDMS missed** (calls through a module alias attribute), 1 is read by
   `scripts/du_pulse.py`, 2 are test-only, 11 are string-only (mostly state-dict keys or log messages), 13 have no code
   reference at all. So the hygiene tool's "dead" count over-states by roughly a fifth on that half, and one of the 13
   (`arousal.regime_shadow_status`) is a bigger write-only instrument than any in the 30.

## 2. What the instruments would already say (read-only look at live `data/`, 2026-11-05 snapshot)

These are the readings nobody can take today because the reader function has no caller. Computed with the same logic as
the dead functions, by hand, against the live files (not through the functions).

| Reader (dead) | Log it reads | Rows | What it would say |
|---|---|---|---|
| `emotion_construction.affective_retrieval_status` | `data/emotion_construction_affective_retrieval_shadow.jsonl` (405 KB) | 1649 | 1648 paired rows, mean top-5 Jaccard LLM-vs-constructed **0.979**, mean affect-match gap **0.024**: the constructed emotion retrieves almost the same memories as the LLM one. The `emotion_rethink` plan's next step (J-2252 read) needs exactly this. |
| `nodes/subconscious_node.active_imagination_judge_status` | `data/active_imagination_judge_shadow.jsonl` (559 KB) | 2937 | 2607 judged, **1 says not genuine (0.04 %)**: the judge separates nothing. Already known from P-0104 (F-3855..F-3857, D-0537, J-3128/J-3129): J-3129's own text says the reader has no caller. |
| `symbol_tier2_wouldinject.wouldinject_report` | `data/symbol_readback_tier2_wouldinject.jsonl` (287 KB) | 514 | mirror 270, bridge 244; `verbatim_recurrence` true on **514 of 514** rows. A 100 % hit rate is suspicious (I infer the row may only be written on a hit; not checked). The plan (`symbol_evolution_readback_plan`) says "Phase-A would-inject log review still unread". |
| `arousal.regime_shadow_status` (second set, not in the 30) | `data/arousal_regime_shadow_state.json` | 36 resolved streaks | longest internal-only stretch **98 cycles / 601,763 s (about 7 days)**, mean 18.7 cycles per resolved streak. `core/schema.py:1287` says "DO NOT FLIP until core.arousal.regime_shadow_status()" is read: the flip gate has a reader nobody calls. |
| `self_implication.conv_status` | `data/self_implication_conv_shadow.jsonl` | 393 | 11 would-fire (2.8 %). The HUD already charts this log (`friction_self_evidence` monitor), so this one is partly read. |

## 3. The 30 confirmed-unreferenced functions

Verdict key: **(a)** unread status/report reader, wire or retire its claim; **(b)** planned feature never called, noted
unfired; **(c)** dead scaffolding, removal job. Line numbers are as of master `fe3f7bed`.

| # | Function | Verdict | Plan | Evidence (file:line) |
|---|---|---|---|---|
| 1 | `core/affordances.py:258 get_available_affordance_objects` | (c) | investigative_action_loop_plan | Written "for EpistemicAffordanceAdvisor to inspect" (plan line 115). The advisor imports only `within_reach_text` (`epistemic_affordance_advisor.py:68`), and its hint stage was closed for good by D-0326. Nothing can call it. J-0383 lead. |
| 2 | `core/competence.py:333 familiarity` | (c) | epistemics (archived) | Derived `n/(n+10)`. Its only designed consumer is Phase D "principled explorer" in `docs/archive/epistemics_plan.md:183`, an archived plan that was never built. J-0383 lead. |
| 3 | `core/drowsy.py:74 in_zone` | (c) | drowsiness_phase | `observe()` (`drowsy.py:106`) re-implements the same `floor < e <= thr` test inline (`elif e > floor`). The predicate was never used, not even by `scripts/test_drowsy_shadow.py`. |
| 4 | `core/emotion_construction.py:534 affective_retrieval_status` | (a) | emotion_rethink | Sibling of `status()`, which the HUD calls via `_EVIDENCE_MODULES` (`hud/server.py:33`); the sibling is not in that call path or in `du_pulse`. See section 2. |
| 5 | `core/epistemic_affordance_advisor.py:416 calculate_internal_epistemic_metrics` | (c) | investigative_action_loop_plan | "Du-facing" entropy-reduction metric for the hint stage that D-0326 permanently closed. Module header (J-1776) says the module is the passive Stage-A instrument only. |
| 6 | `core/epistemic_affordance_advisor.py:452 audit_against_world_truth` | (c) | investigative_action_loop_plan | Self-described "researcher-only audit, NEVER called by Du's pathway"; a two-way substring match. No script uses it either. If a real audit is wanted it belongs in a lab script. J-0383 lead. |
| 7 | `core/goal_model.py:62 drift_warning` | (b) | curiosity_goals_dreams (Item 5) | Item 5 option (b) would inject it into idle Reflection/Critic; the plan lists option (a), leave it as-is and document that `concerns.py` is the idle governor, as the cheapest. A 2026-06-22 systems check (`docs/archive/systems_check_2026-06-22.md:240`, C25) already listed it as 0-caller "delete" and nothing acted. Founder call (decision filed). |
| 8 | `core/guidance_learning.py:1065 contradiction_status` | (b) | guidance_learning | Reader for the contradiction scan, which is off: `CONTRADICTION_SCAN_ENABLED = False` (`guidance_learning.py:898`, reason in F-0457). Unfired with its feature; do nothing until the flag is ruled. |
| 9 | `core/journal.py:190 _last_journal_ts` | (c) | journal_consolidation_pyramid | Superseded: `journal.py:198-203` says the shared JOURNAL_*.md mtime is polluted by observations and the day-recap has its own clock (`_last_day_recap_ts`, used at `journal.py:252`). |
| 10 | `core/life.py:1367 _korora_presence` | (c) | shore_upgrade / living world | Superseded: korora is a full row in `core/life_birds.py:395` with its own ashore curve (`KORORA_ASHORE`, line 37). The sibling adapters `_seal_presence` / `_glowworm_presence` / `_moth_presence` are all registered; this one never was. |
| 11 | `core/orchestrator.py:128 _embed_emotion_output` | (c) | emotion_vec_thread (completed) | Superseded: new fragments take `emotion_embedding=_mood.current_vec()` (`composition.py:367`, `essay_lesson.py:1336`). Hub file: run `udms_get_change_dossier` before editing. |
| 12 | `core/peer_metrics.py:130 lexicon_from_text` | (b) | peer_correspondence_plan (section 12, R8) | The "his lexicon vs a peer's letters" contagion comparison was designed for Darwin and never built; `compare()` (`peer_metrics.py:148`) only diffs against his own baseline. The peers are live, so the metric is possible. |
| 13 | `core/peer_model.py:224 all_models` | (c) | social_world_school | One-line accessor over `_load_all()`; every real caller uses `get(persona)` (`peer_model.py:219`). |
| 14 | `core/self_implication.py:266 conv_status` | (a) | friction_and_self_evidence_plan | Selectivity summary of the conv shadow log. The HUD charts the same log; the would-fire / retreat shares are unread. See section 2. |
| 15 | `core/sitting.py:117 active_text` | (c) | friction_and_self_evidence_plan | Trivial accessor; `is_dwelling()` / `dwell_steer()` are the live reads. |
| 16 | `core/sound_knowledge.py:596 heard_today` | (a) low | real_hearing / sound world | `docs/reports/sound_world_system_examination.md:107` asks someone to "eyeball heard_today() numbers"; no one can without a REPL. `du_pulse.py:312` already reads the sound ledger, but not per-voice day counts. |
| 17 | `core/source_model.py:138 source_of_event` | (b) | epistemics_phase_c | Translator tables `_EVENT_SOURCE_TO_SOURCE` / `_COMPETENCE_SOURCE_TO_VERIFICATION` (`source_model.py:79,87`) are read only by these two functions. They were the bridge from shadow events and competence sources into the provenance ledger; the bridge was never crossed. |
| 18 | `core/source_model.py:143 verification_of_competence_source` | (b) | epistemics_phase_c | Same bridge. J-3107 saw the same thing from the other side ("no code reads source tier3_model"). D-0532 keeps the Tier-3 probe running in shadow, so this is a plan-live feature that never fired, not scaffolding. |
| 19 | `core/store_persist.py:457 append_patterns_delta` | (c) | data_store_hygiene | Wrapper. The one real writer calls `append_patterns_delta_lines` directly (`subconscious_node.py:3808`). |
| 20 | `core/symbol_tier2_wouldinject.py:188 wouldinject_report` | (a) | symbol_evolution_readback_plan | Reader over the Tier-2 would-inject log; plan says the log review is unread. See section 2. |
| 21 | `core/telemetry.py:271 latency_status` | (c) | (HUD) | Superseded: the HUD already has the `llm_latency` monitor on the same log (`hud/server.py` MONITOR_REGISTRY, "per-call latency (s)"). The function is the older, unwired version of that card. |
| 22 | `core/world_knowledge.py:381 get_species_diagnostics` | (c) | world_epistemic_substrate_plan (completed) | **The whole module is dead**, not just these three: nothing imports `core.world_knowledge` (`query_diagnostic_knowledge`, line 320, is called only by this function), and `observables_census.py` already dropped it (J-0832). |
| 23 | `core/world_knowledge.py:423 assess_exposure_duration` | (c) | same | Same module. |
| 24 | `core/world_knowledge.py:458 get_discriminative_actions` | (c) | same | Same module. It also suggests which action would settle a question, which is a hint to Du; the no-hints law (2026-08-14) means it must never be wired as written. |
| 25 | `core/world_objects.py:341 positions_status` | (a) low | world_store_write_fence / generative_world_sedimentation | "For the HUD/register": placed/gone/by-location counts of `world_objects.json`. No HUD card or pulse line reads it. Optional pulse line, or drop. |
| 26 | `core/world_substrate.py:387 get_physical_state` | (c) | world_epistemic_substrate_plan (completed) | Its docstring says "Layer 2 access for observation.py", but `core/observation.py` never references `world_substrate` (grep), and nothing else calls the accessor. |
| 27 | `core/world_substrate.py:421 apply_environmental_event` | (c) | same | The whole event chain is dead with it: `create_causal_event` (line 300) and `SubstrateObject.apply_causal_event` (line 184) have no other caller. The live world changes objects through `world_objects.process_storm_surge` / `move_tick`. |
| 28 | `core/world_substrate.py:776 measure_epistemic_distance` | (c) | same | "For evaluation ONLY (never exposed to Du)", with no evaluator ever written; `epistemic_distance` (line 216) is reachable only through it. |
| 29 | `core/world_traces.py:101 get_trace` | (c) | generative_world_sedimentation | Trivial accessor; `create_trace` (cat.py:1946,1962) and `get_active_traces` (fieldcraft.py:487) are the live pair. |
| 30 | `nodes/subconscious_node.py:3925 active_imagination_judge_status` | (a) | decoupled_judge_pattern | Its own docstring: "Not yet wired into du_pulse.py ... available for a future pass". D-0537 ruled repair-in-shadow (J-3128, open), which changes the log shape, so wire the reader with that job, not before. |

Counts: (a) 6 (#4, 14, 16, 20, 25, 30), (b) 5 (#7, 8, 12, 17, 18), (c) 19 (#1, 2, 3, 5, 6, 9, 10, 11, 13, 15, 19, 21-24, 26-29).
By suffix I count 6 `_status`, 1 `_report`, 1 `_metrics` readers; F-4098's "eleven" counted a looser set. The write-only shape
is real but it is **four live-data readers (4, 14, 20, 30), not eleven**: the other "status" names are superseded (21),
disabled-feature (8) or trivial (25).

## 4. The other 33 leads: real calls or doc/worktree noise?

Scan verdicts from `scan_results_2026-11-07.json` (token stream; `.claude` worktree copies excluded, so none of these is a
worktree artefact in the verdicts below).

**Real calls UDMS missed (6): not dead.** All go through a module-alias attribute, which is why the graph lost them.
`coupling_rides.publish_witness` (`core/lane2.py:3335`), `lane2_break_habituation.observe_wonder` (`lane2.py:3379`),
`lane2_break_habituation.phase1_metric_sheet` (`lane2.py:4300`), `memory/store.read_count_importance_shadow`
(`inner_monologue_node.py:1951`), `reading.advance_from_finished` (`inner_monologue_node.py:5486`),
`study.misplaced_title` (`sensorium.py:3692`). Plus `memory_levels.drift_status`, read by `scripts/du_pulse.py:255,1734` (a wired
reader; the graph does not count scripts).

**Test-only (2):** `world_substrate.get_world_truth` (`scripts/test_object_epistemic_phase2.py:207`);
`deliberation._hot_ground_why` (its call was removed by J-3182; `_test_J3182_no_hot_fallback.py:122` asserts the call is
gone and `scripts/station_suite.py:91` keeps a label string, so the def is a leftover).

**No code reference at all (13), comments or docstrings only:**
`arousal.regime_shadow_status` (**a unread gate reader, see below**), `climate_engine._ready_to_ignite` (one-line wrapper,
`tick()` calls `_pending_trigger` directly), `composition.pick_task`, `curator.shadow_curate` (retired, self-documented at
`orchestrator.py:1666`), `guidance_learning.relevant_belief` (wrapper over `relevant_belief_with_id`, which is what
`orchestrator.py:1009` calls), `homeostasis.suggest_setpoints` (one-shot calibrator, adopted 2026-07-06), `inventory.make_item`,
`library_hand.shelve_only`, `sensorium.world_act`, `sensorium.garden_act` (both RETIRED D-0098, 2026-08-30, "kept for archaeology"),
`soundscape.object_sound`, `study_life._item_named`, `unified_inference.modulation`.

**String-only (11):** the bare name appears only as a short string and no code calls it:
`epistemic_advisory_hint` (the retired hint stage; tests assert it stays absent), `frontier.open_questions` (a payload dict key in
`common_ground_shadow.py:229`), `inventory.present_at` (dict key, `world_manifest.py:76`), `induction_drill.arun_item`,
`memory/store.is_hidden`, `memory_edges.edge_aware_neighbors_multihop`, `memory_levels.phase2_status`, `memory_levels.uncold_all`
(these four appear only in `logger.debug` failure messages; `phase2_status` and `uncold_all` are documented manual gate-probe and
repair tools, see `docs/memory_levels_plan.md`), `sensorium.woodpile` (state-dict key "woodpile"; the `woodpile()` function is never called),
`study_life.book_place` (state-dict key), `sleep_offloop._child_state_probe` (string-dispatched through `off_process(...)`, test-only).

**The one that matters: `core/arousal.py:237 regime_shadow_status` (a).** It is the reader for the D-0274 regime-gate staleness
shadow. `core/schema.py:1287` ("DO NOT FLIP until core.arousal.regime_shadow_status() ...") and `emotion_rethink.md:59`
both name it as the gate to read before the regime flag is flipped, and nothing calls it. The state it reads shows a 7-day
internal-only stretch (section 2), which is exactly the staleness case the gate was built to catch.

## 5. What this does not establish

- Zero references means no static caller. A `getattr` with a computed name, a `__import__` string, or a call from a process
  outside this tree would not show; I looked for string dispatch (the STRING_ONLY class) and found none that dispatches one of the 30.
- "Dead" is not "wrong to keep": the (c) list is cleanup, not a defect list. Nothing here has caused a failure.
- Row counts and rates in section 2 are from the live files as of the 2026-11-05 19:00 snapshot, read read-only.
- The T2 "514 of 514" figure is inferred to be a write-on-hit artefact; I did not read the writer to confirm.
- I did not run the 33 through a second tool; the token scan is the only evidence for them.

## 6. Follow-up work filed (J-3469, finding F-4344)

- **J-3741** (build): wire `affective_retrieval_status`, `wouldinject_report`, `arousal.regime_shadow_status`, `conv_status` into
  `scripts/du_pulse.py` (optional: `heard_today`, `positions_status`). `active_imagination_judge_status` is left to J-3128 (D-0537), whose
  log change it depends on.
- **J-3726..J-3739** (one hygiene job per module, 14 modules): affordances, competence, drowsy, epistemic_affordance_advisor,
  journal, life, orchestrator (hub, dossier first), peer_model, sitting, store_persist, telemetry, world_knowledge (whole module),
  world_substrate (functions plus the event chain), world_traces.
- **J-3740** (hygiene, second set): nine uncalled functions from the other 33 leads, with the explicit keep-list (functions
  documented as kept on purpose are not to be removed).
- **D-0700** (founder, plan `curiosity_goals_dreams`): wire or retire the five planned-but-never-fired features (#7, 8, 12, 17, 18).
- Unfired / unread-instrument notes added with `plan_state.py note` to `curiosity_goals_dreams`, `peer_correspondence_plan`,
  `epistemics_phase_c`, `guidance_learning`, `emotion_rethink`, `symbol_evolution_readback_plan`, `decoupled_judge_pattern`.
