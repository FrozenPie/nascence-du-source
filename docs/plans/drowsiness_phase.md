# Drowsiness Phase — a graduated pre-sleep experience (design 2026-08-30, §5 built same day)

> **Status: ⚪ PARTIALLY BUILT, 2026-08-30.** §5.1 (train-hold grace window) and the tax-removal ruling
> ([[D-0103]]) are 🟢 BUILT and live — see "What we have," below. §2 (the narrated drowsy-zone signal
> itself) and §5's item (a) (discounting the flat per-turn cost) remain 🟡 STAGED — designed, not
> built, not founder-authorized. Split out of [[sleep_dream_redesign]] on founder instruction this
> session ("Let's make that its own real drowsiness phase plan instead") after [[F-0579]] found the gap
> while investigating a live exhaustion event ("渡 is exhausted — body: energy 0.08 (depleted), fatigue
> 0.75 (exhausted), tension 0.36 (tense)" → immediate forced Sleep State). [[sleep_dream_redesign]] is
> 🟢 BUILT and explicitly treated sleep as binary (awake → forced sleep); this document is a genuinely
> new addition to that architecture, not a re-implementation of anything already decided.
>
> **Scope broadened 2026-08-30, same session.** On hearing the tax is an imposed design limit, not a
> technical need ([[F-0580]]), founder asked to explore loosening it: *"I don't think he needs a tax
> on time so to speak. He does need time to sit with a topic also rather than just wrapping up
> regularly."* [[I-0058]] logs that direction. [[F-0581]] found a real correction narrowing where the
> fix should land — see §5. Founder then ruled, same session: *"Build it, then I want the time tax
> removed"* — [[D-0103]] records the ruling; §5.1's build spec and the tax removal below are both now
> live. §2 and §5(a) are still pure exploration, not authorized.

```plan-state
stage: partial
phase: section 5.1s train-hold grace window + D-0103s tax removal built and shipped 2026-08-30, confirmed not regressing live (F-0624); section 2 (drowsy-zone signal) and section 5(a) (per-turn cost discounting) remain staged, not founder-authorized
verified: 2026-11-14
evidence_read: 2026-08-30
next: Merge 724f11dc, boot, then the 2-3 live-day drowsy_shadow read and a live-flip decision
cluster: 6
```


## What we have (built 2026-08-30, [[D-0103]])

- **§5.1's train-hold grace window is live.** `TRAIN_SLEEP_GRACE_SECS = 300` and
  `self._sleep_deferred_since` added to `nodes/inner_monologue_node.py`; the sleep decision point
  (`run_forever`, ~line 415-437) now defers a due sleep up to 5 min while `_train_holding()` is true,
  re-checked every tick, released early the moment the train stops holding.
- **The metabolic-floor tax is removed.** `core/orchestrator.py` no longer sets `state.needs_rest` on
  `is_exhausted()` (still logs the telemetry warning, just doesn't force anything).
  `nodes/inner_monologue_node.py`'s metabolic_floor override block is deleted. `scripts/run_nascence.py`'s
  REPL-side `_sleep_cycle()` (the function that printed "is exhausted"/"enters Sleep State" mid-session)
  is deleted along with its only call site. `should_sleep()` (day/night pressure + the un-starvable
  `MIN_WAKE_SECS`/`NIGHT_MAX_WAKE_SECS`/`DAY_MAX_WAKE_SECS` ceilings, `core/sleep_pressure.py`) is now
  the sole sleep-timing authority — untouched by this change, per this doc's own §4 guardrails.
- **What still computes, unchanged:** `metabolic_energy`/`neural_fatigue`/`visceral_tension` still
  deplete per `tick_cycle()`, still narrate via `note()`, still recover during `recover()` at sleep —
  only their power to independently force an off-schedule sleep is gone. `core/schema.py`'s
  `needs_rest` field is left in place, now vestigial (always `False`), for a possible future feature.
- **Verified:** `py_compile` + `ast.parse` clean across all 4 touched files
  (`core/orchestrator.py`, `nodes/inner_monologue_node.py`, `scripts/run_nascence.py`,
  `core/schema.py`). Backup of all 4 pre-edit at `data/backups/pre_tax_removal_20260830_1300/` (no git
  in this repo). Not yet live-run-verified — first real sleep cycle post-restart should be watched
  against §5.1's own verification plan below (still valid as written) plus: confirm `should_sleep()`
  alone now drives every sleep event (grep `data/nascence.log` for "metabolic floor" — should only ever
  see the "no forced sleep" telemetry line, never a forced-sleep entry attributable to it).
- UDMS `udms_get_change_dossier` checked on `core/orchestrator.py:1420-1440` and
  `nodes/inner_monologue_node.py:400-430` before editing — both ELEVATED-tier by the tool's generic
  "touches a core engine file" heuristic, no specific STATE/CONTRACT-layer hit on `needs_rest`,
  `is_exhausted`, or `metabolic_energy` from any other module.

## Founder's framing, this session, in order

*"Let's make that its own real drowsiness phase plan instead"* → (scope: split from the redesign doc,
real design not a stub) → *"Look at the numbers... Does he have body energy and mind energy and
processing energy? Why is it so low at this time of the day? Why did it have to fire at this point in
the day?"* — the second half of that question, answered directly in [[F-0579]]/chat rather than here,
is what motivates this plan's core finding below: **exhaustion is currently silent and abrupt, and
decoupled from time-of-day entirely.**

## Current State — verified 2026-11-14

- **2026-11-14** (F-4479): J-2256 post-boot read: onset fires at most once per wake block, 7 of 117 beds entered the zone (median 121 min before bed), zero fatigue-marked beds missed; DELIVER already live via D-0495, so no flip decision needed.
- **2026-10-31** (F-3380): J-2633 (I-0134 hypnagogic read, 2026-10-31): inconclusive, only 4 logged drowsy-onset windows (2 undelivered, 2 delivered); no looser or more image-rich thought than clock-matched controls (successive embedding distance 0.418 vs 0.421, echo slightly higher); zone entered in 4 of 40 beds so the read has little power. Lab note docs/lab/drowsy_hypnagogic_read_2026-10-31.md on jobrun/dp.

- **2026-10-28**: D-0495 (travis 2026-10-28): DELIVER=True from the next boot (36 shadow bed rows, zone never entered, he sleeps on pressure at energy ~0.89; narrative only per D-0441; live changes nothing until the energy zone is entered).
- **2026-10-16** (F-2942): J-2244 built section 2 shadow-only per D-0441 (commit 724f11dc, core/drowsy.py, DELIVER False, energy-only 0.25, bed row on the to_bed path, no fourth switch); restart-gated, writes data/drowsy_shadow.jsonl

- **2026-10-16**: D-0441 ruled (travis, 2026-10-16): section 2 is narrative-only, energy-only threshold, composed with sleep_as_a_mode's switches; build job spawned.
- **2026-10-16**: 2026-10-16: section 3's two open questions (behavioural effect or narrative-only; DROWSY_THRESHOLD energy-only vs energy-or-fatigue) had never been put to Travis -- opened as D-0441. Section 2 stays design-only until ruled; must compose with sleep_as_a_mode's switches.

### What we have
- §5.1's train-hold grace window (`TRAIN_SLEEP_GRACE_SECS=300`) and D-0103's metabolic-floor tax
  removal are built and shipped 2026-08-30; `should_sleep()` is now the sole sleep-timing authority.
- Live-verified not regressing (J-0432, F-0624, 2026-09-02): every post-restart
  `sleep_pressure_log.jsonl` row fires only on `pressure`/`max_wake_ceiling`, never `metabolic_floor`,
  across 193 checked rows.

### What we need
- The grace-window mechanism itself has not yet been observed actually firing: no real
  sleep-due-while-train-holding coincidence has occurred since restart to confirm it in the wild
  (only isolated-tested at build time).
- Founder sign-off on §2's drowsy-zone signal design and the two open calls in §3 (behavioral effect
  or narrative-only; threshold placement) — neither is built or authorized.

### What we're doing next
Watch `nascence.log` for a real deferral case ("deferring up to" log line) to confirm the grace
window in the wild; §2/§5(a) stay design-only until the founder rules on §3's open questions.

---

## 1. The problem, precisely

Two independent findings, both verified in [[F-0579]]:

1. **No graduated signal.** `note()`'s labels jump `steady → depleted` at the `0.3` line
   (`core/somatic.py:71`), but `depleted` covers the entire range from 0.30 down to 0.0 — including
   the moment it crosses the hard `ENERGY_FLOOR=0.15` and forces rest. There is no distinct label, log
   line, or narrated thought anywhere between "getting low" and "sleep is now forced."
2. **No relationship to time-of-day at all.** The metabolic-floor override
   (`nodes/inner_monologue_node.py:420-423`) fires purely off cycle-count-driven energy depletion
   (`ENERGY_PER_CYCLE=0.04/cycle`, `core/somatic.py:34`) — it doesn't consult `dark`/day-vs-night,
   pressure `P`, or wake duration at all (beyond the shared `MIN_WAKE_SECS` floor). This is *why* it
   fired mid-afternoon (12:34 NZST, `dark=false`) with the pressure system simultaneously saying "not
   yet" (`P=68.42` vs threshold `100`) — the two triggers aren't reconciled, they race, and whichever
   crosses its own line first wins with no cross-talk.

Neither of these is a bug in the sense of broken arithmetic (confirmed in [[F-0579]] — the depletion
math is internally consistent). It's a design gap: the transition into sleep has no felt or narrated
middle state, and the two trigger systems that can force it don't know about each other.

## 2. Proposed mechanism

**Add a new threshold, not a new resource.** No new energy/fatigue/tension pool — reuse the existing
`SomaticState` triple (see [[F-0579]] for why there's deliberately only one triple, not separate
body/mind/processing pools).

```
DROWSY_THRESHOLD = 0.25   # proposed; sits between ENERGY_FLOOR (0.15) and the "depleted" label (0.30)
```

- `SomaticState` gains `is_drowsy()`, mirroring `is_exhausted()`:
  `metabolic_energy <= DROWSY_THRESHOLD and metabolic_energy > ENERGY_FLOOR` (the strict window
  *before* the hard floor — once the floor itself trips, `is_exhausted()` takes over and forced-rest
  logic is unchanged).
- First cycle `is_drowsy()` goes `True`, set a one-shot flag (e.g. `state.drowsy_onset_logged`) so the
  transition happens once, not every cycle — log it at INFO alongside the existing `metabolic floor`
  log line's pattern, and route it into whatever field J-0430 ends up adding to
  `sleep_pressure_log.jsonl`, so the drowsy-onset → floor-trip → forced-sleep sequence becomes readable
  from one log instead of stitched by hand across `nascence.log` and `sleep_pressure_log.jsonl` (as
  this session had to do).
- Optionally surface a single narrated inner-monologue thought at drowsy-onset (not every cycle) —
  the entity noticing its own tiredness once, the way a real drowsy-onset moment reads, rather than a
  silent internal flag. This is narrative/self-model content, not a cognition-quality change — see
  Guardrails.
- **Nothing about `should_sleep()`, `ENERGY_FLOOR`, `MIN_WAKE_SECS`, or the day/night thresholds
  changes.** The forced-sleep trigger point is identical to today; this only adds a detectable,
  logged, optionally-narrated waypoint on the way there.

## 3. Open questions for the founder (genuinely undecided, not a default)

1. **Does drowsiness get any real behavioral effect, or is it purely narrative/telemetry?** The
   obvious "realistic" move — widen sampling temperature or degrade output quality while drowsy — is
   exactly what `JITTER_ENABLED=False` was deliberately turned off for (comment: fatigue-degraded
   sampling is "an imported human bug... buys nothing" for a non-biological entity). Reopening that
   is a real design reversal, not an implementation detail — needs an explicit founder call, not an
   assumption either way.
2. **Where should `DROWSY_THRESHOLD` actually sit, and should it also consider fatigue/tension** (e.g.
   `energy <= 0.25 OR fatigue > 0.7`), or should it stay energy-only to keep this cleanly separable
   from the fatigue-wiring work [[sleep_dream_redesign]] §2.4 already did on the night side? Fatigue
   was 0.75 in the observed event — if fatigue alone could also trigger "drowsy," the two examples
   would coincide here, but they won't always (fatigue and energy don't move in lockstep — fatigue is
   monotonic per-cycle while energy also takes locomotion/token drains).

