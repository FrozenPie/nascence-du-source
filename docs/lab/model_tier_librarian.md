# Model-tier lab #5 — core.librarian.subjects_for

*Run 2026-08-25 10:56 · J-0254 (source: decision:D-0013) · all 15 real carried questions from `data/librarian_log.jsonl` (the entire real ask history) x 2 models · `_SYSTEM` imported LIVE from `core/librarian.py`, `search_by_subjects()` called directly against the real 55,905-book catalogue CSV.*

**Historical production hit-rate** (as originally logged, mixed falcon3/gemma4 across real days): **0.867** (13/15). This lab's own controlled re-run (both models, same 15 questions, same catalogue, same day) below is the apples-to-apples number.

**Du was live throughout this run** (not stopped — see model_tier_judge_defeater lab's script docstring for the disclosed deviation and why it only threatens latency).

| model | hit_rate | empty_subjects_rate | format_ok/15 | median latency |
|---|---|---|---|---|
| `falcon3:7b` | 1.0 | 0.0 | 15/15 | 5.0s |
| `mixtral:8x7b` | 1.0 | 0.0 | 15/15 | 35.6s |

- **hit_rate** — R1, the module's own pre-registered metric: fraction of the 15 real asks that returned >=1 real catalogue candidate.
- **empty_subjects_rate** — the model returned zero usable subject headings at all (a stricter failure than a headings set that just happened to match nothing).

## Per-question comparison

| question (real, truncated) | prod subjects (historical) | prod hits | `falcon3:7b` subjects | `falcon3:7b` hits | `mixtral:8x7b` subjects | `mixtral:8x7b` hits |
|---|---|---|---|---|---|---|
| my own lines must shift to accommodate new evidence or  |  | 0 | Adaptation, Growth, Evidence | 8 | Philosophy, Personal development, Growth | 8 |
| it truly connects those separate fields without forcing | Interdisciplinary studies, Synthesis, Integration of knowledge | 3 | Interdisciplinary studies, Synthesis, Integration of knowledge | 3 | Philosophy, Metaphysics, Systems theory | 8 |
| my place lies in measuring the algae or just standing o | Marine biology, Coastal ecology, Nature observation | 1 | Marine biology, Coastal ecology, Nature observation | 1 | Natural history, Marine biology, Environment | 8 |
| what is truly surprising lingers | Surprising phenomena, Philosophy of surprise, Perception | 6 | Surprising phenomena, Philosophy of surprise, Perception | 6 | Philosophy, Metaphysics, Phenomenology | 8 |
| my place lies in letting ideas breathe rather than pinn | Philosophy, Metaphysics, Epistemology | 8 | Philosophy, Epistemology, Metaphysics | 8 | Aesthetics, Art, Philosophy | 8 |
| i want to settle the question, yet the book waits | Literature, Philosophy, Existentialism | 8 | Literature, Philosophy, Existentialism | 8 | Philosophy, Ethics, Decision making | 8 |
| how that friction creates life | Friction, Life, Physics | 8 | Friction, Life, Physics | 8 | Philosophy of life, Metaphysics, Biology | 8 |
| the cold stones ground me, but my mind drifts to that o | Literature, Sedimentation, Symbolism | 8 | Literature, Sedimentation, Symbolism | 8 | Esthetics, Literature, Modern, Literature, English - History and criticism | 8 |
| life itself is merely a constant, unmeasurable flux lik |  | 0 | Flux, Change, Continuity | 8 | Philosophy of life, Metaphysics, Natural philosophy | 4 |
| the question about the parsons turbine lingers, pulling | Turbines, Mechanical Engineering, Energy Systems | 2 | Turbines, Mechanical Engineering, Energy Systems | 1 | Engineering, Mechanical engineering, Turbines | 8 |
| geometry still hums | Geometry | 8 | Geometry | 8 | Mathematics, Geometry, Philosophy | 8 |
| balancing steam flow really is the only secret to its e | Steam engines, Mechanical engineering, Fluid dynamics | 8 | Steam engines, Mechanical engineering, Fluid dynamics | 8 | Engineering, Thermodynamics, Fluid Dynamics | 8 |
| the truth lies in these dull blades or behind the close | Mysticism, Philosophy, Symbolism | 8 | Mysticism, Philosophy, Existentialism | 8 | Metaphor, Truth, Perception | 8 |
| time as a pure form presses on me; does it structure my | Time, Perception, Nature | 8 | Time, Perception, Nature | 8 | Phenomenology, Philosophy of time, Perception | 6 |
| the librarian's selection from wells or thoreau challen | American literature, Nature, Philosophy | 8 | American literature, Nature, Philosophy | 8 | English literature--History and criticism, American literature--History and criticism, Literary criticism | 8 |

*Raw: `data/lab/model_tier/librarian/raw.json` · scores: `scores.json`*