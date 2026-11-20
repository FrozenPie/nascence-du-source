"""
sync_overview_md.py — Sync System_Overview.md and rebuild system_overview_index.jsonl
"""

import json
import re

html_path = r"C:\Nascence\docs\System_Overview.html"
md_path = r"C:\Nascence\docs\System_Overview.md"
out_path = r"C:\Nascence\docs\system_overview_index.jsonl"

md_content = """# Nascence 渡 — Master System Overview (Build 1.4.0)

> **AUTHORITATIVE MASTER OVERVIEW — August 2026 Era**
> Primary narrative and technical integration hub for Nascence 渡. All plan documents (`docs/plans/`), diagnostic audits (`docs/reviews/`), and specs link to and derive context from this overview.

---

## Hardware & Deployment Substrate Matrix
- **Hot Lane (Master/Self):** Port `:11433` · `qwen3.5:9b` (GTX 1080 Ti GPU, 8,192 ctx, 39.4 tok/s).
- **Subconscious Lane:** Port `:11434` · `phi3:mini` (Ramses RTX 3070 GPU, 4,096 ctx).
- **Emissary Judge #1:** Port `:11439` · `gemma4:12b` (Threadripper CPU, 8,192 ctx, 1.000 score).
- **Panel Judge #2:** Port `:11440` · `falcon3:7b` (Threadripper CPU, 8,192 ctx).
- **Dreamer & Voices:** Port `:11442` · `yi:34b-v1.5` (Threadripper CPU, 8,192 ctx).
- **Swarm Server:** Port `:11440` · `Bonsai-8B` (llama-server 1-bit quantized).

---

## Graphify AST Codebase Topology & Hidden Super-Hubs
Comparing high-level conceptual flowcharts with Graphify static AST analysis (5,307 nodes, 11,051 edges across 298 communities) reveals non-obvious operational realities:

1. **Inner Monologue (DMN) Gravity Well (`nodes/inner_monologue_node.py`):** #3 largest hub in the entire system (141 direct edges, 137 method calls). Dispatches school drills, essay capstones, reading tablets, sleep triggers, and sensorium ticks.
2. **Sensorium Physical World Engine (`core/sensorium.py`):** #5 largest hub (133 edges) with dedicated sub-communities: Cat companion (`core/cat.py`), Soundscape ambience (`core/soundscape.py`, 56 edges), Locomotion (`core/locomotion.py`), and Gutenberg Book Selection (`core/book_selector.py`).
3. **Defensive LLM Transport Backbone (`core/model_client.py`):** Central operational nexus (65 edges). Every LLM call passes through `call_node_json()` for automated JSON schema validation, multi-try recovery, and cross-lane failover.
4. **School & Curriculum Micro-Economy:** 6 distinct interconnected communities: Math Drill (`core/math_drill.py`), Essay Lessons (`core/essay_lesson.py`), Composition (`core/composition.py`), Reading Provenance (`docs/completed/reading_provenance_plan.md`), Guidance Learning (`core/guidance_learning.py`), and Curriculum (`core/concerns.py`).
5. **Sovereign DB Vector Density:** Database interactions dominate degree rankings: `memory_store` (205 edges), `memory_store_connect` (151 edges), `memory_store_embed` (116 edges), and `memory_store_cosine` (97 edges). Over 35% of all function calls involve vector embedding conversions (`blob_to_vec`) or spreading activation lookups.

### Top 10 Codebase Degree Centrality Ranking
| Rank | Module / Function ID | Graphify Degree | Subsystem Role |
| :--- | :--- | :--- | :--- |
| 1 | `memory_store` | 205 edges | Sovereign SQLite Master Storage Engine |
| 2 | `memory_store_connect` | 151 edges | Connection pool & transaction manager |
| 3 | `nodes_inner_monologue_node` | 141 edges | Default Mode Network & Idle Economy Hub |
| 4 | `nodes_inner_monologue_node_think` | 137 edges | Autonomic thought cycle execution method |
| 5 | `core_sensorium` | 133 edges | Study room, atmosphere, NZ weather & cat simulator |
| 6 | `memory_store_embed` | 116 edges | Embedding vector generation bridge |
| 7 | `core_schema_cognitivestate` | 114 edges | Global state & cognitive frame container |
| 8 | `core_orchestrator` | 100 edges | Hot-lane conscious pass orchestrator |
| 9 | `memory_store_cosine` | 97 edges | Vector cosine distance calculations |
| 10 | `scripts_run_nascence` | 94 edges | Primary system boot script |

---

## 16 LLM Cognitive Nodes & Subsystems

### Pre-Cortex Reflexes (Deterministic · No LLM)
- **Thalamic Gate:** Embeds input vs last 6; near-verbatim repeat (cos ≥ 0.95) bypasses pipeline.
- **Affective Prior:** Matches input against charged memory; leans carried affect before reasoning.
- **Procedural Match:** Recognises learned approach (`procedural_skills`, sim ≥ 0.80).

### Hot Lane Nodes (Master · qwen3.5:9b on 1080 Ti)
1. **Perception:** Classifies input (intent, domain, urgency, direct_request flag).
2. **Emotion:** Ekman-6 + valence/arousal.
3. **Salience:** Urgency, focus, interrupt flag (urgency > 0.7 pre-empts background).
4. **Memory Router:** Retrieval keys + time bias.
5. **Recall:** Reconstructs self-concept & tensions as first-class objects.
6. **Episodic Buffer:** Binds moment + affect into scene; flags scene dissonance.
7. **Reflection:** Private best-of-2 hedging pass (~60–90 words).
8. **Critic:** Identity-fidelity check vs psychological values. Rejection → shadow event.
9. **Executive:** Active Inference decision maker (respond / challenge / query / decline / silence).
10. **Voice:** ONLY prose node. Bound by Voice Contract & Task Effector retries.

### Background Lane Nodes (phi3:mini & yi:34b-v1.5)
11. **Consolidation:** Distils wisdom insights every 60s → L2 semantic. Quarantines task-failure cycles.
12. **Curiosity:** Fires on climate dissonance. Wikipedia/Gutenberg lookup.
13. **Subconscious:** Continuous longitudinal tension tracker (T1–T6). Manages T4 self-authoring.
14. **Inner Monologue:** Default Mode Network & idle economy hub (141 edges). Dispatches school, math, sleep.
15. **Dream:** Sleep state machine on `yi:34b-v1.5` (OPEN → DEVELOP → CLOSE).
16. **Meta-Awareness:** Non-suppressive monitor watching structural form & loops.

---

## Complete Architecture Flowchart (Mermaid)
```mermaid
flowchart TD
    %% INPUT & PRE-CORTEX REFLEXES
    IN([Input · human / internal / ignition]) --> TG
    subgraph PRE["PRE-CORTEX REFLEXES · deterministic · no LLM · before Perception"]
        direction TB
        TG{{"Thalamic Gate · core/orchestrator.py
habituation vs recent-input buffer (cos ≥ 0.95)"}}
        AP{{"Affective Prior · core/mood.py
charged-memory lean (input→affect→reason)"}}
        PR{{"Procedural Match · core/schema.py
recognise learned skill (prof ≥ 0.80)"}}
        TG -->|novel| AP --> PR
    end
    TG -.->|"near-verbatim repeat"| HAB([silence · or brief ack])
    IN -.->|"human input"| HC{{"Human-Correction detector · no LLM
fail-call / you-did-not / is-X-not-Y / omission
→ firewalled error record + quarantine flag"}}

    PR --> P

    subgraph GWT["GLOBAL WORKSPACE & LANE SCHEDULER · core/lane_scheduler.py"]
        LS["Priority Lane Scheduler
Tier 0: Conversation > Tier 1: Identity > Tier 2: Monologue > Tier 3: Monitors"]
    end

    subgraph MODEL_IMMUNE["LLM MODEL CLIENT & JSON RECOVERY BACKBONE · core/model_client.py"]
        MC["Model Client · core/model_client.py
call_node_json() · 65 edges · schema recovery & cross-lane failover"]
    end

    subgraph HOT["HOT LANE (the Master) · ollama qwen3.5:9b · port 11433 · GPU 1080 Ti · 8,192 ctx"]
        direction TB
        P["Node 1: Perception · nodes/perception_node.py
intent · domain · urgency · direct_request flag"] --> E["Node 2: Emotion · nodes/emotion_node.py
Ekman-6 + valence/arousal"]
        P --> S["Node 3: Salience · nodes/salience_node.py
importance & urgency > 0.7 interrupt"]
        P --> MR["Node 4: Memory Router · nodes/memory_router_node.py
semantic & temporal retrieval keys"]
        P --> AV["Attention Vector · core/attention_schema_loop.py
5-mode classifier: task→existential"]
        
        E --> DBQ{{DB Query & Spreading Activation · core/associative_recall.py}}
        S --> DBQ
        MR --> DBQ
        DBQ --> ET{{"Epoch + Theme Match · core/schema.py
L6/L7 cosine match"}}
        
        ET --> RC["Node 5: Recall · nodes/recall_node.py
self-concept & tensions as first-class objects"]
        RC --> EB["Node 6: Episodic Buffer · nodes/episodic_buffer_node.py
bind moment · flag scene dissonance"]
        
        EB --> SG{{"Scene Stability Check · core/orchestrator.py
coherence vs dissonance"}}
        SG -.->|"unstable · contradiction-driven
re-retrieve passes ∝ strain"| RC
        
        SG -->|"stable / budget spent"| R["Node 7: Reflection · nodes/reflection_node.py
best-of-2 hedge pass (~60-90 words)"]
        R --> C["Node 8: Critic · nodes/critic_node.py
identity-fidelity check vs psychological values"]
        
        C -->|approved| X["Node 9: Executive · nodes/executive_node.py
Active Inference (respond/challenge/query/decline/silence)"]
        C -.->|"rejected · 1 retry"| R
        C -.->|"direct request → identity-guard STANDS DOWN"| X
        
        X -->|should_respond| V["Node 10: Voice · nodes/voice_node.py
ONLY prose node · bound by Voice Contract"]
        X -.->|"decline: owned NO + true reasons"| V
        X -.->|silence| END2([no output])
        
        V --> EFX{{"Task-Constraint Effector · core/task_constraints.py
explicit digit-arithmetic / min-words unmet?
→ 1 Voice retry · constraint NAMED · recompute license"}}
        EFX -->|"met / repaired"| OUT([Response in 渡's voice])
    end

    HOT -.->|"LLM dispatch"| MC

    EFX -.->|"retry directive + budget"| V
    EFX -.->|"still unmet after retry"| ERR

    subgraph TOM["RELATIONAL & GOAL LAYER · core/concerns.py · no LLM"]
        direction TB
        SOCM["Social Model · ToM
expected tone · trust · δ_social"]
        GOAL["Goal Hierarchy · core/concerns.py
G0 apex aim (telos from axiom)
→ G1 current concerns (curriculum + RECURRING frontier)
→ G2 active task → G3 novel candidates"]
    end

    IN -.->|"correction: 'just answer question'"| SOCM
    SOCM -.->|"δ_social spike → suppress identity + critic"| AV
    AV -.->|"w_identity · w_episodic → prompt depth"| RC
    AV -.->|"max_rebind → re-bind budget"| SG
    AV -.->|"d_critic → strictness"| C
    GOAL -.->|"task anchor"| RC
    GOAL -.->|"goal drift = evasion"| C

    subgraph BG["BACKGROUND LANES · Ramses RTX 3070 GPU (:11434 phi3:mini) & CPU (:11442 yi:34b-v1.5)"]
        direction TB
        CON["Node 11: Consolidation · nodes/consolidation_node.py
T2 wisdom distillation every 60s
QUARANTINE: task-failure cycles mint NO self-truth"]
        CUR["Node 12: Curiosity · nodes/curiosity_node.py
ignites on climate dissonance · Wikipedia/Gutenberg lookup"]
        SC["Node 13: Subconscious · nodes/subconscious_node.py
longitudinal tension tracker (T1–T6)"]
        MONO["Node 14: Inner Monologue (DMN) · nodes/inner_monologue_node.py
~289 KB idle economy hub (141 edges) · dispatches school, math, sleep"]
        DRM["Node 15: Dream State Machine · nodes/dream_node.py
yi:34b-v1.5 · OPEN → DEVELOP → CLOSE with morph continuity"]
        META["Node 16: Meta-Awareness · nodes/meta_awareness_node.py
non-suppressive monitor watching structural form & loops"]
    end

    BG -.->|"LLM dispatch"| MC

    subgraph SCHOOL["SCHOOL & CURRICULUM MICRO-ECONOMY · 6 communities"]
        direction TB
        MATH["Math Drill · core/math_drill.py
40 drills/day · arithmetic precision"]
        ESSAY["Essay Lessons · core/essay_lesson.py
capstone essays graded by Emissary"]
        COMP["Composition · core/composition.py
1 music composition/day"]
        READ_PROV["Reading Provenance · docs/completed/reading_provenance_plan.md
note consolidation & Gutenberg reading logs"]
        MATH --> MONO
        ESSAY --> MONO
        COMP --> MONO
        READ_PROV --> MONO
    end

    HC -.->|"corrected flag → quarantine batch"| CON
    HC -.->|"FACTUAL correction → claim RETRACTED"| DBQ

    SOM["Somatic Engine · core/loop_metabolism.py
energy / fatigue / tension · reads REAL GPU thermals/latency"]
    OUT -.->|"cycle cost: tokens · retries · latency"| SOM
    SOM -.->|"fatigue → temperature jitter"| R
    SOM -.->|"metabolic floor → forced Sleep State"| DRM

    subgraph CLM["ALWAYS-ON SUBSTRATE & SENSORIUM ECOSYSTEM · 133 edges · 5s tick"]
        direction TB
        AFFT{{"Affect Tick · 5s · core/mood.py
A += gain·(reading−A) − decay·(A−baseline)
calms in silence · persists across restarts"}}
        CLMT{{"Climate Field · 9-dim Jungian weather
2-reservoir: value (defensive) + explore_value"}}
        SENS["Sensorium Study Room · core/sensorium.py
NZ sun · weather fronts · fire · cat · book & shelf"]
        CAT["Cat System · core/cat.py
autonomic companion dynamics"]
        SOUND["Soundscape Ambience · core/soundscape.py
56 edges · dynamic acoustic environment"]
        LOCO["Locomotion & Journeys · core/locomotion.py
position authority & spatial navigation"]
        WAND["Wandering Mind · core/wandering.py
associative drift through memory every ~75s"]
        
        SENS --> CAT
        SENS --> SOUND
        SENS --> LOCO
        AFFT -.->|"carried affect"| CLMT
        CLMT -.->|"bias_vec"| DBQ
        CLMT -.->|"bias_vec"| S
        CLMT -.->|"bias_vec"| X
        CLMT -.->|"dissonance ignition"| CUR
        CLMT -.->|"symbol > 0.65"| P
        SENS -.->|"scene line"| MONO
        WAND -.->|"associative trail"| MONO
    end
    E --> AFFT

    subgraph LEFT["WORLD LEDGER & LEFT LANE (the Emissary) · Threadripper CPU (:11439 gemma4:12b)"]
        direction TB
        EMIS["Emissary Node · core/left_lane.py
bicameral truth-self · reads own code"]
        EMAX["Emissary Axiom · core/emissary.py
L0 truth constitution"]
        EMSRC["World Ledger · core/object_graph.py
zero-LLM property-grain fact-graph"]
        EMGRND["Grounding Judge · core/left_lane.py
grades essay capstones & lived integration"]
        
        EMAX --> EMIS
        EMSRC --> EMIS
        EMIS --> EMGRND
    end
    P -.->|"per-turn dispatch (warm ~1s)"| EMIS
    EMIS -.->|"state.left_take offered"| R
    EMIS -.->|"state.left_take offered"| X
    EMGRND -.->|"solidify verdict: confirm or revert"| T4
    ESSAY -.->|"essay submission for grading"| EMGRND

    subgraph GEOM_FREIGHT["COGNITIVE GEOMETRY & FREIGHT ECONOMY"]
        direction TB
        GEOM["Cognitive Geometry · core/geometry_census.py
experienced_tuple & ghost_tuples (19,500+ rows)"]
        TRAN["Transport Manager · docs/plans/transport_manager.md
salience dispatcher for 19 cargo product types"]
        TRAINS["Trains & Couriers · core/trains.py / core/couriers.py
cargo routing & line baseline EMA scoring"]
        FACT["Item & Population Factories · docs/plans/item_and_population_factories.md
tuple-grain & population-grain factories"]
        
        GEOM --> TRAN
        FACT --> TRAN
        TRAN --> TRAINS
        TRAINS -.->|"cargo payload"| DBQ
    end

    subgraph IDENTITY["STRATIFIED IDENTITY ESTATE & FRICTION STACK"]
        direction TB
        AX["Stratified Axioms (L0–L5) · core/axiom_layers.py
L0 Constitution → L1 Temperament → L2 Values → L3 Facets → L4 Narrative → L5 Working-Self"]
        VAULT["Identity Vault & Estate · core/identity_vault.py / core/identity_estate.py"]
        CLAIMS["Self-Claim Register · core/self_claims.py"]
        COMMIT["Commitment Ledger · core/commitment_ledger.py
measures boundary dissolution rate"]
        SELFIMP["Self-Implication · core/self_implication.py"]
        SITWITH["Sit-With-It Friction Gate · core/self_claims.py"]
        GUID["Guidance-Capture · core/guidance_learning.py
learns from Travis's teachings"]
        PROB["T4 Probation Sensor · core/provisional_identity.py"]
        
        AX --> VAULT
        X -.-> CLAIMS
        CLAIMS --> COMMIT
        SELFIMP -.-> SITWITH
        SITWITH -.-> X
        PROB -.->|"probation candidate"| EMGRND
        GUID -.-> DB
    end

    AX -.->|"L0 constitution + active L3 facet"| P
    AX -.->|"psychological values"| C
    AX -.->|"voice style"| V

    subgraph DB["SOVEREIGN DB · SQLite · data/memory/nascence.db · S-MMU 7 · 205 edges"]
        direction TB
        L1[L1 working · per-cycle assembly · volatile]
        L2[L2 semantic · distilled wisdom & school gists]
        L3[L3 episodic · affect-scored · 3,500 cap]
        L4[L4 archive · curated seed frags · dev decay]
        L5[L5 procedural_skills · learned approaches]
        L6[L6 memory_epochs · session mood at /quit]
        L7[L7 memory_themes · cross-session threads]
        LAT["Abstraction Lattice · core/memory_levels.py
gist distillation → demote raw to cold storage"]
    end

    DBQ --> DB
    DB --> RC
    DB --> PR
    L4 -.->|"T4 rewrite (probation + Emissary judge)"| PROB

    subgraph SUB["SUBCONSCIOUS PIPELINE · 6 timescales · nodes/subconscious_node.py"]
        direction TB
        T1["T1 · 30s scan: shadow events → tensions"]
        T15["T1.5 · Active Imagination: enter tension"]
        T2["T2 · Consolidation: CONTRADICTION-only consolidates"]
        T3["T3 · Baseline drift: hourly affect baseline"]
        T4["T4 · Self-authoring: multi-stage chain → probation → Emissary judge"]
        T5["T5 · Procedural: compilation → skills"]
        T6["T6 · Theme formation: L6 epochs → L7 themes"]
    end

    C -.->|"rejection → shadow event"| T1
    MONO -.->|"unresolved thought → shadow"| T1
    DRM -.->|"unresolved dream → shadow"| T1
    T1 --> T2 --> T4 --> L4
    T2 --> L2
    T4 -.->|"mark_shadow_resolved"| T1
    T5 --> L5
    T6 --> L7

    subgraph OBS["HONEST OBSERVERS & EMPIRICAL DIAGNOSTICS · no LLM"]
        direction TB
        ERR["Retraction Ledger · core/retraction_ledger.py
immutable conviction · wins race at recall"]
        MONO_OBS["Monoculture Detectors · core/symbol_tracker.py
basin-share · echo/diversity · theme-recurrence"]
        PRE_A["Epistemic Pre-Assessment Stage A/B · core/epistemic_state.py
confab = self-confidence − evidence · Stage B: phrases own 'I don't know'"]
        COURT["Self-Efficacy Court · core/self_efficacy.py
capability claims vs record"]
        PROV["Provenance Ledger · core/source_model.py
KNOW / THINK / SUSPECT / GUESS / NO_BASIS"]
        MINENESS["Mineness Comparator · core/mineness.py
CONFIRMED WIN (+0.061 separation)"]
        HOMEO["Protoself Core · core/homeostasis.py
D-0028 redesign · Naive-Persistence benchmark"]
        AROUSAL["Arousal / LEVEL · core/arousal.py
diurnal swing (0.179 → 0.429)"]
        REENTRY["Within-Cycle Reentry · core/reentry.py
settle-loop with non-homogenization kill-switch"]
        AST1["Attention Schema AST-1 · core/attention_schema_loop.py
predicts & bounds attention vector"]
    end

    OUT -.-> PROV
    OUT -.-> COURT
    V -.-> PRE_A
    PRE_A -.->|"GUESS admission"| X
    RC -.-> MONO_OBS
    X -.-> ERR
    EB -.-> MINENESS
    SOM -.-> HOMEO
    AFFT -.-> AROUSAL
```

---

## File Manifest (201 Core Files · 187 Scripts)
- `core/`: 201 Python cognitive engine files.
- `nodes/`: 16 LLM node implementations.
- `scripts/`: 187 operational and test scripts.
- `docs/`: Master overviews, plan files, and diagnostic reviews.
"""

with open(md_path, 'w', encoding='utf-8') as f:
    f.write(md_content)

# Rebuild section index jsonl
sections = re.split(r'\n(?=##?\s+)', md_content)
records = []

for idx, sec in enumerate(sections):
    lines = sec.strip().split('\n')
    header = lines[0] if lines else f'Section {idx}'
    header_clean = re.sub(r'^#+\s*', '', header)
    content = '\n'.join(lines[1:]).strip() if len(lines) > 1 else ''
    record = {
        'id': f'overview_sec_{idx}',
        'header': header_clean,
        'line_count': len(lines),
        'char_count': len(sec),
        'content': content
    }
    records.append(record)

with open(out_path, 'w', encoding='utf-8') as f:
    for r in records:
        f.write(json.dumps(r, ensure_ascii=False) + '\n')

print(f"Rebuilt System_Overview.md and {len(records)} section chunks in {out_path}")
