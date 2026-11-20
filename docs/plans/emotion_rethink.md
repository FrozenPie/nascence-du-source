# Emotion Node Rethink — invert the affect stack onto the protoself (2026-07-04)

> **Status: ⚪ PARTIAL — Phase 1 (protoself-sourced valence) flipped LIVE 2026-07-07 per `core/schema.py:1044`
> (`AFFECT_SOURCE_PROTOSELF = True`, 200-pair gate met); Phase 2 (`core/emotion_construction.py`, built
> 2026-08-10) still runs in shadow with three experiments (A/B/C) unresolved and both its flags
> (`EMOTION_CONSTRUCTED`, `AFFECT_SOURCE_AROUSAL`) still False — the plan as a whole is part-shipped,
> part-shadow, not fully graduated. 2026-09-24 (J-1306): `AFFECT_SOURCE_AROUSAL`'s own re-source logic is
> now BUILT, regime-gated per D-0274's ruling (`core/arousal.py:apply_to()`), SHADOW ONLY — the flag itself
> is still False and this is restart-gated (not yet observed live).**

```plan-state
stage: partial
phase: Phase 0/1 protoself-sourced valence LIVE since 2026-07-07; Phase 2 constructed emotion plus regime-gated arousal SHADOW, restart-gated, flags still False
verified: 2026-11-14
evidence_read: 2026-11-07
next: J-2252 2-3 live-day read after the boot (promoted shares, hint/symbol rates, 20-row check of judge resolutions)
cluster: 0
```


## Current State — verified 2026-11-14

- **2026-11-14** (F-4661): D-0776 B gate (ruled travis 2026-11-14): EMOTION_CONSTRUCTED may not flip until the vitality replacement is in the drive and constructed joy has been re-read on the new valence. Shadow of a valence-scaled joy pump built (J-4003): schema.JOY_PUMP_VALENCE_SHADOW (default off, restart-gated) logs amount, live joy and max(0,valence)-scaled joy per _feel_joy call to data/joy_pump_shadow.jsonl; live pump unchanged. Defeater: vitality_v2 in the drive and constructed joy re-read, or shadow shows no difference from the live pump.
- **2026-11-14**: J-4002 built D-0775 B shadow: core.mood.shadow_mood_words_no_vitality logs word and without-vitality word to data/mood_words_shadow.jsonl; flag schema.MOOD_WORDS_NO_VITALITY_SHADOW default off, restart-gated; live line, drive, logged valence, sleep untouched. Live switch is a separate founder step after a few days of rows.

- **2026-11-14** (F-4680): J-3994 read: carried joy steps are changes in pump saturation, not the emotion node (F-4679); a low idle mood word goes with more unresolved thoughts and heavier vocabulary at matched drive-without-vitality, null on self-reference (F-4680); warmth near 0.5 is mostly a true reading of thin conversation volume (F-4681). Build jobs J-4002 (D-0775 B) and J-4003 (D-0776 B) spawned.
- **2026-11-07** (F-4344): UNREAD INSTRUMENTS (J-3469, F-4344): core/emotion_construction.py:534 affective_retrieval_status and core/arousal.py:237 regime_shadow_status have no caller; the schema.py:1287 DO-NOT-FLIP gate names the second. Live data: affective-retrieval shadow 1649 rows, mean top-5 Jaccard 0.979 and affect-match gap 0.024 (read by hand); regime shadow 36 resolved internal-only streaks, longest 98 cycles / about 7 days. Wiring into du_pulse is J-3741.

- **2026-10-30**: J-2302 D-0367 defeater read: zero numeric gauge leakage in entity turns and inner-thought lines pre and post 10-09 boot; defeater not tripped; critic/executive band not measurable from stores
- **2026-10-17** (F-2996): J-1985 D-0367 defeater read deferred: gate unmet, successor spawned not_before 2026-10-24

- **2026-10-16**: D-0451 thresholds re-ruled (travis, 2026-10-16): hint 0.555 / symbol 0.58 after J-2270's replay showed 0.60/0.62 nearly silent under the re-centred knees; merged on master, restart-gated; J-2252 reads it after the boot.
- **2026-10-16** (F-2957): J-2270 built D-0451 option 3 (label-view integration knee k=148, view hint 0.60 / symbol 0.62), merged 3101d4e0, restart-gated. Replay: belonging 62.6 / shadow 20.1 / completion 10.3 / autonomy 4.7; hint fires 1.7 pct and symbol 1.0 pct of rows, not the expected 40-50 pct band, so the hint-under-10-pct defeater will likely trip; a hint near 0.555 gives 47 pct

