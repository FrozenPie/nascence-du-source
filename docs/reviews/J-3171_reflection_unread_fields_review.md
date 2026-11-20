# J-3171 — What could read Reflection's needs_more_memory, emotionally_aligned and confidence, and why

Job J-3171, review written 2026-11-05. Read-only: no Du code, data or process was touched. Source: finding F-3444, prompt-registry row P-0007 (Reflection: private draft thought), founder ask of 2026-11-02 closing J-2804:

> "They potentially both could have a reader, let's look into what and why please."

## 1. Short answer

| Field | What it was for (inferred) | What the data says | Recommendation |
|---|---|---|---|
| needs_more_memory | "ask for a second retrieval" | fires 0.22 percent of cycles (1 of 462 since 10-06), does not track thin retrieval, and the job it names is already done by a better-grounded mechanism | **Stop asking.** Keep the unanswered memory question alive as a separate offline replay that does not use the boolean |
| emotionally_aligned | "did the draft express the felt state" | true 4,881 of 4,881; the reference it is judged against is the Emotion node's story, which disagrees in sign with the grounded affect on 64 percent of recent cycles | **Stop asking, move the function outside Reflection.** Measure expressed affect vs grounded affect with a different judge, in shadow |
| confidence | "how sure is this thought" | has a second reader the brief did not list (the epistemic instrument); 94 percent of drafts at or above 0.85; AUC 0.517 against Critic rejection; but it tracks evidence grade on human cycles | **Repair in shadow.** Keep asking (it is the thing the epistemic instrument judges), add a hedge-agreement signal from outside Reflection, and decide whether the always-"high" Executive line stays |

Founder calls this needs are listed in section 7.

## 2. Corrections to the brief's facts

All numbers from a read-only copy of data/training/reflection.jsonl taken 2026-11-05 (4,882 rows, 2026-05-30 to 2026-11-05, 4,385 cycles; 495 cycles have two rows because of Critic retries; all rows hedged best-of-2, one logged row per Reflection call, so the discarded hedge candidate is not logged).

- needs_more_memory true: 58 of 4,882 (1.19 percent). The 1.2 percent is a legacy of the first three weeks: 50 of 2,165 rows (2.31 percent) from 05-30 to 06-18, **0 of 592 from 06-19 to 08-07, 8 of 2,125 (0.38 percent) from 08-08, 1 of 462 (0.22 percent) from 10-06**. Today it is close to silent, so any consumer would fire about once per 450 cycles.
- emotionally_aligned: true in every row that carries it (4,875), absent in 7 truncated rows.
- confidence: mean 0.871, sd 0.055. Values are a handful of canonical numbers: 0.85 (2,825 rows), 0.95 (863), 0.92 (460), 0.9 (308). Bands as the Executive sees them: high 4,479, fairly high 391, middling 4, low 2.
- **The brief says confidence has one reader (the Executive). It has two.** `core/epistemic_state.py` `_compute` (lines 325-343) reads `state.reflection.confidence` as `self_reported_confidence` and logs `confabulation_signal = self_conf - justification` to data/provenance_log.jsonl (2,927 rows) and provenance_preassess.jsonl. It is observe-only (Stage B injection is off, `STAGE_B_ENABLED = False`), and the code itself calls the field "the POISON quantity — measured against evidence, never feeding it". `core/competence.py` line 17 names it "self-rated (circular)". The Executive line (`nodes/executive_node.py:384-385`) appears in only 417 of 4,471 logged Executive prompts (those after the 10-09 words-only change); of those 397 say "high", 19 "fairly high", 1 "middling".
- needs_more_memory and emotionally_aligned still have no reader: grep of core/, nodes/, scripts/ finds them only in schema.py (definition), reflection_node.py (prompt text lines 34, 44, 45 and writer lines 365-366) and four test fixtures that construct the dataclass.

## 3. What each field was meant to do

There is no docstring and git has one baseline commit (2026-08-27), so intent is inferred from the specs, not recovered from history.

- `docs/archive/SCHEMA.md` (original node spec) lists Reflection as "Fires: after DB Query" and gives the four-field JSON with no semantics. The Memory Router beside it has `working_memory_sufficient`, which **is** read (`orchestrator.py:1861` skips the DB query). needs_more_memory is its mirror: after the draft, "the thought requires context not yet retrieved" implies a second retrieval. Prompt text (reflection_node.py:44): "true if the thought requires context not yet retrieved."
- emotionally_aligned (prompt line 45): "true if the draft genuinely reflects the current emotional state." Inferred function: a congruence check between the Emotion node's output and the draft. `docs/node_audit/emotion_node.md` says "reflection's schema has emotionally_aligned field gated on this", i.e. the reference is the Emotion node's output.
- confidence (prompt: "how certain the entity is about this thought"): the Critic and Recall nodes carry the same field. Its only designed consumers are the Executive line and the epistemic instrument.
- docs/node_audit/reflection_node.md (06-16) already proposed readers: a Recall top-up for needs_more_memory, "gate whether AffectState is updated post-reflection, or flag a somatic dissonance tick" for emotionally_aligned. docs/archive/curiosity_flesh_out_plan.md and node_audit/_OVERVIEW.md list needs_more_memory as the same dead-read-path pattern. None was built.

