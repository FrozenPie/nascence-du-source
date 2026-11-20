"""
_test_J3310_key_shadow.py -- proving test for J-3310 (D-0552, plan memory_knowledge, row P-0004):
core/memory/key_shadow.py, the OBSERVE-ONLY arm that re-scores the cached embedding matrix with the memory router's
keys blended in (design: docs/reviews/memory_router_keys_shadow_design_J-3163.md section 3).

Run from a WORKTREE, never from C:\\Nascence itself:
    python scripts/_test_J3310_key_shadow.py [--perf]

Everything runs on a tempdir DB with a deterministic fake embedder; no live store, no model, no Ramses call. The
log path (_LOG) is pointed at a tempdir file. Checks:
  A static   store.retrieve() does not reference the new module/accessor (protected base system); the accessor runs
             no SQL; orchestrator has exactly one key-shadow call, unassigned, and the two memory_fragments
             assignments are unchanged; the module is in core.profile's rebase list; retrieve() is byte-identical to
             the base commit when that commit is reachable.
  B parity   the shadow's own recomputation of the plain arm reproduces what the real store.retrieve() returned
             (same ids, same order, same score) over a battery of queries / time_bias / climate bias, on a pool that
             has all layers, seed rows, hidden / cold / chaptered / dormant rows; plain_matches_live is True.
  C arms     A05 == plain when the key vector equals the query vector; arm B swaps at most 2 slots, never the top-1,
             never the archive tier; arm N exists from the second call and flags identical keys; junk filter.
  D safety   kill switch, pool unavailable -> skipped row, garbage input and a raising embedder never raise, the
             write fence refuses a non-live process under data/, one JSON line per call with the design's fields,
             a fragment written between calls is seen by the next call (prep cache keyed on the change log).
  E reader   scripts/key_shadow_summary.py runs on the temp log.
  --perf     51k-row pool: median added time of the shadow computation (stubbed embedder, so embed cost is excluded).
"""
from __future__ import annotations

import ast
import json
import os
import random
import sqlite3
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
import numpy as np

TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TREE))
import core  # noqa: E402  (import core FIRST -- live-store safety rule)
from core import profile  # noqa: E402
from core.memory import store as M  # noqa: E402
from core.memory import key_shadow as KS  # noqa: E402

assert Path(core.__file__).resolve().is_relative_to(TREE), f"core resolved outside tree under test: {core.__file__}"
def _norm_j2677(t):
    """J-2677 (merged after this test) added _pool_stats probe lines to retrieve(); ignore only those so the check still pins the rest."""
    return "\n".join(l.replace(", pool_stats=_pool_stats", "") for l in t.splitlines() if "_pool_stats" not in l or "pool_stats=_pool_stats" in l)


BASE_COMMIT = "f4a4e013"
_fails = 0


def check(ok: bool, msg: str) -> None:
    global _fails
    print(("  PASS  " if ok else "  FAIL  ") + msg)
    if not ok:
        _fails += 1


def _h(s: str) -> int:
    h = 1469598103934665603
    for ch in s.encode("utf-8"):
        h = ((h ^ ch) * 1099511628211) % (2 ** 63)
    return h


def fake_embed(text):
    if not text or not text.strip():
        return None
    v = np.random.RandomState(_h(text) % (2 ** 31)).randn(384).astype(np.float32)
    return v / np.linalg.norm(v)


def quiet_side_channels() -> None:
    """retrieve() has observe-only side channels that append to data/ logs; null them so nothing leaves the tempdir."""
    M._log_retrieve_latency = lambda *a, **k: None
    from core import retrieval_probe as rp, r_shadow as rs
    rp.observe = lambda *a, **k: None
    rs.log_observation = lambda *a, **k: None


