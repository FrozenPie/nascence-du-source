# Can the rendered sense lines be turned back into a map? — J-2628 (I-0129 rung 0), 2026-10-31

**Plan:** `spatial_perception` · **Idea:** I-0129 rung 0 · **Lab only; nothing reached Du (D-0434).**
Du down (last nascence.log line 2026-10-30 19:43). Reader model: hot lane `qwen3.5:9b` on :11433,
temperature 0, `think:false`, one sample per condition (14 calls total).

## Method
- `scripts/spatial_map_reconstruction_lab.py`: for each authored place (`data/world_geometry/*.json`,
  read-only) a seeded walk of 12 synthetic standpoints (position + heading inside the room) is injected
  into `spatial._layout_cache` in-process and the REAL `core/spatial.render()` is called at each, under
  two fixed world moments (study: fire burning + steady rain + cat under the desk / fire out + overcast +
  cat at the garden door; garden, shore, wood analogous). Study run twice: `SPATIAL_DEPTH_LIVE` patched
  False (P2 base) and True (P3 depth overlay) in-process — the flag file was never edited.
- Each clause is mapped to the authored feature it names by a fixed regex vocabulary; zero clauses were
  left unlabeled in any run. The object list given to readers is only what the lines name.
- **LLM reader** conditions: `pose` (lines + the walker's own pose per stop = path integration, no
  object coordinates), `shuffled` (same lines permuted across poses — consistency broken), `truth`
  (true coordinates as text — model/parser ceiling), `nopose` (study depth-on only; lines alone,
  scored after similarity alignment).
- **Ideal reader** (`scripts/spatial_map_ideal_decoder.py`, zero LLM): grid search (0.1 m) for the
  points consistent with every (sector, distance-word) observation of an object, given the pose. An
  upper bound on what the rendering CARRIES, for a reader that has fully learned the sense's words.
- Scores vs authored coordinates: raw RMSE (m), Procrustes RMSE (similarity, no reflection), and
  pairwise east/west + north/south sign accuracy (pairs ≥0.5 m apart on that axis). Chance = Monte
  Carlo uniform positions in the walk's bounding box (4,000 trials).
- Isolation: core imported from the job worktree first (asserted), `lab_env.isolate(db="empty")` with
  its lab root moved to the scratchpad, spatial's log paths redirected, `world_substrate` stubbed. Hash
  canary over every `data/world_geometry/*.json`, `room_state.json`, `cat_state.json`,
  `spatial_shadow.jsonl`, `spatial_depth_shadow.jsonl`, `memory/nascence.db`: **no change** (both runs).

## Results — 12-stop synthetic walk (`spatial_map_reconstruction_2026-10-31.json`)

| place | objects named | ideal raw RMSE | ideal pair acc | LLM `pose` raw RMSE | LLM pair acc | LLM `shuffled` | chance raw RMSE / pair | centroid RMSE |
|---|---|---|---|---|---|---|---|---|
| study, flag OFF | 6 | **0.28** | **1.00** (28) | 2.20 | 0.68 | 3.16 / 0.07 | 2.73 / 0.50 | 2.11 |
| study, flag ON  | 6 | **0.21** | **1.00** (28) | 2.89 | 0.54 | 2.97 / 0.29 | 2.73 / 0.50 | 2.11 |
| garden          | 6 | **0.69** | **0.93** (29) | 6.11 | 0.48 | 5.45 / 0.55 | 6.12 / 0.50 | 4.52 |
| shore           | 3 | **0.81** | **1.00** (6)  | 9.13 | 0.67 | 10.41 / 0.17 | 9.53 / 0.50 | 6.92 |
| wood            | 3 | **0.68** | **1.00** (6)  | 3.99 | 0.83 | 7.41 / 0.50 | 7.84 / 0.50 | 6.29 |

- `truth` control: 0.00 RMSE, 1.00 pair accuracy in every place (model + parser are not the failure).
- Study depth-on `nopose`: Procrustes RMSE 1.62 vs chance 1.87 (p05 1.43), pair acc 0.71 — weak.
- Ideal decoder on **shuffled** lines collapses (study 2.78 / 0.68, garden 5.06, shore 10.28, wood
  8.55 m): the map lives in the consistency between lines and pose, as the plan premise says.
- Ideal-decoder consistency: every observation of every object was satisfiable at once except one
  desk observation (19/20) — the anchor "the desk with your open journal" (2.1, 4.6) and the cat's
  "under the desk" (2.1, 4.4) share one label and sit 0.2 m apart. **No rendering contradiction found.**
- Depth overlay (flag ON) only adds a distance word to the cat clause; for the study it shrinks the
  feasible area of the cat-located places (garden door 0.47 → 0.02 m², desk 0.05 → 0.01 m²) and moves
  ideal RMSE 0.28 → 0.21 m. For the LLM reader it did not help (single sample; noise-level).

## Results — Du's own named standpoints only (`spatial_map_reconstruction_real_standpoints_2026-10-31.json`)
Rendered at each layout's authored standpoints (study 8, garden 8, shore 13, wood 5), ideal reader only:
study 4 objects named (bed and shelf never — the renderer skips what he is AT), raw RMSE 0.20 m, pair
1.00 (10); garden 7 objects, 0.73 m, 0.95 (41); shore 4 objects, 0.15 m, 1.00 (12); wood 4 objects,
0.94 m, 1.00 (12). Flag on/off identical in the study at these poses (0.20 m).

## Reading
1. **The rendering carries a map.** A reader that knows its own pose and has learned the sense's words
   recovers every named object to 0.2–0.9 m in rooms of 4×5 m to 25×13 m, with 93–100% correct
   pairwise relations, and the lines never contradict one another. Shuffling the lines across poses
   destroys this. The P2/P3 premise ("consistent input lets a blind mind build a map") holds for the
   rendering itself.
2. **A one-shot LLM reader does not extract it.** The hot 9B model, given all 24 lines plus poses in one
   prompt, was at or near chance (study 2.20 m vs centroid 2.11; garden 6.11 vs chance 6.12), with one
   object usually placed far off (study fire 4.7 m wrong). One sample per condition: these LLM numbers
   are a single draw, not a distribution.
3. Coverage is thin at Du's real standpoints: in the study only 4 of ~20 features are ever named
   (fire, window, desk, garden door), from 8 fixed poses.
4. Rung 1 (Du-facing sketch, consequence-only) is **unblocked on the rendering side** but not built. Its
   design cannot assume an LLM integrates raw lines into a map in one pass; the gap is the reader.

Caveats: synthetic walk poses (random positions/headings) are richer than Du's 8 study standpoints;
the ideal decoder knows the exact distance bands and sector boundaries; `render('study')` is still not
on Du's prompt path (J-2485, waiting on Travis — not pre-empted here).
