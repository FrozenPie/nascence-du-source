# launch_ramses.ps1 — the Ramses second AND third tier. RUN THIS ON RAMSES (LAN-HOST), not on the
# Nascence box.
#
# Mirrors scripts/launch_servers.ps1's proven pattern deliberately: one llama.cpp hub per model, fixed
# ctx at load, duplicate-spawn guard, port-bind check. Same reasoning as that file's header — one
# server owning both a GPU mind and CPU models is what caused the July eviction freeze.
#
# FOUR HUBS TOTAL now (2026-08-23) — two CPU (i9, RAM-bound), two GPU (1650 Super + 3070, VRAM-bound).
# Run this script FOUR TIMES, once per hub; it is not multi-model-per-port. Exact commands:
#
#   .\launch_ramses.ps1                                                                        # falcon3:7b     -> i9 CPU,  :11436
#   .\launch_ramses.ps1 -Model mixtral -Tag 8x7b -Alias mixtral:8x7b -Port 11440 -Ctx 16384     # mixtral:8x7b   -> i9 CPU,  :11440
#   .\launch_ramses.ps1 -Model granite3.1-moe -Tag 3b -Alias granite3.1-moe:3b `
#       -Port 11437 -GpuLayers 99 -CudaDevice <1650S index — CONFIRM with nvidia-smi first> -Ctx 4096
#   .\launch_ramses.ps1 -Model command-r7b -Tag latest -Alias command-r7b `
#       -Port 11441 -GpuLayers 99 -CudaDevice <3070 index — CONFIRM with nvidia-smi first> -Ctx 8192
#
# PORT NUMBERS, READ THIS FIRST — a real cross-project collision was caught here, not a style choice.
# FreshStart's own Trinity Fabric registry (a SEPARATE project also on this same physical Ramses box)
# reserves :11438 for "ramses_1650" (its own name for this same GTX 1650 Super). This Nascence plan
# had already separately reserved :11437 for the identical card (docs/plans/ramses_second_tier.md,
# 2026-08-20) — the two projects picked DIFFERENT ports for the SAME hardware and neither knew about
# the other's number. mixtral was originally going to take :11438 here too, which would have been a
# direct bind conflict with FreshStart's expectation on the exact same box. Moved to :11440 and
# command-r7b to :11441 instead — both unclaimed by either project's documented scheme. :11437 is kept
# for the 1650S hub (Nascence's own established number), but if FreshStart's sim is ALSO meant to run
# concurrently on this machine, its ramses_1650 node at :11438 and this plan's granite3.1-moe hub at
# :11437 are two different processes serving the same physical GPU — confirm with the founder whether
# both are meant to be live at once before assuming that's fine.
#
# BEFORE the two GPU launches: run `nvidia-smi` and read off which index is the 1650 Super and which
# is the 3070 — do NOT assume 0/1, PCI ordering is per-machine. -CudaDevice sets CUDA_VISIBLE_DEVICES
# for that process only, so llama.cpp cannot land on the wrong card the way ollama already has
# (measured 2026-08-20: 9.82 GB resident against an 8 GB 3070 — the 1650S was already being used
# undirected). Report the confirmed index->card mapping back so it's on record for next time.
#
# WHY THESE FOUR MODELS
#   falcon3:7b (i9, RAM) — FOURTH correction (2026-08-23) to what this hub serves, superseding
#     mistral:7b-instruct below. mistral won the quality lab (coverage 0.71) AND the throughput race
#     (7.40 tok/s) — but both were measured through OLLAMA. Audited on THIS actual serving stack
#     (llama-cpp-python), it fails outright: wraps JSON in an `{"assistant": ...}` shell, does not
#     hold key contracts — caused 114/114 judge failures overnight before this was caught. falcon3:7b
#     is the one verified ON THIS STACK — 4/4 contract tests + both defeater golds. See
#     docs/plans/ramses_second_tier.md for the full correction chain (coder-tuned ->
#     lab-winner-on-wrong-platform -> throughput-winner-at-wrong-job -> JSON-contract failure). The
#     general lesson: a model is chosen per (model, station, platform) triple, every single-axis
#     benchmark so far picked wrong.
#   mixtral:8x7b (i9, RAM) — 48 GB idle RAM is enough for a genuinely large model, but only the MoE
#     kind pays off on CPU: ~13B active params/token despite ~47B total, so it dodges the throughput
#     penalty a same-size DENSE model pays (extrapolated from measured i9 scaling: ~4.3 tok/s for
#     mixtral's 13B-active vs ~1.85 tok/s for a dense 30B — "a poor trade"). Ctx raised to 16384
#     (was 4096) on the same reasoning as falcon3's bump below: MoE shares its dense base model's
#     attention/KV-cache mechanism — only the FFN experts are duplicated — so mixtral's context cost
#     is roughly a 7B model's, not 8x one. No reason to starve it on RAM that's genuinely idle.
#   granite3.1-moe:3b (1650 Super, VRAM) — IBM, MoE again at small scale (~3B total, ~800M active/
#     token) for the same CPU/edge-efficiency reason as mixtral, and a genuinely distinct training
#     lineage (the judge-independence goal — a same-family judge shares its subject's blind spots).
#     VERIFY THE TAG PULLS — if `granite3.1-moe:3b` doesn't resolve, fall back to
#     `granite3.1-moe:1b`, already confirmed to exist in RAMSES_CLAUDE_BRIEF.md's Tier A list.
#   command-r7b (3070, VRAM) — Cohere, the most lineage-distinct model available anywhere in this
#     plan (everything else present is llama/qwen/gemma/phi/mistral/yi/deepseek/falcon/granite —
#     already flagged earlier as "worth testing" for judge independence; this GPU is its first real
#     home, and the fastest card gets the model doing the most differentiated work.
#
# CONTEXT SIZES, why "max RAM" isn't quite the right frame: ctx controls the KV cache, which is
# reserved at load whether or not a call ever uses it — oversizing it for a station that only ever
# sends ~400 tokens burns real memory for zero benefit, it does not sit "banked" for later. The CPU
# hub's two models got bumped to 16384 because 48 GB has genuine headroom past their combined ~31 GB
# of weights. The GPU hubs stayed modest (4096 / 8192) because VRAM is a hard ceiling, not RAM that
# swaps — overflow crashes the process, it does not degrade gracefully. Check the ACTUAL RAM/VRAM
# used after each first load (nvidia-smi for the GPU hubs, Task Manager for the i9 process) rather
# than trusting this arithmetic blind — verify, don't assume.
param(
    [string]$Model     = "falcon3",
    [string]$Tag       = "7b",
    [string]$Alias     = "falcon3:7b",
    [int]   $Port      = 11436,           # 11440 i9/mixtral · 11437 1650S · 11441 3070 (this plan's scheme — see the port note above re: FreshStart's own :11438 claim on the 1650S)
    [int]   $Threads   = 14,              # i9-11900K = 8C/16T; leave headroom for ollama on :11434
    [int]   $Ctx       = 16384,
    [int]   $GpuLayers = 0,               # 0 = CPU-only (the i9 hubs); 99 = all layers on GPU (the GPU hubs) — never partial
    [Nullable[int]]$CudaDevice = $null    # REQUIRED for the GPU hubs — confirm the index with nvidia-smi first, do not guess
)

