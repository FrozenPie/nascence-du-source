"""scripts/test_supervisor_host_starved.py (J-3979, ramses_second_tier, D-0761): hermetic proof that a probe TIMEOUT
while available RAM < HOST_STARVED_RAM_GB is logged but not counted toward the 2-consecutive-fail restart rule.

Touches nothing live: imports a COPY of supervisor.py from a temp dir, scratch port 11497 fake server, restart()
replaced by a recorder, psutil.virtual_memory stubbed.

  [1] starved + timeout: sweeps do not increment fail_count, never restart, the log line says RAM-starved
  [2] not starved + timeout: normal 1/2 then 2/2 -> restart (unchanged)
  [3] starved but NOT a timeout (refused): still counts
  [4] safety cap: after HOST_STARVED_MAX_SKIPS excused checks, failures count again
  [5] a healthy probe resets the skip counter; fail-open when psutil raises

Run:  python scripts/test_supervisor_host_starved.py
"""
from __future__ import annotations
import contextlib, http.server, importlib.util, io, shutil, socket, sys, tempfile, threading, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "scripts" / "supervisor.py"
PORT = 11497
DEAD = 11496
assert PORT not in (11433, 11439, 11440, 11442)
ok_all = True
def check(name, cond, detail=""):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"    <- {detail}" if detail and not cond else ""))

tmp = Path(tempfile.mkdtemp(prefix="j3979_"))
dest = tmp / "tree" / "scripts"; dest.mkdir(parents=True)
shutil.copyfile(SRC, dest / "supervisor.py")
if (SRC.parent / "resolve_blob.py").exists():
    shutil.copyfile(SRC.parent / "resolve_blob.py", dest / "resolve_blob.py")
spec = importlib.util.spec_from_file_location("supervisor_j3979", dest / "supervisor.py")
sup = importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()):
    spec.loader.exec_module(sup)
assert Path(sup.EVENTS_LOG).resolve().is_relative_to(tmp), sup.EVENTS_LOG
sup._host_snapshot = lambda window=1.0, top_n=3: "FAKE"

MODE = {"wedge": True}
class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        try:
            if MODE["wedge"]:
                time.sleep(3); return
            self.send_response(200); self.send_header("Content-Length", "2"); self.end_headers(); self.wfile.write(b"{}")
        except (ConnectionError, OSError):
            pass
    def handle(self):
        try: super().handle()
        except (ConnectionError, OSError): pass
class Server(http.server.ThreadingHTTPServer):
    daemon_threads = True; allow_reuse_address = True
for p in (PORT, DEAD):
    with socket.socket() as s:
        if s.connect_ex(("127.0.0.1", p)) == 0:
            print(f"scratch port {p} taken"); sys.exit(2)
srv = Server(("127.0.0.1", PORT), Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()

class VM:
    def __init__(self, gb): self.available = int(gb * 2**30); self.total = 64 * 2**30
RAM = {"gb": 0.5}
class FakePs:
    def __getattr__(self, n): return getattr(real_ps, n)
    def virtual_memory(self): return VM(RAM["gb"])
real_ps = sup.psutil
sup.psutil = FakePs()

def lines(): return Path(sup.EVENTS_LOG).read_text(encoding="utf-8").splitlines() if Path(sup.EVENTS_LOG).exists() else []
def mk(port):
    sup.SERVERS.clear()
    sup.SERVERS["fake"] = {"port": port, "bin": sys.executable, "cwd": None, "args": [], "log": "fake", "env": {},
                           "health_path": "/api/tags", "health_timeout": 0.4, "proc_match": "nothing"}
restarts = []
sup.restart = lambda name: restarts.append(name)
def sw(fc):
    with contextlib.redirect_stdout(io.StringIO()):
        return sup.sweep(fc)

try:
    mk(PORT); sup._stats.reset(); fc = {"fake": 0}
    print("[1] starved + timeout")
    RAM["gb"] = 0.5; MODE["wedge"] = True
    n0 = len(lines())
    for _ in range(4): sw(fc)
    new = [l for l in lines()[n0:] if "RAM-starved" in l]
    check("4 starved timeouts: fail_count 0, no restart", fc["fake"] == 0 and not restarts)
    check("each logged as RAM-starved with the reading", len(new) == 4 and "ram_avail=0.5GB" in new[0] and "err=timeout" in new[0], str(new[:1]))

    print("[2] not starved + timeout")
    sup._starved_skips.clear(); RAM["gb"] = 8.0
    sw(fc); check("1/2 counts", fc["fake"] == 1 and not restarts)
    sw(fc); check("2/2 restarts", restarts == ["fake"] and fc["fake"] == 0)

    print("[3] starved but dead port (connect-phase failure, not a read timeout)")
    restarts.clear(); mk(DEAD); fc = {"fake": 0}; RAM["gb"] = 0.5; sup._starved_skips.clear()
    sw(fc); check("dead port still counts 1/2", fc["fake"] == 1 and not restarts)
    sw(fc); check("then restarts", restarts == ["fake"])

    print("[4] safety cap")
    restarts.clear(); mk(PORT); fc = {"fake": 0}; sup._starved_skips.clear(); RAM["gb"] = 0.5; MODE["wedge"] = True
    for _ in range(sup.HOST_STARVED_MAX_SKIPS): sw(fc)
    check("cap skips all excused", fc["fake"] == 0 and not restarts)
    sw(fc); check("next failure counts again (1/2)", fc["fake"] == 1 and not restarts)
    sw(fc); check("and restarts at 2/2", restarts == ["fake"])

    print("[5] reset on healthy + fail-open")
    restarts.clear(); fc = {"fake": 0}; sup._starved_skips.clear(); RAM["gb"] = 0.5; MODE["wedge"] = True
    sw(fc); sw(fc)
    MODE["wedge"] = False; sw(fc)
    check("healthy resets skip counter", sup._starved_skips.get("fake") == 0)
    MODE["wedge"] = True
    class Boom:
        def virtual_memory(self): raise RuntimeError("x")
    sup.psutil = Boom(); sup._starved_skips.clear(); fc = {"fake": 0}
    sw(fc); check("psutil raising -> fail-open, counts normally", fc["fake"] == 1)
finally:
    srv.shutdown()
    shutil.rmtree(tmp, ignore_errors=True)
print("\nALL PASS" if ok_all else "\nFAILURES")
sys.exit(0 if ok_all else 1)
