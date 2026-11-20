"""J-1947 (F-2568): INDEXED BY idx_timestamp must return byte-identical rows/order to the old planner choice.
Temp-path synthetic DB ONLY (never the live DB). Runs the REAL query-bearing functions twice -- once with the
' INDEXED BY idx_timestamp' hint stripped by a connection wrapper (= old SQL), once as shipped -- and compares.
Import core BEFORE lab_env (house rule). Optional: pass a DB copy path as argv[1] to also prove it on real data
(opened mode=ro)."""
import sys, os, sqlite3, random, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import core.wandering as W
import core.memory.store as S

HINT = " INDEXED BY idx_timestamp"

class Conn:
    def __init__(self, c, strip): self.c, self.strip = c, strip
    def execute(self, sql, *a):
        return self.c.execute(sql.replace(HINT, "") if self.strip else sql, *a)
    def __enter__(self): return self
    def __exit__(self, *a): return False

def build(path, n=6000):
    random.seed(1947)
    c = sqlite3.connect(path); c.row_factory = sqlite3.Row
    c.executescript("""CREATE TABLE memory_fragments (fragment_id TEXT PRIMARY KEY, content TEXT, layer TEXT, relevance REAL,
      timestamp REAL, keywords TEXT, embedding BLOB, origin TEXT, derived_from TEXT, chapter_id TEXT, emotion_embedding BLOB);
      CREATE INDEX idx_layer ON memory_fragments(layer); CREATE INDEX idx_timestamp ON memory_fragments(timestamp DESC);
      CREATE INDEX idx_chapter ON memory_fragments(chapter_id);""")
    ts = random.sample(range(1, 10_000_000), n)
    for i, t in enumerate(ts):
        vec = bytes(random.getrandbits(8) for _ in range(16))
        origin = random.choice(["inner_thought"] * 5 + ["reading", "study", "research", "essay", "understanding", "lived"])
        c.execute("INSERT INTO memory_fragments VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                  (f"f{i}", f"c{i}", random.choice(["episodic", "semantic", "archive", "episodic"]), .5, float(t), "",
                   vec if random.random() < .9 else None, origin, "[]",
                   None if random.random() < .55 else "ch1", vec if random.random() < .7 else None))
    c.commit(); return c

def main():
    d = tempfile.mkdtemp(prefix="j1947_"); c = build(os.path.join(d, "t.db"))
    if len(sys.argv) > 1:
        c = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True); c.row_factory = sqlite3.Row
    W._POOL_SIZE = 1500 if len(sys.argv) > 1 else 800
    base = ("embedding IS NOT NULL AND layer IN ('episodic','semantic','archive') AND chapter_id IS NULL")
    shapes = {"plain": base, "world_only": base + " AND origin IN ('reading','research','study','essay','understanding')"}
    fails = 0
    # plan check: shipped SQL must actually use idx_timestamp
    plan = c.execute("EXPLAIN QUERY PLAN SELECT fragment_id FROM memory_fragments" + HINT + " WHERE " + base +
                     " ORDER BY timestamp DESC LIMIT 10").fetchall()
    ok = any("idx_timestamp" in str(tuple(r)) for r in plan) and not any("TEMP B-TREE" in str(tuple(r)) for r in plan)
    print("plan uses idx_timestamp, no temp b-tree:", ok); fails += not ok
    for name, where in shapes.items():
        old = [r["fragment_id"] for r in W._recency_pool(Conn(c, True), where)]
        new = [r["fragment_id"] for r in W._recency_pool(Conn(c, False), where)]
        print(f"_recency_pool[{name}] n={len(new)} identical={old == new}"); fails += old != new or not new
    # cap branch: force inner_thought over the cap (plain shape, shrink share to 0.0 -> always re-queries)
    W._INNER_POOL_SHARE = 0.05
    old = [r["fragment_id"] for r in W._recency_pool(Conn(c, True), base)]
    new = [r["fragment_id"] for r in W._recency_pool(Conn(c, False), base)]
    print(f"_recency_pool[cap branch] n={len(new)} identical={old == new}"); fails += old != new or not new
    # _affective_drift: same chosen fragment
    mood = c.execute("SELECT emotion_embedding e FROM memory_fragments WHERE emotion_embedding IS NOT NULL LIMIT 1").fetchone()["e"]
    import numpy as np
    mv = np.frombuffer(bytes(mood), dtype=np.float32) if len(mood) % 4 == 0 else None
    sqls = {}
    for strip in (True, False):
        rows = Conn(c, strip).execute(
            "SELECT fragment_id FROM memory_fragments" + HINT + " WHERE emotion_embedding IS NOT NULL AND chapter_id IS NULL "
            "AND origin IN ('reading','study','research','essay','understanding') ORDER BY timestamp DESC LIMIT 800").fetchall()
        sqls[strip] = [r[0] for r in rows]
    # also assert the source text carries the hint in all 4 places so the proof above mirrors shipped SQL
    import inspect
    src = inspect.getsource(W._affective_drift) + inspect.getsource(W._recency_pool) + inspect.getsource(S.retrieve_by_affect)
    n_hint = src.count("INDEXED BY idx_timestamp"); print("hint occurrences in shipped source (expect 4):", n_hint); fails += n_hint != 4
    print(f"_affective_drift SQL identical={sqls[True] == sqls[False]} n={len(sqls[True])}"); fails += sqls[True] != sqls[False] or not sqls[True]
    # retrieve_by_affect: run the real function through patched _connect, old vs new
    ev = np.random.RandomState(1).rand(384).astype(np.float32)
    res = {}
    for strip in (True, False):
        S._connect = lambda strip=strip: Conn(c, strip)
        res[strip] = [(f.fragment_id, f.relevance) for f in S.retrieve_by_affect(ev, top_k=300)]
    rows = {}
    for strip in (True, False):
        rows[strip] = [r[0] for r in Conn(c, strip).execute(
            "SELECT fragment_id FROM memory_fragments" + HINT + " WHERE layer = 'episodic' AND emotion_embedding IS NOT NULL "
            "AND chapter_id IS NULL ORDER BY timestamp DESC LIMIT 300").fetchall()]
    print(f"retrieve_by_affect function identical={res[True] == res[False]}; SQL ids identical={rows[True] == rows[False]} n={len(rows[True])}")
    fails += res[True] != res[False] or rows[True] != rows[False]
    print("RESULT:", "FAIL" if fails else "PASS"); return 1 if fails else 0

if __name__ == "__main__": sys.exit(main())
