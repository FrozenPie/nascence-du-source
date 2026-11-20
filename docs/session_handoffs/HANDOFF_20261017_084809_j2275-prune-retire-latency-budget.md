# J-2275 — origin-protected per-kind prune retired; 3,500-row cap replaced by a 250 ms retrieve latency budget (D-0453 a)

## Session timing
- **Session started:** UNKNOWN
- **Last message before wrap:** UNKNOWN
- **Wrapped:** 2026-10-17 08:48:09 UTC

(Side session started by local_0eafd142 to work J-2275; its transcript is stored under the worktree project folder, so `new-path` could not resolve start/last-message times. Real work ran roughly 2026-10-17 09:10-09:35 local.)

## Summary
Worked job J-2275 in worktree `C:\Nascence\.claude\worktrees\j2275-prune-retire-22d6d7`, branch `claude/j2275-prune-retire-22d6d7`, commit d5b10de7 (on master 0246ed45, where the J-2274 gate had been merged). Retired `prune_episodic`'s origin-protected per-kind machinery and the 3,500-row cap in `core/memory/store.py`, replaced it with `RETRIEVE_LATENCY_BUDGET_MS = 250` met by a covering index plus an in-process embedding matrix, verified identical results old-vs-new on a sqlite `.backup()` copy, recorded F-2971/F-2972, queued J-2277, marked J-2275 done. The main session handled merging (memory index records it merged as e4880e4f, restart-gated).

