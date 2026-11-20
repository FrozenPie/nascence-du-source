"""scripts/test_worker_thread_appends.py (J-1926 / F-2550, 2026-10-07) -- threaded hammer + negative control for the locks added to
the stores that BOTH a worker thread (asyncio.to_thread / off_loop / daemon Thread) and loop-thread code write.

Why: J-1918's stress_nolock control (scripts/test_idle_offloop_equivalence.py) showed that plain open(path, 'a') + write() appends
from several threads DO interleave on Windows (9 unparseable + 86 lost lines in 8 x 300 + 300 appends). J-1909/J-1917/J-1918 each
locked the stores they touched; this job audited every function reachable from a worker thread and locked the rest (see the
finding F-2550 follow-up for the full table). Nothing here touches the live data/: every store path is redirected to a
scratch dir, the harness prelude (scripts/lag_harness/_prelude.py) refuses any write under live C:\\Nascence and any network
connect, and no node / model code is imported.

usage (from the throwaway worktree, env LAGH_SCRATCH=<scratch dir> LAGH_WT=<worktree dir name under it>):
  python scripts/test_worker_thread_appends.py                  # hammer every store WITH its lock, then with the lock replaced by a no-op
  python scripts/test_worker_thread_appends.py --mode bytes --out OUT.json   # deterministic single-thread run: sha256 of every file written
                                                                  (run in the pre-change tree and in the new one, then --compare A B)
  python scripts/test_worker_thread_appends.py --compare A.json B.json

Per store the check is twofold, so the negative control is deterministic even where the real interleave is a rare window:
  (1) STRUCTURAL: builtins.open / Path.write_text / Path.replace / os.replace are wrapped; every write-mode touch of a file in that
      store's scratch dir records whether the store's lock was HELD BY THE CALLING THREAD at that instant. With the real lock: 0
      violations. With the lock replaced by a no-op: violations > 0 (the test FAILS without the lock).
  (2) OBSERVED: N threads x M calls against the real writer; exact line count, every line parses (appends), or exact counter /
      no torn read (read-modify-write stores). The control reports what actually happened without the lock (it may or may not
      reproduce a corruption in a short run; the structural check is the gate).
Exit 0 only when every WITH-LOCK run is clean AND every NO-LOCK run shows >= 1 structural violation."""
from __future__ import annotations

import argparse
import builtins
import hashlib
import json
import os
import pathlib
import sys
import threading
import time

ap = argparse.ArgumentParser()
ap.add_argument("--mode", choices=["check", "bytes"], default="check")
ap.add_argument("--out")
ap.add_argument("--compare", nargs=2)
ap.add_argument("--threads", type=int, default=8)
ap.add_argument("--iters", type=int, default=250)
ap.add_argument("--only")
args = ap.parse_args()
if os.environ.get("J1926_FH"):
    import faulthandler
    faulthandler.dump_traceback_later(int(os.environ["J1926_FH"]), exit=True)   # debugging aid: dump every thread's stack and exit

if args.compare:
    a = json.load(open(args.compare[0])); b = json.load(open(args.compare[1])); bad = 0
    for k in sorted(set(a) | set(b)):
        same = a.get(k) == b.get(k)
        print(f"{k}: {'IDENTICAL' if same else 'DIFFERENT'}")
        bad += (not same)
    sys.exit(1 if bad else 0)

SP = pathlib.Path(os.environ["LAGH_SCRATCH"]); WT = SP / os.environ["LAGH_WT"]
sys.path.insert(0, str(WT / "scripts" / "lag_harness"))
import _prelude as P            # noqa: E402,F401  (imports core FROM WT, asserts core/_DATA/DB_PATH are inside WT, marks live, audit hook on)
import core                     # noqa: E402
assert str(pathlib.Path(core.__file__).resolve()).lower().startswith(str(WT).lower()), core.__file__
assert os.path.normcase(str(WT)) != os.path.normcase(r"C:\Nascence")
P._NET["block"] = True          # (no event loop here, so the asyncio connect patch is moot; the socket.connect audit event is armed)
import socket                   # noqa: E402
try:
    socket.create_connection(("127.0.0.1", 9), timeout=1)
    print("FATAL: network NOT blocked"); sys.exit(2)
except PermissionError as _e:
    print("network block proven:", _e)
