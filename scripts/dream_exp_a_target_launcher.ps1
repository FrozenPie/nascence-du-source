# scripts/dream_exp_a_target_launcher.ps1 (J-1267, F-1775)
# The actual process WMI launches for a dream_experiment_a.py relaunch. Runs INSIDE the launched
# powershell.exe itself (no cmd.exe involved) -- sets FOR_DISABLE_CONSOLE_CTRL_HANDLER=1 on ITS OWN
# process environment (inherited by the python child it starts), then runs python via PowerShell's own
# "&" call operator with output redirected via "*>>" (PowerShell's own redirect-all-streams operator --
# no shell redirection needed, so no cmd.exe involved at any point).
#
# WHY powershell.exe and not cmd.exe as the WMI-launched wrapper (verified directly, J-1267, 2026-09-23):
# in this session's own sandboxed tool environment, a WMI-launched cmd.exe process could NOT itself
# spawn a working python.exe child -- WMI Win32_Process.Create reported success (ReturnValue=0, a real
# PID) but the python child never appeared in the process list and never produced any output, not even a
# single flushed line written immediately at start. A WMI-launched powershell.exe process, by contrast,
# spawns a python.exe child successfully every time this was tested (repeated, with named parameters
# correctly bound and an environment variable correctly inherited by the child). This may be specific to
# this execution environment rather than the founder's own interactive desktop (where the cmd.exe
# pattern is what every prior manual relaunch in this job chain, and scripts/start_supervisor_detached.ps1,
# have used successfully) -- but a powershell.exe wrapper is a strict superset of what a cmd.exe wrapper
# needs and has no reason to behave worse anywhere cmd.exe currently works, so it is used unconditionally
# here rather than branching on environment.
param(
    [Parameter(Mandatory=$true)][string]$TargetScript,
    [Parameter(Mandatory=$true)][int]$NSeeds,
    [Parameter(Mandatory=$true)][string]$Tag,
    [Parameter(Mandatory=$true)][string]$JobId,
    [Parameter(Mandatory=$true)][string]$RunLog,
    [Parameter(Mandatory=$true)][string]$WorkDir,
    [string]$ExtraArgs = ""
)
$env:FOR_DISABLE_CONSOLE_CTRL_HANDLER = "1"
$runLogDir = Split-Path $RunLog -Parent
if ($runLogDir -and -not (Test-Path $runLogDir)) { New-Item -ItemType Directory -Force -Path $runLogDir | Out-Null }
if ($WorkDir -and (Test-Path $WorkDir)) { Set-Location $WorkDir }
$py = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $py) { $py = "python" }
$argList = @($TargetScript, "--n-seeds", "$NSeeds", "--tag", $Tag, "--job-id", $JobId, "--save-scenes", "--resume")
if ($ExtraArgs) { $argList += ($ExtraArgs -split '\s+' | Where-Object { $_ }) }
& $py @argList *>> $RunLog
