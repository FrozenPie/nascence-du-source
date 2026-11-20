"""J-3478 / D-0630 + D-0434: the weekly self-mirror is retired (flag) and its stored fragments are demoted offline.
Hermetic: _STATE / _PAUSED_LOG point into a temp dir, every model call and store write is a stub that fails loudly, and
the demote script runs only against temp SQLite DBs. Never opens data/memory/nascence.db.

  1. SELF_MIRROR_RETIRED is True by default; hold_up_mirror makes no model call, no store write, no paused-log row and
     does not advance the clock (so flipping the flag back would find the mirror due again).
  2. The idle schedule (nodes/inner_monologue_node.py) only runs the stage when the flag is False.
  3. scripts/apply_J-3478_demote_mirror_fragments.py on a temp DB: dry run writes nothing; --expect mismatch refuses;
     Du-up refuses; --write lowers only origin='mirror' importances (content and every other row byte-identical,
     originals saved to the sidecar), idempotent, never overwrites the saved originals, --restore is exact.
"""
import asyncio
import hashlib
import importlib.util
import io
import contextlib
import json
import sqlite3
import sys
import tempfile
from pathlib import Path

TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TREE))
sys.stdout.reconfigure(encoding="utf-8")
import core  # noqa: E402  (core BEFORE anything lab-ish)
assert TREE in Path(core.__file__).resolve().parents, core.__file__
from core import self_mirror as sm  # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="j3478_"))
fails = []


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        fails.append(msg)


# ---- 1. retired flag ------------------------------------------------------------------------------------------------
sm._STATE = TMP / "state.json"
sm._PAUSED_LOG = TMP / "paused.jsonl"
facts_called = []
sm.mirror_facts = lambda: facts_called.append(1) or ["acting about 34 percent"]


async def _boom(*a, **k):
    raise AssertionError("model called while retired")

check(sm.SELF_MIRROR_RETIRED is True, "SELF_MIRROR_RETIRED defaults True")
check(sm.SELF_MIRROR_PAUSED is True, "SELF_MIRROR_PAUSED still True beneath it")
check(sm.due(), "state file absent => due")
out = asyncio.run(sm.hold_up_mirror(_boom, ["http://x"]))
check(out is None, "retired: returns None")
check(not facts_called, "retired: facts not even computed")
check(not sm._PAUSED_LOG.exists(), "retired: no paused-log row")
check(not sm._STATE.exists() and sm.due(), "retired: clock not advanced")
sm.SELF_MIRROR_RETIRED = False
asyncio.run(sm.hold_up_mirror(_boom, ["http://x"]))   # PAUSED branch: no model call (would raise), logs, marks
check(sm._PAUSED_LOG.exists() and not sm.due(), "flag False falls through to the paused branch (J-3242 behaviour)")
sm.SELF_MIRROR_RETIRED = True

# ---- 2. idle schedule guard -----------------------------------------------------------------------------------------
node = (TREE / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
guard = 'if not getattr(_mir, "SELF_MIRROR_RETIRED", False):'
i = node.find(guard)
j = node.find("await _mir.hold_up_mirror(")
check(i > 0 and j > i and node.find('_hb and _hb.submark("self_mirror")', i) > i and node.find('submark("self_mirror")') > i,
      "inner_monologue_node: submark and hold_up_mirror both sit inside the SELF_MIRROR_RETIRED guard")

# ---- 3. demote script -----------------------------------------------------------------------------------------------
spec = importlib.util.spec_from_file_location("apply_j3478", TREE / "scripts" / "apply_J-3478_demote_mirror_fragments.py")
ap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ap)
ap.du_is_up = lambda: []