except OSError as _e:
    print("FATAL: connect attempt reached the OS:", _e); sys.exit(2)

import numpy as np                                                   # noqa: E402
from core import (arousal, geometry_census, loop_probe, watershed, life, retrieval_probe, r_shadow, peers, coupling_rides,  # noqa: E402
                  light_sidecar, content_risk, emotion_construction, telemetry, school, library_hand, book_selection, book_feelings)
from core.memory import store                                        # noqa: E402
for _m in (arousal, geometry_census, loop_probe, watershed, life, retrieval_probe, r_shadow, peers, coupling_rides, light_sidecar,
           content_risk, emotion_construction, telemetry, school, library_hand, book_selection, book_feelings, store):
    assert str(pathlib.Path(_m.__file__).resolve()).lower().startswith(str(WT).lower()), _m.__file__

OUT_DIR = SP / "J-1926_hammer"
OUT_DIR.mkdir(exist_ok=True)
T, M = args.threads, args.iters


class NoLock:
    """The negative control: same interface as a lock, excludes nothing."""
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def acquire(self, *a, **k): return True
    def release(self): pass
    def locked(self): return False
    def held_by_me(self): return False


class OwnerLock:
    """A real mutex that remembers its owner, so the probe can ask 'does the CALLING thread hold it right now'."""
    def __init__(self): self._l = threading.Lock(); self._owner = None
    def __enter__(self): self._l.acquire(); self._owner = threading.get_ident(); return self
    def __exit__(self, *a): self._owner = None; self._l.release(); return False
    def acquire(self, *a, **k):
        ok = self._l.acquire(*a, **k)
        if ok: self._owner = threading.get_ident()
        return ok
    def release(self): self._owner = None; self._l.release()
    def locked(self): return self._l.locked()
    def held_by_me(self): return self._owner == threading.get_ident()


class Probe:
    """Wrap every write-mode file touch under `root`; record the ones made while `lock.held_by_me()` is False."""
    def __init__(self, root: pathlib.Path, lock):
        self.root = os.path.normcase(str(root)); self.lock = lock; self.violations = 0; self.touches = 0; self._mu = threading.Lock()

    def _hit(self, p) -> bool:
        try:
            return os.path.normcase(os.path.abspath(os.fspath(p))).startswith(self.root)
        except Exception:
            return False

    def _note(self):
        with self._mu:
            self.touches += 1
            if not self.lock.held_by_me():
                self.violations += 1

    def __enter__(self):
        self._o = (builtins.open, pathlib.Path.write_text, pathlib.Path.replace, os.replace)
        probe = self
        o_open, o_wt, o_rep, o_osrep = self._o

        def _open(file, mode="r", *a, **k):
            if isinstance(mode, str) and any(c in mode for c in "wax+") and not isinstance(file, int) and probe._hit(file): probe._note()
            return o_open(file, mode, *a, **k)

        def _wt(self_, *a, **k):
            if probe._hit(self_): probe._note()
            return o_wt(self_, *a, **k)

        def _rep(self_, target):
            if probe._hit(self_): probe._note()
            return o_rep(self_, target)

        def _osrep(src, dst, *a, **k):
            if probe._hit(src): probe._note()
            return o_osrep(src, dst, *a, **k)
        builtins.open, pathlib.Path.write_text, pathlib.Path.replace, os.replace = _open, _wt, _rep, _osrep
        return self

    def __exit__(self, *a):
        builtins.open, pathlib.Path.write_text, pathlib.Path.replace, os.replace = self._o
        return False


def hammer(fn, threads=None, iters=None):
    threads = threads or T; iters = iters or M
    bar = threading.Barrier(threads); errs = []

    def run(tid):
        bar.wait()
        for i in range(iters):
            try:
                fn(tid, i)
            except Exception as e:   # noqa: BLE001
                errs.append(repr(e)[:160]); return
    ths = [threading.Thread(target=run, args=(t,)) for t in range(threads)]
    [t.start() for t in ths]; [t.join() for t in ths]
    return errs


def jsonl_stats(path: pathlib.Path):
    n = bad = 0
    if path.exists():
        for line in path.read_bytes().split(b"\n"):
            if not line.strip(): continue
            n += 1
            try: json.loads(line)
            except Exception: bad += 1
    return n, bad


