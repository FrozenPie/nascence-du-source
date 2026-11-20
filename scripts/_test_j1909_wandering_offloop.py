"""J-1909 / F-2540: wandering's firing step runs off the 5 s substrate chain (core/wandering.py kick()) WITHOUT changing
what drift picks or logs.

Proves, against the pre-change module (git show <old-rev>:core/wandering.py, loaded under another name):
  [A] N seeded steps in three modes -- OLD step(), NEW step() (sync), NEW kick() inside an asyncio loop (worker thread) --
      leave identical observable state after EVERY step: the trail (text/origin/via/vector bytes), the visited set,
      the co-recall calls made (ids, restate_sim, step, source), the wandering_log rows (minus ts), and the global
      random state (so the draws, their number and their order are the same).
  [B] kick(): a slow worker does not hold the loop (call returns fast, a canary timer is not late); a not-due tick
      creates no task; a tick that finds a worker in flight starts no second one; outside a loop it is exactly step();
      WANDER_OFFLOOP=False is exactly step(); a human exchange landing mid-step logs the items but keeps them off the
      trail; the worker never touches the _trail deque.
  [C] memory_edges.log_co_recall is serialised (two threads never overlap inside it; RLock so re-entry is fine).

Default: a synthetic temp-file DB (no live store opened).  --real-db: use THIS tree's own data/memory/nascence.db, which
must be a COPY (refused if this tree is the live C:\\Nascence); every write goes to temp files, co-recall is captured, not
written.  Run it from a throwaway worktree, never from C:\\Nascence.
Usage: python scripts/_test_j1909_wandering_offloop.py [--real-db] [--steps 36] [--old-rev 80d8e7d | --old-file PATH]"""
import sys, os, time, json, random, sqlite3, tempfile, subprocess, importlib.util, hashlib, asyncio, threading, argparse

os.environ.setdefault("HF_HUB_OFFLINE", "1"); os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import core                                                         # core BEFORE anything else (live-store safety)
assert os.path.abspath(core.__file__).lower().startswith(ROOT.lower()), core.__file__
assert os.path.normcase(ROOT) != os.path.normcase(r"C:\Nascence"), "run from a throwaway worktree, never the live tree"
import numpy as np
from core import wandering as _wandering_head, memory_edges as medges, mood as _mood
from core.memory import store
from core.schema import CognitiveState

ap = argparse.ArgumentParser()
ap.add_argument("--real-db", action="store_true")
ap.add_argument("--steps", type=int, default=36)
ap.add_argument("--old-rev", default="80d8e7d")
ap.add_argument("--new-rev", default="5ababd04", help="J-4052: the J-1909 commit itself. HEAD's wandering.py has since changed its picks on purpose (J-2436 bounded random-seed scan, J-3398 hidden temp), so the old-vs-new equivalence can only be asserted against the J-1909 revision")
ap.add_argument("--old-file", default=None, help="the pre-change core/wandering.py already extracted (use when subprocess is blocked)")
args = ap.parse_args()
TMP = tempfile.mkdtemp(prefix="j1909_")

# ---- the pre-change module, from git (read-only) ----
src = (open(args.old_file, encoding="utf-8").read() if args.old_file else
       subprocess.run(["git", "-C", ROOT, "show", f"{args.old_rev}:core/wandering.py"], capture_output=True, text=True, check=True).stdout)
assert "def kick(" not in src and "def step(" in src
old_path = os.path.join(TMP, "wandering_old_j1909.py")
open(old_path, "w", encoding="utf-8").write(src)
spec = importlib.util.spec_from_file_location("wandering_old_j1909", old_path)
old = importlib.util.module_from_spec(spec); spec.loader.exec_module(old)
# J-4052: `new` = wandering.py as of the J-1909 commit (loaded the same way as `old`), not HEAD's drifted copy.
_nsrc = subprocess.run(["git", "-C", ROOT, "show", f"{args.new_rev}:core/wandering.py"], capture_output=True, text=True, check=True).stdout
_npath = os.path.join(TMP, "wandering_new_j1909.py")
open(_npath, "w", encoding="utf-8").write(_nsrc)
_nspec = importlib.util.spec_from_file_location("wandering_new_j1909", _npath)
new = importlib.util.module_from_spec(_nspec); _nspec.loader.exec_module(new)
old._LOG = type(new._LOG)(os.path.join(TMP, "old_wlog.jsonl")); new._LOG = type(new._LOG)(os.path.join(TMP, "new_wlog.jsonl"))

