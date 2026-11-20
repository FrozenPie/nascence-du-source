"""J-3246 / D-0634: moment_ts stamped into fragment_context and world_context at store_fragment time.

Offline. Temp DB only (store.DB_PATH redirected before the first call; world stores + moment files redirected).
Touches no live data and never opens data/memory/nascence.db.

Covers:
  1. migration on an OLD-schema DB (context tables WITHOUT moment_ts, with legacy rows): init_db() adds the column to
     BOTH tables; legacy rows unchanged and NULL; idempotent on re-run and on a DB that already has the column.
  2. store_fragment with a current moment stamps that moment's ts on BOTH the experienced (fragment_context) and the
     truth (world_context) row; with NO current moment the row is written with NULL (fail-open).
  3. kill-switch (MOMENT_TS_STAMP=False) -> NULL, rows still written.
  4. fail-open: a migration that cannot complete falls back to the original moment-less INSERT (row still written).
  5. hot path: the cached readiness check is a set lookup (cost within noise).
  6. scripts/moment_key_validate.py against a temp DB + temp moments.jsonl (exact / lag1 / other classification).
"""
import json
import os
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ["NASCENCE_TRAINING_LOG"] = "0"
TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TREE))
import core                                             # noqa: E402  (core BEFORE lab_env)
assert TREE in Path(core.__file__).resolve().parents, core.__file__
import core.memory.store as store                       # noqa: E402
from core import moment, memory_edges                   # noqa: E402

_TMP = Path(tempfile.mkdtemp(prefix="j3246_moment_ts_"))
store.DB_PATH = _TMP / "test.db"
from scripts._test_isolation import redirect_world_stores   # noqa: E402
redirect_world_stores(_TMP, locomotion=True, watershed=True, census=True)
moment._LOG = _TMP / "moments.jsonl"
moment._STATE = _TMP / "moment_state.json"
assert str(store.DB_PATH).startswith(str(_TMP))

_fails = []


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        _fails.append(msg)


def cols(db, tbl):
    c = sqlite3.connect(str(db))
    try:
        return [r[1] for r in c.execute(f"PRAGMA table_info({tbl})")]
    finally:
        c.close()


def ctx(db, fid):
    c = sqlite3.connect(str(db))
    try:
        fc = c.execute("SELECT moment_ts FROM fragment_context WHERE fragment_id=?", (fid,)).fetchall()
        wc = c.execute("SELECT moment_ts FROM world_context WHERE fragment_id=?", (fid,)).fetchall()
        return fc, wc
    finally:
        c.close()


def fresh_db(name, old_ctx=True):
    """A DB the way the live one is: memory_fragments from init_db, context tables from memory_edges' old schema."""
    p = _TMP / name
    store.DB_PATH = p
    store._MOMENT_TS_READY.clear()
    store.init_db()
    c = sqlite3.connect(str(p))
    c.execute(memory_edges._CTX_SCHEMA)
    c.execute(memory_edges._CTX_SCHEMA.replace("fragment_context", "world_context"))
    if old_ctx:
        c.execute("INSERT INTO fragment_context (fragment_id, tuple_ts, source, place) "
                  "VALUES ('legacy1', 1000.0, 'experienced:idle', 'shore')")
        c.execute("INSERT INTO world_context (fragment_id, tuple_ts, source, place) "
                  "VALUES ('legacy1', 1000.0, 'idle', 'shore')")
    c.commit()
    c.close()
    return p


def legacy_snapshot(db):
    c = sqlite3.connect(str(db))
    try:
        return (c.execute("SELECT * FROM fragment_context WHERE fragment_id='legacy1'").fetchall(),
                c.execute("SELECT * FROM world_context WHERE fragment_id='legacy1'").fetchall(),
                c.execute("SELECT COUNT(*) FROM fragment_context").fetchone()[0])
    finally:
        c.close()


# ---- 1. migration on an old-schema DB ------------------------------------------------------------------------------
db = fresh_db("old.db")
check("moment_ts" not in cols(db, "fragment_context") and "moment_ts" not in cols(db, "world_context"),
      "old-schema context tables start without moment_ts")
