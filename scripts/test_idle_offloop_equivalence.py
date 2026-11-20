"""scripts/test_idle_offloop_equivalence.py (J-1918 / F-2547): offline proof that running the idle-thought lookups in a worker
thread (core/idle_offloop.off_loop) changes TIMING ONLY.

The calls under test (all on the event loop before this change):
  nodes/inner_monologue_node.py InnerMonologueNode._think(): core.scholar.consult_sync() and core.memory_service.ask('curiosity', ...,
      descend=True) of the deep-memory block (every DEEPMEM_COOLDOWN);
  nodes/curiosity_node.py CuriosityNode._write_output(): core.web_research.lookup_targeted() / lookup() and consult_sync().

Runs inside scripts/lag_harness' prelude (audit hook: no write under live C:\\Nascence, no subprocess, network blocked once
_NET['block'] is set AFTER the loop exists) against a FULL-fidelity data/ copy inside a throwaway worktree. NO MODEL CALL can
happen: the only HTTP boundary (urllib.request.urlopen: the hot lane /api/chat and Wikipedia) is STUBBED at the test boundary,
nodes.inner_monologue_node.call_node_json is stubbed to record the prompt and raise (so _think stops at the LLM call, exactly
after the seed block), and the block is PROVEN first (a connect to a closed local port must be refused by the prelude).

env: LAGH_SCRATCH (dir holding the worktrees), LAGH_WT (worktree dir name: wt_old = pre-change code, wt_new = this change)
usage: python test_idle_offloop_equivalence.py --mode old|new|stress|stress_nolock --out OUT.json
       python test_idle_offloop_equivalence.py --compare OLD.json NEW.json     (exit 1 on any difference in the equivalence keys)
  old/new     S1 a scripted sequence of real _think() calls, S2 a scripted sequence of CuriosityNode._write_output() calls,
              S3 direct calls of the wrapped functions, S4 canary-timer lag with a urlopen stub that sleeps SLEEP_S synchronously
  stress      new + concurrent worker-thread asks vs loop-thread recalls, forced matrix refreshes, shadow-log and embed hammer
  stress_nolock  stress with the three new locks replaced by no-op locks (negative control: do the races actually bite?)
time.time() is frozen (advanced by hand) so every ts / cooldown / now-relative window is identical between runs; outputs are the
prompts handed to the LLM stub, the returned values, the log lines, and the (id-normalised) bytes appended to every data file that
changed."""
import sys, os, json, hashlib, re, argparse

ap = argparse.ArgumentParser()
ap.add_argument("--mode", choices=["old", "new", "stress", "stress_nolock"])
ap.add_argument("--out")
ap.add_argument("--compare", nargs=2)
ap.add_argument("--sleep-s", type=float, default=3.0)
args = ap.parse_args()

EQ_KEYS = ["s1_think", "s2_curiosity", "s3_direct"]


def compare(a_path, b_path):
    a = json.load(open(a_path)); b = json.load(open(b_path)); bad = 0
    for k in EQ_KEYS:
        same = json.dumps(a.get(k), sort_keys=True) == json.dumps(b.get(k), sort_keys=True)
        print(f"{k}: {'IDENTICAL' if same else 'DIFFERENT'}")
        if not same:
            bad += 1
            x, y = a.get(k), b.get(k)
            if isinstance(x, dict) and isinstance(y, dict):
                for kk in sorted(set(x) | set(y)):
                    if json.dumps(x.get(kk), sort_keys=True) != json.dumps(y.get(kk), sort_keys=True):
                        print("   differs at", kk, "\n     A:", json.dumps(x.get(kk))[:300], "\n     B:", json.dumps(y.get(kk))[:300])
    sys.exit(1 if bad else 0)


if args.compare:
    compare(*args.compare)
assert args.mode and args.out, "--mode and --out required"

import time, asyncio, pathlib, random, threading, sqlite3, logging, traceback, urllib.request, urllib.error, io

