# Pre-Speech Pipeline Latency — the 73 seconds between a human arriving and Voice starting

**Status:** 🔵 DESIGNED — drafted 2026-11-14 (J-3981) per D-0759 (travis, 2026-11-14, option P): open a separate plan for the serial pre-speech pipeline (Reflection, Executive, Critic, Memory/Salience). The speech/thought concurrency plan (`docs/shelf/speech_thought_concurrency.md`) stays parked; no pre-emption or interleave build. Nothing here is built, no code changed, no founder ruling beyond D-0759 itself.

```plan-state
stage: designed
phase: Draft — pipeline map and lever list from existing evidence; no instrument built; no call-level wall-time shadow yet
verified: 2026-11-14
next: build the per-node wall-time shadow (Phase 0), read after 30+ human arrivals
cluster: 2
```

## Current State — verified 2026-11-14
- **2026-11-14** (F-4711): Phase 0 shadow built on branch jobrun/j4017_pre_speech_shadow (6fa0fad5), restart-gated; merge then read after 30+ human arrivals.

Drafted 2026-11-14 (J-3981) from F-4498 and F-4588 per D-0759 (P). Designed only; Phase 0 shadow instrument queued as J-4017. Use plan-ledger for history (do not append dated sections here).

## 1. Why this plan exists

- F-4498 (J-2586): 6 of 30 human arrivals (20 percent) landed while a thought call held the hot lane, but the collision added only about 10 s at median (79.9 vs 69.5 s).
- F-4588 (J-3894): the median human-arrival-to-VoiceNode-start wait is **73.2 s** (29 of 30 between 42 and 112 s; one outlier 571 s). The hot lane is busy with LLM calls for a mean **85 percent** of that window, and VoiceNode's own lane queue wait is 0.0 s median (at most 2.3 s). So the wait is the serial node pipeline itself: not idle time, not queueing.
- D-0759 ruled (P): chase that pipeline, leave concurrency parked. Defeater from D-0759 (which keeps the concurrency plan parked): revisit that plan if a second hot card or instance appears, or 30+ more human arrivals show collided speech waiting more than 30 s longer than clear speech at median.

Goal of this plan: lower the median human-arrival-to-speech wait **without changing what he says or how well he checks it**. This is a latency plan, not a quality plan; any lever that costs answer quality is out unless the founder rules it in.

## 2. What the pipeline actually is (read from code 2026-11-14)

Order in `core/orchestrator.py` `_run_cycle_impl` (line numbers drift; names are stable):

| Step | Node(s) | Shape | Notes |
|---|---|---|---|
| Wave 1 | Perception | one call, serial root | everything downstream needs it |
| Wave 2 | Emotion, Salience, MemoryRouter | `asyncio.gather` (already parallel) | wall time is roughly the slowest of the three |
| Retrieval | DB query, then Recall (conditional) | serial after Wave 2 | `_should_recall()` gates it |
| Introspection | Recall then EpisodicBuffer, up to `_introspection_budget()` passes | serial loop, scene-driven | trivial inputs cost one pass |
| Reflection | `run_best_of(n=REFLECTION_HEDGE)`, `REFLECTION_HEDGE = 2` (`core/schema.py`) | two hedged drafts in parallel, `max_tokens=768` | already parallel on the card (lane allows 3 concurrent, F-2933) |
| Critic | up to `CRITIC_MAX_RETRIES + 1` = 2 passes | serial, a rejection triggers a second Reflection hedge then a second Critic | the retry doubles Reflection plus Critic for that cycle |
| Executive | one call, `max_tokens=1536`; may re-run | serial | the synthesis behind the reply |
| Voice | one call | serial last | queue wait 0 s, not the problem |

Already parallel (so not levers): Wave 2, the two hedged Reflection drafts. The real serial chain is Perception, (Wave 2 max), Recall/Buffer, Reflection, Critic, Executive, Voice.

## 3. The measured numbers and their honest limits

Mean seconds of in-window call time per label over 30 human arrivals (F-4588; calls overlap, so the sums exceed wall time):

