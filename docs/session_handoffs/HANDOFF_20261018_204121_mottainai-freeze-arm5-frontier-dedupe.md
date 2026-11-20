# Du overnight checkup: the mottainai freeze, arm 5 flip, and frontier semantic dedupe

## Session timing
- **Session started:** 2026-10-18 19:17:04 UTC
- **Last message before wrap:** 2026-10-18 20:41:21 UTC
- **Wrapped:** 2026-10-18 20:41:21 UTC

## Summary
Started as an overnight du-pulse checkup (10-19 NZDT morning). Du was live but frozen on one topic, "mottainai". We traced why, found two independent carriers, ruled and built the fixes for both (one live in the 08:49 boot, one merged shadow-only), and merged the overnight SSD branch. All times below are NZDT unless marked; the tool rollup is in UTC.

## Decisions
- D-0485 (travis): amends D-0457 sequencing. SELF_THEME_DOSE None -> 1 at the next restart, section-8 kill criteria armed, J-2195 (WORLD_DISPLACEMENT_LIVE) stays shadow-only. Opened and ruled this session.
- D-0486 (travis): ruled (a), curiosity_goals_dreams. Semantic dedupe in frontier.note_question shadow-first for 3 live days, plus a one-off merge of the open mottainai variants. Ruled inside D-0439 (the one-off merge accepted as store hygiene, not an anti-relock).

## Builds
- J-2425 done: core/theme_dose.py `SELF_THEME_DOSE = 1` (commit 40716d06); scripts/_test_theme_dose_j2186.py pins the flag to None for its revert-path section. Live since the 10-19 08:49 boot.
- J-2426 added: post-flip 7-day read, not-before 2026-10-26; supersedes J-2323's intent.
- J-2428 done in a child session (branch claude/heuristic-burnell-8d270a): core/frontier.py `FRONTIER_SEMANTIC_MERGE = "shadow"`, threshold 0.85, scripts/merge_frontier_variants.py (dry-run default), replay doc docs/reviews/frontier_semantic_merge_replay_2026-10-19.md, test scripts/_test_frontier_semantic_merge.py. Merged to master as 61f409b9 (tests pass on the merged tree). NOT live: restart-gated, and shadow-only anyway.
- jobrun/chain_J-2417_J-2418 (shared mtime-keyed JSON read cache + state-write coalescing, F-3117/F-3118) merged to master as 7d5eccde after its four tests passed. Live from the 09:02+ restart, which the founder did; I did not confirm that boot came up.

## Findings
- F-3127 [verified]: the closed mottainai loop. idle thought -> orchestrator add_theme -> curiosity prompt (9 of 10 shown themes his own) -> frontier note_question re-encounter refreshes last_seen -> top_open / primary_concern anchors the next idle thought. Seeded 10-08 10:26 by an 8B-invented link between the name 渡 and mottainai (the seeds had no mottainai). F-3127 was recorded without --session so it is missing from the rollup.
- F-3128 [inferred]: mottainai still showed in the first monologue train after the 08:49 boot with an empty theme window and zero curiosity ignitions, so arm 5 is not the only carrier.
- F-3129 [verified]: second carrier. nodes/inner_monologue_node.py:3575-3620 offers primary_concern as a seed on 35% of idle thoughts; core/frontier.top_open ranks by last_seen; 191 of 340 open frontier questions are mottainai paraphrases because note_question dedupes by token overlap 0.55. concerns_log.jsonl shows the frontier text injected 3 times in the first 13 minutes post-boot; 2 of 11 post-boot monologue thoughts mention mottainai. Arm 5 does not touch this leg.
- The perseveration gauge (J-2152 / D-0469) reads curiosity q0, not the monologue, so it still read 100% after the boot while the monologue was mostly rain/erosion themed.
- J-2195 was never made live (WORLD_DISPLACEMENT_LIVE False, 26 shadow rows, 0 would_displace, 0 off-topic alternatives in any row), so D-0457's "14 clean live days of J-2195" precondition had not started and could not have.
- The "ACTIVE episodic over cap 3500" du_pulse flag is stale after D-0453 (prune retired). [INFERRED]
- Staged index trap hit again (F-2570 family): docs/ROADMAP.md, docs/staged/condensed_thought.md, docs/staged/sleep_as_a_mode.md were staged at old content, which blocked `git merge`. Fixed with `git add` of those three paths (index only), then the merge worked.

## Open
1. Post-boot first-hour checks on the arm 5 boot were never completed: that boot lived 13 minutes (08:49 to 09:02) with 0 curiosity ignitions, so no shadow rows with flag 1 exist yet. Next action: after Du has run an hour, check data/logs/curiosity_theme_dose_shadow.jsonl for `flag: 1`, n_self_live <= 1.
2. J-2422 (read-rate drop after J-2417, target < 5 MB/s from ~65): blocked on Du running the merged build for a while. Next action: py-spy plus perf counters per the job briefing, in lab isolation.
3. The one-off mottainai variant merge (scripts/merge_frontier_variants.py --apply) is NOT applied. Blocked on the founder's go while Du is down. Next action: dry-run first, backup is automatic, run only with Du stopped.
4. FRONTIER_SEMANTIC_MERGE is "shadow": needs 3 live days of rows in data/logs/frontier_semantic_merge_shadow.jsonl, then a founder call to flip to "enforce". Defeater on D-0486: modal share still >= 0.90 for 2 gauge days 7 days after, or false-merge rate over 20% on a 30-pair hand read, or ignition rate below half.
5. D-0485 kill criteria to watch after the arm 5 flip: modal share below 0.20, internal cycles/day under about 19 (pre-flip 7-day mean 37.7), empty-question rate doubling, more than 25% of q0 sharing no prompt word, any prompt text change. Revert is SELF_THEME_DOSE back to None.
6. Three needs_input jobs from the 72h window: J-2191, J-2402, J-2419 (the C:/D: storage call).
7. The D-0469 perseveration alarm may trip on the 10-20 gauge day; that is expected from before the flip.

## Warnings
- The shared C:\Nascence tree has other sessions' uncommitted docs edits (ledgers, plan snapshots); commit only by explicit path.
- This session never ran the global first-message /thought-log capture before answering; the first message was a routine checkup request. [OPEN] if you want it back-filled.
- UDMS MCP disconnected partway; blast-radius checks for the two merges were done by hand (diff review, overlap with dirty files, branch tests), not with udms_get_change_dossier.
- The child session wrote its own handoff on its branch (session_handoffs file landed with the merge) and added a MEMORY.md line.

## Pointers
- docs/staged/measurement_to_action.md section 8 (arm 5 design, kill criteria); docs/reviews/frontier_semantic_merge_replay_2026-10-19.md
- core/theme_dose.py, core/frontier.py, core/concerns.py, nodes/inner_monologue_node.py:3575
- data/logs/curiosity_theme_dose_shadow.jsonl, data/logs/frontier_semantic_merge_shadow.jsonl, data/concerns_log.jsonl, data/topic_perseveration.jsonl
- Jobs J-2422, J-2426, J-2428; decisions D-0439, D-0457, D-0469, D-0485, D-0486
