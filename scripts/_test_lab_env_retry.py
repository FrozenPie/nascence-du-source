"""
_test_lab_env_retry.py -- D-0242 (2026-09-19, J-1162) regression test for the bounded retry added to
lab_env.isolate().__exit__'s unwritten-DB-copy unlink(). Exercises __exit__ directly (bypassing
__enter__ and the real DB-copy machinery) against a synthetic file in a temp dir, using a real Windows
handle opened with NO FILE_SHARE_DELETE (the same missing-share shape an un-.close()d sqlite3
connection leaves -- exactly what makes Path.unlink() raise PermissionError: [WinError 32] -- and the
same technique F-1562's own non-destructive lock probe used) to simulate the transient lock
deterministically instead of racing a real sqlite3 connection's GC timing.

Three cases:
  A. never locked                     -> unlink succeeds on attempt 1     -> outcome "deleted"
  B. locked, clears mid-retry window  -> unlink fails once, then succeeds -> outcome "deleted_after_retry"
  C. locked for the whole retry window -> outcome "locked", file left in place, __exit__ never raises

Mutation check (the run's 4th check): case B is replayed with lab_env._DB_UNLINK_RETRY_ATTEMPTS
monkeypatched to 1 (the pre-J-1162 no-retry shape). Against the IDENTICAL lock timing that produced
"deleted_after_retry" in case B, it MUST now report "locked" -- proving the retry is what makes case B
pass, not something else (a stale outcome file, a lock that happened to clear before Python even got
to the try/except, etc).

Isolated: everything happens inside a tempfile.mkdtemp() dir. lab_env._LAB_ROOT and
lab_env._ISOLATE_OUTCOMES_LOG are monkeypatched to point inside that temp dir for the duration of this
script only (restored in a finally:) -- the real data/_lab, the real _isolate_outcomes.jsonl and the
real nascence.db are never opened, read, or written by this script. lab_env.py itself lives outside
this repo (C:\\Users\\USER\\.claude\\skills\\job-queue\\lab_env.py); __file__ is printed and asserted
against that exact path as the F-1285 module-resolution proof.

Run: python scripts/_test_lab_env_retry.py
"""
from __future__ import annotations

import ctypes
import json
import sys
import tempfile
import threading
import time
from ctypes import wintypes
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

SKILLS_JOB_QUEUE = Path(r"C:\Users\USER\.claude\skills\job-queue")
if str(SKILLS_JOB_QUEUE) not in sys.path:
    sys.path.insert(0, str(SKILLS_JOB_QUEUE))
import lab_env  # noqa: E402

print("lab_env module file:", lab_env.__file__)  # module-resolution proof (F-1285 trap)
_resolved = Path(lab_env.__file__).resolve()
_expected = (SKILLS_JOB_QUEUE / "lab_env.py").resolve()
if _resolved != _expected:
    print(f"FATAL: lab_env resolved from {_resolved}, expected {_expected} -- module-resolution trap (F-1285)")
    sys.exit(2)

# ---- Windows CreateFileW plumbing (same technique as F-1562's own non-destructive lock probe) ----
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
kernel32.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
                                  wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
kernel32.CreateFileW.restype = wintypes.HANDLE
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL

GENERIC_READ = 0x80000000
FILE_SHARE_READ = 0x00000001          # deliberately NOT FILE_SHARE_DELETE / FILE_SHARE_WRITE
OPEN_EXISTING = 3
INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value


def _lock_handle(path: Path):
    h = kernel32.CreateFileW(str(path), GENERIC_READ, FILE_SHARE_READ, None, OPEN_EXISTING, 0, None)
    if h in (INVALID_HANDLE_VALUE, 0, None):
        raise ctypes.WinError(ctypes.get_last_error())
    return h


def _make_exit_target(tmp: Path, name: str):
    lab_dir = tmp / name
    lab_dir.mkdir(parents=True, exist_ok=True)
    db = lab_dir / "nascence.db"
    db.write_bytes(b"synthetic unwritten db copy for J-1162's own retry test\n")
    inst = lab_env.isolate.__new__(lab_env.isolate)   # bypass __init__/__enter__ entirely
    inst.also = []
    inst.db = "copy"
    inst.lab_dir = lab_dir
    inst._patches = []
    inst._db_path = db
    inst._db_baseline = lab_env._hash_file(db)         # byte-identical to itself -> "unwritten"
    return inst, db


