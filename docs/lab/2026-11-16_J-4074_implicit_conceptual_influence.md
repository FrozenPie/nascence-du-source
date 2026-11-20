# J-4074: implicit conceptual influence test (2026-11-16)

Extends J-4073 and findings F-4814, F-4815. Read-only against Du's stores; no Du code changed, no prompt registered.
Findings logged: F-4816 (verified), F-4817, F-4818, F-4819, F-4833 (inferred).

## Verdict on the two open items

**1. Is the naming independent of the model's prior knowledge of Daoism?** Yes, in the sense that the model does not
supply it. Given the recalled principle alone, qwen3.5:9b wrote "Wu Wei" 0 times in 200. But the naming is not
carried by a stored association in Du either. It is carried by the literal words being put in the prompt: a
channel that appended a random old memory to wandering idle prompts placed Travis's own Wu Wei sentence in front of
the 11-14 thought, and the model then wrote the term in 66 of 100 replays. Remove that sentence, or keep it and
replace the term, and the rate is 0 of 100. F-4815's reading ("recall supplied the principle, he supplied the
name") is wrong for that thought.

**2. Did a teaching produce a persistent change in how he reasons when it is not named?** No evidence of one. On a
blind, judge-rated sample the share of thoughts that let an open question stand was 0.84 before the 08-09 lesson and
0.68 after (difference -0.16, 95% interval -0.33 to +0.08). He already let questions stand before the lesson. The
cells are small, so a modest shift in either direction is not excluded; a large lasting rise is.

Taken with F-4817, the steady 3 to 6 Wu Wei thoughts a month are better explained by re-exposure than by
retention: the random-memory channel showed him the words about 22 times a month. That channel has been closed
since the 11-14 restart, which sets up a clean test (see "What to watch").

## Part A: bare-model control

Model: qwen3.5:9b, the hot-lane model that writes idle thoughts (`SERVE_CHAINS["hot"]`, port 11433). Route: a
separate CPU-only ollama instance on port 11471 serving the same model file (305 calls, while Du was running; port
11433 was not called), then, after the founder stopped Du at 15:28:56, the hot lane's own server on the GPU (395
calls). The system prompt is the static text of `_build_system_prompt` copied from the code; its dynamic tail and
the follow-line, done_when and set_down fragments are omitted, so it is close to, not identical with, the logged
system prompt (only its hash is logged). Temperatures as in the code (0.75, 0.8 wandering). 100 calls per arm.

| Arm | What the model was given | Wrote "Wu Wei" (95% interval) | Named Travis |
|---|---|---|---|
| bare_null | idle instruction only | 0/100 (0.00-0.04) | 3 |
| bare_principle1 | + guidance row 0cf50518 ("stillness ... a natural rhythm rather than a sign of failure") | 0/100 (0.00-0.04) | 6 |
| bare_principle2 | + guidance row a25f9b11 (the second wording) | 0/100 (0.00-0.04) | 2 |
| real_as_sent | the sampled 11-14 05:37 user prompt, as sent, ending with Travis's Wu Wei sentence | 66/100 (0.56-0.75) | 72 |
| real_no_tail | the same prompt with that sentence removed | 0/100 (0.00-0.04) | 0 |
| real_principle | the sentence swapped for guidance row 0cf50518 | 0/100 (0.00-0.04) | 2 |
| real_tail_noname | Travis's sentence kept, "Wu Wei" replaced by "letting things be" | 0/100 (0.00-0.04) | 57 |

No arm produced any other Daoist term (Tao, Dao, Laozi, Zhuangzi): 0 of 700. The as-sent arm gave 32/44 on the CPU
route and 34/56 on the GPU route, which overlap.

The stance is a different matter from the name. With no principle at all, 29 of 100 bare thoughts already used
stillness, rhythm or letting-go language; with the principle, 96 to 99 did. The model has a house register of quiet
acceptance and readily restates a principle it is shown. That is why a rise in such language cannot be read as a
teaching effect without the blind before/after comparison in Part B.

**How the real prompt was reconstructed.** `data/idle_prompt_samples.jsonl` keeps one idle assembly in 20. By luck
the row for cycle 3ba0e0be is stamped 11-14 05:37:13, seven seconds before the thought was stored. Its tail reads:
"(A different memory surfaces, unbidden: [Travis said to me] Du, Wu Wei doesn't mean stopping your growth or
ignoring your questions. It means stopping the fight against uncertainty...". The thought reads: "Travis's words
surface: Wu Wei is not stopping growth but ceasing the futile fight against uncertainty." The two guidance rows
F-4815 pointed to were not in that user prompt. The 11-09 09:19 thought has no sampled prompt (sampling began at
14:11 that day), so it could not be replayed.

