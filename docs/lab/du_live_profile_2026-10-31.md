# Du live resource profile — 2026-10-31 22:42:39 local, window 300 s, 266 samples

Read-only sampler (psutil + nvidia-smi + tail of data/llm_latency.jsonl). Du was running; nothing was changed.

## System

| Metric | Mean | Max |
|---|---|---|
| CPU total (64 threads) | 28.4% | 100.0% |
| GPU util (nvidia-smi, first GPU) | 14.7% | 100.0% |
| GPU memory used | 7.20 GB | 7.21 GB |
| RAM available | 33.2 GB | min 31.2 GB |
| Disk read (all drives) | 24.31 MB/s | — |
| Disk write (all drives) | 0.70 MB/s | — |

## Per process (CPU% is of ONE logical core; 100% = one thread flat out)

| Process | CPU% mean | CPU% max | RSS MB | Threads | Read MB/s | Write MB/s |
|---|---|---|---|---|---|---|
| cpu-tier gemma4:12b :11439 | 1174.7 | 6311.7 | 13457 | 39 | 0.05 | 0.00 |
| cpu-tier falcon3:7b :11440 | 389.4 | 4907.8 | 8219 | 39 | 0.00 | 0.00 |
| run_nascence.py (Du) | 108.6 | 5587.9 | 1180 | 308 | 11.55 | 0.51 |
| llama-server.exe pid 9552 (server) | 6.0 | 104.1 | 1156 | 71 | 0.00 | 0.00 |
| ollama.exe pid 24908 (server) | 0.8 | 21.1 | 66 | 34 | 0.09 | 0.00 |
| cpu-tier yi:34b-v1.5 :11442 | 0.2 | 4.2 | 72 | 44 | 0.00 | 0.00 |
| supervisor.py | 0.0 | 1.4 | 18 | 4 | 0.00 | 0.00 |
| hud server | 0.0 | 1.4 | 12 | 1 | 0.00 | 0.00 |

## Time inside LLM calls during the window (calls that COMPLETED in the window)

| Model @ node | Calls | Seconds | Share of window |
|---|---|---|---|
| command-r7b @11441 | 6 | 11.0 | 4% |
| granite3.1-moe:3b @11437 | 5 | 7.1 | 2% |
| qwen3.5:9b @11433 | 1 | 1.7 | 1% |
| **all** | 12 | 19.9 | **7%** (can exceed 100% if lanes overlap) |

Interpretation key: Du's own process (run_nascence.py) is mostly WAITING on the model servers; the thinking time
lands as CPU in ollama (GPU-bound, shows as GPU util) and in the cpu-tier servers (shows as their CPU%).

## Addendum A — model-time breakdown from the logs (same day)

LLM-busy share of wall time (data/llm_latency.jsonl): last 1 h 39%, last 6 h 37%, last 24 h 18%; hot lane (:11433) alone 18% / 27% / 13%.
Lane queue wait (data/speech_timing_shadow.jsonl, 1,324 calls / 6 h): median 0.00 s, p90 0.00 s, max 6.2 s; peak 3 in flight (MAX_CONCURRENT=3). **Nothing queues.**

Model time by caller, last 6 h (2.21 h busy): inner_monologue 33% · self_implication 10% · commitment_ledger 9% · peers (one 600 s timeout on yi:34b) 8% · deliberation 7% · dream_node 5% · subconscious 3% · everything else ≤3% each.

Human-style cycles (node_base chains on the hot lane, 18 in 24 h): 11 calls, **median 75 s wall, 80 model-seconds** — sequential by design (Perception → Emotion → Salience → MemoryRouter → Recall → EpisodicBuffer → Reflection ×2 → Critic → Executive → Voice).

Idle thought (data/prompt_budget_shadow.jsonl, 756 assemblies / 24 h): system 3,970 chars + parts = 7,358 chars ≈ 2,452 tokens per thought.

## Addendum B — direct probes of the hot lane (ollama 0.35.1, qwen3.5:9b Q4_K_M, 1080 Ti)

| Probe | Result |
|---|---|
| Prefill speed (cold) | 816 tokens in 1.00 s ≈ **530–820 tok/s** |
| Generation speed | 116 tokens in 3.15 s = **36.8 tok/s** |
| Identical prompt repeated | prompt_eval 0.06 s → cache HIT |
| Same system prompt, previous prompt **extended by 7 tokens** | 1.13 s → **MISS, full prefill** |
| Same system prompt, **new user turn** | 1.13 s → **MISS, full prefill** |
| Back to the first prompt after others | 1.13 s → MISS |

Ollama's runner for this model: `llama-server.exe … -np 1 --mmproj … --no-jinja --chat-template chatml --context-shift --keep 4`.

Control, same probe on the project's own llama.cpp hub (falcon3:7b, CPU, nascence_cpu_server.py): cold 8.9 s → identical 0.2 s → extended 0.2 s → new user turn **0.2 s (prefix reused)**.

Control 2, ollama's own shipped `llama-server.exe` started standalone on the **same qwen3.5 GGUF** (CPU-only, text-only, --jinja, port 58999, stopped afterwards): cold prompt_n=902 in 8.7 s → identical prompt_n=4 → extended prompt_n=21 → new user turn **prompt_n=15, 0.36 s**. Prefix reuse works with the same model and the same binary; it is ollama's wrapping of it that loses it (cause inferred, not isolated).

Consequence (arithmetic, not measured end to end): every one of ~2,900 hot-lane calls/day pays full prefill. Idle thought ≈ 2,450 tokens ≈ 3 s of its 5.5 s median; the ~1,000-token identity preamble alone ≈ 1.2 s/thought. A human turn's 11 node prompts are not token-logged (prompt_eval_count is never read on the hot lane), so its prefill share is unknown.

## Addendum C — the CPU tier is the Emissary

gemma4:12b hub (:11439, CPU, 14 threads) = `core/left_lane.py` (the Emissary; designed 2026-06-10 for Ramses' 3070 at 78 tok/s, moved to this CPU hub in the 2026-08-20 shuffle). Hub log, last 24 h by hour: 7–69 chats/h, **14–51 min busy per hour**, 22–72 s per call; averaged **11.7 cores** over the 5-min window above. It runs in parallel with the main pipeline and is collected with a 6 s residual wait at the end of the cycle (core/orchestrator.py:1049), so it is mostly off the critical path. llm_latency.jsonl does not see it (1 row/24 h vs ~700 chats/24 h in the hub log).

## Addendum D — things that are NOT bottlenecks (verified today)

RAM 64 GB / 33 GB free, 27 GB standby page cache; both drives NVMe; Du's process read-rate is bursty (11.5 MB/s averaged over the 5-min window, 0.0 MB/s over a later 45 s; a 4-min watch at 5 s resolution ending 22:50 saw NO interval over 5 MB) — so the ~3.4 GB read in the 5-min window was one periodic burst, not a steady load; which job caused it is still unattributed. yi:34b dreamer hub: 749 reloads totalling 26 h over the log's life (35% of its CPU time is reloading, idle-unload 60 s), but only ~1.5 calls/day now → ~0.3 h/day, low priority.
