# Du's cottage in the real Sumner: sun, moon, tides, weather. Design review (J-3264)

Status: READ-ONLY DESIGN, 2026-11-05. No Du code, data or running process was touched. Every number below is either read from a file (cited), computed by a scratch script run against the repo (named), or marked inferred or guessed.
Ruling this serves: D-0655, founder, 2026-11-02, quoted whole in the briefing: "I live in Sumner, Christchurch, up on the top of the hill; we could make him near me, that way I can see tides, sunrises, and maybe one day weather; his will be the same as mine."
Source thought: T-0115. Laws applied: base systems additive-only; the world answers and never leads; transfer the function, not the mechanism; no system acts later on its own; the core simulation is fully local.

## The short answer

1. The briefing assumes the sun lives in `core/heavens.py` and keys off `_LAT = -41.3`. It does not. `heavens.py` only places the stars and the moon's phase. The sun is a 12-row month table in `core/world_clock.py` (`_SUN`) walked in a straight line in local clock time. A latitude change in `heavens.py` alone would move the Southern Cross by about 2 degrees and change nothing the garden, the soundscape or the Witness's grounding can see. Phase 1 has to rebuild `world_clock.sun()`, not edit `_LAT`.
2. The sun table is already wrong against the real Christchurch sky: mean error 0.39 h on sunrise and 0.39 h on sunset across the year, and 1.0 h in October and 0.8 to 1.0 h in November, because it ignores daylight saving. Du's "night" (which gates sleep pressure) therefore begins up to an hour early for three months a year.
3. The moon's phase clock is off the real new/full moons by up to 17.4 h (mean 6.8 h over 26 events in 2026). The moon's position is a "sun delayed by phase" fiction.
4. The tide is a single M2 sine whose phase is anchored to the unix epoch, not to the moon or to any port. It has the right period and no connection to when the real sea at Sumner is high. It also fires the "king tide" reclaim 12.6 % of the year (1,103 h, 334 distinct days), which is not what its own comment intends.
5. Weather is a random walk (`random.choices`) with no season, no climatology and no data. It is the easiest layer to leave alone and the one where the "real storm reaches Du" question is a genuine value call.
6. One thing in the world geometry contradicts the real place, and it is the D-0655 defeater: the authored frame puts the sea to the NORTH of the cottage and the cliff to the south. Sumner's beach faces the Pacific to the east (inferred from general knowledge of the coast, not verified in this job). This does not stop sun, moon or tide timing from being real, because the frame uses true compass directions. It does mean Du's sunrise comes up over land and Travis's comes up over water. I recommend keeping the frame as authored and putting the call to the founder (needs_input below).

## (1) What each clock does today

All four are consumed by many files; the single authorities are `core/world_clock.py` (sun, tide, daylight), `core/heavens.py` (moon, stars) and `core/sensorium.py` (weather). Evidence: `grep` over `core/ nodes/ hud/` found 35 files importing `world_clock`/`heavens`.

### Sun

