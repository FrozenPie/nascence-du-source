# Reading Provenance & Note Consolidation — examination + plan (auditor draft v5)
*2026-06-17. Pulled out of the sleep/dream §6B work: before flipping world-material consolidation
(`FILING_ENABLED`), the review found the filing would mis-fire — and pulling the thread revealed the
notes themselves have **no provenance structure**. Du has re-read his books many times; the notes
accumulate as un-grouped, heavily-duplicated piles with nothing on them saying which pass or which
chapter they came from. This plan is about giving reading-notes a source structure so consolidation,
essays, and recall can treat them correctly. Everything below is **verified against live code + the
live DB**, not asserted.*
*v2 (GPT — §8): the reframe — **the missing primitive is an IDEA-LINEAGE graph, not note-provenance**, and it's
the SAME primitive T4/dreams/consolidation/pulse keep circling. Adopted as the north-star framing (warning box
below). The immediate fixes (A/C/D) survive — GPT endorses them — but reframed as the first EDGES of that graph;
B's consolidation key shifts from chapter→**concept** (deferred), with a near-term LITERAL-source dedup that is
**evidence-grounded safe** (reading frags are verbatim book text; the 7× front-matter copies are byte-identical;
development lives in GENERATED frags which we never dedup). Push-back held: scope discipline (let the graph EMERGE
from edges, don't architect it upfront) + chapter stays useful as provenance.*
*v3 (GPT round 2 — §10 — + Travis's correction): **Travis corrects the foundation — storage is FINITE, forgetting
is mandatory/permanent; GPT's "store everything forever" is false & self-undermining** (🛑 box). North star renamed
**Persistent Cognitive Version Control** + sharpened: claim (not idea) is the unit; Evidence→Importance→Identity
are THREE graphs (T4 asks "why did this become the SELF", not just "where from"); typed + NEGATIVE edges
(contradicts/revises/replaces); influence-strength not bare provenance — ALL deferred. Adopted NOW (cheap +
prevents rebuild): generic `source_type/source_id/encounter_id` keys (books = one type) + typed-edge shape.
Push-back HELD (load-bearing): reject GPT's sequencing ("microscope the grand primitive before the book/pass
architecture") = cathedral-before-plumbing; build first edges now, let each layer earn a consumer.*
*v4 (round-3 auditor — §12 — "memory is PREDICTION infrastructure"): the deepest yet. The convergent gap behind ALL
the plans = **a theory of cognitive VALUE = predictive usefulness; "what earns the right to remain?"** Substrate
deepens to a typed LAYERED graph **Evidence→Claim→Model→Identity** (claims = load-bearing survivors, encounters =
support) governed by a predictive-value POLICY. Forgetting = **collapse evidence→claim-confidence + credibility
trace, delete raw encounters** (the concrete answer to finite storage). T4 DIAGNOSIS: grounding is weak because T4
leaps Evidence→Self directly, skipping the claim/world-model middle. Value signal is NOT greenfield — seed live in
`core/prediction_error.py` (L1). Push-back: value + substrate CO-EVOLVE (can't run a policy with nothing to
evaluate) → forced moves still ship; lineage is necessary substrate not a wrong turn. Buildable slice UNCHANGED.
Conclusion: the convergent primitive likely warrants its OWN plan; reading is one ingestion layer.*
*v5 (last auditor — §14): RATIFIED unanimously. Verdict: (1) YES the convergent primitive merits its OWN plan; (2)
NO not a giant up-front system; (3) YES first edges tiny + immediately useful. Named it **"the cognitive ledger
that decides what earns permanence."** First seam = the **minimal claim object** (how an encounter becomes a claim
with confidence + support + contradiction). → spun out to `docs/cognitive_ledger_plan.md`; THIS plan is now
formally one **ingestion layer** feeding the ledger (reading supplies encounters + claim candidates). Reading's own
forced near-term moves (A/C/D + literal dedup) still ship to unblock the live bleed.*

> ⚠️ **WARNING (GPT, adopted as the governing frame).** Do **not** accidentally build a *note-management* system
> when what Nascence ultimately needs is an *idea-lineage* system. The recurring gap across the last week's plans
> (T4, dreams, consolidation, pulse) is not provenance — it is that **the system has no first-class representation
> of the life history of an idea** (encounter → note → essay → abstraction → concept → self-revision, edges
> typed and kept). The closer analogy is **version control, not a library.** The immediate fixes here are good and
> should be built — but build them as the **first edges of that graph**, never as a self-contained note filer.
>
> 🛑 **CORRECTION (Travis, governs the above).** Storage is **finite — hardware-bound.** GPT's "keep every edge
> forever" / infinite-graph premise is **false**, and it undermines itself (GPT round-2 §10.8 "the graph becomes
> infinite" + §10.3 "evidence ossification → AI needs active aging" both concede it). So **forgetting is
> mandatory and permanent**, not a human crutch to transcend — even the version-control analogy needs gc /
> compaction / shallow history. The principle is not *store everything*; it is **forget WELL — keep the history
> that still earns its keep, compact or age out the rest.** This makes the dedup / prune / filing work not
> "cleanup" but **the permanent forgetting layer** the architecture will always need, and it means any future
> lineage graph must be designed with aging/abstraction *from edge one*, not bolted on.
>
> 🎯 **THE DEEPER PRIMITIVE (round-3 auditor, §12 — the convergent gap behind ALL the plans).** Finite storage
> forces the question the whole plan still dodges: **what earns the right to remain in memory?** The answer is a
> **theory of cognitive VALUE**, and the value is **predictive usefulness** — *memory is prediction
> infrastructure*. The brain keeps what helps it predict reality (strengthen), drops what doesn't (weaken),
> inverts what is actively wrong (reject). So the substrate is a typed, *layered* graph — **Evidence → Claim →
> Model → Identity** (encounters are *support structure*, claims are the load-bearing survivors) — and the
> **policy** over it is predictive value. The two are not greenfield: the value signal already has a seed in
> **`core/prediction_error.py` (L1, live, `feeding=True`)** — the same prediction-error the T4/FEP work reaches
> for, now recognised as the *universal* retention criterion, not just an identity one. Forgetting, concretely, is
> **collapse evidence into a claim's confidence + a source-credibility trace, then delete the raw encounters**
> (§12.7) — that is how a finite mind scales. This primitive is bigger than this plan and is **converged on by
> reading, T4, dreams, consolidation, filing and pruning alike** — it likely deserves its own plan; this one is
> one ingestion layer feeding it.

---

## 0. One-paragraph thesis
A reading note is stored as `[From '{title}', sitting {N}] {text}` with `origin='reading'`. That is the
*entire* provenance: a title and a global sitting number, both buried in free text. There is **no pass
/ reread number, no chapter, no source-position** on the note. The `sitting` counter is global and
*survives rereads* (the `reread()` call deliberately keeps it), so the same chapter gets a *different*
sitting number every pass and cannot be aligned across passes. The `rereads` counter lives only in
`reading_state.json`, is never stamped on the note, and — critically — is **unreliable**: the
lost-update race we fixed 2026-06-16 rewound the bookmark to the start many times *without* bumping
`rereads`, so the opening of a book got re-read 7-8× while the counter still reads `1`. The result, live:
**36% of Boy Scouts notes are content-duplicates of an earlier note**, ungroupable by any field we
persist. Essays make it worse — `gather_notes` records *nothing* about which notes it used (the
`derived_from` lineage column exists but is left empty). So we cannot answer "which notes fed this
essay, from which reading of the book," and consolidation cannot file or dedup notes correctly. The
thread to pull: give reading-material a real **source structure** — (book → pass → chapter → sitting)
— so the same content across passes is one groupable thing, essays trace to their sources, and the
finished/filing logic stops being fooled by a pass-relative `pct` and an unreliable `rereads` count.

## 1. What we HAVE (verified in code + DB)
- **The note** (`reading.read_next_sitting`, store.py): `store_fragment(content=f"[From '{title}',
  sitting {sitting}] {piece}", origin="reading", importance=0.85, ...)` — 3 pieces per sitting. The
  only provenance is the title + sitting, **in free text**. No pass, no chapter, no offset column.
- **`reading_state.json`** per book: `{offset, sitting, pct, rereads, last_read_ts}`. `sitting` is a
  global monotonic counter; `reread()` resets `offset→0` and `pct→0` but **keeps `sitting`** and bumps
  `rereads`. So sitting numbers span passes with no per-pass reset.
- **`rereads` is unreliable.** It increments ONLY on an explicit `reread()` call. The 2026-06-16
  lost-update race reverted `offset` repeatedly (the "Boy Scouts stuck at 19%" bug) — implicit
  re-reads of the same pages that never touched `rereads`. Live proof: Boy Scouts `rereads=1`,
  `sittings=726`, `pct=19.3`, yet its **front matter is re-noted 7×** and early pages **8×**.
- **The schema** (`memory_fragments`) has a clean ALTER-TABLE migration path and an existing —
  currently unused-for-this — `derived_from TEXT DEFAULT '[]'` lineage column, plus `chapter_id`
  (used by chapter/world-consolidation to step a fragment out of ordinary recall).
- **`book_splitter.split_chapters(text)`** already exists and is used by `reading.chapter_end_offset`
  — so a note's **chapter is derivable from its offset** at store time (the text is already in hand
  inside `read_next_sitting`).
