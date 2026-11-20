# launch_servers.ps1  (Nascence - 2026-08-15: THE SERVING SPLIT; was 2026-06-20 single-ollama)
# WHY (docs/reports/llm_audit_aug15.md + founder): one ollama instance owning both the GPU mind and the CPU
# models was the root of the July eviction freeze, the CPU/GPU separation trouble, and the
# duplicate-runner disease that forced keep-alive off. The split:
#   [header re-synced to the $tier array 2026-08-27 - it had drifted again (still described the
#    pre-08-20-shuffle lineup). The $tier array below is the truth; this header is a summary.]
#   Self    = qwen3.5:9b   ollama :11433  GPU-ONLY (MAX_LOADED=1, keep-alive 2h) - nothing can evict it
#   Judge1  = gemma4:12b   llama.cpp hub :11439 (CPU, t=14, lazy) - panel member A moved to Ramses
#             mixtral :11438 as of 2026-09-02 (D-0121; left_lane.py grounding moved too, D-0122), but
#             this hub is NOT vestigial: core/peers.py (Twain/Shackleton letters), core/decomposed_
#             critic.py (reflection-draft critic, default fallback), and core/librarian.py (subject-
#             heading lookup, chain fallback) all still hardcode it directly. D-0125 (2026-09-02,
#             founder): keep running this tier rather than migrate those three too - do not stop
#             launching this hub  [nascence_cpu_server.py]
#   Judge2  = falcon3:7b   llama.cpp hub :11440 (CPU, t=14, lazy) - panel member B; also core/peers.py's
#             Marcus/Smith letters and the primary hub in core/librarian.py's chain (D-0125)
#   Dreamer = yi:34b-v1.5  llama.cpp hub :11442 (CPU, t=20, lazy 60s) - FAILOVER ONLY since 2026-08-27:
#             dreams moved to command-r7b on RAMSES :11441 (D-0044 move 2); this hub now loads only if
#             Ramses is unreachable. Local :11441 (old NightJ) stays unlaunched - the judge TIEBREAK
#             also moved to RAMSES :11441 (D-0044 move 3; core/judge_panel.py).
#   Ramses  = :11441 command-r7b background/subconscious lane (CHECK only, D-0057/D-0058 - the 3070's
#             sole resident) · :11438 mixtral (commitment defeater + dreamer) · :11437 granite (tiebreak
#             + curiosity worth-judge) - separate box, launched from Ramses side. Ollama :11434 is
#             RETIRED (D-0056) - do not wire anything new to it; it may still be up-but-empty pending
#             full decommission, never a lane.
# Hubs load ollama's own blobs (resolve_blob.py - blobs ARE GGUFs, verified). One model per hub, fixed
# ctx at load: duplicate runners are impossible by construction, so keep-alive is safe again.
# REVERT: git this file + core URLs (left_lane 11439->11433, peers, dream_node, model_client ports).

# RAM RULE (founder, 2026-08-15, learned the hard way — a full-tier load maxed the 64GB): resident
# CPU models are the TWO small judges only (~10GB). The 24B dreamer is a LAZY hub — its port is up
# always, the model loads on the first dream call (~60s, covered by dream_node's retry/backoff) and
# idle-unloads after 10 quiet minutes (Du barely thinks while dreams run — the swap is natural).
# yi:34b is NOT in the tier: panel disagreements resolve conservatively (no verdict) instead of a
# tiebreak; run yi manually for offline analyses only.
param()

# JOB-OBJECT WARNING (2026-09-03, F-0704): run from a Claude Code PowerShell tool, this shell sits in a
# Windows Job object with breakaway disabled - every hub spawned below (DETACHED_PROCESS or not) dies
# with the job when the Claude app restarts. That is how the whole CPU tier + supervisor vanished at
# 09:18 on 2026-09-03. Warn loudly; the job-safe path is scripts\start_supervisor_detached.ps1.
try {
    Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; public static class NascJob { [DllImport("kernel32.dll")] public static extern bool IsProcessInJob(IntPtr h, IntPtr j, out bool r); [DllImport("kernel32.dll")] public static extern IntPtr GetCurrentProcess(); }' -ErrorAction Stop
    $inJob = $false; [NascJob]::IsProcessInJob([NascJob]::GetCurrentProcess(), [IntPtr]::Zero, [ref]$inJob) | Out-Null
    if ($inJob) {
        Write-Host "[NASCENCE] WARNING: this shell is inside a Windows Job object (e.g. a Claude Code tool). Hubs launched here will be killed when that job closes." -ForegroundColor Red
        Write-Host "[NASCENCE]          Use scripts\start_supervisor_detached.ps1 instead (WMI launch, survives the caller). See CLAUDE.md / F-0704." -ForegroundColor Red
    }
} catch { }

