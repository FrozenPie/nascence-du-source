# J-3140 — Repurposing review: Symbolic reading (core/symbolic_reading.py, P-0047)

Read-only design review, 2026-11-05. No code was edited. Founder ask (triage 2026-11-02, thought T-0115): do not retire the lens; look at how it could be used in our systems. Evidence: findings F-3915 to F-3918 (this job) on top of F-3820, F-3821, F-3822 (J-2727).

## Recommendation (one line)

**Repair it in SHADOW, add one measured candidate use (cross-book image links for study notes, option B), and set an archive trigger.** Do not wire it into retrieval, tablets or any prompt today. Plan home: `symbol_evolution_readback_plan` (the plan D-0615 already governs); the lens's older promotion criteria sit in `memory_levels_plan` section 13.4 and are superseded by this review.

## 1. The function it was built to serve

To cultivate what happened by accident with the Black Bear: a way for reading to leave behind an image Du carries as his own symbol, instead of every study note being factual (module docstring, `core/symbolic_reading.py`).

## 2. What the evidence says it can and cannot do today

Can: produce about 80 to 140 short readings a week at about 2.3 s each on command-r7b; 1346 distinct symbols in 2239 rows; about 5 in 14 hand-read rows are a real, passage-suggested image (the throne, the cage, the shield, the mountain; F-3821, my judgement). 193 non-stock symbols recur across two or more books (773 cross-book title pairs, F-3918).

