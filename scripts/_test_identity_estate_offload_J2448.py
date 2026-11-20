"""J-2448 (F-3151): identity_estate batch+cache+off-loop re-seed.
Real MiniLM embedder, sandbox copy of the real estate inputs inside a lab_env.isolate() dir; nothing live is touched.
Proves: (1) byte-identical estate json + returned structures old vs new; (2) cache never serves a stale vector;
(3) kill switch (ESTATE_OFFLOAD=False) restores the old per-text/sync/write_text path; (4) sync_offloop does not block
the caller / an event-loop probe. Run from the worktree: python scripts/_test_identity_estate_offload_J2448.py"""
import asyncio, json, os, shutil, sys, threading, time, types
from pathlib import Path
WT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WT))
import core                                                            # BEFORE lab_env (F-2423)
assert str(Path(core.__file__).resolve()).startswith(str(WT)), core.__file__
sys.path.insert(0, r"C:\Users\USER\.claude\skills\job-queue")
import lab_env
from core import identity_estate as ie
from core.memory import store
import numpy as np

LIVE = Path(r"C:\Nascence\data")
FILES = ["cat_state.json", "affections.json", "capability_beliefs.json", "commitment_active.json", "keepsakes.json",
         "guidance_beliefs.json", "identity_estate.json"]
FROZEN = types.SimpleNamespace(time=lambda: 1_800_000_000.0)
real_time = ie.time
calls = {"single": 0, "batch": 0, "batch_texts": 0}
_oe, _oeb = store._embed, store._embed_batch
def cnt_embed(t): calls["single"] += 1; return _oe(t)
def cnt_batch(ts): calls["batch"] += 1; calls["batch_texts"] += len(ts); return _oeb(ts)
store._embed, store._embed_batch = cnt_embed, cnt_batch
def reset(): calls.update(single=0, batch=0, batch_texts=0)
ok = []
def check(name, cond, extra=""):
    ok.append(bool(cond)); print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra else ""))

