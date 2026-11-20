"""
_test_retrieve_chapter_pushdown.py -- proving test for J-1842 / F-2475: the `chapter_id` skip in
core/memory/store.py retrieve() moved from a post-fetch Python loop into the SQL WHERE clause (plus the
partial index idx_retrieve_pool). Acceptance bar: ZERO change to what retrieve() returns.

Run from a WORKTREE, never from C:\\Nascence itself:
    python scripts/_test_retrieve_chapter_pushdown.py --prefix <verbatim PRE-fix store.py> \
        [--db <COPY of the live nascence.db>] [--probe-log <retrieval_probe_log.jsonl>] [--n 60]

Section A (synthetic, always runs): a tempdir DB with chapter_id NULL / '' / 'x' rows, cold, hidden rows,
all four layers; retrieve() OLD (the --prefix module) vs NEW over several queries/time_bias values must
return identical fragment ids, in the same order, with the same relevance. The '' row (the one place a
naive `chapter_id IS NULL` would diverge from Python truthiness) must be present in both. Also checks the
index is created by init_db() and that the planner uses it.

Section B (--db given): the same old-vs-new comparison over N real queries (heads sampled from the live
retrieval probe log, which is only READ) against the COPY of the real DB, with the real embedder, before
and after init_db() adds the index on the copy; plus before/after sql-phase timings straight from the
module's own latency-probe hook.

The live DB is never opened: it is only ever stat()ed (canary) -- Section B takes a --db copy.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import random
import sqlite3
import statistics
import sys
import tempfile
import time
import uuid
from pathlib import Path

import numpy as np

TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TREE))

# import core FIRST (live-store safety rule), prove it is THIS tree's core
import core
from core.memory import store as NEW

_REAL_EMBED = NEW._embed   # Section A swaps in a deterministic fake embedder; Section B needs the real one back

assert Path(core.__file__).resolve().is_relative_to(TREE), f"core resolved outside tree under test: {core.__file__}"

LIVE_DB = Path(r"C:\Nascence\data\memory\nascence.db")

_fails = 0


def check(ok: bool, msg: str) -> None:
    global _fails
    print(("  PASS  " if ok else "  FAIL  ") + msg)
    if not ok:
        _fails += 1


def load_prefix(path: Path):
    spec = importlib.util.spec_from_file_location("core.memory.store_prefix", str(path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["core.memory.store_prefix"] = mod
    spec.loader.exec_module(mod)
    return mod


def _det_embed_factory(dim: int = 384):
    def _embed(text):
        if not text or not text.strip():
            return None
        rs = np.random.RandomState(abs(hash_str(text)) % (2 ** 31))
        v = rs.randn(dim).astype(np.float32)
        return v / np.linalg.norm(v)
    return _embed


def hash_str(s: str) -> int:
    h = 1469598103934665603
    for ch in s.encode("utf-8"):
        h = ((h ^ ch) * 1099511628211) % (2 ** 63)
    return h


class Capture:
    """Stands in for the observe-only side channels so nothing is written outside the tempdir."""
    def __init__(self):
        self.latency: list[tuple] = []
        self.rshadow_pool_sizes: list[int] = []
        self.rp_recent_world: list[list[str]] = []


CUR: Capture | None = None   # which Capture the shared (module-level) observers should record into


def patch_side_channels(mod, cap: Capture):
    mod._log_retrieve_latency = lambda rows_fetched, ep_n, ms_sql, ms_score: cap.latency.append(
        (rows_fetched, ep_n, ms_sql, ms_score))
    from core import retrieval_probe as rp, r_shadow as rs
    # retrieval_probe / r_shadow are ONE shared module each (both OLD and NEW import the same ones), so they
    # are patched to record into whichever Capture CUR points at, set by the caller around each retrieve().
    rp.observe = lambda q, pool, sel, recent_world, *a, **k: CUR.rp_recent_world.append(
        [r["fragment_id"] for r in recent_world])
    rs.log_observation = lambda trigger, results, pool=None, now_ts=None: CUR.rshadow_pool_sizes.append(
        len(pool) if pool is not None else -1)


def sig(frags):
    return [(f.fragment_id, round(float(f.relevance), 9), f.layer, f.origin) for f in frags]


def sig_ids(frags):
    return [f.fragment_id for f in frags]


def compare(OLD, NEW_, queries, label, capo, capn, rel_tol=1e-4):
    n_same = n_total = 0
    diffs = []
    for (ek, sk, tb, q) in queries:
        capo.latency.clear(); capn.latency.clear()
        global CUR
        CUR = capo
        a = OLD.retrieve(ek, sk, time_bias=tb, limit=8, query_text=q)
        CUR = capn
        b = NEW_.retrieve(ek, sk, time_bias=tb, limit=8, query_text=q)
        n_total += 1
        same_ids = sig_ids(a) == sig_ids(b)
        # relevance: recency terms read time.time() so two calls ms apart differ at ~1e-9; allow tiny tolerance
        same_rel = same_ids and all(abs(x.relevance - y.relevance) <= rel_tol for x, y in zip(a, b))
        if same_ids and same_rel:
            n_same += 1
        else:
            diffs.append((q[:60], tb, sig_ids(a), sig_ids(b)))
    check(n_same == n_total, f"{label}: {n_same}/{n_total} queries return identical ids, order and relevance")
    for d in diffs[:5]:
        print("      DIFF", d)


# ---------------------------------------------------------------- Section A
def section_a(prefix: Path) -> None:
    print("== Section A: synthetic DB, OLD (prefix) vs NEW ==")
    tmp = Path(tempfile.mkdtemp(prefix="J-1842_pushdown_A_"))
    OLD = load_prefix(prefix)
    capo, capn = Capture(), Capture()
    emb = _det_embed_factory()
    for m in (OLD, NEW):
        m.DB_PATH = tmp / "a.db"
        m._embed = emb
    patch_side_channels(OLD, capo)
    patch_side_channels(NEW, capn)
    NEW.init_db()

    now = time.time()
    rows = []
    rs = random.Random(1842)
    layers = ["archive", "semantic", "episodic", "episodic", "working"]
    states = ["null"] * 6 + ["empty"] * 1 + ["chap"] * 4
    ids_by_state: dict[str, list[str]] = {"null": [], "empty": [], "chap": [], "cold": [], "hidden": []}
    with sqlite3.connect(tmp / "a.db") as c:
        c.row_factory = sqlite3.Row
        cols = [r["name"] for r in c.execute("PRAGMA table_info(memory_fragments)")]
        assert "chapter_id" in cols and "cold" in cols and "temp" in cols
        for i in range(400):
            fid = f"f{i:04d}"
            st = rs.choice(states)
            chap = None if st == "null" else ("" if st == "empty" else f"chap{i % 7}")
            cold = 1 if rs.random() < 0.10 else 0
            temp = "hidden" if rs.random() < 0.05 else "warm"
            text = f"memory {i} about {rs.choice(['river','garden','Travis','sleep','dream','book','cat','music'])} {rs.random():.6f}"
            blob = emb(text).tobytes()
            origin = rs.choice(["lived", "reading", "thermal", "study", "world"])
            c.execute(
                """INSERT INTO memory_fragments (fragment_id, content, layer, relevance, timestamp, embedding,
                   origin, chapter_id, cold, temp, importance) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (fid, text, rs.choice(layers), 0.5, now - rs.random() * 86400 * 60, blob, origin, chap, cold,
                 temp, rs.random()))
            if cold:
                ids_by_state["cold"].append(fid)
            elif temp == "hidden":
                ids_by_state["hidden"].append(fid)
            else:
                ids_by_state[st if st != "chap" else "chap"].append(fid)
        c.commit()
    print(f"  rows by state: { {k: len(v) for k, v in ids_by_state.items()} }")
    check(len(ids_by_state["empty"]) > 0 and len(ids_by_state["chap"]) > 0, "fixture has '' and chaptered rows")

    qs = []
    for tb in ("recent", "distant", "all"):
        for q in ["river", "what did Travis say about sleep", "dream of a garden", "book", "cat music", "zzz unrelated"]:
            qs.append(([q], [], tb, q))
    compare(OLD, NEW, qs, "synthetic", capo, capn)

    # the pool NEW fetches is exactly the Python-surviving subset of OLD's pool, same order
    with sqlite3.connect(tmp / "a.db") as c:
        c.row_factory = sqlite3.Row
        old_rows = c.execute("SELECT * FROM memory_fragments WHERE cold = 0 AND temp != 'hidden'").fetchall()
        old_py = [r["fragment_id"] for r in old_rows if not r["chapter_id"]]
        new_sql = [r["fragment_id"] for r in c.execute(
            "SELECT * FROM memory_fragments WHERE cold = 0 AND temp != 'hidden' "
            "AND (chapter_id IS NULL OR chapter_id = '')").fetchall()]
        check(old_py == new_sql, f"pool ids+order identical (Python skip {len(old_py)} == SQL filter {len(new_sql)})")
        check(any(r["chapter_id"] == "" for r in old_rows) and
              set(ids_by_state["empty"]) <= set(new_sql),
              "'' chapter_id rows survive the SQL filter exactly as they survived the Python skip")
        naive = {r[0] for r in c.execute("SELECT fragment_id FROM memory_fragments WHERE cold = 0 AND temp != 'hidden' "
                                         "AND chapter_id IS NULL")}
        check(len(naive) < len(new_sql), "(control) a naive `chapter_id IS NULL` filter WOULD have diverged on the '' rows")
        idx = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_retrieve_pool'")]
        check(idx == ["idx_retrieve_pool"], "init_db() created idx_retrieve_pool")
        plan = c.execute("EXPLAIN QUERY PLAN SELECT * FROM memory_fragments WHERE cold = 0 AND temp != 'hidden' "
                         "AND (chapter_id IS NULL OR chapter_id = '')").fetchall()
        check(any("idx_retrieve_pool" in str(tuple(p)) for p in plan), f"planner uses the partial index: {[p[3] for p in plan]}")
        NEW.init_db()  # idempotent
        check(True, "init_db() is idempotent with the index present")

    NEW._embed = _REAL_EMBED

    # observe-only side channels: still called, now with the eligible pool
    check(len(capn.rshadow_pool_sizes) > 0 and len(capo.rshadow_pool_sizes) > 0, "r_shadow + retrieval_probe observers still fire")
    check(all(n < o for n, o in zip(capn.rshadow_pool_sizes, capo.rshadow_pool_sizes)),
          "observer pool (all_rows) is now the retrieve-eligible subset (documented discontinuity)")


