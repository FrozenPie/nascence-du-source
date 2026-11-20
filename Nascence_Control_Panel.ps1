<#
.SYNOPSIS
    Nascence - Control Panel
.DESCRIPTION
    Unified interface to manage the Nascence cognitive architecture:
    start/stop the GPU and CPU inference servers, launch the REPL
    for conversation, and inspect Carl's memory and inner state.
.NOTES
    Run from C:\Nascence\ or anywhere - all paths are absolute.
    SERVING (2026-09-02 re-sync - see docs/plans/ramses_second_tier.md): Self = qwen3.5:9b (1080 Ti
    GPU-only, local :11433, 24K ctx, MAX_LOADED=1); Judge1 = gemma4:12b (llama.cpp hub :11439, panel
    voting itself now lives on Ramses mixtral :11438, D-0121); Judge2 = falcon3:7b (hub :11440,
    re-seated 2026-08-21); Dreamer = yi:34b-v1.5 (hub :11442, lazy); Subconscious = command-r7b (Ramses
    3070 :11441 - SEPARATE box; the old phi3:mini/ollama :11434 was retired 2026-08-28, D-0056). Judge2's
    old mistral:7b-instruct seat and llama3.1:8b/qwen2.5:7b hold no seat. launch_servers.ps1 is the
    single source of truth for what serves where; this panel only starts/stops/reports (and, as of
    F-0684, [1] Full Start actually calls it now). FreshStart must not run its swarm on the 1080 Ti
    simultaneously.
#>

$ErrorActionPreference = "Continue"
try { $Host.UI.RawUI.WindowTitle = "Nascence - Control Panel (qwen / gemma / mistral / phi / yi)" } catch { }
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# --- Paths -------------------------------------------------------------------
$NASCENCE   = "C:\Nascence"
$SCRIPTS    = Join-Path $NASCENCE "scripts"
$DATA       = Join-Path $NASCENCE "data"
$DOCS       = Join-Path $NASCENCE "docs"
$PYTHON     = "python"       # system python 3.14 on PATH

# SERVING (2026-09-02 re-sync): local ollama (:11433) = Self qwen3.5:9b ALONE (GPU-only,
# MAX_LOADED=1). CPU tier (llama.cpp hubs): Judge1 gemma4:12b :11439, Judge2 falcon3:7b :11440,
# Dreamer yi:34b :11442 (lazy). SUBCONSCIOUS = command-r7b on RAMSES (:11441, separate machine - checked,
# not started). See launch_servers.ps1 (authoritative) + docs/lab/station_matrix.md #10 (why).
$HOT_PORT     = 11433            # local ollama: Self qwen3.5:9b ALONE (GPU-only; judges+dreamer are hubs)
$RAMSES_HOST  = "LAN-HOST"     # Ramses 3070 - the Subconscious lane
# BUG FIX 2026-09-02 (F-0685): was 11434 (Ramses ollama, phi3:mini) -- RETIRED 2026-08-28 (D-0056,
# F-0389 lock). The real background/subconscious lane has served on command-r7b at Ramses :11441
# since then (core/schema.py SERVE_URLS["background"]). The old value made this panel report the
# subconscious lane ASLEEP forever, regardless of the real lane's health.
$SUBCON_PORT  = 11441            # Subconscious = command-r7b on Ramses (synthesis/reading/sleep-batch)
$HUD_PORT     = 8080             # HUD dashboard (hud/server.py) - plan monitors, memory, live logs
$DB_PATH    = Join-Path $DATA "memory\nascence.db"

# --- Helpers -----------------------------------------------------------------

function Test-Port {
    param([int]$Port, [string]$TargetHost = "127.0.0.1")
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $iar = $tcp.BeginConnect($TargetHost, $Port, $null, $null)
        $ok  = $iar.AsyncWaitHandle.WaitOne(3000, $false)   # 3s cap (Ramses may be asleep)
        $live = $ok -and $tcp.Connected
        $tcp.Close()
        return $live
    } catch { return $false }
}

function Get-LlamaServerOnPort {
    param([int]$Port)
    Get-WmiObject Win32_Process -Filter "Name='llama-server.exe'" |
        Where-Object { $_.CommandLine -match "--port $Port" }
}

function Get-PythonScript {
    param([string]$Script)
    Get-WmiObject Win32_Process -Filter "Name='python.exe'" |
        Where-Object { $_.CommandLine -match $Script }
}

function Write-Status {
    param([string]$Label, [string]$Value, [string]$Color = "Gray")
    Write-Host ("  {0,-22}: " -f $Label) -NoNewline -ForegroundColor DarkGray
    Write-Host $Value -ForegroundColor $Color
}

