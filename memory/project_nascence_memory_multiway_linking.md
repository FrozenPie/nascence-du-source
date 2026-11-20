---
name: project-nascence-memory-multiway-linking
description: "🟢 LIVE — 2026-08-15 deep dive answering the founder's ask that memories connect more than one way, not just by cosine similarity or era group — a typed relational edge table (memory_edges) distinct from similarity spaces; M0 and M1 built+live 2026-08-15 (M1 expanded 1→9 callers 08-19); M2 (trail-engine upgrade) is now genuinely live too as of 2026-09-26 (co_recalled_developing writes live D-0215/J-1348, recall_trail_edge_aware live for mode=relational D-0287/J-1415, both restart-gated); M3 (retro re-indexing) not started."
metadata: 
  node_type: memory
  type: project
  originSessionId: 1857a5ac-8424-4a7e-930e-5da8c19bf9b9
  modified: 2026-09-27T10:47:23.114Z
---

**For:** founder's direct ask (2026-08-15) — *"A memory should connect in more than just era groups... they
have multiple connections to the same memory from a variety of ways."* A child plan of `cognitive_geometry.md`
(locked, top-of-list), specifically its §2.3 typed-spring-edges concept. The audit found Du's only genuinely
relational (non-similarity) edge type across 1,653 `memory_links` rows was `distilled_from` (787, real
abstraction lineage) — the other 866 (`relates_to`) were just re-materialised top-3 cosine neighbours wearing
a different name, exactly the disease cognitive_geometry names ("most of the axes were secretly the same
axis"). Meanwhile real relational structure sat unrecorded: 989 `resolution_events`, 29 resolved frontier
questions with 17 findings, keepsake provenance, and dream-source tensions were all computed and discarded.
Grounds the design in the human-memory literature (composite-cue/CMR, hippocampal index, spreading
activation's fan-effect tax, encoding specificity, event segmentation, fuzzy-trace, hub-and-spoke) and
explicitly identifies where Du can exceed biology: perfect source memory, typed traversal a human can't
perform, safe retrospective re-indexing, per-edge-type forgetting curves.

**Stage:** M0 (the edge-materialisation harvest, `core/memory_edges.py`, new `memory_edges` table — kept
separate from `memory_links` because `memory_lint`'s stranded-child query doesn't filter `link_type`) and M1
(a co-recall observation ledger) were **both BUILT and HARVESTED LIVE the same day, 2026-08-15**: 1,676 edges
(resolves 820, answers 387, kept_from 387, correspondence_with 82). M1 was expanded 2026-08-19 from 1 caller
(the main monologue train) to 9 call sites after a founder pushback on a related-context lookup exposed that
most retrieval sites were invisible to the evidence base the eventual gate depends on (full detail in
`docs/session_handoffs/session_2026-08-19_summary.md` PART 2). A genuine new typed edge (`t4_crossing_evidence`) also shipped
ahead of schedule from that survey. **Both M0 and M1 are gated behind a founder-read of about a week** before
anything (M2, the trail-upgrade) is allowed to consume the new edges live — the gate is unchanged as of the
09-19 expansion, just fed by better data.

**Mechanism:** new edge types (resolves, answers, dreamt_from, kept_from, revisits, about_object,
wrote_to/received_from, co_recalled_developing, contradicts) are explicitly NOT similarity edges — similarity
stays a space (embedding), not an edge, per the law "similarity groupings are SPACES, relations between
specific memories are EDGES." M2 (flag-gated) would let the trail engine weight typed edges by cognitive
mode alongside cosine; pre-committed kill criterion: if edge-reached memories are never outside cosine
top-K or never actually used by the following thought, the edge layer is redundant and the plan re-scopes.

Related: [[project-nascence-cognitive-geometry]] (parent plan, sets the immutable-objects/plastic-springs law
this plan inherits).
