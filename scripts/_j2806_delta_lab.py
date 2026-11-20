"""J-2806 LAB (runs on a COPY of the live DB, never the live file): why is the live fast+delta path slow (p50 ~430 ms)
when an isolated warm delta call is ~20 ms?  Applies realistic write batches to the copy between calls and times
store._load_pool_delta; also times a delta call while a second connection holds a read snapshot and a large WAL exists.
Usage: python scripts/_j2806_delta_lab.py <path-to-copy.db>"""
import sys, time, json, sqlite3, uuid, os
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import numpy as np
from core.memory import store
DB = sys.argv[1]
assert "nascence_J2806" in DB, "refusing to touch anything but the J-2806 copy"
q = np.random.default_rng(7).standard_normal(384).astype(np.float32); q /= np.linalg.norm(q)
def reader():
    c = sqlite3.connect(DB, timeout=30); c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL"); c.execute("PRAGMA busy_timeout=30000"); return c
def writer():
    c = sqlite3.connect(DB, timeout=30); c.execute("PRAGMA journal_mode=WAL"); c.execute("PRAGMA busy_timeout=30000"); return c
def timed(conn):
    s = time.perf_counter(); r = store._load_pool_delta(conn, q, ["x"]); return round((time.perf_counter() - s) * 1000, 1), len(r), dict(store._POOL.stats)
rc = reader(); wc = writer()
store._emb_reset(); store._pool_invalidate()
print("cold rebuild", timed(rc)); print("warm no-change", timed(rc))
blob = (np.random.default_rng(1).standard_normal(384).astype(np.float32)).tobytes()
cols = [r[1] for r in wc.execute("pragma table_info(memory_fragments)")]
tpl = wc.execute("select * from memory_fragments where cold=0 and chapter_id is null and length(embedding)>0 limit 1").fetchone()
def insert_new(n):
    for _ in range(n):
        row = list(tpl); row[cols.index("fragment_id")] = str(uuid.uuid4()); row[cols.index("embedding")] = blob
        row[cols.index("timestamp")] = time.time(); row[cols.index("content_hash")] = str(uuid.uuid4())
        wc.execute(f"insert into memory_fragments values ({','.join('?'*len(cols))})", row)
    wc.commit()
def demote(n):
    ids = [r[0] for r in wc.execute("select fragment_id from memory_fragments where cold=0 and chapter_id is null and origin!='system_note' order by random() limit ?", (n,))]
    wc.executemany("update memory_fragments set cold=1 where fragment_id=?", [(i,) for i in ids]); wc.commit()
def stamp(n):   # an UPDATE OF a watched column that does not change membership (timestamp)
    ids = [r[0] for r in wc.execute("select fragment_id from memory_fragments where cold=0 and chapter_id is null limit ?", (n,))]
    wc.executemany("update memory_fragments set timestamp=timestamp+0.001 where fragment_id=?", [(i,) for i in ids]); wc.commit()
for label, fn, n in [("insert 1", insert_new, 1), ("insert 10", insert_new, 10), ("insert 50", insert_new, 50), ("demote 50", demote, 50),
                     ("stamp 200", stamp, 200), ("insert 500", insert_new, 500), ("insert+demote 2000 (>max?)", insert_new, 2000),
                     ("insert 3500 (> _POOL_DELTA_MAX_CHANGES)", insert_new, 3500)]:
    fn(n); print(label, timed(rc))
# WAL growth with a long-lived reader snapshot (blocks checkpoint), then time the next delta call
hold = reader(); hold.execute("BEGIN"); hold.execute("select count(*) from memory_fragments where fragment_id='x'").fetchone()
for k in range(3):
    insert_new(200); stamp(2000)
wal = Path(DB + "-wal"); print("WAL bytes with a held snapshot:", wal.stat().st_size if wal.exists() else None)
print("delta with big WAL + held snapshot", timed(rc), timed(rc))
hold.rollback()
