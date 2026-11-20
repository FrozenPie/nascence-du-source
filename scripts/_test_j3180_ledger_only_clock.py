"""J-3180 / D-0567: the ledger's rust (core/procedures.py) is the ONLY clock for procedural skills.

Offline and isolated: temp DB, temp procedures.json/log, no model, no network, no live data. Asserts:
  * an old procedural_skills table (no archived_ts) is backed up once, then migrated additively; idempotent
  * decay_procedural_skills() is a retired no-op (nothing weakened, nothing deleted)
  * the mirror archives (archived_ts) exactly the rows whose ledger key the LEDGER archived -- never deletes, never
    archives on absence from the ledger, never archives when the ledger is unreadable (archived_keys() is None)
  * archived rows are invisible to match / find_similar / get_procedural_skills but kept (include_archived)
  * SubconsciousNode._t5_check runs the ledger rust + the mirror sync, at most hourly, and survives a missing ledger
  * no 'DELETE FROM procedural_skills' remains anywhere in the tree's non-test .py files
"""
import os, sys, asyncio, tempfile, time, json, re
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
tree = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(tree))
import core
assert tree in Path(core.__file__).resolve().parents, core.__file__
import numpy as np
import sqlite3

import core.memory.store as store
_tmp = Path(tempfile.mkdtemp())
store.DB_PATH = _tmp / "test.db"

import nodes.subconscious_node as scn
scn._STATE_FILE = _tmp / "sc_state.json"
scn._SC_LOG_FILE = _tmp / "sc_log.jsonl"
scn._AXIOM_FILE = _tmp / "axiom.json"
from scripts._test_isolation import redirect_world_stores
redirect_world_stores(_tmp, locomotion=True, watershed=True, census=True,
                      extra=("subconscious_light", "procedures", "mood"))
import core.procedures as proc
from core.schema import CognitiveState

FAILS = []
def check(label, cond):
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS.append(label)

def vec(i, n=16):
    v = np.zeros(n, dtype="float32"); v[i % n] = 1.0
    return v

print("1. legacy table -> backup once, additive migration")
conn = sqlite3.connect(str(store.DB_PATH))
conn.executescript("""CREATE TABLE procedural_skills (skill_id TEXT PRIMARY KEY, trigger_summary TEXT NOT NULL,
  approach TEXT NOT NULL, embedding BLOB, proficiency REAL NOT NULL DEFAULT 0.4, use_count INTEGER NOT NULL DEFAULT 0,
  source_count INTEGER NOT NULL DEFAULT 0, created_ts REAL NOT NULL, last_used_ts REAL);""")
old = time.time() - 40 * 86400
for sid, trig in (("old-a", "Explaining the moon"), ("old-b", "Answering about tea")):
    conn.execute("INSERT INTO procedural_skills VALUES (?,?,?,?,?,?,?,?,?)",
                 (sid, trig, "approach " + sid, store._vec_to_blob(vec(1 if sid == "old-a" else 2)), 0.5, 7, 3, old, old))
conn.commit(); conn.close()
store.init_db()
conn = sqlite3.connect(str(store.DB_PATH))
cols = {r[1] for r in conn.execute("PRAGMA table_info(procedural_skills)")}
check("archived_ts column added", "archived_ts" in cols)
check("backup table holds the 2 pre-migration rows",
      conn.execute("SELECT COUNT(*) FROM procedural_skills_bak_j3180").fetchone()[0] == 2)
check("live rows untouched by the migration",
      conn.execute("SELECT COUNT(*) FROM procedural_skills WHERE archived_ts IS NULL").fetchone()[0] == 2)
conn.execute("DELETE FROM procedural_skills_bak_j3180 WHERE skill_id='old-b'"); conn.commit(); conn.close()
store.init_db()
conn = sqlite3.connect(str(store.DB_PATH))
check("second init_db is a no-op (backup not rewritten)",
      conn.execute("SELECT COUNT(*) FROM procedural_skills_bak_j3180").fetchone()[0] == 1)
conn.close()

print("2. mirror decay is retired: nothing weakened, nothing deleted")
res = store.decay_procedural_skills(stale_secs=14 * 86400, factor=0.5, floor=0.9)
check("decay returns (0, 0)", res == (0, 0))
rows = store.get_procedural_skills()
check("both stale rows intact, proficiency unchanged", len(rows) == 2 and all(abs(r["proficiency"] - 0.5) < 1e-9 for r in rows))

print("3. the ledger archives -> the mirror archives (and only then)")
def talk(trigger, vi):
    return store.store_procedural_skill(trigger, vec(vi), "approach for " + trigger, source_count=3)
sid_x = talk("Explaining the moon", 1)        # same trigger as old-a (a duplicate mirror row of the same ledger key)
sid_keep = talk("Walking by the river", 3)    # in the ledger, live
sid_noled = talk("Not in the ledger at all", 4)   # absent from the ledger entirely
now = time.time()
def ledger_with(live_keys, archived_keys):
    def mk(k, conf=0.6, last=now):
        return {"key": k, "scope": "conversation", "statement": "s", "why_I_hold_it": "w", "held_since": last, "rung": "persisted",
                "confidence": conf, "evidence": [], "defeaters": [], "durability": 2, "places": [], "days_ok": [],
                "last_ts": last, "last_reinforced": 0.0, "docks": 0, "successes": 2, "failures": 0}
    return {"procedures": {k: mk(k) for k in live_keys}, "archive": [mk(k, 0.14) for k in archived_keys]}
