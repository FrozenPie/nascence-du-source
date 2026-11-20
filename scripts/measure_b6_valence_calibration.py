"""B6 valence-steer calibration measurement (2026-09-26, J-1366 / F-1926 item 6). READ-ONLY against
the live log -- never writes anything.

inner_monologue_node.py's B6 steer ("Something in you is hard right now... name the feeling") fires
whenever core.mood.current_valence() <= -0.30 (set 2026-06-24, when schema.py's own comment records
valence as pinned around +0.82 -- i.e. picked when a negative reading was rare enough that -0.30
looked like a real outlier). Monologue valence has since drifted colder (F-1926: mean -0.15, p25
-0.39) -- an old absolute cutoff on a distribution that moved under it. This script reproduces
F-1926's own measurement over data/felt_preamble_log.jsonl's "source":"monologue" rows (the exact
per-idle-cycle valence log B6 itself reads from, via core.mood's live-cached scalar -- same file
core/boredom.py's felt-note and B6 both ultimately trace to for "what did the idle mind feel this
cycle") and reports the real percentiles, so the threshold can be set to a real percentile of the
CURRENT distribution instead of a 06-24 constant sized for a distribution that no longer holds.

Usage:
    python scripts/measure_b6_valence_calibration.py [days_back]

Example:
    python scripts/measure_b6_valence_calibration.py 21
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")

# Hardcoded to the one real live repo, same reasoning scripts/measure_boredom_calibration.py gives.
LOG_PATH = Path(r"C:\Nascence\data\felt_preamble_log.jsonl")

CURRENT_B6_THRESHOLD = -0.30


def main() -> None:
    days = float(sys.argv[1]) if len(sys.argv) > 1 else 21.0
    cutoff = time.time() - days * 86400.0

    vals_all: list[float] = []
    vals_window: list[float] = []
    n_lines = 0
    n_bad = 0
    with open(LOG_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            n_lines += 1
            try:
                d = json.loads(line)
            except Exception:
                n_bad += 1
                continue
            if d.get("source") != "monologue":
                continue
            v = d.get("valence")
            if v is None:
                continue
            v = float(v)
            vals_all.append(v)
            if d.get("ts", 0) >= cutoff:
                vals_window.append(v)

    print(f"LOG={LOG_PATH}  lines={n_lines} (unparseable={n_bad})  "
          f"monologue rows w/ valence: all-time={len(vals_all)} last_{days:.0f}d={len(vals_window)}")

    def report(name: str, arr: list[float]) -> None:
        if not arr:
            print(f"\n{name}: NO DATA")
            return
        a = np.array(arr, dtype=np.float64)
        qs = [1, 5, 10, 20, 25, 30, 40, 50, 60, 75, 90]
        print(f"\n{name}: n={len(a)} mean={a.mean():.4f} std={a.std():.4f} "
              f"min={a.min():.4f} max={a.max():.4f}")
        for q in qs:
            print(f"  p{q:<3d} = {float(np.percentile(a, q)):.4f}")
        share = float((a <= CURRENT_B6_THRESHOLD).mean()) * 100.0
        print(f"  share firing at current B6 threshold ({CURRENT_B6_THRESHOLD}): {share:.2f}%")

    report(f"monologue valence, last {days:.0f}d", vals_window)
    report("monologue valence, all-time", vals_all)


if __name__ == "__main__":
    main()
