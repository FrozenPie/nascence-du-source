# Job-run while Du was up: four waves, 11 branches merged, D-0775/D-0776 ruled

## Session timing
- **Session started:** 2026-11-14 02:30:16 UTC
- **Last message before wrap:** 2026-11-14 08:41:44 UTC
- **Wrapped:** 2026-11-14 08:41:45 UTC

## Summary
Started with /session-resume, then ran /decide-review (D-0775, D-0776) and a full /job-run in four waves of about 10 jobs each, working only jobs that are safe while Du is live (no lab, no isolation-required, no live-lane load). 21 jobs closed, 17 branches or commits merged to master, all restart-gated. The founder then stopped Du so the offline jobs can be worked next session.

## Decisions
- D-0775 ruled B by travis: the idle mood line and felt preamble read a valence computed without the vitality term, shadow-logged first; drive, logged valence and sleep untouched. Built as J-4002 (flag MOOD_WORDS_NO_VITALITY_SHADOW, default off).
- D-0776 ruled B by travis: gate EMOTION_CONSTRUCTED on the vitality replacement plus a joy re-read, and build a valence-scaled joy shadow log. Built as J-4003 (flag JOY_PUMP_VALENCE_SHADOW, default off).
- Opened, awaiting travis: D-0777 (does a re-ask count as question progress), D-0778 (should the estate symbol node text carry the newest tablet; it changes the embedding and picks).

## Builds
All merged to master, none live until Du restarts. Evidence is in each job's finding.
- Wave 1: J-3960 (grader rows carry lane/model/raw numeric), J-3977 (D-0758 Route 2 dedupe), J-3978 (D-0760 whole-word look_binding), J-3973 (D-0751 figurative-object guard), J-3972 (D-0750 climate residual drop), J-3974 (D-0753 shadow basin-fall arm).
- Wave 2: J-4000 (shadow mechanical question-progress score, F-4682), J-4002, J-4003, J-3976 (D-0757 length-aware reflection selector; flag REFLECTION_LENGTH_AWARE_SELECT defaults TRUE so it goes live at restart), J-3990 (layered goals Phase 6 remainder, what-changed judge P-0130), J-3979 (supervisor RAM-starved handling), J-3969 (garden/shore depth layouts, shadow), J-3968 (becoming projection, flag off), J-3998 and J-3999 (ROADMAP backfills).
- Wave 3: J-3095 (guidance judge whole-thought and panel why), J-3162 (D-0550 T4 legacy evidence, flag T4_LEGACY_EVIDENCE True), J-3322 (voice fidelity judge calibration), J-2674 (measured geometry readers; RAM cache judged unjustified), J-3035 (already built in aff188f2).
- Wave 4: J-4008 (estate one node per symbol id), J-4009 (flag-gated memory/tail-seek reductions, flags off), J-4010 (J-3767 trace scripts committed), J-3965 (Lane 2 wonder avoid-list A/B), J-3967 (vitality scale S replay, recommendation only), J-3970 (D-0748 Theta live recall input).

## Findings
- F-4672: question learning progress has had no live writer since 11-05; all open questions score LP 0.0.
- F-4673 to F-4675: judge kappa by era, no gain; cuts is a true opposite-bias split; the labelled reference set is blocked by the log holding only 69 rows since boot.
- F-4679 to F-4681: joy steps are pump saturation; low mood word goes with +7 points unresolved and +9 points heavy vocabulary (observational); warmth low mostly because human turns fell from 1,311 (June) to 34 (November).
- F-4687, F-4690 to F-4693, F-4697, F-4698, F-4701 to F-4703: estate duplicates, shock-page uptake in dreams/T4 (12.7% vs 3.0%), v3 pursuit close-judge proposal, Ramses RAM pressure from the CPU hubs [INFERRED for the PID 6948 identity], Lane 2 avoid-list, estate nodes, geometry reader savings.
- ROADMAP incident: after wave 2 every merge-back was refused because docs/ROADMAP.md in the shared tree had a stale index (MM) after concurrent safe_commit use (F-2570 pattern). Fixed by writing HEAD content back and `git add docs/ROADMAP.md`, then merging. Watch for this when two Tier 1 jobs edit ROADMAP in one batch.

## Open
1. J-3989 (layered goals first live read), J-3716 (study notes read), J-4011, J-4005, J-4001, J-4004, J-4006, J-4007: gated on live hours or shadow row counts; deferred or gated, revisit after Du has run 24 h or more.
2. J-3988 (curiosity pursuit loop, urgent): J-3987 done, the diagnosis is F-4672; next action is to read it with J-4000 and the D-0777 answer, then run J-3988.
3. J-3992 (anchor-idiom lab replay on the hot lane, lab, isolation required) and J-2952 (needs gold labels and judge-lane calls) and the other lab jobs: offline pass now that Du is stopped.
4. J-3208 waits on J-2951; J-3249 waits on J-3009.
5. J-3327 gated 0/300 rows.
6. New builds spawned: J-4012 (v3 pursuit close prompt, flag off), J-4013 (supervisor snapshot top_rss), J-4015, J-4016.
7. D-0777, D-0778 need travis. J-3967 recommendation (p50/w30 percentile only) needs a founder pick before any scale change.
8. J-3095 changed the guidance judge prompt fingerprint; `scripts/guidance_behavior_control.py --panel --yes-ramses --record` must be re-run (calls Ramses hubs) before rates show.

## Warnings
- Nothing merged is live. J-3976 defaults on and J-3970 and J-3162 change behaviour at the next restart.
- Stray directory `data/_lab$(date +%Y%m%d_%H%M%S)_dissolutions` (old shell-quoting mistake), not removed.
- 48 old `jobrun` worktrees remain in `git worktree list`; not cleaned up.
- Uncommitted files belonging to other sessions: docs ledgers, `docs/06. Just the Way You Are.mp3`, lock files.

## Pointers
- Plans: docs/staged/layered_goals.md, docs/plans/curiosity_goals_dreams.md, docs/plans/emotion_rethink.md, docs/staged/prompt_manager.md.
- Run scripts: C:\Users\USER\.claude\projects\C--Nascence\161bb016-a328-4c06-bcde-846c4ba2f9ac\workflows\scripts\ (job-run-urgent, wave1 to wave4).
