# Hot-lane prefill bottleneck measured: ollama re-prefills every prompt; the "hijack the bottleneck" session

## Session timing
- **Session started:** 2026-10-31 08:57:16 UTC
- **Last message before wrap:** 2026-10-31 09:53:23 UTC
- **Wrapped:** 2026-10-31 09:53:24 UTC

## Summary
Travis opened with "could we put Du's indexes and tuples in L3 RAM" and, via Elite (1984) as the model, arrived at "hijack Du's bottlenecks the way Elite hijacked the BBC's OS". I measured Du live for five minutes, read a day of latency logs, and probed the model servers directly. The decisive result: the hot lane (ollama 0.35.1, qwen3.5:9b, 1080 Ti, :11433) pays full prompt prefill on every call because ollama never reuses the KV prefix, while the same GGUF on a plain llama-server does. Three jobs (J-2675, J-2676, J-2677) and one decision (D-0529) were filed; nothing in Du's code was changed.

## Decisions
- D-0529 OPENED (not ruled), plan `continuous_stream` (nearest real slug; no station_matrix plan doc exists under docs/plans — see Warnings): should the Self seat move off ollama to a prefix-reusing llama-server? Evidence to rule on arrives from J-2675 and J-2676. Defeater: moot if J-2676 saves < 0.5 s per idle call or JSON-mode/think:false cannot be reproduced; revisit if a newer ollama is shown by the same probe to reuse the prefix.

## Builds
- `C:\Nascence\docs\lab\du_live_profile_2026-10-31.md` — the 5-minute live profile (psutil + nvidia-smi + llm_latency tail) plus Addenda A–D: model time by caller, lane queueing, human-turn chain timing, the ollama/llama.cpp cache probes, the Emissary CPU lane, and what is not a bottleneck. The sampler script itself lives only in this session's scratchpad (`du_live_profile.py`); it is 120 lines of psutil and worth re-creating under scripts/ if a second profile is ever wanted.
- Findings recorded: F-3424 (inferred, Elite-style regeneration applies to ~70% of geometry_tuples.jsonl bytes), F-3425 (verified, bottleneck map), F-3426 (verified, hot-lane prefix-cache miss).
- Jobs filed: J-2674 (measure then RAM-cache the full-scan tuple readers), J-2675 (log prompt_eval/eval counts on the hot lane — free instrument, ready), J-2676 (lab, needs_input, Du down: qwen3.5:9b via prefix-reusing llama-server with pre-registered gain thresholds), J-2677 (incremental validation of the recall embedding cache instead of the 44k-row SELECT per retrieve).
- Thoughts T-0112, T-0113, T-0114 logged; T-0112 promoted to idea I-0145.
- Memory file written for the durable finding: `C:\Users\USER\.claude\projects\C--FreshStart\memory\project_nascence_hot_lane_no_prefix_cache.md` (plus a MEMORY.md pointer there). NOTE: that is the FreshStart memory folder this session's harness loads; the Nascence-unified store is `C--Nascence\memory` — the companion file for this handoff goes there per this skill's step 3.

