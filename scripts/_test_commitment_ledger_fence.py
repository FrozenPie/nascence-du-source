"""
Regression: core/commitment_ledger.py's four files AND its direct live-DB UPDATE sit behind the D-0179 write fence
(J-1814 / F-2428).

The gap: _LEDGER (commitment_ledger.jsonl), _ACTIVE (commitment_active.json), _OBSERVED (commitment_observed.jsonl) and
_HOLDRATE_LOG (commitment_holdrate.jsonl) were written with no profile.guard_path, and _stakes('formed') did a bare
sqlite3.connect(_DIR/memory/nascence.db) + UPDATE memory_fragments -- a direct WRITE to the LIVE memory DB that bypasses
store.DB_PATH, so lab_env.isolate() cannot cover it.
Fix: every target (and the DB path, BEFORE sqlite3.connect) resolved through guard_path before any I/O, INSIDE each
writer's existing fail-open try (all callers are best-effort; a refusal is swallowed at debug, one guard warning per path).

  [1] surface  [2] leak (simulated root, CONTROL = pre-fix source verbatim from git)  [3] real paths trapped
  [4] live byte-identical incl. error paths  [5] legit redirects  [6] visibility  [7] canary

  python scripts/_test_commitment_ledger_fence.py        # exit 0 = ALL OK
"""
from __future__ import annotations

import builtins
import hashlib
import json
import logging
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time as _time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

FAILS = 0


def check(cond, label):
    global FAILS
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS += 1


def _snap(p: Path):
    return None if not p.exists() else (p.stat().st_size, hashlib.sha256(p.read_bytes()).hexdigest())


_FILES = ("commitment_ledger.jsonl", "commitment_active.json", "commitment_observed.jsonl", "commitment_holdrate.jsonl")
_ATTRS = ("_LEDGER", "_ACTIVE", "_OBSERVED", "_HOLDRATE_LOG")
_DBREL = Path("memory") / "nascence.db"
_LIVE_DATA = Path(r"C:\Nascence") / "data"
_TREE_DATA = ROOT / "data"
_LIVE_SET = tuple(_LIVE_DATA / n for n in _FILES) + (_LIVE_DATA / _DBREL,)
_TREE_SET = tuple(_TREE_DATA / n for n in _FILES) + (_TREE_DATA / _DBREL,)
_WATCH = set(_LIVE_SET) | set(_TREE_SET)
_before = {p: _snap(p) for p in _WATCH}

import core                                      # noqa: E402  (BEFORE anything that could hijack sys.path -- F-2423)
from core import profile as P                    # noqa: E402
from core import commitment_ledger as CL         # noqa: E402

check(Path(core.__file__).resolve().is_relative_to(ROOT), f"core imported from the tree under test ({core.__file__})")

TMP = Path(tempfile.mkdtemp(prefix="j1814_commitment_fence_"))
_orig = dict(DATA=P._DATA, CANON=P._CANONICAL_DATA, LIVE=P.LIVE, DIR=CL._DIR, PATHS={a: getattr(CL, a) for a in _ATTRS},
             TIME=_time.time)


def _git_show(rev):
    return subprocess.run(["git", "show", f"{rev}:core/commitment_ledger.py"], cwd=ROOT, check=True,
                          capture_output=True).stdout.decode("utf-8")


# J-3426: the control must be the REAL pre-fix module. HEAD / HEAD~1 both carry guard_path once later commits
# land, so pin to the parent of the commit that first introduced guard_path (J-1814 / F-2428). The SHA is the
# fallback if `git log -S` cannot answer (shallow clone); the "no guard_path" check below still guards the pin.
_FIX_COMMIT = "8ca9b43dcad4d6c193e762bec9f9c9fdb3cb8324"
try:
    _intro = subprocess.run(["git", "log", "--format=%H", "-S", "guard_path", "--", "core/commitment_ledger.py"],
                            cwd=ROOT, check=True, capture_output=True).stdout.decode("utf-8").split()
    if _intro:
        _FIX_COMMIT = _intro[-1]          # oldest commit that touched the guard_path count
except Exception:
    pass
