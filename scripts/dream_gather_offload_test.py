"""J-2178 (F-2882): _find_counterpart / _gather_materials identical with cache+offloop on vs off; the pattern-label
embeds are batched+cached (timing comparison); loop stays responsive. Fake slow embedder only; touches no live data."""
import asyncio, sys, time, hashlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np
import core
assert "wt_dream_offload" in core.__file__, core.__file__
from core.memory import store
from nodes import dream_node as dn

PER_CALL = 0.004   # fake per-text latency (real: ~17 ms each)
def vec(t):
    h = hashlib.sha256(t.encode()).digest()
    v = np.frombuffer((h * 12)[:384], dtype=np.uint8).astype(np.float32) - 127.5
    return v / np.linalg.norm(v)
calls = {"single": 0, "batch_texts": 0}
def fake_embed(t):
    if not t or not t.strip(): return None
    calls["single"] += 1; time.sleep(PER_CALL); return vec(t)
class FakeModel:
    def encode(self, x, **kw):
        if isinstance(x, str): calls["single"] += 1; time.sleep(PER_CALL); return vec(x)
        calls["batch_texts"] += len(x); time.sleep(PER_CALL * len(x) * 0.3); return np.stack([vec(t) for t in x])
store._embed = fake_embed; store._get_model = lambda: FakeModel()

labels = [f"integration pattern number {i}" for i in range(300)]
patterns = [{"label": l} for l in labels] + [{"label": ""}, {"label": "  "}]
tens = ["unresolved tension about pattern 17", "a quiet wish regarding number 250"]

def run(cache):
    dn.DREAM_PATTERN_CACHE = cache; dn._PATTERN_VEC_CACHE.clear()
    calls.update(single=0, batch_texts=0)
    t = time.perf_counter(); res = [dn.DreamNode._find_counterpart(x, patterns) for x in tens]
    return res, time.perf_counter() - t, dict(calls)
r_off, t_off, c_off = run(False)
r_on, t_on, c_on = run(True)
r_warm = [dn.DreamNode._find_counterpart(x, patterns) for x in tens]
assert r_off == r_on == r_warm and all(r_on), (r_off, r_on)
assert c_on["single"] == len(tens), c_on            # only the tension vectors are single; labels batched
assert c_on["batch_texts"] == 300                   # embedded once for BOTH tensions (cached)
print(f"counterpart identical {r_on}; uncached {t_off:.2f}s ({c_off['single']} single embeds) -> cached+batched {t_on:.2f}s; warm repeat 0 batch embeds")
assert t_on < t_off

# off-loop: _gather_materials runs a slow body; loop canary must stay responsive
class Fake(dn.DreamNode):
    def __init__(self): pass
    def _gather_materials(self, state, episodes):
        time.sleep(0.8); return ["m"] * episodes
async def go(flag):
    dn.DREAM_GATHER_OFFLOOP = flag
    lag = []
    async def canary():
        for _ in range(30):
            t = time.perf_counter(); await asyncio.sleep(0.02); lag.append(time.perf_counter() - t - 0.02)
    c = asyncio.create_task(canary()); await asyncio.sleep(0)
    if flag:
        from core.idle_offloop import off_loop
        m = await off_loop(Fake()._gather_materials, None, 2)
    else:
        m = Fake()._gather_materials(None, 2)
    await c; return m, max(lag)
m1, lag_on = asyncio.run(go(True)); m0, lag_off = asyncio.run(go(False))
assert m1 == m0 and lag_on < 0.2, (lag_on,)
print(f"offloop max loop lag {lag_on:.3f}s vs inline {lag_off:.3f}s; materials identical")
src = Path(dn.__file__).read_text(encoding="utf-8")
assert "_off_loop_g(self._gather_materials" in src
# batch fail-open: broken batch falls back to per-text
class Bad:
    def encode(self, x, **kw):
        if isinstance(x, list): raise RuntimeError("boom")
        return vec(x)
store._get_model = lambda: Bad(); store._embed = lambda t: vec(t) if t.strip() else None
out = store._embed_batch(["a", "", "b"])
assert out[1] is None and out[0] is not None and out[2] is not None
print("OK")
