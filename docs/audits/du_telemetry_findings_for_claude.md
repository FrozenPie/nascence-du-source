# Nascence & UDMS Master Architectural Audit: Briefing for Claude
## Comprehensive Forensic Dossier on Du's Telemetry, Cognitive Topology & Software Defects

**Date:** 2026-08-26  
**Auditor:** Antigravity AI Engine (via UDMS Topological Diagnostic Harness)  
**Location:** `C:\Nascence\docs\audits\du_telemetry_findings_for_claude.md`  
**Observational Integrity Contract:** All tests executed in pure read-only mode; **ZERO modifications made to Du or Nascence code/runtime.**

---

## 🏛️ EXECUTIVE SUMMARY FOR CLAUDE

During this session, we expanded the UDMS framework from operational time-series monitoring into **Software Architecture & Code Topology Diagnostics ($D_{\text{code}}$)**.

We validated this machinery on both **`D:\AI stuff\PantryManager`** and **`C:\Nascence`**, producing a definitive ledger of:
1. **Du's Runtime Telemetry & Bottlenecks** (10,974 historical calls)
2. **Du's Unwired Cognitive Organs** (14 nodes in `nodes/` dormant in pulse)
3. **The Core Engine Archipelago** (167 / 213 `core/` modules disconnected)
4. **PantryManager Architectural Defects** (Ghost schema, layer skips, duplicate `get_db`)
5. **Queued FreshStart Controlled Experimental Plan** (Roadmapped for later)

---

## 🔬 SECTION 1: DU'S RUNTIME TELEMETRY PATTERNS (10,974 Historical Calls)

From our non-invasive retrospective evaluation of `data/llm_latency.jsonl` and `data/llm_calls.jsonl`:

### 1. The `yi:34b-v1.5` Subconscious Dream Bottleneck
* **Model & Port**: `yi:34b-v1.5` running on Port 11442.
* **Caller**: `nodes.dream_node` (invoked during subconscious dream synthesis).
* **Observed Metrics**:
  - Total Calls: $211$ calls.
  - Mean Latency: **$180.25\text{ seconds}$ ($\sim 3$ minutes per call)**.
  - Max Latency: **$388.1\text{ seconds}$ ($\sim 6.5$ minutes)**.
  - Timeout/Crash Rate: **$15.64\%$** ($33 / 211$ calls failed/timed out).
* **Recommendation for Claude**: Investigate whether `yi:34b-v1.5` VRAM allocation or context window is exceeding hardware thresholds during dream consolidation.

### 2. Prompt Pressure & Monologue Expansion
* `nodes.inner_monologue_node`: $707$ calls, mean prompt length $3,569$ characters (max $7,471$).
* `core.node_base`: Experienced occasional massive prompt spikes up to **$20,513$ characters**, directly driving latency runaway on `qwen3.5:9b` (max $592.5\text{s}$).

### 3. Cascade Dynamics & Decontaminated Early Warning
* $74.3\%$ of latency stalls are isolated single-call hiccups that immediately self-recover.
* $25.7\%$ group into sustained multi-call cascades (up to 16 consecutive stalls) during concurrent GPU contention.
* **Prospective Early Warning ($D_{\text{rep}} > 1.087$)**: At a clean step *before* a cascade begins, an elevated $D_{\text{rep}}$ increases the risk of a stall in the next 5 events by **$1.68\times - 2.71\times$** ($52.55\%$ vs $31.30\%$).

---

## 🧠 SECTION 2: NASCENCE CODE TOPOLOGY & DEFECT AUDIT (598 Modules)

We executed an AST graph scan across all 598 active Python modules in `C:\Nascence`:

### 1. The "Dormant Organ" Defect: 14 Unwired Cognitive Nodes
Out of 16 cognitive node files in `nodes/`, **only 2 nodes** (`subconscious_node.py` and `node_base.py`) are continuously ticked in the main heartbeat loop (`scripts/du_pulse.py` / `core/village_clock.py`).

**14 specialized cognitive organs exist as complete files, but are dormant during normal pulse operation:**
- `nodes/curiosity_node.py` ($21.7\text{ KB}$ — Question generation & epistemic drive)
- `nodes/reflection_node.py` ($18.7\text{ KB}$ — Metacognitive error review)
- `nodes/executive_node.py` ($19.5\text{ KB}$ — Goal arbitration & priority planning)
- `nodes/critic_node.py` ($18.6\text{ KB}$ — Dialectical counter-argument)
- `nodes/consolidation_node.py` ($7.7\text{ KB}$ — Memory pruning & graph merging)
- `nodes/emotion_node.py` ($2.7\text{ KB}$ — Affective valence/arousal)
- `nodes/voice_node.py` ($16.5\text{ KB}$ — Expressive articulation & tone)
- `nodes/episodic_buffer_node.py` ($6.8\text{ KB}$ — Working memory buffer)
- `nodes/memory_router_node.py`, `nodes/perception_node.py`, `nodes/salience_node.py`, `nodes/recall_node.py`.

