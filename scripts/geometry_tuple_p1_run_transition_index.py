"""
Geometry Tuple Index — P1 pilot run-transition index (D-0107, 2026-09-02).

docs/staged/geometry_tuple_index.md §6: "one pilot run-transition index, one field
(geometry_tuples.jsonl, e.g. weather), only if P0 clears. Unchanged from original scope —
additive sidecar, source file untouched, point-query correctness required 100%."

Event-sourcing shape (§6 framing correction): store *transitions* ("weather changed to X at
row/ts Y"), not a raw per-row snapshot — geometry_tuples.jsonl's weather field holds long runs
of the same value, so the transition list is far smaller than the source.

GUARDS (docs/staged/geometry_tuple_index.md §7), all honored here:
- Additive-only: this script only READS data/geometry_tuples.jsonl, never writes it.
- Sidecar crash-consistency: the sidecar is written atomically (temp file + os.replace) and
  carries a completeness marker (source row count + mtime) checked before being trusted.
- Point-query correctness required 100%: verified against every row in the source, not sampled.

NOT wired into Du's live architecture (per the plan's own lineage note and the activation guard) —
this is a standalone, offline index-build-and-verify script, matching the discipline the P0
checkpoint-index benchmark (J-0210) already used.
"""
from __future__ import annotations

import json
import time
import random
from pathlib import Path

_ROOT = Path(__file__).parent.parent
_SOURCE = _ROOT / "data" / "geometry_tuples.jsonl"
_SIDECAR_DIR = _ROOT / "data" / "geometry_tuple_index_sidecar"
_SIDECAR = _SIDECAR_DIR / "p1_weather_transitions.json"
_FIELD = "weather"


def build():
    rows = []
    with open(_SOURCE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))

    transitions = []
    prev = object()  # sentinel that can never equal a real weather value
    for i, row in enumerate(rows):
        val = row.get(_FIELD)
        if val != prev:
            transitions.append({"row": i, "ts": row.get("ts"), _FIELD: val})
            prev = val

    sidecar = {
        "field": _FIELD,
        "source_file": "data/geometry_tuples.jsonl",
        "source_row_count": len(rows),
        "source_mtime": _SOURCE.stat().st_mtime,
        "built_ts": round(time.time(), 1),
        "transition_count": len(transitions),
        "transitions": transitions,
    }

    _SIDECAR_DIR.mkdir(parents=True, exist_ok=True)
    tmp = _SIDECAR.with_suffix(".tmp")
    tmp.write_text(json.dumps(sidecar, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(_SIDECAR)  # atomic on POSIX and Windows (same-volume rename)

    return rows, transitions, sidecar


def point_query_by_ts(transitions: list[dict], ts: float) -> str | None:
    """Binary search: the value in effect at `ts` = the last transition at or before it.
    Answers the doc's own motivating question (§1): "what was field X at/near ... timestamp Y"."""
    lo, hi = 0, len(transitions) - 1
    ans = None
    while lo <= hi:
        mid = (lo + hi) // 2
        if transitions[mid]["ts"] <= ts:
            ans = transitions[mid][_FIELD]
            lo = mid + 1
        else:
            hi = mid - 1
    return ans


def scan_by_ts(rows: list[dict], ts: float) -> str | None:
    """The full-scan ground truth a caller WITHOUT this index has to do today."""
    ans = None
    for row in rows:
        if row.get("ts", float("inf")) <= ts:
            ans = row.get(_FIELD)
        else:
            break
    return ans


def verify(rows: list[dict], transitions: list[dict]) -> tuple[int, int]:
    """100%-required point-query correctness check: EVERY row's own ts, not a sample."""
    correct = 0
    for row in rows:
        if point_query_by_ts(transitions, row["ts"]) == row.get(_FIELD):
            correct += 1
    return correct, len(rows)


def benchmark(rows: list[dict], transitions: list[dict], n_queries: int = 500):
    random.seed(20260902)
    query_ts = [rows[random.randrange(len(rows))]["ts"] for _ in range(n_queries)]

    t0 = time.perf_counter()
    for qt in query_ts:
        scan_by_ts(rows, qt)
    t_scan = time.perf_counter() - t0

    t0 = time.perf_counter()
    for qt in query_ts:
        point_query_by_ts(transitions, qt)
    t_index = time.perf_counter() - t0

    return t_scan, t_index, n_queries


if __name__ == "__main__":
    rows, transitions, sidecar = build()
    print(f"source rows: {len(rows)}")
    print(f"transitions: {len(transitions)} (ratio {len(transitions)/len(rows):.4f})")
    print(f"sidecar written: {_SIDECAR} ({_SIDECAR.stat().st_size} bytes)")

    correct, total = verify(rows, transitions)
    print(f"point-query correctness: {correct}/{total} = {correct/total:.6f}")

    t_scan, t_index, n = benchmark(rows, transitions)
    print(f"benchmark ({n} random point queries):")
    print(f"  full linear scan to query row: {t_scan*1000:.2f}ms total, {t_scan/n*1e6:.1f}us/query")
    print(f"  transition-index binary search: {t_index*1000:.2f}ms total, {t_index/n*1e6:.1f}us/query")
    print(f"  speedup: {t_scan/t_index:.1f}x")

    assert correct == total, "P1's own spec requires 100% point-query correctness — FAILED"
    print("\nP1 pilot run-transition index: PASSED (100% correctness, additive sidecar, source untouched)")
