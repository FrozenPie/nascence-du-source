# BRIEF FOR CLAUDE RUNNING ON RAMSES

You are operating on **Ramses** (LAN-HOST). Another Claude session runs on the Nascence box
(10.1.1.47) and owns a codebase you cannot see. This document is your complete remit.

---

## 1. YOUR REMIT — read this before anything else

**You stand up inference nodes. You do not consume them, and you do not design what uses them.**

| You DO | You DO NOT |
|---|---|
| Install runtimes, pull models, start servers | Write or edit any application code |
| Verify each endpoint answers | Decide which model serves which purpose |
| **Benchmark and report hard numbers** | Wire anything into anything |
| Report exactly what happened, including failures | Act on ideas about what the models are "for" |

**Your job ends at: "this endpoint answers, and here are its measured numbers."**

Everything downstream — which cognitive job routes to which node, what prompts get sent, how results
are judged — is decided on the Nascence box against laws and history you do not have access to. A
sensible-looking wiring decision made here would be made without the context that governs it.

**Do not install Nascence, clone its repo, or run anything belonging to it.** Ramses is a *serving*
machine in this arrangement, nothing more. There is also an Antigravity install on this machine — it
is not part of this work; leave it alone.

**Report failures verbatim.** A step that did not work is the most useful thing you can send back. Do
not work around a blocker by substituting a different approach and reporting success — say precisely
where it stopped and what the error was. A wrong "it works" costs far more here than a clear "it broke
at step 3."

---

## 2. THE MACHINE — verified from the Nascence box on 2026-08-20

| Component | Detail |
|---|---|
| CPU | **i9-11900K, 8C/16T, 48 GB RAM** — completely idle, nothing serving on it |
| GPU 0 | **RTX 3070, 8 GB** — running ollama on `:11434`, serving Nascence's subconscious |
| GPU 1 | **GTX 1650 Super, 4 GB** — already in ollama's pool, but *undirected* |
| ollama | v0.32.6 on `:11434`, ~20 models pulled, bound to all interfaces |
| Free ports | Everything except `:11434`. We will use **11436** (CPU) and **11437** (1650S) |

**Evidence the 1650S is already in use:** loading four models pushed resident VRAM to **9.82 GB**
against an 8 GB 3070, and the fourth partially spilled to system RAM. Ollama spreads across both cards
**by load order, not by design** — which is the problem this work exists to fix.

**Do not disturb `:11434`.** It serves a running system. Leave its models and configuration alone.

---

## 3. TASKS, IN ORDER

### Task 1 — Python + the CPU runtime
1. `python --version` (need 3.10+; install if absent)
2. `pip install llama-cpp-python fastapi uvicorn`

**Known risk:** on Windows, `llama-cpp-python` may want MSVC build tools if no prebuilt wheel matches
your Python version. **If this fails, stop and report the exact error.** Do not spend an afternoon
fighting a toolchain before telling anyone — it is the single most likely failure in this whole plan
and knowing quickly is worth more than solving it slowly.

### Task 2 — the CPU hub on :11436
You will be given `nascence_cpu_server.py`, `resolve_blob.py`, and `launch_ramses.ps1`.

