"""J-0334 / D-0060 rebuild: extract a real numeric state-vector for the geometry_tuple_index staged
design (docs/staged/geometry_tuple_index.md, §7 World-truth-source guard) from `fragment_context` --
the EXPERIENCED layer (core/experienced_tuple.py) -- instead of the raw `geometry_tuples.jsonl`
WORLD-TRUTH stream that F-0269/F-0275/F-0278's benchmarks were built directly on (F-0282's finding).

Read-only against Du's live SQLite store (data/memory/nascence.db); writes only to the sidecar
directory below, never touches the source DB or geometry_tuples.jsonl. Additive-only guard (§7).

WHY 3-D (valence, level, warmth), NOT the original 8-D affect vector, verified 2026-08-29 (J-0334):
`fragment_context` rows written with source LIKE 'experienced:%' (the real "crossed into experience"
rows, excluding the legacy 'census_world:%' rows that pre-date the 2026-08-21 world/fragment split)
have `arousal` NULL in 0/7733 real rows -- traced to core/memory/store.py's `_store_fragment` write
hook: the fallback affect dict built outside a live CognitiveState (`{"valence": ..., "level": ...}`,
around line 436) never sets an `arousal` key, so `aff.get("arousal")` is always None for every
fragment-context row regardless of source. This is a real, separate, live-code gap -- spawned as its
own follow-up job (see J-0334's finding/job in docs/findings.jsonl / docs/job_queue.jsonl), NOT
guessed around here. `valence`, `level` (Bachmann's L / arousal-level proxy, NOT the same field as the
missing circumplex `arousal`), and `warmth` are the three real numeric fields fragment_context
actually carries at 100% coverage for experienced rows (7733/7733) -- an honest, verified substitute,
not a claim that this reproduces the original 8-D affect benchmark's dimensionality.
"""
from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
_DB = _ROOT / "data" / "memory" / "nascence.db"
_OUT_DIR = _ROOT / "data" / "geometry_tuple_index_sidecar"
_CSV_PATH = _OUT_DIR / "fragment_context_vectors.csv"
_GT_PATH = _OUT_DIR / "fragment_context_ground_truth.json"

_K = 10
_QUERY_STRIDE = 40   # deterministic query sample -- every Nth row by tuple_ts order, not random picks


def extract() -> dict:
    conn = sqlite3.connect(str(_DB))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT fragment_id, tuple_ts, valence, level, warmth FROM fragment_context "
        "WHERE source LIKE 'experienced:%' AND valence IS NOT NULL AND level IS NOT NULL "
        "AND warmth IS NOT NULL ORDER BY tuple_ts ASC"
    ).fetchall()
    conn.close()

    _OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(_CSV_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["idx", "valence", "level", "warmth"])
        for i, r in enumerate(rows):
            w.writerow([i, r["valence"], r["level"], r["warmth"]])

    vecs = np.array([[r["valence"], r["level"], r["warmth"]] for r in rows], dtype=np.float32)
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms[norms < 1e-10] = 1.0
    unit = vecs / norms

    query_idx = list(range(0, len(rows), _QUERY_STRIDE))
    queries = {}
    for qi in query_idx:
        sims = unit @ unit[qi]
        sims[qi] = -np.inf   # exclude self
        top = np.argsort(-sims)[:_K]
        queries[str(qi)] = [{"idx": int(j), "score": float(sims[j])} for j in top]

    gt = {"k": _K, "n": len(rows), "source": "fragment_context (experienced:*, valence/level/warmth)",
          "queries": queries}
    with open(_GT_PATH, "w", encoding="utf-8") as f:
        json.dump(gt, f)

    return {"rows": len(rows), "queries": len(queries), "csv": str(_CSV_PATH), "gt": str(_GT_PATH)}


if __name__ == "__main__":
    print(json.dumps(extract(), indent=2))
