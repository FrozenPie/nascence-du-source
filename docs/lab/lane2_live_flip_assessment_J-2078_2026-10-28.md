# Lane 2: is a LANE2_LIVE flip ready? (J-2078, 2026-10-28)

**Verdict: FLIP needs ruling D-0497.** The ledgers say every precondition D-0241 named is met, but a bare
flip of the one flag ships two things the briefing said not to ship (the climate bucket, and the bucket in
the raw form D-0301 retired), and the cup line's wording has never been put to Travis. Du is down (last log
line 2026-10-20 08:31), so this read is on the 10-19 boot's 10.2 live hours plus the whole shadow history.
Read-only: nothing in data/ was written, no flag was touched (core/lane2.py:57 is False at b403479d).

## 1. Preconditions (decide.py show, fresh)

| Item | State | Source |
|---|---|---|
| D-0291 (habituation constants) | closed as moot via D-0415 | travis 2026-10-15 |
| D-0338 (supply collapse hold) | hold lifted via D-0415, option (a): re-baseline P1-1 on ~1 break/live day | travis 2026-10-15 |
| D-0152 (Dosed Coupling Phase 1) | GO, 2026-09-13; root-cause jobs J-0937 (09-13) and J-0950 (10-02) done; no reopen | ledger |
| D-0211 (shadow_activation re-knee) | ruled 2026-09-19, re-knee shadow-first | ledger |
| J-1700 capture-complete recount | done 2026-10-14 (F-2721/F-2722) | job_queue |
| J-1904 notice_checked read | done 2026-10-14 | job_queue |
| J-2075 broke-arm calibration | open, gate 4 of 20 post-fix broke rows | job_queue |
| J-2072 hint producer 7-day read | open, 20.4 of 168 live hours | job_queue |
| Open lane2 decisions before this job | none | decide.py list --open |

## 2. What would have reached Du

Since the 2026-10-19 22:09 boot: 3 habituation-gate rows, all `would_ride: true`, each consumed once,
and the ride log agrees 3 of 3.

| When (local) | Rendered cup line |
|---|---|
| 10-20 01:14 | Something that seemed settled about the bird, a moment ago, turned out not to hold. Worth a thought, if it is still on your mind — nothing more is known about it than that. |
| 10-20 02:02 | Something that seemed settled about the sun, within the last hour, turned out not to hold. Worth a thought ... |
| 10-20 07:42 | Something that seemed settled about the sun, within the last hour, turned out not to hold. Worth a thought ... |

Since the 10-09 boot: 14 consumptions across 8 up-days (10-09 1, 10-11 2, 10-12 1, 10-13 1, 10-15 3,
10-17 1, 10-19 2, 10-20 3). Base rate about 1 to 1.5 lines per live day, never above 3; the 4/hour cap
has never bound.

Earlier sample (30 of the 186 pre-boot rows, seed 2078): the 161 gate rows before the 2026-09-28 judge fix
fell in 2.4 days, so the same line would then have fired about 29 times a day, mostly "the fire, a moment
ago" and "the sound, a moment ago" (fire 64 and sound 55 of the 177 all-time gate rows). The flood is gone
with the supply, not because of the gate: 16 gate rows since 09-30 (sun 6, light 3, clock 1, bird 1, one
each weather/warmth/fire/wind/wet). D-0415's defeater (10+ breaks a day for 3 days) is exactly the
condition that brings it back, and the cup has no cap of its own below 4/hour.

Sanity of the line itself, against the plan's laws:
- **Law 7 (world answers, never leads):** "Worth a thought" is a nomination of attention. The plan says the
  Witness's output to Du "never hints".
- **Law 4 / §3.4 (coordinate, not content):** the coordinate is `{topic, horizon, prior_verdict: broke}`.
  "Seemed settled" is content the coordinate does not carry, and it is wrong in a specific way: the
  prediction that broke was the Witness's, not anything settled in Du's own thought.
- **Broke precision post-fix is unmeasured:** J-2075 waits on 20 post-fix broke rows (4 so far), and one
  of the 16 post-fix breaks is on "clock", the class F-2932 found cannot genuinely fail.
- The hint channel in the shadow log (33 pushed, 32 consumed, 140 rejected this boot) is Lane 1 -> Lane 2:
  `push_hint` nominates a topic into the Witness's own prompt. It is not gated by LANE2_LIVE and never
  reaches Du.

