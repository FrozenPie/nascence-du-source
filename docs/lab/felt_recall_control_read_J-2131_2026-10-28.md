# Felt recall control read, re-run (J-2131, 2026-10-28)

Follow-up to J-2069 / F-2796. Same method: for every fired shadow row with a `valence_lean`, the current
tuple is reconstructed from the nearest `fragment_context` row within 600 s of the row's ts; the as-logged
match is recomputed (trigger dim = value, or `sounds LIKE '"key"'`; valenced; non-`census_world`;
`tuple_ts < ts - 86400`; score 1 + other-coordinate matches over weather/fire/light_band/cat_at/place;
top 24 by (-score, -tuple_ts); score-weighted mean valence) and a CONTROL is computed that is identical
except the trigger filter is removed. Read-only sqlite URI (`mode=ro`), no `core` import, no writes under
`data/`. Script: session scratchpad `run_J-2131.py`; raw output `res_J-2131.json` (copied beside this file).

Du is DOWN (last line 2026-10-20 08:31). Inputs: `data/felt_recall_shadow.jsonl` 5,192 rows
(2026-09-28 19:09 -> 2026-10-20 08:08), `fragment_context` 97,088 rows (86,974 valenced non-census,
store mean valence -0.0929). 4,408 fired rows carry a lean; 0 lacked a reconstructable tuple.
Fingerprints (size, mtime) of both files identical before and after the run.

## 1. The pre-registered n >= 150 is not met

| dimension | fires all-time | post 10-09 boot | new since J-2069 (ts > 2026-10-15 08:20) | post 10-19 22:09 boot |
|---|---|---|---|---|
| weather | 101 | 74 | 25 | 4 |
| fire | 83 | 48 | 17 | 0 |

Live time since the J-2069 read: 89.5 h (3.7 live days, 6 boots). Weather fires ~5.5/live-day, fire ~4/live-day
over 13.2 live days since 09-28, so n >= 150 each needs roughly 9 more live days for weather and 17 for fire.

## 2. Effect vs control (matched lean minus control lean)

| subset | dim | n | mean diff | 95% CI (bootstrap) | >+0.05 | <-0.05 | corr(m,c) | repro <=0.01 |
|---|---|---|---|---|---|---|---|---|
| all | weather | 101 | -0.003 | -0.070 .. +0.064 | 33% | 30% | 0.38 | 96% |
| all | fire | 83 | +0.051 | -0.001 .. +0.105 | 35% | 21% | 0.45 | 88% |
| all | light_band | 296 | +0.042 | +0.015 .. +0.068 | 36% | 21% | 0.46 | 75% |
| all | cat_at | 151 | -0.014 | -0.048 .. +0.021 | 32% | 42% | 0.33 | 98% |
| all | sound (group) | 3,777 | +0.011 | +0.004 .. +0.019 | 34% | 27% | 0.45 | 78% |
| all | ALL | 4,408 | +0.013 | +0.006 .. +0.020 | 34% | 27% | 0.45 | 79% |
| post 10-09 boot | weather | 74 | +0.049 | -0.024 .. +0.120 | 37% | 28% | 0.43 | 99% |
| post 10-09 boot | fire | 48 | +0.083 | +0.020 .. +0.147 | 38% | 15% | 0.42 | 94% |
| new since J-2069 | weather | 25 | -0.057 | -0.157 .. +0.050 | 24% | 40% | 0.53 | 96% |
| new since J-2069 | fire | 17 | +0.061 | -0.043 .. +0.185 | 24% | 29% | 0.02 | 88% |
| new since J-2069 | light_band | 65 | +0.107 | +0.045 .. +0.172 | 43% | 17% | 0.20 | 89% |
| new since J-2069 | ALL | 1,185 | +0.026 | +0.013 .. +0.038 | 36% | 26% | 0.44 | 84% |
| post 10-19 boot | ALL | 166 | -0.066 | -0.103 .. -0.028 | 27% | 44% | 0.34 | 89% |

Reading:
- **Weather: the +0.10 (n 49) from F-2796 did not hold.** The 25 fresh fires lean -0.057 against control;
  all-time is -0.003 with a CI that spans zero either way. Per value, nothing is consistent (clear +0.03 n 21,
  drizzle -0.05 n 17, high cloud -0.04 n 27, overcast +0.02 n 26, steady rain -0.06 n 7, wind and rain +0.36 n 3).
