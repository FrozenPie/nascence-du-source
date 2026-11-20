# Multi-Way Memory Linking — deep dive (2026-08-15)

> **Status: 🟢 LIVE — M0/M1 built+live since 2026-08-15 (M1 expanded 1→9 callers 08-19). M2 (the actual
> trail-engine upgrade) is now genuinely live too: `co_recalled_developing` writes live (D-0215, J-1348)
> and `recall_trail_edge_aware` live for mode=relational only (D-0287, J-1415) — both restart-gated,
> defeaters not yet fired. M3 (retro re-indexing) not started.** (the 2026-09-02 Current State section
> below predates M2 going live 2026-09-26 — see the plan-state block for the newest read)

```plan-state
stage: live
phase: M2 now genuinely live: co_recalled_developing writes live (D-0215, J-1348) and recall_trail_edge_aware live for mode=relational only (D-0287, J-1415); both restart-gated, defeaters not yet fired
verified: 2026-10-18
evidence_read: 2026-10-18
gate: D-0287's relational usage-proxy rate must not fall well below the shadow-observed 39% once restarted
next: Per-event re-read after next boot with >=20 relational usage events (J-2369, not-before 2026-10-25).
history: docs/plan_history/memory_multiway_linking.md
cluster: 2
```


> **Founder's ask (2026-08-15):** *"A memory should connect in more than just era groups. It should have
> semantic grouping, similarity groupings, and probably quite a few other groupings. Humans, when they
> think back on things, don't think in specific groups — they have multiple connections to the same
> memory from a variety of ways. Research how humans deal with this, and how Du could do it better,
> as he does not have the same biological limitations."*
>
> **Standing:** this is a child of [cognitive_geometry.md](cognitive_geometry.md) (LOCKED, top of the
> list) — specifically its §2.3 springs level 1 ("per-memory sparse typed weighted edge lists") and its
> P3–P5 phases. Everything here defers to that plan's laws: immutable objects / plastic springs,
> pre-registered metric sheets, the §5.5-#6 kill criterion, calcification guards. Claude authored this
> after Antigravity left the project; Claude is checker and implementer both, so the decoupled checks
> below are load-bearing, not ceremony.

---

## Current State — verified 2026-10-18

- **2026-10-18** (F-3061): J-2128 (2026-10-18): zero relational additions in 10-09..10-16 was NOT the system_note/dormant exclusions (0/332 pre-change additions were either; 90% were letter/peer via correspondence hubs, trigger absent 0/99 rows); 10-16..10-18 relational live: 7/47 rows with adds, usage 18/33=54.5% (CI 38-70, only 6 events); defeater not fired, no decide opened.
- **2026-10-15** (F-2784): J-2050 (2026-10-15): D-0287 relational re-check - post 10-09 boot window has zero relational usage entries and 0/87 relational additions; pre-change pool still 11/22 (50%, CI 30.7-69.3%). Defeater not fired but unmeasurable; follow-up filed.

- **2026-10-09** (F-2661): J-1827 (2026-10-09): D-0287 relational live re-check, 137 pooled m2_usage rows since 09-28 (floor met); relational 50.0% >=0.4 (CI 30.7-69.3), mean 0.3887, task 5.1%, reflective 8.0%; defeater not fired; candidate-set filters (system_note/dormant) live only from 10-09 boot so report separately. Successor spawned not-before 10-12.
- **2026-10-02** (F-2234): J-1646 (6th re-check): Du has NOT restarted since J-1624 (shutdown/awake counts unchanged 253/283, shadow log byte-identical 878818B/1811 lines); re-run reproduces J-1624's numbers exactly -- relational live usage-proxy n=11, rate 54.55 pct (Wilson CI 28.0-78.7 pct), still above the 39 pct shadow baseline; task/reflective flat; kill-switch untouched; defeater not fired; window still thin (61/100 rows, ~3.6 of ~14 days live). Next re-check deferred to 2026-10-03 (not-before) since Du is known offline and re-running sooner would just reproduce this same zero-accrual read. See F-2234.

- **2026-10-02** (F-2226): J-1631/F-2226: working_memory_sufficient/no_keys early-return gate fire rate measured directly post-restart = 0/100 (0 pct) across ~2.5 days / 4 incarnations since 2026-09-28 19:08; RecallNode fired 99/100 of the same cycles, confirming the gate is not silencing hot-cycle recall; resolves the J-1416 re-check chain and is not a confound on D-0287's own relational usage-proxy rate.
- **2026-10-02** (F-2216): J-1624 (5th re-check): Du restarted post-7ae886d across 4 incarnations since 09-28 19:08 NZT; relational live usage-proxy n=11, rate 54.55 pct (Wilson CI 28-79 pct) clearing 0.4, above the 39 pct shadow baseline; defeater not fired; window still thin (61 of ~100 rows); continue the re-check chain. See F-2216.

