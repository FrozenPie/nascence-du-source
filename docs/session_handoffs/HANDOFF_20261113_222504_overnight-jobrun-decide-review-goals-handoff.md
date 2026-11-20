# Overnight three-pass job-run, Du pulse and hub check, 25-decision review, and a hand-off into a Du-goals discussion

## Session timing
- **Session started:** 2026-11-12 19:28:17 UTC
- **Last message before wrap:** 2026-11-13 22:25:03 UTC
- **Wrapped:** 2026-11-13 22:25:04 UTC

## Summary
Ran three overnight /job-run passes (about 230 jobs closed, every worktree branch merged) while Du was down and then live, committed the leftovers, took a Du pulse and a hub check, and cleared all 25 open decisions in a /decide-review (17 follow-up jobs spawned). The session ends by handing a Du-goals discussion to a new Fable window; the goals brief is under Open item 1.

## Decisions
All 25 ruled by Travis (--by travis, session decide-review-20261114) on 2026-11-14 NZDT:
- Shadow / wait: D-0429 (Lane 2 wonder field stays shadow, add anti-repeat), D-0742 (wait for more farewells), D-0743 (pursuit close judge keeps shadowing with a changed prompt/threshold; specifics NOT given, J-3966 asks for a proposal), D-0752 (Lane 2 notice_unsupported scoreboard-only), D-0753 (v4 re-entry arm, shadow), D-0756 (wait for Travis's own labels, J-3418), D-0744 (replay vitality scale S on 340 real fires first).
- Go live (restart-gated): D-0748 (Theta live recall input), D-0749 (SKY_MODE live at next restart, set SKY_CUTOVER_TS, flip back if sleep onset moves over 1 h), D-0754 (COMMITMENT_ANCHOR_LIVE at dose 0.5), D-0758 (Route 2 recall dedupe=True), D-0760 (whole-word look_binding, drop up/out/far).
- Builds: D-0745 (estate node: Executive projected block only, 3-8 percent band, keep p95 coherence refusal, shadow-only and flag-off), D-0747 (reach-set stays logged only; next P3 build is depth layouts for garden and shore), D-0750 (drop residual half on the four climate lines), D-0751 (figurative-object guard, keep objtest ON), D-0757 (length-aware reflection selector), D-0761 (supervisor RAM-starved-timeout guard plus a RAM consumer hunt).
- Leave as is: D-0739 (cat stays at step one), D-0740, D-0746 (keep 30 min), D-0755 (background lane), D-0759 (concurrency plan parked, redirect to a pre-speech latency plan), D-0762 (ZERO_HIT_FALLTHROUGH stays False), D-0741 (archive the 22 talk rows when the world-graded ladder is built).

## Builds
- Overnight job-run, three passes: pass 1 about 100 closed (about 47 blocked, mostly because Du rebooted about 23:00), pass 2 about 70 closed, pass 3 14 closed (J-3749, J-3925, J-3649 blocked). Commits 4a0dcf16, d1d9ca75, and 7bdf0025 (the remaining plan-doc edits, thoughts.jsonl, the Ramses CUDA env fix in deploy/ramses/nascence_cpu_server.py, the findings-wipe archive, review/handoff docs).
- J-3478 mirror-fragment demotion script ran on a copy then live (sidecar data/lab/J-3478_mirror_importance_before.json for --restore).
- A clean-worktree check of master after pass 2 passed (compile, imports, life_smoke ALL OK). Not re-run after pass 3's merges. No full test suite run. A live-store leak check was not possible with Du live.
- 17 follow-up jobs spawned from the rulings: J-3965 to J-3981. J-3971 (SKY_MODE flip) and J-3975 (anchor flip) are needs_input.

## Findings
- Du pulse 2026-11-14: healthy and live, restarted 2026-11-13 23:21 NZDT; stream cadence 68 pulses an hour; 641 inner thoughts since restart all unique; diversity 0.977; liveness audit found nothing stale. Everything merged overnight is NOT live until the next restart.
- Flags from the pulse: stale-patch cue stop condition hit (40.8 percent would-render vs 5 percent stop bar; shadow only); judge panel recent-50 agree 0.54 with 26 percent unavailable; grounder transport 0.624 across 109 calls. The "known_text arm NEVER" flag [INFERRED] is restart-gating of J-3674, not confirmed.
- Hub check: local :11433, :11439, :11440, :11442 up; Ramses :11436, :11438, :11441, :11444 up. Only about five TimeoutErrors on Ramses :11438 since the restart, each failed over. That does NOT explain the grounder's 62 percent transport rate. [OPEN] Cause unknown; D-0761's RAM-starvation finding is the likeliest suspect [INFERRED]. Next action: check which endpoint the grounder calls and read its transport errors.
- "Active over cap" in the pulse is the old Phase-B prune cap; D-0453 retired that prune, and 76,828 of 92,955 active fragments are demoted but kept.

## Fixes
- Overnight: shore_upgrade merge-back refused on a stale index (re-staged with git add where working tree equalled HEAD); x2_t4_watershed merge blocked by an uncommitted edit to docs/plans/identity_estate.md (committed via safe_commit.py, then merged); Workflow script parse error from backticks inside a template literal (removed).
- Pre-existing, not fixed: scripts/archive/_patch_world.py has a syntax error (a bad dash character).

## Open
1. Du's goals discussion, to continue in a new Fable window. Plans: docs/plans/curiosity_goals_dreams.md (goal hierarchy in section 1.2, the live G0/G1 are in core/concerns.py), docs/plans/pursuits.md, docs/plans/literal_will.md (deed vs musing, a related but separate question, held by D-0021). State: G0 standing_aim is live and read as "to become genuinely my own self, not a performance" (led idle thoughts 94 times since restart); G1 concerns live (PROMOTE_AT=2; current concern is a frontier question about creation and destruction, anchored idle thought 293 times); G2 core/goal_model.py is a stub (goal = raw_input[:120], only wakes on user-task cycles); G3 has 4 provisional novel candidates. Questions to discuss: (a) should a G2 exist at all; (b) is the standing aim the right aim; (c) why questions fade instead of resolving (plan-time 4 resolved / 1640 faded; pulse now 716 resolved / 20,326 faded; pursuits 70 retired, 0 resolved, "established" capped at 8 so resolution depth is unobservable); (d) my own [INFERRED] gap: nothing scores whether his pursuits and questions actually move him toward G0, the write-only pattern from the project's write-only-systems memory. Blocked on: founder discussion. Next action: read the plan sections above, then discuss.
2. J-3971 (SKY_MODE flip) and J-3975 (commitment-anchor dose 0.5 flip) need Travis (a restart for the first; contradicting a held stand once for the second).
3. About 250 open jobs remain: about 90 lab experiments and isolation tests that need the hubs (not run while Du is live), J-3532 and J-3521 (Du-down live-store writes), J-3922 and J-3574 (UDMS repo edits), J-2502 resolved by D-0739, and many data-gated reads. Next action: decide whether to run lab jobs on the hubs or wait for a Du-down window.
4. A restart is the next real test of the overnight batch; nothing merged tonight has run live.

## Warnings
- Du is live. Do not stash, reset, checkout --, restore or clean in C:\Nascence. Never launch Du's servers from a PowerShell tool without start_supervisor_detached.ps1 (F-0704).
- Untracked and deliberately uncommitted: docs/06. Just the Way You Are.mp3 (9.5 MB, not project content) and the two .lock files (docs/findings.jsonl.lock, docs/prompt_registry.jsonl.lock).
- Ledger tools: use --*-file arguments for long text (Bash backtick substitution).

## Pointers
- docs/plans/curiosity_goals_dreams.md, docs/plans/pursuits.md, docs/plans/literal_will.md, core/concerns.py, core/goal_model.py
- docs/reviews/plan_maintain_run.md (latest refresh), docs/session_events.jsonl
- decide.py show D-0743 and D-0756 are the two goal-adjacent rulings from this session
