"""J-3191 / D-0578: mark the dict-repr understanding notes (temp='hidden') so Recall skips them. Offline, temp DBs only.
Never opens data/memory/nascence.db; writes nothing under the repo's data/.

Covers:
  1. is_dict_repr_body (Python) == SELECT_PREDICATE (SQL) on a table of tricky strings.
  2. selection: only origin='understanding' with a '{' / '[' body; prose understanding, a '{...}' lived row, and a
     '{...}' study row are NOT selected.
  3. mark/unmark: idempotent, content+embedding byte-identical, rows outside the selection unchanged, row count
     unchanged, unmark restores temp warm/cold (a cold row goes back to cold), an unrelated hidden row stays hidden.
  4. Recall skips marked rows and serves them again after unmark: store.retrieve (live fast/pool path), the legacy SQL
     path, associative_recall._refresh (the trail matrix), associative_recall._load_rows, evidence_recall._candidates.
  5. scripts/apply_J-3191_mark_dict_repr_notes.py on a COPY: dry run changes nothing; --write marks exactly the
     selection and prints before/after; second --write is a no-op; --expect mismatch refuses and writes nothing;
     refuses while a run_nascence.py process is "up"; scripts/unmark_dict_repr_notes.py restores.
"""
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789: no write to the tree's data/
import hashlib
import importlib.util
import io
import os
import contextlib
import shutil
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
import core                                              # noqa: E402  (core BEFORE lab_env)
assert TREE in Path(core.__file__).resolve().parents, core.__file__
import numpy as np                                       # noqa: E402
import core.memory.store as store                        # noqa: E402
from core.memory import dict_repr_notes as drn           # noqa: E402
from core import associative_recall as ar                # noqa: E402
from core import evidence_recall as er                   # noqa: E402

_TMP = Path(tempfile.mkdtemp(prefix="j3191_dict_repr_"))
store.DB_PATH = _TMP / "test.db"
assert str(store.DB_PATH).startswith(str(_TMP))
ar._EMB_CACHE = _TMP / "embedding_matrix.npz"
er._DB = store.DB_PATH
er._LOG = _TMP / "evidence_log.jsonl"
store._POOL_DELTA_SHADOW_LOG = _TMP / "pool_delta_shadow.jsonl"

_VEC = np.ones(384, dtype=np.float32) / np.sqrt(384.0)
store._embed = lambda text: _VEC.copy()                  # every row and every query share one direction: sims all equal
_fails = []


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        _fails.append(msg)


def sha_all(db):
    c = sqlite3.connect(str(db))
    try:
        h = hashlib.sha256()
        for row in c.execute("SELECT fragment_id, content, embedding, origin, layer, cold, temp FROM memory_fragments ORDER BY fragment_id"):
            h.update(repr(row).encode("utf-8", "surrogatepass"))
        return h.hexdigest()
    finally:
        c.close()


# ---- 1. python twin == SQL predicate ---------------------------------------------------------------------------------
tricky = [
    "[Understanding - from 'The Prince'] {'grasp_of_content': 'x'}",
    "[Understanding - from 'Pioneers'] [{'point': 'a'}]",
    "[Understanding - from 'The Prince'] Machiavelli argues that...",
    "[Understanding - from 'The Prince'] {",
    "[Understanding - from 'Book [one] two'] {'a': 1}",          # first '] ' is inside the title -> body starts 'two'
    "[Understanding - from 'X']{'no space after bracket'}",       # no '] ' at all -> from char 2: '[' ... see SQL
    "{'bare dict, no prefix'}",
    "[bare list no prefix",
    "plain text",
    "",
    "] ",
    "a] {",
]
c = sqlite3.connect(":memory:")
c.execute("CREATE TABLE memory_fragments (fragment_id TEXT, content TEXT, origin TEXT)")
for i, t in enumerate(tricky):
    c.execute("INSERT INTO memory_fragments VALUES (?,?, 'understanding')", (str(i), t))
sql_ids = {r[0] for r in c.execute(f"SELECT fragment_id FROM memory_fragments WHERE {drn.SELECT_PREDICATE}")}
py_ids = {str(i) for i, t in enumerate(tricky) if drn.is_dict_repr_body(t)}
check(sql_ids == py_ids, f"python twin == SQL predicate on {len(tricky)} strings (sql={sorted(sql_ids)} py={sorted(py_ids)})")
check(drn.is_dict_repr_body(None) is False, "None -> False, no raise")
c.close()

# ---- 2-4. a real schema DB ----------------------------------------------------------------------------------------------
store.init_db()
NOW = time.time()
ids = {}


def add(key, content, origin, layer="semantic", cold=False):
    ids[key] = store.store_fragment(content, layer=layer, origin=origin, importance=0.9, timestamp=NOW - len(ids), cold=cold,
                                    context_stamp=False)


