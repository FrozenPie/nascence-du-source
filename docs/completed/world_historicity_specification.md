# 📜 Architectural Contract v1.4: Headless World Laboratory & Phase 0 Testing Protocol

> **System Status:** APPROVED ARCHITECTURAL CONTRACT v1.4 (Phase 0 Ready)  

> **Source Modules:** `core/sensorium.py`, `core/spatial.py`, `core/soundscape.py`, `core/world_content_shore.py`  

> **Date:** August 10, 2026  

---

## 🔬 1. The Headless World Laboratory Principle


### Invariant 8: Headless Isolation Invariant

> **"The world mechanics MUST be completely testable without Du, without LLMs, without monologue, and without prompt generation."**  

By testing world physics in a headless harness, we eliminate attribution error: we never confuse simulation bugs with cognitive failures.


```
                    HEADLESS TESTING HARNESS
            (No Du / No LLM / No Prompt Generation)
                               │
                               ▼
        ┌──────────────────────────────────────────────┐
        │ 1. WORLD PHYSICS & TIME ACCELERATION         │
        │ (Tide cycles, storm surge, state persistence)│
        └──────────────────────┬───────────────────────┘
                               │
                               ▼
        ┌──────────────────────────────────────────────┐
        │ 2. SENSORY ACCESSIBILITY GATE                │
        │ (Line-of-Sight, 3D Sound propagation)        │
        └──────────────────────┬───────────────────────┘
                               │ Only after passing Experiments A-E
                               ▼
        ┌──────────────────────────────────────────────┐
        │ 3. DU COGNITIVITY INTEGRATION                │
        │ (Turn-Time Context Assembly & Reflection)    │
        └──────────────────────────────────────────────┘
```


---

## 🧪 2. The 5 Headless Experiments (World Laboratory)


| Experiment | Objective | Success Criteria |

| :--- | :--- | :--- |

| **Experiment A — Determinism** | Seed 42 run 24h vs. Seed 42 run 24h. | Identical physical world state trajectories. |

| **Experiment B — Single Perturbation** | World A (Storm moves `driftwood_17`) vs World B (No storm). | States diverge deterministically. |

| **Experiment C — Historical Interaction** | Same tide applied to pre-altered World A vs baseline World B. | Downstream physical pooling/drainage diverges. |

| **Experiment D — Sensory Blindness** | Object exists + outside sensory field. | `world_state = present`, `sensory_state = inaccessible`. |

| **Experiment E — Acoustic Causality** | Physical state transition occurs off-camera. | Sound propagated with exact physical provenance. |


---

## 🚀 3. Updated Implementation Sequence


1. **Phase 0 — Headless World Laboratory:** Build `scripts/world_laboratory.py` (no LLM) and pass Experiments A–E.

2. **Phase 1 — Driftwood:** Implement `driftwood_17` single object mechanics in `data/world_objects.json`.

3. **Phase 2 — Footprints:** Add environmental trace decay (rain vs. tide erasure laws).

4. **Phase 3 — Acoustics:** Connect physical state transitions to unseen 3D spatial acoustic propagation.

5. **Phase 4 — Sensory Connection:** Connect the verified world state to S-MMU Context Assembly.

6. **Phase 5 — Du Encounter:** Allow Du to experience the verified persistent world.


---

## 🟢 Contract v1.4 Locked & Ready for Phase 0

Contract v1.4 is frozen. We will now build **Phase 0 (`scripts/world_laboratory.py`)** to test world physics completely headless before introducing Du!