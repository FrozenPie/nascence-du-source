"""J-4410 (M1): temp-path test for core/memory/edit_log.py and its three call sites.

Checks, on a throwaway sqlite DB and a throwaway log path (never data/):
  1. row counts match each writer's own count (replay_strengthen len, downscale_episodic rowcount,
     dream_fade 'faded') -- the numbers the night_log already records;
  2. every logged new_importance equals the value actually stored afterwards;
  3. behaviour is unchanged: the same fixture run with the log OFF ends with identical importances;
  4. a log write failure never breaks the writer.
Run: python scripts/_test_memory_edit_log.py   (exit 0 = pass)
"""
import json
import os
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  (core BEFORE anything else, and assert it is THIS tree)
assert Path(core.__file__).resolve().is_relative_to(ROOT), core.__file__

from core.memory import store, edit_log  # noqa: E402
from core import night  # noqa: E402

NOW = time.time()


def _fixture(db: Path) -> None:
    conn = sqlite3.connect(str(db))
    conn.execute("""CREATE TABLE memory_fragments (fragment_id TEXT PRIMARY KEY, content TEXT, importance REAL,
                    replay_count INTEGER DEFAULT 0, cold INTEGER DEFAULT 0, layer TEXT, timestamp REAL,
                    chapter_id TEXT, origin TEXT)""")
    rows = []
    origins = ["reading", "lived", "inner_thought", "dream", "study", "action"]
    for i in range(40):     # episodic, today
        rows.append((f"e{i}", f"episodic {i}", 0.2 + (i % 7) * 0.1, 0, 0, "episodic", NOW - 600 - i, None,
                     origins[i % len(origins)]))
    for i in range(10):     # episodic, before the wake (outside downscale's window)
        rows.append((f"old{i}", f"old {i}", 0.5, 0, 0, "episodic", NOW - 86400 * 5, None, "lived"))
    for i, age_h in enumerate([2, 30, 40, 50, 60, 71, 80]):   # dreams across the fade curve
        rows.append((f"d{i}", f"dream {i}", 0.85, 0, 1 if age_h == 60 else 0, "episodic",
                     NOW - age_h * 3600, None, "dream"))
    conn.executemany("INSERT INTO memory_fragments VALUES (?,?,?,?,?,?,?,?,?)", rows)
    conn.commit()
    conn.close()


def _run(tmp: Path, mode: str):
    db = tmp / f"mem_{mode}.db"
    log = tmp / f"edit_log_{mode}.jsonl"
    _fixture(db)
    store.DB_PATH = db
    edit_log.EDIT_LOG_PATH = log
    edit_log.MEMORY_EDIT_LOG_MODE = mode
    since = NOW - 3600
    replayed = store.replay_strengthen(since)
    n_down = store.downscale_episodic(since_ts=since)
    fade = night.dream_fade(now=NOW)
    conn = sqlite3.connect(str(db))
    final = dict(conn.execute("SELECT fragment_id, importance FROM memory_fragments").fetchall())
    conn.close()
    rows = [json.loads(l) for l in log.read_text(encoding="utf-8").splitlines()] if log.exists() else []
    return replayed, n_down, fade, final, rows


def main() -> int:
    # store._connect()'s `with` commits but does not close, so Windows keeps the temp DBs open until GC.
    with tempfile.TemporaryDirectory(prefix="j4410_", ignore_cleanup_errors=True) as td:
        tmp = Path(td)
        replayed, n_down, fade, final_on, rows = _run(tmp, "shadow")
        by = {}
        for r in rows:
            by.setdefault(r["stage"], []).append(r)
            assert set(r) == {"ts", "stage", "fragment_id", "old_importance", "new_importance", "cold_before"}, r
        assert len(replayed) > 0 and n_down > 0 and fade["faded"] > 0, (len(replayed), n_down, fade)
        assert len(by.get("replay", [])) == len(replayed), (len(by.get("replay", [])), len(replayed))
        assert len(by.get("downscale", [])) == n_down, (len(by.get("downscale", [])), n_down)
        assert len(by.get("dream_fade", [])) == fade["faded"], (len(by.get("dream_fade", [])), fade)
        # the last logged new value of each fragment equals what the DB holds afterwards
        last = {}
        for r in rows:
            last[r["fragment_id"]] = r["new_importance"]
        for fid, new in last.items():
            assert abs(final_on[fid] - new) < 1e-5, (fid, final_on[fid], new)
        assert any(r["cold_before"] == 1 for r in by["dream_fade"]), "cold dream should be faded with cold_before=1"

        # behaviour unchanged with the log off; off writes nothing
        r2, n2, f2, final_off, rows_off = _run(tmp, "off")
        assert rows_off == [] and not (tmp / "edit_log_off.jsonl").exists()
        assert len(r2) == len(replayed) and n2 == n_down and f2 == fade
        assert final_off == final_on

        # a failing log write must not break the writers
        bad = tmp / "a_file"
        bad.write_text("x")
        _fixture(tmp / "mem_bad.db")
        store.DB_PATH = tmp / "mem_bad.db"
        edit_log.EDIT_LOG_PATH = bad / "sub" / "log.jsonl"     # parent is a file -> mkdir fails
        edit_log.MEMORY_EDIT_LOG_MODE = "shadow"
        assert len(store.replay_strengthen(NOW - 3600)) == len(replayed)
        assert store.downscale_episodic(since_ts=NOW - 3600) == n_down
        assert night.dream_fade(now=NOW) == fade

        print(f"PASS: replay={len(replayed)} downscale={n_down} dream_fade={fade['faded']} "
              f"rows={len(rows)}; off-run identical; failing log path tolerated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
