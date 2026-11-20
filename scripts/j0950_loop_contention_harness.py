"""
J-0950 / Thread 2(a): ISOLATED event-loop contention harness -- does a HEAVY climate tick (~900 ms, the 60 MB
subconscious_state.json parse of core/climate_engine.py before D-0154 Part A) versus a LIGHT tick (~30 ms, the light sidecar)
change how fast other work on the SAME asyncio event loop starts and finishes?  This is Lead A's shared-event-loop hypothesis
(F-1017, F-1305, F-1319), tested directly instead of inferred from code structure.

CONTEXT (why the measured phase is a small, bounded question now): the log read of the same job (F-1684, F-1685) puts the 09-09..09-11
step at the D-0148 option A boot of 09-08 16:41, not at Lead A; F-1686 shows the climate loop is suspended for every internal cycle, so
the tick can only touch (a) the ~1.3 s wait before a threshold crossing is noticed and (b) coroutines that overlap ticks (human-triggered
cycles, monologue, stream); and F-1690 shows the big loss of loop time is the 10-30 min sleep-entry freeze, not the tick.  This harness
measures (a) and (b) directly so they can be quoted as numbers instead of inferred from code structure.

WHAT IT MODELS (faithfully, from core/climate_engine.py ClimateEngine.start_background and core/orchestrator.py):
  * a climate loop coroutine:  `await asyncio.sleep(TICK_SECS); tick()` where tick() is SYNCHRONOUS and holds the GIL
    (busy-wait for HEAVY_MS or LIGHT_MS, or a real json.loads of a synthetic blob), then the ignition check, then -- exactly as
    in the real code (`await self._ignite(trigger)` -> `await self._ignition_callback(...)` -> `await self.run_cycle(...)`) --
    the INTERNAL cycle is awaited INSIDE this same coroutine, so NO tick runs while an internal cycle is in flight.  (Verified
    on the real log, F-1686: 0 of 156 expected climate publish rows fall inside 63 internal-cycle windows.)
  * a "human-like" cycle: the same call chain launched as an independent task, so it IS concurrent with ticks (this is the path
    a tick can actually slow, and it is not what "autonomous cycle throughput" means, but it is what a founder chat would feel).
  * a heartbeat (20 ms sleeps) = the standard event-loop-lag monitor, plus a few chatter tasks (monologue/stream stand-ins).
  * the cycle's "LLM calls" are either asyncio.sleep(delay) (--wait-kind sleep) or real non-streaming aiohttp GETs to a local
    server SUBPROCESS that answers after `delay` (--wait-kind http; one aiohttp.ClientSession per call, like core/model_client.py),
    so wake-ups come from real Windows IOCP completions on the same ProactorEventLoop the orchestrator runs on.

WHAT IT MEASURES per block (one block = one tick kind, --block-s seconds, one fresh event loop):
  M1 ign_latency_s   seconds from a seeded threshold-crossing time to the first line of the internal cycle (the climate loop
                     only notices a crossing at its next tick, AFTER the tick's own cost: HEAVY predicts about +1.3 s vs LIGHT)
  M2 internal_over_s internal cycle wall time minus its ideal sum of call delays (predicted equal for HEAVY and LIGHT: no tick
                     runs during it -- a POSITIVE CONTROL of the code-reading argument; a difference would falsify it)
  M3 human_over_s / human_start_late_s   same for cycles launched as independent tasks (predicted HEAVY > LIGHT)
  M4 hb_late_ms      heartbeat lateness distribution (mean/p50/p90/p99/max)
  M5 tick_ms         the achieved tick durations (self-check that HEAVY really blocked ~HEAVY_MS)
  plus per-block system CPU percent (GetSystemTimes, 1 Hz samples), harness-process CPU seconds, logical CPUs, and a
  process snapshot (python/ollama/llama/node counts) at run start and end, because concurrent CPU load from other jobs
  corrupts timings (paired blocks under equal load are still comparable; contended blocks are flagged).

ISOLATION: pure stdlib + aiohttp + psutil; NO core/ imports; writes ONLY the --out JSONL (default: system temp dir).  A
sys.addaudithook counts every open-for-write / rename / replace under C:\\Nascence\\data or C:\\Nascence\\docs (except an explicit
--out) and prints `write attempts under live data: N` (must be 0).  It never touches Du, the hubs or the network beyond 127.0.0.1.

USAGE
  smoke (<= ~1 min, NOT the measured phase):
      python scripts/j0950_loop_contention_harness.py smoke
  calibrate the real json.loads cost of a synthetic blob on THIS machine (optional, ~1 min for 60 MB):
      python scripts/j0950_loop_contention_harness.py calibrate --heavy-mb 60 --light-mb 2
  the measured phase (interleaved ABBA, paired seeds; run ONLY on a quiet machine): 6 pairs = 12 blocks of 150 s, about 32-35 minutes
  in all (12 x ~155 s plus a 10 s quiet-machine gate).  It refuses to start when system CPU over 10 s exceeds --max-cpu (60%)
  unless --force.  It is RESUMABLE (--resume skips (pair, kind) blocks already in --out), so a stopped run costs at most one block.
  Start it detached (over ~30 min, so through WMI: scripts/j0950_start_harness_detached.ps1) and poll the --out file / the log:
      python scripts/j0950_loop_contention_harness.py measure --out <SCRATCH>\\j0950_harness_results.jsonl --wait-kind http \\
          --pairs 6 --block-s 150 --seed 950 --resume
  What is logged about concurrent CPU load (per block, in the results row): system_cpu_pct (GetSystemTimes over the block),
  system_cpu_pct_max_1s and cpu_samples_p50 (1 Hz samples), proc_cpu_s (this process), and in the header/footer a process snapshot
  (logical CPUs, python/ollama/llama/node/claude process counts, psutil cpu_percent over 1 s).  `analyse` reports every metric for ALL
  pairs and for QUIET pairs only (both blocks <= --max-cpu), plus a per-block CPU summary; read the QUIET table as the result and the
  ALL table as its robustness check.  The analytic expectations are printed under the tables for comparison.
  analyse a results file (also runs at the end of `measure`):
      python scripts/j0950_loop_contention_harness.py analyse --out <results.jsonl>
"""
from __future__ import annotations

