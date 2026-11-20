"""
Offline regression test for J-2350 / D-0472 ruling A (on F-2943): Lens 3 counterfactual consensus now RE-RANKS
the trail's own items (core.associative_recall.LENS3_RERANK = "seed_blend_v1"), shadow-only.

D-0170's shadow-only law: what orchestrator._retrieve_memory returns live must not change. This test proves it
two ways, against the HEAD version of core/associative_recall.py loaded side by side as a separate module
(`git show 34a9bdd5:core/associative_recall.py`, a pinned pre-J-2350 commit -- HEAD now carries J-2350 itself), on one synthetic fixture injected identically into both:

  0 premise    core imported from this tree; the HEAD copy really is the pre-J-2350 code (no LENS3_RERANK)
  1 static     the only top-level functions whose source differs from HEAD are recall_trail_counterfactual_consensus
               and shadow_compare_lens3; nothing but shadow_compare_lens3 calls the former; orchestrator's only
               Lens 3 reference is the awaited, unassigned shadow_compare_lens3 call (its return is discarded)
  2 live path  the _retrieve_memory associative sequence (recall_memory_fragments, then the M2/Lens 1/2/3 shadow
               calls, then recall_memory_fragments again) plus recall_trail / recall_fragments return BYTE-IDENTICAL
               serialisations from HEAD and from this tree, before and after the shadow calls
  3 off-switch LENS3_RERANK="off" reproduces HEAD's recall_trail_counterfactual_consensus byte-for-byte
  4 re-rank    with the default "seed_blend_v1", the #1 slot moves on >=1 fixture query (it never can on HEAD)
  5 log row    shadow_compare_lens3 writes one row to a TEMP log carrying rerank / rerank_w / energy_norm /
               top1_changed, and does not mutate the caller's id list
  6 latency    the re-rank's added cost per Lens 3 call (median over the fixture queries) is reported and bounded
  7 audit      a sys.addaudithook saw zero write-mode opens / sqlite connects under C:\\Nascence\\data or this
               tree's data/ for the whole run

Never loads an embedder or model (store._embed is replaced by a deterministic hash embedding), never reads or
writes live data/. Run: python scripts/_test_j2350_lens3_rerank_shadow_only.py   (exit 0 = all passed)
"""
import ast
import hashlib
import importlib.util
import json
import os
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TREE))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REAL_ROOTS = [os.path.normcase(str(Path(r"C:\Nascence\data").resolve())), os.path.normcase(str(TREE / "data"))]
HOOK_EVENTS: list = []
_busy = threading.local()


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
            (isinstance(fl, int) and bool(fl & (os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC)))
        if not w:
            return
        path = _norm(args[0])
    elif event == "sqlite3.connect":
        path = _norm(args[0])
    elif event in ("os.rename", "os.replace", "os.remove", "os.mkdir"):
        path = _norm(args[0])
    else:
        return
    if not _is_real(path):
        return
    _busy.on = True
    try:
        HOOK_EVENTS.append({"event": event, "path": path})
    finally:
        _busy.on = False
    raise PermissionError(f"J-2350 test hook: blocked real-data {event} {path}")


sys.addaudithook(_hook)

import core  # noqa: E402  -- BEFORE anything else from the tree (no lab_env used here at all)
assert str(Path(core.__file__).resolve()).lower().startswith(str(TREE).lower()), core.__file__

import numpy as np                      # noqa: E402
import core.associative_recall as NEW   # noqa: E402
import core.memory.store as S           # noqa: E402
import core.memory_edges as ME          # noqa: E402

results = []


def check(name, cond, detail=""):
    results.append((name, bool(cond)))
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"  -- {detail}" if (detail and not cond) else ""))


TMP = Path(tempfile.mkdtemp(prefix="j2350_lens3_"))
BASELINE_REV = "34a9bdd5"  # pinned pre-J-2350 commit (J-2358): HEAD now carries J-2350 itself
head_src = subprocess.run(["git", "-C", str(TREE), "show", BASELINE_REV + ":core/associative_recall.py"],
                          capture_output=True, text=True, encoding="utf-8", check=True).stdout