before = legacy_snapshot(db)
store._MOMENT_TS_READY.clear()
store.init_db()                                           # init hook adds the column to both existing tables
check(cols(db, "fragment_context").count("moment_ts") == 1 and cols(db, "world_context").count("moment_ts") == 1,
      "init_db() adds moment_ts to both tables")
after = legacy_snapshot(db)
check(after[2] == before[2] and after[0][0][:-2] == before[0][0] and after[0][0][-2] is None   # J-3479 adds own_moment_ts as the last column
      and after[1][0][-2] is None, f"legacy rows unchanged and moment_ts NULL: {after[0]}")
store._MOMENT_TS_READY.clear()
store.init_db()
check(cols(db, "fragment_context").count("moment_ts") == 1, "idempotent on a second init_db()")
store._MOMENT_TS_READY.clear()
c = sqlite3.connect(str(db))
check(store._ensure_moment_ts_cols(c) is True, "helper is safe on a DB that already has the column")
c.close()

# ---- 2. stamping ---------------------------------------------------------------------------------------------------
db = fresh_db("stamp.db", old_ctx=False)
moment._CURRENT = None
moment._CURRENT_LOADED = True                              # no current moment (and no lazy state read)
fid_none = store.store_fragment("the tide is out and the cat sleeps by the fire in the evening", origin="inner_thought")
fc, wc = ctx(db, fid_none)
check(len(fc) == 1 and len(wc) == 1, f"context rows written with no current moment (fc={fc}, wc={wc})")
check(bool(fc) and fc[0][0] is None and bool(wc) and wc[0][0] is None, "no current moment -> moment_ts NULL on both")
check("moment_ts" in cols(db, "fragment_context") and "moment_ts" in cols(db, "world_context"),
      "tables carry moment_ts after the first store_fragment")

moment._set_current(1730000123.4, 7)
fid1 = store.store_fragment("a second thought about the garden at dusk and the lamp", origin="inner_thought")
fc, wc = ctx(db, fid1)
check(fc == [(1730000123.4,)] and wc == [(1730000123.4,)], f"stamped on both rows: fc={fc} wc={wc}")
fid_old = store.store_fragment("this one is stored by another origin entirely so it carries the stamp too",
                               origin="reading")
fc2, wc2 = ctx(db, fid_old)
check(fc2 == [(1730000123.4,)], f"every origin stamped (reading): {fc2}")

# ---- 2b. first store_fragment on a DB whose context tables lack the column migrates in place -----------------------
db = fresh_db("lazy.db")
store._MOMENT_TS_READY.clear()
c = sqlite3.connect(str(db))
c.close()
moment._set_current(1730000999.9, 9)
# simulate "process started before the column existed": strip the readiness flag, call store_fragment directly
fid_l = store.store_fragment("lazy migration thought about the gulls over the grey water", origin="inner_thought")
fc, wc = ctx(db, fid_l)
check(fc == [(1730000999.9,)], f"store_fragment path also stamps right after init_db migrated: {fc}")

# ---- 3. kill-switch ------------------------------------------------------------------------------------------------
db = fresh_db("ks.db", old_ctx=False)
moment._set_current(1730000555.5, 3)
store.MOMENT_TS_STAMP = False
fid_ks = store.store_fragment("kill switch thought about the wind in the dark wood tonight", origin="inner_thought")
fc, wc = ctx(db, fid_ks)
check(len(fc) == 1 and fc[0][0] is None and wc[0][0] is None, f"kill-switch -> NULL, rows still written: {fc} {wc}")
store.MOMENT_TS_STAMP = True

# ---- 4. fail-open when the migration cannot complete ---------------------------------------------------------------
_real = store._ensure_moment_ts_cols
store._ensure_moment_ts_cols = lambda conn: False
fid_fo = store.store_fragment("fail open thought about the lamp going out in the study", origin="inner_thought")
store._ensure_moment_ts_cols = _real
fc, wc = ctx(db, fid_fo)
check(len(fc) == 1 and len(wc) == 1 and fc[0][0] is None, f"migration failure -> old INSERT, row still written: {fc} {wc}")
_cm = moment.current


