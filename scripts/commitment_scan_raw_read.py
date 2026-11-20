"""J-2848 / F-3511 (P-0038, P-0037): read the commitment scan raw log and the defeater judge's own class mix.

READ-ONLY. No core/ import, no model call. Reads
  data/commitment_scan_raw.jsonl          one row per scan (null scans included): outcome null / formed / reaffirmed /
                                          observed / dissolved_only / no_reply / error, plus the raw parsed reply
  data/commitment_attempts_shadow.jsonl   one row per defeater-judge ask (J-3158/D-0546), with the judge's own class + why.
                                          This is where J-2848's "keep the judge's class and why" lives; no separate
                                          commitment_judge_shadow.jsonl was written (it would duplicate these rows).
Prints outcome rates, the judge's class mix and verdict mix, and an accounting line against scans seen in the window.
Usage: python scripts/commitment_scan_raw_read.py [--root PATH] [--since-days 7]
"""
import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def jl(path):
    rows = []
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass
    except OSError:
        pass
    return rows


def pct(n, d):
    return f"{100.0 * n / d:.1f}%" if d else "n/a"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(Path(__file__).resolve().parent.parent))
    ap.add_argument("--since-days", type=float, default=7.0)
    a = ap.parse_args(argv)
    data = Path(a.root) / "data"
    cut = time.time() - a.since_days * 86400
    scans = [r for r in jl(data / "commitment_scan_raw.jsonl") if float(r.get("ts", 0)) >= cut]
    judge = [r for r in jl(data / "commitment_attempts_shadow.jsonl") if float(r.get("ts", 0)) >= cut]
    print(f"window: last {a.since_days:g} days   root: {a.root}")
    print(f"scan rows: {len(scans)}")
    if scans:
        oc = Counter(r.get("outcome") or "error" for r in scans)
        for k, n in oc.most_common():
            print(f"  {k:<15} {n:>6}  {pct(n, len(scans))}")
        print(f"  raw reply null/empty: {sum(1 for r in scans if not r.get('raw'))}  "
              f"new_commitment present in raw: {sum(1 for r in scans if r.get('new_commitment_present'))}  "
              f"dissolutions proposed in raw: {sum(int(r.get('n_dissolutions_raw', 0)) for r in scans)}  "
              f"dissolutions applied: {sum(int(r.get('n_dissolved', 0)) for r in scans)}")
        lat = sorted(float(r.get("latency_s", 0)) for r in scans)
        print(f"  latency_s median {lat[len(lat) // 2]:.2f}  max {lat[-1]:.2f}")
    print(f"judge rows: {len(judge)}")
    if judge:
        print("  verdict:", dict(Counter(str(r.get("verdict")) for r in judge).most_common()))
        print("  class:  ", dict(Counter(r.get("judge_class") or "(none)" for r in judge).most_common()))
        print("  error:  ", dict(Counter(r.get("error") or "(none)" for r in judge).most_common()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