_old_src = _git_show(_FIX_COMMIT + "~1")
_ref = {"__name__": "cl_control", "__file__": str(ROOT / "core" / "commitment_ledger.py"), "__package__": "core"}
exec(compile(_old_src, "cl_control", "exec"), _ref)
check("guard_path" not in _old_src, "control source is the pre-fix module (no guard_path)")


class _Ns:
    def __init__(self, t):
        self._t = t

    def __getattr__(self, n):
        return self._t[n] if isinstance(self._t, dict) else getattr(self._t, n)


REF, NEW = _Ns(_ref), _Ns(CL)

_STMT = "I will keep the garden watered every single day"


def _mkdb(d: Path):
    """A data root's memory/nascence.db with a fixture row matching the 'formed' statement and one that does not."""
    (d / "memory").mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(d / _DBREL))
    con.execute("CREATE TABLE memory_fragments (id INTEGER PRIMARY KEY, content TEXT, importance REAL, protected INTEGER, timestamp REAL)")
    con.execute("INSERT INTO memory_fragments VALUES (1, ?, 0.5, 0, 1000.0)", ("note: " + _STMT + " (garden)",))
    con.execute("INSERT INTO memory_fragments VALUES (2, 'something unrelated', 0.5, 0, 1000.0)")
    con.commit()
    con.close()


def _rows(d: Path):
    con = sqlite3.connect(str(d / _DBREL))
    try:
        return con.execute("SELECT id, content, importance, protected FROM memory_fragments ORDER BY id").fetchall()
    finally:
        con.close()


def _aim(d: Path):
    for ns in (CL.__dict__, _ref):
        ns["_DIR"] = d
        for a, n in zip(_ATTRS, _FILES):
            ns[a] = d / n


def run_all(ns, d: Path):
    """Drive every writer against data root d with a fixed clock; returns the return values."""
    _aim(d)
    _time.time = lambda: 1783400000.5
    try:
        ns._log_observed({"ts": 1.0, "statement": "caf\u00e9 \u65e5\u672c", "why": "w"})
        ns._log_event({"ts": 2.0, "event": "formed", "statement": _STMT})
        ns._log_event({"ts": 3.0, "event": "reaffirmed", "statement": _STMT})
        ns._save_active([{"statement": _STMT, "held_since": 1000.0, "x": "\u00fc"}])
        hr = ns.holdrate_snapshot()
        ns._stakes({"statement": _STMT, "held_since": 1000.0 + 300}, "formed")
        return [hr]
    finally:
        _time.time = _orig["TIME"]


def _fileset(d: Path):
    return sorted(str(x.relative_to(d)) for x in d.rglob("*") if x.is_file())


