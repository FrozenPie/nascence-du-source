"""
_test_J-3319_chapter_descent_shadow.py -- proving test for J-3319 (D-0637, plan memory_knowledge):
core/chapter_descent_shadow.py, the OBSERVE-ONLY log of the chapter members closest to the query when a chapter gist
is already in Du's served set (docs/reviews/J-3248_chaptered_memory_recall_review.md sections 5 and 6).

Run from a WORKTREE, never from C:\\Nascence itself:
    python scripts/_test_J-3319_chapter_descent_shadow.py [--perf]

Everything runs on a tempdir DB with hand-built vectors (the query is embedded by a deterministic fake embedder);
no live store, no model, no hub, no Ramses call. The log path (_LOG) points at a tempdir file. Checks:
  A static   orchestrator has exactly one descent-shadow call, result unassigned, to_thread, inside its own
             try/except; the memory_fragments assignments in _retrieve_memory are unchanged; _lattice_parents and
             deep_recall are byte-identical to the base commit when it is reachable; the module is in
             core.profile's rebase list; the module has no INSERT/UPDATE/DELETE and no prompt text.
  B (a)      no chapter served (or a chapter below the 0.25 relevance gate) -> no row, no log file
  C (b)      the live return value is unchanged: the served list is not mutated, the return is a count, the
             memory_fragments table is byte-identical before and after
  D (c)      a chapter with members logs 3 candidates and BOTH controls, with the design's fields; members already
             served and near-duplicates (cos >= 0.85) of a served fragment are dropped and counted; candidates are
             ranked by cosine to the query; the same-chapter control is deterministic per cycle
  E (d)      kill switch off -> nothing read, nothing written; a chapter with no members logs an empty row; a
             garbage input and a raising embedder never raise; the write fence refuses a non-live process under data/
  F reader   scripts/chapter_descent_summary.py runs on the temp log
  --perf     1,845-member chapter (the observed maximum) on a 20k-row pool: hook time, vs the 50 ms budget
"""
from __future__ import annotations

import ast
import json
import os
import sqlite3
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
from core import chapter_descent_shadow as CDS  # noqa: E402
from core.schema import MemoryFragment  # noqa: E402

assert Path(core.__file__).resolve().is_relative_to(TREE), f"core resolved outside tree under test: {core.__file__}"
BASE_COMMIT = "f4a4e013"
DIM = 384
_fails = 0


def check(ok: bool, msg: str) -> None:
    global _fails
    print(("  PASS  " if ok else "  FAIL  ") + msg)
    if not ok:
        _fails += 1


def _unit(v):
    v = np.asarray(v, dtype=np.float32)
    return (v / np.linalg.norm(v)).astype(np.float32)


def vec_near(q, w, rs):
    """a unit vector whose cosine to q is about w/sqrt(w^2+1) (noise is orthogonal-ish random)"""
    return _unit(w * q + rs.randn(DIM).astype(np.float32) / np.sqrt(DIM))


QUERY = "the river bank and the green stripe of soil near the cliff edge"
RS = np.random.RandomState(3319)
QV = _unit(RS.randn(DIM))


def fake_embed(text):
    if not text or not text.strip():
        return None
    return QV.copy() if text == QUERY else _unit(np.random.RandomState(abs(hash(text)) % (2 ** 31)).randn(DIM))


