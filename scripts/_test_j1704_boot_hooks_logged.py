"""
_test_j1704_boot_hooks_logged.py -- J-1704 (F-2319) regression test for the three boot hooks in
scripts/run_nascence.py main(): backup_identity, backup_memory and the D-0242 lab_sweep.boot_report line.

THE BUG (F-2319): those hooks reported through print(), which reaches only the launching console.
data/nascence.log is fed only by the logging FileHandler that run_nascence.py's basicConfig installs, so
"did the D-0242 boot sweeper fire at a boot" was unobservable (0 "[lab_sweep]" lines across six boots, and
the comment in main() claimed the opposite). The fix routes each report line through the module logger
(INFO for a normal report, WARNING for a hook that was skipped), keeping every hook fail-open.

HOW THIS TEST WORKS -- hermetic: it never imports run_nascence (which pulls in the whole cognitive stack),
never touches data/, and never runs a real backup. It parses scripts/run_nascence.py with ast, lifts out the
exact try/except statement in main() that imports each hook, and exec()s ONLY that statement against
  (a) a temp-file logging setup shaped like run_nascence's own (StreamHandler + FileHandler, same format,
      logger "nascence.main"), and
  (b) fake scripts.* modules injected into sys.modules. The lab_sweep fake delegates to the REAL
      lab_sweep.boot_report over an empty synthetic root, so the line asserted is the real production string.
It then asserts what landed in the temp log FILE (the thing the post-restart grep reads), at which level, and
that the console still shows the line (no loss of operator visibility).

Without the J-1704 edit the log file stays empty for every scenario (the old code print()ed), so this fails.

Run: python scripts/_test_j1704_boot_hooks_logged.py
"""
from __future__ import annotations

import ast
import contextlib
import io
import logging
import shutil
import sys
import tempfile
import types
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import lab_sweep  # noqa: E402  (the real boot_report, only ever run over a synthetic empty root)

_expected = (ROOT / "scripts" / "lab_sweep.py").resolve()
if Path(lab_sweep.__file__).resolve() != _expected:
    print(f"FATAL: lab_sweep resolved from an unexpected location, expected {_expected} (F-1285 trap)")
    sys.exit(2)

SOURCE = ROOT / "scripts" / "run_nascence.py"
LOG_FMT = "%(asctime)s [%(name)s] %(message)s"      # run_nascence.py's own basicConfig format
HOOKS = ("scripts.backup_identity", "scripts.backup_memory", "scripts.lab_sweep")

failures: list = []
n_checks = 0


def check(name: str, ok: bool, detail="") -> None:
    global n_checks
    n_checks += 1
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  <- {detail}" if (detail and not ok) else ""))
    if not ok:
        failures.append(name)


def hook_statements() -> dict:
    """{hook module name: the ast.Try statement in main() that imports it}."""
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    main = next(n for n in ast.walk(tree) if isinstance(n, ast.AsyncFunctionDef) and n.name == "main")
    found: dict = {}
    for stmt in main.body:
        if isinstance(stmt, ast.Try):
            for sub in stmt.body:
                if isinstance(sub, ast.ImportFrom) and sub.module in HOOKS:
                    found[sub.module] = stmt
    return found


class _ListHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__(logging.INFO)
        self.records: list = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append((record.levelname, record.getMessage()))


def run_hook(stmt: ast.Try, fakes: dict):
    """Exec one lifted try/except against fake hook modules + a production-shaped logger.
    Returns (records[(level, msg)], log-file text, console text, escaped exception or None)."""
    tmpdir = Path(tempfile.mkdtemp(prefix="j1704_log_"))
    console = io.StringIO()
    lst = _ListHandler()
    fh = logging.FileHandler(tmpdir / "nascence.log", encoding="utf-8")
    sh = logging.StreamHandler(console)
    for h in (fh, sh):
        h.setFormatter(logging.Formatter(LOG_FMT))
    lg = logging.getLogger("nascence.main")
    saved_logger = (lg.level, lg.propagate, list(lg.handlers))
    lg.handlers[:] = [fh, sh, lst]
    lg.setLevel(logging.INFO)
    lg.propagate = False
    mod = ast.Module(body=[stmt], type_ignores=[])
    ast.fix_missing_locations(mod)
    code = compile(mod, str(SOURCE), "exec")
    saved_mods = {k: sys.modules.get(k) for k in fakes}
    sys.modules.update(fakes)
    err = None
    try:
        with contextlib.redirect_stdout(console):    # the OLD code's print() lands here, not on the real console
            exec(code, {"logger": lg})
    except BaseException as exc:                     # the hooks are fail-open: nothing may escape
        err = exc
    finally:
        for k, v in saved_mods.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v
        for h in (fh, sh):
            h.flush()
            h.close()
        lg.handlers[:] = saved_logger[2]
        lg.setLevel(saved_logger[0])
        lg.propagate = saved_logger[1]
    text = (tmpdir / "nascence.log").read_text(encoding="utf-8")
    shutil.rmtree(tmpdir, ignore_errors=True)
    return lst.records, text, console.getvalue(), err


