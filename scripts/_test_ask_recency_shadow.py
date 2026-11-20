"""Offline regression test for J-2659 (F-3403 / D-0528 open): the opt-in `recency` argument on
associative_recall.recall_trail / recall_fragments / memory_service.ask, and ask()'s with/without-multiplier
SHADOW row (data/ask_recency_shadow.jsonl).

Proves, on a synthetic matrix (no live store read), against the pre-change module loaded from `git show a45b6dbe:` (master just before the J-2659 merge; HEAD is post-change once merged):
  1. default recall_trail / recall_fragments == pre-change, exactly (many queries);
  2. recency=False == the J-2652 probe's monkeypatch (age := 1e6 d), exactly, and differs from default somewhere;
  3. ask() returns the identical pool with the shadow flag on and off; flag off writes no shadow file;
     recency=False writes none; flag on writes one row per what-slot ask with the briefed fields;
  4. the seed-share shadow counter gets ONE row per ask, not two (the comparison call skips it).
Runs under lab_env.isolate(db="empty") with the lab root under a temp dir (never C:\\Nascence\\data).
Run: python scripts/_test_ask_recency_shadow.py [lab_root]   (exit 0 = all pass)"""
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789: no write to the tree's data/
import importlib.util, json, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import numpy as np
from core import associative_recall as ar          # core BEFORE lab_env
from core import memory_service as ms
from core.memory import store
assert Path(ar.__file__).resolve().is_relative_to(ROOT), ar.__file__
sys.path.insert(0, r"C:\Users\USER\.claude\skills\job-queue")
import lab_env

FAILS = []
def check(label, cond):
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond: FAILS.append(label)

tmp = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(tempfile.mkdtemp(prefix="j2659_"))
tmp.mkdir(parents=True, exist_ok=True)
lab_env._LAB_ROOT = tmp / "lab"
lab_env._ISOLATE_OUTCOMES_LOG = tmp / "lab" / "_isolate_outcomes.jsonl"

# pre-change module, loaded from HEAD under another name
head_src = subprocess.run(["git", "show", "a45b6dbe:core/associative_recall.py"], cwd=ROOT, capture_output=True,
                          text=True, encoding="utf-8", check=True).stdout
head_file = tmp / "ar_head.py"
head_file.write_text(head_src, encoding="utf-8")
spec = importlib.util.spec_from_file_location("ar_head", head_file)
ar_head = importlib.util.module_from_spec(spec); spec.loader.exec_module(ar_head)
check("a45b6dbe module has no recency parameter (baseline is genuinely pre-change)", "recency" not in head_src.split("def recall_trail(")[1].split(")")[0])

# synthetic matrix shared by both modules
rng = np.random.default_rng(2659)
N, D = 500, 24
M = rng.normal(size=(N, D)).astype(np.float32)
M /= np.linalg.norm(M, axis=1, keepdims=True)
# near-duplicate clusters so recency can actually break ties
for i in range(0, 200, 5):
    for j in range(1, 4):
        v = M[i] + 0.03 * rng.normal(size=D).astype(np.float32); M[i + j] = v / np.linalg.norm(v)
ids = [f"f{i:04d}" for i in range(N)]
CACHE = dict(ts=1e18, M=M, ids=ids, imp=rng.uniform(0.2, 1.0, N).astype(np.float32),
             age=rng.uniform(0, 40, N).astype(np.float32), walled=(rng.uniform(size=N) < 0.1),
             origin=[["lived", "reading", "gist", "inner_thought"][i % 4] for i in range(N)],
             self_gist=(rng.uniform(size=N) < 0.08))
def fake_matrix(): return dict(CACHE)
ROWS = {fid: {"content": f"content of {fid}", "origin": CACHE["origin"][i]} for i, fid in enumerate(ids)}
def fake_rows(want): return {f: ROWS[f] for f in want if f in ROWS}
queries = [(M[i] + 0.05 * rng.normal(size=D)).astype(np.float32) for i in range(0, 200, 7)]
texts = [f"cue {i}" for i in range(len(queries))]
def fake_embed(t): return queries[texts.index(t)] if t in texts else None

def canon(x): return json.dumps(x, sort_keys=True, default=str)

