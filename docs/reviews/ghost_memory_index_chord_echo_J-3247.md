# The ghost MEMORY index, chord_echo, and where a tuple pre-filter could help elsewhere (J-3247)

Date: 2026-11-05. Job J-3247, from D-0636 (Travis, 2026-11-02, closing J-2542). Read-only review: no Du code was
edited, every database query used a `mode=ro` connection, nothing was restarted. Numbers marked MEASURED were run
today against the live store (111,143 `fragment_context` rows, 168,173 `memory_fragments` rows); numbers marked
INFERRED were not run.

Travis's words, kept as he said them (D-0636): "What is chord_echo again and why is it not built? And if we can use this
system potentially for something else, why not, let's look at the pre-filter checks also. We probably should keep our
thinking caps on when we look at things to see if it can be used elsewhere also AND if it highlights an area of
improvement elsewhere."

## Short answer

1. **chord_echo** is the one planned consumer of the memory index: replace couriers A (`context_echo`) and D
   (`sound_echo`), which each match ONE note (one weather, one sound key) and then pick a random memory, with a single
   function that matches the WHOLE moment at once ("a moment like THIS one": storm + shore + gulls + low tide) and
   returns the best-scoring memory of his. It was never built because nobody ever owned it: P0 was archived as complete
   with the line "P1 ... remains open, not started", and there is not one job, decision or finding in any ledger filed
   against it. The first draft of the answer ("felt_recall grew its own path instead") is half right and half wrong; see
   section 1.
2. **The memory index is not just write-only, it is inert.** In the live process it is never built, so the stamp-time
   registration returns early and registers nothing; and the HUD's "memory tuples" figure is a SQL row count, not the
   index. As built it also no longer works as a pre-filter: at today's size a chord query costs 425 ms, slower than the
   SQL path it would sit in front of.