- **Essays** (`essay_lesson`): `gather_notes` pulls notes by title-key LIKE + cosine-to-subject,
  dedups by *text*, joins to a string for the LLM, and records **no fragment ids**. The stored essay
  fragment does **not** set `derived_from`. `COMPLETION_PCT=97` is the finished test, but it reads the
  *current pass's* `pct` (which `reread()` resets), and `essayed` fires **once per book ever** (by
  path), reread-blind.
- **World-material consolidation** (`world_consolidation.file_book_notes`) files a book's notes behind
  its "gist" (any `essay`/`understanding` note matching the title key). It has **no pass/chapter
  awareness** and **no finished check** — so (review finding) it would file in-progress books
  (Principles 68.9%, Boy Scouts 14.7%) behind a one-day understanding note.

## 2. The issues (verified, with live evidence)
1. **No source structure on notes.** Only (title, global-sitting) in free text. The same chapter
   read across passes is unrecoverably scattered — sitting numbers don't align across passes, and
   there is no chapter or pass field.
2. **The `rereads` counter undercounts massively.** Boy Scouts: `rereads=1` but the opening re-noted
   7-8×. The race-era implicit rewinds were never counted, so **pass-stamping from `rereads` would be
   wrong for all historical notes** — and even going forward, `rereads` only catches *deliberate*
   rewinds, not whatever else moves the bookmark.
