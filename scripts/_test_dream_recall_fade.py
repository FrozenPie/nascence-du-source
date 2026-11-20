"""Offline regression test for J-3175 (D-0563 / F-3566): the dreamer's recall skips dream-origin fragments younger
than 7 days (core.night.DREAM_RECALL_EXCLUDE_DAYS) via the opt-in `exclude_young` argument on
associative_recall.recall_fragments / memory_service.ask.

Proves, on a synthetic matrix (no live store read), against the pre-change modules loaded from `git show e0602f43:`
(the commit just before J-3175 on this branch):
  1. exclude_young=None (and absent) == pre-change recall_fragments / ask(), exactly (many queries, k=6, grounded_only=False);
  2. exclude_young={'dream': 7} returns NO dream fragment younger than 7 days, still returns dream fragments 7+ days
     old, never touches non-dream fragments (they keep their relative trail order), and still fills k=6 where the
     trail allows (k unchanged);
  3. ask("dream", ..., exclude_young=...) passes it through to the what-slot, and the recency shadow (flag on)
     compares like with like (its with/without ids also contain no young dream);
  4. dream_node passes exclude_young={'dream': night.DREAM_RECALL_EXCLUDE_DAYS} at the memory_service.ask("dream") call
     and the constant is 7.0.
Runs under lab_env.isolate(db="empty") with the lab root under a temp dir (never C:\\Nascence\\data).
Run: python scripts/_test_dream_recall_fade.py [lab_root]   (exit 0 = all pass)"""
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789: no write to the tree's data/
import importlib.util, json, subprocess, sys, tempfile, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import numpy as np
from core import associative_recall as ar          # core BEFORE lab_env
from core import memory_service as ms
from core import night
from core.memory import store
assert Path(ar.__file__).resolve().is_relative_to(ROOT), ar.__file__
sys.path.insert(0, r"C:\Users\USER\.claude\skills\job-queue")
import lab_env

FAILS = []
def check(label, cond):
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond: FAILS.append(label)

tmp = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(tempfile.mkdtemp(prefix="j3175_"))
tmp.mkdir(parents=True, exist_ok=True)
lab_env._LAB_ROOT = tmp / "lab"
lab_env._ISOLATE_OUTCOMES_LOG = tmp / "lab" / "_isolate_outcomes.jsonl"

BASE = "e0602f43"
def load_head(path, name):
    src = subprocess.run(["git", "show", f"{BASE}:{path}"], cwd=ROOT, capture_output=True, text=True,
                         encoding="utf-8", check=True).stdout
    f = tmp / f"{name}.py"; f.write_text(src, encoding="utf-8")
    spec = importlib.util.spec_from_file_location(name, f)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return src, m
ar_src, ar_head = load_head("core/associative_recall.py", "ar_head_j3175")
ms_src, ms_head = load_head("core/memory_service.py", "ms_head_j3175")
check("baseline modules have no exclude_young (genuinely pre-change)", "exclude_young" not in ar_src and "exclude_young" not in ms_src)

rng = np.random.default_rng(3175)
N, D = 500, 24
M = rng.normal(size=(N, D)).astype(np.float32)
M /= np.linalg.norm(M, axis=1, keepdims=True)
for i in range(0, 200, 5):                      # near-duplicate clusters so a trail has many close members
    for j in range(1, 4):
        v = M[i] + 0.03 * rng.normal(size=D).astype(np.float32); M[i + j] = v / np.linalg.norm(v)
