"""J-1910 / F-2540: telemetry.sample()'s work runs off the 5 s substrate chain (core/telemetry.py kick()) WITHOUT changing
what it writes.

Proves, against the pre-change module (git show <old-rev>:core/telemetry.py, loaded under another name):
  [A] the same simulated run (fake clock, ~5.4 s ticks, calls appended to llm_calls.jsonl between ticks, seeded + oversized
      series files so every _cap trim fires, malformed lines in the call log) leaves hardware_load.jsonl /
      llm_usage.jsonl / llm_calls.jsonl BYTE-IDENTICAL in two modes: OLD sample() on the loop thread vs NEW kick() (worker
      thread, joined each tick); plus NEW sample() (HUD path).  Fired-at times (the ~6 s cadence) are identical too.
      With --data-dir: the same on COPIES of this tree's real llm_calls/hardware_load/llm_usage files.
  [B] mechanics: kick() returns in well under 5 ms while a deliberately slow _gpu_load runs, an asyncio canary timer is
      not delayed; a tick that finds the worker in flight starts no second one and does NOT consume the gate (it fires
      on the next tick after the worker ends); a not-due tick starts no thread; a HUD-thread sample() and the worker
      never overlap inside the body (BODY_LOCK); TELEMETRY_OFFLOOP=False is exactly sample() (rows present on return);
      a body that raises / a thread that will not start never raises out of kick().
  [C] the rows still parse with the HUD's own readers (hud.server._tail_rows / _auto_series) and keep their keys.
Run it from a throwaway worktree, never from C:\\Nascence.  No network, no subprocess (nvidia-smi and psutil are stubbed).
Usage: python scripts/_test_j1910_telemetry_offloop.py [--old-rev 99ecbe0 | --old-file PATH] [--data-dir DIR]"""
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789: no write to the tree's data/
import sys, os, time, json, tempfile, subprocess, importlib.util, threading, asyncio, argparse, types, shutil, pathlib, random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import core                                                         # core BEFORE anything else (live-store safety)
assert os.path.abspath(core.__file__).lower().startswith(ROOT.lower()), core.__file__
assert os.path.normcase(ROOT) != os.path.normcase(r"C:\Nascence"), "run from a throwaway worktree, never the live tree"
from core import telemetry as new
assert os.path.abspath(new.__file__).lower().startswith(ROOT.lower())

ap = argparse.ArgumentParser()
ap.add_argument("--old-rev", default="99ecbe0")
ap.add_argument("--old-file", default=None)
ap.add_argument("--data-dir", default=None, help="a COPY of data/ (inside a throwaway tree): its real llm_calls/hardware_load/llm_usage seed [A]")
args = ap.parse_args()
TMP = tempfile.mkdtemp(prefix="j1910_")

src = (open(args.old_file, encoding="utf-8").read() if args.old_file else
       subprocess.run(["git", "-C", ROOT, "show", f"{args.old_rev}:core/telemetry.py"], capture_output=True, text=True, check=True).stdout)
assert "def kick(" not in src and "def sample(" in src
old_path = os.path.join(TMP, "telemetry_old_j1910.py")
open(old_path, "w", encoding="utf-8").write(src)
spec = importlib.util.spec_from_file_location("telemetry_old_j1910", old_path)
old = importlib.util.module_from_spec(spec); spec.loader.exec_module(old)

FAILS = []
def check(name, ok, extra=""):
    print(("PASS " if ok else "FAIL ") + name + ((" -- " + str(extra)) if extra else ""), flush=True)
    if not ok:
        FAILS.append(name)

# ---- fake clock + stubs, shared by both modules ----
T0 = 1_760_000_000.0
CLOCK = {"t": T0}
fake_time = types.SimpleNamespace(time=lambda: CLOCK["t"], sleep=time.sleep, perf_counter=time.perf_counter, monotonic=time.monotonic)
GPU = {"n": 0}
def gpu_stub():
    GPU["n"] += 1
    return {"GTX 1080 Ti GPU%": float(GPU["n"] % 100), "GTX 1080 Ti VRAM%": round(40.0 + (GPU["n"] % 7) * 1.5, 1)}
