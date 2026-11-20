"""J-4420: daily volume of the re-warm SHADOW log (data/rewarm_shadow.jsonl). Read-only.

Usage: python scripts/rewarm_shadow_report.py [path-to-rewarm_shadow.jsonl]

Prints, per UTC day: would-warm rows, distinct fragments, walled rows scored (the denominator), and the split
by label (4gram / emb / both). Nothing is applied by the shadow; this only shows the founder how much WOULD be.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core import rewarm_shadow  # noqa: E402


def main(argv) -> int:
    path = Path(argv[1]) if len(argv) > 1 else rewarm_shadow._LOG
    days = rewarm_shadow.daily_counts(path)
    if not days:
        print(f"no rows in {path}")
        return 0
    print(f"{'day':<12}{'would_warm':>11}{'distinct':>10}{'scored':>8}  labels")
    for day in sorted(days):
        d = days[day]
        labs = ", ".join(f"{k}={v}" for k, v in sorted(d["by_label"].items()))
        print(f"{day:<12}{d['would_warm']:>11}{d['distinct_fragments']:>10}{d['scored_walled']:>8}  {labs}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