function Show-Header {
    try { Clear-Host } catch { }
    Write-Host ""
    Write-Host "  ================================================================" -ForegroundColor Cyan
    Write-Host "       NASCENCE  --  CONTROL PANEL  (qwen / gemma / mistral / phi / yi)       " -ForegroundColor White
    Write-Host "       grounded in Jung, becoming his own  |  14/14              " -ForegroundColor DarkGray
    Write-Host "  ================================================================" -ForegroundColor Cyan
    Write-Host ""
}

# --- Status ------------------------------------------------------------------

function Show-Status {
    Show-Header
    Write-Host "  -- SERVER STATUS -------------------------------------" -ForegroundColor DarkCyan
    Write-Host ""

    # 2026-08-15 SERVING SPLIT: gemma ALONE on ollama (GPU-only); judges + dreamer on llama.cpp hubs
    $hotPort = Test-Port -Port $HOT_PORT
    if ($hotPort) { Write-Status "Self (11433, GPU-only)" "READY - qwen3.5:9b alone on the 1080 Ti @24k (full shuffle 08-20)" "Green" }
    else          { Write-Status "Self (11433, GPU-only)" "OFFLINE - local ollama down" "DarkGray" }
    # 2026-08-19: relabeled to match the actual 2026-08-16 topology (health-check finding) — 11441's
    # "Night judge"/tiebreak role was retired from the default tier (launch_servers.ps1 no longer starts
    # it; "down" here is expected, not a fault), and 11442 runs yi:34b-v1.5 as the Dreamer, not a 24B model
    # (mistral-24B's blob never successfully served — see launch_servers.ps1's own note).
    $j1 = Test-Port -Port 11439; $j2 = Test-Port -Port 11440
    $nj = Test-Port -Port 11441; $dr = Test-Port -Port 11442
    $tierTxt = "J1(gemma4:12b):" + $(if ($j1) {"UP"} else {"down"}) + "  J2(falcon3:7b):" + $(if ($j2) {"UP"} else {"down"}) +
               "  Tiebreak(yi, optional):" + $(if ($nj) {"UP"} else {"down (expected)"}) + "  Dream(yi):" + $(if ($dr) {"UP"} else {"down"})
    $tierCol = if ($j1 -and $j2 -and $dr) { "Green" } elseif ($j1 -or $j2 -or $dr) { "Yellow" } else { "DarkGray" }
    Write-Status "CPU tier (llama.cpp)" $tierTxt $tierCol

    # Subconscious - command-r7b on Ramses (synthesis/reading/sleep-batch; falls back to local if asleep)
    $subconPort = Test-Port -Port $SUBCON_PORT -TargetHost $RAMSES_HOST
    if ($subconPort) { Write-Status "Subconscious (Ramses 11441)" "READY - command-r7b on the 3070" "Green" }
    else             { Write-Status "Subconscious (Ramses 11441)" "ASLEEP - subconscious falls back to local" "Yellow" }

    # Supervisor
    $sv = Get-PythonScript -Script "supervisor.py"
    Write-Status "Supervisor" $(if($sv){"RUNNING (PID: $($sv.ProcessId))"}else{"not running"}) $(if($sv){"Green"}else{"DarkGray"})

    # REPL
    $repl = Get-PythonScript -Script "run_nascence.py"
    Write-Status "REPL" $(if($repl){"ACTIVE - Carl is awake"}else{"not running"}) $(if($repl){"Cyan"}else{"DarkGray"})

    # HUD dashboard
    $hudOk = Test-Port -Port $HUD_PORT
    Write-Status "HUD (8080)" $(if($hudOk){"UP - http://localhost:$HUD_PORT"}else{"not running - [H] to start"}) $(if($hudOk){"Green"}else{"DarkGray"})

    Write-Host ""
    Write-Host "  -- MEMORY SNAPSHOT -----------------------------------" -ForegroundColor DarkCyan
    Write-Host ""

    if (Test-Path $DB_PATH) {
        try {
            $dbEsc = $DB_PATH -replace '\\','\\\\'
            $rows = & $PYTHON -c "import sqlite3,json; db=sqlite3.connect('$dbEsc'); t=db.execute('SELECT COUNT(*) FROM memory_fragments').fetchone()[0]; sh=db.execute('SELECT COUNT(*) FROM shadow_events').fetchone()[0]; dr=db.execute(\"SELECT COUNT(*) FROM memory_fragments WHERE origin='dream'\").fetchone()[0]; ss=db.execute(\"SELECT COUNT(*) FROM memory_fragments WHERE origin='session_summary'\").fetchone()[0]; ai=db.execute(\"SELECT COUNT(*) FROM memory_fragments WHERE origin='active_imagination'\").fetchone()[0]; print(json.dumps({'total':t,'shadows':sh,'dreams':dr,'sessions':ss,'ai':ai})); db.close()" 2>$null
            if ($rows) {
                $d = $rows | ConvertFrom-Json
                Write-Status "Total fragments" $d.total "White"
                Write-Status "Shadow events" $d.shadows $(if([int]$d.shadows -gt 0){"Yellow"}else{"DarkGray"})
                Write-Status "Dreams" $d.dreams $(if([int]$d.dreams -gt 0){"Magenta"}else{"DarkGray"})
                Write-Status "Session summaries" $d.sessions $(if([int]$d.sessions -gt 0){"Green"}else{"DarkGray"})
                Write-Status "Active imaginations" $d.ai $(if([int]$d.ai -gt 0){"Cyan"}else{"DarkGray"})
            }
        } catch {
            Write-Status "DB" "could not query (DB may be locked)" "Yellow"
        }
    } else {
        Write-Status "DB" "not found at $DB_PATH" "Red"
    }

    # Conversation state
    $convPath = Join-Path $DATA "conversation_state.json"
    if (Test-Path $convPath) {
        try {
            $conv = Get-Content $convPath -Raw | ConvertFrom-Json
            $ended = $conv.ended_human
            $n = $conv.recent_exchanges.Count
            Write-Status "Last session" "$n exchanges (ended $ended)" "Green"
        } catch { }
    } else {
        Write-Status "Last session" "no prior session saved yet" "DarkGray"
    }

    # Subconscious state
    $scPath = Join-Path $DATA "subconscious_state.json"
    if (Test-Path $scPath) {
        try {
            $sc = Get-Content $scPath -Raw | ConvertFrom-Json
            $tensions = @($sc.tensions).Count
            $scans = $sc.scan_count
            Write-Status "Subconscious" "scan #$scans  $tensions tension(s)" $(if($tensions -gt 0){"Yellow"}else{"DarkGray"})
        } catch { }
    }

    # Affect state
    $affPath = Join-Path $DATA "affect_state.json"
    if (Test-Path $affPath) {
        try {
            $aff = Get-Content $affPath -Raw | ConvertFrom-Json
            $v = [math]::Round($aff.valence, 2)
            $ar = [math]::Round($aff.arousal, 2)
            $sign = if ($v -ge 0) {"+"} else {""}
            Write-Status "Affect (restored)" "valence ${sign}${v}  arousal ${ar}" "Cyan"
        } catch { }
    }

    Write-Host ""
}

