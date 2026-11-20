"""
Nascence — Server Supervisor (launcher + watchdog)

Production watchdog for the LOCAL ollama lane AND the local CPU judge tier (2026-06-20; extended
2026-09-02, D-0127/J-0496, following F-0684's scope-gap finding — until then this file managed ONLY
local ollama, SERVERS had exactly one entry, and the CPU tier (:11439/:11440/:11442) got launched
once by scripts/launch_servers.ps1 but never auto-healed if a hub died mid-session, unlike hot_ollama.
That gap is also why Nascence_Control_Panel.ps1's [1] Full Start, which used to rely on
Start-Supervisor alone for "servers", could restart Du all night without the CPU tier ever coming up
— see F-0684/F-0685; Full-Start now also calls launch_servers.ps1 directly regardless of this file):
  HOT = ollama serving qwen3.5:9b on 11433 (Self, GPU-only, MAX_LOADED=1). Launched with OLLAMA_HOST +
  KEEP_ALIVE, health-checked via /api/tags, the Self model warmed after every (re)start.
  CPU TIER = Judge1 gemma4:12b (:11439), Judge2 falcon3:7b (:11440), Dreamer yi:34b-v1.5 (:11442) —
  llama.cpp hubs via nascence_cpu_server.py, blob-resolved via resolve_blob.py, mirroring
  launch_servers.ps1's own $tier array (kept in explicit lockstep, see _CPU_TIER below — same
  duplicate-literal-drift risk this project was just burned by with the memory-store split, D-0126).
  Their logs go where launch_servers.ps1 puts them — data/logs/cpu_tier_<port>.log (+ .log.err), via
  the hub's own --log — not data/ (fixed 2026-09-03, J-0520; see CPU_LOGDIR).
  Health = /api/tags, which nascence_cpu_server.py answers from a static in-memory constant and never
  touches the lazy-loaded model object — an idle-unloaded hub still reads as healthy, so this can't
  false-restart a hub that's merely quiet. NOT warmed after (re)start (unlike hot_ollama) — these hubs
  are deliberately --lazy/--idle-unload by launch_servers.ps1's own RAM-budget design; forcing them
  resident here would fight that on purpose.
  Both classes: adopts an already-healthy lane; restarts a dead/hung one after 2 consecutive failed
  checks. The CPU hubs get a longer per-check timeout (CPU_HEALTH_TIMEOUT, 2026-09-11 J-0836/D-0194);
  the hot lane's probe is two-phase since 2026-10-15 (J-2113/D-0420 B: connect 3.0 s, read HOT_READ_TIMEOUT
  10 s) and slow-but-passing / 1/2 lines carry a bounded host snapshot (D-0420 D)
  so a merely-slow hub is never mistaken for a wedged one. The Ramses background/subconscious lane (command-r7b :11441) and the retired Bonsai :11460
  lane are still NOT managed here — Ramses is a separate machine this process cannot launch, and
  Bonsai is dead weight (see REVERT note below).

  OBSERVABILITY (2026-10-03, J-1688 from F-2280/F-2279): every [supervisor] line is ALSO appended,
  ISO-timestamped, to data/logs/supervisor_events.log (append-only, size-capped; it survives supervisor
  restarts, unlike data/supervisor.log which the Control Panel's redirect overwrites on every start and
  whose lines carry no timestamps). A failed probe logs its timeout budget, measured elapsed time and
  exception class; a restart logs a host snapshot just before the kill and its outcome after; one summary
  line per hour (probe max/p99 per lane, probes over 2 s, sweeps, pid). LOG-ONLY: nothing here feeds a
  decision, and no timeout, interval, 2-consecutive-fail rule or launch/restart step depends on any of it.

  WHY the hot lane is watched: on 2026-06-10 ollama simply wasn't running and Du silently
  degraded onto the 1-bit CPU fallback — the failover masked a dead GPU lane. The watchdog's
  job is to make that state impossible to sustain. Same logic now applies to the CPU tier: a
  silently-dead Judge hub degrades judge_panel.py's panel to single-judge-unavailable without
  anyone noticing until they go looking (D-0127's own defeater names the failure mode to watch for).

This is the reliability spine: combined with the GPU→CPU failover in model_client,
a crashed GPU server is both (a) routed around immediately by live thought cycles, and
(b) brought back automatically here — so a days-long run survives a server death.

Run in its own terminal:  python scripts/supervisor.py
Stop with Ctrl+C (leaves the servers running; pass --stop-all to also kill them).
"""

import datetime
import json
import math
import os
import subprocess
import sys
import time
import urllib.error
import http.client
import urllib.error
import urllib.request
from pathlib import Path

try:
    import psutil
except ImportError:
    psutil = None

try:
    # line_buffering=True (2026-09-02, found while verifying D-0127 live): without it, stdout
    # redirected to a file (as Start-Supervisor/Nascence_Control_Panel.ps1 does) is FULLY buffered,
    # not line-buffered — every [supervisor] print(), including real restart activity, sat invisible
    # in an internal buffer well past when it happened (confirmed: killed the dreamer hub, watched
    # it get relaunched in ~20s via port polling, and data\supervisor.log was STILL empty). This
    # only affects when output appears in the log file, not the watchdog's actual behavior.
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
except Exception:
    pass

FRESHSTART = Path(r"C:\FreshStart\swarm")
CUDA_BIN   = FRESHSTART / "bin_cuda" / "llama-server.exe"   # PrismML CUDA fork (GPU)
CPU_BIN    = FRESHSTART / "bin"      / "llama-server.exe"   # CPU-only build
Q2_MODEL   = FRESHSTART / "models"   / "Ternary-Bonsai-8B-Q2_0.gguf"
Q1_MODEL   = FRESHSTART / "models"   / "Bonsai-8B-Q1_0.gguf"
LOGDIR     = Path(__file__).parent.parent / "data"          # supervisor-owned lanes (hot_ollama)
# CPU-tier hub logs live in data/logs/, NOT data/ (2026-09-03, J-0520 from F-0704): launch_servers.ps1
# ($LOGDIR = data\logs) and Nascence_Control_Panel.ps1's Full-Start message ("check data\logs\
# cpu_tier_*.log.err") both already used data/logs; the supervisor alone wrote data/cpu_tier_<port>.log,
# so the SAME hub logged to two places depending on who launched it. One location now:
#   data/logs/cpu_tier_<port>.log      the hub's own prints (via --log, line-buffered — see _cpu_hub_spec)
#   data/logs/cpu_tier_<port>.log.err  native-level stderr/stdout (llama.cpp / ggml, uvicorn tracebacks)
CPU_LOGDIR = LOGDIR / "logs"
CPU_HUB    = Path(__file__).parent / "nascence_cpu_server.py"
RESOLVE_BLOB = Path(__file__).parent / "resolve_blob.py"

