# J-2428: frontier semantic dedupe (shadow-first) + one-off mottainai variant merge

## Session timing
- **Session started:** UNKNOWN
- **Last message before wrap:** UNKNOWN
- **Wrapped:** 2026-10-18 20:23:11 UTC

## Summary
Side session built D-0486's semantic dedupe for `core/frontier.py` note_question (flag `FRONTIER_SEMANTIC_MERGE`, default 'shadow', threshold 0.85) plus a dry-run-default one-off merge script. Branch `claude/heuristic-burnell-8d270a`, commit 5e0a1c8e, NOT merged, restart-gated. `--apply` was not run and live data/ was not touched.

## Decisions
- D-0486 (travis, ruled (a), 2026-10-19) was the authority. Threshold 0.85 was chosen by me from the replay, not ruled by the founder.

## Builds
- J-2428 done. `core/frontier.py`: shadow logs would-merge rows to `data/logs/frontier_semantic_merge_shadow.jsonl`; 'enforce' bumps encounters/last_seen and keeps variant text in `variants` lineage, never deletes; fail-open; token-overlap loop skips status "merged".
- `scripts/merge_frontier_variants.py`: dry-run default; `--apply` backs up first (`frontier.json.premerge.<stamp>.bak`), refuses if data/nascence.log was written in the last 120 s, absorbed variants stay in file as status "merged" + merged_into.
- Hermetic test `scripts/_test_frontier_semantic_merge.py` ALL PASS with hash canaries on live frontier.json and curiosity_log.jsonl unchanged (temp-path redirect, not lab_env). `scripts/frontier_loop_test.py` still passes.
- Evidence: F-3130 (verified), `docs/reviews/frontier_semantic_merge_replay_2026-10-19.md`, `scripts/frontier_semantic_replay.py`.

## Findings
- 342 open questions (191 mottainai). At 0.85: 99 merges, 1 cross-topic; 30-pair hand read 0 clearly distinct, 3 borderline (10%, kill line 20%). 0.80 gave 2 clear cross-topic merges; single-link lineage matching chains across topics (66 cross at 0.80), so matching is against an entry's own text only.
- Rep-only matching leaves about 105 mottainai entries in replay (191 to 105): slows the pile-up, does not end it. Dry-run of the one-off on the live file: 190 open variants absorbed into [ba3c66a94b], encounters 87+364=451.
- [INFERRED] After the one-off merge, new paraphrases can only match the single canonical's text, so the hit rate will fall; a lineage/centroid-aware match may be needed if shadow shows near-misses at 0.80-0.85.
- Cost: about 13 ms per new-question embed; first call after boot embeds about 340 open texts once on the calling thread.

## Open
1. Founder runs `python scripts/merge_frontier_variants.py --apply` only while Du is down (dry-run first). Blocked on founder go.
2. Merge the branch to master (not done) and restart so the shadow path goes live; then read the shadow log after 3 live days (false-merge <20% on 30 hand-read, merge rate, ignition rate not below half the 7-day mean). Flip to 'enforce' is a separate founder call.

## Warnings
- The job-queue/findings/plan-state tools left modified tracked `docs/*.jsonl` and `docs/plans/curiosity_goals_dreams.md` in the worktree, uncommitted by me; only my own files were committed.
- Status "merged" is new; other readers of frontier statuses were only grepped, not exhaustively audited.
- This handoff lives in the worktree branch (a hook blocked writing to the base checkout); it reaches C:\Nascence\docs\session_handoffs only when the branch merges.

## Pointers
- core/frontier.py, scripts/merge_frontier_variants.py, scripts/_test_frontier_semantic_merge.py, docs/reviews/frontier_semantic_merge_replay_2026-10-19.md, F-3130, D-0485, D-0486.