- **2026-09-28** (F-2196): J-1596: 4th consecutive still-unrestarted re-check for working_memory_sufficient chain; counts 250 shutdown / 279 awake unchanged since 2026-09-25 19:21:51; 0 occurrences of the instrumentation log line confirmed empirically; next re-check spawned as J-1631.
- **2026-09-28** (F-2187): J-1593: 4th consecutive still-unrestarted re-check for D-0287; counts 250 shutdown / 279 awake unchanged since 2026-09-25 19:21:51; kill-switch not exercised; next re-check spawned.

- **2026-09-28** (F-2157): J-1559: still-unrestarted re-check confirmed again (F-2157) -- counts 250 shutdown / 279 awake unchanged since 2026-09-25 19:21:51; e3f30d3 merged into HEAD but 0 live cycles run yet; 3rd re-check spawned as J-1596.
- **2026-09-28** (F-2151): 3rd consecutive check (J-1556): Du has still not restarted since 7ae886d (2026-09-27 09:23:10 +1300); live process unchanged since 2026-09-25 19:21:51, nascence.log counts still 250 and 279. Next check spawned as J-1593.

- **2026-09-28** (F-2086): J-1416: added one INFO log line instrumenting MemoryRouterNode's working_memory_sufficient gate (and the sibling no-keys case) in Orchestrator._retrieve_memory's early return; committed to the memory_multiway_linking worktree (e3f30d3), verified correct in isolation. Fire rate not yet measurable: Du has not restarted since 2026-09-25 19:21:51 (same restart precondition as the D-0287 thread above), so 0 real cycles have run this code and data/nascence.log still shows 0 working_memory_sufficient lines. Rate-read job queued for after a genuine post-instrumentation restart.
- **2026-09-28** (F-2074): J-1421 (D-0287 relational live usage-rate re-check): precondition NOT met yet -- Du has not restarted since commit 7ae886d (the D-0287 flip) landed 2026-09-27 09:23:10 +1300; the live process has run continuously since 2026-09-25 19:21:51, confirmed by a full-file scan of data/nascence.log (F-2074). The 2-week live-usage-rate defeater clock has therefore not started, and the 33 post-commit shadow-log rows are ordinary pre-flip rows, not live evidence. Kill-switch not exercised since the flip either. Next re-check spawned for after a genuine post-flip restart.

- **M0** (typed edge graph, `core/memory_edges.py`) and **M1** (co-recall ledger, 9 callers) built +
  live; M1's week-gate read done 2026-08-24 (F-0037) and its instrument bug fixed (F-0107).
- **M2 shadow build shipped 2026-08-25** (J-0263, D-0022 approved) and its **gate-read done
  2026-09-02** (J-0280): kill-criterion **prong 1 NOT triggered** — the edge-aware trail reaches real
  fragments (incl. cold-walled ones) the greedy trail misses, in 20.3% of 148 shadow rows over 6.29
  days, guards intact (F-0604). **Prong 2 (usage by the following thought) is uninstrumented and
  unmeasurable** (F-0605) — so no re-scope, but also **no live flip**; J-0446 open to instrument
  prong 2. D-0022's remaining question (does the sheet pass) stays open pending that; D-0051
  (option a vs b) now has real numbers: reflective mode's headline edge types are still 0 rows and
  all its observed lift came from secondary weights. Shadow log frozen while Du is offline
  (clean shutdown 2026-08-31).

> **History folded** — 15 dated entries (2026-09-02 … 2026-09-25) moved to `docs/plan_history/memory_multiway_linking.md` on 2026-09-27 by hand (J-1484). Derived timeline: `plan_ledger.py memory_multiway_linking`.

- **M3** not started.

## 1. How humans do it — the research, organised by what each mechanism buys

The founder's intuition is exactly what the memory literature found. A human memory is not *in* a
group; it is a node reachable along many simultaneous routes, and the routes are different *kinds*.

