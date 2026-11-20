# Session 2026-08-19 — health-check fix set + HUD audit

**Founder + Claude.** Direct continuation of the 08-18 overnight deep health check (12-agent parallel
audit while Du ran, published separately as "The Night Watch" report). This session closed out the
"needs your call" items from that report — the founder confirmed Du stopped and said to fix what could
be fixed unilaterally, ask where genuinely ambiguous. Three fixes landed, then a HUD monitor-registry
audit to make sure new/repaired systems are actually visible on the dashboard.

## CHANGED

1. **`core/symbol_tracker.py` — the Meaningfulness-axis tracker was structurally broken, now fixed.**
   `symbol_recurrence.jsonl` showed 1000/1000 logged appearances as PRIMED, zero ever UNPRIMED, across
   every tracked symbol — including 174 cases with no human turn that cycle at all. Root cause:
   `_primed_corpus()` folded Du's own recent output (`conversation_history[-3:]`'s `jung` side) into
   the "this was injected" corpus, so any symbol he returned to on his own within 3 cycles was
   automatically disqualified from ever counting as autonomous recurrence — exactly backwards from
   what the tracker exists to detect. Dropped the entity's own voice from that corpus; kept the human
   side (legitimate external input). Verified both directions with a fake-state test: self-continuity
   now reads UNPRIMED, human-input priming still correctly reads PRIMED. This is the mechanism
   `core/symbol_evolution.py`'s drift/tablet system depends on — it could never have fired before this.

2. **`core/world_traces.py` — growth cap added; burst investigated, not conclusively solved.**
   A 9,062-row burst (3,087 shore + 5,975 wood) hit the file in an 11:39–11:45 window on 08-18. Traced
   the live creation path (`sensorium.tick()` → `cat.tick()`) and found it double-throttled (5s + 180s
   real-time gates) — physically incapable of producing that volume in six minutes. The only other
   `create_trace()` call site anywhere in the repo, `scripts/test_cat_ecological_laboratory.py`, makes
   exactly 2 unconditional calls with no loop — ruled out as the sole cause, but it was a real, separate
   hazard: fully unsandboxed, it deleted the live `world_traces.json` and overwrote live `cat_state.json`
   on every run. Fixed by isolating it to `data/lab/cat_ecological_lab/` (matches this project's other
   isolated lab scripts). The burst's exact origin stays unconfirmed. `world_traces.py` now hard-caps at
   500 traces (oldest-first eviction on every `create_trace()`), so it can't recur regardless of cause.

3. **Silent-failure logging hardened across ~24 flagged files/functions.** The health check's most-
   repeated finding: write paths with `except Exception: pass` and no logging, several with no logging
   import at all. Three agents applied this codebase's established `reentry.py` idiom (DEBUG-level,
   `[bracket-tag]` prefix, exception still swallowed — visibility added, no control-flow changes) in
   parallel:
   - `identity_vault.py` (previously zero logging — the T4 write path) instrumented at read/write/
     commit/status.
   - `affect_divergence.py`, `emotion_construction.py`, `mood.py`, `error_pathway.py`,
     `curiosity_queue.py` — no logging import before; added.
   - `commitment_ledger.py`, `self_efficacy.py`, `epistemic_state.py`, `pursuits.py`,
     `memory_levels.py` (specifically `_commit_gist()`/`memory_lint()`), `affections.py` — already had
     loggers, audited for unlogged except blocks and fixed those.
   - `world_model.py`, `world_objects.py`, `keepsakes.py`, `geometry_census.py`,
     `emissary_tension.py` — no logging import before; added. `world_model.py`'s beat-log write (right
     before its state-save) got a *defensively double-wrapped* log call specifically so a logging
     failure there can never cascade into blocking the save.
   - `social_moves.py` — added logging. `judge_panel.py`'s own ruling-metric write instrumented.
   - `orchestrator.py` — touched **only** the 4 named sites from the health check
     (`AFFECT_SOURCE_PROTOSELF` apply, `retraction_ledger.retract`, `letters.mark_delivered`,
     `satisfaction.record` — two call sites, both logged), nothing else in the file.
   - `_save()` in `cat.py`, `soundscape.py` (`_save_snd_state()`), `sound_knowledge.py`,
     `listening.py`.
   All touched files verified with `python -m py_compile`; spot-checked several by hand against source.