with lab_env.isolate(db="empty", also=[(ms, ["_RECENCY_SHADOW_LOG", "_SHADOW_LOG"]), (ar, ["_SEED_SHARE_LOG"]),
                                       (ar_head, ["_SEED_SHARE_LOG"])]) as lab:
    ar._matrix = fake_matrix; ar_head._matrix = fake_matrix
    ar._load_rows = fake_rows; ar_head._load_rows = fake_rows
    store._embed = fake_embed
    ar.CEILING = ar_head.CEILING  # same

    print("[1] default recall_trail / recall_fragments identical to pre-change")
    same_t = all(canon(ar.recall_trail(q)) == canon(ar_head.recall_trail(q)) for q in queries)
    check(f"recall_trail default == HEAD on {len(queries)} queries", same_t)
    same_f = all(canon(ar.recall_fragments(t, k=5, grounded_only=True)) == canon(ar_head.recall_fragments(t, k=5, grounded_only=True))
                 for t in texts)
    check("recall_fragments default == HEAD (grounded_only=True, k=5)", same_f)

    print("[2] recency=False == the J-2652 probe monkeypatch (age := 1e6), and is a real change")
    def fake_matrix_noage():
        c = dict(CACHE); c["age"] = np.full_like(c["age"], 1.0e6); return c
    ar_head._matrix = fake_matrix_noage
    off_same = all(canon(ar.recall_trail(q, recency=False)) == canon(ar_head.recall_trail(q)) for q in queries)
    check("recall_trail(recency=False) == HEAD with age:=1e6 on all queries", off_same)
    ar_head._matrix = fake_matrix
    n_diff = sum(canon(ar.recall_trail(q)) != canon(ar.recall_trail(q, recency=False)) for q in queries)
    t1_diff = sum(ar.recall_trail(q)[0]["fragment_id"] != ar.recall_trail(q, recency=False)[0]["fragment_id"] for q in queries)
    check(f"recency on/off differ on {n_diff}/{len(queries)} trails ({t1_diff} top-1s) -- not vacuous", n_diff > 0)

    print("[3] ask(): pool identical flag on/off; shadow file only when on and recency default")
    seed_log = Path(ar._SEED_SHARE_LOG); shadow = Path(ms._RECENCY_SHADOW_LOG)
    def nrows(p): return len(p.read_text(encoding="utf-8").splitlines()) if p.exists() else 0
    seed_base = nrows(seed_log)
    ms.ASK_RECENCY_SHADOW = False
    pools_off = [ms.ask("test", t, k=5) for t in texts]
    check("flag OFF: no shadow file written", not shadow.exists())
    seed_off = nrows(seed_log)
    check(f"flag OFF: seed-share log got one row per ask ({seed_off - seed_base} == {len(texts)})", seed_off - seed_base == len(texts))
    ms.ASK_RECENCY_SHADOW = True
    pools_on = [ms.ask("test", t, k=5) for t in texts]
    check("flag ON: ask() pools identical to flag OFF (shadow feeds nothing back)", canon(pools_on) == canon(pools_off))
    check("non-empty pools (test is not vacuous)", all(len(p) > 0 for p in pools_on))
    check(f"flag ON: one shadow row per ask ({nrows(shadow)} == {len(texts)})", nrows(shadow) == len(texts))
    check("flag ON: seed-share log got ONE extra row per ask (not two)", nrows(seed_log) - seed_off == len(texts))
    rows = [json.loads(l) for l in shadow.read_text(encoding="utf-8").splitlines()]
    need = {"ts", "kind", "loop", "cue_hash", "grounded_only", "k", "n_with", "n_without", "with_top1", "without_top1",
            "same_top1", "with_ids", "without_ids", "overlap", "with_top1_rank_in_without"}
    check("row has the briefed fields", all(need <= set(r) for r in rows))
    check("with_top1 == the real ask() top-1", all(r["with_top1"]["fragment_id"] == p[0]["fragment_id"] for r, p in zip(rows, pools_on)))
    check("top-1 entries carry fragment_id/origin/activation/age_days", all(
        {"fragment_id", "origin", "activation", "age_days"} <= set(r["with_top1"]) and r["with_top1"]["age_days"] is not None for r in rows))
    check("without_ids == recall_fragments(recency=False) ids", all(
        r["without_ids"] == [f["fragment_id"] for f in ar.recall_fragments(t, k=5, grounded_only=True, recency=False)]
        for r, t in zip(rows, texts)))
    check("same_top1 flag consistent and some rows diverge", all(r["same_top1"] == (r["with_top1"]["fragment_id"] == r["without_top1"]["fragment_id"]) for r in rows)
          and any(not r["same_top1"] for r in rows))
    check("cue text never stored (hash only)", not any("cue " in json.dumps(r) for r in rows))
    # J-4026: real cue similarity fields
    print("[3b] J-4026 cue-similarity fields")
    qn = [q / np.linalg.norm(q) for q in queries]
    check("rows carry cue_sim fields", all({"cue_sim_with", "cue_sim_without", "cue_sim_sample", "cue_sim_sample_n"} <= set(r) for r in rows))
    ix = {f: i for i, f in enumerate(ids)}
    check("cue_sim_with == true cosine to each served fragment", all(
        all(abs(s - float(M[ix[f]] @ qn[j])) < 1e-3 for s, f in zip(r["cue_sim_with"], r["with_ids"]))
        for j, r in enumerate(rows)))
    check("cue_sim_without aligned to without_ids", all(len(r["cue_sim_without"]) == len(r["without_ids"]) for r in rows))
    check("sample is 200 and drawn only from non-walled fragments' range", all(r["cue_sim_sample_n"] == 200 and len(r["cue_sim_sample"]) == 200 for r in rows)
          and int((~CACHE["walled"]).sum()) >= 200)
    check("no cue text / sample ids stored", not any("cue " in json.dumps(r) for r in rows) and all("cue_sim_sample_ids" not in r for r in rows))
    ms.ASK_RECENCY_SHADOW_CUE_SIM = False
    n0 = nrows(shadow); pools_nc = [ms.ask("test", t, k=5) for t in texts[:3]]
    r_nc = [json.loads(l) for l in shadow.read_text(encoding="utf-8").splitlines()[n0:]]
    check("sub-flag OFF: fields absent, pools unchanged", all("cue_sim_with" not in r for r in r_nc) and canon(pools_nc) == canon(pools_off[:3]))
    ms.ASK_RECENCY_SHADOW_CUE_SIM = True
    before = nrows(shadow)
    p_nr = ms.ask("test", texts[0], k=5, recency=False)
    check("ask(recency=False) writes no shadow row", nrows(shadow) == before)
    check("ask(recency=False) returns the without-multiplier pool", [f["fragment_id"] for f in p_nr] == rows[0]["without_ids"])
    ms.ASK_RECENCY_SHADOW = False

print("\nALL PASSED" if not FAILS else f"\n{len(FAILS)} FAILED: {FAILS}")
sys.exit(1 if FAILS else 0)
