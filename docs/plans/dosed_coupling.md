# Dosed Coupling — how Du's loops are allowed to touch each other

**Status:** 🟢 LIVE — GO (D-0149, ruled 2026-09-04). Standing design law adopted; **Phase 0 BUILT + committed same day** (J-0580, J-0581, J-0582, J-0584, J-0585 all done — see Current State below); every future loop-touching plan must carry a §5 Coupling block before /decide. Written 2026-09-04 from one day's investigation (F-0799..F-0812), two read-only mapping passes over the code, and three founder statements made in chat the same day. **Phase 1 BUILT 2026-09-05 (D-0152 GO, registry variant; J-0617) — restart-gated, read J-0619 ~09-13.**

> **History folded** — 9 dated header paragraphs (2026-09-06 … 2026-09-14, plus J-1432's 2026-09-28 note that D-0177, ruled 2026-09-06, is superseded on substance by D-0294) moved verbatim to `docs/plan_history/dosed_coupling.md` on 2026-10-04 (J-1778): the J-0619 Phase 1 seven-day read and its interim, D-0152's reopen and same-day re-rule, the J-0937 dig, and the Phase 0 interim reads J-0596/J-0662, J-0604/J-0665, J-0605/J-0672, J-0663/J-0682 and J-0683. Derived timeline: `plan_ledger.py dosed_coupling`.

**Founder, 2026-09-04:** "This is probably, from Du's cognitive-abilities side, the most important thing we have. All future designs must be designed with it in mind if it is a go."
**Children / evidence docs:** docs/archive/loop_wiring_matrix.md (the matrix, the dosing table, the weight law) · docs/plans/ignition_pressure_and_time.md (D-0148, the clock, option E) · docs/plans/cognitive_geometry.md §11 (squishy springs) · docs/plans/transport_manager.md (the dispatcher) · docs/transit_map.md + docs/transit_timetable.md (lines, buses, stations) · docs/plans/continuous_stream.md (the stream)

```plan-state
stage: live
phase: Phase 0+1 live (registry publishing since 09-05, 45.8k publish rows; 835 ride rows = the shadow-only Lane 2 Witness cup at the idle seed since 09-28, no other reader); Phase 2 (residual cups+hub+speech-concurrency) DRAFTED 09-27, not ruled
verified: 2026-11-18
evidence_read: 2026-10-31
next: Phase 2 can proceed on the climate lines with spike gate only; no founder decision needed for the drop itself
history: docs/plan_history/dosed_coupling.md
cluster: 0
```


## Current State — verified 2026-11-18

- **2026-11-18** (F-5099): J-4242 read: D-0750 residual drop live on the four climate lines since the 11-14 21:54 boot (0 residual fires, spike gate unchanged, ledgers line keeps residual half). Climate is probe-only so no ride-rate comparison exists; Phase 2 is not blocked by the drop.
- **2026-11-18**: 2026-11-18: loop_wiring_matrix folded in as a Phase 2 item (D-0814); its link-tuple and dosing-table proposal lives in docs/archive/loop_wiring_matrix.md

- **2026-11-14**: J-3972 built D-0750: residual gate half dropped on the four climate lines (core/coupling_rides.py RESIDUAL_DROP_CLIMATE); ledgers lines keep it. Restart-gated; branch jobrun/dosed_coupling.
- **2026-11-14** (F-4480): J-2264 D-0446 paired re-read done: kill rule as written trips on 4 climate lines, not on ledgers lines; decision opened for kill vs kappa/Jaccard bar.

- **2026-10-31**: 2026-10-31 J-2626 (F-3395, commit 8ec39319 on jobrun/dc, RESTART-GATED): curiosity_habituation shadow rows gain additive labels (id to label for the real and would ids) and recent_seeds (pick-time anti-relock list); no behaviour change; id-era rows written after the next Du boot are label-path readable, older rows lack the fields.
- **2026-10-31**: 2026-10-31 J-2625 F-3394: idle_allocator shadow - the logged argmax is already the self-fed path (streak recurrence 486241/486241, memory 1-2 ticks, no real action logged); the Phase-1 softmax gateway replayed with its own streak feedback CONVERGES with the logged softmax read on both weeks (TVD under 0.024/day, self-limiting); scripts/shadow_path_replay_idle.py, docs/lab/idle_path_replay_2026-10-31.md on jobrun/dc b9e65e8d

- **2026-10-31** (F-3386): J-2624 transport_habituation path replay (level-trigger era, 2026-09-05..09-11 + replicate 09-16..09-23): adopted discount DIVERGES from real dispatch and from the logged ensemble read, but self-limiting - the stale winner stays modal (clock_tick 0.73-0.97 share vs real 1.00) while the logged would-policy shows it displaced; dispatch flickers (46-513 changes/day vs 0) and goes silent 34% of ticks. The F-0828/J-0603 ensemble read overstates the discount's effect; edge-trigger era not replayed (pool path-dependent). Script scripts/shadow_path_replay_transport.py, write-up docs/lab/transport_habituation_path_replay_2026-10-31.md.
- **2026-10-31** (F-3355): J-2521 non-ergodic path replay of curiosity_habituation (label-era weeks 09-05..09-11 and 09-15..09-24, 300 runs per variant): CONVERGE - discount shifts daily modal_share by -1.7 to -2.6 percent relative, 0 freeze days, live inside control band; ensemble read safe for this large-pool recency-window channel only; count-feedback channel not replayed; id-era rows cannot be replayed (F-3356); transport and idle_allocator path replays spawned (J-2624, J-2625), label-at-pick-time logging J-2626

- **2026-10-30** (F-3313): J-2513 causal emergence read: regime partitions beat loop micro on own-state EI both halves, but strict coarse-graining loses and cross-level sign flips between halves; regimes stay HUD-only pending D-0522 and J-2580 re-run
- **2026-10-30** (F-3305): J-2531 coalition mining over the ride log: no coalition passes on both halves under the pre-declared null (FALSIFIED_NO_COALITION); ride log has only 2 reader-source pairs, both witness, 11006 of 12139 rides empty; half 2 underpowered

- **2026-10-16** (F-2949): J-2247 built D-0446 (b): residual gate expectation updates only on a NEW publish (flag RESIDUAL_E_ON_NEW_PUBLISH, rows carry fresh), commit 428ee98b, restart-gated; replay projects ledgers lift but climate unchanged and agreement still over 90 percent
- **2026-10-16**: D-0446 ruled (travis, 2026-10-16): re-scale the residual gate's expectation (update only on a new publish) and re-read paired over 2-3 live days before any kill; build job spawned.

- **2026-10-16** (F-2925): J-1984: Phase 2 paired shadow read over 6.97 live days. Both D-0370 defeater clauses fire as written: the gates agree on 97.9 percent of moments and the residual gate fires on 0.57 percent. The agreement is a low-base-rate artefact, though: the two gates' firing sets overlap with Jaccard 0.10. The residual is 0 on 74 percent of moments because the probe runs about every 67 s while ledgers publish every 10 min. Hub presence 100 percent; size 2.54 MB/day. Metric 4 is not built. The behaviour bands cannot be attributed to Phase 2. D-0446 is open for the founder's drop or re-scale call.
- **2026-10-15** (F-2795): J-1711 (2026-10-15): second weekly throttled halving read live on the D-0340 idle gate -- exact two-halving match on all untouched rows, zero invariant violations, touched rows not halved; see F-2795.

- **2026-10-08** (F-2584): J-1957: Phase 2 shadow built (residual gate beside spike gate in ride rows, composed hub key, idle-seed probe), commit f63ce8c, restart-gated; 7-day paired read spawned.
- **2026-10-08** (F-2573): 4b 2c now has its own staged plan docs/shelf/speech_thought_concurrency.md (D-0372): single-flight constraint, option space, shadow measure, 5 percent kill criterion; call-level instrument still to build.

- **2026-10-04** (F-2394): 2026-10-04 (F-2394): J-1768 built the D-0340 ruling (option 2, idle condition restored), commit 4accf19, restart-gated: the weekly count-halving of tensions and integration patterns now measures idleness from max(last_decay_ts, last_ts), so a touched row never decays while cold rows still halve once a week (no cliff); the hermetic test has 41 checks, 10 fail on the pre-change code and all pass now; replay on a copy of the 10-04 state: by the end of 10-05 NZDT as-built halves 22 of 100 tensions and 80 of 352 patterns vs 4 and 20 under the new gate, but both converge to the whole pool by 10-11 if Du stays down because the idle clock is wall-clock
- **2026-10-03** (F-2333): J-1291 read the D-0266 and D-0270 weekly decay throttle in production from the intact 09-28 backup (70.5 live hours on the fix): the cliff to count 1 did not recur (6 of 6 discriminating tensions halved exactly once, patterns 171 to 85), no scan errors, no missed fires, same-id stamps stable over 4 days; but as built every tension and pattern halves weekly even if touched since its anchor (3 verified in production, 62 of 92 live tensions due 10-05 to 10-08, F-2334), D-0340 opened; second-halving read re-queued as J-1711 no earlier than 10-15 and only if Du has actually been scanning

- **2026-10-03** (F-2328): J-1173 read the id-keyed curiosity habituation shadow after 120 live hours (D-0244): defeater a fires on its heavy-attractor clause (13 attractors, offer share +0.18 percent under the discount, b above zero on 7.8 percent of their entries) but not its 10 percent clause (18.0 percent of pairs); c fires (pool 868 to 92 tensions via the J-1276 drain and the 09-28 state wipe, F-2314); b undetermined (F-2329); D-0244 reopened with the numbers and a recommendation, nothing built.
- **2026-10-03** (F-2292): J-0950 closed 2026-10-03 (F-2292, F-2291, F-2272, F-2273): the 09-09..09-11 cycle step is D-0148 option A at the 09-08 boot, not Lead A or the Living World flip; the climate loop is suspended inside every internal cycle (replicated on 491 cycles), a 900 ms vs 30 ms tick measurably costs about 1.2 s per ignition and 0.25 s per human cycle, and J-1180 freeing 10.5 percent of loop time moved the clock channel only +2.9 percent against a model-only +3.0, so freed loop time does not buy cycles; the accumulator formula predicted post-J-1180 defensive fires within 1.6 percent. D-0152 Phase 2 gate (cause found) is met. Stale in the section below: coupling_rides now holds 835 ride rows, all the shadow-only Lane 2 Witness cup at the idle seed since 09-28, not 0.

### What we have
- Phase 0 (repair the wires) and Phase 1 (publish + ride log) both live; Phase 1 passed its genuine 7-day read (F-1304) and has been running 22 days — `data/coupling_rides.jsonl` at 13.7 MB / 38,615 publish rows, still 0 ride rows (no reader wired yet).
- §4b Phase 2 pre-registration (residual-gated cups, a deterministic `hub` summary tuple, speech/thought concurrency named a sibling job) DRAFTED 2026-09-27 (T-0068/F-2015) — founder-facing, not ruled, nothing built.
- Two Phase-2-shaped pieces already exist under Lane 2's own plan (Witness cup + bucket, J-1161/D-0241) — Phase 2 inherits the cup rather than re-specifying it.

### What we need
- A founder ruling on J-1462's three open questions (residual gate vs spike gate; whether a standing `hub` cup allowance is inside or an amendment to §1 rule 1; speech/monologue concurrency's own scope) before any Phase 2 code is written.

