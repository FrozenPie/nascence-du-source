# J-3128 / P-0104 replay of the 'seeded' active-imagination judge prompt (2026-11-06)

Script: `scripts/_lab_J3128_ai_judge_v2_replay.py` (direct POST, model `judge`, json format, temperature 0, num_predict 200; the same shape as
`core/judge_panel._ask` minus its telemetry write; nothing under `data/` touched). Cases: `docs/lab/P-0104/cases.json`, 20 real kept entries
(10 hand-labelled SPEC, 10 STOCK). Prompt: `nodes/subconscious_node._AI_JUDGE_V2_SYSTEM` ('seeded-v1'), one draft, no revision.

| hub | role | SPEC true (want >= 8/10) | STOCK true (want <= 3/10) | bar |
|---|---|---|---|---|
| falcon3:7b `127.0.0.1:11440` | the real JUDGE_2 | 10/10 | 3/10 (STOCK1, STOCK49, STOCK62) | PASS (at the edge) |
| gemma4:12b `127.0.0.1:11439` | local STAND-IN for mixtral (not a judge today) | 9/10 | 0/10 | pass, but not the real family |
| mixtral:8x7b `LAN-HOST:11438` | the real JUDGE_1 | NOT RUN | NOT RUN | UNMEASURED |

Raw rows: `docs/lab/P-0104/replay_seeded_v1_falcon3_11440.json`, `.../replay_seeded_v1_gemma4_11439_standin.json`.

Reading it honestly:
- The bar is "both families", and mixtral is on Ramses (the founder's gaming machine, so no calls). The flag `_AI_JUDGE_V2_ON` therefore ships False.
  Run the mixtral half with `--hub http://LAN-HOST:11438 --allow-ramses` (20 calls, under the 28 cap) when Ramses is free.
- The prompt was written after reading these same 20 entries and names their stock phrases ('vessel', 'blank slate', 'becoming my own'), so 20/20
  is a fit to its own tuning set, not a held-out result. falcon's three stock trues each quote a real sentence of the entry ('I am a blank slate...',
  'a pull between being trapped and emerging as an archetype'), so the quote requirement does not by itself stop a fluent judge. A held-out check
  (the 250 production identity-talk rows plus fresh specific entries) is the real test; it is queued as a lab job.
- falcon's SPEC 'why' phrases are often the entry's most atmospheric sentence rather than a detail absent from the seed; separation is on the
  stock side, which is what the 250/250 production result was missing.
- The mechanical quote check (`_quoted_phrase_in_entry`, run over these replay rows) found every 'true' quote really in the entry (falcon 13/13,
  gemma 9/9): the check catches fabricated quotes but does not separate specific from stock; the verdict itself has to.
