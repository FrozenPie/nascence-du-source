# J-2279: predicate-level perseveration vs Rail C modal_share (null result)

## Session timing
- **Session started:** 2026-10-16 21:10:14 UTC
- **Last message before wrap:** 2026-10-17 08:42:01 UTC
- **Wrapped:** 2026-10-17 08:42:04 UTC

## Summary
Ran J-2279 read-only on scratchpad copies of data/monologue_log.jsonl and data/grounding_injection_shadow.jsonl (668 post-boot DMN thoughts, one boot, 2026-10-16 23:12 to 2026-10-17 10:10 local). The Gemini-derived claim in F-2976 (low modal_share masking a repeated mottainai predicate) is not supported; recorded as F-2977 (verified, null) and J-2279 closed.

## Findings
- F-2977 (verified, null result; links F-2976, J-2278). Rail C modal_share recomputed via topic_perseveration.cluster over rolling 12+1 windows of full thought text reproduces the logged value on 100% of rows (max diff 0.0005). Over 51 non-overlapping 13-thought blocks: mean modal_share 0.436 (30 blocks < 0.4); predicate share (mottainai / weight of words / words carry / hoard) mean 0.160, max 0.538; only 1 of the 30 sub-0.4 blocks had predicate share > 0.5, so the ~50% trigger is not met.
- Rail C modal_share is not an about-tag measure: core/grounding_injection.redundancy clusters the full thought (embedding + quoted-anchor greedy). The literal about-tag modal share is only ~0.12 (about 12.3 distinct tags per 13).
- Body diversity moderate, not collapsed: about-noun-stripped mean pairwise cosine 0.494 per window (0.387-0.609) vs 0.431 for random body pairs; embedder core.memory.store._embed_batch (paraphrase-multilingual-MiniLM-L12-v2). Label and body diversity agree in direction.
- Caveats: one 11-hour boot only; predicate regex is lexical and misses paraphrases; 650 of 668 monologue/shadow rows aligned on ts within 5 s (aligned by tail position).

## Warnings
- F-2977 was recorded without --session, so it will not appear in this session's rollup (only the J-2279 job_done does).
- No code changes, no commits; analysis script an.py lives only in the session scratchpad.

## Pointers
- docs/reviews/human_thinking_vs_du_channels_2026-10-17.md (mismatch #3); core/grounding_injection.py; core/topic_perseveration.py
- Findings: F-2976, F-2977; jobs: J-2279, J-2278
