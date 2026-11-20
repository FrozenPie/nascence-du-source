"""
J-0950 / Thread 2(b): stream data/nascence.log ONCE (read-only, 70 MB, never fully loaded) and write a compact
event file of everything needed to read inter-cycle-start gap DISTRIBUTIONS at finer than hourly grain:

  start   [CYCLE id] internal|human: ...            (cycle start; internal = the climate-ignition callback, the only
                                                     call site of input_type="internal", core/orchestrator.py:2825)
  complete [CYCLE id] complete in X.Xs               (duration)
  gate    [CYCLE id] thalamic gate: HABITUATED       (start silenced by the live thalamic gate, F-1564)
  ign     [climate] IGNITION (defensive|exploratory)  (the climate loop's own fire, BEFORE the curiosity LLM call)
  clim    [climate] dominant=X(v) dissonance=d strain=s completion=c integration=i   (the 5-minute telemetry line; the
          integration= value is a direct fingerprint of D-0148 option A: pinned ~0.98 before, ~0.5 after)
  ignline [ignition] dominant=... -> autonomous thought (callback reached run_cycle)
  boot    Identity loaded                             shut  Nascence shutting down
  sleep_in / sleep_out                                entering Sleep State / [night] waking
  silent  any gap >= SILENT_S between two consecutive timestamped lines (a wedge/stall/outage detector that does
          NOT depend on boot markers, since ~51 percent of restarts are unclean, F-1002)

Timestamps: nascence.log lines carry local wall-clock (UTC+12 through 2026-09-26, no DST inside 09-08..09-25,
F-1319's calibration); every value written is "local seconds since 1970-01-01 00:00 local" so differences are exact.

READ-ONLY on the live log; the only write is the output file (SCRATCH or a worktree path given by --out).
Usage: python scripts/j0950_parse_cycle_events.py --log C:\\Nascence\\data\\nascence.log --out <events.jsonl> [--since 2026-08-20]
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

SILENT_S = 120.0

RE_TS = re.compile(r"^(\d{4})-(\d\d)-(\d\d) (\d\d):(\d\d):(\d\d),(\d{3}) ")
RE_START = re.compile(r"\[CYCLE ([0-9a-f]{8})\] (human|internal): (.*)")
RE_COMPLETE = re.compile(r"\[CYCLE ([0-9a-f]{8})\] complete in ([0-9.]+)s")
RE_GATE = re.compile(r"\[CYCLE ([0-9a-f]{8})\] thalamic gate: HABITUATED")
RE_IGN = re.compile(r"\[climate\] IGNITION \((\w+)\) \u2014 dominant=(\w+) \(([0-9.]+)\)")
RE_IGNLINE = re.compile(r"\[ignition\] dominant=(\w+) -> autonomous thought")
RE_BOOT = re.compile(r"\[nascence\.main\] Identity loaded")
RE_SHUT = re.compile(r"\[nascence\.main\] Nascence shutting down")
RE_CLIM = re.compile(r"\[climate\] dominant=(\w+)\(([0-9.]+)\) dissonance=([0-9.]+) strain=([0-9.]+) completion=([0-9.]+) integration=([0-9.]+)")
RE_SLEEP_IN = re.compile(r"entering Sleep State")
RE_SLEEP_OUT = re.compile(r"\[night\] waking:")

_day_cache: dict[str, int] = {}


def _day(y: str, m: str, d: str) -> int:
    k = y + m + d
    v = _day_cache.get(k)
    if v is None:
        v = _dt.date(int(y), int(m), int(d)).toordinal() * 86400
        _day_cache[k] = v
    return v


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default=r"C:\Nascence\data\nascence.log")
    ap.add_argument("--out", required=True)
    ap.add_argument("--since", default="2026-08-20", help="skip lines before this local date")
    a = ap.parse_args()
    since = tuple(int(x) for x in a.since.split("-"))
    n_lines = n_kept = 0
    prev_t = None
    prev_line_no = 0
    with open(a.log, "r", encoding="utf-8", errors="replace") as f, open(a.out, "w", encoding="utf-8") as out:
        for line_no, line in enumerate(f, 1):
            n_lines += 1
            m = RE_TS.match(line)
            if not m:
                continue
            y, mo, d, hh, mi, ss, ms = m.groups()
            if (int(y), int(mo), int(d)) < since:
                continue
            t = _day(y, mo, d) + int(hh) * 3600 + int(mi) * 60 + int(ss) + int(ms) / 1000.0
            if prev_t is not None and t - prev_t >= SILENT_S:
                out.write(json.dumps({"k": "silent", "t": prev_t, "t2": t, "line": prev_line_no, "line2": line_no}) + "\n")
                n_kept += 1
            prev_t, prev_line_no = t, line_no
            if "[CYCLE " in line:
                mm = RE_COMPLETE.search(line)
                if mm:
                    out.write(json.dumps({"k": "complete", "t": t, "id": mm.group(1), "dur": float(mm.group(2)), "line": line_no}) + "\n"); n_kept += 1
                    continue
                mm = RE_GATE.search(line)
                if mm:
                    out.write(json.dumps({"k": "gate", "t": t, "id": mm.group(1), "line": line_no}) + "\n"); n_kept += 1
                    continue
                mm = RE_START.search(line)
                if mm:
                    out.write(json.dumps({"k": "start", "t": t, "id": mm.group(1), "type": mm.group(2), "line": line_no,
                                          "text": mm.group(3)[:100]}, ensure_ascii=False) + "\n"); n_kept += 1
                    continue
                continue
            if "[climate] dominant=" in line:
                mm = RE_CLIM.search(line)
                if mm:
                    out.write(json.dumps({"k": "clim", "t": t, "dom": mm.group(1), "domv": float(mm.group(2)), "diss": float(mm.group(3)),
                                          "strain": float(mm.group(4)), "compl": float(mm.group(5)), "integ": float(mm.group(6)), "line": line_no}) + "\n"); n_kept += 1
                continue
            if "[climate] IGNITION" in line:
                mm = RE_IGN.search(line)
                if mm:
                    out.write(json.dumps({"k": "ign", "t": t, "trig": mm.group(1), "dom": mm.group(2), "val": float(mm.group(3)), "line": line_no}) + "\n"); n_kept += 1
                continue
            if "[ignition] dominant=" in line:
                mm = RE_IGNLINE.search(line)
                if mm:
                    out.write(json.dumps({"k": "ignline", "t": t, "dom": mm.group(1), "line": line_no}) + "\n"); n_kept += 1
                continue
            if "Identity loaded" in line and RE_BOOT.search(line):
                out.write(json.dumps({"k": "boot", "t": t, "line": line_no}) + "\n"); n_kept += 1
                continue
            if "Nascence shutting down" in line and RE_SHUT.search(line):
                out.write(json.dumps({"k": "shut", "t": t, "line": line_no}) + "\n"); n_kept += 1
                continue
            if "entering Sleep State" in line and RE_SLEEP_IN.search(line):
                out.write(json.dumps({"k": "sleep_in", "t": t, "line": line_no}) + "\n"); n_kept += 1
                continue
            if "[night] waking:" in line and RE_SLEEP_OUT.search(line):
                out.write(json.dumps({"k": "sleep_out", "t": t, "line": line_no}) + "\n"); n_kept += 1
                continue
        out.write(json.dumps({"k": "eof", "t": prev_t, "line": prev_line_no}) + "\n")
    print(f"lines read {n_lines}, events kept {n_kept}, last timestamped line {prev_line_no}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
