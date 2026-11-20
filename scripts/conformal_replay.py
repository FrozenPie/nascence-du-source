"""
conformal_replay.py — Trial 8 of docs/staged/udms_du_capability_trials.md (J-0324)
====================================================================================
Offline replay of a real Du signal through UDMS's conformal calibration (ConformalCalibrator,
frozen split-conformal threshold) vs AdaptiveConformalInference (Gibbs & Candes online alpha
adaptation) — both imported, not reimplemented. Every number in conformal.py's self-tests so far
is synthetic; this is the first replay against Du's own data.

Signal chosen: core/affect_divergence.py's shadow log, |gap| (carried_valence - proto_valence) as
the nonconformity score — a continuous divergence magnitude with no existing hardcoded threshold
in the live code (unlike arousal's day/night-gated NIGHT_THRESHOLD), making it a clean subject for
"what would a calibrated threshold look like" rather than one this replay has to reconcile against
an existing rule.

Design: calibrate ONCE on an early prefix (the "nominal baseline"), then replay the rest
chronologically through (a) the frozen conformal threshold and (b) the adaptive online alpha —
bucket the flagged-rate into 10 equal chronological chunks and compare each against the 5% target.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(r"C:\UDMS")))
from core.udms.conformal import ConformalCalibrator, AdaptiveConformalInference  # noqa: E402

LOG = Path(__file__).parent.parent / "data" / "affect_divergence_shadow.jsonl"
ALPHA_TARGET = 0.05
CALIB_FRAC = 0.15   # first 15% of the log is the "nominal baseline" calibration prefix
N_CHUNKS = 10


def load_scores() -> list[float]:
    rows = []
    with open(LOG, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    rows.sort(key=lambda r: r.get("ts", 0.0))
    return [abs(float(r.get("gap", 0.0))) for r in rows]


def chunk_flag_rate(flags: list[bool], n_chunks: int) -> list[float]:
    n = len(flags)
    size = max(1, n // n_chunks)
    out = []
    for i in range(0, n, size):
        chunk = flags[i:i + size]
        if chunk:
            out.append(sum(chunk) / len(chunk))
    return out


def main() -> None:
    scores = load_scores()
    n = len(scores)
    n_calib = int(n * CALIB_FRAC)
    calib, replay = scores[:n_calib], scores[n_calib:]
    print(f"loaded {n} affect_divergence rows; calibration prefix={n_calib}, replay={len(replay)}")
    print(f"|gap| calibration-prefix stats: mean={np.mean(calib):.4f} std={np.std(calib):.4f} "
          f"max={max(calib):.4f}")

    # --- FROZEN: one split-conformal threshold, fit once, never updated ---
    cc = ConformalCalibrator.fit(calib)
    frozen_thr = cc.threshold(ALPHA_TARGET)
    frozen_flags = [s > frozen_thr for s in replay]
    print(f"\nFROZEN threshold (fit once): {frozen_thr:.4f}")
    print(f"  overall flagged rate: {sum(frozen_flags)/len(frozen_flags)*100:.1f}% (target {ALPHA_TARGET*100:.0f}%)")
    frozen_chunks = chunk_flag_rate(frozen_flags, N_CHUNKS)
    print("  per-chunk flagged rate: " + ", ".join(f"{c*100:.1f}%" for c in frozen_chunks))

    # --- ADAPTIVE: online alpha_t, self-corrects on realized coverage error ---
    aci = AdaptiveConformalInference(calib, alpha_target=ALPHA_TARGET)
    adaptive_flags = [aci.step(s) for s in replay]
    print(f"\nADAPTIVE (online alpha, Gibbs & Candes):")
    print(f"  overall flagged rate: {sum(adaptive_flags)/len(adaptive_flags)*100:.1f}% (target {ALPHA_TARGET*100:.0f}%)")
    adaptive_chunks = chunk_flag_rate(adaptive_flags, N_CHUNKS)
    print("  per-chunk flagged rate: " + ", ".join(f"{c*100:.1f}%" for c in adaptive_chunks))

    # --- Verdict, per the trial's pre-registered bar ---
    frozen_dev = max(abs(c - ALPHA_TARGET) for c in frozen_chunks)
    adaptive_dev = max(abs(c - ALPHA_TARGET) for c in adaptive_chunks)
    print(f"\nmax per-chunk deviation from target: frozen={frozen_dev*100:.1f}pp  adaptive={adaptive_dev*100:.1f}pp")
    if frozen_dev > 2 * adaptive_dev and frozen_dev > 0.05:
        print("-> HELPFUL: adaptive materially holds the target rate where frozen drifts.")
    else:
        print("-> NOT (yet) HELPFUL on this signal: frozen already tracks the target reasonably "
              "well — affect_divergence's |gap| looks stationary enough that adaptive recalibration "
              "buys little here. A real, useful null result, not a failure of the tool.")


if __name__ == "__main__":
    main()
