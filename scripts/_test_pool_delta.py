"""
_test_pool_delta.py -- proving test for J-2612 (F-3340): retrieve()'s recall pool can be served from a
trigger-maintained change log (core/memory/store.py _load_pool_delta) instead of re-reading the whole pool
(_load_pool_fast) on every call. Acceptance bar: the delta-loaded pool is IDENTICAL to _load_pool_fast's
(same tuples, same rowid order, same cosines) after every kind of write, and retrieve() returns the same ids
with the mode "on" as with it "off".

Run from a WORKTREE, never from C:\\Nascence itself:
    python scripts/_test_pool_delta.py [--db <sqlite .backup() COPY of the live nascence.db>]

Section A (synthetic, always): a tempdir DB; a fixed battery of writes (insert with/without embedding,
system_note, cold flip both ways, hide, chapter assign/clear, layer -> dormant / tier change, in-place
embedding rewrite with timestamp bump, delete, INSERT OR REPLACE, fragment_id rename, rowid reuse after a
max-rowid delete, bulk update, > MAX changes, pruned log gap, _emb_reset mid-stream, missing table, mode
"on" exception fallback) and a 400-step random fuzz, each step comparing delta vs fast; then retrieve()
off vs on (and shadow) over a query battery.
Section B (--db given): the same comparison on the real 45k-row pool copy plus timings: full rebuild, no-change
call, small-change call, trigger write overhead. The live DB is only stat()ed (canary), never opened.
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
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
import numpy as np

TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TREE))
import core  # noqa: E402  (import core FIRST -- live-store safety rule)
from core.memory import store as M  # noqa: E402

assert Path(core.__file__).resolve().is_relative_to(TREE), f"core resolved outside tree under test: {core.__file__}"
LIVE_DB = Path(r"C:\Nascence\data\memory\nascence.db")
_fails = 0


def check(ok: bool, msg: str) -> None:
    global _fails
    print(("  PASS  " if ok else "  FAIL  ") + msg)
    if not ok:
        _fails += 1


def _load_helpers():
    spec = importlib.util.spec_from_file_location("_t_fast", str(TREE / "scripts" / "_test_retrieve_fast_pool.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_t_fast"] = mod
    spec.loader.exec_module(mod)
    return mod


H = _load_helpers()


def pool_sig(rows):
    return [r._t for r in rows], np.array([r._sim for r in rows], dtype=np.float64)


def same_pool(conn_factory, qv, keys=("river", "garden")):
    """Load via _load_pool_fast and _load_pool_delta in ONE snapshot; True when identical."""
    with conn_factory() as conn:
        conn.execute("BEGIN")
        try:
            a = M._load_pool_fast(conn, qv, list(keys))
            b = M._load_pool_delta(conn, qv, list(keys))
        finally:
            conn.rollback()
    ta, sa = pool_sig(a)
    tb, sb = pool_sig(b)
    ok = ta == tb and len(sa) == len(sb) and bool(np.all(np.abs(sa - sb) <= 1e-6))
    if not ok:
        n = min(len(ta), len(tb))
        first = next((i for i in range(n) if ta[i] != tb[i]), None)
        print(f"      MISMATCH len fast={len(ta)} delta={len(tb)} first_diff_idx={first}")
    return ok, len(a)


def build_synth(tmp: Path, emb, n=700):
    M.DB_PATH = tmp / "a.db"
    M._embed = emb
    M._emb_reset()
    M._pool_invalidate()
    M._POOL_DELTA_MODE = "shadow"      # so init_db installs the change log + triggers
    M.init_db()
    now = time.time()
    rs = random.Random(2612)
    layers = ["archive", "semantic", "episodic", "episodic", "episodic", "working"]
    origins = ["lived", "reading", "seed", "study", "inner_thought", "journal", "system_note", "dream"]
    with sqlite3.connect(tmp / "a.db") as c:
        for i in range(n):
            text = f"memory {i} about {rs.choice(['river', 'garden', 'Travis', 'sleep', 'dream', 'book', 'cat', 'music'])} {rs.random():.6f}"
            blob = emb(text).tobytes() if rs.random() > 0.08 else None
            chap = None if rs.random() < 0.7 else ("" if rs.random() < 0.3 else f"chap{i % 5}")
            c.execute("""INSERT INTO memory_fragments (fragment_id, content, layer, relevance, timestamp, embedding, origin,
                         chapter_id, cold, temp, importance, keywords) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                      (f"f{i:04d}", text, rs.choice(layers) if rs.random() > 0.03 else "dormant", 0.5,
                       now - rs.random() * 86400 * 60, blob, rs.choice(origins), chap,
                       1 if rs.random() < 0.15 else 0, "hidden" if rs.random() < 0.04 else "warm",
                       rs.random(), "river garden" if i % 9 == 0 else ""))
    return now, rs


