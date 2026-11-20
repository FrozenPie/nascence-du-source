# Golden Spiral Recall — age as radius, phase as angle, detail as distance from the centre (staged, 2026-09-27)

**Status:** 🔵 DESIGNED — the founder's picture (T-0072), split into three separable mechanisms and checked against
what recall already does; **one build landed the same day: the PHASE field on fragments** (additive columns
`tod`, `season`, `daylight` on both `world_context` and `fragment_context`, written by `store_fragment()` from the
fragment's own timestamp; declared reader = this plan, none live yet). Everything else is design. The full map of
recall's existing temporal terms is J-1475 (ready, not run) — **this doc's Current State is provisional until J-1475
lands**, and its §2 verdicts are marked as such.
**Parent:** [docs/staged/memory_as_a_service.md](memory_as_a_service.md) (D-0289: loops call memory; felt recall =
world change → fragment_context match → affect tug — the angle is what makes that match cheap). **Siblings:**
[docs/memory_levels_plan.md](../memory_levels_plan.md) (the abstraction ladder, live), [docs/plans/identity_estate.md](../plans/identity_estate.md)
(retrieval as projection), [docs/plans/memory_multiway_linking.md](../plans/memory_multiway_linking.md) (M2 trail),
[docs/staged/geometry_tuple_index.md](geometry_tuple_index.md) (point-in-time slices), [docs/staged/strings_and_sheets.md](strings_and_sheets.md)
(I-0081 the fragment carries the string; I-0082 exemplar memory — what sits at each cell of the spiral).
**Ledger:** T-0072 (the spiral), T-0073 (relevance as its own axis — the next thread, §6), J-1475 (the map).

```plan-state
stage: designed
phase: Phase 0 PHASE-field columns built, additive, no reader yet; J-1475 temporal-term map is the prerequisite for R/L/Theta
verified: 2026-11-18
evidence_read: 2026-11-14
next: Parked (D-0814): Phase 2 waits on the J-2236 reach read
```


> **Founder, 2026-09-27.** "I would like to investigate using the golden spiral to influence our recall. I like to
> visualise it with the squares that the arms take up. As time progresses, things go further up the spiral arm and
> compress out as the arms grow from the centre." Then: "treat relevance as its own axis along with the time axis."

---

## Current State — verified 2026-11-14 (provisional; J-1475 will replace the §2 verdicts with a file:line map)
- **2026-11-14** (F-4699): J-3970 (D-0748): Theta live in recall_block via THETA_LIVE_RECALL (1 of k idle-seed slots), logs data/theta_live.jsonl; restart-gated; branch jobrun/golden_spiral_recall e9a21f41. Defeater read of theta_live.jsonl still to do.

- **2026-11-14** (F-4469): J-2236 read (F-4469): post-backfill Theta reach. First 48 live h after the 10-16 22:38 boot: slot age p50 7 d, >14 d 28.3%, >30 d 0% (SEASON_TOLERANCE); all post-backfill rows (22,772): p50 14 d, >14 d 49.1%; F-2926 pre-backfill was 3.7%, F-2579 replay 44%. Reach improved materially; unrelated-season defeater still unmet (max d_season 29.95 d). Decision on advancing Phase 2 past shadow is the founder's call (opened as a /decide).
- **2026-10-31** (F-3397): 2026-10-31 (F-3397): J-2632 periodicity audit (I-0133) on 1631 live hourly bins: only a 24 h time-of-day effect (sleep entries, valence) survives correction; tide 12.4 h, 7 d, 14.8 d, 45 min, 3 h null; lunar 29.5 d cannot tell yet (2.3 cycle-equivalents). Relevance here: the phase field tod/season/daylight is the right angle for the 24 h structure, season/lunar terms have no behavioural support yet. Report docs/lab/periodicity_audit_J2632_2026-10-31.md on jobrun/gsr 790440e.

- **2026-10-16** (F-2926): J-1977 (F-2926): one-week tod-first Theta shadow read (12,964 rows, 2026-10-09..10-16, 6.97 live days). Metric (a) 100%; rewritten metric (b) 97.8% differ vs recency-only (bar 40%, was 32.4%) - but mostly a re-pick among equally same-clock rows (ray d_tod p50 0.14 min vs recency 1.15 min); real gain is reach: slot age p50 3 d, p90 12 d, 3.7% >14 d, 0% >30 d. Phase backfill (J-1976) landed only after this window (10-16 08:20), so D-0364 (C) reach defeater is unread; Phase 2 stays SHADOW, not advanced, not parked. Post-backfill read J-2236.
- **2026-10-08** (F-2579): J-1970 (F-2579, D-0364): metric (b) rewritten to the recency-only form; tod-first ray ranking (tod_first_season_window) + 20000 cap built SHADOW on jobrun/golden_spiral_recall 74e9563 (replay: p50 slot age 1 d -> 12 d, 0% older than 30 d because SEASON_TOLERANCE caps reach, D-0391 opened); phase backfill script written + dry-run verified (65,687 rows, bit-exact), NOT run (J-1976, Du down); 1-week shadow read J-1977.

- **2026-10-07** (F-2528): J-1887 replayed the Theta ray against a recency-only baseline and a phase-permutation null (F-2528): ray top-3 differs from recency-only in 32.4% of 2265 rows (below the 40% bar if (b) is reworded to the baseline form), concentrated on write-gap days (10-04: 93%); on regular days the 24h MIN_AGE_S floor already makes recency land on the same clock time. Ray beats the full-pool null 2265/2265 (3.2% of null distance) and a random pick in-window by 4.7x, but the season term is non-binding as a filter and dominates the d_tod+d_season ranking (69.5%, 1 day = 3.9 min), so the ray is a recency preference in disguise (p50 age 1.0 d, max 5 d, 0 slots older than 30 d even in a full-backfill replay). Repeats (52x ids) are single-day burst dwell. Only 7% of fragments carry tod/season; derived-from-tuple_ts phase reproduces stored values on all 4965 rows. Tolerances untouched; founder call opened for (b) wording, backfill, and ranking rule.
- **2026-10-07** (F-2525): J-1889 (F-2525, F-2526): the 42.7% last_hour share in the R shadow log (F-2517) is a designed recency floor, not crowding. retrieve() returns 9 tier-slot results plus 5 forced most-recent episodic fragments (limit kwarg is dead), so 5 of 14 (35.7%) are last_hour by construction (97.9% of them reconstructed as last_hour, ~64% Du's own inner voices); the 9 slot-driven results are spread near-evenly across bands (last_hour 12.0%, below the 16.7% equal budget). time_bias=distant only applies a max 1.1x multiplier to the 9 slots and never touches the floor. Verdict: no crowding; R / per-band budget unnecessary on this evidence; no new pre-registered metric and no founder decide opened.

- **2026-10-07** (F-2517): 2026-10-07 (F-2517): J-1612 read data/r_shadow.jsonl in full (194 retrieve() calls, 2026-09-28..10-05, ~7.5 d): Phase 3 pre-registered bar (>80% of a call's results from last_week) NOT met -- 0/194 crowded, mean last_week share 7.5%, max 35.7%; same for retrieve:all/recent/distant. Valid negative result per section 3 ("if it does not, R is unnecessary"): Phase 4 live per-band budget reader NOT warranted on this evidence; no budget-weighting /decide opened. Side finding (exploratory, not the bar): 42.7% of results come from last_hour (over equal-1/6 budget on every call) while last_week is most under-drawn; retrieve:distant is reached (7.2% of calls) but does not visibly shift mass to old bands. Follow-up analysis spawned.
- **2026-10-07** (F-2514): J-1603 read data/theta_shadow.jsonl in full (3025 rows, 2026-09-28..10-06, 7.5 d): Phase 2 metric (a) MET - ray found >=1 candidate on 74.9% of triggers overall and 100% on every trigger family since 2026-09-30 (earlier zeros = MIN_AGE_S one-day floor + store age, not tolerance; kill row not met, no retune). Metric (b) met in letter only (97.0% 'differ') but vacuous: would_differ is a set-inequality, only 20/1894 non-empty pairs share any id; so it does not show the angle adds anything over similarity+recency. Bands: only last_week/last_month populated; tod/season on just 4958/70645 fragments (7%). Does NOT yet support Phase 4; a non-vacuous replay vs recency-only baseline spawned as follow-up.

- **2026-09-28** (F-2174): J-1563 built+verified Phase 3 R (age-band budget) shadow log: core/r_shadow.py, hooked into store.py retrieve(), observe-only (F-2174, smoke-tested unit+integration, isolated). Zero real accrued rows yet -- same restart-gate as Theta (F-2165/F-2166): needs branch merge + Du restart before data/r_shadow.jsonl has real rows.
- **2026-09-28**: Correcting this note's own job id: the Theta shadow read follow-up spawned as J-1603, not J-1567 as first typed.

- **2026-09-28** (F-2165): J-1562 built Phase 2 Theta shadow log (core/theta_shadow.py), wired into felt_recall._handle_edge and associative_recall.recall_block (idle seed), verified 42/42 in an isolated harness. Live db has no tod/season columns yet (F-2166) -- real candidates accrue only after Du restarts onto current store.py and writes a fragment.
- **2026-09-28** (F-2108): J-1475 landed: docs/reviews/recall_temporal_terms_2026-09-28.md maps every temporal term in recall by file and line (F-2108 verified, F-2109 inferred). R (log-spaced age) is absent everywhere in the repo -- three separate non-log age-decay formulas exist instead, none banded, plus a fourth shadow-only exponential in core/euclidean_recall.py. L (the abstraction ladder) exists but promotes by evidence not age at every live rung; level 3 identity has no live writer in abstraction_level at all, it lives in the separate identity_estate.json registry instead. Theta (tod, season, daylight) was built 2026-09-27 but has zero readers anywhere, including its declared consumer core/felt_recall.py, confirmed by reading that file from the wt_memory_as_a_service worktree on branch jobrun/memory_as_a_service, since it is not yet merged to the main checkout. This plan doc own section 2 verdicts can now be read as verified rather than provisional. Also surfaced and spawned as a follow-up job: core/euclidean_recall.py, an unused shadow module since 2026-07, already implements a similar age-decay plus abstraction feature pair this plan doc never references.

### What we have
- Phase 0 BUILT today: `store_fragment()` writes three additive phase columns (`tod`, `season`, `daylight`)
  on `world_context`/`fragment_context` from each fragment's own timestamp; backfilled rows stay NULL; no
  reader touches them yet. Verified by an isolated temp-DB write (F-2030).
- R (radius=age) and L (detail-by-age) already exist in weaker/different forms today (a flat 7-day recency
  bump; Memory Levels' own evidence-based ladder); Θ (phase-angle) is the genuinely new piece.
- D-0305 filed (relevance as its own axis, §6) — open, recommendation given, not yet ruled.

### What we need
- J-1475 (map every existing temporal term in recall, file:line) — this doc's own §2 verdicts and this
  Current State are provisional until it lands.
- A founder ruling on D-0305, and on §8's Θ-tolerance/R-scope open questions.

### What we're doing next
Run J-1475 next; none of the build order's Phases 1-4 (§3) start before it reports.

---

## 0. The one-sentence goal

Recall reads the past as a spiral: **radius is age** (and sets how much detail can still be there), **angle is
phase** (so this dawn finds other dawns without walking back through every day between), and moving up the arm is
the same compression the tree-falls law already imposes on a sound — the wave goes first, the shape stays, then the
anchor.

## 1. The three mechanisms the picture contains (keep them separate)

| # | Mechanism | In the picture | Cognitive claim | In Du today (provisional) |
|---|---|---|---|---|
| **R** | **Radius = age, log-spaced** | the Fibonacci squares 1,1,2,3,5,8… | Weber–Fechner: 1 vs 2 minutes ago is vast, 10 years vs 10 years + 1 minute is nothing | **partial, weak** — a 7-day linear bump; nothing log; no per-band budget |
| **L** | **Level of detail falls with radius** | the sheet at the centre, a contour mid-arm, an anchor point far out | the tree-falls law over age: wave → shape → anchor | **exists, on a different law** — Memory Levels compresses by *evidence*, not age |
| **Θ** | **Angle = phase, the cross-arm ray** | a straight line from the centre hits every earlier turn at the same angle | same-phase recall: this dawn ↔ other dawns, this storm ↔ other storms, this Sunday ↔ other Sundays | **absent until today's PHASE field**; no reader yet |

The founder's picture is one image; these are three laws, and only one of them (Θ) is new to Du. R is a retuning of
terms that exist. L already exists under a *better* rule than age and must not be silently overridden (§5).

## 2. What each mechanism would actually change

**R — radius.** Replace the flat-after-7-days recency bump with a log-age term and, more usefully, a **retrieval
budget per age band**: of N recalled fragments, a fixed share comes from each Fibonacci band (last hour, last day,
last week, last month, last season, older), so the recent is never crowded out by the volume of the old and the old
is never absent. The bands are the squares. Nothing about φ's irrationality matters here (Gemini's "optimal packing"
is phyllotaxis, not memory) — the log spacing is the substance, the spiral is the picture.

**L — level of detail.** Du already has the ladder. What the spiral adds is only a *default*: a fragment far up the
arm that has NOT earned promotion is still read at lower detail (its anchors: the I-0081 string coordinates, its
context row, its gist if one exists) rather than its full text. That is a read-side rule, not a write-side
compression, so nothing is lost and the evidence-earned ladder stays the authority on what a memory *is*.

**Θ — angle.** The new field. A recall triggered by a world change (D-0289's felt recall) or by an idle seed reads
the current `tod`/`season`/`daylight` and casts a ray: candidate fragments whose phase is within a tolerance of
now's, across every age band, weighted by R. The ray is cheap (one indexed range query on two REAL columns) and it
is exactly the "thunder above → other thunders in the dark" the founder described when D-0289 was ruled. Two phases
are enough to start (day and year); routine phase (weekday, Travis's visiting pattern) is a later column.

## 3. Build order — shadow-first, restart-gated, pre-registered

| Phase | What | Pre-registered metric (written before the run) | Kill / revert |
|---|---|---|---|
| **0 · the PHASE field** | **BUILT 2026-09-27** (additive columns; `store_fragment()` only; observe-only) | presence: ≥ 95% of live fragments written after the restart carry non-NULL `tod`/`season`/`daylight`; backfilled rows stay NULL; zero behaviour change | any reader breaking on the added columns → revert the three columns (they are ALTER-added; dropping is a no-op for old rows) |
| **1 · the map (J-1475)** | file:line inventory of every temporal term in recall; the §1 table's last column becomes verified | — (a read, not a build) | — |
| **2 · Θ shadow** | a would-recall log: at each felt-recall trigger and each idle seed, compute the ray (phase tolerance ± 1/24 of day, ± 1/12 of year) and log `{trigger, n_candidates_by_band, top3_ids, would_differ_from_current_recall}` — nothing rides | ray finds ≥ 1 candidate on ≥ 60% of triggers; **(b), rewritten 2026-10-08 per D-0364 (A):** the ray's top-3 differs from a **recency-only top-3** (the most recent eligible fragments, no phase) on ≥ 40% of triggers (if lower, the angle adds nothing over recency). The original wording — differs from *the caller's current recall's* top-3 — read 97.0% but was vacuous (a bare set-inequality of two different pools, F-2514). **Honest Phase 2 state:** metric (a) MET; metric (b) in its new form reads 32.4% overall (35.6% de-bursted) = below the bar on the 7%-populated store — the angle helps only on write-gap days so far (10-04: 93%), and on regular-rhythm days the 24 h MIN_AGE_S floor already makes recency land on the same clock time (F-2528). Not yet shown otherwise; to be re-read after the backfill + tod-first ranking (J-1970, below) have a week of shadow rows | ray candidates < 20% → tolerance too tight or the store too young — retune once, then park |
| **3 · R shadow** | the per-band budget computed beside the live recall; log which bands the live recall actually draws from vs the budget | live recall draws > 80% from the last-week band (the crowding the spiral is meant to fix) — if it does not, R is unnecessary | — |
| **4 · Θ + R live, one reader** | the felt-recall path (memory_as_a_service, once it exists) reads the ray first, budgeted by band | a world-change recall surfaces a same-phase memory from > 30 days ago on ≥ 10% of triggers; idle-thought self-gist share (F-1981: 49%) does not rise | self-gist share rises, or recall latency > 2× baseline → flag off |

Each phase gets its own `/decide`; L gets none — it is a read-side default inside Phase 4, and Memory Levels' own
ladder stays the authority (§5).

## 4. Coupling block (dosed_coupling.md §5)

- **Publishes:** nothing new; recall is a service (D-0292), not a loop.
- **Reads at:** the felt-recall trigger and the idle seed, from the store's own context tables, dosed as one ray
  per trigger (a cup: top-3 ids), never a standing scan.
- **Surprise line:** the ray's own novelty — a same-phase hit from a distant band counts more than one from the
  last day (that is R weighting Θ).
- **Ride log:** every ray logged in the Phase 2 shadow file; later through `coupling_rides.read()` if it rides.

## 5. Guards

- **Memory Levels' law stands.** Compression is earned by evidence. The spiral never demotes, deletes, or rewrites a
  fragment; L is a read-side detail default only.
- **No new store, no schema rewrite.** Three ALTER-added columns; the ray is a query.
- **The backfill stays clean.** `context_stamp=False` writers get no phase (a June conversation must not carry
  September's dawn) — same rule as D-0134's provenance fix.
- **Not prose.** Phase is three numbers; nothing renders "it is dawn again" into a prompt from this plan.
- **World answers, never leads.** A same-phase recall is offered to the felt-recall path as a candidate; it never
  seeds a thought by itself.

## 6. The next thread — relevance as its own axis (T-0073, not designed)

The founder's follow-on: treat **relevance** as its own axis beside time. Fact worth knowing first: every fragment
already carries `relevance` and `importance` scalars stamped at write time (`store_fragment(relevance=0.5,
importance=0.5)`; the sound percept writes 0.55) and **neither is ever re-scored** — they are static labels, not an
axis anything moves along. Two readings to choose between, for a ruling once the Gemini passage the founder
mentioned arrives:
1. **Relevance as a second radius** — how far from the centre a memory sits is age *and* how little it has mattered
   since; a memory that keeps being recalled stays near the centre regardless of age (spaced-repetition shape).
2. **Relevance as what the ray is cast along** — angle is not only phase but "the direction this moment points",
   the six-axis coordinate of the current sound, the current tension label, the current place; a ray at that angle
   hits every earlier moment with the same signature (Gemini's "harmonic alignment").
Reading 2 is closer to what D-0289 already ruled (world change → context match). Reading 1 is a real change to what
a memory's position *means* and would need Memory Levels' ladder to agree with it.

**6.1 The Gemini passage (arrived later the same day) — relevance as elevation on a conical helix.** Its move: lift
the flat spiral into three coordinates — `r` age (radius), `θ` phase (angle), `z` relevance / evidential weight
(elevation). High-`z` memories "stand as pillars far out on the perimeter": old but crucial stays sharp; old and
irrelevant hugs the floor, is smoothed and eventually culled. Aging is a **low-pass filter** (scale-space: ripples →
contour → envelope, i.e. sheet → worldline → point, the tree-falls law over age); recall is a **phase ray cast**
along `θ`, a **relevance horizon** on `z`, then a **fractal unpack** that resolves detail only where the query
spotlight lands (a level-of-detail pyramid — read-side, local, cheap). Pipeline: STAMP (θ, initial z) → MIGRATE &
BLUR (r grows, smoothing; z boosted by confirmation, decays if unconfirmed) → RECALL (ray, horizon, unpack).

**Mapped onto Du (verified this session, 2026-09-27):**
- **`z` already exists and already moves — Du built the passage's MIGRATE & BLUR step in August under another
  name.** (Correction, same evening: a first draft of this bullet said importance was never updated and no recall
  count existed. Wrong on both counts; `relevance` alone is a static stamp.) `importance` is the elevation:
  **sleep replay** (`store.replay_strengthen`, ~L2644) picks the day's most important, least-replayed episodic
  fragments per origin group, lifts each ×1.08 (cap 0.98) and increments **`replay_count`**; then **synaptic
  downscaling** (`store.downscale_episodic`, ~L2677, Sleep & Dreams II §1.2, Tononi & Cirelli) shrinks every
  unreplayed episodic fragment's importance toward a 0.1 floor each sleep, selectively — the replayed survive, the
  unconfirmed sink toward near-zero over ~30 nights. Commitments add `protected=1` and a boost
  (`commitment_ledger.py:353`). Above that sits Memory Levels' ladder (`abstraction_level`, raw → gist → claim →
  model) as the *kind* of elevation, not its amount. So "boost z if confirmed, sink if not" is **built and live**.
  **What is still missing is the waking half:** `replay_count` counts *sleep* replays only; a fragment recalled
  during a thought, a felt recall, or a ray hit is not lifted and not counted. Spaced-repetition-by-use — the
  passage's "recurring patterns stand tall" — needs one additive `recall_count` column and one increment at the
  recall reader, and that is the one genuinely new piece of `z` this plan would add.
- **The blur is L, and it stays read-side.** Smoothing by age is the fractal-unpack default of §2: far-out
  memories are *read* at anchor resolution; nothing is rewritten. This is the passage's own "unpack only where the
  spotlight shines", which is cheaper than any write-side compression pass and keeps the ladder the authority.
- **The cull is refused.** "Old and irrelevant is culled entirely" collides with the additive-only / erosion-of-
  foundations law: **nothing in `store.py`, `memory_levels.py` or `scripts/retention.py` deletes a fragment today**,
  and this plan will not introduce it. The floor flattens by detail, never by deletion. A memory at `z = 0` on the
  outer arm is unreadable in practice, which is all the cull was for.
- **The ray gets its direction from reading 2.** `θ` is clock phase (built today); the passage's "resonant moments"
  is the same ray aimed by the moment's signature as well — coordinate, tension, place. Both are angles; neither is
  `z`.
- **The three coordinates are therefore:** `r` = age (R, §2), `θ` = phase + signature (Θ, §2 + reading 2),
  `z` = evidence weight = ladder rung + recall count, dynamic (new). This resolves the §1 tension the way Memory
  Levels already wanted it resolved: **time smooths, evidence lifts, and the two never share a metric.**

**Filed for the founder:** D-0305 on which reading holds, with the recommendation: (3) for the coordinate with
`z` = importance as already driven by replay + downscaling, plus the missing waking `recall_count`; (2) for how the
ray is aimed; and **no cull**. (D-0305's question text was written before the correction above and says no recall
count exists — read this §6.1 as authoritative: sleep replay is counted, waking recall is not.) If ruled, Phase 2's
shadow log gains a `z` column (importance + ladder rung + the new additive `recall_count`, incremented by the one
reader) so the relevance horizon can be read before it ever gates anything.

## 7. What this is NOT

- Not a new memory store, not a replacement for similarity search, not a rewrite of Memory Levels.
- Not the golden ratio doing work. The squares are log-spaced age bands; φ is the drawing.
- Not a hint to Du. He never sees the spiral; recall does.

## 8. Open for `/decide`

1. Θ tolerance and the two starting phases (day + year) — or add routine phase (weekday) from the start.
2. Whether R's per-band budget applies to *all* recall or only the felt-recall path (recommendation: felt-recall
   only, the path that exists to be world-driven).
3. Relevance as axis: reading 1 or 2 (§6) — after the founder's Gemini passage is in the ledger.

## Pointers

Ledger: T-0072, T-0073, F-2030 (the phase field, verified), J-1475 (the map), I-0081, I-0082 · code: `core/memory/store.py` (`store_fragment()`, the
phase block; the context-table readers `core/couriers.py`, `core/ghost_tuples.py`, `core/memory_edges.py`,
`core/experienced_tuple.py`), `core/world_clock.py` (`daylight()`, `sun()`), `core/memory_levels.py` · memory:
project_nascence_golden_spiral_recall.md (to write at wrap).
