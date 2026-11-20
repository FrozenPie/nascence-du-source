# Technical Positioning Audit

**Status:** 🟡 STAGED (drafted 2026-11-20, not ruled). Origin: a GPT software-perspective review of the Oct 19 System Overview, pasted by the founder 2026-11-20. The corrections brief is `docs/reviews/gpt_technical_review_corrections_2026-11-20.md`.

```plan-state
stage: staged
phase: Phase 0 done (round 1); Phase 1 reliability next, gated on founder ruling and on the J-4426/J-4442 restart
verified: 2026-11-20
gate: founder rules whether to run Phases 1-6; D-NNNN not yet opened
next: founder rules the phase order; verify the reviewer's citations; finish the writer/loader conversion audit (F-5261)
cluster: positioning
```

## Why

A reviewer asked to judge Nascence as software, without the inner-life questions, produced a useful map but
rested on an overview that is a month old and overstates two things: dosed coupling (described as consumers
reading doses; actually publish-side live, one shadow reader, Phase 2 not ruled) and UDMS (described as a
transition-geometry substrate; actually a separate code-analysis tool, with a 5,855x figure that is an index
beating a linear scan). The audit exists to find out how much of the "unusual combination" claim survives
comparison with the best existing work, using today's numbers.

## Rules for this audit

- Four claims stay separate: unusual architecture, novel engineering, research novelty, demonstrated
  technical advantage.
- No prior-art claim without a citation. "I did not find one" is recorded as `inferred`, never `verified`.
- Every number is re-measured at the start of the phase that uses it. Old overview figures are not reused.
- Nothing here touches Du's live stores. Lab work runs in a throwaway worktree (see CLAUDE.md).

## Reviewer's revised ranking (GPT, 2026-11-20, after the corrections brief)

Memory infrastructure first as an engineering result, then dosed coupling as a hypothesis, then temporal
processing, geometry-tuple analysis, world simulation, governance. UDMS removed from the Nascence
contribution list (it is a separate code-analysis tool). Reviewer's priority order for work: persistence
integrity, automated system tests, memory benchmarking, code health, one-consumer coupling experiment,
world-model evaluation, temporal ablation. Its citations (Hearsay-II, LIDA/IDA, Reactive Streams, token
bucket, LongMemEval, LoCoMo, MemoryAgentBench, MemoryArena, and a 2026 paper on LoCoMo judge sensitivity)
are **unchecked leads**, not evidence.

## Phases (reordered 2026-11-20: reliability first)

For each: what Nascence implements, what existing work implements, what differs, whether the difference is
already known, behind / equivalent / ahead / different, what evidence would settle it, and whether anything
is publishable.

0. **Corrections pass.** DONE for round 1 (brief sent, reply received). Output: the reviewer withdrew or
   downgraded 14 claims.
1. **Reliability.** Start from F-5128 / F-5129 / F-5261. The fsync + `.prev` + loud-load fixes (J-4426,
   J-4442, J-4427) are built and restart-gated. Open work, in order: (a) confirm every one of the 19 files'
   writers and loaders was converted; (b) schema and invariant validation beyond non-empty-and-parses;
   (c) checksummed generation manifests for the largest files; (d) cross-process write locking (current
   locks are in-process); (e) crash-injection tests, including a regression test that reproduces the
   zero-filled-file case and asserts no silent empty start; (f) a full-directory restore drill, including
   recovery with a large SQLite WAL present. Release gate: the reviewer's eight criteria.
2. **Test coverage.** 16 files in `tests/` plus 669 `_test*`/`test_*` lab scripts. Decide which lab scripts
   become regression tests; add tests around `_think` and `_run_cycle_impl` before any split (D-0877).
3. **Memory lifecycle.** Compare with Letta, Zep/Graphiti, Mem0, A-Mem. Run LongMemEval, LoCoMo and
   MemoryAgentBench subsets on a copy of the store, in three conditions: native, cold-aware diagnostic
   (record whether gold evidence is active, cold, trail-reachable or inaccessible) and oracle cold access.
   Baselines: full context, no memory, chronological retrieval, plain vector retrieval. Fixed answer model,
   deterministic answer matching where possible, human review of disputed answers, not the internal judge
   panel. Re-measure latency on today's pool (p50/p90/p95/p99, warm and cold, concurrency).
4. **Dosed coupling.** Level 1: descriptive reconstruction of the 258k-row log. Level 2: offline replay of the
   Phase 2 policy against no delivery, unrestricted, fixed-rate, token-bucket and novelty-only baselines.
   Level 3: one consumer (Lane 2 Witness, shadow only), replay-based because live A/B is not possible.
   Pre-register using the existing falsifiers; keep F-3305's null. Report precision, recall, F1, Jaccard,
   base rate, never raw gate agreement. Open problem: "decision quality" needs a ground truth that is not
   the weak judge panel. Do not build the full Phase 2 hub until one reader shows benefit. Prior art to
   cite properly: blackboard, GWT implementations, actor/mailbox, Reactive Streams backpressure, token bucket.
5. **Temporal processing.** Ablate sleep/replay/dream against plain background processing. Separate the
   vectorisation win from the design.
6. **World and action.** Measure prediction accuracy, calibration and long-run consistency. None exists today.
7. **Geometry tuples.** Internal exploratory analysis. Compare with manifold / Koopman / dynamical-systems
   baselines on shared data only if a method claim is wanted. UDMS is out of scope here.

## Out of scope

Anything about Du's inner life. A rewrite. Adding modules.

## Open questions for the founder

- Run Phase 1 before or after the Phase 2 coupling ruling?
- Is publishing a result (a paper or write-up) a goal, or is this only a positioning check?
- Where may lab benchmarks run while Du is up (contention is untested, F-5118)?
