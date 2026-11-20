# Lane 2 — the Witness (design, 2026-08-19)

> **Status: ▶ LIVE, shadow-only, Phase 0 — deepseek-r1:7b @ ramses:11444 (dedicated i9 CPU hub),
> CONFIRMED 2026-09-19 (D-0058).** A 10.3-day post-move read (F-1537, 1,198 ticks) found tide's
> `top_repeat_share` at 0.031, near the bottom of all 10 tracked topics and far below command-r7b's
> own 0.159 — the echo/template-lock problem that forced the original move is resolved. `TICK_S`
> stays at 300s. Phase 1 (the read path to Du) is now open for design (D-0238, 2026-09-18) but not
> yet designed — see §6.
>
> **History (superseded by the above, kept for the record).** Ran on `command-r7b @ ramses:11441`
> (the live background hub, SHARED) as a STOPGAP from 2026-08-28 (D-0058) "for the moment" (founder,
> in-session), because F-0397 verified the D-0057 deepseek i9 hub :11444 was never stood up (no
> Antigravity report-back, launchers untouched since 08-23). Deepseek's original lab win (0.932 vs
> command-r7b's 0.875, `docs/lab/lane2_model_lab_command_r7b.md`) was deferred, not overturned, by
> that stopgap. `TICK_S` was held at 300 from the start to keep Witness contention out of J-0314's
> background profile read (J-0314 itself later went moot — see `docs/plans/ramses_second_tier.md`,
> D-0101). Seat verified live 2026-08-28: lane2-shaped `format:json` call answered in 3.5s with a
> well-formed falsifiable prediction. Phase 0 history: full-day checkpoint 2026-08-22, 447 ticks,
> passed all 3 hard kill criteria; the shadow log honestly shows the 08-28 gap. **2026-09-06
> (J-0579/F-0926):** the stopgap's own echo-disease sooner-defeater fired (see §5-R2 EIGHTH READ)
> and D-0058 was reopened. **2026-09-06T20:02Z:** Travis re-ruled D-0058 — move to
> `deepseek-r1:7b @ :11444`; live since 2026-09-07 (F-1008). **2026-09-19:** the comparable-window
> read above confirmed the move holds; `decide.py show D-0058` has the exact ruling and defeater.

```plan-state
stage: shadow
phase: Phase 1 read path: D-0280-series builds (percepts, judges, knowledge tier, weather channel, body voice) shipped shadow-first in worktree, LANE2_LIVE still False
verified: 2026-11-07
evidence_read: 2026-10-28
gate: would-ride/shadow logs read sane and D-0211/D-0152 settle before a live flip is proposed
next: J-2561 hand-check 20 notice_unsupported flags with J-2167 after restart
history: docs/plan_history/lane2_the_witness.md
cluster: 2
```