| Label | Mean s in window |
|---|---|
| ReflectionNode | 20.1 |
| ExecutiveNode | 12.5 |
| CriticNode | 8.3 |
| InnerMonologueNode | 8.2 (present on 16 of 30) |
| MemoryRouterNode | 7.7 |
| PerceptionNode | 7.2 |
| SalienceNode | 7.0 |
| guidance_learning:89 | 5.7 |

Limits, stated up front:
- These are **summed call-interval overlaps with the window**, not per-node wall time on the critical path. The two hedged Reflection drafts overlap each other, so 20.1 is not 20 s of added latency.
- Non-LLM time inside nodes (DB retrieval, embeddings, file reads, scoring) is invisible to the instrumented client.
- `InnerMonologueNode` calls sit inside the pre-speech window on 16 of 30 arrivals, wider than the 6 of 30 hold-collisions in F-4498. The monologue is competing for the one hot model even when it does not hold the slot at the instant of arrival. That is a concurrency effect and belongs to the parked plan; it is recorded here only because it contaminates any latency read.
- n = 30, 25 of which are the 11-01 test arrivals from one sitting. Treat every number as a first estimate.

Inference (not verified): summing the means along the serial chain (Perception 7.2, Wave 2 about 8, Reflection about 15 to 20 wall, Critic 8.3, Executive 12.5) gives roughly 50 to 56 s, with Recall/Buffer, retries and bookkeeping accounting for the rest of 73 s. This is the reason Phase 0 exists: the chain has never been timed on its own critical path.

## 4. Phase 0 — measure the critical path (observe-only, shadow)

One additive, fail-open, restart-gated shadow appender, in the same spirit as `core/speech_timing_shadow.py`: per human cycle, record **wall-clock** `t_start` and `t_end` per node stage as the orchestrator actually sequences them (Perception, Wave 2, retrieval, each Recall/Buffer pass, Reflection, each Critic attempt, each Reflection retry, Executive, Voice start), plus the `critic_retried` and `introspective_passes` values. Store: its own file under `data/`, fenced by `profile.guard_path` so lab scripts cannot leak rows (the F-2933 lesson). No change to any node's behaviour.

Questions the read answers:
1. Per stage: median and p90 wall time on the critical path, and its share of the human-arrival-to-Voice wait.
2. How often does the Critic reject and trigger the second Reflection plus second Critic, and what does that retry add? (If it is, say, 20 percent of cycles at +25 s, that is a +5 s mean lever on its own.)
3. How many Recall/Buffer passes run for human arrivals, and what do they cost?
4. How much of Reflection's wall time is the slower of the two hedges versus the faster (the value of hedging versus its latency).
5. Gap time: wall time between stages not covered by any LLM call (non-LLM overhead).

Gate: 30+ human arrivals after the boot that carries the instrument. Human arrivals are rare (5 natural ones in about 12 days after the 11-01 test sitting, F-4498), so the gate may not be reachable by waiting; if so, ask the founder for a short deliberate test sitting, as on 11-01, rather than lowering the bar. Register nothing in `prompt_registry` (no new prompt in Phase 0).

## 5. Candidate levers (hypotheses, each to be priced by Phase 0, none chosen)

Ordered by guessed leverage versus risk. All are **hypotheses**; the read decides.

