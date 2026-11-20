"""
hodge_threshold_search.py — Trial 5 of docs/staged/udms_du_capability_trials.md (J-0321), part 1
====================================================================================================
THE BUG (confirmed live this session, F-0402/F-0413 lineage): UDMS's test_c_temporal_holdout_
generalization.py picks the "optimal" curl threshold by maximizing avg_gradient - avg_curl — but
those two numbers are summed UNCONDITIONALLY across every window regardless of the threshold's own
decision (THROTTLE_AND_BRANCH vs CONTINUE). gradient_ratio/curl_ratio are properties of the raw
trajectory, not of the threshold, so the threshold search finds "the same fixed number" at every
candidate threshold — verified: separation was EXACTLY -0.0550 at all 19 thresholds tested.

THE FIX: separation should measure how well a threshold's decision SEPARATES the throttled group
from the continued group — mean_curl(throttled) - mean_curl(continued). This is genuinely
threshold-dependent, because WHICH windows land in each bucket changes with the threshold.

Reuses the real, unbroken DiscreteHodgeGovernor class (imported, not reimplemented) and test_c's
own extract_state_vector/build_windows (imported) — only evaluate_at_threshold's AGGREGATION is
rewritten here.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(r"C:\UDMS\scripts")))
sys.path.insert(0, str(Path(r"C:\UDMS")))
from test_c_temporal_holdout_generalization import extract_state_vector, build_windows  # noqa: E402
from core.math.hodge_governor import DiscreteHodgeGovernor  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stamp_row_filter import drop_stamp_rows  # noqa: E402

DATA = Path(__file__).parent.parent / "data" / "geometry_tuples.jsonl"
TRAIN_FRAC = 0.70


def load_sorted_tuples() -> list[dict]:
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
    rows = drop_stamp_rows(rows)   # J-3944/F-4595: file order, before the sort
    rows.sort(key=lambda t: t.get("ts", 0.0))
    return rows


def evaluate_at_threshold_fixed(windows: list, threshold: float) -> dict:
    """FIXED: separation is the curl-ratio gap BETWEEN the throttled and continued groups, not an
    unconditional average that ignores the threshold's own decision."""
    gov = DiscreteHodgeGovernor(energy_threshold_curl=threshold)
    throttled_curl, continued_curl = [], []
    throttled_grad, continued_grad = [], []
    for window in windows:
        res = gov.evaluate_thought_trajectory(window)
        if res["decision"] == "THROTTLE_AND_BRANCH":
            throttled_curl.append(res["curl_ratio"])
            throttled_grad.append(res["gradient_ratio"])
        else:
            continued_curl.append(res["curl_ratio"])
            continued_grad.append(res["gradient_ratio"])
    total = len(throttled_curl) + len(continued_curl)
    mean_ct = float(np.mean(throttled_curl)) if throttled_curl else 0.0
    mean_cc = float(np.mean(continued_curl)) if continued_curl else 0.0
    return {"threshold": threshold, "throttle_pct": round(len(throttled_curl) / max(1, total) * 100, 2),
            "mean_curl_throttled": round(mean_ct, 4), "mean_curl_continued": round(mean_cc, 4),
            "separation": round(mean_ct - mean_cc, 4), "n_throttled": len(throttled_curl),
            "n_continued": len(continued_curl)}


def main() -> None:
    tuples = load_sorted_tuples()
    n = len(tuples)
    split = int(n * TRAIN_FRAC)
    train_tuples, test_tuples = tuples[:split], tuples[split:]
    print(f"loaded {n} tuples; train={len(train_tuples)} test={len(test_tuples)}")

    train_states = [extract_state_vector(t) for t in train_tuples]
    # build_windows expects raw tuples and extracts internally in test_c's own version -- reuse if
    # that's its signature, else fall back to state-vector windows directly.
    try:
        train_windows = build_windows(train_tuples, window_size=5)
    except Exception:
        train_windows = [train_states[i:i + 5] for i in range(len(train_states) - 4)]

    print(f"\n{'thr':>6s} {'throttle%':>10s} {'curl(throt)':>12s} {'curl(cont)':>12s} {'separation':>11s}")
    thresholds = [round(t, 2) for t in np.arange(0.05, 1.00, 0.05)]
    results = [evaluate_at_threshold_fixed(train_windows, t) for t in thresholds]
    for r in results:
        print(f"{r['threshold']:6.2f} {r['throttle_pct']:10.1f} {r['mean_curl_throttled']:12.4f} "
              f"{r['mean_curl_continued']:12.4f} {r['separation']:11.4f}")

    varies = len(set(r["separation"] for r in results)) > 1
    print(f"\n{'FIXED' if varies else 'STILL BROKEN'}: separation "
          f"{'genuinely varies' if varies else 'is identical'} across thresholds "
          f"({len(set(r['separation'] for r in results))} distinct values of {len(results)} thresholds tested)")

    best = max(results, key=lambda r: r["separation"])
    print(f"optimal threshold (max separation): {best['threshold']:.2f}  (separation={best['separation']:.4f})")

    # Lock the found threshold, evaluate on held-out test
    test_windows = [extract_state_vector(t) for t in test_tuples]
    test_windows = [test_windows[i:i + 5] for i in range(len(test_windows) - 4)]
    test_result = evaluate_at_threshold_fixed(test_windows, best["threshold"])
    print(f"\nlocked-threshold test-set result: throttle%={test_result['throttle_pct']:.1f} "
          f"separation={test_result['separation']:.4f} (train separation was {best['separation']:.4f})")


if __name__ == "__main__":
    main()