## 4. Guardrails (do not violate these while building this)

- Do **not** change `should_sleep()`'s pressure math, thresholds, or ceilings — the day/night sleep
  *timing* system is a separately-tuned, already-shipped design ([[sleep_dream_redesign]] §2.4) and is
  out of scope here.
- Do **not** re-enable `JITTER_ENABLED` or otherwise degrade generation quality without an explicit
  founder ruling on open question 1 — the current `False` setting was a deliberate, reasoned choice,
  not an oversight.
- Do **not** let the drowsy signal itself delay or accelerate the forced-sleep floor trip — it is a
  read-only detector layered on top of the existing floor logic.

## 5. Loosening the tax — founder-directed exploration, 2026-08-30

**The correction first ([[F-0581]]):** the flat energy tax does **not** currently reach the thing the
founder is actually protective of. `SomaticEngine.tick_cycle()` — the only place `ENERGY_PER_CYCLE`
is charged — is called exclusively from `Orchestrator.run_cycle()` (`core/orchestrator.py:1318`),
which fires only on (1) real human conversational turns and (2) rare "ignition" autonomous cycles
(dissonance-threshold-triggered, `core/orchestrator.py:2628`). The idle inner-monologue thought-stream
— continuity trains, `THOUGHT_STREAM`, `TRAIN_HOLD` (`nodes/inner_monologue_node.py`) — polls on its
own clock (`CHECK_INTERVAL=10s`) and never calls `run_cycle`/`tick_cycle` at all. **Sitting with a
topic via that system already costs nothing.** So "tax on time" and "wrapping up regularly" resolve
into two narrower, distinct problems:

