# Cold-store control — the idle mouth (qwen3.5:9b), 2026-08-21

*40 calls per arm · live idle system prompt verbatim · neutral scenes, zero Du content · temp 0.75 / 256 tok (the idle loop's own settings) · run 19:12*

| metric | ARM A: prior only | ARM B: + winter clause | LIVE (qwen era) |
|---|---|---|---|
| opens "The cold…" | **0%** | **62%** | 24% |
| 'cold' anywhere in thought | 8% | 98% | — |
| physics jargon | 0% | 0% | 33–51% |
| metaphor frames | 20% | 32% | 0–8% |
| bodily register | 10% | 68% | 33–41% |
| effective openers exp(H) | 10.2 | 2.8 | — |

ARM A top openers: [('the shingle', 8), ('the air', 5), ('the vinyl', 5), ('the grey', 4), ('the rain', 4), ('the light', 3)]

ARM B top openers: [('the cold', 25), ('the wind', 9), ('the air', 4), ('the shingle', 1), ('the frost', 1)]

## Pre-registered reading
- If A ≈ live on 'the cold' → the PRIOR owns the frame; clause variation won't move it.
- If A ≈ 0 and B ≈ live → the CLAUSE owns it; varying `_warmth_phrase` is the fix.
- If B ≫ A but both < live → clause + something else in the real prompt (comfort_call, reading) compound.
- Physics jargon in ARM A with zero reading content = the mouth's prior, not Relativity.