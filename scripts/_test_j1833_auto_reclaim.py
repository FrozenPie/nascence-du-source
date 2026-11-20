"""
_test_j1833_auto_reclaim.py -- D-0242 build (2026-10-06, J-1833): regression test for the automatic disk
reclaim path. Runs ENTIRELY against synthetic roots under tempfile.mkdtemp() -- never against the real
C:\\Nascence\\data. Covers the three things the ruling asked for:

  (1) scripts/lab_sweep.py  LAB_SWEEP_BOOT_APPLY is True, so boot_report() now QUARANTINES (moves) a verified
      never-written locked copy into data/_trash/<today>/lab_locked/ and reports found/quarantined/GB.
  (2) scripts/retention.py  boot_purge_trash() deletes data/_trash/<YYYYMMDD>/ day-dirs older than TRASH_DAYS
      and nothing else; RETENTION_BOOT_PURGE=False makes it a no-op.
  (3) scripts/retention.py  scheduled_run() applies the labs class by the D-0156 age rule (uncited >= 14 d
      moves, cited >= 14 d < 60 d stays, young stays), purges expired trash, never touches data/backups
      (not its class), data/_hold, non-date trash entries, or anything outside data/_lab + data/_trash;
      RETENTION_SCHEDULED_LABS=False makes it a no-op; an exception inside is captured, not raised.
      scripts/supervisor.py retention_tick() runs both steps on a root and logs one line per step;
      start_retention_thread() runs the tick on its schedule in a daemon thread and is a no-op when
      RETENTION_TICK_ENABLED is False.
  (4) scripts/run_nascence.py main() carries the new fail-open boot hook that logs boot_purge_trash()'s line
      at INFO and a failure at WARNING (lifted and exec'd the way _test_j1704_boot_hooks_logged.py does).

Run: python scripts/_test_j1833_auto_reclaim.py
"""
from __future__ import annotations

import ast
import contextlib
import datetime as dt
import io
import json
import logging
import shutil
import sys
import tempfile
import threading
import time
import types
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import retention  # noqa: E402
import lab_sweep  # noqa: E402

for _mod in (retention, lab_sweep):
    _exp = (ROOT / "scripts" / (_mod.__name__ + ".py")).resolve()
    if Path(_mod.__file__).resolve() != _exp:
        print(f"FATAL: {_mod.__name__} resolved from {_mod.__file__}, expected {_exp} (F-1285 trap)")
        sys.exit(2)
print("retention module file:", retention.__file__)
print("lab_sweep module file:", lab_sweep.__file__)

TODAY = dt.date(2026, 10, 6)
failures: list = []
n_checks = 0


def check(name: str, ok: bool, detail="") -> None:
    global n_checks
    n_checks += 1
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  <- {detail}" if (detail and not ok) else ""))
    if not ok:
        failures.append(name)


def _file(p: Path, size: int = 16) -> Path:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"x" * size)
    return p


def build_tree(tmp: Path) -> dict:
    """A synthetic Nascence root with every case the reclaim path branches on."""
    data = tmp / "data"
    lab = data / "_lab"
    trash = data / "_trash"
    t = {}
    # 2026-09-01 -> 35 d old on TODAY: past the 14 d uncited window, inside the 60 d cited one
    t["old_uncited"] = lab / "20260901_000001_old_uncited";  _file(t["old_uncited"] / "nascence.db", 1000)
    t["old_cited"] = lab / "20260901_000002_old_cited";      _file(t["old_cited"] / "nascence.db", 1000)
    t["young"] = lab / "20261005_000003_young";              _file(t["young"] / "nascence.db", 1000)
    t["locked"] = lab / "20261005_000005_locked";            _file(t["locked"] / "nascence.db", 2000)
    # the citation that keeps old_cited (retention scans docs/findings.jsonl, docs/job_queue.jsonl, docs/**/*.md)
    docs = tmp / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "findings.jsonl").write_text(json.dumps({"claim": f"see data/_lab/{t['old_cited'].name}"}) + "\n",
                                         encoding="utf-8")
    (docs / "job_queue.jsonl").write_text("", encoding="utf-8")
    # sidecar: only the locked dir has a locked row
    (lab / "_isolate_outcomes.jsonl").write_text(
        json.dumps({"ts": 1_700_000_000.0, "lab_dir": str(t["locked"]), "outcome": "locked",
                    "error": "PermissionError: [WinError 32] synthetic"}) + "\n", encoding="utf-8")
    # trash: two expired day-dirs, one young, one non-date entry, the log file
    t["trash_old1"] = trash / "20260901";  _file(t["trash_old1"] / "labs" / "x" / "nascence.db", 500)
    t["trash_old2"] = trash / "20260915";  _file(t["trash_old2"] / "lab_locked" / "y_nascence.db", 500)
    t["trash_young"] = trash / "20261004"; _file(t["trash_young"] / "labs" / "z" / "nascence.db", 500)
    t["trash_odd"] = trash / "not_a_date"; _file(t["trash_odd"] / "keep.bin", 500)
    t["trash_log"] = trash / "retention_log.jsonl"
    t["trash_log"].write_text("", encoding="utf-8")
    # never in scope
    t["hold"] = _file(data / "_hold" / "subconscious_state_20260928_190831.json", 300)
    t["backup_old"] = _file(data / "backups" / "nascence_20260101_000000.db", 300)
    t["live"] = _file(data / "nascence.db", 300)
    return t


