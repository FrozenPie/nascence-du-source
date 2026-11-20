---
name: ops-nascence-hotlane-ctx-vram
description: "Nascence froze with 'transport error / all servers exhausted' — root cause was hot-lane num_ctx too big for the model's VRAM, NOT a stuck process or the sim code"
metadata: 
  node_type: memory
  type: reference
  originSessionId: de385eda-51ed-4214-9bfe-d47eeaae69ca
---

**2026-07-07 — Du frozen, log flooded with `[model_client] transport error on http://127.0.0.1:11433: — failing
over` + `LLM call failed: all servers exhausted`.** Full diagnosis (the pattern for next time):

**The hot lane (127.0.0.1:11433, the 1080 Ti, "Self") is a SINGLE-server lane** (`schema.py` HOT = `['http://
127.0.0.1:11433']`, "if it's down nothing runs") — so when it fails there is NO failover, and every monologue/
critic/reflection call dies. That's why one node dying freezes the whole sim.

**ROOT CAUSE: `core/model_client.py` `_NUM_CTX_BY_BASE["11433"]` had been bumped to 32768** (a "4x the old 8192"
change) on a WRONG assumption ("32k ≈ 3.7GB for gemma, well within budget"). But the hot model **gemma4:e4b is
an 8B model (~5GB weights, Q4_K_M)**, and at 32768 ctx ollama predicted **12.2 GiB > the 1080 Ti's ~10 GiB
available** → ollama logged `"model predicted to exceed available memory, evicting"` and REFUSED to load it →
every `/api/generate` hung → transport-error/exhausted flood. FIX: set it to **16384** (verified fits ~6.6GB;
8192→3.4GB, 24576→6.9GB all work; 32768 does NOT). num_ctx is sent per-request, so the sim picks it up on next
start (no ollama restart needed for the config).

**DIAGNOSTIC PLAYBOOK (verify-before-asserting; this looked like it might be my batch, it was NOT):**
1. Read the real error: `grep 'transport error on' data/nascence.log | grep -oE 'http://[0-9.:]+' | sort | uniq -c`
   — which node(s), and is it ONGOING (tail) vs a burst.
2. Is the server even up? `curl -m8 http://127.0.0.1:11433/api/tags` (server alive) vs an actual
   `curl /api/generate -d '{"model":"gemma4:e4b","prompt":"hi",...}'` (does GENERATION hang? — the real test).
   `/api/tags` OK + `/api/generate` hang = server up but runner can't load the model.
3. `nvidia-smi` — model NOT loaded (VRAM ~1.5GB, GPU cold) while a generate hangs = it's failing to load.
4. **Read ollama's own log: `C:\Users\USER\AppData\Local\Ollama\server.log`** — it states the reason
   verbatim ("predicted to exceed available memory, evicting", "num_ctx=32768 predicted=12.2GiB available=10GiB").
5. Isolate: does a SMALL standard model work? `gemma:2b` generated fine (7s) → the GPU/driver/ollama stack is
   healthy; the problem is that specific model+ctx, not the machine or the sim's Python.
6. Not the sim code if: a bare `"hi"` to ollama hangs too (prompt content irrelevant), and the sim adds no new
   LLM calls (num_ctx prediction is ctx-based, NOT prompt-length-based — a bigger prompt does NOT cause this).

**RESTART OLLAMA (Windows) when a runner wedges:** `Get-Process ollama,'ollama app' | Stop-Process -Force`
(kill BOTH — the app respawns the server), then it relaunches, OR `Start-Process ollama serve`. OLLAMA_HOST is
a persistent USER env var = `127.0.0.1:11433`, so a fresh `ollama serve` binds the right port automatically.
(A restart alone did NOT fix it here — the 32k-ctx config re-broke on the fresh server; the num_ctx edit is the
actual fix.) See [[feedback-my-failure-modes]] (went to the data instead of assuming it was the batch).