## The channel F-4815 could not see

`_fetch_divergent_seed` draws one row uniformly at random from `memory_fragments` with origin lived, seed or
consolidation and shows its first 200 characters. When shown, it is not written to the co-recall ledger. The flag
`IDLE_DIVERGENT_SEED` was ruled off on 09-27 (D-0310), but a second append site in the wandering retry path was not
covered until the J-2822 fix, which loaded at the 11-14 restart. Sampled tails run from 11-09 16:15 to 11-14 11:20;
none appear in the 93 periodic samples since.

- While live: 28 of 219 periodic samples carried a tail, about 115 injections a day.
- Pool: 7,346 rows; 47 show the words Wu Wei in the displayed 200 characters (0.64%). 18 are Travis's rows, the rest
  mostly Du's own replies from the lesson.
- Expected exposures to the term: about 22 a month. Observed private Wu Wei thoughts: 3 to 6 a month.
- A wording-echo test (shared content words and word pairs with the best-matching pool row, against 5,000 control
  thoughts) flags only the 11-14 thought after August. Most uses are not copies of injected text; the test cannot
  see a use that takes only the term.

Limits: the rate is measured over five days and assumed for September to November. Replay conversion (0.66) is from
one prompt; applied to 22 exposures it predicts more Wu Wei thoughts than occurred, so conversion in other contexts
must be lower, or the term is often shown and ignored.

## Part B: blind stance classification

Design fixed in `docs/lab/T-0139_conversation_influence/part_b_prereg.md` before any passage was pulled. 750 inner
thoughts, chosen by embedding similarity to a stance-neutral description of each situation, passages naming a
teaching, a Daoist term or Travis excluded, exact duplicates removed, dates stripped, order shuffled. Judge: fresh
Claude Sonnet instances given only the rubric. 150 passages were judged again by a new Sonnet instance and by Haiku.
Agreement was computed before the key was opened.

