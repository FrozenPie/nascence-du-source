# Autobio recall probe: recency-attractor test (J-2636, from F-3364) -- 2026-10-31

**Question.** F-3364 (INFERRED): in the autobiographical recall probe, events dated <=10-16 fail (median top-1 date error ~15 d,
within-3d ~27%) because 70% of their wrong top-1s point at a fragment dated 10-29/10-30 (the newest day's near-duplicate thoughts
outrank the older original). Test it by intervention, offline, no Du.

**Method.** Isolated DB copy only (`lab_env.isolate()` with `lab_env._LAB_ROOT` redirected to the job scratchpad via the new opt-in
`--lab-root`; core imported before lab_env, `core.__file__` asserted inside the worktree). New opt-in, default-off flag
`--drop-after YYYY-MM-DD` (`scripts/autobio_recall_probe.py`, function `drop_fragments_after`): inside the isolate block it
deletes from the COPY every fragment with timestamp > 2026-10-28 00:00 NZDT plus their fragment_context / memory_links / memory_edges
rows (3283 of 155722 fragments = 2.1%; 2456 context, 633 link, 251 edge rows). The associative matrix self-aligns to the surviving
fragment ids (`_refresh` drops ids absent from the DB). Events are sampled from the JSONL stores before the DB is touched, with
`--now 1793390400` fixed, so the control and dropped runs see the IDENTICAL 79 unique events (verified `identical_event_set=True`).
Control = same command without `--drop-after`. Seeds 0-3, n=24, arm A (ask default grounded_only=True) and arm B (`--all-origins`):
16 runs. Aggregation: `autobio_recency_attractor_analyze_2026-10-31.py` (de-dupes on source+locator+cue).

