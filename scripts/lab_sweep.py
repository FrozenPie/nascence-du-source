"""
lab_sweep -- D-0242 (2026-09-19, J-1162): a reaper for confirmed-unwritten, Windows-locked lab DB
copies that lab_env.isolate().__exit__ could not delete even after its own bounded retry (added in
this same job, C:\\Users\\USER\\.claude\\skills\\job-queue\\lab_env.py). Keyed EXACTLY on the
`locked` rows of data/_lab/_isolate_outcomes.jsonl -- never on directory age or a heuristic. This is a
DIFFERENT, narrower mechanism than scripts/retention.py's own `labs` class (D-0156, unchanged by this
file): retention.py reclaims dirs by AGE (14/60 days, whether or not a DB copy inside was ever
written); this module reclaims ONLY a confirmed-never-written DB copy that isolate() itself already
tried and failed to delete, however young the dir is.

Why a separate reaper is needed at all (F-1561/F-1562, J-1064, 2026-09-18/19): a genuine 5.1-day
window found data/_lab growing 6.29 GB/day, 3.8x the pre-D-0206 rate; 29 of 44 sidecar rows were
confirmed byte-identical (never-written) DB copies whose unlink() failed at isolate().__exit__ with a
transient Windows lock (WinError 32) -- 20.46 GB, 63.7% of that window's growth. A follow-up
non-destructive DELETE-handle probe (F-1562) found the lock had cleared on EVERY one of 47 checked
copies by the time it was re-checked, minutes to days later -- i.e. the lock is real but transient, and
nothing before this module ever re-checked a `locked` row again after the moment isolate() itself gave
up on it. J-1162's own bounded retry (lab_env.py, this same job) narrows the window further at the
source, but its own module docstring says plainly it may only PARTLY help (a handle held by the SAME
live process for a longer-lived reason than GC timing will not clear in a couple of seconds) -- this
sweeper is the second half of the same ruling, for whatever the retry still could not catch.

SAFETY (D-0242's ruling text + this job's own explicit instruction): no agent deletes anything under
data/_lab. This module never calls unlink() on a live-tree path. Its only filesystem-mutating action,
gated behind --apply (or LAB_SWEEP_APPLY=1), is to MOVE (shutil.move) a verified candidate's
nascence.db into data/_trash/<today>/lab_locked/<lab_dir_name>_nascence.db -- fully reversible, and a
row compatible with scripts/retention.py's own apply() shape is appended to the SAME
data/_trash/retention_log.jsonl (class="lab_locked") rather than inventing a second trash ledger.
Symmetric with retention.py's own established dry-run-by-default / quarantine-on-apply / purge-later-
by-hand convention (D-0156) -- NOT a new convention. The one-off cleanup of the 29 copies already on
disk as of the D-0242 ruling is Travis's own action (ruling item 3); this module does not special-case
them, it only ever looks at whatever `locked` rows exist in the sidecar log at run time.

A candidate must pass ALL of:
  1. The MOST RECENT sidecar row for its lab_dir has outcome == "locked" (a dir whose latest row is
     "deleted" or "deleted_after_retry" has nothing left to sweep; a dir with no row at all is not
     touched -- this module only ever acts on what isolate() itself already reported as locked).
  2. <lab_dir>/nascence.db still exists on disk right now.
  3. A non-destructive DELETE-handle probe (identical technique to F-1562's own lock-transience check
     and to this job's own lab_env retry-logic test: ctypes CreateFileW with DELETE access +
     FILE_SHARE_READ|WRITE|DELETE, handle opened and immediately closed, nothing written) finds NO
     conflicting handle right now. A candidate that still shows a conflicting handle is reported
     separately as "still_locked" -- not a false candidate, just not actionable yet (mirrors the
     retry's own "same live process may not have exited" caveat).
  4. The lab_dir resolves to somewhere inside data/_lab (defensive scope check, same philosophy as
     retention.py's own _in_scope -- never act on a malformed/unexpected sidecar row's path).
Report (default, no flags) lists every candidate + still-locked row + GB, touches nothing. --apply
additionally quarantines verified candidates one at a time -- re-checking the live-handle probe again
immediately before each move (the report and the apply pass are not one atomic instant) and skipping
(reporting, not raising) anything that fails that re-check or whose move raises for any other reason,
leaving the copy exactly where it was, same fallback discipline as isolate().__exit__ itself.

Run:  python scripts/lab_sweep.py                     # dry run, live tree, report only
      python scripts/lab_sweep.py --apply              # quarantine verified candidates (live tree)
      python scripts/lab_sweep.py --root <dir>          # any other tree (tests) -- report only
      python scripts/lab_sweep.py --root <dir> --apply  # any other tree (tests) -- quarantines there

boot_report(root=None) is called best-effort from scripts/run_nascence.py at every Du launch, exactly
alongside backup_identity.backup() / backup_memory.main() (which themselves call
retention.boot_rotate()) -- see that file's own comment. LAB_SWEEP_BOOT_APPLY below is the single,
symmetric-with-retention.RETENTION_BOOT_ROTATE switch: it was report-only (False) from J-1162 until the
retry's own sidecar-log success rate had actually been read (F-2320: 46.9%), and was flipped True on
2026-10-06 by D-0242's re-ruling (J-1833) -- boot_report() now quarantines verified candidates at every
boot and RETURNS a one-line summary string (found / quarantined / GB / still locked); it neither prints
nor logs anything itself. scripts/run_nascence.py main() logs that returned string through its module
logger (INFO; WARNING if the hook fails to import or raises), and that is how it reaches
data/nascence.log: that file is fed only by the logging FileHandler, never by stdout, so a print() of
this line would have shown only on the launching console (F-2319, J-1704). Restart-gated: this wiring
takes effect only at Du's NEXT restart, not the process already running when this file lands (this
repo's own Du-live discipline).
"""
from __future__ import annotations

