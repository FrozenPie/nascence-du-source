"""J-2808 / F-3453: the READER for data/episodic_buffer_judge_shadow.jsonl (core/episodic_buffer_judge.py).

  python scripts/episodic_buffer_judge_report.py            # judge's unsupported rate beside the buffer's own coherence

Read-only, no model calls.  The comparison is a 'preview' until READY_ROWS (100) valid rows exist AND the positive control
(scripts/episodic_buffer_judge_control.py --record) has passed on the current prompt.  Prints, acts on nothing.
"""
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401
from core import episodic_buffer_judge as ebj  # noqa: E402

if __name__ == "__main__":
    print(json.dumps(ebj.compare(), indent=2, ensure_ascii=False))
