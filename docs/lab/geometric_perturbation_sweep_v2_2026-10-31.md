# Geometric perturbation sweep v2 — non-embedding-selected co-recall only (J-2638) — 2026-10-31

Status: **PRE-REGISTRATION SHEET** (sections 1-6), committed BEFORE the v2 script is run. Results are appended
below the line after the run; nothing above the line is edited afterwards. Job J-2638, plan `cognitive_geometry`,
follow-up of J-2535 (F-3365..F-3369; `docs/lab/geometric_perturbation_sweep_2026-10-31.md`). F-3369 (inferred):
J-2535's independent measure, co-recall partnership, is itself selected by embedding similarity (MiniLM alone wins
0.905), so it is structurally blind to context that surfaces a different-but-good memory. F-3368: its clock control
was insufficient. Active holds D-0083 / D-0088 (cross-space edge layer) are NOT ruled on here.

## 1. Selection audit (step 1 — code read, done before this sheet; cited file:line, worktree = HEAD c07bfd5d)

Every `memory_edges.log_co_recall` writer, and how the ids in ONE row were chosen:

| ledger source | writer | how the ids were chosen | embedding-selected? |
|---|---|---|---|
| monologue (+ legacy `None`) | `nodes/inner_monologue_node.py:1982` <- `associative_recall.last_block_ids()` (`:1019`) <- `recall_block` -> `recall_fragments` (`:983`) -> `recall_trail` (`:150`) | spreading activation: seeds = MiniLM cosine x importance x recency (`:163-174`), hops = top-cosine neighbours of each node (`:190-193`) | **yes** (seed and every hop) |
| wandering | `core/wandering.py:210` (`_drift_from`, `:160-213`) | top-k by cosine to the trail seed, after dropping echoes (cos >= 0.86) and near-duplicates of the trail (>= 0.92): a band-limited nearest-neighbour pick. The co-logged pair = the 2 nearest-below-cap to the SAME seed | **yes** (band-limited) |
| wandering (felt) | `core/wandering.py:244` (`_affective_drift`) | nearest by emotion_embedding to the current mood | not MiniLM, but always ONE id -> never a pair; contributes nothing to partnership |
| curiosity | `core/memory_service.py:241` via `ask("curiosity", ..., k=5, descend=True)` (`nodes/inner_monologue_node.py:3221`) | `what` slot = `recall_fragments` (embedding, `memory_service.py:168-171`); then **auto-descend** (`:213-227`): the highest-activation lattice parent in the pool (origin gist / standing_insight / journal_week) contributes up to 2 `memory_links` children (`_descend_from`, `:515-532` -> `memory_levels.deep_recall`, `SELECT child_id FROM memory_links WHERE parent_id IN ...`) | **mixed**: up to 5 embedding ids + up to 2 graph-walk (lattice child) ids |
| follow | `core/follow_line.py:594` `ask("follow", what=q, why=q, how=q)` | `what` = embedding; `why` = typed `memory_edges` join to a question/shadow_event id (`memory_service.py:446-461`; a free-text q matches no dst_id, so expected empty); `how` = `_descend_from(q)` (a text q is no parent id, expected empty) | **yes in practice** (non-embedding slots are keyed on ids a text cue cannot hit) |
| pursuits | `core/pursuits.py:743` `ask("pursuits", text, k=3, descend=False)` | `what` only | **yes** |
| dream | `nodes/dream_node.py:322` `ask("dream", key, k=6, descend=False)` | `what` only | **yes** |
| grand_work | `nodes/inner_monologue_node.py:6191-6204` `recall_fragments(topic, k=5)` | spreading activation | **yes** |
| recall_act | `core/evidence_recall.py:236` | cosine short-list over world fragments (`_candidates`, `:81-128`) then an LLM agreement judge | **yes** (+ LLM filter) |
| study_note | `core/study_note.py:469` <- `_related_context` (`:199-212`) | walk of `relates_to` memory_links (`_graph_walk_related`) whose edges were admitted at **0.55-0.85 cosine at write time**; fallback = scored cosine scan | **yes, indirectly** (edge admission is a cosine band) |
| essay | `core/essay_lesson.py:386` | `_graph_walk_cross_book` over the same cosine-gated `relates_to` edges; fallback cosine (>= 0.30) + lexical blend | **yes, indirectly** |
| *_shadow (monologue_shadow, divergent_shadow) | excluded (never shown to a thought) | — | — |

**Reading of the audit:** no ledger source is non-embedding-selected as a whole. The ONLY non-embedding selection
path that can put >= 2 ids in one row is **curiosity's auto-descend**: lattice children reached by a `memory_links`
walk from a gist-like parent that was itself embedding-recalled. The child is selected by lattice membership, not by
its similarity to the cue or to the other ids. (Whether a gist's children were grouped by embedding when the gist
was written is a further upstream question this lab does not settle.)

## 2. What gets tested (fixed now)

* **Census (Part A, descriptive):** per source, rows with >= 2 ids, cohort pairs, and the share of pairs that are a
  `memory_links` parent->child edge (either direction) — the empirical footprint of graph-walk selection. Plus the
  tight-matched (bin 0.02) MiniLM-alone win-rate W_sem per source group, as a quantitative "how embedding-selected
  is this source" read (0.5 = not at all; J-2535's pooled 0.905 = strongly).
