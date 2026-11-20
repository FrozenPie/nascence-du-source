# Implementation Plan — Causal Epistemic World Substrate & Object Biography (`world_epistemic_substrate_plan.md`)

> **System:** Sovereign Hub / Nascence Engine (`core/world_model.py`, `core/world_knowledge.py`, `core/observation.py`)  
> **Status:** 🟢 **STRICT PLANNING MODE — Awaiting User Review & Clearance**  
> **Target Path:** `c:/Nascence/docs/plans/world_epistemic_substrate_plan.md`  
> **Date:** 2026-08-11  

---

## 1. Executive Summary: Generative Causal Substrate & Object Biography

The Generative Epistemic World Substrate is a **Causal, Generative Environment**. Objects (`shore_driftwood_017`) carry persistent, generative **object biographies** (causal event sequences: tree fall $\rightarrow$ river transport $\rightarrow$ marine entry $\rightarrow$ storm events $\rightarrow$ stranding $\rightarrow$ solar exposure $\rightarrow$ fracture). Events dynamically alter physical state parameters, from which `core/observation.py` lossily samples observable features based on action epistemic resolution.

```text
                 ┌──────────────────────────────────────────┐
                 │ CAUSAL EVENTS GENERATOR                  │
                 │ tree_fall ──► river_transport ──►        │
                 │ marine_entry ──► storm_01 ──► storm_02   │
                 └────────────────────┬─────────────────────┘
                                      │
                               generates history
                                      │
                                      ▼
                 ┌──────────────────────────────────────────┐
                 │ LAYER 1: CAUSAL WORLD STATE              │
                 │ species: silver_beech, days_in_water: 91 │ (Accessible to Du: FALSE)
                 │ storm_events: 3, origin: river           │
                 └────────────────────┬─────────────────────┘
                                      │
                           modifies physical state
                                      │
                                      ▼
                 ┌──────────────────────────────────────────┐
                 │ LAYER 2: PHYSICAL STATE & PROPERTIES     │
                 │ density: 620 kg/m³, moisture: 0.31       │
                 │ bark_retention: 0.11, roughness: 0.74    │
                 │ edge_rounding: 0.68, fissuring: 0.28     │
                 └────────────────────┬─────────────────────┘
                                      │
                            sampled via action (lossy)
                                      │
                                      ▼
                 ┌──────────────────────────────────────────┐
                 │ LAYER 3: OBSERVATION & MEASUREMENT       │ (core/observation.py)
                 │ look ──► pale exposed grain, bark loss   │ (Action Epistemic Resolution)
                 │ pick up ──► light weight, dense balance  │
                 │ inspect_end ──► fine annual rings        │
                 └────────────────────┬─────────────────────┘
                                      │
                             evaluated using
                                      │
                                      ▼
                 ┌──────────────────────────────────────────┐
                 │ LAYER 4: DOMAIN KNOWLEDGE (Reference)    │ (core/world_knowledge.py)
                 │ "Bark loss + rounded ends = prolonged    │ (Diagnostic Relations;
                 │  transport; does NOT uniquely determine   │  NOT evidence for object)
                 │  species or exact days"                  │
                 └────────────────────┬─────────────────────┘
                                      │
                                      ▼
                 ┌──────────────────────────────────────────┐
                 │ LAYER 5: DU'S INFERENCE & MODEL REVISION │
                 │ "Branch fragment: 0.72, Silver beech:0.54│
                 │  Prolonged transport: 0.81               │
                 │  Exact duration: UNDETERMINED"           │
                 └──────────────────────────────────────────┘
```

---

## 2. Core Architectural Principles & Provenance Safeguards

### Principle A: Generative Object Biography
Objects carry dynamic event histories (`storm_01`, `sun_exposure`, `marine_reentry`) that modify physical parameters over time. Observations emerge naturally from state transitions.

### Principle B: 5-Layer Provenance Separation
1. **`CAUSAL_WORLD_STATE`**: Hidden simulation biography (species, exposure days, storms). **Lossy & Hidden from Du.**
2. **`PHYSICAL_STATE`**: Generative properties (density, moisture, roughness, edge rounding).
3. **`OBSERVATION`**: Raw perceptual facts directly perceived by Du. **Inference NEVER overwrites observation.**
4. **`DOMAIN_KNOWLEDGE`**: General diagnostic relationships. **Not evidence for this specific object.**
5. **`DU_INFERENCE`**: Derived candidate hypotheses, confidence ratings, and model revisions.

### Principle C: Epistemic Humility & Successful `UNDETERMINED` Outcomes
- When physics is underdetermined, `UNDETERMINED` is a **successful epistemic outcome**.
- Outcome States: `CORRECT`, `INCORRECT`, `PARTIALLY_RESOLVED`, `UNDERDETERMINED`, `UNOBSERVED`, `CONFLICTING`.
- The advisor can explicitly recommend `"do_nothing / pursue another question"` when information gain is low.

---

## 3. Proposed Component Breakdown

### Component 1: `core/world_model.py` [NEW]
- Dataclasses: `PhysicalProperty`, `CausalEvent`, `PhysicalObject`.
- SQLite table `world_objects_v2` in `sovereign_memory.db`.

### Component 2: `core/world_knowledge.py` [NEW]
- Diagnostic domain feature index.

### Component 3: `core/observation.py` [NEW]
- Action-specific epistemic sampling (`look`, `pick_up`, `inspect_end`, `scrape`, `float_test`).

---

## 4. Multi-Dimensional Epistemic Metrics Plan (8 Metrics)

1. **Identification Accuracy**: Correct object/species/category identification.
2. **Property Accuracy**: Alignment between inferred properties and physical state.
3. **Calibration**: Is 60% confidence correct ~60% of the time?
4. **Precision Discipline**: Does he avoid claiming information unsupported by evidence?
5. **Evidence Traceability**: Can every inference be traced back to raw observations and knowledge sources?
6. **Temporal Accuracy**: Model improvement over repeated longitudinal observations.
7. **Belief-Transition Quality**: Directionally appropriate confidence updates ($H_t \xrightarrow{\text{evidence}} H_{t+1}$).
8. **Exploration Value / Identifiability**: Advisor's ability to recognize when an uncertainty is unresolvable and recommend `"do_nothing"`.