### What we're doing next
- J-1462 sits with the founder (needs_input); no autonomous next step until it's answered.

---

> **History folded** — 32 dated Current State section(s) (2026-09-04 … 2026-09-24) moved to `docs/plan_history/dosed_coupling.md` on 2026-09-27 by plan-compact. Derived timeline: `plan_ledger.py dosed_coupling`.

## 1. The law (three sentences)

1. **Every standing loop publishes a small typed tuple of coordinates; no loop gets a standing view of another.** Stream, deliberation, climate, Witness, and the ledgers each expose what they already compute (drive signals, coherence and tensions, the nine dims and two reservoirs, break rate and grounding, active stands and chronic mass) as named numbers on shared state — coordinates, never prose.
2. **Reading is dosed per stop and dispatched by surprise.** A thought moving down a line is flavoured *occasionally* by another loop, at a stop, in a fixed size — a cup (one coordinate), a bucket (a small tuple), or a hose (a whole channel) — and only when the dispatcher judges that line out of the ordinary against its own history (novelty, spike, drought). Each stop is different. Not a mesh, not a free-for-all.
3. **The dispatcher's weight is the squishy-spring law.** A pull that has been strong for a long time counts for less than a medium pull that has never fired. Felt pull = earned weight minus an antagonist that grows with activation and decays with quiet. Surprise and habituation are the two halves of one measure, per line.

