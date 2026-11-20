"""J-3479 (F-4017 / J-3393): own_moment_ts -- the moment a fragment's OWN cycle bound, stamped after moment.record.

Offline, temp DB + temp moment files only (store.DB_PATH and moment._LOG/_STATE redirected before any call). Touches no
live data, never opens data/memory/nascence.db, calls no model.

Covers:
  1. migration on an OLD-schema DB: init_db() adds own_moment_ts to both context tables, legacy rows stay NULL, idempotent.
  2. the real order of _think(): store_fragment (moment_ts = PREVIOUS moment) then moment.record (returns its ts) then
     stamp_own_moment -> own_moment_ts is the NEW moment on both rows, moment_ts is untouched (still the previous one);
     moments.jsonl's last row ts equals own_moment_ts exactly.
  3. idempotent / never overwrites; a second stamp with another ts changes nothing.
  4. exact-dedup guard: a fragment whose context tuple_ts is old (an existing row a dedup hit returned) is NOT stamped.
  5. kill-switch (OWN_MOMENT_TS_STAMP=False) -> NULL; fail-open on a missing fragment id / None ts / missing tables.
  6. moment.record() return value: ts when bound, None for an empty thought; callers ignoring it are unaffected.
  7. scripts/moment_key_validate.py own_exact share, and the measurement script's lag1 classification on a synthetic set.
  8. wiring: inner_monologue_node._think captures the store id and stamps after record (source assertion).
"""
import importlib.util
import json
import os
import sqlite3
import sys
import tempfile
import time as _t
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

_TMP = Path(tempfile.mkdtemp(prefix="j3479_own_moment_"))
store.DB_PATH = _TMP / "test.db"
from scripts._test_isolation import redirect_world_stores   # noqa: E402
redirect_world_stores(_TMP, locomotion=True, watershed=True, census=True)
moment._LOG = _TMP / "moments.jsonl"
moment._STATE = _TMP / "moment_state.json"
moment._DATA = _TMP
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


def both(db, fid):
    c = sqlite3.connect(str(db))
    try:
        # own_moment_ts may not exist yet on a table created after init_db (it is added lazily by the first stamp)
        has = "own_moment_ts" in [r[1] for r in c.execute("PRAGMA table_info(fragment_context)")]
        q = "SELECT moment_ts, " + ("own_moment_ts" if has else "NULL") + ", tuple_ts FROM {} WHERE fragment_id=?"
        return (c.execute(q.format("fragment_context"), (fid,)).fetchall(),
                c.execute(q.format("world_context"), (fid,)).fetchall())
    finally:
        c.close()


def fresh_db(name, old_ctx=True):
    p = _TMP / name
    store.DB_PATH = p
    store._MOMENT_TS_READY.clear()
    store._OWN_MOMENT_READY.clear()
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


def last_moment_ts():
    rows = [json.loads(x) for x in open(moment._LOG, encoding="utf-8") if x.strip()]
    return rows[-1]["ts"], len(rows)


# ---- 1. migration --------------------------------------------------------------------------------------------------
db = fresh_db("old.db")
check("own_moment_ts" not in cols(db, "fragment_context"), "old-schema context tables start without own_moment_ts")
store._OWN_MOMENT_READY.clear()
store.init_db()
check(cols(db, "fragment_context").count("own_moment_ts") == 1 and cols(db, "world_context").count("own_moment_ts") == 1,
      "init_db() adds own_moment_ts to both tables")
c = sqlite3.connect(str(db))
leg = c.execute("SELECT moment_ts, own_moment_ts FROM fragment_context WHERE fragment_id='legacy1'").fetchall()
c.close()
check(leg == [(None, None)], f"legacy row untouched, both stamps NULL: {leg}")
store._OWN_MOMENT_READY.clear()
store.init_db()
check(cols(db, "fragment_context").count("own_moment_ts") == 1, "idempotent on a second init_db()")