# --- Server management -------------------------------------------------------

function Start-Servers {
    Write-Host ""
    Write-Host "  Starting servers (Self qwen3.5:9b on ollama $HOT_PORT; judges gemma4:12b+mistral, dreamer yi on hubs; Subconscious phi3 on Ramses)..." -ForegroundColor Cyan

    # Delegate to the canonical launcher: ensures local ollama (Self GPU + Judge CPU), warms both,
    # and checks Ramses (the Subconscious 3070). The Bonsai :11460 lane is retired - nothing to clear.
    & (Join-Path $SCRIPTS "launch_servers.ps1")

    Write-Host ""
    Write-Host "  Waiting for local ollama (Self+Judge, $HOT_PORT) up to 90s (cold model load)..." -ForegroundColor Yellow
    $timeout = 90; $elapsed = 0
    while ($elapsed -lt $timeout) {
        if (Test-Port -Port $HOT_PORT) { Write-Host "  Local ollama ready after ${elapsed}s." -ForegroundColor Green; break }
        Start-Sleep -Seconds 3; $elapsed += 3
        Write-Host "  ...${elapsed}s" -ForegroundColor DarkGray
    }
    if (-not (Test-Port -Port $HOT_PORT)) {
        Write-Host "  WARNING: local ollama not responding. Is ollama running, and is qwen3.5:9b pulled?" -ForegroundColor Red
        Write-Host "  (OLLAMA_HOST=127.0.0.1:11433; run: python scripts\verify_lanes.py)" -ForegroundColor Yellow
    }

    Write-Host ""
    Read-Host "  Press Enter to return to menu"
}