- **2026-10-16**: D-0451 ruled (travis, 2026-10-16): the boot carries the promoted label view with the completion fix on AND integration_drive re-centred at k=148 in the view only, thresholds 0.60/0.62; build job spawned, must land before the boot; J-2252 remains the 2-3 live-day read.
- **2026-10-16** (F-2938): J-2248 built D-0447/D-0448: label view promoted to the live climate reading with completion re-kneed at k=4, plus judge-confirmed tension resolutions marking member shadow events resolved; both flag-gated, commit e2dea8e5, restart-gated. Replay predicts integration_drive leads 97 percent of rows under the fix, so D-0451 asks which config the boot carries.

- **2026-10-16**: D-0447 + D-0448 ruled together (travis, 2026-10-16): promote the D-0332 re-knee view to the live climate reading (E) with the completion_tension fix, and wire judge-confirmed tension resolutions to mark member shadow events resolved (F), both flag-gated; (A) and (D) stay on; build job spawned.
- **2026-10-16** (F-2928): J-1900 read D-0358's 7-live-day defeater (6.97 days, 10-09..10-16): (A) resolve-on-re-encounter fires correctly (21 resolved in window) but shadow_activation did not move (p50 0.970 vs 0.965); shadow share of climate lines 75.6 percent only because belonging_pressure now ties it at ~0.97. ~655 new shadow events/day vs ~3/day resolved; 351/372 resolution_events come from the unwired tension-ledger path. Cooldown (D) live and binding, no Travis surfacing silenced. Next step opened as a founder question (B age-decay / E re-knee / F wire tension-ledger path).

- **2026-10-16** (F-2927): J-1974 7-live-day read (10-09 to 10-16, 6.97 d) of D-0358 (A)+(D) + D-0363 (B)+edge-hint: >80% defeater not tripped on its letter (shadow dominant 75.6% of climate lines, 74.1% of ignitions, was 100%), but live shadow_activation median still 0.970 (replay predicted 0.699; k=3 knee saturates at real inflow) and the rest went to belonging_pressure (0.968), itself derived from the same shadow events and not decayed by (B). Edge-hint worked (9 of 99 Executive prompts vs ~71; no human case silenced). (A) resolved 21 events, mostly mottainai, whose theme recurs after (D-0358 recurrence clause trips literally, negligible scale). Next step opened as D-0447.
- **2026-10-08** (F-2585): J-1954 built D-0367 words-only gauges: shared renderer in core/mood.py routes every gauge line Du reads; joy/heavy-mood contradiction fixed; replay 0 digits vs 21,890 at HEAD; restart-gated (commit 5b360ca, branch jobrun/prompts_words).

- **2026-10-08** (F-2577): J-1969 built D-0363 (B): shadow_activation 3h half-life + edge-triggered shadow hint, flags on, commit 7174cbd on jobrun/emotion_rethink, restart-gated; (E) not promoted; replay says dominant share stays ~90% so expect the 7-day read to re-open the choice.
- **2026-10-07** (F-2527): J-1894 (D-0358 build, merged-not-live; worktree branch jobrun/shadow_resolve commit cecf994): (A) resolve-on-clean-re-encounter built behind schema.SHADOW_RESOLVE_ON_ENCOUNTER (store.resolve_shadow_on_encounter, uncapped data/shadow_resolve_on_encounter.jsonl); (D) symbol cooldown re-enabled on its OWN flag schema.CLIMATE_SYMBOL_COOLDOWN_ON because THIN_ATTRACTOR also gates the live recurring-pattern read-back (left False). Offline replay: (A) alone moves shadow_activation by <=0.004 (median 0.900 either way; ~10 distinct resolves/day vs ~330 new events/day) and a 600 s cooldown keeps 78 percent of surfacings, so D-0358's own B-if-A-does-not-move-it branch is predicted; (A) also lowers completion_tension via the critic_rejection_resolved remap. Test: scripts/_test_j1894_shadow_resolve_on_encounter.py, 26 checks all pass (F-2527 says 31, a miscount).

