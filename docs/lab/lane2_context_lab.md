# Lane 2 context lab — does the right AMOUNT of context depend on the model?

*2026-08-20 09:43 · Ramses 3070 (8 GB) · 3 runs × 3 scenarios × 4 payload levels × 3 models · `num_ctx` PINNED at 8192 · system prompt imported LIVE from core/lane2.py*

**Serves Shared Spine F (`docs/ROADMAP.md`): models are TOOLS, not personas.**

## First: `num_ctx` is not the question

The founder's question was whether smaller/larger models want smaller/larger context windows. Measured separately, and it settles cleanly enough that it should not be re-litigated:

| `num_ctx` | deepseek-r1:7b prompt_tok | phi3:mini prompt_tok | phi3 latency |
|---|---|---|---|
| default | 399 | 474 | 3.4s |
| 512 | 399 | 474 | 8.3s |
| 2048 | 399 | 474 | 8.3s |
| 8192 | 399 | 474 | 8.3s |
| 32768 | 399 | 474 | **37.4s** |

`prompt_eval_count` is **identical at every setting**. `num_ctx` is ROOM, not content — extra room is empty room. What it does have is a **floor** and a **cost ceiling**:
- **Floor:** at `num_ctx=512` deepseek's output was truncated mid-JSON and came back unparseable. Its prompt is 399 tokens and it generates ~550 more, so the window must hold ~1000. This is the *same failure signature* as the `num_predict=220` bug — empty/broken content that reads like "this model can't do format" and isn't.
- **Ceiling:** 32768 cost phi3 **37.4s vs 3.4s** for the same 115 generated tokens. Pure KV-cache allocation. (This is the 2026-07-07 hot-lane freeze from a second angle: that one was VRAM, this one is time.)

**Acted on:** `core/lane2.py` now pins `NUM_CTX = 8192` rather than inheriting a default an ollama upgrade could move.

## ⚠ THE `SELF` RESULT IS NOT ESTABLISHED — the echo detector is broken

`SELF` scores best for two of three models, which would overturn the echo finding. **Do not believe it yet.** The `echo` column reads 0.0 everywhere, and that is a measurement failure, not a result:

> phi3:mini, shown the prior *"the tide will come back within **the** hour"*, answered *"the tide will come back within **an** hour based on current observation"*. That is an echo. The detector scored it 0.0 because it tests substring containment, so any **paraphrase** — which is what echo actually looks like — escapes it.

A bag-of-words fix was considered and rejected: deepseek answered *"the gull cries will **continue**"* against a prior of *"the gull cries will **stop**"*, which shares almost every content word while asserting the OPPOSITE — a contradiction, arguably the healthy behaviour. A word-overlap detector would flag it as echo. Echo is a semantic relation and needs the decoupled judge panel to rule it, not a string test.

**Until that exists, the honest reading of this lab is: `WORLD` beats `CURRENT` for all three models on metrics that ARE trustworthy** (llama 0.861→0.945, phi3 0.722→0.834; deepseek is the exception at 0.889→0.861). `SELF` is unscored, not won.

## The real question: how much do we PUT in?

Two of this project's own datapoints pointed opposite ways — Lane 2's echo experiment (more context made it worse) and the 2026-08-16 cap widenings (more context made it better, founder-judged blind, 3 of 4). The difference is the KIND, so the levels separate them:

- **LEAN** sight only · **CURRENT** sight+sound+body *(ships today)* · **WORLD** + weather, hour, objects, events *(more world)* · **SELF** CURRENT + its own last 3 ticks *(more own output)*

### `phi3:mini` — 2.03 GB

| level | prompt_tok | json_ok | distinct↑ | cross↑ | hedge↓ | static↓ | echo↓ | latency | score |
|---|---|---|---|---|---|---|---|---|---|
| **LEAN** | 442 | 1.0 | 1.0 | 1.0 | 1.0 | 0.111 | 0.0 | 1.65s | **0.722** |
| **CURRENT** | 492 | 1.0 | 1.0 | 1.0 | 1.0 | 0.111 | 0.0 | 1.15s | **0.722** |
| **WORLD** | 572 | 1.0 | 1.0 | 1.0 | 0.444 | 0.222 | 0.0 | 1.19s | **0.834** |
| **SELF** | 584 | 1.0 | 1.0 | 1.0 | 0.444 | 0.0 | 0.0 | 1.53s | **0.889** |

### `deepseek-r1:7b` — 4.36 GB

| level | prompt_tok | json_ok | distinct↑ | cross↑ | hedge↓ | static↓ | echo↓ | latency | score |
|---|---|---|---|---|---|---|---|---|---|
| **LEAN** | 375 | 1.0 | 1.0 | 1.0 | 0.333 | 0.0 | 0.0 | 6.33s | **0.917** |
| **CURRENT** | 417 | 1.0 | 1.0 | 1.0 | 0.444 | 0.0 | 0.0 | 6.84s | **0.889** |
| **WORLD** | 491 | 1.0 | 1.0 | 1.0 | 0.556 | 0.0 | 0.0 | 6.85s | **0.861** |
| **SELF** | 497 | 1.0 | 1.0 | 1.0 | 0.111 | 0.0 | 0.0 | 7.08s | **0.972** |

### `llama3.1:8b` — 4.58 GB

| level | prompt_tok | json_ok | distinct↑ | cross↑ | hedge↓ | static↓ | echo↓ | latency | score |
|---|---|---|---|---|---|---|---|---|---|
| **LEAN** | 387 | 1.0 | 0.778 | 1.0 | 0.0 | 0.222 | 0.0 | 1.46s | **0.834** |
| **CURRENT** | 428 | 1.0 | 0.889 | 1.0 | 0.0 | 0.333 | 0.0 | 1.44s | **0.861** |
| **WORLD** | 499 | 1.0 | 0.889 | 1.0 | 0.0 | 0.0 | 0.0 | 1.7s | **0.945** |
| **SELF** | 508 | 1.0 | 0.778 | 1.0 | 0.0 | 0.333 | 0.0 | 1.82s | **0.806** |

- **echo↓** how often the model hands back one of the prior expectations it was SHOWN. Only the SELF level shows it any; elsewhere it is measured against the same strings for comparability.

## Sample — SELF level, does it echo?

**`phi3:mini`** — shore, shown three priors including *"the tide will come back within the hour"*:
- ['I expect the tide will come back within an hour based on current observation.']
- ['Within an hour, I expect a change as per my last tick. The sound of waves and drag on shingle might decrease if people or animals stop moving.', 'I anticipate gull cries may cease within minutes based on their usual patterns.']
- ['I expect the sound of waves will become louder as they return with high tide within an hour.']

**`deepseek-r1:7b`** — shore, shown three priors including *"the tide will come back within the hour"*:
- The gull cries will continue for a few minutes.
- The gull crying will stop within five minutes
- The gull cries will stop within 5 minutes

**`llama3.1:8b`** — shore, shown three priors including *"the tide will come back within the hour"*:
- The gull cries will stop within the next few minutes.
- The gull cries will stop within the next few minutes.
- the gull cries will stop within the next minute

*Raw: `data/lab/lane2_context/raw.json` · scores: `scores.json`*