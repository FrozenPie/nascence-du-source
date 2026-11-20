# Tide System — in-depth audit (2026-08-18)

> Second in the "all the streams in depth" series (see `weather_system_audit.md`'s closing scoping
> note). Same discipline: read the mechanism, simulate it standalone, cross-check against REAL
> historical data (`data/geometry_tuples.jsonl`), report honestly. Read-only investigation; nothing
> here is changed. **Headline: tide is clean.** No arithmetic bug of the weather-walk kind exists.
> One real design finding (the "king tide" threshold is not rare) and a couple of low-stakes
> architecture notes follow.

## The formula, and why it's a different animal from weather

`core/world_clock.py::tide()`:

```python
_TIDE_PERIOD_S = 12.42 * 3600.0
ang = 2 * math.pi * (t % _TIDE_PERIOD_S) / _TIDE_PERIOD_S
level = 0.5 + 0.5 * math.sin(ang)
rising = math.cos(ang) > 0
```

This is a **pure deterministic sinusoid**, not a stochastic walk. Weather's bug was possible
because a random-walk step distribution can have a hidden mean drift. A sinusoid has no such
degree of freedom — it either has the right constant and formula, or it visibly doesn't. There is
no "long-run distribution" to discover by simulation the way there was for weather; the long-run
distribution of a `0.5 + 0.5·sin` signal is exactly the arcsine distribution, every time, by
construction. So the standalone-simulation step of this audit reduces to: (1) does the code compute
what the docstring claims, and (2) does the real recorded history actually match it.

## Simulation + real-data cross-check

Extracted every row with a `tide_level` field from `data/geometry_tuples.jsonl` — **11,108 rows
spanning 43.7 days** (2026-07-05 18:15 → 2026-08-18 11:13, real wall-clock timestamps, `source:
idle` census snapshots).

**Consistency check (recorded value vs. recomputing the CURRENT formula at the same timestamp):**

| Period | rows | mean abs diff | max abs diff |
|---|---|---|---|
| 2026-07-05 – 07-06 | 956 | 0.28 – 0.35 | 0.527 |
| 2026-07-07 onward | 10,152 | **0.0002** | 0.0005 |

