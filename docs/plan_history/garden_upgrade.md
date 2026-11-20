# garden_upgrade — folded history


---

# History folded on 2026-09-27 from `docs\plans\garden_upgrade.md` (plan-compact, 10 section(s), verbatim, original order)

_Every J-/F-/D- id below is the canonical record; this file is the prose that once sat in the plan doc. Derived timeline: `plan_ledger.py garden_upgrade`._

## Current State — verified 2026-09-02 (§11, J-0421/F-0553 — live firing CONFIRMED, restart-gated caveat lifted)

The garden hands are confirmed firing continuously in the live loop. `data/garden_ledger.jsonl`
has grown from the 4 rows §10 saw on 2026-08-25 to **31 rows** spanning
**2026-08-22 02:21 → 2026-08-30 13:52 UTC** — first row `mow`, last row
`{"deed": "harvest", "species": "thyme", "plant": "garden_plant_thyme"}`, with F-0553's read
also citing `water`, `take`, and `put` deeds in between. Read directly from the ledger for this
update (J-0421). Deed-type coverage across all seven instrumented hands is J-0243's question,
not settled here. Du has been offline since 2026-08-31 17:47 (clean shutdown), so accrual is
paused, not broken.

---

## Current State — 2026-09-02 (§12, J-0243 — parity-week read attempted; one gate passes, one fails, and a SECOND leak found)

**The parity verdict is still not forced — but now for two precisely-known reasons, one of them a
new bug.** J-0243 ran both of its briefing's gate checks against the full files (F-0606, F-0608,
findings-log):

**Gate 1 (real accrual) PASSES** (F-0606, verified): `data/garden_ledger.jsonl` = 31 rows spanning
2026-08-22 02:21 → 2026-08-30 13:52 UTC (8.48 days); `data/garden_events.jsonl` = 11 rows over
8.67 days. And the new plant-object model is demonstrably the one receiving deeds:
`data/garden.json`'s `last_cut_ts` for rosemary/mint/thyme match the ledger's three harvest rows
**to the second**, and the rack holds all three bundles — the exact signal whose absence proved
the original J-0054 leak. J-0184's fix is confirmed firing on live data.

**Gate 2 (deed-type coverage) FAILS** (F-0608, verified): water 21 · harvest 3 · weed 1 · mow 1 ·
take 4 · put 2 — but **sow, stake, net, save_seed all 0** (4 of the 7 instrumented hands). The
zeros are honest, not leaked: the log shows a sow attempt (08-27) and a save_seed attempt (08-28)
both DISPATCHed through the NEW module and refused for true seasonal reasons (wrong sow month for
sunflowers; nothing at seeding stage in late winter). Coverage should fill in naturally as spring
sow windows open.

**New finding — a SECOND routing leak** (F-0609, verified): `nodes/inner_monologue_node.py`
~2790–2811 holds a legacy (2026-06-20-era) shortcut that routes "water the bed" / plant-word+sow
phrasings to `sensorium.act()` → `_garden_act()` (sensorium.py:1079) — the OLD scalar bed, no
ledger write, invisible to `core/garden.py`. Five real deeds inside the parity window took this
path (2 water, 3 sow — the 08-30/08-31 "he chose to SOW" lines with the pre-upgrade activity
counters). So the two models are *still* not receiving identical deed streams (~14% of window
deeds leaked), the same failure class J-0054 found, via an inlet D-0098's cleanup didn't cover.

**Follow-ups spawned:** **J-0447** (build, urgency 3 — close the monologue shortcut leak, verify
in isolation per the F-0183 pattern) and **J-0449** (analysis, gated — 3rd parity-read attempt,
not before J-0447 lands + ~1 post-fix week of accrual once Du is back online + a coverage
recheck; may score parity per-hand if stake/net/save_seed remain seasonally silent). No parity
comparison was run on the current data — per this job's own briefing, an underpowered/corrupted
read is recorded as findings, not forced into a verdict.

**J-0447 CLOSED 2026-09-02 (F-0620, verified).** The monologue's water/sow latch
(`nodes/inner_monologue_node.py`) now routes through `core.garden.water()`/`sow()` — the same
functions dispatch reaches — instead of the old scalar-bed `sensorium.act()` path; the old path
survives only as an explicit fallback iff `core.garden.ENABLED` is False (never silent, D-0098's
discipline). A `sow` dedup guard was added matching the pre-existing `water` one, closing a
double-fire risk when DISPATCH already sowed on the same thought. Verified in isolation (temp-pathed
`_F`/`_LEDGER`/`_EVENTS`, `activity_memory.record` stubbed so the live sqlite DB was never opened,
live `data/garden_ledger.jsonl`/`data/garden.json` mtimes confirmed unchanged): both `water()` and
`sow()` success paths land a real deed in the new ledger, `sow()`'s honest seasonal-refusal path
still refuses cleanly with no ledger row. Du restarted 2026-09-02 20:48 UTC and this fix was already
on disk before that restart (loaded). **J-0449's gate (~1 post-fix week of accrual) now starts
counting from this restart** — earliest a real 3rd parity read makes sense is ~2026-09-09.

---

## Current State — 2026-09-07 (§13, J-0449 — 3rd parity-read attempt picked up early, gate still not met, F-1090)

