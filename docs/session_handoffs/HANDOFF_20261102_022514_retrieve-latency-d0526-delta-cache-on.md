# Retrieve() latency over budget: investigation, D-0526 ruled, delta pool cache flipped to "on"

## Session timing
- **Session started:** 2026-10-31 18:12:13 UTC
- **Last message before wrap:** 2026-11-02 02:25:13 UTC
- **Wrapped:** 2026-11-02 02:25:14 UTC

## Summary
Travis pasted a `[retrieve] over latency budget` warning (382 ms vs the 250 ms budget, D-0453 defeater (ii) watch) and asked for it to be investigated, suspecting a link to the ghost weaver / index tuple work. The investigation showed the over-budget share is rising and that the exact remedy (the J-2612 recall-pool delta cache) was already built and waiting on D-0526; Travis ruled it and chose to skip the shadow step, so `_POOL_DELTA_MODE` is now `"on"` (commit 62eefa0c). Du rebooted on 2026-11-02 13:17 NZ local and the first `fast+delta` retrieve was logged at 13:33, so the cache is live but has only one row so far.

## Decisions
- D-0526 RULED by Travis (memory_levels_plan): approve the J-2612 delta cache and flip it STRAIGHT TO "on", skipping the planned shadow stage. The ruling text records the pre-flip evidence, the kill switch (set `_POOL_DELTA_MODE` back to `"off"`, restart-gated) and four defeaters. Defeater (iii) matters most: with no shadow log there is no live delta-vs-old identity record, so recall quality must be watched directly.
- Travis answered an explicit question on this: the choice offered was "shadow first, then on (recommended)" vs "straight to on", and he picked straight to on.

## Builds
- `core/memory/store.py:1324` `_POOL_DELTA_MODE` changed `"off"` to `"on"`, committed alone as 62eefa0c on master (the Nascence tree had many other uncommitted ledger and doc files; only this file was staged). J-2612's code (b9a60d9d) was already an ancestor of HEAD, so no merge was needed. At boot `init_db` creates `memory_pool_changes` plus triggers `trg_pool_chg_ins`, `trg_pool_chg_upd`, `trg_pool_chg_del`; verified present in the live DB after the 11-02 boot, change log at 49 entries.
- Pre-flip verification, run from a scratch git worktree at HEAD plus a read-only `.backup()` copy of the live DB (both deleted afterwards): `scripts/_test_pool_delta.py` ALL PASS, including a 400-write fuzz with 0 divergences and the real 44,992-row pool identical after first load and after 12 rounds of writes. Pool load median 16.6 ms (delta) vs 122.8 ms (fast); trigger overhead 1.1 us per row. The test insists it is run from a worktree, never from C:\Nascence itself.

## Findings
- F-3447 (verified): the fast-path over-budget share rose from 24-28% (10-18..10-20) to 31% (10-30), 46% (10-31) and 42% (11-01) while rows_fetched stayed flat at 44-45k and the median sat at 224-245 ms. Also records the unexplained multi-second outliers (24.7 s on 10-18, 5.0 s on 10-30 14:53 with no boot, 2.4 s on 10-31 11:46 three minutes after a boot). Daily n is only 30-90 so day-to-day moves are noisy; the three-day direction is consistent but not statistically firm.
- `data/nascence.log` only records breaches (90 breach lines == 90 `[retrieve]` lines), so it cannot give a breach rate; `data/retrieve_latency_probe.jsonl` (1,667 rows, logs every call) is the only source of the true rate.
- F-3448 (inferred): the ghost index (`core/ghost_tuples.py` MemoryIndex) is NOT the right lever for the latency budget. The cost is the O(pool) membership re-derivation (F-3353: fetchall 62 ms + argsort 8 + slot loop 22 + PoolRow 13; cosine only 1.4 ms), which the exact-result delta cache removes. A ghost pre-filter would also drop every fragment lacking a `fragment_context` row (63.8% coverage per F-3234; action 0%) and would collide with D-0453 defeater (iii); memory_index size was 0 in the live process (F-3235). The genuine connection runs the other way: the J-2590 `cue_hash` / `slots_filled` ride rows (and J-2618) are what could later show whether a ghost-style candidate set covers what ask() returns. [INFERRED] no lab has measured that overlap.
- First post-boot go-live read (2026-11-02): 1 `fast+delta` row, 1,186 ms, which is the expected full rebuild; 0 `pool delta path failed` warnings and 0 "database is locked" since the 13:17 boot. Pre-flip baseline for comparison: last 60 fast calls p50 251 ms, 53% over, one 15.2 s outlier. Not a verdict on the cache.

## Open
1. J-2863 (urgency 2, ready, gated 40 post-boot `fast+delta` rows): the real go-live read of D-0526. Compare p50/p90/p99 and over-budget share vs the fast path (expect p50 well under 150 ms, over-budget under 10%), grep for fallback warnings and lock errors, confirm the triggers and change-log pruning, and spot-check recall quality since no identity log exists. Next action: run it once the gate opens. A background watcher (task bgwc7o5hy) in this session prints a summary at 40 rows, but it dies if the session closes; J-2863 is the durable reminder.
2. J-2806 (ready, analysis): classify the multi-second retrieve outliers as cold-fill / writer-contention / unexplained. Note `prewarm()` only warms the embedder, not `_EMB_MAT`; if cold fill dominates, a boot-time pool warm needs no flag. Read-only, do not change retrieve().
3. J-2622 (open): reads `data/pool_delta_shadow.jsonl`, which will never exist now that shadow was skipped. Close it as superseded by J-2863; I did not close it. J-2623 (profile the remaining scoring phase only if still near budget) stays open.
4. J-2542 (needs_input, founder): wire the ghost MEMORY index as a pre-filter / retire / leave. F-3448 argues against the pre-filter option for latency purposes.
5. Nothing else of this session is uncommitted in code; the Nascence tree still carries many unrelated modified ledger and doc files from other sessions.

## Warnings
- The first `retrieve()` after any boot with the cache on is a full rebuild (about 1.2 s); do not count it as a regression.
- Defeater (iv) of D-0526: a VACUUM that renumbers rowids fires no trigger. Any VACUUM site must call `store._pool_invalidate()`; none exists in the repo as of 2026-10-31.
- The Co-Authored-By trailer on 62eefa0c names Claude Sonnet 5.5.

## Pointers
- `core/memory/store.py` (`RETRIEVE_LATENCY_BUDGET_MS` :699, `_load_pool_fast` ~1246, delta block ~1299-1545, mode flag :1324)
- `scripts/_test_pool_delta.py` (run from a worktree with `--db <backup copy>`)
- `data/retrieve_latency_probe.jsonl`, `data/nascence.log`
- Decisions D-0453, D-0526; findings F-3353, F-3354, F-3340, F-3447, F-3448; jobs J-2612, J-2863, J-2806, J-2622, J-2623
- `core/ghost_tuples.py`, `docs/session_handoffs/HANDOFF_20261030_200354_tuples-new-light-gpt-thread-weaver.md` (the ghost weaver / tuple context)