import argparse
import asyncio
import ctypes
import json
import math
import os
import platform
import random
import socket
import statistics
import subprocess
import sys
import tempfile
import time
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")

# ------------------------------------------------------------------------------------------------------------------
# live-data write audit (rule 5): must print 0
# ------------------------------------------------------------------------------------------------------------------
_LIVE_PREFIXES = (r"c:\nascence\data", r"c:\nascence\docs")
_AUDIT = {"n": 0, "paths": [], "exempt": None}


def _audit_hook(event, args):
    try:
        if event == "open":
            path, mode = args[0], args[1]
            if not isinstance(path, (str, bytes, os.PathLike)):
                return
            writing = isinstance(mode, str) and any(c in mode for c in "wax+")
            flags = args[2] if len(args) > 2 and isinstance(args[2], int) else 0
            if not writing and flags & (os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC):
                writing = True
            if not writing:
                return
            p = os.path.abspath(os.fsdecode(path)).lower()
        elif event in ("os.rename", "os.replace", "shutil.move", "shutil.copyfile", "os.remove", "os.unlink", "os.mkdir", "os.rmdir"):
            cand = [a for a in args if isinstance(a, (str, bytes, os.PathLike))]
            if not cand:
                return
            p = " ".join(os.path.abspath(os.fsdecode(c)).lower() for c in cand)
        else:
            return
        if any(pref in p for pref in _LIVE_PREFIXES) and not (_AUDIT["exempt"] and _AUDIT["exempt"] in p):
            _AUDIT["n"] += 1
            _AUDIT["paths"].append(p[:200])
    except Exception:
        pass


sys.addaudithook(_audit_hook)

# ------------------------------------------------------------------------------------------------------------------
# system CPU load (Windows GetSystemTimes; psutil fallback)
# ------------------------------------------------------------------------------------------------------------------
class _FT(ctypes.Structure):
    _fields_ = [("lo", ctypes.c_uint32), ("hi", ctypes.c_uint32)]


def _ft(x) -> int:
    return (x.hi << 32) | x.lo


def system_times():
    try:
        i, k, u = _FT(), _FT(), _FT()
        ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(i), ctypes.byref(k), ctypes.byref(u))
        return _ft(i), _ft(k), _ft(u)
    except Exception:
        return None


def cpu_pct(a, b):
    if not a or not b:
        return None
    di, dk, du = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    tot = dk + du
    return 100.0 * (tot - di) / tot if tot > 0 else None


def process_snapshot():
    try:
        import psutil
        names = {}
        for p in psutil.process_iter(["name"]):
            n = (p.info["name"] or "").lower()
            names[n] = names.get(n, 0) + 1
        keep = {k: v for k, v in names.items() if any(s in k for s in ("python", "ollama", "llama", "node", "claude", "pythonw"))}
        return {"logical_cpus": os.cpu_count(), "interesting_processes": keep, "cpu_percent_1s": psutil.cpu_percent(interval=1.0)}
    except Exception as exc:
        return {"logical_cpus": os.cpu_count(), "error": str(exc)}


# ------------------------------------------------------------------------------------------------------------------
# tick implementations (SYNCHRONOUS, GIL-holding, like the real json.load)
# ------------------------------------------------------------------------------------------------------------------
def busy_wait_ms(ms: float) -> None:
    end = time.perf_counter() + ms / 1000.0
    x = 0
    while time.perf_counter() < end:
        x += 1


