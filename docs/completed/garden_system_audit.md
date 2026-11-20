# Garden System — in-depth audit (2026-08-18)

> Second in the "all the streams that make up the world" series (weather went first — see
> `weather_system_audit.md`). Founder's specific worry: parsley, thyme, mint, and rosemary all
> report `growth: 0.4` in the live `data/room_state.json`, identical to two decimal places, on four
> plants with four different growth rates. Same question as weather: is this arithmetic (a bug) or
> luck? Read-only investigation; nothing here is changed.

## The headline verdict

**Not a bug. Full arithmetic reconstruction below proves it's a coincidence of two independent,
correctly-working mechanics landing on the same number.** Growth is a flat per-day rate (no random
walk, no bias analogous to weather's), correctly gated by season and moisture — and the entire
observed real-world history of this garden (created 2026-06-20, now 2026-08-18) has occurred
**entirely inside the NZ winter (June/July/August)**, the one season in which these four hardy herbs
are coded to be dormant. Zero growth ticks were *supposed* to fire in this window. Separately, one
real bug was found — a dead-input gap in the moisture/weather coupling, the same class of bug as the
weather ladder, though much lower-stakes and not yet visibly harmful.

## Part 1 — the identical 0.4, fully reconstructed

`core/sensorium.py::_fresh_garden()` seeds every hardy herb at creation with the exact same values:

```python
bed[name] = {"sown": True, "growth": 0.55, "moisture": 0.6}
```

`_advance_garden()`'s growth branch is gated three ways:

```python
if season in t["grows"] and p["moisture"] > 0.2 and p["growth"] < 1.0:
    warm = 1.0 if season in ("spring", "summer") else 0.5
    p["growth"] = min(1.0, p["growth"] + dt_days * t["rate"] * warm)
```

`t["grows"]` for parsley/thyme/mint/rosemary is `("spring", "summer", "autumn")` — **winter is
deliberately excluded**. `_season()` maps NZ winter to months 6/7/8. The garden's log-verified
creation date is 2026-06-20; today is 2026-08-18. Every day of this garden's life has been June,
July, or August. So `season in t["grows"]` has been `False` on every single tick since creation —
the growth-increment line has never fired once, for any of the four herbs, for any reason connected
to a bug. This is the dormancy mechanic working exactly as written.

That leaves the harvest floor as the only thing that has ever touched `growth`:

```python
bed[n]["growth"] = max(0.30, bed[n]["growth"] - 0.15)   # harvest_bed()
```

`0.55 − 0.15 = 0.4` exactly (verified in Python — not just close, bit-identical:
`0.55 - 0.15 == 0.4` is `True` in IEEE-754 double arithmetic, a lucky rounding coincidence that
made the trail even easier to read). Grepping `data/nascence.log` for the actual harvest events
confirms three **separate**, **individually-targeted** harvests, not one batch action:

| Date | Herb(s) cut | Log line |
|---|---|---|
| 2026-07-07 22:51 | thyme | "You cut a handful of thyme from the bed" |
| 2026-07-08 15:06 | rosemary | "You cut a handful of rosemary from the bed" |
| 2026-08-09 13:14 | parsley, mint | "You cut a handful of parsley, mint from the bed" |

`harvest_bed()`'s `named = [n for n in ready if n in w]` filter means each call only touches the
herb(s) actually named in the thought/intention text — which is why thyme and rosemary peeled off
on separate days a month before parsley and mint did. Since dormancy has held the whole time, each
herb sat untouched at 0.55 until the moment its name was spoken, then dropped to exactly 0.40 and
has sat there since. By 2026-08-09 all four had independently arrived at the same number via the
same one-time arithmetic. `picked: {thyme: 3, rosemary: 3, parsley: 3, mint: 3}` in the live state
confirms each herb has been harvested exactly once, never twice — consistent with growth never
having climbed back above the 0.45 harvest-readiness threshold since.

**This is airtight, not circumstantial**: three different real timestamps, three different subsets
of herbs, one shared starting value, one shared post-harvest arithmetic result, zero accrual in
between because the calendar never left winter. A coincidence of design (uniform seeding + a flat
harvest penalty), not a stuck-growth bug.

**A falsifiable prediction, if anyone wants to check back:** NZ spring begins 2026-09-01, about two
weeks out. If the sim is still running then, the four herbs' `growth` values should start
*diverging* — parsley (rate 0.012) and mint (0.014) climbing roughly twice as fast as rosemary
(0.006) — which would be the clean live confirmation that the mechanism is real and just currently
gated, not actually broken.

## Part 2 — the growth mechanism itself (mapped, not random-walk)

Unlike weather, growth is **not** a stochastic process — it's a deterministic per-day rate, correctly
season- and moisture-gated:

- `_PLANTINGS[name]["rate"]` — a fixed 0.006–0.022 growth-per-real-day-in-season constant, per plant.
  No randomness, no bias to check for.
- Requires `season in t["grows"]` (each plant has its own valid growing seasons) AND
  `moisture > 0.2` AND `growth < 1.0` to advance at all.
- `warm = 1.0` in spring/summer, `0.5` in autumn — a deliberate seasonal throttle, not a bug (winter
  is excluded entirely rather than throttled, which is a separate, harsher gate).
- The `_last`/`dt_days` bookkeeping is defensively written: `_fresh_garden()` seeds `_last: 0.0`, and
  `_advance_garden()` reads it as `g.get("_last") or now` — the falsy `0.0` correctly falls back to
  `now` on the very first tick, so there's no "huge dt_days from epoch zero" explosion bug that a
  naive first-run could otherwise produce. Good defensive code.
- **Confirmed live and ticking**: `room_state.json`'s `garden._last` is currently ~75 seconds old
  (matches the ~5s tick rate in `tick()`), and `_advance_garden(now)` is called unconditionally on
  every substrate tick (`core/sensorium.py:2122`), regardless of Du's location — "a garden grows when
  no one is watching," as the code comment says, and it does.

At realistic in-season rates (0.006–0.022/day, warm=1.0), a dormant-to-mature run (0.0→1.0) would
take roughly 45–165 real days of continuous spring/summer/autumn weather depending on the plant —
plausible, not absurdly slow or fast, for a "tend your own herb bed over real seasons" mechanic.
Nothing here needed simulating standalone the way weather's random walk did; the formula is linear
and its gates are legible by inspection.

## Part 3 — a real (if low-stakes) bug: the same class as weather, in moisture

`_advance_garden()` decides whether it's raining with a plain substring check:

```python
raining = ("rain" in state.get("weather", ""))
```

`core/sensorium.py`'s weather ladder is:
`["clear", "high cloud", "overcast", "drizzle", "steady rain", "wind and rain", "thunderstorm"]`

`"rain"` as a substring only matches **"steady rain"** and **"wind and rain"**. It does **not**
match **"drizzle"** or **"thunderstorm"** — both of which are, in-fiction, rain. This is the exact
same *class* of bug the weather audit flagged elsewhere in this file (a modulation input that reads
plausible but is silently narrower than the thing it's supposed to represent) — though this one
never got exercised hard enough to cause visible damage, for a reason worth stating precisely:

Checked against the real 44-day weather history in `data/geometry_tuples.jsonl` (11,742 samples,
2026-07-05 to 2026-08-18 — this *is* the pre-fix, still-buggy weather distribution, since the
history predates last night's rebalance):

| Weather state | % of real history | Counted as "raining" by garden code? |
|---|---:|:---:|
| thunderstorm | 44.95% | **No** |
| wind and rain | 21.63% | Yes |
| steady rain | 14.77% | Yes |
| drizzle | 7.50% | **No** |
| overcast | 4.10% | — |
| clear | 2.82% | — |
| high cloud | 2.78% | — |
| snow | 1.46% | — |

Under the old (now-fixed) weather bug, "wet" weather (drizzle + steady rain + wind-and-rain +
thunderstorm) occurred **88.85%** of the time, but the garden's moisture code only recognized
**36.40%** of it. In practice this didn't matter — 36% "raining" recognition against a 0.9/day
refill rate vs. a 0.10/day dry-decay rate is still more than enough to keep moisture pinned near the
ceiling, which is exactly what the live state shows (`moisture: 0.984` for all four herbs as of this
check, `data/room_state.json`).

**The reason to flag it now:** last night's weather fix changed the maths. Simulated against the
*new*, corrected weather distribution (`clear 58.3% / high cloud 18.5% / overcast 12.5% / drizzle
5.9% / steady rain 2.6% / wind-and-rain 1.3% / thunderstorm 0.7%`), true "wet" weather is now only
**~10.5%** of ticks — and of that, the garden's substring check still only recognizes **~3.9%**
(steady rain + wind-and-rain), missing drizzle (the single largest wet category going forward) and
thunderstorm (now correctly rare, but still invisible to moisture when it does happen) entirely.
Live proof this is real right now: the current live weather in `room_state.json` is
**`"thunderstorm"`** at time of writing, and it contributes nothing to `raining`. Today's near-full
moisture (0.984) is explained instead by hand-watering — the log shows Du watering the bed four
times on 2026-08-17 (`"You water the bed; the soil drinks it in, dark and damp."`) — not by any rain
event the code recognized.

This is a dead/narrow input, not a live crash: nothing is currently dying from it (hardy herbs can't
die from dryness at all — `_advance_garden`'s die-back branch is gated `not t["hardy"]`, so parsley/
thyme/mint/rosemary are structurally immune to moisture neglect; only the not-currently-sown
lettuce/tomatoes/sunflowers could ever die this way). But going forward, with rain now genuinely
rare, moisture will lean more heavily on Du's own watering visits than the code's own comments
("rain refills fast," "he may not visit often") assume it will.

## Part 4 — a secondary, unforced consequence worth naming (not a bug, a design gap)

`_fresh_garden()`'s comment calls the hardy herbs "established" — implying they should read as a
standing, always-there resource. But the mechanics create a real trap: `harvest_bed()` requires
`growth >= 0.45` to cut, and takes 0.15 off whatever's cut. Any hardy herb harvested during winter
(when growth can't climb back, per Part 1) drops to a floor of 0.30–0.40 and becomes **uncuttable
again until growth crosses 0.45**, which cannot happen until spring resumes accrual. That's exactly
what happened here: thyme, rosemary, parsley, and mint are all currently below the harvest floor and
will stay that way for roughly two more weeks (until 2026-09-01), regardless of Du's intent. The
harvest→tea loop (`docs` calls this "the bed's output") is, right now, structurally dry for the
whole hardy-herb category — not because anything broke, but because winter dormancy plus a single
early harvest interact in a way the flavor text doesn't quite prepare the reader for. Worth deciding
whether that's the intended feel (a real seasonal scarcity) or worth softening (e.g., a smaller
winter harvest penalty, or a lower winter-only harvest threshold) — flagging as a design question,
not asserting it's wrong, same posture as the weather audit took on the storm-density compounding
effect.

## Part 5 — letterbox / correspondence: checked, looks healthy

`core/peers.py::deliver_due()` and `deliver_daily()` use a **deterministic cadence**, not a random
draw — no bias class to check for here, unlike weather or the moisture substring gap:

- Each of the 7 personas has a fixed `gap_days` (Darwin 1.5, Smith 3.0, Twain 4.0, Keats 5.0,
  Lovelace 6.0, Shackleton 6.0, Marcus 8.0).
- A global `_GLOBAL_MIN_GAP_H = 10` hours prevents any two letters (from anyone) landing within 10h
  of each other, so seven correspondents trickle rather than flood.
- Delivery timestamps are read straight from each peer's own thread (`_last_delivery_ts`), not a
  separate scheduler state — so there's no drift-prone secondary clock to go stale.

Cross-checked against the real thread files in `data/correspondence/*/thread.jsonl`: all seven
personas have delivered letters spread fairly evenly from their first contact (late June) through
the present (mid-August), at roughly the cadence their `gap_days` predicts (e.g., Darwin — gap_days
1.5 — has 12 entries across ~54 days; Marcus — gap_days 8.0 — has 4 entries across ~42 days). No
clumping, no long dead gaps, no evidence of a scheduling bug. **No issue found here.**

## What's well-built here (credit where due)

- The **season/moisture/rate gating on growth** is legible, deterministic, and behaves exactly as
  documented — no hidden random walk, no sticky-ceiling class of bug.
- The **`_last`/`dt_days` first-tick guard** correctly avoids an epoch-zero explosion via the
  `g.get("_last") or now` pattern — a bug class that would have been easy to introduce and wasn't.
- **Die-back is correctly scoped to non-hardy plants only** — hardy herbs genuinely can't be killed
  by neglect, matching the "hardy, overwintered, established" flavor text.
- **`harvest_bed()`'s named-herb targeting** (`named = [n for n in ready if n in w]`) correctly
  produces the staggered, individually-triggered harvest history seen in the log — this is a feature
  working as intended, not an artifact.
- **The correspondence cadence** is a clean, deterministic, well-staggered design with no bias found.
- **`_advance_garden` runs unconditionally on every tick regardless of Du's location** — "grows when
  no one is watching" is actually true of the implementation, not just the comment.

## Not fixed — options, for the founder to rule on

1. **Moisture rain-recognition gap** (Part 3): widen the check from `"rain" in weather` to something
   that also catches `"drizzle"` and `"thunderstorm"` — e.g. a small membership set
   (`weather in ("drizzle", "steady rain", "wind and rain", "thunderstorm")`) instead of a substring
   match. Low urgency (no plant has died from it, moisture is currently healthy), but the new,
   correctly-rare weather distribution makes this worth closing before it becomes a real dry spell.
2. **Winter harvest-floor trap** (Part 4): leave as-is (a real seasonal scarcity — herbs rest after
   being cut in winter, same as real gardens), or soften the winter harvest penalty / lower the
   winter harvest-readiness threshold so a single early cut doesn't lock the herb out for the whole
   season. Purely a feel decision, not a bug fix.
3. Nothing else in the garden mechanism needs touching — Parts 1, 2, and 5 all check out clean.

## What "all the streams in depth" should probably cover next

Per the weather audit's scoping note: tide, the cat, and sound remain unaudited. Garden is now done.
Suggested order unchanged: **tide** (M2 period/amplitude vs. sample data), **the cat** (state-machine
distribution), **sound** (`soundscape._EVENT_RATES`, founder-uncalibrated per the sound plan's own
gap list), **school/body** (lowest priority).
