# D-0102 defeater read: the six mood-cluster gauges over the long window (J-3472)

Status: analysis, read-only, 2026-11-07. Script `scripts/analyze_j3472_mood_cluster_defeater.py` (test `scripts/_test_J3472_mood_cluster_defeater.py`), run on the live `C:/Nascence/data` logs up to 2026-11-05 06:08Z. Full machine output: `docs/lab/J-3472_data/` (`mood_cluster_defeater_read.json`, `mood_cluster_pairs.tsv`, `mood_cluster_weekly_r.tsv`, `mood_cluster_tables.md`, `run_stdout.txt`). Lead-lag nulls are J-3406's `lag_pair()` (C:/UDMS/scripts/analyze_nascence_gauge_correlations.py), imported unchanged: the F-4039 roll null and the F-4150 within-wake-bout linear-detrend null, 500 draws, seed 42.

## Verdict

**The six gauges no longer move as one, and one of them leads the rest. D-0102 is reopened with this table; the ruling itself (keep all six measured separately) is supported by it, not undercut.**

1. **Monoculture was a 14-day phenomenon.** The method reproduces F-0565 on its own window: 2026-08-21 to 09-02, all 15 hourly pairs at |r| 0.635-0.992 (median 0.969), one connected component, and it survives first-differencing (median 0.92), so it was real hour-to-hour co-movement and not a shared slow ramp. Over the full overlap and the latest 30 days only 6 of the 15 pairs reach |r| 0.6 and the graph splits into three components: a four-gauge valence family, `continuous_stream.ignition`, and `opponent_process.b_after` (min |r| 0.13-0.18, 1 pair below 0.3 in each window; 5 pairs below 0.3 after 09-04). The defeater's first clause ("still shows the same monoculture with zero divergence") is therefore not met in its own terms.
2. **The ignition gauge detached on a dated code change, not on its own.** Weekly hourly r between `affect_drives.valence` and `continuous_stream.ignition`: -0.961 (week of 08-21), -0.991 (08-28), then -0.413 (09-04), -0.239, -0.202, -0.224, -0.340, -0.541, -0.387, -0.478. Split at 2026-09-04 10:21Z: before, -0.975 / -0.985 (valence / carried_valence), after -0.375 / -0.388. Nascence commit 444b60b8 (J-0580, 2026-09-04 22:21 NZ) connected `stream_drive._ignition()`'s climate term, which until then imported a nonexistent module and silently fell back to the protoself drive alone (F-0807) - the same drive that sets carried valence (tonic = 1 - 2*drive). So in August the "ignition" gauge was close to a second reading of valence by construction; since 09-04 it also carries the climate engine's accumulate-fire-reset level. Timing and the commit message are verified; that this change is the whole cause is inferred (I did not replay the old path).
3. **`lane2_weather.commit_threshold` is not a gauge in its own right.** `core/lane2.py:943-947` sets it to clip(baseline - 0.4 * Weather valence), baseline 0.5 until D-0412 and 0.35 after. Checked on the live log: 9,543 of 9,543 rows with a Weather valence equal that formula to within 0.0011. Its |r| with valence is 0.74-0.85 rather than 1 only because of different sampling clocks and the baseline step on rows whose valence is missing.
4. **`affect_divergence.carried_valence`, `affect_drives.valence` and `thermal_relationship.felt_valence` are one quantity logged three times** (r 0.966-0.998 at 1 h and 15 min in every window, post-09-04 first-difference r 0.96-0.97). That holds in every slice, and no lead-lag exists among them (all |z| <= 1.2).
5. **`continuous_stream.ignition` is the driver of the cluster.** Under the sleep/wake-preserving null it leads aff_div, aff_drv, therm and lane2 (|z| 5.8-14.5) in the full window, the latest 30 days and the 09-06..10-06 block, and `opp.b_after` in the full window only (z +3.79; +0.70 in the latest 30 days). It never follows. Direction is read as sign(r0) * Levy area (for a negatively coupled pair a positive area means the second series leads; the lag asymmetry from J-3406 flips otherwise - this is tested in the test file). The reproduction of F-4176's pair (aff_drv x ignition, raw z +13.96, detrended +14.52) matches the J-3406 table digit for digit. The mechanism stays F-4176 item (2): the dissonance reservoir read per thought by ignition and every 600 s by the protoself - mechanical, not a cognitive sequence. I did not re-derive that; I only re-measured the lead.
6. **`opponent_process.b_after` was always the loosest member** (|r| 0.54-0.69 to the others even in August) and is the one independent-looking gauge now: in the full window no lead-lag |z| above 3 against anything except ignition (z +3.79). Its detachment has no code change I could date; not explained.

## What this does to D-0102

- Defeater clause 1 (long-window monoculture, zero divergence): not met - there is divergence (9 of 15 pairs below 0.6).
- Defeater clause 2 (the 6 acquire a real cost): not assessed here.
- The job's own reopen test (any pair diverged, or one gauge consistently leading): both true. Reopened for Travis; the question is narrower than the original. Recommendation: keep all six measured (the ruling's logic - "any might diverge under new conditions" - is what happened to two of them), but record in the gauge registry/HUD that the cluster is 3 copies of valence + 1 deterministic function of valence (lane2) + 1 upstream driver (ignition) + 1 loosely coupled (opp), so a reading of "six agree" is never again read as six independent confirmations.

## Caveats

