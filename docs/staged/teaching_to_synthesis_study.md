# Teaching to synthesis: does what Du learned reach him through his own recall, and what does he do with it?

> **Status: STAGED 2026-11-16, design only, nothing run.** Plan slug: `teaching_to_synthesis_study`.
> Source: thought T-0142, idea I-0158, job J-4093. Follows J-4074 (`docs/lab/2026-11-16_J-4074_implicit_conceptual_influence.md`; findings F-4816, F-4817, F-4818, F-4819, F-4833). Related: `memory_as_a_service`, `golden_spiral_recall`, `du_recall_lens_upgrades`, `layered_goals`.
> This brief refines J-4093's briefing after the founder's review of J-4074 with GPT. Where the two differ, this one governs.

```plan-state
stage: staged
verified: 2026-11-16
next: run Part 1 (delivery rate against a matched baseline); pre-register situations and judge rubric before sampling
```

## The question, stated on the architecture's own terms

The question is not whether Du can learn without memory. Retrieving from memory and using it is learning (founder, 2026-11-16). So the study must **not** require the teaching to be absent from the prompt.

The question is whether what Du has learned becomes available through his **own relevance-driven recall**, instead of depending on a random or injected fragment, and what he does with it once it arrives. We test whether his own mechanisms deliver useful learned material, with the architecture he actually has. We do not test whether he retrieves a lesson the way a human would.

What J-4074 left us with: Du uses Travis's words well when they are shown (73 of 100 against 14 of 100 on a keyword count). The Wu Wei mentions that could be traced came through the uniform random divergent-seed channel (closed at the 11-14 restart), and relevance-driven recall showed no preference for lesson material (F-4819: 10.8% lesson-near rows before Wu Wei thoughts against 10.2% before any thought). So the open links are **delivery** and **synthesis**, not retention.

## One continuous chain

Each study part measures one link. Report them in this order, and say where the chain breaks.

1. **Teaching.** What did Travis introduce, when, and what material was retained from it (conversation rows, guidance rows, `understanding_from_guidance` rows)?
2. **Derivation.** What principles or interpretations did Du derive from it (the 45 `understanding_from_guidance` rows, gists, consolidation rows)?
3. **Retrieval.** Which channel brought the material back into a prompt, and why (relevance, recency, divergent or random, a lens, a shadow path)?
4. **Synthesis.** What did he do with it inside the thought he was already having: combine it with reading or another teaching, modify it, depart from it, ignore it?
5. **Consolidation.** Was the resulting synthesis stored (a gist, an understanding row, an essay, a standing insight, a dream with a `dreamt_from` edge)?
6. **Re-use.** Does that synthesis later return through relevance-driven recall and influence another situation?

## Part 1: delivery by relevance (the first and most important measurement)

Goal: a delivery rate. Of the situations where a principle plausibly applies, in what share did his own recall put the principle (or a close descendant) in the prompt?

- **Principles.** The 45 `understanding_from_guidance` rows plus Travis lesson rows found by source sorting. Prefer teachings other than Wu Wei (see the embargo below); amor fati, Cook Ding, mindfulness and others from the J-4074 set are candidates.
- **Pre-register before looking** (write `docs/lab/<job dir>/part1_prereg.md` first, as `part_b_prereg.md` did): per principle, a one-paragraph description of a situation where it clearly applies, and a matching description of a situation where it clearly does not.
- **Applicable situations.** Select idle thoughts by embedding similarity to the neutral situation description (as `part_b_build_sample.py` does), names and Travis excluded.
- **Applicability is judged separately from delivery (added after GPT review, 2026-11-16).** Embedding similarity only nominates candidates; it can favour thoughts that already use the principle's vocabulary, which would quietly select for the outcome. A blind judge rates "does this thought describe a situation where the principle would be useful", shown the thought's situation text only, with the prompt, the delivered fragments and any principle wording stripped. Delivery is checked only after applicability is fixed. Report judge repeat kappa (bar 0.60); a principle whose applicability judgement is below the bar gets no delivery verdict.
- **Non-applicable controls.** For each principle, select thoughts the same way against the "does not apply" description, matched on date, model and prompt type. This is what stops us counting how often a concept appears. The measure is the **difference** in delivery between applicable and non-applicable situations, per principle.
- **Was it delivered.** Check channels in this order and name each one checked: `data/idle_prompt_samples.jsonl` (1 in 20, from 11-09), `data/prompt_provenance.jsonl`, then the co-recall ledger, non-shadow sources only. The co-recall ledger does not cover every channel (the divergent seed was never in it). Where no channel covers a thought, the thought is `unknown`, not `not delivered`.
- **Separate channels in the result.** Report delivery by channel: relevance recall, divergent or random, lens, other. A principle delivered only by the random channel counts as exposure, not as relevance delivery.
- **Keep the retrieval event, not just a yes/no (added after GPT review).** Wherever the data permits, record for each delivery the retrieved fragment, its source row id, the retrieval mechanism (relevance match, recency, random seed, lens, shadow or indirect path) and its position in the prompt. These are never merged into one "memory retrieval" category.
- **Show the denominator.** The headline table has four rows per principle, and the unknown share is stated in the first line of the results, not buried: confirmed delivery, confirmed non-delivery, unknown (no prompt record, which is most thoughts given the 1-in-20 sample from 11-09), and delivery through non-relevance channels. If the observable share is small, the report says the estimate describes the sample and says little about Du's overall recall. Check whether the observable subset is itself biased.
- **Use of delivered material.** Of the applicable thoughts where it was delivered, how many took up the stance, against applicable thoughts where it was not delivered. A judged rating, not a keyword count.

