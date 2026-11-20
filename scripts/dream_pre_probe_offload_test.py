"""J-2296 (F-2993 re-read): the synchronous pre-probe block in DreamNode.synthesise (_last_unresolved_arc,
_carried_n, _met_carry_check, memory_service.ask('dream')) now runs through _pre_probe_call -> off_loop; this checks
the loop stays responsive, results/exceptions are identical on vs off, the kill switch is inline, the four call
sites are wired, and the additive stage_timing record is shaped right. Fake slow bodies only; touches no live data."""
import asyncio, sys, time, threading
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import core
assert str(Path(core.__file__).resolve()).lower().startswith(str(Path(__file__).resolve().parent.parent).lower()), core.__file__
from nodes import dream_node as dn

def slow(x, *, k=1):
    time.sleep(0.6); return (x, k, threading.get_ident())
def boom():
    time.sleep(0.1); raise ValueError("boom")

async def go(flag):
    dn.DREAM_PRE_PROBE_OFFLOOP = flag
    lag = []
    async def canary():
        for _ in range(25):
            t = time.perf_counter(); await asyncio.sleep(0.02); lag.append(time.perf_counter() - t - 0.02)
    c = asyncio.create_task(canary()); await asyncio.sleep(0)
    r = await dn._pre_probe_call(slow, "a", k=6)
    try:
        await dn._pre_probe_call(boom); err = None
    except ValueError as e:
        err = str(e)
    await c
    return r, err, max(lag)
main = threading.get_ident()
r1, e1, lag_on = asyncio.run(go(True)); r0, e0, lag_off = asyncio.run(go(False))
assert r1[:2] == r0[:2] == ("a", 6) and e1 == e0 == "boom", (r1, r0, e1, e0)
assert r1[2] != main and r0[2] == main, "on = worker thread, off = caller thread"
assert lag_on < 0.2 and lag_off > 0.4, (lag_on, lag_off)
print(f"pre-probe offloop max loop lag {lag_on:.3f}s vs inline {lag_off:.3f}s; results + exception identical")

src = Path(dn.__file__).read_text(encoding="utf-8")
for needle in ("_pre_probe_call(self._last_unresolved_arc)", "_pre_probe_call(self._carried_n)",
               "_pre_probe_call(self._met_carry_check, carried, carried_n)", "_pre_probe_call(_memsvc.ask, \"dream\""):
    assert needle in src, needle

n = dn.DreamNode.__new__(dn.DreamNode)
n._stage_timing = {"gather_begin": 10.0, "gather_end": 11.5, "carry_end": 12.0, "ask_end": 13.25, "probe_end": 19.0}
rec = n._stage_timing_record()
assert rec["durations_s"] == {"gather_begin->gather_end": 1.5, "gather_end->carry_end": 0.5,
                              "carry_end->ask_end": 1.25, "ask_end->probe_end": 5.75}, rec
dn.DREAM_STAGE_TIMING = False; n2 = dn.DreamNode.__new__(dn.DreamNode); n2._t_mark("x")
assert not getattr(n2, "_stage_timing", {}), "timing kill switch"
print("OK")