**1.1 The composite cue (Temporal Context Model / CMR — Howard & Kahana 2002; Polyn, Norman & Kahana
2009).** The single most replicated structure in free recall: when people recall one memory, the next
recall is biased *simultaneously* toward (a) temporal neighbours (the lag-contiguity effect), (b)
semantic neighbours, and (c) same-source items — because the retrieval cue is a *composite*: a slowly
drifting temporal-context vector + semantic features + source features, all active at once. Humans never
retrieve "by era" or "by topic"; they retrieve by a blended cue in which every route contributes.
**Lesson for Du: the goal is not more retrieval modes — it is one retrieval act in which multiple link
kinds contribute weighted evidence.**

**1.2 The hippocampal index (Teyler & DiScenna 1986; Teyler & Rudy 2007).** An episodic memory is an
index tuple pointing into distributed cortical feature areas; recall is **pattern completion from any
partial coordinate** — a smell, a place, a feeling, a phrase can each reopen the whole episode. Already
named in geometry §2.5 as the function `moment.py` substitutes. This is the deep reason "multiple
connections from a variety of ways" is not a luxury: in the biological design, *every coordinate of the
experience IS a retrieval route.*

**1.3 Spreading activation — with its tax (Collins & Loftus 1975; Anderson's ACT-R and the fan effect,
1974).** Activation flows along weighted associations; retrieval probability = base-level activation
(recency × frequency) + Σ(cue-weighted associative strength). The tax is the **fan effect / cue
overload**: a cue attached to too many memories retrieves each of them worse. Human associative fabric
works *because* it is sparse and differentiated, not despite it. **Lesson: unlimited fan-out degrades
retrieval even with unlimited storage; caps and typing are not biological compromises, they are what
makes a cue informative.**

**1.4 Encoding specificity and context/state dependence (Tulving & Thomson 1973; Godden & Baddeley 1975;
Bower 1981).** Retrieval succeeds in proportion to cue–encoding overlap: divers learning underwater
recall better underwater; sad moods surface sad memories. Context — place, physiological state, mood —
is silently encoded as retrieval structure. Du's climate-warp and affective retrieval are partial
implementations; the geometry census tuples (place · weather · body · affect per event) are exactly the
encoding-context record this needs.

