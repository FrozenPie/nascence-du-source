# Antigravity Ecosystem Proposals — Inbox (2026-08-25 research sweep)

**Status:** ⚪ PARTIAL — 6 of 9 group-A items resolved (1 promoted to `lod_staged_retrieval.md`, 4
archived/killed/registered); items 5/7/8 still un-run, D-0114 ruled deferred (see Current State below).
**Provenance:** Antigravity's 2026-08-25 evaluation sweep. Source docs live in
`C:\FreshStart\Thoughts and ideas\` (16 evaluation notes + the master
`Du_Cognitive_Architecture_Research_Blueprint.md`, all 2026-08-25 14:50–18:17). The same themes
were bulk-appended as addenda to 55 plan docs (fate of those addenda = **J-0292**, separate
question from this capture).
**ROADMAP:** [ROADMAP.md](../ROADMAP.md) → cluster 10.
**Triage job:** J-0295 (needs_input).

```plan-state
stage: partial
phase: 6 of 9 group-A items investigated and resolved (1 promoted, 4 archived/killed, 1 registered); items 5/7/8 specs written, not yet run
verified: 2026-11-18
evidence_read: 2026-08-27
next: Item 8 waits on Item D gate: gap normalisation redesign, graduation test (b), founder scope call J-4310; then run 5-scenario arbitration test
cluster: 10
```


> Reading discipline: these are ANTIGRAVITY's evaluations, not verified findings. Citations in the
> evaluation notes are unverified (some look confabulated). The vocabulary ("CriticNode",
> "ExecutiveNode", "SomaticEngine", "12-node architecture") is the blueprint's own model of Du —
> it maps loosely onto real files (`nodes/critic_node.py`, `nodes/executive_node.py`, …) but per
> the (itself-unverified) 2026-08-26 telemetry audit most of those node files are dormant in the
> live pulse. Every item below needs re-grounding in Du's ACTUAL architecture before promotion —
> function over imitation ([[feedback-function-over-imitation]]).

## Current State — verified 2026-11-18

- **2026-11-18** (F-5089): Item 8 (NeuroConscious) checked 2026-11-18: affect_drives Item D is not graduated and drive_note() does not exist; Phase-0 gap is saturated (F-5088). Kill criterion cannot fire; item 8 is held, no parallel drive system.
- **2026-11-18** (F-5084): Item 7 (Lumina dream images) text-read prerequisite run (J-4259): VERDICT DEFER. 0/61 is stale (now 3/309 legacy arcs resolved, 1/60 recent) but dreams still almost never resolve; last 20 arcs reuse the same few symbols with abstract unresolved cores, so an image would add decorative detail only. No image-gen test until dream_overhaul changes this; VRAM on the 11GB hot lane is also tight.

### What we have
D-0054's investigation-first gate (2026-08-27) has processed 6 of 9 group-A items: item 1 (LOD retrieval)
PASSED and promoted to `docs/staged/lod_staged_retrieval.md` (F-0545); items 2/4/6 KILLED (AAAK compression
falsified, GNW bottleneck lost real content, no live audio pipeline for Whisper); item 3 (KIP graph)
ARCHIVED as duplicate but spawned real memory_edges harvester work (J-0395, 3 of 5 gaps closed); item 9
(philosophy corpus) registered via the existing pipeline (J-0370).

### What we need
Items 5 (5-persona panel) and 7 (Lumina dream imagery) still have only their specs written, never run.
D-0114 (spawned from item 3's gap #3) was ruled by travis 2026-09-27: defer until memory_multiway_linking's
M2/D-0022 edge-aware promotion resolves toward live. `memory_edges.py`'s `contradicts` relation still has 0 rows and
needs a semantic-judge harvester design, which is parked behind that ruling.

### What we're doing next
No job currently queued for items 5/7/8's remaining specs — pick up if/when this inbox is revisited.

---

## A. Du-core candidates (real look warranted)

1. **OpenViking L0/L1/L2 progressive-detail retrieval** — layered LOD recall for memory.
   Overlaps [[memory-knowledge]] (Stage A/B) and the parked
   [du_recall_lens_upgrades](du_recall_lens_upgrades.md) (J-0291). ⚠ Blueprint says "implement in
   `cognitive_mmu.py`" — that is a **FreshStart** file; Du's recall stack is
   `core/memory/store.py` + `core/associative_recall.py`. Proposal must be re-grounded.
2. **Lumina AAAK ~30x text compression for old episodic logs** — overlaps [[project-nascence-memory-levels]]
   (memory ABSTRACTS, not transcribes — already the doctrine) and journal_consolidation_pyramid.
   The 30x claim is unverified. Additive-only: never lossy-compress the foundational stores
   ([[feedback-erosion-of-foundations]]).
3. **Anda Hippocampus KIP memory graph** — natural-language graph protocol over permanent memory.
   Du already HAS typed edges (`core/memory_edges.py`) and the staged
   [geometry_tuple_index](geometry_tuple_index.md) covers the multi-dim index theory. Question is
   whether KIP adds anything those don't.
4. **256-token GNW workspace bottleneck** on executive synthesis — force a narrow gestalt pass
   before decisions. Genuinely interesting; adjacent to [[project-nascence-t4-watershed]] and
   ThoughtCompressor-style ideas. Smallest testable version: a shadow-mode compressed-preamble
   experiment.
5. **5-persona internal advisory panel** before high-stakes decisions — overlaps
   `core/judge_panel.py` (exists, live) and the 3-pass lane architecture + [[project-nascence-lane2-the-witness]].
   Panel-as-deliberation is fine; panel-as-self-evaluation would violate
   [[feedback-decoupled-judge]]. Note from factory labs: schema-first framing made judge_panel
   MORE credulous (D-0013) — same risk applies to persona panels.
6. **Buzz / local Whisper audio perception** — offline speech-to-text as a new sensory channel.
   Adjacent to [[project-nascence-music-learning]] (whose residual cap is literally missing raw
   audio) and the sound_causality / sound_world_expansion plans. One of the few items proposing a
   genuinely NEW capability rather than a re-skin.
7. **Lumina multimodal (text-to-image dream anchors)** — render DreamNode symbols as images.
   Adjacent to [[project-nascence-dreams]] (SYMBOLIC lens observe-first LIVE). ⚠ VRAM cost on
   Du's fabric is the practical blocker; also dreams currently have a 0/61 resolution problem —
   rendering them prettier is downstream of making them WORK.
8. **NeuroConscious modular motivation engine** — likely redundant with [[project-nascence-affect-drives]]
   (Item A live) + the 08-24 somatic fatigue work (sleep_dream_redesign §7). Verify what function
   it adds before considering.
9. **Sentient AI philosophy-of-mind corpus** — ingest as reading material. Compatible with the
   [[feedback-world-answers-never-leads]] law ONLY as diegetic books through the existing book
   selection pipeline — never as prompt-injected "grounding." With that constraint it reduces to
   "add candidate books to the library," which is cheap and low-risk.

## A-1. Investigation specs (J-0304, D-0054 gate, written 2026-08-29)

Per D-0054: no item above promotes to a plan doc until its spec below has actually been run and its
PROOF criterion met. This job only writes the specs — none has been executed. Each spec names a
falsifiable test against Du's real data/architecture (not a synthetic benchmark), a cost estimate,
and a kill criterion. The three items D-0054 flagged as overlapping a live Du system (3, 5, 8) get a
**comparative** proof requirement — what the proposal adds over the system already read below —
per the honest-dedup rule.

UDMS advisory check (2026-08-29, `udms_query_pmi`, informational only — see UDMS's own documented
1-of-6-repos ranker caveat, not treated as proof either way): co-change PMI between the candidate
integration points below and their nearest existing-system files came back `pmi_bits: 0.0,
statistical_lift: 1.0` for all three pairs checked (`memory_edges.py`↔`associative_recall.py`,
`judge_panel.py`↔`executive_node.py`, `schema.py`↔`satisfaction.py`) — i.e. no observed co-change
correlation in git history either way. Read as "git history is silent," not as evidence for or
against any of these proposals.

---

**1. OpenViking L0/L1/L2 progressive-detail retrieval**
- **Proof.** Build an L0 (gist) / L1 (abstract) / L2 (full fragment) staged index over a real slice
  of `core/memory/store.py`'s existing fragments. Shadow-mode only: for ≥100 real recall calls drawn
  from live `core/associative_recall.py` traffic (or replayed frontier questions/tension
  resolutions), log BOTH the current single-level top-k and the LOD-staged top-k side by side. Blind
  a decoupled judge (not self-scored) on which set better serves the query, per-pair, no ordering
  hint.
- **Cost.** S–M: an offline abstraction index over existing store content, a shadow logger, no live
  wiring, no new deps.
- **Kill.** If LOD-staged retrieval does not beat single-level baseline by a real margin (target:
  ≥10 points of win-rate over chance on ≥100 judged pairs) — or if the parked
  [du_recall_lens_upgrades](du_recall_lens_upgrades.md) (J-0291) already covers the same staged-detail
  idea once read in full — archive as duplicate/no-lift.

**Result (J-0372, 2026-08-29) — PASS, promote for a real plan doc.** Finding: F-0545 (verified).
Duplicate check done first: `du_recall_lens_upgrades.md` read in full (re-confirmed via keyword grep
for L0/L1/L2/abstraction_level/staged-detail — zero hits) — that plan is a different technique family
(spectral diffusion / deterministic anchoring / counterfactual re-rank over the concept graph), not a
staged-abstraction-level retrieval idea. Not a duplicate.

Built the L0/L1/L2 index directly on Du's real schema — `memory_fragments.abstraction_level` already
exists (0=raw/L0, 1=gist/L1, ≥2=theme/L2), no new columns, no new deps. Real non-cold, non-chaptered
pool sizes: L0=3,732, L1=1,303, L2=179. LOD arm: cosine-scored independently per pool, composed via a
slot cascade (~20% L2 anchor / ~30% L1 gist / rest L0, unfilled coarser slots cascading to finer —
the same idiom `store.py`'s own `TIER_SLOTS`/`retrieve()` overflow already uses) sized to match each
query's real baseline result count. Baseline arm: `core.memory.store.retrieve()` called live,
unmodified. Judge: `core.judge_panel.rule_detail`, the real two-family decoupled panel (gemma4:12b /
falcon3:7b) + granite3.1-moe:3b tiebreak, blind (Set A/B relabeled per query via an independent RNG
stream, judge never told which arm is which). Queries: 120 real logged frontier questions sampled
(seeded/deduped/length-filtered) from `data/frontier.json`'s 6,430 entries.

Isolated throughout via `lab_env.isolate()` — every DB read against a lab-dir copy of `nascence.db`;
`judge_panel._LOG` redirected into the same lab dir so the lab's rulings never touched the live panel
ledger; `telemetry.log_llm_call`/`retrieval_probe.observe` no-op'd. Live DB row-count/mtime checked
before and after every one of the 15 chunked runs (script had to be re-run in ~8-query chunks after
the coding-agent worktree it started in was torn down mid-run by an external cleanup — see
`scripts/lod_retrieval_lab.py`'s own RESUME/CHUNKING notes) — unchanged every time.

**Real result: 120 sampled, 113 actually judged (clears the ≥100 bar). LOD wins 98 (86.7%), baseline
wins 15 (13.3%). Margin = 73.5 win-rate points — clears the ≥10-point kill threshold by a wide
margin.** Full report: `docs/lab/lod_retrieval_lab_2026-08-29.md`. Shadow log (120 rows, one per
attempted pair, both arms' fragment ids + judge verdict): `data/lod_retrieval_lab_shadow.jsonl`.
Promotes out of this staged doc to its own plan doc per D-0054's own promotion rule (spec run, PROOF
criterion met) — see job-queue for the follow-up plan-doc-write job. **Plan doc written (J-0413):
[docs/staged/lod_staged_retrieval.md](../staged/lod_staged_retrieval.md)** — design, the
tier/abstraction-level interaction question, and the shadow-mode-first build order for wiring into
`core/memory/store.py`'s `retrieve()`. Still SHADOW-TESTED only, nothing wired live yet.

**2. Lumina AAAK ~30x compression for old episodic logs**
- **Proof.** The 30x figure is unverified and the doc's own additive-only law
  ([[feedback-erosion-of-foundations]]) forbids lossy-touching the foundational store — so the test
  runs ONLY against already-archived, non-foundational episodic material, never live fragments.
  Sample a batch of old logs, apply the compression, then check whether a downstream query that
  currently succeeds against the existing abstraction-pyramid representation still succeeds (blind
  A/B, judge-scored) against the AAAK-compressed form, and measure the real compression ratio
  achieved on Du's actual log format (not the vendor's claimed 30x).
- **Cost.** XS–S: run against a sample directory, no schema change, no write path to any live store.
- **Kill.** Real compression ratio far under the claimed 30x, OR any measurable loss of
  downstream-query success vs the existing abstraction pyramid, OR the technique requires touching
  anything the additive-only law protects — any one of these kills it outright, no partial credit.

**Result (J-0368, 2026-08-29) — ARCHIVE, 30x claim falsified.** Finding: F-0512 (verified). Isolated
via `lab_env.isolate()` (DB copy patched at `core.memory.store.DB_PATH`, live nascence.db never
touched — post-hoc fragment counts, 58,791 total / 47,656 cold-episodic, matched exactly before and
after the test). Tested ONLY `layer='episodic' AND cold=1` rows — demoted-out-of-active-recall,
non-foundational material, per `core/memory/store.py`'s own `prune_episodic()` doctrine ("never
delete; step out of ordinary recall, stay retrievable"). `layer='archive'` (the protected foundational
tier, 5,716 cold rows) was never selected.

Real compression ratio measured TWO ways, both far under 30x:
  1. **Lossless** (the literal "text compression" reading), over the FULL 47,656-row/50.1MB
     cold-episodic corpus: zlib level 9 → **2.84x**; lzma preset 9 → **4.38x**; per-item (no shared
     dictionary) mean → 1.93x.
  2. **Targeted lossy LLM compression** (the "preserve downstream-query utility" reading), explicitly
     instructed to hit the 30x target on 4 real archived clusters (raw episodic fragments + their
     existing `distilled_from` gist parent, pulled via `memory_links`): aggregate real ratio achieved
     **11.71x** (10,326 raw chars → 882 compressed chars; per-cluster range 7.4x–22.2x) — well under
     half the claim even when directly aimed at it.

Kill criterion 1 (ratio far under claim) is met on its own by both methods — no partial credit needed,
so the item archives regardless of the downstream-query leg. That leg was run anyway (blind two-family
judge panel, gemma4:12b + falcon3:7b, granite3.1-moe tiebreak — pattern mirrored from
`core/judge_panel.py`, called directly via raw HTTP rather than through `judge_panel.rule()`/
`core.model_client` so no live telemetry or `judge_panel_log.jsonl` row was written) and was
INCONCLUSIVE at this scale, n=8 questions: the existing gist-rollup representation answered 1/8
correctly, the AAAK-style fact-preserving compressed form answered 3/8 — no downstream-query LOSS
observed; if anything the compressed form did better on narrow factual recall (plausibly because the
existing gist cap is written for thematic gist per the anti-mush doctrine and deliberately omits
names/numbers/dates). n=8 is too small to found any promotion on, and does not override kill
criterion 1. Scripts + full per-question results (with judge votes) referenced from F-0512.

**3. Anda Hippocampus KIP memory graph — comparative vs `core/memory_edges.py` (read 2026-08-29)**
- **What already exists.** `core/memory_edges.py` is a live, additive, provenance-carrying typed-edge
  store: 7 edge types today (`resolves`, `answers`, `kept_from`, `dreamt_from`, `correspondence_with`,
  `part_of`, `transformed_into`), four M0 harvesters, an M1 co-recall shadow ledger, and an M2
  mode-weighted neighbour lookup (`edge_aware_neighbors()`, direct + bipartite-projection reads)
  already built — currently SHADOW-ONLY (`associative_recall.recall_trail_edge_aware()`, never on a
  live recall path). Census/status read-outs exist for the founder.
- **Proof (comparative).** Catalogue 10 real graph-shaped questions about Du's own memory (e.g. "what
  fragments led to this resolved tension," "who does this letter correspond with," "what dream drew on
  this fragment") and check, for each, whether the existing 7 edge types + `edge_aware_neighbors()`
  can already answer it. For any that can't, determine WHY: (a) the edge_type vocabulary is
  structurally too narrow (a real gap KIP's natural-language graph protocol might fill), vs (b) M2
  simply isn't wired live yet (a wiring problem, not a data-model problem — KIP doesn't fix that
  either).
- **Cost.** S: pure gap-analysis against the already-read code above, zero new code required to run
  this spec.
- **Kill.** If every candidate question is already expressible via the existing edge_type vocabulary
  or projection hops, OR the only real gap is "M2 isn't wired live" (fix: wire M2, not build KIP) —
  archive as duplicate. Only a genuine (a)-class gap, named concretely, justifies further KIP work.

**Result (J-0367, 2026-08-29) — ARCHIVE as duplicate/no-lift.** Finding: F-0500 (verified). Catalogued
10 real graph-shaped questions against the 7 edge types + `edge_aware_neighbors()` (memory_edges.py
read in full, line refs below):

  1. "What fragments fed this resolved tension?" — **NOT answerable.** `resolves` is strictly
     (cycle)→(shadow_event) (`sync_resolves()`, memory_edges.py:154-173); no harvester ever puts a
     `fragment` on either end, so no query walks from a resolution back to the fragments that informed
     it. Vocabulary gap, not M2 wiring — even wired live, `resolves` still has no fragment endpoint.
  2. "Did Du write to X, or did X write to Du?" (correspondence direction) — **NOT answerable.**
     `wrote_to`/`received_from` are declared in `MODE_EDGE_WEIGHTS["relational"]` (memory_edges.py:603)
     but grepped codebase-wide (`*.py`) and found written by **zero** harvesters anywhere — only the
     undirected `correspondence_with` (`backfill_correspondence()`, :237-266) is ever populated.
     Declared-vocabulary-but-never-harvested, distinct from the M2-unwired pattern.
  3. "Does fragment A contradict fragment B?" — **NOT answerable**, but for a different reason again:
     `contradicts` IS wired into M2's direct-read path (`_DIRECT_FRAGMENT_TYPES`, :610) — the gap is
     that nothing anywhere computes contradiction between fragments to populate it (0 rows, per the
     file's own F-0110 note at :575). Needs a semantic-judge harvester; neither M2-wiring nor KIP's
     query protocol would supply that judgment.
  4. "What dream drew on fragment X?" — **Answerable now**, direct SQL/`edge_aware_neighbors` read of
     `dreamt_from` (dst_kind='fragment').
  5. "Who does this letter correspond with?" — **Answerable now**, direct `correspondence_with` read.
  6. "What fragments are part of this dream arc?" — **Answerable now**, direct `part_of` read.
  7. "What fragment(s) does this keepsake anchor?" — **Answerable now**, direct `kept_from` read.
  8. "What fragments fed this essay lesson?" — **Answerable now** via `transformed_into`
     (essay_lesson.py:473 confirms the harvester), already in M2's direct-read set.
  9. "What's the multi-hop chain between two nodes with no 1-hop or single-projection link (e.g. a
     person and a dream with no shared fragment)?" — **NOT answerable.** `edge_aware_neighbors()`
     (:622-673) is fixed single-hop by design: direct fragment↔fragment OR one bipartite projection
     through exactly one hub. Codebase-wide grep for `WITH RECURSIVE`/multi-hop traversal found none —
     no N-hop path function exists anywhere in the system. This is the cleanest real structural gap.
  10. "What raw fragments consolidated into this higher-level abstract (LOD lineage)?" — **NOT
      answerable from memory_edges** — that lineage is real but lives in a DIFFERENT table
      (`memory_links`'s `distilled_from`, written by `core/refinery.py`, per memory_edges.py's own
      :25-38 guard comment), not in `memory_edges` at all. Du's overall system already answers this;
      `memory_edges` specifically does not.

  **Verdict.** Genuine (a)-class gaps exist (#1, #2, #3, #9, #10) — this is NOT the clean "everything's
  already answerable" kill case. But none of them argue for KIP specifically: #1/#2/#3 are missing
  **harvesters** (new edge types/population logic) that plug into `memory_edges`'s existing generic
  schema (`src_kind, src_id, dst_kind, dst_id, edge_type` — already type-agnostic, no redesign needed)
  exactly the way `transformed_into` was added; #9 is a missing **traversal function** (a recursive
  query) over the SAME table, not a different data model; #10 is a table-consolidation question
  (`memory_links` vs `memory_edges`), unrelated to KIP entirely. KIP's actual differentiator — a
  natural-language *protocol* for querying an external graph — adds nothing that extending
  `memory_edges`'s own harvester/traversal surface doesn't already cover more cheaply and consistently.
  **Archive KIP as duplicate/no-lift.** Follow-up spawned as J-0395 (new edge harvesters + a recursive
  multi-hop traversal function on `memory_edges`) — real gaps, but `memory_edges`'s own next step, not
  a case for adopting KIP.

  **J-0395 result (2026-08-29) — Finding F-0505 (verified). 3 of 5 gaps closed, 1 deferred, 1 assessed
  as a non-gap:**
  - **#1 closed.** `backfill_resolves_fragment()` joins `data/subconscious_state.json`'s resolved
    tensions (`resolution_thought`/`resolved_ts`/`member_event_ids`, from
    `tension_ledger.py:750-754`) against `memory_fragments` by LIKE-probe + ±600s window — the same
    idiom `backfill_answers`/`backfill_kept_from` already use. Live run: 34/35 resolved tensions with a
    real `resolution_thought` matched exactly ONE fragment; wrote 99 new `(fragment)-[resolves]->
    (shadow_event)` edges, 0 ambiguous, idempotent on re-run.
  - **#2 closed.** `backfill_directed_correspondence()` classifies all 64 `origin='letter'` (always
    →Travis by construction) + 42 `origin='peer'` fragments into `wrote_to`/`received_from`: named
    directly in the fragment's own content for 26 of them (`'(my letter to NAME...)'`/`'(a letter from
    NAME)'`), and for the 16 older, unnamed `'(a letter he received)'` fragments (pre-2026-08-20,
    before `peers.remember_inbound` started naming the sender), resolved by a unique-substring match
    against each persona's own `data/Correspondence/<persona>/thread.jsonl`. Live run: 106/106
    resolved (87 `wrote_to`, 19 `received_from`), 0 unmatched, 0 ambiguous. Also added `wrote_to`/
    `received_from` to `_PROJECT_THROUGH` so `edge_aware_neighbors()`'s relational mode can actually
    walk them now, not just weight them.
  - **#4 closed.** `edge_aware_neighbors_multihop()` — weighted BFS over the same `memory_edges` table,
    reusing `edge_aware_neighbors()`'s own per-hop weighting/projection logic unchanged (hops=1 output
    verified byte-identical to calling `edge_aware_neighbors()` directly). Geometric decay per hop
    beyond the first, verified against a synthetic chain after catching and fixing a double-decay bug
    in the first draft. SHADOW ONLY, same as `edge_aware_neighbors()` itself.
  - **#3 deferred.** `contradicts` needs a real semantic judge (candidate-pair generator + an LLM judge
    call, closest precedent `tension_ledger.py`'s `_judge_resolution`) — genuine design/cost surface,
    not a bounded harvester. Spawned as **J-0399** rather than guessed at.
  - **#5 assessed, no action.** LOD/abstraction lineage is correctly separate: `core/refinery.py:230`
    already mirrors it into `memory_links` as `distilled_from` (the `derived_from` GUARD's own named
    "good citizen"), and no `memory_edges` M2 consumer needs it duplicated here today.