def section_a() -> None:
    print("== Section A: synthetic DB, delta vs fast ==")
    tmp = Path(tempfile.mkdtemp(prefix="J-2612_pooldelta_A_"))
    emb = H._det_embed_factory()
    now, rs = build_synth(tmp, emb)
    db = tmp / "a.db"
    qv = emb("river garden")
    mk = M._connect

    plan = [tuple(p) for p in sqlite3.connect(db).execute("SELECT name FROM sqlite_master WHERE type='trigger'")]
    check(len(plan) == 3, f"init_db(shadow) installed 3 change-log triggers: {plan}")

    ok, n = same_pool(mk, qv)
    check(ok and n > 100, f"first call = full rebuild, identical to fast ({n} rows)")
    check(M._POOL.stats["rebuilt"] is True, "first call reported rebuilt")
    ok, _ = same_pool(mk, qv)
    check(ok and M._POOL.stats == {"rebuilt": False, "changed": 0}, "no writes -> delta no-op, identical")

    def w(sql, args=()):
        with sqlite3.connect(db) as c:
            c.execute(sql, args)

    def ids(where):
        return [r[0] for r in sqlite3.connect(db).execute(f"SELECT fragment_id FROM memory_fragments WHERE {where}")]

    active = "cold=0 AND temp!='hidden' AND origin!='system_note' AND layer!='dormant' AND (chapter_id IS NULL OR chapter_id='')"
    cases = []

    def case(label, fn):
        fn()
        ok, n = same_pool(mk, qv)
        check(ok, f"{label} ({n} rows, changed={M._POOL.stats['changed']}, rebuilt={M._POOL.stats['rebuilt']})")
        return ok

    t_new = "a brand new memory about the river at dusk"
    case("insert with embedding", lambda: w(
        "INSERT INTO memory_fragments (fragment_id,content,layer,timestamp,embedding,origin,cold,temp) VALUES (?,?,?,?,?,?,?,?)",
        ("fnew01", t_new, "episodic", now, emb(t_new).tobytes(), "lived", 0, "warm")))
    case("insert without embedding (keyword fallback)", lambda: w(
        "INSERT INTO memory_fragments (fragment_id,content,layer,timestamp,origin,cold,temp,keywords) VALUES (?,?,?,?,?,?,?,?)",
        ("fnew02", "river and garden words", "episodic", now + 1, "lived", 0, "warm", "river")))
    case("insert system_note (never in pool)", lambda: w(
        "INSERT INTO memory_fragments (fragment_id,content,layer,timestamp,embedding,origin,cold,temp) VALUES (?,?,?,?,?,?,?,?)",
        ("fnew03", "sys", "episodic", now + 2, emb("sys").tobytes(), "system_note", 0, "warm")))
    a1 = ids(active + " AND embedding IS NOT NULL")[0]
    case("cold flip 0 -> 1", lambda: w("UPDATE memory_fragments SET cold=1 WHERE fragment_id=?", (a1,)))
    case("re-warm cold 1 -> 0", lambda: w("UPDATE memory_fragments SET cold=0 WHERE fragment_id=?", (a1,)))
    a2 = ids(active)[1]
    case("hide (temp='hidden')", lambda: w("UPDATE memory_fragments SET temp='hidden' WHERE fragment_id=?", (a2,)))
    case("unhide", lambda: w("UPDATE memory_fragments SET temp='warm' WHERE fragment_id=?", (a2,)))
    a3 = ids(active)[2]
    case("chapter assigned", lambda: w("UPDATE memory_fragments SET chapter_id='chapX' WHERE fragment_id=?", (a3,)))
    case("chapter cleared to ''", lambda: w("UPDATE memory_fragments SET chapter_id='' WHERE fragment_id=?", (a3,)))
    a4 = ids(active)[3]
    case("layer -> dormant", lambda: w("UPDATE memory_fragments SET layer='dormant' WHERE fragment_id=?", (a4,)))
    case("layer dormant -> semantic (tier change)", lambda: w("UPDATE memory_fragments SET layer='semantic' WHERE fragment_id=?", (a4,)))
    a5 = ids(active + " AND embedding IS NOT NULL")[4]
    t2 = "the river memory rewritten as a rolling action record"
    case("embedding rewrite + timestamp bump", lambda: w(
        "UPDATE memory_fragments SET content=?, embedding=?, timestamp=? WHERE fragment_id=?",
        (t2, emb(t2).tobytes(), now + 5, a5)))
    case("embedding dropped (NULL) + timestamp bump", lambda: w(
        "UPDATE memory_fragments SET embedding=NULL, timestamp=? WHERE fragment_id=?", (now + 6, a5)))
    a6 = ids(active)[5]
    case("delete a pool row", lambda: w("DELETE FROM memory_fragments WHERE fragment_id=?", (a6,)))
    a7 = ids(active + " AND embedding IS NOT NULL")[6]
    case("INSERT OR REPLACE same fragment_id (new rowid)", lambda: w(
        "INSERT OR REPLACE INTO memory_fragments (fragment_id,content,layer,timestamp,embedding,origin,cold,temp) VALUES (?,?,?,?,?,?,?,?)",
        (a7, "replaced row", "episodic", now + 7, emb("replaced row").tobytes(), "lived", 0, "warm")))
    a8 = ids(active)[7]
    case("fragment_id renamed", lambda: w("UPDATE memory_fragments SET fragment_id='renamed_f' WHERE fragment_id=?", (a8,)))

    def rowid_reuse():
        with sqlite3.connect(db) as c:
            mx = c.execute("SELECT fragment_id FROM memory_fragments ORDER BY rowid DESC LIMIT 1").fetchone()[0]
            c.execute("DELETE FROM memory_fragments WHERE fragment_id=?", (mx,))
            c.execute("INSERT INTO memory_fragments (fragment_id,content,layer,timestamp,embedding,origin,cold,temp) VALUES (?,?,?,?,?,?,?,?)",
                      ("reuse01", "rowid reuse", "episodic", now + 8, emb("rowid reuse").tobytes(), "lived", 0, "warm"))
    case("delete max-rowid row then insert (rowid reused)", rowid_reuse)
    case("bulk update 400 rows timestamp", lambda: w(
        "UPDATE memory_fragments SET timestamp=timestamp+1 WHERE rowid IN (SELECT rowid FROM memory_fragments LIMIT 400)"))

    old_max = M._POOL_DELTA_MAX_CHANGES
    M._POOL_DELTA_MAX_CHANGES = 50
    case("more changes than _POOL_DELTA_MAX_CHANGES -> rebuild", lambda: w(
        "UPDATE memory_fragments SET timestamp=timestamp+1 WHERE rowid IN (SELECT rowid FROM memory_fragments LIMIT 200)"))
    check(M._POOL.stats["rebuilt"] is True, "  ... and it was a full rebuild")
    M._POOL_DELTA_MAX_CHANGES = old_max

    def prune_gap():
        with sqlite3.connect(db) as c:
            c.execute("INSERT INTO memory_fragments (fragment_id,content,layer,timestamp,origin,cold,temp) VALUES ('gap01','g','episodic',?, 'lived',0,'warm')", (now + 9,))
            c.execute("INSERT INTO memory_fragments (fragment_id,content,layer,timestamp,origin,cold,temp) VALUES ('gap02','g','episodic',?, 'lived',0,'warm')", (now + 10,))
            c.execute("DELETE FROM memory_pool_changes WHERE seq = (SELECT MIN(seq) FROM memory_pool_changes WHERE seq > ?)", (M._POOL.seq,))
    case("a hole in the change log (pruned/foreign consumer) -> rebuild", prune_gap)
    check(M._POOL.stats["rebuilt"] is True, "  ... and it was a full rebuild")

    def emb_reset_mid():
        M._emb_reset()
        w("UPDATE memory_fragments SET cold=1 WHERE fragment_id=?", (ids(active)[0],))
    case("_emb_reset() between calls -> rebuild", emb_reset_mid)
    check(M._POOL.stats["rebuilt"] is True, "  ... and it was a full rebuild")

    # whole-table prune to nothing (init_db trim at boot with a stale consumer): must not wedge
    def prune_all():
        with sqlite3.connect(db) as c:
            c.execute("DELETE FROM memory_pool_changes")
    case("change log emptied entirely (no new writes)", prune_all)
    ok, _ = same_pool(mk, qv)
    check(ok and M._POOL.stats["rebuilt"] is False, "  ... then a no-write call is a clean no-op (no rebuild loop)")

    # fuzz
    print("-- fuzz (400 random writes, compare after each) --")
    bad = 0
    rs2 = random.Random(77)
    for step in range(400):
        with sqlite3.connect(db) as c:
            kind = rs2.choice(["ins", "cold", "hide", "chap", "layer", "emb", "del", "ts", "rename", "replace"])
            row = c.execute("SELECT fragment_id FROM memory_fragments ORDER BY RANDOM() LIMIT 1").fetchone()
            fid = row[0] if row else None
            if kind == "ins" or fid is None:
                t = f"fuzz {step} river"
                c.execute("INSERT INTO memory_fragments (fragment_id,content,layer,timestamp,embedding,origin,cold,temp) VALUES (?,?,?,?,?,?,?,?)",
                          (f"z{step}", t, rs2.choice(["episodic", "semantic", "archive", "dormant"]), now + 20 + step,
                           emb(t).tobytes() if rs2.random() > 0.2 else None, rs2.choice(["lived", "seed", "system_note"]), 0, "warm"))
            elif kind == "cold":
                c.execute("UPDATE memory_fragments SET cold=1-cold WHERE fragment_id=?", (fid,))
            elif kind == "hide":
                c.execute("UPDATE memory_fragments SET temp=CASE temp WHEN 'hidden' THEN 'warm' ELSE 'hidden' END WHERE fragment_id=?", (fid,))
            elif kind == "chap":
                c.execute("UPDATE memory_fragments SET chapter_id=CASE WHEN chapter_id IS NULL THEN 'c' ELSE NULL END WHERE fragment_id=?", (fid,))
            elif kind == "layer":
                c.execute("UPDATE memory_fragments SET layer=? WHERE fragment_id=?", (rs2.choice(["episodic", "semantic", "dormant", "archive"]), fid))
            elif kind == "emb":
                t = f"rewrite {step}"
                c.execute("UPDATE memory_fragments SET embedding=?, timestamp=? WHERE fragment_id=?", (emb(t).tobytes(), now + 1000 + step, fid))
            elif kind == "del":
                c.execute("DELETE FROM memory_fragments WHERE fragment_id=?", (fid,))
            elif kind == "ts":
                c.execute("UPDATE memory_fragments SET timestamp=timestamp+0.5 WHERE fragment_id=?", (fid,))
            elif kind == "rename":
                c.execute("UPDATE memory_fragments SET fragment_id=? WHERE fragment_id=?", (f"rn{step}", fid))
            elif kind == "replace":
                c.execute("INSERT OR REPLACE INTO memory_fragments (fragment_id,content,layer,timestamp,embedding,origin,cold,temp) VALUES (?,?,?,?,?,?,?,?)",
                          (fid, f"rep {step}", "episodic", now + 2000 + step, emb(f"rep {step}").tobytes(), "lived", 0, "warm"))
        if rs2.random() < 0.6:       # sometimes several writes pile up between reads
            ok, _ = same_pool(mk, qv)
            if not ok:
                bad += 1
                print(f"      fuzz step {step} kind={kind} diverged")
    ok, n = same_pool(mk, qv)
    check(bad == 0 and ok, f"fuzz: {bad} divergences in 400 steps; final pool {n} rows identical")

    # missing table: on-mode falls back to fast, never raises
    print("-- retrieve() off vs on vs shadow, missing-table fallback --")
    cap_off, cap_on = H.Capture(), H.Capture()
    H.patch_side_channels(M, cap_off)

    def run_queries(label):
        out = []
        for tb in ("recent", "distant", "all"):
            for q in ["river", "what did Travis say about sleep", "dream of a garden", "book", "cat music", "zzz unrelated"]:
                out.append([f.fragment_id for f in M.retrieve([q, "garden"], ["sleep"], time_bias=tb, limit=8, query_text=q)])
        return out

    M._POOL_DELTA_MODE = "off"
    r_off = run_queries("off")
    M._POOL_DELTA_MODE = "on"
    M._pool_invalidate()
    r_on1 = run_queries("on")
    with sqlite3.connect(db) as c:
        c.execute("INSERT INTO memory_fragments (fragment_id,content,layer,timestamp,embedding,origin,cold,temp) VALUES (?,?,?,?,?,?,?,?)",
                  ("late01", "late river garden thought", "episodic", now + 5000, emb("late river garden thought").tobytes(), "lived", 0, "warm"))
    r_on2 = run_queries("on after a write")
    M._POOL_DELTA_MODE = "off"
    r_off2 = run_queries("off after a write")
    check(r_off == r_on1, "retrieve(): mode 'on' (first call = rebuild) returns the same ids/order as 'off' over 18 queries")
    check(r_off2 == r_on2, "retrieve(): mode 'on' after a write returns the same ids/order as 'off'")
    check(any("fast+delta" == x[4] for x in cap_off.latency), "probe path label 'fast+delta' recorded when delta served")
    check(sum(1 for x in cap_off.latency if x[4] == "fast") >= 18, "probe path label stays 'fast' with the mode off")

    M._POOL_DELTA_SHADOW_LOG = tmp / "shadow.jsonl"
    M._pool_shadow_calls = 0
    M._POOL_DELTA_MODE = "shadow"
    r_sh = run_queries("shadow")
    rows = [json.loads(x) for x in open(M._POOL_DELTA_SHADOW_LOG, encoding="utf-8")]
    check(r_sh == r_off2, "retrieve(): shadow mode returns the same ids as 'off' (it serves the fast path)")
    check(len(rows) >= 3 and all(r.get("identical") is True for r in rows),
          f"shadow log: {len(rows)} comparison rows, all identical=True")

    M._POOL_DELTA_MODE = "on"
    with sqlite3.connect(db) as c:
        c.executescript("DROP TRIGGER trg_pool_chg_ins; DROP TRIGGER trg_pool_chg_upd; DROP TRIGGER trg_pool_chg_del; DROP TABLE memory_pool_changes;")
    M._pool_invalidate()
    r_nt = run_queries("on, table missing")
    check(r_nt == run_queries("again") and len(r_nt) == 18 and any(r_nt),
          "mode 'on' with the change-log table missing: retrieve() still answers (fell back to _load_pool_fast)")
    M._POOL_DELTA_MODE = "off"

    # off mode: init_db must not create anything
    tmp2 = Path(tempfile.mkdtemp(prefix="J-2612_pooldelta_off_"))
    M.DB_PATH = tmp2 / "b.db"
    M._POOL_DELTA_MODE = "off"
    M.init_db()
    names = [r[0] for r in sqlite3.connect(tmp2 / "b.db").execute(
        "SELECT name FROM sqlite_master WHERE name LIKE '%pool_chg%' OR name='memory_pool_changes'")]
    check(names == [], f"mode 'off': init_db creates no change-log table or trigger ({names})")