PS = {"n": 0}
fake_psutil = types.ModuleType("psutil")
def _cpu(interval=None):
    PS["n"] += 1
    return float((PS["n"] * 7) % 100)
fake_psutil.cpu_percent = _cpu
sys.modules["psutil"] = fake_psutil

def point(mod, d):
    mod._CALLS = pathlib.Path(d) / "llm_calls.jsonl"; mod._HW = pathlib.Path(d) / "hardware_load.jsonl"
    mod._LLM = pathlib.Path(d) / "llm_usage.jsonl"; mod._LAT = pathlib.Path(d) / "llm_latency.jsonl"
    mod._STATIONS = pathlib.Path(d) / "thought_station_log.jsonl"; mod._DATA = pathlib.Path(d)
    mod.time = fake_time; mod._gpu_load = gpu_stub; mod._last_sample = 0.0
    mod._worker = None

def seed(d, real_dir=None):
    os.makedirs(d, exist_ok=True)
    if real_dir:
        for fn in ("llm_calls.jsonl", "hardware_load.jsonl", "llm_usage.jsonl"):
            sp = os.path.join(real_dir, fn)
            if os.path.isfile(sp):
                shutil.copyfile(sp, os.path.join(d, fn))
            else:
                open(os.path.join(d, fn), "w").close()
        return
    models = ["qwen3.5:9b", "phi3:mini", "gemma4:12b", "yi:34b", "command-r7b", "mistral:7b-instruct"]
    with open(os.path.join(d, "llm_calls.jsonl"), "w", encoding="utf-8") as f:
        for i in range(8200):                       # > 6000*1.3 = 7800 -> the _CALLS trim fires
            r = {"ts": round(T0 - 8200 + i, 1), "model": models[i % len(models)], "node": "http://x:11433"}
            if i % 5 == 0:
                r["pc"] = 900 + i; r["nc"] = 4096; r["by"] = "m:%d" % (i % 9)
            if i == 4000:
                f.write("not json at all\n")
            if i == 4001:
                f.write("\n")
            f.write(json.dumps(r) + "\n")
    for fn, mk in (("hardware_load.jsonl", lambda i: {"ts": round(T0 - 800 + i, 1), "CPU %": float(i % 50), "GTX 1080 Ti GPU%": 3.0, "GTX 1080 Ti VRAM%": 55.0}),
                   ("llm_usage.jsonl", lambda i: {"ts": round(T0 - 800 + i, 1), "qwen3.5:9b": i % 4, "phi3:mini": 0, "gemma4:12b": 0, "mistral:7b-instruct": 0})):
        with open(os.path.join(d, fn), "w", encoding="utf-8") as f:           # > 600*1.3 = 780 -> the series trims fire
            for i in range(790):
                f.write(json.dumps(mk(i)) + "\n")

def simulate(mod, d, mode, ticks=90):
    """mode: 'old' (sample() inline), 'kick' (kick() then join the worker), 'sample' (new sample() inline)."""
    point(mod, d)
    CLOCK["t"] = T0
    GPU["n"] = 0; PS["n"] = 0
    fired = []
    rng = random.Random(11)
    for k in range(ticks):
        CLOCK["t"] += 5.0 + rng.random() * 1.2            # the loop's period is ~5.4 s on the real system
        for _ in range(rng.randint(0, 6)):                 # inference calls landing between ticks
            mod.log_llm_call(rng.choice(["qwen3.5:9b", "phi3:mini", "yi:34b", "newmodel:1b"]), "http://x:11433",
                             prompt_chars=rng.randint(100, 4000), num_ctx=4096, caller="m:%d" % rng.randint(0, 9))
        before = mod._last_sample
        if mode in ("old", "sample"):
            mod.sample()
        else:
            mod.kick()
            w = mod._worker
            if w is not None:
                w.join(10)
        if mod._last_sample != before:
            fired.append(round(mod._last_sample, 3))
    return fired

