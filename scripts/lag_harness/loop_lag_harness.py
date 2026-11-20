"""scripts/lag_harness/loop_lag_harness.py (J-1892, F-2540): real-cadence emulation of orchestrator._substrate_loop + ClimateEngine.start_background on one asyncio loop, run from a throwaway git worktree with a full-fidelity data copy (see copy_data_fullfidelity.py). env: LAGH_SCRATCH (dir with the worktree), LAGH_WT (worktree dir name, default wt_head). Usage: python loop_lag_harness.py <seconds> <outname.json> [--no-climate] [--profile]. Originally:
on the throwaway worktree's FULL-fidelity data copy (small+medium stores, DB backup copy). No model calls, no network, no subprocess
(audit hook), no write outside the scratchpad (audit hook). Usage: python loop_lag_harness.py <seconds> <outjson> [--no-climate] [--profile]"""
import sys, os, time, json, asyncio, pathlib, statistics as st, collections, traceback

SP = pathlib.Path(os.environ["LAGH_SCRATCH"])   # the scratch dir that holds the throwaway worktree (+ its data/ copy)
WT = SP / os.environ.get("LAGH_WT", "wt_head")
LIVE_ROOT = os.path.normcase(r"C:\Nascence")
SP_N = os.path.normcase(str(SP))

# ---------- safety net: audit hook ----------
def _norm(p):
    try:
        if isinstance(p, int): return None
        if isinstance(p, bytes): p = p.decode("utf-8", "replace")
        return os.path.normcase(os.path.abspath(os.fspath(p)))
    except Exception:
        return None

def _under_live(n):
    return n is not None and (n == LIVE_ROOT or n.startswith(LIVE_ROOT + os.sep)) and not n.startswith(SP_N)

_WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC
def _hook(event, args):
    try:
        if event == "open":
            path, mode, flags = args[0], args[1], args[2]
            n = _norm(path)
            if _under_live(n):
                w = False
                if isinstance(mode, str) and any(c in mode for c in "wax+"): w = True
                if isinstance(flags, int) and (flags & _WRITE_FLAGS): w = True
                if w: raise PermissionError("lag_harness audit: write under live C:\\Nascence refused: %s" % n)
        elif event in ("os.rename", "os.replace"):
            for p in args[:2]:
                if _under_live(_norm(p)): raise PermissionError("lag_harness audit: rename under live refused")
        elif event in ("os.remove", "os.rmdir", "os.mkdir", "os.truncate", "shutil.rmtree", "os.chmod"):
            if _under_live(_norm(args[0])): raise PermissionError("lag_harness audit: %s under live refused" % event)
        elif event in ("shutil.copyfile", "shutil.copy", "shutil.move", "shutil.copytree"):
            for p in args[:2]:
                if _under_live(_norm(p)) and p is args[1]: raise PermissionError("lag_harness audit: copy into live refused")
        elif event == "sqlite3.connect":
            if _under_live(_norm(args[0])): raise PermissionError("lag_harness audit: sqlite3 connect to live refused")
        elif event == "socket.connect":
            if _NET["block"]: raise PermissionError("lag_harness audit: no network")
        elif event == "subprocess.Popen":
            exe = str(args[0]); cmd = args[1]
            _SUBP.append((exe, str(cmd)[:160]))
            if not any(w in (exe.lower()+" "+str(cmd).lower()) for w in ("nvidia-smi","rocm-sdk","hipconfig")):
                raise PermissionError("lag_harness audit: no subprocess (%s)" % str(cmd)[:80])
        elif event in ("os.system", "os.exec", "os.posix_spawn", "os.spawn"):
            raise PermissionError("lag_harness audit: no subprocess")
    except PermissionError:
        raise
    except Exception:
        pass
_NET={'block':False}; _SUBP=[]
sys.addaudithook(_hook)
try:   # asyncio on Windows connects through overlapped ConnectEx, which raises NO 'socket.connect' audit event
    import asyncio.windows_events as _we
    _orig_connect = _we.IocpProactor.connect
    def _blocked_connect(self, *a, **k):
        if _NET["block"]: raise PermissionError("lag_harness audit: no network (IocpProactor.connect)")
        return _orig_connect(self, *a, **k)
    _we.IocpProactor.connect = _blocked_connect
