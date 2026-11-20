# Lane 2 model lab — which model for the standing reality-testing tick?

*Re-scored 2026-08-20 09:15 from the 2026-08-20 09:13 run · Ramses 3070 (8 GB) · 4 runs × 3 scenarios × 6 models · system prompt imported LIVE from core/lane2.py*

**Serves Shared Spine F (`docs/ROADMAP.md`): models are TOOLS, not personas — judge capability, never packaging.**

> **Two corrections make this table trustworthy where the first run was not.**
> **(1)** `deepseek-r1:7b` was first recorded *"UNUSABLE — no valid JSON"*. **False.** It emits
> VALID JSON inside a fenced code block, and needs a token budget large enough for a reasoning model
> to finish thinking before it emits content at all. Both were OUR failure to adapt, not its failure
> to perform — exactly the trap Spine F names. **It now scores first.**
> **(2)** A HEDGE metric was added after the first run. `phi3:mini` scored 0.944 and looked like
> the winner; it hedges **100%** of its predictions ("might", "could", "if X then maybe Y"), and
> every hedge is worded differently — which **inflated its variety score**. A prediction hedged into
> unfalsifiability fails exactly as a question does. Penalised, it drops to 4th.

| model | size | json_ok | distinct↑ | cross↑ | hedge↓ | static↓ | metaphor↓ | latency | score |
|---|---|---|---|---|---|---|---|---|---|
| `deepseek-r1:7b` | 4.36 GB | 0.917 | 1.0 | 1.0 | 0.273 | 0.0 | 0.0 | 6.28s | **0.932** |
| `qwen2.5:7b` | 4.36 GB | 1.0 | 0.833 | 1.0 | 0.0 | 0.333 | 0.0 | 1.62s | **0.833** |
| `llama3.1:8b` | 4.58 GB | 1.0 | 0.75 | 1.0 | 0.0 | 0.333 | 0.0 | 1.46s | **0.792** |
| `phi3:mini` | 2.03 GB | 1.0 | 1.0 | 1.0 | 1.0 | 0.167 | 0.0 | 1.07s | **0.708** |
| `mistral:7b-instruct` | 4.07 GB | 1.0 | 0.75 | 1.0 | 1.0 | 0.417 | 0.0 | 1.75s | **0.521** |
| `qwen3.5:4b` | 3.16 GB | 0.0 | — | — | — | — | — | — | **unusable — emits no content even at 1400 tokens** |

- **distinct↑** variety given the SAME percepts (the echo metric) · **cross↑** does it change when the WORLD changes
- **hedge↓** "might/could/if" — unfalsifiable, *and* it inflates distinct · **static↓** predicts fixed geography (cannot fail)
- **metaphor↓** §3.2 kill criterion, weighted double

## Verdict

**`deepseek-r1:7b`** — the only candidate combining full variety (1.0) with low hedging (0.27) and **zero** static predictions. Its cost is latency: ~6.3s vs ~1.5s. Against a 90s tick that is a ~7% duty cycle, so it is affordable. **Recommended for Lane 2.**

**On size — a correction worth keeping.** An earlier reading of this lab claimed score was inversely correlated with size. That was an artifact of the missing hedge metric: `phi3:mini` looked best because hedging inflated its variety. The honest finding is narrower and more useful: **fitness for task is not predicted by size in either direction.** The winner is mid-sized; the largest (`llama3.1:8b`) and the smallest both lost. Size stays a legitimate TIEBREAK where fitness is comparable — it is not itself evidence.

## Sample predictions (same scenario, consecutive runs)

**`deepseek-r1:7b`** — shore, low tide, day:
- The tide will come back within the next hour.
- The tide will come back within the next few minutes
- In the next few minutes, rain might cause changes in sound patterns.
- The waves on shingle will get stronger over the next few minutes.

**`qwen2.5:7b`** — shore, low tide, day:
- The gull cries will stop within the next few minutes.
- The sound of waves_on_shingle will diminish as the tide continues to recede.
- The sound of the waves will continue to be heard for the next few minutes.
- The gull cries will stop within the next few minutes.

**`llama3.1:8b`** — shore, low tide, day:
- The tide will come back in within the next hour.
- The tide will come back in within the next hour.
- the tide will come in within the next hour
- The tide will come back in within the next hour

**`phi3:mini`** — shore, low tide, day:
- In the next few minutes, a change in tide direction could prove this observation wrong.
- In the next few minutes, if there are any changes to these conditions such as waves starting coming back with incoming water due to high tide or different bird calls indicating their presence and behavior change.
- I expect to hear a change in sound within the next few minutes if the wind picks up or shifts direction.
- I anticipate hearing either 'waves_on_shingle', 'shingle_drag', 'gull_cries', or 'oystercatcher_call' as these are currently audible and may continue to be so in the immediate future.

*Raw: `data/lab/lane2_model/raw.json` · scores: `scores.json`*