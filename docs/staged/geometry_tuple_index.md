# Geometry Tuple Index — checkpointed multi-dimensional object indexing (STAGED / EXTERNAL — updated 2026-08-29)

> **Status: 🟡 P1 BUILT (2026-09-02, D-0107) — the rest of this document is still a staged
> thought-experiment (last substantial expansion 2026-08-24). NOT part of Du's active architecture.
> NOT linked to ROADMAP.md or `cognitive_geometry.md`'s umbrella. Still performs no action on its
> own — the P1 sidecar is a standalone, offline, read-only-of-source index/benchmark artifact
> (`scripts/geometry_tuple_p1_run_transition_index.py`), not wired into any live code path; nothing
> beyond P1 is authorized. See "Current State" below.**

```plan-state
stage: built
phase: P0/P1 built as an offline benchmark script; P2 real-consumer evaluation run 2026-09-23 (F-1749); nothing beyond P1 authorized
verified: 2026-11-14
evidence_read: 2026-10-31
next: J-3775 natural-traffic check before any helper (J-3778)
history: docs/plan_history/geometry_tuple_index.md
cluster: 0
```


> Domain: whether a real, benched, additive, evidence-gated indexing scheme — informed by a predecessor
> project's compression/indexing archaeology, grounded against current SOTA literature, and validated
> against a real cross-plan survey of Nascence itself — could someday let Du fetch point-in-time slices
> across several real dimensions (world-state, episodic memory, epistemic confidence, time) without full
> linear scans, and let derived signals (transitions, causes) become indexed dimensions in their own right.

> **Honest trajectory note, added 2026-08-24 after two independent external reviews (Gemini, GPT) both
> converged on the same observation without seeing each other's**: this document's own edits have been
> organically drifting from "geometry index over flat state" toward "event-sourced temporal causal graph"
> — the T-KGC quadruple structure (§2.2), the event-sourcing framing unifying P1/P1.5, and the
> causal-relation elevation (§2.3) all pull the same direction. Named explicitly rather than left
> implicit: the real destination this design may be heading toward is a temporal causal memory graph that
> uses geometric/indexed lookups as one mechanism, not a geometric index with temporal/causal features
> bolted on. Not a scope change — a framing-honesty note for whoever picks this up next.

> **Lineage.** Raised as thought T-0010, promoted to idea I-0023 (Travis + Gemini, night of 2026-08-23).
> Grounded across one long session (2026-08-24) through: two rounds of ABF/Pinnacle archaeology
> (F-0243–F-0250); a systematic survey of all ~59 active Nascence plans for real consumers of this idea
> (F-0251, 6 confirmed + 2 weak hits, detailed in §6); three rounds of real SOTA literature research
> (F-0252–F-0254, citations in §8); and direct verification against live Nascence data (`provenance_log.jsonl`,
> `moments.jsonl`, `geometry_tuples.jsonl`). **Explicitly not a child of `cognitive_geometry.md`** — draws
> on its "spaces" ontology and additive-only discipline as prior art, not as a governing parent. The founder
> was explicit early in this design (2026-08-24): this must not be wired into Du's active architecture,
> since several real, active plans already touch this territory and folding this in as a live child-plan
> would collide with them.

---

## Current State — verified 2026-11-14

- **2026-11-14** (F-4596): J-3841: moment_ts lag1 share measured on 6009 stamped inner thoughts, 99.98 percent lag1; own_moment_ts (J-3479) exact 6008 of 6008. No stamp change needed.
- **2026-11-14** (F-4595): J-3753: twin stamp rows measured on rolling_intrinsic_dimension, marginal_reach and ten readers; headline verdicts unchanged, two readers' quoted numbers shift. Report docs/lab/J-3753_twin_effect_dim_reach_audit_2026-11-14.md (worktree branch jobrun/x1_geometry_tuple_index).

- **2026-11-07** (F-4392): J-3308 near-duplicate text replay done: 2,000 pairs, 150-pair 3-model judge panel; pre-registered rule says per-purpose shared helper, qualified as an upper bound; report docs/reviews/near_duplicate_text_tests_J-3308.md
- **2026-11-07** (F-4361): J-3468 twin-row reader audit (2026-11-07): 72.5 percent of idle cycles have an inner_thought stamp twin; mapping census and object_graph commonality count both but stripping the stamps moves headline numbers little and flips no verdict (docs/lab/J-3468_twin_row_reader_audit_2026-11-07.md). HUD gauges are value lines, not rate gauges. Follow-ups J-3752, J-3753.

- **2026-11-06** (F-4094): 2026-11-06: the UDMS Argon-audit follow-up (F-4078) gave the J-2536 'double census calls' item its mechanism: store.py:1080 stamp row + idle row, debounce compares [:120]; 60-95% of idle cycles since 2026-09 are two rows. core/mapping_census.py and core/object_graph.py count both (F-4094, F-4095 inferred); J-3455 (needs_input: A idle row canonical / B mark the stamp row) and the Nascence reader audit spawned from F-4094 land before any debounce change.
- **2026-11-05** (F-3989): J-3306: corrected overclaims about ghost_tuples in this doc (WORLD index live, MEMORY index inert in the live process, no 2-gram code exists); HUD World-tab figure relabelled fragment_context_rows; ghost_tuples docstring updated; P0 doc got a pointer to the J-3247 review.

- **2026-11-05** (F-3901): J-3247 review docs/reviews/ghost_memory_index_chord_echo_J-3247.md: the ghost MEMORY index is inert in the live process (F-3901); chord_echo had no owner (F-3897); an exploratory probe does not favour it (F-3898). Recommendation: leave with a note, run the pre-registered replay J-3307, retire per D-0669 if it fails. Exact-dedup pre-filter stays with J-3266.
- **2026-10-31** (F-3383): J-2640 reading context-stamp loss fixed on jobrun/gti commit 101b4df9: store_fragment census stamp passes debounce=False and reuses the last recorded census row inside the 0.5 s window, no extra geometry_tuples rows, kill-switch STAMP_REUSE_ON_DEBOUNCE, isolated test 20/20 stamped and audit OK vs 3/20 pre-fix, no backfill, RESTART-GATED until Du next boots

- **2026-10-31** (F-3379): - **2026-10-31** (F-3379): J-2642 built the liveness streams in scripts/liveness_audit.py (branch jobrun/gti, 1da25ebe): geometry_tuples writer (2 h cadence) and a 24 h fragment_context stamp-coverage verdict (reading >= 90%, others >= 98%, QUIET under 50 rows). First live read is DEGRADED, reading 150/501 = 30% stamped; fix is J-2640.
- **2026-10-31** (F-3370): J-2536 tuple join integrity audit (docs/lab/tuple_join_integrity_2026-10-31.md, branch jobrun/gti): fragment_context is 89.9% exact-id (fragment_id keyed, write-time stamp since 2026-08-21 21:46), only 10.1% the legacy window join, which is wrong at most 0.19% vs write-time truth; the 63.8% coverage is an era artifact (21,502 pre-census + 19,623 census-pre-stamp + 15,056 post-stamp omissions). Real bug: geometry_census debounce drops 29% of post-stamp reading (J-2640). Moments have no key; 91.2% join by text+time (founder call J-2641). J-2535 should use only experienced:% rows post 08-21, exclude reading and retrospective origins.

> **History folded** — 9 dated entries (2026-08-29 … 2026-09-23) moved to `docs/plan_history/geometry_tuple_index.md` on 2026-09-27 by hand (J-1484). Derived timeline: `plan_ledger.py geometry_tuple_index`.

---

## 0. WIN CONDITION

If ever activated: a real, benched, additive indexing scheme spanning at least the Time × Knowledge
dimensions (and, if warranted by evidence, Memory and world-state), built only on verified-real patterns,
with an honest verdict on which of the 6 real candidate consumers found in §6 actually benefit.

**Never claimed:**
- Not part of Du's active runtime by virtue of this document existing.
- Does not train or fine-tune any model — `RESEARCH_specialists.md`'s territory exclusively, not
  revived or extended here.
- Does not port Pinnacle's or any ABF pillar's code directly — principles only, verified independently
  (see F-0243–F-0250).
- Does not fix `moment.py::recall()` — a semantic/ANN search problem, out of scope (see §1).
  **Revised 2026-08-24, founder decision ("stop deferring")** — this boundary is intentionally
  lifted at the *design* level, not the implementation level: see new §2.5. No code touching the
  live `moment.py` has been written; the activation guard (§7) still applies in full.
- Does not claim the "distinct index structure per band of one multiplexed stream" idea in §4 is
  validated or precedented — SOTA research (F-0254) found each *ingredient* real and proven but this
  *specific combination* has no direct precedent in the literature. Treat §5 as the most speculative,
  least-de-risked part of this whole document, clearly separated from the rest.
- Does not claim a discrete 5-level ordinal confidence grade is itself a validated design (SOTA research,
  F-0252, found no literature validating grade *granularity* specifically) — what's validated is that
  Du's grade is *decoupled from self-report*, which is the part that matters (see §2.2).
- Is not the founder's earlier "7-dimensional consciousness manifold" dossier framing — that framing was
  reviewed and found almost entirely unimplemented fantasy on a few real anchor points; this document
  keeps only what survived independent verification.

---

## 1. DIAGNOSIS — as verified this session

- `core/moment.py::recall()` full-scans `moments.jsonl` (128MB, 14,210+ rows) every call; its own
  docstring already names a semantic/ANN index as the deferred next step — out of scope here (§0).
  **Un-deferred at the design level, 2026-08-24 — see §2.5.**
- `core/mapping_census.py::load_rows()` full-scans `geometry_tuples.jsonl` (16,600+ rows) for population
  statistics that must touch every row by construction — no index reduces this; also out of scope.
- **The real, unmet need**: point-in-time lookups — "what was field X at/near row or timestamp Y" —
  which don't exist today in any form.
- **Correction added 2026-08-24 (external review, GPT) — two distinct justifications were being blurred
  together.** The original P0/P1 motivation is *speed* (full scans slow at 14k+ rows). The §6 baseline
  survey's six real hits are *correctness* problems (a hardcoded guess where a real answer would do), not
  scan-speed problems — none of them fire often enough for speed to be the actual pain. What those six
  consumers need is a *real* signal, not necessarily a *fast* one; even a full scan might suffice for
  their call rate. Keep these as related-but-separate justifications: speed motivates P0/P1's design
  choices (why an index, not a scan), correctness motivates §6's evidence that the gap is real (why build
  anything at all). Conflating them overstates the urgency of the speed argument for the six named
  consumers specifically.