def section_b(dbcopy: Path) -> None:
    print("== Section B: real-pool copy ==")
    assert dbcopy.resolve() != LIVE_DB.resolve(), "refusing to run against the live DB"
    live_stat = (LIVE_DB.stat().st_size, int(LIVE_DB.stat().st_mtime))
    M.DB_PATH = dbcopy
    M._emb_reset()
    M._pool_invalidate()
    M._POOL_DELTA_MODE = "shadow"
    with M._connect() as conn:
        t = time.perf_counter()
        M._init_pool_changes(conn)
        print(f"   change-log table + triggers installed on the copy in {(time.perf_counter() - t) * 1000:.0f} ms")
    rng = np.random.RandomState(26)

    def qv():
        v = rng.randn(384).astype(np.float32)
        return v / np.linalg.norm(v)

    mk = M._connect
    t = time.perf_counter()
    ok, n = same_pool(mk, qv())
    print(f"   first call (both full loads): {(time.perf_counter() - t) * 1000:.0f} ms, pool {n} rows")
    check(ok, f"real pool identical on first load ({n} rows)")

    def time_calls(fn, k=15):
        xs = []
        for _ in range(k):
            q = qv()
            with mk() as conn:
                t0 = time.perf_counter()
                fn(conn, q, ["a"])
                xs.append((time.perf_counter() - t0) * 1000.0)
        return statistics.median(xs), min(xs), max(xs)

    f_med = time_calls(M._load_pool_fast)
    d_med = time_calls(M._load_pool_delta)
    print(f"   fast  (no writes) median/min/max ms: {f_med[0]:.1f} / {f_med[1]:.1f} / {f_med[2]:.1f}")
    print(f"   delta (no writes) median/min/max ms: {d_med[0]:.1f} / {d_med[1]:.1f} / {d_med[2]:.1f}")
    check(d_med[0] < f_med[0], "delta no-write median is below fast median")

    # writes: a few inserts + cold flips + a timestamp rewrite between calls, like a live cycle
    src = sqlite3.connect(dbcopy)
    base = src.execute("SELECT content, layer, embedding, origin FROM memory_fragments WHERE cold=0 AND embedding IS NOT NULL "
                       "AND length(embedding)>0 AND origin='lived' LIMIT 20").fetchall()
    xs_d, xs_f, allok = [], [], True
    for rnd in range(12):
        with sqlite3.connect(dbcopy) as c:
            for j in range(rng.randint(1, 4)):
                b = base[rng.randint(0, len(base))]
                c.execute("INSERT INTO memory_fragments (fragment_id,content,layer,timestamp,embedding,origin,cold,temp) VALUES (?,?,?,?,?,?,0,'warm')",
                          (f"j2612_{rnd}_{j}", b[0], b[1], time.time(), b[2], b[3]))
            c.execute("UPDATE memory_fragments SET cold=1 WHERE rowid IN (SELECT rowid FROM memory_fragments WHERE cold=0 "
                      "AND origin='lived' AND chapter_id IS NULL ORDER BY RANDOM() LIMIT 2)")
        q = qv()
        with mk() as conn:
            t0 = time.perf_counter(); M._load_pool_delta(conn, q, ["a"]); xs_d.append((time.perf_counter() - t0) * 1000.0)
        with mk() as conn:
            t0 = time.perf_counter(); M._load_pool_fast(conn, q, ["a"]); xs_f.append((time.perf_counter() - t0) * 1000.0)
        ok, _ = same_pool(mk, qv())
        allok &= ok
    check(allok, "12 rounds of (inserts + cold flips) between calls: delta identical to fast every round")
    print(f"   after writes: delta median {statistics.median(xs_d):.1f} ms vs fast median {statistics.median(xs_f):.1f} ms "
          f"(last changed={M._POOL.stats['changed']})")
    check(statistics.median(xs_d) < statistics.median(xs_f), "delta median with live-cycle-sized writes beats fast median")

    # trigger write overhead: 3000 single-column updates in one transaction, with vs without triggers
    def upd_ms():
        with sqlite3.connect(dbcopy) as c:
            t0 = time.perf_counter()
            c.execute("UPDATE memory_fragments SET cold=cold WHERE rowid IN (SELECT rowid FROM memory_fragments LIMIT 3000)")
            return (time.perf_counter() - t0) * 1000.0
    with_trg = statistics.median([upd_ms() for _ in range(5)])
    with sqlite3.connect(dbcopy) as c:
        c.executescript("DROP TRIGGER trg_pool_chg_ins; DROP TRIGGER trg_pool_chg_upd; DROP TRIGGER trg_pool_chg_del;")
    without_trg = statistics.median([upd_ms() for _ in range(5)])
    print(f"   3000-row UPDATE ... SET cold=cold: {with_trg:.0f} ms with triggers vs {without_trg:.0f} ms without "
          f"({(with_trg - without_trg) / 3000 * 1000:.1f} us/row)")
    after = (LIVE_DB.stat().st_size, int(LIVE_DB.stat().st_mtime))
    check(after == live_stat, f"live DB canary unchanged (size,mtime) {after}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=None)
    a = ap.parse_args()
    section_a()
    if a.db:
        section_b(a.db)
    print(f"\n{'ALL PASS' if _fails == 0 else str(_fails) + ' FAILURE(S)'}")
    sys.exit(1 if _fails else 0)