def build_db(tmp: Path, n: int, seed: int = 3310) -> list[str]:
    M.DB_PATH = tmp / "k.db"
    M._embed = fake_embed
    M._emb_reset()
    M._pool_invalidate()
    M._POOL_DELTA_MODE = "on"
    M.init_db()
    rs = random.Random(seed)
    now = time.time()
    layers = ["archive", "semantic", "semantic", "episodic", "episodic", "episodic", "episodic", "working", "dormant"]
    origins = ["lived", "reading", "seed", "study", "inner_thought", "journal", "dream", "standing_insight"]
    ids = []
    with sqlite3.connect(tmp / "k.db") as c:
        for i in range(n):
            text = f"memory {i} about {rs.choice(['river', 'garden', 'Travis', 'sleep', 'dream', 'book', 'cat', 'music'])} {rs.random():.6f}"
            fid = f"f{i:06d}"
            ids.append(fid)
            c.execute("""INSERT INTO memory_fragments (fragment_id, content, layer, relevance, timestamp, embedding, origin,
                         chapter_id, cold, temp, importance, keywords) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                      (fid, text, rs.choice(layers), 0.5, now - rs.random() * 86400 * 60, fake_embed(text).tobytes(),
                       rs.choice(origins), None if rs.random() < 0.9 else "chap1",
                       1 if rs.random() < 0.05 else 0, "hidden" if rs.random() < 0.03 else "warm", rs.random(), ""))
    return ids


def static_checks() -> None:
    print("== A: static ==")
    src = (TREE / "core" / "memory" / "store.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    fn = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    ret_src = ast.get_source_segment(src, fn["retrieve"])
    check("key_shadow" not in ret_src and "pool_embedding_view" not in ret_src,
          "store.retrieve() does not reference key_shadow or the accessor")
    acc = ast.get_source_segment(src, fn["pool_embedding_view"])
    check(".execute(" not in acc and "_connect" not in acc and "SELECT" not in acc, "accessor runs no SQL")
    # byte-identical retrieve() against the base commit, when it is reachable from this tree
    try:
        old = subprocess.run(["git", "-C", str(TREE), "show", f"{BASE_COMMIT}:core/memory/store.py"],
                             capture_output=True, text=True, encoding="utf-8", timeout=60)
        if old.returncode == 0:
            old_src = old.stdout
            old_fn = {n.name: n for n in ast.parse(old_src).body if isinstance(n, ast.FunctionDef)}
            check(_norm_j2677(ast.get_source_segment(old_src, old_fn["retrieve"])) == _norm_j2677(ret_src),
                  f"store.retrieve() is byte-identical to {BASE_COMMIT}")
        else:
            print(f"  SKIP  base commit {BASE_COMMIT} not reachable from this tree")
    except Exception as exc:
        print(f"  SKIP  base-commit compare unavailable ({exc})")
    osrc = (TREE / "core" / "orchestrator.py").read_text(encoding="utf-8")
    calls = [ln.strip() for ln in osrc.splitlines() if "shadow_compare_keys" in ln and not ln.strip().startswith("#")]
    check(len(calls) == 1 and calls[0].startswith("_ks.shadow_compare_keys"),
          f"orchestrator has exactly one key-shadow call, result unassigned ({calls})")
    assigns = [ln.strip() for ln in osrc.splitlines() if ln.strip().startswith("self.state.memory_fragments = ")]
    check(assigns.count("self.state.memory_fragments = fragments") == 1
          and assigns.count("self.state.memory_fragments = fragments + _added") == 1,
          f"orchestrator's memory_fragments assignments unchanged ({len(assigns)} in the file)")
    check('"core.memory.key_shadow"' in (TREE / "core" / "profile.py").read_text(encoding="utf-8"),
          "core.memory.key_shadow is in core.profile's rebase list")
    check(KS._LOG.name == "key_shadow.jsonl", "log is data/key_shadow.jsonl")


def row_for(q, keys, tb, bias=None, bw=0.0, live=None, cycle="c1", it="internal"):
    return KS.build_row(q, keys, tb, bias, bw, live if live is not None else [], cycle, it)


def parity(tmp: Path) -> None:
    print("== B: plain arm reproduces store.retrieve() ==")
    build_db(tmp, 900)
    quiet_side_channels()
    rs = random.Random(7)
    bias = fake_embed("a charged climate")
    queries = ["river", "what did Travis say about sleep", "dream of a garden", "book", "cat music", "zzz unrelated",
               "memory 17 about sleep", "the garden at night I am tired"]
    n = ok_ids = ok_order = ok_score = ok_flag = 0
    worst = 0.0
    for tb in ("recent", "distant", "all"):
        for q in queries:
            for use_bias in (False, True):
                ek = ["river", "sleep"]
                sk = ["Travis"]
                live = M.retrieve(ek, sk, time_bias=tb, query_text=q,
                                  bias_vec=bias if use_bias else None, bias_weight=0.3 if use_bias else 0.0)
                live_ids = [f.fragment_id for f in live]
                scored = [f for f in live if f.relevance != 0.0]          # the 5 recency-guarantee rows carry 0.0
                row = row_for(q, type("K", (), {"episodic_keys": ek, "semantic_keys": sk})(), tb,
                              bias if use_bias else None, 0.3 if use_bias else 0.0, live=live_ids)
                assert row is not None and "skipped" not in row, row
                p_ids = [e[0] for e in row["plain9"]]
                n += 1
                ok_ids += set(p_ids) == {f.fragment_id for f in scored}
                ok_order += p_ids == [f.fragment_id for f in scored]
                d = max((abs(e[1] - f.relevance) for e, f in zip(row["plain9"], scored)), default=0.0)
                worst = max(worst, d)
                ok_score += d < 1e-3
                ok_flag += row["plain_matches_live"] is True
    check(ok_ids == n, f"plain id set == live scored set on {ok_ids}/{n} calls")
    check(ok_order == n, f"plain order == live order on {ok_order}/{n} calls")
    check(ok_score == n, f"plain score == live relevance (max abs diff {worst:.2e}) on {ok_score}/{n} calls")
    check(ok_flag == n, f"plain_matches_live True on {ok_flag}/{n} calls")
    r = row_for("river", {"episodic_keys": ["river"], "semantic_keys": []}, "recent", live=["not-a-real-id"])
    check(r["plain_matches_live"] is False and r["plain_missing_from_live"] == len(r["plain9"]),
          "plain_matches_live is False when live shares nothing (the validity flag can fail)")


def prep_patch(tmp: Path) -> None:
    print("== B2: incremental prep == full build, under random writes ==")
    rs = random.Random(99)
    KS._PREP = None
    n_inc = bad = steps = 0
    layers = ["archive", "semantic", "episodic", "working", "dormant"]
    origins = ["lived", "seed", "reading", "inner_thought"]
    with sqlite3.connect(M.DB_PATH) as c:
        c.row_factory = sqlite3.Row
        for step in range(60):
            for _ in range(rs.randint(0, 6)):
                op = rs.choice(["ins", "del", "layer", "ts", "origin", "hide", "cold"])
                fid = c.execute("SELECT fragment_id FROM memory_fragments ORDER BY RANDOM() LIMIT 1").fetchone()[0]
                if op == "ins":
                    t = f"fresh {step} {rs.random()}"
                    c.execute("""INSERT INTO memory_fragments (fragment_id, content, layer, relevance, timestamp, embedding,
                                 origin, cold, temp, importance, keywords) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                              (f"w{step}_{rs.randint(0, 10**9)}", t, rs.choice(layers[:4]), 0.5, time.time(),
                               fake_embed(t).tobytes(), rs.choice(origins), 0, "warm", 0.5, ""))
                elif op == "del":
                    c.execute("DELETE FROM memory_fragments WHERE fragment_id = ?", (fid,))
                elif op == "layer":
                    c.execute("UPDATE memory_fragments SET layer = ? WHERE fragment_id = ?", (rs.choice(layers), fid))
                elif op == "ts":
                    c.execute("UPDATE memory_fragments SET timestamp = ? WHERE fragment_id = ?", (time.time() - rs.random() * 1e5, fid))
                elif op == "origin":
                    c.execute("UPDATE memory_fragments SET origin = ? WHERE fragment_id = ?", (rs.choice(origins), fid))
                elif op == "hide":
                    c.execute("UPDATE memory_fragments SET temp = 'hidden' WHERE fragment_id = ?", (fid,))
                else:
                    c.execute("UPDATE memory_fragments SET cold = 1 WHERE fragment_id = ?", (fid,))
            c.commit()
            M.retrieve(["river"], [], time_bias="recent", query_text=f"river {step}")     # applies the delta
            view = M.pool_embedding_view()
            if view is None:
                bad += 1
                continue
            builds = [0]
            orig_build = KS._build_prep
            KS._build_prep = lambda v: (builds.__setitem__(0, builds[0] + 1), orig_build(v))[1]
            try:
                inc = KS._prep_for(view)
            finally:
                KS._build_prep = orig_build
            n_inc += (builds[0] == 0)
            full = KS._build_prep(view)
            steps += 1
            same = (inc.n == full.n and np.array_equal(inc.tier, full.tier) and np.array_equal(inc.ts, full.ts)
                    and np.array_equal(inc.seed, full.seed) and np.array_equal(inc.slots, full.slots)
                    and all(np.array_equal(a, b) for a, b in zip(inc.tier_idx, full.tier_idx)))
            bad += (not same)
    check(n_inc >= steps - 5, f"the incremental path (no full build) served {n_inc}/{steps} write batches")
    check(steps >= 50 and bad == 0, f"incremental prep identical to a full build on {steps - bad}/{steps} write batches")
    # a different generation must not be patched
    KS._PREP.gen = -5
    v = M.pool_embedding_view()
    p2 = KS._prep_for(v)
    check(p2.gen == v["gen"] and np.array_equal(p2.tier, KS._build_prep(v).tier), "a stale generation falls back to a full build")


