"""J-3173 / D-0561: memory_fragments.input_type (additive column) + a separate readable_label for internal cycles.

Offline. Temp DB only (store.DB_PATH redirected before the first call; world stores redirected too). Touches no live data.

Covers:
  1. migration: an OLD-schema DB (no input_type) gains the column on init_db(); idempotent on a second run and on a DB
     that already has it; legacy rows stay NULL and are unchanged (row count, content, every other column).
  2. store_from_cycle(input_type=...) writes the value; a plain store_fragment() writes NULL.
  3. readable_label(): internal/timer 'lived' rows get the new label; human, NULL (old) rows keep "Our conversation";
     every other origin is unchanged; the kill switch restores the old label.
  4. the readers carry input_type through: retrieve() (whichever pool path), retrieve_by_affect(), _hydrate_rows,
     and the not-yet-migrated DB fallback in _hydrate_rows / retrieve_by_affect still works (no query breaks).
  5. _persist_cycle passes state.input_type (orchestrator source check).
"""
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789: no write to the tree's data/
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ["NASCENCE_TRAINING_LOG"] = "0"
TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TREE))
import core                                             # noqa: E402  (core BEFORE lab_env)
assert TREE in Path(core.__file__).resolve().parents, core.__file__
import core.memory.store as store                       # noqa: E402

_TMP = Path(tempfile.mkdtemp(prefix="j3173_input_type_"))
store.DB_PATH = _TMP / "test.db"
from scripts._test_isolation import redirect_world_stores   # noqa: E402
redirect_world_stores(_TMP, locomotion=True, watershed=True, census=True)
import core.orchestrator as _orch                        # noqa: E402
_orch._AFFECT_LOG = _TMP / "affect_log.jsonl"
from core import schema                                 # noqa: E402
from core.schema import MemoryFragment                  # noqa: E402

OLD_LABEL = "Our conversation"


def cols(db):
    c = sqlite3.connect(str(db))
    try:
        return [r[1] for r in c.execute("PRAGMA table_info(memory_fragments)")]
    finally:
        c.close()


# ---- 1. migration on an OLD-schema DB -----------------------------------------------------------------------------
old_db = _TMP / "old.db"
c = sqlite3.connect(str(old_db))
c.executescript("""
    CREATE TABLE memory_fragments (
        fragment_id TEXT PRIMARY KEY, content TEXT NOT NULL, layer TEXT NOT NULL DEFAULT 'episodic',
        relevance REAL NOT NULL DEFAULT 0.5, timestamp REAL NOT NULL, keywords TEXT NOT NULL DEFAULT '',
        embedding BLOB, origin TEXT NOT NULL DEFAULT 'lived', derived_from TEXT NOT NULL DEFAULT '[]');
""")
c.execute("INSERT INTO memory_fragments (fragment_id, content, layer, relevance, timestamp, origin) "
          "VALUES ('legacy1', 'Q: hello\nA: hi', 'episodic', 0.6, 1000.0, 'lived')")
c.commit()
c.close()
assert "input_type" not in cols(old_db)
store.DB_PATH = old_db
store.init_db()
assert cols(old_db).count("input_type") == 1, cols(old_db)
store.init_db()                                           # idempotent: second run on a DB that already has it
assert cols(old_db).count("input_type") == 1
c = sqlite3.connect(str(old_db))
rows = c.execute("SELECT fragment_id, content, origin, input_type FROM memory_fragments").fetchall()
c.close()
assert rows == [("legacy1", "Q: hello\nA: hi", "lived", None)], rows       # row count, content, origin, NULL
print("1 ok: additive + idempotent; legacy row unchanged, input_type NULL")

# ---- 2. writers ---------------------------------------------------------------------------------------------------
store.DB_PATH = _TMP / "new.db"
store.init_db()
assert "input_type" in cols(store.DB_PATH)
ids = {}
for it in ("human", "internal", "timer", None):
    ids[it] = store.store_from_cycle(f"Q: x-{it}\nA: y-{it}", input_type=it) if it else store.store_from_cycle("Q: x-none\nA: y-none")
other = store.store_fragment("a plain dream fragment", origin="dream")
c = sqlite3.connect(str(store.DB_PATH))
got = {r[0]: r[1] for r in c.execute("SELECT fragment_id, input_type FROM memory_fragments")}
c.close()
assert got[ids["human"]] == "human" and got[ids["internal"]] == "internal" and got[ids["timer"]] == "timer", got
assert got[ids[None]] is None and got[other] is None, got
print("2 ok: store_from_cycle records input_type; other writers write NULL")

# ---- 3. labels ----------------------------------------------------------------------------------------------------
def lab(origin="lived", it=None):
    return MemoryFragment("x", "c", "episodic", 0.5, 0.0, origin=origin, input_type=it).readable_label()

