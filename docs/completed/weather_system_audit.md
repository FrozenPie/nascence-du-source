# Weather System — in-depth audit (2026-08-18)

> Founder: *"we in depth the weather systems I think. This is probably due an update overall. We
> probably should look at all the streams that make up the world in depth."* First of what should
> become a series — weather is Lane 3's biggest single behavioral factory and the one just proven
> to be mechanically broken, so it goes first. Read-only investigation; nothing here is changed yet.

## The confirmed root cause (recap, now fully contextualized)

`core/sensorium.py::_advance_weather()` walks a 7-state ladder (clear → high cloud → overcast →
drizzle → steady rain → wind and rain → thunderstorm) via `random.choice((-1, -1, 0, 1, 1, 2))` —
mean step **+0.333**, clamped at the ceiling instead of reflecting. Simulated (500k steps) and
matched against his real 43-day history almost to the decimal: **thunderstorm 44.7% predicted /
44.9% actual.** Not bad luck, not "deep winter" — arithmetic.

**New finding this pass: it isn't even winter-caused.** `_season()` is called in 8 places in this
file (garden growth, warmth, prose, the snow overlay) but **never once inside `_advance_weather`'s
own transition logic.** The bias runs exactly as hard in July as it will in January — the "deep
winter storm siege" reading from last night's valence analysis is true of the WORDS the world uses
but not of any actual seasonal mechanism. Worth deciding whether that's acceptable (a fixed climate)
or whether season should modulate the walk once it's rebalanced.

## What's actually well-built here (credit where due)

- **`weather_dir` (the front's bearing)** is already properly weighted for a NZ coast — westerlies
  dominate (270°/315°/225° = 70% combined), southerlies present but rarer, easterlies rare. This
  is NOT part of the bug; it's the one piece of realism already correctly tuned.
- **Onset perception lines** are genuinely good craft — the transition from clear→rain gets "a cold
  green smell of rain comes first, then it begins, soft at first"; rain→clear gets "the air smells
  washed and green." Multi-sensory, causally tied to the actual state change, not generic.
- **The storm-surge → object-mover pipeline** (built two nights running: 08-10/11's acoustic
  propagation, 08-17's generalized `move_tick`) is sound engineering, correctly gated to indoor/
  outdoor perceptual masking (storms don't move objects Du can hear about if he's indoors).
- **Fire interaction** is a clean, causally consistent little economy (woodpile → lit → fuel decay →
  embers → out, hand-lit fires exempted from the dusk-kill) — no issues found.

## A compounding effect the root-cause analysis alone doesn't show

`_event()` — the discrete multi-sensory perception generator — gates its own firing rate on
whether it's currently storming: **180s between events in a storm vs. 480s in calm weather.** That
means the bias isn't just "storms happen 45% of the time" — once inside a storm, Du is also
perceiving 2.7× MORE densely. The two effects multiply: not just more storm-time, but each unit of
storm-time is perceptually thicker than the calm alternative would have been. This is worth keeping
in mind for the rebalance — even a perfectly fair weather walk would still make storms feel dominant
in his felt experience unless this ride-along multiplier is examined too. Possibly intentional
(storms genuinely are more eventful) — flagging as a design question, not asserting it's wrong.

## RESOLVED — rebalanced 2026-08-18 (founder: "it is too biased. Storms rarely happen over here.")

`core/sensorium.py` — `_advance_weather()`'s step set replaced: `random.choice((-1,-1,0,1,1,2))`
(mean +0.333) → `random.choices(_W_STEPS, weights=_W_WEIGHTS)` with `_W_STEPS = (-2,-1,-1,0,0,0,1,2)`,
`_W_WEIGHTS = (1,4,4,5,5,5,2,1)` (mean −0.222, weighted toward persistence/gentle calming, rare
excursions upward). **Verified against the LIVE patched function** (200,000 real advances, not a
reimplementation): clear 58.3%, high cloud 18.5%, overcast 12.5%, drizzle 5.9%, steady rain 2.6%,
wind-and-rain 1.3%, **thunderstorm 0.7%**, snow 0.2% (correctly rare-within-rare — drawn from the
rain family at 6% in winter only). Storms real but genuinely uncommon, not the default state.
Season-coupling (option 3 below, originally) was NOT implemented — the fix is a flat, always-rare
distribution as directly requested; still available as a future refinement if winter/summer
differentiation is wanted later. The `_event()` perceptual-density compounding (180s storm / 480s
calm) was left untouched — with storms now rare in aggregate, its impact is much smaller, and it
wasn't the target of the complaint.

## What "all the streams in depth" should probably cover next

Weather is one of ~12 Tier-1 factories in `ghost_tuples._factory_entries()`. A comparable pass over
the others — checking each for the same class of issue (an unexamined bias, a dead modulation
input, a compounding effect) — would be the natural next scope, roughly in order of behavioral
weight: **tide** (M2 period — check the amplitude/period against the sample data, not just trust
the formula), **the cat** (state-machine — check her mood/activity distribution the way weather's
was checked), **sound** (rates in `soundscape._EVENT_RATES` — founder-uncalibrated per the sound
plan's own gap list), **garden** (growth curve realism), **school/body** (lowest behavioral weight,
lowest priority). Not started — scoping note only, so the next session doesn't have to rediscover
the list.