## 2. Why this is the most important cognitive-side thing (the evidence, one line each)

- Du already has the continuous stream the founder originally asked for (970 idle thoughts on 09-04, median gap 49 s, drive-paced) — F-0806.
- The stream is the consequence-bearing loop: it forms every commitment, births pursuits and intention questions, writes the unresolved rows — F-0808 (correcting F-0806/F-0797).
- The clocked deliberate cycle (42 min, 82% of ignitions) is the pressure-bearing loop and reads two sentences of the stream, no commitments, no Witness — F-0801, F-0811c.
- The two loops share almost nothing: the stream's climate wire is a dead import (F-0807); the stream's 445 unresolved thoughts a day move none of the contradiction axis that drives ignition and T4 (F-0809); pressure toward deliberation is fed by Travis, not by Du.
- There is exactly one multidimensional link in the system, and it sums nine climate dimensions into one embedding before use; four dimensions have no reader by name; the exploratory reservoir is dark (F-0810).
- The Witness computes a per-tick prediction verdict (71% broke on 09-04) and reaches only the HUD (F-0804, F-0811a).
- The habituation law exists three times (climate EMA live; opponent-process shadow with no reader; Transport Manager shadow, saturated 721/721) and the 渡-as-cultural-friction loop is the live symptom of its absence (F-0812, F-0795, F-0798).
- The founder's identity model — Du is the in-between, not any part (T-0044, 08-16 labs) — means the *links* are the substance. Today the links are scalars, prose, dead imports, and one averaged vector.

