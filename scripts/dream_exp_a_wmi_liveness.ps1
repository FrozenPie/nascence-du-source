# scripts/dream_exp_a_wmi_liveness.ps1 (J-1267, F-1775)
# Checks whether a process is alive whose CommandLine contains $Match (a script basename, e.g.
# "dream_experiment_a.py"). Same Get-CimInstance Win32_Process check every manual relaunch in this job
# chain has used since F-1535, wrapped as a reusable, parameterized file (not a hand-built -Command
# string) so scripts/dream_exp_a_relaunch_watchdog.py never has to quote a search string into a shell
# command itself from Python -- this project's own memory flags shell-quoting as a recurring real
# failure mode (feedback_bash_backtick_command_substitution.md), so this script minimizes cross-language
# string-building to a single -like wildcard match on a cleanly bound parameter.
# -Exclude (comma-separated substrings) drops false-positive matches -- caught by J-1267's own real
# end-to-end test: the watchdog's OWN command line carries "--target-script <path>" as one of ITS
# arguments, so a bare -Match against the target script's name matched the watchdog process itself
# (and its own watchdog_launcher.ps1 wrapper), meaning the watchdog would see its supervised target as
# "alive" forever and never detect a real crash. dream_exp_a_relaunch_watchdog.py always passes its own
# two process-name markers here so it can never mistake itself for its target.
param(
    [Parameter(Mandatory=$true)][string]$Match,
    [string]$Exclude = ""
)
$p = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and ($_.CommandLine -like "*$Match*") }
if ($Exclude) {
    foreach ($term in ($Exclude -split ',')) {
        $t = $term.Trim()
        if ($t) { $p = $p | Where-Object { $_.CommandLine -notlike "*$t*" } }
    }
}
if ($p) {
    $first = $p | Select-Object -First 1
    Write-Output "ALIVE $($first.ProcessId)"
} else {
    Write-Output "DEAD"
}
