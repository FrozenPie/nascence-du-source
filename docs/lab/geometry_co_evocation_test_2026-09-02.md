# The co-evocation test — cross-space edge layer, third instrument (J-0463, D-0111)

**Script:** `scripts/geometry_co_evocation_test.py` (read-only; reads `data/co_recall_ledger.jsonl`
and, via a read-only `mode=ro` SQLite connection, `fragment_context` + `memory_fragments.embedding`
from `data/memory/nascence.db`; no store written except this script's own report). **Raw output:**
`docs/lab/geometry_co_evocation_test_1788312926.json`. **Command run:**
`python scripts/geometry_co_evocation_test.py --n_perm 200 --seed 42` (2026-09-02).

## Why this is a genuinely different instrument, not a third re-read (D-0111's own bar)

| | F-0501 (marginal reach) | F-0635 (§5.3 realness test) | **This test (co-evocation)** |
|---|---|---|---|
| Question shape | set-overlap: does geometry top-K reach outside a widened text top-K? | predictive accuracy: does geometry-kNN beat text-kNN on an outcome? | cohesion: do REAL co-recalled fragment groups cohere in geometric context more than chance? |
| Comparator | text search coverage | text-distance kNN (horse race) | a permutation null of random groups (primary) + a text-similarity-matched null (confound check) — text is a parallel read, not the competitor |
| Data source | `data/geometry_tuples.jsonl` (per-thought idle snapshots) | same, joined to `train_state_log`/`co_recall_ledger` outcomes | `fragment_context` (per-FRAGMENT context at creation time) + `memory_fragments.embedding`, joined to real co-recall EVENTS |
| Evidence type | constructed kNN benchmark | constructed kNN benchmark | **real production behaviour** — groups Du's own recall mechanism actually pulled together |

§5.3's own wording names three admissible outcome measures — "co-evocation, co-recall, felt
response." F-0635 tested co-recall (`developed`) and felt response (`restate_sim`); co-evocation
itself — do the things recalled TOGETHER actually share real structure — was never operationalised
until now.

## The construct and the join

**Co-evocation event** = one row of `data/co_recall_ledger.jsonl` with `n_ids >= 2`: a real cognitive
step where Du's own recall mechanism (`core/associative_recall.recall_fragments` → `recall_trail`,
confirmed by direct read: pure text-embedding similarity + activation dynamics on the query vector,
**not** state/geometry-conditioned) pulled multiple stored fragments into the same step.