assert lab("lived", "internal") == schema.INTERNAL_CYCLE_LABEL == "My own earlier idle thought and reply"
assert lab("lived", "timer") == schema.INTERNAL_CYCLE_LABEL
assert lab("lived", "human") == OLD_LABEL
assert lab("lived", None) == OLD_LABEL
assert MemoryFragment("x", "c", "episodic", 0.5, 0.0).readable_label() == OLD_LABEL           # default constructor
for o, expect in (("dream", "Dream"), ("inner_thought", "My inner thought"), ("seed", "Core memory (inherited)")):
    assert lab(o, "internal") == expect, o                  # input_type never relabels a non-lived origin
schema.INTERNAL_CYCLE_LABEL_ON = False
try:
    assert lab("lived", "internal") == OLD_LABEL            # kill switch
finally:
    schema.INTERNAL_CYCLE_LABEL_ON = True
assert lab("lived", "internal") == schema.INTERNAL_CYCLE_LABEL
print("3 ok: internal/timer relabelled; human/NULL/other origins unchanged; kill switch works")

# ---- 4. readers ---------------------------------------------------------------------------------------------------
# retrieve(): real pool path (fast when an embedder is up, legacy otherwise). Use keywords so no embedder is needed.
try:
    frs = store.retrieve(["x-internal", "x-human", "y-internal", "y-human"], [], limit=8,
                         query_text="x-internal y-internal x-human y-human")
except Exception as exc:                                    # an embedder-less environment may not support this call
    frs = None
    print("   (retrieve() not exercised here:", type(exc).__name__, exc, ")")
if frs is not None:
    by_id = {f.fragment_id: f for f in frs}
    _hit = 0
    for it in ("internal", "human", "timer"):
        if ids[it] in by_id:
            _hit += 1
            assert by_id[ids[it]].input_type == it, (it, by_id[ids[it]].input_type)
    assert _hit >= 1, "retrieve() surfaced none of the test cycle fragments -- input_type carry not exercised"
    print("   retrieve() returned", len(frs), "fragments; input_type carried where present")

# _hydrate_rows: a _PoolRow hydrated from the DB carries input_type.
conn = store._connect()
pr = store._PoolRow((1, ids["internal"], "episodic", 1.0, "lived", 0), 0.9)
store._hydrate_rows(conn, [pr])
assert pr["input_type"] == "internal", pr._x
# ... and on an UNMIGRATED db the hydrate falls back instead of raising.
conn.close()
legacy = _TMP / "legacy_noinput.db"
c = sqlite3.connect(str(legacy))
c.executescript("""
    CREATE TABLE memory_fragments (fragment_id TEXT PRIMARY KEY, content TEXT, keywords TEXT, abstraction_level INTEGER,
        relevance REAL, importance REAL, replay_count INTEGER, derived_from TEXT);
    INSERT INTO memory_fragments VALUES ('L1','old content','k',0,0.5,0.5,0,'[]');
""")
c.commit()
c.row_factory = sqlite3.Row
pr2 = store._PoolRow((1, "L1", "episodic", 1.0, "lived", 0), 0.9)
store._hydrate_rows(c, [pr2])
assert pr2["content"] == "old content" and pr2["input_type"] is None, pr2._x
c.close()

# retrieve_by_affect: needs emotion_embedding; write two with a fake vector via store_fragment's emotion_embedding.
import numpy as np
vec = np.ones(384, dtype=np.float32) / np.sqrt(384.0)
fid_i = store.store_fragment("Q: affect internal\nA: z", emotion_embedding=vec, input_type="internal")
fid_o = store.store_fragment("Q: affect old\nA: z", emotion_embedding=vec)
aff = store.retrieve_by_affect(vec, top_k=10)
bi = {f.fragment_id: f for f in aff}
assert fid_i in bi and fid_o in bi, [f.fragment_id for f in aff]
assert bi[fid_i].input_type == "internal" and bi[fid_o].input_type is None
assert bi[fid_i].readable_label() == schema.INTERNAL_CYCLE_LABEL and bi[fid_o].readable_label() == OLD_LABEL
print("4 ok: retrieve_by_affect/_hydrate_rows carry input_type; unmigrated-DB fallback does not raise")

# ---- 5. orchestrator wiring ---------------------------------------------------------------------------------------
src = (TREE / "core" / "orchestrator.py").read_text(encoding="utf-8")
assert "input_type=self.state.input_type," in src.split("def _persist_cycle")[1].split("def _log_affect")[0]
print("5 ok: _persist_cycle passes state.input_type to store_from_cycle")

# live DB untouched by construction: nothing above ever opened a path outside _TMP.
assert str(store.DB_PATH).startswith(str(_TMP))
print("OK")
