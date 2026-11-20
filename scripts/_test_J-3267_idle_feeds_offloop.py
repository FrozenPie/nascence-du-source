"""J-3267 (D-0658): the founder-recall retrieve and recall_block run through off_loop in _think.
Static (AST) check on the node source + a behavioural loop-lag check with stand-in blocking callables.
Touches no live data; writes nothing."""
import ast, asyncio, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401  (core before lab_env)
from core import idle_offloop  # noqa: E402

src = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
tree = ast.parse(src)
think = next(n for n in ast.walk(tree) if isinstance(n, ast.AsyncFunctionDef) and n.name == "_think")

def awaited_calls(fn):
    out = []
    for n in ast.walk(fn):
        if isinstance(n, ast.Await) and isinstance(n.value, ast.Call):
            out.append(ast.unparse(n.value))
    return out

aw = awaited_calls(think)
assert any(c.startswith("_idle_off3(_rfm,") and "bump_replay=False" in c for c in aw), aw
assert any(c.startswith("_idle_off4(_rb_with_ids)") for c in aw), aw
# no bare synchronous call remains
bare = [ast.unparse(n) for n in ast.walk(think) if isinstance(n, ast.Call)
        and ast.unparse(n.func) in ("_rfm", "_ar3.recall_block")
        and not any(ast.unparse(n) in c for c in aw)]
# the only remaining direct _ar3.recall_block call lives inside the nested helper (run in the worker)
assert all("recall_block" in b for b in bare), bare
print("static ok")

async def lag_test():
    calls = {}
    def fake_block(q):
        calls["thread"] = __import__("threading").current_thread().name
        time.sleep(0.4)
        return "BLOCK", None
    gaps = []
    async def ticker():
        last = time.perf_counter()
        for _ in range(30):
            await asyncio.sleep(0.02)
            now = time.perf_counter(); gaps.append(now - last); last = now
    t = asyncio.create_task(ticker())
    res = await idle_offloop.off_loop(fake_block, "x")
    await t
    assert res == ("BLOCK", None)
    assert calls["thread"] != __import__("threading").main_thread().name
    assert max(gaps) < 0.2, max(gaps)      # the loop kept ticking while the 0.4 s call ran
    # contrast: kill-switch off = old behaviour, loop stalls
    idle_offloop.IDLE_LOOKUPS_OFFLOOP = False
    gaps.clear()
    t = asyncio.create_task(ticker())
    await asyncio.sleep(0)
    await idle_offloop.off_loop(fake_block, "x")
    await t
    idle_offloop.IDLE_LOOKUPS_OFFLOOP = True
    assert max(gaps) >= 0.35, max(gaps)
asyncio.run(lag_test())
print("lag ok")

# helper pattern: ids read in the same worker thread as the call
class AR:
    ids = []
    def recall_block(self, q): self.ids[:] = ["a", "b"]; return "blk"
    def last_block_ids(self): return list(self.ids)
ar = AR()
def _rb(_p="p"):
    b = ar.recall_block(_p); return b, ar.last_block_ids()
assert asyncio.run(idle_offloop.off_loop(_rb)) == ("blk", ["a", "b"])
print("ALL OK")
