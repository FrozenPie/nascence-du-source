"""
J-3225 / D-0614 -- mark the stored closure fragments the founder ruling names (the 2 dream ones and the 4 on empty
cargo, F-3656 / F-3592), plus (J-3480, founder 2026-11-06) the 3 later empty-cargo line closures: 9 in all with a visible one-line note ahead of the original words, so recall shows the doubt. MARK,
NEVER DELETE: the original text follows the note byte for byte; memory_edges, embedding, importance, relevance, layer,
origin and every other column are untouched; content_hash is recomputed only where it was already non-NULL. The line
closures are left alone (the ruling). See core/memory/closure_marks.py for the fragment table and the exact notes.

OFFLINE ONLY: a --write is refused while any python process whose command line contains run_nascence.py exists.
Idempotent (a re-run finds 0 rows to change). Reversible: --unmark --write, or copy
backups/nascence.db.pre_waveC_20261105 back over the DB.

  python scripts/apply_J-3225_mark_closure_fragments.py                  # DRY RUN (default): selection, counts, sha256; writes nothing
  python scripts/apply_J-3225_mark_closure_fragments.py --write          # mark the 9 rows (one transaction)
  python scripts/apply_J-3225_mark_closure_fragments.py --db PATH        # another DB (default: the live data/memory/nascence.db)
  python scripts/apply_J-3225_mark_closure_fragments.py --unmark [--write]   # the reverse
  python scripts/apply_J-3225_mark_closure_fragments.py --expect N       # abort a --write unless N targets verify (default 9)

Output: total rows before/after, the 9 targets (id, kind, marked or not, first 70 chars of the ORIGINAL words), how many
are marked before/after, sha256 of the targets' (id, content) before/after (differs by design) AND of the ORIGINAL words
with the note stripped (must be EQUAL), and a sha256 of (fragment_id, length(content), layer, temp, origin,
importance, relevance) over every row outside the targets before/after (must be unchanged).

EXPECT 9 on the live DB (6 from J-3225 + 3 from J-3480). If the 6 were already marked by an earlier run, the re-run marks
only the 3 new ones (idempotent per row). The 3 later rows' dry run must show 'unmarked'; if one shows MARKED, stop.
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
    """(row count, sha256 over cheap per-row facts) for every row NOT in the targets -- proves nothing else moved."""
    h = hashlib.sha256()
    n = 0
    q = ("SELECT fragment_id, length(content), layer, temp, origin, importance, relevance "
         "FROM memory_fragments ORDER BY rowid")
    for row in conn.execute(q):
        if row[0] in ids:
            continue
        n += 1
        h.update(("\x00".join(str(x) for x in row) + "\x01").encode("utf-8", "surrogatepass"))
    return n, h.hexdigest()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--write", action="store_true", help="actually write (default: dry run)")
    ap.add_argument("--unmark", action="store_true", help="reverse the marking")
    ap.add_argument("--expect", type=int, default=9, help="abort a --write unless this many targets verify")
    ap.add_argument("--allow-du-up", action="store_true", help=argparse.SUPPRESS)   # test hook only
    a = ap.parse_args(argv)

    from core.memory import closure_marks as cm
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
        conn.row_factory = sqlite3.Row
        mode = "UNMARK" if a.unmark else "MARK"
        print(f"== J-3225 {mode} closure fragments (D-0614)  db={db}  write={a.write}")
        total0 = conn.execute("SELECT COUNT(*) FROM memory_fragments").fetchone()[0]
        rows = cm.target_rows(conn)
        bad = cm.problems(conn)
        ids = set(cm.TARGETS)
        marked0 = cm.marked_count(conn)
        sha_full0, sha_orig0 = cm.rows_sha256(conn), cm.rows_sha256(conn, original=True)
        out_n0, out_sha0 = _outside_sha(conn, ids)
        print(f"rows total before      : {total0}")
        print(f"targets present        : {len(rows)} of {len(cm.TARGETS)}   marked: {marked0}")
        for fid, content, _kw, _o, _h in rows:
            print(f"  {fid}  {cm.TARGETS[fid][0]:<17} {'MARKED' if cm.strip_note(content) != content else 'unmarked'}  "
                  f"{cm.strip_note(content)[:70]!r}")
        print(f"selection sha256 before (id+content)      : {sha_full0}")
        print(f"selection sha256 before (original words)  : {sha_orig0}")
        print(f"rows outside targets   : {out_n0}  sha256 {out_sha0}")
        if bad:
            print("REFUSE: selection does not verify:\n  " + "\n  ".join(bad))
            return 2 if a.write or not a.unmark else 0
        if a.write and len(rows) != a.expect:
            print(f"REFUSE: {len(rows)} targets verify, --expect {a.expect}; nothing written")
            return 2
        if not a.write:
            todo = marked0 if a.unmark else len(rows) - marked0
            print(f"DRY RUN: would {'strip the note from' if a.unmark else 'mark'} {todo} row(s). Nothing written.")
            return 0
        conn.execute("BEGIN IMMEDIATE")
        try:
            changed = cm.unmark(conn) if a.unmark else cm.mark(conn)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        total1 = conn.execute("SELECT COUNT(*) FROM memory_fragments").fetchone()[0]
        marked1 = cm.marked_count(conn)
        sha_full1, sha_orig1 = cm.rows_sha256(conn), cm.rows_sha256(conn, original=True)
        out_n1, out_sha1 = _outside_sha(conn, ids)
        print(f"rows changed           : {changed}")
        print(f"rows total after       : {total1}   (before {total0}; equal => none deleted)")
        print(f"targets marked after   : {marked1}")
        print(f"selection sha256 after (id+content)       : {sha_full1}")
        print(f"selection sha256 after (original words)   : {sha_orig1}   "
              f"{'EQUAL (words untouched)' if sha_orig0 == sha_orig1 else 'DIFFERENT -- INVESTIGATE'}")
        print(f"rows outside targets   : {out_n0} -> {out_n1}; their sha256 "
              f"{'unchanged' if out_sha0 == out_sha1 else 'CHANGED -- INVESTIGATE'}")
        print(f"elapsed {time.time() - t0:.1f}s")
        ok = (total0 == total1 and sha_orig0 == sha_orig1 and out_sha0 == out_sha1)
        return 0 if ok else 1
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