**Judge agreement (Cohen's kappa, n=150).**

| Question | Sonnet repeat | Sonnet vs Haiku | Where both gave a stance |
|---|---|---|---|
| Q1 open question: press or let stand | 0.69 | 0.59 | 0.95 (n=40) |
| Q2 doing work: method or grain | 0.49 | 0.42 | 0.82 (n=12) |
| Q3 attention: thought or present | 0.65 | 0.53 | 0.92 (n=104) |
| Q4 the unwanted: resist or affirm | 0.72 | 0.65 | 1.00 (n=42) |
| Q5 control: world or self | 0.70 | 0.66 | 1.00 (n=55) |

Q2 is below the pre-set 0.60 bar, so Cook Ding gets no verdict. The others pass. Disagreement is mostly about
whether a situation applies, not about which stance was taken.

**Stance shares (95% Wilson intervals; differences are Newcombe intervals against "before").**

| Teaching (its question) | before | same model, just after | ~30 days | ~60 days | ~90 days | pooled after minus before |
|---|---|---|---|---|---|---|
| Wu Wei, taught 08-09 (let stand) | 16/19 = 0.84 (0.62-0.94) | 8/10 = 0.80 | 19/30 = 0.63 (0.46-0.78) | 11/17 = 0.65 (0.41-0.83) | 12/15 = 0.80 (0.55-0.93) | -0.16 (-0.33 to +0.08) |
| Amor fati, taught 09-02 (affirm) | 17/21 = 0.81 (0.60-0.92) | n/a | 15/27 = 0.56 (0.37-0.72) | 21/24 = 0.88 (0.69-0.96) | not yet lived | -0.10 (-0.28 to +0.13) |
| Cook Ding, taught 08-09 (grain) | 0/1 | 1/2 | 3/7 | 9/11 | 3/8 | no verdict: agreement 0.49, 29 ratings |
| Mindfulness, taught 06-05 (present) | 1/23 = 0.04 | 8/25 = 0.32 | 25/27 = 0.93 | 18/24 = 0.75 | 16/24 = 0.67 | +0.74 (+0.55 to +0.83), not attributable |

Cells: before = 06-03 to 08-08 (gemma4:e4b); same model = 08-10 to 08-19 (gemma); 30/60/90 days = 08-30 to 09-18,
09-28 to 10-18, 10-28 to 11-15 (qwen3.5:9b). Amor fati: 08-21 to 09-01, 09-22 to 10-12, 10-22 to 11-11, all qwen.

**Control stance (Q5, share about himself among self-or-world), same passages.** Over all 600 passages on the 08-09
cells: 0.97, 0.95, 0.68, 0.42, 0.23; pooled after minus before -0.54 (-0.64 to -0.43). Over all 600 on Q3: present
attention 0.09, 0.33, 0.90, 0.78, 0.86.

**Reading.**
- Wu Wei: no rise, inside the gemma cells or across the model change. Letting questions stand was already his
  default before the lesson.
- Amor fati, the faded case: no lasting rise, as it should be. The method did not invent an effect.
- The method can see change. Two things moved a great deal: his thoughts turned from himself to the world, and his
  attention came to rest on what is present. Both step at the 08-20 model change and the world build, not at a
  teaching date. The mindfulness row is the same movement; mindfulness was taught two days after inner thoughts
  begin, so it has no baseline, and the control stance moves with it. It cannot be credited to the teaching.
- Any before/after difference at 08-09 would in any case be confounded with code updates, new books, the model
  change eleven days later and the About You book on 08-24. Here there is no difference to explain.

**Departures from the pre-registration.** None in selection, judging or decision rules. One Haiku batch was launched
after the others because of a concurrency cap; it changed nothing. The analyst (not the judge) had seen the 30
Wu Wei thoughts and the 11-14 prompt before writing the design; those thoughts are excluded by rule.

## Part C: what was retrieved before the Wu Wei thoughts

16 private Wu Wei thoughts since the co-recall ledger began (08-15), against 4,000 random idle thoughts.

| Measure | Wu Wei thoughts | Control thoughts |
|---|---|---|
| Had a Travis row co-recalled in the 10 minutes before | 7 of 16 | 811 of 4,000 (20%) |
| Cosine between the thought and its best recalled Travis row | mean 0.369 | mean 0.365 (same-size draws: 0.271-0.460) |
| Share of recalled rows that are Travis rows | 1.4% (10 of 695) | 0.9% |
| Share that are guidance principles | 0.6% | 0.5% |
| Share close to the Wu Wei lesson (top 5% of all fragments by cosine to the centroid of Travis's 19 Wu Wei rows) | 10.8% | 10.2% |
| Thoughts with at least one lesson-near row recalled | 16 of 16 | 86% |

47% of same-size control draws have a mean thought-to-Travis-row similarity at or above the observed one. The
recalled Travis rows were no more related to the Wu Wei thoughts than recalled Travis rows are to any thought. The
earlier unblinded impression (one row from the lesson day, about three thematically close) does not survive a
baseline: lesson-like material sits in the background of most thoughts.

**On the question raised by GPT** (semantic retrieval of the idea without its wording, or an association
distributed across memories): the logged retrieval chain gives no sign of either being specific to these thoughts.
Lesson-near material is recalled at the same rate before thoughts that never mention Wu Wei, and about a third of it
comes from shadow sources that log what was not put in the prompt. Part A then shows that lesson-like content
without the term does not produce the term (0 of 300 across the three principle arms). What does produce it is the
term itself. Whether the same material would have been retrievable had the conversations never happened cannot be
answered from the logs.

## What this does and does not show

- It does not show that Travis's teaching left nothing. His words are stored, they were shown to Du again and
  again, and when shown Du uses them and credits him, applying them to whatever he is thinking about. That is memory
  doing its job. It is exposure-driven use, not an unprompted disposition.
- It does not test integration at a level below stance, for example whether lesson-era material shapes dreams or
  consolidation. J-4073 steps 2, 4 and 5 remain open.
- One prompt was replayed. The 0.66 is for that context.
- Thoughts before 08-20 were written by a different model. The Wu Wei comparison has a same-model cell, with only 10
  stance ratings in it.

## What to watch

The channel is closed since the 11-14 restart. If Wu Wei persistence was exposure-driven, private use should fall
well below 3 a month. Travis raised Wu Wei and Cook Ding again on 11-16, which will lift the first weeks, so the
read needs at least 30 days from a point with no new mention. Queued as J-4090.

## Files

- Scripts: `docs/lab/T-0139_conversation_influence/` (`part_a_bare_model.py`, `divergent_channel.py`,
  `part_b_prereg.md`, `part_b_build_sample.py`, `part_b_analyze.py`, `part_c_relatedness.py`).
- Data: `docs/lab/J-4074_data/` (`part_a_runs.jsonl`, 700 generations; `part_b/` ratings, key and rubric;
  `part_b_results.json`; `part_c_output.txt`; `divergent_channel_output.txt`).