def arms(tmp: Path) -> None:
    print("== C: arms ==")
    KS._prev_kv_set(None)
    q = "river garden"
    live = [f.fragment_id for f in M.retrieve(["river garden"], [], time_bias="recent", query_text=q)]
    r1 = row_for(q, {"episodic_keys": [q], "semantic_keys": []}, "recent", live=live)
    check([e[0] for e in r1["A05_9"]] == [e[0] for e in r1["plain9"]]
          and [e[0] for e in r1["A025_9"]] == [e[0] for e in r1["plain9"]],
          "key vector == query vector -> A05 and A025 equal plain")
    check("N_9" not in r1, "no arm N on the first call (no previous keys)")
    r2 = row_for(q, {"episodic_keys": ["sleep", "dream"], "semantic_keys": ["music"]}, "recent", live=live)
    check(len(r2["B_9"]) == len(r2["plain9"]), "arm B keeps the set size")
    plain_ids = [e[0] for e in r2["plain9"]]
    b_ids = [e[0] for e in r2["B_9"]]
    check(len(set(b_ids) - set(plain_ids)) <= KS.B_SLOTS and set(r2["B_added"]) == set(b_ids) - set(plain_ids),
          f"arm B adds at most {KS.B_SLOTS} items, all listed in B_added ({len(r2['B_added'])} added)")
    check(b_ids[0] == plain_ids[0], "arm B never replaces the top-1 plain hit")
    p_arch = [e for e in r2["plain9"] if e[3] is not None]
    check(all(i in b_ids for i in plain_ids[:2]), "arm B leaves the archive-tier head (positions 0-1) alone")
    check(all(e[1] is not None and e[2] >= 1 for e in r2["B_9"]), "arm B entries carry score and plain rank")
    check("N_9" in r2 and r2["N_same_keys"] is False, "arm N appears on the second call with different keys")
    r3 = row_for(q, {"episodic_keys": ["sleep", "dream"], "semantic_keys": ["music"]}, "recent", live=live)
    check(r3["N_same_keys"] is True, "arm N flags identical keys (control is void for that row)")
    check(r2["A05_9"] != r2["plain9"] or r2["A025_9"] != r2["plain9"], "a real key vector moves at least one arm")
    check(0 <= r2["A05_overlap"] <= len(r2["plain9"]) and isinstance(r2["A05_top1_kept"], bool),
          "overlap and top1_kept fields present")
    check(r2["cos_query_keys"] is not None and -1.0 <= r2["cos_query_keys"] <= 1.0, "cos_query_keys logged")
    # junk filter
    rj = row_for(q, {"episodic_keys": ["the_entity", "you", "string", "Travis"], "semantic_keys": ["The Person"]},
                 "recent", live=live)
    check(rj["keys_used_n"] == 1 and rj["junk_keys_n"] == 4, f"junk tokens dropped before embedding ({rj['keys_used_n']} used, {rj['junk_keys_n']} junk)")
    ra = row_for(q, {"episodic_keys": ["the_entity", "none"], "semantic_keys": ["you"]}, "recent", live=live)
    check(ra.get("no_usable_keys") is True and "A05_9" not in ra and "plain9" in ra,
          "all-junk keys -> plain recomputation only, flagged no_usable_keys")
    used, junk = KS.clean_keys(["river", "River ", "the person I met"], ["river!"])
    check(used == ["river", "the person I met"] and junk == 0, f"dedupe in order, real 'the person I met' key survives ({used})")


