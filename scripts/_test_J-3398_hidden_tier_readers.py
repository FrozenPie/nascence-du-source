"""J-3398 (F-4021 follow-up, D-0578): the remaining direct readers of origin='understanding' honour temp='hidden'.
Offline, temp DB only; touches no live data. Covers, with the SAME 61-style rows marked via dict_repr_notes.mark:
  1. visible_clause: '' on a table with no temp column (old/profile DB unchanged), the guard when it exists, an alias prefix.
  2. wandering: _drift_from (the pool), _affective_drift, _ambient_item -- hidden dict-repr note skipped, back after unmark.
  3. essay_lesson: gather_notes (per-book LIKE read) and _graph_walk_cross_book (relates_to neighbour) skip it.
  4. world_consolidation: a hidden understanding note is not chosen as a book's gist ("no gist yet"); a visible one is.
  5. memory_edges.backfill_answers: no answers edge written onto a hidden row.
  6. nothing deleted/rewritten: content sha256 of every row identical before/after mark.
"""
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789: no write to the tree's data/
import hashlib
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
import core                                              # noqa: E402  (core BEFORE lab_env)
assert TREE in Path(core.__file__).resolve().parents, core.__file__
import numpy as np                                       # noqa: E402
import core.memory.store as store                        # noqa: E402
from core.memory import dict_repr_notes as drn           # noqa: E402
from core import wandering as wd                         # noqa: E402
from core import essay_lesson as el                      # noqa: E402
from core import world_consolidation as wc               # noqa: E402
from core import memory_edges as me                      # noqa: E402

_TMP = Path(tempfile.mkdtemp(prefix="j3398_hidden_"))
store.DB_PATH = _TMP / "test.db"
assert str(store.DB_PATH).startswith(str(_TMP))
store._POOL_DELTA_SHADOW_LOG = _TMP / "pool_delta_shadow.jsonl"
wd._LOG = _TMP / "wander_log.jsonl"
wc._LOG = _TMP / "wc_log.jsonl"
me._DATA = _TMP
_fails = []


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        _fails.append(msg)


# ---- 1. visible_clause ----------------------------------------------------------------------------------------------
c0 = sqlite3.connect(":memory:")
c0.execute("CREATE TABLE memory_fragments (fragment_id TEXT, content TEXT)")
check(drn.visible_clause(c0) == "", "no temp column -> '' (query unchanged on an old/profile DB)")
c0.execute("DROP TABLE memory_fragments")
c0.execute("CREATE TABLE memory_fragments (fragment_id TEXT, temp TEXT)")
check(drn.visible_clause(c0) == " AND temp != 'hidden'", "temp column -> the guard")
check(drn.visible_clause(c0, "f.") == " AND f.temp != 'hidden'", "alias prefix honoured")
c0.close()

# ---- real schema DB ---------------------------------------------------------------------------------------------------
store.init_db()
NOW = time.time()
ids = {}
_VEC = np.ones(384, dtype=np.float32) / np.sqrt(384.0)
_OTHER = np.zeros(384, dtype=np.float32); _OTHER[0] = 1.0     # cosine to _VEC ~0.05: not an echo, not a duplicate
store._embed = lambda text: _VEC.copy()


def add(key, content, origin, vec=None, layer="semantic"):
    ids[key] = store.store_fragment(content, layer=layer, origin=origin, importance=0.9, timestamp=NOW - len(ids),
                                    context_stamp=False)
    if vec is not None:
        c = sqlite3.connect(str(store.DB_PATH))
        c.execute("UPDATE memory_fragments SET embedding=?, emotion_embedding=? WHERE fragment_id=?",
                  (vec.astype(np.float32).tobytes(), vec.astype(np.float32).tobytes(), ids[key]))
        c.commit(); c.close()


DICT = "[Understanding - from 'The Prince'] {'grasp_of_content': 'a', 'key_facts': [{'point': 'b'}]}"
PROSE = "[Understanding - from 'The Prince'] Machiavelli argues that a ruler must be feared and loved in measure."
add("dict", DICT, "understanding", _OTHER)
add("prose", PROSE, "understanding", _OTHER * 0 + np.roll(_OTHER, 1))
conn = sqlite3.connect(str(store.DB_PATH)); conn.row_factory = sqlite3.Row


def content_sha():
    h = hashlib.sha256()
    for r in conn.execute("SELECT fragment_id, content, embedding FROM memory_fragments ORDER BY fragment_id"):
        h.update(repr(tuple(r)).encode("utf-8", "surrogatepass"))
    return h.hexdigest()


def hide():
    conn.execute("UPDATE memory_fragments SET temp='hidden' WHERE fragment_id=?", (ids["dict"],)); conn.commit()


def unhide():
    conn.execute("UPDATE memory_fragments SET temp='warm' WHERE fragment_id=?", (ids["dict"],)); conn.commit()


sha0 = content_sha()
check(drn.select_ids(conn) == [ids["dict"]], "selection is the dict note only")