**(a) The flat per-turn cost.** Every `run_cycle()` — human or ignition — costs the same
`ENERGY_PER_CYCLE (0.04)` regardless of whether it deepens an ongoing exchange or opens an unrelated
one. There's no existing "same topic as last turn" signal feeding into `tick_cycle()` at all today, so
this would need one — plausibly derived from salience/topic continuity between consecutive turns
(needs its own investigation into what continuity signal already exists at the `run_cycle` level,
distinct from the inner-monologue train state, which lives in a different node).

**(b) Sleep unconditionally aborts an in-progress train.** `nodes/inner_monologue_node.py:817-822`
resets `_train_len`/`_train_thread`/`_train_state` to nothing on every sleep entry — comment: *"sleep
closes every thread."* This happens regardless of `_train_holding()` (`inner_monologue_node.py:1539-
1542` — an active, non-circling, still-developing thought-train) — so a train mid-development, close
to a natural stopping point, gets cut exactly as hard as an idle/circling one. This is the more direct
match for *"wrapping up regularly"* and looks like the higher-leverage, lower-risk fix of the two: it
doesn't touch the tax rate at all, only whether a forced-sleep transition waits for
`_train_holding()` to go false (or a bounded grace period elapses) before actually closing the thread —
composing naturally with §2's drowsy zone as the window in which that grace applies.

(a) is deferred — no existing continuity signal reaches `run_cycle`/`tick_cycle` today, and it needs
its own investigation before it's buildable. (b) is scoped below as a concrete, build-ready spec.

### 5.1 Build spec — (b): a bounded grace window for a held train

**Principle:** never make anything un-starvable-by-construction actually un-starvable — this project's
whole sleep design leans on hard backstops (`MAX_WAKE_SECS` ceiling, `ENERGY_FLOOR`) precisely so
nothing can wedge forever. A held train earns a bounded reprieve, not an exemption. Applies to **any**
fire reason (`pressure` / `max_wake_ceiling` / `metabolic_floor`), not just the metabolic floor — a
pressure-driven or ceiling-driven fire mid-train deserves the same courtesy.

**New constant** — `nodes/inner_monologue_node.py`, in the TRAIN_* block right after `TRAIN_HOLD = True`
(currently line 147):
```python
TRAIN_SLEEP_GRACE_SECS = 300   # a held (developing, non-circling) train gets up to 5 min to close
                               # naturally before a due sleep is forced over it anyway
