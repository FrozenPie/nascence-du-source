"""
J-3482 (founder ruling in chat 2026-11-06; source J-3283 / review J-3243) -- mark the understanding notes that contain
text from a random external-shock Wikipedia page (review count: 51 of 537) as temp='hidden' so Recall skips them.
MARK, NEVER DELETE: content, embedding and every other column are untouched; the only column written is
memory_fragments.temp (existing column, existing 'hidden' tier, the same one D-0578 / J-3191 used). OFFLINE ONLY: a
--write is refused while any python process whose command line contains run_nascence.py exists. Idempotent. Reversible
with --unmark, which restores ONLY the rows this script changed (recorded in a manifest), never a J-3191 row.
Selection logic and its honest limits: core/memory/shock_notes.py (a lower bound).

  python scripts/apply_J-3482_mark_shock_notes.py                      # DRY RUN (default): selection, per-note evidence, sha256; writes nothing
  python scripts/apply_J-3482_mark_shock_notes.py --write              # set temp='hidden' on the selection (one transaction)
  python scripts/apply_J-3482_mark_shock_notes.py --db PATH            # another DB (default: the live data/memory/nascence.db)
  python scripts/apply_J-3482_mark_shock_notes.py --exclude ID [ID..]  # founder veto: leave these notes alone
  python scripts/apply_J-3482_mark_shock_notes.py --expect N           # abort a --write unless the selection is N rows
  python scripts/apply_J-3482_mark_shock_notes.py --unmark [--write]   # the reverse, from the manifest (dry run unless --write)
  python scripts/apply_J-3482_mark_shock_notes.py --manifest PATH      # default: <db>.J-3482_marked.json (kept next to the DB)

REHEARSE ON A COPY FIRST: cp data/memory/nascence.db <scratch>/copy.db ; run with --db <scratch>/copy.db (dry, then
--write, then --unmark --write) ; compare. Output: rows total before/after, selection count, how many were already
hidden (the J-3191 dict-repr notes overlap), each selected note with the evidence that selected it, the sha256 of the
selection's (fragment_id, content) before/after (equal => content untouched), and the sha256 of every row outside the
selection's (fragment_id, temp) before/after (equal => nothing else moved).
"""
from __future__ import annotations

import argparse
import json
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


