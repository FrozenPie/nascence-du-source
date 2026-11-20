"""_test_J-3713_prewarm_pool.py -- after store.prewarm_recall_pool(), the first real retrieve-path pool load fetches
zero BLOBs; the warm is fail-open. Temp DB only. Run: python scripts/_test_J-3713_prewarm_pool.py"""
from __future__ import annotations
import importlib.util, os, sqlite3, sys, tempfile, time
from pathlib import Path
os.environ.setdefault("HF_HUB_OFFLINE", "1")
TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TREE))
import core  # noqa: E402
from core.memory import store as M  # noqa: E402
assert Path(core.__file__).resolve().is_relative_to(TREE)
fails = 0
def check(ok, msg):
    global fails
    print(("  PASS  " if ok else "  FAIL  ") + msg); fails += not ok
spec = importlib.util.spec_from_file_location("_t_fast", str(TREE / "scripts" / "_test_retrieve_fast_pool.py"))
H = importlib.util.module_from_spec(spec); sys.modules["_t_fast"] = H; spec.loader.exec_module(H)
def main():
    tmp = Path(tempfile.mkdtemp(prefix="J-3713_"))
    emb = H._det_embed_factory()
    M.DB_PATH = tmp / "a.db"; M._embed = emb
    M._RETRIEVE_LATENCY_LOG = tmp / "probe.jsonl"; M._POOL_TIDY_LOG = tmp / "tidy.jsonl"
    M._emb_reset(); M._pool_invalidate(); M.init_db()
    now = time.time()
    with sqlite3.connect(tmp / "a.db") as c:
        for i in range(300):
            t = f"memory {i} river garden {i}"
            c.execute("INSERT INTO memory_fragments (fragment_id, content, layer, relevance, timestamp, embedding, origin, "
                      "cold, temp, importance, keywords) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                      (f"f{i:04d}", t, "episodic", 0.5, now - i * 60, emb(t).tobytes(), "lived", 0, "warm", 0.5, "river"))
    for mode in ("off", "on"):
        M._POOL_DELTA_MODE = mode; M._emb_reset(); M._pool_invalidate()
        check(M._EMB_N == 0, f"[{mode}] matrix empty before warm")
        r = M.prewarm_recall_pool()
        check(r["ok"] and r["rows"] == 300 and M._EMB_N == 300, f"[{mode}] warm filled matrix: {r}")
        calls = []; orig = M._emb_fetch
        M._emb_fetch = lambda conn, need: (calls.append(len(need)), orig(conn, need))[1]
        try:
            with M._connect() as conn:
                rows, _ = M._load_pool(conn, emb("river garden"), ["river"])
        finally:
            M._emb_fetch = orig
        check(len(rows) == 300 and sum(calls) == 0, f"[{mode}] first real load fetched zero BLOBs (calls={calls})")
    M._POOL_DELTA_MODE = "off"
    M.DB_PATH = tmp / "nonexistent_dir" / "x" / "\0bad"
    r = M.prewarm_recall_pool()
    check(r["ok"] is False and "ms" in r, f"fail-open on error, no raise: {r.get('error','')[:60]}")
    print("FAILS:", fails); return fails
sys.exit(main())
