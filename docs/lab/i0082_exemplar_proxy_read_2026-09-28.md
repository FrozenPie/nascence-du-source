# I-0082 exemplar-memory offline PROXY read — results (2026-09-28)

**Job:** J-1471 · **Plan:** strings_and_sheets · **Idea:** I-0082 · **Method:** pre-registered in
`docs/lab/i0082_exemplar_proxy_metric_sheet.md` (written first; nothing below changed that method
after seeing numbers). **Script:** `scripts/j1471_i0082_exemplar_proxy_read.py`. **Raw output:**
`docs/lab/i0082_exemplar_proxy_results_2026-09-28.json`.

## Confidence

**Counts (this section, §1-§3) are VERIFIED** — one full, unsampled pass over the live
`data/geometry_tuples.jsonl` (95,093 rows, all parsed, 0 malformed), computed by a script that
imports no `core/` module and touches no live state (see metric sheet §6). Anything about what this
implies for real acoustic *shape* (§5) stays **INFERRED**: the six-axis point behind every hearing is
each key's fixed, hand-seeded coordinate (constant per key — see metric sheet §2), never a measured
wave; no world sound has one of those yet.

## 1. Headline: what the rule would keep

| key | n hearings | admissions/1,000 @ T=0.1 | @ T=0.2 | @ T=0.3 | final exemplar count (all T) |
|---|---:|---:|---:|---:|---:|
| morepork_call | 20,222 | 31.75 | 23.98 | 18.89 | 4 |
| tui_song | 7,746 | 19.62 | 15.75 | 11.10 | 4 |
| gull_cries | 26,240 | 22.07 | 17.64 | 14.71 | 4 |
| cat_purr | 3,632 | 107.93 | 93.34 | 85.35 | 4 |

The exemplar set fills its full k=4 budget for all four keys at all three thresholds — the rule never
settles for fewer than the cap. So "how many exemplars would it keep" has two honest answers: the
**size** is always 4 (the cap binds), and the number that matters more is the **churn** — how often a
hearing is different enough to bump one out. At T=0.2, that is roughly one admission per 42-64
hearings for the three bird/owl calls, and one per ~11 hearings for `cat_purr`.

## 2. `cat_purr` churns 3-8x faster than the other three — mostly an early-history transient, not a live rate

**Exploratory, not pre-registered** (added after seeing §1's numbers, to check whether raw
whole-history rates are comparable across keys with very different total counts): splitting each
key's hearing stream at its midpoint and re-running the T=0.2 rule on each half separately —

| key | first-half admissions/1,000 | second-half admissions/1,000 | ratio |
|---|---:|---:|---:|
| morepork_call | 58.35 | 34.62 | 1.7x |
| tui_song | 24.53 | 5.68 | 4.3x |
| gull_cries | 32.39 | 3.73 | 8.7x |
| cat_purr | 180.62 | 13.21 | 13.7x |

All four settle — the back half of every key's history churns less than the front half — which is
what you would want an exemplar store to do (learn the shape of the context space, then stop
replacing once it is covered). `cat_purr` settles hardest (13.7x) and `morepork_call` least (1.7x).
That pairs with §3 below: `morepork_call` is the *only* one of the four whose `place` context axis
ever varies, so it is the only key whose context space is not already saturated after a few weeks —
it keeps meeting genuinely new (place × time × weather) combinations longer than the other three.
The whole-history figures in §1 are real counts, but reading them as one flat "rate" per key
overstates steady-state churn, most for `cat_purr`.

## 3. Structural finding, verified before running anything and confirmed by the run: 3 of 4 keys have a locked `place` axis

Predicted in the metric sheet (§3.3) from reading `core/soundscape.py`'s `_PROPAGATION_TABLE` alone,
then confirmed by the actual data:

| key | places observed |
|---|---|
| tui_song | `{garden}` only |
| gull_cries | `{shore}` only |
| cat_purr | `{study}` (+ a Day-1 anomaly, see §4) |
| morepork_call | `{garden, study, wood}` — the only one that varies |