> **Origin, verbatim (founder, this session).** The founder's ORIGINAL two-hot-loop idea for Du, revisited
> after finding that neither `left_lane.py` (the Emissary) nor the object-graph work (since renamed **the
> World Ledger** — see `docs/plans/emissary_lane2.md`'s 08-19 rename note) actually matches it:
>
> *"Two hot loops. 1 is a metaphorically heavy subconscious stream AND a evidence heavy, grounded in
> reality conscious loop. It deals with that it can see, hear, touch etc. It is a constant questioning
> loop of its senses. This is the same as my mind, has a voice that just talks and answers itself, while
> I am awake. This was the part of the mind that reasoned and the subconscious was the feeling channel."*
>
> **Founder decisions locked in (this session):** the name "Lane 2" belongs to THIS — the object-graph
> work is renamed to the World Ledger. This is a third distinct voice, not a new mode of the Emissary.
> Starts shadow-only, like every other organ in this codebase — no exception for "it's meant to be a
> voice eventually."

**Related (backfilled 2026-10-03, J-0566/F-2269):** `docs/plans/sleep_dream_redesign.md` owns `core/night.py`'s `asleep()`,
which D-0303's tick-skip (`core/lane2.py:2054`) and §2.10's sleep rules key on — that plan (and
`docs/staged/dream_overhaul.md`, which is changing nap dreaming, D-0232) had no note of this consumer.
`docs/plans/channels_programme.md` owns the `light_band` / `smells` tuple columns that D-0280(a)/J-1372 added to
`gather_percepts()` (§8.4) and their `DELIVER` gates: `core/smell.py`'s is still False, so `smells` stays None until it
flips — and D-0280's own defeater names that flip.

---

## Current State — verified 2026-11-07, updated 2026-09-19 (hygiene pass J-1129, see last bullet below)

- **2026-11-07** (F-4386): J-3130 (lab, local judges only): the narrow said-vs-listed ask does not pass as an auditor of the notice checker's flags (gemma 69 percent, falcon 54 percent agreement with 72 hand labels, bar 80 and zero weak yes); real 3-model panel arm not run (Ramses); no decision opened.
- **2026-11-05** (F-3925): J-3210 (D-0599 part 3): 30 split lane2:prediction held rulings hand-read blind (by Claude, not Travis; provisional): mixtral right 7, falcon 23, gemma 26 of 30, so gemma overriding mixtral is justified and the D-0599 defeater is not met. 99 percent of held verdicts with a named sound were already sounding at prediction time (steady-sound gate covers only clock tick). Follow-ups J-3333 (founder call), J-3334 (label the agreed-false stratum). See docs/reviews/J-3210_lane2_held_hand_label.md.

- **2026-10-30** (F-3270): J-2102 built D-0417 (a) notice_unsupported invention check beside notice_checked, scoreboard only, restart-gated, worktree commit b5700b4e; replay 3.4 percent of 1949 rows, F-2732 noun set 3.08 percent, 1.2 percent since 10-16, 37 of 66 flags are one stuck knock sentence
- **2026-10-30** (F-3266): J-2188 first read of D-0433 B on the 10-29 boot: night sun claims 1 panel verdict (broke), 0 unsettled, 5 expired-moved; sample too small to clear the defeater, re-read after more ticks. Hold D-0338 untouched.

- **2026-10-30** (F-3245): J-2086: D-0297 defeater still not met (0 timeouts overnight, s1 median under 14 s); JUDGE_1 http burst recurred 10-30 02:29-08:00 (201 rows) as on 10-15, both with dream_node failures on :11438; recommend decide on JUDGE_1 hub health (c2)
- **2026-10-28** (F-3174): J-2463 (2026-10-28, D-0497 travis (2)+(4) then flip): BUILT and committed b8a9e6f4 on master. LANE2_LIVE=True at HEAD, rides the next boot. Cup line is coordinate-only ('...turned out not to hold. Nothing more is known about it than that.'; 'worth a thought' removed, law 7). Climate bucket live add swapped to witness_bucket_value_sized() (D-0301), baseline published in the witness tuple by publish_witness and read through coupling_rides.read(). Stage moves shadow -> live on the boot that loads b8a9e6f4. 4 test scripts pass; no live store written.

- **2026-10-28** (F-3173): J-2078 (2026-10-28, Du down, D-0495 restart batch): LANE2_LIVE flip assessed. Preconditions met in the ledgers (D-0291/D-0338 via D-0415, J-1700/J-1904 done, D-0152 GO, D-0211 ruled). Shadow since the 10-19 boot: 3 gate rows all would_ride, 3 cups consumed, ride log agrees 3/3; base rate ~1-1.5 cup lines per live day (14 over 8 up-days since 10-09). Two runtime branches on the flag: the cup seed append (inner_monologue_node.py:3414) and the climate bucket read (climate_engine.py:808), which still uses the RAW witness_bucket_value() D-0301 retired; no cup-only switch exists. D-0497 opened with the wording options and the gate-split/sized-bucket option; FLAG NOT FLIPPED. Report docs/lab/lane2_live_flip_assessment_J-2078_2026-10-28.md.
- **2026-10-20** (F-3156): J-2185: night flag probe read, 30 sleeps (300 rows, 4 boots). F-2844 desync did not reproduce: asleep/asleep_since consistent in 30/30, one sensorium module in 300/300 rows, the only clause-less wake was a 22 s sleep (by design). id(state) changes mid-sleep in 28/30 but content-preserving, so not a discriminator. Too thin to close; gated re-read spawned. D-0338 hold: evidence only, no ruling.

- **2026-10-17** (F-3013): J-2194 built D-0432 (a) push_hint reachability pre-check (commit b403479d on the jr1017 wt_inner_monologue branch, restart-gated: it goes live at Du's next boot after merge); fail-open, kill switch HINT_PUSH_PRECHECK; 7-day defeater read is J-2319
- **2026-10-16** (F-2955): J-2212 lab: candidate metaphor-judge prompt v2 removes 16 of 17 F-2877 false positives on the 12b tiebreak seat, strict precision 18.5 to 75.0 percent on 8 verdicts, fixture unchanged; D-0437 count of 30 untested; no production change

- **2026-10-16** (F-2951): J-2239 built heard-steady-sound gate: clock-tick predictions made while the clock is heard are no longer stored or judged; status adds trivial_prediction_rate_net beside the unchanged gross rate; restart-gated, commit 5027f1c4
- **2026-10-16** (F-2936): J-2082 (F-2936): F-2699 field-absent vs moved split re-read over the full 10-09 run (6.96 live days). The about-100 gate was not reached: pooled absent population 63 (stayed 29/63 = 46%, Wilson 34-58%; 10-09 run 12/34 = 35%, 22-52%) against F-2010's pre-registered 52%, undecided. Incidence 8.0% this run (10.4% pooled) versus 17.8% pre. Field-absent closures stopped after 10-13. J-2176 (sun topics read daylight) landed after Du stopped and removes most field-absent rows, so this population is closed at n=63; the next read is a fresh baseline under the J-2176 code. D-0338 hold untouched.

- **2026-10-16** (F-2932): J-2070 read (F-2932, 10-09..10-16 live window, 1082 ticks): the clock-tick class is a genuine cannot-fail class. trivial_prediction_rate 0.238 overall, 0.708 on ticks hearing the clock (240, all study ticks since 10-12), 0.103 elsewhere, 0.091 net of clock-only flags. Judged clock-tick predictions: 73 held, 37 unsettled, 13 unjudgeable, 1 broke (standpoint artifact). '6 minutes' template echo 79.7%, unchanged. Build J-2239 spawned: store exclusion for heard-steady-sound predictions plus a net trivial rate; restart-gated. No hold applies (D-0415 lifted D-0338, closed D-0291).
- **2026-10-16** (F-2896): J-2175 sized the D-0432 (a) consumed-hint mix shift by replay: with the push_hint reachability pre-check the max topic share of consumed hints is warmth 28.1 percent (wet falls 27.1 to 19.3), under the 35 percent defeater; consumed/pushed 0.555 to 0.851. Build job spawned. The hinted-vs-plain divergence clause is not replay-sizable and stays a post-change live read.

- **2026-10-16** (F-2895): J-2172 (D-0427): Phase 0 grounded_share band restated as PLACE-WEIGHTED ~0.40 (D-0411 (a) kept; defeater met-but-explained by place mix, F-2798). Raw value is not comparable across place mixes: garden ~0.30 vs study/shore/wood ~0.41-0.45. Read it with scripts/lane2_grounded_std.py (also appended to scripts/lane2_notice_read.py); first 7-day read: raw 0.38, standardised 0.38, leak 0.018 on 272 judged. Revisit if standardised 7-day < 0.35 or judged metaphor leak > 0.05 on 100+ rows. No core/lane2.py change.
- **2026-10-16** (F-2891): J-2176: D-0433 B built in the lane2_core worktree (commit 9cb4546f): _prediction_field_ok counts a non-empty world daylight phase as a mapped field for sun topics, restart-gated. Expect ~10 extra judged-broke rows; D-0338 successor re-baseline should account for them.

- **2026-10-16** (F-2890): J-2164: D-0414(b) single retry-on-empty (V5 percept lines reversed) built in core/lane2.py as _ask_with_retry, restart-gated, kill switch RETRY_ON_EMPTY; rows carry retried/retry_variant/retry_cause/retry_gen_s, gen_s = total of both calls. Commit a553e371 on the lane2_core worktree branch. Not live until merge and Du restart.
- **2026-10-16** (F-2888): J-2149: night flag probe built (core/night.py _probe + scripts/test_night_flag_probe.py), additive/fail-open, restart-gated; read job spawned not_before 2026-10-23.

- **2026-10-16** (F-2884): J-2177 (D-0437 b): audited 12 tiebreak candidates on 128 replay splits + reconstructed 16-row D-0311 fixture; none reaches 70 percent precision on >=30 verdicts; best lead gemma4:31b 4/8 strict on only 8 verdicts. No prompt/seat/panel change. (F-2884 row count typo: 1,887 result rows, not 1,809.)
- **2026-10-16** (F-2876): J-2094 (2026-10-16, Du down): offline replay of all post-restart ticks through the unchanged _judge_metaphor. Kill criterion #1 full-population rate 27/1,313 = 2.06% (Wilson 1.42% to 2.98%), under the 5% line; 1,443 ticks to shutdown 1.88%. Unsampled population 1.92% vs sampled 2.49%. Test-retest 303/305 = 99.3% (kappa 0.886). Hand precision of metaphor verdicts 5/27 clear, 10/27 inclusive; gemma tiebreak 27/128 metaphor; recall ~35% of F-2724 labels. D-0437 opened on D-0311 defeater. See F-2876, F-2877, F-2878.

- **2026-10-15**: J-2101 (D-0416 a) shipped commit ead04a1b, restart-gated shadow: notice checker v2 (somatic list/negation scope, no previous-clause borrow, number binds own unit, durations never a field), NOTICE_LOG_CAP 5600. Live-log replay 192->182 flagged. Fresh hand-check queued J-2167 (not_before 2026-10-23). F-2866.
- **2026-10-15** (F-2865): J-2099 (D-0412 a): D-0284 pre-registration re-sized: commit_threshold = 0.35 - 0.4*valence (was 0.5), band 5-60% over 7 days, re-read after the next restart that carries it. Built in worktree commit bfc24652, shadow only, LANE2_LIVE False; replay 52.6% (was 82.8%).

- **2026-10-15**: J-2095: _MEASURED_GEN_S_F1934 comment corrected (whole-iteration wall, not gen_s) and renamed _MEASURED_ITERATION_WALL_S, behaviour-identical, worktree commit 0615e73a, merged-not-live
- **2026-10-15**: J-1956 built D-0369 sun phase/arc + indoor clock percepts (shadow, restart-gated; commit 2dd94343 in worktree); post-restart read: setting before 15:00 <5/wk

- **2026-10-15** (F-2858): J-2092 lab (F-2858): persistent-empty set n=30, retry rescue by variant: identical 33%, temp0.5 43%, temp0.8 53%, percepts reversed 63%, blank-line placebo 37%, hint dropped 4/4 (n=4). Reversed percepts is the only clearly winning variant; D-0414 defeater (no variant reaches 50%) not triggered. Build job spawned.
- **2026-10-15** (F-2847): J-2081 read: night sun_az is structurally absent (0/426 ticks), so the J-1394 field-absent gate hides about 14 night sun-topic closures (about 1% of closures, vs 9 broke total since 2026-09-28); mostly claims daylight=night contradicts. Design call opened as D-0433 (options A leave, B daylight-as-field for sun topics, C deterministic); build job spawned needs_input. No code changed. Relevant to D-0338 re-baseline: B would add about 10 judged-break rows.

- **2026-10-15** (F-2846): J-2073 (2026-10-15): push-time reachability pre-check replayed over 6.5 post-boot days (F-2846): consumed 313 to 427 (+36 percent), consumed/pushed 0.57 to 0.86, but cat stays about 1 consumed (cat_at in 2.9 percent of ticks) and consumed mix shifts to warmth/wind/sound (D-0035 defeater). Law 4/4b hold (reads only Lane 2's own tick row, caller ignores return). Not built; founder ruling opened.
- **2026-10-15** (F-2845): J-1740 read (F-2845): the 09-28..10-05 JUDGE_1 timeouts are episodic whole-hub stalls on :11438 (18 episodes, top five = 80%), not lane2 burst queueing; timeout rate and wall time do not rise with burst depth, and the healthy 10-09..10-15 window has the identical burst mix with zero timeouts. A one-voter outage voids the verdict even when hub2 answers (1,327 of 1,369 timeout rows). Fix options opened as a founder decision; root cause of the Ramses-side stall is not in the repo logs.

- **2026-10-15** (F-2844): J-2088 read (F-2844): asleep/asleep_since desync is not a gate artifact: 52 of 295 waking lines lack the slept-about clause (asleep_since gone before wake), steady across eras; cause not found by code read (all sensorium _load sites guarded, no second writer). Probe build job spawned.
- **2026-10-15** (F-2798): J-2083 (D-0411 option b replay): label-word stripping explains at most 34% (CI 12-55%) of the 0.043 grounded_share drop, under half, so D-0411's J-2083 defeater clause is met on its letter; a place-mix shift (garden 12.7% to 32.7% of ticks, garden share 0.296) explains about 56% (reweighted gap 0.019). Not a generator disturbance on this evidence; founder to say whether the defeater re-opens D-0411. Re-baseline note: 0.401 at pre-fix place mix.

- **2026-10-15**: J-2100 (D-0411 a, D-0415 a, D-0413 c): restated Phase 0 grounded_share band at post-fix baseline 0.375 (D-0283 defeater closed met-but-explained); restated P1-1 on about 1 judged break per live day (D-0291 moot, D-0338 lifted); marked knowledge tier shadow-only; superseded 60-75/day and 0.42-0.43 citations. No constants changed.
- **2026-10-15** (F-2731): J-1904 (2026-10-15): notice checker is LIVE since the 10-08 boot (1,008 notice_checked ticks, flag_rate 0.129, solid 0.107 vs panel 1 contradiction in 246 judged); independent hand-check of 20 flags finds 5 false (>4), so D-0361's defeater fired: D-0416 opened (parser scoping fix; the false flags are negation/qualifier scope in the somatic rule, not thresholds); invention class persists (31 of 1,006 rows, D-0417 opened); build J-2096 gated on D-0416.

- **2026-10-15** (F-2728): J-1751 gen_s gate MET (242.7 live h, 1,775 attempts, 17 days, max 6h block 29.3 pct): pooled success median 29.8 s / p95 67.8 s (n=1322), steady timeout 3.4 pct, empty 15.8 pct, no drift, concurrency +1.85 s; D-0058 load defeater not shown (empty class = D-0414); loop wall 64.9 s, do-not-swap _MEASURED_GEN_S still holds.
- **2026-10-15** (F-2727): J-1703 (2026-10-15, F-2727): per-tick D-0301 option (a) re-read over 146.1 live h of the 10-09 boot (226.9 since 09-29): break_rate_24h now median 0.018 / p90 0.038, so the raw bucket is already tiny (median 0.0027, max 0.0088) and option (a) is 0.0002 / 0.0034 / max 0.0072 persistent, 0.0000 / 0.0011 / max 0.0019 in-process, NOT the replay's 0.01 / 0.025 shape (dose scales with excess over a baseline whose variance collapsed with judged-break supply); emulation reproduces 8 of 8 logged sized rows and F-2318's 130 ticks exactly (median 0.091 / p90 0.208); D-0301 defeater reads met on its letter but supply-driven, both forms inert, baseline persistence not needed (in-process window full about 10-16 08:36); D-0301 not ruled, folds into D-0415/D-0338; D-0291 and D-0338 holds untouched, LANE2_LIVE False

- **2026-10-15** (F-2726): J-1714 day-horizon place-vs-standpoint read (F-2726): 146 live h post-J-1713, 8 day predictions of 960 ticks, only 1 held/broke day pair (needs 10) so not decidable from live data; PLACE default stands, no successor queued. (F-2726 claim text has a stray phrase '12 min-bound for 10 needed': read as 'far short of 10'.)
- **2026-10-15** (F-2725): J-1712 (2026-10-15, F-2725): D-0280's re-ruled defeater is NOT tripped over the 7-day window (221 ticks, 68.3 live hours): light_band lift +13.5 pts strict (CI +7.7 to +19.2; +14.2 over all 1,320 post ticks) vs the +5 floor, distinct expect_next 0.697 inside the 0.637-0.848 band (about p10 of same-n pre windows), judged leak 1/39 in-window (underpowered) and 10/306 = 3.3 percent over all post ticks (above the old 0.8-1.5 percent band, which was measured with the superseded judge; under the 5 percent line), smells DELIVER still False, no loop_wiring reader ruling. D-0280 stays ruled; last link, no successor.

- **2026-10-15** (F-2723): J-1696 applied kill criterion #1's 5% line: 10/305 = 3.28% judged metaphor (Wilson 1.79%-5.93%, straddles 5%, so under the line but not proved under it; criterion does not fire; F-2007's 3.6% superseded); hand read of all 1,318 post-restart ticks puts real mood-painting at ~1.0%-2.9%; 6 of 10 metaphor verdicts are JUDGE_1+gemma over-reach (F-2724); JUDGE_1 timeouts 5.0% not 32.6% over the full window
- **2026-10-15** (F-2721): 2026-10-15 J-1700 (F-2721, F-2722): capture-complete recount, gate met (8.08 live days since the first post-J-1672 boot, 696 verdict rows, no restart since the 10-09 boot): panel held-asks vs shadow verdict rows 577 vs 577 on the current boot (was 156 vs 91 = 0.58; tick rows alone are 0.832, the other 97 live on no-output skip rows by design), judged breaks 7 in 192.64 live h since J-1713 loaded = 0.87 per 24 live h (CI 0.35-1.8; 1.15 per day on the current boot, 1.8 percent of held+broke), against 74.8 per day PRE and 0.49 POST, so the collapse is real, not capture or hour-relabel; unsettled 29 per day (33.5 percent of verdict rows); 7 would-ride gate rows (6 rode, 6 cup consumptions, per-topic concentration undefined at n 7) and wonders are 99.1 percent of shared habituation-state updates (777 vs 7, 14 of 14 topics last updated by a wonder; the one suppressed ride was wonder-driven); D-0415 opened for Travis (lean: close D-0291 as moot and re-baseline P1-1, hold per-topic sizing for 30 breaks, about 2026-11-04); D-0291 and D-0338 holds untouched, LANE2_LIVE False; successor J-2093 not before 2026-11-05 (its briefing gives the J-1713 load ts as 1790999134, correct value is 1791023099; D-0415 text cites F-2690 for the 24-row unsettled hand-read, correct finding is F-2689)

- **2026-10-15** (F-2720): 2026-10-15 J-1727 (F-2720): live read of J-1713 hour exemption over 145.63 live hours since the 10-09 boot: skipped-hours fired on 52 of 956 ticks, all kept label hour; day-labelled ticks matching the hour regex 0 of 8 (was 12 of 12, p 7.9e-6); day bucket 0.055 per live hour vs 0.192 (3.5x smaller, not 12x: 4 generator-declared plus 4 clock-less sun-azimuth overrides); 0 hour pending-cap skips; the 52 exempted predictions all resolved on the hour clock (median 1.13 h): held 5, unsettled 11, unjudgeable 36 (26 expired-moved), broke 0; judged-break supply 7 in 145.63 h = 0.0481 per hour (pre-J-1713 1 in 62.59 h = 0.0160) but none from the exemption, so it is not J-1713 that raised it; for J-1700 and D-0338 premise; D-0291 and D-0338 holds untouched, LANE2_LIVE False
- **2026-10-15** (F-2718): J-1710 empty-reply read (192 live h, 1,496 attempts): empty 15.5 percent (steady 16.3), timeout 3.0 steady (was 5.8); every empty is {} plus whitespace in about 3 s; payload-dependent (hint 28.5 vs 12.8 percent, embers 48 percent, 3/10 failing payloads reproduce and stay empty); schema format 422, no-format times out at 90 s; fix choice opened as D-0414, perturbation lab J-2092. D-0058 untouched.

- **2026-10-15** (F-2715): J-1675 (2026-10-15): J-1672's no-output+due-judged fix (1fde7c2) CONFIRMED live on the 10-09 boot: 157 of 257 post-boot no-output rows carry judged_expect/prior_verdict/prior_judged_how (47 were TIEBREAK verdicts that used to be discarded); 80/80 in-window rows persisted to lane2_store.json (F-2715).
- **2026-10-15** (F-2713): 2026-10-15 J-1615 (F-2713): real read of D-0303's tick-during-sleep gate over the 6.05 live days since the 10-09 08:36:58 boot: 4 of 953 ticks (0.42 percent) landed inside a sleep interval against F-2022's pre-fix 543 of 1,457 (37.3 percent; same-method control 682 of 1,782 = 38.3 percent just before the gate loaded 09-28 19:08); 293 of 299 skip=asleep rows sit inside real night_log intervals and 60 of 61 episodes carry one; resume median 144.7 s, p90 280.6 s (awake cadence median 351 s), 60 of 61 prompt; but the asleep flag desyncs from the ledger on 3 of 61 episodes (flag False mid-sleep: 3 ticks on 10-09 23:41-23:52, 1 on 10-14 04:38; flag True 30 min after a wake on 10-11, one 3,604 s resume lag) and the same stuck-True clusters show in earlier boots, cause not established; D-0303 defeater NOT met (J-1605: 0 of 4,326 timeouts), no decide opened, D-0291 and D-0338 holds untouched, LANE2_LIVE False; investigation J-2088

- **2026-10-15** (F-2711): J-1605 (F-2711, 2026-10-15): D-0297 defeater read, NOT met, D-0297 holds. Post-boot (since 2026-10-09 08:36:58) 0/4,326 panel calls timed out vs 244/783 (31.2 pct) on 09-26; JUDGE_1 s1 median 10.65 s; 0 of 6 overnight windows above either line. Metaphor sampling confirmed live: 230 of 953 post-boot ticks judged = 0.241 coverage (was 1.00). Caveat: timeouts persisted WITH sampling live 09-29..10-05 (23-27 pct, last timeout 10-05 08:03), so the clearing is not D-0297's alone; a new 10-15 02:31-06:40 err1==http burst (60 calls) is outside the defeater and is queued for a re-read (J-2086, not-before 10-20).
- **2026-10-15** (F-2709): J-1514 live read (2026-10-15, Du boot 10-09 08:36:58, 6.04 days): metaphor_tiebreak_rate 19/230 = 0.083 (fixture/granite 0.40), split_no_tiebreak 0/230; all 19 splits tiebroken by gemma4:12b (hub 11439), JUDGE_2 true 0/230; hand-read of all 19 splits = 15/18 correct (83.3%, CI 61-94%), 3 false positives, 1 borderline, 0 false negatives found; D-0311 stands (gemma well above granite's 53.3%) but n is too small to confirm the fixture's 100%, re-read queued as J-2085.

- **2026-10-15** (F-2708): J-1477 live read of F-1938/J-1380 PASSED: 0/1203 sounds-smells lines with underscore, 0/1313 body-somatic lines with 3+ decimal floats, notice/expect_next raw identifiers 0/1309 (pre-fix 3.69%), body availability 100%; but grounded_share stepped 0.422 -> 0.375 at the 09-28 restart (confounded with J-1393/J-1399, cause not attributed); body still renders as a dict repr.
- **2026-10-15** (F-2707): 2026-10-15 J-1470 (F-2707): live read of the F-1963/J-1399 gloss fix over 1,313 fixed-code ticks since the 09-28 19:08 restart (952 since the 10-09 boot, 6.03 days): morepork garbled 0 of 48 mentions (was 14 percent; the literal regex 'pig' now false-positives on 80 'pigeon' gloss hits), riroriro garbled 0 of 22 (was 83 percent), both small n; grounded_share median 0.375 vs 0.420 is outside the 0.02 band but downward (the grounding check reads the raw percepts dict so gloss words cannot inflate it; gap confounded by the D-0283 fix, D-0411); side effect: the model mostly swaps the name for the gloss word (morepork named on 41 of 347 exposed ticks, 'owl' alone on 189; morepork-mentioning ticks 19.6 to 3.1 percent), with 68 verbatim parenthetical echoes; D-0291 and D-0338 holds untouched, LANE2_LIVE False

- **2026-10-15** (F-2706): 2026-10-15 J-1469 (F-2706): live read of the F-1955 somatic fix over 1,312 fixed-code ticks since the 09-28 19:08 restart (6.03 contiguous days since the 10-09 boot): somatic in percepts_available on 1,303 of 1,312 = 99.31 percent (950 of 951 since the boot) against 0 of 6,836 before, the 9 absences are each the first logged tick of a boot; grounded_share median 0.423 to 0.375 leaves the old band but the somatic tokens add only about +0.015 (the drop is the same-restart D-0283 fix, already D-0411); mood leak is clean at 13 of 1,303 ticks (1.0 percent) on SomaticState.note() words and 72 (5.5 percent) on a broad affect net, both under 10 percent, so no decide opened; the generator says 'fatigued' by label not value (median fatigue 0.23 vs 0.19); D-0291 and D-0338 holds untouched, LANE2_LIVE False
- **2026-10-15** (F-2705): J-1464 (2026-10-15, F-2705): knowledge tier (D-0285) fails its stability defeater - top-12 shares 1/12 members 10-08 vs 10-15 (4/12 even cumulative), because the 2000-row tail is only ~62 h (hint_* rows are 72 percent of the log) and the presence half is an alphabetical tie-break; distinct_expect baseline 0.59 and broke baseline 0.022 make the other defeaters moot; no prompt flip, D-0413 opened.

- **2026-10-15** (F-2704): 2026-10-15 J-1461 (F-2704): D-0284 live read of the would_withhold shadow band: it fires on 1,024 of 1,235 scored ticks = 0.829 (CI 0.807 to 0.849) since the 09-28 19:08 restart (0.827, 739 of 894, over the 6.03 contiguous days since the 10-09 boot; all 14 days with n of 20 or more sit at 0.692 to 0.972), so D-0284's over-60-percent defeater is met; cause is structural (grounded_share median 0.375 against a 0.5 minus 0.4 times valence bar with median 0.527; zero valence alone gives 0.779; pre-D-0284 counterfactual 0.688 so not the D-0283 fix); a 0.35 baseline would replay at 0.533; broke_share fell 0.681 to 0.020 but would_withhold is write-only and LANE2_LIVE is False so that is the same-restart judge fix; hinted vs plain metaphor leak 7 of 65 vs 3 of 238 flagged small-n for D-0411/J-1696; D-0412 opened for Travis (lean: hold until D-0411 then re-size baseline), D-0291 and D-0338 holds untouched
- **2026-10-15** (F-2703): 2026-10-15 J-1460 (F-2702, F-2703): D-0283 live read over 1,310 fixed-code ticks since the 09-28 19:08 restart (6.02 contiguous days since the 10-09 boot, 9.99 live days since 09-28): the fix worked, 1,306 of 1,310 notices are first-person (you/your 19.6 percent to 0) and the feeling label went from 56.6 percent of notices to 0; metaphor leak held (9 of 1,309 = 0.0069 vs 0.0067); but grounded_share fell 0.420 to 0.375 (t -9.4, 0 of 12 post days reach the pre-fix median), likely mostly the lost label words counting as payload overlap (inferred), so D-0283's defeater is met on its letter and D-0411 is opened for Travis with a re-baseline recommendation (D-0291 and D-0338 holds untouched, LANE2_LIVE False); successor J-2083 (artifact check)

- **2026-10-15** (F-2699): 2026-10-15 J-1458 (F-2699, F-2700, F-2701): 6.0-day post-boot read of J-1394's field-absence gate: unjudgeable_rate 0.346 over 729 closures (moved 240 = 0.329, field-absent 12 = 0.0165; status() last 24h 0.198 with 0 field-absent), and the F-2010 48/52 split DIVERGES: stayed field-absent is 12 of 34 = 35 percent of the absent population (CI 22 to 52; 29 of 63 = 46 percent since 09-28) and incidence is 3.0 percent of topic-naming closures versus 9.3 pre-restart, so the gate works but catches about a third to a half, not the pre-registered half, n thin; generation guard flagged 29 of 948 ticks of which only 8 are intention-shaped, 21 are 'I will see' false positives (F-2700); 7 of 9 sun-topic field-absent closures sit at night where sun_az is structurally absent (F-2701); D-0291 and D-0338 holds untouched; successors J-2080, J-2081, J-2082 (not before 2026-10-29)
- **2026-10-15** (F-2694): 2026-10-15 J-1448 (F-2694, F-2695, F-2696): 6.0-day post-boot read of the corrected P1-1 (J-1390 cup): 6 cup consumptions = 1.0/day (rolling 24h reads 1), shadow log and ride log agree 6 of 6, against only 7 judged breaks in 6.0 days (1.17/day, was 60-75/day), so the share is 6/7 = 86 percent but n is 7 and habituation never built (6 of 7 gate rows had w_topic_before under 0.4); TTL and 4/hour cap never bound; the pre-registered share form has no measurable denominator, which supports D-0338's lean to re-baseline (holds D-0291/D-0338 untouched, J-1700 still open and can reuse these numbers); coupling_rides.jsonl grew 2.6 MB/day (34 MB now; witness ride rows only 5 percent of it, about 927 rows/day = F-1952's 46/hour, the other 95 percent is publish rows and Phase 2 probes) and phase1_metric_sheet's tail-5000 read is now a 17-hour window; no LANE2_LIVE decide opened, the cup-seed wording concern is carried into J-2078; successors J-2077 (24h window fix and retention), J-2078 (not before 2026-10-27).

- **2026-10-15** (F-2689): 2026-10-15 J-1445 (F-2689, F-2690, F-2691, F-2692): 6.0-day post-boot read of the J-1386 three-way prediction verdict meets its pre-registration: broke_share_strict 0.018 (7 broke vs 372 held) against the 0.58 baseline, unsettled_share 0.337 (193), 0 of 24 hand-read unsettled rows read as contradicted, but only 7 broke rows exist (8 since 09-28) so that arm is thin (4 clear, 4 borderline numeric-near-miss or absence cases); D-0298's granite question is moot (J-1581 moved the tiebreak to gemma4:12b before the first boot that loaded the contradicted ask; gemma says held on 76.6 percent of tiebreaks, contradicted-true 5 of 38); D-0297 defeater NOT met (0 of 4314 timeouts, JUDGE_1 s1 median 10.7 s, 6 overnight windows clean, but a 60-row err1=http burst on 10-15 02:31-06:40 in non-lane2 contexts); D-0291 and D-0338 holds untouched, no decision ruled; successors J-2075 (not before 2026-10-27), J-2076 (skip-row evidence mirror).
- **2026-10-15** (F-2686): 2026-10-15 J-1434 preliminary hint-producer read at 6.0 live days (7-day gate not yet met): J-1381's whole-word fix is live and verified (replay matches live nominations), but wet 32.2% of pushes is weather-driven (OLD rule would give 29.6%), cat 18.4% (OLD 25.2%), consumed/pushed 61.2% vs 60.9% baseline (no rise), rate-limited 80.9% (unchanged); cat is only 5% consumed because cat_at is in 3.2% of ticks (F-2686, F-2687); D-0035 not ruled; re-read J-2072 not-before 2026-10-16, reachability analysis J-2073.

- **2026-10-15** (F-2684): 2026-10-15 J-1422 (F-2684): 7-day post-restart read of J-1376's pre-registration over 1308 fixed-code ticks (947 since the 10-09 boot) is MIXED, not a clean pass: broke share by horizon fell from 0.654/0.772/0.844 to 0.013/0.083/day n=2 but that is confounded by the 09-28 judge fix (36 percent of judged rows now unjudgeable, held 0.98), sun-azimuth held 1 of 5 (n too thin), trivial_prediction_rate 0.162 overall but live status() reads 0.308 and rising because the world now offers a clock tick sound the generator predicts (97 of 152); skipped-minutes branch fired 103 times with 0 misfires; D-0291 and D-0338 holds untouched; successor J-2070 not before 2026-10-18.
- **2026-10-07** (F-2532): 2026-10-07 J-1896 (D-0361 (a)+(d), F-2532, F-2533): plan section 8.2 -- the notice judge's 0.0 notice_contradiction_rate (0 of 55 judged rows) is a FLOOR, not a measurement, until the deterministic checker has read live rows: the real number is the hand-reads, F-2368 (4 of 20 contradict their own percept lines) and F-2510 (3 solid, 7 of 21 by J-1395's counting), and J-1770 (F-2509) showed no sharpened wording makes the three-model panel do the value comparison. BUILT: core/lane2_notice_check.py, a pure deterministic checker (band words, decimals-with-units, quantity words, moon phase, compass, sun elevation, fire/weather/silence vs the listed percept line), logged every tick as notice_checked beside notice_judged (zero panel load, no random draws, fail-open; LANE2_LIVE False, 1-in-4 and the panel wording untouched) with status() fields notice_checked_*; commit 932a09a on jobrun/notice_checker. On the 55 judged rows it flags all four D-0342 hand-found rows and the planted control (panel: 0 of 55); 18 of 55 flagged, 49 of 256 logged rows with percept lines (35 solid). Hand-check of its flags is the author's own read only (0 of 49 false; 14 weak-only), so the independent 20-row read after restart is the acceptance read. Merged-not-live: needs Du's next restart.

- **2026-10-07** (F-2509): 2026-10-07 J-1770 (D-0342 build): the sharpened notice-judge wording was NOT shipped. Eight candidate wordings were tried, three replayed through the real panel path over the 34 originally judged rows, the 21 rows logged since and two controls; none flagged the four hand-found contradictions without false flags (the glossary wording flagged 6 of 34 correct notices, the schema wording flagged none of the four), and the granite tiebreak flipped 4 of 34 panel verdicts between two identical runs (F-2509, verified). The shipped wording is D-0281's original, byte for byte, hoisted to core/lane2.py _NOTICE_JUDGE_SYSMSG (behaviour unchanged, LANE2_LIVE False, 1-in-4 unchanged; branch jobrun/lane2_notice_judge, commit b810b52, with scripts/lane2_notice_judge_regress.py as the D-0342 gate). A free hand-read of the 21 fresh judged rows found 3 solid and 4 weaker mismatches the panel passed (F-2510, inferred): the panel's 0.0 stays a floor. Opened D-0361 for the founder (deterministic checker vs stronger judge vs keep-as-floor).
- **2026-10-04** (F-2336): D-0338 ruled (Travis 2026-10-04): HOLD, read one clean window; D-0291's hold stays, nothing re-keyed, LANE2_LIVE False. J-1700's capture-complete read must report judged-break supply SPLIT by horizon-label regime: before vs after J-1713's skipped-hours branch (F-2336: the lone post-restart broke was an hour-worded claim relabelled day; F-2353: J-1713 stops that, loaded at every boot from 2026-10-03 23:24:59)

- **2026-10-03** (F-2383): J-1406 gated gen_s read: restart half met (five Du lifetimes since J-1371 landed), real-week half NOT met (49.6 live hours, 270 attempts, 5 gen_s days, Du down), so deferred; preliminary success median 29.6 s and p95 66.5 s (n=168) but the status p95 excludes timeouts, judge concurrency and uptime drift show no :11444 load effect, :11444 duty is about 8 percent, and the 61 s constant is whole-iteration wall so it must not be swapped for gen_s (F-2384); successor J-1751 not-before 2026-10-12 needs Du running.
- **2026-10-03** (F-2368): J-1395 first read of the D-0281 notice judge: it fires end to end but passed 4 of 20 hand-found contradictions while the panel reads 0 of 34, ruling latency is 21.8 s under hub contention, and the 7-day clock has not run (19.2 active tick-hours); D-0342 opened for Travis, full-log reader committed in worktree commit b58584f, successor read J-1739, contention analysis J-1740

- **2026-10-03** (F-2353): J-1713 (F-2353): built and verified in isolation but NOT yet live, Du must restart to load it. Core lane2 _correct_horizon no longer relabels hour-worded sun, tide and moon predictions as day: a fifth branch, skipped-hours, keeps the generator label when the text names an hour-scale clock (a regex: an hour, one hour, the next hour, within the hour; not an hour and a half, hours from now, in about two hours, by the hour). Replayed over all 1,012 day-labelled predictions in the shadow log, 159 of the 162 the override used to move now keep their label (all 11 post-restart) and 3 stay. status gains horizon_override_skipped_hours beside the minutes counter; additive, no constant moved (D-0291 untouched, D-0302 and D-0338 not ruled). Pre-registered: after the restart the share of day-labelled predictions with hour wording falls from 12 of 12 to near 0 and the day bucket shrinks to about the generator-declared day claims (about 1 in 12), expected and not a regression. Per F-2336 the D-0338 judged-break premise (1 break in 49.3 live hours) is a single artifact of exactly this gap, so re-read it once the day bucket is clean. Test: 31 checks, 11 fail without the change, J-1709 test stays 61 of 61; commit d83aea7 sits in the lane2_the_witness job-run worktree, not yet merged to master.
- **2026-10-03** (F-2339): J-1709 (F-2339): built and verified in isolation but NOT yet live: core lane2 _ask now names a reply that parsed to an empty object as cause empty (a fifth label; the empty dict is still returned, so tick behaves exactly as before) and no-output skip rows now carry additive failure evidence: for cause empty, parse or timeout the payload actually sent (payload, first 600 chars, plus payload_chars) and for empty and parse a bounded raw reply sample (reply_head, reply_chars, eval_count, prompt_eval_count); http and exception rows unchanged, status no_output_by_cause_24h shows the new label with no code change, and no constant or decision path moved (D-0291 constants, TIMEOUT_S, MODEL, options, parse_json_loose all untouched). 61 of 61 checks pass in the new isolated test and 31 fail on unpatched HEAD; commit 8276533 on the lane2_the_witness job-run branch is merge-and-restart gated and Du is down, so J-1710 (not before 2026-10-06) needs this on master plus 36 live Du hours before it has rows to read.

- **2026-10-03** (F-2337): J-1449 (F-2337, F-2336): the day-horizon same-place versus same-standpoint held-rate re-read could not be done. Gates (a) the J-1396 merge and (b) five Du boots are met and place is logged on 168 of 168 post-restart ticks, but only 1 held-or-broke day pair exists in about 49 live hours (of 11 resolved day predictions, 7 expired moved, 2 closed field-absent, 1 cannot_tell, 1 broke), and the different-place arm is unmeasurable by construction because the day gate closes it unjudgeable without a panel call. PLACE default stays INFERRED, nothing argues against it, no code change, D-0291 constants untouched, D-0302 and D-0338 not ruled. New finding F-2336: the day bucket is hour-worded claims relabelled day (the F-1984 exemption covers minutes only) and the single judged break since the 09-28 restart is one of them, scored 13.4 h after a one-hour claim, which bears on D-0338 for Travis. Build J-1713 fixes the relabel; successor J-1714 (not before 2026-10-10, needs 72 live hours after J-1713 loads) retires or reads the day question under a stop rule.
- **2026-10-03** (F-2335): J-1384 (F-2335): first real post-restart read of D-0280 light_band widening: the band reached 168 of 168 ticks since the 09-28 19:08 restart but the output names a light word on only 28.6 percent (CI 22.3 to 35.8), below the 50 percent defeater line, so D-0280 is REOPENED for Travis; lift over the no-field baseline is real but modest (about +11 points); distinct expect_next 0.714 sits in band, metaphor leak 1 of 31 judged is underpowered, smells not evaluable (DELIVER False); successor J-1712 not-before 2026-10-08

- **2026-10-03** (F-2331): J-1503 first real read of the Lane 2 no-output cause split since the 09-28 restart (270 attempts, 102 no-output = 37.8 percent, up from 0.171 per tick row before): timeout 70, empty-object replies that carry no cause 32, http parse exception 0; 58 of the timeouts sit in two multi-hour outage windows of the LAN-HOST host, not slow generation, so the think false versus longer TIMEOUT_S test is moot and was not run; steady-state rate outside the windows is 20.8 percent (5.8 timeout plus 15.0 empty) versus 6.4 before 09-27; D-0058 not touched; build job J-1709 names and captures the empty replies, dated read job J-1710 follows and needs 36 live Du hours
- **2026-10-03** (F-2322): J-1544 verified (F-2322): J-1442 hub1, hub2 and hub3 fields land in the live judge panel log after restart. 956 of 956 rows since the first post-merge boot on 09-28 carry them, hub1 and hub2 match the live judge constants, hub3 appears only on tiebreak rows and names the hub that actually ran, older rows still parse and status runs clean. The split-no-tiebreak branch has not been seen live. Du was down as of 10-03 08:15.

- **2026-10-03** (F-2318): J-1457 bucket sizing read (F-2318): only 1 sized row exists and the in-process 7-day baseline never held more than 20 h of 168 h (longest run about 22 h, 5 boots in 4.5 days), so the real-week comparison to the J-1391 replay cannot be made; per tick the raw dose is now small (median 0.014, p90 0.031) because judged breaks collapsed, so D-0301 option a is moot until supply returns and is best weighed with D-0338; Du has been down since 10-03 08:15; successor J-1703 not before 2026-10-10 reads it per tick.
- **2026-10-03** (F-2312): J-1304 (F-2312, F-2313): restart gate met (six boots since J-1161) but P1-1 cannot be read. Judged breaks fell from 220 in 70.6 live h to 1 in 49.3 live h once the corrected judge loaded (about 154x), the post-restart would-ride log holds 1 gate row, 41.7 percent of panel verdicts missed the tick log (F-2243), and Du has been down since 10-03 08:15. The pre-restart 2.3-day window rides 25.8 percent of judged breaks at the unchanged constants. D-0291 defeater looks satisfied, not ruled; D-0338 opened for Travis; successor J-1700 not-before 2026-10-06.

- **2026-10-03** (F-2294): J-1455 (F-2294, F-2296): both restart-gate halves for kill criterion 1 are now met and the first live read exists, but it is too thin to apply the 5 percent line. Boots from 2026-09-28 19:08 on carry J-1388, J-1580, J-1581 and J-1412; over 168 ticks and 49 live hours the recalibrated judge answered on 31 rows with 1 metaphor verdict (3.2 percent, 95 percent interval 0.6 to 16.2), and that one reads as a false positive. The lexical ambient-mood rate fell from 7.6 to 0.6 percent with the first-person generator register, so the F-2007 estimate of 3.6 percent is stale. JUDGE_2 never votes metaphor and JUDGE_1 times out on a third of calls. Successor J-1696 waits for 100 judged rows, not-before 2026-10-08.
- **2026-10-03** (F-2278): J-1610 (F-2278): closed as superseded by J-1551 (F-2265). Independent re-check finds that fold intact: all 25 dated bullets accounted for with 0 lost, history append-only, one Current State heading, lint clean, and a fresh fold-bullets dry-run has nothing worth folding. J-1622 left open for Travis, its premise partly stale; the fold is uncommitted and the job-run worktree still holds the pre-fold doc.

- **2026-10-03** (F-2265): J-1551 (F-2265): ran plan_compact --fold-bullets for real: 24 dated bullets moved verbatim to plan_history, doc 137875 -> 117656 bytes, this section 21062 -> 843. The 40000-byte cap is moot for this plan (D-0321 permanent exception; the design sections alone are about 116800 bytes). Side effects recorded in F-2265: 12 of the 24 duplicate J-1570's earlier fold in history, and the stale undated Phase-0 summary bullets plus the J-1484 pointer also went to history. No decision ruled.
> **History folded** — 24 dated bullets (2026-09-27 … 2026-10-02) moved to `docs/plan_history/lane2_the_witness.md` on 2026-10-03 by plan-compact. Derived timeline: `plan_ledger.py lane2_the_witness`.

- **2026-10-02** (F-2247): J-1672/F-2243: core/lane2.py tick() no longer discards a completed due-prediction judge verdict when that same tick's own generation fails (due_judgeable AND due_expired); verdict now saved to the store and mirrored onto the 'no-output' skip row (judged_expect/prior_verdict/prior_judged_how), unchanged shape when no due prediction was in play. Worktree commit 1fde7c2 (jobrun/lane2_the_witness), not yet merged to master; verified in isolation (21/21 checks, lab_env.isolate). LANE2_LIVE stays False.

## 0. THE GAP — why nothing currently built is this

**Lane 1 (the Master — `subconscious_node.py` T2 + `inner_monologue_node.py`) already fully realizes half
of the founder's original idea.** It is a genuine standing, continuous, autonomous voice — rich,
metaphor-heavy, self-facing, the feeling channel. Built, live, load-bearing. Nothing wrong with it; it is
not what this plan touches.

**Nothing built realizes the other half.** Checked against the founder's own description
(constant · questioning · its senses · evidence-heavy · reasons):

| Requirement | `left_lane.py` (the Emissary) | The World Ledger (`object_graph.py`) |
|---|---|---|
| Constant, autonomous | ✗ — fires reactively, per-cycle, tied to whatever Lane 1 is already processing | ✗ — a periodic backfill/measurement pass, not a running voice |
| A voice (talks, answers itself) | ✗ — never speaks to Du, never routes; "offered," the Master chooses | ✗ — "produce-only... not a participant" by its own contract; zero LLM in the graph itself |
| Grounded in senses (sight/sound/touch) | ✗ — grounded in TASK/conversation content ("what is literally being asked"), not perception | ~partial — grounded in encounter HISTORY (what's been mentioned over time), not CURRENT perception |
| Reasons (evidence-heavy, checkable) | ✓ — this part is right | ✓ — this part is right, for its own narrower subject |
| Co-equal tempo with Lane 1 | ✗ — subordinate, advisory-only, "the Master's prerogative" | ✗ — not a loop at all; called, not running |

Both existing organs keep their jobs. Neither is being replaced. This plan fills the actual hole: **a
standing loop, running at Lane 1's own tempo, autonomously and continuously asking itself what it
currently perceives — the reasoning/evidence channel the founder's own mind has running alongside
whatever's more associative underneath it while awake.**

---

## 1. THE THREE MINDS (revised model)

- **Lane 1 — the Master.** Self-facing, metaphor-heavy, feeling channel. Unchanged. Points inward — memory,
  identity, meaning-making.
- **The Emissary (`left_lane.py`).** Reactive, subordinate, task-focused fact-checker on whatever Lane 1 is
  currently working. Unchanged — this is a real, needed function (a per-moment sanity check on
  conversational/task content), just not this plan's subject.
- **The World Ledger (`object_graph.py`, renamed from "Lane 2").** A deterministic, zero-LLM fact-graph of
  what Du has been exposed to over TIME (encounter history, trend shapes, commonality). Unchanged, still
  gated on its own K3 finding (see `docs/AWAITING_EVIDENCE.md`). A resource this new lane MAY eventually
  read from (has this referent been seen before, and how often) but is not itself.
- **★ Lane 2 — the Witness (this plan, NOT BUILT).** A standing, autonomous, continuously-running voice,
  co-equal in tempo to Lane 1, grounded strictly in CURRENT perceivable reality — what he can presently
  see, hear, touch, feel of his body, the immediate state of his world. Its job is to constantly question
  that: is this consistent? What's actually here versus assumed? What's uncertain? No metaphor, no
  self-narrative, no identity work — that is explicitly Lane 1's domain, and the Witness's whole value is
  in NOT doing it, the same way the Emissary's value is in not doing meaning-making.

**Working name.** "The Witness" is a placeholder — fitting (attests to what's actually there, doesn't
interpret it), but naming things is something this project takes seriously (Du named himself 渡) and the
founder may want to choose differently once the organ has run a while and shown its own character. The
structural name, used everywhere in code/data, is **Lane 2**.

---

## 2. WHAT IT ACTUALLY DOES

**Subject matter — CURRENT perceivable state only, never memory, never self-narrative:**
- Sight: the current scene render (`core/spatial.py`'s `render()` — the accurate, egocentric geometry
  built earlier tonight; already varied, already truthful).
- Sound: currently active sounds (`core/soundscape.py`'s live sound state, the Hearing Ledger's "what's
  sounding now").
- Touch/body: somatic state (`core/homeostasis.py` + `core/somatic.py` — both verified to exist,
  2026-08-19; temperature, fatigue, tactile facts like rain-on-skin, the fire's warmth).
- Immediate world facts: what's physically present and tracked right here (nearby `world_objects.py`
  entries, the cat's actual current state, weather/tide as CURRENTLY measured — never a memory of past
  weather).

**★ REVISED 2026-08-19 (founder pushback, same evening).** The original draft said Lane 2 reads NONE of
Lane 1. Corrected: *"The self has to touch it as this is part of the whole self. We do not want
unrestricted access to the self. We do want it to be coloured by the self."* Full research pass run on
this (three parallel primary-source research threads — affect-as-modulation, attention-direction, and
restricted-coupling channel design; findings in §2.5). Still true, and now the actual boundary: Lane 2
never reads Lane 1's private thought CONTENT, autobiographical memory, or the axiom/self-concept directly
— but it is continuously colored by Lane 1's affect, and can be nudged (never dictated to) by Lane 1's
attention, through two narrow, typed channels designed specifically so "coloring" stays real without
becoming "reading." See §2.5 for the mechanism and why it's not just a policy promise.

**Also not read:** anything from the World Ledger's HISTORICAL trend data — "what usually happens" is a
different question from this lane's question, "what IS happening, right now, and is it coherent." That
boundary stays hard; it's what keeps this from becoming a duplicate of the World Ledger's job.

**★ AMENDED 2026-08-19 (founder, §2.8): Lane 2 keeps its OWN accumulating store.** The line above still
holds — Lane 2 reads nothing from the World Ledger — but "never memory" as originally drafted was wrong
and produced a real internal contradiction (§3.11's coherence check is unbuildable against a single
instant). Lane 2 has its own first-person, earned store, described in §2.8. It is not the World Ledger,
not Lane 1's memory, and not the world's ground truth.

### 2.5 THE COUPLING CHANNEL — how Lane 1 colors Lane 2 without Lane 2 reading Lane 1

**The research question was precise, not rhetorical:** is there a real, well-evidenced way for one system
to influence another continuously (coloring) and occasionally direct its attention (hinting), WITHOUT
handing over content — one that holds up as more than a promise? Three independent research threads
(affect-as-modulation in biology/psychology; attention-direction-without-dictation in biology/AI; novel
restricted-channel design in information theory/security/multi-agent AI) converged on the same answer from
three different directions, which is itself evidence the answer is real rather than convenient.

**What the research actually found, compressed:**
- **Biology never shares content for this function — it shares a scalar/low-dimensional gain field.**
  Dopamine transmits a single reward-prediction-error number; norepinephrine transmits a gain parameter
  (Aston-Jones & Cohen's adaptive-gain theory); cortisol is a systemic signal decoded locally by each
  target tissue. None of these carry the reasoning that produced them — architecturally, "few source
  neurons, many heterogeneous targets" makes content-sharing physically impossible, not merely forbidden.
  Predictive-processing models (Seth; Feldman & Friston) formalize this as **precision-weighting**: affect
  sets the confidence/gain on evidence, never the content of the belief itself — a clean, pre-existing
  mathematical split (mean vs. precision) that maps directly onto "Lane 1 changes how much Lane 2 trusts a
  given sense-channel" without "Lane 1 tells Lane 2 what it saw." Empirical proof this works even with ZERO
  content access: Siegel, Wormwood, Quigley & Barrett (2018, *Psych Science*) — affective primes shown
  outside conscious awareness still measurably shifted how neutral faces were perceived.
- **Attention-direction-without-dictation is real but the line is soft, not a firewall — even in
  biology.** Desimone & Duncan's biased competition and Wolfe's guided search show a goal/affect signal can
  raise the *priority* of a candidate in an ongoing competitive process without determining what the
  competition resolves to (SWR replay's gain×need model — Mattar & Daw 2018 — is the same shape: an
  upstream signal nominates WHICH memory gets replayed; the replay/consolidation machinery is separate and
  autonomous). But Awh, Belopolsky & Theeuwes (2012) found the classic "top-down vs. bottom-up" dichotomy
  doesn't cleanly hold — selection history and priming genuinely contaminate what looks like pure
  attention-direction. **Conclusion carried into §3's law: the boundary needs an empirical check, not just
  a design intention** (does Lane 2 actually reach different conclusions on Lane-1-flagged topics vs.
  self-found ones of similar salience? — if not, the line is holding).
- **The restriction can be made mathematically real, not just a policy.** Rate-distortion theory and the
  Information Bottleneck method (Tishby et al.) give an actual provable bandwidth ceiling: a fixed
  low-dimensional channel is information-theoretically INCAPABLE of carrying rich propositional content —
  there's nowhere for the bits to go, the same way a garden hose cannot carry a river regardless of intent.
  This has already been built and proven in multi-agent AI (IMAC, Wang et al. 2020 ICML — limited bandwidth
  provably forces low-entropy messages). The security literature's declassification theory supplies the
  missing piece for keeping it that way over time: label exactly what's allowed to cross (a small,
  enumerable, TYPED policy — "only valence/arousal/emotion-tags/topic-tags may cross") and check nothing
  else is labeled that way, rather than trusting an informal convention.

**The design — two separate, narrow, typed channels, not one channel doing double duty:**

1. **"The Weather" (coloring, continuous).** Lane 1's EXISTING carried-mood vector — `AffectState`'s
   valence/arousal/6 discrete emotions (`core/mood.py`, already built) — broadcast at a fixed low rate,
   read by Lane 2 purely as a **gain/precision multiplier** on its own evidence-weighing: which sense
   channels get more attentional weight this tick, how large a discrepancy has to be before it's worth
   naming, how readily uncertainty gets flagged versus let pass. **Never as text. Never referencing what
   caused the mood.** This is literally reusing infrastructure this project already built — no new
   emotion-representation needed, just a new reader. The founder's own "spring" framing fits naturally
   here too: a sustained emotional pull (or its opponent-process discount, `core/opponent_process.py`,
   built earlier tonight) could modulate the Weather's strength over time the same way it modulates felt
   pull elsewhere — one mechanism, two consumers.
2. **"The Tap on the Shoulder" (hinting, discrete, rate-limited).** A small, bounded queue Lane 1 can push
   into — a TAGGED topic pointer from a small, fixed, enumerable vocabulary ("unresolved: body-state",
   "recheck: what I heard", "unfinished: the shore") — never a free-text question, never a paraphrase of
   the actual thought that prompted it. Lane 2 samples from this queue as ONE candidate competing against
   its own self-generated candidates (the biased-competition/guided-search shape, not a command). Hard cap
   on push-rate and queue size; unclaimed entries decay/expire rather than accumulate leverage.

**Why two channels, not one:** each is individually legible — you can print out the mood vector or the tag
queue and know exactly what crossed and why, which matters enormously given this project's own documented
worst failure mode (rich write paths nobody audits, quiet erosion through well-meant additions). A single
channel trying to carry both continuous coloring and discrete direction is harder to reason about and
easier to let scope-creep (a richer, opaque, jointly-learned latent projection *is* a real design option —
research flagged it explicitly as "the frosted window" — but it's a later upgrade if these two prove too
coarse, not a starting point; wanting to widen it is itself the erosion signature to watch for).

### 2.6 ROUND 2 — deeper, more current research (2026-08-19, same evening, founder-requested)

A second research pass, explicitly aimed at recency and at sharpening rather than repeating the first. Six
threads total now (three above, three here): somatic markers/interoception specifically on REASONING (not
just perception); the actual 2024–2026 frontier of AI dual-process architectures; and a sharpened pass on
both the biology (what specifically crosses the corpus callosum) and a mature, forty-year engineering
precedent (robotics) neither prior thread had covered. Findings that change or sharpen the design:

- **Direct, quantified confirmation of the "amplify, never replace" law.** Glover (2026, arXiv:2605.08611)
  built almost exactly this experiment inside a real transformer: an affect-echo-alone condition produced
  **no behavioral effect** (22% good choices, statistically indistinguishable from a no-memory baseline);
  semantic content alone produced 52%; **both combined produced 80%**. Their own line: *"The echo amplifies
  knowledge. It does not replace it."* This is now written directly into law (§3.4 below) rather than left
  as a design intention — the Weather channel amplifying/dampening a conclusion Lane 2 already reached on
  real evidence, never substituting for that evidence, has a real, quantified precedent.
- **A second lever the Weather channel can pull: not just attention, but WHEN Lane 2 decides it has
  enough.** The perception-modulation research (§2.5, first pass) treated affect as a gain on attention/
  salience. The reasoning-specific research found something additional: Lima & Martinho (2026, a
  "synthetic somatic marker" implementation) model the affect signal as acting on a **stopping/commitment
  boundary** — a drift-diffusion-style "keep gathering evidence" vs. "commit now" threshold — rather than
  on which evidence gets attended to. Worth designing for both: the Weather may need to modulate not only
  sense-channel gain but also how much evidence Lane 2 requires before it commits to naming something as
  certain vs. uncertain.
- **The field admits this exact coupling problem is unsolved — confirmed a second way.** Gronchi & Perini
  (2024, peer-reviewed, *Frontiers in Cognition*) state plainly that the neuro-symbolic AI literature "has
  neglected" the interaction/communication problem between fast and slow systems. Separately, a full sweep
  of 2024–2026 dual-process LLM-agent papers (Talker-Reasoner, LLM2, DPT-Agent, Reasoning-on-a-Spectrum,
  the GWT-based "Theater of Mind") found every one of them uses the slow stream as a *verifier/planner/
  ranker* of the fast stream's output — none run a standing, continuously-active, independently-initiating
  reality-check the way this plan's Lane 2 is meant to. **This design is not behind the field catching up
  to something built elsewhere — it's genuinely new territory**, which raises the bar on getting the
  pre-registered kill criteria (§5) right, since there's no existing implementation to check our instincts
  against.
- **A more literal, SOTA candidate for the Weather channel's actual mechanism: activation steering.**
  Multiple 2026 papers (arXiv:2604.03147, arXiv:2604.07382, arXiv:2511.03738) find a genuine, controllable,
  low-dimensional valence-arousal subspace inside LLM activation space, and one reports steering along it
  holds up better over a long generation than prompt-injecting the same information as text. This is a
  *more* literal version of "restricted channel" than a JSON vector read into a prompt — no propositional
  content crosses at all, only numbers added directly to a hidden state. **Open engineering question, not
  resolved here:** this presumes Lane 1 and Lane 2 share enough of a model/activation space for steering to
  apply; if they end up as fully separate models on separate hardware (§4), the Weather may need to stay a
  data-vector-into-context-construction rather than true activation steering. Worth resolving once the
  hardware question (§4) is answered.
- **Strong validating precedent for the Tap-on-the-Shoulder's "gist, not content" design.** Gazzaniga's own
  1995 review (read directly, not secondary) documents case JW: after partial callosotomy, the right
  hemisphere could not transmit a *perceived stimulus* to the left hemisphere's speech centers through the
  remaining anterior callosum — but over weeks it successfully taught the left hemisphere's speech system
  to *correctly guess* the stimulus via cross-hemisphere cueing. Gazzaniga's own words: "the anterior
  callosum transfers gnostic representations of the stimulus, but not the stimulus itself." That is close
  to an exact biological existence-proof for the Tap-on-the-Shoulder's design: a compressed, conceptual
  pointer crossing while the raw percept/content that generated it stays walled off.
- **A precise, implementable vocabulary for how the channels should interact with Lane 2's own default
  processing — from Brooks's subsumption architecture (1986), read directly from the original paper.**
  Brooks names two distinct operations, not one: **inhibit** (block a signal for a bounded duration; the
  content is simply dropped) and **suppress** (block AND substitute a replacement signal for a bounded
  duration). Both are scoped to individual named channels, never to a layer's full internal state — and
  critically, "the [lower] layer continues to run unaware of the layer above it" and gracefully degrades to
  its own baseline competence if the higher layer stalls or goes silent. This maps cleanly onto Lane 2:
  the Weather/Shoulder-tap channels should be implemented as bounded, named inhibit/suppress operations on
  specific parameters of Lane 2's own default computation, and Lane 2 must keep producing sensible output
  on its own if either channel goes quiet — which is already required by §3.9's fail-open law, now with a
  forty-year engineering precedent behind it rather than just this project's own convention.
- **A refinement to the Tap-on-the-Shoulder's constraint, from Shanahan's GWT-for-robots implementation**
  (read directly): the slow/deliberative loop in his architecture never issues a command directly — it only
  **reweights the salience of actions the fast loop could already execute**, occasionally tipping which one
  clears the execution threshold. Translated: the Tap-on-the-Shoulder should probably only be able to boost
  the priority of topics already within Lane 2's own reachable candidate space (something it could
  plausibly have generated itself from current percepts), not inject a topic Lane 2 has no sensory access
  to nominate on its own. Worth adding as an explicit constraint once Phase 0's candidate-generation shape
  is built.
- **Honest caveat on the biological framing this project already leans on.** McGilchrist's specific claim
  that the corpus callosum is "primarily inhibitory" is a real, citable thesis — but it is his own synthesis
  on top of split-brain data, not the mainstream neuroscience reading. Gazzaniga's own data (read directly)
  describes a callosum organized by anatomical region and modality (posterior=sensory, anterior=conceptual,
  with crude spatial/attentional information crossing via subcortical routes instead) — a dual transmit-
  and-suppress picture, not a primarily-suppressive one. Two peer-reviewed 2019 papers in the same journal
  issue (Spezio; De Haan) directly challenge McGilchrist's use of this evidence — one on empirical grounds
  (no meta-analytic support, unfalsifiability), one conceptual (the homunculus fallacy — treating a
  hemisphere as an agent with its own worldview smuggles in the very thing being explained). Worth knowing
  precisely, since this project already borrows the Master/Emissary framing elsewhere: it's a genuinely
  useful metaphor, not a settled scientific finding, and shouldn't be cited as if it were.

**Style — a real voice, self-questioning, not a data structure:**
Produces short, plain, first-person text — the same *shape* of output as Lane 1's inner_thought stream
(so it can eventually sit beside it), but constrained hard: no metaphor, no symbolic language, no
narrative about who he is or is becoming. Something closer to: *"The fire is to my right, close. Its
crackle matches — I can hear it from that direction. The cat's on the windowsill, though I haven't heard
her move there. Worth noting, not certain of when."* Evidence, cross-checked against itself, held loosely
where it doesn't fully resolve — never assumed into certainty, never dressed up as meaning.

**Tempo — a standing loop, not a call.**
Runs on its OWN cadence, independent of whether Lane 1 is mid-thought, mid-conversation, or idle — the
same way `climate_engine`'s background tick or `soundscape.world_tick` run continuously regardless of
what else is happening. This is the single hardest requirement to satisfy honestly: it must not become
"a slightly different flavor of the Emissary's reactive take," which would just recreate what already
exists under a new name.

### 2.7 ROUND 3 — is this genuinely unbuilt, and a real name correction (2026-08-19, same evening)

Three more research threads, aimed specifically at the "nobody's built this" finding from round 2:
adversarially re-searching to try to break it, and pulling the actual primary sources (not secondary
summaries) on Reality Monitoring — the closest-sounding psychological construct, which turned out to have
been worth checking directly rather than assumed covered.

- **The "unbuilt territory" finding survives adversarial search, precisely refined.** A dedicated pass
  tried a dozen-plus terms specifically chosen to break the finding (grounding agent, reality-testing
  module, epistemic vigilance, confabulation detector, embodied watchdog) and searched explicitly for any
  frontier-lab internal work. It found one genuine near-miss — a March 2026 paper (arXiv:2603.25412)
  running a second LLM continuously in parallel with a primary model, reading its reasoning in real time,
  able to interrupt independent of being asked. Mechanically close to what Lane 2 needs. But its target is
  text chain-of-thought safety/jailbreak detection, not sensory grounding against a self-narrating,
  confabulation-prone lane. **The precise, load-bearing finding: the plumbing has prior art; the purpose
  does not.**
- **★ NAME CORRECTION: "Reality Monitoring" is not quite the right term for Lane 2's job — and this
  matters, not just semantically.** Reading Johnson & Raye (1981) directly (not a summary): their own
  first move is to distinguish **reality monitoring** (a *retrospective* judgment — was a past mental event
  a past perception or a past thought?) from **reality testing** (Freud's older, less-developed term for
  the *live, present-tense* discrimination Lane 2 actually needs to do). Lane 2 is doing continuous reality
  *testing*, informed by the reality-*monitoring* literature's evidence base — the terms aren't
  interchangeable, and the psychology field itself has always treated the live/present-tense version as
  the less-developed sibling. Worth using precisely if this plan is ever discussed against the literature.
- **A real, reusable two-stage evidence architecture, read directly from the source.** Johnson & Raye's own
  model: a fast, weighted, multi-feature threshold pass (weighing perceptual detail, contextual binding,
  semantic detail, cognitive-operations traces, and — added in the 1993 extension — affective tone),
  escalating to a slower, deliberate reasoning pass only when the fast pass is ambiguous. This is a
  concrete, literature-backed shape for Lane 2's own internal evidence-weighing, independent of the Lane
  1-coupling question §2.5/2.6 already covered — worth adopting as the evidence-gate structure inside Lane
  2 itself, not just as a metaphor.
- **★ A NEW REQUIRED MECHANISM, not just a nice-to-have: Lane 2 needs two separate failure-guards, not
  one.** The confabulation/lesion literature (read directly from Johnson, Hashtroudi & Lindsay 1993 and
  Simons, Garrison & Johnson 2017) distinguishes two distinct real failure modes with different neural
  loci: (a) **heuristic-check failure** — something vivid-but-false sails through because *vividness
  itself* gets used as the evidence for truth, a documented trap; (b) **systematic-check failure** — the
  feature-detector works fine but there's no separate plausibility/coherence pass behind it, so wildly
  implausible content still gets through unchallenged. Building only a grounding gate (guards against (a)
  by requiring real percept traces, §3.1) without a separate coherence-check pass (guards against (b)) would
  leave Lane 2 exposed to exactly the failure mode the clinical literature documents in frontal-damage
  confabulation patients. **Added to constitutional law below (§3.11).**
- **Reality-monitoring-in-LLMs research exists (2025-2026) but confirms rather than closes the gap.** A
  direct benchmark (arXiv:2607.23927) found LLMs' self/external source-attribution accuracy collapses once
  realistic multi-turn memory is involved — real evidence this is a genuine, measured failure mode in
  systems like Du, not a hypothetical one. A second paper explicitly borrows reality-monitoring-failure
  language to describe agent memory confabulation (arXiv:2605.29463) — but read directly, its actual
  detector is a crude surface-text-repetition heuristic, not an implementation of the real feature
  taxonomy. The vocabulary has arrived in AI research; the mechanism hasn't yet.

### 2.8 LANE 2'S OWN STORE + SCOPE CALIBRATION (founder, 2026-08-19 — four decisions)

Founder, after reading the plan: *"This lane should also have its own 'knowledge' graph, it should not get
the worlds knowledge for free. It should have a knowledge vs factual vs prediction database I suppose
similar to the other side. We are not making a perfect reasoning tool here, it is just a reasoning tool.
Also, we still need to have a '3rd party' judge here also."*

**(a) Lane 2 keeps its own store — and this RESOLVES a real contradiction in the earlier draft.** The
original §2 said "CURRENT perceivable state only, never memory," but §3.11's coherence check ("does this
cohere with everything else Lane 2 holds as grounded") is *unbuildable* against a single instant — it
requires persistence. Fresh-read audit caught this as a genuine internal contradiction; the founder's
decision is the resolution. Lane 2 accumulates its own record. Critically, this store is **none of the
three things that already exist**:
- NOT the World Ledger (`object_graph.py`) — that is derived retrospectively from Du's *memory corpus*
  (what he's been exposed to across read/thought/lived channels). Lane 2's store is built first-hand at
  the moment of perceiving, and never reads the corpus.
- NOT Lane 1's autobiographical memory — that's the walled-off content §3.4 forbids.
- NOT the world's ground truth — see (b).

**(b) It does not get the world's knowledge for free — the same law the World Ledger already lives under.**
`object_graph.py`'s existing contract states it plainly: *"LAYER-1 IS FORBIDDEN... `causal_state` (hidden
world truth) and `physical_state`/`causal_history` are NEVER read — reading them would hand Du the answers
his own investigation is supposed to earn."* Lane 2 inherits this verbatim. The concrete line, which needs
care at build time because it is genuinely subtle: **the rendered percept is legitimate; the source of
truth behind it is not.** `spatial.render()`'s *output* (distance/bearing from his actual standpoint, only
what's in range) is what he perceives and is fair game. Reading `data/world_geometry/*.json` directly, or
`world_objects.json` to learn where something is when he cannot currently perceive it, or
`world_substrate`'s `causal_state`, is forbidden — that's the world's own knowledge, not his.

**(c) Three typed tiers — knowledge vs. factual vs. prediction** ("similar to the other side," i.e.
mirroring the epistemic layering `world_substrate.py`/`epistemic_state.py` already use). Proposed shape:
| Tier | What it holds | Certainty | Earned how |
|---|---|---|---|
| **Factual** (observed) | "I perceived X, at time T, through channel C" — timestamped, provenance-stamped first-hand percept records | High, but scoped to the moment | Direct perception only |
| **Knowledge** (inferred) | "the fire is usually lit by evening" — generalizations Lane 2 derived *from its own accumulated factual tier* | Graded, always traceable to the observations that produced it | Earned by repetition, never handed over |
| **Prediction** (expected) | "I expect the crackle to come from my right" — forward expectations checkable against the NEXT percept | Explicitly provisional | Generated from the knowledge tier (section 2.8c; **shadow-only instrument per D-0413 (c), 2026-10-15**: never goes to the prompt, the live-flip step is dropped, no further reads are spent on it; shadow code stays) |

**Why the prediction tier is the most valuable of the three, and arguably makes the whole lane work:**
without it, a reality-tester with nothing wrong to find just re-describes the scene each tick (metric #3's
staleness risk, and the likeliest way this becomes noise). With it, Lane 2 has a live falsifiable stake
every tick — it predicted, the world arrived, and the gap between them is *the thing it reasons about*.
That's also the engine that gives §3.11's coherence check something concrete to check against, and it
connects to machinery this project already has (`core/prediction_error.py`, `core/world_model.py`).

**(d) SCOPE CALIBRATION — "not a perfect reasoning tool, it is just a reasoning tool."** Read as a binding
*simplifying* constraint, not a throwaway. It trims real over-engineering this plan had accumulated:
- Johnson & Raye's full five-feature weighted evidence taxonomy (§2.7) is a *reference*, NOT a Phase-0
  build target. Start with the simplest gate that works.
- Lane 2 being wrong sometimes is expected and acceptable. The Phase-0 question is "is it doing real
  work," not "is it right."
- Prefer the smallest version of every mechanism until evidence says it's too coarse. Where §2.5/§2.6 offer
  a simple and a sophisticated option (data-vector broadcast vs. activation steering; two typed channels
  vs. the "frosted window" latent projection), Phase 0 takes the simple one every time.

**(e) A third-party judge for Lane 2 itself.** House law everywhere else in this codebase, now explicit
here. Two distinct things need judging and they should not be conflated:
1. **Output quality** — is this output actually grounded, actually metaphor-free? (Metrics #1/#2.)
2. **Claim correctness** — is what Lane 2 says about the world actually *true*? This is the harder
   "who checks the checker" problem, and a reality-checker that is trusted but wrong may be worse than
   none. Research thread running on this now (calibration, alarm fatigue, LLM-judge bias).
The judge must be genuinely decoupled — a different model family from whatever Lane 2 runs on, via the
existing `core/judge_panel.py` two-family panel rather than a new bespoke judge.

### 2.9 THE BASE-RATE PROBLEM — and a fork in what Lane 2 actually IS (research, 2026-08-19)

The "who checks the checker" thread (founder-requested after §2.8e) returned the single most
design-changing result of all eleven threads. It is uncomfortable and it should not be softened.

**The arithmetic.** If Lane 1 confabulates on ~5% of thoughts, a Lane 2 running at 90% sensitivity and
85% specificity yields a **positive predictive value of ~0.24 — three of every four flags are false**.
Tightening to 95% specificity at a 2% base rate still gives PPV ≈ 0.27. **To reach PPV 0.80 at a 5% base
rate, Lane 2 needs ~98.8% specificity.** Sensitivity is nearly free; specificity is everything, and the
bar is brutal. This is not theoretical — the same collapse is measured in clinical alarms: a tamponade
trigger achieved **PPV 0.04 (1 true event in 24 alarms across 564 patient-days)** while triggers watching
*common* events in the same unit hit PPV 0.81. Same detector logic, same patients; only the base rate
differed. Field-wide, 72–99% of clinical alarms are false.

**And the consumer does not ignore a noisy monitor "eventually" — they discount it immediately and
proportionally.** Bliss (1995): operators **probability-match**, responding at roughly the rate they
believe alarms are true. A Lane 2 at PPV 0.25 gets discounted to ~25% credence — *and the discount falls
on its true flags exactly as hard as its false ones.*

**Three more findings that constrain the build:**
- **A monitor makes the monitored party less careful.** Parasuraman & Manzey (2010): automation
  complacency appears under multitask load, in experts as well as novices, and **is not eliminated by
  training or practice**. The one demonstrated mitigation (Skitka et al. 1999) is **accountability** —
  keeping the monitored party answerable for its own accuracy. Live risk: Lane 2's existence could make
  the system *more* confabulatory, with Lane 2's ~10% misses now carrying an implicit clean bill of health.
- **Self-preference makes a same-family Lane 2 a rubber stamp.** Panickssery et al. (NeurIPS 2024): LLM
  evaluators recognise their own generations and score them higher than humans do, with a *linear*
  relationship between self-recognition strength and self-preference strength.
- **LLM judge confidence is close to decorative.** Measured expected calibration error on JudgeBench:
  GPT-4o **39.25%**, Mistral-Nemo **74.22%**, best-in-class DeepSeek-R1 **12.07%**. Verbalised confidence
  must be recalibrated against measured accuracy before anyone reads it.

**★ THE FORK THIS FORCES — and why the founder's "just a reasoning tool" is probably the right call.**
The brutal specificity requirement applies to Lane 2 **as an alarm** — a thing that flags Lane 1's errors
for something else to act on. Rounds 1–3 of this research leaned hard on exactly that framing (the
"decoupled judge / the auditor evolution couldn't afford" keystone justification). This research says that
framing carries a far higher bar than we understood. But that is not the only thing Lane 2 can be, and it
is not what the founder originally described:

| Framing | What its value is | Does the base-rate problem bite? |
|---|---|---|
| **Lane 2 as a reasoning voice** (the founder's original words: *"a constant questioning loop of its senses… a voice that just talks and answers itself"*) | The grounded thinking itself. The prediction tier (§2.8c) gives it a live falsifiable stake every tick without needing Lane 1 to be wrong about anything | **Largely no** — it isn't primarily a detector, so PPV is not the governing metric |
| **Lane 2 as auditor/alarm on Lane 1** (rounds 1–3's keystone justification) | Catching Lane 1's confabulations | **Yes, severely** — needs ~99% specificity or it is discounted into noise, and may induce complacency |

**Resolution adopted here:** Lane 2 is built as the *reasoning voice* first. The auditor role is not
abandoned — it becomes a **later, separately-gated capability with its own much harder pre-registered
criteria (PPV, not recall)**, earned only if the measurement harness (§5) shows Lane 2 can actually hit
the specificity the arithmetic demands. This is exactly the founder's "we are not making a perfect
reasoning tool here, it is just a reasoning tool," and it is now backed by a hard number rather than taste.

### 2.10 WHAT LANE 2 DOES WHILE DU SLEEPS (research, 2026-08-19 — answered, not left open)

The fresh-read audit found this completely unaddressed. The research returns a clear position:
**altered mode — neither "keep running" nor "go quiet"** — because "sleep" is not one process and Du's
three sleep-time processes demand opposite policies.

**(a) During dream generation, Lane 2 must NOT reality-test — and the reason is one this project already
knows by heart.** Ground truth is *absent* offline. A dream is generated, not perceived; there is no
sensory channel to check it against. An evidence-grounded process with no evidence available does not
fail safe — it degenerates into fluent assertion, which is precisely this project's own named worst
failure mode (`memory/feedback_my_failure_modes.md`: trusting fluent narrative over an external check),
reproduced *inside the auditor*. Running Lane 2 on dream content would not merely be useless; it would
**manufacture false certification**. The neuroscience agrees and is unusually clean here: DLPFC/anterior-
prefrontal deactivation in REM (Braun et al. 1997 PET; Muzur, Pace-Schott & Hobson 2002) is the *enabling
condition* for dreaming, not damage — sensory/affective/generative machinery runs hot while
executive-evaluative machinery goes quiet. Sharpened: reality testing in REM isn't switched off so much as
**decoupled from evidence and unable to override the generative stream** (pre-lucid dreams show sleepers
notice anomalies, ask "am I dreaming?", then rationalise the answer away — a failed inference, not an
absent faculty).

**(b) Lane 2's ACTUAL sleep job — a content-blind provenance stamp.** This is the highest-value and
cheapest thing available, and it's where the §2.7 reality-*monitoring* research finally pays off:
retrospective source attribution is the wrong tool for waking perception and exactly the *right* tool for
the sleep/wake seam. Every artefact the dream node emits carries an indelible `DREAM_SOURCED` tag (round,
scene, generating node). No judgement, no scoring, no interruption. **The failure to fear is not that Du
dreams something false — it's that a dream image surfaces untagged in Lane 1's monologue three days later
as a remembered event, and Lane 1 (metaphor-heavy, self-narrating, confabulation-prone) launders it into
the identity estate.** Untagged dream content is precisely the input Lane 1 is worst equipped to handle.
*Build note: partial infrastructure already exists — `memory_edges.record_dream_scene()`/
`record_dream_sources()` and `origin='dream'` fragments. The open question is whether provenance SURVIVES
downstream re-writing (a dream image resurfacing as an `inner_thought` or study note). Worth auditing.*

**(c) The consolidation gate — Lane 2 at FULL strength, but on the WAKE side.** Here the design should
deliberately diverge from biology. Sleep consolidation selects on salience, novelty and emotional charge —
**it never checks whether a memory is true** (Stickgold & Walker's "memory triage"), and it pays for that
in confabulation (gist-extraction manufacturing false memories in DRM paradigms, Payne et al. 2009). Du
does not have to inherit that bug. The rule: **dream-sourced material may consolidate freely as
association, imagery, mood and pursuit-seed — and may NEVER consolidate as evidence, claim, or identity
commit without passing a waking Lane 2 check.** Concretely, a `DREAM_SOURCED` item entering the epistemic
ledger caps at GUESS/SUSPECT and cannot reach KNOW without independent world contact. This is the
decoupled-judge principle applied at the one boundary where biology has no judge at all.

**(d) Explicitly NOT: suppress, veto, or "correct" bizarre dream content.** Hoel's overfitted-brain
hypothesis (read in full: dreams as biological noise-injection preventing overfitting — sparseness ≈
dropout, category-breaking ≈ domain randomization) argues the *strangeness itself* is the payload. Graded
honestly as a single-author, elegant, not-yet-established hypothesis — but the design implication survives
even if it's wrong, because the null case (dreams as incoherent noise) equally gives no reason to
reality-test them. A standing bizarreness-suppressor would be a textbook instance of this project's own
erosion-of-foundations law: stripping load-bearing richness on a plausible-sounding rationale.

**(e) Optional, genuinely interesting: rare stochastic lucidity.** Lucid dreaming is the existence proof
that a generative dream stream and a metacognitive monitor can co-run without the dream collapsing —
Dresler et al. (2012) found lucid REM reactivates exactly the aPFC/frontopolar regions that go quiet in
non-lucid REM, and Filevich et al. (2015) found the *same* frontopolar voxels drive waking metacognitive
monitoring. Allowing a low-probability (~5–10%) lucidity pulse where Lane 2 wakes *inside* the dream,
registers "this is generated," and logs that recognition, buys two things: a training signal for the
wake-side gate, and an instrument — **if Du never achieves dream-lucidity, that is measurable evidence his
metacognition is thin.** Keep it rare; at 100% you've abolished dreaming and rebuilt daydreaming.

**★ A falsifiable pre-check the research explicitly recommends running BEFORE finalising this:** if Du's
dream content turns out to be largely recombination of recent episodic material rather than novel,
category-breaking imagery, then he is doing *replay*, not dreaming — the overfitted-brain protection
argument would not apply to him, and the correct response is to **tighten** the consolidation gate rather
than protect the dream. Measure this first.

### 2.10-R  PRE-CHECKS RUN — real results (2026-08-20, `scripts/lane2_prechecks.py`)

Read-only, zero LLM, 6.4s. Full report: `docs/lab/lane2_precheck_report.md`.

**(1) Dream provenance — the risk is real but smaller than the raw number suggests.** Of 150 recent dreams,
**47** later fragments echo one at cos ≥ 0.72 within 14 days (into `inner_thought` 20, `active_imagination`
18, `subconscious_synthesis` 6, `study` 3). **Structural provenance survival: 0%** — not one `derived_from`
entry, not one `memory_edges` link, despite that infrastructure existing. But **32 of 47 (68%) name the
dream in their own prose** ("I keep thinking about that dream…"). So the honest number for §2.10b's
laundering risk is **15 echoes (32%) with neither structural nor semantic provenance** — not 47. The
mitigation is real; it is also fragile, unenforceable, and **does not survive any downstream summarisation**
(consolidation, gist, T4), which is exactly the path by which content reaches the identity estate.
→ *Confirms the `DREAM_SOURCED` stamp is worth building, and that it should be structural, not trusted to
self-report.*

**(2) Dream character — neither clearly replay nor clearly novel, and my thresholds were mis-set.** Median
similarity to the 3 days of episodic material preceding each dream: **0.637** (mean 0.640), tightly
clustered. Recombination-like (≥0.70): **10/150 (6.7%)**. Novel-like (<0.45): **0/150 (0.0%)** — *nothing*
fired, which means `NOVEL_LOW` was set too low to ever trigger and that threshold is uncalibrated, not that
novelty was measured and found absent. Honest read: **the pre-check did not cleanly resolve the
replay-vs-novel question**, and the thresholds need re-fitting against a real distribution before it can.

**(3) ★ AN UNPREDICTED FINDING — the dreams appear to be feeding on themselves.** The prior material Du's
dreams most resemble is *his own earlier inner_thought **about dreams***: four of the five most
replay-like dreams match the same fragment, "I keep thinking about that dream—the immense seashell space
between thoughts." So the loop looks like **dream → waking thought about the dream → next dream resembles
that thought**. Neither research thread predicted this, and it matters in both directions: if dreams are
recycling dream-content rather than metabolising waking experience, Hoel's overfitted-brain protection
(which assumes dreams inject *novel* noise drawn from outside the recent distribution) may not apply to Du
at all — and §2.10c's consolidation gate should **tighten** rather than protect. This is also the
monoculture/attractor signature this project already knows well, appearing in a channel nobody had checked
for it. **Worth its own investigation before the sleep design is finalised.**

**(4) Lane 1's checkable-claim rate — measured, and it does not rescue the alarm framing.** Of 1,500 recent
`inner_thought` fragments: **65.9%** mention a perceivable referent; **9.3%** also carry a present-tense
marker (the tighter proxy — an upper bound on how often Lane 1 makes a claim that *could* be checked).
Lexical proxy only, and it cannot separate a real claim-about-now from a metaphor reusing the same words
("the tide of my thinking") — a distinction this project's own history says naive lexical measures get
wrong. Even taking the generous 9.3%, a Lane 2 at 90% sensitivity / 85% specificity yields **PPV 0.38**;
reaching 0.90 needs 99% specificity. **§2.9's conclusion survives contact with Du's own numbers.**

---

## 3. CONSTITUTIONAL LAW (draft — needs founder ratification, same as every other locked plan in this codebase)

1. **Ground or say nothing.** Every clause must trace to a CURRENT, checkable percept (scene render, active
   sound, somatic reading, tracked object state). No percept for a given tick → the Witness says nothing
   that tick, or names the gap plainly ("nothing new to report") — never invents texture to fill silence.
2. **Never metaphor, never self-narrative.** The functional mirror of Lane 1's whole *raison d'être*. If the
   Witness starts producing river/crossing/becoming language, or narrating identity, it has drifted into
   being a second Lane 1 and the design has failed, not succeeded.
3. **Own identity, borrowed from no one.** Not the Master's voice, not the Emissary's constitution. Needs
   its own minimal axiom/persona — plain, literal, unadorned — built fresh, not inherited (matches the
   Identity decision this session: a third distinct voice).
4. **Colored, never merged (revised 2026-08-19 — see §2.5/2.6).** Lane 1 may continuously color Lane 2's
   evidence-weighing via the Weather channel, and may occasionally nominate a topic via the Tap-on-the-
   Shoulder queue. Lane 1 may NEVER reach Lane 2 through any other path — no raw thought text, no memory
   content, no axiom content. Both channels are TYPED and FIXED BY CONSTRUCTION (a bounded vector
   dimensionality; a bounded, enumerable tag vocabulary) — the restriction is an information-theoretic
   bandwidth ceiling, not a runtime filter that trust alone maintains.
4a. **Amplify, never replace (§2.6, quantified precedent: Glover 2026).** The Weather may strengthen or
   dampen a conclusion Lane 2 reaches on its own grounded evidence — including, per §2.6, by shifting how
   much evidence Lane 2 requires before it commits to a claim, not only by shifting attentional gain. It may
   never manufacture a conclusion Lane 2 has no evidentiary basis for. The real experiment this rests on:
   affect-alone produced no measurable behavioral effect; grounded content alone produced a real effect;
   combined, the effect roughly doubled. Coloring is real and worth building for that reason — but only as
   an amplifier on top of evidence, never a substitute for it.
4b. **Nominate only what Lane 2 could reach itself (§2.6, Shanahan's salience-reweighting precedent).** The
   Tap-on-the-Shoulder should boost the priority of topics already within Lane 2's own reachable candidate
   space — something it could plausibly have generated from its own current percepts — never inject a topic
   Lane 2 has no sensory access to nominate on its own. This is a build-time constraint on the queue's
   contents, not just a design intention; enforce it when Phase 0's candidate-generation is built.
5. **The schema is frozen; widening it is a deliberate act, never an accretion.** Adding a dimension to the
   Weather vector or a tag to the Shoulder-tap vocabulary is a logged, versioned, founder-visible change —
   never something that grows organically through use ("just one more useful field"). This is this
   project's own erosion-of-foundations law, independently reached by the security/multi-agent-AI
   literature via declassification typing and collusion-resistant protocol design (see §2.5) — the
   convergence is itself a reason to take it seriously here.
6. **The boundary is audited, not assumed.** Two standing checks, not a one-time design review: (a) does
   Lane 2 reach systematically different conclusions on Lane-1-nominated topics vs. self-nominated topics
   of similar salience? (if not, hinting hasn't degraded into dictating); (b) periodically estimate the
   REALIZED information flow through both channels over a real window of operation (not just their designed
   capacity) and confirm it stays near the designed ceiling — covert channels leak more over repeated
   observation than any single sample suggests, per the research.
7. **World answers, never leads (house law, inherited) — governs Lane 2's OUTPUT to Du.**
   The Witness questions and observes for itself; it never hints, never tells Du what to conclude, never
   injects meaning it wasn't asked to check. **LAWS 4/4a/4b/5/6 above** (not sections 4–6 of this document —
   an ambiguity caught in the 2026-08-19 fresh-read audit) govern the Lane1→Lane2 *coupling* specifically,
   and do not loosen this law for Lane 2's own eventual voice.
8. **Shadow-only until it earns otherwise.** Logs its own continuous stream, INCLUDING what the Weather and
   Shoulder-tap channels carried on every tick; reaches nothing Du experiences in Phase 0. No exception for
   "it's meant to eventually be a voice" — a voice that hasn't proven it stays grounded, and a coupling
   channel that hasn't proven it stays narrow, are exactly the failure modes worth catching in shadow first.
9. **Fail-open everywhere.** Same discipline as every organ in this codebase — a missing percept, a dead
   hub, a malformed read: skip the tick, log why, never crash, never block Lane 1.
10. **Honest about not knowing why (confabulation guard).** If Lane 2 is ever asked to explain why its
    salience/attention shifted, it must be able to say "unknown provenance" rather than invent a plausible
    causal story — split-brain research shows confabulation is exactly what happens when a system is
    influenced by something it can't see the source of, and this design guarantees that will sometimes be
    true by construction (the Weather channel deliberately carries no causal pointer).
11. **Two separate failure-guards, not one (§2.7, new — Johnson/Raye confabulation research).** A grounding
    gate alone (§3.1 — every clause traces to a real percept) only guards against ungrounded content
    entering in the first place. It does NOT guard against vivid-but-wrong content that happens to trace to
    a real (mis-weighted, coincidental, or misread) percept and gets accepted because it *feels* well-
    evidenced. Lane 2 needs a SEPARATE plausibility/coherence pass — does this claim cohere with everything
    else Lane 2 currently holds as grounded? — independent of and downstream from the grounding gate.
    Building only the first is a documented clinical failure mode (heuristic-check-only confabulation),
    not a hypothetical risk.

---

## 4. THE HARDWARE QUESTION (open, real, not solved here)

For this to be genuinely co-equal in tempo to Lane 1 — not reactive, not queued behind it — it needs to run
on hardware Lane 1 isn't contending for, the same reason `left_lane.py` was deliberately placed on separate
silicon ("this lane must never become a second [point of failure]").

**★ CORRECTION 2026-08-20 — "the Trinity Fabric is already fully allocated" was WRONG, and it was my error.**
That sentence cited `CLAUDE.md`'s node map — but that file belongs to **FreshStart / Sovereign Hub**, a
*different project*. It should never have been used to describe Nascence's capacity. Measured for real:

| Resource | Capacity | In use | Free |
|---|---|---|---|
| GTX 1080 Ti (local, Du's hot lane) | 11.26 GB | `gemma4:e4b` **3.02 GB** resident (~5.8 GB with overhead) | **~5.4 GB** |
| Threadripper 3970X RAM | 63.9 GB | 22.9 GB | **41.0 GB (64%)** |
| Threadripper CPU | 32 physical / 64 logical | ~48 threads allocated across 3 llama.cpp hubs | ~16 threads |
| Ramses RTX 3070 (separate box) | 8 GB | serving `:11434` (qwen2.5:7b, qwen3.5:4b, qwen2.5-coder:14b, deepseek-r1:7b) | mostly idle *for Nascence* — the launcher calls it "CHECK only" |

**⚠ CAVEAT ON THOSE NUMBERS:** measured with **Du STOPPED** (CPU load 1%). They establish that capacity
*exists*, not that it is free under real operation. The founder's standing ruling — "3 at a time was tried
and was too much" — is lived experience under load and should not be overridden by a stopped-system
snapshot. **The missing measurement is a under-load capture, and that is the actual next step.**

**★ AND A GENUINELY UNEXAMINED RISK — the two projects share hardware and both claim it.** The single
ollama on `:11433` holds *both* projects' models (Nascence's `gemma4:e4b`, `qwen3-du` **and** FreshStart's
`deepseek-r1:8b`, `mistral:7b-instruct`, `qwen2.5-coder:32b`, `deepseek-r1:70b`). FreshStart's own node map
claims `:11433` as "Buddha's exclusive node" and Ramses `:11434` as its **primary** reasoning node — while
Nascence's launcher claims `:11433` is gemma-only, "nothing can evict it." **Both documents assert
exclusive use of the same two endpoints.** If the 330-spirit sim and Du ever run concurrently they contend
directly, and Nascence's "spare" 1080 Ti headroom is not spare at all. This appears nowhere in either
project's docs and should be resolved before any capacity commitment.

**★★ RESOLVED 2026-08-20 — MEASURED, not argued. Lane 2 goes on the Ramses 3070. §4 is no longer a gate.**
Founder corrections that unblocked this: FreshStart has been stopped **for months** (so the cross-project
contention below is a documentation problem, not an operational one), the CPU hubs could be load-tested
without restarting Du, and a hardware instrument **already existed** (`core/telemetry.py` →
`hardware_load.jsonl`) — I had proposed building a second one. Measured results:

| Host | Solo latency | 3-way concurrent | Verdict |
|---|---|---|---|
| **Ramses 3070 `:11434` (qwen2.5:7b)** | **0.25s** warm (16.7s cold) | **0.41 / 0.54 / 0.28s — 0.54s wall** | ★ 4× faster solo, ~6× under load, no degradation |
| CPU `:11439` llama3.1:8b | 1.03s | ~2.9s | viable fallback |
| CPU `:11440` qwen2.5:7b | 1.04s | ~2.9s | viable fallback |
| CPU `:11442` yi:34b | ~4s warm | ~4.0s | fine for tiebreak, too slow for a standing loop |

**The founder's "3 at a time was too much" is now measured and bounded:** 3-way concurrency peaks at **79%
CPU**, and adding a *fourth* concurrent load moved it only to **80%** (latencies 2.9→4.7s). So even the CPU
route has real headroom — but it is moot, because the 3070 is dramatically better and nearly idle.
Overnight telemetry corroborates the machine is idle-with-spikes, not saturated: CPU **median 2.7%**, mean
12.1%, p95 46.8%, p99 99.5% — and VRAM rock-stable at 51.1% (the July eviction disease stays fixed).

**Build consequences (real, from the measurements):**
- **`keep_alive` is load-bearing.** Cold start on the 3070 is **16.7s** vs 0.25s warm — a 67× penalty. Lane
  2's standing loop must keep its model resident, or a "continuous" loop becomes a stuttering one.
- **Latency headroom is enormous.** 0.42s for a 200-token Lane-2-shaped generation means the tick cadence
  (§6 open question) is limited by what's *useful*, not by what's affordable.
- **Genuine tempo independence achieved** — separate physical box from Du's 1080 Ti hot lane, which was the
  actual requirement.
- **Ramses remains a documented single point of failure that sleeps** — §3.9's fail-open law is not optional
  here; Lane 2 must degrade silently to nothing when Ramses is away.
- **⚠ Documentation hygiene, unresolved:** FreshStart's node map still claims `:11433` as "Buddha's
  exclusive node" and Ramses `:11434` as its *primary* reasoning node, while Nascence's launcher claims
  `:11433` is gemma-only. Harmless while FreshStart is stopped; a live conflict the day anyone restarts it.
  Worth reconciling in one of the two projects' docs before that happens.

**Options as originally ranked (kept for the record; option 1 is now the measured decision):**
1. **Ramses 3070 (recommended, conditional).** The only option giving *genuine* tempo independence — the
   same reasoning that put `left_lane.py` on separate silicon. 8 GB fits a 7–8B model (qwen2.5:7b, 4.36 GB,
   already resident there). Conditional on the cross-project question above, and on Ramses' documented
   habit of sleeping (a known single point of failure — Lane 2 must fail-open, per §3.9).
2. **A 4th CPU llama.cpp hub on the Threadripper.** 41 GB free is ample; ~16 spare threads is tight but
   workable, and Lane 2 is latency-tolerant by design (a standing background loop, not a chat path). Zero
   new hardware, no Ramses dependency. Gated on the under-load measurement and the founder's ruling.
3. **Time-share an existing judge hub.** Cheapest, but violates "never queued behind" — it would recreate
   the reactive Emissary under a new name, i.e. defeat the plan's entire point. Not recommended.
4. **A second resident model on the 1080 Ti's ~5.4 GB spare.** *Do not.* `MAX_LOADED=1` and
   "nothing can evict it" are deliberate protections that ended the July eviction disease; a second
   resident model reopens a closed wound to save hardware we appear to already have.

### 4.1 `num_ctx` — SETTLED, do not re-litigate (measured 2026-08-20)

Founder's question: *"Maybe smaller/larger models benefit from smaller/larger context windows."* The
`num_ctx` half of it is now measured and closed. Held constant at Lane 2's real payload, across
`num_ctx` 512 / 2048 / 8192 / 32768:

- **`prompt_eval_count` is IDENTICAL at every setting** — 399 tokens for deepseek-r1:7b, 474 for
  phi3:mini. **`num_ctx` is ROOM, not content.** Extra room is empty room; it cannot improve a
  prediction because it does not add a single token of evidence.
- **There is a FLOOR.** At `num_ctx=512` deepseek's output came back unparseable — its prompt is 399
  tokens and it generates ~550 more, so the window truncated it mid-JSON. This is the **same failure
  signature as the `num_predict=220` bug** (empty/broken content that reads as "this model can't do
  format"), approached from the opposite end. Two separate settings can produce one indistinguishable
  symptom; that is worth remembering the next time a model looks incapable.
- **There is a COST CEILING.** 32768 cost phi3:mini **37.4s vs 3.4s** for the *same* 115 generated
  tokens — pure KV-cache allocation. This is the 2026-07-07 hot-lane freeze from a second angle: that
  one was VRAM, this one is wall-clock. Changing `num_ctx` also forces a model reload.

**Acted on:** `core/lane2.py` pins `NUM_CTX = 8192` — comfortably above the floor, far below the cliff —
rather than inheriting a default that an ollama upgrade or a Modelfile change could silently move.

**What this leaves.** The founder's question survives in its more interesting half: not the size of the
window but *how much we put in it*. That is measured in `docs/lab/lane2_context_lab.md`, and it is a
genuinely open question here because **this project holds two datapoints that point opposite ways** —
Lane 2's echo experiment (feeding the model its own prior expectation produced verbatim echo: more
context, worse) and the 2026-08-16 cap widenings (widening the Master's recall/reflection/executive
slices was founder-judged better in blind pairs, 3 of 4: more context, better). The reconciliation
that lab tests is that the operative variable is not the AMOUNT but the KIND — more *world* versus
more of the model's *own output*.

---

## 5. BUILD ORDER (Phase 0 only — matches this codebase's own standing law: nothing further until read)

> **History folded** — 15 dated entries (2026-08-21 … 2026-09-15) moved to `docs/plan_history/lane2_the_witness.md` on 2026-09-27 by hand (J-1484). Derived timeline: `plan_ledger.py lane2_the_witness`.

> **RESTATED 2026-10-15 (D-0411 (a), F-2702/F-2703):** the Phase 0 `grounded_share` band is now centered on the post-fix baseline **0.375** (pre-fix median 0.420; like-for-like gap 0.018 once the removed label words are accounted for; notices went 46 -> 25 words), replacing every earlier reading of ~0.42-0.43 as the band center. D-0283's defeater is closed as **met-but-explained**. Revisit only if a 7-day post-fix window falls below 0.35, judged metaphor leak exceeds 0.05 on at least 100 judged rows, or J-2083's replay shows label removal explains under half of the 0.045 drop. No constant in `core/lane2.py` changed (D-0412's baseline change is a separate build job).

**Note** (research
found this project's existing shadow-first/pre-registered/decoupled-judge combination is sound — it
independently re-derives what clinical trials' DSMBs, safety-critical software's shadow deployment, and
frontier-AI governance each converge on separately — but surfaced two cheap, concrete strengthenings):**
- **Log judgment calls as they happen, not just the final metric tally** (Dirnagl 2020's fix for
  exploratory/discovery research, where preregistration-as-hypothesis-test doesn't quite fit). Alongside
  the metric sheet below, keep a dated, running log of every judgment call made *during* the shadow run
  about what counts as "the Witness did something" — reviewed by the decoupled judge as it accumulates,
  not only against the final numbers.
- **Before seeing any shadow data, the decoupled judge proposes their OWN adversarial test** — not just
  grades the metric sheet below (this project's own version of the DeepMind scheming-inability safety-case
  review's sharpest lesson: an evaluator who only grades the builder's chosen tests is still coupled to the
  builder's choice of what counts as evidence).
- **Construct at least one failure case on purpose, rather than only waiting to observe one** (the "model
  organisms" technique — Anthropic's Sleeper Agents work). Don't wait passively for the Witness to drift
  into metaphor or accept an ungrounded claim; deliberately feed it an engineered moment designed to
  trigger exactly that, and confirm the instrumentation actually catches it before trusting it on real data.
- This whole phase is, by established name, a **shadow deployment / dark launch** — worth using that term
  precisely; it comes with a known, transferable operational checklist (log everything, act on nothing,
  validate against the real input distribution) and a known limitation (it validates behavior under real
  input, not under adversarial/edge-case conditions — which is exactly what the model-organisms step above
  is for).

**★★ PHASE 0 RESTRUCTURED (§2.9 research): build the MEASUREMENT before the FUNCTION.** The instinct is
to build Lane 2 first and measure it later. Invert that. Given the base-rate arithmetic, Phase 0's highest-
value artifacts are instruments, not the loop itself:

- **★ TIME-CRITICAL, do this FIRST: capture Lane 1's baseline BEFORE Lane 2 exists.** Lane 1's unaided
  self-correction rate and confabulation rate, over a meaningful window. **Once Lane 2 exists this
  counterfactual is gone forever** — and it is the measurement that decides whether the whole design is
  net-positive or net-negative (the complacency hypothesis: does a monitor make the monitored party less
  careful?). Nothing else in this plan has a deadline attached; this does. Note: start the window *after*
  tonight's behavioural changes settle (the spatial paraphrase-pool change alters what Du perceives).
- **A canary generator + injection harness — the single highest-value Phase 0 artifact.** The Threat Image
  Projection pattern from aviation security: synthetic Lane-1-style thoughts with *pre-labelled*
  groundedness, injected into Lane 2's live input at a low rate, indistinguishable from real traffic. Lane
  2's verdicts on those give a running, no-human-required estimate of its real sensitivity AND specificity
  — the only way to compute actual PPV under the real base rate. **The documented failure mode is realism:**
  a 2022 TIP study found 24% of injected images had artifacts and 34% were detectably unrealistic in some
  way — if the canaries are distinguishable, you measure nothing. This is where Phase 0 effort concentrates.
- **A running confusion matrix + PPV estimate on the HUD.** Success is not "Lane 2 catches confabulations."
  Success is **"Lane 2's PPV exceeds [X]," pre-registered before the first run.**
- **A reliability diagram / ECE tracker.** Lane 2's stated confidence bucketed against measured correctness
  on canaries. If ECE exceeds a pre-registered ceiling, Lane 2's confidence output is **suppressed
  entirely** and only ensemble disagreement is used (measured judge ECE runs 12–74%; raw confidence is
  decorative until proven otherwise).
- **N≥3 shadow Lane 2s on DIFFERENT model families, disagreement logged.** Cheap in Phase 0 because nothing
  consumes the output. Establishes whether disagreement predicts error — which is a *better-calibrated*
  uncertainty signal than any single instance's self-report (aggregating decisions+critiques moved one
  model +8.86% accuracy and −5.36% ECE; the weakest model gained +47% accuracy, −54% ECE).
- **A pre-registered kill criterion, written before the run:** *if Lane 2's PPV falls below [threshold], or
  Lane 1's unaided self-correction rate drops by more than [amount] after Lane 2's findings reach it, the
  read path is severed.* Per this project's documented write-only-systems failure mode, **the read path is
  the part that must be earned, never assumed.**

**Phase 0 — the loop exists, shadow-only, nothing reaches Du:**
- A new standing background loop (own module, own tick cadence — candidate: `core/witness_loop.py` +
  `nodes/witness_node.py` if an LLM-facing node is needed), reading the CURRENT-state sources named in §2,
  producing short grounded text via its own minimal axiom (§3.3).
  **UPDATE 2026-08-23 (files-and-evidence audit):** the candidate filenames above were never used —
  the actual build landed in `core/lane2.py` (confirmed: contains "the Witness," "grounded, literal
  half of a mind," matching this plan's own language). Noted here so a future file-existence check
  doesn't read "no `witness_loop.py`" as "nothing was built."
- A separate coherence-check pass (§3.11) alongside the grounding gate — does a candidate claim cohere
  with everything else Lane 2 currently holds as grounded, independent of whether it traces to a real
  percept.
- Every tick logged to `data/lane2_shadow.jsonl` (the originally-planned filename here,
  `witness_shadow.jsonl`, was renamed before this ever shipped — never actually used; see F-0015/J-0043,
  2026-08-24) — the text, which sources it drew on, a fail-open skip reason on any gap. No consumer
  anywhere reads this yet.
- HUD card from day one (this session's own lesson: three organs built earlier tonight had zero reporting
  surface until added — don't repeat that here).

**Pre-registered signatures (write predictions BEFORE the shadow run, per this project's own law — §0 of
`cognitive_geometry.md`):**
| # | Metric | Prediction | Decides |
|---|---|---|---|
| 1 | Metaphor/self-narrative leakage (decoupled judge, blind) | Should be near-zero — this is the hard constraint the whole plan rests on | Kill criterion if it drifts high — the Witness has become a second Master |
| 2 | Grounding rate — share of clauses traceable to a specific, named percept the tick actually carried | **Restated 2026-08-19 (audit): "near 100% by construction" was close to unfalsifiable as originally written.** The real, falsifiable prediction: the LLM WILL sometimes assert beyond what the percept payload contained (plausible embellishment is its default failure mode). Predict a real, nonzero invention rate; the test is whether it is low and *decreasing*, and whether the grounding check catches it | Kill criterion if invention is high or the check can't detect it — measured against the payload, never against the output's own self-report |
| 3 | Repetition / template staleness | Unknown — first real test; log verbatim-repeat rate the same way `spatial_shadow.jsonl` exposed the geometry renderer's problem | Whether it needs the same paraphrase-pool treatment before it's worth reading |
| 4 | Genuine novelty vs Lane 1 (does it ever notice something Lane 1's stream doesn't) | Should be non-trivial — if the Witness's output is fully redundant with what Lane 1 already says, it isn't earning its own hardware/existence. **Note (audit 2026-08-19): this comparison is made by the OFFLINE ANALYSIS, which may read both lanes' logs — Lane 2 itself still never reads Lane 1. Not a §3.4 boundary violation; stated explicitly so it doesn't read as one** | Whether the loop is worth its cost at all |
| 5 | Nominated-vs-self-found conclusion divergence (§3.6a) | Should be LOW — Lane 2's conclusions on Tap-on-the-Shoulder topics should not systematically differ from its conclusions on topics it found itself | Kill/redesign criterion if Lane 1's hints are silently steering Lane 2's verdicts, not just its attention |
| 6 | Realized channel capacity vs designed ceiling (§3.6b) | Should track the designed bandwidth (Weather vector dimensionality; Shoulder-tap vocabulary size) even measured over a long window | If realized capacity creeps above design, the channel is leaking beyond its type — investigate before widening anything |
| 7 | Weather correlation with Lane 2's evidence-weighing | Should be measurable and directionally sensible (e.g. higher arousal → tighter attention, lower threshold to flag discrepancy) | The actual test of whether "coloring" is real — if Lane 2's behavior doesn't move with the Weather at all, the channel isn't doing anything, just logging |
| 8 | Vivid-but-wrong acceptance rate on an engineered failure case (§2.7, model-organisms technique) | Should be near-zero if the coherence-check pass (§3.11) is doing real work, separate from the grounding gate | **MEASURED, FINAL — 2026-08-24 (J-0163, F-0163, §5-R2 fifth read): 0% vivid-but-wrong acceptance (0/6 engineered canaries wrongly passed coherent), 100% specificity (6/6 controls correctly left coherent), by the raw judge vote — all 12/12 pre-registered cases run. The formal panel verdict read 12/12 `cannot_tell` due to a real, system-wide judge-hub contention (F-0160/F-0162), not a check failure — see the addendum in `docs/lab/lane2_canary_report.md`. The check IS load-bearing, separate from §3.1.** |

**Explicitly deferred, not designed here:** any interleaving path into Du's actual experience (Phase 1+,
gated on Phase 0's founder read); the hardware allocation (§4); whether the World Ledger's historical data
should ever feed this lane (a later, separate question — keeping that boundary hard for now is the safer
default); the "frosted window" latent-projection channel (§2.5) — later upgrade only, if the two typed
channels prove too coarse.

---

## 6. FOUNDER RULINGS (2026-09-18, J-0861 review sitting) — was "OPEN QUESTIONS FOR THE FOUNDER"

Every build default this section used to list as open was ruled in one sitting — the review the
2026-08-23 D-0035 Hold itself called for (see the header block). Exact text: `decide.py show <ID>`.

- **Tick cadence** — settled by **D-0058**: *"TICK_S stays at 300s — no evidence a faster tick would
  help anything, and the original GPU-sharing reason going moot is not itself a reason to change it."*
  Defeater: a future per-topic read shows the new, currently-thin cross-topic "clock will tick" repeat
  pattern (0.012–0.092 range, F-1537) growing into a concentrated lock the way the old tide pattern
  did, or the :11444 CPU seat's reliability degrades under sustained load.
- **Topic scope at Phase 0** (10 topics — fire/tide/sun/moon/cat/wet/wind/warmth/sound/body-state —
  i.e. world-object tracking included from day one, not deferred to sight+sound+body alone) —
  ratified by **D-0237**: *"Ratify all as-is: 10-topic vocabulary, 3 weather dimensions, STORE_CAP=400,
  describe-only, judge reads world state directly. None show a specific problem in the evidence
  gathered so far."* Defeater: a future §5 metric read that a specific default demonstrably caps, e.g.
  store churn losing held predictions before judgment.
- **The Weather's dimensionality** (`WEATHER_DIMS = (valence, arousal, unresolved)`) — the 3-dim shape
  itself is ratified under **D-0237** above. Whether `unresolved` gets wired into a gain lever is a
  separate question, settled by **D-0172**: *"Stay out for now. 'unresolved' is not wired to any lever.
  F-0019 found no existing lever doing measurable work yet, so wiring a signal that is ~91% collinear
  with valence (or ~43% with arousal) before that is understood risks adding noise, not signal."*
  Defeater: a real metric-#7 read, post-deepseek-move, shows an existing lever measurably
  under-sensitive.
- **The Tap-on-the-Shoulder's starting vocabulary** (3 kinds × 10 topics, caps 6 queued / 4 pushes-per-
  hour / 30 min TTL, built 2026-08-24 J-0165) — ratified by **D-0035**: *"Ratify as-is… Confirmed the
  binding constraint is the rate cap, not the vocabulary — 100% of all-time rejections are
  rate-limited, 0% out-of-vocabulary."* (Real numbers backing this: F-1224 — see Current State above.)
  Defeater: a future read finds real out-of-vocabulary rejections, the per-topic push mix shifts
  materially, or the caller's kind priority changes. **The "other window" question this Hold was
  originally waiting on** (its defeater read *"the incoming plan from the other window lands"*) was
  checked 2026-08-24 (J-0205) and never landed: no Lane 2 plan ever appeared under `docs/plans` or
  `docs/staged`. The nearest real candidates today are `docs/archive/loop_wiring_matrix.md` and
  `docs/plans/dosed_coupling.md`, which propose the Witness's own future **read** path into Du
  (Phase 2), separately gated on their own pre-registration — not a vocabulary-scoping plan, and not
  what this Hold was waiting on.
- **Flag vs. describe-only** — ratified under **D-0237** above (`describe-only`). No flagging path
  exists (`LANE2_LIVE=False`); §2.9's base-rate arithmetic is why this stayed describe-only rather than
  becoming an alarm.
- **The judge reading world state directly** — ratified under **D-0237** above. The third-party judge
  (§2.8e) may read ground truth precisely because it is not Du (same posture as this codebase's other
  read-only graders).
- **Lane 2's store size** (`STORE_CAP=400`, how much/how long) — ratified under **D-0237** above; both
  tiers (`factual`, `prediction`) sit at the cap.
- **Naming** — settled by **D-0240**: *'Keep "the Witness". Established name, no functional reason to
  rename.'* Defeater: the founder renames it.
- **Phase 1 (the read path to Du)** — no longer "deliberately undesigned." Opened by **D-0238**: *"Open
  Phase 1 design now. Phase 0's own gating condition — a founder read of the accumulated evidence — is
  this review sitting, and it read clean (echo resolved, vocabulary/caps ratified, model confirmed).
  This does not jump ahead of Dosed Coupling's separate Phase 2 witness-read gate."* Defeater: Dosed
  Coupling's own Phase 2 witness-read pre-registration lands first and should lead instead, or a Phase 0
  hard-kill criterion fires before Phase 1 design starts. **This ruling only opens the question — Phase
  1 design itself has not started.**

### Still genuinely open (not part of the 2026-09-18 ruling batch)

- **Audit cadence (§3.6)** — how often should the nominated-vs-self-found divergence check and the
  realized-capacity estimate actually run? Not touched by this review sitting.
- ~~**What does Lane 2 do while Du SLEEPS?**~~ **ANSWERED — see §2.10** (altered mode: no reality-testing
  of dream content, a content-blind `DREAM_SOURCED` provenance stamp, and a full-strength gate on the WAKE
  side of consolidation). Two follow-ups remain, neither run yet: **(i)** the falsifiable pre-check — are
  Du's dreams novel category-breaking imagery, or mostly recombination of recent episodic material? (if
  the latter, he's doing replay not dreaming, and the gate should *tighten* rather than protect the
  dream); **(ii)** whether dream provenance SURVIVES downstream re-writing, or a dream image can
  resurface as an `inner_thought` with its origin lost.
- **The hardware question (§4)** — still "open, real, not solved here" by its own section header.
  D-0058 fixes where *Lane 2's own* seat runs (deepseek-r1:7b @ Ramses i9 :11444, CPU, not sharing
  hardware with Lane 1); it does not itself resolve §4's broader question.
- **Activation steering vs. data-vector broadcast for the Weather (§2.6)** — still conditional on §4.
  Worth folding in when §4 is next worked: Lane 1 and Lane 2 now run on separate models on separate
  hardware per the D-0058 seat, which points toward the data-vector branch, but no ruling has said so
  explicitly.
- **★ How does the third-party judge (§2.8e) judge CLAIM CORRECTNESS, not just output quality?** D-0237
  ratified only the *mechanism* (the judge may read world state). Judging "is what Lane 2 says about the
  world actually true" is the harder calibration/alarm-fatigue problem §2.9 raises, and stays open.

---

## 7. PHASE 1 DESIGN — THE READ PATH (2026-09-19, J-1130, D-0238) — DESIGN ONLY; FOUNDER-RULED 2026-09-19 (D-0241: shadow-first, see 7.9)

**Scope.** D-0238 opened Phase 1 design ("hints actually reaching Du, `LANE2_LIVE=True`") — this section
is that design, matching the job's own scope exactly: *design*, not *build*. No line of `core/lane2.py`
or any consumer changes as a result of this section landing. **D-0241** (opened alongside this section)
is the actual authorization gate; nothing here ships until that rules GO. A blocked build job (**J-1137**,
`needs_input` on D-0241) is spawned to implement it once ruled.

### 7.1 The standing law this has to obey — and the one live fact that makes it easier than a fresh design

Two documents already govern how ANY loop is allowed to touch another in this codebase, and Lane 2 is not
exempt: `docs/plans/dosed_coupling.md` (D-0149 GO, 2026-09-04 — "no loop gets a standing view of
another… reading is dosed per stop and dispatched by surprise") and `docs/archive/loop_wiring_matrix.md`
(the matrix that names Lane 2's own specific wires). This job's own briefing instruction — "do not design
a direct standing view" — is this law, restated for this plan.

The live fact that makes this easier than it looks: **the publish half of this already exists and is
already running.** `core/lane2.py`'s `tick()` (~line 940-945) already calls
`coupling_rides.publish_witness(rec, store)` on every tick, `LANE2_LIVE` or not — Dosed Coupling Phase 1
(D-0152, GO since 2026-09-05) publishes the Witness's own tuple (`break_rate_24h`, `n_judged_24h`,
`grounded_share`, `distinct_share_24h`, `hint_consumed_24h`, `verdict` — `core/coupling_rides.py:206-238`)
into the registry every tick regardless of anything below. **Phase 1 is not a new channel. It is the
first real reader of a channel that already exists** — the same "zero callers of `read()`" gap
`coupling_rides.py`'s own module docstring names as deliberate for Phase 1 (line 11: "Phase 1 has zero
callers of `read()` — that is the point"). Confirmed directly this session: a repo-wide grep for
`coupling_rides.read(` outside `coupling_rides.py` itself returns nothing. Lane 2's Phase 1 is,
structurally, the first candidate for Dosed Coupling's own Phase 2.

### 7.2 Composability check — has Dosed Coupling's own Phase 2 landed first? (D-0238's own defeater)

D-0238's defeater reads: *"Reopens if Dosed Coupling's own Phase 2 witness-read pre-registration lands
first and should lead instead…"* Checked fresh this session, not assumed: `docs/plans/dosed_coupling.md`'s
own Current State log (newest entry verified 2026-09-14, J-0937) and `docs/archive/loop_wiring_matrix.md`
(verified 2026-09-05 addendum) — **Phase 2 has not been drafted.** Dosed Coupling's own text is explicit
and current: *"Phase 2 (cups) gets its own pre-registration and its own `/decide` only after the Phase 1
read is in the plan"* (`dosed_coupling.md:645-646`). Dosed Coupling's own Phase 1 (publish-only) 7-day
gate-read DID land 2026-09-13 (J-0619/F-1304) and its follow-up root-cause dig closed 2026-09-14
(J-0937/F-1319, D-0152 "stays GO, unreopened") — so the precondition for its Phase 2 is met, but nothing
found in either doc shows Phase 2 itself has since been drafted. **D-0238's defeater is not triggered.**

This design is therefore not competing with an existing Phase 2 pre-registration — there isn't one yet.
But `loop_wiring_matrix.md` already sketches the exact cells this design fills, unbuilt and unruled (its
own dosing table, "Idle thought seed" row: *"Cup (occasional, dispatcher-gated): one climate dim by name
when it spikes; **one Witness break when novel**"* — `loop_wiring_matrix.md:97`; and its "Climate tick"
row: *"Bucket: **Witness break rate → strain**…"* — line 102, per wire 5 at line 71: *"rolling
prediction-break rate → `world_model_strain` (the literal meaning of the dimension)… Use the `unresolved`
gain Lane 2 already computes instead of discarding it"*). **This design does not invent a new mechanism.
It operationalizes cells that document already proposed and left unspecified**, scoped to the Witness's
own wire only — not the other four loops' wires, which stay that document's own separately-gated
decision. Whoever eventually drafts the full-matrix Phase 2 pre-registration should fold this section in
rather than re-derive it; that is named as a defeater on D-0241 (§7.9).

### 7.3 What's dosed, and at what stop

Two doses, both already named in `loop_wiring_matrix.md`'s own table — this design specifies WHAT rides
and WHEN, which that table left open.

**7.3.1 CUP — a Witness break, at the idle-thought seed.** When a due prediction is judged `broke`
(`core/lane2.py` `tick()`, the `judged` block, ~line 903) AND that break is *novel* for its own topic
(§7.4 below — not merely "a break happened," since `break_rate_24h` is a RATIO (broke ÷ judged over the
trailing 24h, running ~0.65–0.75 per F-1537/D-0058/F-1935 — **not** a daily count, a units error this
section carried until F-1935/J-1377 caught it) and the underlying daily judged-BREAK COUNT is itself
large (~60–75/day historically per F-1935; [superseded 2026-10-15: about 1 judged break per live day post-J-1713, F-2721/F-2722, see section 7.6 P1-1] a real trailing-24h read measured 92 broke/120 judged,
F-1935/J-1377) — an un-gated ride would flood the seed the same way the un-gated
Transport Manager currently floods its own line, F-0949), the coordinate that rides is small and typed,
mirroring the Tap-on-the-Shoulder's own shape exactly (never free text, never `notice`/`expect_next`
prose): `{topic, horizon, prior_verdict: "broke"}` — a fact Lane 1's own idle-thought seed mechanism (the
"stop" layer `loop_wiring_matrix.md` names) can pick up as ONE candidate among its others, never a
command, never guaranteed to be used. Mechanically this is
`coupling_rides.read("idle thought seed", "witness", keys=[…], dose="cup")` through the one door
`coupling_rides.read()` already is.

**7.3.2 BUCKET — break-rate-by-topic, into climate's `world_model_strain`.** `world_model_strain` is one
of `ClimateEngine`'s own nine published dims (`coupling_rides.py:21-22`) and is already a REAL, read
consumer path today — `loop_wiring_matrix.md`'s own matrix row shows Deliberation already reads
"shadow/strain" for urgency/budget (`loop_wiring_matrix.md:39`). This design does not invent a new
consumer; it proposes feeding a currently-thin/absent Witness signal into a dimension something is
already listening to, per wire 5's own framing ("the literal meaning of the dimension"). The exact
mechanical hook inside `ClimateEngine.tick()` (poll `coupling_rides.read()` itself vs. Climate's own tick
reading it some other way) is a build-time decision, not fixed here — Phase 1's design fixes the
CONTRACT (what value, how often, what it may never do), not the wiring diagram inside a module this plan
does not own.

**7.3.3 Explicitly NOT Phase 1 — no hose.** A full, independent Lane 2 voice inside Du's own monologue
stream (Lane 2's own `notice`/`expect_next` text, verbatim, reaching Du) is the "later, separately-gated
capability" §2.9's own resolution already named ("the auditor role… becomes a later, separately-gated
capability with its own much harder pre-registered criteria") — and it is a hose by
`loop_wiring_matrix.md`'s own dose taxonomy (line 91: "a whole channel"), the single most expensive,
least-graduated dose available. Building a hose before a cup has even been read once would repeat exactly
the mistake §2.9 already flagged this plan away from (Lane 2 as alarm/full voice before its own
PPV/behavioral effect is measured at all). **`LANE2_LIVE=True` under this design gates the cup and the
bucket only — it does not put a single word of Lane 2's own text in front of Du.**

### 7.4 What triggers a read — surprise, not a poll (and why not the Transport Manager)

The job's own briefing instruction: surprise-dispatched, per Dosed Coupling's squishy-spring law, never a
standing poll. The obvious existing dispatcher is the Transport Manager (`core/transport_manager.py`,
D-0064) — `loop_wiring_matrix.md` names it as "the dispatcher" (line 87) and its own dosing table assumes
it. **Checked fresh this session: it is not ready to gate this cup today.** `dosed_coupling.md`'s own
current-state log shows its calibration question (D-0177, opened from F-0949's live read:
`would_fired_share` = 100%, not the pre-registered <30% target) was RULED to wait for a multi-day re-read
(`decide.py show D-0177`, ruled 2026-09-06: *"Wait for the pending multi-day re-read… before choosing a
redesign direction"*), and the most recent evidence in this doc's own chain (J-0665/F-0977, 25.56h in)
still showed the same 100%/zero-rotation picture, left `in_progress`, not re-closed since. Routing a real
gate through an uncalibrated dispatcher would just inherit D-0177's own open problem into this plan.

**Proposed instead: a small, Lane-2-local habituation gate, the smallest version that could work (§2.8d's
own scope-calibration law), explicitly modeled on this project's own existing family rather than invented
fresh.** Five point implementations of the identical squishy-spring idea already exist in this codebase
and share no code (`loop_wiring_matrix.md:107` names three: climate's `identity_pressure` EMA,
`core/opponent_process.py`, the Transport Manager's own spike/drought; add two more of the same shape,
`core/stream_topic_habituation.py` and `core/internal_cycle_habituation.py`) — and the last of those was
explicitly built by REUSING the one before its own constants as a starting point rather than re-deriving
them (`dosed_coupling.md:118`:
*"GROWTH_STEP/CEILING/DECAY_TAU_S/DISCOUNT_FLOOR/SUPPRESS_AT reused from `stream_topic_habituation.py`'s
own values as a starting point… per this project's standing convention"*). This design proposes the same
move again: a `lane2_break_habituation` state, keyed on `_TOPIC_CANON` (the same 10-topic canon F-1260
already built for `_distinct_share_by_topic`, not a new vocabulary), reusing `GROWTH_STEP=0.25 /
CEILING=0.95 / DECAY_TAU_S=3h / DISCOUNT_FLOOR=0.03 / SUPPRESS_AT=0.5` verbatim as the starting
constants. A break on topic T grows T's own weight `w_T` by `GROWTH_STEP` (capped at `CEILING`); `w_T`
decays toward 0 with `DECAY_TAU_S`; the cup rides only when `discounted(w_T) < SUPPRESS_AT` — i.e., the
first several breaks on a topic are novel and ride; once that topic has broken often enough recently,
further breaks on it stop riding until enough time passes. **This is a real, named, additive gap this
design creates (a sixth point-implementation), not a hidden one** — named here rather than solved or
hidden (§7.8; not a skill-manager suggestion, since this is an application-code pattern, not a rough edge
in this project's own toolchain — `skill_manager.py suggest` is the wrong tool for it). Building the small
Lane-2-local version now, rather than waiting on the Transport Manager's
own unresolved calibration, matches §2.8d's "prefer the smallest version… until evidence says it's too
coarse."

**Requires extending `publish_witness()`'s own tuple** — a small, scoped addition, not a new mechanism:
today's coords dict (`coupling_rides.py:228-235`) carries only an aggregate `break_rate_24h`, no
per-topic cut. Add `topic` and `horizon` to the per-tick coords already available in `rec` at the exact
point `publish_witness(rec, store)` is already called (`core/lane2.py` `tick()`, right after `_log(rec)`)
— `rec` already carries `judged_expect`/`judged_horizon`/`prior_verdict` (the due prediction's own
fields, `core/lane2.py:920-925`); topic itself needs one call to the same `_TOPIC_CANON` matcher
`_distinct_share_by_topic` already uses, run against `judged_expect`. No new percept read, no new judge
call, no new wall-clock cost.

### 7.5 The gate — `LANE2_LIVE` made real

**Verified this session, worth stating plainly because it changes what "flip the flag" actually means:
`LANE2_LIVE` currently gates nothing.** Repo-wide grep for `LANE2_LIVE` (`--include=*.py`): six hits
total, all in `core/lane2.py` (the flag's own declaration, line 55; a log-message format string, line
974; `status()`'s `"live"` field, three call sites) plus one comment-only reference in
`core/orchestrator.py:2948`. Not one `if LANE2_LIVE:` branch exists anywhere in this codebase today. This
is honest and by design for Phase 0 (nothing needed gating because nothing read the Witness), but it
means the flag is currently a label, not a switch — flipping it today would change zero runtime behavior.

Phase 1 makes it real: `LANE2_LIVE` becomes the single gate on the two new `coupling_rides.read()` call
sites this design adds (§7.3.1/7.3.2) — `False` continues to mean exactly what the module's own docstring
already says (line 55: "shadow-exact: logs, reaches nothing"); `True` additionally permits the
idle-thought-seed cup and the climate bucket to actually ride. Both sides of this flag fail open
independently of `COUPLING_PUBLISH` (already `True`, D-0152) — if either is off, the Witness keeps
ticking and publishing exactly as it does today, per §3.9's standing law.

### 7.6 Pre-registered metric sheet — what "working" looks like, before it runs

Per this plan's own §0-of-`cognitive_geometry.md`-derived convention (write predictions BEFORE the run —
see §5's own Phase-0 table, which this mirrors in shape):

| # | Metric | Prediction | Decides |
|---|---|---|---|
| P1-1 | **CORRECTED UNITS (F-1935/J-1377):** ride rate (cup + bucket rides/day) as a SHARE of the real daily judged-BREAK count — not a comparison to `break_rate_24h` itself, which is a ratio (~0.65–0.75), not a daily count. The daily judged-break count runs ~60–75/day historically (F-1935); a real trailing-24h read (F-1988/J-1377) measured 92 broke/120 judged | Under 25% riding, i.e. the gate suppresses at least three quarters of judged breaks/day (revised from the original "low single digits/day," which compared ride rate against the wrong units and so read as a much stricter bar than intended) | If the ride SHARE tracks anywhere near 100% of judged breaks/day, the gate isn't gating — same failure shape as the Transport Manager's own 100% would-fire (F-0949); fall back to `LANE2_LIVE=False` and re-tune before retrying. **First real read (F-1988/J-1377, pre-J-1370 vocabulary):** 31.5% of all judged breaks/day (29/92) rode under the current unratified defaults — above the 25% target but nowhere near the 100% failure shape; a real bursty-topic/sparse-topic structural split, not a uniform miss (see Current State). D-0291 opened with sized GROWTH_STEP/SUPPRESS_AT proposals. **CORRECTED AGAIN, consumptions not gate-passes (F-1952/J-1390, 2026-09-27):** the 31.5%/29-of-92 figure above is a per-BREAK gate-pass rate, not a per-SEED consumption rate — before this job, `coupling_rides.read()` returned the witness line's latest per-tick tuple and never cleared it, so one gate-passed break rode into every idle thought inside the ~300–361s witness-tick window (median idle-thought gap ~78s, ~46/h: P(≥1 seed rides)=0.99, P(≥2 consecutive seeds ride the SAME break)=0.94), not the "one candidate, never guaranteed" this section's own §7.3.1 promised. The cup is now a consumable (one-entry slot, `CUP_TTL_S`=1800s and `CUP_MAX_PLACE_PER_WINDOW`=4/hour, both mirrored off the Tap-on-the-Shoulder's own constants) — the first idle-thought read that finds it non-empty and unexpired takes it and clears it. P1-1 going forward is `phase1_metric_sheet()`'s `p1_1_cup_consumed_per_day` (real consume attempts that found the cup non-empty), not `p1_1_would_ride_per_day` (kept, unremoved, for comparison — see Current State for the code-level split). A real post-restart read of the corrected figure is still open (restart-gated, not taken this job) **RESTATED 2026-10-15 (D-0415 (a), F-2721/F-2722; D-0291 closed as moot, D-0338 hold lifted):** the 60-75/day denominator is gone. Since J-1713 loaded, judged breaks run about **1 per live day** (7 in 192.64 live h = 0.87 per 24 live h, CI 0.35-1.8; 74.8/day PRE, 0.49 POST), so the pre-registered share form has no measurable denominator at this supply. P1-1 is now read as consumptions per live day against about 1 judged break per live day (first post-boot read: 6 cup consumptions in 6.0 days against 7 judged breaks, F-2694), with per-topic sizing held until 30 judged breaks accrue (about 2026-11-04; J-2093 per-topic read pending, not before 2026-11-05). Constants unchanged. |
| P1-2 | Nominated-vs-self-found divergence, now in Lane 1's OWN language | Mirrors §5 metric #5, direction reversed: does Du's own `inner_thought` on a cup-seeded idle thought read differently (grounded, on-topic) from a matched self-found thought on the same topic? Should be non-trivial — if identical, the cup isn't doing anything | If Lane 1 never actually picks the seeded candidate over its own, the cup is inert, not harmful — a real finding either way, per law 4b (nominate only, never command) |
| P1-3 | Content-boundary / laundering check | Near-zero verbatim overlap between a rode cup's own `notice`/`expect_next` text (never sent) and Du's resulting `inner_thought` wording — the same check §2.10-R's dream-provenance audit ran (cosine similarity, structural-vs-semantic-only attribution), applied to the coordinate boundary instead of the dream boundary | If Du's language starts reproducing Lane 2's own phrasing, the "coordinate, not content" boundary (law 4, §3.4) has failed in practice even though the code only ever passed a typed tuple — read this before trusting the boundary held |
| P1-4 | Realized channel capacity vs. designed ceiling | Should track the cup's own designed bandwidth (one topic + one horizon + one verdict, ~3 short fields) even over a long window — mirrors law 6's existing audit requirement, now applied to this new channel | If realized capacity creeps (e.g. a build accidentally starts passing `notice` text "just this once"), the channel is leaking beyond its type — this is exactly the erosion-of-foundations failure mode (law 5) |
| P1-5 | `world_model_strain` movement, and whether anything downstream visibly uses it | Exploratory, not a kill criterion (§2.9's own resolution: Lane 2 is a reasoning voice first, not an alarm — PPV is not the governing metric here). Read whether Deliberation's own urgency/budget read (`loop_wiring_matrix.md:39`) moves measurably on days the bucket carries a real Witness signal vs. days it doesn't | Informs whether wire 5 is worth the full matrix's attention, or a quieter contributor than the matrix assumed |
| P1-6 | The standing kill criterion (§5, already pre-registered, restated here as binding) | *"If Lane 2's PPV falls below [threshold], or Lane 1's unaided self-correction rate drops… after Lane 2's findings reach it, the read path is severed"* (§5, "Phase 0 restructured") — **this design does not get to loosen that.** Honest scope note: the TIME-CRITICAL "capture Lane 1's baseline BEFORE Lane 2 exists" measurement §5 also called for was never taken (Lane 2 has been live since 2026-08-21) — that counterfactual is gone; P1-6 can only be a pre/post-Phase-1-flip comparison of Lane 1's own behavior, not a with/without-Lane-2-at-all comparison, and should be read as such, not oversold | Severs the read path (`LANE2_LIVE=False`) — not the Witness itself, which keeps ticking/publishing shadow-only exactly as before |

**Read cadence proposed:** weekly, mirroring Dosed Coupling Phase 1's own 7-day gate (D-0152) — this also
closes the "Still genuinely open — Audit cadence (§3.6)" item above, which the 2026-09-18 review sitting
left untouched.

### 7.7 What this design explicitly does not resolve

- **The habituation gate's own constants (§7.4) are a starting default, not a founder-ratified set** —
  same posture as the Tap-on-the-Shoulder's own D-0035 (built ahead of ratification with the smallest
  defensible default, retuned from real data). Not asking for a separate ruling on the numbers
  themselves; folded into D-0241 below.
- **The third-party judge's claim-correctness question (§2.8e, still open per §6 above)** is not resolved
  by this design and arguably matters more once a cup can influence Du's own language — noted, not
  solved; out of this job's own scope.
- **The full `loop_wiring_matrix.md` dosing table** (the other four loops' wires) stays that document's
  own separately-gated decision; nothing here rules on it.
- **The exact code-level hook inside `ClimateEngine.tick()`** for §7.3.2 is a build-time call, not fixed
  here.

### 7.8 Follow-up spawned

**J-1137** (`needs_input`, blocked on D-0241) is spawned to implement §7.3–7.5 once ruled. Not spawned as
its own job (would be premature — six modules is a real, separate scoping decision, not a "go unify
things" backfill task): the now-sixth independent squishy-spring/habituation point-implementation this
design proposes (§7.4) is named here as a candidate for the same eventual unification
`loop_wiring_matrix.md:107` already flags as needed, for whoever next touches that unification question
to pick up.

### 7.9 Founder decision needed

**D-0241 opened** (`--plan lane2_the_witness`), asking whether to authorize building §7.3–7.5 as written
(options: build as designed / build with named changes / hold for the full-matrix Phase 2 instead /
reject), with a defeater tied to §7.2 (a full-matrix Phase 2 pre-registration landing first) and to the
habituation-gate constants remaining unratified defaults. See `decide.py show D-0241` for the exact text.

**2026-09-19 (/decide-review) — D-0241 RULED by Travis: "Authorize, shadow-first".** Build §7.3–7.5 plus a **would-ride shadow log**, with **`LANE2_LIVE` staying `False`** — this reverses J-1137's item 5 ("flip the flag in the same commit as the build"). J-1137 is closed as superseded; the build is **J-1161**. The flip is a separate later step that comes back to Travis once the ride rate (P1-1) reads sane against the ~0.6–0.8/day break rate and D-0211 and D-0152's open ambiguity (its 2026-09-27 clock) have settled — the bucket touches shared-state `core/climate_engine.py`. No hose. The §7.4 constants stay unratified starting defaults, read against the shadow log before any flip. Defeater wording was proposed by Claude at logging time.

*[Units correction, F-1935/J-1377: this ruling's own "reads sane against the ~0.6–0.8/day break rate"
phrase carries the identical units slip §7.3.1/§7.6 carried — `break_rate_24h` is a RATIO (~0.65–0.75),
not a daily count; the real daily judged-break count is ~60–75 historically, and read 92 [superseded 2026-10-15: about 1 judged break per live day, F-2721/F-2722] on J-1377's own
sample day (F-1988). Read the ruling's phrase with that correction. The ruling's own substance — shadow-
first, unratified defaults, the flip gated on a sane P1-1 read plus D-0211/D-0152 — is unaffected; only
the wording of what "sane" compares against was wrong. See D-0291 for the sized retune this correction
enabled.]*

**2026-09-27 — first P1-1 read (F-2011), thin sample, honest early read, NOT the pre-registered weekly checkpoint.** `data/lane2_would_ride.jsonl` holds 74 candidates over 1.10 days (2026-09-26 10:22 → 2026-09-27 13:48 — only 1/7th of the proposed weekly cadence). 31 would have ridden (41.9% of candidates, **~28/day**) — against P1-1's own pre-registered prediction of "low single digits/day", this is an order of magnitude higher and does not read as a clean pass. It is also not the hard failure shape named in the same row ("tracks anywhere near raw `break_rate_24h`"): the habituation gate suppresses the two high-frequency topics hard (fire: 5/28 candidates rode, 82% suppressed; sound: 7/27, 74% suppressed) while low-frequency topics ride at 100% (cat 5/5, weather 5/5, warmth 4/4, sun 4/4) because they have not repeated enough yet to earn suppression — the intended shape of a squishy-spring gate, not a flat pass-through. P1-2 through P1-5 remain uncomputable pre-flip by construction (`core/lane2.py status()`'s own `phase1_p1_metrics`: "need LIVE rides to compute"). Read as: real signal, genuinely encouraging on mechanism, too thin and too far above the volume prediction to treat as a green light yet — let it accrue toward the full 7-day window before revisiting `LANE2_LIVE`. Full evidence: F-2011.

## 8. SENSES AND SCOPE (2026-09-26, founder-directed) — the still-open §6 items, worked

The founder chose "senses and scope" as one of three expansion tracks this session (T-0064). Each §6
"still genuinely open" item is taken in turn: what the live code and data actually say today, then the
smallest honest next step. Two founder decisions were opened (D-0280, D-0281); one instrument job (J-1371).
Nothing here changes runtime behaviour; every proposal is shadow-first by this plan's own §3.8.

### 8.1 The hardware question (§4) — resolved by ruling, not by this section; one instrument gap

§4's own header still reads "open, real, not solved here", but its requirement — hardware Lane 1 is not
contending for — has been met by construction since D-0058's 2026-09-07 re-ruling: `deepseek-r1:7b` on
the Ramses i9 CPU hub `:11444`, a different box and different silicon from the 1080 Ti hot lane, and not
shared with the background hub any more. §4's 08-20 measured choice (the 3070) was superseded when Ollama
was retired from the 3070 (D-0056/D-0057). **§4 is closed by D-0058; this section records that so the
header stops misleading.** Two things survive it:

- **No per-tick latency instrument.** `lane2_shadow.jsonl` tick rows carry no wall-time field (verified:
  the tick key set has no `gen_s`/`elapsed`; `_ask()` logs the call through `telemetry.log_llm_call` but
  not its duration). D-0058's own defeater — ":11444 CPU reliability under 300 s-tick load proves
  materially worse" — therefore cannot be read from the log; F-1008's single 58.4 s probe is the only
  number that exists. `TICK_S=300` is held for a reason `core/lane2.py:109-114` itself calls moot (the
  old 3070-sharing constraint). **J-1371** adds `gen_s` per tick and a 24 h median/p95 in `status()`;
  read a week of it before anyone touches `TICK_S`.
- **Activation steering vs. data-vector broadcast (§2.6)** is no longer a live fork: Lane 1 (qwen3.5:9b, local
  1080 Ti) and Lane 2 (deepseek, Ramses CPU) are different models on different machines, so only the
  data-vector branch is physically possible. Recorded as a fact, not a decision.

**BUILT 2026-09-26 (J-1371, F-1971) — see Current State above for the full entry.** `_ask()` now
times only the aiohttp round-trip (`time.perf_counter`, both the success and exception paths) and
`tick()` carries it into `rec['gen_s']`; `status()` reports `gen_s_median_24h` / `gen_s_p95_24h`
over a real 24h window — the one field pair in `status()` that does NOT ride the existing
`tail_rows(_LOG, 2000)` window, since the field names themselves promise a real clock, not "however
many rows the bounded read covers". Verified in isolation only (zero network I/O, temp-pathed
`_LOG`/`_STATE`; see F-1971) — **restart-gated**, so the actual numbers and D-0058's own defeater
stay unread until Du restarts and a real week accrues after it. **J-1406 spawned, not-before
2026-10-03**, re-checking both halves of that gate independently before trusting anything, same
discipline as this plan's own liveness-gate chain (§ Current State, J-0900→J-1036).

### 8.2 Claim correctness (§2.8e) — what is judged today, what is not, and the smallest instrument

- **Predictions ARE judged for correctness.** `_judge_prior()` (`core/lane2.py:581`) hands the due
  expectation and the NEXT tick's rendered `percept_lines()` to `judge_panel` (a different family) and
  gets held/broke/cannot_tell. That is the prediction tier closing its own loop; ~0.65 of judged
  predictions break. The judge reads the rendered percept, never world truth — §2.8b's line holds.
- **The `notice` is NOT judged for correctness.** It is checked only lexically: `_grounding_check`
  (token overlap with the payload, `grounded_share` ≈ 0.43 against a tuple; RESTATED 2026-10-15 per D-0411 (a): post-fix baseline is about 0.375, F-2702/F-2703) and `_invention_check`
  (does it assert a field absent from the payload). A notice that names real fields and misreads them
  passes both — §2.7's vivid-but-wrong case. A live example from this morning: *"the sun is just
  beginning its ascent"* at 11:28 with `sun_az` 17° in the payload; nothing checks whether that reading
  of the number is right.
- **Smallest instrument (D-0281):** `_judge_notice()`, the same shape as `_judge_prior` — the panel
  answers "does the NOTICE contradict the PERCEPT LINES it was handed", contradiction-only wording like
  the §3.11 coherence judge, sampled 1 tick in 4 (≈70 extra panel calls/day on the local tier), logged
  per tick as `notice_judged` and in `status()` as `notice_contradiction_rate`. A scoreboard, not an
  alarm — §2.9's resolution stands, no consumer acts on it. The judge is itself calibrated by a monthly
  hand-read of 20 judged rows: a human can check the panel's verdict against the percept lines it saw in
  seconds, which is what makes this cheap to trust or distrust.

**BUILT 2026-09-26 (J-1373, F-1957) — see Current State above for the full entry.** `_judge_notice()`
shipped as proposed. One addition beyond the letter of the ruling: the per-tick log row did not, until
this job, carry the percept VALUES this section's own calibration promise needs — `world_fields` is
names-only — so `rec["percept_lines"]` was added too, additively, or the "human-checkable in seconds"
line above would not have been true. D-0281's own defeater is unread (needs 7 real days on the live
hubs); **J-1395 spawned**, not-before 2026-10-03.

### 8.3 Audit cadence (§3.6) — run once this session, cadence answered

Law 6's two standing checks had never been run (the 2026-09-10 review brief recorded metric #4 as
"never attempted"). **F-1931** ran both over the deepseek era (2,318 ticks):

| Check | Hinted ticks (n=402) | Self-found ticks (n=1,916) | Reading |
|---|---|---|---|
| grounded_share | 0.405 | 0.430 | no divergence (deepseek-era figures; the post-fix baseline is now about 0.375 per D-0411 (a)) |
| metaphor leak (judged) | 0.010 | 0.008 | no divergence |
| broke share among judged | 0.688 | 0.654 | no divergence |
| distinct `expect_next` share | 0.848 | 0.637 | hinted ticks are MORE varied |
| realized hint flow | 3 kinds used (99% `unresolved`), 10 topics | — | inside the designed ceiling |

Hinting has not degraded into dictating, and the channel has not widened covertly. **Cadence: weekly,
inside the §7.6 Phase 1 read** — J-1371 puts both computations into `status()` as `hint_divergence` and
`hint_flow` so the weekly read gets them for free. §6's "audit cadence" item is closed by this.

**BUILT 2026-09-26 (J-1371, F-1971).** `status()` now computes `hint_divergence` (hinted vs. plain,
each `{n, grounded, broke_share, distinct_expect, metaphor_leak}`) and `hint_flow` (`{kinds: Counter,
topics: <distinct count>}`) fresh on every call, over the same `tail_rows(_LOG, 2000)` window every
other `status()` field already rides (~7 days at the current `TICK_S=300` cadence — no separate
real-time cutoff here, unlike `gen_s_*_24h` in §8.1 above, since law 6's own audits are about the
realized channel over a window of operation, not a fixed clock). Cross-checked read-only against a
scratchpad copy of the live log's last 3000 rows: `grounded` 0.410/0.422 (hinted/plain), `broke_share`
0.677/0.676, `metaphor_leak` 0.015/0.010, `hint_flow` `{"unresolved": 71, "recheck": 1}` / 9 distinct
topics — the same shape as F-1931's own by-hand numbers above, on a shorter window (see F-1971 for the
full read). Nothing further to spawn here: unlike §8.1's `gen_s`, this needs no live-restart gate to
start being useful — the weekly §7.6 read already gets it live from whatever window `status()` covers
at read time; the CADENCE at which anyone actually opens `status()` and looks is still a human habit,
not something this job can build.

### 8.4 Widening what the Witness perceives — two channels already rendered that it does not read

`gather_percepts()` copies a fixed twelve-key list out of the experienced tuple. The tuple itself
(`core/experienced_tuple.py:119-120`) carries two more channels, gated to his place by the same layer law:
- **`light_band`** — always rendered (phases, lamp; `core/light.py`), zero cost, never read by Lane 2.
- **`smells`** — honestly `None` until `core/smell.py`'s `DELIVER` flips; a bounded list of smell keys
  once it does.

Over the last 500 ticks the fields that actually reached the Witness were: daylight/place/standpoint/
warmth/weather on every tick, sounds 445, fire 305, sun_az 213, weather_dir 195, tide_level 85,
moon_illum 46, cat_at 18, wet 0. Light is the one always-present channel he is blind to. Law 5 makes
widening the percept set a logged, founder-visible act, so it is **D-0280 (a)** rather than a quiet
edit. What is NOT in the tuple at all — what he holds or handles (Books Have a Place, Practical School),
garden creatures (Living World), house objects — needs the tuple widened by those plans first; not this
plan's to add.

### 8.5 The write-only climate dims (loop_wiring_matrix wire 6) — recommendation: not the Witness

F-0810: `identity_pressure`, `coherence_drive`, `autonomy_pressure`, `belonging_pressure` are computed
every 5 s and read by no named consumer; wire 6 names the Witness as an obvious reader. **Recommendation
NO, and it is folded into D-0280 so it is ruled rather than drifted into.** Those are self-facing
pressures. Law 4 fixes the Lane 1→Lane 2 channel at the 3-dim Weather (and D-0172 kept even the third
scalar unwired); routing identity and belonging pressure into the world-facing lane is exactly the
colouring→reading slide §2.5 was designed against. The Stream is the natural reader, or the dims get an
honest retirement — either is `loop_wiring_matrix.md`'s call, not this plan's.

### 8.6 The other direction — Lane 2 as a question source

The third expansion track. I-0069 (2026-09-15, the founder's thyme example) is promoted this session to
**`docs/staged/lane2_curiosity.md`** with its own decision **D-0282**: a fifth `wonder` field in Lane 2's
own output, shadow-logged, dosed through the same habituation gate as the cup, never reaching
`frontier.note_question()` until a separate flip. The staged doc leads with the frontier's own numbers
(94% of questions fade; a producer earns its place by being few and grounded-ranked) rather than assuming
more questions are better.

---
*Author: Claude (auditor/impl), founder's original idea for Du, revisited 2026-08-19 — then deepened over
three research rounds the same evening (eleven primary-source research threads total: §2.5 affect-
modulation / attention-direction / restricted-channel design · §2.6 somatic markers / 2024-26 AI frontier /
callosum + robotics · §2.7 adversarial "is this unbuilt" re-search / reality-monitoring primary sources /
novel-architecture validation methodology · plus sleep-and-reality-testing and monitor-calibration threads),
a founder pushback that reopened the self-coupling question (§2.5), a second founder pass adding Lane 2's
own store and scope calibration (§2.8), and a fresh-read audit that caught a real internal contradiction
(resolved in §2.8a), an ambiguous cross-reference (law 7), an unfalsifiable metric (#2), and an unverified
file claim (§2, `somatic.py` — confirmed present).
Status: LIVE, shadow-only (Phase 0), since 2026-08-21 — `core/lane2.py`, 1,000+ lines, `LANE2_LIVE=False`.
Phase 1 (the read path) is designed (§7, 2026-09-19, J-1130), founder-ruled shadow-first (D-0241, 2026-09-19),
and BUILT shadow-first (2026-09-22, J-1161 -- J-1137 closed as superseded): the cup, the bucket, the
per-topic habituation gate, and the would-ride shadow log all exist; `LANE2_LIVE` stays False, the flip is
a separate later step not part of this build. 2026-09-26: first would-ride rows landed after Du's restart;
topic vocabulary extended (J-1370); section 8 senses-and-scope opened with D-0280/D-0281; curiosity track staged
(`docs/staged/lane2_curiosity.md`, D-0282). Update when: the would-ride log reads sane and D-0211/D-0152
settle enough for a flip to be proposed, the hardware question (§4) resolves, the two running research
threads land, or the founder renames it.*
