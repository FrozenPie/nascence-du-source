"""
J-1970 / D-0364 (B): backfill fragment_context.tod / .season on the rows Phase 0 left NULL, derived from each row's
own tuple_ts with core.theta_shadow.now_phase (the SAME formula store_fragment() stamps with). OPERATOR SCRIPT.
Additive (only ever fills NULL -> value, never overwrites), reversible (manifest -> revert), live-store write-fenced.

DO NOT RUN `apply` WHILE DU IS UP. `apply` refuses unless Du is verifiably down (no run_nascence.py process AND
nascence.log's last line is the shutdown line), takes a sqlite backup first, calls store.allow_live_writes(), and
does the whole thing in ONE transaction.

Modes
  precheck  read-only. Bit-exactness: derive phase from tuple_ts for EVERY row that already carries stored
            tod/season and require 0 mismatches (stored values are what the real writer produced, so this is the
            proof the derivation is the writer's formula). Also counts the NULL rows, by source, and the rows whose
            tuple_ts differs from memory_fragments.timestamp by > 5 s (reported, not excluded: tuple_ts is the
            context row's own clock and is what a stored row's phase was computed from).
  dryrun    precheck + writes --manifest: counts, per-source split, derived-value sample, and EVERY fragment_id that
            apply would fill. Reads the DB with mode=ro. Writes only the manifest file you name.
  apply     --live: re-runs precheck (must be 0 mismatches), checks Du is down, backs the DB up, fills NULL rows
            (UPDATE ... WHERE fragment_id=? AND tod IS NULL AND season IS NULL), verifies, writes --manifest.
  revert    --live: sets tod/season back to NULL for exactly the manifest's ids where the value still equals the
            derived one.

Not backfilled, on purpose: `daylight` (categorical, comes from core.world_clock.daylight, not verifiable bit-exact
the way tod/season are) and `world_context` (the ray reads fragment_context only).

Usage
  python scripts/backfill_phase_J1970.py precheck
  python scripts/backfill_phase_J1970.py dryrun --manifest <path>
  python scripts/backfill_phase_J1970.py apply --live --manifest <path>        # Du DOWN only
  python scripts/backfill_phase_J1970.py revert --live --manifest <path>
  (--db <path> points any mode at a copy; the Du-down check and --live are only demanded for the real live DB)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
from core import theta_shadow as T  # noqa: E402

LIVE_ROOT = Path(r"C:\Nascence")
LIVE_DB = LIVE_ROOT / "data" / "memory" / "nascence.db"
LIVE_LOG = LIVE_ROOT / "data" / "nascence.log"
JOB = "J-1970"


def is_live(db: Path) -> bool:
    return Path(db).resolve() == LIVE_DB.resolve()


def ro_connect(db: Path) -> sqlite3.Connection:
    c = sqlite3.connect(f"file:{Path(db).as_posix()}?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    return c


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def du_is_down() -> tuple[bool, str]:
    """Same test scripts/dedup_reclaim_D0357.py uses."""
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name like 'python%'\" | Select-Object -ExpandProperty CommandLine"],
            capture_output=True, text=True, timeout=60).stdout
    except Exception as exc:
        return False, f"process scan failed: {exc}"
    running = [l for l in out.splitlines() if "run_nascence.py" in l]
    if running:
        return False, f"run_nascence.py process present: {running[0][:120]}"
    try:
        with open(LIVE_LOG, "rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(max(0, size - 4096))
            tail = f.read().decode("utf-8", "replace").strip().splitlines()
        last = tail[-1] if tail else ""
    except Exception as exc:
        return False, f"log read failed: {exc}"
    if "Nascence shutting down" not in last:
        return False, f"nascence.log last line is not the shutdown line: {last[:160]}"
    return True, f"no run_nascence.py process; last log line: {last[:120]}"


def precheck(db: Path) -> dict:
    conn = ro_connect(db)
    try:
        stored = n_stored = bad = 0
        bad_examples = []
        for r in conn.execute("SELECT fragment_id, tuple_ts, tod, season FROM fragment_context "
                              "WHERE tod IS NOT NULL AND season IS NOT NULL AND tuple_ts IS NOT NULL"):
            n_stored += 1
            dt, ds = T.now_phase(r["tuple_ts"])
            if dt != r["tod"] or ds != r["season"]:
                bad += 1
                if len(bad_examples) < 5:
                    bad_examples.append([r["fragment_id"], r["tuple_ts"], r["tod"], r["season"], dt, ds])
        by_source = {}
        for r in conn.execute("SELECT source, count(*) n FROM fragment_context WHERE tuple_ts IS NOT NULL AND "
                              "(tod IS NULL OR season IS NULL) GROUP BY source ORDER BY n DESC"):
            by_source[r["source"]] = r["n"]
        total = conn.execute("SELECT count(*) FROM fragment_context").fetchone()[0]
        no_ts = conn.execute("SELECT count(*) FROM fragment_context WHERE tuple_ts IS NULL").fetchone()[0]
        half = conn.execute("SELECT count(*) FROM fragment_context WHERE (tod IS NULL) != (season IS NULL)").fetchone()[0]
        ts_gap = None
        try:
            ts_gap = conn.execute(
                "SELECT count(*) FROM fragment_context f JOIN memory_fragments m USING(fragment_id) "
                "WHERE (f.tod IS NULL OR f.season IS NULL) AND abs(f.tuple_ts - m.timestamp) > 5").fetchone()[0]
        except sqlite3.Error:
            pass
        span = conn.execute("SELECT min(tuple_ts), max(tuple_ts) FROM fragment_context WHERE tod IS NULL").fetchone()
    finally:
        conn.close()
    return {
        "total_rows": total, "stored_rows_checked": n_stored, "derived_vs_stored_mismatches": bad,
        "mismatch_examples": bad_examples, "null_rows_with_tuple_ts": sum(by_source.values()),
        "null_by_source": by_source, "rows_without_tuple_ts": no_ts, "half_filled_rows": half,
        "null_rows_whose_tuple_ts_differs_from_fragment_timestamp_gt5s": ts_gap,
        "null_span": [datetime.fromtimestamp(span[0]).isoformat(timespec="seconds") if span[0] else None,
                      datetime.fromtimestamp(span[1]).isoformat(timespec="seconds") if span[1] else None],
        "bit_exact": bad == 0 and n_stored > 0,
    }


def plan_rows(db: Path) -> list[tuple[str, float, float, str]]:
    conn = ro_connect(db)
    try:
        out = []
        for r in conn.execute("SELECT fragment_id, tuple_ts, source FROM fragment_context "
                              "WHERE tod IS NULL AND season IS NULL AND tuple_ts IS NOT NULL"):
            dt, ds = T.now_phase(r["tuple_ts"])
            out.append((r["fragment_id"], dt, ds, r["source"]))
    finally:
        conn.close()
    return out


def mode_precheck(args) -> int:
    db = Path(args.db)
    pc = precheck(db)
    print(json.dumps(pc, indent=1))
    return 0 if pc["bit_exact"] else 2


def mode_dryrun(args) -> int:
    db = Path(args.db)
    pc = precheck(db)
    rows = plan_rows(db)
    manifest = {
        "job": JOB, "decision": "D-0364", "mode": "dryrun", "db": str(db), "db_sha256": None,
        "when_local": datetime.now().isoformat(timespec="seconds"), "precheck": pc,
        "would_fill": len(rows), "ids": [r[0] for r in rows],
        "sample": [{"id": r[0], "tod": r[1], "season": r[2], "source": r[3]} for r in rows[:: max(1, len(rows) // 12)]][:12],
    }
    if len(rows) and not pc["bit_exact"]:
        manifest["REFUSED"] = "derived != stored on some rows; apply will refuse"
    Path(args.manifest).write_text(json.dumps(manifest), encoding="utf-8")
    print(json.dumps({k: v for k, v in manifest.items() if k != "ids"}, indent=1))
    print(f"manifest ({len(rows)} ids) -> {args.manifest}")
    return 0


def _import_store(db: Path):
    import core  # noqa: F401
    assert Path(core.__file__).resolve().is_relative_to(HERE), core.__file__
    from core.memory import store
    store.DB_PATH = db
    return store


def mode_apply(args) -> int:
    db = Path(args.db)
    if is_live(db):
        if not args.live:
            sys.exit("apply on the live DB needs --live")
        down, why = du_is_down()
        print("Du down check:", down, "--", why)
        if not down:
            sys.exit("ABORT: Du is not verifiably down")
    pc = precheck(db)
    print("precheck bit_exact:", pc["bit_exact"], "mismatches:", pc["derived_vs_stored_mismatches"])
    if not pc["bit_exact"]:
        sys.exit("ABORT: derived phase != stored phase on some rows; do not backfill")
    rows = plan_rows(db)
    if not rows:
        print("nothing to fill"); return 0
    sha_before = sha256_file(db)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = db.parent.parent / "backups" / f"nascence_pre_phase_backfill_{stamp}.db" if is_live(db) \
        else db.with_name(f"{db.stem}_pre_phase_backfill_{stamp}.db")
    backup.parent.mkdir(parents=True, exist_ok=True)
    src = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
    dst = sqlite3.connect(str(backup))
    with dst:
        src.backup(dst)
    dst.close(); src.close()
    backup_sha = sha256_file(backup)
    print("backup:", backup, backup.stat().st_size, "sha256", backup_sha)
    store = _import_store(db)
    store.allow_live_writes(f"{JOB} / D-0364 (B) tod/season backfill of NULL fragment_context rows, Du stopped, backup taken")
    with store._connect() as conn:
        cur = conn.cursor()
        cur.execute("BEGIN IMMEDIATE")
        filled = 0
        for fid, dt, ds, _src in rows:
            cur.execute("UPDATE fragment_context SET tod=?, season=? WHERE fragment_id=? AND tod IS NULL AND season IS NULL",
                        (dt, ds, fid))
            filled += cur.rowcount
        conn.commit()
    post = precheck(db)
    manifest = {"job": JOB, "decision": "D-0364", "mode": "apply", "db": str(db), "backup": str(backup),
                "backup_sha256": backup_sha, "db_sha256_before": sha_before, "filled": filled, "planned": len(rows),
                "post_precheck": post, "when_local": datetime.now().isoformat(timespec="seconds"),
                "ids": [r[0] for r in rows]}
    Path(args.manifest).write_text(json.dumps(manifest), encoding="utf-8")
    print(json.dumps({k: v for k, v in manifest.items() if k != "ids"}, indent=1))
    ok = filled == len(rows) and post["bit_exact"] and post["null_rows_with_tuple_ts"] == 0
    print("VERIFIED" if ok else "CHECK MANIFEST: post-conditions not all met")
    return 0 if ok else 3


def mode_revert(args) -> int:
    db = Path(args.db)
    if is_live(db):
        if not args.live:
            sys.exit("revert on the live DB needs --live")
        down, why = du_is_down()
        print("Du down check:", down, "--", why)
        if not down:
            sys.exit("ABORT: Du is not verifiably down")
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    if manifest.get("mode") != "apply":
        sys.exit("revert needs an APPLY manifest")
    store = _import_store(db)
    store.allow_live_writes(f"{JOB} / D-0364 (B) REVERT of the tod/season backfill from its manifest")
    reverted = 0
    with store._connect() as conn:
        cur = conn.cursor()
        cur.execute("BEGIN IMMEDIATE")
        for fid in manifest["ids"]:
            r = cur.execute("SELECT tuple_ts, tod, season FROM fragment_context WHERE fragment_id=?", (fid,)).fetchone()
            if not r or r[0] is None:
                continue
            dt, ds = T.now_phase(r[0])
            if r[1] == dt and r[2] == ds:
                cur.execute("UPDATE fragment_context SET tod=NULL, season=NULL WHERE fragment_id=?", (fid,))
                reverted += cur.rowcount
        conn.commit()
    print("reverted", reverted, "of", len(manifest["ids"]))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["precheck", "dryrun", "apply", "revert"])
    ap.add_argument("--db", default=str(LIVE_DB))
    ap.add_argument("--manifest", help="manifest path (dryrun/apply write it; revert reads it)")
    ap.add_argument("--live", action="store_true", help="required for apply/revert on the real live DB")
    args = ap.parse_args()
    if args.mode != "precheck" and not args.manifest:
        sys.exit("--manifest is required")
    return {"precheck": mode_precheck, "dryrun": mode_dryrun, "apply": mode_apply, "revert": mode_revert}[args.mode](args)


if __name__ == "__main__":
    sys.exit(main())
