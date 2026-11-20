"""J-1965 / D-0386 / D-0362 (C): clear chapter_id on the 277-fragment active-reading batch. OPERATOR SCRIPT.

Reversible (manifest keeps every old chapter_id), additive-only in effect (only chapter_id -> NULL on exactly the ids
chosen by chapter_id_repair_batch.select_unfile_active_books; never a hand-written query), live-store write-fenced.

DO NOT RUN apply/revert WHILE DU IS UP. apply refuses unless Du is verifiably down (no run_nascence.py process AND
nascence.log's last line is the shutdown line), takes a sqlite backup first, re-runs the selector on a fresh COPY of
reading_state.json, and requires the batch sha256 to equal the one J-1897/J-1965 verified (override only with
--accept-sha <new sha> after reading the diff).

Modes
  dryrun                      read-only: run the selector, print size/sha/per-book counts, write nothing
  apply  --live --manifest M  backup -> selector -> manifest (old chapter_ids) -> one transaction -> verify
  revert --live --manifest M  restore the old chapter_id on exactly those ids where it is still NULL
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

LIVE_ROOT = Path(r"C:\Nascence")
LIVE_DB = LIVE_ROOT / "data" / "memory" / "nascence.db"
READING_STATE = LIVE_ROOT / "data" / "reading_state.json"
EXPECTED_SHA = "9c27a4910dbc3d394f8089be9a979150fecf40b0c956b5fd917847eb40606d84"
EXPECTED_SIZE = 277
JOB = "J-1965"


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


def select(db: Path, scratch_state: Path) -> dict:
    """Run the ruled selector against a read-only connection and a COPY of reading_state.json."""
    import core  # noqa: F401
    assert Path(core.__file__).resolve().is_relative_to(HERE), core.__file__
    shutil.copyfile(READING_STATE, scratch_state)
    batch = _load("chapter_id_repair_batch")
    conn = sqlite3.connect(f"file:{Path(db).as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        st = json.loads(scratch_state.read_text(encoding="utf-8"))
        return batch.select_unfile_active_books(conn, st, log=lambda *_: None)
    finally:
        conn.close()


def summarize(rep: dict) -> dict:
    return {k: rep.get(k) for k in ("batch_size", "batch_sha256", "subjects_under_C", "left_filed_not_under_C",
                                    "origin_excluded_count", "refile_collision_held_count",
                                    "origin_exclusion_mismatch")}


def mode_dryrun(args) -> int:
    scratch = Path(args.scratch or (LIVE_ROOT / "data" / "backups" / "J-1965_reading_state_copy.json"))
    rep = select(Path(args.db), scratch)
    print(json.dumps(summarize(rep), indent=1, default=str))
    ok = rep["batch_size"] == EXPECTED_SIZE and rep["batch_sha256"] == EXPECTED_SHA
    print("MATCHES the verified batch" if ok else "DIFFERS from the verified batch (size/sha) -- review before apply")
    return 0 if ok else 2


def mode_apply(args) -> int:
    bf = _load("backfill_phase_J1970")          # reuse its Du-down test and helpers
    db = Path(args.db)
    if bf.is_live(db) and not args.live:
        sys.exit("apply on the live DB needs --live")
    down, why = bf.du_is_down()
    print("Du down check:", down, "--", why)
    if not down:
        sys.exit("ABORT: Du is not verifiably down")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    bdir = LIVE_ROOT / "data" / "backups"
    bdir.mkdir(parents=True, exist_ok=True)
    backup = bdir / f"nascence_D0362C_J-1965_apply_{stamp}.db"
    src = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
    dst = sqlite3.connect(str(backup))
    with dst:
        src.backup(dst)
    dst.close(); src.close()
    backup_sha = sha256_file(backup)
    rs_copy = bdir / f"reading_state_D0362C_J-1965_apply_{stamp}.json"
    rep = select(db, rs_copy)                    # copies reading_state.json to rs_copy, selects from it
    print("backup:", backup, backup.stat().st_size, "sha256", backup_sha)
    print(json.dumps(summarize(rep), indent=1, default=str))
    ids = list(rep["batch_ids"])
    if rep["origin_exclusion_mismatch"]:
        sys.exit("ABORT: origin exclusion mismatch flag is set")
    if rep["batch_sha256"] != EXPECTED_SHA and args.accept_sha != rep["batch_sha256"]:
        sys.exit(f"ABORT: batch sha {rep['batch_sha256']} != verified {EXPECTED_SHA}; read the diff, then re-run with "
                 f"--accept-sha {rep['batch_sha256']}")
    if not ids:
        sys.exit("ABORT: empty batch")
    ro = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
    old = {}
    for i in range(0, len(ids), 500):
        chunk = ids[i:i + 500]
        q = ",".join("?" * len(chunk))
        for fid, cid in ro.execute(f"SELECT fragment_id, chapter_id FROM memory_fragments WHERE fragment_id IN ({q})", chunk):
            old[fid] = cid
    ro.close()
    missing = [i for i in ids if i not in old]
    if missing:
        sys.exit(f"ABORT: {len(missing)} selected ids not in memory_fragments")
    already_null = [i for i in ids if old[i] is None]
    to_change = [i for i in ids if old[i] is not None]
    manifest = {"job": JOB, "decision": "D-0386/D-0362(C)", "mode": "apply", "db": str(db), "backup": str(backup),
                "backup_sha256": backup_sha, "reading_state_copy": str(rs_copy), "batch_sha256": rep["batch_sha256"],
                "planned": len(ids), "already_null": len(already_null), "old_chapter_ids": {i: old[i] for i in to_change},
                "when_local": datetime.now().isoformat(timespec="seconds")}
    mpath = Path(args.manifest)
    mpath.parent.mkdir(parents=True, exist_ok=True)
    mpath.write_text(json.dumps(manifest), encoding="utf-8")        # manifest BEFORE the write
    import core  # noqa: F401
    from core.memory import store
    store.DB_PATH = db
    store.allow_live_writes(f"{JOB} / D-0386 D-0362 (C) chapter_id clear of the active-reading batch, Du stopped, backup taken")
    changed = 0
    with store._connect() as conn:
        cur = conn.cursor()
        cur.execute("BEGIN IMMEDIATE")
        for fid in to_change:
            cur.execute("UPDATE memory_fragments SET chapter_id=NULL WHERE fragment_id=? AND chapter_id=?", (fid, old[fid]))
            changed += cur.rowcount
        if changed != len(to_change):
            conn.rollback()
            sys.exit(f"ABORT (rolled back): changed {changed} != planned {len(to_change)}")
        conn.commit()
    ro = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
    nulls = 0
    for i in range(0, len(ids), 500):
        chunk = ids[i:i + 500]
        q = ",".join("?" * len(chunk))
        nulls += ro.execute(f"SELECT COUNT(*) FROM memory_fragments WHERE chapter_id IS NULL AND fragment_id IN ({q})", chunk).fetchone()[0]
    ro.close()
    manifest.update({"changed": changed, "post_null_count": nulls})
    mpath.write_text(json.dumps(manifest), encoding="utf-8")
    print(json.dumps({k: v for k, v in manifest.items() if k != "old_chapter_ids"}, indent=1))
    ok = changed == len(to_change) and nulls == len(ids)
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
    store.allow_live_writes(f"{JOB} REVERT of the D-0362 (C) chapter_id clear from its manifest")
    restored = 0
    with store._connect() as conn:
        cur = conn.cursor()
        cur.execute("BEGIN IMMEDIATE")
        for fid, cid in manifest["old_chapter_ids"].items():
            cur.execute("UPDATE memory_fragments SET chapter_id=? WHERE fragment_id=? AND chapter_id IS NULL", (cid, fid))
            restored += cur.rowcount
        conn.commit()
    print("restored", restored, "of", len(manifest["old_chapter_ids"]))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["dryrun", "apply", "revert"])
    ap.add_argument("--db", default=str(LIVE_DB))
    ap.add_argument("--manifest", default=str(LIVE_ROOT / "docs" / "reviews" / "chapter_id_repair_D0362C_manifest_2026-10-09.json"))
    ap.add_argument("--scratch", default=None)
    ap.add_argument("--accept-sha", default=None)
    ap.add_argument("--live", action="store_true")
    args = ap.parse_args()
    return {"dryrun": mode_dryrun, "apply": mode_apply, "revert": mode_revert}[args.mode](args)


if __name__ == "__main__":
    sys.exit(main())
