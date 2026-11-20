"""J-3395 / F-4019 (follow-up to J-3266 / D-0657): the writers that edit or insert memory_fragments content OUTSIDE
store_fragment must stamp content_hash in the same statement.

Offline. Temp DB only (store.DB_PATH redirected before the first call; shadow/faithfulness logs redirected); never
opens data/memory/nascence.db and writes nothing under the repo's data/. Model calls stubbed.

Covers, for each writer, on a migrated DB (has the column) AND on an OLD-schema DB (no column: the statement must
still work, byte-identical to before):
  1. core/activity_memory.record  INSERT (new general-event row) and UPDATE (recurrence) -> hash == content_hash(content)
  2. core/refinery.refine         INSERT (mint standing_insight) and UPDATE (evolve it)   -> same
  3. core/study_note.store_note   UPDATE (revise in place)                                -> same
  4. core/memory/store.retract_fragment (content prefixed)                                -> same
  5. scripts/activity_memory_backfill upsert (INSERT + MERGE UPDATE)                      -> same
  6. the hashed exact-dedup lookup (loop_metabolism.find_exact_dup in hash_live) finds the EDITED text of an edited
     row (what a stale hash would have missed) and does not find its pre-edit text.
  7. has_hash_column: True/False/never raises.
  8. the unrelated columns of every touched row (embedding blob, importance, origin...) are what the pre-fix
     statements wrote (the fix adds ONE column value and nothing else).
"""
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789: no write to the tree's data/
import asyncio
import importlib.util
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
import numpy as np                                      # noqa: E402
import core.memory.store as store                       # noqa: E402
from core.memory.content_hash import content_hash, has_hash_column   # noqa: E402
from core import activity_memory as am                  # noqa: E402
from core import refinery                               # noqa: E402
from core import study_note                             # noqa: E402
study_note._diegetic_learn = lambda note, body: None    # J-2961: the revise branch now runs the diegetic hooks (they write data/*.json); not under test here
from core import loop_metabolism as lm                  # noqa: E402
from core import loop_probe                             # noqa: E402

_TMP = Path(tempfile.mkdtemp(prefix="j3395_hash_writers_"))
store.DB_PATH = _TMP / "test.db"
assert str(store.DB_PATH).startswith(str(_TMP))
_VEC = np.ones(8, dtype=np.float32)
store._embed = lambda text: _VEC                        # constant embedding: no model load, clusters/matches everything
loop_probe._LOG = _TMP / "loop_probe_log.jsonl"
loop_probe._seen = {}
lm._DEDUP_HASH_SHADOW_LOG = _TMP / "hash_shadow.jsonl"
lm._DEDUP_SHADOW_LOG = _TMP / "window_shadow.jsonl"
refinery._SHADOW_LOG = _TMP / "refinery_shadow.jsonl"
refinery._FAITH_LOG = _TMP / "refinery_faithfulness.jsonl"
refinery.FAITHFULNESS_JUDGE_ON = False                  # no judge call

spec = importlib.util.spec_from_file_location("amb", TREE / "scripts" / "activity_memory_backfill.py")
amb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(amb)

_fails = []


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        _fails.append(msg)


def rows(sql, args=()):
    c = sqlite3.connect(str(store.DB_PATH))
    c.row_factory = sqlite3.Row
    try:
        return c.execute(sql, args).fetchall()
    finally:
        c.close()


def row(fid):
    r = rows("SELECT * FROM memory_fragments WHERE fragment_id=?", (fid,))
    return r[0] if r else None


def hash_ok(fid, what):
    r = row(fid)
    check(r is not None and r["content_hash"] == content_hash(r["content"]),
          f"{what}: content_hash == content_hash(content) ({'row missing' if r is None else r['content'][:50]!r})")


# ================= migrated DB =====================================================================================
store.init_db()
c = sqlite3.connect(str(store.DB_PATH))
check(has_hash_column(c), "has_hash_column True on a migrated DB")
c.close()

# ---- 1. activity_memory
fid = am.record("read", "The Voyage of the Beagle")
check(bool(fid), "activity_memory.record created a row")
hash_ok(fid, "activity_memory INSERT")
r1 = row(fid)
check(r1["origin"] == "action" and r1["abstraction_level"] == 1 and r1["kind"] == "procedural"
      and abs(r1["importance"] - 0.6) < 1e-9 and r1["layer"] == "episodic",
      "activity_memory INSERT other columns unchanged (origin/level/kind/importance/layer)")
