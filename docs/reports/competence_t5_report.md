# 🧠 Architectural Deep-Dive: The Role of competence.py (T5)

> **Source Module:** `c:\Nascence\core\competence.py`  
> **Date of Audit:** August 10, 2026  

---

## ❓ Core Question: Identity Revision Evaluation vs. Arithmetic/Logical Skills?

**Answer:** `competence.py` (T5) evaluates **arithmetic, logical, and domain capabilities**, NOT the identity revision itself!


### The Clear Separation of Responsibilities:

1. **Identity Revision Evaluation:** Handled by **`provisional_identity.py`** and **`commitment_ledger.py`**. Over a 72-hour probation window, identity revisions are tested to see if they reduce theme contradiction-recurrence.

2. **`competence.py` (T5):** A metacognitive self-efficacy model that measures **prediction error ($|\text{Expected} - \text{Observed}|$)** across domain skills (`mathematics`, `logic`, `philosophy`, `history`, `natural_science`).


```
                     [ Turn / Exercise Cycle ]
                                │
                                ▼
         ┌──────────────────────────────────────────────┐
         │ 1. DOMAIN CLASSIFIER (Cosine Anchor Match)   │
         │ (Classifies: math, logic, science, etc.)     │
         └──────────────────────┬───────────────────────┘
                                │
                                ▼
         ┌──────────────────────────────────────────────┐
         │ 2. THREE-AXIS OUTCOME MEASUREMENT            │
         │ • Signal A: Scene Coherence / Bind          │
         │ • Signal B: External Drill Accuracy          │
         │ • Signal C: Human Correction / Uptake       │
         └──────────────────────┬───────────────────────┘
                                │
                                ▼
         ┌──────────────────────────────────────────────┐
         │ 3. PREDICTION ERROR & SURPRISE CALCULATION   │
         │ Surprise = |Expected Confidence - Outcome|   │
         └──────────────────────┬───────────────────────┘
                                │
                                ▼
         ┌──────────────────────────────────────────────┐
         │ 4. CLIMATE ENGINE FEEDBACK                   │
         │ (Decayed surprise feeds psychological weather│
         │  in data/capability_beliefs.json)            │
         └──────────────────────────────────────────────┘
```

---

## 🔬 1. The 3 Competence Signals Explained


### Signal A: Introspective Scene Coherence (Fluency)

Measured after every substantive turn:

$$\text{Outcome} = \text{Scene Coherence} - (0.05 \times \text{Introspective Passes})$$

If Du engages in math or logic and the introspective scene binds with low struggle, fluency confidence increases.


### Signal B: External Drill Accuracy (Math & Skill Drills)

Evaluates objective performance on idle arithmetic and logic drills (`record_drill_accuracy`). It tracks **calibration error** (gap between felt confidence vs. measured accuracy) to expose over-confidence.


### Signal C: Human Correction Feedback

A negative feedback cue. If the user corrects Du's prior logic/math answer on the next turn, T5 docks fluency confidence in that domain.


---

## 🟢 Conclusion

Identity durability is evaluated by `provisional_identity.py`, while `competence.py` (T5) tracks Du's evolving self-efficacy, math/logic drill accuracy, and prediction error!