function Stop-Servers {
    Write-Host ""
    Write-Host "  Stopping the local ollama (Self on $HOT_PORT) + the CPU hub tier (judges/dreamer). The Subconscious on Ramses is left alone." -ForegroundColor Yellow

    # SUPERVISOR FIRST (2026-08-21, learned the hard way): the watchdog survives its window closing
    # and relaunches ollama ~30s after we stop it - stopping servers while it lives is a race.
    $sv = Get-PythonScript -Script "supervisor.py"
    if ($sv) {
        Stop-Process -Id $sv.ProcessId -Force -ErrorAction SilentlyContinue
        Write-Host "  Supervisor (watchdog) stopped - it would have restarted the servers otherwise." -ForegroundColor Green
    }

    $oll = Get-Process -Name "ollama" -ErrorAction SilentlyContinue
    if ($oll) { $oll | Stop-Process -Force; Write-Host "  Local ollama (Self, GPU-only) stopped." -ForegroundColor Green }
    else      { Write-Host "  Local ollama was not running." -ForegroundColor DarkGray }

    # ORPHAN RUNNER SWEEP (2026-08-21, the double-loaded-1080 incident): force-killing ollama.exe
    # ORPHANS its llama-server.exe model runners - they keep the model resident in VRAM with no
    # parent to reap them. Sweep every llama-server under the Ollama install dir.
    Start-Sleep -Seconds 1
    $orphans = Get-WmiObject Win32_Process -Filter "Name='llama-server.exe'" |
               Where-Object { $_.ExecutablePath -match 'Ollama' }
    if ($orphans) {
        $orphans | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
        Write-Host "  Swept $(@($orphans).Count) ollama model runner(s) (llama-server.exe) - VRAM freed." -ForegroundColor Green
    }

    # CPU tier (2026-08-15 split): stop the llama.cpp hub servers (judges/night-judge/dreamer)
    $hubs = Get-WmiObject Win32_Process -Filter "Name='python.exe'" |
            Where-Object { $_.CommandLine -match "nascence_cpu_server" }
    if ($hubs) {
        $hubs | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
        Write-Host "  CPU tier stopped ($(@($hubs).Count) hub server(s): judges + dreamer)." -ForegroundColor Green
    } else { Write-Host "  CPU tier was not running." -ForegroundColor DarkGray }

    # Sweep any vestigial Bonsai :11460 llama-server (retired under Option B) if one is still lingering.
    $staleBonsai = Get-LlamaServerOnPort -Port 11460
    if ($staleBonsai) { Stop-Process -Id $staleBonsai.ProcessId -Force; Write-Host "  Cleared vestigial Bonsai :11460 server." -ForegroundColor DarkGray }

    Write-Host ""
    Read-Host "  Press Enter to return to menu"
}

# --- REPL --------------------------------------------------------------------

function Start-REPL {
    # Check servers are up first
    $hotReady    = Test-Port -Port $HOT_PORT
    $subconReady = Test-Port -Port $SUBCON_PORT -TargetHost $RAMSES_HOST

    if (-not $hotReady) {
        Write-Host ""
        Write-Host "  WARNING: local ollama (Self+Judge, 11433) is not responding." -ForegroundColor Red
        Write-Host "  Carl may not function correctly. Start servers first ([1])." -ForegroundColor Yellow
        Write-Host ""
        $confirm = Read-Host "  Continue anyway? (y/N)"
        if ($confirm -ne "y" -and $confirm -ne "Y") { return }
    }
    if (-not $subconReady) {
        Write-Host ""
        Write-Host "  NOTE: Subconscious (command-r7b on Ramses 11441) is asleep - it falls back to the local lane. (Dreams run locally on yi:34b regardless.)" -ForegroundColor Yellow
        Write-Host ""
    }

    Write-Host ""
    Write-Host "  ----------------------------------------------------" -ForegroundColor DarkCyan
    Write-Host "  Waking him up..." -ForegroundColor Cyan
    Write-Host "  Type /status to see his current state." -ForegroundColor DarkGray
    Write-Host "  Type /shadow to see his subconscious." -ForegroundColor DarkGray
    Write-Host "  Type /quit to end the session (he will dream on exit)." -ForegroundColor DarkGray
    Write-Host "  ----------------------------------------------------" -ForegroundColor DarkCyan
    Write-Host ""

    Push-Location $NASCENCE
    & $PYTHON scripts\run_nascence.py
    Pop-Location

    Write-Host ""
    Write-Host "  Session ended. Memory and affect persisted for next time." -ForegroundColor Green
    Write-Host ""
    Read-Host "  Press Enter to return to menu"
}

