# scripts/dream_exp_a_watchdog_start.ps1 (J-1267, F-1775)
# Issues the WMI Win32_Process.Create call that starts scripts/dream_exp_a_watchdog_launcher.ps1
# DETACHED, same idiom as the already-proven scripts/start_supervisor_detached.ps1 (F-0704) -- so the
# watchdog survives this call's own session ending and a Claude Code app restart. Warns (does not
# refuse) if a watchdog for the SAME job-id/tag already appears to be running -- two watchdogs on two
# DIFFERENT job-id/tag pairs are legitimate.
param(
    [Parameter(Mandatory=$true)][string]$JobId,
    [Parameter(Mandatory=$true)][string]$Tag,
    [Parameter(Mandatory=$true)][int]$NSeeds,
    [string]$TargetScript = "",
    [string]$ScratchDir = "",
    [int]$PollInterval = 90,
    [int]$PostRelaunchDelay = 8,
    [int]$MaxRetries = 8
)
$ROOT = Split-Path $PSScriptRoot -Parent

$existing = Get-CimInstance Win32_Process | Where-Object {
    $_.CommandLine -and $_.CommandLine -like "*dream_exp_a_relaunch_watchdog.py*" `
        -and $_.CommandLine -like "*--job-id $JobId*" -and $_.CommandLine -like "*--tag $Tag*"
}
if ($existing) {
    Write-Host "[watchdog] one already appears to be running for job-id=$JobId tag=$Tag (PID $($existing[0].ProcessId)) -- not starting a second." -ForegroundColor Yellow
    exit 0
}

$ScratchResolved = $ScratchDir
if (-not $ScratchResolved) { $ScratchResolved = "C:\Users\USER\AppData\Local\Temp\claude\C--Nascence\00e97919-3e83-4e8f-8aaa-b0d563d7d361\scratchpad" }
if (-not (Test-Path $ScratchResolved)) { New-Item -ItemType Directory -Force -Path $ScratchResolved | Out-Null }

$launcher = Join-Path $PSScriptRoot "dream_exp_a_watchdog_launcher.ps1"
$watchdogScript = Join-Path $PSScriptRoot "dream_exp_a_relaunch_watchdog.py"

$cmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$launcher`" -JobId $JobId -Tag $Tag -NSeeds $NSeeds -WatchdogScript `"$watchdogScript`" -ScratchDir `"$ScratchResolved`" -WorkDir `"$ROOT`" -PollInterval $PollInterval -PostRelaunchDelay $PostRelaunchDelay -MaxRetries $MaxRetries"
if ($TargetScript) { $cmd += " -TargetScript `"$TargetScript`"" }

$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = $cmd; CurrentDirectory = $ROOT }
if ($r.ReturnValue -ne 0) {
    Write-Host "[watchdog] WMI Win32_Process.Create failed (code $($r.ReturnValue))." -ForegroundColor Red
    exit 1
}
Write-Host "[watchdog] launched via WMI (wrapper PID $($r.ProcessId)), outside any job object." -ForegroundColor Green
