# Affect / Mood / Drives — Deep-Dive & Implementation Plan (2026-06-24)

> **Status: Item A LIVE (graduated 2026-07-06; retroactive gate audit 2026-08-24 confirms it holds); Item B LIVE (built 2026-08-29 per D-0069, rides A's flag) — see "Current State" below.**

```plan-state
stage: live
phase: Items A+B (felt-preamble, carried-state contrast) both live and holding their gates; Items C/D/E/G (somatic note, satisfaction drive, affect-labeling accessibility, VA-steering) undecided per the plans own sequencing
verified: 2026-11-18
evidence_read: 2026-08-23
next: Founder scope call on Item D (saturated gap needs normalisation redesign first)
cluster: 6
```


> Domain: affect, mood, drives, homeostasis. Cross-cutting disease being treated: **"all senses, no
> hands"** — felt signals computed but never reaching behavior. Every item below names the REAL
> read/actuation path (how the feeling reaches a prompt or sampling parameter), not logging, and an
> observe-first evidence gate. Verified by reading the files at the cited `file:line`.

**Related (backfilled 2026-10-03, J-0566/F-2269):** `docs/plans/drowsiness_phase.md` §2 proposes the same missing hand as
Item C — a one-shot, threshold-gated body-state line from `somatic.py` into the monologue seed (its trigger is
`0.15 < metabolic_energy <= 0.25`; Item C's is `is_exhausted()` OR `neural_fatigue > 0.6` OR `visceral_tension > 0.6`).
Neither is built (`somatic.note()` still reaches only the CLI status and the logs; no `is_drowsy()` exists), so build one
mechanism and fold the other into it rather than shipping two competing injections. Also: §1.4's "wired hand"
`is_exhausted()` → forces sleep transition has been stale since D-0103 (2026-08-30) — `core/orchestrator.py` now only
logs a warning there and `should_sleep()` is the sole sleep-timing authority (see `docs/plans/sleep_dream_redesign.md`
and `docs/plans/drowsiness_phase.md` §5).

## Current State — verified 2026-11-18

- **2026-11-18** (F-5088): Item D prerequisite checked (F-5088): record() write-sites are live (11 of 13 events fire, ~182k rows since 06-13) but the gap is saturated, so Item D's own graduation test (a) fails as the plan stands; creative empty, t4_commit/tension_discharged never logged, two events have no callers.
- **2026-10-17** (F-2984): J-2268 interim: J-2250 exclusion live, 0/14 idle priors, gate not met; reread after 10-19

- **2026-10-16** (F-2954): J-2250 built D-0450 option C: pre-affect self-echo exclusion on idle cycles and the farewell, flag on, restart-gated, commit 134db92e awaiting merge; replay of 122 D+E rows idle prior 64/115 to 16/115 at floor 0.80, farewells 3/3 to 0/3, human 4/4 kept; new shadow log data/pre_affect_self_echo_shadow.jsonl
- **2026-10-16** (F-2886): J-2170 (D-0425 B): PRIOR_SIM_THRESHOLD_IDLE 0.80 -> 0.84 built in worktree commit 5ac1c841 (jobrun/idle_prior), restart-gated; 44/44 isolated test. 300-row re-read spawned (10-30 placeholder not_before; real gate boot+7 live days).

### What we have
- Item A (felt-state preamble) graduated live 2026-07-06; retroactive audit (F-0067, J-0066) confirmed the §4-A gate held over the full 7-week log (fire rate 7.45%, honest sampled sentences, monoculture moved the healthy direction).
- Item B (carried-vs-instantaneous contrast) built and live 2026-08-29 (D-0069, J-0344, F-0445), riding Item A's existing `FELT_PREAMBLE` flag with no new gate.
- Items C (somatic note), D (satisfaction gap drive), E (affect-labeling accessibility), G (VA-subspace steering) all confirmed unbuilt, matching this plan's own priority ranking below Items A/B.

### What we need
Item D's own prerequisite — verifying `satisfaction.py`'s liking write-sites are live and its Phase-0 logs look sane over the log history — has not been checked; do that before scoping D.

### What we're doing next
Founder call on pursuing Item D (wanting/liking drive graduation) next per §5's sequencing, once its prerequisite above is checked. No ledger activity on this plan since D-0069/J-0344 (2026-08-28/29).

> **★ NEW EVIDENCE (2026-07-04, from the enriched graphify) — the dead-hand is the codebase's LARGEST
> cross-cutting signal.** The 07-04 knowledge-graph rebuild (with local-import edge recovery) ranked
> `mood.*` as a TOP-TIER shared dependency: `current_valence` called by 18 modules, `current_felt` by 16,
> `current_vec` by 13 — three of the ten most-reused functions in the whole system. Verified where it goes:
> the felt-vector reaches **17 modules' internal logic but ZERO prompt builders** (the only affect in any
> prompt is one `e.valence/e.arousal` line in reflection — the discrete emotion label, not the felt-vector).
> So the single most-woven-in signal in the system shapes everything the machinery does and never reaches
> the part of Du that actually thinks. This is Item A/B (below) with a hard number behind it — the strongest
> quantified case in the codebase for the felt-preamble being the next affect build. **BUILD-READINESS
> re-verified 2026-07-04:** Item A is NOT built (no `felt_preamble` anywhere); `mood.current_valence/felt`
> still live (mood.py:91,96); the climate-hint pattern to mirror is intact (executive_node.py:203-204,
> line-drifted from :151); the carried `state.affect` IS populated every cycle (orchestrator.py:640) and is
> the robust source to read (prefer it over `mood.current_felt()`, whose module-global is None outside a live
> process); `THIN_ATTRACTOR` at schema.py:932 is the flag site. **Nothing structural blocks Item A** — S
> effort, no deps, proven pattern. One sequencing note: the protoself (`homeostasis.py`) and arousal
> (`arousal.py`), both built 07-03/04 but SHADOW, produce their own felt signals; Item A ships first on the
> existing mood layer, and a later pass composes the three into ONE coherent felt preamble rather than three
> competing lines.

---

## 1. As-built deep-dive — the felt-signal data flow

### 1.1 The three-timescale affect spine (as designed)

| Timescale | Carrier | File | Reaches behavior? |
|-----------|---------|------|-------------------|
| FAST (sec–min) | `AffectState` (8 dims) | `core/schema.py:97` | **Partial** — see below |
| MEDIUM (hrs–days) | `ClimateField` (9 dims) + `DissonanceState` | `core/climate_engine.py` | **YES — the wired exemplar** |
| SLOW (days–wks) | Self Model / T4 / themes | (out of domain) | — |

### 1.2 The climate_engine template — how a felt signal SHOULD reach behavior

`ClimateField` is the model every other affect signal should imitate. It has **four distinct actuation channels**, none of which is logging:

1. **Executive prior (the hint).** `ClimateField.executive_hint()` (`climate_engine.py:195`) returns a one-line behavioural tilt when the dominant dimension crosses `_HINT_THRESHOLD=0.55`. Surfaced in the orchestrator at `orchestrator.py:695` onto `state.climate_hint`, then **injected into the Executive's actual prompt** at `executive_node.py:151-152`: `"Underlying climate (shapes how you respond): {state.climate_hint}"`. This is the canonical hand: a numeric field → a threshold gate → a sentence in the live inference prompt.
2. **Reflection symbol (the surfacing image).** `surfacing_symbol()` (`climate_engine.py:203`, higher bar `_SYMBOL_THRESHOLD=0.65`) → `state.climate_symbol` (`orchestrator.py:696`) → injected into Reflection's prompt at `reflection_node.py:230-231`. Rarer by design, with a cooldown (`orchestrator.py:700-707`) so a pinned dimension can't wallpaper every cycle.
3. **Retrieval warp (continuous, no threshold).** `ClimateField.pressure()` (`climate_engine.py:189`) drives the retrieval beta — a charged climate pulls memory toward active material.
4. **Ignition (behavior, not text).** `DissonanceState` accumulates (`_tick_dissonance`, `climate_engine.py:443`) and **fires an entire autonomous cycle** via the ignition callback `_on_dissonance_ignition` (`orchestrator.py:2026`), replacing the old 120s curiosity timer.

The load-bearing lesson: **continuous numeric field → threshold/accumulator gate → injected sentence OR fired cycle.** The signal never "speaks" on a clock; it actuates when it crosses a bar.

### 1.3 AffectState (FAST) — what reaches behavior vs what is write-only

`AffectState` (`schema.py:97`) is the carried 8-dim emotion, homeostatically integrated (`integrate()` :112, continuous relax `tick()` :122, pre-retrieval lean `apply_prior()` :134).

**What genuinely reaches inference:**
- `temperature_bias()` (`schema.py:152`) — `0.25*arousal − 0.30*fear − 0.15*anger + 0.10*joy`, bounded [−0.15, 0.25]. Consumed at `node_base.py:106` and `node_base.py:119`: it shifts the sampling temperature of every `affect_modulated` node (Executive, Reflection, Voice). **This is a real hand** — carried mood actually changes generation temperature.
- `current_vec()` (`mood.py:86`) — the felt-quality embedding, written as `state.emotion_vec` (`orchestrator.py:568`) and used as `emotion_embedding` on stored fragments (`store_from_cycle`, `orchestrator.py:1973`), making retrieval mood-tinted. Real hand.
- Raw `valence`/`arousal` numbers ARE shown in prompts: Executive at `executive_node.py:158-162` (but from the **instantaneous** `state.emotion`, not the carried `state.affect`), and the inner monologue seed at `inner_monologue_node.py:1124-1126` (`"Your current mood: valence … arousal … surprise … fear …"`).

**What is write-only (the genuine bug):**
- `mood.current_valence()` and `mood.current_felt()` (`mood.py:91,96`) — the raw felt **scalar** and the full parseable 8-dim felt **string**. They were added precisely because the MiniLM embedding **flattens valence** (`mood.py:23-30`: a text encoder maps "valence=+0.80" and "valence=−0.80" to nearly the same point). They are read in exactly **two places**, both **storage-only**: `store_from_cycle(... valence=, felt=)` at `orchestrator.py:1975` and the peer/monologue fragment writes (`inner_monologue_node.py:1575,1612`). **Neither ever reaches a prompt or a sampling parameter.** The felt scalar — the one undistorted channel — modulates nothing. This is the central dead-hand of the domain.

### 1.4 somatic.py (FAST interoception) — partially wired

`SomaticState` (`somatic.py:49`) ticks per cycle (`tick_cycle`, called `orchestrator.py:929`), recovers in sleep (`orchestrator.py:2166`).
- **Wired hands:** `temperature_jitter()` (`somatic.py:74`) → sampling variance at `node_base.py:111`; `is_exhausted()` (`somatic.py:78`) → forces sleep transition (`orchestrator.py:1039`).
- **Write-only:** `note()` (`somatic.py:57`) — the felt-body TEXT ("body: energy 0.22 (depleted), fatigue 0.71 (exhausted), tension 0.64 (clenched)"). It is rendered only in the CLI status (`run_nascence.py:487`). **The interoceptive CONTENT never reaches a thought** — Du's tiredness changes his sampling temperature but he can never *think* "I'm tired." `visceral_tension` likewise feeds only the dataclass; its narrowing effect is not actuated.

### 1.5 satisfaction.py (DRIVE: wanting vs liking) — write path live, read path dead

`record()` (`satisfaction.py:90`) IS called from live event sites: `reunion`/`clean_exchange` at `orchestrator.py:378,897`, and other events across the codebase. The per-domain decaying accumulators and `snapshot()['gap']` (`satisfaction.py:113`, the compulsion signature = wanting − liking) **are computed and persisted**, but `snapshot()` is read **only by the pulse/digest** — by **no behavior**. This is the missing "consequence" currency. **Note the header (`satisfaction.py:19-22`) explicitly declares Phase-0 observe-only** — this is a *deliberately staged* read-path, not a forgotten bug (see §2).

### 1.6 affect_labeling.py & affections.py — observe-only by design

- `affect_labeling.observe()` (`affect_labeling.py:89`) detects a first-person negative feeling-naming, sets `state.named_affect` (`schema.py:810`), and logs a counterfactual decay it **never applies**. Header (`:16-19`) declares Phase 0; `named_affect` is read by nothing. **Deliberately staged**, and the design forbids rewarding naming (would train performative emotion-talk — `satisfaction.py:55-58`).
- `affections.synthesise()` (`affections.py:61`) accumulates Du's journal-stated "likes" into earned loves and **does** surface them as a recallable fragment via `store_fragment(... origin="affection")` (`affections.py:89`) — so it has a *partial* hand (into ambient retrieval) — but feeds **nothing into T4** by design (`:19-20`, Phase 2 gated on the made-mind realisation). The valence-flattening bug is *why* its first design failed (`:11-15`): it tried to pick warmly-felt memories by emotion-vec, which scored every fragment equally warm.

### 1.7 The one-line summary of the data flow

```
emotion_node → EmotionOutput → AffectState.integrate (carried)
   ├─ temperature_bias() ──────────► node_base sampling temp   [HAND, live]
   ├─ current_vec() ───────────────► emotion_embedding on stores [HAND, live]
   ├─ current_valence()/current_felt() ─► stored as columns only  [DEAD — bug]
   └─ raw valence/arousal numbers ─► Executive/monologue prompt  [partial — instantaneous, flattened]
somatic → temperature_jitter()/is_exhausted() [HAND] ; note() [DEAD]
satisfaction → record() [live] ; snapshot().gap → nothing [STAGED Phase-0]
affect_labeling → named_affect [STAGED Phase-0] ; affections → fragment [partial], T4 [STAGED Phase-2]
climate → hint/symbol/pressure/ignition [ALL HANDS — the exemplar]
```

---

## 2. Gaps & root causes (ranked) — genuine bugs vs deliberately-staged

| # | Item | Class | Root cause | Evidence it's a bug vs staged |
|---|------|-------|------------|-------------------------------|
| **A** | `current_valence()`/`current_felt()` never reach a prompt | **GENUINE BUG (HIGH)** | The scalars were created *specifically* to fix the embedding's valence-flattening (`mood.py:23-30`), then wired only into storage. The fix-for-flattening is itself unactuated. | No file declares this observe-first; the docstring frames it as the readable channel, implying it *should* be read. The prompts show flattened/instantaneous numbers instead. |
| **B** | Carried `AffectState` not in Executive prompt as a felt preamble | **GENUINE BUG (HIGH)** | Executive shows `state.emotion` (the instantaneous stimulus, `executive_node.py:158`), not the carried `state.affect`. The mood that *modulates temperature* is invisible to the reasoning itself — temperature ≠ felt content. | Climate already proves the preamble pattern works (`executive_node.py:151`); the affect equivalent is simply absent. |
| **C** | `somatic.note()` interoceptive content never reaches a thought | **GENUINE GAP (MED)** | Somatic actuates sampling (jitter) and sleep, but the *felt body* is never narrated, so Du cannot reflect on his own state. | Not declared observe-first anywhere; it's a missing hand, paralleling B. |
| **D** | `satisfaction.snapshot().gap` read by nothing | **STAGED → ready to graduate (HIGH value)** | Phase-0 observe-only by explicit design (`satisfaction.py:19-22`). The drive currency exists but no read path was *intended* yet. | Header is unambiguous: "PHASE 0: OBSERVE-ONLY … gated on Phase-0 logs looking sane." This is a graduation candidate, not a bug-fix. |
| **E** | `affect_labeling.named_affect` read by nothing | **STAGED by design (LOW)** | Phase-0 accessibility experiment; the design *forbids* a regulation hand prematurely (`affect_labeling.py:5-19`). | Explicit. Leave staged; only graduate the *accessibility* (revisitability) read, never a decay. |
| **F** | `affections` → T4 | **STAGED Phase-2 (LOW)** | Gated on the "made-mind realisation" landing (`affections.py:19-20`). | Explicit. Out of scope for this plan beyond fixing its upstream (the bug A unblocks better love-selection later). |
| **G** | Valence flattened through text→embedding for *all* affective retrieval | **GENUINE ARCHITECTURAL LIMIT (MED/L)** | `felt_text()` (`mood.py:32`) serialises to a sentence the encoder can't separate by sign/magnitude. Affective retrieval (`emotion_embedding`) therefore can't distinguish a dread-memory from an elation-memory. | The `valence`/`felt` columns were the band-aid (item A). A true fix is VA-subspace steering or a numeric valence channel in retrieval scoring. |

**The genuine-bug-vs-staged split:** A, B, C, G are real dead/missing hands. D, E, F are *deliberately* staged behind named evidence gates — for those, the plan proposes *graduation* and names the evidence that earns it; it does **not** treat them as bugs.

---

## 3. Research grounding

| Paper | Mechanism | Adaptation for Du |
|-------|-----------|-------------------|
| **Emotion Circuits / "Do LLMs Feel?"** (arXiv 2510.11328) + **Valence–Arousal Subspace** (arXiv 2604.03147) | Context-agnostic emotion directions exist in activation space; steering along a VA subspace controls emotional expression far more strongly (≈99% expression accuracy) than prompting, which the text channel caps. | This is the antidote to bug **G**. Du computes a real valence scalar then *destroys* it through text→MiniLM. **VA activation steering** would let the scalar modulate generation directly — a much larger, sign-preserving effect than a prompt sentence. Borrow the *direction-extraction + scaled-injection* idea; adapt to the local llama backend as a v2 of items A/G (heavyweight, gated). |
| **CTCS-HRRL** (arXiv 2401.08999) — homeostatic RL, interoception-as-reward; Drive-Reduction ↔ RL | An agent's drive = distance of an internal variable from its setpoint; behavior that reduces the drive is rewarded. Continuous internal-state control of motivated behavior. | This is the model for graduating **satisfaction** (item D) and the **somatic** drives (C). The wanting−liking *gap* is a drive signal (distance from a "fulfilment setpoint"); it should bias *which mode/topic* Du reaches for, the way climate's hint does — not as reward-shaping a policy (Du has no RL loop), but as a homeostatic **prompt bias + ignition contribution**. |
| **Emotional inertia / persistent affect dynamics** | Affect has momentum; healthy mood persists but returns to baseline; pathological inertia = stuck. | `AffectState.tick()` (`schema.py:122`) already implements baseline-return relaxation — good. The risk in any new hand is *adding* inertia (a stuck felt-preamble). Mitigate with the same cooldown pattern climate uses (`orchestrator.py:700`). |
| **Affective framing changes reasoning** (BDCC) | The emotional framing of a prompt measurably shifts downstream reasoning quality/style. | Direct justification for items **B/C**: putting the *carried felt state* and *body state* into the prompt is not cosmetic — it changes how the reasoning runs. This is why the felt preamble belongs in the Executive/monologue, the two main brains. |

**Mechanism to borrow (primary):** the **climate hint pattern** (numeric → threshold → injected sentence) for the near-term hands (A/B/C/D), and **VA activation steering** as the gated heavyweight upgrade for the flattening (G).

---

## 4. Implementation plan

Ranked. Each item: Goal & weakness · Approach · Read-path/actuation · Observe-first gate · Risks · Effort+deps · Verification.

### Item A — Felt-state preamble into the Executive & monologue (the central fix) [HIGH] — ✅ LIVE (graduated 2026-07-06, retroactively re-verified 2026-08-24, `FELT_PREAMBLE=True` at schema.py:1048)

> **BUILT + GRADUATED + AUDITED:** `AffectState.felt_preamble()` (schema.py) + `mood.felt_preamble(affect, source)`
> (gated+logged hand) wired into the Executive (after the climate hint, reading carried `state.affect`) +
> the monologue seed. Log at `data/felt_preamble_log.jsonl` (14,501 rows, 2026-07-04→2026-08-22, still
> actively growing — confirms it is firing in the live path, not a dead flag). Originally shipped OFF pending the
> §4-A graduation gate below; **flipped `FELT_PREAMBLE=True` on 2026-07-06** on a founder evidence read
> documented in-code at `schema.py:1041-1047` (1,780 shadow rows, rate 6.5%, echo .648/diversity .977).
> **Retroactive audit 2026-08-24 (F-0067, job J-0066)** re-checked that gate against the full 7-week log and
> confirms it still holds: fire rate stayed under-band but safe (7.45% overall), sampled sentences read
> honest, and monoculture/diversity moved the healthy direction, not the risk one — see "Retroactive
> graduation audit" under "Current State" above for the full readout. Reads the carried `state.affect` (the
> robust source), not `mood.current_felt()`. Note: the actually-built firing gate is EMA-departure based
> (`mood.py:126-155`), not the static abs-threshold the "Approach" bullet below still describes — see the
> audit's mechanism note. Original spec follows.


