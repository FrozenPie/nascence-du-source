# J-3288: do a study note's key_facts appear in the passage? (D-0631 review, path P11)

Read-only analysis, 2026-11-07. No Du code changed. Data and scripts: `docs/lab/J-3288_data/`, `scripts/_lab_J3288_*.py`, test `scripts/_test_J-3288_study_fact_check.py`.

## Answer in four lines

1. **Parametric knowledge filed as his reading is rare: about 2 of 427 key_facts (0.5 percent), both extrapolations from a sentence the prompt cut off.** I did not find a single fact that is a clean piece of outside world knowledge pasted in.
2. **A different failure is five times commoner: 10 of 427 key_facts (2.3 percent, in 8 of 60 notes) misstate what the passage says** (a date moved to the wrong event, a death given to the wrong bride, a town's capture given to the fort). The words are in the passage; the binding is wrong.
3. **The writer never saw most of what the note claims to cover.** All 60 notes pre-date D-0577 (no `chars:` in any frontmatter, no `data/study_note_chunking_log.jsonl`), so `compose_note` sent `passage[:5000]` of sessions whose median length is 29,336 characters (min 11,194, max 80,697): median 17 percent of the session. The frontmatter still says "sittings: N" for the whole session.
4. **A deterministic "key-fact words must occur in the passage" check is not worth building.** Word-coverage flags a third of all facts to catch 6 of the 10 real problems; the sharper number-and-name check flags 6 facts and catches 1 of 10, because the errors are mis-bindings of words that do occur.

## Method

* **Sample.** The 400 newest `origin='study', source_type='study_note'` fragments with an encounter_id (30 Oct to 5 Nov). 47 had no note file left, 1 was a revision, 1 had no recoverable source: 351 usable. Every 5th, giving 60 notes (14 books; 40 of them the Napoleon memoirs collection, 6 War and Peace), 427 key_facts. Script `_lab_J3288_build_sample.py`.
* **Source passage.** The note fragment's encounter_id is its first sitting; the reading fragments (`origin='reading'`, same book, timestamp from that sitting to the note) are concatenated for the number of sittings in the frontmatter. `passage_seen` is the first 5,000 characters, which is what `compose_note` sent (`core/study_note.py` line 192 in the worktree, `[:5000]`). Notes with `revised` were excluded (their facts can come from the earlier note).
* **Three instruments, then a reader.**
  1. Deterministic (`_lab_J3288_classify.py`): content-stem coverage inside a 3-sentence window, plus number/name check.
  2. Cross-family judge: the notes were written by qwen3.5:9b (Qwen); the judge is gemma4:12b (Google) on the local CPU hub :11439, one call per note (passage plus all its facts), temperature 0, labels P (stated), R (restated or follows), A (not in the passage). 60 calls, 0 errors. No Ramses call was made.
  3. Hand reading (me): every fact the judge called A (31); every fact the lexical rule called absent that the judge passed (read at sentence level, about 35 regex-checked against the passage); a seeded random 34 of the facts both instruments passed. 180 facts hand-labelled (`hand_labels.json`, reasons in `hand_label_notes.json`).

## Results

| Instrument | Result |
|---|---|
| Lexical rule (window cov under 0.5, or a number/name missing) | calls 135 of 427 (32 percent) absent; on the hand-read set 129 of those are false alarms. A paraphrase changes the words, so coverage cannot separate "reworded" from "invented" |
| gemma4:12b judge | P 291 (68 percent), R 105 (25 percent), A 31 (7.3 percent); 26 of 60 notes have at least one A, 1 note has half or more |
| Hand reading of the 31 judge-A | 10 are real problems, 21 are grounded: the judge's A is a 32 percent-precise alarm |
| Hand reading of 149 facts the judge passed (115 lexical-absent plus 34 random) | 0 problems found (the one apparent hit, "Charles II died in 1700", is arithmetic on the passage: Bayonne 1706, "six years after the death of Charles II"). All 10 problems sit in the judge-A set, so the judge looks high-recall, but 34 random of ~247 unread passes is a small check, not a proof |

The 10 problems (reasons in `hand_label_notes.json`): 1.10 May 1802 for May 1801; 1.7 royal table dated 1801 (it was the 1799 Berlin mission); 7.5 invented cause for the diagonal swim; 16.1 and 16.2 extrapolated from a chapter whose visible text stops at "when you first hear t"; 25.1 the 1689 death given to the second bride; 40.1 married Maria Amelia (he married her sister Maria Louisa); 41.0 the fort "held out until 21 May" (the town was carried that day); 49.3 the Customs Director's role inverted; 58.3 "Luneville concluded 1 January 1802" (a wrong merge).

**Reading the rates.** Problems: 10 of 427 = 2.3 percent of facts, floor (only the 31 judge-A and 149 passes were read; the 247 unread passes carry a small residual). Of those, the ones whose content is not in the passage at all (16.1, 16.2, and 7.5's cause) are about 0.5 to 0.7 percent; the other seven are in-passage mis-bindings. Notes affected: 8 of 60 (13 percent).

**Caveats.** (a) One reader, one judge model: the hand labels are not independent of me. (b) `related_text` (the pre-D-0592 book-level walk, three items of 220 characters) was also in the prompt and is not reconstructed; a fact from it would count as a problem here. (c) The sample is two-thirds one author's memoirs; the model knows Napoleon, which makes this a high-risk book for leakage, and the rate is still low. (d) The book texts are probably in the model's training data, so "in the passage" and "also known to the model" cannot be separated; the test is only whether the passage supports the claim.

## Is a deterministic check worth building?

Tested against the 180 hand-labelled facts (10 problems), flag = "ungrounded":

| Check | Flags | Caught of 10 | False alarms |
|---|---|---|---|
| Lexical absent (window cov under 0.5 or number/name missing) | 135 | 6 | 129 |
| Stem coverage of whole passage under 0.7 | 64 | 3 | 61 |
| Stem coverage under 0.8 | 105 | 5 | 100 |
| Number/name must occur in the passage (accent, honorific, spelled-number and ethnonym folding) | 6 | 1 | 5 (two OCR splits, two "Napoleon" for "the Emperor", one arithmetic year) |
| gemma judge A | 31 | 10 | 21 |

**No.** The errors that exist are re-bindings of words that are in the passage, so any "word occurs" test passes them; the number check caught the one case where the model wrote a year that is nowhere near the right sentence. A check that fires on a third of facts or on 1.4 percent while catching 10 to 60 percent is not a gate. What does work as an audit is a cross-family judge plus a human read (judge A to hand-confirm), which is a periodic job, not a per-write gate, and the label "My own study note (my work, about the world)" is accurate for about 97 percent of facts. The fix that matters is upstream: D-0577 chunking (built, merged, restart-gated) makes the writer see the whole session; this audit should be re-run on post-restart notes (spawned job).

## What was not done

Not run: a second judge family (falcon3 :11440) for agreement (CPU hub, ~90 minutes per pass); `essay_lesson.py`, the other file in P11 (spawned as a job); the 247 unread judge-P/R facts beyond the 34 sampled.
