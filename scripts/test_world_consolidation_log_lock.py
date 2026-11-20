"""scripts/test_world_consolidation_log_lock.py (J-1931 / F-2557, 2026-10-08): world_consolidation._log must append under _FILE_LOCK.

sweep() (worker thread via core.sleep_offloop.off_loop) ends with _log(); file_book_notes() (loop thread, essay_lesson) logs under
_FILE_LOCK. Unlocked, the sweep's append can interleave with it (Windows threaded appends lose/garble lines, J-1918 control).
Isolated: _LOG is redirected to a temp dir; nothing under live data/ is touched; no model, no network.
Gate: STRUCTURAL (every write-mode open of the log records whether the calling thread holds _FILE_LOCK; with the real lock 0
violations, with a no-op lock violations > 0) + OBSERVED (line count / parse). Also checks the nested call from inside a
held lock (file_book_notes -> _log) does not deadlock (RLock). Exit 0 only if all hold."""
import builtins, json, os, sys, tempfile, threading, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import core                                     # noqa: F401  (import core BEFORE anything lab-ish)
from core import world_consolidation as wc

T, M = 8, 300


class NoLock:
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def held_by_me(self): return False


class OwnerRLock:
    def __init__(self): self._l = threading.RLock(); self._o = None; self._d = 0
    def __enter__(self):
        self._l.acquire(); self._o = threading.get_ident(); self._d += 1; return self
    def __exit__(self, *a):
        self._d -= 1
        if self._d == 0: self._o = None
        self._l.release(); return False
    def held_by_me(self): return self._o == threading.get_ident()


def run(with_lock):
    d = pathlib.Path(tempfile.mkdtemp(prefix="J-1931_")); log = d / "wc_log.jsonl"
    saved = (wc._LOG, wc._FILE_LOCK); wc._LOG = log
    lk = OwnerRLock() if with_lock else NoLock(); wc._FILE_LOCK = lk
    st = {"t": 0, "v": 0}; mu = threading.Lock(); real = builtins.open; root = os.path.normcase(str(d))

    def spy(f, mode="r", *a, **k):
        if isinstance(mode, str) and "a" in mode and not isinstance(f, int) and os.path.normcase(os.path.abspath(os.fspath(f))).startswith(root):
            with mu:
                st["t"] += 1; st["v"] += (not lk.held_by_me())
        return real(f, mode, *a, **k)
    builtins.open = spy
    try:
        bar = threading.Barrier(T)

        def work(tid):
            bar.wait()
            for i in range(M):
                if tid % 2:   # loop-thread-like: file_book_notes logs while holding the lock (nested acquire)
                    with wc._FILE_LOCK: wc._log({"t": tid, "i": i, "pad": "x" * 200})
                else:         # sweep-like: final bare _log
                    wc._log({"t": tid, "i": i, "sweep": True, "pad": "y" * 200})
        ths = [threading.Thread(target=work, args=(t,)) for t in range(T)]
        [t.start() for t in ths]; [t.join(timeout=60) for t in ths]
        hung = any(t.is_alive() for t in ths)
    finally:
        builtins.open = real; wc._LOG, wc._FILE_LOCK = saved
    n = bad = 0
    for line in log.read_bytes().split(b"\n"):
        if line.strip():
            n += 1
            try: json.loads(line)
            except Exception: bad += 1
    return {"with_lock": with_lock, "touches": st["t"], "violations": st["v"], "lines": n, "expected": T * M, "bad": bad, "hung": hung}


a = run(True); b = run(False)
print(a); print(b)
ok = a["violations"] == 0 and a["lines"] == a["expected"] and a["bad"] == 0 and not a["hung"] and b["violations"] > 0
print("PASS" if ok else "FAIL"); sys.exit(0 if ok else 1)
