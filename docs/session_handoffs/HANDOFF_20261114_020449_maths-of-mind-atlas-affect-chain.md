# Maths-of-mind atlas: 36 human signatures against Du's code and logs, and the affect chain it uncovered

## Session timing
- **Session started:** 2026-11-13 23:46:23 UTC
- **Last message before wrap:** 2026-11-14 02:04:46 UTC
- **Wrapped:** 2026-11-14 02:04:49 UTC

## Summary
The founder pasted a GPT survey of mathematical psychology and asked whether maths is where human and AI meet. This session built an atlas of 36 human signatures, marked each as written into Du's code, inherited from the tool models, or not written, and ran every first read over the live logs (all read-only). One unwritten match was found (memory re-use against age), and two side results matter more: the old vitality reading is about half the reason Du is told his mood is low, and the two panel judges barely agree beyond chance.

## Decisions
- D-0775 (open, the_consciousness_program): whether to do anything about the idle mood line before `vitality_v2` replaces the old vitality reading. Options A wait, B words only, C vitality out of the drive, D bring the replacement forward. Not ruled.
- D-0776 (open, emotion_rethink): whether `EMOTION_CONSTRUCTED` should be barred until the vitality replacement is in the drive, and what the joy pump does meanwhile. Not ruled.
- Founder direction given in chat, not a `/decide` ruling: goals work is in another window and was to be ignored here; build the atlas with a built-in against emerged column; push the measurement side this session.
- My own call, not the founder's: no affect code was changed, because the vitality fix is already ruled (D-0398) and in its shadow period, and the goals window is working on the same need readers.

## Builds
- `docs/staged/maths_of_mind_atlas.md` (I-0152 and T-0128, T-0129 promoted to it). 36 rows; 11 written in, 6 partly, 10 not written, 5 inherited, 3 not checked, 1 measurement row. Results in sections 6.1 to 6.3, auditor round in section 10. Passes plan-state lint. Closed as a catalogue.
- `docs/reviews/affect_chain_2026-11-14.md`: the chain from the sleep gauge to the mood words, link by link.
- No code, no prompt, no store written except through the ledger tools.

## Findings
- F-4639: the one new goal-pursuit source in the GPT survey (Budden et al. 2026) exists; only 23 computational studies, 2 on goal revision. Abstract only.
- F-4642 [INFERRED]: the written-in tally. Code facts are from four read-only agents; eight lines spot-checked by grep.
- F-4649 and F-4662: memory re-use follows a power law of age in the recency-off shadow arm (slope -0.79, R2 0.88) and in the live arm in each of four months (-0.74 to -1.06). Nobody wrote it. [INFERRED] The cause is the cue stream: what he thinks about now resembles what he stored recently. [OPEN] Whether that is topic persistence, the nested structure of his activities (sitting, book, subject), or something in the store: J-3993.
- F-4650: no practice curve is readable; drills sit at 95 to 100 percent. The level-5 maths collapse of 06-20 to 06-22 and its recovery coincide with the founder's method hints of 06-22; cause of the collapse not established.
- F-4651: fatigue does not degrade his thinking; grounded share rises with time awake (0.65 to 0.78).
- F-4652: deed timing is near random (burstiness +0.08 against a +0.05 null).
- F-4653: temporal contiguity in the memory store is a weak, symmetric excess, most simply same-source material.
- F-4654 and F-4659: weekly affect is unstable because valence has been `1 - 2*drive` since 2026-07-07 (`core/homeostasis.py:99`, flag `core/schema.py:1279`) while joy is still model plus pump. Valence is negative mainly from vitality (about 0.38 against a 0.78 setpoint; 44 percent of squared drive) and relational warmth (about 0.5 against 0.824).
- F-4660: every idle thought is seeded with a mood line (`nodes/inner_monologue_node.py:3452`). Since 2026-09-01 the tone word was some form of low on 47 percent of 54,782 idle thoughts; 24 percent with the vitality term removed. [OPEN] Whether the line changes what he thinks: J-3994.
- F-4661 [INFERRED]: emotion node runs about 59 times a week and sees only the perception summary; carried joy mostly comes from `_feel_joy`; constructed joy would be zero on 74 percent of rows while valence is negative.
- F-4663: Cohen kappa between the two panel judges is under 0.5 on every verdict key and near zero on cuts, genuine, metaphor and coherent. Not split by judge-model era.
- Three auditors (GPT, Gemini, Perplexity) read the atlas. Taken: the reads are exploratory; R2 on binned data does not settle the functional form; stop growing the catalogue; trace consequences instead (I-0155). Not taken: Gemini's "discard the human judges" (they are models), "valence is useless", and "write a rule so fatigue degrades thought".

## Open
1. D-0775 and D-0776 await the founder. Next action: `/decide-review`.
2. J-3993: M1 mechanism test and a confirmatory run with the analysis written down first. Ready.
3. J-3994: affect per channel and source era; does the mood line change thought; why warmth stays low. Ready.
4. J-3995: judge kappa by era, a labelled reference set for the four weakest keys, and who consumes them. Ready.
5. J-3996: design only for a planned A-B-A model swap, then a `/decide`. Ready.
6. I-0155: consequence tracing, first test on what a served memory changes. An idea, no plan yet.
7. Atlas rows still NOT CHECKED in code: how peer replies are scheduled (X1). L1 to be re-read once drill levels 10 to 17 have attempts below ceiling.
8. The atlas has no ROADMAP link: `docs/ROADMAP.md` had another window's uncommitted edits. plan-schema-audit will file the backfill.

## Warnings
- The analysis scripts are in this session's scratchpad, not the repo: `read_m1.py`, `read_l1_z2.py`, `read_s3_m3_p1.py`, `read_rest.py` under `C:\Users\USER\AppData\Local\Temp\claude\ec905e32dfc14b49\2ebc3c13-11cd-422f-81c4-4cfbe47512d9\scratchpad`. They may not survive; the atlas describes each read well enough to rebuild.
- The finding ids for the first three reads are F-4649 to F-4651. Another window took F-4643 to F-4645 while this session was writing; the atlas was corrected.
- `plan_state.py lint` was run without `--session`, so it is missing from the rollup. Nothing else is.
- Affect logs must not be pooled across 2026-07-07, and valence must not be read as the model's emotion.
- "Use predicts use" in F-4649 is a correlation; waking retrieval changes nothing in the store.
- The atlas file was modified on disk by something other than this session several times during the work (plan tooling or another window). Contents looked right each time I wrote to it.

## Pointers
- `docs/staged/maths_of_mind_atlas.md` — the atlas, results and auditor round.
- `docs/reviews/affect_chain_2026-11-14.md` — for D-0775 and D-0776.
- `docs/staged/layered_goals.md`, `docs/reviews/goal_distributions_2026-11-14.md` — the goals side, owned by another window.
- `docs/plans/emotion_rethink.md`, D-0398, J-3942, J-3967 — the existing vitality and emotion work.
- Logs used: `data/ask_recency_shadow.jsonl`, `data/co_recall_ledger.jsonl`, `data/felt_preamble_log.jsonl`, `data/homeostasis_shadow.jsonl`, `data/affect_log.jsonl`, `data/judge_panel_log.jsonl`, `data/hands_trace.jsonl`, `data/math_drill_log.jsonl`.
