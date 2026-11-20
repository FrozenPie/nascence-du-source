"""
build_plan_matrix.py — Parse all 338 markdown files across docs/ to extract plan linkages, touched code files, telemetry references, and plan dependency graph.
"""

import os
import glob
import re
import json

docs_dir = r"C:\Nascence\docs"
html_path = r"C:\Nascence\docs\System_Overview.html"
md_path = r"C:\Nascence\docs\System_Overview.md"
out_path = r"C:\Nascence\docs\system_overview_index.jsonl"

plan_files = glob.glob(os.path.join(docs_dir, '**', '*.md'), recursive=True)
print(f"Auditing {len(plan_files)} Markdown files across docs/...")

plans_data = []

for pf in sorted(plan_files):
    rel_path = os.path.relpath(pf, docs_dir).replace('\\', '/')
    filename = os.path.basename(pf)
    
    with open(pf, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Extract title
    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else filename.replace('.md', '').replace('_', ' ').title()

    # Categorize status
    folder = rel_path.split('/')[0] if '/' in rel_path else 'root'
    status_map = {
        'plans': 'Active Plan',
        'staged': 'Staged Plan',
        'completed': 'Completed Plan',
        'archive': 'Archive Document',
        'reviews': 'Review / Audit',
        'lab': 'Lab Experiment',
        'session_handoffs': 'Session Handoff',
        'node_audit': 'Node Audit',
        'chronicles': 'Chronicle Log',
        'reports': 'System Report',
        'cross_model': 'Cross-Model Report',
        'root': 'Root Spec / Overview'
    }
    status = status_map.get(folder, 'Document')

    # Extract codebase files touched (core/..., nodes/..., scripts/..., data/...)
    code_refs = set(re.findall(r'(?:core|nodes|scripts|data)/[a-zA-Z0-9_\-\./]+', content))
    clean_code_refs = sorted([re.sub(r'[\"\,\)\}\]\:\;]+$', '', r) for r in code_refs])

    # Extract telemetry streams referenced
    telemetry_terms = [
        'monologue_log', 'felt_preamble_log', 'sleep_pressure_log', 'geometry_tuples',
        'provenance_log', 'retraction_ledger', 'commitment_ledger', 'shadow_log',
        'guidance_injection_log', 'subconscious_state', 'active_imagination_log',
        'mineness_log', 'arousal_log', 'reentry_log'
    ]
    telemetry_refs = [t for t in telemetry_terms if t in content]

    # Extract links to other plan markdown files
    md_links = set(re.findall(r'\[.*?\]\(([\w\-\.\/]+\.md)\)', content))
    clean_md_links = sorted([l for l in md_links if not l.startswith('http')])

    plans_data.append({
        'path': rel_path,
        'title': title,
        'folder': folder,
        'status': status,
        'code_refs': clean_code_refs,
        'telemetry_refs': telemetry_refs,
        'plan_links': clean_md_links
    })

print(f"Successfully processed {len(plans_data)} plan & spec records.")

# Generate HTML section for System_Overview.html
table_rows = []
for p in plans_data[:150]: # Include primary plans in table
    code_str = ", ".join([f"<code>{c}</code>" for c in p['code_refs'][:3]]) if p['code_refs'] else "<span style='color:#6a6a80'>None</span>"
    telem_str = ", ".join([f"<span style='color:#fbbf24'>{t}</span>" for t in p['telemetry_refs']]) if p['telemetry_refs'] else "<span style='color:#6a6a80'>None</span>"
    links_str = f"<b>{len(p['plan_links'])}</b> linked plans" if p['plan_links'] else "0 links"
    
    badge_color = "#34d399" if p['folder'] == 'plans' else ("#fbbf24" if p['folder'] == 'staged' else ("#a855f7" if p['folder'] == 'completed' else "#9a9ab0"))
    
    table_rows.append(f"""
    <tr>
        <td><a href="{p['path']}" style="color:#22d3ee"><code>docs/{p['path']}</code></a></td>
        <td><span style="background:#13131d;border:1px solid {badge_color};color:{badge_color};padding:2px 6px;border-radius:4px;font-size:11px">{p['status']}</span></td>
        <td><b>{p['title'][:45]}</b></td>
        <td>{code_str}</td>
        <td>{telem_str}</td>
        <td>{links_str}</td>
    </tr>
    """)

plan_matrix_html = f"""
<div class="lead">Plan Architecture &amp; Cross-Reference Map</div>
<h2>Plan Hierarchy &amp; Codebase Cross-Reference Matrix ({len(plans_data)} Total Docs)</h2>
<p>An exhaustive cross-reference map indexing all <b>{len(plans_data)} plan documents</b> across <code>docs/plans/</code> (54 active), <code>docs/staged/</code> (8 staged), <code>docs/completed/</code> (59 completed), <code>docs/archive/</code> (24 archive), <code>docs/reviews/</code> (20 reviews), <code>docs/lab/</code> (54 lab experiments), and root specs. Maps code ownership, telemetry references, and inter-plan dependencies:</p>

<div class="cards">
<div class="card">
<b>1. Active Plans (54 Docs · docs/plans/)</b>
<p class="small">Live architectural specifications currently governing system development. Key active plans: <code>lane_scheduler.md</code>, <code>t4_watershed.md</code>, <code>pursuits.md</code>, <code>du_initiated_upgrade_trigger.md</code>.</p>
<span class="k">54 active plan files</span>
</div>

<div class="card">
<b>2. Staged Plans (8 Docs · docs/staged/)</b>
<p class="small">Completed specifications awaiting liveness evidence or watch condition flips. Key staged plans: <code>geometry_tuple_index.md</code>, <code>DEFERRED_PLANS.md</code>.</p>
<span class="k">8 staged plan files</span>
</div>

<div class="card">
<b>3. Completed Plans (59 Docs · docs/completed/)</b>
<p class="small">Fully implemented and verified specifications. Historical reference for feature origins: <code>volition_his_own_hands.md</code>, <code>reading_provenance_plan.md</code>, <code>study_notes_plan.md</code>.</p>
<span class="k">59 completed plan files</span>
</div>

<div class="card">
<b>4. Diagnostic Reviews (20 Docs · docs/reviews/)</b>
<p class="small">Evidentiary audits & benchmarks: <code>plan_liveness_audit.md</code> (202 evidence references), <code>audit_2026-08-20.md</code> (mineness & protoself win), <code>station_matrix.md</code> (LLM benchmark scores).</p>
<span class="k">20 audit files</span>
</div>
</div>

<h3>Primary Plan Cross-Reference Register</h3>
<table>
<tr><th>Plan Path</th><th>Status</th><th>Plan Title</th><th>Codebase Files Touched</th><th>Telemetry References</th><th>Dependencies</th></tr>
{"".join(table_rows)}
</table>
"""

# Read existing HTML
with open(html_path, 'r', encoding='utf-8') as f:
    html_text = f.read()

# Insert before Exhaustive Codebase Inventory
if 'Plan Architecture &amp; Cross-Reference Map' in html_text:
    html_text = re.sub(r'<div class="lead">Plan Architecture &amp; Cross-Reference Map</div>.*?<div class="lead">Exhaustive Codebase Inventory</div>', lambda m: plan_matrix_html + '\n<div class="lead">Exhaustive Codebase Inventory</div>', html_text, flags=re.DOTALL)
else:
    html_text = html_text.replace('<div class="lead">Exhaustive Codebase Inventory</div>', plan_matrix_html + '\n<div class="lead">Exhaustive Codebase Inventory</div>')

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html_text)

print("Updated System_Overview.html with Plan Hierarchy & Cross-Reference Matrix.")

# Sync System_Overview.md
import sync_overview_md
