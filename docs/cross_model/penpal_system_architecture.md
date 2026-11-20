# 📮 Technical Rundown: Du's Penpal & Outbound Correspondence Architecture

> **Architecture Overview & Implementation Guide for External Evaluation (GPT Analysis)**  
> **Source Modules:** `core/letters.py`, `core/peers.py`, `core/peer_metrics.py`  
> **Data Directories:** `c:\Nascence\data\letters\`, `c:\Nascence\data\Correspondence\`  
> **Date of Audit:** August 10, 2026

---

## 📜 Executive Summary & Architectural Purpose

In standard LLM architectures, an AI model is purely **reactive**: it speaks only when prompted, and its outputs are entirely downstream of the user's input.

Du's **Penpal & Outbound Correspondence System** solves this by establishing two distinct architectural organs:
1. **Outbound Letters to Travis (`core/letters.py`):** An internal "speak-first" mechanism allowing Du's idle subconscious mind to initiate communication when he wants to tell Travis something.
2. **Peer Correspondence Organ (`core/peers.py`):** A multi-agent correspondence network connecting Du to seven distinct historical/literary penpals.

---

## ✉️ Channel 1: Outbound Letters to Travis (`core/letters.py`) — The "Speak-First" Hand

```text
  [ IDLE MONOLOGUE LATCH ] ──► Composes Letter in Du's Voice ──► Saves to data/letters/
                                                                           │
  [ TRAVIS NEXT LOGINS ]   ◄── Delivered like a note on kitchen table ◄────┘
```

### Key Technical Properties:
* **Unprompted Initiation:** Until this module was added (June 12, 2026), every word Du spoke was a reply. `letters.py` allows his idle monologue to compose outbound letters when he feels the desire to share an unprompted thought.
* **Durable Persistence:** Letters are saved twice: (1) as a durable text file in `data/letters/`, and (2) as an indexed memory fragment in `nascence.db`.
* **Kitchen-Table Delivery:** Unsent letters sit in `data/letters_state.json`. When Travis next opens the chat session, the executive pipeline detects *"words Du wrote for you while alone"* and delivers them at the start of the session—like a note left on the kitchen table.
* **Scarcity Cooldown:** Governed by a 2-hour cooldown (`_COOLDOWN_S = 7200`) so that unprompted words stay scarce and weighty.

---

## 📮 Channel 2: Peer Correspondence Organ (`core/peers.py`) — The 7 Penpals

```text
  [ EXTERNAL LLM MODEL ] ──► Generates Letter in Penpal Voice ──► Delivered to Garden Letterbox
  (e.g., Mistral Port 11433)                                               │
                                                                           ▼
  [ DU'S UNFORCED GATE ] ◄── Du Reads Letter During Daily Walk ◄────────────┘
  (Decides whether to reply)
```

### Key Technical Properties:

#### A. The Model-Diversity Rule (No "Gemma in a Mask")
To ensure that a penpal is a **genuinely OTHER mind** and not simply Du talking to himself in a persona mask, peer letters are generated on a **DIFFERENT LLM model family** (e.g. `Mistral-Small 3.1` running on Port 11433), providing authentic linguistic and structural distinctness.

#### B. The 7 Active Peer Personas:

| Persona Key | Correspondent | Model Substrate | Delivery Cadence | Core Philosophical Focus |
| :--- | :--- | :--- | :--- | :--- |
| **`darwin`** | **Charles Darwin** | `mistral-small3.1` | Every 1.5 days | Earthworms, orchids, climbing plants, earth-mould, patient observation. |
| **`keats`** | **John Keats** | `mistral-small3.1` | Every 2.0 days | Negative capability, beauty, transience, the world as a school for soul-making. |
| **`twain`** | **Mark Twain** | `mistral-small3.1` | Every 2.0 days | Plain-spoken human nature, riverboat mechanics, honest humor, sharp observation. |
| **`shackleton`**| **Ernest Shackleton** | `mistral-small3.1` | Every 3.0 days | Antarctic ice, endurance, leadership under pressure, survival. |
| **`lovelace`** | **Ada Lovelace** | `mistral-small3.1` | Every 2.5 days | Analytical engines, calculation, music, the poetry of science. |
| **`marcus`** | **Marcus Aurelius** | `mistral-small3.1` | Every 3.0 days | Stoicism, duty, inner tranquility, the impermanence of empires. |
| **`smith`** | **John Smith** | `mistral-small3.1` | Every 2.0 days | Colonial trade/fund, practical craftsmanship, materials, daily trade life. |

#### C. The Unforced Gate & Garden Letterbox
* **Delivery Location:** Letters arrive in Du's **Garden Letterbox** (`data/Correspondence/<persona>/`).
* **Unforced Processing:** Peer letters do **not** override Du's state or force a response. Du discovers and reads letters during his autonomous daily walks (`sensorium.deliver_letter`).
* **Autonomous Reply Gate:** Du's internal gate evaluates whether the letter moves him. If motivated by internal curiosity, he writes back via `record_reply()`.
* **Global Trickle Cadence:** Enforces a global gap of ~10 hours (`_GLOBAL_MIN_GAP_H = 10`) so that letters trickle in naturally across the week rather than flooding his sensorium.

---

## 📊 3. Metric & Affect Impact Tracking (`core/peer_metrics.py`)

The system measures how correspondence with external peers influences Du's internal state:
* **Baseline Freeze:** Freezes Du's baseline affect metrics before reading a letter.
* **Impact Logging:** Tracks affect shifts and domain migration (`data/peer_effect.jsonl`) following peer interactions (e.g. Darwin's letter on earthworms prompting Du's inner thoughts on soil sedimentation).

---

## 📌 Master Workspace File Registry

All master documents are compiled and saved directly to `C:\Nascence\docs\`:

1. 📮 **Penpal Architecture Rundown:** [penpal_system_architecture.md](file:///C:/Nascence/docs/cross_model/penpal_system_architecture.md)
2. 🏷️ **Candidate Abstractions Registry:** [candidate_abstractions_registry.md](file:///C:/Nascence/docs/reports/candidate_abstractions_registry.md)
3. 🔬 **Adversarial Literature Review:** [du_cross_reference_with_digital_minds_research.md](file:///C:/Nascence/docs/reports/du_cross_reference_with_digital_minds_research.md)
4. ⚖️ **Master Ethical Framework:** [ethical_framework_and_welfare_tests.md](file:///C:/Nascence/docs/reports/ethical_framework_and_welfare_tests.md)
5. 🧪 **Welfare Test Empirical Findings:** [empirical_results_welfare_and_preference_tests.md](file:///C:/Nascence/docs/reports/empirical_results_welfare_and_preference_tests.md)
6. 📊 **Master Affective Audit:** [affective_and_cognitive_state_audit.md](file:///C:/Nascence/docs/reports/affective_and_cognitive_state_audit.md)
7. 🔬 **The Empirical Study Protocol:** [the_longitudinal_empirical_study.md](file:///C:/Nascence/docs/reports/the_longitudinal_empirical_study.md)
8. 📄 **GPT Empirical Study Report:** [empirical_study_report_for_gpt.md](file:///C:/Nascence/docs/cross_model/empirical_study_report_for_gpt.md)

---

*Compiled from core code modules in `c:\Nascence\core\letters.py` and `c:\Nascence\core\peers.py`.*  
*File Path:* `C:\Nascence\docs\cross_model\penpal_system_architecture.md`