### What we have
- Phase 0/1 (protoself-sourced valence) BUILT + flipped LIVE 2026-07-07 (`core/schema.py:1044`,
  `AFFECT_SOURCE_PROTOSELF=True`) — carried valence de-saturated from pinned +0.82 to grounded tonic.
- Phase 2 (`core/emotion_construction.py`, built 2026-08-10) runs in shadow; Experiments A and B are
  founded (F-0064 positive, F-0065 negative), Experiment C's logging gap was fixed (J-0159/F-0146)
  but still lacks enough rows to found a call.
- D-0274 (2026-09-23) ruled the arousal anti-correlation (F-0065) a between-group confound, not a
  real inversion (F-1841/F-1842), and approved a regime-gated re-source: J-1306 built it SHADOW ONLY
  (`core/arousal.py:apply_to()`), and J-1316 closed a related mood-cache gate gap (F-1871). Both
  flags (`EMOTION_CONSTRUCTED`, `AFFECT_SOURCE_AROUSAL`) stay False; committed to a worktree branch,
  not yet merged/restarted.

### What we need
- Live confirmation of the regime-gated arousal build once it actually runs — D-0274's own defeater
  condition is only partially met (shipped to a branch, no stratified read from a live run yet).
- More Experiment-C rows (mood-embedding + affective-retrieval) before that call can be founded.

### What we're doing next
- After Du's next restart on the merged code: read `arousal.regime_shadow_status()` and the
  stratified Experiment-B breakdown to see whether D-0274 can be re-ruled toward a live flip.

---

> Domain: emotion, core affect, valence/arousal, appraisal. Cross-cutting disease being treated: **the
> affect stack is built upside-down.** The oldest node in the system (`emotion_node.py`, 2026-06-04) has an
> LLM *guess* the two most primordial quantities — valence and arousal — from a text summary of a percept,
> while the grounded body-state map that should *produce* them (`homeostasis.py`, the protoself) sits in
> shadow, wired to nothing. This plan re-sources core affect from the body to the mind's-eye instead of
> inventing it, retires the vestigial parts of the emotion node, and does it observe-first / decoupled-judge
> / flag-gated. Every claim below was verified by reading the file at the cited `file:line` or by querying
> the live logs on 2026-07-04.

