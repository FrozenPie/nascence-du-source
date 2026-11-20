"""J-2795 / F-3431 / P-0099: core/evidence_recall.py _candidates() de-duplicates by content before judging.
Offline: a temp DB, stubbed embeddings, stubbed judge panel, stubbed accounting writers. Never opens
data/memory/nascence.db; writes nothing under the repo's data/.

Covers:
  1. identical-content rows (also differing only in whitespace, and differing only AFTER char 300) collapse to
     ONE candidate, and the highest-similarity copy is the one kept.
  2. rows that differ before char 300 stay distinct (the key is not too loose).
  3. the short-list still FILLS with distinct text: k=4 over 3 copies of the top passage + 6 other passages returns
     4 distinct rows (duplicates are skipped before they count toward k).
  4. the echo guard is unchanged (a row containing the question's own text is still dropped) and empty-content
     rows are never collapsed into one another.
  5. gather(): the judge panel is asked once per DISTINCT passage (K_JUDGED slots all go to different text), and a
     duplicated passage cannot come back as two episodes; the evidence_log row's judged ids are all distinct.
"""
import asyncio
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
from core import evidence_recall as er                   # noqa: E402

_TMP = Path(tempfile.mkdtemp(prefix="j2795_evidence_dedupe_"))
DB = _TMP / "test.db"
er._DB = DB
er._LOG = _TMP / "evidence_log.jsonl"
assert str(er._DB).startswith(str(_TMP)) and str(er._LOG).startswith(str(_TMP))

DIM = 16
_fails = []


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        _fails.append(msg)


def vec_at(cos):
    """A unit vector whose cosine with the question vector (e0) is `cos`."""
    v = np.zeros(DIM, dtype=np.float32)
    v[0] = cos
    v[1] = float(np.sqrt(max(0.0, 1.0 - cos * cos)))
    return v


QV = np.zeros(DIM, dtype=np.float32)
QV[0] = 1.0
store._embed = lambda text: QV.copy()                    # the question (and any Q: asked-text) embeds on e0

QUESTION = "Is peace a victory in itself, or only a pause between wars?"

conn = sqlite3.connect(str(DB))
conn.execute("CREATE TABLE memory_fragments (fragment_id TEXT PRIMARY KEY, content TEXT, origin TEXT, "
             "timestamp REAL, embedding BLOB, temp TEXT DEFAULT 'warm')")
_n = [0]


def add(fid, content, cos, origin="reading"):
    conn.execute("INSERT INTO memory_fragments (fragment_id, content, origin, timestamp, embedding) VALUES (?,?,?,?,?)",
                 (fid, content, origin, time.time() - 86400 * (_n[0] + 1), vec_at(cos).tobytes()))
    _n[0] += 1


def reset():
    conn.execute("DELETE FROM memory_fragments")
    conn.commit()
    _n[0] = 0


def ids(k, q=QUESTION):
    return [r["fragment_id"] for r in er._candidates(q, k=k)]


PASSAGE = "Tolstoy writes that the peace after Austerlitz was a silence in which both armies counted their dead. " * 2
assert len(PASSAGE) > 150

# ---- 1. identical / whitespace-only / tail-only duplicates collapse; best-similarity copy kept -------------------------
reset()
add("a_low", PASSAGE, 0.60)
add("a_best", PASSAGE, 0.90)                                        # same text, higher sim -> must be the survivor
add("a_ws", "  " + PASSAGE.replace(" ", "  ").replace("\n", " ") + "\n", 0.80)   # whitespace-only difference
LONG = ("Caesar describes the Gallic settlement in the same words every winter, " * 6)[:320]
add("t_one", LONG + " TAIL ONE", 0.70)
add("t_two", LONG + " TAIL TWO", 0.65)                              # differs only after char 300 -> same passage
conn.commit()
got = ids(12)
check(got.count("a_best") == 1 and "a_low" not in got and "a_ws" not in got,
      f"three copies of one passage collapse to the highest-sim copy (got {got})")
check(("t_one" in got) != ("t_two" in got) and "t_one" in got,
      f"rows differing only after char {er._DEDUPE_CHARS} collapse, higher-sim kept (got {got})")
check(len(got) == 2, f"exactly two distinct passages in the short-list (got {len(got)})")

