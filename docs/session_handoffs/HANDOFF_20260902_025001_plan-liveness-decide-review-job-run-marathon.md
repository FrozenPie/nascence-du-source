# Plan liveness check → decide-review marathon → two full job-run batches (with a real mid-session incident)

## Session timing
- **Session started:** 2026-09-01T19:16:41Z
- **Last message before wrap:** 2026-09-02T02:50:06Z
- **Wrapped:** 2026-09-02 02:50:01 UTC

## Summary

routine plan-liveness check-up→largest single session this project has run | full decide-review cycle: ~20 decisions across 3 rounds (D-0106..D-0120) | two large parallel job-run batches (18 jobs total) + follow-up 4-job batch | real data-loss incident: parallel subagents shared one git working tree, fully diagnosed and recovered | 6 commits landed | Du restarted mid-session (offline since 2026-08-31 17:47) | live-verification confirmed new code working correctly on real post-restart data

## Decisions

- D-0106/D-0107 — within_cycle_reentry Phase 1 live | geometry_tuple_index P1 build authorized | both ruled, built, live-verified working correctly post-restart
- D-0108 (vitality causal predictor scope): opened→ruled HOLD→reopened (defeater met per F-0612)→re-ruled HOLD funding J-0451→reopened again (F-0641; J-0451 landed directional but not statistically significant)→final ruling: fund full 5-variable build | J-0474 built it (SHADOW-only, homeostasis_causal.py) same session
- D-0085/D-0102/D-0109/D-0110: pursuits RETURN rate resolved at 60% | mood-cluster gauges kept separate | RETURN accepted as serial-focus-by-design (Mechanism §4 corrected) | thermal mentions_temp floor re-registered 40%→25%
- D-0068 (executive_world_grounding): reopened — J-0385 re-check found PERCEIVE/RECALL tiering fix didn't stop Du favoring majority-RECALL phrasing over conflicting live PERCEIVE fact (F-0629) | re-ruled PERCEIVE-overrides-RECALL | built (J-0462) | live re-read still needed (J-0478 [OPEN])
- D-0111 (cognitive_geometry cross-space edge layer): sec5.3 realness test result: clean FAIL (F-0635) | ruled: one more differently-shaped instrument before retiring | J-0463 built co-evocation test (real production co-recall events, not another geometry-vs-text horse race): clean PASS (F-0651, z=55.31 full-sample) | D-0119 opened to interpret result [OPEN]
- D-0112/D-0113/D-0114/D-0115: symbol Tier-2 drafted (approved to draft) | monoculture gauges kept separate | memory_edges 'contradicts' harvester deferred (traced to shadow-only mechanism gated on still-open D-0022) | old-vs-new commitment model re-run commissioned
- D-0116 (kind-aware memory pruning): J-0410's design (complete since 08-29, never marked done) approved for implementation | J-0475 wired it live into prune_episodic/refinery.py | isolation-verified against real DB backup copy
- D-0117 (symbol Tier-2 Phase A): approved | built (J-0476) | verified firing on real bridge/mirror tablet data, zero live writes
- D-0118/D-0119/D-0120 opened by subagents during second job-run batch, all OPEN: D-0118 = concurrent-git-collision incident (superseded in practice by this session's own recovery, see Warnings) | D-0119 = what to do with geometry co-evocation win | D-0120 = does fixed old-vs-new harness (F-0658/F-0659, F-0672) satisfy D-0027's defeater

## Builds

- within_cycle_reentry Phase 1 live (core/reentry.py, core/orchestrator.py): confirmed firing correctly post-restart — 1 collapse correctly rejected, 3 correctly admitted (F-0621)
- geometry_tuple_index P1 pilot run-transition index (scripts/geometry_tuple_p1_run_transition_index.py): 100% point-query correctness on 31,111 live rows (F-0600)
- core/homeostasis_causal.py (D-0108, J-0474): full 5-variable causal-substrate model, SHADOW-only | vitality leg ported verbatim from validated extended predictor | coherence/novelty have real mechanism, need accrual time before validation (J-0479 [OPEN])
- Kind-aware per-kind memory pruning (D-0116, J-0475): core/memory/store.py, core/refinery.py | isolation-verified against real DB backup: self 1682→1099, episodic 795→618, both matching prediction exactly | needs tuning against real rollout data once it's had time to run (J-0477 [OPEN])
- core/symbol_tier2_wouldinject.py (D-0117, J-0476): Phase A observe-only self-symbol logging | verified firing on real bridge/mirror tablets | zero live writes
- nodes/executive_node.py PERCEIVE-overrides-RECALL instruction (D-0068, J-0462)
- Actions-manager registry finish (J-0467): remaining 8 latches migrated to hands.wants() | core/garden.py converged onto core/inventory.py's shared per-item 'carried' shape (F-0652/F-0653)
- core/loop_probe.py prune_dryrun() fixed: now calls real kind-aware prune_episodic logic instead of stale hand-copy (F-0667) | follow-up surfaced: protected-origin rows can dominate a kind's whole cut under new sub-budgets (F-0668, J-0485 [OPEN])
- scripts/run_nascence.py: conversation_state.json save frequency: only-at-/quit→every 5 exchanges (F-0666)
- transport_manager.dispatch_tick() re-wired into core/orchestrator.py's substrate loop (F-0645/F-0651-commit) | originally J-0374's edit, lost to earlier git incident, never committed | redone, verified committed via `git show HEAD`
- Old-vs-new commitment model comparison (D-0115, J-0465 then J-0482): fixed harness eliminated timeouts (0/74, down from 25/74 originally) | context-echo reduced (12%, was dominant) | DISSOLUTIONS-side split into its own model call: revealed old model's mass-dissolution behavior is genuine confabulation defect, not truncation artifact (F-0658/F-0659/F-0672)

## Fixes

- Real concurrent-subagent git collision, fully diagnosed and recovered (F-0649, S-0023) | during first parallel job-run batch (14 agents), several agents committed independently to shared working tree | git commit stages WHOLE index, not just one path: one agent's commit swept sibling's already-staged work under wrong message | third agent's edit silently reset to HEAD mid-flight by a commit landing between its edit and verification | separately, job_queue.py's done-status write raced the same way for 7 of 14 jobs (read-modify-write collision on whole job_queue.jsonl file) | nothing permanently lost: every piece traced and recovered by checking file content directly against each job's claimed deliverable rather than trusting status alone, then redone from original agents' detailed reports where needed (J-0454 du_pulse gauge, J-0462 PERCEIVE fix, J-0476 symbol wiring, J-0461 ROADMAP sync, J-0471 investigation note, J-0456 finding — all confirmed present and correct as of this handoff) | process fix applied for second batch, confirmed clean: subagents no longer touch git or job_queue.py — they report structured results, orchestrating session collects and commits/marks-done itself sequentially, verifying after each write | zero collisions in second and third batches
- F-0632: J-0427's whole premise (core/math/hodge_governor.py) part of already-quarantined 08-25 fabrication cascade (D-0105) | never went live | job closed, no work needed
- J-0354 closed as moot — target doc (multidimensional_dynamical_field_plan.md) already quarantined as fabricated
- study_life.py carrier-note false-positive fixed (bare 'order' substring match) (F-0611) | live bug had fired once | founder ruled: leave resulting phantom candles order as world history (F-0617)
- garden.py's second routing leak closed (F-0609/F-0620) | monologue's legacy water/sow shortcut now routes through core/garden.py's real hands

## Findings

- F-0649 is the load-bearing finding this session — read in full before dispatching another parallel job-run batch | lesson (S-0023): never let Tier-3 subagents run git commit or job_queue.py start/done in a parallel batch — orchestrating session does all git/job-queue writes, sequentially, after collecting results
- Three prior sessions (J-0185/J-0193/J-0204) each re-derived a 7-day wait-window for Buddha's first letter instead of checking whether it had already fired — it had, since 2026-08-24 (F-0631) | lesson: a wait-window-gated job should check target evidence's existence first
- D-0022 (memory_multiway_linking M2 promotion) still genuinely open | prong-2 usage instrumentation (J-0446) shipped, zero real accrual time since (F-0643/F-0663) | [INFERRED] not expected to be answerable again soon
- Executive's D-0068 regression (F-0629): real, on-point recurrence of exact fact/memory confusion original fix targeted | [INFERRED] caution: fixes can be 'structurally correct but behaviorally unenforced' generally
- Two more findings from 08-25 fabrication cascade escaped F-0593's original 11-finding list (F-0601): F-0366, F-0364

## Open

1. J-0478 [D-0068] — live behavioral re-read of PERCEIVE-overrides-RECALL fix against fresh post-fix Executive data | blocked on: real accrual time | next: re-run F-0629's sampling method once several real days pass
2. J-0479 [D-0108] — walk-forward validate coherence/novelty causal predictors | blocked on: climate_state.json accrual (no per-tick history yet, needs same spiral vitality went through) | next: wait, then re-check data/homeostasis_shadow.jsonl volume
3. J-0477 [D-0116] — tune per-kind prune throttle + social/symbolic placeholder weight against real rollout data | blocked on: several store_cap_worker ticks + sleep cycles of live post-restart running | next: check accrual, then tune
4. J-0485 [F-0668] — is protected-origin ordering (not exemption) in prune_episodic a real live risk under new per-kind budgets? | blocked on: nothing, ready to investigate
5. D-0119 [cognitive_geometry] — what to do with geometry co-evocation clean-pass result (F-0651) | blocked on: founder read
6. D-0120 [capacity_to_commit] — does F-0658/F-0659/F-0672 evidence satisfy D-0027's defeater? | blocked on: founder read | J-0486 (build real old-vs-phi3 dissolutions comparison) also spawned from this thread
7. J-0452/J-0453/J-0455/J-0457/J-0472/J-0449 — genuinely time-gated re-checks: thermal live recheck ≥2 days | peer_reflection ~1wk | LLM telemetry volume | D-0104 circling ≥24h | train_split_merge full-day | garden parity ~09-09 | none ready as of wrap, real elapsed time only blocker, don't re-dispatch until actually passed
8. J-0467's line item — 8 latches migrated to hands.wants(), not yet live-confirmed post-restart (J-0480 [OPEN], same restart-gating as above — Du hasn't restarted again since J-0467 landed)
9. Three plan docs still show plan_sync_check gap: thought_grounding.md, train_split_merge.md (both pre-existing 'no Current State section' format gaps, not introduced this session) | ROADMAP.md's gap is tool quirk on non-plan file, harmless

