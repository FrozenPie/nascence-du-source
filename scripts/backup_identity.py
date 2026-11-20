"""
Nascence — identity backup. 渡's selfhood (axiom.json: name, self-concept, autobiography)
is one corrupted write from gone. This snapshots axiom.json + the small identity/state files once a day;
retention is scripts/retention.py's snapshots rule (daily 14 d / Sundays 12 wk / monthly forever).
The memory DB is NOT copied here any more (J-1843, F-2476): scripts/backup_memory.py already writes a proper
sqlite .backup() copy of nascence.db to data/backups/ at every launch, and this module's second raw copy
was ~0.9 GB/day (7.4 GB total on 2026-10-06) of pure duplication. Runs automatically at every Du launch (hooked in run_nascence) or manually:
    python scripts/backup_identity.py
"""
import shutil, sys, time
from pathlib import Path

ROOT = Path(__file__).parent.parent
DEST = ROOT / "data" / "_snapshots" / "daily"
KEEP = 14   # legacy; the live rule is scripts/retention.py (D-0156)
# nascence.db deliberately absent (J-1843 / F-2476): data/backups/nascence_<stamp>.db (backup_memory.py) is
# the DB's backup, written every boot with the SQLite online-backup API. Do not re-add a raw shutil copy.
TARGETS = [ROOT / "data" / "identity" / "axiom.json",
           ROOT / "data" / "reading_state.json",
           ROOT / "data" / "subconscious_state.json",
           ROOT / "data" / "subconscious_state.patterns.json",   # J-2418: integration_patterns split out
           ROOT / "data" / "subconscious_state.patterns.delta.jsonl"]   # J-2432: the DELTA journal (D-0495 flip)


def _damaged(p: Path) -> str:
    """J-4427 / F-5128: '' when p may be snapshotted, else why not (empty, or every byte NUL as the 2026-11-20 crash
    left 19 files). Kept local (not imported from backup_memory) so this module still runs alone in a temp tree."""
    try:
        if p.stat().st_size == 0:
            return "empty (0 bytes)"
        with open(p, "rb") as f:
            while True:
                b = f.read(1 << 20)
                if not b:
                    return "all NUL"
                if b.strip(b"\x00"):
                    return ""
    except OSError as exc:
        return f"unreadable: {exc}"


def backup() -> str:
    day = time.strftime("%Y%m%d")
    d = DEST / day
    d.mkdir(parents=True, exist_ok=True)
    done = 0
    skipped: list = []
    for t in TARGETS:
        if t.exists():
            stamp = d / f"{t.name}"
            if not stamp.exists():            # one snapshot per day per file
                why = _damaged(t)
                if why:                       # J-4427: never let a wiped file become the day's snapshot
                    skipped.append(f"{t.name} ({why})")
                    continue
                shutil.copy2(t, stamp)
                done += 1
    # retention — D-0156 (2026-09-05): the 14-day hard delete moved to scripts/retention.py, which keeps every
    # day for 14 days, then Sundays for 12 weeks, then the 1st of each month, and QUARANTINES (data/_trash)
    # instead of deleting. No-op while retention.RETENTION_BOOT_ROTATE is False.
    moved: list = []
    try:
        sys.path.insert(0, str(ROOT))
        from scripts import retention
        moved = retention.boot_rotate("snapshots")
    except Exception:
        pass
    days = sorted([p for p in DEST.iterdir() if p.is_dir()])
    # "N day-dir(s) on disk" -- not "retained": that count is just len(dirs) after retention.py ran, not a
    # configured window (F-2476). The memory DB is in data/backups/ (backup_memory.py), not in these dirs.
    return (f"[backup] {day}: {done} new file(s) snapshotted ({len(days)} day-dir(s) on disk; "
            f"{len(moved)} quarantined; memory DB backed up separately by backup_memory.py)"
            + (f"; WARNING skipped damaged source: {', '.join(skipped)}" if skipped else ""))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(backup())
