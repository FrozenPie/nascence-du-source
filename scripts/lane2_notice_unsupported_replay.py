"""
D-0417 (J-2102) -- replay `core/lane2_notice_unsupported.check_unsupported` over the Lane 2 shadow log, READ-ONLY.

Every tick row with a notice and logged percept_lines is re-checked (the logged notice is the full text since the
J-2101 NOTICE_LOG_CAP raise; older rows were cut at 400 chars, so a mention past char 400 is invisible there).
Prints the flagged share, per-noun counts, logged-vs-replay agreement on rows that already carry a logged
`notice_unsupported`, and (with --sample N --seed S) N flagged rows for a hand-check.

Run: python scripts/lane2_notice_unsupported_replay.py [--log PATH] [--since TS] [--sample N --seed S]
"""
from __future__ import annotations

import argparse
import collections
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.lane2_notice_unsupported import check_unsupported  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default=str(ROOT / "data" / "lane2_shadow.jsonl"))
    ap.add_argument("--since", type=float, default=0.0)
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--seed", type=int, default=2102)
    a = ap.parse_args()
    rows, flagged, nouns, negated, sup = [], [], collections.Counter(), collections.Counter(), collections.Counter()
    agree = disagree = 0
    with open(a.log, encoding="utf-8") as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if not r.get("notice") or not r.get("percept_lines") or float(r.get("ts") or 0) < a.since:
                continue
            res = check_unsupported(r["notice"], r["percept_lines"])
            rows.append(r)
            nouns.update(res["nouns"])
            negated.update(res["negated"])
            sup.update(res["supported_by"].keys())
            if res["flag"]:
                flagged.append((r, res))
            logged = r.get("notice_unsupported")
            if isinstance(logged, dict) and logged.get("how") == "deterministic":
                if bool(logged.get("flag")) == res["flag"] and logged.get("nouns") == res["nouns"]:
                    agree += 1
                else:
                    disagree += 1
    n = len(rows)
    print(f"rows {n}  flagged {len(flagged)}  rate {len(flagged) / n:.4f}" if n else "rows 0")
    print("unsupported nouns:", dict(nouns.most_common()))
    print("supported nouns:  ", dict(sup.most_common()))
    print("negated nouns:    ", dict(negated.most_common()))
    print(f"logged-vs-replay: agree {agree} disagree {disagree}")
    distinct = collections.Counter(r["notice"].strip() for r, _ in flagged)
    print(f"distinct flagged notices {len(distinct)}; most repeated: {distinct.most_common(1)}")
    if a.sample and flagged:
        for r, res in random.Random(a.seed).sample(flagged, min(a.sample, len(flagged))):
            print(f"\n-- ts {r.get('ts')}  nouns {res['nouns']}  supported {res['supported_by']}")
            print("NOTICE:", r["notice"])
            print(r["percept_lines"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
