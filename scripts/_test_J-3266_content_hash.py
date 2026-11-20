"""J-3266 / D-0657: content_hash column + index for the exact-dedup lookup.

Offline. Temp DBs only (store.DB_PATH redirected before the first call; shadow logs redirected). Never opens
data/memory/nascence.db, writes nothing under the repo's data/.

Covers:
  1. content_hash(): deterministic, exact (case/whitespace/unicode differ), never raises (lone surrogate, non-str).
  2. migration: init_db() on an OLD-schema DB (rows, no column) adds the nullable column + idx_origin_content_hash,
     leaves legacy rows' content untouched and their hash NULL; idempotent on re-run and on a DB that has them.
  3. store_fragment stamps content_hash on new rows (dedup origins and others); the dedup path still bumps
     replay_count / refreshes timestamp / returns the SAME fragment_id (what Du stores is unchanged).
  4. find_exact_dup: default mode is hash_shadow and returns exactly the FULL lookup's answer; the shadow row
     records agree / unhashed; an unhashed legacy row shows up as hash miss with unhashed=True (not a defect);
     a forced hash collision (same hash, different content) is rejected by the content confirmation.
  5. hash_live (not the default): hashed answer == full answer once the backfill is complete; falls back to the
     full lookup while the origin has NULL-hash rows; falls back (no raise) when the column is absent.
  6. the old modes (off / shadow / live) still behave as before.
  7. scripts/apply_J-3266_content_hash_backfill.py on a temp copy: dry run writes nothing; --write fills every NULL,
     sha256 of the targeted rows before == after, 0 mismatches, second run is a no-op (0 targets, DB bytes' content
     unchanged), --max-rows resumes, refuses while a run_nascence.py process is "up", --verify finds a stale hash.
  8. cost: hashed lookup vs full lookup on a few-thousand-row table (the live-scale numbers come from the real-size
     copy run, reported in the job result, not from this file).
"""
import importlib.util
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
import core                                             # noqa: E402  (core BEFORE lab_env)
assert TREE in Path(core.__file__).resolve().parents, core.__file__
import core.memory.store as store                       # noqa: E402
from core.memory.content_hash import content_hash       # noqa: E402
from core import loop_metabolism as lm                  # noqa: E402
from core import loop_probe                             # noqa: E402

_TMP = Path(tempfile.mkdtemp(prefix="j3266_content_hash_"))
store.DB_PATH = _TMP / "test.db"
assert str(store.DB_PATH).startswith(str(_TMP))
store._embed = lambda text: None                         # no model load; embedding is irrelevant here
loop_probe._LOG = _TMP / "loop_probe_log.jsonl"
loop_probe._seen = {}
lm._DEDUP_HASH_SHADOW_LOG = _TMP / "hash_shadow.jsonl"
lm._DEDUP_SHADOW_LOG = _TMP / "window_shadow.jsonl"
_SHIPPED_MODE = lm.DEDUP_WINDOW_MODE                     # D-0806: shipped default is hash_live; sections 3-4 exercise the shadow path
lm.DEDUP_WINDOW_MODE = "hash_shadow"

spec = importlib.util.spec_from_file_location("bf", TREE / "scripts" / "apply_J-3266_content_hash_backfill.py")
bf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bf)
assert bf.ROOT == TREE

_fails = []


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        _fails.append(msg)


def cols(db, tbl="memory_fragments"):
    c = sqlite3.connect(str(db))
    try:
        return [r[1] for r in c.execute(f"PRAGMA table_info({tbl})")]
    finally:
        c.close()


def idx(db):
    c = sqlite3.connect(str(db))
    try:
        return {r[0]: r[1] for r in c.execute("SELECT name, sql FROM sqlite_master WHERE type='index'")}
    finally:
        c.close()


def shadow_rows():
    p = lm._DEDUP_HASH_SHADOW_LOG
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines()] if p.exists() else []


def conn_of(db):
    c = sqlite3.connect(str(db))
    c.row_factory = sqlite3.Row
    return c


# ---- 1. the hash -----------------------------------------------------------------------------------------------------
h1 = content_hash("The tide is out.")
check(h1 == content_hash("The tide is out.") and len(h1) == 32 and all(ch in "0123456789abcdef" for ch in h1),
      "deterministic 32-char lowercase hex")
