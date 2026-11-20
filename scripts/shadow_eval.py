"""
shadow_eval.py — CI-backed shadow-log verdicts (J-0323, Trial 7 of docs/staged/udms_du_capability_trials.md)
=============================================================================================================
Thin wrapper around UDMS's eval_harness.py (Wilson CIs, paired bootstrap, marginal-preserving shuffle —
numpy-only, self-tested, C:\\UDMS\\core\\udms\\eval_harness.py). The enabler this session's trials needed:
F-0399 found the UDMS lens scripts' single chronological-split effect sizes are window-unstable; this gives
Du's own shadow logs (associative_recall_shadow.jsonl and future ones) a real confidence interval instead of
a raw eyeballed percentage, and a shuffle control to check a "difference" isn't just noise.

Ports the CLASSES/FUNCTIONS only (per J-0323's own warning) — not test_ap's data loaders or invented cost
economics. Cross-repo import (C:\\UDMS is a sibling project on the same machine) mirrors the pattern UDMS's
own test scripts already use in reverse (they import Nascence's core.math modules to read Nascence's data).

Time-gate discipline (this project's own rule, mirrors M1/J-0072's week gate): a verdict is refused, not
forced, when too few rows exist — the honest output is "insufficient window", same as findings-log would
refuse a --confidence verified claim with no real evidence.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")   # Windows console default (cp1252) can't print en-dash/minus
except Exception:
    pass
sys.path.insert(0, str(Path(r"C:\UDMS")))
from core.udms import eval_harness as _eh  # noqa: E402

_DATA = Path(__file__).parent.parent / "data"
MIN_ROWS_FOR_VERDICT = 200   # ~1 week at M2's per-cycle firing rate; below this, report the window honestly


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    return rows


def wilson_summary(hits: int, n: int) -> dict:
    if n == 0:
        return {"n": 0, "rate": 0.0, "ci_low": 0.0, "ci_high": 1.0}
    lo, hi = _eh.wilson_ci(hits, n)
    return {"n": n, "hits": hits, "rate": round(hits / n, 4), "ci_low": round(lo, 4), "ci_high": round(hi, 4)}


def m2_verdict(log_path: Path | None = None) -> dict:
    """The J-0280 gate-read, CI-backed rather than eyeballed. Reads associative_recall_shadow.jsonl's
    m2_edge_aware field (as landed by J-0263, extended with fragment ids by J-0315). Returns real
    computed numbers only; the plan doc's own kill criterion is what interprets them, not this function."""
    log_path = log_path or (_DATA / "associative_recall_shadow.jsonl")
    rows = [r for r in load_jsonl(log_path) if r.get("m2_edge_aware")]
    modes = ("task", "reflective", "relational")
    out = {"log": str(log_path), "n_rows": len(rows), "min_rows_for_verdict": MIN_ROWS_FOR_VERDICT,
           "window_sufficient": len(rows) >= MIN_ROWS_FOR_VERDICT}

    per_mode = {}
    paired = {m: [] for m in modes}   # per-row 1/0: did this mode surface anything new this cycle?
    for m in modes:
        hits = 0
        for r in rows:
            mm = r.get("m2_edge_aware", {}).get(m)
            if mm is None:
                continue
            got = 1 if mm.get("new_vs_greedy", 0) > 0 else 0
            paired[m].append(got)
            hits += got
        per_mode[m] = wilson_summary(hits, len(paired[m]))
    out["per_mode_hit_rate"] = per_mode

    # Paired bootstrap: relational vs task (F-0400's early read named these as the extremes) — same
    # rows, same query, so a real paired comparison, not two independent samples.
    if paired["relational"] and paired["task"] and len(paired["relational"]) == len(paired["task"]):
        diff_pct, ci_lo, ci_hi = _eh.paired_bootstrap_diff(paired["relational"], paired["task"])
        out["relational_vs_task_diff_pp"] = {"diff_pct_points": round(diff_pct, 2),
                                              "ci_low": round(ci_lo, 2), "ci_high": round(ci_hi, 2)}
    return out


MIN_ROWS_FOR_USAGE_VERDICT = 100   # usage rows are rarer than edge_aware rows -- only ~7-8% of edge_aware
                                    # rows have any new_ids per mode (see m2_verdict's own hit rates)


