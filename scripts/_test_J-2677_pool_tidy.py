"""
_test_J-2677_pool_tidy.py -- proving test for J-2677 (F-3425): the recall-pool delta cache (J-2612, D-0526 'on') gets
its TIDY half: a periodic full-membership comparison that catches what the triggers cannot see, logs one identity row
per check (data/pool_delta_tidy.jsonl), and the latency probe rows carry pool_rebuilt / pool_changed.

Run from a worktree:  python scripts/_test_J-2677_pool_tidy.py
Everything lives under a temp dir (DB, tidy log, probe log); the live store is never opened.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
import numpy as np

TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TREE))
import core  # noqa: E402  (import core FIRST)
from core.memory import store as M  # noqa: E402

assert Path(core.__file__).resolve().is_relative_to(TREE), f"core resolved outside tree: {core.__file__}"
_fails = 0


def check(ok: bool, msg: str) -> None:
    global _fails
    print(("  PASS  " if ok else "  FAIL  ") + msg)
    if not ok:
        _fails += 1


spec = importlib.util.spec_from_file_location("_t_fast", str(TREE / "scripts" / "_test_retrieve_fast_pool.py"))
H = importlib.util.module_from_spec(spec)
sys.modules["_t_fast"] = H
spec.loader.exec_module(H)


def rows_of(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="J-2677_tidy_"))
    emb = H._det_embed_factory()
    M.DB_PATH = tmp / "a.db"
    M._embed = emb
    M._RETRIEVE_LATENCY_LOG = tmp / "probe.jsonl"
    M._POOL_TIDY_LOG = tmp / "tidy.jsonl"
    M._POOL_DELTA_MODE = "on"
    M._emb_reset()
    M._pool_invalidate()
    M.init_db()
    now = time.time()
    with sqlite3.connect(tmp / "a.db") as c:
        for i in range(300):
            t = f"memory {i} river garden {i}"
            c.execute("INSERT INTO memory_fragments (fragment_id, content, layer, relevance, timestamp, embedding, origin, "
                      "cold, temp, importance, keywords) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                      (f"f{i:04d}", t, "episodic", 0.5, now - i * 60, emb(t).tobytes(), "lived", 0, "warm", 0.5, "river"))
    qv = emb("river garden")
    keys = ["river"]

    def load():
        with M._connect() as conn:
            return M._load_pool_delta(conn, qv, keys)

    def fast():
        with M._connect() as conn:
            return M._load_pool_fast(conn, qv, keys)

    print("== constants ==")
    check(M._POOL_TIDY_EVERY_S == 1800.0, "default TIDY interval is 1800 s")

    print("== 1. first call = rebuild, then TIDY identical ==")
    M._POOL_TIDY_EVERY_S = 0.0                       # kill switch
    a = load()
    check(len(a) == 300 and M._POOL.stats["rebuilt"] is True, "first call rebuilds 300 rows")
    time.sleep(0.01)
    load()
    check(not (tmp / "tidy.jsonl").exists(), "kill switch 0 -> no TIDY row, no log file")
    M._POOL_TIDY_EVERY_S = 1e-6                      # due on every call
    load()
    r = rows_of(tmp / "tidy.jsonl")
    check(len(r) == 1 and r[0]["identical"] is True and r[0]["n_cache"] == 300 == r[0]["n_full"], f"TIDY due -> one identical row: {r}")

    print("== 2. in-contract demotion is caught by the trigger delta (bound: 0 calls) ==")
    with sqlite3.connect(tmp / "a.db") as c:
        c.execute("UPDATE memory_fragments SET cold=1 WHERE fragment_id='f0007'")
    M._POOL_TIDY_EVERY_S = 0.0
    b = load()
    check("f0007" not in {x["fragment_id"] for x in b} and len(b) == 299, "cold flip drops the row on the very next call")

    print("== 3. OUT-of-contract write (trigger dropped): delta alone is stale, TIDY heals it and logs it ==")
    with sqlite3.connect(tmp / "a.db") as c:
        c.execute("DROP TRIGGER trg_pool_chg_upd")
        c.execute("UPDATE memory_fragments SET cold=1 WHERE fragment_id='f0011'")
    stale = load()
    check("f0011" in {x["fragment_id"] for x in stale}, "TIDY off: the demoted row is still served (the hazard the TIDY bounds)")
    M._POOL_TIDY_EVERY_S = 1e-6
    healed = load()
    ids = {x["fragment_id"] for x in healed}
    r = rows_of(tmp / "tidy.jsonl")
    check("f0011" not in ids and len(healed) == 298, "TIDY due: demoted row gone, pool rebuilt")
    check(len(r) == 2 and r[1]["identical"] is False and r[1]["only_in_cache"] == 1 and r[1]["only_in_full"] == 0,
          f"mismatch logged with counts: {r[1] if len(r) > 1 else r}")
    f = fast()
    check([x._t for x in healed] == [x._t for x in f], "healed pool identical to _load_pool_fast (tuples + order)")
    check(bool(np.all(np.abs(np.array([x._sim for x in healed]) - np.array([x._sim for x in f])) <= 1e-6)), "cosines identical")

    print("== 4. TIDY interval is respected (not due -> no extra full SELECT / log row) ==")
    n0 = len(rows_of(tmp / "tidy.jsonl"))
    M._POOL_TIDY_EVERY_S = 3600.0
    load(); load()
    check(len(rows_of(tmp / "tidy.jsonl")) == n0, "no TIDY row while the timer has not elapsed")

    print("== 5. probe row carries pool_rebuilt / pool_changed on the delta path ==")
    from core import retrieval_probe as rp, r_shadow as rs     # silence the other observe-only channels, keep the REAL latency probe
    rp.observe = lambda q, pool, sel, recent_world, *a, **k: None
    rs.log_observation = lambda trigger, results, pool=None, now_ts=None: None
    M._POOL_DELTA_MODE = "on"
    M._pool_invalidate()
    M.retrieve(["river", "garden"], ["sleep"], time_bias="all", limit=5, query_text="river garden")
    with sqlite3.connect(tmp / "a.db") as c:
        c.execute("INSERT INTO memory_fragments (fragment_id,content,layer,timestamp,embedding,origin,cold,temp) VALUES (?,?,?,?,?,?,?,?)",
                  ("late1", "late river", "episodic", now + 99, emb("late river").tobytes(), "lived", 0, "warm"))
    M.retrieve(["river", "garden"], ["sleep"], time_bias="all", limit=5, query_text="river garden")
    M.retrieve(["river", "garden"], ["sleep"], time_bias="all", limit=5, query_text="river garden")
    pr = rows_of(tmp / "probe.jsonl")
    d = [x for x in pr if x.get("path") == "fast+delta"]
    check(len(d) == 3 and d[0].get("pool_rebuilt") is True and d[1].get("pool_rebuilt") is False
          and d[1].get("pool_changed") == 1 and d[2].get("pool_changed") == 0,
          f"probe pool fields rebuilt/changed = {[(x.get('pool_rebuilt'), x.get('pool_changed')) for x in d]}")
    M._POOL_DELTA_MODE = "off"
    M.retrieve(["river", "garden"], ["sleep"], time_bias="all", limit=5, query_text="river garden")
    last = rows_of(tmp / "probe.jsonl")[-1]
    check(last["path"] == "fast" and "pool_changed" not in last, "mode off: probe row unchanged (no pool fields)")

    print(f"\n{'ALL PASS' if _fails == 0 else f'{_fails} FAILED'}")
    return 1 if _fails else 0


if __name__ == "__main__":
    sys.exit(main())