**4. 256-token GNW workspace bottleneck**
- **Proof.** Build the smallest testable version the doc itself names: a shadow-mode compressed
  preamble ahead of Executive synthesis. For ≥50 real Executive cycles, log both the full-context
  output and a ≤256-token-bottlenecked-context output for the same cycle. Blind-score via judge_panel
  (decoupled, not self-eval per [[feedback-decoupled-judge]]) on decision coherence, and separately
  code whether the bottlenecked version lost information the full-context decision actually used.
- **Cost.** S: a summarizer + shadow logger, no live wiring, no schema change.
- **Kill.** No distinguishable coherence difference on blind judging, OR the bottleneck version loses
  content the full-context decision needed on a real, checkable fraction of sampled cycles (threshold:
  >10% of sampled pairs) — kill.

**Result (J-0371, 2026-08-29) — KILL, real information loss.** Finding: F-0509 (verified). Sampled 60
real Executive cycles from `data/training/executive.jsonl` (prompt ≥2500 chars, real non-trivial
`output.synthesis`, seed 20260829). Built a principled ≤256-token compression of each real
`user_prompt`: kept Input/Perception/Emotion/Salience lines verbatim, a `WHAT YOU RECALL` header +
the top recall item truncated to ~220 chars, and Reflection truncated to ~150 chars; dropped
conversation history, self-model, the tensions list, subconscious patterns, extra memory fragments
beyond the first, and all but a short stub of Axiom (avg full prompt 1504 tokens → avg bottleneck
197.2 tokens, tiktoken `cl100k_base`, 0/60 over budget).

  - **Content-loss check (real, deterministic, checkable).** For each cycle, checked whether the
    REAL logged `output.synthesis` (the decision Executive actually made from the full context)
    contains a ≥4-word phrase that appears ONLY in the sections the bottleneck drops (not in the
    bottleneck text or the raw input). **19/60 = 31.7%** flagged — over 3× the >10% kill threshold —
    with concrete, traced examples: cycle `66289796`'s output ("the self is born where opposites
    meet") near-verbatim-quotes a `[semantic]` memory fragment (#3 of 8) that the bottleneck's
    top-1-fragment compression drops; cycle `b2d47c85`'s output ("rather than an active agent") is
    verbatim from the dropped `Self-model:` line; cycle `596e9ac2`'s output ("unconscious as a
    vital") reproduces a dropped `Prior positions in tension:` line. This alone meets the kill
    criterion.
  - **Coherence judging — attempted for real, inconclusive on sample size.** Real `judge_panel`
    calls (isolated: `lab_env.isolate()` + `judge_panel._LOG`/`telemetry._CALLS` redirected into the
    lab dir; live `data/judge_panel_log.jsonl` and `data/llm_calls.jsonl` mtimes confirmed unchanged
    before and after) were run asking the decoupled panel whether the compressed context still
    plausibly supports the real decision. Only 3/50 pairs completed in ~20 minutes before the
    channel was judged too slow/unreliable to pursue further in-session: 2/3 `unavailable` (a judge
    hub missed its 90s timeout), 1/3 `agreed`-sufficient. Too small and too failure-prone to support
    any coherence verdict on its own — reported honestly rather than extrapolated.
  - **Live replay not attempted.** Executive's own hot lane (`qwen3.5:9b` @ `:11433`) was not used to
    generate an actual bottlenecked-context output: `data/llm_calls.jsonl` showed that lane in real
    recent use by live Du cognition this session (~90 min prior), and reusing it would contend with
    live cognition rather than stay shadow-only — read as out of bounds in spirit under this job's
    "no live wiring / not live interception" rule even though it doesn't literally touch
    `nodes/executive_node.py`.

  **Verdict.** The structural/content-loss half of the kill criterion is real, checkable, and already
  decisively over threshold (31.7% vs >10%) — sufficient on its own to kill per the spec's OR logic,
  independent of the inconclusive coherence-judging attempt. **Archive as no-lift / real-loss.**