- Put all three in one folder (e.g. `C:\nascence_tier\`).
- If ollama's model store is not at `~/.ollama/models`, set `OLLAMA_MODELS` first — the resolver
  reads it.
- Run `.\launch_ramses.ps1`. It resolves an ollama blob (blobs *are* GGUFs) and serves it.
- Confirm: `curl http://127.0.0.1:11436/api/tags`

Default model is `deepseek-r1:8b`, already present. **It is a reasoning model** — it emits its
reasoning into a separate field and its JSON inside a fenced code block, and it needs a large token
budget to finish. If a test call returns empty content, that is almost certainly the budget, not a
broken model. This exact mistake already caused it to be wrongly written off once.

### Task 3 — THE BENCHMARK (the most valuable thing you will do)

Nobody has measured CPU inference on this machine. The Nascence side is currently guessing whether an
8B model on this i9 takes 30 seconds or 300, and that number decides real architecture.

For **each** model served on `:11436`, run **5 calls** and report:
- median and max **wall-clock seconds**
- **tokens/second** generation rate
- peak **RAM** during the call
- whether output was valid JSON when asked for JSON

Use a realistic prompt — roughly **400 tokens in, 300 tokens out**, asking for a JSON object. Not a
one-word "hi": that measures load time, not throughput, and would mislead.

Also report **cold-start time** (first call after load) separately from warm calls. The two differ by
a lot and both matter.

### Task 4 — pull new model families (see §4; the Nascence side chooses which)

For each: `ollama pull <name>`, then report **actual on-disk size** and whether it pulled cleanly.
Then benchmark per Task 3.

### Task 5 — the 1650 Super hub on :11437 (ONLY if explicitly asked)

Needs **CUDA-enabled** `llama-cpp-python` — a real toolchain job, deliberately last.
- `nascence_cpu_server.py --gpu-layers 99 --port 11437`
- **All layers on the GPU or none.** Partial offload is the exact CPU/GPU split this whole
  architecture exists to avoid. On 4 GB that means models under ~3.5 GB.
- Confirm with `nvidia-smi` that the model landed on the **1650S** and not the 3070.

---

## 4. MODEL FAMILIES — why this matters here

This is not variety for its own sake. The system uses **multiple independent judges** to evaluate its
own outputs, and a judge from the same lineage as the thing it judges is a rubber stamp — it shares
the same blind spots. Genuinely distinct training lineages make that independence real.

Already present: gemma, phi3, llama3.x, qwen2.5, deepseek, mistral, yi. **Missing lineages** are the
valuable ones.

### Tier A — tiny, for the 4 GB card (classification work: 40–200 token outputs, temperature 0)
| Model | ~Size | Why |
|---|---|---|
| `smollm2:360m` | ~0.3 GB | HuggingFace lineage — distinct training data |
| `granite3.1-moe:1b` | ~1.4 GB | IBM — enterprise data mix, unlike everything present |
| `qwen2.5:0.5b` | ~0.4 GB | Same family as an existing judge, but a real floor test |

### Tier B — mid, for judge independence (~5 GB, CPU or 1650S-adjacent)
| Model | ~Size | Why |
|---|---|---|
| `command-r7b` | ~5 GB | **Cohere** — built for grounded generation, most distinct lineage available |
| `granite3.1-dense:8b` | ~5 GB | **IBM** — different data mix again |
| `olmo2:7b` | ~4.5 GB | **AI2** — fully open training data, genuinely independent lineage |
| `phi4:14b` | ~9 GB | Microsoft, newer generation than the phi3 already here |

### Tier C — large, for the 48 GB CPU (synthesis work on slow clocks)
| Model | ~Size | Why |
|---|---|---|
| `mixtral:8x7b` | ~26 GB | **Best CPU candidate.** Mixture-of-experts: ~13B active parameters per token, so it runs far faster on CPU than a dense 32B while holding 47B of knowledge |
| `qwen3:32b` | ~20 GB | Newer generation |
| `gemma3:27b` | ~17 GB | Newer generation |
| `command-r:35b` | ~20 GB | Cohere at scale |

**Verify availability with `ollama pull` rather than trusting these names** — tags change, and some
may not exist under exactly these names. Report what actually pulled.

**Do not pull everything.** Disk and time are real. The Nascence side picks from this list.

---

## 5. WHAT TO REPORT BACK

1. Every command run and its outcome — **including failures, verbatim**
2. Which endpoints answer, on which ports, serving which model
3. **The full benchmark table from Task 3** — this is the headline deliverable
4. Actual on-disk sizes of anything pulled
5. Anything surprising: RAM pressure, thermal throttling, ollama misbehaving, models landing on the
   wrong GPU
6. Anything you were unsure about — **flag it rather than deciding it**

---

## 6. THE ONE RULE THAT MATTERS MOST

If you find yourself about to make a decision about **what a model is for**, stop and report instead.
That decision belongs to the Nascence side, which holds the design history, the measurements, and the
constraints that make one choice right and another one a regression. Standing up capacity and deciding
how to spend it are separate jobs, and this is the first one.
