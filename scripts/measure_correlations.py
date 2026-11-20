"""
Nascence — Correlation Telemetry (Phase 3)

MEASURE FIRST, UNIFY LATER. Before any of the psychological "currencies" (contradiction
pressure, climate dissonance, world-model strain, trust decay, social prediction error) may
be merged into a single Active-Inference equation, we must PROVE they actually move together.
This script reads the per-cycle telemetry the orchestrator writes to
`data/correlation_log.jsonl` and computes the Pearson correlation coefficient R for the pairs
the plan named:

    1. contradiction_pressure   ↔ critic_rejections
    2. dissonance               ↔ world_model_strain
    3. trust (relational_trust) ↔ user_corrections

Only a pair whose |R| clears the activation threshold (0.85) over 100+ paired samples is a
candidate for unification (see core/unified_inference.py, which stays inert until then).

Pure stdlib — no numpy/scipy dependency, so it runs anywhere the logs are. Usage:

    python scripts/measure_correlations.py
    python scripts/measure_correlations.py --min-samples 100
    python scripts/measure_correlations.py --log path/to/correlation_log.jsonl
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # spirit names / glyphs in logs

_DEFAULT_LOG = Path(__file__).parent.parent / "data" / "correlation_log.jsonl"
_ACTIVATION_R = 0.85

# The pairs the plan specified. Each: (label, key_a, key_b).
_PAIRS = [
    ("contradiction_pressure ↔ critic_rejection", "contradiction_pressure", "critic_rejection"),
    ("dissonance ↔ world_model_strain",           "dissonance",             "world_model_strain"),
    ("trust ↔ user_correction",                   "relational_trust",       "user_correction"),
    # Bonus diagnostics — useful while tuning, not gate-bearing.
    ("delta_social ↔ user_correction",            "delta_social",           "user_correction"),
    ("completion_tension ↔ critic_rejection",     "completion_tension",     "critic_rejection"),
]


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    """Pearson R over paired samples. None if undefined (n<2 or zero variance)."""
    n = len(xs)
    if n < 2:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx  = sum((x - mx) ** 2 for x in xs)
    vy  = sum((y - my) ** 2 for y in ys)
    denom = math.sqrt(vx * vy)
    if denom == 0.0:
        return None
    return cov / denom


def _load(log_path: Path) -> list[dict]:
    if not log_path.exists():
        print(f"No telemetry yet at {log_path}")
        print("Run some cycles first — the orchestrator writes one line per cycle.")
        return []
    rows = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="Pearson correlations between psychological currencies.")
    ap.add_argument("--log", type=Path, default=_DEFAULT_LOG, help="path to correlation_log.jsonl")
    ap.add_argument("--min-samples", type=int, default=100, help="samples required before a pair is gate-eligible")
    args = ap.parse_args()

    rows = _load(args.log)
    if not rows:
        return 1

    print(f"\nNascence — Correlation Telemetry")
    print(f"  log:     {args.log}")
    print(f"  samples: {len(rows)} cycles")
    print(f"  gate:    |R| > {_ACTIVATION_R} over ≥{args.min_samples} samples\n")
    print(f"  {'pair':<42} {'R':>8} {'n':>6}   verdict")
    print(f"  {'-'*42} {'-'*8} {'-'*6}   {'-'*28}")

    any_gate_ready = False
    for label, ka, kb in _PAIRS:
        xs, ys = [], []
        for r in rows:
            if ka in r and kb in r and r[ka] is not None and r[kb] is not None:
                try:
                    xs.append(float(r[ka])); ys.append(float(r[kb]))
                except (TypeError, ValueError):
                    pass
        rval = _pearson(xs, ys)
        n = len(xs)
        if rval is None:
            verdict = "insufficient / no variance"
            rstr = "  n/a"
        elif abs(rval) > _ACTIVATION_R and n >= args.min_samples:
            verdict = "★ UNIFICATION-ELIGIBLE"
            rstr = f"{rval:+.3f}"
            any_gate_ready = True
        elif abs(rval) > _ACTIVATION_R:
            verdict = f"strong, need ≥{args.min_samples} (have {n})"
            rstr = f"{rval:+.3f}"
        else:
            verdict = "separate — keep distinct"
            rstr = f"{rval:+.3f}"
        print(f"  {label:<42} {rstr:>8} {n:>6}   {verdict}")

    print()
    if any_gate_ready:
        print("  ⇒ At least one pair clears the gate. Consider listing it in")
        print("    core/unified_inference.py _ACTIVE_PAIRS and setting ENABLE_UNIFIED_INFERENCE=True.")
    else:
        print("  ⇒ No pair is unification-eligible yet. Currencies stay separate (correct default).")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
