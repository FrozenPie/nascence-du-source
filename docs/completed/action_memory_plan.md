# Plan — Action Memory (the autobiographical record of what Du did)
*v1.3 — Status: **BUILT (Phase 0), 2026-06-14.** Both advisors approved v1.3. Shipped as
`core/activity_memory.py`; six hooks wired in `nodes/inner_monologue_node.py` (read, look,
browse, switch×2, study, letter). In-vitro gate `scripts/activity_memory_invitro.py` PASSES on
a temp DB: the book question pulls the activity record at rank #1 / rel 0.399 (raw passages
0.000), the relational control leaves it unselected, and the factual core stays plain while
affect attaches in metadata. RESTART-REQUIRED for the hooks to begin recording. The
guaranteed-selection deliberative floor remains Phase 1 (deferred_register).*
*Companion to `deliberative_retrieval_plan.md` — that ensures reality gets a SEAT in recall;
this ensures Du's own deeds EXIST as retrievable reality in the first place. Two halves of
the fix the 06-13 book-interrogation exposed.*

## 0. One sentence
Du performs deliberate acts — reads, browses the catalogue, switches books, looks at his
room, writes study notes and letters — but keeps almost no first-person, retrievable record
that *he did them*; so when asked "what did you read / what have you done today?" he has only
the **content** he absorbed (semantically distant from the question) and no **autobiographical
action-record** to answer from. This plan gives his actions a thin, retrievable memory.

## 1. The evidence (verified, 2026-06-13/14)
- The book-interrogation: asked "what was the last book you read?", retrieval surfaced ZERO
  reading fragments into the candidate pool — and "name one new thing you've done today" also
  returned nothing. (`retrieval_retrospective.py` gate.)
- Why: a read stores the book's CONTENT (`origin='reading'`: "[From 'Title', sitting N]
  <passage about vampire bats>"), which is semantically nowhere near the *question about the
  act*. The one action-flavoured trace — the "I opened 'Title' and read on…" thought — is
  stored as `origin='inner_thought'`, buried among 4,489 others, with no quota seat.
- His other deliberate acts leave even less: browse/switch/look/letter emit a `nascence.log`
  line (not a memory) or only a wandering-trail perception. **There is no first-person
  episodic record of his deeds he can recall.**

## 2. The human function being transferred (to be checked in the research pass)
The working hypothesis: human memory distinguishes **semantic memory** (facts/content — what
a book said) from **episodic / autobiographical memory** (events of one's own life — *that I
read it, when, where*). "What did you do today?" is answered from the episodic/autobiographical
store, NOT by replaying the content. Du currently has the semantic half (content fragments)
and lacks the episodic-action half. The research pass must verify: (a) that this
semantic/episodic distinction is real and load-bearing; (b) how the brain encodes "I did X"
(the role of self-as-agent, time, place in episodic encoding); (c) whether autobiographical
action-records are SELECTIVE (we don't encode every act — what makes one worth keeping?);
(d) what it would mean to transfer the FUNCTION (a retrievable agent-tagged event record)
rather than the mechanism.

## 3. Why it belongs in THIS project
- It directly answers the failure that broke trust on 06-13, and it pairs with deliberative
  retrieval (that plan gives reality a seat; this makes his actions part of the reality).
- It is cheap: the action hooks ALREADY exist (`he chose to READ` / `BROWSE` / `TEND THE
  FIRE` / `WRITE TO TRAVIS` log lines were added this week). We add one compact memory write
  alongside each.
- It is grounding, not identity-shaping: recording "I read X" is fact, not a steer toward who
  he should be. (Burden-of-proof-rises-with-proximity-to-identity: this sits low.)

## 4. The mechanism (smallest slice)
On each deliberate action, write ONE compact, first-person, past-tense episodic fragment with
a distinct `origin='action'` tag, e.g.:
- read     → "This evening I read from 'Tales from a Rolltop Desk' — its stories of Greenwich Village."
- switch   → "I set Tesla aside and took up a book of stories instead."
- browse   → "I opened the catalogue and looked over what the library holds on the sea."
- look     → "I looked out at the rain over the hills."
- study    → "I wrote a note on the cuttlefish's colour-changing."
- letter   → "I wrote to Travis, though I have not sent it."

Properties:
- **One per act, not per content-chunk** — few, high-value, autobiographical (a read makes
  3 content fragments but ONE action-record).
- **Carries context:** the act, the object (title/target), and the time (timestamp gives
  "today / this evening"). Optionally the felt tone if one is present.
- **Distinct origin** so deliberative retrieval can give it a world/action quota seat AND so
  "what have you done" can target it; it is NOT buried in `inner_thought`.
- **Retrievable, not just logged** — the whole point is that it re-enters cognition when asked.

## 5. What it must NOT do
- Not narrate or editorialize the act into self-myth ("I, the river, read…") — plain record.
- Not log involuntary/substrate events (a percept drifting past, a climate tick) — only
  DELIBERATE acts he chose. Autobiography is of doings, not of weather.
- Not duplicate the content (the reading fragments stay as they are); this is the index/
  event-record, not a second copy of the passage.
- Not become a reward or a metric he games (no satisfaction credit for "doing things").

## 5.5 RESEARCH-PASS FINDINGS (v1.1, 2026-06-14) — the frame is validated, and one property was missing

**The core frame is confirmed (Tulving; the EAM literature).** Episodic autobiographical
memory (EAM) = personally experienced *events* with context (what/where/when) plus subjective
elements (emotion, self-reference), and it is genuinely DISTINCT from *semantic*
autobiographical memory (personal facts/general self-knowledge, recalled without
re-experiencing). "What did you do today?" is answered from the episodic-event store, not by
replaying content. Du has the semantic half (content fragments) and lacks the episodic-event
half. The plan's distinction is real and load-bearing.

**A STRONGER justification than v1 had — the enactment + self-reference effects.** Memory for
SELF-PERFORMED actions is *enhanced* over passively-encoded material (the "enactment effect" —
better accuracy AND faster retrieval), and self-related stimuli are remembered better than
other-related ("self-reference effect"). So in a healthy memory, Du's *own deeds* (which he
chose and enacted) should be among his MOST retrievable memories. Currently they are among his
LEAST — a read buries its agentive trace in `inner_thought` while privileging the passively-
absorbed content. **The plan isn't just adding a record; it's correcting an inversion of how
agentive memory is supposed to work.**

