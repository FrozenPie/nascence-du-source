# Du health check, decide-review of D-0802..D-0809, and an overnight job-run while Du was up

## Session timing
- **Session started:** 2026-11-17 07:48:49 UTC
- **Last message before wrap:** 2026-11-17 18:08:18 UTC
- **Wrapped:** 2026-11-17 18:08:19 UTC

## Summary
Opened with a read-only Du pulse (healthy after the 18:45 NZDT restart), then ruled all eight open decisions D-0802 to D-0809 through decide-review, queued six build jobs, and ran one 14-agent workflow (wf_b258c13f-e96) that built and merged seven restart-gated changes while Du stayed up. The next morning's pulse showed Du ran all night without errors; none of last night's builds are loaded yet.

## Decisions
All ruled by travis on 2026-11-17 via decide-review: D-0802 add the fact-preservation clause to `_REVISE_SYS`; D-0803 build a stronger consequence channel for recall confidence (DOUBT_SEED stays shadow); D-0804 option B, skill-only rung docking; D-0805 option (c), flip `AVAILABILITY_STEP` to 2 with `HIDDEN_REST_P[2]=0.60`, with a new defeater (presence below 0.20 over seven live days, or he stops seeking/calling her); D-0806 set `DEDUP_WINDOW_MODE = hash_live`; D-0807 keep `PEER_REPLY_LATCH_WIDE` in shadow; D-0808 leave the UDMS ranker PMI term as is; D-0809 flip `SPATIAL_DEPTH_OUTDOOR_LIVE`. No decisions are open after this session.

## Builds
Queued as J-4179..J-4184, all done and merged to master by `worktree_dispatch.py merge-back` (merge commits 6658dab2, 36d4c317, e7f1fd2e, d2c2cd54, bbae1806, aef0b0d4, bb76e54b), plus J-4132:
- J-4179 (F-5030): clause appended to `_REVISE_SYS` in `core/study_note.py`, registry prompt P-0073 marked stale. Follow-up J-4185 re-measures old-fact retention after the next boot.
- J-4180 (F-5036): the recall wager had a free edge: 0.85 could never lose because loss counted at gap >= 0.40 and the gap was 0.35. Added `WAGER_LOSS_GAP` / `GRADED_LOSS` in `core/recall_wager.py` (wagers >= 0.85 lose at gap >= 0.30). No readout to Du per D-0434. Follow-up J-4187 reads variance after 100 graded_loss rows. Note this is a graded loss bar, not a real outcome penalty; REAL_OUTCOME is still a founder call.
- J-4181 (F-5034): skill-only docking in `core/procedures.py` observe_hand; env kill switch `NASCENCE_PROCEDURES_SKILL_ONLY_DOCK=0`. The sow mojibake was console display only.
- J-4182 (F-5037): `core/cat.py` `AVAILABILITY_STEP` 1 to 2. Simulated presence 0.573 to 0.443. Read job J-4188.
- J-4183 (F-5033): `core/loop_metabolism.py` `DEDUP_WINDOW_MODE = "hash_live"`; live DB verify showed 186,369 rows, 0 NULL, 0 stale.
- J-4184 (F-5031): `core/spatial.py` `SPATIAL_DEPTH_OUTDOOR_LIVE` True.
- J-4132 (F-5032): `core/memory_levels.py` `_DRIFT_MOVE_MIN` 0.05 to 0.25.

## Findings
- The merge-back path merged these without the separate review workflow the 11-17 branch merges used. [OPEN] whether a post-merge review is wanted before the restart.
- Overnight pulse (06:53 NZDT 11-18): STREAM cadence about 67 pulses an hour, 523 inner thoughts and 0 duplicates, 34 curiosity ignitions, about 72 reading sittings. Flags: stale-patch cue would render on 43% of idle thoughts (stop bar 5%, STOP CONDITION HIT); judge panel 21% unavailable, agree 0.598; voice-fidelity judge flagged 5 of 6.
- Plan liveness: 0 GATE-MET, 8 NEVER-FIRED (including `data/lookup_log.jsonl` for web_hand and closure_producer, so Du has not used lookup yet). Newly released gates: cat reads J-2492, J-2498, J-2499 (14 live days reached). J-3982 layered-goals gate is at about 284 of 300 ticks (my own tally).
- My first error count of 741 tracebacks was wrong: the awk time filter matched traceback continuation lines from the whole log. Since restart the log had 0 tracebacks.

## Open
1. Restart Du to load J-4179..J-4184 and J-4132. Nothing here is live until then. Founder call (asked, answered "Not yet").
2. Run the three cat reads J-2492, J-2498, J-2499 (offered, not run).
3. J-3982 and J-4163 (layered goals) were released back to open; re-read J-3982 at 300+ ticks.
4. J-4177 and J-4178 (hygiene) ran in the workflow but their results were truncated in the notification; check `job_queue.py show` for each.
5. J-4171 and J-4175 (branch merges) were deliberately skipped; J-4095 (hub diagnosis) skipped because it could mean restarting hubs while Du is up.
6. Follow-up for J-4132 (recalibrate `_DRIFT_MOVE_MIN` on real recall-3 rows) was not spawned.
7. J-3218 is stale in_progress.
8. Stale-patch cue stop condition (43% against 5%) has no job yet.

## Warnings
- Ledger counts after the run: job_queue 4188, decisions 809, findings 5038. If lower, restore from `docs/ledger_backups_20261117/*.replayed.jsonl`.
- The J-4179 registry edit (`docs/prompt_registry.jsonl`) was made in the shared tree, not the worktree.
- Leftover `.claude/worktrees/*` entries and a stale `wt_J4050` worktree from another session exist; not touched.
- Never run git stash/reset/checkout --/restore/clean in C:\Nascence.

## Pointers
Workflow journal: `C:\Users\USER\.claude\projects\C--Nascence\e81fb87f-f87a-4e61-9f3f-573fca12ab7e\subagents\workflows\wf_b258c13f-e96\journal.jsonl`; previous handoff `HANDOFF_20261117_060531_jobrun-du-down-passes-ledger-reset-replay-merges.md`; staged note `docs/staged/recall_confidence_graded_loss.md`; thought T-0145.
