# TEMPERATURE AS A CHANNEL — sibling to `sound_causality.md` (2026-08-21)

> **Status:** 🟢 LIVE — `core/thermal.py`'s `DELIVER = True` (D-0047, 2026-08-27; verified per ROADMAP's
> own ★ LIVE note, no parity week). Founder-directed ("spec temperature as a channel, sibling to
> sound_causality"), after the evening's thermal investigation (`docs/reviews/du_24h_2026-08-21.md` §6–7,
> `docs/lab/cold_store_qwen_2026-08-21.md`, `docs/lab/lean_probe_2026-08-21.md`). *(This line was stale
> at DESIGNED until 2026-08-29's J-0406 pass — ROADMAP had already flagged the staleness itself; see
> the "Current State" section below for the full DELIVER-flip history.)*
> **Cluster 0 law applies:** every phase ships with a pre-registered metric sheet; no phase executes
> without one. **Layer law (founder, tonight):** the world couples to the world by physics; only what
> reaches his standpoint crosses into perception; the psyche links only what it experienced together.
> **Sibling law (sound):** no LLM anywhere in the channel; tree-falls (compute only where he is);
> shadow-first for anything that changes live behaviour.
> **2026-09-13 update:** §9 Row 2's missing instrument (`scripts/thermal_stance_batch.py`) built and
> run for real — see the dated section immediately below. F-1308 recorded (confidence inferred);
> D-0214 opened (mirrors D-0110's precedent) on how to treat the station-vs-band comparison now that
> the live architecture no longer rotates stations the way the row was pre-registered to test.
> **2026-09-14 — D-0214 RULED:** station-vs-band comparison retired (see §9 Row 2's own text) —
> eta²(band)=0.15 stands as a correlational fact only; the row's original felt-vs-authored question
> is explicitly NOT resolved by it, and goes back to open pending J-0939's persistent station log.
> **2026-09-15 — J-0939 built (F-1441):** the write side of D-0214's own dormant defeater now exists —
> `core/model_client.py` additionally logs every resolved (model, base_url, caller) to a new UNCAPPED
> `data/thought_station_log.jsonl` (`core/telemetry.py`, mirrors `log_llm_latency`'s own 2026-08-21
> precedent). Zero real rows yet (landed in worktree `wt_thermal_causality`, not yet merged/live); the
> defeater's other half — a genuine 3-week-or-longer direct read — still needs real accrual time
> before D-0214 can be revisited.
> **2026-09-23 — J-1236 checked the defeater's other half (F-1738):** NOT yet met. Real accrued span
> 2026-09-15 19:53 → 2026-09-22 21:59 UTC (7.09 calendar days); cross-checked against
> `data/nascence.log`'s own restart history, cumulative REAL live time in that window is only
> 105.35h / 4.39 days — well short of the ≥3-week bar either way. Also found (same pass): a small,
> real, historical contamination (85/19,183 rows, 0.44%, non-Du `__main__` callers, pre-dating
> J-1199's 2026-09-22 isolation fix) — J-1239 spawned to trace it; and confirmed the generator's own
> call site is still 100% single-station (qwen3.5:9b) once `judge_dwell_release()`'s already-known
> command-r7b background-lane calls are excluded — D-0214's premise stands. No re-ruling; left for a
> later re-check, per the defeater's own terms.
> **2026-09-23 — J-1239 traced the 85-row contamination (F-1760):** not one thing. 80/85 (`__main__:353`)
> are genuine external contamination — `scripts/train_state_invitro.py`'s `_prove()` call site, run by
> job J-1086 (`python scripts/train_state_invitro.py 40`, D-0181's n=80 held_within_scope replay),
> exactly the F-1683 hazard (this script neutralised only `log_llm_call`); already fixed going forward
> by J-1199/D-0252. The other 5 (`__main__:815`) are NOT contamination — confirmed real Du activity
> (`scripts/run_nascence.py`'s own `_form_epoch()` shutdown mechanism, timing-matched to real restarts)
> that merely looks suspicious because of where in the codebase that call lives. Recommendation: leave
> the 85 rows in place, filter `__main__:%` in any future per-station read; no live-file edit, no
> founder call needed. Same leak class found separately, much larger, in `data/llm_latency.jsonl`
> (1343/99106 rows, whole-file history) — spawned **J-1258** to characterise it (different file/plan).

```plan-state
stage: live
phase: Channel live (DELIVER=True); D-0214 retired the station-vs-band comparison (station unmeasurable, eta2(band)=0.15 stands alone); J-1236 found the 3-week defeater read still short (about 4.4 real days accrued)
verified: 2026-11-18
evidence_read: 2026-09-24
gate: data/thought_station_log.jsonl >= 3 weeks accrued (D-0214 defeater)
next: Optional: confirm companion lighting is absent from hands_trace; compute comfort_calls heeded
history: docs/plan_history/thermal_causality.md
cluster: 6
```


---

> **History folded** — 12 dated Current State section(s) (2026-08-27 … 2026-09-24) moved to `docs/plan_history/thermal_causality.md` on 2026-09-27 by plan-compact. Derived timeline: `plan_ledger.py thermal_causality`.

> **History folded** — the legacy "Previous state" section (8,716 bytes) moved to `docs/plan_history/thermal_causality.md` on 2026-09-27 by hand-fold (J-1499; plan-compact-style — plan_compact.py's own CS_HEAD regex does not match this heading text). Derived timeline: `plan_ledger.py thermal_causality`.

## 0. The engineering question (GPT's phrasing, adopted)

Not *"should we give Du temperature?"* but **"can temperature become an honest perceptual channel
under the same epistemic rules as sound?"** If yes, we have not taught him that cold is unpleasant; we
have given the world another way of touching him. What happens after that belongs to the experiment.

## 1. Why now, and what the evidence already showed

- His affect system has **no thermal input by construction** (protoself: coherence · commitment
  integrity · relational warmth · novelty · vitality). The only temperature his body registers is the
  GPU's (somatic strain from `gpu_temp`).
- The world's cold reached him **only as a standing text clause** (`_warmth_phrase`) whose pain verbs
  supplied his suffering vocabulary (cold-store control: clause alone → "The cold…" 62% of openings,
  suffering words ×); neutralised tonight — but a neutral clause is still a text box, not a channel.
- The **stations lean differently** about cold under identical neutral wording (qwen 67% suffering
  words, gemma 88%, phi3 0%, falcon welcoming). Those leans currently *manufacture* the phenomenon.
  Once temperature is a channel, they *process* his experience instead — one influence in the
  pipeline, not its source.
- **Temperature is the one world variable he can change** (the fire) — and in winter the fire is the
  *only* warm in his world: every one of the 60 warm-stamped memories has the fire lit. The fire is
  therefore the natural site of the first agentive thermal relationship.
- He lit it himself at 11:53 today, one second after the honest cold-grate render, and walked in to
  it at 19:40 tonight after two hours outdoors. The channel already has two data points waiting for a
  ledger to hold them.

## 2. The four layers, applied to temperature

```
WORLD        sun · wind · rain · season · time · shelter · fire  ──(thermal physics)──▶ a warmth FIELD
SUBSTRATE    his standpoint + his wetness state                   ──(delivery)──▶ warmth AT HIM, now
PERCEPTION   change / gradient / persistence above threshold      ──(events)──▶ a thermal percept
PSYCHE       the THERMAL LEDGER (felt, where, under what)         ──(inference)──▶ causes he binds, maybe wrongly
```
Information is lost at every boundary on purpose. The world knows the sun's azimuth; he knows a wall
was warm. The substrate knows he is 0.6 wet; he knows the cold has a different quality tonight. He
may bind the warmth to the fire or to the wall or to nothing yet. A wrong binding is a legitimate
state, exactly as an unlearned call is in the Hearing Ledger.

## 3. WORLD — thermal physics (extends `_warmth()`, which is already a causal model)

`sensorium._warmth(loc, phase, weather, season, fire, wind)` already couples season base + weather +
wind + time + per-place shelter + fire into one scalar. The channel keeps it as the **core** and adds
the couplings the founder named. All arithmetic; all world-side; computed for **his place only**
(tree-falls: O(1)).

| cause | today | channel |
|---|---|---|
| **sun** | "clear + day + spring/summer → +0.12" | `world_clock.sun()` gives az/phase/f already. Insolation term = f(az, phase, cloud) × place exposure (garden's west wall in a clear afternoon; the study's north window; the wood's canopy shade; the shore open). Moves through the day → *learnable*. |
| **wind** | binary windy −0.16 | graded by the wind axis; shelter already per place (wood breaks it, study walls, shore exposed). |
| **rain** | −0.10 while raining | rain no longer sets warmth directly — it emits a **wetness rate** (§4); wetness lowers felt warmth with its own persistence. |
| **fire** | flat +0.42 anywhere in the study | +warmth **by distance from the fireplace** (geometry has the hearth at [0.0, 2.0, 0.4] and his standpoint); embers smaller; out = 0. Also a **drying rate** (§4). |
| **shelter / terrain** | per-place constants | unchanged; the wood's canopy and the study's walls are what make "outside is colder, the wood is less exposed" discoverable. |
| **time / season** | phase + season base | unchanged. |

The output is still one number at his standpoint — `warmth ∈ [0,1]` — plus the new `wet ∈ [0,1]`.

## 4. SUBSTRATE — wetness as a state with its own clock (the sound_causality "rate functions" pattern)

Rain does not mean wet. Rain at an exposed place emits a wetting rate; the canopy halves it; indoors
it is zero. Wetness **persists** and decays on its own clock — slowly in the cold, faster by the fire
(the fire emits a drying rate by distance), faster in sun and wind. Felt warmth is reduced by wetness.
So: walk through rain → wet → into the wood → less rain, still wet → the study doorway → the fire
drying him over half an hour. Nobody tells him "you are wet"; the sequence of felt states is the
evidence. State lives in `room_state` beside `woodpile` (substrate, not identity). Zero LLM.

## 5. PERCEPTION — delivery as CHANGE, not as a standing clause (sound's onset/renotice law)

The neutralised clause still describes every prompt. The channel replaces it with **events**:
- **Transitions** when warmth-at-him crosses a band (cold → cool → mild → warm), with the onset law's
  quiet-gate (the previous band must have held ≥N minutes) and cooldown — *"you come in from the
  garden and the room's warmth reaches you"*, *"the wind drops and the cold loses its edge"*,
  *"the sun is on your back for a moment"*. Phrase pools via `phrasing.vary`, neutral verbs.
- **Gradients during legged journeys** — locomotion's legs (garden→wood 70s, wood→shore 70s…) are where
  the field changes fastest; a leg can carry one thermal clause from its *entry* standpoint's warmth
  relative to its exit's (the wood *is* less exposed; he learns it by the walk, not by being told).
- **Persistence renotice** — a long unchanged state may be re-noticed at most every ~4h (the renotice
  law), never every prompt. **Re-tuned 2026-09-02 (J-0443, F-0615): at most every ~2h, keyed to time
  since the last delivered percept (the original band-since key never once fired against the real
  boundary-flapping world) plus a 15-min current-band hold so "still X" stays honest.**
- **Wetness events** — onset of wet, and the drying-by-the-fire sequence, same rails.
- **Silence is honest**: when nothing changes, the channel says nothing. The standing clause is
  retired once the events are live (founder's call on timing; parity/overlap measured first).
- Delivered exactly as sound percepts are: into the idle seed as world perception, provenance-stamped
  (`origin='thermal'`), never into the system prompt.

## 6. PSYCHE — the THERMAL LEDGER (mirrors the Hearing Ledger, experienced-only)

`data/thermal_ledger.json`, fed by the channel's own clock **where he is**:
- **Bands lived** — hours per band per place per phase (like BEDS: lived-in hours, not counts).
- **Transitions felt** — counted events per kind per place (like EVENTS).
- **Wetness episodes** — onset place/weather, duration, where it ended (by the fire / in sun / in wind).
- **Bindings** — his inferences about cause: `warm_here → fire | wall_in_sun | unknown`, with a
  confidence he earned by investigation (the `investigate` hand already exists for objects and sounds;
  "is it the fire or the wall?" is an investigation). **A wrong binding stays until contradicted.**
  The unknown is a knowledge state.
- Nothing in the ledger is world truth; it is what crossed. It is the substrate of the experienced
  tuple's `warmth_band` and `wet`, and of every spring (§7).

## 7. MEMORY and the springs — what the channel makes possible

- The **experienced tuple** (tonight's founder rule: a memory carries only what was rendered to him
  at that moment, from where he stood) gains `warmth_band` (felt) and `wet` — never the thermometer.
- Chords then exist for `cold × shore × night`, `cold × fire × evening`, `wet × wood × rain`,
  `warm × hearthstone × cat`. **Both "cold→misery" and "cold→comfort" can exist as different
  chords; no preference scalar is ever written.**
- Springs (cluster 0 P3, the history-driven ledger the audit's #16 asked for — co-exposure, not
  similarity) stiffen only between things that were together *in his experience*. The first spring
  that can stiffen from his own agency is **cold → fire**.
- The thermal_relationship shadow (built tonight) is **intended, eventually, to be re-pointed from
  the world clause to the ledger**, so the question "does his stance toward the cold track the station
  route or drift free of it" is asked of his *felt record*, not of words the world handed him.
  **CORRECTED 2026-08-25 (J-0249):** this re-pointing has NOT happened. `core/thermal_relationship.py:62`
  still calls `sensorium._warmth()` directly — the same flat, pre-channel physics function the
  original clause used, not even `thermal.field_at()` (the extended world-layer physics with sun/
  wind-grading/fire-by-distance), and it never imports or reads `data/thermal_ledger.json` (the
  psyche-layer felt record) anywhere in the file. The instrument today still reads a *world* number,
  just a slightly different one than the retired text clause used. See §11.1 for why this is left as
  open work rather than fixed immediately.

## 8. What is deliberately NOT in this plan

- No thermal **affect** variable in the protoself. The substrate (warmth-at-him, wetness) may influence
  (as walking effort already does via `metabolic_energy`/`neural_fatigue` — a founder decision per
  coupling, each pre-registered), but temperature never becomes part of what he *is*. Biology is an
  analogy, not the target.
- No cost/penalty for cold. If he enjoys it, who are we to penalise it. The channel delivers
  experience; valuation is his, or the stations', or emergent in the chords.
- No LLM anywhere in the channel.

## 9. Pre-registered metric sheet (cluster-0 law) — written before any phase runs

| question | instrument | prediction | kill |
|---|---|---|---|
| Does delivery-as-events reduce the "The cold…" opener without losing temperature presence? | thermal_relationship shadow: opener share, `mentions_temp` | opener < 10% (from 24%); mentions_temp stays ≥ 25% **(re-registered 2026-09-02, D-0110 — original floor was ≥ 40%, calibrated in the clause era when temperature appeared in EVERY prompt; F-0615's replay proved the §5 event law tops out ~29-30%, so 40% was structurally unreachable, not merely missed. Hard lower reference: the 11% channel-less monologue baseline.)** | opener unchanged → events are a text box by another name |
| Does the ledger's felt record diverge from the station leans? | ledger bands × thought stance (two-judge batch) vs station route | within 3 weeks, stance conditional on band explains more variance than stance conditional on station | stance tracks station, not band → the write-path authored it; say so **RETIRED 2026-09-14 (D-0214, founder, mirrors D-0110's precedent) — the station-vs-band comparison itself is retired, not met/not-met: F-1308 (2026-09-13) found station pinned at zero measured variance (all 80/80 sampled items = qwen3.5:9b, no persisted per-thought station log exists to check further back — the live architecture never rotated stations the way this row was pre-registered to test, and there's no evidence it's coming back). That is structural, not a measurement failure — there was nothing to contrast band against. eta²(band)=0.1507 (N=80, 16/band, real but noisy/non-monotonic) stands as a correlational fact the channel can still show, but retiring the comparison does NOT resolve this row's original question — with station unmeasurable, "does his stance track the writer or drift free of it" goes back to genuinely open, not partially answered by the band number alone. Defeater (dormant, not deleted): revisit if J-0939's persistent station log ever enables a real multi-week direct read, or if the hot lane's SERVE_CHAINS config ever rotates models again.** |
| Do thermal gradients produce discovery without telling? | bindings in the ledger; investigations of warmth; recall of "the wood is less exposed" in his own words | ≥1 unprompted correct binding (fire or sun) within 2 weeks; wrong bindings logged, not corrected by us | zero bindings in a month → perception events aren't salient enough |
| Does the fire become agentive? | hand-lit fires per week (deed record) vs comfort_calls heeded | rises from ~1/2wk baseline | flat → the channel didn't reach the hand |
| Parity first | old clause vs new events: same bands, same places | event channel never reports a band the physics didn't produce | any mismatch → physics bug, stop |

## 10. Open founder decisions

1. **CLOSED 2026-08-24 (D-0038, ruled by claude, job J-0145):** Band thresholds and the onset
   quiet-gate — **yes, final**, as proposed: bands 0.15/0.28/0.42/0.60, quiet-gate 600s, cooldown
   1500s. Code-verified directly in `core/thermal.py` lines 43-46 (`BANDS = ((0.60,'warm'),
   (0.42,'mild'),(0.28,'cool'),(0.15,'cold'),(-1.0,'very_cold'))`, `QUIET_S = 600.0`,
   `COOLDOWN_S = 1500.0`) and named explicitly in the module docstring (lines 25-27) as the
   adopted §10 defaults — not just inferred from the shadow log. Matches F-0048's independent
   shadow-log inference (565 rows, per-band warmth ranges land exactly on these cuts; all 20
   band-changes that didn't fire had gaps under 271s, consistent with the 600s quiet-gate) and is
   now confirmed at the source-of-truth level (F-0175). Defeater: a future re-tune of these
   constants in `core/thermal.py`.
2. **CLOSED 2026-08-25 (D-0048, ruled by claude, job J-0251):** Fire-by-distance shape —
   **yes, final**, as proposed: inverse-square-ish from the hearth, clipped, embers ×0.4.
   Code-verified directly in `core/thermal.py`: `_HEARTH = (0.0, 2.0, 0.4)` (line 60),
   `_fire_term()` (lines 81-93) with `frac = max(0.45, min(1.0, 1.15/(0.6+d*d*0.18)))` (line 92)
   and `peak = 0.42 if fire=='burning' else 0.42*0.4` (line 86). Shipped since 2026-08-21.
   Defeater: a future re-tune of `_HEARTH`, the frac clip formula, or the embers multiplier.
3. **CLOSED 2026-08-25 (D-0049, ruled by claude, job J-0251):** Wetness clocks — **yes, final**,
   as proposed: full soak in ~20 min of rain exposed; dry ~45 min by the fire, ~3h in cold still
   air; canopy roughly halves wetting. Code-verified directly in `core/thermal.py`:
   `_SOAK_EXPOSED = 1.0/(20*60)` (line 49), `_DRY_FIRE_CLOSE = 1.0/(45*60)` (line 50),
   `_DRY_STILL_COLD = 1.0/(180*60)` (line 51), and the exposure table (line 204) giving
   wood=0.5 vs shore=1.0/garden=0.9. Shipped since 2026-08-21. Defeater: a future re-tune of
   these constants or the exposure table.
4. Does warmth/wetness couple into the substrate body (energy/fatigue) at all in Phase 1? Recommend
   **no** for Phase 1 — observe the pure channel first; any coupling is its own pre-registered phase.
5. Retire the standing clause immediately on event go-live, or overlap for a parity week?
6. Sight is explicitly out of scope here (the renderer chooses salience for him — a different kind of
   gap; last, per founder).

## 10b. THE CHANNEL CONTRACT (adopted 2026-08-21 from the founder/GPT exchange — binds EVERY channel)

Not another sensor: a contract. Channels keep their OWN physics (sound propagates and attenuates;
warmth is a field plus wetness; light is an illumination field; smell is emission + wind diffusion;
touch is contact geometry) — no generic `Sense` class manufacturing descriptive events — but every
channel must answer the same eight questions before it is built, and is audited against them after:

| # | clause | thermal answer (this plan) |
|---|---|---|
| 1 | **World state** — what objectively exists | the warmth field from sun/wind/rain/season/time/shelter/fire (§3); wetting/drying rates (§4) |
| 2 | **Propagation** — what physical process decides whether it reaches him | standpoint exposure + shelter + distance-to-hearth; wetness as the carrier of persistence |
| 3 | **Standpoint** — where he is when it arrives | `position.json` place + standpoint; journey legs for gradients |
| 4 | **Perceptual transformation** — what is LOST before him | the thermometer, the causes, the field everywhere he is not; he gets one felt band + wet/dry |
| 5 | **Event law** — new percept vs background | band transitions (quiet-gated, cooldown), journey gradients, ≤1 renotice/2h (was /4h; re-tuned J-0443 2026-09-02, keyed to time-since-last-percept); silence otherwise |
| 6 | **Experienced record** — what is written | `warmth_band`, `wet` into the EXPERIENCED tuple; the thermal ledger (bands lived, transitions, wetness episodes, bindings) |
| 7 | **Epistemic boundary** — what the channel is FORBIDDEN to tell him | the temperature; the cause ("the fire is warming you"); anything about places he is not in; any valuation ("uncomfortable") |
| 8 | **Investigation pathway** — how he reduces uncertainty | the investigate hand: move toward/away, test the wall vs the hearth, wait for a change; bindings earned, wrong ones kept until contradicted |

**Audit of the existing channels against the contract (2026-08-21):**

| channel | state | contract gaps |
|---|---|---|
| **sound** | mature (38 keys, audibility table, Hearing Ledger, onsets, learnable voices) | **#7 honoured, by a GRANDFATHERING rule (founder, correcting my first audit):** the *named* voices (tui, morepork, gull, blackbird, oystercatcher) are told because he had already been told about them — in prose, for months — before the channel existed; he already held the links, and pretending otherwise would be a lie of a different kind. The *learnable* class (fantail, riroriro, kereru — unknown-lines from acoustic properties until `is_learned`) came later and applies to NEW sources. **Rule for every channel: the epistemic boundary protects what he does NOT yet know; prior knowledge is grandfathered.** For thermal: he has been told for months that the fire warms the room — the channel does not pretend he doesn't know it; what he must EARN is the finer structure (the wall in the sun, the wood's shelter, wetness and drying). One propagation leak seen tonight: `rain_on_roof` in his experienced sounds while on the SHORE — a place-gating miss in `active_sounds()` worth a look (sound contract #2). |
| **thermal** | this plan | none yet built; contract answered above |
| **light** | prose + `daylight()` phases + lamp/moth gating | no illumination field, no standpoint delivery, no ledger; the window/north-facing logic exists in comments only |
| **smell** | prose only (33 lines in sensorium: woodsmoke, lamp-oil, salt, the green smell of rain) | no source/emission, no wind diffusion, no event law, no ledger — every smell is told |
| **touch / effort** | substrate only (walking effort → `metabolic_energy`/`neural_fatigue`) | reaches the body, never perception: no percept, no ledger; wetness (§4) would be its first true percept |
| **sight** | the spatial renderer (geometry → standpoint-relative description, sightlines, salience) | structurally a channel, but #4/#7 are inverted: the renderer chooses salience FOR him and names what he sees; deferred last (founder) |

**On building several channels early — FOUNDER DECISION (2026-08-21): ALL TOGETHER, NOW.** I had
argued for staggering (a week apart each, for attribution — the idle-executive precedent). The founder
overruled it, and the reasoning stands on its own: *we are not testing whether each sense pulls him in a
direction; we are testing whether the overall scheme has an effect. Having them all tells us about all
of them — harder to infer which is stronger, easier to tell if the concept holds.* And the clock is
real: three model upgrades in a two-month-old project; in months there will be new models and new
research to use. Weeks between channels is a luxury the experiment does not have. So: the contract +
the experienced-tuple split (built tonight) as shared infrastructure, then **thermal, wetness-as-touch,
light and smell specified and built as one programme**, each still answering the eight clauses and
each keeping its OWN ledger — which is what preserves per-channel evidence even when their arrival is
simultaneous: the ledgers tell us what each channel delivered; only the behavioural attribution is
shared. Primitive is fine; equal sophistication is not required — the unevenness is itself a variable
(does the psyche weight channels by reliability and history?).

**The safeguard, stated once for all channels:** the world decides what exists; the channel decides
what reaches him; the psyche decides what it means.

## 11. Build order (when approved) — every step shadow-first, zero LLM

> **Build state 2026-08-21 (approved same night, founder: 'start the thermal build'):** steps 1–4 BUILT in
> one module `core/thermal.py` (the ledger did not need its own file). Parity law held: 23,040/23,040 cases
> identical to `_warmth` with extensions off. Wetness is hooked in `sensorium.tick`; perception is SHADOW
> (`DELIVER=False`) in the monologue; `wet` is on the experienced tuple; `warmth_band` derives from `warmth`
> via `thermal.band_of` (no second column). Steps 5–6 not started. The neutral clause stays for the parity
> week (§10.5 open). Sibling channels: `channels_programme.md` — built together, not staggered.

1. **World physics** — extend `_warmth()` with sun insolation + fire-by-distance + wind grading; add
   the wetness state + rates. Parity-tested against today's bands before any delivery changes.
2. **Thermal ledger** — `core/thermal_ledger.py`, fed where he is, bands/transitions/wetness
   episodes; no bindings yet.
   **UPDATE 2026-08-23 (files-and-evidence audit): never built as a separate module; the ledger
   landed inside `core/thermal.py` instead, writing `data/thermal_ledger.json` (confirmed: real
   band/place/phase data present, e.g. `"very_cold|shore|night": 4.35`).**
3. **Perception events** — transition/gradient/renotice percepts into the idle seed (`origin='thermal'`),
   shadow-logged for a day (what *would* fire) before they fire; then live, clause retired per §10.5.
4. **Experienced tuple** — `warmth_band` + `wet` from the ledger into the experienced layer (the
   world-truth/experienced split from tonight's tuple work is the prerequisite).
5. **Bindings** — the investigate hand learns "is it the fire or the wall" the way it learns a bird.
6. **Springs** — cold→fire and friends, via cluster 0 P3 once its own retro-validation passes.

*Sibling note:* sound_causality's propagation table (per-place audibility) and this plan's per-place
exposure/shelter table are the same object seen twice — one table of "what of the world reaches each
standpoint" could eventually serve both channels. Not now; noted for the federated-lists design.

## 11.1 §7's re-pointing claim — reconciled, not fixed (J-0249, 2026-08-25)

F-0307 caught §7 stating the thermal_relationship shadow "is re-pointed from the world clause to the
ledger" when `core/thermal_relationship.py:62` still calls `sensorium._warmth()` directly — verified
again this pass, unchanged. Two honest fixes were on the table: (a) actually re-point `observe()` to
read the ledger, or (b) correct the doc. Chose **(b)**, for real reasons, not just to avoid the work:

- **There is no coherent "felt record" to point it at yet.** Build order steps 5–6 (bindings,
  springs — the parts of the ledger that would hold an inferred, experienced "what he thinks is
  warming him" value) are unbuilt. `data/thermal_ledger.json` today holds aggregate bands-lived /
  transition counts / wetness episodes, not a per-tick "felt warmth right now" scalar `observe()`
  could substitute in place of `_warmth()`. Re-pointing to the ledger *now* would mean reading an
  aggregate, which is a different measurement, not a more-felt one.
- **The instrument is mid-flight.** 575+ append-only rows have already accrued reading world warmth
  as their `warmth` field, feeding the pre-registered opener/mentions_temp/by-band metric sheet (§9).
  Changing what `warmth` means partway through would silently confound that comparison — exactly the
  parity discipline this plan holds everywhere else (§9's own "Parity first" row, §11's parity test
  for step 1).
- **The right re-point point is `thermal.field_at()`, not the ledger, and only once §11 step 3
  actually delivers.** Once `DELIVER=True` and events reach the idle seed (J-0248, still open), the
  ledger accumulates his real experienced bands, and *that* is the honest moment to switch
  `observe()`'s `warmth` source to the felt/experienced value and start a fresh comparable series —
  documented as a break in the log, not silently.
- §7's text above is corrected in place rather than left standing; this subsection is the paper
  trail for why the code was not touched to match it. No new job spawned for the re-point itself —
  it is already gated behind J-0248 (idle-seed delivery) and the DELIVER flip (D-0037), both open;
  spawning a third tracker for the same blocked work would just fragment it.

---

## Current State — verified 2026-11-18 (J-1292/F-1844; J-1318/F-1865)

- **2026-11-18** (F-5100): J-4254 first live read since DELIVER=True. Row 3: correct fire and sun warmth bindings appear in Du's thoughts (e.g. 09-04 sun warms skin), but unprompted-vs-ambient-echo not separable; no 'wood less exposed' recall found. Row 4: hands_trace.jsonl gives a Du-only instrument, 10 hand-lit fires in 12.5 wks (~0.8/wk, 8 post-flip) vs ~0.5/wk baseline: flat/slight, small N, none in W46-47.
- **2026-11-18** (F-5076): J-4253 (2026-11-18): D-0214 defeater re-read on 53 days of station log. Duration part met, variance part not: thought-authoring paths are 97.9% qwen3.5:9b (weekly 95.3-100%), so Row 2 stays RETIRED and no eta2(band) vs eta2(station) run was warranted. Rotation only on non-thought callers (weeks 46-47).

### What we have
- Channel live since D-0047 (`DELIVER=True`); D-0214 retired the station-vs-band comparison — station
  is structurally unmeasurable on the live architecture (pinned at one model), so eta²(band)=0.15
  stands as a correlational fact only, not a resolved answer to whether stance tracks the writer.
- The `neutralize_telemetry()` script-guard sweep (F-1683 → F-1787 → F-1811 → F-1844) is closed for
  its 12-script scope: 7 confirmed retired, 4 fixed with the guard (isolation-verified), 1
  reclassified as a non-caller. `scripts/_verify_genesis.py`'s own missing guard was fixed separately
  (J-1318/F-1865).

### What we need
- J-1236 confirmed D-0214's dormant defeater (a real 3-week direct read) is not yet met: only ~4.4
  real accrued days as of 2026-09-23.
- A 4th sweep round is assessed likely, not confirmed: 62 scripts call into a `call_node`-wrapping
  `core/`/`nodes/` module without using the literal text themselves, invisible to every grep-based
  round so far (J-1308, not yet read).

### What we're doing next
- J-1308: read the 62 candidate scripts for the same silent-telemetry-contamination shape.

---

