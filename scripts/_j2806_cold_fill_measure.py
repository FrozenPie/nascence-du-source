"""J-2806 (read-only measurement): time store._load_pool_fast COLD (empty _EMB_MAT) vs WARM on the live DB, opened
immutable+read-only (Du is down; nothing is written, no PRAGMA is run on the live file).
Usage: python scripts/_j2806_cold_fill_measure.py [runs]   -> prints one JSON line per run + a summary."""
import sys, time, json, sqlite3
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import numpy as np
from core.memory import store          # import core BEFORE any lab_env
LIVE = "file:C:/Nascence/data/memory/nascence.db?mode=ro&immutable=1"

def main(runs=3):
    conn = sqlite3.connect(LIVE, uri=True)
    conn.row_factory = sqlite3.Row
    rng = np.random.default_rng(7)
    q = rng.standard_normal(384).astype(np.float32); q /= np.linalg.norm(q)
    out = []
    for i in range(runs):
        store._emb_reset()
        t = time.perf_counter(); rows = store._load_pool_fast(conn, q, ["x"]); cold = (time.perf_counter() - t) * 1000
        t = time.perf_counter(); rows2 = store._load_pool_fast(conn, q, ["x"]); warm = (time.perf_counter() - t) * 1000
        rec = {"run": i, "pool_rows": len(rows), "emb_n": store._EMB_N, "cold_ms": round(cold), "warm_ms": round(warm)}
        out.append(rec); print(json.dumps(rec))
    # decompose one cold fill: the BLOB fetch alone vs the membership scan
    store._emb_reset()
    cur = conn.cursor(); cur.row_factory = None
    t = time.perf_counter()
    mem = cur.execute("SELECT rowid, fragment_id, layer, timestamp, origin, (embedding IS NOT NULL AND length(embedding) > 0) AS has_emb "
                      + store._POOL_SQL_WHERE).fetchall()
    t_mem = (time.perf_counter() - t) * 1000
    need = [(r[1], r[3]) for r in mem if r[5]]
    t = time.perf_counter()
    with store._EMB_LOCK:
        store._emb_fetch(conn, need)
    t_fetch = (time.perf_counter() - t) * 1000
    print(json.dumps({"decompose": True, "membership_ms": round(t_mem), "emb_fetch_ms": round(t_fetch), "blobs": len(need)}))
    return out

if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 3)
