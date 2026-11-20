"""Read data/left_take_outcomes.jsonl (written by core.left_lane.note_outcome and the orchestrator) and print the
Emissary take's delivery report: per input_type, dispatches / produced / delivered / cancelled / empty / error /
filtered, delivery rate, hub generation p50/p90, and delivered takes that still open "The user".

D-0539 (J-3147) is the writer's reason to exist; THIS is its reader. D-0539's defeater: a delivery rate under 80
percent on the re-seated lane means retire the take (founder call, not an automatic action).

  python scripts/left_take_report.py [--since-hours 24] [--path <jsonl>]
"""
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

from core import left_lane  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since-hours", type=float, default=24.0)
    ap.add_argument("--path", default=None)
    a = ap.parse_args()
    since = time.time() - a.since_hours * 3600 if a.since_hours > 0 else 0.0
    rep = left_lane.delivery_report(Path(a.path) if a.path else None, since_ts=since)
    print(json.dumps(rep, indent=1, ensure_ascii=False))
    for it, r in rep["by_input_type"].items():
        rate = r["delivery_rate"]
        verdict = "no dispatches" if rate is None else ("MEETS the 80% bar" if rate >= 0.8 else "BELOW the 80% bar (D-0539 defeater)")
        print(f"{it}: delivery {rate} -> {verdict}; gen p50 {r['gen_p50_s']} s p90 {r['gen_p90_s']} s; "
              f"'The user' openings delivered: {r['user_opening_delivered']}")


if __name__ == "__main__":
    main()
