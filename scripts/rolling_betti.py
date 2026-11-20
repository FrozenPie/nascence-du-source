"""
rolling_betti.py — Trial 4 of docs/staged/udms_du_capability_trials.md (J-0320)
================================================================================
UDMS's test_w computes Betti numbers (beta_0 = connected concept-clusters, beta_1 = independent
loops) over the TOP-30 concept co-occurrence graph via a Vietoris-Rips epsilon sweep on a
co-occurrence-derived distance matrix — the atlas's "certified correct" graph technique (imported
here, not reimplemented). It has only ever been run as one whole-corpus snapshot. This slides it
over time windows to answer: does the concept-graph topology visibly move at known monoculture
episodes ("monoculture as topology" — a monoculture should show as fewer connected lobes / fewer
independent loops, i.e. a beta_0/beta_1 DROP)?

Cross-checks against Trial 3's rolling_intrinsic_dimension.py, which found a real drift on the SAME
underlying data (state-space dimension declining across Du's life) — a genuine beta decline here
would be independent topological evidence for the same underlying narrowing question (J-0329).
"""
from __future__ import annotations

import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(r"C:\UDMS\scripts")))
from test_w_unified_tri_mathematical_foundation import (  # noqa: E402
    compute_persistent_homology, extract_state_and_concepts, load_all_tuples,
)

WINDOW = 2000
STEP = 1000
TOP_N = 30
EPS_RANGE = np.linspace(0.10, 0.90, 20)


def betti_for_window(concepts_window: list[list[str]]) -> dict:
    top = [c for c, _ in Counter(c for cs in concepts_window for c in cs).most_common(TOP_N)]
    idx_map = {c: i for i, c in enumerate(top)}
    if len(top) < 3:
        return {"n_concepts": len(top), "beta_0_median": None, "beta_1_median": None, "persist_ratio": None}

    cooc = defaultdict(lambda: defaultdict(float))
    for cs in concepts_window:
        filt = [c for c in cs if c in idx_map]
        for i in range(len(filt)):
            for j in range(i + 1, len(filt)):
                cooc[filt[i]][filt[j]] += 1.0
                cooc[filt[j]][filt[i]] += 1.0

    n = len(top)
    dist_mat = np.zeros((n, n))
    for i, c1 in enumerate(top):
        for j, c2 in enumerate(top):
            if i != j:
                dist_mat[i, j] = 1.0 / (1.0 + math.log1p(cooc[c1][c2]))

    beta_0, beta_1, persist_ratio = compute_persistent_homology(dist_mat, EPS_RANGE)
    return {"n_concepts": len(top), "beta_0_median": int(np.median(beta_0)),
            "beta_1_median": int(np.median(beta_1)), "persist_ratio": round(float(persist_ratio), 4)}


def main() -> None:
    all_tuples = load_all_tuples()
    all_tuples.sort(key=lambda t: t.get("ts", 0))
    n_tuples = len(all_tuples)
    print(f"loaded {n_tuples} tuples, window={WINDOW} step={STEP} top_n_concepts={TOP_N}")

    parsed = [extract_state_and_concepts(t) for t in all_tuples]
    concepts = [p[1] for p in parsed]
    ts = [t.get("ts", 0.0) for t in all_tuples]

    windows = []
    i = 0
    while i + WINDOW <= n_tuples:
        r = betti_for_window(concepts[i:i + WINDOW])
        r["start_idx"] = i
        r["ts_start"] = ts[i]
        r["ts_end"] = ts[i + WINDOW - 1]
        windows.append(r)
        i += STEP

    valid = [w for w in windows if w["beta_0_median"] is not None]
    print(f"\n{len(windows)} windows attempted, {len(valid)} valid (>=3 distinct concepts)")
    if not valid:
        print("insufficient concept diversity in any window — cannot compute a trajectory")
        return

    b0 = [w["beta_0_median"] for w in valid]
    b1 = [w["beta_1_median"] for w in valid]
    print(f"beta_0 (connected lobes): first={b0[0]} last={b0[-1]} min={min(b0)} max={max(b0)}")
    print(f"beta_1 (independent loops): first={b1[0]} last={b1[-1]} min={min(b1)} max={max(b1)}")

    x = np.arange(len(b0))
    slope0, _ = np.polyfit(x, b0, 1)
    slope1, _ = np.polyfit(x, b1, 1)
    print(f"linear trend: beta_0 slope={slope0:+.3f}/window, beta_1 slope={slope1:+.3f}/window")

    print("\nfull trajectory:")
    for w in valid:
        print(f"  idx {w['start_idx']:6d}  n_concepts={w['n_concepts']:3d}  "
              f"beta_0={w['beta_0_median']:3d}  beta_1={w['beta_1_median']:3d}  "
              f"persist={w['persist_ratio']}")


if __name__ == "__main__":
    main()