add("d1", "[Understanding - from 'The Prince'] {'grasp_of_content': 'a', 'key_facts': [{'point': 'b'}]}", "understanding")
add("d2", "[Understanding - from 'Pioneers of Science'] [{'point': 'one'}, {'point': 'two'}]", "understanding")
add("d3", "[Understanding - from 'my recent reading'] {'Resolved Into Productive Tension': 'I am in conflict'}", "understanding")
add("dcold", "[Understanding - from 'Roughing It'] {'identity_complexity': 'x'}", "understanding", cold=True)
add("p1", "[Understanding - from 'The Prince'] Machiavelli argues that a ruler must be feared and loved in measure.", "understanding")
add("p2", "[Understanding - from 'Roughing It'] Twain's account of the Nevada silver rush is a study in boom and ruin.", "understanding")
add("lived_dict", "{'this is a lived row that happens to start with a brace'}", "lived", layer="episodic")
add("study_dict", "[Study - from 'X'] {'a study row with a dict body is not an understanding note'}", "study")
add("other_hidden", "a row somebody else hid on purpose", "lived", layer="episodic")
store.mark_hidden([ids["other_hidden"]])
store.init_db()           # a boot resyncs temp<-cold exactly as on Du's live DB (store_fragment alone leaves cold=1 rows 'warm')
DICT_KEYS = ["d1", "d2", "d3", "dcold"]
DICT_IDS = {ids[k] for k in DICT_KEYS}

conn = sqlite3.connect(str(store.DB_PATH))
conn.row_factory = sqlite3.Row
sel = drn.select_ids(conn)
check(set(sel) == DICT_IDS and len(sel) == 4,
      "selection = exactly the 4 dict-repr understanding notes (not prose understanding, not a lived/study row with a brace)")
check(all(drn.is_dict_repr_body(conn.execute("SELECT content FROM memory_fragments WHERE fragment_id=?", (i,)).fetchone()[0]) for i in sel),
      "every selected row passes the python twin too")
before_all = sha_all(store.DB_PATH)
n_rows0 = conn.execute("SELECT COUNT(*) FROM memory_fragments").fetchone()[0]
hist0 = drn.temp_histogram(conn)
check(hist0 == {"cold/cold=1": 1, "warm/cold=0": 3}, f"temp histogram before: {hist0}")
sha_sel0 = drn.rows_sha256(conn)


def retrieve_ids(**kw):
    frs = store.retrieve(episodic_keys=["x"], semantic_keys=["x"], time_bias="all", limit=40, query_text="the prince", **kw)
    return {f.fragment_id for f in frs}


def matrix_ids():
    ar._cache.update(ts=0.0, M=None, ids=None)
    ar._refresh(time.time())
    return set(ar._cache["ids"] or [])


def er_ids():
    return {r["fragment_id"] for r in er._candidates("the prince", k=50)} if True else set()


# BEFORE marking: the dict rows are reachable
r0 = retrieve_ids()
check(ids["d1"] in r0 and ids["d2"] in r0 and ids["d3"] in r0, f"retrieve (fast/pool path) serves unmarked dict-repr notes (got {len(r0)} rows)")
m0 = matrix_ids()
check({ids["d1"], ids["d2"], ids["d3"]} <= m0 and ids["dcold"] in m0, "associative matrix includes the dict-repr notes before marking")
check(set(ar._load_rows([ids["d1"], ids["p1"]]).keys()) == {ids["d1"], ids["p1"]}, "_load_rows returns them before marking")

# mark
n = drn.mark(conn)
conn.commit()
check(n == 4, f"mark() changed 4 rows (got {n})")
check(drn.mark(conn) == 0, "mark() is idempotent (second call changes 0)")
conn.commit()
hist1 = drn.temp_histogram(conn)
check(hist1 == {"hidden/cold=1": 1, "hidden/cold=0": 3}, f"all 4 hidden after mark; cold flags untouched: {hist1}")
check(conn.execute("SELECT COUNT(*) FROM memory_fragments").fetchone()[0] == n_rows0, "row count unchanged (nothing deleted)")
check(drn.rows_sha256(conn) == sha_sel0, "selected rows' (fragment_id, content) sha256 unchanged by mark")
rows_after = {r[0]: r[1] for r in conn.execute("SELECT fragment_id, temp FROM memory_fragments")}
check(rows_after[ids["p1"]] == "warm" and rows_after[ids["p2"]] == "warm" and rows_after[ids["lived_dict"]] == "warm"
      and rows_after[ids["study_dict"]] == "warm" and rows_after[ids["other_hidden"]] == "hidden",
      "rows outside the selection keep their temp (prose notes, lived/study brace rows warm; the other hidden row still hidden)")

# Recall skips them (same process, the delta cache is kept honest by the trg_pool_chg_upd trigger)
r1 = retrieve_ids()
check(not (DICT_IDS & r1) and ids["p1"] in r1 and ids["p2"] in r1,
      f"retrieve (fast/pool path) no longer serves any marked row, still serves prose notes (got {len(r1)} rows)")
saved_fast = store._RETRIEVE_FAST_PATH
store._RETRIEVE_FAST_PATH = False
try:
    r1l = retrieve_ids()
finally:
    store._RETRIEVE_FAST_PATH = saved_fast
