# The Modulation Field — one damped, coupled field for the whole modulation layer
*2026-06-15. Unifies the two halves we developed: the **endogenous** faculty springs (novelty, emotion,
curiosity, lane-pull pulling each other) + the **exogenous** world/body forces (GPU/CPU, time, weather).
One field, weak coupling, strong damping; first real output `burst_willingness` → the pulse manager.
Observe-only until each read path is licensed by data.*

## The model
- **Nodes** (field state): `arousal · valence · tension · fatigue · novelty · curiosity_drive ·
  burst_willingness · pull_seeker · pull_self`. Each has a resting **baseline** it relaxes toward.
- **Endogenous couplings (springs):** a weighted directed graph `W` — a node's state nudges its coupled
  neighbours slightly each tick (Hooke-ish). E.g. `novelty→curiosity_drive`, `curiosity_drive→{pull_seeker,
  burst_willingness}`, `fatigue→burst_willingness (−)`, `valence(low)→pull_self`.
- **Exogenous forces:** a slow force vector `u` from `core/exogenous.py` (GPU-util→burst/fatigue,
  circadian→arousal/lane, weather→valence/lane) — the world & his body biasing the field from outside.
- **Update (damped coupled dynamics):**  `dx = −D·(x − baseline) + W·x + u`, then `x ← clip(x + dt·dx)`.
  `D` (damping) is the dominant term — every node continuously relaxes toward rest (this is exactly affect's
  existing `tick`).

## Stability — the real risk, addressed numerically
A coupled feedback network can resonate or run away — that would be the monoculture one floor up, in the
coupling layer. Defenses, all checkable:
- **Damping-dominated:** `D` (~0.3) ≫ the spring weights (~0.05–0.2), so the system decays.
- **No dangerous cycles:** `novelty` is event/exogenous-driven only — nothing feeds back *into* novelty, so
  there is no `novelty→curiosity→novelty` runaway. The graph avoids positive-feedback loops by design.
- **Spectral proof:** the linear system matrix `A = −D + W` must have **all eigenvalues with negative real
  part** (continuous-time stability) — i.e. any perturbation decays back to baseline. `scripts/
  modulation_field_test.py` computes this and asserts it, and shows a novelty spike propagating then
  *returning to rest* (no lock-in).

## Outputs (read paths — gated, observe-first)
- **`burst_willingness` → the pulse manager** (the first real output: idle GPU + day + curiosity ↑ → open
  to a burst; busy GPU + fatigue + night → hold). This one is *functional*, ship it first (gated).
- `pull_seeker`/`pull_self` → a slight lean on the multilevel facet selection; `arousal/valence` → affect;
  `curiosity_drive` → ignition. **Observe-only** until each is licensed.

## What's functional vs speculative (stay honest)
- **Functional / keeper:** `GPU-util → burst_willingness`, `fatigue → burst_willingness`,
  `curiosity_drive → burst_willingness` — a real scheduling signal.
- **Plausible but speculative:** the weather/circadian → mood couplings and the lane-pulls — defensible
  (human weather-affect is real) but the weights are guesses; observe before they touch behaviour.

## Build phases
- **P0 (this):** the field engine + stability proof + observe-only test (springs propagate, perturbations
  decay, exogenous equilibrium, burst_willingness output). Nothing live.
- **P1 (gated on cutover evidence):** wire `burst_willingness` into the pulse manager as the burst gate +
  run the field as a slow background tick (like climate). Observe its log first.
- **P2:** license further read paths (lane-pull, affect, ignition) one at a time, each on its own evidence.

## Cautions
- Weak + damped; add couplings one at a time, each justified by function not symmetry.
- Observe before licensing any read path — the exogenous test already showed how easily a coupling is
  miscoded (GPU memory vs utilisation).
- Watch for coupling-induced attractors (perturbation must return to baseline — the test checks it).