**J-0449 was picked up and checked for real against the live files, not assumed from this doc's own
2026-09-02 prediction.** Verdict: **still not met**, on two of its three gate conditions, both for
honest reasons — no new leak.

**Gate (a) J-0447 done — confirmed.** `job_queue.py show J-0447`: `done_at`
2026-09-02T00:15:16Z. The rerouted code (§12's description) is verified present and live in the
current source (`nodes/inner_monologue_node.py` ~3176–3224, `core/garden.py` `ENABLED = True`
hardcoded, nothing anywhere sets it False).

**Gate (b) ~1 week post-fix accrual — FAILS.** `data/garden_ledger.jsonl` read in full (35 lines):
only **3 rows** exist after the 2026-09-02 20:48 UTC restart that loaded the fix — two `water`
(2026-09-03 01:02, 04:59) and one `take`/trowel (2026-09-04 16:55) — spanning **1.66 days**, not
~7. Worse, the ledger has been completely silent for the **2.3+ days since**, even though
`data/nascence.log` shows Du continuously and actively online across that whole span (no
`"Nascence shutting down"` line since 2026-09-05 16:42:49) — this is a real quiet spell in the
garden specifically, not an offline gap.

**Gate (c) deed-type coverage — still FAILS.** Full-ledger tally: mow 1 · weed 2 · water 22 ·
harvest 3 · take 5 · put 2. `sow`, `stake`, `net`, `save_seed` are still 0 of the 7
originally-instrumented hands — unchanged from J-0243/F-0608's 2026-08-30 read. New this session:
the fixed monologue sow latch **did** fire on real post-restart sow attempts (thyme,
2026-09-07 02:02:32; three more on 2026-09-02 before the 20:48 restart) and each was a verified
**honest refusal, not a leak** — checked against both `core/garden.py`'s own `sow()` refusal order
and the live world state: the seed tin's last recorded position is `wood`, not the garden
(`carried: false`), which refuses before the month/temperature gates are even reached; live
`soil_temp` is 5.58°C against thyme's ~13°C germination floor, so a temperature refusal would
follow regardless; and rosemary's catalogue entry is permanently `"sow": ()` — never sowable in
this model, by design (perennial/cutting-only), independent of month or temperature. Zero `stake`
or `net` attempts of any kind appear anywhere in the log; the one known `save_seed` refusal
(2026-08-28) is unchanged.

**No parity comparison was attempted** — correctly: gate (b) fails outright, and even the hands
with real data (water/harvest) are >90% pre-fix rows, the same invalid-comparison failure mode
§7 (J-0054) already documented. Finding recorded: **F-1090** (verified). **J-0449 left
`in_progress`, not closed** — the next pickup should re-check `data/garden_ledger.jsonl` growth
past 2026-09-04 16:55 first; if the garden stays this quiet, ~1 week of real post-fix accrual will
take longer than this doc's 2026-09-09 estimate assumed.

---

## Current State — 2026-09-21 (§14, J-0449 — 3rd parity-read RUN, scoped per-hand; F-1625..F-1629, D-0243)

**The read was run, and its result is a scoped "no regression found", not a full 7-hand parity pass.** Everything below
was re-derived from the raw files today (full reads of `data/garden_ledger.jsonl`, `garden_events.jsonl`, `garden.json`,
`room_state.json`, and one pass over all 487,973 lines of `data/nascence.log`).

**Gates.** (a) J-0447 is on master (a433abc, 2026-09-02 13:03 NZT); the first run that loaded it began 15:44:16 NZT.
(b) It was a **cumulative live-time** gate and it has cleared: 303.7 live-hours = 12.66 live-days over 22 runs (18.9
wall-clock days; longest run 61.1 h; the 7-live-day mark passed about 2026-09-10 13:13). What did not accrue is deeds:
5 post-fix ledger rows (weed 1, water 3, take 1). (c) Coverage of the seven hands after the fix, attempts / deeds: water
20/3, weed 4/1, harvest 39/0, sow 3/0, stake 0/0, net 0/0, save_seed 0/0 (F-1625). The briefing's premise that
sow/stake/net/save_seed would fill in "naturally as spring opens" does not hold: sow is blocked because the seed tin has
sat in the wood since 2026-08-29 (radish and peas would pass the month and soil gates today); harvest by real regrow
cooldowns on the two herbs Du keeps asking for (thyme to 2026-09-30, rosemary to 2026-10-04) while mint, parsley and
chives are ready (F-1628, plus a latent `harvest()` pool[0] defect, **J-1169**); stake and net have simply never been
willed; save_seed cannot happen before November.

**Leak closed (F-1626).** Zero old-path renders after the fix; all 5 ledger rows reconcile to log lines and to
`garden.json` state to under 0.1 s. Two corrections to §12/§13: the pre-fix leak was about ten times larger than
F-0609's "14%" (52 old-path water renders against 20 ledger water rows, 08-22..09-01) — it was D-0098's 2026-08-30
retirement of `garden_act()` that ended it, and J-0447 closed the last latch; and §12 / F-1090's "restart 2026-09-02
20:48 UTC" was 08:48 NZT = 2026-09-01 20:48 UTC, *before* J-0447 existed, so the true post-fix count is 5 rows, not 3.
Consequence: the old scalar bed now receives **no deed at all** and runs on wall-clock while the new model runs on
live-time (20.06 age-days against 30.09 wall-clock days since the garden's birth), so a same-deed-stream parity week
cannot be recreated by waiting.

**Scoped parity verdict (F-1627, inferred).** Four original herbs exist in both models: the old bed reads "filling out
(the soil round it is dry)" for all four (growth 0.48-0.59, bounded to "filling out" for the whole window); the new model
reads rosemary "in flower", thyme / mint / parsley "full and well-grown"; neither model changed a word in the window. New
is at least as advanced on every plant with a strict-superset vocabulary; water passes (3 deeds, each answered "pools on
the surface"); weed has no old counterpart; harvest, sow, stake, net and save_seed are **not scoreable**. One
soil-wetness disagreement (old 0.147 "dry", new 0.986 "sodden"), cause not investigated.

**Also found (F-1629, inferred; measurement job J-1170):** all 28 crop seedlings of the 2026-09-02 volunteer burst were
dead by 09-08 amid 248 bird events and the netting has never been used; `_soil_temp_c()` relaxes 8% *per tick* (a
time constant of about a minute, not "hours"). Bears on §3 metric 2 (loop closures).

**Decision needed: D-0243** (open; recommendation A) — accept this scoped read as the P0 parity gate and start the §3
metric-sheet clock (about 12.9 of 14 live-days in spring, due about 2026-09-23), or hold the gate until each of the five
unscored hands has a real post-fix deed. **J-0449 closed**; nothing further is waiting on uptime.

---

## Current State — 2026-09-23 (§15, J-1169 — harvest() pool[0]-pinning fix, built and verified in isolation, F-1753)

**F-1628's bug is fixed.** `core/garden.py` `harvest()`'s unnamed-ask branch (`pool = named or [...]`) no longer takes
`pool[0]` unconditionally: it now walks the pool in dict order (rosemary, thyme, mint, parsley, chives) and cuts the
first candidate that is neither in regrow cooldown nor still at stage "leaf", falling back to `pool[0]` (and the
existing, unmodified refusal text naming it) only when every candidate is cooling or too thin. A **named** ask
(`"cut the rosemary"`) is byte-for-byte unchanged — still `p = pool[0]` of the named list, still refuses if that
plant is cooling — matching this doc's §1 law 4 (a named ask's refusal is by design). No refusal/success text,
`_cross`, the ledger row shape, the rack bundle, `garden_soil.crop_drain`, or the smell brush were touched.

**Verified in isolation** (F-1753, findings-log; `scratchpad/J-1169_test_harvest_pool.py`, `lab_env.isolate()` —
extended past the briefing's own `also=` list to include `core.world_substrate`'s three path constants, since
`harvest()`'s `_set_stage()` call syncs into world_substrate on every real cut and a fresh `world_substrate._load()`
in a worktree with no `data/` dir yet unconditionally calls its own `_save()`, which would otherwise raise
`NonLiveWriteError` uncaught out of `harvest()`): all 5 briefing cases pass — an unnamed ask with rosemary+thyme
(pool[0],[1]) cooling cuts mint (the first ready candidate) with one ledger row and `last_cut_ts` updated; a named
ask for a cooling plant still refuses with zero rows; every-candidate-cooling still refuses naming rosemary
(pool[0]) with zero rows; a named ask for a ready herb still cuts it; live `data/garden_ledger.jsonl` and
`data/garden.json` mtimes read via `os.stat` before/after the whole block — unchanged. **Negative control:** the
identical Case-1 scenario run against pre-fix HEAD in a throwaway `git worktree add HEAD` (removed immediately
after, shared tree never touched) reproduced F-1628 exactly — `"You look at the rosemary bush — it is still
filling out from the last cut; better to let it come back."`, mint never tried — confirming the fix, not the
test harness, is what changed the behaviour.

**Restart-gated, not yet live.** Du was online throughout this job and was not restarted (per this project's
standing rule); the fix is on disk in this worktree only until it merges and Du's process next restarts. Follow-up
spawned: **J-1251** (analysis, not before a post-fix restart + some real accrual) — re-check
`data/garden_ledger.jsonl` for a live mint/parsley/chives harvest row as the first real-world signal the fix
reaches Du's actual unnamed asks, the same "isolated-verified now, live-checked after accrual" pattern this
plan's own §7–§14 history already established for J-0184/J-0447's routing-leak fixes. No founder decision was
needed for this job; D-0243 above is untouched (out of this job's own scope).

---

## Current State — 2026-09-23 (§16, J-1170 — soil_temp/bird-survival MEASUREMENT, not a fix; F-1763, F-1764, D-0261)

**Read-only + isolated measurement, per the briefing — no constant in `core/garden.py` was changed.** Full
isolated script kept at `scratchpad/J-1170_measure_soil_and_birds.py` (this job's own scratchpad, not the
shared tree). Two findings recorded, split by confidence:

**F-1763 (verified) — soil_temp physics, and where "neglect" really comes from.** `_soil_temp_c()`'s own
recurrence (`soil + (air-soil)*0.08` per tick) is an exact geometric decay — measured 28 ticks to 90%
convergence on a step change (matches the closed-form `0.92^n<=0.10` exactly), and the real background tick
cadence is confirmed ~5s (`core/orchestrator.py`'s `_substrate_loop()`: `asyncio.sleep(5.0)` then
`sensorium.tick()`, which self-floors to `>=5s`, `sensorium.py:3318`) — so 90% convergence takes **2.33
minutes**, e-folding time constant **60.0 seconds**, not the docstring's claimed "hours" (off by ~2 orders of
magnitude). On a clear September/October day the sow()/germination gates sit open most of the daylight hours
for low-`t_germ` species (radish/peas/lettuce, 12-14 of 24h) but thyme's own 15°C germination gate is **never**
reached even on the best-case clear day in this model (its sow-gate at 13°C does open, ~11-12h). Separately —
answering the briefing's "check where cause neglect is assigned" with certainty — `_advance_plant()`'s
death-cause classifier (~line 724-737) has no branch for bird predation, and bird bites only ever touch
`vigour` directly, never `pests`/`disease`/`rot`/`frost_burn` — so a bird-driven death always falls to the
catch-all `"neglect"`. Confirmed against live `data/garden.json`: of the 28 real non-weed crop volunteers of
the 2026-09-02 burst (all currently `dead`, `vigour=0.0`), **exactly 19 read `cause="neglect"`** — matching
the briefing's own count precisely — despite every one of the 28 having real `eaten_by_birds` history rows
(7-22 bites each for the 19); the other 9 have no `cause` key at all (a narrower, unexplained detail, flagged
not chased further). Live thyme_50d1 (the briefing's own anchor) is confirmed still alive, now vigour 0.257
(up from 0.21 at the briefing's own read), 21 bites — because thyme is evergreen/non-tender and gets THE KEEL
floor (D-0139, `vigour>=0.2` every tick) that none of the 9 vulnerable annual/biennial crop species get.

**F-1764 (inferred) — can the loop close? Monte Carlo says only with netting.** Two isolated Monte Carlo runs
(seed=1170, real `core.garden.advance()` code, 540 synthetic un-netted vs netted shoot-stage plants across the
9 vulnerable species, 14 simulated days) with moisture pinned to isolate birds as the one variable: **un-netted,
1/540 (0.2%) ever reached leaf stage** (chronic bird pressure — measured 2.65 bites/shoot-day, independently
cross-checked against the closed-form `0.25×day-hours` — holds median vigour at 0.021, too suppressed to ever
clear the stage-3 threshold, even though none technically died outright under these favourable, well-watered
conditions); **netted, 480/540 (88.9%) reached leaf**. A separate uncontrolled run (constant dry "clear"
weather, no watering) killed 540/540 in BOTH conditions via drought alone, median 6.35 days — strikingly close
to the real anchor (28/28 real volunteers dead by 09-08, ~6.15 days after the 09-02 burst) — suggesting the
real week's deaths were likely birds **plus** real weather stress (the cited 09-08 05:36 frost dawn), not birds
alone. **Recommendation (not applied): §3 metric 2 (≥1 full loop by end of spring) is achievable under current
constants only if the netting is actually used** — it never has been (0 `net` deeds ever; the item has sat at
its 2026-08-22 spawn position the whole time).

**D-0261 opened (not ruled): does bird seedling-predation fall under D-0140's existing pest ruling, or need its
own?** D-0140's own text is about the `pests` (aphid/caterpillar/slug) mechanic specifically, naming birds as
one of ITS correctives — not as seedling predators in their own right; the `eaten_by_birds` mechanic never
touches `pests` at all. Recommendation given (not a ruling): treat as a separate question. **Two follow-ups
spawned:** **J-1259** (build, ready — give bird-driven deaths their own `cause`, e.g. `"birds"`, instead of
`"neglect"`; a bookkeeping/honesty fix, not a balance change, does not wait on D-0261) and **J-1260** (build,
needs_input — apply whatever D-0261 actually rules on bite harshness/netting-discoverability; explicitly gated,
must not start before D-0261 is ruled).

---

## Current State — 2026-09-23 (§17, J-1251 — harvest() fix re-check attempted, precondition unmet, F-1766)

**Left open, correctly — Du has not restarted since J-1169's fix landed.** J-1251's own briefing gates the
mint/parsley/chives live-coverage check behind Du having restarted after J-1169's `harvest()` pool-pinning fix
(§15, done_at 2026-09-23T03:35:20 UTC). Checked directly against `data/nascence.log` rather than assumed: the
most recent `"Nascence shutting down"` line in the whole file (507,157 lines) is at 2026-09-22 08:43:39 local,
followed by the boot sequence that is still the CURRENTLY-live process (`"Nascence is awake"` at 2026-09-22
16:11:06 local = 2026-09-22 04:11:06 UTC, confirmed against this session's own local-vs-UTC offset, NZST =
UTC+12). That restart precedes J-1169's fix landing by about 23h25m — the live process was started roughly a
day BEFORE the fix existed and has not restarted since, so it is still running the pre-fix `harvest()`. The
ledger was deliberately not read for this cycle: any mint/parsley/chives (or lack thereof) since 2026-09-22
16:11 would reflect pre-fix behaviour and cannot answer what this job asks. **J-1251 stays open** for a session
picked up after Du's next restart (verify the same way: `job_queue.py show J-1169`'s `done_at` against the
latest `"Nascence shutting down"`/boot pair in `data/nascence.log`) — this is the normal, expected outcome of
an unmet time-gate, not a failure. Finding: **F-1766** (verified).

---

## Current State — 2026-09-23 (§18, J-1259 — bird death-cause classifier fix, built + verified in isolation, F-1777, D-0264)

**F-1763's bug is fixed.** `core/garden.py`'s `_advance_plant()` death-cause classifier gained one new branch —
`elif any(h.get("event") == "eaten_by_birds" for h in p.get("history", [])): cause = "birds"` — slotted between
the existing frost check and the final `else: cause = "neglect"` fallback, so a bird-driven death (vigour lost
solely to the `eaten_by_birds` mechanic, `advance()` ~line 476) is no longer misattributed to the self-blaming
"neglect" label; the full priority order (disease > rot > age > pests > frost > birds > neglect) is unchanged
and still takes precedence over birds when a stronger stressor is also present. A matching
`_DEATH_LINES["birds"] = "pecked to bare stubs, the stems broken"` entry was added (distinct wording from both
`"neglect"`'s "dried to a crisp" and `"pests"`'s "stripped and sucked"). No new plant-state field was added —
the branch reuses the `eaten_by_birds` rows the existing bird-bite mechanic already appends to `p["history"]`.
Pure bookkeeping/attribution; `advance()`'s bird-bite frequency, vigour drain and netting check are untouched,
per the briefing's explicit scope. UDMS `udms_get_change_dossier` was run on `core/garden.py:420-900` before
editing (risk tier ELEVATED, `_advance_plant` flagged a StructuralHub); cross-checked by grep that no other
module keys on the literal `"neglect"` string or this classifier's output set except `scripts/life_smoke.py`'s
own heavy-pest-infestation check, which sits ahead of (and is unaffected by) the new birds branch.

**Verified in isolation** (F-1777, findings-log; `scratchpad/J-1259_test_bird_cause.py`, the same extended
`lab_env.isolate()` pattern as J-1169/J-1170's own scripts): a birds-only death gets `cause="birds"` and the
new death line; birds-plus-disease(>0.5) still gets `cause="disease"`; a death with no bird history at all
still gets `cause="neglect"` (no over-firing); birds-plus-pests(>0.5) still gets `cause="pests"` — priority
order holds on both branches ahead of birds, not just disease. Live `garden.json`/`garden_ledger.jsonl`/
`garden_events.jsonl` mtimes confirmed unchanged across the whole isolated run. **Forward-only, confirmed two
ways:** structurally (`_advance_plant()` returns immediately for an already-dead plant, so the classifier
cannot re-run on one) and by a direct read-only load of the live `data/garden.json`, which still shows exactly
the same 19 `cause="neglect"` dead volunteers with real `eaten_by_birds` history that F-1763 found — untouched
by this fix landing on disk.

**D-0264 opened (not ruled):** now that the truth is structurally recoverable from each plant's own history,
should those 19 existing records be backfilled from `"neglect"` to `"birds"`, or left exactly as originally
written? Recommendation given (not a ruling): lean against backfilling by default (this plan's own §1 law 6,
additive/nothing-already-known silently rewritten, plus a live-data hand-edit is off-limits to a session
regardless), but genuinely a founder call, not decided here. **Follow-up spawned:** **J-1269** (backfill,
needs_input, explicitly gated — must not start before D-0264 is ruled, and only proceeds if the ruling actually
calls for a backfill; also flags a second, separate sub-question — whether the matching historical
`plant_died` rows in `data/garden_events.jsonl` should be corrected too, or left as an honest record of what
was written at the time).

---

## Current State — 2026-09-25 (§19, J-1350 — netting-discoverability earned-info affordance, built + isolated-verified, F-1911, D-0278)

**D-0278 ruled** (travis, 2026-09-25, on F-1764's own predecessor evidence — §16): make netting discoverable;
the bird-bite mechanic itself is working as designed and stays untouched. Built accordingly, in
`jobrun/garden_upgrade` — **restart-gated, not yet live.**

**What was built, all additive, zero mention of "net"/"netting" as a suggestion anywhere in the new text**
(per this plan's own §1 law 3 and the job's own briefing — the world answers, it never leads; the netting
item's own existing bio, "to keep the birds off seedlings, if untangled", is left to do the rest):
- `core/garden.py` `_bird_bitten(p)` — true iff THIS plant's own history really carries an `eaten_by_birds`
  row; never a forecast. `_bed_vulnerable(cat)` — the same real distinction THE KEEL (D-0139) already draws
  (not a weed, not evergreen/herbaceous), expressed structurally against `CATALOGUE` rather than as a
  hardcoded species list, so it keeps tracking the catalogue as species are added.
- `_stage_phrase()`'s shoot branch — a really-bitten shoot now shows `", one seed-leaf pecked through"`.
  Added to **both** the grandfathered/known-name branch and the unnamed/unknown-look early-return branch
  (the isolated test caught, before the fix, that the second branch — which is where MOST of F-1764's own
  9 vulnerable species actually render, since only lettuce/parsley/sunflowers of the nine are grandfathered
  — would otherwise never have shown it at all).
- `bed_summary()` — un-netted + a real vulnerable shoot up + daylight (the same phase gate `advance()`'s own
  bite check uses) now adds one truth-gated line: `"Nothing is strung over the bed; the seedlings stand open
  to the sky."`, upgrading to `"...and a blackbird has already been at the seedlings — a bite out of more
  than one."` once a real bite has actually landed on one of them. Mutually exclusive with the existing
  "the netting is stretched over the bed" line.
- `core/garden_knowledge.py` `evidence_for()` — a **real pre-existing bug** found while reading the code this
  job's briefing pointed at: `eaten_by_birds` was lumped into the same bucket as `slug_damage`/
  `eaten_by_slugs` and produced the FALSE slug story ("wet nights... silver trails") for a plant that was
  only ever bird-bitten. Split out; a bird-only plant now gets true, distinct evidence ("bitten clean out of
  it, not holed the way a slug leaves them — you have seen a bird about the bed"). Live `data/garden.json`
  (F-1763) already shows 19 dead volunteers with real `eaten_by_birds` history and no slug event — every one
  of those, investigated before this fix, would have returned this false story.
- `core/garden_knowledge.py` `revise()` — gained a `"birds"` preceding-tag (`garden.py`'s `advance()` now
  calls `_gk.revise(p["species"], "bird_bite", "birds")` on a real bite, matching the existing frost/slug
  call sites) so a binding he authors about birds can firm or weaken by what recurs, the same as every other
  cause already can (law 5) — this was the one real event type the CAUSE-side binding mechanism never
  touched.

**Verified in isolation** (F-1911, findings-log; `scratchpad/J-1350_verify_netting_discoverability.py`, run
against this worktree's own code only, every write redirected outside any `data/` tree since this worktree
has none at all): **39/39 checks passed**, including every false-positive check the briefing asked for
(netted → no exposure line; night → no exposure line; an un-netted but non-vulnerable evergreen shoot alone →
no exposure line; a weed alone → no exposure line; grown past shoot stage → neither line) and a short live
run of the real, unmodified `advance()` mechanic on a 40-plant cohort watching the render flip from nothing
to real evidence as an actual bite landed. `python scripts/life_smoke.py` (the project's own pre-existing
regression suite) — **ALL OK**, unaffected. Full evidence: F-1911.

**Not done here, deliberately:** the netting item itself was not moved, announced, or referenced in any new
text (per the ruling and the briefing); no new `world_traces` bird-peck trace object was added (the
per-plant history text plus the bed-level line already deliver real discoverability without touching a
second subsystem, kept for a later job if evidence says it's still not enough). **Follow-up spawned:
J-1354** (analysis, gated — checks D-0278's own defeater for real: after this lands on master and Du has
genuinely restarted and accrued real time, whether `net`/`unnet` ever appears in `data/garden_ledger.jsonl`
for the first time ever, and whether the new percept text actually reaches him in `data/nascence.log`; left
open with the gate re-stated if picked up too early, per this plan's own §9/§13/§17 precedent).

---

## Current State — 2026-09-26 (§20, J-1354 — netting-discoverability re-check, restart gate MET, accrual gate not yet, F-1946)

**Restart gate MET, accrual gate not yet — outcome (3) of this job's own briefing, exactly the outcome §19
flagged as plausible on first pickup.** Checked directly, not assumed: fix commit `75eedd3` is on `master`
(landed 2026-09-25 09:59:42+12); the most recent boot in `data/nascence.log` (`"Nascence is awake"`, line
525182) is 2026-09-25 19:21:51 local, after the merge, and the process has run continuously since (no
`"shutting down"` line after it) through the log's last line, 2026-09-26 19:31:06 — about **24h9m** of real
accrual against this plan's own established **~1 week** cadence for a behavioral read (§13/§17, J-0449/
J-1251).

**No behavioral signal yet, and it's fully explained by world state, not a broken affordance or avoidance.**
`data/garden_ledger.jsonl` read in full (40 lines, the garden's entire history): zero `net`/`unnet` deeds
ever (F-1764 still holds), and in fact zero deeds of *any* kind since the restart — the ledger hasn't had a
chance to speak either way yet. The four literal percept strings §19 added do not appear once in the whole
post-restart window of `data/nascence.log`, but that's because live `data/garden.json` shows `netted: false`
(that half of the gate holds) while none of the 22 in-bed plants are at `shoot` stage (2 flowering, 4
established, 1 leaf, 15 dead) and zero plants anywhere are at `seed` stage either — there is currently no
vulnerable shoot-stage planting for `_bed_vulnerable()`/`_bird_bitten()` to apply to at all, so
`bed_summary()`'s new line cannot have fired regardless of visits. He *has* visited the garden repeatedly in
this window (227 garden-related log lines, activity counter 1844→1885) — a real "nothing to surface yet"
state, not disengagement.

**D-0278's own defeater is not live.** Both its conditions require the affordance to have actually surfaced
something first ("still never gets used *despite being genuinely surfaced*"; "a real season's data *with
netting in use*") — neither premise holds yet, so neither defeater clause can be evaluated. D-0278 stays
ruled as-is; no fresh `/decide` opened.

**J-1354 stays open** (deferred, not-before 2026-10-02 — one week from the fix-including restart), per this
plan's own §9/§13/§17 precedent for an unmet time-gate. Re-checking sooner would only be useful once a real
vulnerable shoot-stage planting also exists un-netted in the bed — nothing is currently sown toward that at
all, so the calendar defer alone is necessary but may not be sufficient; this should be read naturally at
the next pickup, never engineered (a sowing forced to manufacture a test case would violate this plan's own
§1 law 3, "the world answers, it never leads"). Full evidence: **F-1946** (verified).


---

# History folded on 2026-10-04 from `docs\plans\garden_upgrade.md` (plan-compact, 19 section(s), verbatim, original order)

_Every J-/F-/D- id below is the canonical record; this file is the prose that once sat in the plan doc. Derived timeline: `plan_ledger.py garden_upgrade`._

- **2026-10-04** (F-2402): J-1764 built the D-0333 narrow fix: the seed tin words (seed tin, dented tin, the tin, this tin, that tin, my tin, packet, packets) join the look row via grammar_only plus one whole-word tin cue placed last in the cue table (commit f2fdcdc, restart-gated, not live until merged and Du restarts): a willed look at the tin now fires and names it where it lies and answers like the structured observe route elsewhere, while the match tin, tinder, tinkling, stinging and tin roof are unchanged; the cue order was left alone, so only 3 of 19 real tin-naming look deeds reach the tin cue (4 of the 6 new ones go to thyme, shingle, the flag, the book) and D-0348 asks Travis about a tin-first rule

- **2026-10-03** (F-2390): J-1749 built the net hand agent guard and verb-bound direction in the garden module (commit 31ad4e5, restart-gated, not live until merged and Du restarts): descriptive prose no longer nets or un-nets the bed and lift and take-the-netting wills point the right way; corpus replay 1 net-family DEED read reaching the hand became 0 with 0 genuine wills lost; the net table row is unchanged (untangle and secure stay D-0344)
- **2026-10-03** (F-2386): J-1722 landed the observe-only bed-exposure log in commit 7757f68 (restart-gated): when Du is actually shown the D-0278 tail sentence or one seed-leaf pecked through, ONE INFO line with the full text goes to nascence.log tagged look-bed, look-frame or look-plant, and his text is unchanged. The live scene line comes from the spatial renderer and never carries the bed summary, so these words are look-gated, not ambient: zero lines while a vulnerable shoot stood means not shown, not surfaced but unused

- **2026-10-03** (F-2378): J-1721 net family analysis (F-2378): the 09-28 false net is one case of a wider class, since any non-agent subject with stretch or lift or cover and the bed nets it for real on master code; Du has had only 2 genuine netting wills in 8 weeks (both 09-02, in words the table lacks: untangle and secure); the direction logic also misreads lift, take the netting and the bare word off; the fix is a hand-level agent guard plus verb-bound direction (build J-1749, no decision needed) while adding untangle and secure is D-0344 (J-1748 waits on it); the shared root cause is that literal_will makes a gated DEED from verb-reaches-object alone (analysis J-1747)
- **2026-10-03** (F-2348): J-1680 landed the net hand world-truth guard in commit 64edc3c (restart-gated): un-net on a bare bed and net on an already netted bed now answer honestly with no ledger row and nothing moved, and the direction is read from whole-word clause-local evidence, so the false 09-28 unnet deed of F-2252 cannot recur; the family gate and Du's missing netting vocabulary were left alone and filed as J-1721, the observe-only bed-summary log as J-1722

- **2026-10-03** (F-2330): J-1251 read: the harvest unnamed-ask fix has been live since the 09-25 boot (121 live hours, 17 harvest attempts all naming thyme or rosemary, zero deeds on mint, parsley or chives); no unnamed ask has reached the hand yet, so unobserved and not refuted; successor J-1708 dated 10-21 needs about 290 more live hours or one unnamed ask
- **2026-10-03** (F-2325): J-1572 closing check of the wood seed-tin fix (J-1438, 83923bd) after Du's clean shutdown at 08:15:27 on 10-03: F-2285 reproduces exactly on the final data (wood 5 of 1682 cycles since the 09-28 boot vs 14.2 pct before; tin still in the wood; ledger unchanged at 43 rows; no commit touching the look row or cue table since F-2284), and the 10-03 incarnation was awake under 2 minutes before sleeping so it added no wood exposure (61.5 h wall-clock live since the 09-28 boot). J-1572 closed as superseded by F-2285; J-1691 stays the one dated successor (not before 2026-10-10 and only once Du has really run about 4 live days, roughly 95 h still needed, counted in located cycles); D-0333 still open.

- **2026-10-03** (F-2285): J-1540 takeover read of the wood seed-tin fix (J-1438, 83923bd): gate met (merged 09-28, five Du boots since, about 61 live hours) but Du has almost never been in the wood since the 09-28 restart (5 of 1682 cycles vs 14 pct before), with no tin-directed look, take or sow and the tin still lying in the wood, so the check is underpowered (one tin-directed act per 3079 wood cycles before the merge). F-2284 (verified): a willed look cannot reach the tin because the look row and cue table have no tin words, only the structured observe act can; take works. D-0333 asks Travis how far to go; J-1691 re-reads not before 2026-10-10; J-1572 is superseded by this read.
- **2026-10-03** (F-2252): J-1354: netting re-check -- restart gate met (J-1350 on master, six Du boots since, about 5.0 days live accrual) but the read is event-gated: no vulnerable shoot has stood in the bed since 2026-09-04 (the 8 seeds left in the bank can never germinate, the seed tin is still in the wood, zero sow deeds ever), so the new text has never had a chance to fire and the D-0278 defeater is untestable; the ledger only unnet deed (2026-09-28) is a false positive, not netting use; build J-1680 fixes net(), re-check J-1679 not before 2026-10-10.

- **2026-10-02** (F-2239): J-1657 (F-2239): guessed_cause() scoped from whole-thought substring to clause-level (same/adjacent clause as an investigate-trigger word); isolated pre/post replay (worktree pinned at pre-fix HEAD 31769e1 vs the fix) confirms the F-2229 cross-topic false positive (rosemary bound to an unrelated mood sentence) is gone, 3 genuine cause-guess cases and all 14 historical look() targets are byte-identical pre/post; committed jobrun/garden_upgrade 33f3b3a, stacked on 0da92eb, neither merged/live yet.
- **2026-10-02** (F-2229): J-1639 (F-2229): raw thought+intention now threaded dispatch to sensorium to garden.look so investigate/cause language reaches bind(); verified in isolation, zero regressions on 14 real historical targets, 5 new bindings on real phrasings; committed jobrun/garden_upgrade 0da92eb, not yet merged/live; J-1657 spawned (guessed_cause precision follow-up).

- **2026-10-02** (F-2217): Round-2 post-restart recheck (F-2217, verified): restart precondition now met (4 real boots after the merge), but bindings still 0 -- explained by J-1639's still-open dispatch-layer gap, not restart timing; J-1601 fix confirmed live and observably firing on real per-plant deeds.
- **2026-09-28** (F-2205): J-1601 fixed _OBS_TARGETS collapsing every herb cue to bed (F-2205, verified): garden.py look()'s per-plant branch is now reachable for all 29 cataloged species, not just unreachable via bed. F-2206 (verified, isolated proof) found a deeper gap: dispatch only ever forwards a bare resolved keyword, so investigate/cause language never reaches guessed_cause()/bind(), so S3 metric 3 will still read 0 even after this fix and after restart.

- **2026-09-28** (F-2190): F-2190: Du still not restarted, same PID 25204; bindings still 0 as expected. J-1601 (not J-1567) also still open, so next recheck should expect same explanation until it lands. J-1627 spawned for the real post-restart recheck.
- **2026-09-28** (F-2169): J-1572 recheck of J-1438 wood-tin fix 83923bd: Du live process PID 25204, started 2026-09-25 19:20:56, still not restarted past the commit; reproduces F-2138 about 5.5 hours later with the same PID; left in_progress pending the next restart-gated check.

- **2026-09-28** (F-2161): J-1566: ab62f2c (J-1524 bind wiring) merged to master 09-28 10:21 but Du not restarted since -- bindings still 0 as expected (F-2161, verified). Also found the willed look hand may never reach the per-plant investigate branch at all, restart or not, since _OBS_TARGETS collapses every herb cue to bed (F-2162, inferred).
- **2026-09-28** (F-2101): J-1438/F-2101: the seed tin was genuinely undiscoverable in the wood by any realistic look (wood_life.look() has no vocabulary for it; the generic tracked-object fallback needs the exact phrase seed tin, not Du's own real word for it, the dented tin). Also corrected the move date to 2026-08-29, not 08-25. Fixed additively (garden.item_look() reused as a wood-look fallback), verified 11 of 11 isolated checks, committed to the jobrun/garden_upgrade worktree only -- not yet live. Idea I-0084 opened on the broader pattern (no place's generic look names any lying item at all).

- **2026-09-28** (F-2092): J-1441 (living_world_upgrade, F-2092): of declined moves from the garden, 26 wanted the shore and 16 the wood, both explicit same-clause requests, explained by the already-ruled D-0224 journey-redirect protection, not a garden-specific bug. Within-place misses at the garden include raised bed (8 requests) and gate (12 requests), real move targets the hand does not resolve; see decide question D-0319.
- **2026-09-28** (F-2082): J-1437 read S3 metric sheet in full against live data. 2/6 met (contamination, cost), 1/6 met with caveat (watching - real only at a 1h window, p about 0.04 vs a 300-trial null; 6h+ is chance-level ceiling), 3/6 not met (deed-with-consequence about 15-35pct vs the 0.5 target; loop closures 0 of 1, seed tin still place=wood in live garden.json, moved there 2026-08-29 per the ledger itself not 08-25 as this doc says; phenology bindings 0 - garden_knowledge.bind() has zero call sites anywhere in the repo and zero entries in its own live store despite existing since 08-22). No row hits the kill wording; D-0243 defeater not triggered, stands as ruled. J-1524 spawned to wire bind() to a real caller.