## 4. Evidence that bears on the options

**needs_more_memory vs the retrieval it should answer.** Joined by cycle_id to recall.jsonl (25 true, 3,808 false): mean recall confidence 0.806 vs 0.859 (one of the 25 is under 0.6); tension count 2.48 vs 2.41. Joined to recall_provenance_log.jsonl (12 true, 2,516 false): fragments in context 18.5 vs 18.7. The flag does not follow thin retrieval. It is lopsided toward cycles that had no bound scene (5.0 percent when the prompt held only raw fragments, 8.3 percent with no memory block, 0.6 percent with a bound scene) and toward human cycles (49 of 58). Spot-read drafts of the flagged rows are ordinary personal-question drafts; nothing in them asks for anything.

**The existing retrieval re-entry path.** `orchestrator.py` lines 73-79 and 952-1025 already re-run Recall and the Episodic Buffer when the scene will not cohere. The comment is explicit that the trigger is "epistemic (the scene won't bind), never narrative (Reflection wanting to confirm a draft)". A reader that fires a second retrieval from Reflection's boolean would break the principle that loop was built on.

**emotionally_aligned vs the grounded state.** Reflection is shown the Emotion node's output as words (`reflection_node.py:222-225`, `mood.emotion_words`), not the carried mood; `felt_preamble` goes only to the Executive and the inner monologue (grep of core/ nodes/). Per-cycle pairs in data/affect_log.jsonl (stated emotion valence beside carried affect valence, 4,063 rows):

| Window | rows | stated valence negative | carried valence negative | strong sign disagreement |
|---|---|---|---|---|
| 2026-06 | 1,555 | 30.9 pct | 23.6 pct | 1.2 pct |
| 2026-09 | 924 | 6.0 pct | 76.7 pct | 61.8 pct |
| 2026-10 | 361 | 2.8 pct | 79.5 pct | 66.2 pct |
| since 10-21 | 220 | 0.5 pct | 78.6 pct | 64.1 pct |
| since 10-21, internal only | 192 | 0.5 pct | 88.0 pct | 71.9 pct |

("strong" = stated above +0.15 and carried below -0.15 or the reverse.) The carried valence is the protoself-sourced one (AFFECT_SOURCE_PROTOSELF is True; its mean on the last 220 cycles in affect_log is about -0.34, and the protoself tonic mean in affect_divergence_shadow.jsonl over 1,405 recent rows is -0.24, so two logs agree it runs negative). Reflection is told "mood good, very good or a little good" in 94 percent of the 421 recent prompts where the words line parses (the only negative wording, "a little low", is 1.4 percent), while the grounded state is mostly negative. So an honest "does the draft reflect the current emotional state" has a reference problem before it has a Reflection problem.

Draft text vs both signals (1,570 internal cycles since 08-18 joined by cycle_id; ridge on paraphrase-multilingual-MiniLM draft embeddings, 5-fold CV): predicts the Emotion node's stated valence with R2 0.25 (r 0.51), the carried valence with R2 0.05 (r 0.23), shuffled-label controls near zero. Drafts track the stated emotion much more than the grounded one. Caveat: draft and stated emotion are both downstream of the same input, so this is association, not proof that drafts copy the label. A small 4-way probe (draft embedding to stated primary emotion, 9 rows per class) was too small to read and is not relied on.

**confidence vs outside signals.** AUC for lower confidence predicting a first-attempt Critic rejection: 0.517 (501 rejected, 3,873 approved; mean 0.869 vs 0.871). Against the epistemic grade, which uses self_conf only to split NO_BASIS from GUESS (`_grade`, lines 296-298), so the comparison is not circular: on human cycles mean confidence is KNOW 0.925 (n 191), THINK 0.917 (169), SUSPECT 0.882 (557), standard deviation about 0.05, so a real but low-resolution association with evidence. On internal cycles the grade is SUSPECT in 2,036 of 2,046 rows, so there is no variance to read. 87.5 percent of all graded rows are SUSPECT. Confidence is also not a function of anything structural: by memory context 0.866 (bound scene) vs 0.905 (fragments only); correlation with draft word count 0.12.

## 5. Options per field