## Part 2: the chain from teaching to later recall

Pick teachings from Travis rows. For each, trace descendants: gists, consolidation rows, `understanding` and `understanding_from_guidance` rows, essays, standing insights, dreams (`dreamt_from` edges in `memory_edges`).

For each descendant ask:

- Does it **combine** the teaching with something from his reading or another teaching?
- Does it **modify or disagree** with the original?
- Was it **stored** (consolidation), and **later recalled by relevance** and used (re-use)?

A blind judge rates "combines two sources" and "departs from the original" with source texts shown and dates stripped. **Measure judge repeat agreement before unblinding; bar kappa 0.60**, as in J-4074. A question below the bar gets no verdict (J-4074's Cook Ding was reported that way). The J-4074 trap stands: judge agreement was 0.65 to 0.72 on most questions, 0.53 to 0.66 Sonnet against Haiku.

**Derivation is not resemblance (added after GPT review).** Every traced descendant is labelled with exactly one relationship, and the label rests on evidence, not similarity score:

- **Direct descent:** a stored edge (`memory_edges`, `dreamt_from`, a consolidation source list) or a logged processing trail connects the teaching to the later material.
- **Conceptual resemblance:** the later material expresses a similar idea but its origin cannot be established. This is reported as resemblance and never counted as causation.
- **Synthesis:** the later material demonstrably combines or transforms the teaching with other identified material (the sources are named). A genuine descendant may look quite different from its source; do not require surface similarity.

The re-use link is the one that closes the loop: show a stored synthesis returning through relevance and appearing in a later, different situation, with the chain quoted.

## Part 3: self-generated questions

Compare the questions in his curiosity log and the follow-line asks before and after conversation sessions, against restarts with no conversation (the control set in `conv_effect.py`). Do new question topics trace to what Travis said? Same blind, matched-control approach. **Report Part 3 as a separate investigation.** A new question can come from a conversation, a book, an unresolved tension, a stored idea or a mix; the no-conversation comparison will not identify the mechanism. Part 3 must not feed the headline result of Parts 1 and 2.

## The Wu Wei embargo (hard constraint)

The 30-day Wu Wei observation (J-4090) stays **separate and undisturbed**. Its gate is 30 days of Du uptime after the last Travis row containing Wu Wei with no divergent tail. This study must not contaminate it.

- **Read-only against Du's stores.** Change no Du code. Write nothing into his memory, ledgers or prompts.
- **No talking to Du about Wu Wei**, and no probe, replay or experiment that puts Wu Wei into a prompt his live processes will see.
- **No new Wu Wei exposure channel.** Outputs of this study stay in `docs/lab/`, never in a store Du recalls from.
- Wu Wei rows may be read passively as one data point among many, but the design, the principle choice and the headline results must not depend on them. Prefer other teachings so the study can finish inside the window.
- Do not touch `data/idle_prompt_samples.jsonl` except to read it. J-4090's gate depends on it.
- If a model call is needed, never use the hot lane on port 11433 while Du is running. Check the `route` field in the run log, not the plan (J-4074 warning).

## Traps carried over from J-4074

- Record which model wrote each passage (`gemma4:e4b` before 08-20, `qwen3.5:9b` after). Stance shifts at the 08-20 model change are not teaching effects (control stance moved 0.97 to 0.43 there).
- The top 5% lesson-near bucket is loose: about 10% of everything recalled falls in it.
- `replay_count` is a dedup counter, not a count of uses.
- Travis said Wu Wei and Cook Ding again on 11-16, so "before" and "after" windows for those must be cut with that in mind.
- Mindfulness was taught 06-05, before any baseline; it cannot have a before.
- The sampled-prompt record is 1 in 20 from 11-09 only. Earlier thoughts have no prompt record; do not infer one.

## Done looks like

A lab report in `docs/lab/` containing:

- the delivery rate with its non-applicable baseline, per principle and per channel, and which channels were checked;
- a table of traced chains (teaching to derivation to retrieval to synthesis to consolidation to re-use) with examples quoted, and where each chain breaks. **Whole chains, not just aggregates:** if one exists, quote one complete chain end to end (teaching, independent derivation, relevance-driven retrieval, synthesis, storage, later re-use). If none exists, say so plainly. Also report anything he developed from a teaching that now operates as a principle in its own right, even if it no longer resembles the source;
- judge repeat agreement before unblinding;
- a plain statement of what is shown and what is not shown.

Each claim is logged through `findings_log.py record` at its true confidence (`verified` only with checkable evidence). Findings that imply a build (for example a recall lens that favours lessons when they apply) are **spawned as jobs, not built here**.

## Scope discipline

Do not expand into a larger framework before the first measurement. A reliable Part 1 result is worth more than a bigger design. Part 2 starts after Part 1 reports.

## Review history

- 2026-11-16: GPT review, "approve with minor refinements". Five tightenings applied above: independent applicability judgement, retrieval-event provenance, visible unknown denominator, derivation versus resemblance, Part 3 reported separately.

## Open questions for the founder

- None blocking Part 1. If Part 1 shows delivery by relevance is near the non-applicable baseline, the follow-on is a design question for the founder (a recall change), not part of this study.