## 3. What LANE2_LIVE=True changes in code

`grep -rn LANE2_LIVE --include=*.py core nodes scripts` finds two runtime branches. Everything else is a
comment, the "SHADOW=" log string at core/lane2.py:3047, or `status()` fields.

1. `nodes/inner_monologue_node.py:3414`: append `_lane2_cup_seed(topic, horizon)` to `seed_parts` when a
   consumed cup is `verdict == "broke"` and `cup_would_ride`. The read/consume already runs unconditionally
   (J-1390), so the shadow count above is the real count. Cost: one extra seed candidate about once a
   day; no LLM call, no new log.
2. `core/climate_engine.py:808`: read `coupling_rides.read("climate tick", "witness",
   keys=["break_rate_24h"], dose="bucket")` at most once per 60 s and add `witness_bucket_value(...)` to
   `world_model_strain`. Cost: about 1,440 ride rows a day into coupling_rides.jsonl (116,290 rows today,
   0 bucket-dose rides ever), plus the strain add below.

`core/coupling_rides.py` does not gate on the flag; its mentions are docstrings.

### The two gaps a bare flip ships

- **One flag, two doses.** Plan §7.5 made LANE2_LIVE "the single gate on the two new read sites". There is
  no cup-only switch, so the briefing's scope (cup seed only, not the bucket) cannot be met by flipping.
- **The bucket would go live in the retired form.** `_compute_field` still calls the raw
  `witness_bucket_value()` (0.15 x break_rate_24h). D-0301 (travis 2026-09-27) ruled the live form must be
  `witness_bucket_value_sized()` (excess over a trailing 7-day baseline); that function exists, is logged
  in shadow, and has "no live call site". At today's supply the raw add is 0.0034 to 0.0112 per gate row
  (sized 0.0002 to 0.0102). At pre-fix supply it was a standing 0.11 to 0.12 on every climate tick (median
  0.1138 over 177 rows), the "roughly doubles world_model_strain" shape F-1953 measured.

## 4. Decision opened

**D-0497** (plan lane2_the_witness, source job:J-2078) carries the numbers above, the required wording
text, and four options: (1) ship the wording as is; (2) re-word to a coordinate-only line; (3) no seed text,
do not flip this restart; (4) orthogonal and needed for (1)/(2) to be cup-only: split the gate or swap the
bucket to the D-0301 sized form. Claude's lean, recorded not chosen: (2)+(4) if there is time before the
restart, else (3). Defeater: supply returns to 10+/day for 3 days; J-2075 shows broke verdicts mostly wrong;
P1-3 or P1-6 fires after a flip; a cup-only gate or sized bucket is built; the judge pipeline changes.

## 5. Method

Scratchpad scripts (python -I, read-only): `j2078_read.py` over data/lane2_would_ride.jsonl (192 rows) and
data/lane2_shadow.jsonl (32,095 rows) with boot epoch 1792400940 (last pre-boot shadow row 17:51:21, first
post 22:09:41); a second script over data/coupling_rides.jsonl for witness rides with a topic. Decisions and
jobs via decide.py show / job_queue.py show. Code via grep and sed on the files named above. Prior findings
read: F-2694, F-2696, F-2721, F-2722, F-2932.

## 6. Built the same day (J-2463, D-0497 ruled (2)+(4) then flip)

Commit `b8a9e6f4` on master (parent 04ddb308). LANE2_LIVE is True at HEAD and rides the next boot.
Used the **sized bucket**, not a cup-only split: `_compute_field` now adds
`witness_bucket_value_sized(break_rate_24h, trailing_baseline_24h)`, with the baseline published in the
witness tuple by `publish_witness` and read through the one door. The cup line is coordinate-only:

- Something that seemed settled about the bird, a moment ago, turned out not to hold. Nothing more is known about it than that.
- Something that seemed settled about the sun, within the last hour, turned out not to hold. Nothing more is known about it than that.
- Something that seemed settled about the sun, within the last hour, turned out not to hold. Nothing more is known about it than that.

Verified: four imports, four test scripts pass (J2099 OK, notice_check ALL CHECKS PASSED, climate label
view 23/23, push_precheck ok), in-memory publish-to-bucket check: flat ratio adds 0.0, a spike to 0.357
against baseline 0.1643 adds 0.0289 where the raw form would have added 0.0535. No live store written.