# ---- 2. the real _think() order ------------------------------------------------------------------------------------
db = fresh_db("order.db", old_ctx=False)
moment._CURRENT = None
moment._CURRENT_LOADED = True
prev_ts = moment.record("the previous cycle thought about the gulls over the grey water this morning")
check(prev_ts is not None, f"record() returns the bound moment ts: {prev_ts}")
_t.sleep(0.15)
fid = store.store_fragment("this cycle thought about the shore and the slow tide coming in over the stones",
                           origin="inner_thought")                                # 1) store first, as _think does
_t.sleep(0.15)
own_ts = moment.record("this cycle thought about the shore and the slow tide coming in over the stones")   # 2) bind
check(own_ts is not None and own_ts >= prev_ts, f"second record() returned a ts: {own_ts}")
fc, wc = both(db, fid)
check(fc[0][0] == prev_ts and wc[0][0] == prev_ts,
      f"BEFORE the stamp, moment_ts is the PREVIOUS moment (F-4017): {fc} {wc}")
check(fc[0][1] is None and wc[0][1] is None, "own_moment_ts starts NULL")
check(store.stamp_own_moment(fid, own_ts) is True, "stamp_own_moment returns True")
fc, wc = both(db, fid)
check(fc[0][1] == own_ts and wc[0][1] == own_ts, f"own_moment_ts is the NEW moment on both rows: {fc} {wc}")
check(fc[0][0] == prev_ts and wc[0][0] == prev_ts, "moment_ts is unchanged (ruled D-0634 semantics kept)")
lt, n = last_moment_ts()
check(lt == own_ts and n == 2, f"own_moment_ts equals moments.jsonl's last row ts ({lt}, rows={n})")

# ---- 3. idempotent, never overwrites ------------------------------------------------------------------------------
check(store.stamp_own_moment(fid, own_ts + 500.0) is False, "second stamp with another ts is a no-op (False)")
fc, wc = both(db, fid)
check(fc[0][1] == own_ts and wc[0][1] == own_ts, "never overwritten")

# ---- 4. exact-dedup guard ------------------------------------------------------------------------------------------
c = sqlite3.connect(str(db))
c.execute("INSERT INTO fragment_context (fragment_id, tuple_ts, source) VALUES ('oldrow', ?, 'experienced:inner_thought')",
          (own_ts - 7200.0,))
c.execute("INSERT INTO world_context (fragment_id, tuple_ts, source) VALUES ('oldrow', ?, 'inner_thought')",
          (own_ts - 7200.0,))
c.commit()
c.close()
check(store.stamp_own_moment("oldrow", own_ts) is False, "a dedup-returned OLD fragment (tuple_ts 2 h earlier) is not stamped")
fc, wc = both(db, "oldrow")
check(fc[0][1] is None and wc[0][1] is None, "old row still NULL")

# ---- 5. kill-switch and fail-open ----------------------------------------------------------------------------------
fid2 = store.store_fragment("kill switch thought about the wind in the dark wood tonight again", origin="inner_thought")
store.OWN_MOMENT_TS_STAMP = False
ts2 = moment.record("kill switch thought about the wind in the dark wood tonight again")
check(store.stamp_own_moment(fid2, ts2) is False, "kill-switch -> False")
fc, _w = both(db, fid2)
check(fc[0][1] is None, "kill-switch -> NULL, row intact")
store.OWN_MOMENT_TS_STAMP = True
check(store.stamp_own_moment("no-such-id", ts2) is False, "unknown fragment id -> False, no raise")
check(store.stamp_own_moment(None, ts2) is False and store.stamp_own_moment(fid2, None) is False,
      "None id / None ts -> False")
_real = store._connect


def _boom():
    raise RuntimeError("db gone")