def filehash(d):
    out = {}
    for fn in ("llm_calls.jsonl", "hardware_load.jsonl", "llm_usage.jsonl"):
        p = os.path.join(d, fn)
        out[fn] = open(p, "rb").read() if os.path.isfile(p) else b""
    return out

def keys_of(blob):
    return [list(json.loads(l)) for l in blob.decode().splitlines() if l.strip()][-20:]

# ---------------- [A] ----------------
print("[A] equivalence of what is written")
for label, real in (("synthetic", None), ("real-data-copy", args.data_dir)):
    if label == "real-data-copy" and not real:
        continue
    if real:
        assert "scratchpad" in os.path.abspath(real).lower() or os.path.abspath(real).lower().startswith(ROOT.lower()), "--data-dir must be a COPY under a throwaway tree"
    runs = {}
    for mode, mod in (("old", old), ("kick", new), ("sample", new)):
        d = os.path.join(TMP, "%s_%s" % (label, mode))
        seed(d, real)
        runs[mode] = (simulate(mod, d, mode), filehash(d))
    fo, ho = runs["old"]
    for m in ("kick", "sample"):
        fm, hm = runs[m]
        check("[A/%s] fired-at times identical old vs %s (%d samples)" % (label, m, len(fo)), fo == fm and len(fo) > 20)
        for fn in ho:
            check("[A/%s] %s byte-identical old vs %s (%d bytes)" % (label, fn, m, len(ho[fn])), ho[fn] == hm[fn] and len(ho[fn]) > 0)
    check("[A/%s] hardware row keys unchanged" % label, keys_of(runs["kick"][1]["hardware_load.jsonl"]) == keys_of(ho["hardware_load.jsonl"]))
    check("[A/%s] llm_usage row keys unchanged" % label, keys_of(runs["kick"][1]["llm_usage.jsonl"]) == keys_of(ho["llm_usage.jsonl"]))
    n_hw = runs["kick"][1]["hardware_load.jsonl"].count(b"\n")
    check("[A/%s] hardware cap held (<= 600*1.3 rows)" % label, n_hw <= 780, n_hw)

# ---------------- [B] ----------------
print("[B] mechanics")
d = os.path.join(TMP, "mech"); seed(d); point(new, d)
for _fn in ("hardware_load.jsonl", "llm_usage.jsonl"):      # few rows: no trim here, so row counts below count fires
    open(os.path.join(d, _fn), "w").write("".join(json.dumps({"ts": 1.0 + i}) + chr(10) for i in range(5)))
CLOCK["t"] = T0 + 100_000.0
SLOW = {"s": 0.0, "running": 0, "max_running": 0, "entered": threading.Event()}
def slow_gpu():
    SLOW["running"] += 1; SLOW["max_running"] = max(SLOW["max_running"], SLOW["running"])
    SLOW["entered"].set()
    time.sleep(SLOW["s"])
    SLOW["running"] -= 1
    return {"GTX 1080 Ti GPU%": 1.0}
new._gpu_load = slow_gpu
def nrows():
    return open(new._HW, "rb").read().count(b"\n")