$ErrorActionPreference = "Stop"
$here    = $PSScriptRoot
$HUB     = Join-Path $here "nascence_cpu_server.py"
$RESOLVE = Join-Path $here "resolve_blob.py"

foreach ($f in @($HUB, $RESOLVE)) {
    if (-not (Test-Path $f)) {
        Write-Host "[RAMSES] MISSING: $f" -ForegroundColor Red
        Write-Host "         Copy nascence_cpu_server.py and resolve_blob.py from the Nascence box's" -ForegroundColor Red
        Write-Host "         scripts\ folder into THIS folder. See README_RAMSES.md step 3." -ForegroundColor Red
        exit 1
    }
}

# Already up?
try {
    $null = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/api/tags" -UseBasicParsing -TimeoutSec 4
    Write-Host "[RAMSES] hub already up on :$Port." -ForegroundColor Green
    exit 0
} catch { }

# DUPLICATE-SPAWN GUARD — same lesson as launch_servers.ps1: a hub still starting has not bound its
# port yet, so a naive port check spawns a second one.
$existing = Get-WmiObject Win32_Process -Filter "Name='python.exe'" |
            Where-Object { $_.CommandLine -match "nascence_cpu_server" -and $_.CommandLine -match "--port $Port" }
if ($existing) {
    Write-Host "[RAMSES] hub already starting (PID $($existing.ProcessId))." -ForegroundColor Yellow
    exit 0
}