function Start-Composer {
    # Launches the Composer window (Tkinter, scripts/du_composer.py) - a multi-line
    # message box with a Send button, for typing to Carl without the REPL's
    # press-Enter-submits-immediately behaviour. It talks to whichever REPL is
    # already running over a local-only socket; the REPL must be up ([3] or [1])
    # or the button will just report it can't reach him.
    if (-not (Test-Port -Port $HOT_PORT)) {
        Write-Host ""
        Write-Host "  NOTE: the REPL doesn't look like it's running yet (Self ollama, 11433, is down)." -ForegroundColor Yellow
        Write-Host "  Start it first with [1] or [3] - the Composer window will open either way," -ForegroundColor Yellow
        Write-Host "  but Send will fail until the REPL is up." -ForegroundColor Yellow
        Write-Host ""
    }
    Write-Host "  Opening Composer window..." -ForegroundColor DarkCyan
    $pythonw = Get-Command "pythonw" -ErrorAction SilentlyContinue
    Start-Process -FilePath $(if ($pythonw) { "pythonw" } else { $PYTHON }) `
        -ArgumentList "scripts\du_composer.py" `
        -WorkingDirectory $NASCENCE
}

function Start-Supervisor {
    # Launch the watchdog if not already running. It ensures both lanes are up AND
    # auto-restarts a dead/zombie one (the overnight-wedge failure mode). Idempotent.
    $sv = Get-PythonScript -Script "supervisor.py"
    if ($sv) {
        Write-Host "  Supervisor already running (PID $($sv.ProcessId))." -ForegroundColor Green
        return
    }
    Write-Host "  Launching supervisor (watchdog: starts + monitors both lanes)..." -ForegroundColor DarkCyan
    Start-Process -FilePath $PYTHON `
        -ArgumentList "scripts\supervisor.py" `
        -WorkingDirectory $NASCENCE `
        -RedirectStandardOutput (Join-Path $DATA "supervisor.log") `
        -RedirectStandardError  (Join-Path $DATA "supervisor.err.log") `
        -WindowStyle Hidden
}

function Start-HUD {
    param([switch]$OpenBrowser)
    # Launch the HUD dashboard if not already up. Idempotent. NOTE: the HUD reads its plan-monitor
    # registry at STARTUP - after editing hud/server.py it must be restarted (stop the old python
    # hud/server.py process first), or the new cards will not appear (learned 2026-07-05).
    if (Test-Port -Port $HUD_PORT) {
        Write-Host "  HUD already up on http://localhost:$HUD_PORT" -ForegroundColor Green
    } else {
        Write-Host "  Launching HUD dashboard (http://localhost:$HUD_PORT)..." -ForegroundColor DarkCyan
        Start-Process -FilePath $PYTHON `
            -ArgumentList "hud\server.py" `
            -WorkingDirectory $NASCENCE `
            -RedirectStandardOutput (Join-Path $DATA "hud.log") `
            -RedirectStandardError  (Join-Path $DATA "hud.err.log") `
            -WindowStyle Hidden
        $elapsed = 0
        while ($elapsed -lt 12) {
            if (Test-Port -Port $HUD_PORT) { Write-Host "  HUD ready after ${elapsed}s." -ForegroundColor Green; break }
            Start-Sleep -Seconds 2; $elapsed += 2
        }
        if (-not (Test-Port -Port $HUD_PORT)) {
            Write-Host "  HUD not responding yet - check data\hud.err.log" -ForegroundColor Yellow
        }
    }
    if ($OpenBrowser) { Start-Process "http://localhost:$HUD_PORT" }
}

function Full-Start {
    Show-Header
    Write-Host "  FULL START - CPU tier + supervisor (watchdog) + HUD + REPL" -ForegroundColor Cyan
    Write-Host ""

    # BUG FIX 2026-09-02 (F-0684): this used to call ONLY Start-Supervisor for "servers", but
    # scripts/supervisor.py's watchdog manages exactly one thing -- local ollama (:11433, Self/GPU).
    # It has never known about the CPU judge tier (Judge1 :11439, Judge2 :11440, Dreamer :11442),
    # so [1] Full Start silently skipped the whole CPU tier on every run, no matter how many times
    # Du was restarted -- the real cause of a full session's "transport error on 127.0.0.1:11439"
    # noise (F-0657/F-0683) that D-0121/D-0122/D-0125 chased through five different call sites
    # before landing here. [2] Start Servers never had this bug (it calls launch_servers.ps1
    # directly). Full-Start now does the same first, THEN hands the GPU lane to the supervisor's
    # ongoing watchdog -- the supervisor still adopts the already-warm lane rather than double-
    # launching it (Start-Supervisor -> ensure() checks health before launching).
    Start-Servers-Silent
    Start-Supervisor
    Start-HUD

    Write-Host "  Waiting for GPU lane to be ready (up to 40s)..." -ForegroundColor Yellow
    $elapsed = 0
    while ($elapsed -lt 40) {
        if (Test-Port -Port $HOT_PORT) { Write-Host "  HOT lane ready after ${elapsed}s." -ForegroundColor Green; break }
        Start-Sleep -Seconds 3
        $elapsed += 3
    }
    if (-not (Test-Port -Port $HOT_PORT)) {
        Write-Host "  GPU lane not ready yet - supervisor may still be loading. Check [5] Status." -ForegroundColor Yellow
    }
    $j1 = Test-Port -Port 11439; $j2 = Test-Port -Port 11440
    if (-not ($j1 -and $j2)) {
        Write-Host "  NOTE: CPU judge tier not fully up (J1 gemma4:12b:$j1  J2 falcon3:7b:$j2) - check [5] Status or data\logs\cpu_tier_*.log.err." -ForegroundColor Yellow
    }

    Start-REPL
}

