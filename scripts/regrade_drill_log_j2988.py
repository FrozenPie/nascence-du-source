"""
J-2988 (F-3685): regrade the music / maths drill logs with the answer-field-only graders in core/music_drill.py and
core/math_drill.py. READ-ONLY: it opens the logs for reading and prints a per-level table (logged verdict vs regraded
verdict); it writes nothing. This is the reader of the two keys the drill loggers now append (raw_answer, working_head):
a row that carries raw_answer is regraded from it (the whole answer field); an older row falls back to his_answer
(truncated to 60 / 40 chars at the time) and is counted under "legacy".
  python scripts/regrade_drill_log_j2988.py [--data-dir C:/Nascence/data] [--since 2026-11-07]
"""
import argparse
import datetime
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401  BEFORE anything that loads lab_env
from core import math_drill, music_drill  # noqa: E402


def _kind(true) -> str:
    t = str(true).strip()
    if t.lstrip("-").isdigit():
        return "number"
    return "notes3" if len(t.split()) > 1 else "note"


def _rows(path: Path, since: float):
    if not path.exists():
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("ts", 0) >= since:
                yield r


def regrade(which: str, path: Path, since: float) -> None:
    table = defaultdict(lambda: defaultdict(int))
    for r in _rows(path, since):
        legacy = "raw_answer" not in r
        field = r.get("his_answer", "") if legacy else r.get("raw_answer", "")
        if which == "music":
            new = music_drill.grade(field, str(r.get("true", "")), _kind(r.get("true", "")))
        else:
            new = math_drill.grade(field, r.get("true"))
        t = table[r.get("level")]
        t["n"] += 1
        t["logged_correct"] += bool(r.get("correct"))
        t["regraded_correct"] += bool(new)
        blank = not str(field).strip()
        t["blank_field"] += blank
        t["nonblank"] += not blank
        t["nonblank_correct"] += (not blank) and bool(new)
        t["legacy"] += legacy
    print(f"\n== {which}: {path}")
    print("level      n  logged_correct  regraded_correct  blank_field  legacy")
    tot = defaultdict(int)
    for lv in sorted(table, key=lambda x: (x is None, x)):
        t = table[lv]
        print(f"{lv!s:>5} {t['n']:6d} {t['logged_correct']:15d} {t['regraded_correct']:17d} {t['blank_field']:12d} {t['legacy']:7d}")
        for k, v in t.items():
            tot[k] += v
    if tot["n"]:
        print(f"  all {tot['n']:6d} {tot['logged_correct']:15d} {tot['regraded_correct']:17d} {tot['blank_field']:12d} {tot['legacy']:7d}"
              f"   logged {tot['logged_correct'] / tot['n']:.1%} -> regraded {tot['regraded_correct'] / tot['n']:.1%}"
              f" (blank fields would now be wobbles, skipped: {tot['nonblank_correct'] / max(tot['nonblank'], 1):.1%} of the {tot['nonblank']} non-blank)")
        print("  note: legacy rows hold his_answer = the TAUGHT re-attempt's answer when it landed, so a legacy row can regrade "
              "above its logged verdict; rows with raw_answer carry the independent attempt.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=r"C:\Nascence\data")
    ap.add_argument("--since", default="2000-01-01", help="YYYY-MM-DD; only rows from this date on")
    a = ap.parse_args()
    since = datetime.datetime.strptime(a.since, "%Y-%m-%d").timestamp()
    d = Path(a.data_dir)
    regrade("music", d / "music_drill_log.jsonl", since)
    regrade("math", d / "math_drill_log.jsonl", since)