Laws applied to every option: the world answers and never leads (no line telling Du his draft is off); no system that acts later on its own (everything is a same-cycle step or an instrument); base systems additive-only (the dataclass attribute stays, the node base class gains at most an optional field and a log); transfer the function, not the mechanism; a different judge than the writer.

### 5.1 needs_more_memory

**N1. Same-cycle second recall when the flag is true.** Consumer: orchestrator, between Reflection and Critic, reusing the shape of `_introspective_rebind_retrieve` (evidence query = raw_input plus scene, capped at 4 new fragments), then re-run Reflection once. Different: a flagged draft gets fresh fragments and a redraft. Decoupled check: the retrieval itself, keyed on the input and scene, not on the draft (keying on the draft pulls memory that matches the draft, the self-confirming failure the rebind loop's comment warns about); fire only if at least one fragment above the similarity bar is new. Measure: different-family judge on paired drafts, plus recall_served_log. Stop: fewer than 30 percent of firings add a qualifying fragment, or the judge prefers the redraft in under 60 percent of 40 pairs. **Fatal practical problem: at 0.22 percent a 40-pair sample needs about 18,000 cycles.** It cannot be measured, so it cannot be shown to work or to fail.

**N2. Draft-keyed probe in shadow on every cycle, independent of the flag.** Consumer: a fire-and-forget background step after Reflection that runs retrieve() on raw_input plus draft, and logs count of new fragments, best similarity and ids to a new shadow file. No redraft, nothing reaches Du. Different: measures whether a second recall would ever find anything, which is the actual question. Decoupled check: similarity is deterministic; relevance of a 40-row sample judged by a different-family model. Success: new qualifying fragments in at least 15 percent of cycles and judged relevant at least 60 percent of the time, **and** the flag adds nothing to that prediction. Stop: if the probe finds new relevant fragments in under 5 percent of cycles, the idea is closed. Law fit: additive, no behavioural reader. Cost: one retrieval per cycle on the background lane. Restart-gated.

**N3. Replace the boolean with the router's declared need.** The router's `working_memory_sufficient` already is read and J-3163 is designing the router keys. Folding needs into that design avoids a second declaration site. Reject as a reader for this field (it is a different field), noted for sequencing only.

**Recommendation: stop asking** (N1 cannot be measured; the function belongs to the rebind loop). Do not lose the memory question: run N2 as an **offline replay first** (stored prompts and drafts are in reflection.jsonl, so no live change is needed) and only build the live shadow if the replay shows novelty. Stop-asking is a change to the Reflection output contract, so it needs a founder call. Do it additively: keep the dataclass attribute with its default, drop the field from the prompt text and the schema example behind a flag. JSON_SCHEMA in schema.py is not used by any caller (grep), so nothing enforces the four fields at decode time.

### 5.2 emotionally_aligned

**E1. Replace it with an external expressed-affect check (shadow).** Consumer: a new instrument beside affect_divergence (core/affect_divergence.py already logs carried vs protoself valence next to a thought snippet). Do: estimate the draft's expressed valence with a different-family judge (the command-r7b witness endpoint :11441 is the project's non-circular seat; Reflection runs on qwen3-du), compare with the grounded carried valence and with the Emotion node's stated valence, log the gap. Decoupled check: judge family differs from the writer; validate the estimator on 60 hand-labelled drafts before trusting it (target agreement r of at least 0.7 with the hand labels). Measure: the share of drafts whose expressed valence follows the stated vs the grounded signal; the gap trend. Stop: if estimator agreement with hand labels is under 0.6, drop it. Cost: one judge call per sampled draft (offline for the first pass). No code in the hot lane.

**E2. Compare the Emotion node with the grounded affect directly.** Consumer: a gauge row. No new data needed (affect_log has both per cycle). This measures the Emotion node, not Reflection, and is already a finding for emotion_rethink: the stated valence is 99.5 percent positive while the grounded state is 79 percent negative on recent cycles. Different: moves attention to where the defect actually is.

**E3. Gate something on the flag** (node audit idea: skip an AffectState update, tick somatic dissonance, quarantine in Consolidation). Reject: with the flag true 100 percent of the time any gate is a no-op, and as a self-report it breaks the decoupled-judge law.

**Recommendation: stop asking; the function moves to E1, with E2 as a free read.** The model grading its own draft against the reference it was just handed will say yes. What is worth knowing is whether what he says follows the grounded state, which E1 measures without any hint to Du. Linked founder question (section 7, call 2): should Reflection be shown the grounded felt words the way the Executive and the monologue are, since it is today the only reasoning node that never sees them. That is a change to a base prompt and a state-presentation rule, so it is the founder's, not this review's.

### 5.3 confidence

