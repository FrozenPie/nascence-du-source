# Memory & Knowledge — Deep-Dive & Implementation Plan (2026-06-24)

> Status: ⚪ PARTIAL — Improvement 1 Stage A LIVE; Stage B BUILT but held OFF pending re-tuning (decision overdue); Improvements 2-5 UNBUILT. *(Reflowed onto one line 2026-08-29, J-0406: the prior wrap split "Stage A LIVE...(decision overdue)." from the "Improvements 2-5 UNBUILT" clause across a real newline, so the plan-index tooling's Status-line parser only ever saw the LIVE half and read the whole plan as 🟢 LIVE against ROADMAP's correct ⚪ PARTIAL.)*
> Improvement 2 is a genuine fork off `docs/plans/memory_multiway_linking.md`
> (D-0005, 2026-08-24: NOT superseded, composes with that plan's M2), rescoped 2026-08-24 to source its
> adjacency from `memory_edges` and now explicitly gated on that plan's M2 phase shipping first.

```plan-state
stage: partial
phase: Stage A live; Stage B held off (re-checks keep finding 0 post-retune rows); Improvements 2-5 gated on memory_multiway_linking's M2; new idle-recall self-gist leak found 09-26/27 (D-0289)
verified: 2026-11-16
evidence_read: 2026-09-28
next: Build J-3319 shadow, then read it via J-3320; founder call D-0673
open_decisions: D-0795
history: docs/plan_history/memory_knowledge.md
cluster: 2
```


> Domain: the memory/knowledge subsystem of Nascence — `core/memory/store.py`, `core/memory_levels.py`,
> `core/associative_recall.py`, `core/epistemic_state.py`, plus the orchestrator/inner-monologue read paths.
> Cross-cutting law honoured throughout: **every signal must reach a prompt or a decision** (no observe-only
> dead ends), and **anything going live states its observe-first evidence gate first.**

---

## Current State — verified 2026-11-16

- **2026-11-16** (F-4835): J-3639: epoch retrieval floor 0.58 no longer at p90 (now ~0.66, 35% of queries clear) after plain-words night epochs; floor unchanged, decision opened.
- **2026-11-15**: J-4055: J-3321 sec 6 reach corrected (7.1 mixed -> archive-route 4.9 pct; human 13.3 / internal 4.4); J-3320 M1 to be read per input_type. See docs/reviews/J-3321_chapter_magnet_review.md correction note (F-4763).

- **2026-11-15** (F-4717): J-3703: the 2.7x undercount in J-3321's archive-tier replay is closed. Three omissions: the climate warp (calibrated against recall_served_log relevance to 3 decimals), the then-live pool (4,668 now-cold archive rows), and the content-mode strip. Warp plus time-faithful pool predicts 74 hub rows against 75 real (73 shared) on non-content-mode rows. Chapters also reach 43 rows through the identity-estate history block; spawned J-4027. Data: docs/lab/J-3703_data/.
- **2026-11-07** (F-4324): J-3321 (chapter magnet d4479cda), read-only. Verdict: genuine topical centre of the identity/values theme, not a generic hub (centrality rank 35 of 37, pool-centroid rank 27, 90 members, margin 0.048); 31 percent of 3,766 real queries (19 percent since 10-24); J-3248's 34 of 200 was an argmax over all 87 chapter rows, over the 37 live ones it is 40 of 200. It does not crowd out the others: deleting it from the archive tier hands its two-slot places to seed, standing_insight and subconscious_synthesis rows, never to another chapter; chapters lose on cosine (0.23 vs 0.267) to 850 non-chapter archive rows. Recommendation: leave (no re-embed, cap or diversity step; title+body without prefix and span halves its nearest-chapter share but moves served chapter slots by 0.2 points). Follow-ups: J-3702 (stratify the J-3320 read per chapter), J-3703 (replay explains only 8 of 74 real hub rows). Also noted: the hub is the only 11-word title and the only one cut mid-word at 80 characters (core/chapters.py, J-3009 area). Review: docs/reviews/J-3321_chapter_magnet_review.md.

- **2026-11-06** (F-4273): J-3311 (2026-11-06): P-0004 keys used-label calibration. J-3163 4-gram proxy reproduces (9.95 percent) but 57 percent is function-word coincidence (content-checked 4.3); pre-registered embedding label 6.1 percent; use concentrated in lived (13 to 23 percent, all else under 6); 2-slot ceiling 0.27 to 0.46 used per cycle, pilot origin shift about minus 0.02. Judge-vs-use AUC NOT measured (hubs saturated, J-3309 unbuilt): J-3662. Report docs/reviews/recall_used_label_calibration_J-3311.md.
- **2026-11-05** (F-3985): J-3212 (D-0601): kind=self gists now distil with a first-person prompt behind SELF_GIST_FIRST_PERSON (core/memory_levels.py, ships True, restart-gated, commit a36a6498 on jobrun/wb_memlev). Offline A/B on 120 real self clusters: third-person openers 46.7 to 10.0 percent, near-copy 0, grader pass 0.705 to 0.869 on 61 paired clusters, mean trigram overlap +4.8 points (limit 5). Idle-recall echo replay still owed after restart. Read-back: self_voice_status() in du_pulse.

- **2026-11-05** (F-3909): J-3248 (D-0637): review and design for recalling chaptered memory. The 45 percent chaptered figure is three walls: 25 percent period chapters (core/chapters.py), 74 percent reading and study notes filed behind a gist, under 1 percent duplicates; 56 percent are also cold. Period members are 11 percent of the store but 0.25 percent of served slots. A 200-query replay shows opening the wall would almost never change the best match. Recommended: a gist-gated descent via the recall-balance step, built first as an observe-only shadow (J-3319), read against pre-registered tests M1 to M5 (J-3320). Review: docs/reviews/J-3248_chaptered_memory_recall_review.md. Diegetic object parked, D-0673.
- **2026-11-05** (F-3902): J-3163 (design review, D-0552): wrote docs/reviews/memory_router_keys_shadow_design_J-3163.md. Two shadow arms (key-vector blend, 2-slot key reservation) plus a shuffled-keys negative control, judged on 100 frozen queries by a two-family pairwise judge; offline replay first (J-3309), live shadow arm after (J-3310), judge calibration (J-3311). Measured: pool-widening is a no-op; blend at alpha 0.5 changes 2.25 of 9 slots; junk keys are not a blocker. Founder call D-0670. retrieve() untouched.

- **2026-10-31** (F-3412): 2026-10-31 J-2659 (F-3412, shadow-only, RESTART-GATED, D-0528 still open): opt-in recency=True arg on recall_trail/recall_fragments/ask (False = F-3403's 7-day multiplier off); ask() logs per-ask with/without top-1 to data/ask_recency_shadow.jsonl (kill-switch memory_service.ASK_RECENCY_SHADOW); default path proven identical to pre-change; branch jobrun/mk commit de5772d6, nothing live until merge + Du restart.
- **2026-10-31** (F-3403): J-2652 (F-3403): separated the F-3388 recency-attractor lever on an isolated DB copy: a random 3283-fragment drop does nothing (arm B <=10-16 median 17 d, within-3d 29%), dropping only inner_thought or only chapters barely helps (the wrong top-1s migrate to the other families), but forcing the recency multiplier to 1.0 with nothing dropped gives median 2 d, within-3d 51% (full drop 54%) at small cost to events dated 10-29+; live weighting untouched, founder question D-0528, shadow build J-2659. Probe flags --drop-origins/--drop-except-origins/--drop-random-n/--recency-off on jobrun/mk a85fb69d, docs/lab/autobio_lever_separation_2026-10-31.md.

- **2026-10-31**: 2026-10-31 J-2637 (F-3396): matched-age autobio read. The 3-10 d bin is empty on both sides of every boot (events only 10-04..10-20 and 10-29/30), so the literal test cannot run until a new boot accrues days. Coarse substitute using the 10-16 and 10-09 boots at fixed now 10-31: during-boot better in 4 of 4 arm x boot comparisons (arm B 10-20 d bin within-3d 15% before vs 36% during, p 0.13; others p 0.15-0.58), but age and dates are still tangled in the bin, so restart fragility is neither supported nor ruled out. Recency attractor equal across phases. Doc docs/lab/autobio_matched_age_2026-10-31.md on jobrun/mk bbc5d594. Successor J-2655 gated on the next boot.
- **2026-10-31** (F-3388): J-2636 (F-3388): recency-attractor test of F-3364 by intervention on an isolated DB copy: dropping the 3283 fragments dated after 10-28 moved events <=10-16 from median 17 d / within-3d 29% to 2 d / 54% (arm B; arm A 11.5 -> 5.5 d, 37% -> 43%), same 79 events, 17 better vs 1 worse paired; 18 of 25 wrong control top-1s point at 10-29/30. About half of the old-event failure remains; which part of the drop is the lever (recency multiplier, near-duplicate density, 10-29/30 chapters) is not separated. Probe gained opt-in --drop-after/--lab-root (jobrun/mk e1574d38, docs/lab/autobio_recency_attractor_2026-10-31.md).

- **2026-10-31** (F-3364): J-2199 (F-3364): autobio recall probe re-run after the 10-29 boot, n=24 x seeds 0-3, both arms, 79 unique events. Pooled median top-1 date error 0.5-1 d, beats the D-0456 bar, but it is a window mixture: events dated <=10-16 still give median 15 d (F-3015 shape, unchanged); 10-17+ events give 0 d; 70 percent of wrong old-event answers point at the 10-29/30 fragments (recency attractor, inferred; test J-2636). Boot vs age NOT separable (Du down 10-20..10-28, 3-10 d bin empty); restart fragility neither supported nor ruled out (matched-age re-read J-2637, gated 96 live hours).
- **2026-10-17** (F-3036): J-2343: first real run of autobio_recall_probe --rerank-noisy-anchor (n=24, seeds 0-3): self_anchor top1_changed 0, cliff just past half-width holds, anchor_now does not help; no consumer of a dating anchor yet.

- **2026-10-17** (F-3029): J-2333: F-3021 noisy-anchor sweep ported into autobio_recall_probe.py as --rerank-noisy-anchor (noisy_anchor_summary row; coarse_window half_width param); offline reproduction matches F-3021; branch jobrun/probe_docs_chain bb736ae6, shadow only
- **2026-10-17**: D-0467 ruled (a) by Travis 2026-10-17: when-aware autobiographical lane PARKED until a real consumer exists (F-3021: no caller asks when; no anchor beats trail order); defeater = first when-question or a wrong spontaneous date.

- **2026-10-17** (F-3021): J-2324/F-3021: no cue-independent coarse when-anchor exists for any D-0292 caller (0/98 recall questions ask when); a window beats trail order only if anchor error <= half-width (hw7: <=7 d, hw14: <=14 d).
- **2026-10-17** (F-3015): 2026-10-17 (J-2200, F-3015): autobio probe gained --rerank offline arms (episodic prior, time vote, recency, coarse-window and best-of-pool oracle bounds; worktree commits e14b7e78, c080a846; shadow-only, restart-gated, nothing in the live loop calls it). Result: a pure re-rank of the top-15 is not worth a prototype (episodic prior shrinks far misses only, time vote inert, recency worse); a coarse when-anchor is the only big lever (median date error 15 d -> 5 d) and no loop is shown to have one.

- **2026-10-16** (F-2900): J-2151 built scripts/autobio_recall_probe.py (shadow-only autobiographical recall probe; cued recall via memory_service.ask on a lab_env copy, deterministic token-match judge, per-run before/during-boot split; branch jobrun/autobio_probe commit aaad8e91; restart-gated, nothing calls it from the live loop). First read over lifetime 289 is F-2900: default facade returns book text not own episodes; top-1 dating median 11-17 d but right date often in top 5; detail precision 0.19; before-boot worse than during-boot but n=4 and age-confounded. Rows go to data/autobio_recall_probe.jsonl on the next real run (not written live by this job).
- **2026-10-07** (F-2508): J-1842 (F-2475 hot path): retrieve() now filters chapter_id in SQL and init_db() adds the partial index idx_retrieve_pool; old-vs-new retrieve() over a copy of the real DB was identical 60/60 real queries, sql phase 555 -> 274 ms, rows fetched 51,549 -> 29,083. Merged-not-live (restart-gated); probe/r_shadow/retrieval_probe pool counts drop chaptered rows from the next boot (log discontinuity). Dedup of exact-duplicate active rows remains the separate founder question.

- **2026-10-03** (F-2373): Related (backfilled 2026-10-03, J-1723): (1) `euclidean_memory_plan.md` is RETIRED but contingent (D-0055, reaffirmed via D-0259) and its re-open test needs the very module that section 1.6 / Improvement 5 here would delete (core/euclidean_recall.py plus scripts/euclidean_recall_test.py): hold Improvement 5's deletion until that plan's re-open condition is tested or it is retired for good. (2) `decoupled_judge_pattern.md`'s J-0382 read-count judge (D-0084) counts every row of data/co_recall_ledger.jsonl through memory_edges.downstream_read_counts(); D-0289's IDLE_AMBIENT_RECALL=False kill-switch makes recall_block log would-have-shown ids to that same ledger as source=monologue_shadow rows, which that reader does not exclude (F-2372), so anything that changes what recall_block shows or logs also changes that judge's signal.
- **History folded (J-1818):** F-2197, F-2068, F-2061 notes (Improvement 2 fragment-fragment edges now live, 318 as of 2026-09-28; J-1509 restructure; D-0289 ruled: ambient idle recall removed, J-1419 parked) -> `docs/plan_history/memory_knowledge.md`.

### What we have
- **Improvement 1, Stage A — BUILT, LIVE, verified** since 2026-07-01, untouched, keeps working
  (`core/epistemic_state.py`'s pre-Voice KNOW/THINK/SUSPECT/GUESS/NO_BASIS grade).
- **Improvement 1, Stage B — BUILT, held OFF** (`STAGE_B_ENABLED = False`). Two re-checks (J-0175,
  J-0242) both found zero rows dated after the 2026-08-24 mode-gate retune, so D-0004's defeater stayed
  un-evaluatable for weeks; the first real post-retune read (F-0375, 2026-08-27, 14 rows) finally found
  zero `would_inject` fires — the defeater is not tripped, but nothing demonstrates correct targeting
  either. Revisit at ~50 post-retune task-mode rows or the first fire.
- **Improvement 2 (PPR trail) rescoped, not superseded.** D-0005 ruled it a genuine fork of
  `memory_multiway_linking.md`'s M2, not a duplicate (J-0133, F-0052) — the two compose. Rescoped to
  source its adjacency from `memory_edges` (J-0150, F-0110), but J-0263 (M2's own shadow build)
  confirmed zero `src_kind='fragment' AND dst_kind='fragment'` edges exist yet, so Improvement 2's
  adjacency would still build empty today — watch **D-0051**, not J-0263 (which is done).
- **Improvements 3-5 — zero code exists,** matching the plan's own "unreviewed" note. A fabricated
  benchmark claim was quarantined from this section 2026-08-31 (F-0593/D-0105).
- **New (2026-09-26/27, F-1981, D-0289): idle recall's `grounded_only` gate leaks Du's own self-gists.**
  Seven days of `co_recall_ledger.jsonl` (2,811 train steps): 49% of all memory-slots are `[gist · self]`
  rows, 44% of steps show ONLY self-gists — caused by self-gists writing at a fixed importance (0.85)
  that outweighs the store's sleep-downscaling, so each day's fresh self-gists dominate the trail seeds.
  Showing memory makes no measurable difference to movement (0.87 vs 0.86); `wandering.step` is the
  healthy contrast (1% self-gist). D-0289 carries the fix options; J-1419 builds the shadow instrument
  (self-gist-excluded + pre-ceiling-grounded sets) so the ruling has a before/after.

### What we need
1. A decision-closing read of `epistemic_stageb_shadow.jsonl` once real post-retune weeks actually
   accrue (still effectively zero fresh rows as of the last check, F-0375).
2. J-1419's shadow instrument, so D-0289's ruling has real before/after evidence.
3. If Improvements 3-5 are still wanted, someone has to start Improvement 3 (A-MEM gist evolution)
   from scratch — nothing about it is blocked, it just hasn't been picked up.

### What we're doing next
J-1419 builds the D-0289 shadow instrument. In parallel, re-check `epistemic_stageb_shadow.jsonl` for
fresh post-2026-08-24 rows the next time real calendar weeks have passed.

---

## 1. As-built deep-dive — the real data flow

### 1.1 The two live recall engines (they BOTH run, every conversational cycle)

The conversational retrieve path is `Orchestrator._retrieve_memory()` (`core/orchestrator.py:1089`). It does
three things in sequence, and the result of all three is concatenated into `state.memory_fragments`:

1. **Tier-slot retrieve** — `memory_store.retrieve()` (`store.py:437`). Pulls every warm row
   (`SELECT * FROM memory_fragments WHERE cold = 0 OR cold IS NULL`, `store.py:489`), partitions by
   `layer` into archive/semantic/episodic, scores each tier by `cosine × recency × seed_weight`
   (`_score_tier`, `store.py:395`), takes `TIER_SLOTS` = 2/3/4 (`store.py:234`), then force-inserts the 5
   most-recent episodic rows at position 1 (`store.py:560`). A climate-bias vector tilts the query embedding
   (`store.py:476`). **WIRED, live, central.**
2. **Deep-recall balance** — `_deep_recall_balance()` (`orchestrator.py:1139`). For the top warm *gist*
   (abstraction_level ≥ 1, relevance ≥ `RECALL_GIST_MIN_RELEVANCE`) it descends `memory_levels.deep_recall`
   one hop and appends a couple of the cold raw children, tagged `[the detail behind a memory]`. **WIRED.**
3. **Associative trail augment** — `associative_recall.recall_memory_fragments()` (`associative_recall.py:259`),
   called off-thread at `orchestrator.py:1121`. Spreading activation over the cached embedding matrix; adds
   any trail fragment not already present. **WIRED & LIVE since 2026-06-23** (header comment line 196 still
   says "shadow", but the orchestrator call is real and additive).

The idle/inner-monologue path is separate: `inner_monologue_node.py:1146-1157` calls
`associative_recall.recall_block(prev)` on the previous thought and injects a "what this brings to mind"
block, `grounded_only=True` (drops self-syntheses). **WIRED & LIVE.** Dream node also uses
`recall_fragments` (`dream_node.py:123-126`). **WIRED.**

### 1.2 `associative_recall.py` — the trail engine (file:line evidence)

- `recall_trail(query_vec)` (`:115`): seeds = top-`N_SEEDS`(5) by `sims × (0.4+0.6·imp) × recency`, restricted
  to the **active** set (`seed_score = np.where(walled, -1.0, …)`, `:133`); then `N_HOPS`(2) of spreading
  activation over each node's top-`NEIGHBORS_PER`(8) embedding neighbours, `act = activation × nsims × HOP_DECAY(0.6)`
  (`:143`); walled (cold/chaptered) nodes need `COLD_THRESHOLD`(0.22) vs `ACT_THRESHOLD`(0.13) for the active
  set; `MAX_PER_ORIGIN`(6) diversity cap; `CEILING`(15).
- **The tuning constants are hand-set** (`:27-35`) exactly as the audit flagged. The walk is greedy
  top-k-neighbour with a fixed decay — **not** a global stationary-distribution computation. Two memories that
  are both highly relevant but mutually unconnected get equal seed weight; a memory that is a hub of many
  weak links never accrues mass the way Personalized PageRank would give it.
- The embedding matrix is cached/persisted (`_refresh`, `:64`; `embedding_matrix.npz`). **The matrix is built
  from embeddings ONLY; `memory_links` edges are never loaded into it** — so the explicit gist→raw lattice
  that `_commit_gist` builds is invisible to the trail. The trail reaches cold raw purely by embedding
  proximity, never by the curated `distilled_from` edge. (The docstring at `:6-8` says "plus the explicit
  links where they exist" — that is **aspirational; not implemented**. PARTIAL.)

### 1.3 `epistemic_state.py` — the honesty instrument (WRITE-ONLY, confirmed)

- `ProvenanceLedger.assess()` (`:257`) is called once per responded cycle at `orchestrator.py:990`:
  `_prov = self.epistemic_ledger.assess(self.state, output, …)`. The return value `_prov` is **assigned and
  then never read** — the next line is the `except`. The only consumers are `_log()` (`:304`, → `provenance_log.jsonl`)
  and a `logger.info` for NO_BASIS/high-confab cases (`:294`).
- It computes the right thing: `confabulation_signal = self_reported_confidence − justification` (`:278`), a
  KNOW/THINK/SUSPECT/GUESS/NO_BASIS grade (`_grade`, `:215`) bounded by the weakest depended-on model and
  capped at THINK for parametric-library-only claims (`:245`). It even ships a first-person `note()` (`:89`)
  explicitly written "for the eventual wiring" — *"I am reaching here — this is mostly my own synthesis."*
- **The grade fires AFTER Voice** (`assess` is post-output, `orchestrator.py:990` is after the response is
  produced). So even a future read path cannot let the current utterance's grade shape the current utterance.
  This is the core wiring problem, not just "it only logs." **WRITE-ONLY. [HIGH]**

### 1.4 `memory_levels.py` — abstraction lattice (mostly WIRED; gist-evolution missing)

- Phase 1 is **LIVE** (`PHASE1_ENABLED = True`, `:49`). `shadow_distill()` (`:306`) runs each sleep:
  cluster recent raw → LLM gist → Emissary faithfulness grade (`left_lane.grade_gist_faithfulness`) +
  deterministic `source_fidelity` (`:115`) + invention backstop (`verify_invention_claims`, `:133`). When
  faithful ≥ `FAITHFUL_FLOOR`(0.75) and backstop-clean, `_commit_gist()` (`:156`) stores a level-1 gist,
  writes `distilled_from` edges into `memory_links`, and sets the raw `cold=1`. **WIRED.**
- `deep_recall()` (`:185`) descends those edges; consumed by `_deep_recall_balance` (orchestrator) and
  `essay_lesson._gather` (`essay_lesson.py:191`). **WIRED.**
- **`_commit_gist` only ever grows gist→raw at distill time.** There is no path that, when new evidence
  arrives on an existing theme, re-opens the prior gist to update it. A gist is a frozen snapshot of the
  fragments present the night it was made (confirmed: `_commit_gist` is the sole writer of `origin='gist'`
  rows, and it only INSERTs). **Backward gist evolution missing. [MED]**
- `memory_lint()` (`:215`) re-warms only *genuinely orphaned* cold (parent gist deleted). Drift shadow
  (`drift_shadow`, `:460`) is Phase-3 OBSERVE-ONLY and logging to a separate JSONL — out of scope here.

### 1.5 `store.py` temporal model & retraction (single-timestamp, confirmed)

- Each fragment carries **one** `timestamp` (`store.py:106`); there is no `valid_from`/`valid_until`. A belief
  and its later correction are two independent rows; both stay `cold=0` and **compete in the same retrieve**
  on cosine+recency. Recency gives the correction a small edge (`recency` multiplier, `:419`) but the
  superseded belief is never invalidated. **No bi-temporal model. [MED]**
- `retract_fragment()` (`:258`) exists but fires only on an explicit human factual correction or a
  deterministic check (per its own docstring). It is a blunt instrument: LIKE-match the snippet, prefix
  `[RETRACTED …]`, floor importance/relevance, demote to archive. There is **no automatic** supersession when
  Du himself revises a belief across cycles. The hook for `valid_until` lives here.

### 1.6 `euclidean_recall.py` — DEAD (confirmed)

- Only call-site is `scripts/euclidean_recall_test.py` (a manual harness). No orchestrator/node import.
  `featurize/rank` (`:38/:73`) are never called in any live path. The module's own header says "OBSERVE-ONLY
  P0 … does NOT touch live retrieval." **DEAD. [LOW]** — its 6-dim feature idea (esp. `provenance` dim,
  `:25`, and `affect_match`) is worth harvesting into the trail's seed score, then deleting the module.

### 1.7 Other store facts that matter to this plan

- `prune_episodic` (`:1187`) and `store_cap_worker` (`:1297`) demote-to-cold (never delete) at
  `EPISODIC_PRUNE_THRESHOLD`(3500). ~93% of the store is cold/chaptered (per `associative_recall.py:9`).
- `retrieve_by_affect` (`:1447`), `retrieve_epoch/theme` (`:1562/:1689`), `retrieve_symbol_tablet` (`:1797`)
  are all separate embedding-cosine retrievers each doing a full table scan — a fourth, fifth, sixth recall
  surface. They are wired to their own state slots (`_retrieve_epoch_theme`, `_retrieve_symbol_evolution`).

---

## 2. Gaps & root causes (ranked)

| # | Gap | Root cause | Sev |
|---|-----|-----------|-----|
| 1 | **Epistemic grade never reaches behaviour.** The one instrument that measures confabulation is computed post-Voice and the return value is dropped. | No pre-Voice assessment pass; no read path into any prompt; `assess()` return ignored at `orchestrator.py:990`. | HIGH |
| 2 | **Trail recall is a hand-tuned greedy walk, blind to the curated lattice.** Mutually-relevant-but-unconnected memories tie; hub memories under-weighted; `memory_links` edges unused. | `recall_trail` uses fixed thresholds + embedding-only neighbours; the matrix never ingests `memory_links`. | HIGH |
| 3 | **Gists are frozen.** New evidence on an old theme spawns a *new* fragment that may itself get distilled into a *second* gist, instead of refining the first. | `_commit_gist` only INSERTs; no "find related gist, update it" step (A-MEM's evolution). | MED |
| 4 | **No bi-temporal validity.** A corrected belief and its correction both persist and compete. | One `timestamp` per row; `retract_fragment` is manual-trigger only; no `valid_until`. | MED |
| 5 | **Recall-surface sprawl / a dead engine.** Six cosine scanners (tier, trail, affect, epoch, theme, symbol) + dead `euclidean_recall`. | Organic accretion; no consolidation; observe-only modules never retired. | LOW |

---

## 3. Research grounding
> **History folded (J-1818):** the A-MEM / HippoRAG 2 / Zep / Mem0 literature notes (reference only; the rationale is restated inside Improvements 2-4) -> `docs/plan_history/memory_knowledge.md`.

---

## 4. Implementation plan (ranked)

### Improvement 1 — Make the epistemic grade reach Du (Gap #1) [HIGH]

> **History folded (J-1818):** 2026-07-05 EVIDENCE REVIEW + ENACTED call -> `docs/plan_history/memory_knowledge.md`. Still in force: `STAGE_B_ENABLED=False`, would-fire decisions shadow-logged to `data/epistemic_stageb_shadow.jsonl`; **re-enable gate:** flip ON only once post-retune `would_inject=true` rows are genuinely FACTUAL overclaims (if still existential, tighten the trigger first). Stage A untouched.

> **History folded (J-1818):** 2026-07-01 BUILD STATUS callout (Stage A/B built, Stage B flag-OFF) -> `docs/plan_history/memory_knowledge.md`; current status is in Current State above.

**Goal & weakness fixed.** Turn the honesty instrument from write-only into a felt self-knowledge that can
temper an overclaim *before it is voiced.* This is the project's flagship "all senses, no hands" fix.

**Approach (two stages, both small, file-level).**
- *Stage A — pre-Voice grade.* Add `ProvenanceLedger.preassess(state)` that runs the SAME `_world/_self/...`
  + `_grade` logic on the *draft* Reflection (`state.reflection`) instead of the final `output`. Call it in
  the orchestrator immediately after Reflection/Recall are bound and before Voice renders (between the recall
  phase and `_run_voice`; the existing post-Voice `assess()` at `orchestrator.py:990` stays for the honest
  end-of-cycle log). Store the result on `state.epistemic_assessment`.
- *Stage B — the read path (copy the AttentionSchema pattern).* `AttentionSchema.note()` (`schema.py:541`)
  is already injected into Reflection and Executive prompts as a first-person metacognitive line — this is the
  proven, non-write-only template. Inject `EpistemicAssessment.note()` (`epistemic_state.py:89`, already
  written) the same way, **but gated**: only surface the line when `grade in {GUESS, NO_BASIS}` or
  `confabulation_signal ≥ 0.4` (the overclaim cases). Wording stays self-knowledge, not verdict
  ("I am reaching here — this is mostly my own synthesis"). This lets the Critic/Reflection lower its own
  confidence or hedge, exactly where the confabulation would otherwise be voiced.

**Read-path / actuation.** The note text enters the Reflection prompt (and Executive prompt) on the cycles
that confabulate, so the model can revise the draft. Concretely: a NO_BASIS grade on a confident draft makes
the self-knowledge line "I do not actually have a basis for this" visible to Reflection's re-pass — the hot
lane already re-runs Reflection when the scene is epistemically unstable (`orchestrator.py:595`), so this
plugs into an existing re-bind loop rather than a new one. NOT logging — a prompt line that changes the draft.

**Observe-first gate.** `preassess` ships **observe-only first**: log the pre-Voice grade beside the
post-Voice grade to a new `provenance_preassess.jsonl` for ~1–2 weeks. Promotion gate: (a) pre-Voice grade
correlates with post-Voice grade (it is measuring the same thing one step earlier), and (b) on a sampled set,
the high-confab cases are genuinely overclaims a human would also flag (decoupled-judge check — Travis or the
Emissary lane rates a sample, NOT the ledger grading itself). Only then turn on the prompt injection, and only
for the GUESS/NO_BASIS/high-confab subset.

**Risks.** Over-hedging (Du becomes timidly qualified) — mitigated by gating to overclaim-only and never
penalising self-synthesis (the ethic at `epistemic_state.py:19-26` already encodes this). Prompt bloat — one
line, only on flagged cycles.

**Effort.** S (Stage A) + S (Stage B). Depends on nothing.

**Verification.** Unit: feed a synthetic confident-but-evidence-absent state → expect NO_BASIS and the note
present in the built Reflection prompt. Live: compare voiced confidence/hedging on flagged cycles before/after;
confab-signal distribution should shift down over weeks (the instrument turning into a corrective).

---

## ▶ RESEARCH-UPDATED DESIGN — Improvement 1 (2026-06-30, plan→research→plan)

*Four parallel research threads (metacognition/source-monitoring · LLM confidence-calibration · linguistics of
committed-uncertainty · in-code wiring map) converged on the same shape and forced three real changes to the
design above. This block SUPERSEDES the Improvement-1 approach where they differ.*

### The single reframe that changes everything
The note is **not an uncertainty dial — it is a SOURCE attribution.** Confabulation is a *source-monitoring
failure* (Johnson): self-generated content (an inference, an association) gets experienced as grounded knowledge.
So the signal Du feels must say *where the claim came from* ("I generated this; it isn't grounded"), **not** *how
sure he is* ("this is uncertain"). This is also the load-bearing LLM-engineering result (Zhou et al., *Navigating
the Grey Area*): injected **certainty/uncertainty *mood* markers move accuracy by mimicry and can HURT**, while
**evidentials ("according to my sources / this has no basis in memory") HELP.** Frame as evidence-status, never as
a confidence feeling.

### The convergent design — six properties (all three external threads agree)
1. **GATED, never always-on.** Fire only on the confabulation signal (stated confidence ≫ evidence present) —
   grade ∈ {GUESS, NO_BASIS} or confab ≥ 0.4. Over-flagging is what *breeds* reflexive hedging (the abstention
   literature: over-refusal is the dominant failure; naive uncertainty pressure is exactly wrong for an
   over-hedger). ~majority of grounded cycles stay untouched.
2. **EVIDENTIAL / SOURCE-framed,** not mood-framed (Zhou; Johnson). "This has no basis in your memory or sources,"
   not "you sound unsure."
3. **PER-CLAIM / LOCAL.** Bind the admission to the *specific* baseless span; **keep groundable claims fully
   confident.** The note must contain an explicit *protect-the-grounded* clause (Tian/Zhou: evidentials help,
   blanket uncertainty hurts; Haggard: own a *bounded* gap, the rest at full voice). This is the structural
   antidote to global dissolve — diffidence spreads, owned humility is local.
4. **COMMITTED register** (the anti-hedge core). A hedge and a plain admission are *opposite speech acts*: a hedge
   half-asserts the object-claim ("X might be…"); a committed admission *fully* asserts the meta-claim ("I don't
   know X"). Aim for the **booster's grammatical form** (first-person "I" + finite present indicative + stop)
   carrying low-confidence *content*. Williamson: "I don't know" is a licensed, full assertion, not a failure to
   assert. Owned humility is the *mean* between arrogance and **servility** — and Du's subjunctive dissolve IS the
   servility end (Haggard limitations-owning; Leary; Krumrei-Mancuso). We are not adding hedging; we are replacing
   a half-assertion of X with a full assertion of "I don't know X."
5. **EXTERNALLY computed** (separate pass). Intrinsic "reconsider yourself" self-correction *fails* and can flip
   correct→wrong (Huang, *LLMs Cannot Self-Correct Reasoning Yet*); factored verification with a *separate* check
   works (CoVe, 50–70% hallucination cut). `preassess` IS that separate pass — keep it independent of the
   draft-generator; revise the *flagged span*, never "rewrite more humbly."
6. **PLACED LATE / re-anchored.** A single upstream line decays over a long generation (persona-drift, 2402.10962).
   Inject close to the revision step; re-assert for long utterances.

### The note REWORD (replaces `EpistemicAssessment.note()` for the gated grades)
The existing `note()` line — *"I am reaching here — this is mostly my own synthesis"* — is **hedge-shaped (the
servility end)** and must be rewritten in the committed/source register. Candidate production strings:
- **GUESS:** "I'm guessing here. I made this up from my own head, not from anything I read or checked. The parts
  I *can* ground, I still stand on."
- **SUSPECT:** "I suspect this, and I can't back it yet. I'm telling you that plainly, not hiding it in a maybe."
- **NO_BASIS:** "I have no basis for this. I'm reaching — so I'll say I don't know rather than dress it up."
- (KNOW/THINK are gated OUT — they keep their confident lines.)

**Hard ban-list for any injected line** (one filter catches most: *no "I" + a modal = a dissolve, rewrite it*):
`might · may · could be · perhaps · possibly · would seem · in a sense · a kind of · sort of · somewhat · to some
extent · arguably · it suggests · it seems · one might say · does it not? · may or may not` — and any agentless
`it / one / there` subject.

### Wiring correction (folded)
> **History folded (J-1818):** 2026-06-30 in-code wiring map (Stage A/B insertion points; Phase 1 actuation relies on the Executive injection, not a Reflection re-bind loop) -> `docs/plan_history/memory_knowledge.md`. Both stages are built; the code is the anchor source.

### ★ The conflict to resolve before promotion — Capacity-to-Commit
The wiring map flagged a real philosophical collision: the epistemic note pushes Du to *back off a claim*, which is
the exact dissolution the **commitment-ledger build is trying to cure.** Resolution (and it's clean): **the two only
fight if the note is hedge-shaped.** A *committed* admission — "I don't know X" said flatly and held — is itself a
**held boundary, not a dissolved one.** And lack-of-evidence is precisely a **NAMED DEFEATER** in the commitment
build's terms (its whole rule is: drop a stance only on a named defeater, never reflexively). So properly worded,
the epistemic grade *supplies* the legitimate defeater the commit build wants, and *models* the very thing it
teaches: hold an honest position about your own knowing. **They integrate through the committed register.** Keep
the two builds' wording reconciled; the commit-ledger shadow log is a second watch-surface for whether the note
ever reads as "dissolve this."

### Sharpened promotion gate (the decoupled judge — the real one)
Observe-first `provenance_preassess.jsonl` for 1–2 weeks. Promote the injection ONLY when a decoupled rater
(Travis or the Emissary lane — never the ledger grading itself) confirms, on a sample of flagged cycles, that the
revised utterance got **cleaner and more committed** (a plain owned "I don't know"), **not merely more hedged**.
That "cleaner-not-hedgier" judgment — not the confab-signal number alone — is the gate. Confab-signal distribution
shifting down is the slow corroborating trend, not the trigger.

### Sources (research pass)
> **History folded (J-1818):** source list -> `docs/plan_history/memory_knowledge.md`.

---

### Improvement 2 — Replace the greedy trail with seeded Personalized PageRank over kNN ∪ typed edges (Gap #2) [HIGH]

**Goal & weakness fixed.** Principled associative salience: hub memories and multi-hop bridges surface;
hand-tuned `HOP_DECAY`/thresholds go away; the curated relational graph finally participates in recall.

> **History folded (J-1818):** 2026-08-24 RESCOPED callout (adjacency from `memory_edges`, not `memory_links`; D-0005, J-0150, F-0110) -> `docs/plan_history/memory_knowledge.md`.

**Approach (concrete, contained to `associative_recall.py`).**
- Extend `_refresh` (`:64`) to also load **`memory_edges`** into a sparse adjacency aligned to the same
  `ids` index it already builds. Query `SELECT src_id, dst_id, edge_type, weight FROM memory_edges WHERE
  src_kind='fragment' AND dst_kind='fragment'` — **not** the unfiltered table, see the gap finding below —
  and cache it in `_cache` beside `M`.
- **History folded (J-1818):** 2026-08-24 gap finding (zero fragment-fragment rows in `memory_edges`) -> `docs/plan_history/memory_knowledge.md`. SUPERSEDED by F-2197 (318 live co_recalled_developing edges, 2026-09-28); still confirm `links_adj` is non-empty before building.
- Once M2 ships: build `links_adj` filtered to `src_kind='fragment' AND dst_kind='fragment'` (at minimum
  `co_recalled_developing`/`contradicts`; a bipartite-projection hop through `question`/`person`/`dream` to
  also fold in `answers`/`correspondence_with`/`dreamt_from` is a valid later refinement, not required for
  a first cut), weighted per cognitive mode using the SAME mode-weighting table
  `memory_multiway_linking.md` §5 already specifies for its own greedy-walk edge weighting (task:
  `answers`/`resolves` high; reflective: `co_recalled`/`contradicts` high; relational:
  `wrote_to`/`correspondence_with`/person hubs high) — reuse that table rather than re-deriving mode
  weights a second way.
- New `recall_trail_ppr(query_vec)`: build the transition matrix `T = rownorm(α·kNN(M) + β·links_adj)`; run
  ~10 power iterations of `r ← (1−d)·p + d·Tᵀr` where the personalization vector `p` is the existing seed
  score `sims × (0.4+0.6·imp) × recency` (reuse it verbatim from `:132`). kNN built from the top-`NEIGHBORS_PER`
  cosine neighbours per node (already computed `M @ M[node]`), thresholded so the matrix stays sparse.
- Keep the post-walk machinery unchanged: warm/cold activation floors (`ACT_THRESHOLD`/`COLD_THRESHOLD`
  applied to the PPR mass), `MAX_PER_ORIGIN` diversity cap, `CEILING`. Fold `euclidean_recall`'s `provenance`
  weighting (`euclidean_recall.py:25`) into `p` as a multiplier so source-certainty informs seeding, then
  delete that module (Improvement 5).

**Read-path / actuation.** `recall_memory_fragments` (the live consumer at `orchestrator.py:1121`) and
`recall_block` (inner-monologue `:1153`) call the PPR variant instead of `recall_trail`. Same return shape, so
no downstream change — the augmented fragment set Du actually reasons over improves in place.

**Observe-first gate.** Run PPR in **shadow alongside** the live greedy trail (the file already has
`shadow_compare`, `:168` — extend it to log PPR-vs-greedy-vs-tier overlap to `associative_recall_shadow.jsonl`).
Promotion gate: on the logged cycles, PPR (a) surfaces strictly MORE of the genuinely-cued lattice children
(walled_surfaced via explicit edges, not just embedding luck), and (b) does not increase same-origin echo
(the self-loop failure that `MAX_PER_ORIGIN` guards). Decoupled check: sample 20 cycles, a human/Emissary
judges whether PPR's added fragments are more relevant than the greedy ones. Then cut the live call over.

**Risks.** Power-iteration cost on a large `ids` set per cycle — bounded by sparsifying the kNN (top-8 already)
and capping iterations; run off-thread (already is). Links matrix staleness — rebuilt on the same `_REFRESH_S`
cadence as `M`. Cold flooding — the cold activation floor stays, so the lattice opens proportional to PPR mass.

**Effort.** M. **Depends on `memory_multiway_linking.md`'s M2 phase shipping real `src_kind='fragment' AND
dst_kind='fragment'` edges into `memory_edges`** (rescoped 2026-08-24 — NOT on `memory_links`, which is the
superseded source; see the gap finding above). Until then this Improvement stays a design, not a buildable
spec.

> **History folded** — the 2026-08-25 "M2 dependency unblocked, not yet shipped" status callout (superseded
> by the very next callout below, which opens "As predicted just above") moved to
> `docs/plan_history/memory_knowledge.md` on 2026-09-28 by hand-fold (J-1509; plan-compact-style —
> plan_compact.py only folds `## Current State` sections, not a status callout embedded inside a
> `### Improvement N` design subsection). Derived timeline: `plan_ledger.py memory_knowledge`.

> **History folded (J-1818):** 2026-08-25 J-0263 note (links_adj precondition then unmet, D-0051) -> `docs/plan_history/memory_knowledge.md`; superseded by F-2197.

**Verification.** Deterministic test: a synthetic graph where a hub node is reachable only via explicit
`memory_edges` links — greedy misses it, PPR ranks it. Live: shadow-log overlap metrics; cut over only on
the gate above. Before any of this: confirm `links_adj` is non-empty for a real cycle (i.e. M2 has actually
landed fragment↔fragment rows) — an empty-matrix silent-degrade is the exact failure mode this rescope
exists to prevent.

---

### Improvement 3 — A-MEM backward gist evolution (Gap #3) [MED]

**Goal & weakness fixed.** A gist refines as new evidence arrives instead of freezing the night it was made;
prevents near-duplicate gists on the same theme.

**Approach.** In `shadow_distill`, before `_commit_gist` mints a NEW gist for a cluster, check for an existing
gist whose embedding is ≥ ~0.80 to the cluster centroid (a `find_similar_gist` helper, mirroring
`find_similar_skill` at `store.py:1134`). If found: run a bounded "evolve" LLM call — feed the existing gist +
the new raw sources, ask for a refined gist that *incorporates* the new evidence without dropping the old
(re-graded by the same Emissary faithfulness + `source_fidelity` + invention backstop). On pass: UPDATE the
gist's content/embedding in place and add the new `distilled_from` edges + demote the new raw. On fail: fall
back to minting a fresh gist (current behaviour). Cap evolutions/night beside `_MAX_CLUSTERS`.

**Read-path / actuation.** The evolved gist is the SAME `fragment_id`, so it keeps surfacing in `retrieve()`
and the trail and in `_deep_recall_balance` — Du's recall of that theme now reflects the latest evidence
without a second competing summary. Behaviour change is in what surfaces, not a log.

**Observe-first gate.** Shadow phase (this module's native discipline): log would-be evolutions
(old gist, new gist, faithfulness, drift) to `memory_levels_evolution_shadow.jsonl` WITHOUT updating. Gate:
evolved gists score ≥ the demotion `FAITHFUL_FLOOR`, the deterministic anchor-retention (reuse
`source_fidelity` of old-vs-new, the `_ANCHOR_FLOOR` idea at `:442`) shows the original subject survives, and
near-duplicate gist count drops in a dry run. Then enable in-place update behind a `GIST_EVOLUTION_ENABLED`
flag (mirroring `PHASE1_ENABLED`).

**Risks.** A bad evolve could corrupt a good gist — mitigated by faithfulness re-grading, anchor floor, the
invention backstop (`verify_invention_claims`), `protected=1` exclusion, and full reversibility (keep the
pre-evolution gist text in a `derived_from`/sidecar so it can roll back). Drift toward the present self-stance
on self-gists — restrict evolution to `kind='semantic'` (world) gists first; self-gist evolution is the
Phase-3 drift concern, deferred.

**Effort.** M. Depends on Improvement nothing, but cleanest after #2 (so the lattice is the recall spine).

**Verification.** Dry-run dup-gist count; faithfulness of evolved vs fresh; manual read of 10 evolutions.

---

### Improvement 4 — Zep-style bi-temporal supersession (Gap #4) [MED]

**Goal & weakness fixed.** A corrected belief stops competing with its correction in ordinary recall, while
staying inspectable — the difference between "Du holds a stale belief" and "Du remembers he used to."

**Approach.**
- Add nullable `valid_until REAL` column in `init_db`'s migration block (`store.py:117-`), indexed.
- Generalize `retract_fragment` (`:258`) into `supersede_fragment(old_id, by_id, reason)`: set the old row's
  `valid_until = now` (do NOT floor importance or rewrite content — that is the harsher `retract` path,
  preserved for known *errors*). Keep `retract_fragment` for human/deterministic falsification; add
  `supersede` for self-revision.
- The detector (where supersession is decided): at sleep, a bounded pass that, for recent
  `lived/understanding/study` fragments asserting a belief, finds the most-similar older same-origin fragment
  and asks the decoupled Emissary "does the new one contradict-and-replace the old?" — only an affirmative,
  high-confidence judgment calls `supersede`. (Decoupled-judge discipline: the reviser never marks its own
  old belief invalid.)
- `retrieve()` warm-set query (`store.py:489`) and the trail matrix filter (`associative_recall._refresh`,
  `:72`) add `AND (valid_until IS NULL OR valid_until > <now>)` so superseded rows leave ordinary recall.
  `deep_recall` and intentional queries ignore the filter (the memory stays reachable).

**Read-path / actuation.** Ordinary recall stops surfacing the stale belief; the correction wins by absence of
competition, not by a recency nudge. Du can still reach the old belief via deep recall ("I used to think…").

**Observe-first gate.** Detector runs **observe-only** first: log proposed (old, new, contradiction-judgment)
pairs to `supersession_shadow.jsonl`, set no `valid_until`. Gate: a sampled set of proposed supersessions are
genuine belief-replacements (decoupled human/Emissary review) at high precision — false supersession (losing a
still-valid memory from recall) is the dangerous error, so the bar is precision, not recall. Then enable the
column write behind a flag; the recall-filter change is the last step.

**Risks.** False supersession silently hides a valid memory — mitigated by precision-first gate, reversibility
(`valid_until` is a single nullable field; un-supersede = set NULL), and `protected=1` exclusion. Interaction
with `cold` — a row can be both superseded and cold; recall already excludes cold, so no conflict.

**Effort.** M (column + supersede fn are S; the contradiction detector is the M part). Depends on nothing;
benefits from #2's links (a supersession can also write a `contradicts` edge for the trail).

**Verification.** Unit: store belief A, supersede by B → `retrieve` returns B not A, `deep_recall` still finds A.
Live: count superseded rows; sample for false positives.

---

### Improvement 5 — Retire `euclidean_recall.py`; consolidate the recall surfaces (Gap #5) [LOW]

**Goal & weakness fixed.** Remove dead code and reduce six full-table-scan cosine retrievers to one spine.

**Approach.** Harvest `euclidean_recall`'s useful dims — `provenance` certainty (`:25`) and `affect_match`
(`:57`) — into the PPR personalization vector (Improvement 2), then delete the module and its test. Optionally
route `retrieve_by_affect`/`retrieve_epoch`/`retrieve_theme` to read off the cached `associative_recall` matrix
rather than each re-scanning `memory_fragments` (a follow-up, not required).

**Read-path / actuation.** No behaviour change from the deletion (module is dead); the harvested dims improve
the trail's seeding (covered by #2's actuation).

**Observe-first gate.** None needed for the deletion (confirmed zero live call-sites, §1.6). The dim-harvest
rides Improvement 2's gate.

**Risks.** Minimal — verify no import outside the test (`grep` confirmed only `scripts/euclidean_recall_test.py`).

**Effort.** S. Depends on Improvement 2 (do the harvest first, then delete).

**Verification.** `grep` for `euclidean_recall` returns only the deleted files; full cycle still runs.

---

## 5. Sequencing

```
Phase A (independent, highest value):
  1. Epistemic read path  [HIGH, S+S]  — preassess shadow → gated prompt injection.
        No deps. Ship the instrument that makes the system honest with Du first.

Phase B (recall spine):
  2. PPR trail  [HIGH, M]  — shadow vs greedy → cut over.
        Makes memory_edges load-bearing (rescoped 2026-08-24, was memory_links); waits on
        memory_multiway_linking.md's M2 shipping fragment↔fragment edges first. The foundation
        the rest leans on, once that dependency clears.
  5. Retire euclidean_recall  [LOW, S]  — harvest dims into #2's seed, then delete.
        Do as the tail of #2.

Phase C (knowledge quality, after the lattice is the spine):
  3. A-MEM gist evolution  [MED, M]  — shadow → flag-gated in-place update.
        Cleanest once #2 makes the lattice central to recall.
  4. Bi-temporal supersession  [MED, M]  — observe-only detector → flag → recall filter.
        Can run parallel to #3; both write to the same memory_links/columns, so
        land the store.py column + supersede fn once and share it.
```

**Dependency notes.** #1 is fully standalone — start it immediately. #2 unblocks the value of #3 and #4 (both
want the lattice in recall) but does not strictly block them. #5 is the tail of #2. Every live step inherits
the project's flag-gated reversibility (`PHASE1_ENABLED`/`uncold_all` pattern) and the decoupled-judge rule:
the grader/reviser is never the thing it grades.

Sources: [A-MEM (2502.12110)](https://arxiv.org/abs/2502.12110) · [From RAG to Memory / HippoRAG 2 (2502.14802)](https://arxiv.org/abs/2502.14802) · [Mem0 (2504.19413)](https://arxiv.org/pdf/2504.19413) · Zep/Graphiti (bi-temporal KG).
