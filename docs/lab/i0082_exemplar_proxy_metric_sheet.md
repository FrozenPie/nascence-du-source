# I-0082 exemplar-memory offline PROXY — metric sheet (written BEFORE computing)

**Job:** J-1471 · **Plan:** strings_and_sheets · **Idea:** I-0082 · **Date:** 2026-09-28
**Status:** pre-registration. Nothing below has been run yet as this file is written. The script
(`scripts/j1471_i0082_exemplar_proxy_read.py`) must implement exactly this and nothing else; any
deviation discovered while coding gets fixed here first, not silently in the script.

## 0. What this is and is not

World sounds have no measured strings yet (strings_and_sheets Object A, Phase 4, unbuilt — only
`Heavyweight.mp3` has ever been measured, and that is music, not a world sound). So this is a
**PROXY**: a per-hearing point built from (a) the sound key's fixed, hand-seeded six-axis coordinate
in `core/soundscape.py`'s `_SOUNDS` (identical for every hearing of the same key — see §2) plus
(b) three context axes that genuinely vary hearing to hearing and are already recorded in the real
census log. This measures **how much the surrounding CONTEXT differs**, not how the sound itself
sounded — that distinction is the whole reason the confidence on this job's finding is split (counts
verified, anything about acoustic *shape* stays inferred, per the job briefing).

## 1. Data

- **Primary:** `C:\Nascence\data\geometry_tuples.jsonl` — the P0 mapping-census log
  (`core/geometry_census.py:snapshot()`), one row per cognitive event (idle thought or hot cycle).
  Read in full, in ts order, exactly as it stands at run time (95,091 lines confirmed by `wc -l`
  2026-09-28 00:44 — up from the briefing's own 92,980 as of 2026-09-27, since this is a live,
  still-growing append log; the read processes whatever is on disk at run time, once, start to end —
  no tailing, no sampling).
- **Row shape actually used** (confirmed by reading `core/geometry_census.py:250-296` and one live
  sample row): `ts` (float, `round(time.time(), 1)` — real wall-clock Unix time, not a separate
  simulated clock; every day/night/season function elsewhere in `core/soundscape.py` also reads
  `time.localtime()` directly, so this analysis's local-time interpretation of `ts` is the same one
  the live system itself uses), `place`, `weather`, `weather_dir` (present on ~87% of a 5,000-row
  sample checked 2026-09-28), `sounds` (list of active keys — this is the field a "hearing" is read
  from).
- **Secondary (cross-check only, not part of the metric):** `data/sound_knowledge.json`'s `hearings`
  block. This counts a *different* thing (world_tick's own Poisson-rate event/bed-hour accounting,
  not census-row co-occurrence) and is used only as an independent plausibility check on the raw
  counts this script produces, never as an input to the exemplar algorithm itself.
