"""scripts/profile_sleep_sweeps.py (J-1917 / F-2546): where do the minutes go inside book_residue.sweep, stick_test.census and
world_consolidation.sweep? Read-mostly profiling on a lag-harness data copy (env LAGH_SCRATCH, LAGH_WT; prelude audit hook,
network block proven). Times by phase (monkeypatched wrappers), counts sqlite statements and sums time in conn.execute+fetch vs
Python. NOTE: runs the real sweeps against the COPY (they append to its jsonl and world_consolidation may UPDATE chapter_id there).
usage: python profile_sleep_sweeps.py OUT.json"""
import sys, os, time, json, pathlib, collections, sqlite3, asyncio
SP = pathlib.Path(os.environ["LAGH_SCRATCH"]); WT = SP / os.environ["LAGH_WT"]
sys.path.insert(0, str(WT / "scripts" / "lag_harness"))
import _prelude as P
import core
assert str(pathlib.Path(core.__file__).resolve()).lower().startswith(str(WT).lower())
from core import book_residue, stick_test, world_consolidation
from core.memory import store

async def _net():
    P._NET["block"] = True
    try:
        await asyncio.wait_for(asyncio.open_connection("127.0.0.1", 9), 5)
    except PermissionError:
        return True
    except Exception:
        return False
    return False
assert asyncio.run(_net()), "network block not proven"

out = {}
SQL = collections.Counter(); SQLT = collections.Counter()

class TimedConn:
    """Wrap the connection returned by store._connect: time every execute()+full iteration, bucket by statement shape."""
    def __init__(self, c): object.__setattr__(self, '_c', c)
    def __setattr__(self, k, v): setattr(self._c, k, v)
    def __enter__(self): self._c.__enter__(); return self
    def __exit__(self, *a): return self._c.__exit__(*a)
    def __getattr__(self, k): return getattr(self._c, k)
    def execute(self, sql, params=()):
        key = " ".join(sql.split())[:90]
        t0 = time.perf_counter()
        cur = self._c.execute(sql, params)
        rows = cur.fetchall()           # materialise so the scan time is inside the timer
        dt = time.perf_counter() - t0
        SQL[key] += 1; SQLT[key] += dt
        return _Rows(rows)

class _Rows(list):
    def fetchone(self): return self[0] if self else None
    def fetchall(self): return list(self)

_orig_connect = store._connect
store._connect = lambda: TimedConn(_orig_connect())

def phase(mod, name, bucket):
    f = getattr(mod, name)
    def w(*a, **k):
        t0 = time.perf_counter(); r = f(*a, **k); bucket[name] = bucket.get(name, 0) + time.perf_counter() - t0
        bucket[name + "#calls"] = bucket.get(name + "#calls", 0) + 1
        return r
    setattr(mod, name, w)

for label, runner, mods in (
        ("book_residue", lambda: book_residue.sweep(), [(book_residue, "_book_spans"), (book_residue, "_signatures")]),
        ("world_consolidation", lambda: world_consolidation.sweep(), [(world_consolidation, "file_book_notes")]),
        ("stick_test", lambda: stick_test.snapshot(), [(stick_test, "build_roster"), (stick_test, "_sound_context_index"),
                                                      (stick_test, "_book_context_index"), (stick_test, "_cat_triple_count")])):
    SQL.clear(); SQLT.clear(); b = {}
    for m, n in mods: phase(m, n, b)
    if label == "stick_test":
        # census() opens its own mode=ro connection, not store._connect: shim stick_test.sqlite3.connect to return a TimedConn
        class _Shim:
            Row = sqlite3.Row
            @staticmethod
            def connect(*a, **k): return TimedConn(sqlite3.connect(*a, **k))
        stick_test.sqlite3 = _Shim
    t0 = time.perf_counter(); r = runner(); tot = time.perf_counter() - t0
    out[label] = {"total_s": round(tot, 1), "phases_s": {k: (round(v, 2) if not k.endswith("#calls") else v) for k, v in b.items()},
                  "sql_total_s": round(sum(SQLT.values()), 1),
                  "sql_by_shape": [{"sql": k, "n": SQL[k], "sum_s": round(SQLT[k], 2)} for k in sorted(SQLT, key=lambda x: -SQLT[x])[:8]],
                  "ret": r if isinstance(r, dict) and len(json.dumps(r, default=str)) < 600 else "(large)"}
    print(label, json.dumps(out[label], default=str)[:1500], flush=True)
conn = sqlite3.connect(f"file:{store.DB_PATH}?mode=ro", uri=True)
out["db"] = {"fragments": conn.execute("SELECT COUNT(*) FROM memory_fragments").fetchone()[0],
             "indexes": [r[1:3] for r in conn.execute("SELECT * FROM sqlite_master WHERE type='index' AND tbl_name='memory_fragments'")],
             "reading_rows": conn.execute("SELECT COUNT(*) FROM memory_fragments WHERE origin='reading'").fetchone()[0],
             "self_origin_rows": conn.execute("SELECT COUNT(*) FROM memory_fragments WHERE origin IN ('inner_thought','subconscious_synthesis','dream','mirror')").fetchone()[0]}
conn.close()
json.dump(out, open(sys.argv[1], "w"), indent=1, default=str); print("wrote", sys.argv[1])
