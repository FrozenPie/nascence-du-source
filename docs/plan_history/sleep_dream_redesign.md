# sleep_dream_redesign — folded history


---

# History folded on 2026-10-04 from `docs\plans\sleep_dream_redesign.md` (J-1818 hand-fold of 4 superseded/historical span(s), verbatim, original order; each preceded by its original line range)

_Every J-/F-/D- id below is the canonical record. Derived timeline: `plan_ledger.py sleep_dream_redesign`._

_[original lines 43-43]_

- **2026-09-28** (F-2065): Reviewed the over-cap design sections for a safe fold (J-1511). Both candidates J-1499 flagged, the external-literature review and the implementation log, turned out to be load-bearing with no other home once checked against plan-ledger and plan-compact output, not genuinely redundant history. Left the doc content unmodified; it stays over the 40000-byte cap by deliberate choice, not oversight. Full evidence in F-2065.

_[original lines 68-102]_

## 0. THE GAP — why the 08-22 rebuild isn't enough, stated honestly

**Correcting the premise first, because the evidence doesn't support "old and never touched."**
`docs/reviews/sleep_dream_2026-08-22.md` was a rigorous, measured audit — 14 findings, all with real
numbers (616 dreams, 24,703 sleep-pressure rows, 733 tensions), built same day, with pre-registered
target metrics. It fixed real things: dreams were stuck in one 51-night unresolved loop, going cold on
write (unreachable by ordinary recall), importance was being flattened nightly, sleep pressure was
structurally starved near zero. Most of that work holds — `core/night.py`'s staged pipeline (bed →
replay → dream → fade → wake, one row per night in `night_log.jsonl`) is genuinely well-built and is
**not** what this redesign should discard.

**What's actually wrong, verified 2026-08-24 (this session):**
1. **The chronic-mass fix overshot.** The 08-22 fix for "chronic mass never accumulates" added a second
   recurrence trigger (`core/tension_ledger.py:260`, `or _last > _chronic_last_ts`) that bumps +0.3 on
   almost any re-touch, decaying on only a 3-day half-life. Anything recurring more than ~once every 2
   days now accumulates without bound. "Unresolved: thermal energy" has recurred 170 times since
   2026-06-11 (74 days) — an ambient, constantly-re-touched theme (he sits near a hearth), not a genuine
   unresolved crisis — and it's the single largest contributor to a chronic floor that climbed 42.6 →
   67.7 in under two days, now structurally above the night threshold (45.0) on its own.
2. **The dream-arc carry cap looks like it silently failed for an extended period.** `CARRY_MAX_NIGHTS =
   3` (`core/night.py:46`) is correctly checked in `dream_node.py:137`, but tonight's log shows *"the
   unfaced thread has returned 23 nights"* before the cap fired — nearly 8x the intended ceiling.
   Not root-caused this session; flagged as an open question (§5).
3. **The sleep-pressure formula was never recalibrated post-rebuild**, despite the 08-22 doc's own build
   order explicitly calling for it ("Recalibrate `P_THRESHOLD` from the measured curve"). `P_THRESHOLD =
   90.0` in `core/sleep_pressure.py` is unchanged from before the rebuild.
4. **The sleep-trigger log message is stale**, still reading `"N idle thoughts -> entering Sleep State"`
   — leftover phrasing from the pre-08-22 fixed-count trigger. The real cause (pressure vs. ceiling) is
   silently not reported.

**The deeper, structural reason both real bugs above exist:** a single "chronic tension" scalar
currently does double duty as **both** the sleep-trigger input **and** the dream-content selector. The
literature review below (§2) makes clear this is not a parameter-tuning problem — it's an architecture
problem, and it's the same one the founder named independently: **sleep and dreaming need to be two
distinct, coupled systems, not one pipeline with dreaming as stage 8 of 13.**

_[original lines 106-255]_

## 1. THE RESEARCH — external literature pass, 2026-08-24

Full sourced briefing on file (session record); condensed here by what it changes in the design.
Confidence markers preserved from the source pass: **[well-established]** / **[contested]** / **[general
knowledge, verify before citing further]**.