except Exception:
    pass

os.environ.setdefault("HF_HUB_OFFLINE", "1"); os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
sys.path.insert(0, str(WT)); os.chdir(WT)
import core
assert str(pathlib.Path(core.__file__).resolve()).lower().startswith(str(WT).lower()), core.__file__
from core import profile
assert str(profile._DATA).lower().startswith(str(WT).lower()), profile._DATA
profile.mark_live()      # the worktree's own _DATA only; the audit hook above refuses any write under live C:\Nascence
from core.memory import store
assert str(store.DB_PATH).lower().startswith(str(WT).lower()), store.DB_PATH

DUR = float(sys.argv[1]) if len(sys.argv) > 1 else 120
OUT = SP / (sys.argv[2] if len(sys.argv) > 2 else "loop_lag_harness_out.json")
NO_CLIMATE = "--no-climate" in sys.argv
PROFILE = "--profile" in sys.argv

from core.schema import CognitiveState
from core import mood as _mood, wandering as _wander, sensorium as _room, couriers as _cour, felt_recall as _felt, transport_manager as _transport
from core import telemetry as _tel, pursuits as _pu

# ---------- per-callable timing wrappers ----------
T = collections.defaultdict(list)       # name -> [(wall_ts, ms)]
def wrap(mod, name, label=None):
    fn = getattr(mod, name, None)
    if fn is None: print("NO", mod.__name__, name); return
    label = label or f"{mod.__name__.split('.')[-1]}.{name}"
    def w(*a, **k):
        t = time.perf_counter()
        try: return fn(*a, **k)
        finally: T[label].append((time.time(), (time.perf_counter() - t) * 1000))
    w.__wrapped__ = fn
    setattr(mod, name, w)

import importlib
for modname, names in {
    "core.soundscape": ["world_tick"], "core.world_manifest": ["tick"], "core.garden": ["advance"], "core.shore_life": ["advance"],
    "core.fieldcraft": ["advance"], "core.wood_life": ["advance"], "core.study_life": ["advance"], "core.life": ["advance"],
    "core.smell": ["advance"], "core.locomotion": ["tick"], "core.thermal": ["advance"], "core.world_traces": ["advance_trace_decay"],
    "core.cat": ["tick"], "core.homeostasis": ["tick"], "core.world_model": ["tick"], "core.telemetry": ["sample", "kick", "_sample_body", "_gpu_load", "_llm_rates", "_cap"],
    "core.pursuits": ["sample_series", "status", "_load"], "core.wandering": ["perceive", "step", "kick", "_step_body"], "core.transport_manager": ["dispatch_tick"],
    "core.couriers": ["context_echo", "sound_echo"], "core.felt_recall": ["on_substrate_tick"], "core.mood": ["update"],
}.items():
    try:
        m = importlib.import_module(modname)
        for n in names: wrap(m, n)
    except Exception as e:
        print("import fail", modname, repr(e)[:100])
for n in ["_advance_garden", "_advance_wind", "_advance_weather", "_advance_fire", "_garden_event", "_shore_event", "_wood_event", "_event",
          "_world_arrival", "_presence_tick", "_save", "_load"]:
    wrap(_room, n, f"sensorium.{n}")
wrap(_room, "tick", "sensorium.tick")

state = CognitiveState(spirit_name="J1892", axiom="CORE AXIOM: become.")
SUB = {"periods": [], "bodies": [], "wake_lag": []}
CLI = {"periods": [], "bodies": []}
CAN = {"lag": []}

def substrate_body(affect):
    t0 = time.perf_counter()
    affect.tick(5.0)
    _mood.update(affect)
    getattr(_wander, "kick", _wander.step)(state)   # J-1909: the call the substrate loop makes (kick on code that has it, else step)
    _room.tick()
    try:
        _cour.context_echo() or _cour.sound_echo()
    except Exception: pass
    try:
        _felt.on_substrate_tick(affect)
    except Exception: pass
    return (time.perf_counter() - t0) * 1000

