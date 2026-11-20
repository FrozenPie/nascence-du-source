"""core/sleep_offloop.py (J-1917 / F-2546, 2026-10-07, restart-gated).

The once-per-sleep consolidation block in nodes/inner_monologue_node.py used to call five plain
synchronous functions ON the event loop: stick_test.snapshot (~40 s), peer_metrics.snapshot +
commitment_ledger.holdrate_snapshot (~1 s), world_consolidation.sweep (~40 s) and book_residue.sweep
(155-265 s and growing) -- full-table LIKE scans of memory_fragments through their own sqlite
connections. While they ran the whole event loop stood still (no log lines, no 5 s substrate/climate
rows, no competence wakes, no chat input): 89 pct of the competence-timer late-seconds (F-2546).

`off_loop(fn, *args)` runs one such call in a worker thread and AWAITS it, so the sleep routine stays
strictly sequential (the next step starts only after the call returned; same order, same exceptions
raised into the caller's own fail-open try/except, same log lines) and only the loop is free.

Thread-safety audit of every wrapped call (J-1917): each opens its own sqlite connection inside the
function (core.memory.store._connect: busy_timeout 30 s, check_same_thread=False; stick_test and
nothing else uses mode=ro); no module-level cache or ContextVar/threading.local is touched; every
output is an append-only jsonl written by that one function only, except
world_consolidation.file_book_notes (also called by essay_lesson from the loop thread) which now holds
world_consolidation._FILE_LOCK for the whole call, the J-1909 _CO_RECALL_LOCK pattern.

SLEEP_SWEEPS_OFFLOOP is the kill switch: False makes off_loop() the plain synchronous call on the
caller's thread, exactly the pre-J-1917 behaviour."""
from __future__ import annotations

import asyncio

SLEEP_SWEEPS_OFFLOOP = True     # kill-switch: False = run the call synchronously on the loop thread (old behaviour)


async def off_loop(fn, *args):
    """Await fn(*args) in a worker thread (or call it inline when the kill switch is off)."""
    if not SLEEP_SWEEPS_OFFLOOP:
        return fn(*args)
    return await asyncio.to_thread(fn, *args)


# ── off_process: a CPU-bound sweep in a short-lived SPAWNED child (J-2384 / F-3082, 2026-10-18, restart-gated) ──
# off_loop() frees the loop but not the GIL. F-3082 (J-2379) measured book_residue.sweep's per-book loop
# (SelfRows.top str.find over an 18 MB string, up to 11.7 ms per call; the _signatures regexes) turning every
# GIL-releasing callback on the loop thread into a convoy: a 0.8 ms 2000-row sqlite fetch became 2.8 s and the
# 0.5 s heartbeat lagged 2.45 s, inside an off_loop() call. to_thread and sys.setswitchinterval cannot fix it
# (measured). A separate interpreter shares no GIL, so the loop keeps its speed while the child works.
#
# The child is the SAME code tree (cwd and sys.path[0] = the root this copy of core/ was imported from) and
# sees the SAME stores the in-process call would have: every path/flag constant the call depends on is read
# from the parent's own modules at call time and set on the child's before the target runs (store.DB_PATH and
# the D-0353 fence flags, like_scan.SWEEPS_SINGLE_PASS, plus the caller's `mirror` list, e.g.
# book_residue._DATA/_LOG). profile.LIVE is mirrored by calling profile.mark_live() in the child only when the
# parent is live, so the D-0353 write fence treats the child exactly as it treats the parent (a live parent:
# no authorizer, no "non-live process opened the live memory DB" line; a test parent with a redirected
# DB_PATH: unfenced because redirected, as in-process). The child's log records (at the parent's root level)
# come back on stdout and are re-emitted on the parent's loggers of the same names, so the lines reach
# data/nascence.log through the parent's own handlers with the same text; the child never opens the log
# file. The parent awaits the child, so ordering against the rest of the sleep is unchanged.
# Fail-open: a non-zero exit, a timeout (the child is killed) or no parseable dict RESULT line logs why at
# WARNING, calls on_fail(reason) if given, and returns a copy of `zero`; it never raises into sleep.
import json as _json
import logging as _logging
import os as _os
import sys as _sys
from pathlib import Path as _Path

_logger = _logging.getLogger("nascence.sleep_offloop")

OFF_PROCESS_TIMEOUT_S = 300.0
_ROOT = _Path(__file__).resolve().parent.parent
# Constants every off_process child mirrors from the parent (module, attribute), before the caller's own.
_BASE_MIRROR = (("core.memory.store", "DB_PATH"), ("core.memory.store", "_FENCE_MODE"),
                ("core.memory.store", "_LIVE_WRITES_ALLOWED"), ("core.like_scan", "SWEEPS_SINGLE_PASS"))


def _snapshot_mirror(mirror) -> list:
    import importlib
    out = []
    for mod, attr in tuple(_BASE_MIRROR) + tuple(mirror or ()):
        v = getattr(importlib.import_module(mod), attr)
        if isinstance(v, _Path):
            out.append([mod, attr, "path", str(v)])
        elif v is None or isinstance(v, (bool, int, float, str)):
            out.append([mod, attr, "json", v])
        else:
            raise TypeError(f"off_process cannot mirror {mod}.{attr} of type {type(v).__name__}")
    return out


