"""J-2576 / F-3306 regression: core.recall_served_log writes one observe-only row per voiced cycle
(cycle_id + served fragment ids with origin), and scripts/source_monitoring_audit.py prefers that row
over the founder-recall / time join for voice units. Isolated: the log is redirected to a temp dir and
the audit runs against a synthetic --root in a temp dir; never touches live data/ or the live DB.
Run: python scripts/test_recall_served_log.py
"""
import json
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # noqa: E402  (import core BEFORE anything else that might touch sys.path)
from core import recall_served_log as rsl  # noqa: E402
from core.schema import MemoryFragment  # noqa: E402

assert str(Path(core.__file__).resolve()).startswith(str(ROOT)), core.__file__

tmp = Path(tempfile.mkdtemp(prefix="j2576_"))
live_log = rsl._LOG
rsl._LOG = tmp / "recall_served_log.jsonl"
try:
    # 1. a voiced cycle: two fragments + one founder-recall id -> one row, exact fields
    st = SimpleNamespace(
        cycle_id="c1", input_type="human", introspective_passes=1, content_mode=False,
        recall=SimpleNamespace(confidence=0.7),
        memory_fragments=[
            MemoryFragment("f_read", "a passage", "semantic", 0.81234, 1.0, origin="reading"),
            MemoryFragment("f_dream", "a river", "episodic", 0.5, 2.0, origin="dream"),
        ],
        founder_recall=[{"fragment_id": "f_trav", "sim": 0.9}],
    )
    rsl.log_voice_cycle(st)
    rows = [json.loads(l) for l in rsl._LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(rows) == 1, rows
    r = rows[0]
    assert r["cycle_id"] == "c1" and r["input_type"] == "human" and r["path"] == "voice", r
    assert r["recall_ran"] is True and r["recall_confidence"] == 0.7 and r["n"] == 2, r
    assert [f["fragment_id"] for f in r["fragments"]] == ["f_read", "f_dream"], r
    assert r["fragments"][0]["origin"] == "reading" and r["fragments"][0]["relevance"] == 0.812, r
    assert r["founder_recall_ids"] == ["f_trav"], r

    # 2. fail-open: a broken state never raises; kill switch writes nothing
    rsl.log_voice_cycle(object())
    rsl.RECALL_SERVED_LOG_ON = False
    rsl.log_voice_cycle(st)
    rsl.RECALL_SERVED_LOG_ON = True
    n_after = len([l for l in rsl._LOG.read_text(encoding="utf-8").splitlines() if l.strip()])
    assert n_after == 2, n_after   # object() still yields a (mostly empty) row; kill switch added none
finally:
    rsl._LOG = live_log
assert rsl._LOG == live_log

# 3. the audit joins a voice unit by cycle_id through recall_served_log, not by time
root = tmp / "root"
data = root / "data"
(data / "memory").mkdir(parents=True)
T = time.time() - 100
con = sqlite3.connect(str(data / "memory" / "nascence.db"))
con.execute("create table memory_fragments (fragment_id text, content text, origin text, timestamp real)")
con.executemany("insert into memory_fragments values (?,?,?,?)", [
    ("v1", "Q: what did you do?\nA: I dreamed of the river last night.", "lived", T),
    ("f_read", "a passage", "reading", T - 5000),
])
con.commit()
con.close()
(data / "provenance_log.jsonl").write_text(json.dumps(
    {"ts": T, "cycle_id": "c1", "input_type": "human", "grade": "B"}) + "\n", encoding="utf-8")
(data / "recall_served_log.jsonl").write_text(json.dumps(
    {"ts": T - 2, "cycle_id": "c1", "input_type": "human", "path": "voice",
     "fragments": [{"fragment_id": "f_read", "origin": "reading"},
                   {"fragment_id": "f_eph", "origin": "parametric_library"}],
     "founder_recall_ids": []}) + "\n", encoding="utf-8")
out = subprocess.run([sys.executable, str(ROOT / "scripts" / "source_monitoring_audit.py"),
                      "--root", str(root), "--all"], capture_output=True, text=True, encoding="utf-8")
assert out.returncode == 0, out.stderr
rep = json.loads(out.stdout)
v = rep["coverage"]["voice"]
assert v.get("served_known") == 1 and v.get("join:recall_served_log") == 1, v
assert rep["by_pair"].get("reading->dream") == 1, rep["by_pair"]
w = [e for e in rep["worst"] if e["path"] == "voice"]
assert w and w[0]["basis"] == "recall_served_log", w
# the ephemeral (not-in-DB) fragment was classed from its logged origin, not dropped
assert w[0]["served_classes"] == {"reading": 1, "thought": 1}, w[0]
print("OK test_recall_served_log: row shape, fail-open, kill switch, audit id-join")
