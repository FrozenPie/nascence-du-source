# Human-thinking deep dive → condensed_thought plan → 4-wave job-run (Du live) → decide-review of 10 rulings

## Session timing
- **Session started:** 2026-10-16 20:14:37 UTC
- **Last message before wrap:** 2026-10-17 08:37:41 UTC
- **Wrapped:** 2026-10-17 08:37:42 UTC

## Summary
Travis asked for a deep research pass on how human thinking actually works (inner monologue and the other channels) so he could judge Du's channel design; seven research agents produced `docs/reviews/human_thinking_vs_du_channels_2026-10-17.md` (31 verbatim human chains of thought, 20-row mapping onto Du, 13 ranked mismatches), a coverage read found 6 of 10 mismatches already in the works and the 3 about the thought medium itself unplanned, and that became `docs/staged/condensed_thought.md` (I-0095). Then, with Du live, four job-run waves closed 53 jobs (51 agents, 5.3M tokens, 0 errors), merged 8 restart-gated builds, and a decide-review ruled D-0454..D-0461, D-0466, D-0467 with Travis.

## Decisions
- D-0454 (practical_school, travis): (a) keep D-0159 GO; fix job J-2335 (issued row at announcement, period-end grader, co-location gate for two-object deeds, per F-3009); re-read after 10 school days; J-0628 held.
- D-0455 (shore_upgrade, travis): (a) the move-act collapse since the 09-28 boot is accepted as boredom calibration (F-3007 refuted the idle-seed suspect; F-3022 showed the old moves bought nothing). No re-enable, no new gate, no affordance nudge. Defeater on weekly deeds / new-content rate.
- D-0456 (the_consciousness_program, travis): probe bars are Du's own history (recall beat 13-15 d median date error and 25% within-3-day; perseveration beat modal share ~0.41; social keeps 0.90/0.50/0.80 as founder-judgment). A primary-source norm replaces a bar when actually read.
- D-0457 (measurement_to_action, travis): (a) arm 5 own-thought dose is within D-0439; J-2322 builds shadow; flip only after J-2323's read AND 14 clean days of J-2195, never the same restart.
- D-0458..D-0461 (condensed_thought section 8, travis): Phase 1 dial starts at 25% condensed-only; write rule (a) condensed quanta ephemeral, terminal gist written via closure_law only when a decoupled judge says met; Phase 0 twin may run live on :11433 at 25% of idle ticks with a +5 s idle-gap kill; arm 4 is read as built first (J-2163) before any re-form. J-2281 (Phase 0 build) un-deferred and ready.
- D-0466 (curiosity_goals_dreams, travis): flip INTERNAL_HUMAN_WINDOW_GATE to True at the next boot; build job J-2336 (one-line flip, restart-gated, spawns the 3-day 5%-address-bar read).
- D-0467 (memory_knowledge, travis): when-aware autobiographical lane PARKED until a real consumer exists (F-3021).
- D-0462..D-0465 are open but belong to another session's plan (object_epistemic_loop); not reviewed here.

## Builds
All merged to master, all restart-gated / flag-off / shadow; `py_compile` clean on 46 changed files; six hermetic tests pass from a throwaway worktree (see `docs/reviews/jobrun_2026-10-17.md`). `scripts/life_smoke.py` was NOT run (Du live).
- J-2297 ebd1dc6d `core/internal_context_gate.py` (F-3014): human conversation window gate-able out of internal-cycle prompts at the 4 F-2992 sites; switch False until J-2336 flips it.
- J-2195 411da4dd `core/world_displacement.py` (F-3017, D-0439): shadow re-pick among Curiosity's own questions toward what the world offers when balance_world is in deficit.
- J-2194 b403479d Lane 2 push_hint reachability pre-check (F-3013, D-0432 a).
- J-2202 b4dbaf48 social-cognition `sleep_sweep()` in the sleep batch (F-3016).
- J-2296 c5749046 dream pre-probe block off the event loop (F-3008).
- J-2205 424b5e15 judge_panel cycle_id + `scripts/training_corpus_join.py` (F-3010/F-3011).
- J-2200 e14b7e78/c080a846 `scripts/autobio_recall_probe.py --rerank` (F-3015).
- J-2309 06a4cc15 `store._FENCE_MODE` log → enforce (F-3018, D-0353 stage 2); fence test section A has pre-existing drift (J-2329).