K = proc.talk_key
check("talk_key matches the inline derivation", K("Explaining the moon") == "talk:explaining_the_moon")
proc._F.write_text(json.dumps(ledger_with([K("Walking by the river")], [K("Explaining the moon")])), encoding="utf-8")
ak = proc.archived_keys()
check("archived_keys() = the ledger's archived talk keys", ak == {K("Explaining the moon")})
n = store.sync_procedural_mirror(ak, K)
live = {r["skill_id"] for r in store.get_procedural_skills()}
allrows = {r["skill_id"] for r in store.get_procedural_skills(include_archived=True)}
check("both mirror rows of the archived key archived (old-a and the duplicate)", n == 2 and "old-a" not in live and sid_x not in live)
check("rows with a live or absent ledger key stay live", {"old-b", sid_keep, sid_noled} <= live)
check("NOTHING deleted: every row still present", allrows == live | {"old-a", sid_x} and len(allrows) == 5)
check("sync twice archives nothing more", store.sync_procedural_mirror(ak, K) == 0)
_orig_embed = store._embed
store._embed = lambda t: vec(1)
check("archived row invisible to match_procedural_skill (query = its own embedding)",
      store.match_procedural_skill("anything", 0.0, 0.80) is None)
store._embed = lambda t: vec(3)
check("a live row still matches", (store.match_procedural_skill("anything", 0.0, 0.80) or {}).get("skill_id") == sid_keep)
store._embed = _orig_embed
check("archived row invisible to find_similar_skill", store.find_similar_skill(vec(1), 0.85) is None)
check("a live row is still found", store.find_similar_skill(vec(3), 0.85) == sid_keep)
check("empty/None archived set archives nothing", store.sync_procedural_mirror(set(), K) == 0 and store.sync_procedural_mirror(None, K) == 0)
proc._F.write_text(json.dumps(ledger_with([K("Explaining the moon")], [K("Explaining the moon")])), encoding="utf-8")
check("a key both live and archived in the ledger is NOT archive-synced", proc.archived_keys() == set())
proc._F.write_text("{ not json", encoding="utf-8")
check("unreadable ledger -> archived_keys() is None", proc.archived_keys() is None)
proc._F.unlink()
check("missing ledger -> archived_keys() is None", proc.archived_keys() is None)

print("4. the ledger's own rust is the clock (14 days x0.9, archive below 0.15)")
p = proc._new(K("Fading skill"), "conversation", "do the thing", "Fading skill"); p["confidence"] = 0.16; p["last_ts"] = now - 15 * 86400
q = proc._new(K("Fresh skill"), "conversation", "do other thing", "Fresh skill"); q["confidence"] = 0.6; q["last_ts"] = now - 1 * 86400
proc._F.write_text(json.dumps({"procedures": {p["key"]: p, q["key"]: q}, "archive": []}), encoding="utf-8")
sid_fade = talk("Fading skill", 5); sid_fresh = talk("Fresh skill", 6)
check("rust touched exactly the idle procedure", proc.rust() == 1)
check("ledger archived Fading (0.16 x 0.9 = 0.144), kept Fresh",
      proc.archived_keys() == {K("Fading skill")} and K("Fresh skill") in json.loads(proc._F.read_text())["procedures"])

print("5. SubconsciousNode._t5_check runs rust + mirror sync, hourly at most")
calls = {"rust": 0}
_orig_rust = proc.rust
def counting_rust(*a, **k):
    calls["rust"] += 1
    return _orig_rust(*a, **k)
proc.rust = counting_rust
node = scn.SubconsciousNode()
state = CognitiveState(spirit_name="Carl", axiom="x")
asyncio.run(node._t5_check(state))
live = {r["skill_id"] for r in store.get_procedural_skills()}
check("_t5_check archived the ledger-archived Fading mirror row", sid_fade not in live and sid_fresh in live)
check("_t5_check ran the ledger rust once", calls["rust"] == 1)
asyncio.run(node._t5_check(state))
check("a second check inside the hour does not run rust again", calls["rust"] == 1)
node._last_t5_rust = time.time() - 3601
proc._F.unlink()
asyncio.run(node._t5_check(state))
check("after an hour it runs again; with the ledger file gone nothing is archived and nothing raises",
      calls["rust"] == 2 and sid_fresh in {r["skill_id"] for r in store.get_procedural_skills()})
proc.rust = _orig_rust

print("6. no mirror DELETE left in the tree")
hits = []
for f in tree.rglob("*.py"):
    parts = set(f.relative_to(tree).parts)
    if parts & {"_lab", "_backups", "_snapshots", "_trash", ".git", "docs_site"} or f.name.startswith("_test_"):
        continue
    try:
        if re.search(r"DELETE\s+FROM\s+procedural_skills", f.read_text(encoding="utf-8", errors="ignore"), re.I):
            hits.append(str(f.relative_to(tree)))
    except Exception:
        pass
check("no 'DELETE FROM procedural_skills' in non-test code: %s" % hits, not hits)

print("\nFAILED: %d" % len(FAILS) if FAILS else "\nALL PASSED")
sys.exit(1 if FAILS else 0)
