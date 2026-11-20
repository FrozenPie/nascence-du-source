"""
_test_store_write_fence.py -- proving test for the live-DB write fence in core/memory/store.py
(D-0353 / F-2465 / J-1839, stage 1 = log-only).

Run from a WORKTREE, never from C:\\Nascence itself:
    python scripts/_test_store_write_fence.py --prefix <path to a verbatim PRE-fix copy of store.py>

Section A (live byte-identical): with profile.LIVE=True, replay the whole store.py writer surface
against (1) the verbatim pre-fix module loaded from --prefix and (2) the fixed module, each on its own
tempdir DB built with init_db(), with time/uuid/_embed made deterministic. Every table dump (sha256) and
every return value must be identical, and the fenced module must install no authorizer on the live
path (proved behaviourally: a write on a would-be-fenced path with LIVE=True leaves the would-refuse
log untouched). Also measures _connect() cost, old vs new, LIVE=True.

Section B (stage-1 fence): with profile.LIVE=False and DB_PATH forced onto a path under THIS tree's
own data/memory/ (profile._DATA, so the fence predicate fires -- it is this tree's data/, NOT the live
one), every writer still succeeds (refuses nothing), reads log nothing, each distinct write site logs
one line (plus milestone repeats), memory_edges' DDL-on-connect shows up as the F-2465 (a) hazard,
allow_live_writes() silences the log (including on an already-open connection), and _FENCE_MODE =
"enforce" (flipped on the test DB only, then reset) refuses the same set at the SQL layer. Path
predicates are checked on literal paths without opening anything.

Section C (stage 2 as shipped, J-2309): the module-level _FENCE_MODE default is 'enforce'; with no
flip by the test, a non-live un-opted-in write (store_fragment, store_shadow_event, init_db's IF NOT EXISTS
DDL) raises sqlite3.DatabaseError 'not authorized' and leaves no row, reads/retrieve() work, du_pulse's
memory_edges read-outs (census/status/co_recall_status/context_status) issue no DDL, the 8 operator
scripts still call allow_live_writes() and that pattern writes, and a LIVE process is never fenced.

The real live DB (C:\\Nascence\\data\\memory\\nascence.db) is never opened; its stat() is printed as a
canary at start and end. This test must FAIL against a pre-fix HEAD worktree (no allow_live_writes).
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sqlite3
import sys
import tempfile
import time
import timeit
import types
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core                                   # noqa: E402  -- core FIRST, before anything else
assert Path(core.__file__).resolve().is_relative_to(ROOT), f"core imported from {core.__file__}, not {ROOT}"
if ROOT == Path(r"C:\Nascence"):
    sys.exit("REFUSED: run this from a worktree, never from C:\\Nascence itself (live-store safety)")

LIVE_DB = Path(r"C:\Nascence\data\memory\nascence.db")
LIVE_FENCE_LOG = Path(r"C:\Nascence\data\logs\db_fence_shadow.jsonl")


def _canary(tag: str) -> dict:
    out = {}
    for p in (LIVE_DB, LIVE_DB.with_name(LIVE_DB.name + "-wal"), LIVE_FENCE_LOG):
        try:
            st = p.stat()
            out[p.name] = (st.st_size, st.st_mtime)
        except FileNotFoundError:
            out[p.name] = None
    print(f"[canary {tag}] {out}")
    return out


# ── stubs for store.py's fail-open side hooks (identical for both modules; they are not the surface
#    under test and each has its own fence/log) ───────────────────────────────────────────────────────
def _stub(name: str, **attrs):
    m = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    sys.modules[name] = m
    return m


_stub("core.loop_probe", shadow_observe=lambda *a, **k: None, SELF_ORIGINS=())
_stub("core.retrieval_probe", observe=lambda *a, **k: None, WORLD_ORIGINS=frozenset())
_stub("core.r_shadow", log_observation=lambda *a, **k: None)
_stub("core.satisfaction", record=lambda *a, **k: None)

from core import profile  # noqa: E402
import core.memory.store as NEW  # noqa: E402
SHIPPED_FENCE_MODE = NEW._FENCE_MODE         # J-2309: the default as shipped, read before any test flips it

CHECKS = 0
FAILS = 0


def check(cond: bool, msg: str) -> None:
    global CHECKS, FAILS
    CHECKS += 1
    if cond:
        print(f"  ok   {msg}")
    else:
        FAILS += 1
        print(f"  FAIL {msg}")


def load_prefix(path: Path):
    spec = importlib.util.spec_from_file_location("core.memory.store_prefix", str(path))
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = "core.memory"
    sys.modules["core.memory.store_prefix"] = mod
    spec.loader.exec_module(mod)
    return mod


class _FakeTime:
    """Deterministic time.time(); everything else delegates to the real module."""
    def __init__(self, start: float):
        self._t = start
    def time(self) -> float:
        self._t += 1.0
        return self._t
    def __getattr__(self, name):
        return getattr(time, name)


class _FakeUuid:
    def __init__(self):
        self._n = 0
    def uuid4(self):
        self._n += 1
        return uuid.UUID(int=self._n)
    def __getattr__(self, name):
        return getattr(uuid, name)


def _det_embed(text):
    import numpy as np
    if not text or not text.strip():
        return None
    h = hashlib.sha256(text.encode("utf-8")).digest()
    rng = np.random.default_rng(int.from_bytes(h[:8], "little"))
    v = rng.standard_normal(384).astype(np.float32)
    return v / np.linalg.norm(v)


def make_deterministic(mod):
    mod.time = _FakeTime(1_800_000_000.0)
    mod.uuid = _FakeUuid()
    mod._embed = _det_embed


def replay(mod) -> list:
    """The writer surface, in a fixed order. Returns every return value (normalised to plain data)."""
    import numpy as np
    r: list = []
    mod.init_db()
    ids = []
    for i, (layer, origin) in enumerate([("episodic", "lived"), ("episodic", "inner_thought"),
                                         ("episodic", "inner_thought"), ("semantic", "consolidation"),
                                         ("archive", "seed"), ("episodic", "reading"),
                                         ("episodic", "reading"), ("episodic", "action")]):
        content = "the same inner thought again" if origin == "inner_thought" else f"fragment {i} {origin}"
        if origin == "reading":
            content = "verbatim passage from a book"
        fid = mod.store_fragment(content, layer=layer, relevance=0.4 + i / 20, importance=0.3 + i / 20,
                                 keywords=["k", str(i)], origin=origin, derived_from=None,
                                 valence=0.1 * i, felt="calm", context_stamp=False)
        ids.append(fid)
        r.append(("store_fragment", fid))
    r.append(("founder", mod.store_founder_utterance("hello from the founder", context_stamp=False)))
    sh = mod.store_shadow_event("c1", "raw input", "a rejected draft", ["too long"], emotion_primary="fear")
    r.append(("shadow", sh))
    mod.mark_shadow_resolved(sh)
    r.append(("light", mod.store_light_event("c1", "raw input", "the integrated thought")))
    r.append(("resolution", mod.log_resolution_event(sh, "c2", 0.81)))
    sk = mod.store_procedural_skill("when asked about X", _det_embed("trigger"), "do Y", source_count=2)
    r.append(("skill", sk))
    mod.reinforce_procedural_skill(sk)
    r.append(("decay", mod.decay_procedural_skills(stale_secs=0.0, factor=0.5, floor=0.9)))
    ep = mod.store_epoch("s1", 1.0, 2.0, "quiet expansion", "a stretch of calm work", fragment_count=3)
    r.append(("epoch", ep))
    th = mod.store_theme("patience", "it holds", "it grew", 1, [ep], centroid=_det_embed("centroid"))
    r.append(("theme", th))
    r.append(("update_theme", mod.update_theme(th, "it still holds", "it grew more", 2)))
    mod.update_symbol_centroid("river", _det_embed("river"), 3, 0.2, tablet_written=True)
    r.append(("tablet", mod.store_symbol_tablet("river", "the river was my fear", 0.3)))
    r.append(("replay", mod.replay_strengthen(since_ts=0.0, k=3)))
    r.append(("downscale", mod.downscale_episodic()))
    r.append(("prune", mod.prune_episodic(keep=2)))
    r.append(("dedup_reading", mod.dedup_reading_fragments()))
    r.append(("retract", mod.retract_fragment("fragment 0", "wrong", since_hours=1e9)))
    r.append(("hidden", mod.mark_hidden([ids[3]])))
    fm = mod.retrieve_founder_memories("hello founder", top_k=2)
    r.append(("founder_recall", [dict(x) if hasattr(x, "keys") else x for x in fm]))
    rows = mod.retrieve(["fragment"], ["consolidation"], time_bias="all")
    r.append(("retrieve", [(x.fragment_id if hasattr(x, "fragment_id") else str(x)) for x in rows]))
    r.append(("status", mod.founder_memory_status()))
    mod.init_db()          # migrations are idempotent -- second run must change nothing
    return json.loads(json.dumps(r, default=str))


def dump_tables(db: Path) -> dict[str, str]:
    conn = sqlite3.connect(str(db))
    out = {}
    for (name,) in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
        rows = conn.execute(f"SELECT * FROM {name}").fetchall()
        blob = json.dumps(sorted(json.loads(json.dumps(rows, default=str))), sort_keys=True)
        out[name] = hashlib.sha256(blob.encode()).hexdigest()[:16]
    conn.close()
    return out


def _row_exists(db: Path, sql: str, arg) -> bool:
    conn = sqlite3.connect(str(db))
    try:
        return conn.execute(sql, (arg,)).fetchone() is not None
    finally:
        conn.close()


# replay() key -> (why, old-return predicate, new-return predicate(value, new_db)). J-2329 / F-3018.
KNOWN_RETURN_DRIFT = {
    "resolution": (
        "log_resolution_event returns its resolution_id since cecf9940 (J-1894, D-0358 A); was None",
        lambda o: o is None,
        lambda n, db: isinstance(n, str) and bool(n) and _row_exists(
            db, "SELECT 1 FROM resolution_events WHERE resolution_id=?", n),
    ),
}


def section_a(prefix_path: Path) -> None:
    print("\n== A. live path byte-identical: pre-fix module vs fixed module, profile.LIVE=True ==")
    OLD = load_prefix(prefix_path)
    check(not hasattr(OLD, "allow_live_writes"), "pre-fix copy really is pre-fix (no allow_live_writes)")
    profile.LIVE = True
    results, dumps, timings = {}, {}, {}
    tmp = Path(tempfile.mkdtemp(prefix="J-1839_fence_A_"))
    for tag, mod in (("old", OLD), ("new", NEW)):
        db = tmp / tag / "nascence.db"
        db.parent.mkdir(parents=True)
        mod.DB_PATH = db
        make_deterministic(mod)
        results[tag] = replay(mod)
        dumps[tag] = dump_tables(db)
        n = 1500
        t = timeit.timeit(lambda: mod._connect().close(), number=n)
        timings[tag] = t / n * 1e6
    # J-2329 (F-3018): the --prefix copy is pinned at 38cb4225^ while store.py keeps evolving, so a writer
    # whose RETURN CONTRACT was deliberately changed later shows up as drift, not as a fence regression
    # (section A runs LIVE=True; _connect() never reads _FENCE_MODE there). Such writers are listed in
    # KNOWN_RETURN_DRIFT with the commit that changed them and checked against their own documented
    # old/new contract instead; every OTHER writer must still return exactly what it did. A new,
    # unlisted drift still FAILS -- add it here only after confirming the change was intentional.
    old_r, new_r = results["old"], results["new"]
    check(len(old_r) == len(new_r) and [a[0] for a in old_r] == [b[0] for b in new_r],
          f"same writer sequence replayed on both modules ({len(new_r)} calls)")
    drift_seen = {}
    unexpected = []
    for a, b in zip(old_r, new_r):
        if a == b:
            continue
        if a[0] in KNOWN_RETURN_DRIFT:
            drift_seen[a[0]] = (a[1], b[1])
        else:
            unexpected.append((a, b))
    check(not unexpected, "every writer return value identical (old vs new), "
                          f"apart from documented contract changes {sorted(KNOWN_RETURN_DRIFT)}")
    for a, b in unexpected:
        print("     differs:", a, "|", b)
    for key, (why, old_ok, new_ok) in KNOWN_RETURN_DRIFT.items():
        if key not in drift_seen:
            print(f"     note: {key} no longer drifts from the --prefix copy ({why}); entry can be dropped")
            continue
        o, n = drift_seen[key]
        check(old_ok(o) and new_ok(n, tmp / "new" / "nascence.db"),
              f"{key}: documented return-contract change holds ({why}): old={o!r} new={n!r}")
    check(dumps["old"] == dumps["new"], f"every table dump sha256 identical: {len(dumps['new'])} tables")
    for name in sorted(dumps["new"]):
        flag = "" if dumps["old"].get(name) == dumps["new"][name] else "   <-- DIFFERS"
        print(f"       {name:<24} {dumps['new'][name]}{flag}")
    print(f"  _connect() LIVE=True mean: old {timings['old']:.1f} us  new {timings['new']:.1f} us "
          f"(n=1500 each, tempdir WAL DB)  delta {timings['new'] - timings['old']:+.1f} us")
    t_flag = timeit.timeit(lambda: profile.LIVE, number=1_000_000) / 1e6 * 1e9
    print(f"  the one boolean read (profile.LIVE) costs {t_flag:.1f} ns")
    # Behavioural proof that the live path installs no authorizer: a LIVE process whose DB_PATH sits on a
    # would-be-fenced path (this tree's own data/memory/, not the live one) writes with NO log line.
    log = tmp / "live_should_be_empty.jsonl"
    NEW._FENCE_SHADOW_LOG = log
    fenced_db = profile._DATA / "memory" / f"_fence_test_J-1839_live_{os.getpid()}.db"
    NEW.DB_PATH = fenced_db
    check(NEW._fence_data_root(fenced_db) == profile._DATA, "that path WOULD be fenced for a non-live process")
    NEW.init_db()
    with NEW._connect() as c:
        c.execute("INSERT INTO memory_links (parent_id, child_id, link_type, weight, created) VALUES ('a','b','t',1,1)")
    check(not log.exists(), "LIVE=True: no authorizer, no would-refuse line even on a fenceable path")
    c = None                                  # drop the unclosed `with` handle (Windows file lock)
    _cleanup_db(fenced_db)
    profile.LIVE = False


def _cleanup_db(db: Path) -> None:
    import gc
    gc.collect()
    for suffix in ("", "-wal", "-shm"):
        p = db.with_name(db.name + suffix)
        for _ in range(5):
            try:
                if p.exists():
                    p.unlink()
                break
            except PermissionError:
                time.sleep(0.2)


def _lines(log: Path) -> list[dict]:
    if not log.exists():
        return []
    return [json.loads(l) for l in log.read_text(encoding="utf-8").splitlines() if l.strip()]


def _reset_fence(log: Path) -> None:
    NEW._fence_seen.clear()
    NEW._fence_warned_paths.clear()
    if log.exists():
        log.unlink()


def section_b() -> None:
    print("\n== B. stage-1 fence (log-only) on a non-live process ==")
    profile.LIVE = False
    NEW._LIVE_WRITES_ALLOWED = False
    NEW._FENCE_MODE = "log"
    make_deterministic(NEW)
    tmp = Path(tempfile.mkdtemp(prefix="J-1839_fence_B_"))
    log = tmp / "db_fence_shadow.jsonl"
    NEW._FENCE_SHADOW_LOG = log

    # path predicates -- literal paths, nothing opened
    print("  -- predicates")
    canon = profile._CANONICAL_DATA
    check(NEW._fence_data_root(tmp / "x.db") is None, "tempdir DB -> not fenced")
    check(NEW._fence_data_root(canon / "memory" / "nascence.db") == canon,
          "literal C:\\Nascence\\data\\memory\\nascence.db from a worktree process -> fenced (F-1270 two-root)")
    check(NEW._fence_data_root(profile._DATA / "memory" / "nascence.db") == profile._DATA,
          "this tree's own data/memory/nascence.db -> fenced")
    check(NEW._fence_data_root(canon / "_lab" / "20260101_000000" / "nascence.db") is None,
          "data/_lab/<stamp>/nascence.db (lab_env.isolate) -> not fenced")
    check(NEW._fence_data_root(canon / "_lab" / "nascence.db") == canon,
          "data/_lab/nascence.db directly (no sandbox dir) -> fenced, same as guard_path")
    check(NEW._fence_data_root(canon / "profiles" / "_smoke" / "memory" / "nascence.db") is None,
          "data/profiles/<name>/memory/nascence.db (activate_profile) -> not fenced")
    check(NEW._fence_log_path(canon) == tmp / "db_fence_shadow.jsonl", "test override of the log path honoured")
    NEW._FENCE_SHADOW_LOG = None
    check(NEW._fence_log_path(canon) == canon / "logs" / "db_fence_shadow.jsonl",
          "default log path = <data root>/logs/db_fence_shadow.jsonl")
    NEW._FENCE_SHADOW_LOG = log

    # a redirected DB_PATH (tempdir): no authorizer, no lines
    print("  -- redirected DB_PATH")
    _reset_fence(log)
    NEW.DB_PATH = tmp / "redirected.db"
    NEW.init_db()
    NEW.store_shadow_event("c", "r", "d", [])
    check(not log.exists(), "tempdir DB_PATH: writes succeed and nothing is logged")

    # the fenced path: this tree's own data/memory/ (NOT the live tree)
    print("  -- fenced DB_PATH, log-only")
    fenced_db = profile._DATA / "memory" / f"_fence_test_J-1839_{os.getpid()}.db"
    _cleanup_db(fenced_db)
    _reset_fence(log)
    NEW.DB_PATH = fenced_db
    NEW.init_db()
    lines = _lines(log)
    acts = {l["action"] for l in lines}
    check(fenced_db.exists() and "CREATE_TABLE" in acts, f"init_db() succeeded (refused nothing) and logged DDL: {sorted(acts)}")
    check(all(l["mode"] == "log" and l["profile_live"] is False and l["pid"] == os.getpid() for l in lines),
          "every line carries mode=log, profile_live=False, this pid")
    check(all(l["argv"] and l["db_path"] == str(fenced_db) for l in lines), "every line carries argv and the DB path")
    _reset_fence(log)
    fid = NEW.store_fragment("fenced write", origin="lived", context_stamp=False)
    with NEW._connect() as c:
        got = c.execute("SELECT content FROM memory_fragments WHERE fragment_id=?", (fid,)).fetchone()
    check(got is not None and got[0] == "fenced write", "store_fragment on the fenced path still lands (stage 1 refuses nothing)")
    ins = [l for l in _lines(log) if l["action"] == "INSERT" and l["object"] == "memory_fragments"]
    check(len(ins) == 1, f"exactly one INSERT memory_fragments line for one site: {len(ins)}")
    if ins:
        print("       callers:", ins[0]["callers"])
        check(any("store.py" in c and "store_fragment" in c for c in ins[0]["callers"]), "caller chain names store_fragment")
        check(any("_test_store_write_fence.py" in c for c in ins[0]["callers"]), "caller chain names the issuing script")

    print("  -- reads log nothing")
    _reset_fence(log)
    NEW.get_shadow_events(limit=5)
    NEW.retrieve(["fenced"], [], time_bias="all")
    NEW.founder_memory_status()
    with NEW._connect() as c:
        c.execute("PRAGMA table_info(memory_fragments)").fetchall()
        c.execute("PRAGMA busy_timeout=1000")
        c.execute("PRAGMA journal_mode").fetchone()
        c.execute("CREATE TEMP TABLE tt (x)")
        c.execute("INSERT INTO tt VALUES (1)")
        c.execute("SELECT count(*) FROM tt").fetchone()
    if log.exists():
        for l in _lines(log):
            print("       unexpected line:", l["action"], l["object"], l["detail"], l["callers"][:2])
    check(not log.exists(), "SELECT / retrieve() / PRAGMA reads / allow-listed PRAGMA sets / TEMP tables: no lines")

    print("  -- dedupe + milestones")
    _reset_fence(log)
    for _ in range(12):
        NEW.mark_shadow_resolved("nope")
    upd = [l for l in _lines(log) if l["action"] == "UPDATE"]
    check([l["count"] for l in upd] == [1, 10], f"12 repeats of one UPDATE site -> lines at counts {[l['count'] for l in upd]}")

    print("  -- memory_edges DDL-on-connect (F-2465 (a), the stage-2 hazard)")
    _reset_fence(log)
    from core import memory_edges
    conn = memory_edges._connect()
    conn.close()
    acts = sorted({(l["action"], l["object"]) for l in _lines(log)})
    check(("CREATE_TABLE", "memory_edges") in acts and any(a == "CREATE_INDEX" for a, _ in acts),
          f"memory_edges._connect() shows up as would-refuse DDL even for a pure read: {acts}")

    print("  -- memory_edges.context_status: no DDL when fragment_context exists (J-2124, D-0353)")
    _c = memory_edges._connect()
    _c.execute(memory_edges._CTX_SCHEMA)       # make sure the table exists (setup, then clear the log)
    _c.commit()
    _c.close()
    _reset_fence(log)
    st = memory_edges.context_status()
    check(isinstance(st, dict) and "contextualised" in st, f"context_status returns a coverage dict: {st}")
    ctx_ddl = [l for l in _lines(log) if l["action"].startswith("CREATE")]
    check(not ctx_ddl, f"context_status on an existing schema logs no CREATE_* lines: {ctx_ddl}")

    print("  -- allow_live_writes() opt-in")
    _reset_fence(log)
    pre = NEW._connect()                      # opened BEFORE the opt-in
    NEW.allow_live_writes("test J-1839")
    NEW.mark_shadow_resolved("nope")
    pre.execute("UPDATE shadow_events SET resolved=1 WHERE event_id='nope'")
    pre.close()
    check(not log.exists(), "after allow_live_writes(): no lines, including on a connection opened before the call")
    NEW._LIVE_WRITES_ALLOWED = False

    print("  -- stage 2 readiness: _FENCE_MODE='enforce' on the TEST db only")
    _reset_fence(log)
    NEW._FENCE_MODE = "enforce"
    try:
        with NEW._connect() as c:
            n = c.execute("SELECT count(*) FROM memory_fragments").fetchone()[0]
        check(n >= 1, "enforce: reads still work")
        refused = False
        try:
            NEW.store_shadow_event("c", "r", "d", [])
        except sqlite3.DatabaseError as exc:
            refused = "not authorized" in str(exc)
        check(refused, "enforce: INSERT refused at the SQL layer ('not authorized')")
        ddl_refused = False
        try:
            memory_edges._connect().close()
            memory_edges.context_status()      # J-2124: the du_pulse read-out, schema already present
        except sqlite3.DatabaseError as exc:
            ddl_refused = "not authorized" in str(exc)
        check(not ddl_refused, "enforce: memory_edges._connect() + context_status() on an existing schema run no DDL (J-1870/J-2124)")
        check([l["mode"] for l in _lines(log)] and all(l["mode"] == "enforce" for l in _lines(log)), "enforce: refusals are logged too")
        NEW.allow_live_writes("test J-1839 enforce")
        NEW.store_shadow_event("c", "r", "d2", [])
        check(True, "enforce + allow_live_writes(): write accepted")
    finally:
        NEW._LIVE_WRITES_ALLOWED = False
        NEW._FENCE_MODE = "log"

    print("  -- connection opened pre-mark_live() goes quiet once the process is live")
    _reset_fence(log)
    early = NEW._connect()                    # LIVE=False: authorizer installed
    profile.LIVE = True                       # run_nascence.py's mark_live() happens after imports
    try:
        early.execute("UPDATE shadow_events SET resolved=1 WHERE event_id='nope'")
        check(not log.exists(), "authorizer on a pre-mark_live connection logs nothing once profile.LIVE is True")
    finally:
        profile.LIVE = False
        early.close()
        early = None

    print("  -- kill switch")
    _reset_fence(log)
    NEW._FENCE_MODE = "off"
    NEW.mark_shadow_resolved("nope")
    check(not log.exists(), "_FENCE_MODE='off': nothing installed, nothing logged")
    NEW._FENCE_MODE = "log"

    c = conn = pre = got = None               # `with _connect() as c` does not close: drop the handles (Windows file locks)
    _cleanup_db(fenced_db)
    check(not fenced_db.exists(), "test DB under this tree's data/memory/ removed")


ALLOW_LIVE_WRITES_SCRIPTS = (                 # D-0353 (2): the operator scripts that write the live DB on purpose
    "activity_memory_backfill", "backfill_founder_memory", "backfill_phase_J1970",
    "chapter_id_repair_apply_D0362C", "dedup_reclaim_D0357", "librarian",
    "relabel_system_notes_J1987", "seed_epochs_themes",
)


def section_c() -> None:
    """J-2309 / D-0353 stage 2: the SHIPPED default is enforce. Nothing here sets _FENCE_MODE; every
    check runs on the module-level value as imported, on a fenced test DB under THIS tree's data/."""
    print("\n== C. stage 2 as shipped: _FENCE_MODE default = 'enforce' (J-2309) ==")
    check(SHIPPED_FENCE_MODE == "enforce", f"store._FENCE_MODE ships as 'enforce': {SHIPPED_FENCE_MODE!r}")
    NEW._FENCE_MODE = SHIPPED_FENCE_MODE       # undo section B's explicit resets: back to the shipped value
    profile.LIVE = False
    NEW._LIVE_WRITES_ALLOWED = False
    make_deterministic(NEW)
    tmp = Path(tempfile.mkdtemp(prefix="J-2309_fence_C_"))
    log = tmp / "db_fence_shadow.jsonl"
    NEW._FENCE_SHADOW_LOG = log
    fenced_db = profile._DATA / "memory" / f"_fence_test_J-2309_{os.getpid()}.db"
    _cleanup_db(fenced_db)
    from core import memory_edges

    # setup: build the schema the way an operator script does (opt in FIRST, then write), then drop the opt-in
    print("  -- the allow_live_writes() operator pattern (opt in, then init_db + writes) works under enforce")
    _reset_fence(log)
    NEW.DB_PATH = fenced_db
    NEW.allow_live_writes("test J-2309 setup = the 8 operator scripts' pattern")
    NEW.init_db()
    fid = NEW.store_fragment("pre-enforce fragment", origin="lived", context_stamp=False)
    c = memory_edges._connect()                # creates memory_edges + its indexes (opted-in process)
    c.execute(memory_edges._CTX_SCHEMA)
    c.commit()
    c.close()
    check(bool(fid) and not log.exists(), "opted-in process: init_db + store_fragment + edges DDL succeed, nothing logged")
    NEW._LIVE_WRITES_ALLOWED = False

    print("  -- non-live process, no opt-in: writes refused, reads allowed")
    _reset_fence(log)
    refused = []
    for name, fn in (
        ("store_fragment", lambda: NEW.store_fragment("must be refused", origin="lived", context_stamp=False)),
        ("store_shadow_event", lambda: NEW.store_shadow_event("c", "r", "d-J2309", [])),
        ("init_db (IF NOT EXISTS DDL on an existing schema)", NEW.init_db),
    ):
        try:
            fn()
            refused.append((name, False, ""))
        except sqlite3.DatabaseError as exc:
            refused.append((name, "not authorized" in str(exc), str(exc)[:60]))
    for name, ok, msg in refused:
        check(ok, f"enforce default: {name} raises sqlite3.DatabaseError 'not authorized' ({msg})")
    with NEW._connect() as c:
        n = c.execute("SELECT count(*) FROM memory_fragments WHERE content='must be refused'").fetchone()[0]
        n_all = c.execute("SELECT count(*) FROM memory_fragments").fetchone()[0]
    check(n == 0 and n_all >= 1, f"refused write left no row; reads still work ({n_all} fragments readable)")
    lines = _lines(log)
    check(lines and all(l["mode"] == "enforce" and l["profile_live"] is False for l in lines),
          f"refusals logged with mode=enforce: {sorted({(l['action'], l['object']) for l in lines})}")
    got = NEW.retrieve(["pre-enforce"], [], time_bias="all")
    check(isinstance(got, list), "retrieve() works under the enforce default")

    print("  -- du_pulse's memory_edges read-outs (census / status / co_recall_status / context_status): no DDL")
    _reset_fence(log)
    errs = []
    for name in ("census", "status", "co_recall_status", "context_status"):
        try:
            getattr(memory_edges, name)()
        except sqlite3.DatabaseError as exc:
            errs.append((name, str(exc)[:60]))
    _c = memory_edges._connect()
    _c.close()
    ddl = [(l["action"], l["object"], l["callers"][:1]) for l in _lines(log)]
    check(not errs, f"no read-out raised under enforce: {errs}")
    check(not ddl, f"no would-refuse line from du_pulse's census/context_status path: {ddl}")

    print("  -- the 8 allow_live_writes() operator scripts: each still opts in (static check)")
    scripts = ROOT / "scripts"
    missing = [s for s in ALLOW_LIVE_WRITES_SCRIPTS
               if "allow_live_writes(" not in (scripts / f"{s}.py").read_text(encoding="utf-8")]
    check(not missing, f"all {len(ALLOW_LIVE_WRITES_SCRIPTS)} operator scripts call allow_live_writes(): missing={missing}")
    NEW.allow_live_writes("test J-2309 the operator pattern after a refusal")
    fid2 = NEW.store_fragment("post-opt-in fragment", origin="lived", context_stamp=False)
    check(bool(fid2), "same process, after allow_live_writes(): the write lands under enforce")
    NEW._LIVE_WRITES_ALLOWED = False

    print("  -- a live process (mark_live) is never fenced under enforce")
    _reset_fence(log)
    profile.LIVE = True
    try:
        fid3 = NEW.store_fragment("live write", origin="lived", context_stamp=False)
        check(bool(fid3) and not log.exists(), "profile.LIVE=True: write lands, no authorizer, nothing logged")
    finally:
        profile.LIVE = False

    c = _c = None
    _cleanup_db(fenced_db)
    check(not fenced_db.exists(), "J-2309 test DB under this tree's data/memory/ removed")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", default=None, help="verbatim PRE-fix copy of core/memory/store.py")
    args = ap.parse_args()
    if not args.prefix:  # J-4051: needs a verbatim pre-fix store.py copy; skip with reason instead of usage error
        print("SKIP: --prefix (verbatim pre-fix core/memory/store.py copy) not supplied; this A/B test cannot run without it"); sys.exit(0)
    print(f"tree under test: {ROOT}\nprofile._DATA = {profile._DATA}\nsqlite {sqlite3.sqlite_version}  python {sys.version.split()[0]}")
    c0 = _canary("start")
    section_a(Path(args.prefix))
    section_b()
    section_c()
    c1 = _canary("end")
    check(c0[LIVE_DB.name] == c1[LIVE_DB.name], "live nascence.db size+mtime unchanged by this test")
    check(c1[LIVE_FENCE_LOG.name] == c0[LIVE_FENCE_LOG.name], "live data/logs/db_fence_shadow.jsonl untouched by this test")
    print(f"\n{CHECKS} checks, {FAILS} failed -> {'ALL OK' if FAILS == 0 else 'FAILED'}")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