# ---- 2. rows that differ before char 300 stay distinct ------------------------------------------------------------------
reset()
add("d1", "Passage one: the treaty ended the fighting but not the grievance. " + "x " * 30, 0.90)
add("d2", "Passage two: the treaty ended the fighting but not the grievance. " + "x " * 30, 0.85)
add("d3", "Passage three: the treaty ended the fighting but not the grievance. " + "x " * 30, 0.80)
conn.commit()
check(sorted(ids(12)) == ["d1", "d2", "d3"], "near-identical rows that differ before the cut-off stay distinct")

# ---- 3. the short-list still fills with distinct text ------------------------------------------------------------------
reset()
for j in range(3):
    add(f"top_copy{j}", PASSAGE, 0.95 - j * 0.01)                   # three copies of the best passage
for j in range(6):
    add(f"other{j}", f"A different witness number {j} on the cost of peace and what it bought. " * 3, 0.80 - j * 0.02)
conn.commit()
got = ids(4)
check(len(got) == 4 and len(set(got)) == 4, f"k=4 returns 4 rows (got {got})")
check(sum(1 for g in got if g.startswith("top_copy")) == 1 and got[0] == "top_copy0",
      "exactly one copy of the duplicated best passage, ranked first")
check(got[1:] == ["other0", "other1", "other2"],
      "duplicates were skipped BEFORE counting toward k, so the other slots hold the next-best distinct passages")
got12 = ids(er.K_CANDIDATES)
check(len(got12) == 7 and len(set(got12)) == 7, f"K_CANDIDATES walk yields 1 + 6 distinct passages (got {len(got12)})")

# ---- 4. echo guard unchanged; empty bodies never collapsed -------------------------------------------------------------
reset()
add("echo", f"someone asked: {QUESTION} and then went quiet", 0.99)
add("keep", PASSAGE, 0.80)
add("e1", "", 0.70)
add("e2", "", 0.69)
add("e3", "   ", 0.68)
conn.commit()
got = ids(12)
check("echo" not in got and "keep" in got, "the literal-echo guard still drops the question echoing back")
check({"e1", "e2", "e3"} <= set(got), f"empty / blank bodies are not collapsed into one another (got {got})")

# ---- 5. gather(): one judge call per distinct passage; no duplicate episode ----------------------------------------------
reset()
for j in range(4):
    add(f"dup{j}", PASSAGE, 0.95 - j * 0.01)
for j in range(8):
    add(f"w{j}", f"Witness {j}: a lived account of how the quiet after the guns felt like winning and like losing. " * 3,
        0.85 - j * 0.02)
conn.commit()

from core import judge_panel                             # noqa: E402
from core import memory_edges, memory_service            # noqa: E402

asked = []


async def fake_rule_detail(system, user, key, context="", **kw):
    asked.append(user)
    return {"verdict": True, "v1": True, "v2": True, "how": "agree"}


judge_panel.rule_detail = fake_rule_detail
memory_edges.log_co_recall = lambda *a, **k: None
memory_service.stash_usage = lambda *a, **k: None
memory_service._fetch_context = lambda ids_: {}

res = asyncio.run(er.gather(QUESTION, train_id="t-test", source="route2"))
bodies = [u.split("EPISODE", 1)[1] for u in asked]
check(len(asked) == er.K_JUDGED, f"the panel was asked {er.K_JUDGED} times (all slots used) (got {len(asked)})")
check(len(set(bodies)) == len(bodies), "every judged slot carried DIFFERENT text (no passage judged twice)")
eps = res["episodes"]
check(res["outcome"] == "found" and len(eps) == er.K_RETURN, f"outcome found, K_RETURN episodes (got {res['outcome']}, {len(eps)})")
check(len({e["content"][:300] for e in eps}) == len(eps), "no two returned episodes share content (Follow Line is not handed one ground twice)")
rows = [json.loads(line) for line in er._LOG.read_text(encoding="utf-8").splitlines() if line.strip()]
check(len(rows) == 1 and len({j["fragment_id"] for j in rows[0]["judged"]}) == len(rows[0]["judged"]) == er.K_JUDGED,
      "evidence_log row: judged fragment ids are all distinct")
check(sum(1 for j in rows[0]["judged"] if j["fragment_id"].startswith("dup")) == 1,
      "the four stored copies of the duplicated passage occupy exactly ONE judged slot")
check(rows[0]["n_candidates"] == 9, f"n_candidates counts distinct short-listed rows (1 dup passage + 8 witnesses = 9) (got {rows[0]['n_candidates']})")

conn.close()
print()
print("ALL PASS" if not _fails else f"{len(_fails)} FAILED")
sys.exit(1 if _fails else 0)