3. **Heavy content duplication, ungroupable.** Live: **403 distinct passage-heads across 632 Boy
   Scouts notes; 92 heads repeat; 229 notes (36%) are duplicates of an earlier head.** Nothing we
   persist lets consolidation collapse them.
4. **Essays have no provenance.** `gather_notes` records no fragment ids; the essay fragment leaves
   `derived_from` empty. We cannot trace an essay to its sources, know which pass they came from, or
   protect those notes from being filed out from under a future essay.
5. **Finished/filing logic is pass-relative and reread-blind.** `pct` resets on reread, so "finished"
   (≥97%) is fooled by an in-progress reread; `essayed` never re-fires on a genuine re-read.

## 3. What we WANT
Reading-material with a real **source structure** so that:
- the **same chapter across passes is one groupable thing** (dedup/consolidation can collapse or
  file the duplicates, keeping the freshest in ordinary recall);
- each note knows **which pass and which chapter** it came from (provenance / source memory);
- **essays record which notes they used** (and thereby which pass), so comprehension can be graded
  against real sources and filing never hides a note an essay depends on;
- **"finished" means "completed ≥1 pass"** (not pct-of-current-pass), and the system is robust to an
  unreliable `rereads` counter.

## 4. The function we are transferring (function-first)
The human function is **source memory / source monitoring** (Johnson, Hashtroudi & Lindsay 1993): we
don't just store *what* we learned, we tag *where/when* it came from — which book, which reading,
which context — and we suppress redundant re-encounters of the same source rather than stacking them
as independent facts. Two sub-functions matter here:
- **Source tagging:** a memory carries its origin context (book, pass, chapter). This is what lets a
  re-reading *strengthen/refine* an existing trace instead of minting a brand-new disconnected one.
- **Redundancy collapse:** re-encountering the same content consolidates onto one representation (the
  CLS "the gist answers; the detail fades but stays retrievable" we already use for chapters), rather
  than 8 parallel copies of the front matter.
