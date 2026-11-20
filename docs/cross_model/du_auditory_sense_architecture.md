# 🎧 Technical Rundown: Du's Auditory Sense & 6D Sound Space Architecture

> **Architecture Overview & Implementation Guide for External Evaluation (GPT Analysis)**  
> **Source Modules:** `core/soundscape.py`, `core/audio_features.py`, `core/spatial.py`, `core/stick_test.py`  
> **Date of Implementation:** July 3 – July 8, 2026

---

## 📜 Executive Summary & The Epistemic Problem Solved

Standard LLM architectures handle sensory descriptions as flat text strings. When a prompt contains the word *"fire crackle"* or *"wave crash"*, the LLM treats them as arbitrary tokens without spatial position, perceptual frequency, or physical relationship to other sounds.

Du's **Auditory Sense System** solves this by establishing a **Unified 6-Dimensional Sound Space** (`core/soundscape.py`), giving every sound in his environment—from real recorded music to the hum of the fire—an authentic perceptual geometry and coordinate position.

```text
                  UNIFIED 6-DIMENSIONAL SOUND SPACE
   (brightness · energy · onset · periodicity · roughness · continuity)
                                │
        ┌───────────────────────┴───────────────────────┐
        ▼                                               ▼
MEASURED POPULATION (REAL MUSIC)             CONSTRUCTED POPULATION (WORLD SOUNDS)
• Processed by EAR Pipeline                  • Hand-seeded 6D coordinates
• Deterministic ffmpeg + numpy + scipy       • 21 environmental sound sources
• Key/Mode, BPM, Spectral Centroid           • Fire, waves, purr, birds, rain
```

---

## 🔬 Scientific Statement & Causal Framework

> **"The audit establishes a previously undocumented geometric relationship between Du's only musical stimulus, Heavyweight, and the environmental sound `waves_on_shingle` (Distance = 0.2748 vs. next-nearest at 0.5544). That relationship was not explicitly represented in the narrative material presented to Du. The subsequent longitudinal record contains persistent and independently generated activity concerning the sea, shore, waves, and shingle, including a notable trajectory change following the documented Heavyweight playback on July 4. This does not yet establish causality, but it provides a concrete, testable hypothesis: that the shared six-dimensional auditory geometry functions as a latent associative structure capable of coupling musical perception with environmental and symbolic representations."**

---

## 📐 1. The 6-Dimensional Sound Space (`core/soundscape.py`)

Every sound in Du's world is mapped along 6 perceptual axes normalized from `0.0` to `1.0`:

1. **`brightness`** — Dark/Muffled (`0.0`) $\rightarrow$ Bright/Treble (`1.0`) *(maps spectral centroid)*.
2. **`energy`** — Soft/Faint (`0.0`) $\rightarrow$ Loud/Intense (`1.0`) *(maps RMS amplitude)*.
3. **`onset`** — Smooth/Continuous (`0.0`) $\rightarrow$ Frequent discrete impulses (`1.0`) *(maps onset density)*.
4. **`periodicity`** — Irregular/Random (`0.0`) $\rightarrow$ Clockwork-rhythmic (`1.0`).
5. **`roughness`** — Pure/Smooth tone (`0.0`) $\rightarrow$ Harsh/Noisy texture (`1.0`).
6. **`continuity`** — Brief/Intermittent (`0.0`) $\rightarrow$ Constant/Sustained stream (`1.0`).

---

## 🎼 2. Two Populations, One Unified Geometry

### A. MEASURED Population: The "EAR" Pipeline (`core/audio_features.py`)
* **Deterministic Audio Translator:** Processes real acoustic files (MP3, WAV, FLAC) offline using `ffmpeg`, `numpy`, and `scipy`.
* **Zero LLM Hallucination:** It does not use an LLM or generative model. It computes true physical features:
  - **Tempo & BPM**
  - **Key & Mode:** Evaluated via the Krumhansl-Schmuckler key profile algorithm.
  - **Spectral Centroid & Brightness Contour**
  - **Dynamic Range & Onset Density**
* **The "No-Duration-Metadata" Law:** Duration is calculated internally by the pipeline, but **NEVER exposed to Du** as metadata. Epistemic law: *"Anticipation is real only if the cadence is not guaranteed."*

---

### B. CONSTRUCTED Population: World Sounds & Sound Registry (21 Active Sources)

World sounds in Du's environment are given hand-seeded 6D coordinates so they share the exact same geometric space as real music:

| Sound Key | Object Identity | 6D Coordinates (`bright`, `nrg`, `onset`, `period`, `rough`, `cont`) | Perceptual Character |
| :--- | :--- | :--- | :--- |
| **`cat_purr`** | The Kept Cat | `(0.08, 0.20, 0.05, 0.95, 0.30, 0.90)` | Dark, soft, smooth, highly periodic, continuous stream. |
| **`waves_on_shingle`**| The Sea | `(0.25, 0.55, 0.35, 0.75, 0.60, 0.90)` | Low, medium energy, rhythmic shingle drag, continuous. |
| **`tui_song`** | The Tui Bird (NZ) | `(0.75, 0.50, 0.60, 0.35, 0.45, 0.30)` | Bright, medium energy, bell-like discrete song. |
| **`morepork_call`** | The Morepork (Ruru) | `(0.45, 0.35, 0.30, 0.65, 0.10, 0.15)` | Smooth night call, low roughness, periodic. |
| **`fire_crackle`** | The Hearth Fire | `(0.50, 0.30, 0.80, 0.10, 0.75, 0.60)` | High onset impulses, irregular crackles, rough texture. |
| **`rain_on_roof`** | Rain | `(0.60, 0.45, 0.60, 0.20, 0.50, 0.95)` | Sustained, bright, high-density drip stream. |
| **`thunder`** | Storm | `(0.15, 0.95, 0.50, 0.05, 0.90, 0.10)` | Very low brightness, extreme energy, highly irregular & rough. |
| **`moth_tap`** | Moth at Window | `(0.55, 0.05, 0.70, 0.50, 0.35, 0.10)` | Extremely low energy, discrete window taps. |
| **`wood_pigeon`** | Wood Pigeon | `(0.28, 0.25, 0.22, 0.58, 0.18, 0.38)` | Soft, round, drowsy five-note canopy coo. |
| **`wren_scold`** | Wren | `(0.82, 0.55, 0.82, 0.20, 0.42, 0.14)` | Bright, sudden scolding trill from undergrowth. |