import argparse
import ctypes
import datetime as dt
import json
import os
import re
import shutil
import sys
import time
from ctypes import wintypes
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# D-0242: mirrors retention.RETENTION_BOOT_ROTATE's own precedent exactly -- False until a founder
# decision flips it after reading the retry's real success rate from the sidecar log (this job's own
# briefing: "Measure its success rate from the sidecar log instead of assuming"). While False,
# boot_report() below only ever reports; it never moves anything, on any tree.
#
# FLIPPED True 2026-10-06 (D-0242 re-ruled by travis after the 7-day read F-2320 fired its free-space
# defeater; built J-1833). The retry's real rate was read first: 46.9% of lock-hit exits recovered, so the
# sweeper is load-bearing for the other half. Every Du boot now quarantines (shutil.move, never unlink)
# each verified candidate into data/_trash/<today>/lab_locked/ -- the same apply() the --apply flag always
# ran, with the same re-probe-before-move and the same no-live-handle rule. Report-only state at the flip:
# 65 candidate(s), 42.13 GB actionable, 0 still locked (nascence.log, three boots 10-03..10-06). The
# scripts/supervisor.py daily retention tick (J-1833) calls boot_report() too, so a long-running Du no
# longer needs a reboot for the sweep to happen. Quarantine is freed by retention.boot_purge_trash() /
# retention.scheduled_run() after TRASH_DAYS -- that is the part that actually returns disk space.
LAB_SWEEP_BOOT_APPLY = True

_STAMP_RE = re.compile(r"^(\d{8})_(\d{6})")


def _stamp_date(name: str) -> dt.date | None:
    m = _STAMP_RE.match(name)
    if not m:
        return None
    try:
        return dt.datetime.strptime(m.group(1), "%Y%m%d").date()
    except Exception:
        return None


# ── the same non-destructive DELETE-handle probe as F-1562 / this job's own lab_env retry test ──────
_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True) if sys.platform == "win32" else None
if _kernel32 is not None:
    _kernel32.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
                                       wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    _kernel32.CreateFileW.restype = wintypes.HANDLE
    _kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    _kernel32.CloseHandle.restype = wintypes.BOOL

_DELETE = 0x00010000
_FILE_SHARE_READ = 0x00000001
_FILE_SHARE_WRITE = 0x00000002
_FILE_SHARE_DELETE = 0x00000004
_OPEN_EXISTING = 3
_INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value if sys.platform == "win32" else None