SLOW["s"] = 0.6
async def amain():
    lags = []
    stop = asyncio.Event()
    async def canary():
        while not stop.is_set():
            t = time.perf_counter(); await asyncio.sleep(0.02); lags.append((time.perf_counter() - t - 0.02) * 1000)
    c = asyncio.create_task(canary())
    await asyncio.sleep(0.2)
    n0 = nrows(); w0 = len(lags)
    CLOCK["t"] += 10.0
    SLOW["entered"].clear()
    t = time.perf_counter(); new.kick(); dt = (time.perf_counter() - t) * 1000
    check("[B] kick() returns in < 5 ms while the body is slow (600 ms _gpu_load)", dt < 5.0, "%.2f ms" % dt)
    th1 = new._worker
    check("[B] a worker thread is running", th1 is not None and th1.is_alive())
    SLOW["entered"].wait(2)
    CLOCK["t"] += 7.0                                   # in flight, and the clock is past the gap again
    last_before = new._last_sample
    new.kick()
    check("[B] in-flight worker: the next due tick starts no second worker", new._worker is th1 and SLOW["max_running"] == 1)
    check("[B] in-flight worker: the gate is not consumed", new._last_sample == last_before)
    await asyncio.sleep(0.9)
    lag_max = max(lags[w0:]) if lags[w0:] else 0
    check("[B] loop canary (20 ms timer) not held by the 600 ms body (max lag < 60 ms)", lag_max < 60, "max lag %.1f ms" % lag_max)
    check("[B] worker finished, exactly one row written for the first fire", (not th1.is_alive()) and nrows() == n0 + 1, (n0, nrows()))
    new.kick()                                          # gate held open (claimed at +10, now +17): fires now
    th2 = new._worker
    check("[B] after the worker ends, the held-open gate fires on the next tick", th2 is not th1 and th2 is not None)
    th2.join(5)
    check("[B] second fire wrote one more row", nrows() == n0 + 2, nrows())
    n1 = nrows()
    CLOCK["t"] += 2.0; new.kick()
    check("[B] not-due tick (2 s after the last claim) starts no thread and writes nothing", new._worker is th2 and nrows() == n1)
    stop.set(); await c
asyncio.run(amain())

# HUD-thread sample() vs worker: bodies never overlap
SLOW["s"] = 0.25; SLOW["running"] = 0; SLOW["max_running"] = 0
CLOCK["t"] += 20.0
new.kick(); time.sleep(0.05)
CLOCK["t"] += 20.0
th = threading.Thread(target=lambda: new.sample(force=True)); th.start()
th.join(5); new._worker.join(5)
check("[B] HUD sample(force) and the worker never ran the body at the same time", SLOW["max_running"] == 1, SLOW["max_running"])

# kill switch
new._gpu_load = gpu_stub
new.TELEMETRY_OFFLOOP = False
CLOCK["t"] += 20.0
n2 = nrows(); wk = new._worker
new.kick()
check("[B] TELEMETRY_OFFLOOP=False: kick() == sample(), row present on return, no new thread", nrows() == n2 + 1 and new._worker is wk)
new.TELEMETRY_OFFLOOP = True

# fail-open
orig_body = new._sample_body
def boom(now):
    raise RuntimeError("boom")
new._sample_body = boom
CLOCK["t"] += 20.0
ok = True
try:
    new.kick(); new._worker.join(5)
except Exception:
    ok = False
check("[B] a body that raises does not raise out of kick() / the worker", ok)
new._sample_body = orig_body
CLOCK["t"] += 20.0; n3 = nrows(); new.kick(); new._worker.join(5)
check("[B] and the next kick still works", nrows() == n3 + 1)
orig_thread = threading.Thread
class NoStart(orig_thread):
    def start(self):
        raise RuntimeError("can't start new thread")
threading.Thread = NoStart
CLOCK["t"] += 20.0
ok = True
try:
    new.kick()
except Exception:
    ok = False
threading.Thread = orig_thread
check("[B] a thread that will not start does not raise out of kick()", ok)

# ---------------- [C] ----------------
print("[C] HUD readers still parse the rows")
try:
    from hud import server as hs
    d = os.path.join(TMP, "hud_check"); seed(d); point(new, d); new._gpu_load = gpu_stub
    CLOCK["t"] = T0 + 200_000.0
    for _ in range(12):
        CLOCK["t"] += 6.5; new.kick(); new._worker.join(5)
    for fn in ("hardware_load.jsonl", "llm_usage.jsonl"):
        rows = hs._tail_rows(pathlib.Path(d) / fn, limit=140)
        series = hs._auto_series(rows, nested=None, whitelist=None)
        check("[C] hud.server reads %s" % fn, len(rows) >= 12 and bool(series), "%d rows, series %s" % (len(rows), str(list(series))[:80]))
except Exception as e:
    check("[C] hud.server import/read", False, repr(e)[:200])

shutil.rmtree(TMP, ignore_errors=True)
print("\nRESULT:", "ALL PASS" if not FAILS else "%d FAIL: %s" % (len(FAILS), FAILS))
sys.exit(1 if FAILS else 0)
