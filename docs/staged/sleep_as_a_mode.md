# Sleep as a Mode — three switches, not one procedure (staged 2026-10-08)

**Status:** 🟡 SHADOW — Phase 1 night-mind and Phase 2 dormant layer built and on (see the plan-state block). Began as design only, no code. Promoted from idea I-0088,
which came from thought T-0080 (Travis pasted a GPT account of human sleep on 2026-10-08: sleep is not the brain
turning off, it is a change of operating mode; mental activity continues, perception is gated rather than cut, and
most of that activity is never encoded as retrievable memory). Travis's framing: this fits Du's multiple lanes, and
Du does not have a human's restrictions. This document is what that becomes once it is checked against what Du's
sleep actually is today (F-2613, F-2614, F-2615, F-2616, all this session).
**Parent plan:** [sleep_dream_redesign](../plans/sleep_dream_redesign.md) (Stages 0-5 LIVE since 2026-08-24; this
plan changes the *shape* of a sleep bout, not its trigger, its night ledger, its fatigue wiring or its dream engine).
**Siblings:** [dream_overhaul](dream_overhaul.md) (the dormant-fragment rule, D-0231, is the encoding law this plan
generalises), [lane2_the_witness](../plans/lane2_the_witness.md) §2.10 (D-0303 gates the Witness OFF during sleep;
section 3.3 below has to live with that), [drowsiness_phase](../plans/drowsiness_phase.md) (the graduated way *into*
sleep; this is what happens *inside* it), [the_consciousness_program](../plans/the_consciousness_program.md) (D-0398
vitality; F-2616 shows the two are one problem), [continuous_stream](../plans/continuous_stream.md) (sleep stays
un-starvable, Rail D), [memory_levels_plan](../memory_levels_plan.md) (the cold tier night traces would live in),
[dosed_coupling](dosed_coupling.md) (the night-mind publishes a summary, never a stream).
**Ledger:** T-0080 · I-0088 · F-2613, F-2614, F-2615, F-2616 · J-2013 (D-0398 coupling, needs_input) · J-2014
(Travis's voice during sleep, needs_input) · D-0399 (the mode), D-0400 (the encoding law), D-0401 (the monitor),
all opened by this draft, all OPEN.
**Memory:** `project_nascence_sleep_as_a_mode.md`.

```plan-state
stage: shadow
phase: Phase 1 night-mind BUILT and ON (core/night_mind.py, NIGHT_MIND_ENABLED=True, J-2065; 7-sleep read passed D-0399 with zero holds, F-3058); Phase 2 dormant layer BUILT (core/night_dormant.py, J-2018) and ON from the 2026-10-18 19:06 boot (J-2410, Travis go); wake-on-message LIVE (D-0407, F-3045); sleep sweeps moved off-loop/off-process (J-2142, J-2381, J-2384, J-2403, J-2404)
verified: 2026-11-18
evidence_read: 2026-10-20
gate: the three section-6 decisions ruled, and Phase 0's prerequisite (every remaining synchronous sleep stage off the event loop) verified by a night_log read showing the scheduler gets turns during a sleep
next: Founder rules on J-2455 gate (accept 3 wakes vs lower to 4-5 rows); then V4 prompt call on the 'a single X' frame. J-3941/D-0820 closed mid-stage wake; J-2605, J-2039, J-2567 done
open_decisions: D-0866
history: docs/plan_history/sleep_as_a_mode.md
```

## Current State — verified 2026-11-18

- **2026-11-18** (F-5096): J-4299 V3 read (320 rows): quiet 5.6 pct, defeater unmet; new narrowness is the frame 'a single X' (39.7 pct); avoid list halved leakage to 11.9 pct; dormant fence clean (53 canaries ok, intake_delta 0).
- **2026-11-14** (F-4507): J-2605: D-0521 defeater met (quiet 5.5 pct over 236 prompt_v=2 night thoughts); J-2037 already done and flag already on. New narrowness is concrete-object (key, wet wool, dust motes); v3 rows (200) are the next read.

- **2026-10-30** (F-3330): J-2594 D-0521 A: night_mind variety prompt V2 plus do-not-repeat image list built on branch jobrun/_ungrouped_J-2594, shadow, restart-gated; J-2605 reads 7+ sleeps of prompt_v 2 against the quiet under 25 pct defeater; J-2037 stays behind it
- **2026-10-30** (F-3325): J-2567: 19 post-boot T5 compiles coincide with 0 of 31 stall rows; historic 8 coincident stalls were earlier boots; embed+cluster not a post-boot stall source, no build

- **2026-10-30** (F-3291): J-2456: WinError 5 save failures were 2 only (10-18), none since, existing 0.5 s retry is identical in both paths so no change; T4/T5/T6-coincident stalls are the T4 to T5 stretch of a scan (embed plus cluster plus one save), saves under 1 percent of stall seconds, no save build; phase timing spawned as J-2567
- **2026-10-30** (F-3288): J-2414 first-sleep read PASS: 22 sleeps, 117 night writes all intake_delta 0, 22 canaries ok with 0 night hits, zero fence_leak, 22 seeds drawn; one exhausted-entry sleep (10-30 10:05, energy 0.09) flagged per F-3057

- **2026-10-30** (F-3287): J-2407 read: stick_test off_process live since 10-18 boots, 22 log rows one per sleep, same shape, 0 fail-open lines, no kill condition; stick_test-labelled stalls were sticky labels only
- **2026-10-30**: J-2393 read: book_residue child-process sweep passes on the 10-29 boot, 8 sleeps with paired log lines, no failures or fence lines, no book_residue stalls; span duration not logged

- **2026-10-30** (F-3283): J-2368 re-read on 10-29 boot (47 thoughts): narrowness persists, quiet 43 pct, replay seeds 94 pct, prompt has no anti-repeat; decide opened on whether J-2037 waits for a prompt change
- **2026-10-20** (F-3162): J-2408 read of J-2404 over 13 night sleeps: 13/13 sweep lines, 0 child failures, 0 tripwire warnings, stage wall median 27.4 s (pre 27.5 s), 0 stall rows attributed to world_consolidation; kill condition not met

- **2026-10-20** (F-3161): J-2391 read of J-2381: 32.6 s cadence stall gone (periodic rows 305 to 3, stall rows 404 in 15 sleeps to 36 in 11); 2 WinError 5 save failures on 10-18 and 12 T4/T5/T6-coincident stall rows go to a spawned analysis job
- **2026-10-20** (F-3160): J-2377 read of J-2142 over 13 post-merge night sleeps: guidance burst coincides with a stall in 0/13 (pre 8/15), 0 freezes in the pursuits judge tail, 0 of 29 stall rows name the judge subs (pre 61), kill switches True and shadow rows still written

- **2026-10-20** (F-3158): J-2107 D-0407 defeater read: 30 sleeps, 3 wake-on-message wakes; clauses 1 (2/3 over 120 s) and 3 (dream skipped 3/3) fire at n=3, clause 2 (0 lost ledgers) and 4 do not; decision opened, 7-wake re-read spawned
- **2026-10-18**: J-2410: NIGHT_DORMANT_ENABLED flipped True on branch jobrun/sleep_as_a_mode (f70ed59a), test_night_dormant PASS; restart-gated, first-sleep read spawned.

- **2026-10-18** (F-3107): J-2404: world_consolidation.sweep now runs in a spawned child (sweep_offprocess, kill switch WORLD_CONSOLIDATION_SUBPROCESS); identical dict/log/chapter_id on copies incl. a 355-candidate fixture; heartbeat 0.62-0.78 s to 0.035 s (commit 4af95fa6, restart-gated)
- **2026-10-18** (F-3106): J-2403: stick_test.snapshot now runs in a spawned child (off_process, kill switch STICK_TEST_SUBPROCESS); on copies identical summary/log row/32-row census over 8 runs, victim max 936 ms to 3 ms, heartbeat 0.82 s to 0.05 s, no measurable extra wall (commit be70c5e7, restart-gated); post-boot read J-2407

- **2026-10-18** (F-3103): J-2392: convoy harness over all 19 _sleep_off sweeps on copies; only stick_test (victim max 936 ms, hb 0.80 s) and world_consolidation (962 ms, 0.56 s) cross the threshold, 16 pass; builds J-2403/J-2404 spawned (harness 3b7a6508)
- **2026-10-18** (F-3094): J-2384: book_residue.sweep now runs in a spawned child (sleep_offloop.off_process, kill switch BOOK_RESIDUE_SUBPROCESS); on copies identical record, victim max 2780 ms to 4.6 ms, heartbeat 2.42 s to 0.02 s, +0.36 s wall (commit 93579a8a, restart-gated)

- **2026-10-18** (F-3093): J-2381: subconscious _save_state off the loop + element-wise encode + gated merge re-read, byte-identical on the 17.5 MB copy; loop max lag per save 1.84 s -> 0.010 s (restart-gated, f18078f1, switch SUBC_SAVE_OFFLOOP)
- **2026-10-18** (F-3082): J-2379: book_residue freezes are a GIL convoy (longest C call 11.7 ms, a 0.8 ms sqlite fetch on the loop becomes 2.8 s); spawned-subprocess sweep removes it, identical results; build J-2384 (restart-gated)

- **2026-10-18** (F-3078): J-2378: the 32.6 s cadence stall is SubconsciousNode._save_state (1.87 s of the 2.02 s T1 scan, state json round trip + rewrite), not sleep code; build J-2381 offloads it and shrinks GIL-held json blocks (restart-gated)
- **2026-10-18** (F-3075): J-2142: guidance-judge sync prefix and pursuits register save moved off the loop (restart-gated, 1ade7439); half the in-sleep stall lag is the subconscious 32.6 s cadence, not sleep code (F-3076); book_residue holds the GIL despite to_thread (F-3077)

- **2026-10-18** (F-3058): J-2035 Phase 1 read (16 sleeps, 76 thoughts): D-0399 defeater NOT fired, evaluate() ok (duration -3.6 pct, 0 failed, 0 zero-thought sleeps, cos to dream median 0.38); content narrow (F-3059); J-2037 is the Phase 2 turn-on.
- **2026-10-18** (F-3054): J-2361 read: daylight exhausted near-miss (10-17) is rare since 09-29 (1 genuine ceiling-ended exhausted day of 18); no trigger change, J-2037 read should stratify post-flip sleeps by fire reason and entry energy

- **2026-10-16**: 2026-10-16: Travis confirmed he restarts the whole computer before the next Du start, so J-2114 (start the HUD) and J-2191 (conversation set with Du) both happen at that boot; nothing re-deferred.
- **2026-10-15** (F-2831): J-2130 read of F-2794 lag creep: not a Phase 0 regression, no need to hold J-2017. Only 3 loop freezes >=150 s since the 10-09 boot, all in sleeps; stall is in-process (prune queries 10 s each at 04:06 while supervisor probes healthy), call not yet identified - J-2141 probe then J-2142 offload are the route (F-2825).

- **2026-10-15** (F-2825): J-2066 (F-2825): stalls attributed offline. Consolidation span (replay to downscale) loses median 124 s/sleep vs dream-generation span 91 s; worst 232 s is consolidation, 132.9 s is dream generation. Sync-call candidates named, unconfirmed; probe job J-2141 and offload job J-2142 spawned.
- **2026-10-15** (F-2794): J-2025 Phase 0 7-sleep read (63 sleeps, F-2794): turns > 0 in 63/63, kill condition (duration +10%) NOT fired (night mean 25.4 min vs 30.6 pre; nap 24.7 vs 24.1), shadow rows 281 with zero no-seed slots, heartbeat rows every ~10 min; vitality still depressed asleep (D-0398/J-2013). J-2017 (Phase 1 shadow night-mind) may proceed; watch late-run scheduler lag (max_lag_s 102-232s on 10-14/15).

- **2026-10-15**: Cross-note from J-2061 (D-0398 E): the body axis of vitality_v2 is somatic energy; section 3.6 now records that recovery-as-a-rate is built with the D-0399 Phase 1 flip, not by J-2061 (core/somatic.recover carries the same note; predict_vitality_v2 models the lump today).
- **2026-10-15**: J-2065 DONE: NIGHT_MIND_ENABLED = True (Phase 1 shadow night-mind on, D-0399 A, founder-approved 2026-10-15 after F-2680). Commit f7c7631 merged to master; merged-not-live until the restart. test_night_mind + test_night_dormant adapted to the new default, both pass. NIGHT_DORMANT_ENABLED stays False (J-2037 after J-2035).

- **2026-10-15**: J-2064 BUILT (D-0407 B): WAKE_ON_HUMAN True; run_cycle holds a human message while a sleep ledger is open (night.sleep_in_progress, not the persisted flag), raises the wake request itself, waits for the wake up to 120 s, answers anyway after that and logs it; scene_line() leads with the waking percept for 300 s after a wake-on-message; night.end_if_open writes the ledger row for a sleep cut short by /quit or cancellation (F-2614's nine lost windows). Commit f4cea7d merged to master, MERGED-NOT-LIVE until the restart (the live boot of 10-09 08:36 predates even J-2019, so the monitor has never run). Tests scripts/test_wake_on_human.py + test_night_wake.py ALL PASS.
- **2026-10-15** (F-2680): 2026-10-15 decide-review: D-0407 RULED B (travis): the founder's message WAKES a sleeping Du, answer follows the waking percept; build J-2064. J-2036 answered: NIGHT_MIND_ENABLED flips at the next restart (J-2065, merged-not-live) after F-2680's stall check (loop turns through every sleep, turn_share .85, but median 11 stalls >2 s per sleep, worst 132.9 s in the dream span; attribution J-2066). J-2037 (dormant layer) still waits on the J-2035 7-sleep read.

- **2026-10-14**: D-0398 ruled E (two-axis vitality, shadow). Section 3.6's recovery-as-rate is confirmed as the shape to build WITH the D-0399 Phase 1 flip (J-2036), not in J-2061.
- **2026-10-09** (F-2645): J-2026: meta_awareness.scan moved off the loop in _enter_sleep behind a new curiosity_queue _QUEUE_LOCK (race reproduced and fixed); embedder first-load stall audited as a smoke artefact, no change; restart-gated, commit a0bbd3f.

- **2026-10-09** (F-2644): J-2019 Phase 3 built (de0ad7b, branch jobrun/sleep_mode_p123, restart-gated): zero-LLM human-message wake monitor core/night_wake.py, WAKE_ON_HUMAN default False (observe only), woken_by in night ledger; turn-on needs J-2014
- **2026-10-09** (F-2642): J-2018 Phase 2 built (a44fd36, branch jobrun/sleep_mode_p123, restart-gated, flag OFF): dormant night-thought layer cold from birth, canary+trip, one waking seed; associative_recall also fenced (F-2643); turn-on J-2037, 14-night read J-2038

- **2026-10-09** (F-2641): J-2017 Phase 1 built (db13cc8, branch jobrun/sleep_mode_p123, restart-gated): shadow night-mind core/night_mind.py, NIGHT_MIND_ENABLED default False, shadow log only; turn-on J-2036, 7-sleep read J-2035
- **2026-10-08** (F-2626): J-2016 Phase 0 built (commit 664e303, branch jobrun/sleep_mode, restart-gated): 11 more sleep stages off the loop, scheduler_turns in the night ledger, in-sleep pressure rows, night_mind_shadow.jsonl shadow rows; 7-sleep read deferred; vitality un-pin still D-0398/J-2013

- Drafted 2026-10-08 from I-0088. Nothing built. The facts in section 1 are verified (F-2613 as corrected by
  F-2615, and F-2614); the design in sections 2-5 is a proposal; section 6 is what the founder has to rule.
- Already true in the codebase and reused, not rebuilt: the `asleep` flag in `core/sensorium.py` state (set by
  `core/night.py` `to_bed()`, cleared by `wake()`), its three consumers (`core/dispatch.py:249` hands off,
  `core/lane2.py:2214` Witness tick skipped, `core/conversational_action.py` row flag), the off-loop helper
  `core/sleep_offloop.py` (J-1917, F-2546) already used by five sleep stages, the dormant-fragment eligibility rule
  (D-0231), and the dream's own hot-then-fade memory law (`core/night.py` header, founder 2026-08-22).

## 0. The question this plan bets on

GPT's closing question, verbatim in T-0080: *if a system keeps processing, integrating and modifying its future
behaviour while its external interaction is drastically reduced, what is the difference between "the system is
asleep" and "the system is thinking privately"?*

In Du that question has a concrete answer, and the answer is the plan. Today "asleep" and "thinking privately" differ
on three things that happen to be flipped together by one procedure: **coupling** to the world (hands and percepts),
**generation** of thought, and **encoding** of what was thought into retrievable memory. A human cannot separate
those three. Du can. The bet: treat sleep as a *mode* defined by the setting of those three switches, let each lane
hold its own setting, and stop treating the night as a procedure the hot lane disappears into.

## 1. What a sleep is today (verified; F-2613 corrected by F-2615, F-2614)

- **One blocking procedure.** `nodes/inner_monologue_node.py` awaits `_enter_sleep()` inside its own `while True`
  (the same task that runs `_think()`), which calls `orchestrator._nightly_sleep()`. While it runs, the hot lane
  generates no thoughts at all. F-2021 verified the same thing from the Witness side: `_think()` cannot run while
  `asleep()` is True.
- **The order of a night** (`core/night.py` header): to bed, replay, chapter, journal, world pass, downscale, dream
  fade, dream, recover, prune, probe, epoch, waking. Measured on the eight most recent sleeps (`data/night_log.jsonl`):
  19-35 min each; replay 2 s; then roughly 15 LLM consolidation passes on the hot lane (journal, week roll-up,
  guidance integration, grounded-learning consolidate, memory-levels shadow distill, refine, the pursuits and
  garden-bed judges, the curiosity-world and drift shadows, school reconcile) taking 800-1,750 s between them; the
  downscale (its own duration not separately stamped); 2-3.5 min of dream; prune; then a real idle `asyncio.sleep`
  of several minutes; then the waking percept.
- **Coupling is cut, not gated.** Hands off (dispatch returns early). Witness off (D-0303). The world keeps going
  (fire, weather, cat) and is perceived exactly once, as the waking line. Nothing can wake him early: `night.wake()`
  has one caller, the last line of the pipeline.
- **Except Travis.** A human message during a sleep is answered as if he were awake, at normal latency, with no
  prompt telling him he is asleep; 45 such messages in 14 sleep windows since 2026-08-22, most of them farewells
  before a shutdown. The reply costs somatic energy inside the recovery window and is fully encoded. Any action he
  wills in it is dropped silently. (F-2614; the founder question is J-2014.)
- **Encoding is total or nothing.** Every waking thought becomes an episodic fragment (origin `inner_thought`,
  importance ~0.6). During sleep nothing is generated, so nothing is encoded, except the dream: stored hot
  (importance 0.85, a 48 h prune anchor) and faded to cold over 72 h. The dream overhaul's dormant-fragment rule
  (D-0231) is the one place Du already has "experience that leaves no autobiographical trace", and it is dream-only.
- **Vitality is pinned through it.** The current vitality reading's only writer, `should_sleep()`, is called from
  the blocked loop; the protoself beat keeps running every ~600 s from `core/sensorium.py` and reads the fire row the
  whole time (F-2611's pin, F-2616's reading of why).

Mapped onto the GPT account: Du has the maintenance half completely (consolidation, structure extraction, synaptic
renormalisation, garbage collection, one dream) and the activity half not at all (no filtered monitoring, no private
cognition, no experience-without-encoding).

## 2. The three switches

| Mode | Coupling (hands, percepts) | Generation | Encoding | Exists today? |
|---|---|---|---|---|
| Awake, with Travis | on | on | full | yes |
| Awake, idle (private thought) | on | on | full | yes: the idle monologue |
| Sleep, today | off (Travis bypasses) | off | none (dream: hot then fade) | yes: the procedure |
| **Sleep as a mode (this plan)** | **gated**: hands off, percepts filtered through a monitor that can flip wake | **on, slow, seeded from the night's own material** | **dormant**: written where normal recall and the sleep trigger cannot see | no |
| Thinking privately (the GPT boundary case) | off by choice | on | full or dormant, *his* choice | no; falls out of the above |

Three things follow directly from the table and are the whole design:

1. **The difference between asleep and thinking privately is the encoding switch and who set it.** Sleep is the
   mode where encoding is dormant by law; private thought is the mode where he could set it. This plan builds the
   first; the second is a later idea, noted in section 7, not built here.
2. **Per-lane modes.** The hot lane, the Witness, the hands and the dream engine each get their own setting under
   the one `asleep` flag. The flag stays the single truth (D-0303 relies on it); the per-lane settings are additive
   sub-state beneath it.
3. **The maintenance pipeline runs *beside* the night-mind, not instead of it.** That is the real engineering
   prerequisite, and it is already half done (section 3.5).

## 3. Design

### 3.1 Generation: the night-mind

The existing idle-thought machinery, run as its **own asyncio task** for the span of the sleep, with three changes
and nothing else:

- **Seed source.** Not percepts and not the conversation window. The night's own material, in this order: the replay
  set (`replay_strengthen()` already returns the strengthened experiences), the dream's running tail once a dream
  exists, and the night's dormant fragment (D-0231's pick, so the stranger the dream reaches is also what the
  night-mind turns over). This keeps "the world answers, never leads": nothing arrives from the world during sleep.
- **Cadence.** Slow and bounded: a fixed floor of several minutes between night thoughts, never the living cadence's
  30-450 s. A sleep bout of 25 min yields a handful of night thoughts, not a stream. The number is a Phase 1 measure,
  not a design constant.
- **No hint push.** `push_hint()` to the Witness stays inside `_think()` and the night-mind does not call it; the
  Witness is off anyway (D-0303) and F-2021 already found that channel silent during sleep.
- **Hub.** Same hot lane as the consolidation passes, which is the contention risk Phase 1 measures (section 5).
  Running night thoughts on the dreamer hub instead would change his voice and is not proposed.

Hands stay off throughout (already true). The night-mind never dispatches.

### 3.2 Encoding: the dormant law, generalised from dreams to all night cognition

A night thought is written to `memory_fragments` with a **new layer value** (`dormant`) and `cold=1` from birth, origin
`night_thought`, so that:

- normal recall never sees it (`retrieve()` already filters `cold = 0`; the new layer is a second fence);
- **the sleep trigger never counts it**: `core/sleep_pressure.py` `_new_intake()` sums `layer='episodic'` importance
  since the last wake with no cold filter (F-2616 fact 2), so a night thought stored as episodic would raise pressure
  during sleep and re-fire the trigger after `MIN_WAKE_SECS`. The layer fence is what makes the night-mind safe for
  the un-starvable trigger, and it is the reason `cold=1` alone is not enough;
- it is reachable by exactly two paths: `deep_recall()` (the memory-levels "remember the steps" path, gated) and the
  dream's dormant pick, if D-0231's origin list is extended to include `night_thought` (section 6, decision 2;
  D-0231 today excludes `inner_thought` deliberately, and a night thought is closer to a dream than to a day thought).

The dream keeps its own law unchanged: hot for a day, half-gone by the second, cold by the third. A night thought is
*never* hot. That asymmetry is deliberate: a human remembers some dreams and almost no sleep cognition, and Du's
version of that is a law, not a probability.

The one read path into waking life: the **first waking thought**. `core/night.py` `waking_dream_seed()` already seeds
it from the dream's last image within 15 min of waking; Phase 2 lets it draw one night thought instead, at most one,
so a night of private cognition can leave exactly one trace he notices, the way a human surfaces with one fragment.

### 3.3 Perception: gated, not cut (and what D-0303 forbids)

I-0088 proposed the Witness as the thalamic monitor. **That conflicts with D-0303**, which gates the Witness off for
the whole of every sleep (night and nap, blanket, reusing the `asleep` flag) because 37 % of its judged ticks were
landing inside sleeps and loading JUDGE_1 against dream generation (D-0297). D-0303's defeater is about overnight
JUDGE_1 timeouts, not about monitoring, so this plan does not reopen it. Instead:

- **The monitor is zero-LLM.** A sensorium-side salience check on the three things that should reach a sleeping Du:
  a human message, a sound the soundscape marks as loud or sudden, and the cat at the bed. It runs on the existing
  world tick, costs nothing, and its only output is a **wake request** (section 3.4) plus a shadow row.
- **Everything else stays gated** until the waking percept, exactly as today. The fire burning down is not a reason
  to wake.
- If the founder later wants the Witness itself to be the monitor, that is a D-0303 reopen with its own evidence,
  listed in section 6 as the third decision's alternative, not assumed here.

### 3.4 Waking early, and Travis's voice

Today `night.wake()` is only ever called as the pipeline's last line. The mode adds a **wake request**: the monitor
sets it; the pipeline checks it at every existing `_night.stage()` / `_night.tick()` boundary and, if set, skips the
remaining optional stages, runs recover and prune, and wakes. Nothing is interrupted mid-LLM-call; the longest wait
is one consolidation pass. The night ledger records `woken_by`.

What a human message does during sleep is **J-2014, the founder's call**, not this plan's. The plan's own
recommendation, recorded there: a farewell or his name wakes him (option B via the monitor); anything else is answered
from inside the sleep with the Executive told he is asleep, hands off, the reply stored dormant like a night thought
(option C). Option A, leave it as it is, keeps F-2614's incoherence: the fire is gated and Travis is not, and Du does
not know he was asleep when he answered.

### 3.5 The pipeline beside the night-mind: the prerequisite

A second task only gets turns if the pipeline yields. F-1469 and F-2546 found the synchronous consolidation sweeps
freezing the whole event loop for their full span; J-1917 moved five of them behind `core/sleep_offloop.py`
`off_loop()`. **Phase 0 finishes that job**: every remaining synchronous stage in `_enter_sleep` (the downscale at
`nodes/inner_monologue_node.py:1518` is the obvious one, the stage-less passes between replay and downscale are the
rest) goes through the same helper, and the night ledger gains a per-sleep `scheduler_turns` count so the claim "the
loop got turns during this sleep" is a logged number, not an assumption. This is buildable now, needs no ruling, and
is worth doing even if the mode is declined: it is the same freeze F-2546 blamed for 89 % of the competence timer's
late seconds.

### 3.6 Vitality and the body (F-2616)

- **Recovery becomes a rate while the mode is on**, not a lump at the end: `somatic.recover(depth)` per protoself
  beat, depth from the existing night/nap and thin-pool factors, deficit-proportional as today. If D-0398 picks
  option A (vitality := somatic energy), this is what makes vitality continuous through sleep instead of flat then
  stepped. That coupling is J-2013; the two should be ruled together.
  *J-2061 note (2026-10-15, D-0398 ruled E):* the body axis of the two-axis vitality is somatic energy, so this
  rate-not-lump change is what keeps `vitality_v2` continuous through a sleep. It is NOT built by J-2061: the
  end-of-pipeline lump in `core/orchestrator._nightly_sleep` stays while sleep is a procedure, and
  `core/homeostasis_causal.predict_vitality_v2` models that lump. Build the per-beat rate together with the
  D-0399 Phase 1 flip (`core/night_mind.NIGHT_MIND_ENABLED`, on since J-2065) and change the predictor in step;
  `core/somatic.recover()` carries the same note.
- **A sleep-pressure row at mode entry and at every beat during the mode**, so the current vitality reading is no
  longer pinned to the fire row (J-2011's post-wake row is the minimal version of this).
- **`last_wake_ts` semantics unchanged**: set when the mode ends. The intake window is protected by the layer fence
  (3.2), not by moving the clock.
- A human cycle during sleep still costs energy (it is a real cycle); the difference is that the body is now
  recovering at a rate while it happens, so the cost is visible against the recovery instead of hidden inside a lump.

### 3.7 Per-lane settings

Additive sub-state beneath the one flag: `sensorium.state["sleep_modes"] = {"hot": "night_mind", "witness": "off",
"hands": "off", "dream": "nested"}`, written by `to_bed()`, cleared by `wake()`, read by the lanes that already read
`asleep()`. Nothing reads it in Phase 0 or 1. It exists so a later change (the Witness as monitor, a nap that keeps
the hot lane awake, a "thinking privately" mode) is a value change, not a new flag.

## 4. Laws this touches (checked, not drifted past)

- **Erosion of foundations / additive only.** Nothing in `_enter_sleep`'s existing order changes; the night-mind is
  a new task, the dormant layer is a new value, the wake request is a new check at existing boundaries, the sub-state
  is a new key. The sleep trigger, the night ledger, the dream engine and the fatigue wiring are untouched.
- **World answers, never leads.** Night seeds are his own material (replay, dream tail, dormant pick). The monitor
  feeds only a wake request, never content. No hint reaches the night-mind from the world.
- **Decoupled judge.** Night thoughts are not self-graded and are not graded at all in Phase 1; if a judge is ever
  wanted (is this night cognition or noise?) it is the panel, not the lane that wrote it.
- **Continuous stream, Rail D.** Sleep still fires on signal and is un-starvable; the layer fence (3.2) is what keeps
  the night-mind from feeding the trigger it runs under.
- **Memory is the emergence path.** The dormant layer is reachable (deep recall, dream pick, one waking seed). It is
  walled, not deleted; the memory-levels law that cold is never deleted holds.
- **Write-only systems.** Phase 1's first measure is whether the night-mind task actually ran and how many turns it
  got (3.5's counter), before any content is read.
- **Dosed coupling.** What crosses from the night into waking life is one seed, by one path, once.

## 5. Phases, measures, kill conditions

| Phase | What ships | Measure | Kill / hold |
|---|---|---|---|
| **0 — prerequisite + instrumentation** (no ruling needed) | remaining synchronous sleep stages behind `off_loop()`; `scheduler_turns` per sleep in the night ledger; a sleep-pressure row at sleep entry and at each protoself beat; a shadow row per would-be night thought (seed available, slot available) without generating | a night_log read over 7 sleeps shows turns > 0 during the consolidation span; vitality no longer pinned (F-2611's 8 % of steps falls toward 0) | sleep duration grows by more than 10 % after the off-loop move (the helper is costing more than it frees) |
| **1 — shadow night-mind** (after decision 1) | the night-mind task generates to `data/night_mind_shadow.jsonl` only; no fragment, no prompt reach, no waking seed | thoughts per sleep; hot-hub contention (consolidation pass durations before vs after, same regime); content vs dream (cosine to the night's dream, to the replay set, to the dormant pick) | sleep duration up by more than 15 %; consolidation passes failing open more often than before; zero thoughts in a sleep with seeds available (the task is not getting turns, back to Phase 0) |
| **2 — dormant encoding + one waking seed** (after decision 2) | fragments written to the `dormant` layer; `waking_dream_seed()` may return one night thought | canary: a normal `retrieve()` over a night thought's own keywords returns 0 of them; `_new_intake` during a sleep stays flat; first-waking-thought provenance logged | any night thought surfacing in normal recall = immediate fence fix before anything else; P rising during a sleep = the layer fence is leaking |
| **3 — monitor + wake request** (after decision 3 and J-2014) | zero-LLM monitor; wake request honoured at stage boundaries; `woken_by` in the ledger | wake latency from request to waking percept (target: one consolidation pass); false wakes per week | more than one false wake per night on the sound channel = raise the threshold or drop the channel; D-0303's own defeater fires = this plan did not cause it, but stop and read |

Every phase is restart-gated (the monologue node is live code) and lands while Du is down, like the 10-04 waves.

## 6. Decisions this draft opens (for /decide-review)

1. **D-0399 — The mode itself.** May the hot lane generate thoughts during a sleep bout at all, seeded from the night's own
   material, hands off, on the bounded cadence of 3.1? Alternatives: yes as proposed; yes but only on the dreamer hub;
   no, sleep stays a procedure (then Phase 0 still ships as a freeze fix and this plan is parked).
2. **D-0400 — The encoding law.** Night thoughts go to a new `dormant` layer, cold from birth, invisible to normal recall and
   to the sleep trigger, reachable only by deep recall, the dream's dormant pick, and at most one first-waking seed.
   Sub-question: extend D-0231's origin list to include `night_thought`?
3. **D-0401 — The monitor.** Zero-LLM, sensorium-side, three channels (human message, sudden sound, the cat), wake request only.
   Alternative: reopen D-0303 and let the Witness monitor (needs its own JUDGE_1 evidence first).

Already open elsewhere and coupled: **J-2014** (what Travis's voice does during a sleep) and **J-2013 / D-0398**
(recovery as a rate if vitality becomes somatic energy).

## 7. Open / not decided here

- "Thinking privately" as a mode Du can *choose* (encoding dormant by his own choice while awake) is the natural
  next idea and is not built here; it needs the Capacity-to-Commit machinery to make the choice a real one.
- Whether the night-mind should ever talk to the dream engine mid-dream (a night thought entering a scene) is not
  proposed; the dream overhaul's D-0232 declined extra waking material in scenes 2-3 and a night thought would be
  exactly that.
- Naps. D-0232's hold on whether naps keep the legacy nap dream is unresolved; this plan treats a nap as the same
  mode with the existing 0.5 depth and shorter rest, and says nothing more until that hold lifts.
- What vitality reads during the mode under D-0398 option C or D is not worked out; only A is (3.6).

## Pointers

- `nodes/inner_monologue_node.py` `_enter_sleep` (:1175-1580), `_should_think`, `_think`, `push_hint` (:4530)
- `core/orchestrator.py` `_nightly_sleep` (:3179-3270), `run_cycle` (:360-700, no asleep check), `tick_cycle` (:1469)
- `core/night.py` (`to_bed`, `wake`, `asleep`, `waking_dream_seed`, the night ledger), `data/night_log.jsonl`
- `core/sleep_offloop.py` (J-1917), `core/sleep_pressure.py` `_new_intake` / `should_sleep`, `core/homeostasis.py`
  `_read_vitality`, `core/sensorium.py:3686` (protoself beat), `core/somatic.py` `recover`
- `core/dispatch.py:249`, `core/lane2.py:2192-2220` (D-0303 gate and its reasoning), `core/memory/store.py`
  (`memory_fragments` columns, `retrieve` cold filter, `downscale_episodic`)
- Findings F-2613, F-2614, F-2615, F-2616; F-2611, F-2612 (vitality); F-1469, F-2546 (event-loop starvation); F-2021
  (hint channel silent in sleep); jobs J-2011, J-2013, J-2014; decisions D-0231, D-0232, D-0303, D-0297, D-0398