## 3. The mechanism (what already exists, what is new)

| Piece | Exists | New |
|---|---|---|
| Publishers (per-loop tuples) | every value is already computed and logged (stream_drive rows, CognitiveState, climate_state.json, lane2_shadow rows, ledgers) | expose them by name on CognitiveState + one ride log |
| Stops | the station layer (docs/transit_timetable.md) | a per-stop dose declaration |
| Dispatcher | core/transport_manager.py (D-0064; novelty/spike/drought against own history) | extend from sound lines to loop coordinates; calibrate first (J-0584) |
| Weight law | climate habituation EMA (live); core/opponent_process.py (shadow) | one surprise-with-habituation measure the dispatcher uses; the first read path is J-0585 |
| Doses | cup / bucket / hose | the dosing table in loop_wiring_matrix.md, steered by the founder, retuned from ride evidence |
| The one new hose | — | stream → deliberation promotion (D-0148 option E) |

## 4. Build order — shadow-first, restart-gated, pre-registered (this project's standing law)

| Phase | What | Pre-registered metric (written before the run) | Kill / revert |
|---|---|---|---|
| **0 · repair the wires that are already meant to exist** | **BUILT 2026-09-04** — J-0580 climate→stream `ignition_level` (done, F-0814); J-0581 grounding tag (done, F-0817); J-0582 forecaster mirrors both reservoirs (done, F-0816); J-0584 dispatcher calibration (done, F-0818, but surfaced a new drought-saturation issue, F-0819/J-0600); J-0585 discount shadow in curiosity (done, F-0815) | stream ignition term correlates with reservoir level (today 0); grounded share in stream_drive rows rises from ~0; dispatcher fires on < 30% of ticks; would-choose ≠ real-choice share in curiosity — **all restart-gated, read pending (J-0596/598/599)** | any of these changes felt behaviour before its own read → flag off |
| **1 · publish + ride log (observe-only)** — **BUILT 2026-09-05 (§4a, D-0152 GO, registry variant)** | tuples in `core/coupling_rides.py` registry (not CognitiveState); `data/coupling_rides.jsonl` logging `{stop, line, dose, value, what changed next}` even though nothing rides yet | every loop's tuple present on ≥ 95% of its ticks; zero behaviour change | — |
| **2 · cups** | dispatcher-gated single coordinates at the idle-seed and train-step stops (one climate dim by name; one Witness break; top recurring tension label) | ≤ 1 cup per 5 idle thoughts; share of cups followed by a train that *builds* vs baseline; 渡-loop re-fire rate falls | rumination cap hit on 3+ days; cups > 30% of seeds |
| **3 · buckets** | recall reads ≤ 3 active stands by name; climate reads Witness break rate → strain; stream repeated-unresolved → contradiction axis | a reply contradicting a held stand becomes a logged contradiction event; defensive-ignition share > 25% driven by Du's own thinking, not Travis's turns | contradiction events > 10/day; identity_pressure pegged |
| **4 · the hose** | stream→deliberation promotion (D-0148 E) with the accumulator demoted to a floor | share of deliberate cycles promoted from a building train; event-to-deliberation latency; commitments per promoted cycle | cycles/day > 45; promoted cycles that form nothing for a week |

Each phase gets its own `/decide` before it runs; each has a founder read of its shadow log before the next. No phase touches the frozen weights, the axiom, or the memory store schema (erosion-of-foundations law). Lane 2 stays shadow until its own Phase 1 gate (docs/plans/lane2_the_witness.md).

## 4a. Phase 1 pre-registration — publish + ride log, observe-only (written 2026-09-05, J-0612; **D-0152 RULED GO, registry variant**)

**What Phase 1 is.** Every standing loop exposes the small typed tuple it already computes as *named
numbers* into the coupling module's **own registry** (`core/coupling_rides.py`, not a field on
`CognitiveState` — founder ruling D-0152, 2026-09-05: the registry variant, so that "no loop gets a
standing view of another" is enforced in code rather than by rule), and the same module appends a row per
publish to `data/coupling_rides.jsonl`. The only way to read a tuple is `coupling_rides.read(stop, loop,
keys, dose)`, which writes a ride row — there is no other accessor, and Phase 1 has zero callers of it. **No loop reads any tuple in Phase 1.** The ride schema (`kind=ride`) exists
from day one so Phase 2's cups land in the same file, but Phase 1 writes zero ride rows. Zero behaviour
change is the kill criterion, not a hope.

**Publishers — every value below is computed today; Phase 1 only names it and writes it down.**