# ------------------------------------------------------------------------------------------------ store table
# (name, module, {path_attr: file}, lock_attr, setup(d), call(tid,i), kind)   kind: "append:<file>" | "custom"
HEAVY: dict = {}   # per-store (threads, iters) overrides; none needed now that the arousal tonic read is stubbed


def _setup_arousal(d):
    arousal._LOG_EVERY = -1.0e9; arousal._TONIC_TTL = -1.0e9; arousal._last_log = 0.0; arousal._cache.update({"level": None, "ts": 0.0})
    arousal._tonic = lambda now: (0.4, {"stub": 1})   # the tonic is a ~100 ms homeostasis/log-tail read per call (a pure read); stubbed so the hammer reaches the append


def _setup_geo(d):
    geometry_census._MIN_GAP = 0.0; geometry_census._last_ts = 0.0; geometry_census._last_thought = None
    arousal._tonic = lambda now: (0.4, {'stub': 1})   # the arousal tonic is a ~100 ms read per call; stubbed (same as the arousal row)
    for k in range(2): geometry_census.snapshot(None, 'warm', f'warm{k}')   # warm the world-state caches single-threaded first (production state; a cold 4-thread first load is itself the unsynchronised first-load race noted in the audit)
    geometry_census._last_ts = 0.0; geometry_census._last_thought = None
    pathlib.Path(geometry_census._LOG).unlink(missing_ok=True)   # drop the two warm-up rows: the hammer expects exactly threads x iters


def _setup_loop_probe(d):
    loop_probe._seen = {}


def _setup_watershed(d):
    watershed._batch_mode = False


META = {"title": "t", "author": "Dixon, Thomas", "downloads": 3, "subjects": "Fiction -- Test; Adventure"}

STORES = [
    ("arousal.level -> arousal_shadow.jsonl", arousal, {"_LOG": "a.jsonl"}, "_APPEND_LOCK", _setup_arousal,
     lambda t, i: arousal.level(), "append:a.jsonl"),
    ("geometry_census.snapshot -> geometry log", geometry_census, {"_LOG": "g.jsonl"}, "_APPEND_LOCK", _setup_geo,
     lambda t, i: geometry_census.snapshot(None, "hammer", f"t{t}-{i}"), "append:g.jsonl"),
    ("loop_probe.shadow_observe -> loop_probe_log", loop_probe, {"_LOG": "l.jsonl"}, "_APPEND_LOCK", _setup_loop_probe,
     lambda t, i: loop_probe.shadow_observe("inner_thought", f"c{t}-{i}"), "append:l.jsonl"),
    ("watershed._log_row -> watershed shadow log", watershed, {"_LOG": "w.jsonl"}, "_IO_LOCK", _setup_watershed,
     lambda t, i: watershed._log_row({"ts": i, "t": t, "pad": "x" * 200}), "append:w.jsonl"),
    ("watershed._save_state (shared tmp name)", watershed, {"_STATE": "ws_state.json"}, "_IO_LOCK", _setup_watershed,
     lambda t, i: watershed._save_state({"t": t, "i": i, "pad": "y" * 400}), "state:ws_state.json"),
    ("life._log -> any life ledger", life, {}, "_APPEND_LOCK", lambda d: None,
     lambda t, i: life._log(OUT_DIR / "life" / "life.jsonl", {"t": t, "i": i, "pad": "z" * 200}), "append:life.jsonl"),
    ("retrieval_probe.observe -> retrieval_probe_log", retrieval_probe, {"_LOG": "rp.jsonl"}, "_APPEND_LOCK", lambda d: None,
     lambda t, i: retrieval_probe.observe(f"q{t}-{i} " + "w" * 150, [], set(), [], "hammer"), "append:rp.jsonl"),
    ("r_shadow.log_observation -> r_shadow.jsonl", r_shadow, {"_SHADOW_LOG": "rs.jsonl"}, "_APPEND_LOCK", lambda d: None,
     lambda t, i: r_shadow.log_observation(f"h{t}-{i}", []), "append:rs.jsonl"),
    ("store._log_retrieve_latency -> retrieve_latency_probe", store, {"_RETRIEVE_LATENCY_LOG": "rl.jsonl"}, "_LATENCY_LOG_LOCK", lambda d: None,
     lambda t, i: store._log_retrieve_latency(t, i, 0.5, 0.25), "append:rl.jsonl"),
    ("peers.log_reflection_injection -> peer_reflection_injection_log", peers, {"_PEER_REFLECTION_INJECT_LOG": "pr.jsonl"}, "_APPEND_LOCK",
     lambda d: None, lambda t, i: peers.log_reflection_injection(f"c{t}-{i}", "n" * 200), "append:pr.jsonl"),
    ("coupling_rides._append -> coupling_rides.jsonl", coupling_rides, {"_LOG": "cr.jsonl"}, "_APPEND_LOCK", lambda d: None,
     lambda t, i: coupling_rides._append({"t": t, "i": i, "pad": "c" * 200}), "append:cr.jsonl"),
    ("light_sidecar.shadow_log -> light_sidecar_shadow", light_sidecar, {"SHADOW_LOG": "ls.jsonl"}, "_APPEND_LOCK", lambda d: None,
     lambda t, i: light_sidecar.shadow_log("hammer", i, i, 1.0, 2.0, t=t, pad="s" * 150), "append:ls.jsonl"),
    ("content_risk.shadow_check -> content_risk_shadow", content_risk, {"_LOG": "cx.jsonl"}, "_APPEND_LOCK", lambda d: None,
     lambda t, i: content_risk.shadow_check(META, context=f"h{t}-{i}"), "append:cx.jsonl"),
    ("library_hand._save_last_fetch (shared tmp name)", library_hand, {"_FETCH_STATE": "lf.json"}, "_FETCH_STATE_LOCK", lambda d: None,
     lambda t, i: library_hand._save_last_fetch(1.0e9 + t * 1000 + i), "state:lf.json"),
]


