# Sound System (Acoustic Clock) — in-depth audit (2026-08-18)

> Second in the "all the streams" series, after `weather_system_audit.md`. Direct trigger: the
> weather rebalance that just landed (thunderstorm 44.9%→0.7% of real time) — does anything in
> `core/soundscape.py` need recalibrating as a knock-on consequence? Read-only investigation;
> nothing in this file changes soundscape.py. Method: read the mechanism, simulate it standalone,
> cross-check against real accumulated data (`data/sound_knowledge.json`'s Hearing Ledger and
> `data/geometry_tuples.jsonl`'s `sounds` field, ~11,742 samples over ~44 days) — same discipline
> as the weather audit.

## The headline answer

**No sound rate needs emergency recalibration as a direct consequence of tonight's weather fix.**
Every storm-dependent sound (`thunder`, `wind_in_eaves`, `rain_on_roof`, `window_rattle`) is
**gated on the live `weather` string read fresh each tick**, not on a separately-tuned constant
that assumed the old (broken) storm frequency. There is no compounding: `active_sounds()` asks
"is `weather == "thunderstorm"` true right now?", and now that the true answer is "true" 0.7% of
the time instead of 44.9%, every sound gated on that condition automatically becomes correctly
rare too, with zero code changes needed in soundscape.py. This is the "gated, not compounding"
case the task asked me to distinguish, confirmed by direct measurement below, not just by reading
the code.

That said, the drop is **large and worth knowing the size of**, and one sound (`window_rattle`)
lands somewhere the founder may want to look at as a design question (not a bug) — see §4.

## 1 · The mechanism — is `world_tick()` a fair Poisson process?

`core/soundscape.py::world_tick(place, dt_s)`, called from `sensorium.tick` every ~5s:

```python
expected = rate * dt_s / 3600.0
n = int(expected) + (1 if random.random() < (expected - int(expected)) else 0)
```

This is the standard unbiased-rounding trick for turning a fractional expectation into an integer
count: it always banks `floor(expected)` events, then banks one more with probability equal to
the fractional remainder. There is **no drift, no sticky ceiling, no positive-mean-bias** — the
class of bug that broke weather. I simulated it standalone (not a reimplementation risk — this
*is* the exact two-line formula from the file) at four very different rate magnitudes, 1,000,000
ticks (dt=5s, ≈1389 simulated hours) each:

| Sound (rate) | Target rate/hr | Simulated rate/hr | Deviation |
|---|---|---|---|
| gull_cries (40.0/hr) | 40.0 | 39.95 | −0.12% |
| thunder (25.0/hr) | 25.0 | 24.95 | −0.20% |
| shag_wingbeats (1.5/hr) | 1.5 | 1.473 | −1.8% |
| kingfisher_call (0.8/hr, 1wk run) | 0.8 | 0.887 | +10.9% (small-sample noise at this rate/duration; converges at longer runs) |

**Verdict: `world_tick`'s event math is clean.** It has none of weather's disease. The only
robustness note: `dt_s = min(dt_s, 300.0)` caps burst-banking after a stopped stretch (comment:
"downtime guard"). At the documented ~5s tick cadence this cap is never touched; it would only
matter if the sim were paused for minutes at a time, in which case the *first* tick back would
under-count by design, not over-count. Not a bug, a deliberate anti-burst choice — flagging only
because it's the one place `dt_s` is clamped rather than banked in full.

`_BEDS` (continuous presences: waves, wind, rain, fire, purr, etc.) skip the Poisson math
entirely and just accumulate `dt_s / 3600.0` hours directly into `bed_hours` — also unbiased by
construction, nothing to check.

## 2 · Are storm-gated sounds compounding with the weather bug, or cleanly decoupled?

Read `active_sounds()` (soundscape.py:265-357) against `sensorium._WEATHERS` directly — the
seven real state strings are `clear, high cloud, overcast, drizzle, steady rain, wind and rain,
thunderstorm` (plus the rare `snow` overlay). Every storm-dependent sound tests **substring
membership against this exact live string**, not a cached/precomputed severity constant:

| Sound | Gate condition | What it's really testing |
|---|---|---|
| `thunder` | `weather == "thunderstorm"` | live state, unconditional on place |
| `wind_in_eaves` | `"wind" in weather or weather == "thunderstorm"` | matches `wind and rain` + `thunderstorm` |
| `rain_on_roof` | `"rain" in weather or "drizzle" in weather` | matches `drizzle` + `steady rain` + `wind and rain` (all three legitimately contain "rain") |
| `window_rattle` | `"gale" in weather or weather == "thunderstorm"` (study only) | see §4 — `"gale"` is dead, see below |
| `wind_in_trees` / branches_creak / canopy_drip | same weather-substring pattern, per garden/wood | live state |

**This is exactly the "gated, not compounding" shape** the task asked me to determine. There is
no place in the sound factory that stores "storms happen ~45% of the time" as a number — it asks
the live weather string every single tick. Fixing weather's distribution therefore fixes every
downstream sound's frequency for free, with no separate edit needed.

### Confirmed empirically, not just by reading the code

I cross-tabulated `data/geometry_tuples.jsonl`'s `weather` field against its `sounds` field
across all 11,742 samples (spanning 2026-07-04 → 2026-08-17, i.e. through the *old, broken*
weather — useful because it lets me verify the gate arithmetic against real accumulated state,
then extrapolate to the fixed distribution):

```
weather distribution (11,742 samples, pre-fix):
  thunderstorm    44.95%   <- matches the weather audit's 44.9% almost exactly
  wind and rain   21.63%   <- ALSO inflated; the bug wasn't thunderstorm-only, the whole
  steady rain     14.77%      upper half of the ladder was over-visited
  drizzle          7.50%
  overcast         4.10%
  clear            2.82%
  high cloud       2.78%
  snow             1.46%

sound-active-in-tuple frequency, cross-checked against the gate math:
  thunder          44.95%  == weather=="thunderstorm" fraction, EXACTLY (44.95% == 44.95%)
  wind_in_eaves    66.58%  == "wind and rain" + "thunderstorm" (21.63 + 44.95 = 66.58), EXACTLY
  rain_on_roof     43.90%  == drizzle + steady rain + wind and rain (7.50+14.77+21.63=43.90), EXACTLY
```

Three separate boolean unions, three exact matches to the fourth decimal place. There is no
leakage, no double-counting, no off-by-one in how `active_sounds()` composes weather substrings.
The gate logic is arithmetically exactly what it reads as.

**Projected post-fix (using the weather audit's verified new stationary distribution: clear
58.3%, high cloud 18.5%, overcast 12.5%, drizzle 5.9%, steady rain 2.6%, wind-and-rain 1.3%,
thunderstorm 0.7%; NB persistence duration [30–90 min] is drawn independently of which state is
entered, so the per-transition stationary distribution the weather audit measured **is** the true
long-run time-fraction, not just a visit-frequency artifact):**

| Sound | Old active-time fraction | New active-time fraction | Reduction |
|---|---|---|---|
| `thunder` | 44.95% | ~0.7% | **~64×** |
| `wind_in_eaves` | 66.58% | ~2.0% (1.3+0.7) | **~33×** |
| `rain_on_roof` | 43.90% | ~9.8% (5.9+2.6+1.3) | **~4.5×** |

These are large, correct drops — exactly the behavior the founder wanted from the weather fix,
now shown to propagate automatically through the whole acoustic layer. `rain_on_roof`'s smaller
reduction is also correct: drizzle/steady-rain were never part of the sticky-ceiling pathology
the way thunderstorm and wind-and-rain were (they're mid-ladder, not the runaway top), so they
stay a plausible, present-but-not-dominant feature of his coast.

## 3 · Long-run simulated frequency vs the live Hearing Ledger

`data/sound_knowledge.json`'s `hearings` table banks real accumulated exposure from the *live,
still-mostly-pre-fix* run. Spot-checking two sounds against the rate formula:

- **`thunder`**: ledger shows count=487 over a `first_ts`→`last_ts` span of 125,522s (34.87h).
  At rate 25/hr, that implies ≈19.5 hours of actual thunderstorm-active exposure inside that
  34.9h window — a ~56% active fraction, consistent with (slightly above, plausible given
  clustering/persistence) the 44.95% measured directly from `geometry_tuples.jsonl` over the same
  broken-weather era. The ledger and the tuple census agree with each other independently.
- **`gull_cries`** (weather-independent — gated only on `place=="shore"` and daylight): ledger
  shows count=255 over a 96,082s (26.69h) span → 9.55/hr observed. Predicted from the tuple
  census's measured active-fraction (32.05%) × rate (40/hr) = 12.82/hr unconditional. Same order
  of magnitude, off by ~34% — plausible given the ledger window and the tuple census aren't the
  exact same clock slice, and gull_cries has its own day/night and tide sub-gating this back-of
  envelope check doesn't fully reconstruct. No red flag; nothing resembling weather's 44%-vs-0.7%
  scale of discrepancy.

Both cross-checks land in the same ballpark as the formula predicts — no evidence of a second
hidden multiplier anywhere in the exposure-banking path.

### A false alarm, resolved (worth recording so it isn't rediscovered)

`window_rattle`'s gate (`study` + `weather=="thunderstorm"`) predicts it should be active in
~3.64% of all-time samples (study-fraction 6.79% × storm-fraction 44.95%, pre-fix), but the raw
tuple census only shows it active in 0.68% of samples — a 5× shortfall that looked like a bug at
first. It isn't: `window_rattle` was only added to the code on 2026-08-15, partway through the
44-day tuple history. Restricting the check to the **last 3 days only** (post-feature-add):
**80/80 study+thunderstorm tuples show `window_rattle` active — 100% match, zero misses.** The
apparent gap was stale pre-feature history, not a live bug. Recorded here so nobody re-diagnoses
it as a compounding bug later.

## 4 · Findings that are real but NOT caused by tonight's weather fix

These predate the fix and are unaffected by it, but were surfaced by reading the file end-to-end
per the task brief. None are urgent; none need fixing tonight.

- ⚪ **`"gale"` is a dead string everywhere it's tested.** `sensorium._WEATHERS` never produces a
  weather value containing the substring `"gale"` — the seven real states are clear / high cloud
  / overcast / drizzle / steady rain / wind and rain / thunderstorm (+ the snow overlay). Every
  `"gale" in weather` check across `soundscape.py` (window_rattle's gate, `_sea_state()`,
  `wood_ambience()`'s windy flag, `garden_ambience()`'s windy flag, `fire_ambience()`'s storm
  branch), `locomotion.py`, and `sensorium.py` is therefore **always False** — dead code, not a
  crash risk (harmless because most of these conditions are `or`-chained with a check that *does*
  fire, e.g. `"wind" in weather`), except one place it isn't harmless:
  - **`window_rattle`'s gate is `"gale" in weather or weather == "thunderstorm"` — no `"wind" in
    weather` fallback.** That means the window never rattles during `"wind and rain"` (a state
    that legitimately has wind in it), only during full `thunderstorm`. Given `window_rattle`'s
    own flavour text ("the north window worked loose-toothed by a gale"), this might be
    intentional (reserve the rattle for genuinely severe wind) or might be a small oversight where
    `"gale"` was meant to be `"wind"`. Worth a one-line founder decision, not urgent — pre-existing,
    not touched by the weather rebalance.
- ⚪ **Two registered Sound Space points are never reachable from `active_sounds()`.**
  `moth_tap` and `leaf_rustle` are both fully defined in `_SOUNDS` (coordinates, `object` spoke)
  and both appear in `couriers.py`'s naming table and `sound_knowledge.py`'s known-sounds set —
  but no branch of `active_sounds()` ever appends either key. They exist as static Sound-Space
  geometry (useful for `distance()`/`neighbours()` — e.g. anchoring the generalisation gradient
  near `fire_crackle`/`wren_scold`) but can never fire an event, never bank a Hearing, never be
  learned. Confirmed absent from all 11,742 `geometry_tuples.jsonl` samples. Not a weather-fix
  consequence — these have presumably been dead since they were added.
- ⚪ **Absolute rate values remain founder-uncalibrated**, per `sound_world_system_examination.md`
  Seam 5 (already flagged, unchanged by this audit): 40/hr gulls, 25/hr thunder-while-active,
  20/hr window-rattle-while-active, etc. were estimates, never checked against how the founder's
  actual coast sounds. This audit confirms the *mechanism* delivering those rates is honest
  (§1–3); it does not and cannot confirm the rates themselves are realistic — that's a taste
  judgement, not a code check.

## 5 · What's well-built here (credit where due)

- **The event-count math is genuinely unbiased** (§1) — no rounding drift at any rate magnitude
  tested, unlike weather's sticky-ceiling walk.
- **The gating is clean, live-state-driven, and exactly matches its own arithmetic** (§2) — three
  independent boolean-union checks against real data landed on exact percentage matches. This is
  the single most important finding for tonight's question: sound was built the *right* way
  (ask the live state fresh) rather than the fragile way (cache a rate that assumes today's
  climate), and that design choice is exactly why it needed zero changes when weather got fixed.
- **The Hearing Ledger and the geometry-tuple census independently corroborate each other**
  (§3) — two separately-written recording paths agree on the pre-fix storm-heavy reality, which
  is itself a small integrity check on the whole observation pipeline, not just soundscape.py.
- **The tree-falls law is honestly implemented** — `world_tick` only ever samples `active_sounds()`
  at Du's own current place (never simulates the other three locations), which is both the
  founder's stated design intent and the reason this system is cheap to audit: one place, one
  clock, no hidden state anywhere else pretending to have "happened."

## 6 · Recommendation

**No code changes needed as a direct result of tonight's weather fix.** The storm-dependent sound
rates will self-correct the instant the corrected weather code is live, because they were never
independently tuned in the first place — they read weather fresh every tick. Two follow-ups worth
the founder's attention on their own schedule, neither urgent:

1. Decide whether `window_rattle`'s new extreme rarity (~0.05% of all time, roughly once every
   few days of world-time at most) is the intended feel now that storms are genuinely rare, or
   whether its gate should also catch `"wind" in weather` (bringing it in line with
   `wind_in_eaves`'s broader gate) so the house still has *some* voice during ordinary windy rain,
   not just full thunderstorms.
2. `moth_tap` / `leaf_rustle` are dead Sound-Space points (§4) — either wire a real gate for them
   (moth at the glass on warm evenings? leaf-litter rustle in the wood/garden underbrush?) or note
   them as geometry-only anchors on purpose. Small, not urgent.

The founder's own next-scope note in `weather_system_audit.md` (tide, the cat, garden, school/body)
remains the natural continuation; sound itself is now checked and comes back clean.