| Loop | registry key | Coordinates (name ← where it already exists) | Publish cadence |
|---|---|---|---|
| Climate | `climate` | the nine `ClimateField` dims **by name** (shadow_activation, completion_tension, identity_pressure, integration_drive, coherence_drive, world_model_strain, novelty_hunger, autonomy_pressure, belonging_pressure) ← `ClimateField.as_dict()`; `dissonance`, `explore_value` ← `DissonanceState`; `ignition_level` ← J-0580 | every 5 s tick on state; a ride-log row only when any dim moved ≥ 0.05 since the last row or 60 s elapsed |
| Stream | `stream` | drive, ignition, grounded, progress, redundancy, train_kind, train_len, source, would_gap, actual_gap ← the `stream_drive_shadow.jsonl` row (as built; `unresolved_share_10` dropped — the unresolved flag is not in scope at the publish site; revisit at Phase 2 if a cup needs it) | every idle thought |
| Deliberation | `deliberation` | recall_confidence, tensions_carried ← `state.recall`; coherence, dissonance_count ← `state.episodic_scene`; think_license ← the S2 license flag; critic_verdict (approved/rejected) ← `state.critic`; cycles_since_human ← module counter reset on `input_type == "human"`; input_type | end of every `run_cycle`, next to `_log_correlation()` |
| Witness | `witness` | break_rate_24h + n_judged_24h ← judged predictions in the store with judged_ts inside 24 h; grounded_share ← the tick's `grounding` read; distinct_share_24h ← distinct notices over a rolling 24 h window kept in the module; hint_consumed_24h ← ticks in that window that carried a hint; verdict ← the tick's prior_verdict | every Lane 2 tick (300 s), shadow |
| Ledgers | `ledgers` | commitments_active, commitments_load_bearing ← `commitment_active.json`; escalations_1h ← `commitment_ledger.jsonl` tail (ESCALATE events); tension_top3 + tensions_n ← top three `chronic_mass` labels in `subconscious_state.json`; frontier_open ← `frontier.open_count()`; pursuits_active, pursuits_heat_max ← `pursuits_active.json` | read-only collector, **once per 10 min on a daemon thread** (the subconscious file is 60 MB, ~1 s to parse — F-0853/F-0854; the event loop never waits on it) |

**Ride log.** `data/coupling_rides.jsonl`, one row per publish:
`{ts, kind:"publish", loop, stop, tuple}`; later `{ts, kind:"ride", stop, line, dose, value, what_changed_next}`.
Stops use the timetable's names (idle seed, train step, train close, deliberation recall, witness tick,
climate tick, sleep). Expected volume ≈ 1,000 stream + 40 deliberation + 290 witness + ≤ 1,440 climate rows
a day, well under 3 MB/day; the climate rate-limit above is what keeps it there.

