"""
J-1681 UPDATE: the day-granularity limitation described below is now SOLVED by
scripts/du_lifetimes.py, which reads data/nascence.log's own lifecycle markers for EXACT
per-process lifetimes (every boot, clean shutdown vs unclean end, same-day restarts,
overlapping double-launches) and classifies which lifetimes BOOTED after, or were ALIVE
across, a given instant (an epoch, a file's mtime or a commit's committer date). Reach it
from here with --from-log (every other flag is forwarded to it):
    python scripts/du_restart_history.py --from-log --commit HEAD
    python scripts/du_restart_history.py --from-log --file core/mood.py --json
    python scripts/du_restart_history.py --from-log --all --check-live
Without --from-log this tool is unchanged (the daily-snapshot timeline below).

J-0707: reusable Du-process restart timeline, built after this job found a real
methodology gap in the causal-substrate accrual re-checks (F-0893/F-0986/F-1013).

THE GAP: those findings treated a commit LANDING (git log timestamp) on
core/climate_engine.py or core/homeostasis_causal.py as the moment the change
went LIVE in Du's running process, using it directly as a data-filter cutoff
(`ts >= <commit epoch>`). That is wrong whenever Du's own process does not
restart at that instant: Python caches an imported module's code for the life
of the process, so a formula change committed to disk has no effect on a
long-running process until its NEXT restart. F-0986/F-1013 already understood
this for D-0148 specifically (they checked data/climate_state.json's
integration_drive field directly rather than trusting git log alone) but the
same discipline was never applied to the ORIGINAL 68a0364 fix's own "post-fix"
cutoff -- it was assumed live from its commit timestamp, unchecked, for three
findings in a row (F-0893, F-0986, F-1013).

WHAT THIS SCRIPT DOES: reconstructs Du's real restart timeline from two
independent, genuinely evidenced sources, so a future accrual re-check can
filter shadow-log rows by the regime ACTUALLY live in the process, not by
commit timestamps:

  1. scripts/backup_identity.py's backup() runs at the top of every
     run_nascence.py launch (see that file's own docstring: "Runs
     automatically at every Du launch"), and writes into
     data/_snapshots/daily/<YYYYMMDD>/ -- ONE new folder the first time
     backup() runs on a given calendar day. A folder's own filesystem
     CREATION time (not the mtime of the files inside it -- shutil.copy2
     preserves the SOURCE's mtime, not the copy event's time) is real
     evidence a launch happened at approximately that instant. This only
     resolves to day granularity if you only look at folder *existence*,
     but the folder's own creation timestamp is exact to the second and
     free — this script reads that directly via Windows CreationTimeUtc,
     no assumption of "first launch of the day" precision loss.
     Limitation: only ONE timestamp per calendar day even if Du restarted
     multiple times that day (backup() only acts once/day per file) --
     this script prints a WARNING when it cannot rule that out, rather
     than silently under-counting restarts.

  2. The CURRENTLY live process (if Du is running right now), queried via
     Win32_Process -- gives an exact, second-precision "last restart"
     instant for free, independent of the snapshot mechanism.

Cross-referencing both is what let this job discover TWO previously-unknown
restarts (2026-09-04T23:37:04Z and 2026-09-08T04:41:26Z) sitting inside what
three prior findings had been treating as one uniform "post-fix" window.

USAGE:
    python scripts/du_restart_history.py
    python scripts/du_restart_history.py --since 1788517496   # only show restarts after this epoch
    python scripts/du_restart_history.py --check-live         # also query the live process (Windows only,
                                                                 requires PowerShell on PATH)

This does not, and cannot, catch a restart that happened and fully completed
between two runs of THIS script on the same calendar day with no snapshot-
day boundary crossed and no live-process query bracketing it — for that,
narrow the causal-substrate accrual test's own `--since` cutoff to a
known-good regime boundary this script DID find, and re-run this script
again close to when you actually run the walk-forward test, not once at the
start of a multi-day wait.
"""
import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"C:\Nascence")
SNAP_DIR = ROOT / "data" / "_snapshots" / "daily"


def iso(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def snapshot_folder_restarts():
    """Return sorted list of (epoch_utc, day_str) from each daily snapshot folder's
    own filesystem creation time (Windows-only: uses PowerShell Get-Item for a
    reliable CreationTimeUtc; falls back to Path.stat().st_ctime, which on
    Windows IS creation time, if PowerShell is unavailable)."""
    if not SNAP_DIR.exists():
        return []
    days = sorted(p for p in SNAP_DIR.iterdir() if p.is_dir())
    out = []
    # Ask PowerShell to enumerate the directory itself (avoids fragile arg-passing
    # through -Command; this is the exact form validated by hand for this job).
    ps_script = (
        f"Get-ChildItem -LiteralPath '{SNAP_DIR}' -Directory | ForEach-Object {{ "
        "  $dto = [DateTimeOffset]::new($_.CreationTimeUtc, [TimeSpan]::Zero); "
        "  Write-Output ($_.Name + '|' + $dto.ToUnixTimeSeconds()) "
        "}"
    )
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True, text=True, timeout=30,
        )
        seen = set()
        for line in proc.stdout.splitlines():
            line = line.strip()
            if "|" not in line:
                continue
            name, epoch_str = line.rsplit("|", 1)
            try:
                epoch = float(epoch_str)
            except ValueError:
                continue
            seen.add(name)
            out.append((epoch, name))
        missing = {d.name for d in days} - seen
        if missing:
            print(f"WARNING: PowerShell query returned {len(out)} folder(s) but "
                  f"{len(missing)} folder(s) on disk were not matched: {sorted(missing)}",
                  file=sys.stderr)
    except Exception as e:
        print(f"WARNING: PowerShell creation-time query failed ({e}); "
              f"falling back to Path.stat().st_ctime (Windows: also creation time).",
              file=sys.stderr)
        for d in days:
            out.append((d.stat().st_ctime, d.name))
    out.sort(key=lambda t: t[0])
    return out