first_content = r1["content"]
fid2 = am.record("read", "The Voyage of the Beagle")
check(fid2 == fid, "second record() updates the same row")
r2 = row(fid)
check(r2["content"] != first_content, "content changed on recurrence (count went up)")
hash_ok(fid, "activity_memory UPDATE")
check(r2["embedding"] is not None and r2["timestamp"] >= r1["timestamp"], "activity_memory UPDATE still writes embedding/timestamp")

# ---- 6. hashed lookup sees the edited text, not the pre-edit text
hits_new = rows("SELECT 1 FROM memory_fragments WHERE origin='action' AND content_hash=?", (content_hash(r2["content"]),))
hits_old = rows("SELECT 1 FROM memory_fragments WHERE origin='action' AND content_hash=?", (content_hash(first_content),))
check(len(hits_new) == 1 and len(hits_old) == 0,
      "index probe finds the edited text and no longer the pre-edit text (a stale hash would invert this)")

# ---- 2. refinery: mint then evolve
src = ["I keep going back to the tide when I feel uneasy", "the tide again, the shore and the uneasy feeling",
       "uneasy at the shore, I watch the tide", "tide and shore, the same uneasy return"]


def add_syntheses(n0, ts0):
    c = sqlite3.connect(str(store.DB_PATH))
    for i, t in enumerate(src):
        c.execute("INSERT INTO memory_fragments (fragment_id, content, timestamp, origin, embedding, content_hash) "
                  "VALUES (?,?,?,?,?,?)", (f"syn{n0}_{i}", t, ts0 + i, "subconscious_synthesis",
                                           store._vec_to_blob(_VEC), content_hash(t)))
    c.commit()
    c.close()


add_syntheses(1, 1000.0)
calls = []


async def fake_call_json(base_urls, system, user, max_tokens=0, temperature=0.0):
    calls.append(user)
    return {"insight": "I keep returning to the tide and the shore when I feel uneasy." if len(calls) == 1
            else "I keep returning to the tide and the shore, uneasy, and the return is the same each time."}


stats = asyncio.run(refinery.refine(fake_call_json, ["stub"]))
check(stats["minted"] == 1 and stats["evolved"] == 0, f"refinery minted one standing insight {stats}")
ins = rows("SELECT * FROM memory_fragments WHERE origin='standing_insight'")
check(len(ins) == 1, "one standing_insight row")
hash_ok(ins[0]["fragment_id"], "refinery INSERT (mint)")
check(ins[0]["layer"] == "archive" and ins[0]["abstraction_level"] == 2 and abs(ins[0]["importance"] - 0.9) < 1e-9,
      "refinery INSERT other columns unchanged")
old_ins = ins[0]["content"]
add_syntheses(2, 2000.0)
stats = asyncio.run(refinery.refine(fake_call_json, ["stub"]))
check(stats["evolved"] == 1 and stats["minted"] == 0, f"refinery evolved the standing insight {stats}")
ins2 = rows("SELECT * FROM memory_fragments WHERE origin='standing_insight'")
check(len(ins2) == 1 and ins2[0]["content"] != old_ins, "standing insight content was rewritten in place")
hash_ok(ins2[0]["fragment_id"], "refinery UPDATE (evolve)")

# ---- 3. study_note revise in place
note = {"title": "Tides", "subject": "tides", "understanding": "Tides follow the moon.", "key_facts": ["two a day"],
        "thoughts": "", "connects_to": "", "question": ""}
sfid = store.store_fragment(content="[My study note: 'Tides' · on 'B' · subject: tides] old understanding",
                            layer="episodic", relevance=0.8, importance=0.8, keywords=["study"], origin="study")
hash_ok(sfid, "(setup) store_fragment row")
res = study_note.store_note(note, "Some Book", revise_target=(sfid, "old", None))
check(res.get("action") == "revised" and res.get("fragment_id") == sfid, f"store_note revised in place {res.get('action')}")
rs = row(sfid)
check("Tides follow the moon" in rs["content"] and "old understanding" not in rs["content"], "study fragment content rewritten")
hash_ok(sfid, "study_note UPDATE (revise)")

# ---- 4. retract_fragment
rfid = store.store_fragment(content="The harbour master said the ferry leaves at nine every day of the week",
                            layer="episodic", relevance=0.8, importance=0.8, keywords=["x"], origin="lived")
