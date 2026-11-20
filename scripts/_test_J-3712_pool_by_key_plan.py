"""J-3712 regression: _pool_select_sql(by_key=True) stays on the PK index for n=1..900 ids (no MULTI-INDEX OR over idx_chapter)."""
import os, sys, sqlite3, tempfile
from pathlib import Path
os.environ.setdefault("HF_HUB_OFFLINE", "1")
TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TREE))
import core  # noqa
from core.memory import store as M
fails = 0
def check(ok, msg):
    global fails
    print(("PASS " if ok else "FAIL ") + msg)
    fails += (not ok)
tmp = Path(tempfile.mkdtemp(prefix="J-3712_"))
M.DB_PATH = tmp / "a.db"
M.init_db()
c = sqlite3.connect(tmp / "a.db")
for i in range(300):
    c.execute("INSERT INTO memory_fragments (fragment_id, content, layer, relevance, timestamp, origin, cold, temp, importance, keywords, chapter_id) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
              (f"f{i:04d}", "x", "episodic", .5, float(i), "lived", i % 17 == 0, "warm", .5, "k", "ch1" if i % 10 == 0 else None))
c.commit()
sql = lambda n: M._pool_select_sql(f" AND fragment_id IN ({','.join('?' * n)})", by_key=True)
check("+chapter_id IS NULL OR +chapter_id" in sql(1), "by_key SQL carries unary plus on chapter_id")
check("(chapter_id IS NULL" in M._pool_select_sql(), "non-by_key SQL unchanged")
for n in (1, 8, 9, 10, 50, 300, 900):
    p = " | ".join(r[3] for r in c.execute("EXPLAIN QUERY PLAN " + sql(n), ["a"] * n))
    check("MULTI-INDEX OR" not in p and "autoindex" in p, f"PK plan at n={n}")
ids = [r[0] for r in c.execute("SELECT fragment_id FROM memory_fragments")]
a = sorted(c.execute(sql(300), ids).fetchall())
b = sorted(c.execute(M._pool_select_sql(" AND fragment_id IN (%s)" % ",".join("?" * 300)), ids).fetchall())
check(a == b and 0 < len(a) < 300, f"identical rows to non-by_key form ({len(a)})")
print("ALL PASS" if not fails else f"{fails} FAILED")
sys.exit(1 if fails else 0)
