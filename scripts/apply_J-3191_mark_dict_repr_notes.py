"""
J-3191 / D-0578 -- mark the dict-repr 'understanding' notes (F-3779, row P-0066; expected 61) as temp='hidden' so Recall
skips them. MARK, NEVER DELETE: content, embedding and every other column are untouched; the only column written is
memory_fragments.temp (an existing column, existing 'hidden' tier -- see core/memory/dict_repr_notes.py). OFFLINE ONLY:
it refuses a --write while any python process whose command line contains run_nascence.py exists. Idempotent (a re-run
finds 0 rows to change). Reversible: scripts/unmark_dict_repr_notes.py (or --unmark here).

  python scripts/apply_J-3191_mark_dict_repr_notes.py                 # DRY RUN (default): selection, ids, temp histogram, sha256; writes nothing
  python scripts/apply_J-3191_mark_dict_repr_notes.py --write         # set temp='hidden' on the selection (one transaction)
  python scripts/apply_J-3191_mark_dict_repr_notes.py --db PATH       # another DB (default: the live data/memory/nascence.db)
  python scripts/apply_J-3191_mark_dict_repr_notes.py --unmark [--write]   # the reverse (dry run unless --write)
  python scripts/apply_J-3191_mark_dict_repr_notes.py --expect N      # abort a --write if the selection is not N rows (default 61)

Output: total rows before/after, selection count, the selected fragment_ids, the temp/cold histogram of the selection
before and after, how many of the selection are 'hidden' before/after, whether any row OUTSIDE the selection changed
temp (must be none), and the sha256 of the selection's (fragment_id, content) before and after (equal => content untouched).

Restore (if anything looks wrong): --unmark --write, or copy backups/nascence.db.pre_waveC_20261105 back over the DB.
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


def du_is_up() -> list:
    """'pid: command line' for every python process running run_nascence.py (this process excluded). Fails CLOSED:
    an unreadable process list raises, and the caller refuses."""
    me = os.getpid()
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
    out = []
    for ln in lines:
        pid = ln.split(":", 1)[0].split(" ", 1)[0]
        if pid.isdigit() and int(pid) == me:
            continue
        out.append(ln)
    return out


def _outside_sha(conn, ids: set) -> tuple:
    """(row count, sha256 of (fragment_id, temp)) over every row NOT in the selection -- proves nothing else moved."""
    h = hashlib.sha256()
    n = 0
    for fid, temp in conn.execute("SELECT fragment_id, temp FROM memory_fragments ORDER BY rowid"):
        if fid in ids:
            continue
        n += 1
        h.update(f"{fid}\x00{temp}\x01".encode("utf-8", "surrogatepass"))
    return n, h.hexdigest()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--write", action="store_true", help="actually write (default: dry run)")
    ap.add_argument("--unmark", action="store_true", help="reverse the marking")
    ap.add_argument("--expect", type=int, default=61, help="abort a --write unless the selection has this many rows")
    ap.add_argument("--allow-du-up", action="store_true", help=argparse.SUPPRESS)   # test hook only
    a = ap.parse_args(argv)

    from core.memory import dict_repr_notes as drn
    db = Path(a.db)
    if not db.exists():
        print(f"REFUSE: {db} does not exist")
        return 2
    if a.write and not a.allow_du_up:
        try:
            up = du_is_up()
        except Exception as exc:
            print(f"REFUSE: cannot tell whether Du is up ({exc})")
            return 2
        if up:
            print("REFUSE: Du appears to be running; stop him first.\n  " + "\n  ".join(up))
            return 2

    t0 = time.time()
    # Dry run opens read-only so it cannot take a write lock or touch the file; --write opens read-write.
    if a.write:
        conn = sqlite3.connect(str(db), timeout=60)
    else:
        conn = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True, timeout=60)
    try:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(memory_fragments)")}
        if "temp" not in cols:
            print("REFUSE: memory_fragments has no temp column (this DB predates the Axis-4 migration)")
            return 2
        mode = "UNMARK" if a.unmark else "MARK"
        print(f"== J-3191 {mode} dict-repr understanding notes  db={db}  write={a.write}")
        total0 = conn.execute("SELECT COUNT(*) FROM memory_fragments").fetchone()[0]
        ids = drn.select_ids(conn)
        idset = set(ids)
        hid_sql = f"SELECT COUNT(*) FROM memory_fragments WHERE {drn.SELECT_PREDICATE} AND temp='hidden'"
        hid0 = conn.execute(hid_sql).fetchone()[0]
        sha0 = drn.rows_sha256(conn)
        hist0 = drn.temp_histogram(conn)
        out_n0, out_sha0 = _outside_sha(conn, idset)
        print(f"rows total before      : {total0}")
        print(f"selection (dict-repr)  : {len(ids)}   already hidden: {hid0}")
        print(f"temp histogram before  : {hist0}")
        print(f"selection sha256 before: {sha0}")
        print(f"fragment_ids           : {ids}")
        if not a.unmark and a.write and len(ids) != a.expect:
            print(f"REFUSE: selection is {len(ids)} rows, --expect {a.expect}; nothing written")
            return 2
        if not a.write:
            todo = hid0 if a.unmark else len(ids) - hid0
            print(f"DRY RUN: would {'restore' if a.unmark else 'hide'} {todo} row(s). Nothing written.")
            return 0
        conn.execute("BEGIN IMMEDIATE")
        try:
            changed = drn.unmark(conn) if a.unmark else drn.mark(conn)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        total1 = conn.execute("SELECT COUNT(*) FROM memory_fragments").fetchone()[0]
        hid1 = conn.execute(hid_sql).fetchone()[0]
        sha1 = drn.rows_sha256(conn)
        hist1 = drn.temp_histogram(conn)
        out_n1, out_sha1 = _outside_sha(conn, idset)
        print(f"rows changed           : {changed}")
        print(f"rows total after       : {total1}   (before {total0}; equal => none deleted)")
        print(f"selection hidden after : {hid1}")
        print(f"temp histogram after   : {hist1}")
        print(f"selection sha256 after : {sha1}   {'EQUAL (content untouched)' if sha0 == sha1 else 'DIFFERENT -- INVESTIGATE'}")
        print(f"rows outside selection : {out_n0} -> {out_n1}; their (fragment_id,temp) sha256 "
              f"{'unchanged' if out_sha0 == out_sha1 else 'CHANGED -- INVESTIGATE'}")
        print(f"elapsed {time.time() - t0:.1f}s")
        ok = (total0 == total1 and sha0 == sha1 and out_sha0 == out_sha1)
        return 0 if ok else 1
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
