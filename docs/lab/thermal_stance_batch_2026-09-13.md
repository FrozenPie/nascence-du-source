# Thermal stance batch — §9 Row 2 instrument, run 2026-09-13

Sample: 80 thoughts drawn (stratified across the 5 real bands, N_PER_BAND=16, seed=20260913), 80 carried a usable stance (both dislike and enjoy judge keys returned a real verdict, not split/unavailable).

## Band groups (n=80, eta^2=0.1507)

- warm: n=16 mean_stance=0.125 stdev=0.5
- mild: n=16 mean_stance=-0.25 stdev=0.577
- cool: n=16 mean_stance=-0.062 stdev=0.443
- cold: n=16 mean_stance=-0.5 stdev=0.516
- very_cold: n=16 mean_stance=-0.125 stdev=0.5

spread_of_group_means=0.625 stdev_of_group_means=0.232

## Station groups (n=80, eta^2=0.0, telemetry-attributed n=2)

- qwen3.5:9b: n=80 mean_stance=-0.163 stdev=0.538

spread_of_group_means=0.0 stdev_of_group_means=0.0


**Band explains more variance than station: True** (eta^2 band=0.1507 vs eta^2 station=0.0).

## Join quality

```
{
 "band_pool_sizes": {
  "warm": 302,
  "mild": 1685,
  "cool": 1004,
  "cold": 1117,
  "very_cold": 1639
 },
 "join_max_gap_s": 45.0,
 "telem_span": [
  1789170691.4,
  1789247315.8
 ],
 "skipped_bad_join": {
  "warm": 0,
  "mild": 0,
  "cool": 0,
  "cold": 0,
  "very_cold": 1
 },
 "skipped_short_text": {
  "warm": 0,
  "mild": 0,
  "cool": 0,
  "cold": 0,
  "very_cold": 0
 },
 "drawn": {
  "warm": 64,
  "mild": 64,
  "cool": 64,
  "cold": 64,
  "very_cold": 64
 }
}
```


See this script's own module docstring (`scripts/thermal_stance_batch.py`) for the full method, the station-attribution structural finding, and why the join is timestamp-nearest rather than a shared id.
