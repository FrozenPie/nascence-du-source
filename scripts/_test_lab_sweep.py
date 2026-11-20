"""
_test_lab_sweep.py -- D-0242 (2026-09-19, J-1162) regression test for scripts/lab_sweep.py. Runs
ENTIRELY against a synthetic root under tempfile.mkdtemp() -- never against the real C:\\Nascence\\data
or the real data/_lab/_isolate_outcomes.jsonl. Builds a synthetic <root>/data/_lab/ tree + a synthetic
_isolate_outcomes.jsonl covering every case lab_sweep.Scan.run() branches on:

  dir_free     locked row, db present, NOT actually locked right now  -> candidate
  dir_locked   locked row, db present, a real Windows handle held      -> still_locked
  dir_gone     locked row, db already removed                         -> already_gone
  dir_deleted  outcome "deleted", db present                          -> ignored (outcome != locked)
  dir_flip     TWO rows for the same dir: "locked" then "deleted_after_retry" (later ts) -> the LATEST
               row wins, so this must be ignored, not counted as a candidate (tests the
               _latest_outcome_by_lab_dir tie-break)
  dir_outside  a locked row whose lab_dir string points OUTSIDE data/_lab                -> out_of_scope

Then: report() text sanity; apply() actually quarantines dir_free's db (move, not delete) into
data/_trash/<today>/lab_locked/ and appends a compatible data/_trash/retention_log.jsonl row; dir_locked
is never even attempted (apply() only ever iterates scan.candidates). Mutation check: apply() is called
again on a Scan whose .candidates list has been hand-forced to ALSO include dir_locked's item (bypassing
the normal free/still_locked split) -- apply()'s own re-probe-before-move must catch this and skip it
WITHOUT moving the still-locked file, proving that re-check is load-bearing, not decorative.

Run: python scripts/_test_lab_sweep.py
"""
from __future__ import annotations

import ctypes
import datetime as _dt
import json
import sys
import tempfile
from ctypes import wintypes
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import lab_sweep  # noqa: E402

print("lab_sweep module file:", lab_sweep.__file__)
_expected = (ROOT / "scripts" / "lab_sweep.py").resolve()
if Path(lab_sweep.__file__).resolve() != _expected:
    print(f"FATAL: lab_sweep resolved from an unexpected location, expected {_expected} (F-1285 trap)")
    sys.exit(2)

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
kernel32.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
                                  wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
kernel32.CreateFileW.restype = wintypes.HANDLE
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL
GENERIC_READ = 0x80000000
FILE_SHARE_READ = 0x00000001
OPEN_EXISTING = 3
INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value


def _lock_handle(path: Path):
    h = kernel32.CreateFileW(str(path), GENERIC_READ, FILE_SHARE_READ, None, OPEN_EXISTING, 0, None)
    if h in (INVALID_HANDLE_VALUE, 0, None):
        raise ctypes.WinError(ctypes.get_last_error())
    return h


def _mk_db(lab_dir: Path) -> Path:
    lab_dir.mkdir(parents=True, exist_ok=True)
    db = lab_dir / "nascence.db"
    db.write_bytes(b"synthetic\n")
    return db