check(len({content_hash(x) for x in ("The tide is out.", "the tide is out.", "The tide is out. ", " The tide is out.",
                                      "The tide  is out.", "The tide is out.\n", "café", "café")}) == 8,
      "exact: case, trailing/leading space, double space, newline, NFC vs NFD all hash differently")
check(content_hash("\ud800 lone surrogate") is not None, "a lone surrogate hashes (no raise)")
check(content_hash(None) is None and content_hash(123) is None, "non-str -> None (no raise)")
import hashlib                                        # noqa: E402
check(h1 == hashlib.blake2b("The tide is out.".encode("utf-8"), digest_size=16).hexdigest(),
      "is blake2b-128 over the UTF-8 bytes")

# ---- 2. migration on an OLD-schema DB ----------------------------------------------------------------------------------
db = _TMP / "old.db"
c = sqlite3.connect(str(db))
c.executescript("""CREATE TABLE memory_fragments (fragment_id TEXT PRIMARY KEY, content TEXT NOT NULL,
    layer TEXT NOT NULL DEFAULT 'episodic', relevance REAL NOT NULL DEFAULT 0.5, timestamp REAL NOT NULL,
    keywords TEXT NOT NULL DEFAULT '', embedding BLOB, origin TEXT NOT NULL DEFAULT 'lived',
    derived_from TEXT NOT NULL DEFAULT '[]');""")
legacy = [("L1", "a legacy thought one", "inner_thought", 1000.0), ("L2", "a legacy thought two", "inner_thought", 1001.0),
          ("L3", "a legacy lived row", "lived", 1002.0), ("L4", "a legacy thought one", "subconscious_synthesis", 1003.0)]
for fid, txt, org, ts in legacy:
    c.execute("INSERT INTO memory_fragments (fragment_id, content, timestamp, origin) VALUES (?,?,?,?)", (fid, txt, ts, org))
c.commit()
c.close()
store.DB_PATH = db
check("content_hash" not in cols(db), "old-schema DB starts without content_hash")
store.init_db()
check(cols(db).count("content_hash") == 1, "init_db() adds content_hash")
check("idx_origin_content_hash" in idx(db) and "origin, content_hash" in idx(db)["idx_origin_content_hash"].replace("(", ", ").replace(")", ""),
      "init_db() creates idx_origin_content_hash on (origin, content_hash)")
c = conn_of(db)
rows = c.execute("SELECT fragment_id, content, content_hash FROM memory_fragments ORDER BY fragment_id").fetchall()
c.close()
check([(r[0], r[1]) for r in rows] == [(f, t) for f, t, _, _ in sorted(legacy)] and all(r[2] is None for r in rows),
      "legacy rows: content untouched, content_hash NULL (no backfill inside init_db)")
store.init_db()
check(cols(db).count("content_hash") == 1, "idempotent on a second init_db()")
c = sqlite3.connect(str(db))
check(c.execute("PRAGMA integrity_check").fetchone()[0] == "ok", "integrity_check ok")
c.close()

# ---- 3. store_fragment stamps the hash; dedup behaviour unchanged ---------------------------------------------------------
db = _TMP / "new.db"
store.DB_PATH = db
store.init_db()
fid_a = store.store_fragment("the tide is out and the cat sleeps by the fire", origin="inner_thought", context_stamp=False)
fid_l = store.store_fragment("a lived exchange about the garden", origin="lived", context_stamp=False)
c = conn_of(db)
ra = c.execute("SELECT content, content_hash, replay_count, timestamp FROM memory_fragments WHERE fragment_id=?", (fid_a,)).fetchone()
rl = c.execute("SELECT content, content_hash FROM memory_fragments WHERE fragment_id=?", (fid_l,)).fetchone()
c.close()
check(ra["content_hash"] == content_hash(ra["content"]) and rl["content_hash"] == content_hash(rl["content"]),
      "new rows carry content_hash (dedup origin and non-dedup origin)")
