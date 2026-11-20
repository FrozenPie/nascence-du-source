"""scripts/test_study_archive_lock.py (J-1924 / F-2549 residual b): core/study.archive_book_note_files' chapter_id UPDATE now runs under
world_consolidation._FILE_LOCK (the lock J-1917 added so file_book_notes cannot overlap the worker-thread sweep).
Everything runs on a SCRATCH sqlite DB + scratch Study dir (store.DB_PATH, study.STUDY_DIR/NOTES_SUBDIR, world_consolidation._LOG are
redirected before any call); no live data, no model, no network (socket connect is blocked and the block is proven first).
  T1  lock held by a 'sweep' thread -> archive_book_note_files' DB UPDATE waits (rows stay NULL), its FILE MOVES do not wait (the lock
      is around the DB block only); released -> the UPDATE lands, filed_db == number of notes; re-entrant from a lock-holding thread.
  T2  NEGATIVE CONTROL: the same T1 against the pre-change study.py (git show HEAD / --old FILE) -> the UPDATE lands WHILE the lock is held
      (no serialisation), so T1's assertion is genuinely about the new lock.
  T3  stress equivalence: real world_consolidation.sweep() looping in one thread while archive_book_note_files runs in another on a
      scratch DB; final (fragment_id, chapter_id) hash == the sequential (archive then sweep) result on an identical copy; no exceptions;
      PRAGMA integrity_check ok.
Run: python scripts/test_study_archive_lock.py [--old PATH_TO_PRE_CHANGE_study.py]"""
import sys, time, threading, pathlib, tempfile, shutil, hashlib, sqlite3, importlib.util, subprocess, socket
HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import core                                                       # core BEFORE anything else; assert the tree under test
assert pathlib.Path(core.__file__).resolve().parent.parent == HERE, core.__file__
from core.memory import store
from core import study, world_consolidation as wc

# no network: block connects, then prove the block
def _blocked(self, *a, **k): raise OSError("test_study_archive_lock: no network")
socket.socket.connect = _blocked
try:
    socket.create_connection(("127.0.0.1", 9), timeout=1)
    raise SystemExit("network block FAILED")
except OSError as e:
    assert "no network" in str(e), e

BOOK = "Zephyr Chronicles Almanac"
OTHER = "Quartz Meridian Ledger"
N_NOTES = 12
SCR = pathlib.Path(tempfile.mkdtemp(prefix="J-1924_study_lock_"))


def make_scratch(tag, n_reading=300):
    """fresh scratch DB + Study dir with N_NOTES TAB_ files citing BOOK, fragments for them, an essay gist and tagged reading rows"""
    d = SCR / tag
    d.mkdir(parents=True)
    db = d / "nascence.db"
    sd = d / "Study"
    sd.mkdir()
    conn = sqlite3.connect(str(db))
    conn.execute("CREATE TABLE memory_fragments (fragment_id TEXT PRIMARY KEY, content TEXT NOT NULL, layer TEXT DEFAULT 'episodic', "
                 "relevance REAL DEFAULT 0.5, timestamp REAL NOT NULL, keywords TEXT DEFAULT '', embedding BLOB, origin TEXT DEFAULT 'lived', "
                 "derived_from TEXT DEFAULT '[]', chapter_id TEXT)")
    t0 = 1_790_000_000.0
    rows = [("gist1", f"[Essay on '{BOOK}'] the capstone essay about {BOOK}.", "essay", t0 + 5000),
            ("gist2", f"[Essay on '{OTHER}'] a different book's capstone.", "essay", t0 + 4000)]
    for i in range(N_NOTES):
        t = f"Notes number {i} on almanac weather"
        rows.append((f"st{i}", f"[My study note: '{t}'] body {i}", "study", t0 + i))
        (sd / f"TAB_2026100{i % 9}_{i:04d}_note{i}.md").write_text(
            f"# {t}\n\n*A study note by x · 2026-10-07 12:00 · on: {BOOK}*\n\nbody {i} " + "x" * 60 + "\n", encoding="utf-8")
    for i in range(n_reading):
        book = BOOK if i % 3 else OTHER
        rows.append((f"rd{i}", f"[Read from '{book}' p{i}] passage {i}", "reading", t0 + 100 + i))
    conn.executemany("INSERT INTO memory_fragments (fragment_id,content,origin,timestamp) VALUES (?,?,?,?)", rows)
    conn.commit()
    conn.close()
    return db, sd


def redirect(mod, db, sd):
    store.DB_PATH = db
    mod.STUDY_DIR = sd
    mod.NOTES_SUBDIR = sd / "notes"
    wc._LOG = db.parent / "wc_log.jsonl"
    wc._completed_passes_for = lambda title: 1          # reading_state is not on the scratch tree


def chash(db):
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    r = c.execute("SELECT fragment_id, COALESCE(chapter_id,'') FROM memory_fragments ORDER BY fragment_id").fetchall()
    c.close()
    return hashlib.sha256(repr(r).encode()).hexdigest()[:16], sum(1 for _, ch in r if ch)


def null_count(db):
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    n = c.execute("SELECT COUNT(*) FROM memory_fragments WHERE origin='study' AND chapter_id IS NULL").fetchone()[0]
    c.close()
    return n


