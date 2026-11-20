"""Regression test for F-2883 / J-2180: memory_service.ask() under lab_env.isolate() must not write live data/.

Before the fix, core.opponent_process, core.spring_ledger and core.associative_recall (assoc_seed_share_shadow.jsonl,
embedding_matrix.npz) resolved their writes from a bare __file__-relative data/ constant that isolate() does not
redirect (isolate only redirects DB_PATH plus what `also=` names), so a lab ask() leaked into live data/. They now go
through profile.guard_path() (D-0179, the J-1783 pattern): a non-live process is refused (fail-open, swallowed) unless the
constant is redirected (also=) into the lab sandbox.

Checks (read-only on live data/: it only stats top-level files before/after):
  1. core resolves inside this worktree (import core BEFORE lab_env, F-2423);
  2. each fenced writer, called directly with its LIVE-path constant, creates/modifies nothing;
  3. each fenced writer, redirected via isolate(also=...), DOES write inside the lab sandbox (fence is not a blanket no-op);
  4. a real memory_service.ask() under a bare isolate() leaves the canonical top-level data/ fingerprint unchanged
     (hub/supervisor logs excluded -- not this process's).
Exit 0 = pass. Run from a worktree, never bare from the shared tree."""
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789: no write to the tree's data/
import os, sys, pathlib, time, json
HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import core
assert str(pathlib.Path(core.__file__).resolve()).startswith(str(HERE)), core.__file__
sys.path.append(str(pathlib.Path.home() / ".claude" / "skills" / "job-queue"))
from core import opponent_process, spring_ledger, associative_recall, memory_service
try:
    from core import speech_timing_shadow as _sts
    for _n in dir(_sts):
        if _n.startswith(("record", "log", "append", "write")) and callable(getattr(_sts, _n)):
            setattr(_sts, _n, lambda *a, **k: None)
except Exception:
    pass
import lab_env

LIVE = pathlib.Path(r"C:\Nascence") / "data"
IGNORE_SUFFIX = (".log",)
# J-4050: the shared live data/ is also appended to by OTHER concurrent processes (job-run agents' model_client telemetry), so a
# size/mtime diff of these files cannot attribute a change to THIS process. They are excluded from the fingerprint and covered
# instead by an in-process audit hook recording every write-mode open() THIS process makes directly under live data/.
CONCURRENT_TELEMETRY = ("llm_calls.jsonl", "llm_latency.jsonl", "thought_station_log.jsonl")
LIVE_WRITES = []
def _audit(event, args):
    try:
        if event == "open":
            path, mode, flags = args[0], args[1], args[2]
            w = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
                isinstance(flags, int) and bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC)))
            if w and not isinstance(path, int):
                q = pathlib.Path(os.path.abspath(os.fsdecode(os.fspath(path))))
                if q.parent == LIVE:
                    LIVE_WRITES.append(q.name)
    except Exception:
        pass
sys.addaudithook(_audit)
FAILS = []
def check(label, cond):
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond: FAILS.append(label)

def fp():
    out = {}
    for p in LIVE.iterdir():
        if p.is_file() and not p.name.endswith(IGNORE_SUFFIX) and p.name not in CONCURRENT_TELEMETRY:
            st = p.stat(); out[p.name] = (st.st_size, st.st_mtime_ns)
    return out
def diff(a, b):
    return sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))

# live-path constants as shipped (the module constants are __file__-relative; under a worktree they point at the worktree's
# data/, which guard_path also refuses -- point them at the REAL live paths to prove the canonical-root check as well)
saved = {m: {} for m in (opponent_process, spring_ledger, associative_recall)}
def live_paths():
    opponent_process._STATE = LIVE / "opponent_process_state.json"; opponent_process._LOG = LIVE / "opponent_process_shadow.jsonl"
    spring_ledger._STATE = LIVE / "spring_ledger_state.json";       spring_ledger._LOG = LIVE / "spring_ledger_shadow.jsonl"
    associative_recall._SEED_SHARE_LOG = LIVE / "assoc_seed_share_shadow.jsonl"
    associative_recall._EMB_CACHE = LIVE / "embedding_matrix.npz"
import numpy as np
live_paths()
before = fp()
opponent_process._save({"x": 1}); opponent_process._log({"x": 1})
spring_ledger._save({"x": 1}); spring_ledger._log({"x": 1})
associative_recall._save_persisted(np.zeros((2, 3), dtype=np.float32), ["a", "b"])
check("direct writers on LIVE paths change nothing in live data/", diff(before, fp()) == [])

# 3: redirected writers still write (inside the sandbox)
with lab_env.isolate(db="empty", also=[(opponent_process, ["_STATE", "_LOG"]), (spring_ledger, ["_STATE", "_LOG"]),
                                       (associative_recall, ["_SEED_SHARE_LOG", "_EMB_CACHE"])]) as lab:
    opponent_process._save({"x": 1}); opponent_process._log({"x": 1})
    spring_ledger._save({"x": 1}); spring_ledger._log({"x": 1})
    associative_recall._save_persisted(np.zeros((2, 3), dtype=np.float32), ["a", "b"])
    names = {p.name for p in lab.iterdir()}
    check("redirected writers land in the lab sandbox", {"opponent_process_state.json", "opponent_process_shadow.jsonl",
          "spring_ledger_state.json", "spring_ledger_shadow.jsonl", "embedding_matrix.npz"} <= names)
check("sandbox writes did not touch live data/ top level", diff(before, fp()) == [])

# 4: real ask() under a BARE isolate (nothing named in also=) -- the F-2883 scenario
live_paths()
before = fp()
err = None
try:
    with lab_env.isolate(db="copy"):
        res = memory_service.ask("j2180_fence_test", "what do I remember about dreams", k=5)
        associative_recall._cache["ts"] = 0.0
        print("  ask returned", len(res or []), "rows")
except Exception as exc:
    err = exc
    print("  ask raised (fail-open expected not to):", repr(exc))
d = diff(before, fp())
check("ask() under bare isolate leaves live data/ top-level unchanged (changed: %s)" % d, d == [])
check("ask() under bare isolate made no write-mode open directly under live data/ in THIS process (%s)" % sorted(set(LIVE_WRITES)),
      not LIVE_WRITES)
check("ask() did not raise", err is None)
print("FAIL" if FAILS else "PASS")
sys.exit(1 if FAILS else 0)
