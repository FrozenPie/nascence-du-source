"""
_test_J-2806_retrieve_outliers.py -- proving test for the two MECHANISMS J-2806 found behind the slow fast-path retrieve()
calls (F-3447 outliers).  Pure mechanism checks on a synthetic temp DB; the live store is never opened (the analysis
itself, scripts/_j2806_*.py, reads the live logs read-only and is not run here).

  1. cold fill: the first _load_pool_fast / _load_pool_delta call after _emb_reset() fetches every embedding BLOB, the
     second fetches none; and store.prewarm() (the only boot warm today) leaves the embedding matrix EMPTY.
  2. delta re-read plan flip: with >= 9 distinct changed ids the by_key membership re-read leaves the PK index for a
     MULTI-INDEX OR over idx_chapter (a table-sized scan, ~550-650 ms on the live 52k pool); a unary plus on chapter_id
     keeps it on the PK for any list length and returns the identical rows.  The test PASSES whether or not the defect
     is present in store.py (it reports DEFECT PRESENT / FIXED) -- it asserts the property of the proposed rewrite.

Run from a worktree:  python scripts/_test_J-2806_retrieve_outliers.py
"""
from __future__ import annotations

import importlib.util
import os
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
import numpy as np

TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TREE))
import core  # noqa: E402  (import core FIRST)
from core.memory import store as M  # noqa: E402

assert Path(core.__file__).resolve().is_relative_to(TREE), f"core resolved outside tree: {core.__file__}"
_fails = 0


def check(ok: bool, msg: str) -> None:
    global _fails
    print(("  PASS  " if ok else "  FAIL  ") + msg)
    if not ok:
        _fails += 1


spec = importlib.util.spec_from_file_location("_t_fast", str(TREE / "scripts" / "_test_retrieve_fast_pool.py"))
H = importlib.util.module_from_spec(spec)
sys.modules["_t_fast"] = H
spec.loader.exec_module(H)


def plan(c: sqlite3.Connection, sql: str, n: int) -> str:
    return " | ".join(r[3] for r in c.execute("EXPLAIN QUERY PLAN " + sql, ["a"] * n))


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="J-2806_"))
    emb = H._det_embed_factory()
    M.DB_PATH = tmp / "a.db"
    M._embed = emb
    M._RETRIEVE_LATENCY_LOG = tmp / "probe.jsonl"
    M._POOL_TIDY_LOG = tmp / "tidy.jsonl"
    M._POOL_DELTA_MODE = "on"
    M._emb_reset()
    M._pool_invalidate()
    M.init_db()
    now = time.time()
    with sqlite3.connect(tmp / "a.db") as c:
        for i in range(300):
            t = f"memory {i} river garden {i}"
            chap = "ch1" if i % 10 == 0 else None
            c.execute("INSERT INTO memory_fragments (fragment_id, content, layer, relevance, timestamp, embedding, origin, "
                      "cold, temp, importance, keywords, chapter_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                      (f"f{i:04d}", t, "episodic", 0.5, now - i * 60, emb(t).tobytes(), "lived", 1 if i % 17 == 0 else 0,
                       "warm", 0.5, "river", chap))
    qv = emb("river garden")
    keys = ["river"]

    print("== 1. cold fill ==")
    fetched = []
    real_fetch = M._emb_fetch

    def counting_fetch(conn, need):
        fetched.append(len(need))
        return real_fetch(conn, need)

    M._emb_fetch = counting_fetch
    try:
        M._emb_reset()
        with M._connect() as conn:
            pool = M._load_pool_fast(conn, qv, keys)
            n1 = sum(fetched)
            M._load_pool_fast(conn, qv, keys)
            n2 = sum(fetched) - n1
        check(n1 == len(pool) and len(pool) > 200, f"first call fetches every pool BLOB ({n1} of a {len(pool)}-row pool)")
        check(n2 == 0, "second call fetches none (warm)")
        M._emb_reset()
        M._pool_invalidate()
        before = sum(fetched)
        with M._connect() as conn:
            M._load_pool_delta(conn, qv, keys)
        check(sum(fetched) - before == len(pool), "delta path: the rebuild after a reset pays the same full fetch")
        # prewarm() warms only the embedder: stub the model and confirm the matrix stays empty
        class _Stub:
            def encode(self, *a, **k):
                return np.zeros(384, dtype=np.float32)
        M._emb_reset()
        saved = M._get_model
        M._get_model = lambda: _Stub()
        try:
            M.prewarm()
        finally:
            M._get_model = saved
        check(M._EMB_N == 0 and M._EMB_MAT is None, "store.prewarm() leaves _EMB_MAT empty -> the first retrieve() still pays the fill")
    finally:
        M._emb_fetch = real_fetch

    print("== 2. delta re-read plan flip at >= 9 changed ids ==")
    c = sqlite3.connect(tmp / "a.db")
    cur_sql = lambda n: M._pool_select_sql(f" AND fragment_id IN ({','.join('?' * n)})", by_key=True).replace("(+chapter_id IS NULL OR +chapter_id = '')", "(chapter_id IS NULL OR chapter_id = '')")  # J-3712: fix is in store.py now; revert it here to keep proving the defect
    alt_sql = lambda n: cur_sql(n).replace("(chapter_id IS NULL OR chapter_id = '')", "(+chapter_id IS NULL OR +chapter_id = '')")
    check(alt_sql(3) != cur_sql(3), "the rewrite actually changes the SQL text (guards a silent no-op replace)")
    flips = [n for n in range(1, 40) if "MULTI-INDEX OR" in plan(c, cur_sql(n), n)]
    print(f"  INFO  current by_key plan leaves the PK index at n = {flips[0] if flips else None} ids -> "
          + ("DEFECT PRESENT" if flips else "FIXED / not reproduced in this sqlite"))
    for n in (1, 2, 8, 9, 10, 50, 900):
        p = plan(c, alt_sql(n), n)
        check("sqlite_autoindex_memory_fragments_1" in p and "MULTI-INDEX OR" not in p, f"rewrite stays on the PK index at n={n}")
    ids = [r[0] for r in c.execute("SELECT fragment_id FROM memory_fragments")]
    for n in (1, 9, 40, 300):
        a = sorted(c.execute(cur_sql(n), ids[:n]).fetchall())
        b = sorted(c.execute(alt_sql(n), ids[:n]).fetchall())
        check(a == b, f"rewrite returns identical rows at n={n} ({len(a)} rows; includes cold and chaptered ids that must be excluded)")
    c.close()
    print(f"\n{'ALL PASS' if not _fails else str(_fails) + ' FAILED'}")
    return 1 if _fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
