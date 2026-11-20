"""
J-0950 / Thread 2: is the climate loop SUSPENDED while an internal cycle is in flight?

core/climate_engine.py ClimateEngine.start_background awaits `_ignite(trigger)` -> `_ignition_callback` -> the orchestrator's
`_on_dissonance_ignition` -> `await self.run_cycle(question, input_type="internal")` (core/orchestrator.py:2825, the only
call site with input_type="internal").  If that reading is right, tick() (which also calls coupling_rides.publish_climate,
at a >= 1-per-minute floor) cannot run during an internal cycle, so a cheaper tick cannot speed one up.

Test (READ-ONLY on data/coupling_rides.jsonl; opens no other live file): for the window --lo .. --hi (local, UTC+12), take every
internal cycle whose span from the [climate] IGNITION line to its end ("complete in" / thalamic-gate silence) is >= 100 s, and count
the climate publish rows inside that span.  Control: windows of the same lengths placed at random OUTSIDE every internal-cycle span
and every nap stall (silent log window >= 300 s).

NOTE (2026-10-03, J-0950 takeover): the local-time conversion in this script is a FIXED UTC+12 and is only valid for windows that end before
2026-09-27 02:00 NZST.  NZ daylight saving (UTC+13) began then: a window after it is one hour out of register against coupling_rides.jsonl
(epoch UTC), and the parser records the jump itself as a fake 60-minute silent window.  For anything later use
scripts/j0950_post_j1180_replication.py, whose utc() applies the right offset and is checked against the log (section 0 of its output).

Input: the event file from scripts/j0950_parse_cycle_events.py.  Usage:
  python scripts/j0950_climate_rows_inside_cycles.py --events <events.jsonl> [--rides C:\\Nascence\\data\\coupling_rides.jsonl]
"""
from __future__ import annotations

import argparse
import bisect
import datetime as dt
import json
import random
import sys

sys.stdout.reconfigure(encoding="utf-8")

OFF = dt.date(1970, 1, 1).toordinal() * 86400 + 12 * 3600      # epoch UTC seconds -> "local seconds" (UTC+12, no DST before 2026-09-27)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", required=True)
    ap.add_argument("--rides", default=r"C:\Nascence\data\coupling_rides.jsonl")
    ap.add_argument("--lo", default="2026-09-10T00:00", help="local, window start")
    ap.add_argument("--hi", default="2026-09-11T13:00", help="local, window end (2026-09-11 13:18 is a shutdown, so stop before it)")
    a = ap.parse_args()

    def loc(s):
        d = dt.datetime.fromisoformat(s)
        return d.date().toordinal() * 86400 + d.hour * 3600 + d.minute * 60
    lo, hi = loc(a.lo), loc(a.hi)

    ev = [json.loads(l) for l in open(a.events, encoding="utf-8")]
    ign = sorted([e for e in ev if e["k"] == "ign"], key=lambda e: e["t"])
    it = [e["t"] for e in ign]
    starts = sorted([e for e in ev if e["k"] == "start" and e["type"] == "internal"], key=lambda e: e["t"])
    comp = {e["id"]: e for e in ev if e["k"] == "complete"}
    gate = {e["id"]: e for e in ev if e["k"] == "gate"}
    naps = [(e["t"], e["t2"]) for e in ev if e["k"] == "silent" and e["t2"] - e["t"] >= 300]

    spans = []
    for s in starts:
        j = bisect.bisect_right(it, s["t"]) - 1
        t0 = it[j] if j >= 0 and 0 <= s["t"] - it[j] <= 900 else s["t"]
        end = comp[s["id"]]["t"] if s["id"] in comp else (gate[s["id"]]["t"] if s["id"] in gate else s["t"])
        if lo <= t0 < hi:
            spans.append((t0, end))

    rows = []
    with open(a.rides, encoding="utf-8") as f:                    # read-only
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("loop") == "climate":
                t = r["ts"] + OFF
                if lo <= t < hi:
                    rows.append(t)
    rows.sort()

    def inside(x, y):
        return bisect.bisect_left(rows, y) - bisect.bisect_right(rows, x)

    def overlap(x, y, wins):
        return sum(max(0.0, min(y, w1) - max(x, w0)) for (w0, w1) in wins)

    full = [w for w in spans if w[1] - w[0] >= 100]
    exp = sum((w[1] - w[0]) / 60.0 for w in full)
    got = sum(inside(*w) for w in full)
    zero = sum(1 for w in full if inside(*w) == 0)
    print(f"window {a.lo} .. {a.hi} (local); climate publish rows in window: {len(rows)}")
    print(f"internal cycles with ignition->end span >= 100 s: {len(full)}; with ZERO climate rows inside: {zero}; "
          f"rows expected at the 60 s floor: {exp:.0f}, observed: {got}")
    rng = random.Random(7)
    lens = [w[1] - w[0] for w in full]
    ce = cg = n = 0
    for _ in range(50000):
        if n >= len(full):
            break
        L = rng.choice(lens)
        x = rng.uniform(lo, hi - L)
        y = x + L
        if overlap(x, y, spans) > 0 or overlap(x, y, naps) > 0:
            continue
        n += 1
        ce += L / 60.0
        cg += inside(x, y)
    print(f"control windows (same lengths, outside every internal-cycle span and nap stall): {n}; expected {ce:.0f}, observed {cg}")
    print("VERDICT:", "climate loop SUSPENDED during internal cycles" if got == 0 and zero == len(full) and cg > 0.5 * ce else "NOT clean - inspect")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
