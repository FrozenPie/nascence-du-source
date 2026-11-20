"""Read-only reader for data/pursuits_judged.jsonl (J-3000 / F-3700): what each pursuit ruling was ABOUT.

One row per pending item core/pursuits.judge_pending resolved: the judged thought (sha + first 200 chars), the
pursuit's prior standing, the panel's verdict/how/why, and ruled_ts. Joins each row to its panel row in
data/judge_panel_log.jsonl (key=advances, context=pursuit:<id>, nearest ts at or before ruled_ts) so a refuted
or confirmed advance can finally be read as a (prior position, new thought, verdict) triple.

    python scripts/pursuits_judged_read.py                 # summary + the last 10 rows
    python scripts/pursuits_judged_read.py --pursuit ID    # one pursuit's rows
    python scripts/pursuits_judged_read.py --refuted -n 20 # only refuted advances
    python scripts/pursuits_judged_read.py --data DIR      # read another data directory (default: ../data)

Never writes anything."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent


def _rows(path: Path) -> list:
    out = []
    try:
        for ln in path.read_text(encoding="utf-8").splitlines():
            try:
                out.append(json.loads(ln))
            except Exception:
                pass
    except Exception:
        pass
    return out


def join_panel(rows: list, panel_rows: list, slack_s: float = 120.0) -> list:
    """Attach the nearest earlier panel row (key=advances, same pursuit context) to each judged row as 'panel'.
    Pure; a row with no panel row within slack_s gets panel=None."""
    by_ctx: dict = {}
    for r in panel_rows:
        if r.get("key") == "advances" and str(r.get("context", "")).startswith("pursuit:"):
            by_ctx.setdefault(r["context"], []).append(r)
    out = []
    for r in rows:
        cand = [x for x in by_ctx.get(f"pursuit:{r.get('pursuit_id')}", [])
                if 0 <= float(r.get("ruled_ts") or 0) - float(x.get("ts") or 0) <= slack_s]
        out.append(dict(r, panel=max(cand, key=lambda x: x.get("ts", 0)) if cand else None))
    return out


def summarise(rows: list) -> dict:
    return {"rows": len(rows),
            "verdict": dict(Counter(str(r.get("verdict")) for r in rows)),
            "how": dict(Counter(str(r.get("how")) for r in rows)),
            "dropped": sum(1 for r in rows if r.get("dropped")),
            "pursuits": len({r.get("pursuit_id") for r in rows}),
            "distinct_thoughts": len({r.get("thought_sha") for r in rows})}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(ROOT / "data"))
    ap.add_argument("--pursuit", default="")
    ap.add_argument("--refuted", action="store_true")
    ap.add_argument("-n", type=int, default=10)
    a = ap.parse_args(argv)
    d = Path(a.data)
    rows = _rows(d / "pursuits_judged.jsonl")
    if a.pursuit:
        rows = [r for r in rows if r.get("pursuit_id") == a.pursuit]
    if a.refuted:
        rows = [r for r in rows if r.get("verdict") is False]
    print(json.dumps(summarise(rows), ensure_ascii=False))
    panel = _rows(d / "judge_panel_log.jsonl") if rows else []
    for r in join_panel(rows[-a.n:], panel):
        pr = r.get("panel") or {}
        print(f"\n[{r.get('pursuit_id')}] verdict={r.get('verdict')} how={r.get('how')} sha={r.get('thought_sha')}"
              f"{' DROPPED' if r.get('dropped') else ''}  panel_how={pr.get('how')}")
        print(f"  Q    : {r.get('question')}")
        print(f"  PRIOR: {r.get('prior_standing')}")
        print(f"  THINK: {r.get('thought')}")
        print(f"  WHY  : {r.get('why') or pr.get('why1')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
