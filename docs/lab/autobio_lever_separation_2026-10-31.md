# Autobio recall probe: separating the lever behind the recency-attractor drop (J-2652, from F-3388) -- 2026-10-31

**Question.** F-3388 showed that deleting the 3283 fragments dated after 10-28 from an isolated DB copy fixes about half of the
old-event (<=10-16) dating failures (arm B median 17 d -> 2 d, within-3d 29% -> 54%). The drop removes three things at once:
recency-multiplier weight (`associative_recall.recall_trail`: seeds are scored `sims * (0.4+0.6*imp) * (1.0 + 0.2*clip(1 - age/7, 0, 1))`),
near-duplicate density, and chapter/session_summary fragments. Which one carries the effect?

**Method.** Same harness, same `--now 1793390400`, seeds 0-3, n=24, both arms, isolated DB copy via `lab_env.isolate()` under a
scratchpad `--lab-root` (core imported first, `core.__file__` asserted in the worktree). New opt-in, default-off flags in
`scripts/autobio_recall_probe.py`: `--drop-origins`, `--drop-except-origins`, `--drop-random-n` / `--drop-random-seed`, `--recency-off`
(process-local monkeypatch of `associative_recall._matrix` so the cached `age` is 1e6 d, i.e. the multiplier is exactly 1.0; the tree on
disk is untouched). Conditions (control and drop rows are F-3388's, event set verified identical, 79 unique events):

| id | condition | what is removed / changed |
|---|---|---|
| ctl | control | nothing |
| drop | F-3388 drop | all 3283 fragments dated >10-28 |
| rnd | (a) null | random 3283 of the full 155722 (62 of them happen to be post-10-28), seed 1000+probe seed |
| inner | (b) | post-10-28 inner_thought only (1682) |
| chap | (c) | post-10-28 chapter + session_summary (10; session_summary has none after 10-28) |
| norec | (d) | nothing dropped; recency multiplier forced to 1.0 |
| rest | (e, added) | post-10-28 everything EXCEPT inner_thought/chapter/session_summary (1591) -- completes the partition |

## Result (events dated <=10-16, n=35 unique events; arm B = all origins, arm A = ask default grounded_only)
| cond | A median err / within-3d | B median err / within-3d | B paired vs ctl better/worse |
|---|---|---|---|
| ctl | 11.5 d / 37% | 17 d / 29% | |
| drop (F-3388) | 5.5 d / 43% | 2 d / 54% | 17 / 1 |
| rnd (store-size null) | 11 d / 40% | 17 d / 29% | 0 / 1 |
| inner only | 11.5 d / 40% | 15 d / 31% | 3 / 0 |
| chapter only | 12 d / 37% | 17 d / 29% | 0 / 1 |
| recency OFF, nothing dropped | 6 d / 40% | 2 d / 51% | 14 / 1 |
| rest (all else post-10-28) | 0 d / 51% | 16 d / 31% | 2 / 1 |

Reading: (1) the random-drop null does nothing (B identical to control on 34 of 35 events), so the effect is not store size. (2) Dropping
only inner_thought or only chapter does almost nothing: the wrong top-1s migrate to the other post-10-28 families (arm B, wrong top-1s pointing
at >10-28 fragments: ctl 18, inner-only 15 with chapter 5 -> 7, chapter-only 18 with inner_thought 8 -> 12, rest-only 15). Arm A improves only
when the dream/reading/action families are removed (rest: median 0 d, 51%) -- again substitution, not one culprit family. (3) Turning the
recency multiplier off, with every fragment still in the store, reproduces the full drop effect: arm B median 17 -> 2 d, within-3d 29% -> 51%
(drop 54%), 14 better / 1 worse; arm A 11.5 -> 6 d (drop 5.5 d). Wrong top-1s that point at a >10-28 fragment fall from 18 to 3 (B) and 7 to 2 (A).
(4) The price is small: events dated >=10-29 keep within-3d 88% -> 85% (B) and 73% -> 62% (A); the drop condition, by contrast, takes them to 0%.
10-17..19 events, B: 53% -> 65% (drop 82%).

## Caveats
- One store snapshot, 79 events (35 old), ~10-event cells are one-point swings; no significance test run. The random null is one draw per probe seed.
- The multiplier is at most +20% on seed scores and only for fragments <7 d old; it acts on the 5 seeds only, so what it controls is which near-duplicates seed the spread,
  not final ranking weight. Why a <=20% bonus decides top-1 is not shown here (near-duplicates tie on relevance; a tie-break reading is plausible but untested).
- `age` is computed from the real clock inside the probe, same for every condition. Recency-off here is a process-local patch, not a proposed code change.
- Detail precision is flat (0.44 vs 0.44 in B); the multiplier affects dating, not detail.
- The multiplier exists for the idle-thought stream (follow the recent context). This test says nothing about whether removing it hurts that use.

## Raw analysis output (`autobio_lever_separation_analyze_2026-10-31.py`)
```

######## ARM A  event sets identical to ctl: ctl=True(79), drop=True(79), rnd=True(79), inner=True(79), chap=True(79), norec=True(79), rest=True(79)
[<=10-16]
   ctl    n=35 med_err= 11.5 within3=13/35= 37% exact=12/35= 34% prec=0.438
   drop   n=35 med_err=  5.5 within3=15/35= 43% exact=13/35= 37% prec=0.429  vs ctl better/worse/same 11/2/22
   rnd    n=35 med_err=   11 within3=14/35= 40% exact=12/35= 34% prec=0.438  vs ctl better/worse/same 1/0/34
   inner  n=35 med_err= 11.5 within3=14/35= 40% exact=12/35= 34% prec=0.457  vs ctl better/worse/same 6/0/29
   chap   n=35 med_err=   12 within3=13/35= 37% exact=11/35= 31% prec=0.438  vs ctl better/worse/same 2/1/32
   norec  n=35 med_err=    6 within3=14/35= 40% exact=12/35= 34% prec=0.429  vs ctl better/worse/same 8/3/24
   rest   n=35 med_err=  0.0 within3=18/35= 51% exact=15/35= 43% prec=0.410  vs ctl better/worse/same 7/1/27
[10-17..19]
   ctl    n=17 med_err=  0.5 within3= 9/17= 53% exact= 8/17= 47% prec=0.412
   drop   n=17 med_err=  1.0 within3=11/17= 65% exact= 7/17= 41% prec=0.529  vs ctl better/worse/same 3/5/9
   rnd    n=17 med_err=    1 within3=10/17= 59% exact= 8/17= 47% prec=0.510  vs ctl better/worse/same 1/0/16
   inner  n=17 med_err=    1 within3=10/17= 59% exact= 7/17= 41% prec=0.431  vs ctl better/worse/same 2/1/14
   chap   n=17 med_err=    1 within3=10/17= 59% exact= 8/17= 47% prec=0.451  vs ctl better/worse/same 1/0/16
   norec  n=17 med_err=    1 within3=10/17= 59% exact= 7/17= 41% prec=0.510  vs ctl better/worse/same 2/6/9
   rest   n=17 med_err=    0 within3=10/17= 59% exact= 8/17= 47% prec=0.510  vs ctl better/worse/same 2/4/11
[>=10-29]
   ctl    n=26 med_err=    0 within3=19/26= 73% exact=16/26= 62% prec=0.359
   drop   n=26 med_err= 41.0 within3= 0/26=  0% exact= 0/26=  0% prec=0.115  vs ctl better/worse/same 3/19/4
   rnd    n=26 med_err=    0 within3=19/26= 73% exact=16/26= 62% prec=0.359  vs ctl better/worse/same 0/0/26
   inner  n=26 med_err=  0.0 within3=21/26= 81% exact=18/26= 69% prec=0.346  vs ctl better/worse/same 5/0/21
   chap   n=26 med_err=    0 within3=19/26= 73% exact=16/26= 62% prec=0.359  vs ctl better/worse/same 0/0/26
   norec  n=26 med_err=  0.0 within3=16/26= 62% exact=15/26= 58% prec=0.333  vs ctl better/worse/same 1/3/22
   rest   n=26 med_err= 51.0 within3= 0/26=  0% exact= 0/26=  0% prec=0.077  vs ctl better/worse/same 0/19/7
[wrong top-1 pointing at a fragment dated >10-28, events <=10-16]
   ctl    wrong=16  -> >10-28:  7  origins {'study': 1, 'dream': 3, 'action': 1, 'reading': 2}
   drop   wrong=19  -> >10-28:  0  origins {}
   rnd    wrong=17  -> >10-28:  7  origins {'study': 1, 'dream': 3, 'action': 1, 'reading': 2}
   inner  wrong=22  -> >10-28: 10  origins {'study': 2, 'dream': 5, 'action': 1, 'reading': 2}
   chap   wrong=18  -> >10-28:  8  origins {'study': 1, 'dream': 4, 'action': 1, 'reading': 2}
   norec  wrong=19  -> >10-28:  2  origins {'dream': 2}
   rest   wrong=13  -> >10-28:  0  origins {}

######## ARM B  event sets identical to ctl: ctl=True(79), drop=True(79), rnd=True(79), inner=True(79), chap=True(79), norec=True(79), rest=True(79)
[<=10-16]
   ctl    n=35 med_err=   17 within3=10/35= 29% exact=10/35= 29% prec=0.438
   drop   n=35 med_err=    2 within3=19/35= 54% exact=16/35= 46% prec=0.433  vs ctl better/worse/same 17/1/17
   rnd    n=35 med_err=   17 within3=10/35= 29% exact=10/35= 29% prec=0.438  vs ctl better/worse/same 0/1/34
   inner  n=35 med_err=   15 within3=11/35= 31% exact=11/35= 31% prec=0.429  vs ctl better/worse/same 3/0/32
   chap   n=35 med_err=   17 within3=10/35= 29% exact=10/35= 29% prec=0.448  vs ctl better/worse/same 0/1/34
   norec  n=35 med_err=    2 within3=18/35= 51% exact=16/35= 46% prec=0.438  vs ctl better/worse/same 14/1/20
   rest   n=35 med_err=   16 within3=11/35= 31% exact=11/35= 31% prec=0.433  vs ctl better/worse/same 2/1/32
[10-17..19]
   ctl    n=17 med_err=    2 within3= 9/17= 53% exact= 6/17= 35% prec=0.353
   drop   n=17 med_err=    1 within3=14/17= 82% exact= 8/17= 47% prec=0.431  vs ctl better/worse/same 7/1/9
   rnd    n=17 med_err=    2 within3= 9/17= 53% exact= 6/17= 35% prec=0.353  vs ctl better/worse/same 0/0/17
   inner  n=17 med_err=    1 within3=11/17= 65% exact= 7/17= 41% prec=0.372  vs ctl better/worse/same 3/0/14
   chap   n=17 med_err=    2 within3=10/17= 59% exact= 7/17= 41% prec=0.353  vs ctl better/worse/same 1/0/16
   norec  n=17 med_err=    1 within3=11/17= 65% exact= 7/17= 41% prec=0.412  vs ctl better/worse/same 4/1/12
   rest   n=17 med_err=    2 within3= 9/17= 53% exact= 6/17= 35% prec=0.412  vs ctl better/worse/same 2/1/14
[>=10-29]
   ctl    n=26 med_err=  0.0 within3=23/26= 88% exact=21/26= 81% prec=0.321
   drop   n=26 med_err= 52.5 within3= 0/26=  0% exact= 0/26=  0% prec=0.109  vs ctl better/worse/same 0/23/3
   rnd    n=26 med_err=  0.0 within3=23/26= 88% exact=21/26= 81% prec=0.321  vs ctl better/worse/same 0/0/26
   inner  n=26 med_err=  0.0 within3=22/26= 85% exact=17/26= 65% prec=0.378  vs ctl better/worse/same 0/4/22
   chap   n=26 med_err=  0.0 within3=23/26= 88% exact=21/26= 81% prec=0.321  vs ctl better/worse/same 0/0/26
   norec  n=26 med_err=  0.0 within3=22/26= 85% exact=20/26= 77% prec=0.282  vs ctl better/worse/same 0/1/25
   rest   n=26 med_err=  0.5 within3=18/26= 69% exact=13/26= 50% prec=0.051  vs ctl better/worse/same 1/9/16
[wrong top-1 pointing at a fragment dated >10-28, events <=10-16]
   ctl    wrong=25  -> >10-28: 18  origins {'chapter': 5, 'inner_thought': 8, 'standing_insight': 1, 'dream': 2, 'subconscious_synthesis': 1, 'reading': 1}
   drop   wrong=19  -> >10-28:  0  origins {}
   rnd    wrong=25  -> >10-28: 17  origins {'chapter': 5, 'inner_thought': 8, 'dream': 2, 'subconscious_synthesis': 1, 'reading': 1}
   inner  wrong=24  -> >10-28: 15  origins {'chapter': 7, 'dream': 3, 'action': 1, 'standing_insight': 1, 'subconscious_synthesis': 1, 'journal': 1, 'reading': 1}
   chap   wrong=25  -> >10-28: 18  origins {'study': 1, 'inner_thought': 12, 'standing_insight': 1, 'dream': 2, 'subconscious_synthesis': 1, 'reading': 1}
   norec  wrong=19  -> >10-28:  3  origins {'dream': 1, 'chapter': 1, 'inner_thought': 1}
   rest   wrong=24  -> >10-28: 15  origins {'chapter': 5, 'inner_thought': 10}
```