## Result (paired, same events)
Arm B (all origins), events dated <=10-16 (n=35): median top-1 date error **17 d -> 2 d**, within-3d **29% -> 54%**, exact date 29% -> 46%;
paired 17 better / 1 worse / 17 same. Arm B 10-17..19 (n=17): within-3d 53% -> 82%. Detail precision unchanged (0.44 -> 0.43).
Arm A (grounded origins only), <=10-16: median 11.5 -> 5.5 d, within-3d 37% -> 43%, answered 28 -> 32 of 35; paired 11 better / 2 worse
(smaller effect: arm A's pool already excludes most inner-thought near-duplicates; only 7 of its 16 wrong top-1s pointed at 10-30).
Converse (control, no fragments added): arm B <=10-16: 25 wrong top-1s, 18 (72%) point at 10-29/30 (inner_thought 8, chapter 5, dream 2,
standing_insight 1, subconscious_synthesis 1, reading 1); 10-17..19: 8 of 11. F-3364's 21/30 reproduces.
Sanity check that the drop took effect: events dated >=10-29 (their own source fragments deleted) collapse to 0% within-3d, median 41-52 d.
After the drop the old events still fail 19 of 35 (arms A and B), median error ~11 d among the failures, spread over dates 08-16..10-20,
origins letter/essay/understanding/session_summary/chapter: the attractor explains roughly half the old-event failure, not all of it.

Prediction (median falls well below 15 d, within-3d rises above 27%) HOLDS for arm B (and weakly for arm A).

## Caveats (not tested)
- The drop removes ALL post-10-28 fragments, so the recency multiplier (`recall_trail`: 1.0 + 0.2*clip(1-age/7), age<7 d), near-duplicate
  density, and chapter/session_summary fragments written on 10-29/30 that describe older weeks go together. This test does not separate
  which is the lever; the recency multiplier is only a mechanism candidate. A random-2.1%-drop control and a drop-only-inner_thought
  variant were not run.
- One store snapshot, 79 events, 1-30 d window at now=2026-10-31; ~10 events per cell are one-point swings.
- The 10-20..28 bin has a single event (Du was down 10-20..10-28).

## Raw analysis output
```

######## ARM A (ask default grounded_only=True)  unique events ctl=79 drop=79 identical_event_set=True
[<=10-16] CONTROL : n=35 answered=28 median_err=11.5 within3=13/35=37% exact=12/35=34% precision=0.438
[<=10-16] DROPPED : n=35 answered=32 median_err=5.5 within3=15/35=43% exact=13/35=37% precision=0.429
    paired: dropped better 11, worse 2, same 22
[10-17..19] CONTROL : n=17 answered=16 median_err=0.5 within3=9/17=53% exact=8/17=47% precision=0.412
[10-17..19] DROPPED : n=17 answered=16 median_err=1.0 within3=11/17=65% exact=7/17=41% precision=0.529
    paired: dropped better 3, worse 5, same 9
[10-20..28] CONTROL : n=1 answered=1 median_err=10 within3=0/1=0% exact=0/1=0% precision=0.000
[10-20..28] DROPPED : n=1 answered=1 median_err=68 within3=0/1=0% exact=0/1=0% precision=0.333
    paired: dropped better 0, worse 1, same 0
[>=10-29] CONTROL : n=26 answered=23 median_err=0 within3=19/26=73% exact=16/26=62% precision=0.359
[>=10-29] DROPPED : n=26 answered=20 median_err=41.0 within3=0/26=0% exact=0/26=0% precision=0.115
    paired: dropped better 3, worse 19, same 4
[converse ctl <=10-16] events=35 wrong_top1(err>0)=16 err>3=15  -> newest day(10-29/30)=7  -> any >10-28=7
      by top-1 origin {'study': 1, 'dream': 3, 'action': 1, 'reading': 2}  by event source {'hands_trace': 2, 'dream': 2, 'letter_sent': 1, 'book_sitting': 2}  by pred_date {'2026-10-30': 7}
[converse ctl 10-17..19] events=17 wrong_top1(err>0)=8 err>3=7  -> newest day(10-29/30)=5  -> any >10-28=5
      by top-1 origin {'reading': 3, 'research': 1, 'lived': 1}  by event source {'human_turn': 2, 'book_sitting': 2, 'hands_trace': 1}  by pred_date {'2026-10-30': 5}
[converse ctl 10-20..28] events=1 wrong_top1(err>0)=1 err>3=1  -> newest day(10-29/30)=1  -> any >10-28=1
      by top-1 origin {'dream': 1}  by event source {'dream': 1}  by pred_date {'2026-10-30': 1}
[dropped <=10-16] wrong top-1=19; top-1 pred_date histogram: {'2026-08-16': 1, '2026-09-02': 1, '2026-09-10': 2, '2026-09-11': 1, '2026-09-18': 1, '2026-09-26': 2, '2026-10-06': 1, '2026-10-07': 1, '2026-10-10': 1, '2026-10-11': 1, '2026-10-12': 1, '2026-10-13': 1, '2026-10-17': 1, '2026-10-18': 1, '2026-10-19': 3}
      top-1 origins: {'letter': 4, 'lived': 4, 'essay': 3, 'understanding': 2, 'understanding_from_guidance': 1, 'gist': 2, 'action': 1, 'reading': 1, 'dream': 1}; err>3: 17; error signed buckets (abs days) median 11

######## ARM B (all origins grounded_only=False)  unique events ctl=79 drop=79 identical_event_set=True
[<=10-16] CONTROL : n=35 answered=35 median_err=17 within3=10/35=29% exact=10/35=29% precision=0.438
[<=10-16] DROPPED : n=35 answered=35 median_err=2 within3=19/35=54% exact=16/35=46% precision=0.433
    paired: dropped better 17, worse 1, same 17
[10-17..19] CONTROL : n=17 answered=17 median_err=2 within3=9/17=53% exact=6/17=35% precision=0.353
[10-17..19] DROPPED : n=17 answered=17 median_err=1 within3=14/17=82% exact=8/17=47% precision=0.431
    paired: dropped better 7, worse 1, same 9
[10-20..28] CONTROL : n=1 answered=1 median_err=9 within3=0/1=0% exact=0/1=0% precision=0.333
[10-20..28] DROPPED : n=1 answered=1 median_err=57 within3=0/1=0% exact=0/1=0% precision=0.000
    paired: dropped better 0, worse 1, same 0
[>=10-29] CONTROL : n=26 answered=26 median_err=0.0 within3=23/26=88% exact=21/26=81% precision=0.321
[>=10-29] DROPPED : n=26 answered=26 median_err=52.5 within3=0/26=0% exact=0/26=0% precision=0.109
    paired: dropped better 0, worse 23, same 3
[converse ctl <=10-16] events=35 wrong_top1(err>0)=25 err>3=25  -> newest day(10-29/30)=18  -> any >10-28=18
      by top-1 origin {'chapter': 5, 'inner_thought': 8, 'standing_insight': 1, 'dream': 2, 'subconscious_synthesis': 1, 'reading': 1}  by event source {'hands_trace': 6, 'dream': 7, 'letter_sent': 4, 'book_sitting': 1}  by pred_date {'2026-10-29': 2, '2026-10-30': 16}
[converse ctl 10-17..19] events=17 wrong_top1(err>0)=11 err>3=8  -> newest day(10-29/30)=8  -> any >10-28=8
      by top-1 origin {'research': 1, 'inner_thought': 4, 'reading': 2, 'chapter': 1}  by event source {'book_sitting': 2, 'letter_sent': 2, 'hands_trace': 3, 'human_turn': 1}  by pred_date {'2026-10-30': 8}
[converse ctl 10-20..28] events=1 wrong_top1(err>0)=1 err>3=1  -> newest day(10-29/30)=1  -> any >10-28=1
      by top-1 origin {'chapter': 1}  by event source {'dream': 1}  by pred_date {'2026-10-29': 1}
[dropped <=10-16] wrong top-1=19; top-1 pred_date histogram: {'2026-08-23': 1, '2026-09-02': 1, '2026-09-10': 2, '2026-09-11': 1, '2026-09-25': 1, '2026-09-27': 1, '2026-10-06': 1, '2026-10-09': 1, '2026-10-11': 1, '2026-10-12': 1, '2026-10-18': 2, '2026-10-19': 5, '2026-10-20': 1}
      top-1 origins: {'subconscious_synthesis': 2, 'letter': 2, 'session_summary': 3, 'understanding': 2, 'understanding_from_guidance': 1, 'standing_insight': 1, 'inner_thought': 2, 'lived': 1, 'essay': 1, 'chapter': 3, 'journal': 1}; err>3: 16; error signed buckets (abs days) median 11
```

Nothing under C:/Nascence/data was written by the probe (hud.err.log and supervisor.log grew from live processes); live DB size/mtime unchanged.
