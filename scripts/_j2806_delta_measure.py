"""J-2806 (read-only measurement): warm cost of store._load_pool_delta vs _load_pool_fast on the live DB, opened
immutable+read-only (Du down). Isolated, single thread, OS cache warm -- the floor the live probe should be compared to."""
import sys, time, json, sqlite3
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import numpy as np
from core.memory import store
LIVE = "file:C:/Nascence/data/memory/nascence.db?mode=ro&immutable=1"
conn = sqlite3.connect(LIVE, uri=True); conn.row_factory = sqlite3.Row
q = np.random.default_rng(7).standard_normal(384).astype(np.float32); q /= np.linalg.norm(q)
print("mode", store._POOL_DELTA_MODE)
store._emb_reset(); store._pool_invalidate()
def t(fn):
    s = time.perf_counter(); r = fn(conn, q, ["x"]); return (time.perf_counter() - s) * 1000, len(r)
print("delta call 1 (cold: rebuild + matrix fill)", t(store._load_pool_delta))
for i in range(4):
    print("delta warm", i, t(store._load_pool_delta), store._POOL.stats)
for i in range(3):
    print("fast  warm", i, t(store._load_pool_fast))
n_nan = sum(1 for r in store._load_pool_delta(conn, q, ["x"]) if r._sim != r._sim)
print("rows with no usable embedding (keyword-fallback hydrate each call):", n_nan)
