# Memory router keys: shadow design to make them do work (J-3163, D-0552)

Status: DESIGN ONLY. No Du code, no live store, no restart touched. Written 2026-11-05 by job J-3163.
Plan: memory_knowledge. Prompt row: P-0004 (MemoryRouterNode). Protected base system: `core/memory/store.py retrieve()` stays byte-identical.

## 0. The ruling this implements (quoted, not paraphrased)

D-0552, founder, 2026-11-02: "Do a shadow design to make the keys do work (repurposing review): for example embed the key list and blend it into the query vector in retrieve(), shadow first, judged by a recall-quality metric or a different-family judge, with no live change until a shadow read. Keep the node as it is meanwhile (retrieve() is a protected base system)."

Defeater (his): "Revisit if the shadow read shows no recall-quality gain over the plain embedding across 100 real queries, in which case retire the LLM call (stop calling the node, keep the schema)."

## 1. Recommendation in one paragraph

Build two shadow arms beside the live ranking, in a NEW sibling module called from `Orchestrator._retrieve_memory` (the same pattern as `shadow_compare_lens1..3`), never inside `retrieve()`: **Arm A** blends the embedded key string into the query vector (alpha 0.5, with alpha 0.25 as a dose point), **Arm B** reserves 2 of the 9 slots for the best key-only hits that the plain ranking missed. Drop the "widen the candidate pool" idea outright: it is a no-op here (section 2). Judge the arms on **100 frozen real queries replayed offline against a read-only DB snapshot first** (all inputs are already in `data/training/memory_router.jsonl`, so the verdict does not have to wait weeks for live cycles), with a pairwise blind two-family judge, a **shuffled-keys negative control** and a founder-hand-judged calibration slice. The live shadow arm then confirms on the live distribution. Acceptance bar: the arm wins at least 60 percent of decided pairs (one-sided binomial p < 0.05 on at least 100 decided queries), AND beats the shuffled-keys control by 10 points, AND the judge passes its own sanity check (prefers plain over shuffled keys at least 65 percent). If it fails, D-0552's defeater fires and the call is retired. Whole offline stage costs about 600 judge calls and no hot-lane load.

## 2. What the evidence says (read before designing)