def fake(name: str, **attrs) -> types.ModuleType:
    m = types.ModuleType(name)
    m.__dict__.update(attrs)
    return m


def _boom(msg: str):
    def _f(*a, **k):
        raise RuntimeError(msg)
    return _f


def has(records, level: str, needle: str) -> bool:
    return any(lv == level and needle in m for lv, m in records)


def run() -> int:
    stmts = hook_statements()
    for h in HOOKS:
        check(f"main() still has a try/except importing {h}", h in stmts)
    if len(stmts) != len(HOOKS):
        print(f"\n{len(failures)} check(s) failed -- cannot lift every hook statement from main() -- FAILED")
        return 1

    empty_root = Path(tempfile.mkdtemp(prefix="j1704_root_"))   # no data/ dir -> real boot_report reports 0
    try:
        # ---- lab_sweep (the D-0242 line this job exists for) ----
        ls_ok = fake("scripts.lab_sweep", boot_report=lambda: lab_sweep.boot_report(root=empty_root))
        recs, text, console, err = run_hook(stmts["scripts.lab_sweep"], {"scripts.lab_sweep": ls_ok})
        check("lab_sweep report: fail-open, nothing escapes", err is None, repr(err))
        # J-1833 (D-0242 re-ruling, 2026-10-06): LAB_SWEEP_BOOT_APPLY is True now, so over an empty root the real
        # boot_report() line reads "[lab_sweep] boot: 0 candidate(s) found, 0 quarantined ..." (nothing to move).
        check("lab_sweep report: logged at INFO", has(recs, "INFO", "[lab_sweep] boot: 0 candidate(s) found, 0 quarantined"), recs)
        check("lab_sweep report: reaches the log FILE (the post-restart grep)",
              "[nascence.main] [lab_sweep] boot: 0 candidate(s) found, 0 quarantined" in text, repr(text))
        check("lab_sweep report: console still shows it", "[lab_sweep] boot: 0 candidate(s) found" in console, repr(console))

        ls_bad = fake("scripts.lab_sweep", boot_report=_boom("boom"))
        recs, text, console, err = run_hook(stmts["scripts.lab_sweep"], {"scripts.lab_sweep": ls_bad})
        check("lab_sweep skipped: fail-open, nothing escapes", err is None, repr(err))
        check("lab_sweep skipped: logged at WARNING", has(recs, "WARNING", "[lab_sweep] skipped: boom"), recs)
        check("lab_sweep skipped: reaches the log FILE", "[lab_sweep] skipped: boom" in text, repr(text))

        # ---- backup_identity (sibling hook: its return line was dropped at boot, even from the console) ----
        line = "[backup] 20261004: 0 new file(s) snapshotted (3 day(s) retained; 0 quarantined)"
        bi_ok = fake("scripts.backup_identity", backup=lambda: line)
        recs, text, console, err = run_hook(stmts["scripts.backup_identity"], {"scripts.backup_identity": bi_ok})
        check("backup_identity report: fail-open, nothing escapes", err is None, repr(err))
        check("backup_identity report: logged at INFO", has(recs, "INFO", line), recs)
        check("backup_identity report: reaches the log FILE", f"[nascence.main] {line}" in text, repr(text))

        bi_bad = fake("scripts.backup_identity", backup=_boom("disk full"))
        recs, text, console, err = run_hook(stmts["scripts.backup_identity"], {"scripts.backup_identity": bi_bad})
        check("backup_identity skipped: fail-open, nothing escapes", err is None, repr(err))
        check("backup_identity skipped: logged at WARNING", has(recs, "WARNING", "[backup] skipped: disk full"), recs)
        check("backup_identity skipped: reaches the log FILE", "[backup] skipped: disk full" in text, repr(text))

        # ---- backup_memory (sibling hook: its own success lines are print()ed INSIDE backup_memory.main(),
        #      untouched here; only its skipped branch is routed) ----
        calls: list = []
        bm_ok = fake("scripts.backup_memory", main=lambda: calls.append(1))
        recs, text, console, err = run_hook(stmts["scripts.backup_memory"], {"scripts.backup_memory": bm_ok})
        check("backup_memory success: hook still called exactly once, nothing escapes", calls == [1] and err is None,
              f"calls={calls} err={err!r}")

        bm_bad = fake("scripts.backup_memory", main=_boom("nope"))
        recs, text, console, err = run_hook(stmts["scripts.backup_memory"], {"scripts.backup_memory": bm_bad})
        check("backup_memory skipped: fail-open, nothing escapes", err is None, repr(err))
        check("backup_memory skipped: logged at WARNING", has(recs, "WARNING", "[backup-memory] skipped: nope"), recs)
        check("backup_memory skipped: reaches the log FILE", "[backup-memory] skipped: nope" in text, repr(text))
    finally:
        shutil.rmtree(empty_root, ignore_errors=True)

    print(f"\n{n_checks - len(failures)}/{n_checks} checks passed" +
          (f" -- FAILED: {failures}" if failures else " -- ALL PASS"))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(run())