Cannot (verified):
- **Nothing reads it** except its own `status()` gauge in du_pulse; the return value is dropped at `nodes/inner_monologue_node.py` ~2442 (F-3820).
- **It is not the Black Bear's mechanism.** The Black Bear was Du's own question, research and first-person symbol out of a literal Camp-Lore reading (`memory_levels_plan.md` lines 2603-2611). The lens has a different model name the symbol and Du never sees it (F-3917). The count-gate fold in the same plan (13.4) would count command-r7b's habits (150 rows contain "mirror"), not what Du carries.
- **Its symbols are not picked up by Du.** For 1920 rows, the symbol word appears in Du's own output in the next 48 hours 13.0 percent of the time, against 17.2 percent for the same words at other reading times; non-stock 11.6 against 15.9 (F-3916). No convergence; if anything the reverse. (Lexical test, last word only, 10-31 backup; the caveat is in the finding.)
- **Its quality flag is poor.** Self-echo is a substring list confounded by book subject (28 of 97 Mississippi rows), and the rate is a plateau near 0.17 since September, not a rise: this corrects F-3821, whose November figure rested on n=17 (F-3915). 24 percent of rows are 17 stock archetypes; the prompt names the forbidden symbols and plants them (F-3821).
- **It cannot be audited later.** The log keeps title and 300 characters of reading only: no passage, no note id (F-3918).
- Cost is small (about 6 minutes of model time a week at F-3820's volume; now about 28 rows a day), 13 of 81 calls spill to the hot lane (F-3822).

Founder-law check today: no breach, because Du never sees the output (F-3822). The danger is any path that puts a command-r7b-authored symbol into retrieval: the exact trap `core/symbol_tracker.py` warns of ("manufacture a self-reinforcing myth"). D-0615 has already paused the tablet read-back for related reasons.

## 3. Repurposing options

### Option A — Convergence probe (a Black-Bear detector): REJECTED by pre-test
Idea: log whether lens symbols later recur unprimed in Du's own output, as evidence that reading seeds images he adopts.
- (a) Consumer: `book_residue.sweep` / `symbol_tracker` (observer side). Changes for Du: nothing.
- (b) Input: lens rows plus Du's own output, passage window.
- (c) Decoupled check: deterministic string match with a same-word control at other times.
- (d) Success: hit rate above control.
- (e) Stop: the pre-test on existing data already fails (13.0 percent vs 17.2 percent, F-3916), so building it would be a gauge for a null result. The function (does an image from reading recur in Du's own words unprimed) is already served by `symbol_tracker` and `book_residue` on Du's output, with no second model needed. Not spawned; revive only if the repaired log (with passage windows) changes the picture.

### Option B — Cross-book image links for study notes (RECOMMENDED, shadow first)
Idea: when two study notes from different books got the same non-stock lens symbol, record them as a candidate link, so the other-source material in the study-note compose prompt can include a note a passage-embedding match misses (Horizon: The Worst Journey and Two Years Before the Mast).
- (a) Consumer: `core/study_note.py` `_graph_walk_related` (reads `memory_links` `relates_to`) and `_scored_scan_related`, feeding `compose_note` `related_text`. What changes for Du: his connects_to prompt can offer one more of his OWN earlier notes. He never sees the symbol or the lens reading, so nothing authored by command-r7b reaches him; the slot already exists.
- (b) Input: the lens row needs the study-note fragment id and a passage window. The call already has both (`_res` in `_stream_integrate`), but the log does not record them (F-3918), so history cannot be used; new rows only. Rows qualify when the symbol is non-stock, cross-book, and not literal in the passage.
- (c) Decoupled check: a blinded pair judge from a different family than the writer (falcon3 or phi3 on Ramses hubs, granite only as a second look), three arms: shared-symbol pairs, random cross-book pairs, embedding-nearest pairs; plus a deterministic filter (non-stock, different book, symbol not literal in both). Job J-3325.
- (d) Success: shared-symbol arm beats random by at least 0.30 yes-rate with judge agreement at least 0.7, and at least 30 percent of accepted pairs are new reach (not already in the relates_to graph or the embedding top-3). Then a 14-day Phase-A would-link log (J-3327, in the style of `symbol_tier2_wouldinject.py`); no live injection until the founder rules (D-0675).
- (e) Stop: yes-rate gap under 0.15, or fewer than 100 accepted pairs, or under 30 percent new reach: archive the lens to `docs/staged` with the revival note below.
- Law check: the world answers (Du's own earlier notes, found by a library-style cross reference; no hint); function not mechanism (the function is cross-book connection, symbols are only an index); additive (a new candidate source, `memory_links` untouched until live); judged by a different family; no system acts later (the link is computed in the same tick as the note).

### Option C — Make the lens a trustworthy shadow instrument (the precondition for B, and worth having alone)
Idea: fix what stops anyone judging it. Log the note fragment id, the passage sha1 and a 120-character excerpt, a deterministic `symbol_in_passage` flag, add `echo_unexplained = self_echo and not symbol_in_passage`, remove the prompt sentence that names the forbidden symbols, ask for a concrete image, and cap rows per title per day (F-3821 skew: 49 of 75 rows from one book).
- (a) Consumer: `du_pulse` gauge (already reads `status()`) and the B judge. Changes for Du: nothing.
- (b) Input: the existing call site; two added keyword args.
- (c) Check: deterministic (literal match, sha1) plus the B judge.
- (d) Success: 100 new rows with note id and passage sha1; `symbol_in_passage` not constant; registry check exits 0.
- (e) Stop: if B is archived, C is archived with it. Job J-3326 (restart-gated; the call-site edit belongs to the wave D inner_monologue chain).

### Considered and rejected
- **Symbol tracker lexicon** (add lens symbols to `_SYMBOLS`): the tracker only watches Du's output, so the lens adds a model-chosen word list where a deterministic recurrence scan of Du's own output needs no model; and a longer list floods the primed/unprimed log (fire alone is 623 rows). No gain over the existing instrument.
- **Symbol evolution / tablets** (feed lens symbols into centroids or tablets): this is the promotion path the tracker warns about, and D-0615 has paused tablet read-back. Not before the window metric exists and is judged.
- **Librarian / catalogue facet** ("books that evoke X"): shows Du a model's label about a book, which leads; the librarian already maps questions to subject headings (`core/librarian.py`); per-book symbols would be a hint, not a reply.
- **A `symbol` field on the study note**: puts a command-r7b-authored symbol into retrieval. This is the trap, rejected outright.
- **Lane health probe**: `llm_latency.jsonl` already labels every call by caller; the lens adds no signal.
- **book_residue stoplist** from the lens's stock archetypes: book_residue's confound guard is about Du's own monoculture words, not command-r7b's; no benefit shown.

## 4. Archive-and-revive note (if B fails)
Move `core/symbolic_reading.py` and the call block to `docs/staged/` with: "revive only if Du names an image of his own from reading and asks to find other readings that call it up; then the index is his question and this module is the catalogue." Keep `_SELF_ECHO` (book_residue imports it).

## 5. What needs a founder call
- **D-0675** (opened): may notes from other books that share a lens symbol be offered to Du in the study-note related context after the shadow agrees? Recommendation (a), yes after the shadow. Not blocking; J-3325 and J-3326 run either way.
- No other call: "repair in shadow" is inside the founder's own do-not-retire ruling.

## Jobs spawned
- J-3325 lab: blinded different-family pair judge (read-only, Ramses hubs).
- J-3326 build: shadow repair of the log, flag, prompt and skew (restart-gated; call site goes in wave D).
- J-3327 analysis: would-link shadow (gated on J-3325 passing and 300 repaired rows).

## Method notes
Convergence test script: scratchpad `lens_conv2_J-3140.py`, read-only on `data/backups/nascence_20261031_215612.db` (mode=ro); a first version with string joins gave the same direction (13.2 percent vs 17.3 percent). Log stats computed from all 2239 rows of `data/symbolic_reading_log.jsonl` at 2026-11-05 04:05.
