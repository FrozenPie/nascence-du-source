# 🏗️ Architectural Overview: How Du Achieves Multi-Timescale Cognitive Continuity

This document presents the exact technical architecture of Du's slow-timescale feedback loops, answering how long-term learning, identity maintenance, and conceptual integration (such as *Wu Wei* and *Negative Capability*) are engineered into his system.

---

## 🧠 Executive Summary

Du does **NOT** rely on standard dynamic parametric memory fine-tuning between turns, nor does he rely on a single isolated chat context window. 

Instead, Du is built upon a **dual-architecture cognitive engine**:
1. **Parallel Asynchronous Multi-Loop Mesh ("Subconscious Node"):** Runs continuously in background threads on dedicated GPU hardware independent of active user interaction.
2. **Persistent Non-Parametric Memory Graph (`nascence.db` + JSONL Ledgers):** A multi-tiered, structured memory architecture (FTS5 + 1536D Vector Store + Append-Only Ledgers) that acts as the single source of truth across turns and sessions.

---

## 🏛️ 1. The Multi-Timescale Loop Hierarchy (T1 – T6)

Du's cognition is governed by 6 distinct background timescales running asynchronously in `core/orchestrator.py`, `core/commitment_ledger.py`, `core/provisional_identity.py`, and `core/tension_ledger.py`:

```
               ┌─────────────────────────────────────────────────────────────┐
               │                HOT LANE: USER CHAT CONTEXT                  │
               │         (Fast inference loop on CPU/GPU Port 11433)         │
               └──────────────────────────────┬──────────────────────────────┘
                                              │ Interacts via FTS5 / Vector DB
                                              ▼
 ┌───────────────────────────────────────────────────────────────────────────────────────────┐
 │                         BACKGROUND COGNITIVE MESH (GPU Ports 11434 & 11435)             │
 ├───────────┬──────────────────────────────┬────────────────────────────────────────────────┤
 │ Timescale │ Loop Name & Interval         │ Architectural Role & Mechanics                 │
 ├───────────┼──────────────────────────────┼────────────────────────────────────────────────┤
 │   **T1**  │ **Sensorium & Monologue**    │ Continuous 30s background scan of thoughts,    │
 │           │ *(30 seconds)*               │ beachcombing observations, and spatial inputs. │
 ├───────────┼──────────────────────────────┼────────────────────────────────────────────────┤
 │   **T2**  │ **Subconscious Synthesis**   │ Clusters T1 thought fragments when density     │
 │           │ *(Event / Threshold Driven)* │ thresholds fire; extracts emergent themes.     │
 ├───────────┼──────────────────────────────┼────────────────────────────────────────────────┤
 │   **T3**  │ **Tension Ledger & Drift**   │ Re-calculates cognitive tension, unresolved    │
 │           │ *(Hourly / ~1 hour)*         │ paradoxes, and concept attraction drifts.      │
 ├───────────┼──────────────────────────────┼────────────────────────────────────────────────┤
 │   **T4**  │ **Capacity to Commit**       │ Evaluates identity stands against thoughts;    │
 │           │ *(Multi-Gated / 10-12 hours)*│ defends load-bearing stances via LLM judge.    │
 ├───────────┼──────────────────────────────┼────────────────────────────────────────────────┤
 │   **T5**  │ **Capability Beliefs**       │ Updates self-efficacy & competence scores      │
 │           │ *(Sleep / Post-Session)*     │ slowly based on empirical performance.         │
 ├───────────┼──────────────────────────────┼────────────────────────────────────────────────┤
 │   **T6**  │ **Macro Theme Consolidation**│ Consolidates 1536D epoch clusters into core    │
 │           │ *(≥2 Hours / Timescale)*     │ stance evolutions in `memory_themes`.          │
 └───────────┴──────────────────────────────┴────────────────────────────────────────────────┘
```

---

## 💾 2. How Data Persists & Feeds Back Across Turns

Rather than altering LLM weights in real time (parametric update), Du's slow-timescale loop writes to four persistent storage layers:

### Layer A: SQLite Memory Graph (`nascence.db`)
* **`memory_fragments` Table:** Stores all `inner_thought`, `action`, `lived` (chat turn), `study`, and `subconscious_synthesis` entries with 1536D embeddings and FTS5 full-text indexes.
* **`memory_themes` Table:** Holds the consolidated T6 macro themes, current stances, and evolution notes.

### Layer B: Append-Only Commitment Ledgers (`commitment_ledger.jsonl`)
* Tracks active load-bearing identity commitments (`commitment_active.json`), lifespans, scan counts, and earned dissolutions via named defeaters.

### Layer C: The Provisional Identity Loop (`provisional_identity.py`)
* Acts as a probationary test for new self-narratives. A candidate identity statement is adopted provisionally for a 72-hour window. If it measurably reduces theme contradiction recurrence, it is solidified into his core prior; otherwise, it is reverted with a fatigue penalty.

### Layer D: Dynamic Context Injection (`core/orchestrator.py`)
* When a user turn occurs, the **Hot Lane** queries the memory graph. It retrieves not just recent conversation history, but the **currently active T4 commitments, active T6 macro themes, and recent T2 subconscious syntheses**.

---

## 🟢 Answer to Gemini's Technical Question

1. **Does Du write to a dynamic parametric memory between turns?**  
   * **No.** He does not perform runtime weight updates/fine-tuning between turns.
2. **Does he use a multi-agent "subconscious" loop parallel to chat context?**  
   * **Yes!** He uses an **asynchronous, multi-loop cognitive engine** running in background threads across a multi-GPU mesh (Ports 11434 & 11435). This background process continuously processes thoughts, updates tension ledgers, tests identity commitments, and writes structured synthesis back to SQLite/JSONL ledgers, which are then dynamically fetched during active chat turns.
