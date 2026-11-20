# J-3280 - Rehearsal of the Oct-7 hub server (deploy/ramses/nascence_cpu_server.py), Phase 2

Status: DONE, all six items pass. Plan: docs/reviews/ramses_stall_plan_2026-11-03.md Phase 2. Run 2026-11-14 22:08-22:11 NZDT.

## Setup
- New file: deploy/ramses/nascence_cpu_server.py (J-1830 / F-2466 / F-2494). Old file: scripts/nascence_cpu_server.py (what the local hubs run).
- Model: qwen2.5-coder 1.5B (Ollama blob sha256-29d8c98f...), CPU, 6 threads, ctx 2048. Not a Ramses model, so absolute timings differ from Ramses.
- Ramses flags: `--host 0.0.0.0 --lazy --idle-unload 900 --log <file> --max-gen-seconds 150`; second run with `--max-gen-seconds 5`. Ports 11471-11474 (spare). Old file run with the same flags minus `--max-gen-seconds` (it has none).
- Harness: scratchpad lab_J-3280_rehearse.py (plain HTTP client; the repo parsers were imported but no call_node was made, so no telemetry rows). Writes only to docs/lab/j3280_data/ (results.json plus the four server logs). No live hub, Ramses, or data/ file touched. Du was live; all servers stopped afterwards.

## Results

| # | Item | Result |
|---|---|---|
| 1 | GET /api/status | PASS. Before load: loaded=false, counters all 0. Mid-generation with a second request waiting: in_flight={endpoint, lock_wait_s, deadline_s, json, tokens, phase "loading", elapsed_s}, queue_depth=1, counters.requests=2. After: in_flight null, completed=2. Counters: requests, completed, deadline_cuts, abandoned_before_gen, abandoned_during_gen, errors. |
| 2 | Abandon test | PASS. 300-token job abandoned by the client at 3 s, then an 8-token call: NEW 0.40 s (baseline 0.37 s). OLD 8.85 s (baseline 0.38 s), because the old file finished the whole job first (old log: 300 chars in 11.2 s). New log: that job ended `tok=79 done=disconnected` at 3.1 s; counter abandoned_during_gen=1. The old delay was 8.5 s here, not 32 s, only because this model is much faster than Ramses's. |
| 3 | Deadline cut | PASS. `--max-gen-seconds 5`, num_predict 3000: returned after 5.06 s with done=true, done_reason="deadline", 128 tokens of partial text, counter deadline_cuts=1. A following 8-token call was normal (done_reason "length"). |
| 4 | Parsers still parse | PASS. /api/chat with format=json (core/model_client.py and core/lane2.py payload shapes): core.model_client.extract_json and core.lane2.parse_json_loose both returned the right dict on new and old output. Free-text reply is a non-empty string; core.model_client._eval_counts reads eval counts fine. The only response difference vs the old file is the added `done_reason` key (also on /api/generate). The new JSON reply was compact, the old one pretty-printed; both parse. |
| 5 | Log line | PASS. New: `[22:08:35.086] [chat] 1 msgs -> 79 chars wait=0.0s gen=3.1s tok=79 done=disconnected (json=False)`. Old: no timestamp, only `in 11.2s`. |
| 6 | Idle-unload and lazy reload | PASS, with a shortened timer. Started lazy (loaded=false), first call loaded it; with `--idle-unload 20` it unloaded 45 s after the last call (the unloader polls every 60 s, so unload is idle-time plus up to 60 s) and the next call reloaded it and answered. The real 900 s was not waited for; the code path is identical apart from the number. |

## Things to know before deploying (not failures)
- On the first call after a lazy load, `gen=` includes the model load time (gen=22.3 s for a 120-token call, gen=17.8 s for an 8-token call), and requests queued behind it show a large `wait=`. Read first-call lines after a restart with that in mind.
- The deadline does not cut a model load: the 5 s deadline run still completed a call that spent 17.8 s loading. The deadline is checked between tokens only.
- Binding `--host 0.0.0.0` was exercised, but only connected to over 127.0.0.1. Reachability from the Ramses network was not tested here (Phase 3 step 3 check stays).
- Not exercised: GPU offload (`--gpu-layers`, `--cuda-device`), a 7B+ model, concurrent hubs on one box, or timeouts against real Du clients. Phase 4 watching covers those.

Verdict: the Oct-7 server is safe to proceed to Phase 3.
