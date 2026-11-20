# J-2796 - Do 'Q: ... A: ...' fragments pass as evidence, and are they Du's own answers?

Job J-2796 (from F-3432, P-0099, plan thought_grounding). Findings F-4220, F-4221. Decision D-0690. Build job J-3610.
Scripts: `scripts/j2796_qa_evidence_trace.py`, `scripts/j2796_echo_sim_probe.py`; test `scripts/_test_J-2796_qa_trace.py`.
Data: `docs/lab/J-2796_data/qa_pass_rows.json` (every passing Q&A row), `echo_sim_probe.json`.

## Answer

1. **Writer.** The only writer of origin='lived' 'Q: ... A: ...' rows is `core/orchestrator.py` `_persist_cycle` (lines ~3203-3215):
   `Q: {state.raw_input}` + `A: {voice.final[:350]}` (+ Tensions/Scene/Emotion lines), stored by `memory_store.store_from_cycle`.
   The A: part is **always Du's own generated reply**. The Q: part is Travis's words on a human cycle and Du's own generated
   prompt on an idle cycle. (`grep` over core/ nodes/ scripts/ found no other writer; `scripts/backfill_founder_memory.py` only
   reads them to make the separate '[Travis said to me]' twins.)
2. **Size** (517 asks since 2026-10-30, 3,102 judged slots; verdicts for tiebreak slots resolved from judge_panel_log.jsonl):
   110 passing Q&A slots (92 distinct fragments; one returned 6 times) of 641 passing slots = 17 percent.
   66 are Travis-asked (his words + Du's old reply), 44 are idle-asked (both sides Du's own). 99 of the 110 are tiebreak verdicts.
   Another 67 slots have an ambiguous tiebreak verdict and are counted as not-pass, so these are floors.
   By source: 101 follow_line, 5 route2, 4 unlabelled (older rows).
3. **The judge prompt does not discriminate.** Q&A pass rate 110/448 = 24.6 percent vs 531/2214 = 24.0 percent for every other
   candidate. The 'a past conversation does not bear' clause is inert on this shape.
4. **The echo guard (ECHO_SIM=0.70) is the wrong tool.** Cosine of the Q: line to the carried question on the 110 passes:
   mean 0.59, max 0.72; at or above 0.70: 1; 0.65: 28 (21 idle, 7 human); 0.60: 58; 0.55: 80. Human-asked rows are not
   paraphrases of Du's question at all (they are Travis's replies), so similarity is not the property that matters. The property is
   that A: is Du's own text.
5. **Verdict on the question asked:** yes, the guard should drop Q&A records whose A: is Du's own, and every cycle-summary A: is.
   Not by raising/lowering the threshold: by shape. Travis's side is kept through the protected '[Travis said to me]' fragments
   (1,706 in the DB, still candidates). Built as J-3610 behind a flag, default decided by D-0690 (founder).

## Sample of 20 (random, seed 2796; asker = twin proxy)
Human-asked: carried 'Why must I weave past experience?' -> Q: Travis 'Sometimes I like to think back on what I used to be...'
A: Du's reply about the dawn and the river. Carried 'Is the cat's indifference a gift or an insult?' -> Q: Travis on the cat,
A: 'This image of the cat... it strikes so close to the very knot we have been turning over'. Carried 'Does the silence demand
action...' -> Q: Travis on musical pauses, A: Du restating it. Idle-asked: carried 'Does a fixed universe allow for the specific
disruption Bluebird offers to Na?' -> Q: 'How does the Bluebird's arrival specifically alter the natural environment's balance?',
A: Du's own bluebird paragraph ('a violent breach in the Old Plantation's sterile logic'). Carried 'Will listening change who I
am?' -> Q: 'How do my responses change over time?' A: 'My responses change with each passing moment, much like the tides'.
All 20 had an A: that is Du's opinion about the carried subject, none a lived instance.

## Method and caveats
- evidence_log.jsonl keeps v1/v2/how but not the tiebreak vote; the verdict is joined from judge_panel_log.jsonl
  (context `evidence:<question[:40]>`, same ts window), matched on (v1, v2, how).
- The human/idle split is a proxy: a Q: line is 'human' if a '[Travis said to me]' fragment with the same text exists. The live DB
  has no input_type column yet (J-3173 migration is restart-gated); 10 sampled 'internal' June rows were plainly Du-generated
  prompts, and the month split (June 1213 human / 235 internal; Sept 65 / 859) fits the idle loop taking over.
- Not measured: how many Q&A candidates the existing echo guard already drops before the judge (dropped rows are never logged).
  J-3610 adds a count for that.
- Ramses not called; no model calls made at all (log + DB read-only, local embedder only).