CHECK_INTERVAL = 15   # seconds between health sweeps
BOOT_GRACE     = 90   # seconds to allow a freshly launched server to load
HEALTH_TIMEOUT = 3.0  # per-check HTTP timeout, the value every lane used until 2026-09-11 (hot_ollama keeps it)
# CPU_HEALTH_TIMEOUT (2026-09-11, J-0836 / D-0194): a per-spec override for the three CPU hubs. D-0194's
# defeater is a false-positive kill of a hub that is merely slow (mid yi:34b load, mid 90s+ chat). The
# mechanism already protects against that — nascence_cpu_server.py's /api/tags is an async handler that
# never takes the generation lock, and both model load and inference run in an executor thread, so the
# event loop keeps answering — and the live evidence agrees: the supervisor run started 2026-09-09 13:24
# polled every 15 s at 3.0 s through 241 model loads (max 124 s) and 2,045 chats (max 522.6 s) in ~47 h with
# ZERO "health check failed" lines in data/supervisor.log (F-1248). A generous timeout here is belt-and-braces
# for the case that evidence cannot cover — a host so CPU/IO-saturated (three hubs loading at once on a
# 64 GB box) that the loop thread itself is starved for seconds. Cost: a truly wedged hub delays one sweep
# by this much before its (still 2-consecutive-fails) restart; that is 10 s on a 15 s cadence, acceptable.
CPU_HEALTH_TIMEOUT = 10.0
# HOT_READ_TIMEOUT (2026-10-15, J-2113 / D-0420 B, travis): the hot lane's probe is split into two phases. The
# CONNECT phase keeps HEALTH_TIMEOUT (3.0 s): a dead process (refused) or a dead port is still detected in about
# 2 s, so the 2026-10-08 08:47 tray-quit recovery is unchanged. The READ phase (connected, request sent, waiting
# for /api/tags to answer) gets this budget instead, mirroring D-0194's CPU-hub budget. Why: F-2740's 217 h read
# found zero wedge kills and zero false kills, but three isolated read-phase probes that crossed 3.0 s (ollama
# answered 200 at 2.995 s and 3.081 s during a 13.5 min idle slowdown on 10-08, cause unknown); the 2-consecutive
# rule absorbed them, and two back to back would have killed a live ollama. Cost: a true wedge is detected one
# sweep later (~35-50 s instead of ~33 s). The 2-consecutive-fail rule is unchanged. Read at start: a running
# supervisor keeps the constants it started with.
HOT_READ_TIMEOUT = 10.0

# ── Observability (2026-10-03, J-1688 from F-2280 / F-2279) ─────────────────────────────────────────
# WHY: the one watchdog kill in ~351 h of supervision (hot_ollama, 2026-09-30 ~10:15:26, during Du's
# farewell quit-sleep) could not be classified as a true wedge vs an IO/CPU-starved-but-alive ollama:
# data\supervisor.log lines carry no timestamps, Nascence_Control_Panel.ps1's Start-Supervisor redirect
# OVERWRITES that file on every supervisor start, and a failed probe was logged with no latency, exception
# class or host context. Everything in this block is LOG-ONLY. It never feeds a decision, and every helper
# swallows its own exceptions (sweep()/restart() call them through _obs() or guarded wrappers), so a bug or
# a full disk in here cannot change what the watchdog does. is_healthy()/lane_healthy() keep their exact
# bool contracts; the probe diagnostics ride along in the _last_probe side channel that only sweep()'s
# log lines read.
EVENTS_LOG = CPU_LOGDIR / "supervisor_events.log"   # data/logs/supervisor_events.log: ISO-timestamped, append-only
EVENTS_LOG_MAX_BYTES = 5 * 1024 * 1024  # rotate to supervisor_events.log.1 (one generation kept) past this size
SLOW_PROBE_S = 2.0           # a probe slower than this is "slow": counted in the hourly line, and logged on its own if it still passed
SLOW_LINES_PER_WINDOW = 20   # per-lane cap on individual slow-but-passing lines per summary window (the count is always kept)
SUMMARY_INTERVAL_S = 3600    # one summary line per this many seconds (monotonic clock, so DST/clock jumps do not matter)
SNAPSHOT_WINDOW_S = 1.0      # length of the host sample taken just before a restart's kill
SNAPSHOT_PASS_BUDGET_S = 0.75  # hard deadline for each of the snapshot's two per-process passes (see _host_snapshot)
# J-2113 / D-0420 D (2026-10-15): the host snapshot also rides (a) slow-but-passing probe lines and (b) the 1/2
# failure line, not only the pre-kill line, so the next idle slowdown names its cause (F-2740 could not: no host
# sample existed for the 10-08 00:23-00:37 window). Log-only, bounded: a shorter sample window than the pre-kill
# one, and at most SLOW_SNAPSHOT_LINES_PER_WINDOW snapshot-carrying slow lines per lane per summary window (the
# slow line itself is still written without the snapshot past the cap). The 2/2 line is not snapshotted here
# because restart() takes the full pre-kill snapshot a moment later.
SLOW_SNAPSHOT_WINDOW_S = 0.5
SLOW_SNAPSHOT_LINES_PER_WINDOW = 5

# J-3979 / D-0761 (travis 2026-11-14, from F-4615): a probe TIMEOUT while the box has under HOST_STARVED_RAM_GB of
# available RAM means "host starved, not wedged" (11-07 08:09 false hot_ollama restart; ram_avail 0.2-1.4 GB in 23 of
# 43 hot snapshots). Such a failure is logged but does NOT increment the 2-consecutive-fail counter. Only a
# READ-phase timeout (connected, no answer) is excused (connect timeouts, refused / reset / http errors still count), and only while psutil can read RAM. Safety cap
# (an addition to the ruling): after HOST_STARVED_MAX_SKIPS excused checks in a row for one lane, failures count
# normally again so a genuinely wedged lane on a permanently starved box still gets restarted.
HOST_STARVED_RAM_GB = 2.0
HOST_STARVED_MAX_SKIPS = 8

_last_probe: dict[int, dict] = {}    # port -> {timeout, elapsed, err, exc} of the most recent is_healthy() call
_boot_secs: dict[str, float] = {}    # lane -> seconds from wait_healthy() start to its first healthy probe

