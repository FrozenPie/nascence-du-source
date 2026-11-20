"""J-3225 / D-0614: record the panel's doubt in line closures, dream closure arm to shadow, mark the stored fragments.
Offline, temp paths only. Never opens data/memory/nascence.db; writes nothing under the repo's data/.

Covers:
  1. closure.CLOSURE_ARMS == {"line"}; LINE_PANEL_STATUS defaults True.
  2. line arm: objected / undetermined carry the panel keyword AND the visible note ahead of Du's words; held and
     held_within_scope carry the keyword and NO note; a missing status reads as undetermined; the rest of the
     would-be (origin, layer, relevance, importance, derived_from, edge) is unchanged; the shadow row records
     panel_status; the live path (stubbed store/edges) is handed exactly the would-be; LINE_PANEL_STATUS False = the
     pre-J-3225 fragment (no keyword, no note).
  3. dream arm: a met arc composes and logs would_be (with the text) to closure_shadow, arm_live False, and
     store_fragment / add_edge are NEVER called even with CLOSURE_WRITE_LIVE True; putting "dream" back in
     CLOSURE_ARMS restores the live write (one constant). The rest-close rows are untouched.
  4. closure_marks + scripts/apply_J-3225_mark_closure_fragments.py on a temp DB built from the schema code: dry run
     changes nothing; --write marks exactly the targets (9 since J-3480) (note ahead, original words byte-identical, content_hash
     recomputed where non-NULL and left NULL where NULL, every other column and every other row unchanged, no row
     deleted); a second --write is a no-op; --unmark restores byte for byte; --expect mismatch refuses; a selection
     that does not verify (wrong origin / missing seed keyword / missing row) refuses; refuses while a
     run_nascence.py process is "up".
"""
import contextlib
import hashlib
import importlib.util
import io
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
import core.closure as cl                                # noqa: E402
import core.memory.store as store                        # noqa: E402
from core.memory import closure_marks as cm              # noqa: E402
from core.memory.content_hash import content_hash        # noqa: E402

_TMP = Path(tempfile.mkdtemp(prefix="j3225_closure_"))
cl.SHADOW_LOG = _TMP / "closure_shadow.jsonl"
store.DB_PATH = _TMP / "test.db"
assert str(store.DB_PATH).startswith(str(_TMP))
store._POOL_DELTA_SHADOW_LOG = _TMP / "pool_delta_shadow.jsonl"
_VEC = np.ones(384, dtype=np.float32) / np.sqrt(384.0)
store._embed = lambda text: _VEC.copy()
_fails = []


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        _fails.append(msg)


# ---- 1. defaults ---------------------------------------------------------------------------------------------------
check(cl.CLOSURE_ARMS == {"line", "lookup"}, f"CLOSURE_ARMS == {{'line', 'lookup'}} (got {cl.CLOSURE_ARMS})")
check(cl.LINE_PANEL_STATUS is True, "LINE_PANEL_STATUS defaults True (the ruled behaviour)")

