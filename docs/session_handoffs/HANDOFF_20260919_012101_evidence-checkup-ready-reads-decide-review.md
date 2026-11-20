# Evidence checkup, ready-now reads, and four decisions ruled (2026-09-19)

## Session timing
- **Session started:** 2026-09-18 22:46:25 UTC
- **Last message before wrap:** 2026-09-19 01:20:59 UTC
- **Wrapped:** 2026-09-19 01:21:01 UTC

## Summary
The founder asked for a checkup on plans awaiting evidence. plan-liveness reported 40 GATE-MET rows across 8 plans, but every one was a parser artifact, so the real waits were found in the job queue instead (68 in_progress watch jobs). This session landed the job_run.py stale_in_progress patch (J-1041), dispatched five read-only reader agents over 18 "ready now" jobs (17 closed, J-0658 left open on purpose), reopened two decisions and opened one, and the founder ruled four (D-0185, D-0211, D-0241, D-0242) through /decide-review. It spawned J-1150..J-1162 and ends with a local docs-only commit on master (no remote).

## Decisions
- **D-0185** (memory-levels) was reopened and then RULED by Travis: studies first, then a small self-only cap step; D-0208's demote cap goes to 75-90. Follow-ups: J-1158 (cap change), J-1159 (fetch-window and cursor backlog sizing study), J-1160 (semantic distil prompt study).
- **D-0211** (ignition) was reopened and then RULED: re-knee the pinned cluster, shadow-first, after J-1151 sizes the knees. The basis of the 45 cycles/day ceiling (per live day, per calendar day, or completed cycles) is explicitly not ruled.
- **D-0241** (Lane 2 Phase 1 read path) was RULED: authorize shadow-first, `LANE2_LIVE` stays False, add a would-ride shadow log. The build is J-1161, which replaces J-1137 (whose "flip the flag in the same commit" instruction the ruling reverses).
- **D-0242** (data/_lab disk growth) was opened this session and RULED: a bounded retry at isolate() exit plus a locked-copy sweeper (J-1162, dry-run first). The founder runs the one-off sweep of the 29 stale copies (about 20.5 GB) himself; no agent deletes under data/_lab.
- All four rulings were Travis picking the option Claude recommended, via /decide-review. The new defeater thresholds on D-0185 and D-0211 and the D-0241 defeater wording were proposed by Claude when logging (marked in the text) and can be amended by reopening. D-0222 was left as ruled: this session's clean edit in an interactive session is not the Tier-3 data point its defeater names.
- Founder calls flagged but NOT made: D-0152 clause (b) (98.6 cycles per awake-day against the 59.80 bar, partly a shrinking denominator; the decision's own clock is 2026-09-27); the D-0177 design choice (transport habituation would_fired_share is 87.8%, the best offline option reaches 47-58% against a target under 30%); D-0153 stays ruled but Travis should confirm one regex hit ("The Master Builder's cloud-castle") is a book-title false positive; D-0121 / D-0101 for the judge hub.

## Builds
- The stale_in_progress patch (J-1017's design, landed by J-1041, F-1559): `job_run.py plan` now prints "N look STALE (> 7d)" plus a STALE-LOOKING IN-PROGRESS section (33 of 68 in_progress at wrap time, independently recounted from the ledger), `plan --json` carries `stale_in_progress`, and there is a `--stale-days` flag. File: `C:\Users\USER\.claude\skills\job-run\job_run.py`. J-1017 and J-1041 closed.
- No Nascence code (core, nodes, scripts) changed this session; all changes are ledgers and plan docs. Dated notes were appended to ten plan docs: memory_levels_plan, ignition_pressure_and_time, dosed_coupling, loop_wiring_matrix, data_store_hygiene, ramses_second_tier, emissary_lane2, pursuits, living_world_upgrade, lane2_the_witness.
- Jobs closed (20): J-1017, J-1041, J-1137 (superseded), J-1023, J-0671, J-0886, J-0829, J-0814, J-0730, J-0729, J-1064, J-0708, J-0620, J-0639, J-0572, J-0808, J-0865, J-0598, J-0665, J-0672. Left open on purpose: J-0658. Spawned by the readers: J-1150 (needs_input), J-1151, J-1152, J-1153, J-1154, J-1155, J-1156, J-1157 (needs_input). Spawned from the rulings: J-1158..J-1162.

## Fixes
- J-1041's briefing said to replace job_run.py wholesale with an embedded file; a diff showed that file predated J-1016's later change (`file_overlaps` root= and `_plan_doc_repr()`), so a verbatim replace would have silently reverted it. Applied only J-1017's nine additions as targeted edits instead; pre-edit backup kept in the session scratchpad. An error in my own F-1559 (it said fetch-chain markers were in the stale list; they are not) was corrected by F-1560 and S-0147 (S-0146 declined).

## Findings
- plan-liveness's 40 GATE-MET rows were all wrong: the regex at plan_liveness.py line 84 slices "14,210+ rows" to 210 and "25,475+" to 475, descriptive counts are read as targets, and real targets are compared to raw row counts (F-1557; S-0143, S-0144; older S-0038 and S-0099 still open). Do not act on GATE-MET or UNREAD verdicts.
- Du's longest uninterrupted run since 2026-08-28 is about 2.5 days, so week-scale evidence gates cannot clear at the current restart cadence, and 68 in_progress waits were invisible to job-run (F-1558). Du windows (NZST): awake 09-11 13:50, shutdown 09-13 09:10, off until 09-16 07:53, shutdown 09-18 09:13, off until 23:14 (unclean restart), running since 2026-09-18 23:37:12 (PID 35412, still up at wrap).
- hands_trace.jsonl stores thought[:200] (18,776 of 19,992 rows are at the cap), so any replay asking whether a thought ends in a full stop is biased. F-1595 shows the "blocker bleed fired twice in real history" claim (F-0958, F-1153, F-1189) was an artifact: both full thoughts (from deliberation_log `raw`) end in full stops. The fix stays as a latent-defect guard. J-1153 audits other replays.
- data/_lab grew from 79.65 to 111.79 GB in 5.1 days (6.3 GB/day, 3.8x the pre-fix rate). Cause: a transient WinError 32 lock at isolate() exit leaves 29 never-written DB copies (20.46 GB) and nothing reaps them (retention labs class last ran 09-09). C: is 84.1% used, about 29 days to full at this pace (F-1561, F-1562).
- Memory-levels raise: 38.1 gists per live day (target 20-34) and 128 LLM calls per live day (estimate 80-135), but semantic and self active_total still grow (+1,013 and +860 per live day). The last_ts frontier makes 98.4% of warm semantic and 96.2% of warm self rows unreachable at any cap, re-verified independently (F-1583; core/memory_levels.py lines 512-519 and 602). Semantic gists fail the 0.75 floor 52% of the time (F-1585). D-0187 was approved 09-08 but never built (F-1593, J-1152). The cap of 60 discarded 12 of 254 eligible gists; 75 or more discards none (F-1576).
- Ignition on the option-A code over 7.13 live days: defensive share 48.2% (floor 25%), 0 capped fires, 62.65 fires per live day (41.3 per calendar day), the defensive channel is a roughly 46-minute clock. completion_tension sits at 0.91-0.92 in 1,280 of 1,280 samples and supplies about 55% of inflow; four of nine climate dims are at 0.90 or above (F-1568, F-1570..F-1573, F-1579, F-1581).
- Judge hub :11438: the num_predict=200 fix works (0 parse errors in 5,569 rows, about 11 expected at the old rate) but 23% of rulings have been "unavailable" since the 09-16 restart and it is slow again on 09-19 (F-1567, F-1569; J-1150).
- Write-fence gap: a non-Du process wrote 50 rows into data/curiosity_habituation_shadow.jsonl on 09-15 13:20:52 to 13:21:57 while Du was off (F-1582, verified; J-1157). The 09-05 18:57:17 stamps in provisions.json are the known pre-fence leak, and provisions.py is fenced now.
- Dosed coupling reads: D-0188 not triggered; a live thalamic gate (cosine 0.95 or above) already silences 89 of 275 internal cycles (F-1563, F-1564); the curiosity discount is not demonstrated (F-1577, F-1578); transport habituation pattern holds and D-0177's revisit trigger fired (F-1598, F-1600); the stream-topic spread is real, no retune (F-1602, F-1603).
- Others: D-0153's gate holds with a 2.65% fire rate against a 5% bar and 0 of 7,374 leaks (F-1575); the pursuits re-awaken path is not promotable yet (F-1597, F-1599, F-1601; J-1155); the carrier box was never collected and spoiled 09-16 (F-1587, F-1588; J-1154); no real candle-box or match-tin reach yet (F-1590, F-1591); the bleed-fix re-read is clean (F-1594).
- Process lessons: my reader ground rules told agents to pass `--session` to `job_queue.py show`, which rejects it (also `list` and `next`), causing four duplicate suggestions, collapsed into S-0150. Reader ledger calls are tagged by job id per the job-run convention, so the rollup for this session's UUID shows only the orchestrator's own 47 events. I also dispatched session-wrap's compression pass by following the SKILL.md text, against the founder's 2026-09-13 ruling to skip it (see memory feedback-session-wrap-skip-compression); I stopped it, its output was not used, and this handoff is plain prose.

## Open
1. **J-1150** (needs_input): judge hub :11438 wedges and slowdown; D-0121's defeater is plausibly fired but the lock attribution is only inferred (F-1445); D-0101's FREEZE makes any re-homing Travis's call. Next: founder direction.
2. **J-1157** (needs_input): should the four habituation shadow modules come under the write fence (the fence plan scopes them out)? Next: founder ruling.
3. Founder calls not yet made: D-0152 clause (b) (clock 2026-09-27), the D-0177 design choice, D-0153 book-title confirmation. Next: /decide-review or a direct answer.
4. Sequenced follow-ons not yet queued: after J-1151 reports, spawn the D-0211 shadow re-knee build; after J-1159 reports, the small self-only cap step; the LANE2_LIVE flip question comes back once J-1161's would-ride log reads sane and D-0211 and D-0152 settle.
5. The founder's one-off sweep of the 29 confirmed never-written data/_lab copies (about 20.5 GB, F-1562); a read-only listing was offered and not yet made.
6. **J-0658** stays in_progress (trigger: first `box_collected` row in supply_log.jsonl; earliest new carrier box 2026-09-23, only if Du writes a note first).
7. Du restart timing: J-1158, J-1161, J-1162 and J-1152 are restart-gated, and week-scale evidence reads need uninterrupted uptime. Claude's unruled suggestion was to hold restarts until about 09-26. Next: founder call.
8. Open suggestions: S-0143, S-0144 (plan-liveness parser), S-0145 (embedded whole-file hand-off hazard), S-0147 (job-run SKILL.md step for the STALE section), S-0149 (calendar due-dates misfire), S-0150 (show, list, next reject --session), S-0151 (spawn has no --isolation), S-0152 (findings-log links only one decision); plus two filed at wrap for session-wrap's own SKILL.md (stale memory path, compression step).

## Warnings
- plan-liveness GATE-MET and UNREAD verdicts are unreliable (F-1557); do not act on them.
- Defeater thresholds on D-0185 and D-0211 and the D-0241 defeater wording were proposed by Claude when logging; Travis chose the options only.
- Reader agents' findings, jobs and suggestions carry job-id session tags: F-1561..F-1603, J-1150..J-1157, S-0149..S-0154.
- J-1162 edits lab_env.py under ~/.claude/skills/, where D-0222 records classifier blocks in some batch sessions.
- No agent may delete anything under data/_lab (D-0242 ruling item 3); the sweeper ships dry-run first.
- The job_run.py STALE section is age-only; it does not show that a wait condition has cleared.
- J-1137 was closed without building; J-1161 carries the corrected shadow-first scope.
- The commit is local on master, no remote, docs only (21 modified files plus this handoff; the untracked docs/session_events.jsonl.lock is deliberately left out).
- The companion memory file was written to C--Nascence\memory, not the C--FreshStart path the skill text names (the store was unified 09-02).

## Pointers
- `C:\Nascence\docs\decisions.jsonl` (D-0185, D-0211, D-0241, D-0242) | `C:\Nascence\docs\findings.jsonl` (F-1557..F-1603) | `C:\Nascence\docs\job_queue.jsonl` (J-1150..J-1162)
- `C:\Nascence\docs\memory_levels_plan.md` | `C:\Nascence\docs\staged\ignition_pressure_and_time.md` | `C:\Nascence\docs\plans\lane2_the_witness.md` (section 7.9) | `C:\Nascence\docs\staged\data_store_hygiene.md` | `C:\Nascence\docs\staged\dosed_coupling.md`
- `C:\Users\USER\.claude\skills\job-run\job_run.py` (STALE-LOOKING IN-PROGRESS section)