# GPU SAFETY GATE (2026-08-23): a GPU launch with no explicit device pin is exactly the "which card
# by load order, not by design" disease this whole architecture exists to avoid. Refuse rather than
# silently let CUDA pick a default.
if ($GpuLayers -gt 0 -and $null -eq $CudaDevice) {
    Write-Host "[RAMSES] -GpuLayers > 0 but -CudaDevice was not set." -ForegroundColor Red
    Write-Host "         Run nvidia-smi, confirm which index is the card you mean, and pass" -ForegroundColor Red
    Write-Host "         -CudaDevice <index> explicitly. Refusing to guess which GPU to use." -ForegroundColor Red
    exit 1
}

Write-Host "[RAMSES] resolving $Model`:$Tag from the ollama blob store ..." -ForegroundColor Cyan
$blob = & python $RESOLVE $Model $Tag 2>$null
if (-not $blob -or -not (Test-Path $blob)) {
    Write-Host "[RAMSES] could not resolve $Model`:$Tag." -ForegroundColor Red
    Write-Host "         Check 'ollama list', and if the store is off the system drive set" -ForegroundColor Red
    Write-Host "         `$env:OLLAMA_MODELS to its path first (resolve_blob.py reads it)." -ForegroundColor Red
    exit 1
}
Write-Host "[RAMSES] blob: $blob" -ForegroundColor DarkGray

$log = Join-Path $here "hub_$Port.log"
$hubArgs = @($HUB, "--model", $blob, "--alias", $Alias, "--port", $Port,
             "--threads", $Threads, "--ctx", $Ctx, "--gpu-layers", $GpuLayers,
             # --host 0.0.0.0 EXPLICITLY (2026-08-23) — nascence_cpu_server.py's own default stayed
             # 127.0.0.1 on purpose (so every LOCAL hub's exposure is unchanged); every Ramses hub
             # needs the network-reachable bind since its whole point is being called from the
             # Nascence box across the LAN, so it's passed here rather than changed globally.
             "--host", "0.0.0.0",
             # LAZY + idle-unload for the same RAM/VRAM discipline as the local dreamer: the port
             # binds immediately so nothing looks dead, the model loads on the first real call, and
             # capacity is not held hostage between sparse firings (the Deep Line's synthesis
             # stations run on 600-2700s clocks; classifier stations fire more often but briefly).
             "--lazy", "--idle-unload", "900")
if ($null -ne $CudaDevice) {
    $hubArgs += @("--cuda-device", $CudaDevice)
}

Start-Process -FilePath "python" -WindowStyle Hidden `
    -RedirectStandardOutput $log -RedirectStandardError "$log.err" `
    -ArgumentList $hubArgs

$gpuNote = if ($GpuLayers -gt 0) { ", gpu_layers=$GpuLayers, cuda_device=$CudaDevice" } else { ", CPU-only" }
Write-Host "[RAMSES] hub starting on :$Port ($Alias, t=$Threads, ctx=$Ctx, lazy$gpuNote)." -ForegroundColor Green
Write-Host "[RAMSES] log: $log" -ForegroundColor DarkGray
Write-Host ""
Write-Host "Verify from the Nascence box:  curl http://LAN-HOST:$Port/api/tags" -ForegroundColor Cyan
Write-Host "Nothing in Du points here yet - standing it up and wiring it in are separate decisions." -ForegroundColor Yellow