head_path = TMP / "associative_recall_head_J2350.py"
head_path.write_text(head_src, encoding="utf-8")
_spec = importlib.util.spec_from_file_location("core._associative_recall_head_j2350", head_path)
HEAD = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(HEAD)

# ── fixture: 600 fragments, 12 clusters, deterministic ──────────────────────────────────────────────────────────
N, DIM, K = 600, 32, 12
rng = np.random.default_rng(2350)
centers = rng.standard_normal((K, DIM)).astype(np.float32)
lab = rng.integers(0, K, N)
Mx = centers[lab] + 0.55 * rng.standard_normal((N, DIM)).astype(np.float32)
Mx /= np.linalg.norm(Mx, axis=1, keepdims=True)
IDS = [f"frag{i:04d}" for i in range(N)]
ORIGINS = ["lived", "reading", "gist", "dream", "action", "study"]
NOW = time.time()
CACHE = dict(ts=NOW + 10 ** 7, M=Mx, ids=IDS,
             imp=rng.uniform(0.2, 0.95, N).astype(np.float32),
             age=rng.uniform(0.0, 60.0, N).astype(np.float32),
             walled=(rng.uniform(0, 1, N) < 0.15),
             origin=[ORIGINS[int(x)] for x in rng.integers(0, len(ORIGINS), N)],
             self_gist=np.zeros(N, dtype=bool))
ROWS = {fid: {"fragment_id": fid, "content": f"content of {fid}", "layer": "active", "timestamp": NOW - i,
              "origin": CACHE["origin"][i], "abstraction_level": 0} for i, fid in enumerate(IDS)}
fact = rng.standard_normal((2, DIM)).astype(np.float32)
fact /= np.linalg.norm(fact, axis=1, keepdims=True)


def fake_embed(text):
    h = int(hashlib.sha256((text or "").encode("utf-8")).hexdigest(), 16)
    r = np.random.default_rng(h % (2 ** 32))
    v = centers[h % K] + 0.6 * r.standard_normal(DIM)
    return (v / np.linalg.norm(v)).astype(np.float32).tolist()


def fake_edge_neighbors(seed_ids, mode="task", limit=8):
    out = []
    for s in seed_ids:
        i = int(s[4:])
        for j in (i + 7, i + 13):
            out.append({"fragment_id": IDS[j % N], "weight": 0.5})
    return out[:limit]


S._embed = fake_embed
_orig_edge = ME.edge_aware_neighbors
ME.edge_aware_neighbors = fake_edge_neighbors


def prep(mod):
    mod._cache.clear()
    mod._cache.update({k: v for k, v in CACHE.items()})
    mod._fact_embed_cache.clear()
    mod._fact_embed_cache.update(day=fact[0], night=fact[1])
    mod._load_rows = lambda ids: {f: ROWS[f] for f in ids if f in ROWS}
    d = TMP / mod.__name__.replace(".", "_")
    d.mkdir(exist_ok=True)
    for attr in ("_LOG", "_LENS1_LOG", "_LENS2_LOG", "_LENS3_LOG", "_SEED_SHARE_LOG", "_EMB_CACHE"):
        setattr(mod, attr, d / Path(getattr(mod, attr)).name)
    return d


DIR_NEW, DIR_HEAD = prep(NEW), prep(HEAD)
QUERIES = [f"fixture query {i} about cluster things" for i in range(25)]


def ser_frags(frags):
    return json.dumps([{k: getattr(f, k, None) for k in ("fragment_id", "content", "layer", "relevance", "timestamp",
                                                          "origin", "abstraction_level")} for f in frags],
                      sort_keys=True, default=str)


def ser(x):
    return json.dumps(x, sort_keys=True, default=str)