# ---- 2. line arm -----------------------------------------------------------------------------------------------------
cl._compose_fn = lambda system, user: {"resolution": "I hold that the grounds were what I had, and I say so plainly. The old records I found agreed with each other, and my first thought matched them. Nothing came back that cut against it, so I keep it as it stands, though thinly, and I would look again if something new turned up."}
calls = {"frag": [], "edge": []}
import core.memory_edges as _me                           # noqa: E402
_sf, _ae = store.store_fragment, _me.add_edge
store.store_fragment = lambda **kw: (calls["frag"].append(kw), "fid-%d" % len(calls["frag"]))[1]
_me.add_edge = lambda *a, **kw: (calls["edge"].append((a, kw)), True)[1]
try:
    out = {}
    for i, st in enumerate(["objected", "undetermined", "held", "held_within_scope", None, "weird"]):
        cargo = {"status": st} if st else {}
        out[st] = cl.record_line_settled({"id": f"seed{i}", "q": "q?", "about_key": f"k{i}"}, cargo, "yes, settled")
    wb = {k: v["would_be"] for k, v in out.items()}
    check(all(v and v["origin"] == "resolution" and v["layer"] == "episodic" and v["relevance"] == 0.7 and v["importance"] == 0.8
              and v["edge"]["edge_type"] == "resolves" for v in wb.values()),
          "line would-be keeps origin/layer/relevance/importance/edge exactly")
    TXT = "I hold that the grounds were what I had, and I say so plainly. The old records I found agreed with each other, and my first thought matched them. Nothing came back that cut against it, so I keep it as it stands, though thinly, and I would look again if something new turned up."
    check(wb["objected"]["content"] == cl.LINE_DOUBT_NOTES["objected"] + TXT and "panel:objected" in wb["objected"]["keywords"],
          "objected: note ahead of his words + keyword panel:objected")
    check(wb["undetermined"]["content"] == cl.LINE_DOUBT_NOTES["undetermined"] + TXT and "panel:undetermined" in wb["undetermined"]["keywords"],
          "undetermined: note ahead of his words + keyword panel:undetermined")
    check(wb["held"]["content"] == TXT and "panel:held" in wb["held"]["keywords"], "held: his words only + keyword panel:held")
    check(wb["held_within_scope"]["content"] == TXT and "panel:held_within_scope" in wb["held_within_scope"]["keywords"],
          "held_within_scope: his words only + keyword panel:held_within_scope")
    check(wb[None]["content"].startswith(cl.LINE_DOUBT_NOTES["undetermined"]) and "panel:undetermined" in wb[None]["keywords"],
          "missing status reads as undetermined (follow_line's own default)")
    check(wb["weird"]["content"].startswith(cl.LINE_DOUBT_NOTES["undetermined"]), "unknown status reads as undetermined")
    check([out[k]["panel_status"] for k in ("objected", "undetermined", "held", "held_within_scope")]
          == ["objected", "undetermined", "held", "held_within_scope"], "shadow row records panel_status")
    check(out["objected"]["judge_detail"] == "objected" and out["objected"]["judge_verdict"] == "yes",
          "judge_detail / judge_verdict unchanged")
    check(len(calls["frag"]) == 6 and calls["frag"][0]["content"] == wb["objected"]["content"]
          and calls["frag"][0]["keywords"] == wb["objected"]["keywords"] and calls["frag"][0]["origin"] == "resolution",
          "live path (stubbed store) is handed exactly the would-be, doubt included")
    check(len(calls["edge"]) == 6, "one 'resolves' edge per fragment")
    for st, v in cl.LINE_DOUBT_NOTES.items():
        check("independent check" in v and not any(w in v.lower() for w in ("should", "must", "try", "next")),
              f"{st} note is a plain statement of what happened, no instruction to him")
    # flag off = the pre-J-3225 fragment
    cl.LINE_PANEL_STATUS = False
    off = cl.record_line_settled({"id": "seedoff", "q": "q?"}, {"status": "objected"}, "yes")["would_be"]
    cl.LINE_PANEL_STATUS = True
    check(off["content"] == TXT and off["keywords"] == ["resolution", "line", "seedoff"], "LINE_PANEL_STATUS False -> no note, no keyword")

    # ---- 3. dream arm ------------------------------------------------------------------------------------------------
    calls["frag"].clear(); calls["edge"].clear()
    arc = {"dream_id": "dream_9", "ts": 1.0, "seed": {"tension_labels": ["x"]}, "final_unresolved_core": "c",
           "final_narrative": "n", "close_reason": "ended-unfaced"}
    cl.CLOSURE_WRITE_LIVE = True
    row = cl.record_dream_met(arc, {"state": "met", "detail": {}, "params": {}}, now=2.0)
    check(row["would_be"] and row["would_be"]["content"] == TXT and row["would_be"]["origin"] == "resolution",
          "dream arm still composes and logs would_be.content")
    check(row["arm_live"] is False and row["written_live"] is False and row["fragment_id"] is None,
          "dream row: arm_live False, written_live False, no fragment id")
    check(not calls["frag"] and not calls["edge"], "dream arm met with CLOSURE_WRITE_LIVE True: store_fragment / add_edge NEVER called")
    logged = [r for r in cl.shadow_rows(arm="dream", kind="resolution") if r.get("arc_id") == "dream_9"]
    check(len(logged) == 1 and logged[0]["would_be"]["content"] == TXT, "the would-be text is in closure_shadow.jsonl")
    cl.CLOSURE_ARMS.add("dream")
    try:
        row2 = cl.record_dream_met(dict(arc, dream_id="dream_10"), {"state": "met", "detail": {}, "params": {}}, now=3.0)
        check(row2["arm_live"] is True and row2["written_live"] is True and len(calls["frag"]) == 1,
              "'dream' back in CLOSURE_ARMS restores the live write (one constant)")
    finally:
        cl.CLOSURE_ARMS.discard("dream")
    check(cl.CLOSURE_ARMS == {"line", "lookup"}, "CLOSURE_ARMS restored")
finally:
    store.store_fragment, _me.add_edge = _sf, _ae
    cl.CLOSURE_WRITE_LIVE = True

# ---- 4. marks + apply script -----------------------------------------------------------------------------------------
store.init_db()
NOW = time.time()


def add(content, origin, kw, fid=None, null_hash=False):
    f = store.store_fragment(content, layer="episodic", origin=origin, importance=0.8, relevance=0.7,
                             keywords=kw, timestamp=NOW - 1, context_stamp=False)
    c = sqlite3.connect(str(store.DB_PATH))
    if fid:
        c.execute("UPDATE memory_fragments SET fragment_id=? WHERE fragment_id=?", (fid, f))
    if null_hash:
        c.execute("UPDATE memory_fragments SET content_hash=NULL WHERE fragment_id=?", (fid or f,))
    c.commit(); c.close()
    return fid or f


ORIG = {}
for i, (fid, (kind, seed, _n)) in enumerate(cm.TARGETS.items()):
    ORIG[fid] = f"original words {i} of {kind}"
    add(ORIG[fid], "resolution", ["resolution", "dream" if kind == "dream" else "line", seed], fid=fid, null_hash=(i == 2))