* **Subset G (the v2 test set):** a co-recall pair (q, p) is in G iff, in the same non-shadow row, p is a
  `memory_links` child of another id r in that row (r != q) and q is not itself a memory_links parent/child of p.
  i.e. p arrived by the descend walk, q arrived by the embedding slot. Any source qualifies (expected: curiosity).
* **Run rule:** Part M v2 runs on G **iff G yields >= 40 units** (query fragments in the cohort with >= 1 G-partner
  that gets >= 3 matched negatives). Below 40, G is reported as too thin and the plain answer is "no testable
  non-embedding source". Separately, any source group whose tight W_sem <= 0.75 with >= 40 units also gets Part M v2.

## 3. Part M v2 design (J-2535 harness, `scripts/lab_geometric_perturbation_sweep.py` imported unchanged)

* Negatives: same origin, same sign, same log10(|age|+1 d) bin of width **0.02** (J-2535 primary: 0.15), 10 per positive.
* **Pure-clock pseudo-coordinate** clk = min(1, log10(|t_item - t_query| / 1 d + 1) / log10(61)); reported beside
  every dimension as W_clk (clock alone).
* **Clock-partialled lift:** lift_i = W(6 + clk + i) - W(6 + clk), with clk entering the ranker as
  0.15 * clk^2 and coordinate i as 0.15 * (1 - match_i)^2 (J-2535's match kernels and weight). Also reported:
  lift over the clock alone, W(clk + i) - W(clk), and the unpartialled J-2535 lift.
* harm_i = W(6+clk+i)(true value) - mean W(6+clk+i)(perturbed values) (J-2535's perturbations).
* Shuffle-null R = 20 (coordinate i permuted within the unit's pool); bootstrap 95% CI over units (500 resamples).
* Conditions: unconditional, place held fixed, tod held fixed (as J-2535), each run only if >= 40 units.

## 4. Verdict rules (unchanged from J-2535, applied to the clock-partialled lift)

* **coordinate** = lift_i > 0 with z >= 3 AND harm_i > 0 with z >= 3, unconditional.
* **conditional** = fails unconditionally, passes both in the place-fixed or tod-fixed condition.
* **label** = fails in all conditions run.
* STRICT sec 5.3 bar (W_i > W_sem, paired CI excludes 0) reported per dimension.

## 5. Predictions (before any number)

| # | Prediction |
|---|---|
| Q1 | G is small: < 40 units likely (descend needs a gist-like parent in a grounded k=5 pool, and the child must carry an experienced fragment_context row). If so, the honest answer is "the co-recall ledger cannot test this question". |
| Q2 | Every source's tight W_sem is >= 0.80 (all embedding-selected per the audit); curiosity's is the lowest because of descend children. |
| Q3 | If G is testable: W_sem on G is much lower than 0.9 (children are not picked for cue similarity), and the coordinates still come out labels; place is the most likely exception because lattice children share the parent's episode. |
| Q4 | felt_recall shadow: the courier id is rarely set (`courier_would_have_fired` mostly false), so the join is thin. |

## 6. Step 3 — felt_recall shadow join (descriptive)

From `data/felt_recall_shadow.jsonl` (read-only): rows, fired rows, rows with a non-null `courier_fragment_id`. For each
courier id: was it ever co-recalled (any non-shadow ledger row)? MiniLM cosine between the courier fragment and the ids
the embedding path co-recalled within +/- 10 min, against the same cosine for 20 random cohort fragments of the same
origin (does the coordinate-keyed path surface partners the embedding path does not?).

---
## PLAIN VERDICT (read this first) — run 2026-10-31, after the sheet above was committed (c25db4a3)

**No co-recall source is non-embedding-selected as a whole, and the one non-embedding selection path that exists is
too thin to test.** The code audit (sec 1) finds every multi-id writer picks by MiniLM similarity, directly
(monologue, wandering, pursuits, dream, grand_work, recall_act, follow) or through `relates_to` edges that were
admitted at 0.55-0.85 cosine (study_note, essay). The only pick with no similarity in it is **curiosity's lattice
descend** (`memory_links` `distilled_from` children of a gist-like parent): in the whole ledger it yields **127 cohort
pairs over 19 query fragments, 9 testable units** (pre-registered floor 40). On those 9 units MiniLM alone is at
chance (W_sem **0.500**, CI [0.23, 0.76]) — consistent with "not embedding-selected", but n is far too small to run
the realness test. **The co-recall ledger cannot answer the F-3369 question today.** Use the decoupled-judge pass
(already spawned by J-2535), or an instrument that logs which slot delivered each id.

What *was* testable — every population with W_sem below J-2535's pooled 0.905 — still gives **10/10 labels** after
exact-age matching (bin 0.02) and clock partialling:

| population | units | W_sem | pure clock W_clk | coordinates passing the incremental bar (lift over 6+clk AND harm, both z>=3) | verdict |
|---|---|---|---|---|---|
| G (walk-reached partners, any link type; pre-registered) | 233 | 0.827 | 0.548 | 0 of 10 uncond; 0 of 9 place-fixed (129 u); 0 of 9 tod-fixed (99 u) | all **label** |
| G_relates_to (declared split, see deviations) | 234 | 0.841 | 0.537 | 0 / 0 / 0 (124, 107 u) | all **label** |
| G_distilled_from (curiosity descend: the non-embedding path) | 9 | 0.500 | 0.492 | not run (< 40 units) | **untestable** |
| study_note (only source with tight W_sem <= 0.75) | 243 | 0.710 | 0.543 | 0 / 0 / 0 (131, 137 u) | all **label** |

The STRICT sec 5.3 bar (coordinate alone beats MiniLM alone) fails 10/10 everywhere (closest: season in G tod-fixed,
W_i - W_sem = -0.185). With tight matching **every standalone coordinate sits at chance** (W_i 0.46-0.54 in G,
G_relates_to and study_note; season 0.60 only inside the tod-fixed G slice, where the clock itself is 0.64), so
J-2535's small standalone residuals (place 0.520, fire 0.522, tod 0.557, season 0.541) do not survive in these
populations. Two isolated z>3 cells (G_relates_to tod-fixed valence lift z +3.3 with harm z +1.9; G_relates_to
place lift-over-clock z +3.4 while its lift over 6+clk is negative) fail their paired condition — about what ~150
cells give by chance.

**Bearing on D-0083 / D-0088:** none directly. Those holds concern the cross-space edge layer; this lab tests the
experienced `fragment_context` coordinates inside the euclidean ranker. What it adds: the sec 5.3 co-recall
instrument that D-0088 asked for is **structurally unable** to grade context-keyed retrieval on this ledger (every
partner set is similarity-chosen), so a "label" verdict from it is weak evidence for retiring a layer and a
"coordinate" verdict was never reachable. No ruling made or implied.

## RESULTS

### 0. Run facts

* Script `scripts/lab_geometric_perturbation_sweep_v2.py` (imports the J-2535 harness unchanged, patches `BIN_W=0.02`),
  seed 20261031, runtime 77 s, CPU only, no model calls. Raw output `docs/lab/geometric_perturbation_sweep_v2_2026-10-31_results.json`.
* Cohort identical to J-2535 (59,187 experienced fragments, ts >= 1787957042.9). Ledger: all non-shadow rows.
* Isolation: `lab_env.isolate(db="empty")` with `_LAB_ROOT` patched to the job scratchpad (S-0315); `core` imported from
  the worktree before lab_env (asserted). Live canary (size, mtime epoch) before -> after, identical:
  `nascence.db` 1,185,161,216 / 1793342673.64; `co_recall_ledger.jsonl` 21,757,888 / 1793383425.38;
  `felt_recall_shadow.jsonl` 3,282,947 / 1793342380.85.

### 1. Census (Part A): how embedding-selected is each source? (tight bin 0.02, up to 250 queries per group)

| group | rows >=2 ids | pairs | memory_links-linked pairs | G pairs in cohort | query frags | units | W_sem [CI] | W_clk | W_6 |
|---|---|---|---|---|---|---|---|---|---|
| monologue (+legacy None) | 8559 | 37668 | 307 | 14 | 1316 | 209 | 0.898 [0.879,0.917] | 0.562 | 0.892 |
| wandering | 43787 | 43787 | 195 | 0 | 15239 | 225 | 0.885 [0.859,0.911] | 0.566 | 0.885 |
| curiosity | 2600 | 34727 | 1778 | 188 (127 distilled_from, 61 relates_to) | 595 | 231 | 0.917 [0.900,0.933] | 0.551 | 0.916 |
| follow | 88 | 260 | 10 | 0 | 86 | 76 | 0.868 [0.820,0.912] | 0.583 | 0.873 |
| pursuits | 45 | 131 | 0 | 0 | 38 | 31 | 0.894 [0.832,0.956] | 0.468 | 0.894 |
| dream | 406 | 6090 | 8 | 4 | 268 | 177 | 0.884 [0.860,0.912] | 0.548 | 0.887 |
| grand_work | 328 | 3197 | 23 | 0 | 494 | 190 | 0.861 [0.832,0.887] | 0.537 | 0.867 |
| recall_act | 54 | 186 | 9 | 4 | 24 | 22 | 0.973 [0.940,0.995] | 0.649 | 0.973 |
| study_note | 2252 | 6690 | 1294 | 260 | 404 | 243 | **0.665** [0.634,0.697] | 0.523 | 0.669 |
| essay | 126 | 3521 | 543 | 706 | 468 | 244 | 0.903 [0.889,0.915] | 0.576 | 0.902 |
| G (pooled) | | | | | 438 | 225 | 0.834 [0.806,0.860] | 0.551 | 0.836 |
| G_distilled_from | | | | | 19 | 9 | 0.500 [0.233,0.756] | 0.492 | 0.533 |
| G_relates_to | | | | | 419 | 236 | 0.843 [0.817,0.867] | 0.563 | 0.843 |

Reading: 9 of 10 sources sit at W_sem 0.86-0.97 (similarity-selected, as the code says). study_note is the exception at
0.665: its partners arrive over `relates_to` edges admitted at 0.55-0.85 cosine to a *different* text (the note), so
partner-to-query similarity is looser, but the pick is still similarity-made upstream. The pure clock is weak
everywhere in this tight design (0.47-0.65), so the 0.02 bin removes most of the time-proximity effect J-2535's 0.15
bin left in (its pure clock was 0.650).

### 2. Part M v2 tables

`lift` = W(6+clk+i) - W(6+clk) (the verdict quantity); `lift over clk alone` = W(clk+i) - W(clk); `unpartialled` =
J-2535's W(6+i) - W6. z against the shuffle-null (20 replicates); CI = bootstrap 95% over units.

**G / uncond** -- 233 units; W_sem 0.827, W_clk 0.548, W_6 0.828, W_6+clk 0.829

| dim | Wi | Wi-Wsem [CI] | lift over 6+clk [CI] | z | harm | z | lift over clk alone (z) | unpartialled lift (z) | bar |
|---|---|---|---|---|---|---|---|---|---|
| place | 0.512 | -0.315 [-0.347,-0.281] | -0.0172 [-0.0284,-0.0058] | +0.5 | -0.0050 | +0.1 | -0.0000 (+1.3) | -0.0172 (+0.5) | fail |
| weather | 0.505 | -0.321 [-0.348,-0.289] | -0.0129 [-0.0206,-0.0061] | +0.8 | -0.0081 | +0.5 | -0.0004 (+0.4) | -0.0129 (+0.8) | fail |
| warmth | 0.475 | -0.351 [-0.394,-0.310] | -0.0004 [-0.0111,+0.0104] | +1.6 | +0.0024 | +0.9 | -0.0455 (-0.5) | -0.0007 (+1.6) | fail |
| fire | 0.518 | -0.308 [-0.340,-0.268] | -0.0099 [-0.0212,+0.0016] | +0.8 | +0.0046 | +1.0 | +0.0179 (+2.6) | -0.0099 (+0.8) | fail |
| cat_at | 0.497 | -0.330 [-0.358,-0.301] | -0.0018 [-0.0061,+0.0023] | +0.6 | -0.0013 | +0.3 | -0.0032 (+0.3) | -0.0018 (+0.7) | fail |
| valence | 0.487 | -0.340 [-0.389,-0.293] | -0.0033 [-0.0167,+0.0099] | +0.0 | +0.0046 | +1.5 | -0.0654 (-1.1) | -0.0029 (+0.1) | fail |
| arousal | 0.497 | -0.330 [-0.372,-0.285] | -0.0065 [-0.0191,+0.0059] | +1.0 | +0.0009 | +1.2 | -0.0373 (-0.3) | -0.0068 (+0.9) | fail |
| tod | 0.511 | -0.316 [-0.363,-0.268] | +0.0025 [-0.0030,+0.0094] | +2.0 | +0.0047 | +1.9 | -0.0404 (-0.1) | +0.0027 (+2.1) | fail |
| season | 0.522 | -0.304 [-0.347,-0.263] | +0.0001 [+0.0000,+0.0003] | +1.3 | +0.0000 | -0.4 | +0.0000 (+2.5) | +0.0002 (+1.4) | fail |
| daylight | 0.496 | -0.331 [-0.359,-0.302] | -0.0021 [-0.0074,+0.0032] | +0.1 | -0.0007 | -0.2 | +0.0020 (+0.5) | -0.0021 (+0.1) | fail |

**G / place** -- 129 units; W_sem 0.855, W_clk 0.507, W_6 0.855, W_6+clk 0.858

| dim | Wi | Wi-Wsem [CI] | lift over 6+clk [CI] | z | harm | z | lift over clk alone (z) | unpartialled lift (z) | bar |
|---|---|---|---|---|---|---|---|---|---|
| weather | 0.522 | -0.334 [-0.379,-0.286] | -0.0021 [-0.0177,+0.0137] | +1.3 | +0.0040 | +1.1 | +0.0221 (+0.9) | -0.0021 (+1.3) | fail |
| warmth | 0.494 | -0.362 [-0.420,-0.293] | -0.0067 [-0.0186,+0.0047] | +1.0 | +0.0020 | +1.7 | +0.0176 (+0.6) | -0.0042 (+1.1) | fail |
| fire | 0.498 | -0.358 [-0.403,-0.306] | -0.0088 [-0.0267,+0.0093] | +0.5 | +0.0005 | +0.5 | +0.0060 (-0.1) | -0.0088 (+0.4) | fail |
| cat_at | 0.501 | -0.354 [-0.389,-0.315] | -0.0021 [-0.0052,+0.0000] | +0.5 | +0.0000 | +0.3 | -0.0032 (-0.0) | -0.0021 (+0.5) | fail |
| valence | 0.514 | -0.342 [-0.410,-0.279] | -0.0188 [-0.0401,+0.0043] | -0.5 | -0.0152 | -1.7 | +0.0029 (+0.3) | -0.0154 (-0.4) | fail |
| arousal | 0.542 | -0.313 [-0.366,-0.257] | -0.0092 [-0.0297,+0.0098] | +0.1 | +0.0021 | +0.5 | +0.0215 (+2.1) | -0.0069 (+0.1) | fail |
| tod | 0.526 | -0.330 [-0.394,-0.249] | -0.0052 [-0.0192,+0.0078] | +0.1 | +0.0006 | +0.5 | +0.0300 (+1.4) | -0.0022 (+0.3) | fail |
| season | 0.488 | -0.368 [-0.432,-0.304] | +0.0000 [+0.0000,+0.0000] | -0.4 | -0.0004 | -1.8 | +0.0000 (+0.4) | +0.0000 (-0.5) | fail |
| daylight | 0.502 | -0.353 [-0.391,-0.316] | -0.0013 [-0.0103,+0.0052] | +0.4 | -0.0018 | +0.1 | +0.0134 (+1.9) | -0.0013 (+0.3) | fail |

**G / tod** -- 99 units; W_sem 0.785, W_clk 0.642, W_6 0.787, W_6+clk 0.787

| dim | Wi | Wi-Wsem [CI] | lift over 6+clk [CI] | z | harm | z | lift over clk alone (z) | unpartialled lift (z) | bar |
|---|---|---|---|---|---|---|---|---|---|
| place | 0.484 | -0.302 [-0.359,-0.241] | -0.0305 [-0.0503,-0.0100] | -0.5 | -0.0191 | -0.5 | -0.0843 (-0.9) | -0.0305 (-0.5) | fail |
| weather | 0.516 | -0.270 [-0.328,-0.215] | -0.0048 [-0.0247,+0.0143] | +0.3 | -0.0017 | +0.3 | -0.0005 (+0.9) | -0.0048 (+0.3) | fail |
| warmth | 0.481 | -0.304 [-0.370,-0.236] | -0.0103 [-0.0313,+0.0090] | -1.6 | +0.0005 | -1.0 | -0.1040 (-1.0) | -0.0103 (-1.6) | fail |
| fire | 0.495 | -0.290 [-0.356,-0.220] | -0.0113 [-0.0312,+0.0079] | -0.8 | -0.0030 | -0.4 | -0.0674 (-1.9) | -0.0113 (-0.8) | fail |
| cat_at | 0.493 | -0.292 [-0.338,-0.245] | -0.0123 [-0.0283,-0.0007] | -1.6 | -0.0095 | -0.8 | -0.0064 (-0.3) | -0.0123 (-1.6) | fail |
| valence | 0.493 | -0.292 [-0.384,-0.205] | +0.0038 [-0.0225,+0.0363] | +0.7 | +0.0038 | +0.5 | -0.1377 (-0.2) | +0.0038 (+0.7) | fail |
| arousal | 0.498 | -0.287 [-0.369,-0.211] | -0.0135 [-0.0359,+0.0053] | -0.0 | -0.0084 | -0.2 | -0.1349 (-0.4) | -0.0135 (-0.0) | fail |
| season | 0.600 | -0.185 [-0.242,-0.127] | +0.0000 [+0.0000,+0.0000] | +1.0 | -0.0005 | -1.0 | +0.0000 (+1.5) | +0.0000 (+1.0) | fail |
| daylight | 0.498 | -0.287 [-0.335,-0.235] | +0.0000 [+0.0000,+0.0000] | -0.1 | -0.0006 | -0.3 | +0.0000 (+0.3) | +0.0000 (-0.1) | fail |

**G_distilled_from / uncond**: skipped (< 40 units; units 9, candidates 19)

**G_distilled_from / place**: skipped (< 40 units; units 7, candidates 19)

**G_distilled_from / tod**: skipped (< 40 units; units 3, candidates 19)

**G_relates_to / uncond** -- 234 units; W_sem 0.841, W_clk 0.537, W_6 0.842, W_6+clk 0.842

| dim | Wi | Wi-Wsem [CI] | lift over 6+clk [CI] | z | harm | z | lift over clk alone (z) | unpartialled lift (z) | bar |
|---|---|---|---|---|---|---|---|---|---|
| place | 0.543 | -0.297 [-0.327,-0.267] | -0.0104 [-0.0242,+0.0016] | +1.3 | +0.0070 | +1.0 | +0.0327 (+3.4) | -0.0104 (+1.2) | fail |
| weather | 0.508 | -0.333 [-0.363,-0.297] | -0.0110 [-0.0198,-0.0023] | +1.1 | -0.0065 | +0.8 | +0.0143 (+1.4) | -0.0112 (+1.1) | fail |
| warmth | 0.463 | -0.378 [-0.414,-0.341] | -0.0045 [-0.0145,+0.0059] | +0.9 | +0.0033 | +1.1 | -0.0504 (-1.8) | -0.0040 (+0.9) | fail |
| fire | 0.509 | -0.332 [-0.366,-0.299] | -0.0112 [-0.0225,+0.0006] | +0.7 | +0.0017 | +0.6 | +0.0060 (+1.0) | -0.0111 (+0.7) | fail |
| cat_at | 0.496 | -0.344 [-0.371,-0.316] | -0.0059 [-0.0115,-0.0004] | -0.8 | -0.0040 | -1.0 | -0.0034 (-0.9) | -0.0059 (-0.8) | fail |
| valence | 0.466 | -0.375 [-0.422,-0.329] | -0.0134 [-0.0267,-0.0008] | -0.5 | +0.0019 | +0.4 | -0.0774 (-2.4) | -0.0128 (-0.5) | fail |
| arousal | 0.495 | -0.346 [-0.387,-0.298] | -0.0134 [-0.0276,-0.0009] | -0.2 | -0.0018 | +0.7 | -0.0320 (+0.1) | -0.0132 (-0.2) | fail |
| tod | 0.527 | -0.314 [-0.359,-0.270] | -0.0064 [-0.0125,-0.0005] | -1.1 | -0.0044 | -1.2 | -0.0098 (+1.0) | -0.0056 (-1.0) | fail |
| season | 0.512 | -0.328 [-0.371,-0.286] | +0.0000 [+0.0000,+0.0000] | +0.6 | -0.0001 | +0.3 | +0.0000 (+0.4) | +0.0002 (+0.7) | fail |
| daylight | 0.495 | -0.345 [-0.370,-0.318] | -0.0043 [-0.0083,-0.0008] | -1.0 | -0.0050 | -1.5 | +0.0018 (+0.4) | -0.0043 (-1.0) | fail |

**G_relates_to / place** -- 124 units; W_sem 0.863, W_clk 0.561, W_6 0.862, W_6+clk 0.862

| dim | Wi | Wi-Wsem [CI] | lift over 6+clk [CI] | z | harm | z | lift over clk alone (z) | unpartialled lift (z) | bar |
|---|---|---|---|---|---|---|---|---|---|
| weather | 0.515 | -0.347 [-0.389,-0.302] | -0.0085 [-0.0262,+0.0066] | +1.0 | -0.0028 | +0.8 | +0.0091 (+0.6) | -0.0085 (+1.0) | fail |
| warmth | 0.468 | -0.394 [-0.446,-0.336] | -0.0080 [-0.0205,+0.0032] | +1.1 | -0.0026 | +1.1 | -0.0370 (-2.1) | -0.0080 (+1.1) | fail |
| fire | 0.497 | -0.366 [-0.407,-0.322] | +0.0014 [-0.0134,+0.0181] | +2.4 | +0.0116 | +2.2 | +0.0066 (+0.9) | +0.0014 (+2.4) | fail |
| cat_at | 0.507 | -0.356 [-0.390,-0.315] | -0.0021 [-0.0129,+0.0082] | +1.1 | +0.0031 | +0.9 | +0.0049 (+1.5) | -0.0021 (+1.1) | fail |
| valence | 0.486 | -0.377 [-0.445,-0.316] | -0.0177 [-0.0350,-0.0003] | -0.1 | -0.0042 | -0.2 | -0.0758 (-0.7) | -0.0169 (-0.0) | fail |
| arousal | 0.543 | -0.320 [-0.380,-0.260] | -0.0059 [-0.0283,+0.0123] | +1.4 | +0.0049 | +1.5 | -0.0270 (+1.7) | -0.0068 (+1.2) | fail |
| tod | 0.540 | -0.323 [-0.389,-0.252] | -0.0129 [-0.0239,-0.0027] | -2.1 | -0.0114 | -2.3 | -0.0059 (+1.5) | -0.0124 (-2.1) | fail |
| season | 0.534 | -0.329 [-0.389,-0.269] | +0.0002 [+0.0000,+0.0006] | +0.4 | -0.0002 | -1.5 | +0.0000 (+1.1) | +0.0008 (+0.6) | fail |
| daylight | 0.494 | -0.368 [-0.406,-0.333] | -0.0052 [-0.0125,-0.0008] | -0.5 | -0.0082 | -0.8 | +0.0047 (+1.2) | -0.0052 (-0.5) | fail |

**G_relates_to / tod** -- 107 units; W_sem 0.804, W_clk 0.640, W_6 0.804, W_6+clk 0.804

| dim | Wi | Wi-Wsem [CI] | lift over 6+clk [CI] | z | harm | z | lift over clk alone (z) | unpartialled lift (z) | bar |
|---|---|---|---|---|---|---|---|---|---|
| place | 0.491 | -0.314 [-0.370,-0.254] | -0.0191 [-0.0371,-0.0004] | +0.6 | -0.0044 | +0.5 | -0.0527 (-0.8) | -0.0191 (+0.6) | fail |
| weather | 0.507 | -0.297 [-0.350,-0.250] | -0.0075 [-0.0245,+0.0086] | -0.6 | -0.0059 | -0.4 | -0.0107 (+0.1) | -0.0075 (-0.6) | fail |
| warmth | 0.462 | -0.342 [-0.403,-0.275] | -0.0061 [-0.0219,+0.0098] | -1.1 | +0.0031 | -0.4 | -0.0920 (-1.0) | -0.0061 (-1.1) | fail |
| fire | 0.502 | -0.303 [-0.352,-0.246] | -0.0166 [-0.0373,+0.0015] | -0.4 | -0.0067 | -0.1 | -0.0273 (+0.1) | -0.0166 (-0.4) | fail |
| cat_at | 0.491 | -0.314 [-0.356,-0.268] | -0.0077 [-0.0204,+0.0017] | -0.8 | -0.0082 | -0.5 | -0.0167 (-0.3) | -0.0077 (-0.8) | fail |
| valence | 0.475 | -0.329 [-0.403,-0.258] | +0.0256 [-0.0023,+0.0536] | +3.3 | +0.0160 | +1.9 | -0.1602 (-0.6) | +0.0256 (+3.3) | fail |
| arousal | 0.481 | -0.324 [-0.411,-0.244] | -0.0133 [-0.0306,+0.0009] | -0.3 | -0.0076 | -0.3 | -0.1497 (-1.1) | -0.0133 (-0.3) | fail |
| season | 0.588 | -0.216 [-0.273,-0.152] | +0.0000 [+0.0000,+0.0000] | +0.2 | -0.0005 | -1.5 | +0.0000 (+1.3) | +0.0000 (+0.2) | fail |
| daylight | 0.500 | -0.305 [-0.342,-0.257] | +0.0000 [+0.0000,+0.0000] | +0.2 | -0.0014 | -0.1 | +0.0047 (+0.9) | +0.0000 (+0.2) | fail |

**study_note / uncond** -- 243 units; W_sem 0.710, W_clk 0.543, W_6 0.708, W_6+clk 0.708

| dim | Wi | Wi-Wsem [CI] | lift over 6+clk [CI] | z | harm | z | lift over clk alone (z) | unpartialled lift (z) | bar |
|---|---|---|---|---|---|---|---|---|---|
| place | 0.488 | -0.221 [-0.256,-0.191] | -0.0137 [-0.0262,-0.0020] | +0.3 | -0.0065 | -0.4 | -0.0228 (-1.0) | -0.0138 (+0.2) | fail |
| weather | 0.496 | -0.214 [-0.248,-0.184] | -0.0139 [-0.0230,-0.0059] | -0.3 | -0.0115 | -0.8 | +0.0091 (+3.1) | -0.0143 (-0.4) | fail |
| warmth | 0.504 | -0.205 [-0.240,-0.169] | -0.0024 [-0.0115,+0.0068] | +1.5 | +0.0007 | +0.8 | -0.0242 (+0.4) | -0.0024 (+1.5) | fail |
| fire | 0.508 | -0.201 [-0.236,-0.165] | +0.0001 [-0.0113,+0.0103] | +2.3 | +0.0098 | +2.1 | -0.0110 (+0.0) | +0.0001 (+2.3) | fail |
| cat_at | 0.494 | -0.216 [-0.244,-0.187] | -0.0052 [-0.0109,+0.0001] | -1.8 | -0.0099 | -2.9 | -0.0092 (-2.5) | -0.0052 (-1.8) | fail |
| valence | 0.513 | -0.196 [-0.237,-0.144] | -0.0110 [-0.0253,+0.0018] | -0.4 | -0.0025 | -0.9 | -0.0225 (+1.3) | -0.0110 (-0.5) | fail |
| arousal | 0.489 | -0.221 [-0.259,-0.180] | -0.0113 [-0.0220,-0.0018] | -0.3 | -0.0011 | +0.6 | -0.0310 (+0.1) | -0.0112 (-0.2) | fail |
| tod | 0.529 | -0.180 [-0.217,-0.145] | -0.0029 [-0.0088,+0.0029] | +0.2 | -0.0034 | -0.5 | -0.0203 (+1.7) | -0.0029 (+0.1) | fail |
| season | 0.528 | -0.182 [-0.221,-0.146] | -0.0001 [-0.0005,+0.0002] | +1.1 | +0.0000 | -0.2 | +0.0000 (+2.0) | +0.0006 (+1.5) | fail |
| daylight | 0.502 | -0.208 [-0.241,-0.175] | +0.0013 [-0.0013,+0.0041] | +2.5 | +0.0013 | +1.4 | +0.0035 (+0.9) | +0.0013 (+2.6) | fail |

**study_note / place** -- 131 units; W_sem 0.720, W_clk 0.509, W_6 0.719, W_6+clk 0.719

| dim | Wi | Wi-Wsem [CI] | lift over 6+clk [CI] | z | harm | z | lift over clk alone (z) | unpartialled lift (z) | bar |
|---|---|---|---|---|---|---|---|---|---|
| weather | 0.497 | -0.223 [-0.276,-0.170] | -0.0148 [-0.0281,-0.0019] | -0.2 | -0.0106 | -0.2 | +0.0025 (+0.4) | -0.0144 (-0.1) | fail |
| warmth | 0.483 | -0.237 [-0.290,-0.179] | +0.0020 [-0.0089,+0.0136] | +1.4 | +0.0027 | +1.7 | -0.0214 (-0.5) | +0.0026 (+1.4) | fail |
| fire | 0.496 | -0.224 [-0.276,-0.172] | -0.0051 [-0.0172,+0.0052] | +2.1 | -0.0007 | +1.4 | -0.0123 (-1.5) | -0.0047 (+2.2) | fail |
| cat_at | 0.486 | -0.233 [-0.285,-0.182] | -0.0059 [-0.0152,+0.0014] | -2.7 | -0.0153 | -4.0 | -0.0119 (-2.9) | -0.0059 (-2.7) | fail |
| valence | 0.504 | -0.216 [-0.288,-0.149] | -0.0017 [-0.0211,+0.0181] | +0.3 | +0.0060 | +0.1 | -0.0022 (+0.5) | -0.0021 (+0.3) | fail |
| arousal | 0.536 | -0.184 [-0.242,-0.115] | -0.0014 [-0.0175,+0.0165] | +0.9 | +0.0000 | +0.3 | +0.0568 (+1.9) | -0.0014 (+0.9) | fail |
| tod | 0.504 | -0.215 [-0.281,-0.151] | -0.0042 [-0.0158,+0.0057] | -0.8 | -0.0063 | -1.2 | +0.0037 (+0.0) | -0.0042 (-0.9) | fail |
| season | 0.512 | -0.207 [-0.277,-0.144] | +0.0002 [+0.0000,+0.0006] | +0.9 | +0.0011 | +1.7 | +0.0000 (+0.3) | +0.0006 (+1.0) | fail |
| daylight | 0.504 | -0.216 [-0.268,-0.163] | +0.0022 [-0.0048,+0.0097] | +1.9 | +0.0035 | +1.2 | +0.0060 (+1.3) | +0.0022 (+1.9) | fail |

**study_note / tod** -- 137 units; W_sem 0.721, W_clk 0.528, W_6 0.719, W_6+clk 0.719

| dim | Wi | Wi-Wsem [CI] | lift over 6+clk [CI] | z | harm | z | lift over clk alone (z) | unpartialled lift (z) | bar |
|---|---|---|---|---|---|---|---|---|---|
| place | 0.495 | -0.226 [-0.280,-0.171] | -0.0139 [-0.0346,+0.0070] | -0.5 | -0.0050 | -0.4 | +0.0000 (-0.1) | -0.0142 (-0.5) | fail |
| weather | 0.493 | -0.228 [-0.283,-0.175] | -0.0059 [-0.0198,+0.0050] | +0.3 | -0.0060 | -0.1 | +0.0079 (+1.2) | -0.0061 (+0.2) | fail |
| warmth | 0.501 | -0.220 [-0.287,-0.162] | -0.0046 [-0.0192,+0.0092] | +0.1 | +0.0033 | +0.3 | +0.0088 (+1.2) | -0.0045 (+0.0) | fail |
| fire | 0.532 | -0.189 [-0.244,-0.124] | -0.0012 [-0.0275,+0.0219] | +0.9 | +0.0096 | +1.1 | +0.0164 (+1.4) | -0.0008 (+1.0) | fail |
| cat_at | 0.491 | -0.230 [-0.278,-0.177] | -0.0001 [-0.0142,+0.0140] | -0.3 | -0.0062 | -1.0 | -0.0089 (-1.8) | -0.0001 (-0.3) | fail |
| valence | 0.525 | -0.196 [-0.262,-0.129] | +0.0075 [-0.0112,+0.0271] | +1.5 | +0.0085 | +1.8 | +0.0143 (+1.7) | +0.0075 (+1.5) | fail |
| arousal | 0.503 | -0.218 [-0.281,-0.148] | -0.0138 [-0.0304,+0.0031] | -0.7 | -0.0034 | -0.1 | -0.0031 (+0.3) | -0.0137 (-0.7) | fail |
| season | 0.541 | -0.180 [-0.234,-0.124] | +0.0000 [+0.0000,+0.0000] | +0.1 | +0.0000 | -0.6 | +0.0000 (+1.7) | -0.0002 (+0.1) | fail |
| daylight | 0.494 | -0.227 [-0.278,-0.177] | -0.0027 [-0.0069,+0.0000] | +0.5 | -0.0042 | +0.0 | -0.0033 (-0.0) | -0.0027 (+0.5) | fail |


### 3. Step 3 — felt_recall shadow join: **not joinable**

`data/felt_recall_shadow.jsonl`: 5,852 rows, 4,979 fired, **0 rows with a `courier_fragment_id`**
(`courier_would_have_fired` is false on all 5,852). The row records `n_match` and the affect lean of the matched
fragments but not their ids (`core/felt_recall.py:672-682` writes only the courier id). So whether the
coordinate-keyed path surfaces partners the embedding path does not **cannot be read from the shadow as written**.
Spawned as an instrument job (see findings).

### 4. Prediction scoreboard

| # | Prediction | Outcome |
|---|---|---|
| Q1 | G small, < 40 units likely | **half wrong**: pooled G has 233 units, but most of its pairs are essay/study_note `relates_to` walks (cosine-gated). The non-embedding part (distilled_from) has 9 units, so the spirit of Q1 holds |
| Q2 | every source W_sem >= 0.80; curiosity lowest | **wrong in detail**: 9/10 >= 0.86, but study_note is 0.665, and curiosity is among the HIGHEST (0.917): descend children are too few to pull it down |
| Q3 | on G, W_sem well below 0.9; coordinates still labels; place the likeliest exception | W_sem 0.827 (lower, not much lower); labels **confirmed**; place **not** an exception (W_i 0.512) |
| Q4 | felt_recall courier id rarely set | **confirmed, stronger**: never set (0/5,852) |

### 5. Deviations and limits

* **Declared after the smoke run, before the full run:** G split by the link type that reached the partner
  (distilled_from vs relates_to), because the smoke census showed G is mostly essay/study_note `relates_to` walks,
  which the audit classes as indirectly similarity-selected. The pre-registered pooled G is still reported and
  decides nothing differently.
* Subset G is identified from the ledger plus `memory_links` after the fact (the ledger does not record which `ask()`
  slot delivered an id); a lattice child that was ALSO embedding-recalled would be counted as walk-reached.
* `lift` and `harm` for season are ~0 by construction (season is near-constant inside a unit's pool).
* A smoke run (30 queries per group, 3 reps) preceded the full run; its numbers were used only to see G's composition.
* No decoupled-judge pass (no model calls; the hot model is shared with other lab agents).