def make_blob(mb: float) -> str:
    """Synthetic subconscious-state-like JSON (tensions with label, counts, member id lists, float vectors) of ~mb megabytes."""
    rng = random.Random(1234)
    parts, size = [], 0
    target = int(mb * 1e6)
    i = 0
    while size < target:
        rec = {"id": "%08x" % rng.getrandbits(32), "label": "tension label %d %s" % (i, "x" * rng.randint(5, 40)), "count": rng.randint(1, 200),
               "first_ts": 1.78e9 + i, "last_ts": 1.78e9 + rng.random() * 1e6, "charge": rng.random(), "member_event_ids": [rng.randint(1, 10**6) for _ in range(rng.randint(2, 40))],
               "centroid": [round(rng.random(), 6) for _ in range(64)]}
        s = json.dumps(rec)
        parts.append(s)
        size += len(s) + 2
        i += 1
    return '{"tensions": [' + ", ".join(parts) + '], "integration_patterns": []}'


class Tick:
    def __init__(self, kind: str, tick_kind: str, heavy_ms: float, light_ms: float, blobs: dict | None):
        self.kind, self.tick_kind, self.heavy_ms, self.light_ms, self.blobs = kind, tick_kind, heavy_ms, light_ms, blobs

    def __call__(self) -> None:
        if self.tick_kind == "json":
            json.loads(self.blobs[self.kind])
        else:
            busy_wait_ms(self.heavy_ms if self.kind == "heavy" else self.light_ms)


# ------------------------------------------------------------------------------------------------------------------
# synthetic workload
# ------------------------------------------------------------------------------------------------------------------
def draw_delays(rng: random.Random, n_calls: int, median_s: float, sigma: float) -> list[float]:
    return [max(0.02, rng.lognormvariate(math.log(median_s), sigma)) for _ in range(n_calls)]


async def wait_call(kind: str, delay_s: float, url: str | None) -> None:
    if kind == "sleep":
        await asyncio.sleep(delay_s)
        return
    import aiohttp
    async with aiohttp.ClientSession() as session:            # one session per call, like core/model_client.py
        async with session.get(url, params={"ms": f"{delay_s * 1000.0:.1f}"}, timeout=aiohttp.ClientTimeout(total=60)) as resp:
            await resp.read()


async def run_chain(cfg, delays: list[float], url: str | None) -> float:
    """One synthetic cycle: sequential 'LLM calls'.  Returns wall seconds minus the ideal sum of delays."""
    t0 = time.perf_counter()
    for d in delays:
        await wait_call(cfg.wait_kind, d, url)
    return (time.perf_counter() - t0) - sum(delays)


class Schedule:
    """Seeded threshold-crossing times (relative to block start) for internal ignitions."""
    def __init__(self, seed: int, block_s: float, mean_gap_s: float, min_gap_s: float):
        rng = random.Random(seed * 7919 + 1)
        t, self.times = min(10.0, block_s * 0.15), []
        while t < block_s - min_gap_s:
            self.times.append(t)
            t += max(min_gap_s, rng.expovariate(1.0 / mean_gap_s))
        self.i = 0

    def pending(self, now: float) -> bool:
        return self.i < len(self.times) and now >= self.times[self.i]

    def pop(self) -> float:
        t = self.times[self.i]
        self.i += 1
        return t


async def climate_loop(cfg, tick: Tick, sched: Schedule, seed: int, stats: dict, stop: asyncio.Event, url: str | None):
    rng = random.Random(seed * 104729 + 3)
    k = 0
    while not stop.is_set():
        await asyncio.sleep(cfg.tick_secs)
        ts = time.perf_counter()
        tick()                                                         # SYNCHRONOUS, blocks the loop
        stats["tick_ms"].append((time.perf_counter() - ts) * 1000.0)
        now = time.perf_counter() - stats["t0"]
        # 2026-10-03 (J-0950 takeover) detection-rule fix: the REAL engine's tick() takes `now = time.time()` and dt = now - _last_tick
        # BEFORE _compute_field(), so the accumulator is integrated up to the tick's START and a crossing is registered by the first tick
        # whose START is at or after it (_pending_trigger() then runs after the tick's own cost B).  The original rule compared the
        # crossing to the tick's END (`now`), which registers a crossing that fell inside the tick's own run one tick early and so
        # under-measures the heavy-vs-light start-latency difference by about B (measured mean = P/2 instead of the real P/2 + B,
        # i.e. 0.43 s instead of the 1.3 s the analytic bound in F-1686 and this file's own `analyse` expectation print).
        if sched.pending(ts - stats["t0"]):                             # ClimateEngine: tick() then _pending_trigger()
            tc = sched.pop()
            stats["ign_latency_s"].append(now - tc)
            delays = draw_delays(rng, cfg.n_calls, cfg.call_median_s, cfg.call_sigma)
            over = await run_chain(cfg, delays, url)                    # AWAITED INSIDE the climate loop => no ticks meanwhile
            stats["internal_over_s"].append(over)
            k += 1


