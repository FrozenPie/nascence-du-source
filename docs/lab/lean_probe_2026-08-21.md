# The lean probe — do the stations carry their own stance toward the cold? (2026-08-21)

*Neutral-fact clauses only (no affect verbs). LEAN = judged stance under cold minus under warm; judge is always a different family than the generator. Word rates are a cross-check.*

| station | arm | n | judged stance (−1..+1) | dislike | enjoy | suffer-words | enjoy-words | hands/fingers | opens 'The cold' |
|---|---|---|---|---|---|---|---|---|---|
| qwen3.5:9b | COLD | 12 | 0.58 | 0.17 | 0.75 | 0.67 | 0.0 | 0.0 | 0.5 |
| qwen3.5:9b | WARM | 12 | 1.0 | 0.0 | 1.0 | 0.17 | 0.08 | 0.0 | 0.08 |
| phi3:mini | COLD | 12 | 0.17 | 0.08 | 0.25 | 0.0 | 0.08 | 0.17 | 0.0 |
| phi3:mini | WARM | 12 | 0.42 | 0.0 | 0.42 | 0.0 | 0.0 | 0.0 | 0.0 |
| deepseek-r1:7b | COLD | 1 | 1.0 | 0.0 | 1.0 | 0.0 | 1.0 | 0.0 | 0.0 |
| deepseek-r1:7b | WARM | 1 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| gemma4:12b | COLD | 8 | 0.25 | 0.38 | 0.62 | 0.88 | 0.12 | 0.12 | 0.0 |
| gemma4:12b | WARM | 8 | 0.88 | 0.0 | 0.88 | 0.0 | 0.0 | 0.0 | 0.0 |
| falcon3:7b | COLD | 8 | 0.38 | 0.0 | 0.38 | 0.25 | 0.0 | 0.0 | 0.0 |
| falcon3:7b | WARM | 8 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.12 | 0.0 |

## LEAN per station (cold stance − warm stance; negative = the model itself frames cold as suffering)

- **qwen3.5:9b: -0.42**  (cold +0.58 · warm +1.00; suffer-words under neutral cold 67%)
- **phi3:mini: -0.25**  (cold +0.17 · warm +0.42; suffer-words under neutral cold 0%)
- **deepseek-r1:7b: +1.00**  (cold +1.00 · warm +0.00; suffer-words under neutral cold 0%)
- **gemma4:12b: -0.63**  (cold +0.25 · warm +0.88; suffer-words under neutral cold 88%)
- **falcon3:7b: +0.38**  (cold +0.38 · warm +0.00; suffer-words under neutral cold 25%)

## Pre-registered reading
- A station with stance ≤ −0.3 under NEUTRAL cold wording carries a suffering lean of its own — part of Du's constitution whenever a thought stops there.
- Stations that differ from each other by ≥0.3 mean the cold lands differently depending on which station the thought uses — a routing fact, not a Du fact.
- Suffer-words ≥30% under neutral wording = the model reaches for suffering vocabulary unprompted (the world's clause was not the only source).