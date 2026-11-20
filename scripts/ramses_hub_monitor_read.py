"""
Reader for data/ramses_hub_monitor.jsonl (J-3279). Prints, per hub, how often it answered, and the :11441 stall
windows (probe slower than 20 s or failing, for 3 or more consecutive probes), so they can be laid against
Du's own data/llm_latency.jsonl and the Ramses-side GPU and memory logs.

  python scripts/ramses_hub_monitor_read.py [--hours 24] [--du]

--du also counts, for each stall window, Du's own :11441 calls that ended inside it and how many hit the 120 s ceiling.
Read-only.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import statistics as st
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(_ROOT, "data", "ramses_hub_monitor.jsonl")
DU_LAT = os.path.join(_ROOT, "data", "llm_latency.jsonl")
PROBE_PORT = 11441
SLOW_PROBE_MS = 20000.0
MIN_RUN = 3
MAX_GAP_S = 400.0     # probes back off to 300 s while failing; allow a little slack


def _rows(path: str, since: float):
    out = []
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if r.get("ts", 0) >= since:
                    out.append(r)
    except FileNotFoundError:
        pass
    return out


def _fmt(t: float) -> str:
    return datetime.datetime.fromtimestamp(t).strftime("%m-%d %H:%M:%S")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=24.0)
    ap.add_argument("--du", action="store_true")
    a = ap.parse_args()
    since = time.time() - a.hours * 3600
    rows = _rows(LOG, since)
    if not rows:
        print(f"no rows in {LOG} for the last {a.hours:g} h (is scripts/ramses_hub_monitor.py running?)")
        return 1
    polls = [r for r in rows if r.get("type") == "poll"]
    probes = sorted((r for r in rows if r.get("type") == "probe"), key=lambda r: r["start_ts"])
    print(f"window: {_fmt(rows[0]['ts'])} -> {_fmt(rows[-1]['ts'])}  ({len(polls)} polls, {len(probes)} probes)\n")
    print("hub    polls  tcp_ok  tags_ok  tags_ms p50   status endpoint")
    for port in sorted({r["port"] for r in polls}):
        P = [r for r in polls if r["port"] == port]
        tcp = sum(1 for r in P if r.get("tcp_ms") is not None)
        tg = sum(1 for r in P if r.get("tags_ok"))
        ms = [r["tags_ms"] for r in P if r.get("tags_ok") and r.get("tags_ms") is not None]
        stc = {r.get("status_code") for r in P}
        sdesc = "new server (200)" if 200 in stc else ("old server (404)" if 404 in stc else str(sorted(x for x in stc if x)))
        print(":%d  %5d  %5.0f%%  %6.0f%%  %8.0f   %s" % (port, len(P), 100 * tcp / len(P), 100 * tg / len(P),
                                                          st.median(ms) if ms else float("nan"), sdesc))
    if not probes:
        print("\nno :11441 probes yet")
        return 0
    okp = [p["probe_ms"] for p in probes if p.get("probe_ok")]
    print("\n:11441 probe: %d total, %.0f%% ok, ok-latency median %.0f ms p95 %.0f ms" % (
        len(probes), 100 * len(okp) / len(probes), st.median(okp) if okp else float("nan"),
        sorted(okp)[int(0.95 * len(okp)) - 1] if len(okp) > 1 else (okp[0] if okp else float("nan"))))
    bad = lambda p: (not p.get("probe_ok")) or p.get("probe_ms", 0) > SLOW_PROBE_MS
    windows, cur = [], []
    for p in probes:
        if bad(p):
            if cur and p["start_ts"] - cur[-1]["start_ts"] > MAX_GAP_S:
                windows.append(cur); cur = []
            cur.append(p)
        elif cur:
            windows.append(cur); cur = []
    if cur:
        windows.append(cur)
    windows = [w for w in windows if len(w) >= MIN_RUN]
    print("\nstall windows (>= %d consecutive bad probes): %d" % (MIN_RUN, len(windows)))
    du = _rows(DU_LAT, since) if a.du else []
    for w in windows:
        start, end = w[0]["start_ts"], w[-1]["ts"]
        # tags during the window: a hub that answers /api/tags but not the probe is lock-wedged, not dead
        tg = [r for r in polls if r["port"] == PROBE_PORT and start <= r["ts"] <= end]
        tg_ok = (100 * sum(1 for r in tg if r.get("tags_ok")) / len(tg)) if tg else float("nan")
        line = "  %s -> %s  %5.1f min  %d probes bad  /api/tags ok %.0f%%" % (
            _fmt(start), _fmt(end), (end - start) / 60, len(w), tg_ok)
        if a.du:
            D = [r for r in du if str(r.get("node")) == "11441" and r.get("model") == "command-r7b"
                 and start <= r["ts"] <= end + 130]
            line += "  | Du :11441 calls in window %d, at ceiling %d" % (len(D), sum(1 for r in D if r.get("s", 0) >= 118))
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