def _last_outcome_row(log: Path):
    if not log.exists():
        return None
    lines = [l for l in log.read_text(encoding="utf-8").splitlines() if l.strip()]
    return json.loads(lines[-1]) if lines else None


def run() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="test_lab_env_retry_"))
    print("isolated temp dir:", tmp)
    real_lab_root, real_log = lab_env._LAB_ROOT, lab_env._ISOLATE_OUTCOMES_LOG
    lab_env._LAB_ROOT = tmp
    lab_env._ISOLATE_OUTCOMES_LOG = tmp / "_isolate_outcomes.jsonl"
    failures = []
    try:
        # ---- Case A: never locked ----
        inst, db = _make_exit_target(tmp, "case_a")
        t0 = time.time()
        inst.__exit__(None, None, None)
        dt = time.time() - t0
        row = _last_outcome_row(lab_env._ISOLATE_OUTCOMES_LOG)
        ok = (not db.exists()) and bool(row) and row["outcome"] == "deleted" and dt < 0.4
        print(f"[A] never-locked: db_gone={not db.exists()} outcome={row and row['outcome']} "
              f"dt={dt:.2f}s -> {'PASS' if ok else 'FAIL'}")
        if not ok:
            failures.append("A")

        # ---- Case B: locked, clears partway through the retry window ----
        inst, db = _make_exit_target(tmp, "case_b")
        h = _lock_handle(db)
        timer = threading.Timer(0.7, lambda: kernel32.CloseHandle(h))   # clears during attempt 2 or 3
        timer.start()
        t0 = time.time()
        inst.__exit__(None, None, None)
        dt = time.time() - t0
        timer.join()
        row = _last_outcome_row(lab_env._ISOLATE_OUTCOMES_LOG)
        ok = (not db.exists()) and bool(row) and row["outcome"] == "deleted_after_retry"
        print(f"[B] locked-then-clears@0.7s: db_gone={not db.exists()} outcome={row and row['outcome']} "
              f"dt={dt:.2f}s -> {'PASS' if ok else 'FAIL'}")
        if not ok:
            failures.append("B")

        # ---- Case C: locked for the entire retry window ----
        inst, db = _make_exit_target(tmp, "case_c")
        h = _lock_handle(db)
        t0 = time.time()
        raised = False
        try:
            inst.__exit__(None, None, None)      # must never raise
        except Exception as exc:
            raised = True
            print(f"    unexpected raise: {exc!r}")
        dt = time.time() - t0
        row = _last_outcome_row(lab_env._ISOLATE_OUTCOMES_LOG)
        ok = (not raised) and db.exists() and bool(row) and row["outcome"] == "locked"
        print(f"[C] always-locked: raised={raised} db_still_there={db.exists()} "
              f"outcome={row and row['outcome']} dt={dt:.2f}s -> {'PASS' if ok else 'FAIL'}")
        if not ok:
            failures.append("C")
        kernel32.CloseHandle(h)
        db.unlink()   # confirm the lock, not something else, was the only blocker
        print(f"    cleanup unlink after closing the handle: {'PASS' if not db.exists() else 'FAIL'}")

        # ---- Mutation check: attempts=1 (pre-J-1162 shape) replays case B's exact lock timing ----
        real_attempts = lab_env._DB_UNLINK_RETRY_ATTEMPTS
        lab_env._DB_UNLINK_RETRY_ATTEMPTS = 1
        try:
            inst, db = _make_exit_target(tmp, "case_b_mutation")
            h = _lock_handle(db)
            timer = threading.Timer(0.7, lambda: kernel32.CloseHandle(h))
            timer.start()
            inst.__exit__(None, None, None)
            row = _last_outcome_row(lab_env._ISOLATE_OUTCOMES_LOG)
            mutation_caught = bool(row) and row["outcome"] == "locked"
            print(f"[mutation] attempts=1 (no retry) on the SAME lock timing that passed case B: "
                  f"outcome={row and row['outcome']} -> "
                  f"{'PASS (fix is load-bearing)' if mutation_caught else 'FAIL (fix NOT load-bearing!)'}")
            if not mutation_caught:
                failures.append("mutation")
            timer.join()
            if db.exists():
                db.unlink()
        finally:
            lab_env._DB_UNLINK_RETRY_ATTEMPTS = real_attempts
    finally:
        lab_env._LAB_ROOT, lab_env._ISOLATE_OUTCOMES_LOG = real_lab_root, real_log

    total = 4
    print(f"\n{total - len(failures)}/{total} checks passed" +
          (f" -- FAILED: {failures}" if failures else " -- ALL PASS"))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(run())