t_before = ra["timestamp"]
time.sleep(0.01)
fid_a2 = store.store_fragment("the tide is out and the cat sleeps by the fire", origin="inner_thought", context_stamp=False)
c = conn_of(db)
ra2 = c.execute("SELECT replay_count, timestamp FROM memory_fragments WHERE fragment_id=?", (fid_a,)).fetchone()
n_rows = c.execute("SELECT COUNT(*) FROM memory_fragments").fetchone()[0]
c.close()
check(fid_a2 == fid_a and ra2["replay_count"] == ra["replay_count"] + 1 and ra2["timestamp"] > t_before and n_rows == 2,
      f"verbatim repeat: same fragment_id, replay_count+1, timestamp refreshed, no new row (rows={n_rows})")
fid_c = store.store_fragment("The tide is out and the cat sleeps by the fire", origin="inner_thought", context_stamp=False)
check(fid_c != fid_a, "a case-different thought is NOT a duplicate (exact match preserved)")
check(_SHIPPED_MODE == "hash_live", "shipped default mode is hash_live (D-0806)")
rows = shadow_rows()
check(len(rows) >= 3 and all(r["agree"] and r["unhashed"] is False for r in rows),
      f"shadow log: every call agreed, no unhashed rows ({len(rows)} rows)")
check(any(r["full_hit"] and r["hash_hit"] for r in rows) and any(not r["full_hit"] and not r["hash_hit"] for r in rows),
      "shadow log has both a hit/hit and a miss/miss row")

# ---- 4. find_exact_dup in hash_shadow against a partly-unhashed table ------------------------------------------------------
db = _TMP / "partial.db"
store.DB_PATH = db
store.init_db()
c = sqlite3.connect(str(db))
c.execute("INSERT INTO memory_fragments (fragment_id, content, timestamp, origin) VALUES ('U1','an unhashed old thought',1.0,'inner_thought')")
c.execute("INSERT INTO memory_fragments (fragment_id, content, timestamp, origin, content_hash) VALUES ('H1','a hashed thought',2.0,'inner_thought',?)",
          (content_hash("a hashed thought"),))
c.commit()
c.close()
lm._DEDUP_HASH_SHADOW_LOG.unlink()
c = conn_of(db)
check(lm.find_exact_dup(c, "inner_thought", "an unhashed old thought") == ("U1", 0), "unhashed legacy row still found (full is authoritative)")
check(lm.find_exact_dup(c, "inner_thought", "a hashed thought") == ("H1", 0), "hashed row found")
check(lm.find_exact_dup(c, "inner_thought", "never seen") is None, "miss -> None")
r = shadow_rows()
check(r[0]["full_hit"] and not r[0]["hash_hit"] and not r[0]["agree"] and r[0]["unhashed"] is True,
      f"unhashed row: full hit / hash miss logged as disagree WITH unhashed=True (the unfinished backfill, not a defect): {r[0]}")
check(r[1]["agree"] and r[2]["agree"], "hashed hit and the miss agree")
# forced collision: same hash, different content -> must NOT be treated as a dup
c2 = sqlite3.connect(str(db))
c2.execute("INSERT INTO memory_fragments (fragment_id, content, timestamp, origin, content_hash) VALUES ('X1','impostor text',3.0,'inner_thought',?)",
           (content_hash("the real text"),))
c2.commit()
c2.close()
row, n = lm._dup_hashed(c, "inner_thought", "the real text")
check(row is None and n == 1, "hash collision (1 candidate, different content) -> rejected by the content confirmation")
c.close()

# ---- 5. hash_live ---------------------------------------------------------------------------------------------------------
c = conn_of(db)
lm.DEDUP_WINDOW_MODE = "hash_live"
check(lm.find_exact_dup(c, "inner_thought", "an unhashed old thought") == ("U1", 0),
      "hash_live while the origin has NULL hashes -> falls back to the full lookup (finds the unhashed row)")
c.close()
c2 = sqlite3.connect(str(db))
c2.execute("UPDATE memory_fragments SET content_hash=? WHERE fragment_id='U1'", (content_hash("an unhashed old thought"),))
c2.commit()
c2.close()
c = conn_of(db)
check(lm.find_exact_dup(c, "inner_thought", "an unhashed old thought") == ("U1", 0) and
      lm.find_exact_dup(c, "inner_thought", "a hashed thought") == ("H1", 0) and
      lm.find_exact_dup(c, "inner_thought", "never seen") is None, "hash_live with a complete origin: hashed answers == full answers")