ids = [f"f{i:04d}" for i in range(N)]
ORIG = [["lived", "dream", "reading", "dream", "gist"][i % 5] for i in range(N)]
NOW = time.time()
# dream rows: even-numbered ones 1 day old (young), odd-numbered 10 days old (old enough); others 3 days old
AGE_D = [(1.0 if (i // 5) % 2 == 0 else 10.0) if ORIG[i] == "dream" else 3.0 for i in range(N)]
CACHE = dict(ts=1e18, M=M, ids=ids, imp=rng.uniform(0.2, 1.0, N).astype(np.float32),
             age=np.array(AGE_D, dtype=np.float32), walled=(rng.uniform(size=N) < 0.1),
             origin=ORIG, self_gist=(rng.uniform(size=N) < 0.08))
def fake_matrix(): return dict(CACHE)
ROWS = {fid: {"content": f"content of {fid}", "origin": ORIG[i], "timestamp": NOW - AGE_D[i] * 86400.0}
        for i, fid in enumerate(ids)}
def fake_rows(want): return {f: ROWS[f] for f in want if f in ROWS}
queries = [(M[i] + 0.05 * rng.normal(size=D)).astype(np.float32) for i in range(0, 200, 7)]
texts = [f"cue {i}" for i in range(len(queries))]
def fake_embed(t): return queries[texts.index(t)] if t in texts else None
def canon(x): return json.dumps(x, sort_keys=True, default=str)
def young_dreams(frs): return [f for f in frs if f["origin"] == "dream" and ROWS[f["fragment_id"]]["timestamp"] > NOW - 7 * 86400.0]

with lab_env.isolate(db="empty", also=[(ms, ["_RECENCY_SHADOW_LOG", "_SHADOW_LOG"]), (ar, ["_SEED_SHARE_LOG"]),
                                       (ar_head, ["_SEED_SHARE_LOG"]), (ms_head, ["_RECENCY_SHADOW_LOG", "_SHADOW_LOG"])]) as lab:
    for m in (ar, ar_head):
        m._matrix = fake_matrix; m._load_rows = fake_rows
    store._embed = fake_embed
    ar.CEILING = ar_head.CEILING

    print("[1] default (absent / None) == pre-change")
    check("recall_fragments absent == HEAD on all queries", all(
        canon(ar.recall_fragments(t, k=6, grounded_only=False)) == canon(ar_head.recall_fragments(t, k=6, grounded_only=False)) for t in texts))
    check("recall_fragments exclude_young=None == HEAD", all(
        canon(ar.recall_fragments(t, k=6, grounded_only=False, exclude_young=None)) == canon(ar_head.recall_fragments(t, k=6, grounded_only=False)) for t in texts))
    ms.ASK_RECENCY_SHADOW = False; ms_head.ASK_RECENCY_SHADOW = False
    # ask() lazily imports core.associative_recall (the NEW module), so its default pool is checked against itself
    # with exclude_young=None; the recall_fragments equality above is the byte-for-byte HEAD comparison.
    check("ask() absent == ask(exclude_young=None) pool", all(
        canon(ms.ask("dream", t, k=6, grounded_only=False)) == canon(ms.ask("dream", t, k=6, grounded_only=False, exclude_young=None)) for t in texts))
    base_has_young = sum(bool(young_dreams(ar.recall_fragments(t, k=6, grounded_only=False))) for t in texts)
    check(f"synthetic default recall DOES surface young dreams ({base_has_young}/{len(texts)} queries) -- test not vacuous", base_has_young >= len(texts) // 2)

    print("[2] exclude_young={'dream': 7}")
    EX = {"dream": 7.0}
    outs = {t: ar.recall_fragments(t, k=6, grounded_only=False, exclude_young=EX) for t in texts}
    check("no young dream in any result", all(not young_dreams(v) for v in outs.values()))
    check("old (10 d) dreams still surface somewhere (not excluded entirely)",
          any(f["origin"] == "dream" for v in outs.values() for f in v))
    check("k filled: every query returns 6", all(len(v) == 6 for v in outs.values()))
    # non-dream fragments keep their relative order versus the unfiltered list
    ok_order = True
    for t in texts:
        full = ar.recall_fragments(t, k=15, grounded_only=False)
        keep = [f["fragment_id"] for f in full if not (f["origin"] == "dream" and f in young_dreams(full))]
        got = [f["fragment_id"] for f in outs[t]]
        ok_order &= (got == keep[:len(got)])
    check("result == unfiltered trail minus young dreams, same order", ok_order)
    check("other origins untouched: exclude_young={'reading': 0} == default", all(
        canon(ar.recall_fragments(t, k=6, grounded_only=False, exclude_young={"reading": 0})) ==
        canon(ar.recall_fragments(t, k=6, grounded_only=False)) for t in texts))
    ROWS_BAK = dict(ROWS["f0001"])
    del ROWS["f0001"]["timestamp"]
    check("a row with no readable timestamp is kept, not crashed on",
          isinstance(ar.recall_fragments(texts[0], k=6, grounded_only=False, exclude_young=EX), list))
    ROWS["f0001"].update(ROWS_BAK)

    print("[3] ask() passes it through; shadow compares like with like")
    ms.ASK_RECENCY_SHADOW = True
    pools = [ms.ask("dream", t, k=6, grounded_only=False, descend=False, exclude_young=EX) for t in texts]
    check("ask pools carry no young dream", all(not young_dreams(p) for p in pools))
    check("ask pools == recall_fragments(exclude_young) ids", all(
        [f["fragment_id"] for f in p] == [f["fragment_id"] for f in outs[t]] for p, t in zip(pools, texts)))
    check("ask pools are full (k=6)", all(len(p) == 6 for p in pools))
    shadow = Path(ms._RECENCY_SHADOW_LOG)
    rows = [json.loads(l) for l in shadow.read_text(encoding="utf-8").splitlines()]
    check("shadow wrote one row per ask", len(rows) == len(texts))
    check("shadow with_ids/without_ids contain no young dream", all(
        all(not (ORIG[ids.index(f)] == "dream" and AGE_D[ids.index(f)] < 7.0) for f in r["with_ids"] + r["without_ids"]) for r in rows))
    ms.ASK_RECENCY_SHADOW = False

print("[4] wiring")
dn = (ROOT / "nodes" / "dream_node.py").read_text(encoding="utf-8")
check("dream_node passes exclude_young at the ask('dream') call",
      'exclude_young={"dream": _night.DREAM_RECALL_EXCLUDE_DAYS}' in dn and '_pre_probe_call(_memsvc.ask, "dream"' in dn)
check("DREAM_RECALL_EXCLUDE_DAYS == 7.0 and DREAM_COLD_HOURS still 72.0", night.DREAM_RECALL_EXCLUDE_DAYS == 7.0 and night.DREAM_COLD_HOURS == 72.0)
check("no other live caller of ask()/recall_fragments passes exclude_young", all(
    "exclude_young" not in (ROOT / p).read_text(encoding="utf-8") for p in ("nodes/inner_monologue_node.py", "nodes/curiosity_node.py") if (ROOT / p).exists()))

print("\nALL PASSED" if not FAILS else f"\n{len(FAILS)} FAILED: {FAILS}")
sys.exit(1 if FAILS else 0)