So for three of the four target keys, every admission this whole job measured came entirely from
**time-of-day phase, weather severity, and (for `morepork_call` also) place** — never from acoustic
shape, which does not exist yet for any of them. That is the proxy's real ceiling: it is measuring
how varied the *ambient conditions under which a sound is audible* are, not how varied the *sound*
is — consistent with all four keys entering `active_sounds()` through condition gates
(`_sec_garden`/`_sec_shore`/`_sec_study_main`/`_sec_morepork`), never per-discrete-call.

## 4. Caveat found in passing, verified: `cat_purr`'s 6.6% place anomaly is Day-1 data, not a live bug

241 of `cat_purr`'s 3,632 hearings (6.6%) show `place` = `garden` (76) or `shore` (165) — impossible
under the CURRENT source, which only ever adds `cat_purr` to `active_sounds()` from `_sec_study_main`
(place=="study" required by its own `_PROPAGATION_TABLE` row), and confirmed `cat_purr` is not one of
`core/cat_sounds.py`'s 8 `KEYS` (the location-independent "her voice" pool) either — checked directly,
not assumed from the module's own comment.

**All 241, without exception, are dated 2026-07-05** — the exact day `core/geometry_census.py`'s own
docstring names as its P0 launch date, and the very first ~250 rows of the entire 95,093-row log (the
file's first row is `ts=1783171482.0`, itself 2026-07-05; the anomalies start 244 seconds later). Every
one of the 241 rows also has `at_study`/`at_garden`/`at_shore`/`standpoint`/`in_transit` all `null` —
fields `core/soundscape.py`'s own comments date to 2026-08-15 ("LOCOMOTION... standpoint + transit
flag") and later than 2026-07-05 (the wood location itself is dated "authored 07-08" in the same
file). Verified conclusion: this is Day-1 census output from before the current place-gating source
existed, not a live race condition or an ongoing (place, sounds) consistency bug. Effect on §1/§2 is
almost certainly small (241 of 3,632 total, concentrated at the very start of `cat_purr`'s history)
but not separately re-quantified here — flagged as inferred, and as the follow-up job below.

## 5. What this does and does not say about I-0082's design (inferred)

- The rule's **long-run** churn (§2's second-half column: 3.7-34.6 admissions per 1,000 hearings once
  settled) is modest — roughly one exemplar swap per 30-270 real hearings depending on the key. A
  k=4 store built this way would not be constantly chattering once past its own early history.
- But three of the four keys can *only* ever admit on time-of-day/weather grounds (§3) — with real
  measured strings (Phase 4, unbuilt), the same keys might admit far more, or far less, once actual
  acoustic variation enters the picture. Nothing here bounds that.
- The choice of T matters less than which half of history you are in (§2) — T=0.1 vs T=0.3 changes
  the whole-history rate by roughly 1.4-1.8x per key, but settling changes it by 1.7-13.7x. A future
  real design should pre-register against steady-state behaviour, not whole-history averages.

## 6. Re-quote with census stamp rows stripped (J-3959, 2026-11-14)

**Why:** every idle cycle wrote two rows (a census stamp 0.1-0.3 s before the idle row, F-4078/F-4595), so §1-§4's
"hearings" counted each cycle twice. J-3944 added `scripts/stamp_row_filter.py` (`drop_stamp_rows`) to the reader; this
section reruns the identical, unchanged method on today's `data/geometry_tuples.jsonl` (190,469 parsed rows; 136,968 kept
after the filter, 53,501 = 28.1% dropped). Raw outputs: `docs/lab/i0082_exemplar_proxy_results_stampstripped_2026-11-14.json`
(filtered). The 09-28 numbers above are NOT edited: they were measured on a file half this size, so old-vs-stripped alone
conflates two changes. Three columns separate them: **09-28** (95,093 rows, stamps in), **today as-is** (same file as the
stripped run, filter bypassed), **today stripped**.