store._connect = _boom
check(store.stamp_own_moment(fid2, ts2) is False, "a failing connection is swallowed (fail-open)")
store._connect = _real
check(store.stamp_own_moment(fid2, ts2) is True, "and the stamp works once the DB is back")
bare = _TMP / "bare.db"
store.DB_PATH = bare
store._OWN_MOMENT_READY.clear()
check(store.stamp_own_moment("x", 1.0) is False, "no context tables -> False, no raise")
store.DB_PATH = db
store._OWN_MOMENT_READY.clear()

# ---- 6. record() return value --------------------------------------------------------------------------------------
check(moment.record("") is None and moment.record("   ") is None, "empty thought -> None")
check(isinstance(moment.record("a plain call that ignores the return value as before"), float), "non-empty -> float ts")

# ---- 7. validator + measurement script -----------------------------------------------------------------------------
sys.path.insert(0, str(TREE / "scripts"))
import moment_key_validate as mkv                           # noqa: E402
spec = importlib.util.spec_from_file_location("meas", TREE / "scripts" / "measure_J-3479_moment_ts_offbyone.py")
meas = importlib.util.module_from_spec(spec)
spec.loader.exec_module(meas)
base = _t.time() - 3600.0
thoughts = [f"thought number {i} about the shore and the slow tide coming in over the grey stones" for i in range(4)]
mpath = _TMP / "vm.jsonl"
with open(mpath, "w", encoding="utf-8") as f:
    for i, t in enumerate(thoughts):
        f.write(json.dumps({"ts": base + i * 60, "thought": t}) + "\n")
vdb = _TMP / "v.db"
store.DB_PATH = vdb
store._MOMENT_TS_READY.clear()
store._OWN_MOMENT_READY.clear()
store.init_db()
c = sqlite3.connect(str(vdb))
c.execute(memory_edges._CTX_SCHEMA)
for col in ("moment_ts", "own_moment_ts"):
    c.execute(f"ALTER TABLE fragment_context ADD COLUMN {col} REAL")
for i in range(1, 4):       # each fragment stored 1 s BEFORE its own moment (the live shape); moment_ts = previous moment
    fid_ = f"vf{i}"
    c.execute("INSERT INTO memory_fragments (fragment_id, content, layer, relevance, timestamp, origin) "
              "VALUES (?,?,?,?,?,?)", (fid_, thoughts[i], "episodic", 0.5, base + i * 60 - 1, "inner_thought"))
    c.execute("INSERT INTO fragment_context (fragment_id, tuple_ts, source, moment_ts, own_moment_ts) VALUES (?,?,?,?,?)",
              (fid_, base + i * 60 - 1, "experienced:inner_thought", base + (i - 1) * 60,
               (base + i * 60) if i < 3 else (base + 0.0)))     # vf3 carries a WRONG own stamp (a defect to be seen)
c.commit()
c.close()
res = mkv.validate(vdb, mpath)
check(res["lag1"] == 3 and res["own_unique"] == 3 and res["own_exact"] == 2 and res["own_other"] == 1,
      f"validator: moment_ts is lag1 x3, own stamp exact x2 / other x1: {res}")
check(abs(res["share_own_exact"] - 0.6667) < 1e-3, "validator share_own_exact")
m = meas.measure(vdb, mpath, since_days=1.0)
check(m["unique"] == 3 and m["lag1"] == 3 and m["own"] == 0 and m["share_lag1"] == 1.0
      and m["frag_before_own_moment"] == 3, f"measurement script: replayed moment_ts rule is lag1 on all 3: {m}")

# ---- 8. wiring -----------------------------------------------------------------------------------------------------
src = (TREE / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
i_store = src.index("_inner_fid = store_fragment(")
i_rec = src.index("_own_mts = _mom.record(")
i_stamp = src.index("_stamp_own(_inner_fid, _own_mts)")
check(i_store < i_rec < i_stamp, "node: store captures the id, record returns the ts, stamp runs after both")

print()
if _fails:
    print(f"{len(_fails)} FAILED")
    sys.exit(1)
print("ALL PASS")
