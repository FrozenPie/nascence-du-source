"""
Offline regression test for J-1867 / F-2489: core.associative_recall must be rebased by
core.profile.activate_profile() like every other module-level data/ path constant.

THE LEAK (F-2489). The J-1718 dynamic write audit RE-RUN on the J-1824-fixed tree (all 3 probes; the
first run stopped at the first unclean cycle) caught the correction-probe cycle's memory recall making
6 write attempts against the tree's own data/ top level from core.associative_recall: _save_persisted
(embedding_matrix.tmp.npz -> embedding_matrix.npz, from _EMB_CACHE) and the shadow logs _LOG,
_LENS1_LOG, _LENS2_LOG, _LENS3_LOG. Worse than log noise: _refresh() loads the persisted matrix, DROPS
every id absent from the CURRENT DB, and re-saves -- so a named profile with its own small memory DB
would have shrunk Du's REAL embedding_matrix.npz to the profile's own few fragments.

HOW THIS TEST STAYS SAFE. Every path lives under a tempdir (core.profile._DATA and every constant
under test are pointed there BEFORE activate_profile() runs; the "live" files are stand-ins), and a
sys.addaudithook installed before the first core import RAISES on any write-mode open / sqlite3.connect
/ rename / mkdir under the real C:\\Nascence\\data or this tree's own data/ -- a real write is a hard
FAIL, never advisory.

Covers: 0 premise (core from this tree; the 5 constants live under _DATA); 1 activate_profile(<named>)
rebases all 5 and drops the process-global matrix cache; 2 a real _refresh() (the function that did the
destructive re-save) run under the named profile builds the PROFILE's own matrix from the PROFILE's own
DB and leaves the live stand-in matrix byte-identical (sha256 + mtime_ns); 3 re-activation never nests
and re-resets the cache; 4 root alias (activate_profile(None)) is an identity no-op; 5 audit hook saw
zero real-tree writes.

Expected: FAILS on HEAD (constants stay at the live path; the live stand-in matrix is rewritten), PASSES
with the J-1867 change.   Run: python scripts/_test_j1867_assoc_recall_rebase.py   (exit 0 = all passed)
"""
import hashlib
import os
import shutil
import sqlite3
import sys
import tempfile
import threading
import time
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TREE))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REAL_ROOTS = [os.path.normcase(str(Path(r"C:\Nascence\data").resolve())),
              os.path.normcase(str(TREE / "data"))]
HOOK_EVENTS: list = []
_busy = threading.local()
_WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC


def _norm(p):
    try:
        if isinstance(p, int):
            return None
        if isinstance(p, bytes):
            p = os.fsdecode(p)
        return os.path.normcase(os.path.abspath(os.fspath(p)))
    except Exception:
        return None


def _is_real(p):
    return bool(p) and any(p == r or p.startswith(r + os.sep) for r in REAL_ROOTS)


def _hook(event, args):
    if getattr(_busy, "on", False):
        return
    path = None
    if event == "open":
        m, fl = args[1], args[2]
        w = (isinstance(m, str) and any(c in m for c in "wax+")) or \
            (isinstance(fl, int) and bool(fl & _WRITE_FLAGS) and m != "r")
        if not w:
            return
        path = _norm(args[0])
    elif event == "sqlite3.connect":
        path = _norm(args[0])
    elif event in ("os.rename", "os.replace"):
        path = _norm(args[1]) if _is_real(_norm(args[1])) else _norm(args[0])
    elif event in ("os.remove", "os.mkdir", "os.rmdir", "shutil.copyfile"):
        path = _norm(args[-1] if event == "shutil.copyfile" else args[0])
    else:
        return
    if not _is_real(path):
        return
    _busy.on = True
    try:
        HOOK_EVENTS.append({"event": event, "path": path})
    finally:
        _busy.on = False
    raise PermissionError(f"J-1867 test hook: blocked real-data {event} {path}")


sys.addaudithook(_hook)

import core  # noqa: E402  -- BEFORE anything else from the tree (and before any lab_env)
assert str(Path(core.__file__).resolve()).lower().startswith(str(TREE).lower()), core.__file__

import numpy as np                      # noqa: E402
import core.profile as P                # noqa: E402
import core.associative_recall as AR    # noqa: E402
import core.memory.store as S           # noqa: E402

results = []


def check(name, cond, detail=""):
    results.append((name, bool(cond)))
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"  -- {detail}" if (detail and not cond) else ""))


