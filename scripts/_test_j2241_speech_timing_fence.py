"""Regression test for F-2933 / J-2241: core.speech_timing_shadow must not write Du's live
data/speech_timing_shadow.jsonl from a non-live (lab) process, with or without lab_env.isolate().

Checks (read-only on live data/: hashes the live store before/after):
  1. core resolves inside this tree (import core BEFORE lab_env, F-2423);
  2. log_call/log_human with the shipped constant and with _LOG pointed at the REAL live path write nothing
     and never raise (fail-open), outside AND inside a bare lab_env.isolate();
  3. a real model_client.call_node_json-shaped path: log_call reached via a hot-lane base_url writes nothing;
  4. redirected via isolate(also=[(sts, ["_LOG"])]) it DOES write in the sandbox (fence is not a blanket no-op);
  5. profile.mark_live() -> the write goes through (live behaviour unchanged) -- exercised on a temp path only;
  6. live store sha256 + size unchanged.
Exit 0 = pass. Run from a worktree."""
import hashlib, os, pathlib, sys, tempfile, time
HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import core
assert str(pathlib.Path(core.__file__).resolve()).startswith(str(HERE)), core.__file__
sys.path.append(str(pathlib.Path.home() / ".claude" / "skills" / "job-queue"))
from core import speech_timing_shadow as sts, profile, telemetry
import lab_env

LIVE_LOG = pathlib.Path(r"C:\Nascence") / "data" / "speech_timing_shadow.jsonl"
FAILS = []
def check(label, cond):
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond: FAILS.append(label)
def h(p):
    if not p.exists(): return None
    return (p.stat().st_size, hashlib.sha256(p.read_bytes()).hexdigest())

before = h(LIVE_LOG)
wt_log = sts._LOG
wt_before = h(wt_log)
check("telemetry lab mode is OFF (the gap under test)", telemetry._LAB_MODE is False)
check("profile.LIVE is False (non-live process)", profile.LIVE is False)
t = time.time()
def fire():
    sts.log_call("http://127.0.0.1:11433", "j2241_test:1", t, t, t + 1, True)
    sts.log_human("j2241")
try:
    fire()                                   # shipped constant (this tree's data/)
    sts._LOG = LIVE_LOG; fire()              # the real live path
    with lab_env.isolate(db="empty"):
        fire()                               # bare isolate(): the replay_v2 case
    raised = False
except Exception as e:
    raised = True; print("   raised:", e)
finally:
    sts._LOG = wt_log
check("no exception escaped log_call/log_human", not raised)
check("live store unchanged (sha256+size)", h(LIVE_LOG) == before)
check("this tree's data/ shadow unchanged", h(wt_log) == wt_before)

with lab_env.isolate(db="empty", also=[(sts, ["_LOG"])]) as lab:
    fire(); red = sts._LOG
    n = len(red.read_text(encoding="utf-8").splitlines()) if red.exists() else 0
check(f"redirected into sandbox writes (rows={n})", n == 2)
check("_LOG restored after isolate", sts._LOG == wt_log)

tmp = pathlib.Path(tempfile.mkdtemp(prefix="x_J-2241_")) / "sts.jsonl"
saved = profile.LIVE
try:
    profile.LIVE = True                      # simulate mark_live() without touching any live path
    sts._LOG = LIVE_LOG
    # guard_path returns the live path unchanged when LIVE -- check the decision only, never write live
    check("live process: guard_path passes the live path", profile.guard_path(LIVE_LOG) == LIVE_LOG)
    sts._LOG = tmp; fire()
    check("live process: rows written as before", tmp.exists() and len(tmp.read_text().splitlines()) == 2)
finally:
    profile.LIVE = saved; sts._LOG = wt_log
check("live store unchanged at end (canary)", h(LIVE_LOG) == before)
print("PASS" if not FAILS else f"FAIL {FAILS}")
sys.exit(1 if FAILS else 0)