def prong2_usage_verdict(log_path: Path | None = None) -> dict:
    """Prong 2 (J-0446/F-0605, the 'is an edge-reached fragment ever actually USED by the following
    thought' question kill-criterion prong 1 alone cannot answer). Joins m2_usage rows to their parent
    m2_edge_aware row by parent_ts (per the plan doc's own note that this join was the missing piece).
    No pre-registered 'used' threshold exists anywhere in memory_multiway_linking.md or cognitive_geometry
    .md -- J-0446's own briefing deliberately left the score un-binarized for a future gate-read to pick
    its own bar or read the distribution directly. This function does the latter: reports the real
    cos_sim distribution per mode plus an illustrative >=0.5 rate (Wilson CI) as a descriptive anchor,
    NOT a pass/fail verdict -- interpreting these numbers against the kill criterion is a founder read,
    same discipline m2_verdict() above already applies to prong 1."""
    log_path = log_path or (_DATA / "associative_recall_shadow.jsonl")
    rows = load_jsonl(log_path)
    usage_rows = [r for r in rows if r.get("kind") == "m2_usage"]
    modes = ("task", "reflective", "relational")
    out = {"log": str(log_path), "n_usage_rows": len(usage_rows),
           "min_rows_for_verdict": MIN_ROWS_FOR_USAGE_VERDICT,
           "window_sufficient": len(usage_rows) >= MIN_ROWS_FOR_USAGE_VERDICT}

    per_mode = {}
    for m in modes:
        sims = [entry.get("cos_sim") for r in usage_rows
                for entry in ((r.get("usage_by_mode") or {}).get(m) or [])
                if entry.get("cos_sim") is not None]
        n = len(sims)
        summary = {"n_scored_fragments": n}
        if n:
            sims_sorted = sorted(sims)
            summary["mean"] = round(sum(sims) / n, 4)
            summary["median"] = round(sims_sorted[n // 2], 4)
            summary["min"] = round(sims_sorted[0], 4)
            summary["max"] = round(sims_sorted[-1], 4)
            summary["rate_ge_0.5"] = wilson_summary(sum(1 for s in sims if s >= 0.5), n)
        per_mode[m] = summary
    out["per_mode_usage"] = per_mode
    return out


def _print_usage_report(v: dict) -> None:
    print(f"\nprong-2 (usage) -- {v['log']}")
    print(f"  m2_usage rows: {v['n_usage_rows']}  (verdict threshold: {v['min_rows_for_verdict']})")
    if not v["window_sufficient"]:
        print("  WINDOW INSUFFICIENT -- reporting the real numbers below as a status read, NOT a verdict.")
    for mode, s in v["per_mode_usage"].items():
        n = s["n_scored_fragments"]
        if n == 0:
            print(f"  {mode:11s} n=0 scored fragments (no new_ids were pending for this mode when a usage row landed)")
            continue
        r = s["rate_ge_0.5"]
        print(f"  {mode:11s} n={n:4d}  mean_cos={s['mean']:.3f}  median={s['median']:.3f}  "
              f"range=[{s['min']:.3f}, {s['max']:.3f}]  rate>=0.5={r['rate']*100:.1f}% "
              f"(95% CI [{r['ci_low']*100:.1f}%, {r['ci_high']*100:.1f}%])")
    print("  (no pre-registered 'used' threshold exists in the plan docs -- 0.5 is an illustrative anchor")
    print("   only, not a pass/fail bar; interpreting this against the kill criterion is a founder read.)")


def _print_report(v: dict) -> None:
    print(f"shadow_eval — {v['log']}")
    print(f"  rows with m2_edge_aware: {v['n_rows']}  (verdict threshold: {v['min_rows_for_verdict']})")
    if not v["window_sufficient"]:
        print(f"  WINDOW INSUFFICIENT — reporting the real numbers below as a status read, NOT a verdict.")
    print()
    for mode, s in v["per_mode_hit_rate"].items():
        print(f"  {mode:11s} hit-rate {s['rate']*100:5.1f}%  (n={s['n']}, hits={s.get('hits','?')})  "
              f"95% CI [{s['ci_low']*100:.1f}%, {s['ci_high']*100:.1f}%]")
    d = v.get("relational_vs_task_diff_pp")
    if d:
        print(f"\n  relational vs task: {d['diff_pct_points']:+.1f}pp  "
              f"(paired-bootstrap 95% CI [{d['ci_low']:+.1f}, {d['ci_high']:+.1f}])")
        if d["ci_low"] > 0:
            print("    -> CI excludes zero: relational is REAL-y ahead of task (not noise, this window).")
        else:
            print("    -> CI includes zero: cannot yet distinguish from no difference.")


if __name__ == "__main__":
    _print_report(m2_verdict())
    _print_usage_report(prong2_usage_verdict())
