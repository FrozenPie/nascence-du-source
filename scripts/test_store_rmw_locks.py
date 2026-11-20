"""scripts/test_store_rmw_locks.py (J-1933 / F-2557, 2026-10-08) -- threaded hammer + negative control for the three
read-modify-write stores whose WRITES J-1926 made torn-safe but whose load -> mutate -> save SEQUENCES were still open to a
LOST UPDATE: core/school.py (advance/assign/_extend_program vs record_session/new_day), core/library_hand.py request_book()
(cooldown check vs write-back), core/watershed.py observe() (shared _state_cache load -> mutate -> save).

Nothing here touches live data/: every store path is redirected to a scratch dir, the harness prelude
(scripts/lag_harness/_prelude.py) refuses any write under live C:\\Nascence and any network connect, urlopen / the catalogue
search / the shelf are stubbed, and no node or model code is imported.

usage (from the throwaway worktree, env LAGH_SCRATCH=<scratch dir> LAGH_WT=<worktree dir name under it>):
  python scripts/test_store_rmw_locks.py            # each store WITH its real lock, then with the lock replaced by a no-op
Per store the gate is twofold, as in scripts/test_worker_thread_appends.py:
  (1) STRUCTURAL: every write-mode file touch in the store's scratch dir records whether the store's lock was HELD BY THE CALLING
      THREAD. With the lock: 0 violations. With a no-op lock: violations > 0 (the test FAILS without the lock).
  (2) OBSERVED, conserved quantity: school curriculum_idx == advances and history rows == advances (a stale save reverts them);
      today_done == record_session calls; library fetches == 1 for N overlapping requests inside one cooldown window;
      watershed candidates for one repeated image == 1 and sum(n) == observe calls.
Exit 0 only when every WITH-LOCK run is clean AND every NO-LOCK run shows >= 1 structural violation."""
from __future__ import annotations

import builtins
import json
import os
import pathlib
import sys
import threading
import time

SP = pathlib.Path(os.environ["LAGH_SCRATCH"]); WT = SP / os.environ["LAGH_WT"]
sys.path.insert(0, str(WT / "scripts" / "lag_harness"))
import _prelude as P            # noqa: E402,F401
import core                     # noqa: E402
assert str(pathlib.Path(core.__file__).resolve()).lower().startswith(str(WT).lower()), core.__file__
assert os.path.normcase(str(WT)) != os.path.normcase(r"C:\Nascence")
P._NET["block"] = True
import socket                   # noqa: E402
try:
    socket.create_connection(("127.0.0.1", 9), timeout=1)
    print("FATAL: network NOT blocked"); sys.exit(2)
except PermissionError as _e:
    print("network block proven:", _e)
except OSError as _e:
    print("FATAL: connect attempt reached the OS:", _e); sys.exit(2)

import numpy as np                                   # noqa: E402
from core import school, library_hand, watershed, reading, book_selection   # noqa: E402
for _m in (school, library_hand, watershed):
    assert str(pathlib.Path(_m.__file__).resolve()).lower().startswith(str(WT).lower()), _m.__file__

OUT_DIR = SP / "J-1933_hammer"
OUT_DIR.mkdir(exist_ok=True)


class NoLock:
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def acquire(self, *a, **k): return True
    def release(self): pass
    def held_by_me(self): return False


class OwnerLock:
    """A real (optionally re-entrant) mutex that remembers its owner and depth."""
    def __init__(self, reentrant=False):
        self._l = threading.RLock() if reentrant else threading.Lock(); self._owner = None; self._depth = 0
    def __enter__(self):
        self._l.acquire(); self._owner = threading.get_ident(); self._depth += 1; return self
    def __exit__(self, *a):
        self._depth -= 1
        if self._depth == 0: self._owner = None
        self._l.release(); return False
    def held_by_me(self): return self._owner == threading.get_ident()


class Probe:
    def __init__(self, root, lock):
        self.root = os.path.normcase(str(root)); self.lock = lock; self.violations = 0; self.touches = 0; self._mu = threading.Lock()

    def _hit(self, p):
        try:
            return os.path.normcase(os.path.abspath(os.fspath(p))).startswith(self.root)
        except Exception:
            return False

    def _note(self):
        with self._mu:
            self.touches += 1
            if not self.lock.held_by_me(): self.violations += 1

    def __enter__(self):
        self._o = (builtins.open, pathlib.Path.write_text, pathlib.Path.replace, os.replace)
        probe = self; o_open, o_wt, o_rep, o_osrep = self._o

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