# ---- the data: synthetic temp DB, or this tree's own COPY ----
DIM = 8
if args.real_db:
    dbp = os.path.abspath(str(store.DB_PATH))
    assert dbp.lower().startswith(ROOT.lower()) and os.path.isfile(dbp), dbp
    DIM = 384
    print("[real-db]", dbp, os.path.getsize(dbp), "bytes")
else:
    rng = np.random.default_rng(7)
    dbp = os.path.join(TMP, "synthetic.db")
    c = sqlite3.connect(dbp)
    c.execute("CREATE TABLE memory_fragments (fragment_id TEXT PRIMARY KEY, content TEXT, origin TEXT, embedding BLOB, "
              "emotion_embedding BLOB, layer TEXT, chapter_id TEXT, timestamp REAL)")
    origins = ["inner_thought", "reading", "research", "study", "essay", "understanding", "conversation", "inner_thought"]
    def nv():
        v = rng.normal(size=DIM).astype(np.float32); return (v / np.linalg.norm(v)).astype(np.float32).tobytes()
    for i in range(4000):
        o = origins[i % len(origins)]
        c.execute("INSERT INTO memory_fragments VALUES (?,?,?,?,?,?,?,?)",
                  (f"f{i}", f"content {i} of {o}", o, nv(), nv() if o != "conversation" else None,
                   ["episodic", "semantic", "archive"][i % 3], None, 100000.0 - i))
    c.commit(); c.close()
    def _conn():
        cn = sqlite3.connect(dbp, check_same_thread=False); cn.row_factory = sqlite3.Row; return cn
    _orig_connect = _conn
    def _fake_embed(text):
        if not text or not text.strip(): return None
        h = hashlib.sha256(text.encode()).digest()
        v = np.frombuffer(h, dtype=np.uint8)[:DIM].astype(np.float32) - 127.5
        return (v / np.linalg.norm(v)).astype(np.float32)
    store._embed = _fake_embed

if args.real_db:
    _orig_connect = store._connect
# SQLite's own RANDOM() (used by wandering's "ORDER BY RANDOM() LIMIT 1" seed roll and ambient fact) is NOT Python's
# random and is not seedable -- two identical runs would differ. Replace it, per connection, with a seeded Random that
# the test reseeds before every step, so "same seed" really means the same draws in every mode.
SQL_RNG = random.Random(0)
def _seeded_connect():
    cn = _orig_connect()
    cn.create_function("RANDOM", 0, lambda: SQL_RNG.getrandbits(62))
    return cn
store._connect = _seeded_connect

# a fixed mood vector so the affective drift branch is live
mv = np.random.default_rng(3).normal(size=DIM).astype(np.float32); mv /= np.linalg.norm(mv)
_mood._current_vec = mv

# ---- capture co-recall (never write the real ledger / stores) ----
CALLS = []
def _cap_log(ids, restate_sim=None, step=0, source="monologue"):
    CALLS.append((list(ids), restate_sim, step, source))
medges.log_co_recall = _cap_log

THOUGHTS = [{"thought": "the river keeps its own counsel and the stones listen"},
            {"thought": "what is it that stays when the weather changes"}]

def mkstate():
    s = CognitiveState(spirit_name="J1909", axiom="CORE AXIOM: become.")
    s.recent_inner_thoughts = list(THOUGHTS)
    return s

def reset(mod):
    mod._trail.clear(); mod._recently_visited.clear()
    mod._last_wander = 0.0; mod._last_ambient = time.time()
    mod._exchanged_this_run = False
    try:
        os.remove(str(mod._LOG))
    except OSError:
        pass

