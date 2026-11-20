# Autobio recall probe: matched-age restart-fragility read (J-2637, from F-3364) -- 2026-10-31

**Question.** Does the probe's recall quality depend on whether the event was before or during the current boot, once age is held fixed?
J-2199 (F-3364) could not tell: the 3-10 d age bin was empty, so boot and age were perfectly confounded.

**Precondition check (honest).** The briefing's literal precondition (a populated 3-10 d bin on BOTH sides of a boot) is NOT met and cannot be
met by choosing a different fixed --now. Event dates in the stores are 10-04..10-20 and 10-29/30 only (Du was down 10-20..10-28). With now = 10-31
the 3-10 d bin (dates 10-21..10-28) is empty. Moving --now earlier cannot help: an event during the 10-29 boot cannot be older than the
boot, and a now late enough for 10-29 events to be 3 d old (>= 11-01) pushes every before-boot event past 12 d. The 10-29 boot has been dead since
10-30 19:44, so no new 3-10 d during-boot events will exist until a new boot has run for days. What CAN be read now: the
earlier boots inside the 10-04..10-19 window (boot log: 10-09 08:36, 10-16 22:37, 10-18 19:06/19:37, 10-19 08:50/10:05/22:09) used as the
boot split at fixed now = 1793390400 (2026-10-31 09:00 NZDT), which puts events of both phases in the 10-20 d age bin.

**Method.** Isolated DB copy via the probe's own `lab_env.isolate()` (`--lab-root` under the job scratchpad; core imported before lab_env,
core.__file__ asserted under the worktree). No code change: the existing probe with `--now 1793390400 --boot-ts T`, n=24, seeds 0-3, arm A (default) and
arm B (`--all-origins`), for T = 1792143440 (10-16 22:37:20, long-ish quiet boot) and T = 1791488217 (10-09 08:36:57).
16 runs; `autobio_matched_age_analyze_2026-10-31.py` de-dupes on source+locator+cue and bins age_days (0-3, 3-10, 10-20, 20-30) x phase.
Phase is recomputed against T. The probe stratifies sampling across T, so before/during counts are roughly balanced per source pool, not per age cell.

## Result: boot 10-16 22:37, the only shared age bin is 10-20 d
| arm | cell (age 10-20 d) | n | median err (d) | within-3d | precision | wrong top-1 -> 10-29/30 |
|---|---|---|---|---|---|---|
| A | before_boot (events 10-11..10-16) | 20 | 15 | 6/20 = 30% | 0.32 | 7 of 12 wrong |
| A | during_boot (10-16..10-21) | 36 | 5 | 15/36 = 42% | 0.34 | 12 of 18 wrong |
| B | before_boot | 20 | 16.5 | 3/20 = 15% | 0.37 | 15 of 17 wrong |
| B | during_boot | 36 | 11 | 13/36 = 36% | 0.34 | 22 of 25 wrong |

Fisher exact on within-3d: arm B p = 0.13, arm A p = 0.57. Direction favours "during" in both arms; not significant. Arm B: wrong answers
are equally attractor-dominated in both phases (88% vs 88% point at 10-29/30), so the phase gap is in how OFTEN the old event is wrong
(85% vs 69% wrong), not in where the wrong answers point. Other cells: age 0-3 d during n=3 (3/3 within 3 d); age 20-30 d before n=19 (A 26%, B 32% within-3d)
with no during counterpart; age 3-10 d empty on both sides.

## Result: boot 10-09 08:36, the shared bin is 20-30 d but during n=6
Age 20-30 d: before_boot (10-04..10-08) n=34, A median 13 d, within-3d 18%; B median 23 d, 21%. During_boot (10-09..10-11) n=6, A median 0 d, 33%;
B median 9.5 d, 50%. Fisher within-3d: A p = 0.58, B p = 0.15. The 10-20 bin is all during_boot (n=33), so no contrast there.