def build_db(tmp: Path, n_members: int = 30, n_pool: int = 60):
    M.DB_PATH = tmp / "d.db"
    M._embed = fake_embed
    M._emb_reset()
    M._pool_invalidate()
    M._POOL_DELTA_MODE = "on"
    M.init_db()
    now = time.time()
    rs = np.random.RandomState(7)
    info = {"pool": [], "members": [], "chapter": "chap1", "empty_chapter": "chapEmpty"}

    def ins(c, fid, text, layer, origin, chapter_id, vec, cold=0, level=0, age_days=3.0):
        c.execute("""INSERT INTO memory_fragments (fragment_id, content, layer, relevance, timestamp, embedding, origin,
                     chapter_id, cold, temp, importance, keywords, chapter_level) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (fid, text, layer, 0.5, now - age_days * 86400, np.asarray(vec, dtype=np.float32).tobytes(), origin,
                   chapter_id, cold, "warm", 0.5, "", level))

    with sqlite3.connect(tmp / "d.db") as c:
        ins(c, "chap1", "A period when I kept watching the river and the soil", "archive", "chapter", None,
            vec_near(QV, 0.9, rs), level=1)
        ins(c, "chapEmpty", "A chapter nobody was filed behind", "archive", "chapter", None, vec_near(QV, 0.9, rs), level=1)
        # unwalled episodic pool: 3 served rows, then a spread of cosines so the +/-0.05 band is populated
        for i in range(n_pool):
            w = 0.1 + 1.6 * (i / max(1, n_pool - 1))
            fid = f"p{i:04d}"
            info["pool"].append(fid)
            ins(c, fid, f"pool memory {i} about the river and cliff soil number {i}", "episodic", "lived", None,
                vec_near(QV, w, rs))
        # chapter members: cosine grades from 0 to ~0.7; every member is cold + walled
        for i in range(n_members):
            w = 0.05 + 1.2 * (i / max(1, n_members - 1))
            fid = f"m{i:04d}"
            info["members"].append(fid)
            ins(c, fid, f"member {i} the soil stripe cliff river anxious winter {i}", "episodic",
                "inner_thought" if i % 2 else "active_imagination", "chap1", vec_near(QV, w, rs), cold=1,
                age_days=100 + i)
        # a near-duplicate member: same vector as served pool row p0010
        c.execute("SELECT embedding FROM memory_fragments WHERE fragment_id='p0010'")
        dup_blob = c.execute("SELECT embedding FROM memory_fragments WHERE fragment_id='p0010'").fetchone()[0]
        ins(c, "mDUP", "member that is a near copy of a served row", "episodic", "inner_thought", "chap1",
            np.frombuffer(dup_blob, dtype=np.float32), cold=1)
    M.retrieve(["river"], [], time_bias="recent", query_text=QUERY)       # builds the pool cache
    return info


def frag(fid, origin="lived", relevance=0.5, layer="episodic", content=None):
    return MemoryFragment(fragment_id=fid, content=content or f"served {fid} river soil", layer=layer,
                          relevance=relevance, timestamp=time.time(), origin=origin)


def rows_of(p: Path) -> list:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


def table_digest(path: Path) -> str:
    import hashlib
    with sqlite3.connect(path) as c:
        h = hashlib.sha256()
        for r in c.execute("SELECT * FROM memory_fragments ORDER BY fragment_id"):
            h.update(repr(r).encode("utf-8", "replace"))
        return h.hexdigest()


def static_checks() -> None:
    print("== A: static ==")
    osrc = (TREE / "core" / "orchestrator.py").read_text(encoding="utf-8")
    calls = [ln.strip() for ln in osrc.splitlines() if "_cds.shadow_descent" in ln and not ln.strip().startswith("#")]
    check(len(calls) == 1 and calls[0].startswith("_cds.shadow_descent"), f"exactly one descent-shadow call ({calls})")
    check("await asyncio.to_thread(\n                    _cds.shadow_descent" in osrc, "the call is awaited via asyncio.to_thread, result unassigned")
    tree = ast.parse(osrc)
    meth = next(n for c in tree.body if isinstance(c, ast.ClassDef) for n in c.body
                if isinstance(n, ast.AsyncFunctionDef) and n.name == "_retrieve_memory")
    hit = [n for n in ast.walk(meth) if isinstance(n, ast.Try) and any("_cds" in ast.dump(b) for b in n.body)]
    check(bool(hit) and any(h.handlers for h in hit), "the call sits inside its own try/except in _retrieve_memory")
    assigns = [ln.strip() for ln in osrc.splitlines() if ln.strip().startswith("self.state.memory_fragments = ")]
    check(assigns.count("self.state.memory_fragments = fragments") == 1
          and assigns.count("self.state.memory_fragments = fragments + _added") == 1
          and assigns.count("self.state.memory_fragments = self.state.memory_fragments + added") == 1,
          f"memory_fragments assignments unchanged ({len(assigns)} in the file)")
    try:
        old = subprocess.run(["git", "-C", str(TREE), "show", f"{BASE_COMMIT}:core/orchestrator.py"],
                             capture_output=True, text=True, encoding="utf-8", timeout=60)
        if old.returncode == 0:
            ofn = {n.name: n for c in ast.parse(old.stdout).body if isinstance(c, ast.ClassDef) for n in c.body
                   if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
            nfn = {n.name: n for c in tree.body if isinstance(c, ast.ClassDef) for n in c.body
                   if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
            check(ast.get_source_segment(old.stdout, ofn["_deep_recall_balance"]) == ast.get_source_segment(osrc, nfn["_deep_recall_balance"]),
                  f"_deep_recall_balance (incl. _lattice_parents) is byte-identical to {BASE_COMMIT}")
            o2 = subprocess.run(["git", "-C", str(TREE), "show", f"{BASE_COMMIT}:core/memory_levels.py"],
                                capture_output=True, text=True, encoding="utf-8", timeout=60).stdout
            check(o2 == (TREE / "core" / "memory_levels.py").read_text(encoding="utf-8"),
                  f"core/memory_levels.py (deep_recall) is byte-identical to {BASE_COMMIT}")
        else:
            print(f"  SKIP  base commit {BASE_COMMIT} not reachable from this tree")
    except Exception as exc:
        print(f"  SKIP  base-commit compare unavailable ({exc})")
    check('"core.chapter_descent_shadow"' in (TREE / "core" / "profile.py").read_text(encoding="utf-8"),
          "module is in core.profile's rebase list")
    msrc = (TREE / "core" / "chapter_descent_shadow.py").read_text(encoding="utf-8")
    code = "\n".join(ln for ln in msrc.splitlines() if not ln.strip().startswith("#"))
    check(not any(k in code.upper() for k in ("INSERT INTO", "UPDATE MEMORY", "DELETE FROM", "STORE_FRAGMENT")),
          "module issues no write SQL and calls no store writer")
    names = {n.id for n in ast.walk(ast.parse(msrc)) if isinstance(n, ast.Name)} | {n.attr for n in ast.walk(ast.parse(msrc)) if isinstance(n, ast.Attribute)}
    imps = {a.name for n in ast.walk(ast.parse(msrc)) if isinstance(n, (ast.Import, ast.ImportFrom)) for a in n.names}
    check(not (names & {"call_json", "run_task", "chat", "generate"}) and not any("facade" in i or "inference" in i for i in imps),
          "module makes no model call (no inference/facade import, no call_json/run_task)")


def behaviour_checks(tmp: Path) -> None:
    info = build_db(tmp)
    CDS._LOG = tmp / "cds.jsonl"
    served_plain = [frag("p0005"), frag("p0010"), frag("p0020")]

    print("== B (a): no chapter served -> no row ==")
    n = CDS.shadow_descent(served_plain, QUERY, "cycNone", "internal")
    check(n == 0 and not CDS._LOG.exists(), "no chapter in the served set -> 0 rows, no file")
    n = CDS.shadow_descent(served_plain + [frag("chap1", "chapter", relevance=0.2, layer="archive")], QUERY, "cycLow", "internal")
    check(n == 0 and not CDS._LOG.exists(), "a chapter below relevance 0.25 -> 0 rows")
    n = CDS.shadow_descent(served_plain + [frag("m0003", "inner_thought", relevance=0.9)], QUERY, "cycMember", "internal")
    check(n == 0 and not CDS._LOG.exists(), "a chaptered MEMBER served (not a gist) does not trigger it")

    print("== C (b): live return value unchanged ==")
    served = served_plain + [frag("chap1", "chapter", relevance=0.6, layer="archive"), frag("m0029", "inner_thought")]
    snapshot = [(f.fragment_id, f.content, f.relevance, f.origin, f.layer) for f in served]
    ids_before = [id(f) for f in served]
    dig0 = table_digest(tmp / "d.db")
    n = CDS.shadow_descent(tuple(served), QUERY, "cycA", "internal")
    check(n == 1, f"one chapter -> one row written (got {n})")
    check([(f.fragment_id, f.content, f.relevance, f.origin, f.layer) for f in served] == snapshot
          and [id(f) for f in served] == ids_before, "the served fragments are not mutated, added to or reordered")
    check(isinstance(n, int), "the return value is a plain count, never fragments")
    check(table_digest(tmp / "d.db") == dig0, "memory_fragments is byte-identical before and after (no store write)")

    print("== D (c): candidates and controls ==")
    rs = rows_of(CDS._LOG)
    r = rs[0]
    for k in ("ts", "cycle_id", "chapter_id", "chapter_level", "n_members", "query_head", "served_ids",
              "served_cos_median", "served_lex_median", "candidates", "control_chapter_member", "control_unwalled"):
        check(k in r, f"row carries '{k}'")
    check(r["cycle_id"] == "cycA" and r["chapter_id"] == "chap1" and r["chapter_level"] == 1, "cycle id, chapter id and level")
    check(r["n_members"] == 31, f"n_members counts the members, not the chapter row itself ({r['n_members']})")
    check(r["query_head"] == QUERY[:120] and len(r["query_head"]) <= 120, "query_head is the first 120 chars")
    check(r["served_ids"] == [f.fragment_id for f in served], "served_ids lists the served set in order")
    check(r["served_cos_median"] is not None and r["served_lex_median"] is not None, "served medians present")
    cands = r["candidates"]
    check(len(cands) == 3, f"3 candidates logged ({len(cands)})")
    check(all(set(c) >= {"fragment_id", "origin", "cos", "lex_overlap", "age_days", "max_cos_to_served"} for c in cands),
          "each candidate has fragment_id, origin, cos, lex_overlap, age_days, max_cos_to_served")
    check([c["cos"] for c in cands] == sorted((c["cos"] for c in cands), reverse=True), "candidates ranked by cosine to the query")
    cid = {c["fragment_id"] for c in cands}
    check("m0029" not in cid, "a member already in the served set is dropped")
    check("mDUP" not in cid and r["n_dropped_neardup"] >= 1, "a member with cosine >= 0.85 to a served fragment is dropped and counted")
    check(r["n_dropped_served"] == 1, f"the already-served member is counted ({r['n_dropped_served']})")
    check(all(c["max_cos_to_served"] < 0.85 for c in cands), "every candidate is under 0.85 to every served fragment")
    check(all(c["age_days"] is not None and c["age_days"] > 90 for c in cands), "age_days is read from the row")
    # the top eligible member should be the best by hand-computed cosine
    with sqlite3.connect(tmp / "d.db") as c:
        mem = {fid: np.frombuffer(b, dtype=np.float32) for fid, b in
               c.execute("SELECT fragment_id, embedding FROM memory_fragments WHERE chapter_id='chap1'")}
    served_vecs = [np.frombuffer(c2, dtype=np.float32) for c2 in
                   [sqlite3.connect(tmp / "d.db").execute("SELECT embedding FROM memory_fragments WHERE fragment_id=?", (f.fragment_id,)).fetchone()[0]
                    for f in served if f.origin != "chapter" or True]]
    elig = {fid: float(v @ QV) for fid, v in mem.items()
            if fid not in {f.fragment_id for f in served} and max(float(v @ s) for s in served_vecs) < 0.85}
    best = max(elig, key=elig.get)
    check(cands[0]["fragment_id"] == best and abs(cands[0]["cos"] - round(elig[best], 4)) < 1e-3,
          f"top candidate is the best eligible member by cosine ({best})")
    cc = r["control_chapter_member"]
    check(cc is not None and set(cc) >= {"fragment_id", "origin", "cos", "lex_overlap", "age_days", "max_cos_to_served"},
          "same-chapter control present with the same fields")
    check(cc is not None and cc["fragment_id"] in mem and cc["fragment_id"] not in cid and cc.get("also_candidate") is False,
          "the same-chapter control is a member of the same chapter, outside the top 3")
    cu = r["control_unwalled"]
    check(cu is not None and cu["origin"] == "lived" and cu["fragment_id"].startswith("p")
          and cu["fragment_id"] not in {f.fragment_id for f in served}, "unwalled control is an unserved unwalled episodic pool row")
    check(cu is not None and abs(cu["cos"] - cands[0]["cos"]) <= CDS.BAND + 1e-3, "unwalled control is in the cosine band of the best candidate")
    check(isinstance(r["ms"], float), "hook latency is logged")
    CDS.shadow_descent(served, QUERY, "cycA", "internal")                 # same cycle again: same random draws
    r2 = rows_of(CDS._LOG)[-1]
    check(r2["control_chapter_member"]["fragment_id"] == cc["fragment_id"]
          and r2["control_unwalled"]["fragment_id"] == cu["fragment_id"], "controls are deterministic per (cycle, chapter)")
    CDS.shadow_descent(served, QUERY, "cycB", "internal")
    r3 = rows_of(CDS._LOG)[-1]
    check(r3["candidates"] == r["candidates"] or r3["candidates"][0]["fragment_id"] == cands[0]["fragment_id"],
          "candidates do not depend on the cycle id (ranking is deterministic)")
    # two chapters in one cycle -> two rows
    before = len(rows_of(CDS._LOG))
    n2 = CDS.shadow_descent(served + [frag("chapEmpty", "chapter", relevance=0.5, layer="archive")], QUERY, "cycTwo", "internal")
    check(n2 == 2 and len(rows_of(CDS._LOG)) == before + 2, "two served chapters -> one row each")
    empty = rows_of(CDS._LOG)[-1]
    check(empty["chapter_id"] == "chapEmpty" and empty["n_members"] == 0 and empty["candidates"] == []
          and empty["control_chapter_member"] is None and empty["control_unwalled"] is None,
          "a chapter with no members logs an empty row, no controls")

    print("== E (d): kill switch, safety ==")
    size = CDS._LOG.stat().st_size
    CDS.CHAPTER_DESCENT_SHADOW = False
    called = []
    real_embed = M._embed
    M._embed = lambda t: called.append(t) or real_embed(t)
    n = CDS.shadow_descent(served, QUERY, "cycOff", "internal")
    CDS.CHAPTER_DESCENT_SHADOW = True
    check(n == 0 and CDS._LOG.stat().st_size == size and not called, "kill switch off: returns 0, writes nothing, embeds nothing")
    M._embed = real_embed
    for bad in ((None, QUERY), ([], QUERY), (served, ""), (served, None), ([object()], QUERY), ("junk", QUERY)):
        try:
            CDS.shadow_descent(bad[0], bad[1], "cycBad", None)
            ok = True
        except Exception:
            ok = False
        check(ok, f"garbage input {type(bad[0]).__name__}/{bad[1]!r:.12} never raises")
    M._embed = lambda t: (_ for _ in ()).throw(RuntimeError("boom"))
    try:
        CDS.shadow_descent(served, QUERY, "cycBoom", None)
        ok = True
    except Exception:
        ok = False
    M._embed = real_embed
    check(ok, "a raising embedder never raises out of the hook")
    # a pool that is not serving -> the unwalled control is null, the rest still logs
    M._POOL_DELTA_MODE = "off"
    CDS.shadow_descent(served, QUERY, "cycNoPool", None)
    rn = rows_of(CDS._LOG)[-1]
    M._POOL_DELTA_MODE = "on"
    check(rn["cycle_id"] == "cycNoPool" and rn["control_unwalled"] is None and len(rn["candidates"]) == 3,
          "pool view not serving -> control_unwalled null, candidates unaffected")
    # the write fence: a non-live process pointed at the default data/ path is refused (swallowed), nothing written
    default_log = TREE / "data" / "chapter_descent_shadow.jsonl"
    keep = CDS._LOG
    existed = default_log.exists()
    CDS._LOG = default_log
    try:
        n = CDS.shadow_descent(served, QUERY, "cycFence", None)
    finally:
        CDS._LOG = keep
    check(n == 0 and default_log.exists() == existed, "write fence: a non-live process cannot write under data/ (0 rows, no file)")

    print("== F: reader ==")
    out = subprocess.run([sys.executable, str(TREE / "scripts" / "chapter_descent_summary.py"), "--log", str(CDS._LOG),
                          "--served-log", str(tmp / "none.jsonl")], capture_output=True, text=True, encoding="utf-8")
    check(out.returncode == 0 and "chapter-descent shadow:" in out.stdout and "m5_self_loop_share" in out.stdout,
          "scripts/chapter_descent_summary.py runs on the log and prints the M1/M2/M5/cost inputs")
    out2 = subprocess.run([sys.executable, str(TREE / "scripts" / "chapter_descent_summary.py"), "--log", str(tmp / "absent.jsonl")],
                          capture_output=True, text=True, encoding="utf-8")
    check(out2.returncode == 0 and "no log at" in out2.stdout, "reader copes with an absent log")


def perf(tmp: Path) -> None:
    print("== --perf: 1,845-member chapter, 20k-row pool ==")
    M.DB_PATH = tmp / "perf.db"
    M._embed = fake_embed
    M._emb_reset()
    M._pool_invalidate()
    M._POOL_DELTA_MODE = "on"
    M.init_db()
    rs = np.random.RandomState(1)
    now = time.time()
    with sqlite3.connect(tmp / "perf.db") as c:
        def ins(fid, layer, origin, chap, vec, cold):
            c.execute("""INSERT INTO memory_fragments (fragment_id, content, layer, relevance, timestamp, embedding, origin,
                         chapter_id, cold, temp, importance, keywords, chapter_level) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                      (fid, "river soil cliff content " + fid, layer, 0.5, now - 86400, vec.tobytes(), origin, chap, cold, "warm", 0.5, "", 1 if origin == "chapter" else 0))
        ins("bigchap", "archive", "chapter", None, vec_near(QV, 0.9, rs), 0)
        for i in range(1845):
            ins(f"bm{i}", "episodic", "inner_thought", "bigchap", vec_near(QV, 0.05 + 1.2 * i / 1845, rs), 1)
        for i in range(20000):
            ins(f"pp{i}", "episodic", "lived", None, vec_near(QV, rs.rand(), rs) if i % 7 == 0 else _unit(rs.randn(DIM)), 0)
    M.retrieve(["river"], [], time_bias="recent", query_text=QUERY)
    CDS._LOG = tmp / "perf.jsonl"
    served = [frag("bigchap", "chapter", relevance=0.7, layer="archive"), frag("pp0"), frag("pp7"), frag("pp14")]
    CDS.shadow_descent(served, QUERY, "warm", None)
    ts = []
    for i in range(7):
        t0 = time.perf_counter()
        CDS.shadow_descent(served, QUERY, f"perf{i}", None)
        ts.append((time.perf_counter() - t0) * 1000.0)
    logged = [r["ms"] for r in rows_of(CDS._LOG)[1:]]
    print(f"  wall per call (ms): median {sorted(ts)[len(ts)//2]:.1f}, max {max(ts):.1f}; logged row ms: median {sorted(logged)[len(logged)//2]:.1f}, max {max(logged):.1f}")
    r = rows_of(CDS._LOG)[-1]
    print(f"  n_members {r['n_members']}, candidates {len(r['candidates'])}, control_unwalled {'yes' if r['control_unwalled'] else 'no'}")


def quiet_side_channels() -> None:
    """retrieve() has observe-only side channels that append to data/ logs; null them so nothing leaves the tempdir."""
    M._log_retrieve_latency = lambda *a, **k: None
    from core import retrieval_probe as rp, r_shadow as rs
    rp.observe = lambda *a, **k: None
    rs.log_observation = lambda *a, **k: None


def main() -> int:
    quiet_side_channels()
    static_checks()
    with tempfile.TemporaryDirectory(prefix="J3319_", ignore_cleanup_errors=True) as t:
        tmp = Path(t)
        behaviour_checks(tmp)
        if "--perf" in sys.argv:
            perf(tmp)
    print(f"\n{'ALL OK' if not _fails else str(_fails) + ' FAILED'}")
    return 0 if not _fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