def snap(path: Path):
    try:
        return (hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mtime_ns)
    except FileNotFoundError:
        return None


SPEC = [
    ("_LOG",       Path("associative_recall_shadow.jsonl")),
    ("_EMB_CACHE", Path("embedding_matrix.npz")),
    ("_LENS1_LOG", Path("associative_recall_lens1_shadow.jsonl")),
    ("_LENS2_LOG", Path("associative_recall_lens2_shadow.jsonl")),
    ("_LENS3_LOG", Path("associative_recall_lens3_shadow.jsonl")),
]
# the two fenced-but-unrebased instrument logs the same audit re-run's stderr showed (hook-invisible:
# guard_path() raises before any open) -- (module, attr, rel)
import core.retrieval_probe as RP       # noqa: E402
import core.r_shadow as RS              # noqa: E402
import core.reentry as RE            # noqa: E402  -- NOT fenced; hook-visible leak found by a 2nd audit re-run (cycle 3)
EXTRA = [(RP, "_LOG", Path("retrieval_probe_log.jsonl")), (RS, "_SHADOW_LOG", Path("r_shadow.jsonl")),
         (RE, "_DATA", Path(".")), (RE, "_LOG", Path("reentry_shadow.jsonl")), (RE, "_STATE", Path("reentry_state.json"))]

print("\n=== J-1867 / F-2489 -- core.associative_recall rebase isolation (offline, tempdir, audit hook) ===\n")
print("0. Premise")
check("core imported from the tree under test", Path(core.__file__).resolve().parent.parent == TREE, core.__file__)
for attr, rel in SPEC:
    v = getattr(AR, attr, None)
    try:
        r = v.relative_to(P._DATA)
    except (ValueError, AttributeError):
        r = None
    check(f"associative_recall.{attr} == core.profile._DATA / {rel.as_posix()!r}", r == rel, f"{v} vs _DATA={P._DATA}")

for mod, attr, rel in EXTRA:
    v = getattr(mod, attr, None)
    try:
        r = v.relative_to(P._DATA)
    except (ValueError, AttributeError):
        r = None
    check(f"{mod.__name__}.{attr} == core.profile._DATA / {rel.as_posix()!r}", r == rel, f"{v} vs _DATA={P._DATA}")

