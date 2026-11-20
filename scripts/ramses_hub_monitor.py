"""
Read-only monitor for the Ramses model hubs (J-3279, Phase 0 of docs/reviews/ramses_stall_plan_2026-11-03.md).

WHY: Du's background lane (command-r7b on Ramses :11441) has intermittent total stalls (F-3872, F-3873: 9.4 percent
of calls at the 120 s ceiling, windows of 12 minutes to 6.7 hours). The hub's own log is un-timestamped and its [chat]
durations include lock waits, so nothing records WHEN a stall starts and ends independently of Du's workload. This
process does, from outside Du, with no Ramses-side change.

WHAT IT DOES (every POLL_S seconds, per hub, in its own thread so one stalled hub never delays another):
  - TCP connect time to the port (is the process listening?)
  - GET /api/tags latency (the hub's cheap route; it does NOT take the generation lock, so a hub that answers /api/tags
    but not the probe is lock-wedged rather than dead)
  - GET /api/status when the hub runs the Oct-7 server (J-1830): in_flight, queue_depth, counters. 404 = old server.
  - on :11441 only, a ONE-TOKEN free-text POST /api/chat probe. It queues behind the hub's generation lock, so its
    latency is the lock wait. The probe backs off (PROBE_BACKOFF_S) after PROBE_FAILS_BEFORE_BACKOFF consecutive
    failures, because the OLD server runs every request to completion even after the caller has gone: probing every
    30 s through a six-hour stall would leave ~700 tiny jobs queued behind it and delay recovery by minutes.

WHAT IT NEVER DOES: write to Ramses, stop or restart anything, touch Du's stores, import anything from core/.
Output: data/ramses_hub_monitor.jsonl (one row per hub per poll, one row per probe), rotated at 20 MB to .1.
Side effect worth knowing: the probe keeps command-r7b resident, so the hub's 900 s idle-unload never fires while this
runs. Du's own calls (about 15 an hour) already keep it loaded most of the time.

RUN (own process, not inside Du):   python scripts/ramses_hub_monitor.py            (runs until stopped)
                                    python scripts/ramses_hub_monitor.py --max-minutes 10
READ:                               python scripts/ramses_hub_monitor_read.py [--hours 24] [--du]
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import threading
import time
import urllib.error
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HOST = "LAN-HOST"
HUBS = {11436: "falcon3:7b", 11437: "granite3.1-moe:3b", 11438: "mixtral:8x7b",
        11441: "command-r7b", 11444: "deepseek-r1"}
PROBE_PORT = 11441
PROBE_MODEL = "command-r7b"
POLL_S = 30
TCP_TIMEOUT_S = 3.0
HTTP_TIMEOUT_S = 5.0
PROBE_TIMEOUT_S = 20.0
PROBE_FAILS_BEFORE_BACKOFF = 3
PROBE_BACKOFF_S = 300
ROTATE_BYTES = 20 * 1024 * 1024

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(_ROOT, "data", "ramses_hub_monitor.jsonl")
_LOG_LOCK = threading.Lock()


def _write(row: dict) -> None:
    """Append one row. Never raises."""
    try:
        line = json.dumps(row, ensure_ascii=False) + "\n"
        with _LOG_LOCK:
            os.makedirs(os.path.dirname(LOG), exist_ok=True)
            try:
                if os.path.getsize(LOG) > ROTATE_BYTES:
                    os.replace(LOG, LOG + ".1")
            except OSError:
                pass
            with open(LOG, "a", encoding="utf-8") as f:
                f.write(line)
    except Exception:
        pass


def _ms(t0: float) -> float:
    return round((time.perf_counter() - t0) * 1000.0, 1)


def _tcp(port: int):
    t0 = time.perf_counter()
    try:
        with socket.create_connection((HOST, port), timeout=TCP_TIMEOUT_S):
            return _ms(t0), None
    except Exception as exc:
        return None, type(exc).__name__


def _get(port: int, path: str):
    """GET -> (ms, http_code, parsed_json_or_None, error). Never raises."""
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(f"http://{HOST}:{port}{path}", timeout=HTTP_TIMEOUT_S) as r:
            body = r.read()
            code = r.status
        try:
            return _ms(t0), code, json.loads(body), None
        except Exception:
            return _ms(t0), code, None, None
    except urllib.error.HTTPError as exc:
        return _ms(t0), exc.code, None, None
    except Exception as exc:
        return _ms(t0), None, None, type(exc).__name__


def poll_hub(port: int) -> None:
    tcp_ms, tcp_err = _tcp(port)
    row = {"ts": time.time(), "type": "poll", "port": port, "tcp_ms": tcp_ms, "tcp_err": tcp_err,
           "tags_ms": None, "tags_ok": None, "status": None, "status_code": None}
    if tcp_ms is not None:
        ms, code, _data, err = _get(port, "/api/tags")
        row["tags_ms"], row["tags_ok"] = ms, (code == 200)
        if err:
            row["tags_err"] = err
        ms, code, data, err = _get(port, "/api/status")
        row["status_code"] = code
        if code == 200 and isinstance(data, dict):
            row["status"] = {k: data.get(k) for k in ("queue_depth", "in_flight", "counters", "uptime_s") if k in data}
    _write(row)


class Prober:
    """One-token free-text probe against PROBE_PORT, run in its own thread with backoff after repeated failures."""

    def __init__(self) -> None:
        self.fails = 0
        self.next_at = 0.0
        self.busy = False
        self.lock = threading.Lock()

    def maybe_start(self, tcp_ok: bool) -> None:
        now = time.time()
        with self.lock:
            if self.busy or now < self.next_at or not tcp_ok:
                return
            self.busy = True
        threading.Thread(target=self._probe, daemon=True).start()

    def _probe(self) -> None:
        t_wall = time.time()
        t0 = time.perf_counter()
        ok, err, content_len = False, None, None
        try:
            body = json.dumps({"model": PROBE_MODEL, "stream": False,
                               "messages": [{"role": "user", "content": "Reply with the single word: ok"}],
                               "options": {"num_predict": 1, "temperature": 0.0}}).encode()
            req = urllib.request.Request(f"http://{HOST}:{PROBE_PORT}/api/chat", body,
                                         {"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=PROBE_TIMEOUT_S) as r:
                d = json.loads(r.read())
            content_len = len((d.get("message") or {}).get("content") or "")
            ok = True
        except Exception as exc:
            err = type(exc).__name__
        ms = _ms(t0)
        _write({"ts": time.time(), "type": "probe", "port": PROBE_PORT, "start_ts": t_wall, "probe_ms": ms,
                "probe_ok": ok, "err": err, "content_len": content_len, "consecutive_fails": 0 if ok else self.fails + 1})
        with self.lock:
            self.fails = 0 if ok else self.fails + 1
            gap = PROBE_BACKOFF_S if self.fails >= PROBE_FAILS_BEFORE_BACKOFF else POLL_S
            self.next_at = time.time() + gap
            self.busy = False


def main() -> int:
    ap = argparse.ArgumentParser(description="Read-only Ramses hub monitor (J-3279)")
    ap.add_argument("--max-minutes", type=float, default=0.0, help="stop after this many minutes (0 = run until stopped)")
    args = ap.parse_args()
    prober = Prober()
    end = time.time() + args.max_minutes * 60 if args.max_minutes > 0 else None
    print(f"[ramses-monitor] polling {sorted(HUBS)} on {HOST} every {POLL_S}s -> {LOG}", flush=True)
    last_report = 0.0
    while end is None or time.time() < end:
        t_cycle = time.time()
        threads = [threading.Thread(target=poll_hub, args=(p,), daemon=True) for p in HUBS]
        for t in threads:
            t.start()
        # the probe only fires when the hub's port is accepting connections right now
        tcp_ok = _tcp(PROBE_PORT)[0] is not None
        prober.maybe_start(tcp_ok)
        for t in threads:
            t.join(timeout=TCP_TIMEOUT_S + 2 * HTTP_TIMEOUT_S + 2)
        if time.time() - last_report > 300:
            last_report = time.time()
            print(f"[ramses-monitor] {time.strftime('%H:%M:%S')} probe consecutive_fails={prober.fails}", flush=True)
        time.sleep(max(1.0, POLL_S - (time.time() - t_cycle)))
    # let an in-flight probe finish and be recorded
    for _ in range(int(PROBE_TIMEOUT_S) + 2):
        if not prober.busy:
            break
        time.sleep(1)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(0)