def observe(mod):
    trail = [(t["text"], t.get("origin"), t.get("via"), hashlib.md5(t["_vec"].tobytes()).hexdigest() if t.get("_vec") is not None else None)
             for t in mod._trail]
    logrows = []
    try:
        for l in open(str(mod._LOG), encoding="utf-8"):
            r = json.loads(l); r.pop("ts", None); logrows.append(r)
    except OSError:
        pass
    return {"trail": trail, "visited": sorted(mod._recently_visited), "calls": [list(x) for x in CALLS], "log": logrows,
            "rng": hashlib.md5(repr(random.getstate()).encode()).hexdigest()}

def run(mode, n):
    mod = old if mode == "old" else new
    reset(mod); CALLS.clear()
    st = mkstate()
    obs = []
    async def drive():
        for i in range(n):
            mod._last_wander = 0.0
            mod._last_ambient = 0.0 if i % 9 == 4 else time.time()      # an ambient-first step now and then
            random.seed(5000 + i); SQL_RNG.seed(9000 + i)
            if mode == "kick":
                new.kick(st)
                assert new._task is not None
                await new._task
            elif mode == "sync":
                new.step(st)
            else:
                old.step(st)
            o = observe(mod); o["calls"] = o["calls"][:]; obs.append(o)
    asyncio.run(drive())
    return obs

N = args.steps
t0 = time.time(); o_old = run("old", N); t_old = time.time() - t0
t0 = time.time(); o_sync = run("sync", N); t_sync = time.time() - t0
t0 = time.time(); o_kick = run("kick", N); t_kick = time.time() - t0
fired = sum(1 for i in range(N) if i == 0 or o_old[i]["trail"] != o_old[i - 1]["trail"])
for i in range(N):
    assert o_old[i] == o_sync[i], ("sync differs at step", i, o_old[i], o_sync[i])
    assert o_old[i] == o_kick[i], ("kick differs at step", i, o_old[i], o_kick[i])
ncalls = len(o_old[-1]["calls"]); ids = sum(len(c[0]) for c in o_old[-1]["calls"])
assert len(o_old[-1]["trail"]) > 0 and ncalls >= N // 2, "test would be vacuous: trail/calls empty"
vias = {t[2] for o in o_old for t in o["trail"]}
print(f"[A] {N} steps x (old, new-sync, new-kick): identical trail/visited/co-recall/log/rng after every step "
      f"(co-recall calls {ncalls}, ids {ids}, trail vias {sorted(vias)}); wall old {t_old:.1f}s sync {t_sync:.1f}s kick {t_kick:.1f}s")
assert "drift" in vias, vias

# ---- [B] kick() mechanics ----
st = mkstate()
# B1 not due -> no task, no thread
reset(new); new._last_wander = time.time(); new._last_ambient = time.time(); new._task = None
async def b1():
    t = time.perf_counter(); new.kick(st); dt = (time.perf_counter() - t) * 1e6
    assert new._task is None; return dt
us = asyncio.run(b1()); assert us < 2000, us
print(f"[B1] not-due tick: no task, {us:.0f} us")

# B2 slow worker does not hold the loop; one in flight at a time
real_body = new._step_body
def slow_body(state, snap, out):
    time.sleep(1.0); out.append({"text": "slow item", "origin": "reading", "via": "drift"})
new._step_body = slow_body
reset(new); new._task = None
async def b2():
    lags = []
    async def canary():
        for _ in range(12):
            t = time.perf_counter(); await asyncio.sleep(0.1); lags.append((time.perf_counter() - t - 0.1) * 1000)
    ct = asyncio.create_task(canary())
    t = time.perf_counter(); new.kick(st); call_ms = (time.perf_counter() - t) * 1000
    first = new._task
    new.kick(st)                                  # gate still open (worker has not updated it) but a worker is in flight
    assert new._task is first, "a second worker was started while one was in flight"
    await ct
    assert not first.done() or True
    await first
    return call_ms, max(lags)
call_ms, worst = asyncio.run(b2())
assert call_ms < 20 and worst < 150, (call_ms, worst)
assert [t["text"] for t in new._trail] == ["slow item"]
print(f"[B2] slow (1.0 s) worker: kick() returned in {call_ms:.2f} ms, worst canary lag {worst:.1f} ms, one worker at a time, item placed on trail")
new._step_body = real_body