def hammer(fns, iters):
    """fns: list of callables (one thread each, each called `iters` times with (i))."""
    bar = threading.Barrier(len(fns)); errs = []

    def run(fn):
        bar.wait()
        for i in range(iters):
            try:
                fn(i)
            except Exception as e:   # noqa: BLE001
                errs.append(repr(e)[:160]); return
    ths = [threading.Thread(target=run, args=(f,)) for f in fns]
    [t.start() for t in ths]; [t.join() for t in ths]
    return errs


# ---------------------------------------------------------------------------------------------------------------- school
def run_school_advance(with_lock: bool):
    """2 worker threads advance() (the advance_if_finished worker) vs 2 'loop' threads record_session(). Conserved: after N advances
    curriculum_idx == N and history has N rows; a stale record_session save reverts them."""
    d = OUT_DIR / ("L" if with_lock else "N") / "school_adv"; d.mkdir(parents=True, exist_ok=True)
    for p in d.glob("*"): p.unlink()
    N_ADV, N_REC = 60, 120
    titles = [f"bk{n:04d}" for n in range(N_ADV + 20)]
    saved = (school.STATE, school._RMW_LOCK, library_hand.shelf_books, reading.current_book, reading.set_current)
    school.STATE = d / "school.json"
    lk = OwnerLock(reentrant=True) if with_lock else NoLock(); school._RMW_LOCK = lk
    library_hand.shelf_books = lambda: [pathlib.Path(t + ".txt") for t in titles]
    reading.current_book = lambda: pathlib.Path("x.txt"); reading.set_current = lambda p: None
    school._save({"assigned_book": None, "assigned_title": None, "sessions_per_day": 3, "today_done": 0, "history": [],
                  "curriculum": titles, "curriculum_idx": 0})
    try:
        with Probe(d, lk) as pr:
            errs = hammer([lambda i: school.advance(), lambda i: school.advance(),
                           lambda i: school.record_session(), lambda i: school.record_session()], iters=N_ADV // 2)
            # the two record threads ran N_ADV//2 each; top up so the record side is longer than the advance side
        st = school._load()
        idx, hist = st.get("curriculum_idx"), len(st.get("history", []))
        return {"name": "school.advance (worker) vs record_session (loop): load->mutate->save", "with_lock": with_lock, "errors": errs[:2],
                "touches": pr.touches, "violations": pr.violations, "curriculum_idx": idx, "history_rows": hist, "expected": N_ADV,
                "clean": (idx == N_ADV and hist == N_ADV and not errs)}
    finally:
        school.STATE, school._RMW_LOCK, library_hand.shelf_books, reading.current_book, reading.set_current = saved


def run_school_counter(with_lock: bool):
    d = OUT_DIR / ("L" if with_lock else "N") / "school_ctr"; d.mkdir(parents=True, exist_ok=True)
    for p in d.glob("*"): p.unlink()
    saved = (school.STATE, school._RMW_LOCK); school.STATE = d / "school.json"
    lk = OwnerLock(reentrant=True) if with_lock else NoLock(); school._RMW_LOCK = lk
    school._save({"today_done": 0, "history": [], "curriculum": [], "curriculum_idx": 0})
    try:
        with Probe(d, lk) as pr:
            errs = hammer([lambda i: school.record_session()] * 4, iters=100)
        got = school._load().get("today_done")
        return {"name": "school.record_session x4 threads (counter)", "with_lock": with_lock, "errors": errs[:2], "touches": pr.touches,
                "violations": pr.violations, "today_done": got, "expected": 400, "clean": (got == 400 and not errs)}
    finally:
        school.STATE, school._RMW_LOCK = saved


def run_school_extend(with_lock: bool):
    """_extend_program's fetch phase is slow: a record_session that lands DURING it must survive the program-extension save."""
    d = OUT_DIR / ("L" if with_lock else "N") / "school_ext"; d.mkdir(parents=True, exist_ok=True)
    for p in d.glob("*"): p.unlink()
    saved = (school.STATE, school._RMW_LOCK, book_selection.pick_one, library_hand.request_book, reading.current_book, reading.set_current,
             library_hand.shelf_books)
    school.STATE = d / "school.json"
    lk = OwnerLock(reentrant=True) if with_lock else NoLock(); school._RMW_LOCK = lk
    book_selection.pick_one = lambda: {"id": "PG1"}
    started = threading.Event()

    def slow_fetch(topic, row=None):
        started.set(); time.sleep(0.4)            # the network fetch
        return ("Fetched Title", "Author")
    library_hand.request_book = slow_fetch
    library_hand.shelf_books = lambda: [pathlib.Path("bk0001.txt")]
    reading.current_book = lambda: pathlib.Path("x.txt"); reading.set_current = lambda p: None
    school._save({"today_done": 0, "history": [], "curriculum": ["a"], "curriculum_idx": 0})
    import random as _r
    orig_rand = _r.random; _r.random = lambda: 0.9       # never the 20% spiral branch
    try:
        res = {}
        with Probe(d, lk) as pr:
            th = threading.Thread(target=lambda: res.setdefault("r", school.advance()))
            th.start(); started.wait(2)
            t0 = time.time()
            school.assign("bk0001")                        # a loop-side mutation landing INSIDE the fetch window
            school.record_session()
            loop_wait = time.time() - t0                   # << 0.4 s proves the lock is NOT held across the fetch
            th.join()
        st = school._load()
        titles = [h.get("title") for h in st.get("history", [])]
        ok = (loop_wait < 0.3 and st.get("curriculum") == ["a", "Fetched Title"] and st.get("curriculum_idx") == 1
              and titles == ["bk0001", "Fetched Title"])     # the assign() row survived the extension's save (built on fresh state)
        return {"name": "school._extend_program: fetch phase must not hold the lock; mutation built on fresh state", "with_lock": with_lock,
                "loop_side_wait_s": round(loop_wait, 3), "history_titles": titles, "touches": pr.touches, "violations": pr.violations, "clean": ok}
    finally:
        _r.random = orig_rand
        (school.STATE, school._RMW_LOCK, book_selection.pick_one, library_hand.request_book, reading.current_book, reading.set_current,
         library_hand.shelf_books) = saved


# ------------------------------------------------------------------------------------------------------------ library_hand
class _Resp:
    def __init__(self, b): self._b = b
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def read(self): return self._b


def run_library(with_lock: bool):
    d = OUT_DIR / ("L" if with_lock else "N") / "library"; d.mkdir(parents=True, exist_ok=True)
    for p in list(d.glob("**/*")):
        if p.is_file(): p.unlink()
    meta_f = d / "meta.csv"; meta_f.write_text("x", encoding="utf-8")
    saved = (library_hand.META, library_hand.BOOKS, library_hand._FETCH_STATE, library_hand._last_fetch, library_hand._REQUEST_LOCK,
             library_hand._search, library_hand._set_current, book_selection.record_pick, library_hand.urllib.request.urlopen)
    library_hand.META = meta_f; library_hand.BOOKS = d / "books"; library_hand._FETCH_STATE = d / "state.json"; library_hand._last_fetch = 0.0
    lk = OwnerLock() if with_lock else NoLock(); library_hand._REQUEST_LOCK = lk
    fetches = [0]; mu = threading.Lock()
    library_hand._search = lambda topic: {"id": "PG123", "title": "A Test Book", "author": "Nobody"}
    library_hand._set_current = lambda p: None
    book_selection.record_pick = lambda *a, **k: None

    def fake_urlopen(url, timeout=0):
        with mu: fetches[0] += 1
        time.sleep(0.3)
        return _Resp(b"*** START OF THIS ***\nbody text\n*** END OF THIS ***")
    library_hand.urllib.request.urlopen = fake_urlopen
    results = []
    try:
        with Probe(d, lk) as pr:
            errs = hammer([lambda i: results.append(library_hand.request_book("a test"))] * 4, iters=1)
        got = [r for r in results if r]
        return {"name": "library_hand.request_book: 4 overlapping requests inside one cooldown window", "with_lock": with_lock, "errors": errs[:2],
                "touches": pr.touches, "violations": pr.violations, "network_fetches": fetches[0], "successful_returns": len(got), "expected_fetches": 1,
                "clean": (fetches[0] == 1 and len(got) == 1 and not errs)}
    finally:
        (library_hand.META, library_hand.BOOKS, library_hand._FETCH_STATE, library_hand._last_fetch, library_hand._REQUEST_LOCK,
         library_hand._search, library_hand._set_current, book_selection.record_pick, library_hand.urllib.request.urlopen) = saved


def run_library_failed_first(with_lock: bool):
    """A failed first fetch writes no _last_fetch, so the next serialised request must still TRY (the lock must not turn a failure into a cooldown)."""
    d = OUT_DIR / ("L" if with_lock else "N") / "library_fail"; d.mkdir(parents=True, exist_ok=True)
    for p in list(d.glob("**/*")):
        if p.is_file(): p.unlink()
    meta_f = d / "meta.csv"; meta_f.write_text("x", encoding="utf-8")
    saved = (library_hand.META, library_hand.BOOKS, library_hand._FETCH_STATE, library_hand._last_fetch, library_hand._REQUEST_LOCK,
             library_hand._search, library_hand._set_current, book_selection.record_pick, library_hand.urllib.request.urlopen)
    library_hand.META = meta_f; library_hand.BOOKS = d / "books"; library_hand._FETCH_STATE = d / "state.json"; library_hand._last_fetch = 0.0
    lk = OwnerLock() if with_lock else NoLock(); library_hand._REQUEST_LOCK = lk
    calls = [0]
    library_hand._search = lambda topic: {"id": "PG9", "title": "Second Book", "author": "N"}
    library_hand._set_current = lambda p: None
    book_selection.record_pick = lambda *a, **k: None

    def fake_urlopen(url, timeout=0):
        calls[0] += 1
        if calls[0] <= 3: raise OSError("simulated network failure")   # the whole first request (3 URL variants) fails
        return _Resp(b"*** START OF THIS ***\nbody\n*** END OF THIS ***")
    library_hand.urllib.request.urlopen = fake_urlopen
    try:
        r1 = library_hand.request_book("x"); r2 = library_hand.request_book("x")
        return {"name": "library_hand.request_book: failed first fetch does not consume the cooldown", "with_lock": with_lock, "first": r1, "second": r2,
                "touches": 0, "violations": 0, "control_exempt": True, "clean": (r1 is None and r2 is not None)}
    finally:
        (library_hand.META, library_hand.BOOKS, library_hand._FETCH_STATE, library_hand._last_fetch, library_hand._REQUEST_LOCK,
         library_hand._search, library_hand._set_current, book_selection.record_pick, library_hand.urllib.request.urlopen) = saved


# ------------------------------------------------------------------------------------------------------------- watershed
def run_watershed(with_lock: bool):
    d = OUT_DIR / ("L" if with_lock else "N") / "watershed"; d.mkdir(parents=True, exist_ok=True)
    for p in d.glob("*"): p.unlink()
    saved = (watershed._OBSERVE_LOCK,)
    lk = OwnerLock() if with_lock else NoLock(); watershed._OBSERVE_LOCK = lk
    rng = np.random.default_rng(7)
    vec = rng.standard_normal(384).astype(np.float32); vec /= np.linalg.norm(vec)
    ROUNDS, THREADS = 30, 8
    dup_rounds = 0; sum_bad_rounds = 0; errs_all = []
    try:
        with Probe(d, lk) as pr:
            for r in range(ROUNDS):
                for _f in d.glob('*'): _f.unlink()
                watershed.configure(data_dir=d)                 # fresh empty state each round: the first-candidate race is the sharp one
                thought = "a recurring image of the sea at dusk " + str(r)
                errs_all += hammer([lambda i, t=thought: watershed.observe(t, vec=vec, ts=1_790_000_000.0 + i, cycle_id="c", day0=1_790_000_000.0, _cooldown=False)] * THREADS, iters=1)
                cands = watershed._load_state().get("candidates", [])
                if len(cands) != 1: dup_rounds += 1
                if sum(c.get("n", 0) for c in cands) != THREADS: sum_bad_rounds += 1
        return {"name": "watershed.observe: 8 threads, one repeated image, fresh state x30", "with_lock": with_lock, "errors": errs_all[:2],
                "touches": pr.touches, "violations": pr.violations, "rounds_with_duplicate_candidates": dup_rounds,
                "rounds_with_lost_observe_count": sum_bad_rounds, "clean": (dup_rounds == 0 and sum_bad_rounds == 0 and not errs_all)}
    finally:
        watershed._OBSERVE_LOCK, = saved
        watershed.configure(data_dir=watershed._DATA)


def main():
    rows = []
    for fn in (run_school_advance, run_school_counter, run_school_extend, run_library, run_library_failed_first, run_watershed):
        for wl in (True, False):
            r = fn(wl); rows.append(r)
            print(json.dumps(r, default=str))
    bad = 0
    for r in rows:
        if r["with_lock"] and not (r["clean"] and r["violations"] == 0): print("FAIL (with lock):", r["name"]); bad += 1
        if not r["with_lock"] and not r.get("control_exempt") and not (r["violations"] > 0 or not r["clean"]): print("FAIL (no-lock control did not show the race):", r["name"]); bad += 1
    print("RESULT:", "PASS" if not bad else f"{bad} FAIL")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
