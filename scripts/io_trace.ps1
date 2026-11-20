# io_trace.ps1 — standing disk-I/O tracer (2026-08-28, built to catch Du's spike bursts live).
#
# WHY: Du's I/O spikes are short (~4s) and bursty — by the time anyone opens a monitor they're gone.
# The 08-23 FreshStart investigation caught run_nascence.py at 167 MB/s and the HUD at ~45 MB/s
# sustained, but the run_nascence burst source was never traced to a line. This tracer keeps a
# timestamped record so a spike at HH:MM:SS can be cross-referenced against Du's own logs
# (session_events.jsonl, llm telemetry, moments.jsonl mtimes, nascence.log) after the fact.
#
# WHAT IT LOGS (CSV, one file per day, data\io_trace\io_trace_YYYYMMDD.csv):
#   ts, kind, disk_pct, disk_mbs, queue, pid, proc, read_mbs, write_mbs
#   - kind=proc  : any python*/ollama* process moving >1 MB/s (read+write) that second
#   - kind=disk  : the C: physical-disk line whenever disk_pct>5 or disk_mbs>5
#   - kind=beat  : one heartbeat row per 60s so "tracer was alive but saw nothing" is provable
#   - kind=pid   : first sighting of each python*/ollama* PID with its command line (the PID map —
#                  written to the same CSV so one file carries everything)
#
# STOP: create the file data\io_trace\STOP (checked every second), or kill the powershell PID
#       (recorded in data\io_trace\tracer.pid). Survives this Claude session; dies on reboot —
#       re-run manually or wire into a scheduled task if it earns permanence.

$ErrorActionPreference = "Continue"
$traceDir = "C:\Nascence\data\io_trace"
if (-not (Test-Path $traceDir)) { New-Item -ItemType Directory -Path $traceDir | Out-Null }
$stopFile = Join-Path $traceDir "STOP"
Set-Content -Path (Join-Path $traceDir "tracer.pid") -Value $PID -Encoding utf8

$seenPids = @{}
$lastBeat = Get-Date

function Trace-Line([string]$line) {
    $f = Join-Path $traceDir ("io_trace_{0}.csv" -f (Get-Date -Format "yyyyMMdd"))
    if (-not (Test-Path $f)) {
        Add-Content -Path $f -Value "ts,kind,disk_pct,disk_mbs,queue,pid,proc,read_mbs,write_mbs" -Encoding utf8
    }
    Add-Content -Path $f -Value $line -Encoding utf8
}

while ($true) {
    if (Test-Path $stopFile) {
        Trace-Line ("{0},stop,,,,,,," -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"))
        Remove-Item $stopFile -Force
        break
    }
    try {
        $c = Get-Counter '\PhysicalDisk(0 c:)\% Disk Time', '\PhysicalDisk(0 c:)\Disk Bytes/sec',
                         '\PhysicalDisk(0 c:)\Avg. Disk Queue Length',
                         '\Process(python*)\ID Process', '\Process(python*)\IO Read Bytes/sec',
                         '\Process(python*)\IO Write Bytes/sec',
                         '\Process(ollama*)\ID Process', '\Process(ollama*)\IO Read Bytes/sec',
                         '\Process(ollama*)\IO Write Bytes/sec' `
                         -SampleInterval 1 -MaxSamples 1 -ErrorAction SilentlyContinue
    } catch { Start-Sleep -Seconds 1; continue }
    if (-not $c) { Start-Sleep -Seconds 1; continue }

    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $diskPct = 0.0; $diskMBs = 0.0; $queue = 0.0
    $byInst = @{}
    foreach ($s in $c.CounterSamples) {
        if ($s.Path -match 'physicaldisk') {
            if     ($s.Path -match 'disk time') { $diskPct = $s.CookedValue }
            elseif ($s.Path -match 'bytes')     { $diskMBs = $s.CookedValue / 1MB }
            elseif ($s.Path -match 'queue')     { $queue   = $s.CookedValue }
        } else {
            if (-not $byInst[$s.InstanceName]) { $byInst[$s.InstanceName] = @{ pid = 0; r = 0.0; w = 0.0 } }
            if     ($s.Path -match 'id process') { $byInst[$s.InstanceName].pid = [int]$s.CookedValue }
            elseif ($s.Path -match 'read')       { $byInst[$s.InstanceName].r   = $s.CookedValue }
            elseif ($s.Path -match 'write')      { $byInst[$s.InstanceName].w   = $s.CookedValue }
        }
    }

    foreach ($k in $byInst.Keys) {
        $v = $byInst[$k]
        if ($v.pid -gt 0 -and -not $seenPids[$v.pid]) {
            $seenPids[$v.pid] = $true
            $cmd = ""
            try {
                $p = Get-CimInstance Win32_Process -Filter "ProcessId = $($v.pid)" -ErrorAction Stop
                if ($p -and $p.CommandLine) { $cmd = ($p.CommandLine -replace '[,\r\n"]', ' ') }
                if ($cmd.Length -gt 160) { $cmd = $cmd.Substring(0, 160) }
            } catch {}
            Trace-Line ("{0},pid,,,,{1},{2},," -f $ts, $v.pid, $cmd)
        }
        if (($v.r + $v.w) -gt 1MB) {
            Trace-Line ("{0},proc,{1:N1},{2:N1},{3:N2},{4},{5},{6:N1},{7:N1}" -f `
                $ts, $diskPct, $diskMBs, $queue, $v.pid, $k, ($v.r/1MB), ($v.w/1MB))
        }
    }

    if ($diskPct -gt 5 -or $diskMBs -gt 5) {
        Trace-Line ("{0},disk,{1:N1},{2:N1},{3:N2},,,," -f $ts, $diskPct, $diskMBs, $queue)
    }

    if (((Get-Date) - $lastBeat).TotalSeconds -ge 60) {
        $lastBeat = Get-Date
        Trace-Line ("{0},beat,{1:N1},{2:N1},{3:N2},,,," -f $ts, $diskPct, $diskMBs, $queue)
    }
}
