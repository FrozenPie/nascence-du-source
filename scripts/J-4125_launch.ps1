# J-4125 lab launcher: runs gen + grade as separate detached python processes, logs to data/lab/ground_contract_lab/
param([string]$Which)
$lab = "C:\Nascence\data\lab\ground_contract_lab"
$script = if ($Which -eq "gen") { "C:\Nascence\docs\lab\J-4125_gen.py" } else { "C:\Nascence\docs\lab\J-4125_grade.py" }
$out = "$lab\J-4125_$Which.out"
& python -u $script *>> $out
if ($Which -eq "gen") { New-Item -ItemType File -Force "$lab\J-4125_gen.finished" | Out-Null }