async def human_launcher(cfg, seed: int, stats: dict, stop: asyncio.Event, url: str | None):
    rng = random.Random(seed * 1299709 + 5)
    loop = asyncio.get_running_loop()
    tasks = []
    t = 5.0 + rng.random() * cfg.human_every_s
    while t < cfg.block_s - (cfg.n_calls * cfg.call_median_s * 3.0 + 3.0) and not stop.is_set():
        due = stats["t0"] + t
        delays = draw_delays(rng, cfg.n_calls, cfg.call_median_s, cfg.call_sigma)

        async def one(due=due, delays=delays):
            wait = due - time.perf_counter()
            if wait > 0:
                await asyncio.sleep(wait)
            stats["human_start_late_s"].append(max(0.0, time.perf_counter() - due))
            stats["human_over_s"].append(await run_chain(cfg, delays, url))

        tasks.append(asyncio.create_task(one()))
        t += rng.uniform(0.6, 1.4) * cfg.human_every_s
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


async def heartbeat(cfg, stats: dict, stop: asyncio.Event):
    period = cfg.hb_ms / 1000.0
    last = time.perf_counter()
    while not stop.is_set():
        await asyncio.sleep(period)
        now = time.perf_counter()
        stats["hb_late_ms"].append((now - last - period) * 1000.0)
        last = now


async def chatter(cfg, seed: int, stats: dict, stop: asyncio.Event):
    rng = random.Random(seed * 31337 + 7)
    while not stop.is_set():
        await asyncio.sleep(rng.uniform(0.05, 0.5))
        busy_wait_ms(0.2)


async def cpu_sampler(stats: dict, stop: asyncio.Event):
    prev = system_times()
    while not stop.is_set():
        await asyncio.sleep(1.0)
        cur = system_times()
        v = cpu_pct(prev, cur)
        if v is not None:
            stats["cpu_samples"].append(round(v, 1))
        prev = cur


def quant(a, p):
    if not a:
        return None
    s = sorted(a)
    k = (len(s) - 1) * p / 100.0
    lo, hi = int(math.floor(k)), int(math.ceil(k))
    return s[lo] if lo == hi else s[lo] + (s[hi] - s[lo]) * (k - lo)


def summ(a):
    if not a:
        return {"n": 0}
    return {"n": len(a), "mean": statistics.fmean(a), "p50": quant(a, 50), "p90": quant(a, 90), "p99": quant(a, 99), "max": max(a)}


def run_block(cfg, kind: str, seed: int, tick_obj: Tick, url: str | None, pair: int, slot: int) -> dict:
    stats = defaultdict(list)

    async def main():
        stop = asyncio.Event()
        stats["t0"] = time.perf_counter()
        sched = Schedule(seed, cfg.block_s, cfg.ignite_every_s, cfg.n_calls * cfg.call_median_s * 2.0 + 3 * cfg.tick_secs)
        tasks = [asyncio.create_task(climate_loop(cfg, tick_obj, sched, seed, stats, stop, url)),
                 asyncio.create_task(human_launcher(cfg, seed, stats, stop, url)),
                 asyncio.create_task(heartbeat(cfg, stats, stop)),
                 asyncio.create_task(cpu_sampler(stats, stop))]
        tasks += [asyncio.create_task(chatter(cfg, seed + i, stats, stop)) for i in range(cfg.chatter)]
        await asyncio.sleep(cfg.block_s)
        stop.set()
        await asyncio.wait(tasks, timeout=cfg.grace_s)
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    a, pt0 = system_times(), time.process_time()
    w0 = time.perf_counter()
    asyncio.run(main())
    wall = time.perf_counter() - w0
    b, pt1 = system_times(), time.process_time()
    cs = list(stats["cpu_samples"])
    return {"kind": kind, "pair": pair, "slot": slot, "seed": seed, "wall_s": wall, "system_cpu_pct": cpu_pct(a, b),
            "system_cpu_pct_max_1s": max(cs) if cs else None, "cpu_samples_p50": quant(cs, 50), "proc_cpu_s": pt1 - pt0,
            "tick_ms": summ(stats["tick_ms"]), "ign_latency_s": summ(stats["ign_latency_s"]), "ign_latency_raw": [round(x, 4) for x in stats["ign_latency_s"]],
            "internal_over_s": summ(stats["internal_over_s"]), "internal_over_raw": [round(x, 4) for x in stats["internal_over_s"]],
            "human_over_s": summ(stats["human_over_s"]), "human_over_raw": [round(x, 4) for x in stats["human_over_s"]],
            "human_start_late_s": summ(stats["human_start_late_s"]), "hb_late_ms": summ(stats["hb_late_ms"])}