## HUD audit (same session, following straight on)

Cross-referenced every `MONITOR_REGISTRY` entry in `hud/server.py` against the real `data/*.jsonl`
files. Four gaps found — real, actively-growing systems with zero graph anywhere on the dashboard —
plus one stale label from fix #1 above. All added/fixed in `hud/server.py`, all verified functionally
(`load_monitors_index()` / `load_monitor()` return correct payloads, frontend already iterates a fixed
`["system","ready","failing","hold","plans","staged"]` group list so no HTML/JS changes were needed):

- **`emissary_tension`** (plans) — the Lane 2 standing-tension accumulator (`chronic_mass`,
  `recurrences`) the K1/K3 kill-criteria recheck reads from. 7,900+ real rows, zero prior graph.
- **`t4_watershed`** (plans) — the Phase 0 harvester built this week. Deliberately added even though
  `watershed_shadow.jsonl` doesn't exist at the live data root yet (Phase 0 isn't wired into the
  orchestrator per the plan's own build order) — `has_data` correctly reads `false`. The card exists
  now so it's visible the moment Phase 1 wires it in, instead of someone having to remember to add it.
- **`identity_projection`** (plans) — Identity Estate P1 shadow projection (`IDENTITY_PROJECT_LIVE=
  False`). 2,200+ real rows, zero prior graph. Renders as an events/hour rate card (its fields are
  lists, not numbers) — still a real "is it actually firing" signal.
