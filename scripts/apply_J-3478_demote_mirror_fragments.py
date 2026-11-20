"""
J-3478 / D-0630 + D-0434 (founder, 2026-11-06) -- demote the stored self-mirror fragments (origin='mirror'; 17 on
2026-11-06). The weekly mirror is retired (core/self_mirror.SELF_MIRROR_RETIRED); its stored paragraphs reach the same
verdict whatever the numbers (J-3241: 51/51 'gap'), so they should stop outranking real memories. MARK, NEVER DELETE:
the only column written is memory_fragments.importance, lowered to min(importance, --to) (default 0.05, the same floor
store.mark_known_error uses). Content, embedding, origin, layer, cold, temp and every other column are untouched, and
no row outside origin='mirror' is touched. Each row's ORIGINAL importance is saved to a sidecar JSON before the write
so --restore is exact. OFFLINE ONLY: a --write is refused while any python process whose command line contains
run_nascence.py exists. Idempotent (a re-run finds nothing above the floor).

  python scripts/apply_J-3478_demote_mirror_fragments.py                  # DRY RUN (default, read-only connection)
  python scripts/apply_J-3478_demote_mirror_fragments.py --write          # demote (one transaction; backup first)
  python scripts/apply_J-3478_demote_mirror_fragments.py --restore [--write]   # put the saved importances back
  options: --db PATH (default data/memory/nascence.db)  --to 0.05  --expect 17  --backup PATH

Prints rows before/after, the selection ids with importance before/after, the sha256 of the selection's
(fragment_id, content) before/after (equal => content untouched) and of every OTHER row's (fragment_id, importance)
before/after (equal => nothing else moved). Rehearse on a copy of the DB first (--db COPY).
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
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "data" / "memory" / "nascence.db"
DEFAULT_BACKUP = ROOT / "data" / "lab" / "J-3478_mirror_importance_before.json"
ORIGIN = "mirror"


def du_is_up() -> list:
    """'pid: command line' for every python process running run_nascence.py (this process excluded). Fails CLOSED."""
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


def selection(conn) -> list:
    """[(fragment_id, importance)] for every origin='mirror' row, rowid order."""
    return [(r[0], r[1]) for r in conn.execute(
        "SELECT fragment_id, importance FROM memory_fragments WHERE origin=? ORDER BY rowid", (ORIGIN,))]


def sel_content_sha(conn) -> str:
    h = hashlib.sha256()
    for fid, content in conn.execute(
            "SELECT fragment_id, content FROM memory_fragments WHERE origin=? ORDER BY rowid", (ORIGIN,)):
        h.update(f"{fid}\x00{content}\x01".encode("utf-8", "surrogatepass"))
    return h.hexdigest()


def outside_sha(conn) -> tuple:
    h = hashlib.sha256()
    n = 0
    for fid, imp in conn.execute(
            "SELECT fragment_id, importance FROM memory_fragments WHERE origin IS NOT ? ORDER BY rowid", (ORIGIN,)):
        n += 1
        h.update(f"{fid}\x00{imp!r}\x01".encode("utf-8", "surrogatepass"))
    return n, h.hexdigest()


def load_backup(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("importance", {})
    except Exception:
        return {}


def save_backup(path: Path, saved: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps({"job": "J-3478", "origin": ORIGIN, "saved_at": time.time(), "importance": saved},
                              indent=1), encoding="utf-8")
    os.replace(tmp, path)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--write", action="store_true", help="actually write (default: dry run)")
    ap.add_argument("--restore", action="store_true", help="put the saved original importances back")
    ap.add_argument("--to", type=float, default=0.05, help="importance ceiling for the demoted rows")
    ap.add_argument("--expect", type=int, default=17, help="abort a --write unless the selection has this many rows")
    ap.add_argument("--backup", default=str(DEFAULT_BACKUP))
    ap.add_argument("--allow-du-up", action="store_true", help=argparse.SUPPRESS)   # test hook only
    a = ap.parse_args(argv)

    db, bk = Path(a.db), Path(a.backup)
    if not db.exists():
        print(f"REFUSE: {db} does not exist")
        return 2
    if not (0.0 <= a.to <= 1.0):
        print("REFUSE: --to must be in [0, 1]")
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
    conn = (sqlite3.connect(str(db), timeout=60) if a.write
            else sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True, timeout=60))
    try:
        mode = "RESTORE" if a.restore else "DEMOTE"
        print(f"== J-3478 {mode} origin='{ORIGIN}' fragments  db={db}  write={a.write}  to={a.to}")
        total0 = conn.execute("SELECT COUNT(*) FROM memory_fragments").fetchone()[0]
        sel0 = selection(conn)
        csha0 = sel_content_sha(conn)
        on0, osha0 = outside_sha(conn)
        print(f"rows total before      : {total0}")
        print(f"selection (mirror)     : {len(sel0)}")
        print(f"selection sha256 before: {csha0}")
        for fid, imp in sel0:
            print(f"  {fid}  importance {imp:.4f}")

        if a.restore:
            saved = load_backup(bk)
            plan = [(fid, saved[fid]) for fid, imp in sel0 if fid in saved and abs((imp or 0) - saved[fid]) > 1e-12]
            print(f"backup {bk}: {len(saved)} saved; {len(plan)} row(s) would be restored")
            if not a.write:
                print("DRY RUN: nothing written.")
                return 0
            conn.execute("BEGIN IMMEDIATE")
            try:
                for fid, imp in plan:
                    conn.execute("UPDATE memory_fragments SET importance=? WHERE fragment_id=? AND origin=?",
                                 (imp, fid, ORIGIN))
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            changed = len(plan)
        else:
            todo = [(fid, imp) for fid, imp in sel0 if imp is not None and imp > a.to]
            print(f"{len(todo)} row(s) above {a.to} -> would be lowered to {a.to}")
            if a.write and len(sel0) != a.expect:
                print(f"REFUSE: selection is {len(sel0)} rows, --expect {a.expect}; nothing written")
                return 2
            if not a.write:
                print("DRY RUN: nothing written.")
                return 0
            saved = load_backup(bk)
            for fid, imp in todo:
                saved.setdefault(fid, imp)         # never overwrite an earlier original with an already-demoted value
            save_backup(bk, saved)
            print(f"backup written         : {bk}  ({len(saved)} originals)")
            conn.execute("BEGIN IMMEDIATE")
            try:
                cur = conn.execute("UPDATE memory_fragments SET importance=? WHERE origin=? AND importance>?",
                                   (a.to, ORIGIN, a.to))
                changed = cur.rowcount
                conn.commit()
            except Exception:
                conn.rollback()
                raise

        total1 = conn.execute("SELECT COUNT(*) FROM memory_fragments").fetchone()[0]
        sel1 = selection(conn)
        csha1 = sel_content_sha(conn)
        on1, osha1 = outside_sha(conn)
        print(f"rows changed           : {changed}")
        print(f"rows total after       : {total1}   (before {total0}; equal => none deleted)")
        print(f"selection importance after: min {min((i for _, i in sel1), default=None)} max {max((i for _, i in sel1), default=None)}")
        print(f"selection sha256 after : {csha1}   {'EQUAL (content untouched)' if csha0 == csha1 else 'DIFFERENT -- INVESTIGATE'}")
        print(f"rows outside selection : {on0} -> {on1}; their (fragment_id,importance) sha256 "
              f"{'unchanged' if osha0 == osha1 else 'CHANGED -- INVESTIGATE'}")
        print(f"elapsed {time.time() - t0:.1f}s")
        return 0 if (total0 == total1 and csha0 == csha1 and osha0 == osha1 and len(sel0) == len(sel1)) else 1
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