# ------------------------------------------------------------------------------------------------------------------
# http server subprocess (wait-kind http)
# ------------------------------------------------------------------------------------------------------------------
def serve(port: int) -> None:
    from aiohttp import web

    async def h(req):
        await asyncio.sleep(float(req.query.get("ms", "0")) / 1000.0)
        return web.json_response({"ok": 1})

    app = web.Application()
    app.router.add_get("/delay", h)
    web.run_app(app, host="127.0.0.1", port=port, print=None, access_log=None)


def start_server():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    proc = subprocess.Popen([sys.executable, os.path.abspath(__file__), "--serve", str(port)],
                            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    for _ in range(100):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
            return proc, f"http://127.0.0.1:{port}/delay"
        except OSError:
            time.sleep(0.1)
    proc.terminate()
    raise RuntimeError("harness http server did not start")


# ------------------------------------------------------------------------------------------------------------------
# analysis
# ------------------------------------------------------------------------------------------------------------------
def _des_block(seed: int, B: float, h: dict) -> list[float]:
    """Discrete-event replay of ONE block's M1 under this harness's own schedule: the same Schedule and delay RNG as run_block/climate_loop, ticks of length B
    every tick_secs of sleep, the internal cycle awaited inside the loop (so no tick during it), a crossing registered by the first tick whose START is at or
    after it, latency measured to the end of that tick.  No asyncio, no OS timers."""
    T, block_s = h["tick_secs"], h["block_s"]
    n_calls, med, sig = h["n_calls"], h["call_median_s"], h["call_sigma"]
    sched = Schedule(seed, block_s, h["ignite_every_s"], n_calls * med * 2.0 + 3 * T)
    rng = random.Random(seed * 104729 + 3)
    t, lat = 0.0, []
    while t < block_s:
        t += T
        s = t
        t += B
        if sched.pending(s):
            tc = sched.pop()
            lat.append(t - tc)
            t += sum(draw_delays(rng, n_calls, med, sig))
    return lat


def analyse(path: str, max_cpu: float = 60.0) -> None:
    blocks = []
    header = None
    with open(path, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r.get("record") == "header":
                header = r
            elif r.get("kind") in ("heavy", "light"):
                blocks.append(r)
    print(f"blocks: {len(blocks)} from {path}")
    if header:
        print("config:", json.dumps({k: header[k] for k in ("wait_kind", "tick_kind", "tick_secs", "heavy_ms", "light_ms", "block_s", "pairs", "seed", "n_calls", "call_median_s") if k in header}))
    pairs = defaultdict(dict)
    for b in blocks:
        pairs[b["pair"]][b["kind"]] = b

    def mean_of(b, key, stat="mean"):
        v = b.get(key, {})
        return v.get(stat) if isinstance(v, dict) else None

    metrics = [("ign_latency_s", "mean", "s"), ("internal_over_s", "mean", "s"), ("human_over_s", "mean", "s"), ("human_start_late_s", "mean", "s"),
               ("hb_late_ms", "mean", "ms"), ("hb_late_ms", "p99", "ms"), ("hb_late_ms", "max", "ms"), ("tick_ms", "mean", "ms")]
    for label, sel in (("ALL PAIRS", lambda p: True), (f"QUIET PAIRS ONLY (both blocks system CPU <= {max_cpu:.0f}%)", lambda p: all((p[k].get("system_cpu_pct") or 0) <= max_cpu for k in ("heavy", "light")))):
        use = [p for p in pairs.values() if "heavy" in p and "light" in p and sel(p)]
        print(f"\n== {label}: {len(use)} complete pairs")
        for key, stat, unit in metrics:
            hs = [mean_of(p["heavy"], key, stat) for p in use]
            ls = [mean_of(p["light"], key, stat) for p in use]
            pr = [(h, l) for h, l in zip(hs, ls) if h is not None and l is not None]
            if not pr:
                continue
            d = [h - l for h, l in pr]
            pos = sum(1 for x in d if x > 0)
            try:
                from scipy import stats as st
                w = st.wilcoxon(d) if len(d) >= 5 and any(x != 0 for x in d) else None
                pv = f"Wilcoxon p={w.pvalue:.3g}" if w is not None else "n<5"
            except Exception:
                pv = "(scipy missing)"
            print(f"  {key:>20}.{stat:<5} HEAVY mean {statistics.fmean(h for h, _ in pr):9.4f} {unit}  LIGHT {statistics.fmean(l for _, l in pr):9.4f}  paired diff {statistics.fmean(d):+9.4f} "
                  f"(HEAVY>LIGHT in {pos}/{len(d)} pairs; {pv})")
    cpu = [b.get("system_cpu_pct") for b in blocks if b.get("system_cpu_pct") is not None]
    if cpu:
        print(f"\nsystem CPU% per block: min {min(cpu):.0f} median {statistics.median(cpu):.0f} max {max(cpu):.0f}; blocks above {max_cpu:.0f}%: {sum(1 for c in cpu if c > max_cpu)}")
    print("EXPECTED (analytic, uniform phase, T=5 s tick period, B=0.9 s block): mean extra wake-up delay = B/(T+B) * B/2 = "
          f"{0.9 / 5.9 * 0.45 * 1000:.0f} ms per independent wake-up for HEAVY vs {0.03 / 5.03 * 0.015 * 1000:.2f} ms LIGHT; mean ignition start-latency difference about "
          f"{(5.9 / 2 + 0.9) - (5.03 / 2 + 0.03):.2f} s; internal_over_s difference about 0 (no tick runs during an internal cycle).")
    print("   (the per-wake-up figure applies to a wake-up that lands at a random time; a human-like cycle with n_calls sequential waits should show about n_calls times it on top of the light baseline,"
          " which is the timer-granularity floor)")
    if header and all(k in header for k in ("tick_secs", "block_s", "n_calls", "call_median_s", "call_sigma", "ignite_every_s", "seed", "heavy_ms", "light_ms")):
        # 2026-10-03 (J-0950 takeover): M1 is noisy per block (about 5 seeded crossings) and this harness's schedule is not uniform-phase (the first crossing
        # is at a fixed time and the min-gap spacing phase-locks to the tick after each cycle), so the right expectation is a discrete-event replay of the SAME
        # schedule and delay RNG with no asyncio and no OS in it.  It is also a check on the real run: measured should track the replay block by block.
        Bh, Bl = header["heavy_ms"] / 1000.0, header["light_ms"] / 1000.0
        print("\n== M1 (ignition start latency, seconds from a seeded threshold crossing to the first line of the internal cycle): MEASURED vs a discrete-event replay of the same schedule")
        print(f"  {'pair':>4} {'seed':>5}   {'meas HEAVY':>10} {'meas LIGHT':>10} {'meas diff':>10}   {'DES HEAVY':>10} {'DES LIGHT':>10} {'DES diff':>9}")
        md, dd = [], []
        for p in sorted(pairs):
            if "heavy" in pairs[p] and "light" in pairs[p]:
                sd = pairs[p]["heavy"]["seed"]
                lh, ll = pairs[p]["heavy"].get("ign_latency_raw") or [], pairs[p]["light"].get("ign_latency_raw") or []
                eh, el = _des_block(sd, Bh, header), _des_block(sd, Bl, header)
                if lh and ll and eh and el:
                    m_h, m_l, d_h, d_l = statistics.fmean(lh), statistics.fmean(ll), statistics.fmean(eh), statistics.fmean(el)
                    md.append(m_h - m_l)
                    dd.append(d_h - d_l)
                    print(f"  {p:>4} {sd:>5}   {m_h:10.3f} {m_l:10.3f} {m_h - m_l:+10.3f}   {d_h:10.3f} {d_l:10.3f} {d_h - d_l:+9.3f}")
        if md:
            print(f"  mean of pairs: measured diff {statistics.fmean(md):+.3f} s, replay diff on the same seeds {statistics.fmean(dd):+.3f} s; mean |measured - replay| per pair {statistics.fmean(abs(a - b) for a, b in zip(md, dd)):.3f} s")
        bigh, bigl = [], []
        for sd in range(header["seed"], header["seed"] + 2000):
            bigh += _des_block(sd, Bh, header)
            bigl += _des_block(sd, Bl, header)
        if bigh and bigl:
            print(f"  large-sample replay of this schedule (2000 seeds, {len(bigh)} crossings per kind): HEAVY {statistics.fmean(bigh):.3f} s, LIGHT {statistics.fmean(bigl):.3f} s, diff {statistics.fmean(bigh) - statistics.fmean(bigl):+.3f} s "
                  f"(uniform-phase analytic {(5.9 / 2 + 0.9) - (5.03 / 2 + 0.03):.2f} s)")
        allh = [x for p in pairs.values() if "heavy" in p for x in (p["heavy"].get("ign_latency_raw") or [])]
        alll = [x for p in pairs.values() if "light" in p for x in (p["light"].get("ign_latency_raw") or [])]
        if len(allh) > 2 and len(alll) > 2:
            se = math.sqrt(statistics.variance(allh) / len(allh) + statistics.variance(alll) / len(alll))
            dall = statistics.fmean(allh) - statistics.fmean(alll)
            print(f"  pooled measured crossings: HEAVY {statistics.fmean(allh):.3f} s (n {len(allh)}), LIGHT {statistics.fmean(alll):.3f} s (n {len(alll)}), diff {dall:+.3f} s, "
                  f"standard error {se:.3f} s (95% interval {dall - 1.96 * se:+.2f} .. {dall + 1.96 * se:+.2f}); M1 is a small-sample read by construction (about 5 crossings per block), "
                  f"which is why the replay on the same seeds is the comparison that matters")


def quiet_gate(a) -> bool:
    """Refuse to run a measured phase on a loaded machine (other jobs' CPU corrupts timings).  smoke ignores this."""
    t0 = system_times()
    time.sleep(10.0)
    v = cpu_pct(t0, system_times())
    print(f"quiet-machine gate: system CPU over 10 s = {v if v is None else round(v, 1)}% (limit {a.max_cpu:.0f}%)")
    return v is None or v <= a.max_cpu


def do_measure(a, out_path: str, tick_secs=None) -> None:
    _AUDIT["exempt"] = os.path.abspath(out_path).lower()
    snap0 = process_snapshot()
    blobs = None
    if a.tick_kind == "json":
        t0 = time.perf_counter()
        blobs = {"heavy": make_blob(a.heavy_mb), "light": make_blob(a.light_mb)}
        print(f"synthetic blobs built in {time.perf_counter()-t0:.1f}s ({len(blobs['heavy'])/1e6:.1f} MB heavy, {len(blobs['light'])/1e6:.2f} MB light)")
    proc = url = None
    if a.wait_kind == "http":
        proc, url = start_server()
        print("http server subprocess up:", url)

        async def _warm():                       # first aiohttp import + first ClientSession would otherwise land in block 1
            for _ in range(3):
                await wait_call("http", 0.01, url)
        asyncio.run(_warm())
    busy_wait_ms(50)
    try:
        header = {"record": "header", "ts": time.time(), "wait_kind": a.wait_kind, "tick_kind": a.tick_kind, "tick_secs": a.tick_secs, "heavy_ms": a.heavy_ms, "light_ms": a.light_ms,
                  "block_s": a.block_s, "pairs": a.pairs, "seed": a.seed, "n_calls": a.n_calls, "call_median_s": a.call_median_s, "call_sigma": a.call_sigma,
                  "ignite_every_s": a.ignite_every_s, "human_every_s": a.human_every_s, "chatter": a.chatter, "hb_ms": a.hb_ms,
                  "python": sys.version, "platform": platform.platform(), "loop": "ProactorEventLoop" if hasattr(asyncio, "ProactorEventLoop") and os.name == "nt" else "default",
                  "perf_counter": str(time.get_clock_info("perf_counter")), "process_snapshot_start": snap0}
        done_keys = set()
        if getattr(a, "resume", False) and os.path.exists(out_path):
            with open(out_path, encoding="utf-8") as f:
                for line in f:
                    try:
                        r = json.loads(line)
                    except Exception:
                        continue
                    if r.get("kind") in ("heavy", "light"):
                        done_keys.add((r["pair"], r["kind"]))
            print(f"resume: {len(done_keys)} finished blocks found in {out_path}")
        with open(out_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(header) + "\n")
        # ABBA counterbalancing: pair p runs H,L when p is even and L,H when p is odd; the SAME seed for both blocks of a pair
        for p in range(a.pairs):
            order = ("heavy", "light") if p % 2 == 0 else ("light", "heavy")
            for slot, kind in enumerate(order):
                if (p, kind) in done_keys:
                    continue
                tk = Tick(kind, a.tick_kind, a.heavy_ms, a.light_ms, blobs)
                res = run_block(a, kind, a.seed + p, tk, url, p, slot)
                with open(out_path, "a", encoding="utf-8") as f:                 # resumable style: one row per finished block
                    f.write(json.dumps(res) + "\n")
                print(f"pair {p} slot {slot} {kind:>5}: wall {res['wall_s']:.1f}s  cpu {res['system_cpu_pct'] and round(res['system_cpu_pct'])}%  tick mean {res['tick_ms'].get('mean', 0):.0f} ms  "
                      f"ign_lat {res['ign_latency_s'].get('mean', float('nan')):.2f} s (n {res['ign_latency_s']['n']})  human_over {res['human_over_s'].get('mean', float('nan')):.3f} s (n {res['human_over_s']['n']})  "
                      f"internal_over {res['internal_over_s'].get('mean', float('nan')):.3f} s  hb mean {res['hb_late_ms'].get('mean', 0):.1f} ms p99 {res['hb_late_ms'].get('p99', 0):.0f} ms", flush=True)
        snap1 = process_snapshot()
        with open(out_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"record": "footer", "ts": time.time(), "process_snapshot_end": snap1, "audit_write_attempts_under_live_data": _AUDIT["n"]}) + "\n")
    finally:
        if proc is not None:
            proc.terminate()
    print(f"write attempts under live data: {_AUDIT['n']}" + (f"  {_AUDIT['paths'][:3]}" if _AUDIT["n"] else ""))
    analyse(out_path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--serve", type=int, default=None, help=argparse.SUPPRESS)
    ap.add_argument("mode", nargs="?", choices=["smoke", "measure", "analyse", "calibrate"])
    ap.add_argument("--out", default=os.path.join(tempfile.gettempdir(), "j0950_harness_results.jsonl"))
    ap.add_argument("--wait-kind", choices=["sleep", "http"], default="http")
    ap.add_argument("--tick-kind", choices=["spin", "json"], default="spin")
    ap.add_argument("--tick-secs", type=float, default=5.0)
    ap.add_argument("--heavy-ms", type=float, default=900.0)
    ap.add_argument("--light-ms", type=float, default=30.0)
    ap.add_argument("--heavy-mb", type=float, default=60.0)
    ap.add_argument("--light-mb", type=float, default=2.0)
    ap.add_argument("--block-s", type=float, default=150.0)
    ap.add_argument("--pairs", type=int, default=6)
    ap.add_argument("--seed", type=int, default=950)
    ap.add_argument("--n-calls", type=int, default=6, help="sequential synthetic 'LLM calls' per cycle")
    ap.add_argument("--call-median-s", type=float, default=0.4)
    ap.add_argument("--call-sigma", type=float, default=0.5)
    ap.add_argument("--ignite-every-s", type=float, default=20.0, help="mean seconds between seeded ignition crossings (real: ~1100; only the tick PHASE matters "
                    "for start latency, and ~10%% of loop time spent inside an internal cycle matches the real ~11%%)")
    ap.add_argument("--resume", action="store_true", help="measure mode: skip (pair, kind) blocks already present in --out")
    ap.add_argument("--force", action="store_true", help="measure mode: skip the 10 s quiet-machine gate")
    ap.add_argument("--human-every-s", type=float, default=25.0)
    ap.add_argument("--chatter", type=int, default=4)
    ap.add_argument("--hb-ms", type=float, default=20.0)
    ap.add_argument("--grace-s", type=float, default=20.0)
    ap.add_argument("--max-cpu", type=float, default=60.0)
    ap.add_argument("--smoke-configs", default="sleep:spin,http:spin,sleep:json", help="smoke mode only: comma list of wait_kind:tick_kind")
    a = ap.parse_args()
    if a.serve is not None:
        serve(a.serve)
        return 0
    if a.mode is None:
        ap.print_help()
        return 2
    if a.mode == "analyse":
        analyse(a.out, a.max_cpu)
        return 0
    if a.mode == "calibrate":
        for label, mb in (("heavy", a.heavy_mb), ("light", a.light_mb)):
            t0 = time.perf_counter()
            blob = make_blob(mb)
            tb = time.perf_counter() - t0
            ts = []
            for _ in range(5):
                t1 = time.perf_counter()
                json.loads(blob)
                ts.append((time.perf_counter() - t1) * 1000.0)
            print(f"{label}: blob {len(blob)/1e6:.1f} MB (built in {tb:.1f}s); json.loads ms over 5 runs: min {min(ts):.0f} median {statistics.median(ts):.0f} max {max(ts):.0f}")
        return 0
    if a.mode == "smoke":
        # a scaled-down exercise of every code path (NOT the measured phase): tick 1 s, heavy 300 ms / light 10 ms, 2 blocks x 12 s, both wait kinds, both tick kinds
        out = os.path.join(tempfile.gettempdir(), "j0950_harness_smoke.jsonl")
        if os.path.exists(out):
            os.remove(out)
        for wk, tk in [tuple(c.split(":")) for c in a.smoke_configs.split(",")]:
            a2 = argparse.Namespace(**vars(a))
            a2.wait_kind, a2.tick_kind, a2.tick_secs, a2.heavy_ms, a2.light_ms = wk, tk, 1.0, 300.0, 10.0
            a2.heavy_mb, a2.light_mb, a2.block_s, a2.pairs, a2.ignite_every_s, a2.human_every_s = 6.0, 0.3, 12.0, 1, 5.0, 4.0
            a2.grace_s, a2.n_calls, a2.call_median_s = 8.0, 3, 0.15
            print(f"\n--- smoke: wait_kind={wk} tick_kind={tk}")
            do_measure(a2, out)
        return 0
    if not a.force and not quiet_gate(a):
        print("REFUSING to start the measured phase: the machine is not quiet (rerun later, or pass --force to override and accept flagged results).")
        return 3
    do_measure(a, a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