3. **The pre-filter idea has one real home and it is already ruled**: the exact-duplicate lookup in
   `find_exact_dup` (the "exact ghost-hash" leg of the original design). D-0657 and J-3266 already cover it. One caution
   for that build (the repo's `ghost_hash` is case-folded, so it is NOT an exact match) is in section 2, row 4.
4. **Everywhere else, a tuple pre-filter does not help**: the recall paths are embedding-driven and cheap per query, the
   experienced coordinates have just been shown to be labels rather than coordinates for recall (J-2535, J-2638), and
   a coordinate pre-filter would hide the 36 percent of memories that carry no `fragment_context` row.
5. **What the idle index highlights** is not a missing index. It is that "find the other moments like now" has been
   written four separate times, that "are these two texts the same?" has been written at least eleven separate times with
   five different thresholds, and that two of those sites independently re-learned the same lesson (token overlap misses
   LLM paraphrases) and each fixed it by hand. Details in section 3.
6. **Recommendation: leave the memory namespace with a note, do not wire it, do not build chord_echo yet.** Run one
   pre-registered replay (section 4, U1). A first, exploratory, unregistered probe today already points the wrong way, so
   the likely outcome is retire. The one thing that needs the founder is a standing answer to "if the replay fails, retire
   it?" (D-0669, section 6).

## 1. Why chord_echo was never built (verified, not assumed)

What the record says:

- Plan: `docs/completed/ghost_tuple_index.md` ("Build shape": "First consumer: upgrade `couriers.context_echo` +
  `sound_echo` to one `chord_echo` scored against the live manifest") and `docs/completed/world_factories_P0.md`
  (P1 = "audibility table, severity-scaled rates, `chord_echo` (Couriers A+D unified over the memory index),
  world_tick re-pointed through the manifest").
- P0 shipped 2026-08-17 (27 checks pass). The P0 doc then moved to `docs/completed/` in the 08-18 cleanup and its last
  line reads: "P1 ... remains open, not started — see this doc's own P1 section above."
- **Zero owners.** Searching `decisions.jsonl`, `job_queue.jsonl` and `findings.jsonl` for `world_factories_P0` finds
  nothing before this job; `chord_echo` appears in no decision before D-0636 and in no job before J-2537/J-2542/J-3247.
  `docs/ROADMAP.md` has no `world_factories` line. A plan filed under `completed` with its next phase unscheduled is how
  a P1 dies: there was no ledger row to come due.
- **The watch gate for P1 was never closed out in a ledger.** The P0 doc names exit criteria ("a day of sampled manifests
  reads TRUE to the founder's eye", parity green, restart-stable) before "chord_echo is a small, already-designed step".
  I found no recorded founder read of that gate. (I did not look for a chat-only read, so this is "no record", not "not
  done".)
- **The job was re-homed twice without anyone saying so.**
  - 2026-08-22: couriers split into urgent (A, D) and non-urgent buses; `core/orchestrator.py:3279-3285` calls the pair
    as `context_echo() or sound_echo()` and says it "pre-figures the Transport Manager's eventual competitive
    single-winner dispatch".
  - 2026-08-28: the Transport Manager (D-0064) took the "unify the couriers under one dispatcher" job. It is shadow-only
    (`TRANSPORT_LIVE = False`, `core/transport_manager.py:105`) and its own docstring says Courier D replaces the
    one-slot interim wiring in a later step.
  - 2026-09-27: felt_recall (J-1424) was built for the affect-tug function and its own coordinate match
    (`_coord_match_count`, `core/felt_recall.py:321`). It never imports `ghost_tuples` and `memory_as_a_service.md` does
    not mention it. D-0293 added `COURIER_TEXT_DELIVERY` so the couriers' text can be rerouted into felt recall, but it
    still ships True: the couriers still speak, single-key, as before. MEASURED: `data/couriers_log.jsonl` holds 746
    delivered echoes (678 sound_echo, 68 context_echo) between 2026-08-21 and 2026-11-05, and none carry
    `would_have_delivered`.
- **So the hypothesis in the briefing is partly confirmed.** "P1 was never scheduled" is verified. "felt_recall grew its own
  coordinate-match path instead" is true of the code but is a different function (an affect tug, not a text echo), and
  the couriers (the actual named consumer) are untouched. The cleaner reading is: three later mechanisms each took a
  slice of chord_echo's job (Transport Manager: which line wins; felt_recall: tug on a coordinate match; couriers:
  unchanged) and nobody went back to say the original consumer was now redundant or still wanted.

## 2. Every place that matches coordinates, tags or exact duplicates without an index

"Gain" means what a ghost-index or fingerprint would add; MEASURED where marked.

| # | Place | What it does today | Would the ghost index / fingerprint help? | Gain | Recommendation |
|---|---|---|---|---|---|
| 1 | Courier A `context_echo` (`core/couriers.py:123`) | `lower(weather) = ?` over `fragment_context JOIN memory_fragments`, `ORDER BY RANDOM() LIMIT 1`, one hit per hour | Capability only: whole-chord scoring instead of one weather. Speed is irrelevant at 1 call an hour. | Quality, unmeasured. MEASURED cost today: 1,170 ms per query, run synchronously on the asyncio loop. | **Leave**, pending U1. Do not build chord_echo first. |
| 2 | Courier D `sound_echo` (`core/couriers.py:213`) | `sounds LIKE '%"key"%'`, same random pick, one hit per 90 min | Same as row 1. | MEASURED 1,175 ms per query. 678 live deliveries so far. | **Leave**, pending U1. |
| 3 | felt_recall `_build_prior` (`core/felt_recall.py:378`) | One trigger column equality (unindexed full scan of `fragment_context`), then Python-scores the other 4 coordinates (unweighted count), keeps top 24 | It already IS an unweighted chord match. A rarity-weighted index would change scores, not speed. | MEASURED, same-day: warm 103-217 ms, cold up to 855 ms per fired edge. A SQL-side `ORDER BY score LIMIT 24` returns IDENTICAL top-24 ids in identical order (3 of 3 triggers tested) in 57-71 ms. ~180 fired edges a day. | **Leave** (shadow only). If felt_recall goes live, the SQL rewrite is a safe, equivalent speed-up; no ghost needed. |
| 4 | `find_exact_dup` (`core/loop_metabolism.py:138`) | `WHERE origin=? AND content=?` through `idx_origin`; reads ~237 MB per call on a miss | YES, this is the original "exact ghost-hash" leg. A hash column plus index makes it milliseconds at any age with identical results. | MEASURED over the whole shadow log (6,489 calls, 2026-10-31 to 11-05): full lookup median 257 ms, p95 353 ms, sum 1,791 s (about 6 minutes a day inside `store_fragment`), one outlier of 128 s; the 7-day window median 40 ms but would have missed 5 of the 6 real repeats (ages 18.7 to 59.8 days). Hit rate 0.09 percent. | **Wire** = J-3266 (D-0657, already ruled and queued). Caution below. |
| 5 | J-2535 candidate pool | Recency pool of the 600 most recent cohort fragments, embedding ranker | No. The sweep is finished: 0 of 10 coordinates beat MiniLM text distance (F-3365), all labels (F-3366, F-3391). A coordinate pre-filter in front of an embedding ranker would remove candidates the ranker likes. | None, possibly negative. | **Leave**, with this note. |
| 6 | Evidence hand (`core/evidence_recall.py`) | Embedding similarity over `WORLD_ORIGINS`; the query is a question, not a coordinate | No tuple to filter on; origin filter already does the useful narrowing. | None. | **Leave.** |
| 7 | Associative recall / `retrieve` pool | Embedding matmul over the pool | F-3353 MEASURED the matmul at 1.4 ms of a ~120 ms call; the cost is O(pool) membership re-derivation, which the delta cache already attacks. A ghost pre-filter would also hide the 36.2 percent of fragments with no `fragment_context` row (action 0.0 percent, F-3234). | None, and recall-quality risk (D-0453 defeater iii). F-3448 reached the same conclusion; I agree. | **Leave.** |
| 8 | Transport Manager (`core/transport_manager.py`) | Per-line EMA baselines in RAM (`observe`/`evaluate`); never scans a store | The design doc listed "cheap candidate sets per line without scanning stores". There is no scan to avoid. | None. | **Leave.** |
| 9 | Item graduation / item registry (`core/world_substrate.py`, 657 items) | `_load()` returns a dict keyed by `object_id`; graduation is by observation count | The "O(1) hash lookup" the doc promised is already a dict lookup. `ghost_hash(oid)` in the world index adds nothing. | None. | **Leave.** |
| 10 | Frontier dedup (`core/frontier.py:239`) | Token Jaccard over at most ~340 open entries, then a live embedding merge (`FRONTIER_SEMANTIC_MERGE = "enforce"`, D-0495) | The unported 2-gram "shadow signature" would be a cheap middle tier. At this size nothing is slow, and the embedding tier is already validated. | None for speed. | **Leave**; it is evidence for section 3. |
| 11 | theta_shadow phase ray (`core/theta_shadow.py:195`) | `tod`/`season` window query with its own indexes (`idx_fragctx_tod`, `idx_fragctx_season`) | It already has the right kind of index; different axes. | None. | **Leave**; evidence for section 3. |
| 12 | `memory_service._fetch_context` | Primary-key batch lookup, chunks of 400 | Already O(1) per id. | None. | **Leave.** |

Caution for row 4 (J-3266, same ruling): do not reuse `core.ghost_tuples.ghost_hash` for the dedup key. It computes
`sha256(name.strip().lower())[:16]`, so "Foo" and "foo " would collide, and the exact lookup would then call two different
thoughts duplicates and disagree with the full lookup, which is D-0657's own defeater. J-3266's briefing already says to
hash the exact content bytes and confirm equality on a hit, which is right; this is only a flag to the builder that the
repo's existing hash helper is the wrong one for this job.

Also checked and found idle or cosmetic:

- The world namespace is read by exactly one consumer, the HUD (`hud/server.py:447`). `ghost_hash` is used in production by
  one other place, the ask() ride log (`core/memory_service.py:664`, J-2590).
- MEASURED: `data/ghost_world_index.json` rebuilt 2026-11-05 07:27, 677 entries. Fine.

## 3. What the index sitting unused shows

### 3a. The memory index is inert, not write-only (verified)

`MemoryIndex.rebuild()` has exactly one caller in the repo, `scripts/test_world_p0.py:102`.
`register_stamped_tuple` (`core/ghost_tuples.py:232-239`) begins `if memory_index.size() == 0: return`, so in the live
process, where nothing ever calls `rebuild()`, every stamp-time call from `core/memory_edges.py:588` does nothing. The
earlier statement "registered on every fragment_context stamp" (F-3235, D-0636, this job's briefing) is therefore too
generous: it is a no-op from both ends. Worse, the HUD World tab shows "memory_tuples" computed as
`SELECT COUNT(*) FROM fragment_context` (`hud/server.py:449`): the one instrument that appears to say the index is
populated is reading the database, not the index. That is the project's "write-only is the number one failure" pattern
with a green light on it.

### 3b. The design numbers have been outrun by the data (MEASURED today)

| | Design (08-16/17, 7,647 rows) | Today (111,143 rows) |
|---|---|---|
| Rebuild | 45-60 ms | 4,192 ms |
| Whole-chord query | 5.6-15 ms | 425 ms median |
| RAM | "tiny" | 149.6 MB (tracemalloc) |

`query()` is a full scan over a dict of Python sets, so it was never an index in the database sense, only a scorer that
scales linearly. A "pre-filter" that costs 425 ms placed in front of a 100-200 ms SQL path is a net loss. A true
inverted index (tag to id list) would fix the speed for rare tags and not for `place:study` (42,026 rows), and the one
place a rare-tag candidate set matters is the thing nobody has asked for.

### 3c. "Find the other moments like now" exists four times

1. couriers (`context_echo`, `sound_echo`): single column, random pick.
2. felt_recall: single trigger plus an unweighted count of four other coordinates.
3. theta_shadow: `tod`/`season` window with its own index and its own rank rule.
4. the ghost MemoryIndex: all tags, rarity weighted, never called.

They disagree on what "the same" means (the ghost index bands warmth and tide into thirds; felt_recall ignores both;
couriers ignore everything but one key). I found no incident caused by this, so it is a divergence risk, not a defect.

### 3d. "Are these two texts the same?" exists at least eleven times, and two sites re-learned the same lesson

MEASURED by `grep`: eleven private tokenizer functions (`_tokens` in `book_residue`, `common_ground_shadow`,
`guidance_learning`, `life_shore`, `memory_levels`, `moment`, `object_graph`, `reentry`; `_toks` in `frontier`,
`retraction_ledger`, `wager_curiosity`), more `_words`/stem helpers, and inline Jaccard in `deliberation._too_similar`
(0.88) and `lane2._wonder_repeat_check` (0.5). Thresholds seen: 0.5, 0.55, 0.88, and an overlap coefficient in
`guidance_learning` (`core/guidance_learning.py:239`). Which of the eleven are used as near-duplicate tests rather than
for other purposes I did not audit (INFERRED: at least five are).

The telling part is the failure record. Token overlap does not merge LLM paraphrases:

- `core/frontier.py:158-169`: 191 of 340 open questions were "mottainai" variants; fixed in D-0486 with an embedding
  merge, live since D-0495.
- `core/commitment_ledger.py:605-625`: Jaccard reaffirm fired 0.000 for 82 samples in a row after the 08-20 gating; fixed
  with an embedding cosine, Jaccard kept as the fallback.
- D-0429: the Lane 2 wonder field's lexical anti-repeat reads 0.59 distinct share.

The original ghost pair was a ladder: exact hash, then 2-gram fuzzy signature, then embedding/LLM. Nascence ported only
the tag leg (F-3235: there is no 2-gram code in `ghost_tuples.py`, and the geometry plan's "SHA-256 + 2-gram, live"
claims at `docs/staged/geometry_tuple_index.md` lines 399 and 786 overstate it). The need the missing legs were for has
since appeared in many places and each place built its own rung. This is the one place the review found "one mechanism built
several times". The function worth transferring (not the mechanism) is "ask whether this text is already known, cheapest
test first, with one measured threshold per tier", and it is a candidate for one shared helper only if a replay shows the
sites actually disagree on real pairs (U5).

### 3e. Other areas of improvement the review turned up (MEASURED)

- **Couriers block the event loop for about a second.** `_substrate_loop` (`core/orchestrator.py:3250`) runs
  `context_echo() or sound_echo()` and `felt_recall.on_substrate_tick` directly in the `async def` body. A courier fire
  costs about 1.17 s of loop time (about 9 a day), and each felt_recall edge 0.1-0.85 s (about 180 a day). The sibling
  `wander.kick` was already moved to a worker thread for the same reason (J-1909 comment at line 3272). Roughly 2-3
  minutes of event-loop stall a day; small but entirely avoidable.
- **The courier delivery log cannot be joined to what was delivered.** Delivered rows carry `route`, `context`,
  `freight_age`, `cargo_type`; only the would-have branch logs `fragment_id` (`core/couriers.py:163` vs `:176`). 746
  deliveries, no way to ask what Du was given or whether he took it up. Any test of chord_echo's value in the live path
  needs that field first.
- **Coverage.** `fragment_context` covers 63.8 percent of memories (F-3234), and all four coordinate matchers inherit it.
  action memories are 0.0 percent.
- **A latent bug, unreachable today.** `felt_recall._build_prior` line 450 returns a 3-tuple (`return None, 0, None`) where
  every other path returns 4. Only reachable when `SOUND_COORD_MATCH` is True and every candidate is dropped; the flag is
  False. Worth fixing before the flag is flipped. (Noted, not filed as its own job.)
- **A suggestion for chord_echo itself** if it is ever built: the couriers' `ORDER BY RANDOM()` is a variety guard. A
  deterministic best-match would echo the same memory every time the same storm recurs. Sample from the top-k and keep a
  do-not-repeat ledger, or the courier becomes a stuck record.

## 4. Pre-registered tests and stop conditions

Laws applied: the world answers and never leads (an echo is his own memory, provenance-stamped, never an instruction);
base systems additive only; transfer the function, not the mechanism; no system acts later on its own (no test below flips
anything live; each stage ends in a founder read); the judge is never the writer.

### U1. chord_echo (couriers A+D) versus the current single-key rule

Not a speed question. Question: does whole-chord matching surface moments that are more like the present one, by a measure
the matcher did not use?

Stage 1 (offline, read-only, free). Sample 3,000 experienced moments (`source LIKE 'experienced:%'`, valence not null).
For each, candidates are other moments at least 7 days away (the F-3368 clock lesson: no matching on near time). Arms:
(a) single-key random (the couriers' rule: same weather for A, same sound key for D), (b) chord top-24 mean, rarity
weighted (the ghost scorer), (c) the 24 nearest in time, (d) shuffle-null (tags permuted across rows, 20 replicates),
(e) global mean. Outcome, decoupled from matching: the held-out moment's own stored valence and arousal (never used in
tag matching). Pass bar, fixed now: chord MAE is lower than arm (a) by at least 0.02 with a bootstrap 95 percent CI that
excludes 0, AND lower than arm (c), AND better than the null at z of at least 3, for both valence and arousal.
Stop: any miss, retire chord_echo as a build, and the memory namespace per D-0669 (section 6).

EXPLORATORY probe, run today, NOT pre-registered, labelled as such (3,000 sampled moments, gap at least 1 day, seed
20261105, `scratchpad/probe_valence_J-3247.py`): MAE of predicting a moment's own valence: global mean 0.288, same-weather
0.289, chord top-24 **0.325 (worse than doing nothing)**, nearest-in-time 0.313. Correlation with truth: chord +0.09 against
a shuffled-tag null of -0.02, nearest-in-time +0.23 (the clock again). The chord has a faint real signal and it does not
beat the single-key rule or the clock. This used a 1-day gap, looser than Stage 1's 7 days, so treat it as direction only.
That matches J-2535 and J-2638 (coordinates are labels for recall) and means I expect Stage 1 to fail.

Stage 2 (only if Stage 1 passes; needs the courier fragment_id log first). Decoupled judge panel (a different family
from whatever writes), 100 blind, order-randomised pairs: the present moment in plain words plus one memory text from
arm (a) or arm (b); the judge scores "does this memory describe a situation like the present one" 0 to 2. Pass: chord
mean exceeds single-key by at least 0.3 with CI excluding 0. Stop: otherwise retire.

Stage 3 (only if Stage 2 passes; shadow, 14 days). On each courier fire log the chord pick beside the actual random pick
(fragment ids, no delivery change), then read uptake: cosine of the next three thoughts to each pick, against a matched
unpicked control. Stop: no uptake gap, retire. A founder read ends each stage; nothing flips by itself.

### U2. Pre-filter in front of felt_recall and J-2535's pool

Not worth testing as a ghost pre-filter. The only open item is the equivalence of a SQL-side score in felt_recall, which
returned identical top-24 id lists in 3 of 3 triggers today. Pre-registered check if ever built: identical top-24 ids on
every fired edge in `felt_recall_shadow.jsonl` (about 7,000 edges); stop on a single mismatch. Do not build unless
felt_recall goes live and the edge cost matters.

### U3. Exact-duplicate lookup (the real pre-filter)

Already pre-registered in J-3266/D-0657: the hashed lookup agrees with the full lookup on every row for at least a week
and 5,000 calls, with the shadow log running beside it; stop and fall back on any disagreement or if `store_fragment`
gets slower than the current full lookup. Nothing to add except the `ghost_hash` caution above.

### U4. Shared near-duplicate helper (section 3d)

Offline replay, read-only. Take 2,000 real pairs (frontier variants and their parents, wonder rows, commitment
restatements, deliberation integrate pairs). Apply each site's own rule and a single three-tier helper (exact normalised
text, 3-gram Jaccard, embedding cosine). Report per site: agreement with the site's current verdict, and agreement with a
decoupled judge panel on a 150-pair stratified sample. Pass for extracting a shared helper: sites disagree with the
judge on at least 10 percent of pairs where one tier would be right, and no site's current behaviour regresses.
Stop: if sites already agree with the judge at 90 percent or more, leave them alone and log the eleven tokenizers as a
known duplication with no cost.

## 5. Recommendation per use

| Use | Verdict | Why |
|---|---|---|
| Memory index as a felt_recall / J-2535 pre-filter | **Leave with a note** (do not wire) | 425 ms scan versus a 100-200 ms path; coordinates are labels for recall; hides 36 percent of memories. |
| chord_echo (couriers A+D) | **Leave, run U1 stage 1 first** | Exploratory probe says whole-chord does not beat single-key or the clock. Needs the delivered-row `fragment_id` before any live read. |
| Memory index itself | **Leave now, retire if U1 fails** | D-0636 says not to retire yet; the defeater is "retire the memory namespace if no consumer survives". Keep `ghost_hash` and the world index regardless. |
| Exact-dedup lookup | **Wire** (J-3266, already queued) | Original ghost-hash leg; fixes a roughly 6 minute a day cost with identical results. |
| Evidence hand, associative recall, Transport Manager, item graduation, frontier | **Leave** | No scan to avoid or already O(1). |
| Shared near-dup helper | **Analyse first (U4)** | Strongest "built several times" finding; extract only if a replay shows disagreement. |
| Honesty fixes (HUD label, doc overclaims) | **Do now (small)** | An instrument that reads green while the thing is inert. |

## 6. What was filed

Findings (session J-3247, plan geometry_tuple_index): F-3901 (memory index inert, stale numbers), F-3897 (why chord_echo
was never built), F-3898 (exploratory valence probe), F-3899 (near-duplicate tests built eleven times), F-3900 (courier and
felt_recall event-loop cost, delivered-row log gap).

Follow-up jobs, all spawned from D-0636:

| Job | Kind | What |
|---|---|---|
| J-3304 | build | Couriers: log `fragment_id` and candidate count on delivered echo rows (precondition for any live read). |
| J-3305 | build | Move couriers and felt_recall database work off the asyncio event loop; fix felt_recall's 3-tuple return. |
| J-3306 | doc | HUD relabel, `ghost_tuples` docstring honesty, geometry-plan overclaims, pointer from the P0 doc. |
| J-3307 | lab | Pre-registered chord_echo replay (U1 stage 1). Expected to fail. |
| J-3308 | analysis | Near-duplicate test inventory and replay against a decoupled judge (U4). |

Already queued and unchanged: J-3266 (D-0657, hashed exact-dedup lookup). Founder question: D-0669 (may a failed U1
replay retire the memory namespace without another call; recommended yes). D-0636 is not ruled over.

Scratch scripts (kept under the job id, all read-only): `bench_J-3247.py`, `probe_valence_J-3247.py`,
`sqlscore_J-3247.py`, `spawn_J-3247.py` in the session scratchpad.
