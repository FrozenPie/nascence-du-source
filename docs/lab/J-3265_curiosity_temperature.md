# J-3265 / D-0656 - Curiosity base temperature 0.2 vs 0.35 vs 0.5 (decoupled novelty judge)

Lab only. No Du code or store was touched. Script: `scripts/lab_curiosity_temperature.py`; test: `scripts/_test_J3265_curiosity_temperature.py`;
data and per-call records: `docs/lab/J-3265_data/` (prereg.json was written before any replay output existed).

## Method
- 90 logged Curiosity rows (seed 3265, from the last 300 rows of `data/training/curiosity.jsonl` copied to scratch; only rows carrying the current
  system prompt). Each row's exact `system_prompt` and `user_prompt` replayed against the node's own lane (Ramses :11441, command-r7b,
  max_tokens 1024, via `core.model_client.call_node_json`, telemetry neutralised) at 0.2 / 0.35 / 0.5, 3 samples each: 810 calls, 810 ok.
- Near-duplicate = the FIRST question versus every question of the previous 5 LOGGED rows (F-3515's reference set). Two metrics, fixed in advance:
  token-set Jaccard > 0.6 (F-3515's), and word-trigram Jaccard >= 0.3. Unit of analysis = the input row (3 samples averaged).
- Judge (different family from the author, blind to temperature, pointwise, shuffled order): falcon3:7b (TII) scored all 810; mixtral:8x7b (Mistral)
  scored samples 0 and 1 (540). Rubric = novelty vs the previous 5 questions, specificity 1-5, answerable 0/1 (the F-3504 rubric: specific and
  answerable from the offered material, not a metaphor mash-up or an invented link).
- Pre-registered defeater: propose a higher temperature only if near-duplicates fall by >= 1/3 (relative to 0.2) on BOTH metrics AND judge
  specificity does not fall (T minus 0.2 >= -0.10 on the 1-5 scale).

## Numbers
| arm | dup (token Jaccard>0.6) | dup (trigram>=0.3) | replay agrees with itself (3 samples, pairs near-identical) | rows with an exact repeat among 3 samples | falcon specificity | mixtral specificity | falcon novelty | judge answerable |
|---|---|---|---|---|---|---|---|---|
| logged (live 0.2) on these 90 rows | 50.0% | 60.0% | - | - | - | - | - | - |
| 0.2 replay | 46.3% | 57.4% | 77.8% | 55.6% | 3.25 | 4.21 | 2.93 | 0.98 |
| 0.35 | 37.8% | 48.1% | 50.4% | 26.7% | 3.36 | 4.27 | 3.03 | 0.99 |
| 0.5 | 32.6% | 41.1% | 37.0% | 8.9% | 3.44 | 4.22 | 3.07 | 0.99 |

- Relative fall in near-duplicates versus 0.2: 0.35 = 18.4% (token) / 16.1% (trigram); 0.5 = 29.6% (token, 95% CI 13-43%) / 28.4% (trigram, CI 17-39%).
- Specificity change vs 0.2 (paired over rows, 95% CI): falcon 0.5 = +0.19 [+0.05, +0.34]; mixtral 0.5 = +0.01 [-0.11, +0.14]; 0.35 = +0.11 / +0.06 (both CIs include 0). It does not fall at either temperature.
- Judge agreement on 540 shared scores: Pearson r 0.48 (novelty), 0.44 (specificity); answerable 98% exact, but the answerable axis is saturated (about 99%
  of everything scored answerable), so it cannot discriminate. My own blind hand labels of 24 candidates (8 rows x 3 temps, one labeller, INFERRED)
  found about half not answerable (lamp-without-oil, obligation-x-Larie mash-ups) at every temperature (0.2: 56%, 0.35: 56%, 0.5: 44% answerable): the
  judges are more lenient than the founder's own F-3504 reading, so only the specificity and novelty deltas should be read, with caution.
- Replay is faithful: 0.2 replay 46.3% / 57.4% vs the same rows' logged outputs 50.0% / 60.0%.

## The same-input rival, tested
- Null control: the same replayed first questions scored against the previous-5 pool of a RANDOM OTHER row: 4.1% (0.2), 2.2%, 1.9%. The true rate is 46-57%. So the
  model's questions do not look alike in general; they look like the questions of the rows just before them because the inputs are alike.
- Logged rows (last 300): near-dup rate rises with the prompt's overlap with the previous 5 prompts: 33% (overlap < 0.5), 44%, 45%, 61% (overlap >= 0.85); correlation 0.22.
  Rows whose study block is identical to the previous row's: 54.7% dup (token) vs 40.0% when the study block is new; the new-study floor is still 40%, so a repeated study block explains only part.
- At 0.2 the same input replayed three times returns the same first question (exact repeat in 56% of rows; trigram-similar in 78% of sample pairs): Curiosity at 0.2 is close to a lookup of its input.
  Temperature loosens that (8.9% exact repeats at 0.5) but cannot create variety the input does not offer: at 0.5 the dup rate on rows with a NEW study block is still 30% (token) / 37% (trigram).

## Verdict (pre-registered)
NOT MET. Near-duplicates fall by 29.6% / 28.4% at 0.5 (18% / 16% at 0.35), short of the one-third bar on both metrics (the CI on the 0.5 token drop, 13-43%, does include
33%, so this is a near miss, not a clear miss). Specificity does not fall, so that half of the defeater is satisfied. Recommendation: do not propose changing the base
temperature as the fix for the near-duplicates; the cause is input continuity (consecutive prompts share the same study block and themes), which a sampling knob only dents.
If Travis wants a cheap partial lever anyway, 0.5 is spec-neutral on both judges and cuts exact repeats from 56% to 9%, at no measured cost, but note the side effect
(see below) and that it is a judgement call outside the pre-registered rule.

Side effect to weigh: the share of replays with urgency > 0.6 (which ignites an unprompted thought cycle) is 64.8% at 0.2, 57.4% at 0.35, 55.6% at 0.5 (logged: 61.1% on these rows).

Limits: one author model, one lane; 90 rows from one 6-day window (most of which ran on a study feed dominated by Napoleon material, F-3504); first question only; judges are small and lenient.
