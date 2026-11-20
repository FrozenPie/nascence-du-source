"""J-2806 LAB (on the COPY only): does a large un-checkpointed WAL (a held reader blocks the checkpoint) slow the
fast-path read?  Times store._load_pool_fast before, with a big WAL, and after the checkpoint."""
import sys, time, sqlite3
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import numpy as np
from core.memory import store
DB = sys.argv[1]; assert "nascence_J2806" in DB
q = np.random.default_rng(7).standard_normal(384).astype(np.float32); q /= np.linalg.norm(q)
def conn():
    c = sqlite3.connect(DB, timeout=30); c.row_factory = sqlite3.Row; c.execute("PRAGMA journal_mode=WAL"); c.execute("PRAGMA busy_timeout=30000"); return c
rc = conn(); wc = conn(); hold = conn()
store._emb_reset()
def timed(label, n=3):
    store._load_pool_fast(rc, q, ["x"])   # fill the matrix once
    v = []
    for _ in range(n):
        s = time.perf_counter(); store._load_pool_fast(rc, q, ["x"]); v.append(round((time.perf_counter() - s) * 1000))
    wal = Path(DB + "-wal"); print(label, v, "WAL MB:", round(wal.stat().st_size / 1e6) if wal.exists() else 0)
timed("baseline (WAL after open)")
hold.execute("BEGIN"); hold.execute("select count(*) from memory_fragments").fetchone()   # snapshot: blocks checkpoint past here
for k in range(4):   # ~4 x 1.5 MB-ish rows per 1000 -> grows the WAL; touch 30k rows' timestamp + rewrite
    wc.execute("update memory_fragments set importance=importance where rowid % 4 = ?", (k,)); wc.commit()
    timed(f"after write batch {k} (held snapshot)", 2)
hold.rollback(); hold.close()
wc.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchall()
timed("after checkpoint truncate")