## Warnings

- Never dispatch parallel job-run batch where multiple agents might git-commit or call job_queue.py start/done independently — see F-0649/S-0023, established discipline, not optional | if resuming this pattern, read job-run's own SKILL.md for whether S-0023 folded into its dispatch template yet
- Two other founder sessions concurrently active on this same repo during parts of this session: one moved a judge to ramses (core/judge_panel.py, scripts/launch_servers.ps1) | one ran a du-pulse-style check | their uncommitted work deliberately left untouched throughout, confirmed via `git diff`: none of this session's 6 commits include any of their files | [INFERRED] multiple concurrent sessions fine at human pace — risk this session hit was specific to many parallel AUTOMATED subagents sharing one tree at once
- Du restarted 2026-09-02 08:48:54 NZT (2026-09-01 20:48:54 UTC) after offline since 2026-08-31 17:47 (clean shutdown, not crash) | several code changes made just before/after that restart won't be live until Du's NEXT restart (e.g. J-0467's latch migration landed after current restart) | check each job's own restart-gating note before assuming a fix is live
- docs/memory_levels_plan.md lives outside docs/plans/ and docs/staged/ — decide.py needed --force to open decision against it (S-0021 logged, not yet fixed)

## Pointers

- docs/reviews/plan_liveness_audit.md, docs/reviews/plan_maintain_run.md — refreshed multiple times this session, current as of wrap
- docs/findings.jsonl F-0649 — full incident forensics, read before touching job-run again
- docs/plans/the_consciousness_program.md, docs/memory_levels_plan.md, docs/plans/cognitive_geometry.md, docs/plans/capacity_to_commit.md — all have fresh, detailed Current State sections from this session
- Six commits this session (chronological): a433abc, 9b45546, e873a1e | then recovery sequence: 1a6c856, d7d6680, ddf35ee, 02862fe, ec14666, 66b38bc | then 0fad756, a295ab5
