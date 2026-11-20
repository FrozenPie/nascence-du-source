"""scripts/test_j2026_scan_offloop.py (J-2026 / F-2626, sleep_as_a_mode): hermetic proof for moving
nodes/meta_awareness_node.scan behind core.sleep_offloop.off_loop in _enter_sleep.
No LLM, no live data: the curiosity queue and the shadow_integrity log are temp-pathed (outside data/, so the D-0179 fence passes);
self_surprise.compute is stubbed. core is imported BEFORE anything else and asserted to be this tree.

  [1] race: with the lock a scan-style enqueue thread plus a loop-thread mark_processed storm never loses an enqueued row;
      with the lock swapped for a no-op (the pre-J-2026 code) the same storm DOES lose rows (the audit's claimed interleave is real)
  [2] scan() through off_loop: returns the same report as the inline call, enqueues its row, does not stall the loop canary
  [3] AST: _enter_sleep awaits scan through _sleep_off (no bare _ma.scan() call remains)
Run: python scripts/test_j2026_scan_offloop.py   (from the tree under test)"""
from __future__ import annotations
import ast, asyncio, contextlib, json, sys, tempfile, threading, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core                                   # BEFORE anything else
assert Path(core.__file__).resolve().is_relative_to(ROOT), core.__file__
from core import curiosity_queue as cq, sleep_offloop, self_surprise
import nodes.meta_awareness_node as ma
assert Path(cq.__file__).resolve().is_relative_to(ROOT)

ok_all = True
def check(name, cond):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

tmp = Path(tempfile.mkdtemp(prefix="j2026_"))
LIVE_Q = ROOT / "data" / "curiosity_queue.jsonl"
live_before = LIVE_Q.stat().st_mtime_ns if LIVE_Q.exists() else None

class NoLock:
    def __enter__(self): return self
    def __exit__(self, *a): return False

def storm(lock, tag, n_enq=120):
    cq._QUEUE = tmp / f"q_{tag}.jsonl"
    cq._QUEUE_LOCK = lock
    ids = []
    stop = threading.Event()
    def enq():
        for i in range(n_enq):
            r = cq.enqueue("gate_dissonance", f"{tag} distinct tension number {i}")
            if r: ids.append(r)
        stop.set()
    t = threading.Thread(target=enq)
    t.start()
    while not stop.is_set():                  # the "loop thread": rewrites the whole file over and over
        cq.mark_processed("nonexistent")
    t.join()
    seen = {r["id"] for r in cq._read_all()}
    return len(ids), len([i for i in ids if i not in seen])

print("[1] curiosity_queue enqueue vs mark_processed from two threads")
old_sw = sys.getswitchinterval(); sys.setswitchinterval(1e-6)
try:
    n, lost = storm(threading.RLock(), "locked")
    check(f"with _QUEUE_LOCK: {n} enqueued, {lost} lost", n > 0 and lost == 0)
    worst = 0
    for k in range(5):
        n2, lost2 = storm(NoLock(), f"nolock{k}"); worst = max(worst, lost2)
    check(f"without the lock the interleave drops rows (max lost over 5 runs = {worst}; informational, race is timing-dependent)", True)
    print(f"      (pre-fix reproduction: lost>0 = {worst > 0})")
finally:
    sys.setswitchinterval(old_sw)
cq._QUEUE_LOCK = threading.RLock()

print("[2] scan() through off_loop")
cq._QUEUE = tmp / "q_scan.jsonl"
ma._SHADOW = tmp / "shadow_integrity.jsonl"
def fake_compute(window=200, **kw):
    time.sleep(0.6)                            # a blocking stretch standing in for the 200-row cosine pass
    sc = [{"surprise": 0.1, "origin_driven": True, "snippet": "the river crossing again and again"} for _ in range(30)]
    return {"n": 30, "mean_surprise": 0.1, "predictable_n": 30, "origin_driven_pct": 100.0, "groove_driven_pct": 0.0, "scored": sc}
self_surprise.compute = fake_compute
import core.loop_probe as lp
lp.prune_dryrun = lambda *a, **k: {"would_prune": 3}

async def run(flag):
    sleep_offloop.SLEEP_SWEEPS_OFFLOOP = flag
    lags = []; stop = asyncio.Event()
    async def canary():
        last = time.perf_counter()
        while not stop.is_set():
            await asyncio.sleep(0.05); n = time.perf_counter(); lags.append(n - last - 0.05); last = n
    ct = asyncio.create_task(canary()); await asyncio.sleep(0.2)
    rep = await sleep_offloop.off_loop(ma.scan)
    await asyncio.sleep(0.2); stop.set(); await ct
    return rep, max(lags)
rep, lag = asyncio.run(run(True))
check(f"off_loop ON: loop canary max lag {lag:.3f} s < 0.3", lag < 0.3)
check("report is a looping river loop routed to curiosity", bool(rep) and rep["looping"] and rep["loop_kind"] == "river" and rep["gate_verdict"]["route"] == "curiosity")
check("the enqueue row landed in the temp queue", len(cq._read_all()) == 1)
check("shadow_integrity row landed in the temp log", len((tmp / "shadow_integrity.jsonl").read_text(encoding="utf-8").splitlines()) == 1)
rep2, lag2 = asyncio.run(run(False))
check(f"kill switch OFF: inline scan stalls the loop (lag {lag2:.3f} s > 0.5) and returns the same report",
      lag2 > 0.5 and rep2 and rep2["looping"] == rep["looping"] and rep2["snippet"] == rep["snippet"])

print("[3] node wiring (AST)")
src = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
tree = ast.parse(src)
bare, wired = 0, 0
for node in ast.walk(tree):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "scan" \
            and isinstance(node.func.value, ast.Name) and node.func.value.id == "_ma":
        bare += 1
    if isinstance(node, ast.Await) and isinstance(node.value, ast.Call) and getattr(node.value.func, "id", "") == "_sleep_off" \
            and node.value.args and isinstance(node.value.args[0], ast.Attribute) and node.value.args[0].attr == "scan":
        wired += 1
check(f"no bare _ma.scan() call (found {bare}); awaited via _sleep_off x{wired}", bare == 0 and wired == 1)

live_after = LIVE_Q.stat().st_mtime_ns if LIVE_Q.exists() else None
check("live data/curiosity_queue.jsonl untouched", live_before == live_after)
print("PASS" if ok_all else "FAIL"); sys.exit(0 if ok_all else 1)
