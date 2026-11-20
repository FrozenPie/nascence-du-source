"""scripts/test_supervisor_probe_budget.py (J-2113, ramses_second_tier, D-0420 B+D): hermetic proof of the hot lane's
two-phase probe (connect 3.0 s / read 10 s) and the bounded host snapshots on slow-but-passing and 1/2 lines.

Touches nothing live: imports a COPY of scripts/supervisor.py from a temp dir (its data/ paths resolve there), stubs
_host_snapshot, runs an in-process fake HTTP server on a scratch port (11498) whose behaviour the test steers per
request, replaces restart() with a recorder (nothing is ever killed or launched), and never contacts the live lanes
(11433/11439/11440/11442) or the running supervisor.

  [1] constants and specs: HOT_READ_TIMEOUT 10.0; hot_ollama has health_timeout 3.0 + read_timeout 10.0; the CPU hubs
      keep CPU_HEALTH_TIMEOUT 10.0 and have no read_timeout; _log_config names both hot budgets
  [2] two-phase is_healthy: an answer after 1.2 s under connect 0.5 / read 3.0 -> True (the old single budget of 0.5
      would have failed it); the note carries timeout=3.0 (read) + connect_timeout=0.5, err ''; fast answer -> True
  [3] read wedge: accepted, never answered -> False after ~read budget, err=timeout phase=read, timeout = read budget
  [4] dead port: refused in connect time -> False fast, err=refused, timeout = connect budget; a connect that cannot
      complete -> phase=connect (URLError-wrapped) when it times out
  [5] single-phase path unchanged (no read_timeout): slow answer past the budget -> False err=timeout phase=read via
      urllib; read_timeout <= timeout collapses to the single-phase path
  [6] sweep(): slow-but-passing lines carry ' | host: ' up to SLOW_SNAPSHOT_LINES_PER_WINDOW per lane per window, the
      lines after that are still written without it; the 1/2 failure line carries the snapshot; the 2/2 line does not
      (restart() takes the pre-kill one) and restart() is reached exactly once; fail counts as before
  [7] every new helper is fail-open: a raising _host_snapshot never breaks the sweep

Run:  python scripts/test_supervisor_probe_budget.py   (from the tree under test)
"""
from __future__ import annotations
import contextlib, http.server, importlib.util, io, shutil, socket, sys, tempfile, threading, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "scripts" / "supervisor.py"
PORT = 11498
assert PORT not in (11433, 11439, 11440, 11442)

ok_all = True
def check(name, cond, detail=""):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"    <- {detail}" if detail and not cond else ""))

# ── load a COPY of supervisor.py so its own data/ paths resolve inside the temp dir ──────────────────────
tmp = Path(tempfile.mkdtemp(prefix="j2113_"))
dest = tmp / "tree" / "scripts"; dest.mkdir(parents=True)
shutil.copyfile(SRC, dest / "supervisor.py")
if (SRC.parent / "resolve_blob.py").exists():
    shutil.copyfile(SRC.parent / "resolve_blob.py", dest / "resolve_blob.py")   # the CPU-hub specs resolve model blobs through it at import
spec = importlib.util.spec_from_file_location("supervisor_j2113", dest / "supervisor.py")
sup = importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()):
    spec.loader.exec_module(sup)
assert Path(sup.EVENTS_LOG).resolve().is_relative_to(tmp), sup.EVENTS_LOG
sup._host_snapshot = lambda window=1.0, top_n=3: f"cpu=7% FAKE window={window}"

# ── the fake lane: an in-process HTTP server steered by MODE ─────────────────────────────────────────────
MODE = {"delay": 0.0, "wedge": False, "status": 200}

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        try:
            if MODE["wedge"]:
                time.sleep(4)         # never answers within any test budget; the client closes first
                return
            if MODE["delay"]:
                time.sleep(MODE["delay"])
            self.send_response(MODE["status"]); self.send_header("Content-Length", "2"); self.end_headers()
            self.wfile.write(b"{}")
        except (ConnectionError, OSError):
            pass                      # the client gave up (expected in the wedge / slow cases); not a test failure
    def handle(self):
        try:
            super().handle()
        except (ConnectionError, OSError):
            pass

