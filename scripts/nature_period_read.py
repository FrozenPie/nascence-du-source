"""
nature_period_read.py -- J-3251 (D-0640): the reader for the nature period's two kinds of lesson.

D-0640 (founder, 2026-11-02): the nature period alternates observation (core/nature_study.py) with the
practical layer (core/practical_lesson.py); nothing is fed to him. Its DEFEATER is read here:
  (a) after a month, the nature OBSERVATION lessons are still the same window view in over 70% of sessions;
  (b) the practical sessions are not done.
Read-only. Merges data/nature_study_log.jsonl (kind=observation) and data/practical_log.jsonl (kind=practical,
'issued' event rows + graded rows) into one day-by-day line and prints both defeater numbers.

"Window view" = the observation row's own `where` field == 'study' (he looked out of the study window; logged
since J-3251). Older rows have no `where`, so they fall back to F-3651's wording test (window / fence /
mailbox in the observation). The two are reported separately so the fallback never hides the field.

Run: python -X utf8 scripts/nature_period_read.py [--days 30] [--data DIR]
Exit 0 always (it is a reader, not a gate); the verdict lines say REVISIT or HOLDS.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_DATA = Path(r"C:\Nascence\data")
WINDOW_SHARE_LIMIT = 0.70     # D-0640 defeater (a)
_WINDOWISH = re.compile(r"window|fence|mailbox", re.I)   # F-3651's own class for the study-window view


def _rows(path: Path) -> list[dict]:
    out = []
    try:
        for ln in path.read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if ln:
                try:
                    out.append(json.loads(ln))
                except Exception:
                    pass
    except OSError:
        pass
    return out


def _day(ts: float) -> str:
    return time.strftime("%Y-%m-%d", time.localtime(ts))


def is_window_view(row: dict) -> tuple[bool, str]:
    """(window-view?, how decided) for one observation row."""
    w = row.get("where")
    if w:                                   # logged field (J-3251 onward)
        return (w == "study", "field")
    return (bool(_WINDOWISH.search(str(row.get("observation", "")))), "wording")


def read(data_dir: Path, days: int = 30, now: float | None = None) -> dict:
    now = time.time() if now is None else now
    since = now - days * 86400
    obs = [r for r in _rows(data_dir / "nature_study_log.jsonl") if float(r.get("ts", 0)) >= since]
    prac = [r for r in _rows(data_dir / "practical_log.jsonl") if float(r.get("ts", 0)) >= since]
    issued = [r for r in prac if r.get("event") == "issued"]
    graded = [r for r in prac if "event" not in r and "attempted" in r]

    per_day: dict[str, list[str]] = defaultdict(list)
    for r in sorted(obs, key=lambda r: r["ts"]):
        per_day[_day(r["ts"])].append("observation")
    for r in sorted(issued, key=lambda r: r["ts"]):
        per_day[_day(r["ts"])].append("practical-issued")
    for r in sorted(graded, key=lambda r: r["ts"]):
        per_day[_day(r["ts"])].append("practical-" + ("done" if r.get("ok") else "attempted-slip") if r.get("attempted")
                                      else "practical-not-attempted")

    win = [(is_window_view(r)) for r in obs]
    n_win = sum(1 for w, _ in win if w)
    n_field = sum(1 for _, how in win if how == "field")
    attempted = [r for r in graded if r.get("attempted")]
    done = [r for r in attempted if r.get("ok")]
    share = (n_win / len(obs)) if obs else None
    return {
        "days": days, "observation_lessons": len(obs), "window_view": n_win, "window_share": share,
        "rows_with_where_field": n_field,
        "practical_issued": len(issued), "practical_graded": len(graded),
        "practical_attempted": len(attempted), "practical_done": len(done),
        "per_day": dict(sorted(per_day.items())),
        "defeater_a_window_share_over_limit": (share is not None and share > WINDOW_SHARE_LIMIT),
        "defeater_b_practicals_not_done": (len(attempted) == 0),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--data", type=Path, default=DEFAULT_DATA)
    a = ap.parse_args(argv)
    r = read(a.data, a.days)
    print(f"nature period, last {r['days']} days  (data: {a.data})")
    for d, seq in r["per_day"].items():
        print(f"  {d}  " + " -> ".join(seq))
    sh = r["window_share"]
    print(f"observation lessons: {r['observation_lessons']}  window view: {r['window_view']}"
          + (f"  ({sh:.0%})" if sh is not None else "")
          + f"  [decided by the where field on {r['rows_with_where_field']} of them, by wording on the rest]")
    print(f"practicals: issued {r['practical_issued']}  graded {r['practical_graded']}  "
          f"attempted {r['practical_attempted']}  done {r['practical_done']}")
    print("D-0640 (a) window share > %d%%: %s" % (WINDOW_SHARE_LIMIT * 100,
          "REVISIT" if r["defeater_a_window_share_over_limit"] else ("HOLDS" if sh is not None else "no observation lessons")))
    print("D-0640 (b) practicals not done: %s" % ("REVISIT" if r["defeater_b_practicals_not_done"] else "HOLDS"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
