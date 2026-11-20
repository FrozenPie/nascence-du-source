"""
koopman_mood_forecast.py — Trial 6 of docs/staged/udms_du_capability_trials.md (J-0322)
==========================================================================================
"Where is this mood heading" — a question nothing in Du produces today (mood.py, opponent_process.py,
sleep_pressure.py are all reactive). UDMS's Koopman/DMD machinery is the one lens in the corpus with
genuine out-of-sample validation (catalog: "the real thing, not name-dropping"); this session's own
first-pass runs already found the 87.8% tensor-residual-reduction number IS computed (correcting an
earlier survey note). What it has never had: a fight against classical baselines or the affect
question specifically.

Fits KoopmanStandard + VARBaseline + KalmanBaseline (all imported from UDMS's baseline_models.py,
not reimplemented) plus a plain persistence baseline on data/affect_log.jsonl's 8D affect vector,
forecasts k in {1, 5, 10, 25} steps ahead, compares MSE. Helpful bar (per the plan): Koopman beats
persistence AND at least one classical baseline at k>=5 with a real margin.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(r"C:\UDMS")))
from core.udms.baseline_models import VARBaseline, KalmanBaseline, KoopmanStandard  # noqa: E402

DATA = Path(__file__).parent.parent / "data" / "affect_log.jsonl"
AFFECT_KEYS = ("joy", "fear", "anger", "trust", "surprise", "disgust", "valence", "arousal")
TRAIN_FRAC = 0.70
HORIZONS = (1, 5, 10, 25)


def load_matrix() -> np.ndarray:
    rows = []
    with open(DATA, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    rows.sort(key=lambda r: r.get("ts", 0.0))
    aff = [r.get("affect") or {} for r in rows]
    return np.array([[a.get(k, 0.0) for k in AFFECT_KEYS] for a in aff])


def mse_at_horizon(predict_fn, X_test: np.ndarray, k: int) -> float:
    errs = []
    for i in range(len(X_test) - k):
        pred = predict_fn(X_test[i], k)
        actual = X_test[i + k]
        errs.append(float(np.mean((pred - actual) ** 2)))
    return float(np.mean(errs)) if errs else float("nan")


def main() -> None:
    X = load_matrix()
    n = len(X)
    split = int(n * TRAIN_FRAC)
    X_train, X_test = X[:split], X[split:]
    print(f"loaded {n} affect rows ({len(AFFECT_KEYS)}D); train={split} test={len(X_test)}")

    var_m = VARBaseline().fit(X_train)
    kal_m = KalmanBaseline(latent_dim=3).fit(X_train)
    koo_m = KoopmanStandard(n_observables=15).fit(X_train)

    models = {
        "persistence": lambda x0, k: x0,
        "VAR":         lambda x0, k: var_m.predict_k(x0, k),
        "Kalman":      lambda x0, k: kal_m.predict_k(x0, k),
        "Koopman":     lambda x0, k: koo_m.predict_k(x0, k),
    }

    results = {name: {} for name in models}
    for k in HORIZONS:
        for name, fn in models.items():
            results[name][k] = mse_at_horizon(fn, X_test, k)

    print(f"\n{'model':12s}" + "".join(f"  k={k:<6d}" for k in HORIZONS))
    for name in models:
        row = "".join(f"  {results[name][k]:8.5f}" for k in HORIZONS)
        print(f"{name:12s}{row}")

    print("\nKoopman vs persistence and best classical baseline, per horizon:")
    for k in HORIZONS:
        koo = results["Koopman"][k]
        pers = results["persistence"][k]
        best_classical = min(results["VAR"][k], results["Kalman"][k])
        beats_persistence = koo < pers
        beats_classical = koo < best_classical
        verdict = "BEATS BOTH" if (beats_persistence and beats_classical) else \
                  ("beats persistence only" if beats_persistence else
                   ("beats classical only" if beats_classical else "loses to both"))
        print(f"  k={k:3d}: Koopman={koo:.5f}  persistence={pers:.5f}  best_classical={best_classical:.5f}  -> {verdict}")


if __name__ == "__main__":
    main()