- **Fire: same sign as before (+0.05 all-time, +0.06 fresh) but the CI touches zero at n 83**; embers +0.07
  (n 38) and out +0.07 (n 27) carry it, burning -0.02 (n 18). Suggestive, still not established.
- **light_band is the one dimension consistently above control** (+0.04 all-time, CI excludes zero; +0.11
  on fresh rows) -- small, and arriving at dark/dim is also the most time-structured trigger (every evening).
- cat_at and the sound group sit at zero. The one sound dim above zero is `sound:small_birds` +0.074 (n 101,
  CI +0.039 .. +0.116); page_turn, gate_latch, footsteps, stream, waves are all within +-0.03.
- Matched and control correlate 0.45 overall: most of the lean is still shared recency/episode structure.
- The latest boot alone (166 fires, 10 h) runs the other way (-0.066): the per-boot sign is not stable.

## 3. Thunderstorm

Zero live thunderstorm edges in 5,192 rows (weather edge values: high cloud 27, overcast 26, clear 21,
drizzle 17, steady rain 7, wind and rain 3). The store has 0 `weather='thunderstorm'` fragment_context rows
since the 10-09 boot (4,285 older ones). The plan's -0.173 vs -0.085 datapoint remains untested live.

## 4. Defects in the shadow rows (pre-flip)

1. **Same-tick multi-fire compounds the tug.** 658 of 2,054 fired ticks (32%) carry 2 to 15 fired rows at
   the same `ts` -- a soundscape change puts several keys into `sounds` at once and each key is its own
   dimension with its own cooldown (e.g. bees_in_garden, cuckoo_call, fantail_chatter, riroriro_trill,
   small_birds, tui_song, waves_on_shingle all fired with the identical lean on the same tick, 16 times;
   34 ticks had 11 fires). `core/felt_recall.py:536-538` calls `affect.apply_prior(prior)` once per fired
   edge, and `core/schema.py:145-160` is multiplicative per call (valence moves w = 0.15 x similarity of the
   remaining gap each call, and the named primary emotion gains +w flat each call). Seven calls at
   similarity 0.83 move valence 61% of the way to the matched lean and add +0.87 to fear/joy -- not the
   "maximum tug is AFFECT_PRIOR_MAX_NUDGE" the plan (section 3.3) promises. Summed per-tick max-nudge
   budget: median 0.15, p95 0.995, max 1.81. Must coalesce per tick (one prior per happening, or the
   max/mean over the tick's fires) before any flip.
2. Alias sound keys still duplicate rows exactly (kereru_wingbeats == wood_pigeon 14x,
   gull_cries/kingfisher_call/oystercatcher_call/shag_wingbeats/shingle_drag as one 5-key block 28x),
   so sound dims are not independent signals (known from F-2683, unchanged).
3. Minor: 3 sound rows are `fired: true` with `n_match: 0` and no lean (honest empty, not a bug);
   `gate_used` appears only from 2026-10-16 22:38 (J-2097 live since that boot), 4,090 older rows lack it;
   one `dispatcher_verdict: spike` row now exists (F-2685 saw 0).

## 5. Verdict against the plan's own criterion

Plan section 7: "Flip FELT_RECALL_LIVE only on a founder read of Phase 0's sheet." D-0408 A (travis,
2026-10-15): do not flip until the control read is read with F-2685 and a dimension-by-dimension keep/drop
list is brought as a new decision; its defeater: no signal beyond control on every dimension -> option D
(re-scope to sections 2 + 4); signal on some -> those become the Phase 1 list.

- The pre-registered n >= 150 for weather and fire is not reached (101 / 83 all-time).
- Weather carries no signal beyond control; the earlier +0.10 reversed on fresh rows. Fire is +0.05, CI
  touching zero. light_band is the only dimension with a CI above zero (+0.04).
- Defect 1 means a live flip today would apply up to 15 compounding tugs on one happening.

**The promotion criterion for FELT_RECALL_LIVE is not met. FLIP: no.** The honest options for the founder
(new decision, per D-0408's own defeater): (A) re-scope to sections 2 + 4 (section 8 option D) -- weather,
the founder's own example dimension, shows nothing; (B) Phase 1 on light_band only, after the per-tick
coalescing fix, as the one dimension with a signal above control; (C) keep the shadow running to n >= 150
on fire before deciding. Thunderstorm has still never happened.
