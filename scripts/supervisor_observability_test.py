"""
supervisor.py observability test (2026-10-03, J-1688 from F-2280 / F-2279).

Re-creates F-1248's throwaway fake-hub harness (a tiny HTTP server on scratch port 11499) and drives the
REAL supervisor.sweep() / restart() / kill_on_port() / main() against a fake SERVERS entry, to prove:

  A. NEW  every [supervisor] line also lands, ISO-timestamped, in the append-only events log; a failed probe
          carries its timeout budget / measured elapsed / exception class; a slow-but-passing probe, a
          restart (host snapshot before the kill, outcome after) and the hourly summary each log a line;
          the log rotates, and a broken log path or broken stdout can never raise into the watchdog.
  B. SAME is_healthy()/lane_healthy()/kill_on_port() keep their contracts, and the wedge -> 1/2 -> 2/2 ->
          kill -> relaunch sequence behaves exactly like the BASELINE (the commit this build started from):
          same sweep() return values, same fail counts, same pids killed/relaunched, and every line the
          baseline printed is still printed, in the same order, with the same text (modulo pids, and the
          extra " | timeout=... elapsed=... err=..." suffix on the 'health check failed' line).

Run:   python scripts/supervisor_observability_test.py
       python scripts/supervisor_observability_test.py --supervisor <path to another supervisor.py>
         (e.g. the baseline: section A must then FAIL, section B must still PASS -- the "fails without the change" proof)
Exit code 0 = every check passed.

Touches no live state. It imports only supervisor.py (stdlib + psutil), from a COPY in a temp dir (so the
supervisor's own data/ paths resolve inside that temp dir), points every log at the temp dir, and only ever
listens on / kills things bound to 127.0.0.1:11499 (a refusal-to-run if that port is already taken). It never
touches the live lanes (11433/11439/11440/11442), the live supervisor, or any data/ store. Internal mode:
`python supervisor_observability_test.py --fake-hub PORT MODEFILE` is the throwaway hub the test launches.
"""
import argparse
import contextlib
import importlib.util
import io
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve()
PORT = 11499          # scratch port, never a live lane
BASELINE_REV = "e26d19a"   # the commit J-1688 started from: supervisor.py as it was before the observability change


# ── the fake hub (a child process: `python <this file> --fake-hub PORT MODEFILE`) ───────────────────────
def run_fake_hub(port: int, mode_file: str) -> None:
    """GET anything -> 200 {}. The mode file (read on EVERY request) steers it: 'ok', 'slow:<secs>',
    'status:<code>', or 'hang_once' = THIS process wedges from now on (accepts connections, never answers) and
    rewrites the file to 'ok' so a relaunched hub, which re-reads it, starts healthy."""
    import http.server
    import socketserver
    state = {"wedged": False}

    def read_mode() -> str:
        try:
            return Path(mode_file).read_text().strip() or "ok"
        except OSError:
            return "ok"

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            mode = read_mode()
            if mode == "hang_once":
                state["wedged"] = True
                try:
                    Path(mode_file).write_text("ok")
                except OSError:
                    pass
            if state["wedged"]:
                time.sleep(3600)
                return
            if mode.startswith("slow:"):
                time.sleep(float(mode.split(":", 1)[1]))
            if mode.startswith("status:"):
                self.send_response(int(mode.split(":", 1)[1]))
                self.end_headers()
                return
            body = b'{"models": []}'
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
        daemon_threads = True
        allow_reuse_address = False   # Windows: SO_REUSEADDR would let a second hub bind beside a still-live first

    Server(("127.0.0.1", port), Handler).serve_forever()


if len(sys.argv) > 1 and sys.argv[1] == "--fake-hub":
    run_fake_hub(int(sys.argv[2]), sys.argv[3])
    sys.exit(0)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ── tiny check framework ───────────────────────────────────────────────────────────────────────────────
RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, cond, detail: str = "") -> bool:
    RESULTS.append((name, bool(cond), detail))
    print(("  PASS  " if cond else "  FAIL  ") + name + (f"    <- {detail}" if detail and not cond else ""))
    return bool(cond)


