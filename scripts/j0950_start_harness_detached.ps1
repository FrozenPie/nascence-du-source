# j0950_start_harness_detached.ps1  (Nascence - 2026-09-22, J-0950 Thread 2a)
# Start the MEASURED phase of scripts/j0950_loop_contention_harness.py outside any Windows Job object (WMI
# Win32_Process.Create, a child of WmiPrvSE), so a ~35 minute run survives the launching Claude app restarting
# (F-0704; same pattern as scripts/start_supervisor_detached.ps1).  Run it ONLY when the machine is quiet
# (the harness also refuses to start when system CPU over 10 s is above --max-cpu, 60% by default, unless -Force).
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts\j0950_start_harness_detached.ps1 -Out C:\path\to\j0950_harness_results.jsonl
#   add -DryRun to print the command line without starting anything; -Extra '--pairs 8 --block-s 120' to change the plan.
#
# It writes only <Out> (the results JSONL, one row per finished block, resumable) and <Out>.log; never anything under
# C:\Nascence\data or C:\Nascence\docs.  Poll with:  Get-Content <Out>.log -Tail 20
param(
    [Parameter(Mandatory = $true)][string]$Out,
    [string]$Extra = "",
    [switch]$Force,
    [switch]$DryRun
)

$ROOT = Split-Path $PSScriptRoot -Parent
$existing = Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
            Where-Object { $_.CommandLine -match 'j0950_loop_contention_harness\.py\s+measure' }
if ($existing) {
    Write-Host "[J-0950] a measured-phase harness is already running (PID $($existing.ProcessId)) - nothing to do." -ForegroundColor Yellow
    exit 0
}
if ($Out -match '(?i)^c:\\nascence\\(data|docs)\\') {
    Write-Host "[J-0950] refusing: -Out must not be under C:\Nascence\data or docs." -ForegroundColor Red
    exit 1
}

$py = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $py) { $py = "C:\Python314\python.exe" }
$log  = "$Out.log"
$args = "measure --out `"$Out`" --wait-kind http --pairs 6 --block-s 150 --seed 950 --resume"
if ($Force) { $args += " --force" }
if ($Extra) { $args += " $Extra" }
# the whole command is wrapped in one more pair of quotes: cmd /c strips the first and last quote of a string that starts
# with one, which would otherwise break a line holding several quoted paths
$inner = "`"$py`" scripts\j0950_loop_contention_harness.py $args >> `"$log`" 2>&1"
$cmd = "cmd.exe /c `"$inner`""

if ($DryRun) {
    Write-Host "[J-0950] DRY RUN. CurrentDirectory=$ROOT"
    Write-Host "[J-0950] $cmd"
    exit 0
}
$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = $cmd; CurrentDirectory = $ROOT }
if ($r.ReturnValue -ne 0) {
    Write-Host "[J-0950] WMI Win32_Process.Create failed (code $($r.ReturnValue))." -ForegroundColor Red
    exit 1
}
Write-Host "[J-0950] harness launched via WMI (wrapper PID $($r.ProcessId)), outside any job object." -ForegroundColor Green
Write-Host "[J-0950] results: $Out   log: $log   (about 32-35 minutes; resumable with the same command)" -ForegroundColor Cyan