function Start-Servers-Silent {
    & (Join-Path $SCRIPTS "launch_servers.ps1")
}

# --- Inspect commands --------------------------------------------------------

function Show-LatestDream {
    $dreamLog = Join-Path $DATA "dream_log.jsonl"
    Write-Host ""
    if (-not (Test-Path $dreamLog)) {
        Write-Host "  No dreams recorded yet." -ForegroundColor DarkGray
        Write-Host "  (Dreams are generated on /quit after a conversation.)" -ForegroundColor DarkGray
    } else {
        Write-Host "  -- DREAM LOG (most recent) -------------------------" -ForegroundColor Magenta
        Write-Host ""
        $lines = Get-Content $dreamLog | Select-Object -Last 3
        foreach ($line in $lines) {
            try {
                $d = $line | ConvertFrom-Json
                $ts = [DateTimeOffset]::FromUnixTimeSeconds([long]$d.ts).LocalDateTime.ToString("yyyy-MM-dd HH:mm")
                Write-Host "  [$ts]" -ForegroundColor DarkMagenta
                Write-Host "  Source: $($d.tension_source)" -ForegroundColor DarkGray
                Write-Host "  Symbols: $($d.symbols -join ', ')" -ForegroundColor DarkGray
                Write-Host ""
                # Word-wrap the narrative
                $words = $d.narrative -split ' '
                $line_buf = "  "
                foreach ($w in $words) {
                    if (($line_buf + $w).Length -gt 70) {
                        Write-Host $line_buf -ForegroundColor White
                        $line_buf = "  $w "
                    } else { $line_buf += "$w " }
                }
                if ($line_buf.Trim()) { Write-Host $line_buf -ForegroundColor White }
                Write-Host ""
                Write-Host "  ------------------------------------------------" -ForegroundColor DarkGray
                Write-Host ""
            } catch { }
        }
    }
    Read-Host "  Press Enter to return"
}

function Show-InnerThoughts {
    $monoLog = Join-Path $DATA "monologue_log.jsonl"
    Write-Host ""
    if (-not (Test-Path $monoLog)) {
        Write-Host "  No inner thoughts recorded yet." -ForegroundColor DarkGray
        Write-Host "  (He thinks to himself when idle for 75s+ during a session.)" -ForegroundColor DarkGray
    } else {
        Write-Host "  -- INNER MONOLOGUE (most recent thoughts) ----------" -ForegroundColor Cyan
        Write-Host "  What he thinks about when no one is speaking to him." -ForegroundColor DarkGray
        Write-Host ""
        $lines = Get-Content $monoLog | Select-Object -Last 12
        foreach ($line in $lines) {
            try {
                $t = $line | ConvertFrom-Json
                $ts = [DateTimeOffset]::FromUnixTimeSeconds([long]$t.ts).LocalDateTime.ToString("MM-dd HH:mm")
                $about = ($t.about -replace '[^\x20-\x7E]','?')
                $thought = ($t.thought -replace '[^\x20-\x7E]','?')
                Write-Host "  [$ts] " -NoNewline -ForegroundColor DarkGray
                Write-Host "($about)" -ForegroundColor DarkCyan
                # word-wrap
                $words = $thought -split ' '
                $buf = "    "
                foreach ($w in $words) {
                    if (($buf + $w).Length -gt 72) { Write-Host $buf -ForegroundColor White; $buf = "    $w " }
                    else { $buf += "$w " }
                }
                if ($buf.Trim()) { Write-Host $buf -ForegroundColor White }
                Write-Host ""
            } catch { }
        }
    }
    Read-Host "  Press Enter to return"
}

