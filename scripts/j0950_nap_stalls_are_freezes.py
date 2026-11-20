"""
J-0950 / Thread 2: are Du's "nap" silences (log-silent windows of 10-30 min inside a live process, about every 70-75 min at
night) real PROCESS-WIDE FREEZES, or just quiet?  Test: count the rows the other instrumented loops publish inside them.

READ-ONLY on data/coupling_rides.jsonl (every loop publishes there: climate at a >= 1/min floor, stream every few seconds, witness,
deliberation per cycle).  Input: the event file from scripts/j0950_parse_cycle_events.py.  A stall counts as a nap when it is a
silent window >= --min-stall seconds that does NOT abut a shutdown/boot line (those are outages, not naps).

NOTE (2026-10-03, J-0950 takeover): the local-time conversion in this script is a FIXED UTC+12 and is only valid for windows that end before
2026-09-27 02:00 NZST.  NZ daylight saving (UTC+13) began then: a window after it is one hour out of register against coupling_rides.jsonl
(epoch UTC), and the parser records the jump itself as a fake 60-minute silent window.  For anything later use
scripts/j0950_post_j1180_replication.py, whose utc() applies the right offset and is checked against the log (section 0 of its output).

Usage: python scripts/j0950_nap_stalls_are_freezes.py --events <events.jsonl> [--lo 2026-09-10T00:00 --hi 2026-09-11T13:00]
"""
from __future__ import annotations

import argparse
import bisect
import datetime as dt
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

OFF = dt.date(1970, 1, 1).toordinal() * 86400 + 12 * 3600      # epoch UTC -> local seconds (UTC+12, no DST before 2026-09-27)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", required=True)
    ap.add_argument("--rides", default=r"C:\Nascence\data\coupling_rides.jsonl")
    ap.add_argument("--lo", default="2026-09-10T00:00")
    ap.add_argument("--hi", default="2026-09-11T13:00")
    ap.add_argument("--min-stall", type=float, default=600.0)
    a = ap.parse_args()

    def loc(s):
        d = dt.datetime.fromisoformat(s)
        return d.date().toordinal() * 86400 + d.hour * 3600 + d.minute * 60
    lo, hi = loc(a.lo), loc(a.hi)
    ev = [json.loads(l) for l in open(a.events, encoding="utf-8")]
    boots = [e["t"] for e in ev if e["k"] == "boot"]
    shuts = [e["t"] for e in ev if e["k"] == "shut"]
    naps = [(e["t"], e["t2"]) for e in ev if e["k"] == "silent" and e["t2"] - e["t"] >= a.min_stall
            and not any(abs(s - e["t"]) < 2 for s in shuts) and not any(e["t2"] - 5 <= b <= e["t2"] + 90 for b in boots)]
    win = [(x, y) for (x, y) in naps if lo <= x < hi]
    rows = {"climate": [], "stream": [], "witness": [], "deliberation": [], "ledgers": []}
    with open(a.rides, encoding="utf-8") as f:                    # read-only
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            k = r.get("loop")
            if k in rows:
                t = r["ts"] + OFF
                if lo <= t < hi:
                    rows[k].append(t)
    print(f"window {a.lo} .. {a.hi} (local); nap stalls >= {a.min_stall:.0f} s not abutting a restart: {len(win)}, total {sum(y - x for x, y in win) / 60:.0f} min, "
          f"lengths (min): " + ", ".join(f"{(y - x) / 60:.1f}" for x, y in win))
    for k, v in rows.items():
        v.sort()
        inside = sum(bisect.bisect_left(v, y) - bisect.bisect_right(v, x) for (x, y) in win)
        print(f"  {k:<13} rows in window {len(v):5d}; rows INSIDE the stalls: {inside}" + (f" (climate floor expects {sum((y - x) / 60 for x, y in win):.0f})" if k == "climate" else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