# ── Scheduled disk reclaim (2026-10-06, D-0242 re-ruling / J-1833) ───────────────────────────────────
# WHY here: D-0242 (travis, 2026-10-06) ruled "automate the reclaim, no manual step" after the 7-day read
# F-2320 found C: at 78.69 GiB free and falling 5.16 GiB/day with scripts/retention.py's labs class last
# applied by hand on 2026-09-09 (133 candidates / 54.70 GB waiting on 10-06). The briefing left the vehicle
# open -- Task Scheduler or this supervisor's own tick -- with one hard rule: it must not be launched from a
# Claude Code job object (CLAUDE.md, F-0704). This process already satisfies that by construction (it is
# started by the Control Panel or scripts/start_supervisor_detached.ps1's WMI launch, never by a job-run
# agent), already runs for days, and needs no registration step that would itself be a manual step. So:
# a daemon thread, separate from the 15 s watchdog loop (the labs apply + trash purge can take minutes on
# tens of GB and must never delay a health sweep), runs once RETENTION_TICK_FIRST_DELAY_S after start and
# then every RETENTION_TICK_INTERVAL_S. Each run: (1) retention.scheduled_run() -- labs class quarantine
# per the D-0156 age rule + purge of data/_trash day-dirs older than TRASH_DAYS; (2) lab_sweep.boot_report()
# -- the D-0242 locked-copy sweeper, so a Du that stays up for days still gets swept. Both are flag-gated in
# their own modules (RETENTION_SCHEDULED_LABS, LAB_SWEEP_BOOT_APPLY), both never raise, both refuse any path
# outside data/_lab + data/_trash (+ the two backup roots retention.py has always owned); data/_hold is never
# in scope. Everything here is wrapped so a failure cannot touch the watchdog. RETENTION_TICK_ENABLED=False
# turns the whole thread off.
RETENTION_TICK_ENABLED = True
RETENTION_TICK_FIRST_DELAY_S = 10 * 60          # let the hubs finish loading before the first disk pass
RETENTION_TICK_INTERVAL_S = 24 * 60 * 60        # once a day thereafter
_retention_runs: list[dict] = []                # most recent tick summaries (kept short; log-only)


def _iso_now() -> str:
    return datetime.datetime.now().astimezone().isoformat(timespec="milliseconds")


def _append_event(msg: str) -> None:
    """Append `msg` with an ISO timestamp to EVENTS_LOG, rotating to <name>.1 once it passes
    EVENTS_LOG_MAX_BYTES. Any failure (disk full, a viewer holding the file, a bad path) is swallowed."""
    try:
        path = Path(EVENTS_LOG)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            if path.stat().st_size >= EVENTS_LOG_MAX_BYTES:
                os.replace(path, path.with_name(path.name + ".1"))
        except OSError:
            pass   # no file yet, or the rotation was refused: just keep appending
        line = msg.strip().replace("\r", " ").replace("\n", " | ")
        with open(path, "a", encoding="utf-8", errors="replace") as f:
            f.write(f"{_iso_now()} {line}\n")
    except Exception:
        pass


def _log(msg: str) -> None:
    """The one way this file reports anything. The line goes to stdout exactly as the old print() calls did
    (the Control Panel redirects stdout to data\\supervisor.log) AND, timestamped, to the append-only
    EVENTS_LOG. The events log is written first, and a broken stdout (a dead launcher's pipe) is swallowed:
    the line is already in the events log, and neither may ever take the watchdog down."""
    _append_event(msg)
    try:
        print(msg)
    except Exception:
        pass


def _obs(fn, *args) -> None:
    """Run an observability helper; whatever it does, it must never reach the watchdog loop."""
    try:
        fn(*args)
    except Exception:
        pass


def _probe_error(exc: BaseException) -> tuple[str, str, str]:
    """(category, phase, exception-class text) for a failed probe. Category: timeout / refused / reset /
    http_<code> / other. Phase is only set for a timeout: urllib wraps a connect/send-phase failure in
    URLError and lets a read-phase timeout through bare, so URLError(TimeoutError) = no TCP connect completed
    in time (a dead port, or a full accept queue) and a bare TimeoutError = connected, request sent, no answer
    (a wedged or starved server). That is the wedge-vs-dead distinction F-2280 could not make."""
    inner = getattr(exc, "reason", None)          # URLError wraps the socket-level exception in .reason
    if not isinstance(inner, BaseException):
        inner = exc
    cls = type(exc).__name__ if inner is exc else f"{type(exc).__name__}({type(inner).__name__})"
    if isinstance(exc, urllib.error.HTTPError):
        return f"http_{exc.code}", "", cls
    if isinstance(inner, TimeoutError):           # socket.timeout is TimeoutError since 3.10
        return "timeout", ("read" if inner is exc else "connect"), cls
    if isinstance(inner, ConnectionRefusedError):
        return "refused", "", cls
    if isinstance(inner, ConnectionError):        # reset / aborted / RemoteDisconnected
        return "reset", "", cls
    return "other", "", cls


def _note_probe(port: int, timeout: float, elapsed: float, ok: bool, status, exc,
                connect_timeout: float | None = None) -> None:
    """Remember how the latest probe of `port` went, for sweep()'s log lines. Never raises. `timeout` is the budget
    that governed the probe (for a two-phase probe: the READ budget, or the CONNECT budget when the connect phase is
    what failed); `connect_timeout` is set only for a two-phase probe (J-2113), so the line can show both."""
    try:
        if ok:
            err, phase, cls = "", "", ""
        elif exc is not None:
            err, phase, cls = _probe_error(exc)
        elif status is not None:
            err, phase, cls = f"http_{status}", "", ""
        else:
            err, phase, cls = "other", "", ""
        # two-phase probe: every connect-phase failure arrives URLError-wrapped (refused, reset, connect timeout);
        # a read-phase failure is bare. So the wrapper, not the category, says which budget governed it.
        if connect_timeout is not None and exc is not None and isinstance(exc, urllib.error.URLError)                 and not isinstance(exc, urllib.error.HTTPError):
            timeout = connect_timeout
        _last_probe[port] = {"timeout": timeout, "elapsed": elapsed, "err": err, "phase": phase, "exc": cls,
                             "connect_timeout": connect_timeout}
    except Exception:
        pass


def _probe_detail(spec: dict) -> str:
    """' | timeout=3.0s elapsed=3.003s err=timeout phase=read exc=TimeoutError' for the lane's latest probe, or ''."""
    try:
        info = _last_probe.get(spec["port"])
        if not info:
            return ""
        return (f" | timeout={float(info['timeout'])!r}s elapsed={info['elapsed']:.3f}s err={info['err']}"
                + (f" phase={info['phase']}" if info["phase"] else "")
                + (f" exc={info['exc']}" if info["exc"] else "")
                + (f" connect_timeout={float(info['connect_timeout'])!r}s" if info.get("connect_timeout") is not None else ""))
    except Exception:
        return ""