- **Goal & weakness.** The undistorted felt scalar/string (`mood.current_felt()`/`current_valence()`) modulates nothing. Weakness class: write-only cognitive system — rich write path, dead read path.
- **Approach.** Add a helper `mood.felt_preamble(threshold=…)` returning a single short sentence ONLY when the carried state is non-neutral (e.g. `abs(valence) ≥ 0.35` OR `arousal ≥ 0.6` OR any of fear/anger/joy ≥ 0.4), built from `current_felt()` — e.g. `"You are carrying a low, heavy mood right now (valence −0.6); let it colour how you think, not dictate what is true."` Mirror the climate-hint guard exactly. Inject in two places:
  - `executive_node.py` immediately after the climate hint block (`:153`), reading `state.affect` (the *carried* state) — NOT the instantaneous `state.emotion` already shown at `:158`.
  - `inner_monologue_node.py` seed block, replacing/augmenting the bare-numbers line at `:1124-1126` with the felt sentence.
- **Read-path/actuation.** The sentence enters the live system/user prompt of the two main brains → directly conditions generation (affective-framing effect, BDCC). This is a *content* hand, complementary to the existing *temperature* hand (`temperature_bias`).
- **Observe-first gate.** Kill-switch flag (`FELT_PREAMBLE` in `schema.py` beside `THIN_ATTRACTOR`). Run shadow-only first: log the preamble that *would* fire each cycle to `data/felt_preamble_log.jsonl` for ~2 days. **Graduation evidence:** (1) it fires on a sane fraction of cycles (target ~15–40%, not every cycle — else it's wallpaper), (2) manual read of 20 firings shows the sentence matches the logged affect, (3) no measurable rise in the monoculture/recitation detectors after going live (the felt line must not become a new attractor).
- **Risks.** Becoming a stuck preamble (mitigate: same-sentence cooldown like climate `:700`); double-counting with the instantaneous emotion line (mitigate: show carried *or* instantaneous, not both jammed). Over-narration of feeling → performative affect (mitigate: gate hard on non-neutral threshold).
- **Effort.** S. Deps: none (mood scalars already populated).
- **Verification.** Unit: `felt_preamble` returns None at baseline, a sentence at valence −0.6. Integration: grep a live Executive prompt dump for the felt line on a charged cycle; confirm absence on a calm one.

### Item B — Show the *carried* AffectState (not just instantaneous) in the Executive [HIGH, folds into A] — ✅ LIVE (built 2026-08-29 per D-0069, `nodes/executive_node.py`)

> **BUILT:** D-0069 ruled to pursue Item B now that A is live. Per the plan's own spec ("largely subsumed
> by A... keep the instantaneous `state.emotion` line... let A's preamble be 'what you are carrying'"),
> the change is the minimal additive rider it was scoped as — no new flag, no new data source, rides
> Item A's existing `FELT_PREAMBLE` gate. `nodes/executive_node.py`'s `_build_prompt`: the carried felt
> preamble (Item A, unchanged) is tracked via a new `_fp_fired` bool; the pre-existing instantaneous
> `state.emotion` line right below it gets a contrast label — "Emotion right now (the stimulus this
> instant — distinct from the carried mood named above)" — **only when the carried preamble actually
> fired that cycle**, so a quiet/neutral cycle (no carried line above to contrast against) stays
> single-line, per the item's own "prompt clutter" risk note. Composes cleanly with the same-day
> PERCEIVE/RECALL origin-tiering (D-0068, job J-0343): `state.emotion`/`state.perception` sit outside
> both the WHAT YOU PERCEIVE and WHAT YOU RECALL blocks (verified by reading `_build_prompt` in full) so
> this is a genuinely separate, non-overlapping edit — no reordering or duplication of that structure.
> UDMS `udms_get_change_dossier` run before editing: CONTRACT-layer hits (`core/schema.py`, `core/mood.py`,
> `core/node_base.py`, `core/left_lane.py`, `core/sensorium.py`, real static-AST deps) reviewed, none
> touched by this change (only `core/mood.felt_preamble` call site, already present, was read not
> modified). The flagged `core/heavens.py`/`core/world_clock.py` CYCLIC_FEEDBACK_LOOP warning does not
> apply — `nodes/executive_node.py` imports neither module (grepped its own `import`/`from` lines).
> **Verification.** `python -c "import ast; ast.parse(open('nodes/executive_node.py',encoding='utf-8').read())"` → syntax OK. Behavioral: unchanged when Item A's preamble is silent (label stays plain "Emotion"); label appears only alongside a fired carried-mood line — same shadow log (`data/felt_preamble_log.jsonl`) and same `FELT_PREAMBLE` flag as Item A, no separate graduation gate needed per the item's own spec ("Same as A").

