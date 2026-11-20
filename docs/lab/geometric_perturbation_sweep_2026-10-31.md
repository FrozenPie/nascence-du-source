# Geometric perturbation sweep over the experienced tuple (J-2535) — 2026-10-31

Status: **RUN COMPLETE 2026-10-31.** Sections 1-7 below are the PRE-REGISTRATION SHEET, committed as c6faedd7 BEFORE
the script was run and not edited since. The plain verdict and all results follow the sheet. Job J-2535, plan `cognitive_geometry`, from idea I-0122 /
thought T-0107 (GPT tuple dialogue, `docs/reviews/tuple_substrate_reply_to_gpt_2026-10-30.md`).

## 1. The question

Does the experienced-tuple geometry do work beyond labelling? `core/euclidean_recall.py` names its own
operational test: "whether the same query under different states surfaces meaningfully different (and
sensible) memories". Nobody ran it as a systematic sweep. This lab runs it and extends it to the ten
experienced coordinates in `fragment_context`: **place, weather, warmth, fire, cat_at, valence, arousal,
tod, season, daylight**.

Two readings of "sensitivity", kept apart on purpose:

* **Distance sensitivity** (Part S) — does moving one coordinate move the top-k? Cheap to get and, on its own,
  close to trivial: any feature with nonzero weight moves a ranking. It is only interesting against its shuffle-null.
* **Meaningful sensitivity** (Part M) — is the moved/unmoved set *more appropriate* by a measure that does not
  use an LLM and is not the ranker's own score? This is the realness test (`cognitive_geometry.md` sec 5.3).

## 2. The realness bar (sec 5.3, quoted into the sheet so it cannot be reworded after the fact)

> A space is real iff its internal distances predict something (co-evocation, co-recall, felt response)
> BETTER than MiniLM text-distance on the same items. Candidate fails -> it's text wearing a costume.

Operationalised here, with TWO bars fixed in advance:

* **STRICT bar (sec 5.3 as written):** coordinate i alone, as a distance, must beat MiniLM cosine alone at
  telling a co-recalled partner from an age/origin-matched non-partner (win-rate W_i > W_sem, paired bootstrap
  95% CI over queries excludes 0).
* **INCREMENTAL bar (the question that matters if text is the base):** adding coordinate i to the existing
  6-feature euclidean ranker must raise the partner win-rate (lift_i > 0) by more than its own shuffle-null
  (z >= 3), AND moving the query's coordinate *away from its true value* must lower the win-rate by more than
  null (harm_i > 0, z >= 3). Both required.

## 3. Verdict rules (fixed now)

Per dimension, from Part M, unconditional and conditioned (place held fixed; tod held fixed):

* **coordinate** = incremental bar passed unconditionally (and, separately flagged, STRICT bar passed or not).
* **conditional** = incremental bar fails unconditionally but passes (z >= 3, both parts) in the place-held-fixed
  or tod-held-fixed condition.
* **label** = incremental bar fails in all three conditions. A dimension whose perturbation effect is not above
  its own shuffle-null is a label, not a coordinate.
* **time proxy** (an overlay flag, not a fourth verdict) = the dimension is a deterministic function of the
  fragment timestamp (tod, season, daylight are written from the fragment's own timestamp, PHASE field
  2026-09-27; season is a monotone clock over this window). A pass for those is reported as "coordinate, but
  possibly only a clock" and checked by the absolute-time control in sec 7.

## 4. Pre-registered predictions (written before any number exists)

| # | Prediction | Basis |
|---|---|---|
| P1 | STRICT bar: **0 of 10** dimensions beat MiniLM alone | story/language/memory already failed as spaces; co-recall is *selected by* semantic recall so text is favoured by construction (sec 6 caveat) |
| P2 | Part S distance sensitivity is above shuffle-null for most dims (z>0) simply because weight>0; **not** informative alone | any weighted feature moves a ranking |
| P3 | INCREMENTAL bar passes for **place** and at most 2-3 more (likely valence, arousal — they share a source with the emotion_embedding feature — and tod); **cat_at, fire, daylight, warmth, weather = label** (sparse / mostly null / place-determined) | place structure is real; sparse coordinates have no support |
| P4 | At least one of tod/season passes, and the absolute-time control shows part of it is a clock | PHASE is derived from timestamp |
| P5 | Under place-held-fixed, weather/warmth/fire change materially (some may flip label -> conditional) | GPT's point: dims may matter only jointly |
| P6 | Expected overall: the cross-space hypothesis lineage (failed 3 of 4 realness tests, F-0651 the one pass) predicts **few real coordinates**; a result of "mostly labels" is the expected one, not a surprise | `cognitive_geometry.md` status header |

Expected failure modes of the lab itself, stated in advance: (a) co-recall pairs are selected by an
embedding-driven recall, so MiniLM is advantaged; (b) coordinates are strongly correlated (place implies
fire/cat_at/standpoint), so single-coordinate perturbations create physically impossible tuples
(fire=burning on the shore); (c) the valence coordinate and the emotion_embedding feature share one upstream
mood, so valence has a built-in overlap with `affect_match`.