**Context per fragment** = `fragment_context` (a real per-fragment table populated at fragment
creation time — distinct from `geometry_tuples.jsonl`'s per-thought log): `place`, `weather`, `fire`,
`light_band`, `standpoint`, `cat_at`, `held` (set), `sounds` (set), `affect_quadrant` (binned from
`valence`/`arousal` at 0.5, same convention as `core/mapping_census.extract_regions`) — chosen from a
coverage audit run before writing the script (place/weather/level ~100%, fire 68%, light_band 53%,
standpoint 70%, cat_at 9%, held 24%).

`coherence(a,b)` = fraction of the fields BOTH fragments have populated on which they AGREE (fields
where either is null are excluded from the denominator, not scored as disagreement). Undefined pairs
(< 2 shared-populated fields) are skipped.

**Eligible pool:** 22,933 fragments with both `fragment_context` and a stored embedding (of 64,447
total memory fragments). **4,120 of 12,021** `n_ids>=2` co-recall events had ALL member fragments in
the eligible pool (the strict "all-covered" sample used throughout, to avoid partial-coverage bias).

## Pre-registered design (written before results were read — see script docstring, full text)

1. **Primary test:** permutation null (200 permutations, mirroring `core.mapping_census.
   state_conditioning`'s existing methodology) — for each real event, draw a same-size random group
   from the eligible pool; compare observed mean geometric coherence in REAL groups to the null
   distribution → z-score + one-sided permutation p.
2. **Robustness split:** re-run on NEAR-TERM (<1 day fragment-span) vs LONG-RANGE (≥1 day) event
   subsets — the same "does this survive being about something other than recency" guard the plan's
   own `book`/time-confound flag already established as this project's honesty bar.
3. **Verdict rule, fixed before running:** PASS iff geometric z≥2.0 (p<0.05) on BOTH the full sample
   AND the long-range subset specifically (not recency-explainable); MIXED iff full passes but
   long-range doesn't; FAIL iff the full sample itself isn't significant.
4. **Confound guard (added before the run, diagnostic only — does not gate the verdict):**
   text-similarity-matched control. For every real pair (a,b), find a substitute b* from a random
   50-candidate subsample whose text-cosine to a is closest to the real pair's own text-cosine to a,
   then compare `coherence(a,b)` [real] to `coherence(a,b*)` [text-matched substitute], paired.

## Results

**Primary permutation test** (n=4,120 events):
- Full sample: observed mean geometric coherence 0.4655 vs null mean 0.2756 (std 0.0034) — **z=55.31,
  p≈0** (200/200 permutations below observed).
- Near-term (<1 day, n=3,093): observed 0.5081 vs null 0.2754 — **z=58.16**.
- Long-range (≥1 day, n=1,027 — fragments recalled together despite being FORMED in different life
  periods, median span 0.30 days / p90 2.1 days overall): observed 0.3374 vs null 0.2755 — **z=10.00,
  p≈0**. Weaker than near-term (expected — less shared ambient state) but still 10 standard deviations
  above chance. **Not recency-explainable.**
- Text-similarity coherence (context, not gating): full z=162.47, long-range z=95.04 — text cohesion
  is present and stronger, as expected since recall is itself text-driven; this arm does not compete
  with the geometry arm here, it contextualizes it.

**Confound guard** (paired, text-similarity-matched):
- Full sample (n=7,730 pairs): real-pair coherence 0.4685 vs text-matched-substitute coherence 0.2865
  — real pairs win on 4,718/6,625 decided pairs, sign-test p≈0. **`geom_adds_beyond_text = true`.**
- Long-range only (n=2,801 pairs): real 0.3778 vs matched-substitute 0.2635 — real wins 1,536/2,328,
  p≈0. **Still true on the harder subset.**

**Verdict: PASS**, per the pre-registered rule, on both required legs (full sample AND long-range),
and the confound guard the plan's own honesty conventions call for holds too — the coherence is not
explained away by recency, and it survives holding text-similarity level fixed.

## Honest limitations for the founder-read (this module does not grade its own output, §7)

- **A residual "shared query" pathway is not fully ruled out.** `recall_trail`'s query vector is the
  embedding of the CURRENT thought, which itself may encode state-flavoured language (a thought about
  the shore is more likely while AT the shore). Two fragments could each be individually text-similar
  to that query for state-flavoured reasons without being text-similar to EACH OTHER (my pairwise
  text-matched control checks a-vs-b text similarity, not each fragment's relationship to the shared
  query) — a subtler version of the confound this section's guard was built to catch, not fully closed
  by it. Neither prior instrument (F-0501, F-0635) controlled for this at all, so this is not a new
  weakness relative to the existing evidence base, but it is real and worth a founder eye.
- **This measures a correlational structure in real behaviour, not the specific P1/P2 mechanism.**
  It shows co-recalled fragments cohere geometrically beyond chance and beyond a text-similarity
  match — evidence the underlying construct (episodes sharing real-world context get recalled
  together) has ecological reality in Du's actual cognition today, using ONLY the text-embedding
  recall path that already exists. It does not by itself demonstrate that BUILDING an explicit
  cross-space edge layer (P1/P2) would improve retrieval beyond what text-embedding recall already
  achieves on its own — that remains what F-0501/F-0635 tested and found negative. The three
  instruments together read as: **the coherence exists in the world Du experiences (this test); text
  embedding alone already captures enough of it that an explicit geometry-distance signal doesn't
  additionally out-predict text (F-0635) or reach meaningfully beyond a widened text search on
  average (F-0501, 50/50 on hand-grade)** — three different lenses on the same underlying fact
  rather than three contradictory reads.

Per D-0111's defeater ("a clear pass reopens P1/P2 investment; another clear/mixed fail retires the
cross-space edge layer for real, no further re-tests"): this is a clear pass on ITS OWN pre-registered
terms. A new founder decision is opened (not ruled — CLAUDE.md's own discipline) to read all three
instruments together, including the honest tension in the paragraph above, rather than mechanically
applying "one pass = reopen" without that context reaching the founder.
