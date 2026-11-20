"""scripts/lag_harness/ab_pursuits_light_J2363.py (J-2363, F-3051 follow-up): one arm of the PURSUITS_LIGHT_READ A/B.
Runs loop_lag_harness.py unchanged except that core.pursuits.PURSUITS_LIGHT_READ is forced to the given value right
after the harness imports pursuits (source-injected, so the harness's own audit hook / isolation asserts run first),
and samples host load (system CPU %, every python.exe's CPU %, the harness process's own CPU %) every 30 s on a
daemon thread via psutil (native API, no subprocess). Also counts heavy vs light status() answers.
env: LAGH_SCRATCH, LAGH_WT (as the harness). Usage: python ab_pursuits_light_J2363.py <on|off> <seconds> <outname.json>"""
import sys, os, json, time, threading, pathlib

arm, dur, outname = sys.argv[1], sys.argv[2], sys.argv[3]
assert arm in ("on", "off")
HERE = pathlib.Path(__file__).resolve().parent
SRC = (HERE / "loop_lag_harness.py").read_text(encoding="utf-8")
ANCHOR = "from core import telemetry as _tel, pursuits as _pu\n"
assert SRC.count(ANCHOR) == 1
INJECT = ANCHOR + (
    "_pu.PURSUITS_LIGHT_READ = %s\n"
    "_AB = {'light_hit': 0, 'heavy': 0}\n"
    "_orig_ls = _pu._light_status\n"
    "def _ls_count():\n"
    "    r = _orig_ls()\n"
    "    if _pu.PURSUITS_LIGHT_READ: _AB['light_hit' if r is not None else 'heavy'] += 1\n"
    "    return r\n"
    "_pu._light_status = _ls_count\n"
    "_orig_ld = _pu._load\n"
    "def _ld_count(*a, **k):\n"
    "    _AB['heavy_load_calls'] = _AB.get('heavy_load_calls', 0) + 1\n"
    "    return _orig_ld(*a, **k)\n"
    "_pu._load = _ld_count\n"
    "print('J-2363 arm PURSUITS_LIGHT_READ =', _pu.PURSUITS_LIGHT_READ, flush=True)\n"
) % ("True" if arm == "on" else "False")
SRC = SRC.replace(ANCHOR, INJECT)

LOAD = []
def _sampler():
    import psutil
    me = psutil.Process()
    psutil.cpu_percent(None); me.cpu_percent(None)
    procs = {}
    while True:
        time.sleep(30)
        row = {"ts": round(time.time(), 1), "sys_cpu_pct": psutil.cpu_percent(None), "self_cpu_pct": me.cpu_percent(None),
               "mem_pct": psutil.virtual_memory().percent}
        py = []
        for p in psutil.process_iter(["pid", "name"]):
            try:
                if (p.info["name"] or "").lower().startswith("python") and p.pid != me.pid:
                    if p.pid not in procs:
                        procs[p.pid] = p; p.cpu_percent(None); continue
                    py.append(round(procs[p.pid].cpu_percent(None), 1))
            except Exception:
                pass
        row["other_python_n"] = len(py); row["other_python_cpu_pct_sum"] = round(sum(py), 1)
        LOAD.append(row)
threading.Thread(target=_sampler, daemon=True).start()

sys.argv = [str(HERE / "loop_lag_harness.py"), dur, outname]
g = {"__name__": "__main__", "__file__": str(HERE / "loop_lag_harness.py")}
exec(compile(SRC, str(HERE / "loop_lag_harness.py"), "exec"), g)

out = pathlib.Path(os.environ["LAGH_SCRATCH"]) / outname
res = json.loads(out.read_text())
res["J2363"] = {"arm": arm, "light_read": g["_pu"].PURSUITS_LIGHT_READ, "status_counts": g["_AB"], "host_load": LOAD,
                "sample_series_ts": [round(ts, 1) for ts, _ in g["T"].get("pursuits.sample_series", [])],
                "sample_series_ms_raw": [round(ms, 2) for _, ms in g["T"].get("pursuits.sample_series", [])]}
out.write_text(json.dumps(res, indent=1))
print("J-2363 counts", g["_AB"], "load rows", len(LOAD))