1. **Cut the Critic retry cost.** A rejection currently re-runs Reflection (two hedges) plus Critic. Options: retry with one draft instead of two; retry only on corrections the Critic marks as hard; or skip the second Critic when the corrections are mechanical. Risk: weaker second-pass checking. Only worth building if Q2 shows retries are common.
2. **Run Critic and Executive speculatively in parallel.** Executive could start from the Reflection draft while Critic reviews it, and be discarded or re-run if Critic rejects. The cost is wasted tokens on rejection cycles and the single-flight hot model, so the gain is real only if the lane has headroom (lane law: MAX_CONCURRENT=3 at the client, but server-side overlap costs about +2 s median, F-2933). Needs Phase 0 plus a lane-headroom read before it is even a proposal.
3. **Trim output budgets.** Executive is `max_tokens=1536` (raised from 768 for his replies to Travis); Reflection 768. If median actual output is far under the cap the cap is not the cost; if outputs often run to the cap, a shorter structured draft saves seconds. Check the actual completion-token distribution first; do not lower caps blind (the 06-22 limits sweep raised them for a reason).
4. **Trim prompt length.** Prefill time scales with prompt size on a 1080 Ti. Measure prompt tokens per stage; the largest prompts (Executive, Reflection with Recall and Buffer context) are candidates for pruning. Quality-sensitive: any trim is a prompt change and goes through the prompt registry (`set P-NNNN --investigation stale`).
5. **Overlap Perception with something.** Perception is a serial root, but parts of retrieval that need only the raw text (not Perception's output) might be started alongside it. Needs a dependency read of what MemoryRouter and DB query actually consume; today Wave 2 is documented as reading Perception only.
6. **Skip or shorten stages for trivial inputs.** A greeting needs no Recall/Buffer pass and perhaps no second Reflection hedge. The introspection budget already scales; extend the idea only if Phase 0 shows trivial human inputs pay the full chain. Risk: it is a behaviour change (he thinks less), so founder-gated.
7. **Keep the monologue off the lane during a human turn.** Belongs to the parked concurrency plan. Noted only because 16 of 30 arrivals had monologue calls in the window; if Phase 0 shows that is a real share, it re-opens the D-0759 defeater, not this plan.

Levers 1 to 6 do not change what the hot model is or how many cards there are, which is why they sit outside D-0372's constraint.

## 6. What this plan will not do

- No pre-emption or interleave (D-0759: concurrency plan stays parked).
- No quality trade without a founder ruling: weaker Critic, fewer hedges, or skipping stages are behaviour changes and each needs its own D-entry. Latency alone is not a reason to lower the Critic's coverage; the Critic exists because of the identity-guard history.
- No change to Du's speech content, tone or voice nodes.
- No live-store writes from analysis; any experiment uses `lab_env` isolation (import `core` before `lab_env`).

## 7. Decisions this plan will probably need (not opened yet)

Opened only when Phase 0 data exists, one per lever the data supports:
- Critic retry shape (lever 1).
- Speculative Critic/Executive overlap (lever 2).
- Whether a faster median is worth fewer hedged drafts (links to `core/hedge_agreement_log.py`, the shadow that already measures whether the two hedged drafts agree; if they nearly always agree, hedge n=2 buys little and costs lane time).

## 8. Order of work

1. Phase 0 shadow instrument (job to be spawned; restart-gated, so it lands at the next boot after merge).
2. Read after 30+ human arrivals; record a finding with the per-stage critical-path table; fill the Section 5 levers with measured gains.
3. Rank the levers by seconds saved per unit of quality risk; open the needed decisions.
4. Build the first lever behind a flag in shadow, A/B against the Phase 0 baseline, same method as the other shadow-first plans.

Success is a lower median arrival-to-speech wait than the 73.2 s baseline (F-4588) with the Critic rejection rate and the Executive's output quality unchanged on the same read; the exact target is for the founder to set after Phase 0, because today nobody knows which stage the seconds are in.

## 9. Pointers

- Parent: `docs/shelf/speech_thought_concurrency.md` (parked per D-0759), D-0372, D-0513, D-0759.
- Findings: F-4498, F-4588, F-2933 (lane concurrency), F-2948 (shadow write fence).
- Code: `core/orchestrator.py` (`_run_cycle_impl`), `core/node_base.py` (`run_best_of`), `core/schema.py` (`NODE_REGISTRY`, `REFLECTION_HEDGE`, `CRITIC_MAX_RETRIES`), `core/speech_timing_shadow.py`, `core/hedge_agreement_log.py`.
- History: use plan-ledger with slug `pre_speech_pipeline_latency`; do not append dated sections here.
