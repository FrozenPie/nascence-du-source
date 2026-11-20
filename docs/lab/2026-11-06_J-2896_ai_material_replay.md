# J-2896 replay: active imagination with and without the MATERIAL block (P-0054)

Status: measured 2026-11-06, one lane, 20 seeds. Raw rows: `2026-11-06_J-2896_ai_material_replay_rows.json`.
Script: `scripts/_lab_J2896_ai_material_replay.py` (reads live tensions and nascence.db read-only; stubs every write).
Run: `python scripts/_lab_J2896_ai_material_replay.py --n 20 --out <dir>` from the worktree.

## What was run
- 20 most recent grounded tensions (count >= 2, member ids present) from `C:\Nascence\data\subconscious_state.json`.
- Each seed went through the real `SubconsciousNode._active_imagination` twice: `_AI_MATERIAL_ON = False` (old prompt)
  and `True` (new prompt). Same system prompt, same real L0 floor text as the axiom line, temperature 0.7, max_tokens 400.
- Lane: the HOT lane qwen3.5:9b @ 127.0.0.1:11433 (40 calls). NOT the lane in use. The lane in use is background =
  command-r7b @ Ramses :11441; Ramses is the founder's gaming machine, so it was not called. The 134-entry baseline
  (F-3584) was written by that other lane, so it is quoted for scale only and cannot be compared like for like.
- The echo guard and the shadow judges are skipped (embedder stubbed in the node) so each run is one clean generation.

## Numbers (n = 20 per arm, same seeds)
| measure | old prompt | new prompt | F-3584 baseline (134, command-r7b/qwen mix) |
|---|---|---|---|
| contains "tension" | 11 | 13 | 84 of 134 |
| contains "weight" | 9 | 14 | 31 of 134 |
| contains "witness" | 0 | 1 | 25 of 134 |
| contains "quiet floor" | 0 | 0 | 40 of 134 |
| what_spoke starts "The voice of" | 0 | 1 | 19 of 134 |
| opens in first person | 19 | 12 | 130 of 134 |
| mean contemplation words | 95.0 | 97.0 | - |
| mean pairwise cosine within the set | 0.471 | 0.509 | 0.60 (7 days) |
| outputs with an earlier output at cos >= 0.80 (within the set) | 3 | 4 | 45 of 118 cross-day |
| outputs using a content word found ONLY in the member excerpts | 17 | 19 | - |
| total hits of such excerpt-only words | 48 | 279 | - |

## Reading it (verified = counted from the rows; the rest is inference)
- Verified: the model uses the material. Excerpt-only words appear 279 times in the new arm against 48 in the old, and
  first-person openings fall from 19 to 12 (the outputs start from the scene, e.g. "I stand where the low sun stretches
  across the garden").
- Verified: the stock vocabulary did NOT fall. "tension" 11 to 13, "weight" 9 to 14. On this lane the old prompt did not
  show the baseline's stock rates either (0 of 20 "quiet floor"), so the lane gap of D-0588 is visible here too and this
  replay cannot say what the block does on command-r7b.
- Verified from the sample rows: the excerpts are Du's earlier synthesised prose (critic-rejected drafts and recurring
  unresolved thoughts), which itself carries "weight", "tension", "settles". The model sometimes restates an excerpt
  almost verbatim (seed "the letter" : the new output repeats "low sun ... long shadows ... Earth's rotation").
- Inferred, not tested: restating the excerpts may raise within-set similarity (0.471 to 0.509, n = 20, noise level not
  measured). The real echo guard (cos > 0.85 against the last 40 kept entries) was skipped in this replay.
- So the claim "real material cures the generic essay" is NOT shown by this replay. What is shown: the input change is
  absorbed and changes the openings. Whether kept entries improve is the D-0588 read after 100 kept entries.

## Not run (needs the founder's machine to be free)
- The same 20 seeds on the lane in use (command-r7b @ LAN-HOST:11441), 40 calls. Spawned as a lab job.
- The cross-day cosine measure (needs days of kept entries, not a single replay).