_tt = {"n": 0}
async def substrate_loop(stop):
    last_wake = None
    while not stop.is_set():
        await asyncio.sleep(5.0)
        wake = time.perf_counter()
        if last_wake is not None: SUB["periods"].append(wake - last_wake)
        last_wake = wake
        t = time.perf_counter()
        ms = substrate_body(state.affect)
        _tt["n"] += 1
        if _tt["n"] >= 12:
            _tt["n"] = 0
            t2 = time.perf_counter()
            try: _transport.dispatch_tick()
            except Exception: pass
            ms += (time.perf_counter() - t2) * 1000
        SUB["bodies"].append(ms)

async def canary(stop, step=0.7):
    # random-phase canary: how late does a plain short timer fire on this loop?
    while not stop.is_set():
        t = time.perf_counter()
        await asyncio.sleep(step)
        CAN["lag"].append((time.perf_counter() - t - step) * 1000)

async def climate_runner(stop, eng):
    orig_tick = eng.tick
    last = {"w": None}
    def tick_w(*a, **k):
        now = time.perf_counter()
        if last["w"] is not None: CLI["periods"].append(now - last["w"])
        last["w"] = now
        t = time.perf_counter()
        try: return orig_tick(*a, **k)
        finally: CLI["bodies"].append((time.perf_counter() - t) * 1000)
    eng.tick = tick_w
    task = asyncio.create_task(eng.start_background(state))
    await stop.wait()
    task.cancel()
    try: await task
    except BaseException: pass

async def main():
    stop = asyncio.Event()
    tasks = [asyncio.create_task(substrate_loop(stop)), asyncio.create_task(canary(stop))]
    eng = None
    if not NO_CLIMATE:
        from core.climate_engine import ClimateEngine
        eng = ClimateEngine(ignition_callback=None)
        tasks.append(asyncio.create_task(climate_runner(stop, eng)))
    await asyncio.sleep(DUR)
    stop.set()
    await asyncio.sleep(6)
    for t in tasks: t.cancel()

# warm-up (cold first calls: embedder load, imports, caches) -- NOT counted
t0 = time.perf_counter()
for i in range(3):
    try:
        _room._last_tick = 0.0
        substrate_body(state.affect)
    except Exception as e:
        print("warm err", repr(e)[:120])
print("warmup secs", round(time.perf_counter() - t0, 1), flush=True)
for k in list(T): T[k].clear()
if PROFILE:
    import cProfile, pstats
    pr = cProfile.Profile(); pr.enable()
t_run = time.time()
_loop = asyncio.new_event_loop(); asyncio.set_event_loop(_loop)
_NET['block'] = True
try:
    _loop.run_until_complete(main())
finally:
    _NET['block'] = False; _loop.close()
print('subprocess attempts:', collections.Counter(_SUBP).most_common(6))
if PROFILE:
    pr.disable(); ps = pstats.Stats(pr); ps.sort_stats("cumulative"); ps.dump_stats(str(OUT) + ".prof")
def summ(xs):
    if not xs: return None
    xs = sorted(xs)
    return {"n": len(xs), "mean": round(st.mean(xs), 2), "median": round(st.median(xs), 2), "p90": round(xs[int(.9 * (len(xs) - 1))], 2), "p99": round(xs[int(.99 * (len(xs) - 1))], 2), "max": round(xs[-1], 2), "sum": round(sum(xs), 1)}
res = {"duration_s": DUR, "start": t_run, "components_ms": {k: summ([ms for _, ms in v]) for k, v in T.items() if v},
       "substrate_period_s": summ(SUB["periods"]), "substrate_body_ms": summ(SUB["bodies"]),
       "climate_period_s": summ(CLI["periods"]), "climate_body_ms": summ(CLI["bodies"]), "canary_lag_ms": summ(CAN["lag"])}
res["raw"] = {"sub_periods": [round(x, 3) for x in SUB["periods"]], "cli_periods": [round(x, 3) for x in CLI["periods"]],
              "sub_bodies": [round(x, 1) for x in SUB["bodies"]]}
OUT.write_text(json.dumps(res, indent=1))
print(json.dumps({k: v for k, v in res.items() if k != "raw"}, indent=1))
