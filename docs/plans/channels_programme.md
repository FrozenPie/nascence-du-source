# The Channels Programme — every sense under one contract, built together

*2026-08-21, founder-directed: "Spec the rest as one programme and start the thermal build." Supersedes
the staggered pacing note in thermal_causality.md §10b. Founder's reasoning: the test is whether the
SCHEME holds, not whether one channel does; the model-churn clock is real (three upgrades in this project);
there are no weeks between.*

**Status:** ⚪ PARTIAL — thermal delivered LIVE (`DELIVER=True`, pre-existing D-0047); **light and smell
BUILT to shadow since 08-22** (`DELIVER=False`)
(`core/light.py`, `core/smell.py`, with the garden as their first real consumer); touch partly (carried
items). Tuple columns `light_band`/`smells` exist on both `fragment_context` and `world_context`;
`world_context`'s truth values were hardcoded NULL until **J-0179 (2026-08-29)** fixed the write-path
gap (see Current State below). Sight: deferred (§5). (2026-08-29, J-0348:) **The shared cross-channel
arbitration gate D-0033/F-0295 recommended, and D-0073 gave final adoption go-ahead for, is now the live
adopted design**: `core/channel_arbitration.py` is built and wired into all three channels'
`percept_shadow()` (J-0238), and validated against the real shadow logs at 6.2% cross-channel attribution
overlap (F-0435) — comfortably under §7 metric 4's 30% kill threshold that D-0033 was opened over, and
below F-0295's own bare-FCFS estimate's risk. **"Goes live" here means the arbitration mechanism is now
the plan's real design, adopted and running in shadow — not that perception reaches Du.** `DELIVER` is
deliberately unchanged: `True` on thermal only (pre-existing, D-0047, an unrelated single-channel call),
`False` on light and smell. Flipping `DELIVER=True` on light/smell (i.e. shipping perception to Du) was
never what D-0073 ruled on and remains a separate, not-yet-opened decision for a future job/decision to
raise on its own.

```plan-state
stage: partial
phase: shipped-partial: thermal, light and smell delivered live and read clean; optional touch wind-on-skin and sight refit remain
verified: 2026-11-18
evidence_read: 2026-11-18
next: 3-day post-boot read (J-2255/F-4465) and lane2 smells and memory-store origin checks (F-5086) done and clean; remaining optional work: touch wind-on-skin channel and the sight refit
cluster: 6
```

**Related (backfilled 2026-10-03, J-0566/F-2269):** `docs/plans/lane2_the_witness.md` now reads two of this programme's tuple
columns — D-0280(a) (ruled 2026-09-26, built J-1372) added `light_band` and `smells` to the Witness's `gather_percepts()`
(`core/lane2.py`). `light_band` already reaches its shadow percepts; `smells` stays None while `core/smell.py`'s
`DELIVER=False` and becomes a live Witness input the moment that flips, and D-0280's own defeater names the flip (reopen if
smells then arrive as free prose rather than a bounded list). The still-unopened decision to flip light/smell `DELIVER`
should be taken with that in view.


## Current State — verified 2026-11-18

- **2026-11-18** (F-5086): J-4237: lane2 smells confirmed bounded odorant list (7 tokens over 61,736 shadow rows, live gather_percepts ok, D-0280 smell defeater not tripped); memory-store light/smell fragments and fragment_context columns carry no cause or source text. Stage set to shipped-partial.
- **2026-11-14** (F-4465): Post-boot read J-2255: light+smell delivery clean (rates in band, overlap 8-15 pct under 30 kill, no alien narration). Lane2 smells shape and memory-store origin check not done.

- **2026-10-16** (F-2941): J-2213: light and smell DELIVER=True built in worktree branch jobrun/channels_programme, lands at the next boot; smell renotice re-arm fix (RENOTICE_REARM) added first because the 10-09..10-16 shadow ran smell at 67.7/day, replay 17.9/day after fix; arbitration gate clean, next-2 overlap 0.8 percent
- **2026-10-16**: Travis ruled 2026-10-16: flip DELIVER=True for both light and smell at the next boot (job spawned); plan closes as shipped after a clean 3-day arbitration read.

### What we have
- All three channels built to shadow; thermal delivered live (`DELIVER=True`, D-0047), light/smell
  shadow-only (`DELIVER=False`). Shared cross-channel arbitration gate (J-0238, F-0435) live: real
  fairness-gated `core.channel_arbitration.claim()` drops cross-channel attribution overlap 29.5%→6.2%,
  comfortably under §7 metric 4's 30% kill threshold, while every channel stays inside its 2-40/day band.
