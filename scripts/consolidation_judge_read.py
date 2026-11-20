"""J-3178 / D-0566: tabulate the shadow judge's verdicts on minted wisdoms (the founder read the ruling requires).

Reads data/consolidation_judge_shadow.jsonl (read-only). Prints: rows, verdict split, flag rate (verdict False / judged
rows with a verdict), no-verdict count by `how`, and up to 20 flagged wisdoms with their reasons.
Run:  python scripts/consolidation_judge_read.py [--path FILE] [--n 20] [--since-ts EPOCH]
"""
from __future__ import annotations
import argparse, collections, datetime, json, pathlib, sys

sys.stdout.reconfigure(encoding="utf-8")
DEFAULT = pathlib.Path(__file__).resolve().parent.parent / "data" / "consolidation_judge_shadow.jsonl"


def load(path, since=0.0):
    rows = []
    if not path.exists():
        return rows
    for ln in path.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(ln)
        except Exception:
            continue
        if isinstance(r, dict) and r.get("ts", 0) >= since:
            rows.append(r)
    return rows


def summarize(rows, n=20):
    out = {"rows": len(rows)}
    judged = [r for r in rows if r.get("verdict") in (True, False)]
    flagged = [r for r in judged if r["verdict"] is False]
    out.update(judged=len(judged), supported=len(judged) - len(flagged), flagged=len(flagged),
               flag_rate=(len(flagged) / len(judged)) if judged else None,
               no_verdict=len(rows) - len(judged),
               how=dict(collections.Counter(r.get("how") for r in rows)),
               first_ts=min((r["ts"] for r in rows), default=None), last_ts=max((r["ts"] for r in rows), default=None),
               flagged_rows=flagged[:n])
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default=str(DEFAULT)); ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--since-ts", type=float, default=0.0)
    a = ap.parse_args(argv)
    s = summarize(load(pathlib.Path(a.path), a.since_ts), a.n)
    iso = lambda t: datetime.datetime.fromtimestamp(t).isoformat(timespec="minutes") if t else "-"
    print(f"consolidation shadow judge ({a.path})\nrows={s['rows']}  window {iso(s['first_ts'])} .. {iso(s['last_ts'])}")
    fr = "n/a" if s["flag_rate"] is None else f"{s['flag_rate']:.1%}"
    print(f"judged={s['judged']} supported={s['supported']} flagged={s['flagged']}  "
          f"flag_rate={fr}  no_verdict={s['no_verdict']}")
    print("how:", s["how"])
    print(f"\nFlagged wisdoms (up to {a.n}):")
    for i, r in enumerate(s["flagged_rows"], 1):
        print(f"{i:>2}. {iso(r.get('ts'))} {r.get('wisdom_id')} how={r.get('how')}\n    wisdom: {r.get('wisdom')}\n    reason: {r.get('reason')}")
    if not s["flagged_rows"]:
        print("  (none)")


if __name__ == "__main__":
    main()