TMP = Path(tempfile.mkdtemp(prefix="j1867_assoc_iso_"))
OLD_NS = 1_700_000_000 * 10 ** 9
DIM = 4
try:
    FAKE = TMP / "data"
    (FAKE / "memory").mkdir(parents=True)
    _REAL_DATA = P._DATA
    P._DATA = FAKE
    for attr, rel in SPEC:
        setattr(AR, attr, FAKE / rel)
    for mod, attr, rel in EXTRA:
        setattr(mod, attr, FAKE / rel)
    S.DB_PATH = FAKE / "memory" / "nascence.db"

    # the live stand-in persisted matrix: 3 "Du" fragments
    live_M = np.eye(3, DIM, dtype=np.float32)
    np.savez(FAKE / "embedding_matrix.npz", M=live_M, ids=np.asarray(["du1", "du2", "du3"], dtype="U64"))
    for attr, rel in SPEC:
        if rel.suffix == ".jsonl":
            (FAKE / rel).write_text('{"stand_in": true}\n', encoding="utf-8")
    for attr, rel in SPEC:
        os.utime(FAKE / rel, ns=(OLD_NS, OLD_NS))
    LIVE_FILES = [rel for _, rel in SPEC]
    before = {rel: snap(FAKE / rel) for rel in LIVE_FILES}

    print("\n1. activate_profile(<named>) rebases all five constants and drops the matrix cache")
    AR._cache.update(ts=time.time(), M="SENTINEL-from-a-previous-profile", ids=["x"])
    PROFILE = "_j1867_assoc_iso"
    base = P.activate_profile(PROFILE)
    for attr, rel in SPEC:
        check(f"associative_recall.{attr} rebased into the profile dir", getattr(AR, attr) == base / rel,
              f"{getattr(AR, attr)} != {base / rel}")
    for mod, attr, rel in EXTRA:
        check(f"{mod.__name__}.{attr} rebased into the profile dir", getattr(mod, attr) == base / rel,
              f"{getattr(mod, attr)} != {base / rel}")
    check("_cache dropped on activation", AR._cache["M"] is None and AR._cache["ts"] == 0.0, AR._cache["M"])
    check("store.DB_PATH is the profile's own DB", S.DB_PATH == base / "memory" / "nascence.db", S.DB_PATH)

    print("\n2. A real _refresh() under the named profile builds the PROFILE's matrix and spares the live one")
    S.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(S.DB_PATH))
    conn.execute("CREATE TABLE memory_fragments (fragment_id TEXT PRIMARY KEY, importance REAL, timestamp REAL, "
                 "cold INTEGER, chapter_id TEXT, origin TEXT, embedding BLOB, "
                 "layer TEXT NOT NULL DEFAULT 'episodic', kind TEXT)")   # J-2357: layer (J-2018 filter) + kind (J-2098) as in core.memory.store schema
    for i, fid in enumerate(["p1", "p2"]):
        v = np.zeros(DIM, dtype=np.float32)
        v[i] = 1.0
        conn.execute("INSERT INTO memory_fragments (fragment_id, importance, timestamp, cold, chapter_id, origin, "
                     "embedding, layer, kind) VALUES (?,?,?,?,?,?,?,?,?)",
                     (fid, 0.5, time.time(), 0, None, "lived", v.tobytes(), "episodic", None))
    conn.commit()
    conn.close()
    # J-2357: guard_path() (D-0179) refuses a write whose path sits under profile._DATA. This test points _DATA at the
    # tempdir FAKE root (so activate_profile rebases there), which makes the temp profile dir look like "default data/".
    # For the _refresh() call only, restore the REAL _DATA so the temp profile path is correctly "outside data/" -- an
    # upstream redirect, exactly the situation a real isolated run is in. The real data dir is never written.
    P._DATA = _REAL_DATA
    try:
        AR._refresh(time.time())
    finally:
        P._DATA = FAKE
    after = {rel: snap(FAKE / rel) for rel in LIVE_FILES}
    check("live stand-in embedding_matrix.npz byte-identical (sha256 + mtime_ns)",
          after[Path("embedding_matrix.npz")] == before[Path("embedding_matrix.npz")],
          f"before={before[Path('embedding_matrix.npz')]} after={after[Path('embedding_matrix.npz')]}")
    pm = base / "embedding_matrix.npz"
    check("the profile got its OWN persisted matrix", pm.exists(), pm)
    if pm.exists():
        z = np.load(pm, allow_pickle=False)
        check("profile matrix holds exactly the profile's fragments (not Du's)",
              sorted(str(x) for x in z["ids"]) == ["p1", "p2"], [str(x) for x in z["ids"]])
    check("in-process _cache ids are the profile's", sorted(AR._cache["ids"] or []) == ["p1", "p2"], AR._cache["ids"])
    check("no stray .tmp.npz in the live stand-in dir", not any(p.name.endswith(".tmp.npz") for p in FAKE.iterdir()),
          [p.name for p in FAKE.iterdir()])
    check("every live stand-in (matrix + 4 shadow logs) untouched", after == before, f"{before} vs {after}")

    print("\n3. Re-activation never nests and resets the cache again")
    P.activate_profile(PROFILE)
    check("same profile again -> same paths", all(getattr(AR, a) == base / r for a, r in SPEC),
          [str(getattr(AR, a)) for a, _ in SPEC])
    check("EXTRA paths: same profile again -> same paths", all(getattr(m, a) == base / r for m, a, r in EXTRA))
    check("cache reset again on re-activation", AR._cache["M"] is None, AR._cache["ids"])
    other = P.activate_profile(PROFILE + "_b")
    check("another profile -> its own paths, not nested",
          other == FAKE / "profiles" / (PROFILE + "_b") and all(getattr(AR, a) == other / r for a, r in SPEC),
          [str(getattr(AR, a)) for a, _ in SPEC])

    print("\n4. Root alias (Carl) is an identity no-op")
    P.activate_profile(None)
    for attr, rel in SPEC:
        check(f"associative_recall.{attr} back at the live path", getattr(AR, attr) == FAKE / rel,
              f"{getattr(AR, attr)} != {FAKE / rel}")
    for mod, attr, rel in EXTRA:
        check(f"{mod.__name__}.{attr} back at the live path", getattr(mod, attr) == FAKE / rel,
              f"{getattr(mod, attr)} != {FAKE / rel}")
finally:
    shutil.rmtree(TMP, ignore_errors=True)

print("\n5. Audit hook")
check("zero real-tree write/connect events during the whole run", not HOOK_EVENTS, HOOK_EVENTS[:5])

passed = sum(1 for _, ok in results if ok)
print(f"\n=== {passed}/{len(results)} passed ===")
sys.exit(0 if passed == len(results) else 1)
