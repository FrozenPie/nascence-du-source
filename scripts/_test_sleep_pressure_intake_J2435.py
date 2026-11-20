"""J-2435 / F-3139: sleep_pressure._new_intake must return IDENTICAL values to the old query while
range-scanning idx_timestamp. Read-only immutable connection to the live nascence.db; no writes, no DDL."""
import sys, time, sqlite3
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core import sleep_pressure as sp  # import core BEFORE any lab_env
assert str(Path(sp.__file__).resolve()).startswith(str(ROOT)), sp.__file__
import core.memory.store as store
try:
    import psutil
    _p = psutil.Process()
except Exception:
    _p = None

URI = "file:C:/Nascence/data/memory/nascence.db?mode=ro&immutable=1"


def conn():
    c = sqlite3.connect(URI, uri=True)
    c.row_factory = sqlite3.Row
    return c


OLD_N = "SELECT COUNT(*) n FROM memory_fragments WHERE origin IN ('reading','study') AND timestamp > ?"
OLD_E = "SELECT COALESCE(SUM(importance),0) w FROM memory_fragments WHERE layer='episodic' AND timestamp > ?"
NEW_N = OLD_N.replace("WHERE origin", "WHERE +origin")
NEW_E = OLD_E.replace("WHERE layer", "WHERE +layer")


def rb():
    return _p.io_counters().read_bytes if _p else 0


def run(c, qn, qe, ts):
    b0, t0 = rb(), time.perf_counter()
    n = c.execute(qn, (ts,)).fetchone()["n"]
    e = c.execute(qe, (ts,)).fetchone()["w"]
    return int(n or 0), float(e or 0.0), time.perf_counter() - t0, rb() - b0


def plan(c, q):
    return " | ".join(r[3] for r in c.execute("EXPLAIN QUERY PLAN " + q, (0,)))


c = conn()
for q in (NEW_N, NEW_E):
    pl = plan(c, q)
    print("NEW PLAN:", pl)
    assert "idx_timestamp" in pl, pl
for q in (OLD_N, OLD_E):
    print("OLD PLAN:", plan(c, q))

# the real function, with _connect redirected to the read-only connection
orig = store._connect
store._connect = conn
try:
    now = time.time()
    tot_ob = tot_nb = 0
    tot_ot = tot_nt = 0.0
    for w in (3600, 26000, 86400):
        ts = now - w
        on, oe, ot_, ob = run(c, OLD_N, OLD_E, ts)
        nn, ne, nt_, nb = run(c, NEW_N, NEW_E, ts)
        fn = sp._new_intake(ts)
        assert on == nn and abs(oe - ne) < 1e-9, (w, on, nn, oe, ne)
        assert fn[0] == on and abs(fn[1] - oe) < 1e-9, (w, fn, on, oe)
        print(f"window {w:6d}s: notes={on} epi={oe:.3f} | old {ot_*1000:.0f} ms {ob/1e6:.1f} MB | "
              f"new {nt_*1000:.1f} ms {nb/1e6:.1f} MB")
        tot_ot += ot_; tot_nt += nt_; tot_ob += ob; tot_nb += nb
    print(f"TOTAL old {tot_ot*1000:.0f} ms {tot_ob/1e6:.1f} MB read | new {tot_nt*1000:.1f} ms {tot_nb/1e6:.1f} MB read")
finally:
    store._connect = orig
    c.close()
print("PASS")