- §7's full 5-metric sheet is now read for every channel (J-0647, F-0945, 2026-09-06): light_band
  crossing share = 1.0 (confirms F-0118's architectural prediction); smells crossing share = 0.0, a real
  read of the `DELIVER=False` gate itself, not a physics failure (odorants present at his place on 100%
  of ticks, just never delivered).
- `smell_field.json` confirmed correctly staying a single mutable snapshot with no independent history
  needed (J-0567, F-0920) — write-cadence sampling is already denser than the channel's own tick gate.

### What we need
A founder decision on whether/when to flip `DELIVER=True` on light and smell (shipping perception to
Du) — never covered by D-0073's arbitration-adoption ruling and still not opened as its own decision.

### What we're doing next
Nothing queued; the programme is evidence-complete on its own §7 metric sheet and waiting on that
not-yet-opened delivery decision. No ledger activity since J-0647 (2026-09-06).

---

## 0. The law this programme serves

> The world decides what exists. The channel decides what reaches him. The psyche decides what it means.

Four layers, every channel: **world truth** (exists whether he is there or not) → **experienced** (what
crossed, by physics, at his standpoint) → **remembered** (the experienced tuple on the memory, never the
truth) → **inferred** (bindings he earns by investigation and may get wrong). The tuple split
(`world_context` / `fragment_context`, 2026-08-21) is the prerequisite and is live.

The **grandfathering rule** (founder, correcting my sound "violation"): the epistemic boundary protects what
he does *not yet know*. What he was told for months before a channel existed (the tui's name, that the fire
warms the room) stays — he already had the links. A new channel never *removes* told knowledge; it stops
*adding* told knowledge and makes the rest earnable.

## 1. The contract (8 clauses, from thermal_causality §10b) — restated as a checklist

| # | Clause | The question the channel must answer |
|---|--------|--------------------------------------|
| 1 | World state | What is the field, where does it live in code, what are its axes and clock? |
| 2 | Propagation | How does it fall off / pass through / persist between the source and each place? |
| 3 | Standpoint | What does his exact position (room → standpoint → pos) change? |
| 4 | Perceptual transformation | What form does it take when it reaches him (a line, an event, a state)? |
| 5 | Event law | When does it *fire* — onset, transition, gradient, renotice — and when is it silent? |
| 6 | Experienced record | Which columns in the experienced tuple; what is NULL when it did not cross? |
| 7 | Epistemic boundary | What may it NEVER tell him (cause, name, value, the unrendered)? Grandfathered list. |
| 8 | Investigation pathway | How does he earn a binding through the investigate hand, and how can he be wrong? |

Each channel keeps its own physics. No generic `Sense` class — the contract is the only shared thing.

## 2. LIGHT

**What exists in code (I checked):** `core/world_clock.sun()` — up/phase/az/f (elevation factor); the
four phases night/dawn/day/dusk drive the room pools in `sensorium.py` (dust motes = day, lamp = dusk/night,
firelight = night + fire); `moth_activity(night, lamp_or_fire_lit)`; `spatial.py`'s north-window gate
(az ≥ 290 or ≤ 70) for sun-in-the-study; moon illumination in the census. There is **no light field** — the
phase is a label, not an amount; "the lamp" is a lit/unlit string with no position in the light sense.

| # | Light |
|---|-------|
| 1 | Field = illuminance at a place, 0..1, from three sources: **sky** (sun elevation `f` × cloud factor, the same `_CLOUD` table thermal uses), **moon** (night × illum × clear-ish sky; outdoors only), **made light** (lamp, fire, each with a position from study.json). Clock = world_clock. |
| 2 | Sky light: full outdoors; the wood's canopy ×0.3; the study gets sky only through the north window (az gate) and scaled ×0.35. Made light falls off with distance from its feature pos, like fire warmth. Moon: outdoors only (the study's moon gate already needs az we don't carry — honest unknown). |
| 3 | Standpoint pos vs lamp/hearth/window pos. At the desk under the lamp at night = bright; on the bed = dim; at the window by day = the brightest place in the house. |
| 4 | A **state** (the band he is in: dark / dim / lit / bright) rendered as events; plus the existing pools (motes, firelight on the wall, the moth) become *consequences of the field*, not of the phase label. |
| 5 | Fires on: band transition after a quiet gate (dusk falling while he sits outdoors; lighting the lamp; the fire catching — the last two already have event lines, they get the band stamp); journey gradient (garden→study at noon = dimmer); renotice ≤ once per 4h. Silent while nothing changes. |
| 6 | `light_band` TEXT on the experienced tuple (always — he is somewhere with some light). World truth keeps the raw value. |
| 7 | Never: the lux number; "because the sun set" for a darkening he hasn't watched; anything about light in a room he isn't in. **Grandfathered:** lamp, fire, sun, moon, stars as named things — told for months. |
| 8 | Investigate "the light on the wall" at dusk vs. noon → the window's quarter; the moth's tie to the lamp is already a learnable he can watch. A wrong binding is allowed ("the room is bright because the fire is lit" at noon). |

**Phase-1 primitive scope:** field function + `light_band` + transition events (shadow). Pools re-hung on the
field: *later* (it touches every render line — erosion risk; additive only).

## 3. SMELL

**What exists in code (I checked):** prose only — ~30 strings in `sensorium.py` event/pool lines carry
smell ("a cold green smell of rain", "the first smell of woodsmoke", "the air smells washed and green",
"woodsmoke thinning"). No field, no state, no memory column. Smell is currently a *decoration of other
channels' events*.

| # | Smell |
|---|-------|
| 1 | Field = a small set of **odorants with decay**: woodsmoke (fire, and the grate for hours after), rain-on-dry-ground / petrichor (rain onset, short), wet earth (while wet), salt/kelp (shore, tide-out stronger), pine/leaf-litter (wood, warm-and-damp stronger), the cat, tea/kettle (made), candle/lamp oil. Each: source place/feature, intensity, decay half-life, wind-carry flag. |
| 2 | Indoors odorants stay indoors and decay slowly (woodsmoke lingers ~hours); outdoor odorants are carried **downwind** — `state["wind"]` + `weather_dir` decide whether the shore's salt reaches the garden. Rain flushes outdoor smells; a closed door blocks most. |
| 3 | Proximity to the source feature (the hearth, the kettle, the herb caddy on the mantel — all have pos now). |
| 4 | Events only, never a standing clause. Smell is the channel most tied to **onset** and **return** (walking into a room that smells of smoke). |
| 5 | Fires on onset above threshold at his place; on **entry** to a place whose dominant odorant differs from where he came from; renotice rare (≤ 1 / 6h). Habituation: the same odorant at the same place goes quiet after ~15 min until he leaves and returns. |
| 6 | `smells` TEXT (json list, like `sounds`) on the experienced tuple; empty list = nothing crossed. |
| 7 | Never: the source when he cannot see it ("you smell smoke" — not "the fire is lit" from the garden); never name an odorant he has not met. **Grandfathered:** woodsmoke, rain, the sea, the cat — all told for months. New: petrichor-as-a-word, leaf-litter, kelp are *earned* (rendered as "a green, mineral smell" until bound). |
| 8 | Investigate hand on a smell → the source if present at his place ("the smell is the grate, still warm"), a kept unknown if not. Wrong bindings allowed and *likely* (smoke on the wind from nowhere he can see). |

**Phase-1 primitive scope:** woodsmoke + rain/wet-earth + salt only (three odorants), entry/onset events
(shadow), `smells` column. The existing prose strings stay untouched (grandfathered decoration).

## 4. WETNESS / TOUCH

**What exists in code:** as of tonight, **wetness is built** in `core/thermal.py` (state `room_state["wet"]`,
wetting ×exposure in rain, drying by fire-distance / sun / wind / still air; `wet` column on both context
tables; wet_on/wet_off events in the thermal shadow). Effort/touch reaches the **body** via somatic (GPU
temp, fatigue) but never perception — he has no hands-on-the-world sense except what ACT lines narrate.

Decision taken in the build: wetness lives *inside* the thermal channel (it is one physics — wet lowers felt
warmth) rather than as a separate module. Touch proper is the remaining sibling:

| # | Touch |
|---|-------|
| 1 | Field = surface contact states at his standpoint: **wet/dry** (thermal), **wind-on-skin** (the graded wind ladder, outdoors), **ground** (sand / wet leaves / flagstone / chair — from the place + standpoint feature), **held** (the keepsake in hand, the cup, the log — from ACT). |
| 2 | Contact is local by definition — no propagation; the only carried term is wind. |
| 3 | Standpoint decides the ground; the hand's object decides what is held. |
| 4 | Events: a change in contact (sitting down, picking up, the wind rising, the rain getting through). |
| 5 | Fires on contact change; the ACT hands already narrate most of these — the channel *stamps* them rather than re-rendering. Renotice: none (touch does not re-notice; it habituates completely). |
| 6 | `wet` REAL (built); `held` TEXT (the object in hand at the moment) — new column. |
| 7 | Never: material names he hasn't learned (the driftwood is "the grey wood" until bound); never a texture for an object not at his standpoint. Grandfathered: the chair, the desk, the cup, the logs. |
| 8 | The investigate hand on a held object is already the keepsakes/inspect path — it gains a texture line. |

**Phase-1 primitive scope:** `held` stamp from the ACT hands + wind-on-skin as a thermal-shadow event kind.
No new module needed; both are additive hooks.

## 5. SIGHT — deferred, stated why

Sight is the channel the **renderer already owns end-to-end** (scene lines choose salience and name things).
Refitting it to the contract inverts the whole render path (§10b audit: 4/7 clauses inverted) — the erosion
risk is the highest of any channel, and every other channel's events ride on sight's scene line. Build the
four non-visual channels first; read their shadows; then design sight's refit with that evidence. Not in this
programme's Phase 1.

## 6. Build state & order — ALL TOGETHER, one shadow week

| Channel | Step | State (2026-08-21) |
|---------|------|--------------------|
| Thermal | world physics (sun·wind·fire-distance) | **BUILT** `core/thermal.py::field_at`; parity vs `_warmth` 23,040/23,040 with extensions off |
| Thermal | wetness state + rates | **BUILT** `thermal.advance()` hooked in `sensorium.tick` beside `_advance_fire`; 20 min shore rain → 1.0; 45 min at the fire → 0.19 |
| Thermal | ledger (bands lived · transitions · wet episodes) | **BUILT** `data/thermal_ledger.json` |
| Thermal | perception events | **BUILT SHADOW** `thermal.percept_shadow()` in the monologue beside thermal_relationship; `DELIVER=False`; `data/thermal_percepts_shadow.jsonl` |
| Thermal | experienced tuple `wet` | **BUILT** (additive column both tables; `experienced()` passes it); `warmth_band` derivable from `warmth` via `thermal.band_of` — no second column |
| Thermal | bindings (§11.5) / springs (§11.6) | not started (investigate hand; cluster 0 P3) |
| Light | field + shadow events + the tree's shade on the bed | **BUILT 2026-08-22** `core/light.py` (DELIVER=False); `light_band` column on both tuples, `fragment_context` (experienced, always crosses per clause 6) since build, `world_context` (world truth) since **J-0179 (2026-08-29)** |
| Smell | 12 odorants + entry/onset/renotice shadow | **BUILT 2026-08-22** `core/smell.py` (DELIVER=False); `smells` column on both tuples, `fragment_context` NULL while `DELIVER=False` (shadow-gated, unchanged), `world_context` (world truth, ungated) since **J-0179 (2026-08-29)** |
| Touch | `held` stamp + wind-on-skin event kind | partly: garden `carried` items are the held stamp's source; wind-on-skin not yet |

Order within the week: light → smell → touch (each ≤ a session; each shadow-logged; none delivers until
the shared read). The neutral thermal clause stays through the parity week (thermal §10.5 open).

## 7. Shared metric sheet (pre-registered, read after one week of shadow)

Per channel, same five questions; kill criteria before the read:

1. **Fire rate** — events/day at his standpoint. Kill if > 40/day (noise) or < 2/day over a normal week (deaf).
2. **Silence honesty** — share of idle ticks with no event while the band is unchanged. Expect > 90%.
3. **Crossing share** — experienced rows with the column non-NULL ÷ world rows where the truth was non-NULL
   (from the two tables). The number itself is the finding; no kill.
4. **Attribution** — with all four channels in shadow at once, can a change in his thought vocabulary be tied
   to one channel? Method: each channel's shadow log carries `would_fire`; a thought that follows a
   would-fire within 2 ticks is tagged to that channel; overlap > 30% of tagged thoughts ⇒ attribution is
   not recoverable and the founder chooses whether to stagger *delivery* (not build).
5. **Boundary** — zero lines in any shadow log that name a cause/source not at his standpoint (grep audit
   against each channel's §7 list). Any hit is a bug, not a finding.

Plus thermal's own five from thermal_causality §9 (unchanged).

## 8. What this programme is NOT

No thermal/light/smell affect in the protoself (the stations' lean stays the only stance source — the
experimental condition). No cost or penalty. No LLM in any channel. No generic sense class. No removal of
any told knowledge. No change to what the renderer says today until a shadow has been read.