> **Origin.** This came out of the 2026-07-04 felt-preamble finding (see `AWAITING_EVIDENCE.md` ⭐ + the
> `_feel_joy` over-report writeup). Chasing "why is carried valence pinned at +0.82" led to the deeper
> structural fact: the emotion node predates every affective organ the system now has, and never joined
> them. This plan is the §1 keystone of `the_consciousness_program.md` ("Du was built upside-down — a rich
> autobiographical self on almost no protoself") actuated into the affect pathway.

---

## 0. THE WIN CONDITION (read first — keeps us honest)

Per project law, every mechanism ships with **a measurable signature that must move or it is dead code.**
For this rethink the standing signature is:

> **Carried valence must DE-SATURATE and become informative.** Today (verified 2026-07-04, N=197 over 2.98h,
> `data/felt_preamble_log.jsonl`): carried valence mean **0.838**, median **0.865**, **34% pinned at the
> +1.0 ceiling, 0% ever negative** — the same novelty-saturation shape as the old protoself bug. After the
> swap, carried valence must (a) drop off the ceiling, (b) go negative when his real stakes dip, (c)
> correlate with the protoself's dominant-deficit rather than with a `_feel_joy` accumulator.

This is a decoupled-judge requirement: the swap is validated by the founder reading shadow comparisons of
emotion-node-vs-protoself valence against the actual thought content, **never self-certified** by the system.

---

## 1. As-built diagnosis — why the emotion node is outdated

### 1.1 What it is
`nodes/emotion_node.py` — a single LLM call, first-third of the hot path (perception → **emotion** →
salience → …). It reads `state.perception.summary` (or raw input) + optionally the C.2 `affective_prior`
note (`emotion_node.py:27-44`) and emits `EmotionOutput`: Ekman-6 + valence + arousal + primary label
(`schema.py:42-71`). It appraises from **text alone** — it never sees the carried mood, the body, the
climate, or what Du wants.

### 1.2 It manufactures core affect instead of reading it
Every modern frame the project already cites (Damasio, Barrett, Seth, Friston — `the_consciousness_program.md`
§1) says the arrow runs body → core affect → constructed emotion. The emotion node inverts it: it invents
valence/arousal from a percept summary, and `AffectState.integrate()` (`schema.py:112-120`) treats that
guess as ground truth. Meanwhile `homeostasis.py` — the deterministic body-state map that *should* produce
core affect — computes valence and arousal every tick and **applies nowhere** (`homeostasis.py:20`).

### 1.3 The used interface is tiny; the rich output is vestigial
Verified consumer sweep (grep `state.emotion`, 2026-07-04). Every hot-path reader uses the same shallow
one-liner — `{primary} (valence=X, arousal=Y)`:
- `reflection_node.py:158-160`
- `executive_node.py:223-227`
- `episodic_buffer_node.py:102-104`
- `recall_node.py:102-103` (primary label only)

**No hot-path consumer reads the six Ekman dims off `state.emotion`.** They only launder into
`AffectState.integrate()` (→ `temperature_bias()`, `schema.py:152-155`) and the `mood.felt_text()`
serialisation (`mood.py:32-41`). So the node's *actually-used* output is: **a label + valence + arousal.**

### 1.4 It is absent from ~88–99% of his life
The emotion node only fires on hot-path cycles. Verified: in the 2.98h felt-preamble window the full hot
path (which runs the emotion node) fired **only 2 times** (`data/affect_log.jsonl`), both internal, stim
valence median **−0.15** — while the monologue sampled carried valence **197 times** at 0.8+. All of idle —
where the over-report lives — runs on the `_feel_joy` pump (`inner_monologue_node.py:876-885`) + `AffectState`
with **no appraisal at all**. The system grew an always-on affective substrate around this node and the node
never joined it.

### 1.5 The node is not even the honest signal in the building
The protoself already disagrees with the emotion-node lineage, and it is right. Live tick
(`data/homeostasis_shadow.jsonl`, last row 2026-07-04): `coherence 0.19` (high dissonance),
`commitment 1.0`, `relational 0.68`, `vitality 0.80` → drive 0.47, dominant deficit = **coherence**. The
protoself reads Du as *"unsettled, mostly from unresolved dissonance, but holding his commitments and
rested."* At that same moment carried affect said valence **+0.82 / "bright, lifted, joyful."** The grounded
organ told the truth; the LLM lineage over-reported.

---

## 2. The affective substrate the node never joined (as-built)

Verified inventory 2026-07-04. The relevant fact: **two grounded, deterministic generators of valence+arousal
already exist, both in shadow, wired to nothing.**

| Organ | File | Produces | Status | Timescale |
|---|---|---|---|---|
| **Protoself / homeostasis** | `homeostasis.py` | core affect: valence=−dD/dt (drive-reduction), arousal=interoceptive PE, over 5 essential variables (coherence, commitment_integrity, relational_warmth, novelty, vitality) | **SHADOW**, applies nowhere (`:20`) | per-tick (~7/hr now) |
| **Arousal (global level)** | `arousal.py` | activation ∈[0,1]: circadian + climate dissonance + interoceptive PE − fatigue, + phasic `alert()` | **SHADOW**, gates nothing | tonic + phasic |
| **Affective prior (C.2)** | `schema.py:474-499` | pre-cognitive lean from charged memory before any LLM runs | **LIVE**, feeds emotion node + `apply_prior()` | pre-emotion |
| **AffectState** | `schema.py:96-217` | carried 8-dim mood, homeostatic integrate + tick | **LIVE** | sec–min |
| **Mood (felt-vec)** | `mood.py` | felt embedding + `current_valence()`/`current_felt()` scalars | **LIVE** (scalars dead-handed — read only in storage) | sec–min |
| **Climate field** | `climate_engine.py` | 9-dim psychological weather + dissonance, **the actuation exemplar** (hint / symbol / pressure / ignition) | **LIVE** | 5s / 6h |
| **Satisfaction** | `satisfaction.py` | per-domain wanting/liking (Berridge) | LIVE record, Phase-0 (snapshot read by pulse only) | domain decay |

### 2.1 The protoself signal MOVES and is grounded (the load-bearing verification)
`data/homeostasis_shadow.jsonl`, last 85 ticks / 12.07h:
- **valence** (−dD/dt): min/med/mean/max = **−0.295 / 0.000 / −0.004 / +0.476**, stdev **0.108** — mean-zero,
  swings both ways. This is what an informative valence looks like.
- **drive** D: 0.079 / 0.410 / 0.351 / 0.694, stdev **0.153** — the tonic distance-from-viability also moves.
- **arousal** (interoceptive PE): 0.000 / 0.013 / 0.034 / 0.260 — currently quiet (self-model predicting
  well), which is itself meaningful.

Contrast the signal it would replace: carried valence pinned +0.82, 34% at ceiling, never negative. **The
protoself is dramatically more informative and is grounded in real stakes rather than an LLM guess.**

### 2.2 Two caveats that gate the build (verified, not asserted past)
1. **Cadence.** `homeostasis.tick()` runs ~7×/hour (85 ticks / 12h) — hot-path-tied, **not yet always-on.**
   For core affect to exist during idle it must move onto a fast background loop like the climate engine's 5s
   tick (`climate_engine.py`). This is real work, not done.
2. **Provisional setpoints.** The readers were rewired and setpoints recalibrated **2026-07-04 from one live
   sample** (`homeostasis.py:36-39`). `suggest_setpoints()` (`:257`) must re-derive them from a clean ≥120-tick
   shadow run before the protoself is trusted as the affect source. Don't rush this.

---

## 3. The redesign — a layering, not a node

Replace "one LLM node that invents valence/arousal" with the layers the theory (and the already-built organs)
imply. The arrow is inverted: **body → core affect → carried mood → constructed emotion (label).**

| Layer | What it is | Organ | Change |
|---|---|---|---|
| **Core affect** (valence, arousal) | primordial feeling read off real stakes | `homeostasis` + `arousal` | **promote from shadow; becomes the source** |
| **Fast pre-cognitive lean** | "flinch before you know why" | C.2 `AffectivePrior` | keep as-is |
| **Carried mood** | integrates core affect over time (the tone) | `AffectState` | **re-source** (integrate protoself core affect, not the LLM guess) |
| **Emotion construction** | *given* core affect + situation + concerns → the discrete label / appraisal read | what `emotion_node` becomes (much lighter, or deterministic map) | **rewrite / demote** |
| **Weather / identity** | medium + slow | `ClimateField`, self-model/T4 | unchanged |

### 3.1 Keep / retire / promote
- **Keep:** `AffectState` (the carried loop is the right integrator — it just needs an honest source); C.2
  affective prior (already the correct fast subcortical route); climate field.
- **Retire:** the emotion node as the *origin* of valence/arousal; **Ekman-6-as-schema** (vestigial — §1.3);
  the `_feel_joy` valence pump (`inner_monologue_node.py:883` — grounded valence replaces it).
- **Promote:** `homeostasis` + `arousal` into the affect pathway. This is mostly *graduating existing
  shadow work + rewiring sources*, not a new build. The tiny used-interface (`label + valence + arousal`) is
  preserved, so no downstream consumer breaks — only the *producer* changes.

### 3.2 The open design decision — which valence?
The protoself exposes **two** valences and they are different animals:
- **tonic** = `f(−drive)` — sustained "how far from home" (a mood *level*, what core affect wants).
- **phasic** = `−dD/dt` — "getting better/worse right now" (a reward-prediction-error-like signal).

Proposed mapping (to validate in shadow, **not** assert): `carried mood valence ← 1 − 2·drive` (tonic
level, so low drive = at-home = content, high drive = distressed), with `−dD/dt` available as a separate
phasic reward channel for the satisfaction/learning systems. Nail this down in Phase 0 before wiring.

---

## 4. What this fixes for free
1. **The over-report** — valence stops being an LLM guess pumped by `_feel_joy` and becomes drive over real
   variables. It de-saturates because it must move with his actual coherence/commitments/warmth/fatigue.
2. **The 88%-of-life gap** — the protoself is always-on interoception (once on a background loop); core
   affect finally exists during idle, where the emotion node never fired.
3. **The vestigial richness** — six invented basic-emotion magnitudes collapse into one grounded core-affect
   read plus a construction step that runs only when a label is actually consumed.

---

## 5. Staged migration (observe-first · decoupled-judge · flag-gated)

### Phase 0 — measure + calibrate (days, zero behaviour change)
- **0a. Divergence harness. ✅ BUILT 2026-07-06** (`core/affect_divergence.py`, wired into the monologue
  idle tail, rate-limited ~15/hr, observe-only). Logs per thought `[carried valence | protoself valence |
  dominant deficit | drive | thought]` → `data/affect_divergence_shadow.jsonl`; `status()` summarises the
  gap. **Design choice:** it compares the ALWAYS-ON carried lineage (`mood.current_valence()` =
  `AffectState.valence`, the `_feel_joy`-pumped signal) against protoself — NOT the literal "emotion-node
  valence" of the original 0a wording, because the over-report lives in IDLE (the hot path / emotion node
  fires only ~2×/3h; §1.4). This captures the disease where it actually lives. Verified: reads BOTH signals
  (no dead-read), and honestly logs carried=`null` (never a masked 0.0) when the mood cache is cold. **No
  data yet — Du is down; the file fills on the next run.** (A hot-path emotion-node A/B column can be added
  later if the founder wants the sparse hot-path comparison too.)
