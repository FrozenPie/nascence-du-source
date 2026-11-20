"""
J-3266 / D-0657 -- add memory_fragments.content_hash + idx_origin_content_hash to a Nascence memory DB and backfill the
hash for every row that does not have one yet. OFFLINE ONLY: run with Du down (it refuses while any python process whose
command line contains run_nascence.py exists). ADDITIVE ONLY: it adds one nullable column, one index, and fills the
column. It never changes content, never deletes, never rewrites any other column.

  python scripts/apply_J-3266_content_hash_backfill.py                       # DRY RUN (default): counts + sha256 of the target rows, writes nothing
  python scripts/apply_J-3266_content_hash_backfill.py --write               # add column + index if missing, then backfill in batches
  python scripts/apply_J-3266_content_hash_backfill.py --db PATH             # another DB (default: the live data/memory/nascence.db)
  python scripts/apply_J-3266_content_hash_backfill.py --write --batch 500   # rows per transaction (default 500; small = short write locks)
  python scripts/apply_J-3266_content_hash_backfill.py --write --max-rows N  # stop after N rows (resume later: just run it again)

Hash: BLAKE2b-128 hex of the exact UTF-8 content (core/memory/content_hash.py, the same function the writer and the
reader use). Resumable and idempotent: the targets are exactly the rows whose content_hash IS NULL, found through the
(origin, content_hash) index (index-only: an already-hashed row is never even read), each batch is its own short
transaction guarded by `content_hash IS NULL`, so an interrupted run loses at most one batch and a finished run finds
nothing to do (second run: 0 targets, DB unchanged).

Output (printed): rows before/after, NULL-hash rows before/after, the sha256 of the targeted rows' (fragment_id, content)
BEFORE and AFTER (equal => content untouched), the number of stored hashes that do not equal a fresh recompute (must be
0), elapsed seconds and rows/s. `--verify` is a read-only pass that recomputes EVERY stored hash and reports mismatches
(a stale hash can arise if some writer UPDATEs content without clearing content_hash: core/activity_memory.py,
core/refinery.py and core/study_note.py do, on non-dedup origins).

Restore = copy the pre-run DB file back (backups/nascence.db.pre_waveC_20261105 holds the pre-wave-C state); the column
and index are harmless to leave in place.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
DEFAULT_DB = ROOT / "data" / "memory" / "nascence.db"
INDEX_NAME = "idx_origin_content_hash"


def _content_hash(content):
    from core.memory.content_hash import content_hash        # the ONE definition (writer, reader, this script)
    return content_hash(content)


def du_is_up() -> list:
    """Return a list of 'pid: command line' for python processes running run_nascence.py. Fail CLOSED: if the process
    list cannot be read, raise (the caller refuses)."""
    me = os.getpid()
    out = []
    if os.name == "nt":
        ps = ("Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^pythonw?[0-9.]*\\.exe$' -and "
              "$_.CommandLine -like '*run_nascence.py*' } | ForEach-Object { \"$($_.ProcessId): $($_.CommandLine)\" }")
        r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
                           capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            raise RuntimeError(f"could not list processes: {r.stderr.strip()[:200]}")
        lines = [ln.strip() for ln in r.stdout.splitlines() if ln.strip()]
    else:
        r = subprocess.run(["ps", "-eo", "pid,args"], capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            raise RuntimeError(f"could not list processes: {r.stderr.strip()[:200]}")
        lines = [ln.strip() for ln in r.stdout.splitlines() if "run_nascence.py" in ln]
    for ln in lines:
        pid = ln.split(":", 1)[0].split(" ", 1)[0]
        if pid.isdigit() and int(pid) == me:
            continue
        out.append(ln)
    return out


def _cols(conn) -> set:
    return {r[1] for r in conn.execute("PRAGMA table_info(memory_fragments)")}


def _has_index(conn) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='index' AND name=?", (INDEX_NAME,)).fetchone() is not None


def _counts(conn):
    total = conn.execute("SELECT COUNT(*) FROM memory_fragments").fetchone()[0]
    if "content_hash" in _cols(conn):
        nulls = conn.execute("SELECT COUNT(*) FROM memory_fragments WHERE content_hash IS NULL").fetchone()[0]
    else:
        nulls = total
    return total, nulls


def _target_rowids(conn, batch: int):
    """Yield lists of rowids of rows that still need a hash, in a stable order, WITHOUT holding a read transaction open
    across the caller's writes (each fetch is its own short SELECT, resumed by a (origin, rowid) cursor)."""
    cols = _cols(conn)
    if "content_hash" in cols and _has_index(conn):
        origins = [r[0] for r in conn.execute("SELECT DISTINCT origin FROM memory_fragments ORDER BY origin")]
        for org in origins:
            last = -1
            while True:
                rows = conn.execute(
                    "SELECT rowid FROM memory_fragments WHERE origin=? AND content_hash IS NULL AND rowid>? "
                    "ORDER BY rowid LIMIT ?", (org, last, batch)).fetchall()
                if not rows:
                    break
                ids = [r[0] for r in rows]
                last = ids[-1]
                yield ids
    else:                                                      # no column/index yet (dry run on an unmigrated DB)
        has_col = "content_hash" in cols
        last = -1
        while True:
            q = ("SELECT rowid FROM memory_fragments WHERE rowid>? " + ("AND content_hash IS NULL " if has_col else "")
                 + "ORDER BY rowid LIMIT ?")
            rows = conn.execute(q, (last, batch)).fetchall()
            if not rows:
                break
            ids = [r[0] for r in rows]
            last = ids[-1]
            yield ids