def _host_snapshot(window: float = SNAPSHOT_WINDOW_S, top_n: int = 3) -> str:
    """One line on what the HOST is doing, sampled over `window` seconds: whole-box CPU %, available RAM,
    system-wide disk read/write MB/s, and the top-N processes by CPU (% of the whole box) and by IO bytes/s.
    Taken just before a restart kills anything, to tell a wedged server (idle host) from a starved one
    (busy host). Costs ~`window` seconds, and is bounded: the per-process part only samples processes running
    as OUR user (measured on this box, 2026-10-03: psutil reads those in ~0.03 ms each, while a service /
    other-user process falls back to a 10-100 ms path, ~7 s for the whole table), with a hard deadline per
    pass, and says how many it sampled. Never raises."""
    try:
        if psutil is None:
            return "unavailable (psutil not installed)"
        ncpu = psutil.cpu_count() or 1
        try:
            me = psutil.Process().username()
        except Exception:
            me = None
        psutil.cpu_percent(None)            # prime the system-wide counters first: both windows start together
        d0 = psutil.disk_io_counters()
        t_start = time.perf_counter()
        primed = []                         # (Process, io_counters-or-None) read before the window
        deadline = t_start + SNAPSHOT_PASS_BUDGET_S
        for p in psutil.process_iter():
            if time.perf_counter() > deadline:
                break
            try:
                if me is not None and p.username() != me:
                    continue
                p.cpu_percent(None)         # prime: the next call reports usage since this one
            except Exception:
                continue
            try:
                io0 = p.io_counters()
            except Exception:
                io0 = None
            primed.append((p, io0))
        time.sleep(max(0.0, window - (time.perf_counter() - t_start)))   # the window includes the prime pass
        dt = max(time.perf_counter() - t_start, 1e-6)
        cpu = psutil.cpu_percent(None)
        d1 = psutil.disk_io_counters()
        vm = psutil.virtual_memory()
        rows = []                           # (Process, cpu % of the whole box, io bytes/s or None)
        deadline = time.perf_counter() + SNAPSHOT_PASS_BUDGET_S
        for p, io0 in primed:
            if time.perf_counter() > deadline:
                break
            try:
                c = p.cpu_percent(None) / ncpu
            except Exception:
                continue
            io = None
            if io0 is not None:
                try:
                    io1 = p.io_counters()
                    io = ((io1.read_bytes + io1.write_bytes) - (io0.read_bytes + io0.write_bytes)) / dt
                except Exception:
                    io = None
            try:
                rss = p.memory_info().rss
            except Exception:
                rss = None
            rows.append((p, c, io, rss))

        def label(p) -> str:
            try:
                return f"{p.name()}/{p.pid}"
            except Exception:
                return f"?/{p.pid}"

        def label_ex(p) -> str:
            # J-4013 (F-4698): python entries also name the script basename and --port, so a RAM-starved
            # cluster names its consumer (e.g. python.exe/6948 cpu_server.py:11442). Additive, never raises.
            base = label(p)
            try:
                if not p.name().lower().startswith("python"):
                    return base
                args = p.cmdline()[1:]
                script = next((os.path.basename(a) for a in args if a.lower().endswith(".py")), None)
                port = None
                for i, a in enumerate(args):
                    if a == "--port" and i + 1 < len(args):
                        port = args[i + 1]
                    elif a.startswith("--port="):
                        port = a.split("=", 1)[1]
                extra = (script or "") + (f":{port}" if port else "")
                return f"{base}[{extra}]" if extra else base
            except Exception:
                return base

        rows = [r for r in rows if r[0].pid != 0]          # pid 0 is the System Idle Process
        by_cpu = sorted(rows, key=lambda r: r[1], reverse=True)[:top_n]
        by_io = sorted((r for r in rows if r[2] is not None), key=lambda r: r[2], reverse=True)[:top_n]
        by_rss = sorted((r for r in rows if r[3] is not None), key=lambda r: r[3], reverse=True)[:top_n]
        mb = 1024 * 1024
        if d0 is None or d1 is None:
            disk = "disk=n/a"
        else:
            disk = (f"disk_read={(d1.read_bytes - d0.read_bytes) / dt / mb:.1f}MB/s "
                    f"disk_write={(d1.write_bytes - d0.write_bytes) / dt / mb:.1f}MB/s")
        return (f"cpu={cpu:.0f}% ({ncpu} logical) ram_avail={vm.available / 2**30:.1f}/{vm.total / 2**30:.1f}GB "
                f"{disk} sample={dt:.1f}s procs_sampled={len(rows)}/{len(psutil.pids())}"
                f"({'own-user only' if me is not None else 'all, deadline-bounded'}) "
                f"top_cpu(%box)=[{', '.join(f'{label_ex(p)}={c:.1f}%' for p, c, _, _r in by_cpu)}] "
                f"top_io=[{', '.join(f'{label_ex(p)}={io / mb:.1f}MB/s' for p, _, io, _r in by_io)}] "
                f"top_rss=[{', '.join(f'{label_ex(p)}={r / 2**30:.2f}GB' for p, _, _i, r in by_rss)}]")
    except Exception as exc:
        return f"unavailable ({type(exc).__name__}: {exc})"


class _SweepStats:
    """Probe statistics for one summary window (default an hour). Log-only; sweep() reaches it via _obs()."""

    def __init__(self) -> None:
        self._prev_end = None
        self.reset()

    def reset(self) -> None:
        self.t0 = time.monotonic()
        self.sweeps = 0
        self.late_max = 0.0                          # worst overshoot of the loop's own sleep(CHECK_INTERVAL)
        self.lat: dict[str, list[float]] = {}        # lane -> probe elapsed seconds (every probe, pass or fail)
        self.failed: dict[str, int] = {}             # lane -> failed probes
        self.slow: dict[str, int] = {}               # lane -> probes above SLOW_PROBE_S (pass or fail)
        self.slow_lines: dict[str, int] = {}         # lane -> individual slow-but-passing lines written
        self.snap_lines: dict[str, int] = {}         # J-2113: lane -> slow lines that carried a host snapshot this window

    def sweep_started(self) -> None:
        now = time.monotonic()
        if self._prev_end is not None:
            self.late_max = max(self.late_max, now - self._prev_end - CHECK_INTERVAL)
        self.sweeps += 1

    def sweep_ended(self) -> None:
        self._prev_end = time.monotonic()

    def record(self, name: str, elapsed: float, ok: bool) -> bool:
        """Count one probe. True when a slow-but-passing probe should also get its own log line (capped)."""
        self.lat.setdefault(name, []).append(elapsed)
        if not ok:
            self.failed[name] = self.failed.get(name, 0) + 1
        if elapsed <= SLOW_PROBE_S:
            return False
        self.slow[name] = self.slow.get(name, 0) + 1
        if not ok or self.slow_lines.get(name, 0) >= SLOW_LINES_PER_WINDOW:
            return False
        self.slow_lines[name] = self.slow_lines.get(name, 0) + 1
        return True

    def take_snapshot_slot(self, name: str) -> bool:
        """J-2113 / D-0420 D: True while this lane has snapshot-carrying slow lines left in the window."""
        if self.snap_lines.get(name, 0) >= SLOW_SNAPSHOT_LINES_PER_WINDOW:
            return False
        self.snap_lines[name] = self.snap_lines.get(name, 0) + 1
        return True

    def summary_line(self) -> str:
        parts = []
        for name, lat in self.lat.items():
            s = sorted(lat)
            p99 = s[min(len(s) - 1, math.ceil(0.99 * len(s)) - 1)]
            parts.append(f"{name} n={len(s)} max={s[-1]:.3f}s p99={p99:.3f}s "
                         f">{SLOW_PROBE_S:g}s={self.slow.get(name, 0)} failed={self.failed.get(name, 0)}")
        return (f"[supervisor] hourly summary: pid={os.getpid()} window={time.monotonic() - self.t0:.0f}s "
                f"sweeps={self.sweeps} late_max={self.late_max:.1f}s | " + " | ".join(parts))

    def maybe_emit_summary(self) -> None:
        if time.monotonic() - self.t0 >= SUMMARY_INTERVAL_S:
            _log(self.summary_line())
            self.reset()