def _child_config(module: str, func: str, mirror) -> dict:
    from core import profile
    return {"module": module, "func": func, "live": bool(profile.LIVE),
            "log_level": _logging.getLogger().getEffectiveLevel(), "mirror": _snapshot_mirror(mirror)}


class _StdoutRecordHandler(_logging.Handler):
    """Child side: one 'LOG<TAB>{json}' stdout line per record; the parent re-emits it."""
    def emit(self, record):
        try:
            msg = record.getMessage()
            if record.exc_info and not record.exc_text:
                record.exc_text = _logging.Formatter().formatException(record.exc_info)
            if record.exc_text:
                msg = msg + "\n" + record.exc_text
            _sys.stdout.write("LOG\t" + _json.dumps({"name": record.name, "level": record.levelno,
                                                      "msg": msg}) + "\n")
            _sys.stdout.flush()
        except Exception:
            pass


def _child_main(cfg_json: str) -> None:
    """Runs in the spawned child: mirror the parent's constants, call module.func(), print the result."""
    import importlib
    cfg = _json.loads(cfg_json)
    root = _logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)
    root.addHandler(_StdoutRecordHandler())
    root.setLevel(int(cfg.get("log_level", _logging.INFO)))
    if cfg.get("live"):
        from core import profile
        profile.mark_live()
    for mod, attr, kind, val in cfg.get("mirror", []):
        setattr(importlib.import_module(mod), attr, _Path(val) if kind == "path" else val)
    fn = getattr(importlib.import_module(cfg["module"]), cfg["func"])
    res = fn()
    _sys.stdout.write("RESULT\t" + _json.dumps(res, default=str) + "\n")
    _sys.stdout.flush()


def _child_state_probe() -> dict:
    """Test hook (scripts/test_j2384_offprocess.py): what the child sees after mirroring, plus one read
    through store._connect() so the D-0353 fence's own log line (or its absence) is observable."""
    from core import profile, like_scan
    from core.memory import store
    with store._connect() as conn:
        conn.execute("SELECT 1").fetchall()
    return {"live": bool(profile.LIVE), "db_path": str(store.DB_PATH), "fence_mode": store._FENCE_MODE,
            "live_writes_allowed": bool(store._LIVE_WRITES_ALLOWED),
            "single_pass": bool(like_scan.SWEEPS_SINGLE_PASS), "pid": _os.getpid()}


def _replay_and_parse(stdout: bytes):
    """Parent side: re-emit the child's log records on the same-named loggers; return (have, RESULT)."""
    result, have = None, False
    for raw in (stdout or b"").decode("utf-8", "replace").splitlines():
        tag, _, body = raw.partition("\t")
        if tag == "LOG":
            try:
                r = _json.loads(body)
                _logging.getLogger(r["name"]).log(int(r["level"]), "%s", r["msg"])
            except Exception:
                pass
        elif tag == "RESULT":
            try:
                result, have = _json.loads(body), True
            except Exception:
                result, have = None, False
    return have, result


async def off_process(module: str, func: str, *, zero: dict, mirror=(), timeout: float | None = None,
                      on_fail=None) -> dict:
    """Await module.func() (no arguments, dict result) in a spawned child interpreter. Never raises
    (except CancelledError, after killing the child): any failure logs why and returns a copy of `zero`."""
    timeout = OFF_PROCESS_TIMEOUT_S if timeout is None else timeout
    proc = None
    reason = None
    try:
        cfg = _json.dumps(_child_config(module, func, mirror))
        code = (f"import sys; sys.path.insert(0, {str(_ROOT)!r}); "
                "from core.sleep_offloop import _child_main; _child_main(sys.argv[1])")
        env = dict(_os.environ, PYTHONIOENCODING="utf-8")
        proc = await asyncio.create_subprocess_exec(
            _sys.executable, "-c", code, cfg, cwd=str(_ROOT), env=env,
            stdin=asyncio.subprocess.DEVNULL, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        try:
            out, err = await asyncio.wait_for(proc.communicate(), timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            reason = f"timeout after {timeout:g} s, child killed"
        else:
            have, res = _replay_and_parse(out)
            if proc.returncode == 0 and have and isinstance(res, dict):
                return res
            tail = " | ".join((err or b"").decode("utf-8", "replace").strip().splitlines()[-3:])[:400]
            reason = f"child exit {proc.returncode}, result {'not a dict' if have else 'missing'}: {tail}"
    except asyncio.CancelledError:
        if proc is not None and proc.returncode is None:
            try:
                proc.kill()
            except Exception:
                pass
        raise
    except Exception as exc:
        reason = f"could not run the child: {exc!r}"
    _logger.warning("off_process %s.%s failed (fail-open): %s", module, func, reason)
    if on_fail is not None:
        try:
            on_fail(reason)
        except Exception:
            pass
    return dict(zero)
