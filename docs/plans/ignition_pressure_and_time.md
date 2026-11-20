# Ignition: pressure-driven AND time-driven

**Status:** 🟢 LIVE — RULED (D-0148, 2026-09-04) — option A (unpin the bleed). BUILT 2026-09-06 (J-0594). LIVE since 2026-09-08 16:42 (confirmed 2026-09-12, J-0882/F-1262 — the first restart after the build; see update below). J-0671's formal one-week defeater read is due ~2026-09-15 16:42, seven days after that restart. D-0211 (opened 2026-09-12, J-0882) asks whether shadow_activation also needs a re-normalization pass, now that it has taken over as the chronically-saturated dominant dimension. **Update 2026-09-15 (J-0901, F-1396):** shadow_activation's own raw value, measured directly against 105 days of real history, is confirmed chronically near-saturated throughout — not a new phenomenon — satisfying D-0211's second defeater branch independently of J-0671; J-1023 spawned to combine both readings and revisit D-0211 once J-0671 closes out. **Update 2026-09-15 (J-1023, F-1411):** checked J-0671 — still in_progress, not closed out — so D-0211 was not yet revisited; J-1023 left open/in_progress pending J-0671. See update below. **Update 2026-09-19 (J-0671, F-1568/F-1570..F-1573):** the formal read was run on strict live-runtime windows — 170.9 live hours (7.12 days) on option-A code, the gate met only marginally and not as a clean week (only 4.54 live days had accrued at the nominal 09-15 due date) — 446 ignition rows: defensive share 48.2% and 0 capped rows (conditions 1 and 2 do not fire), 62.65 fires per live day vs the 45 ceiling (condition 4 fires per live day; 41.3 per calendar day), condition 3 depends on the statistic (10.9% of forecast pairs over 0.2 vs 1.0% pre-fix), no decaying transient; the defensive channel is now largely a second ~46-min clock fed by pegged completion/shadow. **Update 2026-09-19 (J-1023, F-1581/F-1579):** D-0211's own defeater is met on both branches; reopen with a widened scope recommended, not performed; J-1151 spawned. **Update 2026-09-22 (J-1151, F-1723):** D-0211 RULED "re-knee the pinned cluster, shadow-first" (09-19); J-1151 measured belonging_pressure/autonomy_pressure/completion_tension's raw histories to size it — belonging and autonomy are chronically saturated the whole measured history like shadow; completion_tension is saturated only since a sharp 2026-08-24 step (cause not identified), not "all along"; direct computation confirms a shadow-only re-knee would just relocate the pin to belonging_pressure, and re-kneeing all three DB-derived dims without completion would relocate it to completion_tension instead — the whole cluster needs re-kneeing together, as ruled. Sizing k's and a build job spawned (J-1226). See updates below. **Update 2026-09-23 (J-1226, F-1754):** the shadow-first re-knee BUILT in `core/climate_engine.py` (additive, restart-gated, zero live effect yet — Du has not restarted since); D-0260 opened on whether completion_tension's eventual promoted form should stay static-k or go baseline-relative/decaying; J-1253 spawned to read the new shadow log once live days accrue. See update below.
**Owner:** core/climate_engine.py (dissonance reservoirs + ignition) · core/orchestrator.py `_on_dissonance_ignition` · core/homeostasis_causal.py (projects the same accumulator forward for its coherence/novelty forecast — imports climate_engine's rate constants directly since F-0810/J-0582, 2026-09-04, not a hand-copy)
**Founder ask (2026-09-04):** "Let's investigate whether we can make it both pressure driven AND time driven."
**Evidence:** F-0799 (what a self-generated cycle is), F-0801 (the 42-min clock), F-0802 (the pinned bleed), F-0803 (replay + acute response). Related rulings: D-0142 (its defeater names "integration_drive still pinned"), the 2026-06-15 exploratory-ignition research (`docs/curiosity_ignition_research.md`).

```plan-state
stage: live
phase: Option A live since 2026-09-08; D-0211 re-knee shadow log live since 2026-09-25 (J-1253 first read done: promotion as built not supported, D-0332 open)
verified: 2026-11-14
evidence_read: 2026-10-15
gate: D-0332 ruled (split the two jobs, re-knee only what dominates); J-1686 second read needs 10 or more live days
next: J-1780 reads the v2 rows after 5 or more live days of Du uptime on the build (not before 2026-10-11): proposes hint and symbol thresholds and reports the completion-excluded label variant; J-1686 still reads completion_raw not before 2026-10-10; Du must be restarted for either to produce evidence
cluster: 0
```


## Current State — verified 2026-11-14

- **2026-11-14** (F-4586): J-2662 built Option E shadow-first (worktree commit 8f67ab61, restart-gated): core/ignition_promotion.py logs would-promote rows to data/ignition_promotion_shadow.jsonl; dormant live path behind PROMOTION_LIVE=False. The stream ignition wire (F-0807) was already live via J-0580. homeostasis_causal port judged safe to omit while off (documented in the module). Needs a Du restart for rows to accrue.
- **2026-10-15** (F-2813): J-1780 D-0332 label-view first read done (192 live h): k's centre, completion bounded <=7, label ~ legacy when completion excluded, old 0.55/0.65 thresholds always-on/never; hint ~0.60 proposed. See F-2813; promotion is a founder decision.

- **2026-10-15** (F-2801): J-2058 third read at 13.34 live days: completion_raw bounded (daily medians 0-7, latest 4); D-0332 defeater (i) does not fire; completion k should be re-sized to about 5-10 (or dropped) for the label view, not 30. Shadow/autonomy k still centre; belonging raw median 72 vs k 85. J-1780 owns the v=2 label-view read.
- **2026-10-10** (F-2671): J-1686 interim evidence read (2026-10-10): 7.822 live days on the J-1226 build (gate 10 not met). completion_raw bounded 3-7 (latest 5.0), no climb toward 30; tension pool 88->128 slowly re-accumulating; k's off (raw medians 111/72/31/5). D-0332 defeater (i) not triggered yet; successor job carries the 10-day verdict.

- **2026-10-04** (F-2399): J-1763 built D-0332 option B as a SHADOW-ONLY label view (worktree commit 66aa070, merged by the job-run orchestrator, NOT live until Du restarts): k re-sized to 116 75 33 from the J-1253 window medians, completion_tension dropped from the cluster pending J-1686, log row schema v2 adds all nine live dimensions plus dissonance plus propagated novelty_hunger plus would-fire flags for a 0.40 to 0.70 candidate threshold grid (no live threshold chosen); live field, pressure and the reservoir byte-identical before and after (test 24 of 24, fails without the change). F-2400 INFERRED caution: with completion left at its live knee it would lead the label view on most rows, so the first read must report the completion-excluded variant
- **2026-10-03** (F-2264): J-1253 first read of the re-knee shadow log (4.96 live days, 6148 rows): both gates met; as built the re-knee widens the dominant value range but relocates the pin to a two-way near-tie (integration_drive 50 percent, autonomy 40 percent), would silence the Reflection symbol channel and, per a validated first-order replay, nearly starve the defensive ignition channel; completion_tension no longer pins since the J-1276 tension-demotion fix drained 632 stale tensions at the same restart, so D-0260 premise lapsed; founder decision D-0332 opened, J-1685 and J-1686 spawned

### What we have
- Option A (unpin the integration_drive bleed) RULED D-0148, built J-0594, LIVE since 2026-09-08; J-0671's
  formal defeater read (F-1568/F-1570-73) found it met only marginally (defensive share 48.2%, cycles/day
  62.65 vs the 45 ceiling) — not reopened, ceiling basis left unsettled.
- D-0211 RULED 2026-09-19 to re-knee the whole saturated cluster (shadow/belonging/autonomy/completion),
  sized by J-1151 (F-1723); J-1226 BUILT the shadow-first re-knee (F-1754) — nothing switched live yet.

### What we need
- Du restarted onto the J-1226 build (`da061f3`) plus ~5 live days on `data/climate_reknee_shadow.jsonl`
  before D-0211's discriminative-range question or D-0260's completion_tension-k question can be answered
  (J-1253 checked 2026-09-24, F-1833: gate still NOT met).

### What we're doing next
J-1253 stays open/in_progress; re-check the restart gate each session until Du restarts onto `da061f3`
plus 5 live days, then run the combined D-0211/D-0260 read.


## Options

**A. Unpin the bleed (fix `integration_drive` normalisation).** Additive: compute momentum against a baseline (events per hour relative to a rolling daily mean, or D-0142's verdict subset with a knee sized for it, e.g. k≈60), so the value varies with actual recent integration instead of sitting at 0.98. Replay (F-0803) predicts: bleed input ~0.5 → ~12 defensive fires/day (from 4.5), median gap ~80 min; exploratory floor untouched; ~35 internal cycles/day total (from ~27). Also resolves D-0142's defeater. Risk: rumination if completion/shadow stay pegged (shadow 0.978, completion 0.904 live) — guard with a per-hour cap on defensive fires (e.g. max 3/h) logged as `capped` in ignition_log.

**B. Make the time channel honest, not blind.** Keep a baseline reach (a mind wanders even when nothing presses) but key its rate to backlog *growth* (open questions born since the last fire) or a reading-momentum term, and lengthen the floor (60–90 min) so pressure fires visibly fill the gaps. Optional; changes cadence Travis is used to.

**C. Acute impulses.** Named events add a lump to the defensive reservoir through a new `nudge(source, amount)` API: critic rejection (+0.15), `[s2] self-claim contradicted` (+0.25), tension REFUTES / commitment `drop_denied_ESCALATE` (+0.10). Refractory 300 s still applies. Makes a challenge produce a thought within minutes rather than 7–40. Log each nudge in ignition_log `contrib` so the share is readable. Needs the caller sites in core/orchestrator.py, core/critic*, core/commitment*, core/tension_ledger.py.

**D. Leave timing as is.** Accept the 42-min clock; content is already self-generated (F-0799).

## Recommendation
A first (a real normalisation bug and D-0142's own defeater), measured for one week from `data/ignition_log.jsonl` (defensive share, gap distribution, cap hits) with the rumination guard on. Then C if pressure fires still lag real events by more than ~10 min. B only if the founder wants a slower floor.

## Blast radius (UDMS dossier 2026-09-04: LOW, PURE_SCALAR_TWEAK)
- Static dependents: core/orchestrator.py (beta = base + range × `field.pressure()`), core/competence.py (feeds strain/novelty), core/identity_cost.py.
- **Hidden coupling UDMS did not flag (updated 2026-09-06, J-0594):** core/homeostasis_causal.py:148-236 *re-implements the accumulator* for its coherence/novelty forecasts, projecting it forward from a `climate_state.json` snapshot rather than reading a live object. As of F-0810/J-0582 (2026-09-04) it *imports* `_DISS_RATE_*`/`_DISS_MAX`/`_IGNITION_THRESHOLD`/`_REFRACTORY_SECS` directly from climate_engine.py rather than hand-copying them, so a RATE-CONSTANT change (unlike this job's own, which touched neither) now mirrors automatically. A discrete BEHAVIOURAL rule (like the refractory window, or J-0594's new per-hour defensive cap) is a different kind of thing and does NOT mirror automatically — it must still be deliberately ported into `_simulate_reservoirs`'s own loop, or explicitly judged safe to omit and documented as such (see that function's own comments for exactly how J-0594 judged the new cap). core/homeostasis.py reads `novelty_hunger`, which carries a `dissonance.value` self-term.
- Test harness: scripts/exploratory_ignition_test.py (in-vitro, temp stores). Add a replay script over ignition_log as the measuring instrument for A.
- Not in conflict with the "intentional, not a rule" law: ignition is an existing mechanism (06-15); this is calibration, not a want→act bridge.

## Gate
Founder ruling on which option(s) → build → restart-gated → one-week read of ignition_log → promote or revert.

## Lane 2 (the Witness) — founder question 2026-09-04: "will this change how we treat this?"
Today, no: Lane 2 is shadow (`LANE2_LIVE=False`), ticks every 300 s, writes only its own shadow log and store, reads Lane 1 as three scalars plus the hint queue, and touches no reservoir, field, frontier, or tension (F-0804). It is already the shape D-0148 asks for in miniature: a fixed clock with a real per-tick pressure signal (71% of judged predictions broke on 09-04).

When Phase 1 (the read path, undesigned by plan §5/§6) lands, three things change:
1. **Its natural entry is the pressure channel.** A broken prediction is `world_model_strain` in the literal sense. Mirror §2.5's two-channel form in reverse: a continuous scalar (prediction-break rate → strain), and a discrete channel (a broke-prediction becomes a frontier question of source `witness`, so it enters curiosity's pool). That makes option A a prerequisite (or Lane 2's pressure is bled away with the rest) and takes over part of option C (acute impulses from the world failing his expectation, rather than from Lane 1's own critic).
2. **Two clocks, not one.** Lane 2's tick is an independent time floor. Do not let it also fire Lane 1 cycles by clock; only its pressure should cross over. Otherwise the 42-min problem doubles.
3. **Telemetry per lane.** "Internal cycles/day", the defensive share, and D-0148's defeater thresholds need a lane column; core/homeostasis_causal.py's duplicated accumulator must learn the new source too.

Watch item surfaced while reading: D-0058's echo-disease defeater looks met (distinct predictions 0.66 today, one repeated 12×; F-0805) — a read is queued before any promotion talk.

## Reframe (founder, 2026-09-04 evening): "my original plan was a thought stream and not pulses"

The stream already exists and is live (docs/plans/continuous_stream.md, Phase 1, `CONTINUOUS_STREAM=True`): 970 idle thoughts on 09-04, median gap 49 s, paced by `core/stream_drive.py` with `would_gap == actual_gap` on every row (F-0806). What the 42-min clock schedules is not thought but **deliberation** — the orchestrator's full cycle (recall, scene binding, critic, commitment). **Corrected 2026-09-04 (F-0808):** commitments are formed from STREAM thoughts by the monologue's ledger scan; the deliberate-cycle ids on the rows were stale labels. Deliberation neither writes nor reads the commitment ledger. So the stream is the consequence-bearing loop and deliberation the pressure-bearing one, and the two share almost nothing (see docs/archive/loop_wiring_matrix.md). The stream still has no path to promote one of its own thoughts into a deliberate cycle.

Two defects the reframe exposes:
1. **The stream is deaf to the reservoirs.** `stream_drive._ignition()` calls `core.climate.ignition_level()`, which does not exist; the term silently falls back to protoself drive alone (F-0807). Pressure cannot deform the stream's trajectory today because the wire was never connected.
2. **Deliberation is scheduled, not emergent.** The accumulator decides *when* a heavy cycle runs; the stream's own state (building, grounded, high drive, a train that has found something) has no say.

**Option E — ignition as promotion, not scheduling (recommended objective).**
- Wire `stream_drive._ignition()` to the real engine: expose `ClimateEngine.ignition_level()` = max(defensive value, explore value) / threshold, and register it where the node can reach it. Pressure then paces the stream continuously (Rail A's original intent) — this is the "pressure deforms the trajectory" half.
- Promote from the stream: when a train is `_building`, grounded, and the ignition level is high, hand the train's current thought to `run_cycle(..., input_type="internal")` instead of waiting for the accumulator; reset the reservoir that licensed it. Deliberation then emerges from the stream's state — the "thought emerges, then state changes" half.
- Demote the exploratory accumulator to a floor (reach when nothing has been building for a long while), and keep A (unpin the bleed) because a pinned bleed flattens the very level the stream would now read.
- Keep the scheduler underneath as infrastructure (5-s climate tick, stream gap controller); the causal reason for a deliberate cycle must be readable in the state at the moment of promotion — log it in `ignition_log.jsonl` as `trigger: promoted` with the stream row's drive/progress/grounded values.

**Metrics that replace "pressure fires/day":** share of deliberate cycles that were promoted from a building train vs fired by the accumulator; correlation of the stream's ignition term with reservoir level (today 0); commitments formed per stream-promoted cycle vs accumulator cycle; gap between a real event (critic rejection, contradiction, broken Witness prediction) and the next deliberate cycle.

Guards: Rail B's grounding gate applies to promotion (anchor-less self-reflection may not promote); per-hour cap on promoted cycles; the existing single-flight `_cycle_active` guard; homeostasis_causal mirrors any new term.
