"""Test -- J-3865 default-off read-side light_events dedupe. Hermetic: temp sqlite DB, no live data.
Run: python scripts/test_light_read_dedupe_J3865.py   (exit 0 = all passed)"""
import sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401  (before lab_env)
from core.memory import store  # noqa: E402
assert str(Path(store.__file__).resolve()).startswith(str(ROOT)), store.__file__

class R(dict):
    pass
def row(i, ts, txt, emb=b"x"):
    return R(event_id=i, timestamp=ts, integrated_content=txt, raw_input="r", embedding=emb, source="s")

rows = [row("c2", 5, "Same  thing"), row("u", 4, "unique"), row("c1", 3, "same thing"),
        row("orig", 1, "SAME THING"), row("e", 0.5, "")]
rows[-1]["raw_input"] = ""
FAILS = []
def check(n, got, want):
    if got != want: FAILS.append(n)
    print(("PASS " if got == want else "FAIL ") + n, got)

out = store._collapse_light_duplicates(rows)
check("keeps earliest, order preserved", [r["event_id"] for r in out], ["u", "orig", "e"])
check("empty content kept", any(r["event_id"] == "e" for r in out), True)
check("flag default off", store.LIGHT_READ_DEDUPE, False)

# DB-level: patch _connect to an in-memory db
import sqlite3, contextlib
conn = sqlite3.connect(":memory:"); conn.row_factory = sqlite3.Row
conn.execute("CREATE TABLE light_events (event_id TEXT PRIMARY KEY, timestamp REAL, cycle_id TEXT, raw_input TEXT, integrated_content TEXT, emotion_primary TEXT, embedding BLOB, source TEXT)")
for r in rows:
    conn.execute("INSERT INTO light_events VALUES (?,?,?,?,?,?,?,?)", (r["event_id"], r["timestamp"], "c", r["raw_input"], r["integrated_content"], None, b"x", "s"))
@contextlib.contextmanager
def fake(): yield conn
store._connect = fake
ids = lambda xs: [x["event_id"] for x in xs]
check("off == all rows", ids(store.get_light_events()), ["c2", "u", "c1", "orig", "e"])
check("param on", ids(store.get_light_events(dedupe=True)), ["u", "orig", "e"])
check("emb off", [x[0] for x in store.get_light_events_with_embeddings()], ["c2", "u", "c1", "orig"])
check("emb on", [x[0] for x in store.get_light_events_with_embeddings(dedupe=True)], ["u", "orig"])
store.LIGHT_READ_DEDUPE = True
check("flag on", ids(store.get_light_events()), ["u", "orig", "e"])
sys.exit(1 if FAILS else 0)