- **The join problem, verified directly against live data (2026-08-24):** `provenance_log.jsonl` carries
  both `ts` and a real `cycle_id` (UUID). `moments.jsonl` and `geometry_tuples.jsonl` carry only `ts` —
  **no exact shared key exists across all three logs.** **Resolved 2026-08-24, external review (Gemini)
  + independent verification**: `orchestrator.py` confirmed single-threaded/synchronous —
  `epistemic_ledger.assess()` (line 1381) and `geometry_census.snapshot()` (line 2547) both fire from the
  same per-cycle method, no async/threading. The real gap isn't concurrency jitter (a generic
  distributed-systems assumption that doesn't fit this codebase) — it's that LLM calls between logging
  steps within one sequential cycle take real wall-clock seconds, a predictable, not random, offset. **The
  fix**: thread `cycle_id` (already generated, already on `provenance_log.jsonl`) through to
  `moment.record()` and `geometry_census.snapshot()` too, giving all three logs an exact shared key —
  eliminates the fuzzy-join problem outright instead of managing it with a tolerance window. Small, cheap,
  concrete; supersedes the tolerance-window idea as the P1.5 join mechanism.
  **Reconciled 2026-08-24, F-0277's open question closed by reading the real source
  (`memory_edges.py::sync_fragment_context()`)**: this fix has **not** been superseded by anything
  live — `sync_fragment_context()` uses exactly the tolerance-window approach this note argues against
  (±300s bucket match + text-content uniqueness as the disambiguator, no `cycle_id` anywhere), and it's
  real, live, working code today. So the two aren't competing solutions to the same problem — `cycle_id`
  remains a real, unimplemented, still-valid improvement. But `sync_fragment_context()` is also
  **narrower than this section's original scope**, not a full substitute: its own code explicitly limits
  matching to `source in ("idle", "monologue", "monologue_train")`, with an honest inline comment —
  *"cycle rows match 'lived' Q/A shapes — later"* — meaning conversational/cycle-sourced rows (exactly
  what this section's `cycle_id` proposal was aimed at) are still unjoined by anything live. **A real,
  separate correction found along the way**: `sync_fragment_context()` doesn't join to `moments.jsonl`
  at all — it joins `geometry_tuples.jsonl` to a *different*, SQL-backed episodic store,
  `memory_fragments` (`origin='inner_thought'`, the same store `associative_recall.py`'s spreading
  activation reads). Nascence has **two separate real memory stores** — `moment.py`'s `moments.jsonl`
  (cycle-bound "moments," §2.5's subject) and this older, broader `memory_fragments` SQL table — this
  document had been treating "Memory" as one thing; it's two, and `sync_fragment_context()` only
  touches the second.
- `C:\FreshStart\core\lib\abf\abf_fold_v3_alczip.py:104-127`'s dead `fold_with_checkpoints` and
  `scripts/legacy/pinnacle_hmc.py`'s real adaptive octree remain the two concrete archaeological
  precedents for "index intertwined with compression" (F-0246, F-0249) — neither runs as-is; J-0210
  tests whether the checkpoint pattern specifically transfers to JSONL.

---

## 2. THE THREE CANDIDATE DIMENSIONS (added 2026-08-24)

### 2.1 Time
Free and trivial at the base level: every row in every relevant log already carries a real wall-clock
`ts`. **A real cautionary tale exists in this exact codebase**: `moment.py`'s own `_drift_key()` — an
attempted "temporal feel" signature — was proven (`moment.py:399`) to be *"a mathematical artifact of the
AR(1)-style smoothing recursion... cannot fail,"* not real information, replaced with an honest
shuffle-null significance test. Any *derived/felt* time signal (as opposed to plain timestamp) needs that
same shuffle-null-grade skepticism. **Real precedent for doing better**: Zep/Graphiti's bi-temporal model
(valid-time vs. ingestion-time; arXiv:2501.13956, Jan 2025, F-0252) — real, current, shipping — is what
`memory_knowledge.md` already gestures at by name without building. Real precedent for *branching*
without corrupting objective time also exists here: `train_split_merge.md`'s Lane 1 (prove) / Lane 2
(disprove) fork-and-merge, done carefully, unlike this dossier's original hand-wavy τ-axis idea.

### 2.2 Knowledge (epistemic state)
**Already real, live, and richer than a 3-state model.** `core/epistemic_state.py` computes a genuine
5-level ordinal grade — `NO_BASIS < GUESS < SUSPECT < THINK < KNOW` (confidence weights 0.00/0.25/0.50/
0.75/1.00) — persisted one line per responded cycle to `data/provenance_log.jsonl` (plus shadow variants).
**Verified directly (2026-08-24) that the grade is NOT copied from self-report**: a real sample row shows
`self_reported_confidence: 0.85` but assigned `grade: SUSPECT` (weight 0.5), dragged down by
`contradiction_count: 5` and `confabulation_signal: 0.35`. This matches SOTA research's single strongest,
most-replicated finding (F-0252): verbalized LLM self-confidence is unreliable; only decoupled signals
(semantic entropy, contradiction-checking, hidden-state probes) are validated. **Du's existing mechanism
already does the right thing.**

**Design: Time × Knowledge transitions, not just point-in-time grades.** Track *when/how/why* a memory's
grade changed, distinguishing:
- **Upgrades** (e.g. GUESS→THINK — a belief firming up)
- **Downgrades** (e.g. KNOW→SUSPECT — something Du thought was solid getting undercut)
as separate event types from the start (founder decision, 2026-08-24), since they are very unlikely to
be equally interesting for the "why" question. Each transition record's "why" comes free from data
already logged — no new instrumentation needed: capture the delta in `contradiction_count`/
`confabulation_signal`/`source_count`/`dominant_source` at the moment of transition.

**Formalization added 2026-08-24 (external review; citation independently verified same day)**: rather
than an ad-hoc transition record, structure each event as a temporal-knowledge-graph quadruple
`(entity, relation, grade, [t_start, t_end])` — e.g. `(this_memory, has_grade, SUSPECT, [ts_i, ts_j])` —
matching the standard `(s, r, o, t)` TKG representation confirmed real and current (Wang et al. 2023
survey; "Temporal Knowledge Graph Completion: A Survey of Models, Benchmarks, and Methodological
Perspectives," IEA/AIE 2026) — with edge weight derived from the same decoupled signals already in
`provenance_log.jsonl` (contradiction/confabulation deltas) rather than a bespoke difference vector.
Gives the transition tracker a real, recognized structure (T-KGC) instead of a one-off schema, and
composes naturally with the bi-temporal (Zep-style) framing already in §2.1.

**Two distinct tuple shapes, added 2026-08-24 — both already real in Nascence, need different math.**
**Vector-shaped**: fixed-length numeric tuples — the real, live 8-float affect vector, Sound Space's 6
coordinates. Compress via rotation/PCA or Product Quantization (§3). **Graph-shaped**: `memory_edges.py`'s
typed edges (`resolves`, `dreamt_from`, `co_recalled_developing`, `contradicts` — real, live, M0+M1 built)
and the T-KGC quadruples above are relational, not vectors — compress via graph/KG embedding methods, a
different family entirely. "Does each dimension get its own tuple, or can tuples be multidimensional" —
both, already, simultaneously: `geometry_tuples.jsonl` rows are joint multi-field tuples, affect is a
vector-tuple nested inside one field of that row, and memory_edges is a separate graph-tuple structure
alongside it. Nothing here needs inventing.

### 2.3 Memory
`moments.jsonl` (episodic memory — the project's own vocabulary) and `geometry_tuples.jsonl`
(state-snapshot) are parallel, uncrossed logs today (§1). This is not a new direction — it's the thread
tying together two of the six real baseline-survey hits (§6): `memory_multiway_linking.md`'s M2
trail-walk wanting a real edge-weighting signal, and `factory_candidates_from_history.md`'s cause
attribution ("was the cat there") wanting real state at a memory's formation instant instead of a guess.
Memory-as-a-dimension means: a memory's epistemic grade (§2.2) and the world-state at its formation
instant (§1's join problem) both become real, queryable coordinates once cross-indexed.

**Elevated 2026-08-24 (external review, GPT)**: `factory_candidates_from_history.md`'s "was the cat
there" hit is not just one entry in the §6 table — it's a **causal-indexing** need specifically (a
percept's *cause*, not just its co-occurring state), and deserves more weight than a footnote. The
distinction matters: `weather=sunny` is a state fact; `weather=sunny → increased_outdoor_observation` is
a causal claim. The T-KGC quadruple structure (above) already accommodates this (`relation` can encode
`caused`/`preceded`, not only `has_grade`) — worth designing P1.5's schema with causal relations in mind
from the start, not just grade transitions, since the real consumer evidence already points there.

**Noted, explicitly out of scope (external review, GPT)**: counterfactual retrieval ("what usually
happens when the cat is absent") is a real, legitimate direction — causal inference / structural
counterfactual models is a mature field (Pearl-style do-calculus) — but it's further out than anything
in P0-P2, same tier as §4's speculative compression work. Not pursued here; named so it isn't
rediscovered from scratch later.

### 2.4 Slice + overlay: the four standard queries (proposed 2026-08-24, session continuation — unconfirmed)

Every dimension in §2 (and any overlay of them) supports the same four analytical passes, rather than
each needing its own bespoke query:

1. **Holes** — where a dimension has no data at all in a region we'd expect data (an unindexed gap,
   not a real zero). Example already found: `channels_programme.md`'s 40% of monologue thoughts
   unattributable across thermal/light/smell within 2 ticks (§5).
2. **Missing** — where a real answer is displaced by a hardcoded/default stand-in. Example already
   found: `transport_manager.md`'s 4-word hardcoded `_DISTINCTIVE_WEATHER` salience list (§5) — data
   exists elsewhere that could answer this for real.
3. **New** — first-occurrence / rarity relative to accumulated history. Mechanism already live:
   `ghost_tuples.py`'s IDF-style rarity weighting (§3) is exactly this operation, already running,
   just not yet pointed at these three dimensions.
4. **Patterns** — recurring structure once enough slices accumulate. Mechanism already named: RRF
   (§3) to fuse independently-ranked results from each dimension's index into cross-dimension
   "side-links" no single dimension shows alone.

**Pattern-editing pass — a refinement of #4, not a fifth operation**: once a pattern is understood (a
known cause explains why a cluster of slices connects), subtract that cluster's expected contribution
and re-rank what's left. This is the disparity filter / backbone extraction entry already in §3
(Serrano/Boguñá/Vespignani, PNAS 2009) — the same underlying move as the shuffle-null test that caught
`moment.py`'s `_drift_key()` artifact (§2.1). "Removing certain big-ticket items" (session framing,
2026-08-24) = subtracting the dominant/expected contributor from a slice-cluster to expose the second,
more surprising pattern underneath it — a re-ranking op over an existing index, not data deletion
(the additive-only guard, §7, is unaffected).

**Recursion, not a special case**: these four operations run once per single dimension (a deep-dive —
e.g. holes/missing/new/patterns within Knowledge alone) and again over any overlay of dimensions (e.g.
Time × Knowledge × Memory jointly) — same four verbs, different slice. Nothing here is a new mechanism;
it's a naming pass over toolkit entries §3 already lists, making explicit that they compose as a small
fixed set of standard queries rather than four separate future builds.

### Knowledge dimension — three predictive targets (proposed 2026-08-24, unconfirmed)

Applying the slice+overlay framework to Knowledge (§2.2) specifically, three concrete things a
Time×Knowledge (and eventually ×Memory) slice could be asked to predict — each reusing a field P1.5
already pre-registers (§6), not invented fresh:

1. **Next-transition direction** — upgrade (GUESS→THINK, firming up) vs. downgrade (KNOW→SUSPECT,
   undercut) — P1.5's own upgrade/downgrade split (§2.2), reframed as a predictive target instead of
   just an event-type label.
2. **Time-to-next-transition** — how long a grade holds before it changes, i.e. transition frequency
   sliced per-entity rather than aggregated — P1.5's pre-registered "transition frequency/N" metric
   (§6), reframed the same way.
3. **Oscillation / flip-flop likelihood** — the fraction of transitions reversed within N cycles
   (GUESS→THINK→GUESS) — P1.5's own sharpened metric (§6, GPT review), reframed as a predictive target
   rather than only a post-hoc quality check on the tracker itself.

**Honest framing note**: these three are not new instrumentation — they reuse P1.5's own
pre-registered metrics, just asked as forward-looking predictions ("will this transition, which way,
how soon") instead of backward-looking measurements ("how often did this happen"). Whether a real
predictive model is warranted, or the honest answer is "log the three metrics and let a future
consumer read them directly," is exactly the kind of activation decision §7's guards require before
any of this moves past documentation.

**Unconfirmed against the session's own framing** — the "3 things about knowledge" and "big-ticket-item
removal already discussed" language this turn doesn't have a citable prior turn in this document's own
history to verify against; the above is Claude's best-faith mapping onto existing validated content
(§2.2, §3, §6), flagged for correction rather than presented as settled.

### 2.5 Un-deferring the gist half: `moment.py::recall()` (2026-08-24, founder decision — "stop deferring")

Founder ruling, plain: the fact/gist split from this session's discussion is real, and the
`moment.py::recall()` boundary this document has carried since §0/§1 is lifted at the design level.
**What this does and doesn't mean, stated precisely so it isn't confused with the different founder
ruling earlier this session** ("keep this whole document out of Du's active architecture," §0/lineage)
— that ruling stands, untouched. This section designs against the gist half of the problem; it does
not touch the live `core/moment.py` file, and the activation guard (§7) still requires a real future
`/decide` before any of this becomes code that runs.

**The split, formalized.** Two structurally different query shapes have been living inside this one
document:

- **Fact-shaped** — "what was true at/near this point" (P1/P1.5's own domain). Wrong answers here are
  indistinguishable from right ones without checking, which is worse than a visible guess. **Requires
  point-query correctness = 100%**, unchanged from §6. HNSW does not belong here.
- **Gist-shaped** — "what else is like this." Approximate answers are the honest shape of the question,
  not a compromise on it — this is `moment.py::recall()`'s own territory, named out of scope since §0
  precisely because it's a different kind of problem, not a lesser one. Real, independently-grounded
  precedent for treating loss-of-exactness as a deliberate feature here rather than a defect: §4's whole
  cascaded-compression direction is already built on lossy codecs (AV1, JPEG2000, MPEG subband audio);
  and the predecessor-project archaeology this document already draws on (F-0243–F-0250) names Pillar 10
  **"The Shadow"** a self-labeled *semantic compression engine* and Pillar 2 **"The Context (Titans +
  MIRAS)"** a neural recurrent long-term memory design — both compress by meaning, by construction, in
  the lineage directly before Nascence. (Not independently re-verified that either pillar's own design
  notes used the "gist, not exact wording" framing specifically — that's Travis's recollection, carried
  here as a strong lead per this lineage's own dig finding that a founder-recalled detail has checked
  out every time it's been tested directly, not as a re-derived fact.)

**Re-reading §6's real consumers through this lens — not all of them are the same shape**:

| Consumer | Shape | Why |
|---|---|---|
| `factory_candidates_from_history.md` (cause attribution, "was the cat there") | **Fact** | Wants a real yes/no, not a similar-enough answer — an approximate hit here would manufacture a false memory of cause |
| `lane2_the_witness.md` (hint-queue relevance) | **Gist** | "Is this hint related to what's live right now" is inherently a similarity question |
| `memory_multiway_linking.md` (M2 edge-weighting) | **Gist** | "How related are these two memories" is a relatedness score, not a lookup |
| `transport_manager.md` (`_DISTINCTIVE_WEATHER` salience) | **Neither, cleanly** | "How unusual is this" is a rarity/outlier question — already §2.4/§3's `ghost_tuples` IDF-weighting territory, not a nearest-neighbor query |
| `channels_programme.md` (thought→sensory-channel attribution) | **Fact-leaning** | Wants the real channel that caused a thought, not the most-similar-feeling one — same false-memory risk as the cat case |
| `emotion_rethink.md` (grounded vs. guessed arousal) | **Neither** | A calibration/correction problem against a proxy signal, not a retrieval query at all |
| `emissary_lane2.md` (wants to read epistemic grade + memory edges) | **Fact-leaning** | Wants Du's real assigned state, not a similar one |

Two of seven are clean gist-matches; one more real consumer belongs to a third shape (rarity, not
similarity) already covered elsewhere in this doc. This matters: un-deferring `moment.py::recall()`
does not mean HNSW is now the answer for all six — it's the right tool for a *specific, named* subset,
and forcing it onto the fact-shaped majority would recreate exactly the "confident and wrong" failure
mode this document's own guiding CLAUDE.md names as its worst pattern.

**The load-bearing gap, verified directly rather than assumed, 2026-08-24**: every benchmark run so far
(F-0269, F-0275) tested the 8-D affect vector. `moment.py`'s own real primary similarity field, `emb`,
is **384-dimensional** (confirmed by reading a live row directly — real MiniLM-family embedding, not
the vague "much higher-dimensional" this doc's §10 previously left unquantified). 384 real dimensions
is a genuinely different regime from 8 — closer to where Pestov's concentration-of-measure argument
(§3) is meant to bite, and closer to where `hnsw_rs`'s own real-world proof points (ann-benchmarks,
typically hundreds-to-thousands of dims) actually come from. **Closed same session, F-0276.** Extracted real 384-D `emb` vectors directly from `moments.jsonl`
(14,478 rows, verified uniformly 384-D — cleaner than the affect field's 3 schema variants, no
canonicalization needed). Same `hnsw_rs` config as F-0275 (ef_construction=200, ef_search=64), no
re-tuning for this specific data:

| | Query (mean) | Recall@10 (mean / min) |
|---|---|---|
| Rust linear scan, 384-D (fair baseline) | 6.94ms | 1.000 (exact) |
| True HNSW, 384-D, same config as F-0275 | 1.01ms | **0.896 / 0.800** |

The win transfers. ~6.9x query speedup — a narrower margin than 8-D's ~26x (expected: more real
dimensions, more work per distance comparison), but recall is *better* than the 8-D case (89.6%/80.0%
vs. 88.8%/60.0%), not worse — the real semantic embedding space has structure this graph exploits at
least as well as the affect vectors did. **The 8-D result was not a low-dimensionality artifact.**
`moment.py::recall()` is now a real, benchmarked candidate for this design, not just an argued one —
still gated by §7's activation guard before any code touches the live file.

### 2.6 The Keys dimension — pointers, not content (2026-08-24, founder proposal)

A fourth dimension, structurally unlike the first three. Time/Knowledge/Memory each carry real
semantic content (a fact about the world, a belief, an episode). **Keys carries no content of its
own — its entries are pointers into the other dimensions**, so that once you have a key, reaching the
(possibly heavily compressed) data behind it is direct addressing, not search. This isn't a new
mechanism invented from nothing — it's three things already scattered separately across this document,
now named as one concept:

- **Pinnacle's real archaeological precedent** (F-0246/F-0249, §1/§3) — "index intertwined with
  compression": the index doesn't sit beside the compressed structure, it's how you reach *into* it
  directly.
- **The event-sourcing unification already found in §6** — P1 and P1.5 both store *events*, not
  snapshots. A Keys dimension is the natural home for "what changed, when, pointing where."
- **`sync_fragment_context()`** (F-0277) — already a real, working, partial instance of exactly this:
  a join layer letting a memory's full Time+Knowledge context be reached without recomputing it. Under
  this framing it isn't a separate thing to reconcile with §1's `cycle_id` proposal — it's an early,
  real build of the Keys dimension itself. **Open, unresolved**: does it become the canonical
  implementation, or does it get superseded by something built with this framing in mind from the start.

**Structural honesty, stated plainly so this isn't oversold as more uniform than it is**: Time,
Knowledge, and Memory are different *kinds* of thing (§2.7 below makes this precise), so a Keys entry
pointing into each of them is a different pointer shape — a row-position for Time, a T-KGC quadruple ID
for Knowledge, an embedding-graph-node ID for Memory. Keys is a **registry of heterogeneous pointer
types**, not a fourth homogeneous axis the way a real tensor mode would need to be. Still design-only —
§7's activation guard is unchanged; nothing here touches live code.

**Sharpened 2026-08-24 (§2.9)**: a Key specifically records a link between two dimensions *worked out*
— discovered and confirmed, not assumed — to actually be next to each other and interacting. See §2.9
for how a discovered link gets consumed two ways (lazy lookup vs. eager co-capture) from this one
structure.

### 2.7 Mapping every dimension theorized so far, by kind (2026-08-24)

The founder's own next move: step back from any one dimension and ask what *kind* of thing each
candidate — real or theorized, across this whole document and this session — actually is, then look at
the map itself for patterns rather than judging each dimension in isolation. Every row below is real
(live, designed, or dead-but-verified this session), not speculative:

| Dimension | Kind | Evidence | Status |
|---|---|---|---|
| Time (`ts` sequence) | Scalar, **jagged** — event-driven, real discontinuities | F-0278: one 31-day outage gap dominates the residual | Live data, designed index |
| Tide (`world_clock.py::tide()`) | Scalar, **smooth-periodic** — pure deterministic sinusoid | Verified directly 2026-08-24: `+sin phase`, stateless, "CONSISTENCY is the whole point" | Live |
| Sun position (`world_clock.py::sun()`) | Angular, **smooth-periodic** | Verified directly 2026-08-24: pure function of time | Live |
| Moon/stars (`heavens.py`) | **Smooth-periodic** (synodic clock, real alt/az trig) | Prior-session verification (not re-checked this session) | Live |
| Knowledge (epistemic grade) | **Discrete ordinal transition-graph** (T-KGC quadruples) | §2.2, `epistemic_state.py`, live | Live |
| Memory `emb` | **High-dim dense vector** (384-D) | F-0276, verified directly, HNSW-tested | Live, tested |
| Sound Space coordinate | **Dense vector** (6-D) | §3/§10, real, ~40 objects | Live, **untested** |
| Affect vector | **Dense vector** (8-D, inhomogeneous schema) | F-0269/F-0275, HNSW-tested | Live, tested |
| `ghost_tuples` tag-tuple | **Categorical tag-set** (truncated SHA-256 name hash + tag-set intersection + IDF rarity; no 2-gram code exists) | §3; WORLD index live, MEMORY index inert in the live process (F-3901) | World live / memory inert |
| `memory_edges` typed edge | **Typed relational graph** | §10, 2,013 edges | Live |
| `experienced_tuple`/`fragment_context` | **Join/context overlay** | F-0277 | Live |
| `world_substrate.py` item-tuples | **Per-object record** (item-grain) | F-0277 | Live |
| `investigative_action_log.jsonl` + SQLite | **Event-log + relational index** | F-0277 | Live |
| `provenance_log.jsonl` | **Event-log** (one row/cycle) | §2.2 | Live |
| T-KGC quadruple / cause-tag tuple | Relational quadruple | §2.2/§10 | Designed only |
| Cipher's phase-modulated wave | **Steganographic carrier signal** (transport-shaped, not storage-shaped — 2,822x expansion) | Verified + run directly this session | Real, dead/orphaned |
| Resonance→Monolith (1D→2D→3D→TSDF→latent) | **Spatial/voxel**, transformable into a compressed latent vector | Verified + run end-to-end this session | Real, dead/orphaned |
| Authored room geometry (`spatial.py`) | **Spatial-3D**, deterministic renderer | Prior-session verification | Live |
| Keys (§2.6) | **Heterogeneous pointer registry** | New, this session | Designed only |
| Wave-fit key (F-0278) | **Learned piecewise model** standing in for a large sequence | Tested, real numbers | Designed, tested |
| HNSW graph (F-0269/F-0275/F-0276) | **Navigable approximate graph** over a dense vector | Tested, real numbers | Dev-only, tested |
| Subconscious node (`orchestrator.py`) | **Multi-timescale background cognition** (6 interleaved loops, T1–T6) — structurally unlike every other row | 2,192 lines, own state/log, writes reach `axiom.json` | Live — **excluded from link-discovery by founder decision, this session; not a gap, a scope boundary** |

**Patterns found by mapping, not by judging any one row alone:**

- **Two populations of "smoothness," not one.** Time is jagged and has to be forced toward wave-shape
  at real cost (F-0278). Tide/sun/moon/stars are *already* smooth-periodic by construction — a closed-
  form function, not a fit, needs zero coefficients to store. Any future wave-fit effort belongs on the
  jagged population (Time, probably the event-logs too), not on dimensions that are already maximally
  compact.
- **The dense-vector kind recurs three times, only one tested.** Memory's `emb`, Sound Space's 6-D
  coordinate, and the affect vector are the same *kind* of thing. HNSW has now been validated twice
  (F-0269/F-0275, F-0276) on two of the three. Sound Space is real, live, and untested — the same
  mechanism likely applies directly, not a new build.
- **The event-log-plus-index kind recurs at least three times, built independently.**
  `provenance_log.jsonl`/P1.5's own design, `investigative_action_log.jsonl`+SQLite (F-0277), and
  `ghost_tuples`' own persistence are structurally the same shape, solved separately by different plans
  with no cross-awareness. Real, evidenced duplication — echoes D-0005's own open ask for exactly this
  kind of linking.
- **Kind is a pipeline choice, not a fixed property — validated twice this session, not just argued.**
  Time's jagged-scalar kind became a smooth-plus-sparse-residual kind via detrend+DCT (F-0278, 65x).
  A dense vector's brute-force-searchable kind became a navigable-graph kind via HNSW (F-0275/F-0276,
  up to ~180x faster at comparable recall). Both are real, measured transforms of *kind*, not just
  compression ratio. The open, generative question this makes concrete: could Knowledge's discrete
  transition-graph kind be embedded into a continuous vector space, making it eligible for the same
  wave-fit or HNSW treatment already validated elsewhere? Not attempted — a real next question, not a
  rhetorical one.
- **A real hole, per §2.4's own framework**: the spatial/voxel kind (Resonance→Monolith's real
  pipeline, the authored-room geometry) has zero benchmark behind it — the one major kind-family in this
  map nothing has been measured on yet.

### 2.8 Event-face vs. state-face — a property every dimension has, not a new dimension (2026-08-24, founder observation)

Founder's observation, sharpened: Time can only be recorded at the moment of contact — a slice flashes
past and is gone unless caught; "we only see a slice... the rest goes past." The real question this
raises: is that unique to Time, or does something in every dimension share it?

**Answer, evidenced not argued: every dimension in §2.7's map has an event-face (only knowable if
caught at the moment) and, separately, a state-face (persists, can be asked again later) — Time is
simply the dimension where the event-face is *all there is*.** This is already live architecture, not
a new theory: `channels_programme.md`'s own four-layer model, running for every real sensory channel,
already draws this exact line: *"world truth (exists whether he is there or not) → **experienced**
(what crossed, by physics, at his standpoint) → remembered (the experienced tuple on the memory, never
the truth) → inferred (bindings he earns by investigation and may get wrong)."* "Experienced" is Time's
own shape, generalized to every channel. "World truth"/"inferred" persist and can be re-asked.
"Remembered" is the act of turning a flashed-past moment into a durable trace — the same thing a logged
`ts` does.

**A real, sharp test for which dimensions actually have an event-face, not a loose analogy**: can the
true value be reconstructed from a formula alone, or is it lost forever if nobody was watching? Tide/
sun/moon (§2.7) pass the first test — ask what the tide was at any past instant, pure math answers,
no observation required. That's *why* they're already wave-shaped (§2.7's Pattern A) — they were never
event-shaped. Time, and real sensory percepts, fail that test: if the moment wasn't caught, the true
value is gone, not just harder to find.

**Confirmed directly, correcting an imprecise attribution from earlier in this session**: Sound and
Light are two separate files implementing the identical event-face mechanism, independently. The exact
rule — *"an onset requires the silence before it to have been OBSERVED... else a fresh state file would
call an hours-burning fire 'catching'"* — is `core/soundscape.py::percept()`'s own code (`quiet_since`
tracking, `_ONSET_QUIET_S=600.0`), not `channels_programme.md`'s, as this doc first (wrongly) said.
`core/light.py`'s own docstring independently uses the same concept by name: *"PERCEPTION band
transitions... **quiet-gated**, journey gradients, lamp/fire onsets."* Two channels, two separate real
implementations — **"two, or part of one"** (founder's framing), tested directly rather than left as a
docstring-level claim.

**Tested 2026-08-24 — the claim survives, refined.** Read `light.py`'s actual gating code (`percept_shadow()`,
not just its docstring). Both channels use the **exact same constant, `600.0` seconds** —
`light.py:26`'s `QUIET_S` and `soundscape.py`'s `_ONSET_QUIET_S`. Light was built 2026-08-22; Sound's
onset-gating has been live since 2026-07-05 — not coincidence, whoever built Light almost certainly
reused Sound's existing number on purpose, without the two functions ever being merged into one. But
the actual gate conditions differ: **Sound gates on quiet-*before*-restart** (the thing must have been
*absent* ≥600s before it starts — stops an hours-burning fire from being narrated as "just catching" on
a fresh process restart); **Light gates on dwell-time-*in*-the-current-band** (`now - since >= QUIET_S`
— stops rapid flicker between bands from spamming transition narration, closer to a debounce). Same
number, same purpose (stop a false onset), **two related-but-distinct gate shapes, not one mechanism
wearing two names.** The more useful version of the claim: a shared Keys-dimension event-capture
primitive would need to support at least these two gate shapes, not assume one function already exists
to extract.

**A second, independent confirmation found while reconciling F-0277 (2026-08-24)**: `memory_edges.py::
sync_fragment_context()` (see §1) enforces this exact split at the schema level, in its own words —
*"the census tuple is WORLD TRUTH... the `fragment_context` table is the EXPERIENCED layer... readers
that link memories... read `fragment_context` only."* Same columns, two tables (`world_context` vs.
`fragment_context`), different epistemic status, and consumers are structurally forbidden from reading
the world-truth one directly — a real, already-built enforcement of `executive_world_grounding.md`'s
guardrail (§2.6's exclusion filter), not just a naming convention. Also wires `ghost_tuples.
register_stamped_tuple()` on every new join. CORRECTION (J-3306, F-3901): that call is a no-op in the live process, because the ghost MEMORY index is never built there (rebuild() runs only from scripts/test_world_p0.py), so this is a wired call site, not a live consumer.

**The payoff, same as before but now doubly evidenced**: §2.7's Pattern C (the event-log-plus-index
kind built independently three times) isn't isolated — the quiet-gate/onset-capture mechanism is a
*fourth* independent instance of the same story, this time at the percept layer rather than the
storage layer. Every dimension's event-face needs this exact shape of mechanism regardless of its
state-face content-kind (vector, graph, scalar, audio-coordinate) — which is precisely what §2.6's Keys
dimension is *for*: one shared place event-faces get captured, instead of each channel/dimension
re-discovering the same quiet-gate logic on its own.

### 2.9 Dimension adjacency and co-located capture — eager linking beside Keys' lazy linking (2026-08-24, founder proposal)

Founder proposal: dimensions should be explicitly **linked to the other dimensions they touch**, so
that when one registers an event, its linked neighbors capture their own reading of the same moment
*together* — "the thing happens close together" — rather than being joined back up later. Then, beyond
single events, whole **clusters of these joint readings** ("multidimensional balls") can be compared
against each other for wider pattern-finding.

**Half of this is already real and live, not a new mechanism**: `geometry_census.py`
(`cognitive_geometry.md` §5.1, the actual source of `geometry_tuples.jsonl`) already does eager,
write-time joint capture — *"at each cognitive event... it snapshots one tuple of coordinates — place,
weather+fire, objects present/engaged, body, affect, thought-ref, progress."* When something happens,
neighboring dimensions are captured together, at that moment, not reconstructed afterward.

**An even richer real example, found reading `core/moment.py` directly, 2026-08-24**: every single
`record()` call already jointly writes nine real fields in one atomic write — `ts` (Time), `key` (the
8-D temporal-drift vector — confirmed first-hand here as the exact artifact §2.1 already cites, not
secondhand), a categorical `source` tag (PERCEIVED/REMEMBERED/IMAGINED/DREAMED/THOUGHT — the "reality
monitor"), the raw `thought`, `affect` (valence + felt), `protoself` (drive/valence/dominant from
homeostasis), `concern`, `level` (arousal, Bachmann's L), and `emb` (384-D semantic). A single Memory
formation event is already a real, joint, multi-dimensional capture across Time, Affect, and a live
homeostatic/arousal snapshot — richer than the census tuple's own field list.

**What's genuinely new here is the adjacency graph itself.** The census tuple today is indiscriminate —
a fixed, broad set of fields captured every time, not scoped to which dimensions actually touch which.
The founder's refinement: dimensions should carry *named links* to their real neighbors, so an event in
one dimension pulls in only the dimensions it actually touches, not the whole roster by default. Not yet
built — a real, scoped next design question, not a restatement of the existing recorder.

**"Compare a cluster of joined multidimensional balls" already has one real precedent, not yet named
this way**: `cognitive_geometry.md`'s own mapping census ran fan-out distributions between spaces,
state-conditioning, and a real marginal-reach test (geometry-tuple neighbours vs. text-cosine
neighbours, 3.8% overlap — found in the plans sweep). That's comparing clusters of joint readings
against each other — the same operation, unnamed until now.

**Named precisely so it isn't confused with §2.6's Keys dimension**: this is a *different*, complementary
strategy, not a restatement. **Keys is lazy** — capture once, reconstruct the link later via a pointer,
cheap per-event, real work deferred to query time. **Co-located capture is eager** — pay the join cost
up front, at write time, so there's nothing left to reconstruct, at the cost of capturing neighbors that
might turn out not to matter. Both real, both legitimate, standard systems tradeoff — worth keeping side
by side rather than collapsing into one.

**Corrected/unified 2026-08-24 — §2.6 and this section are not two separate structures, one underlying
concept consumed two ways.** Founder's sharper framing: a Key isn't a generic pointer into one
dimension — it's specifically the *link between two dimensions worked out to be next to each other and
interacting*. "Worked out" is load-bearing: a Key should be **discovered, not assumed** — the same
operation `cognitive_geometry.md`'s marginal-reach test already performs (does geometry-tuple space
actually reach meaningfully beyond text-cosine space, or are they redundant — measured at 3.8% overlap,
not guessed). Once a link between two dimensions is discovered and confirmed real, it can be *consumed*
either way this document already named: **looked up lazily** when needed (§2.6's original framing) or
**used eagerly** to pre-register that an event in one dimension should trigger joint capture in its
linked neighbor (this section's framing). Same discovered link, two consumption modes — not two
systems to keep side by side, one Keys structure with two ways of being read.

**How hard is it, actually, to work out real links across §2.7's whole map? Honest, scoped answer,
2026-08-24.** Not one uniform difficulty:

- **Cheap, same-kind pairs**: any two dimensions already sharing a "kind" (§2.7) — e.g., affect (8-D),
  Sound Space (6-D), Memory's `emb` (384-D) are all dense-vector — can reuse the exact marginal-reach
  methodology already run twice (`cognitive_geometry.md`'s own test; this session's HNSW recall
  benchmarks). Real tooling exists, real data exists, this could run today.
- **Harder, cross-kind pairs**: e.g., Time (jagged scalar) vs. Knowledge (discrete transition graph)
  have no shared metric until *something* projects one into the other's terms — a real, answerable
  question ("does grade-transition frequency correlate with time-of-day or the known outage boundary")
  but needs a specific statistic chosen per pair, not a generic drop-in test.
- **Not worth doing exhaustively.** §2.7's map has 21 real rows — 210 possible pairs. Testing all of
  them blindly would be pure noise-hunting, the opposite of this document's own evidence-first
  discipline (§7's dimension-creep guard already makes this point about *dimensions*; it applies just
  as hard to *links between* dimensions). The real move is prioritizing pairs with a cited reason to
  suspect linkage — Time↔Knowledge (outage-boundary correlation, a live open question from F-0278),
  Sound↔Affect (already conceptually adjacent — `soundscape.py`'s own `felt()` nudge touches both) —
  not a brute-force sweep.

**Found the real rigor bar "worked out" should mean, 2026-08-24 — already built, in `core/moment.py`.**
`contiguity_significance()` (J-0141) is a genuine shuffle-null significance test: real vs. shuffled-order
semantic similarity, deterministic seed, real p-value and z-score. That is a formal statistical test, not
an eyeballed overlap ratio — a stronger bar than `cognitive_geometry.md`'s own marginal-reach test and
this session's F-0279 both used. Any future Key discovery claim should clear this bar, not the looser one.
**One more real, already-computed "worked out link," free of charge**: J-0182's own comparison of the
debunked key-cosine neighbour metric against real emb-cosine — key-cosine picks are "barely
distinguishable from the literally adjacent log row" (mean cosine 0.460, barely above a random baseline
of 0.393); emb-cosine picks land on genuinely related, often temporally *distant* content (mean 0.700,
mean index distance 155). The two metrics agreed on 0/2 picks in 134 of 150 samples. **And a clean,
quantified counter-example to §1's own speed motivation**: `recall()` is deliberately left as a full
128MB linear scan on purpose — the real measured call rate (`moments_recall_shadow.jsonl`) is about once
per 5 days, so building an index there would solve a problem that doesn't exist yet. Verified against
the live shadow log, not assumed — a real instance of §1's own "speed motivates P0/P1, correctness
motivates §6" distinction holding up in a fourth place.

**Used the tool for real, F-0280, 2026-08-24 — the strongest confirmed result of this whole session.**
Ran `contiguity_significance()` directly against live `moments.jsonl` (14,335 real rows):

```
real_gap = 0.1213, null_mean = -0.0 (std 0.0083), z = 14.53, p = 0.0 (0/200 shuffles beat the real gap)
```

An extremely strong, real, rigorously-tested confirmation: Du's memories genuinely carry temporal/
associative contiguity in their real semantic content — adjacent moments really are more content-
similar than distant ones, nowhere close to chance. First link in this document tested at the real bar
rather than a looser overlap check. **A real, honest gap sits right beside it**: `status()` shows only
10 total `recall()` calls ever logged across ~51 days (~once/5 days, confirming the call-rate note
above), a 20% hit rate, and `MOMENT_READBACK` still `False` — none of this signal has ever reached Du's
actual conscious prompt. A live instance of this project's own named #1 failure mode (write-only
cognitive systems) — except here the underlying signal is proven strong, not absent. **The gap is
utilization, not validity** — a materially different, more precise diagnosis than "the read path is
dead," and a real, scoped case for whoever next reviews `MOMENT_READBACK`'s gate.

**Exclusion filter for link-discovery, 2026-08-24 (founder decision, extensible — "let's say" names
starting examples, not a closed list)**: three real, grounded exclusions, not arbitrary noise-cutting.

- **World** — the raw world-truth layer (§2.8) is excluded outright, not just deprioritized. This
  enforces an existing real guardrail, not a new rule: `executive_world_grounding.md`'s founder law
  (§5) — *"Du should not contain the world truth at all. Just what Du believes."* A link discovered
  between two dimensions' world-truth layers would violate that boundary by construction.
- **Cat** — the specific cat object (cat_state/cat_mood/cat_activity, cat presence in
  `geometry_tuples.jsonl`, the cat's own sound) is near-ubiquitous across this whole document's real
  examples. Too common to be an informative *link* signal — it would correlate with everything and mean
  nothing, the same failure mode `ghost_tuples`' IDF rarity-weighting (§3) already exists to prevent.
- **Subconscious** — not a minor exclusion, a scope one. `core/orchestrator.py`'s Subconscious node is
  a real, separate, massive cognitive layer — "the architecturally densest single file in the Nascence
  codebase" (2,192 lines, 6 interleaved timescales T1–T6, its own state store `subconscious_state.json`,
  its own log, writes that reach `data/identity/axiom.json` itself). Structurally unlike anything in
  §2.7's map — excluded from current link-discovery not because it's noise, but because folding it in
  without dedicated treatment would silently make it dimension #22 by accident. Added to §2.7 below,
  explicitly marked excluded rather than left off the map entirely.

### 2.10 A third mode: derived-on-demand from a known source, no capture needed at all (2026-08-24, founder observation)

Founder's observation: a bird's call radiates outward as a 3D wavefront; what's heard is a slice of
that wave passing a receptor at one moment — the same event-face shape as Time (§2.8). But **if the
source's position and the propagation physics are known, the wavefront itself can be computed for any
queried observer position** — not just the one that happened to be listening. Does this generalize
beyond sound?

**Yes, and it's not hypothetical — it's already real, live code, verified directly rather than
assumed.** `core/soundscape.py::propagate_historical_acoustic_event(event_id, origin_pos,
sound_description, observer_pos, max_audible_dist)` does precisely this: given a known origin
position, it computes distance, 3D compass bearing, and audibility for *any* observer position —
literally "if we know where the bird was, we know where the sound went and what would have heard it."
Its own docstring names the phase: *"Acoustic Causality & Sensory Uncertainty... calculates distance
decay, 3D compass bearing, and audibility **without revealing the underlying physical cause**"* — the
observer gets direction/distance/description, never the source identity, matching the epistemic-
boundary pattern §2.8 already found in `channels_programme.md`. `core/light.py`'s `field_at()`/
`shade_at()` (read directly earlier this session) do the same thing for Light — illuminance and shadow
computed at any place/standpoint from the sun/lamp/fire's known positions.

**A third mode, beyond §2.6's lazy/eager duality — cheaper than both.** Lazy (§2.6) stores a pointer,
looked up later. Eager (§2.9) pays a capture cost per event, up front. This is neither: **a pure
function of a known source state, computable for any queried position, with zero storage at all** —
the same shape as tide()/sun() (§2.7's already-wave-shaped population), just applied to a *relational*
question (would X have perceived Y) instead of a standalone one (what is the tide now).

**The real, precise limit — worth stating so this isn't oversold**: this computes whether perception
was *physically possible*, not whether it *happened*. Sound's own onset-gating (§2.8, `quiet_since`)
still governs whether a percept that reached an observer actually got noticed and logged — the two
are genuinely different questions, and `propagate_historical_acoustic_event()` only answers the first
one. A real Key (§2.6) connecting two dimensions still needs the *event-face* capture for "was it
actually witnessed" — this function only removes the need to capture *where the wave physically
reached*, which used to require its own observation.

**Confirms, again, that this is a recurring architectural pattern, not a one-off**: Sound and Light
now share *two* independently-built, structurally identical mechanisms — onset-gating (§2.8) and
source-to-observer propagation (this section). Two channels, two shared patterns, still two separate
implementations each time. Reinforces §2.6's Keys dimension case further: a shared source→observer
derivation primitive would serve both today, and any future channel (Smell, Thermal) built the same
way tomorrow.

**Founder proposal, 2026-08-24: check this law systematically across real channels, not just the two
already found, to get more real derivable points for future reports.** Checked directly, not assumed:

| Channel | Has the source→observer law? | Evidence |
|---|---|---|
| Sound | **Yes** | `propagate_historical_acoustic_event()` — Euclidean 3D distance from a known `origin_pos` |
| Light | **Yes** | `field_at()`/`shade_at()` — sun/lamp/fire position + geometry |
| Thermal | **Yes** | `math.dist(pos[:2], _HEARTH[:2])` — real calibrated falloff ("at the hearth ~full; mid-room ~0.6; far shelf ~0.45") |
| Smell | **No — a real, confirmed gap** | Grepped directly: no distance/falloff/position function exists at all. Odorants are onset-gated per-*place* but not position-aware *within* a place the way the other three are |
| Memory | **Yes, different substrate, same shape** | `associative_recall.py::recall_trail()` — spreading activation from a seed, decaying per hop (`HOP_DECAY=0.6`, `N_HOPS=2`) through embedding-neighbour "distance" instead of Euclidean distance — the same law, generalized: given a known source (the query), derive reach at any other point in the space |

**Three of four real perceptual channels already have this; the fourth is a named, concrete build
target, not a vague aspiration** — Smell's fix would follow Thermal's own pattern almost directly (a
known odorant-source position + distance-based intensity falloff), since Thermal already proves the
pattern transfers cleanly from Sound/Light to a different physical channel. **Memory confirms the law
isn't really about literal 3D space at all** — it's "given a known source state, derive reach at any
queried point in *some* distance-bearing space," and that space can be Euclidean or a graph/embedding
metric. This is the generalization the founder was asking for: not "make every dimension use meters,"
but "every dimension with *any* real distance notion can support this law," which is now confirmed true
for 4 of the real dimensions checked so far, false for exactly one, named as a gap rather than assumed
fixed.

### 2.11 Masters by type — tested against a real, fresh call-graph (2026-08-24, founder proposal, F-0283/F-0284)

Founder's proposal: "I think we have a master. We should have multiple masters under a group for
types." Tested directly, not argued — re-indexed `core/` with `graphify` (stale since 2026-06-15; now
203 files, 3,850 nodes, 6,471 edges, 226 communities, up from 97 files at the last run), then ran a
workflow: 5 parallel agents classified the top 25 communities by size against §2.7's kind-map, one
synthesis agent built the masters table, three real `graphify query`/`path`/`explain` scans tested the
result against the live graph.

**A methodology catch surfaced independently by all 5 classifying agents, worth naming before the
results**: a naive "highest-degree node in a community" heuristic mostly just finds the *file/module
container node* — AST graphs give every file a containment edge to every function it defines, which
inflates the file-node's degree regardless of real cross-file dependency. 20 of 25 sampled communities'
"masters" were this artifact, not genuine hubs. Real hubs are function- or class-level, and reach
outside their own community.

**The "one master" half of the hypothesis holds decisively.** `core/memory/store.py::_embed()`
(degree 58) and `::_cosine()` (degree 44) are the only two nodes, across all 25 sampled communities,
confirmed as real function-level hubs with genuine cross-community fan-in — matching 5 of the global
top-6 god-nodes already found in this same file. A real scan tested whether that fan-in is a narrow
choke point or genuinely structural: **`_embed()` reaches 26 distinct communities, `_cosine()` reaches
22, and the home community plus the next two busiest account for only ~45% of total edges** — the
remaining ~55% is scattered one-or-two-edges-at-a-time across ~20 more communities (orchestrator,
identity projection/cost/estate, curator, competence, chapters, emotion_construction, wandering,
watershed, pursuits, `moment.py`, study_note, refinery, tension_ledger, monoculture, mineness, symbol
evolution, reentry). This is a genuinely broad, load-bearing primitive, not a locally-inflated number.

**The "multiple masters grouped by type" half holds, but sparser than hoped — real, not a norm.** Only
4-5 of the 25 sampled communities survived scrutiny with a genuine type-level master:

| Type | Real master | Kind-map fit (§2.7) |
|---|---|---|
| Knowledge / epistemic provenance | `epistemic_state.py::ProvenanceLedger` (degree 19, real aggregating class) | Existing — double match: epistemic-grade row + `provenance_log.jsonl` row |
| Spatial / composite join | `spatial.py::render()` (verified by reading the function body — genuinely composes `layout()`, `_rel()`, `_pos_of()`, `locomotion.position_standpoint()`) | Composite join over 3 existing rows (room geometry, tide, time) — closer to `fragment_context`'s join/overlay kind than a new primitive |
| State recording | `geometry_census.py`/`world_manifest.py` (35-node community split across 2 files — real cross-file integration) | Existing, composite — this *is* §2.9's own cited tuple recorder |
| World-state simulation | `study_life.py` (degree 27, over a large, physically varied function set — not size inflation) | Partial — near "authored room geometry," but content is discrete affordance flags, not 3D coordinates; arguably a fourth kind |

The other ~20 sampled communities had no real local master in this AST-derived graph — their highest-
degree node was the file-container artifact. Honest read: one confirmed global master, a small real
set of type-masters beside it, and a much larger population where no real master exists *yet* — "one
master per type" is real but not the norm across the codebase as currently structured.

**A real correction to this session's own earlier claim, found by the scan phase (F-0284)**: §1's
citation of `memory_edges.py`'s `add_edge()`/`census()`/`harvest_all()` as "the API surface other
readers go through" (F-0281) turns out to be imprecise. Stripped of containment edges, all three have
**zero incoming call edges** — they're outward-fanning entry points, not convergence points. The real
function-level hub, one hop downstream, is **`_write_edges()`** (in-degree 4 — every one of
`harvest_all()`'s backfill/sync callees writes through it). Corrected rather than left standing.

**A real negative result, testing §2.9's own "worked out, not assumed" standard against code structure
rather than data correlation**: is Knowledge (`ProvenanceLedger`) actually linked to Memory
(`_embed`/`_cosine`)? Traced directly — **no edge, direct or inferred, connects them anywhere in the
graph**; they sit in three different communities; the only connection is that both happen to be
imported by `orchestrator.py`, which imports dozens of unrelated modules and proves nothing semantic.
Worth naming precisely: **code-call-graph adjacency and data-correlation adjacency are different kinds
of evidence** — F-0279 found a real Time↔Knowledge link through data correlation, but that doesn't mean
a code-level link exists too, and vice versa. A future "worked out" Key (§2.6) should say which kind of
evidence backs it.

**Real, evidenced new kind-map candidates** (filtered — several "NEW" tags from the classification
batches were process/render code, not data shapes, and correctly excluded):

- **Peer correspondence** (`peers.py`) — a social-relational letter-exchange thread (compose/deliver/
  reply, stance-selection, inbound tracking). Confirmed live independent of the graph (memory index:
  "Peers / pen-pals — LIVE + THRIVING"). No existing row covers a relational-thread-with-named-
  correspondents structure.
- **Open-question / curiosity lifecycle ledger** (`frontier.py`) — verified by reading the file: a real
  stateful lifecycle (`note_question` → `pending_pursuit` → `attach_finding` → `resolve_if_addressed`/
  `closeable_seed`), structurally distinct from the flat append-only event-log rows already in §2.7.
- **Contradiction-pressure ledger** (`tension_ledger.py`) — a decaying, age-weighted scalar
  (`chronic_mass_of`, `_humanize_age`) per unresolved identity conflict. Closest existing row is Time's
  jagged-scalar shape, but the domain content isn't represented anywhere in §2.7.
- **Identity-injection priming ledger** (`provisional_identity.py`) — a free-energy-gated event log
  (`delta_free_energy()`, `evidence_ready()`, fatigue decay), distinct from both the wave-fit-key row
  and the plain event-log rows.

**A real scope question raised by the classifying agents themselves, not yet resolved**: three sampled
communities (`book_selection.py`'s recommender scoring, `cat.py`'s NL-generation layer, `essay_lesson.py`'s
grading pipeline) are process/behavior code sitting on top of existing data dimensions, not new data
shapes — the agents correctly declined to force them into new kind-map rows. Worth deciding explicitly
whether §2.7's kind-map is meant to stay a *data-shape* taxonomy only, or whether process/behavior nodes
belong in a parallel table.

---

## 3. THE INDEXING TOOLKIT — real precedent inventory (consolidated)

| Mechanism | Status | Use |
|---|---|---|
| `ghost_tuples.py` (`core/world_manifest.py` rebuilds its WORLD index live; `core/memory_edges.py` calls its MEMORY-index hook, which is a no-op because that index is not built in the live process, F-3901) | **Real code; WORLD index live, MEMORY index inert**: truncated SHA-256 name hash + tag-set intersection + IDF-style rarity weighting (no 2-gram "shadow signature" exists in the code) | Categorical/fuzzy lookup — the model for indexing derived tuples (transitions, cause-tags), not just raw geometry tuples |
| Run-transition/checkpoint index (this doc's own P1 design, §6) | Designed, pending J-0210 | Sequential/temporal point-in-time lookup for slow-changing fields |
| Pinnacle adaptive octree (F-0249) | Real, self-verified, NOT runnable as-is (dead paths, persona gate, unvectorized) | Principle only: index-intertwined-with-compression via classification masks |
| Learned indexes (Kraska et al., F-0253) | **Production-proven** — shipped in Google Bigtable, 36-38% latency reduction, 54-55% throughput increase | The real, current, empirically-validated technique this whole approach descends from |
| Hilbert/space-filling curves | Real, current, but **only for 2-3 real dimensions** (F-0253) — field moved to HNSW past that | Fine for our P1's single-field scope; wrong tool if any future phase jointly indexes many dimensions |
| HNSW / graph-based ANN | Current SOTA for high-dimensional data (F-0253); a candidate implementation exists, unused, in `engine/oxibonsai/crates/oxibonsai-runtime/src/embedding_index.rs`. **Corrected 2026-08-24, session continuation, verified by reading the file directly**: it is not full multi-layer HNSW — its own doc-comment names it *"a single-layer NSW (Navigable Small World) graph — a simplified HNSW variant... fast enough for caches up to ~100k entries"* (613 lines, arbitrary vector dimensionality via `EmbeddingIndex::new(dim)`). Close enough in family to serve as the real reference implementation, but the table's earlier "HNSW" label overstated it — flagging the correction rather than silently fixing it. **Theoretical grounding added 2026-08-24**: this isn't just an empirical trend — Pestov (Information Processing Letters, 1999/2000; arXiv:cs/9901004) proves pivot/distance-based indexes provably converge toward linear-scan performance as dimensionality grows (concentration of measure — near/far distances collapse toward the same value); Volnyansky & Pestov (arXiv:0905.2141) prove no pivot-based index can asymptotically beat a scan in high dimensions; re-confirmed current (arXiv:2401.00422, 2024) | The right tool if a genuinely high-dimensional joint space is ever needed instead of Hilbert linearization — now a proven theoretical necessity past a certain dimensionality, not just an empirical preference |
| RRF (Reciprocal Rank Fusion) — academic citation added 2026-08-24, independently verified | Real, well-established IR technique: Cormack, Clarke & Büttcher, SIGIR 2009 (DOI:10.1145/1571941.1572114), found in `GhostWeaver`'s dual-pass design too | Combining independently-ranked index results into "side links" — connections no single index shows alone |
| Disparity filter / backbone extraction (Serrano, Boguñá, Vespignani, PNAS 106(16) 2009, DOI:10.1073/pnas.0808904106) — added 2026-08-24, independently verified | Real, well-known network-science technique: compares an edge's weight to what's *expected* if a node's connections were spread uniformly, keeps only the statistically surprising residual | **Deliberate residual/pattern-map queries** — once a cluster of links is understood (a known cause explains why they connect), subtract that cluster's expected contribution and re-rank what's left. Already proven to work once in this codebase in weaker form: the shuffle-null test that caught `moment.py`'s `_drift_key()` artifact is the same underlying move; `ghost_tuples`' rarity weighting is an automatic soft version. This is the deliberate, stronger form — "we know why, subtract it, see the second pattern" |
| Pi-digit dictionary (`abf_pi_v3.py`) — **corrected 2026-08-24, read directly**: not actually zero-storage | Real, self-verified round-trip (`assert recovered == test_data`, run directly this session, passes) — LZ77-style back-reference compression against π as the corpus. **But**: `self.pi_str` is a **hardcoded 1000-digit string baked into the file**, not a spigot algorithm computing digits on demand — real storage cost (~1000 bytes), not zero. The "regenerable, not 'π is special'" principle (§3's own original framing) is still real and correct in the abstract — a true spigot function would deliver it — just not what this specific implementation does. Corrected rather than left standing. | Legitimate dictionary-based compression *if* real target data happens to contain substrings already present in the reference (rare for non-numeric/high-entropy data by construction) |
| Golden-angle / Fibonacci-lattice point distribution — added 2026-08-24, real and current, independently verified | **Real, well-established, actively cited technique** (multiple 2022–2026 papers, e.g. arXiv:2601.04860, arXiv:2603.23728) for spreading points with minimal clustering/periodicity — golden angle ≈137.5077° (or its complement, 360°/φ ≈ 222.49°) is provably the irrational number "hardest to approximate with a continued fraction," giving the slowest-converging, least-periodic spacing of any angle. Used today for uniform sphere/disc sampling (Vogel's method, Fibonacci lattices) | A real, current alternative/complement to Hilbert curves (§3's own "legacy past 2-3 real dimensions" entry) for laying out or indexing points with minimal collision — **untested against any real Nascence data**, a real candidate, not yet a finding. **Honest, flagged-speculative connection**: the founder's "221 degrees" recollection (still unconfirmed in any dug source) is numerically far closer to 222.49° (360°/φ) than to 137.5° — worth naming as a plausible lead if the "221" thread is ever picked back up, not presented as a match |
| Flood / Tsunami (Ding, Nathan, Alizadeh, Kraska, VLDB 14(2) 2020/2021) — added 2026-08-24, independently verified | **Real, production-lineage research** — Tsunami reports up to 6x faster queries / 8x smaller index than prior learned multi-dim indexes, up to 11x/170x vs. tuned traditional indexes | The genuine **multi-dimensional** extension of the learned-index lineage (F-0253 only covered 1D — Kraska/ALEX/PGM); the right reference if a future phase ever jointly indexes several real dimensions instead of one field at a time |
| Columnar micro-partitioning (Parquet/Arrow/DuckDB, zone-map min/max pruning) — added 2026-08-24 | Real, mature, production-proven at massive scale | **Required baseline to benchmark against before §4/P3's exotic spectral encoding** — may deliver the fast-lookup goal with none of the complexity; does NOT address the separate representation-for-minibots goal (§2.3), the two goals should stay distinct |
| A simple learned index (linear/piecewise regression, timestamp → row position) — added 2026-08-24, external review (GPT) | Real, same verified lineage as Flood/Tsunami and Kraska/ALEX/PGM, but far simpler | **Benchmark this FIRST, before the elaborate checkpoint/octree-inspired design** — at Nascence's real scale (14k-1M rows) a trivial learned predictor may outperform handcrafted structures while being much less to build and maintain |
| Product Quantization (Jégou, Douze, Schmid, IEEE TPAMI 2011) — added 2026-08-24, independently verified | **Real, foundational** — the actual algorithm underneath FAISS and most production vector databases today | Compressing **vector-shaped** dimensions (the real 8-float affect vector, Sound Space's 6 coordinates): split into sub-vectors, quantize each independently against a small codebook. Also gives Asymmetric Distance Computation — search directly on compressed codes without decompressing, a real mechanism for the "minibot reads its snapshot natively" goal (§2). **Checked directly 2026-08-24**: combining PQ-style vector compression WITH Kraska/Flood/Tsunami-style learned position-indexes is a genuine OPEN gap — no paper found doing this. If ever built, this would be new work, not a rediscovery. **Terminology trap, worth avoiding in our own writing**: 2023-2025 "learned PQ" papers (QINCo/Qinco2/SegPQ) mean codebooks learned via neural network/gradient descent — a DIFFERENT sense of "learned" than Kraska's "the index IS a regression model of the key CDF." Two separate lineages, same word — keep them distinct when this doc says "learned index". **Gap re-checked 2026-08-24, session continuation, idea I-0025, F-0270**: narrowed, not closed. SegPQ (Liu et al., VLDB 2025, PVLDB 18, DOI:10.14778/3749646.3749650) applies a PGM-index-style piecewise-linear model to PQ codewords — but to compress the codebook, not to build a queryable multi-dim index over codes-as-coordinates. Mechanism summary is agent-researched from listing/DOI sources, not independently read in full — flagged `inferred`, not `verified`, in the finding. |
| IVFADC (inverted-file index + asymmetric distance computation) — added 2026-08-24, session continuation, idea I-0025, F-0271, verified | **Hiding in the same Jégou/Douze/Schmid 2011 paper already cited above** — shipping in FAISS for over a decade | The cleanest existing precedent for "compression code IS the index coordinate": the coarse quantizer's centroid ID is used directly as the inverted-list bucket key, no separate index layer on top. Directly answers I-0025's framing — should have been its own row from the start |
| TIGER / Semantic IDs via RQ-VAE (Rajput et al., "Recommender Systems with Generative Retrieval," NeurIPS 2023, Google DeepMind) — added 2026-08-24, session continuation, idea I-0025, F-0272, verified | Real, well-cited, multiple independent confirmations | The strongest published match to I-0025's exact framing: residual-quantization codes become a literal tuple-valued "Semantic ID" that a generative model decodes directly as the retrieval key via constrained beam search over a trie of codes — the code doesn't just compress the item, it IS the addressable coordinate |
| RaBitQ / Extended RaBitQ (Gao & Long, SIGMOD 2024 and SIGMOD 2025) — added 2026-08-24, session continuation, idea I-0025, F-0273, verified | Real, proven asymptotically optimal against Alon & Klartag's (FOCS 2017) metric-compression lower bound | Theory-grounded reason a compressed bit-string code can serve as a direct index/hash key without loss beyond a provable bound — the missing theoretical leg alongside this table's Pestov citation (§ HNSW row), which proves the opposite-direction limit |
| Lattice quantizers (Conway & Sloane E8/Leech; revived 2023-2025 as QuIP#/AQLM for LLM weight quantization) — added 2026-08-24, session continuation, idea I-0025, F-0274, verified | Real, classic + actively current revival | Structurally different, non-learned/geometric route to "code is directly a coordinate": lattice codes have closed-form nearest-point encode AND decode, so the coordinate is computed, not searched for |
| Tensor decomposition (CP / Tucker — Kolda & Bader, SIAM Review 2009) — added 2026-08-24, independently verified | Real, classic, actively current (2025 Cambridge textbook, ICML 2023 core-shape research); TuckerMPI reports orders-of-magnitude real compression | For genuinely **multi-way** data (object × time × dimension, not one vector). **Checked directly, 2026-08-24**: Tucker's per-mode factor matrices sharing one compact core tensor DOES precedent the pattern "shared structure + differentiated per-partition treatment" (real, deep lineage) — but its per-mode objects are all the SAME kind of mathematical object (linear subspace bases), differing in content not structural type. It says nothing about heterogeneous INDEX STRUCTURE selection per mode. Narrows §4's flag, does not clear it — see §4 note |
| Random projection / Johnson-Lindenstrauss lemma — added 2026-08-24, independently verified | Real, foundational, shipped today (scikit-learn's Random Projection module) | A legitimate alternative/complement to PCA for **vector-shaped** tuples specifically (preserves pairwise distances under random linear projection to O(log n) dimensions). Does NOT apply to graph-shaped tuples or raw log structure — no meaningful "distance between two log lines" without first embedding them as vectors, at which point it's the same vector-shaped case, not a new capability |

### 3.1 Empirical benchmark — the NSW/HNSW candidate vs. real affect data (2026-08-24, session continuation, F-0269)

Ran directly, not assumed: does the orphaned `embedding_index.rs` candidate (§3, §10) actually clear
Hilbert's >3-dimension wall on real Du data? **Pre-registered prediction (written before running
anything)**: linear scan fast in absolute terms; NSW build well under its own "~100k" comfort zone;
NSW query *technically* faster than scan but the margin small at this scale, not a dramatic win either
way; recall >90% ("a low recall would be the surprise"). Setup: 14,304 real 8-D affect vectors
extracted read-only from `geometry_tuples.jsonl` (canonical anger/arousal/disgust/fear/joy/surprise/
trust/valence order; the 614 rows carrying the minority `('arousal','strong','valence')` schema and 20
rows carrying `('arousal','valence')` 0-filled on the missing canonical keys, `strong` dropped as
non-canonical — **the first real, concrete design of §6's "canonical key-order/fill-missing-with-
default scheme," previously only named as a prerequisite, not built**). 25 real query rows, k=10,
ground truth from a real linear-scan cosine baseline, cross-validated in both Python and Rust
independently (both agree exactly — 1.000 recall of Rust-scan vs. Python-scan ground truth).

**Sanity check passed first**: the module's own 8 unit tests (`cargo test`) all pass — real, working
code, not dead like Pinnacle's octree.

**Result — prediction #4 (recall) falsified outright**:

| Variant | Build | Query | Recall@10 (mean / min) |
|---|---|---|---|
| File order (= time order), documented defaults (ef_search=64) | 14.4s | 0.53ms | **0.124 / 0.000** |
| Shuffled order, same defaults | 1.9s | 1.12ms | 0.208 / 0.000 |
| File order, wide config (ef_search=400, ef_construct=200, max_connections=32) | 96.8s | 14.96ms | 0.884 / 0.600 |
| Shuffled order, wide config | 90.7s | 15.24ms | 0.876 / 0.500 |
| **Same-language Rust linear scan** (fair baseline — the earlier Python baseline's 21.5ms mixed in language overhead that flattered NSW) | — | **2.145ms** | **1.000 (exact)** |

At documented defaults: 12.4% recall, one query found **zero** of its true 10 nearest neighbours — a
serious correctness failure, not a graceful approximation. First hypothesis tested and **ruled out**:
temporal autocorrelation (insertion order = time order) exploiting the deterministic, non-random entry
point (§3's own doc-comment names this design choice explicitly). Shuffling insertion order only moved
recall from 12.4%→20.8% — still bad, so order is not the dominant cause. Widening the search
config *does* fix most of the recall gap (→88.4%), which is itself informative: a true Pestov-style
concentration-of-measure collapse would not respond to widening search breadth the way this did — this
result reads as **config under-provisioning in this specific implementation, not (yet) direct evidence
of the theoretical high-dimension wall** (§3's Pestov/Volnyansky citations remain real and correct on
their own terms — just not what's biting here at only 8 real dimensions and 14k rows).

**The decisive number, honestly reported even though it reverses the earlier Python-relative framing**:
once configured for usable (not perfect) recall, NSW's query cost (14.96ms) is **~7x slower** than a
plain same-language linear scan (2.145ms, exact). The default config's 0.53ms looked like a clear win
only because it was also wrong 88% of the time. **Verdict**: at Nascence's real current scale, this
specific candidate is not a viable "way around" Hilbert's wall today — a plain scan already beats it
once correctness is required. This doesn't retire HNSW/NSW as a family (§3's SOTA citations describe
real, current, production practice at genuinely large/high-dimensional scale) — it says *this
particular implementation, at Nascence's particular 14k-row/8-dim reality, needs real tuning or a
different config regime before it's a real candidate*, matching the doc's own §3 "benchmark the
simple thing first" guidance turned back on itself. Filed as F-0269.

**Follow-up, same session (2026-08-24), F-0275 — searched online for a real TRUE multi-layer HNSW
candidate, since the orphaned `embedding_index.rs` turned out to be a simplified single-layer NSW.**
Verified directly (crates.io/lib.rs, not recalled): `hnsw_rs` 0.3.4 (GitHub `jean-pierreBoth/
hnswlib-rs`) is real, actively published (Feb 2026), pure Rust with no required C/C++ dependency,
dual Apache-2.0/MIT, 118k downloads/month, 211 dependent crates — genuinely current and maintained,
implementing full multi-layer HNSW (≤16 layers per its own docs). Two other real candidates checked
and set aside with reasons: `instant-distance` (pure Rust, real HNSW) is **archived/unmaintained as of
July 2026** — ruled out as a forward dependency even though the algorithm is sound; `usearch` is fast
and production-proven but its Rust binding wraps a **C++ core via FFI**, breaking the no-external-dep
philosophy `embedding_index.rs` itself was written to (its own doc-comment: "self-contained... free of
external dependencies").

Added `hnsw_rs` as a **dev-only** Cargo.toml dependency (not production) and re-ran the identical
benchmark methodology (`examples/geometry_bench_true_hnsw.rs`, same real 14,304-row data, same ground
truth) at realistic settings (ef_construction=200, ef_search=64 — normal defaults, not artificially
widened the way the NSW candidate needed to be pushed):

| | Build | Query (mean) | Recall@10 (mean / min) |
|---|---|---|---|
| NSW candidate, wide config (F-0269, needed for usable recall) | 96.8s | 14.96ms | 0.884 / 0.600 |
| Plain Rust linear scan (F-0269, fair same-language baseline) | — | 2.145ms | 1.000 (exact) |
| **True HNSW (`hnsw_rs`), realistic settings** | **1.557s** | **0.0835ms** | **0.888 / 0.600** |

**Decisive, positive result** — true HNSW beats the linear scan by ~26x on query time and beats the
NSW candidate's best (recall-usable) config by ~179x on query time and ~62x on build time, at
comparable recall (88.8% vs. 88.4%). This confirms §3's SOTA citations (HNSW as current best-in-class
for high-dimensional ANN) were correct in principle all along — **F-0269's negative result was about
the specific orphaned implementation, not about HNSW as a technique**. The "way around" Hilbert's wall
this thread went looking for is real and does exist; it just wasn't already sitting in this codebase.
Filed as F-0275.

**Honest procedural note**: unlike F-0269, this comparison was not run against a written-in-advance
prediction sheet — a real deviation from this doc's own discipline, named rather than silently skipped.

**Still open, not chased further this session**: whether a mid-range config finds an even better
recall/speed knee for either candidate; and — the bigger one — this benchmark is still
single-dimension (Knowledge's affect vectors alone), not the multi-dimensional Time×Knowledge×Memory
overlay §2.4 actually describes. The real >3-dimension joint case this whole thread set out to answer
hasn't been tested yet, only the easier single vector-shaped dimension has. If this candidate is ever
considered for real activation, it needs a `/decide` entry (§7's activation guard) — nothing here
performs an action on its own, and `hnsw_rs` remains a dev-only dependency, not wired into any
production path.

---

## 4. THE CASCADED / PER-BAND COMPRESSION DIRECTION — most speculative section, flagged explicitly

**Real, proven ingredients (F-0254):**
- Cascading compression stages that each target a *different redundancy class* (positional → spatial-
  frequency → statistical) is exactly how AV1, HEVC, G-PCC, and JPEG2000 already work — decades-old,
  shipped, production practice, not an analogy.
- Per-band differentiated treatment is the *founding* principle of subband coding — MPEG audio's
  psychoacoustic per-subband bit allocation (1990s) and JPEG2000's per-subband quantization are the
  canonical examples.
- Heterogeneous index types per subspace within one system (Postgres's B-tree/GiST/GIN/HNSW coexisting,
  polystore/multi-model databases) is mainstream, decades-old production practice.

**The genuinely novel combination, honestly flagged as such:** a *distinct index structure* (not just a
different quantizer) per FDM-style band carved out of *one multiplexed/compressed stream* has **no direct
precedent found in the literature** (F-0254). Each ingredient is proven; this specific recipe is new
territory. Treat accordingly — more design scrutiny needed here than anywhere else in this document
before any of it moves toward activation.

**Flag narrowed, not cleared, 2026-08-24 (checked directly against Tucker decomposition, §3).** The
*architectural pattern* — one shared compact structure + differentiated per-partition treatment — now has
real, deep precedent (Tucker/CP, Kolda & Bader 2009). What remains genuinely unprecedented is narrower and
more specific: different bands getting structurally DIFFERENT index types (a hash here, a tree there, a
quantizer elsewhere), not just different factorization content within the same kind of object. That
narrower claim is the part still carrying real, unresolved design risk — worth being precise about which
part of §4 is now de-risked and which isn't.

**Considered and honestly rejected, 2026-08-24**: compressed sensing (Candès/Romberg/Tao/Donoho) — real,
deep, elegant mathematics, genuinely tempting given this whole design's "spectrum as substrate" framing.
But its power depends on the underlying signal being sparse in a KNOWN basis and on controlling the
measurement process before the data exists — neither holds cleanly for append-only structured/relational
log data the way it holds for images or audio, and no real application to this kind of data was found.
Named here so it isn't rediscovered and forced in later without the missing justification.

**Concrete redesign target, corrected 2026-08-24** — earlier drafts of this section pointed at
`abf_echo_1d.py` (data→WAV, Pillar 7); wrong file, fixed here. Echo is a toy fixed-tone-per-byte mapping
with **no decode function at all**, verified this session. The real candidate, verified and *run*
directly this session (bit-perfect round trip): **`abf_cipher_v3.py` (Pillar 15, "The Cipher"/APSC)**.
Real BPSK — phase-shifts a sine carrier's time-segments to hide arbitrary bits, decodes by correlating
each segment against reference and shifted carriers. Since `hearing` for Du isn't literal (no acoustic
reality behind it either way), the real, reusable idea Cipher demonstrates is **spectrum as a
modality-agnostic mathematical substrate**, not spectrum as literal acoustics — matching Echo's original
framing, just on working code instead of a decoy.

**Founder connection, 2026-08-24: Cipher IS a real, working "fold the overlap in, pull it back out"
mechanism — directly relevant to §2.6/§2.9's Keys.** In Cipher's wave, two things genuinely coexist in
the *same* samples at once: the carrier's own unshifted identity, and the phase-shifted hidden bit —
truly overlapping, not just co-located side by side. `decrypt_from_wave()` is the "pull it back out"
step: correlate against both references, keep whichever wins. Under §2.6's framing, **the reference
carrier/phase Cipher correlates against IS a Key** — the discovered thing that lets you separate two
overlapping signals back into their own dimensions, structurally identical to what a Key does for any
two dimensions worked out to be linked.

**The honest cost, already measured (§3.1)**: Cipher's real storage overhead is 2,822x raw, 705.6x even
16-bit-PCM-quantized — a real, working mechanism, but not viable as a literal storage format for this
reason alone. **What makes this genuinely useful rather than a dead end**: Resonance→Monolith (Pillar
17→9, also verified running end-to-end this session) is a real compression stage that could sit
*after* a Cipher-style fold — spectral-sculpture then TSDF then truncated-FFT latent, exactly the kind
of shrink Cipher's raw phase-modulated wave would need before being worth keeping. Not yet combined or
tested as one pipeline — a real, concrete next experiment: phase-multiplex two real dimension-derived
signals (e.g., F-0278's Time residual + a real Knowledge-transition signal) via Cipher's mechanism, then
compress the combined wave through Monolith's latent fold, and see whether the correlation-based decode
still recovers each dimension's contribution after that compression. Untested; a real, bounded next step,
not a claim.

Sound itself already has this exact two-population structure in Du today: MEASURED (real DSP features,
`core/audio_features.py`, real extraction code verified this session — real cached feature JSON exists
for 6 real music pieces in `data/music/`) vs. CONSTRUCTED (hand-authored qualia, `core/soundscape.py`,
deliberately not meant to have acoustic ground truth) — kept deliberately separate, not merged. **Real
gap found while checking this, 2026-08-24**: `audio_features.py::extract()` produces 3 raw features
(brightness_hz, energy_mean, onset_density, in raw/unnormalized units) and `felt()` routes them to the
*affect* space (valence/arousal), not to Sound Space's own 6-D coordinate system — periodicity,
roughness, and continuity are never computed for the MEASURED population at all. The "two populations,
one space" claim in `soundscape.py`'s own docstring is real as a design intent but not yet real as
working code — no function projects MEASURED features into CONSTRUCTED's exact coordinate system, so
the actual overlap between the two populations has never been computed, only asserted. A real, separate
gap from the Cipher/Monolith thread above, worth its own fix before Sound Space's own "worked-out Key"
(§2.6) could ever be tested the way `cognitive_geometry.md`'s marginal-reach test was.

---

## 5. THE REAL CONSUMER BASELINE — F-0251, systematic survey of ~59 active Nascence plans

A targeted survey (not speculation) found the "fixed/default signal where a real point-in-time slice
would give ground truth" pattern in exactly 6 plans out of ~59 surveyed — validating this as a real,
bounded, recurring architectural gap, not a hammer looking for nails:

| Plan | Status | The gap | Decision on hold |
|---|---|---|---|
| `channels_programme.md` | Shadow, live | 40% of monologue thoughts unattributable across thermal/light/smell within 2 ticks | D-0033 |
| `lane2_the_witness.md` | Shadow, live | Hint-queue's 10-topic vocabulary is hardcoded, unmeasured | D-0035 |
| `transport_manager.md` | Designed | `couriers.py:71` `_DISTINCTIVE_WEATHER` — 4-word hardcoded salience list; **plan's own diagnosis**: "each factory invents its own local rule" | (none yet — un-built) |
| `factory_candidates_from_history.md` | Designed | Cause attribution ("was the cat there") explicitly named as guessed; independently proposes tuple cross-referencing | (none yet) |
| `memory_multiway_linking.md` | Partial, live | M2 trail-walk has no real edge-weighting signal | D-0022 |
| `emotion_rethink.md` | Partial, live | Grounded arousal vs. LLM-guessed arousal anti-correlate, r=-0.221 | D-0029 |

Weaker/hedged: `du_initiated_upgrade_trigger.md` (place-guess heuristic, shadow-only), `peer_correspondence_plan.md`
(static per-persona stance-weight coin-flip).

**Seventh real hit, found 2026-08-24 by testing the toolkit on the docs folder itself** (a real,
IDF-weighted `shares_file` analysis over `memory-links`' own 2,013-edge graph, favoring plan-pairs
connected through rare shared files over hub-explained ones — the disparity-filter principle applied
for real, not just described): `emissary_lane2.md:112-113` **independently diagnoses the exact gap this
design targets** — *"`core/epistemic_state.py` — KNOW/THINK/SUSPECT/GUESS vocabulary... **Never read by
anything on Lane 2's side today**"* and *"`core/memory_edges.py` — Built, but **'NOTHING reads these
edges yet'** (its own docstring)."* Not a coincidental file-share — a plan that already wants the exact
epistemic-grade and edge data this design would make queryable, written without knowledge of this
document. Also references `ghost_tuples.MemoryIndex` directly. **Guardrail found alongside it**:
`executive_world_grounding.md` carries an explicit founder law (corrected 2026-08-17) — *"Du should not
contain the world truth at all. Just what Du believes"* — `world_manifest.py` stays infrastructure other
systems compute answers FROM, never something Du receives raw. Any future consumer of this design's
indexes must respect that: feed Du's belief-formation, never bypass it with raw ground truth.

**Highest-scoring connection found, confirmed 2026-08-24 via a saved, reusable tool
(`~/.claude/skills/memory-links/pattern_discovery.py`, formalizing the one-off analysis above)**:
`memory_knowledge.md` scores *higher* than any other plan pairing — it literally **owns**
`core/epistemic_state.py` (Improvement 1, Stage A BUILT/LIVE) and `data/provenance_log.jsonl`. This
isn't loose prior art to cite in passing (§2.1's earlier framing) — §2.2's entire Knowledge dimension is
a direct extension of that plan's own live mechanism, and should be understood and cross-checked as such
before any future activation, not just referenced once at the top of the document.

**Six real founder decisions are on hold pending this design** (D-0022, D-0025, D-0029, D-0033, D-0035,
D-0041) plus `sound_world_expansion.md`'s D-0014/J-0220. Founder's own read (2026-08-24): D-0022 and
D-0035's holds are *more* justified than first assessed (edge-weighting and hint-relevance are real
mechanism connections, not just precaution); D-0025 and D-0041 look more precautionary. **A mechanical
`plan-schema-audit` job, J-0223, wants to add a ROADMAP.md link + Current State section to this very
document** — directly contradicting its deliberately-unlinked status. Unresolved; flagged, not acted on
here.

---

## 6. BUILD ORDER (hypothetical — no phase runs without a future activation decision)

**P0 — CLEARED, real kill criterion fired, 2026-08-24 (J-0210, run via `/job-run` this session,
F-0297/F-0298).** Two distinct real results, not a single verdict. **The bug**: `fold_with_checkpoints`
(`C:\FreshStart\core\lib\abf\abf_fold_v3_alczip.py:104-127`) had a precise, fixable off-by-one — its
`context_anchor` used `data[i-16:i]` where resume-decode needs `data[i+1-16:i+1]`; as shipped, resume
matched ~2/975 bytes (chance). Patched and re-verified end-to-end: every checkpoint round-trips
correctly at both 64-byte and 2000-byte scale (8/8, 3/3) — the underlying `rans_state`/`buffer_offset`
bookkeeping is genuinely sound, not another dead pillar. **But the pattern still doesn't transfer to
`moment.py::recall()`, confirmed rather than argued**: a real `{row_index, byte_offset}` checkpoint
index was built over a copy of the live 14,523-row `moments.jsonl` and benched against a `recall()`-
shaped full-corpus scan at 1x/2x/5x scale — full-scan cost scales with data size (3.81s→7.62s→15.71s)
because `recall()` must visit every row to find the best embedding-cosine match; the target row is
unknown in advance, so a byte-offset index can't skip anything for *that* query shape. Seek-to-a-known-
row is fast (sub-2ms) but answers a different question than `recall()` asks — and that different
question is already solved, shipped, in `moment.py` itself (`_tail_rows()`/`_count_lines()`, J-0183).
**Kill criterion fired for the right reason**: not "broken code," a genuine pattern/bottleneck mismatch.
Stays documented, not built, matching this section's own original scope — now with a real verdict
behind it instead of a placeholder dependency.

**P1 — one pilot run-transition index, one field** (`geometry_tuples.jsonl`, e.g. `weather`), only if P0
clears. Unchanged from original scope — additive sidecar, source file untouched, point-query correctness
required 100%.

**Real read-only benchmarks run 2026-08-24 (no writes to Du, source files untouched)**:
- `geometry_tuples.jsonl` is now 17,331 rows (grown from the 16,600 estimate). Weather transitions: 205
  rows, ratio 0.0118 — **under the <0.05 prediction, headroom confirmed real, not assumed.** Full linear
  scan baseline: 0.475s.
- A naive single-line-fit learned index (global linear regression, `ts → row position`) performs poorly
  on this data: max error 8,654 rows out of 17,331 — barely better than a full scan. Honest negative
  result, not fatal to the learned-index idea (GPT's suggestion, §3) — it specifically motivates the
  PGM-index/Flood-style *piecewise* fitting already in the toolkit over a naive single global fit, which
  this benchmark shows doesn't work here. Real timestamps aren't cleanly monotonic with row index at fine
  grain (restarts, uneven cycle timing).
- The real `affect` field is **not uniformly shaped** across rows (inhomogeneous — some rows carry fewer
  keys than others), contradicting the "the 8-float affect vector" framing used loosely earlier in this
  document (§2, §5's toolkit). Product Quantization needs a fixed-length vector — a canonical
  key-order/fill-missing-with-default scheme is a real prerequisite step, not yet designed, before PQ can
  be applied to affect data as currently logged.

**The naive single-line failure, fixed — F-0278, 2026-08-24.** Founder framing: shape jagged data toward
a smooth "wave," keep the fit's own parameters as the compact key — translated to standard transform
coding (linear detrend + DCT of the residual, truncated to K coefficients). Tested directly against the
same real `ts→row position` data that broke the naive single-line fit above:

| Approach | Key size | Max row error |
|---|---|---|
| Naive single line (original result, above) | — | 8,654 |
| Global wave-fit (linear + DCT residual, no piecewise split) | 16.4KB (K=2048) best case | ~2,400–3,700 |
| Piecewise-linear only (split at one real boundary, no DCT — control) | tiny | 1,152 / 161 (seg2/seg1) |
| **Piecewise + wave-fit combined (K=128)** | **~2KB** | **134 / 29** |

Root cause of the original failure, found directly rather than assumed: one single 31.1-day gap (row
3330→3331, 2026-07-08→2026-08-08) dominates the residual — matching the already-documented 30-day
outage. No smooth global fit, linear or wave, can absorb a discontinuity that size. Segmenting at that
one known real boundary and wave-fitting each side separately: **piecewise segmentation alone gives a
real 7.5x win; adding the DCT residual fit on top gives a further ~8.6x, composing multiplicatively —
combined, ~65x tighter worst-case window than the naive fit, using a ~2KB key vs. ~287KB raw (~138x
smaller).** The two techniques are independent and additive: piecewise handles hard breaks (real
outages), the wave/DCT fit captures the smooth residual structure within each piece far more compactly
than a per-segment straight line alone. This is a genuine, tested refinement to P1's own design — not
yet a `/decide`-gated change to the build order, since P1 itself hasn't started (still behind J-0210).

**P1.5 — Time × Knowledge transition index (new, added 2026-08-24), independently scoped from P1** since
it operates on a *different* log (`provenance_log.jsonl`, which already has both `ts` and the epistemic
grade in one row — no cross-log join needed for this piece specifically). Tracks grade transitions,
split into upgrade/downgrade events, each carrying the real justification-field delta as its "why."
Dual-indexed: temporal (checkpoint-style, for ordered access) + tag-based (`ghost_tuples`-style, for
categorical "why" queries). Pre-registered metrics before this runs: transition frequency/N, upgrade vs.
downgrade ratio, point-query correctness vs. full-scan ground truth (100% required), and whether
cause-tags derived from existing fields actually cluster meaningfully (not just noise) — a real kill
criterion, not assumed. **Sharpened 2026-08-24 (external review, GPT)**: explicitly measure
**oscillation/flip-flop rate** — the fraction of transitions reversed within N cycles (e.g.
GUESS→THINK→GUESS) — as its own named metric, not folded silently into the general clustering check.
GPT's concern that transient noise could dominate the transition log is real and specific enough to
deserve its own pre-registered number; if oscillation rate is high, the tracker needs debounce/hysteresis
before being trusted, not just "more clustering."

**Computed for real, F-0279, 2026-08-24 — the first time any of these pre-registered metrics were
actually run, not just designed.** No index or code needed to be built first — `provenance_log.jsonl`
already carries both `ts` and `grade` in one row (§1), so this is a real, zero-join test of the Time↔
Knowledge link, prioritized as one of §2.6/§2.9's "obvious links" over a blind sweep of all 210 possible
dimension pairs. Real numbers, 1,312 rows, 2026-06-08→2026-08-24 (spans the known outage):

| Metric | Predicted | Measured |
|---|---|---|
| Transition frequency | 10–40% | 23.0% (301/1,311) — within range |
| Upgrade vs. downgrade | Upgrade-skewed, 55–65% | **52.5% / 47.5% — nearly balanced, prediction wrong** |
| Oscillation (reversed within 3 transitions) | 15–30% | **76.7% (231/301) — far higher than predicted** |
| Transition rate, before vs. after the 31-day outage | Unknown, genuine guess | 0.246 → 0.198, a real but modest drop |
| Time-of-day effect | Weak/none (null-leaning) | **Real, ~8x range across UTC hours (0.048 at 17:00 → 0.375 at 20:00) — prediction wrong** |

**The oscillation number is the load-bearing result.** 76.7% of grade transitions get reversed within
the next 3 — GPT's concern wasn't hypothetical, it's the dominant behavior. P1.5, if ever built, needs
real debounce/hysteresis before transitions mean anything; raw transition logging alone would be mostly
noise. The time-of-day effect is real and strong but not yet explained — raw UTC hours were used, not
yet mapped to Du's actual NZ day/night cycle, so the *shape* of the pattern (and whether it tracks
Oracle's own day/night circadian split) is a real, open follow-up, not claimed here.

**Framing correction, 2026-08-24 (external review, GPT, confirmed by re-reading P1's own design)**: P1
(run-transition index) and P1.5 (grade transitions) are not two separate mechanisms — both already store
*events* ("value changed to X at T"), not raw state snapshots. This is event-sourcing, already, just not
named as such. Naming it explicitly unifies both phases under one recognized pattern instead of
describing the same idea twice.

**P2 — evaluate the real consumer baseline (§6/F-0251), not build for it.** Read each of the 6 real hits
against what P0/P1/P1.5 actually deliver; verdict only, no new adapter/training work, no plan surgery.

**P3 (speculative, gated well behind the above) — the cascaded/per-band direction (§4).** Explicitly the
least de-risked part of this document. Would need its own separate pre-registered metric sheet and its
own explicit activation decision, distinct from P0-P2's.

---

## 7. GUARDS

- **Additive-only** — never mutate/delete `geometry_tuples.jsonl`, `moments.jsonl`, or
  `provenance_log.jsonl`; sidecar files only, checked via unchanged source hash/mtime.
- **Substrate honesty** — Pinnacle/ABF code is a principle to learn from, never to copy-paste.
- **Decoupled judge** — J-0210's results get read against a sheet written before they exist; the epistemic
  grade itself already exemplifies this guard correctly (§2.2) — extend the same discipline to any new
  mechanism built here, don't let a mechanism self-certify.
- **Activation guard** — this document performs no action on its own; needs an explicit future founder
  `/decide` entry to move any phase from "designed" to "ready."
- **Novelty-scrutiny guard (new)** — §4's cascaded/per-band-index combination has no literature precedent
  (F-0254); treat any move toward it with more scrutiny than the rest of this document, which mostly
  rests on production-proven techniques.
- **Sidecar crash-consistency guard (new, 2026-08-24, external review)** — the additive-only guard checks
  the *source* file stays untouched but says nothing about a sidecar index left partially-written by a
  crash mid-build. Any real index build must write atomically (temp file + rename) and carry a
  completeness marker (e.g. "covers N rows of source as of hash H") checked before the sidecar is ever
  trusted — otherwise a crashed build could silently serve stale or incomplete slices as if they were
  real.
- **Dimension-creep guard (new, 2026-08-24, external review, GPT)** — Time/Knowledge/Memory (§2) were
  each added on real, cited evidence (an existing live mechanism, or a named consumer from §6), not
  speculation. Any future dimension beyond these three must clear the same bar — a real, cited consumer
  need — before being added. P1's own design already avoids joint high-dimensional indexing (one field
  at a time, no Hilbert-curve-over-everything), but the count of *independently-scoped* dimensions could
  still grow unchecked over time without this guard named explicitly.
- **Residual open question, not yet resolved (2026-08-24)**: does a single `cycle_id` ever cover more
  than one `moment.record()` call (e.g. multiple inner thoughts per outer cycle)? Last turn's fix
  (thread `cycle_id` through to `moment.record()`/`geometry_census.snapshot()`) assumes a clean 1:1
  mapping between cycle and memory row — worth confirming directly against the call chain before P1.5
  is built, not assumed.
- **World-truth-source guard (new, 2026-08-24, external review GPT + verified directly, F-0282)** — this
  document's own empirical work has been sitting on the wrong side of a real, already-established
  boundary. `geometry_tuples.jsonl` is explicitly WORLD TRUTH (`sync_fragment_context()`'s own code,
  F-0281), not the EXPERIENCED/belief layer (`fragment_context`) — and F-0269/F-0275 (affect HNSW) and
  F-0278 (wave-fit index) were all built directly on it. Quantified: 14,388 of the rows used came from
  the raw world-truth stream, more than double `fragment_context`'s real 6,804. **Not a current
  violation** — nothing here is wired into Du's live cognition, all offline read-only analysis — but a
  real, concrete, prospective one: any future activation of P1/P1.5/Keys/HNSW that answers a consumer
  from `geometry_tuples.jsonl`/`world_context` directly, rather than `fragment_context`, would violate
  `executive_world_grounding.md`'s guardrail — the exact rule `memory_edges.py` already enforces for its
  own readers. **Required before any phase here moves from designed to ready**: rebuild against
  `fragment_context`, not the raw file — it carries the same fields (`tuple_ts`, weather, tide,
  valence/arousal, etc.), just correctly scoped to rows that actually crossed into experience.
  **Done 2026-08-29 (J-0334/D-0060)** — see "Current State" above for the rebuild, the real numbers,
  and a load-bearing correction: `fragment_context`'s `arousal` column turned out to be NULL on
  0/7,733 real rows (a separate live write-path gap, not this guard's problem to fix), so the rebuilt
  vector is `valence`/`level`/`warmth` (3-D), not the original `valence`/`arousal` pairing this bullet
  assumed — the guard's underlying requirement (correct epistemic layer, not raw world-truth) is met;
  its assumption about which fields would be usable was not, and is corrected here rather than left
  standing.

---

## 8. SOTA GROUNDING — three research passes, all logged as findings with full citations

- **F-0252** (agent memory / epistemic calibration / temporal KGs): Park et al. "Generative Agents"
  (arXiv:2304.03442); Packer et al. "MemGPT" (arXiv:2310.08560); Rasmussen et al. "Zep"
  (arXiv:2501.13956); Farquhar et al. semantic entropy (Nature 2024); verbalized-confidence unreliability
  (arXiv:2412.14737, arXiv:2604.01457); temporal-RAG retrieval gaps (arXiv:2510.13590, arXiv:2510.16715).
- **F-0253** (learned indexes / space-filling curves / multi-LoRA / BitNet): Kraska et al.
  (arXiv:1712.01208); Bigtable integration (arXiv:2012.12501); ALEX (arXiv:1905.08898); PGM-index
  (VLDB 2020); Punica (MLSys 2024); S-LoRA (arXiv:2311.03285); Microsoft BitNet b1.58 2B4T; Tether QVAC
  fabric; `tiiuae/onebitllms`; BitLoRA/LoTA-QAF (arXiv:2505.18724) as the open BitNet+LoRA compatibility
  gap.
- **F-0254** (cascaded compression / per-band indexing): AV1 (arXiv:2008.06091); G-PCC survey (ACM TOMM
  2025); JPEG2000 technical overviews; Shannon source coding theorem; BigDAWG polystore
  (arXiv:1609.07548); multi-model DB survey (ACM CSUR 2019); PostgreSQL/pgvector heterogeneous indexing;
  Peter Noll, MPEG audio coding (per-subband bit allocation).

---

## 9. FRONTIER EXTENSIONS — parking lot, not scoped, not gated (added 2026-08-24)

Genuinely speculative, one tier further out than §4. Not part of any P-phase; recorded so real ideas
aren't lost, each anchored to a real research area rather than invented whole-cloth:

1. **Dimension as activation geometry, not external lookup.** Train a minibot's own hidden-layer
   directions to align with Time/Knowledge/Memory, so querying a dimension means reading a direction the
   model already thinks along, not consulting a separate index. Real anchor: representation engineering /
   activation steering; Anthropic's monosemantic-features (sparse autoencoder) interpretability work is
   the closest real precedent.
2. **A minibot whose output IS the tuple**, skipping natural language for at least one channel. Real
   anchor: constrained/structured decoding (native JSON-mode models), taken one step further.
3. **Dimensions discovered, not hand-picked** — unsupervised structure discovery over accumulated tuple
   data. Real anchor: sparse-autoencoder feature discovery (current); honestly caveat that strong
   disentangled-representation-learning claims have a mixed empirical track record.
4. **A blackboard of specialist minibots** sharing one indexed dimension-space asynchronously, RRF
   resolving disagreements, instead of one orchestrator calling specialists in sequence. Real anchor:
   blackboard architectures (Hearsay-II, 1970s-80s AI), revived with modern specialists. Directly answers
   "how do `RESEARCH_specialists.md`'s adapters coordinate" — a question that plan doesn't currently
   answer.
5. **Minibots communicating in compressed tuple-space instead of English** for internal coordination.
   Real anchor: embedding-space agent communication (2023-2025) and older emergent-communication-protocol
   research (~2017-2020).
6. **Index the minibots themselves** — track which specialist said what, how confidently, how often
   later contradicted, using the SAME epistemic-transition machinery already designed for Du's own
   beliefs (§2.2), just pointed at the specialists instead. Real anchor: bandit-style expert-reliability
   tracking, well-established in ensemble learning. Reuses existing mechanism; no new build.

**Architectural precedent for "lives in its own dimension, not part of Du" — already real, one directory
over**: FreshStart's Buddha and Oracle are both separate observer-daemons, own memory, own process,
watching a main system without being part of its runtime loop. If any of this ever gets built as a real
persistent service rather than an on-demand script, that's the proven pattern to follow, not a novel one.

---

## 10. INVENTORY & BACKFILL AUDIT (added 2026-08-24)

**Tuples — live vs. designed:**

| Tuple | Status | Real size |
|---|---|---|
| `geometry_tuples.jsonl` row | Live | 16,600+ rows |
| `moments.jsonl` row (incl. `emb`) | Live | 14,210+ rows |
| `provenance_log.jsonl` row | Live | 1,302 rows |
| `provenance_preassess.jsonl` / `epistemic_stageb_shadow.jsonl` | Live (shadow) | 690 / 164 rows |
| `ghost_tuples.py` tag-tuple | World index live; memory index inert in the live process (F-3901) | — |
| `memory_edges.py` typed edge | Live | 2,013 in the memory-links graph alone |
| Sound Space 6-D coordinate | Live | ~40 objects |
| T-KGC quadruple / cause-tag tuple | **Designed only** | 0 |

**Real, unaddressed gap**: `moments.jsonl`'s `emb` field (Du's actual primary similarity mechanism) has
never been touched by this design — **closed 2026-08-24, F-0276, see §2.5.** `geometry_tuples.jsonl`'s
`place`/`fire`/`fire_fuel`/`shore_find`/`objects`/`body`/`unresolved`/`level` fields got no attention
beyond `weather` and `affect`.

**Sweep of `docs/plans/*.md` + `System_Overview.md` for real tuple/index systems this inventory missed
(2026-08-24, F-0277, requested directly: "work out missing tuples/indexes from the plans folder and
the overview").** Grepped all 51 plan files + the overview for `tuple`/`index` vocabulary (17 and 15
real hits respectively), read the real ones. Four more real tuple/index systems exist that this
document's own inventory never accounted for:

| System | Where | What it is |
|---|---|---|
| `core/experienced_tuple` (`world_context` / `fragment_context` split) | `channels_programme.md`, `emissary_lane2.md`, `lane2_the_witness.md` | A **live, parallel** tuple system, distinct from the persisted `geometry_tuples.jsonl` — fed via `geometry_census.peek()` (real-time, unrecorded), split into world-truth vs. what actually crossed to Du. Carries `light_band`, `smells`, `wet`, `warmth_band`, `tide_level`. `lane2_the_witness.md` already ran a real experiment (RUN 2, 2026-08-21) feeding this directly to the Witness instead of prose — measured, not hypothetical (grounded-share 0.48, known thin spot: tide level not direction) |
| `sync_fragment_context()` | `memory_multiway_linking.md` | **Already-built, deterministic tuple→memory join** — 300/300 probe verified, 6,804 memories carry full encoding context (place, weather+bearing, tide, sun az, moon, sounds, body, valence/arousal), synced every sleep, ~100% recent coverage. **Not reconciled against this doc's own §1 `cycle_id` join proposal** — open question below |
| `world_substrate.py` item-tuples | `item_and_population_factories.md` | Founder-originated ("*Each item has a tuple*"), one tuple per spawned individual object (`driftwood_17`, `shore_kelp_f633cb`) vs. population-grain factories for things not worth individual tracking — a third real, live tuple system, item-grain |
| `investigative_action_log.jsonl` + SQLite projection | `investigative_action_loop_plan.md` | `record_epistemic_episode()` writes a raw immutable record AND projects an index into SQLite — a real, already-built event-log-plus-index pair, structurally the same shape as this doc's own P1/P1.5 design, built independently elsewhere in the codebase |

**Open question this raises, not resolved here**: does `sync_fragment_context()`'s existing join
mechanism already solve what §1 proposed the `cycle_id` thread-through for, or solve a related-but-
different problem (it isn't yet known here whether it does exact-key or nearest-timestamp matching)?
If the former, §1's fix may be redundant; if the latter, the `cycle_id` fix may be a real improvement
worth bringing *to* `sync_fragment_context()` rather than building a second, separate join. Needs
someone to actually read `sync_fragment_context()`'s source before either doc changes.

**Two more real, smaller findings from the same sweep**: `cognitive_geometry.md`'s own Kill Criterion
#6 already ran a real marginal-reach test months before this session's benchmarks — geometry-tuple
top-10 neighbours vs. a 3x-widened text-cosine search overlap only 3.8% of the time (n=700) — the same
recall/neighbour-overlap methodology F-0269/F-0275/F-0276 used here independently, real prior art this
document should have cited from the start. And the hippocampal-indexing citation (Teyler & DiScenna
1986; Teyler & Rudy 2007) this document's own "index tuple" language descends from (via
`cognitive_geometry.md` §11) is real, current academic grounding already cited by
`memory_multiway_linking.md` and `emissary_lane2_cognition.md` for the identical concept — missing from
this document's own §8 bibliography despite being directly on-topic. `emissary_lane2_cognition.md` also
names `ghost_tuples.MemoryIndex` as its exact class, confirming §3's `ghost_tuples.py` toolkit entry's
real name.

**D-0005 (open, `memory_knowledge.md`)**: explicitly asks for two plans to be "linked in the
indexing/tuple system with a stated reason WHY... a real `memory-links` edge (or a `cognitive_geometry`
tuple category)" — a live founder-facing decision directly about this document's own subject matter,
not currently referenced here.

**Indexes — live vs. designed vs. orphaned:**

| Index | Status |
|---|---|
| `ghost_tuples.py` | World index live; memory index inert (not built in the live process, F-3901; D-0636 hold) |
| `memory-links` edge graph | Live (Claude's toolchain, not Du's) |
| P1 run-transition index / P1.5 transition index | Designed, zero code |
| Disparity-filter rarity analysis | Demonstrated working, one-off script only, not saved as a tool |
| NSW/simplified-HNSW-variant (`oxibonsai/embedding_index.rs`) | Real code, orphaned, no call sites — **re-confirmed 2026-08-24**: `oxibonsai-runtime/TODO.md:92` marks *"Semantic cache — embedding-based response cache (`semantic_cache.rs`, `embedding_index.rs`)"* `[x]` done, but `semantic_cache.rs` never references `EmbeddingIndex` — the two files were built separately and never actually wired together; the TODO checkbox is wrong, not the §10 "orphaned" claim |
| Pinnacle octree / `fold_with_checkpoints` | Real, not runnable as-is / untested (J-0210 pending) |
| Learned-index benchmark, Product Quantization, RRF | Named as right tools, never applied to real Du data |

**Backfill requirement, named explicitly**: any real index build must cover existing history
(16,600+/14,210+/1,302 rows already accumulated), not just data from build-day forward — otherwise
historical queries silently return wrong/empty results. This is a P1/P1.5 acceptance criterion, not
optional.

**Backfill triage — script-only vs. needs an LLM pass (2026-08-24):**
- **Script-only** (deterministic, no LLM cost): weather transition backfill (P1), grade transition
  backfill (P1.5 — deltas already sit in logged fields), `cycle_id` best-effort retroactive matching,
  saving the disparity-filter analysis as a reusable tool, Product Quantization on affect/sound vectors,
  the learned-index benchmark, HNSW wiring.
- **Needs an LLM pass** (semantic/qualitative judgment required): synthesizing human-readable "why"
  narratives from raw deltas (optional enrichment, not required for P1.5's core function), any new
  semantic tagging not already a structured field, re-processing `emb`/text content for new categories,
  and true causal disambiguation beyond simple corroboration (e.g. `factory_candidates_from_history.md`'s
  "was the cat there" — corroborating cat-presence from `objects` is script-only; judging whether the cat
  *caused* a specific sound is not).

---

## 11. WHERE IT SITS

Not an umbrella child of any live plan. Related-but-independent context: `cognitive_geometry.md` (source
of `geometry_tuples.jsonl`, additive-only discipline borrowed as good practice), `RESEARCH_specialists.md`
(dormant "minibots as nodes" design — §2 P2's real consumer evaluation target if ever activated, no
adapters trained here), `docs/job_queue.jsonl` J-0210 (the real, independently-filed, actionable first
step this whole document is downstream of). The 6 plans in §6 are potential future consumers, not
dependencies — this document does not build for them, only names them honestly as evidence the gap is
real.

---

*Author: Claude (design), Travis + Gemini (origin idea I-0023), Travis (the archaeology redirect, the
"keep this out of Du" correction, and the Time/Knowledge/tuple design decisions), 2026-08-24. STAGED,
deliberately unlinked from ROADMAP.md/cognitive_geometry.md — note J-0223 currently conflicts with this
(§6), unresolved. Update when: the founder explicitly decides to activate/promote a phase, J-0210 closes,
or new real consumer evidence emerges.*