_stats = _SweepStats()


def _record_probe(name: str, spec: dict, ok: bool) -> None:
    """Feed the lane's latest probe into the summary stats; a slow-but-passing one also gets its own line."""
    info = _last_probe.get(spec["port"])
    if info is None:        # lane_healthy() was replaced/stubbed: nothing measured, nothing to record
        return
    if _stats.record(name, info["elapsed"], ok):
        snap = ""
        try:   # J-2113 / D-0420 D: the host at the moment of a slow pass, bounded per lane per window
            if _stats.take_snapshot_slot(name):
                snap = f" | host: {_host_snapshot(SLOW_SNAPSHOT_WINDOW_S)}"
        except Exception:
            snap = ""
        _log(f"[supervisor] {name} probe slow but passed on port {spec['port']}" + _probe_detail(spec) + snap)


def _fail_snapshot_detail() -> str:
    """J-2113 / D-0420 D: ' | host: ...' for the 1/2 failure line. Never raises (returns '')."""
    try:
        return f" | host: {_host_snapshot(SLOW_SNAPSHOT_WINDOW_S)}"
    except Exception:
        return ""


def _log_config() -> None:
    """One startup line saying which supervisor (pid) runs with which probe budgets, so a later reader never
    has to reconstruct which timeouts were live (F-2279 had to)."""
    budgets = ", ".join(f"{n}={float(s.get('health_timeout', HEALTH_TIMEOUT))!r}s"
                        + (f"(read {float(s['read_timeout'])!r}s)" if s.get("read_timeout") is not None else "")
                        for n, s in SERVERS.items())
    _log(f"[supervisor] config: pid={os.getpid()} check_interval={CHECK_INTERVAL}s boot_grace={BOOT_GRACE}s "
         f"probe_timeouts: {budgets} events_log={EVENTS_LOG}")


def _log_restart_outcome(name: str, healthy: bool, own_pid, killed_pids: list, t_kill: float,
                         t_launch: float) -> None:
    """After a restart: which pids were killed, the new pid, and how long the lane was down."""
    t_end = time.perf_counter()
    boot = _boot_secs.get(name)
    if healthy and boot is not None:
        timing = (f"secs_to_healthy={(t_launch - t_kill) + boot:.1f} (kill->launch {t_launch - t_kill:.1f}s + "
                  f"boot {boot:.1f}s) warm={t_end - t_launch - boot:.1f}s")
    else:
        timing = f"secs_to_healthy=n/a (not healthy after {t_end - t_launch:.1f}s)"
    proc = _procs.get(name)
    _log(f"[supervisor] {name} restart outcome: healthy={healthy} {timing} killed_pids={killed_pids} "
         f"own_handle_pid={own_pid} relaunch_pid={proc.pid if proc else None}")

# ── Server specs ──────────────────────────────────────────────────────────────
# HOT lane = ollama (gemma4:e4b + num_ctx 32768). NOT a llama-server: launched as
# "ollama serve" with OLLAMA_HOST pinned to 11433 (NOT the default 11434) and KEEP_ALIVE so the
# model is not unloaded between turns. Health = /api/tags. After every (re)start the model is
# warmed so Du's first cycle is not a cold load. The old Bonsai-Q2 CUDA lane (11470) is dead —
# do not resurrect it; it fights the hot model for VRAM.
HOT_MODEL = "qwen3.5:9b"   # FULL SHUFFLE 2026-08-20 (station_matrix.md #10; was gemma4:e4b). Found stale
                           # 2026-08-21: the supervisor kept warming gemma onto the 1080 Ti alongside qwen —
                           # half of the double-load incident. Keep in lockstep with launch_servers.ps1
                           # $SELF_MODEL; that file is the single source of truth for what serves where.

# The watchdog only manages the LOCAL ollama now. STALE UNTIL 2026-09-02 (F-0684): this used to say
# the DREAMER ran locally on this same ollama and the SUBCONSCIOUS was phi3 on Ramses :11434 — both
# describe the pre-08-15-split architecture. Since the split: SUBCONSCIOUS is command-r7b on RAMSES
# :11441 (:11434 retired 2026-08-28, D-0056; if Ramses naps the code-level fallback routes it to the
# local lane, core/schema.SERVE_CHAINS["background"]) and the DREAMER is yi:34b-v1.5 on its own
# llama.cpp hub (local :11442, lazy, launch_servers.ps1) — neither is local-ollama traffic, so
# neither is this watchdog's concern any more than Judge1/Judge2 are. The old CPU Bonsai-Q1 lane
# (:11460) is RETIRED.
# REVERT: set HOT_MODEL="qwen3-du" and re-add :11460 (see git).
SERVERS = {
    "hot_ollama": {
        "port": 11433,
        "bin":  "ollama",
        "cwd":  None,
        "args": ["serve"],
        "log":  "server_hot_ollama",
        # 2026-08-21: MAX_LOADED/KEEP_ALIVE added — a supervisor-relaunched ollama previously lacked
        # them (launch_servers.ps1 sets them), so two models could co-load on the 1080 Ti.
        "env":  {"OLLAMA_HOST": "127.0.0.1:11433",
                 "OLLAMA_MAX_LOADED_MODELS": "1",
                 "OLLAMA_KEEP_ALIVE": "2h"},
        "health_path": "/api/tags",
        "health_timeout": HEALTH_TIMEOUT,     # the CONNECT-phase budget (3.0 s): a dead process is still caught fast
        "read_timeout": HOT_READ_TIMEOUT,     # J-2113 / D-0420 B: the READ-phase budget (10.0 s) for a slow-but-alive ollama
        "proc_match": "ollama",
        "warm_model": HOT_MODEL,
    },
}