SP = pathlib.Path(os.environ["LAGH_SCRATCH"]); WT = SP / os.environ["LAGH_WT"]
sys.path.insert(0, str(WT / "scripts" / "lag_harness"))
import _prelude as P            # noqa: E402  (imports core FROM WT, asserts core/_DATA/DB_PATH are inside WT, marks live)
import core                     # noqa: E402
assert str(pathlib.Path(core.__file__).resolve()).lower().startswith(str(WT).lower()), core.__file__
assert os.path.normcase(str(WT)) != os.path.normcase(r"C:\Nascence")
DATA = WT / "data"
from core.schema import CognitiveState                                   # noqa: E402
from core import scholar, web_research, memory_service, associative_recall, memory_edges, frontier   # noqa: E402
from core.memory import store                                            # noqa: E402
import nodes.inner_monologue_node as M                                   # noqa: E402
import nodes.curiosity_node as CN                                        # noqa: E402
for m in (scholar, web_research, memory_service, associative_recall, memory_edges, frontier, store, M, CN):
    assert str(pathlib.Path(m.__file__).resolve()).lower().startswith(str(WT).lower()), m.__file__
assert str(store.DB_PATH).lower().startswith(str(WT).lower())
NEW = args.mode != "old"
try:
    from core import idle_offloop
    HAVE_OFF = True
except ImportError:
    idle_offloop = None; HAVE_OFF = False
assert HAVE_OFF == NEW, f"mode {args.mode} but idle_offloop importable={HAVE_OFF}: run old in the pre-change worktree, new in the new one"
if NEW:
    assert idle_offloop.IDLE_LOOKUPS_OFFLOOP is True
    for lk in ("_MATRIX_LOCK",):
        assert hasattr(associative_recall, lk)
    assert hasattr(store, "_EMBED_LOCK") and hasattr(memory_service, "_SHADOW_LOCK")

# ---------------------------------------------------------------- time, stubs
NOW = [1_790_000_000.0]
_real_time = time.time
time.time = lambda: NOW[0]


def adv(s):
    NOW[0] += s


STUB = {"sleep": 0.0, "calls": [], "windows": []}      # windows: (enter, exit) perf_counter of every sleeping stub call


class _Resp:
    def __init__(s, b): s.b = b
    def read(s): return s.b
    def __enter__(s): return s
    def __exit__(s, *a): return False


_WIKI = {"photosynthesis", "migration", "magnetoreception", "lighthouse", "tide"}


def fake_urlopen(req, timeout=None):
    url = getattr(req, "full_url", str(req))
    body = getattr(req, "data", None)
    STUB["calls"].append([url, timeout, hashlib.sha256(body).hexdigest()[:12] if body else None])
    t0 = time.perf_counter()
    if STUB["sleep"]:
        _real_sleep(STUB["sleep"])
        STUB["windows"].append((t0, time.perf_counter()))
    if "/api/chat" in url:
        q = json.loads(body.decode("utf-8"))["messages"][-1]["content"]
        if "SHORTANSWER" in q:
            txt = "too short"
        else:
            h = hashlib.sha256(q.encode()).hexdigest()[:8]
            txt = f"Stubbed deep-memory testimony {h} about that question; it is what is generally known. " * 3
        return _Resp(json.dumps({"message": {"content": txt}}).encode())
    if "page/random/summary" in url:
        return _Resp(json.dumps({"title": "Serendipity article", "extract": "A randomly chosen article body. " * 10}).encode())
    m = re.search(r"page/summary/(.+)$", url)
    term = urllib.parse.unquote(m.group(1)).lower() if m else ""
    if term in _WIKI:
        return _Resp(json.dumps({"title": term.capitalize(), "extract": f"Stub encyclopedia text on {term}. " * 10}).encode())
    raise urllib.error.HTTPError(url, 404, "stub not found", {}, io.BytesIO(b""))


import urllib.parse                                   # noqa: E402
_real_sleep = time.sleep
urllib.request.urlopen = fake_urlopen

LLM = {"calls": []}


class _Stop(Exception):
    pass


