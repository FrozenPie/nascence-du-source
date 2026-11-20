"""
rolling_intrinsic_dimension.py — Trial 3 of docs/staged/udms_du_capability_trials.md (J-0319)
================================================================================================
The snapshot estimators (Levina-Bickel MLE, TwoNN, local-PCA participation ratio) already agree
Du's 6D affect state occupies ~2.0 effective dimensions (F-0402, this session's first-pass run).
The open question the snapshot can't answer: does that number DRIFT over Du's life? This slides
the SAME certified estimator (UDMS's compute_intrinsic_dimensions, imported not reimplemented)
over 500-tuple windows across the full chronological span of geometry_tuples.jsonl.

Answers docs/staged/geometry_tuple_index.md's open sizing question: how many real dimensions are
worth indexing, and is that a fixed number or a moving target.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(r"C:\UDMS\scripts")))
from test_y_through_ad_surgical_manifold_battery import compute_intrinsic_dimensions  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stamp_row_filter import drop_stamp_rows  # noqa: E402

DATA = Path(__file__).parent.parent / "data" / "geometry_tuples.jsonl"
WINDOW = 500
STEP = 250   # 50% overlap — enough windows to see a trend without redundant noise from step=1


def extract_state(t: dict) -> list[float]:
    body = t.get("body") or {}
    affect = t.get("affect") or {}
    unresolved = t.get("unresolved", False)
    return [
        1.0 - affect.get("valence", 0.5),
        body.get("tension", 0.1),
        0.8 if unresolved else 0.1,
        1.0 - t.get("level", 0.5),
        body.get("energy", 0.5),
        affect.get("arousal", 0.3),
    ]


def load_sorted_states() -> tuple[list[float], list[list[float]]]:
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
    rows = drop_stamp_rows(rows)   # J-3944/F-4595: file order, BEFORE the ts sort; stamps are near-duplicate twins
    rows.sort(key=lambda t: t.get("ts", 0.0))
    ts = [r.get("ts", 0.0) for r in rows]
    states = [extract_state(r) for r in rows]
    return ts, states


def main() -> None:
    ts, states = load_sorted_states()
    n = len(states)
    print(f"loaded {n} tuples, chronologically sorted, window={WINDOW} step={STEP}")

    windows = []
    i = 0
    while i + WINDOW <= n:
        X = np.array(states[i:i + WINDOW])
        res = compute_intrinsic_dimensions(X)
        windows.append({"start_idx": i, "ts_start": ts[i], "ts_end": ts[i + WINDOW - 1],
                        **res})
        i += STEP

    if not windows:
        print(f"insufficient data: {n} tuples < one window ({WINDOW})")
        return

    consensus = [w["consensus_dim"] for w in windows]
    print(f"\n{len(windows)} windows computed")
    print(f"consensus_dim: min={min(consensus):.3f} max={max(consensus):.3f} "
          f"first={consensus[0]:.3f} last={consensus[-1]:.3f} mean={np.mean(consensus):.3f}")

    # Simple trend check: linear fit of consensus_dim vs window index
    x = np.arange(len(consensus))
    slope, intercept = np.polyfit(x, consensus, 1)
    total_drift = slope * (len(consensus) - 1)
    print(f"linear trend: slope={slope:+.4f}/window, total drift across the series = {total_drift:+.3f} dims")
    if abs(total_drift) < 0.3:
        print("-> STABLE: consensus dimension does not meaningfully drift across Du's recorded life so far.")
    else:
        print(f"-> DRIFTS: {'increasing' if total_drift > 0 else 'decreasing'} complexity over time — "
              f"worth a closer look before treating ~2.0 as a fixed index size.")

    print("\nfirst 3 windows:")
    for w in windows[:3]:
        print(f"  idx {w['start_idx']:5d}  consensus={w['consensus_dim']:.3f}  "
              f"(mle={w['dim_mle']:.2f} twonn={w['dim_twonn']:.2f} pr={w['participation_ratio']:.2f})")
    print("last 3 windows:")
    for w in windows[-3:]:
        print(f"  idx {w['start_idx']:5d}  consensus={w['consensus_dim']:.3f}  "
              f"(mle={w['dim_mle']:.2f} twonn={w['dim_twonn']:.2f} pr={w['participation_ratio']:.2f})")


if __name__ == "__main__":
    main()
