# J-3967 / D-0744: vitality mind-axis scale S replay (percentile x window)

Script: `scripts/vitality_scale_replay_J3967.py` (read-only; imports `core.homeostasis.self_calibrated_scale` and `mind_axis`).
Data: `data/sleep_pressure_log.jsonl` read in place, 1,183 real fires in total (reason pressure | max_wake_ceiling), 366 at or after the shadow start 2026-10-16 09:37 UTC (the 340 of F-4456 is the same set, counted slightly differently at the boundary and by the log's current length).
Method: for each scored fire, S = percentile of P-at-fire over the window of fires ending at (and including) that fire; vit_mind = exp(-ln2 P/S) at the fire's own P. Clause 5 (D-0398): share of fires reading vit_mind > 0.7 must be under 1/3. "recent" = fires since 2026-11-09 11:00 UTC (the drifted window, 88 fires). Baseline reproduces F-4456: p60/w30 reads 44.3% recent (F-4456: 50% over the slightly different 62-fire window since 11-10) and 20.8% overall (F-4456: 27.6% on the logged rows, which used the live S as it stood at each row).
Columns: all%/recent% = share of fires reading > 0.7; night%/day% by the log's dark flag; recNight% = night fires in the recent window; S = scale min/median/max; swing7d = largest max/min of S inside any 7-day span (whole span, then recent only); awake<.1 / >.9 = share of awake sp rows reading under 0.1 / over 0.9 at the S then in force; n-d gap = mean vit_mind of night fires minus day fires.

```
fires total 1183, scored 366
pct    win  all%  recent%(n) night% day%  recNight% S[min/med/max]  swing7d(recent) awake<.1 >.9   n-d gap  C5all C5rec swingOK
0.6     30  20.8  44.3( 88)  26.1   1.3  69.6   10.1/  16.4/ 104.7  10.01( 9.81)   21.3  10.8   0.316  Y     N     N  <-baseline
0.5     30  10.1  25.0( 88)  12.5   1.3  39.3   10.1/  15.5/ 100.9   9.70( 9.63)   27.3   5.3   0.349  Y     Y     N
0.4     30   4.9  13.6( 88)   5.9   1.3  21.4   10.1/  11.2/ 100.6   9.78( 9.78)   31.7   3.3   0.351  Y     Y     N
0.3     30   3.6  10.2( 88)   4.2   1.3  16.1   10.0/  10.6/ 100.3   9.81( 9.81)   33.0   2.8   0.348  Y     Y     N
0.2     30   1.1   3.4( 88)   1.0   1.3   5.4   10.0/  10.3/  33.5   3.32( 3.32)   35.9   1.5   0.379  Y     Y     N
0.6     20  23.5  31.8( 88)  29.6   1.3  50.0   10.1/  17.8/ 105.0  10.04(10.02)   24.8  10.0   0.348  Y     Y     N
0.5     20  18.9  26.1( 88)  23.7   1.3  41.1   10.1/  15.5/ 104.9  10.09(10.07)   27.3   8.1   0.353  Y     Y     N
0.4     20  10.7  21.6( 88)  13.2   1.3  33.9   10.0/  13.0/ 104.7  10.25(10.19)   29.3   5.8   0.343  Y     Y     N
0.3     20   6.0  13.6( 88)   7.3   1.3  21.4   10.0/  10.7/ 100.2   9.86( 9.80)   33.1   4.2   0.390  Y     Y     N
0.2     20   3.3   9.1( 88)   3.8   1.3  14.3   10.0/  10.2/ 100.1   9.98( 9.98)   39.6   2.2   0.402  Y     Y     N
0.6     15  22.4  23.9( 88)  28.2   1.3  37.5   10.1/  19.2/ 105.2  10.13(10.11)   24.1   9.5   0.296  Y     Y     N
0.5     15  14.5  19.3( 88)  18.1   1.3  30.4   10.1/  13.7/ 105.0  10.23(10.22)   28.6   8.1   0.289  Y     Y     N
0.4     15  12.3  17.0( 88)  15.3   1.3  26.8   10.0/  12.9/ 105.0  10.27(10.27)   29.2   6.8   0.331  Y     Y     N
0.3     15   6.8  10.2( 88)   8.4   1.3  16.1   10.0/  10.5/ 104.8  10.43(10.43)   32.0   4.6   0.354  Y     Y     N
0.2     15   4.4   6.8( 88)   5.2   1.3  10.7   10.0/  10.3/ 104.7  10.44(10.44)   33.8   3.9   0.351  Y     Y     N
0.6     10  17.5  17.0( 88)  22.0   1.3  26.8   10.1/  16.3/ 105.3  10.17(10.05)   21.0  11.1   0.235  Y     Y     N
0.5     10  13.1  13.6( 88)  16.4   1.3  21.4   10.1/  15.4/ 105.3  10.36(10.11)   26.4   8.2   0.248  Y     Y     N
0.4     10  10.7  10.2( 88)  13.2   1.3  16.1   10.0/  13.2/ 105.2  10.42(10.37)   27.2   6.9   0.251  Y     Y     N
0.3     10   7.9   6.8( 88)   9.8   1.3  10.7   10.0/  11.2/ 105.1  10.48(10.44)   29.9   6.0   0.253  Y     Y     N
0.2     10   4.9   4.5( 88)   5.9   1.3   7.1    3.9/  10.4/ 105.0  26.66(26.66)   31.7   5.1   0.247  Y     Y     N
median  30   9.8  25.0( 88)  12.2   1.3  39.3   10.1/  15.4/ 100.8   9.70( 9.64)   28.6   4.9   0.360  Y     Y     N
median  20  17.2  26.1( 88)  21.6   1.3  41.1   10.1/  14.1/ 104.8  10.15(10.13)   27.4   7.8   0.355  Y     Y     N
median  15  14.5  19.3( 88)  18.1   1.3  30.4   10.1/  13.7/ 105.0  10.23(10.22)   28.6   8.1   0.289  Y     Y     N
median  10  12.3  13.6( 88)  15.3   1.3  21.4   10.0/  13.8/ 105.2  10.39(10.17)   26.7   7.8   0.251  Y     Y     N
```

## Reading

- Clause 5 on the recent window fails ONLY for the baseline (p60/w30, 44.3%) and the marginal p60/w20 (31.8%, 1.5 points under the line). Every lower percentile at w30, and every shorter window at p60, passes both the recent and the overall read.
- Day fires read "not tired" 1.3% of the time under every option (day fires have P~100, so a low S never makes them look rested). The whole clause-5 failure is night fires being read through a day-inflated S: recent night fires reading > 0.7 fall 69.6% (baseline) to 39.3% (p50/w30) to 21.4% (p40/w30).
- Price of lowering S: awake sp rows pinned under 0.1 rise from 21.3% (baseline) to 27.3% (p50/w30), 31.7% (p40), 35.9% (p20); rows over 0.9 fall 10.8% to 5.3% to 3.3%. Lower S makes daytime P read as exhausted more often, which is the mirror of the original saturation concern (F-2744). p60/w10 and p60/w15 give the smallest saturation increase (21.0%/11.1% and 24.1%/9.5%) but the shortest windows; w10 equals V2_MIN_FIRES, so S there is a 10-sample percentile and is noisy.
- Night-minus-day gap (separation of night from day fires) is 0.316 at baseline and 0.349-0.402 for the lower-percentile options; shorter windows reduce it (0.235-0.296).
- D-0744's other defeater (S swing under 3x in 7 days) cannot be met by any option on this history except p20/w30 (3.3x, essentially still over): the 10-to-100 jump of 11-09/10 sits inside the recent window and every option that sees day fires reproduces it. Only ignoring day fires (p20/w30) damps it. So the swing clause is a forward-looking watch, not something this replay can pick between.

## Recommendation (founder's call; no code or live flag changed)

Clause 5 is passed with real margin by two choices:
1. p50 / w30 (percentile only: V2_SCALE_PERCENTILE 0.60 to 0.50, window unchanged): recent 25.0%, overall 10.1%, night-minus-day gap 0.349, awake saturation 27.3% under 0.1 / 5.3% over 0.9. Smallest change; keeps the window the ruling and tests were built on.
2. p60 / w15 (window only): recent 23.9%, overall 22.4%, gap 0.296, saturation 24.1% / 9.5%. Less saturation cost, but a 15-fire window.
p40/w30 and below buy a bigger margin at a visibly higher daytime-exhausted rate; median/w30 (option C) is nearly identical to p50/w30 (25.0% recent) so C adds nothing over B.
Caveats: 88 recent fires (about 24 on the day side or fewer), replay of fires only (not the 1,861 shadow rows); the recent window comprises a single regime shift, so the ordering of options is solid but the exact percentages are not forecasts. Applying either needs a constant change in `core/homeostasis.py` (restart-gated) and a re-read of the one-third line after 7 live days per D-0744's defeater. No drive weight is touched.