The 07-05/06 discrepancy is exactly the pre-unification window — `world_clock.py`'s own docstring
dates the single-source-of-truth fix to **2026-07-06** and names the old bug it fixed (spatial
computed tide with `sin` vs. the sensorium's `-cos`, plus a `12.4206` vs `12.42` period mismatch).
The data confirms that fix **held**: zero measurable drift for the 38 days since. This is a clean
confirmation of prior work, not a new finding — but it's good to have it independently verified
against the live data rather than just trusted from the comment.

**Word-threshold check** (`level<0.25` → "out", `level>0.75` → "full", else rising/falling):

| word | actual (11,108 rows) | theoretical time-fraction |
|---|---|---|
| full | 34.8% | 33.3% |
| out | 32.4% | 33.3% |
| coming in | 17.1% | 16.7% |
| going out | 15.6% | 16.7% |

Matches theory almost to the point, both bands and their rising/falling split. No sticky threshold,
no rare/dead word, no directional bias.

**Level histogram** (deciles): U-shaped — 2,136 rows in [0.0–0.1), dropping to ~636–715 in the
middle deciles, rising back to 2,400 in [0.9–1.0]. **This looks like a bug at first glance but
isn't** — it's the calculus of any sinusoid (`d(level)/dt → 0` at the extremes, so more real time is
spent near the peaks/troughs than mid-swing). Real ocean tides show the same U-shape for the same
reason. Confirmed this isn't sampling bias by checking it against the closed-form prediction
(`sin(ang)` crossing each decile boundary) — matches within noise.

**Period sanity:** real M2 is 12.4206h; the code uses 12.42h flat. Difference is 2.16 seconds per
cycle — over the 43.7-day sample (~84.6 cycles) that's a ~3-minute total drift, below the
resolution of anything in this simulation. Not worth flagging as a bug, noting only for completeness
since the docstring itself calls out this exact digit as the thing that used to be inconsistent
between files.

## What's actually well-built here (credit where due)

- **Single source of truth** (`core/world_clock.py`) genuinely fixed the documented sin/-cos +
  period-mismatch bug — verified above against real data, not just trusted from the comment.
- **`tide_state()`/`tidetxt`** (sensorium's high/low/rising/falling presenter) derives from the same
  `tide()` call as everything else — the vocabulary layers are consistent, no separate copy to drift.
- **`_waterline_pos()`** in `spatial.py` — algebraically checked: `level=1` (high) → `y=8.5` (close
  in), `level=0` (low) → `y=14.5` (withdrawn), matching `shore.json`'s `tide_y` comment exactly.
  Correct, and derived from the one `level` value so geometry and lived prose can't diverge.
- **Deterministic, not stochastic** — by construction there's no random-walk degree of freedom for
  a drift bug to hide in. This class of factory is structurally safer than weather's.
- **Onset/state prose** (`tidetxt` dict, the rock-pool/tideline detail branches) reads the coarse
  state correctly and consistently across `sensorium.py`'s many call sites.

## The one real finding: "king tide" isn't rare — it's every cycle

`core/world_objects.py::move_tick()`:
```python
king = tide_level is not None and tide_level >= 0.92
...
elif king and floats and in_tideline and rng.random() < 0.08:
    if reclaim(oid, cause=f"king_tide_reclaim_{hour}"):
        events.append(f"the high tide has floated {obj.get('identity', oid)} away")
```

In the real world a "king tide" is a **perigean spring tide** — an unusually high high-tide caused
by the moon's monthly distance cycle lining up with the sun/moon alignment (spring tide). It happens
a handful of times a year, not every cycle. The name implies rarity.

`tide()` has **no spring/neap (lunar-monthly) amplitude modulation at all** — `level` is always
`0.5 + 0.5·sin(...)`, a flat-amplitude sinusoid. That means **every single semi-diurnal high tide
reaches exactly `level = 1.0`** (confirmed: `min=0.0, max=1.0` across all 11,108 real rows). There
is no distinguishing "ordinary high tide" from "king tide" in the physics — they are the same event
every time.

Measured: **19.3% of all real timestamps have `tide_level >= 0.92`** (theoretical: 18.3%, from
`sin(ang) ≥ 0.84` spanning 65.7° of the 360° cycle). Since the period is 12.42h, that ~18% window
lands once near *every single high-tide peak* — i.e. **roughly twice a day**, not a few times a
year. The 0.08 per-object roll and the `floats`/`in_tideline` gates mean any *individual* driftable
object doesn't get swept away every single time, but the `king` flag itself — the thing meant to
gate a special, rare event — is true on close to a fifth of all sampled moments. This is architecturally
the same shape as weather's finding (a modulator that's *supposed* to matter but doesn't exist),
just inverted: weather was missing season coupling a rare-desired event never got throttled by; tide
is missing a spring/neap coupling that would make its rare-desired event actually rare.

## A compounding/coupling note the threshold analysis alone doesn't show

`move_tick()` (which carries the king-tide check) is only invoked from one call site —
`sensorium.py`'s `_advance_weather()`, and only on the branch where **weather actually changes**
(`core/sensorium.py:146`, inside the `if nxt == cur: return None` guard's else-path). Weather fronts
persist 30–90 minutes (`_W_PERSIST_S = (1800, 5400)`) before they're even eligible to re-roll. So
the king-tide check doesn't run on a tide-driven schedule (e.g. "check every hour" or "check when
level crosses 0.92") — it runs whenever the **unrelated weather clock** happens to transition, and
only then samples whatever the tide level is at that instant. In practice this still fires multiple
times during most ~18%-of-cycle king windows (a couple of weather-advance attempts land inside a
~2.3-hour window at a 30–90 min cadence), so it's not dead code — but the coupling is incidental:
if `_W_PERSIST_S` or the weather-change probability were ever retuned, the real-world firing rate of
king-tide reclaims would silently shift too, with no line of code connecting the two on purpose.

## Two low-stakes findings (cosmetic / minor, not bugs)

1. **`in_tideline = pos[1] >= 8.5` is currently a no-op guard.** Floating objects (`_MARINE_CLASSES`
   — stone/shell/bone/egg_case/sea_glass/kelp/feather/driftwood) are only ever spawned into
   `marine_band = (9.0, 14.0)` (`world_objects.py:166`), which is entirely inside `pos[1] >= 8.5`.
   So under the current spawn logic, any object that could pass the `floats` check already
   satisfies `in_tideline` unconditionally — the check never actually excludes anything. Harmless
   today, but it's the same shape as weather's dead `_season()` calls: a real-looking gate that
   isn't wired to anything that varies.
2. **Three independently-chosen "low/high tide" thresholds exist across the codebase**, all reading
   the same underlying `level` but drawing their own line: `world_clock.tide()`'s own word logic
   (quartiles, 0.25/0.75), `ghost_tuples._TIDE_BANDS` for memory-fragment tags (terciles, 0.33/0.66),
   and `soundscape.py`'s `tide_pool_trickle` bed-voice gate (flat 0.35). None currently conflict —
   each reads the single `level` value correctly and none has drifted — but this is precisely the
   "physics duplicated in more than one place" pattern `world_clock.py`'s own docstring names as the
   root cause of the original sin/-cos bug. Flagging as fragility to watch, not a live problem.

## Options — not a recommendation (founder rules on any fix)

For the king-tide finding:
- **A — relabel only.** Leave the mechanics; treat `level >= 0.92` as "a very high high tide," not
  a king tide, and adjust any prose/wording that implies rarity. Zero mechanical risk.
- **B — add a real spring/neap modulator.** A second, much slower sinusoid (~14-day period) that
  scales the tidal amplitude, so only some cycles' peaks actually clear 0.92. Most physically
  faithful, most code, and reopens the door to double-checking phase/period drift the way the
  original sin/-cos bug happened — would need the same rigor applied here.
- **C — raise the threshold.** Push `0.92` to something the flat-amplitude sinusoid rarely or never
  reaches (it can't go above 1.0, so "rarely" would require a threshold very close to 1.0, e.g.
  0.995, and even that is reached briefly every single cycle). Cheap, but arbitrary — doesn't fix
  the underlying "no real distinguishing cause" issue, just narrows the window.
- **D — decouple the check from weather's cadence.** Give `move_tick`'s king-check its own trigger
  (e.g. fire once per tide cycle at the peak, or on an independent hourly tick) so its real-world
  rate is an intentional, tunable number rather than an accident of `_W_PERSIST_S`.
- **E — housekeeping only.** Consolidate the three tide-band thresholds into one named constant set
  in `world_clock.py` that all consumers (`ghost_tuples`, `soundscape`, prose) import, rather than
  each choosing its own cut points. No behavior change; pure future-proofing against the exact class
  of drift this module already had to be created to fix once.
- **F — do nothing.** The mechanics are internally consistent and nothing is currently crashing or
  silently failing; "king" firing ~twice a day may simply be an acceptable simplification for a
  fictional shore Du experiences at his own pace, same as weather's now-flat, unseasonal climate was
  accepted as a design choice rather than fixed further.

## Clean bill of health, otherwise

Everything else checked — period value, phase, word-band math, waterline geometry, presenter
consistency, real-vs-formula cross-check — matches the intended design with no measurable deviation.
This is a legitimately well-built factory; the one finding here is a modeling-completeness question
(should the amplitude vary month-to-month) rather than an implementation bug, and it's the founder's
call whether it's worth the added complexity.