def run_store(spec, with_lock: bool):
    name, mod, paths, lock_attr, setup, call, kind = spec
    d = OUT_DIR / ("L" if with_lock else "N") / (name.split(" ")[0].replace(".", "_"))
    if d.exists():
        for f in d.glob("*"): f.unlink()
    d.mkdir(parents=True, exist_ok=True)
    saved = {a: getattr(mod, a) for a in paths}
    saved_lock = getattr(mod, lock_attr)
    for a, f in paths.items(): setattr(mod, a, d / f)
    lk = OwnerLock() if with_lock else NoLock()
    setattr(mod, lock_attr, lk)
    setup(d)
    th, it = HEAVY.get(name.split(" ")[0], (T, M))
    try:
        if mod is life:
            fn = lambda t, i: life._log(d / "life.jsonl", {"t": t, "i": i, "pad": "z" * 200})
        else:
            fn = call
        with Probe(d, lk) as pr:
            errs = hammer(fn, threads=th, iters=it)
        res = {"name": name, "with_lock": with_lock, "errors": errs[:2], "touches": pr.touches, "violations": pr.violations}
        k, _, f = kind.partition(":")
        if k == "append":
            n, bad = jsonl_stats(d / f)
            res.update(lines=n, bad=bad, expected=th * it)
            res["clean"] = (n == th * it and bad == 0 and not errs)
        else:   # shared-tmp state file: the file must parse and no tmp left over; calls swallow their own errors, so only the structural gate is exact
            ok = True
            try: json.loads((d / f).read_text(encoding="utf-8"))
            except Exception: ok = False
            res.update(state_parses=ok, tmp_left=sorted(p.name for p in d.glob("*.tmp")))
            res["clean"] = ok and not res["tmp_left"] and not errs
        return res
    finally:
        for a, v in saved.items(): setattr(mod, a, v)
        setattr(mod, lock_attr, saved_lock)


