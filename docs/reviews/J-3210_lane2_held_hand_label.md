# J-3210: hand-label of 30 split Lane 2 "held" rulings (per D-0599 part 3)

Status: analysis, read-only, 2026-11-05. Job J-3210, from the build-marathon brief wave A. No judge, prompt, flag or data store was changed. Data: `docs/lab/J-3210_lane2_held_labels.jsonl` (the 30 items, my labels, and the three votes).

## The question

D-0599 part 3, in the founder's words: "Hand-label 30 split held rows first (an analysis job) to learn who is right before touching the held key." The D-0599 defeater names the test: revisit "if the hand-label of 30 splits shows mixtral right more often than gemma."

F-3744 had found that on `lane2:prediction` held, mixtral (JUDGE_1, :11438) is true 8.5 percent, falcon (JUDGE_2, :11440) 73 percent, 65 percent of rulings are splits, and the gemma tiebreak (:11439) says true 89 percent, so most held verdicts are gemma overriding mixtral. Nobody had checked who is right.

## Answer in one paragraph

On 30 stratified splits, gemma is right far more often than mixtral, so the D-0599 defeater is NOT met and gemma overriding mixtral is justified. Counting "the observation does not settle it" as false, which is the judge prompt's own rule: mixtral right 7 of 30 (23 percent), falcon 23 of 30 (77 percent), gemma 26 of 30 (87 percent). Mixtral is right only on items where the right answer is "unsettled"; on every item where the prediction plainly held, mixtral said false (0 of 23). I recommend: keep the gemma tiebreak and the held key as they are, do not retire the key, and do not repoint mixtral yet. The bigger finding is that the question the key asks is nearly empty: 592 of 598 held verdicts with a named sound were for a sound already sounding when the prediction was made.

## Label provenance (read this first)

D-0599 asked for a hand label "by hand or by a clearly labelled hand-read (Travis), not by a model". I could not obtain a Travis hand-read inside this job. The labels below are a hand-read by me, Claude. That is a model, so it does not meet the founder's bar. What I did to keep it honest:

- The 30 items were drawn by a seeded sampler (seed 3210) and shown to me as a blinded sheet (prediction, the percepts it was made against, the percepts at judging time; no votes, no why strings, no verdict).
- I wrote all 30 labels to a file BEFORE opening the key that carries the three votes. The labels were not revised after scoring.
- Claude is a different family from all four panel models (Mistral, TII, Google, IBM) and from the generator (deepseek), so the decoupled-judge law holds in family terms, but I am not an independent human.
- Where I was unsure I marked the label soft (`*`).

So the numbers are real counts of a blind, hand-read label, but the labels are provisional until Travis reads them. The 30 items with my label and reason are in the table and the jsonl; Travis can overwrite any label in minutes and the scoring script is trivial. I list this as the first founder call below.

## Method

