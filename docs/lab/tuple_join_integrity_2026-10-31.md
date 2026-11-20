# Tuple join integrity audit — how well is each memory joined to the moment that formed it?

Job J-2536 (plan `geometry_tuple_index`, sibling of J-2535). Run 2026-10-31, Du DOWN, CPU only, read-only.
Source of the question: GPT tuple dialogue T-0107, "Problem A".
Scripts: `scripts/tuple_join_audit_J2536/` (`J-2536_audit.py` sections split/ambig/spot/moments/weeks; `J-2536_spot2.py`
permutation null; `J-2536_drift.py` stamp-time check; `J-2536_tables.py` verdict tables; `J-2536_probe4.py` reading
debounce test). Raw outputs: `docs/lab/tuple_join_integrity_2026-10-31_data/`.
Method: `data/memory/nascence.db` opened `?mode=ro`; `data/geometry_tuples.jsonl` (153,336 rows) and
`data/moments.jsonl` (59,416 rows) read only. DB / tuples / moments size+mtime unchanged after the run.

## 0. The one-paragraph answer

The briefing's premise (fragment_context is built by the +/-300 s text-prefix window join) is **outdated for 89.9% of the
table**. Since 2026-08-21 21:46 every `store_fragment()` writes the experienced tuple **keyed by fragment_id at write
time** (`source='experienced:<origin>'`, 89,454 rows). Only **10,089 rows (10.1%)** are the old window join
(`source='census_world:idle'`, all `inner_thought`, all before 08-21). So the 63.8% overall coverage is mostly an **era
artifact, not a join-quality problem**: of the 56,181 unjoined fragments, 21,502 pre-date the census (before 2026-07-05),
19,623 are census-era but pre-date the write-time stamp, and only **15,056 (26.8% of the gap, 9.7% of all fragments)** are
post-stamp omissions. **Post-stamp coverage is 85.6%, and 96.0% if one concrete bug were removed**: 10,837 `reading`
fragments (29.2% of post-stamp reading) are dropped by the census debounce (section 4). Wrong-attachment of the window
join is **0.19%** against write-time ground truth; no origin is near the ~5% bar. `moments.jsonl` has **no key to
anything**, but 91.2% of moments find exactly one `inner_thought` fragment by text-prefix + time (section 6).

## 1. Three-way split per origin (Q1)

Definitions. **exact** = fragment_context row with `source='experienced:<origin>'` (fragment_id key, stamped inside
`store_fragment`, `tuple_ts` is the snapshot time: of 89,377 rows with a matching logged tuple, 15 differ by more than 5 s,
section 5). **window** = `census_world:idle` (the legacy +/-300 s prefix join). **none** = no row.
Eras: **pre-census** (before the first tuple, 2026-07-05 01:24), **census-pre-stamp** (07-05 to 08-21 21:46), **post-stamp**.