$OLLAMA  = "http://127.0.0.1:11433"
$RAMSES  = "http://LAN-HOST:11441"   # D-0057/D-0058 (2026-08-28): background/subconscious lane moved
                                       # here (command-r7b, 3070 sole resident). Was :11434 ollama,
                                       # retired D-0056 - do not repoint this back to :11434.
$SELF_MODEL = "qwen3.5:9b"   # FULL SHUFFLE 2026-08-20 (station_matrix.md #10) - was gemma4:e4b
$ROOT    = Split-Path $PSScriptRoot -Parent
$LOGDIR  = Join-Path $ROOT "data\logs"
New-Item -ItemType Directory -Force -Path $LOGDIR | Out-Null
$PYTHON  = "python"
$HUB     = Join-Path $PSScriptRoot "nascence_cpu_server.py"
$RESOLVE = Join-Path $PSScriptRoot "resolve_blob.py"

function Test-Api($url) {
    try { $null = Invoke-WebRequest -Uri "$url/api/tags" -UseBasicParsing -TimeoutSec 4; return $true }
    catch { return $false }
}

# --- 1. The GPU instance: gemma ALONE ---------------------------------------------------------
Write-Host "[NASCENCE] Self ollama (GPU-only) on $OLLAMA ..." -ForegroundColor Cyan
if (-not (Test-Api $OLLAMA)) {
    # GPU-only discipline: one loaded model max, pinned warm. These env vars bind to THIS serve.
    $env:OLLAMA_HOST = "127.0.0.1:11433"
    $env:OLLAMA_MAX_LOADED_MODELS = "1"
    $env:OLLAMA_KEEP_ALIVE = "2h"
    Start-Process -FilePath "ollama" -ArgumentList @("serve") -WindowStyle Hidden
    Start-Sleep -Seconds 5
} else {
    Write-Host "[NASCENCE] ollama already running - NOTE: MAX_LOADED_MODELS=1/keep-alive apply only if it was started by this script (else restart ollama once to adopt them)." -ForegroundColor Yellow
}
try {
    $b = '{"model":"' + $SELF_MODEL + '","prompt":"ok","stream":false,"think":false,"keep_alive":"2h","options":{"num_predict":4}}'
    $null = Invoke-WebRequest -Uri "$OLLAMA/api/generate" -Method POST -Body $b -ContentType "application/json" -UseBasicParsing -TimeoutSec 180
    Write-Host "[NASCENCE] Self ($SELF_MODEL) warmed + pinned on the 1080 Ti." -ForegroundColor Green
} catch { Write-Host "[NASCENCE] WARN: could not warm $SELF_MODEL - $($_.Exception.Message)" -ForegroundColor Red }