### 1.1 The two-process model (Borbély, 1982; Daan/Beersma/Borbély, 1984) — Process S vs. Process C
**[well-established]** Sleep timing = homeostatic pressure (Process S, rises in wake / decays in sleep,
indexed physiologically by slow-wave EEG activity) + circadian phase (Process C, SCN-driven, largely
independent of prior wake duration). Two things this model has that the current build doesn't:
- **Saturating exponential dynamics**, not a linear sum with hard clamps. A linear accumulator can't
  produce diminishing marginal pressure from chronic-but-not-acute input the way a proper asymptotic
  process does.
- **Locality.** Real Process S is not one global scalar — SWA rebound after wake is *regionally
  specific* to what was actually used (Huber et al. 2004, *Nature*, "Local sleep and learning"). A
  single undifferentiated pressure number structurally cannot represent "this one topic has
  disproportionate local pressure" vs. "overall load is high" — which is very likely part of why a
  single scalar mis-serves both jobs it's currently doing.
- **A genuine upper/lower threshold pair**, both circadian-modulated — not one threshold times a
  day/night constant. Worth checking whether MIN_WAKE/MAX_WAKE is really doing the lower-threshold's
  job or is a bolted-on afterthought.

**What the model explicitly does NOT cover [well-established gap]:** it says nothing about REM/dream
timing or function at all. It's a NREM/SWA model with a circadian gate bolted on — confirming the
founder's point independently: even the foundational biological model treats sleep-the-consolidation-
process and REM-the-dream-process as separate layers, one of which (REM) it doesn't address.

### 1.2 Synaptic Homeostasis Hypothesis (Tononi & Cirelli) — selective, not uniform, downscaling
**[well-established as hypothesis; universality contested]** Sleep performs net synaptic downscaling to
restore signal-to-noise, but critically: **proportional/multiplicative scaling that preserves relative
differences, not uniform movement toward a center.** Direct structural evidence (de Vivo, Bellesi,
Tononi, Cirelli et al. 2017, *Science*): sleep preferentially shrinks **smaller, weaker** synapses;
larger/stronger ones are relatively spared — not because they're separately "protected," but because
proportional scaling combined with a floor effect hits weak synapses harder. The actual selectivity
mechanism is the **interaction of two processes**: replay actively reinforces tagged-important material
(pulling it away from center) while everything else decays proportionally (not toward center).

**This directly indicts the current implementation.** `downscale_episodic(factor=0.96, center=0.5)`
renormalizes *toward a fixed center* — the literature's mechanism does the opposite of that for anything
worth keeping. Replay and downscale are currently two uncoordinated steps; they should be one mechanism
where replay selection **is** the thing that exempts material from downscaling.

### 1.3 Active systems consolidation — NREM vs. REM, and what dreaming is actually for
**[well-established framework]** Diekelmann & Born (2010, *Nat Rev Neurosci*): hippocampal sharp-wave
ripples during NREM replay the day's encoding, temporally coupled to cortical slow oscillations and
sleep spindles, progressively transferring traces to cortex. Replay is **biased toward salient,
rewarded, or tagged-important material** — not indiscriminate — which is the actual mechanism section
1.2's selectivity depends on.

**NREM vs. REM have different jobs [well-established at the division-of-labor level]:**
- NREM: hippocampal replay, declarative/episodic systems consolidation.
- REM: procedural consolidation, emotional processing, and loose associative integration — a distinct
  neurochemical state (notably low noradrenaline) that the field treats as functionally separate from
  NREM's replay mechanism, not a variant of it.

**What dreaming is FOR — four competing accounts, genuinely contested, not to be presented as settled:**
1. **Depotentiation / "sleep to forget, sleep to remember"** (Walker & van der Helm, 2009, *Psychol
   Bull*) — REM's low-noradrenaline state is proposed to strip the *affective charge* from a memory
   while retaining its *informational content*. **This is the theory most directly relevant to the
   dream-looping bug**: the theory's own account of failure is that insufficient/disrupted REM leaves
   the charge un-stripped, predicting exactly the "keeps recurring, never resolves" pathology PTSD/
   nightmare research documents — a near-exact match to the 51-night carried arc finding 1 (08-22 audit)
   and the current 23-nights anomaly (§0.2).
2. **Threat simulation** (Revonsuo, 2000) — dreams rehearse threat-response offline; predicts (and
   empirically dream content shows) a negative-affect bias beyond waking mood.
