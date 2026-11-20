# Node benchmark — can the Ramses i9 carry a CPU tier?

*2026-08-20 · Du stopped, both machines otherwise idle · prompt ~400 tok in / 300 max out, JSON
requested · 3 runs per config · `scripts/node_benchmark.py` + `node_benchmark_local.py`*

**The question this exists to answer** (`docs/plans/ramses_second_tier.md` Phase 1a): an 8B model on
Ramses' i9 — 30 seconds or 300? That 10x uncertainty decided whether the CPU tier was worth standing
up at all, and it had never been measured.

**No Ramses-side setup was needed.** Ollama accepts `num_gpu: 0`, which forces full CPU offload, so
the i9 was reached straight through the endpoint already serving on `:11434`. In this codebase's own
history that flag is documented as a *trap* (it silently sent GPU work to a CPU); here the same lever
is the instrument.

## Results

| node | model | tok/s | warm wall | tokens to finish | valid JSON |
|---|---|---|---|---|---|
| **Ramses 3070 GPU** | `deepseek-r1:8b` | **47.6** | 6.5s | 300 (capped) | no |
| **Ramses i9 CPU** | `llama3.1:8b` | **6.94** | **8.7–11.2s** | **58–75** | **yes, 3/3** |
| **Ramses i9 CPU** | `deepseek-r1:8b` | 6.44 | 47.0s | **never finished** | **no, 0/3** |
| **Ramses i9 CPU** | `qwen2.5-coder:14b` | 3.76 | 27.8–36.1s | 103–134 | yes |
| Local Threadripper CPU | `llama3.1:8b` | ~7.4 | 9.9–12.1s | 72–91 | yes |
| Local Threadripper CPU | `qwen2.5:7b` | — | 20.8–32.4s | 117–166 | yes |

Run-to-run variance on the i9 was ±0.02 tok/s — these are stable numbers, not single samples.

## The three findings

### 1. The i9 is viable, and is a peer to the CPU tier already in production
**6.94 tok/s, ~9–11s warm** for a complete JSON answer. Against the Deep Line's **600–2700s** clocks
that is a **~2% duty cycle**. The 300-seconds-per-call scenario that would have killed Phase 1a does
not exist.

And on the same model, the i9 runs at **~94% of the local Threadripper hub** (6.94 vs ~7.4 tok/s).
Whatever the CPU tier is worth today, a second one on Ramses is worth about the same.

### 2. A reasoning model on CPU costs 15–20x — and the earlier pick was wrong
`deepseek-r1:8b` was chosen for this tier because it **won the Lane 2 model lab outright**. That lab
measured **quality on a GPU**, where its reasoning cost 6.3s and was affordable.

On CPU the cost profile inverts, and the ranking with it. deepseek spent its entire 300-token budget
thinking and produced **no valid JSON on 3 of 3 runs**. At the ~1400 tokens it actually needs, its
measured 6.44 tok/s implies **~218s per call** — against `llama3.1:8b` finishing the same job in
58–75 tokens and ~10 seconds.

**On CPU, reasoning tokens ARE generated tokens.** A lab result does not transfer across a platform
change; benchmark the hardware you actually have.

### 3. GPU is ~7x CPU — which is why this tier is for slow clocks only
47.6 vs 6.44 tok/s on the identical model. That is the honest price of moving work to CPU, and it is
exactly why the plan puts **only latency-tolerant stations** there. A station firing twice an hour
does not care about 10s versus 1.4s. The Idle and Conversation lines would.

*(Cold load is the reverse: 30.6s to push 5.24 GB across PCIe onto the 3070, versus 4.3–13.8s on CPU.
Hence `--lazy --idle-unload` on the hub rather than a resident model.)*

## Scaling on the i9 — measured, then extrapolated

| params | tok/s | source |
|---|---|---|
| 8B | 6.94 | measured |
| 14B | 3.76 | measured |

The 14B/8B speed ratio is **0.54** against a parameter ratio of 0.57 — near inverse-linear, so
extrapolation is reasonable over this range:

- **Dense 30B: ~1.85 tok/s** → ~70s for 130 tokens, ~162s for 300. **Marginal.**
- **`mixtral:8x7b` (MoE, ~13B active/token): ~4.3 tok/s** → ~30s for 130 tokens. **Viable**, and it
  carries 47B of total knowledge. This confirms the Tier-C recommendation on measured scaling rather
  than on reputation.

## A methodology note worth keeping

The first "3070 GPU" row read **6.38 tok/s** — suspiciously identical to the i9 CPU. It was wrong:
`/api/ps` showed `size_vram = 0.00GB`, i.e. **0% on GPU**. Earlier `num_gpu: 0` runs had left the
model resident in CPU mode, and ollama reused that instance instead of reloading to GPU. The
benchmark had measured the i9 twice and labelled one of them "GPU".

Two lessons: **a suspiciously equal number is a signal to check placement, not a finding**; and
`size_vram` is the check — it cleanly reports 0% for CPU-mode models, which is also what makes the
separate two-GPU finding (9.82 GB resident across a 8 GB card) trustworthy.

## Incidental finding — `MAX_LOADED=1` is NOT armed on the hot lane

While benchmarking, `phi3:mini` (5.41 GB) loaded onto the local 1080 Ti **alongside** the pinned
`gemma4:e4b` (3.25 GB) — 8.66 GB of 11.26 GB, both fully resident. `launch_servers.ps1` warns about
precisely this: `OLLAMA_MAX_LOADED_MODELS=1` and the 2h keep-alive **only apply if that script started
ollama**. The running instance was not started by it.

So the protection that ended the July eviction disease is **not currently in effect**. Nothing broke
here (both models fit), but a third model would evict gemma — the original failure. The hot lane was
restored to `gemma4:e4b` alone after the test.

*Raw: `data/lab/node_benchmark/raw.json`, `raw_local.json`, `data/lab/gpu_recheck.log`*