def guarded(name: str, fn) -> None:
    """Run a check that needs the NEW code: a missing attribute / TypeError on an older supervisor.py is a FAIL
    for that check, not a crash of the whole test."""
    try:
        fn()
    except Exception as exc:
        check(name, False, f"{type(exc).__name__}: {exc}")


# ── helpers ────────────────────────────────────────────────────────────────────────────────────────────
TS = r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}[+-]\d\d:\d\d"


def port_listening(port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def load_module(src: Path, tag: str, root: Path):
    """Import a COPY of supervisor.py placed at <root>/<tag>/scripts/supervisor.py, so its own
    Path(__file__).parent.parent / 'data' resolves inside the temp dir. Returns (module, import-time stdout)."""
    dest = root / tag / "scripts"
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest / "supervisor.py")
    spec = importlib.util.spec_from_file_location(f"supervisor_{tag}", dest / "supervisor.py")
    mod = importlib.util.module_from_spec(spec)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        spec.loader.exec_module(mod)
    return mod, buf.getvalue()


def spawn_hub(mode_file: Path) -> subprocess.Popen:
    return subprocess.Popen([sys.executable, str(HERE), "--fake-hub", str(PORT), str(mode_file)],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def reaped(proc: subprocess.Popen, secs: float = 10) -> bool:
    try:
        proc.wait(timeout=secs)
        return True
    except subprocess.TimeoutExpired:
        return False


def wait_up(sup, secs: float = 20) -> bool:
    end = time.time() + secs
    while time.time() < end:
        if sup.is_healthy(PORT, 1.0, "/api/tags"):
            return True
        time.sleep(0.2)
    return False


def fake_spec(root: Path, mode_file: Path, timeout: float) -> dict:
    return {"port": PORT, "bin": sys.executable, "cwd": None,
            "args": [str(HERE), "--fake-hub", str(PORT), str(mode_file)],
            "log": "fake_hub", "logdir": root / "hublogs", "env": {}, "health_path": "/api/tags",
            "health_timeout": timeout, "proc_match": "python"}


def kill_fake_hubs() -> None:
    """Belt and braces: kill any leftover fake hub of THIS script (cmdline has --fake-hub and this file)."""
    try:
        import psutil
    except ImportError:
        return
    for p in psutil.process_iter(["pid", "cmdline"]):
        try:
            cl = p.info["cmdline"] or []
            if p.pid != os.getpid() and "--fake-hub" in cl and any(c.endswith(HERE.name) for c in cl):
                p.kill()
        except Exception:
            pass


def legacy_lines(text: str) -> list[str]:
    """The [supervisor] lines the BASELINE printed: drop the new line kinds, cut the new ' | ...' suffix
    off 'health check failed' lines, mask pids."""
    new_kinds = (" host before kill: ", " restart outcome: ", " probe slow but passed", " hourly summary:",
                 "] config: ")
    out = []
    for ln in text.splitlines():
        if not ln.startswith("[supervisor]") or any(k in ln for k in new_kinds):
            continue
        out.append(re.sub(r"pid \d+", "pid N", ln.split(" | ", 1)[0]))
    return out


def events_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines() if path.exists() else []


def strip_ts(ln: str) -> str:
    return ln.split(" ", 1)[1] if " " in ln else ln


# ── the shared scenario: healthy -> wedge -> 1/2 -> 2/2 -> kill -> relaunch ─────────────────────────────
def wedge_scenario(sup, root: Path, label: str) -> dict:
    mode = root / f"mode_{label}.txt"
    mode.write_text("ok")
    sup.SERVERS = {"fake_hub": fake_spec(root, mode, 1.0)}
    sup._procs.clear()
    ev = root / f"events_{label}.log"
    if hasattr(sup, "EVENTS_LOG"):
        sup.EVENTS_LOG = ev
    h0 = spawn_hub(mode)
    t: dict = {"label": label, "events": ev}
    try:
        if not wait_up(sup):
            raise RuntimeError("fake hub did not come up")
        fc = {"fake_hub": 0}
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            t["r1"], t["c1"] = sup.sweep(fc), fc["fake_hub"]                       # healthy
            mode.write_text("hang_once")
            t0 = time.perf_counter()
            t["r2"], t["c2"] = sup.sweep(fc), fc["fake_hub"]                       # wedged probe: 1/2
            t["d2"] = time.perf_counter() - t0
            t["r3"], t["c3"] = sup.sweep(fc), fc["fake_hub"]                       # wedged probe: 2/2 -> restart
        t["stdout"] = buf.getvalue()
        t["h0_pid"] = h0.pid
        try:
            h0.wait(timeout=10)
            t["h0_dead"] = True
        except subprocess.TimeoutExpired:
            t["h0_dead"] = False
        proc1 = sup._procs.get("fake_hub")
        t["h1_pid"] = proc1.pid if proc1 else None
        t["h1_healthy"] = sup.is_healthy(PORT, 1.0, "/api/tags")
        return t
    except BaseException:
        h0.kill()
        kill_fake_hubs()
        raise


def stop_hub(sup) -> None:
    p = sup._procs.get("fake_hub")
    if p and p.poll() is None:
        p.kill()
        try:
            p.wait(timeout=10)
        except subprocess.TimeoutExpired:
            pass
    kill_fake_hubs()


# ── sections ───────────────────────────────────────────────────────────────────────────────────────────
def contract_checks(sup, label: str, root: Path, new_features: bool) -> None:
    """is_healthy()'s and kill_on_port()'s old contracts (run on the baseline AND the new code); with
    new_features also the diagnostics they now leave behind for sweep() / restart()."""
    print(f"-- [{label}] is_healthy() / kill_on_port() contract")
    mode = root / f"mode_contract_{label}.txt"
    mode.write_text("ok")
    h = spawn_hub(mode)
    try:
        check(f"[{label}] fake hub up", wait_up(sup))
        check(f"[{label}] is_healthy(HTTP 200) is True", sup.is_healthy(PORT, 1.0, "/api/tags") is True)
        if new_features:
            guarded(f"[{label}] probe note for a 200 has no error",
                    lambda: check(f"[{label}] probe note for a 200 has no error",
                                  sup._last_probe[PORT]["err"] == "" and 0 <= sup._last_probe[PORT]["elapsed"] < 1.0))
        mode.write_text("status:500")
        check(f"[{label}] is_healthy(HTTP 500) is False", sup.is_healthy(PORT, 1.0, "/api/tags") is False)
        if new_features:
            guarded(f"[{label}] probe note for a 500 says http_500",
                    lambda: check(f"[{label}] probe note for a 500 says http_500",
                                  sup._last_probe[PORT]["err"] == "http_500" and "HTTPError" in sup._last_probe[PORT]["exc"]))
        mode.write_text("slow:2.5")
        t0 = time.perf_counter()
        r = sup.is_healthy(PORT, 0.7, "/api/tags")
        dt = time.perf_counter() - t0
        check(f"[{label}] is_healthy(timeout) is False after ~the timeout", r is False and 0.6 < dt < 1.8, f"r={r} dt={dt:.2f}")
        if new_features:
            guarded(f"[{label}] probe note for a timeout says timeout, elapsed ~0.7 s",
                    lambda: check(f"[{label}] probe note for a timeout says timeout, elapsed ~0.7 s",
                                  sup._last_probe[PORT]["err"] == "timeout" and 0.6 < sup._last_probe[PORT]["elapsed"] < 1.8
                                  and sup._last_probe[PORT]["timeout"] == 0.7 and sup._last_probe[PORT]["phase"] == "read"
                                  and sup._last_probe[PORT]["exc"] == "TimeoutError", str(sup._last_probe.get(PORT))))
    finally:
        h.kill()
        h.wait(timeout=10)
    check(f"[{label}] is_healthy(closed port) is False", sup.is_healthy(PORT, 1.0, "/api/tags") is False)
    if new_features:
        # Windows reports a closed loopback port as 'refused' only after ~2 s of SYN retries, so a budget under
        # that shows up as a connect-phase timeout. Both are real, and the phase tells them from a wedged server.
        sup.is_healthy(PORT, 0.5, "/api/tags")
        guarded(f"[{label}] probe note for a closed port under a short budget says timeout/connect (URLError)",
                lambda: check(f"[{label}] probe note for a closed port under a short budget says timeout/connect (URLError)",
                              sup._last_probe[PORT]["err"] == "timeout" and sup._last_probe[PORT]["phase"] == "connect"
                              and sup._last_probe[PORT]["exc"] == "URLError(TimeoutError)", str(sup._last_probe.get(PORT))))
        r_dead = sup.is_healthy(PORT, 5.0, "/api/tags")
        guarded(f"[{label}] probe note for a closed port under a long budget says refused",
                lambda: check(f"[{label}] probe note for a closed port under a long budget says refused",
                              r_dead is False and sup._last_probe[PORT]["err"] == "refused" and sup._last_probe[PORT]["phase"] == ""
                              and sup._last_probe[PORT]["exc"] == "URLError(ConnectionRefusedError)"
                              and sup._last_probe[PORT]["elapsed"] < 5.0, str(sup._last_probe.get(PORT))))
    # kill_on_port: the 2-arg call keeps returning the int count killed; the new optional list collects the pids
    mode.write_text("ok")
    h = spawn_hub(mode)
    try:
        wait_up(sup)
        n1 = sup.kill_on_port(PORT, "python")
        check(f"[{label}] kill_on_port(port, match) returns the int count killed (1) and the hub dies",
              n1 == 1 and isinstance(n1, int) and reaped(h), str(n1))
    finally:
        h.kill()
        reaped(h)
    if new_features:
        h = spawn_hub(mode)
        try:
            wait_up(sup)
            pids: list = []
            guarded(f"[{label}] kill_on_port(port, match, pids) fills pids",
                    lambda: check(f"[{label}] kill_on_port(port, match, pids) fills pids",
                                  sup.kill_on_port(PORT, "python", pids) == 1 and pids == [h.pid], f"pids={pids} hub={h.pid}"))
        finally:
            h.kill()
            reaped(h)
    n = sup.kill_on_port(PORT, "python")
    check(f"[{label}] kill_on_port(port, match) returns 0 when nothing listens", n == 0 and isinstance(n, int), str(n))


def new_feature_checks(sup, root: Path, t: dict) -> None:
    """Section A against the wedge scenario's trace t, then slow / 500 / refused / summary / rotation / safety."""
    print("-- [new] wedge scenario: the events log and the new lines")
    ev: Path = t["events"]
    lines = events_lines(ev)
    out_lines = [ln.strip() for ln in t["stdout"].splitlines() if ln.startswith("[supervisor]")]
    check("events log exists and is non-empty", bool(lines))
    check("every events-log line starts with an ISO timestamp (ms, UTC offset) then [supervisor]",
          bool(lines) and all(re.match(rf"^{TS} \[supervisor\] ", ln) for ln in lines), lines[0] if lines else "")
    check("timestamps never go backwards", [ln.split(" ", 1)[0] for ln in lines] == sorted(ln.split(" ", 1)[0] for ln in lines))
    check("events log == stdout, line for line (stdout still carries every line, untimestamped)",
          [strip_ts(ln) for ln in lines] == out_lines, f"{len(lines)} vs {len(out_lines)}")
    f1 = [ln for ln in lines if "health check failed (1/2)" in ln]
    f2 = [ln for ln in lines if "health check failed (2/2)" in ln]
    check("one 1/2 and one 2/2 failure line", len(f1) == 1 and len(f2) == 1, f"{len(f1)} {len(f2)}")
    for tag, ln in (("1/2", f1[0] if f1 else ""), ("2/2", f2[0] if f2 else "")):
        # J-2113 (D-0420 D): the 1/2 line may now end with ' | host: <snapshot>'; the 2/2 line does not (restart() snapshots)
        m = re.search(r"on port 11499 \| timeout=1\.0s elapsed=([\d.]+)s err=timeout phase=read exc=TimeoutError( \| host: .*)?$", ln)
        check(f"{tag} failure line: old text + timeout budget + measured elapsed (~1 s) + err=timeout phase=read (a wedged "
              f"server: connected, no answer) + exception class", bool(m) and 0.9 <= float(m.group(1)) <= 2.0, ln)
    snap = [ln for ln in lines if " host before kill: " in ln]
    check("exactly one host snapshot line", len(snap) == 1, str(len(snap)))
    if snap:
        s = snap[0]
        check("snapshot carries cpu, ram, disk, sample window, top_cpu and top_io",
              all(k in s for k in ("cpu=", "ram_avail=", "sample=", "top_cpu(%box)=[", "top_io=[")) and
              ("disk_read=" in s or "disk=n/a" in s), s)
    outc = [ln for ln in lines if " restart outcome: " in ln]
    check("exactly one restart outcome line", len(outc) == 1, str(len(outc)))
    if outc:
        o = outc[0]
        check("outcome names the killed pid, the relaunch pid, healthy=True and seconds-to-healthy",
              f"killed_pids=[{t['h0_pid']}]" in o and f"relaunch_pid={t['h1_pid']}" in o and "healthy=True" in o
              and re.search(r"secs_to_healthy=[\d.]+ ", o), o)
    order = [next((i for i, ln in enumerate(lines) if k in ln), -1)
             for k in ("health check failed (2/2)", "is DOWN", " host before kill: ", "killed python process",
                       "launched fake_hub", "fake_hub healthy on", " restart outcome: ")]
    check("restart log order: 2/2 fail < DOWN < host snapshot < killed < launched < healthy < outcome",
          -1 not in order and order == sorted(order), str(order))
    check("the 1/2 sweep took ~the 1.0 s budget (a wedged probe is not abandoned early)", 0.9 <= t["d2"] <= 3.0, f"{t['d2']:.2f}")

    # slow-but-passing, HTTP 500 and refused, all on the relaunched hub
    mode = root / "mode_new.txt"
    ev2 = root / "events_new_more.log"
    sup.EVENTS_LOG = ev2
    sup.SLOW_PROBE_S = 0.4
    fc = {"fake_hub": 0}
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        mode.write_text("slow:0.6")
        r_slow = sup.sweep(fc)
        mode.write_text("status:500")
        r_500 = sup.sweep(fc)
        c_500 = fc["fake_hub"]
        mode.write_text("ok")
        r_ok = sup.sweep(fc)
    lines2 = events_lines(ev2)
    print("-- [new] slow-but-passing probe, HTTP 500, recovery")
    slow = [ln for ln in lines2 if "probe slow but passed" in ln]
    check("a slow-but-passing probe logs its own line (timeout budget + elapsed >= 0.6 s) and no failure",
          r_slow == [] and len(slow) == 1 and re.search(r"timeout=1\.0s elapsed=0\.[6-9]\d*s", slow[0])
          and not any("health check failed" in ln for ln in lines2[:lines2.index(slow[0]) + 1]) if slow else False, str(slow))
    f500 = [ln for ln in lines2 if "health check failed (1/2)" in ln]
    check("an HTTP 500 probe logs err=http_500 exc=HTTPError at 1/2 and does not restart",
          r_500 == [] and c_500 == 1 and len(f500) == 1 and "err=http_500 exc=HTTPError" in f500[0], str(f500))
    check("the next healthy sweep resets the count, no restart", r_ok == [] and fc["fake_hub"] == 0)
    # refused: kill the hub, one sweep -> 1/2 err=refused; relaunch, sweep -> healthy
    stop_hub(sup)
    time.sleep(0.5)
    sup.SERVERS["fake_hub"]["health_timeout"] = 5.0      # Windows reports a closed loopback port as refused after ~2 s
    with contextlib.redirect_stdout(buf):
        r_ref = sup.sweep(fc)
        c_ref = fc["fake_hub"]
        sup.SERVERS["fake_hub"]["health_timeout"] = 1.0
        sup.launch("fake_hub")
        up = wait_up(sup)
        r_back = sup.sweep(fc)
    lines3 = events_lines(ev2)
    fref = [ln for ln in lines3 if "err=refused" in ln]
    check("a dead port logs timeout budget + elapsed + err=refused exc=URLError(ConnectionRefusedError) at 1/2, no restart",
          r_ref == [] and c_ref == 1 and len(fref) == 1 and "exc=URLError(ConnectionRefusedError)" in fref[0]
          and "timeout=5.0s" in fref[0] and "phase=" not in fref[0]
          and float(re.search(r"elapsed=([\d.]+)s", fref[0]).group(1)) < 5.0, str(fref))
    check("relaunched hub is healthy again and the count resets", up and r_back == [] and fc["fake_hub"] == 0)

    # hourly summary through the real sweep() path
    print("-- [new] hourly summary")
    ev3 = root / "events_new_summary.log"
    sup.EVENTS_LOG = ev3
    sup.SUMMARY_INTERVAL_S = 0
    with contextlib.redirect_stdout(buf):
        sup.sweep(fc)
    sup.SUMMARY_INTERVAL_S = 3600
    summ = [ln for ln in events_lines(ev3) if " hourly summary: " in ln]
    check("one summary line per window with pid, window, sweeps, late_max", len(summ) == 1 and
          re.search(rf"hourly summary: pid={os.getpid()} window=\d+s sweeps=\d+ late_max=[\d.]+s \|", summ[0]), str(summ))
    if summ:
        m = re.search(r"fake_hub n=(\d+) max=([\d.]+)s p99=([\d.]+)s >0\.4s=(\d+) failed=(\d+)", summ[0])
        check("summary has per-lane n, max, p99, probes over the slow threshold and failed probes "
              "(this run: 9 probes, max >= the 1 s timeout, 4 failed = 2 wedge + 1 HTTP 500 + 1 dead port)",
              bool(m) and int(m.group(1)) == 9 and float(m.group(2)) >= 0.9 and float(m.group(3)) >= 0.9
              and int(m.group(4)) >= 1 and int(m.group(5)) == 4, summ[0])
    check("the summary window restarted (stats reset)", sup._stats.sweeps == 0 and not sup._stats.lat)
    # the arithmetic, deterministically: 4 probes on one lane (0.1 ok, 2.5 ok-but-slow, 3.0 failed, 0.2 ok), threshold 2 s
    st = sup._SweepStats()
    sup.SLOW_PROBE_S = 2.0
    flags = [st.record("a", e, ok) for e, ok in ((0.1, True), (2.5, True), (3.0, False), (0.2, True))]
    st.sweeps = 4
    line = st.summary_line()
    check("stats: only the slow-but-PASSING probe asks for its own line; summary = n=4 max=3.000s p99=3.000s >2s=2 failed=1",
          flags == [False, True, False, False] and "a n=4 max=3.000s p99=3.000s >2s=2 failed=1" in line and "sweeps=4" in line, line)
    st2 = sup._SweepStats()
    capped = [st2.record("b", 2.5, True) for _ in range(sup.SLOW_LINES_PER_WINDOW + 5)]
    check("stats: individual slow-probe lines are capped per window, the count is not",
          capped.count(True) == sup.SLOW_LINES_PER_WINDOW and st2.slow["b"] == sup.SLOW_LINES_PER_WINDOW + 5)
    sup.SLOW_PROBE_S = 0.4

    print("-- [new] host snapshot, rotation, safety")
    t0 = time.perf_counter()
    snap = sup._host_snapshot()
    dt = time.perf_counter() - t0
    check("_host_snapshot(): cpu / ram / disk / sample coverage / top lists, in ~1 s (bounded, even on a box where "
          "psutil needs ~7 s for the whole process table)",
          0.9 <= dt < 3.0 and snap.startswith("cpu=") and "procs_sampled=" in snap and "top_cpu(%box)=[" in snap
          and "top_io=[" in snap, f"{dt:.2f}s {snap[:400]}")
    print(f"    snapshot ({dt:.2f}s): {snap}")
    real_psutil = sup.psutil
    sup.psutil = None
    check("_host_snapshot() without psutil says so instead of raising", sup._host_snapshot().startswith("unavailable"))
    sup.psutil = real_psutil
    # rotation
    rot = root / "rot" / "events.log"
    sup.EVENTS_LOG = rot
    sup.EVENTS_LOG_MAX_BYTES = 800
    with contextlib.redirect_stdout(io.StringIO()):
        for i in range(30):
            sup._log(f"[supervisor] rotation line {i:02d} " + "x" * 40)
    rot1 = rot.with_name(rot.name + ".1")
    check("log rotates to .1 past the cap, newest line in the live file, live file stays near the cap",
          rot1.exists() and "line 29" in rot.read_text(encoding="utf-8").splitlines()[-1] and rot.stat().st_size < 800 + 200,
          f"{rot1.exists()} {rot.stat().st_size}")
    sup.EVENTS_LOG_MAX_BYTES = 5 * 1024 * 1024
    # safety: an unwritable events-log path and a broken stdout must not raise
    blocker = root / "blocker"
    blocker.write_text("not a directory")
    sup.EVENTS_LOG = blocker / "sub" / "events.log"
    cap = io.StringIO()
    try:
        with contextlib.redirect_stdout(cap):
            sup._log("[supervisor] still prints")
        ok1 = "[supervisor] still prints" in cap.getvalue()
    except Exception as exc:
        ok1 = False
        print("    unwritable-path raise:", exc)
    check("an unwritable events-log path is swallowed and stdout still gets the line", ok1)

    class BrokenOut:
        def write(self, *_):
            raise OSError("broken pipe")

        def flush(self):
            raise OSError("broken pipe")

    sup.EVENTS_LOG = root / "events_broken_stdout.log"
    try:
        with contextlib.redirect_stdout(BrokenOut()):
            sup._log("[supervisor] stdout is dead")
        ok2 = True
    except Exception as exc:
        ok2 = False
        print("    broken-stdout raise:", exc)
    check("a broken stdout is swallowed and the line is still in the events log",
          ok2 and any("stdout is dead" in ln for ln in events_lines(root / "events_broken_stdout.log")))

    # main(): the real startup/shutdown path against the fake lane, bounded to two sweeps
    print("-- [new] main() startup / shutdown lines")
    ev4 = root / "events_new_main.log"
    sup.EVENTS_LOG = ev4
    mode.write_text("ok")
    if not sup.is_healthy(PORT, 1.0, "/api/tags"):
        stop_hub(sup)
        sup.launch("fake_hub")
        wait_up(sup)
    real_sweep, real_interval, calls = sup.sweep, sup.CHECK_INTERVAL, {"n": 0}

    def limited(fc_):
        calls["n"] += 1
        r = real_sweep(fc_)
        if calls["n"] >= 2:
            raise KeyboardInterrupt
        return r

    sup.sweep, sup.CHECK_INTERVAL = limited, 0.2
    buf4 = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf4):
            sup.main()
    finally:
        sup.sweep, sup.CHECK_INTERVAL = real_sweep, real_interval
    lines4 = events_lines(ev4)
    check("main(): starting, config (pid + per-lane probe budgets + events log path), adopted, watchdog active, stopped watching",
          len(lines4) >= 5 and "starting" in lines4[0] and any(f"config: pid={os.getpid()} check_interval=0.2s" in ln and "probe_timeouts: fake_hub=1.0s" in ln for ln in lines4)
          and any("adopted already-healthy fake_hub" in ln for ln in lines4) and any("watchdog active" in ln for ln in lines4)
          and "stopped watching" in lines4[-1], "\n".join(lines4))
    check("main(): stdout still has the legacy lines, including the leading blank line before 'stopped watching'",
          "\n[supervisor] stopped watching (servers left running).\n" in buf4.getvalue() and "[supervisor] watchdog active" in buf4.getvalue())
    stop_hub(sup)


