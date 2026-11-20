"""J-3946 (F-4603): SHADOW-ONLY deterministic series verdict for prediction_error T4 hearings.

For a hearing on tension label 'prediction_error:<domain> (felt F vs real R)', compares the median
|felt-real| over the 72h before the hearing against the prior 72h for that domain. Verdict is
'moved' (shift >= SERIES_EPS), 'flat', or 'undecidable' (either window empty). Prototype logic:
scripts/analysis_J3641_pe_series.py series_moved(). Read-only (sqlite mode=ro); fail-open; never
shown to Du and never read by the T4 stage -- the verdict is only written beside the LLM verdict in
data/logs/t4_chain_trace.jsonl so series-vs-LLM agreement accrues on live data.
"""
from __future__ import annotations
import json
import re
import sqlite3
import statistics
from pathlib import Path

SERIES_EPS = 0.05
WINDOW_S = 72 * 3600.0
_RE_LAB = re.compile(r"prediction_error:(\w+) \(felt ([\d.]+) vs real ([\d.]+)\)")
_RE_DOM = re.compile(r"^\s*prediction_error:(\w+)")


def domain_of(label) -> str | None:
    m = _RE_DOM.match(str(label or ""))
    return m.group(1) if m else None


def series_verdict(evs, t: float, w: float = WINDOW_S, eps: float = SERIES_EPS) -> dict:
    """evs: [(ts, felt, real)] for one domain. Pure function."""
    cur = [abs(f - r) for ts, f, r in evs if t - w <= ts < t]
    prev = [abs(f - r) for ts, f, r in evs if t - 2 * w <= ts < t - w]
    if not cur or not prev:
        return {"verdict": "undecidable", "n_cur": len(cur), "n_prev": len(prev)}
    d = statistics.median(cur) - statistics.median(prev)
    return {"verdict": "moved" if abs(d) >= eps else "flat",
            "n_cur": len(cur), "n_prev": len(prev), "d": round(d, 3), "eps": eps}


def load_domain_events(domain: str, since: float, until: float, db_path=None) -> list:
    if db_path is None:
        from core.memory.store import DB_PATH as db_path
    uri = f"file:{Path(db_path).as_posix()}?mode=ro"
    con = sqlite3.connect(uri, uri=True, timeout=2.0)
    try:
        rows = con.execute(
            "SELECT timestamp, corrections FROM shadow_events WHERE source='prediction_error' "
            "AND timestamp >= ? AND timestamp < ? ORDER BY timestamp", (since, until)).fetchall()
    finally:
        con.close()
    out = []
    for ts, corr in rows:
        try:
            m = _RE_LAB.search(json.loads(corr)[0])
        except Exception:
            continue
        if m and m.group(1) == domain:
            out.append((ts, float(m.group(2)), float(m.group(3))))
    return out


def series_column(label, t: float, db_path=None) -> dict | None:
    """The trace-row column for a hearing, or None when the tension is not a prediction_error one.
    Fail-open: any error yields {'verdict': 'error', ...} rather than raising."""
    dom = domain_of(label)
    if dom is None:
        return None
    try:
        evs = load_domain_events(dom, t - 2 * WINDOW_S, t, db_path)
        out = series_verdict(evs, t)
    except Exception as exc:
        out = {"verdict": "error", "err": f"{type(exc).__name__}: {exc}"[:120]}
    out["domain"] = dom
    return out
