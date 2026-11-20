# start_supervisor_detached.ps1  (Nascence - 2026-09-03)
# Start scripts/supervisor.py OUTSIDE any Windows Job object, so it (and the hubs it launches) survive
# the launcher's own death.
#
# WHY (2026-09-03, F-0704): the Claude Code desktop app runs its PowerShell tool inside a Windows Job
# object with breakaway DISABLED. Anything started from that tool - even with DETACHED_PROCESS, even
# a grandchild whose parent already exited - stays in the job, and the whole job is killed when the
# Claude app restarts (e.g. its own auto-update at 09:18:08 on 2026-09-03, which took down Judge1
# :11439, Judge2 :11440, Dreamer :11442 AND the supervisor watchdog that D-0127 had made responsible
# for healing them, all launched from a Claude session on 2026-09-02). Du kept running (started from
# the Control Panel, a standalone window) and fail-opened on the dark tier for the rest of the morning.
#
# A process created through WMI's Win32_Process.Create is a child of WmiPrvSE, in no caller job, so it
# outlives whatever launched it. The Control Panel's own Start-Supervisor is fine as-is (the panel is
# not inside a job); this script exists for launches from a Claude Code session or any other job-
# confined shell. Idempotent: if a supervisor.py is already running it does nothing.
#
# Since D-0127 the supervisor ensures + watches ALL FOUR local servers (hot_ollama :11433, judge1_hub
# :11439, judge2_hub :11440, dreamer_hub :11442), so this one command is the full local bring-up.
param()

$ROOT = Split-Path $PSScriptRoot -Parent
if ($ROOT -match ' ') { Write-Host "[NASCENCE] refusing: repo path contains a space, the cmd redirect below is unquoted."; exit 1 }

$existing = Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
            Where-Object { $_.CommandLine -match 'supervisor\.py' }
if ($existing) {
    Write-Host "[NASCENCE] supervisor already running (PID $($existing.ProcessId)) - nothing to do." -ForegroundColor Green
    exit 0
}

$py  = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $py) { $py = "C:\Python314\python.exe" }
$log = Join-Path $ROOT "data\supervisor.log"
$err = Join-Path $ROOT "data\supervisor.err.log"
# FIXED (2026-09-24, J-1341/D-0277 -- supersedes the doc-only CAVEAT J-1295/F-1821 left here): this used
# to launch via a WMI + cmd.exe wrapper ("cmd.exe /c $py scripts\supervisor.py >> $log 2>> $err"), which
# F-1821 (an automated job-run session) and F-1893 (reproduced from a genuinely interactive session, 2/2
# both times) confirmed can report WMI success (ReturnValue=0, a real PID) while the wrapped python.exe
# child silently never starts -- no process, no output, ever. D-0277 (travis) ruled: build and verify a
# powershell.exe-wrapper replacement, mirroring scripts/dream_exp_a_target_launcher.ps1's own
# already-verified pattern, tested only against a disposable target script until proven reliable -- see
# that job's own finding for the full build+verify record. Now launches
# scripts/start_supervisor_launcher.ps1 (a powershell.exe process, no cmd.exe involved) via this same WMI
# Win32_Process.Create call; see that script's own header for why it uses System.Diagnostics.Process
# directly rather than PowerShell's own "&" + 1>>/2>> redirection (a real stderr-formatting difference
# from cmd.exe was found and fixed while verifying this fix). Verified end-to-end, 2/2 runs, isolated in
# scratchpad against a disposable target script, never the real supervisor.py: reliable child start,
# separate append-mode stdout/stderr files preserved, raw text preserved (no PowerShell ErrorRecord
# wrapping), no stray processes left behind either run. Full evidence: F-1894. If this script ever
# appears to succeed (ReturnValue=0) but supervisor.py never actually comes up (check
# `netstat -ano | findstr 1143` and data\supervisor.log), this silent-failure mode is no longer the first
# thing to suspect -- check F-1894 before assuming a regression of it.
$launcher = Join-Path $PSScriptRoot "start_supervisor_launcher.ps1"
$cmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$launcher`" -Py `"$py`" -Root `"$ROOT`" -ScriptPath `"scripts\supervisor.py`" -Log `"$log`" -Err `"$err`""

$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create `
        -Arguments @{ CommandLine = $cmd; CurrentDirectory = $ROOT }
if ($r.ReturnValue -ne 0) {
    Write-Host "[NASCENCE] WMI Win32_Process.Create failed (code $($r.ReturnValue))." -ForegroundColor Red
    exit 1
}
Write-Host "[NASCENCE] supervisor launched via WMI (wrapper PID $($r.ProcessId)), outside any job object." -ForegroundColor Green
Write-Host "[NASCENCE] it will adopt/launch hot_ollama :11433 + judge1 :11439 + judge2 :11440 + dreamer :11442 and watch them every 15s." -ForegroundColor Cyan
Write-Host "[NASCENCE] log: $log" -ForegroundColor DarkGray
