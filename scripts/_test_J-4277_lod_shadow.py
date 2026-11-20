"""J-4277: LOD shadow. Temp DB + temp log only. Checks retrieve() byte-identical flag on/off, shadow rows written, cascade shape."""
import os, sys, tempfile, json
from pathlib import Path
os.environ.setdefault("HF_HUB_OFFLINE", "1"); os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
sys.path.insert(0, str(Path(__file__).parent.parent))
_TMP = Path(tempfile.mkdtemp(prefix="lod_shadow_test_"))
import numpy as np
import core.memory.store as store
store.DB_PATH = _TMP / "test.db"
store._LOD_SHADOW_LOG = _TMP / "lod_shadow.jsonl"
from scripts._test_isolation import redirect_world_stores
try: redirect_world_stores(_TMP)
except Exception as e: print("redirect note:", e)
store.init_db()
rng = np.random.default_rng(1)
with store._connect() as c:
    for i in range(60):
        lvl = 0 if i < 40 else 1 if i < 55 else 2
        v = rng.standard_normal(384).astype(np.float32); v /= np.linalg.norm(v)
        c.execute("INSERT INTO memory_fragments (fragment_id, content, layer, timestamp, embedding, abstraction_level) VALUES (?,?,?,?,?,?)",
                  (f"f{i}", f"content {i}", "episodic", 1000.0 + i, store._vec_to_blob(v), lvl))
q = rng.standard_normal(384).astype(np.float32); q /= np.linalg.norm(q)
store._embed = lambda t: q
ok = True
def chk(n, c):
    global ok; ok &= bool(c); print(("PASS " if c else "FAIL ") + n)
def ids(): return [(f.fragment_id, f.content, f.relevance) for f in store.retrieve([], [], limit=8, query_text="hello")]
store.LOD_RETRIEVAL_SHADOW = False; a = ids()
chk("flag off: no log file", not store._LOD_SHADOW_LOG.exists())
store.LOD_RETRIEVAL_SHADOW = True; b = ids()
chk("retrieve byte-identical flag off/on", a == b)
rows = [json.loads(l) for l in store._LOD_SHADOW_LOG.read_text().splitlines()]
chk("shadow row written with keys", len(rows) == 1 and {"query","baseline_ids","lod_ids"} <= set(rows[0]))
cand = store._lod_staged_candidates(q, 10)
lv = [r["abstraction_level"] for _, r in cand]
chk("cascade 2xL2,3xL1,5xL0", lv.count(2) == 2 and lv.count(1) == 3 and lv.count(0) == 5)
chk("LOD_RETRIEVAL_LIVE False", store.LOD_RETRIEVAL_LIVE is False)
print("ALL PASS" if ok else "FAILURES"); sys.exit(0 if ok else 1)
