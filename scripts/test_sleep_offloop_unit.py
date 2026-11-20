"""scripts/test_sleep_offloop_unit.py (J-1917): fast synthetic proof of core/sleep_offloop.off_loop -- touches no data, no DB.
(1) a 1.5 s blocking call awaited through off_loop does not stall a 0.05 s canary on the same loop (max lag < 0.25 s);
(2) with SLEEP_SWEEPS_OFFLOOP=False the same call runs inline and DOES stall it (kill switch = old behaviour);
(3) awaiting keeps the caller sequential (step 2 starts only after step 1 returned) and an exception in the worker is raised
into the caller's own try/except exactly like the sync call; (4) world_consolidation's _FILE_LOCK serialises overlapping
file_book_notes calls (a second thread cannot enter while the first holds it) and is re-entrant."""
import sys, time, asyncio, threading, pathlib
HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import core                                                       # core BEFORE anything else; assert the tree under test
assert pathlib.Path(core.__file__).resolve().parent.parent == HERE, core.__file__
from core import sleep_offloop, world_consolidation

async def canary_max(stop, lags):
    last = time.perf_counter()
    while not stop.is_set():
        await asyncio.sleep(0.05); n = time.perf_counter(); lags.append(n - last - 0.05); last = n

async def run(flag):
    sleep_offloop.SLEEP_SWEEPS_OFFLOOP = flag
    stop = asyncio.Event(); lags = []; ct = asyncio.create_task(canary_max(stop, lags)); await asyncio.sleep(0.2)
    order = []
    def slow(tag):
        order.append(("start", tag)); time.sleep(1.5); order.append(("end", tag)); return tag
    r1 = await sleep_offloop.off_loop(slow, "a"); order.append(("after", "a")); r2 = await sleep_offloop.off_loop(slow, "b")
    def boom(): raise ValueError("x")
    try:
        await sleep_offloop.off_loop(boom); raised = False
    except ValueError:
        raised = True
    await asyncio.sleep(0.2); stop.set(); await ct
    return max(lags), order, (r1, r2), raised

ok = True
mx, order, res, raised = asyncio.run(run(True))
print("offloop ON : max canary lag %.3f s, order %s" % (mx, order))
ok &= mx < 0.25 and raised and res == ("a", "b") and order == [("start","a"),("end","a"),("after","a"),("start","b"),("end","b")]
mx2, order2, res2, raised2 = asyncio.run(run(False))
print("offloop OFF: max canary lag %.3f s (inline, the old behaviour)" % mx2)
ok &= mx2 > 1.0 and raised2 and res2 == ("a", "b")
# (4) the lock
lk = world_consolidation._FILE_LOCK; got = []
with lk:
    with lk:                                  # re-entrant
        pass
    t = threading.Thread(target=lambda: (lk.acquire(timeout=0.3) and (got.append(1), lk.release()))); t.start(); t.join()
print("lock blocks a second thread while held:", got == [])
ok &= got == []
print("PASS" if ok else "FAIL"); sys.exit(0 if ok else 1)