**5. 5-persona internal advisory panel — comparative vs `core/judge_panel.py` (read 2026-08-29)**
- **What already exists.** `core/judge_panel.py` is a live, decoupled, boolean-verdict panel: two
  independent model families rule, agreement = verdict, disagreement escalates to a third
  (family-decoupled) tiebreak model, unavailable-either = no verdict (fail-closed, never single-judge).
  Every ruling is logged with both votes + free-text `why`. Used today by
  `tension_ledger._judge_resolution` and `pursuits.judge_pending`. Separately, `core/lane2.py` (read
  2026-08-29) is NOT a deliberation panel — it's a standing reality-testing/grounding loop
  (prediction-vs-percept gap checking), so it is not actually the comparator the proposal implies; the
  real comparator is judge_panel.py alone.
- **Proof (comparative).** judge_panel judges ONE proposition AFTER the fact (advances/resolves/bears);
  a 5-persona panel proposes multiple viewpoints feeding INTO a decision BEFORE it's made — a
  structurally different role (deliberation vs adjudication), so the comparison must be honest about
  that difference, not just "we already have a panel." Take N real upcoming high-stakes decisions,
  run a shadow 5-persona pass alongside the existing single-generation path, and judge (via the
  EXISTING decoupled judge_panel, never self-scored) whether the persona pass produces measurably more
  diverse/considered reasoning — while explicitly tracking the D-0013 risk (schema-first framing made
  judge_panel MORE credulous, not less) for any rise in agreement/sycophancy rate in the persona
  outputs.