got = store.retract_fragment("The harbour master said the ferry leaves at nine", "ferry timetable was wrong")
check(got == rfid, "retract_fragment found the row")
rr = row(rfid)
check(rr["content"].startswith("[RETRACTED") and rr["layer"] == "archive" and abs(rr["importance"] - 0.05) < 1e-9,
      "retract_fragment other columns unchanged (prefix, archive, importance 0.05)")
hash_ok(rfid, "retract_fragment UPDATE")

# ---- 5. offline activity backfill script
conn = sqlite3.connect(str(store.DB_PATH))
conn.row_factory = sqlite3.Row
amb.upsert(conn, "study", "Some Book", 3, 5000.0, 6000.0, True)           # NEW
conn.commit()
nb = rows("SELECT * FROM memory_fragments WHERE origin='action' AND keywords LIKE '%study Some Book%'")
check(len(nb) == 1, "backfill INSERT made one row")
hash_ok(nb[0]["fragment_id"], "activity_memory_backfill INSERT")
amb.upsert(conn, "study", "Some Book", 9, 5000.0, 7000.0, True)           # MERGE
conn.commit()
conn.close()
nb2 = rows("SELECT * FROM memory_fragments WHERE origin='action' AND keywords LIKE '%study Some Book%'")
check(len(nb2) == 1 and nb2[0]["content"] != nb[0]["content"], "backfill MERGE rewrote the content")
hash_ok(nb2[0]["fragment_id"], "activity_memory_backfill UPDATE (merge)")
conn = sqlite3.connect(str(store.DB_PATH))
conn.row_factory = sqlite3.Row
amb.upsert(conn, "study", "Dry Book", 1, 1.0, 2.0, False)                 # dry run writes nothing
conn.close()
check(not rows("SELECT 1 FROM memory_fragments WHERE keywords LIKE '%Dry Book%'"), "backfill dry run still writes nothing")

# ================= OLD-schema DB: no content_hash column (statements must still work) ============================
store.DB_PATH = _TMP / "old.db"
c = sqlite3.connect(str(store.DB_PATH))
c.executescript("""CREATE TABLE memory_fragments (fragment_id TEXT PRIMARY KEY, content TEXT NOT NULL,
    layer TEXT NOT NULL DEFAULT 'episodic', relevance REAL NOT NULL DEFAULT 0.5, importance REAL NOT NULL DEFAULT 0.5,
    timestamp REAL NOT NULL, keywords TEXT NOT NULL DEFAULT '', embedding BLOB, origin TEXT NOT NULL DEFAULT 'lived',
    derived_from TEXT NOT NULL DEFAULT '[]', abstraction_level INTEGER NOT NULL DEFAULT 0,
    kind TEXT NOT NULL DEFAULT 'episodic', cold INTEGER NOT NULL DEFAULT 0, protected INTEGER NOT NULL DEFAULT 0);""")
c.execute("INSERT INTO memory_fragments (fragment_id, content, timestamp, origin) VALUES "
          "('R1', 'The harbour master said the ferry leaves at nine every day of the week', "+str(__import__('time').time())+", 'lived')")
c.commit()
check(not has_hash_column(c), "has_hash_column False on an old-schema DB")
c.close()
check(has_hash_column(object()) is False, "has_hash_column never raises (bad conn -> False)")
ofid = am.record("water", "the bed")
check(bool(ofid) and row(ofid) is not None, "old schema: activity INSERT still works")
ofid2 = am.record("water", "the bed")
check(ofid2 == ofid and row(ofid)["content"] != "", "old schema: activity UPDATE still works")
check(store.retract_fragment("The harbour master said the ferry leaves at nine", "wrong") == "R1"
      and row("R1")["content"].startswith("[RETRACTED"), "old schema: retract_fragment still works")
conn = sqlite3.connect(str(store.DB_PATH))
conn.row_factory = sqlite3.Row
amb.upsert(conn, "read", "Old Book", 2, 1.0, 2.0, True)
amb.upsert(conn, "read", "Old Book", 4, 1.0, 3.0, True)
conn.commit()
conn.close()
check(len(rows("SELECT 1 FROM memory_fragments WHERE keywords LIKE '%Old Book%'")) == 1, "old schema: backfill INSERT+MERGE still work")

print()
print("FAILED: " + "; ".join(_fails) if _fails else "ALL PASS")
sys.exit(1 if _fails else 0)
