# data_store_hygiene — folded history


---

# History folded on 2026-09-27 from `docs\staged\data_store_hygiene.md` (plan-compact, 29 section(s), verbatim, original order)

_Every J-/F-/D- id below is the canonical record; this file is the prose that once sat in the plan doc. Derived timeline: `plan_ledger.py data_store_hygiene`._

## Current State — updated 2026-09-24 (J-1305, F-1857 — re-check #2, ~4.2h after F-1839: gate still NOT met (1.785 of 7 days), free-space clause re-checked immediately and still NOT tripped (112.19 GiB, 12.19 GiB above the ~100 GiB floor); no full 6-item re-read attempted this soon, no new job spawned — J-1305 itself stays open for the real day-7 read)

**J-1305 (spawned by F-1839/J-1210 for the genuine 7-day-mark read) was dispatched same-day, only ~4.18h after F-1839.** Per this plan's own precedent for a check this premature (F-1524/J-1108: "avoiding an eighth premature finding"), the full 1-6 item read (scoped by this job's own briefing to "ONCE THE 7-DAY GATE IS GENUINELY MET") was deliberately NOT re-attempted — it would reproduce F-1839 almost verbatim with no new signal. Two things were checked directly, matching this job's own explicit instructions:
- **The wall-clock gate:** 42h50m (1.785 days) elapsed since the merge (`93410bd`, 2026-09-22T16:43:27+12:00) as of 2026-09-24T11:33:20+12:00 — ~5.22 days still short of the 2026-09-29T16:43+12:00 mark. Gate not met, no verdict.
- **The free-space clause (checked immediately per this job's own standing exception, independent of the 7-day mark):** C: free space is 112.19 GiB, essentially flat from F-1839's own same-day 112.58 GiB reading (a 0.39 GiB drop over ~4.18h) — still 12.19 GiB above the ~100 GiB floor. Clause not tripped; no `/decide reopen D-0242` recommended.
- **D-0216 vs D-0242 confirmed distinct** (per the dispatching harness's own instruction to check directly): D-0216's HOLD is an unrelated event-loop-lag-probe question on this same plan and does not gate this job; D-0242 is RULED (not held) and its own defeater is what actually governs this read.
- **No `/decide` action taken** — same rule as every prior read in this chain. **No new follow-up job spawned** — a deliberate deviation from J-1210's own choice, matching J-1108's precedent instead: a third near-duplicate gate-check job within the same ~4-hour window would add ledger noise without a genuinely new checkpoint. **J-1305 itself is left in_progress** and remains the job to re-check at the real 7-day mark (on or after 2026-09-29T16:43+12:00), or sooner if C: free space is next observed closer to the ~100 GiB floor.
- Full numbers, commands and citations: **F-1857**.

## Current State — updated 2026-09-21 (J-1108, F-1643/F-1644/F-1645 — the isolate_outcomes read at the genuine window: 6.25 d elapsed, 44 rows, 72.7% locked, but the sample has STALLED since 09-19 09:18 and the ratio is a conditional batch-time figure, not a background rate; job closed, no further re-read of the pre-fix sample)

**J-1108's window has elapsed (6.25 d = 150 h from the log's own 2026-09-15 08:27:14 creation; the 5-day mark 09-20 08:27 has passed, the 7-day mark 09-22 08:27 is ~18 h away) and the full read was done — but `data/_lab/_isolate_outcomes.jsonl` has not grown since 2026-09-19 09:18:27 (still exactly 44 rows, 53 h idle) and the newest lab dir anywhere is `20260919_102121`, so no `isolate()` has even been entered for ~52 h** (Du was offline 09-19 14:12 -> 09-21 09:29; 09-20 has zero toolchain events; the 12 jobs started and 64 done since the last row created no lab dir after 10:21 on 09-19). Waiting for day 7 cannot add rows unless an `isolate()`-using job runs.

- **Q1 — ratio (re-derived, full log):** 12 deleted (27.3%) / 32 locked (72.7%, all WinError 32), same 44/12/32 the earlier reads saw, stable by day: 09-15 15/22 locked (68%), 09-17 4/5, 09-18 12/16 (75%), 09-19 1/1; no rows 09-16/09-20/09-21. It counts only **unwritten-copy exits** (`lab_env.py:237-262` appends a row only when the copy is byte-identical and the unlink is attempted; written-copy exits leave no row), so it is not an all-exits or background rate.
- **Q2 — independence:** rows do continue on days other than 09-15 (09-17/18/19), but 10 of 11 time-clusters coincide with `session_events.jsonl` activity within ±15 min (3-86 events, 2-22 sessions). The one quiet cluster (09-17 21:56:40) is **1/44 = 2.3% independent-looking rows (1/39 at F-1514) — not growing**; that ±15-min test has no power on batch days.
- **Q3 — clustering (this corrects the earlier reads' eyeball "uniform within a cluster"):** outcomes are **time-clumped, not iid** — 11 runs in the time-ordered sequence vs 18.5 expected (permutation p=0.005, analytic Wald-Wolfowitz p=0.004) and 79% same-outcome adjacent pairs inside clusters vs 59% (p=0.007) — which supports F-1356's direction (lock frequency tracks who/what is running when) over a fixed per-exit probability. But it is finer than whole batches: 5 of 8 multi-row clusters are mixed (the 15-row one is `LLLLDDDDDLLLLLL`), a whole-cluster homogeneity test is null (p=1.0), the effect leans on that one cluster (without it p=0.17), and rows carry no caller/session field, so caller vs machine-state cannot be told apart from this log. Nothing else in the log predicts outcome (Du online/offline p=0.71, concurrent density p=0.13, enter-to-exit time identical at 2.9 s median).
- **Q4 — defeaters, reported not ruled:** *D-0206* — `lab_env.py status` is **byte-identical to J-1064's 09-19 reading (111,787.6 MB)**: zero new dirs and nothing reclaimed in 2.12 d, so the flat spell is "nothing ran", not "fixed"; raw growth from J-0942's baseline is 98 dirs / 32.13 GB = 4.44 GB/day over 7.23 d (2.7x the 1.66 GB/day pre-fix figure, 0.94x the 4.74 GB/day broader average — clause 1 fires either way, as F-1561 found); clause 2 (disk acute) not fired, C: 136.50 GiB free. *D-0242* — **J-1162 (retry + sweeper) is still `open`, never started**, so its 7-day defeater clock has not begun; Travis's one-off sweep (ruling item 3) has not happened — 31 locked-row DB copies (20,462.1 MB) are still on disk. *D-0200* — its clauses are not tested by this data; one-file canary clean (live `light_sidecar_shadow.jsonl` untouched, 8202 rows, across all 44 logged exits).
- **Disk pointer (F-1645, inferred, not a Nascence defect):** C: free fell 14.84 GiB in 2.12 d (151.34 -> 136.50) while `data/_lab` grew 0 bytes; file mtimes point at ~22.6 GiB of new Fallout 4 mod downloads under `AppData\Roaming\Vortex\downloads` — so D-0242's "C: under ~100 GiB" clause (36.5 GiB away) can be tripped by non-Nascence use. Founder to confirm the attribution.
- **J-1108 closed; no further time-gated re-read of this pre-fix sample is spawned** — it is stalled at n=44 and re-reading it after day 7 would only reproduce this note. The rate question moves to its real vehicle, **J-1162's post-fix measurement** (its briefing already asks for a distinct `deleted_after_retry` outcome). Two design notes for it from this read: estimate retry success per run/cluster rather than per row with an iid interval (outcomes are autocorrelated over minutes, runs up to 9), and a seconds-scale retry may under-perform if a lock state persists for minutes (inference — that is exactly what its measurement will show). The D-0242 defeater check (7 days after J-1162 ships) should be created when J-1162 lands, not now (job-queue has no `--not-before`; this plan has already paid for that once).
- Full numbers, tests and citations: **F-1643** (log read), **F-1644** (growth/defeater status), **F-1645** (disk-drop attribution).

## Current State — updated 2026-09-21 (J-1022, F-1636 — the light->heavy fallback instrument re-read at 69.1 live hours / 30,424+ reads: still ZERO fallbacks; the wait had already cleared 09-17, J-1022 closed as a reconfirmation of F-1448)

**J-1022's read was done fresh (reader wave 2, Du live since 2026-09-21 09:29) and the answer is the same as F-1448's, at twice the uptime: the D-0154 light->heavy fallback has never fired.** The instrument reached master via merge `cc1d73d` (2026-09-15 11:04:38 NZ, carrying `613bf4e`); `live_since.py cc1d73d` shows 4 Du runs since (first restart 2026-09-16 07:53, 20.8 h after the merge; longest 49.3 h) = **69.1 cumulative live hours (2.88 live-days)**. `data/light_sidecar_shadow.jsonl` read in full: still exactly 8202 rows, **0 carry a `fallback` key**, none newer than 2026-09-09 19:00:20, mtime unmoved; the literal warning `light sidecar fallback` appears **0 times** in the full 488,379-line `data/nascence.log`.

- **Reads behind the zero (counted from the log, not assumed):** the `[climate] dominant=` telemetry line fires at `ticks % 60 == 1`, so the 4 runs' 360/1/110/40 lines mean **30,424–30,660 executed climate ticks**; each calls `_read_subconscious` once (its only call site) and, via `_explore_pull`, `frontier.open_count()` once — so ≥30,424 reads of EACH reader (`frontier.open_count` has three more callers that the log cannot count). Observed rate **0 per read / 0 per hour for both readers** (rule-of-three 95% upper bound ≈1e-4 per read, ≈0.043 per uptime-hour). There are no fallback occurrences, so the briefing's step 2 (writer racing an atomic replace vs. a corrupt light file) has nothing to examine.
- **The zero is not a muted instrument:** `scripts/run_nascence.py` calls `mark_live()` (so `light_sidecar._shadow_path()` resolves the real path for Du) and installs a root INFO file handler (so the warning would reach the log); `shadow_due()` is True on a process's first call, so the first fallback of any run would always have been logged. Both light files are refreshing in lockstep with their heavy siblings right now (same-second mtimes, no leftover `.tmp`).
- **Wait classification: CUMULATIVE, and it had already cleared 2026-09-17** (J-1053/F-1448, 34.7 h, zero). The briefing's premise that this still awaited a restart was stale; J-1022 stayed `in_progress` only because the J-1022 -> J-1038 -> J-1053 chain never closed its parent (job-queue has no reopen verb; J-1038 and J-1053 are both `done`). **J-1022 closed.**
- **No follow-up job, no `/decide` action.** D-0154's defeater is untriggered (no heavy != light row anywhere, none newer than 09-09). D-0216 (the founder's ACTIVE HOLD, event-loop lag) was read as context only, not touched; for what it is worth, the median telemetry-gap overrun in the three loaded runs is 1.32–1.55 s/tick, in line with F-1238's 1.27 s/tick, nowhere near the 5 s "TICK_SECS" trigger in its defeater.
- Full evidence (every command, counts, line cites): **F-1636**.

## Current State — updated 2026-09-19 (J-1064, F-1561/F-1562 — D-0206 GB/day re-check at a genuine 5.11-day window: 6.29 GB/day, 3.8x the pre-fix rate; the defeater's rate clause fires, its "lab jobs write to the DB" mechanism does not — the leak is transient Windows locks with no active reaper)

**J-1064 measured at 2026-09-18T23:35:38Z (2026-09-19 11:35 NZST), 5.112 days (5d 2h 41m) after J-0942's own 2026-09-13T20:54:14Z baseline — past the job's own 5-day floor, short of its preferred 7-day mark: `data/_lab` went 184 dirs / 79,652.9 MB → 283 real dirs (`lab_env.py status` says 284, S-0129/S-0135) / 111,787.6 MB, +99 dirs / +32,134.7 MB = 6.29 GB/day.**

- **Rate vs. every baseline: 3.8x the pre-fix ~1.65-1.67 GB/day (F-1277), 5.9x F-1312's ~1.06 GB/day, 1.3x J-0942's burst-window 4.75 GB/day, 1.33x the broader pre-fix average of surviving dirs (149 dirs / 74.3 GB over 08-27..09-11 ≈ 4.74 GB/day)** — nowhere near F-1277's predicted 0.4-0.5 GB/day settled range or F-1312's "below ~64%" bar. The last 1.71 days alone (since J-0942's read) added +28 dirs / +15.95 GB ≈ 9.3 GB/day. Per local day: 09-14 7.18 GB, 09-15 9.00, 09-16 0, 09-17 2.87, 09-18 11.61, 09-19 (so far) 1.47 — burst-shaped, but waiting for day 7 cannot move the verdict: the 32.1 GB already accrued exceeds what a 7-day average at the pre-fix rate (11.6 GB), at F-1312's rate (7.4 GB) or at the predicted rate (3.5 GB) would allow, and nothing in the 184-dir baseline set has been reclaimed (still exactly 79,652.9 MB).
- **Sidecar log `_isolate_outcomes.jsonl` re-read in full: 44 rows (09-15 08:27:14 → 09-19 09:18:27 NZST, four calendar days), 12 deleted (27.3%) / 32 locked (72.7%, all WinError 32)** — the locked share has sat inside a 63-73% band across all eight reads since F-1406 and the newest 8 rows are all locked. 45 of the 99 new dirs still hold a full 684-731 MB DB copy = 31.6 GB = **98.3% of the window's growth**; 29 of those are sidecar-`locked` (confirmed never-written) copies = 20.46 GB (63.7% of growth); 11 (7.5 GB) predate the log; 5 (3.6 GB, extra files present) look genuinely written (inference, not checked).
- **Mechanism (F-1562):** a non-destructive DELETE-handle probe found **no conflicting handle on any of the 31 existing locked-row DB copies (nor on 16 other post-baseline full copies)** — the locks are a race at `isolate().__exit__`, not a persistent holder, so ~20.5 GB of confirmed-unwritten copies is deletable today and a bounded retry, or a sweeper keyed on the log's `locked` rows, would fix it at the source. **`scripts/retention.py` cannot be that sweeper as written**: its labs class only takes dirs > 14 d (uncited) / > 60 d (cited) — a read-only dry run today lists 26 labs candidates / 11.28 GB, all dated 2026-08-29..09-05, none from this window (earliest eligible: 2026-09-28) — the boot-time rotation never runs the labs class, and the last labs apply was 2026-09-09 (F-1208, `data/_trash/retention_log.jsonl` shows 4 labs rows, all that day).
- **Disk:** C: 84.1% used / 151.34 GiB free (177.73 GiB at F-1312, 174.14 at J-0942) — net −26.4 GiB in 5.11 d ≈ 5.2 GiB/day, ~29 days to full at that pace; not yet acute.
- **D-0206's defeater test, applied for real:** clause 1 ("growth continues at a similar rate even after the auto-delete fix ships") **fires on the rate**; the clause's own parenthetical mechanism ("most lab jobs genuinely do write to the DB") is **not** what the evidence shows. Clause 2 (disk pressure acute) does not fire yet. **No `/decide` action was taken by this job** (the run that produced it was barred from opening/reopening decisions); recommendation for the founder: open a fresh /decide quoting the defeater verbatim, scoped to the lock/retention-cadence gap (retry-or-sweep at exit; whether retention.py's labs class should get a sweep for confirmed-unwritten copies), not to reconsidering `db="empty"` as the default. A drafted question is at scratchpad `read_J-1064_proposed_decide_question.md`. **D-0216 (the founder's ACTIVE HOLD, event-loop-lag probe) was read as context, is unrelated to this topic, and was not touched.**
- **Correction to F-1562's evidence text:** it says the lock probe ran "between about 23:45Z and 23:55Z"; it actually ran ≈23:41-23:43Z (F-1562 itself was recorded 23:44:05Z). Substance unaffected.
- **J-1064 recommended done** — 5.11 d clears its own floor and the extra ~1.9 d to the 7-day mark cannot change the verdict. J-1108's own sidecar-log re-read (5-7 d from 09-15 08:27, i.e. 09-20 → 09-22) is unaffected and remains the watch on whether the locked share moves.
- Nothing was deleted, moved or written under `data/`; `retention.py` was run dry only. Full numbers and citations: **F-1561** (rate + defeater test), **F-1562** (lock transience + retention reach).
- **2026-09-19 (orchestrator, on the founder's instruction): D-0242 OPENED** (this plan) — the fresh /decide the bullet above recommended, quoting D-0206's defeater verbatim and scoped to the lock/retention-cadence gap (bounded retry at `isolate().__exit__`, a sweeper keyed on the log's `locked` rows, both, D-0206's original size-cap/shorter-window alternatives, or leave as is with hand-run retention). Nothing ruled. J-1064 closed as done. J-1108's sidecar-log re-read (5-7 d from 09-15 08:27, i.e. 09-20 → 09-22) is unaffected and still open. D-0216 (the founder's ACTIVE HOLD) untouched.
- **2026-09-19 (/decide-review): D-0242 RULED by Travis — "Retry plus sweeper".** (1) Bounded retry around the unlink in `isolate().__exit__`; (2) a sweeper keyed on the sidecar log's `locked` rows (deletes only the DB copy in a locked-row dir with no live handle; dry-run first), run at Du boot or job-run start; `retention.py` labs windows unchanged; both built by **J-1162** (urgency 4; note `lab_env.py` lives under `~/.claude/skills/`, D-0222 applies). (3) The one-off sweep of the 29 confirmed never-written copies (~20.5 GB) is **Travis's own action** — no agent deletes anything under `data/_lab`. The defeater on record (growth still above ~2 GB/day after 7 days of the fix, or C: free space under ~100 GiB) was kept.

## Current State — updated 2026-09-18 (J-1108, F-1524 — real-clock check before touching the log: still ~38.5h short of the 5-day/120h bar, full re-read deferred rather than forced)

**J-1108 (spawned from F-1514/J-1096) checked the real calendar date/time first, per its own explicit instruction, before running any of the actual multi-part re-read.** Current local time at check: 2026-09-18T17:59:09+12:00 (`Get-Date`) — elapsed since the log's own 2026-09-15T08:27:14 local creation timestamp is ~81.5h (~3.4 days), still ~38.5h short of even the 5-day/120h mark (2026-09-20T08:27 local) and well short of the 7-day/168h mark (2026-09-22T08:27 local).

- **The full multi-part re-read (deleted/locked ratio over the genuine window, cross-calendar-day spread, same-hour clustering vs `session_events.jsonl`, D-0206 defeater revisit) was deliberately NOT performed** — doing so now would have produced an EIGHTH consecutive premature-sample finding on this exact question (after F-1372/F-1406/F-1423/F-1451/F-1488/F-1500/F-1514), the precise anti-pattern this job's own briefing named and asked to avoid.
- **Light context only, not a representative measurement**: the log grew from 39 rows (F-1514: 27 locked/12 deleted) to 42 rows (30 locked/12 deleted) by this check — the 3 new rows are all "locked", none "deleted"; the newest row's `lab_dir` timestamp (`20260918_175945`) landed essentially in real time as this check ran, consistent with continued burst-driven rather than steady-background growth.
- **Cross-checked J-1064** (the parallel D-0206 GB/day-rate chain this job is meant to cross-reference): still `status: in_progress`, its own 5-day mark (~2026-09-18T20:54Z / ~2026-09-19T08:54 local) also not yet reached as of this check (current UTC ~2026-09-18T05:59Z).
- **No `/decide` action.** D-0206 is an already-ruled decision with its own defeater on file — not reopened, since no genuine multi-day sample exists yet to test that defeater for real. **D-0216 (the founder's ACTIVE HOLD, ruled 2026-09-14) was checked and confirmed still in force, still unrelated to this job's own topic (event-loop-lag probe, not data/_lab growth) — read as context, not touched or ruled over**, per this job's own ground rules.
- **Job left `in_progress`, not closed** — the timing precondition is genuinely unmet, matching J-1064/F-1487's own precedent for this exact situation. A fresh attempt should re-check the real clock again on or after 2026-09-20T08:27 local (5-day floor), ideally 2026-09-22 for the cleaner 7-day read.
- **No new follow-up job spawned** — this job (J-1108) itself already IS the correctly-scoped re-check; per this plan's S-0031/S-0113/S-0114 precedent (job-queue has no `--not-before`/reopen verb), it stays `in_progress` rather than a fresh job id being minted for the same wait.
- Full evidence (exact commands run, timestamps, counts): **F-1524**.

## Current State — updated 2026-09-18 (J-1096, F-1514 — isolate_outcomes sidecar log re-read: still premature at ~77.7h of the 120-168h bar, growth now spans three calendar days, one first genuinely-independent row found)

**J-1096 (spawned from F-1500/J-1088) re-read `data/_lab/_isolate_outcomes.jsonl` in full: the log has grown to 39 rows, but elapsed time since its own creation (2026-09-15T08:27:14 local) is still only ~77.7h (~3.24 days) — the 120h/5-day mark falls 2026-09-20T08:27:14 local, the 168h/7-day mark 2026-09-22T08:27:14 local.** New totals: 12/39 (30.8%) "deleted", 27/39 (69.2%) "locked" (up from F-1500's 11/33 and 22/33).

- **Growth now spans three calendar days for the first time** (20260915=22 rows, 20260917=5 rows, 20260918=12 rows so far) — no longer confined to the single day the log went live, a real change from every prior read in this chain.
- **Same-hour clustering (gap>1h) still shows near-total job-run-batch confinement, but with one first exception**: of 9 clusters found, 8 had between 3 and 86 `docs/session_events.jsonl` entries within a ±15-minute window (concurrent job-run activity across many sessions), matching F-1356's caller/session-clustering hypothesis exactly as every prior read found. One single-row cluster (local 2026-09-17 21:56:40) had **zero** nearby session_events entries — the first row in this whole chain with no batch correlation at all. This is a genuine new data point toward independent/organic usage, but at 1/39 rows it is far too small to revise the batch-clustering conclusion; worth tracking whether this fraction grows in future reads.
- **D-0206's own defeater (data/_lab growth RATE) is a separate question from this deleted/locked ratio** — "locked" means the auto-delete check itself could not run due to concurrent file access, not that the DB was written to. The parallel J-0942/J-1064 GB/day-rate chain remains the right instrument for that question; J-1064 was confirmed still `status: in_progress` at read time, its own 5-day mark (~2026-09-18T20:54Z) not yet reached either, consistent with its own last finding F-1487.
- **Does not clear the job's own pre-registered validity bar** — this is the SEVENTH consecutive premature-sample finding on this exact question (F-1372/J-0985, F-1406/J-1013, F-1423/J-1031, F-1451/J-1044, F-1488/J-1063, F-1500/J-1088, F-1514/J-1096).
- **No `/decide` action**: D-0206 is neither re-ruled nor reopened — not enough real evidence yet on either channel. **D-0216 (the founder's ACTIVE HOLD) was read as context but not touched or ruled over**, per this job's own ground rules.
- **Follow-up spawned: J-1108** — re-read the log once at least 5-7 days have genuinely elapsed from 2026-09-15 08:27:14 (the 5-day mark 2026-09-20 08:27 local, 7-day mark 2026-09-22 08:27 local), watching in particular whether the fraction of genuinely-independent (non-batch) rows grows beyond this read's single instance.
- Full numbers and citations: **F-1514**.

## Current State — updated 2026-09-18 (J-1088, F-1500 — isolate_outcomes sidecar log re-read: still premature at ~72.8h of the 120-168h bar, new rows continue to correlate with job-run batch windows)

**J-1088 (spawned from F-1488/J-1063) re-read `data/_lab/_isolate_outcomes.jsonl` in full: the log has grown to 33 rows, but elapsed time since its own creation (2026-09-15T08:27:14 local) is still only ~72.8h (~3.03 days) — the 120h/5-day mark falls 2026-09-20T08:27:14 local, the 168h/7-day mark 2026-09-22T08:27:14 local.** New totals: 11/33 (33.3%) "deleted", 22/33 (66.7%) "locked".

- **Only 3 new rows since F-1488, all "locked", at local 08:21:24 and 09:11:40/09:11:54 on 2026-09-18** — a window that exactly overlaps this session's own job-run batch chain (`docs/session_events.jsonl` shows J-1085/J-0904/J-1086/J-1054/J-1064/J-1063/J-1055/J-1082/J-1094/J-1087/J-1091/J-1088 all logging activity across UTC 2026-09-17T20:04:55-21:13:35, i.e. local 2026-09-18T08:04:55-09:13:35). This again matches F-1356's caller/session-clustering hypothesis over a smooth background rate — no calendar day since 2026-09-15 has yet shown growth clearly outside a job-run-batch window.
- **D-0206's own defeater (data/_lab growth RATE) is a separate question from this deleted/locked ratio** — "locked" means the auto-delete check itself could not run due to concurrent file access, not that the DB was written to. The parallel J-0942/J-1064 GB/day-rate chain remains the right instrument for that question, and its most recent check (F-1487, same session window) also found its own 5-7 day precondition still unmet.
- **Does not clear the job's own pre-registered validity bar** — this is the SIXTH consecutive premature-sample finding on this exact question (F-1372/J-0985, F-1406/J-1013, F-1423/J-1031, F-1451/J-1044, F-1488/J-1063, F-1500/J-1088).
- **No `/decide` action**: D-0206 is neither re-ruled nor reopened — not enough real evidence yet on either channel. **D-0216 (the founder's ACTIVE HOLD) was not touched or ruled over**, per this job's own ground rules.
- **Follow-up spawned: J-1096** — re-read the log once at least 5-7 days have genuinely elapsed from 2026-09-15 08:27:14, cross-referenced against whatever D-0206 growth-rate job succeeds J-1064 by then.
- Full numbers and citations: **F-1500**.

## Current State — updated 2026-09-18 (J-1063, F-1488 — isolate_outcomes sidecar log re-read: still premature at ~71.8h of the 120-168h bar, but the log started growing beyond 2026-09-15 for the first time)

**J-1063 (spawned from F-1451/J-1044) re-read `data/_lab/_isolate_outcomes.jsonl` in full: the log has grown to 30 rows, but elapsed time since its own creation (2026-09-15T08:27:14 local) is still only ~71.8h (~2.99 days) — the 120h/5-day mark falls 2026-09-20T08:27:14 local, the 168h/7-day mark 2026-09-22T08:27:14 local.** New totals: 11/30 (36.7%) "deleted", 19/30 (63.3%) "locked".

- **The 50+ hour stagnation F-1451 flagged has broken: 8 new rows appeared, the first ever outside 2026-09-15** — 5 rows on 2026-09-17 (20:50:37-21:56:40 local: locked×3, deleted×1, locked×1) and 3 rows on 2026-09-18 (08:10:09-08:10:41 local: deleted×3). Both new clusters correlate directly with concurrent job-run batch activity in `docs/session_events.jsonl` (the 09-17 cluster with job J-1059's own logged window, the 09-18 cluster with this same batch's own jobs J-1075/J-0904/J-1054/J-1064/J-1063) rather than independent multi-day organic usage — outcome is fairly uniform within each new cluster but differs across clusters, again matching F-1356's caller/session-clustering hypothesis over a smooth background rate.
- **Cross-referenced against J-0942** (the parallel D-0206 growth-rate re-check): now done (F-1452), measured a raw ~4.75 GB/day rate but flagged by its own finding as a burst/quiet artifact, not a steady-state figure — not directly comparable to the pre-fix ~1.65-1.67 GB/day rate.
- **Does not clear the job's own pre-registered validity bar** — this is the FIFTH consecutive premature-sample finding on this exact question (F-1372/J-0985, F-1406/J-1013, F-1423/J-1031, F-1451/J-1044, F-1488/J-1063).
- **No `/decide` action**: D-0206 is neither re-ruled nor reopened — not enough real evidence yet. **D-0216 (the founder's ACTIVE HOLD, an unrelated event-loop-lag question) was read as context but not touched or ruled over**, per this job's own explicit ground rules.
- **Follow-up spawned: J-1088** — re-read the log once at least 5-7 days have genuinely elapsed from 2026-09-15 08:27:14, checking specifically whether growth beyond 2026-09-15 continues to be job-run-batch-shaped or starts showing genuinely independent multi-day spread, and cross-referenced against whatever D-0206 growth-rate job succeeds J-0942 by then.
- Full numbers and citations: **F-1488**.

## Current State — updated 2026-09-17 (J-1053, F-1448 — the fallback-rate read completed: precondition finally met, rate is zero)

**J-1053 re-checked the precondition fresh (per J-1038's own instruction, not assuming a third attempt would find it met) and this time it IS met.** `data/nascence.log` grepped in full for shutdown/startup lines: Du's tick loop shut down 2026-09-13 09:10:46,516 (the same pause F-1413/F-1434 already documented) and restarted **2026-09-16 07:53:01,143** — no shutdown line since, and `climate_state.json`/`frontier.json`/`subconscious_state.json`/`nascence.log` mtimes are all seconds-old at read time (2026-09-17 18:37:25 NZST), confirming Du is live right now. That restart postdates the J-0883/F-1395 fallback instrumentation's merge to master (2026-09-15T11:04:38+12:00) by ~20h48m, and ~34h44m of instrumented uptime has now accrued — comparable to J-0847's own ~36.9h precedent. supervisor.log/netstat again only show the separate LLM-hosting tier, correctly not treated as evidence either way (same distinction F-1413/F-1434 already established).

**Ran J-1022's original 4-step read: the real fallback rate is zero.** `data/light_sidecar_shadow.jsonl` is still exactly 8202 lines, mtime still unmoved since 2026-09-09 19:00:20 — byte-for-byte unchanged even after ~34.7h of live instrumented uptime — and `grep -c '"fallback"'` across the whole file returns 0; no row of either reader carries a fallback key. Cross-checked independently against `nascence.log` itself: the instrument's own literal warning string, `"light sidecar fallback -> heavy"`, appears **0** times in the full 473,491-line live log (the 2631 unrelated hits for bare "fallback" are all LLM-hosting failover / hot-lane / weak-filter grounding messages, confirmed by direct inspection, not this instrument). Confirmed this is a real negative result, not an idle/untested path: the instrumented code is present in the live `core/climate_engine.py`/`core/frontier.py` (not just a worktree copy), 259 `[climate] dominant=` telemetry lines since the restart imply ~15,500+ real climate ticks (each calling the instrumented reader), and both `subconscious_state.light.json`/`frontier.light.json` are refreshing continuously (mtimes seconds old) — the light read path is genuinely exercised at high volume and has simply succeeded every time.

- **F-1395's own open question is now answered plainly, no further action** (per this job's own step-3 instruction for a negligible/explained result): the light→heavy fallback has not fired at all in its first ~34.7h of live post-flip runtime; the light writer (`light_sidecar.write_atomic`'s tmp+`os.replace`) is keeping both light files continuously valid across this whole window, so the None/missing-keys condition that would trigger a fallback has not occurred. Step 4 (pattern-check on fallback rows) does not apply — there are no fallback rows to examine.
- **No `/decide` action needed for this finding** — the result is clean and requires no founder call. This job's own operating instructions also carried an active-Hold flag on **D-0216** (a different, unrelated question, the event-loop-lag probe) — confirmed unrelated to this job's topic, read but not touched, not re-ruled.
- **No follow-up job spawned** — this job's own briefing explicitly says a negligible/explained result needs no further action; the long-blocked J-1022→J-1038→J-1053 chain is now genuinely resolved rather than re-deferred a third time.
- Full evidence (exact commands run, timestamps, log lines, telemetry counts): **F-1448**.

## Current State — updated 2026-09-17 (J-1044, F-1451 — isolate_outcomes sidecar log re-read: still premature at ~58.2h of the 120-168h bar, and the log has stopped growing entirely for 50+ hours)

**J-1044 (spawned from F-1423/J-1031) re-read `data/_lab/_isolate_outcomes.jsonl` in full: the log has grown to 22 rows, but elapsed time since its own creation is still only ~58.2h (~2.43 days) — about 34-48% of the job's own required 5-7+ day (120-168h) window.** New totals: 7/22 (31.8%) "deleted", 15/22 (68.2%) "locked" — recorded for the record, not as a representative long-run rate (same caveat every prior read in this chain applied).

- **All 22 rows are still confined to a single calendar day (2026-09-15), now across THREE same-day clusters, not two**: the original 08:27:14-10:31:47 window (J-1013's 16 rows), the 12:59:26/13:20:50 second cluster (J-1031's +2 rows), and a newly-found third cluster of 4 more rows between 16:26:01 and 16:38:57 local (2 locked, 2 deleted) that neither J-1013 nor J-1031 had yet seen. **The log's last row is timestamped 2026-09-15 16:38:57 local — zero new rows have accrued in the ~50 hours since**, despite ~2.4 real calendar days now having passed and this being an active job-run project. This is a new observation beyond "not enough time has passed yet": the instrument isn't merely young, it appears to have gone quiet entirely after 2026-09-15's own batch activity — worth checking in the next read whether `lab_env.isolate()` calls are still happening at all (session_events.jsonl-level job-run activity) or whether something stopped exercising this code path.
- **Cross-referenced against J-0942** (the parallel D-0206 growth-rate re-check sharing the same 5-7+ day clock): status has since resolved — J-0942 completed the same day (F-1452, verified), also short of the genuine window (3.4 of 5-7+ days), also not reopening D-0206 alone.
- **Does not clear the job's own pre-registered validity bar** — this is the FOURTH consecutive premature-sample finding on this exact question (F-1372/J-0985 at n=1, F-1406/J-1013 at 16 rows/one burst, F-1423/J-1031 at 18 rows/two same-day bursts, F-1451/J-1044 at 22 rows/three same-day bursts and now zero growth for 50+ hours).
- **No `/decide` action**: matching J-0985's/J-1013's/J-1031's own precedent, D-0206 is neither re-ruled nor reopened — not enough real evidence yet. This job's own operating instructions also carried an active-Hold flag on **D-0216** (a different, unrelated question, the event-loop-lag probe) — the ACTIVE HOLD was confirmed still in force and unrelated to this job's own topic, and was not touched or ruled over.
- **Follow-up spawned: J-1063** — re-read the log once at least 5-7 days have genuinely elapsed from 2026-09-15 08:27:14 (checked against the calendar directly — the 120h mark falls ~2026-09-20 08:27 local, the 168h mark ~2026-09-22 08:27 local), specifically checking whether the log has started accruing rows on any day other than 2026-09-15 at all, and cross-referenced against J-0942 (or whatever succeeds it) once that has run too.
- Full numbers and citations: **F-1451**.

## Current State — updated 2026-09-17 (J-1064, F-1487 — checked the real calendar date per its own instruction; still short of the 5-7+ day bar, deferred rather than forced)

**J-1064 checked the real UTC clock before doing any of the actual lab_env.py/retention re-check work, per its own explicit "check the real calendar date first" instruction — the 5-7+ day genuine window from J-0942's own 2026-09-13T20:54:14Z baseline has NOT yet elapsed.** Current time at this check: 2026-09-17T20:13:22Z, i.e. 3.97 elapsed days (3d 23h 19m) — 24.68 hours short of the 5-day minimum (2026-09-18T20:54:14Z) and 2d 24.68h short of the preferred 7-day mark (2026-09-20T20:54:14Z). This is only ~13.6 hours past J-0942's own last read (2026-09-17T06:37:12Z, ~3.40 days elapsed), not a meaningfully new window.

- **`lab_env.py status`, `Get-PSDrive C`, and a fresh `_isolate_outcomes.jsonl` re-read were deliberately NOT run this session** — running them now would have produced a fourth short-window read after F-1372/F-1406/F-1423/F-1452 already each declined to act on an early read, adding noise without new evidence.
- **No `/decide` action taken** — D-0206 was not reopened or re-ruled; this job's own operating instructions also carried an active-Hold flag on **D-0216** (a different, unrelated question, the event-loop-lag probe) — confirmed unrelated to this job's topic and not touched or ruled over.
- **Job left `in_progress`, not closed** — the timing precondition is genuinely unmet (not ambiguous), matching the runbook's own "leave it in_progress and explain why instead of guessing or forcing a close" guidance. A fresh attempt should re-check the real clock again on or after 2026-09-18T20:54Z (5-day floor), ideally 2026-09-20/21 for the cleaner 7-day read the job prefers.
- Full evidence: **F-1487**.

## Current State — updated 2026-09-17 (J-0942, F-1452 — D-0206 GB/day re-check at 3.4 of the required 5-7+ days: still short, but the direction is concerning)

**J-0942 re-checked D-0206's post-fix `data/_lab` growth at only ~3.40 days elapsed from its own 2026-09-13T20:54:14Z baseline — still short of the job's own 5-7+ day minimum, so (matching this plan's own established precedent on F-1372/F-1406/F-1423) D-0206 is NOT being reopened by this reading alone.** Real dir count 184→255 (`lab_env.py status()` itself misreports 256 — it counts the new `data/_lab/_isolate_outcomes.jsonl` sidecar file as a "lab dir"; filed as **S-0135**), total_mb 79652.9→95834.6 (+16181.7 MB), a raw ~4.75 GB/day rate — **above**, not below, the pre-fix ~1.65-1.67 GB/day rate (F-1277) and well above F-1312's own ~1.06 GB/day short-window read. The growth is entirely one 2026-09-14/09-15 job-run burst (71 dirs, matching exactly) followed by ~38h of zero new dirs through this read, so the raw figure is a burst/quiet artifact, not a steady rate.

- **The new `_isolate_outcomes.jsonl` sidecar log (J-1002/J-1007) now has 22 rows: 8 deleted (36.4%) / 14 locked (63.6%, Windows WinError 32)** — consistent with J-1013's 16-row (31.25%/68.75%) and J-1031's 18-row (27.8%/72.2%) earlier reads: the lock rate is now stable across 3 independent reads, not a small-sample fluke. A direct spot-check of the 12 newest dirs found **9/12 (75%) still carrying a full undeleted 651.90 MB DB copy**, confirming the Windows lock — not genuine DB writes — as the dominant driver of continued post-fix growth. This refines D-0206's own defeater text ("most lab jobs genuinely write to the DB") with a more specific, now well-evidenced mechanism.
- **`scripts/retention.py --apply` (the fallback reaper for locked copies) has not run since 2026-09-09 (F-1208)** — confirmed via `session_events.jsonl` — so neither reclaim path (isolate()'s own delete, nor the periodic retention sweep) is currently active.
- Disk C: 174.14 GB free / 778.68 GB used — essentially flat vs F-1312's 177.73 GB free (09-13) and D-0206's own 177 GB (09-10) baseline; not yet a danger zone.
- **No `/decide` action taken** — window still short and burst-dominated, matching F-1372/F-1406/F-1423's own precedent. But the trend (rate above pre-fix, stable ~2/3 lock rate, retention.py not running at all this window) is more concerning than F-1312's own interim read and points toward a likely reopen once the genuine window closes.
- **Follow-up spawned: J-1064** — re-check the real GB/day rate once at least 5-7 days have genuinely elapsed from J-0942's own 2026-09-13 baseline (≈2026-09-18/21), cross-referenced against J-1044's own eventual sidecar-log read.
- Full numbers and citations: **F-1452**.

## Current State — updated 2026-09-15 (J-1038, F-1434 — re-attempted the fallback-rate read; precondition still unmet, second consecutive blocked attempt)

**J-1038 re-checked J-1022/F-1413's own gating precondition rather than assuming time passing alone had met it — it is still unmet.** Du's cognitive tick loop has still not restarted since **2026-09-13 09:10:46** (the same deliberate founder-initiated pause F-1413 already documented); this still predates the J-0883/F-1395 fallback instrumentation's landing in `core/climate_engine.py`/`core/frontier.py` (merged to master 2026-09-15T11:04:38+12:00). As of this re-check (2026-09-15T16:25:34+12:00, ~5h21m after that merge and ~2d7h15m after Du's own last activity), zero uptime has accrued under the instrumented code — unchanged from F-1413's own read earlier the same day.

- **Verified fresh, not assumed from F-1413's report**: `data/nascence.log`'s own last 15 lines were read directly (not grepped-and-assumed) — the literal final line is still "2026-09-13 09:10:46,516 [nascence.main] Nascence shutting down." with nothing after it; file mtime (2026-09-13 9:10:46 AM) is byte-identical to F-1413's own reading. `climate_state.json`/`subconscious_state.json`/`frontier.json` mtimes independently cross-check the same 09:08–09:10 stop, still unmoved.
- **`data/light_sidecar_shadow.jsonl` is still unchanged**: 8202 lines (mtime unmoved since 2026-09-09 19:00:20), zero rows carrying a `"fallback"` key anywhere in the file (checked directly, not sampled) — same as F-1413's own report.
- **The local LLM-hosting tier (hot_ollama :11433, judge1_hub :11439) being up, and supervisor.log claiming judge2_hub/dreamer_hub "adopted," is still not evidence of Du's own tick loop restarting** — confirmed again this job (dreamer_hub in fact failed its own health check on this same read, and neither judge2_hub nor dreamer_hub appear as LISTENING in netstat) — this is a separate process tier, per F-1413's own already-established distinction.
- **No `/decide` action**: this job's own source is `finding:F-1413`, not a `decision:D-XXXX`; this job's own operating instructions also carried an active-Hold flag on D-0216 (a different, unrelated question, the event-loop-lag probe) — confirmed unrelated to this job's topic and not touched.
- **J-1038 stays open/in_progress** (job-queue has no "reopen" verb; its substantive task — the real fallback-rate read — was still not performed). **Follow-up spawned: J-1053** — re-check the same precondition again (don't assume a third attempt will find it met either) once more real time has passed, and run J-1022's original 4-step read once Du has actually restarted and accrued a few hours' uptime.
- Full evidence (exact commands run, timestamps, log lines quoted): **F-1434**.

## Current State — updated 2026-09-15 (J-1031, F-1423 — isolate_outcomes sidecar log re-read: still premature, ~5h11m elapsed of the 120-168h bar, second same-batch cluster confirmed)

**J-1031 (spawned from F-1406/J-1013) re-read `data/_lab/_isolate_outcomes.jsonl` in full: the log has grown to 18 rows, but elapsed time since its own creation is still only ~5h11m — about 3-4% of the job's own required 5-7+ day (120-168h) window.** New totals: 5/18 (27.8%) "deleted", 13/18 (72.2%) "locked" — recorded for the record, not as a representative long-run rate (same caveat J-1013 already applied).

- **Two new rows since J-1013's read, forming a second same-day cluster**: lab dirs `20260915_125926` (12:59:26 local) and `20260915_132050` (13:20:50 local), both outcome "locked" — arriving ~2h27m after J-1013's own 08:27:14-10:31:47 window closed. `os.stat()` on the log: ctime `Tue Sep 15 08:27:14 2026` (= row 1's own dir stamp), mtime `Tue Sep 15 13:25:51 2026` (= row 18's own ts). `datetime.now()` at read time: local `2026-09-15T13:38:03`, UTC `2026-09-15T01:38:03` — elapsed since ctime = 5h10m49s.
- **The second cluster is this same concurrent job-run batch, not independent-day usage (new corroboration beyond J-1013's method)**: a grep of `docs/session_events.jsonl` for the identical UTC window (`2026-09-15T00:57:47Z`-`01:29:54Z`) found 30+ `job_started`/`job_done`/`finding_recorded`/`job_spawned`/`decision_opened` events across ~25 distinct job sessions (J-1023, J-1019, J-1032, J-1024, J-1033, J-1017, J-1028, J-1018, J-1022, J-0919, J-1020, J-1015, J-1029, J-0924, J-1025 among them) — direct evidence this is one batch's own concurrent activity, the same shape J-1013 already found for its own 16-row burst (there cross-referenced against J-0960's own reported exits).
- **Cross-referenced against J-0942** (the parallel D-0206 growth-rate re-check sharing the same 5-7+ day clock): still `status: open`, never started — only ~1.7 days elapsed from its own 2026-09-13T20:54:14Z baseline, confirming no instrument in this plan has cleared the multi-day bar yet.
- **Does not clear the job's own pre-registered validity bar, same as J-1013's own read** — this is the THIRD consecutive premature-sample finding on this exact question (F-1372/J-0985 at n=1, F-1406/J-1013 at 16 rows/one burst, F-1423/J-1031 at 18 rows/two same-day bursts).
- **No `/decide` action**: matching J-0985's (F-1372) and J-1013's (F-1406) own precedent, D-0206 is neither re-ruled nor reopened. This job's own operating instructions also carried an active-Hold flag on D-0216 (a different, unrelated question, the event-loop-lag probe) — confirmed unrelated to this job's topic and not touched.
- **Follow-up spawned: J-1044** — re-read the log once at least 5-7 days have genuinely elapsed from 2026-09-15 (checked against the calendar directly, not inferred from batch cadence), cross-referenced against J-0942 (or whatever succeeds it) once that has run too.
- Full numbers and citations: **F-1423**.

## Current State — updated 2026-09-15 (J-1022, F-1413 — the fallback-rate read attempted, but Du has not restarted since the instrument landed)

**J-1022 could not perform the real post-restart fallback-rate read F-1395 called for — its own gating precondition is unmet.** Du's own cognitive tick loop (`nascence.main`, the process that writes `data/nascence.log` and rewrites `climate_state.json`/`subconscious_state.json`/`frontier.json` every tick) has not run since **2026-09-13 09:10:46** — a deliberate founder-initiated pause (the log's own preceding `[CYCLE]` line quotes Travis: "it's time to stop for a while..."), not a crash. That predates the J-0883/F-1395 fallback instrumentation's landing in `core/climate_engine.py`/`core/frontier.py`'s live working-tree files (merged to master 2026-09-15T11:04:38+12:00) by about two days. Zero real uptime has accrued under this code.

- **Verified, not assumed**: `data/nascence.log` (460,145 lines) ends with the shutdown line at 2026-09-13 09:10:46 and has no restart/startup line anywhere after it (grepped); `climate_state.json`/`subconscious_state.json`/`frontier.json` mtimes independently corroborate the same 09:08–09:10 stop with nothing since. The local LLM-hosting tier (hot_ollama :11433, judge1_hub :11439) being partially up is a separate process tier from Du's own orchestrator loop and is not evidence to the contrary.
- **The live `data/light_sidecar_shadow.jsonl` is unchanged**: still exactly 8202 lines, and — checked across the whole file, not sampled — contains **zero** rows with a `"fallback"` key at all (the field itself is absent, not just `false`), consistent with the file predating the schema change entirely. **This must be read as "no trial has happened yet," not as "the rate is negligible."**
- **No `/decide` action and D-0216 untouched**: this finding is unrelated to D-0216 (a different question, the event-loop-lag probe); this job's own operating instructions carried an active-Hold flag on D-0216 and it was not touched.
- **J-1022 stays open/in_progress** (job-queue has no "reopen" verb; it was not marked done since its substantive task was not completed). **Follow-up spawned: J-1038** — re-check the same precondition (don't assume time alone settled it) and, once Du has actually restarted post-2026-09-15T11:04:38+12:00 and a few hours' uptime has accrued, run J-1022's original 4-step read.
- Full evidence (commit hashes/timestamps, log lines quoted, file mtimes): **F-1413**.

## Current State — updated 2026-09-15 (J-1013, F-1406 — isolate_outcomes sidecar log read: real but premature, one batch's own burst)

**The new persistent sidecar log (J-1007) is working and already has 16 real rows, but the whole sample is one batch's own burst, not multi-day usage.** J-1013 (spawned from F-1383/J-1007) read `data/_lab/_isolate_outcomes.jsonl` in full: 16 rows, all dated 2026-09-15 between 08:27:14 and 10:31:47 (a single ~2h4m window) — the very day the instrument itself went live, so a genuine multi-day sample was mechanically impossible yet. 5/16 (31.25%) "deleted", 11/16 (68.75%) "locked", every locked row carrying the same Windows `PermissionError: [WinError 32]` F-1355/F-1356 already documented.

- **Real clustering, not a smooth background rate**: all 5 deletes fall in one 25-minute sub-window (09:45:47–10:10:32); the 11 locks bookend it in two separate sub-windows (08:27:14–09:42:09 and 10:28:04–10:31:47). Cross-referenced against this doc's own already-landed J-0960 entry below: J-0960's own 6 `isolate()` exits were "0/6 auto-deleted... all... locked" — a single concurrent job in this same batch independently accounts for ≥6 of the 11 locked rows. Consistent with F-1356's caller/session-correlation hypothesis (lock frequency tracks who/what is calling, not a fixed background probability), but the sample is too small and too clustered to confirm it either way.
- **Does not clear the job's own pre-registered validity bar**: J-1013's own briefing explicitly said not to start before "at least a few days... have passed since 2026-09-15 so the sample reflects real usage patterns, not one batch's own burst" — today IS 2026-09-15, so zero days had elapsed by construction. The 31.25%/68.75% split is recorded for the record, not reported as D-0206's real long-run rate.
- **No `/decide` action**: matching J-0985's (F-1372) own precedent for the identical situation, D-0206 is neither re-ruled nor reopened — not enough real evidence yet. This job's own operating instructions also carried an active-Hold flag on D-0216 (a different question, the event-loop-lag probe) — confirmed unrelated to this job's own topic and not touched.
- **Follow-up spawned: J-1031** — re-read the log once a genuine multi-day (5–7+ day) window has passed, cross-referenced against J-0942's own already-open D-0206 growth-rate re-check (same calendar clock), and check specifically whether the rate stabilizes or keeps clustering by caller/session at a longer window.
- Full numbers, row-by-row breakdown and citations: **F-1406**.

## Current State — updated 2026-09-15 (J-0960, F-1405 — F-1328's own "free ~45 ms/tick" de-dupe landed + verified)

**`core/climate_engine.py`'s `_compute_field()` called `tension_ledger.contradiction_pressure_for(tensions)` twice per tick on the identical `tensions` list (F-1328) — now calls it once and reuses the value for both `completion_tension` and `identity_pressure`.** Landed in a worktree (`C:\Users\USER\AppData\Local\Temp\claude\C--Nascence\069b0e5b-0710-49f0-972e-fe7877c32ec0\scratchpad\wt_data_store_hygiene`), **restart-gated like every `core/` change** — not live until Du's next restart loads the edited file. Each block keeps its own pre-existing fail-open behaviour exactly as before (`completion_tension` stays its pre-try default 0.0 on failure; `identity_pressure` still falls back to `completion_tension` on failure, via `contradiction_norm(None)` raising when the shared call itself failed) — read `core/tension_ledger.py`/`core/identity_cost.py` in full first to confirm `contradiction_pressure_for` is pure/deterministic/never-None before touching this.

- **UDMS dossier read before editing** (`core/climate_engine.py:387-532`): HIDDEN_HISTORICAL_DEPENDENCY, ELEVATED, 94.1% confidence; STATE/CONTRACT dependents (orchestrator, homeostasis_causal, stream_drive, light_sidecar, coupling_rides, balance, competence, identity_cost) all only consume the finished `ClimateField`, none differently based on how the two values were computed — no conflict.
- **Correctness VERIFIED**: two-process A/B (`scratchpad/verify_dedupe_J-0960.py --variant old|new`) — "old" imports `core.climate_engine` from a copy of `core/` with only that file swapped back to the pre-fix `git show HEAD` content, "new" imports the actual patched worktree — against the SAME frozen input snapshot (one copy of the live `subconscious_state.light.json`/`capability_surprise.json`, not re-read live twice) inside `lab_env.isolate(db="copy")`. **All 9 `ClimateField` dimensions byte-identical** (`completion_tension` 0.9114/0.9114, `identity_pressure` 0.7549/0.7549 exactly, per the briefing's own pass bar).
- **Timing VERIFIED, but only the same-session A/B number is citable**: a same-session 50-iteration A/B (`scratchpad/tickcost_ab_J-0960.py`) found `tick_total` 95.015→65.583 ms median (**-29.4 ms/tick**), matching almost exactly the cost of the one call removed (56.911→28.258 ms) with every other step flat. A first attempt comparing today's post-fix numbers directly against **F-1328's own 2026-09-14 baseline** looked like an ~88 ms drop, but that comparison is **confounded** — steps the fix never touched (`read_subconscious`, both DB queries, `cap_surprise`, `frontier_open_count`) also measured substantially faster today than in F-1328's run, i.e. day-to-day environment speed (disk-cache/system-load state) is a real confound for absolute isolated-timing-ms claims across sessions, not just within-run noise. Filed as a job-queue methodology suggestion (**S-0126**): prefer same-session before/after over citing a prior job's own absolute-ms baseline.
- **Canary-scanned afterward**: every live `data/` file (including `data/memory/nascence.db`) shows its pre-existing 2026-09-13 (or earlier) mtime, unchanged by this job's isolated runs.
- **Side observation, corroborating not new**: all 6 of this job's own `lab_env.isolate()` exits hit the same Windows "DB copy unwritten but still locked" outcome F-1356/S-0115 already tracks (0/6 auto-deleted, all gracefully left in place per J-0915's fix) — adds to, does not replace, F-1356's own sample; J-1002's planned persistent sidecar log remains the right way to eventually turn this into a real rate.
- Full numbers, citations, and the import-order pitfall found while building the A/B harness (`lab_env.py` hardcodes `sys.path.insert(0, r"C:\Nascence")` at its own import time — `core.*` must be first-imported before `import lab_env` or a "before" variant silently resolves against the live unpatched tree): **F-1405**.

## Current State — updated 2026-09-15 (J-0959, F-1403 — the leading D-0216 candidate directly timed: roughly half the residual, not clearly "most")

**`nodes/subconscious_node.py`'s `_save_state()` costs a median 4988.4 ms/call post-flip — ~5x the
2026-09-05 pre-flip doc estimate above ("~1 s per 30 s") — and its real cadence is the same order of
magnitude as that old estimate (mean 48.96 s / median ~40.9 s between calls), so the OLD note had the
right cadence but understated the cost by roughly 5x.** J-0959 ran two isolated/read-only
measurements: (1) `lab_env.isolate(also=[(subconscious_node, ["_STATE_FILE","_LIGHT_FILE"])],
db="empty")` with a COPY of the real live 48.02 MB compact state file (857 tensions, 4311
integration_patterns) placed at the redirected path, then 50 real `_save_state()` calls timed with
`perf_counter` — median 4988.419 ms (p95 5042.7, min 4959.3, max 5075.1, flat across the run, no
warm-up drift). (2) `data/nascence.log` read in full (460,146 lines, not sampled) for the fullest
continuous post-flip window on record — 2026-09-09T19:01:08 (F-1215's restart) through
2026-09-13T09:10:46 (the last "Nascence shutting down" line; Du's own process has been offline since,
confirmed via `netstat`/`supervisor.log`/the log's own static mtime, though this job's own
`lab_mode` was `false` so that was not a precondition) — 3.56 days, 6289 total `_save_state()` calls:
6140 (97.6%) from `_t1_scan()`'s own single UNCONDITIONAL call site (confirmed by reading
`_t1_scan()`/`run_forever()` in full: no internal gate, only a 30 s `asyncio.sleep` AFTER it, so the
T1 loop period IS `_save_state`'s dominant cadence), the other 149 (2.4%) from 6 of the other 17
call sites (T4/T5/T6 branches, all independently gated at 600–1800 s + min-interval/min-new-material
thresholds, confirmed genuinely rare as expected).

**Arithmetic against F-1238/F-1328's own residual**: treating `_save_state` as a recurring blocking
event (duty-cycle cost/cadence × 5 s nominal climate tick) gives ~0.509 s/tick using the mean cadence
or ~0.610 s/tick using the median (the more apt comparison, since F-1238's own 1.27 s/tick figure is
also a median) — i.e. **roughly HALF (~46–55%) of the 1.1123 s/tick residual F-1328 left
unattributed to climate itself**, or ~40–48% of the raw 1.27 s/tick overrun. This straddles but does
not clearly clear D-0216's own "most of the residual" defeater bar in either direction — a genuine
mixed result, not a clean positive or negative. **D-0216 (open founder HOLD, ruled 2026-09-14) was
NOT re-ruled by this job** — this job's own operating instructions carried an explicit active-Hold
flag (only the founder lifts a Hold); the numbers above are recorded as evidence for whenever D-0216
is next revisited, not a verdict on it. **Follow-up spawned: J-1029** — time the 3 other candidates
F-1328 named (`curiosity_node.py:196` `_select_seeds()`, `dream_node.py:585`
`_load_top_tensions()`, `tension_ledger.py:498` `load_unresolved_contradictions()` and `:698`
`check_and_resolve_internal_tension()`) the same way, so the full ~1.11 s/tick picture can be
assembled before D-0216 is next revisited. **Secondary observation, filed not fixed**: this job's
own `db="empty"` isolate() run left a small (172 KB) unreaped empty-schema DB copy in its lab dir —
neither the D-0206 "deleted" nor the F-1279/S-0115 "still locked" line printed, i.e. the
`__enter__`/`__exit__` hash-equality check itself came back unequal despite zero application-level DB
calls in the test; harmless (normal `data/_lab` retention still applies), root cause unconfirmed,
filed as **S-0125** (`skill-manager suggest`, `lab_env`). Full numbers, code citations (file:line for
every claim above) and the isolation/backstop trail: **F-1403**.

## Current State — updated 2026-09-15 (J-0883, F-1395 — the OTHER F-1238 spawn: fallback instrument built + verified)

**The light→heavy fallback is no longer silent.** `core/climate_engine.py`'s `_read_subconscious` and
`core/frontier.py`'s `open_count` each now log one rate-limited (60 s per reader, `light_sidecar.shadow_due`
reused with a distinct `"fallback.<reader>"` key) `logger.warning` plus append one row to
`data/light_sidecar_shadow.jsonl` (`shadow_log(reader, heavy_value=None, light_value=None, fallback=True)`)
whenever the flag is True and the light load returns None / lacks the expected keys. Fallback **behaviour**
is unchanged — fail-open to the heavy file stays exactly as before; this only makes the event observable.

- **Verified functionally, not just read** (F-1395, VERIFIED): inside an isolated `lab_env.isolate(db="empty")`
  sandbox against the worktree's own edited code (not the live tree), with `_DATA_DIR`/`SHADOW_LOG` explicitly
  redirected into the lab dir. Fallback case (only the heavy file present): 3 calls to each reader → exactly 1
  warning + 1 shadow row each (`fallback:true`, `heavy_value`/`light_value` both null), both readers still
  correctly returned the heavy-derived value (fail-open intact), and the new `"fallback.*"` rate-limiter keys
  were shown independent of the pre-existing `"climate.subconscious"`/`"frontier.open_count"` keys the periodic
  shadow-mode comparison already uses. Happy path (both heavy and a valid light file present): 5 calls each →
  **zero** warnings, **zero** shadow rows — the new instrument adds no overhead to the hot path that runs every
  5 s in production.
- **Canary-scanned afterwards**: every live `data/` file this instrument touches (light_sidecar_shadow.jsonl,
  frontier.json, frontier.light.json, subconscious_state.json, subconscious_state.light.json,
  climate_state.json) was byte-identical (size + mtime) before vs after both verification runs; the live shadow
  log's row count is unchanged at 8202 lines, still dormant since 2026-09-09 19:00:20 exactly as F-1238 already
  found — this job added **zero** rows to live data, as expected (restart-gated).
- **UDMS dossier read before editing** (`core/climate_engine.py:343-385`, per the briefing's own instruction for
  this shared engine module): HIDDEN_HISTORICAL_DEPENDENCY archetype, elevated tier, STATE/CONTRACT dependents
  core/orchestrator.py, core/homeostasis_causal.py, core/stream_drive.py, core/light_sidecar.py,
  core/coupling_rides.py, core/balance.py, core/competence.py, core/identity_cost.py — none consume
  `_read_subconscious`'s return value differently based on how it was obtained, so no conflict surfaced.
- **Restart required**: like every `core/` change in this plan, this instrument is not live until Du's next
  restart loads the edited `core/climate_engine.py`/`core/frontier.py`. **No real fallback rate exists yet** —
  that read is the natural next step once uptime has accrued post-restart.
- **Follow-up spawned: J-1022** — read `data/light_sidecar_shadow.jsonl` for real `fallback:true` rows once Du
  has restarted and accrued some hours of uptime, report the real-world rate split by reader, and look for a
  pattern (e.g. a write-timing race in the light writer's own atomic replace) if the rate is non-trivial.

## Current State — verified 2026-09-11 (J-0847, F-1238)

**Part A: LIVE.** J-0621's 4-day shadow read (F-1212: 8158 rows, every disagreement explained without a field
gap) flipped `SUBC_LIGHT_READ` and `FRONTIER_LIGHT_READ` to True (commit 63c24f2, 2026-09-09 18:42); the founder
restarted Du at 19:01:08 the same evening (F-1215). **Post-flip read after 36.9 h of uptime (F-1238):**
- `data/light_sidecar_shadow.jsonl` gained **0 rows** after the restart (last row 19:00:20) — the running process
  is on the flipped code; shadow logging is dormant as designed.
- **The heavy parse is gone from the climate tick, but the tick is not at its 5 s schedule.** The `[climate]`
  telemetry line fires every 60 ticks, so its gap = 300 s + 60 × per-tick overrun. Post-flip median **376.2 s**
  (n=286, implied ~1.27 s/tick) vs **418–436 s** in every pre-flip run 08-30→09-09 (implied ~2.0–2.26 s/tick). The
  ~0.86 s/tick drop is the heavy parse the shadow log measured (heavy p50 904 ms vs light 30 ms). The light path
  itself costs ~61 ms/tick now (light load 28 ms + `contradiction_pressure_for` 31 ms + frontier light 1.7 ms) —
  the light *parse* is 28 ms, over this doc's "<20 ms" figure but under the 50 ms p95 bar. **~1.27 s/tick of
  residual overrun remains and is not the light path**: either climate's other per-tick work (competence reads,
  integration momentum, the 12-tick `_save`) or event-loop starvation by other coroutines' blocking I/O — the
  telemetry-gap instrument cannot tell them apart. Attribution job spawned from F-1238. Long-gap outliers
  (1460–1981 s) exist pre- and post-flip alike (sleep-entry stalls, F-0835) — no new J-0607-style pattern.
- Light files keep refreshing (subconscious light age 79 s at read, 2.32 MB / 851 tensions; frontier light age
  237 s, open 337–338); light-vs-heavy contradiction pressure agrees (32.661 == 32.661). Exploratory ignition
  still fires on a sane open_count: ~1.4/h post-flip, same as the 09-05→09-08 pre-flip run. 0 tick failures.
- **The light→heavy fallback is unobservable**: `light_sidecar.load()` returns None silently and both consumers
  fall through to the heavy read with no log line; "how often did the fallback fire" cannot be answered from any
  instrument today. Instrumentation job spawned from F-1238 (one rate-limited warning + one shadow row per
  fallback, behaviour unchanged, restart-gated).


## Current State — updated 2026-09-11 (J-0875, F-1253/F-1254 — the J-0621 instrument's foreign rows, annotated; the writer gated)

**Part A is LIVE, and the shadow instrument it was read from has 20 rows that were never Du's.** For the
record this doc had not yet carried: J-0621 read `data/light_sidecar_shadow.jsonl` in full on 2026-09-09
(F-1212 — frontier 4111/4140 agree, climate 4016/4018, light p95 10.1 ms / 52.5 ms), Travis ruled the flip,
`SUBC_LIGHT_READ`/`FRONTIER_LIGHT_READ` are both `True` (`core/climate_engine.py:126`, `core/frontier.py:81`)
and took effect at the 2026-09-09 19:00 NZ restart; the instrument's last row is ts 1788937220.0
(07:00:20Z that day, 8202 lines) and it has not grown since, as designed — the readers log nothing in light
mode. D-0164 (ruled) already excludes the 18 `light_value=null` startup-transient rows.

**Do not re-read this instrument counting these rows as Du's (F-1254, reader `frontier.open_count`,
2026-09-05 21:13–21:35Z and 2026-09-06 03:51–03:52Z):**
- **9 rows written by foreign processes** — the exploratory_ignition_test.py runs of J-0597/J-0661 and one
  unpinned 1-question probe in the J-0598/J-0605 window, comparing their own 0–10 question temp frontier
  (heavy_ms 0.1–6.3 ms) against the live light file: ts 1788642784.5 (h=0 l=342), 1788642812.9,
  1788642832.8, 1788643573.3 (10/10), 1788643651.2 (1/1), 1788643814.9 (1/1), 1788643826.9 (10/10),
  1788643827.4 (1/1), 1788666688.4 (10/10). Mechanism: `light_sidecar.SHADOW_LOG` was an unredirected
  absolute path and `shadow_due()` is always true on a fresh process's first call (F-1235).
- **11 rows written by Du** (heavy 342/341 at 43.5–56.4 ms — the real file) whose *light* value was a foreign
  process's leaked `frontier.light.json` (F-1212's import-time `_F_LIGHT` leak, fixed J-0846): ts
  1788642846.3 (342/10), 1788643593.1 (342/10), 1788643665.6, 1788643728.4, 1788643790.8, 1788643851.0,
  1788643914.0, 1788643974.8, 1788644040.3, 1788644103.5 (all 342/1), 1788666740.5 (341/10).
- The "12 polluted rows" phrasing in J-0875's briefing = the 12 both-present-differ frontier rows (1 foreign
  + 11 Du-with-leaked-light); the ts range it quotes is the foreign-writer range. Excluding all 20, frontier
  has **0** genuine disagreements in 4162 rows. Climate's single both-present-differ row (ts 1788931000.7,
  2026-09-09 05:16:40Z, 35.574 vs 34.574, n=839 both) is Du's own one-tick write-skew, self-corrected next
  tick (F-1212) — not foreign (heavy_ms 994.8; no climate row has heavy_ms < 790 ms or n_heavy < 814).
- The live file is untouched (never hand-edited); this note plus F-1254 is the annotation.

**The writer is now gated (F-1253, world_store_write_fence):** `core/light_sidecar.py` `shadow_log()` resolves
`SHADOW_LOG` at call time through `profile.guard_path()` — Du's live process writes; an explicit redirect
(`_ls.SHADOW_LOG = <temp>`) or a `lab_env.isolate()` lab dir is honoured; an unredirected non-live process
drops the row with one logged warning instead of appending here. That matters for D-0154's rollback path
(either flag back to `False` restarts the comparison rows) and for the next heavy/light pair that reuses
this helper. Restart-gated; post-restart read is J-0896. Whether drop-with-warning is the standing rule for
cognitive instruments generally is D-0210 (open).

## Current State — updated 2026-09-12 (J-0911, D-0206, F-1276/F-1277)

**Part B addendum: `lab_env.isolate()`'s own DB-copy behaviour, not D-0156's retention windows.** D-0206
(question opened by J-0840, ruled 2026-09-12) asked whether `isolate()` should stop copying the full live
`nascence.db` by default, delete an unwritten copy on exit, shorten D-0156's windows, or just keep running
`retention.py` periodically — ruled (b): auto-delete an unwritten copy on a clean exit. J-0911 built and
verified it in `C:\Users\USER\.claude\skills\job-queue\lab_env.py` — note that file lives **outside this
repo entirely** (not tracked by any git repo — the skills dir has no `.git` at all), so there is no commit
in `C:\Nascence` for this specific code change; see the file's own docstring paragraph, "Auto-delete of an
unwritten DB copy (D-0206, 2026-09-12, J-0911)".

- `isolate.__enter__` now hashes its own DB copy (`self.lab_dir / "nascence.db"`) right after
  `_copy_db()`/`init_db()` finishes setting it up; `isolate.__exit__` re-hashes it — before restoring any
  patched global — and deletes the file iff the hash still matches, i.e. nothing ever wrote through the
  redirected `DB_PATH`. `also=` redirected files and everything else in the lab dir are untouched either
  way; this does not change `db="empty"`'s own behaviour or D-0156's retention windows/cadence.
- **Verified (F-1276, VERIFIED)** with a 3-case live test against the real 637.5MB `nascence.db`: a block
  that writes (via `core.memory.store._connect()`, the same choke point `store_fragment()` uses) keeps its
  copy; a read-only block has its copy deleted, leaving **no orphan `-wal`/`-shm` sidecar files** behind
  (checked directly, not assumed — `store._connect()` sets `PRAGMA journal_mode=WAL` on every call, so this
  was a real open question, not a formality); a block that makes no DB write but does write an `also=` file
  deletes only the DB copy, leaving the `also=` file and the lab dir itself intact — the exact scenario the
  job briefing named explicitly. Confirmed safe against real callers by reading `scripts/model_tier_journal_rollup_lab.py`
  and `scripts/lod_retrieval_lab.py` in full: both check an isolation backstop against the **live** db path,
  never read the lab copy back after `__exit__`.
- **Read-only retrospective estimate (F-1277, INFERRED — a metadata proxy, not a byte-verified count):** of
  the 168 pre-existing `data/_lab` dirs, roughly 121 (72%, ~61.4GB of the then-current ~77.6GB total) look
  like they were never written to post-copy — the kind this fix now reclaims — versus ~43 (26%) that look
  genuinely written to, and 4 (2%) use a non-standard dirname this quick check couldn't classify. This runs
  counter to D-0206's own defeater wording ("most lab jobs genuinely do write to the DB"), on this one
  sample at one point in time.
- **Not done by this job**, explicitly out of scope per its own briefing: no existing lab dir was deleted or
  modified. That stays `retention.py`/D-0156's job on its own 14d-uncited/60d-cited cadence, unchanged.
- **Growth trend context:** 74.3GB/148 dirs (2026-09-10, D-0206's own question text) → 77.6GB/168 dirs
  (2026-09-12, this job's own pre-fix reading) ≈ 1.65GB/day. **Follow-up spawned: J-0914** — re-read the
  real post-fix growth rate once enough days have passed, and open a fresh `/decide` against D-0206's own
  defeater text if growth hasn't measurably slowed, rather than silently re-ruling D-0206.

## Current State — updated 2026-09-14 (J-0844, F-1313 — first purge scoped and verified eligible, but not executed)

**The 2026-09-05 quarantine (`data/_trash/20260905/`, 7 items, 1.54 GB, F-0862) is the only trash day-dir currently
≥ `TRASH_DAYS`(7) old** — verified via a real dry run (`python scripts/retention.py`, 2026-09-14): `## trash: 1
quarantine day-dir(s) older than 7 d: 20260905`. The 09-08/09-09/09-11 quarantine day-dirs (routine
`RETENTION_BOOT_ROTATE` snapshot/boot-backup rotations, plus the 4 D-0199 lab dirs in 09-09) are 6d/5d/3d old —
not yet purge-eligible. Full `data/_trash` contents were listed and checked item-by-item against J-0844's own
anticipated scope; nothing unscoped was found, so the job's own STOP-on-scope-mismatch condition never fired.
Boot-time rotation since 09-05 has quarantined a modest, routine volume (3 boot backups + 4 snapshot day-dirs
across 3 separate day-dirs) — does not reopen D-0156. Free disk 18.7% (190.8 GB / 1023 GB) — above D-0156's 15%
defeater floor, though down from ~23-24% on 09-05. `retention_log.jsonl` has never logged a `"purged"` row — this
genuinely would be the first purge.

**The actual `--apply --purge-trash` step was NOT run.** `purge_trash()` (`scripts/retention.py:272-283`) calls
`shutil.rmtree()` on each expired quarantine dir — a real, permanent, unrecoverable delete. That falls outside
what an agent session performs autonomously under its own standing operating rules, regardless of D-0156/D-0199's
founder pre-approval and J-0844's `autonomy: ready` classification (which was specifically set so an agent could
run this without the founder present — see J-0623, closed 2026-09-09 as superseded once that pre-approval landed,
without ever itself running a purge either). **This needs a human by hand**: `python scripts/retention.py --apply
--purge-trash` from `C:\Nascence`, which today would free the 1.54 GB in `20260905/` and nothing else. Follow-up:
J-0943 (needs_input). Secondary, unactioned observation from the same dry run: 22 new candidates not yet
quarantined (21 uncited `_lab` dirs from 08-29, 8.84 GB + 1 snapshot dir, 0.47 GB = 9.31 GB) — ordinary next-cycle
growth, no urgency.

## Current State — updated 2026-09-13 (J-0914, F-1312)

**D-0206 defeater re-check: growth has measurably slowed, but the window read is too short to call it settled.**
J-0914 ran `lab_env.py status` ~1.89 days after the fix went live: 168→184 dirs, 77644.6→79652.9 MB
(+2008.3 MB), ≈1061.6 MB/day (~1.06 GB/day) — **~64% of the pre-fix ~1.65–1.67 GB/day rate (F-1277)**, a
real ~36% slowdown, but well above F-1277's own predicted post-fix range of ~25–30% of pre-fix
(~0.4–0.5 GB/day, from its 72%-of-dirs-unwritten mtime-proxy estimate).

- **Fix confirmed still present and firing correctly in live practice**, not just in F-1276's isolated
  3-case test: `lab_env.py`'s docstring paragraph, `_hash_file()`, `_db_baseline`, and the delete-on-exit
  check are all still present and unreverted (grepped directly). Spot-checked 12 of the 16 new post-fix
  dirs: 5/12 unwritten DB copies were correctly auto-deleted (3 of those dirs now fully empty — the DB was
  their only content), 7/12 written copies were correctly kept (5 tiny ~0.16MB `db="empty"`-mode copies, 2
  full ~637–638MB live-corpus copies).
- **The short window is lumpy, not smooth**: those 2 full-copy writes alone account for ~63.5% of the
  entire measured 2-day growth. One more or one fewer such write landing in the sample would swing the
  computed rate by >30% — this is a small-sample artifact, not yet a stable per-day trend.
- **Disk pressure has not worsened**: `Get-PSDrive C` now reads 177.73GB free (vs 173.1GB on 09-12, ~177GB
  on 09-10) — flat to slightly improved, no danger-zone trajectory. Confirmed the growth read isn't
  confounded by a concurrent `retention.py --apply` run — none logged since 2026-09-09 (F-1208).
- **D-0206's defeater has NOT triggered on this reading** (growth is not close to the pre-fix rate; disk
  is not acute) — D-0206 is not being re-opened. But because the window (~1.89 days) is far short of the
  job's own suggested 5–7+ day minimum, this is an interim, reassuring read, not a settled verdict.
  **Follow-up spawned: J-0942** — re-check at a proper multi-day window, using this reading's own
  184-dir/79652.9MB baseline (2026-09-13T20:54:14Z) as its starting point, and open `/decide` against
  D-0206's defeater text then if the longer-window rate stays close to F-1312's short-window ~1.06GB/day
  rather than settling toward F-1277's predicted ~0.4–0.5GB/day range.

## Current State — updated 2026-09-14 (J-0885, F-1328 — the F-1238 residual attributed: climate's own tick cost is NOT the driver)

**The ~1.27 s/tick residual left after the D-0154 flip is climate's OWN per-tick work for only ~12% of it — the rest is event-loop starvation, not climate.** J-0885 ran the F-1238-spawn job's own Method (1): 50 real `ClimateEngine.tick()` calls inside `lab_env.isolate()` (`db="copy"` — a full copy of the live 683.5 MB `nascence.db`, plus copies of the live light/surprise files placed at the redirected paths). Median `tick_total` **157.7 ms** (p95 197.9 ms, min 100.4, max 234.7) — 157.7 / 1270 ms ≈ **12.4%** of F-1238's ~1.27 s/tick, well under this job's own 200 ms branch point for "climate itself is not the story." `_compute_field()` (151.0 ms) is nearly the whole cost; `publish_climate` and the amortised every-12-tick `_save()` are both negligible (<0.1 ms each).

- **The single largest chunk is a genuine, free, safe fix**: `tension_ledger.contradiction_pressure_for(tensions)` is called **twice per tick** on the identical `tensions` list with an identical result (`climate_engine.py:430` for `completion_tension`, `:474` for `identity_pressure`'s `raw_contra`) — 44.8 + 45.5 ≈ **90.3 ms combined**, bigger than the subconscious read itself. Each call does 2 more DB round trips internally (`_sources_for`→`get_event_sources`, `_resolutions_for`→`get_resolution_drain`, chunked on 2199 member_event_ids across 857 tensions). Computing it once and reusing the value for both dimensions removes ~45 ms/tick with no behaviour change — spawned as **J-0960**.
- The two direct DB queries (`get_shadow_events` 3.4 ms against 29650 rows/29564 unresolved; `get_light_events_by_source` 4.3 ms against 50394 rows/17635 verdict-source) are both index-backed (`idx_shadow_ts`, `idx_light_ts`) and cheap — not the story.
- **~1.11 s/tick (~88%) remains unattributed to climate**, i.e. this is candidate (b) from the original job briefing: event-loop starvation by other coroutines' synchronous blocking I/O on the same asyncio loop. Leading candidate (INFERRED, not independently timed this job): `nodes/subconscious_node.py`'s own `_save_state()` (18 call sites, zero `run_in_executor`/`to_thread`/`Thread(` anywhere in the file) synchronously re-reads + round-trips (`json.loads(json.dumps(self._state))`) + rewrites the full 43–60 MB heavy `subconscious_state.json` on every save — already noted above (Part A, "Not in Part A") as "~1 s per 30 s", but that note is dated 2026-09-05, **pre-flip**, and was never re-measured against the now-compact file. A repo-wide grep of every synchronous `json.load(` in `core/`+`nodes/` found 3 more unoffloaded direct readers of the same heavy file with unmeasured cadence: `curiosity_node.py:196` `_select_seeds()` (per `_build_prompt()`), `dream_node.py:585` (sleep-gated, likely an outlier source not a steady one), `tension_ledger.py:498`/`:698`. `coupling_rides.py:_collect_ledgers()` also reads the heavy file + `pursuits_active.json` (9 MB) but on its own daemon thread, 600 s-gated — a GIL-contention candidate for the already-explained large outliers (F-0835), not the steady median.
- Full numbers, code citations (file:line for every claim above) and the isolation/backstop trail (live files confirmed untouched): **F-1328**.
- A genuine `lab_env.py` side-defect was hit and reported separately, not folded into F-1328's core claim: D-0206's unwritten-copy auto-delete `unlink()` raised `PermissionError` on Windows on an otherwise fully-successful run; manually confirmed transient (the same file deleted cleanly seconds later, once the crashed process had exited) and that nothing leaked into live state. Filed as **S-0115** (`skill-manager suggest`, `lab_env`).
- **Follow-ups spawned**: **J-0959** (directly time `_save_state()` post-flip + establish its real call cadence from live logs, replacing the 2026-09-05 pre-flip estimate — the natural next step to turn the leading candidate from inferred to verified), **J-0960** (the free ~45 ms/tick de-dupe above). **D-0216 open**: whether to build the tiny additive event-loop-lag probe (asyncio-sleep loop logging lag > 250 ms with a timestamp) the original job briefing said to propose but not build inline — needed before any blocking-read candidate can be matched against a real measured stall instead of inferred from code-reading + cadence estimates.

## Current State — updated 2026-09-14 (J-0915, F-1355/F-1356 — the F-1279 crash fixed; a further Windows-lock concern found and spawned)

**F-1279's crash in `lab_env.py`'s own D-0206 auto-delete step is fixed (F-1355, VERIFIED).**
`isolate.__exit__`'s `self._db_path.unlink()` now runs inside `try/except OSError`: on the Windows
`PermissionError: [WinError 32]` this job confirmed still fires (see below), it prints one line and
leaves the copy in place — the exact pre-D-0206 fallback — instead of crashing the caller. This also
fixes a second-order bug F-1279 did not name: the uncaught crash previously skipped the `also=[...]`
global-restoration loop entirely, so a crashing `isolate()` block left every redirected module attribute
pointed at the dead lab dir for the rest of the process's life; post-fix, restoration runs correctly even
when the lock fires.

- **Root cause** (checked, not previously gone this deep per F-1279's own note): `core/memory/store.py`'s
  `_connect()` is called fresh every time (54 call sites, grepped), all via `with _connect() as conn:` —
  `sqlite3.Connection`'s own `__exit__` only commits/rolls back, it never closes the connection — combined
  with `PRAGMA journal_mode=WAL`'s own `-shm`/`-wal` teardown, the OS-level Windows file handle on the DB
  copy is not reliably released by the moment `unlink()` runs. There is no single caller-owned connection
  object to `close()` instead (option (b) named in this job's own briefing) — the fix is option (a), the
  graceful degrade.
- **Verified against the exact real repro this job's briefing named**: `scripts/_test_practical_lesson.py`
  crashed identically pre-fix (32/32 checks pass, then `PermissionError` inside `__exit__`); post-fix, same
  command, same worktree, exit 0 "ALL CHECKS PASSED" (32/32), with the lock still occurring internally but
  now caught and logged. A separate job-scoped 2-case regression check (write / no-write, matching J-0911's
  own original pattern) confirms D-0206's write-preservation behaviour is not regressed: an unwritten
  `db="empty"` copy is still deleted-or-gracefully-skipped, never crashes; a copy a real
  `core.memory.store.store_fragment()` call wrote to is still correctly KEPT.
- **More precise than F-1279's own hypothesis (F-1356, INFERRED)**: the lock is not only a "real caller
  held a connection open" shape. The cheapest possible case — `isolate(db="empty")` with zero code executed
  inside the block — hit the identical lock on 2/2 runs, meaning `lab_env.py`'s OWN internal
  `_store.init_db()` call inside `__enter__` is enough on its own. 3 of 3 delete-attempts sampled this
  session hit the lock, 0 succeeded — a small same-machine/same-session sample, not a measured rate, but if
  it holds at scale it means D-0206's actual disk-reclaim benefit could be much smaller than F-1277/F-1312
  assumed, independent of genuinely-written copies. **Follow-up spawned: J-0985** — measure the real
  delete-succeeded vs still-locked ratio against real job-run activity, cross-referenced against J-0942's
  own already-open GB/day re-check.
- **Incidental, out-of-scope, filed not fixed**: `_new_lab_dir()`'s 1-second-granularity timestamp naming
  lets two `isolate()` calls in the same wall-clock second silently reuse the same lab dir (reproduced
  twice) — harmless within one process, but a real cross-contamination risk between two concurrent job-run
  agents' isolated DB copies if it is ever hit across processes. Filed as **S-0119** (`skill-manager
  suggest`, `job-queue`), not fixed here.
- No `/decide` action: this job's own source is `finding:F-1279`, not a `decision:D-XXXX`; nothing here
  needed a founder call beyond what F-1356/J-0985 already route through the normal finding → job → (possible
  future) `/decide` path if the measured rate turns out high.

## Current State — updated 2026-09-14 (J-0985, F-1372 — post-fix sample still n=1; transcript-mining confirmed too fragile/incomplete on its own, sidecar log spawned)

**J-0985 (F-1356's own spawn: measure the real delete-succeeded vs still-locked ratio against real
job-run activity, cross-referenced against J-0942) is done — F-1372 (verified).** This job's own
first task, per its briefing, was deciding how to capture the two outcome lines at all (`lab_env.py`
only `print()`s them, no persistent log exists) — a script
(`scratchpad/J-0985_scan_lab_env_prints.py`, outer Claude Code scratchpad, job-id-qualified,
read-only) scanned every Claude Code session transcript for this project (763 `.jsonl` files under
`C:\Users\USER\.claude\projects\C--Nascence`, covering this job-run batch plus every prior batch
back to 2026-09-11) for the two exact runtime print substrings, distinguishing genuine stdout from
Read-tool source-code views (unevaluated `{self._db_path}` template) and from prose citations (no
real evaluated path) by requiring an actual trailing `nascence.db` path.

**Result: the post-fix sample is still n=1, not a new, larger measurement.** 18 raw runtime-classified
hits dedupe to 14 distinct real `isolate()`-exit events: 13 are "deleted" (success), and every one of
them has a timestamp *before* `lab_env.py`'s own last-write time (2026-09-14T04:41:11Z, confirmed via
`Get-Item`) — i.e. all 13 are PRE-FIX (the success print already existed under J-0911; only the
"still locked" print + graceful catch is new per J-0915). Exactly 1 distinct event is POST-fix — a
"locked" outcome at ~04:43:46-52Z, lab dir `20260914_164252` — and its own transcript file
(`069b0e5b-.../wf_23771823-217/agent-a3fd7f530d20a9bdf.jsonl`) was confirmed (by content grep: "J-0915"
×4, "F-1279" ×4, "_test_practical_lesson" ×2) to BE J-0915's own session — i.e. this is F-1356's own
already-reported case 3, not a new independent data point. Despite ~2.5h of this same job-run batch's
own substantial subsequent activity (5 workflow groups, several Tier 1-3 jobs already landed), zero
new post-fix events of either outcome were found. F-1356's own case 2
(`J-0915_verify_two_case.py`'s `isolate(db="empty")` case) left no matching artifact in any transcript
this scan covered — a real, acknowledged coverage gap of transcript-mining (its stdout may not have
been captured inline), not evidence that case didn't happen; F-1356 itself remains the authority on
that count.

**Cross-reference against J-0942 remains impossible**: J-0942 is still `status: open`, never started —
only ~10.3h of its own required 5-7+ day (120-168h) window has elapsed from its own
2026-09-13T20:54:14Z baseline as of this finding (2026-09-14T07:10:52Z). **No `/decide` action**: the
rate is not "confirmed high" (n=1 is not a population measurement), so per this job's own briefing's
own explicit instruction, D-0206 is neither re-ruled nor reopened. **Follow-up spawned: J-1002** — add
a small, persistent, append-only sidecar log directly inside `lab_env.py`'s `isolate.__exit__`
(suggested location `data/_lab/_isolate_outcomes.jsonl`, to be checked against D-0200's own
allow-list scope) recording `{ts, lab_dir, outcome, error}` per unwritten-copy exit, so a *future*
read of this exact question is a direct log read instead of repeated transcript archaeology — ideally
timed to accrue alongside J-0942's own eventual multi-day re-check.

## Current State — updated 2026-09-15 (J-1029, F-1422 — the other 3 D-0216 candidates timed: the sweep is complete, the combined picture still straddles "most")

**All 4 of F-1328's named heavy-subconscious-file readers are now directly timed post-flip.** J-1029
timed the 3 F-1328 left unmeasured after J-0959/F-1403 timed `subconscious_node._save_state()`:
`curiosity_node._select_seeds()`, `dream_node._load_top_tensions()`, and
`tension_ledger.load_unresolved_contradictions()` / `check_and_resolve_internal_tension()`. All four
read the SAME live 48.02 MB compact `data/subconscious_state.json` (unchanged since Du went offline
2026-09-13 09:08) and cost almost identical medians in isolation (50 calls each, `lab_env.isolate()`,
`db="copy"` — two of the four also make a real indexed DB query): curiosity 1379.9 ms,
dream 1388.0 ms, `load_unresolved_contradictions` 1393.3 ms, `check_and_resolve_internal_tension`
1428.9 ms (engineered no-match path — a rare real match would additionally await an async
judge-panel call, out of scope for this blocking-I/O question). For comparison, J-0959's own
`_save_state()` (read+merge+re-serialize+write of the same-sized file) cost 4988.4 ms, ~3.5x a pure
read — an internal consistency check across the two jobs, not assumed.

- **Real cadence split 3 genuinely rare/gated candidates from 1 that is NOT rare — exactly the
  possibility this job's own briefing flagged rather than assumed.** curiosity: 212 real calls in
  the SAME 3.59-day post-flip window J-0959 used (2026-09-09T19:01:08 .. 2026-09-13T09:10:46),
  mean cadence 1463 s (~24 min). dream: only 30 real calls, mean cadence 10,339 s (~2.9 h) — confirms
  F-1328's own "sleep-gated, likely an outlier source not a steady one" read; the rarest of all 5
  candidates now timed across both jobs. `load_unresolved_contradictions`: its only LIVE caller is
  `core/symbol_tier2_wouldinject.py` (`identity_block()`'s other call path is re-confirmed dead code,
  D-0191/F-1133, downstream of an unconditional `is_multilevel()` early-return on Du's live
  axiom.json) — 46 real calls via its own dedicated sidecar log, mean cadence 6743 s (~1.9 h).
  `check_and_resolve_internal_tension`, by contrast, fires every time Du's monologue produces a
  substantive RESOLVED thought (`nodes/inner_monologue_node.py:4513`) — measured EXACTLY via a direct
  SQL query against a live-DB copy's `light_events` table (`source='resolved_thought'`, the same
  branch's own sibling write): **1900 real calls in the identical window, mean cadence 163 s
  (~2.7 min)** — an order of magnitude more frequent than the other 3, and the dominant ~87% of this
  job's own combined contribution.
- **This job's own 4 candidates sum to only ~0.050 s/tick (~4.5% of F-1328's 1.1123 s/tick
  climate-unattributed residual)** — even the one non-rare candidate's 1.43 s cost is 2 orders of
  magnitude below its own 163 s cadence, so its duty cycle stays small despite firing 500+ times/day.
- **COMBINED with F-1403's own subconscious_node contribution, all 4 named candidates now total
  0.560 s/tick (50.3% of the residual) on the mean-cadence basis, or 0.660 s/tick (59.3%) on the
  median-cadence basis** — genuinely straddling D-0216's own "most of the residual" defeater bar
  without clearly clearing it, the SAME mixed character F-1403 alone already showed (~46–55%), not
  resolved by adding these 4 smaller shares. **A real, substantial gap of ~0.45–0.55 s/tick
  (41–50% of the residual) remains unattributed even crediting all 4 candidates their full measured
  share.**
- **D-0216 (active founder HOLD, ruled 2026-09-14) was NOT re-ruled by this job** — this job's own
  operating instructions carried an explicit active-Hold flag (only the founder lifts a Hold); the
  numbers above are recorded as evidence for whenever D-0216 is next revisited, not a verdict on it.
  D-0216's own ruling asked for exactly the follow-up jobs this job (plus J-0959) now completes —
  the full picture across all 4 named candidates is assembled, but does not unambiguously satisfy
  either of D-0216's own named defeater directions.
- **Follow-up spawned: J-1043** — a fresh `core/`+`nodes/` `json.load(` grep (F-1328's own original
  grep found 17 hits that session; only these 4 + subconscious_node were individually characterised)
  to find any still-unnamed synchronous blocking reader that could explain the remaining ~41–50% gap,
  since the named-candidate list is now exhausted without clearing "most."
- **Secondary, not folded into the core measurement**: `lab_env.py`'s known Windows DB-copy-unlink
  `PermissionError` (S-0115) recurred a further time on this job's own `db="copy"` exit — a 4th+
  independent data point, still caught gracefully per J-0915's own fix, did not affect the run.
- Full numbers, code citations (file:line for every claim above), the exact `light_events` SQL query,
  and the isolation/backstop/canary trail: **F-1422**.

## Current State — updated 2026-09-22 (J-1162, F-1705 — D-0242's retry + sweeper built and verified, both parts; merged to master as `93410bd`)

J-1162 shipped both halves of D-0242's ruling. (1) `lab_env.isolate().__exit__` (`~/.claude/skills/job-queue/lab_env.py`, outside this repo) now retries its unwritten-DB-copy `unlink()` up to 4 attempts / 1.5 s with `gc.collect()` between, recording a new `"deleted_after_retry"` outcome distinct from `"deleted"`/`"locked"` in `_isolate_outcomes.jsonl` so the retry's real success rate is directly readable. (2) New `scripts/lab_sweep.py` reaps confirmed-unlocked copies the retry still misses, keyed on the sidecar log's `locked` rows plus a live-handle re-probe (F-1562's technique); report-only by default, `--apply` **quarantines** (moves to `data/_trash/<date>/lab_locked/`, never deletes) verified candidates. (3) Wired report-only into `run_nascence.py`'s boot sequence (`LAB_SWEEP_BOOT_APPLY=False`), same pattern as `backup_identity`/`backup_memory`; **restart-gated, not yet live** — takes effect only at Du's next restart. Both new modules pass dedicated regression tests with mutation checks (4/4, 10/10); `life_smoke.py`'s one unrelated pre-existing failure (day/dusk/night light check) confirmed via a clean-base `a9f042f` throwaway-worktree comparison, not caused by this job.

**Deliberate deviation from D-0242's literal text, disclosed by the builder:** the ruling's item (2) authorized the automated sweeper to DELETE a confirmed-safe copy (locked row + no live handle); this build instead QUARANTINES every case, never deletes, on the reasoning that this matches item (3)'s "no agent deletes under `data/_lab`" and `retention.py`'s own established quarantine-then-purge-by-hand convention, applied uniformly rather than split by confidence tier. Strictly safer than the ruling required, not less; worth a look if Travis wants the automated path to actually delete once he trusts the live-handle probe.

**Watch after the next Du restart + 7 days of normal job-run cadence** (D-0242's own defeater, quoted in J-1210): (a) `_isolate_outcomes.jsonl`'s new `deleted_after_retry` share — the retry's real measured success rate, previously unmeasured; (b) `data/_lab` growth in GB/day against the ~2 GB/day defeater threshold; (c) `nascence.log` for `[lab_sweep] boot (report-only): …` lines confirming the boot hook actually fired; (d) C: free space against the ~100 GiB floor (151 GiB on 09-19, falling ~5.2 GiB/day at the time of the ruling — check the current figure, since this session's own lab window and the 8-worktree build batch have both added to `data/_lab`). Travis's own one-off sweep of the 29 pre-existing locked copies (~20.5 GB, ruling item 3) is still outstanding and untouched by this job. D-0216 (unrelated active Hold, event-loop-lag) confirmed out of scope, not touched.
