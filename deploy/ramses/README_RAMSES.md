# Ramses second tier — setup you run ON Ramses, once

**Why this folder exists:** Ramses has an i9-11900K with **48 GB** doing nothing, and a **GTX 1650
Super (4 GB)** that is *already* in ollama's pool but undirected. There is no SSH (tried, failed) and
no working SMB path from the Nascence box, so this is packaged to be copied over and run by hand.

## What the measurements actually showed (2026-08-20)

- Resident VRAM on Ramses was pushed to **9.82 GB**. The 3070 alone is 8 GB, so **the 1650S is already
  serving** — ollama spreads across both cards by load order, not by design. The fourth model loaded
  partially spilled to system RAM (`llama3.2:3b` held only 0.62 GB of its 2.02 GB), which is where the
  ~10 GB combined ceiling sits.
- **Nothing else is serving on Ramses** — only `:11434`. The i9 and its 48 GB are idle.
- Every model needed is **already pulled** on Ramses. Nothing downloads.

So the problem was never capacity. It is that **nobody is allocating** — the same finding as the
missing signal box in `docs/transit_timetable.md`, one layer down in the stack.

## Why llama.cpp and not a second ollama

Founder's standing rule, and it is written into `scripts/launch_servers.ps1`'s own header: one ollama
owning both a GPU mind and CPU models caused the July eviction freeze, the CPU/GPU separation trouble,
and the duplicate-runner disease. llama.cpp hubs are used everywhere else because they give explicit
control — one model per hub, fixed ctx at load, so duplicate runners are impossible by construction.

That reasoning is respected here. **Stage 1 is CPU-only and touches no GPU at all.**

## STAGE 1 — the i9 CPU hub (do this first; it is the big win and the easy one)

The Deep Line's synthesis stations (`_t2_synthesise`, `_t5_compile`, `_synthesise_theme`,
`_self_relate_check`) currently run on **phi3:mini — a 3.8B model** — because they sit on the
`background` chain. Their clocks are **600–2700 seconds** with hour-long minimums. CPU latency is
irrelevant to a job that fires twice an hour, and 48 GB holds models neither GPU can:

**MEASURED on this exact hardware 2026-08-20** (`docs/lab/node_benchmark.md`), 3 runs each,
~400 tok in / 300 max out, JSON requested:

| model | node | tok/s | warm wall | tokens to finish | valid JSON |
|---|---|---|---|---|---|
| `llama3.1:8b` | Ramses i9 CPU | **6.94** | **8.7-11.2s** | 58-75 | **yes, 3/3** |
| `qwen2.5-coder:14b` | Ramses i9 CPU | 3.76 | 27.8-36.1s | 103-134 | yes |
| `deepseek-r1:8b` | Ramses i9 CPU | 6.44 | 47s | **never finished** | **no, 0/3** |
| `llama3.1:8b` | Local Threadripper | ~7.4 | 9.9-12.1s | 72-91 | yes |

**The i9 runs at ~94% of the local Threadripper CPU tier on the same model** — a genuine peer to the
CPU tier Du already depends on in production, not a downgrade dressed as capacity.

> **Correction, twice over (2026-08-20).** A first draft named `qwen2.5-coder:14b` as a "~4x" upgrade —
> it is a **CODER** model, as is `qwen3-coder:30b`, and both are wrong for synthesis work. A second
> draft then picked `deepseek-r1:8b` because it won the Lane 2 model lab. **Also wrong.** That lab
> measured quality on a GPU where reasoning cost 6.3s. On CPU, reasoning tokens *are* generated
> tokens: deepseek spent its whole budget thinking and produced no JSON on 3/3 runs. At the ~1400
> tokens it actually needs that is **~218s per call** against llama3.1's ~10s — 15-20x for the same
> output. **Benchmark the hardware you have; a lab result does not transfer across a platform change.**

### Steps (PowerShell, on Ramses)

1. Confirm Python: `python --version` (3.10+). Install it if absent.
2. `pip install llama-cpp-python fastapi uvicorn`
   *CPU wheel — no CUDA toolchain needed. This is why Stage 1 is the easy one.*
3. Copy these three files from the Nascence box into a folder on Ramses, e.g. `C:\nascence_tier\`:
   - `scripts/nascence_cpu_server.py`
   - `scripts/resolve_blob.py`
   - `deploy/ramses/launch_ramses.ps1` (this folder)
4. If Ramses stores ollama models off the system drive, set `OLLAMA_MODELS` first —
   `resolve_blob.py` now reads it.
5. Run `.\launch_ramses.ps1`. It resolves the blob and starts the hub on **:11436**.
6. Back on the Nascence box, verify from here:
   `curl http://LAN-HOST:11436/api/tags`

Nothing in Du points at :11436 yet — **that is deliberate.** Standing it up and wiring it in are
separate decisions, and the wiring should follow a reading of `telemetry.job_status()`, not precede it.

## STAGE 2 — the 1650 Super (deferred, and it is the harder one)

Needs a **CUDA-enabled** `llama-cpp-python` build on Ramses, which is a real toolchain job — the
reason this is Stage 2 rather than part of Stage 1.

`nascence_cpu_server.py` gained a `--gpu-layers` flag on 2026-08-20 (default **0**, so every existing
local hub is byte-for-byte unchanged in behaviour). The founder's objection to ollama's CPU/GPU
handling does not apply to a model that fits **entirely** on one card: with all layers on the GPU
there is no split to mishandle. On 4 GB that means `llama3.2:1b` (1.32 GB) or `gemma:2b` (1.68 GB),
both already pulled. Pass `--gpu-layers 99`; **avoid partial offload**, which is precisely the split
being avoided.

Intended tenants: the **six classifier stations** — `peers:489` (40 tokens, temp 0.0),
`librarian:78` (120, 0.0), `commitment_ledger:348` (150, 0.2), `deliberation:145` (200, 0.1). These
are classification wearing a chat interface and are the natural home for small task-trained models.

## What is NOT decided here

Standing these up does not move any station. Re-platforming is gated on reading `cap_rate` and
utilisation per job from `telemetry.job_status()` after a real run — see `docs/transit_timetable.md` §4.
Moving load on a hypothesis is how the July freeze happened.