def probe_no_live_handle(path: Path) -> bool:
    """True iff a non-destructive DELETE-access open of `path` succeeds RIGHT NOW -- no other handle is
    open on it without FILE_SHARE_DELETE. Opens and immediately closes; never writes, deletes, renames,
    or sets a delete-disposition. Windows-only (this project runs on Windows exclusively; on any other
    platform this conservatively returns False -- 'not provably free' is the safe default here, never a
    false go-ahead). Any OSError/WinError (including the file being gone) also returns False."""
    if _kernel32 is None:
        return False
    try:
        h = _kernel32.CreateFileW(str(path), _DELETE, _FILE_SHARE_READ | _FILE_SHARE_WRITE | _FILE_SHARE_DELETE,
                                   None, _OPEN_EXISTING, 0, None)
    except Exception:
        return False
    if h in (None, 0, _INVALID_HANDLE_VALUE):
        return False
    _kernel32.CloseHandle(h)
    return True


# ── sidecar log reading ───────────────────────────────────────────────────────────────────────────
def _latest_outcome_by_lab_dir(outcomes_log: Path) -> dict:
    """{lab_dir (as logged, i.e. str(Path) at write time) -> its most recent row}. A dir can only be
    written by one isolate() call (each gets a fresh timestamped dir), so normally at most one row
    exists per dir; keeping the latest is a defensive tie-break, not an expected case."""
    latest: dict = {}
    if not outcomes_log.exists():
        return latest
    with open(outcomes_log, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            ld = row.get("lab_dir")
            if not ld:
                continue
            prev = latest.get(ld)
            if prev is None or row.get("ts", 0) >= prev.get("ts", 0):
                latest[ld] = row
    return latest


# ── scan ───────────────────────────────────────────────────────────────────────────────────────────
class Scan:
    def __init__(self, root: Path):
        self.root = root
        self.data = root / "data"
        self.lab_root = self.data / "_lab"
        self.outcomes_log = self.lab_root / "_isolate_outcomes.jsonl"
        self.candidates: list = []        # verified free right now -- actionable
        self.still_locked: list = []      # locked row, db present, probe says still held
        self.already_gone = 0             # locked row, but db no longer there (cleaned some other way)
        self.out_of_scope = 0             # locked row naming a path outside data/_lab -- never acted on

    def run(self) -> "Scan":
        latest = _latest_outcome_by_lab_dir(self.outcomes_log)
        try:
            lab_root_resolved = self.lab_root.resolve()
        except Exception:
            lab_root_resolved = self.lab_root
        for lab_dir_str, row in latest.items():
            if row.get("outcome") != "locked":
                continue
            lab_dir = Path(lab_dir_str)
            try:
                lab_dir_resolved = lab_dir.resolve()
            except Exception:
                self.out_of_scope += 1
                continue
            if lab_root_resolved != lab_dir_resolved and lab_root_resolved not in lab_dir_resolved.parents:
                self.out_of_scope += 1
                continue
            db = lab_dir / "nascence.db"
            if not db.exists():
                self.already_gone += 1
                continue
            item = {
                "lab_dir": str(lab_dir), "path": str(db), "bytes": db.stat().st_size,
                "row_ts": row.get("ts"),
                "ref_date": (_stamp_date(lab_dir.name) or dt.date.today()).isoformat(),
            }
            if probe_no_live_handle(db):
                self.candidates.append(item)
            else:
                self.still_locked.append(item)
        return self

    def report(self) -> str:
        lines = [f"# lab_sweep dry run -- root {self.root} -- rule D-0242 (J-1162)"]
        tot = sum(c["bytes"] for c in self.candidates)
        lines.append(f"\n## candidates (locked row, db present, verified NO live handle now): "
                      f"{len(self.candidates)}, {tot/1e9:.2f} GB")
        for c in sorted(self.candidates, key=lambda x: x["ref_date"]):
            lines.append(f"  {c['ref_date']}  {c['bytes']/1e6:8.1f} MB  {Path(c['path']).relative_to(self.data)}")
        tot2 = sum(c["bytes"] for c in self.still_locked)
        lines.append(f"\n## still_locked (locked row, db present, probe STILL shows a live handle): "
                      f"{len(self.still_locked)}, {tot2/1e9:.2f} GB -- left alone, not actionable yet")
        for c in sorted(self.still_locked, key=lambda x: x["ref_date"]):
            lines.append(f"  {c['ref_date']}  {c['bytes']/1e6:8.1f} MB  {Path(c['path']).relative_to(self.data)}")
        lines.append(f"\n## already_gone (locked row, no db left -- reclaimed some other way): {self.already_gone}")
        if self.out_of_scope:
            lines.append(f"## out_of_scope (locked row outside data/_lab -- refused, not acted on): {self.out_of_scope}")
        lines.append(f"\n{len(self.candidates)} candidate(s), {tot/1e9:.2f} GB total. Nothing moved (dry run).")
        return "\n".join(lines)

    def apply(self, today: "dt.date | None" = None) -> list:
        """Quarantines (shutil.move, never unlink) each candidate into
        data/_trash/<today>/lab_locked/<lab_dir_name>_nascence.db, re-probing immediately before each
        move. Appends a retention.py-compatible row to data/_trash/retention_log.jsonl (class=
        "lab_locked"). A candidate that fails the re-probe or whose move raises is skipped, reported,
        and left exactly where it was -- never retried within the same apply() call."""
        today = today or dt.date.today()
        trash = self.data / "_trash"
        dest_day = trash / today.strftime("%Y%m%d") / "lab_locked"
        log = trash / "retention_log.jsonl"
        moved: list = []
        for c in self.candidates:
            src = Path(c["path"])
            if not probe_no_live_handle(src):
                print(f"  ! skip (no longer free at apply time): {src}")
                continue
            dest = dest_day / f"{Path(c['lab_dir']).name}_nascence.db"
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.move(str(src), str(dest))
                row = {**c, "class": "lab_locked", "moved_to": str(dest), "ts": time.time(),
                       "reason": "locked row in _isolate_outcomes.jsonl, verified no live handle at sweep time"}
                moved.append(row)
                log.parent.mkdir(parents=True, exist_ok=True)
                with open(log, "a", encoding="utf-8") as f:
                    print(json.dumps(row, ensure_ascii=False), file=f)
            except Exception as exc:
                print(f"  ! could not move {src}: {exc}")
        return moved


def boot_report(root: "Path | None" = None) -> str:
    """Called at Du launch (scripts/run_nascence.py) alongside backup_identity/backup_memory. ALWAYS
    report-only unless LAB_SWEEP_BOOT_APPLY is flipped True by a future founder decision (see module
    docstring). Never raises -- any failure here must never block Du's own boot."""
    try:
        r = root or Path(__file__).resolve().parent.parent
        scan = Scan(r).run()
        if LAB_SWEEP_BOOT_APPLY:
            moved = scan.apply()
            tot = sum(m["bytes"] for m in moved)
            return (f"[lab_sweep] boot: {len(scan.candidates)} candidate(s) found, "
                    f"{len(moved)} quarantined ({tot/1e9:.2f} GB), {len(scan.still_locked)} still locked")
        return (f"[lab_sweep] boot (report-only): {len(scan.candidates)} candidate(s), "
                f"{sum(c['bytes'] for c in scan.candidates)/1e9:.2f} GB actionable, "
                f"{len(scan.still_locked)} still locked -- LAB_SWEEP_BOOT_APPLY is False, nothing moved")
    except Exception as exc:
        return f"[lab_sweep] boot: skipped ({exc.__class__.__name__}: {exc})"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=str(Path(__file__).resolve().parent.parent))
    ap.add_argument("--apply", action="store_true",
                     help="quarantine verified candidates into data/_trash/<today>/lab_locked/ (default: report only)")
    a = ap.parse_args(argv)
    apply_ = a.apply or os.environ.get("LAB_SWEEP_APPLY") == "1"
    scan = Scan(Path(a.root)).run()
    print(scan.report())
    if not apply_:
        return 0
    moved = scan.apply()
    tot = sum(m["bytes"] for m in moved)
    print(f"\nquarantined {len(moved)} candidate(s), {tot/1e9:.2f} GB, into "
          f"{scan.data / '_trash' / dt.date.today().strftime('%Y%m%d') / 'lab_locked'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
