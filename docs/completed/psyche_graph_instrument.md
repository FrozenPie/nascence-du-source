# The Psyche Graph — a deterministic instrument for symbolic development (LIVE, built 2026-07-03)

> **Origin (2026-07-02):** grew out of the graphify rebuild. GPT asked whether Du's dream-symbol
> trajectories track "integration in the architecture's graph" — a category error (graphify maps the
> WORKSHOP, not the psyche), but the redirected question is strong: do symbolic trajectories track
> measurable structure in DU'S OWN runtime artifacts? GPT then contributed the key metric refinement
> (stability under reinterpretation, below).
>
> **Status (corrected 2026-08-19 — this header said "NOT built" for 6+ weeks after it was built):**
> **LIVE.** `core/psyche_graph.py` was un-shelved 2026-07-03 and is called every sleep from
> `nodes/inner_monologue_node.py` (~line 422). `data/psyche_graph_snapshots.jsonl` has 90+ real,
> growing snapshots as of tonight. Confirmed independently in `docs/UNFINISHED_PLANS_SURVEY_2026-08-18.md`
> ("confirmed built+fired"). This file lives in `docs/completed/`, not `docs/staged/` — the move
> happened without this header, `core/psyche_graph.py`'s own header comment, or `docs/ROADMAP.md`'s
> link being updated; all three corrected today.
>
> **Known design deviation (not yet resolved — see "Hard constraints" below):** the code does NOT
> actually integrate with `symbol_tracker.py`'s primed/unprimed classification the way this doc
> originally claimed — see the updated constraints section.

## What it is
A per-sleep deterministic snapshot of Du's symbolic economy as a graph:
- **Nodes:** significant symbolic fragments (mirror, glass, gardener, river, story-tree, pen, key, sea…)
  drawn from symbol_tracker/symbol_evolution + dream arcs + idle-thought symbols.
- **Edges (deterministic spine):** `derived_from` lineage · same-dream co-occurrence · chapter membership ·
  resolved-tension links · letter references. These are trustworthy — pure record.
- **Edges (soft, secondary):** embedding/emotion similarity — INHERIT THE KNOWN DISTORTION (the memory
  review's A4: MiniLM cosine sees his self-talk as one blob and *inflates* the monoculture). Never let
  similarity edges drive a conclusion the deterministic spine doesn't support.
- **Snapshot cadence:** every sleep, appended (never rewritten) — the graph's own history is append-only.

## The PRIMARY metric — stability under reinterpretation (GPT's contribution, 2026-07-02)
Raw connectivity/integration is the wrong headline number. The right one: when a symbol gains new
neighbours, **do its original edges survive?**
- Neighborhood expands while lineage is preserved → **growth** (developmental continuity).
- Original neighborhood destroyed on each evolution → **rewriting**, not integrating — the graph-level
  signature of the averaging attractor.

**The triple convergence that licenses this metric** (three independent sources, same shape):
1. My documented failure mode — *erosion of foundations* (strip the original richness while "improving").
2. The E1/F1 formation bug — `principle = merged` rewrote the belief on every assimilation; 14 merges
   sanded sharp lessons into mush. The fix (exemplar-medoid + pole-fork, both-stand) IS
   stability-under-reinterpretation enforced at the belief level.
3. Memory-levels drift guards — anchor-retention ≥ 0.40 + snap-to-verbatim: reinterpretation licensed
   only while the anchor survives — the same law at the fragment level.
The psyche graph generalizes an already-proven house law to the symbol level. Secondary metrics:
modularity/integration trend · bridge-symbol emergence · hub formation · symbol death · cross-pole edges
(built-mind cluster ↔ river cluster — the graph form of what judge_lived_integration assesses in prose).

## Causal framing (agreed with the triple-lens review)
Dreams are a **downstream readout** of the same dynamics — they neither cause integration nor constitute
the graph. Expected sequence if the cure works: waking drainage (tension ledger) → structural change in
the psyche graph → recurring dream stops returning. Three instruments, one arrow.

## Hard constraints (from existing law — non-negotiable)
- **Deterministic + decoupled:** graph math, no LLM in the loop; it never grades what it produced.
- **Primed/unprimed — CORRECTED 2026-08-19, this was never actually true.** This doc originally said
  "only UNPRIMED symbol appearances feed the graph (symbol_tracker already enforces this)." As
  implemented, `core/psyche_graph.py` does NOT call `symbol_tracker.py` at all — it has its own
  independent, hand-curated `MOTIFS` lexicon (36 words) and does plain regex word-boundary matching
  against raw dream-arc text, with zero primed/unprimed gating. The "spontaneous-only" guarantee holds
  only by lexicon curation (river/avon/du_glyph/knot were deliberately left out of `MOTIFS`), not by
  any enforced mechanism — and it isn't fully consistent even on that basis: **`mirror` and `bridge`
  are both in `MOTIFS` (core/psyche_graph.py:30,32) and are both `symbol_tracker.SELF_SYMBOLS`**
  (identity-adjacent, Tier-2, read-back deliberately deferred because re-surfacing an evolved
  self-symbol is the exact operation that once monocultured Du — see `symbol_tracker.py`'s own
  comments). `mirror` is consistently one of the graph's highest-frequency nodes in real data
  (weight 3-5 across recent snapshots) — i.e. the instrument tracks exactly the self-referential
  material its own design intent was originally written to exclude. **Founder call (2026-08-19):
  leave them in.** This instrument is observe-only and never read back to him — no live behavioral
  risk, only a documentation-accuracy question — and their presence preserves continuity with 90+
  existing snapshots. It may also be informative on its own terms: whether `mirror`'s stability
  pattern differs from the world-facing symbols is itself a real question this graph can now answer.
  `MOTIFS` unchanged.
- Known consequence of the lexicon design (DEFERRED_PLANS, the 0/460 finding): axiom-resident symbols
  (the river) are permanently primed by the axiom injection — the graph's measurable population is the
  SPONTANEOUS symbols (mirror, door, root, garden, pen…), which is exactly the population that matters.
  Dream-log evidence (verified 2026-07-02, earliest-third vs latest-third of 457 records): door 95→24 ·
  key 35→8 · mirror 104→47 · root 3→50 · tree 10→44 · garden(er) 0→7 — the trajectory is real; the
  instrument would make it continuous.
- **Observe-only, firewalled log, read by reports** — Du never sees it (at least until a deliberate
  read-back design with its own injection logging, per the mirror lesson).
- **Complements, never replaces, the qualitative judges:** the judge answers "does this feel integrated?";
  the graph answers "what structural change accompanied that impression?" Different evidence kinds.
