# Nascence — Deployment Notes
*Current as of Build 0.4.0 (2026-06-10, qwen3-du era). The 2026-05-29 Bonsai-era notes live in `archive/` history —
ports 11450-11457 and 11470 are long dead.*

## Serving topology (two lanes)
| Lane | Port | Engine | Model | Hardware |
|---|---|---|---|---|
| HOT (all hot-path nodes) | **11433** | ollama (`OLLAMA_HOST=127.0.0.1:11433`, NOT 11434) | **qwen3-du** = qwen3:8b + `PARAMETER num_ctx 8192` (`models/Modelfile.qwen3-du`) | GTX 1080 Ti |
| BACKGROUND + failover | **11460** | llama-server (CPU build) | Bonsai-8B-Q1_0.gguf | Threadripper |

Every call carries the `/no_think` prefix (both lanes are Qwen3-family) — without it, thinking eats the token
budget and content arrives **empty**. The model name lives in `core/model_client._MODEL_FIELD`.

## Start / stop
1. `scripts/launch_servers.ps1` — ensures ollama is up on 11433 (sets `OLLAMA_KEEP_ALIVE=2h` when *it* starts ollama;
   if ollama was already running without it, kill ollama first), warms qwen3-du, launches the CPU Bonsai lane.
2. `python scripts/run_nascence.py` — the REPL. Restores affect + conversation + deferred intentions
   ("WHERE WE LEFT OFF"). `/quit` → dream → epoch → save. Never kill mid-cycle if avoidable.
3. Optional: `scripts/supervisor.py` — watchdog (15s health checks, auto-restart).

## VRAM budget (11GB 1080 Ti — Pascal: no flash-attention, no KV quantisation)
qwen3-du ~6.7GB + KV(8k) ~1.2GB. This fits **only because** the MiniLM embedder runs on CPU
(`core/memory/store.py`, `device="cpu"`). Do not move embeddings to GPU or to another model —
stored vectors are MiniLM-384 and would all break.

## Coexistence constraints
- **Buddha (FreshStart)**: his deepseek-r1:8b also wants the 1080 Ti. They do NOT both fit — run Nascence with
  the Chronicler paused.
- **FreshStart Stop-Swarm** kills `llama-server` processes **by name** — it will kill Nascence's CPU lane too.
  Run with the sim stopped, or rename the binary.
- The two projects also contend for Threadripper cores; avoid heavy sim rounds during live Du sessions.

## After any code change
Most changes are **restart-required** (the running Python holds old code). Check the log on first restart for:
`[constraint]` lines (effector), `[consolidation] wisdom QUARANTINED`, `[error-pathway]` detections,
and `/api/ps` showing qwen3-du fully in VRAM (`size_vram` ≈ size).