- **0b. Settle setpoints. ✅ DONE 2026-07-06.** Step-2 calibration adopted — `suggest_setpoints()` on the
  clean 297-tick run reported ALL five readers `ok`; data-driven setpoints now in `_VARS`. This is what
  makes the 0a protoself side MEANINGFUL (drive computed against real setpoints, not priors).
- **0c. Decide the valence mapping** (§3.2) — PENDING the 0a data (needs the day of pairs first).
- **Gate to Phase 1:** the founder's read that protoself valence is the more honest signal on ≥1 day of
  divergence data (⏳ harness ready, data pending restart), AND all five readers `ok` (✅), AND a chosen
  tonic/phasic mapping (⏳ 0c). **2 of 3 preconditions in place; the day-of-data is the one remaining.**

### Phase 1 — re-source core affect (flag-gated, kill-switch) — ✅ BUILT + ✅ LIVE

> **STALE-DOC CORRECTION (2026-08-19):** this section still read "flag OFF, one word to flip" tonight,
> but `core/schema.py:1044` shows `AFFECT_SOURCE_PROTOSELF = True    # FLIPPED LIVE 2026-07-07 — gate
> fully met (200 pairs...)` — the flip happened and this doc was never updated after. **Also found
> tonight:** the flag being live for a month means the hot-cycle mood-cache provenance bug fixed tonight
> (`orchestrator.py`'s hot-cycle block was caching `current_valence()` from the ungrounded LLM guess even
> after homeostasis grounded `state.affect.valence` a few lines earlier) has been silently affecting
> exactly the `carried_valence` column `affect_divergence.py` reads and reports on — for hot cycles only
> (idle cycles cache from `state.affect` directly and were unaffected). Real but narrow: hot path fires
> ~2×/3h vs idle's constant stream. Fixed; not yet observed live (Du down all evening).