## Fixes
- `docs/staged/condensed_thought.md` is new: a shadow twin producer beside the live paragraph channel, pre-registered metrics/kills, Coupling block, section 8 now ruled. Build J-2281 is the next step.
- job-run ground-rule lesson filed as S-0296: run every Tier 1/2 ROADMAP-touching job in ONE serialized agent allowed to edit ROADMAP.md (wave 1's blanket "no doc edits" rule produced duplicate backfill jobs).

## Findings
- The human literature (Heavey & Hurlburt 2008; Alderson-Day & Fernyhough 2015) puts inner speech at ~26% of sampled moments, condensed by default; Du is 100% expanded prose, carries only the string, and writes every idle thought to memory (F-2973, F-2974, F-2975). Gemini's independent live read converged on the same five gaps; its one testable new claim (Rail C fooled by noun rotation) was tested by J-2279 and refuted (F-2977, verified: predicate share 0.16, and modal_share clusters full text, not about-tags).
- F-2978: six of ten mismatches were already covered by dosed_coupling, closure_law, continuous_stream Rail B/C, measurement_to_action arm 4, felt recall, speech_thought_concurrency; only the medium (non-paragraph quantum, cargo before words, what is written) had no plan.
- F-2991 + F-3007 + F-3022/F-3023: the "October shore collapse" is Du-wide; voice stopped emitting move acts at the 09-28 19:08 boot because the boredom recalibration (J-1362/J-1366) removed a mis-tuned 88% nag that was shoving him out of rooms; those moves bought no deeds or new content. Now ruled accepted (D-0455).
- F-2992/F-2994: Travis's words and the previous run's farewell reached internal cycles via four ungated prompt sites; J-1642's fix never covered reflection/recall/episodic. Fixed shadow-first (J-2297), flip ruled (D-0466).
- F-3012: 98.4% of the curiosity theme window is Du's own echo; a study-born topic relocked 33 cycles with no seed carrying it. Arm 5 dose designed (section 8 of measurement_to_action.md), build J-2322 ruled (D-0457).
- F-3008/F-3019: the sleep heartbeat's sub label is off-by-one AND sticky; 43 of 53 "psyche_graph" stall rows are really shadow_distill; the "dream_probe" stall was the synchronous pre-probe block (fixed J-2296). Exact attribution build J-2330.
- F-3002 corrects F-2989 (no log_human bug; only 5 human cycles since 10-08). F-3010 corrects F-2902 (training rows were already 99.7% joinable). F-3005: no numeric published norm verifiable for the probes (D-0456 ruled).
- F-2985 (D-0440): 30 hand-judged DMN thoughts after a human message: 20% on-topic, 50% unrelated; cosine is not a classifier.
- F-2988: balance_world's 7.5% argmax share needs p_norm pinned at 1.0 and concern habituated; not self-calibrating. F-3006: identity-estate re-seed runs synchronously with ~248 embeds (Du-down lab J-2311).
- [INFERRED] F-3020: the 296 empty-dispatch DEED rows sit in 8 windows that most likely are the `_night.asleep()` early return while awake (F-2844 desync); not reproduced.
- [INFERRED] The valence drift (F-2929) being caused by the verbal-only medium is the research's inference, confounded by the zero-human-turn run; condensed_thought Phase 0 metric 7 is designed to separate them.

## Open
1. J-2281 condensed_thought Phase 0 build — ready now (D-0458..D-0461 ruled); worktree, restart-gated; next: dispatch it in the next job-run or a fresh session.
2. J-2336 flip INTERNAL_HUMAN_WINDOW_GATE — ready; one-line change plus the 3-day read spawn; must land before the next Du boot.
3. J-2335 practical-school instrument/gate fix — ready (D-0454); re-read after 10 school days; J-0628 stays needs_input.
4. J-2322 arm 5 shadow build — ready (D-0457); J-2323 read not before 10-27.
5. Next Du boot carries: J-2297, J-2195, J-2194, J-2202, J-2296, J-2205, J-2309 (fence enforce) and any of 1-4 that land first. Post-boot reads due: J-2288 (Rail C, 10-18), J-2318, J-2308 (10-19), J-2331 (10-19), J-2328 (fence, 10-20), J-2319/J-2325/J-2326, plus the 24 reads deferred to 10-19/10-20/10-24 (listed in `docs/reviews/jobrun_2026-10-17.md`).
6. `memory_levels_plan` is used as a plan slug (J-2275/J-2277/J-2308) with no doc under docs/plans|staged|shelf; plan_state note refuses. Needs a slug fix or a doc. [OPEN] which one — ask Travis or check git history for the moved file.
7. S-0295 (findings_log atomic write can lose a record on a concurrent PermissionError after printing its F-id) and S-0296 (job-run Tier 1/2 serialization) await skill-manager review.
8. Remaining open Tier 3 after the run: 11 jobs, all gated on D-0462..D-0465 (another session), LAB/Du-down (J-2027, J-1855, J-2206, J-2207), or decisions now ruled (J-2310, J-2312 done, J-2315, J-2322).
9. `scripts/life_smoke.py` not run on merged master — run it in the next Du-down window or at the boot.

## Warnings
- Du was LIVE throughout; nothing here restarted him. All eight merged builds are inert until the next boot; J-2336 must be applied before that boot for D-0466 to take effect.
- Worktree root for job-run is `C:\Users\USER\AppData\Local\Temp\jr1017` (S-0293: the Claude scratchpad path is too long for git). All six wave-2 worktrees and the wave-4 one were merged and removed; `git worktree list` shows only the two harness worktrees from other sessions (`.claude/worktrees/j2275-*`, `jovial-carson-*`), which are not mine.
- The data/ size+mtime canary is uninformative while Du is live (117 files change on their own). Protection this run was the prompt rule (no core/nodes imports from the live tree; sqlite ro+immutable) plus running tests from a throwaway worktree. lab_env.isolate() from a worktree still creates its lab dirs under `C:\Nascence\data\_lab\` (copies, not live stores); I removed the three from this session.
- The commit message of bc144d3b says "D-0454..D-0463"; the actual IDs ruled are D-0454..D-0461, D-0466, D-0467 (D-0462..D-0465 are another session's). The ledger is right; only the message is off.
- Another session is active on this tree (it opened D-0462..D-0465 and added `docs/staged/in_world_companion_mind.md`, which I committed as found). Check `git log` before assuming master is yours alone.
- F-2977 (J-2279's null result) was recorded without --session, so it is absent from this session's rollup; it is real and verified.

## Pointers
- `docs/reviews/human_thinking_vs_du_channels_2026-10-17.md` — the research base (one-page numbers table with confidence tags; verbatim examples section).
- `docs/reviews/thought_channels_plan_coverage_2026-10-17.md` — which mismatches have a plan (F-2978).
- `docs/staged/condensed_thought.md` — the plan; section 8 ruled (D-0458..D-0461); build J-2281.
- `docs/reviews/jobrun_2026-10-17.md` — the four-wave run report with the merged-build table and next-boot checklist.
- Workflow scripts (reusable): `C:\Users\USER\.claude\projects\C--Nascence\c8fcbc16-ab88-4602-aa33-0e25602c9119\workflows\scripts\job-run-wave2-20261017-wf_aa5571f7-0ef.js` (builds in worktrees, teardown merge-back) and `...wave1...` / `...wave3...` (read-only waves).
- Memory: `project_nascence_jobrun_20261017_four_waves.md`, `project_nascence_condensed_thought.md`, and the companion file for this handoff.