def live_process_start(name_substr="run_nascence.py"):
    """Query the currently-running Du process's creation time via WMI, if any.
    Returns (epoch_utc, pid, commandline) or None.

    J-1658 (F-2230): the WMI query is pre-filtered to Name='python.exe' OR
    Name='pythonw.exe' before the CommandLine match, not just a bare
    Where-Object over every process. Without that pre-filter, THIS FUNCTION'S
    OWN spawned "powershell -NoProfile -Command <ps_script>" subprocess has a
    CommandLine that (while the query is executing) itself contains the
    literal name_substr text -- it is embedded in ps_script via
    [regex]::Escape('{name_substr}') below -- so a bare query can match its
    own invocation and silently report itself as "LIVE process found", a
    different pid/timestamp every single call. Reproduced twice in direct
    succession, J-1626 2026-10-01 (F-2230), with zero real run_nascence.py
    process on the machine at the time (confirmed via a manual
    exclusion-filtered query) -- a clean false positive, not stale data.
    run_nascence.py is always launched via `& $PYTHON scripts\\run_nascence.py`
    ($PYTHON="python" on PATH) or pythonw for the composer window, never via
    powershell.exe directly (Nascence_Control_Panel.ps1 line 290/30; its own
    Get-PythonScript helper, lines 66-70, already pre-filters the identical
    way: `Get-WmiObject Win32_Process -Filter "Name='python.exe'"` before its
    own CommandLine match) -- so this pre-filter cannot hide a real restart,
    only the query's own powershell.exe self-match.
    """
    ps_script = (
        "Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='pythonw.exe'\" | "
        f"Where-Object {{ $_.CommandLine -match [regex]::Escape('{name_substr}') }} | "
        "ForEach-Object { "
        "  $dto = [DateTimeOffset]::new($_.CreationDate.ToUniversalTime(), [TimeSpan]::Zero); "
        "  Write-Output ($_.ProcessId.ToString() + '|' + $dto.ToUnixTimeSeconds().ToString() + '|' + $_.CommandLine) "
        "}"
    )
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True, text=True, timeout=30,
        )
        lines = [ln for ln in proc.stdout.strip().splitlines() if ln.strip()]
        if not lines:
            return None
        pid, epoch_str, cmdline = lines[0].split("|", 2)
        return float(epoch_str), pid, cmdline
    except Exception as e:
        print(f"WARNING: live-process query failed ({e})", file=sys.stderr)
        return None


def _report_live():
    live = live_process_start()
    if live:
        epoch, pid, cmdline = live
        print(f"LIVE process found: pid={pid}, started {epoch:.1f} ({iso(epoch)})")
        print(f"  cmdline: {cmdline.strip()}")
    else:
        print("No live run_nascence.py process found (or query failed / not on Windows).")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", type=float, default=None,
                     help="only print restarts with epoch >= this value")
    ap.add_argument("--check-live", action="store_true",
                     help="also query the currently-running Du process (if any)")
    ap.add_argument("--from-log", action="store_true",
                     help="J-1681: exact per-process lifetimes from data/nascence.log (scripts/du_lifetimes.py); "
                          "all other flags (--commit/--file/--at/--json/--all/--log ...) are forwarded to it")
    if "--from-log" in sys.argv[1:]:
        args, forward = ap.parse_known_args()      # --from-log: unrecognised flags belong to du_lifetimes
    else:
        args, forward = ap.parse_args(), []        # otherwise argument handling is exactly as before

    if args.from_log:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import du_lifetimes
        if args.since:
            forward += ["--since", str(args.since)]
        rc = du_lifetimes.main(forward)
        if args.check_live:
            print()
            _report_live()
        return rc

    restarts = snapshot_folder_restarts()
    if args.since:
        restarts = [(e, d) for e, d in restarts if e >= args.since]

    print("=" * 70)
    print("Du restart timeline (from data/_snapshots/daily/ folder creation times)")
    print("One entry per CALENDAR DAY a launch happened -- see this script's own")
    print("docstring: cannot rule out additional same-day restarts by itself.")
    print("=" * 70)
    for epoch, day in restarts:
        print(f"  {day}: {epoch:.1f}  ({iso(epoch)})")
    if not restarts:
        print("  (none in range)")

    if args.check_live:
        print()
        _report_live()


if __name__ == "__main__":
    sys.exit(main())