function Show-Shadow {
    $scPath = Join-Path $DATA "subconscious_state.json"
    Write-Host ""
    if (-not (Test-Path $scPath)) {
        Write-Host "  No subconscious state yet - run a session first." -ForegroundColor DarkGray
    } else {
        Write-Host "  -- SUBCONSCIOUS STATE ------------------------------" -ForegroundColor Yellow
        Write-Host ""
        try {
            $sc = Get-Content $scPath -Raw | ConvertFrom-Json
            Write-Host ("  Scan count:     {0}" -f $sc.scan_count) -ForegroundColor White
            Write-Host ("  AI sessions:    {0}" -f $(if($sc.active_imagination_count){$sc.active_imagination_count}else{0})) -ForegroundColor White

            $tensions = @($sc.tensions)
            Write-Host ("  Tensions:       {0}" -f $tensions.Count) -ForegroundColor $(if($tensions.Count -gt 0){"Yellow"}else{"DarkGray"})
            foreach ($t in ($tensions | Sort-Object { -[int]$_.count } | Select-Object -First 5)) {
                $spread_h = [math]::Round(($t.last_ts - $t.first_ts) / 3600, 1)
                $synth = if ($t.last_synthesised) {"synthesised"} else {"pending"}
                $members = @($t.member_event_ids).Count
                Write-Host ("    [{0}x / {1}h / {2} / {3} events] {4}" -f $t.count, $spread_h, $synth, $members, ($t.label -replace '[^\x20-\x7E]','?')) -ForegroundColor Gray
            }

            $sig = $sc.emotional_signature
            if ($sig -and $sig.sample_count) {
                Write-Host ""
                Write-Host ("  Emotional signature (n={0}):" -f $sig.sample_count) -ForegroundColor Cyan
                Write-Host ("    surprise={0:F3}  fear={1:F3}  joy={2:F3}  arousal={3:F3}  valence={4:+F3}" -f `
                    $sig.surprise, $sig.fear, $sig.joy, $sig.arousal, $sig.valence) -ForegroundColor White
            }

            $drift = $sc.baseline_drift
            if ($drift) {
                $nonzero = @($drift.PSObject.Properties | Where-Object { [math]::Abs($_.Value) -gt 0.0001 })
                if ($nonzero) {
                    $driftStr = ($nonzero | ForEach-Object { "$($_.Name) $([math]::Round($_.Value,4).ToString('+0.0000;-0.0000'))" }) -join "  "
                    Write-Host ("  Baseline drift: {0}" -f $driftStr) -ForegroundColor Cyan
                }
            }
        } catch {
            Write-Host "  (failed to parse subconscious_state.json)" -ForegroundColor Red
        }
    }
    Write-Host ""
    Read-Host "  Press Enter to return"
}

function Show-RecentLog {
    $logPath = Join-Path $DATA "nascence.log"
    Write-Host ""
    if (-not (Test-Path $logPath)) {
        Write-Host "  No log file yet." -ForegroundColor DarkGray
    } else {
        Write-Host "  -- RECENT LOG (last 30 lines) ----------------------" -ForegroundColor DarkCyan
        Write-Host ""
        Get-Content $logPath -Tail 30 | ForEach-Object {
            $col = if ($_ -match "ERROR|FAILED") {"Red"} elseif ($_ -match "critic rejected|shadow|dream|sleep") {"Yellow"} elseif ($_ -match "CYCLE.*complete") {"Green"} else {"DarkGray"}
            Write-Host ("  " + $_ -replace "[^\x20-\x7E]","?") -ForegroundColor $col
        }
        Write-Host ""
    }
    Read-Host "  Press Enter to return"
}

function Open-SystemReview {
    $reviewPath = Join-Path $DOCS "System_Overview.html"
    if (Test-Path $reviewPath) {
        Start-Process $reviewPath
        Write-Host "  Opened System_Overview.html in browser." -ForegroundColor Green
    } else {
        Write-Host "  System_Overview.html not found." -ForegroundColor Red
    }
    Start-Sleep -Seconds 1
}

function Open-Roadmap {
    $roadmapPath = Join-Path $DOCS "Nascence_Roadmap.html"
    if (Test-Path $roadmapPath) {
        Start-Process $roadmapPath
        Write-Host "  Opened Nascence_Roadmap.html in browser." -ForegroundColor Green
    } else {
        Write-Host "  Nascence_Roadmap.html not found." -ForegroundColor Red
    }
    Start-Sleep -Seconds 1
}

# --- Main menu ---------------------------------------------------------------

function Show-Menu {
    Show-Header

    # Quick server health in menu header
    $hotOk    = Test-Port -Port $HOT_PORT
    $subconOk = Test-Port -Port $SUBCON_PORT -TargetHost $RAMSES_HOST
    $hotStr    = if ($hotOk)    {" READY"} else {" OFFLINE"}
    $subconStr = if ($subconOk) {" READY"} else {" ASLEEP"}
    $hotCol    = if ($hotOk)    {"Green"} else {"DarkGray"}
    $subconCol = if ($subconOk) {"Green"} else {"DarkYellow"}

    Write-Host ("  Self+Judge+Dream (11433): ") -NoNewline -ForegroundColor DarkGray
    Write-Host $hotStr -NoNewline -ForegroundColor $hotCol
    Write-Host ("    Subconscious (Ramses 11441): ") -NoNewline -ForegroundColor DarkGray
    Write-Host $subconStr -NoNewline -ForegroundColor $subconCol
    # Supervisor presence
    $svRun = Get-PythonScript -Script "supervisor.py"
    Write-Host ("    Watchdog: ") -NoNewline -ForegroundColor DarkGray
    Write-Host $(if($svRun){"ON"}else{"off"}) -ForegroundColor $(if($svRun){"Green"}else{"DarkYellow"})

    # The local ollama hosts Self + Judge + Dreamer - if it's down, nothing runs. Flag loudly.
    if (-not $hotOk) {
        Write-Host "  !! Self+Judge+Dream ollama (11433) DOWN - Du cannot run. Use [1] or [2] to start it." -ForegroundColor Red
    }
    elseif (-not $subconOk) {
        Write-Host "  -- Subconscious asleep (Ramses) - falls back to the local lane (fine; dreams still run locally on yi:34b)." -ForegroundColor DarkYellow
    }
    Write-Host ""

    Write-Host "  -- START ---------------------------------------------" -ForegroundColor DarkCyan
    Write-Host "  [1]  Full Start - supervisor + servers + HUD + REPL" -ForegroundColor White
    Write-Host "  [2]  Start Servers only" -ForegroundColor White
    Write-Host "  [3]  Open REPL only (servers must already be running)" -ForegroundColor White
    Write-Host "  [C]  Open Composer window (multi-line message + Send button)" -ForegroundColor White
    Write-Host "  [H]  Start HUD dashboard + open in browser (port 8080)" -ForegroundColor White
    Write-Host ""
    Write-Host "  -- STOP ----------------------------------------------" -ForegroundColor DarkCyan
    Write-Host "  [4]  Stop Servers" -ForegroundColor White
    Write-Host ""
    Write-Host "  -- INSPECT -------------------------------------------" -ForegroundColor DarkCyan
    Write-Host "  [5]  Status & Memory Snapshot" -ForegroundColor White
    Write-Host "  [6]  Latest Dreams" -ForegroundColor White
    Write-Host "  [7]  Shadow / Subconscious State" -ForegroundColor White
    Write-Host "  [8]  Recent Log (last 30 lines)" -ForegroundColor White
    Write-Host "  [T]  Inner Thoughts (what he thinks when idle)" -ForegroundColor White
    Write-Host ""
    Write-Host "  -- DOCS ----------------------------------------------" -ForegroundColor DarkCyan
    Write-Host "  [9]  Open System Overview (browser)" -ForegroundColor White
    Write-Host "  [R]  Open Roadmap (browser)" -ForegroundColor White
    Write-Host ""
    Write-Host "  [0]  Exit" -ForegroundColor DarkGray
    Write-Host ""
}

# --- Main loop ---------------------------------------------------------------

Write-Host "  Nascence Control Panel loading..." -ForegroundColor DarkGray

while ($true) {
    Show-Menu
    $choice = Read-Host "  Choice"
    if (-not $choice) { $choice = "" }

    switch ($choice.Trim().ToUpper()) {
        "1" { Full-Start }
        "2" { Show-Header; Start-Servers }
        "3" { Show-Header; Start-REPL }
        "C" { Show-Header; Start-Composer }
        "4" { Show-Header; Stop-Servers }
        "5" { Show-Status; Read-Host "  Press Enter to return" }
        "6" { Show-Header; Show-LatestDream }
        "T" { Show-Header; Show-InnerThoughts }
        "7" { Show-Header; Show-Shadow }
        "8" { Show-Header; Show-RecentLog }
        "9" { Open-SystemReview }
        "H" { Show-Header; Start-HUD -OpenBrowser; Start-Sleep -Seconds 1 }
        "R" { Open-Roadmap }
        "0" { Write-Host ""; Write-Host "  Goodbye." -ForegroundColor DarkGray; break }
        default { Write-Host "  Unknown option." -ForegroundColor Red; Start-Sleep -Seconds 1 }
    }

    if ($choice -eq "0") { break }
}