3. **Problem-solving/insight** — reduced prefrontal top-down control during REM permits looser
   associative recombination (Cai et al. 2009, *PNAS*; Wagner et al. 2004, *Nature*).
4. **Schema integration** (Lewis, Knoblich & Poe, 2018) — dream bizarreness as a feature, promoting
   integration of new material into existing associative networks.

Current reviews treat these as complementary, not competing. For design purposes: **theory 1 is the one
that motivates an explicit resolution/release condition**, which is the missing piece.

### 1.4 Genuinely unresolved vs. merely frequent — the construct the current design conflates
This is the section that most directly diagnoses the chronic-mass bug.
- **Habituation [well-established]**: repeated *non-reinforced* exposure should produce *decreasing*
  response. A frequent, emotionally-neutral, ambient theme (thermal energy near a hearth) should be
  habituating — going down with repetition — not accumulating. A flat per-touch bump is, mechanistically,
  the *opposite* of habituation.
- **Rumination vs. reflection** (Trapnell & Campbell, 1999) — the actual studied distinction for
  "unresolved" content, and it is **not about frequency**. The discriminators are: (a) threat/loss
  relevance of the content, and (b) **trajectory across repetitions** — does each re-engagement show
  movement (new appraisal, partial resolution) or is it stereotyped, unchanging replay? Rumination is
  *defined* by lack of productive movement across repeats — this is the dream-looping bug described from
  the clinical-psychology side, independently of the neuroscience account in §1.3.
- **Zeigarnik effect [well-established but narrower than folklore suggests]** — incomplete/interrupted
  tasks are better remembered than completed ones; real, but about goal-interruption specifically, with
  real replication/boundary caveats — don't over-lean on it.

**What a principled "genuinely unresolved" signal needs, per this literature:** (a) a valence/threat
component, not just recurrence; (b) a trajectory component distinguishing stereotyped repetition from
development; (c) an **engagement-triggered decay** distinct from passive time-decay — something must
explicitly reduce charge when a dream or waking reflection productively engages the material. The
current formula has time-decay only. Touching a tension in a dream currently isn't wired as a resolution
signal at all — which is very plausibly *why* dreaming about something repeatedly never reduces it.

### 1.5 AI/continual-learning precedent — corroborating, and naming a real gap
**[well-established as an active subfield]** Complementary Learning Systems theory (McClelland,
McNaughton & O'Reilly, 1995) is the original biological-sleep-replay analogy applied to catastrophic
forgetting in neural nets. Generative replay (Shin et al. 2017) and spiking-network "sleep replay
consolidation" work (Tadros/Bazhenov et al., architecture worth locating directly rather than trusting
recall on exact venue) both converge, independently of the biology, on: **selective/biased replay beats
uniform replay** for both efficiency and effectiveness — direct AI-side corroboration of §1.2's
selectivity requirement.

**The gap worth naming explicitly:** this ML literature optimizes for *retention* (don't forget old
tasks), not for *resolution* (this specific memory should stop demanding replay once processed). That
problem — a stopping/release criterion — has no ML-native answer; it's the clinical rumination/reflection
literature's territory (§1.4), not the continual-learning literature's. Worth stating plainly in this
doc: **the AI precedent tells us how to make replay selective; it does not tell us when something should
be allowed to stop recurring. That has to come from §1.4.**

### 1.6 Day residue and the dream-lag effect — how far back dream material should actually reach
**Founder ask, this session:** *"I am thinking dreams should be multiple days worth of thoughts. Not
always tensions."* Checked against the live code first, not just the literature: `dream_node.py:436`
sources material via `since = sleep_pressure.last_fire_ts()` — **since the last sleep only.** At the
cadence measured this session (sleeps every 30–90 min through a cluster, several per day), that window is
routinely under two hours — nowhere near even a single full day, let alone multiple. And
`_load_top_tensions()` (`dream_node.py:439`) is called **unconditionally on every dream** — not one
optional source among several, a standing default every single time. The founder's read of the current
behavior is exactly right, verified against the actual lines.