def baseline_equivalence(base_t: dict, new_t: dict) -> None:
    print("-- [same] restart semantics vs the baseline, same scenario")
    check("sweep() return values identical (healthy [], 1/2 [], 2/2 ['fake_hub'])",
          [base_t[k] for k in ("r1", "r2", "r3")] == [new_t[k] for k in ("r1", "r2", "r3")] == [[], [], ["fake_hub"]],
          f"{[base_t[k] for k in ('r1','r2','r3')]} vs {[new_t[k] for k in ('r1','r2','r3')]}")
    check("fail counts identical after each sweep (0, 1, 0)",
          [base_t[k] for k in ("c1", "c2", "c3")] == [new_t[k] for k in ("c1", "c2", "c3")] == [0, 1, 0])
    for t in (base_t, new_t):
        check(f"[{t['label']}] old pid killed, a different pid relaunched and healthy",
              t["h0_dead"] and t["h1_pid"] not in (None, t["h0_pid"]) and t["h1_healthy"],
              f"h0={t['h0_pid']} dead={t['h0_dead']} h1={t['h1_pid']} healthy={t['h1_healthy']}")
    bl, nl = legacy_lines(base_t["stdout"]), legacy_lines(new_t["stdout"])
    check("every line the baseline printed is still printed, same order, same text (modulo pids and the new suffix)",
          bl == nl and len(bl) == 6, f"\nbaseline: {bl}\nnew:      {nl}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--supervisor", default=str(HERE.parent / "supervisor.py"), help="supervisor.py under test")
    ap.add_argument("--baseline-rev", default=BASELINE_REV, help="git rev whose scripts/supervisor.py is the baseline")
    ap.add_argument("--keep", action="store_true", help="keep the temp dir")
    args = ap.parse_args()
    if port_listening(PORT):
        print(f"refusing to run: 127.0.0.1:{PORT} is already in use")
        return 2
    root = Path(tempfile.mkdtemp(prefix="supervisor_obs_test_"))
    print(f"temp dir: {root}\nsupervisor under test: {args.supervisor}")
    try:
        new, new_import = load_module(Path(args.supervisor), "new", root)
        base_src = None
        try:
            base_src = subprocess.run(["git", "show", f"{args.baseline_rev}:scripts/supervisor.py"], cwd=HERE.parent.parent,
                                      capture_output=True, check=True, timeout=30).stdout
        except Exception as exc:
            print(f"(baseline {args.baseline_rev} unavailable: {exc}; section B comparison skipped)")
        base = None
        if base_src is not None:
            bp = root / "baseline_supervisor.py"
            bp.write_bytes(base_src)
            base, _ = load_module(bp, "base", root)

        if base is not None:
            contract_checks(base, "baseline", root, new_features=False)
        contract_checks(new, "new", root, new_features=True)

        base_t = wedge_scenario(base, root, "baseline") if base is not None else None
        stop_hub(base) if base is not None else None
        new_t = wedge_scenario(new, root, "new")
        if base_t is not None:
            baseline_equivalence(base_t, new_t)
        guarded("new-feature checks", lambda: new_feature_checks(new, root, new_t))
    finally:
        kill_fake_hubs()
        if not args.keep:
            shutil.rmtree(root, ignore_errors=True)
    left = port_listening(PORT)
    check(f"port {PORT} is free again after the test (no fake hub left running)", not left)
    bad = [r for r in RESULTS if not r[1]]
    print(f"\n{len(RESULTS) - len(bad)} passed, {len(bad)} failed")
    for name, _, detail in bad:
        print(f"  FAILED: {name}  {detail}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