class Server(http.server.ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

with socket.socket() as s:
    if s.connect_ex(("127.0.0.1", PORT)) == 0:
        print(f"scratch port {PORT} is taken; refusing to run"); sys.exit(2)
srv = Server(("127.0.0.1", PORT), Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()

def note(): return sup._last_probe.get(PORT) or {}
def lines(): return Path(sup.EVENTS_LOG).read_text(encoding="utf-8").splitlines() if Path(sup.EVENTS_LOG).exists() else []

try:
    print("[1] constants and specs")
    check("HOT_READ_TIMEOUT 10.0", sup.HOT_READ_TIMEOUT == 10.0)
    hot = sup.SERVERS["hot_ollama"]
    check("hot_ollama: connect budget 3.0 (health_timeout), read budget 10.0 (read_timeout)", hot.get("health_timeout") == 3.0 and hot.get("read_timeout") == 10.0)
    cpu = [s_ for n, s_ in sup.SERVERS.items() if n != "hot_ollama"]
    check("the four CPU hubs (3 lazy + the D-0539 resident take hub): health_timeout 10.0 (D-0194), no read_timeout", len(cpu) == 4 and all(s_.get("health_timeout") == 10.0 and s_.get("read_timeout") is None for s_ in cpu))
    check("2-consecutive rule still the constant in sweep() (source text)", "if fail_count[name] >= 2:" in SRC.read_text(encoding="utf-8"))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        sup._log_config()
    check("_log_config names both hot budgets", "hot_ollama=3.0s(read 10.0s)" in buf.getvalue() and "judge1_hub=10.0s" in buf.getvalue())
    check("SLOW_SNAPSHOT_LINES_PER_WINDOW 5, SLOW_SNAPSHOT_WINDOW_S 0.5", sup.SLOW_SNAPSHOT_LINES_PER_WINDOW == 5 and sup.SLOW_SNAPSHOT_WINDOW_S == 0.5)

    print("[2] two-phase is_healthy: slow but alive passes under the read budget")
    MODE.update(delay=1.2, wedge=False, status=200)
    t0 = time.perf_counter(); r = sup.is_healthy(PORT, 0.5, "/api/tags", read_timeout=3.0); dt = time.perf_counter() - t0
    check("1.2 s answer under connect 0.5 / read 3.0 -> True", r is True and 1.0 < dt < 2.5, f"r={r} dt={dt:.2f}")
    n = note()
    check("note: timeout = read budget 3.0, connect_timeout 0.5, err ''", n.get("timeout") == 3.0 and n.get("connect_timeout") == 0.5 and n.get("err") == "")
    check("_probe_detail shows both budgets", "timeout=3.0s" in sup._probe_detail({"port": PORT}) and "connect_timeout=0.5s" in sup._probe_detail({"port": PORT}))
    MODE.update(delay=0.0)
    t0 = time.perf_counter(); r = sup.is_healthy(PORT, 0.5, "/api/tags", read_timeout=3.0); dt = time.perf_counter() - t0
    check("fast answer -> True quickly", r is True and dt < 0.5)
    MODE.update(status=500)
    check("HTTP 500 -> False, err http_500", sup.is_healthy(PORT, 0.5, "/api/tags", read_timeout=3.0) is False and note().get("err") == "http_500")
    MODE.update(status=200)

    print("[3] read wedge")
    MODE.update(wedge=True)
    t0 = time.perf_counter(); r = sup.is_healthy(PORT, 0.5, "/api/tags", read_timeout=1.5); dt = time.perf_counter() - t0
    n = note()
    check("accepted but never answered -> False after ~read budget (1.5 s)", r is False and 1.3 < dt < 3.0, f"r={r} dt={dt:.2f}")
    check("note: err=timeout phase=read, timeout = read budget", n.get("err") == "timeout" and n.get("phase") == "read" and n.get("timeout") == 1.5, str(n))
    MODE.update(wedge=False)

    print("[4] dead port")
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0)); dead = s.getsockname()[1]
    # Windows loopback reports a closed port as refused only after its SYN retry (~1 s on this box; the J-1688 test
    # documents the same), so the real hot connect budget (3.0 s) is used here: a dead port must read refused well
    # inside it and never wait out the 10 s read budget.
    t0 = time.perf_counter(); r = sup.is_healthy(dead, 3.0, "/api/tags", read_timeout=10.0); dt = time.perf_counter() - t0
    n = sup._last_probe.get(dead) or {}
    check("closed port under connect 3.0 / read 10.0 -> False as refused inside the connect budget, never the read budget",
          r is False and dt < 3.0 and n.get("err") == "refused" and n.get("phase") == "", f"dt={dt:.2f} {n}")
    check("note: timeout = connect budget (3.0) on a connect-phase failure", n.get("timeout") == 3.0 and n.get("connect_timeout") == 3.0)
    t0 = time.perf_counter(); r = sup.is_healthy(dead, 0.3, "/api/tags", read_timeout=10.0); dt = time.perf_counter() - t0
    n = sup._last_probe.get(dead) or {}
    check("closed port under a too-short connect budget (0.3) -> timeout/connect at ~0.3 s, not 10 s", r is False and dt < 1.0 and n.get("err") == "timeout" and n.get("phase") == "connect", f"dt={dt:.2f} {n}")
    # a connect that cannot complete: a non-routable address is not available on loopback, so prove the wrapping directly
    exc = urllib_err = None
    try:
        raise sup.urllib.error.URLError(TimeoutError("connect"))
    except Exception as e:
        exc = e
    cat, phase, cls = sup._probe_error(exc)
    check("a connect-phase timeout (URLError-wrapped) classifies as timeout/connect", cat == "timeout" and phase == "connect")

    print("[5] single-phase path unchanged")
    MODE.update(delay=1.0)
    t0 = time.perf_counter(); r = sup.is_healthy(PORT, 0.4, "/api/tags"); dt = time.perf_counter() - t0
    n = note()
    check("no read_timeout: 1.0 s answer under 0.4 -> False err=timeout phase=read (urllib path)", r is False and n.get("err") == "timeout" and n.get("phase") == "read" and n.get("connect_timeout") is None, str(n))
    r = sup.is_healthy(PORT, 2.0, "/api/tags", read_timeout=1.0)
    check("read_timeout <= timeout collapses to the single-phase path (no connect_timeout in the note)", r is True and note().get("connect_timeout") is None)
    MODE.update(delay=0.0)

    print("[6] sweep(): snapshots on slow-but-passing and 1/2 lines")
    sup.SERVERS.clear()
    sup.SERVERS["fake_hot"] = {"port": PORT, "bin": sys.executable, "cwd": None, "args": [], "log": "fake", "env": {},
                               "health_path": "/api/tags", "health_timeout": 0.5, "read_timeout": 3.0, "proc_match": "nothing"}
    sup.SLOW_PROBE_S = 0.3           # make a 0.6 s answer "slow" without waiting 2 s each time
    restarts = []
    sup.restart = lambda name: restarts.append(name)
    sup._stats.reset()
    fc = {"fake_hot": 0}
    MODE.update(delay=0.6)
    n0 = len(lines())
    for _ in range(7):
        with contextlib.redirect_stdout(io.StringIO()):
            sup.sweep(fc)
    new = [l for l in lines()[n0:] if "probe slow but passed" in l]
    with_snap = [l for l in new if "| host: cpu=7% FAKE window=0.5" in l]
    check("7 slow passes -> 7 slow lines, the first 5 carry the host snapshot, the last 2 do not (cap)",
          len(new) == 7 and len(with_snap) == 5 and all("host:" in l for l in new[:5]) and all("host:" not in l for l in new[5:]), f"{len(new)} {len(with_snap)}")
    check("slow lines carry both budgets", all("connect_timeout=0.5s" in l and "timeout=3.0s" in l for l in new))
    check("healthy sweeps keep the fail count at 0", fc["fake_hot"] == 0 and not restarts)
    MODE.update(delay=0.0, wedge=True)
    n0 = len(lines())
    with contextlib.redirect_stdout(io.StringIO()):
        r1 = sup.sweep(fc)
    l1 = [l for l in lines()[n0:] if "health check failed (1/2)" in l]
    check("1/2 line written with err=timeout phase=read and the host snapshot", len(l1) == 1 and "err=timeout phase=read" in l1[0] and "| host: cpu=7% FAKE" in l1[0] and fc["fake_hot"] == 1 and r1 == [], str(l1))
    n0 = len(lines())
    with contextlib.redirect_stdout(io.StringIO()):
        r2 = sup.sweep(fc)
    l2 = [l for l in lines()[n0:] if "health check failed (2/2)" in l]
    check("2/2 line written WITHOUT the inline snapshot (restart() takes the pre-kill one); restart reached once; counter reset",
          len(l2) == 1 and "host:" not in l2[0] and restarts == ["fake_hot"] and fc["fake_hot"] == 0 and r2 == ["fake_hot"], str(l2))
    MODE.update(wedge=False)

    print("[7] fail-open")
    def boom(*a, **k): raise RuntimeError("snapshot broke")
    sup._host_snapshot = boom
    sup._stats.reset()
    MODE.update(delay=0.6)
    n0 = len(lines())
    with contextlib.redirect_stdout(io.StringIO()):
        sup.sweep(fc)
    sl = [l for l in lines()[n0:] if "probe slow but passed" in l]
    check("a raising _host_snapshot: the slow line is still written, without host", len(sl) == 1 and "host:" not in sl[0])
    MODE.update(delay=0.0, wedge=True)
    n0 = len(lines())
    with contextlib.redirect_stdout(io.StringIO()):
        sup.sweep(fc)
    fl = [l for l in lines()[n0:] if "health check failed (1/2)" in l]
    check("a raising _host_snapshot: the 1/2 line is still written, without host", len(fl) == 1 and "host:" not in fl[0] and fc["fake_hot"] == 1)
    MODE.update(wedge=False)
finally:
    srv.shutdown(); srv.server_close()

print("\nALL PASS" if ok_all else "\nFAILURES")
sys.exit(0 if ok_all else 1)
