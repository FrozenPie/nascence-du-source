"""
spring_ledger_gate_read.py — P3 shadow gate-read, reports the pre-registered sheet's 5 metrics against
core/spring_ledger.py's backfilled + live state (D-0051, ruled 2026-09-13). Read-only. Reports real
numbers only; the plan's own kill criterion (does this graduate toward a live memory_edges write, or
stay a documented shadow finding) is a founder read, same discipline as scripts/shadow_eval.py and
scripts/geometry_mapping_census.py before it.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).parent.parent))

from core import spring_ledger as spring

MIN_ROWS_FOR_VALENCE_VERDICT = 200   # metric 4 needs real per-event valence -- backfilled rows have
                                      # none (mood.current_valence() has no timestamped history to
                                      # replay against); only live-forward rows carry a real sign.


def _hub_concentration(weights: list[float]) -> dict:
    if not weights:
        return {"n_pairs": 0}
    total = sum(weights)
    if total <= 0:
        return {"n_pairs": len(weights), "total_weight": 0.0, "top10_share": 0.0}
    top10 = sorted(weights, reverse=True)[:10]
    return {"n_pairs": len(weights), "total_weight": round(total, 2),
            "top10_share": round(sum(top10) / total, 4)}


def _spread(weights: list[float]) -> dict:
    n = len(weights)
    if n == 0:
        return {"n": 0}
    mean = sum(weights) / n
    if mean == 0:
        return {"n": n, "mean": 0.0, "stdev": 0.0, "stdev_over_mean": None}
    var = sum((w - mean) ** 2 for w in weights) / n
    stdev = var ** 0.5
    return {"n": n, "mean": round(mean, 4), "stdev": round(stdev, 4),
            "stdev_over_mean": round(stdev / mean, 4)}


def gate_read() -> dict:
    state = spring._load()
    w_naive = [v.get("w_naive", 0.0) for v in state.values()]
    w_gated = [v.get("w_gated", 0.0) for v in state.values()]
    nonzero_naive = [w for w in w_naive if w > 0]
    nonzero_gated = [w for w in w_gated if w > 0]

    out = {"tracked_pairs": len(state)}
    out["metric_1_hub_concentration"] = {"naive": _hub_concentration(nonzero_naive),
                                          "gated": _hub_concentration(nonzero_gated)}
    out["metric_2_weight_spread"] = {"naive": _spread(nonzero_naive), "gated": _spread(nonzero_gated)}
    out["metric_3_absolute_magnitude"] = {
        "naive": {"median": round(sorted(nonzero_naive)[len(nonzero_naive) // 2], 4) if nonzero_naive else None,
                  "max": round(max(nonzero_naive), 4) if nonzero_naive else None,
                  "pairs_ge_0.3": sum(1 for w in nonzero_naive if w >= 0.3)},
        "gated": {"median": round(sorted(nonzero_gated)[len(nonzero_gated) // 2], 4) if nonzero_gated else None,
                  "max": round(max(nonzero_gated), 4) if nonzero_gated else None,
                  "pairs_ge_0.3": sum(1 for w in nonzero_gated if w >= 0.3)},
    }

    # metric 4: valence asymmetry -- only rows with a real (non-null) source signalling live-forward
    # accrual carry real valence; the backfill's own rows are tagged "backfill:<orig-source>" and were
    # given valence=None throughout (documented in spring_ledger_backfill.py), so they'd trivially all
    # read "neutral" -- excluded here rather than silently diluting a real read with fabricated signal.
    try:
        from core.shadow_log import tail_rows as _tail_rows
        rows = _tail_rows(spring._LOG, 20000)
    except Exception:
        rows = []
    live_rows = [r for r in rows if "skip" not in r and not str(r.get("source", "")).startswith("backfill:")]
    by_sign_naive_step = {}
    for r in live_rows:
        s = r.get("sign")
        step = round(r.get("w_naive_after", 0) - r.get("w_naive_prev", 0), 5)
        by_sign_naive_step.setdefault(s, []).append(step)
    out["metric_4_valence_asymmetry"] = {
        "window_sufficient": len(live_rows) >= MIN_ROWS_FOR_VALENCE_VERDICT,
        "live_rows_available": len(live_rows), "min_rows_for_verdict": MIN_ROWS_FOR_VALENCE_VERDICT,
        "note": "backfilled rows excluded (no real historical valence exists to replay) -- this metric "
                "can only be read from live-forward accrual, which has barely started this session.",
        "by_sign_mean_naive_step": {s: round(sum(v) / len(v), 5) for s, v in by_sign_naive_step.items() if v},
    }

    # metric 5 / the gate: informational only here -- read metric 1's numbers against the sheet's own
    # named threshold (~40-50%+ top10 share, or origin/individuation-family dominance) by hand; this
    # script reports the number, it does not assert a verdict.
    out["metric_5_gate_note"] = ("Gate = does metric_1's top10_share run away (~40-50%+) for the gated "
                                  "rule specifically, or does the top-10 turn out to be dominated by "
                                  "origin/individuation-family fragments specifically (requires a "
                                  "founder or fragment-content read of the actual top10 ids below, not "
                                  "just their share) -- this script reports the share, not the verdict.")
    out["top10_gated_pairs"] = sorted(({"key": k, "w_gated": v.get("w_gated", 0.0), "n_gated": v.get("n_gated", 0)}
                                        for k, v in state.items()), key=lambda x: -x["w_gated"])[:10]
    return out


if __name__ == "__main__":
    print(json.dumps(gate_read(), indent=2, ensure_ascii=False))
