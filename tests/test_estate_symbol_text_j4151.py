"""J-4151 (D-0778): hermetic test, a tablet-derived estate symbol node carries its NEWEST tablet text
("<symbol> — now: <tablet, ~160 chars>"), markup stripped and cut at a word boundary; the placeholder
survives only when no usable tablet text exists, and the flag off restores the old text. Everything temp-pathed.
Run: python tests/test_estate_symbol_text_j4151.py"""
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

LONG = ("The fire no longer warns me of what burns; it has become the small warmth I keep lit while I wait "
        "for someone to answer, and the waiting itself has started to feel like a kind of company I chose.")
tmp = Path(tempfile.mkdtemp(prefix="j4151_"))
db = sqlite3.connect(str(tmp / "t.db")); db.row_factory = sqlite3.Row
db.execute("CREATE TABLE symbol_tablets (tablet_id TEXT PRIMARY KEY, symbol TEXT NOT NULL, tablet TEXT NOT NULL, "
           "drift REAL NOT NULL DEFAULT 0.0, embedding BLOB, created REAL NOT NULL)")
rows = [("t1", "fire", "old fire meaning", 100.0), ("t3", "fire", LONG, 300.0), ("t2", "fire", "mid", 200.0),
        ("s1", "stillness", "first stillness", 50.0),
        ("s2", "stillness", '{"tablet": "**Stillness** now\n holds the  room open."}', 60.0),
        ("k1", "knot", "   ", 10.0),
        ("q1", "bird", '"A bird I let go."', 5.0)]
for tid, sym, tab, c in rows:
    db.execute("INSERT INTO symbol_tablets (tablet_id, symbol, tablet, created) VALUES (?,?,?,?)", (tid, sym, tab, c))
db.commit()

class _Conn:
    def __enter__(self): return db
    def __exit__(self, *a): return False
store._connect = lambda *a, **k: _Conn()
sd = tmp / "data"; sd.mkdir()
ie._DATA, ie._ESTATE_F = sd, sd / "identity_estate.json"
assert str(ie._ESTATE_F).startswith(str(tmp))

def run():
    ie.seed()
    nodes = json.loads(ie._ESTATE_F.read_text(encoding="utf-8"))["nodes"]
    return nodes, {n["id"]: n for n in nodes if n.get("source") == "symbol_evolution"}

check("flag defaults on", ie.SYMBOL_NODE_NEWEST_TABLET is True)
nodes, by = run()
fire = by["symb_fire"]["text"]
check("fire text starts with newest tablet", fire.startswith("fire — now: The fire no longer warns"), fire[:60])
body = fire[len("fire — now: "):]
check("fire tablet cut to ~160 chars", len(body) <= ie._SYMBOL_TABLET_CHARS + 1, str(len(body)))
check("fire cut at a word boundary with ellipsis", body.endswith("…") and LONG.startswith(body[:-1])
      and LONG[len(body) - 1] == " ", repr(body[-12:]))
check("stillness markup stripped (json wrapper, **, newline, double space)",
      by["symb_stillness"]["text"] == "stillness — now: Stillness now holds the room open.", by["symb_stillness"]["text"])
check("wrapping quotes stripped", by["symb_bird"]["text"] == "bird — now: A bird I let go.", by["symb_bird"]["text"])
check("blank tablet keeps placeholder", by["symb_knot"]["text"] == "knot — its meaning has moved as I lived")
check("newest_tablet_id still t3", by["symb_fire"]["newest_tablet_id"] == "t3")
check("weight unchanged 0.6", all(n["weight"] == 0.6 for n in by.values()))
check("_duplicate_id_census == {}", ie._duplicate_id_census(nodes) == {})
check("no symbol_tablets rows touched", db.execute("SELECT COUNT(*) FROM symbol_tablets").fetchone()[0] == 7)
check("short tablet passes through", ie._clean_tablet("short and plain") == "short and plain")

ie.SYMBOL_NODE_NEWEST_TABLET = False
nodes, by = run()
check("flag off -> exact old text for every symbol",
      all(n["text"] == f"{n['text'].split(' — ')[0]} — its meaning has moved as I lived" for n in by.values())
      and by["symb_fire"]["text"] == "fire — its meaning has moved as I lived")
print("ALL PASS" if all(ok) else "FAILURES"); sys.exit(0 if all(ok) else 1)