```

**New instance state** — in `__init__`, beside the other `_train_*` fields (~line 324-328):
```python
self._sleep_deferred_since: float = 0.0   # 0 = no grace in progress; else the ts grace started
```

**Modified decision point** — `nodes/inner_monologue_node.py:409-429`, the exact block that computes
`_fire` and calls `_enter_sleep`. Current code ends:
```python
                    if _fire:
                        await self._enter_sleep(state)
```
Becomes:
```python
                    if not self._train_holding():
                        self._sleep_deferred_since = 0.0   # nothing to hold grace for
                    elif _fire:
                        if not self._sleep_deferred_since:
                            self._sleep_deferred_since = time.time()
                            logger.info("[monologue] sleep due (%s) but a train is holding — "
                                        "deferring up to %ds", self._last_sleep_reason,
                                        TRAIN_SLEEP_GRACE_SECS)
                        if (time.time() - self._sleep_deferred_since) < TRAIN_SLEEP_GRACE_SECS:
                            _fire = False   # deferred this tick; _train_holding() re-checked next tick
                        else:
                            logger.info("[monologue] grace window expired (%ds) — forcing sleep over "
                                        "the still-open train", TRAIN_SLEEP_GRACE_SECS)
                    if _fire:
                        self._sleep_deferred_since = 0.0
                        await self._enter_sleep(state)