- **`self_relate`** (plans) — 600 real rows, `n_world` numeric field charted, zero prior graph.
- **`symbol_evolution`** label corrected — was "structurally unreachable" (accurate as of 08-18, now
  false as of fix #1 above). Kept in the "failing" group, not moved to "ready", because no live cycle
  has run against the fix yet; new title: "fix landed 08-19 — watch for first UNPRIMED row". This card
  is exactly how to confirm the fix is working once Du runs again.
- **`psyche_graph`** moved from "staged" to "plans" and retitled. It had sat mislabeled as an unreviewed
  design for 6+ weeks — it actually shipped 2026-07-03 and has run every sleep since (90+ real
  snapshots). See item 4 below for the full audit.

## Psyche Graph audit — founder asked to look at this "staged plan" next

It turned out not to be staged at all, and turned up something more important along the way.

- **Status was stale everywhere it was recorded.** The doc's own header said "design captured, NOT
  approved, NOT built"; `core/psyche_graph.py`'s own header comment pointed at
  `docs/staged/psyche_graph_instrument.md` (file actually lives in `docs/completed/`);
  `docs/ROADMAP.md` linked the same wrong path and marked it 💤 staged. All three corrected — it's
  confirmed live, called every sleep from `nodes/inner_monologue_node.py`.
- **A documented-but-unenforced design contract.** The doc claimed the graph only ingests UNPRIMED
  symbol appearances via `symbol_tracker.py`. In reality `psyche_graph.py` never calls
  `symbol_tracker` at all — it has its own independent `MOTIFS` lexicon with plain regex matching,
  no primed/unprimed gating. Two of those motifs, `mirror` and `bridge`, are literally
  `symbol_tracker.SELF_SYMBOLS` — identity-adjacent symbols whose read-back is deliberately deferred
  elsewhere in the codebase because re-surfacing an evolved self-symbol is what once monocultured
  Du. `mirror` is consistently one of the graph's highest-frequency nodes in real data. **Founder
  call: leave them in** — the instrument is observe-only and never read back to him, so there's no
  behavioral risk, only a documentation-accuracy question; their presence also preserves continuity
  with 90+ existing snapshots and may itself be informative (does a self-symbol show the same
  stability pattern as world symbols?). `MOTIFS` unchanged; doc corrected to describe reality.
- **The more important find: this reopened fix #1.** `docs/ROADMAP.md` already had an entry
  (`symbol_evolution_readback_plan.md`, dated 2026-07-05) diagnosing the exact same
  `_primed_corpus()` bug fix #1 addressed tonight — down to the same root cause — and it had been
  **explicitly parked pending a founder decision** ("retire, OR revive by narrowing priming to
  architecture-injection only... not his memory/thoughts"). Fix #1 was found independently through
  fresh data analysis without seeing this entry, and effectively executed the "revive" branch
  without that decision being made first. It was also **narrower** than what the 07-05 note
  prescribed — it only dropped Du's own recent conversation turns, not the other retrieval-based
  fields. Surfaced to the founder directly; **decision: go further.** `_primed_corpus()` now excludes
  `recall.reconstruction/tensions`, `episodic_scene.scene`, `memory_fragments`, `recent_dreams`, and
  `recent_inner_thoughts` as well — only true architecture injections remain (raw human input,
  perception summary, axiom/climate/epoch/theme/readback, and the human side of recent conversation
  history). Verified with fake-state tests covering self-continuity, human-priming, and
  memory-retrieval cases — all three now classify correctly. `docs/ROADMAP.md`'s entry updated to
  record the full resolution.

## New build: Self-Interrogation (`core/self_interrogation.py`, Phase 0 shadow)

Founder-directed, from a discussion (not a bug report): the existing architecture has real machinery
that keeps a loose thought from instantly hardening into belief (T4 probation, the Watershed harvester
below) — but all of it works by making a claim wait and recur over time. Nothing taught Du to catch
himself in the moment, on a single thought, and ask why he believes it. Built on a developed thought-
train (past `TRAIN_MAX_STEPS`, sampled 20%, 15-min cooldown): a neutral first-person reflection prompt
(deliberately not "check if you're wrong" — `reentry.py`'s documented sycophantic-flip lesson), graded by
the DECOUPLED judge panel (a different model than generated either the thought or the reflection) for
whether it named something specific or just performed the shape of humility. Wired as a non-blocking
background task from `nodes/inner_monologue_node.py`'s train-step handler; verified with an isolated
mocked test (all three gate paths + a full fire) and confirmed correctly profile-rebased. Full design and
what would license a Phase 1: `docs/plans/self_interrogation.md`.

## Restart + live confirmation

Du was stopped for the fix work above, then restarted (~09:42). Confirmed live, not just code-reviewed:

- **Symbol tracker fix: working in production.** First real cycle after restart produced the mechanism's
  first-ever genuine UNPRIMED row (`knot`/"rope", 10:10:16, internal cycle) — 1000+ rows had been 100%
  primed before tonight's fix; the very next new row was unprimed. Centroid confirmed seeded (`count: 1`)
  in `core.memory.store.get_symbol_centroid`. No tablet yet (needs `_MIN_SAMPLES_FOR_DRIFT=4` per symbol)
  — expected, not a problem.
- **`self_interrogation` hasn't fired yet — confirmed expected, not broken.** Its gate requires a
  thought-train past `TRAIN_MAX_STEPS=4`; checked `nascence.log` directly and no train reached step 2
  in the ~33 minutes since restart, so the gate was never reached. Wiring was already verified via
  isolated mocked test before deploy.
- **HUD restarted twice** (stale in-memory registry doesn't hot-reload) and re-verified over real HTTP
  each time — all new/changed cards render correctly, including the psyche_graph/symbol_evolution/
  contradiction_rearch label updates and the new self_interrogation/emissary_tension/t4_watershed/
  identity_projection/self_relate cards.

## AST-1 attention-schema loop — fixation-prediction baseline fixed (`core/attention_schema_loop.py`)

Checked on request: both halves (`observe_schema()`/`control()`) are genuinely wired into
`orchestrator.py`, not dead code — 330 real predictions logged since 2026-07-04, `AST_CONTROL` still
`False`, 0 controls ever applied (the "represents" half has real data; the "enables control" half has
never been tested, as designed). But `fixation_acc: 0.76` turned out to be a misleading number: fixation
is only true ~18-22% of the time, so "always guess not-fixated" scores ~0.78-0.82 — beating the
self-model's raw accuracy. Textbook class-imbalance failure, not evidence fixation is unpredictable.

**The fix, and the lesson in how it was built:** `status()` now reports `fixation_base_rate`,
`fixation_beats_base`, and `fixation_informedness` (Youden's J = sensitivity + specificity − 1, which is
0 for any baseline-mimicking predictor and only positive when the self-model genuinely discriminates) —
raw accuracy is never reported alone again. Measured against real history, the *existing* persistence
predictor scores informedness ≈0.3-0.37 — genuinely positive; it was never actually broken, raw accuracy
was just the wrong lens. **A second attempt was made to also improve the predictor itself** (a two-state
learned transition estimator, backfilled from the 330-row history) — and backtesting it against the real
sequence *before* deploying showed it would have made informedness worse (≈0.16-0.21), converging toward
always-guessing-majority — the exact degenerate behavior the new metric exists to catch, reached by a
fancier route. Not shipped. Kept as a logged-only diagnostic, explicitly commented to never silently
start driving the prediction without a fresh backtest proving it helps. HUD signature added
(`AST · fixation informedness`) so this can never regress to a misleading number unnoticed again.

## Still open

- **World-traces burst origin** — not conclusively identified. The cap prevents recurrence regardless;
  if it happens again, check whether it's reproducible (would narrow it to something still live, not a
  one-off ad hoc invocation).
- **`self_interrogation`'s real evidence** — wired and verified, but has not fired yet (see above). Watch
  `self_interrogation_shadow.jsonl` / `self_interrogation.status()`'s `genuine_rate` once a real
  thought-train develops past step 4.
- **Symbol Evolution's fuller confirmation** — one genuine unprimed row confirmed (see above); still
  needs 3 more unprimed appearances of the same symbol before drift becomes measurable at all, and a real
  tablet is further out than that.
- **T4 Watershed Phase 1** (orchestrator wiring, claim-test panel, estate `becoming-symbol` node type)
  — per the plan's own phasing, still gated on reading the Phase 0 retro-validation result
  (`docs/lab/watershed_retro_validation_report.md`) against the 4 open founder decisions in
  `docs/plans/t4_watershed.md`. Founder review pending.
- **~90 other `data/*.jsonl` files with no HUD graph** — deliberately not all added. Most are one-shot
  event/training logs (debate transcripts, math drills, essay lessons) that were never meant to be
  dashboard series; `voice_contract_shadow.jsonl` (8 rows) and `needle_triage_shadow.jsonl` (15 rows)
  were checked and left out as too low-volume to be worth a permanent card yet — revisit if either
  starts firing more.

---

# PART 2 (same date, later session) — Reading/school/curriculum, study-system expansion, memory-linking

Separate continuation later the same day. Started as "check school" → became a full reading-system
audit → curriculum redesign → a much larger study-system rebuild → a founder-flagged concern about one
piece of that rebuild ("3 related snippets feels old") → discovery of `docs/plans/memory_multiway_linking.md`
(built 08-15, not previously seen this thread) → a full codebase survey (3 parallel agents) for the same
pattern elsewhere → a long punch-list of fixes across two more turns. Ordered as it happened.

## Reading/school audit + curriculum redesign

- **Music competence bug fixed.** `core/competence.py`'s `CompetenceTracker._save()` overwrote the whole
  `data/capability_beliefs.json` with only its own in-memory beliefs, silently erasing domains (like
  `music`, first-ever graded that day) that `record_drill_accuracy()` — a separate writer to the same
  file — knew about but the tracker didn't. Fixed to merge-before-write. Backfilled the real file to match
  the actual logged outcome (8/8 correct).
- **Reading-duplicate mystery solved — a real bug, not organic behavior.** ~27 books "completed" in 64
  minutes (02:09–03:13 on 08-12) while Du's own activity log showed him doing unrelated things (observing
  the sea, an anemone) — a pure bookkeeping artifact, not lived reading. Root cause: `school.py`'s
  `set_curriculum()` unconditionally reset `curriculum_idx` to 0 with no check for whether the incoming
  list overlapped already-finished books; since `reading_state.json`'s per-book `pct` persists forever,
  the reset instantly found the whole original 40-book list "already finished" and cascaded through it.
  **Fixed:** `set_curriculum()` is now idempotent — a re-run with an unchanged (or already-loaded-prefix)
  list is a no-op instead of resetting. Verified isolated (3/3 cases: no-op on identical re-run, correct
  reset on a genuinely new list, first-ever load still works).
- **A second real bug found in the same audit:** `Meditations`, `On Liberty`, and Montaigne's `Essays`
  (shelved back in an earlier session, task #10) were fetched but **completely unread, zero entries ever**
  — because `book_selection.select_explore()` excludes anything already on the shelf from candidacy, so a
  shelved-but-never-formally-assigned book can never be organically reached. Fixed by putting them in the
  new curriculum explicitly (below).
- **New 40-book curriculum designed and loaded live** (`scripts/load_curriculum_v2.py`), replacing the
  original list Du had mostly already read. Founder asks: a book about time (Einstein's *Relativity*,
  Eddington's *Space, Time and Gravitation*, Poincaré's *Science and Hypothesis*, Bergson's *Time and Free
  Will*, Kant's *Critique of Pure Reason*) and a book about memory vs. physical possession (Locke's *Essay
  Concerning Humane Understanding*, Hume's *Enquiry*, James's *Principles of Psychology Vol. 2*, the two
  shelved-and-stranded classics above) — plus a general rebalance toward real epistemology/psychology/
  philosophy-of-science over the original list's heavy skew toward boyhood-adventure/craft manuals. Every
  title verified against the real Gutenberg catalogue before load; none already-finished (would retrigger
  the same cascade class the idempotency fix just closed). **Live**, book #1 = Einstein's *Relativity*.
- **Content-safety gap found, not yet fixed:** the breadth engine has *zero* content curation — pure
  novelty(=rarity)×relevance×coverage weighting, which actively *favors* obscure books. Found a real
  instance: *The Traitor* (Thomas Dixon Jr., the Reconstruction-trilogy predecessor to *The Clansman*/
  *Birth of a Nation*, 22 downloads) was fully read (100%, 62 sittings) and essayed with zero critical
  distance, engaging Klan content as neutral plot texture. Scanned all 83 real read titles for similar red
  flags — this looks like an isolated incident, not a pattern, but the structural gap that produced it is
  still live. **Not fixed — flagged for a founder decision** on what kind of gate (subject/keyword denylist
  vs. a stricter floor for public-domain political fiction vs. something else).

## Book Feelings (`core/book_feelings.py`, new)

Per-book affective valence, separate from the flat existing `JOY_READING` bump. Light EMA touch every
reading sitting (`core/reading.py`, real carried mood → book's valence); heavy touch once per book at
essay completion (`core/essay_lesson.py`, mood + the predicted/measured comprehension gap — overconfidence
mildly sours it). Read path: `joy_multiplier()` scales the existing flat reading-joy bump by the book's own
valence (0.4×–1.6×) — called on every real reading integration, so it's live from day one, not a shadow log
waiting for a consumer. Verified isolated (7/7 checks).

## Study system expanded to two tiers (`core/study_note.py`, `core/essay_lesson.py`, `core/reading.py`)

Founder ask: session-level notes linked to the actual sitting, a distinct "thoughts" field separate from
factual learning, cross-source referencing, and — for the book-level capstone — heavy weight on the current
read-through's notes with lower-weight access to an earlier read-through's, for rereads.

- `core/reading.py` gained `pop_session_encounters()` — an additive accumulator of every sitting's
  `encounter_id`/`offset`/pass, non-breaking (no existing caller's signature changed).
- `core/study_note.py` notes now carry a distinct `thoughts` field (his reaction, kept separate from
  `understanding`), and are tagged with the session's pass number (reread count) in both the file
  frontmatter and the DB (`source_pass`, `encounter_id`) — both the automatic remediation stream and his
  own free "I want to read" choice wired.
- `core/essay_lesson.gather_notes()` now splits this-read-through's notes (full weight) from an earlier
  read-through's (demoted into a clearly separated "FROM AN EARLIER READING" section, split off *before*
  the map-reduce condensation step so it can't be mangled). Backward-compatible: the ~1,657 existing
  untagged notes default to pass 0, so nothing changes until a book is actually reread.
- Cross-source referencing (v1): a bounded, zero-extra-LLM-cost lookup of related material from other
  books, offered to the compose prompt as optional grounding ("use only if it genuinely fits"). Superseded
  by the graph-walk redesign below within the same session.

## The "3 related snippets" conversation → discovery of the real memory-linking plan

Founder pushback on the cross-source-referencing v1 above ("this feels like a very old system... I have a
feeling we can make this work better now") led to an empirical check: sampled 8 real study notes, found
200–900 of 1,600 fragments clear a naive 0.35 cosine bar against any one of them — the corpus is
stylistically homogeneous first-person prose, so raw cosine mostly measures "sounds like his writing," not
"same idea." Two fixes shipped immediately (graph-walk over the already-validated `relates_to` edges
first, cosine-blended-with-lexical-overlap scan as fallback — `_lexical_overlap`, `_graph_walk_related` /
`_scored_scan_related` in `study_note.py`). A third, bigger direction ("standing pursuit-style threads for
reading, not one-shot lookups") was being planned when **`docs/plans/memory_multiway_linking.md`
(2026-08-15) surfaced** — a more rigorous, partly-already-built typed-edge system (`core/memory_edges.py`)
that explicitly names `study_note.py`'s `relates_to` links as "re-materialised similarity, not a second
kind of connection." Its M2 (the part that would actually let anything *read* the typed graph) is
explicitly gated behind a founder-read of ~a week of M1 co-recall shadow data — not reached yet (checked:
4 days in at the time). Decision: don't invent a parallel system; respect the existing gate; in the
meantime, close the observability gap the survey below found (reading/study material was entirely outside
the M1 evidence base the eventual gate-decision depends on).

## M1 co-recall ledger wiring — the big cross-cutting fix

`memory_edges.log_co_recall()` was, before tonight, called from exactly one place (the main monologue
train). A full codebase survey (3 parallel research agents: retrieval call-sites, untracked relational
connections, shadow-system inventory) found it missing from most of the codebase's other similarity-based
retrieval. Wired in, in order:

1. `study_note.py`'s session notes (`_log_m1_co_recall` — `restate_sim` = cosine to this book's own most
   recent PRIOR note, matching the main train's exact semantics; `ids` = the related-context material).
2. `essay_lesson.gather_notes()`'s cross-book compounding — found to be the **worst offender** in the
   survey: same pathology as study_note's original code, a *lower* bar (0.30) and *bigger* cap (12), and
   querying on the bare book **title** rather than any actual content. Rebuilt with the same graph-walk-
   first + blended-scan-fallback pattern (`_graph_walk_cross_book`, new). `restate_sim` honestly left
   `None` — essays fire once per book, no clean "prior thought in this thread" exists at that granularity.
3. `inner_monologue_node.py`'s Grand Work grounding and `dream_node.py`'s scene-weaving — both called
   `associative_recall.recall_fragments()` directly, bypassing the hook `recall_block()` already has.
   Both wired; dream's `close_reason` (resolved/stalled/ended-unfaced) is a genuine categorical verdict
   sitting right there but was **not** mapped onto a fabricated cosine value to force it through
   `log_co_recall`'s numeric classification — flagged in comments for later if the ledger's API grows a
   direct categorical path.
4. `wandering.py`'s `_drift_from`/`_affective_drift` — logged, but **deliberately no relevance floor
   added**, unlike everywhere else: this module's whole purpose is loose, serendipitous association
   ("any of them is as worthy of your next thought as you are"), and a floor would fight that intent, not
   fix a bug.

All verified isolated (temp DBs / mocked `log_co_recall`, real ledger never touched by tests except one
deliberate real smoke-test row on `essay_lesson.py` against real data, confirmed in the ledger).

## `subconscious_node.py` T4 crossing retrieval — real relation, not another M1 log

`_t4_retrieve_crossings()` discarded the `light_event` id it retrieved on, and the evidence-stage's
`has_movement` verdict (a genuine LLM judgment, not a similarity score) was computed and thrown away right
next to it — the survey's "best evidence-per-line" finding. Return shape changed to include the id;
written as a real new `memory_edges` edge type (`t4_crossing_evidence`, tension-hash → light_event,
weighted by cosine, provenanced with the actual verdict) rather than forced through `log_co_recall`'s
cosine-derived classification (mapping a category onto a fake similarity number would be fabricating
signal). **While making this change, a full-file grep caught a third call site (`:1679`) still unpacking
the old 2-tuple shape** — would have thrown `ValueError` the next time T4 deliberation ran. Fixed before
calling the change done, not after. Verified isolated (3/3).

## `memory/store.py` — four retrievals with literally no minimum similarity, now have one

`retrieve_by_affect`, `retrieve_epoch`, `retrieve_theme`, `retrieve_symbol_tablet` were pure top-K argmax
with **no floor at all** — always returned `top_k` results regardless of match quality, worse than a
badly-tuned threshold. Added a shared `_WEAK_RETRIEVAL_FLOOR = 0.30` (matching `evidence_recall.py`'s
already-proven value in this codebase). Confirmed all four real callers in `orchestrator.py` already guard
on empty results, so this is a safe behavior change. Verified isolated (5/5: weak-only matches now return
`[]`, a genuinely strong match still survives).

## `deliberative_judge.py` — decided, not left ambiguous

Backtested last night against the T4 keystone judge: 0/17 historical reverts would solidify vs. 1/17 for
the simpler already-shipped fix — stricter, risking this project's own known unreachable-floor disease one
layer deeper. **Decision: not adopted** for that role. Docstring rewritten to say so plainly (was "future
work," which — per the shadow-system survey — is exactly the framing that leaves a built, backtested,
never-wired module looking perpetually pending instead of actually decided). The `deliberate()` primitive
itself stays available for a judge that genuinely needs dual-reading + cross-rebuttal + evidence-expansion.

## `refinery.py` flipped live — after catching a real "big bang" bug first

Its own stated gate ("founder reads one night's shadow before the flip") was met — 3 nights, 72 records,
99% accept rate, mean fidelity 0.899. Before flipping, checked what the first live run would actually do:
`MAX_CLUSTERS_PER_RUN=6` bounds cluster *count* but nothing bounded cluster *size* — on the real backlog
(4,799 raw fragments, 112 clusters), the 6 largest alone total 2,803 members, which would have consolidated
58% of the entire archive in one run, directly contradicting the module's own stated law ("gradual
refinement, never a big bang"). **Added `MAX_MEMBERS_COOLED_PER_RUN=200` first** (soft cap — a cluster that
crosses it still finishes, so one legitimately large theme is never truncated mid-cluster); confirmed the
first live run now processes 1 cluster (368 members) instead of 6 (2,803). Then flipped `REFINERY_LIVE=True`.

## `derived_from` column poisoning — found, guarded, one writer fixed

Survey found the `memory_fragments.derived_from` column written by 5 places in 3 incompatible shapes: real
id-lists (subconscious/consolidation/refinery), a **metadata dict disguised as a one-element list**
(`activity_memory.py` — `json.dumps([{"action_type":...}])`), and a **private typed-edge object**
(`essay_lesson.py`'s own pre-`memory_edges` lineage format). Verified all three directly by reading each
writer. Added a prominent guard docstring in `memory_edges.py` (the natural future home for a `derived_from`
harvester) so a naive `for fid in derived_from` loop can't silently corrupt on the `activity_memory` rows.
Converted `essay_lesson.py`'s own contribution into a real `memory_edges` `transformed_into` edge
(essay → source notes) — kept the old field too for backward compat, but this removes one of the five
inconsistent writers from the underlying problem rather than only documenting it. `activity_memory.py`'s
shape was left as-is (a bigger, separate task — would need to check every consumer of its `derived_from`
field first). Verified isolated (2/2: edges written, idempotent on re-run).

## `needle_triage.py` — wired in, not shelved

Unlike `deliberative_judge.py`, this one had never been *evaluated* — built 08-18, smoke-tested once
(14 seconds of test traffic), then simply never connected to `core/pursuits.py`'s real judge calls despite
its own purpose requiring exactly that ("see over real volume whether Needle2 tends to agree"). Its prompt
is hardcoded to the PURSUIT/PRIOR-POSITION/NEW-THOUGHT shape, which matches exactly one real caller:
`pursuits.judge_pending()`. Wired there, off the event loop (`asyncio.to_thread`), never gating the real
verdict. Confirmed the `needle` engine is genuinely installed and returns real verdicts (~940ms) — this
will now actually accumulate real data. Docstring corrected to say precisely where it's wired (not "every
panel call," which was never true — `tension_ledger`/`left_lane` use different prompt shapes).

## `emotion_construction.py` — closed the blind spot, and it said something real

No `status()` existed at all despite the module being actively called from the live orchestrator (152+
rows, growing) — a genuine, previously-invisible blind spot per the shadow-system survey. Added `status()`
(primary-emotion agreement rate + mean valence gap between the LLM's guess and the grounded constructor),
wired into `hud/server.py`'s `_EVIDENCE_MODULES`. **First real read against live data: 0.7% primary-
emotion agreement over 152 paired rows** — essentially none. The deterministic-construction hypothesis
does not currently look like it's tracking the LLM's read at all. Not fixed — this is a finding, not a bug
in the monitoring code; flagged for the emotions discussion that follows this session.

## Still open (Part 2)

- **Content-safety gate for the breadth engine** — ~~founder decision needed on approach~~ **DECIDED +
  SHADOW-BUILT same evening (Part 4/5 continuation):** a critical-distance floor, author-keyed rather than
  subject-keyed (`core/content_risk.py`, wired into `book_selection.record_pick()`). See AWAITING_EVIDENCE.md.
- **`activity_memory.py`'s `derived_from` shape** — guarded against (documented), not fixed. Would need a
  consumer audit first.
- **`memory_multiway_linking.md`'s M2 gate** — still pending the founder-read of a week of M1 data; now
  fed by 8 more sources than before tonight, which should make that eventual read more representative.
- **`emotion_construction.py`'s 0.7% agreement finding** — surfaced, not investigated; the natural next
  session's subject (founder asked to move to an emotions discussion next).
- **Grand Work/dream `close_reason`-style categorical verdicts** — flagged in comments as a real richer
  signal `log_co_recall`'s API doesn't have a clean path for yet; not built.
