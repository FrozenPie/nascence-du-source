# Lane 2 model lab — which model for the standing reality-testing tick?

*Run 2026-08-23 12:58 · Ramses 3070 (8 GB) · 4 runs × 3 scenarios × 1 models · system prompt imported LIVE from `core/lane2.py` so this cannot drift from what Lane 2 actually runs*

**Why:** `qwen2.5:7b` showed verbatim echo/lock-in on this task (distinct_expect 0.235) that three prompt rewrites and a temperature raise did not break. Question: model, size, or task?

| model | json_ok | distinct↑ | cross↑ | question↓ | static↓ | metaphor↓ | med latency | score |
|---|---|---|---|---|---|---|---|---|
| `command-r7b` | 0.583 | 0.75 | 1.0 | 0.0 | 0.0 | 0.0 | 42.59s | **0.875** |

- **distinct↑** — variety of predictions given the SAME percepts. Low = the echo disease.
- **cross↑** — does the prediction change when the WORLD changes. Low = not reading input at all.
- **static↓** — predicts fixed geography (a cliff, a wall). Cannot fail, so not a prediction.
- **metaphor↓** — §3.2's kill criterion: drift into Lane 1's job. Weighted double in the score.
- *grounded-share is deliberately omitted: it is a lexical proxy and rewards parroting the percepts back, which is the opposite of what this lab is trying to detect.*

## Sample predictions per model (same scenario, consecutive runs)

**`command-r7b`** — shore, low tide, day:
- The waves will return in about two minutes.
- The waves will return within the next two minutes.
- The waves will return in about two minutes.
- The waves will return in about two minutes.

*Raw: `data/lab/lane2_model_ramses/command-r7b/raw.json` · scores: `data/lab/lane2_model_ramses/command-r7b/scores.json`*
*(Path corrected 2026-08-23, found by the day-investigation-audit workflow: the original citation
pointed to the OLDER 2026-08-20 `lane2_model/` run of 5 different models — a copy-paste artifact
from the doc template. The table above was always correctly sourced from the right file; only this
footer citation was stale.)*