def _load_manifest(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8")).get("previous_temp", {})
    except Exception:
        return {}


def _save_manifest(p: Path, previous: dict, db: Path) -> None:
    """Atomic write (temp file + replace). Merges: a re-run never drops an earlier row."""
    p.parent.mkdir(parents=True, exist_ok=True)
    doc = {"job": "J-3482", "db": str(db), "written": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "note": "fragment_id -> temp the row had before this script hid it; --unmark restores exactly these",
           "previous_temp": previous}
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, p)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--write", action="store_true", help="actually write (default: dry run)")
    ap.add_argument("--unmark", action="store_true", help="reverse the marking from the manifest")
    ap.add_argument("--exclude", nargs="*", default=[], help="fragment_ids to leave alone (founder veto)")
    ap.add_argument("--expect", type=int, default=None, help="abort a --write unless the selection has this many rows")
    ap.add_argument("--manifest", default=None)
    ap.add_argument("--allow-du-up", action="store_true", help=argparse.SUPPRESS)   # test hook only
    a = ap.parse_args(argv)

    from core.memory import shock_notes as sn
    db = Path(a.db)
    if not db.exists():
        print(f"REFUSE: {db} does not exist")
        return 2
    manifest = Path(a.manifest) if a.manifest else db.with_name(db.name + ".J-3482_marked.json")
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
        print(f"== J-3482 {mode} shock-page understanding notes  db={db}  write={a.write}")
        total0 = conn.execute("SELECT COUNT(*) FROM memory_fragments").fetchone()[0]
        n_und = conn.execute("SELECT COUNT(*) FROM memory_fragments WHERE origin='understanding'").fetchone()[0]

        if a.unmark:
            prev = _load_manifest(manifest)
            ids = list(prev)
            hid = sum(1 for f in ids if (conn.execute("SELECT temp FROM memory_fragments WHERE fragment_id=?", (f,))
                                         .fetchone() or [None])[0] == "hidden")
            sha0 = sn.rows_sha256(conn, ids)
            out0 = sn.outside_sha256(conn, ids)
            print(f"manifest               : {manifest}  ({len(ids)} row(s), {hid} currently hidden)")
            if not a.write:
                print(f"DRY RUN: would restore {hid} row(s) to their previous temp. Nothing written.")
                return 0
            conn.execute("BEGIN IMMEDIATE")
            try:
                changed = sn.unmark(conn, prev)
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            sha1 = sn.rows_sha256(conn, ids)
            out1 = sn.outside_sha256(conn, ids)
            total1 = conn.execute("SELECT COUNT(*) FROM memory_fragments").fetchone()[0]
            print(f"rows restored          : {changed}   rows total {total0} -> {total1}")
            print(f"selection sha256       : {'EQUAL (content untouched)' if sha0 == sha1 else 'DIFFERENT -- INVESTIGATE'}")
            print(f"outside-selection sha  : {'unchanged' if out0 == out1 else 'CHANGED -- INVESTIGATE'}")
            return 0 if (total0 == total1 and sha0 == sha1 and out0 == out1) else 1

        sel = sn.select(conn, exclude=a.exclude)
        ids = [s["id"] for s in sel]
        already = sum(1 for s in sel if s["temp"] == "hidden")
        sha0 = sn.rows_sha256(conn, ids)
        out0 = sn.outside_sha256(conn, ids)
        print(f"rows total before      : {total0}   understanding notes: {n_und}")
        print(f"selection (shock text) : {len(ids)}   already hidden (J-3191 overlap): {already}   to hide: {len(ids) - already}")
        print(f"selection sha256 before: {sha0}")
        for s in sel:
            ev = "; ".join(f"{t!r}:{k}" + (f"x{n}" if n else "") for t, k, n in s["signals"])
            print(f"  {s['id']}  temp={s['temp']:<6}  {ev}")
        if a.write and a.expect is not None and len(ids) != a.expect:
            print(f"REFUSE: selection is {len(ids)} rows, --expect {a.expect}; nothing written")
            return 2
        if not a.write:
            print(f"DRY RUN: would hide {len(ids) - already} row(s). Nothing written.")
            return 0
        conn.execute("BEGIN IMMEDIATE")
        try:
            changed = sn.mark(conn, ids)
            # manifest first (merged, atomic): if the commit then fails nothing is hidden and unmark is a no-op
            _save_manifest(manifest, {**_load_manifest(manifest), **changed}, db)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        total1 = conn.execute("SELECT COUNT(*) FROM memory_fragments").fetchone()[0]
        hid1 = sum(1 for f in ids if conn.execute("SELECT temp FROM memory_fragments WHERE fragment_id=?", (f,))
                   .fetchone()[0] == "hidden")
        sha1 = sn.rows_sha256(conn, ids)
        out1 = sn.outside_sha256(conn, ids)
        print(f"rows changed           : {len(changed)}   manifest: {manifest}")
        print(f"rows total after       : {total1}   (before {total0}; equal => none deleted)")
        print(f"selection hidden after : {hid1} of {len(ids)}")
        print(f"selection sha256 after : {sha1}   {'EQUAL (content untouched)' if sha0 == sha1 else 'DIFFERENT -- INVESTIGATE'}")
        print(f"rows outside selection : {out0[0]} -> {out1[0]}; their (fragment_id,temp) sha256 "
              f"{'unchanged' if out0[1] == out1[1] else 'CHANGED -- INVESTIGATE'}")
        print(f"elapsed {time.time() - t0:.1f}s")
        return 0 if (total0 == total1 and sha0 == sha1 and out0 == out1 and hid1 == len(ids)) else 1
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
