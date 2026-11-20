# Appendix A, re-joined per git commit (J-2977, F-3670)

Generated 2026-11-07 by `scripts/rejoin_appendix_a_j2977.py` from `data/llm_latency.jsonl` (read-only), `data/nascence.log` (process starts) and the git history of the code. The old inventory (`docs/reviews/du_prompt_inventory_2026-10-31.md`, Appendix A) is untouched.

## 1. What was wrong, and how this table is built

A telemetry label is `module:line(Class)`: the line number in the file **at the time of the call**. Appendix A looked every label up in the file as it stood on 2026-10-31, so any label written before an edit that shifted the file landed inside whatever function now sits on that line (T2 was credited with Active Imagination's calls; F-3670). This table looks each label up in the version of the file that **was running**.

Which version was running. Du reads its code once, at process start. So the version is the newest mainline commit of that file at or before the last `Nascence is awake` line in `data/nascence.log` (300 starts found), not the newest commit before the row's timestamp. Per row the script tries, in order: B (commit at the last process start), A (commit at the row's own timestamp, the brief's method), C (a commit made while that process was running, for an edit that was live at start and only committed later); the first in which the label's line is the start of a plausible call (an `ast.Call` named like call/ask/judge/generate, or an `await`) wins.

- Resolution of the 101,880 labelled rows read (30 days before the later anchor): B 101,800, A 4, C 2, no valid call line in any candidate 4 (kept as B, unvalidated), no file to look up 70 (`asyncio.events`, `__main__`).
- Validation of the predicate (`--calibrate`, labels of the last 12 h of data): 3223/3225 = 99.9% under B against 2670/3225 = 82.8% under A. That gap is the evidence that the running version is the right one to join to: the newest commit before the row is wrong for about one row in six, because commits land after the restart that loaded the older code.
- Control: the OLD method (labels joined to the file as of the anchor) recomputed here reproduces 107 of 108 of the old table's rows exactly, so the pipeline reads the same data the inventory did. Anchor = 2026-10-31 23:00 local, found by search (it reproduces `core.deliberation:187` = 13602 / 1669 / 491 exactly).
- Function names are the names in the version that ran. A function renamed later appears under its old name and is marked `†` (not in the current file); its calls are real, they belong to the renamed function.
- Not re-joined: the three raw-HTTP rows (`judge_panel`, `left_lane`, `lane2`). Their label has no line number, so nothing drifts, and `data/llm_calls.jsonl` now holds only 2026-11-05, so the 10-31 window cannot be recomputed; they are carried from the old table at the bottom of section 2.

## 2. Corrected Appendix A (windows end 2026-10-31 23:00, the inventory's own anchor)

`old` = the inventory's figure for the same function name (0 = row absent). `Δ30d` = rejoined against old. `now` = the same rejoin with windows ending at the last telemetry row (2026-11-05 19:10, when Du was stopped). `†` = name not in the current file.

| 30d | 7d | 24h | old 30d | Δ30d | now 30d / 7d / 24h | module:function(class) | models@port (30d) | raw labels (30d) |
|---|---|---|---|---|---|---|---|---|
| 20622 | 2610 | 763 | 21020 | -2% | 26462 / 9438 / 1613 | nodes.inner_monologue_node:InnerMonologueNode._think(InnerMonologueNode) | qwen3.5:9b@11433 20622 | nodes.inner_monologue_node:3504(InnerMonologueNode), nodes.inner_monologue_node:3538(InnerMonologueNode), nodes.inner_monologue_node:3586(InnerMonologueNode) (+13) |
| 13602 | 1669 | 491 | 13602 | +0% | 17376 / 6066 / 1020 | core.deliberation:deliberate | qwen3.5:9b@11433 13602 | core.deliberation:187 |
| 9681 | 1134 | 365 | 365 | +2552% | 12470 / 4434 / 743 | core.commitment_ledger:_scan_shadow_locked | qwen3.5:9b@11433 9681 | core.commitment_ledger:459, core.commitment_ledger:487, core.commitment_ledger:511 |
| 9681 | 1134 | 365 | 9681 | +0% | 12470 / 4434 / 743 | core.self_implication:scan_shadow | qwen3.5:9b@11433 9681 | core.self_implication:89 |
| 1118 | 620 | 200 | 1118 | +0% | 2726 / 2228 / 358 | core.condensed_thought:shadow_tick | qwen3.5:9b@11433 1118 | core.condensed_thought:157 |
| 872 | 416 | 7 | 872 | +0% | 1110 / 747 / 31 | core.deliberation:_hot_ground_why | qwen3.5:9b@11433 872 | core.deliberation:146 |
| 289 | 289 | 93 | 93 | +211% | 1160 / 1148 / 185 | core.follow_line:_gen_json | command-r7b@11441 289 | core.follow_line:404, core.follow_line:489 |
| 2189 | 272 | 77 | 493 | +344% | 2788 / 1046 / 162 | nodes.subconscious_node:SubconsciousNode._active_imagination(SubconsciousNode) | command-r7b@11441 2083, qwen3.5:9b@11433 106 | nodes.subconscious_node:1342(SubconsciousNode), nodes.subconscious_node:1431(SubconsciousNode), nodes.subconscious_node:1538(SubconsciousNode) (+2) |
| 1091 | 122 | 29 | 1091 | +0% | 1254 / 424 / 79 | core.memory_levels:shadow_distill | command-r7b@11441 1036, qwen3.5:9b@11433 55 | core.memory_levels:694, core.memory_levels:706, core.memory_levels:724 (+1) |
| 690 | 122 | 36 | 546 | +26% | 940 / 494 / 56 | core.node_base:NodeBase.run_best_of.one(ReflectionNode) | qwen3.5:9b@11433 690 | core.node_base:130(ReflectionNode), core.node_base:141(ReflectionNode), core.node_base:144(ReflectionNode) |
| 537 | 117 | 51 | 537 | +0% | 660 / 375 / 24 | core.competence:CompetenceTracker.run_stability_loop(CompetenceTracker) | qwen3.5:9b@11433 537 | core.competence:764(CompetenceTracker), core.competence:781(CompetenceTracker) |
| 309 | 105 | 42 | 42 | +636% | 632 / 428 / 86 | core.reentry_p2:_default_primitives._revise | command-r7b@11441 303, qwen3.5:9b@11433 6 | core.reentry_p2:263, core.reentry_p2:330, core.reentry_p2:382 |
| 685 | 97 | 27 | 583 | +17% | 842 / 355 / 51 | core.node_base:NodeBase.run(CuriosityNode) | command-r7b@11441 628, qwen3.5:9b@11433 57 | core.node_base:74(CuriosityNode), core.node_base:84(CuriosityNode), core.node_base:85(CuriosityNode) |
| 652 | 96 | 0 | 80 | +715% | 870 / 322 / 48 | nodes.inner_monologue_node:InnerMonologueNode._author(InnerMonologueNode) | command-r7b@11441 627, qwen3.5:9b@11433 25 | nodes.inner_monologue_node:5653(InnerMonologueNode), nodes.inner_monologue_node:5676(InnerMonologueNode), nodes.inner_monologue_node:5707(InnerMonologueNode) (+9) |
| 938 | 90 | 32 | 938 | +0% | 1303 / 492 / 111 | core.librarian:subjects_for | falcon3:7b@11440 932, gemma4:12b@11439 6 | core.librarian:161 |
| 226 | 79 | 24 | 24 | +842% | 438 / 285 / 53 | nodes.inner_monologue_node:InnerMonologueNode._enter_sleep._nm_generate(InnerMonologueNode) | qwen3.5:9b@11433 226 | nodes.inner_monologue_node:1273(InnerMonologueNode), nodes.inner_monologue_node:1302(InnerMonologueNode), nodes.inner_monologue_node:1306(InnerMonologueNode) (+1) |
| 693 | 75 | 20 | 693 | +0% | 810 / 265 / 50 | core.memory_levels:drift_shadow | command-r7b@11441 660, qwen3.5:9b@11433 33 | core.memory_levels:888, core.memory_levels:925, core.memory_levels:927 |
| 660 | 65 | 20 | 660 | +0% | 790 / 255 / 50 | core.curiosity_worth:grade | granite3.1-moe:3b@11437 660 | core.curiosity_worth:62 |
| 755 | 64 | 6 | 755 | +0% | 955 / 315 / 72 | core.study_note:compose_note | qwen3.5:9b@11433 755 | core.study_note:220 |
| 542 | 64 | 36 | 36 | +1406% | 667 / 204 / 32 | core.commitment_ledger:_judge_defeater | mixtral:8x7b@11438 542 | core.commitment_ledger:395, core.commitment_ledger:423, core.commitment_ledger:447 |
| 345 | 61 | 18 | 283 | +22% | 470 / 247 / 28 | core.node_base:NodeBase.run(CriticNode) | qwen3.5:9b@11433 345 | core.node_base:74(CriticNode), core.node_base:84(CriticNode), core.node_base:85(CriticNode) |
| 513 | 59 | 12 | 172 | +198% | 600 / 198 / 34 | nodes.dream_node:DreamNode._gen_episode(DreamNode) | mixtral:8x7b@11438 489, yi:34b-v1.5@11442 24 | nodes.dream_node:435(DreamNode), nodes.dream_node:444(DreamNode), nodes.dream_node:460(DreamNode) (+3) |
| 340 | 59 | 18 | 279 | +22% | 464 / 243 / 27 | core.node_base:NodeBase.run(EmotionNode) | qwen3.5:9b@11433 340 | core.node_base:74(EmotionNode), core.node_base:84(EmotionNode), core.node_base:85(EmotionNode) |
| 340 | 59 | 18 | 279 | +22% | 464 / 243 / 27 | core.node_base:NodeBase.run(ExecutiveNode) | qwen3.5:9b@11433 340 | core.node_base:74(ExecutiveNode), core.node_base:84(ExecutiveNode), core.node_base:85(ExecutiveNode) |
| 340 | 59 | 18 | 279 | +22% | 464 / 243 / 27 | core.node_base:NodeBase.run(MemoryRouterNode) | qwen3.5:9b@11433 340 | core.node_base:74(MemoryRouterNode), core.node_base:84(MemoryRouterNode), core.node_base:85(MemoryRouterNode) |
| 340 | 59 | 18 | 279 | +22% | 464 / 243 / 27 | core.node_base:NodeBase.run(PerceptionNode) | qwen3.5:9b@11433 340 | core.node_base:74(PerceptionNode), core.node_base:84(PerceptionNode), core.node_base:85(PerceptionNode) |
| 340 | 59 | 18 | 279 | +22% | 464 / 243 / 27 | core.node_base:NodeBase.run(SalienceNode) | qwen3.5:9b@11433 340 | core.node_base:74(SalienceNode), core.node_base:84(SalienceNode), core.node_base:85(SalienceNode) |
| 340 | 59 | 18 | 279 | +22% | 464 / 243 / 27 | core.node_base:NodeBase.run(VoiceNode) | qwen3.5:9b@11433 340 | core.node_base:74(VoiceNode), core.node_base:84(VoiceNode), core.node_base:85(VoiceNode) |
| 335 | 59 | 18 | 274 | +22% | 438 / 222 / 27 | core.node_base:NodeBase.run(EpisodicBufferNode) | qwen3.5:9b@11433 335 | core.node_base:74(EpisodicBufferNode), core.node_base:84(EpisodicBufferNode), core.node_base:85(EpisodicBufferNode) |
| 335 | 59 | 18 | 274 | +22% | 438 / 222 / 27 | core.node_base:NodeBase.run(RecallNode) | qwen3.5:9b@11433 335 | core.node_base:74(RecallNode), core.node_base:84(RecallNode), core.node_base:85(RecallNode) |
| 451 | 55 | 15 | 99 | +356% | 560 / 215 / 36 | nodes.subconscious_node:SubconsciousNode._self_relate_check(SubconsciousNode) | command-r7b@11441 420, qwen3.5:9b@11433 31 | nodes.subconscious_node:438(SubconsciousNode), nodes.subconscious_node:516(SubconsciousNode), nodes.subconscious_node:620(SubconsciousNode) (+2) |
| 565 | 51 | 6 | 565 | +0% | 676 / 213 / 42 | core.symbolic_reading:read_symbolically | command-r7b@11441 544, qwen3.5:9b@11433 21 | core.symbolic_reading:50 |
| 311 | 49 | 14 | 311 | +0% | 345 / 123 / 17 | core.sitting:judge_dwell_release | command-r7b@11441 311 | core.sitting:210, core.sitting:220, core.sitting:232 |
| 175 | 48 | 8 | 1753 | -90% | 231 / 124 / 14 | nodes.subconscious_node:SubconsciousNode._t2_synthesise(SubconsciousNode) | command-r7b@11441 157, qwen3.5:9b@11433 18 | nodes.subconscious_node:1132(SubconsciousNode), nodes.subconscious_node:1165(SubconsciousNode), nodes.subconscious_node:1221(SubconsciousNode) (+4) |
| 190 | 46 | 22 | 247 | -23% | 271 / 144 / 20 | nodes.subconscious_node:SubconsciousNode._t4_deliberate(SubconsciousNode) | qwen3.5:9b@11433 190 | nodes.subconscious_node:2190(SubconsciousNode), nodes.subconscious_node:2237(SubconsciousNode), nodes.subconscious_node:2279(SubconsciousNode) (+5) |
| 296 | 44 | 17 | 296 | +0% | 422 / 200 / 39 | core.self_interrogation:interrogate | qwen3.5:9b@11433 296 | core.self_interrogation:169, core.self_interrogation:170 |
| 234 | 39 | 9 | 71 | +230% | 270 / 118 / 14 | nodes.subconscious_node:SubconsciousNode._synthesise_theme(SubconsciousNode) | command-r7b@11441 213, qwen3.5:9b@11433 21 | nodes.subconscious_node:2919(SubconsciousNode), nodes.subconscious_node:3008(SubconsciousNode), nodes.subconscious_node:3015(SubconsciousNode) (+4) |
| 529 | 38 | 15 | 529 | +0% | 583 / 148 / 11 | core.narrative_quality:score_llm | qwen3.5:9b@11433 494, command-r7b@11441 35 | core.narrative_quality:160 |
| 249 | 24 | 0 | 0 | new | 350 / 125 / 37 | nodes.inner_monologue_node:InnerMonologueNode._solve_attempt(InnerMonologueNode) | qwen3.5:9b@11433 249 | nodes.inner_monologue_node:1739(InnerMonologueNode), nodes.inner_monologue_node:1743(InnerMonologueNode), nodes.inner_monologue_node:1782(InnerMonologueNode) (+2) |
| 118 | 23 | 5 | 95 | +24% | 157 / 85 / 8 | core.node_base:NodeBase.run(ConsolidationNode) | command-r7b@11441 103, qwen3.5:9b@11433 15 | core.node_base:74(ConsolidationNode), core.node_base:84(ConsolidationNode), core.node_base:85(ConsolidationNode) |
| 93 | 22 | 11 | 93 | +0% | 127 / 76 / 9 | core.symbol_evolution:SymbolEvolutionEngine.write_tablet(SymbolEvolutionEngine) | command-r7b@11441 84, qwen3.5:9b@11433 9 | core.symbol_evolution:176(SymbolEvolutionEngine) |
| 18 | 16 | 2 | 18 | +0% | 54 / 50 / 8 | asyncio.events:?(Handle) | mixtral:8x7b@11438 18 | asyncio.events:94(Handle) |
| 137 | 14 | 3 | 137 | +0% | 161 / 53 / 10 | core.grounded_learning:consolidate | command-r7b@11441 131, qwen3.5:9b@11433 6 | core.grounded_learning:87 |
| 39 | 14 | 3 | 38 | +3% | 31 / 18 / 1 | core.chapters:try_form_chapter | command-r7b@11441 35, qwen3.5:9b@11433 4 | core.chapters:318, core.chapters:370 |
| 131 | 12 | 3 | 131 | +0% | 153 / 49 / 8 | core.curiosity_queue:transform_and_seed | command-r7b@11441 124, qwen3.5:9b@11433 7 | core.curiosity_queue:148, core.curiosity_queue:150, core.curiosity_queue:162 |
| 29 | 11 | 0 | 29 | +0% | 52 / 32 / 5 | core.refinery:refine | command-r7b@11441 27, qwen3.5:9b@11433 2 | core.refinery:180, core.refinery:194 |
| 162 | 9 | 1 | 162 | +0% | 187 / 42 / 8 | core.journal:write_observation | qwen3.5:9b@11433 162 | core.journal:259 |
| 78 | 8 | 0 | 0 | new | 82 / 50 / 2 | core.orchestrator:Orchestrator._reentry_shadow._revise | command-r7b@11441 56, qwen3.5:9b@11433 22 | core.orchestrator:2733, core.orchestrator:2777, core.orchestrator:2792 (+3) |
| 146 | 7 | 0 | 146 | +0% | 162 / 23 / 4 | core.essay_lesson:compose | command-r7b@11441 125, qwen3.5:9b@11433 21 | core.essay_lesson:445, core.essay_lesson:470 |
| 105 | 7 | 0 | 105 | +0% | 129 / 31 / 5 | core.essay_lesson:_reduce_notes | command-r7b@11441 85, qwen3.5:9b@11433 20 | core.essay_lesson:412 |
| 35 | 5 | 2 | 35 | +0% | 42 / 16 / 2 | core.peers:compose_letter | yi:34b-v1.5@11442 21, falcon3:7b@11440 7, gemma4:12b@11439 7 | core.peers:542, core.peers:551, core.peers:556 (+1) |
| 19 | 3 | 1 | 19 | +0% | 21 / 8 / 2 | core.journal:write_entry | qwen3.5:9b@11433 19 | core.journal:217 |
| 8 | 3 | 0 | 13 | -38% | 9 / 5 / 1 | nodes.subconscious_node:SubconsciousNode._t5_compile(SubconsciousNode) | command-r7b@11441 7, qwen3.5:9b@11433 1 | nodes.subconscious_node:2716(SubconsciousNode), nodes.subconscious_node:2812(SubconsciousNode), nodes.subconscious_node:2942(SubconsciousNode) |
| 15 | 2 | 0 | 15 | +0% | 21 / 8 / 2 | core.composition:run | qwen3.5:9b@11433 15 | core.composition:55 |
| 24 | 1 | 0 | 24 | +0% | 28 / 5 / 1 | core.essay_lesson:self_predict | command-r7b@11441 19, qwen3.5:9b@11433 5 | core.essay_lesson:518 |
| 8 | 1 | 0 | 8 | +0% | 11 / 4 / 1 | core.nature_study:run | qwen3.5:9b@11433 8 | core.nature_study:55 |
| 7 | 1 | 0 | 7 | +0% | 7 / 2 / 0 | core.journal_rollup:_author | qwen3.5:9b@11433 7 | core.journal_rollup:138 |
| 4 | 1 | 0 | 4 | +0% | 4 / 1 / 1 | core.self_mirror:hold_up_mirror | qwen3.5:9b@11433 4 | core.self_mirror:104 |
| 192 | 0 | 0 | 27 | +611% | 201 / 26 / 0 | nodes.subconscious_node:SubconsciousNode._t4_legacy_author(SubconsciousNode) | qwen3.5:9b@11433 192 | nodes.subconscious_node:2492(SubconsciousNode), nodes.subconscious_node:2599(SubconsciousNode), nodes.subconscious_node:2611(SubconsciousNode) (+1) |
| 120 | 0 | 0 | 120 | +0% | 120 / 0 / 0 | si_open_doubt_cup_replay_v2:gen_stage | qwen3.5:9b@11433 120 | si_open_doubt_cup_replay_v2:175 |
| 28 | 0 | 0 | 28 | +0% | 51 / 27 / 1 | core.self_implication:scan_conversation_shadow | qwen3.5:9b@11433 28 | core.self_implication:195 |
| 15 | 0 | 0 | 15 | +0% | 40 / 25 / 0 | core.decomposed_critic:evaluate | gemma4:12b@11439 15 | core.decomposed_critic:184 |
| 15 | 0 | 0 | 15 | +0% | 40 / 25 / 0 | core.guidance_learning:capture_shadow | qwen3.5:9b@11433 15 | core.guidance_learning:89 |
| 14 | 0 | 0 | 14 | +0% | 11 / 2 / 1 | __main__:? | command-r7b@11441 13, qwen3.5:9b@11433 1 | __main__:859, __main__:867, __main__:963 (+3) |
| 10 | 0 | 0 | 10 | +0% | 32 / 22 / 0 | core.guidance_learning:_classify | command-r7b@11441 10 | core.guidance_learning:485 |
| 8 | 0 | 0 | 8 | +0% | 8 / 0 / 0 | core.study_note:_revise | qwen3.5:9b@11433 8 | core.study_note:231 |
| 4 | 0 | 0 | 1 | +300% | 11 / 7 / 0 | core.guidance_learning:_self_clash | command-r7b@11441 4 | core.guidance_learning:743, core.guidance_learning:762 |
| 4 | 0 | 0 | 4 | +0% | 6 / 2 / 0 | core.peer_model:update_after_exchange | qwen3.5:9b@11433 4 | core.peer_model:142 |
| 1 | 0 | 0 | 1 | +0% | 2 / 1 / 0 | core.competence:CompetenceTracker.run_tier3_probe_loop(CompetenceTracker) | command-r7b@11441 1 | core.competence:874(CompetenceTracker) |
| 1 | 0 | 0 | 1 | +0% | 1 / 0 / 0 | core.peers:_stance_compliance_judge | mixtral:8x7b@11438 1 | core.peers:600 |

Carried unchanged from the old table (raw-HTTP, coarse label, ~1-day window):

| 30d | 7d | 24h | module:function(class) | models@port | raw labels seen |
|---|---|---|---|---|---|
| 2414 | 2414 | 2414 | judge_panel:(raw-http; only llm_calls.jsonl, ~1-day window) | 11438-judge@11438 1071, 11440-judge@11440 1071, 11437-judge@11437 224 |  |
| 865 | 865 | 865 | left_lane:(raw-http; only llm_calls.jsonl, ~1-day window) | mixtral:8x7b@11438 743, gemma4:12b@11439 122 |  |
| 183 | 183 | 183 | lane2:(raw-http; only llm_calls.jsonl, ~1-day window) | deepseek-r1:7b@11444 183 |  |

## 3. Rows whose 30d figure moved by more than 25 percent

A row counts as moved if |rejoined - old| / old > 25%, or it appears or disappears. A row that is only in the old table (rejoined 30d = 0) is a label the old join pinned to a function that never ran it.

| old 30d | rejoined 30d | Δ | 7d old -> new | function | where the calls moved (30d, labels re-attributed) |
|---|---|---|---|---|---|
| 365 | 9681 | +2552% | 365 -> 1134 | core.commitment_ledger:_scan_shadow_locked | gains 8965 from scan_shadow, 351 from ? |
| 8965 | 0 | -100% | 769 -> 0 | core.commitment_ledger:scan_shadow | loses 8965 to _scan_shadow_locked |
| 493 | 2189 | +344% | 272 -> 272 | nodes.subconscious_node:SubconsciousNode._active_imagination(SubconsciousNode) | gains 1696 from SubconsciousNode._t2_synthesise(SubconsciousNode) |
| 1753 | 175 | -90% | 48 -> 48 | nodes.subconscious_node:SubconsciousNode._t2_synthesise(SubconsciousNode) | gains 113 from SubconsciousNode._find_t2_trigger(SubconsciousNode), 4 from ?(SubconsciousNode); loses 1696 to SubconsciousNode._active_imagination(SubconsciousNode) |
| 846 | 0 | -100% | 28 -> 0 | core.commitment_ledger:? | loses 495 to _judge_defeater, 351 to _scan_shadow_locked |
| 80 | 652 | +715% | 80 -> 96 | nodes.inner_monologue_node:InnerMonologueNode._author(InnerMonologueNode) | gains 398 from InnerMonologueNode._think(InnerMonologueNode), 158 from InnerMonologueNode._route_act(InnerMonologueNode) |
| 36 | 542 | +1406% | 36 -> 64 | core.commitment_ledger:_judge_defeater | gains 495 from ?, 11 from _stakes |
| 403 | 0 | -100% | 55 -> 0 | nodes.inner_monologue_node:InnerMonologueNode._enter_sleep(InnerMonologueNode) | loses 202 to InnerMonologueNode._enter_sleep._nm_generate(InnerMonologueNode), 201 to InnerMonologueNode._solve_attempt(InnerMonologueNode) |
| 356 | 0 | -100% | 0 -> 0 | nodes.subconscious_node:?(SubconsciousNode) | loses 352 to SubconsciousNode._self_relate_check(SubconsciousNode), 4 to SubconsciousNode._t2_synthesise(SubconsciousNode) |
| 99 | 451 | +356% | 55 -> 55 | nodes.subconscious_node:SubconsciousNode._self_relate_check(SubconsciousNode) | gains 352 from ?(SubconsciousNode) |
| 341 | 0 | -100% | 0 -> 0 | nodes.dream_node:DreamNode.synthesise(DreamNode) | loses 341 to DreamNode._gen_episode(DreamNode) |
| 172 | 513 | +198% | 59 -> 59 | nodes.dream_node:DreamNode._gen_episode(DreamNode) | gains 341 from DreamNode.synthesise(DreamNode) |
| 267 | 0 | -100% | 63 -> 0 | core.reentry_p2:settle_shadow_p2 | loses 267 to _default_primitives._revise |
| 42 | 309 | +636% | 42 -> 105 | core.reentry_p2:_default_primitives._revise | gains 267 from settle_shadow_p2 |
| 0 | 249 | new | 0 -> 24 | nodes.inner_monologue_node:InnerMonologueNode._solve_attempt(InnerMonologueNode) | gains 201 from InnerMonologueNode._enter_sleep(InnerMonologueNode), 48 from InnerMonologueNode._redirect_patch(InnerMonologueNode) |
| 24 | 226 | +842% | 24 -> 79 | nodes.inner_monologue_node:InnerMonologueNode._enter_sleep._nm_generate(InnerMonologueNode) | gains 202 from InnerMonologueNode._enter_sleep(InnerMonologueNode) |
| 196 | 0 | -100% | 196 -> 0 | core.follow_line:grounds_unclear | loses 196 to _gen_json |
| 93 | 289 | +211% | 93 -> 289 | core.follow_line:_gen_json | gains 196 from grounds_unclear |
| 27 | 192 | +611% | 0 -> 0 | nodes.subconscious_node:SubconsciousNode._t4_legacy_author(SubconsciousNode) | gains 165 from SubconsciousNode._t4_deliberate(SubconsciousNode) |
| 71 | 234 | +230% | 39 -> 39 | nodes.subconscious_node:SubconsciousNode._synthesise_theme(SubconsciousNode) | gains 152 from SubconsciousNode._t6_theme_check(SubconsciousNode), 10 from SubconsciousNode._t5_compile(SubconsciousNode) |
| 158 | 0 | -100% | 0 -> 0 | nodes.inner_monologue_node:InnerMonologueNode._route_act(InnerMonologueNode) | loses 158 to InnerMonologueNode._author(InnerMonologueNode) |
| 152 | 0 | -100% | 0 -> 0 | nodes.subconscious_node:SubconsciousNode._t6_theme_check(SubconsciousNode) | loses 152 to SubconsciousNode._synthesise_theme(SubconsciousNode) |
| 546 | 690 | +26% | 122 -> 122 | core.node_base:NodeBase.run_best_of.one(ReflectionNode) | gains 124 from NodeBase._temperature(ReflectionNode), 20 from NodeBase.run_best_of(ReflectionNode) |
| 124 | 0 | -100% | 0 -> 0 | core.node_base:NodeBase._temperature(ReflectionNode) | loses 124 to NodeBase.run_best_of.one(ReflectionNode) |
| 113 | 0 | -100% | 0 -> 0 | nodes.subconscious_node:SubconsciousNode._find_t2_trigger(SubconsciousNode) | loses 113 to SubconsciousNode._t2_synthesise(SubconsciousNode) |
| 102 | 0 | -100% | 0 -> 0 | core.node_base:?(CuriosityNode) | loses 102 to NodeBase.run(CuriosityNode) |
| 0 | 78 | new | 0 -> 8 | core.orchestrator:Orchestrator._reentry_shadow._revise | gains 36 from Orchestrator._pre_affect_self_echo_ctx, 14 from Orchestrator._compute_attention |
| 62 | 0 | -100% | 0 -> 0 | core.node_base:?(CriticNode) | loses 62 to NodeBase.run(CriticNode) |
| 61 | 0 | -100% | 0 -> 0 | core.node_base:?(VoiceNode) | loses 61 to NodeBase.run(VoiceNode) |
| 61 | 0 | -100% | 0 -> 0 | core.node_base:?(SalienceNode) | loses 61 to NodeBase.run(SalienceNode) |
| 61 | 0 | -100% | 0 -> 0 | core.node_base:?(RecallNode) | loses 61 to NodeBase.run(RecallNode) |
| 61 | 0 | -100% | 0 -> 0 | core.node_base:?(PerceptionNode) | loses 61 to NodeBase.run(PerceptionNode) |
| 61 | 0 | -100% | 0 -> 0 | core.node_base:?(MemoryRouterNode) | loses 61 to NodeBase.run(MemoryRouterNode) |
| 61 | 0 | -100% | 0 -> 0 | core.node_base:?(ExecutiveNode) | loses 61 to NodeBase.run(ExecutiveNode) |
| 61 | 0 | -100% | 0 -> 0 | core.node_base:?(EpisodicBufferNode) | loses 61 to NodeBase.run(EpisodicBufferNode) |
| 61 | 0 | -100% | 0 -> 0 | core.node_base:?(EmotionNode) | loses 61 to NodeBase.run(EmotionNode) |
| 58 | 0 | -100% | 0 -> 0 | nodes.subconscious_node:SubconsciousNode._t4_distinct_tensions(SubconsciousNode) | loses 58 to SubconsciousNode._t4_deliberate(SubconsciousNode) |
| 48 | 0 | -100% | 24 -> 0 | nodes.inner_monologue_node:InnerMonologueNode._redirect_patch(InnerMonologueNode) | loses 48 to InnerMonologueNode._solve_attempt(InnerMonologueNode) |
| 38 | 0 | -100% | 0 -> 0 | nodes.subconscious_node:SubconsciousNode._t4_rests_active(SubconsciousNode) | loses 38 to SubconsciousNode._t4_deliberate(SubconsciousNode) |
| 36 | 0 | -100% | 0 -> 0 | core.orchestrator:Orchestrator._pre_affect_self_echo_ctx | loses 36 to Orchestrator._reentry_shadow._revise |
| 23 | 0 | -100% | 0 -> 0 | core.node_base:?(ConsolidationNode) | loses 23 to NodeBase.run(ConsolidationNode) |
| 20 | 0 | -100% | 0 -> 0 | core.node_base:NodeBase.run_best_of(ReflectionNode) | loses 20 to NodeBase.run_best_of.one(ReflectionNode) |
| 16 | 0 | -100% | 16 -> 0 | nodes.inner_monologue_node:InnerMonologueNode._observe_journal(InnerMonologueNode) | loses 16 to InnerMonologueNode._author(InnerMonologueNode) |
| 14 | 0 | -100% | 8 -> 0 | core.orchestrator:Orchestrator._compute_attention | loses 14 to Orchestrator._reentry_shadow._revise |
| 12 | 0 | -100% | 0 -> 0 | nodes.subconscious_node:SubconsciousNode._t4_self_authoring(SubconsciousNode) | loses 12 to SubconsciousNode._t4_deliberate(SubconsciousNode) |
| 12 | 0 | -100% | 0 -> 0 | core.orchestrator:Orchestrator._emotional_pre_retrieval | loses 12 to Orchestrator._reentry_shadow._revise |
| 11 | 0 | -100% | 0 -> 0 | core.commitment_ledger:_stakes | loses 11 to _judge_defeater |
| 10 | 0 | -100% | 0 -> 0 | core.orchestrator:Orchestrator._edge_trigger_shadow_hint | loses 10 to Orchestrator._reentry_shadow._revise |
| 6 | 0 | -100% | 0 -> 0 | core.orchestrator:Orchestrator._log_pre_affect_self_echo | loses 6 to Orchestrator._reentry_shadow._revise |
| 13 | 8 | -38% | 3 -> 3 | nodes.subconscious_node:SubconsciousNode._t5_compile(SubconsciousNode) | gains 4 from SubconsciousNode._log_t4(SubconsciousNode), 1 from SubconsciousNode._apply_self_authoring(SubconsciousNode); loses 10 to SubconsciousNode._synthesise_theme(SubconsciousNode) |
| 4 | 0 | -100% | 0 -> 0 | nodes.subconscious_node:SubconsciousNode._log_t4(SubconsciousNode) | loses 4 to SubconsciousNode._t5_compile(SubconsciousNode) |
| 1 | 4 | +300% | 0 -> 0 | core.guidance_learning:_self_clash | gains 3 from _log_contradiction |
| 3 | 0 | -100% | 0 -> 0 | core.guidance_learning:_log_contradiction | loses 3 to _self_clash |
| 1 | 0 | -100% | 0 -> 0 | nodes.subconscious_node:SubconsciousNode._update_emotional_signature(SubconsciousNode) | loses 1 to SubconsciousNode._t2_synthesise(SubconsciousNode) |
| 1 | 0 | -100% | 0 -> 0 | nodes.subconscious_node:SubconsciousNode._cluster_epochs(SubconsciousNode) | loses 1 to SubconsciousNode._synthesise_theme(SubconsciousNode) |
| 1 | 0 | -100% | 0 -> 0 | nodes.subconscious_node:SubconsciousNode._apply_self_authoring(SubconsciousNode) | loses 1 to SubconsciousNode._t5_compile(SubconsciousNode) |
| 1 | 0 | -100% | 0 -> 0 | core.chapters:_existing_chapter_vecs | loses 1 to try_form_chapter |

57 rows moved by more than 25 percent, of 110 distinct function keys.

## 4. Prompt-registry rows (`calls_7d`)

`prompt_registry.py` stores `calls_7d` per row but has no flag to set it (`set` takes `--note`, not a count), so the registry owner has to edit the field another way or add `--calls-7d` (follow-up job). Listed: every registry row whose covered function has a changed 7d, or a 30d that moved by more than 25 percent.

| row | stored calls_7d | Appendix A 7d (old -> rejoined) | 30d (old -> rejoined) | covered keys |
|---|---|---|---|---|
| P-0016 | 10 | 0 -> 8 | 0 -> 78 | Orchestrator._reentry_shadow._revise |
| P-0019 |  | 0 -> 0 | 1 -> 4 | _self_clash |
| P-0023 | 50 | 24 -> 79 | 24 -> 226 | InnerMonologueNode._enter_sleep._nm_generate(InnerMonologueNode) |
| P-0024 |  | 0 -> 24 | 0 -> 249 | InnerMonologueNode._solve_attempt(InnerMonologueNode) |
| P-0029 | 80 | 80 -> 96 | 80 -> 652 | InnerMonologueNode._author(InnerMonologueNode) |
| P-0037 | 48 | 36 -> 64 | 36 -> 542 | _judge_defeater |
| P-0038 | 597 | 365 -> 1134 | 365 -> 9681 | _scan_shadow_locked |
| P-0044 | 168 | 93 -> 289 | 93 -> 289 | _gen_json |
| P-0045 | 66 | 42 -> 105 | 42 -> 309 | _default_primitives._revise |
| P-0052 | 65 | 55 -> 55 | 99 -> 451 | SubconsciousNode._self_relate_check(SubconsciousNode) |
| P-0053 | 52 | 48 -> 48 | 1753 -> 175 | SubconsciousNode._t2_synthesise(SubconsciousNode) |
| P-0054 | 332 | 272 -> 272 | 493 -> 2189 | SubconsciousNode._active_imagination(SubconsciousNode) |
| P-0058 |  | 0 -> 0 | 27 -> 192 | SubconsciousNode._t4_legacy_author(SubconsciousNode) |
| P-0059 | 3 | 3 -> 3 | 13 -> 8 | SubconsciousNode._t5_compile(SubconsciousNode) |
| P-0060 | 51 | 39 -> 39 | 71 -> 234 | SubconsciousNode._synthesise_theme(SubconsciousNode) |
| P-0061 | 77 | 59 -> 59 | 172 -> 513 | DreamNode._gen_episode(DreamNode) |

Commands for the orchestrator, only for rows whose 7d column moved. `set --note` REPLACES the field, so each command repeats the row's current note and appends the correction:

```
prompt_registry.py set P-0016 --note "REENTRY_ADMIT=True confirmed; output reaches Du as broadcast seed 'you concluded'; gate is embedding math only; D-0106 defeater fired (collapse 31.6 pct since ruling, status() says do not promote); 20 calls in 7d by function (labels drift, 10 under current line). | Founder 2026-11-02 (D-0540): REENTRY_ADMIT off (back to Phase 0). | Appendix A re-join (J-2977): 7d at the 10-31 anchor is 8, not 0; stored calls_7d 10" --session J-2977
prompt_registry.py set P-0023 --note "Prompts live in core/night_mind.py; flag-gated per the reader. | Founder 2026-11-02 (D-0579): nouns-only avoid list, drop V2 example list. | J-2955 (F-3640): NOT shadow-only. NIGHT_MIND_ENABLED True since J-2065, NIGHT_DORMANT_ENABLED True since J-2410: every night thought is written as a dormant fragment and the last of each sleep seeds the first waking thought; module docstring corrected. | Appendix A re-join (J-2977): 7d at the 10-31 anchor is 79, not 24; stored calls_7d 50" --session J-2977
prompt_registry.py set P-0024 --note "Three caller prompt variants; not seen in telemetry. | Founder 2026-11-02 (D-0582): extend the maths ladder; (D-0583): the method hint is the Travis branch, keep. Recorded in code and docs by J-3197: comments above method_hint in core/math_drill.py and core/music_drill.py, and an exception line in docs/guidelines/prompt_registry.md section 4 item 8. Hint text must stay Travis-authored, never model-generated. | Appendix A re-join (J-2977): 7d at the 10-31 anchor is 24, not 0; stored calls_7d None" --session J-2977
prompt_registry.py set P-0029 --note "One chain of three stage prompts. Real 7d calls 96 (16 outline + 80 parts), fallback 0. Corrections to F-3616: docstring-misplaced text is at inner_monologue_node.py:6173; 45 outline attempts vs 44 works (last cut by shutdown, inferred). | Founder 2026-11-02 (D-0584): Grand Work parts as plain prose behind a flag, A/B first. | Founder 2026-11-02 (D-0587): his own works excluded from the authoring act's grounding only. | Appendix A re-join (J-2977): 7d at the 10-31 anchor is 96, not 80; stored calls_7d 80" --session J-2977
prompt_registry.py set P-0037 --note "LIVE veto on dissolution (mixtral:8x7b, 2,154 rulings, 65% deny of answered). Deny delays rather than holds (58% of denied stands dissolved ~32 min later). Allows mostly the mind's own re-reading counted as 'superseded'; no abstain class; class/why discarded (J-2848). Jobs J-2942 doc, J-2943 lab, J-2944 founder call. | Founder 2026-11-02 (D-0546): per-stand attempt log first; no behaviour change. | Appendix A re-join (J-2977): 7d at the 10-31 anchor is 64, not 36; stored calls_7d 48" --session J-2977
prompt_registry.py set P-0038 --note "Run G: _scan_shadow_locked renamed _scan_shadow_body | Appendix A re-join (J-2977): 7d at the 10-31 anchor is 1134, not 365; stored calls_7d 597" --session J-2977
prompt_registry.py set P-0044 --note "Three distinct prompts through one call site. | Founder 2026-11-02 (D-0611): newest-first queue. | calls_7d field reads 168 but is stale (J-2913, F-3599): measured 372 calls in the 2.6 days from 2026-10-29 to 11-01 (3 per grounded run, 1 per ungrounded), about 700-1,000 a week; largest single caller of :11441. The row's calls_7d is not settable through this tool. | Appendix A re-join (J-2977): 7d at the 10-31 anchor is 289, not 93; stored calls_7d 168" --session J-2977
prompt_registry.py set P-0045 --note "Appendix A re-join (J-2977): 7d at the 10-31 anchor is 105, not 42; stored calls_7d 66" --session J-2977
```

## 5. What the re-join changes

Numbers are the 30d / 7d / 24h columns at the inventory's anchor (2026-10-31 23:00 local).

- **T2 (`_t2_synthesise`): 1753 / 48 / 8 becomes 175 / 48 / 8.** The 30d figure was 10 times too high; 7d and 24h were never exposed. F-3670 estimated "about 190 in 30 days, 54 in 7 days" from the commit-time join on its own window; the running-version join gives 175 / 48 and the commit-time join (`--method A`) gives the same 175 / 48 / 8 for this function, so the difference is F-3670's window edge, not the method. The 1,696 calls the old join pinned to T2 are Active Imagination's (`_t2_synthesise` -> `_active_imagination` in the flow list).
- **Active Imagination: 493 / 272 / 77 becomes 2189 / 272 / 77.** It was the busiest hidden station in the subconscious line (2,083 of its 2,189 calls on command-r7b:11441).
- **Commitment scan: the old table showed it three ways and made it look dead.** `scan_shadow` 8965 / 769 / **0**, `_scan_shadow_locked` 365 / 365 / 365 and `core.commitment_ledger:?` 846 / 28 / 0. In the version that ran, one call site (`_scan_shadow_locked`) made all of them: 9681 / 1134 / 365, the same as `core.self_implication:scan_shadow` (both fire once per idle thought). The `?` row also held 495 `_judge_defeater` calls: `_judge_defeater` is 542 / 64 / 36, not 36 / 36 / 36. (Master has since moved the call into `_scan_shadow_body`; the registry key P-0038 names that.)
- **Idle-thought satellites.** `_author` (Grand Work authoring, P-0029) 80 / 80 / 0 becomes 652 / 96 / 0, and 96 is exactly the "real 7d calls 96" the P-0029 investigation measured on its own. `_enter_sleep` 403 / 55 / 0 was the night mind and the drill: `_enter_sleep._nm_generate` (P-0023) is 226 / 79 / 24 and `_solve_attempt` (P-0024, whose registry note says "not seen in telemetry") is 249 / 24 / 0. `_route_act` 158 were `_author` lines of an older file. `_think` itself loses 398 (to `_author`): 20622 / 2610 / 763.
- **Subconscious line.** `?(SubconsciousNode)` 356 is `_self_relate_check` (451 / 55 / 15); `_t6_theme_check` 152 is `_synthesise_theme` (234 / 39 / 9); 165 of `_t4_deliberate` are `_t4_legacy_author` (192 / 0 / 0; its registry note counts ~225 runs 09-29..10-20, the same order); `_find_t2_trigger` 113 were T2 calls.
- **Elsewhere.** `core.follow_line:grounds_unclear` (196 / 196 / 0) is `_gen_json`, now 289 / 289 / 93 (P-0044 stores 168; its note already says that is stale). `reentry_p2:settle_shadow_p2` 267 is `_default_primitives._revise`, now 309 / 105 / 42 (P-0045 stores 66). `DreamNode.synthesise` 341 is `_gen_episode`, now 513 / 59 / 12. The 61 `core.node_base:?(Node)` rows per node (a line of an older `node_base.py`) are `NodeBase.run(Node)`, +17 to +22 percent on each of the twelve nodes; 7d and 24h for the nodes do not move.
- **Unchanged.** 39 of the 110 function keys do not move in any window (deliberation, self_implication, condensed_thought, memory_levels, competence, librarian, curiosity_worth, and the other modules whose lines did not shift). The 30d column moves for 71 keys, the 7d column for 16 and the 24h column for none, as F-3670 predicted (30d most exposed, 24h least).
- **Two logs agree.** The same join on `data/thought_station_log.jsonl` (one row per call start) gives the same counts to within one call per function (`_think` 20623 against 20622), so the numbers do not depend on which log is read.
- **The brief's method (A, newest commit before the row) against the running-version method (B).** A leaves 15,418 of 101,880 rows (15 percent) on a line that is not a call, B leaves 4. They agree for T2 and Active Imagination and differ on a dozen rows (`_solve_attempt` 88 under A, 249 under B; `_author` 564 against 652), because Du keeps running the file it loaded at start while commits land afterwards.

## 6. Prompt-registry `calls_7d`

- `prompt_registry.py` has no way to set `calls_7d` (section 4). Follow-up job spawned to add `--calls-7d` and refresh the stored counts from this script.
- The stored `calls_7d` of ten node rows (P-0001 to P-0010) equals Appendix A's 7d column PLUS its 24h column: 77 = 59 + 18 for six nodes, 79 = 61 + 18 for the Critic, 158 = 122 + 36 for Reflection. The 24h window sits inside the 7d window, so the true 7d is 59 (61, 122), not 77 (79, 158). Inferred cause (the arithmetic matches 10 of 12 node rows exactly; Curiosity 117 and Consolidation 29 do not); the correction is in the follow-up job.
- Rows whose 7d column moved: P-0016, P-0023, P-0024, P-0029, P-0037, P-0038, P-0044, P-0045 (P-0038 by alias: its registry key is `_scan_shadow_body`, where the call lives in master; in the running version it was in `_scan_shadow_locked`; also P-0035, P-0060 and P-0075 are matched by the same kind of alias and do not move). Rows whose only change is the 30d column (P-0019, P-0052, P-0053, P-0054, P-0058, P-0059, P-0060, P-0061) store a 7d count that the re-join does not touch.

## 7. Correction to F-3675 (the count of T2 rows tied to a named reading item)

F-3675 says 11 of its 16 T2 rows are tied to a named reading item and 5 are generic. The job brief corrects this to 12 and 4. Re-read from the 16 rows themselves (`P-0053/t2rows.json`, the last 16 `T2_synthesis` rows to 10-31 18:51 UTC): the rows that name a book, film, person, species or place from the reading are the two Tao Te Ching rows, the two dragonfly / Chapter 81 rows, Napoleon / Ouvrard, Portland Exposition Building, the two War and Peace rows, the two Napoleon-at-Acre rows and the 'Evil Twin' row: **11**. The rows with no named item are 10-30 01:40 (factual recall), 10-30 01:55 (wealth, ethics), 10-31 02:48 (the Core axiom line), 10-31 06:46 (sense of reality) and 10-31 18:51 ('the sea shore, a neglected frontier'): **5**. My count is 11 and 5. One reading gives 12 and 4: counting the last row as tied to a named item (a shore is a place in his world, not a reading item); I do not find a second row that would flip. The logged fields (`pattern_label`, `tension_count`, `observation`) do not store the source item, so the row cannot be settled mechanically. Recorded as a finding with that one-row dependency; F-3675's conclusion (output is a reading summary with the tension label pasted on) does not depend on it.

## 8. Limits

- The three raw-HTTP rows are carried, not re-joined (section 1).
- Version-at-start is taken from `Nascence is awake` lines of `data/nascence.log` (local time, the machine's own zone). A file edited before a restart and committed after it is handled by candidate C (2 rows in this window); a file edited and never committed would be wrong in a way no git join can see.
- `core.node_base` and other files with a history of renames are followed by path only (no `git log --follow`); the nodes' `(Class)` suffix keeps the twelve nodes apart, and every label resolved to a file that existed at the row's time except the 70 `asyncio` / `__main__` rows.
- 4 rows had no candidate version with a call on the label's line (kept under B).
- Re-run: `python scripts/rejoin_appendix_a_j2977.py --out <file> --json <file>` from any worktree; it reads `C:/Nascence/data` and the repo's git history and writes only the two outputs. Output data: `docs/lab/J-2977_data/rejoin.json` (method B) and `rejoin_methodA.json`.

