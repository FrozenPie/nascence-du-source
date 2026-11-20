"""J-2873 reader for data/ground_skip_log.jsonl (why the Emissary did not ground a thought; D-0569 skip path).

Per day: skips by reason next to the grounded-and-integrated count (deliberation_log.jsonl) and the grounder-null
count (deliberation_null_log.jsonl), so the D-0569 defeater (more than 25 percent of idle thoughts ungrounded over
a month) can be read without joining nascence.log to llm_latency. Read-only. Usage:
    python scripts/ground_skip_report.py [--days N]
"""
import argparse
import collections
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import core  # noqa: E402,F401  -- before anything else, must be THIS checkout

from core import left_lane  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def _day_counts(path: Path, since_ts: float) -> collections.Counter:
    c: collections.Counter = collections.Counter()
    try:
        for ln in path.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(ln)
            except Exception:
                continue
            if r.get("ts", 0) >= since_ts:
                c[time.strftime("%Y-%m-%d", time.localtime(r["ts"]))] += 1
    except FileNotFoundError:
        pass
    return c


def report(data_dir: Path | None = None, days: int = 30) -> str:
    d = Path(data_dir) if data_dir else HERE / "data"
    since = time.time() - days * 86400
    skips = left_lane.ground_skip_summary(d / "ground_skip_log.jsonl", since_ts=since)
    grounded = _day_counts(d / "deliberation_log.jsonl", since)
    nulls = _day_counts(d / "deliberation_null_log.jsonl", since)
    lines = [f"ground skips, last {days} days: {skips['rows']} rows, by reason {skips['by_reason']}",
             "day         grounded  null  skips  reasons"]
    for day in sorted(set(skips["by_day"]) | set(grounded) | set(nulls)):
        s = skips["by_day"].get(day, {})
        lines.append(f"{day}  {grounded.get(day, 0):8d}  {nulls.get(day, 0):4d}  {sum(s.values()):5d}  {s}")
    return "\n".join(lines)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30)
    print(report(days=ap.parse_args().days))