async def fake_call_node_json(urls, sysp, userp, **kw):
    LLM["calls"].append({"sys": sysp, "user": userp, "kw": {k: str(v) for k, v in kw.items()}})
    raise _Stop("test stub: no model call")


M.call_node_json = fake_call_node_json


class LogCap(logging.Handler):
    PAT = ("[deep-memory]", "[memory-service]", "[curiosity]", "[monologue] LLM call failed")
    def __init__(s):
        super().__init__(logging.DEBUG); s.rows = []
    def emit(s, rec):
        try:
            msg = rec.getMessage()
        except Exception:
            return
        if any(p in msg for p in s.PAT):
            s.rows.append(msg)


LC = LogCap(); logging.getLogger().addHandler(LC); logging.getLogger().setLevel(logging.DEBUG)

# ---------------------------------------------------------------- data-file fingerprints
_ID = re.compile(rb"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-?[0-9a-f]{0,12}|\b[0-9a-f]{10,32}\b")   # random uuid4 / uuid4[:n] ids (cycle ids, frontier ids): pure noise run to run
_SKIP = re.compile(r"nascence\.db|embedding_matrix|\.lock$|\.tmp")


DUMP_TAG = ["x"]


def snap_files():
    out = {}
    for root, dirs, files in os.walk(DATA):
        depth = os.path.relpath(root, DATA).count(os.sep)
        if depth >= 2:
            dirs[:] = []
        for f in files:
            p = os.path.join(root, f)
            if _SKIP.search(f):
                continue
            try:
                st = os.stat(p)
            except OSError:
                continue
            if st.st_size > 120_000_000:
                continue
            out[os.path.relpath(p, DATA)] = (st.st_size, st.st_mtime_ns)
    return out