def snapshot(tmp: Path) -> set:
    return {str(p.relative_to(tmp)) for p in tmp.rglob("*") if p.is_file()}


def run() -> int:
    # ---------------------------------------------------------------- (1) lab_sweep flag + boot_report applies
    check("LAB_SWEEP_BOOT_APPLY is True (D-0242 re-ruling)", lab_sweep.LAB_SWEEP_BOOT_APPLY is True)
    check("RETENTION_BOOT_PURGE is True", retention.RETENTION_BOOT_PURGE is True)
    check("RETENTION_SCHEDULED_LABS is True", retention.RETENTION_SCHEDULED_LABS is True)

    tmp = Path(tempfile.mkdtemp(prefix="j1833_"))
    print("isolated temp root:", tmp)
    try:
        t = build_tree(tmp)
        line = lab_sweep.boot_report(root=tmp)
        print("   ", line)
        dest = tmp / "data" / "_trash" / dt.date.today().strftime("%Y%m%d") / "lab_locked" / f"{t['locked'].name}_nascence.db"
        check("boot_report: quarantines the locked copy (move, not delete)",
              not (t["locked"] / "nascence.db").exists() and dest.exists() and dest.stat().st_size == 2000,
              f"src_gone={not (t['locked'] / 'nascence.db').exists()} dest={dest.exists()}")
        check("boot_report: line reports 1 found / 1 quarantined",
              line.startswith("[lab_sweep] boot: 1 candidate(s) found, 1 quarantined (0.00 GB), 0 still locked"), line)
        check("boot_report: the other lab dirs untouched",
              all((t[k] / "nascence.db").exists() for k in ("old_uncited", "old_cited", "young")))
        log_rows = [json.loads(l) for l in t["trash_log"].read_text(encoding="utf-8").splitlines() if l.strip()]
        check("boot_report: one class=lab_locked row appended to retention_log.jsonl",
              len(log_rows) == 1 and log_rows[0].get("class") == "lab_locked", log_rows)

        # ---------------------------------------------------------------- (2) boot_purge_trash
        before = snapshot(tmp)
        line = retention.boot_purge_trash(root=tmp, today=TODAY)
        print("   ", line)
        after = snapshot(tmp)
        removed = before - after
        check("boot_purge_trash: both expired day-dirs deleted",
              not t["trash_old1"].exists() and not t["trash_old2"].exists())
        check("boot_purge_trash: young day-dir, non-date entry, log file kept",
              t["trash_young"].exists() and t["trash_odd"].exists() and t["trash_log"].exists())
        check("boot_purge_trash: removed ONLY files under the two expired day-dirs",
              all(r.startswith(("data\\_trash\\20260901", "data\\_trash\\20260915", "data/_trash/20260901", "data/_trash/20260915"))
                  for r in removed) and len(removed) == 2, sorted(removed))
        check("boot_purge_trash: line reports 2 of 2 deleted",
              line.startswith("[retention] boot purge: 2 of 2 quarantine day-dir(s) older than 7 d deleted"), line)
        check("boot_purge_trash: _hold / backups / live db untouched",
              t["hold"].exists() and t["backup_old"].exists() and t["live"].exists())
        log_rows = [json.loads(l) for l in t["trash_log"].read_text(encoding="utf-8").splitlines() if l.strip()]
        check("boot_purge_trash: purge rows appended to retention_log.jsonl",
              sum(1 for r in log_rows if "purged" in r) == 2, log_rows)

        # flag off -> no-op (re-create an expired day-dir to prove it stays)
        _file(t["trash_old1"] / "labs" / "x" / "nascence.db", 500)
        saved = retention.RETENTION_BOOT_PURGE
        retention.RETENTION_BOOT_PURGE = False
        try:
            line = retention.boot_purge_trash(root=tmp, today=TODAY)
        finally:
            retention.RETENTION_BOOT_PURGE = saved
        check("boot_purge_trash: RETENTION_BOOT_PURGE=False is a no-op",
              t["trash_old1"].exists() and "RETENTION_BOOT_PURGE is False" in line, line)

        # ---------------------------------------------------------------- (3) scheduled_run
        before = snapshot(tmp)
        r = retention.scheduled_run(root=tmp, today=TODAY)
        print("   ", r["line"])
        after = snapshot(tmp)
        dest_dir = tmp / "data" / "_trash" / TODAY.strftime("%Y%m%d") / "labs" / t["old_uncited"].name
        check("scheduled_run: no error", r["error"] is None, r["error"])
        check("scheduled_run: exactly 1 labs candidate (old uncited), moved",
              r["candidates"] == 1 and r["moved"] == 1 and not t["old_uncited"].exists()
              and (dest_dir / "nascence.db").exists(), r)
        check("scheduled_run: old CITED dir kept (14 d < age < 60 d)", (t["old_cited"] / "nascence.db").exists())
        check("scheduled_run: young dir kept", (t["young"] / "nascence.db").exists())
        check("scheduled_run: the re-created expired day-dir purged, young kept",
              r["purged"] == 1 and not t["trash_old1"].exists() and t["trash_young"].exists(), r)
        check("scheduled_run: backups class NOT touched (labs only)", t["backup_old"].exists())
        check("scheduled_run: _hold / live db / non-date trash entry untouched",
              t["hold"].exists() and t["live"].exists() and t["trash_odd"].exists())
        gained = after - before
        check("scheduled_run: every new file sits under data/_trash/<today>/labs/",
              gained and all("_trash" in g and TODAY.strftime("%Y%m%d") in g for g in gained), sorted(gained))
        check("scheduled_run: line names the counts",
              "1 of 1 lab dir(s) quarantined" in r["line"] and "1 of 1 quarantine day-dir(s)" in r["line"], r["line"])

        saved = retention.RETENTION_SCHEDULED_LABS
        retention.RETENTION_SCHEDULED_LABS = False
        try:
            r2 = retention.scheduled_run(root=tmp, today=TODAY)
        finally:
            retention.RETENTION_SCHEDULED_LABS = saved
        check("scheduled_run: RETENTION_SCHEDULED_LABS=False is a no-op",
              r2["enabled"] is False and r2["moved"] == 0 and "is False" in r2["line"], r2)

        saved_labs = retention.Plan.labs
        retention.Plan.labs = lambda self: (_ for _ in ()).throw(RuntimeError("synthetic failure"))
        try:
            r3 = retention.scheduled_run(root=tmp, today=TODAY)
        finally:
            retention.Plan.labs = saved_labs
        check("scheduled_run: an exception inside is captured, not raised",
              r3["error"] == "RuntimeError: synthetic failure" and "skipped" in r3["line"], r3)

        # ---------------------------------------------------------------- (3b) supervisor tick + thread
        import supervisor
        _exp = (ROOT / "scripts" / "supervisor.py").resolve()
        check("supervisor imported from this tree", Path(supervisor.__file__).resolve() == _exp, supervisor.__file__)
        logged: list = []
        saved_log = supervisor._log
        supervisor._log = lambda msg: logged.append(msg)
        try:
            tmp2 = Path(tempfile.mkdtemp(prefix="j1833_sup_"))
            try:
                t2 = build_tree(tmp2)
                # J-4052: the fixture's dates are fixed around TODAY (2026-10-06), but retention_tick() uses the real clock, so
                # as the calendar moved on the "young" and "locked" dirs aged past the 14 d window and were swept as ordinary
                # uncited labs (4 moved instead of 1; nothing left for lab_sweep). Pin retention's clock to TODAY for this call.
                import retention as _ret_pin
                _orig_sched = _ret_pin.scheduled_run
                _ret_pin.scheduled_run = lambda root=None, today=None: _orig_sched(root=root, today=today or TODAY)
                try:
                    out = supervisor.retention_tick(root=tmp2)
                finally:
                    _ret_pin.scheduled_run = _orig_sched
                check("retention_tick: no error", out["error"] is None, out)
                check("retention_tick: retention step ran on the given root (old uncited dir moved)",
                      out["retention"] and out["retention"]["moved"] == 1 and not t2["old_uncited"].exists(), out)
                check("retention_tick: lab_sweep step ran (locked copy quarantined)",
                      str(out["lab_sweep"]).startswith("[lab_sweep] boot: 1 candidate(s) found, 1 quarantined")
                      and not (t2["locked"] / "nascence.db").exists(), out)
                check("retention_tick: one [supervisor] line per step",
                      sum(1 for m in logged if m.startswith("[supervisor] retention tick: [retention]")) == 1
                      and sum(1 for m in logged if m.startswith("[supervisor] retention tick: [lab_sweep]")) == 1, logged)
                check("retention_tick: _hold untouched", t2["hold"].exists())
            finally:
                shutil.rmtree(tmp2, ignore_errors=True)

            calls: list = []
            saved_tick = supervisor.retention_tick
            supervisor.retention_tick = lambda root=None: calls.append(time.time())
            try:
                th = supervisor.start_retention_thread(first_delay=0.2, interval=0.3)
                deadline = time.time() + 3.0
                while len(calls) < 2 and time.time() < deadline:
                    time.sleep(0.05)
            finally:
                supervisor.retention_tick = saved_tick
            check("start_retention_thread: returns a daemon thread that ticks on schedule (>= 2 ticks in 3 s)",
                  isinstance(th, threading.Thread) and th.daemon and len(calls) >= 2, f"calls={len(calls)} th={th}")
            check("start_retention_thread: logs the schedule line",
                  any("retention tick: scheduled" in m for m in logged), logged[-3:])
            saved_en = supervisor.RETENTION_TICK_ENABLED
            supervisor.RETENTION_TICK_ENABLED = False
            try:
                th2 = supervisor.start_retention_thread(first_delay=0.1, interval=0.1)
            finally:
                supervisor.RETENTION_TICK_ENABLED = saved_en
            check("start_retention_thread: RETENTION_TICK_ENABLED=False returns None", th2 is None)
            check("production schedule: first tick >= 5 min, interval 24 h",
                  supervisor.RETENTION_TICK_FIRST_DELAY_S >= 300 and supervisor.RETENTION_TICK_INTERVAL_S == 86400)
            check("main() calls start_retention_thread()",
                  "start_retention_thread()" in (ROOT / "scripts" / "supervisor.py").read_text(encoding="utf-8")
                  .split("def main() -> None:")[1].split("def retention_tick")[0])
        finally:
            supervisor._log = saved_log

        # ---------------------------------------------------------------- (4) run_nascence boot hook
        src = ROOT / "scripts" / "run_nascence.py"
        tree = ast.parse(src.read_text(encoding="utf-8"))
        main_fn = next(n for n in ast.walk(tree) if isinstance(n, ast.AsyncFunctionDef) and n.name == "main")
        stmt = None
        order = []
        for s in main_fn.body:
            if isinstance(s, ast.Try):
                for sub in s.body:
                    if isinstance(sub, ast.ImportFrom):
                        order.append(sub.module)
                        if sub.module == "scripts.retention":
                            stmt = s
        check("run_nascence main(): has a try/except importing scripts.retention", stmt is not None, order)
        check("run_nascence main(): the purge hook comes right after the lab_sweep hook",
              "scripts.lab_sweep" in order and order.index("scripts.retention") == order.index("scripts.lab_sweep") + 1,
              order)
        if stmt is not None:
            def run_hook(fake_mod):
                recs: list = []

                class H(logging.Handler):
                    def emit(self, rec):
                        recs.append((rec.levelname, rec.getMessage()))
                lg = logging.getLogger("nascence.main.j1833test")
                lg.handlers[:] = [H()]
                lg.setLevel(logging.INFO)
                lg.propagate = False
                mod = ast.Module(body=[stmt], type_ignores=[])
                ast.fix_missing_locations(mod)
                code = compile(mod, str(src), "exec")
                saved_mod = sys.modules.get("scripts.retention")
                sys.modules["scripts.retention"] = fake_mod
                err = None
                try:
                    with contextlib.redirect_stdout(io.StringIO()):
                        exec(code, {"logger": lg})
                except BaseException as exc:
                    err = exc
                finally:
                    if saved_mod is None:
                        sys.modules.pop("scripts.retention", None)
                    else:
                        sys.modules["scripts.retention"] = saved_mod
                return recs, err

            ok_mod = types.ModuleType("scripts.retention")
            ok_mod.boot_purge_trash = lambda: "[retention] boot purge: 3 of 3 quarantine day-dir(s) older than 7 d deleted (17.97 GB)"
            recs, err = run_hook(ok_mod)
            check("hook: logs boot_purge_trash()'s line at INFO, nothing escapes",
                  err is None and ("INFO", ok_mod.boot_purge_trash()) in recs, f"err={err!r} recs={recs}")

            bad_mod = types.ModuleType("scripts.retention")

            def _boom():
                raise RuntimeError("disk on fire")
            bad_mod.boot_purge_trash = _boom
            recs, err = run_hook(bad_mod)
            check("hook: a raising purge is fail-open and logged at WARNING",
                  err is None and any(lv == "WARNING" and "[retention] boot purge skipped: disk on fire" in m for lv, m in recs),
                  f"err={err!r} recs={recs}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"\n{n_checks - len(failures)}/{n_checks} checks passed" +
          (f" -- FAILED: {failures}" if failures else " -- ALL PASS"))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(run())
