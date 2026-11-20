# J-3309: P-0004 key-blend replay, stage 0 of the J-3163 design (PARTIAL: instrument built and run, judged read NOT complete)

Job J-3309, plan memory_knowledge, D-0552. Du down, lab only, read-only on `data/memory/nascence.db` (mode=ro), `lab_env.isolate(db="empty")` around the scoring run, no Du source edited.

## Verdict: INCONCLUSIVE (not pass, not fail)

The judged read did not run to completion. Judge hubs Ramses mixtral :11438 and local falcon3 :11440 were saturated by other labs: a one-line trivial prompt took 222 s and 241 s at the end of the run, and 25 minutes of two parallel judge workers produced 3 pairwise votes per hub. The whole read needs about 1,200 calls. Granite :11437 answers fast (3.8 s trivial) but its Ramses hub stalled the same way once the real prompts started (7 votes in 15 min). So there are NO usable win rates and NO sanity-control result. The 6 + 7 + 6 votes cached are not analysed as results. Design section 5 says judge sanity failure or under 100 decided pairs is inconclusive, and that is where this stands.

## What was built and is reusable (all under `docs/lab/J-3309/`)

- `freeze_J-3309.py` -> `frozen_queries_J-3309.json`: 100 queries (50 human distinct raw_input, 50 internal), seed 3163, rows since 2026-08-08 from `data/training/memory_router.jsonl`, frozen before any arm was scored (sha1 prefix bc6709e6ba0a, all 100 have a summary).
- `score_arms_J-3309.py` -> `arms_J-3309.json`: arms plain, A05 (alpha 0.5), A025, B (2 reserved key-only slots), N (A05 with keys deranged across queries, seed 3163). Same tier slots 2/3/4 with spare cascade, recency and seed-weight logic as `retrieve()`, recency-guarantee rows excluded, junk keys filtered with `MemoryRouterNode._JUNK_ENTITY_TOKENS` (J-2836 list). Pool 51k eligible rows, 0 without an embedding. Climate warp is NOT applied (bias_vec is not logged), identical across arms. The J-3163 pilot script was not on disk this run, so the logic was rebuilt from store.py, not from the pilot.
- `judge_J-3309.py` (resumable cache per hub, arm-only vs plain-only items, both orders), `analyze_J-3309.py` (panel verdicts, one-sided exact binomial), `guards_J-3309.py`, `make_sheet_J-3309.py`.
- Blind sheet for the founder: `docs/reviews/J-3309_blind_sheet.md` (20 items, 10 A05 and 10 B, 5 human + 5 internal each, X/Y order randomised); key in `docs/lab/J-3309/sheet_key_J-3309.json`. Judge-vs-human agreement is pending his answers.

## Structural results (no LLM, on the frozen 100)

Slots changed out of 9 (mean; queries with zero change): A05 2.15 (7), A025 1.35 (20), B 2.00 (0), N 3.42 (0). This matches the J-3163 pilot (2.25 / 1.43 / 2 / 3.35). Human vs internal for A05: 2.36 vs 1.94. Shuffled keys move MORE than real keys, so movement alone proves nothing and the control is needed.

Guards (design 4.4):
- (c) top-1 plain hit removed: 0 of 100 for every arm. Passes.
- (a) inner_thought share of newly surfaced items vs the items replaced: A05 6 percent vs 4, A025 4 vs 4, N 4 vs 3, but **arm B 18 percent vs 1 percent**. Arm B's key-only slots pull the inner-thought loop in; this is a guard failure in the structure, independent of any judge, and a reason to treat B with suspicion even if a judge likes it.
- (b) lived share: A05 adds 31 lived items and drops 59 (of 215 added), so lived share falls by about 13 points of the changed slots; B adds 36 and drops 6. Per-query lived share of all 9 was not computed; the change-set figures only show the direction.

## What is not done

Steps 3 (judge read) and 5 (win rates, bar check) of the briefing. Not run: the second condition (keys regenerated from the J-2836 prompt), because J-2836 landed 2026-11-16 05:05 and Du has not restarted since. Not done: granite tiebreak on disagreements, `data/recall_served_log.jsonl` use-AUC check.

## To finish

Re-run when the hubs are quiet (check with a one-line probe first; under 20 s per call is workable):
`python docs/lab/J-3309/judge_J-3309.py j1 N,A05,B`, same for `j2`, then `analyze_J-3309.py`. The caches resume. Judge N and A05 on the 50-human stratum first if time is short. About 600 calls per hub. Reducing item text further (now 280 chars) will not help much; the delay is hub queueing, not prompt size.