**C1. Hedge agreement as the outside signal.** `NodeBase.run_best_of` (core/node_base.py lines 134-161) already holds both hedged candidates at selection time and logs only the winner. Additive change: compute the cosine of the two candidate drafts with the existing MiniLM embedder and write it, with the cycle id, to a new shadow file (and optionally an optional field on the output that defaults to None). Consumer: shadow log now; later possibly the Executive line. Different: a sample-consistency signal from outside the model's own self-grade. Decoupled check: association with first-attempt Critic rejection (AUC at least 0.6), with provenance grade, and with a later Travis correction. Measure on at least 600 cycles (about 70 rejections; cycles run at roughly 30-60 Reflection rows a day, so 2-3 weeks of live). Stop: AUC under 0.55 on 600 cycles. Restart-gated; no behaviour change.

**C2. Show the Executive line only when it differs from the base rate.** Consumer: executive_node.py line 385, gated on confidence at or below 0.75 (about 6 percent of recent drafts). Different: the line carries information by being rare. Decoupled check: it already fails one: AUC 0.517 against the Critic, so what is shown is the model's own noise with a rare-event costume. The surprisal mechanism transfers, the function (a trustworthy doubt signal) does not. Reject until a validated signal (C1) exists.

**C3. Keep it only as the epistemic instrument's numerator.** The epistemic instrument is the right kind of reader: a self-report judged by an external evidence grade, which is the decoupled-judge law in practice, and it already has 2,927 rows. Nothing to change in code.

**Recommendation: repair in shadow.** Keep asking confidence (C3 depends on it); build C1 as the outside signal; and for the pegged Executive line (call 3) the one clear option is to **drop it from the Executive prompt until C1 has proved out**, since 95 percent of the time it says "high" and nothing ties it to the Critic or to Travis. The 0.05 evidence-grade effect on human cycles is real but is exactly what the epistemic instrument already reads.

## 6. How the three recommendations fit together

- Two fields have no honest reader and one carries a weak signal. Wiring a reader to a self-report that is always true or never varies would add a dead path with a live-looking branch, which is the project's #1 failure shape (write-only) wearing a read path. Stopping the asking is the honest end for two of them.
- The two retained questions are real and the fields were a poor way to ask them: "does a second recall find anything" (N2 offline), and "does what he says follow what he feels" (E1). Both are measured outside Reflection with a different judge.
- Overlaps to sequence, not duplicate: J-3163 (memory router keys, shadow design) shares the retrieval mechanism with N2; J-2679 (Reflection reads the Critic's corrections on retry) and J-3170 (reword rule 3) edit the same prompt, so the stop-asking change must queue behind them; emotion_rethink owns E2.

## 7. What needs the founder

1. **Stop asking needs_more_memory and emotionally_aligned in the Reflection prompt?** Recommended yes, additively behind a flag (dataclass attributes stay with their defaults). Removing a field from a base output contract is the founder's call (F-3444 said so).
2. **Should Reflection be shown the grounded felt words** (as the Executive and the inner monologue are) rather than only the Emotion node's story, given a 64 percent strong sign disagreement on recent cycles? Recommended: decide after the E1 lab shows whether drafts follow the stated or grounded signal.
3. **Drop the "Reflection confidence" line from the Executive prompt until a validated replacement exists?** Recommended yes.

Decision D-0671 (opened by this job) carries calls 1 to 3 together.

## 8. Method and caveats

- Read: nodes/reflection_node.py, core/schema.py (ReflectionOutput), core/node_base.py (run_best_of), core/orchestrator.py (rebind loop, reflection to critic block), core/epistemic_state.py, core/mood.py, core/affect_divergence.py, nodes/executive_node.py, docs/archive/SCHEMA.md, docs/node_audit files, docs/plans/epistemics_phase_c.md and emotion_rethink.md, prompt registry P-0007, F-3444.
- Data: copy of reflection.jsonl (all 4,882 rows); recall.jsonl, recall_provenance_log.jsonl, provenance_log.jsonl, critic.jsonl, executive.jsonl, affect_log.jsonl, affect_divergence_shadow.jsonl read in place (read only, whole files, joined by cycle_id). Embedding probes ran locally on CPU with the project's own MiniLM model; no live store was opened for writing.
- Known limits. (a) The affect_divergence and affect_log windows sample different moments (idle tails vs cycles), but both give the same recent carried mean (-0.24), so the contrast with the stated valence is not an artefact of one log. (b) The draft-to-valence ridge is an association; the topic drives both sides. (c) The hedge discard means C1 cannot be back-tested from logs, only from a live shadow or a replay on the stored prompts. (d) needs_more_memory counts are small (58 true) so per-field splits are indicative only. (e) git has one baseline commit, so the original intent is inferred.