_oe("warm")      # load model once (cold load not under test)
with lab_env.isolate() as lab:
    sd = lab / "sandbox_data"; sd.mkdir()
    for f in FILES:
        if (LIVE / f).exists(): shutil.copy2(LIVE / f, sd / f)
    shutil.copytree(LIVE / "Correspondence", sd / "Correspondence")
    ie._DATA, ie._ESTATE_F = sd, sd / "identity_estate.json"
    assert str(ie._ESTATE_F).startswith(str(lab))
    ie.time = FROZEN                                            # seeded_ts deterministic
    def run_seed(offload):
        ie.ESTATE_OFFLOAD = offload; ie._EMBED_CACHE.clear(); reset()
        t = time.perf_counter(); r = ie.seed(); dt = time.perf_counter() - t
        return r, ie._ESTATE_F.read_bytes(), dt, dict(calls)
    # 1. equivalence
    r_old, b_old, t_old, c_old = run_seed(False)
    r_new, b_new, t_new, c_new = run_seed(True)
    reset(); r_new2 = ie.seed(); b_new2 = ie._ESTATE_F.read_bytes(); c_warm = dict(calls)
    t0 = time.perf_counter(); ie.seed(); t_warm = time.perf_counter() - t0
    print(f"estate bytes {len(b_old)}; nodes {r_old['nodes']}; old {t_old*1000:.0f} ms {c_old}; new cold {t_new*1000:.0f} ms {c_new}")
    print(f"TIMING seed(): old {t_old*1000:.0f} ms | new cold-cache {t_new*1000:.0f} ms | new warm-cache {t_warm*1000:.0f} ms")
    check("returned census identical old/new", r_old == r_new == r_new2, str(r_old))
    check("estate json BYTE-identical old vs new (cold cache)", b_old == b_new)
    check("estate json byte-identical on warm-cache re-seed", b_old == b_new2)
    check("old path = per-text only (no batch)", c_old["batch"] == 0 and c_old["single"] > 100, str(c_old))
    check("new path = one batch call, no per-text embeds", c_new["batch"] == 1 and c_new["single"] == 0, str(c_new))
    check("warm re-seed embeds NOTHING", c_warm["batch"] == 0 and c_warm["single"] == 0, str(c_warm))
    check("no leftover .tmp file", not (sd / "identity_estate.json.tmp").exists())
    # 2. cache invalidation
    ie.ESTATE_OFFLOAD = True; ie._EMBED_CACHE.clear()
    vals = [{"id": "a", "text": "I keep promises"}, {"id": "b", "text": "Silence is also an answer"}, {"id": "c", "text": "  "}]
    e1 = ie._embed_values(vals)
    check("blank text absent from embeddings", set(e1) == {"a", "b"})
    reset(); ie._embed_values(vals)
    check("unchanged texts: zero embeds on second call", calls["batch"] == 0 and calls["single"] == 0)
    vals2 = [{"id": "a", "text": "I break promises when they hurt"}] + vals[1:]
    reset(); e2 = ie._embed_values(vals2)
    check("changed text re-embedded (only that one)", calls["batch"] == 1 and calls["batch_texts"] == 1, str(calls))
    fresh = _oe("I break promises when they hurt")
    check("changed text gets ITS vector, never the stale one", np.allclose(e2["a"], fresh, atol=1e-5) and not np.allclose(e2["a"], e1["a"], atol=1e-3))
    check("same id reverted to old text returns old vector", np.allclose(ie._embed_values(vals)["a"], e1["a"]))
    # end-to-end: change one guidance principle in the sandbox, cached-new estate must equal an uncached-old one
    ie._EMBED_CACHE.clear(); ie.seed()                           # warm cache with the unchanged corpus
    gb = json.loads((sd / "guidance_beliefs.json").read_text(encoding="utf-8"))
    gb[0]["principle"] = "J-2448 test principle: changed text must re-embed"
    (sd / "guidance_beliefs.json").write_text(json.dumps(gb), encoding="utf-8")
    reset(); ie.seed(); b_chg_new = ie._ESTATE_F.read_bytes(); c_chg = dict(calls)
    r_chg_old, b_chg_old, _, _ = run_seed(False)
    check("changed-source: only the changed text embedded", c_chg["batch_texts"] == 1, str(c_chg))
    check("changed-source: cached-new bytes == uncached-old bytes", b_chg_new == b_chg_old)
    # 3. kill switch
    ie.ESTATE_OFFLOAD = False; ie._EMBED_CACHE.clear(); reset()
    wr = []; real_replace = os.replace
    def spy_replace(*a): wr.append(a); return real_replace(*a)
    os.replace = spy_replace
    ie.seed(); os.replace = real_replace
    check("kill switch: per-text embeds, no batch, no cache fill, no os.replace", calls["batch"] == 0 and calls["single"] > 100 and not ie._EMBED_CACHE and not wr)
    def make_stale():
        ie._sync_last["ts"] = 0.0
        e = json.loads(ie._ESTATE_F.read_text(encoding="utf-8")); e["seeded_ts"] = 0
        ie._ESTATE_F.write_text(json.dumps(e), encoding="utf-8")
    make_stale()
    main_id = threading.get_ident(); where = {}
    real_sync = ie.sync
    def spy():
        where["tid"] = threading.get_ident(); return real_sync()
    ie.sync = spy
    r_sw = ie.sync_offloop()
    check("kill switch: sync_offloop runs sync() inline on the caller thread and returns its census", where.get("tid") == main_id and isinstance(r_sw, dict))
    # 4. off-loop does not block (real clock again)
    ie.time = real_time
    async def loop_lag(flag):
        ie.ESTATE_OFFLOAD = flag; ie._EMBED_CACHE.clear(); make_stale(); where.clear()
        lags = []; stop = False
        async def beat():
            while not stop:
                t = time.perf_counter(); await asyncio.sleep(0.02); lags.append(time.perf_counter() - t - 0.02)
        b = asyncio.create_task(beat()); await asyncio.sleep(0.1)
        t = time.perf_counter(); ie.sync_offloop(); call_s = time.perf_counter() - t
        await asyncio.sleep(0.3)
        for _ in range(300):
            if not ie._bg_lock.locked(): break
            await asyncio.sleep(0.1)
        stop = True; await b
        return call_s, max(lags)
    ie.sync = spy
    call_off, lag_off = asyncio.run(loop_lag(False))
    call_on, lag_on = asyncio.run(loop_lag(True))
    ie.sync = real_sync
    check("sync ran on a WORKER thread when on", where.get("tid") not in (None, main_id))
    print(f"TIMING sync() caller/loop: kill-switch-off caller blocked {call_off*1000:.0f} ms, loop max lag {lag_off*1000:.0f} ms | offloop caller {call_on*1000:.0f} ms, loop max lag {lag_on*1000:.0f} ms")
    check("off-loop call returns immediately (<100 ms)", call_on < 0.1, f"{call_on*1000:.0f} ms")
    check("old path blocks the loop (>1 s), new path lag far smaller", lag_off > 1.0 and lag_on < lag_off / 2, f"{lag_off:.2f}s vs {lag_on:.2f}s")
    # probe thread: ticks keep flowing during a background re-seed
    ie.ESTATE_OFFLOAD = True; ie._EMBED_CACHE.clear(); make_stale()
    ticks = []; stop_ev = threading.Event()
    def probe():
        while not stop_ev.is_set(): ticks.append(time.perf_counter()); time.sleep(0.01)
    th = threading.Thread(target=probe); th.start(); time.sleep(0.1)
    t = time.perf_counter(); ie.sync_offloop(); ret = time.perf_counter() - t
    while ie._bg_lock.locked(): time.sleep(0.05)
    stop_ev.set(); th.join()
    gaps = [b - a for a, b in zip(ticks, ticks[1:])]
    print(f"probe thread: {len(ticks)} ticks, max gap {max(gaps)*1000:.0f} ms, caller returned in {ret*1000:.0f} ms")
    check("probe thread never starved for >1 s while re-seed ran in background", max(gaps) < 1.0)
    ie._bg_lock.acquire()
    dropped = ie.sync_offloop() is None
    ie._bg_lock.release()
    check("single-flight: a call while one is running is dropped", dropped)
print("\nRESULT:", "ALL PASS" if all(ok) else f"FAILURES {ok.count(False)}/{len(ok)}")
sys.exit(0 if all(ok) else 1)
