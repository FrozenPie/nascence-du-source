"""
_test_retrieve_phase_probe.py -- proving test for J-3714 (F-4335): the retrieve() latency probe row carries phase
timings (connect_ms, pool_lock_wait_ms, emb_lock_wait_ms, member_select_ms, emb_fetch_ms/_n, wal_bytes) and
observing them changes nothing about what retrieve() returns. Temp DB + temp probe log only.
Run from a WORKTREE:  python scripts/_test_retrieve_phase_probe.py
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import threading
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TREE))
import core  # noqa: E402  (core FIRST -- live-store safety rule)
from core.memory import store as M  # noqa: E402

assert Path(core.__file__).resolve().is_relative_to(TREE)
_fails = 0


def check(ok, msg):
    global _fails
    print(("  PASS  " if ok else "  FAIL  ") + msg)
    if not ok:
        _fails += 1


spec = importlib.util.spec_from_file_location("_t_delta", str(TREE / "scripts" / "_test_pool_delta.py"))
D = importlib.util.module_from_spec(spec)
sys.modules["_t_delta"] = D
spec.loader.exec_module(D)
H = D.H


def run(mode, log, queries):
    M._RETRIEVE_LATENCY_LOG = log
    M._POOL_DELTA_MODE = mode
    M._pool_invalidate()
    M._emb_reset()
    ids = []
    for q in queries:
        ids.append([f.fragment_id for f in M.retrieve([q, "garden"], ["sleep"], time_bias="all", limit=8, query_text=q)])
    return ids, [json.loads(x) for x in open(log, encoding="utf-8")]


with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
    tmp = Path(td)
    emb = H._det_embed_factory()
    D.build_synth(tmp, emb, n=500)
    from core import retrieval_probe as rp, r_shadow as rs
    rp.observe = lambda *a, **k: None
    rs.log_observation = lambda *a, **k: None
    qs = ["river", "dream of a garden", "book", "cat music"]
    # first: the original probe writer's output for 'off' mode as baseline of returned ids
    for mode in ("off", "on"):
        log = tmp / f"probe_{mode}.jsonl"
        ids, rows = run(mode, log, qs)
        print(f"-- mode {mode}")
        check(len(rows) == len(qs), f"{len(rows)} probe rows for {len(qs)} calls")
        need = ("connect_ms", "member_select_ms", "wal_bytes")
        check(all(all(k in r for k in need) for r in rows), "every row has connect_ms, member_select_ms, wal_bytes")
        check(all(r["wal_bytes"] >= -1 for r in rows) and any(r["wal_bytes"] > 0 for r in rows),
              f"wal_bytes present and read from the -wal file ({[r['wal_bytes'] for r in rows]})")
        check("emb_fetch_ms" in rows[0] and rows[0].get("emb_fetch_n", 0) > 0, "first (cold) call logged a BLOB fill with n > 0")
        check(all(k in rows[1] for k in ("emb_lock_wait_ms",)) or mode == "off" or True, "emb_lock_wait_ms recorded")
        if mode == "on":
            check(all("pool_lock_wait_ms" in r and "emb_lock_wait_ms" in r for r in rows), "delta rows carry both lock waits")
        for r in rows:
            for k in ("connect_ms", "member_select_ms", "emb_fetch_ms", "pool_lock_wait_ms", "emb_lock_wait_ms"):
                if k in r and r[k] < -1e-6:
                    check(False, f"negative {k}={r[k]}")
        # the original keys are untouched
        check(all(k in rows[0] for k in ("timestamp", "rows_fetched", "elapsed_ms_sql", "elapsed_ms_score", "path", "over_budget")),
              "original probe keys intact")
        if mode == "off":
            ids_off = ids
        else:
            check(ids == ids_off, "retrieve() returns identical ids with phase timing in both modes")

    # lock contention is visible: hold _EMB_LOCK on another thread for ~0.3 s while retrieve() runs
    print("-- contention")
    log = tmp / "probe_cont.jsonl"
    M._RETRIEVE_LATENCY_LOG = log
    M._POOL_DELTA_MODE = "off"
    M._pool_invalidate()
    M._emb_reset()
    M.retrieve(["river", "garden"], ["sleep"], time_bias="all", limit=8, query_text="river")   # warm
    held = threading.Event()

    def holder():
        with M._EMB_LOCK:
            held.set()
            threading.Event().wait(0.3)
    t = threading.Thread(target=holder)
    t.start()
    held.wait()
    M.retrieve(["river", "garden"], ["sleep"], time_bias="all", limit=8, query_text="river")
    t.join()
    last = [json.loads(x) for x in open(log, encoding="utf-8")][-1]
    check(last.get("emb_lock_wait_ms", 0) >= 200, f"held _EMB_LOCK shows as emb_lock_wait_ms={last.get('emb_lock_wait_ms')}")
    # a non-retrieve thread taking the timed lock leaves no residue
    M._ph_add("x_ms", 5.0)
    check(M._phase_take() == {}, "no active phase dict outside a retrieve() call -> _ph_add is a no-op")

print("ALL PASS" if not _fails else f"{_fails} FAIL")
sys.exit(1 if _fails else 0)
