# Model-tier lab #6 — core.composition grading (left_lane.grade_work)

*Run 2026-08-29 16:18 · J-0284 (source: decision:D-0013) · 8 real (task, piece) pairs from `data/composition_log.jsonl` (35-row real history) x 2 models · system = `emissary.constitution() + _WORK_GRADE_TASK`, both imported LIVE from `core/left_lane.py`/`core/emissary.py`.*

## Checked first, per the scope's own instruction: does an existing lab already cover this?

`data/lab/station_bench/scores.json`'s `ground` station has both models on record already: `gemma4:12b` and `mixtral:8x7b_ramses` BOTH score a perfect `groundedness=1.0, cites_valid_ids=1.0, json_ok=1.0`. A task both models ace identically gives zero signal about which is the better JUDGE — the station_matrix.md constant-answer/ceiling trap, here on an evidence-citing EXPLAIN task that isn't even the same shape as grading a WRITTEN PIECE against a task. **Existing data does not cover this shape** — hence the small real-case check below (deliberately small: row 6 is the lowest-urgency mechanism in the scope doc).

| model | mean grounded | spread (max-min) | distinct scores (of 8) | corr vs. historical gemma4 score | format_ok/8 | median latency |
|---|---|---|---|---|---|---|
| `gemma4:12b` | 0.938 | 0.3 | 3 | -0.075 | 8/8 | 59.6s |
| `mixtral:8x7b` | 0.85 | 0.15 | 3 | 0.359 | 8/8 | 14.1s |

- **spread / distinct scores** — the discrimination check: does the judge actually vary its score across 8 genuinely different real pieces (kinds mixed, historical score 0.6-1.0), or does it collapse toward one constant number (the exact failure mode a judge that scores differently on paper but the same in practice would hide).
- **corr vs. historical** — each real piece already carries the score gemma4:12b actually gave it in production at the time. This checks whether a RE-run of gemma4:12b today reproduces its own past verdicts (sanity check on judge stability) and whether mixtral's verdicts track the same real quality signal or diverge.

## ★ Data-hygiene catch: one 'historical score' in the log is not a real judge verdict

Case idx=33 (`describe`, hist_score=0.6) carries `feedback=""` in the real log — that is `core/composition.py:61`'s hardcoded FAIL-OPEN default (`score, feedback = 0.6, ""`), used when `left_lane.grade_work()` returned `None` that day (Ramses/judge-1 unreachable), not an actual judge score. All 7 other cases here have real historical feedback text, i.e. were genuinely graded. Re-running the correlation excluding this one non-judged case: gemma4:12b corr=0.133, mixtral corr=0.228 (both still weak — see below, this is not the main finding here, the ceiling effect is).

## What the real numbers actually say

Both models land in a mostly-lenient, low-variance band on these 8 real pieces (gemma4:12b spread 0.3, mixtral 0.15) — neither correlates strongly with the historical gemma4:12b score (0.133 / 0.228 excluding the fail-open case above), but with only 7-8 real points and most historical scores already clustered at 0.8-1.0, that is a genuinely weak, `inferred`-not-`verified` signal, not evidence either judge is unstable. The one clear, real, actionable difference: **mixtral is ~4x faster** (median 14.1s vs 59.6s) while landing in a slightly tighter, marginally stricter band — on this small sample, a plausible latency win with no clear quality cost, but not a strong enough signal on its own to justify a judge-seat move for the LOWEST-urgency mechanism in the scope. Worth a larger real re-run before any change; not worth building a bigger lab for on current urgency.

## Raw grades (all 8 cases, both models)

| idx | kind | hist score | `gemma4:12b` grounded | `gemma4:12b` feedback | `mixtral:8x7b` grounded | `mixtral:8x7b` feedback |
|---|---|---|---|---|---|---|
| 33 | describe | 0.6 | 1.0 | The work is highly grounded, utilizing specific textures and sensory details; th | 0.8 | Great job describing the weather and the room with vivid, exact details! Conside |
| 3 | narrate | 0.8 | 1.0 | The work is highly grounded in physical sensory details, specifically the tactil | 0.8 | Good job describing specific, real things from your day. For next time, try to i |
| 6 | argue | 0.8 | 0.7 | The claim is clear and addresses a specific educational policy, but the paragrap | 0.8 | Strong focus on the argument against mandatory standardized testing, but could b |
| 16 | describe | 0.8 | 1.0 | The work is highly grounded, utilizing specific colors, materials, and textures  | 0.95 | Strong use of vivid and specific details, but could improve by specifying the ty |
| 24 | explain | 1.0 | 0.8 | The description of the mechanical chain and gear relationship is concrete, but t | 0.8 | Great job explaining the mechanical function, but consider adding more real-worl |
| 27 | describe | 1.0 | 1.0 | The work is highly grounded in sensory specifics like 'wet wool' and 'grinding s | 0.95 | Strong use of vivid and exact details to create a clear image of the scene. One  |
| 29 | narrate | 1.0 | 1.0 | The work is highly grounded, providing specific times, quantities, and sensory d | 0.9 | Great job capturing specific details of the day! Consider adding even more senso |
| 0 | narrate | 0.9 | 1.0 | The response is perfectly grounded in the literal mechanism of the system's oper | 0.8 | Strong focus on specific actions and time, but lacks sensory details or personal |

*Raw: `data/lab/model_tier/composition/raw.json` · scores: `scores.json`*