- **A "hearing"** = one census row whose `sounds` list contains the target key. **Pre-registered
  caveat, not a post-hoc excuse:** verified by reading `core/soundscape.py`'s `_PROPAGATION_TABLE`
  (`_sec_shore`, `_sec_garden`, `_sec_study_main`, `_sec_morepork`) that all four target keys enter
  `active_sounds()` via **ambient condition gates** (daylight, location, dryness, or — for
  `cat_purr` — the cat's own mood/activity state), not per-discrete-call Poisson arrivals; the
  Poisson rate in `_EVENT_RATES` only feeds `world_tick`'s separate hearing-ledger accounting, never
  `active_sounds()` itself. So a run of consecutive census rows at the same ambient condition is a
  run of consecutive "hearings" of the same standing condition, not independent call events. This
  matters most for `cat_purr`, which is registered in `_BEDS` (continuous-presence class) — expect
  its raw hearing count to track *time spent purring, sampled at census cadence*, not discrete purrs.

## 2. The fixed six-axis point (reference only — NOT part of the distance calculation)

Verbatim from `core/soundscape.py` `_SOUNDS` (axes: brightness, energy, onset, periodicity,
roughness, continuity — all 0..1):

| key | brightness | energy | onset | periodicity | roughness | continuity |
|---|---|---|---|---|---|---|
| morepork_call | .45 | .35 | .30 | .65 | .10 | .15 |
| tui_song | .75 | .50 | .60 | .35 | .45 | .30 |
| gull_cries | .70 | .65 | .70 | .25 | .85 | .15 |
| cat_purr | .08 | .20 | .05 | .95 | .30 | .90 |

**Decision (pre-registered): this six-axis point is excluded from the distance formula.** Reason:
the exemplar sets are built and evaluated *per key* (never mixing keys), and this point is identical
for every hearing of a given key — its pairwise contribution to any intra-key distance is
mathematically always zero. Folding six always-tied axes into a shared normalisation denominator
would only dilute the context signal (make every distance smaller for no informational reason). It
is reported here for reference/documentation, not fed to the script's distance function.

## 3. Context axes (these ARE the distance)

1. **Time-of-day phase**, `phase = (hour*3600 + minute*60 + second) / 86400` from `ts`, local time.
   Circular: `d_tod(a,b) = 2 * min(|a-b|, 1-|a-b|)` → range [0,1] (the ×2 rescales the circle's max
   half-period, 0.5, back up to 1.0 so it sits on the same scale as the other axes).
2. **Weather severity**, via `core/soundscape.py:_weather_severity()` — reimplemented verbatim in the
   script (no `core/` import; see §5 isolation note) from the confirmed source
   (`core/sensorium.py:40`): `_WEATHERS = ["clear","high cloud","overcast","drizzle","steady rain",
   "wind and rain","thunderstorm"]`, severity = `_WEATHERS.index(weather)`, fail-open to `0` if the
   weather string is not on that ladder (confirmed live case: `"snow"` appears in the real data and
   is NOT on this ladder — it will read as severity 0, same as `"clear"`; this is the named function's
   own real behaviour, inherited deliberately, not a bug this job fixes). `d_sev(a,b) = |sev_a -
   sev_b| / 6` (6 = top index, "thunderstorm").
3. **Place**, from the row's `place` field. `d_place(a,b) = 0` if equal, else `1`.
   **Pre-registered structural fact, verified by reading `_PROPAGATION_TABLE` before running anything:**
   `tui_song` only ever fires from `_sec_garden` (place≡"garden"), `gull_cries` only from `_sec_shore`
   (place≡"shore"), `cat_purr` only from `_sec_study_main` (place≡"study") — so for **three of the
   four target keys, `d_place` is identically 0 for every pair, by construction**, before a single
   row is read. Only `morepork_call` (`_sec_morepork`, gated on `loc in {garden, study, wood}`) can
   ever show a non-zero place term. The script must confirm this (report the observed place-set per
   key) rather than assume it — it is a prediction from the source read, not yet a measurement.
4. **Direction** (the job's "any direction" hedge) — `weather_dir` is the only directional field the
   census carries: the *weather front's* bearing in degrees (`core/sensorium.py:262-264`; NZ-weighted
   compass sectors), **not** a per-sound source bearing (Nascence sounds carry no bearing of their
   own yet — confirmed, this is exactly D-0304's scoped-for-later microphone work). **Usability rule,
   decided now, applied mechanically by the script, not judged after seeing results:** include
   `weather_dir` as a 4th context axis only if it is non-null on ≥90% of the combined hearings of all
   four target keys; otherwise drop it for all four (one decision, not per-key, so T stays comparable
   across keys). If included: `d_dir(a,b) = min(|a-b|, 360-|a-b|) / 180` (circular degrees → [0,1]).

**Distance:** `D(i,j) = sqrt(mean(d_tod², d_sev², d_place² [, d_dir²]))` — RMS over whichever context
axes are in play (3 or 4, per the rule above), each already in [0,1], so `D ∈ [0,1]` always. `T ∈
{0.1, 0.2, 0.3}` is then read directly as "how many tenths of the maximum possible normalised context
difference."

## 4. The exemplar algorithm (k=4, per key, independently for T ∈ {0.1, 0.2, 0.3})

Walk that key's hearings in `ts` order.
1. First hearing: unconditional seed (no exemplar yet exists to be "nearest"). Counts as 1 admission,
   flagged separately in the output as the seed, not compared against T.
2. Every later hearing: compute `d* = min` distance to every exemplar currently in the set.
   - If `d* > T`: **admit**. If the set has fewer than k=4 members, append it. If the set is already
     full (k=4), first find the "least-distinct" current exemplar — the one with the smallest
     nearest-*other*-exemplar distance within the current set (ties broken by removing the oldest) —
     and replace it with the new hearing's point.
   - Else: discard (the exemplar set is unchanged; this hearing does not count as an admission).
3. Report, per key per T: total admissions (with the seed called out separately), admissions per
   1,000 hearings (`admissions / n_hearings * 1000`), and the raw hearing count itself.

## 5. Pre-registered secondary reads

- **Dawn/dusk clustering.** Fixed clock-hour buckets (a deliberately simple, season-independent
  binning for this descriptive pass — NOT `soundscape._is_dawn()`'s own season-conditioned window,
  which is a gating law for a different purpose): dawn `[5,8)`, day `[8,17)`, dusk `[17,20)`, night
  otherwise. Report, per key per T: the fraction of ALL hearings in each bucket (base rate) vs. the
  fraction of ADMISSIONS in each bucket, as a ratio (>1 = admissions cluster there more than base
  rate).
- **Weather-change clustering.** For each admission (excluding the seed), check whether the
  immediately-*preceding* hearing of the same key (in its own ts-ordered stream) had a different
  `weather` string. Compare that fraction against the base rate (the same check run over every
  consecutive hearing pair of that key, admitted or not). Ratio >1 = admissions cluster at weather
  transitions more than chance.
- **Raw-count comparison.** `admissions / n_hearings` at each T, i.e. what share of real hearings this
  rule would actually keep — the job's central question.
- **Reliability floor:** if a key's `n_hearings < 50`, its per-1,000 rate is flagged unstable in the
  write-up rather than read as a real rate.

## 6. Isolation note (job's `isolation: required`)

The script imports **no `core/` module** and touches **no live state file** — it opens
`data/geometry_tuples.jsonl` (and, for one cross-check table, `data/sound_knowledge.json`) read-only
via plain `pathlib`/`json`, and every constant normally read from `core/soundscape.py` /
`core/sensorium.py` is instead copied verbatim from the source lines cited above. Nothing
live-adjacent is touched at all, so `lab_env.isolate()` (built for code that calls into
`core.memory.store`/`store_fragment` or reads/writes live state) is not applicable here — there is
nothing for it to isolate. All outputs are new files under this worktree's own `docs/lab/` and
`scripts/`; nothing under `C:\Nascence` is written directly by this job.

## 7. What would make this proxy's shape-claims wrong (kept honest, per job instruction)

Every number this produces is about **when the ambient gate opens/closes and how varied the census's
own snapshots of that gate are** — never about how the sound itself actually sounded on two
occasions, because the six-axis point is fixed per key (§2) and no real audio exists for any world
sound. A future real read (post Phase 4, measured strings) could show these keys cluster completely
differently once actual acoustic variation is on the table. That is exactly why the finding this job
files records counts as verified and says nothing stronger than "inferred" about what this implies
for exemplar-store *design*.