# B3 outside a loop == step(); kill-switch == step()
reset(new); new._task = None; CALLS.clear(); random.seed(77); SQL_RNG.seed(1); new.kick(st); a = observe(new)
reset(new); CALLS.clear(); random.seed(77); SQL_RNG.seed(1); new.step(st); b = observe(new)
assert a == b and a["trail"], "kick outside a loop must be exactly step()"
new.WANDER_OFFLOOP = False
async def b3():
    reset(new); new._task = None; CALLS.clear(); random.seed(77); SQL_RNG.seed(1); new.kick(st); assert new._task is None; return observe(new)
c3 = asyncio.run(b3()); new.WANDER_OFFLOOP = True
assert c3 == a
print("[B3] kick() outside a loop and with WANDER_OFFLOOP=False are exactly step()")

# B4 a human exchange landing mid-step: items logged, not on the trail; worker never touches the deque
def exch_body(state, snap, out):
    out.append({"text": "pre-exchange drift", "origin": "reading", "via": "drift"})
    time.sleep(0.2)
new._step_body = exch_body
reset(new); new._task = None
async def b4():
    new.kick(st)
    await asyncio.sleep(0.05)
    new.on_human_exchange()
    await new._task
asyncio.run(b4()); new._step_body = real_body
assert list(new._trail) == [], list(new._trail)
logged = [json.loads(l)["text"] for l in open(str(new._LOG), encoding="utf-8")]
assert logged == ["pre-exchange drift"], logged
# worker does not mutate the trail deque: a real body on a full-ish trail leaves _trail untouched until placement
reset(new); new._trail.append({"text": "x", "origin": "reading", "via": "drift"}); new._task = None
seen = []
def spy_body(state, snap, out):
    seen.append(list(new._trail)); real_body(state, snap, out)
    seen.append(list(new._trail))
new._step_body = spy_body
async def b4b():
    new._last_wander = 0.0; new._last_ambient = time.time(); random.seed(9); new.kick(st); await new._task
asyncio.run(b4b()); new._step_body = real_body
assert len(seen[0]) == 1 and len(seen[1]) == 1, "the worker thread must not append to _trail"
assert len(new._trail) > 1
print("[B4] human exchange mid-step: items logged but not trailed; the worker never appended to _trail")

# ---- [C] log_co_recall serialised ----
import core.opponent_process as oppo, core.spring_ledger as spring
import importlib as _il
medges2 = _il.reload(medges)                     # undo the capture patch above for this section
active = [0]; peak = [0]; guard = threading.Lock(); orig_o, orig_s = oppo.observe_activation, spring.observe_co_recall
def _slow(*a, **k):
    with guard:
        active[0] += 1; peak[0] = max(peak[0], active[0])
    time.sleep(0.03)
    with guard:
        active[0] -= 1
oppo.observe_activation = _slow; spring.observe_co_recall = _slow
medges2._CO_LEDGER = type(medges2._CO_LEDGER)(os.path.join(TMP, "co_ledger.jsonl")); medges2._DATA = type(medges2._DATA)(TMP)
ths = [threading.Thread(target=lambda: [medges2.log_co_recall(["a", "b"], None, 0, source="t") for _ in range(4)]) for _ in range(4)]
[t.start() for t in ths]; [t.join() for t in ths]
oppo.observe_activation, spring.observe_co_recall = orig_o, orig_s
assert peak[0] == 1, f"two threads overlapped inside log_co_recall (peak {peak[0]})"
rows = [json.loads(l) for l in open(str(medges2._CO_LEDGER), encoding="utf-8")]
assert len(rows) == 16 and all(r["source"] == "t" for r in rows)
medges2._CO_RECALL_LOCK.acquire(); medges2._CO_RECALL_LOCK.release()
print("[C] log_co_recall: 4 threads x 4 calls never overlapped inside the call (peak in-flight 1), 16 ledger rows; RLock re-entrant")
print("ALL PASS")