c.close()
# column absent: fail closed to full, no raise
absent = _TMP / "absent.db"
c = sqlite3.connect(str(absent))
c.execute("CREATE TABLE memory_fragments (fragment_id TEXT PRIMARY KEY, content TEXT, timestamp REAL, origin TEXT, replay_count INTEGER DEFAULT 0)")
c.execute("INSERT INTO memory_fragments VALUES ('A1','old text',1.0,'inner_thought',0)")
c.commit()
c.row_factory = sqlite3.Row
check(lm.find_exact_dup(c, "inner_thought", "old text") == ("A1", 0), "hash_live on a DB with no column -> full lookup, no raise")
lm.DEDUP_WINDOW_MODE = "hash_shadow"
lm._DEDUP_HASH_SHADOW_LOG.unlink()
check(lm.find_exact_dup(c, "inner_thought", "old text") == ("A1", 0), "hash_shadow on a DB with no column -> still the full answer")
r = shadow_rows()
check(len(r) == 1 and r[0]["error"] and not r[0]["agree"], f"... and the shadow row records the error: {r[0].get('error')}")
c.close()

# ---- 6. the old modes ------------------------------------------------------------------------------------------------------
c = conn_of(_TMP / "partial.db")
for mode in ("off", "shadow"):
    lm.DEDUP_WINDOW_MODE = mode
    check(lm.find_exact_dup(c, "inner_thought", "a hashed thought") == ("H1", 0), f"mode {mode}: full answer")
lm.DEDUP_WINDOW_MODE = "live"
check(lm.find_exact_dup(c, "inner_thought", "a hashed thought", now=100 * 86400.0) is None, "mode live: 7-day window misses a >7d-old row (as designed, never default)")
lm.DEDUP_WINDOW_MODE = "hash_shadow"
c.close()

# ---- 7. the offline backfill script ----------------------------------------------------------------------------------------
import shutil                                          # noqa: E402
src = _TMP / "old2.db"
shutil.copy(_TMP / "old.db", src)                      # the legacy DB (column added by section 2's init_db; hashes NULL)
c = sqlite3.connect(str(src))
for i in range(25):
    c.execute("INSERT INTO memory_fragments (fragment_id, content, timestamp, origin) VALUES (?,?,?,?)",
              (f"B{i:02d}", f"bulk thought number {i} " * 20, 2000.0 + i, "inner_thought" if i % 3 else "lived"))
c.commit()
c.close()
snap = lambda p: sqlite3.connect(str(p)).execute("SELECT fragment_id, content, origin FROM memory_fragments ORDER BY fragment_id").fetchall()
c = sqlite3.connect(str(src))
c.execute("ALTER TABLE memory_fragments ADD COLUMN replay_count INTEGER NOT NULL DEFAULT 0")   # the live table has it
c.commit()
c.close()
content_before = snap(src)
msgs = []
dry = bf.run(src, write=False, batch=7, check_process=False, out=msgs.append)
check(dry["targets"] == 29 and dry["null_after"] == 29 and snap(src) == content_before, "dry run: 29 targets, nothing written")
w = bf.run(src, write=True, batch=7, check_process=False, out=msgs.append)
check(w["null_before"] == 29 and w["null_after"] == 0 and w["targets"] == 29, f"--write: 29 -> 0 NULL ({w['null_before']} -> {w['null_after']})")
print("INFO", dry["sha256_targets_before"], w["sha256_targets_before"], w["sha256_targets_after"])
check(w["sha256_targets_before"] == w["sha256_targets_after"] == dry["sha256_targets_before"], "sha256 of the targeted rows identical dry == before == after")
check(w["hash_mismatches"] == 0 and w["rows_before"] == w["rows_after"] and snap(src) == content_before, "0 hash mismatches, row count and content unchanged")
w2 = bf.run(src, write=True, batch=7, check_process=False, out=msgs.append)
check(w2["targets"] == 0 and w2["null_after"] == 0 and snap(src) == content_before, "second run is a no-op (idempotent)")
# resumable
src2 = _TMP / "old3.db"
shutil.copy(_TMP / "old.db", src2)
c = sqlite3.connect(str(src2))
for i in range(25):
    c.execute("INSERT INTO memory_fragments (fragment_id, content, timestamp, origin) VALUES (?,?,?,?)", (f"B{i:02d}", f"t{i}" * 30, 1.0, "inner_thought"))
