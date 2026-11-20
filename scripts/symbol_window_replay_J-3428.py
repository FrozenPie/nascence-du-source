"""
symbol_window_replay_J-3428.py - offline replay of Du's PAST cycle outputs through the D-0615 window metric.

J-3428 / D-0615 (plan symbol_evolution_readback_plan). The live shadow log (data/symbol_window_shadow.jsonl)
only fills after the metric went live (first row 2026-11-07), so the calibration and the hold-out set are thin.
Du's past cycle outputs ARE recoverable read-only: each cycle's output is stored as a `lived` row in
memory_fragments (data/memory/nascence.db), and data/symbol_recurrence.jsonl says which symbols appeared
UNPRIMED in which cycle (by timestamp; ~0.3s after the fragment). This script joins the two, then folds the
windows in time order through core.symbol_window_shadow.WindowMetric with TEMP state/log paths.

READ-ONLY on live data: sqlite opened mode=ro, jsonl opened for read. Writes ONLY under --out.
Output: <out>/replay_shadow.jsonl (same row schema as the live log, so scripts/symbol_window_report.py --log
reads it unchanged) and <out>/replay_summary.json.

  python scripts/symbol_window_replay_J-3428.py --out <dir> [--since-ts T] [--limit N]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--since-ts", type=float, default=0.0)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--recurrence", default=str(ROOT / "data" / "symbol_recurrence.jsonl"))
    ap.add_argument("--db", default=str(ROOT / "data" / "memory" / "nascence.db"))
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    # Refuse to write into the live data dir.
    if (ROOT / "data").resolve() in out.resolve().parents or out.resolve() == (ROOT / "data").resolve():
        print("refusing: --out is inside the live data dir")
        return 2

    import core  # noqa: F401  (before anything that could import lab_env)
    from core import symbol_window_shadow as sw
    from core.symbol_evolution import _SYMBOLS
    from core.memory.store import _embed_batch

    rec = []
    with open(a.recurrence, encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("primed") or r.get("symbol") not in _SYMBOLS or r.get("ts", 0) < a.since_ts:
                continue
            rec.append(r)
    rec.sort(key=lambda r: r["ts"])
    if a.limit:
        rec = rec[-a.limit:]

    con = sqlite3.connect(f"file:{a.db}?mode=ro", uri=True)
    # Group unprimed symbols by cycle_id, find that cycle's output fragment.
    by_cycle: dict[str, list] = {}
    for r in rec:
        by_cycle.setdefault(r["cycle_id"], []).append(r)
    stats = Counter()
    cycles = []
    for cid, rs in by_cycle.items():
        ts = max(r["ts"] for r in rs)
        rows = con.execute(
            "select content, timestamp from memory_fragments where origin='lived' and timestamp between ? and ?",
            (ts - 10.0, ts + 1.0)).fetchall()
        best = None
        for content, fts in sorted(rows, key=lambda x: abs(x[1] - ts)):
            forms = {r["symbol"]: _SYMBOLS[r["symbol"]] for r in rs}
            if any(sw.extract_window(content, fs)[0] for fs in forms.values()):
                best = (content, fts)
                break
        if best is None:
            stats["cycles_no_fragment"] += 1
            continue
        stats["cycles_matched"] += 1
        cycles.append((ts, cid, rs[0].get("input_type", ""), best[0], {r["symbol"]: _SYMBOLS[r["symbol"]] for r in rs}))
    cycles.sort(key=lambda c: c[0])
    stats["cycles_total"] = len(by_cycle)
    stats["unprimed_appearances"] = len(rec)

    state = out / "replay_state.json"
    log = out / "replay_shadow.jsonl"
    for p in (state, log):
        if p.exists():
            p.unlink()
    wm = sw.WindowMetric(embed_batch=_embed_batch, state_file=state, log_file=log)
    n_rows = 0
    for ts, cid, itype, output, forms in cycles:
        rows = wm.observe(output, cid, forms, {}, cycle_vec=None, input_type=itype)
        for r in rows:           # restore the true timestamp (observe stamps now())
            n_rows += 1
    # rewrite the log with real timestamps (observe wrote time.time()); rows are in order, so re-stamp by cycle
    ts_by_cycle = {cid: ts for ts, cid, *_ in cycles}
    fixed = []
    with open(log, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            r["ts"] = ts_by_cycle.get(r["cycle_id"], r["ts"])
            fixed.append(r)
    with open(log, "w", encoding="utf-8") as f:
        for r in fixed:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    stats["rows_written"] = len(fixed)
    stats["status"] = dict(Counter(r["status"] for r in fixed))
    stats["by_symbol"] = dict(Counter(r["symbol"] for r in fixed if r["status"] == "ok").most_common())
    if fixed:
        stats["first_ts"], stats["last_ts"] = fixed[0]["ts"], fixed[-1]["ts"]
    (out / "replay_summary.json").write_text(json.dumps(stats, indent=2, default=str), encoding="utf-8")
    print(json.dumps(stats, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
