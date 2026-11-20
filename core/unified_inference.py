"""
Nascence — Unified Inference Gate (Phase 4, scaffold · DISABLED by design)

THE GOVERNANCE RULE: MEASURE FIRST, UNIFY LATER. The architecture runs several distinct
psychological "currencies" — contradiction pressure (the tension ledger), climate dissonance,
social prediction error, world-model strain. The Active Inference literature is seductive: it
says these are all forms of one quantity (prediction error / free energy) and could be merged
into a single equation. They might be. But merging currencies that are NOT in fact correlated
manufactures a false unity and produces the unstable, hard-to-debug feedback loops that the AIF
literature explicitly warns about.

So this gate is built but INERT. It computes, every cycle, the unified scalar it WOULD act on —
a free-energy-style combination of the normalised currencies — and logs it next to the live
correlation telemetry (Phase 3). It changes NO behaviour. It will only ever act on a pair of
currencies once `scripts/measure_correlations.py` has shown, over 100+ turns, a Pearson R above
the activation threshold (0.85) for that specific pair. Until then `active_pairs` is empty and the
gate is a pure observer — exactly as Phase 4 of the plan specifies ("TBD based on Phase 3 results").

This file is therefore the *mechanism* for unification, deliberately decoupled from the *decision*
to unify. Turning it on is a data-driven act (set ENABLE_UNIFIED_INFERENCE and list the proven
pairs), not a code change to the cognition.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

logger = logging.getLogger("nascence.unified_inference")

# --- The master switch. False = pure observer (logs the scalar, touches nothing). -----------
# Flip to True ONLY after Phase 3 telemetry proves a correlation pair clears _ACTIVATION_R.
ENABLE_UNIFIED_INFERENCE = False

# Correlation strength a currency PAIR must clear (in measure_correlations.py output) before it
# may be merged. The plan's hard gate. A pair below this stays separate — no exceptions.
_ACTIVATION_R = 0.85

# Currency pairs eligible for unification once proven. Empty until the data licenses one.
# Format: ("currency_a", "currency_b"). measure_correlations.py reports R for these names.
_ACTIVE_PAIRS: list[tuple[str, str]] = []

# Free-energy weights — how each normalised currency contributes to the unified scalar. These
# are the values to fine-tune once the gate is live; until then the scalar is observe-only so the
# weights cost nothing. All currencies are pre-normalised to [0,1] by the caller.
_WEIGHTS = {
    "contradiction_pressure": 0.35,
    "dissonance":             0.25,
    "world_model_strain":     0.25,
    "delta_social":           0.15,
}

_UNIFIED_LOG = Path(__file__).parent.parent / "data" / "unified_inference_log.jsonl"


class UnifiedInferenceGate:
    """
    Observe-only free-energy aggregator. Each cycle it folds the live currencies into one scalar
    (`free_energy`) and logs it. When ENABLE_UNIFIED_INFERENCE is True AND a currency pair has been
    proven correlated (listed in _ACTIVE_PAIRS), it would expose a unified modulation for that pair;
    until then `modulation()` returns None and nothing downstream is touched.
    """

    def __init__(self):
        self.enabled = ENABLE_UNIFIED_INFERENCE
        self.active_pairs = list(_ACTIVE_PAIRS)
        if self.enabled and self.active_pairs:
            logger.info("[unified] ACTIVE — unifying pairs: %s", self.active_pairs)
        else:
            logger.info("[unified] observe-only (measure-first; no proven pairs)")

    @staticmethod
    def _free_energy(currencies: dict) -> float:
        """Weighted sum of the normalised currencies — the single scalar the unified view WOULD
        minimise. Pure arithmetic; bounded to [0,1] by the weights summing to 1.0."""
        total = 0.0
        for name, w in _WEIGHTS.items():
            total += w * max(0.0, min(1.0, float(currencies.get(name, 0.0))))
        return round(total, 4)

    def observe(self, state, currencies: dict) -> float:
        """
        Compute and log the unified free-energy scalar for this cycle. Returns the scalar but —
        in observe-only mode — feeds nothing back into cognition. Never raises into the cycle.
        """
        fe = 0.0
        try:
            fe = self._free_energy(currencies)
            record = {
                "ts":          time.time(),
                "cycle_id":    getattr(state, "cycle_id", ""),
                "free_energy": fe,
                "currencies":  {k: round(float(v), 4) for k, v in currencies.items()},
                "enabled":     self.enabled,
                "active_pairs": ["+".join(p) for p in self.active_pairs],
            }
            _UNIFIED_LOG.parent.mkdir(parents=True, exist_ok=True)
            with open(_UNIFIED_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception as exc:
            logger.debug("[unified] observe failed (non-fatal): %s", exc)
        return fe

