# Open-doubt cup (coordinate-only) -- discriminating replay v2

*Run 2026-10-09 · J-2031 (from J-2008 / F-2634 / F-2635) · script `scripts/si_open_doubt_cup_replay_v2.py` · raw `data/lab/J-2031/{gens,pairs}.jsonl`, `summary.json` · nothing wired into Du · D-0396 hold and D-0403 (coordinates, never prose) untouched*

## Verdict: INSTRUMENT INVALID -- no arm may be read; the coordinate is neither shown to carry the concern nor refuted

The pre-registered gate (mismatched thought must beat the matched baseline thought <= 11% of the time) **failed: 5 of 13 judged pairs (38.5%, 95% CI 17.7-64.5%)**. Under the rule written before the data, no arm comparison counts. The numbers are given below for the record only.

## What was built (all three briefed changes)

1. **Pairwise within-fire judge** (forced choice, A/B order randomised per pair, the standard 3-judge panel): "which next thought engages the specific concern the reflection raised more". Instrument checks run first: negative control (own baseline vs a MISMATCHED fire's baseline) and a null pair (baseline sample 1 vs baseline sample 2).
2. **Live-like seed**: the mid-thread block plus 'Travis is here with you', a scene line, a mood line, the 'Since you last spoke ... wandered' block and an open-book line (wording from live code, shapes measured from `prompt_budget_shadow.jsonl`: median 7 parts, ~2.6k chars), plus an associative-recall block of 3 real grounded fragments (read-only from the live memory DB, nearest to the last step, timestamp before the fire). Scene/mood/book are fixed representative instances; the retraction block is omitted.
3. **2 samples per arm per fire** (baseline / cup / shuffled-control), 15 fires (16 requested; one case did not complete), 90 generations, 120 pairwise judgements.

## Numbers (read as unreadable, see verdict)

| check / comparison | n judged | x wins | rate (95% Wilson CI) |
|---|---|---|---|
| **negative control: mismatched beats own baseline** (gate <= 11%) | 13 | 5 | **0.385 (0.177-0.645) -- FAIL** |
| null pair: first-position (A) wins | 14 | 7 | 0.50 -- no position bias |
| CUP beats BASELINE | 28 | 13 | 0.464 (0.295-0.642) |
| CONTROL beats BASELINE | 29 | 16 | 0.552 (0.375-0.716) |
| CUP beats CONTROL | 30 | 13 | 0.433 (0.274-0.608) |
| CUP beats CONTROL, no cue echo | 27 | 13 | 0.481 (0.307-0.660) |

Rumination guard (unaffected by the instrument problem): mean restate_sim baseline 0.614 / cup 0.593 / control 0.572; early-close proxy 0.034 / 0.0 / 0.033. No rise from the cup. Cue echo (thought literally says 'doubt'/'point N'): cup 0%, control 10% (v1 had ~28%).

## Reading it

- **The judge cannot tell a thought that follows the fire from a thought that does not.** A random other fire's thought beats the real next thought 38% of the time. The v1 failure (30% on the absolute verdict) was not fixed by going pairwise on this seed. The null pair is balanced (50% by position), so this is not position bias; it is the two candidates being equally (un)related to the reflection.
- **Why that is plausible, not just noise.** With the realistic seed (scene, recall, wander items competing) the baseline next thought mostly continues the scene and the thread's imagery, not the particular doubt (the live counterfactual F-2604 found 1 affected of 16). When neither candidate engages the concern, a forced choice is a coin flip; the rates above (46% / 55% / 43%) are all inside noise of 50%. The v1 ceiling (97%) was therefore a property of the bare seed; the v2 floor is a property of the live-like seed. Neither seed gives the judge a contrast to measure.
- **A bare coordinate has little to carry.** In every sampled fire the 'true' ledger index is the LAST point of the ledger (index == ledger length, because the reflection fires on the latest step), so 'point {i} was doubted' only says 'the latest point'. Cup thoughts did not echo it (0% cue echo): the model gave it no weight, so the cue did not even become the vocabulary the judge might have latched onto.
- **What this does and does not show.** It does not show the coordinate can carry the concern (no win-rate lower bound above 50%), and it does not show it cannot: the instrument failed its own gate, so the comparison is unreadable. It narrows the problem: the missing piece is an instrument that can be shown sensitive, not another run of this one.

## Caveats and confounds

- **Generator is gemma4:12b (:11439), not the live qwen3.5:9b** -- the hot hub (Du's voice) was off limits. Judges (mixtral / falcon / granite) are a different family from the generator.
- **Du was running** and shares the CPU judge hubs; generation ran ~45-100 s/sample, slower during Du load. Calls were sequential with a 1 s pause. One baseline sample failed ('all servers exhausted'); its pairs have no verdict.
- A second `gen` process was started by mistake for ~12 minutes and wrote 3 fires twice; first copy kept, dedupe in the loader. Does not change the sample.
- Small n: 15 fires, 13 judged negative-control pairs; wide intervals throughout. The condensed system prompt (not the live one) and the representative scene/mood/book strings are the main fidelity gaps.

## Next (spawned)

A **positive control**: for each fire, a synthetic next thought written to take up the doubt explicitly (and a matched-length synthetic that does not), to show the pairwise judge can separate engagement from topic at all; if it cannot, the judge needs a different formulation (reflection-quoting rubric, or an embedding-free lexical-overlap-masked check) before any cup read is meaningful.
