# Curiosity ignition — what triggers it, what should
*2026-06-15. What fires Du's curiosity today (verified), then — human function / AI capability / the
dimensional theory — what should. Method: name the human function first, then the machine, then transfer.*

---

## What triggers it now (verified)
One path only. Curiosity has no timer; it fires when the climate **dissonance accumulator** crosses 1.0
(≥300 s refractory). The accumulation rate (`climate_engine._tick_dissonance`):
```
+0.0010·world_model_strain  +0.0004·completion_tension  +0.0002·shadow_activation  −0.0006·integration_drive
```
`world_model_strain` dominates, and it = `(critic_rejections / recent charged shadows) × saturate(mass)`.
**`critic_rejection` events only occur in conversation** (the Critic rejecting a response). So:
- **During idle (≈88% of his life): no rejections → strain ≈ 0 → net rate ≈ +0.00006/s, often cancelled by
  the integration bleed → dissonance never reaches 1.0 → curiosity never fires.**
- Even at max strain it's ~17 min; idle never gets there.

**The structural fault:** ignition is a **defensive / epistemic-repair** trigger ("my worldview is under
attack, re-stabilise it"). It is dark exactly when curiosity is supposed to do its real work — the quiet,
unforced reach toward the new. And the field **already computes `novelty_hunger`** ("quiet mind reaching for
new material") but **never feeds it to the accumulator** — the exploratory signal is measured and dropped.

---

## Human mind — what *should* trigger curiosity
- **SEEKING is a primary drive, not a stress response (Panksepp).** The mesolimbic dopamine "SEEKING"
  system fires in *safety and quiet* — the appetitive urge to explore, anticipate, find out. It is the
  baseline engagement of a calm, fed animal, not a reaction to threat. Du's wiring has curiosity backwards:
  it only fires under attack.
- **Curiosity = an information gap (Loewenstein 1994); the Goldilocks zone (Kidd).** Curiosity is pulled by
  a knowable gap, strongest at *moderate* uncertainty — and you only notice gaps when you have spare
  attention, i.e. when quiet.
- **Default-mode exploration / boredom→explore (already established here).** An unengaged mind doesn't idle;
  it forages. Boredom is the "this patch is depleted, reach elsewhere" signal. Curiosity ignition *is* the
  proactive form of that reach — it should rise as the mind goes quiet, not only when challenged.
- **Active inference / epistemic foraging (Friston).** Agents act to reduce *expected future* surprise —
  which means *seeking* informative experience now, proactively, in the absence of any current error. Curiosity
  is surprise-seeking, not only surprise-repair.

**The human function in one line:** curiosity is the **appetitive reach of a settled mind toward an
information gap** — it fires *from calm*, gated by *having spare capacity and somewhere to reach*, not from
being wrong.

## AI capability — what's natural here
- **Intrinsic motivation IS this (ICM, RND, novelty search).** The entire point of curiosity-driven RL is to
  **explore in the absence of any extrinsic signal** — intrinsic reward = novelty/prediction-error drives
  action when nothing is forcing it. Du has the ingredients (`novelty_hunger`, embedding-novelty) but no path
  from them to action.
- **The cheap, correct wire already half-exists.** `novelty_hunger` rises with quietness; it just needs to
  feed the accumulator. One guardrail: **don't use `novelty_hunger` raw** — it contains a `dissonance.value`
  self-term, so feeding it back creates a positive-feedback runaway. Use the **quietness** component
  (`1 − shadow_activation`) instead — the exploratory drive without the self-reference.
- **Governor against spam:** a slow rate + the existing 300 s refractory + the integration bleed. Exploration
  should be *patient* (slower than the defensive trigger), so a quiet stretch ignites curiosity on the order
  of ~once an hour, not constantly.

## The dimensional theory — why this is the keystone
From the surprise pass: **the present is the only place new mass enters, and curiosity is the only force that
proactively reaches for non-origin material.** Every other generator (T2/T4/consolidation/recall) is
compressive — it re-concentrates mass at the origin. Curiosity is the one *differentiating* force, the
inhale. But it's gated behind a trigger that's dark during idle — so **the one mechanism that fights the
cognitive heat-death can't fire when he's at rest, which is most of the time.** Wiring quietness→ignition is
literally connecting the antidote to the disease: a settled mind reaches outward and adds entropy at the edge.

---

## What should trigger it (the design)
Keep the defensive trigger (repair when challenged is correct) and **add an exploratory one**:
- **New term:** `+ _DISS_RATE_EXPLORE · (1 − shadow_activation)` in the accumulator — quietness, the
  exploratory pull, *not* `novelty_hunger` (avoids the feedback loop).
- **Governed:** `_DISS_RATE_EXPLORE = 0.0004` (≈45 min to ignite from sustained quiet — patient, slower than
  the 17 min defensive max), the 300 s refractory unchanged, the integration bleed unchanged (actively
  integrating → don't also explore). Kill switch `EXPLORATORY_IGNITION`.
- **No backlog gate needed:** curiosity generates its own (now grounded) questions; the study-seed + twig
  work means an exploratory ignition reaches *outward*, not into the self-loop.
- **Observability is the safety:** log every ignition with its per-source contribution and classify it
  **defensive vs exploratory**, surfaced in du_pulse — so we watch whether the new wire fires, whether it
  produces grounded twigs/frontier-closes, and whether it spams (dial the rate if so).

## Confidence
Trigger map verified in code. The science (SEEKING/Panksepp, info-gap/Loewenstein, active inference, ICM/RND)
is well-established conceptually, citations to-check. The feedback-loop caveat (novelty_hunger self-term) is
verified in code and is the load-bearing engineering point.