**[well-established, specific, and more directly relevant than §1.3's systems-consolidation timescale]**
The literature has a named finding for exactly this: the **dream-lag effect** (Nielsen, Kuiken, Alain,
Stenstrom & Powell, 2004, *Sleep*, "Immediate and delayed incorporations of events into dreams"; replicated
in several follow-ups). When dreamers are asked to match dream content against a daily log of waking
events, the rate of incorporation across days-prior is **bimodal, not monotonic**: a peak for events from
**1–2 days prior** ("day-residue effect" — the classical, intuitive result), a **trough at 3–4 days
prior**, and a **second peak at roughly 5–7 days prior** (the dream-lag effect proper). This second peak is
the empirical evidence for "multiple days" as a real property of dream material, not just a design
preference — and it's a distinct, more fine-grained finding than §1.3's systems-consolidation account
(which describes a much slower, weeks-to-months hippocampal-to-cortical transfer). The two aren't in
conflict — dream-lag is thought to reflect an intermediate-timescale memory process operating *within* the
broader systems-consolidation arc — but dream-lag is the right citation for *this specific* design
question (how wide should the material window be), not the slower one.

**Implication for material sourcing:** the window should be reshaped from "since last sleep" (a couple of
hours) to a genuine multi-day pull with the bimodal shape above — weighted toward the last 1–2 days
*and* toward ~5–7 days prior, with less weight in between — rather than either a single cutoff or a flat
lookback. This is a real, citable, non-arbitrary curve to implement against, not a round-number guess.

**Implication for tensions:** "not always tensions" is the correct read of what real dreams mostly are.
Day-residue/dream-lag incorporation is about *ordinary* waking content — most of what gets incorporated
into most dreams isn't a flagged unresolved conflict, it's whatever was salient in the preceding
1–2-and-5–7-day windows, tension or not. §2.2 (below) already frames Dream's own charge signal as
*separate* from Sleep's trigger — this extends that: **tension-inclusion should be conditional on genuine
charge being present (§1.4's valence/threat gate), not a standing default block called on every dream
regardless.** Most nights, most dreams, should be able to run on pure day-residue/dream-lag recombination
with zero tension component, exactly like most real dreams are mundane rather than conflict-resolution
work.

_[original lines 619-691]_

Backup of every touched file before editing: `data/backups/pre_sleep_redesign_20260824_215527/`
(no git in this project). All 12 touched files verified `py_compile`-clean; `should_sleep()`,
`dream_lag_material()`, `update_chronic_mass()`/`_touch_charge()`, and `SomaticEngine.recover(depth=)`
each smoke-tested directly against live data/DB this session (not just compiled) — see chat log for the
actual runs. **Not yet exercised on a live running process** — Du was stopped for this work.

### Files changed
- `core/sleep_pressure.py` — full rewrite. Chronic mass removed from `P` (informational only now).
  `NIGHT_THRESHOLD=10.0` / `DAY_THRESHOLD=100.0` replace `P_THRESHOLD × factor` (recalibrated against
  25,415 real logged rows — see §1's derivation). `DAY_MAX_WAKE_SECS` lengthened 5h → 14h. New
  `POOL_FLOOR_P=5.0` marks (never blocks) a thin-material fire via `info["pool_thin"]`.
- `core/tension_ledger.py` — `CHARGE_WEIGHTS` table + `_touch_charge()` (reads the already-existing
  `shadow_events.emotion_primary`, no new capture). `update_chronic_mass()` now bumps proportional to
  charge, or applies `HABITUATION_FACTOR` extra decay on a sub-floor touch instead of bumping at all.
- `core/night.py` — new `dream_lag_material()` (+ `day_material()` gained an optional `until_ts` bound it
  needs). Hardened the `CARRY_MAX_NIGHTS` check to fail loudly and fail SAFE (clear the carry) instead of
  silently swallowing exceptions — the 23-nights anomaly's root cause is still unknown, per the founder's
  "harden now, root-cause later" call.
- `core/somatic.py` — `recover()` gained a `depth` parameter; recovery is now proportional to actual
  accumulated deficit × depth, replacing the old flat `ENERGY_RECOVERY`/`FATIGUE_RECOVERY` amounts.
- `core/memory/store.py` — `downscale_episodic()`'s default `center` lowered `0.5 → 0.1` (one parameter,
  see the function's own docstring for the full SHY reasoning — the existing proportional-decay math was
  already right, the fixed midpoint was the actual bug).
- `nodes/dream_node.py` — `_gather_materials()` now calls `dream_lag_material()` instead of
  `day_material(since=last_fire_ts)`; `_load_top_tensions()` gained `require_charge=True` gating on new
  `TENSION_CHARGE_FLOOR=1.0`.
- `nodes/inner_monologue_node.py` — real `should_sleep()` reason threading (fixes the stale "N idle
  thoughts" log line); `pool_thin` threaded onto `state` so the sleep callback can go light; chapter/
  journal formation skipped on a thin-pool sleep.
- `core/orchestrator.py` — `_nightly_sleep()` skips dream generation on `pool_thin`; computes recovery
  `depth` (nap → ×0.5, thin-pool → ×0.5, both stack) and passes it into `somatic.recover()`.
- `core/homeostasis.py`, `core/arousal.py`, `hud/server.py`, `hud/static/app.js`, `scripts/du_pulse.py` —
  fixed four consumers of the now-removed `sp.P_THRESHOLD` constant to read each logged row's own actual
  day/night threshold instead (strictly more accurate than the old flat approximation these already were).

### Two real deviations from §4's original build spec — made during implementation, not pre-planned
1. **The pool gate does not HOLD a sleep back (as §4 item 9 originally specified) — it makes the sleep
   LIGHT instead.** Working through the actual numbers: `should_sleep()`'s night/day thresholds already
   sit above `POOL_FLOOR_P`, so a pressure-fire can never itself be pool-thin — only a ceiling-fire can.
   Holding a ceiling-fire back on thin material would have reintroduced exactly the starvation risk the
   un-starvable ceiling exists to prevent. Instead: the ceiling still fires unconditionally (unchanged,
   still un-starvable), and `pool_thin` makes THAT firing skip chapter/journal/dream — cheap instead of
   delayed. Safer, and still delivers the same real goal (a near-empty sleep stops costing a full 20-25
   minute pipeline).
2. **Fatigue's second wiring point (§2.4/§4 item 13, "feeds the small/big dream axis") was NOT built.**
   It depends on dream cycle-position tracking, which is §4 Stage 6 item 17 — explicitly deferred by the
   founder's own scope choice tonight ("Stages 0-5 only"). What WAS built instead: fatigue wires into
   recovery `depth` (item 12), which is a real, working, felt consequence on its own — a hard day still
   produces a measurably bigger recovery at night (smoke-tested: depth=1.0 recovered energy 0.30→0.79 vs.
   depth=0.25's 0.30→0.42, from identical starting debt). The dream-size wiring can be added later once
   Stage 6's cycle-position concept actually exists, without touching this piece.

### Not done, listed honestly
- §4 Stage 2 item 8 (extending `material_sources` to a third value distinguishing which dream-lag peak
  supplied material) — only partially done: the tag changed from `"day"` to `"day_residue"`, but the two
  windows aren't yet distinguished from each other in the log. Lower-priority per §3.3's own framing;
  deferred.
- The 23-nights carry-cap anomaly itself remains un-root-caused (hardened, not fixed at the cause) —
  per the founder's own explicit call this session.
- §4's open questions 9 (which process is "after school, ~10 min") and everything under Stage 6 — not
  attempted, out of tonight's chosen scope.
- **`sleep_pressure_log.jsonl`'s historical rows now mix two schemas** (pre-tonight rows have the old
  `P` that included chronic mass; post-tonight rows don't) — any future analysis of that file needs to
  filter by `ts` against tonight's cutover, not treat the whole file as one consistent series.

### Recommended before restarting Du
1. Skim this log against the actual diffs if anything looks off — better now than after a live run.
2. Consider filing a real `docs/decisions.jsonl` entry for tonight's build authorization (Status header) —
   this document is thorough but isn't the ledger, and the standing rule elsewhere in this project is that
   a ruling only counts once it's recorded there.
3. First restart is worth watching semi-closely — this touched the trigger, the material source, the
   downscale mechanism, and the recovery mechanism all in one night. Check `nascence.log` for the first
   `entering Sleep State` line and confirm it reports a real reason, not `reason=?`.
