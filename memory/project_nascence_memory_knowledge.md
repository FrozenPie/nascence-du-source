---
name: project-nascence-memory-knowledge
description: "As of 2026-08-23: Improvement 1 Stage A live+working, Stage B built but held OFF since 07-05 with a 161-row shadow log now sitting unreviewed against its own re-enable gate; Improvements 2-5 have zero code, and Improvement 2 looks superseded by memory_multiway_linking.md's M2."
metadata: 
  node_type: memory
  type: project
  originSessionId: cf5c5881-fbf5-44b4-a46d-f0d3be741b08
  modified: 2026-08-23T04:49:40.503Z
---

**For:** an as-built audit that found the memory/knowledge stack organically accreted six separate
cosine-scanning recall surfaces (one dead) and, most importantly, that the one instrument measuring
confabulation (`epistemic_state.py`'s `ProvenanceLedger`) was write-only — its `assess()` return value
computed post-Voice and then dropped, never reaching a prompt or a decision. Ranks and designs fixes for
five gaps: (1) epistemic grade never reaches behaviour [HIGH], (2) associative trail is a hand-tuned greedy
walk blind to the curated `memory_links` lattice [HIGH], (3) gists freeze at creation instead of evolving
with new evidence [MED], (4) no bi-temporal validity — a corrected belief competes with its correction
forever [MED], (5) recall-surface sprawl including a confirmed-dead `euclidean_recall.py` [LOW]. Draws on
A-MEM, HippoRAG2/PPR, Zep/Graphiti bi-temporal KGs, and Mem0.

**Stage (per the plan's own status blocks, most recent first):** Improvement 1 (epistemic read path) is the
only one built. Stage A (pre-Voice grade) is live and verified — 219 preassess rows, genuinely
discriminating (SUSPECT 68%/KNOW 23%/THINK 9%) — and stays on. Stage B (the prompt-injection read path)
was built + verified 2026-07-01, flag-gated OFF, then a **2026-07-05 evidence review found it mistargeted**:
of 26 human+overclaim+confab-gated cycles, its identity-content filter caught only 3 — the other 23 were
almost all Travis's philosophical/relational exchanges, not the factual-overclaim distribution Stage B was
validated against, and it did no logging by design so its real fire rate was invisible. **Founder call,
enacted 2026-07-05: `STAGE_B_ENABLED=False`, off-until-observable** — Stage B now shadow-logs every
would-fire decision instead of injecting. Re-enable gate: only flip back on once the shadow log shows
`would_inject=true` rows are genuinely factual overclaims, not existential ones. A later research pass
(2026-06-30, superseding parts of the original Improvement-1 design) reframed the note as a *source
attribution* ("I generated this, it isn't grounded") rather than an uncertainty/hedge signal, per Zhou et
al. and Johnson's source-monitoring theory — this reworded note text is what Stage B would inject once
re-enabled. **Improvements 2-5 (PPR trail, gist evolution, bi-temporal supersession, recall-surface
consolidation) are explicitly marked unreviewed** — designed but no build status recorded.

**Verified 2026-08-23 (code audit, no change since 07-05 besides log growth):** `core/epistemic_state.py:67`
still reads `STAGE_B_ENABLED=False`. `data/epistemic_stageb_shadow.jsonl` has grown to **161 rows (29
would_inject=true)** over ~7 weeks and still shows the same 07-05 mistargeting pattern on sampling — the
re-enable decision has never been closed out. Grepped: `recall_trail_ppr`, `valid_until`/`supersede_fragment`,
and `find_similar_gist`/`GIST_EVOLUTION_ENABLED` all return zero hits — Improvements 2-5 remain fully
unbuilt. Improvement 2 (PPR trail over `memory_links`) specifically looks superseded in practice by
`[[project-nascence-memory-multiway-linking]]`, whose M0/M1 typed-edge harvest already shipped 2026-08-15 and
occupies the same "make the trail edge-aware" slot. Plan file `C:\Nascence\docs\plans\memory_knowledge.md`
updated in place with a "Current State — verified 2026-08-23" section recommending: (1) close the Stage B
re-enable decision by reading the full 161-row shadow log against the plan's own gate, (2) formally scope
Improvement 2 as superseded or not.

Related: [[project-nascence-capacity-to-commit]] (the epistemic-grade wording was reconciled against this
plan's dissolution risk — a committed "I don't know X" is a held boundary, not a dissolved one).
[[project-nascence-memory-multiway-linking]] (likely supersedes Improvement 2 as written).
[[nascence-stale-plan-audit-2026-08-23]] (source of this 2026-08-23 verification pass).