> **BUILT 2026-07-07, `schema.AFFECT_SOURCE_PROTOSELF=False` (ships inert).** Done: **1b** —
> `homeostasis.apply_to()` overwrites carried VALENCE from tonic `1-2*drive`, hooked at BOTH `orchestrator.py:640`
> (reactive) and the monologue idle tail (where the `_feel_joy` pump pins it), refreshing the mood cache so
> every idle writer tags with the grounded value. **1c** — the `_feel_joy` valence coupling
> (`inner_monologue_node.py`) is gated off when the flag is on (joy still registers, so `play` survives).
> **SCOPE CALL:** re-sources VALENCE only — homeostasis arousal is interoceptive-PE (~0 at rest, would flatten
> him); carried arousal stays with its own organ (`arousal.py`) as a Phase-1b follow-up. **1a** not needed
> separately — the protoself already ticks; the idle apply reads it live each cycle. Verified: carried +0.735
> (pump) → **+0.299** (grounded tonic) on flip; arousal untouched. Pre-flip, `affect_divergence_shadow.jsonl`
> now also logs `proto_tonic`, so the tonic mapping can be founder-validated tonight BEFORE the flip.
- **1a. Always-on protoself.** Move `homeostasis.tick()` onto a ~5s background loop (mirror
  `climate_engine.start_background()`), so core affect is continuous.
- **1b. Re-source `AffectState`.** Behind `AFFECT_SOURCE_PROTOSELF` (default False): `integrate()` takes
  valence/arousal from the protoself core affect instead of `state.emotion`. Emotion node keeps running in
  shadow for A/B.