def _read_rows(conn, ids):
    ph = ",".join("?" * len(ids))
    got = {r[0]: (r[1], r[2]) for r in conn.execute(
        f"SELECT rowid, fragment_id, content FROM memory_fragments WHERE rowid IN ({ph})", ids)}
    return [(rid, *got[rid]) for rid in ids if rid in got]


class _RowsSha:
    """sha256 over the targeted rows' (fragment_id, content), independent of the ORDER the rows were visited in (a dry
    run on an unmigrated DB walks by rowid, a migrated one walks by origin): one digest per row, combined in rowid order."""

    def __init__(self):
        self._d = {}

    def feed(self, rowid, fragment_id, content):
        h = hashlib.sha256()
        h.update(str(fragment_id).encode("utf-8", "surrogatepass"))
        h.update(bytes([0]))
        h.update(str(content).encode("utf-8", "surrogatepass"))
        self._d[rowid] = h.digest()

    def hexdigest(self):
        h = hashlib.sha256()
        for rid in sorted(self._d):
            h.update(self._d[rid])
        return h.hexdigest()


def run(db: Path, write: bool, batch: int = 500, max_rows: int | None = None, check_process: bool = True,
        out=print) -> dict:
    if not db.exists():
        raise SystemExit(f"{db}: no such file, refusing")
    if check_process:
        try:
            up = du_is_up()
        except Exception as exc:
            raise SystemExit(f"REFUSING: cannot tell whether Du is up ({exc})")
        if up:
            raise SystemExit("REFUSING: Du appears to be up (run_nascence.py): " + " | ".join(up)
                             + "\nShut Du down first; this backfill is offline-only.")
    t_start = time.time()
    conn = sqlite3.connect(str(db), timeout=60.0, isolation_level=None)       # autocommit: we BEGIN/COMMIT ourselves
    try:
        conn.execute("PRAGMA busy_timeout=60000")
        if conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='memory_fragments'").fetchone() is None:
            raise SystemExit(f"{db}: no memory_fragments table -- not a Nascence memory DB, refusing")
        total_b, null_b = _counts(conn)
        had_col = "content_hash" in _cols(conn)
        had_idx = _has_index(conn)
        out(f"db: {db}  ({db.stat().st_size / 1e6:.1f} MB)  mode: {'WRITE' if write else 'DRY RUN'}")
        out(f"rows before: {total_b}   NULL content_hash before: {null_b}   column present: {had_col}   index present: {had_idx}")

        if write:
            if not had_col:
                conn.execute("ALTER TABLE memory_fragments ADD COLUMN content_hash TEXT")
                out("added column content_hash (metadata-only)")
            if not had_idx:
                t0 = time.time()
                conn.execute(f"CREATE INDEX IF NOT EXISTS {INDEX_NAME} ON memory_fragments(origin, content_hash)")
                out(f"created {INDEX_NAME} in {time.time() - t0:.1f}s")

        # pass 1: read the targets (and, in WRITE mode, hash + update them in short transactions)
        sha_before = _RowsSha()
        target_ids: list = []
        done = 0
        t_loop = time.time()
        for ids in _target_rowids(conn, batch):
            if max_rows is not None and done >= max_rows:
                break
            if max_rows is not None:
                ids = ids[: max_rows - done]
            rows = _read_rows(conn, ids)
            upd = []
            for rid, fid, content in rows:
                sha_before.feed(rid, fid, content)
                target_ids.append(rid)
                if write:
                    upd.append((_content_hash(content), rid))
            if write and upd:
                conn.execute("BEGIN IMMEDIATE")
                try:
                    conn.executemany("UPDATE memory_fragments SET content_hash=? WHERE rowid=? AND content_hash IS NULL", upd)
                    conn.execute("COMMIT")
                except Exception:
                    conn.execute("ROLLBACK")
                    raise
            done += len(rows)
            if done % (batch * 20) < len(rows):
                out(f"  ... {done} rows ({done / max(time.time() - t_loop, 1e-9):.0f} rows/s)")
        loop_s = time.time() - t_loop

        # pass 2: re-read the same rows -- content must be byte-identical (sha) and every stored hash must recompute
        sha_after = _RowsSha()
        mismatches = 0
        if write:
            for i in range(0, len(target_ids), batch):
                ids = target_ids[i:i + batch]
                ph = ",".join("?" * len(ids))
                got = {r[0]: (r[1], r[2], r[3]) for r in conn.execute(
                    f"SELECT rowid, fragment_id, content, content_hash FROM memory_fragments WHERE rowid IN ({ph})", ids)}
                for rid in ids:
                    fid, content, stored = got[rid]
                    sha_after.feed(rid, fid, content)
                    if stored != _content_hash(content):
                        mismatches += 1
            try:
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            except Exception:
                pass
        total_a, null_a = _counts(conn)
        res = {"db": str(db), "write": write, "rows_before": total_b, "rows_after": total_a,
               "null_before": null_b, "null_after": null_a, "targets": len(target_ids),
               "sha256_targets_before": sha_before.hexdigest(),
               "sha256_targets_after": sha_after.hexdigest() if write else None,
               "hash_mismatches": mismatches if write else None, "loop_seconds": round(loop_s, 2),
               "rows_per_s": round(done / loop_s, 1) if loop_s > 0 and done else None,
               "total_seconds": round(time.time() - t_start, 2)}
        out(f"rows after: {total_a}   NULL content_hash after: {null_a}")
        out(f"target rows: {len(target_ids)}   sha256(targets, fragment_id+content) before: {res['sha256_targets_before']}")
        if write:
            out(f"                                                         after : {res['sha256_targets_after']}"
                f"   {'IDENTICAL' if res['sha256_targets_after'] == res['sha256_targets_before'] else 'DIFFERENT -- INVESTIGATE'}")
            out(f"stored hashes that differ from a fresh recompute: {mismatches}")
            out(f"backfill loop {loop_s:.1f}s ({res['rows_per_s']} rows/s); total {res['total_seconds']}s; db now {db.stat().st_size / 1e6:.1f} MB")
        else:
            out(f"dry run: would hash {len(target_ids)} rows (and add the column/index if missing); nothing written")
        return res
    finally:
        conn.close()