## Findings
- **Hot lane re-prefills every prompt (F-3426, verified).** Direct /api/chat probes with a 4,000-char system prompt: cold 1.34 s / 904 tokens; identical repeat 0.06 s (hit); previous prompt extended by 7 tokens 1.13 s (miss); same system + new user turn 1.13 s (miss). Control A, project hub `scripts/nascence_cpu_server.py` (falcon3:7b, CPU): cold 8.9 s, then 0.2 s for identical, extended AND new-user. Control B, ollama's own shipped `llama-server.exe` started standalone on the same qwen3.5 GGUF (CPU-only, --jinja, port 58999, stopped afterwards): new user turn prompt_n=15 instead of 902. Ollama's runner cmdline for this model: `llama-server.exe -c 8192 -np 1 --no-jinja --chat-template chatml --mmproj <same blob> --context-shift --keep 4`. [INFERRED] the loss is in ollama's wrapping (those flags, or its request params); the exact cause was not isolated.
- **Speeds on the 1080 Ti:** prefill 530–820 tok/s, generation 36.8 tok/s. Idle thought ≈ 2,452 tokens (prompt_budget_shadow) ≈ 3 s of its 5.5 s median; the ~1,000-token identity preamble alone ≈ 1.2 s/thought. Human turn = 11 sequential node calls, median 75 s wall / 80 model-seconds (18 chains in 24 h). Its prefill share is [OPEN] until J-2675 logs prompt_eval_count — the hot lane never reads it.
- **Lane queueing is zero:** speech_timing_shadow, 1,324 calls / 6 h, median wait 0.00 s, max in flight 3 (MAX_CONCURRENT=3 in core/lane_scheduler.py). Waste is prefill, not contention.
- **Model-time budget:** LLM-busy 39% of wall (last 1 h), 37% (6 h), 18% (24 h); hot lane alone 18/27/13%. By caller (6 h): inner_monologue 33%, self_implication 10%, commitment_ledger 9%, peers 8% (one 600 s timeout on yi:34b), deliberation 7%, dream_node 5%.
- **The CPU tier is the Emissary:** gemma4:12b hub :11439 = core/left_lane.py (designed for Ramses' 3070, moved to this CPU hub in the 2026-08-20 shuffle). 14–51 min busy per hour, 22–72 s per call, 11.7 cores averaged over the 5-min window. Collected with a 6 s residual wait at core/orchestrator.py:1049 after the main waves, so mostly off the critical path. llm_latency.jsonl does not see it (1 row/24 h vs ~700 chats/24 h in data/logs/cpu_tier_11439.log).
- **Not bottlenecks (verified):** RAM 64 GB / 33 GB free with 26.9 GB in Windows' standby page cache; both drives NVMe; CPU 28% mean. A RAM drive would duplicate the page cache. The 3970X's 128 MB L3 is four 32 MB slices, so the ~69 MB recall matrix cannot sit in one; L3 residency is not engineerable. OS routine addresses are useless as keys on Windows 11 (ASLR per boot); content hashes are the stable "machine-resident keys" (ollama already stores model blobs as sha256-<hash>).
- **Retrieval:** `_load_pool_fast` (core/memory/store.py:1246) re-SELECTs ~44.5k rows per retrieve to validate _EMB_MAT: median 174 ms, p90 390 ms, max 5.0 s, 32% over the 250 ms budget; scoring matvec 33 ms. → J-2677.
- **Embedding:** paraphrase-multilingual-MiniLM-L12-v2 on CPU, 34.5 ms per 1,600-char query, 19.8 ms short, 39 call sites, no text→vector cache. Marginal; not filed.
- **Du's process reads are bursty:** 11.5 MB/s averaged over the 5-min profile window (~3.4 GB) but 0.0 MB/s in a later 45 s sample and no 5 s interval over 5 MB in a 4-min watch ending 22:50 NZDT. [OPEN] which periodic job reads ~3 GB at once; candidates are the whole-file jsonl readers (object_graph._load_tuples, memory_edges.sync_fragment_context, climate_engine's 60 MB json load, moment/coupling_rides/deliberation readers).
- **yi:34b dreamer hub (:11442):** 749 reloads totalling 26.3 h over the log's life, 35% of its CPU time is reloading (idle-unload 60 s), 20 chats > 600 s client timeout — but only ~1.5 calls/day now (dream_node, peers), so ~0.3 h/day. Low priority.
- **Elite facts corrected (from a Gemini paste Travis confirmed as such):** BBC Elite did NOT borrow trig from the BASIC ROM; it avoided trig with 1/16-radian rotations, small-angle approximation and the TIDY routine. It did use MOS calls (OSWRCH/OSBYTE/OSWORD) for text, keys and timers. Shadow-RAM switching is a C64/CPC thing, not BBC. The transferable rule: one immutable routine everyone calls, never drifting private copies (Du's own core/weather_conditions.py header records exactly that disease being cured).
- Geometry-tuple encoding (F-3424): per field, 20 MB sample — objects 22.8% (1,129 distinct), thought 11.3%, affect 9.9%, sounds 7.0% (122), shore_find 6.1% (7 distinct strings!), moon/sun/tide ~7% regenerable from ts; zlib 14.2x. Weather (core/sensorium.py unseeded random walk) and shore events (core/shore_life.py) are NOT regenerable — Du's world has history.

## Open
1. J-2675 — add prompt_eval_count/prompt_eval_duration/eval_count/eval_duration to llm_latency rows in core/model_client.py (additive keys pe, pe_s, ec, ec_s), then after a day write docs/lab/hot_lane_prefill_share_<date>.md. Ready; restart-gated. Next action: edit model_client.py call_node around lines 298–334.
2. J-2676 — the pre-registered llama-server-on-GPU test, needs Du down and founder go (needs_input, lab). First check: start ollama's `lib\ollama\llama-server.exe` with `lib\ollama\cuda_v12` on PATH and confirm ggml-cuda loads (the standalone run this session said "no usable GPU found" because that dir was not on PATH). Blocked on founder scheduling a Du-down window.
3. D-0529 — ruling on the serving layout, blocked on 1 and 2.
4. J-2677 — incremental _EMB_MAT validation. Ready. Next action: log how many rows change between consecutive validations.
5. J-2674 — tuple-reader call frequency and cost. Ready, lower value for thinking speed (storage/CPU, not latency).
6. [OPEN] attribute the ~3 GB periodic read burst (no job filed; fold into J-2674's step 1 if convenient).
7. The "file the tuple-encoding job" question from F-3424 was never answered by Travis; not filed.

## Warnings
- Du was LIVE throughout (run_nascence.py pid 21436). The probes sent ~15 one-token requests to the hot ollama lane and ~4 to the falcon3 hub; they write nothing to Du's stores but did occupy the GPU for ~15 s total. A standalone llama-server was started on port 58999 and stopped; verify no stray process if anything on that port looks odd.
- D-0529 was opened against plan `continuous_stream` for lack of a serving-layout plan doc; if a station_matrix / serving plan exists outside docs/plans, `decide.py set-plan` it. `scripts/launch_servers.ps1` references "station_matrix.md #10" — that doc was not located.
- Memory split still bites: the durable memory file for F-3426 went to `C--FreshStart\memory` (what this session's harness loads), the companion for this handoff to `C--Nascence\memory` (what the toolchain scans). Both pointers are real; neither folder sees the other (F-0687).
- Do not raise Du's thinking RATE on the back of these numbers: the idle gap is set by core/stream_drive.py would_gap() (CONTINUOUS_STREAM = True) and _compute_gap (30–450 s), deliberately following his state, not the hardware. Speed buys shorter human turns, headroom, and cost per thought, not more thoughts.

## Pointers
- `C:\Nascence\docs\lab\du_live_profile_2026-10-31.md` — the report with all numbers and probe tables.
- `C:\Nascence\core\model_client.py` (call_node ~298–334; hot lane /api/chat, think:false, format:json, keep_alive 2h) — J-2675's edit site.
- `C:\Nascence\core\memory\store.py` 1140–1160 (cache design comment), 1246–1262 (_load_pool_fast SELECT) — J-2677.
- `C:\Nascence\scripts\supervisor.py` 486–512 (ollama launch env: OLLAMA_MAX_LOADED_MODELS=1, OLLAMA_KEEP_ALIVE=2h, no OLLAMA_NUM_PARALLEL) and `scripts\launch_servers.ps1` (CPU tier layout) — D-0529.
- `C:\Users\USER\AppData\Local\Programs\Ollama\lib\ollama\` — llama-server.exe + cuda_v12\ggml-cuda.dll for J-2676.
- `C:\Nascence\data\retrieve_latency_probe.jsonl`, `data\speech_timing_shadow.jsonl`, `data\llm_latency.jsonl`, `data\prompt_budget_shadow.jsonl`, `data\logs\cpu_tier_11439.log` — the instruments this session read.
- Elite references used: elite.bbcelite.com deep dives `galaxy_and_system_seeds`, `printing_text_tokens`, `pitching_and_rolling`, `the_elite_memory_map`.