def lock_probe(mod, tag):
    """hold wc._FILE_LOCK in this thread, run mod.archive_book_note_files in a worker; report what it did while we held the lock"""
    db, sd = make_scratch(tag, n_reading=0)
    redirect(mod, db, sd)
    out = {}
    res = {}

    def worker():
        res["r"] = mod.archive_book_note_files(BOOK)
    with wc._FILE_LOCK:
        th = threading.Thread(target=worker, daemon=True)
        th.start()
        t_end = time.time() + 4.0
        while time.time() < t_end and not (sd / "notes").exists():
            time.sleep(0.02)
        time.sleep(1.0)
        out["alive_while_held"] = th.is_alive()
        out["null_while_held"] = null_count(db)
        out["moved_while_held"] = len(list((sd / "notes").glob("*/TAB_*.md"))) if (sd / "notes").exists() else 0
    th.join(15)
    out["finished"] = not th.is_alive()
    out["res"] = res.get("r", {})
    out["null_after"] = null_count(db)
    return out


ok = True


def check(name, cond, extra=""):
    global ok
    ok &= bool(cond)
    print(("PASS " if cond else "FAIL ") + name, extra)


# T1
p = lock_probe(study, "t1")
print("T1:", {k: v for k, v in p.items() if k != "res"}, "filed_db=%s moved=%s" % (p["res"].get("filed_db"), p["res"].get("moved")))
check("T1 DB UPDATE waits for _FILE_LOCK (thread alive, 12 study rows still NULL while held)", p["alive_while_held"] and p["null_while_held"] == N_NOTES)
check("T1 file moves do NOT wait for the lock (all 12 TAB files already moved while held)", p["moved_while_held"] == N_NOTES)
check("T1 after release: finished, filed_db == 12, 0 study rows NULL", p["finished"] and p["res"].get("filed_db") == N_NOTES and p["null_after"] == 0)
db, sd = make_scratch("t1b", 0)
redirect(study, db, sd)
with wc._FILE_LOCK:                                     # re-entrant: a caller already holding the lock must not deadlock
    r = study.archive_book_note_files(BOOK)
check("T1 re-entrant from a lock-holding thread", r.get("filed_db") == N_NOTES and r.get("moved") == N_NOTES)

# T2 negative control: pre-change study.py
old_path = None
if "--old" in sys.argv:
    old_path = sys.argv[sys.argv.index("--old") + 1]
if old_path is None:
    old_path = str(SCR / "study_old.py")
    src = subprocess.run(["git", "-C", str(HERE), "show", "HEAD:core/study.py"], capture_output=True, text=True, encoding="utf-8").stdout
    if "_FILE_LOCK" in src:
        print("NOTE: HEAD already contains the lock; pass --old PATH (pre-change study.py) for the negative control")
        old_path = None
    else:
        pathlib.Path(old_path).write_text(src, encoding="utf-8")
if old_path:
    assert "_FILE_LOCK" not in pathlib.Path(old_path).read_text(encoding="utf-8")
    spec = importlib.util.spec_from_file_location("study_old", old_path)
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    q = lock_probe(old, "t2")
    print("T2 (pre-change code):", {k: v for k, v in q.items() if k != "res"})
    check("T2 NEGATIVE CONTROL: without the lock the UPDATE lands while the lock is held (thread finished, 0 NULL) -- the T1 wait is the new lock",
          (not q["alive_while_held"]) and q["null_while_held"] == 0)

# T3 stress equivalence
dbA, sdA = make_scratch("t3_seq", 300)
redirect(study, dbA, sdA)
rs = study.archive_book_note_files(BOOK)
wc.sweep(now=1_791_400_000.0)
hA, nA = chash(dbA)
dbB, sdB = make_scratch("t3_con", 300)
redirect(study, dbB, sdB)
errs = []
stop = threading.Event()
sweeps = [0]


def sweeper():
    try:
        while not stop.is_set():
            wc.sweep(now=1_791_400_000.0)
            sweeps[0] += 1
    except Exception as e:
        errs.append(("sweep", repr(e)))


def archiver():
    try:
        for _ in range(3):                       # repeat: later calls are no-ops, hammer the lock
            study.archive_book_note_files(BOOK)
    except Exception as e:
        errs.append(("archive", repr(e)))


ts = threading.Thread(target=sweeper)
ta = threading.Thread(target=archiver)
ts.start()
ta.start()
ta.join(60)
time.sleep(0.5)
stop.set()
ts.join(60)
wc.sweep(now=1_791_400_000.0)            # settle (sweep is idempotent)
hB, nB = chash(dbB)
c = sqlite3.connect(f"file:{dbB}?mode=ro", uri=True)
integ = c.execute("PRAGMA integrity_check").fetchone()[0]
c.close()
print("T3: sequential hash %s (%d filed) | concurrent hash %s (%d filed) | sweeps during run %d | errs %s | integrity %s | seq archive filed_db %s"
      % (hA, nA, hB, nB, sweeps[0], errs, integ, rs.get("filed_db")))
check("T3 concurrent final chapter_id hash == sequential result", hA == hB and nA == nB and nA > N_NOTES)
check("T3 no exceptions, integrity ok, at least one sweep overlapped", not errs and integ == "ok" and sweeps[0] >= 1)
shutil.rmtree(SCR, ignore_errors=True)
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