def verify(db: Path, batch: int = 2000, out=print) -> dict:
    """Read-only: recompute every stored hash; report NULLs and stale/wrong hashes."""
    conn = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True, timeout=60.0)
    try:
        if "content_hash" not in _cols(conn):
            out("no content_hash column: nothing to verify")
            return {"column": False}
        total = nulls = bad = 0
        bad_by_origin: dict = {}
        last = -1
        while True:
            rows = conn.execute("SELECT rowid, origin, content, content_hash FROM memory_fragments WHERE rowid>? "
                                "ORDER BY rowid LIMIT ?", (last, batch)).fetchall()
            if not rows:
                break
            last = rows[-1][0]
            for rid, org, content, stored in rows:
                total += 1
                if stored is None:
                    nulls += 1
                elif stored != _content_hash(content):
                    bad += 1
                    bad_by_origin[org] = bad_by_origin.get(org, 0) + 1
        out(f"verify: rows {total}  NULL {nulls}  wrong/stale {bad}  by origin {bad_by_origin}")
        return {"column": True, "rows": total, "null": nulls, "bad": bad, "bad_by_origin": bad_by_origin}
    finally:
        conn.close()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--write", action="store_true", help="actually add the column/index and backfill (default: dry run)")
    ap.add_argument("--batch", type=int, default=500)
    ap.add_argument("--max-rows", type=int, default=None)
    ap.add_argument("--verify", action="store_true", help="read-only: recompute every stored hash and report mismatches")
    a = ap.parse_args(argv)
    if a.verify:
        try:
            up = du_is_up()
        except Exception as exc:
            raise SystemExit(f"REFUSING: cannot tell whether Du is up ({exc})")
        if up:
            raise SystemExit("REFUSING: Du appears to be up (run_nascence.py): " + " | ".join(up))
        verify(Path(a.db))
        return 0
    run(Path(a.db), a.write, a.batch, a.max_rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