## Reading (what is and is not shown)
- A weak, consistent direction: events from after the later boot are recalled better than those from before it at coarse-matched age
  (4 of 4 arm x boot comparisons favour during; none significant at n=6-36).
- NOT a clean matched-age test. Inside the 10-20 d bin the before_boot events are older (14.5-20 d, mean ~17) than the during_boot events
  (10-14.5 d, mean ~12), and before_boot is exactly dates 10-11..10-16 while during_boot is dominated by 10-17..10-19 (33 of 36 events). So boot,
  within-bin age and the specific dates (10-17..19 are the best-recalled days in J-2636's tables too) are still tangled; the finer age
  split has no overlap between phases at all (before >= 14.5 d, during <= 14.5 d).
- The recency attractor (F-3364, tested by intervention in F-3388) is the dominant error in every cell and equal across phases, so it does not
  explain the phase gap on its own; it is a separate effect.
- Verdict: restart fragility is neither supported nor ruled out. A real matched-age test needs a boot that runs several days and leaves
  events 3-10 d old on both sides (a successor job is gated on that).

## Raw analysis output
```

#### boot 2026-10-16T22:37 arm A: unique events 78
  age 0-3   before_boot : n=0
  age 0-3   during_boot : n=3 med_err=1 within3=3/3=100% prec=0.44 wrong=2 ->10-29/30=2
  age 3-10  before_boot : n=0
  age 3-10  during_boot : n=0
  age 10-20 before_boot : n=20 med_err=15 within3=6/20=30% prec=0.32 wrong=12 ->10-29/30=7
  age 10-20 during_boot : n=36 med_err=5 within3=15/36=42% prec=0.34 wrong=18 ->10-29/30=12
  age 20-30 before_boot : n=19 med_err=13.0 within3=5/19=26% prec=0.35 wrong=9 ->10-29/30=4
  age 20-30 during_boot : n=0
  ALL before_boot: n=39 med_err=15 within3=11/39=28% prec=0.33 wrong=21 ->10-29/30=11
  ALL during_boot: n=39 med_err=2.0 within3=18/39=46% prec=0.35 wrong=20 ->10-29/30=14
  event dates: {'b:2026-10-04': 3, 'b:2026-10-05': 2, 'b:2026-10-06': 2, 'b:2026-10-07': 1, 'b:2026-10-08': 4, 'b:2026-10-09': 3, 'b:2026-10-10': 1, 'b:2026-10-11': 7, 'b:2026-10-12': 5, 'b:2026-10-13': 5, 'b:2026-10-14': 2, 'b:2026-10-15': 3, 'b:2026-10-16': 1, 'd:2026-10-16': 1, 'd:2026-10-17': 11, 'd:2026-10-18': 8, 'd:2026-10-19': 14, 'd:2026-10-20': 2, 'd:2026-10-29': 2, 'd:2026-10-30': 1}

#### boot 2026-10-16T22:37 arm B: unique events 78
  age 0-3   before_boot : n=0
  age 0-3   during_boot : n=3 med_err=0 within3=3/3=100% prec=0.44 wrong=1 ->10-29/30=1
  age 3-10  before_boot : n=0
  age 3-10  during_boot : n=0
  age 10-20 before_boot : n=20 med_err=16.5 within3=3/20=15% prec=0.37 wrong=17 ->10-29/30=15
  age 10-20 during_boot : n=36 med_err=11.0 within3=13/36=36% prec=0.34 wrong=25 ->10-29/30=22
  age 20-30 before_boot : n=19 med_err=19 within3=6/19=32% prec=0.30 wrong=13 ->10-29/30=8
  age 20-30 during_boot : n=0
  ALL before_boot: n=39 med_err=17 within3=9/39=23% prec=0.33 wrong=30 ->10-29/30=23
  ALL during_boot: n=39 med_err=11 within3=16/39=41% prec=0.35 wrong=26 ->10-29/30=23
  event dates: {'b:2026-10-04': 3, 'b:2026-10-05': 2, 'b:2026-10-06': 2, 'b:2026-10-07': 1, 'b:2026-10-08': 4, 'b:2026-10-09': 3, 'b:2026-10-10': 1, 'b:2026-10-11': 7, 'b:2026-10-12': 5, 'b:2026-10-13': 5, 'b:2026-10-14': 2, 'b:2026-10-15': 3, 'b:2026-10-16': 1, 'd:2026-10-16': 1, 'd:2026-10-17': 11, 'd:2026-10-18': 8, 'd:2026-10-19': 14, 'd:2026-10-20': 2, 'd:2026-10-29': 2, 'd:2026-10-30': 1}

#### boot 2026-10-09T08:36 arm A: unique events 74
  age 0-3   before_boot : n=0
  age 0-3   during_boot : n=1 med_err=1 within3=1/1=100% prec=0.33 wrong=1 ->10-29/30=1
  age 3-10  before_boot : n=0
  age 3-10  during_boot : n=0
  age 10-20 before_boot : n=0
  age 10-20 during_boot : n=33 med_err=7 within3=14/33=42% prec=0.40 wrong=17 ->10-29/30=10
  age 20-30 before_boot : n=34 med_err=13 within3=6/34=18% prec=0.22 wrong=23 ->10-29/30=9
  age 20-30 during_boot : n=6 med_err=0 within3=2/6=33% prec=0.22 wrong=1 ->10-29/30=1
  ALL before_boot: n=34 med_err=13 within3=6/34=18% prec=0.22 wrong=23 ->10-29/30=9
  ALL during_boot: n=40 med_err=1 within3=17/40=42% prec=0.38 wrong=19 ->10-29/30=12
  event dates: {'b:2026-10-04': 5, 'b:2026-10-05': 6, 'b:2026-10-06': 5, 'b:2026-10-07': 8, 'b:2026-10-08': 10, 'd:2026-10-09': 2, 'd:2026-10-10': 1, 'd:2026-10-11': 7, 'd:2026-10-12': 3, 'd:2026-10-13': 4, 'd:2026-10-15': 1, 'd:2026-10-16': 3, 'd:2026-10-17': 5, 'd:2026-10-18': 4, 'd:2026-10-19': 8, 'd:2026-10-20': 1, 'd:2026-10-29': 1}

#### boot 2026-10-09T08:36 arm B: unique events 74
  age 0-3   before_boot : n=0
  age 0-3   during_boot : n=1 med_err=1 within3=1/1=100% prec=0.33 wrong=1 ->10-29/30=1
  age 3-10  before_boot : n=0
  age 3-10  during_boot : n=0
  age 10-20 before_boot : n=0
  age 10-20 during_boot : n=33 med_err=12 within3=10/33=30% prec=0.42 wrong=25 ->10-29/30=21
  age 20-30 before_boot : n=34 med_err=23 within3=7/34=21% prec=0.24 wrong=27 ->10-29/30=19
  age 20-30 during_boot : n=6 med_err=9.5 within3=3/6=50% prec=0.22 wrong=3 ->10-29/30=3
  ALL before_boot: n=34 med_err=23 within3=7/34=21% prec=0.24 wrong=27 ->10-29/30=19
  ALL during_boot: n=40 med_err=12.0 within3=14/40=35% prec=0.39 wrong=29 ->10-29/30=25
  event dates: {'b:2026-10-04': 5, 'b:2026-10-05': 6, 'b:2026-10-06': 5, 'b:2026-10-07': 8, 'b:2026-10-08': 10, 'd:2026-10-09': 2, 'd:2026-10-10': 1, 'd:2026-10-11': 7, 'd:2026-10-12': 3, 'd:2026-10-13': 4, 'd:2026-10-15': 1, 'd:2026-10-16': 3, 'd:2026-10-17': 5, 'd:2026-10-18': 4, 'd:2026-10-19': 8, 'd:2026-10-20': 1, 'd:2026-10-29': 1}
```
