"""J-2384 (F-3082): core/sleep_offloop.off_process + core/book_residue.sweep_offprocess.

Run from a throwaway worktree or a scratch copy, NEVER from C:\\Nascence itself: test 3 creates a tiny probe DB
under THIS tree's data/memory/ to observe the D-0353 fence, and refuses to run when that tree is the live one.

  1. mirror: a parent with a redirected DB_PATH spawns a child that sees the same DB_PATH / fence flags /
     like_scan switch, is a different process, and is not live.
  2. fail-open: an unimportable target returns a copy of `zero`, calls on_fail, logs a WARNING; a timeout
     kills the child and does the same.
  3. fence equivalence: with DB_PATH under the tree's own data/, a NON-live parent's child logs the D-0353
     "non-live process opened the live memory DB" line (replayed on the parent's nascence.memory logger);
     after profile.mark_live() in the parent the child is live and logs no fence line.
  4. book_residue.sweep_offprocess on a DB with no memory_fragments table: the child's own sweep() fails
     open (zero dict, a 'sweep-error' skip row in the REDIRECTED _LOG, nothing in the tree's data/).
"""
import asyncio
import json
import logging
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402
assert Path(core.__file__).resolve().is_relative_to(ROOT), core.__file__
if ROOT.resolve() == Path(r"C:\Nascence").resolve():
    sys.exit("refusing to run from the live tree C:\\Nascence (test 3 writes a probe DB under data/memory/)")

from core import sleep_offloop, profile, book_residue  # noqa: E402
from core.memory import store  # noqa: E402

records = []


class _Cap(logging.Handler):
    def emit(self, r):
        records.append((r.name, r.levelno, r.getMessage()))


logging.getLogger().addHandler(_Cap())
logging.getLogger().setLevel(logging.INFO)
ZERO = {"books_tracked": 0, "books_with_residue": 0, "unstuck": 0}
fails = []


def check(cond, what):
    print(("PASS " if cond else "FAIL ") + what)
    if not cond:
        fails.append(what)


tmp = Path(tempfile.mkdtemp(prefix="j2384_"))
db = tmp / "probe.db"
sqlite3.connect(db).close()

# 1. mirror
store.DB_PATH = db
r = asyncio.run(sleep_offloop.off_process("core.sleep_offloop", "_child_state_probe", zero={"x": 1}))
check(r.get("db_path") == str(db), f"1 child DB_PATH mirrored ({r.get('db_path')})")
check(r.get("pid") not in (None, os.getpid()), "1 child is a separate process")
check(r.get("live") is False, "1 non-live parent -> non-live child")
check(r.get("fence_mode") == store._FENCE_MODE and r.get("single_pass") is True, "1 fence mode + like_scan mirrored")

# 2. fail-open
why = []
r = asyncio.run(sleep_offloop.off_process("core.no_such_module_j2384", "x", zero=ZERO, on_fail=why.append))
check(r == ZERO and r is not ZERO, "2 bad target -> copy of zero")
check(bool(why) and "exit 1" in why[0], f"2 on_fail got the reason ({why[:1]})")
check(any(n == "nascence.sleep_offloop" and lv == logging.WARNING for n, lv, _ in records), "2 WARNING logged")
why.clear()
r = asyncio.run(sleep_offloop.off_process("core.sleep_offloop", "_child_state_probe", zero=ZERO,
                                          timeout=0.05, on_fail=why.append))
check(r == ZERO and bool(why) and "timeout" in why[0], f"2 timeout -> zero, child killed ({why[:1]})")

# 3. fence equivalence (DB under this tree's own data/, i.e. a path the fence treats as live)
fdb = ROOT / "data" / "memory" / "_j2384_fence_probe.db"
fdb.parent.mkdir(parents=True, exist_ok=True)
sqlite3.connect(fdb).close()
try:
    store.DB_PATH = fdb
    records.clear()
    r = asyncio.run(sleep_offloop.off_process("core.sleep_offloop", "_child_state_probe", zero={"x": 1}))
    fence = [m for n, _, m in records if n == "nascence.memory" and "non-live process opened" in m]
    check(r.get("live") is False and len(fence) == 1, f"3 non-live parent: child fenced, line replayed ({len(fence)})")
    profile.mark_live()
    records.clear()
    r = asyncio.run(sleep_offloop.off_process("core.sleep_offloop", "_child_state_probe", zero={"x": 1}))
    fence = [m for n, _, m in records if "db fence" in m]
    check(r.get("live") is True and not fence, f"3 live parent: child live, no fence line ({len(fence)})")
finally:
    for suf in ("", "-wal", "-shm"):
        try:
            Path(str(fdb) + suf).unlink()
        except FileNotFoundError:
            pass

# 4. book_residue fail-open inside the child, redirected log
store.DB_PATH = db
log = tmp / "book_residue.jsonl"
book_residue._DATA, book_residue._LOG = tmp, log
tree_log = ROOT / "data" / "book_residue.jsonl"
before = tree_log.stat().st_mtime if tree_log.exists() else None
r = asyncio.run(book_residue.sweep_offprocess())
rows = [json.loads(x) for x in open(log, encoding="utf-8")] if log.exists() else []
check(r == ZERO, f"4 sweep error in child -> zero dict ({r})")
check(len(rows) == 1 and rows[0].get("reason") == "sweep-error", f"4 skip row in the redirected log ({rows})")
after = tree_log.stat().st_mtime if tree_log.exists() else None
check(before == after, "4 tree data/book_residue.jsonl untouched")

print("ALL PASS" if not fails else f"{len(fails)} FAILED")
sys.exit(1 if fails else 0)