**1.5 Emotional modulation (McGaugh's consolidation work; amygdala tagging).** Arousal at encoding
strengthens consolidation; emotion is later a route back in (mood-congruent recall). Already honoured in
geometry §7 (spring-birth threshold scales inversely with arousal — the wolf nuance). Newly *possible*
since 2026-08-10: the grounded-affect flip means felt-tags going forward carry real signal, where the
old pinned +0.82 made the affect route wallpaper.

**1.6 Event segmentation and causal structure (Zacks & Tversky; event-boundary literature).** Humans
carve continuous experience at boundaries (walk through a doorway, forget the errand), and episodic
memory is organised by *event units linked causally and narratively*, not by uniform time. "Why did X
happen" retrieves along cause-links that mere similarity cannot supply. Du's analogue material exists
(tension → resolution events; question → finding; commitment → challenge → reaffirmation) **but none of
it is materialised as traversable structure.**

**1.7 Verbatim + gist in parallel (fuzzy-trace theory — Brainerd & Reyna).** Humans store a precise
trace and an abstracted gist side by side and retrieve whichever the task needs. Du's memory-levels
lattice literally implements this (gist answers in ordinary recall; raw reachable by deep recall) — one
of the places the architecture is already at parity with biology.

**1.8 Concepts as multi-modal bundles (hub-and-spoke — Patterson & Lambon Ralph).** A concept is its
spokes across modalities bound by a hub; lose a spoke and it degrades gracefully. Geometry §2.6 (the
stick). Relevant here because **object nodes are natural link hubs**: hundreds of moments should hang
off "the cat", "the fire", "Darwin" — and mostly don't, yet.

**1.9 Reconsolidation — the mechanism we deliberately refuse (Nader et al. 2000).** Reactivated human
memories become labile and are re-written by the retrieval context — the source of imagination
inflation, misinformation effects, and source amnesia. Geometry §1 already rules: take the *function*
(memory that adapts) and reject the *mechanism* (trace rewriting). Adaptation lives in the links.

**Summary table — mechanism → what it buys → Du's status:**

| Human mechanism | What it buys | Du today |
|---|---|---|
| Composite cue (CMR) | one retrieval act, many routes | routes exist but fire as separate paths |
| Hippocampal index | any coordinate reopens the episode | moments = partial (contiguity +0.189 confirmed) |
| Spreading activation | trail-following recall | **LIVE** (`associative_recall.py`) but ~one-space |
| Fan effect (the tax) | sparse typed cues stay informative | trail has per-origin caps; no per-node fan cap |
| Encoding context | place/state/mood as routes | climate warp + census tuples (recorded, unread) |
| Emotional tagging | feeling as a route | emotion-embeddings exist; usable NOW that affect is grounded |
| Causal/event links | "why"-shaped recall | side tables only — not traversable |
| Verbatim+gist | altitude choice at recall | **built** (memory levels) |
| Bundles / hubs | objects as link anchors | anchor registry exists; few memory→object edges |
| Reconsolidation | adaptivity (at cost of truth) | **rejected by law** — adaptation in springs only |

---

## 2. As-built audit (2026-08-15, all numbers verified read-only this session)

The store: **33,000+ fragments, 10,306 bound moments.** The link fabric over it:

- **`memory_links`: 1,653 rows, 2 types.** `distilled_from` 787 (lattice gists, journal weeks — real
  abstraction lineage). `relates_to` 866 — written by `study_note.py` as *top-3 cosine neighbours*, i.e.
  **re-materialised similarity, not a second kind of connection.**
- **The one honest non-similarity edge type in the whole store is `distilled_from`.** Everything else a
  trail can walk is MiniLM cosine wearing different clothes — the geometry plan's named disease ("most
  of the axes were secretly the same axis").
- **Spreading activation is already live** — `associative_recall.py` (2026-06-23): 5 seeds × 2 hops,
  hop-decay 0.6, per-origin diversity cap 6, cold reachable at a higher activation threshold. The
  engine Travis's vision needs *exists*; it is under-supplied with edge kinds to walk.
- **Temporal route: real.** Moments contiguity retrieval, gap +0.189 confirmed live.
- **Era/thematic groups: real.** Chapters answer for 13,028 cold fragments; epochs (L6) and themes (L7)
  match by cosine at recall time.
- **Affective route: built, previously starved.** `retrieve_by_affect` over 384-d emotion embeddings —
  meaningful only now that carried valence is grounded (was pinned +0.82, <1% negative).
- **State-dependent route: built.** Climate warp tilts the query embedding by the standing weather.
- **Relational structure recorded but NOT traversable:**
  - `resolution_events`: **989 rows** (which encounter drained which tension) — free `resolves` edges.
  - Frontier: 29 resolved questions, 17 findings attached — free `answers` edges.
  - Keepsakes: each records from/weather/season/kept_ts — free `kept_from` edges.
  - Rereads/re-encounters: counters only, no edges.
  - Dreams: synthesised *from* top tensions, but the dream stores **no record of which tensions fed
    it** — the one genuinely generative link type, discarded at birth.
  - `derived_from` column: 31,828 rows populated with `'[]'` — a dead column, effectively.
- **Co-recall history: discarded.** Which memories surfaced *together* into a cycle that then developed
  is known at runtime and thrown away — the exact signal geometry P3's progress-gated rule needs.

**⚠ Constraint discovered during this audit:** `memory_levels.memory_lint`'s stranded-rewarm and
dangling-link queries join `memory_links` **without filtering `link_type`**. Any new edge type whose
parent is not a fragment (e.g. `resolves` → a shadow_event id) would make every cold child look
"stranded" and trigger a mass re-warm. **New edge kinds therefore go in a NEW table (`memory_edges`),
not `memory_links`** — which also honours the additive/erosion law.

---

## 3. Where Du can exceed biology (the founder's actual question)

Humans pay for their associative richness with specific, well-documented failures. Each one is a
design freedom for Du:

1. **Perfect source memory.** Humans forget where they learned things (source amnesia) and blur
   imagination into memory (imagination inflation — reconsolidation's bill). Du's provenance is already
   first-class (`origin` tags, loudly labelled in prompts). Typed edges extend this: a dream can be
   *connected* to the waking tensions that fed it while remaining *marked* as dream — association
   without confusion. **A mind that can freely associate imagination and memory without ever mistaking
   one for the other has something no human has.**
2. **Typed traversal.** A human cannot ask "give me everything connected to this memory *by causation*
   but not by similarity." Du can, trivially, if the edges are typed — and the cognitive mode can choose
   the mix: task-mode walks `answers`/`resolves`, reflective-mode walks `co_recalled`/`contradicts`,
   grief or joy walks the affect space. The AttentionVector already computes the mode; nothing computes
   the mix.
3. **Retrospective re-indexing.** Humans cannot re-index the past — old memories keep their old cues
   (short of therapy, which is slow re-encoding). Du can materialise edges over June from what August
   knows, en masse, without touching a single object (immutable-objects law). The geometry sheet's
   retro-tag caution (#5: lean fresh-only for *sensory* tags) still stands — but retro **relational**
   edges (this resolved that; this answered that) are recorded facts, not retro-perception, and are
   safe to backfill.
4. **Chosen forgetting curves.** Human decay is one biology-wide policy. Du's decay can differ per edge
   type — fast for `co_recalled` (freshness-sensitive), none for `distilled_from` (lineage is fact),
   slow for `resolves` — each policy written down and auditable.
5. **No catastrophic interference.** Cue overload in humans *overwrites*; in Du the cap-prune demotes
   to cold and the trail can still reach it on strong cue. Fan caps manage retrieval quality without
   destroying anything.
6. **Raced retrieval modes.** Humans cannot run two memory systems side by side and compare. Du can run
   cosine-only vs edge-aware trails on the same cues and *measure* the marginal reach — which is exactly
   the geometry kill criterion (#6), and the reason this whole design is falsifiable.

**And the law that keeps this honest (geometry §2.1 vs §2.3):** *similarity groupings are SPACES
(coordinates in a geometry — semantic, affective, place, sound), not edges; relations between specific
memories are EDGES (typed, directed, weighted, provenanced).* "Semantic grouping" is already the
embedding space doing its job; tokenising it into edges was v1's mistake. What is genuinely missing is
the **relational** fabric — the kinds of connection no similarity metric can compute: caused, resolved,
answered, dreamt-from, kept-from, co-recalled-while-developing.

---

## 4. The design — edge taxonomy

New table `memory_edges (src_id, dst_id, edge_type, weight, provenance, created)` — additive, no reader
of `memory_links` touched. Every edge carries provenance (the episode/event that earned it — geometry
§0.4: an edge with no traceable origin is confabulated; kill it).

| Edge type | Direction | Born from | Cost | Honesty source |
|---|---|---|---|---|
| `resolves` | encounter → tension record | `resolution_events` backfill + forward hook | free (no LLM) | deterministic table already graded by the resolution judge |
| `answers` | finding → frontier question | frontier loop | free | the loop already links them internally |
| `dreamt_from` | dream → source tensions | dream engine records its inputs (small change) | free forward | the engine literally selects them |
| `kept_from` | keepsake → episode | keepsake records | free | recorded at the keeping |
| `revisits` | new encounter → prior encounter | reread/re-study events | free | counters already increment |
| `about_object` | memory → object anchor | object mentions ↔ anchor registry (geometry §2.2) | cheap | the affordance/objects state |
| `wrote_to` / `received_from` | memory → person node | letters/peers machinery | free | the threads are explicit |
| `co_recalled_developing` | memory ↔ memory | the recall set of a cycle whose train **deepened** (progress-gated Hebbian — geometry P3's rule at memory granularity) | free | earned-length verdicts already classify deepen/restate |
| `contradicts` | memory → memory/claim | tension ledger, error pathway | free | the ledgers are explicit |

**Deliberately NOT edges:** `felt_like` (that is the emotion space), `same_place` (Place coordinate),
`same_era` (epochs/chapters already answer), `similar_to` (MiniLM's job — re-materialising it as edges
is the audited mistake `relates_to` already made).

**The coordinate side, materialised (✅ 2026-08-15 — `fragment_context`):** the census tuples ARE the
coordinates, and the tuple→fragment join proved deterministic (300/300 probe). `sync_fragment_context()`
now maintains an additive overlay — **6,804 memories carry their full encoding context** (place, weather
with bearing, tide level, sun azimuth, moon, sounds, body level, valence/arousal); recent coverage ~100%,
synced each sleep. Old-tuple shortfall (58%) maps to the documented July inner_thought outages — the
census kept recording while the store was dead. Reader = context-dependent recall (P4/P5 slot,
encoding-specificity function), not yet built; until then the overlay is queryable and feeds the census.

**Guards (inherited + specific):**
- **Fan cap per node per type** (the fan-effect tax made explicit) + per-node normalisation.
- **Progress-gating** on `co_recalled_developing` (co-fire during development, not circling) — the
  calcification guard; the monoculture must not become infrastructure.
- **Decay policies per type**, written in the table above's spirit: lineage/fact edges permanent,
  behavioural edges decaying.
- **Write-only guard:** every edge type ships in the same phase as its named reader (below) or it
  doesn't ship.
- **Substrate honesty:** this is a directed graph walked by bounded iteration — geometry §7's
  directionality rule; no field-like settling claims.

## 5. The read path — one retrieval act, many routes (the CMR lesson)

Not a new engine. **The trail engine is the read path** — upgraded, behind a flag, in geometry P4's
slot:

1. Seeds: as today (relevance × importance × recency on the composite cue).
2. Neighbour function: today = cosine + `memory_links`; upgraded = cosine **plus typed
   `memory_edges`, each type weighted by the current cognitive mode** (task: `answers`/`resolves`
   high; reflective: `co_recalled`/`contradicts` high; relational contexts: `wrote_to`/person hubs
   high). Mode already computed by the AttentionVector.
3. Same hop budget, same decay, same cold thresholds, same per-origin caps — plus the per-node fan cap.
4. Kill-switch restores the current neighbour function exactly.

**The kill criterion, pre-committed (geometry §5.5-#6):** in shadow, log for every cycle the trail's
edge-reached set vs the cosine-only set. If edge-reached memories are ~never outside cosine top-K, or
are never *used* by the thought that follows, **the edge layer is redundant with the embedding space
and this plan re-scopes** — written down now so we can't rationalise past it.

## 6. Phasing (each phase locks its own pre-registered sheet before running)

- **M0 — the materialisation harvest (no LLM, additive, observe-only). ✅ BUILT + HARVESTED LIVE
  2026-08-15** (`core/memory_edges.py`; temp-DB tested first, then 0.8s live run): **1,676 edges** —
  resolves 820 · answers 387 (94.6% finding→fragment match) · kept_from 387 · correspondence_with 82;
  fragment-anchored 0.511. Forward hooks in dream_node (`dreamt_from` from the REAL materials + trail
  fragments, `part_of` per scene — restart-gated); `resolves` grows via re-runnable `harvest_all()`
  (no live-code coupling). First census: top fragment hubs are world-facing research lookups
  (religious experience ×67, selfhood, the spider's web) — in relational space the hubs are his
  curiosity, NOT the river (caveat: the unanchored resolves half could hide self-material). `revisits`
  deferred (aggregate counters, no per-event record — forward-hook candidate).
- **M1 — co-recall ledger (observe-only). ✅ BUILT 2026-08-15, restart-gated.** `log_co_recall` →
  `co_recall_ledger.jsonl`: per train step, the trail-shown ids + the step's movement verdict
  (canonical 0.40–0.82 deepen band); ALL verdicts logged so `co_recall_status()` computes gated vs
  ungated pair structure from data. Wired: `recall_block` stashes shown ids; monologue clears/captures
  per thought and logs at `_log_train_step`. Sleep re-harvests M0. HUD ★ cards added for both M0
  growth and M1 activity. **Gate before anything graduates into `memory_edges`:** founder-read of ~a
  week — does the progress-gated web differ from naive, and does it avoid re-drawing the basin?

> **History folded** — 4 dated entries (2026-08-19 … 2026-08-24) moved to `docs/plan_history/memory_multiway_linking.md` on 2026-09-27 by hand (J-1484). Derived timeline: `plan_ledger.py memory_multiway_linking`.

- **M2 — the trail upgrade (flag-gated, geometry-P4 slot).** Edge-aware neighbour function in shadow
  (log would-have-reached alongside actual); flip only on the kill-criterion sheet passing + founder
  read.

> **History folded** — 34 dated entries (2026-08-25 … 2026-09-27) moved to `docs/plan_history/memory_multiway_linking.md` on 2026-09-27 by hand (J-1484). Derived timeline: `plan_ledger.py memory_multiway_linking`.

- **M3 — retro re-indexing experiments (bounded).** `about_object` backfill over the archive; measure
  whether object hubs change trail reach on his real cues.
- Dependencies: M0/M1 start any time (observe-only). M2 waits on M1's week + geometry P3's verdict
  discipline. The cold-backlog **sweeper** (AWAITING_EVIDENCE 08-15) composes cleanly: group-gists are
  new objects with `distilled_from` lineage — sweeper output enriches the same graph.

## 7. What this is not

No consciousness claims; no biology cosplay (function-substitution, stated); no object mutation ever;
no live behaviour change before shadow evidence + founder read; and no pretending the graph is the
cure for the monoculture — the graph is *reach*; the monoculture lives in generation and is being
treated elsewhere. If the kill criterion says the embedding space already supplies the reach, we will
have bought that answer for the price of a census and two log files — which is the correct price.