- Population: `data/judge_panel_log.jsonl` rows with `context == lane2:prediction`, `how == tiebreak`, mixtral false and falcon true. Each was joined to its Lane 2 tick in `data/lane2_shadow.jsonl` (window from the tick ts to the next tick ts; the join was checked on 5836 judged ticks and the panel `how` and `why` matched the tick's `prior_judged_how` and `prior_judged_why` on 1204 of 1204 single-candidate joins that carry `percept_lines`).
- Only ticks since 2026-09-29 carry `percept_lines`, so that is the frame: 28 distinct days, 542 splits with percepts at both prediction time and judging time. Every one has `prior_judgeability` matched-standpoint, and every panel row used hubs :11438 / :11440 / :11439.
- Stratification: one split drawn at random from each of the 28 days, plus one extra from each of the two largest days (10-14, 11-01), 30 in all. Days are 09-29 to 11-05; none from the 10-21 to 10-28 gap because Du was down then.
- Left out of the frame, stated so nobody over-reads the result: the 11 reverse splits (mixtral true, falcon false; 11 of 581, under 2 percent) and all agreed rows. This says who is right when mixtral and falcon split, not how the agreed rows score.
- Label rule: the judge prompt says "if the observation does not settle it either way, answer false", so the strict truth is held only when the observation affirms the prediction; contradicted and unsettled both score false. I label three ways (H held, U unsettled, B broke) and report both the strict scoring and a version that drops soft unsettled items. No item came out B.
- Reading rule for sounds: a predicted sound counts as heard if it is named in the observation's sounds line. The judge saw only the first 600 characters of the observation; two items run to about 600 characters and in both the relevant sound was inside the first 600.

## Result

Strict scoring (unsettled counts as false), n = 30:

| voter | right | share | 95 percent interval |
|---|---|---|---|
| mixtral (JUDGE_1) | 7 | 23 percent | 12 to 41 |
| falcon (JUDGE_2) | 23 | 77 percent | 59 to 88 |
| gemma (tiebreak) | 26 | 87 percent | 70 to 95 |

By construction of the sample mixtral said false and falcon said true on all 30, so the three scores are the number of U items (mixtral), the number of H items (falcon), and gemma's own calls. My labels: 23 held (21 clear, 2 soft), 7 unsettled (5 soft "vacuous", 2 clear), 0 broke.

- Clear items only (24 of 30; drops the 6 soft): mixtral 2 of 24, falcon 22 of 24, gemma 22 of 24.
- Items I called held (23): mixtral right 0, falcon 23, gemma 22.
- Items I called unsettled (7): mixtral right 7, falcon right 0, gemma right 4.
- Gemma overrode mixtral (said true against mixtral's false) on 25 of 30: right on 22, wrong on 3 (B02, B03, B13, all unsettled). On the 5 where gemma sided with mixtral it was right on 4 (B12 is the miss).
- Paired: gemma right and mixtral wrong on 22 items, mixtral right and gemma wrong on 3 (a sign test on 22 to 3 is about p = 0.0001).

Is gemma overriding mixtral justified? On this sample, yes: 22 of 25 overrides were correct, and mixtral's votes were wrong on all 23 plainly held predictions. The D-0599 defeater condition (mixtral right more often than gemma) is false by 7 to 26.

What mixtral is actually doing: its own `why1` strings contradict its verdict. Examples, verbatim from the panel log:

- B04 "Observed sounds include penguin bray, but expectation was to hear it" (false).
- B09 "Observed sounds include waves on shingle, but the expectation was not" (false).
- B16 "no bird call heard" against an observation naming kingfisher and oystercatcher calls.
- B10 "Observed many other sounds, not just the clock tick" (the prediction was only the tick).

It reads the observation as a snapshot and wants an event that is new or specific, rather than checking whether the predicted thing is present. Mixtral's seven "correct" calls are the vacuous or unmatched items (for example B21, "I see a shadow on the wall", where the observation holds no shadow information). That is agreement by luck of the item type, not discrimination.

Gemma's four misses: B02, B03 and B13 are unsettled items it called held (B13's why3 says "the sun's position (dawn) was observed" although the observation has no sun field), and B12 is a held item it called false on a "static snapshot" reading the same way mixtral does (why3 "does not confirm a change in sound volume"). Gemma says false on every "more sounds" item (B05, B11, B12, B25), which is the one family where it shares mixtral's habit.

Falcon alone scores 23 of 30 and is perfect on the held items; its weakness is that it also says true on the unsettled ones, so it is lenient where gemma is a little stricter.

## The larger finding: held is mostly "a sound that was already sounding is still sounding"

Reading the 30 items, almost every held one predicts a sound that was already named in the percepts it was made against: 21 of the 23 held items (all but B12 and B17). Lane 2 does gate one such case (`_heard_steady_sound_flag` in `core/lane2.py`, F-2932/J-2239: "clock tick" only, never stored, never judged), and in this sample that flag is False or missing on every item that was not a clock tick.

I measured it over the whole post-09-29 judged population with a lexical proxy (a small sound vocabulary: cuckoo, gull, owl/morepork, penguin, kingfisher, clock, waves, warbler, trill, bird and so on, matched against the sounds line of the prediction-time percepts; honestly a proxy, not a judge): of 598 held verdicts whose prediction names one of those sounds, 592 (99 percent) named a sound already present at prediction time. For unsettled verdicts it is 137 of 143 (96 percent); for broke it is 3 of 3. A further 108 held and 171 unsettled predictions name none of the vocabulary and are not counted.

This does not make the held key wrong; it makes the held share a measure of persistence in a soundscape that the world supplies, not of the generator's foresight. It also explains why the voters split at all: they disagree about whether "the cuckoo is still calling" counts as a prediction that came true. It matches the notice-judge story in F-3744: a verdict that barely discriminates.

## Recommendation (one per question)

1. Keep the gemma tiebreak and the held key as they are. Do not retire the key and do not touch the judges on this evidence. Gemma overriding mixtral is justified here; D-0599's defeater is not met.
2. Do not repoint mixtral off this key yet. The hand-label covers only the splits. Over the whole log mixtral and falcon agree false on 2787 of the 7359 `lane2:prediction` held rulings, and that stratum (which feeds the unsettled and broke verdicts and the cup) has not been read by anyone. One more labelled sample answers whether mixtral earns its call on this key: filed as an analysis job below.
3. Fix the question rather than the voter. The cheapest honest improvement is to generalise the F-2932 gate from "clock tick" to any sound already sounding at prediction time (never stored, never judged), which the 99 percent figure says would remove 732 of the 744 sound-named judged predictions (and the panel calls behind them), and stops the held share reading as foresight. That is a Lane 2 design change on a LIVE-provisional plan, so it is filed as a needs_input job with these numbers, not built.

## What needs a founder call

1. Read or overwrite my 30 labels. D-0599 said a hand label, not a model; this is a model's blind hand-read. Travis can read the table below (or the jsonl, items B01 to B30, with the percepts) and overwrite any label; the result is robust to a handful of flips (mixtral would need 19 more items to go its way to match gemma).
2. The held-key action (keep, repoint, retire): my recommendation is keep as is, generalise the steady-sound gate, and read the agreed-false stratum before repointing mixtral. Filed as a needs_input job.

## The 30 items

Label: H held, U unsettled; `*` marks a soft label. Votes: T true, F false (M mixtral, F falcon, G gemma). All 30 are mixtral F, falcon T by construction.

| id | day | prediction (truncated) | mine | M | F | G |
|---|---|---|---|---|---|---|
| B01 | 10-10 | I expect to hear a bird call in about 5 minutes. | H | F | T | T |
| B02 | 11-03 | In about 6 minutes, I should check the fire's status and ensure it's e | U* | F | T | T |
| B03 | 09-29 | I expect to hear more sounds within the next 6 minutes, as the horizon | U* | F | T | T |
| B04 | 10-29 | In about 6 minutes, I will hear a penguin bray. | H | F | T | T |
| B05 | 10-14 | I will hear more sounds in about 6 minutes. | U* | F | T | F |
| B06 | 10-31 | I expect to hear a bird call in the next 6 minutes. | H | F | T | T |
| B07 | 10-12 | I expect to hear a cuckoo call in about 6 minutes. | H | F | T | T |
| B08 | 11-01 | In about 6 minutes, I will hear a gull cry. | H | F | T | T |
| B09 | 10-20 | In about 6 minutes, I will hear a wave on shingle. | H | F | T | T |
| B10 | 10-16 | I expect to hear the clock tick in about 6 minutes. | H | F | T | T |
| B11 | 09-30 | I expect to hear more sounds in about 6 minutes. | U* | F | T | F |
| B12 | 10-09 | I expect to hear more sounds in about 6 minutes. | H | F | T | F |
| B13 | 11-02 | In about 6 minutes, I will hear the kingfisher's call and see the sun' | U | F | T | T |
| B14 | 11-01 | In about 6 minutes, I will hear a bird call or a wave crash. | H | F | T | T |
| B15 | 10-19 | In about 6 minutes, I will hear the sound of waves on the shingle and  | H | F | T | T |
| B16 | 10-08 | In about 6 minutes, I will hear a bird call. | H | F | T | T |
| B17 | 10-04 | I expect to hear more sounds within the next hour. | H* | F | T | T |
| B18 | 10-11 | I expect to hear a cuckoo call within the next 6 minutes. | H | F | T | T |
| B19 | 10-15 | In about 6 minutes, the clock will tick. | H | F | T | T |
| B20 | 10-13 | In about 6 minutes, the clock will tick again. | H | F | T | T |
| B21 | 10-05 | I see a shadow on the wall. | U | F | T | F |
| B22 | 10-01 | I expect the warmth to remain mild in the next 15 minutes. | H | F | T | T |
| B23 | 10-17 | In about 6 minutes, I will hear the cuckoo call and see the sun's posi | H | F | T | T |
| B24 | 10-30 | In about 6 minutes, I will hear a cuckoo call. | H | F | T | T |
| B25 | 10-06 | I expect to hear more sounds in about 6 minutes. | U* | F | T | F |
| B26 | 10-07 | I expect to hear a cuckoo call in about 6 minutes. | H | F | T | T |
| B27 | 11-05 | I expect to hear a wave sound within the next 6 minutes. | H | F | T | T |
| B28 | 10-18 | In the next 6 minutes, I will hear an owl call again. | H | F | T | T |
| B29 | 11-04 | I expect to hear a bird chirping in about 6 minutes. | H | F | T | T |
| B30 | 10-14 | In about 6 minutes, the clock will tick. | H | F | T | T |

Soft labels: B02 (an intention to check the fire, not a perceivable event); B03, B05, B11, B25 (vacuous "more sounds" with an identical sound list, so nothing was added); B17 ("more sounds within the hour", a new sound appeared but the place changed and the prediction was 109 minutes old). B12 is held because a new sound (bees in the garden) did appear. The strict scoring above counts the soft U items as false; dropping the six soft items gives mixtral 2 of 24, falcon 22, gemma 22.

## Limits

- One reader (me), not the founder; see provenance. The label rule for "heard" (named in the sounds line) is generous to the predictions, and a stricter reader (a new event after the prediction) would move most of the 21 clear held items toward unsettled, which would help mixtral. That is exactly why the recommendation reads the agreed-false stratum and generalises the steady-sound gate instead of declaring gemma "correct" in an absolute sense.
- Frame: post-09-29 FT splits only; reverse splits (11) and agreed rows not read.
- n = 30, intervals above. The paired 22 to 3 result is the load-bearing number and is not close.

## Follow-ups filed

See the done summary for the job ids (a needs_input job for the held-key and steady-sound-gate call, and an analysis job to hand-label 30 agreed-false rows).
