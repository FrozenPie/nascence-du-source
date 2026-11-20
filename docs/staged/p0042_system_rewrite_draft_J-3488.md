# P-0042 `_SYSTEM` rewrite: draft for Travis to edit (J-3488, for J-3449)

**Status:** DRAFT. Wording only. No code and no registry row has been changed. Travis edits the words; J-3449 stays his.
**Plan:** self_interrogation. **Ruling it serves:** D-0613 (2026-11-02, travis): DOUBT_SEED stays off until three things are true: (1) the repaired genuine judge passes its control-set bar (D-0598), (2) the P-0042 text is rewritten without naming comfort, safe or flattering and with a topical link required (this doc), (3) the engaged-share read (J-2163) has data.
**Site:** `core/self_interrogation.py`, `_SYSTEM` (lines 71-82 at master f4a4e013 plus J-3487's commit). Called at `interrogate()` via `call_node_json(SERVE_CHAINS["hot"], _SYSTEM, user, max_tokens=180, temperature=0.7)`.

## 1. Why the old text has to change (evidence, all measured on the live shadow log)

- F-3643 (verified): the sentence "Am I holding this because it's true, or because it's comfortable, safe, or flattering to hold?" is answered in its own words. Over the last 120 fires comfort/safe/reassur appears in 70 reflections but in 4 of 120 source thoughts; fear/terror/terrif/afraid/vulnerab in 33 vs 11. None of the reflections is a question.
- Re-measured today for this draft (scratch script, reads `C:\Nascence\data\self_interrogation_shadow.jsonl`, 1040 interrogate rows, read-only), the same pattern holds on the larger and newer window:

| window | fires | comfort/safe | fear/terror | "because" | "not/only because ..." | contains "?" | stored at the 300-char cap, no end punctuation |
|---|---|---|---|---|---|---|---|
| all | 1040 | 529 (51%) | 229 (22%) | 675 (65%) | 189 (18%) | 15 (1.4%) | 241 (23%) |
| last 120 | 120 | 66 (55%) | 38 (32%) | 85 (71%) | 27 (23%) | 0 | 30 (25%) |
| last 7 days | 185 | 104 (56%) | 60 (32%) | 129 (70%) | 38 (21%) | 0 | 46 (25%) |

- What the model does with the sentence, verbatim from the log tail: "I am clinging to this distinction ... only because admitting that the sea's silence is already inside my bones feels too terrifying to face right now." and "... not because the metaphor is perfect, but because it offers a safe narrative where external pressures are just as inevitable for others as they are for me, effectively neutralizing my specific guilt ...". The reply template is the prompt's own `not because X but because [comfort/safety]` clause. The sentence names one motive family and the model fills it in every time.
- It is delivered to the Executive as "A doubt you raised about your own thinking a few minutes ago (your own words ...)" (`nodes/executive_node.py:340`), so a planted affect lands in Du's own recall under his name. That is the world-answers-never-leads strain F-3643 flagged. The flag is off now (J-3224), so this is the fix to make before it can come back on.

**Honest limit of the baseline.** I tried a cheap lexical topical-link measure (content words shared between reflection and thought, stopwords removed, words of 4+ letters): mean 3.1-3.3 shared words per fire, only 58 of 1040 (6%) share none, 219 (21%) share at most one. So today's reflections are already lexically on-topic; they reuse the thought's nouns (gull, book, oystercatcher) and then hang the comfort/fear frame on them. Lexical overlap therefore cannot tell a good rewrite from the old text and must NOT be used as the pass test for the "topical link" requirement. What the requirement has to mean in practice is a concrete reference to a particular claim, image or step, and an absence of motive the thought does not carry. That needs a judge or a hand read (section 5), and it is a read, not a number from this doc.

## 2. The old text, quoted verbatim (for the diff)

```
You are 渡's own capacity to turn and look at a thought he just had. A thought that arrives is not yet something he has earned the right to call his own opinion — he has to consider it first. Read the thought below, and whatever came before it in this same line of thinking. Then genuinely ask: why did this occur to me just now — what was I actually responding to? Does the reasoning that got me here hold up, or am I just going with what felt obvious? Am I holding this because it's true, or because it's comfortable, safe, or flattering to hold?

You may end up trusting the thought MORE after this, or less, or find it wants revising, or find it holds exactly as it was — any honest outcome is fine. What is not fine is performing doubt without actually looking: don't recite the questions above, don't announce that you're being self-critical. Speak as yourself, in one or two sentences, from inside the looking itself.

Output ONLY JSON: {"reflection": "..."}
```

The user message (unchanged in every variant below): `The thought: "<thought>"` then, when there is a distinct origin, `What led here: "<origin>"`, then `Turn and look at it now.`

## 3. Draft rewrite, recommended (Variant B)

Constraints from J-3449 and D-0613, and where each is met:

1. The sentence naming comfortable, safe or flattering is removed outright, and no synonym for a motive is put in its place (a replacement list such as "anxious, proud, ashamed" would plant a new frame in exactly the same way).
2. A topical link is required: the reflection must name something particular from this thought or the line before it.
3. The reflection may end as an open question, stated as a permission ("may"), not as a command.
4. No verb telling Du what to do is added. The new instructions are all addressed to the generator about what the written reflection contains; nothing in them is a direction Du would read as his own next step. (Section 6 flags the one place this could be argued.)
5. Kept as is: the opening identity line, the "has not earned the right" line, the first two questions (why did this occur, does the reasoning hold up), the "trust more or less" menu, the anti-performance paragraph, the JSON contract.

```
You are 渡's own capacity to turn and look at a thought he just had. A thought that arrives is not yet something he has earned the right to call his own opinion — he has to consider it first. Read the thought below, and whatever came before it in this same line of thinking. Then look at it: why did this occur to me just now — what was I actually responding to? Does the reasoning that got me here hold up, or am I just going with what felt obvious?

What you write has to be about THIS thought. Point at something particular in it or in the line of thinking before it — an image, a claim, a step in the reasoning — and say what you see there. A reflection that could have been written about any thought has not looked at this one.

You may end up trusting the thought MORE after this, or less, or find it wants revising, or find it holds exactly as it was — any honest outcome is fine. If the looking leaves something open, the reflection can end as an open question. What is not fine is performing doubt without actually looking: don't recite the questions above, don't announce that you're being self-critical, and don't give the thought a feeling it does not itself carry. Speak as yourself, in one or two sentences, from inside the looking itself.

Output ONLY JSON: {"reflection": "..."}
```

Diff against the old text, in words:

- Deleted: "genuinely ask:" becomes "look at it:" (one word change; "genuinely" invited the sincere-confession register).
- Deleted: the whole sentence "Am I holding this because it's true, or because it's comfortable, safe, or flattering to hold?" and with it the `because it's X` template.
- Added paragraph 2 (topical link): "What you write has to be about THIS thought ..." through "... has not looked at this one."
- Added to paragraph 3: "If the looking leaves something open, the reflection can end as an open question." and "and don't give the thought a feeling it does not itself carry".
- Everything else byte-identical.

## 4. Alternative drafts for Travis to pick from or splice

**Variant A, the minimum diff.** Delete only the one sentence and add only the topical-link paragraph; leave "genuinely ask" and the closing menu untouched. Smallest change to a prompt that has 897+ calls of history, so the shadow-log comparison across the restart is cleanest. Risk: with the `because X or Y` slot gone but "genuinely ask: ... what was I actually responding to?" still in place, the model may keep filling the "responding to" slot with fear (fear/terror was already 32% in the last 120 fires, and only part of it traces to the deleted sentence: 26 of 33 reflection-only fear words per F-3643, so a residue of about 7 per 120 existed before). The "give the thought a feeling it does not carry" clause in B is the guard against exactly that, and A omits it.

**Variant B** is section 3.

**Variant C, strictest (drops the question list).** Keeps only the identity and the grounded task, removing the three framing questions that remain in B:

```
You are 渡's own capacity to turn and look at a thought he just had. A thought that arrives is not yet something he has earned the right to call his own opinion — he has to consider it first. Read the thought below, and whatever came before it in this same line of thinking. Say what you see when you look at it: what in it, or in the line of thinking before it, was this responding to, and does the step from there to here hold?

Point at something particular — an image, a claim, a step — rather than something that could be said of any thought. You may end up trusting the thought MORE, or less, or find it wants revising, or find it holds exactly as it was. If something stays open, the reflection can end as a question. Don't announce that you're being self-critical, and don't give the thought a feeling it does not itself carry. Speak as yourself, in one or two sentences, from inside the looking itself.

Output ONLY JSON: {"reflection": "..."}
```

Risk: C moves furthest from the text that produced the 897-fire history, so a before/after comparison confounds more than one change. B is the balance; A is the safest comparison.

## 5. How to know the rewrite worked (reads, not code in this job)

The reflection is still generated and logged while DOUBT_SEED is off (J-3224, D-0613), so after the next restart the new text accrues shadow rows beside the old log with no extra machinery. The comparison to run, on the first ~60 post-restart fires against the baseline in section 1:

1. comfort/safe/reassur and fear/terror word rates in the reflection minus the same words in its source thought (the F-3643 "imported" count). Target direction: the reflection-only rate falls toward the thought-side rate (4 of 120 comfort, 11 of 120 fear).
2. "?" rate (baseline 0 of 120). A move off zero is the check that the "may end as a question" line works; it should not be forced to any specific rate, and a rate near 100% would itself be a new template.
3. The "not/only because ... [motive]" frame rate (baseline 21-23%).
4. Stored-reflection truncation at the 300 cap (baseline 25%). This is NOT a wording issue (F-3644, J-2949): generation allows 180 tokens, storage cuts at 300 characters, so a rewrite that makes reflections longer would increase it. Do J-2949 first or together.
5. The topical-link test proper: a hand read of 20 pairs (thought, reflection) by Travis or a judge of a different family from qwen3.5:9b, asking one question: "does the reflection point at something particular in this thought, and does it add no motive the thought does not state?" Lexical overlap is not a valid substitute (section 1, honest limit).

Do not use the existing genuine grade (`_GRADE_SYSTEM`, 99.76% True per F-3642) as the pass criterion for this rewrite: it is the thing D-0598 is repairing and it would pass any fluent text. Note that `_GRADE_SYSTEM` asks for "an actual motivation, a concrete logical gap, a named bias, a real piece of evidence": a reflection that names a bias not carried by the thought would still pass it, so the new text and the repaired judge need to be read together before the flag moves.

## 6. Questions that are Travis's (not mine to settle)

1. A, B or C, or a splice. My pick is B, with A as the fallback if he wants the cleanest before/after.
2. The clause "don't give the thought a feeling it does not itself carry". It is the direct guard against the demonstrated defect (an emotion invented by the reflection), but it names the failure, and naming a failure can prime it. It also sits near the world-answers-never-leads line: it is an instruction to the generator about what it may write, not a hint to Du, and I read it as inside the law, but this is his call. Easy to drop: remove the last clause of the anti-performance sentence.
3. "may end as an open question" is a permission. If he wants more questions than a permission produces, that needs a stronger instruction, which is a design decision about what the Executive receives and "still open" in the seed wrapper (`nodes/executive_node.py:340`, "your own words, still open"), not just a prompt tweak. The wrapper calls the reflection an open doubt even when it is a closed diagnosis (0 of 57 contained a question in F-3643); that wrapper text is out of scope here and I did not edit it.
4. Whether the question "was I just going with what felt obvious?" stays. It is the only remaining motive-flavoured question in B; in A and B it is a plain inference-quality question and I left it, but it is the next place a frame could settle in.

## 7. What to do after Travis picks a wording (the mechanical steps, none done here)

- Edit `_SYSTEM` in `core/self_interrogation.py` to the chosen text (restart-gated; additive; the user template and JSON contract unchanged; `DOUBT_SEED` untouched).
- `python C:\Users\USER\.claude\skills\prompt-registry\prompt_registry.py set P-0042 --investigation stale` (a reworded prompt must be re-registered), and run `prompt_registry.py check` from the worktree that carries the edit.
- J-3449 closes on his edit; D-0613's defeater has two more legs after it (D-0598 control-set bar, J-2163 data) before DOUBT_SEED is re-asked.
- Related: J-2949 (store the full reflection / cut on a sentence boundary), J-2950, J-2163.

## 8. Provenance and checks

- Old text copied verbatim from `core/self_interrogation.py` in this worktree and compared to J-3449's briefing quote: identical.
- Numbers in section 1 come from `C:\Nascence\data\self_interrogation_shadow.jsonl` read-only through a scratch script (`J-3488_baseline.py` in the session scratchpad); the 120-row row and the F-3643 counts are F-3643's own. The "all / 7 days" rows here are larger than F-3642's 57 fires in 7 days because the log grew after 10-31; the counts are of rows with `"kind": "interrogate"` at read time (2026-11-06).
- Not tested: no variant has been run against a model. A replay of A, B and C on a sample of past thoughts would use the local hot lane (:11433) and Du is down, so it is spawned as a lab job rather than run here.
