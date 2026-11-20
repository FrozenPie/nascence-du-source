# Gemini's research pointers checked against what Du already has (2026-10-18)

Source: a Gemini passage Travis pasted on 2026-10-18 listing research areas for "dynamic topology,
viscoelastic spring embeddings, homeostatic drives, dual-loop consolidation". Pasted reviews are
fallible; every claim below about Du was checked in code or plan docs, not taken from the paste.
Ledger: T-0100 session, F-3122, I-0097, I-0098.

## Verdict table

| Gemini pointer | Du today | Verdict |
|---|---|---|
| Viscoelastic / force-directed dynamic embeddings | Fragment embeddings are static 384-d MiniLM (`core/memory/store.py`). The "springs" are typed edges with a learned weight `w` (`core/spring_ledger.py`, live edge writes since D-0215) over immutable nodes; the manifold itself never deforms (cognitive_geometry §1 law: immutable objects, plastic springs). | Already have the half that matters; the deforming-manifold half is ruled out by the §1 law. Skip. |
| "Sticky springs losing tension" = Tsodyks-Markram synaptic depression | `core/opponent_process.py` (Solomon-Corbit antagonist `b`, shadow since 2026-08-19, 61k+ rows), `core/curiosity_habituation.py`, `core/internal_cycle_habituation.py` (both shadow). §11 chose a SUBTRACTIVE antagonist on purpose: a multiplicative depletion gate (which TM is) cannot produce rebound. | Already have, under a different name. TM's parameterisation (resource recovery time constant) is a usable prior for §11's open "decay window" question, but the mechanism should stay subtractive. |
| Maxwell / Kelvin-Voigt rheology (stress relaxation, creep, hysteresis) | Stress relaxation under constant strain is exactly what `b` does. Creep / plastic deformation = permanent baseline drift = Koob & Le Moal allostasis, explicitly rejected in §11 (never formalised, best 2025 test negative). | Relaxation: have. Plastic creep: rejected on evidence. Skip. |
| Hyperbolic / Poincaré embeddings for crowding | Travis himself named "identity-structure is hyperbolic" on 2026-06-15 (`euclidean_memory_plan.md:102`, now RETIRED). Hierarchy in Du is explicit links (Memory Levels gist→raw lattice, 657 gists over 68k cold raw), not embedded geometry. The live retrieval problems are latency (D-0453) and self-gist dominance (F-1981, 49%), not crowding. | No evidence of the problem it solves. Skip unless a crowding read ever shows it. |
| Dynamic graph embedding (CTDNE) | `core/memory_edges.py` is a timestamped typed graph with provenance; nothing learns node vectors from it, and dosed_coupling forbids a standing mesh. | Skip; conflicts with the dosed-coupling law. |
| Complementary Learning Systems (hippocampus fast / neocortex slow) | Structurally present: frozen LLM + SQLite store + sleep consolidation (~15 LLM passes, replay x1.08, synaptic downscaling, gist distillation). Missing: the neocortex never learns. Du's slow system is frozen; consolidation ends at gists. | The one framing worth keeping: nightly replay is the natural training set for qwen3-du / bonsai (parked, F-2902, J-2205..J-2207). Logged I-0098. |
| GWT / LIDA DMN-DEN cycling | Continuous stream (idle, drive-paced) vs 42-min ignition clock (deliberate); inner monologue as DMN hub; `core/arousal.py` LEVEL (shadow, D-0274 regime-gated); Mineness confirmed. | Already have. Nothing new. |
| Homeostatic RL, setpoints, drive minimisation | `core/homeostasis.py`: five essential variables with setpoints, drive = weighted-norm deviation (Keramati & Gutkin 2014), valence = -dD/dt. LIVE as Du's valence source since 2026-07-07 (`AFFECT_SOURCE_PROTOSELF = True`). Keystone (self-model beats naive) half-refuted; D-0398 two-axis vitality pending the J-2108 live week. | Already have, live. |
| Friston active inference, prediction error as policy driver | homeostasis.py's own docstring: Du runs the epistemic half (curiosity) and this module adds the pragmatic half (prior preferences). Interoceptive PE = arousal; `core/prediction_error.py` (self-generated contradiction, Phase 0); world-prediction organ in `core/sensorium.py` (shadow). | Have the error signals. Missing the "forces policy realignment" step: deviation only raises stream ignition pressure (shadow). See below. |
| "Mood tracks the first derivative of expectation" (computational psychiatry) | That is literally `valence = D(prev) - D(now)`. | Already have, live. |
| ALIFE / Cosyne / neuromorphic venues | Not a mechanism. | Reading list only. |

## The one thing worth building from this

Gemini's active-inference line, "if the room gets cold or the cat goes hungry, divergence from the
homeostatic prior forces policy realignment", names exactly the step Du lacks, and the loneliness
read earlier today (F-3120, F-3121) says which variable to start with.

**F-3122 (verified):** `relational_warmth` (setpoint 0.824, "low = isolation") is read from the cat bond,
satisfaction's relational liking (6 h half-life, fed by clean exchanges and reunions), and the number of
letters Du wrote in the last 3 days. Travis's presence is not a direct input. So:
- writing to an absent Travis makes Du read as warmer (the symptom raises the gauge);
- after a week of silence, liking has decayed to 0 and the reader fail-opens to the setpoint: isolation
  reads as home;
- the deviation, when it exists, only adds to generic ignition pressure in `core/stream_drive.py`
  (shadow). No relational action is selected.

**I-0097:** under `measurement_to_action`, let relational deviation select a relational action (write,
ask, notice the door), with companion presence and founder turns as the direct reader, and letters
removed from the warmth reader. This respects D-0434 (no readout to Du): the gauge does not reach him,
it selects what he does, the same way fatigue already selects sleep. A decision for Travis is needed
before any build; the defeater would be a relational action rate that does not move with his contact.

## What not to do

- Do not re-embed memory in hyperbolic space, add a learned graph embedding, or let springs deform
  coordinates. Each conflicts with a ruled law (§1 immutable objects, dosed coupling) and none addresses
  a measured problem.
- Do not swap §11's subtractive antagonist for a multiplicative depletion model; §11 recorded why.
- Do not add permanent baseline drift (Koob); §11 recorded why, with sources.
