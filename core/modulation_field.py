"""
Nascence — The Modulation Field (one damped, coupled field for the modulation layer)
====================================================================================
See docs/modulation_field_plan.md. Endogenous faculty springs (W) + exogenous world/body forces (u) +
strong damping (D), integrated as a damped coupled dynamical system:

    dx = -D·(x - baseline) + W·x + u ;   x ← clip(x + dt·dx)

Damping-dominated and acyclic in the dangerous direction → stable (proven numerically: all eigenvalues of
A = -D + W have negative real part, so any perturbation decays back to baseline — no runaway, no coupling-
layer monoculture). Observe-only: the field computes its state; read paths into behaviour are licensed one
at a time (burst_willingness first, gated). Zero LLM, cheap enough to tick like the climate engine.
"""
from __future__ import annotations

import numpy as np

NODES = ["arousal", "valence", "tension", "fatigue", "novelty",
         "curiosity_drive", "burst_willingness", "pull_seeker", "pull_self"]
IDX = {n: i for i, n in enumerate(NODES)}
N = len(NODES)

# Resting baselines (arousal rests calm-but-awake, like AffectState; the rest rest at 0).
BASELINE = np.zeros(N)
BASELINE[IDX["arousal"]] = 0.30

# Per-node relaxation rate (the damper — the dominant force). Novelty fades fast (fleeting);
# fatigue lingers; the rest relax at a steady ~0.3.
DAMP = np.full(N, 0.30)
DAMP[IDX["novelty"]] = 0.50
DAMP[IDX["fatigue"]] = 0.12

# Endogenous springs: (target ← source, weight). Weak (≪ damping). NOTHING feeds back into `novelty`
# (it is event/exogenous-driven only) → no novelty→curiosity→novelty runaway.
COUPLINGS = [
    ("curiosity_drive",   "novelty",          0.20),   # novelty stirs curiosity
    ("arousal",           "novelty",          0.10),   # novelty activates
    ("valence",           "novelty",          0.06),   # novelty is mildly pleasant (interest)
    ("pull_seeker",       "curiosity_drive",  0.15),   # curiosity pulls outward
    ("burst_willingness", "curiosity_drive",  0.15),   # curious → want to pursue (burst)
    ("burst_willingness", "arousal",          0.10),   # activated → more push
    ("burst_willingness", "fatigue",         -0.20),   # tired → less push
    ("pull_seeker",       "valence",          0.08),   # good mood → outward
    ("pull_self",         "valence",         -0.10),   # low mood → inward
    ("arousal",           "tension",          0.10),   # tension activates
    ("pull_self",         "tension",          0.06),   # tension → guarded/inward
]


def _W() -> np.ndarray:
    W = np.zeros((N, N))
    for tgt, src, w in COUPLINGS:
        W[IDX[tgt], IDX[src]] += w
    return W


W = _W()
_LO, _HI = -1.0, 1.0


class ModulationField:
    def __init__(self):
        self.x = BASELINE.copy()

    def step(self, dt: float = 1.0, exogenous: dict | None = None) -> None:
        u = np.zeros(N)
        if exogenous:
            for k, v in exogenous.items():
                if k in IDX:
                    u[IDX[k]] += float(v)
        dx = -DAMP * (self.x - BASELINE) + W @ self.x + u
        self.x = np.clip(self.x + dt * dx, _LO, _HI)

    def perturb(self, node: str, amount: float) -> None:
        self.x[IDX[node]] = float(np.clip(self.x[IDX[node]] + amount, _LO, _HI))

    def get(self, node: str) -> float:
        return float(self.x[IDX[node]])

    def state(self) -> dict:
        return {n: round(float(self.x[i]), 3) for i, n in enumerate(NODES)}


def stability() -> dict:
    """Continuous-time linear stability of A = -D + W: stable iff every eigenvalue has negative real
    part (perturbations decay). This is the numerical proof the field cannot run away."""
    A = -np.diag(DAMP) + W
    eig = np.linalg.eigvals(A)
    max_real = float(max(e.real for e in eig))
    return {"max_real_eig": round(max_real, 4), "stable": max_real < 0,
            "eigs": [round(float(e.real), 3) for e in sorted(eig, key=lambda z: z.real)]}
