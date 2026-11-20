"""scripts/test_sleep_offloop_equivalence.py (J-1917 / F-2546): offline proof that running the sleep-consolidation sweeps in a
worker thread (core/sleep_offloop.off_loop) changes TIMING ONLY.

Runs inside scripts/lag_harness' prelude (audit hook: no write under live C:\\Nascence, no subprocess, network blocked once
_NET['block'] is set) against a FULL-fidelity data/ copy inside a throwaway worktree. No model call can happen: only core
data modules are imported (never nodes/*), and the block is PROVEN first (a connect to a closed local port must be refused
by the prelude, not by the OS).

env: LAGH_SCRATCH (dir holding the worktrees), LAGH_WT (worktree dir name under it: wt_old = HEAD code, wt_new = this change)
usage: python test_sleep_offloop_equivalence.py --mode old|new|stress --out OUT.json --now EPOCH [--passes 1|2]
  old    the plain synchronous calls on the loop thread (the pre-J-1917 code path)
  new    each call awaited through core.sleep_offloop.off_loop (a worker thread)
  stress new + a loop-thread file_book_notes()/DB-write storm overlapping the worker sweep (lock + sqlite proof)
Each pass runs, in the node's order: psyche_graph.snapshot (unchanged, sync), stick_test.snapshot, peer_metrics.snapshot,
holdrate_snapshot, world_consolidation.sweep, book_residue.sweep, with a 0.1 s canary timer on the same loop. time.time()
is frozen to --now so every ts / now-relative window is identical between runs; outputs are the raw bytes appended to each
jsonl, the return values, and a hash of (fragment_id, chapter_id) over all memory_fragments. Pass 2 first NULLs chapter_id
of every filed reading/study fragment (identically in both copies) so the sweep has real UPDATEs to do."""
import sys, os, time, json, asyncio, pathlib, hashlib, argparse, sqlite3, threading, traceback

ap = argparse.ArgumentParser()
ap.add_argument("--mode", required=True, choices=["old", "new", "stress"])
ap.add_argument("--out", required=True)
ap.add_argument("--now", type=float, required=True)
ap.add_argument("--passes", type=int, default=2)
args = ap.parse_args()

SP = pathlib.Path(os.environ["LAGH_SCRATCH"]); WT = SP / os.environ["LAGH_WT"]
sys.path.insert(0, str(WT / "scripts" / "lag_harness"))
import _prelude as P            # noqa: E402  (imports core FROM WT, asserts core/_DATA/DB_PATH are inside WT, marks live)
import core                     # noqa: E402
assert str(pathlib.Path(core.__file__).resolve()).lower().startswith(str(WT).lower()), core.__file__
DATA = WT / "data"
from core import psyche_graph, stick_test, peer_metrics, commitment_ledger, world_consolidation, book_residue  # noqa: E402
from core.memory import store                                                                                    # noqa: E402
for m in (psyche_graph, stick_test, peer_metrics, commitment_ledger, world_consolidation, book_residue):
    assert str(pathlib.Path(m.__file__).resolve()).lower().startswith(str(WT).lower()), m.__file__
assert str(store.DB_PATH).lower().startswith(str(WT).lower())
off_loop = None
if args.mode != "old":
    from core import sleep_offloop
    assert sleep_offloop.SLEEP_SWEEPS_OFFLOOP is True
    off_loop = sleep_offloop.off_loop

FILES = {"stick_test_log": "stick_test_log.jsonl", "commitment_holdrate": "commitment_holdrate.jsonl",
         "peer_effect": "peer_effect.jsonl", "world_consolidation_log": "world_consolidation_log.jsonl",
         "psyche_graph_snapshots": "psyche_graph_snapshots.jsonl", "book_residue": "book_residue.jsonl"}
_real_time = time.time
time.time = lambda: args.now            # frozen: identical ts and windows in both runs (asyncio uses monotonic)


def sizes():
    return {k: ((DATA / v).stat().st_size if (DATA / v).exists() else 0) for k, v in FILES.items()}