## 5. Design

**Cohort** (every filter fixed in advance, from `core/geometry_census.py` header caveats):
fragments with a `fragment_context` row whose `source LIKE 'experienced:%'` (the `census_world:*` window-joined
rows are EXCLUDED pending the J-2536 join audit), `embedding IS NOT NULL`, `cold=0`, `origin != 'system_note'`,
and `timestamp >= 1787957042.9` (2026-08-29 10:44 NZST, the affect-staleness boundary; this also clears the
Day-1 null-place rows and the pre-2026-08-21 rain/wind place-flag bug). Store opened `?mode=ro`; ledgers
read-only; nothing written outside `docs/lab/`, `scripts/`, and the scratch dir. Isolated via
`lab_env.isolate(db="empty")` so a stray store write cannot reach the live DB; live-file size+mtime canary
checked before and after.

**Ranker.** The 6 features and `distance()` are `euclidean_recall.featurize/distance` unchanged (verified by an
equality test of my vectorised ranker against `euclidean_recall.rank()` on the 6-feature subset). Need point
`[1,.5,1,1,.5,.8]`, state weights `w_state=[1,.5,.3+1.2*min(1,|v|*2),.4,.2,.2]` with v = the query's own valence
(exactly the shadow's). EXTENSION: ten context-match features, need = 1, weight **0.15 each** (primary; 0.05 and
0.5 run as robustness on Part S only). Match: categorical = 1 if equal else 0 (null is its own value "none");
numeric = Gaussian kernel exp(-0.5 (dq/sd)^2) with sd = cohort SD (tod: circular distance, sd 0.25). The query's
felt vector is its own `emotion_embedding`; need_emb is its own embedding; `now` = the query's timestamp.