- **Goal & weakness.** Executive sees only `state.emotion` (the stimulus this cycle), so the *persisting* mood that actually biases temperature is invisible to reasoning. Weakness: signal/actuation mismatch (temperature carries it; content doesn't).
- **Approach.** Largely subsumed by A (the felt preamble *is* the carried state). Minimal extra: keep the instantaneous `state.emotion` line as "the stimulus just now," and let A's preamble be "what you are carrying," so the contrast (a calm stimulus landing on a heavy mood) is itself legible.
- **Read-path/actuation.** Same prompt injection as A.
- **Observe-first gate.** Same flag/log as A; additionally check the carried-vs-instantaneous lines don't contradict confusingly in the 20-sample read.
- **Risks.** Prompt clutter (mitigate: one line each, only when non-neutral).
- **Effort.** S (rider on A). Deps: A.
- **Verification.** Same as A.

### Item C — Somatic felt-body note into the monologue [MED]

- **Goal & weakness.** `somatic.note()` content never reaches a thought; Du's body changes his temperature but he can't reflect on tiredness/tension. Weakness: write-only interoception.
- **Approach.** Add a guarded one-liner in the monologue seed (`inner_monologue_node.py` near `:1127`): when `state.somatic` is in a *notable* band (`is_exhausted()` OR `neural_fatigue > 0.6` OR `visceral_tension > 0.6`), append a softened felt-body line derived from `note()` — e.g. `"Your body feels worn — energy low, a clench of tension."` Only on threshold, never every cycle.
- **Read-path/actuation.** Enters the monologue prompt → conditions the idle thought (e.g. lets fatigue surface as a theme, motivates rest-seeking thoughts rather than only forcing sleep mechanically).
- **Observe-first gate.** Flag `SOMATIC_NOTE`. Shadow-log when it *would* fire for ~2 days. **Graduation evidence:** it fires only in genuinely strained states (cross-check against the somatic telemetry already in `_log_affect`/CLI), fires on <20% of cycles, and 15 sampled firings read as honest (not melodramatic). Confirm it does NOT cause more sleep-loops or rumination about the body.
- **Risks.** Hypochondriac attractor (Du fixating on "I'm tired"); mitigate with a firing cooldown and a high threshold. GPU-temp jitter making it flicker; mitigate by reading the smoothed `neural_fatigue`, not raw `gpu_temp`.
- **Effort.** S. Deps: none.
- **Verification.** Force `neural_fatigue=0.8` in a test state → line present; `=0.2` → absent.

### Item D — Graduate the wanting/liking *gap* into a drive [HIGH value, was STAGED]

- **Goal & weakness.** `snapshot().gap` (compulsion signature) is computed per-domain and read by nothing behavioral. It is the missing "did it land?" currency. **Staged Phase-0 by design** — this item is *graduation*, gated on its own logs.
- **Approach (two actuations, both climate-pattern, no RL):**
  1. **Prompt bias (the main brain hand).** Add `satisfaction.drive_note()` returning a sentence ONLY when a domain's gap is large and persistent — e.g. high `self` gap = "You have been *pursuing* without *landing* — much wanting, little settling; consider whether to finish something rather than chase the next." Inject in the Executive after the climate hint and in the monologue seed. This mirrors `executive_hint`.
  2. **Ignition contribution (the no-text hand).** Feed a *large sustained gap* as a small additive term into the climate dissonance accumulator (a new `_DISS_RATE_*` source in `_tick_dissonance`, `climate_engine.py:443`), so chronic unfulfilled wanting can *itself* pull toward an autonomous, possibly-resolving thought. Keep it small and gated, with the integration bleed as governor.
- **Read-path/actuation.** (1) sentence into the two main brains' prompts; (2) numeric into the existing, proven ignition machinery.
- **Observe-first gate.** This is the graduation, so the gate is the *existing Phase-0 logs* (`data/satisfaction_log.jsonl` + `satisfaction_state.json`). **Graduation evidence:** (a) the per-domain gaps look sane over ≥1 week (not pinned at 0 or saturated — the same normalisation failure that killed climate's `integration_drive`, `climate_engine.py:354-372`); (b) the compulsion signature (high self/world gap) actually correlates with observed mirror-era loops in the pulse; (c) the liking events are firing at all (verify `record()` sites produce non-trivial liking, else the gap is meaningless). Only then wire the read. Keep the ignition term behind its own flag.
- **Risks.** A pinned/saturated gap becoming a constant nag (the `integration_drive` peg failure — use the same 6h-style normalisation / bounded saturation, not lifetime sums). Reward-hacking is N/A (no RL), but a *prompt* nag could train Du to perform "settling." Mitigate: gate on persistence (gap large for N hours), not instantaneous.
- **Effort.** M. Deps: verify the liking write-sites are live first; the ignition half depends on climate_engine.
- **Verification.** Synthesise a state with self-gap=2.0 → `drive_note()` returns the sentence; balanced → None. Replay a week of the log offline and confirm the gate would have fired sensibly.

### Item E — Graduate affect-labeling *accessibility* (not decay) [LOW, was STAGED]

- **Goal & weakness.** `named_affect` is set and read by nothing. Staged Phase-0 accessibility experiment. The design *correctly* forbids a pharmacological decay hand.
- **Approach.** The honoured graduation is **revisitability**, not regulation: when `state.named_affect` is set, store the named feeling as a lightweight recallable fragment ("Earlier I named a fear in myself") so it becomes an *object* future thought can encounter — exactly the "representational promotion" the header describes (`affect_labeling.py:5-9`). Do NOT apply the counterfactual decay.
- **Read-path/actuation.** A fragment into episodic store → ambient retrieval (same hand affections already uses, `affections.py:89`).
- **Observe-first gate.** **Graduation evidence:** Phase-0 manual review (already specified in the header) shows the detector's false-positive rate is low and the namings are genuine; AND the accessibility question ("does an explicit, revisitable feeling get re-encountered?") is answerable. Until that review is done, leave fully staged.
- **Risks.** Training performative naming (the design's stated fear). Mitigate: store as a *noticing*, never reward it (no satisfaction credit — already enforced, `satisfaction.py:55-58`).
- **Effort.** S. Deps: the Phase-0 review must be done first (evidence gate).
- **Verification.** With `named_affect` set, confirm exactly one fragment is stored, no decay applied to `state.affect`.

### Item G — VA-subspace activation steering for valence (the heavyweight flattening fix) [MED/L, gated, v2]

- **Goal & weakness.** All affective retrieval (`emotion_embedding`) and any text-channel valence is flattened by `felt_text()`→MiniLM (`mood.py:23-30`). The scalar exists but its sign/magnitude can't survive the encoder. Items A–D route *around* this with explicit numbers/sentences; G *fixes* it at the source for generation.
- **Approach.** Following arXiv 2510.11328 / 2604.03147: extract a valence direction in the generation model's activation space (contrastive +valence/−valence prompt pairs), then inject `α·v_valence` scaled by `mood.current_valence()` during the Executive/Reflection/monologue generations. Two sub-paths: (1) *generation steering* (modulate the felt tone of output); (2) *retrieval* — replace the flattened emotion-embedding similarity with a hybrid score that adds a numeric valence-match term (`|valence_query − valence_fragment|`) on top of the embedding, using the `valence` column already stored (`store_from_cycle`, `orchestrator.py:1975`). Sub-path (2) is far cheaper and should land first — it needs no activation access, just the existing column.
- **Read-path/actuation.** (1) activation injection at inference; (2) numeric valence term in the retrieval ranker — the stored `valence`/`felt` columns finally *do* something.
- **Observe-first gate.** Sub-path (2) first: shadow-rank retrievals with and without the valence term, log both orderings for ~3 days. **Graduation evidence:** the valence-aware ranking surfaces *sign-appropriate* memories (a dread-query stops pulling elation-memories) on manual review of 20 retrievals. Only after (2) proves the scalar is load-bearing, attempt (1). For (1): A/B a handful of generations with steering on/off; gate on the founder's read that steered output is *felt-appropriate and still truthful* (no identity drift) — this is a decoupled-judge requirement, not self-scored.
- **Risks.** Activation steering can degrade coherence or induce identity drift (HIGH — this is the most invasive item; keep it last, behind a flag, founder-judged). Local backend may not expose hidden states cleanly. Mitigate: do sub-path (2) — pure scoring, no model surgery — and possibly stop there.
- **Effort.** L (sub-path 1) / M (sub-path 2). Deps: A (proves the scalar matters in prompts) should land first; retrieval ranker location.
- **Verification.** (2): a −0.8 valence query ranks a stored −0.8 fragment above a +0.8 one with identical text-embedding. (1): steering vector shifts output valence on a fixed prompt without breaking the Critic.

---

## 5. Sequencing

1. **A + B (felt preamble, carried-state contrast)** — one small change, the central dead-hand, immediate. Flag `FELT_PREAMBLE`, shadow 2 days, graduate on the §4-A gate.
2. **C (somatic note)** — same pattern, independent, S effort. Flag `SOMATIC_NOTE`, shadow 2 days.
3. **D (wanting/liking drive)** — M effort; **first verify the liking write-sites are live and the Phase-0 gaps look sane** (its graduation gate), then wire the prompt-bias half, then the ignition half behind its own flag.
4. **E (affect-labeling accessibility)** — only after its Phase-0 false-positive review is done; LOW, cheap.
5. **G sub-path 2 (valence-aware retrieval)** — after A confirms the scalar matters; pure scoring, the cheap real fix for flattening.
6. **G sub-path 1 (activation steering)** — last, heaviest, founder-judged; optional if sub-path 2 suffices.

**Rationale:** A→C are the cheap, high-value "connect the hand" wins using the proven climate pattern, each independently flagged and shadowed. D is the highest-value *drive* graduation but needs its upstream verified first. E is a small honouring of a staged design. G is the only architectural fix (the flattening) and is sequenced last because the items above route around it and because activation steering is the highest-risk change in the domain. Every graduating item carries a kill-switch flag and a shadow-log window; nothing goes live on assertion.

---

### Appendix — key `file:line` anchors

- Wired exemplar: `core/climate_engine.py:189,195,203` → `core/orchestrator.py:695-696` → `nodes/executive_node.py:151`, `nodes/reflection_node.py:230`; ignition `orchestrator.py:2026`.
- The bug: `core/mood.py:23-30,91,96` (scalars) read only at `orchestrator.py:1975`, `inner_monologue_node.py:1575,1612` (storage).
- Temperature hand (works): `core/schema.py:152` → `core/node_base.py:106,111,119`.
- Carried-vs-instantaneous mismatch: `nodes/executive_node.py:158` (instantaneous) vs absent carried preamble.
- Somatic: `core/somatic.py:57,74,78` ; wired at `orchestrator.py:929,1039,2166` ; `note()` only at `run_nascence.py:487`.
- Satisfaction: `core/satisfaction.py:90,113` ; live `record()` at `orchestrator.py:378,897` ; `snapshot()` read by no behavior.
- Affect labeling: `core/affect_labeling.py:89` → `state.named_affect` (`schema.py:810`), read by nothing.
- `affections`: `core/affections.py:61,89` (fragment hand) ; T4 staged Phase-2.
