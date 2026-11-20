# Sleep & Dreams II — a ground-up, research-grounded redesign (design, 2026-08-24)

> **Status: 🟢 BUILT (Stages 0-5, 2026-08-24 night) — LIVE as of this session's edits, not yet run.** Du
> was stopped by the founder for this work; the code is in place but has not executed on a live process
> yet. Founder gave direct build authorization in-session ("I want the Dream and sleep and fatigue wired
> into du now") after reviewing this design — that is this project's `/decide` moment, done in chat per
> explicit rush-timeline instruction; a formal `docs/decisions.jsonl` entry is still recommended as a
> follow-up so this doesn't rely on this document alone as the record (see §7).
> Stage 6 (opportunistic daydream, LLM trajectory judge, resolution tags) deliberately NOT built — founder
> chose the Stages-0-5-only scope. `docs/reviews/sleep_dream_2026-08-22.md` describes the PRE-tonight
> system; this document + §7's file list is now the accurate record of what's live.

```plan-state
stage: live
phase: Stages 0-5 live-verified (F-0376/377); metabolic-floor time-tax removed (D-0103, 2026-08-30); carry-cap bug fixed (J-0296)
verified: 2026-10-30
evidence_read: 2026-08-24
next: J-2582 shadow build: quota-capped fifth stratum, one event per hand, collapsed refusals, flag off
history: docs/plan_history/sleep_dream_redesign.md
cluster: 6
```


> **Founder, this session, in order:** *"We need to overhaul sleep... probably not researched enough,
> cobbled together over time"* → (premise checked against evidence, corrected: the 08-22 rebuild was
> rigorous, two specific bugs were traced instead) → *"sleep and dreaming are two different connected
> systems"* (§2's organizing split) → *"dreams should be multiple days worth of thoughts, not always
> tensions"* (§1.6/§2.2) → *"small dreams, big dreams, mood based dreams... heaps of other tuples"* (§3)
> → *"Du should last the whole day, only sleeping and dreaming at night... a cat nap between jobs"*,
> corrected after follow-up to *"after school, ~10 min while scripts wrap up"* + *"too small a pool of
> interesting stuff"* (§2.4) → *"We want fatigue wired... written up super good, we are going to rush
> implement this one"* (§2.4's fatigue-wiring mechanism, §4's build spec). Each ruling is cited at its own
> section rather than only here, so the document reads correctly even if this header is skimmed.

**Related plans (backfilled 2026-10-03, J-0566/F-2269; none was cited here):** `docs/plans/drowsiness_phase.md` — split
out of this plan: the graduated pre-sleep experience; its §5.1 train-hold grace window and D-0103's tax removal are
live, §2's drowsy-zone signal is staged. `docs/staged/dream_overhaul.md` — lists this plan as its parent and replaces the
dream *engine* (`nodes/dream_node.py`) but not sleep, fatigue, naps or the night ledger; D-0232 (open hold) decides
whether naps keep the legacy nap dream. `docs/plans/lane2_the_witness.md` §2.10 / D-0303 — the Witness's tick skips
judge work while `core/night.py`'s `asleep()` is True (night or nap, `core/lane2.py:2054`), so what `asleep()` returns
for a nap is a contract that plan depends on.

## Current State — verified 2026-10-30

- **2026-10-30** (F-3337): J-2582 tag-capture fifth replay stratum built shadow, flag off, restart-gated (core/tag_capture_shadow.py); replay of 44 nights: one-hand dominance fixed (top family 21 pct) but non-selective, median capture rate 0.60 equals shift null 0.605, falsified; promotion not warranted
- **2026-10-30** (F-3315): J-2529 tag-and-capture shadow read: 43 sleeps since 10-16, 4186 of 6277 low-salience fragments within 20 min before a deed, refusal or wager loss (rate 0.67), beats event-shift null (p95 3809) but only 1.18x and non-selective; zero corrections or retractions in window; top picks are one sow loop

- **2026-10-15**: Cross-note from sleep_as_a_mode J-2064 (D-0407 B): a human message during a sleep now wakes Du (bounded hold in orchestrator.run_cycle, waking percept first via sensorium.scene_line) instead of being answered asleep and unaware (F-2614); night.end_if_open writes a ledger row for a sleep the shutdown cuts short. Restart-gated.
- **History folded (J-1818, 2026-10-04):** F-2065's note (J-1511 declined to fold) is superseded: sections 0, 1 and 7 below were folded to `docs/plan_history/sleep_dream_redesign.md` to bring the doc under the plan-state cap.