Prior findings (all on file): F-3495 (keys are write-only in effect: `retrieve()` embeds `raw_input + " " + perception.summary` and ranks the pool by cosine; the keys feed only a keyword fallback for rows with no embedding; 0 of 44,955 rows lacked one; time_bias moves at most 1 of 9 slots), F-3496 (junk "Key entities:" line), F-3497 (key quality is one rater's judgement; nothing judges the keys).

New measurements this job (read-only on `nascence.db` with `mode=ro`, same embedder `paraphrase-multilingual-MiniLM-L12-v2`, same TIER_SLOTS 2/3/4 + recency multiplier + seed weight as `retrieve()`, recency-guarantee rows excluded because they are router-independent; scripts `pilot_J-3163.py`, `pilot2_J-3163.py` in the job scratchpad). Sample: 200 real logged queries (100 human, 100 internal) drawn with seed 3163 from the 2,038 current-model rows (2026-08-08 to 2026-11-05), pool 51,111 embedded rows.

1. **"Use the keys to widen the candidate pool before ranking" is vacuous in this store.** `retrieve()` already scores every row of the pool (51,111 today); the "pool" is the whole corpus, there is no top-k pre-filter to widen. Only a re-ranking or a slot reservation can change anything. This drops one of the two mechanisms the briefing floated and is the main reason the design is two arms, not three.
2. **The key vector is a genuinely different view of the query, not a copy.** cosine(query_text, key string) mean 0.658 (human 0.639, internal 0.677). Key-only top-9 overlaps the plain top-9 by only 34 percent (human 26, internal 43). So there is something to gain or lose; the keys are not redundant noise.
3. **Blend dose-response, slots changed out of 9 (mean / queries with zero change):** alpha 0.25: 1.43 / 41 of 200; alpha 0.5: 2.25 / 14; alpha 1.0: 3.15 / 7. Human queries move more than internal (alpha 0.5: 2.46 vs 2.03). Arm B (2 reserved slots): exactly 2 by construction. Per-key RRF fusion (an arm C I tried): 5.37 of 9, far too disruptive, not recommended.
4. **The newly surfaced items are real material, not near-ties.** For arm A at 0.5, the 449 items that enter the top-9 sat at plain rank median 79 (p90 1,044); 37 percent were within the plain top 30. For arm B the median plain rank is 41. So a judge can see a difference; this is also what makes a wrong blend costly.
5. **Origin mix is stable under the blend.** Added vs dropped by origin at alpha 0.5: lived 85 vs 115, standing_insight 82 vs 70, consolidation 77 vs 86, inner_thought 31 vs 33, understanding 38 vs 34. No drift toward the inner-thought loop; the blend is not a monoculture lever. (Still a guard in the bar, section 4.)
6. **The negative control matters.** Keys shuffled across queries change MORE slots than the real keys (3.35 vs 2.25 of 9) and share only 5.3 of 9 slots with the real-key arm. So "the arm moved the results" proves nothing; only a judge that prefers real keys over shuffled keys proves the keys carry signal. The control is therefore mandatory, not optional.

## 3. The two shadow arms and how they are instrumented

### 3.1 Arms

- **Arm A, key-vector blend.** `qv' = normalise(qv + alpha * kv)` where `qv = embed(raw_input + " " + perception.summary)` (exactly what live embeds), `kv = embed(", ".join(episodic_keys + semantic_keys))`, then the SAME climate warp live applies (`bias_vec`, `bias_weight`) so the arm differs from live in exactly one thing. Run alpha 0.5 as the headline arm and alpha 0.25 as a dose point. Rank with the same tier/slot/time_bias/seed-weight logic.
- **Arm B, key slot reservation.** Take the plain 9; find the 2 best-scoring rows under the key-only vector `kv` that are not already in the plain set (non-archive, same eligibility); they replace the 2 lowest-scoring non-archive plain slots. Tests the claim that the keys find memories the query words do not, with the smallest possible footprint (at most 2 of 9 slots, order of the top-1 hit untouched).
- **Control arm N (negative control, logged live too):** Arm A at alpha 0.5 but with the keys of the PREVIOUS cycle (live) or of a shuffled other query (replay). It must lose to plain; if it does not, the judge cannot see quality and the verdict is void.
- **Not an arm:** the router's time_bias. It is already measured as nearly inert (F-3495) and stays as is.

### 3.2 Where it lives (protected-base rule)

`retrieve()` is not edited. Add `core/memory/key_shadow.py` with `shadow_compare_keys(query_text, keys, time_bias, bias_vec, bias_weight, live_ids, cycle_id, input_type)`, called from `Orchestrator._retrieve_memory` in the same `asyncio.to_thread` try/except block pattern as `shadow_compare_lens1/2/3`, right after `memory_store.retrieve`. It reads the already-cached embedding matrix through one small additive accessor in `core/memory/store.py` (taking `_EMB_LOCK`, returning `(matrix_view, id_list, layer, origin, timestamp)` for the current pool), so it needs no extra SQL and no second matrix in RAM. Fenced with `profile.guard_path`; kill switch `KEY_SHADOW_ON = False`; fail-open; restart-gated (Du is live; nothing is written until the next restart). Feeds nothing Du experiences (D-0434); no node reads the log.

### 3.3 What is stored per cycle (`data/key_shadow.jsonl`, one row per retrieve call)

`ts, cycle_id, input_type, time_bias, episodic_keys, semantic_keys, junk_keys_n, cos_query_keys, live_ids (as returned, incl. recency-guarantee rows), plain9 (recomputed ids + scores), A05_9, A025_9, B_9, N_9 (each: id, score, plain_rank), embed_ms, matvec_ms, plain_matches_live (bool)`. Ids only, no content (a judge fetches content by id from the DB).

Validity self-check built in: `plain_matches_live` asserts the arm's own recomputation of the plain set equals the live scored slots (live minus the 5 recency-guarantee rows and minus trail/deep-recall additions). If it is below roughly 95 percent over the first 50 rows, the arms are not comparable to live and the shadow read is invalid until fixed. The one known divergence to watch is the J-2612 pool-delta cache and the farewell-echo skip (`_fw_skip_on` forces the legacy path); farewell cycles should be logged and excluded.

### 3.4 Cost

Measured here on this box: embedding the key string 16 ms median (19 max); one 51k x 384 matvec 1.9 ms. Per cycle: 2 matvecs for A (two alphas) + 1 for B + 1 for N + one embed = roughly 25 to 30 ms on a worker thread, against a retrieve median of about 215 ms; it contends only for `_EMBED_LOCK` (16 ms). Log volume about 2 KB per row. No LLM calls on the live path: the router already runs (77 calls a week, F-3495), the shadow adds none. The offline judged read: 100 queries x 4 comparisons (A05, A025 optional, B, N) x 2 position orders x 2 families, under 1,000 calls to Ramses mixtral and local falcon, a few hours serial; no hot-lane load.

## 4. The quality metric (not the router itself)

### 4.1 Query set

100 fixed real queries, frozen in a file before any arm is scored: 50 human (distinct `raw_input`) and 50 internal, seed 3163, from `data/training/memory_router.jsonl` rows since 2026-08-08 (2,038 rows, 317 human of which 270 distinct raw inputs, so 50 distinct human is available without repeats). The file stores `cycle_id, raw_input, perception.summary, router keys, time_bias`; every input needed to replay is already in that log. 28 human cycles exist in the served log window; human traffic is rare and bursty (26 on 11-01, 1 on 11-02), which is exactly why the primary read is the replay and the live shadow is the confirmation, not the other way round.

### 4.2 Judgement (a different family from the writer, and the keys never shown to the judge)

- **Pairwise, blind, order-swapped.** For each query and arm the judge sees the query (raw_input plus summary) and two item lists labelled X and Y, containing ONLY the items that differ (arm-only vs plain-only), order randomised and run in both orders. Question: "which set would help the entity most in answering or thinking about this?" Verdict per query = win / loss / tie after the order swap (disagreeing orders = tie).
- **Judges:** the established two-family panel from `core/judge_panel.py` (JUDGE_1 mixtral:8x7b on Ramses :11438 and JUDGE_2 falcon3:7b local :11440, granite3.1-moe :11437 tiebreak). All three families differ from qwen3.5, which wrote the keys, and neither arm uses a judge-side model for embeddings. Do NOT route a judge call through the key writer's lane. (Check that falcon :11440 is up when the job runs; the panel logs `how=unavailable` otherwise.)
- **Hand calibration:** 20 of the 100 queries judged by hand by the founder (a short blind sheet, X/Y/tie), to measure judge-vs-human agreement. This is the only founder-time cost and is optional but strongly recommended: without it the whole verdict is LLM-judged-by-LLM. Needs a founder call (section 7).
- **Negative control:** the judge must prefer plain over arm N (shuffled keys) in at least 65 percent of decided pairs. Below that the judge cannot discriminate and no arm result is accepted.

### 4.3 What `data/recall_served_log.jsonl` can and cannot do here (verified)

The log has 179 rows (2026-10-31 11:47 to 2026-11-05 05:17; 151 internal, 28 human), written one per voiced cycle with the SERVED fragment ids (median 18), origin, layer and relevance. It does not record which fragments Du USED; the briefing's wording "which served fragments Du used" overstates it. Every one of the 179 cycle_ids joins to a `voice.jsonl` output, so a use proxy can be derived. I derived the cheapest one (served fragment shares at least one 4-gram with the voice `final` text): **only 10.0 percent of 3,224 served fragments register as used; 57 of 179 cycles use none; 2.9 percent share at least 25 percent of their content words with the output.** By origin the proxy is dominated by `lived` (22.9 percent, because lived Q-and-A fragments are verbatim-echoable) versus understanding 1.3, study 3.1, reading 1.6, gist 0.6, research 0.8. Consequences for the design:

- It is a biased signal that rewards verbatim echo (the self-echo failure mode the farewell-echo work removed, D-0442), so it MUST NOT be the success metric.
- Fragments only the shadow arm would have served are never shown to Du, so no live "used" label can ever exist for them. It cannot evaluate the arms directly.
- It is valuable as (a) a **judge validity check**: on the served set, the judge's relevance score for a fragment should predict the derived use label (AUC at least 0.6), and (b) a **ceiling**: if only about 10 percent of what is served is used, a 2-slot change shifts what Du uses by at most about 0.2 slot per cycle, so any gain will be small and the bar must be about judged relevance, not about behaviour change.
- It is also a live log the shadow row can be joined to by `cycle_id`, which gives each arm's overlap with the actually-served set, but only 28 human rows in 5 days.

### 4.4 Guard metrics (must not regress)

(a) inner_thought share of newly surfaced items not higher than the share of items they replace (pilot: 31 vs 33); (b) lived share of the 9 within 5 points of plain; (c) no query where Arm A removes the top-1 plain hit more than 10 percent of the time (alpha 0.5 normalised blend can demote it; Arm B cannot by construction); (d) `retrieve` latency not moved (shadow is off-thread).

## 5. Acceptance bar, stop condition, cost

- **Accept for a live trial (a separate founder call, not part of this job):** on at least 100 decided queries (ties excluded; if fewer than 100 differ, extend the query set rather than lower the bar), the arm wins at least 60 percent, one-sided exact binomial p below 0.05 (that is 61 of 100), AND its win rate exceeds arm N's win rate by at least 10 points, AND the judge sanity checks pass (N loses to plain at least 65 percent; judge-vs-founder agreement on the 20 hand items at least 75 percent; used-label AUC at least 0.6), AND the guards hold. Report the headline split by human vs internal; if only one stratum passes, the finding says so and the call is scoped to that stratum.
- **Stop (D-0552's defeater fires, retire the call):** the best arm's win rate is below 55 percent on the 100 queries, or is within 5 points of the shuffled control, in the replay AND the live shadow after at least 100 live rows. The retire action is then the founder's own pre-stated one: stop calling MemoryRouterNode, keep the schema and a fixed time_bias default (the 77 hot-lane calls a week go away).
- **Inconclusive:** judge sanity fails or fewer than 100 decided pairs after extending to 150 queries. Do not read it as pass or fail; fix the judge or the set.
- **Time:** replay build plus judged read in one working session; live shadow needs a restart and then about 3 to 4 days to collect 100 internal rows (about 25 to 40 cycles a day lately); the human stratum from live will take weeks and is not required for the verdict.

## 6. What the "Key entities" junk-token leak does to key quality (F-3438/F-3496, checked on the replay sample)

- **The leak mostly does not poison the keys, so it is not a blocker for the blend.** In the 200-query pilot only 3 had any junk token as an actual KEY, and filtering those keys out changed the blend result by 0.02 slots (2.23 vs 2.25 of 9). F-3496 saw the same on the full log (literal token as a key on 17 rows of 4,259). The model largely ignores the junk line.
- **It does matter indirectly, in the direction the design must control for:** the blend inherits whatever the router wrote, and the router's two real defects are (i) the input is framed as a person speaking on every internal cycle (1,991 of 1,991) while Perception's summary is first person, and (ii) 69 percent of logged calls carry at least one junk entity and 63 percent carry nothing else, so on most calls the router sees only raw_input plus summary. Keys from clean inputs are better-posed than keys from the current prompt; any win measured on today's keys is a LOWER bound on what clean keys would do, and any loss could be partly the prompt's fault.
- **Design consequence:** (1) the shadow arm applies a junk-token filter to the keys before embedding (cheap, deterministic, same token list as J-2836, logged in `junk_keys_n`), so a literal `the_entity` key can never pollute the vector; (2) the replay is run in TWO conditions, current logged keys (as the router writes them today) and, once J-2836 has landed and Du has restarted, keys re-generated from the fixed prompt for the same 100 queries; the decision uses the second if it differs, because the repurposed keys should start clean as the briefing asks; (3) J-2836 (framing and entities fix to `nodes/memory_router_node.py`) is therefore a prerequisite for the final read, not for building the instrument. J-2836 itself says "only do this if the router is not retired"; D-0552 keeps it, so it should proceed. It is a prompt change: `prompt_registry.py check` applies there, not here.
- **One constraint on the fix** carried from the world-answers-never-leads law: the J-2836 repair must not add any hint about what to remember to the router prompt.

## 7. Spawned work and founder calls

Jobs spawned from this design (see done-summary for ids): (1) offline replay + judged read harness (lab, read-only), (2) the live shadow module and its orchestrator hook (build, restart-gated), (3) the used-proxy and judge-calibration analysis on the served log. Existing J-2836 stays the clean-keys prerequisite.

Founder calls (needs_input, not decided here):
1. Will Travis hand-judge 20 blind X/Y/tie items for judge calibration (about 15 to 20 minutes)? Without it the read is LLM-vs-LLM with only the shuffled-control and used-label checks as external anchors.
2. Confirm the acceptance bar (60 percent win rate, +10 over the shuffled control, p < 0.05 on 100 queries) as the meaning of D-0552's "no recall-quality gain".
3. After the shadow read, only if it passes: whether a live trial of the winning arm is wanted. That is a change to the protected `retrieve()` input and its own decision; this design deliberately stops short of it.

## 8. Caveats on my own numbers

- The pilot compares top-9 sets, not judged quality; it shows the arms move results and by how much, never that the move is good. Whether it helps is exactly what the judged read is for.
- Replay is against TODAY's pool for historical queries; live cycles have the recency guarantee, trail augmentation and deep-recall on top, which are router-independent and excluded from both arms.
- The pool is now about 51,100 embedded rows versus 44,955 in F-3495; re-checked read-only this job: 51,119 retrieve-eligible rows, 0 without an embedding (my loader used 51,111, the 8-row difference is writes landing between the two reads).
- Use proxy is a 4-gram overlap; it is crude and biased toward echo, as stated in section 4.3.
