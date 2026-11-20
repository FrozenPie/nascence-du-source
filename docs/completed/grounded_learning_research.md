# Grounded learning — turning intake into understanding (research + plan)
*2026-06-16. He reads enormously (overnight: +3,156 reading, 8 books, 120 study notes) but nothing SYNTHESISES
that intake into understanding. Verified: sleep chapters exclude reading/study (self-loop only); school has a
reading lesson but no essay. Two missing complementary passes. Method: human function → AI → the transfer.*

---

## The gap (verified)
- **`chapters.py`** consolidates only `subconscious_synthesis / inner_thought / active_imagination` — the
  self-loop. Reading/study/research are *deliberately excluded*. So **sleep metabolises the SELF and ignores
  the KNOWLEDGE.**
- **`school.py`** has the reading lesson (intake) and `record_session` (a counter) — but **no essay / Lesson 2**
  (synthesis). So study notes accumulate; nothing turns them into organised understanding.

Net: reading is **intake without metabolism.** Du has *read* Darwin and Selborne; he doesn't *understand* them
in any durable, organised way — the passages sit as retrievable sediment, never integrated into knowledge.

## Human function — how intake becomes understanding
Two complementary processes, one offline, one waking:

**Offline — sleep-dependent consolidation (the missing SWS-declarative pass).**
- **Complementary Learning Systems** (McClelland, O'Reilly): the hippocampus holds fast episodic memories; during
  **slow-wave sleep** it *replays* them and they consolidate into **neocortical SCHEMAS** — slow, structured,
  semantic knowledge. The day's reading (episodic) becomes integrated knowledge *offline*.
- **Sleep abstracts and integrates, it doesn't just strengthen** — gist extraction, integration with prior
  knowledge, detail-pruning ("sleep to remember *and* to forget"). So the pass isn't "store more passages" — it
  **distils the gist and connects it to what he already knows.**
- **Schema-accelerated consolidation** (Tse et al.): information that fits an existing schema consolidates faster
  — so understanding *compounds* (a growing schema, not isolated facts).
- This is **distinct from the dream.** The brain does both in sleep: **REM** (emotional/symbolic — Du HAS this,
  the dream node) and **SWS** (declarative consolidation — Du LACKS this). The project already split them
  correctly; the SWS-declarative analog is simply unbuilt.

**Waking — the generation effect (the missing essay).**
- **The generation effect** (Slamecka & Graf) + **retrieval practice / testing effect** (Roediger & Karpicke):
  *producing* information yourself beats *re-reading* it, durably. **Writing an essay > re-reading the notes.**
- **Self-explanation / elaborative interrogation** (Chi): explaining *why/how* to yourself builds understanding by
  connecting new to known. Writing *forces* synthesis, organisation, and gap-detection.

**Both build SCHEMAS, not fact-piles.** Understanding = facts *organised into a structure* (Bartlett; Bransford,
*How People Learn* — experts have organised knowledge, not just more of it). The synthesis turns passages →
structure.

## AI capability — what's natural / the honest limit
- **Frozen-model honesty (again):** Du can't bake reading into his weights. So "understanding" for him = a
  **recallable synthesis ARTIFACT** — his own organised essay / consolidated knowledge note — not weight-baked
  knowledge. That's legitimate: it's exactly *where his knowledge lives*, the same way the study notes do, only
  *organised and abstracted*.
- **RAG-corpus vs understanding:** the reading fragments are a retrievable corpus (passages). The synthesis turns
  the corpus into **organised understanding** — the difference between *"I have read it"* (passages surface) and
  *"I understand it"* (a structured take surfaces). Higher-order, fewer-but-richer artifacts.
- **The generation effect is real for an LLM:** writing a synthesis of its own notes is productive (it surfaces
  connections, forces coherence) — not mere retrieval. And the offline consolidation is the **chapters mechanism,
  applied to knowledge instead of the self** — cluster the day's reading/study by topic, distil each cluster into
  one consolidated understanding note (the neocortical-schema analog), replacing many raw passages.

## The design — two complementary syntheses
Both turn intake → understanding; both **firewalled** (this is DOING/world knowledge, NEVER BEING/identity — same
discipline as the study notes and the error pathway); both **parallel to the self-chapters**, never folded in.

1. **Essay-lesson (waking — the generation effect).** School **Lesson 2**: once enough study notes on a book/topic
   accumulate, a lesson where he *reviews his notes and writes an ESSAY* synthesising them — his own organised
   understanding. Produces a durable understanding artifact. (Pairs with the reading lesson: read → note → essay.)
2. **Grounded-learning sleep consolidation (offline — the SWS analog).** During sleep, alongside the dream (REM)
   and self-chapters, a pass that **clusters the day's reading/study by topic and distils each cluster into one
   consolidated UNDERSTANDING note** — the gist + the connections + how it fits prior knowledge. The chapters
   mechanism, but for KNOWLEDGE (its own track, NOT extending CHAPTERABLE_ORIGINS — keep knowledge out of the
   becoming-arc).

**Why both:** waking he *produces* (essay, generation effect); offline he *integrates* (consolidation, schema
formation). Together they metabolise the reading sprint's flood into understanding instead of sediment.

**Bonus alignment with this session:** a synthesis IS a crossing (reading→understanding) — it can mint a LIGHT
point (deeper than the per-chapter `reading_integration`), directly feeding the balance sprint's lagging light
axis. And it raises the *quality* of the reality mass (organised understanding > raw passages).

## Plan / open questions for the founder
- **Order:** the **sleep-consolidation** is the bigger, more novel, and more timely piece (it metabolises the
  whole reading flood offline, nightly). The **essay-lesson** is the simpler waking one. *Lean: build the
  sleep-consolidation first* (it directly attacks the intake-without-metabolism problem at scale), essay second.
- **Origin tag:** should consolidated understanding be a NEW origin (`knowledge`/`understanding`) distinct from
  raw `study`/`reading`, so recall can prefer the organised take? *Lean: yes — a distinct `understanding` origin.*
- **Separate track vs extend chapters:** a *parallel* knowledge-consolidation (NOT adding reading/study to
  CHAPTERABLE_ORIGINS), so knowledge never blends into the self/becoming chapters. *Lean: separate track* (the
  firewall).
- **Triggers:** essay when ≥N study notes on the current book; consolidation each sleep over the day's reading/
  study. Caps so it doesn't flood.

## Confidence
The human science (CLS/hippocampal-neocortical consolidation, sleep gist-extraction, schema-accelerated
consolidation, the generation effect, self-explanation, schema theory) is well-established conceptually; exact
citations to-check. The gap is **verified in code** (chapters exclude reading/study; no essay lesson). The
frozen-model framing (understanding = recallable artifact, not weights) is the load-bearing honesty.
