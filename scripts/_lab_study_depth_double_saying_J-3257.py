"""
Replay (read-only, offline, no model): does the nearness-said FIRE clause that J-3257 / D-0648 puts into the study
scene line say the same warmth as thermal's felt-warmth channel (J-2254 question 5, D-0648's double-saying check)?

Inputs (never written): data/spatial_depth_shadow.jsonl (one row per study scene cycle; `depth_line` is the line the
renderer said, `fire.band` close/mid/faint, `fire.state`) and data/thermal_percepts_shadow.jsonl (thermal's own
per-cycle row; `line` + `delivered` where the channel put an EVENT line in front of him -- thermal delivers
transitions and gradients, never a standing clause, D-0047).

For every study depth row whose fire clause says a warmth (the clause carries 'warm' or 'heat'), look for a thermal
row for the same place within +-WINDOW seconds that DELIVERED a line, and classify it warmer / colder / other:
  same     fire clause says warmth AND thermal delivered a warming line in the window (the two say the same thing)
  opposed  fire clause says warmth AND thermal delivered a COOLING line in the window (a contradiction)
  none     no delivered thermal line in the window
The D-0648 defeater: revisit if `same` is over 20 percent of study lines carrying a fire clause.

  python scripts/_lab_study_depth_double_saying_J-3257.py [--dir <folder with the two jsonl files>] [--window 90]
"""
from __future__ import annotations

import argparse
import bisect
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ap = argparse.ArgumentParser()
ap.add_argument("--dir", default=r"C:\Nascence\data", help="folder holding the two jsonl files (read only)")
ap.add_argument("--window", type=float, default=90.0)
a = ap.parse_args()
D = Path(a.dir)

WARM = re.compile(r"\bwarm|\bheat", re.I)
T_WARM = re.compile(r"warmer|warmed|warming|eases off|warm now|has warmed", re.I)
T_COLD = re.compile(r"colder|cooled|cooling|cold now|has cooled", re.I)


def rows(name):
    out = []
    for ln in open(D / name, encoding="utf-8"):
        ln = ln.strip()
        if ln:
            try:
                out.append(json.loads(ln))
            except Exception:
                pass
    return out


depth = [r for r in rows("spatial_depth_shadow.jsonl") if r.get("room", "study") == "study" and r.get("fire")]
therm = [r for r in rows("thermal_percepts_shadow.jsonl")
         if r.get("place") == "study" and r.get("delivered") and r.get("line")]
therm.sort(key=lambda r: r["ts"])
tts = [r["ts"] for r in therm]


def fire_clause(line: str) -> str:
    for part in (line or "").split("; "):
        p = part.split(" — ", 1)
        if "the fire is" in part or "the embers are" in part:
            return part
    return ""


stats = {"rows_with_fire": 0, "clause_says_warmth": 0, "same": 0, "opposed": 0, "none": 0}
by_band = {}
for r in depth:
    stats["rows_with_fire"] += 1
    fc = fire_clause(r.get("depth_line") or "")
    # a 'faint' clause says the warmth is NOT reaching him ("little of its warmth gets this far"), so it cannot repeat a
    # thermal warming line; it is counted under rows_with_fire only. close/mid clauses are the ones that say a warmth.
    if not (fc and WARM.search(fc)) or (r["fire"] or {}).get("band") == "faint":
        continue
    stats["clause_says_warmth"] += 1
    lo, hi = bisect.bisect_left(tts, r["ts"] - a.window), bisect.bisect_right(tts, r["ts"] + a.window)
    near = therm[lo:hi]
    same = any(T_WARM.search(x["line"]) for x in near)
    opp = any(T_COLD.search(x["line"]) and not T_WARM.search(x["line"]) for x in near)
    k = "same" if same else ("opposed" if opp else "none")
    stats[k] += 1
    b = (r["fire"] or {}).get("band", "?")
    by_band.setdefault(b, {"same": 0, "opposed": 0, "none": 0})[k] += 1

n = stats["rows_with_fire"]
w = stats["clause_says_warmth"]
print(f"study depth rows with a fire        : {n}")
print(f"  of them, fire clause says a warmth (close/mid) : {w}")
print(f"  thermal delivered a WARMING line in +-{a.window:.0f}s (the two say the same): {stats['same']}"
      f"  = {100.0 * stats['same'] / max(1, n):.1f}% of study lines with a fire, {100.0 * stats['same'] / max(1, w):.1f}% of warmth-saying clauses")
print(f"  thermal delivered a COOLING line (opposed)                : {stats['opposed']}")
print(f"  no delivered thermal line in the window                   : {stats['none']}")
print("  by fire band:", json.dumps(by_band))
print("delivered thermal study lines in the file:", len(therm))
share = 100.0 * stats["same"] / max(1, n)
print(f"\nD-0648 defeater (revisit if > 20% of study lines): {'TRIPPED' if share > 20.0 else 'not tripped'} ({share:.1f}%)")