# ------------------------------------------------------------------------------------------------ the read-modify-write / read-vs-rewrite stores
def run_telemetry(with_lock: bool):
    d = OUT_DIR / ("L" if with_lock else "N") / "telemetry"; d.mkdir(parents=True, exist_ok=True)
    f = d / "llm_calls.jsonl"
    for p in d.glob("*"): p.unlink()
    saved = (telemetry._CALLS, telemetry._JSONL_LOCK, telemetry._LAB_MODE)
    telemetry._CALLS = f; telemetry._LAB_MODE = False
    lk = OwnerLock() if with_lock else NoLock(); telemetry._JSONL_LOCK = lk
    f.write_text("".join(json.dumps({"ts": 0, "model": "pre", "node": "n", "by": f"pre{k}"}) + "\n" for k in range(8000)), encoding="utf-8")
    N = 6000; stop = threading.Event(); caps = [0]; errs = []

    def capper():
        while not stop.is_set():
            telemetry._cap(f, 6000); caps[0] += 1

    def appender():
        try:
            for s in range(N):
                telemetry.log_llm_call("m", "n", caller=f"s{s}")
        except Exception as e:   # noqa: BLE001
            errs.append(repr(e))
    try:
        with Probe(d, lk) as pr:
            c = threading.Thread(target=capper); a = threading.Thread(target=appender); c.start(); a.start(); a.join(); stop.set(); c.join()
        seqs = []; bad = 0
        for line in f.read_bytes().split(b"\n"):
            if not line.strip(): continue
            try:
                r = json.loads(line)
                if str(r.get("by", "")).startswith("s"): seqs.append(int(r["by"][1:]))
            except Exception: bad += 1
        # cap only ever drops the OLDEST lines, so the surviving appender sequence numbers must be one contiguous run ending at N-1
        gaps = (seqs[-1] - seqs[0] + 1 - len(seqs)) if seqs else -1
        ends_ok = bool(seqs) and seqs[-1] == N - 1
        return {"name": "telemetry.log_llm_call vs _cap (llm_calls.jsonl rewrite)", "with_lock": with_lock, "errors": errs, "touches": pr.touches,
                "violations": pr.violations, "caps_run": caps[0], "appended": N, "surviving": len(seqs), "lost_lines_in_middle": gaps,
                "unparseable": bad, "ends_at_last": ends_ok, "clean": (gaps == 0 and bad == 0 and ends_ok and not errs)}
    finally:
        telemetry._CALLS, telemetry._JSONL_LOCK, telemetry._LAB_MODE = saved


def run_school(with_lock: bool):
    d = OUT_DIR / ("L" if with_lock else "N") / "school"; d.mkdir(parents=True, exist_ok=True)
    f = d / "school.json"
    for p in d.glob("*"): p.unlink()
    saved = (school.STATE, school._IO_LOCK); school.STATE = f
    lk = OwnerLock() if with_lock else NoLock(); school._IO_LOCK = lk
    full = {"assigned_book": "b", "assigned_title": "t", "sessions_per_day": 3, "today_done": 1, "curriculum": ["x"] * 20, "curriculum_idx": 5,
            "history": [{"ts": k, "title": "book %d" % k, "pad": "p" * 40} for k in range(2500)]}
    school._save(full)
    stop = threading.Event(); torn = [0]; reads = [0]; errs = []

    def reader():
        while not stop.is_set():
            got = school._load()
            reads[0] += 1
            if len(got.get("history", [])) != 2500: torn[0] += 1      # the DEFAULT dict (history == []) came back: the file read as torn/empty

    def writer():
        for _ in range(250):
            school._save(full)
    try:
        with Probe(d, lk) as pr:
            rs = [threading.Thread(target=reader) for _ in range(4)]; ws = [threading.Thread(target=writer) for _ in range(2)]
            [t.start() for t in rs + ws]; [t.join() for t in ws]; stop.set(); [t.join() for t in rs]
        return {"name": "school._save (truncate+write) vs _load (loop-thread reader)", "with_lock": with_lock, "errors": errs, "touches": pr.touches,
                "violations": pr.violations, "reads": reads[0], "torn_reads_returning_default": torn[0], "clean": torn[0] == 0}
    finally:
        school.STATE, school._IO_LOCK = saved


def run_book_selection(with_lock: bool):
    d = OUT_DIR / ("L" if with_lock else "N") / "book_selection"; d.mkdir(parents=True, exist_ok=True)
    for p in d.glob("*"): p.unlink()
    saved = (book_selection.COVERAGE, book_selection.LOG, book_selection._RECORD_LOCK, content_risk._LOG, content_risk._APPEND_LOCK)
    book_selection.COVERAGE = d / "cov.json"; book_selection.LOG = d / "sel.jsonl"; content_risk._LOG = d / "cx.jsonl"
    lk = OwnerLock() if with_lock else NoLock(); book_selection._RECORD_LOCK = lk
    content_risk._APPEND_LOCK = OwnerLock() if with_lock else NoLock()
    meta = {"title": "t", "author": "nobody", "downloads": 3, "subjects": "Fiction"}
    try:
        with Probe(d, lk) as pr:
            errs = hammer(lambda t, i: book_selection.record_pick(meta, reason="hammer"), threads=6, iters=60)
        n, bad = jsonl_stats(d / "sel.jsonl")
        try: cov = json.loads((d / "cov.json").read_text(encoding="utf-8")); counted = sum(cov.get("subjects", {}).values())
        except Exception: counted = -1
        return {"name": "book_selection.record_pick (coverage load->bump->write + log)", "with_lock": with_lock, "errors": errs[:2], "touches": pr.touches,
                "violations": pr.violations, "log_lines": n, "bad": bad, "coverage_counted": counted, "expected": 360,
                "clean": (n == 360 and bad == 0 and counted == 360 and not errs)}
    finally:
        (book_selection.COVERAGE, book_selection.LOG, book_selection._RECORD_LOCK, content_risk._LOG, content_risk._APPEND_LOCK) = saved