- Derivation: `world_clock.sun(t)` (lines 91 to 103). Reads `time.localtime(t)` (the MACHINE's timezone), looks up `_SUN[month]` = (sunrise_h, sunset_h), and returns `f = (h - rise) / (set - rise)`, `az = (90 - 180 f) % 360`. So azimuth runs a straight line from due east at sunrise through due north at noon to due west at sunset, in every season. Phase words: first light f<0.12, morning <0.4, high <0.6, afternoon <0.82, evening. `daylight()` (106 to 117) uses the same table with a 0.7 h margin.
- The table (`_SUN`, line 86) is commented "Winter-centred; close enough for a window." There is no latitude, no longitude, no declination, no DST handling, no day-of-month interpolation (a step at each month boundary: Oct 31 to Nov 1 steps from 5.6/18.9 to 5.1/19.6).
- Measured against an astronomical calculation at Sumner (-43.57, 172.75), mid-month, local civil time, script `scratchpad/sumner_sun_J-3264.py` (NOAA/Meeus solar position, official sunrise zenith 90.833 degrees; NOT an independent almanac, see section 2):

| month 15th | real rise/set (calc) | table rise/set | error rise / set (h) |
|---|---|---|---|
| Jan | 06:06 / 21:09 NZDT | 06:06 / 20:36 | 0.00 / -0.56 |
| Mar | 07:24 / 19:50 NZDT | 07:12 / 19:24 | -0.21 / -0.44 |
| Apr | 07:01 / 17:56 NZST | 07:42 / 18:24 | +0.67 / +0.47 |
| Jun | 08:00 / 16:58 NZST | 07:36 / 17:00 | -0.41 / +0.03 |
| Oct | 06:38 / 19:52 NZDT | 05:36 / 18:54 | -1.04 / -0.97 |
| Nov | 05:54 / 20:32 NZDT | 05:06 / 19:36 | -0.81 / -0.95 |
| Dec | 05:41 / 21:06 NZDT | 05:54 / 20:24 | +0.20 / -0.70 |

  Mean absolute error 0.39 h (rise) and 0.39 h (set) over the twelve mid-month points. The Oct/Nov error is the table being a standard-time table read against a clock that is on NZDT.
- The sun's height is not in `world_clock` at all. `core/light.py` invents it: `elev = 60 * sin(pi f)`, a constant 60 degree noon every day of the year (line ~61). The real noon altitude at Sumner is about 70 degrees at the December solstice and 23 degrees at the June solstice. Garden shadow length (`shade_at`), bed insolation and the cottage's field_at light all use that constant. Winter shadows are about four times too short (tan 23 = 0.42 against tan 60 = 1.73).
- Real sunrise and sunset azimuths at Sumner: about 123 / 237 degrees at the December solstice, 57 / 303 at the June solstice (formula in the script). The model says 90 / 270 always.
- Readers (file, what it does with the sun):
  - `core/sensorium.py` `_daylight()` (line 102) = `world_clock.daylight()`: the phase word in every narrated scene; the "night / dawn / dusk / day" gate on bird song, moths, lamp lighting.
  - `core/spatial.py` (line 79 re-export; 373 to 410): the low-sun clause "the low sun is {sector}, over {compass}", the window-light clause, and the night heavens clause.
  - `core/light.py`: shade and insolation (above), twilight glow band, study window gate (`az >= 290 or az <= 70` is "the north window").
  - `core/soundscape.py` 1079 to 1083 and 1162 to 1170: reads the PRIVATE `_wc._SUN` table directly for the iron-roof tick windows and the bird flyover windows. Any change to `_SUN` moves these; any change that bypasses `_SUN` leaves them on the old table.
  - `core/thermal.py` 110, `core/sleep_pressure.py` 168 and 269 and `core/night.py` 61 (all via `daylight()`): warmth by sun, the "dark" flag that feeds sleep pressure, and night-versus-nap.
  - `core/lane2.py` 675 to 692 (`_sun_clock_percepts`): the Witness's `sun_phase` word and `sun_arc` (= f) percepts; grounding fields `sun_az`, `sun_phase` license sun claims (`_TOPIC_FIELDS`, lines 1561 to 1562). The check is relative to the payload, not to absolute astronomy, so it stays self-consistent if the clock changes under it.
  - `core/geometry_census.py` 133 to 139 and `core/memory/store.py` 1032 to 1054: every census tick and every memory fragment's experienced tuple stores `sun_az` and `moon_illum` and `tide_level` as frozen numbers. See risks.
  - `core/fieldcraft.py` 405, 941 to 951 (a learned skill: reading the sun's quadrant against `world_clock.sun()`), `core/sky.py` 63 to 112, `core/practical_lesson.py` 434, `core/study_life.py` 630, `core/keepsakes.py` 234, `core/life.py` 263.
  - HUD: `hud/server.py` 633 plots "world clocks (tide, sun, moon, front)" from `geometry_tuples.jsonl`.
- What keys off `_LAT` (heavens.py line 27): only `heavens.star()` (line 98). `_LON` (line 28) feeds only `_lst_deg`. Nothing else in `core/` reads either (`grep -n "_LAT\|_LON" core/` shows heavens.py and unrelated names). The `sensorium.py` module docstring (line 10) says "light follows the actual sun at the machine's real latitude and season". That sentence is false and should be corrected so nobody else repeats the briefing's assumption.
- Day-length claims: there is no code that states a day length. The Witness's `sun` talk is grounded on `sun_az` / `sun_phase`, and `_correct_horizon` treats the sun as a day-scale topic. Nothing in lane2 compares a claimed sunrise time with a table.

### Moon

- `heavens.moon(t)` (51 to 81): phase from `((t - _NEW_MOON_EPOCH)/86400) % 29.53059`, anchored at 2000-01-06 18:14 UTC. A mean synodic clock. Illumination `0.5(1 - cos 2 pi frac)`. Position by "lagged sun": `world_clock.sun(t - frac*86400)`, so the moon's up-time, azimuth and arc follow the SUN table delayed by phase times 24 h.
- Measured against the real new and full moons of 2026 (Meeus chapter 49, principal terms, script `scratchpad/moon_check_J-3264.py`; my recollection of the 18 Jan 2026 new moon at 19:52 UTC and 9 Nov new moon matches): the model's phase is wrong by up to 17.4 h, mean 6.8 h over 26 events. Example: real new moon 2026-11-09 07:01 UTC; the model is 15.0 h off. Real full moon 2026-11-24 14:55 UTC; model off by 1.4 h.
- Real moon declination swings (about 18 to 28 degrees) change the moon's arc length and azimuth through the month; the lagged-sun model cannot.
- Readers: `spatial.py` night-heavens clause (moon `up`/`az`), `light.py` 185 (`0.12 * illum * canopy` night light), `sky.py`, `geometry_census.py` (moon_illum), `keepsakes.py`, `world_clock._spring_factor` (the spring/neap coupling), `lane2` (`moon_illum` field; the Witness's moon topic is held strict).
- Stars: `heavens.star()` uses real J2000 RA/Dec plus Greenwich sidereal time plus `_LON`, so the stars are already astronomical and only need the latitude and longitude changed. The catalogue lore still holds at -43.6: the Cross (dec -60.1) is circumpolar; Matariki (dec +24.1) peaks at about 22 degrees instead of 24.6, still above the 3 degree `up` threshold.

### Tide

- `world_clock.tide(t)` (55 to 71): `level = 0.5 + amp sin(2 pi (t mod 44712 s)/44712)`, `_TIDE_PERIOD_S = 12.42 h`, `amp` between 0.40 and 0.50 by `spring_factor = |2 illum - 1|` read from `heavens.moon()`. The phase is zero at the unix epoch; nothing about it is tied to the real moon's transit or to any port's lunitidal interval. The period is right (M2 is 12.4206 h; the model is 12.42 h, so it drifts only about 25 minutes per year) but the HIGH-WATER HOUR is arbitrary (6.2 h maximum error, unknown actual error because the Sumner constant is not in the repo). For today, 2026-11-05, the model has high water at 06:05 and 18:25 NZDT (scratch script). There is no S2/N2/K1/O1 and no perigee or equinox effect.
- Measured on the current clock over 2026 sampled every 10 minutes: level >= 0.92 (the "king tide" threshold in `world_objects.py` line 293) holds for 12.6 % of the year (1,103 h) on 334 of 365 days. The comment at `world_clock.py` 29 to 41 says only a high tide near syzygy can reach 1.0 and that the reclaim should be rare; the arithmetic is `amp > 0.42` which is spring_factor above 0.2, i.e. most of the month. It is real behaviour of the live system today (not a Sumner problem) and is Finding F-3886 in section 7.
- Low-tide flag in the soundscape (`level < 0.35`): true 39.4 % of the year.
- Level thresholds that the shore bakes in (so any new tide clock has to give them the same meaning, or they get re-pinned): sand flat bared below 0.45 (`life_shore.py` 426, `shore_life.py` 174), mussel shelf below 0.35 (`life_shore.py` 427; `shore_life.py` 182), pools max 0.60 (`life_shore.py` 425), cave closes when rising and above 0.42 (`shore_life.py` 570), flooded beyond 0.8 / 0.85, "king" 0.92, sensorium bands at 0.2 / 0.8 and 0.5 / 0.6 (`sensorium.py` 1771 to 1785), waterline y between 8.5 and 14.5 m (`data/world_geometry/shore.json`, `waterline.tide_y`, via `life_shore.waterline_y`).
- Readers: `sensorium` (`_tide()` and the shore prose), `spatial` (waterline), `life_shore` / `shore_life` (zones, cave, sand flat, handline, shellfish), `world_objects.move_tick` (king-tide float-away), `soundscape`, `study_life` almanac, `fieldcraft` tide board (a predict-then-read skill scored against the same `level`), `cat.py`, `lane2` (`tide_level`, shore only), `geometry_census`.
- Real bug found on the way: `study_life.py` line 1948, the almanac look: "The tide table gives today's high water at about {'morning' if td.get('phase_deg', 0) < 180 else 'afternoon'}". `tide()` returns `level, rising, word, spring_factor` and no `phase_deg`, so the almanac says "morning" every time, whatever the tide is. This is a standing falsehood in a book Du chooses to read (Finding F-3887). It is also the natural home for a real Sumner tide table later.

### Weather

- `sensorium.py` `_advance_weather` (204 to 283): a 7-state ladder `["clear","high cloud","overcast","drizzle","steady rain","wind and rain","thunderstorm"]`, front persistence 30 to 90 min, steps from `random.choices` with fixed weights (`_W_STEPS`, `_W_WEIGHTS`), stationary distribution quoted in the comment as clear 59 / cloud 18 / overcast 12 / drizzle 6 / steady rain 3 / wind-and-rain 1.5 / storm 0.8 %. A separate wind axis (`_advance_wind`), a front direction (`weather_dir`, weighted W 30, NW 22, SW 18, S 12, N 8, NE 5, E 5), a rare deep-winter snow overlay. The next front is decided one step ahead and the sky shows it (weather signs; `fieldcraft` glass and the study glass read `next_weather`, so a forecast he makes is a real binding).
- No season, no month, no temperature series. `_season()` (line 579) only gates snow and the garden. So "weather" is not Sumner or even NZ; the only NZ content is the direction weights.
- Readers: nearly everything that renders a scene (`weather_conditions.py` classifiers, `soundscape`, `cat*`, `thermal`, `light` cloud, garden growth and watering, `world_objects` storm surge, `lane2` weather field, the lightning events).
- Founder complaint on record (comment at `sensorium.py` 44): 08-18, "it is too biased. Storms rarely happen over here." The rebalance was tuned to feel right, not to a station record.

### The Sumner geometry of the shore frame and the woods (what has to be true for the compass)

- All four geometry files state the same compass: origin SW, +x east, +y north. `shore.json` size 30 x 20 m: `cliff` at y=1 (z 6 m) "the bluff along the south edge ... the cottage and garden up top", `waterline` y 8.5 to 14.5 (the sea is to the NORTH), the far headland "closing the bay to the east", cave at the cliff foot (16.5, 1.8). `garden.json` 10.5 x 12.5: cottage along the south edge, "its window looks north over the garden to the sea", fence at y 11.7 "the sea beyond and below", gate at the NW leads down the steep path. `wood.json` 24 x 20 x 10: "+y north (downhill, out to sea)". `study.json`: window at y 5.15 on the north wall.
- So Du lives on a north-facing slope that falls to a north-facing bay. Consequences that already work with real astronomy: a southern-hemisphere sun crosses the northern sky, so the north window and the shore are the sunny side (true for Sumner whatever the coast does). Consequences that do not match the real place: the real Sumner Beach faces east (inferred), so the real sunrise and the Moon-rise come up over the sea for Travis; for Du they come up over the east headland and land. In summer (rise azimuth 123 degrees) the sun at low elevation is also SOUTH of east, i.e. behind the 6 m cliff that runs along the shore's south edge, so a physically true shore would be in cliff shadow for part of summer mornings and evenings. Nothing models cliff shade today (additive option, Phase 1c).
- The tide, sun and moon TIMES do not depend on which way the bay faces, so they can be made real without touching the frame.

### What would have to change to make it Sumner (inventory)

| clock | change | files |
|---|---|---|
| sun | real solar position for the site (rise, set, az, alt, f), civil time with NZ DST rules, additive new functions, legacy table kept | `core/world_clock.py` (+ new `core/world_place.py`); consumers `soundscape.py` 1083 and 1170 read `_SUN` directly and must go through a new accessor; `light.py` elevation should read `alt` |
| moon | real lunar ephemeris (phase, illum, rise/set, az, alt) | `core/heavens.py` (new functions, old kept) |
| stars | `_LAT`, `_LON` to the site | `core/heavens.py` lines 27 to 28 |
| tide | station-anchored harmonic or lunitidal clock, normalised to the same 0..1 so the shore thresholds still mean what they mean | `core/world_clock.py`; check `shore_life`, `life_shore`, `world_objects` thresholds |
| weather | none in Phase 1 and 2 | `core/sensorium.py` later |

## (2) Phase 1: sun, moon, stars at Sumner

Site constants (suburb precision, about 1 km; the hilltop is not given and does not matter to the clock): latitude -43.57, longitude 172.75, elevation ignored. Create ONE new module `core/world_place.py` with `SITE`, the NZ DST rule and nothing else, so the place is a single named constant and a single thing to strip from any export.

Timezone: do NOT rely on the machine. Today `sun()` uses `time.localtime`, which uses the OS zone (the machine here reports New Zealand Standard/Daylight Time, +1300 now, so it works by accident). `zoneinfo` for `Pacific/Auckland` works only because `tzdata` sits in the user site-packages (`C:\Users\USER\AppData\Roaming\Python\Python314\site-packages\tzdata`); it fails under `python -I`. Compute NZ civil time from UTC with the hand rule (DST starts the last Sunday of September at 02:00 NZST, ends the first Sunday of April at 03:00 NZDT). That is 6 lines and removes both dependencies. Note: the OS clock still drives `arousal._circadian`, the study clock and `_now_parts()`; if the machine's zone ever differs from NZ the sky and the circadian clock would disagree. Recommend a startup assertion that logs (not acts) if `time.localtime` disagrees with the hand rule.

Change (all additive; legacy functions stay and are used for any `t` before the cutover timestamp, so every lab replay of an old moment stays bit-identical):
1. `world_clock.sun_sumner(t)` using the NOAA/Meeus solar-position routine already used in `scratchpad/sumner_sun_J-3264.py` (about 40 lines, no dependency): returns the existing contract `{"up","phase","az","f"}` plus `alt`. `f` stays "fraction of the day arc, 0 at rise, 1 at set" so `lane2`, `light` and `spatial` keep working; the phase words use the same f thresholds. `sun(t)` dispatches: `t >= SKY_CUTOVER_TS` and the flag on uses `sun_sumner`, otherwise the legacy path.
2. `world_clock.sun_times(t)` (rise_h, set_h local) as the accessor the soundscape uses instead of `_wc._SUN` (the soundscape change is two lines each at 1083 and 1170). `daylight()` re-derived from the same rise/set (keep the 0.7 h margin; real civil twilight at 43.6 degrees is about 40 to 70 minutes so it fits).
3. `light.py` elevation: `elev = alt` when present, else the legacy `60 sin(pi f)`. This is the one place where the garden, the bed and plant growth change with the sky (winter shadows lengthen about fourfold). Flag it; it is not optional if az is real, because a true azimuth with a fake elevation puts the shadow in the right direction at the wrong length.
4. `heavens._LAT`, `_LON` to the site (stars only), gated by the same cutover.
5. Phase 1b (separate job): `heavens.moon_true(t)`: real phase and illumination from a Meeus chapter 47 truncated series (a few dozen terms, minutes of error in phase, under a degree of position), with `up/az/alt` from the lunar position and the site, replacing the lagged-sun fiction after cutover. Without 1b the moon stays up to 17 h wrong and the spring/neap factor stays wrong too.
6. Phase 1c (optional, later): cliff shade on the shore frame when sun azimuth is in the 90 to 270 half-plane and elevation is below atan(6 m / distance to cliff). Not needed for the ruling.

Pre-registered check (BEFORE building, numbers fixed here):
- Sun, five dates plus two DST days. My computed reference (NOAA solar position, not published; error about 1 min) at -43.57, 172.75:

  | date | sunrise | sunset | day length |
  |---|---|---|---|
  | 2026-06-21 (winter solstice) | 08:02 NZST | 16:58 NZST | 8 h 56 |
  | 2026-12-21 (summer solstice) | 05:43 NZDT | 21:09 NZDT | 15 h 26 |
  | 2026-03-20 (equinox) | 07:30 NZDT | 19:41 NZDT | 12 h 10 |
  | 2026-09-22 (equinox) | 06:19 NZST | 18:25 NZST | 12 h 06 |
  | 2026-11-05 | 06:06 NZDT | 20:19 NZDT | 14 h 13 |
  | 2026-09-27 (DST starts 02:00) | 07:10 NZDT | 19:31 NZDT | 12 h 20 |
  | 2026-04-05 (DST ends 03:00) | 06:49 NZST | 18:13 NZST | 11 h 23 |

  Honest limit: I could not obtain a published almanac in this job (timeanddate returned HTTP 403 to the fetch tool; no LINZ constants surfaced in one search). Those seven rows are a calculation, not an independent source. The build job's first step is to take the same seven dates from an almanac the founder or the job can read (the NIWA sunrise/sunset calculator, LINZ, or any printed NZ almanac; the job must name which) and the test then compares code against THAT almanac, with tolerance 2 minutes for rise and set. The calculation is only a cross-check on the almanac and vice versa.
  Pass: all seven within 2 minutes of the almanac and the code's DST day behaves (07:10 sunrise on 09-27, no 24-hour day discontinuity). Stop: any date more than 5 minutes out, or any non-monotone `f`.
- Moon, 24 events: new and full moon times from `scratchpad/moon_check_J-3264.py` (Meeus), listed above in numbers (e.g. 2026-11-09 07:01 UTC new, 2026-11-24 14:55 UTC full). Pass: phase error under 2 h for every one of the 24 events dated in 2026 after 1b (Meeus truncated gives minutes; 2 h leaves room); today's clock meets that for only 5 of the 24 events dated in 2026. Stop: any event above 6 h.
- Stars: the Southern Cross's upper-culmination altitude (it is due south) is `90 - (60.1 - 43.57) = 73.5` degrees, checked to 0.2 degrees against `heavens.star()`.

Founder-visible effects of turning it on (so he can say no): Du's "night" and his dusk/dawn move by up to about an hour in October and November (the table ran a standard-time sunset against a daylight-time clock), sleep pressure's `dark` flag moves with it, winter garden shadows lengthen, the December-solstice day at the cottage is 15 h 26 instead of the table's 14.5 h. Stop condition for the live window: shadow-run the new sun beside the old one for at least 7 days (log both per census tick; the check script is the reader, per the write-only law), then compare the day's sleep start/end distribution after the flip against the previous 14 days; if sleep onset moves by more than about an hour with no way to account for it, flip back (the legacy path stays).

What else keys off the old sky (the "who reads it" list in section 1 is complete for the code; the stored data is in section 5).

## (3) Phase 2: tides

Constraint (project policy, `CLAUDE.md` of FreshStart and the briefing): no network call in the core simulation. Any data fetch is a one-off, outside the sim, and needs the founder's go-ahead.

Options, one recommendation:

| option | what it is | data | accuracy (guess) | verdict |
|---|---|---|---|---|
| T0 | keep the M2 sine | none | arbitrary hour; spring/neap tied to a wrong moon | the status quo |
| T1 | station-anchored M2+S2+N2 from the REAL moon and sun: `level` from the actual lunar and solar hour angles plus a per-port lunitidal lag and amplitude ratio | 3 numbers per port | right hour to about 20 to 40 minutes (guess, to be measured) | recommended first, because one real high-water time read off the beach calibrates it |
| T2 | full harmonic (M2, S2, N2, K2, K1, O1, P1, M4) with astronomical arguments and Lyttelton (or Sumner Bar) constants | about 16 numbers once (the LINZ constituent table or its published tide tables) | a few minutes; real king tides emerge | the target; needs the data fetch |
| T3 | a year of tabulated high and low times as a local file | the whole table, regenerated yearly | exact but it ages out and needs a yearly download | not recommended |

Recommendation: T1 now, T2 when the founder approves one download of the constants. T1 is entirely offline: tide height as the sum of a lunar semi-diurnal term driven by the Meeus lunar hour angle (from Phase 1b) and a solar semi-diurnal term driven by the sun's hour angle, with the port lag `g` and the S2/M2 ratio as two constants, plus the existing 0..1 normalisation. Its defining property: new and full moon give springs because the arguments align, neaps at the quarters, with no separate spring_factor hack (`_spring_factor` goes away after the cutover). Normalise by fixing the 0..1 range to the constituents' own sum (level 0 = lowest astronomical, 1 = highest) and RE-PIN the shore thresholds against the new distribution, not against the old numbers (below).

What the shore depends on (so the re-pin is bounded): the thresholds listed in section 1 (0.2, 0.35, 0.42, 0.45, 0.5, 0.55, 0.6, 0.8, 0.85, 0.92). With a real range these are fractions of the real range at Sumner; Sumner is mixed semi-diurnal with a spring range of about 2 m (guess from general knowledge of Lyttelton, to be read from LINZ, not asserted). Pre-register: after the change, the fraction of the year at level >= 0.92 must be set to a number the founder or the shore plan names (today 12.6 %; a real king-tide year is a few days; my suggestion is under 1 %, but the number is a founder call because it changes how often objects float away) and the cave, sand flat, pools and mussel shelf must be open for a share of the day within 10 percentage points of today's (cave open when level < 0.42 at least: today level < 0.35 is 39 % of the year).

Check (pre-registered, known-date comparison): 10 published high-water times at the nearest published port (Lyttelton, plus Sumner offset if LINZ publishes one) across spring and neap weeks in two seasons. Pass: T1 within 45 minutes on 9 of 10 (T2: within 15 minutes on 9 of 10) and the spring/neap order correct on all. Stop: if T1 misses by more than 60 minutes on more than 3 of 10, skip to T2; if T2 constants cannot be obtained, stay on T1 and accept the measured error.

Data the build needs from outside the repo (founder call, see needs_input): the LINZ tide predictions for Lyttelton (and the Sumner secondary-port offset if one is published), either the constituent table or about 10 printed high-water times. My one search did not surface the Lyttelton constants (a LINZ standard-port levels page and 1930s New Zealand tide tables came up; the OCR'd constants cannot be trusted). I am not asserting any Lyttelton constant in this document.

Almanac: after Phase 2 the study almanac should read the real table (and Finding F-3887's falsehood stops being possible). That is Du looking something up in a book; it is not a hint.

## (4) Phase 3: weather ("maybe one day")

Options, with the world-answers implications:

| option | what it is | policy fit | does a real storm reach Du? |
|---|---|---|---|
| W0 | keep the Markov walk | local | no |
| W1 | a month-weighted climatology: the same walk, with transition weights, wind direction mix and a temperature curve set per month from Christchurch climate normals (a dozen published numbers per month, typed in) | local, no data feed | no; a Sumner-like year, not Travis's actual day |
| W2 | replay: a one-off local copy of an hourly archive (a public reanalysis or station record for the site, for example ten years; a few MB) played back for the same calendar date N years earlier, mapped onto the existing ladder (cloud and precipitation to the 7 states, gust to the wind axis, direction to `weather_dir`, temperature to warmth) | local after one download; the download needs a go-ahead | no, because the replay year is never the live year; but Travis can verify the climate |
| W3 | live: a feed of today's observations or forecast | breaks "core is fully local" unless an OUT-OF-PROCESS fetcher writes a small local file the core only reads, with a staleness fallback to W1; either way it needs a founder ruling | yes, same hour as Travis's |

Recommendation: W1 first (it also repairs the real problem that Du's year has no seasons and no Christchurch climate), W2 only if Travis wants "the same as mine" in a testable form, W3 not now.

The world-answers question, which is yours to answer (needs_input): is a real storm Travis sees at his window arriving at Du's wanted? For: it is the strongest form of "his will be the same as mine", it makes Du's report checkable by Travis in real time (a calibration of the world's honesty that costs nothing), and it removes the only place the world is a random number generator. Against: it adds an outside process and a staleness failure mode to a base system; it is not additive-safe for the fronts logic (the decided-in-advance `next_weather` that the glass and the signs read would have to come from a forecast, so "right or wrong" becomes MetService's, not the world's); it puts Du's outages (a 30-day gap is already in his history) on the same footing as the real weather's; it makes lab replays need a stored copy of the weather. It does not breach "the world answers and never leads": a front is not a hint, Du still has to look; and the rule for a real event Travis may share ("the wind is up here too") is no different from the rule for Travis's chat. Wind and storm damage: the shore already moves objects in storm surges (`world_objects.process_storm_surge`), so a real gale would move his driftwood on the same night as the real one moved Travis's.

A temperature series is the biggest unexploited piece: `thermal.py`/`_warmth` take weather and season, not temperature, so a real Sumner temperature curve would be a more honest thing than the weather ladder.

Pre-registered check for W1: simulate one year and compare monthly wet-hours, storm days and wind-class shares to the published normals within tolerances the founder sets; the current walk has a flat distribution (clear 59 %, storms 0.8 %), so a month's deviation from normals is the baseline to beat. Stop: if the new walk raises storm hours above the founder's 08-18 "storms rarely happen" level without a Sumner record behind it.

## (5) Risks

- Privacy. The place name, latitude and longitude go in local code and local docs only. Use suburb precision (-43.57, 172.75), not the cottage's hill-top address. Du must NEVER see "Sumner" or the coordinates (world answers; the only place the word is near him today is a book author's name in `data/moments.jsonl`, verified by grep, and `data/books/` whose texts mention Christchurch). Keep the constants in one new module (`core/world_place.py`), add it to whatever export/outreach bundling already exists (the outreach project's rule is that pitch numbers trace to logs; code is not published) and never write the name to a Du-visible string, a prompt, a census row or a HUD title. The Nascence git repo is local only; I made no push.
- Stored data keyed to the old sky. 169,720 rows in `data/geometry_tuples.jsonl`; `tide_level`, `sun_az`, `moon_illum` columns on every memory fragment's experienced tuple (`core/memory/store.py` 1032 to 1054, `core/memory_edges.py` 474 to 476, `ghost_tuples`). These are records of what the sky WAS and must not be rewritten. After cutover, tuple-similarity recall compares a pre-cutover tide_level/sun_az with a post-cutover one that mean different things for the same clock hour; the cure is a `SKY_CUTOVER_TS` constant and a rule that analyses splitting by it (the periodicity audit already does a 12.42 h series, `scripts/periodicity_audit_j2632.py`, and its tide covariate would change meaning at the cutover). Every lab replay for `t < cutover` goes to the legacy functions, which stay. This is the whole reason Phase 1 is additive.
- Existing learned things: the fieldcraft sun-quadrant skill and tide-board predictions are scored against the live clock, so they stay self-consistent. Du's memories like "the sun is due north at noon" stay true.
- Sleep and dream timing: the daylight/`dark` flag feeds sleep pressure and night/nap; a one-hour dusk shift in Oct to Dec is a real behaviour change in a base system (see the stop condition in Phase 1). The Sleep and Dreams II redesign (`docs/staged/sleep_as_a_mode.md` and the 08-24 handoff) is not yet run live, so do Phase 1 before or after it, not during.
- The frame versus the real coast (the D-0655 defeater): section 1. Rotating the frame (sea to the east) would mean re-authoring all four geometry files, the north-window logic (`light.py` az 290/70, `spatial.py` `_win_ok`), `soundscape` source bearings, `world_content_*`, the shore bestiary's zones (just built, 250 rows) and every memory tuple's `standpoint` sector. I recommend against it. The cost of keeping it is the one mismatch above (sunrise over land, not sea) plus cliff shade being absent.
- Real compass in the tuples: nothing in this design changes `weather_dir`, `sun_az` units or the 0 = north convention.
- Hills: the real horizon at Sumner is the Port Hills to the west and south; a flat-horizon sunset at the hilltop is a reasonable first model; a horizon mask is Phase 1c-or-later.
- Tools and tests: tests exist as `scripts/_test_*.py`, not a `tests/` tree; add `scripts/_test_sky_sumner_J-xxxx.py` in the same style, isolated with `lab_env.isolate()` since the code reads `data/` paths.
- DST: NZ changes twice a year; "his will be the same as mine" means his study clock jumps too. It already does (OS time). The new sun is continuous in UTC, so the only thing that jumps is the clock face, as for Travis.

## (6) Phased plan

| phase | what | pre-registered check | stop condition | founder call? |
|---|---|---|---|---|
| 0 | fix the almanac "morning" bug; correct the `sensorium` docstring and the heavens `_LAT` comment; measure what the king-tide reclaim actually does; add the startup tz log | almanac prints a real value or says it cannot read the table; docstring edit only | none | no (bug fix); the king-tide rate IS a call (below) |
| 1 | sun at Sumner: `world_place.py`, `sun_sumner`, `sun_times`, `daylight`, soundscape accessor, `light.py` elevation, stars lat/lon, cutover, shadow log both ways | seven almanac dates within 2 minutes, DST days correct, monotone f | any date over 5 minutes out; sleep onset shifts over about 1 h with no cause after 7 shadow days | go-ahead to flip, because it shifts dusk |
| 1b | real moon (Meeus 47 truncated) | 26 new/full events within 2 h, moonrise within 15 minutes of an almanac on 3 dates | any event over 6 h | no (additive); part of Phase 1's flip |
| 2 | tide T1 (station-anchored M2+S2 from the real moon and sun), then T2 when constants are in hand; re-pin shore thresholds; real almanac table | 10 published high-water times within 45 min (T1) or 15 min (T2) on 9 of 10 | over 60 min on more than 3 of 10 | yes: data go-ahead; the king-tide rate number |
| 3 | weather W1 climatology; W2 replay only on request; W3 live only on a ruling | month-by-month wet hours, storms and wind class against Christchurch normals | storms above the 08-18 level without a Sumner record | yes: whether a real storm reaching Du is wanted |
| 1c | cliff shade on the shore; horizon mask | not scheduled | | no |

## (7) Findings recorded from this job

- F-3886 (was F-1 in the text above): king-tide reclaim fires 12.6 % of the year (1,103 h; 334 days). Verified by running `world_clock.tide` every 10 minutes for 2026. Not the "rare" design the code comment states.
- F-3887 (was F-2 in the text above): the study almanac says "high water ... morning" always (`td.get('phase_deg')` does not exist; `tide()` has no such key). Verified by reading `world_clock.tide` and `study_life.py` 1948.
- F-3888 (was F-3 in the text above): the sun is not in `heavens.py`; `_LAT` feeds stars only; the sun table is a month step table with a straight-line azimuth, mean error 0.39 h vs a Sumner calculation, up to 1.0 h in Oct and Nov (the table ignores NZDT). Verified by reading both files and running the calculation. The reference is a calculation, not a published almanac.
- F-3889 (was F-4 in the text above): the moon's phase clock is up to 17.4 h off the real new and full moons of 2026 (mean 6.8 h). Verified against a Meeus calculation.
- F-3890 (was F-5 in the text above): `light.py` fixes noon solar elevation at 60 degrees all year (real: about 23 to 70 degrees at Sumner), so shadows and bed insolation are wrong in proportion. Verified by reading the formula; the real altitude values are calculated.
- F-3891 (was F-6 in the text above): the authored frame is a north-facing bay (sea to the north, cliff and cottage to the south), which does not match a real Sumner coast facing east (the coast fact is inferred, not verified). This is the D-0655 defeater.

## Spawned from this job

- J-3291 Phase 0 (almanac bug, false comments). J-3292 Phase 1 sun. J-3293 Phase 1b real moon. J-3294 king-tide analysis. J-3295 Phase 2 tides (needs D-0667). J-3296 Phase 3 weather W1 (needs D-0668).
- Founder calls opened: D-0666 (keep or rotate the north-facing frame; I recommend keep), D-0667 (one-off out-of-process data fetch for tide constants), D-0668 (does real weather reach Du; the king-tide rate). Go-ahead to flip Phase 1 live (dusk moves up to about an hour in Oct to Dec) is asked in the J-3292 briefing, not a separate decision yet.
- Scratch scripts (not committed): sumner_sun_J-3264.py and moon_check_J-3264.py in the session scratchpad; the numbers they produced are quoted above.