## Builds
- Retire half (F-2971): `KIND_BUDGET_WEIGHT`, `MAX_DEMOTED_PER_KIND_PER_RUN`, the 12-origin + dream<48 h protected expression, the D-0124 PROTECTED-SATURATED branch, the per-kind demotion loop, `PRUNE_PROTECTED_ORIGINS`, `EPISODIC_PRUNE_THRESHOLD` are gone from `core/memory/store.py`. `prune_episodic()` returns 0 or a report-only dry-run dict (`retired: True`, `would_prune`/`would_demote`/`would_delete` 0, historical keys kept empty); `enforce_store_cap()` returns 0; `store_cap_worker` keeps only `dedup_reading_fragments()`. `core/loop_probe.py` no longer imports the threshold. `core/orchestrator.py` comment only (the nightly-sleep call stays, always 0). `scripts/phaseA_report.py` one print string. `memory_levels.commit_gist` is the sole cold writer; the `protected=1` column (D-0134) is untouched.
- Latency half (F-2972): new covering partial index `idx_retrieve_pool_cover` (created in `init_db()`, ~4 s on the copy, so it lands at Du's next boot); `_load_pool_fast` / `_PoolRow` / `_emb_fetch` / `_hydrate_rows` / `_score_tier_vec`. Membership via the covering index in rowid order (ties sort exactly as the legacy `(cold, rowid)` order), embeddings in a float32 matrix keyed by fragment_id and validated by `timestamp` (activity_memory, refinery and the backfill script all bump timestamp when they rewrite an embedding in place), content fetched by id for the ~13 returned rows plus the probe's 5 recent world rows. Legacy `SELECT *` kept for farewell queries (D-0442 needs every row's content), embedder outage, or any error; kill switch `_RETRIEVE_FAST_PATH`. Probe records in `data/retrieve_latency_probe.jsonl` gain `path`, `budget_ms`, `over_budget`; an over-budget call logs a warning at most once per 10 minutes.
- New proving test `scripts/_test_retrieve_fast_pool.py` (J-1842 style, takes `--prefix <pre-J-2275 store.py> --db <.backup() copy> --probe-log data/retrieval_probe_log.jsonl`). On the 41,923-row pool, 60 real query heads: 60/60 identical ids, order, relevance and content. Legacy 581 ms median (433 SQL + 145 score), p90 712, max 780; fast 157 ms median (134 + 21), p90 273, max 314; isolated loader 115 median / 122 p90; first call after process start ~930 ms (one-off matrix load). Live legacy baseline since the 10-16 boot (probe, n=83): total median 538, max 1093.
- `scripts/life_smoke.py` ALL OK; `scripts/smoke_test.py` SMOKE PASS (3 cycles, 141 s, live hot lane; needed `data/identity/axiom.json` copied into the worktree, gitignored). `scripts/_test_store_write_fence.py --prefix <pre-J-2275>`: 36/37, the one failure is its own prefix sanity check expecting a pre-J-1839 copy, unrelated.
- `docs/memory_levels_plan.md`: dated J-2275 note above `## 8. Risks & guards`, plus two design-text corrections (§2 "episodic (3,500...)" and §4.3 normal recall) so the doc no longer describes the per-kind prune as live. `plan_state.py` cannot reach this doc (S-0294), edited by hand.

## Findings
- Even `SELECT fragment_id` over the pool cost ~200 ms on the 1.1 GB DB because every index hit still fetched a table page holding 1.5 KB embedding BLOBs; the covering index cut the membership fetch to 64 ms. The remaining per-call cost is Python-side (42k tuples, dict lookups, 42k `_PoolRow` objects), about 2.7 µs/row.
- [INFERRED] The p90 spread in the test process (273 vs 157 median) came from that process's own heap after the legacy path's 100 MB fetches; the isolated loader was stable at 115/122 ms. Not re-measured in a clean process.
- Headroom is finite: at ~2k new active rows/day the fast-path median climbs ~5 ms/day and crosses 250 ms after roughly 2-3 weeks of continuous uptime. This is D-0453 defeater (ii)'s watch and the reason J-2277 exists.
- UDMS dossier on `core/memory/store.py`: ELEVATED, 19 CONTRACT-layer dependents (orchestrator, inner_monologue_node, memory_levels, schema, ...). None of them referenced the removed names; grep confirmed only `core/loop_probe.py` imported `EPISODIC_PRUNE_THRESHOLD`.

## Open
1. J-2277 (ready, urgency 3): retrieve pool membership without an O(pool) scan per call. Options written into its briefing: trigger-maintained change counter; persistent connection + `PRAGMA data_version`; short-interval refresh with superset semantics (needs a founder call). Next action: after Du's next boot, read `data/retrieve_latency_probe.jsonl` `path=fast` rows for a week and confirm the ~5 ms/day slope before building.
2. D-0453 defeaters (ii) latency above budget and (iii) recall-quality drop against lived/journal/letter are unread until the fast path runs live. Next action: first live read after the boot, compare `over_budget` share and the replayed-origin mix.
3. Rollup gap: `job_queue.py start J-2275` and `job_queue.py add` (J-2277) ran without `--session`, so they are missing from this session's rollup; findings and `done` carry the session id.

## Warnings
- Restart-gated: the live process keeps the legacy path (and the dead prune call) until Du restarts; `init_db()` builds the new index at boot.
- `euclidean_recall.shadow_log` and `emotion_construction` (F-2969) still read `cold=0` newest-600 on purpose: retrieve's POOL definition did not change, only how it is loaded.
- Anyone touching `_load_pool_fast`: the covering index's WHERE and `(embedding IS NOT NULL AND length(embedding) > 0)` expression must stay textually identical to the query or SQLite stops using it; an embedding writer that does not bump `timestamp` would silently serve a stale vector.

## Pointers
- `core/memory/store.py` (constants block ~line 656, fast path block just above `retrieve()`, retired prune block before `enforce_store_cap`)
- `scripts/_test_retrieve_fast_pool.py`
- `docs/memory_levels_plan.md` 2026-10-17 J-2275 note
- Hand-over note: `C:\Users\USER\AppData\Roaming\Claude\side-session-notes\local_0eafd142-1ef3-4587-98af-5ef29c358873\J-2275_prune_retire_handover.md`
- Findings F-2971, F-2972; jobs J-2275 (done), J-2277 (open); decision D-0453