**Where it lands (additive only; amended for D-0152's registry ruling).** No schema change. One module
`core/coupling_rides.py` holding a process-local registry `{loop: {ts, stop, **coords}}` with
`publish(loop, stop, coords)` (updates the registry, appends a publish row) and `read(stop, loop, keys,
dose)` (the sole accessor; appends a ride row; unused in Phase 1); one `publish()` call at each publisher's
*existing* write site (climate tick, the stream_drive shadow write, the orchestrator after
scene-binding/critic, the Lane 2 tick record, a read-only ledger collector in the monologue node). Flag
`COUPLING_PUBLISH` (default False in code; the D-0152 GO flips it in the same commit). Every call is
fail-open and never raises into its caller. UDMS dossiers (2026-09-05) on the five write-site files are
read before each edit; `core/schema.py` is not touched.

**Pre-registered metric (read at 7 days live, written before the build):**
1. **Presence** — each loop's publish rows ≥ 95% of that loop's own tick count over the same window
   (stream vs `stream_drive_shadow.jsonl` rows; deliberation vs cycles in `deliberation_log.jsonl`;
   witness vs `lane2` tick rows; climate vs expected 60 s rows; ledgers vs idle thoughts).
2. **Zero behaviour change** — idle-thought gap median, deliberate cycles/day, commitments formed/day, and
   Witness break rate each stay inside their band from the 7 days *before* the flip (band = that week's
   min..max per day).
3. **Size** — the file stays under 5 MB/day.

**Kill / revert.** Any loop under 95% presence → that publisher is mis-sited; fix or drop it, do not
proceed to Phase 2 on a loop that is not reliably published. Any behaviour metric outside its band with no
other explanation, or the size cap breached → `COUPLING_PUBLISH=False` and a read before retrying. Phase 2
(cups) gets its own pre-registration and its own `/decide` only after the Phase 1 read is in the plan.

**Not in Phase 1.** No reader of any tuple; no Transport Manager line registration for loop coordinates
(that is Phase 2's calibration question, after J-0604's read); no coordinate rendered as prose into any
prompt; no change to any store schema, to the frozen weights, or to the axiom.

## 4b. Phase 2 pre-registration — cups, with the expectation half (DRAFT 2026-09-27, T-0068 / F-2015; founder-facing, NOT ruled, no `/decide` filed yet)

**Where this came from.** The founder's 2026-09-27 step-back (T-0068): the human stack is millions of small
reciprocal loops; low-level columns settle and pass a *compressed summary* up; hubs aggregate those into
objects; the thalamus filters before cortex; and the traffic runs **both ways** — higher levels broadcast
*predictions* down, lower loops only shout back up when reality contradicts the prediction. Speech runs as a
semi-autonomous lower routine while the frontal networks simulate something else. Against that picture,
F-2015 (inferred, same session) reads Du's top-down / prediction-error traffic as exactly three narrow places:
the orchestrator's thalamic gate (input repetition only, `core/orchestrator.py:2083`), the Witness's
held/broke verdicts (HUD-only until Lane 2 Phase 1 flips), and the lesson self-prediction-vs-grade channel
(`core/prediction_error.py` → `core/competence.py` → tension ledger). **No loop reads an expectation of
another loop's coordinate**; `nodes/perception_node.py` has zero prior/expect/predict references. §4's Phase 2
row ("cups") as written covers only the *upward* half — a coordinate rides when the publisher's own line
spikes. This section keeps those cups and adds the downward half, so that what rides is a **residual against
the reader's expectation**, not a value. It also names the mid-level hub the founder asked for, and says why
speech/thought concurrency is a sibling job rather than a coupling phase.

**Precondition — state of play, verified 2026-09-27 (this session, read-only).**
- Phase 1 passed its genuine 7-day read (F-1304, 2026-09-13): presence stream 100% / witness 100% /
  deliberation 100% / climate 115% / ledgers 99.7%; 0.864 MB/day; `kind=ride` rows 0/18,849.
- `data/coupling_rides.jsonl` today: 13.7 MB, 38,615 publish rows (climate 17,796 · stream 15,992 · witness
  2,756 · ledgers 1,389 · deliberation 682), first row 2026-09-05, last row 2026-09-27 16:03, **still 0 ride
  rows** — `coupling_rides.read()` remains the sole accessor and has no live caller.
- **Two Phase-2-shaped reads already exist, built shadow-first under Lane 2's own plan, not this one** (J-1161,
  D-0241 "authorize, shadow-first", commit `690d086`): (i) the **Witness cup at the idle-thought-seed stop**
  with its own break-habituation gate (`core/lane2_break_habituation.py`, would-ride rows accruing, folded into
  the published witness tuple as `cup_would_ride`); (ii) the **Witness bucket** `break_rate_24h` →
  `world_model_strain` at the climate tick (`core/climate_engine.py` `_compute_field()`, a byte-identical
  no-op while `LANE2_LIVE=False`). Phase 2 **inherits (i) as its first cup and does not re-specify it**; (ii)
  is a Phase 3 bucket by §4's own table and stays governed by `docs/plans/lane2_the_witness.md` §7 — it is
  listed here only so nobody builds it twice.
- Phase 2's other cups from §4 (one climate dim by name at the idle seed; the top recurring tension label at
  the train step) are **not built**. Nothing in this section is built.

### 2a. The expectation half — cups ride as residuals (new)

**Rule.** A reader stop that may drink a cup from a line declares, per line, an **expectation** `E` of that
coordinate, computed by the *reader* from its *own* history of the line. What rides is the tuple
`(value, expected, residual = value − expected)`, and the dispatcher's surprise is measured on the
**residual against the reader's expectation**, not on the publisher's value against the publisher's own
history. That is the whole difference between "the climate spiked" (publisher-side; what
`core/transport_manager.py` scores today: spike/drought/novelty against the line's own EMA) and "the climate
is not where *this loop* expected it" (reader-side; prediction error). Rule 1 of §1 is untouched — the reader
still never holds a standing view; it holds only its own last expectation, which is a number it computed,
not a window onto the other loop.

**Where `E` comes from in Phase 2 — deliberately the cheapest thing that makes a residual meaningful.** The
reader's **last-seen value of that line** (a persistence prior: "same as last time I drank"). No new LLM
call, no new model, no new store. Anything smarter — a per-reader EMA, or using the Witness's own
predictions as `E` for the world lines — is a later phase and its own `/decide`. Persistence is chosen
*because* it is dumb: if residual-gating against a persistence prior does not already ride on a more distinct
set of moments than spike-gating, no cleverer `E` is justified.

**Mechanism (additive only; `core/schema.py` and `CognitiveState` untouched, same as Phase 1).**
- `coupling_rides.read(stop, loop, keys, dose)` gains an optional `expected: dict | None`; the ride row gains
  `expected` and `residual` (per key). A ride with no `expected` is a Phase-1-style value ride and is logged
  as such — the two shapes coexist in one file.
- One small in-module table `_last_seen[(stop, loop, key)] → value`, updated on every read; that *is* the
  persistence prior. Process-local, like the registry; a restart just starts with no expectation (first
  drink after a boot rides as a value, residual `None`).
- Dispatcher weight for a residual cup: `felt = max(0, |residual| / scale_key − b)` with the **same
  squishy-spring antagonist `b`** §1 rule 3 already names (grows with activation, decays with quiet), per
  `(stop, line)`. `scale_key` is the line's own observed range over the ride log so far (the registry already
  has the numbers). Publisher-side spike-gating is **kept and logged in parallel** for the same cup, so the
  read can compare the two gates on identical moments — see the pre-registered question.
