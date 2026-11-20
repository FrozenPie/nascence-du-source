#!/usr/bin/env python
"""Offline replay / read tool for the Lane 2 deterministic notice checker (D-0361(a), J-1896, 2026-10-07).

READ-ONLY and OFFLINE: opens the shadow log for reading, imports only the pure checker (no hub, no LLM, no network,
no write to any store).  Two jobs:

  1. REPLAY: re-run `core.lane2_notice_check.check_notice` over every logged tick row that carries `percept_lines`
     and a notice (the checker is a pure function of exactly those two strings, so a replay equals what a live tick
     would have logged), and report counts -- overall, over the panel-judged rows, and the 2x2 against the panel's
     own `notice_judged` verdict.  This is how the 55 judged rows were read the day the checker was built.
  2. LIVE ROWS: when rows already carry a logged `notice_checked` (after Du's next restart), report the logged
     verdicts too and whether they agree with a fresh replay (a drift detector for the checker itself).

  --sample N [--seed S]   print N seeded flagged rows (percept lines + notice + flags) for the 20-row HAND-CHECK that
                          D-0361's defeater asks for (more than 4 false flags of 20 reopens the decision).  Only rows
                          the panel did NOT judge are drawn by default (--include-judged to draw from all), so the
                          sample is out-of-sample for rules that were written while reading the 55 judged rows.
  --since ISO             only rows at or after this UTC timestamp (e.g. the first post-restart tick).

    python scripts/lane2_notice_check_replay.py --shadow C:/Nascence/data/lane2_shadow.jsonl --sample 20 --seed 1896
"""
import argparse
import collections
import datetime
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.stdout.reconfigure(encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--shadow", required=True)
    ap.add_argument("--since", default="", help="ISO UTC timestamp; only rows at or after it")
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--seed", type=int, default=1896)
    ap.add_argument("--include-judged", action="store_true")
    a = ap.parse_args()

    import core                                    # noqa: F401  (import before anything under core)
    from core import lane2_notice_check as nc
    assert os.path.realpath(core.__file__).lower().startswith(os.path.realpath(ROOT).lower()), core.__file__

    since = 0.0
    if a.since:
        since = datetime.datetime.fromisoformat(a.since.replace("Z", "+00:00")).timestamp()

    rows = []
    with open(a.shadow, encoding="utf-8", errors="replace") as f:       # read-only
        for line in f:
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("kind") != "tick" or not r.get("percept_lines") or not (r.get("notice") or "").strip():
                continue
            if float(r.get("ts") or 0) < since:
                continue
            nj = (r.get("notice_judged") or {}).get("verdict")
            rows.append({"ts": r.get("ts"), "notice": r["notice"], "pl": r["percept_lines"], "panel": nj,
                         "logged": r.get("notice_checked")})
    for r in rows:
        r["res"] = nc.check_notice(r["notice"], r["pl"])

    def answered(r):
        return r["res"]["verdict"] in ("contradiction", "consistent")

    ans = [r for r in rows if answered(r)]
    fl = [r for r in ans if r["res"]["verdict"] == "contradiction"]
    solid = [r for r in fl if r["res"].get("n_solid")]
    judged = [r for r in ans if r["panel"] in ("contradiction", "consistent")]
    jfl = [r for r in judged if r["res"]["verdict"] == "contradiction"]
    pc = sum(1 for r in judged if r["panel"] == "contradiction")
    both = sum(1 for r in jfl if r["panel"] == "contradiction")
    summary = {
        "rows_with_notice_and_percept_lines": len(rows), "checker_answered": len(ans),
        "flagged": len(fl), "flag_rate": round(len(fl) / len(ans), 3) if ans else None,
        "flagged_solid": len(solid), "solid_rate": round(len(solid) / len(ans), 3) if ans else None,
        "kinds": dict(collections.Counter(k for r in fl for k in r["res"]["kinds"])),
        "panel_judged_rows": len(judged), "panel_contradictions": pc,
        "checker_flagged_among_judged": len(jfl), "both_flagged": both,
        "checker_only": len(jfl) - both, "panel_only": pc - both,
    }
    logged = [r for r in rows if isinstance(r["logged"], dict) and r["logged"].get("verdict")]
    if logged:
        summary["logged_notice_checked_rows"] = len(logged)
        summary["logged_vs_replay_disagree"] = sum(1 for r in logged if r["logged"]["verdict"] != r["res"]["verdict"]
                                                    and r["logged"]["verdict"] != "not_checked")
    print(json.dumps(summary, indent=1))

    if a.sample:
        pool = [r for r in fl if a.include_judged or r["panel"] not in ("contradiction", "consistent")]
        random.Random(a.seed).shuffle(pool)
        print(f"\n--- hand-check sample: {min(a.sample, len(pool))} of {len(pool)} flagged rows (seed {a.seed}) ---")
        for i, r in enumerate(pool[:a.sample]):
            pl = r["pl"].split("\n", 1)[-1].replace("\n- ", " | ").lstrip("- ")
            print(f"\n[{i}] ts={r['ts']}  panel={r['panel']}\n  PERCEPTS: {pl}\n  NOTICE:   {r['notice']}")
            for f in r["res"]["flags"]:
                print(f"  FLAG {f['kind']}{' (weak)' if f.get('weak') else ''}: said {f['said']!r} vs {f['listed']}")


if __name__ == "__main__":
    main()