**Confidence: VERIFIED** (full unsampled passes, scripts read-only, no hub touched). The as-is and stripped runs are the same
code on the same file, so the only difference between those two columns is the filter.

Admissions per 1,000 hearings at T=0.2 (admission counts are identical as-is vs stripped, a stamp never admits an exemplar;
only the hearing denominator changes):

| key | hearings 09-28 | hearings as-is | hearings stripped | per-1k 09-28 | per-1k as-is | per-1k stripped |
|---|---:|---:|---:|---:|---:|---:|
| morepork_call | 20,222 | 46,945 | 34,417 | 23.98 | 14.74 | 20.11 |
| tui_song | 7,746 | 25,020 | 15,838 | 15.75 | 7.39 | 11.68 |
| gull_cries | 26,240 | 42,433 | 29,223 | 17.64 | 12.30 | 17.86 |
| cat_purr | 3,632 | 11,072 | 8,990 | 93.34 | 36.04 | 44.38 |

Same, T=0.1 / T=0.3 (as-is -> stripped): morepork 19.92->27.17 / 10.61->14.47; tui 10.63->16.80 / 4.40->6.95;
gull 16.05->23.30 / 9.64->14.00; cat_purr 43.80->53.95 / 30.17->37.15. Final exemplar count is 4 for every key and
threshold in all three runs (unchanged).

Weather-change lift at T=0.2 (as-is -> stripped): morepork 43.0->31.5, tui 84.0->53.2, gull 43.4->29.9, cat_purr 17.9->14.5.
The lift shrinks by roughly 15-37% when stamps go (the reason is INFERRED, not tested: stamps share their idle twin's
weather tick, so they shift the base rate's denominator and numerator unevenly); direction (admissions concentrate on weather changes, lift >> 1) is unchanged for all keys.
Place sets observed are identical.

What changed in the story of §1-§2:
- **Stripping raises every churn rate 1.2-1.6x relative to as-is** (hearing denominator was 1.36x, 1.58x, 1.45x, 1.23x too
  big for morepork, tui, gull, cat_purr). Quote the stripped column from now on; the 09-28 §1 figures were also stamp-inflated
  in the denominator (stamp writes predate the J-3455 marker), so they understated churn by a similar factor (INFERRED: the
  09-28 file was not re-filtered, only today's).
- **The §2 headline survives but the ratio narrows.** At T=0.2, cat_purr vs the other three: 93.34 vs 15.75-23.98 on 09-28
  (3.9-5.9x) -> 44.38 vs 11.68-20.11 stripped (2.2-3.8x). It is still the fastest churner, but "3-8x" overstated it; the
  honest figure on today's file is about 2-4x. Much of the 09-28 gap was the small-sample early-history transient §2 already
  flagged (cat_purr had only 3,632 hearings then).
- The §2 first-half/second-half table is NOT re-quoted here (the script does not emit it; it was an exploratory side
  computation not in the script).

### Companion re-quotes (rolling_intrinsic_dimension, eigenform_variety_read)
- `rolling_intrinsic_dimension.py` (today's file): as-is 190,476 rows / 760 windows, consensus mean **1.656**, drift -0.005,
  last window 1.430; stripped 136,968 rows / 546 windows, mean **1.668**, drift -0.020, last 1.576. Stable either way. This
  differs from the J-3753 doc's section 4 expectation (stripped 1.673 vs copied-unresolved arm 1.436): that comparison was
  against the "copy the twin's `unresolved` into the stamp" arm, not as-is, and J-3753's as-is mean was 1.659. Stripping
  moves the headline dimension by about +0.01; the 1.436 value belongs to the hypothetical repair arm only.
- `eigenform_variety_read.py` (--out scratch only): verdict MIXED both as-is and stripped. One cell flips: E_1009 requisite
  variety R `recovers` is **true as-is, false stripped** (R after/base 35.8/39.5 as-is vs 36.6/41.8 stripped); E_1009 drop
  and E_0928 outcomes unchanged. Treat the E_1009 R recovery as filter-sensitive, i.e. not robust.