def safety(tmp: Path) -> None:
    print("== D: safety ==")
    log = tmp / "key_shadow_test.jsonl"
    KS._LOG = log
    KS._prev_kv_set(None)
    q = "river garden"
    keys = {"episodic_keys": ["sleep"], "semantic_keys": ["music"]}
    KS.shadow_compare_keys(q, keys, "recent", None, 0.0, ["x"], "cycle-1", "human")
    lines = log.read_text(encoding="utf-8").splitlines()
    check(len(lines) == 1, "one row per call")
    row = json.loads(lines[0])
    need = {"ts", "cycle_id", "input_type", "time_bias", "episodic_keys", "semantic_keys", "junk_keys_n",
            "cos_query_keys", "live_ids", "plain9", "A05_9", "A025_9", "B_9", "embed_ms", "matvec_ms",
            "plain_matches_live", "farewell"}
    check(need <= set(row), f"row carries the design's fields (missing: {sorted(need - set(row))})")
    check(row["cycle_id"] == "cycle-1" and row["input_type"] == "human" and row["farewell"] is False, "ids and flags")
    check(all(len(e) == 4 for e in row["plain9"]), "entries are [id, score, plain_rank, origin]")
    # a fragment written between calls is seen by the next call
    nid = "fnew-exact"
    with sqlite3.connect(M.DB_PATH) as c:
        c.execute("""INSERT INTO memory_fragments (fragment_id, content, layer, relevance, timestamp, embedding, origin,
                     cold, temp, importance, keywords) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                  (nid, "needle exact", "episodic", 0.5, time.time(), fake_embed("needle exact").tobytes(), "lived",
                   0, "warm", 0.5, ""))
    live = [f.fragment_id for f in M.retrieve([], [], time_bias="recent", query_text="needle exact")]
    check(nid in live, "fixture: retrieve() surfaces the new fragment")
    r = row_for("needle exact", keys, "recent", live=live)
    check(nid in [e[0] for e in r["plain9"]] and r["plain_matches_live"] is True,
          "prep cache sees the fragment written between calls")
    # kill switch
    KS.KEY_SHADOW_ON = False
    KS.shadow_compare_keys(q, keys, "recent", None, 0.0, [], "c2", "internal")
    check(len(log.read_text(encoding="utf-8").splitlines()) == 1, "KEY_SHADOW_ON=False writes nothing")
    KS.KEY_SHADOW_ON = True
    # pool unavailable
    M._POOL_DELTA_MODE = "off"
    KS.shadow_compare_keys(q, keys, "recent", None, 0.0, [], "c3", "internal")
    last = json.loads(log.read_text(encoding="utf-8").splitlines()[-1])
    check(last.get("skipped") == "pool_unavailable" and "plain9" not in last, "pool delta cache not serving -> small skipped row")
    M._POOL_DELTA_MODE = "on"
    # never raises
    try:
        KS.shadow_compare_keys(None, object(), None, "bad", "bad", None, None, None)
        KS.shadow_compare_keys("", None, "recent", None, 0.0, [], "c4", "internal")
        good = M._embed
        M._embed = lambda t: (_ for _ in ()).throw(RuntimeError("embedder down"))
        KS.shadow_compare_keys(q, keys, "recent", None, 0.0, [], "c5", "internal")
        M._embed = good
        raised = False
    except Exception as exc:
        raised = True
        print("      raised:", exc)
    M._embed = fake_embed
    check(not raised, "garbage input and a raising embedder never raise out of shadow_compare_keys")
    # write fence: a non-live process pointed under data/ is refused, no file appears
    fenced = profile._DATA / "key_shadow_J3310_fence_probe.jsonl"
    KS._LOG = fenced
    existed = fenced.exists()
    KS.shadow_compare_keys(q, keys, "recent", None, 0.0, ["x"], "c6", "internal")
    created = fenced.exists() and not existed
    if created:
        fenced.unlink()
    check(not created, "guard_path refuses a non-live write under data/ (swallowed, no file)")
    KS._LOG = log


def reader(tmp: Path) -> None:
    print("== E: reader ==")
    r = subprocess.run([sys.executable, str(TREE / "scripts" / "key_shadow_summary.py"), "--log",
                        str(tmp / "key_shadow_test.jsonl")], capture_output=True, text=True, encoding="utf-8",
                       timeout=120, cwd=str(TREE))
    check(r.returncode == 0 and "rows" in r.stdout and "plain_matches_live" in r.stdout,
          f"key_shadow_summary.py runs on the temp log (rc={r.returncode})")
    if r.returncode != 0:
        print(r.stdout[-600:], r.stderr[-600:])


def perf() -> None:
    print("== perf: 51k-row pool, stubbed embedder (embed cost excluded) ==")
    tmp = Path(tempfile.mkdtemp(prefix="J-3310_perf_"))
    M.DB_PATH = tmp / "k.db"
    M._embed = fake_embed
    M._emb_reset()
    M._pool_invalidate()
    M._POOL_DELTA_MODE = "on"
    M.init_db()
    rs = np.random.RandomState(1)
    now = time.time()
    layers = ["archive", "semantic", "episodic", "episodic", "episodic", "episodic"]
    n = 51000
    mat = rs.randn(n, 384).astype(np.float32)
    mat /= np.linalg.norm(mat, axis=1, keepdims=True)
    with sqlite3.connect(tmp / "k.db") as c:
        c.executemany("""INSERT INTO memory_fragments (fragment_id, content, layer, relevance, timestamp, embedding, origin,
                         cold, temp, importance, keywords) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                      ((f"p{i:06d}", f"m{i}", layers[i % 6], 0.5, now - (i % 5000) * 600.0, mat[i].tobytes(),
                        "seed" if i % 997 == 0 else "lived", 0, "warm", 0.5, "") for i in range(n)))
    quiet_side_channels()
    M.retrieve(["river"], [], time_bias="recent", query_text="river")            # builds the cache
    keys = {"episodic_keys": ["sleep", "river"], "semantic_keys": ["music"]}
    ts, tot = [], []
    for i in range(25):
        with sqlite3.connect(M.DB_PATH) as c:                                    # a write per call, as live
            c.execute("UPDATE memory_fragments SET importance = importance WHERE fragment_id = ?", (f"p{i:06d}",))
            c.execute("UPDATE memory_fragments SET timestamp = ? WHERE fragment_id = ?", (time.time(), f"p{i:06d}"))
        live = [f.fragment_id for f in M.retrieve(["river"], [], time_bias="recent", query_text=f"river {i}")]
        t0 = time.perf_counter()
        row = KS.build_row(f"river {i}", {"episodic_keys": [f"sleep {i}"], "semantic_keys": ["music"]}, "recent",
                           None, 0.0, live, "c", "internal")
        tot.append((time.perf_counter() - t0) * 1000.0)
        ts.append(row)
    ok = [r for r in ts if "skipped" not in r]
    print(f"  rows computed {len(ok)}/25; build_row ms median {statistics.median(tot):.1f} max {max(tot):.1f}; "
          f"prep {statistics.median(r['prep_ms'] for r in ok):.1f} matvec {statistics.median(r['matvec_ms'] for r in ok):.1f} "
          f"select {statistics.median(r['select_ms'] for r in ok):.1f}; plain_matches_live "
          f"{sum(1 for r in ok if r['plain_matches_live'])}/{len(ok)}")
    check(len(ok) == 25 and statistics.median(tot) < 500.0, "51k pool: shadow computation well under half a second")


def main() -> int:
    static_checks()
    tmp = Path(tempfile.mkdtemp(prefix="J-3310_keyshadow_"))
    KS._LOG = tmp / "key_shadow_test.jsonl"
    parity(tmp)
    prep_patch(tmp)
    arms(tmp)
    safety(tmp)
    reader(tmp)
    if "--perf" in sys.argv:
        perf()
    print("FAILED" if _fails else "ALL PASS", f"({_fails} failing)")
    return 1 if _fails else 0


if __name__ == "__main__":
    sys.exit(main())
