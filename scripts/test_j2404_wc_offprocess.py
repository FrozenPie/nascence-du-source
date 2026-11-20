"""J-2404: world_consolidation.sweep_offprocess() -- fail-open and the _OFFPROCESS_ACTIVE tripwire.

Every path the child could touch is a temp path (store.DB_PATH, the module _LOG, reading.STATE/BOOKS_DIR,
essay_lesson._STATE/_LOG); nothing under any data/ directory is opened. Run from a throwaway tree:
    python scripts/test_j2404_wc_offprocess.py
The identity check (thread vs child, same result dict, same log rows, same chapter_id column) is the convoy
harness on sandbox copies (scripts/lab_convoy_sweeps_J2392.py --sweep world_consolidation --mode offproc).
"""
from __future__ import annotations

import asyncio
import json
import logging
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main() -> int:
    import core
    assert Path(core.__file__).resolve().is_relative_to(ROOT), core.__file__
    from core import essay_lesson, reading, sleep_offloop
    from core import world_consolidation as wc
    from core.memory import store

    tmp = Path(tempfile.mkdtemp(prefix="j2404_"))
    db = tmp / "nascence.db"
    c = sqlite3.connect(str(db))
    c.execute("CREATE TABLE memory_fragments (fragment_id TEXT PRIMARY KEY, content TEXT, origin TEXT, "
              "chapter_id TEXT, timestamp REAL)")
    c.commit(); c.close()
    store.DB_PATH = db
    wc._LOG = tmp / "world_consolidation_log.jsonl"
    reading.STATE = tmp / "reading_state.json"
    reading.BOOKS_DIR = tmp / "books"
    reading.DEFAULT_BOOK = tmp / "books" / "none.txt"
    essay_lesson._STATE = tmp / "essay_lesson_state.json"
    essay_lesson._LOG = tmp / "essay_lesson_log.jsonl"
    fails = []

    # 1. a real child on an empty temp DB: same dict as in-process (ts aside), one sweep row each
    res_child = asyncio.run(wc.sweep_offprocess())
    res_inproc = wc.sweep()
    strip = lambda d: {k: v for k, v in d.items() if k != "ts"}
    if strip(res_child) != strip(res_inproc):
        fails.append(f"child {res_child} != in-process {res_inproc}")
    rows = [json.loads(l) for l in open(wc._LOG, encoding="utf-8")]
    if [strip(r) for r in rows] != [strip({**res_inproc, "sweep": True})] * 2:
        fails.append(f"log rows {rows}")
    if wc._OFFPROCESS_ACTIVE:
        fails.append("tripwire left set after a successful child")

    # 2. fail-open: a child killed by a timeout -> zero dict, one error sweep row, tripwire cleared
    old = sleep_offloop.OFF_PROCESS_TIMEOUT_S
    sleep_offloop.OFF_PROCESS_TIMEOUT_S = 0.001
    try:
        res_fail = asyncio.run(wc.sweep_offprocess())
    finally:
        sleep_offloop.OFF_PROCESS_TIMEOUT_S = old
    if strip(res_fail) != {"subjects": 0, "candidates": 0, "filed": 0, "enabled": wc.FILING_ENABLED}:
        fails.append(f"fail-open dict {res_fail}")
    rows = [json.loads(l) for l in open(wc._LOG, encoding="utf-8")]
    if len(rows) != 3 or not str(rows[-1].get("error", "")).startswith("subprocess-error: timeout"):
        fails.append(f"fail-open row {rows[-1:]}")
    if wc._OFFPROCESS_ACTIVE:
        fails.append("tripwire left set after a failed child")

    # 3. tripwire: file_book_notes during an off-process sweep logs a WARNING and still runs
    caught = []

    class _H(logging.Handler):
        def emit(self, r):
            caught.append((r.levelno, r.getMessage()))
    logging.getLogger("nascence.world_consolidation").addHandler(_H())
    wc._OFFPROCESS_ACTIVE = True
    try:
        s = wc.file_book_notes("Some Book Title")
    finally:
        wc._OFFPROCESS_ACTIVE = False
    if not any(lv == logging.WARNING and "off-process sweep is running" in m for lv, m in caught):
        fails.append(f"tripwire did not warn: {caught}")
    if s.get("reason") != "no gist yet (gist-first: not filing)":
        fails.append(f"file_book_notes under tripwire did not run normally: {s}")
    caught.clear()
    wc.file_book_notes("Some Book Title")
    if caught:
        fails.append(f"tripwire warned with no sweep running: {caught}")

    for f in fails:
        print("FAIL", f)
    print("ALL PASS" if not fails else f"{len(fails)} FAILED")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