# ---------------------------------------------------------------- Section B
def section_b(prefix: Path, db: Path, probe_log: Path, n: int) -> None:
    print("== Section B: COPY of the real DB, real embedder, real query heads ==")
    assert db.resolve() != LIVE_DB.resolve(), "refusing to run against the live DB path -- pass a COPY"
    live_stat = LIVE_DB.stat() if LIVE_DB.exists() else None
    OLD = load_prefix(prefix)
    capo, capn = Capture(), Capture()
    for m in (OLD, NEW):
        m.DB_PATH = db
    patch_side_channels(OLD, capo)
    patch_side_channels(NEW, capn)

    heads = []
    for line in probe_log.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            h = json.loads(line).get("query_head")
        except Exception:
            continue
        if h and h.strip():
            heads.append(h)
    heads = list(dict.fromkeys(heads))
    rs = random.Random(1842)
    sample = rs.sample(heads, min(n, len(heads)))
    tbs = ["recent", "distant", "all"]
    qs = [([], [], tbs[i % 3], h) for i, h in enumerate(sample)]
    print(f"  {len(qs)} distinct real query heads, time_bias cycled over {tbs}")

    # warm the OS cache + embedder, then timings: alternate OLD/NEW per query so cache state is shared
    with sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True) as c:
        has_idx = bool(c.execute("SELECT 1 FROM sqlite_master WHERE name='idx_retrieve_pool'").fetchall())
    print(f"  idx_retrieve_pool present in the copy at start: {has_idx}")

    # per-query latency collected inside this wrapper (compare() clears latency per query)
    all_o, all_n = [], []

    def compare_collect(OLD_, NEW__, queries, label, co, cn, rel_tol=1e-4):
        n_same = n_total = 0
        diffs = []
        for (ek, sk, tb, q) in queries:
            global CUR
            CUR = co
            a = OLD_.retrieve(ek, sk, time_bias=tb, limit=8, query_text=q)
            CUR = cn
            b = NEW__.retrieve(ek, sk, time_bias=tb, limit=8, query_text=q)
            all_o.append(co.latency[-1][2]); all_n.append(cn.latency[-1][2])
            n_total += 1
            ok = sig_ids(a) == sig_ids(b) and all(abs(x.relevance - y.relevance) <= rel_tol for x, y in zip(a, b))
            n_same += ok
            if not ok:
                diffs.append((q[:60], tb, sig_ids(a), sig_ids(b)))
        check(n_same == n_total, f"{label}: {n_same}/{n_total} real queries identical ids/order/relevance")
        for d in diffs[:5]:
            print("      DIFF", d)

    compare_collect(OLD, NEW, qs, "real DB copy, NO index (filter only)", capo, capn)
    f_o, f_n = statistics.median(all_o), statistics.median(all_n)
    print(f"  [no index]   sql-phase ms: OLD median {f_o:.0f}  NEW median {f_n:.0f}  ({100 * (1 - f_n / f_o):.0f}% faster)")

    print("  -- running NEW.init_db() on the COPY (adds idx_retrieve_pool, runs every boot-time migration) --")
    t = time.perf_counter()
    NEW.init_db()
    print(f"     init_db on copy: {time.perf_counter() - t:.1f}s")
    all_o.clear(); all_n.clear()
    compare_collect(OLD, NEW, qs, "real DB copy, WITH idx_retrieve_pool", capo, capn)
    i_o, i_n = statistics.median(all_o), statistics.median(all_n)
    print(f"  [with index] sql-phase ms: OLD median {i_o:.0f}  NEW median {i_n:.0f}  ({100 * (1 - i_n / i_o):.0f}% faster)")
    print(f"  rows fetched per retrieve: OLD {capo.latency[-1][0]}  NEW {capn.latency[-1][0]}")

    if live_stat is not None:
        s2 = LIVE_DB.stat()
        check((s2.st_size, s2.st_mtime_ns) == (live_stat.st_size, live_stat.st_mtime_ns), "live DB stat() unchanged (canary)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", default=None, help="verbatim PRE-fix copy of core/memory/store.py")
    ap.add_argument("--db", help="a COPY of the real nascence.db (never the live path)")
    ap.add_argument("--probe-log", help="live retrieval_probe_log.jsonl (read only) for real query heads")
    ap.add_argument("--n", type=int, default=60)
    args = ap.parse_args()
    if not args.prefix:  # J-4051: needs a verbatim pre-fix store.py copy; skip with reason instead of usage error
        print("SKIP: --prefix (verbatim pre-fix core/memory/store.py copy) not supplied; this A/B test cannot run without it"); sys.exit(0)
    print("live DB canary at start:", (LIVE_DB.stat().st_size, LIVE_DB.stat().st_mtime_ns) if LIVE_DB.exists() else None)
    section_a(Path(args.prefix))
    if args.db:
        section_b(Path(args.prefix), Path(args.db), Path(args.probe_log), args.n)
    print("live DB canary at end:  ", (LIVE_DB.stat().st_size, LIVE_DB.stat().st_mtime_ns) if LIVE_DB.exists() else None)
    print(f"\n{'ALL PASS' if _fails == 0 else str(_fails) + ' FAILED'}")
    sys.exit(1 if _fails else 0)


if __name__ == "__main__":
    main()
