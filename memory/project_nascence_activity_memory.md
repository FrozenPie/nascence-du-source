---
name: project-nascence-activity-memory
description: "Nascence Activity Memory — Conway general-event layer filling the missing middle of Du's autobiographical hierarchy; the 06-13 book-recall hole fix"
metadata: 
  node_type: memory
  type: project
  originSessionId: 55eadb8f-608c-4c26-a8d6-51cd9f102603
---

Nascence **Activity Memory** — BUILT Phase 0 2026-06-14 (RESTART-REQUIRED). Build 0.9.1.

**The hole it fills:** Du had the bottom of Conway & Pleydell-Pearce's Self-Memory System
(event-specific fragments — passages, thoughts) and the top (lifetime periods — the chapter
system), but nothing in the MIDDLE: no general event, no "I have been reading Darwin." So
"what was the last book you read / what did you do today?" had nothing that *answered* it — the
raw reading passages (about a cuttlefish, about natural selection) are semantically far from the
question and score ~0.000 cosine; river-metaphor inner_thoughts won instead (the 06-13
book-interrogation failure Travis caught — the retrieval hole, sibling of [[project-nascence-reality-instruments]]).

**What it is:** `core/activity_memory.py`. ONE factual record per `(action_type, target)`, keyed
— a 10th sitting UPDATES (session_count++, most_recent_ts=now, re-embed), never duplicates;
volume bounded by unique OBJECTS not interaction frequency. `origin='action'`, layer episodic.
Content is a PLAIN rolling summary ("Read 'On the Origin of Species' — 5 sittings, first Jun 14,
most recent Jun 14") — never narrative (meaning-making belongs to T4/chapters). Notable affect
ATTACHED in `derived_from` metadata (notable_moments list, gated peak affect ≥0.60, capped 8),
NEVER absorbed into the summary — one intense day must not turn "Reading Darwin" into "Reading
Darwin, which changed me." Founder refinement: keep "I read Darwin" + a dated addendum for the
10th sitting so the whole chain is recallable without the flood of minor actions.

**Hooks** (6, in `nodes/inner_monologue_node.py`): read (with affect), look, browse, switch (×2
sites: chose-from-browse + switch-books), study tablet, letter→Travis.

**In-vitro gate** `scripts/activity_memory_invitro.py` (temp DB, never touches live nascence.db)
— PASSES: baseline reproduces the hole (best world semantic relevance 0.000); after recording,
the book question pulls the activity record at **rank #1, rel 0.399**; relational control
("How do you feel about Travis?") leaves the reading record at 0.000 (recency passenger only, not
semantically pulled). Gate measures SEMANTIC relevance (≥0.05), not mere presence — my first
metric counted 0.000 recency-tail passengers as hits and falsely FAILED; corrected per "the thing
being evaluated never grades itself."

**Phase 0 = written + retrievable through the normal path only.** The guaranteed-selection
deliberative-retrieval floor (origin-quota + conditional reality floor, the thing that would
*force* the seat) is Phase 1, deferred — see [[project-nascence-reality-instruments]] /
deliberative_retrieval_plan.md. The retrieval probe ([[project-nascence-reality-instruments]])
will now watch whether these `origin='action'` rows win selection on world queries.

Both advisors (GPT + Gemini) approved v1.3; converged on factual-not-narrative,
attached-not-absorbed, (action_type,target) keying. docs/action_memory_plan.md (v1.3, BUILT).