# ── CPU judge tier (2026-09-02, D-0127/J-0496) ─────────────────────────────────
# KEEP IN LOCKSTEP WITH scripts/launch_servers.ps1's $tier array — this is a second, necessarily
# duplicated copy (PowerShell vs Python) of the same 3-hub topology. That duplication is exactly
# the class of bug D-0126 found and fixed for the memory-store path; there is no cross-language
# single-source-of-truth available here, so the discipline is a comment, not code — if you change
# one, change the other. Ports/models/threads/idle-unload values verified against launch_servers.ps1
# as of 2026-09-02. The lockstep also covers HOW a hub is launched, not just what: launch_servers.ps1
# passes --ctx 8192 and --log data\logs\cpu_tier_<port>.log; _cpu_hub_spec() below passes the same
# (the --log half was missing until 2026-09-03, J-0520 — see CPU_LOGDIR and _cpu_hub_spec).
_CPU_TIER = [
    # (server key, Model, Tag, Alias, port, threads, idle_unload_seconds)
    ("judge1_hub", "gemma4", "12b",     "gemma4:12b",     11439, 14, 300),
    ("judge2_hub", "falcon3", "7b",     "falcon3:7b",     11440, 14, 300),
    ("dreamer_hub", "yi",    "34b-v1.5", "yi:34b-v1.5",   11442, 20, 60),
    # D-0539 / J-3147 (2026-11-06): the Emissary's per-turn take gets its OWN RESIDENT hub (idle_unload 0 = no --lazy,
    # loaded at startup, never unloaded): on the lazy shared hubs a take paid a cold model load (16 of 27) and queued
    # behind judge calls on the hub's one generation lock, so a median 77 s missed the orchestrator's 6 s wait
    # (F-3545). Same model as judge2 on purpose (its JSON contract is proven on this platform) but a SEPARATE process
    # so the two never share a lock; ~5 GB resident RAM. core/left_lane.py TAKE_URL points here.
    ("take_hub", "falcon3", "7b", "falcon3:7b", 11445, 16, 0),
]


def _resolve_blob(model: str, tag: str) -> str | None:
    """python resolve_blob.py <model> <tag> -> the blob path it prints, or None on failure (missing
    manifest, model never pulled, etc.) — same contract launch_servers.ps1 relies on."""
    try:
        r = subprocess.run([sys.executable, str(RESOLVE_BLOB), model, tag],
                           capture_output=True, text=True, timeout=15)
        blob = r.stdout.strip()
        return blob or None
    except Exception:
        return None


def _cpu_hub_spec(model: str, tag: str, alias: str, port: int, threads: int,
                  idle_unload: int) -> dict | None:
    """Build a SERVERS-compatible spec for one CPU-tier hub, or None if its blob can't be resolved
    (mirrors launch_servers.ps1's own "no blob for X - is it pulled in ollama?" skip-with-warning,
    rather than crashing the whole watchdog over one unpulled model)."""
    blob = _resolve_blob(model, tag)
    if blob is None:
        _log(f"[supervisor] WARNING: no blob for {alias} ({model}:{tag}) — is it pulled in ollama? "
             f"Skipping this hub; the watchdog will not manage or restart it.")
        return None
    hub_log = CPU_LOGDIR / f"cpu_tier_{port}.log"
    return {
        "port": port,
        "bin": sys.executable,
        "cwd": None,
        # --log <file> (2026-09-03, J-0520 from F-0704): launch_servers.ps1 has always passed it; this
        # spec did not. Without it nascence_cpu_server.py's own prints ("[cpu-tier] ... loaded",
        # "[chat] ...") went to the Popen-redirected stdout, which Python BLOCK-buffers when it is a
        # file — data/cpu_tier_11439.log was 0 bytes after a completed real /api/chat while the .err
        # side (native llama.cpp stderr, unbuffered) had content. --log makes the hub open its log
        # itself with buffering=1 (line-buffered), same as launch_servers.ps1's hubs.
        "args": [str(CPU_HUB), "--model", blob, "--alias", alias, "--port", str(port),
                "--threads", str(threads), "--ctx", "8192",
                *(["--lazy", "--idle-unload", str(idle_unload)] if idle_unload > 0 else []),
                "--log", str(hub_log)],
        "log": f"cpu_tier_{port}",
        "logdir": CPU_LOGDIR,
        # With --log owning the hub's Python-level output, what still reaches the Popen handles is
        # native-level only (ggml/llama.cpp stderr, asyncio/uvicorn tracebacks) — one file for both
        # fds, named as launch_servers.ps1's WARN and the Control Panel's Full-Start message expect.
        "stdout_file": f"cpu_tier_{port}.log.err",
        "stderr_file": f"cpu_tier_{port}.log.err",
        "env": {},
        "health_path": "/api/tags",
        "health_timeout": CPU_HEALTH_TIMEOUT,   # D-0194 (J-0836): tolerate a merely-slow hub, see constant
        "proc_match": "python",
        # No warm_model, deliberately: these hubs are --lazy by design (RAM budget), forcing a load
        # at every supervisor (re)start would fight that on purpose. See module docstring.
    }


for _key, _model, _tag, _alias, _port, _threads, _idle in _CPU_TIER:
    _spec = _cpu_hub_spec(_model, _tag, _alias, _port, _threads, _idle)
    if _spec is not None:
        SERVERS[_key] = _spec
del _key, _model, _tag, _alias, _port, _threads, _idle, _spec

_procs: dict[str, subprocess.Popen] = {}


def is_healthy(port: int, timeout: float = HEALTH_TIMEOUT, path: str = "/health",
               read_timeout: float | None = None) -> bool:
    # Same contract as ever (True only for an HTTP 200, any exception -> False). J-1688's one addition is
    # _note_probe(): how long the probe took and why it failed, for sweep()'s log lines.
    # J-2113 / D-0420 B: with `read_timeout` set (the hot lane), the probe is TWO-PHASE: `timeout` bounds the TCP
    # connect (a dead process/port still fails fast), `read_timeout` bounds the wait for the answer. A connect-phase
    # failure is wrapped in URLError exactly as urllib does, so _probe_error() keeps classifying it phase=connect;
    # a read-phase timeout stays a bare TimeoutError (phase=read). Without `read_timeout` nothing changes.
    t0 = time.perf_counter()
    ok, status, err = False, None, None
    if read_timeout is None or read_timeout <= timeout:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=timeout) as r:
                status = r.status
                ok = status == 200
        except Exception as exc:
            ok, err = False, exc
        _note_probe(port, timeout, time.perf_counter() - t0, ok, status, err)
        return ok
    conn = None
    try:
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)
        try:
            conn.connect()
        except Exception as exc:                  # connect phase: refused / connect-timeout / other
            raise urllib.error.URLError(exc) from exc
        try:
            conn.sock.settimeout(read_timeout)    # read phase: the longer budget
        except Exception:
            pass
        conn.request("GET", path)
        resp = conn.getresponse()
        status = resp.status
        ok = status == 200
        try:
            resp.read()
        except Exception:
            pass
    except Exception as exc:
        ok, err = False, exc
    finally:
        try:
            if conn is not None:
                conn.close()
        except Exception:
            pass
    _note_probe(port, read_timeout, time.perf_counter() - t0, ok, status, err, connect_timeout=timeout)
    return ok


