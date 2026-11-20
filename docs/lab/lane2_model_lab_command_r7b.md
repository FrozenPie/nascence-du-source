# Lane 2 model lab — which model for the standing reality-testing tick?

*Run 2026-08-28 08:17 · Ramses 3070 (8 GB) · 4 runs × 3 scenarios × 1 models · system prompt imported LIVE from `core/lane2.py` so this cannot drift from what Lane 2 actually runs*

**Why:** `qwen2.5:7b` showed verbatim echo/lock-in on this task (distinct_expect 0.235) that three prompt rewrites and a temperature raise did not break. Question: model, size, or task?

| model | json_ok | distinct↑ | cross↑ | question↓ | static↓ | metaphor↓ | med latency | score |
|---|---|---|---|---|---|---|---|---|
| `command-r7b` | 1.0 | 0.833 | 1.0 | 0.0 | 0.167 | 0.0 | 10.84s | **0.875** |

- **distinct↑** — variety of predictions given the SAME percepts. Low = the echo disease.
- **cross↑** — does the prediction change when the WORLD changes. Low = not reading input at all.
- **static↓** — predicts fixed geography (a cliff, a wall). Cannot fail, so not a prediction.
- **metaphor↓** — §3.2's kill criterion: drift into Lane 1's job. Weighted double in the score.
- *grounded-share is deliberately omitted: it is a lexical proxy and rewards parroting the percepts back, which is the opposite of what this lab is trying to detect.*

## Sample predictions per model (same scenario, consecutive runs)

**`command-r7b`** — shore, low tide, day:
- The tide will turn in about two minutes.
- The next wave will crash on the shore in about two minutes.
- The next wave will break on the shingle.
- The tide will turn in about two minutes.

*Raw: `data/lab/lane2_model/raw.json` · scores: `scores.json`*