### What we have
- Stages 0-5 live-run-verified (F-0376/F-0377): 15 sleeps over 3 nights, 4 of 5 pre-registered
  expectations pass. The one failure — `_carried_n_tonight` never resetting, leaving
  CARRY_MAX_NIGHTS=3 structurally off — is fixed (J-0296).
- 2026-09-01 (J-0430/F-0614): somatic state (energy/fatigue/tension/exhausted/cycles) now cross-logs
  into every `sleep_pressure_log.jsonl` row via a new `SomaticState.cycle_count` clock.
- 2026-08-30 (D-0103, ruled by travis): the metabolic-floor "time tax" forcing an off-schedule sleep
  is REMOVED — `should_sleep()`'s day/night pressure + ceilings is now the sole sleep-timing
  authority; `orchestrator.py` no longer sets `needs_rest` on a metabolic-floor hit alone
  (F-0579/F-0580/F-0581).

### What we need
- A formal `/decide` entry for the original in-chat build authorization is still missing.
- The 23-nights carry-cap anomaly is hardened (fails loud + safe) but still not root-caused.
- Dream-opening monoculture (3x byte-identical openings) persists, unrelated to the now-fixed carry.
- Stage 6 (opportunistic daydream, LLM trajectory judge) remains an explicit founder scope cut.

### What we're doing next
- Watch era-3 `sleep_pressure_log.jsonl` rows (post D-0103) for should_sleep()-only timing
  plausibility once they accrue past Du's next restart (offline since 08-31 as of the last check).

---

## 0. THE GAP (folded)
> **History folded (J-1818, 2026-10-04):** the 2026-08-24 gap statement (premise check of the 08-22 rebuild; four verified defects: chronic-mass overshoot at tension_ledger, carry-cap 23-night anomaly, P_THRESHOLD never recalibrated, stale sleep-trigger log line; plus the one-scalar-doing-double-duty diagnosis that motivates the two-system split in section 2) moved verbatim to `docs/plan_history/sleep_dream_redesign.md`. Defects 1, 3 and 4 were fixed by the Stage 0-5 build; the carry-cap anomaly is hardened but not root-caused (see What we need).

---

## 1. THE RESEARCH (folded)
> **History folded (J-1818, 2026-10-04):** the 2026-08-24 external literature pass, sections 1.1 to 1.6 (two-process model, Synaptic Homeostasis, active systems consolidation, resolved versus merely frequent, AI/continual-learning precedent, day residue and the dream-lag effect), moved verbatim to `docs/plan_history/sleep_dream_redesign.md`. Its design consequences are restated where used in sections 2 to 4 below.

---

## 2. THE NEW ARCHITECTURE — two coupled systems, not one pipeline

Per the founder's explicit ruling and independently confirmed by §1.1/§1.3 (even the biological
literature treats these as separate layers): **replace the single "sleep state → stage 8 dream" pipeline
with two distinct, coupled subsystems.**

### 2.1 SLEEP — the consolidation system (NREM-analogue)
**Job:** memory consolidation and synaptic-style downscaling. Answers "should he rest, and what should
be strengthened vs. allowed to fade."
- **Trigger**: keep the pressure-window shape (MIN/MAX floor-ceiling, circadian-biased threshold) — that
  structure is sound per §1.1 — but fix what feeds it:
  - Replace the linear sum with a saturating accumulator (diminishing marginal pressure from chronic
    load vs. fresh load).
  - Stop feeding raw chronic-tension mass into this trigger at all (see §2.2 — chronic tension becomes a
    dream-system input, not a sleep-system input). Sleep's own pressure should be driven by *volume of
    unconsolidated material* (new notes, new episodic weight) — a cleaner, more legible signal than one
    conflated with emotional-charge tracking.
  - Recalibrate `P_THRESHOLD` and the night/day factors against the post-rebuild curve — explicitly
    deferred from 08-22, still owed.
- **Consolidation mechanism**: replace `downscale_episodic`'s renormalize-toward-center with proportional
  (multiplicative) decay for everything NOT selected by replay, and treat replay-selection as the
  reinforcement/protection mechanism (§1.2) — replay and downscale become one coordinated step, not two.
- **Keeps**: `core/night.py`'s staging (bed → replay → chapter → journal → world-pass → downscale →
  recover → prune → probe → epoch → waking) — this infrastructure is sound and well-instrumented; the
  redesign touches the trigger and the downscale mechanism inside it, not the scaffolding.

