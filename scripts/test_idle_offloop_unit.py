"""scripts/test_idle_offloop_unit.py (J-1918 / F-2547): fast synthetic proof of core/idle_offloop.off_loop and the three locks that make
its overlap safe -- touches no data, no DB, no network, no model (a dummy NodeBase subclass and plain functions only).
(1) a 1.5 s blocking call awaited through off_loop does not stall a 0.05 s canary on the same loop (max lag < 0.25 s) and runs on
another thread; (2) with IDLE_LOOKUPS_OFFLOOP=False the same call runs inline on the loop thread and DOES stall it (kill switch =
old behaviour); (3) awaiting keeps the caller sequential, kwargs pass through, and an exception in the worker is raised into the
caller's own try/except exactly like the sync call; (4) NodeBase.run() accepts BOTH a sync and an async _write_output (curiosity's is
async since J-1918) and a NonLiveWriteError from an async one still propagates; (5) associative_recall._matrix() hands back a SNAPSHOT
(a refresh on another thread cannot change what a caller already holds) and its lock is re-entrant and blocks a second thread;
(6) store._EMBED_LOCK and memory_service._SHADOW_LOCK exist and serialise."""
import sys, time, asyncio, threading, pathlib
HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import core                                                       # core BEFORE anything else; assert the tree under test
assert pathlib.Path(core.__file__).resolve().parent.parent == HERE, core.__file__
from core import idle_offloop, associative_recall, memory_service, profile
from core.memory import store
from core.node_base import NodeBase


async def canary_max(stop, lags):
    last = time.perf_counter()
    while not stop.is_set():
        await asyncio.sleep(0.05); n = time.perf_counter(); lags.append(n - last - 0.05); last = n


async def run(flag):
    idle_offloop.IDLE_LOOKUPS_OFFLOOP = flag
    stop = asyncio.Event(); lags = []; ct = asyncio.create_task(canary_max(stop, lags)); await asyncio.sleep(0.2)
    order = []; threads = []
    def slow(tag, *, extra=None):
        threads.append(threading.get_ident()); order.append(("start", tag)); time.sleep(1.5); order.append(("end", tag)); return (tag, extra)
    r1 = await idle_offloop.off_loop(slow, "a", extra=1); order.append(("after", "a")); r2 = await idle_offloop.off_loop(slow, "b")
    def boom(): raise ValueError("x")
    try:
        await idle_offloop.off_loop(boom); raised = False
    except ValueError:
        raised = True
    await asyncio.sleep(0.2); stop.set(); await ct
    return max(lags), order, (r1, r2), raised, threads, threading.get_ident()


ok = True
def check(name, cond):
    global ok
    ok &= bool(cond); print(("PASS " if cond else "FAIL ") + name)

mx, order, res, raised, th, main_th = asyncio.run(run(True))
print("offloop ON : max canary lag %.3f s, order %s" % (mx, order))
check("(1) ON: loop not stalled (< 0.25 s)", mx < 0.25)
check("(1) ON: ran on a worker thread", all(t != main_th for t in th))
check("(3) sequential order + kwargs + result", order == [("start","a"),("end","a"),("after","a"),("start","b"),("end","b")] and res == (("a", 1), ("b", None)))
check("(3) exception re-raised into the caller", raised)
mx2, order2, res2, raised2, th2, main_th2 = asyncio.run(run(False))
print("offloop OFF: max canary lag %.3f s (inline, the old behaviour)" % mx2)
check("(2) OFF: stalls the loop like the old code (> 1.0 s)", mx2 > 1.0)
check("(2) OFF: ran inline on the loop thread", all(t == main_th2 for t in th2))
check("(2) OFF: same result + exception", res2 == (("a", 1), ("b", None)) and raised2)
idle_offloop.IDLE_LOOKUPS_OFFLOOP = True


# (4) NodeBase.run with sync / async / raising-async _write_output
class _N(NodeBase):
    node_id = "j1918_dummy"
    def __init__(self, kind):
        self.kind = kind; self.got = None; self.base_urls = ["x"]; self.max_tokens = 8
        import logging; self.logger = logging.getLogger("j1918dummy")
    def _build_prompt(self, state): return "p"
    def system_prompt_for(self, state): return "s"
    @property
    def system_prompt(self): return "s"
    def _temperature(self, state): return 0.5
    def _log_teacher_example(self, *a, **k): pass
    def _write_output(self, state, data):
        if self.kind == "sync":
            self.got = ("sync", data); return None
        async def _a():
            await asyncio.sleep(0.01)
            if self.kind == "raise":
                raise profile.NonLiveWriteError("nonlive")
            self.got = ("async", data)
        return _a()

import core.node_base as nb
async def fake_cnj(*a, **k): return {"k": 1}
nb.call_node_json = fake_cnj
async def node_runs():
    out = {}
    for kind in ("sync", "async"):
        n = _N(kind); r = await n.run(None); out[kind] = (r, n.got)
    n = _N("raise")
    try:
        await n.run(None); out["raise"] = "swallowed"
    except profile.NonLiveWriteError:
        out["raise"] = "propagated"
    return out
try:
    nr = asyncio.run(node_runs())
    check("(4) NodeBase.run: sync _write_output", nr["sync"] == (True, ("sync", {"k": 1})))
    check("(4) NodeBase.run: async _write_output awaited", nr["async"] == (True, ("async", {"k": 1})))
    check("(4) NodeBase.run: NonLiveWriteError from an async writer propagates", nr["raise"] == "propagated")
except TypeError as exc:      # the dummy cannot be constructed on a tree without the needed NodeBase shape: report, do not hide
    check("(4) NodeBase dummy constructible: " + repr(exc)[:100], False)

# (5) _matrix snapshot + lock
associative_recall._cache.update(ts=time.time(), M="MA", ids=["a"], imp="IA", age="AA", walled="WA", origin=["o"])
snap = associative_recall._matrix()
check("(5) _matrix returns a copy, not the live dict", snap is not associative_recall._cache and snap["M"] == "MA")
associative_recall._cache.update(M="MB", ids=["b"], imp="IB")        # a 'refresh' on another thread
check("(5) a held snapshot is unchanged by a later refresh", snap["M"] == "MA" and snap["ids"] == ["a"] and snap["imp"] == "IA")
lk = associative_recall._MATRIX_LOCK; got = []
with lk:
    with lk:
        pass                                                         # re-entrant
    t = threading.Thread(target=lambda: (lk.acquire(timeout=0.3) and (got.append(1), lk.release()))); t.start(); t.join()
check("(5) _MATRIX_LOCK re-entrant, blocks a second thread while held", got == [])
associative_recall._cache.update(ts=0.0, M=None, ids=None, imp=None, age=None, walled=None, origin=None)
# (6) the other two locks
for name, lk in (("store._EMBED_LOCK", store._EMBED_LOCK), ("memory_service._SHADOW_LOCK", memory_service._SHADOW_LOCK)):
    got = []
    with lk:
        t = threading.Thread(target=lambda: (lk.acquire(timeout=0.3) and (got.append(1), lk.release()))); t.start(); t.join()
    check(f"(6) {name} blocks a second thread while held", got == [])

print("PASS" if ok else "FAIL"); sys.exit(0 if ok else 1)
