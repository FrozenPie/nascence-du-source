# Job-run wave 2026-10-17 (12 jobs): condensed_thought Phase 0, Practical School fixes, night stall attribution, probe docs

## Session timing
- **Session started:** 2026-10-17 09:01:06 UTC
- **Last message before wrap:** 2026-10-17 09:40:33 UTC
- **Wrapped:** 2026-10-17 09:40:34 UTC

## Summary
Travis asked for a new /job-run with the right models per job. plan-maintain showed 141 open jobs, 116 date-deferred, 16 ready; I dispatched 12 as one Workflow (wf_8c47f952-02e, 14 agents, 0 failures, ~1.54M subagent tokens, ~31 min): Haiku for backfill J-2338, Sonnet for hygiene J-2337 and teardown, Opus for 10 plan-work jobs in 4 worktree-isolated chains. All three file-editing branches are merged to master.

## Decisions
- No new rulings by Claude. D-0456, D-0457, D-0466 were already ruled by travis; jobs only applied them.
- D-0468 OPENED (founder-only): place a second twine ball in the study? (from J-2315).

## Builds
All restart-gated; nothing is live until Du restarts. Evidence is in the findings named.
- J-2281: condensed_thought Phase 0 (core/condensed_thought.py, one hook in nodes/inner_monologue_node.py, offline judge scripts/judge_condensed_thought.py, scripts/read_condensed_thought.py), ships with CONDENSED_TWIN=False. F-3028. Spawned J-2341 (7-day read, not before 2026-10-24) and J-2342 (founder: flip the flag at that boot).
- J-2315 / J-2332 / J-2335: Practical School issued rows, period-end grader, generalized co-location gate (core/practical_lesson.py), and SKIP-asleep / SKIP-not-live / ERR-* rows in core/dispatch.py. F-3030; follow-up J-2344 (not before 2026-10-26); J-2317 already covers the re-read.
- J-2330: exact night stall attribution in core/sleep_phase0.py (observe-only, STALL_EXACT_ATTRIBUTION). F-3033; successor J-2346.
- J-2322: arm 5 curiosity theme-dose shadow (core/theme_dose.py, SELF_THEME_DOSE=None). Per D-0457 the flag flip must never share a restart with J-2195.
- J-2333: noisy-anchor sweep in scripts/autobio_recall_probe.py (--rerank-noisy-anchor). F-3029; spawned J-2343.
- J-2310: D-0456 bars written into three probe docstrings, unsourced human norms removed.
- J-2336: INTERNAL_HUMAN_WINDOW_GATE = True in core/internal_context_gate.py (D-0466). F-3025; spawned J-2340.
- J-2329: scripts/_test_store_write_fence.py section A gets a documented KNOWN_RETURN_DRIFT table (F-3018).
- J-2338: object_epistemic_loop ROADMAP bullet (badge 🔵 DESIGNED, d94f4992) + memory file project_nascence_object_epistemic_loop.md.
- Merge commits: fd225359 (inner_monologue_chain), 905fea33 (probe_docs_chain), 144b14e0 (gate_flip). J-2329 and J-2338 were committed straight to master.

## Findings
- J-2337 needed no edit: in_world_companion_mind already has the correct 💤 badge; plan-index's stage-mismatch report reads the enclosing section heading instead of the bullet. Filed S-0297 (without --session).
- Teardown first failed: merge-back refused because docs/ROADMAP.md had a stale staged deletion of J-2338's bullet (index behind HEAD after safe_commit, the F-2570 pattern). Fixed with `git add docs/ROADMAP.md` (working tree already equalled HEAD), then all three merge-backs succeeded. [INFERRED] cause is safe_commit.py leaving the index stale.
- J-2338's agent launched plan_maintain.py by accident and stopped it after ~1 min, so plan-index/ledger reports may be partly written. [OPEN] check with a clean /plan-maintain.
- Per-agent --session values were job ids, so the session rollup for this session shows only T-0095; use the job ids for attribution.

## Open
1. D-0468 (twine ball): founder call via /decide-review.
2. J-2342: turn on CONDENSED_TWIN at a boot, founder call.
3. Restart Du to make all of the above live; J-2336's gate flip and the J-2322 flag rule (D-0457 / J-2195) are the sequencing constraints.
4. Lab jobs skipped because Du is live: J-2027, J-2206, J-2207, J-1855 (J-1855 also has an active Hold D-0083/D-0088). Run when Du is down.
5. Next job-run plan: 1 hygiene + 5 plan-work ready, 121 deferred, 8 needs-input.
6. Uncommitted ledger/plan-doc edits from agents remain in the shared tree; commit by explicit path.

## Warnings
- Do not git stash/reset/checkout/restore/clean in C:\Nascence. Check `git status` for a `D ` or staged deletion you did not make before any bare commit.
- Worktree root for this wave was C:\Users\USER\AppData\Local\Temp\jr1017b (worktrees removed by merge-back).

## Pointers
- Workflow script: C:\Users\USER\.claude\projects\C--Nascence\0ab543b7-684a-4ce0-9734-e59e758e88ae\workflows\scripts\job-run-1017b-wf_8c47f952-02e.js; journal in the subagents\workflows\wf_8c47f952-02e folder.
- docs/staged/condensed_thought.md, docs/plans/practical_school.md, docs/staged/dream_overhaul.md.
