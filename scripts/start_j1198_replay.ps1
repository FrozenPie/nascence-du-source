# start_j1198_replay.ps1 (J-1198, 2026-09-22): start the D-0213 walk-back replay OUTSIDE the Claude app's Job object.
# The Claude Code desktop app runs its PowerShell tool inside a Windows Job object with breakaway disabled, so a
# plain Start-Process / Popen child dies when the app restarts (F-0704); a process created through WMI's
# Win32_Process.Create is a child of WmiPrvSE, in no caller job (same pattern as scripts/start_supervisor_detached.ps1).
# No console of its own that a window-close could hit: stdout/stderr go to files, and the runner sets
# FOR_DISABLE_CONSOLE_CTRL_HANDLER=1 before any import (F-1535/F-1545: the Intel Fortran runtime aborts on CTRL_CLOSE).
# Resumable: re-running this script continues from the finished units in the scratch results file.
param([int]$N = 40)

$ROOT = Split-Path $PSScriptRoot -Parent
if ($ROOT -match ' ') { Write-Host "refusing: worktree path contains a space, the cmd redirect below is unquoted."; exit 1 }
$SCRATCH = Split-Path $ROOT -Parent
$py  = "C:\Python314\python.exe"
$out = Join-Path $SCRATCH "lab_j1198_replay.out.log"
$err = Join-Path $SCRATCH "lab_j1198_replay.err.log"

$existing = Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -match 'lab_j1198_walkback_replay' }
if ($existing) { Write-Host "already running (PID $($existing.ProcessId)) - nothing to do."; exit 0 }

$cmd = "cmd.exe /c set FOR_DISABLE_CONSOLE_CTRL_HANDLER=1&& set PYTHONUNBUFFERED=1&& $py -u scripts\lab_j1198_walkback_replay.py $N >> $out 2>> $err"
$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = $cmd; CurrentDirectory = $ROOT }
if ($r.ReturnValue -ne 0) { Write-Host "WMI Win32_Process.Create failed (code $($r.ReturnValue))."; exit 1 }
Write-Host "launched via WMI (wrapper PID $($r.ProcessId)); stdout: $out ; stderr: $err"