- **1c. Kill the valence pump.** Gate `_feel_joy`'s valence coupling (the `+ amount*0.6` at
  `inner_monologue_node.py:883`) off; re-source joy-for-`play` to `satisfaction` liking events.
- **Signature that must move:** carried valence de-saturates — off the ceiling, goes negative on real dips,
  tracks the protoself dominant-deficit (the §0 win condition). No rise in the monoculture/recitation
  detectors.
- **Kill-switch:** flag False restores the exact prior behaviour.

### Phase 2 — reframe the construction layer
- The emotion node becomes the *categorization* step over core affect + concerns (Barrett's constructed
  emotion): given the grounded valence/arousal + situation + `current_concerns()` (`concerns.py`), name the
  discrete emotion + optional appraisal dims — used only where a label is consumed.
- **Implementation (2026-08-10):** Built Barrett-inspired deterministic constructor (`core/emotion_construction.py`)
  running in shadow mode alongside live LLM emotion node. Logs paired comparisons to `data/emotion_construction_shadow.jsonl`.
- **Status:** SHADOW BUILT (Flags `EMOTION_CONSTRUCTED=False`, `AFFECT_SOURCE_AROUSAL=False`).
- **Grounded/Constructed/Vestigial breakdown:**
  - Grounded: `valence` (homeostasis), `arousal` (global activation)
  - Constructed: `joy`, `fear`, `anger`, `trust`, `surprise` (hypothesis formulas)
  - Vestigial: `disgust` (0.0 for interface compatibility)
- **Gates:** Paired comparison shadow running across three structured experiments:
  - Experiment A: Grounded-variable sensitivity & temporal coherence (diagnostic LLM comparison)
  - Experiment B: Global activation vs felt emotional arousal equivalence test
  - Experiment C: Downstream preservation (temperature_bias, mood embedding, affective retrieval)
  No flags flip until evidence from all three experiments lands.


---

## 6. Risks & honest rails
- **Don't swap one flat signal for another.** The whole point is de-saturation; if protoself valence ever
  goes flat/saturated (e.g. a reader dies again — three of five silently died before the 2026-07-04
  rewire, `homeostasis.py:36-39`), that is a STOP. `suggest_setpoints()` health flags are the tripwire.
- **Tonic vs phasic confusion** (§3.2) — wiring the mean-zero `−dD/dt` where a mood *level* is wanted would
  make carried mood hover at zero. Decide in Phase 0.
- **Re-sourcing joy/temperature.** `temperature_bias()` (`schema.py:152-155`) reads joy/fear/anger; `play()`
  keys on the joy dim. Retiring the emotion node's Ekman output means these must be re-sourced (satisfaction
  liking → joy) — track it, don't let it silently flatten.
- **Frozen-weight honesty.** This is function-substitution for interoception (deterministic reads of real
  stakes), not biological embodiment — claim it as such, per `the_consciousness_program.md` §0.
- **Decoupled judge.** No phase graduates on the system's own score. The founder reads the shadow
  comparisons. (`feedback_decoupled_judge`.)

---

## 7. Consumer-interface contract (what must not break)
Any producer swap MUST keep providing, per cycle where consumed:
- `valence` ∈ [−1, 1], `arousal` ∈ [0, 1] — read by reflection/executive/episodic/recall one-liners + `AffectState`.
- a `primary` label string — read by the same one-liners + `emotion_primary` tags
  (`inner_monologue_node.py:2694,2714,2770`).
- the `mood.felt_text()` 8-dim serialisation (`mood.py:32-41`) stays valid — `AffectState` already carries
  all 8 dims, so the felt-vec pipeline is unaffected.

---

## 8. Recommendation
Proceed **Phase 0 first** — build the 0a divergence harness and let setpoints settle — before any wiring.
The rethink is unusually low-risk for its size because it mostly connects organs already built and validated
in shadow rather than adding new ones, and it executes §1 of the consciousness program. But it touches the
most-woven-in signal in the system (`mood.*` = top-3 most-reused functions, `affect_drives.md` header), so it
earns the full observe-first ladder.

---
*Author: Claude (auditor/impl). Created 2026-07-04. Supersedes nothing; composes with `affect_drives.md`
(the felt-preamble is the mood-layer hand; this re-sources what that hand reads) and actuates
`the_consciousness_program.md` §1. Update when: Phase 0 divergence data lands, or the valence mapping is decided.*