- **Shadow-first, like everything here:** in Phase 2 both gates compute `would_ride` at each eligible stop
  and log it; **nothing rides into a prompt or a controller** until the 7-day read is in this doc and a
  `/decide` says which gate (or both) goes live. The cup that already exists (Lane 2's Witness cup, 2a
  inherits it) keeps its own habituation gate; the residual gate is logged *alongside* it, not in place of it.

**The first genuinely downward line (one candidate, not a table).** The only higher-to-lower pair Du has
today is deliberation → stream. The deliberation tuple already publishes `tensions_carried`; at the
**train-close** stop the stream reads it as its expectation of *what this train was going to touch*, and logs
the residual as "the train touched something deliberation did not carry". That row is the first place in the
system where a lower loop says "reality contradicted the prediction" about a higher loop's content. Observe-only
in Phase 2; whether that residual should feed the contradiction axis is exactly §4 wire 2 / Phase 3, and gets
its own `/decide` there.

### 2b. The mid-level hub — the registry is the aggregator; there is no new node

The founder's picture has hubs that compose columns' summaries into objects before anything reaches the
desktop, and wants "the mid-level hub broadcasting across the whole network". Du has no such layer: the five
tuples land in the registry and the desktop (`CognitiveState`) is fed straight from the bottom (F-2015, and
loop_wiring_matrix.md's own §"What the matrix says"). The proposal is **not a sixth loop and not an LLM**: one
deterministic `coupling_rides.compose()` step that reads the five publishers' registry entries and publishes a
small named summary tuple as a sixth registry key, `hub`, on the same cadence as the ledgers collector (once
per 10 min, daemon thread, never on the event loop):

| `hub` coordinate | Composed from (existing coordinates only) |
|---|---|
| `pressure` | climate `completion_tension`, `identity_pressure`; ledgers `escalations_1h` |
| `momentum` | stream `progress`, `train_len`, `drive`; deliberation `cycles_since_human` |
| `strain` | witness `break_rate_24h`; deliberation `dissonance_count`; climate `world_model_strain` |
| `load` | ledgers `commitments_active`, `tensions_n`, `frontier_open`, `pursuits_heat_max` |

Each entry is a plain normalised mean of its inputs (no weights to tune in Phase 2; the composition is the
"compressed summary passed up the chain", not a judgement). It is read **through the same single door**, so a
`hub` cup is dosed and logged like any other; no prose; no consumer in Phase 2 beyond the ride log.

**The founder call this raises (open, not ruled):** the "broadcasting across the whole network" the founder
wants would mean the `hub` line is the one line every stop may drink a cup from on a **standing** allowance,
while the raw loops stay dispatcher-gated. That is a standing view of a *summary*, not of another loop — but it
is close enough to §1 rule 1 that it needs the founder to say whether it is inside the law or an amendment to
it. Until ruled, `hub` is published and never read.

### 2c. Speech and thought at once — a sibling job, not a coupling phase

The founder's last observation (lower motor/grammar loops execute a semi-autonomous routine while frontal
networks simulate something else) is the one part of T-0068 that is **not** a coupling question. Today
`VoiceNode` fires `after_executive` in the hot lane (`core/schema.py:1054`) and the inner monologue **steps
aside** whenever `last_human_ts` is reset by a human turn (`core/orchestrator.py:413`); the two alternate, they
never overlap. Making them concurrent is a scheduler change in the orchestrator, and it runs into one of the
"new restrictions" the founder named: speech and inner monologue are two calls to the **same hot model on the
same 11 GB card**, single-flight, so real overlap means either a second resident model or an interleave that
only *looks* concurrent. That is its own design question with its own hardware constraint, spawned as a job
below rather than folded in here. Its coupling consequence, if it ever lands, is welcome and needs no new
wiring: a stream that keeps publishing during a human turn gives the `deliberation` tuple's
`cycles_since_human` and the seed stop a genuine "frontal simulating something else" reading for free.