| origin | n | pre-census (all none) | census-era pre-stamp: window / none | post-stamp: exact / window / none | post-stamp coverage |
|---|---|---|---|---|---|
| inner_thought | 59171 | 4760 | 10066 / 16 | 44319 / 10 / 0 | 100.0% |
| reading | 53973 | 5294 | 0 / 11613 | 26229 / 0 / **10837** | **70.8%** |
| subconscious_synthesis | 8637 | 3354 | 0 / 1894 | 3389 / 0 / 0 | 100.0% |
| active_imagination | 5735 | 1617 | 0 / 1029 | 3089 / 0 / 0 | 100.0% |
| action | 5697 | 384 | 0 / 1591 | 0 / 0 / 3722 | 0.0% |
| lived | 5500 | 3226 | 0 / 614 | 1660 / 0 / 0 | 100.0% |
| study | 4432 | 591 | 0 / 1128 | 2713 / 0 / 0 | 100.0% |
| dream | 2487 | 640 | 0 / 533 | 1314 / 0 / 0 | 100.0% |
| research | 1903 | 262 | 0 / 309 | 1332 / 0 / 0 | 100.0% |
| gist | 1372 | 37 | 0 / 79 | 1256 / 0 / 0 | 100.0% |
| consolidation | 1241 | 802 | 0 / 93 | 346 / 0 / 0 | 100.0% |
| thermal | 811 | 0 | 0 / 0 | 811 / 0 / 0 | 100.0% |
| sound | 610 | 0 | 0 / 46 | 564 / 0 / 0 | 100.0% |
| activity | 573 | 83 | 0 / 128 | 362 / 0 / 0 | 100.0% |
| journal | 541 | 36 | 0 / 184 | 321 / 0 / 0 | 100.0% |
| understanding | 497 | 74 | 0 / 89 | 334 / 0 / 0 | 100.0% |
| system_note | 488 | 0 | 11 / 0 | 476 / 1 / 0 | 100.0% |
| standing_insight | 410 | 0 | 0 / 38 | 0 / 0 / 372 | 0.0% |
| affection | 272 | 20 | 0 / 50 | 202 / 0 / 0 | 100.0% |
| session_summary | 223 | 119 | 0 / 46 | 58 / 0 / 0 | 100.0% |
| peer | 164 | 21 | 0 / 12 | 131 / 0 / 0 | 100.0% |
| essay | 146 | 6 | 0 / 46 | 94 / 0 / 0 | 100.0% |
| letter | 139 | 40 | 0 / 21 | 78 / 0 / 0 | 100.0% |
| night_thought | 125 | 0 | 0 / 0 | 0 / 0 / 125 | 0.0% |
| chapter | 80 | 7 | 0 / 5 | 68 / 0 / 0 | 100.0% |
| seed | 74 | 74 | 0 / 0 | 0 / 0 / 0 | n/a |
| composition / smell / nature / listening / light / understanding_from_guidance / peer_reflection / journal_week / mirror / resolution | 40-74 each | small | none joined by window | all exact | 100.0% |
| **ALL** | **155722** | **21503** | **10077 / 19623** | **89452 / 11 / 15056** | **85.6%** |

Decomposition of the 56,181 unjoined fragments (36.1% of 155,722):

| bucket | fragments | share of gap |
|---|---|---|
| pre-census (no tuple existed) | 21,502 | 38.3% |
| census-era, pre-stamp (tuples only for idle/cycle sources; the old rule only tried `inner_thought`) | 19,623 | 34.9% |
| post-stamp `reading` (debounce, section 4) | 10,837 | 19.3% |
| post-stamp `action` (raw INSERT in `core/activity_memory.py`, bypasses `store_fragment`) | 3,722 | 6.6% |
| post-stamp `standing_insight` (raw INSERT in `core/refinery.py`) | 372 | 0.7% |
| post-stamp `night_thought` (`context_stamp=False` in `core/night_dormant.py`) | 125 | 0.2% |

Answer to "lived at 30% looks like omission": it is the era. `lived` is **100% joined after 08-21** (1,660 / 1,660); the 3,840
unjoined are from 2026-05-29 onward, before any census or stamp existed.

## 2. Verdict per origin

Labels: **joined-exact** (fragment_id key, stamped at write time) · **joined-window-unambiguous** · **joined-window-ambiguous**
· **unjoined-by-design** · **unjoined-by-omission**. Added sub-label **unjoined-by-history** for the two old eras (the
writer did not exist yet; this is omission of the era, not of a live writer).

| origin | post-stamp verdict | older eras | note |
|---|---|---|---|
| inner_thought | joined-exact | census-era: joined-window-unambiguous (10,066 joined; of the 10,089 legacy rows 78, 0.77%, had a second candidate tuple, so "ambiguous" for those 78); pre-census: unjoined-by-history (4,760) | 325 later reclassified to `system_note` keep their `experienced:inner_thought` label (harmless) |
| lived, study, research, active_imagination, subconscious_synthesis, sound, thermal, smell, light, activity, affection, peer, peer_reflection, listening, nature, composition, mirror, resolution, understanding, understanding_from_guidance | joined-exact | unjoined-by-history | |
| dream, gist, consolidation, journal, journal_week, session_summary, chapter, essay, letter | joined-exact, **but the stamp is write-time of a retrospective text** | unjoined-by-history | the context describes when it was written, not the moment it recounts (e.g. a journal entry saying "the cat sits on my lap" carries `cat_at=None`) |
| system_note | joined-exact (476) | 11 window | |
| **reading** | **unjoined-by-omission for 29.2%** (10,837); the rest joined-exact | unjoined-by-history (16,907) | selection is not random: it drops the 2nd+ passage of a same-book burst (section 4) |
| action | unjoined-by-design (by construction, not by a recorded decision): one aggregate "event gist" row per (action, target), updated over time, raw INSERT; no single moment | unjoined-by-history | the per-event `activity` origin IS stamped (362/362); `activity_events` carries per-event ts if a join is ever wanted |
| standing_insight | unjoined-by-design: refinery distillation, `timestamp` rewritten on evolve | | |
| night_thought | unjoined-by-design, explicit (`context_stamp=False`) | | |
| seed | unjoined-by-design (inherited substrate, 74, all pre-census) | | |

