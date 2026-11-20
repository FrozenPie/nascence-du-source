"""J-4008 (F-4687): hermetic test, estate seed() emits ONE symbol node per symbol id with additive
tablet_count/newest_tablet_id/first_ts/last_ts; text and weight unchanged. Everything temp-pathed.
Run: python tests/test_estate_symbol_nodes_j4008.py"""
import json, sqlite3, sys, tempfile
from pathlib import Path
WT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WT))
import core                                                            # BEFORE lab_env
assert str(Path(core.__file__).resolve()).startswith(str(WT)), core.__file__
from core import identity_estate as ie
import core.memory.store as store

ok = []
def check(name, cond, extra=""):
    ok.append(bool(cond)); print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra else ""))

tmp = Path(tempfile.mkdtemp(prefix="j4008_"))
db = sqlite3.connect(str(tmp / "t.db")); db.row_factory = sqlite3.Row
db.execute("CREATE TABLE symbol_tablets (tablet_id TEXT PRIMARY KEY, symbol TEXT NOT NULL, tablet TEXT NOT NULL, "
           "drift REAL NOT NULL DEFAULT 0.0, embedding BLOB, created REAL NOT NULL)")
rows = [("t1", "fire", 100.0), ("t3", "fire", 300.0), ("t2", "fire", 200.0),   # newest NOT last inserted
        ("s1", "stillness", 50.0), ("s2", "stillness", 60.0),
        ("p1", "abcdefghijklmnopqrstuvwxy", 10.0), ("p2", "abcdefghijklmnopqrstZZZZZ", 20.0)]
for tid, sym, c in rows:
    db.execute("INSERT INTO symbol_tablets (tablet_id, symbol, tablet, created) VALUES (?,?,?,?)", (tid, sym, "x", c))
db.commit()

class _Conn:
    def __enter__(self): return db
    def __exit__(self, *a): return False
store._connect = lambda *a, **k: _Conn()
sd = tmp / "data"; sd.mkdir()
ie._DATA, ie._ESTATE_F = sd, sd / "identity_estate.json"
assert str(ie._ESTATE_F).startswith(str(tmp))
ie.SYMBOL_NODE_NEWEST_TABLET = False   # J-4151: this test pins the flag-off (pre-D-0778 placeholder) text path

ie.seed()
est = json.loads(ie._ESTATE_F.read_text(encoding="utf-8"))
nodes = est["nodes"]
sym = [n for n in nodes if n.get("source") == "symbol_evolution"]
ids = [n["id"] for n in sym]
by = {n["id"]: n for n in sym}
check("unique symbol ids", len(ids) == len(set(ids)) == 3, str(ids))
check("fire tablet_count 3", by["symb_fire"]["tablet_count"] == 3)
check("fire newest_tablet_id t3", by["symb_fire"]["newest_tablet_id"] == "t3")
check("fire span", (by["symb_fire"]["first_ts"], by["symb_fire"]["last_ts"]) == (100.0, 300.0))
check("stillness count 2, newest s2", by["symb_stillness"]["tablet_count"] == 2 and by["symb_stillness"]["newest_tablet_id"] == "s2")
check("text unchanged", by["symb_fire"]["text"] == "fire — its meaning has moved as I lived")
check("weight unchanged", by["symb_fire"]["weight"] == 0.6)
pref = "symb_abcdefghijklmnopqrst"
check("prefix collision merged to one node, count 2", pref in by and by[pref]["tablet_count"] == 2)
check("collision text is first row's (as before)", by[pref]["text"].startswith("abcdefghijklmnopqrstuvwxy"))
check("_duplicate_id_census == {}", ie._duplicate_id_census(nodes) == {})
check("no symbol_tablets rows deleted", db.execute("SELECT COUNT(*) FROM symbol_tablets").fetchone()[0] == 7)
print("ALL PASS" if all(ok) else "FAILURES"); sys.exit(0 if all(ok) else 1)
