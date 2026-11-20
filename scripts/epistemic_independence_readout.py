#!/usr/bin/env python
"""READ-ONLY readout of the Epistemic Independence metric: the Phase-1 exit gate of
docs/plans/investigative_action_loop_plan.md (Section 2 Principle D, Section 5 Invariant 9).

Committed by J-1776 (2026-10-04) to apply D-0326 (Travis, 2026-10-03: the 2026-08-14 no-hints law stands, Phase 2 /
Live Advisory Mode is never built, Principle D is reworded to this metric). It replaces the one-off scratchpad script
that produced the 2026-09-28 baseline (J-1619 / F-2193) and was never in the repo, so the number can be re-read as the
dataset grows. D-0326's own revisit trigger is "the closed-episode dataset grows enough that the numbers shift
materially": this prints the numbers and a human reads them. There is NO pass/fail threshold here, deliberately
(Invariant 9: a positive experimental variable, not a compliance target; Principle D carries none).

What it computes (zero live wiring; no hint is ever produced or shown to Du):
  For every REAL CLOSED EPISODE in data/investigative_action_log.jsonl -- a row whose confidence_explanation starts
  with "real (non-shadow) episode" (what core.epistemic_affordance_advisor.close_real_episode() writes) AND whose
  selection_source is "du" (the definition F-2193 used) -- re-run the advisor's own pure
  rank_epistemic_affordances(question, competing_hypotheses, location) on the STORED question, hypotheses and
  location, and compare with Du's recorded selected_affordance.
    hint-eligible  n   the advisor's top non-do_nothing candidate has IG >= INFORMATION_GAIN_THRESHOLD (0.30), i.e.
                       exactly the episodes where epistemic_advisory_hint() would have been non-empty had it ever
                       been called (it has zero call sites and must keep it; this script never calls it).
    top-match      k1  of the n: Du's own choice == the advisor's top-ranked family.
    any-match      k2  of the n: Du's own choice is ANY ranked non-do_nothing candidate.

How to read it (the plan's own caveats):
  * any-match is membership in the advisor's candidate list for that location: every Hand family registered there
    EXCEPT look and move, which core/epistemic_affordance_advisor.py's _real_candidate_families() deliberately
    leaves out. A choice of move can never match, so part of every mismatch is that documented vocabulary gap, not
    disagreement; the "outside the candidate list" line shows how much.
  * Stored rows are re-ranked under the CURRENT advisor code (the Hand registry in core/dispatch.py and the keyword
    tables in the advisor), not the ranking made at the time, so a shift between two snapshots can come from code
    changes as well as from new episodes.

Read-only by construction: the log is opened for reading only, nothing is written anywhere and the SQLite store is
never opened. It imports the advisor module for ONE pure function and never calls epistemic_advisory_hint(),
record_epistemic_episode() or close_real_episode(). Safe to run while Du is live (a torn last line is skipped).

Usage:  python scripts/epistemic_independence_readout.py [--log PATH]
        default log: the advisor's own LOG_JSONL_PATH (the live data/investigative_action_log.jsonl); --log lets a test
        or a copy be read instead.
Test:   python scripts/_test_j1776_epistemic_independence_readout.py
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core import epistemic_affordance_advisor as eaa  # noqa: E402  (the pure ranker, its 0.30 threshold, the log path)

# How close_real_episode() starts the confidence_explanation of every real closed episode.
REAL_PREFIX = "real (non-shadow) episode"
# The dated snapshot Principle D cites (F-2193), printed for reference only: no verdict is computed from it.
BASELINE = {"date": "2026-09-28", "finding": "F-2193", "real": 1317, "eligible": 128, "top": 34, "any": 66}


def is_real_closed_episode(row) -> bool:
    """F-2193's definition plus its explicit du clause: a row close_real_episode() produced, taken by Du himself.
    The passive shadow-ranking rows (advisor_shadow_only, and the pre-J-0180 mislabel system_suggestion) and the
    2026-08 test-fixture rows are not episodes Du closed."""
    if not isinstance(row, dict):
        return False
    return (str(row.get("confidence_explanation") or "").startswith(REAL_PREFIX)
            and row.get("selection_source") == "du")


def read_rows(path):
    """(parsed rows, count of unparseable lines). The only open() in this script, mode "r" -- the log is
    append-only and may be mid-write while Du runs, so a torn line is counted and skipped, never fatal."""
    rows, bad = [], 0
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except ValueError:
                bad += 1
    return rows, bad


def compute(path) -> dict:
    rows, bad = read_rows(path)
    prefix_rows = sum(1 for r in rows
                      if isinstance(r, dict) and str(r.get("confidence_explanation") or "").startswith(REAL_PREFIX))
    real = [r for r in rows if is_real_closed_episode(r)]
    threshold = eaa.INFORMATION_GAIN_THRESHOLD
    eligible = top_match = any_match = 0
    outside: Counter = Counter()
    for r in real:
        ranked = eaa.rank_epistemic_affordances(
            r.get("question") or "", r.get("competing_hypotheses") or [], r.get("location", "study"))
        candidates = [c for c in ranked if c["affordance"] != "do_nothing"]
        if not candidates:
            continue                      # unstructured, or no Hand family at this location: the advisor is silent
        top = max(candidates, key=lambda c: c["expected_information_gain"])
        if top["expected_information_gain"] < threshold:
            continue                      # below threshold: epistemic_advisory_hint() would have returned ""
        eligible += 1
        chosen = r.get("selected_affordance") or ""
        if chosen == top["affordance"]:
            top_match += 1
        if chosen in {c["affordance"] for c in candidates}:
            any_match += 1
        else:
            outside[chosen or "(none)"] += 1
    return {"lines": len(rows) + bad, "unparseable": bad, "prefix_rows": prefix_rows, "real": len(real),
            "eligible": eligible, "top": top_match, "any": any_match, "outside": outside}


def _pct(k: int, n: int) -> str:
    return f"{100.0 * k / n:.1f}%" if n else "n/a"


def format_report(res: dict, path, today: str) -> str:
    n_real, n, k1, k2 = res["real"], res["eligible"], res["top"], res["any"]
    out = [
        f"Epistemic Independence readout (READ-ONLY) -- snapshot date {today}",
        f"log: {path}  ({res['lines']} non-blank lines read, {res['unparseable']} unparseable skipped)",
        f"real closed episodes N: {n_real}   (confidence_explanation starts with {REAL_PREFIX!r} AND "
        f"selection_source == 'du'; the prefix alone matches {res['prefix_rows']})",
        f"hint-eligible n: {n} of {n_real} ({_pct(n, n_real)})   "
        f"(advisor's top non-do_nothing candidate IG >= {eaa.INFORMATION_GAIN_THRESHOLD:.2f})",
        f"top-match   k1/n: {k1}/{n} ({_pct(k1, n)})   Du's own choice == the advisor's top-ranked action",
        f"any-match   k2/n: {k2}/{n} ({_pct(k2, n)})   Du's own choice is any ranked non-do_nothing candidate",
    ]
    if res["outside"]:
        out.append("outside the advisor's candidate list (hint-eligible, not any-match): "
                   + ", ".join(f"{fam} {cnt}" for fam, cnt in res["outside"].most_common(8)))
    b = BASELINE
    out.append(f"reference only -- {b['date']} baseline ({b['finding']}): {b['eligible']}/{b['real']} hint-eligible "
               f"({_pct(b['eligible'], b['real'])}), top-match {b['top']}/{b['eligible']} "
               f"({_pct(b['top'], b['eligible'])}), any-match {b['any']}/{b['eligible']} "
               f"({_pct(b['any'], b['eligible'])})")
    out.append("NOTE: stored rows are re-ranked under the CURRENT advisor code (Hand registry + keyword tables), so a "
               "shift against another snapshot can come from code as well as from new episodes. There is no pass/fail "
               "threshold (Principle D / Invariant 9); whether the numbers moved materially is a founder read "
               "(D-0326 revisit trigger).")
    return "\n".join(out)


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--log", type=Path, default=eaa.LOG_JSONL_PATH,
                    help="investigative action log to read (default: the advisor's own LOG_JSONL_PATH)")
    args = ap.parse_args(argv)
    if not args.log.is_file():
        print(f"epistemic_independence_readout: log not found: {args.log}", file=sys.stderr)
        return 2
    print(format_report(compute(args.log), args.log, datetime.date.today().isoformat()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
