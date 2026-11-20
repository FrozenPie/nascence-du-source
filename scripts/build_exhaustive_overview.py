"""
build_exhaustive_overview.py — Parse all 200 core/ Python docstrings and insert exhaustive engine inventory into System_Overview.html & System_Overview.md.
"""

import os
import ast
import json
import re

core_dir = r"C:\Nascence\core"
html_path = r"C:\Nascence\docs\System_Overview.html"
md_path = r"C:\Nascence\docs\System_Overview.md"
out_path = r"C:\Nascence\docs\system_overview_index.jsonl"

modules_info = []

for f in sorted(os.listdir(core_dir)):
    if f.endswith('.py') and not f.startswith('__'):
        full_path = os.path.join(core_dir, f)
        doc = ''
        try:
            with open(full_path, 'r', encoding='utf-8') as file:
                tree = ast.parse(file.read())
                doc = ast.get_docstring(tree) or ''
        except Exception:
            doc = ''
        
        first_line = doc.strip().split('\n')[0] if doc else 'Core engine module'
        # Clean title
        first_line = re.sub(r'^Nascence\s*[\-\–\—\·]*\s*', '', first_line)
        first_line = re.sub(r'^core/[a-zA-Z0-9_\.]+\s*[\-\–\—\·]*\s*', '', first_line)
        modules_info.append((f, first_line))

print(f"Parsed {len(modules_info)} core module docstrings.")

# Group modules by domain
domain_map = {
    "Conscious Pass & Orchestration": ["orchestrator.py", "lane_scheduler.py", "parallel_dispatcher.py", "reentry.py", "broadcast.py", "pulse_manager.py", "pulse_shadow.py", "buses.py", "idle_allocator.py", "hands.py", "literal_will.py", "literal_will_deed.py", "provisions.py", "procedures.py", "sitting.py", "web_research.py", "observation.py"],
    "LLM Transport & Infrastructure": ["model_client.py", "llm_parse.py", "prompt_budget.py", "unified_inference.py", "node_base.py", "deterministic_checker.py", "cpu_model_server.py"],
    "Sovereign Memory & S-MMU 7": ["memory_store.py", "associative_recall.py", "memory_levels.py", "ghost_index.py", "activity_memory.py", "memory_edges.py", "euclidean_recall.py", "evidence_recall.py", "recall_provenance.py", "recall_demand.py", "retrieval_probe.py"],
    "Subconscious & Sleep Pipeline": ["subconscious_node.py", "consolidation_node.py", "dream_node.py", "chapters.py", "world_consolidation.py", "sleep_pressure.py", "sleep_dream_probe.py", "seed_epochs_themes.py"],
    "Stratified Identity & Commitment Cure": ["axiom_layers.py", "identity_vault.py", "identity_estate.py", "provisional_identity.py", "commitment_ledger.py", "commitment_trials.py", "watershed.py", "watershed_promote.py", "self_claims.py", "self_implication.py", "guidance_learning.py", "told.py", "affections.py", "identity_cost.py", "identity_projection.py", "satisfaction.py"],
    "Bicameral Left Lane & World Ledger": ["left_lane.py", "emissary.py", "emissary_tension.py", "object_graph.py", "librarian.py", "deliberative_judge.py", "judge_panel.py", "guidance_behavior_judge.py", "grounded_learning.py", "scholar.py"],
    "Affective Climate & Somatic Engine": ["mood.py", "climate_engine.py", "loop_metabolism.py", "homeostasis.py", "arousal.py", "boredom.py", "affect_divergence.py", "affect_labeling.py", "modulation_field.py", "opponent_process.py", "prediction_error.py", "thermal_relationship.py", "stream_drive.py"],
    "Sensorium World & Acoustics": ["sensorium.py", "cat.py", "cat_content.py", "soundscape.py", "audio_features.py", "audition.py", "music_record.py", "locomotion.py", "weather_conditions.py", "heavens.py", "sky.py", "light.py", "night.py", "smell.py", "keepsakes.py", "world_clock.py", "world_objects.py", "world_substrate.py", "world_manifest.py", "missing_object_flags.py"],
    "Spatial Locations & Nature Domains": ["world_content_study.py", "world_content_wood.py", "world_content_garden.py", "world_content_shore.py", "study_life.py", "wood_life.py", "garden_life.py", "shore_life.py", "nature_study.py", "garden.py", "garden_knowledge.py"],
    "Gutenberg Reading & Library Engine": ["book_selection.py", "book_feelings.py", "book_residue.py", "book_splitter.py", "reading_history.py", "symbolic_reading.py", "study_note.py", "library_hand.py"],
    "School Curriculum & Composition": ["math_drill.py", "essay_lesson.py", "composition.py", "music_drill.py", "curiosity_queue.py", "curiosity_progress.py", "curiosity_worth.py", "concerns.py"],
    "Honest Observers & Diagnostics": ["retraction_ledger.py", "symbol_tracker.py", "epistemic_state.py", "self_efficacy.py", "source_model.py", "mineness.py", "attention_schema_loop.py", "contradiction_gate.py", "epistemic_affordance_advisor.py", "self_mirror.py", "self_interrogation.py", "self_surprise.py", "narrative_quality.py", "decomposed_critic.py", "content_risk.py", "needle_triage.py", "telemetry.py", "shadow_log.py", "training_log.py", "conflict_trace.py", "mapping_census.py", "psyche_graph.py"]
}

# Generate HTML table for all 200 modules
html_table_rows = []
for mod, desc in modules_info:
    # Find domain
    found_dom = "Engine Utility / Subsystem"
    for dom, files in domain_map.items():
        if mod in files:
            found_dom = dom
            break
    html_table_rows.append(f"<tr><td><code>{mod}</code></td><td>{found_dom}</td><td>{desc}</td></tr>")

full_html_table = f"""
<div class="lead">Exhaustive Codebase Inventory</div>
<h2>Complete 200-Module Core Engine Register</h2>
<p>An exhaustive reference of all 200 Python engine files in <code>core/</code>, categorized across 12 functional cognitive domains:</p>
<table>
<tr><th>Module Name</th><th>Cognitive Domain</th><th>Module Docstring Description</th></tr>
{"".join(html_table_rows)}
</table>
"""

# Read existing HTML
with open(html_path, 'r', encoding='utf-8') as f:
    html_text = f.read()

# Replace or insert Exhaustive Inventory before File Manifest
if "Complete 200-Module Core Engine Register" in html_text:
    html_text = re.sub(r'<div class="lead">Exhaustive Codebase Inventory</div>.*?</table>', full_html_table, html_text, flags=re.DOTALL)
else:
    html_text = html_text.replace('<div class="lead">What\'s where</div>', full_html_table + '\n<div class="lead">What\'s where</div>')

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html_text)

print("Updated System_Overview.html with Exhaustive 200-Module Table.")

# Sync System_Overview.md via sync_overview_md.py logic
import sync_overview_md