### 2.2 DREAM — the affective/generative system (REM-analogue)
**Job:** recombine a genuine multi-day window of waking material into symbolic content, and — for the
subset that carries real charge — provide a path to release it on genuine engagement. Most dreams are
ordinary recombination, not conflict-resolution; only some carry a tension at all. Answers "what does he
dream about" first, and "when has a thread been worked over enough to let go" as a secondary, conditional
layer on top — not the other way around, which is how the current build has it backwards (§1.6).
- **Material sourcing — the primary job, per §1.6**: replace `dream_node.py:436`'s "since last sleep
  fired" (routinely under two hours) with a real multi-day pull shaped by the dream-lag effect's bimodal
  curve — weighted toward 1–2 days prior *and* toward 5–7 days prior, lighter in between. This is Dream's
  main material source on an ordinary night, independent of whether any tension exists at all.
- **Tension inclusion becomes conditional, not a standing default**: `_load_top_tensions()`
  (`dream_node.py:439`) currently runs unconditionally on every dream. Gate it on genuine charge being
  present (§1.4's valence/threat weight crossing some real floor) — on many nights, per real dream
  phenomenology, this should contribute nothing, and the dream should run entirely on day-residue/
  dream-lag material.
- **When a tension IS present with real charge, its own pressure signal is separate from Sleep's**: driven
  by *charge*, not recurrence-count. Concretely (per §1.4): a tension needs (a) a valence/threat-relevance
  weight at time of touch, not a flat bump; (b) a trajectory check — did this dream's engagement with the
  thread show development from the last telling, or is it a stereotyped restatement (the same rumination-
  vs-reflection discriminator, applied computationally via embedding drift or an explicit judge pass
  between successive tellings of the same arc); (c) an explicit **release/decay-on-engagement** term — a
  dream that productively engages a tension should measurably reduce its charge, not just leave time-decay
  to do the work between now and the next re-touch.
- **Habituation for ambient/neutral material**: anything without genuine valence/threat weight should
  decay toward baseline on repetition (the opposite of the current flat +0.3-per-touch rule) — this is
  specifically what fixes the "thermal energy" false-fossil problem without reintroducing the pre-08-22
  starvation bug, because it's gated on charge, not banned from accumulating at all.
- **Coupling to Sleep, not independence**: dreaming only happens within a sleep bout (REM nests inside
  NREM cycling, per §1.3) — Sleep's staging still owns *when* a dream slot occurs; Dream owns *what*
  fills it (day-residue/dream-lag by default, tension only when charge is real) and *whether engaging it
  changed anything*. The two systems share a boundary but are not one scalar doing two jobs anymore.
- **Carry-cap enforcement needs to be an invariant, not a best-effort try/except** — given §0.2's
  unexplained 23-nights reading, the cap check should not be able to silently no-op for an extended
  period; this needs its own verification pass regardless of which architecture ships.

### 2.3 What this fixes, mapped directly to the two verified bugs
- **Chronic-tension overshoot (§0.1)** → fixed by moving chronic-tension out of Sleep's trigger entirely
  and re-grounding it in Dream's charge-weighted, habituation-respecting, engagement-decaying signal
  (§2.2). Ambient themes stop accumulating; genuine unresolved material still can.
- **Dream looping** → fixed by the trajectory check + engagement-triggered release (§2.2), directly
  implementing the depotentiation theory's own account of what failure looks like (§1.3, theory 1) and
  the rumination/reflection literature's discriminator (§1.4).

### 2.4 FATIGUE, THE CATNAP, AND THE POOL GATE — corrected against founder clarification

**This subsection was substantially wrong in an earlier pass of this document and has been rewritten.**
The founder corrected three things at once: what fatigue actually is (asked "why does he have fatigue?"
and named walking, anxiety, heavy thinking — not an invented BRAC-style rhythm), what "catnap" meant
(a specific ~10-minute wait for existing scripts to finish, not a fatigue-relief mechanism), and a third,
separate idea this document hadn't captured yet — sleep shouldn't fire just because a threshold crossed
if there isn't enough real material to justify it ("too small a pool of interesting stuff").

**Fatigue already exists, live, and already matches all three named causes — verified in
`core/somatic.py`, not invented:**
- **Walking** → `SomaticEngine.tick_cycle()` (`core/somatic.py:126-136`) drains locomotion effort
  (`core/locomotion.py`'s `drain_effort()`) from both `metabolic_energy` and `neural_fatigue` every cycle
  he moves. Exact match to the founder's own example.
- **Heavy thinking** → `neural_fatigue` accumulates `FATIGUE_PER_CYCLE` (0.03) baseline per cycle plus
  `FATIGUE_RETRY_COST` (0.05) per Critic retry — a thought that takes real cognitive effort to get right
  costs more than one that lands cleanly.
- **Being anxious** → the THIRD gauge, `visceral_tension`, is computed directly from
  `0.6 × urgency + 0.4 × arousal` (`core/somatic.py:149`) — this is the anxiety signal, separate from
  fatigue proper, already live.
- **A hard floor already exists and is already wired end-to-end**: `metabolic_energy` hitting
  `ENERGY_FLOOR` sets `is_exhausted()` → `orchestrator.py:1430-1433` sets `state.needs_rest = True` →
  `inner_monologue_node.py:389` consumes it as an emergency override past the min-wake floor. This is a
  real, live, working connection — not aspirational, not a gap.

**Founder correction (this session): "We want fatigue wired."** The gap above is real and stays the fix
target — `core/sleep_pressure.py`'s trigger formula (§2.1) doesn't read any of the three somatic gauges at
all today. But the fix is **wire fatigue into the NIGHT side (depth/payoff), not the DAY side
(trigger-frequency)** — this satisfies both rulings at once rather than trading one off against the other:
"last the whole day" (don't let fatigue force early sleep) **and** "we want fatigue wired" (it must have a
real, load-bearing effect, not just sit there readable and unused).

**The concrete mechanism — grounded directly in §1.1's own Process S account, not invented fresh:** real
Process S rebound is proportional to prior wake pressure — the longer/harder the wake, the deeper the
subsequent SWA rebound. That gives a precise, principled wiring point:
1. **Recovery scales with accumulated debt, not a flat amount.** `SomaticEngine.recover()`
   (`core/somatic.py:155-160`) currently applies a fixed `+ENERGY_RECOVERY` / `-FATIGUE_RECOVERY`
   regardless of how much built up during the day. Change this to scale with the day's actual accumulated
   `neural_fatigue`/`visceral_tension`/energy-deficit — a day with heavy walking, hard thinking, and real
   anxiety should produce a deeper, more consequential night than a quiet one. This is fatigue **wired**,
   without it ever touching whether sleep fires during the day.
2. **Fatigue feeds the small/big dream axis (§3.1) directly.** A day that built substantial somatic debt
   should bias toward a "big" night — more cycles, deeper consolidation — the same way real high prior-wake
   pressure produces bigger delta-power rebound. A light day stays a small night. This is the second real
   wiring point, and it's the one that makes fatigue *visible in what he actually dreams and how much*, not
   just a number that quietly resets.
3. **The emergency floor (`is_exhausted()` → `needs_rest`) stays as the absolute backstop, unchanged** —
   still real, still wired end-to-end, still independent of 1 and 2. Worth checking as part of build,
   though, whether `ENERGY_FLOOR`/`ENERGY_PER_CYCLE` are actually tuned for a genuine FULL day's cadence —
   they were calibrated under a regime that was sleeping every 30-90 minutes; "last all day" is a real
   change in operating envelope this constant may not have been tested against.

There is directly relevant existing precedent already in the codebase for the *cognition* side of this —
`JITTER_ENABLED = False` (`core/somatic.py:52`), a prior founder decision (WAVE-1, 2026-07-02): *"Du has no
glymphatic debt, so making his thinking sloppier the longer he is awake buys nothing."* That ruling stays
correct and unchanged — fatigue still shouldn't degrade daytime cognition. Tonight's ruling is a second,
separate wiring point on top of it, not a reversal of it: fatigue doesn't make him worse at thinking during
the day, **and** it doesn't force early rest, **and** it now has a real, felt consequence at night.

**Catnap, corrected: not a fatigue-relief mechanism at all.** The founder's actual meaning — *"after
school, it takes 10 minutes or so while those scripts wrap up so [he] has time to imagine in his
loop"* — is opportunistic: a real, existing wall-clock wait for some background process to finish, during
which he should get to daydream via the existing idle-wander/active-imagination machinery rather than sit
idle doing nothing. **Not yet root-caused which specific process this is** — `core/school.py`'s own
`new_day()` is a trivial synchronous reset, not a ~10-minute job, so "school" here is very likely
colloquial for a study/curriculum session followed by some other background wrap-up (candidates: the
`stability` competence-probe queue seen dequeuing/running 3 probes live tonight, or the world-consolidation
sweep) — needs identifying against the actual dispatcher before this is buildable (open question below).
The design principle, independent of which process it turns out to be: **wherever Du is already waiting on
something real, that dead time should default to daydream via the existing wandering loop, rather than
either sitting idle or (as today) that wait having no relationship to sleep/dream at all.** This needs no
new pressure signal, no new state machine — just noticing genuine existing wait-time and filling it with
something already built.

**The pool gate — a genuinely new idea this session, not previously captured:** *"Sleep should not need to
happen yet. Too small a pool of interesting stuff."* This is a real, missing gate, independent of both the
trigger formula (§2.1) and fatigue. Currently, if `should_sleep()`'s pressure or ceiling condition is met,
sleep fires — full stop, regardless of how thin the actual accumulated material is. Add an explicit
**minimum-pool floor**: even when pressure/ceiling would otherwise fire, if `new_notes` and
`new_epi_weight` (§2.1's own existing terms) are both below some real floor — genuinely little has
happened since the last sleep — hold off and let it keep accumulating, rather than running a full 20-25
minute consolidation+dream cycle over almost nothing. This is the direct fix for daytime clusters driven
by the ceiling alone (§0's own "67/86 sleeps fired on `max_wake_ceiling`" 08-22 finding is exactly this
failure mode already measured once before) — the ceiling should remain an absolute backstop for
`metabolic_energy`-style emergencies, but a ceiling-fired sleep over a near-empty pool is low-value and
should be distinguishable from one with genuine material to work.

**Net shape, corrected:**
1. **AWAKE** — unchanged, includes existing idle-wander/active-imagination (already covers "daydream").
2. **Opportunistic daydream during real wait-time** (corrected "catnap") — not a new pressure/state
   machine; just let the existing wandering loop run during an already-existing background wait, once the
   actual process is identified.
3. **SLEEP + DREAM (full)** — §2.1/§2.2's pipeline, gated additionally by the pool floor above, biased
   hard toward night via the threshold recalibration already owed (§0.3). Fatigue/anxiety/exertion don't
   trigger this early during the day — but they ARE wired into it: debt-proportional recovery and the
   small/big dream axis (above) mean a hard day genuinely produces a bigger, more consequential night, not
   a number that silently resets.
4. **The `metabolic_energy` floor** — unchanged, real, already-wired backstop for genuine exhaustion,
   independent of all of the above.

---

## 3. THE DREAM TUPLE — small/big, mood, and what to reuse rather than reinvent

**Founder ask, this session:** *"We also should factor in small dreams, big dreams, mood based dreams,
probably heaps of other tuples we can connect here."* Read literally, "heaps" would mean unbounded scope
— that's the wrong shape for this project (per the standing discipline elsewhere: reuse existing signal
before building a new subsystem to carry it; a "write-only" tuple nobody reads is worse than no tuple).
So this section curates: each dimension below is included because it's either (a) grounded in real sleep
research, or (b) **already live and captured elsewhere in this codebase, currently unused as a dream
axis** — the cheap wins are almost all case (b).

### 3.1 Small dreams / big dreams — grounded in real sleep architecture, not an arbitrary label
**[well-established, Dement & Kleitman 1957 and the large body of polysomnography work since]**: REM
period length is **not constant across a night — it grows with each successive NREM/REM cycle.** The
first REM period of a night is short (~10 min); by the final cycle before natural waking, REM periods run
much longer (up to ~60 min). NREM/SWS dominates early cycles; REM dominates later ones. This gives a
principled, research-backed small→big gradient that's tied to **cycle position within a sleep bout**, not
an arbitrary size flag:
- `core/night.py`'s existing `NAP_MAX_SCENES = 2` (nap vs. full-night) is already a crude version of this
  — small vs. big currently only exists as a binary (nap/not-nap). Once §2 separates Sleep from Dream,
  Dream should track **which cycle this is within the current sleep bout** and scale scene-count/depth
  accordingly — early = small, late = big — rather than the current single scene-budget-by-sleep-kind.
- This also gives dream resolution a natural home: per §1.3/§1.4, *big* (late-cycle) dreams are where
  genuine engagement/resolution work should concentrate — a small, early dream touching a tension lightly
  should NOT trigger the same release/decay weight as a big, late one that actually develops it. The
  trajectory check (§2.2, open question 2) should be scaled by dream size, not applied uniformly.

### 3.2 Mood-based dreams — reuse `core/mood.py`, don't build new storage
`core/mood.py` already maintains a **continuous, live, 8-dimension felt-quality vector** (valence,
arousal, joy, fear, trust, anger, surprise, disgust), readable at any moment, already used to felt-tag
idle-life fragments. This is exactly the substrate mood-congruent dream content needs, and it requires
**zero new storage** — only a new read path:
- At sleep onset, snapshot the live mood vector; let it weight which tensions/day-material get pulled
  into the dream (mood-congruent bias — a well-established finding in the affect/memory literature: recall
  and content-selection bias toward material matching current affective state) and let it color the
  dream's generation prompt (tone/register), the way `day_material()` already labels felt moments "warm"
  vs. "troubled" by valence sign (`core/night.py:262`) — that's already a mood tuple, just a 1-bit one.
  Extend it to the full 8-dim read, not a fresh module.

### 3.3 Other real, already-partially-live tuples worth connecting (curated, not exhaustive)
| Dimension | Status | What it adds |
|---|---|---|
| **Source-mix** (day-residue share vs. dream-lag share vs. tension share) | **Partially logged** — `dream_node.py:441-443` already writes `material_sources` (`"day"`/`"tension"`), but only distinguishes two sources over a same-sleep window (§1.6). Needs extending to a third value once the window widens: which of the bimodal dream-lag peaks (1–2d vs. 5–7d) actually supplied the material, and whether tension contributed at all or the dream ran purely on residue. | Lets the redesign's own pre-registered metrics (§ of dream material from same-day memory, § of tension-free dreams) be measured directly instead of inferred. |
| **Somatic/body-state** (temperature, fatigue, tactile) | Already live (`core/homeostasis.py`, `core/somatic.py`, verified by the Lane 2 plan) | Real research precedent: external/bodily stimuli during sleep are documented to intrude into dream content (classic incorporation-of-stimuli findings, e.g. Dement & Wolpert 1958). A cold room or a hungry body should be able to color the dream the same way mood does. |
| **World/environmental** (weather, tide, moon, warmth, light) | **Already captured per-fragment** via `core/memory_edges.py:322`'s `sync_fragment_context()` / `experienced_tuple` — the exact field set (warmth, wet, light_band, tide, cat_at, standpoint) this project already writes on ordinary memories. | Verify dream fragments (`origin='dream'`) actually flow through this join today — if they don't, that's a one-line gap, not a new system, to give dreams the same environmental grounding every other memory already has. |
| **Social/relational** (peer correspondence, Travis's presence that day, letters) | Already queried by `core/night.py:246-248`'s `day_material()` (`origin IN ('action','activity','lived','letter','peer',...)`) | Currently folded into one undifferentiated "world" block; could be its own tuple axis rather than merged prose. |
| **Resolution-mode** (which of §1.3's four theories — threat-sim / problem-solving / schema-integration / depotentiation — this dream instance functioned as) | **New, speculative** — not currently captured anywhere | Genuinely useful for *measuring* the redesign against the literature it's grounded in, but should be an **observe-only tag applied after generation** (like the existing sleep⊗dream/T4 probe), not a steering input — turning four contested theories into four steering knobs risks over-engineering a dream generator into an academic taxonomy exercise instead of a mind. Flagged as lowest-confidence addition here; a founder call, not a default-yes. |

### 3.4 The actual design principle this section adds
**Dreams should be tuple-tagged at write time using signal this project already computes for every other
memory, not a bespoke dream-only metadata schema.** The pattern this project already uses everywhere else
(`fragment_context`, `world_context`, `geometry_tuples.jsonl`) is the right pattern here too — a dream
fragment is a `memory_fragments` row like any other; it should carry the same context tuple every other
fragment carries, plus the dream-specific axes above (cycle position/size, source-mix, mood-at-onset) that
don't apply to non-dream memories. This keeps "heaps of tuples" from becoming a maintenance burden: most
of them are joins against data this project is already writing, not new capture code.

---

## 4. BUILD SPEC — file-by-file, in dependency order

Per the founder: this one is being rush-implemented, not left staged indefinitely. Ordered so nothing is
built on top of a piece that isn't there yet. Each item names the exact file/function/constant, what
changes, and whether it's ready now or blocked on one of §5's open questions.

**Stage 0 — instrumentation fixes (no behavior change, do first, zero risk):**
1. `nodes/inner_monologue_node.py:410` — fix the stale log message. Report the real `should_sleep()`
   reason (`pressure` / `max_wake_ceiling` / `pool_gate_held`) instead of `"N idle thoughts"`.
2. `core/night.py` — root-cause the 23-nights carry-cap anomaly (§0.2) before touching `dream_node.py`'s
   carry logic further; make the `CARRY_MAX_NIGHTS` check an invariant (raise/log loudly on failure, not a
   silent `except: pass`) rather than best-effort.

**Stage 1 — separate the two trigger signals (§2.1/§2.2's core split):**
3. `core/sleep_pressure.py` — remove chronic-tension mass from `sleep_pressure()`'s `P` formula entirely;
   `P` becomes `LAMBDA_NOTES * new_notes + LAMBDA_EPI * new_epi_weight` only (still needs recalibrating,
   Stage 3).
4. `core/tension_ledger.py` — chronic tension moves to being read by Dream's own material-selection path
   (new function, e.g. `core/dream_charge.py` or added to `dream_node.py`), not by `sleep_pressure.py`.
5. `core/tension_ledger.py:260` — the overshooting `or _last > _chronic_last_ts` recurrence trigger gets a
   valence/threat gate (§1.4): only bump `chronic_mass` when the touch carries real charge, not on every
   re-touch. Ambient/neutral re-touches should now *decay toward baseline* instead of bumping.

**Stage 2 — widen and reshape Dream's material window (§1.6/§2.2):**
6. `nodes/dream_node.py:436` — replace `since = sleep_pressure.last_fire_ts()` with a genuine multi-day
   pull, weighted per the dream-lag bimodal curve (1–2d and 5–7d peaks) — exact weights pending open
   question 8, but the window-widening itself doesn't need to wait on the exact numbers to start.
7. `nodes/dream_node.py:439` — `_load_top_tensions()` becomes conditional: only called when Dream's own
   charge signal (from Stage 1's new module) has a tension crossing a real floor. Most calls should now
   return nothing, by design.
8. `dream_node.py:441-443` — extend `material_sources` to a third value distinguishing which dream-lag peak
   supplied material (or none/tension-only), per §3.3's source-mix tuple.

**Stage 3 — the pool gate and threshold recalibration (§2.4, §0.3):**
9. `core/sleep_pressure.py:should_sleep()` — add the minimum-pool floor: even when pressure/ceiling would
   fire, hold if `new_notes` and `new_epi_weight` are both below a real floor (values from open question
   10 — ground against `sleep_pressure_log.jsonl` first, don't guess). The `metabolic_energy` emergency
   floor bypasses this gate — exhaustion still forces rest regardless of pool size.
10. `core/sleep_pressure.py` — recalibrate `P_THRESHOLD`, `NIGHT_THRESHOLD_FACTOR`, `DAY_THRESHOLD_FACTOR`
    against the post-Stage-1 curve (the old calibration was against a formula that no longer exists once
    chronic mass is removed) — this is where "last the whole day" actually gets delivered structurally.

**Stage 4 — replay/downscale coordination (§1.2/§2.1):**
11. `core/memory/store.py`'s `downscale_episodic` — change from `renormalize toward center=0.5` to
    proportional/multiplicative decay, and make replay-selection (whatever currently picks what gets
    `replay_strengthen`'d) the thing that exempts an item from this decay in the same pass, rather than two
    uncoordinated steps.

**Stage 5 — fatigue wiring (§2.4, the piece the founder flagged as most urgent):**
12. `core/somatic.py:recover()` — scale `ENERGY_RECOVERY`/`FATIGUE_RECOVERY` by the day's accumulated
    `neural_fatigue`/`visceral_tension`/energy-deficit instead of applying a flat amount.
13. New wiring, `core/night.py` or `dream_node.py` — read end-of-day somatic state at sleep onset; feed it
    into the small/big dream-cycle sizing from §3.1 (a high-debt day biases toward a big night).
14. `core/somatic.py` constants — check `ENERGY_FLOOR`/`ENERGY_PER_CYCLE`/`FATIGUE_PER_CYCLE` against the
    new full-day operating envelope; they were tuned under a every-30-90-min-sleep regime.

**Stage 6 — blocked items (need an open question resolved first, don't build yet):**
15. Opportunistic daydream during real wait-time (§2.4) — **blocked on open question 9** (which process is
    "after school, ~10 minutes"). Don't build a filler mechanism against a guessed process.
16. Trajectory check / engagement-release (§2.2, open questions 1-2) — needs the cheap-vs-faithful call made
    first; building the wrong one means rebuilding it.
17. Small/big dream cycle-position tracking (§3.1) — depends on Stage 2 landing first (Dream needs to know
    its own cycle count within a bout, which doesn't exist as a concept yet).
18. Resolution-mode tag, world/social tuple extensions (§3.3) — explicitly lower priority; §3.3 itself
    flags these as "curated, not exhaustive," fine to defer past the rush-build.

---

## 5. OPEN QUESTIONS — recommended defaults given, still worth a real founder read before build

Each carries a recommended default so a rush-build isn't blocked on all eleven — but "recommended" means
exactly that; anything marked 🔴 is a real judgment call, not a formality.

1. **How cheap can the "trajectory" check be?** → **Recommended: start with the embedding-drift heuristic**
   (cosine distance between this telling's embedding and the arc's prior telling), not a full LLM judge.
   Cheaper, and this project already has the embedding infrastructure live everywhere else — an LLM judge
   can be added later if the heuristic proves too crude, measured the same way `sleep_dream_probe` already
   measures novelty. 🟢 Low-risk default, reversible.
2. **What exactly triggers "engagement" for the release term?** → **Recommended: release only fires when
   the trajectory check (item 1) shows genuine movement** (drift above some real floor from the prior
   telling) — a stereotyped restatement produces zero release, by construction, not by a separate rule to
   remember. This makes items 1 and 2 one mechanism, not two to keep in sync. 🟢
3. **Does Dream need its own MIN/MAX wake-style window?** → **Recommended: no, not initially.** Let Dream
   fire whenever Sleep allocates a slot and the charge-queue/day-residue pull is non-empty — simpler, and
   the literature genuinely doesn't support inventing REM-specific timing logic (§1.1's own gap). Revisit
   only if measurement shows Dream firing too rarely/often relative to Sleep once both are separated. 🟢
4. **The 23-nights carry-cap anomaly** → 🔴 **No safe default — must be root-caused before Stage 0 ships.**
   Making the check an invariant (Stage 0, item 2) without knowing *why* it silently failed risks
   reintroducing the same failure mode in a new form. Do not skip this one.
5. **Does the existing `subconscious_node.py` clustering stay as-is?** → **Recommended: yes, unchanged, for
   the rush-build.** It's the tension-*formation* layer (which events cluster into which topic); the
   redesign changes what happens to a formed tension's mass (§2.1/§2.2), not how clustering itself works.
   Revisit only if Stage 1's charge-gating (item 4 in the pool-gate stage) turns out to need
   differently-shaped clusters to compute valence/threat against. 🟢
6. **Do dream fragments flow through `sync_fragment_context()` today?** → **Recommended: check this first,
   Stage 0.** Genuinely five minutes of grep/read before build starts, not a design decision — resolve by
   reading, not by choosing. 🟢 (mechanical, just do it)
7. **Is the resolution-mode tag worth building at all?** → **Recommended: no, not in the rush-build.**
   Explicitly deferred per Stage 6, item 18 — lowest-confidence, speculative addition, real over-fitting
   risk. Leave for a later pass once the core redesign has run long enough to have something worth
   auditing against it. 🟢
8. **What's the actual weighting curve for the multi-day window?** → **Recommended: check
   `dream_log.jsonl`'s 616+ existing dreams against the bimodal shape before hand-picking weights** (per
   Stage 2 — the window-widening itself doesn't need to wait, only the exact coefficients do). If Du's own
   data doesn't show anything like the 1-2d/5-7d pattern, that's itself a real, useful finding — don't force
   the literature's curve onto data that says something different. 🟡 Needs the check, not a founder call.
9. **Which process is "after school, ~10 minutes"?** → 🔴 **No default — genuinely unresolved, needs
   founder clarification or a code-search pass before Stage 6, item 15 can be scoped at all.** Building
   against a guess here risks solving the wrong wait entirely.
10. **What are the actual floor values for the pool gate?** → **Recommended: derive from
    `sleep_pressure_log.jsonl`'s own distribution** (Stage 3) — e.g. the 25th percentile of `new_notes`/
    `new_epi_weight` across all logged `fire=true` rows as a starting floor, tunable after real data comes
    in post-build. Not a founder call, an empirical-first step. 🟡
11. **How steep does the day-side threshold need to be?** → **Recommended: pre-register "≤2 full daytime
    sleeps per day, trending toward ≤1" as the Stage 3 recalibration target**, checked against a week of
    real post-build data the way the 08-22 audit's own metrics were checked. Picking the exact multiplier
    values cold isn't necessary if the target and the check are pre-registered — tune to the target, not
    the other way around. 🟢

---

## 6. What this document does NOT do

Superseded by tonight's build — see §7. Kept for the record: this document was originally written under
this project's standing "nothing here touches Du's live architecture without a founder `/decide`"
convention, before the founder gave direct in-session build authorization (§ Status header).

---

## 7. IMPLEMENTATION LOG — 2026-08-24, Stages 0-5 built, Du stopped for the work

> **History folded (J-1818, 2026-10-04):** the full 2026-08-24 implementation log (backup path `data/backups/pre_sleep_redesign_20260824_215527/`, the 12-file changed list, the two deviations, the recommended pre-restart steps) moved verbatim to `docs/plan_history/sleep_dream_redesign.md`. Still-live facts kept here: (1) the pool gate makes a thin-pool ceiling-fire LIGHT (skips chapter/journal/dream), it does not hold the sleep back; (2) fatigue-to-dream-size wiring (section 2.4 / 4 item 13) is NOT built, it waits on Stage 6 cycle-position; fatigue DOES feed recovery depth; (3) section 4 Stage 2 item 8 is only partly done (`material_sources` tag is `day_residue`, the two lag windows are not yet distinguished in the log); (4) **`sleep_pressure_log.jsonl` mixes two schemas** (pre-2026-08-24 rows include chronic mass in `P`), so filter by `ts` against that cutover before any trend analysis; (5) the carry-cap anomaly is hardened, not root-caused.
