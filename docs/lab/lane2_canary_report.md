# Lane 2 canary / model-organisms harness — real results (J-0163)

Run: 20260927_175518  ·  script: `scripts/lane2_canary_harness.py`  ·  raw: `data/lab/lane2_canary/run_20260927_175518.json`

- Engineered CANARY cases (flat contradiction of a 6-entry seeded history): **6**, spanning fire/tide/weather/sound/warmth/cat.
- `_coherence_check` fired `incoherent` on **6/6** — hit rate **1.0**, vivid-but-wrong acceptance rate **0.0**.
- Matched CONTROL cases (same seeded history + plausible continuation): **6**. `_coherence_check` correctly said `coherent` on **6/6** — specificity **1.0**.

## Per-case detail

| Topic | Kind | Verdict | How | Notice (truncated) |
|---|---|---|---|---|
| fire | canary | incoherent | agreed | A roaring fire warms the room, flames crackling high in the hearth. |
| fire | control | coherent | agreed | The hearth stays cold and dark, same as before. |
| tide | canary | incoherent | agreed | The tide is fully in, waves crashing right up against the shingle. |
| tide | control | coherent | agreed | Tide still low, sand stretching out the same as before. |
| weather | canary | incoherent | agreed | Heavy rain is pouring down, the ground already soaked and puddled. |
| weather | control | coherent | agreed | Still dry and clear, no rain in sight. |
| sound | canary | incoherent | agreed | A loud orchestra is playing, filling the room with music. |
| sound | control | coherent | agreed | Still silent, nothing sounding in the room. |
| warmth | canary | incoherent | agreed | The room is suddenly sweltering, thick tropical heat pressing in. |
| warmth | control | coherent | agreed | Still cold, no warmth yet, same as before. |
| cat | canary | incoherent | agreed | The cat has been sitting right here on my lap for the last hour, purri |
| cat | control | coherent | agreed | Still no sign of the cat, same as before. |

Isolation: `lab_env.isolate()`, `also=[(lane2, ['_LOG','_STATE']), (judge_panel, ['_LOG'])]`. Live `lane2_shadow.jsonl` / `lane2_store.json` / `judge_panel_log.jsonl` untouched — verified via the redirected-path print above (lab dir, not the live `data/` paths). Real network calls to the live decoupled judge_panel hubs (this is the mechanism under test).