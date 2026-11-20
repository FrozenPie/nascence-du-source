"""scripts/lag_harness/cpu_contention_J1927.py (J-1927, F-2551/F-2552): time, ON THE LOOP THREAD, the real synchronous
statements that wake first after the 1-2 min silent stalls, with and without synthetic CPU contention from
busy_standin_J1927.py processes (started by run_contention_sweep_J1927.sh, never from inside this process: the
_prelude audit hook refuses subprocesses, network and any write under live C:\\Nascence).

Runs from the throwaway worktree $LAGH_SCRATCH/$LAGH_WT on its full-fidelity data copy (copy_data_fullfidelity.py
first). NO MODEL CALLS, no node code: the statements are called directly --
  embed        core.memory.store._embed on real fragment text (the CPU SentenceTransformer, torch pool)
  drift        core.wandering._drift_from: the 1500-row recency pool + numpy cosines (+ co-recall ledger write)
  wander_step  core.wandering.step forced onto its firing path (embed + pool + drift + ledger)
  recall       core.associative_recall.recall_memory_fragments on real text (embed + trail + row loads)
  felt_tick    core.felt_recall.on_substrate_tick (ro sqlite reads, the awake substrate tick's F-2540 class)
  theta_ray    core.theta_shadow.cast_ray (the ro range query the felt_recall edge logs through)
  sql_recent   the step's own 'SELECT embedding ... ORDER BY timestamp DESC LIMIT 40'
  torch_mm     a bare 256x256 torch matmul (the torch intra-op pool alone, no model)
  np_cos1500   a bare 1500x384 @ 384 numpy dot (the cosine loop's shape, OpenBLAS alone)
A 0.5 s canary coroutine records how late a plain timer fires while each statement runs (= loop lag), and a sampler
thread records system CPU %. --cap N sets OMP/MKL/OPENBLAS_NUM_THREADS and torch.set_num_threads(N) before any
heavy import, so the thread-cap arm of the experiment is a real cap.

Usage: python cpu_contention_J1927.py --label idle [--reps 8] [--rounds 2] [--cap N]
Output: $LAGH_SCRATCH/contention_<label>_J-1927.json and a printed table."""
import os, sys, argparse

ap = argparse.ArgumentParser()
ap.add_argument("--label", required=True)
ap.add_argument("--reps", type=int, default=8)
ap.add_argument("--rounds", type=int, default=2)
ap.add_argument("--cap", type=int, default=None)
ap.add_argument("--only", default=None, help="comma list of statement names")
A = ap.parse_args()
if A.cap:
    for k in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
        os.environ[k] = str(A.cap)

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _prelude                                   # audit hook + chdir/sys.path to the throwaway worktree + asserts
from _prelude import SP, WT, store, _NET, _SUBP
import time, json, asyncio, statistics as st, threading, random, collections, pathlib
import numpy as np
import torch
if A.cap:
    torch.set_num_threads(A.cap)
import psutil
from core.schema import CognitiveState
from core import wandering as _wander, felt_recall as _felt, theta_shadow as _theta, associative_recall as _assoc
from core.memory.store import _connect, _embed, _blob_to_vec

assert str(pathlib.Path(_wander.__file__).resolve()).lower().startswith(str(WT).lower()), _wander.__file__

# ---------- real inputs: fixed sample of recent fragment texts (deterministic across conditions) ----------
with _connect() as conn:
    rows = conn.execute("SELECT content FROM memory_fragments WHERE embedding IS NOT NULL AND content IS NOT NULL "
                        "ORDER BY timestamp DESC LIMIT 400").fetchall()
    n_frag = conn.execute("SELECT COUNT(*) FROM memory_fragments").fetchone()[0]
_rng = random.Random(1927)
TEXTS = [r["content"][:300] for r in _rng.sample(rows, 60)]
state = CognitiveState(spirit_name="J1927", axiom="CORE AXIOM: become.")
state.recent_inner_thoughts = [{"ts": time.time(), "thought": TEXTS[0], "mood": "quiet"}]
_seed_vec = None

# ---------- the statements ----------
def s_embed(i):
    _embed(TEXTS[i % len(TEXTS)])

