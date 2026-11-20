# scripts/start_supervisor_launcher.ps1  (J-1341, F-1821/F-1893/F-1894, D-0277)
# The actual process WMI launches to start scripts/supervisor.py detached. Runs INSIDE the launched
# powershell.exe itself (no cmd.exe involved) -- start_supervisor_detached.ps1's own powershell.exe-
# wrapper replacement for its former WMI->cmd.exe->python.exe launch line. That exact shape was
# confirmed (F-1821, from an automated job-run session; F-1893, reproduced from a genuinely interactive
# one, 2/2 both times) to sometimes report WMI success (ReturnValue=0, a real PID) while the wrapped
# python.exe child silently never started -- no process, no output, ever. See
# scripts/dream_exp_a_target_launcher.ps1's own header for the same root finding on a different script,
# and start_supervisor_detached.ps1's own header for the fuller incident history.
#
# Uses System.Diagnostics.Process directly with async output-event handlers, NOT PowerShell's own "&"
# call-operator + 1>>/2>> redirection. Verified while building this fix (J-1341, F-1894): PowerShell's
# native-command stderr redirection wraps every stderr line from a real child process as a formatted
# ErrorRecord ("python.exe : <text>" plus CategoryInfo/FullyQualifiedErrorId boilerplate) instead of
# passing it through raw the way cmd.exe's own "2>>" always did -- a real, silent format change to
# data\supervisor.err.log that the simpler "&"-based wrapper would have introduced. A naive synchronous
# StandardOutput/StandardError.ReadToEnd() is also a known .NET deadlock risk for a long-running process
# that writes to both streams (one pipe's OS buffer can fill while the code is blocked reading the
# other). BeginOutputReadLine/BeginErrorReadLine avoids both problems and preserves true append-mode on
# two SEPARATE files, matching the prior cmd.exe version's own >> $log 2>> $err behavior exactly.
param(
    [Parameter(Mandatory=$true)][string]$Py,
    [Parameter(Mandatory=$true)][string]$Root,
    [Parameter(Mandatory=$true)][string]$ScriptPath,
    [Parameter(Mandatory=$true)][string]$Log,
    [Parameter(Mandatory=$true)][string]$Err
)
if ($Root -and (Test-Path $Root)) { Set-Location $Root }

$logStream = New-Object System.IO.StreamWriter($Log, $true)
$logStream.AutoFlush = $true
$errStream = New-Object System.IO.StreamWriter($Err, $true)
$errStream.AutoFlush = $true

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $Py
$psi.Arguments = $ScriptPath
$psi.WorkingDirectory = $Root
$psi.UseShellExecute = $false
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.CreateNoWindow = $true

$proc = New-Object System.Diagnostics.Process
$proc.StartInfo = $psi

$writeLine = {
    if ($null -ne $EventArgs.Data) { $Event.MessageData.WriteLine($EventArgs.Data) }
}
$outSub = Register-ObjectEvent -InputObject $proc -EventName OutputDataReceived -Action $writeLine -MessageData $logStream
$errSub = Register-ObjectEvent -InputObject $proc -EventName ErrorDataReceived -Action $writeLine -MessageData $errStream

try {
    $proc.Start() | Out-Null
} catch {
    $errStream.WriteLine("[start_supervisor_launcher] failed to start '$Py $ScriptPath': $_")
    $errStream.Close(); $logStream.Close()
    Unregister-Event -SourceIdentifier $outSub.Name -ErrorAction SilentlyContinue
    Unregister-Event -SourceIdentifier $errSub.Name -ErrorAction SilentlyContinue
    exit 1
}
$proc.BeginOutputReadLine()
$proc.BeginErrorReadLine()
$proc.WaitForExit()

Unregister-Event -SourceIdentifier $outSub.Name -ErrorAction SilentlyContinue
Unregister-Event -SourceIdentifier $errSub.Name -ErrorAction SilentlyContinue
$logStream.Close()
$errStream.Close()
exit $proc.ExitCode
