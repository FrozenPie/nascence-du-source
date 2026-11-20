"""scripts/lag_harness/busy_standin_J1927.py (J-1927, F-2552): a stand-in for ONE generating llama.cpp CPU hub.

No model, no network, no Nascence import. T python threads each own a private MB-sized float32 matrix and run
sgemv over it in a tight loop (`membw`: streams the matrix through the memory system every call, the shape of a
q4 decode step where the weights are read once per token) or a cache-resident 512x512 sgemm (`compute`: pure
ALU/SIMD). numpy releases the GIL inside dot(), and OPENBLAS/OMP are pinned to 1 thread, so every python thread is
exactly one 100 %-busy core -- the way a llama.cpp threadpool looks to the scheduler (its threads spin even at
barriers). Two real hubs = two of these processes (14 + 20 threads, the :11439 / :11442 settings in
scripts/supervisor.py).

Usage: python busy_standin_J1927.py --threads 20 [--mode membw|compute] [--mb 256] [--secs 900] [--stopfile PATH]
Exits when the stop file appears or --secs elapse, whichever comes first."""
import os, sys, time, argparse, threading, pathlib

ap = argparse.ArgumentParser()
ap.add_argument("--threads", type=int, required=True)
ap.add_argument("--mode", choices=["membw", "compute"], default="membw")
ap.add_argument("--mb", type=int, default=256, help="private matrix size per thread, MB (membw mode)")
ap.add_argument("--secs", type=float, default=900.0)
ap.add_argument("--stopfile", default=None)
A = ap.parse_args()
for k in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[k] = "1"
import numpy as np

stop = threading.Event()
counts = [0] * A.threads


def worker(i):
    rng = np.random.default_rng(1927 + i)
    if A.mode == "membw":
        rows = A.mb * 1024 * 1024 // (1024 * 4)
        M = rng.random((rows, 1024), dtype=np.float32)
        v = np.ones(1024, dtype=np.float32)
        while not stop.is_set():
            M.dot(v); counts[i] += 1
    else:
        M = rng.random((512, 512), dtype=np.float32)
        while not stop.is_set():
            M.dot(M); counts[i] += 1


ths = [threading.Thread(target=worker, args=(i,), daemon=True) for i in range(A.threads)]
t0 = time.time()
for t in ths: t.start()
print(f"busy_standin pid={os.getpid()} threads={A.threads} mode={A.mode} mb={A.mb}", flush=True)
try:
    while time.time() - t0 < A.secs:
        if A.stopfile and pathlib.Path(A.stopfile).exists():
            break
        time.sleep(0.5)
finally:
    stop.set()
    for t in ths: t.join(timeout=5)
    el = time.time() - t0
    print(f"busy_standin pid={os.getpid()} done after {el:.1f}s, {sum(counts)} dots ({sum(counts)/el:.0f}/s)", flush=True)