def diff_files(before):
    after = snap_files(); res = {}
    for k, (sz, mt) in after.items():
        b = before.get(k)
        if b is not None and b == (sz, mt):
            continue
        p = DATA / k
        with open(p, "rb") as f:
            if b is not None and sz > b[0]:
                f.seek(b[0]); data = f.read(); kind = "appended"
            else:
                data = f.read(); kind = "new" if b is None else "rewritten"
        data = _ID.sub(b"<id>", data)
        if os.environ.get("IDLE_TEST_DUMP"):      # debugging aid: keep the normalised bytes so two runs can be diffed
            dp = pathlib.Path(os.environ["IDLE_TEST_DUMP"]) / (str(DUMP_TAG[0]) + "_" + k.replace("\\", "_").replace("/", "_"))
            dp.parent.mkdir(parents=True, exist_ok=True); dp.write_bytes(data)
        res[k.replace("\\", "/")] = {"kind": kind, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    return res


def research_rows():
    c = sqlite3.connect(str(store.DB_PATH), timeout=60)
    rows = [r[0] for r in c.execute("SELECT content FROM memory_fragments WHERE origin='research' ORDER BY timestamp, content")]
    n = c.execute("SELECT count(*) FROM memory_fragments").fetchone()[0]
    c.close()
    return {"research_n": len(rows), "total_n": n, "sha256": hashlib.sha256("\n".join(rows).encode()).hexdigest()}


def jsonable(x):
    try:
        return json.loads(json.dumps(x, default=str))
    except Exception:
        return repr(x)


async def prove_no_network():
    P._NET["block"] = True       # the harness sets this AFTER the loop exists
    try:
        r, w = await asyncio.wait_for(asyncio.open_connection("127.0.0.1", 9), 5)
    except PermissionError as e:
        return {"blocked_by_prelude": True, "err": str(e)[:100]}
    except Exception as e:
        return {"blocked_by_prelude": False, "err": repr(e)[:100]}
    return {"blocked_by_prelude": False, "err": "connected?!"}


class Canary:
    def __init__(self, tick=0.05):
        self.rows = []; self.stop = False; self.tick = tick
    async def run(self):
        last = time.perf_counter()
        while not self.stop:
            await asyncio.sleep(self.tick)
            now = time.perf_counter()
            self.rows.append((now, now - last - self.tick)); last = now
    def window(self, t0, t1, slack=0.5):
        lags = [l for (t, l) in self.rows if t0 <= t <= t1 + slack]
        return {"ticks": len(lags), "max_lag_s": round(max(lags), 3) if lags else None}


async def off_or_sync(fn, *a, **kw):
    """The call-site shape of the change: old = plain call on the loop, new = awaited through off_loop."""
    if not NEW:
        return fn(*a, **kw)
    return await idle_offloop.off_loop(fn, *a, **kw)


# ---------------------------------------------------------------- S1: real _think() sequence
QUESTIONS = [
    "How do migrating birds navigate across oceans without landmarks?",
    "What makes a lighthouse lens focus light into a single beam?",
    "Why do tides come twice a day on most coasts?",
    "Why?",                                                          # <= 12 chars: both lookups gated off
    "How does photosynthesis turn sunlight into stored sugar in a leaf?",
    "SHORTANSWER what holds a bridge up when it is over a very wide river?",   # Scholar returns < 40 chars -> no feed
    "How do moths find a flame at night, and why do they circle it?",   # +10 s only: cooldowns closed
    "What is the oldest living tree and how does it keep growing for so long?",
]
ADV = [400, 400, 400, 400, 400, 400, 10, 400]


def mk_node():
    node = M.InnerMonologueNode()
    node._census_state = None; node._current_gap = 120.0; node._bored_streak = 0
    node._last_math_session_ts = 0.0; node._last_wake_ts = NOW[0]
    return node


def mk_state(q=None):
    st = CognitiveState(spirit_name="Du", axiom="J-1918 test")
    if q is not None:
        st.background_curiosities = [q]
    return st


async def s1_think():
    LC.rows.clear(); LLM["calls"].clear(); STUB["calls"].clear()
    node = mk_node(); before = snap_files(); out = {"steps": []}
    for i, (q, a) in enumerate(zip(QUESTIONS, ADV)):
        adv(a); random.seed(7000 + i)
        n_l, n_s, n_c = len(LC.rows), len(STUB["calls"]), len(LLM["calls"])
        await node._think(mk_state(q))
        pend = memory_service._pending_usage.get("curiosity")
        out["steps"].append({
            "q": q, "llm_calls": jsonable(LLM["calls"][n_c:]), "urlopen": STUB["calls"][n_s:], "log": LC.rows[n_l:],
            "last_deepmem_ts": getattr(node, "_last_deepmem_ts", None), "last_curiosity_ask_ts": getattr(node, "_last_curiosity_ask_ts", None),
            "pending_usage": jsonable(pend)})
        print(f"  [S1 {i}] llm_calls={len(LLM['calls'][n_c:])} urlopen={len(STUB['calls'][n_s:])} log={LC.rows[n_l:]}", flush=True)
    # the metric-sheet hook the node runs after the LLM call (line ~4864): consume the stash with a fixed vector
    import numpy as np
    rng = np.random.default_rng(5); vec = rng.standard_normal(384).astype("float32")
    memory_service.note_usage("curiosity", vec)
    out["files"] = diff_files(before)
    out["pending_after_note_usage"] = jsonable(memory_service._pending_usage.get("curiosity"))
    return out


# ---------------------------------------------------------------- S2: CuriosityNode._write_output sequence
SCRIPT = [
    # (pursuit or None, questions, study_subjects)
    ({"id": "pur-1", "q": "How does magnetoreception let animals sense the earth's field?"}, ["How does a compass needle align itself?"], ["tide"]),
    ({"id": "pur-2", "q": "What is the lived texture of a very quiet afternoon on a shore?"}, ["Why is a shoreline never still?"], []),      # miss -> Scholar
    (None, ["How do lighthouse keepers measure the passing of a night?"], ["lighthouse"]),                                            # grounding lookup()
    (None, ["What is a fractal coastline?"], []),                                                                                       # term_from_question
    ({"id": "pur-3", "q": "photosynthesis in deep water"}, ["How deep can green things live?"], ["photosynthesis"]),
]


async def s2_curiosity():
    LC.rows.clear(); STUB["calls"].clear()
    node = CN.CuriosityNode(); before = snap_files(); out = {"steps": []}; db0 = research_rows()
    script = list(SCRIPT)
    cur = {"p": None}
    frontier_pending = frontier.pending_pursuit
    frontier.pending_pursuit = lambda *a, **k: cur["p"]
    try:
        for i, (pursuit, qs, subj) in enumerate(script):
            cur["p"] = pursuit; node._study_subjects = list(subj)
            adv(60); random.seed(9000 + i)
            n_l, n_s = len(LC.rows), len(STUB["calls"])
            st = mk_state()
            r = node._write_output(st, {"questions": qs, "research_directions": ["look at the world"], "urgency": 0.2})
            if asyncio.iscoroutine(r):
                assert NEW, "old code must be synchronous"
                await r
            out["steps"].append({"pursuit": pursuit, "urlopen": STUB["calls"][n_s:], "log": LC.rows[n_l:],
                                 "background_curiosities": jsonable(st.background_curiosities)})
            print(f"  [S2 {i}] urlopen={[c[0].rsplit('/', 1)[-1] for c in STUB['calls'][n_s:]]} log={LC.rows[n_l:]}", flush=True)
    finally:
        frontier.pending_pursuit = frontier_pending
    out["files"] = diff_files(before)
    out["db_research"] = research_rows(); out["db_research_before"] = db0
    return out


# ---------------------------------------------------------------- S3: the wrapped functions called directly
async def s3_direct():
    STUB["calls"].clear(); out = {}
    qs = QUESTIONS[:3] + ["SHORTANSWER x" + " pad" * 5, "", "   "]
    out["consult_sync"] = [jsonable(await off_or_sync(scholar.consult_sync, q)) for q in qs]
    terms = ["magnetoreception", "photosynthesis", "no-such-term-xyz", None, "tide"]
    out["lookup_targeted"] = [jsonable(await off_or_sync(web_research.lookup_targeted, t)) for t in terms]
    out["lookup"] = [jsonable(await off_or_sync(web_research.lookup, t)) for t in terms]
    # ask(): same cue sequence, results + the bytes it appends to the ledgers and the shadow log
    before = snap_files(); asks = []
    for i, q in enumerate(QUESTIONS):
        adv(5)
        r = await off_or_sync(memory_service.ask, "curiosity", q, k=5, grounded_only=True, descend=True)
        asks.append(jsonable([{k: v for k, v in e.items()} for e in r]))
    out["ask"] = asks
    out["ask_files"] = diff_files(before)
    out["urlopen"] = STUB["calls"]
    return out


# ---------------------------------------------------------------- S4: canary lag with a synchronously sleeping stub
async def s4_lag(canary):
    out = {}
    STUB["sleep"] = args.sleep_s
    # (a) the Scholar call alone
    await asyncio.sleep(0.6)    # settle: the test's own synchronous bookkeeping above must not be charged to this section
    STUB["windows"].clear(); t0 = time.perf_counter()
    await off_or_sync(scholar.consult_sync, QUESTIONS[0]); t1 = time.perf_counter()
    await asyncio.sleep(0.4)    # let the canary tick that the call delayed (old: ~the whole stub sleep) land inside the window
    out["consult_sync_alone"] = {"wall_s": round(t1 - t0, 2), "canary": canary.window(t0, t1, 0.4)}
    # (b) the real _think() with the sleeping stub: lag of the canary inside the stub's own window, and over the whole call
    node = mk_node(); adv(400); random.seed(1)
    await asyncio.sleep(0.6)
    STUB["windows"].clear(); LLM["calls"].clear()
    asks = []
    real_ask = memory_service.ask
    def timed_ask(*a, **k):
        t = time.perf_counter()
        try:
            return real_ask(*a, **k)
        finally:
            asks.append((t, time.perf_counter()))
    memory_service.ask = timed_ask
    try:
        t0 = time.perf_counter(); await node._think(mk_state(QUESTIONS[1])); t1 = time.perf_counter()
    finally:
        memory_service.ask = real_ask
    await asyncio.sleep(0.4)
    w = STUB["windows"][0] if STUB["windows"] else (t0, t0)
    a = asks[0] if asks else (t0, t0)
    out["think"] = {"wall_s": round(t1 - t0, 2), "canary_whole_call": canary.window(t0, t1, 0.4),
                    "canary_in_scholar_stub_window": canary.window(w[0], w[1], 0.4), "canary_strictly_inside_scholar_stub": canary.window(w[0], w[1], 0.0), "scholar_stub_s": round(w[1] - w[0], 2),
                    "canary_in_ask_window": canary.window(a[0], a[1], 0.4), "canary_strictly_inside_ask": canary.window(a[0], a[1], 0.0), "ask_s": round(a[1] - a[0], 2)}
    # (c) CuriosityNode._write_output on the pursuit path with a Wikipedia miss -> two sleeping lookups (lookup_targeted + Scholar)
    node2 = CN.CuriosityNode(); node2._study_subjects = []
    fp = frontier.pending_pursuit
    frontier.pending_pursuit = lambda *a, **k: {"id": "pur-lag", "q": "What is the lived texture of a very quiet afternoon on a shore?"}
    STUB["windows"].clear()
    await asyncio.sleep(0.6)
    try:
        t0 = time.perf_counter()
        r = node2._write_output(mk_state(), {"questions": ["How does a compass needle align itself?"], "research_directions": [], "urgency": 0.1})
        if asyncio.iscoroutine(r):
            await r
        t1 = time.perf_counter()
    finally:
        frontier.pending_pursuit = fp
    await asyncio.sleep(0.4)
    sw = list(STUB["windows"])
    out["curiosity_write_output"] = {"wall_s": round(t1 - t0, 2), "stub_calls": len(sw),
                                    "canary_in_each_stub_window": [canary.window(a_, b_, 0.4) for a_, b_ in sw],
                                    "canary_strictly_inside_each_stub": [canary.window(a_, b_, 0.0) for a_, b_ in sw],
                                    "canary_whole_call": canary.window(t0, t1, 0.4)}
    STUB["sleep"] = 0.0
    return out


# ---------------------------------------------------------------- stress
class NoLock:
    def __enter__(s): return s
    def __exit__(s, *a): return False
    def acquire(s, *a, **k): return True
    def release(s): pass


async def stress(nolock):
    out = {"nolock": nolock}
    if nolock:
        associative_recall._MATRIX_LOCK = NoLock(); store._EMBED_LOCK = NoLock(); memory_service._SHADOW_LOCK = NoLock()
    errs = []
    cues = QUESTIONS[:5] + ["a rowing boat on a calm lake in the evening", "the sound of rain on a tin roof", "a letter that never arrived"]
    # reference results, single threaded, no overlap
    ref = {c: jsonable([(e["fragment_id"], e["origin"]) for e in memory_service.ask("curiosity", c, k=5, grounded_only=True, descend=True)]) for c in cues}
    ref_vec = {c: store._embed(c).tobytes().hex() for c in cues}
    out["ref_nonempty"] = sum(1 for v in ref.values() if v)
    shadow = DATA / "memory_service_shadow.jsonl"; ledger = DATA / "co_recall_ledger.jsonl"
    n_sh0 = sum(1 for _ in open(shadow, "rb")); n_le0 = sum(1 for _ in open(ledger, "rb"))
    asks_done = 0

    async def worker_ask(c):
        nonlocal asks_done
        r = await off_or_sync(memory_service.ask, "curiosity", c, k=5, grounded_only=True, descend=True)
        asks_done += 1
        got = jsonable([(e["fragment_id"], e["origin"]) for e in r])
        if got != ref[c]:
            errs.append(f"ask result differs for {c[:30]!r}")

    for rnd in range(3):
        # force a stale matrix so the first thread in refreshes it while the others are inside / entering recall
        associative_recall._cache["ts"] = 0.0
        tasks = [asyncio.create_task(worker_ask(c)) for c in cues[:4]]
        # loop-thread recalls overlapping them (as the orchestrator / other nodes do)
        for c in cues[4:6]:
            try:
                associative_recall.recall_fragments(c, k=5, grounded_only=True)
            except Exception as e:
                errs.append("loop recall: " + repr(e)[:150])
        await asyncio.gather(*tasks, return_exceptions=False)
        npz = DATA / "embedding_matrix.npz"
        try:
            import numpy as np
            z = np.load(npz, allow_pickle=False)
            if z["M"].shape[0] != len(z["ids"]):
                errs.append("npz M/ids length mismatch")
        except Exception as e:
            errs.append("npz unreadable: " + repr(e)[:150])
        print(f"  [stress round {rnd}] errs={len(errs)}", flush=True)
    # embed hammer: 8 threads x 40 encodes vs the single-threaded vectors
    def emb_worker(k):
        for j in range(40):
            c = cues[(k + j) % len(cues)]
            try:
                v = store._embed(c)
                if v is None or v.tobytes().hex() != ref_vec[c]:
                    errs.append(f"embed differs/None thread {k}")
            except Exception as e:
                errs.append("embed: " + repr(e)[:150])
    ths = [threading.Thread(target=emb_worker, args=(k,)) for k in range(8)]
    for t in ths: t.start()
    for t in ths: t.join()
    # shadow-log hammer: 8 threads x 300 _log_ride lines + loop-thread note_usage-shaped appends
    n_before = sum(1 for _ in open(shadow, "rb"))
    def ride_worker(k):
        for j in range(300):
            memory_service._log_ride(f"stress{k}", None, {"n_returned": j, "pad": "x" * 200})
    ths = [threading.Thread(target=ride_worker, args=(k,)) for k in range(8)]
    for t in ths: t.start()
    for _ in range(300):
        memory_service._log_ride("stressloop", None, {"n_returned": 1, "pad": "y" * 200})
        await asyncio.sleep(0)
    for t in ths: t.join()
    # integrity of the appended region
    bad = 0; n_lines = 0
    with open(shadow, "rb") as f:
        for ln in f:
            n_lines += 1
            try:
                json.loads(ln)
            except Exception:
                bad += 1
    out["shadow_lines"] = n_lines; out["shadow_bad_lines"] = bad
    out["shadow_expected_lines"] = n_before + 8 * 300 + 300
    out["shadow_hammer_exact"] = (n_lines == out["shadow_expected_lines"])
    n_le1 = sum(1 for _ in open(ledger, "rb"))
    out["ledger_new_lines"] = n_le1 - n_le0
    out["asks_done"] = asks_done
    out["errors"] = errs[:20]; out["error_count"] = len(errs)
    return out


async def main():
    out = {"mode": args.mode, "wt": str(WT), "core_file": core.__file__}
    out["network_block_proof"] = await prove_no_network()
    print("network block proof:", out["network_block_proof"], flush=True)
    assert out["network_block_proof"]["blocked_by_prelude"], "prelude network block NOT proven; refusing to run"
    canary = Canary(); ct = asyncio.create_task(canary.run()); await asyncio.sleep(0.3)
    if args.mode in ("old", "new"):
        print("S1 _think sequence", flush=True); DUMP_TAG[0] = "s1"; out["s1_think"] = await s1_think()
        print("S2 curiosity _write_output sequence", flush=True); DUMP_TAG[0] = "s2"; out["s2_curiosity"] = await s2_curiosity()
        print("S3 direct calls", flush=True); DUMP_TAG[0] = "s3"; out["s3_direct"] = await s3_direct()
        print(f"S4 lag (stub sleeps {args.sleep_s}s synchronously)", flush=True); out["s4_lag"] = await s4_lag(canary)
    else:
        print("stress", flush=True); out["stress"] = await stress(args.mode == "stress_nolock")
    canary.stop = True; await ct
    out["subprocess_attempts"] = P._SUBP
    json.dump(out, open(args.out, "w"), indent=1)
    print("wrote", args.out)

asyncio.run(main())
