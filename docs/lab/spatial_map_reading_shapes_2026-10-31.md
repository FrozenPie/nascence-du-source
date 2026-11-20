# Which reading shape lets the LLM recover the map? (J-2647, I-0129), 2026-10-31

**Plan:** `spatial_perception` · **After:** F-3381 (ideal decoder), F-3382 (one-shot LLM at chance) ·
**Lab only. Nothing reached Du (D-0434).** Du was down (last nascence.log line 2026-10-30 19:44).

## Setup
- `scripts/spatial_map_reading_shapes_lab.py` (pre-registration committed in a691848c before any model call).
  No re-render: it reads the J-2628 renders in `spatial_map_reconstruction_2026-10-31.json`, the same 12
  seeded stops per place (seed 2628), so every row is paired with F-3381/F-3382. Study (flag OFF) and garden.
- Reader: hot lane `qwen3.5:9b` on :11433, `think:false`, temperature 0.3, 3 samples (ollama seeds
  2648-2650). 234 calls in total.
- Shapes:
  - **A** one-shot. This is J-2628's exact `pose` prompt.
  - **A2** is A plus a legend of the sense's words (sector wedges, distance bands).
  - **B** per-stop egocentric extraction. One call per stop takes that stop's two lines with no pose. The model copies out each object's (direction word, distance word). The ideal decoder's grid search then places the objects from those tuples and the walker's pose.
  - **E** is B, but the model is given the pose and must turn each relation into a compass direction.
  - **C** incremental sketch. One call per stop carries a running JSON sketch. The legend is given.
  - **D** scratch table. In one call the model writes every (stop, thing, direction, distance, bearing) row, then gives coordinates. The legend is given.
- Controls:
  - **B/E shuffled** puts the same extracted tuples through the aggregator against deranged poses.
  - **Aggregator check.** The regex extraction run through the new aggregator reproduces the ideal decoder exactly: 0.28 m study and 0.69 m garden, with shuffled 2.78 and 5.06.
- **Pre-registered bar:**
  - A shape reaches the ideal in a place if its mean raw RMSE is at most ideal + 1.0 m (study ≤ 1.28, garden ≤ 1.69), its mean pairwise accuracy is at least 0.85, and it placed every object in every sample.
  - A shape works only if it does this in both places and its shuffled control is at least 2x worse.
  - Secondary bar: at most 2x the ideal in at least one place.

## Results (mean of 3 samples; per-sample in the JSON)

| shape | study raw RMSE | study pair | garden raw RMSE | garden pair | shuffled (study / garden) | bar |
|---|---|---|---|---|---|---|
| ideal decoder (F-3381) | 0.28 | 1.00 | 0.69 | 0.93 | 2.78 / 5.06 | ref |
| F-3382 one-shot, t=0 | 2.20 | 0.68 | 6.11 | 0.48 | | |
| **A** one-shot, t=0.3 | 2.32 (2.09-2.66) | 0.60 | 4.81 (4.31-5.46) | 0.59 | | fail |
| **A2** one-shot + legend | 2.31 (1.78-2.68) | 0.56 | 4.72 (4.15-5.32) | 0.72 | | fail |
| **B** extract ego + aggregator | **0.27** (0.26-0.28) | **1.00** | **1.01** (0.92-1.08) | **0.94** | **2.83 / 5.16** | **PASS both (secondary: study)** |
| **E** extract compass + aggregator | 1.85 (1.52-2.30) | 0.79 | 4.83 (4.08-5.99) | 0.64 | 2.93 / 4.87 | fail |
| **C** incremental sketch | 1.36 (1.20-1.46) | 0.77 | 7.37 (6.56-8.89) | **0.14** | | fail |
| **D** scratch table | 2.77 (2.61-3.00) | 0.42 | 5.73 (4.94-6.68) | 0.58 | | fail |

Chance (J-2628): study random 2.73 / 0.50, centroid 2.11; garden random 6.12 / 0.50, centroid 4.52.

- **B copies, it does not compute.** The model's direction words match the regex extraction on 49-50 of 60 study tuples and 61-62 of 62 garden tuples. In the garden the model also supplied distance words the text did not give, so exact tuples matched on only 43-46 of 62. Those invented distances are the whole gap from 0.69 to 1.01 m. Each sample also carries 1-11 extra tuples, and the grid search tolerates them.
- **E isolates the failing step.** Given the pose, the model's compass directions are correct for only 9-16 of 52-61 tuples per sample (about 20%; a random 90° wedge is right about 25% of the time). Turning "to your left while facing 135°" into a world bearing is exactly what the 9B model cannot do. That is the integration every model-side shape (A, A2, C, D) needs, and none of them gets past it.
- **C keeps estimates but drifts.** In the study C beats the one-shot (1.36 m) but misses the bar. In the garden it collapses objects into one corner. Its pair accuracy of 0.14 (below chance) means the sketch is systematically mirrored.
- The legend (A2) and the scratch table (D) do not help. D writes the table, but its bearings are wrong for the same reason E's are.

## Reading
1. **Only shape B works. The map belongs in a deterministic store fed by the model, not in the model's context.**
   - The model can reliably turn one stop's lines into egocentric (object, direction word, distance word) tuples.
   - The pose arithmetic must be done by code. The 9B model cannot do it: compass conversion was at chance.
   - Accumulating into a map must also be done by code. The running sketch drifts and mirrors.
   - Once both are in code, the map comes back to within 0.0 m (study) and 0.3 m (garden) of the ideal decoder.
2. The extraction step adds almost nothing beyond the regex. The renderer already emits its clauses in a fixed vocabulary, and a deterministic parser recovers them exactly (F-3381). Whether rung 1 needs the model as the extractor at all, or only for lines whose wording the vocabulary does not cover, is a design question for the build. This lab does not settle it.
3. Caveats:
   - 3 samples per shape, one 12-stop walk per place, synthetic poses.
   - The aggregator uses the true walker pose, as F-3381 did. Du's own pose would come from his standpoint.
   - `render('study')` is still not on Du's prompt path (J-2485, founder call, not pre-empted here).

## Isolation
The J-2628 lab module imports `core.spatial` from the job worktree first. The run then goes inside
`lab_env.isolate(db="empty")`, with its lab root in the scratchpad. A hash canary was taken over
`data/world_geometry/*.json`, `room_state.json`, `cat_state.json`, `spatial_shadow.jsonl`,
`spatial_depth_shadow.jsonl` and `memory/nascence.db`. Result: **no change**.