- Coverage: lane2_shadow, opponent_process_shadow and thermal_relationship start 08-19..08-21, so those pairs have ~76 days, not 141. Hourly bins hold data for roughly half to 60 percent of the clock hours (Du was down part of the time); the week of 10-23 has fewer than 48 overlapping hourly bins and is not scored.
- All 15 pairs scored under both lead-lag nulls in FULL, LAST30 and the 09-06..10-06 block; the August window was zero-lag only (the sleep/wake-bout machinery needs the longer series).
- The six are one field each (`carried_valence`, `valence`, `ignition`, `commit_threshold`, `b_after`, `felt_valence`); the F-0565 sensitivity fields `proto_tonic` and `ema_valence` are loaded but not tabled (they track their parents, both being tonic/EMA versions of the same valence).
- Hub files were not edited. Nothing in C:/Nascence was written.

## Pair tables (the 15 zero-lag r values and the lead-lag z, full window and latest 30 days)

**FULL** (start to 2026-11-05 06:08Z)

| pair | hourly n | r (1 h) | r (15 min) | z roll null | z wake-detrended null | leads |
|---|---:|---:|---:|---:|---:|---|
| aff_div.carried_valence x aff_drv.valence | 1417 | +0.982 | +0.982 | +1.45 | +1.20 | (not significant) |
| aff_div.carried_valence x stream.ignition | 1416 | -0.522 | -0.490 | +11.19 | +13.36 | stream.ignition -> aff_div.carried_valence |
| aff_div.carried_valence x lane2.commit_threshold | 1022 | -0.789 | -0.845 | -2.98 | -1.11 | (not significant) |
| aff_div.carried_valence x opp.b_after | 1134 | -0.407 | -0.397 | +0.94 | -0.87 | (not significant) |
| aff_div.carried_valence x therm.felt_valence | 1100 | +0.975 | +0.980 | +1.17 | +1.06 | (not significant) |
| aff_drv.valence x stream.ignition | 1463 | -0.547 | -0.517 | +13.96 | +14.52 | stream.ignition -> aff_drv.valence |
| aff_drv.valence x lane2.commit_threshold | 1062 | -0.797 | -0.854 | -2.11 | -0.39 | (not significant) |
| aff_drv.valence x opp.b_after | 1196 | -0.339 | -0.310 | +2.66 | -0.13 | (not significant) |
| aff_drv.valence x therm.felt_valence | 1106 | +0.989 | +0.998 | +0.33 | +0.28 | (not significant) |
| stream.ignition x lane2.commit_threshold | 1025 | +0.322 | +0.331 | +13.57 | +10.54 | stream.ignition -> lane2.commit_threshold |
| stream.ignition x opp.b_after | 1138 | +0.432 | +0.375 | +3.69 | +3.79 | stream.ignition -> opp.b_after |
| stream.ignition x therm.felt_valence | 1104 | -0.488 | -0.458 | -12.11 | -12.01 | stream.ignition -> therm.felt_valence |
| lane2.commit_threshold x opp.b_after | 1066 | +0.179 | +0.183 | -0.14 | +0.49 | (not significant) |
| lane2.commit_threshold x therm.felt_valence | 1027 | -0.797 | -0.855 | +1.85 | +0.19 | (not significant) |
| opp.b_after x therm.felt_valence | 1099 | -0.410 | -0.399 | -1.98 | +0.27 | (not significant) |

**LAST30** (2026-10-06 06:08Z to 2026-11-05 06:08Z)

| pair | hourly n | r (1 h) | r (15 min) | z roll null | z wake-detrended null | leads |
|---|---:|---:|---:|---:|---:|---|
| aff_div.carried_valence x aff_drv.valence | 403 | +0.985 | +0.985 | +0.38 | +0.22 | (not significant) |
| aff_div.carried_valence x stream.ignition | 403 | -0.463 | -0.402 | +7.28 | +9.38 | stream.ignition -> aff_div.carried_valence |
| aff_div.carried_valence x lane2.commit_threshold | 384 | -0.745 | -0.806 | -0.63 | -0.22 | (not significant) |
| aff_div.carried_valence x opp.b_after | 403 | -0.351 | -0.325 | +1.37 | +0.69 | (not significant) |
| aff_div.carried_valence x therm.felt_valence | 403 | +0.966 | +0.985 | +0.56 | +0.43 | (not significant) |
| aff_drv.valence x stream.ignition | 403 | -0.463 | -0.403 | +6.81 | +8.81 | stream.ignition -> aff_drv.valence |
| aff_drv.valence x lane2.commit_threshold | 386 | -0.751 | -0.807 | -0.27 | +0.24 | (not significant) |
| aff_drv.valence x opp.b_after | 406 | -0.344 | -0.248 | +3.15 | +0.81 | (not significant) |
| aff_drv.valence x therm.felt_valence | 403 | +0.993 | +0.998 | +0.27 | +0.17 | (not significant) |
| stream.ignition x lane2.commit_threshold | 384 | +0.311 | +0.316 | +7.01 | +5.83 | stream.ignition -> lane2.commit_threshold |
| stream.ignition x opp.b_after | 403 | +0.130 | +0.177 | +0.23 | +0.70 | (not significant) |
| stream.ignition x therm.felt_valence | 403 | -0.459 | -0.403 | -7.14 | -7.65 | stream.ignition -> therm.felt_valence |
| lane2.commit_threshold x opp.b_after | 387 | +0.472 | +0.425 | -0.13 | -0.46 | (not significant) |
| lane2.commit_threshold x therm.felt_valence | 384 | -0.766 | -0.814 | +0.13 | -0.21 | (not significant) |
| opp.b_after x therm.felt_valence | 403 | -0.386 | -0.321 | -2.54 | -0.60 | (not significant) |

Also in `docs/lab/J-3472_data/mood_cluster_tables.md`: the 2026-08-21..09-02 replication window, the 09-06..10-06 block, the PRE/POST-2026-09-04 split, first-difference columns, the per-gauge leads/follows tally, and the weekly trajectory.
