"""J-1970: isolated test of scripts/backfill_phase_J1970.py on a TEMP db (never the live one). Run directly."""
import json, sqlite3, subprocess, sys, tempfile, time
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
from core import theta_shadow as T
S = str(HERE / "scripts" / "backfill_phase_J1970.py")
tmp = Path(tempfile.mkdtemp(prefix="bf_test_J1970_")); db = tmp / "t.db"
c = sqlite3.connect(db)
c.execute("CREATE TABLE fragment_context (fragment_id TEXT PRIMARY KEY, tuple_ts REAL, source TEXT, tod REAL, season REAL, daylight TEXT)")
base = time.mktime((2026, 8, 1, 3, 4, 5, 0, 0, -1))
for i in range(40):
    ts = base + i * 7919.3
    if i % 4 == 0:
        t, s = T.now_phase(ts); c.execute("INSERT INTO fragment_context VALUES (?,?,?,?,?,?)", (f"s{i}", ts, "experienced:x", t, s, "day"))
    else:
        c.execute("INSERT INTO fragment_context VALUES (?,?,?,NULL,NULL,NULL)", (f"n{i}", ts, "census_world:idle"))
c.execute("INSERT INTO fragment_context VALUES ('nots', NULL, 'x', NULL, NULL, NULL)")
c.commit(); c.close()
fails = 0
def check(ok, m):
    global fails; print(("ok   " if ok else "FAIL ") + m); fails += (not ok)
def run(*a):
    return subprocess.run([sys.executable, S, *a, "--db", str(db)], capture_output=True, text=True)
r = run("precheck"); check(r.returncode == 0 and json.loads(r.stdout)["null_rows_with_tuple_ts"] == 30, "precheck bit-exact, 30 NULL rows")
r = run("dryrun", "--manifest", str(tmp / "d.json")); d = json.load(open(tmp / "d.json"))
check(r.returncode == 0 and d["would_fill"] == 30 and len(d["ids"]) == 30, "dryrun manifest lists 30 ids")
check(sqlite3.connect(db).execute("select count(*) from fragment_context where tod is null").fetchone()[0] == 31, "dryrun wrote nothing")
r = run("apply", "--manifest", str(tmp / "a.json")); a = json.load(open(tmp / "a.json"))
check(r.returncode == 0 and a["filled"] == 30 and "VERIFIED" in r.stdout, "apply filled 30, verified")
q = sqlite3.connect(db)
check(q.execute("select count(*) from fragment_context where tod is null").fetchone()[0] == 1, "only the no-tuple_ts row left NULL")
check(q.execute("select count(*) from fragment_context where daylight is null").fetchone()[0] == 31, "daylight untouched")
check(all(q.execute("select tod,season from fragment_context where fragment_id=?", (i,)).fetchone() == T.now_phase(q.execute("select tuple_ts from fragment_context where fragment_id=?", (i,)).fetchone()[0]) for i in d["ids"]), "values equal now_phase")
q.close()
r = run("apply", "--manifest", str(tmp / "a2.json")); check("nothing to fill" in r.stdout, "second apply is a no-op")
q = sqlite3.connect(db); q.execute("UPDATE fragment_context SET tod=0.5 WHERE fragment_id='s0'"); q.commit(); q.close()
r = run("precheck"); check(r.returncode == 2, "tampered stored row -> precheck fails (exit 2)")
q = sqlite3.connect(db); t = T.now_phase(q.execute("select tuple_ts from fragment_context where fragment_id='s0'").fetchone()[0]); q.execute("UPDATE fragment_context SET tod=? WHERE fragment_id='s0'", (t[0],)); q.commit(); q.close()
r = run("revert", "--manifest", str(tmp / "a.json")); 
q = sqlite3.connect(db)
check(q.execute("select count(*) from fragment_context where tod is null").fetchone()[0] == 31 and q.execute("select count(*) from fragment_context where tod is not null").fetchone()[0] == 10, "revert restored exactly the 30 rows to NULL, kept the 10 originals")
live = subprocess.run([sys.executable, S, "apply", "--manifest", str(tmp / "x.json")], capture_output=True, text=True)
check(live.returncode != 0 and "--live" in (live.stderr + live.stdout), "apply on the LIVE db refuses without --live (default --db is live)")
print("FAILED" if fails else "ALL PASS"); sys.exit(1 if fails else 0)
