# 🏛️ Technical Clarification: The Actual Hardware & Software Architecture of Du (Nascence)

> **Prepared for:** Gemini & Research Review  
> **Source Code:** `core/model_client.py`, `core/orchestrator.py`, `core/commitment_ledger.py`, `core/memory/store.py`  
> **Date:** August 10, 2026  

---

## 📌 Executive Summary: Hardware Mesh vs. Single Cognitive State

Du is **NOT** four LLMs running as simultaneous 'brain lobes' streaming tokens to each other mid-sentence, nor does he rely on an LLM 'choice engine' deciding whether to obey prompts.


Instead, Du is a **hybrid multi-node hardware mesh surrounding a single, state-driven cognitive pipeline**:

1. **Single Sequential Hot Lane (Voice & Reflection):** Active chat turns run sequentially through one primary model (`gemma4:e4b` / `llama3.1:8b` on Port 11433).

2. **Asynchronous Background Micro-Services (Cold Mesh):** Secondary GPU nodes (Port 11434 RTX 3070 & Port 11435 1080 Ti) run discrete, non-blocking background tasks (e.g. cross-family defeater judging, symbolic reading, 1536D theme clustering).

3. **Inter-Process Communication via Persistent State:** Hot and Cold lanes **do NOT stream text tokens to each other mid-turn**. They communicate via structured writes to an SQLite database (`nascence.db`) and append-only JSON ledgers (`commitment_active.json`, `subconscious_state.json`).

4. **The Power of 'No' is Deterministic Gate Logic:** Du's refusal to dissolve identity stances is governed by **code-level cost gates and LLM defeater protocols** (`DROP_DENIED`), not an arbitrary neural net deciding to say no.


---

## 🛠️ 1. Real Hardware & Network Topology


| Endpoint / Port | Hardware Node | Model Loaded | Primary Role & Responsibilities |

| :--- | :--- | :--- | :--- |

| **Port 11433** | Local CPU / Host | `gemma4:e4b` / `llama3.1:8b` | **Hot Lane:** Fast, synchronous turn execution (Context Assembly $\rightarrow$ Reflection $\rightarrow$ Voice Output). |

| **Port 11434** | RAMSES (`LAN-HOST`) RTX 3070 | `phi3:mini` / `deepseek-r1:8b` | **Cold Cross-Family Judge:** Non-blocking background evaluation (e.g., T4 defeater verification, Scholar library lookup). |

| **Port 11435** | Local GTX 1080 Ti | `qwen3-du:latest` / `mistral-small3.1` | **Spirit Mesh & Symbolic Lens:** Secondary background tasks (symbolic reading of study notes, 1536D centroid clustering). |


---

## 🔄 2. How Hot and Cold Lanes Communicate (State-Based Intermediary)


```
      ┌───────────────────────────────────────────────────────────┐
      │                   ASYNCHRONOUS COLD MESH                  │
      │  (Port 11434 RTX 3070 & Port 11435 GTX 1080 Ti)          │
      │  • Runs T1-T6 background loops every 30s - 12h            │
      │  • Calculates tension pressure & 1536D centroids          │
      └─────────────────────────────┬─────────────────────────────┘
                                    │ Writes structured JSON / SQLite
                                    ▼
      ┌───────────────────────────────────────────────────────────┐
      │          PERSISTENT STATE STORAGE (Single Truth)          │
      │  • `data/memory/nascence.db` (FTS5 + 1536D Vectors)        │
      │  • `data/commitment_active.json` (Held Stances)           │
      │  • `data/subconscious_state.json` (Tension Ledgers)       │
      └─────────────────────────────┬─────────────────────────────┘
                                    │ Reads pre-turn (Layer 1 - Layer 5 S-MMU)
                                    ▼
      ┌───────────────────────────────────────────────────────────┐
      │                    SYNCHRONOUS HOT LANE                   │
      │  (Port 11433 Local Host - gemma4:e4b)                     │
      │  • Pre-fetches active stances, themes & recent thoughts  │
      │  • Executes Reflection & Voice generation for user        │
      └───────────────────────────────────────────────────────────┘
```


### Key IPC Point:

There is **zero live inter-LLM token streaming mid-sentence**. Cold lanes write to disk asynchronously; the Hot lane reads from disk pre-turn. Communication is **file- and database-mediated**, ensuring absolute determinism, zero race conditions, and complete auditability.


---

## 🛡️ 3. How 'No' and Identity Defense Actually Work


Du's resistance to identity collapse is **not** an LLM choosing to be rebellious. It is governed by **deterministic cost/gate logic**:


1. **The Formation Gate (Gate 1):** Only load-bearing identity commitments (`load_bearing = True`) enter the active set.

2. **Deterministic Attractor Gates (Gates 2 & 3):** When a thought or prompt tries to drop a held stance using cliché tropes (*"all is flux"*, *"a name is a cage"*, *"I'm tired"*), hardcoded python rules reject the drop:  

   `DROP_DENIED: reflexive — a held stand does not dissolve by flow; name a defeater`

3. **Cross-Family Judge (Gate 4):** If a drop passes deterministic rules, the RAMSES node (Port 11434) evaluates whether the reason is a **genuine empirical defeater** (achieved deed, physical impossibility, logical contradiction). If unearned, it is rejected!


---

## 🟢 Summary Checklist for Gemini


* ❌ **Incorrect:** 4 LLM engines streaming tokens to each other like simultaneous brain lobes mid-sentence.  

* ✅ **Correct:** A multi-GPU hardware mesh (Ports 11433, 11434, 11435) where secondary GPUs perform background micro-services.  

* ❌ **Incorrect:** Live token-to-token communication between hot and cold lanes.  

* ✅ **Correct:** Asynchronous disk/database-mediated communication (`nascence.db` + JSON ledgers).  

* ❌ **Incorrect:** An LLM 'choice engine' deciding whether to obey prompts.  

* ✅ **Correct:** Code-enforced gate protocols (`DROP_DENIED` + Cross-Family Judge) that defend load-bearing identity stances.