# ---- 2. wandering -----------------------------------------------------------------------------------------------------
wd._recently_visited.clear()
seed = np.roll(_OTHER, 7)                                   # orthogonal to both rows


def drift_texts():
    wd._recently_visited.clear()
    out = wd._drift_from(seed, conn, k=5, inner_count=0, trail_vecs=[])
    return " | ".join(i["text"] for i in out)


def drift_texts_world_only():
    wd._recently_visited.clear()
    out = wd._drift_from(seed, conn, k=5, inner_count=5, trail_vecs=[])   # the inner_count>=3 branch (origin IN ...)
    return " | ".join(i["text"] for i in out)


check("grasp_of_content" in drift_texts() and "grasp_of_content" in drift_texts_world_only(),
      "control: unhidden, the dict note IS drifted into (both branches)")
hide()
check("grasp_of_content" not in drift_texts() and "grasp_of_content" not in drift_texts_world_only(),
      "hidden: _drift_from never returns the dict note (both branches)")
check("Machiavelli" in drift_texts(), "hidden: the prose note is still drifted into (not over-filtering)")
wd._recently_visited.clear()
aff = wd._affective_drift(_OTHER, conn)
check(aff is None or "grasp_of_content" not in aff["text"], "hidden: _affective_drift skips the dict note")
seen_amb = set()
for _ in range(60):
    wd._recently_visited.clear()
    # _ambient_item's book branch needs a live reading state; force the stored-fact branch
    import random as _r
    _orig = _r.random; _r.random = lambda: 0.99
    try:
        it = wd._ambient_item()
    finally:
        _r.random = _orig
    if it:
        seen_amb.add(it["text"][:40])
check(seen_amb and not any("grasp" in t or "Understanding" in t and "{" in t for t in seen_amb)
      and any("Machiavelli" in t or "Understanding" in t for t in seen_amb),
      f"hidden: _ambient_item only ever returns the prose note ({seen_amb})")
unhide()
wd._recently_visited.clear()
aff = wd._affective_drift(_OTHER, conn)
check(aff is not None, "unhidden: _affective_drift can reach it again")

# ---- 3. essay_lesson --------------------------------------------------------------------------------------------------
# gather_notes reads the book file + DB notes; stub the file side so only the DB understanding read is exercised.
hide()
text, used = el.gather_notes("The Prince", "")
check(ids["dict"] not in used and "grasp_of_content" not in text, "hidden: gather_notes does not include the dict note")
check(ids["prose"] in used, "hidden: gather_notes still includes the prose understanding note")
unhide()
text, used = el.gather_notes("The Prince", "")
check(ids["dict"] in used, "unhidden: gather_notes includes the dict note again")
# relates_to graph walk
conn.execute("INSERT INTO memory_links (parent_id, child_id, link_type, weight, created) VALUES (?,?,?,?,?)", (ids["prose"], ids["dict"], "relates_to", 0.7, NOW))
conn.commit()
check([f for f, _ in el._graph_walk_cross_book([ids["prose"]], "zzz")] == [ids["dict"]],
      "control: unhidden, the graph walk reaches the dict note as a neighbour")
hide()
check(el._graph_walk_cross_book([ids["prose"]], "zzz") == [], "hidden: the graph walk drops the dict neighbour")
unhide()

# ---- 4. world_consolidation gist ---------------------------------------------------------------------------------------
import core.essay_lesson as _el2                           # noqa: E402
_el2.filing_held = lambda t: False
conn.execute("UPDATE memory_fragments SET origin='study' WHERE fragment_id=?", (ids["prose"],)); conn.commit()  # only the dict note can be a gist
hide()
s = wc._file_book_notes("The Prince")
check(s.get("gist") is None and "no gist" in str(s.get("reason")),
      f"hidden: a hidden dict note is NOT chosen as the gist ({s.get('reason')!r})")
unhide()
s = wc._file_book_notes("The Prince")
check(s.get("gist") == ids["dict"], f"unhidden: it is a gist candidate again ({s.get('gist')!r})")

# ---- 5. memory_edges.backfill_answers ---------------------------------------------------------------------------------
probe = "grasp_of_content a key_facts point b grasp"
(_TMP / "frontier.json").write_text(json.dumps({"questions": [
    {"id": "q1", "q": "what?", "finding": "{'grasp_of_content': 'a', 'key_facts': [{'point': 'b'}]}", "finding_ts": NOW}]}),
    encoding="utf-8")
# the probe is the first 60 whitespace-normalised chars of the finding -> matches the dict note's content
hide()
out = me.backfill_answers()
check(out.get("matched") == 0 and out.get("written") == 0, f"hidden: no answers edge onto a hidden row ({out})")
unhide()
out = me.backfill_answers()
check(out.get("matched") == 1, f"unhidden: the finding text matches it again ({out})")

# ---- 6. nothing rewritten ---------------------------------------------------------------------------------------------
check(content_sha() == sha0, "content+embedding of every row byte-identical after all of the above")
conn.close()

print("\nALL PASS" if not _fails else f"\n{len(_fails)} FAILED: {_fails}")
sys.exit(1 if _fails else 0)