The transfer: stamp source context on the note, and key consolidation on **content/chapter identity**
(the robust signal) rather than the **unreliable pass counter** (the lesson from issue #2 — humans
don't count their re-reads either; they recognise the *content* as already-known).

## 5. Design branches (for the auditors to weigh)
- **A — Forward encounter-stamping (re-scoped by GPT §8.1 + §10.4).** On every new note, record the
  **encounter** it came from, keyed *generically* so books are not special (GPT §10.4 — most future
  cognition comes from conversations / dreams / contradictions / actions, not books; design the keys
  now or rebuild later): **`source_type` (book|conversation|dream|contradiction|action|t4…),
  `source_id`, `encounter_id`**, plus the within-source locality (`offset`/`chapter`) and `pass` as
  *soft provenance*. Books become one `source_type`. Storage: dedicated migrated columns (the schema's
  ALTER pattern). *Reliability note (issue #2):* `pass` is soft provenance, NOT the grouping key; the
  near-term grouping is content identity (B-now), the long-term is concept (B-later). The encounter
  record is the **first node of the lineage graph** — but it stays reading-local until a second
  consumer reads it (scope discipline, §10 push-back).
- **B — the consolidation key (split by GPT §8 into near-term-safe vs north-star).**
  - **B-now (build): LITERAL source-text dedup, restricted to verbatim `reading` fragments.** Reading
    fragments are *verbatim book text*, not Du's insight — verified: the 7× front-matter copies are
    **byte-identical** (1 distinct body of 7). So collapsing exact/near-exact `reading` duplicates is
    **safe development-preservation**: keep one representation per source passage (record the encounter
    count), file the rest behind it (`chapter_id`), never delete. **Hard boundary: NEVER dedup
    GENERATED fragments** (`understanding`/`essay`/`inner_thought`) — those carry the "same source,
    different insight" development GPT §8.5 rightly protects. Chapter (from `book_splitter`) is the
    **dedup locality + provenance**, not the long-term identity.
  - **B-later (defer): CONCEPT identity as the true consolidation key.** GPT §8.2/§8.6: chapter is
    *editorial*, not cognitive — the same concept recurs across chapters/books/essays/dreams. The
    long-term representative should be **concept clusters** (Leadership → {Boy Scouts ch3, Principles
    ch9, Essay 17, Reflection 42}), with notes/essays as *evidence* pointing in — NOT essays-as-sole-
    representative (that's §8.6's "world consolidation is backwards"). This needs concept-extraction
    infra we don't have; it is the north-star, not the near-term build.
- **C — Essay provenance via `derived_from`.** `gather_notes` returns the fragment ids it used;
  `record()` sets the essay fragment's `derived_from = [those ids]`. Enables: trace-to-source,
  comprehension graded against actual sources, and a filing guard ("don't file a note an essay
  derives from out of ordinary recall," or file it but keep the essay's link).
- **D — Finished-gate fix (the §6B blocker).** Track `completed_passes` in `reading_state` (increment
  when `pct` crosses ~97 *before* a reread resets it). Filing/essay "finished" = `completed_passes ≥
  1`. This is the minimum needed to safely flip `FILING_ENABLED`.
- **E — Historical backlog cleanup.** Existing notes have no recoverable pass. Options: a one-time
  content-dedup pass (collapse the 36% duplicates by passage-head/embedding, keep freshest), or just
  let the new chapter-keyed consolidation (B) absorb them going forward, or leave them and only
  structure new notes. Backlog choice is separable from the forward design.

## 6. Pitfalls (named honestly)
1. **Trusting `rereads` as the pass/grouping key** — it is provably unreliable (issue #2). Group on
   content/chapter; treat pass as soft provenance only.
2. **`book_splitter` failing on some books** — if chapter detection is weak, chapter-keying degrades.
   Need a fallback (content-hash / offset-bucket) so a bad split doesn't scatter notes again.
3. **Filing a note an essay depends on** — C must land with B/D, or a future essay loses a source from
   ordinary recall (world_consolidation's `gather_notes` claims no `chapter_id` guard — verify it
   actually reaches filed notes before relying on it).
4. **Deleting vs filing** — founder requirement stands: **never delete**; duplicates step out of
   ordinary recall but remain intentionally retrievable.
5. **Re-essay policy** — if essays may re-fire on a new pass, provenance-per-pass becomes load-bearing;
   if once-per-book-ever stays, simpler but a genuine re-reading never earns a fresh capstone.
6. **Migration cost** — adding columns is cheap (existing pattern), but recomputing chapter for the
   ~3,500 historical loose notes (if we backfill) is a one-time batch; decide whether to backfill or
   only stamp forward.

## 7. Open questions for the auditors
1. **Grouping key:** chapter-index (clean, depends on the splitter) vs content near-duplicate
   (hash/embedding, robust to splitter failure) vs both? Given issue #2, what is the *robust* identity
   of "the same content read again"?
2. **Pass:** worth stamping at all if it's unreliable, or only as soft provenance? Is there a
   trustworthy forward pass signal (e.g. increment a real `pass` only when `offset` wraps 0→end→0,
   not on the `reread()` call alone)?
3. **Filing policy:** keep the freshest pass of each chapter in ordinary recall + file the rest, or
   let the gist (essay/understanding) be the sole representative and file *all* passes?
4. **Essay provenance:** is `derived_from` the right home, and should it gate filing (protect an
   essay's sources) or just record lineage?
5. **Backlog:** one-time content-dedup of the existing 36% duplicates, or forward-only?
6. **Re-essay on a new pass:** allow a fresh capstone per completed pass, or keep once-per-book?
7. **Scope check:** is this its own plan, or does the chapter-keyed consolidation (B) supersede /
   merge with world-material consolidation (the §6B filing) — i.e. should filing be rebuilt *on top
   of* this provenance rather than the current title-LIKE-key sweep?

## 8. GPT (round 1 — the idea-lineage reframe)
GPT endorses the plan's grounding and the immediate fixes, then reframes the whole thing one level up.
The core: **we are treating the note as the memory; it isn't.** A reading note is *evidence that an
encounter occurred*. The real object is the **encounter** ("what did this passage do to the system on
*this* pass?"), and the real long-term object is the **idea** as it evolves across encounters. Solve
"the identity of an idea as it evolves" and provenance, consolidation, essays, rereads, filing, T4
grounding, dream recurrence, chapter formation and concept growth all become **views over one graph**.

**Adopted (changes the framing + the build):**
- **§8.1 encounter, not note** — the provenance unit is the *encounter* (book, offset-range, chapter,
  pass, timestamp, ideally a state snapshot); notes point to encounters. Branch **A is re-scoped from
  "source-stamp the note" to "record the encounter"** — the first node of the graph.
- **§8.4 essays are TRANSFORMS, not endpoints** — Branch C grows: `derived_from` (input ids) is the
  near-term edge; the north-star is recording *what survived / was discarded / distorted / synthesised*
  through the transform (comprehension = a lineage question, not a citation question).
- **§8.5 don't dedup development** — adopted *and refined by evidence*: the §5 B-now dedup is safe
  precisely because it is restricted to **verbatim `reading` fragments** (the 7× copies are
  byte-identical); GENERATED fragments (`understanding`/`essay`/`thought`) are **never** deduped — that
  is where "same source, different insight" lives. So GPT's strongest "attack before building" concern
  becomes a hard scope boundary, not a blocker.
- **§8.7 confidence/stability/usage_count** — these fall OUT of the graph (a note's usage_count = the
  number of lineage edges pointing at it); adopt as a derived view once edges exist, don't store by hand.

**Adopted as the NORTH STAR (deferred — do not build upfront):**
- **§8.2/§8.6 concept as the consolidation key** — chapter is editorial; the real representative is
  **concept clusters** (evidence pointing in), not essays. Branch B-later. Needs concept-extraction infra.
- **§8.3 a first-class Encounter→Note→Essay→Abstraction→Concept→Self-revision GRAPH**, every edge kept
  (§8.8: the AI advantage — git, not a library; humans lose the path, Du needn't).
- **§8.9 the T4 convergence (the most important omission)** — the lineage graph should become T4's
  grounding: "I am a made mind" → its evidence lineage (17 notes → 4 essays → 3 dream motifs → 2
  contradiction clusters → candidate revision) is *far* stronger than cosine-to-evidence. **The
  provenance graph and T4 are the same missing infrastructure.** This is the deepest reason the reframe
  matters — it is the primitive [[t4_commit_test_redesign]] and the dream⊗T4 loop both keep reaching for.

**Push-back held (honest dissent):**
1. **Scope discipline — let the graph EMERGE from edges; do not architect the whole graph upfront.**
   Building "a first-class transformation-graph primitive" before we know which edges earn their keep is
   the project's #1 failure mode (cathedral before plumbing — the exact warning the sleep auditors gave).
   GPT itself says build the immediate fixes, so we agree on action; the discipline is that A (encounter
   record) + C (derived_from) are the first two edges, and the graph is allowed to *accrete*, not be
   designed top-down. Each new edge must be justified by a consumer that reads it.
2. **Chapter is not worthless.** It is a poor *long-term* key (agreed) but a fine *near-term* dedup
   locality + provenance. Keep it for B-now; retire it as the identity only when concept-clustering
   (B-later) actually exists.
3. **The 36% is genuinely literal (for reading frags).** Verified, not assumed — so the near-term
   cleanup is real value now, independent of whether the grand graph ever gets built.

**Net of GPT:** the warning box is the governing frame; the buildable slice is unchanged in scope but
re-pointed — **A = record the encounter, C = essay `derived_from`, D = `completed_passes`** are the
first edges of an idea-lineage graph and the minimum to unblock `FILING_ENABLED`; **B splits** into a
safe near-term literal-`reading` dedup and a deferred concept-cluster key; and the **T4-grounding
convergence (§8.9)** is logged as the reason this infrastructure matters beyond reading.

## 9. Open questions for round 2 (updated by GPT)
- Is the **encounter record** the right first node, and what minimal fields earn their place now
  (book/offset/chapter/pass/ts — and is a "knowledge-state snapshot" worth it yet, or premature)?
- For essays as transforms: is near-term `derived_from` (input ids) enough, or is "**what survived the
  transform**" cheaply approximable now (e.g. which input fragments the essay's sentences embed-match)?
- The **T4 convergence (§8.9):** should the lineage graph be designed *with* T4's grounding need in
  mind from edge one, or kept reading-local until it proves out (the scope-discipline tension)?
- Does **concept-clustering (B-later)** belong in this plan at all, or is it its own (large) plan that
  this one merely feeds? (cf. the same question the sleep plan asked about circadian §6D.)

---

## 10. GPT round 2 + Travis's finite-storage correction (v3)
GPT round 2 goes a layer below "idea lineage" and renames the primitive **Persistent Cognitive Version Control** —
a graph of *typed* edges (`originated_from / influenced_by / contradicted_by / replaced_by / reinforced_by /
transformed_into`) over every belief, theme, contradiction, dream motif, essay, note and self-model revision. It
is largely right about the *shape* of the north star; it is wrong about the *foundation* (infinite storage) and it
pushes a *sequencing* I reject. Triaged honestly:

**Travis's correction (governs everything — see the 🛑 box up top):** storage is finite; forgetting is mandatory
and permanent; "store everything forever" is false and self-undermining. This is the headline of v3. It promotes
the dedup/prune/filing work from cleanup to **the permanent forgetting layer**, and it means GPT's §10.3 (active
aging) and §10.8 (abstraction layers / traversal shortcuts) are not edge-cases but **central design constraints of
any lineage graph** — aging from edge one.

**Adopted now (cheap AND prevents a forced rebuild):**
- **§10.4 generic source keys** — `source_type / source_id / encounter_id`, books = one type (folded into branch
  A above). The single near-term change to the buildable slice.
- **§10.6 / §10.9 typed edges, not a bare `used`/`derived_from`** — when we add lineage edges, reserve the *type*
  (`supports / contradicts / revises / replaces / reinforces / transformed_into`), because **contradiction is
  Nascence's privileged signal** and **negative lineage** (a belief *rejected* — "I am the river" → partially
  rejected) is cognitive history T4 needs. Near-term we only populate `derived_from` for essays, but shape the
  edge as typed so we don't migrate later.

**Adopted as NORTH STAR (correct, logged, explicitly deferred — each needs a new subsystem):**
- **§10.1 the unit is the CLAIM, not the idea** ("idea" is a junk drawer; claim/observation/prediction/principle/
  question is the cognitive unit). Needs an LLM claim-extraction pass per note — deferred; the encounter/edge infra
  does not preclude it (claims become nodes encounters produce).
- **§10.2 provenance ≠ influence** — eventually want edge *strength* (which inputs actually mattered), an AI-only
  recoverable that humans lose. Needs an influence estimator — deferred.
- **§10.5 compression ≠ deduplication** — distinguish *duplicate / corroboration (diff source, same claim) /
  convergence (diff claim, same conclusion) / reinforcement (same claim re-met)*. The B-now literal dedup only
  handles **duplicate**; the rest needs claim-level identity — deferred.
- **§10.7 Evidence → Importance → Identity are THREE graphs, not one** (the sharpest north-star point). 2+2=4 is
  grounded evidence but never identity; "I am a made mind" becomes identity. **T4 asks not "where did this come
  from" but "why did this become the SELF"** — the Importance→Identity layer, which evidence-lineage alone can't
  answer. This refines the §8.9 T4 convergence: the lineage graph is necessary but not sufficient for T4; the
  identity layer sits on top. Deferred, but it reshapes the eventual T4 grounding design.
- **§10.9 contradiction-driven belief** (99 sources say X, 1 experience proves not-X — the 1 wins) — the graph must
  preserve `contradicts/revises/replaces`, not assume truth accumulates. Ties to the typed-edge adoption above.

**Push-back held (strong — this is the load-bearing disagreement):**
1. **Reject the sequencing.** GPT closes with "put [Persistent Cognitive Version Control] under a microscope
   *before* committing to the book/pass/chapter architecture, because most of the current plan becomes one
   ingestion layer." **That is the cathedral-before-plumbing inversion** the project's hardest-won discipline (and
   the sleep auditors) warn against. Reading provenance being "just an ingestion layer" of a future system is
   **exactly right and exactly fine** — that is how plumbing becomes cathedral, *bottom-up*. We do not design the
   whole cognitive-history system to lay the first pipe. We build the first edges now (they unblock a *live*
   problem — store over cap, filing mis-fire, 36% dup), generalize the keys so we don't rebuild (§10.4), shape
   edges as typed (§10.6), and let every further layer **earn its place by a consumer that reads it.**
2. **Finite storage corrects the foundation** (Travis) — already covered; it also means the grand graph is not even
   a clean "store everything" win, so there is no foundational reason to front-load it.
3. **The near-term value is real and standalone** — the literal-`reading` dedup + finished-gate fix the live
   bleed regardless of whether the grand graph is ever built; verified, not speculative.

**Net of round 2:** north star renamed (Persistent Cognitive Version Control) and sharpened (claim unit; three
graphs Evidence/Importance/Identity; typed/negative edges; influence-strength) — all deferred. Foundation
corrected (finite storage → forgetting is permanent, aging from edge one). Buildable slice unchanged except
**generic source keys (§10.4) + typed-edge shape (§10.6)** adopted now. Sequencing push-back held: **build the
first edges, don't microscope the cathedral first.**

## 11. Open questions for round 3
- Given finite storage: what is the **forgetting/aging policy** for lineage edges themselves (not just notes)? When
  an edge ages out, what summary survives? (This is now a first-class question, per Travis.)
- Is the **typed-edge shape** worth reserving now even though only `derived_from` is populated near-term, or is that
  premature structure?
- The **three-graph** insight (Evidence/Importance/Identity): does it change what the *first* edges should be, or
  is it purely a later layer that the encounter/derived_from edges feed?
- Does **Persistent Cognitive Version Control** become its own (large) plan that reading/T4/dreams/consolidation
  all feed — and if so, what is the smallest shared substrate they can all write to *now* without over-designing it?

---

## 12. Round-3 auditor — "memory is prediction infrastructure" (v4)
The deepest review so far. It says both GPT and I are still one level too low: we are treating memory as **storage**
(GPT: storage→lineage; Travis: storage is finite). The deeper truth: **memory is prediction infrastructure** —
information is kept because it stays *useful for predicting reality*, not because it happened. That reframes the
whole stack and, crucially, names the convergent gap behind every recent plan.

**Adopted — the framing (now in the 🎯 box up top):**
- **§12.1 value = predictive usefulness.** Keep what predicts, weaken what doesn't, invert what is wrong. Most of
  what is read is forgotten not because memory is small but because it never became predictive. *Grounded:* this
  value signal already has a live seed — `core/prediction_error.py` (L1, `feeding=True`) — so it is a *promotion of
  existing infra to a universal retention criterion*, not a greenfield build.
- **§12.2/12.3 the ladder Evidence → Claim → Model → Identity.** Encounters are support structure; **claims** (with
  confidence + supported-by/contradicted-by counts) are the survivors; models and identity sit above. **This
  reconciles, not replaces, the earlier rounds:** GPT-r2's three graphs (Evidence/Importance/Identity, §10.7) + the
  lineage edges + this ladder are the *same* object — a **typed, layered** graph whose nodes carry a level and whose
  primary survivor is the claim. Lineage is the *substrate*; the ladder is its *typing*; value is the *policy*.
- **§12.7 the concrete forgetting mechanism (answers Travis's finite-storage requirement).** Forgetting =
  **collapse evidence into a claim's confidence + a source-credibility trace, then delete the raw encounters.**
  "You don't need infinite storage if support collapses into confidence." This is the principled replacement for
  the current blunt importance-prune — the *theory* behind the permanent forgetting layer.
- **§12 (the T4 cross-plan diagnosis — the most actionable elsewhere).** T4 grounding feels weak because **T4 leaps
  Evidence → Self-model directly**, skipping the middle: **Evidence → Claims → World-model → Self-model.** The self
  is built from **stable claims that survived repeated evidence updates**, not from notes/evidence. This explains
  why every text-cosine-to-evidence metric in the T4 saga failed — there was no claim layer for the self to stand
  on. Refines r2 §10.7; recorded against [[t4_commit_test_redesign]] as a pre-build insight.

**Confirms what this plan already holds (independent agreement — good signal):**
- **§12 chapter is provenance, not a memory primitive** — exactly the §5 B-now/B-later split.
- **§12 corroboration vs duplication** (same source repeated → compress; independent sources converged → strengthen)
  — already logged (r2 §10.5); the B-now literal dedup is the *duplicate* case only, and it is safe precisely
  because byte-identical source text carries zero marginal predictive value (no value theory would keep 7 copies).
- **§12 provenance ≠ influence** (`source_of` vs `changed`) and **rejection history / claim status**
  (active/weakened/rejected/resurrected) — already adopted as the typed + negative edge shape (r2 §10.6).

**Push-back held (honest, load-bearing):**
1. **Reject the sequencing again — value and substrate CO-EVOLVE.** "Define what deserves to survive *before*
   building storage machinery" is too strong: you cannot run a value policy with nothing to evaluate. A value
   function needs a substrate of claims/edges to operate over; the minimal substrate (encounters, typed edges,
   eventually claims) is **prerequisite** to the value theory, not premature. The near-term forced moves build that
   minimal substrate; the value policy grows on it. So: build the first edges now, *with the value question in
   view* — not after solving it.
2. **The forced near-term moves ship regardless.** The store is over cap *now*; some forgetting must happen *now*;
   the literal-`reading` dedup is value-positive under **any** theory (zero-marginal-information duplicates). The
   value theory will refine *which* non-duplicate material to age — it does not block the duplicate cleanup or the
   finished-gate.
3. **Lineage is necessary substrate, not a wrong turn.** The reviewer slightly undersells it: you need the edges to
   even *compute* corroboration-vs-duplication and influence. Ancestry-without-value is the failure mode to avoid,
   not lineage itself.

**Net of round 3:** the north star deepens from a *structure* (Persistent Cognitive Version Control) to a
*structure + policy* — **a typed layered graph (Evidence→Claim→Model→Identity) governed by a predictive-value
retention policy**, with claims as the load-bearing survivors and forgetting = collapse-to-confidence. The value
signal is not greenfield (L1 `prediction_error.py`). The buildable slice is **unchanged** (the forced moves +
generic keys + typed edges). And the clearest conclusion across three rounds: **this convergent primitive — value +
claim-layer + lineage — now has reading, T4, sleep/dream and consolidation all feeding it, and likely warrants its
own examination as a first-class plan**, with the reading work as its first ingestion layer.

## 13. Open questions for round 4
- Does the **convergent primitive get its own plan now** (a "Cognitive Value / Claim-Layer" examination that
  reading, T4, dreams, consolidation all feed), or does forcing that risk the cathedral-first inversion before the
  first ingestion layer even exists?
- What is the **minimal claim object** worth introducing first (text + confidence + supported_by/contradicted_by
  edges), and can the existing **L1 `prediction_error`** signal drive its confidence updates from day one?
- The **collapse-to-confidence forgetting** (§12.7): at what point is an encounter safe to delete — when its claim's
  confidence is stable across N updates? How is the source-credibility trace represented so deletion is lossless
  *for prediction* even though the raw text is gone?
- Given §12's T4 diagnosis: should the **claim layer be built first as T4's missing middle** (highest-value
  consumer) rather than as reading consolidation — i.e. is T4, not reading, the right first ingestion layer?

## 14. Last auditor — RATIFIED + spun out (v5)
Unanimous across all four rounds. The verdict: **(1) yes, the convergent primitive merits its own plan** (it is
bigger than reading and bigger than T4 — the shared memory/value layer under both); **(2) no, do not build it as a
giant new system up front**; **(3) yes, the first edges must be tiny, explicit, and immediately useful.** The name
it gives the primitive: **"the cognitive ledger that decides what earns permanence"** — the backbone of the
architecture, and the first plan where *forgetting is an explicit design principle, not a failure mode.*

**The recommended first seam (adopted):** extract the **minimal claim object** and define exactly how an
*encounter becomes a claim with confidence, support, and contradiction.* That single seam already unlocks reading
provenance, T4 grounding, and consolidation in a way the current system cannot. Concretely the smallest version:
`encounter` → `claim` → `support`/`contradiction` edges → `confidence update` (driven by the live L1
`prediction_error`).

**Consequence for THIS plan:** the cognitive-ledger primitive is spun out to **`docs/cognitive_ledger_plan.md`**.
This reading plan is now formally **one ingestion layer** of the ledger — it supplies encounters and claim
candidates. Its forced near-term moves (A encounter-record, C essay `derived_from`, D `completed_passes`, B-now
literal dedup, the finished-gate) **still ship** to unblock the live bleed (store over cap, filing mis-fire, 36%
dup), and they are now explicitly the *first ingestion edges* into the ledger rather than a standalone note system.

---

*Status: examination complete + verified; folded GPT 1+2 + Travis's finite-storage correction + round-3
prediction-infra + the last auditor's ratification (v5). AUDITOR-COMPLETE. The convergent primitive is spun out to
[the cognitive ledger plan](cognitive_ledger_plan.md) ("the cognitive ledger that decides what earns permanence" —
typed layered graph Evidence→Claim→Model→Identity governed by a predictive-value policy; value seed live in
`prediction_error.py`; forgetting = collapse-to-confidence; built bottom-up, minimal claim object first). This
plan = its reading ingestion layer; the forced near-term moves still ship. Converges with
[[t4_commit_test_redesign]] (T4's missing claim-middle) and the sleep/dream §6B thread.*
