# Ramses care package — 2026-08-23

**Copy this whole folder to Ramses and run it from there.** Everything it needs is inside it —
you should not need to reach back into the Nascence box's `scripts/` folder for anything.

This supersedes `README_RAMSES.md` / `RAMSES_CLAUDE_BRIEF.md` in this same folder (both dated
2026-08-20 — kept as historical record of how the model picks were reached, not wrong, just one
round further back). Read this one for what to actually do today.

**Update, same day:** Part A (the two CPU hubs) is DONE — both stood up and verified live with
real inference calls from the Nascence side. Part B (the two GPU hubs) is new — do this next.

---

## 0. RE-SYNC FIRST — read this before anything in Part B

I looked at what's actually on Ramses (`\\ramses\D\Du`) and found two things worth fixing before
going further, not just noting:

**1. `nascence_cpu_server.py` and `resolve_blob.py` were modified on Ramses** (via
`start_ramses_tier.ps1`, which isn't part of this package). The changes were real fixes, not
mistakes — a `get_gen_lock()` lazy-init pattern for a genuine asyncio bug, `--host`/`--log`
flags, and a prefix-matching fallback in `resolve_blob.py` that mixtral's actual tag needed to
resolve at all. **All of it has been merged back into the canonical copies in this folder** — the
version here now has everything: those fixes, plus this session's own `--cuda-device` addition.
Going forward, edits to these two files should happen on the Nascence side and flow out through
this folder, the same as everything else — not the other way round, so there's one source of
truth instead of two drifting copies. If a future need calls for changing them again, flag it
back rather than editing directly, same as the standing rule already says.

**2. UPDATE, resolved:** `mixtral:8x7b` was flagged as colliding with a port FreshStart's own
registry reserved (`:11438`) on this same box. **Founder confirmed FreshStart no longer runs at
all** — that project is dead, so there's no actual conflict. `mixtral:8x7b` stays right where it
is on `:11438`. No relaunch needed for that reason. Ignore any earlier instruction to move it.

**What still matters from the re-sync:** the merged `nascence_cpu_server.py` now has
`--cuda-device` (needed for Part B's two GPU hubs — your current copy doesn't have this flag yet)
and `--host` handling identical to what you already built. Nothing needs restarting on the two
already-running CPU hubs just to pick this up — they're working fine as-is. Just use the copy in
this folder for anything you launch **from here on**, so a future relaunch doesn't lose the
`--cuda-device` support Part B needs.

---

## 1. What's in this folder

| File | What it is |
|---|---|
| `nascence_cpu_server.py` | The server. One process, one model, mimics Ollama's own API (`/api/tags`, `/api/chat`, `/api/generate`) so nothing downstream needs to change. **This is the only server that should be running for this — see §4.** Updated today with a `--cuda-device` flag for Part B. |
| `resolve_blob.py` | Finds the GGUF file inside an already-`ollama pull`ed model (ollama's blobs *are* GGUFs) so `nascence_cpu_server.py` can load it directly. |
| `launch_ramses.ps1` | Launcher. Resolves the blob, starts the server, binds the port. Updated today for all four hubs. |
| `README_RAMSES.md`, `RAMSES_CLAUDE_BRIEF.md` | Prior rounds' briefs — history, not instructions. |

---

## PART A — the CPU tier (DONE — verified live, nothing to do here)

Two models, i9 CPU, both confirmed working with real inference calls from the Nascence side:

| Model | Port | Verified |
|---|---|---|
| `falcon3:7b` | `:11436` | 13.4s incl. cold load, clean 2-key JSON, holds contract |
| `mixtral:8x7b` | `:11438` | 28.1s incl. cold load of a ~26GB model, clean JSON |

Both launched via `.\launch_ramses.ps1` (defaults) and `.\launch_ramses.ps1 -Model mixtral -Tag
8x7b -Alias mixtral:8x7b -Port 11438 -Ctx 16384` respectively. Context on both was bumped from
the originally-launched values (8192 / 4096) to **16384** — see §3 for why.

(An earlier draft of this doc worried `:11438` collided with a dead project's old port reservation
and told you to move mixtral to `:11440`. Founder confirmed that project never runs — false alarm,
ignore any instruction elsewhere to relaunch mixtral on a different port. `:11438` stays.)

---

## PART B — the GPU tier (do this next)

### 1. Two more models, two more ports

`nascence_cpu_server.py` binds **exactly one model per process** — every hub here is its own
launch of `.\launch_ramses.ps1`, never a shared one.

| Model | Ollama tag | Port | GPU | Ctx | Why |
|---|---|---|---|---|---|
| **granite3.1-moe:3b** | `granite3.1-moe:3b` | **11437** | 1650 Super (4GB) | 4096 | IBM, mixture-of-experts at small scale (~3B total, ~800M active/token) — same edge-efficiency reasoning as mixtral, and a genuinely distinct training lineage for judge independence. **Verify this tag actually pulls** — if not, fall back to `granite3.1-moe:1b` (already confirmed to exist). |
| **command-r7b** | `command-r7b` | **11441** | 3070 (8GB) | 8192 | Cohere — the most lineage-distinct model available in this whole plan (everything else here is llama/qwen/gemma/phi/mistral/yi/deepseek/falcon/granite). Already flagged as worth testing for judge independence; the fastest card gets the model doing the most differentiated work. |

Pull both first:
```powershell
ollama pull granite3.1-moe:3b
ollama pull command-r7b
```
**Verify the exact tags landed** (`ollama list`) — same caveat as Part A, names drift. If
`granite3.1-moe:3b` fails to resolve, use `granite3.1-moe:1b` instead and say so when reporting back.

### 2. Port note (resolved, kept for the record)

An earlier draft worried `:11438` (mixtral's port) collided with a separate project's own port
reservation for the same 1650 Super card on this box. **Founder confirmed that project never
runs — no actual conflict, nothing to change.** `mixtral:8x7b` stays on `:11438`, `granite3.1-moe`
takes `:11437`, `command-r7b` takes `:11441` — all three are free and yours to use.

### 3. Before launching either GPU hub: find out which index is which card

```powershell
nvidia-smi
```
Read off which index (0, 1, ...) is the 1650 Super and which is the 3070 — **do not assume**,
PCI ordering is per-machine and this has never been checked here. `nascence_cpu_server.py` now
takes a `--cuda-device N` flag (added today) that sets `CUDA_VISIBLE_DEVICES` for that process
only, so it physically cannot land on the wrong card the way ollama already has on this exact
machine (measured 2026-08-20: 9.82 GB resident against an 8 GB 3070 — the 1650S was already being
used, undirected, by load order). `launch_ramses.ps1` **refuses to start a GPU hub without an
explicit `-CudaDevice`** — this is on purpose, not a bug if it stops you.

**Report the confirmed index → card mapping back** — worth having on record, this will come up again.

### 4. Launch both

```powershell
.\launch_ramses.ps1 -Model granite3.1-moe -Tag 3b -Alias granite3.1-moe:3b `
    -Port 11437 -GpuLayers 99 -CudaDevice <1650S index from nvidia-smi> -Ctx 4096

.\launch_ramses.ps1 -Model command-r7b -Tag latest -Alias command-r7b `
    -Port 11441 -GpuLayers 99 -CudaDevice <3070 index from nvidia-smi> -Ctx 8192
```
`-GpuLayers 99` means every layer on the GPU, never partial — the same all-or-nothing rule Part
A's CPU hubs follow for the opposite reason (0 layers, CPU-only). Confirm with `nvidia-smi` after
each launch's first real call that the model actually landed on the intended card, not the other one.

---

## 3. Context sizes — why "max RAM" isn't quite the right frame

Ctx controls the KV cache, and it's **reserved at load whether or not a call ever uses it** — it
doesn't sit "banked" for later use. Oversizing it for a station that only ever sends ~400 tokens
burns real memory for zero benefit.

- **The CPU tier (Part A)** got bumped to **16384** (from 8192 / 4096) because 48 GB of system RAM
  has genuine headroom past the two models' combined ~31 GB of weights, and mixture-of-experts
  models share their dense base model's attention/KV-cache mechanism — only the FFN experts are
  duplicated — so mixtral's context cost is roughly a 7B model's, not an 8x one. No reason to
  starve it on RAM that's sitting idle.
- **The GPU tier (Part B) stayed modest** (4096 / 8192) on purpose — VRAM is a hard ceiling, not
  RAM that swaps to disk under pressure. Overflow crashes the process; it doesn't degrade
  gracefully the way an oversized system-RAM allocation might. Generous, not maximal.

**Check the actual figure after each first load** rather than trusting this arithmetic blind —
`nvidia-smi` for the two GPU hubs, Task Manager for the two i9 processes. If either GPU hub's
real VRAM use after loading is well under 4/8 GB, that's useful evidence the ctx could go higher
next time; report the actual numbers back either way.

---

## 4. The one thing that will quietly break everything if missed

**Use `nascence_cpu_server.py` from this folder for all four hubs. Do not use llama-cpp-python's
own built-in server (`python -m llama_cpp.server`) instead.**

Both can serve the same GGUF file, but they speak different protocols:

- `nascence_cpu_server.py` (this folder) → **`/api/tags`, `/api/chat`, `/api/generate`** — mimics
  Ollama on purpose, so the Nascence side can point at it with a URL change and nothing else.
- llama-cpp-python's own server → **`/v1/chat/completions`, `/v1/models`** (OpenAI-style) — a
  different program, a different contract, and none of the `/api/tags`-based tooling on the
  Nascence side (station discovery, the HUD's transit map) will see it.

If an endpoint here ever reports itself at a `/v1/...` path instead of `/api/...`, that's the
wrong server — stop and flag it rather than proceeding.

---

## 5. Verify each one came up (from Ramses, right after each launch)

```powershell
curl http://127.0.0.1:11437/api/tags
curl http://127.0.0.1:11441/api/tags
```
Each should return JSON naming the model. If either times out or connection-refuses, check
`hub_11437.log` / `hub_11441.log` in this folder for the error.

We'll do our own verification from the Nascence box once you confirm these are up locally.

---

## 6. The boundary, same as it's always been

**You stand these up. We decide what they're for.**

- Do install (the CUDA-enabled `llama-cpp-python` build for Part B is the real toolchain job —
  report the exact error if it fights you rather than spending an afternoon on it), pull, launch,
  and verify these endpoints answer.
- Do report exact errors verbatim if something fails — a clear "it broke at step 3, here's the
  error" is worth far more than a worked-around "it's fine now."
- Do not wire any endpoint into anything, decide which cognitive job should use which model, or
  treat "it answers" as "it's approved for use" — the actual JSON-contract audition happens from
  the Nascence side before anything gets used for real, not here.
- Leave `:11434` (the existing ollama instance) alone.

## 7. Report back

1. Confirmation both new `ollama pull`s landed, and their actual on-disk sizes.
2. The `nvidia-smi` output and the confirmed index → card mapping.
3. Both launcher runs' output for Part B, including resolved blob paths.
4. Both `curl .../api/tags` results, and — ideally — `nvidia-smi` again after each one's first
   real call, to confirm it landed on the intended card with the expected VRAM footprint.
5. Anything that didn't go as expected — verbatim, not smoothed over.
