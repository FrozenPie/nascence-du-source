"""J-1838/D-0352: _drift_from's recency pool caps inner_thought at 25% of the 1500-pool, filling from the next
most recent non-inner_thought rows. Synthetic in-memory sqlite only -- no live store is opened."""
import sys, os, sqlite3
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import core
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
assert os.path.abspath(core.__file__).startswith(root), core.__file__
from core import wandering as w
import numpy as np

W = ("embedding IS NOT NULL AND layer IN ('episodic','semantic','archive') AND chapter_id IS NULL")

def mk(rows):
    c = sqlite3.connect(":memory:"); c.row_factory = sqlite3.Row
    c.execute("CREATE TABLE memory_fragments (fragment_id TEXT, content TEXT, origin TEXT, embedding BLOB, "
              "layer TEXT, chapter_id TEXT, timestamp REAL)")
    blob = np.ones(4, dtype=np.float32).tobytes()
    for i, (origin, ts) in enumerate(rows):
        c.execute("INSERT INTO memory_fragments VALUES (?,?,?,?,?,?,?)", (f"f{i}", f"c{i}", origin, blob, "episodic", None, ts))
    return c

def comp(rows):
    inner = sum(1 for r in rows if r["origin"] == "inner_thought")
    return inner, len(rows)

# 1. binding: 3000 rows, alternating-ish 60% inner (newest first by ts) -> pool 1500, inner exactly 375, ids unique
rows = [("inner_thought" if i % 5 < 3 else "reading", 10000 - i) for i in range(3000)]
p = w._recency_pool(mk(rows), W)
inner, n = comp(p)
assert n == 1500 and inner == 375, (inner, n)
assert len({r["fragment_id"] for r in p}) == 1500
# the kept inner rows are the 375 most recent inner rows; the fill is the most recent non-inner rows
inner_ids = sorted(int(r["fragment_id"][1:]) for r in p if r["origin"] == "inner_thought")
exp_inner = [i for i in range(3000) if i % 5 < 3][:375]
assert inner_ids == exp_inner, inner_ids[:5]
other_ids = sorted(int(r["fragment_id"][1:]) for r in p if r["origin"] != "inner_thought")
exp_other = [i for i in range(3000) if i % 5 >= 3][:1125]
assert other_ids == exp_other

# 2. not binding: 10% inner -> byte-identical to plain recency pool
rows = [("inner_thought" if i % 10 == 0 else "reading", 10000 - i) for i in range(3000)]
c = mk(rows)
p = w._recency_pool(c, W)
plain = c.execute(f"SELECT fragment_id, content, origin, embedding FROM memory_fragments WHERE {W} ORDER BY timestamp DESC LIMIT 1500").fetchall()
assert [r["fragment_id"] for r in p] == [r["fragment_id"] for r in plain]

# 3. short supply of non-inner: pool shrinks, never above the cap, no crash
rows = [("inner_thought", 10000 - i) for i in range(1400)] + [("reading", 100 - i) for i in range(50)]
inner, n = comp(w._recency_pool(mk(rows), W))
assert inner == 375 and n == 425, (inner, n)

# 4. NULL origin is not inner_thought and is eligible for the fill
rows = [("inner_thought", 10000 - i) for i in range(1500)] + [(None, 5 - i * 0.001) for i in range(10)]
p = w._recency_pool(mk(rows), W)
assert comp(p) == (375, 385) and sum(1 for r in p if r["origin"] is None) == 10

# 5. world-only where clause (inner_count>=3 rule) -> no inner_thought rows at all, unchanged path
w._trail.clear(); w._trail.extend([{"origin": "inner_thought"}] * 3)
assert w._inner_count() == 3
W2 = W + " AND origin IN ('reading','research','study','essay','understanding')"
rows = [("inner_thought" if i % 2 else "reading", 10000 - i) for i in range(3000)]
p = w._recency_pool(mk(rows), W2)
assert comp(p) == (0, 1500)

# 6. end-to-end _drift_from on a synthetic DB: read-only, returns <=2 items, inner share of picks bounded
import core.memory_edges as me
me.log_co_recall = lambda *a, **k: None
w._trail.clear(); w._recently_visited.clear()
rng = np.random.default_rng(0)
c = sqlite3.connect(":memory:"); c.row_factory = sqlite3.Row
c.execute("CREATE TABLE memory_fragments (fragment_id TEXT, content TEXT, origin TEXT, embedding BLOB, layer TEXT, chapter_id TEXT, timestamp REAL)")
for i in range(3000):
    v = rng.normal(size=8).astype(np.float32)
    c.execute("INSERT INTO memory_fragments VALUES (?,?,?,?,?,?,?)", (f"f{i}", f"c{i}", "inner_thought" if i % 5 < 3 else "reading", v.tobytes(), "episodic", None, 10000 - i))
before = c.total_changes
out = w._drift_from(rng.normal(size=8).astype(np.float32), c)
assert len(out) == 2 and c.total_changes == before
w._recently_visited.clear(); w._trail.clear()
print("OK")
