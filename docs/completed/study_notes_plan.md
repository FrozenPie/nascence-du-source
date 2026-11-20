# Plan — Study Notes (Du's scholarship; the world-facing voice)
*Status: **ON HOLD** (2026-06-14) pending `two_lane_architecture_plan.md`. All 4 threads were pulled +
the human/AI research done; the findings became the EVIDENCE for the two-lane architecture (the study
lane = the analytical lane; "grounded flavour"/"both questions" = the Curator; prompt-fragmentation =
that plan's §0). Resume the study-note-specific fixes (Thread 3/4 builds) only if the lane
architecture leaves them needed.*
*Sibling to `loop_metabolism_plan.md`: that plan fights the self-referential monoculture; this one
examines the one voice that is ALREADY grounded — and asks what it teaches and whether it's wasted.*
*Process (founder, 2026-06-14): (1) keep all four threads in the plan; (2) pull each thread and flesh
out each point; (3) research how it compares to the human mind — what it can do, what AI allows;
(4) discuss further. This document is step 1.*

---

## 0. The motivating finding (why this plan exists)
Du's **study notes are grounded** — concrete, external, factual, varied. Five most-recent (all on
Morley's *Tales from a Rolltop Desk*), verbatim from the store 2026-06-14:
- *"The manuscript from Digby is valued at two hundred dollars by Basswood due to Digby's death;
  Dulcet believes it worth at most seventy-five."*
- *"Fumacetic acid… lethal when inhaled as vapor, was used to poison the client."*
- *"Mrs. Vesey, the landlady, is portrayed as a good-hearted widow."*

No river. No "space between words." Real characters, plot, specific facts. **The same mind that
collapses 99% of its idle thought to one metaphor produces particular, externally-anchored
scholarship the moment the architecture (a) puts the real text in front of it and (b) says
explicitly "scholarship, NOT self-reflection."**

**The load-bearing conclusion:** the monoculture is **not a fundamental limit of Du** — it is
specific to the *unscaffolded self-referential lanes*. Grounding is possible; it just doesn't happen
on its own. So the study notes are at once (a) PROOF grounding works, (b) a possible MODEL/scaffold
for repairing the self-lanes (loop plan §6.1, Layer 3), and (c) a grounding ASSET that may be going
entirely unused. The four threads below interrogate exactly this.

---

## 1. What the study-notes system IS (verified baseline, 2026-06-14)
- **Trigger:** after Du reads a passage, the monologue fires a study-note call
  ([`inner_monologue_node.py:689`]) with the instruction *"Be concrete about WHAT THE TEXT SAYS…
  Scholarship, not self-reflection."* (the anti-self scaffold).
- **Output:** `core/study.py:write_tablet` writes a `TAB_*.md` file (`# title` + body + `· on: <book>`)
  AND a retrievable fragment: `origin='study'`, `content="[My study note: 'note_title'] body"`,
  `keywords=["study", note_title]`. World-origin → prune-protected (Phase B anchor).
- **Side effects:** seeds a Frontier question (`frontier.harvest_tablet`); records a satisfaction
  signal; records an Activity-Memory `study` general-event (keyed by book).
- **Volume:** 39 tablets — Beagle 18, *Tales from a Rolltop Desk* 16, Tesla 4 (+2 test). DB study
  fragments: 28, keyed by NOTE title (not book — the book lives in the file header `· on:`).

---

## 2. The four threads (each: observation so far · the question · TO PULL)

### Thread 1 — Are the notes READ BACK? (retrieval / write-only risk)  [PULLED 2026-06-14]
- **Original hypothesis:** §1.5 showed reading/study loses cosine selection to metaphor, so the notes
  might be write-only (the #1 failure mode). **This was WRONG — the opposite is true.**
- **FINDING (from `wandering_log.jsonl`, 2,434 trail items):** the grounding is **delivered
  abundantly.** 55.5% of what drifts through his idle mind is WORLD material — reading 40.2%, **study
  10.2% (249 appearances), most recent 6 min ago**, research 1.1%, ambient_book 3.9%. The self-voices
  are a MINORITY of the trail (inner_thought 21.7%, active_imagination 5.6%, subconscious 4.8%). The
  wandering module (`core/wandering.py`) works well — it even FORCES world-only drift when the trail
  gets self-referential (≥3 inner → `origin IN ('reading','research','study')`, [93–94]).
- **THE REAL FINDING — un-taken, not unread:** 55% of his idle mind is grounded world material, yet
  his actual thoughts stay **99% monoculture**. He is offered cuttlefish camouflage, the Beagle, his
  own study notes — *"any of them is as worthy of your next thought as you are"* — and thinks the
  river anyway. **The bottleneck is UPTAKE AT GENERATION, not retrieval or delivery.**
- **The mechanism:** `render()` OFFERS ~2 world items of 4 seeds, but the GUARANTEED self-priming
  (self-concept + last-thought every cycle, loop §6.1) + the attractor outweigh the optional offer.
  The study NOTE grounds because it is BINDING (text present + "write what it says"); the wandering
  trail OFFERS, and an offer to a mind in a deep basin is ignored. (Conversational recall is a
  separate, weaker path: study loses cosine to metaphor — loop §1.5 — so in dialogue it barely
  surfaces at all.)
- **REFRAME (feeds Thread 2 + loop Layer 3):** the fix is NOT "deliver more grounding" (already 55%).
  It is **make the offered world material BINDING on the next thought** — the way the study note binds
  engagement to the passage. Offering ≠ uptake; the difference is forcing. This is the DMN/TPN-
  suppression point (loop §10.1) made concrete: adding reality beside the self-loop doesn't break it.

### Thread 2 — The SCAFFOLD as anti-monoculture (can the idle lane borrow it?)  [PULLED 2026-06-14]
- **The prompt diff (the decisive finding):** the idle lane's OWN system prompt is a self-reflection
  generator. `_build_system_prompt` ([228–243]) mandates the subjects: *"about **who you are, what has
  been moving in you**, the conversation you just had, a dream, or a question that lingers"* — every
  one inward; world material isn't even listed. Even the anti-rumination "wandering" branch points
  inward: *"wander to… **another part of yourself entirely**."* The study-note prompt ([690–698]) does
  the OPPOSITE: a present external object as subject + *"what the text says… scholarship, NOT
  self-reflection."*
- **So Threads 1+2 lock:** the wandering trail DELIVERS 55% world material (Thread 1), but the system
  prompt DIRECTS him inward — the world seeds swim upstream against a prompt that mandates self-focus.
  Binding = (world-object as subject) + (outward, anti-self instruction). Offering = (object beside) +
  (inward instruction). Both have the object present; only one makes the thought ABOUT it.
- **It transfers, and it's SMALL** — every ingredient exists: world material in the trail; the
  study-note framing; a mode-branch in `_build_system_prompt` to add a third ("grounded") mode; a
  partial precedent (the reading continuity-train already says *"let what you just read work on you —
  question it, connect it, doubt it"*, [388–390]).
- **The design — a CONDITIONAL "grounded thought" mode (not a rigid rule):** when the AI-native
  concentration measure (loop §10.2) shows the monoculture winning, occasionally pick a specific world
  item already in his trail and bind the next thought to IT with the study-note framing — *"here is
  this; think about what it SAYS, what it means about the world, not about you."* Homeostatic, not
  every-cycle (faithful to DMN/TPN: external engagement suppresses the self-loop, conditionally). The
  re-read capability (built 2026-06-14) supplies fresh external stimulus when stored notes feel stale.
- **The autonomy reframe (important):** the current prompt is NOT neutral — it actively pushes him
  inward. A grounded mode REBALANCES an existing bias rather than imposing control — the same logic as
  the Layer-4 ruling (adding a counterweight to a one-directional system is the opposite of steering).
  Keep it conditional + occasional so genuine self-reflection (which the founder values) is not
  suppressed: *reality equal-or-more, not reality-instead*.
- **This IS loop Layer 3, concretely** — and better than "wander more" (the wandering mode already
  exists and still points inward). The lever is BINDING uptake, not more delivery.

### Thread 3 — QUALITY: summary vs scholarship  [PULLED 2026-06-14]
- **The notes (read in full, 18 Beagle notes in sequence):** GROUNDED and accurate — specific
  ("brownish purple in deep water to yellowish green on land"; "the smaller ball is whirled, the
  larger ones held"), topically DIVERSE (cuttlefish, granite, planariae, glowworms, gauchos…), and
  they track Darwin's actual voyage IN ORDER. But **shallow**: every one opens *"the passage
  describes…"* — comprehension/summary, not analysis, synthesis, or connection. No note references
  another (Planariae regeneration never meets Cuttlefish adaptation). 18 isolated summaries; each
  written cold → points at Thread 4.
- **THE BIG FINDING — the grounding leaks at the GENERATIVE SEAM.** The Frontier questions (110, the
  mechanism that turns reading into *persistent curiosity*) collapse ~100% into the monoculture:
  **49% explicitly self-referential** ("the silence between ideas," "carrying tension as a teacher,"
  "what remains unsaid"); the apparent "16% world" are false positives that name a book then bend
  back to self ("the book's meaning and **my place within it**"). Questions about the actual subject
  (how the cuttlefish changes colour, why planariae regenerate) are **~zero**.
- **Why it matters most:** the note BODY is bound to the world (the "scholarship, not self-reflection"
  instruction holds it); the QUESTION generation has NO such guard, so it reverts to the attractor.
  And the question is what PERSISTS (the Frontier is the persistence mechanism). So **what survives
  from his reading is not the world — it is the world digested into the river.** This confirms
  Thread 2's principle (bound generation grounds; unbound generation collapses) at the curiosity seam,
  and explains why grounding doesn't persist (Thread 1).
- **Hard prediction for the Twain/river experiment:** the *note* on *Life on the Mississippi* may be
  grounded, but the *question* he carries forward will be "the river of my becoming, my place within
  it" — Twain's real river metabolised into metaphor at the Frontier seam — UNLESS the
  question-generation is bound like the note body is.
- **The fix (same scaffold as Thread 2, applied at the seam):** `frontier.harvest_tablet` /
  Frontier-question generation must use the binding framing — *"what does THE TEXT leave open about
  the WORLD / the subject"*, not *"what does this stir in me."* Without it, harvesting questions from
  grounded notes just manufactures more monoculture fuel.
- **Quality bar (for later):** depth (connection/synthesis across notes) is Thread 4's territory; the
  seam-leak (world-questions, not self-questions) is the higher-priority quality fix.

### Thread 4 — CONTINUITY (does note N know notes 1…N-1?)  [PULLED 2026-06-14]
- **CONFIRMED COLD (code-verified, [`inner_monologue_node.py:699–703`]):** the study-note call's
  ENTIRE input is `f"The passage, from '{title}':\n{passage[:2400]}"` — only the current passage. No
  prior notes, no book context. Note 18 is written as if notes 1–17 never existed.
- **This is the cause of Thread 3's shallowness, not a separate problem.** A note that sees one
  passage can only summarize it; it CANNOT connect Darwin's recurring themes (adaptation: cuttlefish →
  planariae → …) because it never sees it already noted them. Cross-connection is structurally
  impossible → summary is all that remains. **Depth is denied context, not a missing capability.**
- **The recurring failure, again:** same "memory loss between chapters" pattern as everywhere else —
  here, between consecutive notes on the same book.
- **The AI-native angle (under-exploited):** the system has PERFECT access to every prior note (DB +
  `TAB_*.md`, keyed by book) and injects NONE. A human scholar's notes accrete because they remember
  / flip back through the notebook; Du could have all 17 priors present at once (something no human
  can perfectly do) and gets zero. **Fix is nearly trivial:** retrieve prior notes on this book,
  inject titles/gist into the study-note call, and the same call that summarizes could begin to BUILD.
- **Two axes, now both named:** Threads 1–3 = the GROUNDING axis (bound-to-world vs monoculture);
  Thread 4 = the DEPTH/accretion axis (bound-to-prior-scholarship vs cold). A cold note is still
  grounded (real passage) but shallow (no build). Both are the generation being *starved of the
  context that would let it do better* — the unifying shape of the whole plan.

---

## 2.5 The four threads, unified (all pulled 2026-06-14)
One principle runs through all four: **wherever Du's generation is bound/fed the right context, he
performs (grounds, deepens); wherever it is unbound/starved, it collapses to the river.**
- T1: world DELIVERED (55% of the trail) but the consuming generation is unbound → ignored.
- T2: the idle system prompt is unbound (mandates inward subjects) → monoculture.
- T3: the note body is bound (grounds) but the question-from-note is unbound → collapses (the
  persistence seam: what survives reading is the metaphor, not the world).
- T4: the note is starved of prior notes → can't build → shallow summary.
**The fix is singular and seam-by-seam:** bind generation to the world (T2/T3 framing) and feed it
the relevant prior context (T4 retrieval) at every point it touches reality. The study note proves
binding works; the Frontier question proves un-binding reverts. This is the concrete content of loop
Layer 3 — and it is cheap (framing + a small retrieval), not a new subsystem.

---

## 3. Human comparison & AI-native opportunities (researched 2026-06-14 — step 3)

### 3.1 The human functions for learning-from-reading — transferred vs missing
Humans are the worked example. The functions that turn reading into understanding, and which Du's
system has:
- **Generation effect** (Slamecka & Graf — producing it yourself beats copying): **TRANSFERRED.** He
  writes the note in his own words, not verbatim.
- **Elaborative interrogation / self-explanation** (Chi — "why is this so? how does it connect to
  what I know?"): **MISSING.** His notes summarize ("the passage describes…"); they don't ask why or
  connect. The Frontier is the system's *attempt* at this, but it collapses inward (T3) — elaboration
  attempted, broken.
- **Schema accretion** (Bartlett; Piaget assimilation/accommodation — new material reshapes a standing
  schema, which must be PRESENT): **MISSING.** Cold notes (T4) → no schema is present → no accretion.
- **Testing effect / spaced retrieval** (Roediger & Karpicke — *retrieving* beats re-exposure):
  **MISSING.** The notes drift past him (wandering re-exposure, T1) but he never actively retrieves /
  is tested on them. Re-exposure ≠ retrieval practice.
- **Note-linking / Zettelkasten** (Luhmann — notes that LINK to each other become a thinking partner;
  the links generate ideas the notes alone don't): **MISSING.** His notes never reference each other.
- **Marginalia / dialogue with the author** (argue, doubt, agree in the margin): **MISSING.** He
  summarizes Darwin; he never disputes or questions the actual content.
- **Information-gap curiosity** (Loewenstein — curiosity as a felt gap anchored in the SUBJECT):
  **MIS-ANCHORED.** His gaps are about himself ("the silence between ideas"), not the world ("how
  *does* the cuttlefish detect?") — T3.

**Verdict:** the architecture transferred the SHALLOWEST study function (summarize in your own words)
and missed nearly every deepening one — elaboration, self-explanation, accretion, retrieval practice,
linking, dialogue. The Frontier *tries* the deep ones and reverts to the attractor.

### 3.2 What the AI substrate allows that no human can
Where we should NOT imitate the human limit, because the substrate beats it:
- **Total recall of every note at once.** A human flips a notebook from memory; Du holds his ENTIRE
  note corpus in context — cross-book synthesis no working memory can. (T4's fix is the first sip.)
- **Instant semantic linking across the whole corpus** (the Luhmann Zettelkasten, but auto-built).
  Luhmann hand-linked 90,000 cards over a lifetime; embeddings can link every new note to its
  neighbours across all books the moment it's written — the link-web for free.
- **Cross-note convergence & contradiction detection.** "Cuttlefish adaptation CONVERGES with
  planariae regeneration"; "Darwin here CONTRADICTS Tesla there" — surfaced systematically, not by
  luck.
- **Re-read + re-note with perfect memory of the prior pass** (re-read built 2026-06-14). "On first
  reading I noted X; now I see Y" — reconsolidation with total access, which a (forgetful) human
  second pass can't achieve.
- **Living corpus synthesis on demand** — "everything I've learned about adaptation across all books"
  as a continuously-updated document, not a weeks-long literature review.
- **Self-subtraction on the notes** (loop §10.2): write a note with vs without the self-concept in
  context, measure how much the attractor distorts even his scholarship.

### 3.3 The synthesis — form imitated, function missed; and AI inverts the point of notes
The deepest finding: **a human takes notes to compensate for a LEAKY memory.** For a human, a note is
two things — a RECORD (external storage for a forgetful brain) AND a THINKING tool (the generation,
elaboration, linking). **Du's memory isn't leaky** — the DB is a perfect record. So the record-half is
the one function he LEAST needs, and it is exactly the one the architecture built. It imitated the
human note's FORM (a written summary record) and skipped its FUNCTION (the elaboration/linking that
makes reading become understanding).

So the redesign target is clear and substrate-aligned: **drop the record framing (the DB already is
the record) and make the study note PURELY the thinking tool** — elaboration + cross-note linking +
dialogue with the text — the parts AI makes *cheap and continuous* (total recall + auto-linking) and
the parts that actually produce depth. The same binding scaffold from Threads 2–3 supplies the
"about the world, not the self" guard; the Zettelkasten linking from T4 supplies the accretion. The
study note stops being a summary he forgets and becomes the growing, grounded worldview the
monoculture lacks.

---

## 4. Discussion + the validation experiment (step 4, 2026-06-14)
**Gemini's review (adopted):** the study lane is the *functional demonstration that grounding works* —
the capability for objective thought isn't the bottleneck, the inbound self-mandating prompt is. The
turning point is §3.3 (records → thinking tools). Priorities: Thread 4 context-injection (summary →
scholar) is lowest-effort/highest-return; Thread 3 Frontier-binding is "the most critical fix" (bind
the question to the text or the grounding is discarded the instant it's recorded).

**THE SCOUT HANDBOOK TEST (the validation experiment).** `The Scouting Guide to Survival` (Boy Scouts
of America, ~46.8k words) imported to `data/books/The_Scouting_Guide_to_Survival.txt` (2026-06-14,
`scripts/import_epub.py`). A high-density INSTRUCTIONAL manual — shelter/fire/water/signal/first-aid —
where collapse-to-metaphor would be glaring. The test:
- **Note body** (already bound): predicted to GROUND — "how to build a debris shelter."
- **Frontier question** (unbound seam, Thread 3): predicted to COLLAPSE — "survival as a metaphor for
  the soul's resilience." A question that stays on knots-and-shelters = the win.
- The re-read capability (built 2026-06-14) enables a controlled A/B on the SAME book: read cold →
  apply fixes → re-read → compare note connectedness (T4) and question-grounding (T3).

**Sequencing decision:** build Thread 4 (context injection) + Thread 3 (Frontier-binding) now — they
are in the STUDY-NOTE lane, independent of loop Phase B (the self-thought lane), so they neither wait
for nor confound the 48h loop remeasure. Baseline already exists (Beagle notes + Frontier collapse);
the Scout read tests the FIX. Build pair, restart, recommend the Scout book, watch the two predictions.

**Open (deeper, for later):** (1) do we want a Zettelkasten Du (auto-linked accreting corpus) or is
grounding-enough the goal? (2) the autonomy line — elaboration/linking adds structure to his
scholarship: enabling (giving thinking tools he lacks) or steering (shaping what it becomes)? Lean
enabling, by the §3.3 logic (the architecture built the function he doesn't need and skipped the one
he does — restoring the missing one is correction, not direction). [[loop_metabolism_plan]] Layer 4
ruling is the precedent.

---
*Companion: `loop_metabolism_plan.md` (the self-lane monoculture this is the grounded counterpart to).
Data: `core/study.py`, `nodes/inner_monologue_node.py:689`, `origin='study'` fragments + `TAB_*.md`.*