def lane_healthy(name: str) -> bool:
    spec = SERVERS[name]
    return is_healthy(spec["port"], timeout=spec.get("health_timeout", HEALTH_TIMEOUT),
                      path=spec.get("health_path", "/health"),
                      read_timeout=spec.get("read_timeout"))     # J-2113: only the hot lane sets it


def warm(name: str) -> None:
    """Best-effort: load the lane's model so the first real cycle is not a cold start."""
    spec = SERVERS[name]
    model = spec.get("warm_model")
    if not model:
        return
    try:
        body = json.dumps({"model": model, "prompt": "/no_think ok", "stream": False,
                           "options": {"num_predict": 4}}).encode()
        req = urllib.request.Request(f"http://127.0.0.1:{spec['port']}/api/generate",
                                     data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=240):
            pass
        _log(f"[supervisor] {model} warmed on {name}")
    except Exception as exc:
        _log(f"[supervisor] WARNING: could not warm {model} on {name}: {exc}")


def launch(name: str) -> None:
    spec = SERVERS[name]
    # Per-spec log location/names (2026-09-03, J-0520): default = data/<log>.log + .err.log as before
    # (hot_ollama); a spec may point at another dir ("logdir") and name either handle ("stdout_file" /
    # "stderr_file") — the CPU hubs use both to land in data/logs/ under launch_servers.ps1's names.
    logdir = Path(spec.get("logdir", LOGDIR))
    logdir.mkdir(parents=True, exist_ok=True)
    out_name = spec.get("stdout_file", f"{spec['log']}.log")
    err_name = spec.get("stderr_file", f"{spec['log']}.err.log")
    out = open(logdir / out_name, "ab")
    err = out if err_name == out_name else open(logdir / err_name, "ab")
    env = {**os.environ, **spec.get("env", {})}
    proc = subprocess.Popen([spec["bin"], *spec["args"]], cwd=spec["cwd"] or None,
                            stdout=out, stderr=err, env=env)
    _procs[name] = proc
    _log(f"[supervisor] launched {name} (pid {proc.pid}) on port {spec['port']}")


def wait_healthy(name: str, grace: int = BOOT_GRACE) -> bool:
    port = SERVERS[name]["port"]
    t0 = time.perf_counter()   # J-1688: only feeds restart()'s outcome line (_boot_secs)
    deadline = time.time() + grace
    while time.time() < deadline:
        if lane_healthy(name):
            _boot_secs[name] = time.perf_counter() - t0
            _log(f"[supervisor] {name} healthy on {port}")
            warm(name)
            return True
        time.sleep(5)
    _log(f"[supervisor] WARNING: {name} did not become healthy within {grace}s")
    return False


def ensure(name: str) -> None:
    """Adopt if already healthy, else launch and wait."""
    port = SERVERS[name]["port"]
    if lane_healthy(name):
        _log(f"[supervisor] adopted already-healthy {name} on {port}")
        warm(name)
        return
    launch(name)
    wait_healthy(name)


def kill_on_port(port: int, proc_match: str = "llama-server", pids: list | None = None) -> int:
    """
    Kill ANY process matching proc_match ("llama-server" for the old CUDA/CPU forks, "ollama" for
    the hot lane, "python" for a CPU-tier hub — see each spec's own "proc_match") bound to this
    port, whether we launched it or adopted it. Critical for the zombie case: a process
    alive-but-refusing-connections (overnight wedge) is not in _procs if we adopted it, so
    terminating only our own handle would leave the zombie holding the port and spawn a duplicate.
    Returns count killed. `pids` (J-1688, optional): a list that gets the killed pids appended, for
    restart()'s outcome line; the return value and behaviour are unchanged.
    """
    killed = 0
    if psutil is None:
        return 0
    for p in psutil.process_iter(["pid", "name"]):
        try:
            if proc_match not in (p.info["name"] or "").lower():
                continue
            for c in p.net_connections(kind="inet"):
                if c.laddr and c.laddr.port == port and c.status == psutil.CONN_LISTEN:
                    p.kill()
                    killed += 1
                    if pids is not None:
                        pids.append(p.pid)
                    _log(f"[supervisor] killed {proc_match} process pid {p.pid} on port {port}")
                    break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return killed


def restart(name: str) -> None:
    port = SERVERS[name]["port"]
    _log(f"[supervisor] {name} is DOWN — restarting (killing anything on port {port})")
    # J-1688 (F-2280): what was the HOST doing when the probes failed? Sampled for ~SNAPSHOT_WINDOW_S just
    # before the kill, so a wedged server (idle host) can be told from a starved one (busy host). Log-only,
    # never raises; its only effect on the restart is that the kill starts that much later.
    _log(f"[supervisor] {name} host before kill: {_host_snapshot()}")
    t_kill = time.perf_counter()
    own_pid = None
    killed_pids: list[int] = []
    # Kill our own handle if we have one...
    proc = _procs.get(name)
    if proc and proc.poll() is None:
        own_pid = proc.pid
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
    # ...AND kill any zombie holding the port (adopted, or our handle gone stale).
    kill_on_port(port, SERVERS[name].get("proc_match", "llama-server"), killed_pids)
    time.sleep(2)  # let the OS release the port
    t_launch = time.perf_counter()
    _boot_secs.pop(name, None)
    launch(name)
    healthy = wait_healthy(name)
    _obs(_log_restart_outcome, name, healthy, own_pid, killed_pids, t_kill, t_launch)


def main() -> None:
    if "--stop-all" in sys.argv:
        for name in SERVERS:
            p = _procs.get(name)
            if p:
                p.terminate()
        _log("[supervisor] stop-all requested (only kills procs this instance launched)")
        return

    _log(f"[supervisor] starting — ensuring {len(SERVERS)} server(s) are up: {', '.join(SERVERS)}")
    _obs(_log_config)
    for name in SERVERS:
        ensure(name)

    _log(f"[supervisor] watchdog active (every {CHECK_INTERVAL}s). Ctrl+C to stop watching.")
    start_retention_thread()
    if psutil is None:
        _log("[supervisor] WARNING: psutil not installed — cannot kill adopted/zombie "
             "processes on restart. `pip install psutil` for full zombie recovery.")
    # Require TWO consecutive failed checks before restarting, so one transient miss on a
    # busy server (mid-long-generation) doesn't trigger a needless restart.
    fail_count = {name: 0 for name in SERVERS}
    try:
        while True:
            time.sleep(CHECK_INTERVAL)
            sweep(fail_count)
    except KeyboardInterrupt:
        _log("\n[supervisor] stopped watching (servers left running).")


