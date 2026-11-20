# J-3312 Offline replay: does a draft-keyed second recall find anything the first missed?

Status: DONE (similarity-only read; judged-relevance step deferred, see section 5). From J-3171 section 5.1 N2 and D-0671.

## 1. Method
- Rows: last 500 of data/training/reflection.jsonl; 381 rows (354 distinct cycle ids) have a recall_served_log.jsonl entry, so the served set is reproducible only for those. The other 119 were skipped (not reconstructed).
- Served set per cycle = fragment ids in recall_served_log (all fragments served, plus founder_recall_ids).
- Second recall = memory_store.retrieve(query_text = raw_input + draft, time_bias "all", default limit 14) run against a COPY of data/memory/nascence.db inside a throwaway worktree of HEAD (live store and live data/ untouched; the guard_path refused all log writes). Climate warp not applied (no per-cycle climate stored), so this is the un-warped query.
- A fragment counts as NEW if its id is not in the served set. The rebind loop (_introspective_rebind_retrieve) has no similarity bar, only "not already present", so bars of 0.5/0.6/0.7/0.8 are reported. For reference the served fragments' own relevance has median 0.42, p75 0.64.
- Leak control: the store is the Nov-15 store, so retrieve also returns fragments written after the cycle (including the cycle's own stored thought). Reported numbers EXCLUDE fragments with timestamp later than the cycle.
- Control: same replay keyed on raw_input alone.

## 2. Results (381 cycles)
| bar | cycles with a new fragment, draft-keyed (leak-filtered) | input-only control | draft-keyed, leak NOT filtered |
|---|---|---|---|
| 0.5 | 68.5% | 65.9% | 100% |
| 0.6 | 40.2% | 37.3% | 100% |
| 0.7 | 22.0% | 18.1% | 97% |
| 0.8 | 5.0% | 5.5% | n/a |
- Median best new similarity: 0.56 filtered (0.90 unfiltered, the unfiltered figure is the cycle's own later-written thought and is invalid).
- Mean new fragments per cycle (unfiltered) 11.6 of 14 returned; the served set overlaps only about 2.4 of the 14.
- New fragments are mostly old: median age 1,069 h; layers episodic 67%, semantic 19%, archive 15%; origins lived, dream, consolidation, active_imagination, session_summary.
- The draft adds little over the input: at bar 0.6, 53% of the draft-keyed new fragments are not found by the input-only query, but the cycle share barely moves (+3 points).

## 3. Against the stop conditions
- Under 5% closes the idea: NOT met (40% at 0.6, 22% at 0.7; only at 0.8 is it 5%).
- At least 15% plus at least 60% judged relevant justifies a live shadow: the 15% half is met at bars up to 0.7; the judged-relevant half was NOT measured (section 5). So no verdict to build or close.
- Caveat on "new": served_log is one cycle's served union (up to about 27 fragments from several paths) while a fresh retrieve returns 14 by tier-mixed slots, so the two sets are different draws from the same pool. A high new share partly reflects that retrieval is a wide pool with many similarly ranked fragments, not that the first recall was deficient. Similarity alone cannot tell a missed relevant fragment from an interchangeable neighbour.

## 4. needs_more_memory prediction
Only 1 of the 381 replayable cycles has needs_more_memory true (58 true rows in the whole 5083-row file, 1 with a served-log entry). AUC is not computable (n_pos = 1). Nothing can be said about whether the flag predicts novelty.

## 5. Judge
The command-r7b witness seat (:11441) lives on Ramses (LAN-HOST); the founder is gaming on it, so it was not used. Local hubs run the qwen family, which the briefing excludes. The 40-row judged sample is therefore NOT done; this is a deterministic similarity-only read. Follow-up job spawned to run the 40-row sample when Ramses is free (the sample would be drawn from J-3312_out.json cycles with a new fragment at 0.6 or above).

## 6. Recommendation
Do not close N2 and do not build the live shadow yet. Run the judged sample first; that single number (judged relevance of new fragments at bar 0.6 or 0.7) decides it. The draft-vs-input control suggests keying on the draft adds only about 3 points of cycle coverage, so if the judge rate is high, the cheaper design is a second retrieval on raw_input alone.
