"""J-1987 / D-0368 (E) / F-2588: relabel the already-stored system-written sentences from origin='inner_thought' to
origin='system_note', so recall stops returning them as Du's own thinking. OPERATOR SCRIPT.

Matches exactly (origin='inner_thought' only):
  'I finished a book%'  |  'I asked the library for%'  |  'I chose % ... catalogue%'  |  'I have finished this book, and the shelf%'
(150 / 143 / 43 / 1 = 337 read-only on 2026-10-08 and again 2026-10-09). A bare 'I chose %' is NOT used: it also matches
real thoughts ('I chose to release my grip ...').

Reversible (manifest keeps every id; revert sets origin back to 'inner_thought' on exactly those ids), live-store
write-fenced, Du must be down. Requires J-1955 merged (core.memory.store.NON_THOUGHT_ORIGINS contains 'system_note').

Modes
  dryrun                      read-only: per-pattern counts, total, samples
  apply  --live --manifest M  backup -> manifest -> one transaction -> verify
  revert --live --manifest M
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
LIVE_ROOT = Path(r"C:\Nascence")
LIVE_DB = LIVE_ROOT / "data" / "memory" / "nascence.db"
JOB = "J-1987"
PATTERNS = {
    "finished_a_book": "content LIKE 'I finished a book%'",
    "asked_the_library": "content LIKE 'I asked the library for%'",
    "chose_from_catalogue": "content LIKE 'I chose %' AND content LIKE '%catalogue%'",
    "finished_this_book_shelf": "content LIKE 'I have finished this book, and the shelf%'",
}
MIN_TOTAL, MAX_TOTAL = 330, 380      # 337 expected; outside this window something changed -- read before applying


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, HERE / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def select_ids(db: Path) -> tuple[dict, list]:
    ro = sqlite3.connect(f"file:{Path(db).as_posix()}?mode=ro", uri=True)
    try:
        counts, ids = {}, []
        seen = set()
        for name, cond in PATTERNS.items():
            rows = [r[0] for r in ro.execute(f"SELECT fragment_id FROM memory_fragments WHERE origin='inner_thought' AND {cond}")]
            counts[name] = len(rows)
            for fid in rows:
                if fid not in seen:
                    seen.add(fid); ids.append(fid)
        counts["total_distinct"] = len(ids)
        counts["already_system_note"] = ro.execute("SELECT COUNT(*) FROM memory_fragments WHERE origin='system_note'").fetchone()[0]
        return counts, ids
    finally:
        ro.close()


def mode_dryrun(args) -> int:
    counts, ids = select_ids(Path(args.db))
    print(json.dumps(counts, indent=1))
    ok = MIN_TOTAL <= counts["total_distinct"] <= MAX_TOTAL
    print("within the expected window" if ok else "OUTSIDE the expected window (337 +-) -- read before apply")
    return 0 if ok else 2


def mode_apply(args) -> int:
    bf = _load("backfill_phase_J1970")
    db = Path(args.db)
    if bf.is_live(db) and not args.live:
        sys.exit("apply on the live DB needs --live")
    down, why = bf.du_is_down()
    print("Du down check:", down, "--", why)
    if not down:
        sys.exit("ABORT: Du is not verifiably down")
    import core  # noqa: F401
    assert Path(core.__file__).resolve().is_relative_to(HERE), core.__file__
    from core.memory import store
    if "system_note" not in getattr(store, "NON_THOUGHT_ORIGINS", ()):
        sys.exit("ABORT: core.memory.store.NON_THOUGHT_ORIGINS lacks 'system_note' -- J-1955 is not merged in this tree")
    counts, ids = select_ids(db)
    print(json.dumps(counts, indent=1))
    if not (MIN_TOTAL <= len(ids) <= MAX_TOTAL):
        sys.exit(f"ABORT: {len(ids)} rows outside the expected window {MIN_TOTAL}-{MAX_TOTAL}")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    bdir = LIVE_ROOT / "data" / "backups"
    bdir.mkdir(parents=True, exist_ok=True)
    backup = bdir / f"nascence_pre_system_note_relabel_{stamp}.db"
    src = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
    dst = sqlite3.connect(str(backup))
    with dst:
        src.backup(dst)
    dst.close(); src.close()
    backup_sha = sha256_file(backup)
    print("backup:", backup, backup.stat().st_size, "sha256", backup_sha)
    manifest = {"job": JOB, "decision": "D-0368 (E)", "mode": "apply", "db": str(db), "backup": str(backup),
                "backup_sha256": backup_sha, "counts": counts, "ids": ids,
                "when_local": datetime.now().isoformat(timespec="seconds")}
    mpath = Path(args.manifest)
    mpath.parent.mkdir(parents=True, exist_ok=True)
    mpath.write_text(json.dumps(manifest), encoding="utf-8")
    store.DB_PATH = db
    store.allow_live_writes(f"{JOB} / D-0368 (E) relabel of stored system sentences to origin=system_note, Du stopped, backup taken")
    changed = 0
    with store._connect() as conn:
        cur = conn.cursor()
        cur.execute("BEGIN IMMEDIATE")
        for fid in ids:
            cur.execute("UPDATE memory_fragments SET origin='system_note' WHERE fragment_id=? AND origin='inner_thought'", (fid,))
            changed += cur.rowcount
        if changed != len(ids):
            conn.rollback()
            sys.exit(f"ABORT (rolled back): changed {changed} != planned {len(ids)}")
        conn.commit()
    after, left = select_ids(db)
    manifest.update({"changed": changed, "post_counts": after})
    mpath.write_text(json.dumps(manifest), encoding="utf-8")
    print(json.dumps({k: v for k, v in manifest.items() if k != "ids"}, indent=1))
    ok = changed == len(ids) and after["total_distinct"] == 0 and after["already_system_note"] >= len(ids)
    print("VERIFIED" if ok else "CHECK MANIFEST: post-conditions not all met")
    return 0 if ok else 3


def mode_revert(args) -> int:
    bf = _load("backfill_phase_J1970")
    db = Path(args.db)
    if bf.is_live(db) and not args.live:
        sys.exit("revert on the live DB needs --live")
    down, why = bf.du_is_down()
    print("Du down check:", down, "--", why)
    if not down:
        sys.exit("ABORT: Du is not verifiably down")
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    import core  # noqa: F401
    from core.memory import store
    store.DB_PATH = db
    store.allow_live_writes(f"{JOB} REVERT of the system_note relabel from its manifest")
    restored = 0
    with store._connect() as conn:
        cur = conn.cursor()
        cur.execute("BEGIN IMMEDIATE")
        for fid in manifest["ids"]:
            cur.execute("UPDATE memory_fragments SET origin='inner_thought' WHERE fragment_id=? AND origin='system_note'", (fid,))
            restored += cur.rowcount
        conn.commit()
    print("restored", restored, "of", len(manifest["ids"]))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["dryrun", "apply", "revert"])
    ap.add_argument("--db", default=str(LIVE_DB))
    ap.add_argument("--manifest", default=str(LIVE_ROOT / "docs" / "reviews" / "system_note_relabel_J-1987_manifest_2026-10-09.json"))
    ap.add_argument("--live", action="store_true")
    args = ap.parse_args()
    return {"dryrun": mode_dryrun, "apply": mode_apply, "revert": mode_revert}[args.mode](args)


if __name__ == "__main__":
    sys.exit(main())