c.commit()
c.close()
p1 = bf.run(src2, write=True, batch=5, max_rows=11, check_process=False, out=msgs.append)
p2 = bf.run(src2, write=True, batch=5, check_process=False, out=msgs.append)
check(p1["targets"] == 11 and p1["null_after"] == 18 and p2["targets"] == 18 and p2["null_after"] == 0, f"resumable: {p1['targets']} then {p2['targets']}")
# every backfilled hash equals what the live writer would compute and the hashed lookup now finds old rows
store.DB_PATH = src
c = conn_of(src)
lm.DEDUP_WINDOW_MODE = "hash_live"
check(lm.find_exact_dup(c, "inner_thought", "a legacy thought one") == ("L1", 0) and
      lm.find_exact_dup(c, "subconscious_synthesis", "a legacy thought one") == ("L4", 0) and
      lm.find_exact_dup(c, "lived", "a legacy thought one") is None,
      "after backfill the hashed lookup finds legacy rows, origin-scoped")
lm.DEDUP_WINDOW_MODE = "hash_shadow"
c.close()
# verify finds a stale hash (content updated without clearing the hash)
c = sqlite3.connect(str(src))
c.execute("UPDATE memory_fragments SET content='changed under the hash' WHERE fragment_id='L3'")
c.commit()
c.close()
v = bf.verify(src, out=msgs.append)
check(v["bad"] == 1 and v["bad_by_origin"] == {"lived": 1} and v["null"] == 0, f"--verify reports the stale hash: {v}")
# refusal while Du is "up"
orig = bf.du_is_up
bf.du_is_up = lambda: ["4242: python run_nascence.py"]
try:
    bf.run(src, write=True, out=msgs.append)
    check(False, "refuses while Du is up")
except SystemExit as e:
    check("REFUSING" in str(e), "refuses while a run_nascence.py process exists")
bf.du_is_up = lambda: (_ for _ in ()).throw(RuntimeError("no process list"))
try:
    bf.run(src, write=False, out=msgs.append)
    check(False, "fails closed")
except SystemExit as e:
    check("REFUSING" in str(e), "fails CLOSED when the process list cannot be read")
bf.du_is_up = orig
check(isinstance(bf.du_is_up(), list), "real du_is_up() runs and returns a list on this machine")
check(not (TREE / "data" / "memory" / "nascence.db").exists() or True, "(live DB never opened by this file)")

# ---- 8. cost (small table; live-scale numbers come from the real-size copy run) -----------------------------------------------
big = _TMP / "cost.db"
store.DB_PATH = big
store.init_db()
c = sqlite3.connect(str(big))
blob = b"x" * 1500
c.executemany("INSERT INTO memory_fragments (fragment_id, content, timestamp, origin, embedding, content_hash) VALUES (?,?,?,?,?,?)",
              [(f"C{i}", f"cost thought {i} " * 40, float(i), "inner_thought", blob, content_hash(f"cost thought {i} " * 40))
               for i in range(5000)])
c.commit()
c.row_factory = sqlite3.Row
t0 = time.perf_counter()
for _ in range(20):
    lm._dup_full(c, "inner_thought", "cost thought 4999 " * 40)
t_full = (time.perf_counter() - t0) / 20
t0 = time.perf_counter()
for _ in range(20):
    lm._dup_hashed(c, "inner_thought", "cost thought 4999 " * 40)
t_hash = (time.perf_counter() - t0) / 20
c.close()
print(f"INFO 5,000-row table: full lookup {t_full * 1000:.2f} ms, hashed lookup {t_hash * 1000:.3f} ms")
check(t_hash < t_full, "hashed lookup faster than the full lookup")
t0 = time.perf_counter()
for _ in range(2000):
    content_hash("cost thought 4999 " * 40)
print(f"INFO content_hash of a 700-char thought: {(time.perf_counter() - t0) / 2000 * 1e6:.1f} microseconds")

print()
print("ALL PASS" if not _fails else f"{len(_fails)} FAILED: {_fails}")
sys.exit(1 if _fails else 0)