def mkdb(path):
    c = sqlite3.connect(str(path))
    c.execute("CREATE TABLE memory_fragments (fragment_id TEXT PRIMARY KEY, content TEXT, origin TEXT, importance REAL, "
              "embedding BLOB, temp TEXT, cold INTEGER, layer TEXT)")
    for k in range(17):
        c.execute("INSERT INTO memory_fragments VALUES (?,?,?,?,?,?,?,?)",
                  (f"m{k}", f"(the mirror) paragraph {k}", "mirror", [0.9039, 0.15, 0.03][k % 3], b"\x01\x02", "warm", 0, "episodic"))
    for k in range(30):
        c.execute("INSERT INTO memory_fragments VALUES (?,?,?,?,?,?,?,?)",
                  (f"o{k}", f"other {k}", "inner_thought" if k % 2 else "lived", 0.5 + k / 100, b"\x03", "warm", 0, "episodic"))
    c.execute("INSERT INTO memory_fragments VALUES ('n0','null-origin',NULL,0.7,NULL,'warm',0,'episodic')")
    c.commit()
    c.close()


def snap(path):
    c = sqlite3.connect(str(path))
    try:
        return c.execute("SELECT * FROM memory_fragments ORDER BY fragment_id").fetchall()
    finally:
        c.close()


def run(*args):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = ap.main(list(args))
    return rc, buf.getvalue()


db = TMP / "t.db"
bk = TMP / "before.json"
mkdb(db)
orig = snap(db)
rc, txt = run("--db", str(db), "--backup", str(bk))
check(rc == 0 and "DRY RUN" in txt and snap(db) == orig and not bk.exists(), "dry run writes nothing (db and backup)")
rc, txt = run("--db", str(db), "--backup", str(bk), "--write", "--expect", "16")
check(rc == 2 and "REFUSE" in txt and snap(db) == orig, "--expect mismatch refuses, nothing written")
ap.du_is_up = lambda: ["123: python run_nascence.py"]
rc, txt = run("--db", str(db), "--backup", str(bk), "--write")
check(rc == 2 and "REFUSE: Du appears" in txt and snap(db) == orig, "refuses while Du is up")
def _nops():
    raise RuntimeError("no ps")
ap.du_is_up = _nops
rc, txt = run("--db", str(db), "--backup", str(bk), "--write")
check(rc == 2 and "cannot tell" in txt and snap(db) == orig, "fails closed when the process list is unreadable")
ap.du_is_up = lambda: []
rc, txt = run("--db", str(db), "--backup", str(bk), "--write")
after = snap(db)
check(rc == 0 and "EQUAL (content untouched)" in txt and "unchanged" in txt, "--write succeeds, hashes report clean")
mir = [r for r in after if r[2] == "mirror"]
check(len(mir) == 17 and all(r[3] <= 0.05 for r in mir), "all 17 mirror rows at or below 0.05")
check(any(abs(r[3] - 0.03) < 1e-12 for r in mir), "a row already below the floor is not raised")
oth0 = [r for r in orig if r[2] != "mirror"]
oth1 = [r for r in after if r[2] != "mirror"]
check(oth0 == oth1, "every non-mirror row (incl. NULL origin) byte-identical")
check([r[:3] + r[4:] for r in orig if r[2] == "mirror"] == [r[:3] + r[4:] for r in mir],
      "mirror rows: content, embedding, temp, cold, layer untouched (only importance moved)")
saved = json.loads(bk.read_text(encoding="utf-8"))["importance"]
check(len(saved) == 12 and abs(saved["m0"] - 0.9039) < 1e-9, "sidecar holds originals of the 12 rows that were above the floor")
rc, txt = run("--db", str(db), "--backup", str(bk), "--write")
check(rc == 0 and "rows changed           : 0" in txt and snap(db) == after, "second --write is a no-op")
check(json.loads(bk.read_text(encoding="utf-8"))["importance"] == saved, "second run did not overwrite the saved originals")
rc, txt = run("--db", str(db), "--backup", str(bk), "--restore")
check(rc == 0 and "DRY RUN" in txt and snap(db) == after, "--restore dry run writes nothing")
rc, txt = run("--db", str(db), "--backup", str(bk), "--restore", "--write")
check(rc == 0 and snap(db) == orig, "--restore --write puts the database back exactly")

print("FAIL: " + "; ".join(fails) if fails else "ALL PASS")
sys.exit(1 if fails else 0)