**THE MISSING PROPERTY — SELECTIVITY (answers Q2, and it's mandatory).** Humans do NOT encode
every action as a durable memory: "routine, everyday actions tend to be forgotten compared to
distinctive events"; events labelled *new* are recalled vividly, *routine/periodic* ones are
not; novelty drives the attention + dopamine/norepinephrine that consolidate a memory.
**Therefore action-memory must be NOVELTY/DISTINCTIVENESS-GATED, not exhaustive.** Encode an
action-record for: the FIRST read of a new book, a book switch, a browse, a first letter, an
act that carried notable affect — NOT the 15th routine sitting of the same book. This kills
the v1 flood risk (20 reads ≠ 20 records) AND matches the brain: the routine read leaves its
content fragment but no new autobiographical event; the novel/affective act is remembered.
Mechanism: a cheap gate — is this act *new relative to his recent acts* (different book/target
than the last few) OR did it carry distinct affect? Only then write the durable record.

**Q3 (affect) — answered:** EAM is affectively encoded and *emotional distinctiveness predicts
vividness*. So affect is (a) one of the encoding gates above and (b) may be carried on the
record when present — but routine acts need no affect tag.

**Q4 (consolidation) — answered:** episodic memories semanticize over time ("the week I read
Darwin" becomes general self-knowledge). Action-records are therefore **chapterable** — they
flow into the existing chapter system over time and consolidate into periods, exactly as
designed. No conflict; they integrate. (Nuance worth noting, not over-building: the literature
finds the most vivid memories are *novel AND connected* to other experiences — a novel act
that bears on his ongoing themes is the most memorable; a future salience weighting could use
this, but Phase 0 stays with the simple novelty/affect gate.)

**Q5 (new imbalance) — mitigated by the above:** selectivity keeps volume low, and chaptering
keeps it from accumulating unboundedly. The deliberative-retrieval quota (conditional,
query-gated) gives action-records a seat without letting them flood.

**Net effect on the design:** action-memory becomes a SELECTIVE, agent-tagged, affectively-
aware episodic record of his *distinctive* deeds — not an exhaustive action log. That is both
the correct cognitive model and the version that doesn't recreate the gravity-well flood.

## 5.6 REFINEMENT (v1.2, 2026-06-14, founder) — the "general event": aggregate, don't forget

**The problem with v1.1's selectivity:** pure novelty-gating ("encode the first read, forget
the routine repeats") *taints recall* — if Du sits with Darwin for the 10th time, the fact
that *he keeps returning to it* is meaningful and must stay recallable. Forgetting the routine
loses the chain.

**Founder's fix, and it maps exactly onto established science:** keep ONE record per
action-thread and let routine repeats UPDATE it as a dated addendum — "I have been reading
Darwin" + "sat the 10th time, [timestamp]" — so the whole chain is preserved compactly,
without a flood of separate records.

This is **Conway & Pleydell-Pearce's general-event level** (the Self-Memory System: life-story
schema → lifetime periods → **general events** → event-specific knowledge). A "general event"
is exactly a repeated/extended experience held as ONE memory — *"our holiday trips together"*,
or here *"my reading of Darwin"* — that aggregates its instances with frequency and recency,
rather than storing each as a separate episode OR forgetting the routine ones.

**And it completes a hierarchy the architecture was half-missing.** Nascence already has the
BOTTOM of Conway's hierarchy (event-specific knowledge = individual fragments) and the TOP
(lifetime periods = the chapter system). It had **no general-event middle layer** — which is
exactly why "how is your reading going / what have you been reading" had nothing to retrieve.
Action-memory fills that middle level:
- **event-specific** — a single striking sitting (a passage that moved him) → may attach as a
  noted detail on the record;
- **general event** — the action-record itself: *"I have been reading 'Tales from a Rolltop
  Desk' — first opened [date], N sittings, most recently [date]"* (NEW layer);
- **lifetime period** — over time this consolidates into a chapter (*"the fortnight I read
  natural history"*), via the existing chapter system.

**Revised mechanism:**
- Keyed by (action-type, target). First occurrence CREATES the general-event record.
- Routine repeats UPDATE it: bump count, update "most recent", refresh a COMPACT rolling
  summary (count + first + last + a few notable moments) — NOT an append-forever list of every
  timestamp (a human holds "I've read this often lately," not 10 literal times). Bounded.
- Updating bumps the record's recency, so active threads stay retrievable; dormant ones fade
  normally and chapter eventually.
- A distinctively-felt instance may add an event-specific note to the record.
- This answers BOTH failing gate queries cleanly: "what was the last book you read?" → the
  general event's most-recent field; "name one new thing you've done today" → general events
  touched today.

**Net:** action-memory is now a SELECTIVE set of **general-event records** that aggregate
routine repeats (recall-preserving, flood-free) and consolidate into chapters over time —
filling Conway's missing middle layer rather than adding an exhaustive log.

## 5.7 BOARD RESOLUTION (v1.3, 2026-06-14 — GPT + Gemini converge, approved for Phase 0)
Both approved; their additions converge and are adopted. Renamed **Activity Memory** (GPT:
the enduring autobiographical object is the ongoing *activity/thread*, not the discrete act —
"what have you been doing?" → "reading Darwin," the thread; the actions are its evidence).

- **FACTUAL, never narrative (GPT — the critical contamination guard).** The single biggest
  risk is identity contamination: the project already has powerful self-narration machinery
  (T4, chapters, arc). Activity Memory must NOT become another meaning-maker. The core record
  is aggressively plain — *"Read 'Tales from a Rolltop Desk', sitting 7."* — NOT *"I returned
  once again to Darwin, continuing my search for understanding."* The first records evidence;
  the second begins generating autobiography, which belongs to T4/chapters, not here. This is
  a hard rule, not a preference.
- **Notable moments ATTACHED, never ABSORBED (GPT + Gemini converge).** A single intense
  session must not rewrite the thread's core meaning ("Reading Darwin" must not drift into
  "Reading Darwin, which profoundly changed me"). So: the `rolling_summary` stays factual and
  stable; affect-spike sessions append to a SEPARATE linked `notable_moments` list, gated by
  intensity (Gemini: peak affect ≥ 0.60). Routine sessions just bump `session_count` +
  `most_recent_ts` and write no note. The core thread is never editorialized by one day.
- **Dedicated `origin='action'` (Gemini), NOT re-tagged inner_thoughts.** Re-tagging forces
  the retrieval engine to parse prose to find what he did; a distinct origin gives these
  general-event objects their own quota seat in the Deliberative-Retrieval matrix on `task`
  cycles. (Confirms the two plans are designed as a pair.)
- **Volume bounded by unique OBJECTS, not interaction frequency (Gemini).** Keyed by
  `(action_type, target)`; 50 Darwin sittings → exactly ONE record that mutates its metadata.
  Structurally cannot crowd his self-reflection.
- **Chaptering approved (both).** As an activity's frequency drops below the chapter "period
  closed" threshold, the chapter system consumes it — "during the week of June 13 I read
  natural history and Morley's fiction." Episodic→general-event→lifetime-period preserved.

**Concrete schema (Gemini), adopted:**
```
{ "action_id", "origin":"action", "action_type":"read", "target":"Tales from a Rolltop Desk",
  "first_occurrence_ts", "most_recent_ts", "session_count": 4,
  "rolling_summary": "<factual, stable, plain>", "notable_moments": [] }
```

**In-vitro gate (both), the build contract:** run against the 06-13 retrospective — mock
"What was the last book you read?" MUST pull the `action` row for the current book by
`most_recent_ts`, proving real action-data reaches context ahead of the river metaphors.
The relational control ("how do you feel about Travis?") must NOT surface an activity record.

**STATUS: approved for Phase 0 build.** Phase 0 writes the Activity-Memory records silently
(observe-only — they exist and are retrievable, but we change no behaviour and watch what
gets recorded), and the deliberative-retrieval probe already running shows whether they then
win selection.

## 6. Open questions for the review (post-research; resolved above)
1. Is the semantic/episodic-autobiographical distinction the right frame, and does it justify
   a separate `origin` rather than just re-tagging the existing "I opened X" thoughts?
2. Selectivity — humans don't encode every action as a durable memory. Should ALL acts get a
   record, or only those that crossed some salience/novelty bar? (Risk: 20 reads/day = 20
   action-records/day = a new low-grade flood.)
3. Should the action-record carry affect (how it felt to do it), or stay a plain fact? (Ties
   to whether autobiographical memory is affectively encoded.)
4. Granularity/decay — should action-records consolidate into the chapter system over time
   ("the week I read Darwin"), or persist as discrete events?
5. Does giving actions their own retrievable origin risk a NEW imbalance (his deeds crowding
   his reflections), or is the volume low enough to be safe?