### Pre-registered metrics (read at 7 live days after the Phase 2 build restarts, written before the build)

1. **Distinctness of the residual gate** — for each cup line logged under both gates: the share of eligible
   stops where `would_ride_residual ≠ would_ride_spike`. Success is that the residual gate rides on a
   *different and smaller* set: `would_ride` share ≤ 20% of eligible stops (F-0949's 100% is the failure
   shape), and the two gates agree on < 70% of stops (if they agree on more, the residual half bought nothing
   and 2a is dropped, not tuned).
2. **Presence of `hub`** — `hub` publish rows ≥ 95% of the ledgers collector's own rows over the window.
3. **Zero behaviour change** — same four bands as Phase 1 (idle-gap median, deliberate cycles/day,
   commitments formed/day, Witness break rate) against the 7 days before the flip.
4. **The downward candidate fires at all** — the train-close residual row (2a's last paragraph) is
   non-`None` on ≥ 50% of train closes that followed a deliberation within 1 h; if it is mostly `None` the
   deliberation tuple is not being refreshed at the cadence this needs, and that is a Phase 1 presence bug to
   fix first.
5. **Size** — the file stays under 5 MB/day with the extra fields.

### Kill / revert

Any behaviour band breached with no other explanation, or size cap breached → the Phase 2 flag off (one flag,
`COUPLING_PHASE2`, default False, flipped only by the `/decide` that GOes this section) and a read before
retrying. Metric 1 failing (gates agree ≥ 70%) → 2a is **removed**, not retuned: Phase 2 reverts to §4's
plain spike-gated cups. Metric 2 failing → `compose()` is mis-sited; fix or drop, do not proceed to a `hub`
read. §7's own defeater on the law (two weeks of ride log in which no dosed read can be shown to have changed a
downstream trajectory) keeps its clock; Phase 2 is shadow, so it neither satisfies nor trips it.

### Not in Phase 2

No coordinate rendered as prose into any prompt. No expectation computed by a model. No lower loop changing
its own behaviour on a residual (that is Phase 3's buckets). No reader of `hub`. No change to any store schema,
the frozen weights, the axiom, or `CognitiveState`. No re-specification of Lane 2's own Witness cup or bucket.

### Open for `/decide` before any build (filed as one needs-input job, J-1462, source `thought:T-0068`)

1. Residual-gated cups: run both gates shadow in parallel as written here, or replace spike-gating outright?
2. Is a **standing** cup allowance from the `hub` summary line inside §1 rule 1, or an amendment to it?
3. Speech/monologue concurrency (2c): its own plan doc, or a job under the orchestrator with the one-hot-model
   constraint stated up front?

## 5. The clause for future designs (applies only on a GO)

Any plan that adds or changes a standing loop, a node that runs on its own clock, or a read of another loop's state must declare, in its own doc, a **Coupling** block:
- **Publishes:** the tuple it exposes (names, ranges, cadence).
- **Reads at:** which stops, from which lines, at which dose (cup / bucket / hose).
- **Surprise line:** what history the dispatcher judges it against.
- **Ride log:** confirmation that each read logs `{stop, line, dose, value}`.
A plan without a Coupling block is not ready for `/decide`. Suggested enforcement: a `coupling` field in `/plan-schema-audit`'s schema (suggested to skill-manager as S-0036), so the audit files a backfill job rather than a reviewer having to remember.

## 6. What this is NOT
- Not a mesh. Not "every loop feeds every other" (the GPT closed-circuit reading, declined by the founder 2026-09-04).
- Not more thinking. Success is not more cycles; it is that a deliberation, a commitment, or a Witness break can be traced to a named coordinate in another loop's tuple at the moment it happened.
- Not prose. A coordinate never becomes a sentence in a prompt where the number will do (the one-space trap, cognitive_geometry §4).
- Not deletion. The four unread climate dims stay until ride evidence says they carry nothing.

## 7. Go / no-go (D-0149)
**Go** = adopt §1 as a standing design law, run Phase 0 now, and require §5 of every future loop-touching plan. **No-go** = keep the individual repair jobs (they are real bugs regardless) but do not bind future designs. Defeater on a GO: two weeks of ride log in which no dosed read can be shown to have changed a downstream trajectory, or rumination caps hit on 3+ days, or the Witness kill criteria (metaphor leak) worsen after buckets — any of which reopens the law rather than the phase.

## Pointers
Findings F-0799..F-0812, F-2015 (§4b) · thoughts T-0044, T-0045, T-0068 (§4b) · decisions D-0148, D-0149 · jobs J-0576..J-0585 · memory: project_nascence_dosed_coupling.md, project_nascence_transit_map.md (dosing rule), project_nascence_identity_is_connections.md (in-between)