# --- 2. The CPU tier: one llama.cpp hub per model ---------------------------------------------
$tier = @(
    # FULL SHUFFLE 2026-08-20 (docs/lab/station_matrix.md #10): judge16 measured the old pair in the
    # bottom third (llama3.1:8b 0.688, qwen2.5:7b 0.625, heavy false-defeat bias). New pair: gemma4:12b
    # (1.000 - eligible because the hot lane is qwen3.5:9b now) + mistral:7b-instruct (0.812). Both
    # blobs load-verified in llama-cpp-python 2026-08-20 (17s / 7s). Resident RAM ~12GB vs old ~9.6GB,
    # inside the RAM RULE. To REVERT: llama3.1/8b and qwen2.5/7b here + model_client _MODEL_BY_BASE.
    @{ Name="Judge1 gemma4:12b"; Model="gemma4"; Tag="12b"; Alias="gemma4:12b"; Port=11439; Threads=14; Extra=@("--lazy", "--idle-unload", "300") },
    # JUDGE-2 RE-SEATED mistral -> falcon3 (2026-08-21, overnight evidence): the panel was 100%
    # unavailable all night (114/114 rulings v1=answered v2=None). Root cause: hub-mistral does NOT
    # hold JSON key contracts on THIS platform - it wraps verdicts in {"assistant":...}/{"function":...}
    # shells, so every v.get(key) parsed None. Its judge16 0.812 was measured via GPU OLLAMA, whose
    # chat template + format-json it does follow. (model, station, PLATFORM) - candidates must be
    # probed on the serving stack itself. falcon3:7b auditioned ON THE HUB: 4/4 contracts held
    # (panel/defeater x2/librarian), both defeater gold verdicts correct, 5-13s. TII lineage keeps
    # three distinct families across the panel (gemma / falcon / yi).
    @{ Name="Judge2 falcon3:7b"; Model="falcon3"; Tag="7b"; Alias="falcon3:7b"; Port=11440; Threads=14; Extra=@("--lazy", "--idle-unload", "300") },
    # DREAMER = yi:34b (2026-08-16, founder call): mistral-small3.1's blob is MULTIMODAL and
    # llama-cpp-python CANNOT construct it (found by the ablation lab — the hub answered 500 on
    # every real call; it had never successfully served since the split). yi:34b loads and serves
    # JSON cleanly. Still LAZY + idle-unload per the RAM rule: ~19.5GB resident only while dreams
    # / Darwin/Keats/Lovelace letters actually run, freed 10 min after.
    # 2026-08-24 (overnight RAM safety, unattended run): idle-unload tightened 300->60s. Judge1+
    # Judge2 staying resident together is fine (~18GB, safe); the risk is THIS 28GB+ hub overlapping
    # with them - that's what maxed system RAM (5.7GB free observed) within minutes of a fresh
    # restart, with Du actively calling it. 60s is the idle-unloader's own check granularity
    # (_idle_unloader polls every 60s), so this is close to the fastest release the code supports.
    @{ Name="Dreamer yi34b (lazy)"; Model="yi"; Tag="34b-v1.5"; Alias="yi:34b-v1.5";
       Port=11442; Threads=20; Extra=@("--lazy", "--idle-unload", "60") },
    # TAKE HUB (2026-11-06, D-0539 / J-3147): the Emissary's per-turn take gets its own RESIDENT falcon3:7b hub (no
    # --lazy: loaded at startup, never idle-unloaded) so a take never pays a cold load or queues behind judge calls;
    # ~5GB resident. Keep in lockstep with scripts/supervisor.py _CPU_TIER; core/left_lane.py TAKE_URL points here.
    @{ Name="Take falcon3:7b (resident)"; Model="falcon3"; Tag="7b"; Alias="falcon3:7b"; Port=11445; Threads=16; Extra=@() }
)
foreach ($t in $tier) {
    $url = "http://127.0.0.1:$($t.Port)"
    if (Test-Api $url) { Write-Host "[NASCENCE] $($t.Name) already up on :$($t.Port)." -ForegroundColor Green; continue }
    # DUPLICATE-SPAWN GUARD (2026-08-15, learned the hard way): a hub whose port is not bound yet may
    # still be starting - check for an existing process wearing this port before spawning another.
    $existing = Get-WmiObject Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe'" |
                Where-Object { $_.CommandLine -match "nascence_cpu_server" -and $_.CommandLine -match "--port $($t.Port)" }
    if ($existing) { Write-Host "[NASCENCE] $($t.Name) already starting (PID $($existing.ProcessId))." -ForegroundColor Yellow; continue }
    $blob = & $PYTHON $RESOLVE $t.Model $t.Tag 2>$null
    if (-not $blob) { Write-Host "[NASCENCE] WARN: no blob for $($t.Name) - is it pulled in ollama?" -ForegroundColor Red; continue }
    $log = Join-Path $LOGDIR ("cpu_tier_" + $t.Port + ".log")
    $pyLauncher = "import subprocess, sys; cmd = [sys.executable, r'$HUB', '--model', r'$blob', '--alias', '$($t.Alias)', '--port', '$($t.Port)', '--threads', '$($t.Threads)', '--ctx', '8192', '--log', r'$log'] + '$([string]::Join(' ', $t.Extra))'.split(); subprocess.Popen(cmd, creationflags=0x00000008 | 0x00000200)"
    & $PYTHON -c $pyLauncher
}
# Ports bind IMMEDIATELY now (models load behind them) - short wait, honest report
$deadline = (Get-Date).AddSeconds(60)
foreach ($t in $tier) {
    $url = "http://127.0.0.1:$($t.Port)"
    while (-not (Test-Api $url) -and (Get-Date) -lt $deadline) { Start-Sleep -Seconds 3 }
    if (Test-Api $url) { Write-Host "[NASCENCE] $($t.Name) port UP on :$($t.Port) (model loads behind it)." -ForegroundColor Green }
    else { Write-Host "[NASCENCE] WARN: $($t.Name) port not up (see $LOGDIR\cpu_tier_$($t.Port).log.err) - callers fail-open." -ForegroundColor Yellow }
}

# --- 3. Ramses (Subconscious/background lane, command-r7b, D-0057/D-0058) - CHECK only --------
Write-Host "[NASCENCE] Subconscious (command-r7b) on Ramses $RAMSES (3070) - checking..." -ForegroundColor Cyan
if (Test-Api $RAMSES) { Write-Host "[NASCENCE] Ramses reachable - subconscious lane up." -ForegroundColor Green }
else { Write-Host "[NASCENCE] Ramses asleep - subconscious falls back to the local lane (documented SPOF)." -ForegroundColor Yellow }

Write-Host "[NASCENCE] Serving split complete: GPU=gemma alone - judges 11439/11440 lazy (idle-unload 300s), dreamer 11442 lazy (RAM rule: ~10GB idle)." -ForegroundColor Cyan