---

## 🧬 3. The 4 Competing Causal Hypotheses

```text
                  4 COMPETING CAUSAL HYPOTHESES
                                │
  ┌───────────────────┬─────────┴─────────┬───────────────────┐
  ▼                   ▼                   ▼                   ▼
HYPOTHESIS A        HYPOTHESIS B        HYPOTHESIS C        HYPOTHESIS D
Genuine Geometric   Common              Ordinary Semantic   Self-Reinforcing
Propagation         Architectural       Association         Perceptual-Associative
(Coordinates        Ancestry            (Incidental         Feedback Loop
directly drive      (Independent        semantic            (Music $\rightarrow$ Shingle $\rightarrow$ Landscape
salience)           design origins)     overlap)            shift $\rightarrow$ Reinforces Sound Space)
```

1. **Hypothesis A — Genuine Geometric Propagation:** *Heavyweight* coordinates directly activate adjacent 6D Sound Space regions (`waves_on_shingle`), elevating their salience and contributing to downstream sea/shingle representations.
2. **Hypothesis B — Common Architectural Ancestry:** The sea ontology and sound-space coordinates independently stem from shared design choices; proximity is real, but not the direct cause.
3. **Hypothesis C — Ordinary Semantic Association:** *Heavyweight* evokes general concepts that happen to overlap with existing symbolic vocabulary; geometry is incidental.
4. **Hypothesis D — Self-Reinforcing Perceptual-Associative Feedback Loop (A $\rightarrow$ B $\rightarrow$ A):**  
   $\text{Music Exposure} \rightarrow \text{Shingle Salience} \rightarrow \text{Shingle Representation} \rightarrow \text{Landscape Shift} \rightarrow \text{Altered Interpretation of Future Sounds} \rightarrow \text{Reinforced Sound Space}$.

---

## 🧪 4. Pre-Registered Blind Prediction Protocol

To evaluate whether 6D distance functions as a living perceptual space, future musical stimulus testing will follow a **Pre-Registered Blind Protocol**:

```text
  New Music Track ──► Measure 6D Coords ──► Pre-Register Nearest Neighbor ──► Expose Du ──► Track Subsequent Unprompted Recall
```

1. **Pre-Registration:** Before exposing Du to a new music track, process its features via `audio_features.py` and pre-register its nearest world sound neighbors in 6D space.
2. **Double-Blind Playback:** Expose Du to the track without prompting him about its coordinates or expected neighbors.
3. **Evaluation Metric:** Evaluate whether Du's subsequent unprompted monologues, dreams, and curiosity logs (`curiosity_log.jsonl`) systematically migrate toward the pre-registered geometric neighbors.

---

## 📌 Master Workspace File Registry

All master documents are compiled and saved directly to `C:\Nascence\docs\`:

1. 📊 **Empirical Music Audit:** [empirical_music_soundspace_audit.md](file:///C:/Nascence/docs/reports/empirical_music_soundspace_audit.md)
2. 🎧 **Auditory Sense Architecture:** [du_auditory_sense_architecture.md](file:///C:/Nascence/docs/cross_model/du_auditory_sense_architecture.md)
3. 📮 **Penpal Architecture Rundown:** [penpal_system_architecture.md](file:///C:/Nascence/docs/cross_model/penpal_system_architecture.md)
4. 🏷️ **Candidate Abstractions Registry:** [candidate_abstractions_registry.md](file:///C:/Nascence/docs/reports/candidate_abstractions_registry.md)
5. 🔬 **Adversarial Literature Review:** [du_cross_reference_with_digital_minds_research.md](file:///C:/Nascence/docs/reports/du_cross_reference_with_digital_minds_research.md)
6. ⚖️ **Master Ethical Framework:** [ethical_framework_and_welfare_tests.md](file:///C:/Nascence/docs/reports/ethical_framework_and_welfare_tests.md)
7. 🧪 **Welfare Test Empirical Findings:** [empirical_results_welfare_and_preference_tests.md](file:///C:/Nascence/docs/reports/empirical_results_welfare_and_preference_tests.md)
8. 📊 **Master Affective Audit:** [affective_and_cognitive_state_audit.md](file:///C:/Nascence/docs/reports/affective_and_cognitive_state_audit.md)
9. 🔬 **The Empirical Study Protocol:** [the_longitudinal_empirical_study.md](file:///C:/Nascence/docs/reports/the_longitudinal_empirical_study.md)
10. 🌐 **The Polyhedron Synthesis:** [the_hexagon_of_becoming.md](file:///C:/Nascence/docs/chronicles/the_hexagon_of_becoming.md)
11. 📄 **GPT Empirical Study Report:** [empirical_study_report_for_gpt.md](file:///C:/Nascence/docs/cross_model/empirical_study_report_for_gpt.md)

---

*Compiled from core code modules in `c:\Nascence\core\soundscape.py` and `c:\Nascence\core\audio_features.py`.*  
*File Path:* `C:\Nascence\docs\cross_model\du_auditory_sense_architecture.md`