def _boom():
    raise RuntimeError("boom")


moment.current = _boom
fid_ex = store.store_fragment("exception thought about the sea breaking over the rocks again", origin="inner_thought")
moment.current = _cm
fc, wc = ctx(db, fid_ex)
check(len(fc) == 1 and fc[0][0] is None, f"moment.current() raising -> NULL, row written: {fc}")

# ---- 5. hot-path cost ----------------------------------------------------------------------------------------------
c = sqlite3.connect(str(db))
store._MOMENT_TS_READY.clear()
store._ensure_moment_ts_cols(c)                           # prime the cache
t0 = time.perf_counter()
N = 20000
for _ in range(N):
    store._ensure_moment_ts_cols(c)
    store._current_moment_ts()
per = (time.perf_counter() - t0) / N * 1e6
c.close()
print(f"INFO cached readiness check + current ts read: {per:.2f} microseconds per store_fragment")
check(per < 100.0, "hot-path addition is microseconds (a store_fragment is milliseconds of embedding + SQL)")

# ---- 6. validator --------------------------------------------------------------------------------------------------
sys.path.insert(0, str(TREE / "scripts"))
import moment_key_validate as mkv                           # noqa: E402
vdb = _TMP / "validate.db"
store.DB_PATH = vdb
store._MOMENT_TS_READY.clear()
store.init_db()
c = sqlite3.connect(str(vdb))
c.execute(memory_edges._CTX_SCHEMA)
c.execute("ALTER TABLE fragment_context ADD COLUMN moment_ts REAL")
base = 1730001000.0
thoughts = [f"thought number {i} about the shore and the slow tide coming in over the grey stones" for i in range(4)]
mpath = _TMP / "vmoments.jsonl"
with open(mpath, "w", encoding="utf-8") as f:
    for i, t in enumerate(thoughts):
        f.write(json.dumps({"ts": base + i * 60, "thought": t}) + "\n")
# fragment 1: stamped with its OWN moment (exact) -- fragment 2: stamped with the moment BEFORE (lag1) --
# fragment 3: stamped with an unrelated moment (other) -- fragment 0: not stamped (excluded).
plan = [(0, None), (1, base + 1 * 60), (2, base + 1 * 60), (3, base + 0)]
for i, stamp in plan:
    fid = f"vf{i}"
    c.execute("INSERT INTO memory_fragments (fragment_id, content, layer, relevance, timestamp, origin) "
              "VALUES (?,?,?,?,?,?)", (fid, thoughts[i], "episodic", 0.5, base + i * 60 + 2, "inner_thought"))
    c.execute("INSERT INTO fragment_context (fragment_id, tuple_ts, source, moment_ts) VALUES (?,?,?,?)",
              (fid, base + i * 60, "experienced:inner_thought", stamp))
c.commit()
c.close()
res = mkv.validate(vdb, mpath)
check(res["inner_thought_stamped"] == 3 and res["heuristic_unique"] == 3, f"validator counts: {res}")
check(res["exact"] == 1 and res["lag1"] == 1 and res["other"] == 1, f"validator exact/lag1/other = 1/1/1: {res}")
check(abs(res["share_exact_or_lag1"] - 0.6667) < 1e-3 and res["defeater_met_99pct"] is False,
      f"validator shares: {res}")
old_db = _TMP / "plain.db"
c = sqlite3.connect(str(old_db))
c.execute(memory_edges._CTX_SCHEMA)
c.execute("CREATE TABLE memory_fragments (fragment_id TEXT PRIMARY KEY, content TEXT, timestamp REAL, origin TEXT)")
c.commit()
c.close()
check("error" in mkv.validate(old_db, mpath), "validator reports (not crashes) when moment_ts is absent")

print()
if _fails:
    print(f"{len(_fails)} FAILED")
    sys.exit(1)
print("ALL PASS")