def run_book_feelings(with_lock: bool):
    d = OUT_DIR / ("L" if with_lock else "N") / "book_feelings"; d.mkdir(parents=True, exist_ok=True)
    for p in d.glob("*"): p.unlink()
    saved = (book_feelings._DATA, book_feelings._RMW_LOCK); book_feelings._DATA = d / "bf.json"
    lk = OwnerLock() if with_lock else NoLock(); book_feelings._RMW_LOCK = lk
    try:
        with Probe(d, lk) as pr:
            errs = hammer(lambda t, i: (book_feelings.touch("A Book", 0.1) if t % 2 == 0 else book_feelings.capstone("A Book", 0.1, 0.5, 0.2)), threads=6, iters=60)
        try: rec = json.loads((d / "bf.json").read_text(encoding="utf-8")).get("abook", {}); sit = rec.get("sittings", -1)
        except Exception: sit = -1
        return {"name": "book_feelings.touch (worker) vs capstone (loop): load->mutate->save", "with_lock": with_lock, "errors": errs[:2], "touches": pr.touches,
                "violations": pr.violations, "sittings": sit, "expected": 3 * 60, "clean": (sit == 180 and not errs)}
    finally:
        book_feelings._DATA, book_feelings._RMW_LOCK = saved


def run_emotion_log(with_lock: bool):
    """_affective_retrieval_shadow itself (a per-cycle daemon thread: DB read + rank + one append). Real function on the data copy, tiny candidate cap."""
    d = OUT_DIR / ("L" if with_lock else "N") / "emotion"; d.mkdir(parents=True, exist_ok=True)
    for p in d.glob("*"): p.unlink()
    saved = (emotion_construction._AR_SHADOW_LOG, emotion_construction._AR_LOG_LOCK); emotion_construction._AR_SHADOW_LOG = d / "ar.jsonl"
    lk = OwnerLock() if with_lock else NoLock(); emotion_construction._AR_LOG_LOCK = lk
    vec = np.zeros(384, dtype=np.float32); vec[0] = 1.0   # the stored emotion_embedding dimension
    try:
        with Probe(d, lk) as pr:
            errs = hammer(lambda t, i: emotion_construction._affective_retrieval_shadow(vec, vec, None, f"c{t}-{i}", max_candidates=5), threads=4, iters=6)
        n, bad = jsonl_stats(d / "ar.jsonl")
        return {"name": "emotion_construction._affective_retrieval_shadow (daemon thread per cycle)", "with_lock": with_lock, "errors": errs[:2], "touches": pr.touches,
                "violations": pr.violations, "lines": n, "bad": bad, "expected": 24, "clean": (n == 24 and bad == 0 and not errs)}
    finally:
        emotion_construction._AR_SHADOW_LOG, emotion_construction._AR_LOG_LOCK = saved


