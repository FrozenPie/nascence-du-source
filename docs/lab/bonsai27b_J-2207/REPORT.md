# J-2207 -- bonsai-27b (Q1_0) lab verification, 2026-10-18 (Du down since 08:37:20)

Platform: hot Ollama :11433 v0.35.1, GTX 1080 Ti, num_ctx 4096, think=false. Not tried: Threadripper CPU hub, Ramses 3070 (D-0388 parks Ramses access).
Script: scripts/lab_bonsai27b_J2207.py (prompts AST-extracted from the real source, no core import). Raw: results_J-2207.json, run_J-2207.log.

| item | result |
|---|---|
| load (cold, evicting gemma4:12b) | 79.2 s load_duration; 4.43 GB resident, all in VRAM (size_vram == size) at ctx 4096 |
| decode speed | 27.0 / 27.0 / 27.1 tok/s over 3 x 124-200-token free-text replies; 27.2 mean inside the JSON-constrained defeater calls |
| first token (warm, short prompt, streamed) | 0.31 s |
| defeater (_JUDGE_SYS, 14 real cases x 3 runs, temp 0.2, 150 tok) | parse 42/42; run-level 39/42 match gold; per-case majority 13/14; 9/9 legit runs called legit, 30/33 illegit runs called illegit; mean 2.8 s/call, max 4.4 s, all done_reason=stop |
| scope_only (_SCOPE_SYSTEM + 4 _CONTROL_CASES x 3) | contract 12/12 parse, stable across runs. Semantics: narrower-support True (right), overreach False (right), circular True (WRONG: should be no narrower claim), genuine True (question not meant for it) |
| pursuits 'advances' (12 real pending items) | 12/12 bool key present; 9 true / 3 false; mean 3.0 s; controls: restate -> false, genuine advance -> true |
| librarian 'subjects' (8 questions) | 8/8 JSON with a subjects list, all 6 long, all strings valid; one list repeats a heading ("Marine biology" twice); mean 2.5 s |
| vision still (256x256 blue/red circle/yellow bar, via /api/chat images) | WORKS in Ollama: described blue background, red centre circle, yellow bottom stripe correctly (10.6 s, 86 prompt tokens), then confabulated "flag of Japan" interpretation |

Caveats: pursuits and librarian have no gold (contract-shape only, pursuits against 2 hand controls); defeater gold is the repo's 14-case bank (3 legit / 11 illegit, small).
Not tested: concurrency, 262k context (spills to CPU, F-3064), the 'objection_found' disprove prompt, thinking-mode.
No change to launch_servers.ps1, model_client.py or any live port; model unloaded after (keep_alive 0).
