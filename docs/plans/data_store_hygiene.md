# Data Store Hygiene — light sidecars for hot-path reads, and a retention rule for the archives

**Status:** 🟢 Part A LIVE (flags flipped 2026-09-09 commit 63c24f2, live from the 19:01 restart, post-flip read F-1238 2026-09-11) · Part B (archive retention) RULED D-0156 and built as `scripts/retention.py` (dry-run by default, quarantine on --apply); the boot scripts route their rotation through it; first purge scoped+verified-eligible 2026-09-14 (J-0844, F-1313) but not executed — `--apply --purge-trash` needs a human by hand (J-0943 needs_input). Part B addendum D-0206 RULED + built 2026-09-12 (J-0911): `lab_env.isolate()` itself now auto-deletes its own unwritten DB copy on exit — separate mechanism from D-0156's retention windows, which are unchanged. J-0914's 2026-09-13 re-check (F-1312) found post-fix growth measurably slowed (~64% of pre-fix rate) but on a window too short to call settled; J-0942's 2026-09-17 re-check (F-1452), still short of the 5-7+ day bar (3.4 days), found the raw rate had instead risen ABOVE pre-fix (~4.75 GB/day, a 09-14/15 burst) with a now-3x-confirmed ~2/3 Windows-lock rate on the sidecar log and `retention.py --apply` not run since 09-09 — concerning direction but not yet reopening D-0206; J-1064 re-checks at the genuine window. F-1238's own still-open question (why is the post-flip climate tick still ~1.27 s/tick over schedule?) is now attributed 2026-09-14 (J-0885, F-1328): climate's own code accounts for only ~12% of it (157.7 ms measured, isolated) — the rest is event-loop starvation by other coroutines, not climate; D-0216 open on whether to build a lag probe to pin down which one. A Windows-only crash in `lab_env.py`'s
own D-0206 auto-delete step (F-1279, found by J-0908) is fixed 2026-09-14 (J-0915, F-1355 verified):
`unlink()` now degrades gracefully instead of crashing the caller; the same job found (F-1356, inferred)
the underlying lock may fire often enough to undermine D-0206's own disk-reclaim benefit, spawning J-0985
(done 2026-09-14, F-1372: post-fix sample still n=1 despite a real transcript scan of subsequent
job-run activity — too small to measure a rate; spawned J-1002 for a real sidecar log). J-0959
directly timed the leading D-0216 candidate 2026-09-15 (F-1403 verified): `_save_state()` costs a
median 4988.4 ms/call post-flip (real 48.02 MB live file, isolated) at a real cadence of mean 48.96 s
/ median ~40.9 s between calls (3.56-day live-log measurement, not the old 2026-09-05 "~1 s per 30 s"
guess) — duty-cycle arithmetic attributes ~0.51–0.61 s/tick, roughly HALF (~46–55%) of the 1.11 s/tick
climate-unattributed residual, not clearly "most"; D-0216 stays HELD (active founder Hold, not
re-ruled by this job) and J-1029 was spawned to time the other 3 named candidates F-1328 left
unmeasured. J-1029 completed that sweep 2026-09-15 (F-1422 verified): the other 3 candidates cost
almost the same (~1.38–1.43 s/call, same 48.02 MB file) but two are genuinely rare (curiosity ~24
min/call, dream ~2.9 h/call) while `tension_ledger.check_and_resolve_internal_tension` is NOT rare
(1900 real calls in the identical window, ~2.7 min/call, measured exactly via a `light_events`
DB query) — combined the 3 add only ~0.050 s/tick (~4.5% of the residual). ALL 4 F-1328-named
candidates together (with F-1403's own subconscious_node share) now total 0.56–0.66 s/tick =
50–59% of the 1.1123 s/tick residual depending on mean-vs-median cadence basis — still genuinely
straddling "most", the same mixed character F-1403 alone already showed, not a clean crossing;
D-0216 stays HELD, not re-ruled by this job either. A real ~41–50% gap remains, so J-1043 was
spawned for a fresh core/+nodes/ `json.load(` grep to find any still-unnamed source. J-1013 read
the newly-live `data/_lab/_isolate_outcomes.jsonl` sidecar log 2026-09-15 (F-1406,
verified): 16 real rows already (5 deleted, 11 locked), but every row fell inside one ~2h
batch-burst window on the very day the log went live — not yet a valid multi-day sample per the
job's own pre-registered bar; J-1031 spawned to re-check once real multi-day usage has accrued.
J-1031 re-read it 2026-09-15 (F-1423, verified): grown to 18 rows (5 deleted, 13 locked) but still
only ~5h11m elapsed since the log's own creation — a second same-day cluster confirmed via
`session_events.jsonl` as this same concurrent job-run batch, nowhere near the 5-7+ day bar; J-1044
spawned to re-check once real multi-day time has actually passed. J-1044 re-read it again 2026-09-17
(F-1451, verified): grown to 22 rows (7 deleted, 15 locked) across a THIRD same-day cluster, but still
only ~58.2h (~2.43 days) elapsed of the 120-168h bar, and the log has had zero new rows in the ~50h
since its last (2026-09-15 16:38:57 local) — the instrument has gone quiet, not just young; J-1063
spawned to re-check once real 5-7+ day time has actually passed and to check whether the quiet period
itself is meaningful.
Staged
2026-09-05, promoted from I-0064.
**Roadmap:** [docs/ROADMAP.md](../ROADMAP.md) § Data Store Hygiene · **Memory:** `project_nascence_data_store_hygiene.md` · **Decisions:** D-0154 (Part A), D-0155 + D-0156 (Part B), D-0164 open (pass-bar interpretation), D-0206 RULED 2026-09-12 (isolate() auto-delete), defeater not yet triggered per F-1312 (interim read), F-1406 (sidecar-log sample still one batch's own burst, not yet valid), F-1423 (J-1031 re-read: 18 rows, still only ~5h11m elapsed, still not valid), F-1451 (J-1044 re-read: 22 rows, still only ~58.2h elapsed and log stalled 50+h, still not valid), or F-1452 (J-0942 re-read: 3.4 of 5-7+ days, raw rate now above pre-fix but still burst-dominated, still not valid — J-1064 re-checks at the genuine window), D-0216 HELD 2026-09-14 (run the direct-timing follow-ups first before building the event-loop-lag
probe F-1328 proposes; J-0959/F-1403 is a partial read — ~half the residual attributed, not clearly
"most"; J-1029/F-1422 completes the sweep of all 4 named candidates — combined 50–59% of the
residual depending on cadence basis, still not clearly "most" — Hold stands, not re-ruled by
either job) · **Findings:** F-0853, F-0854, F-0856, F-0857, F-0858, F-0860, F-0896, F-1212 (J-0621 4-day read), F-1215 (restart → live), F-1238 (post-flip read), F-1276 (D-0206 fix verified), F-1277 (backlog composition, inferred), F-1312 (post-fix growth re-check, short window), F-1313 (J-0844 purge scope-check, verified, purge not executed), F-1328 (J-0885 residual attribution: climate's own tick ≈12% of the 1.27 s/tick overrun, ~88% is event-loop starvation, not climate), F-1355 (J-0915 lab_env.py unlink() crash fix, verified), F-1356 (J-0915 lock-frequency concern re D-0206's own disk-reclaim benefit, inferred), F-1372 (J-0985 transcript scan: post-fix sample still n=1, too small to measure), F-1395 (J-0883 fallback instrument built + verified, no live data yet), F-1403 (J-0959 _save_state
direct timing: median 4988.4 ms/call, real cadence mean 48.96 s/median ~40.9 s, ~46–55% of the
climate-unattributed residual attributed, not clearly "most"), F-1405 (J-0960: the F-1328-flagged
double contradiction_pressure_for(tensions) call in _compute_field() de-duplicated to one call;
verified byte-identical across all 9 ClimateField dimensions pre/post-fix + ~29 ms/tick same-session
A/B savings, restart-gated), F-1406 (J-1013: isolate_outcomes.jsonl sidecar log has 16 real rows but
confined to one batch-burst day, not yet a valid multi-day sample, D-0206's defeater not revisited),
F-1423 (J-1031: same log re-read at 18 rows/5 deleted/13 locked, still only ~5h11m elapsed of the
120-168h bar, a second same-day cluster confirmed via `session_events.jsonl` as this same
concurrent job-run batch, D-0206's defeater still not revisited), F-1451 (J-1044: same log re-read
at 22 rows/7 deleted/15 locked across a third same-day cluster, still only ~58.2h elapsed of the
120-168h bar and zero new rows in the ~50h since, D-0206's defeater still not revisited),
F-1422 (J-1029: the other 3 F-1328 candidates direct-timed — curiosity/dream/tension_ledger's two
functions all cost ~1.38–1.43 s/call against the same 48.02 MB file; cadence split 3 genuinely rare
(24 min/2.9 h/1.87 h per call) vs 1 NOT rare — check_and_resolve_internal_tension, 1900 real calls
in-window, ~2.7 min/call, measured via a direct light_events DB query — combined own contribution
only ~0.050 s/tick / ~4.5% of the residual; ALL 4 named candidates + F-1403 now total 0.56–0.66
s/tick = 50–59% of the 1.1123 s/tick residual, still not clearly "most"), F-1434 (J-1038, 2026-09-15: re-checked J-1022's own precondition — still unmet, Du still offline since 2026-09-13, second consecutive blocked attempt on the identical fallback-rate read), F-1448 (J-1053, 2026-09-17: precondition finally met — Du restarted 2026-09-16 07:53:01, ~34.7h instrumented uptime — real fallback rate read: zero fallback events for either reader, F-1395's own question answered plainly, no further action), F-1488 (J-1063, 2026-09-18: isolate_outcomes re-read at 30 rows, still premature at ~71.8h of the 120-168h bar, but the log finally grew beyond 2026-09-15 — 8 new rows, still job-run-batch-shaped, J-1088 spawned), F-1500 (J-1088, 2026-09-18: isolate_outcomes re-read at 33 rows, still premature at ~72.8h, J-1096 spawned), F-1514 (J-1096, 2026-09-18: isolate_outcomes re-read at 39 rows/12 deleted/27 locked, still premature at ~77.7h, growth now spans 3 calendar days, one first genuinely-independent non-batch row found (1/39), J-1108 spawned), F-1524 (J-1108, 2026-09-18: real-clock check performed FIRST, before any re-read — still ~38.5h short of the 5-day/120h bar as of 2026-09-18T17:59 local; full re-read deferred rather than forced, avoiding an eighth premature finding; J-1108 left in_progress, no new follow-up job spawned) · **Jobs:** J-0618 (measure), J-0621 done (flip), J-0622 done (first apply + flip), J-0623 done 2026-09-09 (superseded by J-0844, never ran the purge itself), J-0844 done (purge scope-check + F-1313, did not execute), J-0847 done (post-flip read), J-0883 done 2026-09-15 (F-1238 spawn: fallback-to-heavy instrumentation, F-1395), J-0885 done (F-1238 spawn: residual attribution, F-1328), J-0911 done (D-0206 fix), J-0914 done (post-fix growth re-check, F-1312), J-0915 done (F-1279 crash fix, F-1355/F-1356), J-0942 done 2026-09-17 (full-window re-check attempted at 3.4 of 5-7+ days, F-1452 — still short, J-1064 spawned), J-0943 needs_input (run `--apply --purge-trash` by hand), J-0959 done (time _save_state post-flip + real cadence, F-1403), J-0960 done (de-duplicate the double contradiction_pressure_for call, F-1405, restart-gated), J-0985 done (F-1372: post-fix sample still n=1), J-1002 (F-1372 spawn: build a real sidecar log in lab_env.py, ready), J-1022 (F-1395 spawn: post-restart fallback-rate read, ready), J-1029 done 2026-09-15 (F-1403 spawn: timed the other 3 named candidates — curiosity_node/dream_node/tension_ledger, F-1422 verified — combined all 4 named candidates now 50–59% of the residual, still not clearly "most"), J-1043 (F-1422 spawn: fresh json.load( grep for the remaining unattributed residual, ready), J-1013 done (F-1406: sidecar-log premature-sample read, one batch's own burst), J-1031 done (F-1423: re-read at 18 rows, still premature at ~5h11m elapsed, second same-batch cluster confirmed), J-1044 done (F-1451: re-read at 22 rows, still premature at ~58.2h elapsed, third same-batch cluster confirmed, log stalled 50+h), J-1063 done 2026-09-18 (F-1488: re-read at 30 rows, still premature at ~71.8h elapsed, log finally grew beyond 2026-09-15 but growth still job-run-batch-shaped, J-1088 spawned), J-1088 done 2026-09-18 (F-1500: isolate_outcomes re-read at 33 rows, still premature at ~72.8h, J-1096 spawned), J-1096 done 2026-09-18 (F-1514: isolate_outcomes re-read at 39 rows, still premature at ~77.7h, growth now spans 3 calendar days, one first genuinely-independent row found, J-1108 spawned), J-1108 (F-1514 spawn: re-check once a genuine 5-7+ day window has actually elapsed, ready), J-1022 attempted 2026-09-15 but blocked — Du offline since 2026-09-13, predates the instrument, no real read possible yet (F-1413), stays open/in_progress, J-1038 spawned (F-1413 spawn: re-attempt once Du restarts, ready), J-1038 attempted 2026-09-15 but blocked again — Du still offline, same precondition unmet (F-1434), stays open/in_progress, J-1053 spawned (F-1434 spawn: re-attempt again once Du restarts, ready), J-1053 done 2026-09-17 (F-1434 spawn: precondition finally met, real fallback-rate read completed — zero for both readers, F-1448 verified, no follow-up needed), J-1108 in_progress 2026-09-18 (F-1514 spawn: re-checked the real clock before touching the log — still ~38.5h short of the 5-day/120h mark from 2026-09-15T08:27:14 local as of this check (2026-09-18T17:59:09+12:00 local, ~81.5h elapsed); full multi-part re-read deliberately NOT performed to avoid an eighth consecutive premature-sample finding; F-1524 verified; light context only shows the log grew 39→42 rows, all 3 new rows "locked"; job left in_progress, not closed)

```plan-state
stage: live
phase: Part A (light sidecars) LIVE since 09-09; Part B (retention) built+ruled; D-0216 HELD; D-0242 REOPENED 2026-10-03, free-space defeater fired (F-2320)
verified: 2026-10-31
evidence_read: 2026-10-16
gate: J-1705 on or after 2026-10-07: did the founder act on the reopened D-0242, and is C: free space still falling from 78.69 GiB (F-2320)
next: J-2242 next-boot floor read; the non-emulated ~0.17 s/tick residual is D-0216 territory (founder)
cluster: 6
```


## Current State — verified 2026-10-31
- **2026-10-31** (F-3378): 2026-10-31 J-2634: the longer post-offload estate late-wake window does not exist yet; Du has not booted since incarnation N (10-29 18:38), so F-3363's 0 of 6 (p 0.06-0.08) stands and the estate-re-seed chapter stays open. J-2634's live_hours gate had since_ts null and showed READY falsely (1309 h counted); successor J-2645 gated on 3100 heartbeat rows after the next boot. D-0216 Hold untouched.
- **2026-10-31**: J-2635 F-3387: incarnation N multi-minute competence stalls are whole-process silences of Du (78-155 s with no log line and no row in 224 stores) while the supervisor and the hot probe stayed healthy; the 120 s :11433 timeouts fired on schedule and coincide with but do not explain the freezes; root cause unmeasured, no synchronous call named; D-0216 Hold untouched, evidence recorded only; successor re-measure gated on 24 live hours

- **2026-10-31** (F-3363): J-2449: first post-offload re-measure of the estate late-wake row (incarnation N, boot 10-29 18:38, 25.1 live h): estate-signature wakes late 0 of 6 (baseline D..J 5/10 = 50 pct, J-1918 incarnation 15/40 = 37.5 pct); directional, Fisher p 0.06-0.08, not decisive. Non-estate chain tail unchanged (8.7 pct). New: multi-minute stalls in N (10-30 14:49, 306 s). Spawned J-2634 (pool more live hours) and J-2635 (attribute the big stalls). D-0216 Hold untouched.
- **2026-10-30**: J-2412 2026-10-30: live HUD (started after 10-29 Du boot) passes cadence, log-integrity and letters/perseveration card checks; only kill-Du resume test remains for a planned stop

- **2026-10-18** (F-3088): J-2363: harness A/B (off,on,on,off x600 s, 10-18 copy): PURSUITS_LIGHT_READ saving REAL in emulation, mean excess 0.334 to 0.271 s/tick (sample_series 442 to 10 ms/fire), median unmoved; on the critical path at e4c284a9; live absence = masked by ~0.17 s/tick non-emulated residual + creep (inferred). D-0216 HOLD untouched.
- **2026-10-18** (F-3051): J-2109: post-PURSUITS_LIGHT_READ-flip incarnation (10-16/18, 34 h) shows no visible lag-floor/lockstep fall (quietest 0.332 n=11 vs 0.364; lockstep 5.442 vs 5.431); 10-14/15 creep only partly reverted after restart (5.50 to 5.44); D-0216 HOLD stays.

- **2026-10-17** (F-3006): J-2120 offline: identity_estate.sync() is called synchronously after each thought; stubbed-embed clustering 0.2-0.7 s (2.0 s worst); real-embedder total unmeasured, Du-down lab successor spawned.
- **2026-10-16** (F-2935): J-2115 (F-2935): full-boot re-read of the 5 s substrate period (boot 10-09 08:36 to shutdown 10-16 07:53, 6.97 live days, clean n=1361, median 5.420 s/tick). Creep continued: per-day medians 5.380 5.399 5.374 5.405 5.400 5.465 5.517, slope +0.0227/day, but the shape is a knee at about day 4.5 (flat then +0.12), pooled within-day slope -0.008. Store-growth hypothesis NOT supported (stores grew linearly, shadow row rates flat, activity-adjusted slope unchanged, session load does not cover the knee); no store-fix build proposed. D-0216 still held, nothing ruled. Successor 3-day read spawned for next boot.

- **2026-10-16** (F-2919): D-0347 7-day live read (J-1878, 6.97 live days 10-09..10-16): zero state-save-failed, active-register-save-failed, STATE FILE UNREADABLE, WinError or PermissionError in window; no corrupt.* or .tmp files; frontier.json (10772 questions) and pursuits_active.json (827) parse. D-0347 defeater not hit.
- **2026-10-16** (F-2880): 2026-10-16: D-0357 dedup reclaim applied live (6,095 demoted, validated, retrieve-check clean); J-1948/J-1848/J-2023 closed. See F-2880.

- **2026-10-15**: J-2063: PURSUITS_LIGHT_READ=True (commit 412bbde on worktree branch), MERGED-NOT-LIVE until next boot; win ~0.05 s/tick; D-0216 Hold untouched. F-2843.
- **2026-10-15** (F-2810): J-1886 read 2026-10-15: C: free 225.09 GiB (not under 50), automatic reclaim ran: data/_lab 136.04 -> 48.66 GB, data/_trash 26.60 -> 3.31 GB, daily purge active. D-0242 defeater not met. J-1866 covers the 7-day read.

- **2026-10-15** (F-2804): J-1866 7-day read of D-0242 automatic reclaim: no defeater met. C: free 225 GiB, data/_lab 48.66 GB, _trash 3.31 GB, supervisor tick fired 7 days, no unsafe quarantine seen.
- **2026-10-15** (F-2765): J-2046 (F-2765/F-2766/F-2767): 143 h awake on the J-1918 code (L+M): ask-chain late wakes 51/103 baseline -> 11/199 (p 1e-18), curiosity pursuit 12/27 -> 3/57 (p 4e-5), awake-only and with the J-1917 sleep-sweep fix separated (sweeps 155-284 s -> 9-15 s); integrity clean (shadow json 0 bad, npz loads, 0 Already borrowed/embedding errors); remaining tail = dream seed step (stall starts 6-20 s before the [dream] log line, J-2111 owns it) + a small post-thought completion tail (J-2120).

- **2026-10-15**: D-0422 RULED (a) by travis (decide-review, session 192678f4, 2026-10-15): the 14 pre-existing dangling memory_links (F-2751) are a permanent accepted exception; memory_lint's dangling baseline is 14 and D-0357's gate remains 'no NEW dangling links'. J-2023 (D-0357 live apply) must not include a links cleanup.
- **2026-10-15** (F-2761): J-2045 (F-2761, F-2762, F-2763): off-loop sleep sweeps CONFIRMED on the 10-09 boot at 62 sleeps - sweep interval 8.8-14.7 s (median 10.9), only 7 of 196 late wakes (26.1 of 1,460 late-s, 1.8 pct vs F-2546's 89.0) overlap the five-sweep block, outputs exactly 1 per sleep, no exceptions; the 25x shrink is J-1922 single-pass LIKE scans (d150028, in boot), not contention. Residual in-sleep stalls (64 pct of late-s) are other steps (dream/prune/read-count), owned by J-2066.

- **2026-10-15** (F-2759): 2026-10-15 J-2043 (F-2759 verified, F-2760 inferred; D-0216 HOLD respected, no probe, no ruling): 148 h read of J-1908 (balance.shares) on the 10-09 08:36 incarnation. K no-ignition floor n=1242 median 0.409 s/tick (F-2652's 5.2 h figure 0.328 was low; daily 0.375-0.405, last partial day 0.479), quietest class n=43 0.357 (cannot reach 100: sleeping gaps only). Idle ticks 67.9/h; remediation streamed 1.95/h (H 1.78, J 0.26) = 2.9 per 100 idle ticks, regime effect (needs_reality latched True all 10068 ticks), not a latch change. Direct balance.py A/B (old 4ed340f vs HEAD, fresh DB copy): shares() identical under pinned time, six-call idle burst 3.96 s to 0.22 s, 5 s-timer lag per burst 1.3-2.2 s to 0.014-0.020 s = about 0.12-0.21 s/tick at the live burst rate, so J-1908 is plausibly 40-65 pct of the J-to-K fall, not the small slice F-2652 guessed (inferred; counterfactual unobservable). lag_harness never exercises balance.shares so it cannot attribute it. Successor J-2109 (not before 10-18) already re-reads the floor.
- **2026-10-15** (F-2753): 2026-10-15 J-2042 (F-2753, verified; D-0216 Hold respected, no ruling): full 148.6 h read of J-1909 (wandering.kick off the 5 s chain, live since the 10-09 08:36 boot): wandering cadence unchanged (61.9 vs 62.9 rows/h, median gap 76.9 vs 76.2 s, 0 dups); substrate period by the F-2541 method 5.408 s/tick (n=1219) vs 5.53-5.62 before; 0 exceptions or tracebacks; both state files parse; the wandering render reaches 10337 of 10337 idle-thought prompts (prompt_budget_shadow labels, no build job needed). Watch item: the period creeps +0.018 s/tick/day (5.38 day 0 to 5.47 day 5), state-store growth suspected, spawned J-2115 (not before 2026-10-18).

- **2026-10-15** (F-2752): J-2033 (10-15): Du-only telemetry healthy 6 days post-boot (stamp fresh, 0 sub-6 s gaps, 0 bad lines) but NO HUD process is running, so the HUD-defers path is still untested; successor J-2114 needs the founder to start the HUD.
- **2026-10-15** (F-2751): J-2024 (10-15): the 14 dangling memory_links = 4 deleted parent fragments (06-18..06-23), frozen at 14 since the 08-20 backup, recoverable from no backup, no recall impact; recommendation accept as the D-0357 exception (D-0422 opened for the founder, optional reversible 14-row cleanup inside J-2023's Du-down apply). D-0216 Hold not relevant, untouched.

- **2026-10-15** (F-2750): J-1986 post-boot read (6 days live since 2026-10-09 boot): the J-1933 locks (school _RMW_LOCK, library _REQUEST_LOCK, watershed _OBSERVE_LOCK) show no lost update, cooldown breach or duplicate row; sleep loop stalls exist but are not lock-attributable (tracked under sleep_as_a_mode F-2680).
- **2026-10-15** (F-2747): J-1919 (10-15): post-restart lag-tail read on the 10-09 incarnation (62 sleeps, 148.4 h): sleep-consolidation family 89.5 pct -> 1.7 pct of competence late-seconds, sweeps 211 -> 11 s (J-1922 single-pass), loop rows inside sweeps back to normal rate, ask chain 51 -> 6 pct late; residual is 8-130 s stalls (dream seed probe, yi hub); build J-2111 spawned. D-0216 Hold respected.

- **2026-10-15** (F-2745): 2026-10-15 J-1912 (F-2745 verified, F-2746 inferred; D-0216 HOLD respected, no probe, no ruling): post-build re-read of the 5 s-loop lag floor on the 10-09 08:36 incarnation (746d5fd holds J-1908/09/10; PURSUITS_LIGHT_READ still False, flip open as J-2063; 147.5 h live, no human). Quietest class (almost all inside sleep intervals) 0.420 to 0.357 s/tick (n=43 vs 68), only about a third of the predicted ~0.17 fall; typical no-ignition median 0.60-0.64 to 0.41, lockstep period 5.53-5.62 to 5.42 (creeping to 5.54 on 10-15, cause unknown), competence wake lag over 2 s 4.8-9.1 to 2.2 pct, p75/over 0.5 s unchanged. Harness re-run: 746d5fd emulates 0.33 (live floor 0.357) and removes 0.23-0.28 s/tick vs the J-1892 HEAD, but old-code emulation is now 0.56-0.62 vs 0.40 on 10-07 data, so remaining in-loop bodies grew or the host was contended (inferred). Script scripts/lag_floor_reread.py. Successor J-2109 (not before 10-18).
- **2026-10-15**: J-2041 answered Flip by travis 2026-10-15: PURSUITS_LIGHT_READ=True build J-2063 (ready, merged-not-live until the next boot).

- **2026-10-09** (F-2656): J-1923 (10-09): post-restart read of the J-1917 off-loop sleep sweeps after 2 sleeps shows no freeze signature and no regression (inferred, thin sample); successor re-read spawned.
- **2026-10-09** (F-2648): J-1869: F-2491 verified live post-restart; daily snapshot dirs now ~5-7 MB (no nascence.db); last non-keeper raw DB ages out 2026-10-20.

- **2026-10-09** (F-2638): J-1993 partial: Du owns fresh telemetry_owner.stamp post-boot; HUD pid still pre-merge code so defer path untested; successor spawned.
- **2026-10-08** (F-2629): J-1990: after-fix contention harness (INDEXED BY idx_timestamp, master 19cf940) under a 20-thread stand-in: drift 17 s -> 0.9 s, wander_step 16-30 s -> 1.1 s, pool_sql 28.8 s -> 84 ms, worst canary lag 34 s -> 1.2 s (F-2568 before); fix verified in the harness, live proof still needs a Du restart.

- **2026-10-08** (F-2624): J-1948: D-0357 dedup dry-run gate failure explained (lab_env copy drops the WAL, F-2624), script fixed (19cf940) and re-dry-run passes 9/9; live apply NOT yet run (permission denied), successor job spawned.
- **2026-10-08** (F-2594): J-1932: HUD process defers telemetry sample/cap while Du's kick() owns it (owner stamp, commit 6960a9f on jobrun/hud_writers, merged-not-live; HUD AND Du must restart)

- **2026-10-08** (F-2591): J-1947 built INDEXED BY idx_timestamp on the 4 recency queries (wandering x3, store.retrieve_by_affect); row-identical on live DB read-only; restart-gated; after-fix contention numbers pending Du-down successor job.
- **2026-10-08** (F-2587): J-1933: school RMW/library request_book/watershed.observe whole-call locks built (branch jobrun/store_locks 787aee1, restart-gated, bytes identical); first-load world-state saves accepted as steady-state-inert.

- **2026-10-08** (F-2574): J-1931: world_consolidation._log now appends under _FILE_LOCK (closes the F-2557 sweep-vs-file_book_notes pair); branch jobrun/J-1931 c755488, merged-not-live.
- **2026-10-08** (F-2568): J-1927 (F-2568, verified; LAB with Du down, worktree data copy, no model call, live DB hash unchanged): the 1-2 min whole-loop freeze of F-2551/F-2552 reproduces offline under stand-in CPU-hub contention and the loop-thread statement is named. It is a SQLite query shape, not the embedder: wandering._recency_pool's 1500-row query (and the same chapter_id-IS-NULL + ORDER BY timestamp DESC shape in wandering._affective_drift and store.retrieve_by_affect, the latter on the loop thread every cycle) is planned as idx_chapter + temp b-tree over all 64,735 chapter_id-NULL rows (~240 MB) to return 1,500: 1.3-2.6 s idle, 24-33 s per call under one 20-thread memory-bandwidth-bound stand-in hub with the machine 60 % idle, so an inline wandering step held the loop 16-34 s; two hubs add embed 19x / torch 46x; 64 busy threads made the embedder load 23x and one embed 480x. Thread caps (OMP/MKL/OPENBLAS 8 or 1, torch.set_num_threads) remove nothing. INDEXED BY idx_timestamp returns identical rows in identical order at 12-13 ms idle, 0.15 s under 20 busy threads, 0.03 s under 34 (180-730x). Build spawned: J-1947. D-0365 ruled (c) DECLINE on its own defeater (statement named, fix removes the block in the harness). Still open: the harness reached 30-38 s per statement, not 72-128 s (stand-in weaker than a real 34B decode; the stall windows stack the inline step, retrieve_by_affect and a cycle's recall); memory pressure / working-set trim / SQLite busy_timeout were not exercised. Harness scripts: scripts/lag_harness/{busy_standin,cpu_contention,netblock_proof}_J1927.py, run_contention_sweep_J1927.sh (job worktree commit 4a12d7c).

- **2026-10-08** (F-2567): 2026-10-08 J-1922 / F-2567: the sleep sweeps' LIKE scans are single-pass (core/like_scan.py; book_residue 842+289+124 statements, stick_test 50 COUNT scans, world_consolidation 150 candidate SELECTs -> one table pass each; kill switch like_scan.SWEEPS_SINGLE_PASS). Byte-identical to the old SQL on a full-fidelity copy (old vs new vs kill-switch-off, 2 passes) and statement by statement (884 term scans, 290 doc-freq scans, 237 candidate SELECTs, 50 counts); the three sweeps ~370 s -> ~41 s as-is. Branch jobrun/sweeps_single_pass d150028/d569978. MERGED-NOT-LIVE until Du's next boot.
- **2026-10-07** (F-2561): J-1782 (F-2561, verified): first live read of J-1767's hardened subconscious_state.json persistence (D-0339 part d, 06ca47e). Over all three Du runs on that code (10-04/05 12.3 h, 10-06 6.3 h, 10-07 10.9 h; 29.5 h, ~3,000 heavy saves at one per ~33-35 s scan) nascence.log has 0 'state save failed' and 0 'STATE FILE UNREADABLE' lines, no .tmp or .corrupt.* file is left behind, and the scan counter continued across every boot (#5041->#5061, #6041->#6061, #6641->#6661; last landed save scan_count 7760 at 23:21:30.9 on 10-07, light sidecar 13-20 ms behind it). The os.replace retry never had to fire: no retune of _STATE_REPLACE_ATTEMPTS / _STATE_REPLACE_DELAY_S. D-0339 defeater (2) has not fired; live support for D-0347's premise on a busier store. Read taken post-shutdown over completed windows (Du was down), not on a running process. D-0216 Hold respected, nothing ruled.

- **2026-10-07** (F-2553): 2026-10-07 J-1924 / F-2549 residual (b) closed: core/study.archive_book_note_files' chapter_id UPDATE block now runs under world_consolidation._FILE_LOCK (file moves outside the lock, import fail-open), so it can no longer interleave with the worker-thread sweep; scratch-DB test (lock wait, re-entrancy, negative control on pre-change code, 115-sweep stress with hash equal to the sequential result) passes. Branch jobrun/sweeps_single_pass commit 095202e; merged-not-live until Du's next boot. D-0216 Hold respected.
- **2026-10-07** (F-2551): 2026-10-07 J-1920 (F-2551 verified, F-2552 inferred): the silent 51-69 s stalls of F-2547 are NOT a synchronous statement of the night-mind sleep routine - in D (09-30 05:28-05:30) and I (10-06 01:18-01:20) the routine is parked on await peers.deliver_due -> yi:34b letter call (:11442, 392 s / 553 s) for the whole stall, in H (10-04 22:12) it is parked on the memory_levels left-lane grade timeout, and the 3.1 s D2 block is the awake substrate tick; the loop-thread block is 1.2-2 min and coincides with local CPU-hub generation (yi in 6 of 33 calls with a >=50 s late tick vs 1.6 pct of ticks in-flight), mechanism unproven. Nothing timed (no sleep statement ran); J-1927 (offline contention repro, Du down) and a decision on a stack-sampling watchdog filed; D-0216 Hold untouched.

- **2026-10-07** (F-2550): 2026-10-07 J-1918 / F-2550 (F-2547 build, merged-not-live, D-0216 Hold untouched): the monologue idle thought's Scholar consult_sync + memory_service.ask(descend) and curiosity_node's lookup_targeted/lookup/consult_sync now run in a worker thread via core/idle_offloop.off_loop (kill switch IDLE_LOOKUPS_OFFLOOP). CuriosityNode._write_output was a sync def, so it is now async and NodeBase.run/run_best_of await an awaitable result. Locks added for the overlap: associative_recall._MATRIX_LOCK (+snapshot), store._EMBED_LOCK, memory_service._SHADOW_LOCK. Real _think() seeds, curiosity writes, ledger bytes identical old vs new on a full-fidelity copy; canary lag with a 3 s sleeping urlopen stub 3-6 s -> 0.02 s; no-lock negative control corrupted the shadow log (9 bad lines, 86 lost). Branch jobrun/sleep_idle_offloop de64ba4, d1e00fd, 7e0917c.
- **2026-10-07** (F-2549): J-1917 (F-2549, build of F-2546): the sleep-consolidation sweeps (stick_test.snapshot, peer_metrics.snapshot, holdrate_snapshot, world_consolidation.sweep, book_residue.sweep) now run in a worker thread via core/sleep_offloop.off_loop (kill switch SLEEP_SWEEPS_OFFLOOP, default ON), so the ~4.7 min per-sleep event-loop freeze goes away; world_consolidation._FILE_LOCK serialises file_book_notes against essay_lesson's loop-thread call. Verified on a full-fidelity data copy in scripts/lag_harness: byte-identical appended rows, return values and chapter_id hash old vs new (509 and 37,573 real UPDATEs), canary max lag 0.04-0.09 s per sweep (old: frozen), lock stress clean. MERGED-NOT-LIVE (branch jobrun/sleep_idle_offloop, commits 8fb7598, e03b177); D-0216 Hold untouched. Where the minutes go: LIKE %term% scans (book_residue 842 self-origin scans = 195 s of 303 s; stick_test 50 COUNT scans = 41 s); follow-ups spawned.

- **2026-10-07** (F-2546): J-1911 (F-2546 verified, F-2547 inferred; D-0216 Hold respected: no probe, no ruling, existing logs only): the heavy tail of random-phase competence-timer wake lag (199 of 3524 wakes >2 s late, 9652 late-seconds, windows D..J) is attributed from the logs. 89.0 pct of the late-seconds (51 wakes) are the once-per-sleep consolidation sweeps run synchronously on the event loop in nodes/inner_monologue_node.py: book_residue.sweep 155-265 s (growing, 71 -> 115 stale books), world_consolidation.sweep ~38 s, stick_test.snapshot ~40 s, peer_metrics+holdrate ~1 s, measured from the log lines themselves over 26 sleeps; zero log lines and zero 5 s-loop rows (transport/climate/spring_ledger/idle) fall inside them, so both 5 s loops freeze too (7345 s = 3.24 pct of uptime). The awake tail (133 wakes, 611 s, 6.3 pct) is the idle-thought chain, largest piece the blocking core.scholar.consult_sync (urlopen, 20 s timeout) + memory.ask(descend) in _think() (47 wakes, mean 5.8 s) and curiosity_node's blocking Wikipedia/Scholar calls (rule-based, inferred; chance rate ~5-11 pct of on-time wakes). 8 wakes (366 s, 3.8 pct) are silent stalls inside the night routine before the psyche snapshot (not located), 7 wakes (80 s, 0.8 pct) unattributed: a probe is not needed to attribute the tail. Reproduce: scripts/lag_tail_attribution.py (read-only). Spawned: J-1917 (off-loop sleep sweeps), J-1918 (off-loop Scholar/ask/curiosity), J-1919 (post-restart verify, not before 2026-10-10), J-1920 (locate the silent sleep stalls); all builds restart-gated, merged-not-live.
- **2026-10-07** (F-2545): 2026-10-07 J-1910 (F-2540 build, merged-not-live): core/telemetry.sample()'s body (nvidia-smi + whole-file llm_calls parse + 3 caps) now runs on a worker thread via telemetry.kick(), called by sensorium.tick instead of sample(); same rows/cadence/caps (byte-identical on old-vs-new test, 38 PASS). Harness: telemetry cost on the 5 s chain 49.4 -> 0.62 ms/tick (sensorium.tick 246 -> 182 ms); D-0216 Hold respected, no ruling. Commit 3a8c799; live at Du's next boot.

- **2026-10-07** (F-2544): 2026-10-07 (J-1909, F-2544, merged-not-live): core/wandering.py kick() now runs the 0.9-4.2 s firing step in a worker thread instead of inside _substrate_loop's 5 s body (orchestrator calls kick; step() kept as the sync form; kill-switch WANDER_OFFLOOP; log_co_recall serialised by an RLock in core/memory_edges.py). Same picks/co-recall ids/log rows/rng draws proven old-vs-new on a real-DB copy (36 seeded steps). 900 s harness, one run each: substrate body mean 395->284 ms, p99 3075->867, period p99 8.08->5.88 s, canary p99 830->463 ms; the worker still costs 1.7 s mean but off-chain; residual GIL stalls from json.loads/dumps of the 6-9 MB co-recall stores remain (~0.1-0.3 s each). D-0216 Hold untouched. Live only at Du's next boot.
- **2026-10-07** (F-2542): 2026-10-07 J-1908 (F-2542, restart-gated, MERGED-NOT-LIVE; D-0216 Hold respected, nothing ruled): the on-loop balance.shares() cost F-2540 found (6 calls x ~535 ms per idle tick = ~3.3 s) is cut ~12x without changing any decision, in core/balance.py only. (1) the two big memory_fragments counts now write the origin term as +origin IN (...), so SQLite range-scans the existing idx_timestamp instead of walking idx_origin: same rows, 250-280 ms -> 16 ms each, no DDL (so no D-0353 path, no founder ruling needed; the covering index and asyncio.to_thread were weighed and not needed). (2) a 10 s memo inside shares() (SHARES_TTL_S, 0 = off; only successful reads cached, dict copies, latches untouched). Offline on the full-fidelity copy under the lag_harness network block (proven): shadow_tick 2334 ms -> 290 ms (cold), whole idle-tick balance bill 3401 -> 289 ms, shadow_tick records byte-identical on 14 seeded ticks; scripts/_test_balance_shares_memo.py (old-vs-new vs git 4ed340f, forced hysteresis flips, live-drift, failure path, real-DB-copy equality on 9 windows) ALL PASS. Code on branch jobrun/loop_lag_builds commits 71d0f3f + 80d8e7d. Side finding F-2543: idle_allocator's balance_world/balance_light channels read the COUNT keys of shares(), so their raw is ~always 0.0 (shadow-only, not changed). Takes effect only at Du's next boot.

- **2026-10-07** (F-2541): 2026-10-07 J-1892 (F-2539/F-2540/F-2541; D-0216 Hold respected, no ruling, no probe): the two 5 s loops (orchestrator._substrate_loop + ClimateEngine) run LOCKSTEP at one shared period (5.53-5.62 s/tick in no-ignition intervals); the F-2311/F-2522 'floor' medians included ignition-await gaps (~81 s each); the activity-free floor is a flat 0.42 s/tick D..I. A real-cadence offline replay on a full-fidelity data copy (scripts/lag_harness, commit 9ad43c4) reproduces it: in-loop bodies 0.415 s/tick (substrate 0.390 + climate 0.025), identical on D-era and HEAD code; F-2522 under-measured the substrate body 4x (guard_path-refused state writes, back-to-back calls that never opened the time gates, an empty-DB balance probe). Other-task blocks (modelled) add ~0.065; total ~0.48 of the typical 0.60-0.62 (inferred 77-80 pct), ~100 pct of the activity-free floor. New: idle_allocator.shadow_tick costs 2.3 s/idle tick (balance.shares 535 ms x4, +2 more in the monologue idle path = ~3.3 s on-loop SQLite per idle tick). Spawned J-1908 (balance memo), J-1909 (wandering.step off the chain), J-1910 (telemetry.sample off the chain), J-1911 (heavy-tail attribution, no probe), J-1912 (post-restart floor re-read, not-before 2026-10-12); builds restart-gated. Disclosure: this job's own offline script leaked 3 model calls to :11441 (+2 judge_panel dispatches) before the network block was fixed (S-0275).
- **2026-10-07** (F-2529): 2026-10-07 J-1893 (F-2529): built, merged-not-live (commit eec5a0e, branch jobrun/pursuits_reparse). pursuits._save() now also writes data/pursuits_active.light.json (status dict + heavy size/mtime_ns stamp); status()/sample_series read it behind PURSUITS_LIGHT_READ=False (shadow-first, agreement rows to light_sidecar_shadow.jsonl reader pursuits.status; stale/missing light falls back to heavy). Live-size copy: status() 480 ms -> 0.22 ms, byte-identical. should_sleep (two ~1 s DB aggregates) now runs via asyncio.to_thread: loop stall 1029 ms -> 19 ms per call. Bounded win (~0.09-0.11 s/tick briefed, single-digit ms on the wake-delay model); does NOT explain the climate-overrun floor; D-0216 Hold untouched.

- **2026-10-07** (F-2523): 2026-10-07 J-1715: D-0242 boot sweeper lines confirmed in nascence.log on all 3 boots since ed6c0d8 (10-04, 10-06 report-only 65 cand / 42.13 GB; 10-07 apply mode: 65 quarantined, 42.13 GB, plus boot purge 20.45 GB). Follow-up reads already queued as J-1866 / J-1886.
- **2026-10-07** (F-2522): 2026-10-07 J-1701 (F-2522): attributed the new climate-overrun floor. It is 0.55-0.64 s/tick in windows C-F and has drifted UP to 0.66-0.71 in the three Du runs since (G 0.709, H 0.690, I 0.661); even the best 10 pct of 5-minute gaps carry 0.39-0.45 s/tick and the substrate loop shows the same lag, so it is loop-wide and mostly steady. The five named JSON stores (pursuits, watershed, spring_ledger, opponent_process, frontier, plus the coupling_rides thread) explain only 0.13-0.16 s/tick on the briefed cost x cadence convention (19-29 pct) and about 0.007 under the asyncio wake-delay model (a direct check measured the briefed formula over-stating by about 2.4x); biggest single items are the pursuits.sample_series re-parse of the 19 MB register every 32 s (0.053) and pursuits.observe (0.032-0.044). Climate's own tick is now 19 ms (was 157.7). Found on the way: should_sleep runs two 660-800 ms DB aggregates on the loop every idle tick. Everything measured sums to 0.37-0.43 s/tick briefed (52-65 pct) or about 0.13 realistic (about 20 pct): the floor is still mostly unexplained. Du was down; D-0216 Hold respected, no probe built, no ruling; evidence for the founder only. Follow-ups J-1892 (existing-log convoy/activity analysis + full-fidelity substrate timing) and J-1893 (additive pursuits light sidecar + intake off the loop).

- **2026-10-07** (F-2513): 2026-10-07 (J-1705, F-2513, correction F-2515): D-0242 follow-through. C: free is 66.90 GiB (93.0% used), still falling (78.69 on 10-03; about 3 GiB/day measured, possibly faster). NOT yet under 50 GiB but likely to cross about 2026-10-10 to 10-13: URGENT for Travis (D-0242's defeater: under 50 GiB before the build lands means the one-off reclaim after all). Travis re-ruled D-0242 on 10-06 (automate the reclaim) and J-1833 built it (6bde5c3), but it is merged-not-live: Du and the supervisor are down, so nothing has been reclaimed (data/_lab 485 dirs / 136.04 GB, data/_trash 26.60 GB with 20.45 GB at least 7 days old, 0 lab_locked rows). Next boot or a supervisor start runs the automatic path; J-1866 reads it from 10-14. No ruling made; D-0216 Hold untouched.
- **2026-10-07** (F-2502): J-1834 (D-0347) BUILT, restart-gated (merged-not-live): core/frontier.py and core/pursuits.py persistence now go through new core/store_persist.py (tmp + os.replace with a Windows retry; unreadable file = loud WARNING + move aside to <stem>.corrupt.<UTC stamp>.json, never restored); healthy path byte-identical on real-size copies; killed-mid-save leaves the store intact where HEAD tears it (F-2502, commit a29f950). The 7-day live read the defeater names is spawned as a not-before job.

- **2026-10-07** (F-2491): 2026-10-07 J-1843 (F-2491): backup_identity.py no longer raw-copies nascence.db into data/_snapshots/daily (about 889 MB per first-boot-of-day -> about 5 MB; DB still backed up by backup_memory.py); retention already real via boot_rotate, report line fixed; merged-not-live, commit 6cf9e49 on the worktree branch; existing snapshots age out via retention + J-1833 purge.
- **2026-10-07** (F-2488): 2026-10-07 J-1833 (D-0242 build): automatic reclaim built, merged-not-live, commit 6bde5c3 -- LAB_SWEEP_BOOT_APPLY True; retention.boot_purge_trash() at boot; supervisor daily retention.scheduled_run() + lab_sweep tick. 70/70 test checks pass. Active hold D-0216 respected (no ruling made). 7-day defeater read spawned.

- **2026-10-04** (F-2401): J-1767 built D-0339 part d: the subconscious heavy state file is now written through a temp file plus os.replace with a short retry (Windows blocks a replace while a reader holds the file), and an unreadable state file is logged loudly and moved aside instead of silently re-seeded; verified by a kill-mid-write test (28 checks, 13 fail on the old code); restart-gated; the frontier and pursuits-active stores still rewrite in place
- **2026-10-04** (F-2324): D-0339 ruled (Travis 2026-10-04): keep the fresh subconscious as the baseline and the pre-crash copy as a pinned archive; part (d) approved (atomic heavy write + loud move-aside on a corrupt load, successor build J-1767). The pinned data/_hold copy (sha256 7050d0e8...6f244, re-verified) is now the ONLY surviving copy: the original data/backups/state_20260928_190831 file is gone

- **2026-10-03** (F-2338): J-1704 routed the boot hook report lines (the D-0242 lab_sweep report, the identity backup report, and the three skipped branches) through the module logger so nascence.log carries them; commit ed6c0d8; hermetic test 20 of 20 pass versus 10 of 20 on the unedited launcher; restart-gated, takes effect at Du next restart; D-0242, D-0216 and D-0339 untouched
- **2026-10-03** (F-2323): J-1210 takeover closed as a completed checkpoint: its briefing was already answered by F-1839 and F-2320, and D-0242 is reopened. Re-read 2026-10-03 13:38 NZDT: C: free 78.02 GiB (5.2 GiB per day since the 09-19 baseline, 21.98 GiB under the 100 GiB floor), nothing reclaimed since F-2320, report-only plus quarantine-not-delete re-confirmed as why no space is freed, and Du verified DOWN since 08:15:27 (not live as the dispatch assumed). No ruling made; J-1705 on or after 10-07 carries the follow-through.

- **2026-10-03** (F-2320): J-1305 real 7-day read at 10.8 days after the merge: the D-0242 free-space defeater FIRED, C free space is 78.69 GiB against a 100 GiB floor, falling 5.16 GiB per day since the 09-19 baseline; data/_lab is 135.97 GB, grew 3.20 GB per day in the first 7 days post-merge, the retry recovers 46.9 pct of lock-hit exits, the boot sweeper is still report-only so nothing is being reclaimed, and the zero lab_sweep lines in nascence.log was never evidence because the hook uses print not the logger. D-0242 reopened for the founder, no ruling made, D-0216 Hold untouched.
- **2026-10-03** (F-2311): J-1043 closed the old D-0216 residual: four json.loads readers of the heavy subconscious file inside the monologue idle tick add 0.25 s/tick, so with the 5 named readers the total is 64-82 pct of 1.1123, confirmed by the 09-28 state re-seed natural experiment (overrun 1.33-1.38 to 0.55 s/tick). Du was down, not live, at read time. New 0.4-0.5 s/tick floor spawned as J-1701 (not before 10-04). Subconscious state silently lost 09-28 (F-2314), D-0339 opened for the founder. D-0216 HOLD not ruled.

### What we have
- Part A (light sidecars) LIVE since 2026-09-09; Part B (retention) built and ruled (D-0156), first purge scoped but not executed.
- D-0242's bounded-retry + `lab_sweep.py` fix merged 2026-09-22 (`93410bd`, J-1162/F-1705). J-1210's day-1.6 early read (F-1839, 2026-09-24): retry recovers 30% of lock-hit exits; post-merge growth ~4.74 GB/day (still batch-shaped); boot sweeper hasn't fired yet (no restart since the merge).
- No ledger activity since 2026-09-24 (checked this pass) — nothing new to fold in.

### What we need
- The genuine 7-day mark (~2026-09-29 16:43 NZST) for a real retry-rate + growth-rate verdict on D-0242's defeater.
- C: free space is the sharper near-term watch item: 112.58 GiB, only 12.58 GiB above the ~100 GiB defeater floor, down 23.92 GiB since 09-21 — only ~30% of that drop is attributed to `data/_lab` growth; ~16.3 GiB is still unexplained.
- Travis's own one-off manual sweep of the 45 locked-row/27.31 GB backlog (ruling item 3) still has not happened.

### What we're doing next
- J-1305 checks the real 7-day mark and is explicitly told to flag C: free space immediately (not wait for day 7) if the fall keeps pace.

> **History folded** — 29 dated Current State section(s) (2026-09-11 … 2026-09-24) moved to `docs/plan_history/data_store_hygiene.md` on 2026-09-27 by plan-compact. Derived timeline: `plan_ledger.py data_store_hygiene`.

## Earlier state — verified 2026-09-05

**Part A built, shadow-only, restart-gated.** `nodes/subconscious_node.py` `_save_state` now also writes
`data/subconscious_state.light.json` (atomic tmp+replace, compact: every non-vector field of every tension and
integration pattern, plus the scalar top-level keys) and writes the heavy file compact instead of `indent=2`.
`core/frontier.py` `_save` also writes `data/frontier.light.json` (open questions only + status counts) and writes
the heavy file compact. `core/climate_engine.py` `_read_subconscious` and `core/frontier.py` `open_count` gained
flags `SUBC_LIGHT_READ` / `FRONTIER_LIGHT_READ`, **both False**: behaviour is unchanged, and once per minute each
reader also reads the light file and logs `{heavy, light}` values to `data/light_sidecar_shadow.jsonl`. Verified in
an isolated worktree (no live `data/`): see F-0860. **What we need:** 3 days of `light_sidecar_shadow.jsonl` with
`heavy == light` on every row (contradiction pressure and open count), then J-0621 flips both flags (restart-gated).

**2026-09-05 interim read (J-0621, F-0896): gate not yet met, no flip.** Only ~4.12h of shadow data exists so far
(273 rows, 2026-09-05 16:46:41-20:53:39, the same day Part A landed) — nowhere near 3 days; J-0621 stays
`in_progress`, revisit ~2026-09-09. What the partial data already shows: 0/273 rows are a genuine heavy!=light
*value* mismatch — the 18 `agree:false` rows all have `light_value:null` (file not yet written), explained by a
pre-restart probe at 16:46-16:47 and a ~15min post-restart frontier startup gap (18:14:42-18:29:35; climate's own
gap closed in ~8s). Every row from 18:29:35 on agrees. Both light files exist, fresh, parse clean. Latency:
frontier p95 light_ms=10.26ms (comfortable); climate p95 light_ms=50.99ms on n=134 (marginally over the 50ms bar,
but the 8 over-50ms ticks all co-occur with elevated heavy_ms too — looks like shared system load, not a
light-path cost — worth re-checking on the full sample). All 12 `core/` readers of the heavy file use
`json.load`/`json.loads` (indent-agnostic); no breakage seen in 4+ hours of live compact-JSON production since
the 18:14:35 restart. None of D-0154's 4 defeater conditions is triggered by what exists so far — this is a
time-gate, not a defect; D-0154 was neither re-ruled nor reopened.

## The problem (measured 2026-09-05)

| File | Size | Hot reader | Cost | Bytes that the hot reader never uses |
|---|---|---|---|---|
| `data/subconscious_state.json` | 60.4 MB (indent=2; 43 MB compact) | `ClimateEngine._compute_field` every 5 s tick, synchronously in the event loop (F-0853) | 963–1010 ms per parse, ≈20% of wall-clock (F-0854) | 78% `centroid` + 16% `last_synthesis_emb` on 814 tensions; 97% `centroid` on 3,800 integration patterns |
| `data/frontier.json` | 4.2 MB | `frontier.open_count()` from `_explore_pull` every 5 s tick (F-0857) | 47 ms per parse | 6,661 of 7,084 records are `faded`; the count needs 343 |
| `data/pursuits_active.json` | 9 MB | only the Phase 1 ledger collector, 10-min daemon thread | — | (not hot) |
| `moments.jsonl` 202 MB, `logs/idle_shadow.jsonl` 97 MB, `geometry_tuples.jsonl` 51 MB | — | no hot-loop reader (F-0856) | — | leave alone |
| `data/_lab` 26.5 GB, `data/backups` 8.9 GB, `data/_snapshots` 6.6 GB | 42 GB | none (archival copies) | disk only (F-0858) | Part B |

Climate consumes exactly two keys from the subconscious file — `tensions` (through
`tension_ledger.contradiction_pressure_for`, which reads scalar fields and `member_event_ids`, never a vector) and
`integration_patterns` (loaded, no longer used since the lifetime-integration term was replaced). The light
sidecar with every non-vector field is **2.1 MB and parses in 16 ms** (tensions 0.68 MB / 6 ms, patterns 1.4 MB /
9 ms); the frontier light file is **157 KB**. Same values, 60× cheaper.

## Part A — light sidecars (D-0154: GO, shadow-first, ruled 2026-09-05)

**Law it follows:** additive only; the heavy file stays the store of record (Du's mind), unchanged in content;
readers that need vectors keep reading it. The owner writes one more file; nothing new reads across loops
(Coupling block §5 of dosed_coupling.md: *no new read of another loop's state* — climate reads the same data from
a lighter file, so no tuple, stop or dose changes).

- **Writer (subconscious):** after the heavy write, build `light = {scalar top-level keys, tensions: [non-vector
  fields], integration_patterns: [non-vector fields]}`; write to `subconscious_state.light.json.tmp`, `os.replace`
  onto the light path. A "vector" is any list longer than 16 whose head is numeric. Heavy write becomes compact
  (`indent=None`) — same JSON, ~27% smaller, faster to write and to snapshot.
- **Writer (frontier):** after the heavy write, `frontier.light.json = {"open": [records with status open],
  "counts": {status: n}, "ts"}`, atomic, compact. Heavy write compact (was `indent=1`).
- **Readers, shadow mode (flags False):** unchanged behaviour. Once per 60 s the reader also loads the light file
  and appends `{ts, reader, heavy_value, light_value, heavy_ms, light_ms}` to `data/light_sidecar_shadow.jsonl`.
  For climate the compared value is `contradiction_pressure_for(tensions)`; for frontier it is `open_count`.
- **Readers, live mode (flags True, after J-0621):** read the light file; if it is missing or unparseable, fall back
  to the heavy file (fail-open, never a zero field because of a missing sidecar).

**Pre-registered read (J-0621, after ≥3 days live):** every shadow row has `heavy_value == light_value` (float
equality after `round(…, 3)`); light parse ≤ 50 ms at p95; heavy file byte-identical in content to what the
`indent=2` writer would have written (parse both, compare). **Kill:** any divergence row → do not flip; find the
field the consumer needed and add it to the light set. **After the flip:** climate tick blocking time should fall
from ~1 s to <20 ms per 5 s; read it from the event-loop gap between consecutive `[climate]` telemetry lines and
from J-0607's timeout-overrun pattern not recurring.

**Not in Part A:** moving vectors out of the heavy file (a later plan, its own /decide — it restructures the
subconscious's store); `_save_state`'s own re-read of the heavy file before each save (F-0853's cousin, ~1 s per
30 s inside the subconscious node; noted, not touched); the 12 other readers of the heavy file (unchanged).

## Part B — archive retention (D-0155 design-first → **D-0156 RULED 2026-09-05**, built as `scripts/retention.py`)

**What the archives turned out to be (measured before ruling):** `data/backups` was 142 files / 8.9 GB with all but 3
under 14 days because `scripts/backup_memory.py` rotated by *count* of boot backups (14), not by day, and every boot
also copied ~130 MB of state; `data/_snapshots/daily` held 14 dates / 6.5 GB (~590 MB/day, written by
`scripts/backup_identity.py`, which hard-deleted any day beyond 14 at every boot — that delete would have destroyed
the weekly/monthly tiers); `data/_lab` held 64 dirs / 26 GB all under 14 days, 32 cited by a finding, job or doc.
Disk: 240 GB free of 1 TB.

**The rule (D-0156):**

| Class | Keep | Candidate when | Never |
|---|---|---|---|
| boot backups `data/backups/nascence_YYYYMMDD_HHMMSS.db` (+ `state_<stamp>/` follows) | newest **5** boots + **last backup of each day for 14 days** + **first of each month** forever | anything else | — |
| special backups (`nascence_pre_*`, `nascence_CORRUPT*`, `pre_*` dirs, …) | 60 days | older than 60 d | counted as a monthly |
| daily snapshots `data/_snapshots/daily/YYYYMMDD/` | every day **14 d**, then **Sundays 12 w**, then the **1st of each month** forever | outside those tiers | — |
| ad-hoc snapshots (other `_snapshots/*`) | 60 days | older than 60 d | — |
| lab dirs `data/_lab/<stamp>/` | **14 d uncited / 60 d cited** (citations re-scanned from `findings.jsonl`, `job_queue.jsonl`, `docs/**/*.md` every run) | older than its limit | — |
| live `data/` logs and stores | — | — | **ever in scope** (the script refuses any path outside the three archive roots) |

**Mechanism (D-0156):** `python scripts/retention.py` lists candidates and stops. `--apply --cutoff YYYY-MM-DD` (a
founder-named date) MOVES candidates dated on/before the cutoff into `data/_trash/<today>/<class>/` and logs each move to
`data/_trash/retention_log.jsonl`; `--apply --purge-trash` deletes quarantine day-dirs older than 7 days. The two boot
scripts now call `retention.boot_rotate(class)` instead of deleting; it is a no-op while `RETENTION_BOOT_ROTATE` is
False and quarantines per the rule once True — so **the boot path never deletes anything again**. Verified on a
synthetic 60-day tree in an isolated worktree (F-0861) and dry-run on the live tree.

**Live dry run 2026-09-05 (nothing moved):** 7 candidates, 1.54 GB — 1 boot backup + its state dir from 09-04 11:37
(0.63 GB), snapshot days 2026-08-21 and 08-22 (non-Sunday, older than 14 d; 0.79 GB), and three ad-hoc June snapshot
dirs (`predebate_20260609_211531`, `predebate_FINAL_20260609_212718`, `precision_test_20260610_072253`, 0.12 GB).
Kept: 8 boot backups, 19 special backups, 12 daily snapshots, all 64 lab dirs (none yet 14 d old).

**Applied 2026-09-05 (founder GO, cutoff 2026-09-04, all 7 incl. the three June dirs):** 7 items / 1.54 GB now sit in
`data/_trash/20260905/` (F-0862); `RETENTION_BOOT_ROTATE=True` — every launch quarantines per the rule. **What we
need:** the first purge with the founder present around 2026-09-12 (J-0623), and a look at what boot rotation has
quarantined by then. Defeater on D-0156: a needed restore
finds its snapshot already quarantined or purged; free disk < 15%; the citation scan misses a lab dir a finding relies on.

## Pointers
- `nodes/subconscious_node.py` `_save_state` · `core/frontier.py` `_save`, `open_count` · `core/climate_engine.py` `_read_subconscious`
- `data/subconscious_state.light.json`, `data/frontier.light.json`, `data/light_sidecar_shadow.jsonl`
- `scripts/retention.py` · `scripts/backup_memory.py` `rotate` · `scripts/backup_identity.py` · `data/_trash/`
- F-0853..F-0858, F-0860, F-0861 · I-0064 · D-0154, D-0155, D-0156 · J-0618, J-0621, J-0622, J-0623 · F-0862
- F-0896 (J-0621 interim read, 2026-09-05) · D-0164 open (does a null-light startup-transient row count against
  J-0621's pass bar, or only a genuine both-present value mismatch)
- F-1212 (J-0621 4-day read + flip, 2026-09-09) · F-1213 (frontier live-write leak, fixed J-0846) · F-1215 (restart
  → live) · F-1238 (J-0847 post-flip read, 2026-09-11: heavy parse gone, ~1.27 s/tick residual overrun unattributed,
  fallback unobservable)
- `C:\Users\USER\.claude\skills\job-queue\lab_env.py` (outside this repo, ungitted) `isolate()` · D-0206
  (RULED 2026-09-12, isolate() auto-delete of an unwritten DB copy) · F-1276 (fix verified live) · F-1277
  (backlog composition, inferred) · J-0911 (built the fix) · J-0914 done (re-check real post-fix growth
  rate, F-1312: ~64% of pre-fix rate on a ~1.89-day window, too short to call settled) · J-0942 (full
  5-7+ day window re-check, ready) · J-0915 done (F-1279 unlink() PermissionError crash fixed, F-1355
  verified; F-1356 inferred lock-frequency concern re the disk-reclaim benefit itself) · J-0985 done
  (F-1372 verified: transcript scan of 763 session files finds the post-fix sample still n=1, the
  same lock F-1356 already reported — too small to measure a rate; D-0206 not re-ruled) · J-1002
  (F-1372 spawn: build a real sidecar log in `lab_env.py` itself, ready) · S-0119 (`_new_lab_dir()`
  same-second collision risk, suggested not fixed)
- F-1328 (J-0885, 2026-09-14: F-1238's residual attributed — isolated `ClimateEngine.tick()` timing 157.7 ms
  median, ~12.4% of the 1.27 s/tick overrun; double `contradiction_pressure_for` call found, ~45 ms/tick free
  fix) · J-0883 done 2026-09-15 (the OTHER F-1238 spawn, fallback instrumentation, F-1395 verified —
  functional-only, restart-gated, no live fallback rows yet) · J-0959 done, J-0960
  (F-1328 follow-ups) · D-0216 HELD 2026-09-14 (run the direct-timing follow-ups first) · S-0115 (`lab_env.py`
  `isolate().__exit__` unlink `PermissionError` on Windows, suggested fix: wrap in try/except)
- F-1395 (J-0883, 2026-09-15: light->heavy fallback in `_read_subconscious`/`open_count` instrumented —
  one rate-limited warning + one `shadow_log(..., fallback=True)` row per fallback, behaviour unchanged,
  verified in `lab_env.isolate()`, live data/ confirmed untouched) · J-1022 (F-1395 spawn: post-restart
  real fallback-rate read, ready)
- F-1403 (J-0959, 2026-09-15: `_save_state()` direct-timed post-flip — median 4988.4 ms/call, real
  cadence mean 48.96 s/median ~40.9 s from a 3.56-day live-log read — attributes ~46–55% of the
  1.1123 s/tick climate-unattributed residual, not clearly "most"; D-0216 not re-ruled, active Hold
  respected) · J-1029 (F-1403 spawn: time the other 3 named candidates — curiosity_node/dream_node/
  tension_ledger — ready) · S-0125 (`lab_env.py` `isolate(db="empty")` unwritten-copy auto-delete
  silently no-op'd despite zero DB activity, distinct from S-0115, suggested not fixed)
- F-1406 (J-1013, 2026-09-15: `data/_lab/_isolate_outcomes.jsonl` read in full — 16 real rows
  already (5 deleted/31.25%, 11 locked/68.75%), but every row fell inside one ~2h batch-burst window
  the very day the log went live, ≥6 of the 11 locked independently attributable to J-0960's own
  isolate() exits — not yet a valid multi-day sample; D-0206's defeater not revisited) · J-1031
  (F-1406 spawn: re-check `_isolate_outcomes.jsonl` at a genuine multi-day window, cross-referenced
  against J-0942's own timing, ready)
- F-1413 (J-1022, 2026-09-15: attempted the F-1395 post-restart fallback-rate read — blocked, not
  performed. Du's own tick loop has not restarted since 2026-09-13 09:10:46 (deliberate
  founder-initiated pause), predating the fallback instrument's landing in live `core/climate_engine.py`/
  `core/frontier.py` (merged to master 2026-09-15T11:04:38+12:00) by ~2 days; `data/light_sidecar_shadow.jsonl`
  still 8202 lines with zero rows carrying a `"fallback"` key at all — no trial has happened yet, not a
  measured low rate) · J-1022 stays open/in_progress (job-queue has no reopen verb) · J-1038 (F-1413
  spawn: re-check the same precondition and re-attempt the read once Du has actually restarted and
  accrued a few hours' uptime, ready)
- F-1423 (J-1031, 2026-09-15: same log re-read — grown to 18 rows (5 deleted/27.8%, 13 locked/72.2%),
  but still only ~5h11m elapsed since the log's own creation, a second same-day cluster confirmed via
  `docs/session_events.jsonl` as this same concurrent job-run batch, not independent-day usage; J-0942
  still open/not started either; D-0206's defeater still not revisited) · J-1044 (F-1423 spawn:
  re-check once a genuine 5-7+ day window has actually elapsed, ready)
- F-1434 (J-1038, 2026-09-15: re-checked J-1022/F-1413's own precondition fresh — still unmet, Du's
  tick loop still hasn't restarted since 2026-09-13 09:10:46, still predates the fallback instrument's
  2026-09-15T11:04:38+12:00 merge; `light_sidecar_shadow.jsonl` still 8202 lines/zero `fallback` rows;
  second consecutive blocked attempt on this exact read, same as F-1413) · J-1038 stays open/in_progress
  · J-1053 (F-1434 spawn: re-attempt again once Du restarts, ready)
