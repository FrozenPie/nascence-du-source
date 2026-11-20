# scripts/dream_exp_a_wmi_relaunch.ps1 (J-1267, F-1775)
# Issues the WMI Win32_Process.Create call that starts scripts/dream_exp_a_target_launcher.ps1 DETACHED
# (a child of WmiPrvSE, in no caller job -- survives this call's own session ending and a Claude Code
# app restart, the same escape F-0704 documents for Du's own servers, generalized to a lab script by
# F-1535). This script itself runs as an ordinary short-lived child of whatever calls it (the watchdog's
# own subprocess.run) -- only the launched target_launcher.ps1 (and the python.exe it starts) needs to
# be, and is, detached. See dream_exp_a_target_launcher.ps1's own header for why the launched process is
# a powershell.exe wrapper and not a cmd.exe one.
param(
    [Parameter(Mandatory=$true)][string]$TargetScript,
    [Parameter(Mandatory=$true)][int]$NSeeds,
    [Parameter(Mandatory=$true)][string]$Tag,
    [Parameter(Mandatory=$true)][string]$JobId,
    [Parameter(Mandatory=$true)][string]$RunLog,
    [Parameter(Mandatory=$true)][string]$WorkDir,
    [string]$ExtraArgs = ""
)
$launcher = Join-Path $PSScriptRoot "dream_exp_a_target_launcher.ps1"
$runLogDir = Split-Path $RunLog -Parent
if ($runLogDir -and -not (Test-Path $runLogDir)) { New-Item -ItemType Directory -Force -Path $runLogDir | Out-Null }
$cmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$launcher`" -TargetScript `"$TargetScript`" -NSeeds $NSeeds -Tag $Tag -JobId $JobId -RunLog `"$RunLog`" -WorkDir `"$WorkDir`" -ExtraArgs `"$ExtraArgs`""
$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = $cmd; CurrentDirectory = $WorkDir }
if ($r.ReturnValue -ne 0) {
    Write-Output "WMI_CREATE_FAILED $($r.ReturnValue)"
    exit 1
}
Write-Output "WMI_CREATE_OK $($r.ProcessId)"
