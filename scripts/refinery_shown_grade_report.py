"""
READER for the shown-members fidelity grade in data/refinery_shadow.jsonl (J-3066 phase 0). Read-only.

Prints refinery.shown_grade_status(): how many records carry `fidelity_shown`, how many ACCEPTED insights (old
all-members gate) the shown-members whole-word grade would have rejected, overall and split by cluster size, and
whether the SHOWN_GRADE_REVIEW_N (20) review point is reached. It decides nothing: moving the gate onto the new grade
is a founder call after this is read.

Run from the repo root:  python scripts/refinery_shown_grade_report.py [--log PATH]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default=str(ROOT / "data" / "refinery_shadow.jsonl"))
    a = ap.parse_args()
    from core import refinery
    st = refinery.shown_grade_status(a.log)
    print("status:", json.dumps(st))
    if not st.get("records"):
        print("no records carry fidelity_shown yet (Du restart from a merged master needed, then a sleep refinery run)")
        return 0
    n = st["review_n"]
    print(f"{st['records']} records carry the shown-members grade; review point {n}: "
          f"{'REACHED' if st['review_ready'] else 'not yet'}")
    print(f"accepted by the old gate: {st['accepted']}; would be rejected under the shown-members grade: "
          f"{st['would_reject']} ({st['would_reject_rate']})")
    print(f"{'size':>8} {'accepted':>9} {'would_reject':>13} {'rate':>6}")
    for k, b in sorted(st["by_cluster_size"].items(), key=lambda kv: int(kv[0].split('-')[0].rstrip('+'))):
        print(f"{k:>8} {b['accepted']:>9} {b['would_reject']:>13} {b['would_reject_rate']!s:>6}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