def run() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="test_lab_sweep_"))
    print("isolated temp root:", tmp)
    lab_root = tmp / "data" / "_lab"
    lab_root.mkdir(parents=True, exist_ok=True)
    outcomes = lab_root / "_isolate_outcomes.jsonl"
    outside = tmp / "data" / "memory"        # a real dir, but NOT under data/_lab
    outside.mkdir(parents=True, exist_ok=True)

    failures = []
    t0 = 1_700_000_000.0

    dir_free = lab_root / "20260101_000001"
    db_free = _mk_db(dir_free)
    dir_locked = lab_root / "20260101_000002"
    db_locked = _mk_db(dir_locked)
    dir_gone = lab_root / "20260101_000003"
    dir_gone.mkdir(parents=True, exist_ok=True)          # no db written -- already reclaimed some other way
    dir_deleted = lab_root / "20260101_000004"
    db_deleted = _mk_db(dir_deleted)                      # present, but outcome says "deleted"
    dir_flip = lab_root / "20260101_000005"
    db_flip = _mk_db(dir_flip)
    dir_outside_name = str(outside / "not_really_a_lab_dir")

    rows = [
        {"ts": t0 + 1, "lab_dir": str(dir_free), "outcome": "locked", "error": "PermissionError: [WinError 32] synthetic"},
        {"ts": t0 + 2, "lab_dir": str(dir_locked), "outcome": "locked", "error": "PermissionError: [WinError 32] synthetic"},
        {"ts": t0 + 3, "lab_dir": str(dir_gone), "outcome": "locked", "error": "PermissionError: [WinError 32] synthetic"},
        {"ts": t0 + 4, "lab_dir": str(dir_deleted), "outcome": "deleted", "error": None},
        {"ts": t0 + 5, "lab_dir": str(dir_flip), "outcome": "locked", "error": "PermissionError: [WinError 32] synthetic"},
        {"ts": t0 + 6, "lab_dir": str(dir_flip), "outcome": "deleted_after_retry", "error": "succeeded on attempt 2/4"},
        {"ts": t0 + 7, "lab_dir": dir_outside_name, "outcome": "locked", "error": "PermissionError: [WinError 32] synthetic"},
    ]
    with open(outcomes, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

    h = _lock_handle(db_locked)   # hold dir_locked's db open for the WHOLE scan+report+apply pass
    try:
        scan = lab_sweep.Scan(tmp).run()

        cand_paths = {c["path"] for c in scan.candidates}
        locked_paths = {c["path"] for c in scan.still_locked}

        ok = cand_paths == {str(db_free)}
        print(f"[1] candidates == {{dir_free}}: {sorted(cand_paths)} -> {'PASS' if ok else 'FAIL'}")
        if not ok:
            failures.append("1-candidates")

        ok = locked_paths == {str(db_locked)}
        print(f"[2] still_locked == {{dir_locked}}: {sorted(locked_paths)} -> {'PASS' if ok else 'FAIL'}")
        if not ok:
            failures.append("2-still_locked")

        ok = scan.already_gone == 1
        print(f"[3] already_gone == 1 (dir_gone): {scan.already_gone} -> {'PASS' if ok else 'FAIL'}")
        if not ok:
            failures.append("3-already_gone")

        ok = str(db_flip) not in cand_paths and str(db_flip) not in locked_paths
        print(f"[4] dir_flip excluded (latest row is deleted_after_retry, not locked): {'PASS' if ok else 'FAIL'}")
        if not ok:
            failures.append("4-latest-row-tiebreak")

        ok = scan.out_of_scope == 1
        print(f"[5] out_of_scope == 1 (row naming a path outside data/_lab): {scan.out_of_scope} -> {'PASS' if ok else 'FAIL'}")
        if not ok:
            failures.append("5-out_of_scope")

        ok = str(db_deleted) not in cand_paths and str(db_deleted) not in locked_paths
        print(f"[6] dir_deleted (outcome=deleted) never considered: {'PASS' if ok else 'FAIL'}")
        if not ok:
            failures.append("6-outcome-deleted-ignored")

        rpt = scan.report()
        ok = "1 candidate(s)" in rpt and "still_locked" in rpt
        print(f"[7] report() renders, shows 1 candidate + a still_locked section: {'PASS' if ok else 'FAIL'}")
        if not ok:
            failures.append("7-report")

        # ---- apply(): quarantines dir_free only; dir_locked was never in scan.candidates to begin with ----
        moved = scan.apply(today=_dt.date(2026, 9, 22))
        trash_log = tmp / "data" / "_trash" / "retention_log.jsonl"
        dest = tmp / "data" / "_trash" / "20260922" / "lab_locked" / f"{dir_free.name}_nascence.db"
        ok = (len(moved) == 1 and not db_free.exists() and dest.exists() and trash_log.exists()
              and '"class": "lab_locked"' in trash_log.read_text(encoding="utf-8"))
        print(f"[8] apply() quarantines dir_free (move not delete) + logs to retention_log.jsonl: "
              f"moved={len(moved)} dest_exists={dest.exists()} src_gone={not db_free.exists()} -> "
              f"{'PASS' if ok else 'FAIL'}")
        if not ok:
            failures.append("8-apply-quarantine")

        ok = db_locked.exists()   # never touched -- it was never in scan.candidates
        print(f"[9] dir_locked's db untouched by apply(): still_there={db_locked.exists()} -> {'PASS' if ok else 'FAIL'}")
        if not ok:
            failures.append("9-locked-untouched")

        # ---- Mutation check: force db_locked into .candidates (bypassing the normal free/still_locked
        # split) -- apply()'s OWN re-probe-before-move must still refuse to move a genuinely locked file,
        # proving that re-check inside apply() is load-bearing, not decorative. ----
        forced = lab_sweep.Scan(tmp)
        forced.candidates = [{"lab_dir": str(dir_locked), "path": str(db_locked),
                               "bytes": db_locked.stat().st_size, "row_ts": t0 + 2, "ref_date": "2026-01-01"}]
        moved2 = forced.apply(today=_dt.date(2026, 9, 22))
        ok = len(moved2) == 0 and db_locked.exists()
        print(f"[mutation] apply() re-probes before moving a forced still-locked candidate: "
              f"moved={len(moved2)} still_there={db_locked.exists()} -> "
              f"{'PASS (re-check is load-bearing)' if ok else 'FAIL (re-check NOT load-bearing!)'}")
        if not ok:
            failures.append("mutation-reprobe")
    finally:
        kernel32.CloseHandle(h)

    # sanity: now that the handle is closed, db_locked really was just a lock, nothing else wrong with it
    db_locked.unlink()
    print(f"    cleanup unlink of dir_locked's db after closing the handle: "
          f"{'PASS' if not db_locked.exists() else 'FAIL'}")

    total = 10
    print(f"\n{total - len(failures)}/{total} checks passed" +
          (f" -- FAILED: {failures}" if failures else " -- ALL PASS"))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(run())