**Perturbations** (one coordinate at a time, P' = P + delta e_i): categorical = swap to each other value with
>= 200 cohort rows plus "none"; numeric = +/- 1 cohort SD (tod +/- 0.25 circular).

**Part S — sensitivity sweep (spec steps 1,2,4,5).** 300 queries stratified by origin x place (24 cells, ~12
each; origins = the six largest in the cohort). Pool = the 600 most recent cohort fragments before the query
(the shadow's own max_candidates). For each (query, perturbation): Jaccard of top-8 before/after; mean absolute
rank shift of the base top-8 members; which coordinates of newly surfaced vs dropped fragments moved
(standardised mean difference, reported as the share carried by the perturbed coordinate); popularity delta
(mean log1p co-recall read-count of surfaced minus dropped) and reuse delta (children in memory_links).
Shuffle-null: R=20 replicates, each permuting that coordinate across the pool's fragments (query value kept);
aggregate per replicate -> z = (observed - null mean)/null SD.

**Part M — meaningful sensitivity (spec steps 3,4,5).** Queries = cohort fragments that appear in
co_recall_ledger rows (non-shadow, n_ids >= 2) with >= 1 cohort partner; up to 600, stratified by ledger source
group (monologue / wandering / other). Positives = up to 20 co-recall partners. Each positive gets 10 matched
negatives: same origin, same sign and same log10(|age|+1d) bin (width 0.15) relative to the query. Win-rate =
P(positive scores closer than its matched negatives), ties 0.5. Quantities per dimension i: W_i (coordinate
alone), W_sem (MiniLM cosine alone), W_6 (6-feature ranker), lift_i = W_(6+i) - W_6, harm_i = W_(6+i)(P) -
W_(6+i)(P'). Shuffle-null R=20: permute coordinate i among the pool (positives+negatives of that query).
Bootstrap 95% CI across queries. **Conditional:** repeat with the pool restricted to the query's own place, and
again to |tod diff| <= 0.125 (circular).

**Optional decoupled-judge pass on a 30-pair subset:** NOT run (needs a model; Du's hot model must not be
loaded). Recorded as a gap, not skipped silently.

## 6. Caveats carried into the reading

* Co-recall membership is *selected by embedding-driven recall* — W_sem is inflated by construction. The strict
  bar is therefore the hard one for context; the incremental bar is the fair one.
* "Appropriate" here = co-recalled with the query by a live generative step, not "good". It is the only
  non-LLM, non-self-scored independent measure that exists at scale.
* Single-coordinate perturbation of a correlated tuple builds impossible tuples; the place-held-fixed condition
  partially controls this.
* Wandering dominates the ledger (59k of 112k rows); source-group strata are reported separately.

## 7. Controls

* Absolute-time control: for tod/season/daylight, re-run Part M with negatives additionally matched on
  |ts_pos - ts_neg| < 1 day to the positive (so a clock cannot separate them). Reported as "clock-controlled".
* Equality test of the vectorised ranker against `euclidean_recall.rank()`.
* Live-store canary: size+mtime of `data/memory/nascence.db`, `co_recall_ledger.jsonl` recorded before/after.

---
## PLAIN VERDICT (read this first)

**All ten experienced coordinates come out as LABELS under the bar the sheet fixed in advance. None is a coordinate; none is even a conditional one (place-held-fixed and tod-held-fixed both flip nothing).** The strict sec 5.3 bar (beat MiniLM text-distance alone) is failed by 10 of 10, as predicted: MiniLM alone separates a co-recalled partner from an origin- and age-matched non-partner 90.5% of the time; the best single experienced coordinate manages 65.6% (season, and that one is mostly a clock, see below).

| dim | verdict | one-line reason |
|---|---|---|
| place | **label** | standalone win-rate 0.541 (chance 0.5); adding it to the 6-feature ranker lowers win-rate, never raises it; no conditional rescue |
| weather | **label** | weakly better than its own shuffle-null (lift z +4.6) but lift is negative: costs more than it pays |
| warmth | **label** | no incremental lift (z +2.0, lift negative) |
| fire | **label** | likewise (lift z +6.3 vs null, lift negative); fire perturbation does surface more-read and more-reused fragments than null (popularity drift, not shown to be appropriateness) |
| cat_at | **label** | indistinguishable from null on every measure; ~96% of a recent pool shares one value (none) |
| valence | **label (closest to passing: `partial`)** | lift z +3.8 and harm z +3.1 both clear null, but lift is -0.0105 absolute and harm is +0.0073; fails when the weight is cut to 0.01-0.06 as well |
| arousal | **label** | within-pool SD barely varies (kernel SD 0.032); nothing above null |
| tod | **label (time-proxy)** | standalone 0.630 but pure |dt| alone gets 0.650 in the same design; see clock diagnostic |
| season | **label (time-proxy)** | standalone 0.656 vs pure |dt| 0.650: it is a clock; the recent pool's within-pool SD is 0.02 of cohort SD |
| daylight | **label** (`partial` under clock control) | the only dimension with a same-sign, above-null lift AND harm in the clock-controlled run (lift z +5.4, harm z +4.2) but both effect sizes are 0.002-0.004 and lift is still negative at wc=0.15. The only dimension to watch: at wc=0.06 (post-hoc) it has lift +0.0010 (z +4.8) and harm +0.0035 (z +4.6), though the lift CI still includes 0, and its tight-matched standalone win-rate is exactly chance |

**What "label" means here, precisely:** adding that coordinate to the existing text-dominated ranker does not improve its ability to
recover what the live generative steps actually co-recalled, beyond what a shuffled version of the same coordinate would do. It
does **not** mean the coordinate carries no information: standalone, every coordinate except cat_at/daylight is a little above
chance, and place, fire, tod, season keep a small residual (0.520, 0.522, 0.557, 0.541) even after tight age-matching removes
most of the time-proximity effect. Co-recall is **selected by embedding-driven recall**, so this ledger structurally
rewards text distance and punishes context-keyed divergence: the experiment cannot see value that context provides by
surfacing a *different but good* memory. That blind spot is exactly what the optional decoupled-judge pass would have
addressed; it was not run (a model would have to be loaded; Du is down and servers must not be started), and is spawned as follow-up work.

**Part S (does moving a coordinate move the top-8?):** yes, all ten move it, but **by LESS than a structure-free coordinate would** (Jaccard z +2.7 to +48.7 on all 10; mean rank shift below null on 9 of 10, cat_at n.s.). Real coordinates are aligned with what the text/recency features already rank
high, so the dominant top-k survives the swap. The sheet's prediction P2 was ambiguously worded ("z>0"); under its intended meaning (movement at least as large as null) it is **contradicted**.

**This does not resolve D-0083 / D-0088.** Those holds are about the cross-space edge layer; this lab tests the experienced `fragment_context` coordinates inside the euclidean ranker. It is evidence on the neighbouring question (does the tuple geometry do work beyond labelling) and says: not in this ranker, against this ledger, at present.

## RESULTS (run 2026-10-31; script `scripts/lab_geometric_perturbation_sweep.py`, seed 20261031)

### 0. Run facts

* Cohort: **59,187** fragments (experienced fragment_context join, embedded, non-cold, ts >= 1787957042.9). Co-recall ledger: 92,397 non-shadow rows read.
* Cohort origin mix (top): inner_thought 32,835, reading 16,620, active_imagination 2,416, study 2,045, gist 1,208, research 1,154.
* Fragments with co-recall partners in the cohort, by ledger source group: monologue 1,399, wandering 15,306, other 1,944.
* Ranker equality test (my vectorised 6-feature ranking vs `euclidean_recall.rank()` on real rows): **5/5** top-8 sets identical.
* Categorical values kept (>=200 rows; '' = none): place: ['study', 'shore', 'garden', 'wood']; weather: ['clear', 'high cloud', 'overcast', 'drizzle', 'steady rain', 'wind and rain']; fire: ['', 'out', 'burning', 'embers']; cat_at: ['', 'garden', 'shore']; daylight: ['', 'day', 'night', 'dawn', 'dusk']. Numeric kernel SDs: warmth 0.165, valence 0.343, arousal 0.032, tod 0.250, season 0.045.
* Part S: 276 queries used (unconditional), place-fixed 275, tod-fixed 276. Part M units: unconditional 738, place-fixed 532, tod-fixed 510, clock-controlled 733.
* Baseline win-rates in Part M (unconditional): **MiniLM cosine alone W_sem = 0.905**; 6-feature euclidean ranker W_6 = 0.902 (1.0 = always tells a co-recalled partner from its matched non-partner; 0.5 = chance).
* Live-store canary (size, mtime before -> after): `nascence.db` UNCHANGED; `co_recall_ledger.jsonl` UNCHANGED. Runtime 130 s.

### 1. Part S -- distance sensitivity (does moving one coordinate move the top-8?)

Jaccard = overlap of top-8 before/after the perturbation (1.0 = nothing moved). z is against the shuffle-null (coordinate permuted across the pool, 20 replicates). **Negative jac z = the real coordinate moves the top-k MORE than a structure-free one; positive = LESS** (the real coordinate is already aligned with what the other features rank high, so changing it displaces less). Shift = mean |rank change| of the base top-8. Share = fraction of the standardised movement among newly-surfaced-vs-dropped fragments carried by the perturbed coordinate itself. pop/reuse = independent-measure deltas of newly surfaced minus dropped (mean log1p co-recall reads / log1p children in memory_links), with z against null.

| dim | n pert | Jaccard | null Jac | z | mean rank shift | null shift | z | share on own coord | pop delta (z) | reuse delta (z) | most-moved coords in newly surfaced |
|---|---|---|---|---|---|---|---|---|---|---|---|
| place | 828 | 0.534 | 0.316 | +39.6 | 9.66 | 14.48 | -28.1 | 0.24 | 0.090 (+1.9) | 0.068 (+3.1) | place(306), warmth(59), salience(40) |
| weather | 1380 | 0.750 | 0.650 | +17.9 | 3.29 | 4.82 | -15.5 | 0.09 | -0.025 (-1.5) | -0.030 (-1.6) | weather(135), recency(89), place(80) |
| warmth | 552 | 0.868 | 0.736 | +27.8 | 0.77 | 1.77 | -34.5 | 0.16 | 0.028 (+0.7) | 0.093 (+4.7) | place(52), warmth(44), weather(29) |
| fire | 828 | 0.766 | 0.510 | +48.7 | 2.20 | 5.79 | -30.0 | 0.16 | 0.199 (+5.2) | 0.358 (+14.2) | fire(123), place(75), salience(60) |
| cat_at | 552 | 0.887 | 0.848 | +8.4 | 0.90 | 0.87 | +0.5 | 0.34 | -0.086 (-1.5) | -0.020 (-0.7) | cat_at(94), semantic_sim(9), recency(7) |
| valence | 552 | 0.732 | 0.664 | +11.6 | 1.77 | 2.56 | -12.9 | 0.26 | -0.055 (-1.5) | -0.039 (-1.7) | valence(155), weather(38), place(35) |
| arousal | 552 | 0.809 | 0.769 | +12.0 | 1.32 | 1.63 | -7.1 | 0.26 | -0.035 (-0.7) | 0.003 (+0.0) | arousal(116), place(28), valence(24) |
| tod | 552 | 0.852 | 0.758 | +29.8 | 0.82 | 1.54 | -35.5 | 0.18 | 0.023 (+0.9) | 0.003 (-0.1) | tod(82), weather(31), place(26) |
| season | 552 | 0.994 | 0.990 | +2.7 | 0.04 | 0.06 | -5.4 | 0.19 | 0.342 (+1.9) | -0.158 (-1.1) | weather(3), season(3), tod(2) |
| daylight | 1104 | 0.891 | 0.825 | +18.3 | 1.76 | 2.70 | -9.8 | 0.10 | -0.218 (-4.2) | 0.010 (-0.8) | daylight(48), place(37), weather(32) |

Conditional (Jaccard, z vs null) -- place held fixed / tod held fixed (pool = the 600 most recent cohort fragments meeting the condition); robustness to the context weight (primary 0.15):

| dim | uncond Jac (z) | place-fixed Jac (z) | tod-fixed Jac (z) | wc=0.05 Jac (z) | wc=0.5 Jac (z) |
|---|---|---|---|---|---|
| place | 0.534 (+39.6) | -- | 0.527 (+56.9) | 0.670 (+29.1) | 0.446 (+80.9) |
| weather | 0.750 (+17.9) | 0.606 (+11.7) | 0.673 (+17.0) | 0.814 (+6.5) | 0.723 (+19.0) |
| warmth | 0.868 (+27.8) | 0.838 (+29.1) | 0.881 (+36.2) | 0.897 (+7.6) | 0.893 (+58.3) |
| fire | 0.766 (+48.7) | 0.914 (+23.1) | 0.768 (+37.5) | 0.775 (+12.3) | 0.850 (+63.8) |
| cat_at | 0.887 (+8.4) | 0.901 (+7.1) | 0.896 (+7.7) | 0.933 (+2.6) | 0.858 (+14.9) |
| valence | 0.732 (+11.6) | 0.709 (+15.2) | 0.731 (+15.0) | 0.844 (+5.1) | 0.663 (+27.4) |
| arousal | 0.809 (+12.0) | 0.773 (+7.9) | 0.803 (+9.8) | 0.891 (+4.0) | 0.744 (+26.7) |
| tod | 0.852 (+29.8) | 0.736 (+24.9) | -- | 0.904 (+11.0) | 0.817 (+29.5) |
| season | 0.994 (+2.7) | 0.963 (+5.9) | 0.972 (+6.7) | 0.996 (+0.6) | 0.993 (+9.5) |
| daylight | 0.891 (+18.3) | 0.847 (+18.7) | 0.905 (+13.3) | 0.906 (+6.6) | 0.898 (+41.7) |

### 2. Part M -- meaningful sensitivity (the realness test, sec 5.3)

Task: tell a co-recalled partner of the query fragment from an origin- and age-matched non-partner (win-rate; 0.5 = chance). `Wi` = coordinate i alone. `lift` = win-rate gain from adding coordinate i to the 6-feature ranker. `harm` = win-rate LOSS when the query's coordinate is moved away from its true value (positive = the true value was doing work). z = against the shuffle-null of that same statistic (coordinate permuted within each unit's pool, 20 replicates); [..] = bootstrap 95% CI over units. `Wi - Wsem` is the STRICT sec 5.3 test.

**Unconditional** -- 738 units; W_sem 0.905, W_6 0.902

| dim | Wi | Wi null | Wi - Wsem [CI] | lift | lift z | harm | harm z | incremental bar |
|---|---|---|---|---|---|---|---|---|
| place | 0.541 | 0.500 | -0.363 [-0.377,-0.349] | -0.0262 | +2.6 | -0.0038 | +1.8 | fail |
| weather | 0.545 | 0.500 | -0.359 [-0.373,-0.345] | -0.0183 | +4.6 | -0.0050 | +4.3 | fail |
| warmth | 0.571 | 0.499 | -0.334 [-0.351,-0.316] | -0.0189 | +2.0 | 0.0004 | +1.2 | fail |
| fire | 0.542 | 0.502 | -0.362 [-0.374,-0.349] | -0.0228 | +6.3 | -0.0021 | +3.8 | fail |
| cat_at | 0.505 | 0.500 | -0.399 [-0.408,-0.388] | -0.0022 | +1.6 | 0.0007 | +1.6 | fail |
| valence | 0.564 | 0.500 | -0.341 [-0.362,-0.321] | -0.0105 | +3.8 | 0.0073 | +3.1 | partial |
| arousal | 0.527 | 0.499 | -0.378 [-0.397,-0.359] | -0.0217 | +1.1 | -0.0001 | +1.6 | fail |
| tod | 0.630 | 0.499 | -0.275 [-0.293,-0.255] | -0.0056 | +5.0 | 0.0011 | +1.2 | fail |
| season | 0.656 | 0.499 | -0.249 [-0.266,-0.230] | 0.0002 | +2.7 | -0.0000 | -6.8 | fail |
| daylight | 0.518 | 0.501 | -0.387 [-0.398,-0.375] | -0.0051 | +4.5 | -0.0000 | +3.8 | fail |

**Place held fixed** -- 532 units; W_sem 0.898, W_6 0.895

| dim | Wi | Wi null | Wi - Wsem [CI] | lift | lift z | harm | harm z | incremental bar |
|---|---|---|---|---|---|---|---|---|
| place | -- | | | | | | | (held fixed) |
| weather | 0.548 | 0.501 | -0.350 [-0.367,-0.332] | -0.0187 | +3.9 | -0.0083 | +3.2 | fail |
| warmth | 0.581 | 0.499 | -0.317 [-0.337,-0.297] | -0.0104 | +2.5 | -0.0018 | +0.7 | fail |
| fire | 0.516 | 0.500 | -0.381 [-0.396,-0.366] | -0.0159 | +2.9 | -0.0054 | +1.8 | fail |
| cat_at | 0.504 | 0.500 | -0.393 [-0.407,-0.379] | -0.0039 | +0.3 | -0.0017 | +0.3 | fail |
| valence | 0.577 | 0.496 | -0.320 [-0.344,-0.295] | -0.0085 | +2.1 | 0.0031 | +0.0 | fail |
| arousal | 0.565 | 0.499 | -0.333 [-0.356,-0.307] | -0.0185 | +0.7 | -0.0006 | -0.1 | fail |
| tod | 0.629 | 0.500 | -0.269 [-0.295,-0.242] | -0.0024 | +4.5 | 0.0035 | +1.9 | fail |
| season | 0.649 | 0.503 | -0.249 [-0.270,-0.225] | -0.0003 | +1.8 | -0.0004 | -3.0 | fail |
| daylight | 0.515 | 0.500 | -0.382 [-0.397,-0.369] | -0.0021 | +3.3 | 0.0013 | +2.6 | fail |

**tod held fixed (|diff|<=0.125)** -- 510 units; W_sem 0.902, W_6 0.902

| dim | Wi | Wi null | Wi - Wsem [CI] | lift | lift z | harm | harm z | incremental bar |
|---|---|---|---|---|---|---|---|---|
| place | 0.550 | 0.501 | -0.352 [-0.371,-0.333] | -0.0241 | +3.6 | -0.0029 | +2.6 | fail |
| weather | 0.530 | 0.500 | -0.372 [-0.389,-0.354] | -0.0109 | +5.1 | -0.0038 | +4.5 | fail |
| warmth | 0.565 | 0.499 | -0.337 [-0.358,-0.313] | -0.0122 | +1.2 | 0.0010 | +0.4 | fail |
| fire | 0.538 | 0.498 | -0.364 [-0.382,-0.345] | -0.0190 | +5.1 | -0.0052 | +3.9 | fail |
| cat_at | 0.500 | 0.499 | -0.402 [-0.416,-0.388] | -0.0073 | -1.1 | -0.0045 | -0.8 | fail |
| valence | 0.582 | 0.502 | -0.320 [-0.346,-0.293] | -0.0122 | +2.3 | 0.0012 | +1.0 | fail |
| arousal | 0.556 | 0.503 | -0.347 [-0.370,-0.320] | -0.0187 | +1.0 | -0.0012 | +0.2 | fail |
| tod | -- | | | | | | | (held fixed) |
| season | 0.643 | 0.503 | -0.259 [-0.282,-0.237] | 0.0003 | +1.4 | -0.0001 | -1.8 | fail |
| daylight | 0.510 | 0.500 | -0.392 [-0.405,-0.378] | -0.0022 | +3.6 | 0.0008 | +3.0 | fail |

**Clock-controlled (negatives within 1 day of the positive)** -- 733 units; W_sem 0.902, W_6 0.900

| dim | Wi | Wi null | Wi - Wsem [CI] | lift | lift z | harm | harm z | incremental bar |
|---|---|---|---|---|---|---|---|---|
| place | 0.541 | 0.500 | -0.361 [-0.375,-0.347] | -0.0291 | +2.8 | -0.0071 | +1.4 | fail |
| weather | 0.543 | 0.500 | -0.359 [-0.372,-0.345] | -0.0158 | +5.7 | -0.0035 | +5.2 | fail |
| warmth | 0.562 | 0.500 | -0.340 [-0.360,-0.322] | -0.0137 | +3.4 | 0.0025 | +1.2 | fail |
| fire | 0.541 | 0.500 | -0.361 [-0.374,-0.346] | -0.0216 | +3.4 | -0.0010 | +2.4 | fail |
| cat_at | 0.500 | 0.500 | -0.401 [-0.411,-0.390] | -0.0070 | -1.4 | -0.0052 | -1.7 | fail |
| valence | 0.576 | 0.502 | -0.326 [-0.346,-0.308] | -0.0127 | +2.4 | 0.0030 | +0.2 | fail |
| arousal | 0.545 | 0.501 | -0.357 [-0.376,-0.337] | -0.0209 | +0.8 | -0.0009 | +0.4 | fail |
| tod | 0.633 | 0.503 | -0.269 [-0.288,-0.248] | -0.0068 | +2.9 | -0.0000 | -0.5 | fail |
| season | 0.647 | 0.501 | -0.255 [-0.272,-0.239] | 0.0001 | +3.6 | 0.0001 | -4.4 | partial |
| daylight | 0.522 | 0.500 | -0.380 [-0.392,-0.368] | -0.0036 | +5.4 | 0.0021 | +4.2 | partial |

By ledger source group (unconditional): n units and the incremental-bar status per dim.

| dim | monologue (n=244) lift z / harm z | wandering (n=249) lift z / harm z | other (n=245) lift z / harm z |
|---|---|---|---|
| place | +1.3 / +0.5 | +2.5 / +2.2 | +1.0 / +0.4 |
| weather | +3.2 / +3.0 | +4.3 / +4.5 | +2.1 / +1.6 |
| warmth | +1.1 / +1.4 | +2.4 / +2.2 | +0.2 / -0.6 |
| fire | +3.6 / +2.5 | +3.2 / +2.5 | +2.3 / +0.5 |
| cat_at | +1.1 / +1.6 | +1.6 / +1.3 | -0.0 / -0.1 |
| valence | +0.4 / -0.5 | +2.3 / +2.9 | +3.5 / +3.2 |
| arousal | +1.2 / +2.5 | +0.3 / +0.5 | +0.5 / -0.4 |
| tod | +1.9 / +0.3 | +2.1 / -0.1 | +3.3 / +1.5 |
| season | +0.6 / -5.1 | +0.3 / -0.8 | +2.6 / -2.0 |
| daylight | +0.8 / +0.7 | +1.9 / +1.8 | +5.4 / +4.3 |

### 3. Verdict per dimension (rules fixed in section 3 of the sheet)

| dim | STRICT sec 5.3 bar (beats MiniLM alone) | incremental, uncond | incremental, place-fixed | incremental, tod-fixed | clock-controlled | **verdict** |
|---|---|---|---|---|---|---|
| place | fail (Wi-Wsem -0.363) | fail | n/a | fail | fail | **label** |
| weather | fail (Wi-Wsem -0.359) | fail | fail | fail | fail | **label** |
| warmth | fail (Wi-Wsem -0.334) | fail | fail | fail | fail | **label** |
| fire | fail (Wi-Wsem -0.362) | fail | fail | fail | fail | **label** |
| cat_at | fail (Wi-Wsem -0.399) | fail | fail | fail | fail | **label** |
| valence | fail (Wi-Wsem -0.341) | fail | fail | fail | fail | **label** |
| arousal | fail (Wi-Wsem -0.378) | fail | fail | fail | fail | **label** |
| tod | fail (Wi-Wsem -0.275) | fail | fail | n/a | fail | **label** |
| season | fail (Wi-Wsem -0.249) | fail | fail | fail | fail | **label** |
| daylight | fail (Wi-Wsem -0.387) | fail | fail | fail | fail | **label** |

Prediction scoreboard: 
P1 (strict 0/10): observed 0/10 beat MiniLM alone. 

### 4. Post-hoc diagnostics (NOT pre-registered; added after seeing the primary results)

Script: `scripts/lab_geometric_perturbation_posthoc.py`. Labelled post-hoc so nobody reads them as part of the pre-registered verdicts; none changes a verdict.

**(a) Lower context weight.** The primary wc=0.15 made lift negative for every dimension (a noise term costing more than the signal pays). Re-running Part M (unconditional, 20 shuffle replicates):

| dim | wc=0.01 lift (z) | wc=0.03 lift (z) | wc=0.06 lift (z) |
|---|---|---|---|
| place | -0.0009 (-0.9) | -0.0015 (+1.4) | -0.0091 (+0.5) |
| weather | +0.0002 (+0.9) | -0.0003 (+2.4) | -0.0038 (+3.1) |
| warmth | -0.0009 (-1.1) | -0.0004 (+1.1) | -0.0053 (+1.0) |
| fire | +0.0001 (+2.0) | -0.0006 (+2.7) | -0.0075 (+1.8) |
| cat_at | -0.0003 (-1.4) | +0.0002 (+1.2) | -0.0016 (+0.0) |
| valence | +0.0001 (+0.3) | -0.0021 (-1.6) | -0.0047 (+1.4) |
| arousal | -0.0012 (-2.4) | -0.0002 (+1.4) | -0.0079 (-0.9) |
| tod | +0.0006 (+2.0) | +0.0011 (+1.9) | -0.0007 (+2.6) |
| season | +0.0003 (+0.9) | -0.0001 (+0.8) | +0.0000 (+0.7) |
| daylight | +0.0004 (+1.5) | +0.0000 (+1.1) | +0.0010 (+4.8) |

No dimension has a lift whose bootstrap CI excludes zero on the positive side except season at wc=0.01 ([+0.0001,+0.0005], 0.03 percentage points: negligible and a clock). At small weight every coordinate's lift is ~0 (|lift| < 0.003): it does not hurt, and does not help.

**(b) Pure-clock diagnostic.** In the sheet's own matched design (age bins of width 0.15 in log10 days), the distance |ts_item - ts_query| alone wins 0.650 of the time (n=740 units); the standalone coordinates in the same units: tod 0.616, season 0.645, daylight 0.513, place 0.547, weather 0.538. In the sheet's "clock-controlled" variant (negatives within 1 day of the positive) the same pure clock gets 0.651 and season 0.642: **the sheet's clock control did not remove the clock** (positives sit nearer the query than their bin-mates, so any time-monotone coordinate inherits a ~0.65 win-rate). Every standalone win-rate in the primary tables above is therefore contaminated by temporal autocorrelation of context, place and weather included.

**(c) Tight age matching** (bin width 0.02, n=674 units): pure clock alone falls to 0.586; MiniLM alone 0.879. Standalone coordinates then: place 0.520 (z +4.4), weather 0.509 (z +2.8), warmth 0.517 (z +1.9), fire 0.522 (z +4.8), cat_at 0.496 (z -2.0), valence 0.531 (z +2.0), arousal 0.515 (z +2.2), tod 0.557 (z +6.8), season 0.541 (z +5.1), daylight 0.500 (z -0.0). Incremental lift stays <= 0 for all ten at wc=0.15 (largest: season +0.0001, z +2.4, negligible). The standalone residuals that survive and clear their own null at z >= 4: place, fire, tod, season (all <= 0.056 above chance); tod and season cannot be separated from a not-fully-removed clock (pure clock still 0.586).

**(d) Pool homogeneity** (the shadow's own 600-most-recent pool, 300 queries). Categorical: share of the pool on its modal value; numeric: within-pool SD as a fraction of the cohort kernel SD.

| dim | statistic | value |
|---|---|---|
| place | modal share | 0.504 |
| weather | modal share | 0.724 |
| warmth | SD ratio | 0.781 |
| fire | modal share | 0.692 |
| cat_at | modal share | 0.965 |
| valence | SD ratio | 0.874 |
| arousal | SD ratio | 0.855 |
| tod | SD ratio | 0.718 |
| season | SD ratio | 0.023 |
| daylight | modal share | 0.868 |

Reading: season is essentially constant inside a recent pool (SD ratio 0.02) and cat_at is none for 96% of it, so
perturbing them cannot reorder anything that matters; place is NOT homogeneous (modal share 0.50), so pool constancy does
not explain place's Part S result. The alignment-with-text explanation for place is **inferred, not tested here**.

### 5. Prediction scoreboard (sheet section 4)

| # | Prediction | Outcome |
|---|---|---|
| P1 | strict bar: 0 of 10 beat MiniLM alone | **confirmed**, 0/10 (best: season, Wi - Wsem = -0.249 [-0.266,-0.230]) |
| P2 | Part S distance sensitivity "above shuffle-null (z>0)" | **contradicted under its intended meaning**: Jaccard z>0 on all ten but that means LESS movement than null; rank-shift below null on 9/10. The sheet's wording was ambiguous; I mean it as a miss |
| P3 | incremental bar passes for place and 2-3 more; cat_at/fire/daylight/warmth/weather = label | **half wrong**: all ten are labels, including place. The sparse-dimension half was right |
| P4 | at least one of tod/season passes, and clock control shows part is a clock | **half wrong**: neither passes; the clock half is confirmed far more strongly than predicted (standalone win-rate ~ pure clock) |
| P5 | place-held-fixed flips some dims to conditional | **contradicted**: no dimension passes in any condition |
| P6 | mostly labels | **confirmed** (10/10) |

### 6. Deviations from the sheet and honest limits

* Part S ran **276** queries (24 origin x place cells x 12, short cells took what they had), not 300; place-fixed 275, tod-fixed 276.
* Part M used **up to 250 units per ledger source group** (738 unconditional). Partner-bearing cohort fragments by group: wandering 15,306, other 1,944, monologue 1,399 (groups overlap), so the pooled result leans on wandering-style recall unless read by group (table above).
* Conditional runs build the pool/negatives from candidates that satisfy the condition (place equal; |tod diff| <= 0.125), so they are re-sampled populations, not subsets of the unconditional run.
* The sheet's "clock-controlled" variant is insufficient (diagnostic (b)); the tight-matching run (c) is the better clock control and is post-hoc.
* The optional decoupled-judge pass was **not run** (needs a model; Du's hot model must not be loaded and servers must not be started).
* Valence perturbation changes the query's |valence| weight on affect_match as well as its context match (as the shadow does); its null shuffles only the match, so valence's Part S z includes that fixed weight path.
* Single-coordinate swaps produce physically impossible tuples (fire=burning with place=shore). `place`-held-fixed partially controls this; nothing here controls it fully.
* Excluded by pre-registration: `census_world:*` window-joined fragment_context rows (10,089 rows overall; pending the J-2536 join audit), and everything before 2026-08-29 10:44 NZST. Results say nothing about earlier history or about the excluded join type.
* Popularity (`pop`) and reuse deltas in Part S measure whether the surfaced set is more-read / more-reused, a popularity drift, **not** appropriateness to the query; fire's large z there (+5.2, +14.2) should not be read as fire doing good work (Part M shows it does not).
* Live-store safety: run inside `lab_env.isolate(db="empty")`; `nascence.db` and `co_recall_ledger.jsonl` size+mtime identical before and after; the live DB was read only through a `?mode=ro` connection.

### 7. Follow-up work spawned

See the plan note and job queue (ids in the findings below). In short: (1) a decoupled-judge pass on a 30-pair context-divergent subset once judge hubs are up; (2) Part M v2: find which co-recall sources are NOT embedding-selected, rerun on those only, with exact-age matching and a pure-clock covariate; (3) read the shadow `felt_recall` n>=150 gate against this result before D-0496 is revisited.