try:
    print("\n=== J-2350 / D-0472 A -- Lens 3 re-rank is shadow-only (HEAD vs tree, offline fixture) ===\n")
    print("0. Premise")
    check("core imported from the tree under test", Path(core.__file__).resolve().parent.parent == TREE, core.__file__)
    check("tree module defines LENS3_RERANK = 'seed_blend_v1'", getattr(NEW, "LENS3_RERANK", None) == "seed_blend_v1")
    check("pinned baseline (34a9bdd5) is pre-J-2350 (no LENS3_RERANK)", not hasattr(HEAD, "LENS3_RERANK"))

    print("\n1. Static: what changed, and who can reach it")
    t_new, t_head = ast.parse((TREE / "core" / "associative_recall.py").read_text(encoding="utf-8")), ast.parse(head_src)
    def fns(tree, src):
        return {n.name: ast.get_source_segment(src, n) for n in tree.body if isinstance(n, ast.FunctionDef)}
    f_new = fns(t_new, (TREE / "core" / "associative_recall.py").read_text(encoding="utf-8"))
    f_head = fns(t_head, head_src)
    changed = sorted(n for n in set(f_new) | set(f_head) if f_new.get(n) != f_head.get(n))
    # J-3525 / F-4136: the baseline is pinned pre-J-2350, so later deliberate merges (J-2659, J-3173, J-3175, J-3191,
    # J-3200, J-3507, J-3970 ...) legitimately differ too. The invariant is not "nothing else changed" but "the Lens 3
    # re-rank touched only the two Lens 3 functions": both differ, and no OTHER changed function mentions the re-rank.
    LENS3 = {"recall_trail_counterfactual_consensus", "shadow_compare_lens3"}
    leaked = sorted(n for n in changed if n not in LENS3 and f_new.get(n)
                    and ("LENS3_RERANK" in f_new[n] or "recall_trail_counterfactual_consensus(" in f_new[n]))
    check("Lens 3 functions differ from pinned baseline; no other changed function references the re-rank",
          LENS3 <= set(changed) and not leaked, (changed, leaked))
    callers = sorted(n for n, src in f_new.items()
                     if n != "recall_trail_counterfactual_consensus" and "recall_trail_counterfactual_consensus(" in src)
    check("recall_trail_counterfactual_consensus called only from shadow_compare_lens3", callers == ["shadow_compare_lens3"],
          callers)
    orch = (TREE / "core" / "orchestrator.py").read_text(encoding="utf-8")
    l3 = [ln.strip() for ln in orch.splitlines() if "lens3" in ln.lower() and "_ar." in ln]
    check("orchestrator's only Lens 3 call is an awaited, unassigned shadow_compare_lens3",
          l3 == ["await asyncio.to_thread(_ar.shadow_compare_lens3, query_text, _cur_ids)"], l3)
    check("orchestrator never references recall_trail_counterfactual_consensus",
          "recall_trail_counterfactual_consensus" not in orch)

    print("\n2. Live path byte-identical, HEAD vs tree, before and after the shadow calls")
    bad = []
    for q in QUERIES:
        qv = fake_embed(q)
        out = {}
        for tag, mod in (("head", HEAD), ("new", NEW)):
            before = (ser_frags(mod.recall_memory_fragments(q)), ser(mod.recall_trail(qv)), ser(mod.recall_fragments(q)))
            cur = [f.fragment_id for f in mod.recall_memory_fragments(q)][:9]
            cur_copy = list(cur)
            for sc in (mod.shadow_compare, mod.shadow_compare_lens1, mod.shadow_compare_lens2, mod.shadow_compare_lens3):
                sc(q, cur)
            after = (ser_frags(mod.recall_memory_fragments(q)), ser(mod.recall_trail(qv)), ser(mod.recall_fragments(q)))
            out[tag] = (before, after, cur == cur_copy)
        if not (out["head"][0] == out["new"][0] == out["head"][1] == out["new"][1]) or not out["new"][2]:
            bad.append(q)
    check(f"recall_memory_fragments / recall_trail / recall_fragments identical on {len(QUERIES)} queries", not bad, bad[:3])
    nonempty = sum(1 for q in QUERIES if NEW.recall_memory_fragments(q))
    check("the live path is exercised (non-empty recall on most queries)", nonempty >= len(QUERIES) // 2,
          f"{nonempty}/{len(QUERIES)}")

    print("\n3. LENS3_RERANK='off' reproduces HEAD's Lens 3 exactly")
    NEW.LENS3_RERANK = "off"
    diff = [q for q in QUERIES if ser(NEW.recall_trail_counterfactual_consensus(fake_embed(q), now=NOW))
            != ser(HEAD.recall_trail_counterfactual_consensus(fake_embed(q), now=NOW))]
    check("off == HEAD on every fixture query", not diff, diff[:3])
    NEW.LENS3_RERANK = "seed_blend_v1"

    print("\n4. With the re-rank on, the #1 slot can move (never on HEAD)")
    moved_new = moved_head = 0
    for q in QUERIES:
        qv = fake_embed(q)
        tr = NEW.recall_trail(qv)
        if not tr:
            continue
        rn = NEW.recall_trail_counterfactual_consensus(qv, base=tr, now=NOW)
        rh = HEAD.recall_trail_counterfactual_consensus(qv, base=tr, now=NOW)
        moved_new += bool(rn and rn[0]["fragment_id"] != tr[0]["fragment_id"])
        moved_head += bool(rh and rh[0]["fragment_id"] != tr[0]["fragment_id"])
    print(f"     top1 moved: tree {moved_new}/{len(QUERIES)}, HEAD {moved_head}/{len(QUERIES)}")
    check("tree: top1 moves on >=1 fixture query", moved_new >= 1, moved_new)
    check("HEAD: top1 never moves (the F-2943 structural zero)", moved_head == 0, moved_head)

    print("\n5. Lens 3 shadow row: temp log, tagged, caller ids untouched")
    log3 = NEW._LENS3_LOG
    rows = [json.loads(x) for x in log3.read_text(encoding="utf-8").splitlines() if x.strip()] if log3.exists() else []
    check("rows went to the TEMP Lens 3 log", len(rows) == len(QUERIES) and str(log3).startswith(str(TMP)),
          f"{len(rows)} rows at {log3}")
    keys_ok = all({"rerank", "rerank_w", "energy_norm", "top1_changed"} <= set(r) for r in rows)
    check("every row carries rerank / rerank_w / energy_norm / top1_changed", keys_ok and rows)
    check("rows tagged seed_blend_v1, w=LENS3_RERANK_W", all(r.get("rerank") == "seed_blend_v1" and
                                                             r.get("rerank_w") == NEW.LENS3_RERANK_W for r in rows))
    print(f"     logged top1_changed: {sum(1 for r in rows if r['top1_changed'])}/{len(rows)}")

    print("\n6. Latency: added cost of the re-rank per Lens 3 call")
    def timed(mode):
        NEW.LENS3_RERANK = mode
        ts = []
        for q in QUERIES:
            qv = fake_embed(q)
            tr = NEW.recall_trail(qv)
            t0 = time.perf_counter()
            NEW.recall_trail_counterfactual_consensus(qv, base=tr, now=NOW)
            ts.append(time.perf_counter() - t0)
        return statistics.median(ts)
    timed("off")
    m_off, m_on = timed("off"), timed("seed_blend_v1")
    NEW.LENS3_RERANK = "seed_blend_v1"
    print(f"     median ms: off {1000 * m_off:.2f}, seed_blend_v1 {1000 * m_on:.2f}")
    check("re-rank adds < 2 ms median per Lens 3 call", (m_on - m_off) < 0.002, f"{1000 * (m_on - m_off):.2f} ms")
finally:
    ME.edge_aware_neighbors = _orig_edge
    import shutil
    shutil.rmtree(TMP, ignore_errors=True)

print("\n7. Audit hook")
check("zero real-tree write/connect events during the whole run", not HOOK_EVENTS, HOOK_EVENTS[:5])

passed = sum(1 for _, ok in results if ok)
print(f"\n=== {passed}/{len(results)} passed ===")
sys.exit(0 if passed == len(results) else 1)
