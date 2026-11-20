"""
READER for data/refinery_faithfulness.jsonl (D-0627, J-3238 phase 1). Read-only.

Prints: how many standing insights the cross-family judge has graded, the pass rate, the D-0627 defeater check
(over 95% or under 20% = the judge carries no information), pass rate by cluster size and evolving/new, judge
errors, and the failed insights (read ~10 with the founder if the judge flags a real share). The withhold-or-lower-
standing decision is NOT taken here: after FAITH_PHASE1_N judged insights, file it as a needs_input job.

Run from the repo root:  python scripts/refinery_faithfulness_report.py [--log PATH] [--fails N]
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
    ap.add_argument("--log", default=str(ROOT / "data" / "refinery_faithfulness.jsonl"))
    ap.add_argument("--fails", type=int, default=10, help="how many failed insights to print")
    a = ap.parse_args()
    from core import refinery
    st = refinery.faithfulness_status(a.log)
    print("status:", json.dumps(st))
    if not st.get("rows"):
        print("no rows yet: the judge has not graded an insight (Du restart from a merged master needed, then a sleep refinery run)")
        return 0
    rows = [json.loads(l) for l in open(a.log, encoding="utf-8") if l.strip()]
    judged = [r for r in rows if isinstance(r.get("supported"), bool)]
    n = refinery.FAITH_PHASE1_N
    print(f"judged {len(judged)} of the {n} needed for the phase-1 review"
          + (" -> REVIEW POINT REACHED: report this and file the withhold-or-lower-standing decision as needs_input" if len(judged) >= n else ""))
    if st.get("no_information"):
        print("D-0627 DEFEATER MET: pass rate outside 20%..95% -> the judge carries no information; revisit with the founder (drop to archive level)")

    def rate(rs):
        return f"{sum(1 for r in rs if r['supported'])}/{len(rs)}" if rs else "0/0"

    print("by new vs evolving:", "new", rate([r for r in judged if not r.get("evolving")]),
          "evolving", rate([r for r in judged if r.get("evolving")]))
    for lo, hi in ((0, 8), (9, 20), (21, 100), (101, 10 ** 9)):
        print(f"by cluster size {lo}-{hi}:", rate([r for r in judged if lo <= (r.get("members_total") or 0) <= hi]))
    errs: dict = {}
    for r in rows:
        if r.get("err"):
            errs[r["err"]] = errs.get(r["err"], 0) + 1
    print("judge errors:", errs or "none")
    fails = [r for r in judged if not r["supported"]]
    print(f"failed insights ({len(fails)}), first {a.fails}:")
    for r in fails[: a.fails]:
        print(f"  [{r.get('fragment_id')}] fid={r.get('fidelity')} n={r.get('members_total')} :: {r.get('insight', '')[:200]}")
        print(f"      why: {r.get('why')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
