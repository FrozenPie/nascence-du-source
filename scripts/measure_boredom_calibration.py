"""Boredom calibration measurement (2026-09-26, J-1362 / F-1921). READ-ONLY against the live DB --
never writes anything, never touches boredom_state.json.

core/boredom.py's record() is fed the memory store's real embedding vector (paraphrase-multilingual-
MiniLM-L12-v2, live since 2026-06-13), but its COH_STUCK/ESCAPE_COS thresholds were set 2026-06-24
"against the real nomic-embed distribution" -- a model that was never actually loaded (F-1921). This
script reproduces record()'s own rolling-WINDOW=10 math (window coherence, new-thought-to-prior-
centroid cosine) over real live inner_thought embeddings from data/memory/nascence.db, so the two
thresholds can be set to real measured percentiles instead of guessed at.

Also what core/boredom.py's own _log_calibration_snapshot() runs internally (once per process, on
record()'s first real call) to log a live check of the same two distributions against whatever
COH_STUCK/ESCAPE_COS are currently set to -- this script is the same measurement, run by hand, with
full percentile detail and no rate limiting, for when that log line's WARNING says the calibration
looks stale again and you need the real numbers to pick new ones.

Usage:
    python scripts/measure_boredom_calibration.py [days_back] [candidate_coh_stuck] [candidate_escape_cos]

Examples:
    python scripts/measure_boredom_calibration.py 21
    python scripts/measure_boredom_calibration.py 21 0.76 0.52
"""
from __future__ import annotations

import sqlite3
import sys
import time
from pathlib import Path

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")

# Hardcoded to the one real live repo on this machine, same reasoning core/boredom.py's own _STATE
# and scripts/lab_env.py use C:\Nascence for -- a job-run worktree has no data/ dir of its own at all,
# and this script's whole point is to read the LIVE store, not whatever (usually absent) copy sits
# next to wherever this file happens to be checked out.
DB_PATH = Path(r"C:\Nascence\data\memory\nascence.db")
WINDOW = 10
MIN_FOR_RISE = 8

# current constants at time of writing (core/boredom.py), for share-below/above comparison
CURRENT_COH_STUCK = 0.76
CURRENT_ESCAPE_COS = 0.52


def blob_to_vec(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32)


def main() -> None:
    days = float(sys.argv[1]) if len(sys.argv) > 1 else 21.0
    candidate_coh = float(sys.argv[2]) if len(sys.argv) > 2 else None
    candidate_esc = float(sys.argv[3]) if len(sys.argv) > 3 else None
    cutoff = time.time() - days * 86400.0

    uri = f"file:{DB_PATH.as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT timestamp, embedding FROM memory_fragments "
        "WHERE origin='inner_thought' AND embedding IS NOT NULL AND timestamp >= ? "
        "ORDER BY timestamp ASC",
        (cutoff,),
    ).fetchall()
    conn.close()

    coherences: list = []
    escape_coss: list = []
    window: list = []

    for r in rows:
        raw = blob_to_vec(bytes(r["embedding"])).astype(np.float32)
        norm = float(np.linalg.norm(raw))
        if norm == 0:
            continue
        v = raw / norm

        prev = list(window)
        if len(prev) >= MIN_FOR_RISE:
            pmat = np.stack(prev)
            pcen = pmat.mean(axis=0)
            pcn = float(np.linalg.norm(pcen))
            if pcn > 0:
                escape_coss.append(float(v @ (pcen / pcn)))

        window.append(v)
        window[:] = window[-WINDOW:]
        if len(window) == WINDOW:
            mat = np.stack(window)
            cen = mat.mean(axis=0)
            cn = float(np.linalg.norm(cen))
            if cn > 0:
                coherences.append(float((mat @ (cen / cn)).mean()))

    qs = [1, 5, 10, 20, 25, 50, 75, 80, 90, 95, 99]

    def report(name: str, arr: list) -> None:
        a = np.array(arr, dtype=np.float64)
        print(f"\n{name}: n={len(a)} mean={a.mean():.4f} std={a.std():.4f} "
              f"min={a.min():.4f} max={a.max():.4f}")
        for q in qs:
            print(f"  p{q:<3d} = {float(np.percentile(a, q)):.4f}")

    print(f"DB={DB_PATH}  days_back={days}  cutoff_ts={cutoff:.0f}  rows_fetched={len(rows)}")
    if rows:
        print(f"  first_ts={rows[0]['timestamp']:.0f}  last_ts={rows[-1]['timestamp']:.0f}")

    report("window_coherence (WINDOW=10, mean cos to own centroid)", coherences)
    report("escape_cos (new thought vs prior<=10 centroid)", escape_coss)

    coh = np.array(coherences, dtype=np.float64)
    esc = np.array(escape_coss, dtype=np.float64)
    if len(coh):
        print(f"\nshare coherence >= CURRENT_COH_STUCK({CURRENT_COH_STUCK}) [reads as 'stuck']: "
              f"{float((coh >= CURRENT_COH_STUCK).mean()) * 100:.2f}%")
    if len(esc):
        print(f"share escape_cos <= CURRENT_ESCAPE_COS({CURRENT_ESCAPE_COS}) [reads as 'escape']: "
              f"{float((esc <= CURRENT_ESCAPE_COS).mean()) * 100:.2f}%")

    if candidate_coh is not None and len(coh):
        print(f"\nshare coherence >= candidate({candidate_coh}): "
              f"{float((coh >= candidate_coh).mean()) * 100:.2f}%")
    if candidate_esc is not None and len(esc):
        print(f"share escape_cos <= candidate({candidate_esc}): "
              f"{float((esc <= candidate_esc).mean()) * 100:.2f}%")


if __name__ == "__main__":
    main()