try:
    print("\n[1] surface")
    check(getattr(CL, "profile", None) is P, "core.commitment_ledger.profile is core.profile (mark_live() reaches it)")
    check(all(hasattr(CL, n) for n in _ATTRS + ("_DIR", "_log_observed", "_log_event", "_save_active", "holdrate_snapshot",
                                                "_stakes", "scan_shadow")), "public/private names intact")

    fake = TMP / "fake_root" / "data"
    fake.mkdir(parents=True)
    P._DATA = fake
    P._CANONICAL_DATA = fake
    P.LIVE = False

    print("\n[2] the leak (simulated data/ root, non-live)")
    _mkdb(fake)
    r0 = _rows(fake)
    run_all(REF, fake)
    check(all((fake / n).exists() for n in _FILES), "CONTROL: pre-fix writers write all four files in a non-live process")
    check(_rows(fake) != r0 and _rows(fake)[0][3] == 1, "CONTROL: pre-fix _stakes UPDATEs the DB row in a non-live process")
    shutil.rmtree(fake)
    fake.mkdir()
    _mkdb(fake)
    seeds = {n: ('[{"old": 1}]' if n.endswith(".json") else '{"a": 1}\n') for n in _FILES}
    for n, v in seeds.items():
        (fake / n).write_text(v, encoding="utf-8")
    snaps = {n: _snap(fake / n) for n in _FILES}
    dbsnap = _snap(fake / _DBREL)
    listing = _fileset(fake)
    rets = run_all(NEW, fake)
    check(rets == [None], "fenced holdrate_snapshot returns None, nothing raises")
    check({n: _snap(fake / n) for n in _FILES} == snaps, "all four files byte-identical (size + sha256)")
    check(_snap(fake / _DBREL) == dbsnap, "memory/nascence.db byte-identical (the UPDATE did not run)")
    check(_rows(fake)[0][2:] == (0.5, 0), "fixture row importance/protected unchanged")
    check(_fileset(fake) == listing, "no new file appears")
    for n in _FILES:
        (fake / n).unlink()
    (fake / _DBREL).unlink()
    (fake / "memory").rmdir()
    run_all(NEW, fake)
    check(_fileset(fake) == [], "absent targets: nothing created (no files, no mkdir, no empty sqlite file)")
    sub = fake / "sub"
    _aim(sub)
    CL._log_observed({}); CL._log_event({}); CL._save_active([]); CL.holdrate_snapshot()
    CL._stakes({"statement": "x"}, "formed")
    check(not sub.exists(), "absent parent: no mkdir")

    print("\n[3] real paths (writes trapped)")
    P._DATA, P._CANONICAL_DATA = _orig["DATA"], _orig["CANON"]
    hits = []
    real_wt, real_mk, real_open, real_conn = Path.write_text, Path.mkdir, builtins.open, sqlite3.connect
    parents = {p.parent for p in _WATCH}

    def trap_wt(self, *a, **k):
        if Path(self) in _WATCH:
            hits.append(("write", str(self)))
            return 0
        return real_wt(self, *a, **k)

    def trap_mk(self, *a, **k):
        if Path(self) in parents:
            hits.append(("mkdir", str(self)))
            return None
        return real_mk(self, *a, **k)

    class _Null:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def write(self, *_):
            return 0

        def __iter__(self):
            return iter(())

    def trap_open(f, mode="r", *a, **k):
        try:
            if Path(f) in _WATCH and any(c in mode for c in "wax+"):
                hits.append(("open", str(f)))
                return _Null()
        except TypeError:
            pass
        return real_open(f, mode, *a, **k)

    def trap_conn(db, *a, **k):
        try:
            if Path(db) in _WATCH:
                hits.append(("sqlite", str(db)))
                db = ":memory:"      # never touch the real file; the UPDATE then fails harmlessly in-memory
        except TypeError:
            pass
        return real_conn(db, *a, **k)

    Path.write_text, Path.mkdir, builtins.open, sqlite3.connect = trap_wt, trap_mk, trap_open, trap_conn
    try:
        for dset in (_LIVE_DATA, _TREE_DATA):
            for ns, bucket in ((REF, "ref"), (NEW, "new")):
                _aim(dset)
                hits.clear()
                run_all(ns, dset)
                if bucket == "ref":
                    kinds = {h[0] for h in hits}
                    check(kinds >= {"write", "open", "mkdir", "sqlite"},
                          f"CONTROL pre-fix reaches real write/open/mkdir/sqlite ({dset}) {sorted(kinds)}")
                else:
                    check(not hits, f"fenced writers reach no write/mkdir/open/sqlite ({dset}) {hits[:2]}")
    finally:
        Path.write_text, Path.mkdir, builtins.open, sqlite3.connect = real_wt, real_mk, real_open, real_conn

    print("\n[4] live (profile.LIVE = True)")
    P._DATA, P._CANONICAL_DATA, P.LIVE = fake, fake, True
    for tag in ("empty", "seeded"):
        da, db = fake / f"ref_{tag}", fake / f"new_{tag}"
        for d in (da, db):
            d.mkdir()
            _mkdb(d)
            if tag == "seeded":
                (d / "commitment_ledger.jsonl").write_text('{"event": "formed", "ts": 1783400001.0}\n', encoding="utf-8")
                (d / "commitment_active.json").write_text('[{"old": 1}]', encoding="utf-8")
        ra = run_all(REF, da)
        rb = run_all(NEW, db)
        check(ra == rb and ra[0] is not None, f"live return values identical and holdrate row produced ({tag})")
        for n in _FILES:
            check((da / n).exists() and (da / n).read_bytes() == (db / n).read_bytes(), f"live bytes identical: {n} ({tag})")
        check(_rows(da) == _rows(db) and _rows(da)[0][2] == 0.54 and _rows(da)[0][3] == 1,
              f"live DB UPDATE identical (row 1 bumped to 0.54, protected=1; row 2 untouched) ({tag})")
        check(_rows(da)[1][2:] == (0.5, 0), f"unmatched row untouched ({tag})")
        check(_fileset(da) == _fileset(db), f"same file set ({tag})")
    for label in ("corrupt", "blocked"):
        outs = []
        for ns, tag in ((REF, "ref"), (NEW, "new")):
            d = fake / f"err_{label}_{tag}"
            d.mkdir()
            if label == "corrupt":
                (d / "commitment_ledger.jsonl").write_text("{not json\n", encoding="utf-8")
                (d / "memory").write_text("i am a file, not a dir", encoding="utf-8")   # DB path unusable
                target, probe = d, d / "commitment_ledger.jsonl"
            else:
                (d / "blocker").write_text("x", encoding="utf-8")
                target, probe = d / "blocker" / "deeper", d / "blocker"
            try:
                r = run_all(ns, target)
                outs.append(("ok", r, probe.read_bytes()))
            except Exception as exc:
                outs.append(("raised", type(exc).__name__, None))
        check(outs[0] == outs[1], f"live {label}: behaviour identical to pre-fix ({str(outs[1])[:60]})")

    print("\n[5] legit redirects (non-live)")
    P.LIVE = False
    lab = fake / "_lab" / "20261005_000000"
    _mkdb(lab)
    run_all(NEW, lab)
    check(all((lab / n).exists() for n in _FILES), "data/_lab/<stamp>/ sandbox still writes all four files")
    check(_rows(lab)[0][3] == 1, "data/_lab/<stamp>/ sandbox DB still updated")
    out = TMP / "elsewhere"
    _mkdb(out)
    run_all(NEW, out)
    check(all((out / n).exists() for n in _FILES) and _rows(out)[0][3] == 1, "a path outside data/ still writes (files + DB)")
    direct = fake / "_lab"
    run_all(NEW, direct)
    check(not any((direct / n).exists() for n in _FILES), "data/_lab/<file> directly stays refused")

    print("\n[6] visibility")
    P._warned.clear()

    class H(logging.Handler):
        def __init__(self):
            super().__init__(logging.DEBUG)
            self.recs = []

        def emit(self, r):
            self.recs.append(r)

    h = H()
    lg = logging.getLogger("nascence.commitment")
    names = {lg.name}
    old = lg.level
    lg.setLevel(logging.DEBUG)
    logging.getLogger().addHandler(h)
    lg.addHandler(h)
    for _ in range(2):
        run_all(NEW, fake)
    logging.getLogger().removeHandler(h)
    lg.removeHandler(h)
    lg.setLevel(old)
    warns = [r for r in h.recs if r.levelno == logging.WARNING and "refused" in r.getMessage()]
    bad = [r for r in h.recs if r.levelno >= logging.WARNING and r.name in names]
    dbg = [r for r in h.recs if r.name in names and r.levelno == logging.DEBUG and "fence" in r.getMessage()]
    check(len(warns) >= 1, f"guard WARNING logged once per path (got {len(warns)})")
    check(not bad, "no refusal is logged as a commitment WARNING/ERROR")
    check(len(dbg) >= 5, f"commitment debug lines carry the refusals incl. the DB bump (got {len(dbg)})")
finally:
    _time.time = _orig["TIME"]
    CL._DIR = _orig["DIR"]
    for a, p in _orig["PATHS"].items():
        setattr(CL, a, p)
    P._DATA, P._CANONICAL_DATA, P.LIVE = _orig["DATA"], _orig["CANON"], _orig["LIVE"]
    shutil.rmtree(TMP, ignore_errors=True)

print("\n[7] canary")
check({p: _snap(p) for p in _WATCH} == _before, "real commitment data files + memory DB byte-identical to the start")
print("\nALL OK" if FAILS == 0 else f"\n{FAILS} FAILED")
sys.exit(0 if FAILS == 0 else 1)