check(not (DICT_IDS & r1l) and ids["p1"] in r1l, "retrieve (legacy SQL path) skips marked rows too")
m1 = matrix_ids()
check(not (DICT_IDS & m1) and ids["p1"] in m1, "associative matrix (trail / recall_block / recall_memory_fragments) skips marked rows")
check(set(ar._load_rows(list(DICT_IDS) + [ids["p1"]]).keys()) == {ids["p1"]}, "_load_rows (M2 edge-aware route) never hands back a marked row")
try:
    ev = {r["fragment_id"] for r in er._candidates("the prince", k=50)}
    check(not (DICT_IDS & ev) and ids["p1"] in ev, "evidence_recall._candidates skips marked rows, keeps prose notes")
except Exception as exc:                                  # the judge / embed stack may not be available offline
    check(False, f"evidence_recall._candidates raised {exc!r}")

# unmark
check(drn.unmark(conn) == 4, "unmark() restored 4 rows")
conn.commit()
check(drn.unmark(conn) == 0, "unmark() is idempotent")
conn.commit()
check(drn.temp_histogram(conn) == hist0, "temp histogram restored exactly (the cold row is back to cold)")
check(conn.execute("SELECT temp FROM memory_fragments WHERE fragment_id=?", (ids["other_hidden"],)).fetchone()[0] == "hidden",
      "unmark does not touch an unrelated hidden row")
check(sha_all(store.DB_PATH) == before_all, "whole table (content, embedding, origin, layer, cold, temp) byte-identical to before mark")
r2 = retrieve_ids()
check({ids["d1"], ids["d2"], ids["d3"]} <= r2, "retrieve serves the notes again after unmark (reversible)")
check(DICT_IDS <= matrix_ids(), "associative matrix serves them again after unmark")
conn.close()

# ---- 5. the apply script on a COPY -----------------------------------------------------------------------------------------
spec = importlib.util.spec_from_file_location("apply3191", TREE / "scripts" / "apply_J-3191_mark_dict_repr_notes.py")
ap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ap)
assert ap.ROOT == TREE


def run(argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = ap.main(argv)
    return rc, buf.getvalue()


copy = _TMP / "copy.db"
src = sqlite3.connect(str(store.DB_PATH))
dst = sqlite3.connect(str(copy))
src.backup(dst)
src.close()
dst.close()
sha_c0 = sha_all(copy)

rc, out = run(["--db", str(copy), "--expect", "4"])
check(rc == 0 and "DRY RUN: would hide 4 row(s)" in out and sha_all(copy) == sha_c0, "dry run: reports 4, writes nothing")
check("selection (dict-repr)  : 4" in out and "selection sha256 before:" in out and all(i in out for i in DICT_IDS),
      "dry run prints the selection count, the sha256 and the fragment_ids")

rc, out = run(["--db", str(copy), "--expect", "7", "--write", "--allow-du-up"])
check(rc == 2 and "REFUSE: selection is 4 rows" in out and sha_all(copy) == sha_c0, "--expect mismatch refuses and writes nothing")

ap.du_is_up = lambda: ["1234: python run_nascence.py"]
rc, out = run(["--db", str(copy), "--expect", "4", "--write"])
check(rc == 2 and "REFUSE: Du appears to be running" in out and sha_all(copy) == sha_c0, "refuses --write while a run_nascence.py process is up")
ap.du_is_up = lambda: []

rc, out = run(["--db", str(copy), "--expect", "4", "--write"])
check(rc == 0 and "rows changed           : 4" in out and "EQUAL (content untouched)" in out
      and "unchanged" in out and "selection hidden after : 4" in out, "--write marks exactly 4, content sha256 equal, outside rows unchanged")
cc = sqlite3.connect(str(copy))
check(drn.temp_histogram(cc) == {"hidden/cold=1": 1, "hidden/cold=0": 3}, "copy: the 4 rows are hidden")
cc.close()
sha_c1 = sha_all(copy)
rc, out = run(["--db", str(copy), "--expect", "4", "--write"])
check(rc == 0 and "rows changed           : 0" in out and sha_all(copy) == sha_c1, "second --write is a no-op (idempotent)")

um_spec = importlib.util.spec_from_file_location("unmark3191", TREE / "scripts" / "unmark_dict_repr_notes.py")
check(um_spec is not None and (TREE / "scripts" / "unmark_dict_repr_notes.py").exists(), "scripts/unmark_dict_repr_notes.py exists")
rc, out = run(["--db", str(copy), "--unmark"])
check(rc == 0 and "DRY RUN: would restore 4 row(s)" in out and sha_all(copy) == sha_c1, "--unmark dry run writes nothing")
rc, out = run(["--db", str(copy), "--unmark", "--write"])
check(rc == 0 and "rows changed           : 4" in out and sha_all(copy) == sha_c0, "--unmark --write restores the copy byte-identically")

shutil.rmtree(_TMP, ignore_errors=True)
print()
print("FAILS: %d" % len(_fails) if _fails else "ALL PASS")
sys.exit(1 if _fails else 0)