def retention_tick(root: Path | None = None) -> dict:
    """One scheduled disk-reclaim pass (D-0242 / J-1833): retention.scheduled_run() (labs class quarantine
    by the D-0156 age rule + purge of expired data/_trash day-dirs) then lab_sweep.boot_report() (the locked
    never-written DB copies). Imports the two sibling scripts lazily from this file's own directory so the
    supervisor keeps starting even if either is missing or broken. Never raises; returns a summary dict and
    logs one [supervisor] line per step. `root` is only for tests -- production uses the repo root."""
    out = {"ts": _iso_now(), "retention": None, "lab_sweep": None, "error": None}
    scripts_dir = str(Path(__file__).resolve().parent)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    try:
        import retention as _retention
        r = _retention.scheduled_run(root=root)
        out["retention"] = r
        _log(f"[supervisor] retention tick: {r.get('line')}")
    except Exception as exc:
        out["error"] = f"retention: {exc.__class__.__name__}: {exc}"
        _log(f"[supervisor] retention tick: retention step skipped ({out['error']})")
    try:
        import lab_sweep as _lab_sweep
        line = _lab_sweep.boot_report(root=root)
        out["lab_sweep"] = line
        _log(f"[supervisor] retention tick: {line}")
    except Exception as exc:
        err = f"lab_sweep: {exc.__class__.__name__}: {exc}"
        out["error"] = (out["error"] + "; " + err) if out["error"] else err
        _log(f"[supervisor] retention tick: lab_sweep step skipped ({err})")
    _retention_runs.append(out)
    del _retention_runs[:-10]
    return out


def _retention_loop(first_delay: float, interval: float) -> None:
    """Body of the daemon thread start_retention_thread() launches: sleep, tick, repeat. A tick that raises
    (it should not -- retention_tick() swallows its own errors) is logged and the loop keeps going."""
    time.sleep(first_delay)
    while True:
        try:
            retention_tick()
        except Exception as exc:
            _log(f"[supervisor] retention tick: unexpected failure ({exc.__class__.__name__}: {exc})")
        time.sleep(interval)


def start_retention_thread(first_delay: float = RETENTION_TICK_FIRST_DELAY_S,
                           interval: float = RETENTION_TICK_INTERVAL_S):
    """Starts the daily reclaim thread (daemon, so it never keeps the process alive past Ctrl+C). Returns the
    Thread, or None when RETENTION_TICK_ENABLED is False or the thread could not be started -- the watchdog
    runs exactly as before in either case."""
    if not RETENTION_TICK_ENABLED:
        _log("[supervisor] retention tick: disabled (RETENTION_TICK_ENABLED is False)")
        return None
    try:
        import threading
        t = threading.Thread(target=_retention_loop, args=(first_delay, interval),
                             name="retention-tick", daemon=True)
        t.start()
        _log(f"[supervisor] retention tick: scheduled (first in {first_delay/60:.0f} min, then every "
             f"{interval/3600:.0f} h) -- D-0242 labs retention + trash purge + lab_sweep")
        return t
    except Exception as exc:
        _log(f"[supervisor] retention tick: could not start ({exc.__class__.__name__}: {exc})")
        return None


_starved_skips: dict[str, int] = {}     # J-3979: lane -> consecutive RAM-starved excused timeouts


def _host_starved(port: int) -> str:
    """J-3979 / D-0761: '' unless the lane's latest probe failed by READ-phase TIMEOUT while available RAM is under
    HOST_STARVED_RAM_GB; then 'ram_avail=X.XGB'. Fail-open: any error -> '' (the failure then counts as before)."""
    try:
        if psutil is None:
            return ""
        info = _last_probe.get(port) or {}
        if info.get("err") != "timeout" or info.get("phase") != "read":
            return ""       # connect-phase timeouts (a dead port; on Windows a refused loopback connect reads as one) still count
        avail = psutil.virtual_memory().available / 2**30
        return f"ram_avail={avail:.1f}GB" if avail < HOST_STARVED_RAM_GB else ""
    except Exception:
        return ""


def sweep(fail_count: dict[str, int]) -> list[str]:
    """One health pass over every lane in SERVERS: a healthy lane resets its counter, an unhealthy one
    increments it, and a lane at 2 consecutive failures is restarted (counter reset). Returns the names
    restarted this pass. Split out of main()'s loop 2026-09-11 (J-0836) purely so the real 2-fail ->
    kill_on_port -> relaunch path can be driven by a test against a fake hub — behaviour unchanged."""
    restarted = []
    _obs(_stats.sweep_started)
    for name, spec in SERVERS.items():
        _last_probe.pop(spec["port"], None)      # J-1688: so the log lines below never show a stale probe
        if lane_healthy(name):
            fail_count[name] = 0
            _starved_skips[name] = 0
            _obs(_record_probe, name, spec, True)
        else:
            starved = _host_starved(spec["port"])
            if starved and _starved_skips.get(name, 0) < HOST_STARVED_MAX_SKIPS:
                # J-3979 / D-0761: a timeout on a RAM-starved host is not evidence of a wedge: log, do not count.
                _starved_skips[name] = _starved_skips.get(name, 0) + 1
                _obs(_record_probe, name, spec, False)
                _log(f"[supervisor] {name} health check timed out on port {spec['port']} but host is RAM-starved "
                     f"({starved} < {HOST_STARVED_RAM_GB}GB): not counted toward restart "
                     f"(fail_count stays {fail_count[name]}/2, starved skip {_starved_skips[name]}/{HOST_STARVED_MAX_SKIPS})"
                     + _probe_detail(spec))
                continue
            fail_count[name] += 1
            _obs(_record_probe, name, spec, False)
            # J-1688 (F-2280): the old text, unchanged, then the probe's budget / measured elapsed / exception class.
            # J-2113 (D-0420 D): the 1/2 line also carries a host snapshot (the 2/2 line's comes from restart()).
            _log(f"[supervisor] {name} health check failed "
                 f"({fail_count[name]}/2) on port {spec['port']}" + _probe_detail(spec)
                 + (_fail_snapshot_detail() if fail_count[name] == 1 else ""))
            if fail_count[name] >= 2:
                restart(name)
                fail_count[name] = 0
                _starved_skips[name] = 0
                restarted.append(name)
    _obs(_stats.maybe_emit_summary)
    _obs(_stats.sweep_ended)
    return restarted


if __name__ == "__main__":
    main()