def s_drift(i):
    global _seed_vec
    if _seed_vec is None:
        _seed_vec = _embed(TEXTS[1])
    with _connect() as conn:
        _wander._drift_from(_seed_vec, conn)

def s_wander_step(i):
    _wander._last_wander = 0.0                 # force the firing (wander) path, not the ambient one
    _wander._last_ambient = time.time()
    random.seed(1927 + i)                      # the same roll sequence in every condition
    _wander.step(state)

def s_recall(i):
    _assoc.recall_memory_fragments(TEXTS[(i * 7) % len(TEXTS)])

def s_felt_tick(i):
    _felt.on_substrate_tick(state.affect)

def s_theta_ray(i):
    _theta.cast_ray()

def s_sql_recent(i):
    with _connect() as conn:
        conn.execute("SELECT embedding FROM memory_fragments WHERE embedding IS NOT NULL "
                     "ORDER BY timestamp DESC LIMIT 40").fetchall()

_tA = torch.rand(256, 256); _tB = torch.rand(256, 256)
def s_torch_mm(i):
    (_tA @ _tB).sum().item()

_nA = np.random.default_rng(1).random((1500, 384), dtype=np.float32); _nv = np.ones(384, dtype=np.float32)
def s_np_cos1500(i):
    _nA.dot(_nv)

# breakdown of `drift` (added after sweep 1 showed it 10x slower under 20 busy threads): its two halves apart
_WHERE = ("embedding IS NOT NULL AND layer IN ('episodic','semantic','archive') AND chapter_id IS NULL")
_POOL_ROWS = []
def s_pool_sql(i):
    # the 1500-row recency pool fetch alone (same SQL _drift_from runs when the trail holds <3 inner items)
    global _POOL_ROWS
    with _connect() as conn:
        _POOL_ROWS = _wander._recency_pool(conn, _WHERE)

def s_score_loop(i):
    # the python/numpy half: blob->vec + cosine against the seed for every pool row (no SQL, no ledger)
    from core.memory.store import _cosine
    sv = _seed_vec if _seed_vec is not None else np.ones(384, dtype=np.float32)
    acc = 0.0
    for r in _POOL_ROWS:
        acc += _cosine(sv, _blob_to_vec(r["embedding"]))
    return acc

def s_pool_sql_tsidx(i):
    # the candidate fix: the same pool query forced onto idx_timestamp (walk the newest rows until 1500 eligible
    # ones are found) instead of the planner's idx_chapter choice (every chapter_id-NULL row + a temp-b-tree sort)
    with _connect() as conn:
        conn.execute(f"SELECT fragment_id, content, origin, embedding FROM memory_fragments INDEXED BY idx_timestamp "
                     f"WHERE {_WHERE} ORDER BY timestamp DESC LIMIT 1500").fetchall()

def s_py_spin(i):
    # pure-python control: 2e6 loop iterations, no numpy, no sqlite, no torch
    x = 0
    for k in range(2_000_000): x += k & 7
    return x

STMTS = [("embed", s_embed), ("drift", s_drift), ("wander_step", s_wander_step), ("recall", s_recall),
         ("felt_tick", s_felt_tick), ("theta_ray", s_theta_ray), ("sql_recent", s_sql_recent),
         ("torch_mm", s_torch_mm), ("np_cos1500", s_np_cos1500),
         ("pool_sql", s_pool_sql), ("score_loop", s_score_loop), ("py_spin", s_py_spin),
         ("pool_sql_tsidx", s_pool_sql_tsidx)]
if A.only:
    keep = set(A.only.split(","))
    STMTS = [s for s in STMTS if s[0] in keep]

# ---------- instruments ----------
CAN = []                       # (wall_ts, lag_ms) of a 0.5 s timer
CPU = []                       # (wall_ts, system cpu %) every 1 s
DUR = collections.defaultdict(list)     # name -> [(wall_ts, ms)]
_stop_sampler = threading.Event()

def sampler():
    psutil.cpu_percent(None)
    while not _stop_sampler.is_set():
        time.sleep(1.0)
        CPU.append((time.time(), psutil.cpu_percent(None)))

async def canary(stop, step=0.5):
    while not stop.is_set():
        t = time.perf_counter()
        await asyncio.sleep(step)
        CAN.append((time.time(), (time.perf_counter() - t - step) * 1000))

