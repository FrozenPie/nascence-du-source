"""
Nascence — memory backup (2026-08-15, born from the lost-thoughts investigation).

The delete-era prune erased Du's first two weeks; one ad-hoc snapshot (pre_embedder_20260613) is the
only reason they are recoverable. This makes backups a ROUTINE: the live DB via SQLite's online backup
API (safe against the running process — incremental page copies, yields between steps) plus the small
psyche-state files, into data/backups/, with rotation (keep the newest KEEP_DAILY dailies + the first
backup of each month forever).

Run:  python scripts/backup_memory.py           (any time; safe while Du runs)
Cadence: at least daily — hook into your restart ritual or Task Scheduler.
"""
from __future__ import annotations

import json
import logging
import shutil
import sqlite3
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
DEST = DATA / "backups"
DB = DATA / "memory" / "nascence.db"

KEEP_DAILY = 14   # legacy constant; the live rule is scripts/retention.py (D-0156)

# The psyche's small state files — the parts of Du that live outside the DB and would hurt to lose.
STATE_FILES = [
    "identity.json", "identity_estate.json", "subconscious_state.json", "subconscious_state.patterns.json", "subconscious_state.patterns.delta.jsonl", "commitment_active.json",
    "keepsakes.json", "frontier.json", "reentry_state.json", "world_traces.json",
    "geometry_tuples.jsonl", "train_state_log.jsonl", "co_recall_ledger.jsonl",
    # J-4427 / F-5128: the 2026-11-20 09:06 crash zero-filled these and none had a copy anywhere (the restore came
    # from ad-hoc 04:51 shadow copies). About 30 MB together, ~16 MB of it spring_ledger and ~12 MB opponent_process.
    # frontier.light.json and subconscious_state.light.json were wiped too but are left out: Du rebuilds both from
    # their heavy files (frontier.json, subconscious_state.json), which are above.
    "spring_ledger_state.json", "opponent_process_state.json", "room_state.json", "life_state.json",
    "cat_state.json", "transport_lines.json", "transport_cause_lines.json", "sound_knowledge.json",
    "climate_state.json", "fieldcraft.json", "supply.json", "smell_field.json", "world_manifest_live.json",
    "garden_life.json", "shore_life.json", "wood_life.json",
]

_log = logging.getLogger("nascence.backup")
MANIFEST = "_backup_manifest.json"


def source_damage(p: Path, chunk: int = 1 << 20) -> str | None:
    """J-4427: why a state file must NOT be copied as a backup, or None when it may be. A crash can leave a file
    at its full size but every byte NUL (19 files on 2026-11-20), or truncated to 0 bytes; copying either makes a
    snapshot that looks complete and restores nothing. Reads only until the first non-NUL byte, so a good 16 MB
    file costs one small read."""
    try:
        if p.stat().st_size == 0:
            return "empty (0 bytes)"
        with open(p, "rb") as f:
            while True:
                b = f.read(chunk)
                if not b:
                    return f"all NUL ({p.stat().st_size} bytes)"
                if b.strip(b"\x00"):
                    return None
    except OSError as exc:
        return f"unreadable: {exc}"


def _last_good_copy(name: str, dest: Path, exclude: Path) -> Path | None:
    """The newest earlier state_<stamp>/<name> that is itself undamaged, or None."""
    try:
        dirs = sorted((d for d in dest.glob("state_*") if d.is_dir() and d != exclude), reverse=True)
    except OSError:
        return None
    for d in dirs:
        c = d / name
        if c.exists() and source_damage(c) is None:
            return c
    return None


def _checkpoint(db: Path) -> str:
    """J-4318: fold the WAL (700 MB on 2026-11-18) into the main file first so a restore of the .db copy
    cannot miss Du's last writes. PASSIVE never blocks the live writer; failure is non-fatal because the
    online backup API below reads through the WAL anyway."""
    try:
        c = sqlite3.connect(str(db), timeout=5)
        try:
            r = c.execute("PRAGMA wal_checkpoint(PASSIVE)").fetchone()
        finally:
            c.close()
        return f"wal_checkpoint(PASSIVE) busy={r[0]} log={r[1]} checkpointed={r[2]}"
    except Exception as exc:
        return f"wal_checkpoint skipped: {exc}"