- **Cost.** M: 5 persona prompts + a shadow harness + judge_panel-scored comparison; no live wiring.
- **Kill.** No measurable diversification of reasoning over the existing single pass, OR the same
  D-0013 credulity-increase pattern reproduces in persona form — kill; panel-as-self-evaluation
  (persona verdicts scoring their own deliberation) is out of scope entirely per
  [[feedback-decoupled-judge]] and must not be attempted.

**6. Buzz / local Whisper audio perception**
- **Proof.** One of the few proposals adding a genuinely NEW sensory channel (no live overlap). Feed
  a real recorded audio sample through local Whisper and compare the resulting transcription-derived
  fragment against Du's current TEXT-ONLY sound representation (`sound_causality` /
  `sound_world_expansion`) for informational content actually new to the associative-recall pool —
  not just re-stating what the text description already said.
- **Cost.** XS–S: run Whisper offline against sample audio; separately measure real VRAM/CPU cost
  against Du's currently-resident model fabric (the doc's own capacity constraints apply here too,
  though Whisper is lighter than image generation).
- **Kill.** No real live audio-capture pipeline exists to feed it today (making the channel moot until
  that's built first), OR the resource cost can't be absorbed without evicting a resident model —
  kill or defer behind that prerequisite.

**Result (J-0369, 2026-08-29) — KILL, both criteria hit.** Finding: F-0507 (verified). Checked for a
real live audio-capture pipeline before doing anything else, per the job's own instruction not to
fabricate a synthetic sample to force a test:

  - `core/sensorium.py` and `core/soundscape.py` (the entire sound-representation surface) are pure
    generative-text pools — hardcoded prose strings for waves/wind/fire/gulls/etc — with no recording,
    microphone, or audio-file decode call anywhere in either file.
  - Repo-wide grep for `pyaudio|sounddevice|whisper|microphone|record_audio|speech_recognition|ffmpeg`
    across every `.py`/`.md`/`.txt` file surfaces only `core/audio_features.py` +
    `scripts/play_the_record.py` + `core/listening.py` — a MUSIC playback path (`data/music/
    Heavyweight.mp3` decoded via ffmpeg into deterministic tempo/key/brightness features for a
    human-initiated shared-listening ritual), explicitly documented as "NOT wired into Du's runtime
    yet" in `audio_features.py`'s own docstring. That is not a live capture pipeline, carries no
    speech content, and isn't even runtime-wired — three separate reasons it can't feed Whisper.
  - No microphone or environment-audio-recording code exists anywhere in the repo.
  - `openai-whisper`/`whisper` is not pip-installed (`pip show`/`import` both fail) — confirms the
    resource-cost side of the kill would also apply if the pipeline existed: nothing is pre-staged.
  - `core/schema.py` `SERVE_URLS`/`SERVE_CHAINS` (lines 936-989, current post-2026-08-28
    redistribution) show both GPUs already fully tenanted — 1080Ti runs qwen3.5:9b (hot lane), Ramses
    3070 runs command-r7b as sole tenant (background lane) plus mixtral:8x7b (judge_mixtral) — no
    spare VRAM seat for a Whisper model without evicting a resident model.

  First kill criterion (no live audio-capture pipeline) is sufficient on its own; the resource-cost
  criterion would independently kill it too. No synthetic audio file was fabricated to force a test —
  per the job briefing, that would have misrepresented the real feasibility question. Archive; the
  real prerequisite (build a live audio-capture pipeline) is out of scope for this spec.

**7. Lumina multimodal (text-to-image dream anchors)**
- **Proof.** Explicitly downstream of dreams working at all — the doc already notes dreams have a
  0/61 resolution problem. Before any image-gen test: sample 20 current dream arcs and check whether
  the underlying SYMBOLIC content is specific/coherent enough that an image would add real information
  beyond the text, or so vague/unresolved that a rendered image would just be decorative confabulated
  detail layered onto a broken signal.
- **Cost.** ~zero for the text-read prerequisite check; a real image-gen prototype costs real VRAM
  budget the doc already flags as the practical blocker.
- **Kill.** If the 0/61 dream-resolution problem isn't fixed first, OR no VRAM budget can be found
  without evicting a resident model — kill/defer; no image-gen test should run before the prerequisite
  is cleared.

**8. NeuroConscious modular motivation engine — comparative vs `docs/plans/affect_drives.md` (read
   2026-08-29)**
- **What already exists.** affect_drives.md is a comprehensive, already-partly-graduated multi-
  timescale drive architecture: Item A (felt-preamble into Executive/monologue) is LIVE and
  retroactively re-verified 2026-08-24; `climate_engine.py` is the fully-wired affect-to-behavior
  exemplar (hint → threshold → injected sentence, symbol, retrieval warp, ignition — 4 real actuation
  channels); `satisfaction.py`'s wanting−liking gap is a designed drive-currency signal, STAGED
  Phase-0, with its OWN already-specified graduation path (Item D §4: a prompt-bias hand + an ignition
  contribution into climate dissonance) — not yet wired only because its own evidence gate hasn't been
  read.
- **Proof (comparative).** Before considering a new motivation engine at all, graduate affect_drives
  Item D per its own pre-existing spec (verify the Phase-0 `satisfaction_log.jsonl` gaps look sane,
  wire `drive_note()`). Only if, AFTER that graduation, a concrete motivational function is identified
  that gap-driven prioritization structurally cannot produce — the strongest candidate being
  arbitration among multiple SIMULTANEOUS competing drives, since satisfaction.py's gaps are
  per-domain and don't obviously rank across domains — does a new engine get investigated. That test:
  construct 5 real scenarios with competing drives, show the graduated gap-only approach can't produce
  sane prioritization, then show a modular arbitration layer can.
- **Cost.** The Item D graduation itself is already scoped as its own next step in affect_drives.md's
  own "What we need" §5 — effectively free re-use rather than new cost.
- **Kill.** If Item D's graduation (once run) already covers the claimed motivational function —
  which is the default expectation given how much of this ground the existing architecture already
  covers — archive NeuroConscious as duplicate; do not build a parallel drive system alongside a
  half-graduated one.

**9. Sentient AI philosophy-of-mind corpus**
- **Proof.** Doc's own constraint: diegetic books through the existing book-selection pipeline only,
  never prompt-injected grounding ([[feedback-world-answers-never-leads]]). Register the candidate
  titles as book metadata and check whether Du's EXISTING selection pipeline actually picks them up
  and reads them in the natural course of operation (not just added to an inert shelf), and whether
  any observable engagement follows (a journal reference, a fragment citing the book) within a
  reasonable window.
- **Cost.** XS: metadata registration only, reuses the existing pipeline entirely.
- **Kill.** Low-stakes by construction — if the books are never selected within a few weeks, remove
  from the catalog. Given near-zero cost either way, this is the one item where a null result is
  cheap enough not to need a hard pre-registered threshold.

## B. Tooling / pair-programming workflow (not Du's psyche)

10. **Docusaurus + `llms.txt` knowledge site** — ⚠ **already part-built without a ruling**:
    `C:\Nascence\docs_site\` (full Docusaurus install incl. node_modules + build/) appeared
    2026-08-25. No `llms.txt` bundles yet. Needs a keep/remove call — it's also disk-heavy.
11. **RTK (Rust Token Killer) CLI output filtering** — for our agent sessions, not Du.
12. **PostHog self-hosted agent tracing** — observability backend candidate; overlaps
    [[project-nascence-du-pulse-rebuild]] + [[project-nascence-gauge-rethink]] (sequenced: gauge
    taxonomy first). Cite it inside that work when it runs rather than as its own plan.
13. **Matt Pocock skills** (`/grill-me`, `/wayfinder`, TDD) — our workflow, plus a Socratic-gate
    idea for Du's curiosity organ (adjacent to [[project-nascence-field-scan]] curiosity judge).
14. **Vibe Coding Playbook governance** — specs-first / verification gates for our sessions.
15. **Awesome Claude Code skill mining** — overlaps the existing skill-manager toolchain.

## C. Peripheral / dismissed (recorded for completeness — Antigravity's own verdicts)

16. **Public APIs catalog** — peripheral; forbidden from Du's core loop (zero-cloud rule).
17. **Zapier MCP** — dismissed; cloud-dependent, incompatible with Du's local-only philosophy.

---

## What this doc is NOT

Not an endorsement, not a build queue. Promotion of any item = its own plan doc after the founder
triage (J-0295), with the usual gates. The 5-phase "roadmap" in the blueprint (Docusaurus →
OpenViking → AAAK/KIP → deliberation/GNW → audio/PostHog) is Antigravity's proposed ordering, not
ours — several phases duplicate live Du systems and should not be executed as written.