def appended(before):
    out = {}
    for k, v in FILES.items():
        p = DATA / v
        b = b""
        if p.exists() and p.stat().st_size > before[k]:
            with open(p, "rb") as f:
                f.seek(before[k]); b = f.read()
        out[k] = {"bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()}
    return out


def chapter_hash():
    c = sqlite3.connect(str(store.DB_PATH), timeout=60)
    h = hashlib.sha256(); n = nn = 0
    for fid, ch in c.execute("SELECT fragment_id, chapter_id FROM memory_fragments ORDER BY fragment_id"):
        h.update(f"{fid}\x00{ch}\n".encode()); n += 1; nn += ch is None
    c.close()
    return {"rows": n, "null_chapter": nn, "sha256": h.hexdigest()}


def refile_prep():
    c = sqlite3.connect(str(store.DB_PATH), timeout=60)
    cur = c.execute("UPDATE memory_fragments SET chapter_id=NULL WHERE origin IN ('reading','study') AND chapter_id IS NOT NULL")
    c.commit(); n = cur.rowcount; c.close()
    return n


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
    def __init__(self):
        self.rows = []; self.stop = False
    async def run(self):
        last = time.perf_counter()
        while not self.stop:
            await asyncio.sleep(0.1)
            now = time.perf_counter()
            self.rows.append((now, now - last - 0.1)); last = now
    def window(self, t0, t1):
        lags = [l for (t, l) in self.rows if t0 <= t <= t1 + 0.5]
        return {"ticks": len(lags), "max_lag_s": round(max(lags), 4) if lags else None}


async def call(fn, *a):
    return fn(*a) if args.mode == "old" else await off_loop(fn, *a)


async def storm(stop_evt, stats, titles):
    """Loop-thread traffic overlapping the worker sweep: file_book_notes (as essay_lesson does) + sqlite writes."""
    c = store._connect()
    c.execute("CREATE TABLE IF NOT EXISTS j1917_scratch (k INTEGER PRIMARY KEY, v TEXT)"); c.commit()
    i = 0
    while not stop_evt.is_set():
        i += 1
        try:
            t0 = time.perf_counter()
            r = world_consolidation.file_book_notes(titles[i % len(titles)], now=args.now)
            stats["fbn_calls"] += 1; stats["fbn_max_block_s"] = max(stats["fbn_max_block_s"], time.perf_counter() - t0)
            if str(r.get("reason", "")).startswith("error"):
                stats["fbn_errors"].append(r["reason"])
            c.execute("INSERT OR REPLACE INTO j1917_scratch VALUES (?,?)", (i, "x" * 50)); c.commit(); stats["writes"] += 1
        except Exception as e:
            stats["exceptions"].append(repr(e)[:150])
        await asyncio.sleep(0.02)
    c.close()


async def one_pass(label, canary):
    res = {"label": label}
    before = sizes(); res["pre_chapter"] = chapter_hash()
    await asyncio.sleep(0.5)   # the synchronous prep above (and refile_prep) must not be charged to the first step's canary window
    timings = {}; rets = {}
    stats = {"fbn_calls": 0, "fbn_max_block_s": 0.0, "fbn_errors": [], "writes": 0, "exceptions": []}
    stop = asyncio.Event(); st_task = None
    if args.mode == "stress":
        titles = []
        c = sqlite3.connect(f"file:{store.DB_PATH}?mode=ro", uri=True)
        import re as _re
        for (t,) in c.execute("SELECT content FROM memory_fragments WHERE origin IN ('essay','understanding')"):
            m = _re.search(r"(?:on|from) '([^']+)'", t or "")
            if m: titles.append(m.group(1).strip())
        c.close(); titles = sorted(set(titles))[:25]
        st_task = asyncio.create_task(storm(stop, stats, titles))
    steps = [("psyche_graph.snapshot", None), ("stick_test.snapshot", stick_test.snapshot),
             ("peer_metrics.snapshot", peer_metrics.snapshot), ("holdrate_snapshot", commitment_ledger.holdrate_snapshot),
             ("world_consolidation.sweep", world_consolidation.sweep), ("book_residue.sweep", book_residue.sweep)]
    for name, fn in steps:
        t0 = time.perf_counter()
        if fn is None:
            r = psyche_graph.snapshot()           # unchanged: stays synchronous in the node as well
        else:
            r = await call(fn)
        t1 = time.perf_counter()
        timings[name] = round(t1 - t0, 2); rets[name] = jsonable(r)
        res.setdefault("canary", {})[name] = canary.window(t0, t1)
        print(f"[{label}] {name}: {t1 - t0:.1f}s canary={res['canary'][name]}", flush=True)
    if st_task:
        stop.set(); await st_task
        res["storm"] = {k: (v if not isinstance(v, list) else v[:5]) for k, v in stats.items()}
        res["storm"]["fbn_error_count"] = len(stats["fbn_errors"]); res["storm"]["exception_count"] = len(stats["exceptions"])
    res["timings_s"] = timings; res["returns"] = rets
    res["appended"] = appended(before); res["post_chapter"] = chapter_hash()
    return res


async def main():
    out = {"mode": args.mode, "wt": str(WT), "now": args.now, "core_file": core.__file__}
    out["network_block_proof"] = await prove_no_network()
    print("network block proof:", out["network_block_proof"], flush=True)
    assert out["network_block_proof"]["blocked_by_prelude"], "prelude network block NOT proven; refusing to run"
    out["subprocess_attempts"] = P._SUBP
    canary = Canary(); ct = asyncio.create_task(canary.run())
    await asyncio.sleep(0.5)
    out["passes"] = []
    out["passes"].append(await one_pass("pass1_as_is", canary))
    if args.passes >= 2:
        out["refile_nulled"] = refile_prep()
        out["passes"].append(await one_pass("pass2_refile", canary))
    canary.stop = True; await ct
    allv = [l for (_t, l) in canary.rows]
    out["canary_overall"] = {"ticks": len(allv), "max_lag_s": round(max(allv), 4), "p99_lag_s": round(sorted(allv)[int(len(allv) * .99)], 4)}
    if args.mode == "stress":
        c = sqlite3.connect(str(store.DB_PATH)); out["integrity_check"] = c.execute("PRAGMA integrity_check").fetchone()[0]; c.close()
    out["subprocess_attempts_after"] = P._SUBP
    json.dump(out, open(args.out, "w"), indent=1)
    print("wrote", args.out)

asyncio.run(main())