# ------------------------------------------------------------------------------------------------ bytes mode (old vs new equivalence)
def run_bytes(out):
    d = OUT_DIR / "bytes"; d.mkdir(exist_ok=True)
    for p in d.glob("**/*"):
        if p.is_file(): p.unlink()
    clock = [1_790_000_000.0]
    real = time.time
    time.time = lambda: (clock.__setitem__(0, clock[0] + 1.0), clock[0])[1]
    res = {}
    try:
        for spec in STORES:
            name, mod, paths, lock_attr, setup, call, kind = spec
            sd = d / name.split(" ")[0].replace(".", "_"); sd.mkdir(exist_ok=True)
            saved = {a: getattr(mod, a) for a in paths}
            for a, f in paths.items(): setattr(mod, a, sd / f)
            setup(sd)
            try:
                if name.startswith(("arousal", "geometry_census")):
                    continue   # these read live-shaped world state; their change is the one-token `with LOCK, open(...)` (see the diff)
                for t in range(2):
                    for i in range(5):
                        if mod is life: life._log(sd / "life.jsonl", {"t": t, "i": i, "pad": "z" * 200})
                        else: call(t, i)
            finally:
                for a, v in saved.items(): setattr(mod, a, v)
            for p in sorted(sd.glob("*")):
                if p.is_file() and not p.name.endswith(".tmp"): res[f"{name.split(' ')[0]}:{p.name}"] = hashlib.sha256(p.read_bytes()).hexdigest()
        # the four read-modify-write / rewrite stores, single-threaded, same inputs in both trees
        sd = d / "extra"; sd.mkdir(exist_ok=True)
        sv = (telemetry._CALLS, telemetry._LAB_MODE, school.STATE, book_feelings._DATA, book_selection.COVERAGE, book_selection.LOG, content_risk._LOG)
        telemetry._CALLS = sd / "llm_calls.jsonl"; telemetry._LAB_MODE = False; school.STATE = sd / "school.json"
        book_feelings._DATA = sd / "bf.json"; book_selection.COVERAGE = sd / "cov.json"; book_selection.LOG = sd / "sel.jsonl"; content_risk._LOG = sd / "cx.jsonl"
        try:
            for i in range(30): telemetry.log_llm_call("m", "n", prompt_chars=i, caller=f"c{i}")
            telemetry._cap(telemetry._CALLS, 10)
            school._save({"assigned_book": "b", "history": [{"i": k} for k in range(40)]}); school._save(school._load() | {"today_done": 2})
            for i in range(6): book_feelings.touch("A Book", 0.1 * i)
            book_feelings.capstone("A Book", 0.2, 0.6, 0.3)
            for i in range(6): book_selection.record_pick({"title": f"t{i}", "author": "Dixon, Thomas", "downloads": i, "subjects": "Fiction"}, reason="bytes")
        finally:
            (telemetry._CALLS, telemetry._LAB_MODE, school.STATE, book_feelings._DATA, book_selection.COVERAGE, book_selection.LOG, content_risk._LOG) = sv
        for p in sorted(sd.glob("*")):
            if p.is_file() and not p.name.endswith(".tmp"): res[f"extra:{p.name}"] = hashlib.sha256(p.read_bytes()).hexdigest()
    finally:
        time.time = real
    json.dump(res, open(out, "w"), indent=1, sort_keys=True)
    print("bytes mode: hashed", len(res), "files ->", out)


if args.mode == "bytes":
    assert args.out
    run_bytes(args.out)
    sys.exit(0)

# ------------------------------------------------------------------------------------------------ check mode
rows = []; fail = 0
runners = [("store", s) for s in STORES] + [("fn", run_telemetry), ("fn", run_school), ("fn", run_book_selection), ("fn", run_book_feelings), ("fn", run_emotion_log)]
for kind, r in runners:
    nm = r[0] if kind == "store" else r.__name__
    if args.only and args.only not in nm: continue
    pair = []
    for with_lock in (True, False):
        res = run_store(r, with_lock) if kind == "store" else r(with_lock)
        pair.append(res)
    L, N = pair
    ok_with = L["clean"] and L["violations"] == 0 and L["touches"] > 0
    ok_ctl = N["violations"] > 0
    rows.append((L, N, ok_with, ok_ctl))
    if not (ok_with and ok_ctl): fail += 1
    print(f"\n=== {L['name']}")
    print("  WITH lock   :", {k: v for k, v in L.items() if k not in ("name", "with_lock")})
    print("  NO lock ctl :", {k: v for k, v in N.items() if k not in ("name", "with_lock")})
    print("  verdict     :", "PASS" if (ok_with and ok_ctl) else "FAIL", f"(with-lock clean={ok_with}, control fails structurally={ok_ctl}, control observed corruption={not N['clean']})")

print("\nSUMMARY: %d stores, %d failing; control observed real corruption in %d of %d" % (len(rows), fail, sum(1 for r in rows if not r[1]["clean"]), len(rows)))
sys.exit(1 if fail else 0)