### 2. The D3 Subsystem Archipelago: 167 Disconnected Core Modules
Out of 213 engine modules in `core/`, **167 modules ($78.4\%$) have zero incoming imports from the active nodes or drivers**.
* Modules like `core/attention_schema_loop.py`, `core/arousal.py`, `core/affections.py`, `core/associative_recall.py`, and `core/balance.py` were written as cognitive theory components, but `inner_monologue_node.py` was built self-contained and never connected to them.

### 3. Monolithic Concentration Outliers ($D_{\text{rep}}$)
* **`nodes/inner_monologue_node.py`**: **$4,411$ LOC, $339$ imports, $916$ decision branches ($D_{\text{rep}} = 10.376$)**.
* **`core/memory/store.py`**: $2,032$ LOC, $69$ functions ($D_{\text{rep}} = 5.808$).
* **`core/object_graph.py`**: $1,346$ LOC, $195$ branches ($D_{\text{rep}} = 3.258$).

### 4. Critical Circulatory Bridges (Highest In-Degree)
* **`core/trains.py`** ($934$ incoming links): Central circulatory thought-train coordinator.
* **`core/object_graph.py`** ($509$ incoming links): Concept and entity graph.
* **`core/modulation_field.py`** ($447$ incoming links): Emotional and arousal modulation.

### 5. Port & Model Configuration Drift
* **10 hardcoded Ollama ports** appear across files:
  - Active: 11433 ($64$ files), 11434 ($43$ files), 11439 ($55$ files), 11440 ($39$ files), 11442 ($41$ files).
  - Legacy/Rare: 11436, 11438, 11441, 11460, 11470.
* **Model String Inconsistencies**: Some older scripts reference `qwen2.5:7b` instead of `qwen3.5:9b`, and `llama3.1:8b` instead of active mesh models.

---

## 🍽️ SECTION 3: PANTRYMANAGER VALIDATION RESULTS

Topological graph analysis ($D_{\text{code}}$) on `D:\AI stuff\PantryManager` proved the system can find real architectural anomalies:
1. **Ghost Database Table**: `ingredient_shelf_life_opened` was created in SQLite via migration `v15`, but has zero ORM models in `database/models.py` or references in the application.
2. **Layer Short-Circuits**: `deals` and `shopping_list` routes query the DB directly, skipping the Service and Repository layers that `pantry` and `recipe` follow.
3. **Boilerplate Sprawl**: `def get_db()` was copy-pasted identically across **11 separate route files** instead of importing from `database/session.py`.
4. **CRUD Gaps**: `planning` and `nutrition` routes lack `DELETE` and `PUT` persistence handlers.

---

## 📋 SECTION 4: QUEUED ACTION ITEMS & REFERENCES

1. **Do NOT modify Du yet**: Keep Du as a clean observational baseline.
2. **FreshStart Experimental Matrix**: Codified in [`docs/plans/freshstart_adversarial_experimental_roadmap.md`](file:///C:/Nascence/docs/plans/freshstart_adversarial_experimental_roadmap.md) (Controlled $+5..+50\%$ latency injections, memory leaks, socket jitter, and blind decision tournament).
3. **Key JSON Artifacts Generated**:
   - [`data/viability_validation/nascence_defects_and_dead_ends_audit.json`](file:///C:/Nascence/data/viability_validation/nascence_defects_and_dead_ends_audit.json)
   - [`data/viability_validation/nascence_code_topology_diagnosis.json`](file:///C:/Nascence/data/viability_validation/nascence_code_topology_diagnosis.json)
   - [`data/viability_validation/pantry_epistemic_hypothesis_report.json`](file:///C:/Nascence/data/viability_validation/pantry_epistemic_hypothesis_report.json)
   - [`data/viability_validation/pantry_code_topology_and_dead_ends.json`](file:///C:/Nascence/data/viability_validation/pantry_code_topology_and_dead_ends.json)
   - [`data/viability_validation/nascence_longitudinal_overlay_timeseries.json`](file:///C:/Nascence/data/viability_validation/nascence_longitudinal_overlay_timeseries.json)