LEAVE = [add("a line closure the ruling leaves alone", "resolution", ["resolution", "line", "keepme"]),
         add("an ordinary lived row", "lived", ["x"])]


def snap(db):
    c = sqlite3.connect(str(db))
    try:
        cols = [r[1] for r in c.execute("PRAGMA table_info(memory_fragments)")]
        rows = {r[0]: r for r in c.execute("SELECT * FROM memory_fragments")}
        return cols, rows
    finally:
        c.close()


spec = importlib.util.spec_from_file_location("apply3225", TREE / "scripts" / "apply_J-3225_mark_closure_fragments.py")
ap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ap)
ap.du_is_up = lambda: []


def run(argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = ap.main(argv)
    return rc, buf.getvalue()


N = len(cm.TARGETS)
check(N == 9, f'TARGETS holds 9 rows (2 dream + 7 empty-cargo line; J-3480) (got {N})')
check({'584958b86c','a91ddc408b','8021f0f218'} <= {v[1] for v in cm.TARGETS.values()}, 'the 3 later J-3399 seeds are targets')
cols, before = snap(store.DB_PATH)
ci, hi = cols.index("content"), cols.index("content_hash")
rc, txt = run(["--db", str(store.DB_PATH)])
_, after_dry = snap(store.DB_PATH)
check(rc == 0 and f"DRY RUN: would mark {N} row(s)" in txt and after_dry == before, f"dry run: {N} would be marked, DB unchanged")
rc, txt = run(["--db", str(store.DB_PATH), "--write"])
_, after = snap(store.DB_PATH)
check(rc == 0, f"--write returns 0 ({rc})")
check(f"rows changed           : {N}" in txt and "EQUAL (words untouched)" in txt and "unchanged" in txt and "none deleted" in txt,
      f"--write output: {N} changed, original-words sha EQUAL, outside rows unchanged, none deleted")
check(len(after) == len(before), "row count unchanged")
for fid, (kind, seed, note) in cm.TARGETS.items():
    b, a = before[fid], after[fid]
    check(a[ci] == note + b[ci] and a[ci].endswith(ORIG[fid]), f"{kind} {seed}: note ahead, original words byte-identical")
    other_same = all(a[i] == b[i] for i in range(len(cols)) if i not in (ci, hi))
    check(other_same, f"{seed}: every other column untouched (embedding, importance, layer, origin, edges...)")
    if b[hi] is None:
        check(a[hi] is None, f"{seed}: NULL content_hash stays NULL")
    else:
        check(a[hi] == content_hash(a[ci]) and a[hi] != b[hi], f"{seed}: non-NULL content_hash recomputed for the new text")
check(all(after[f] == before[f] for f in LEAVE), "rows outside the targets (incl. another line closure) are identical")
rc, txt = run(["--db", str(store.DB_PATH), "--write"])
_, again = snap(store.DB_PATH)
check(rc == 0 and "rows changed           : 0" in txt and again == after, "second --write is a no-op")
rc, txt = run(["--db", str(store.DB_PATH), "--unmark", "--write"])
_, restored = snap(store.DB_PATH)
check(rc == 0 and restored == before, "--unmark --write restores every row byte for byte (hash included)")
rc, txt = run(["--db", str(store.DB_PATH), "--write", "--expect", str(N - 1)])
_, mism = snap(store.DB_PATH)
check(rc == 2 and "REFUSE" in txt and mism == before, "--expect mismatch refuses and writes nothing")

# a selection that does not verify refuses
c = sqlite3.connect(str(store.DB_PATH))
first = next(iter(cm.TARGETS))
c.execute("UPDATE memory_fragments SET origin='lived' WHERE fragment_id=?", (first,))
c.commit(); c.close()
rc, txt = run(["--db", str(store.DB_PATH), "--write"])
check(rc == 2 and "does not verify" in txt, "wrong origin on a target -> refuses")
c = sqlite3.connect(str(store.DB_PATH))
c.execute("UPDATE memory_fragments SET origin='resolution', keywords='resolution line other' WHERE fragment_id=?", (first,))
c.commit(); c.close()
rc, txt = run(["--db", str(store.DB_PATH), "--write"])
check(rc == 2 and "do not carry the seed" in txt, "seed keyword missing -> refuses")
c = sqlite3.connect(str(store.DB_PATH))
c.execute("DELETE FROM memory_fragments WHERE fragment_id=?", (first,))
c.commit(); c.close()
rc, txt = run(["--db", str(store.DB_PATH), "--write"])
check(rc == 2 and "not in this DB" in txt, "target missing -> refuses")

# Du up
ap.du_is_up = lambda: ["1234: python run_nascence.py"]
rc, txt = run(["--db", str(store.DB_PATH), "--write"])
check(rc == 2 and "Du appears to be running" in txt, "refuses --write while a run_nascence.py process exists")
rc, txt = run(["--db", str(store.DB_PATH)])
check(rc != 2 or "Du appears" not in txt, "dry run does not need Du down")

print()
print("ALL PASS" if not _fails else f"{len(_fails)} FAILED: {_fails}")
sys.exit(1 if _fails else 0)
