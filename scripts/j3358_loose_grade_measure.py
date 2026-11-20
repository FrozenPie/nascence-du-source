"""
J-3358 (D-0582): measure how many logged maths-drill rows were graded CORRECT under the old loose grader although the
declared answer field was wrong, and confirm the strict answer-field grader (J-2988) now in core/math_drill.py.
READ-ONLY on the log (opened for reading). Writes only the report to --out if given.
  python scripts/j3358_loose_grade_measure.py [--log C:/Nascence/data/math_drill_log.jsonl] [--since 2026-10-01] [--out FILE]
For each row: field = raw_answer if the row has it else his_answer. strict = math_drill.grade(field, true) (last number in
the answer field). loose_pass_wrong = logged correct==True but strict==False. Also the reverse (strict pass, logged miss),
which is the taught re-attempt landing in his_answer on legacy rows.
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
import core  # noqa: E402,F401  BEFORE lab_env
from core import math_drill  # noqa: E402


def main(log: Path, since: float, out: Path | None) -> int:
    tab = defaultdict(lambda: defaultdict(int))
    wrong_examples = []
    with open(log, encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("ts", 0) < since:
                continue
            legacy = "raw_answer" not in r
            field = r.get("his_answer", "") if legacy else r.get("raw_answer", "")
            strict = math_drill.grade(field, r.get("true"))
            logged = bool(r.get("correct"))
            t = tab[r.get("level")]
            t["n"] += 1
            t["logged_correct"] += logged
            t["strict_correct"] += strict
            t["loose_pass_wrong"] += (logged and not strict)
            t["strict_pass_logged_miss"] += (strict and not logged)
            t["legacy"] += legacy
            if logged and not strict and len(wrong_examples) < 25:
                wrong_examples.append({"level": r.get("level"), "problem": r.get("problem"), "true": r.get("true"),
                                       "field": str(field)[:60], "legacy": legacy})
    lines = [f"log={log} since={datetime.datetime.fromtimestamp(since):%Y-%m-%d}",
             "level      n  logged_ok  strict_ok  loose_pass_wrong  strict_ok_logged_miss  legacy"]
    tot = defaultdict(int)
    for lv in sorted(tab, key=lambda x: (x is None, x)):
        t = tab[lv]
        lines.append(f"{lv!s:>5} {t['n']:6d} {t['logged_correct']:10d} {t['strict_correct']:10d} {t['loose_pass_wrong']:17d}"
                     f" {t['strict_pass_logged_miss']:22d} {t['legacy']:7d}")
        for k, v in t.items():
            tot[k] += v
    lines.append(f"  all {tot['n']:6d} {tot['logged_correct']:10d} {tot['strict_correct']:10d} {tot['loose_pass_wrong']:17d}"
                 f" {tot['strict_pass_logged_miss']:22d} {tot['legacy']:7d}")
    hi = sum(tab[l]["loose_pass_wrong"] for l in tab if l and l >= 10)
    hn = sum(tab[l]["n"] for l in tab if l and l >= 10)
    lines.append(f"levels >= 10: n={hn}, loose_pass_wrong={hi}")
    for e in wrong_examples:
        lines.append("  e.g. " + json.dumps(e, ensure_ascii=False))
    txt = "\n".join(lines)
    print(txt)
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(txt + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default=r"C:\Nascence\data\math_drill_log.jsonl")
    ap.add_argument("--since", default="2026-10-01")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    since = datetime.datetime.strptime(a.since, "%Y-%m-%d").timestamp()
    sys.exit(main(Path(a.log), since, Path(a.out) if a.out else None))
