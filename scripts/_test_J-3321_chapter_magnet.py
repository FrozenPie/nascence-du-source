"""J-3321: smoke test for the read-only chapter-magnet analysis scripts (docs/lab/J-3321_data/).

Builds a SYNTHETIC temp DB + recall log, points the scripts at them through J3321_DB / J3321_RECALL / J3321_OUT, runs
chapter_magnet_J-3321.py end to end and asserts the report's shape and arithmetic invariants. Touches no live data: the live
nascence.db and recall.jsonl are only stat()ed (to prove they were not modified). Run from the worktree:
    python scripts/_test_J-3321_chapter_magnet.py
"""
import json, os, sqlite3, subprocess, sys, tempfile, py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
assert ROOT.name != "scripts"
sys.path.insert(0, str(ROOT))
import core  # noqa: F401  (core BEFORE lab_env, per the job rules; the analysis scripts themselves never import core)
try:
    import lab_env  # noqa: F401
except Exception:
    pass
import numpy as np

LAB = ROOT / "docs" / "lab" / "J-3321_data"
SCRIPTS = ["chapter_magnet_J-3321.py", "chapter_magnet_timetravel_J-3321.py", "chapter_magnet_trail_J-3321.py", "chapter_served_counts_J-3321.py"]
for s in SCRIPTS:
    py_compile.compile(str(LAB / s), doraise=True)
print("compile ok:", len(SCRIPTS), "scripts")

LIVE_DB, LIVE_REC = Path("C:/Nascence/data/memory/nascence.db"), Path("C:/Nascence/data/training/recall.jsonl")
before = [(p.stat().st_mtime, p.stat().st_size) for p in (LIVE_DB, LIVE_REC) if p.exists()]

tmp = Path(tempfile.mkdtemp(prefix="j3321_test_"))
rng = np.random.default_rng(1)
def unit(v): return (v / np.linalg.norm(v)).astype(np.float32)
db = tmp / "t.db"
c = sqlite3.connect(db)
c.execute("""CREATE TABLE memory_fragments (fragment_id TEXT PRIMARY KEY, content TEXT, layer TEXT, relevance REAL, timestamp REAL, keywords TEXT,
             embedding BLOB, origin TEXT, importance REAL, chapter_id TEXT, chapter_level INTEGER, cold INTEGER DEFAULT 0, temp TEXT DEFAULT 'warm')""")
base = [unit(rng.normal(size=384)) for _ in range(8)]
ids = ["d4479cda-0000-0000-0000-000000000001"] + [f"c{i:07d}-0000-0000-0000-000000000000" for i in range(1, 8)]
for i, fid in enumerate(ids):
    body = ("I kept circling the same quiet theme and this is a long enough chapter body number %d. " % i) * 3
    c.execute("INSERT INTO memory_fragments VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (fid, f"[A chapter of my life \u2014 'Title {i} of the period' (June 01 to June 09)] {body}", "archive", .85, 1786229463.0 + i, "", base[i].tobytes(), "chapter", .85, None, 1, 0, "warm"))
    for m in range(12):   # members
        c.execute("INSERT INTO memory_fragments VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                  (f"m{i}-{m}", "member", "episodic", .5, 1786000000.0 + m, "", unit(base[i] + .3 * rng.normal(size=384)).tobytes(), "inner_thought", .3, fid, 0, 1, "warm"))
for k in range(40):
    c.execute("INSERT INTO memory_fragments VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (f"si{k}", "insight", "archive", .8, 1787000000.0 + k, "", unit(rng.normal(size=384)).tobytes(), "standing_insight", .9, None, 0, 0, "warm"))
for k in range(80):
    c.execute("INSERT INTO memory_fragments VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (f"ep{k}", "episodic", "episodic", .3, 1787000000.0 + k, "", unit(rng.normal(size=384)).tobytes(), "lived", .3, None, 0, 0, "warm"))
c.commit(); c.close()
rec = tmp / "recall.jsonl"
with open(rec, "w", encoding="utf-8") as f:
    for k in range(70):
        f.write(json.dumps({"ts": 1793000000.0 + k * 100 if k % 2 else 1790000000.0 + k * 100, "cycle_id": f"cy{k}", "node": "recall",
                            "input_type": "internal" if k % 3 else "human", "raw_input": f"Test query number {k} about quiet themes and values and the period of my life {k * 7}",
                            "user_prompt": "[archive] [A chapter of my life \u2014 'Title 0 of the period' (June 01 to June 09)] x" if k % 5 == 0 else "none"}) + "\n")
out = tmp / "out"; out.mkdir()
env = dict(os.environ, J3321_DB="file:" + str(db).replace("\\", "/") + "?mode=ro&immutable=1", J3321_RECALL=str(rec), J3321_OUT=str(out), PYTHONIOENCODING="utf-8")
r = subprocess.run([sys.executable, str(LAB / "chapter_magnet_J-3321.py")], env=env, capture_output=True, text=True, encoding="utf-8")
assert r.returncode == 0, r.stderr[-1500:]
R = json.load(open(out / "J-3321_report.json", encoding="utf-8"))
assert R["chapters_live_pool"] == 8 and R["chapters_total"] == 8, R["chapters_live_pool"]
assert R["archive_tier_pool_rows"] == 48, R["archive_tier_pool_rows"]          # 8 chapters + 40 standing_insight
assert R["pool_rows"] == 8 + 40 + 80
for k in ("hub_cos_to_other_chapters", "q200_live", "big_live", "q200_hub_removed", "big_hub_removed", "archive_top2_big", "member_test", "variants"):
    assert k in R, k
bl = R["big_live"]
assert bl["n"] == R["distinct_queries_big"] and 0.0 <= bl["hub_share"] <= 1.0
assert sum(v["n"] for v in bl["by_input_type"].values()) == bl["n"]
assert R["big_hub_removed"]["queries_hub_won"] == bl["hub_wins"]
v1 = R["variants"]["V1 full content (prefix+title+span+body)"]; assert -1.0 <= v1["hub_cos_to_own_stored_embedding"] <= 1.0 and 0.0 <= v1["big_hub_share"] <= 1.0   # (synthetic stored vectors are random, so V1 != stored here; on the live DB the cosine is 1.0)
assert "V8 prefix + body (no title, no span)" in R["variants"] and not any(k.startswith("V8 prefix only") for k in R["variants"])
assert R["member_test"]["members_sampled"] == 8 * 12
# nothing written outside the temp dir; live inputs untouched
after = [(p.stat().st_mtime, p.stat().st_size) for p in (LIVE_DB, LIVE_REC) if p.exists()]
assert before == after, "a live input changed"
print("J-3321 test OK: hub share on synthetic big set = %.3f, effective winners = %.2f" % (bl["hub_share"], bl["effective_n_winners"]))
