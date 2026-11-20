# scripts/dream_exp_a_watchdog_launcher.ps1 (J-1267, F-1775)
# The actual process WMI launches to start scripts/dream_exp_a_relaunch_watchdog.py detached. Runs
# INSIDE the launched powershell.exe itself -- see dream_exp_a_target_launcher.ps1's own header for why
# a powershell.exe wrapper is used instead of cmd.exe (verified directly, J-1267: a WMI-launched cmd.exe
# could not spawn a working python.exe child in this environment; a WMI-launched powershell.exe could).
param(
    [Parameter(Mandatory=$true)][string]$JobId,
    [Parameter(Mandatory=$true)][string]$Tag,
    [Parameter(Mandatory=$true)][int]$NSeeds,
    [Parameter(Mandatory=$true)][string]$WatchdogScript,
    [Parameter(Mandatory=$true)][string]$ScratchDir,
    [Parameter(Mandatory=$true)][string]$WorkDir,
    [string]$TargetScript = "",
    [int]$PollInterval = 90,
    [int]$PostRelaunchDelay = 8,
    [int]$MaxRetries = 8
)
if ($ScratchDir -and -not (Test-Path $ScratchDir)) { New-Item -ItemType Directory -Force -Path $ScratchDir | Out-Null }
if ($WorkDir -and (Test-Path $WorkDir)) { Set-Location $WorkDir }
$py = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $py) { $py = "python" }
$argList = @($WatchdogScript, "--job-id", $JobId, "--tag", $Tag, "--n-seeds", "$NSeeds",
             "--poll-interval", "$PollInterval", "--post-relaunch-delay", "$PostRelaunchDelay",
             "--max-retries", "$MaxRetries", "--scratch-dir", $ScratchDir)
if ($TargetScript) { $argList += @("--target-script", $TargetScript) }
$log = Join-Path $ScratchDir "dream_exp_a_watchdog_launch_stdout_$($JobId)_$($Tag).log"
& $py @argList *>> $log