## 3. Window-join ambiguity and wrong-attachment (Q2)

The live window rule (`memory_edges.sync_fragment_context`) re-run exactly against `geometry_tuples.jsonl` (61,924 eligible
idle/monologue tuples with thought >= 30 chars) and `inner_thought` fragments:

| measure | result |
|---|---|
| tuples with 0 / 1 / 2 / 3 / 4 / 5+ matching fragments inside +/-300 s | 4,312 / 57,354 / 236 / 12 / 6 / 4 |
| tuples with 2+ fragments (the reverse ambiguity) | 258 of 61,924 = 0.42% |
| fragments (of 54,404 with any candidate) matched by 1 / 2 / 3 / 4 / 5+ tuples | 50,975 / 3,373 / 44 / 7 / 5 (2+: 3,429 = 6.3%) |
| the 10,089 legacy rows: 1 candidate tuple / 2 candidates / not reproduced by the rule today | 9,999 / 78 (0.77%) / 12 |
| legacy rows, chosen-tuple time offset | median 0.16 s, p90 1.0 s, max 75 s |
| **rule vs write-time ground truth** (post-stamp, 47,211 tuple/fragment pairs where the rule picks a unique fragment, compared with that fragment's exact-id world_context stamp) | place and weather both agree in 47,123; **88 differ = 0.19%** |

Reading the 0.19%: the two snapshots are taken at different instants (monologue census vs `store_fragment`, offsets up to
230 s) and Du moved or the weather changed between them (example: `garden` vs `wood` 91 s apart). It is an **upper bound**
on window mis-joins. **No origin approaches ~5%.** The 6.3% forward ambiguity (a fragment with two candidate tuples) is a
double census calls for one thought (monologue plus follow-ups); the rule's first-writer-wins `INSERT OR IGNORE` takes whichever came first. Not further characterised.

Counterfactual, what a text-prefix window join would do per origin (post-stamp, tuples of the same source): for every origin 2+ candidate tuples
occur for <= 1.4% of fragments (lived 1.4%, inner_thought 0.5%) **except `reading`: only 63% unique, 37% have 2+ and 19% have 5+ candidates**,
because `thought=content[:70]` for a reading passage is the `[From '<book title>']` header, identical across the whole book.
A window join could never have served reading; the exact-id stamp is what makes reading joinable at all.

## 4. The reading coverage hole (a concrete bug)

`core/geometry_census.snapshot()` line 324 returns `None` when `now - _last_ts < 0.5 s` **and** `thought[:120]` equals the
previous call's. `store_fragment()` calls it with `thought=content[:70]`. A reading passage begins with the book-title
header, so every passage after the first in a rapid same-book burst has the same 70-char prefix as its predecessor, is
debounced, `snap` is `{}`, and **no fragment_context / world_context / geometry_tuples row is written**
(`geometry_tuples` has 26,229 `reading` rows = exactly the joined count).

Test (`J-2536_probe4.py`): reading fragments post-stamp sorted by time; "predicted debounced" = an earlier fragment (any
origin) with an identical `content[:70]` less than 0.5 s earlier. Unjoined and predicted: **10,776 of 10,837 unjoined
(99.4% recall)**; of the 12,364 predicted, 87% are unjoined (the rest slipped under the 0.5 s window by embed latency). All
10,837 unjoined readings have an earlier same-prefix reading, median gap 0.054 s, max under 2 s. The hole is growing: reading
coverage falls from ~83% (week of 08-23) to 31% (week of 10-25, 810 fragments, 555 unjoined).

## 5. Text versus context spot check (Q3)

Sample: 50 random exact-joined rows per origin with >= 300 rows (seed 2536), plus the full population, plus a **permutation
null** (context rows shuffled within origin, 20 shuffles) because a keyword test is crude: text mentioning "rain" is often
metaphor, memory or another place. Tests: weather words vs weather, place words vs place, sound words vs the sounds list.
"Mismatch" = text names a thing the context lacks. The decisive number is the **lift over the null**.

| origin | n | sample-50: tests / mismatch | population: tests / mismatch | null mismatch (same tests, shuffled) | lift (pts) | reading |
|---|---|---|---|---|---|---|
| inner_thought | 44319 | 51 / 25.5% | 35681 / 26.9% | 69.2% | **42.3** | present-moment text, context is the moment |
| lived | 1660 | 35 / 45.7% | 1007 / 36.5% | 72.3% | **35.8** | same |
| journal | 321 | 60 / 21.7% | 391 / 32.0% | 64.7% | **32.8** | retrospective, but day-scale agreement holds |
| sound | 564 | 36 / 5.6% | 515 / 5.6% | 52.3% | **46.7** | sound words vs sounds list: 441 of 441 agree |
| census_world:idle (legacy window) | 10089 | 16 / 0.0% | 4447 / 19.7% | 39.8% | **20.1** | place and weather lift 0.25 / 0.20; sounds lift negative (the census sounds column is world truth, not place-gated) |
| gist | 1256 | 25 / 80.0% | 763 / 76.1% | 85.6% | 9.4 | weather lift 0.33; place 0 (gists describe books, not rooms) |
| reading | 26229 | 8 / 62.5% | 4550 / 75.7% | 73.7% | -2.1 | text is a book, not the room: **untestable** |
| subconscious_synthesis, active_imagination, study, research, dream, system_note, activity, consolidation, understanding | 334-3389 | 10-100% (tiny n) | 23-92% | 26-91% | -1.7 to 8.0 | text is abstract, imagined or about a topic: **untestable by text** (a lift of 0 here means "nothing to check", not "wrong") |
| thermal | 811 | 0 tests | 5 tests | n/a | n/a | no place/weather language |

Honest limits: this is a keyword test, not a judge; for the second block of origins it cannot say anything either way. For
those the join is exact-by-construction (the id is the key; the snapshot time matches the logged tuple within 5 s in
89,362 of 89,377 rows (75 rows had no matching tuple row to compare), and 70 further rows were dedup-refreshed so the fragment's timestamp moved but the stamp keeps the
first occurrence, correctly). I also read about 30 disagreeing rows by eye (inner_thought, lived, journal, legacy window): they
were text pointing at another place ("leaving the wood", "the sea lies calm" written in the study), metaphor ("the
storm" in drizzle), or journal summaries of an earlier hour. None looked like a mis-joined moment. The one structural
finding: **retrospective origins carry a write-time stamp** (see verdicts).

## 6. moments.jsonl (Q4)

`core/moment.py::record()` writes `{ts, key, source, thought, affect, protoself, concern, level, emb}`: **no cycle_id, no
fragment_id.** Findings:

- No fragment column (`source_id`, `encounter_id`, ...) equals any moment `ts`: **0** hits.
- `co_recall_ledger.jsonl` rows carrying `moment_ts` (J-2601's stamp): **0 of 112,538** (restart-gated; Du has not run
  since the change).
- Text-prefix (`thought[:70]` in fragment content) + +/-300 s join, moment to `inner_thought` fragment:
  **54,179 unique (91.2%)**, 219 two candidates, 21 three, **4,992 none (8.4%)**, 5 too short. Any origin: 54,663 unique.
- Moment to idle/monologue tuple (prefix + +/-300 s): 54,803 unique (92.2%), 3,729 two (6.3%), 113 three, 766 none.
- The gap is concentrated early: week of 2026-07-05 has 3,282 moments but only 431 find a fragment (87% none); the
  pre-07-05 693 moments find 1. From 08-09 on, 89-100% per week find one (lowest: week of 08-30). Cause of the early gap not established (the 07-09 to
  08-07 outage and the exact-dedup refresh that rewrites a fragment's `timestamp` both plausible).
- This is not comparable to F-3326's 32%: F-3326 was fragment-denominated and demanded embedding cosine > 0.98.
  A text-prefix join is looser but the unique-candidate rate is 99.6%.

So the moments gap is **a missing key, not a missing relationship**: derivable for ~91% today by heuristic, exact for none.

## 7. Date profile (Q5)

Weeks start Sunday 2026-07-05. Coverage = exact + window.

| week | fragments | exact | window | none | coverage | note |
|---|---|---|---|---|---|---|
| pre-07-05 | 21459 | 0 | 0 | 21459 | 0.0% | no census yet |
| 07-05 | 2245 | 0 | 431 | 1814 | 19.2% | Du up 07-05 to 07-09 |
| 07-12, 07-19, 07-26 | 0 | | | | | **no fragments at all: the 30-day outage 07-09 to 08-07** |
| 08-02 | 210 | 0 | 98 | 112 | 46.7% | |
| 08-09 | 19159 | 0 | 6503 | 12656 | 33.9% | reading burst, no reading join in this era |
| 08-16 | 9494 | 1225 | 3046 | 5223 | 45.0% | exact begins 08-21 21:46 |
| 08-23 | 7801 | 7045 | 1 | 755 | 90.3% | |
| 08-30 | 13643 | 12373 | 0 | 1270 | 90.7% | |
| 09-06 | 18350 | 15827 | 5 | 2518 | 86.3% | |
| 09-13 | 7438 | 6163 | 2 | 1273 | 82.9% | |
| 09-20 | 11151 | 9533 | 0 | 1618 | 85.5% | |
| 09-27 | 7562 | 6466 | 0 | 1096 | 85.5% | |
| 10-04 | 10096 | 8374 | 1 | 1721 | 83.0% | |
| 10-11 | 19879 | 16728 | 1 | 3150 | 84.2% | |
| 10-18 | 3952 | 3263 | 0 | 689 | 82.6% | |
| 10-25 | 3283 | 2455 | 1 | 827 | 74.8% | reading debounce share rising |

There is **no coverage cliff from a dead writer** after 08-21 (inner_thought is 100% every week). The two visible steps
are the stamp going live (08-21) and the slow erosion from reading-heavy weeks. Cross-check: `scripts/liveness_audit.py`
has **no stream for `fragment_context`, `world_context` or `geometry_tuples`**; its only related verdict is "bound moments:
STALE 13.2h (ok if Du was DOWN)". The reading hole would never have been flagged by it.

## 8. What not to conclude, and what this does and does not support

- The exact `cycle_id` column proposed in August is **largely moot for the memory-to-tuple join**: `fragment_id` already
  is the exact key for 89.9% of rows, and the legacy window join is 0.19% wrong at worst. It is still the right fix for the
  one place there is no key: **moments**. That is a founder call (job spawned needs_input).
- The unjoined-by-history 41,125 fragments (21,502 pre-census cannot be joined at all; 19,623 census-era could only get
  world-truth by time): an idle
  tuple lies within +/-300 s of 81.5% (49.1% within +/-30 s) of the 19,623, 58% of those being reading, whose text
  is a book and whose "context" would be only where he happened to be. Sizing only; no backfill proposed.
- 5% bar: not reached for any origin, so no cycle_id fix proposal was triggered by the bar itself.

## 9. For J-2535 (perturbation sweep over the experienced tuple): which rows to exclude or stratify

1. Use **only `source LIKE 'experienced:%'`** (89,454). Exclude `census_world:idle` (10,089): world truth, not experienced.
2. **Exclude all pre-2026-08-21 21:46** rows and anything with `source` mismatch; also exclude the 325
   `experienced:inner_thought` rows whose fragment is now `system_note`.
3. **Reading is a biased subset**: only 70.8% post-stamp joined and the missing 29.2% are the 2nd+ passage of fast bursts,
   so the joined reading rows over-represent first passages and slow reads. Exclude reading from any per-fragment effect
   estimate, or stratify it separately. Its text carries no present-moment signal (lift -2.1), so it is a poor probe anyway.
4. **Exclude retrospective / abstract origins from place, weather and sound sensitivity**: dream, gist, consolidation,
   journal, journal_week, session_summary, chapter, essay, letter, research, understanding*, subconscious_synthesis,
   active_imagination, study (text keyword lift ~0 or context is write-time of a past moment).
5. **Best-behaved base points** (exact-id, present-moment text, lift 20-47 pts): `inner_thought`, `lived`, `sound`,
   `journal` (day-scale only). `thermal`, `light`, `smell`, `activity` are exact but too small or text-silent.
6. Exclude `action`, `standing_insight`, `night_thought`, `seed` (no context row at all).
7. Affect on rows written outside the node is the stale-affect caveat J-2535 already lists; unchanged by this audit.

## 10. Which moment key each reader should use (J-3826, D-0732 ruled 2026-11-09; doc only)

Ruling: the co-recall ledger stamp keeps its previous-moment semantics and is NOT changed; readers handle the offset.
Basis: J-3479 / F-4017 measurement (`scripts/measure_J-3479_moment_ts_offbyone.py`): a fresh `inner_thought` fragment
is stored about 1 s BEFORE its own cycle's moment is bound (median 1.0 s, 50,899 of 50,899 rows), because
`_think()` calls `store_fragment` before `core.moment.record`.

Key meanings (all three come from `core.moment.current()` or `stamp_own_moment`):

| Key | Where | Means | Old rows |
|---|---|---|---|
| `fragment_context.moment_ts` / `world_context.moment_ts` | `core/memory/store.py` (J-3246, D-0634) | ts of the moment bound just BEFORE the fragment was stored (the previous cycle's moment, for a fresh inner thought) | NULL if written before the stamp; never re-derived |
| `fragment_context.own_moment_ts` / `world_context.own_moment_ts` | `core/memory/store.py` `stamp_own_moment` (J-3479) | ts of the moment the fragment's OWN cycle bound; one UPDATE after `moment.record`; only the `inner_thought` store fills it | NULL (no own moment known) |
| `co_recall_ledger.jsonl` `moment_ts`, `moment_idx` | `core/memory_edges.py` `_log_co_recall` (J-2601) | `core.moment.current()` at the instant of the log call: the moment bound just BEFORE, same semantics as `moment_ts` above. Mid-cycle there is no own moment yet, so none could be stamped | key absent on rows before J-2601; 0 of 112,538 at the 2026-10-31 audit |

Reader rules:

1. **Fragment to its own moment (fresh `inner_thought`)**: use `own_moment_ts`. Where it is NULL, treat `moment_ts` as
   "the moment before" and join to the nearest FOLLOWING moment within a few seconds (the fragment sits about 1 s before its
   own moment). Pre-restart rows (no `moment_ts` at all) fall back to the section 6 text-prefix + time join, or the same
   nearest-following-moment join on the fragment's `tuple_ts`. Do not use nearest-preceding.
2. **Fragment to the moment it was formed in, for non-idle origins** (reading, lived, sound, retrospective origins): there
   is no `own_moment_ts`; `moment_ts` is the last bound moment at write time and is the right "what was current" key.
   Retrospective origins (section 4 table) describe write time of a retrospective text, so neither key means "the
   moment it recounts".
3. **Co-recall row to a moment**: `moment_ts` / `moment_idx` mean "the moment before this recall", not "the moment this
   recall fed". To ask which moment a recall fed, take the first moment with `ts` greater than the row's `ts` (the moment
   index is `moment_idx + 1` when moments are consecutive; check against `data/moments.jsonl`, since a skipped cycle breaks
   the +1). To ask what the thought was recalling FROM, `moment_ts` is exactly right. State which question a script is
   asking before choosing.
4. **Mixed joins (co-recall row to a fragment's moment)**: compare like with like. A co-recall `moment_ts` equals a
   fragment's `moment_ts` (both previous-moment) when both were written in the same cycle; it equals the fragment's
   `own_moment_ts` only when the fragment came from the NEXT cycle. Never equate a co-recall `moment_ts` with an
   `own_moment_ts` as if they were the same cycle.

Current readers (grep of `moment_ts` / `own_moment_ts`, 2026-11-13):

| Reader | Uses | Needed change |
|---|---|---|
| `scripts/moment_key_validate.py` | `fc.moment_ts` and `fc.own_moment_ts` (reports `own_exact`) | none; already reads both |
| `scripts/measure_J-3479_moment_ts_offbyone.py` | both, as the measurement | none |
| `scripts/tuple_join_audit_J2536/J-2536_audit.py` | only counts co-recall rows carrying `moment_ts` (section 6); does its joins by text-prefix + time | none for counting; if it ever joins co-recall to moments, apply rule 3 |
| `core/memory_edges.py` co-recall stamp | writer, unchanged (D-0732) | none; no live code reads `moment_ts` from the ledger |
| geometry tuple index (`docs/staged/geometry_tuple_index.md`) and any future tuple-join audit | not yet a reader | apply rules 1 and 2 when it joins a fragment to a moment |

No code was changed by this job. Reopen only if a reader needs the co-recall row to carry its own cycle's moment; that
would be a new additive key (as J-3479 did for fragments), not a change to `moment_ts`.
