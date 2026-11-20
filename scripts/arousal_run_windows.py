"""J-1994 / F-2595: window-based filter for data/arousal_shadow.jsonl (and the D-0274 J-1306 regime shadow).

Before J-1994, the HUD process's evidence poll (hud/server.py -> core.arousal.status() -> level())
appended arousal_shadow rows with no Du process running (~12.2% of rows, upper bound). Those rows are NOT
deleted from the live file; any READ of the shadow that wants Du-only samples should filter through
rows_in_run_windows(). Logic lifted from the J-1934 scratch script: nascence.log boot ('Memory store
initialised') -> 'Nascence shutting down.' (or last log line if no shutdown) windows, +-120s slack.
Read-only; never writes.
"""
from __future__ import annotations
import bisect, json, re, time
from pathlib import Path

_PAT = re.compile(r'^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d),\d+ \[')
SLACK = 120.0


def run_windows(log_path) -> list:
    wins, cur, last = [], None, None
    for line in open(log_path, encoding="utf-8", errors="replace"):
        m = _PAT.match(line)
        if not m:
            continue
        t = time.mktime(time.strptime(m.group(1), "%Y-%m-%d %H:%M:%S"))
        if "Memory store initialised" in line:
            if cur is not None and last is not None:
                wins.append((cur, last))      # previous boot never logged a shutdown
            cur = t
        elif "Nascence shutting down." in line and cur is not None:
            wins.append((cur, t))
            cur = None
        last = t
    if cur is not None and last is not None:
        wins.append((cur, last))
    wins.sort()
    return wins


def make_inside(windows, slack: float = SLACK):
    starts = [w[0] for w in windows]

    def inside(ts: float) -> bool:
        i = bisect.bisect_right(starts, ts) - 1
        for j in range(max(0, i - 5), i + 1):
            if windows[j][0] - slack <= ts <= windows[j][1] + slack:
                return True
        return False
    return inside


def rows_in_run_windows(rows, log_path=None, slack: float = SLACK) -> list:
    """Keep only rows (dicts with 'ts') that fall inside a Du run window."""
    if log_path is None:
        log_path = Path(__file__).resolve().parent.parent / "data" / "nascence.log"
    inside = make_inside(run_windows(log_path), slack)
    return [r for r in rows if inside(r["ts"])]


# ---- J-2040: incremental, cached reader so a ~6s poll never re-parses the whole (80+ MB) nascence.log ----
_INC: dict = {}


def run_windows_cached(log_path) -> list:
    """Same result as run_windows(), but remembers the byte offset + parser state per log path and only
    reads newly appended bytes on each call (first call pays the full parse, ~5s on an 86 MB log). If the
    file shrank (rotation/truncation) it re-parses from scratch. Returns closed windows plus the currently
    open one (ending at the last log line seen), sorted."""
    key = str(log_path)
    st = _INC.get(key)
    size = Path(log_path).stat().st_size
    if st is None or size < st["off"]:
        st = {"off": 0, "wins": [], "cur": None, "last": None, "tail": b""}
        _INC[key] = st
    if size > st["off"]:
        with open(log_path, "rb") as f:
            f.seek(st["off"])
            data = st["tail"] + f.read(size - st["off"])
        st["off"] = size
        nl = data.rfind(b"\n")
        if nl < 0:
            st["tail"] = data
            data = b""
        else:
            st["tail"] = data[nl + 1:]
            data = data[:nl + 1]
        for raw in data.split(b"\n"):
            line = raw.decode("utf-8", errors="replace")
            m = _PAT.match(line)
            if not m:
                continue
            t = time.mktime(time.strptime(m.group(1), "%Y-%m-%d %H:%M:%S"))
            if "Memory store initialised" in line:
                if st["cur"] is not None and st["last"] is not None:
                    st["wins"].append((st["cur"], st["last"]))
                st["cur"] = t
            elif "Nascence shutting down." in line and st["cur"] is not None:
                st["wins"].append((st["cur"], t))
                st["cur"] = None
            st["last"] = t
    wins = list(st["wins"])
    if st["cur"] is not None and st["last"] is not None:
        wins.append((st["cur"], st["last"]))
    wins.sort()
    return wins


def filter_rows_cached(rows, log_path=None, slack: float = SLACK) -> list:
    """rows_in_run_windows() backed by run_windows_cached(). Fail-open: if the log is missing/unreadable
    the rows come back UNFILTERED (a reader must not go blind because the filter could not run)."""
    try:
        if log_path is None:
            log_path = Path(__file__).resolve().parent.parent / "data" / "nascence.log"
        inside = make_inside(run_windows_cached(log_path), slack)
        return [r for r in rows if inside(r["ts"])]
    except Exception:
        return list(rows)