async def run_statements():
    for rnd in range(A.rounds):
        for name, fn in STMTS:
            for i in range(A.reps):
                await asyncio.sleep(0.05)
                t = time.perf_counter()
                try:
                    fn(rnd * A.reps + i)
                except Exception as exc:
                    print("ERR", name, repr(exc)[:160], flush=True)
                DUR[name].append((time.time(), (time.perf_counter() - t) * 1000))
            print(f"  round {rnd} {name:12s} median {st.median([m for _, m in DUR[name][-A.reps:]]):9.1f} ms "
                  f"max {max(m for _, m in DUR[name][-A.reps:]):9.1f} ms", flush=True)

async def main():
    stop = asyncio.Event()
    c = asyncio.create_task(canary(stop))
    await asyncio.sleep(1.0)
    await run_statements()
    await asyncio.sleep(1.0)
    stop.set(); await c

# warm-up: embedder load, first sqlite opens, caches -- NOT counted
t0 = time.perf_counter()
for name, fn in STMTS:
    try: fn(99)
    except Exception as exc: print("warm err", name, repr(exc)[:160])
print(f"warmup {time.perf_counter() - t0:.1f}s; torch threads {torch.get_num_threads()}; cap {A.cap}; "
      f"fragments {n_frag}; texts {len(TEXTS)}", flush=True)

busy = []
for p in psutil.process_iter(["pid", "cmdline"]):
    try:
        cl = " ".join(p.info["cmdline"] or [])
        if "busy_standin_J1927" in cl: busy.append(cl.split("busy_standin_J1927.py", 1)[1].strip())
    except Exception: pass
print("busy stand-ins seen:", busy, flush=True)

th = threading.Thread(target=sampler, daemon=True); th.start()
t_run = time.time()
_loop = asyncio.new_event_loop(); asyncio.set_event_loop(_loop)
_NET["block"] = True
try:
    _loop.run_until_complete(main())
finally:
    _NET["block"] = False; _loop.close(); _stop_sampler.set()
t_end = time.time()

def summ(xs):
    if not xs: return None
    xs = sorted(xs)
    return {"n": len(xs), "mean": round(st.mean(xs), 2), "median": round(st.median(xs), 2),
            "p90": round(xs[int(.9 * (len(xs) - 1))], 2), "max": round(xs[-1], 2), "sum": round(sum(xs), 1)}

def canary_during(name):
    # worst canary lag whose timer window overlaps a call of `name`
    worst = 0.0
    for ts, ms in DUR[name]:
        lo, hi = ts - ms / 1000, ts
        for cts, lag in CAN:
            if lo - 0.6 <= cts <= hi + 0.6: worst = max(worst, lag)
    return round(worst, 1)

res = {"label": A.label, "cap": A.cap, "torch_threads": torch.get_num_threads(), "cpu_count": os.cpu_count(),
       "busy_standins": busy, "reps": A.reps, "rounds": A.rounds, "start": t_run, "end": t_end,
       "cpu_pct": summ([c for _, c in CPU]), "canary_lag_ms": summ([l for _, l in CAN]),
       "statements": {n: dict(summ([m for _, m in v]), canary_worst_ms=canary_during(n)) for n, v in DUR.items()},
       "raw": {n: [round(m, 1) for _, m in v] for n, v in DUR.items()}, "subprocess_attempts": _SUBP[:5]}
OUT = SP / f"contention_{A.label}_J-1927.json"
OUT.write_text(json.dumps(res, indent=1))
print(f"\n== {A.label}: cap={A.cap} torch_threads={res['torch_threads']} busy={busy} cpu%={res['cpu_pct']} "
      f"canary={res['canary_lag_ms']}")
print(f"{'statement':12s} {'n':>3s} {'median':>9s} {'p90':>9s} {'max':>9s} {'canary_worst':>12s}")
for n, s in res["statements"].items():
    print(f"{n:12s} {s['n']:3d} {s['median']:9.1f} {s['p90']:9.1f} {s['max']:9.1f} {s['canary_worst_ms']:12.1f}")
print("subprocess attempts:", _SUBP[:3])