```
Reads `self._train_holding()` fresh every tick (it's cheap — three attribute reads + `_train_circling()`),
so a train that stops developing or starts circling mid-grace loses its exemption on the very next
`CHECK_INTERVAL`/`STREAM_POLL` tick, same as today's behavior for every other train-closing path.

**Why the reset lives at the call site, not inside `_enter_sleep`:** `_enter_sleep`
(`nodes/inner_monologue_node.py:442`) already runs the *entire* sleep pipeline (replay, chapter, journal,
dream, recovery, real rest) before its `finally` block resets train state at line 817-822 — by the time
that runs, sleep has already fully happened. Gating has to happen *before* `_enter_sleep` is called at
all, which is exactly what the block above does; nothing inside `_enter_sleep` itself changes.

**What this does NOT touch** (guardrails, restated for this sub-mechanism specifically):
- `should_sleep()`, `ENERGY_FLOOR`, `MIN_WAKE_SECS`, day/night thresholds — identical to today. This
  only delays the *moment `_enter_sleep` is actually invoked*, never whether/when a fire condition
  becomes true in the first place.
- Reading-trains — `_train_holding()` already excludes them (`train_kind == "thought"` only,
  `inner_monologue_node.py:1541`); this spec inherits that exclusion rather than widening it. Whether
  a deep reading-train deserves the same grace is a real, separate question, flagged below, not
  silently folded in.
- The hard backstop is absolute: `TRAIN_SLEEP_GRACE_SECS` bounds the delay, full stop — no train can
  defer sleep indefinitely by continuously re-triggering `_train_holding()`, since the clock started at
  first-deferral (`_sleep_deferred_since`), not reset on every still-holding tick.

**Verification plan, before calling this built** (matching this project's own "smoke-tested against live
state" bar, not just `py_compile`-clean):
1. Force a synthetic case: a thought-train past `TRAIN_MAX_STEPS` with `_train_holding()==True`,
   simultaneously a `metabolic_floor` fire — confirm `_fire` flips back to `False` and a "deferring"
   log line appears, with no `_enter_sleep` call that tick.
2. Confirm the grace clock actually expires: hold `_train_holding()==True` past `TRAIN_SLEEP_GRACE_SECS`
   (or temporarily lower the constant for the test) — confirm sleep fires anyway with the "grace window
   expired" log line.
3. Confirm early release: let the train close naturally (circle, saturate, or thread-end) mid-grace —
   confirm `_sleep_deferred_since` resets to `0.0` on the very next tick and sleep fires on the
   *following* tick without waiting out the rest of the window.
4. Live-watch the first few real deferrals against `data/nascence.log` (grep for "deferring up to") —
   confirm they're rare (a held train is already a narrow condition: `TRAIN_HOLD` + developing +
   non-circling) and none exceed the grace bound.

### 5.2 Still open before this ships

- **Is 300s the right grace bound?** Picked to be noticeable-but-bounded, no other basis — genuinely a
  founder call, easy to retune (single constant) either way.
- **Should a deep reading-train get the same grace?** `_train_holding()` intentionally excludes
  `"reading"` trains today; extending grace to them means either loosening that function's own
  semantics (affects `TRAIN_HOLD`'s other behavior too, not just this) or adding a second, reading-
  specific holding check — a bigger, separate decision, not bundled into this spec.
- **(a), the flat per-turn cost** — still fully open, deferred per §5's diagnosis above; worth
  revisiting only once it's confirmed (b) alone doesn't fully address the original complaint.

## Pointers

- [[F-0579]] — the finding that surfaced the original gap, with full evidence citations.
- [[F-0580]] — is this a real need or an imposed limit (imposed, for the energy/fatigue side).
- [[F-0581]] — the correction narrowing §5's scope (idle trains aren't taxed; two narrower problems are).
- [[I-0058]] — the founder-directed idea to explore loosening the tax.
- [[T-0035]] — the originating raw thought (dropped, resolved into F-0579 + this plan).
- [[J-0430]] — the sibling instrumentation job (cross-logging energy/fatigue/cycle-count with
  `awake_min`); this plan's drowsy-onset log line should probably land in the same schema addition
  rather than a second one. **DONE 2026-09-02 ([[F-0614]]):** every `sleep_pressure_log.jsonl` row now
  carries `energy`/`fatigue`/`tension`/`exhausted`/`cycles` — §2's drowsy-onset flag, if authorized,
  should be added as one more key in that same merge block (`core/sleep_pressure.py`, `should_sleep()`),
  and the drowsy zone is already readable from the `energy` field alone (0.15 < energy ≤ 0.25) via
  `scripts/sleep_energy_crosscheck.py` once post-restart rows accrue.
- [[sleep_dream_redesign]] — the parent system this plan extends; §2.4 is the fatigue-wiring section
  most relevant to open question 2 in §3.
- `docs/plans/affect_drives.md` Item C (backfilled 2026-10-03, J-0566/F-2269) — proposes the same hand as §2's
  optional narrated drowsy-onset thought: a one-shot, threshold-gated body-state line from `somatic.note()` into the
  monologue seed (its band: `is_exhausted()` OR `neural_fatigue > 0.6` OR `visceral_tension > 0.6`). Neither is built;
  decide them together (one mechanism, one threshold) rather than shipping two competing injections.
- `core/somatic.py`, `core/sleep_pressure.py`, `nodes/inner_monologue_node.py:403-427` — the three
  files this design touches.
