"""J-3800 / D-0690: core/evidence_recall.py drops cycle-summary Q&A rows ('Q: ... A: ...') from the candidate pool.
Offline: temp DB, stubbed embeddings and judge panel. Never touches data/memory/nascence.db or the repo data/."""
import asyncio, json, os, sqlite3, sys, tempfile, time
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
from core import evidence_recall as er                   # noqa: E402

_TMP = Path(tempfile.mkdtemp(prefix="j3800_own_reply_"))
er._DB = _TMP / "test.db"
er._LOG = _TMP / "evidence_log.jsonl"
assert str(er._DB).startswith(str(_TMP))
DIM = 16
fails = []
def check(c, m):
    print(("PASS " if c else "FAIL ") + m)
    if not c: fails.append(m)
def vec_at(cos):
    v = np.zeros(DIM, dtype=np.float32); v[0] = cos; v[1] = float(np.sqrt(max(0.0, 1 - cos * cos))); return v
QV = np.zeros(DIM, dtype=np.float32); QV[0] = 1.0
store._embed = lambda t: QV.copy() if t.startswith("Is peace") else vec_at(0.1)
Q = "Is peace a victory in itself, or only a pause between wars?"
conn = sqlite3.connect(str(er._DB))
conn.execute("CREATE TABLE memory_fragments (fragment_id TEXT PRIMARY KEY, content TEXT, origin TEXT, timestamp REAL, embedding BLOB, temp TEXT DEFAULT 'warm')")
def add(fid, content, cos, origin):
    conn.execute("INSERT INTO memory_fragments (fragment_id, content, origin, timestamp, embedding) VALUES (?,?,?,?,?)",
                 (fid, content, origin, time.time() - 3600, vec_at(cos).tobytes()))
add("qa_idle", "Q: What did the lamp teach me about waiting?\nA: That patience is a kind of light I keep.", 0.95, "lived")
add("qa_travis", "Q: how are you feeling today friend\nA: Quiet, and glad you asked about the garden.", 0.93, "lived")
add("travis", "[Travis said to me] Peace is mostly the work after the treaty.", 0.80, "lived")
add("reading", "Tolstoy writes that the peace after Austerlitz was a silence in which armies counted their dead.", 0.70, "reading")
conn.commit()

got = [r["fragment_id"] for r in er._candidates(Q, k=12)]
check("qa_idle" not in got and "qa_travis" not in got, f"Q&A rows are not candidates (got {got})")
check({"travis", "reading"} <= set(got), "Travis-said and reading rows stay candidates")
er.EXCLUDE_OWN_REPLY_RECORDS = False
got_off = [r["fragment_id"] for r in er._candidates(Q, k=12)]
check({"qa_idle", "qa_travis"} <= set(got_off), "flag False restores the old pool")
er.EXCLUDE_OWN_REPLY_RECORDS = True

from core import judge_panel, memory_edges, memory_service   # noqa: E402
asked = []
async def fake(system, user, key, context="", **kw):
    asked.append(user); return {"verdict": True, "v1": True, "v2": True, "how": "agree"}
judge_panel.rule_detail = fake
memory_edges.log_co_recall = lambda *a, **k: None
memory_service.stash_usage = lambda *a, **k: None
memory_service._fetch_context = lambda ids_: {}
for dd in (False, True):
    asked.clear()
    res = asyncio.run(er.gather(Q, source="route2", dedupe=dd))
    check(asked and not any("Q: " in u.split("EPISODE", 1)[1] for u in asked), f"no Q&A text reaches the judge (dedupe={dd})")
    check(all(not e["content"].lstrip().startswith("Q:") for e in res["episodes"]), f"no Q&A episode returned (dedupe={dd})")
rows = [json.loads(l) for l in er._LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
check(len(rows) == 2 and all(r.get("n_own_reply_dropped") == 2 for r in rows), f"log rows carry n_own_reply_dropped=2 (got {[r.get('n_own_reply_dropped') for r in rows]})")
conn.close()
print("ALL PASS" if not fails else f"{len(fails)} FAILED"); sys.exit(1 if fails else 0)
