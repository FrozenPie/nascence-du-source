"""
build_exhaustive_script_manifest.py — Parse all 193 script docstrings in scripts/ and insert complete script registry & workflow linkages into System_Overview.html & System_Overview.md.
"""

import os
import ast
import json
import re

scripts_dir = r"C:\Nascence\scripts"
html_path = r"C:\Nascence\docs\System_Overview.html"
md_path = r"C:\Nascence\docs\System_Overview.md"
out_path = r"C:\Nascence\docs\system_overview_index.jsonl"

scripts_info = []

for f in sorted(os.listdir(scripts_dir)):
    if f.endswith('.py') and not f.startswith('__'):
        full_path = os.path.join(scripts_dir, f)
        doc = ''
        try:
            with open(full_path, 'r', encoding='utf-8') as file:
                tree = ast.parse(file.read())
                doc = ast.get_docstring(tree) or ''
        except Exception:
            doc = ''
        
        first_line = doc.strip().split('\n')[0] if doc else 'Operational script'
        first_line = re.sub(r'^Nascence\s*[\-\–\—\·]*\s*', '', first_line)
        first_line = re.sub(r'^scripts/[a-zA-Z0-9_\.]+\s*[\-\–\—\·]*\s*', '', first_line)
        scripts_info.append((f, first_line))

print(f"Parsed {len(scripts_info)} operational script docstrings.")

# Group scripts into operational workflows
workflow_map = {
    "System Boot & Runtime Harness": ["run_nascence.py", "launch_servers.ps1", "start_pulse.py", "run_chronicler_pulse.py", "bootstrap_report.py", "health_check.py"],
    "Smoke, Regression & Isolation Testing": ["smoke_test.py", "_smoketest.py", "liveness_audit.py", "validate_mermaid_topology.py", "_failover_test.py", "_concurrency_test.py", "_verify_budget.py"],
    "Evidentiary Audits & Plan Indexing": ["plan_liveness.py", "plan_index.py", "benchmark_runner.py", "consciousness_program_audit.py", "era8_health_check.py"],
    "Graphify & Topology Suite": ["graphify_enrich.py", "graphify_force_html.py", "graphify_health_check.py", "omni_ghost_indexer.py"],
    "Subconscious, School & Sleep Drivers": ["_fire_t4.py", "math_drill_runner.py", "essay_grading_harness.py", "run_apex_debate.py", "spirit_deliberator.py"],
    "Maintenance, DB Purge & Backfill": ["_clean_test_fragments.py", "activity_memory_backfill.py", "reconnect_3070.py", "update_integrity.py", "lai_backfill.py"]
}

# Build HTML table for all 193 scripts
script_rows = []
for sc, desc in scripts_info:
    found_wf = "Operational / Utility Harness"
    for wf, files in workflow_map.items():
        if sc in files:
            found_wf = wf
            break
    script_rows.append(f"<tr><td><code>{sc}</code></td><td>{found_wf}</td><td>{desc}</td></tr>")

full_script_table = f"""
<div class="lead">Operational Workflows &amp; Tooling</div>
<h2>Complete Operational Script Registry &amp; Workflow Linkages ({len(scripts_info)} Scripts)</h2>
<p>An exhaustive, structured guide documenting all operational, diagnostic, test, and maintenance scripts in <code>scripts/</code> and how they link together into core system workflows:</p>

<div class="cards">
<div class="card">
<b>1. Primary System Boot &amp; Pulse Harness</b>
<p class="small"><code>run_nascence.py</code> boots the interactive engine; <code>launch_servers.ps1</code> initializes the multi-station Ollama ports (:11433–:11442); <code>start_pulse.py</code> drives the Inner Monologue idle economy.</p>
</div>

<div class="card">
<b>2. Headless Regression &amp; Isolation Purge</b>
<p class="small"><code>smoke_test.py</code> executes the full 16-node cycle and runs mandatory isolation purge (Invariant #8); <code>liveness_audit.py</code> and <code>validate_mermaid_topology.py</code> verify 100% component liveness.</p>
</div>

<div class="card">
<b>3. Plan Liveness &amp; Telemetry Audits</b>
<p class="small"><code>plan_liveness.py</code> audits 202 evidence references across 52 active plans against live telemetry stores; <code>plan_index.py</code> indexes all plan specifications.</p>
</div>

<div class="card">
<b>4. Graphify Topology &amp; Health Pipeline</b>
<p class="small"><code>graphify_enrich.py</code> recovers call/import edges; <code>graphify_force_html.py</code> renders D3 visual graphs; <code>graphify_health_check.py</code> scans for dead code.</p>
</div>
</div>

<table>
<tr><th>Script Name</th><th>Workflow Category</th><th>Operational Purpose &amp; Description</th></tr>
{"".join(script_rows)}
</table>
"""

# Read existing HTML
with open(html_path, 'r', encoding='utf-8') as f:
    html_text = f.read()

# Replace or insert Script Registry before File Manifest
if "Complete Operational Script Registry &amp; Workflow Linkages" in html_text or "Complete Operational Script Registry" in html_text:
    html_text = re.sub(r'<div class="lead">Operational Workflows &amp; Tooling</div>.*?</table>', full_script_table, html_text, flags=re.DOTALL)
else:
    html_text = html_text.replace('<div class="lead">What\'s where</div>', full_script_table + '\n<div class="lead">What\'s where</div>')

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html_text)

print(f"Updated System_Overview.html with Exhaustive {len(scripts_info)}-Script Registry.")

# Sync System_Overview.md
import sync_overview_md