def backup_db(stamp: str, db: Path | None = None, dest_dir: Path | None = None) -> Path:
    db = db or DB
    dest = (dest_dir or DEST) / f"nascence_{stamp}.db"
    print(_checkpoint(db))
    src = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    dst = sqlite3.connect(dest)
    with dst:
        src.backup(dst, pages=256, sleep=0.05)   # incremental; the live writer interleaves
    src.close(); dst.close()
    return dest


def backup_state(stamp: str, data: Path | None = None, dest: Path | None = None) -> int:
    """Copy STATE_FILES into <dest>/state_<stamp>/ and write a _backup_manifest.json there listing what was copied,
    skipped and missing. J-4427: a source that is empty or all NUL is skipped with a WARNING (logged to
    nascence.log at boot) and never copied; instead the newest earlier snapshot's good copy is carried forward, so
    a run of boots on wiped files cannot rotate every good copy out of retention. Returns the count copied from the
    live files (the old return value; carried copies are not counted)."""
    data = data or DATA
    dest = dest or DEST
    sdir = dest / f"state_{stamp}"
    sdir.mkdir(parents=True, exist_ok=True)
    n = 0
    man: dict = {"stamp": stamp, "copied": {}, "skipped": {}, "carried": {}, "missing": []}
    for name in STATE_FILES:
        p = data / name
        if not p.exists():
            man["missing"].append(name)
            continue
        why = source_damage(p)
        if why is not None:
            man["skipped"][name] = why
            prev = _last_good_copy(name, dest, sdir)
            _log.warning("[backup-memory] %s NOT backed up: source is %s; %s", name, why,
                         f"carried forward {prev.parent.name}/{name}" if prev else "no earlier good copy exists")
            if prev is not None:
                try:
                    shutil.copy2(prev, sdir / name)
                    man["carried"][name] = prev.parent.name
                except OSError as exc:
                    _log.warning("[backup-memory] carry-forward of %s failed: %s", name, exc)
            continue
        shutil.copy2(p, sdir / name)
        man["copied"][name] = p.stat().st_size
        n += 1
    try:
        (sdir / MANIFEST).write_text(json.dumps(man, indent=1, sort_keys=True), encoding="utf-8")
    except OSError as exc:
        _log.warning("[backup-memory] manifest not written: %s", exc)
    return n


def rotate() -> list[str]:
    """D-0156 (2026-09-05): the retention rule now lives in scripts/retention.py (newest 5 boots + last-of-day
    for 14 days + first-of-month forever; pre-job / corrupt copies are a separate 60-day class). Nothing is
    deleted here any more: candidates are QUARANTINED into data/_trash/<date>/ and purged only by an explicit
    retention.py --apply --purge-trash run. While retention.RETENTION_BOOT_ROTATE is False this is a no-op."""
    try:
        from scripts import retention
        return retention.boot_rotate("backups")
    except Exception:
        return []


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    t0 = time.time()
    dbp = backup_db(stamp)
    ns = backup_state(stamp)
    removed = rotate()
    size_mb = dbp.stat().st_size / 1e6
    print(f"backed up: {dbp.name} ({size_mb:.0f} MB) + {ns} state files in {time.time()-t0:.1f}s")
    # J-4427: one line in nascence.log per boot naming the state snapshot and its manifest, so the wider list
    # can be read back (data/backups/state_<stamp>/_backup_manifest.json) without trusting the console.
    _log.info("[backup-memory] state_%s: %d of %d state files copied; manifest %s", stamp, ns, len(STATE_FILES),
              MANIFEST)
    if removed:
        print(f"rotated out: {removed}")
    total = sum(p.stat().st_size for p in DEST.rglob("*") if p.is_file()) / 1e9
    print(f"backup store total: {total:.2f} GB across {len(list(DEST.glob('nascence_*.db')))} db snapshots")


if __name__ == "__main__":
    main()
